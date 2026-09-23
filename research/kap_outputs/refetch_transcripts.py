#!/usr/bin/env python3
"""
Resilient YouTube transcript fetcher with rate limiting, exponential backoff,
and user-agent rotation. Designed to handle 50+ videos without IP bans.

Usage:
    python3 refetch_transcripts.py                  # Re-fetch all failed transcripts
    python3 refetch_transcripts.py --all            # Re-fetch everything (skip existing good ones)
    python3 refetch_transcripts.py --test 1         # Test with just video 1
    python3 refetch_transcripts.py --range 16 62    # Re-fetch videos 16-62
"""

import os
import re
import sys
import time
import random
import argparse
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PROJECT_DIR = Path(__file__).resolve().parent.parent.parent  # gold-agent/
URLS_FILE = PROJECT_DIR / "research" / "kap_outputs" / "urls.txt"
TRANSCRIPTS_DIR = PROJECT_DIR / "research" / "kap_outputs" / "transcripts"

# Rate limiting: random delay between requests (seconds)
MIN_DELAY = 4
MAX_DELAY = 10

# After every BATCH_SIZE requests, take a longer pause
BATCH_SIZE = 8
BATCH_PAUSE_MIN = 30
BATCH_PAUSE_MAX = 60

# Exponential backoff on failure
MAX_RETRIES = 4
BACKOFF_BASE = 15  # seconds; retry delays: 15, 30, 60, 120

# User-Agent rotation pool (real browser user agents)
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/0.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/0.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/0.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/0.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/0.0.0.0 Safari/537.36 Edg/0.0.0.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:126.0) Gecko/20100101 Firefox/126.0",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_videos(urls_file: Path):
    """Parse urls.txt into a list of video dicts."""
    videos = []
    with open(urls_file) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("|")
            url = parts[0].strip()
            title = parts[1].strip() if len(parts) > 1 else "Unknown"
            channel = parts[2].strip() if len(parts) > 2 else "Unknown"
            views = parts[3].strip() if len(parts) > 3 else "?"
            date = parts[4].strip() if len(parts) > 4 else "?"
            reason = parts[5].strip() if len(parts) > 5 else ""

            video_id = None
            if "v=" in url:
                video_id = url.split("v=")[1].split("&")[0].split("#")[0]
            elif "youtu.be/" in url:
                video_id = url.split("youtu.be/")[1].split("?")[0]

            if video_id:
                videos.append({
                    "id": video_id,
                    "url": url,
                    "title": title,
                    "channel": channel,
                    "views": views,
                    "date": date,
                    "reason": reason,
                })
    return videos


def is_failed_transcript(filepath: Path) -> bool:
    """Check if a transcript file is a failed placeholder."""
    if not filepath.exists():
        return True
    content = filepath.read_text()[:600]
    if "NO TRANSCRIPT AVAILABLE" in content:
        return True
    if "YouTube is blocking" in content:
        return True
    if "## Transcript:" not in content:
        return True
    return False


def make_session(user_agent: str):
    """Create a requests.Session with a rotated User-Agent."""
    import requests
    session = requests.Session()
    session.headers.update({
        "User-Agent": user_agent,
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })
    return session


def fetch_one(video_id: str, session):
    """
    Fetch transcript for a single video using youtube-transcript-api v1.2.x.
    Returns the full text or None on failure.
    """
    from youtube_transcript_api import YouTubeTranscriptApi

    ytt = YouTubeTranscriptApi(http_client=session)

    # Try primary fetch
    try:
        transcript_data = ytt.fetch(video_id)
        return " ".join([snippet.text for snippet in transcript_data])
    except Exception:
        pass

    # Try listing available transcripts and fetching first available
    try:
        transcript_list = ytt.list(video_id)
        for t in transcript_list:
            try:
                fetched = t.fetch()
                texts = []
                for s in fetched:
                    if hasattr(s, "text"):
                        texts.append(s.text)
                    elif isinstance(s, dict):
                        texts.append(s.get("text", ""))
                    else:
                        texts.append(str(s))
                return " ".join(texts)
            except Exception:
                continue
    except Exception:
        pass

    return None


def fetch_with_backoff(video_id: str):
    """Fetch with exponential backoff and user-agent rotation on failure."""
    for attempt in range(MAX_RETRIES + 1):
        ua = random.choice(USER_AGENTS)
        session = make_session(ua)

        try:
            result = fetch_one(video_id, session)
            if result:
                return result
        except Exception as e:
            err_str = str(e).lower()
            is_ip_ban = "blocking" in err_str or "blocked" in err_str or "requestblocked" in err_str

            if is_ip_ban and attempt < MAX_RETRIES:
                delay = BACKOFF_BASE * (2 ** attempt) + random.uniform(0, 5)
                print(f"    IP blocked on attempt {attempt + 1}/{MAX_RETRIES + 1}. "
                      f"Backing off {delay:.0f}s...")
                time.sleep(delay)
                continue
            else:
                print(f"    Error: {e}")
                break

        # If fetch_one returned None (no transcript found, but no exception)
        if attempt < MAX_RETRIES:
            delay = BACKOFF_BASE * (2 ** attempt) + random.uniform(0, 5)
            print(f"    No transcript on attempt {attempt + 1}. Retrying in {delay:.0f}s...")
            time.sleep(delay)

    return None


