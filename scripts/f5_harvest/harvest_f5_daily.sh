#!/bin/bash
# harvest_f5_daily.sh — daily read-only pull of F5 ($10 lane) evidence from the VPS.
#
# Pulls into /Users/borr/GTOSActive/f5-harvest/<YYYY-MM-DD>/ :
#   execution_manager_v4_decisions.jsonl   (exec-manager decision rows, ~1 MB)
#   events.jsonl                           (F5 minimal-size event stream)
#   slippage_runtime.jsonl                 (slippage fidelity, archive)
#   ultimate_book_launcher.tailday.jsonl   (server-side byte-tail, last 4 MB --
#                                           covers a full UTC day: max observed
#                                           day volume 3.06 MB, 2026-08-13. The
#                                           11 MB file is NEVER pulled whole via
#                                           Get-Content: `-Tail 400` was measured
#                                           2026-08-17 at 8.5 min of remote CPU;
#                                           the seek-from-end byte read returned
#                                           1 MB in ~10 s measured 2026-08-18.
#                                           Was tail256k (~9 rows) before
#                                           2026-08-18; the outcome-ledger
#                                           builder reads both names and dedupes)
#   outbox/*.md + outbox/_listing.json     (grok-jobs lane pages + VPS mtimes)
# and refreshes into <ROOT>/trade_records/ (cumulative, not per-day):
#   placed_decisions.jsonl                 (placement ledger: candidate_id<->ticket)
#   f5_notional_ledger.json                (notional/real-PnL state)
#   <ticket>.json                          (per-ticket broker-truth trade records;
#                                           only new/changed files are fetched,
#                                           by Name+Length against the local copy)
# then writes <day>/DAILY.md via summarize_f5_daily.py, and builds the
# decision->fill->outcome ledger via build_f5_outcome_ledger.py:
#   <day>/outbox/f5_outcome_ledger_<day>.jsonl  (+ .sha256)
#   <ROOT>/f5_outcome_ledger_cumulative.jsonl   (+ .sha256)
#
# VPS access is READ-ONLY by construction: `get` transfers and Get-Content /
# Get-ChildItem only. No writes, no process changes. Commands kept small —
# the box is fragile.
#
# Day semantics: target day = current UTC date. The 06:10 Asia/Bangkok launchd
# run is 23:10 UTC of the day being summarized, so each dated folder is written
# at the end of its own UTC day. Override: harvest_f5_daily.sh YYYY-MM-DD
#
# launchd schedule note: StartCalendarInterval fires in the Mac's local
# timezone; this Mac runs Asia/Bangkok (UTC+7), so Hour=6/Minute=10 is
# 06:10 Asia/Bangkok as intended. If the Mac's timezone ever changes, the
# schedule moves with it.

set -u

# IN-REPO COPY (scripts/f5_harvest/, 2026-08-25). Changes vs the f5-harvest
# original: helper scripts resolve REPO-RELATIVE (this dir), the outcome-ledger
# builder runs BEFORE the summarizer (DAILY.md v2 reads the ledger +
# reconciliation), and the pull adds the broker-deals dump (deals_f5_*.json),
# its bars_f5/ M15 dump, and judgment/judge_<day>.jsonl when present on the
# VPS. Data root stays /Users/borr/GTOSActive/f5-harvest — the harvest state
# (dated dirs, trade_records, cumulative ledger) is machine state, not repo
# state. The Mac cron keeps running the OLD copies until the orchestrator
# switches it to this script.

ROOT="/Users/borr/GTOSActive/f5-harvest"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VPS_SESSIONS="${CODEX_HOME:-$HOME/.codex}/skills/vps-agent-sessions/scripts/vps-sessions"
SUMMARIZER="$SCRIPT_DIR/summarize_f5_daily.py"
PY="/usr/bin/python3"

DAY="${1:-$(date -u +%F)}"
DEST="$ROOT/$DAY"
LOG="$DEST/harvest.log"

# VPS source paths (read-only)
WIN_SHADOW='host-local\redacted_host\repo\shadow_logs'
WIN_OUTBOX='C:\Users\trader\gtos\grok-jobs\outbox'
WIN_PSTATE='host-local\redacted_host\repo\pipeline_state\ultimate_book\operator'
RECDIR="$ROOT/trade_records"

