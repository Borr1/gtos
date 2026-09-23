"""J46-J49 v2 Shadow Logger — replay OLD policy on closed J46-J49 trades.

Each closed trade records:
  - actual realized R under the NEW J46-J49 policy (live exit)
  - hypothetical R under the OLD policy (100% close at AI-emitted TP1 or
    SL; adverse-first when both touch in the same bar)

Output: shadow_logs/j46_j49_shadow_outcomes.jsonl (one row per fill).
Failures emit a row with hypothetical_old=null + error; never raises.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)

SHADOW_LOG_PATH = "shadow_logs/j46_j49_shadow_outcomes.jsonl"
POLICY_VERSION = "j46_j49_v2_2026_04_28"


def _normalize_bar_time(t) -> Optional[datetime]:
    if t is None:
        return None
    if isinstance(t, datetime):
        return t if t.tzinfo else t.replace(tzinfo=timezone.utc)
    if isinstance(t, str):
        try:
            bt = datetime.fromisoformat(t)
            return bt if bt.tzinfo else bt.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    try:
        return datetime.fromtimestamp(float(t), tz=timezone.utc)
    except (ValueError, TypeError, OSError):
        return None


def _replay_old_policy(
    *,
    entry_price: float,
    original_sl: float,
    original_ai_tp1: float,
    sl_distance: float,
    direction: str,
    entry_time: datetime,
    actual_exit_time: datetime,
    bars: list[dict],
) -> dict:
    """Walk M1 bars; resolve OLD-policy outcome.

    Logic:
    - SL touched first -> hypothetical_old_R = -1.0
    - TP1 touched first -> hypothetical_old_R = (tp1 - entry) / sl_distance (LONG)
                                           or (entry - tp1) / sl_distance (SHORT)
    - Both touched same bar -> adverse-first: SL wins
    - Neither by actual_exit_time -> signed close-of-last-bar return in R units
    """
    if direction not in ("LONG", "SHORT"):
        raise ValueError(f"unsupported direction: {direction!r}")
    if sl_distance <= 0:
        raise ValueError("sl_distance must be > 0")

    norm: list[tuple[datetime, dict]] = []
    for b in bars:
        bt = _normalize_bar_time(b.get("time"))
        if bt is None:
            continue
        if "high" not in b or "low" not in b or "close" not in b:
            continue
        norm.append((bt, b))
    norm.sort(key=lambda x: x[0])

    if not norm:
        raise ValueError("no usable bars in replay window")

    last_close: Optional[float] = None
    last_time: Optional[datetime] = None

    for bar_time, b in norm:
        if bar_time + timedelta(minutes=1) < entry_time:
            continue
        if bar_time > actual_exit_time:
            break

        high = float(b["high"])
        low = float(b["low"])
        close_px = float(b["close"])
        last_close = close_px
        last_time = bar_time

        if direction == "LONG":
            sl_touched = low <= original_sl
            tp_touched = high >= original_ai_tp1
        else:
            sl_touched = high >= original_sl
            tp_touched = low <= original_ai_tp1

        if sl_touched:
            return {
                "exit_price": float(original_sl),
                "exit_time": bar_time.isoformat(),
                "exit_reason": "old_sl_hit",
                "hypothetical_R": -1.0,
            }
        if tp_touched:
            if direction == "LONG":
                r = (original_ai_tp1 - entry_price) / sl_distance
            else:
                r = (entry_price - original_ai_tp1) / sl_distance
            return {
                "exit_price": float(original_ai_tp1),
                "exit_time": bar_time.isoformat(),
                "exit_reason": "old_tp1_hit",
                "hypothetical_R": round(float(r), 4),
            }

    if last_close is None or last_time is None:
        last_time, last_bar = norm[-1]
        last_close = float(last_bar["close"])

    if direction == "LONG":
        r = (last_close - entry_price) / sl_distance
    else:
        r = (entry_price - last_close) / sl_distance
    return {
        "exit_price": float(last_close),
        "exit_time": last_time.isoformat(),
        "exit_reason": "old_open_at_actual_exit",
        "hypothetical_R": round(float(r), 4),
    }


def compute_j46_j49_shadow(
    *,
    fill_id: str,
    instrument: str,
    direction: str,
    entry_time: datetime,
    exit_time: datetime,
    entry_price: float,
    original_sl: float,
    original_ai_tp1: float,
    sl_distance: Optional[float],
    actual_exit_price: float,
    actual_exit_time: datetime,
    actual_r: float,
    actual_exit_reason: str,
    bar_fetcher: Callable[[datetime, datetime], Optional[list[dict]]],
) -> dict:
    """Build one shadow row for a closed trade. NEVER raises.

    Returns dict shaped for write_j46_j49_shadow_log().
    """
    if entry_time.tzinfo is None:
        entry_time = entry_time.replace(tzinfo=timezone.utc)
    if exit_time.tzinfo is None:
        exit_time = exit_time.replace(tzinfo=timezone.utc)
    if actual_exit_time.tzinfo is None:
        actual_exit_time = actual_exit_time.replace(tzinfo=timezone.utc)

    base = {
        "fill_id": fill_id,
        "instrument": instrument,
        "direction": direction,
        "entry_time": entry_time.isoformat(),
        "exit_time": exit_time.isoformat(),
        "entry_price": entry_price,
        "original_sl": original_sl,
        "original_ai_tp1": original_ai_tp1,
        "actual_close": {
            "exit_price": actual_exit_price,
            "exit_time": actual_exit_time.isoformat(),
            "exit_reason": actual_exit_reason,
            "realized_R": round(float(actual_r), 4),
        },
        "policy_version": POLICY_VERSION,
        "timestamp_logged": datetime.now(timezone.utc).isoformat(),
    }

    if sl_distance is None or sl_distance <= 0:
        try:
            sl_distance = abs(entry_price - original_sl)
        except Exception:
            sl_distance = 0.0
    if sl_distance is None or sl_distance <= 0:
        base["hypothetical_old"] = None
        base["error"] = "sl_distance unavailable or non-positive"
        return base

    if not original_ai_tp1 or original_ai_tp1 <= 0:
        base["hypothetical_old"] = None
        base["error"] = "original_ai_tp1 unavailable"
        return base

    fetch_from = entry_time - timedelta(minutes=2)
    fetch_to = actual_exit_time + timedelta(minutes=5)

    try:
        bars = bar_fetcher(fetch_from, fetch_to)
    except Exception as e:
        logger.warning(
            "j46_j49 bar_fetcher raised for fill=%s: %s", fill_id, e,
        )
        base["hypothetical_old"] = None
        base["error"] = f"bar_fetcher raised: {e!r}"
        return base

    if bars is None or len(bars) == 0:
        base["hypothetical_old"] = None
        base["error"] = "bar_fetcher returned no bars"
        return base

    try:
        hypo = _replay_old_policy(
            entry_price=entry_price,
            original_sl=original_sl,
            original_ai_tp1=original_ai_tp1,
            sl_distance=float(sl_distance),
            direction=direction,
            entry_time=entry_time,
            actual_exit_time=actual_exit_time,
            bars=bars,
        )
    except Exception as e:
        logger.warning(
            "j46_j49 replay failed for fill=%s: %s", fill_id, e,
        )
        base["hypothetical_old"] = None
        base["error"] = f"replay failed: {e!r}"
        return base

    base["hypothetical_old"] = {
        "exit_price": hypo["exit_price"],
        "exit_reason": hypo["exit_reason"],
        "hypothetical_R": hypo["hypothetical_R"],
    }
    base["delta_r"] = round(float(actual_r) - float(hypo["hypothetical_R"]), 4)
    base["shadow_better"] = base["delta_r"] > 0
    return base


def write_j46_j49_shadow_log(
    entry: dict,
    log_path: str = SHADOW_LOG_PATH,
) -> None:
    """Append one row to the JSONL log. NEVER raises."""
    try:
        path = Path(log_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a") as f:
            f.write(json.dumps(entry) + "\n")
        if entry.get("hypothetical_old") is not None:
            logger.info(
                "J46_J49_SHADOW: fill=%s actual=%.4fR hypo_old=%.4fR "
                "delta=%+.4fR reason=%s",
                entry.get("fill_id", "?"),
                entry.get("actual_close", {}).get("realized_R", 0.0),
                entry["hypothetical_old"].get("hypothetical_R", 0.0),
                entry.get("delta_r", 0.0),
                entry["hypothetical_old"].get("exit_reason", "?"),
            )
        else:
            logger.info(
                "J46_J49_SHADOW: fill=%s actual=%.4fR hypo_old=NONE error=%s",
                entry.get("fill_id", "?"),
                entry.get("actual_close", {}).get("realized_R", 0.0),
                entry.get("error", "?"),
            )
    except Exception as e:
        logger.warning(
            "Failed to write j46_j49 shadow log (non-blocking): %s", e,
        )
