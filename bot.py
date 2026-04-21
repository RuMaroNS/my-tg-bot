import asyncio
import random
import sqlite3
import datetime
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# Эти данные бот сам возьмет из настроек Bothost
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0")) 

# Создаем бота (настройка для версии aiogram 3.7.0+)
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
DB_NAME = "dick_game.db"

# --- ЛОГИКА БАЗЫ ДАННЫХ (храним размеры и деньги) ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
        (user_id INTEGER PRIMARY KEY, username TEXT, dick_size INTEGER DEFAULT 0, balance INTEGER DEFAULT 0, last_grow TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS promo_codes 
        (code TEXT PRIMARY KEY, reward_size INTEGER, reward_balance INTEGER, uses INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS used_promos 
        (user_id INTEGER, code TEXT, PRIMARY KEY (user_id, code))''')
    conn.commit()
    conn.close()

def get_user(user_id, username="👤 Неизвестный"):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    if not user:
        cursor.execute('INSERT INTO users (user_id, username) VALUES (?, ?)', (user_id, username))
        conn.commit()
        return (user_id, username, 0, 0, None)
    conn.close()
    return user

def update_user(user_id, **kwargs):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    for key, value in kwargs.items():
        cursor.execute(f'UPDATE users SET {key} = ? WHERE user_id = ?', (value, user_id))
    conn.commit()
    conn.close()

# --- ОСНОВНЫЕ КНОПКИ ---
def get_private_kb(user):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Ввести промокод", callback_query_data="promo_info")],
        [InlineKeyboardButton(text="🛒 Магазин", callback_query_data="shop_menu")]
    ])

def get_group_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📏 Вырастить!", callback_query_data="grow")],
        [InlineKeyboardButton(text="🏆 ТОП игроков", callback_query_data="top")]
    ])

# --- ОБРАБОТЧИКИ КОМАНД ---

@dp.message(CommandStart())
async def start_handler(message: Message):
    user = get_user(message.from_user.id, message.from_user.username)
    if message.chat.type in ['group', 'supergroup']:
        await message.answer(f"💪 Привет чату <b>{message.chat.title}</b>!\nКто тут самый длинный? Жми кнопку!", reply_markup=get_group_kb())
    else:
        await message.answer(
            f"👋 Привет, {message.from_user.first_name}!\n\n"
            f"Твой размер: <b>{user[2]} см</b>\n"
            f"Твой баланс: <b>{user[3]} 💰</b>\n\n"
            "⚠️ Выращивать можно только в группах!", 
            reply_markup=get_private_kb(user)
        )

# --- ЛОГИКА ДЛЯ ГРУПП ---

@dp.callback_query(F.data == "grow")
async def grow_callback(callback: CallbackQuery):
    if callback.message.chat.type == 'private':
        await callback.answer("❌ В личке не растет! Иди в группу.", show_alert=True)
        return
    
    user = get_user(callback.from_user.id, callback.from_user.username)
    now = datetime.datetime.now()
    
    if user[4]:
        last_grow = datetime.datetime.strptime(user[4], '%Y-%m-%d %H:%M:%S.%f')
        if (now - last_grow).total_seconds() < 86400:
            await callback.answer("⏳ Только раз в сутки! Приходи завтра.", show_alert=True)
            return

    change = random.randint(-4, 12)
    new_size = max(0, user[2] + change)
    update_user(user_id=callback.from_user.id, dick_size=new_size, balance=user[3]+30, last_grow=str(now))
    
    res = "+" if change >= 0 else ""
    await callback.message.answer(f"📈 @{callback.from_user.username}, {res}{change} см!\nТеперь: <b>{new_size} см</b>")
    await callback.answer()

@dp.callback_query(F.data == "top")
async def top_callback(callback: CallbackQuery):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT username, dick_size FROM users ORDER BY dick_size DESC LIMIT 10')
    rows = cursor.fetchall()
    conn.close()
    
    text = "🏆 <b>ТОП-10 ГИГАНТОВ:</b>\n\n"
    for i, r in enumerate(rows, 1):
        text += f"{i}. @{r[0]} — {r[1]} см\n"
    await callback.message.answer(text)
    await callback.answer()

# --- МАГАЗИН И ПРОМОКОДЫ (ДЛЯ ЛИЧКИ) ---

@dp.callback_query(F.data == "promo_info")
async def promo_info(callback: CallbackQuery):
    await callback.message.edit_text(
        "Чтобы активировать промокод, напиши боту:\n\n<code>/promo ТВОЙ_КОД</code>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_query_data="to_main")]])
    )

@dp.callback_query(F.data == "shop_menu")
async def shop_menu(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    text = f"🛒 <b>МАГАЗИН</b>\nТвой баланс: <b>{user[3]} 💰</b>\n\nВыбери товар:"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💊 Витаминки (+5 см) - 250 💰", callback_query_data="buy_5")],
        [InlineKeyboardButton(text="💉 Укол (+15 см) - 600 💰", callback_query_data="buy_15")],
        [InlineKeyboardButton(text="🔙 Назад", callback_query_data="to_main")]
    ])
    await callback.message.edit_text(text, reply_markup=kb)

@dp.callback_query(F.data.startswith("buy_"))
async def buy_process(callback: CallbackQuery):
    size_add = int(callback.data.split("_")[1])
    price = 250 if size_add == 5 else 600
    user = get_user(callback.from_user.id)
    
    if user[3] >= price:
        update_user(user_id=callback.from_user.id, dick_size=user[2]+size_add, balance=user[3]-price)
        await callback.answer(f"✅ Успешно! +{size_add} см", show_alert=True)
        await shop_menu(callback)
    else:
        await callback.answer("❌ Недостаточно монет!", show_alert=True)

@dp.callback_query(F.data == "to_main")
async def to_main(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    await callback.message.edit_text(
        f"👋 Твой размер: <b>{user[2]} см</b>.\nБаланс: <b>{user[3]} 💰</b>",
        reply_markup=get_private_kb(user)
    )

# --- АДМИНКА (КОМАНДЫ) ---

@dp.message(Command("promo"))
async def use_promo(message: Message, command: CommandObject):
    if message.chat.type != 'private': return
    code = command.args
    if not code: return await message.answer("Введи код: `/promo КОД`")
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM promo_codes WHERE code = ?', (code,))
    pr = cursor.fetchone()
    
    if pr:
        user = get_user(message.from_user.id)
        update_user(user_id=message.from_user.id, dick_size=user[2]+pr[1], balance=user[3]+pr[2])
        await message.answer(f"✅ Успех! +{pr[1]} см и +{pr[2]} 💰")
    else:
        await message.answer("❌ Код не найден.")
    conn.close()

@dp.message(Command("addpromo"))
async def add_promo(message: Message, command: CommandObject):
    if message.from_user.id != ADMIN_ID: return
    try:
        c, s, b, u = command.args.split()
        conn = sqlite3.connect(DB_NAME)
        conn.execute('INSERT INTO promo_codes VALUES (?,?,?,?)', (c, int(s), int(b), int(u)))
        conn.commit()
        await message.answer(f"✅ Промокод <code>{c}</code> создан!")
    except:
        await message.answer("Ошибка! Пример: `/addpromo КОД СМ БАБКИ КОЛВО`")

# --- ЗАПУСК ---
async def main():
    init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
