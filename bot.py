import os
import random
import requests
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# Логи для отладки в панели Bothost
logging.basicConfig(level=logging.INFO)

# Конфиг
TOKEN = os.getenv("BOT_TOKEN")
CF_TOKEN = os.getenv("CF_API_TOKEN")
CF_ACCOUNT_ID = "c75d835ea2ac37e6ba549eadbe375d94"
MODEL = "@cf/meta/llama-3-8b-instruct" # Твои новые мозги

async def get_babon_response(user_text):
    url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/{MODEL}"
    headers = {"Authorization": f"Bearer {CF_TOKEN}"}
    
    # Промпт для Ламы, чтобы она стала Бабоном
    payload = {
        "messages": [
            {
                "role": "system", 
                "content": "Ты — Бабон, агрессивный зумер. Хами, используй сленг: скуф, кринж, ливни. Отвечай коротко и дерзко."
            },
            {"role": "user", "content": user_text}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        data = response.json()
        
        if data.get("success"):
            return data["result"]["response"]
        else:
            logging.error(f"Ошибка CF: {data}")
            return "Слышь, даже Лама от тебя в ахуе. (Ошибка API)"
    except Exception as e:
        logging.error(f"Ошибка сети: {e}")
        return "Бабон прилег отдохнуть, неси пиво."

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    
    text = update.message.text.lower()
    # Реагирует на имя или шанс 20%
    if "бабон" in text or random.random() < 0.2:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        answer = await get_babon_response(update.message.text)
        await update.message.reply_text(answer)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_messages))
    print("Бабон-Лама запущен!")
    app.run_polling()
        
