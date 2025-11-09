from pytube import Playlist
from youtube_transcript_api import YouTubeTranscriptApi
import time
import re
from pathlib import Path
import random
import json

def sanitize_filename(filename):
    """Remove invalid characters from filename"""
    return re.sub(r'[<>:"/\\|?*]', '', filename)[:200]

def clean_text(text):
    """
    Clean text by removing unwanted characters and formatting
    """
    # Replace newlines with spaces
    text = text.replace('\n', ' ')
    # Remove backslashes
    text = text.replace('\\', '')
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)
    # Strip leading/trailing whitespace
    text = text.strip()
    return text

def get_english_transcript(api, video_id):
    """Try to get English transcript (US or UK)"""
    # Try different English variants
    for lang_code in ['en', 'en-GB', 'en-US']:
        try:
            return api.fetch(video_id, languages=[lang_code])
        except:
            continue
    
    # If no English found, raise error
    raise Exception("No English transcript available")

def create_chunks(transcript_list, chunk_duration_seconds=30, overlap_seconds=5):
    """
    Split transcript into chunks with overlap to maintain context.
    
    Args:
        transcript_list: List of transcript entries with 'text', 'start', 'duration'
        chunk_duration_seconds: Target duration per chunk in seconds (default: 30)
        overlap_seconds: Overlap duration in seconds (default: 5)
    
    Returns:
        List of chunks with chunk_id, text, start_time, end_time
    """
    if not transcript_list:
        return []
    
    chunks = []
    chunk_id = 1
    i = 0
    
    while i < len(transcript_list):
        chunk_start_time = transcript_list[i].start
        chunk_text = ""
        chunk_entries = []
        
        # Collect entries for this chunk
        j = i
        while j < len(transcript_list):
            entry = transcript_list[j]
            entry_end = entry.start + entry.duration
            
            # Add entry if it's within chunk duration
            if entry.start - chunk_start_time < chunk_duration_seconds:
                cleaned_text = clean_text(entry.text)
                if chunk_text:
                    chunk_text += " " + cleaned_text
                else:
                    chunk_text = cleaned_text
                chunk_entries.append(entry)
                j += 1
            else:
                break
        
        # Create chunk if we have text
        if chunk_text:
            chunk_end_time = chunk_entries[-1].start + chunk_entries[-1].duration
            
            chunks.append({
                "chunk_id": chunk_id,
                "text": chunk_text,
                "start_time": round(chunk_start_time / 60, 2),  # Convert to minutes
                "end_time": round(chunk_end_time / 60, 2)  # Convert to minutes
            })
            chunk_id += 1
        
        # Move to next chunk with overlap
        # Find the entry that starts at (chunk_start_time + chunk_duration - overlap)
        overlap_start_time = chunk_start_time + chunk_duration_seconds - overlap_seconds
        
        # Find next starting position with overlap
        next_i = i
        for k in range(i, len(transcript_list)):
            if transcript_list[k].start >= overlap_start_time:
                next_i = k
                break
        else:
            # If no entry found, move to the end
            next_i = len(transcript_list)
        
        # Ensure we're making progress
        if next_i <= i:
            next_i = i + 1
        
        i = next_i
    
    return chunks

