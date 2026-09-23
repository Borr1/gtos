"""
API Refusal Monitor — called by watchdog.ps1 every 15 minutes.

Reads shadow_logs/malformed_responses.jsonl, counts flat JSON refusals
in the last 30 minutes. If more than THRESHOLD found, sends a Telegram alert.

Flat refusal signature:
  - error starts with "Expecting value:" (JSON decode failure, not Pydantic)
  - raw_response_length < 100 (not a real AI response that failed parsing)

Pool_type/Pydantic failures are explicitly excluded — they are different bugs
handled separately.

Exit codes:
  0 — below threshold, or cooldown active, or alert sent successfully
  1 — alert needed but TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not configured
  2 — Telegram HTTP call failed
"""

import json
import os
import sys
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv  # noqa: E402
load_dotenv(PROJECT_ROOT / ".env", override=True)

SHADOW_LOG = PROJECT_ROOT / "shadow_logs" / "malformed_responses.jsonl"
STATE_FILE = PROJECT_ROOT / "shadow_logs" / "api_refusal_alert_state.json"

WINDOW_MINUTES = 30    # look-back window
THRESHOLD = 2          # alert when refusal count EXCEEDS this (i.e. >= 3)
COOLDOWN_MINUTES = 30  # suppress repeat alerts within this window


# ---------------------------------------------------------------------------
# Detection logic
# ---------------------------------------------------------------------------

def _normalized(value: Any) -> str:
    return "" if value is None else str(value)


def _raw_response_length(entry: dict) -> int:
    try:
        return int(entry.get("raw_response_length") or 0)
    except (TypeError, ValueError):
        return 0


def malformed_response_category(entry: dict) -> str:
    """Classify a malformed AI response without calling any API."""
    raw_response = _normalized(entry.get("raw_response")).strip().lower()
    error = _normalized(entry.get("error")).lower()
    raw_len = _raw_response_length(entry)
    if error.startswith("expecting value:") and raw_len < 100:
        return "FLAT_REFUSAL_OR_SHORT_NON_JSON"
    if raw_response.startswith("```json") or "extra data" in error:
        return "JSON_FENCE_OR_TRAILING_TEXT_PARSE_FAILURE"
    if raw_response and not raw_response.startswith("{"):
        return "NON_JSON_RESPONSE_PARSE_FAILURE"
    return "OTHER_MALFORMED_AI_RESPONSE"


def summarize_malformed_entries(entries: list[dict]) -> dict:
    """Return row-preserving malformed-response counts for audits and tests."""
    categories = Counter(malformed_response_category(entry) for entry in entries)
    context_present = sum(
        bool(entry.get("symbol") and entry.get("candle_time"))
        for entry in entries
    )
    return {
        "malformed_response_rows": len(entries),
        "malformed_response_category_counts": dict(sorted(categories.items())),
        "malformed_response_rows_with_symbol_and_candle_time": context_present,
        "malformed_response_rows_missing_symbol_or_candle_time": len(entries) - context_present,
    }


def _is_flat_refusal(entry: dict) -> bool:
    """Return True if this entry is a flat JSON refusal (not a Pydantic error)."""
    return malformed_response_category(entry) == "FLAT_REFUSAL_OR_SHORT_NON_JSON"


def count_recent_refusals(log_path: Path, window_minutes: int = WINDOW_MINUTES) -> list:
    """
    Return all flat-refusal entries from log_path whose timestamp falls within
    the last window_minutes. Non-parseable lines are silently skipped.
    """
    if not log_path.exists():
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
    refusals = []

    with open(log_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            ts_str = entry.get("timestamp", "")
            try:
                ts = datetime.fromisoformat(ts_str)
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                continue

            if ts >= cutoff and _is_flat_refusal(entry):
                refusals.append(entry)

    return refusals


# ---------------------------------------------------------------------------
# State / cooldown
# ---------------------------------------------------------------------------

def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state), encoding="utf-8")


def _in_cooldown(state: dict, cooldown_minutes: int = COOLDOWN_MINUTES) -> bool:
    last_alert = state.get("last_alert_utc")
    if not last_alert:
        return False
    try:
        ts = datetime.fromisoformat(last_alert)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) - ts < timedelta(minutes=cooldown_minutes)
    except (ValueError, TypeError):
        return False


# ---------------------------------------------------------------------------
# Telegram
# ---------------------------------------------------------------------------

def build_alert_message(refusals: list) -> str:
    first_ts = refusals[0].get("timestamp", "")[:19].replace("T", " ")
    last_ts = refusals[-1].get("timestamp", "")[:19].replace("T", " ")
    return (
        f"GTOS API REFUSAL ALERT\n"
        f"{len(refusals)} flat refusals in last {WINDOW_MINUTES} min\n"
        f"First: {first_ts} UTC\n"
        f"Last:  {last_ts} UTC\n"
        f"Check Anthropic status — entire kill zone may be missed."
    )


def send_telegram(token: str, chat_id: str, text: str) -> bool:
    """Send a Telegram message using urllib (stdlib). Returns True on success.

    Refuses unless this process is authorized to page the operator (F30 / Q7).
    This monitor POSTs directly rather than through the notification queue, so
    it needs its own gate — credential presence is not authorization. See
    ``src/safety/notification_authorization.py``.
    """
    from src.safety.notification_authorization import delivery_authorization

    _auth = delivery_authorization()
    if not _auth.allowed:
        print(
            f"[api_refusal_monitor] Telegram send REFUSED (unauthorized process): "
            f"{_auth.detail}",
            file=sys.stderr,
        )
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({"chat_id": chat_id, "text": text}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except urllib.error.HTTPError as e:
        print(f"[api_refusal_monitor] Telegram HTTP error: {e.code} {e.reason}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"[api_refusal_monitor] Telegram send failed: {e}", file=sys.stderr)
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    # Operator notification delivery is default-deny per process (F30 / Q7).
    # This monitor is an operator-facing cron alerter launched by
    # scripts/watchdog.ps1; it takes the grant explicitly at its entrypoint so
    # send_telegram() below can deliver, while an import of this module from a
    # test or another tool stays refused.
    from src.safety.notification_authorization import authorize_operator_delivery
    authorize_operator_delivery(reason="scripts/api_refusal_monitor.py cron entrypoint")

    refusals = count_recent_refusals(SHADOW_LOG)

    if len(refusals) <= THRESHOLD:
        return 0

    state = _load_state()
    if _in_cooldown(state):
        print(
            f"[api_refusal_monitor] {len(refusals)} refusals found but in cooldown — skipping"
        )
        return 0

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

    if not token or not chat_id:
        print(
            f"[api_refusal_monitor] ALERT: {len(refusals)} flat refusals in {WINDOW_MINUTES} min "
            f"but TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID not set — configure in .env"
        )
        return 1

    msg = build_alert_message(refusals)
    success = send_telegram(token, chat_id, msg)

    if success:
        state["last_alert_utc"] = datetime.now(timezone.utc).isoformat()
        _save_state(state)
        print(f"[api_refusal_monitor] Alert sent: {len(refusals)} refusals detected")
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