mkdir -p "$DEST/outbox" "$ROOT/logs"
: > "$LOG"

log() { printf '%s %s\n' "$(date -u +%FT%TZ)" "$*" | tee -a "$LOG"; }

# macOS ships no `timeout`; guard every VPS call with a perl alarm (TERM, then
# KILL, exit 124) so a hung host-admin session cannot wedge the launchd job.
run_to() {
  local secs="$1"; shift
  perl -e '
    my $t = shift @ARGV;
    my $pid = fork();
    if (!$pid) { exec @ARGV or exit 127; }
    $SIG{ALRM} = sub { kill "TERM", $pid; sleep 2; kill "KILL", $pid; exit 124; };
    alarm $t;
    waitpid($pid, 0);
    exit($? >> 8);
  ' "$secs" "$@"
}

FAILS=0

fetch_opt() { # fetch_opt <winpath> <localpath> — optional artifact: absence is
              # expected (feature not yet deployed on the VPS), never a FAIL.
  local win="$1" loc="$2"
  if run_to 120 "$VPS_SESSIONS" get "$win" "$loc" --force >>"$LOG" 2>&1 && [ -s "$loc" ]; then
    log "OK  get(opt) $win ($(wc -c <"$loc" | tr -d ' ') B)"
    return 0
  fi
  rm -f "$loc"
  log "INFO optional artifact absent: $win"
  return 1
}

fetch_get() { # fetch_get <winpath> <localpath>
  local win="$1" loc="$2" try
  for try in 1 2; do
    if run_to 180 "$VPS_SESSIONS" get "$win" "$loc" --force >>"$LOG" 2>&1 && [ -s "$loc" ]; then
      log "OK  get $win ($(wc -c <"$loc" | tr -d ' ') B)"
      return 0
    fi
    log "WARN attempt $try failed: get $win"
    [ "$try" -lt 2 ] && sleep 5
  done
  FAILS=$((FAILS+1)); return 1
}

fetch_ps() { # fetch_ps <ps-command> <outfile> <label>  (stdout of remote command -> file)
  local cmd="$1" out="$2" label="$3" try
  for try in 1 2; do
    if run_to 120 "$VPS_SESSIONS" ps --command "$cmd" >"$out" 2>>"$LOG" && [ -s "$out" ]; then
      log "OK  ps $label ($(wc -c <"$out" | tr -d ' ') B)"
      return 0
    fi
    log "WARN attempt $try failed: ps $label"
    [ "$try" -lt 2 ] && sleep 5
  done
  rm -f "$out"   # leave no empty artifact: the summarizer flags it MISSING
  FAILS=$((FAILS+1)); return 1
}

log "F5 harvest start day=$DAY dest=$DEST"

# --- shadow logs (small files pulled whole) ---------------------------------
fetch_get "$WIN_SHADOW\\execution_manager_v4_decisions.jsonl" "$DEST/execution_manager_v4_decisions.jsonl"
fetch_get "$WIN_SHADOW\\f5_minimal\\operator\\events.jsonl" "$DEST/events.jsonl"
fetch_get "$WIN_SHADOW\\slippage_runtime.jsonl" "$DEST/slippage_runtime.jsonl"

# --- launcher: server-side byte-tail only (file is 11 MB; do NOT pull whole).
# Read-only, share-friendly open (FileShare ReadWrite: never blocks the live
# writer); seeks to EOF-4MB and returns only that slice (a full UTC day).
TAIL_CMD="\$p='$WIN_SHADOW\\ultimate_book_launcher.jsonl'; \$fs=[IO.File]::Open(\$p,'Open','Read','ReadWrite'); \$take=[Math]::Min(4194304,\$fs.Length); [void]\$fs.Seek(-\$take,'End'); \$b=New-Object byte[] \$take; [void]\$fs.Read(\$b,0,\$take); \$fs.Close(); [Text.Encoding]::UTF8.GetString(\$b)"
fetch_ps "$TAIL_CMD" "$DEST/ultimate_book_launcher.tailday.jsonl" "launcher byte-tail 4M"

