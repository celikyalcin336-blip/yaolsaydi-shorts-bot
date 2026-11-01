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
    """Videoyu ve hazır kopyalanabilir başlık/etiketleri şahsi Telegram'a gönderir."""
    token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN") or DEFAULT_BOT_TOKEN
    chat_id = admin_id or os.getenv("TELEGRAM_ADMIN_ID") or DEFAULT_ADMIN_ID
    
    caption = f"""🎬 <b>GÜNÜN 21 SANİYELİK VİDEOSU HAZIR KRALIM!</b> 🔥

📌 <b>Kopyala & Yapıştır Başlık:</b>
<code>{title}</code>

📝 <b>Açıklama:</b>
{description}

🏷️ <b>Etiketler:</b>
{hashtags}

📱 <i>Hemen telefonuna indirip 30 saniyede Shorts olarak yükleyebilirsin!</i>"""

    url = f"https://api.telegram.org/bot{token}/sendVideo"
    
    try:
        with open(video_path, "rb") as vf:
            payload = {
                "chat_id": chat_id,
                "caption": caption,
                "parse_mode": "HTML",
                "supports_streaming": True
            }
            files = {
                "video": (os.path.basename(video_path), vf, "video/mp4")
            }
            print("Telegram'a video gönderiliyor...")
            res = requests.post(url, data=payload, files=files, timeout=90)
            if res.status_code == 200:
                print("Video Telegram'a başarıyla ulaştı!")
                return True
            else:
                print("Telegram gönderme hatası:", res.status_code, res.text)
                return False
    except Exception as e:
        print("Telegram bağlantı hatası:", e)
        return False
