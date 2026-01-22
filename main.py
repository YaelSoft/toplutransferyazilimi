import os
import asyncio
from pyrogram import Client

# --- GITHUB'DAN GELEN BİLGİLER ---
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")

# --- TELEFONDAN GİRECEĞİN LİNKLER ---
SOURCE_LINK = os.environ.get("SOURCE_LINK") # Kaynak Topic
DEST_LINK = os.environ.get("DEST_LINK")     # Hedef Topic
OFFSET_ID = int(os.environ.get("OFFSET_ID", 0)) # Kaldığın yer

# --- AYARLAR ---
MAX_SIZE_MB = 350
MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024 

app = Client("koy_iscisi", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING, in_memory=True)

def get_chat_details(link):
    """ Linkten Chat ID ve Topic ID çeker """
    chat_id = None
    topic_id = None
    try:
        if "t.me/c/" in link:
            parts = link.split("t.me/c/")[1].split("/")
            chat_id = int("-100" + parts[0])
            if len(parts) > 1:
                topic_id = int(parts[1].split("?")[0])
    except:
        pass
    return chat_id, topic_id

def get_file_size(msg):
    """ Mesajdaki dosyanın boyutunu bulur """
    if msg.video: return msg.video.file_size
    elif msg.document: return msg.document.file_size
    elif msg.photo: return 1 # Fotoğraflar her zaman küçüktür
    elif msg.audio: return msg.audio.file_size
    elif msg.voice: return msg.voice.file_size
    return 0

async def main():
    async with app:
        print("🚜 KÖY MODU: TRANSFER BAŞLIYOR...")
        print(f"🛑 Boyut Sınırı: {MAX_SIZE_MB} MB")
        
        src_chat, src_topic = get_chat_details(SOURCE_LINK)
        dest_chat, dest_topic = get_chat_details(DEST_LINK)
        
        if not src_chat or not dest_chat:
            print("❌ LİNKLER HATALI! 'https://t.me/c/...' formatında olmalı.")
            return

        print(f"📤 Kaynak ID: {src_chat} | Topic: {src_topic}")
        print(f"📥 Hedef ID: {dest_chat} | Topic: {dest_topic}")
        print(f"⏩ Başlangıç: {OFFSET_ID}. mesajdan sonrası")

        count = 0
        last_processed_id = OFFSET_ID
        
        # reverse=True: En eskiden en yeniye doğru
        async for msg in app.get_chat_history(src_chat, message_thread_id=src_topic, reverse=True):
            
            # Kaldığımız yerden devam etme kontrolü
            if msg.id <= OFFSET_ID:
                continue

            last_processed_id = msg.id 

            # Medya Kontrolü
            if msg.video or msg.photo or msg.document or msg.audio:
                
                # 1. BOYUT KONTROLÜ (350 MB)
                f_size = get_file_size(msg)
                if f_size > MAX_SIZE_BYTES:
                    mb_size = f_size / 1024 / 1024
                    print(f"⚠️ ATLANIYOR (Büyük Dosya): {mb_size:.2f} MB | ID: {msg.id}")
                    continue

                # 2. İNDİR & YÜKLE
                try:
                    print(f"⬇️ İndiriliyor ({f_size / 1024 / 1024:.1f} MB)... ID: {msg.id}")
                    path = await app.download_media(msg)
                    
                    print(f"⬆️ Hedefe Yükleniyor...")
                    
                    # Doğru medya türüyle gönder
                    if msg.video:
                        await app.send_video(dest_chat, path, caption=msg.caption, message_thread_id=dest_topic)
                    elif msg.photo:
                        await app.send_photo(dest_chat, path, caption=msg.caption, message_thread_id=dest_topic)
                    elif msg.document:
                        await app.send_document(dest_chat, path, caption=msg.caption, message_thread_id=dest_topic)
                    elif msg.audio:
                        await app.send_audio(dest_chat, path, caption=msg.caption, message_thread_id=dest_topic)
                    
                    os.remove(path)
                    count += 1
                    print(f"✅ Başarılı! Toplam: {count}")
                    
                    # Ban yememek için bekleme
                    await asyncio.sleep(4) 

                except Exception as e:
                    print(f"❌ HATA (Msg {msg.id}): {e}")
                    await asyncio.sleep(5)
            
            # GitHub logunda son ID'yi görmek için (6 saat dolunca lazım olur)
            if count % 20 == 0:
                print(f"--- 📌 SON İŞLENEN MESAJ ID: {last_processed_id} ---")

        print("🏁 İŞLEM BİTTİ! Topic sonuna gelindi.")

if __name__ == "__main__":
    app.run(main())
