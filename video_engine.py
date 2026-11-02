import os
import shutil
import subprocess
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

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

def render_scene_clip(
    ffmpeg_exe: str,
    image_path: str,
    output_clip_path: str,
    duration: float,
    motion_type: int = 0,
    fps: int = 25
) -> bool:
    """
    Tek bir görselden akıcı Ken Burns kamera hareketi ve sinematik geçiş efekti üretir.
    motion_type:
      0: Yavaş Yakınlaşma (Slow Zoom In) - Giriş / Kanca
      1: Yavaş Uzaklaşma (Slow Zoom Out) - Geniş Açı / Keşif
      2: Kayma ve Yakınlaşma (Pan & Zoom) - Kaos / Olay
      3: Hızlı Doruk Yakınlaşması (Punch Climax Zoom) - Sonuç / Çağrı
    """
    total_frames = int(duration * fps) + 5
    fade_duration = 0.35
    fade_out_start = max(0.1, duration - fade_duration)
    
    # 25 fps'de kare başına zoom artış katsayısı
    if motion_type == 0:
        # Slow Zoom In + Fade Out
        zoom_expr = "zoompan=z='min(zoom+0.0012,1.18)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
        fade_expr = f"fade=t=out:st={fade_out_start:.2f}:d={fade_duration:.2f}"
        vf = f"{zoom_expr}:d={total_frames}:s=1080x1920:fps={fps},{fade_expr}"
        
    elif motion_type == 1:
        # Slow Zoom Out + Fade In + Fade Out
        zoom_expr = "zoompan=z='max(1.18-0.0012*on,1.0)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
        fade_expr = f"fade=t=in:st=0:d={fade_duration:.2f},fade=t=out:st={fade_out_start:.2f}:d={fade_duration:.2f}"
        vf = f"{zoom_expr}:d={total_frames}:s=1080x1920:fps={fps},{fade_expr}"
        
    elif motion_type == 2:
        # Pan Left-to-Right & Zoom + Fade In + Fade Out
        zoom_expr = "zoompan=z='min(zoom+0.0010,1.16)':x='if(lte(on,1),(iw-iw/zoom)/2,min(x+0.6,iw-iw/zoom))':y='ih/2-(ih/zoom/2)'"
        fade_expr = f"fade=t=in:st=0:d={fade_duration:.2f},fade=t=out:st={fade_out_start:.2f}:d={fade_duration:.2f}"
        vf = f"{zoom_expr}:d={total_frames}:s=1080x1920:fps={fps},{fade_expr}"
        
    else:
        # Punch Climax Zoom In + Fade In
        zoom_expr = "zoompan=z='min(zoom+0.0016,1.22)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
        fade_expr = f"fade=t=in:st=0:d={fade_duration:.2f}"
        vf = f"{zoom_expr}:d={total_frames}:s=1080x1920:fps={fps},{fade_expr}"

    cmd = [
        ffmpeg_exe, "-y",
        "-loop", "1",
        "-i", image_path,
        "-vf", vf,
        "-t", f"{duration:.2f}",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "ultrafast",
        output_clip_path
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return res.returncode == 0 and os.path.exists(output_clip_path)

def build_video_short(
    image_paths: list,
    voice_path: str,
    subtitles_path: str,
    output_video_path: str,
    music_path: str = None,
    total_duration: float = 21.5
) -> bool:
    """
    4 sahne görselini Ken Burns kamera dinamizmi, pürüzsüz geçişler, stüdyo ses miksajı
    ve Montserrat fontlu modern viral altyazıyla 1080x1920 Full HD sinematik videoya dönüştürür.
    """
    ffmpeg_exe = get_ffmpeg_path()
    work_dir = os.path.dirname(os.path.abspath(subtitles_path))
    bot_dir = os.path.dirname(os.path.dirname(work_dir)) if "temp_build" in work_dir else os.path.dirname(os.path.abspath(__file__))
    fonts_dir = os.path.join(bot_dir, "assets", "fonts")
    
    os.makedirs(work_dir, exist_ok=True)
    os.makedirs(os.path.dirname(os.path.abspath(output_video_path)), exist_ok=True)
    
    num_scenes = len(image_paths)
    if num_scenes == 4:
        # Shorts ritmine göre optimize süre dağılımı
        # Sahne 1 (Kanca): 5.5s, Sahne 2 (Gelişme): 5.5s, Sahne 3 (Kaos): 5.0s, Sahne 4 (Doruk): 5.5s
        base_durations = [5.5, 5.5, 5.0, 5.5]
        factor = total_duration / sum(base_durations)
        durations = [d * factor for d in base_durations]
    else:
        per_img = total_duration / max(1, num_scenes)
        durations = [per_img] * num_scenes

    # 1. Her sahne için Ken Burns klip üretimi
    rendered_clips = []
    print(f"🎬 {num_scenes} sahne için sinematik Ken Burns kamera hareketleri işleniyor...")
    for idx, img_path in enumerate(image_paths):
        clip_path = os.path.join(work_dir, f"scene_clip_{idx+1}.mp4")
        motion = idx % 4
        success = render_scene_clip(
            ffmpeg_exe=ffmpeg_exe,
            image_path=img_path,
            output_clip_path=clip_path,
            duration=durations[idx],
            motion_type=motion
        )
        if not success:
            print(f"HATA: Sahne {idx+1} klip montajı başarısız!")
            return False
        rendered_clips.append(clip_path)

    # 2. Klipleri birleştirme listesi (concat demuxer)
    concat_txt_path = os.path.join(work_dir, "concat_scenes.txt")
    with open(concat_txt_path, "w", encoding="utf-8") as f:
        for c_path in rendered_clips:
            f.write(f"file '{c_path.replace(chr(92), '/')}'\n")

    combined_visual = os.path.join(work_dir, "combined_visual.mp4")
    concat_cmd = [
        ffmpeg_exe, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_txt_path,
        "-c", "copy",
        combined_visual
    ]
    res_concat = subprocess.run(concat_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res_concat.returncode != 0 or not os.path.exists(combined_visual):
        print("HATA: Klipler birleştirilemedi:", res_concat.stderr[-400:])
        return False

    # 3. Altyazı ve Ses Miksajı
    ass_rel_path = os.path.basename(subtitles_path)
    fonts_rel = os.path.relpath(fonts_dir, work_dir).replace(chr(92), '/')
    fonts_filter_arg = f":fontsdir='{fonts_rel}'" if os.path.exists(fonts_dir) else ""
    video_filter = f"[0:v]subtitles={ass_rel_path}{fonts_filter_arg}[v]"

    # Stüdyo kalitesinde ses işleme:
    # 1. Seslendirme kompresörle güçlendirilir (tüm kelimeler net ve yüksek çıkar)
    # 2. Arka plan gerilim müziği sesin altına gömülür (ducking), looplanır ve yumuşak fade-in/out yapılır
    if music_path and os.path.exists(music_path):
        fade_out_music_st = max(1.0, total_duration - 1.5)
        filter_complex = (
            f"{video_filter};"
            f"[1:a]acompressor=threshold=-16dB:ratio=3:attack=5:release=50,volume=1.25[voice];"
            f"[2:a]volume=0.13,aloop=loop=-1:size=2e+09,afade=t=in:st=0:d=1.0,afade=t=out:st={fade_out_music_st:.2f}:d=1.5[bgm];"
            f"[voice][bgm]amix=inputs=2:duration=first:dropout_transition=2[a]"
        )
        inputs = [
            "-i", combined_visual,
            "-i", voice_path,
            "-i", music_path
        ]
    else:
        filter_complex = (
            f"{video_filter};"
            f"[1:a]acompressor=threshold=-16dB:ratio=3:attack=5:release=50,volume=1.25[a]"
        )
        inputs = [
            "-i", combined_visual,
            "-i", voice_path
        ]

    cmd_final = [
        ffmpeg_exe, "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "19",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_video_path
    ]

    print(f"🎞️ Full HD 1080x1920 video montajlanıyor... (Hedef: {output_video_path})")
    res_final = subprocess.run(cmd_final, cwd=work_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res_final.returncode == 0 and os.path.exists(output_video_path):
        size_mb = os.path.getsize(output_video_path) / (1024 * 1024)
        print(f"✨ VİDEO MONTAJI TAMAMLANDI! Boyut: {size_mb:.2f} MB")
        return True
    else:
        print("FFmpeg Montaj Hatası:", res_final.stderr[-800:])
        return False
