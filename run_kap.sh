#!/bin/bash
# KAP Pipeline Orchestrator — chains 4 agents via claude -p
# Usage: ./run_kap.sh [--from-stage N]
# Uses Claude Max subscription (no API costs)

set -euo pipefail

# --- Config ---
AGENT1_PROMPT="agents/KAP_AGENT_1_EXTRACTOR.md"
AGENT2_PROMPT="agents/KAP_AGENT_2_COMPREHENSION.md"
AGENT3_PROMPT="agents/KAP_AGENT_3_FILTER.md"
AGENT4_PROMPT="agents/KAP_AGENT_4_STRATEGIST.md"
URLS_FILE="research/kap_outputs/urls.txt"
OUTDIR="research/kap_outputs"
KB_DIR="knowledge_base"

# --- Parse args ---
FROM_STAGE=1
if [[ "${1:-}" == "--from-stage" ]]; then
    FROM_STAGE="${2:-1}"
fi

# --- Helpers ---
timestamp() { date "+%H:%M:%S"; }

git_save() {
    git add -A 2>/dev/null
    git commit -m "$1" 2>/dev/null || echo "  (nothing to commit)"
}

check_file() {
    if [[ ! -f "$1" ]]; then
        echo "ERROR: Missing: $1"
        exit 1
    fi
}

# Progress indicator — runs in background, killed on stage completion
PROGRESS_PID=""
start_progress() {
    local logfile="$1"
    (
        while true; do
            sleep 60
            local size=$(wc -c < "$logfile" 2>/dev/null || echo 0)
            echo "  [$(timestamp)] waiting... log: ${size} bytes"
        done
    ) &
    PROGRESS_PID=$!
}

stop_progress() {
    if [[ -n "$PROGRESS_PID" ]]; then
        kill "$PROGRESS_PID" 2>/dev/null || true
        wait "$PROGRESS_PID" 2>/dev/null || true
        PROGRESS_PID=""
    fi
}

trap 'stop_progress 2>/dev/null' EXIT

# --- Pre-flight checks ---
echo "KAP Pipeline starting at $(timestamp)"

for f in "$AGENT1_PROMPT" "$AGENT2_PROMPT" "$AGENT3_PROMPT" "$AGENT4_PROMPT"; do
    check_file "$f"
done

if [[ ! -f "$URLS_FILE" ]]; then
    echo "ERROR: No urls.txt found at $URLS_FILE"
    echo "   Create it with one YouTube URL per line."
    exit 1
fi

URL_COUNT=$(grep -c 'https://' "$URLS_FILE" 2>/dev/null || echo 0)
echo "   URLs to process: $URL_COUNT"
echo "   Starting from stage: $FROM_STAGE"
echo ""

# Create output directories
mkdir -p "$OUTDIR/transcripts" "$OUTDIR/claims" "$OUTDIR/filtered" "$OUTDIR/tests"

# --- Stage 1: Extract transcripts ---
if [[ "$FROM_STAGE" -le 1 ]]; then
    echo "[$(timestamp)] Stage 1: Extracting transcripts..."

    start_progress "$OUTDIR/stage1_log.txt"

    claude -p "You are Agent 1 (Extractor).

Read the file $URLS_FILE. For each YouTube URL, fetch the transcript using youtube-transcript-api (pip install it if needed).

RULES:
- Add random 3-8 second delay between fetches
- Retry up to 3 times with exponential backoff on failure
- Skip URLs where transcript file already exists with real content (>100 bytes)
- Save each transcript to $OUTDIR/transcripts/video_NN.txt (or .md if that format already exists)
- Format: ## Source: [url]\n## Transcript:\n[text]
- Print a summary at the end: N extracted, N skipped, N failed

Start now." \
        --allowedTools "Bash(python3*) Bash(pip*) Bash(mkdir*) Bash(ls*) Bash(cat*) Bash(wc*) Bash(head*) Bash(grep*) Read Write" \
        < /dev/null > "$OUTDIR/stage1_log.txt" 2>&1

    stop_progress
    echo "[$(timestamp)] Stage 1 complete. Log: $OUTDIR/stage1_log.txt"
    tail -20 "$OUTDIR/stage1_log.txt"
    git_save "KAP Agent 1: Transcripts extracted at $(timestamp)"
    echo ""
fi

