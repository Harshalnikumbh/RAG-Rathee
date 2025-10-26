# whisper_transcribe.py
import whisper
import yt_dlp
from pathlib import Path
import re

def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '', filename)[:200]

def transcribe_missing_videos():
    """Automatically download audio and transcribe"""
    
    # Your missing video URLs (30-46)
    missing_videos = [
        "https://www.youtube.com/watch?v=NXVxDtvXZO8",
        "https://www.youtube.com/watch?v=KjiizZng_Y0",
        "https://www.youtube.com/watch?v=F_0H2TVywRQ",
        "https://www.youtube.com/watch?v=5Fk_yU1O6w8",
        "https://www.youtube.com/watch?v=-seG9em_m2Q",
        "https://www.youtube.com/watch?v=dUCIkax4jdM",
        "https://www.youtube.com/watch?v=TBE12bdWmQo",
        "https://www.youtube.com/watch?v=prrgCqv576c",
        "https://www.youtube.com/watch?v=sfju7EAukEs",
        "https://www.youtube.com/watch?v=051CBvanVwU",
        "https://www.youtube.com/watch?v=aAikZJvjFPw",
        "https://www.youtube.com/watch?v=zn0XD7HBs9s",
        "https://www.youtube.com/watch?v=gYWXC3vQ1rs",
        "https://www.youtube.com/watch?v=Swm72ewthlM",
        "https://www.youtube.com/watch?v=nnlyR5EdbIA",
        "https://www.youtube.com/watch?v=WEnaBfzu-ec",
        "https://www.youtube.com/watch?v=mmz67ouBhF4",
    ]
    
    # Load Whisper model
    print("🔄 Loading Whisper model...")
    model = whisper.load_model("base")
    print("✅ Model loaded!\n")
    
    output_dir = Path("transcripts")
    output_dir.mkdir(exist_ok=True)
    
    success = 0
    failed = []
    
    for idx, video_url in enumerate(missing_videos, 30):
        try:
            video_id = video_url.split("v=")[1].split("&")[0]
            print(f"[{idx}/46] Processing: {video_id}")
            
            # Temporary audio file path
            audio_path = Path(f"temp_audio_{video_id}.mp3")
            
            # Download audio using yt-dlp
            print("  📥 Downloading audio...")
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': str(audio_path.with_suffix('')),  # without extension
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                video_title = sanitize_filename(info.get('title', 'Unknown_Title'))
                downloaded_file = ydl.prepare_filename(info)
            
            # Transcribe with Whisper
            print(" Transcribing (this takes 1-3 minutes)...")
            result = model.transcribe(downloaded_file, language='en')
            transcript_text = result['text']
            
            # Save transcript
            filename = f"{idx:02d}_{video_title}_{video_id}.txt"
            filepath = output_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Video ID: {video_id}\n")
                f.write(f"URL: {video_url}\n")
                f.write(f"Title: {video_title}\n")
                f.write("-" * 80 + "\n\n")
                f.write(transcript_text)
            
            print(f"  ✅ Saved!\n")
            success += 1
            
            # Cleanup: Delete downloaded audio
            try:
                Path(downloaded_file).unlink()
            except:
                pass
            
        except Exception as e:
            print(f"  ❌ Failed: {str(e)[:100]}\n")
            failed.append(f"Video {idx}: {video_id}")
            continue
    
    # Summary
    print("=" * 60)
    print(f"✅ Successfully transcribed: {success}/17")
    print(f"❌ Failed: {len(failed)}/17")
    if failed:
        print("\nFailed videos:")
        for f in failed:
            print(f"  - {f}")

if __name__ == "__main__":
    transcribe_missing_videos()