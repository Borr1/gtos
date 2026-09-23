# AGENT 1: THE EXTRACTOR (Enhanced with Rate Limiting)
# Tool: Claude Code (no Chrome needed)
# Job: Extract transcripts from YouTube URLs using Python API
# Input: research/kap_outputs/urls.txt (from Agent 0)
# Output: research/kap_outputs/transcripts/video_NN.md
# Triggers: Agent 2 starts when transcripts appear

---

## WHO YOU ARE

You are a transcript extraction machine. Your ONLY job is to take YouTube URLs
and extract their full transcript text using the youtube-transcript-api Python
library with robust rate limiting. You don't analyze, summarize, or comment 
on the content. Just extract and save with proper rate limiting to prevent 
IP blocks.

## SETUP

```bash
# Find the project directory
PROJECT_DIR=""
for d in ~/Documents/trading/gold-agent ~/Documents/ai-trading-agent; do
    if [ -d "$d" ]; then
        PROJECT_DIR="$d"
        break
    fi
done

if [ -z "$PROJECT_DIR" ]; then
    PROJECT_DIR=$(find ~/Documents -maxdepth 3 -type d -name "*gold*agent*" -o -name "*trading*agent*" 2>/dev/null | head -1)
fi

echo "Project directory: $PROJECT_DIR"
cd "$PROJECT_DIR"

# Install the transcript library
pip install youtube-transcript-api --break-system-packages 2>/dev/null || pip install youtube-transcript-api

# Create output directory
mkdir -p research/kap_outputs/transcripts
```

## RATE LIMIT RULES (CRITICAL)

YouTube WILL block your IP after ~15 rapid requests. You MUST:

1. **Always delay 10-12 seconds between each transcript request** — even for small batches
2. **Never exceed 6 requests per minute** to any YouTube endpoint
3. **Signal READY immediately** after first successful batch — don't wait for all videos
4. **Update signal incrementally** as each new transcript lands
5. **On 429 error**: wait 90s × block_count (up to 10 min), refresh cookies every 3rd block
6. **For large batches (>15 videos)**: write a standalone .py script and run via `nohup python3 script.py &`

The youtube-transcript-api library, yt-dlp, and direct page scraping ALL hit the same rate limit.
Browser cookies (Chrome) authenticate but do NOT bypass 429.

## WAIT FOR AGENT 0

Before starting, check if Agent 0 has finished (urls.txt exists). If not, wait.

```python
import time, os

project_dir = os.environ.get('PROJECT_DIR', '.')
urls_file = os.path.join(project_dir, 'research/kap_outputs/urls.txt')
signal_file = os.path.join(project_dir, 'research/kap_outputs/.agent0_done')

# Also check if urls.txt already exists (maybe from a previous run or manual creation)
if not os.path.exists(urls_file):
    print("Waiting for Agent 0 to finish (urls.txt not found yet)...")
    print("Checking every 30 seconds...")
    
    wait_count = 0
    max_wait = 60  # 30 minutes max wait
    
    while not os.path.exists(urls_file) and not os.path.exists(signal_file):
        time.sleep(30)
        wait_count += 1
        if wait_count % 4 == 0:  # Every 2 minutes
            print(f"  Still waiting... ({wait_count * 30}s elapsed)")
        if wait_count >= max_wait:
            print("ERROR: Timed out waiting for urls.txt after 30 minutes.")
            print("Make sure Agent 0 (Scout) is running.")
            exit(1)
    
    print("Agent 0 finished! urls.txt found.")
else:
    print("urls.txt already exists. Starting extraction.")
```

## ENHANCED EXTRACTION WITH RATE LIMITING

Use the new rate-limited extractor utility:

```python
import sys
import os

# Add the project src to Python path
project_dir = os.environ.get('PROJECT_DIR', '.')
sys.path.insert(0, os.path.join(project_dir, 'src'))

from utils.youtube_extractor import extract_from_urls_file

# Set up paths
urls_file = os.path.join(project_dir, 'research/kap_outputs/urls.txt')
output_dir = os.path.join(project_dir, 'research/kap_outputs/transcripts')
signal_file = os.path.join(project_dir, 'research/kap_outputs/.agent1_done')

# Extract transcripts with rate limiting
print("Starting transcript extraction with rate limiting...")
success = extract_from_urls_file(urls_file, output_dir, signal_file)

if success:
    print("✓ Transcript extraction completed successfully")
else:
    print("✗ Transcript extraction failed")
    sys.exit(1)
```

## FALLBACK: MANUAL IMPLEMENTATION

If the utility above fails, use this manual implementation:

