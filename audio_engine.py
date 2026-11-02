import asyncio
from datetime import timedelta
import os
import re
import sys
import edge_tts

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def split_sentence_into_chunks(text: str, max_words: int = 4, max_chars: int = 24) -> list:
    """Cümleyi dikey videoda ASLA taşmayacak 2-4 kelimelik vuruşlu parçalara böler."""
    words = text.split()
    chunks = []
    current_chunk = []
    current_len = 0
    
    for word in words:
        if len(current_chunk) >= max_words or (current_len + len(word) + 1 > max_chars and current_chunk):
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_len = len(word)
        else:
            current_chunk.append(word)
            current_len += len(word) + 1
            
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    return chunks

def format_ass_time(td: timedelta) -> str:
    """ASS formatı için süre: H:MM:SS.cs"""
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    centis = int(td.microseconds / 10000)
    return f"{hours}:{minutes:02d}:{seconds:02d}.{centis:02d}"

HIGHLIGHT_KEYWORDS = {
    "yok", "tükenseydi", "sıfırlansa", "altın", "karanlık", "savaş",
    "bomba", "dünya", "türkiye", "felaket", "uçar", "kaç", "ölüm",
    "son", "su", "para", "asla", "hemen", "tavan", "patlama", "dolar",
    "elektrik", "okul", "insan", "zaman", "durursa", "çöker", "uyan"
}

def highlight_viral_text(text: str) -> str:
    """Önemli kelimeleri dikkat çeken sarı/altın renkle vurgular."""
    words = text.split()
    formatted = []
    for w in words:
        clean_w = re.sub(r'[^\w]', '', w.lower())
        if clean_w in HIGHLIGHT_KEYWORDS or clean_w.startswith("türk"):
            # Sarı/Altın tonu: ASS BGR formatında &H00E5FF& (parlak sarı)
            formatted.append(r"{\c&H00E5FF&}" + w + r"{\c&H00FFFFFF&}")
        else:
            formatted.append(w)
    return " ".join(formatted).upper()

async def generate_speech_and_safe_subtitles(
    script: str,
    output_mp3: str,
    output_ass: str,
    voice: str = "tr-TR-AhmetNeural"
) -> float:
    """
    Ahmet sesiyle tam 21 saniyelik Shorts temposuna göre seslendirir (+13% rate).
    Modern ASS formatında kelime vurgulu, Montserrat-Black uyumlu altyazı üretir.
    Dönen değer: Ses süresi (saniye).
    """
    communicate = edge_tts.Communicate(script, voice, rate="+13%", pitch="+0Hz")
    submaker = edge_tts.SubMaker()
    
    with open(output_mp3, "wb") as file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                file.write(chunk["data"])
            elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                submaker.feed(chunk)
                
    ass_events = []
    total_duration = 0.0
    
    for sub in submaker.cues:
        start_td = sub.start
        end_td = sub.end
        duration_sec = (end_td - start_td).total_seconds()
        total_duration = max(total_duration, end_td.total_seconds())
        
        chunks = split_sentence_into_chunks(sub.content)
        if not chunks:
            continue
            
        chunk_duration = duration_sec / len(chunks)
        
        for i, chunk_text in enumerate(chunks):
            c_start = start_td + timedelta(seconds=i * chunk_duration)
            c_end = start_td + timedelta(seconds=(i + 1) * chunk_duration)
            
            styled_text = highlight_viral_text(chunk_text)
            event_line = f"Dialogue: 0,{format_ass_time(c_start)},{format_ass_time(c_end)},Default,,0,0,0,,{styled_text}"
            ass_events.append(event_line)

    ass_header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Montserrat-Black,64,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,6,3,2,80,80,380,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    with open(output_ass, "w", encoding="utf-8") as f:
        f.write(ass_header + "\n".join(ass_events) + "\n")
        
    print(f"🎙️ Ses ve Modern Altyazı hazırlandı! Süre: {total_duration:.2f}s, Parça sayısı: {len(ass_events)}")
    return total_duration

def generate_audio(script: str, output_mp3: str, output_ass: str) -> float:
    return asyncio.run(generate_speech_and_safe_subtitles(script, output_mp3, output_ass))

if __name__ == "__main__":
    test_script = "Yarın sabah uyandığında tavana doğru süzüldüğünü fark etsen ne yapardın? 24 saat yerçekimi sıfırlanırsa her şey uçar!"
    generate_audio(test_script, r"C:\Users\celik\Desktop\yaolsaydi_bot\test_voice.mp3", r"C:\Users\celik\Desktop\yaolsaydi_bot\test_sub.ass")
