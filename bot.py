import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# Настройка логирования для консоли Bothost
logging.basicConfig(level=logging.INFO)

# Берем токен из Variables на сайте Bothost
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 6176762600

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Функция для кнопки телефона
def get_phone_kb():
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="📱 Отправить номер телефона", request_contact=True))
    return builder.as_markup(resize_keyboard=True)

# Команда /start
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 **Служба поддержки**\n\nЧтобы отправить запрос, подтвердите свой номер телефона кнопкой ниже.",
        reply_markup=get_phone_kb(),
        parse_mode="Markdown"
    )

# Прием контакта
@dp.message(F.contact)
async def handle_contact(message: types.Message):
    user = message.from_user
    username = f"@{user.username}" if user.username else "Скрыт"
    
    # Сообщение админу
    text_to_admin = (
        f"📱 **ПОЛУЧЕН НОМЕР**\n"
        f"Юзернейм: {username}\n"
        f"Айди пользователя: {user.id}\n"
        f"Номер телефона: {message.contact.phone_number}"
    )
    
    await bot.send_message(ADMIN_ID, text_to_admin)
    await message.answer(
        "✅ Номер получен! Теперь напишите ваш вопрос текстом ниже.",
        reply_markup=types.ReplyKeyboardRemove()
    )

# Прием текстового сообщения
@dp.message(F.text)
async def handle_support_msg(message: types.Message):
    if message.text == "/start":
        return

    user = message.from_user
    username = f"@{user.username}" if user.username else "Скрыт"

    # Формируем сообщение для саппорта
    report = (
        f"🆘 **НОВОЕ ОБРАЩЕНИЕ**\n"
        f"Юзернейм: {username}\n"
        f"Айди пользователя: {user.id}\n"
        f"Сообщение: \n{message.text}"
    )

    await bot.send_message(ADMIN_ID, report)
    await message.answer("🚀 Ваше сообщение отправлено поддержке.")

async def main():
    # Удаляем старые сообщения, которые накопились пока бот был офлайн
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    )
    await bot.send_message(ADMIN_ID, text_to_admin, parse_mode="Markdown")
    
    # Говорим юзеру писать вопрос
    await message.answer(
        "✅ Спасибо! Теперь напишите ваше сообщение (текст), и оно будет передано оператору.",
        reply_markup=types.ReplyKeyboardRemove()
    )

# Когда юзер пишет текст (после старта или контакта)
@dp.message(F.text)
async def handle_support_msg(message: types.Message):
    if message.text == "/start":
        return

    # Формируем отчет для саппорта
    report = (
        f"🆘 **ОБРАЩЕНИЕ**\n"
        f"От: @{message.from_user.username or 'нет'}\n"
        f"ID: `{message.from_user.id}`\n"
        f"Сообщение:\n{message.text}"
    )

    await bot.send_message(ADMIN_ID, report, parse_mode="Markdown")
    await message.answer("🚀 Ваше сообщение отправлено. Ожидайте ответа.")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
        f"ID: `{message.from_user.id}`\n"
        f"Номер: `{message.contact.phone_number}`"
    )
    await bot.send_message(ADMIN_ID, report, parse_mode="Markdown")
    
    # Подтверждаем юзеру
    await message.answer(
        "✅ Номер получен! Теперь напишите ваш вопрос, и саппорт ответит вам в ближайшее время.",
        reply_markup=types.ReplyKeyboardRemove()
    )

# Хендлер на текстовые сообщения (только после отправки контакта)
@dp.message(F.text)
async def support_handler(message: types.Message):
    if message.text == "/start":
        return

    # Данные для саппорта
    report = (
        f"🆘 **НОВОЕ ОБРАЩЕНИЕ**\n\n"
        f"👤 **Юзернейм:** @{message.from_user.username if message.from_user.username else 'Скрыт'}\n"
        f"🆔 **Айди:** `{message.from_user.id}`\n"
        f"💬 **Сообщение:** \n{message.text}"
    )

    try:
        await bot.send_message(ADMIN_ID, report, parse_mode="Markdown")
        await message.answer("🚀 Ваше сообщение доставлено саппорту.")
    except Exception as e:
        await message.answer("❌ Ошибка отправки. Попробуйте позже.")
        print(f"Ошибка: {e}")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    )

# Хендлер на любые текстовые сообщения (пересылка саппорту)
@dp.message(F.text)
async def forward_to_admin(message: types.Message):
    user = message.from_user
    # Пытаемся получить контакт из данных (если он уже был отправлен ранее)
    phone = "Не указан"
    
    # Формируем текст для саппорта
    report_text = (
        f"🆘 **НОВОЕ ОБРАЩЕНИЕ**\n\n"
        f"👤 **Юзернейм:** @{user.username if user.username else 'нет'}\n"
        f"🆔 **Айди пользователя:** `{user.id}`\n"
        f"📩 **Сообщение:** \n{message.text}"
    )
    
    try:
        await bot.send_message(ADMIN_ID, report_text, parse_mode="Markdown")
        await message.answer("✅ Ваше сообщение отправлено поддержке. Ожидайте ответа.")
    except Exception as e:
        await message.answer("❌ Ошибка при отправке. Попробуйте позже.")
        print(f"Ошибка: {e}")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    builder.row(
        types.InlineKeyboardButton(text="🕹 Играть в WEB", url="https://t.me/telegram")
    )
    
    # 4 ряд: Кнопка ставки
    builder.row(
        types.InlineKeyboardButton(text="✏️ Изменить ставку", callback_data="btn_bet")
    )
    
    return builder.as_markup()

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    await message.answer(
        "🎮 **ДАВАЙ НАЧНЕМ ИГРАТЬ!**\n\n"
        "💰 **Баланс:** 190 m₵\n"
        "💸 **Ставка:** 10 m₵\n\n"
        "👇 *Выбери игру и начинай!*",
        reply_markup=main_kb(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("game_"))
async def handle_games(callback: types.CallbackQuery):
    emoji_dict = {
        "game_basket": "🏀", "game_soccer": "⚽", "game_darts": "🎯",
        "game_bowling": "🎳", "game_dice": "🎲", "game_slots": "🎰"
    }
    # Отправляем кубик/мяч/слоты
    await callback.message.answer_dice(emoji=emoji_dict[callback.data])
    # Убираем состояние загрузки на кнопке
    await callback.answer()

@dp.callback_query(F.data.startswith("btn_"))
async def handle_menu(callback: types.CallbackQuery):
    if callback.data == "btn_bet":
        await callback.answer("Окно изменения ставки откроется скоро!", show_alert=True)
    else:
        await callback.answer("Режим в разработке...")

async def main():
    # Удаляем вебхуки перед запуском (важно для чистого старта)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
async def start(message: types.Message):
    await message.answer(
        "🎮 **ДАВАЙ НАЧНЕМ ИГРАТЬ!**\n\n💰 **Баланс:** 0 m₵\n💸 **Ставка:** 10 m₵",
        reply_markup=get_keyboard(),
        parse_mode="Markdown"
    )

@dp.callback_query(lambda c: c.data.startswith('g_'))
async def play(callback: types.CallbackQuery):
    emoji_dict = {
        "g_basket": "🏀", "g_soccer": "⚽", "g_darts": "🎯",
        "g_bowling": "🎳", "g_dice": "🎲", "g_slots": "🎰"
    }
    # Кидает кубик в ответ на нажатие эмодзи
    await callback.message.answer_dice(emoji=emoji_dict[callback.data])
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