def save_transcript(filepath: Path, video: dict, full_text: str):
    """Save a successful transcript."""
    words = full_text.split()
    quality_warnings = []
    if len(words) < 100:
        quality_warnings.append(f"Very short ({len(words)} words) - may be incomplete")
    sentences = full_text.split(".")
    avg_sentence_len = len(words) / max(1, len(sentences))
    if avg_sentence_len > 50:
        quality_warnings.append("Low punctuation - likely auto-generated")

    quality_note = ""
    if quality_warnings:
        quality_note = f"# Quality warnings: {'; '.join(quality_warnings)}\n"

    with open(filepath, "w") as f:
        f.write(f'# Title: {video["title"]}\n')
        f.write(f'# Channel: {video["channel"]}\n')
        f.write(f'# URL: {video["url"]}\n')
        f.write(f'# Views: {video["views"]}\n')
        f.write(f'# Uploaded: {video["date"]}\n')
        f.write(f'# Scout reason: {video["reason"]}\n')
        f.write(f'# Words: {len(words)}\n')
        if quality_note:
            f.write(quality_note)
        f.write(f"\n## Transcript:\n\n{full_text}\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Resilient YouTube transcript re-fetcher")
    parser.add_argument("--all", action="store_true", help="Process all videos (skip existing good transcripts)")
    parser.add_argument("--test", type=int, help="Test with a single video number")
    parser.add_argument("--range", nargs=2, type=int, metavar=("START", "END"),
                        help="Re-fetch a range of video numbers (inclusive)")
    parser.add_argument("--force", action="store_true", help="Overwrite even good transcripts")
    args = parser.parse_args()

    if not URLS_FILE.exists():
        print(f"ERROR: {URLS_FILE} not found")
        sys.exit(1)

    videos = load_videos(URLS_FILE)
    print(f"Loaded {len(videos)} videos from urls.txt")

    # Determine which videos to process
    if args.test:
        indices = [args.test - 1]
    elif args.range:
        indices = list(range(args.range[0] - 1, args.range[1]))
    else:
        indices = list(range(len(videos)))

    # Filter to only failed transcripts (unless --force)
    to_fetch = []
    for idx in indices:
        if idx >= len(videos):
            continue
        filepath = TRANSCRIPTS_DIR / f"video_{idx + 1:02d}.md"
        if args.force or is_failed_transcript(filepath):
            to_fetch.append(idx)
        else:
            print(f"  Skipping video {idx + 1:02d} - already has good transcript")

    print(f"\nWill fetch {len(to_fetch)} transcripts")
    print(f"Rate limiting: {MIN_DELAY}-{MAX_DELAY}s between requests, "
          f"{BATCH_PAUSE_MIN}-{BATCH_PAUSE_MAX}s pause every {BATCH_SIZE} requests")
    print(f"Retries: {MAX_RETRIES} with exponential backoff (base {BACKOFF_BASE}s)")
    print()

    succeeded = 0
    failed = 0
    failed_list = []

    for count, idx in enumerate(to_fetch):
        video = videos[idx]
        num = idx + 1
        filepath = TRANSCRIPTS_DIR / f"video_{num:02d}.md"

        print(f"[{count + 1}/{len(to_fetch)}] Video {num:02d}: {video['title'][:60]}...")

        # Rate limiting: delay between requests
        if count > 0:
            # Batch pause every BATCH_SIZE requests
            if count % BATCH_SIZE == 0:
                pause = random.uniform(BATCH_PAUSE_MIN, BATCH_PAUSE_MAX)
                print(f"  -- Batch pause: {pause:.0f}s (to avoid IP ban) --")
                time.sleep(pause)
            else:
                delay = random.uniform(MIN_DELAY, MAX_DELAY)
                print(f"  (waiting {delay:.1f}s)")
                time.sleep(delay)

        full_text = fetch_with_backoff(video["id"])

        if full_text:
            save_transcript(filepath, video, full_text)
            word_count = len(full_text.split())
            print(f"  OK - {word_count} words saved")
            succeeded += 1
        else:
            print(f"  FAILED - no transcript available")
            failed += 1
            failed_list.append(f"video_{num:02d}: {video['title'][:50]}")

    # Summary
    print(f"\n{'=' * 50}")
    print(f"RE-FETCH COMPLETE")
    print(f"Succeeded: {succeeded}/{len(to_fetch)}")
    print(f"Failed:    {failed}/{len(to_fetch)}")
    if failed_list:
        print(f"\nFailed videos:")
        for f_name in failed_list:
            print(f"  - {f_name}")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
