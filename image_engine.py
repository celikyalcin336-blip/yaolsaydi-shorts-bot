import os
import re
import time
import urllib.parse
import requests

def generate_image_pollinations(prompt: str, output_path: str, max_attempts: int = 8) -> bool:
    """Pollinations AI üzerinden 9:16 görsel üretir. 402 veya 503 durumlarında dinamik bekler."""
    if os.path.exists(output_path) and os.path.getsize(output_path) > 10000:
        print(f"Görsel zaten mevcut, atlanıyor: {output_path}")
        return True

    enhanced_prompt = f"{prompt}, photorealistic, 8k resolution, cinematic lighting, dramatic depth of field"
    encoded = urllib.parse.quote(enhanced_prompt)
    seed = int(time.time() * 1000) % 999999
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=768&height=1344&nologo=true&seed={seed}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for attempt in range(1, max_attempts + 1):
        try:
            print(f"Görsel üretiliyor (Deneme {attempt}/{max_attempts})...")
            resp = requests.get(url, headers=headers, timeout=60)
            
            if resp.status_code == 200 and len(resp.content) > 10000:
                with open(output_path, "wb") as f:
                    f.write(resp.content)
                print(f"Görsel başarıyla kaydedildi: {output_path} ({len(resp.content)/1024:.1f} KB)")
                return True
                
            elif resp.status_code == 402:
                match = re.search(r"Retry after (\d+)s", resp.text)
                wait_sec = int(match.group(1)) + 4 if match else 46
                print(f"Hız limiti (402): {wait_sec} saniye bekleniyor...")
                time.sleep(wait_sec)
                
            elif resp.status_code == 503:
                print("Sunucu meşgul (503): 20 saniye bekleniyor...")
                time.sleep(20)
                
            else:
                print(f"Durum kodu: {resp.status_code}, 15s bekleniyor...")
                time.sleep(15)
                
        except Exception as e:
            print(f"Bağlantı hatası: {e}, 15s bekleniyor...")
            time.sleep(15)
            
    return False

def generate_all_scenes(scene_prompts: list, output_dir: str) -> list:
    """Tüm 4 sahnenin görsellerini üretir. Başarısızlık durumunda akıllı telafi yapar."""
    os.makedirs(output_dir, exist_ok=True)
    paths = []
    
    for idx, prompt in enumerate(scene_prompts, 1):
        path = os.path.join(output_dir, f"scene_{idx}.jpg")
        print(f"\n--- Sahne {idx}/{len(scene_prompts)} Hazırlanıyor ---")
        
        already_cached = os.path.exists(path) and os.path.getsize(path) > 10000
        success = generate_image_pollinations(prompt, path)
        if success:
            paths.append(path)
        else:
            print(f"Uyarı: Sahne {idx} üretilemedi, telafi görseli atanıyor...")
            if paths:
                fallback_path = paths[-1]
                paths.append(fallback_path)
            else:
                return []
                
        # Eğer görsel yeni indirildiyse ve son sahne değilse bekleme yap
        if not already_cached and idx < len(scene_prompts):
            print("Sonraki sahne için API soğutma beklemesi (46s)...")
            time.sleep(46)
            
    return paths
