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

# 1. Настройки из Bothost
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0")) 

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
DB_NAME = "game_data.db"

# 2. База данных
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

# 3. Кнопки
def main_private_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Промокод", callback_query_data="view_promo")],
        [InlineKeyboardButton(text="🛒 Магазин", callback_query_data="view_shop")]
    ])

def group_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📏 Вырастить!", callback_query_data="do_grow")],
        [InlineKeyboardButton(text="🏆 ТОП", callback_query_data="view_top")]
    ])

# 4. Логика
@dp.message(CommandStart())
async def start_cmd(message: Message):
    user = get_user(message.from_user.id, message.from_user.username)
    if message.chat.type in ['group', 'supergroup']:
        await message.answer(f"💪 Привет чату! Кто тут самый длинный?", reply_markup=group_kb())
    else:
        await message.answer(f"👋 Привет! Твой размер: <b>{user[2]} см</b>.\nБаланс: {user[3]} 💰\n⚠️ Выращивать можно только в группах!", reply_markup=main_private_kb())

@dp.callback_query(F.data == "do_grow")
async def process_grow(callback: CallbackQuery):
    if callback.message.chat.type == 'private':
        await callback.answer("❌ Растет только в группах!", show_alert=True)
        return
    user = get_user(callback.from_user.id, callback.from_user.username)
    now = datetime.datetime.now()
    if user[4]:
        last = datetime.datetime.strptime(user[4], '%Y-%m-%d %H:%M:%S.%f')
        if (now - last).total_seconds() < 86400:
            await callback.answer("⏳ Приходи завтра!", show_alert=True)
            return
    diff = random.randint(-3, 10)
    new_size = max(0, user[2] + diff)
    update_user(user_id=callback.from_user.id, dick_size=new_size, balance=user[3]+25, last_grow=str(now))
    await callback.message.answer(f"📈 @{callback.from_user.username}, {'+' if diff>=0 else ''}{diff} см!\nТеперь: <b>{new_size} см</b> (+25 💰)")
    await callback.answer()

@dp.callback_query(F.data == "view_top")
async def process_top(callback: CallbackQuery):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT username, dick_size FROM users ORDER BY dick_size DESC LIMIT 10')
    rows = cursor.fetchall()
    conn.close()
    res = "🏆 <b>ТОП-10 ГИГАНТОВ:</b>\n\n"
    for i, r in enumerate(rows, 1):
        res += f"{i}. @{r[0]} — {r[1]} см\n"
    await callback.message.answer(res)
    await callback.answer()

@dp.callback_query(F.data == "view_promo")
async def process_promo_menu(callback: CallbackQuery):
    await callback.message.edit_text("Введи команду: <code>/promo КОД</code>", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_query_data="back_main")]]))

@dp.callback_query(F.data == "view_shop")
async def process_shop_menu(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💊 Витамины (+5 см) — 200 💰", callback_query_data="buy_5")],
        [InlineKeyboardButton(text="🔙 Назад", callback_query_data="back_main")]
    ])
    await callback.message.edit_text(f"🛒 <b>МАГАЗИН</b>\nБаланс: {user[3]} 💰", reply_markup=kb)

@dp.callback_query(F.data == "buy_5")
async def process_buy(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    if user[3] >= 200:
        update_user(user_id=callback.from_user.id, dick_size=user[2]+5, balance=user[3]-200)
        await callback.answer("✅ Куплено!", show_alert=True)
        await process_shop_menu(callback)
    else:
        await callback.answer("❌ Мало монет!", show_alert=True)

@dp.callback_query(F.data == "back_main")
async def process_back(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    await callback.message.edit_text(f"👋 Твой размер: <b>{user[2]} см</b>\nБаланс: {user[3]} 💰", reply_markup=main_private_kb())

@dp.message(Command("promo"))
async def promo_cmd(message: Message, command: CommandObject):
    if message.chat.type != 'private': return
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

# 5. Запуск
async def main():
    init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
