import os, random, requests, logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

logging.basicConfig(level=logging.INFO)

# Конфиг
TOKEN = os.getenv("BOT_TOKEN")
CF_TOKEN = os.getenv("CF_API_TOKEN")
CF_ACCOUNT_ID = "c75d835ea2ac37e6ba549eadbe375d94"
MODEL = "@cf/meta/llama-3-8b-instruct"
ADMIN_USERNAME = "R0bONE"

# Состояния чатов (в памяти)
chat_modes = {} # {chat_id: "toxic" | "chill" | "light"}

ZAPAS = "хуйлан, пидормот, уебище, долбоеб, блядота, шкура, даун, нищееб, выблядок, хуесос, мразь, помойка, хуепутало, залупа, дристун, гнида, чушпан, скуф, инцел, куколд, симп, npc, уебан, отброс, биомусор, байт на говно, слитый, лоутаб, нищ, бездарь, позорище, чурка, шлюха, еблан, затупок, выродок, мразота, пиздолиз, черт, чертила, опущенный, лох, терпила, сын шлюхи, мать сдохла, выкидыш, урод, гной, спермобак"

session = requests.Session()

async def get_babon_ai(user_text, mode="toxic"):
    url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/{MODEL}"
    headers = {"Authorization": f"Bearer {CF_TOKEN}"}
    
    # Формируем личность в зависимости от режима
    if mode == "chill":
        system_content = "Ты Бабон, сейчас ты на чилле. Общайся лениво, редко, без мата. Твой сленг: база, рил, пох."
    elif mode == "light":
        system_content = "Ты Бабон, веди себя попроще. Меньше оскорблений, больше иронии. Сленг 2026 года."
    else:
        system_content = (
            f"Ты Бабон, борзый зумер 2026 года. Твой базар живой, а не тупой. Огрызайся, унижай за тупость. "
            f"Используй органично этот словарь: {ZAPAS}. Не спамь словами, а вставляй их в тему. "
            "Если тебе хамят — уничтожай. Будь выблядком, но умным выблядком. КРАТКОСТЬ — ТВОЙ КОНЕК."
        )

    payload = {"messages": [{"role": "system", "content": system_content}, {"role": "user", "content": user_text}]}

    try:
        r = session.post(url, headers=headers, json=payload, timeout=12)
        ans = r.json().get("result", {}).get("response", "Че ты там мявкнул?")
        return ans
    except:
        return "Сервак сдох, нищ."

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    
    user = update.message.from_user.username
    chat_id = update.effective_chat.id
    text = update.message.text.lower()
    
    # 1. Личка
    if update.effective_chat.type == "private":
        keyboard = [[InlineKeyboardButton("Добавить в группу", url=f"https://t.me/{context.bot.username}?startgroup=true")]]
        await update.message.reply_text("В личке не базарю. Добавляй в чат по кнопке.", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # 2. Стоп-команды (только для админа)
    is_admin = (user == ADMIN_USERNAME)
    cmd_executed = False
    
    if is_admin:
        if "закрыл ебальник" in text and "бобон" in text:
            chat_modes[chat_id] = "chill"
            cmd_executed = True
        elif "потише будь" in text:
            chat_modes[chat_id] = "light"
            cmd_executed = True
        elif "бабон, фас" in text: # Вернуть в обычный режим
            chat_modes[chat_id] = "toxic"
            cmd_executed = True

    # 3. Логика ответов
    current_mode = chat_modes.get(chat_id, "toxic")
    chance = 0.3 if current_mode == "toxic" else 0.1
    
    names = ["бабон", "бобон", "жиробончик"]
    called = any(n in text for n in names) or "?" in text
    
    if called or random.random() < chance:
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        
        answer = await get_babon_ai(update.message.text, mode=current_mode)
        
        if cmd_executed:
            answer += " (оф)"
            
        await update.message.reply_text(answer)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_messages))
    print("БАБОН 2.0 В СЕТИ")
    app.run_polling(drop_pending_updates=True)
    
