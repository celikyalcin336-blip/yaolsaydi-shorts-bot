import os
import re
import sys
import time
import urllib.parse
import requests
from PIL import Image

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def clean_and_upscale_to_fhd(image_path: str):
    """
    Görselin en boy oranını (9:16) milimetrik koruyarak alt köşedeki filigranı temizler
    ve doğrudan 1080x1920 Full HD stüdyo çözünürlüğüne Lanczos ile yükseltir.
    """
    try:
        with Image.open(image_path) as img:
            w, h = img.size
            if h > 200:
                # 9:16 oranını bozmadan sağ alt logoyu çıkarmak için simetrik kenar kırpma:
                # 10px soldan, 10px sağdan, 0px üstten, 35px alttan
                # 576 -> 556, 1024 -> 989 (556 / 989 = 0.56218, tam 9:16 oranı)
                crop_box = (10, 0, w - 10, h - 35)
                cropped = img.crop(crop_box)
                
                # 1080x1920 Full HD çözünürlüğe kristal netliğinde Lanczos yükseltme
                fhd_img = cropped.resize((1080, 1920), Image.Resampling.LANCZOS)
                fhd_img.save(image_path, "JPEG", quality=95)
                print(f"🧹 Görsel 1080x1920 Full HD stüdyo kalitesine yükseltildi: {image_path}")
    except Exception as e:
        print("Görsel işleme uyarısı:", e)

def generate_image_pollinations(prompt: str, output_path: str, max_attempts: int = 8) -> bool:
    """
    Pollinations FLUX modeli üzerinden ultra gerçekçi sinematik 9:16 görsel üretir.
    """
    if os.path.exists(output_path) and os.path.getsize(output_path) > 20000:
        print(f"Görsel zaten mevcut, atlanıyor: {output_path}")
        return True

    # Flux için optimize edilmiş yüksek gerçekçilik ve sinematik ışık komutları
    enhanced_prompt = (
        f"hyperrealistic vertical 9:16 cinematic shot, 8k resolution, award-winning cinematography, "
        f"volumetric lighting, photorealistic details, masterpiece, sharp focus, depth of field: {prompt}"
    )
    encoded = urllib.parse.quote(enhanced_prompt)
    seed = int(time.time() * 1000) % 999999
    
    # Flux modelini hedefle
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=768&height=1344&model=flux&nologo=true&seed={seed}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for attempt in range(1, max_attempts + 1):
        try:
            print(f"🎨 Flux Görsel üretiliyor (Deneme {attempt}/{max_attempts})...")
            resp = requests.get(url, headers=headers, timeout=60)
            
            if resp.status_code == 200 and len(resp.content) > 10000:
                with open(output_path, "wb") as f:
                    f.write(resp.content)
                # İndirilen görseli anında temizle ve 1080x1920 Full HD'ye çek
                clean_and_upscale_to_fhd(output_path)
                print(f"✅ Görsel başarıyla kaydedildi: {output_path} ({os.path.getsize(output_path)/1024:.1f} KB)")
                return True
                
            elif resp.status_code == 402:
                match = re.search(r"Retry after (\d+)s", resp.text)
                wait_sec = int(match.group(1)) + 3 if match else 46
                print(f"⏳ API Hız Limiti (402): {wait_sec} saniye bekleniyor...")
                time.sleep(wait_sec)
                
            elif resp.status_code == 503:
                print("⏳ Sunucu meşgul (503): 20 saniye bekleniyor...")
                time.sleep(20)
                
            else:
                print(f"Durum kodu: {resp.status_code}, 15s bekleniyor...")
                # Eğer flux yanıt vermiyorsa fallback olarak varsayılan turbo endpointini dene
                if attempt >= 3:
                    url = f"https://image.pollinations.ai/prompt/{encoded}?width=768&height=1344&nologo=true&seed={seed}"
                time.sleep(15)
                
        except Exception as e:
            print(f"Bağlantı hatası: {e}, 15s bekleniyor...")
            time.sleep(15)
            
    return False

def generate_all_scenes(scene_prompts: list, output_dir: str) -> list:
    """Tüm 4 sahnenin görsellerini üretir, temizler ve 1080x1920 HD olarak kaydeder."""
    os.makedirs(output_dir, exist_ok=True)
    paths = []
    
    for idx, prompt in enumerate(scene_prompts, 1):
        path = os.path.join(output_dir, f"scene_{idx}.jpg")
        print(f"\n--- Sahne {idx}/{len(scene_prompts)} Hazırlanıyor ---")
        
        already_cached = os.path.exists(path) and os.path.getsize(path) > 20000
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
                
        if not already_cached and idx < len(scene_prompts):
            print("Sonraki sahne için API soğutma beklemesi (46s)...")
            time.sleep(46)
            
    return paths

if __name__ == "__main__":
    test_out = r"C:\Users\celik\Desktop\yaolsaydi_bot\test_flux_engine.jpg"
    generate_image_pollinations("A majestic lion sitting on a throne of ice vertical shot", test_out)
