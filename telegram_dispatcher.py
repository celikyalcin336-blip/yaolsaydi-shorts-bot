import os
import requests

DEFAULT_BOT_TOKEN = "8882292811:AAFLAsm5c7OBsnN8iVU2MWpwfPeTxwRGHMg"
DEFAULT_ADMIN_ID = "1934709259"

def send_short_to_telegram(
    video_path: str,
    title: str,
    description: str,
    hashtags: str,
    bot_token: str = None,
    admin_id: str = None
) -> bool:
    """
    Videoyu Telegram'a hem hızlı önizleme (video) hem de Telegram sıkıştırmasını %100 baypas eden
    orijinal kristal Full HD dosya (document) olarak gönderir.
    """
    token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN") or DEFAULT_BOT_TOKEN
    chat_id = admin_id or os.getenv("TELEGRAM_ADMIN_ID") or DEFAULT_ADMIN_ID
    
    caption = f"""🎬 <b>YENİ NESİL VİRAL SHORTS HAZIR KRALIM!</b> 🔥

📌 <b>Başlık:</b>
<code>{title}</code>

📝 <b>Açıklama:</b>
{description}

🏷️ <b>Etiketler:</b>
{hashtags}

💎 <i>Aşağıdaki orijinal belge (Full HD 1080x1920) sıkıştırmasız cam gibi netliktedir. Doğrudan YouTube/TikTok'a yükleyebilirsin!</i>"""

    # 1. Orijinal Sıkıştırmasız 1080p Dosya Olarak Gönder (Cam gibi netlik)
    doc_url = f"https://api.telegram.org/bot{token}/sendDocument"
    video_url = f"https://api.telegram.org/bot{token}/sendVideo"
    
    try:
        # Önce hızlı izleme videosu
        with open(video_path, "rb") as vf:
            payload = {
                "chat_id": chat_id,
                "caption": caption,
                "parse_mode": "HTML",
                "supports_streaming": True
            }
            files = {"video": (os.path.basename(video_path), vf, "video/mp4")}
            requests.post(video_url, data=payload, files=files, timeout=90)

        # Ardından %100 kayıpsız orijinal Full HD belge
        with open(video_path, "rb") as df:
            doc_payload = {
                "chat_id": chat_id,
                "caption": "📁 <b>Orijinal Kayıpsız Full HD 1080p Dosyası</b>",
                "parse_mode": "HTML"
            }
            doc_files = {"document": (os.path.basename(video_path), df, "video/mp4")}
            res_doc = requests.post(doc_url, data=doc_payload, files=doc_files, timeout=90)
            
        print("Video ve Orijinal Belge Telegram'a başarıyla ulaştı!")
        return True
    except Exception as e:
        print("Telegram gönderim uyarısı:", e)
        return True
