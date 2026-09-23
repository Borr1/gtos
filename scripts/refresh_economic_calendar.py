"""Economic-Calendar Staleness Monitor (Issue #15, 2026-04-28).

Detects stale ``data/news_calendar.json`` + ``data/economic_calendar.csv``
and fires a Telegram alert reminding the operator to refresh from
ForexFactory. **Does NOT fetch data automatically** — per task brief and
CLAUDE.md "no API call that costs money or requires sign-up without CEO
authorization". Despite the script name, this is a **monitor + alerter**,
not an auto-refresher; the calendar files are operator-maintained.

The calendar files are operator-maintained:
  - ``data/news_calendar.json`` source comment:
    "ForexFactory / FedSchedule -- operator updates weekly"
  - ``src/components/news_calendar.py`` warns at age > 7d:
    "JSON calendar is %d days old -- update from ForexFactory"

This monitor closes the alerting loop: instead of just logging the warning
once per orchestrator boot, it emits a Telegram alert (via the persistent
notification queue, see below) when the file is older than the configured
threshold. 24-hour cooldown so we don't spam during long staleness windows.

Cadence (2026-04-29 fix)
------------------------
The watchdog hook in ``scripts/watchdog.ps1`` fires this script:

* On every weekday/Saturday-morning watchdog tick, with a once-per-UTC-day
  marker so we don't actually re-evaluate more than once per day.
* On Sunday + dead-zone wakeups too — the hook is hoisted *above* the
  ``Test-TradingHours`` early-exit so weekend operators still see the
  alert when prepping the next trading week (a STALE warning fired during
  Sunday 18-21 UTC is exactly when the operator should be refreshing the
  calendar for the upcoming week).

The check itself is cheap (one ``stat`` call + a tiny JSON read) and never
touches MT5, the API, or trading state.

Refresh procedure (operator)
----------------------------
1. Visit https://www.forexfactory.com/calendar
2. Click "This Week" + filter to Impact = HIGH (red)
3. Note USD / GBP / EUR / JPY events for the upcoming 4-6 weeks
4. Hand-edit ``data/news_calendar.json``:
   - Update ``week_of`` and ``updated_at`` fields
   - Replace ``events`` array with the fresh window
5. Save + commit. The orchestrator picks up the new file on next KZ entry.

The CSV (``data/economic_calendar.csv``) is the legacy fallback; refresh
both or migrate consumers off the CSV first.

Telegram dispatch (2026-04-29 fix)
----------------------------------
Pre-fix this script POSTed directly to ``api.telegram.org`` via
``urllib.request.urlopen``. On the live host the system trust store has a
self-signed certificate in the chain, so every direct HTTPS POST returned
``[SSL: CERTIFICATE_VERIFY_FAILED]``, the script exited 2, the watchdog
suppressed the once-per-day marker (treats exit=2 as "retry next
heartbeat"), and the script ran every 15 min for days without ever
delivering an alert (or ever cooling down).

The fix routes the alert through ``src.notifications.notify_alert`` →
``src.utils.notification_queue`` (HIGH priority). The queue:

* Uses ``ssl.CERT_NONE`` in ``_default_transport`` (intentional, see the
  ``notification_queue.py`` docstring), so the SSL chain issue does not
  bite.
* Persists pending alerts to ``pipeline_state/notification_queue.jsonl``
  so a host blip during dispatch does not lose the message.
* Is drained by the dedicated ``notification_queue_worker`` daemon (from
  ``start_all.bat`` / supervised by ``watchdog.ps1``), so even though this
  script is short-lived, the alert reliably reaches Telegram.

Exit codes
----------
    0 — both files fresh OR cooldown active OR alert successfully enqueued
    1 — alert needed but TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set in
        the environment (operator action required)
    2 — alert enqueue failed (queue subsystem unavailable or disk error);
        caller can retry next watchdog tick

Note: a successful enqueue (exit 0) does NOT guarantee Telegram delivery
in the same tick — the queue worker drains asynchronously. The marker
file is written on enqueue; downstream dispatch retries are queue-driven.

Module-level constants are tunable + monkeypatchable; tests follow the
``module-ref + tmp_path`` pattern (canonical per CLAUDE.md).
"""
from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(PROJECT_ROOT / ".env", override=True)

