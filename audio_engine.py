import asyncio
from datetime import timedelta
import os
import edge_tts

def split_sentence_into_chunks(text: str, max_words: int = 4, max_chars: int = 24) -> list:
    """Cümleyi mobilde ASLA taşmayacak 3-4 kelimelik kısa parçalara böler."""
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

def format_srt_time(td: timedelta) -> str:
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    millis = int(td.microseconds / 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"

async def generate_speech_and_safe_subtitles(script: str, output_mp3: str, output_srt: str, voice: str = "tr-TR-AhmetNeural") -> float:
    """
    Ahmet sesiyle tam 21 saniyeye göre seslendirir (+13% rate).
    Altyazıları taşmayacak şekilde kısa parçalara böler ve senkronize SRT oluşturur.
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
                
    # Gelen cümleleri alıp taşmayacak mikro-parçalara böl
    srt_lines = []
    cue_idx = 1
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
            
            srt_lines.append(str(cue_idx))
            srt_lines.append(f"{format_srt_time(c_start)} --> {format_srt_time(c_end)}")
            srt_lines.append(chunk_text)
            srt_lines.append("")
            cue_idx += 1

    with open(output_srt, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_lines))
        
    print(f"Ses ve Güvenli Altyazı hazırlandı! Süre: {total_duration:.2f}s, Altyazı parça sayısı: {len(srt_lines)//4}")
    return total_duration

def generate_audio(script: str, output_mp3: str, output_srt: str) -> float:
    return asyncio.run(generate_speech_and_safe_subtitles(script, output_mp3, output_srt))

if __name__ == "__main__":
    test_script = "Yarın sabah uyandığında tavana doğru süzüldüğünü fark etsen ne yapardın? 24 saat yerçekimi sıfırlanırsa her şey uçar!"
    generate_audio(test_script, r"C:\Users\celik\Desktop\yaolsaydi_bot\test_voice.mp3", r"C:\Users\celik\Desktop\yaolsaydi_bot\test_sub.srt")