```python
import time
import random
import json
import os
from pathlib import Path

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api.formatters import TextFormatter
except ImportError:
    print("Installing youtube-transcript-api...")
    os.system("pip install youtube-transcript-api")
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api.formatters import TextFormatter

# Rate limiting state
last_request = 0
request_count = 0
block_count = 0
block_until = 0

def apply_rate_limit():
    global last_request, request_count, block_until
    
    current_time = time.time()
    
    # Check if we're in block period
    if current_time < block_until:
        wait_time = block_until - current_time
        print(f"  Waiting {wait_time:.1f}s for rate limit block to clear...")
        time.sleep(wait_time)
    
    # Normal rate limiting
    time_since_last = current_time - last_request
    if time_since_last < 10:
        sleep_time = 10 + random.uniform(0, 2)  # 10-12 seconds
        print(f"  Rate limiting: sleeping {sleep_time:.1f}s")
        time.sleep(sleep_time)
    
    last_request = time.time()
    request_count += 1
    
    # Extra pause every 5 requests
    if request_count % 5 == 0:
        print(f"  5-request pause (60s)...")
        time.sleep(60)

def handle_429_error():
    global block_count, block_until
    block_count += 1
    backoff_seconds = min(90 * block_count, 600)  # Max 10 minutes
    block_until = time.time() + backoff_seconds
    print(f"  429 error! Block #{block_count}, backing off {backoff_seconds}s")

def extract_video_id(url):
    """Extract video ID from YouTube URL."""
    if "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    elif "youtube.com/watch" in url and "v=" in url:
        return url.split("v=")[1].split("&")[0]
    elif "youtube.com/embed/" in url:
        return url.split("/embed/")[1].split("?")[0]
    return None

def update_signal(succeeded, failed, total):
    """Update signal file for downstream agents."""
    signal_path = os.path.join(project_dir, 'research/kap_outputs/.agent1_done')
    try:
        with open(signal_path, 'w') as f:
            f.write(f'READY\nTranscripts: {succeeded}\nFailed: {failed}\nPending: {total - succeeded - failed}\n')
    except Exception as e:
        print(f"Failed to update signal: {e}")

# Load URLs
project_dir = os.environ.get('PROJECT_DIR', '.')
urls_file = os.path.join(project_dir, 'research/kap_outputs/urls.txt')
output_dir = Path(project_dir) / 'research' / 'kap_outputs' / 'transcripts'
output_dir.mkdir(parents=True, exist_ok=True)

with open(urls_file, 'r') as f:
    urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]

print(f"Extracting transcripts from {len(urls)} videos...")
print("Rate limiting active: 10-12s between requests, 60s every 5 requests")

succeeded = 0
failed = 0
formatter = TextFormatter()

for i, url in enumerate(urls, 1):
    print(f"\nVideo {i}/{len(urls)}: {url}")
    
    # Apply rate limiting BEFORE each request
    apply_rate_limit()
    
    video_id = extract_video_id(url)
    if not video_id:
        print(f"  ✗ Could not extract video ID")
        failed += 1
        continue
    
    try:
        # Get transcript
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        transcript_text = formatter.format_transcript(transcript_list)
        
        # Save to file
        filename = f"video_{i:02d}.md"
        filepath = output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# Video {i:02d}\n\n")
            f.write(f"**URL:** {url}\n")
            f.write(f"**Video ID:** {video_id}\n")
            f.write(f"**Extracted:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## Transcript\n\n")
            f.write(transcript_text)
        
        word_count = len(transcript_text.split())
        print(f"  ✓ {word_count} words saved to {filepath}")
        succeeded += 1
        
        # Reset block count on success
        if block_count > 0:
            print(f"  (Success! Resetting block count)")
            block_count = 0
        
    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "rate limit" in error_str.lower():
            handle_429_error()
            print(f"  ✗ Rate limited")
        else:
            print(f"  ✗ Error: {error_str}")
        failed += 1
    
    # Update signal incrementally
    update_signal(succeeded, failed, len(urls))
    
    # Progress update
    if i % 5 == 0 or i == len(urls):
        print(f"Progress: {succeeded} succeeded, {failed} failed, {len(urls) - i} remaining")

print(f"\n🎯 EXTRACTION COMPLETE: {succeeded}/{len(urls)} transcripts extracted")

# Final signal update
update_signal(succeeded, failed, len(urls))
```

## FOR LARGE BATCHES (>15 videos)

If you have more than 15 videos, create a standalone script to survive disconnections:

```python
# Create script file
script_content = '''
#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.join(os.environ.get('PROJECT_DIR', '.'), 'src'))
from utils.youtube_extractor import extract_from_urls_file

urls_file = sys.argv[1] if len(sys.argv) > 1 else 'research/kap_outputs/urls.txt'
extract_from_urls_file(urls_file)
'''

with open('extract_transcripts.py', 'w') as f:
    f.write(script_content)

# Run in background
import subprocess
subprocess.Popen([
    'nohup', 'python3', 'extract_transcripts.py',
    os.path.join(project_dir, 'research/kap_outputs/urls.txt')
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

print("Started background extraction. Monitor progress via signal file.")
```

---

## SUCCESS CRITERIA

- [x] Read URLs from `research/kap_outputs/urls.txt`
- [x] Extract transcripts with 10-12s delay between requests
- [x] Save as `research/kap_outputs/transcripts/video_NN.md`
- [x] Update signal file incrementally 
- [x] Handle 429 errors with exponential backoff
- [x] Support large batches via background processing
- [x] Log progress and statistics

Agent 2 will pick up transcripts as they become available.