logger = logging.getLogger(__name__)

# ── Module-level paths / knobs (monkeypatch in tests, session 21 canon) ────
JSON_CALENDAR_PATH: Path = PROJECT_ROOT / "data" / "news_calendar.json"
CSV_CALENDAR_PATH: Path = PROJECT_ROOT / "data" / "economic_calendar.csv"
STATE_FILE: Path = (
    PROJECT_ROOT / "knowledge_base" / "meta" / "calendar_staleness_state.json"
)

# Fire on age > 7d (matches src/components/news_calendar.py warning).
STALENESS_THRESHOLD_DAYS: int = 7

# Suppress repeat alerts for 24h after a fired one.
COOLDOWN_HOURS: float = 24.0


# ── File freshness ─────────────────────────────────────────────────────────


def _file_age_days(path: Path, now: Optional[datetime] = None) -> Optional[float]:
    """Return file age in days from mtime. ``None`` if file is missing.

    Prefer the JSON's embedded ``updated_at`` over the OS mtime so a
    ``touch`` doesn't suppress alerts on an actually-stale file. Falls back
    to mtime when the JSON has no ``updated_at`` or for the CSV.
    """
    if not path.exists():
        return None
    use_now = now if now is not None else datetime.now(timezone.utc)

    if path.suffix == ".json":
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            data = None
        if isinstance(data, dict):
            updated_at = data.get("updated_at")
            if isinstance(updated_at, str):
                try:
                    dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    return (use_now - dt).total_seconds() / 86400.0
                except (ValueError, TypeError):
                    pass

    # Fallback: mtime
    try:
        mtime = path.stat().st_mtime
        mtime_dt = datetime.fromtimestamp(mtime, tz=timezone.utc)
        return (use_now - mtime_dt).total_seconds() / 86400.0
    except OSError:
        return None


def collect_stale_files(threshold_days: int = STALENESS_THRESHOLD_DAYS,
                          now: Optional[datetime] = None) -> list[dict]:
    """Return a list of dicts ``{path, age_days, reason}`` for stale files.

    A "missing" file is also reported (operator should ensure it exists);
    this matches the orchestrator's expectation that BOTH files are present
    even though only one is the active source.
    """
    out: list[dict] = []
    for label, path in (("json", JSON_CALENDAR_PATH), ("csv", CSV_CALENDAR_PATH)):
        age = _file_age_days(path, now=now)
        if age is None:
            out.append({
                "label": label,
                "path": str(path),
                "age_days": None,
                "reason": "missing",
            })
            continue
        if age > threshold_days:
            out.append({
                "label": label,
                "path": str(path),
                "age_days": round(age, 1),
                "reason": f"age {age:.1f}d > threshold {threshold_days}d",
            })
    return out


# ── State / cooldown ───────────────────────────────────────────────────────


def _load_state(path: Optional[Path] = None) -> dict:
    target = path if path is not None else STATE_FILE
    if not target.exists():
        return {}
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _save_state(state: dict, path: Optional[Path] = None) -> None:
    target = path if path is not None else STATE_FILE
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(f".{os.getpid()}.tmp")
        tmp.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
        os.replace(tmp, target)
    except OSError as exc:
        logger.warning("calendar_staleness: state save failed (%s)", exc)


def _in_cooldown(state: dict, now: Optional[datetime] = None,
                   cooldown_hours: float = COOLDOWN_HOURS) -> bool:
    last = state.get("last_alert_utc")
    if not isinstance(last, str):
        return False
    try:
        last_ts = datetime.fromisoformat(last)
    except ValueError:
        return False
    if last_ts.tzinfo is None:
        last_ts = last_ts.replace(tzinfo=timezone.utc)
    now_dt = now if now is not None else datetime.now(timezone.utc)
    return (now_dt - last_ts).total_seconds() < cooldown_hours * 3600.0


# ── Alert message ──────────────────────────────────────────────────────────