# --- Stage 2: Extract claims ---
if [[ "$FROM_STAGE" -le 2 ]]; then
    echo "[$(timestamp)] Stage 2: Extracting claims..."

    TRANSCRIPT_COUNT=$(find "$OUTDIR/transcripts" -name "video_*" \( -name "*.txt" -o -name "*.md" \) 2>/dev/null | wc -l | tr -d ' ')
    echo "   Transcripts available: $TRANSCRIPT_COUNT"

    start_progress "$OUTDIR/stage2_log.txt"

    claude -p "You are Agent 2 (Comprehension).

Your full instructions are below in the system prompt — follow them exactly.

Process ALL transcript files in $OUTDIR/transcripts/.
For each transcript, extract testable trading claims as structured JSON.
Save claims to $OUTDIR/claims/video_NN_claims.json.
Skip videos where claims file already exists with real claims (>50 bytes).
Print a summary: N videos processed, N total claims extracted." \
        --append-system-prompt "$(cat "$AGENT2_PROMPT")" \
        --allowedTools "Bash(python3*) Bash(ls*) Bash(cat*) Bash(wc*) Bash(head*) Bash(grep*) Read Write" \
        < /dev/null > "$OUTDIR/stage2_log.txt" 2>&1

    stop_progress
    echo "[$(timestamp)] Stage 2 complete. Log: $OUTDIR/stage2_log.txt"
    tail -20 "$OUTDIR/stage2_log.txt"
    git_save "KAP Agent 2: Claims extracted at $(timestamp)"
    echo ""
fi

# --- Stage 3: Filter claims ---
if [[ "$FROM_STAGE" -le 3 ]]; then
    echo "[$(timestamp)] Stage 3: Filtering claims against KB..."

    CLAIMS_COUNT=$(ls "$OUTDIR/claims/"*_claims.json 2>/dev/null | wc -l | tr -d ' ')
    echo "   Claims files available: $CLAIMS_COUNT"

    start_progress "$OUTDIR/stage3_log.txt"

    claude -p "You are Agent 3 (Filter).

Your full instructions are below in the system prompt — follow them exactly.

Load ALL claims from $OUTDIR/claims/.
Filter them against the knowledge base files in $KB_DIR/.
Output:
  - $OUTDIR/filtered/findings_report.md
  - $OUTDIR/filtered/all_findings.json
Include cross-video analysis pass as specified in your instructions.
Print a summary: N total claims -> N kept findings." \
        --append-system-prompt "$(cat "$AGENT3_PROMPT")" \
        --allowedTools "Bash(python3*) Bash(ls*) Bash(cat*) Bash(wc*) Bash(head*) Bash(grep*) Bash(find*) Read Write" \
        < /dev/null > "$OUTDIR/stage3_log.txt" 2>&1

    stop_progress
    echo "[$(timestamp)] Stage 3 complete. Log: $OUTDIR/stage3_log.txt"
    tail -20 "$OUTDIR/stage3_log.txt"
    git_save "KAP Agent 3: Claims filtered at $(timestamp)"
    echo ""
fi

# --- Stage 4: Strategic report ---
if [[ "$FROM_STAGE" -le 4 ]]; then
    echo "[$(timestamp)] Stage 4: Producing strategic report..."

    start_progress "$OUTDIR/stage4_log.txt"

    claude -p "You are Agent 4 (Strategist).

Your full instructions are below in the system prompt — follow them exactly.

Load findings from $OUTDIR/filtered/findings_report.md.
MANDATORY: Before promoting ANY finding to priority action, run the codebase
cross-reference check (grep src/ for the relevant mechanism).
Output: $OUTDIR/BATCH_REPORT.md
Include test scripts in $OUTDIR/tests/ and RUN them if data exists.
Print a summary of priority findings." \
        --append-system-prompt "$(cat "$AGENT4_PROMPT")" \
        --allowedTools "Bash(python3*) Bash(pip*) Bash(ls*) Bash(cat*) Bash(wc*) Bash(head*) Bash(grep*) Bash(find*) Read Write" \
        --add-dir src \
        < /dev/null > "$OUTDIR/stage4_log.txt" 2>&1

    stop_progress
    echo "[$(timestamp)] Stage 4 complete. Log: $OUTDIR/stage4_log.txt"
    tail -20 "$OUTDIR/stage4_log.txt"
    git_save "KAP Agent 4: BATCH_REPORT complete at $(timestamp)"
    echo ""
fi

# --- Done ---
echo "========================================"
echo "Pipeline complete at $(timestamp)"
echo "Report: $OUTDIR/BATCH_REPORT.md"
echo "Logs:   $OUTDIR/stage[1-4]_log.txt"
echo "========================================"
