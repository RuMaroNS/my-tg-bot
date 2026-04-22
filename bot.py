import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Настройка логов, чтобы видеть ошибки в консоли Bothost
logging.basicConfig(level=logging.INFO)

# Берем токен из Variables (обязательно назови её BOT_TOKEN на сайте)
TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

def main_kb():
    builder = InlineKeyboardBuilder()
    
    # 1 ряд: Те самые эмодзи в одну полоску
    builder.row(
        types.InlineKeyboardButton(text="🏀", callback_data="game_basket"),
        types.InlineKeyboardButton(text="⚽", callback_data="game_soccer"),
        types.InlineKeyboardButton(text="🎯", callback_data="game_darts"),
        types.InlineKeyboardButton(text=" bowling", callback_data="game_bowling"),
        types.InlineKeyboardButton(text="🎲", callback_data="game_dice"),
        types.InlineKeyboardButton(text="🎰", callback_data="game_slots")
    )
    
    # 2 ряд: Кнопки под эмодзи
    builder.row(
        types.InlineKeyboardButton(text="🚀 Быстрые", callback_data="btn_fast"),
        types.InlineKeyboardButton(text="Режимы 💣", callback_data="btn_modes")
    )
    
    # 3 ряд: Web App или ссылка
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
    
