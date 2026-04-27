import os
import random
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from huggingface_hub import InferenceClient

# Токены
TOKEN = os.getenv("BOT_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

# Инициализация клиента
client = InferenceClient(model="meta-llama/Meta-Llama-3.1-8B-Instruct", token=HF_TOKEN)

logging.basicConfig(level=logging.INFO)

# ИСПРАВЛЕНО: Название функции теперь совпадает с вызовом
async def get_babon_ai_logic(user_text, mood):
    if mood == "evil":
        system_msg = (
            "Ты — Бабон, агрессивный зумер-хам. Твоя мать — шлюха, и ты постоянно об этом напоминаешь другим. "
            "Используй лютый зумерский сленг: скуф, альтушка, ливни, кринж, тюбик. "
            "Будь максимально токсичным, матерись, хами. Отвечай коротко, как в телеге."
        )
    else:
        system_msg = (
            "Ты — добрый Бабон, бро на чилле. Ты любишь всех в чате, называешь их родными. "
            "Используй сленг: чиназес, вайб, сигма, легенда. Отвечай коротко."
        )

    try:
        response = client.chat_completion(
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_text}
            ],
            max_tokens=100,
            temperature=1.0
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Ошибка генерации: {e}")
        return random.choice(["Слышь, ИИ прилег, но ты всё равно скуф.", "Ливни, нейронка сдохла."])

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        return

    if not update.message or not update.message.text:
        return

    text = update.message.text.lower()
    
    is_called = any(name in text for name in ["бабон", "бобон"])
    is_random = random.random() < 0.20 

    if is_called or is_random:
        mood = "evil" if random.random() < 0.7 else "good"
        
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        # Теперь функция точно определена!
        answer = await get_babon_ai_logic(update.message.text, mood)
        await update.message.reply_text(answer)

if __name__ == '__main__':
    if not TOKEN or not HF_TOKEN:
        print("Заполни переменные на Bothost!")
    else:
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_messages))
        print("Бабон запущен без ошибок!")
        app.run_polling()
    
