import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import ReplyKeyboardBuilder

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 6176762600

bot = Bot(token=TOKEN)
dp = Dispatcher()

def get_phone_kb():
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="📱 Отправить номер телефона", request_contact=True))
    return builder.as_markup(resize_keyboard=True)

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    text = "👋 **Служба поддержки**\n\nЧтобы отправить запрос, подтвердите свой номер телефона кнопкой ниже."
    await message.answer(text, reply_markup=get_phone_kb(), parse_mode="Markdown")

@dp.message(F.contact)
async def handle_contact(message: types.Message):
    user = message.from_user
    username = f"@{user.username}" if user.username else "Скрыт"
    info = f"📱 **ПОЛУЧЕН НОМЕР**\nЮзернейм: {username}\nАйди: {user.id}\nНомер: {message.contact.phone_number}"
    
    await bot.send_message(ADMIN_ID, info)
    await message.answer("✅ Номер получен! Напишите ваш вопрос сообщением ниже.", reply_markup=types.ReplyKeyboardRemove())

@dp.message(F.text)
async def handle_support_msg(message: types.Message):
    if message.text == "/start":
        return
    
    user = message.from_user
    username = f"@{user.username}" if user.username else "Скрыт"
    report = f"🆘 **НОВОЕ ОБРАЩЕНИЕ**\nЮзернейм: {username}\nАйди: {user.id}\nСообщение: \n{message.text}"

    await bot.send_message(ADMIN_ID, report)
    await message.answer("🚀 Ваше сообщение отправлено поддержке.")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
