"""Daily loss-stop dormant-state helpers.

T2.8 risk architecture (session 33). When the MTM daily loss crosses the
configured cap (``risk.max_daily_loss_pct`` — 4% by default), the orchestrator
writes a dormant marker to ``pipeline_state/dormant_state.json`` and stops
making AI calls for the rest of the UTC day. Open positions close naturally
via their own SL/TP (locked decision #5 — no forced flatten).

Why a JSON marker rather than an in-memory flag:
- The 4% stop must survive process restart. If the orchestrator crashes or is
  bounced after trigger, the flag must still be honored through 23:59:59 UTC.
- Other tools (dashboards, watchdog) can read the marker to know why the
  process is idle without shelling out to MT5.
- Clean handoff with the 00:00 UTC clear path — ``new_day`` simply calls
  ``clear_if_stale()`` which unlinks the file when its ``dormant_until_utc_day``
  is no longer today.

Schema (one record, atomic write):

    {
      "dormant_until_utc_day": "2026-04-21",
      "triggered_at_utc":       "2026-04-21T14:07:12Z",
      "trigger_reason":         "daily_loss_stop",
      "equity_at_trigger":      96120.31,
      "daily_pnl_pct_at_trigger": -4.05,
      "max_daily_loss_pct":     4.0,
      "symbol":                 "XAUUSD"   # informational — process that tripped
    }

Module-level path is patchable from tests (the canonical ``tmp_path`` +
monkeypatch pattern; see ``tests/conftest.py`` Layer 1).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.utils.file_io import atomic_write

logger = logging.getLogger(__name__)


# Module-level path — patch via ``monkeypatch.setattr(module, "DORMANT_STATE_PATH", tmp_path / ...)``
# in tests. Never read through a fresh ``Path(...)`` literal elsewhere.
DORMANT_STATE_PATH: Path = Path("pipeline_state/dormant_state.json")


def _today_utc_day() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def load_dormant_state() -> Optional[dict]:
    """Read the dormant marker if present. Returns None on missing/malformed."""
    path = DORMANT_STATE_PATH
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError, json.JSONDecodeError) as e:
        logger.warning("dormant_state.json unreadable, treating as absent: %s", e)
        return None


def is_dormant_today(now: Optional[datetime] = None) -> bool:
    """Return True iff a valid dormant marker exists for today's UTC date.

    Stale markers (``dormant_until_utc_day`` != today) are NOT cleared here
    — that's ``clear_if_stale()``'s job, called from ``_new_day``. A stale
    marker is treated as not-dormant so a mid-day restart doesn't get
    stuck in last-day's dormant state.
    """
    state = load_dormant_state()
    if not state:
        return False
    marker_day = state.get("dormant_until_utc_day")
    if not isinstance(marker_day, str):
        return False
    today = (now or datetime.now(timezone.utc)).strftime("%Y-%m-%d")
    return marker_day == today


def write_dormant_state(*, trigger_reason: str, equity_at_trigger: float,
                        daily_pnl_pct_at_trigger: float,
                        max_daily_loss_pct: float,
                        symbol: str,
                        now: Optional[datetime] = None) -> dict:
    """Persist the dormant marker atomically. Returns the record written."""
    now_utc = now or datetime.now(timezone.utc)
    record = {
        "dormant_until_utc_day": now_utc.strftime("%Y-%m-%d"),
        "triggered_at_utc": now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "trigger_reason": trigger_reason,
        "equity_at_trigger": float(equity_at_trigger),
        "daily_pnl_pct_at_trigger": float(daily_pnl_pct_at_trigger),
        "max_daily_loss_pct": float(max_daily_loss_pct),
        "symbol": symbol,
    }
    DORMANT_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(DORMANT_STATE_PATH, record)
    logger.critical(
        "DAILY_LOSS_STOP_TRIGGERED — dormant until next UTC day. "
        "symbol=%s equity=%.2f pnl=%.2f%% cap=%.2f%% reason=%s",
        symbol, equity_at_trigger, daily_pnl_pct_at_trigger,
        max_daily_loss_pct, trigger_reason,
    )
    return record


def clear_if_stale(now: Optional[datetime] = None) -> bool:
    """Delete the marker if its UTC day is no longer today.

    Called from ``_new_day``. Returns True if a stale marker was cleared.
    """
    state = load_dormant_state()
    if not state:
        return False
    marker_day = state.get("dormant_until_utc_day")
    today = (now or datetime.now(timezone.utc)).strftime("%Y-%m-%d")
    if marker_day == today:
        return False
    try:
        DORMANT_STATE_PATH.unlink(missing_ok=True)
        logger.info("Cleared stale dormant marker (was %s, today is %s)",
                    marker_day, today)
        return True
    except OSError as e:
        logger.warning("Failed to unlink stale dormant marker: %s", e)
        return False


def clear_dormant_state() -> None:
    """Delete the marker unconditionally (manual override / test cleanup)."""
    try:
        DORMANT_STATE_PATH.unlink(missing_ok=True)
    except OSError as e:
        logger.warning("Failed to unlink dormant marker: %s", e)
