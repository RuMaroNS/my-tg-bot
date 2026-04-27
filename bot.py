import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from supabase import create_client, Client

# --- КОНФИГ ---
TOKEN = "8630026221:AAGfuIfKQPdxSkyhU3IVCnRtRkKrlzKD0nk"
URL = "https://wbkygibviddkdjxbahbg.supabase.co"
KEY = "sb_publishable_l5wIAt6RrAl4Uo8uZKerRQ_xBYDS-Kv"

# Инициализация
bot = Bot(token=TOKEN)
dp = Dispatcher()
supabase: Client = create_client(URL, KEY)

logging.basicConfig(level=logging.INFO)

# --- АВТО-РЕГИСТРАЦИЯ ЧАТОВ ---
# Бот запоминает любой чат (группу, канал, личку), как только там что-то происходит
@dp.message()
@dp.my_chat_member()
@dp.channel_post()
async def auto_save_chat(event):
    chat = None
    if hasattr(event, 'chat'):
        chat = event.chat
    elif hasattr(event, 'message') and hasattr(event.message, 'chat'):
        chat = event.message.chat
        
    if chat:
        # Сохраняем ID чата в базу
        try:
            supabase.table("active_chats").upsert({"chat_id": chat.id}).execute()
        except Exception as e:
            print(f"Ошибка сохранения чата {chat.id}: {e}")

# --- ЦИКЛ МОНИТОРИНГА РОБЛОКСА ---
async def check_roblox_events():
    print("📡 Бабон-Глашатай запущен. Жду щелчок...")
    while True:
        try:
            # 1. Ищем новые щелчки в базе
            res = supabase.table("game_events").select("*").eq("status", "new").execute()
            
            if res.data:
                # 2. Достаем все чаты, которые бот успел запомнить
                chats_data = supabase.table("active_chats").select("chat_id").execute()
                all_targets = [c['chat_id'] for c in chats_data.data]

                for ev in res.data:
                    event_id = ev['id']
                    event_name = ev['event_name']
                    
                    # ТВОЙ ФОРМАТ СООБЩЕНИЯ
                    text = f"🚨 ЩЕЛЧОК ('{event_name}') БЫЛ ЗАПУЩЕН\n\nЗаходим в игру🎮"

                    print(f"Начинаю рассылку ивента: {event_name}")
                    
                    # 3. Рассылаем по всем чатам
                    for target_id in all_targets:
                        try:
                            await bot.send_message(target_id, text)
                        except Exception:
                            # Если бот кикнут или забанен — просто идем дальше
                            continue

                    # 4. Помечаем как готовое
                    supabase.table("game_events").update({"status": "done"}).eq("id", event_id).execute()
                    print(f"✅ Рассылка завершена!")

        except Exception as e:
            print(f"⚠️ Ошибка в цикле рассылки: {e}")
        
        await asyncio.sleep(5) # Проверка каждые 5 секунд

# --- ЗАПУСК ---
async def main():
    # Запускаем чекалку базы в фоне
    asyncio.create_task(check_roblox_events())
    # Запускаем сбор чатов
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен")