# --- F5 join spine + broker truth (cumulative, into $RECDIR) ----------------
# placement ledger (candidate_id<->ticket), notional ledger, per-ticket trade
# records. Trade records are fetched only when new or changed (Name+Length
# against the local copy) -- each is ~75 KB and written at close then
# occasionally repaired, so most nights fetch zero or one.
mkdir -p "$RECDIR"
fetch_get "$WIN_PSTATE\\placed_decisions.jsonl" "$RECDIR/placed_decisions.jsonl"
fetch_get "$WIN_PSTATE\\f5_notional_ledger.json" "$RECDIR/f5_notional_ledger.json"

# --- broker-deals authority dump (dump_f5_deals.py output on the VPS) --------
# Newest deals_f5_*.json + its bars_f5/ M15 dump. Tolerate absence: until the
# orchestrator schedules the dump on the VPS these pulls just WARN.
DEALS_LIST_CMD="Get-ChildItem '$WIN_PSTATE' -Filter deals_f5_*.json | Sort-Object LastWriteTimeUtc | Select-Object -Last 1 -ExpandProperty Name"
if run_to 60 "$VPS_SESSIONS" ps --command "$DEALS_LIST_CMD" >"$RECDIR/_deals_name.txt" 2>>"$LOG"; then
  DEALS_NAME="$(tr -d '\r\n ' < "$RECDIR/_deals_name.txt")"
  if [ -n "$DEALS_NAME" ]; then
    fetch_opt "$WIN_PSTATE\\$DEALS_NAME" "$RECDIR/$DEALS_NAME"
  else
    log "WARN no deals_f5_*.json on VPS yet (dump_f5_deals.py not scheduled?)"
  fi
else
  log "WARN deals listing failed"
fi
BARS_LIST_CMD="Get-ChildItem '$WIN_PSTATE\\bars_f5' -Filter *.csv -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Name"
if run_to 60 "$VPS_SESSIONS" ps --command "$BARS_LIST_CMD" >"$RECDIR/_bars_names.txt" 2>>"$LOG" && [ -s "$RECDIR/_bars_names.txt" ]; then
  mkdir -p "$RECDIR/bars_f5"
  while IFS= read -r name; do
    name="$(printf '%s' "$name" | tr -d '\r')"
    [ -z "$name" ] && continue
    fetch_opt "$WIN_PSTATE\\bars_f5\\$name" "$RECDIR/bars_f5/$name" || true
    fetch_opt "$WIN_PSTATE\\bars_f5\\$name.timebase.json" "$RECDIR/bars_f5/$name.timebase.json" || true
  done < "$RECDIR/_bars_names.txt"
else
  log "WARN no bars_f5 dump on VPS (excursion falls back to bars-aug-extension)"
fi

# --- judge rows (judgment seam; tolerate absence) ----------------------------
WIN_JUDGMENT='host-local\redacted_host\repo\judgment'
mkdir -p "$DEST/judgment"
fetch_opt "$WIN_JUDGMENT\\judge_$DAY.jsonl" "$DEST/judgment/judge_$DAY.jsonl" || true
fetch_opt "$WIN_JUDGMENT\\flow_$DAY.json" "$DEST/judgment/flow_$DAY.json" || true
LISTREC_CMD="Get-ChildItem '$WIN_PSTATE\\trade_records' -Filter *.json | Select-Object Name,Length | ConvertTo-Json"
fetch_ps "$LISTREC_CMD" "$RECDIR/_records_listing.json" "trade-records listing"

if [ -s "$RECDIR/_records_listing.json" ]; then
  "$PY" - "$RECDIR/_records_listing.json" "$RECDIR" <<'PYEOF' > "$RECDIR/_records_to_fetch.txt" 2>>"$LOG"
import json, os, sys
raw = open(sys.argv[1], encoding="utf-8", errors="replace").read().strip()
recdir = sys.argv[2]
d = json.loads(raw) if raw else []
if isinstance(d, dict):
    d = [d]
for x in d:
    name = str(x.get("Name") or "")
    if not name.endswith(".json"):
        continue
    local = os.path.join(recdir, name)
    try:
        want = int(x.get("Length"))
    except (TypeError, ValueError):
        continue
    if not os.path.isfile(local) or os.path.getsize(local) != want:
        print(name)
PYEOF
  while IFS= read -r name; do
    [ -z "$name" ] && continue
    fetch_get "$WIN_PSTATE\\trade_records\\$name" "$RECDIR/$name"
  done < "$RECDIR/_records_to_fetch.txt"
else
  log "WARN no trade-records listing; skipping record refresh"
