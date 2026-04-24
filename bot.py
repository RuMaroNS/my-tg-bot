import asyncio
import random
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from supabase import create_client, Client

# Настройка логирования (чтобы видеть ошибки в консоли)
logging.basicConfig(level=logging.INFO)

# ========== КОНФИГУРАЦИЯ ==========
SB_URL = 'https://wbkygibviddkdjxbahbg.supabase.co'
SB_KEY = 'sb_publishable_l5wIAt6RrAl4Uo8uZKerRQ_xBYDS-Kv'
BOT_TOKEN = '8630026221:AAGfuIfKQPdxSkyhU3IVCnRtRkKrlzKD0nk'

supabase: Client = create_client(SB_URL, SB_KEY)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

def get_profile(tg_id):
    """Ищем юзера в profiles по TelegramUSER"""
    res = supabase.table("profiles").select("*").eq("TelegramUSER", str(tg_id)).execute()
    return res.data[0] if res.data else None

def get_item_details(item_name):
    """Берем инфу о предмете (редкость и т.д.) из items_meta"""
    res = supabase.table("items_meta").select("*").eq("name", item_name).execute()
    return res.data[0] if res.data else None

# ========== ОБРАБОТЧИКИ ==========

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user = get_profile(message.from_user.id)
    kb = ReplyKeyboardBuilder()
    kb.row(types.KeyboardButton(text="👤 Профиль"), types.KeyboardButton(text="📦 Кейсы"))
    
    if user:
        await message.answer(f"✅ Доступ разрешен! С возвращением, {user['username']}.", 
                             reply_markup=kb.as_markup(resize_keyboard=True))
    else:
        await message.answer(f"❌ Твой ID `{message.from_user.id}` не найден в таблице profiles.\n"
                             f"Укажи его в колонке TelegramUSER, чтобы бот тебя узнал.")

@dp.message(F.text == "👤 Профиль")
async def cmd_profile(message: types.Message):
    user = get_profile(message.from_user.id)
    if not user:
        return await message.answer("Сначала привяжи TelegramID в базе данных!")
    
    score = user.get('score', 0)
    inv_count = len(user.get('inventory', []))
    
    msg_text = (
        f"👤 **Профиль: {user['username']}**\n"
        f"━━━━━━━━━━━━━━\n"
        f"💰 **Баланс (score):** {score} 💎\n"
        f"🎒 **Инвентарь:** {inv_count} шт.\n\n"
        f"Твой ID: `{message.from_user.id}`"
    )
    await message.answer(msg_text, parse_mode="Markdown")

