import asyncio
import random
import sqlite3
import datetime
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# --- Конфиг ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0")) 

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
DB_NAME = "game_data.db"

# --- База данных ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
        (user_id INTEGER PRIMARY KEY, username TEXT, dick_size INTEGER DEFAULT 0, balance INTEGER DEFAULT 0, last_grow TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS promo_codes 
        (code TEXT PRIMARY KEY, reward_size INTEGER, reward_balance INTEGER)''')
    conn.commit()
    conn.close()

def get_user(user_id, username="👤 Игрок"):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    if not user:
        cursor.execute('INSERT INTO users (user_id, username) VALUES (?, ?)', (user_id, username))
        conn.commit()
        user = (user_id, username, 0, 0, None)
    conn.close()
    return user

def update_user(user_id, **kwargs):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    for key, value in kwargs.items():
        cursor.execute(f'UPDATE users SET {key} = ? WHERE user_id = ?', (value, user_id))
    conn.commit()
    conn.close()

# --- Команды ---

@dp.message(CommandStart())
async def start_cmd(message: Message):
    await message.answer(
        "👋 Привет! Я бот-выращиватель.\n\n"
        "📜 <b>Команды:</b>\n"
        "➕ /grow — Вырастить (раз в сутки)\n"
        "🏆 /top — Топ игроков\n"
        "💰 /balance — Твой профиль\n"
        "🎁 /promo КОД — Активировать бонус"
    )

@dp.message(Command("grow"))
async def grow_cmd(message: Message):
    if message.chat.type == 'private':
        return await message.answer("❌ Растить можно только в группах! Добавь меня в чат с друзьями.")
    
    user = get_user(message.from_user.id, message.from_user.username)
    now = datetime.datetime.now()
    
    if user[4]:
        last = datetime.datetime.strptime(user[4], '%Y-%m-%d %H:%M:%S.%f')
        if (now - last).total_seconds() < 86400:
            return await message.reply("⏳ Можно только раз в 24 часа! Приходи завтра.")

    diff = random.randint(-3, 10)
    new_size = max(0, user[2] + diff)
    update_user(user_id=message.from_user.id, dick_size=new_size, balance=user[3]+25, last_grow=str(now))
    
    sign = "+" if diff >= 0 else ""
    await message.reply(f"📈 {'+' if diff>=0 else ''}{diff} см!\nТеперь: <b>{new_size} см</b> (+25 💰)")

@dp.message(Command("balance"))
async def balance_cmd(message: Message):
    user = get_user(message.from_user.id, message.from_user.username)
    await message.answer(
        f"👤 <b>Профиль @{user[1]}</b>\n\n"
        f"📏 Размер: {user[2]} см\n"
        f"💰 Баланс: {user[3]} монет"
    )

@dp.message(Command("top"))
async def top_cmd(message: Message):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT username, dick_size FROM users ORDER BY dick_size DESC LIMIT 10')
    rows = cursor.fetchall()
    conn.close()
    
    res = "🏆 <b>ТОП-10 ИГРОКОВ:</b>\n\n"
    for i, r in enumerate(rows, 1):
        res += f"{i}. @{r[0]} — {r[1]} см\n"
    await message.answer(res)

@dp.message(Command("promo"))
async def promo_cmd(message: Message, command: CommandObject):
    code = command.args
    if not code: return await message.answer("Пиши: <code>/promo КОД</code>")
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM promo_codes WHERE code = ?', (code,))
    promo = cursor.fetchone()
    
    if promo:
        user = get_user(message.from_user.id)
        update_user(user_id=message.from_user.id, dick_size=user[2]+promo[1], balance=user[3]+promo[2])
        await message.answer(f"🎁 Успех! +{promo[1]} см и +{promo[2]} 💰")
    else:
        await message.answer("❌ Код не найден.")
    conn.close()

# --- Запуск ---
async def main():
    init_db()
    print("Бот запущен без кнопок!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
