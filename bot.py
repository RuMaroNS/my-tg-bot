import time
import asyncio
from aiogram import Bot
from supabase import create_client, Client

# Данные
TOKEN = "8630026221:AAGfuIfKQPdxSkyhU3IVCnRtRkKrlzKD0nk"
URL = "https://wbkygibviddkdjxbahbg.supabase.co"
KEY = "sb_publishable_l5wIAt6RrAl4Uo8uZKerRQ_xBYDS-Kv"

bot = Bot(token=TOKEN)
supabase: Client = create_client(URL, KEY)

async def check_and_broadcast():
    print("Мониторинг запущен. Жду событий из Roblox...")
    while True:
        try:
            # 1. Ищем новые события
            res = supabase.table("game_events").select("*").eq("status", "new").execute()
            events = res.data
            
            if events:
                # 2. Получаем список ID всех игроков из твоей базы
                user_res = supabase.table("profiles").select("user_id").execute()
                user_ids = [u['user_id'] for u in user_res.data]

                for ev in events:
                    text = f"🚨 **ГЛОБАЛЬНОЕ СОБЫТИЕ!**\n\nАктивирован: **{ev['event_name']}**\nВсе в игру! 🎮"
                    
                    for uid in user_ids:
                        try:
                            await bot.send_message(uid, text, parse_mode="Markdown")
                        except Exception:
                            pass # Если юзер заблокал бота

                    # 3. Метка, что всё отправили
                    supabase.table("game_events").update({"status": "done"}).eq("id", ev['id']).execute()
                    print(f"Уведомление '{ev['event_name']}' отправлено {len(user_ids)} игрокам.")

        except Exception as e:
            print(f"Ошибка: {e}")

        await asyncio.sleep(10) # Проверка каждые 10 секунд

if __name__ == "__main__":
    asyncio.run(check_and_broadcast())
