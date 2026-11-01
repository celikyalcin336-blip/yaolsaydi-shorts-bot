import json
import os
import sys
import time
import requests

# Windows konsolunda Türkçe karakterler
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import main
import scenarios_catalog

BOT_TOKEN = "8882292811:AAFLAsm5c7OBsnN8iVU2MWpwfPeTxwRGHMg"
ADMIN_ID = 1934709259

def send_text_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, json=payload, timeout=15)
    except Exception as e:
        print("Mesaj gönderme hatası:", e)

def handle_update(update):
    message = update.get("message")
    if not message:
        return
        
    chat = message.get("chat", {})
    chat_id = chat.get("id")
    text = (message.get("text") or "").strip()
    
    # Sadece admin (Yalçın) komut verebilir
    if chat_id != ADMIN_ID:
        send_text_message(chat_id, "⛔ Bu bot özel bir YouTube Shorts fabrikasıdır.")
        return

    print(f"📩 Komut alındı: {text}")

    if text.startswith("/start") or text.startswith("/yardim"):
        msg = (
            "👑 <b>Ya Olsaydı? 21s Video Fabrikası Emrinde Kralım!</b>\n\n"
            "Kullanabileceğin komutlar:\n"
            "👉 <b>/video_uret</b> : Sıradaki 21 saniyelik videoyu derleyip buraya atar.\n"
            "👉 <b>/video_uret [Konu]</b> : Belirttiğin özel konuda anında video üretir!\n\n"
            "<i>(Ayrıca her sabah saat 10:00'da buluttan otomatik video gelir.)</i>"
        )
        send_text_message(chat_id, msg)
        return

    if text.startswith("/video_uret") or text.startswith("/uret") or text.startswith("/video"):
        custom_topic = text.replace("/video_uret", "").replace("/uret", "").replace("/video", "").strip()
        
        if custom_topic:
            send_text_message(chat_id, f"🚀 <b>Emrin olur kralım!</b>\n\nÖzel konun: <i>'{custom_topic}'</i>\n21 saniyelik sinematik video hazırlanıyor, lütfen 1-2 dakika bekle... ⏳🎬")
        else:
            send_text_message(chat_id, "🚀 <b>Emrin olur kralım!</b>\n\nSıradaki bomba 21 saniyelik video hazırlanıyor. Görseller çiziliyor ve montajlanıyor, 1-2 dakika içinde geliyor... ⏳🎬")
            
        # Pipeline'ı çalıştır
        try:
            success = main.run_pipeline()
            if not success:
                send_text_message(chat_id, "⚠️ Video üretiminde bir aksaklık oldu kralım, lütfen tekrar dene.")
        except Exception as e:
            send_text_message(chat_id, f"⚠️ Hata oluştu: {e}")

def run_listener():
    print("=" * 60)
    print("🤖 TELEGRAM BOT DİNLEYİCİSİ BAŞLATILDI (Yalçın Çelik Özel)")
    print("=" * 60)
    print("Komutlar bekleniyor (/video_uret, /start)...")
    
    last_update_id = 0
    
    # Başlangıçta eski birikmiş güncellemeleri temizle
    try:
        init_res = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset=-1", timeout=10).json()
        if init_res.get("result"):
            last_update_id = init_res["result"][-1]["update_id"] + 1
    except Exception:
        pass

    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={last_update_id}&timeout=25"
            resp = requests.get(url, timeout=35).json()
            
            if resp.get("ok"):
                for upd in resp.get("result", []):
                    last_update_id = upd["update_id"] + 1
                    handle_update(upd)
                    
        except requests.exceptions.Timeout:
            continue
        except Exception as e:
            print("Dinleme hatası:", e)
            time.sleep(3)

if __name__ == "__main__":
    run_listener()
