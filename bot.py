import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# Берем из Variables на хостинге
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 6176762600

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Клавиатура с кнопкой телефона
def get_phone_kb():
    builder = ReplyKeyboardBuilder()
    builder.row(
        types.KeyboardButton(text="📱 Отправить номер телефона", request_contact=True)
    )
    return builder.as_markup(resize_keyboard=True)

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    await message.answer(
        "🔴 **Внимание!**\n\nЧтобы связаться с поддержкой, необходимо подтвердить свой номер телефона.",
        reply_markup=get_phone_kb(),
        parse_mode="Markdown"
    )

# Хендлер на получение номера
@dp.message(F.contact)
async def contact_handler(message: types.Message):
    # Уведомляем админа о новом контакте
    report = (
        f"👤 **Новый контакт в базе**\n"
        f"Юзер: @{message.from_user.username}\n"
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
    