def main():
    playlist_url = "https://www.youtube.com/playlist?list=PL8828Z-IEhFFejp6N8hTc3Gdub3R9_7Pv"
    
    print("📥 Fetching playlist...")
    playlist = Playlist(playlist_url)
    
    # Create output directory
    output_dir = Path("transcripts_json")
    output_dir.mkdir(exist_ok=True)
    
    # Get video URLs first
    video_urls = list(playlist.video_urls)
    total_videos = len(video_urls)
    print(f"📋 Found {total_videos} videos in playlist\n")
    print("🔍 Fetching ENGLISH transcripts only\n")
    print("📦 Creating chunked JSON outputs (30-second chunks with 5-second overlap)\n")
    
    # Create API instance
    api = YouTubeTranscriptApi()
    
    success_count = 0
    failed_videos = []
    no_english = []
    ip_blocked_count = 0
    
    for idx, video_url in enumerate(video_urls, 1):
        video_id = None
        try:
            # Extract video ID from URL
            video_id = video_url.split("v=")[1].split("&")[0]
            
            print(f"[{idx}/{total_videos}] Processing: {video_id}...")
            
            # Get ENGLISH transcript only
            transcript_list = get_english_transcript(api, video_id)
            
            # Try to get title (optional)
            video_title = "Unknown_Title"
            duration = "Unknown"
            try:
                from pytube import YouTube
                yt = YouTube(video_url)
                video_title = sanitize_filename(yt.title)
                duration = yt.length
            except:
                pass
            
            # Create chunks (30 seconds with 5-second overlap)
            chunks = create_chunks(transcript_list, chunk_duration_seconds=30, overlap_seconds=5)
            
            # Create full text with additional cleaning
            full_text = " ".join([chunk["text"] for chunk in chunks])
            full_text = clean_text(full_text)
            
            # Build JSON structure
            duration_minutes = round(duration / 60, 2) if isinstance(duration, (int, float)) else "Unknown"
            output_data = {
                "video_id": video_id,
                "video_url": video_url,
                "video_title": video_title,
                "duration_minutes": duration_minutes,
                "total_chunks": len(chunks),
                "chunk_duration_seconds": 30,
                "overlap_seconds": 5,
                "language": "English",
                "chunks": chunks,
                "full_text": full_text
            }
            
            # Save JSON file with ensure_ascii=False to handle special characters
            filename = f"{idx:02d}_{video_title}_{video_id}.json"
            filepath = output_dir / filename
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Saved {len(chunks)} chunks ({len(transcript_list)} entries) - English ✓")
            print(f"   📄 {filename}\n")
            success_count += 1
            
            # Longer delays to avoid IP ban (3-5 seconds)
            delay = random.uniform(3, 5)
            print(f"⏳ Waiting {delay:.1f}s...\n")
            time.sleep(delay)
            
        except Exception as e:
            error_str = str(e)
            
            # Track no English transcript separately
            if "No English transcript available" in error_str:
                no_english.append(f"Video {idx} (ID: {video_id})")
                print(f"⚠️  No English transcript available\n")
                continue
            
            # Check if IP blocked
            if "blocking requests from your IP" in error_str:
                ip_blocked_count += 1
                print(f"🛑 IP BLOCKED! Pausing for 2 minutes...")
                time.sleep(120)  # Wait 2 minutes
                
                # Retry once
                try:
                    transcript_list = get_english_transcript(api, video_id)
                    chunks = create_chunks(transcript_list, chunk_duration_seconds=30, overlap_seconds=5)
                    full_text = " ".join([chunk["text"] for chunk in chunks])
                    full_text = clean_text(full_text)
                    
                    output_data = {
                        "video_id": video_id,
                        "video_url": video_url,
                        "video_title": "Unknown_Title",
                        "duration_minutes": "Unknown",
                        "total_chunks": len(chunks),
                        "chunk_duration_seconds": 30,
                        "overlap_seconds": 5,
                        "language": "English",
                        "chunks": chunks,
                        "full_text": full_text
                    }
                    
                    filename = f"{idx:02d}_Unknown_Title_{video_id}.json"
                    filepath = output_dir / filename
                    
                    with open(filepath, "w", encoding="utf-8") as f:
                        json.dump(output_data, f, indent=2, ensure_ascii=False)
                    
                    print(f"✅ Retry successful! Saved {len(chunks)} chunks\n")
                    success_count += 1
                    time.sleep(5)
                    continue
                except:
                    pass
            
            error_msg = f"Video {idx} (ID: {video_id}): {error_str[:100]}"
            failed_videos.append(error_msg)
            print(f"❌ Error: {error_str[:150]}\n")
            continue
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 FINAL SUMMARY")
    print("=" * 80)
    print(f"✅ Successfully downloaded: {success_count}/{total_videos}")
    print(f"⚠️  No English transcript: {len(no_english)}/{total_videos}")
    print(f"❌ Other failures: {len(failed_videos)}/{total_videos}")
    
    if ip_blocked_count > 0:
        print(f"\n🛑 IP blocked {ip_blocked_count} time(s)")
        print("   ⏰ Wait 1-2 hours before retrying")
    
    if no_english:
        print("\n⚠️  Videos without English transcripts:")
        for video in no_english[:10]:
            print(f"  - {video}")
        if len(no_english) > 10:
            print(f"  ... and {len(no_english) - 10} more")
    
    if failed_videos:
        print("\n❌ Failed videos (other errors):")
        for failed in failed_videos[:5]:
            print(f"  - {failed}")
        if len(failed_videos) > 5:
            print(f"  ... and {len(failed_videos) - 5} more")
        
        # Save failed IDs
        with open("failed_videos.txt", "w") as f:
            for video in failed_videos:
                f.write(video + "\n")
        print(f"\n💾 Failed IDs saved to: failed_videos.txt")
    
    print(f"\n📁 All JSON transcripts saved in: {output_dir.absolute()}")
    print(f"🎯 Total JSON files created: {success_count}")
    print(f"📦 Each file contains chunked transcript data with 5-second overlap for context")

if __name__ == "__main__":
    main()
    