import os
import shutil
import subprocess

def get_ffmpeg_path():
    """Sistemde veya imageio_ffmpeg kütüphanesinde ffmpeg bulur."""
    which_ffmpeg = shutil.which("ffmpeg")
    if which_ffmpeg:
        return which_ffmpeg
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"

def build_video_short(
    image_paths: list,
    voice_path: str,
    subtitles_path: str,
    output_video_path: str,
    music_path: str = None,
    total_duration: float = 21.5
) -> bool:
    """
    4 sahne görselini ses ve güvenli altyazıyla birleştirip 1080x1920 Full HD video üretir.
    Altyazılar mobilde asla ekrandan taşmayacak şekilde sağ-sol 90px marjla yerleştirilir.
    """
    ffmpeg_exe = get_ffmpeg_path()
    output_dir = os.path.dirname(os.path.abspath(output_video_path))
    os.makedirs(output_dir, exist_ok=True)
    
    # subtitles.srt'nin olduğu klasörde çalıştırıyoruz ki FFmpeg doğrudan bulsun
    work_dir = os.path.dirname(os.path.abspath(subtitles_path))
    
    durations = [5.8, 5.6, 4.8, 5.3]
    if len(image_paths) != 4:
        per_img = total_duration / max(1, len(image_paths))
        durations = [per_img] * len(image_paths)
        
    concat_txt_path = os.path.join(work_dir, "concat_temp.txt")
    with open(concat_txt_path, "w", encoding="utf-8") as f:
        for idx, img_p in enumerate(image_paths):
            f.write(f"file '{img_p.replace(chr(92), '/')}'\n")
            f.write(f"duration {durations[idx]}\n")
        f.write(f"file '{image_paths[-1].replace(chr(92), '/')}'\n")
        
    srt_name = os.path.basename(subtitles_path)
    
    # Subtitle styling:
    # MarginL=90, MarginR=90 (Sağdan ve soldan 90 piksel güvenlik marjı - ASLA TAŞMAZ!)
    # MarginV=150 (Alttan 150 piksel yukarıda, Shorts UI butonlarının üstünde)
    # Fontsize=18, Bold=1, Sarı metin, Kalın siyah kontur
    sub_style = (
        "force_style='Fontname=Arial,Fontsize=18,Bold=1,"
        "PrimaryColour=&H0000FFFF,OutlineColour=&H00000000,BorderStyle=1,"
        "Outline=2.5,Shadow=1,Alignment=2,MarginV=150,MarginL=90,MarginR=90'"
    )
    
    # Filtre zinciri
    if music_path and os.path.exists(music_path):
        filter_complex = (
            f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,"
            f"subtitles={srt_name}:{sub_style}[v];"
            f"[1:a]volume=1.0[voice];"
            f"[2:a]volume=0.18,aloop=loop=-1:size=2e+09[bgm];"
            f"[voice][bgm]amix=inputs=2:duration=first[a]"
        )
        inputs = [
            "-i", concat_txt_path,
            "-i", voice_path,
            "-i", music_path
        ]
    else:
        filter_complex = (
            f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,"
            f"subtitles={srt_name}:{sub_style}[v];"
            f"[1:a]volume=1.0[a]"
        )
        inputs = [
            "-i", concat_txt_path,
            "-i", voice_path
        ]
        
    cmd = [
        ffmpeg_exe, "-y",
        "-f", "concat",
        "-safe", "0",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "20",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_video_path
    ]
    
    print(f"FFmpeg ile video montajlanıyor... (Hedef: {output_video_path})")
    res = subprocess.run(cmd, cwd=work_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode == 0 and os.path.exists(output_video_path):
        size_mb = os.path.getsize(output_video_path) / (1024 * 1024)
        print(f"Video montajı başarıyla tamamlandı! Boyut: {size_mb:.2f} MB")
        return True
    else:
        print("FFmpeg hatası:", res.stderr[-800:])
        return False