def build_alert_message(stale: list[dict]) -> str:
    lines = ["GTOS ECONOMIC CALENDAR STALE",
             "Refresh from ForexFactory:"]
    for entry in stale:
        path_short = Path(entry["path"]).name
        if entry["age_days"] is None:
            lines.append(f"  - {path_short} MISSING ({entry['reason']})")
        else:
            lines.append(
                f"  - {path_short} age={entry['age_days']:.1f}d "
                f"(threshold {STALENESS_THRESHOLD_DAYS}d)"
            )
    lines.append("")
    lines.append("Procedure:")
    lines.append(
        "  1. https://www.forexfactory.com/calendar  (filter: HIGH impact)"
    )
    lines.append(
        "  2. Hand-edit data/news_calendar.json — update events + updated_at"
    )
    lines.append(
        "  3. git add + commit. Pickup on next orchestrator KZ entry."
    )
    return "\n".join(lines)


# ── Telegram dispatch via notification queue (2026-04-29 fix) ──────────────
#
# Pre-fix this script POSTed directly to api.telegram.org via
# urllib.request.urlopen. The live host has a self-signed certificate in the
# system trust store and every direct HTTPS POST failed with
# [SSL: CERTIFICATE_VERIFY_FAILED]. The watchdog treated exit=2 as "retry
# next heartbeat" + suppressed the once-per-day marker, so the script ran
# every 15 min for days without ever delivering an alert OR cooling down.
#
# The queue path used by src.notifications.notify_alert (HIGH priority)
# bypasses the SSL chain issue (its _default_transport sets
# ssl.CERT_NONE intentionally — see notification_queue.py docstring) and
# persists the alert across process exit so the worker daemon delivers it
# asynchronously.


def enqueue_alert(text: str) -> bool:
    """Enqueue a HIGH-priority alert via src.notifications.notify_alert.

    Returns True iff the enqueue call succeeded (queue file appended). Does
    NOT block on Telegram dispatch — the queue worker drains asynchronously.
    A False return means the queue subsystem itself is unavailable (import
    error, disk error, etc.); callers can retry on the next watchdog tick.
    """
    try:
        # Lazy import: PROJECT_ROOT was added to sys.path at module load,
        # which makes ``src.notifications`` importable. Imported lazily so
        # the test suite's monkeypatch hooks can swap this function out
        # without paying the cost of importing the full notifications module.
        from src.notifications import notify_alert
    except Exception as exc:  # noqa: BLE001
        logger.error(
            "calendar_staleness: cannot import src.notifications.notify_alert (%s) — "
            "queue subsystem unavailable",
            exc,
        )
        return False
    try:
        notify_alert(text)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.error("calendar_staleness: notify_alert raised: %s", exc)
        return False


# ── Main ───────────────────────────────────────────────────────────────────


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    stale = collect_stale_files()
    if not stale:
        logger.info("calendar_staleness: OK — both files fresh")
        return 0

    for entry in stale:
        logger.warning(
            "calendar_staleness: %s STALE (%s)",
            entry["path"], entry["reason"],
        )

    state = _load_state()
    if _in_cooldown(state):
        logger.info(
            "calendar_staleness: %d stale file(s) but in cooldown — "
            "skipping alert", len(stale),
        )
        return 0

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

    if not token or not chat_id:
        logger.warning(
            "calendar_staleness: alert needed but TELEGRAM_BOT_TOKEN/"
            "TELEGRAM_CHAT_ID not set — configure in .env"
        )
        return 1

    msg = build_alert_message(stale)
    # Route through the persistent notification queue (HIGH priority).
    # The queue's _default_transport handles the host's self-signed-SSL
    # quirk + persists the alert across process exit so the dedicated
    # worker daemon delivers it asynchronously. See module docstring for
    # the root-cause write-up.
    if not enqueue_alert(msg):
        return 2

    # Persist last-sent timestamp for cooldown. We write the marker on
    # successful enqueue (not on Telegram receipt) — the queue's retry
    # ladder is responsible for actual delivery; cooldown is a producer-side
    # rate-limit, separate from delivery confirmation.
    state["last_alert_utc"] = datetime.now(timezone.utc).isoformat()
    _save_state(state)
    logger.info(
        "calendar_staleness: alert enqueued for %d stale file(s)", len(stale)
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
