#!/usr/bin/env bash
# Batch-fetch YouTube transcripts via yt-dlp for the QuantLabsNet Tier 1 playlist.
# Tries manual subs → auto-gen → logs failure. No Whisper fallback (too costly at scale).
# Writes dedup'd plain-text .txt to transcripts/<video_id>.txt plus a _fetch.log.

set -u

ROOT="research/quantlabs_competitor_intel"
INPUT="$ROOT/urls_youtube.txt"
OUT_DIR="$ROOT/transcripts"
LOG="$OUT_DIR/_fetch.log"
YTDLP="/c/Users/MSI/AppData/Roaming/Python/Python313/Scripts/yt-dlp.exe"

mkdir -p "$OUT_DIR"
: > "$LOG"
echo "=== Fetch started $(date -u +%FT%TZ) ===" | tee -a "$LOG"

total=0
ok=0
fail=0
skip=0

# Skip header lines starting with #
grep -v '^#' "$INPUT" | while IFS='|' read -r URL VID TITLE DUR UPLOAD; do
    URL="${URL# }"; URL="${URL% }"
    VID="${VID# }"; VID="${VID% }"
    TITLE="${TITLE# }"; TITLE="${TITLE% }"
    [ -z "$VID" ] && continue
    total=$((total + 1))
    OUT="$OUT_DIR/$VID"

    if [ -f "${OUT}.txt" ]; then
        echo "[skip] $VID already fetched" | tee -a "$LOG"
        skip=$((skip + 1))
        continue
    fi

    # Trim title for log line
    TITLE_SHORT=$(printf '%s' "$TITLE" | cut -c1-70)
    echo "[fetch] $VID $TITLE_SHORT" | tee -a "$LOG"

    # Request manual + auto-gen English subs, skip media download
    "$YTDLP" \
        --write-sub --write-auto-sub --sub-langs en \
        --skip-download \
        --no-warnings \
        --output "$OUT" \
        "$URL" >> "$LOG" 2>&1

    # Find whichever VTT landed (manual or auto)
    VTT=$(ls "${OUT}".*.vtt 2>/dev/null | head -1)
    if [ -z "$VTT" ]; then
        echo "[FAIL] $VID — no English subtitles available" | tee -a "$LOG"
        fail=$((fail + 1))
        continue
    fi

    # Convert VTT → dedup'd plain text
    python -c "
import re
seen = set()
with open(r'''$VTT''', 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith('WEBVTT') or line.startswith('Kind:') or line.startswith('Language:') or '-->' in line:
            continue
        clean = re.sub('<[^>]*>', '', line)
        clean = clean.replace('&amp;', '&').replace('&gt;', '>').replace('&lt;', '<')
        if clean and clean not in seen:
            print(clean)
            seen.add(clean)
" > "${OUT}.txt"

    # Prepend header
    HEADER="# $TITLE\nURL: $URL\nVideo ID: $VID\nDuration: ${DUR}s\nFetched: $(date -u +%FT%TZ)\n---\n\n"
    printf "$HEADER" | cat - "${OUT}.txt" > "${OUT}.tmp" && mv "${OUT}.tmp" "${OUT}.txt"

    rm -f "${OUT}".*.vtt
    WC=$(wc -w < "${OUT}.txt")
    echo "[ok]   $VID words=$WC" | tee -a "$LOG"
    ok=$((ok + 1))

    # Polite pause
    sleep 3
done

echo "=== Fetch done $(date -u +%FT%TZ) ok=$ok fail=$fail skip=$skip ===" | tee -a "$LOG"
