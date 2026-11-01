import json
import os
import shutil
import sys
import time

# Windows konsolunda Türkçe karakterler
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import scenarios_catalog
import image_engine
import audio_engine
import video_engine
import telegram_dispatcher

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_PATH = os.path.join(BASE_DIR, "history.json")
MUSIC_PATH = os.path.join(BASE_DIR, "assets", "music", "ambient_suspense.mp3")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
TEMP_DIR = os.path.join(BASE_DIR, "temp_build")

def load_history():
    if os.path.exists(HISTORY_PATH):
        try:
            with open(HISTORY_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"total_generated": 0, "past_topics": []}

def save_history(history):
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def run_pipeline():
    print("=" * 60)
    print("🎬 YA OLSAYDI? 21 SANİYELİK VİDEO FABRİKASI BAŞLATILDI")
    print("=" * 60)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    # 1. Konu Seçimi
    history = load_history()
    past_topics = set(history.get("past_topics", []))
    scenario = scenarios_catalog.get_next_scenario(past_topics)
    
    print(f"📌 Seçilen Konu: {scenario['title']}")
    print(f"📝 Senaryo Metni:\n{scenario['script']}\n")
    
    # 2. Ses ve Altyazı Üretimi
    voice_path = os.path.join(TEMP_DIR, "voice.mp3")
    subtitles_path = os.path.join(TEMP_DIR, "subtitles.srt")
    print("🎙️ Seslendirme ve Güvenli Altyazı üretiliyor...")
    duration = audio_engine.generate_audio(scenario["script"], voice_path, subtitles_path)
    print(f"⏱️ Ses Süresi: {duration:.2f} saniye")
    
    # 3. Görsel Üretimi (4 Sahne)
    print("🎨 4 Sahnenin sinematik 9:16 görselleri üretiliyor...")
    image_paths = image_engine.generate_all_scenes(scenario["scene_prompts"], TEMP_DIR)
    if len(image_paths) < 4:
        print("HATA: Görsellerin tamamı üretilemedi!")
        return False
        
    # 4. Video Montajı
    timestamp = int(time.time())
    output_mp4 = os.path.join(OUTPUT_DIR, f"ya_olsaydi_{scenario['id']}_{timestamp}.mp4")
    print("🎞️ Full HD 1080x1920 video derleniyor...")
    build_success = video_engine.build_video_short(
        image_paths=image_paths,
        voice_path=voice_path,
        subtitles_path=subtitles_path,
        output_video_path=output_mp4,
        music_path=MUSIC_PATH if os.path.exists(MUSIC_PATH) else None,
        total_duration=duration
    )
    
    if not build_success:
        print("HATA: Video montajı başarısız!")
        return False
        
    # 5. Telegram'a Gönderim
    print("🚀 Video Telegram'a iletiliyor...")
    send_success = telegram_dispatcher.send_short_to_telegram(
        video_path=output_mp4,
        title=scenario["title"],
        description=scenario["description"],
        hashtags=scenario["hashtags"]
    )
    
    if send_success:
        # Geçmişe kaydet
        history["past_topics"].append(scenario["topic"])
        history["total_generated"] = history.get("total_generated", 0) + 1
        save_history(history)
        print("✅ GÜNÜN VİDEOSU BAŞARIYLA TAMAMLANDI VE TELEGRAM'A ULAŞTI!")
    else:
        print("⚠️ Video üretildi fakat Telegram gönderiminde sorun oluştu.")
        
    # Geçici dosyaları temizle
    try:
        shutil.rmtree(TEMP_DIR)
    except Exception:
        pass
        
    return True

if __name__ == "__main__":
    run_pipeline()