fi

# --- grok-jobs outbox: listing (with VPS mtimes), then each *.md ------------
LIST_CMD="Get-ChildItem '$WIN_OUTBOX' -Filter *.md | Select-Object Name,Length,@{n='mtime_utc';e={\$_.LastWriteTimeUtc.ToString('yyyy-MM-ddTHH:mm:ssZ')}} | ConvertTo-Json"
fetch_ps "$LIST_CMD" "$DEST/outbox/_listing.json" "outbox listing"

if [ -s "$DEST/outbox/_listing.json" ]; then
  "$PY" - "$DEST/outbox/_listing.json" <<'PYEOF' > "$DEST/outbox/_names.txt" 2>>"$LOG"
import json, sys
raw = open(sys.argv[1], encoding="utf-8", errors="replace").read().strip()
d = json.loads(raw) if raw else []
if isinstance(d, dict):
    d = [d]
for x in d:
    n = x.get("Name")
    if n and str(n).lower().endswith(".md"):
        print(n)
PYEOF
  while IFS= read -r name; do
    [ -z "$name" ] && continue
    fetch_get "$WIN_OUTBOX\\$name" "$DEST/outbox/$name"
  done < "$DEST/outbox/_names.txt"
else
  log "WARN no outbox listing; skipping page pulls"
fi

# --- outcome ledger FIRST (DAILY.md v2 reads it + the reconciliation) --------
LEDGER_BUILDER="$SCRIPT_DIR/build_f5_outcome_ledger.py"
if [ -f "$LEDGER_BUILDER" ]; then
  # bars live INSIDE f5-harvest: macOS TCC blocks cron from ~/Documents, so a
  # Documents path silently yields bars_unavailable on every cron build.
  # Interactive runs (which CAN read Documents) refresh the snapshot; cron's
  # read test fails silently and it uses the existing copy.
  if [ -r /Users/borr/Documents/gtos/grok-jobs/bars/aug-extension/M15/MANIFEST.json ] 2>/dev/null || ls /Users/borr/Documents/gtos/grok-jobs/bars/aug-extension/M15/*.csv >/dev/null 2>&1; then
    rsync -a --delete /Users/borr/Documents/gtos/grok-jobs/bars/aug-extension/M15/ "$ROOT/bars-aug-extension/M15/" 2>/dev/null || true
  fi
  # no --bars-dir: the builder's default merges bars-aug-extension/M15 with
  # every bars_f5 dump (trade_records/bars_f5 + dated dirs) per symbol.
  if "$PY" "$LEDGER_BUILDER" "$DEST" --date "$DAY" >>"$LOG" 2>&1; then
    log "OK  outcome ledger written: $DEST/outbox/f5_outcome_ledger_$DAY.jsonl + $ROOT/f5_outcome_ledger_cumulative.jsonl"
  else
    log "ERROR outcome-ledger builder failed (see $LOG)"
    FAILS=$((FAILS+1))
  fi
else
  log "WARN outcome-ledger builder missing at $LEDGER_BUILDER"
fi

# --- summarize (DAILY.md v2 owner page + TELEGRAM.txt) -----------------------
if [ -f "$SUMMARIZER" ]; then
  if "$PY" "$SUMMARIZER" "$DEST" --date "$DAY" >>"$LOG" 2>&1; then
    log "OK  DAILY.md + TELEGRAM.txt written: $DEST/DAILY.md"
  else
    log "ERROR summarizer failed (see $LOG)"
    FAILS=$((FAILS+1))
  fi
else
  log "ERROR summarizer missing at $SUMMARIZER"
  FAILS=$((FAILS+1))
fi

# --- tripwires (Mac side; the VPS runs its own copy every 10 min) ------------
TRIPWIRES="$SCRIPT_DIR/f5_tripwires.py"
if [ -f "$TRIPWIRES" ]; then
  if "$PY" "$TRIPWIRES" --harvest-root "$ROOT" --day "$DAY" --no-mt5 \
       --state "$ROOT/f5_tripwire_state.json" >>"$LOG" 2>&1; then
    log "OK  tripwires evaluated (see harvest.log for the wire report)"
  else
    log "WARN tripwires run failed (see $LOG)"
  fi
fi

log "F5 harvest done day=$DAY fails=$FAILS"
[ "$FAILS" -eq 0 ]