@dp.message(F.text == "📦 Кейсы")
async def cmd_cases(message: types.Message):
    res = supabase.table("cases_meta").select("*").execute()
    kb = InlineKeyboardBuilder()
    
    for c in res.data:
        kb.row(types.InlineKeyboardButton(
            text=f"Открыть {c['name']} — {c['price']} 💰", 
            callback_data=f"buy_{c['id']}_{c['price']}"
        ))
    
    await message.answer("🎁 Выбери кейс для прокрутки в слотах:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("buy_"))
async def handle_opening(callback: types.CallbackQuery):
    _, c_id, price = callback.data.split("_")
    price = int(price)
    user = get_profile(callback.from_user.id)

    if not user or user.get('score', 0) < price:
        return await callback.answer("Недостаточно score! ❌", show_alert=True)

    # 1. Списание баланса
    new_score = user['score'] - price
    supabase.table("profiles").update({"score": new_score}).eq("id", user['id']).execute()

    # 2. Анимация СЛОТОВ
    dice_msg = await callback.message.answer_dice(emoji="🎰")
    await callback.message.edit_text(f"🎰 Кейс «{c_id}» запущен...")
    
    await asyncio.sleep(3.5) # Время анимации в ТГ

    # 3. Выбор лута из JSON кейса
    case_data = supabase.table("cases_meta").select("loot").eq("id", c_id).single().execute()
    loot_pool = case_data.data.get('loot', [])

    if not loot_pool:
        return await callback.message.answer("Ошибка: в этом кейсе нет лута (пустой JSON)!")

    # Рандом по шансам
    winning_loot = random.choices(
        population=loot_pool,
        weights=[float(i.get('chance', 1)) for i in loot_pool],
        k=1
    )[0]
    
    item_name = winning_loot['name']

    # 4. Получаем данные о предмете из items_meta
    details = get_item_details(item_name)
    rarity = details.get('rarity', 'common') if details else 'common'
    d_name = details.get('display_name', item_name) if details else item_name

    # 5. Обновляем инвентарь (массив объектов id + char)
    current_inv = user.get('inventory', [])
    if not isinstance(current_inv, list): current_inv = []
    
    new_entry = {
        "id": str(random.randint(1000000000, 9999999999)), 
        "char": item_name
    }
    current_inv.append(new_entry)
    
    supabase.table("profiles").update({"inventory": current_inv}).eq("id", user['id']).execute()

    # 6. Результат
    await callback.message.answer(
        f"🎉 **ВЫПАЛО:** {d_name}\n"
        f"━━━━━━━━━━━━━━\n"
        f"💎 Редкость: `{rarity.upper()}`\n"
        f"💰 Остаток score: {new_score}\n"
        f"🎰 Слоты показали: {dice_msg.dice.value}",
        parse_mode="Markdown"
    )

async def main():
    print("=== Бот запущен ( profiles / cases_meta / items_meta ) ===")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
async def cmd_profile(message: types.Message):
    user = get_user(message.from_user.id)
    if not user:
        return await message.answer("Сначала привяжи аккаунт в Supabase!")
    
    balance = user.get('balance', 0)
    # ЗДЕСЬ БЫЛА ОШИБКА ОТСТУПА:
    msg_text = (
        f"👤 **Твой профиль**\n"
        f"━━━━━━━━━━━━━━\n"
        f"💰 **Баланс:** {balance} $\n\n"
        f"Колонка TelegramUSER: `{message.from_user.id}`"
    )
    
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="🎒 Инвентарь", callback_data="view_inv"))
    await message.answer(msg_text, reply_markup=kb.as_markup(), parse_mode="Markdown")

@dp.message(F.text == "📦 Кейсы")
async def cmd_cases(message: types.Message):
    res = supabase.table("cases").select("*").execute()
    kb = InlineKeyboardBuilder()
    for c in res.data:
        kb.row(types.InlineKeyboardButton(text=f"{c['name']} — {c['price']}$", callback_data=f"buy_{c['id']}_{c['price']}"))
    await message.answer("🎁 Выбери кейс для прокрутки:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("buy_"))
async def handle_buy(callback: types.CallbackQuery):
    _, c_id, price = callback.data.split("_")
    price = int(price)
    user = get_user(callback.from_user.id)

    if not user or user['balance'] < price:
        return await callback.answer("Недостаточно денег!", show_alert=True)

    # Списываем бабки
    new_balance = user['balance'] - price
    supabase.table("users").update({"balance": new_balance}).eq("id", user['id']).execute()

    # СЛОТЫ ТГ
    msg = await callback.message.answer_dice(emoji="🎰")
    await callback.message.edit_text(f"🎰 Крутим кейс {c_id}...")
    
    await asyncio.sleep(3.0) # Ждем анимацию

    loot_pool = get_loot(c_id)
    if not loot_pool:
        return await callback.message.answer("Кейс пустой в БД!")

    # Рандом по шансам
    win = random.choices(loot_pool, weights=[i['chance'] for i in loot_pool], k=1)[0]

    # В инвентарь
    supabase.table("inventory").insert({"user_id": user['id'], "item_name": win['name']}).execute()

    await callback.message.answer(
        f"🎊 **ВЫПАЛО:** {win['name']}\n"
        f"💰 Остаток: {new_balance} $\n"
        f"🎰 Значение слотов: {msg.dice.value}",
        parse_mode="Markdown"
    )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
