#!/usr/bin/env python3
"""Background transcript extractor for batch 2 (videos 16-62).
Runs slowly to avoid YouTube rate limits. 12s between requests, auto-backoff on 429."""

import requests, re, html, time, os
import browser_cookie3

project_dir = '/Users/borr/Documents/trading/gold-agent'
urls_file = os.path.join(project_dir, 'research/kap_outputs/urls.txt')
transcripts_dir = os.path.join(project_dir, 'research/kap_outputs/transcripts')
log_file = os.path.join(project_dir, 'research/kap_outputs/.agent1_bg_log.txt')

def log(msg):
    ts = time.strftime('%H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(log_file, 'a') as f:
        f.write(line + '\n')

# Parse URLs
videos = []
with open(urls_file) as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.split('|')
        url = parts[0].strip()
        title = parts[1].strip() if len(parts) > 1 else 'Unknown'
        channel = parts[2].strip() if len(parts) > 2 else 'Unknown'
        views = parts[3].strip() if len(parts) > 3 else '?'
        date = parts[4].strip() if len(parts) > 4 else '?'
        reason = parts[5].strip() if len(parts) > 5 else ''

        video_id = None
        if 'v=' in url:
            video_id = url.split('v=')[1].split('&')[0].split('#')[0]
        elif 'youtu.be/' in url:
            video_id = url.split('youtu.be/')[1].split('?')[0]

        if video_id:
            videos.append({
                'id': video_id, 'url': url, 'title': title,
                'channel': channel, 'views': views, 'date': date, 'reason': reason
            })

def make_session():
    cj = browser_cookie3.chrome(domain_name='.youtube.com')
    s = requests.Session()
    s.cookies = cj
    s.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/0.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.youtube.com/',
    })
    return s

session = make_session()

def extract_one(v, idx):
    filepath = os.path.join(transcripts_dir, f'video_{idx:02d}.md')

    if os.path.exists(filepath):
        with open(filepath) as f:
            content = f.read()
        if '## Transcript:' in content and 'NO TRANSCRIPT' not in content and 'NO CAPTIONS' not in content:
            return 'skip'

    resp = session.get(f"https://www.youtube.com/watch?v={v['id']}", timeout=15)
    if resp.status_code != 200:
        return f'page_{resp.status_code}'

    match = re.search(r'"baseUrl"\s*:\s*"(https?://[^"]+timedtext[^"]+)"', resp.text)
    if not match:
        with open(filepath, 'w') as f:
            f.write(f'# Title: {v["title"]}\n# URL: {v["url"]}\n# STATUS: NO CAPTIONS ON VIDEO\n')
        return 'no_captions'

    cap_url = match.group(1).replace('\\u0026', '&')
    cap_resp = session.get(cap_url, timeout=15)

    if cap_resp.status_code == 429:
        return 'rate_limited'
    if cap_resp.status_code != 200:
        return f'cap_{cap_resp.status_code}'

    text_parts = re.findall(r'<text[^>]*>(.*?)</text>', cap_resp.text)
    full_text = ' '.join([html.unescape(t) for t in text_parts])
    words = full_text.split()

    if len(words) < 10:
        with open(filepath, 'w') as f:
            f.write(f'# Title: {v["title"]}\n# URL: {v["url"]}\n# STATUS: EMPTY TRANSCRIPT\n')
        return 'empty'

    quality_warnings = []
    if len(words) < 100:
        quality_warnings.append(f'Very short ({len(words)} words)')

    with open(filepath, 'w') as f:
        f.write(f'# Title: {v["title"]}\n')
        f.write(f'# Channel: {v["channel"]}\n')
        f.write(f'# URL: {v["url"]}\n')
        f.write(f'# Views: {v["views"]}\n')
        f.write(f'# Uploaded: {v["date"]}\n')
        f.write(f'# Scout reason: {v["reason"]}\n')
        f.write(f'# Words: {len(words)}\n')
        if quality_warnings:
            f.write(f'# Warning: {"; ".join(quality_warnings)}\n')
        f.write(f'\n## Transcript:\n\n{full_text}\n')

    return f'ok_{len(words)}'

# Main loop
log("Starting batch 2 extraction (no cooldown - already waited)...")

succeeded = 0
failed = 0
skipped = 0
i = 15
consecutive_blocks = 0

while i < len(videos):
    v = videos[i]
    idx = i + 1

    try:
        result = extract_one(v, idx)
    except Exception as e:
        result = f'error:{str(e)[:40]}'

    if result == 'skip':
        skipped += 1
        i += 1
        continue
    elif result == 'rate_limited':
        consecutive_blocks += 1
        wait = min(90 * consecutive_blocks, 600)
        log(f"  [{idx}] RATE LIMITED. Waiting {wait}s (block #{consecutive_blocks})...")
        time.sleep(wait)
        if consecutive_blocks % 3 == 0:
            try:
                session = make_session()
                log("  Refreshed session + cookies")
            except:
                pass
        continue
    elif result.startswith('ok_'):
        wc = result.split('_')[1]
        log(f"  [{idx}/{len(videos)}] OK {wc}w — {v['title'][:55]}")
        succeeded += 1
        consecutive_blocks = 0
        signal_path = os.path.join(project_dir, 'research/kap_outputs/.agent1_done')
        with open(signal_path, 'w') as f:
            f.write(f'READY\nTranscripts: {15 + succeeded}\nPending: {len(videos) - 15 - succeeded - failed - skipped}\nFailed: {failed}\n')
        time.sleep(12)
    else:
        log(f"  [{idx}/{len(videos)}] FAIL ({result}) — {v['title'][:55]}")
        failed += 1
        consecutive_blocks = 0
        time.sleep(8)

    i += 1

log(f"\nALL DONE: {succeeded} extracted, {failed} failed, {skipped} skipped")
log(f"Total transcripts with content: {15 + succeeded}")

signal_path = os.path.join(project_dir, 'research/kap_outputs/.agent1_done')
with open(signal_path, 'w') as f:
    f.write(f'READY\nTranscripts: {15 + succeeded}\nFailed: {failed}\nBatch2: COMPLETE\n')
