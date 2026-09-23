# Proposed Changes to KAP_AGENT_1_EXTRACTOR.md

**Date:** 2026-04-06  
**Author:** Agent 1 (self-improvement after rate limit incident)  
**Status:** PENDING REVIEW

---

## Problem

Agent 1 fires all transcript requests rapidly with no delay. After ~15 requests, YouTube IP-blocks the timedtext API with 429 errors. This blocked extraction of 47/62 videos in batch 2.

## Proposed Changes

### 1. Add rate limit section to the prompt

**Add after the SETUP section:**

```markdown
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
```

### 2. Modify the extraction loop to include delays

In the "EXTRACT TRANSCRIPTS" section, add `time.sleep(12)` after each successful extraction:

```python
        print(f"  ✓ {word_count} words saved to {filepath}")
        succeeded += 1
        time.sleep(12)  # RATE LIMIT: 10-12s between requests
```

### 3. Add incremental signal updates

After each successful extraction, update the signal file so downstream agents can pick up new transcripts:

```python
        # Update signal incrementally
        signal_path = os.path.join(project_dir, 'research/kap_outputs/.agent1_done')
        with open(signal_path, 'w') as f:
            f.write(f'READY\nTranscripts: {succeeded}\nPending: {len(videos) - succeeded - failed}\n')
```

### 4. Add fallback: direct page scraping

When youtube-transcript-api fails with IpBlocked, fall back to scraping the YouTube page HTML for the timedtext URL and fetching caption XML directly. Same rate limits apply but gives more control over retry logic.

---

## Impact

- Prevents the entire batch 2 failure scenario
- Downstream agents start working sooner (incremental signals)
- Long extractions survive session disconnects (nohup)
- No change to output format — transcripts are identical
