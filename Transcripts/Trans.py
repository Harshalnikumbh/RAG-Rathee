from pytube import Playlist
from youtube_transcript_api import YouTubeTranscriptApi
import time
import re
from pathlib import Path
import random

def sanitize_filename(filename):
    """Remove invalid characters from filename"""
    return re.sub(r'[<>:"/\\|?*]', '', filename)[:200]

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

def main():
    playlist_url = "https://www.youtube.com/playlist?list=PL8828Z-IEhFGkz7F_paNquqsFyd357oYA"
    
    print("📥 Fetching playlist...")
    playlist = Playlist(playlist_url)
    
    # Create output directory
    output_dir = Path("transcripts")
    output_dir.mkdir(exist_ok=True)
    
    # Get video URLs first
    video_urls = list(playlist.video_urls)
    total_videos = len(video_urls)
    print(f"📋 Found {total_videos} videos in playlist\n")
    print("🔍 Fetching ENGLISH transcripts only\n")
    
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
            text = " ".join([entry.text for entry in transcript_list])
            
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
            
            # Save file
            filename = f"{idx:02d}_{video_title}_{video_id}.txt"
            filepath = output_dir / filename
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"Video ID: {video_id}\n")
                f.write(f"URL: {video_url}\n")
                f.write(f"Title: {video_title}\n")
                f.write(f"Duration: {duration}s\n")
                f.write(f"Transcript entries: {len(transcript_list)}\n")
                f.write(f"Language: English\n")
                f.write("-" * 80 + "\n\n")
                f.write(text)
            
            print(f"✅ Saved ({len(transcript_list)} entries) - English ✓\n")
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
                    text = " ".join([entry.text for entry in transcript_list])
                    
                    filename = f"{idx:02d}_Unknown_Title_{video_id}.txt"
                    filepath = output_dir / filename
                    
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(f"Video ID: {video_id}\n")
                        f.write(f"URL: {video_url}\n")
                        f.write(f"Language: English\n")
                        f.write("-" * 80 + "\n\n")
                        f.write(text)
                    
                    print(f"✅ Retry successful!\n")
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
    
    print(f"\n📁 All English transcripts saved in: {output_dir.absolute()}")
    print(f"🎯 Total English transcripts: {success_count}")

if __name__ == "__main__":
    main()