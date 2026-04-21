import asyncio
import random
import sqlite3
import datetime
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.enums import ParseMode

# --- НАСТРОЙКИ (Берутся из панели Bothost) ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0")) 

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
DB_NAME = "dick_game.db"

# --- РАБОТА С БАЗОЙ ДАННЫХ ---
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

# --- КЛАВИАТУРЫ ---
def group_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📏 Вырастить!", callback_query_data="grow")],
        [InlineKeyboardButton(text="🏆 Топ игроков", callback_query_data="top")]
    ])

def private_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Ввести промокод", callback_query_data="promo_info")],
        [InlineKeyboardButton(text="🛒 Магазин улучшений", callback_query_data="shop_menu")]
    ])

# --- ОБРАБОТКА КОМАНД ---

@dp.message(CommandStart())
async def start_handler(message: Message):
    user = get_user(message.from_user.id, message.from_user.username)
    
    if message.chat.type in ['group', 'supergroup']:
        await message.answer(
            f"💪 Привет, чат <b>{message.chat.title}</b>!\nЯ бот-выращиватель. Кто тут самый длинный?",
            reply_markup=group_kb()
        )
    else:
        await message.answer(
            f"👋 Привет, {message.from_user.first_name}!\n\n"
            f"Твой размер: <b>{user[2]} см</b>\n"
            f"Твой баланс: <b>{user[3]} 💰</b>\n\n"
            "⚠️ Выращивать можно только в группах!\nДобавь меня в чат и жми кнопку.",
            reply_markup=private_kb()
        )

# --- ЛОГИКА ДЛЯ ГРУПП (КНОПКИ) ---

@dp.callback_query(F.data == "grow")
async def grow_callback(callback: CallbackQuery):
    if callback.message.chat.type == 'private':
        await callback.answer("❌ В личке не растет! Иди в группу.", show_alert=True)
        return

    user = get_user(callback.from_user.id, callback.from_user.username)
    now = datetime.datetime.now()
    
    if user[4]:
        last_grow = datetime.datetime.strptime(user[4], '%Y-%m-%d %H:%M:%S.%f')
        if (now - last_grow).total_seconds() < 86400: # 24 часа
            await callback.answer("⏳ Ты уже пробовал сегодня! Приходи завтра.", show_alert=True)
            return

    change = random.randint(-4, 12)
    new_size = max(0, user[2] + change)
    bonus_money = random.randint(15, 60)
    
    update_user(user_id=callback.from_user.id, dick_size=new_size, balance=user[3]+bonus_money, last_grow=str(now))
    
    msg = f"📈 @{callback.from_user.username}, +" if change >= 0 else f"📉 @{callback.from_user.username}, "
    await callback.message.answer(
        f"{msg}{change} см!\nТеперь: <b>{new_size} см</b>\nБонус: <b>+{bonus_money} 💰</b>"
    )
    await callback.answer()

@dp.callback_query(F.data == "top")
async def top_callback(callback: CallbackQuery):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT username, dick_size FROM users ORDER BY dick_size DESC LIMIT 10')
    rows = cursor.fetchall()
    conn.close()
    
    text = "🏆 <b>ТОП-10 ГИГАНТОВ:</b>\n\n"
    for i, row in enumerate(rows, 1):
        text += f"{i}. @{row[0]} — {row[1]} см\n"
    
    await callback.message.answer(text)
    await callback.answer()

# --- ЛОГИКА ДЛЯ ЛИЧКИ (МАГАЗИН И ПРОМО) ---

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
async def buy_item(callback: CallbackQuery):
    size_add = int(callback.data.split("_")[1])
    price = 250 if size_add == 5 else 600
    user = get_user(callback.from_user.id)
    
    if user[3] >= price:
        update_user(user_id=callback.from_user.id, dick_size=user[2]+size_add, balance=user[3]-price)
        await callback.answer(f"✅ Куплено! +{size_add} см", show_alert=True)
        await shop_menu(callback)
    else:
        await callback.answer("❌ Мало денег! Иди в чат и расти бесплатно.", show_alert=True)

@dp.callback_query(F.data == "promo_info")
async def promo_info(callback: CallbackQuery):
    await callback.message.edit_text(
        "Чтобы активировать код, напиши:\n<code>/promo ТВОЙ_КОД</code>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_query_data="to_main")]])
    )

@dp.callback_query(F.data == "to_main")
async def to_main(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    await callback.message.edit_text(
        f"Твой размер: <b>{user[2]} см</b>\nТвой баланс: <b>{user[3]} 💰</b>",
        reply_markup=private_kb()
    )

# --- АДМИН-КОМАНДЫ И ПРОМОКОДЫ ---

@dp.message(Command("promo"))
async def use_promo(message: Message, command: CommandObject):
    if message.chat.type != 'private':
        return await message.answer("❌ Промокоды только в личке!")
    
    code = command.args
    user_id = message.from_user.id
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM promo_codes WHERE code = ?', (code,))
    pr = cursor.fetchone()
    
    if not pr:
        return await message.answer("❌ Код не найден.")
    
    cursor.execute('SELECT * FROM used_promos WHERE user_id = ? AND code = ?', (user_id, code))
    if cursor.fetchone():
        return await message.answer("❌ Ты уже юзал этот код.")
    
    if pr[3] <= 0:
        return await message.answer("❌ Код закончился.")
    
    user = get_user(user_id)
    update_user(user_id=user_id, dick_size=user[2]+pr[1], balance=user[3]+pr[2])
    cursor.execute('INSERT INTO used_promos VALUES (?, ?)', (user_id, code))
    cursor.execute('UPDATE promo_codes SET uses = uses - 1 WHERE code = ?', (code,))
    conn.commit()
    conn.close()
    await message.answer(f"🎁 Успех! Получено +{pr[1]} см и +{pr[2]} 💰")

@dp.message(Command("addpromo"))
async def add_promo(message: Message, command: CommandObject):
    if message.from_user.id != ADMIN_ID: return
    try:
        c, s, b, u = command.args.split()
        conn = sqlite3.connect(DB_NAME)
        conn.execute('INSERT INTO promo_codes VALUES (?,?,?,?)', (c, int(s), int(b), int(u)))
        conn.commit()
        await message.answer(f"✅ Код <code>{c}</code> создан!")
    except:
        await message.answer("Ошибка! Пример: `/addpromo ЛЕТО 10 500 20`")

async def main():
    init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
    if user["secret"] is None:
        return # Игнорируем, если игра не начата

    guess = int(message.text)
    user["attempts"] += 1

    if guess < user["secret"]:
        await message.answer("⬆️ Бери выше!")
    elif guess > user["secret"]:
        await message.answer("⬇️ Слишком много, бери ниже!")
    else:
        await message.answer(
            f"🥳 Ура! Ты угадал число {user['secret']}!\n"
            f"Попыток потрачено: {user['attempts']}.\n"
            "Напиши /start, чтобы сыграть еще раз."
        )
        user["secret"] = None

async def main():
    print("Бот успешно запущен на хостинге!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

