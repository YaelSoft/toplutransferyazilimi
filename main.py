import os
import asyncio
from pyrogram import Client

# GitHub'dan gelen gizli bilgiler
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")

# Telefondan gireceğin bilgiler
SOURCE_LINK = os.environ.get("SOURCE_LINK") # Kaynak
DEST_LINK = os.environ.get("DEST_LINK")     # Hedef
OFFSET_ID = int(os.environ.get("OFFSET_ID", 0)) 

app = Client("my_worker", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING, in_memory=True)

# 🔥 GÜNCELLENMİŞ LİNK ÇÖZÜCÜ (KAYITLI MESAJLAR DESTEKLİ) 🔥
def get_chat_details(link):
    chat_id = None
    topic_id = None
    
    # Eğer "me" veya "kayitli" yazarsan Saved Messages olur
    if link.lower() in ["me", "kayitli", "saved"]:
        return "me", None

    try:
        if "t.me/c/" in link:
            parts = link.split("t.me/c/")[1].split("/")
            chat_id = int("-100" + parts[0])
            if len(parts) > 1:
                topic_id = int(parts[1].split("?")[0])
        elif "t.me/" in link: # Kullanıcı adı varsa (örn: t.me/arsiv_kanali)
            parts = link.split("t.me/")[1].split("/")
            chat_id = parts[0]
            if len(parts) > 1:
                topic_id = int(parts[1])
    except:
        pass
    return chat_id, topic_id

async def main():
    async with app:
        print("🚀 YAEL TRANSFER BAŞLATIYOR...")
        
        src_chat, src_topic = get_chat_details(SOURCE_LINK)
        dest_chat, dest_topic = get_chat_details(DEST_LINK)
        
        if not src_chat or not dest_chat:
            print("❌ Linkler hatalı! Özel grup linki veya 'me' yazmalısın.")
            return

        print(f"📤 Kaynak: {src_chat} (Topic: {src_topic})")
        print(f"📥 Hedef: {dest_chat} (Topic: {dest_topic})")
        print(f"⏩ Başlangıç Mesaj ID: {OFFSET_ID}")

        count = 0
        last_id = 0
        
        # reverse=True: Eskiden Yeniye doğru gider
        async for msg in app.get_chat_history(src_chat, message_thread_id=src_topic, reverse=True):
            
            if msg.id <= OFFSET_ID:
                continue

            last_id = msg.id 

            if msg.video or msg.photo or msg.document:
                try:
                    print(f"⬇️ İndiriliyor: Mesaj {msg.id}")
                    path = await app.download_media(msg)
                    
                    print(f"⬆️ Yükleniyor...")
                    await app.send_document(
                        chat_id=dest_chat, 
                        document=path, 
                        caption=msg.caption, 
                        message_thread_id=dest_topic
                    )
                    
                    os.remove(path)
                    count += 1
                    print(f"✅ Tamamlandı: {count}. Dosya (ID: {msg.id})")
                    
                    await asyncio.sleep(4) 

                except Exception as e:
                    print(f"⚠️ Hata (Msg {msg.id}): {e}")
                    await asyncio.sleep(5)
            
            if count % 10 == 0:
                print(f"--- 📌 ŞU ANKİ MESAJ ID: {last_id} (Not et!) ---")

        print("🏁 BU TUR BİTTİ! Tüm mesajlar tarandı.")

if __name__ == "__main__":
    app.run(main())
