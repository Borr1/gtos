"""Time-in-Trade Shadow Logger (T5.4) — observation-only.

For each closed trade, logs the hypothetical R-multiple outcome if the trade
had been exited at 30, 60, 120, and 240 minutes post-entry, alongside the
actual close outcome. Pure additive; does NOT affect live exits.

Feeds future analysis on whether a time-based exit rule beats the current
"100% at TP1" policy.

Checkpoint semantics:
- Hypothetical exit price at checkpoint T = close of the LAST M15 bar whose
  open-time is <= entry_time + T minutes. (The bar the trader would exit on.)
- If the trade closed before a checkpoint, that checkpoint's `r` is null and
  the record carries `closed_before: true`.
- If bar fetch fails, the row is SKIPPED entirely (no partial/degraded rows)
  and the error logged. Never propagates to the orchestrator.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

SHADOW_LOG_PATH = "shadow_logs/time_in_trade.jsonl"

CHECKPOINTS_MINUTES = (30, 60, 120, 240)


def _compute_r(price: float, entry_price: float, sl_distance: float,
               direction: str) -> float:
    """Compute R-multiple for a hypothetical exit price."""
    if sl_distance <= 0:
        return 0.0
    if direction == "LONG":
        return (price - entry_price) / sl_distance
    return (entry_price - price) / sl_distance


def _checkpoint_record(bar_close_price: float | None,
                       entry_price: float,
                       sl_distance: float,
                       direction: str,
                       closed_before: bool) -> dict:
    """Build per-checkpoint audit record."""
    if closed_before or bar_close_price is None:
        return {"r": None, "bar_close_price": None, "closed_before": closed_before}
    return {
        "r": round(_compute_r(bar_close_price, entry_price, sl_distance, direction), 4),
        "bar_close_price": bar_close_price,
        "closed_before": False,
    }


def compute_time_in_trade_hypotheticals(
    *,
    trade_id: str,
    symbol: str,
    direction: str,
    entry_time: datetime,
    close_time: datetime,
    entry_price: float,
    sl_distance: float,
    actual_close_r: float,
    bar_fetcher,
) -> dict | None:
    """Compute the shadow row for one closed trade.

    `bar_fetcher(date_from, date_to)` is a callable returning a list of M15
    bar dicts with keys {time, open, high, low, close, ...} (same shape as
    `mt5.get_candles_range`). Kept injectable for easy testing.

    Returns the JSONL-shaped dict, or None if we cannot build a meaningful
    record (e.g. bar fetch failed, invalid inputs). Never raises.
    """
    try:
        if sl_distance is None or sl_distance <= 0:
            return None
        if entry_time is None or close_time is None:
            return None
        if entry_time.tzinfo is None:
            entry_time = entry_time.replace(tzinfo=timezone.utc)
        if close_time.tzinfo is None:
            close_time = close_time.replace(tzinfo=timezone.utc)
        if direction not in ("LONG", "SHORT"):
            return None

        # Fetch M15 bars covering entry -> last checkpoint horizon.
        horizon_end = entry_time + timedelta(minutes=max(CHECKPOINTS_MINUTES) + 15)
        bars = bar_fetcher(entry_time, horizon_end)
        if bars is None:
            bars = []

        # Normalize bar times -> aware UTC datetimes.
        normalized: list[tuple[datetime, float]] = []
        for bar in bars:
            t = bar.get("time")
            if t is None:
                continue
            if isinstance(t, str):
                bt = datetime.fromisoformat(t)
                if bt.tzinfo is None:
                    bt = bt.replace(tzinfo=timezone.utc)
            elif isinstance(t, datetime):
                bt = t if t.tzinfo else t.replace(tzinfo=timezone.utc)
            else:
                bt = datetime.fromtimestamp(t, tz=timezone.utc)
            close_price = bar.get("close")
            if close_price is None:
                continue
            normalized.append((bt, float(close_price)))
        normalized.sort(key=lambda x: x[0])

        checkpoints: dict[int, dict] = {}
        any_bar_used = False
        for mins in CHECKPOINTS_MINUTES:
            checkpoint_ts = entry_time + timedelta(minutes=mins)

            # Did the actual trade close before this checkpoint?
            if close_time < checkpoint_ts:
                checkpoints[mins] = _checkpoint_record(
                    bar_close_price=None,
                    entry_price=entry_price,
                    sl_distance=sl_distance,
                    direction=direction,
                    closed_before=True,
                )
                continue

            # Take the close of the last M15 bar whose open-time <= checkpoint_ts.
            bar_price: float | None = None
            for bt, close_price in normalized:
                if bt <= checkpoint_ts:
                    bar_price = close_price
                else:
                    break

            if bar_price is None:
                # Bar not available for this checkpoint — skip gracefully.
                checkpoints[mins] = _checkpoint_record(
                    bar_close_price=None,
                    entry_price=entry_price,
                    sl_distance=sl_distance,
                    direction=direction,
                    closed_before=False,
                )
            else:
                any_bar_used = True
                checkpoints[mins] = _checkpoint_record(
                    bar_close_price=bar_price,
                    entry_price=entry_price,
                    sl_distance=sl_distance,
                    direction=direction,
                    closed_before=False,
                )

        # If the trade closed before the earliest checkpoint AND we got no
        # bars, skip — nothing meaningful to log.
        earliest_cp_ts = entry_time + timedelta(minutes=min(CHECKPOINTS_MINUTES))
        if not any_bar_used and close_time < earliest_cp_ts:
            return None

        return {
            "trade_id": trade_id,
            "symbol": symbol,
            "direction": direction,
            "entry_time": entry_time.isoformat(),
            "close_time": close_time.isoformat(),
            "entry_price": entry_price,
            "sl_distance": sl_distance,
            "actual_close_r": round(float(actual_close_r), 4),
            "hypothetical_30min": checkpoints[30],
            "hypothetical_60min": checkpoints[60],
            "hypothetical_120min": checkpoints[120],
            "hypothetical_240min": checkpoints[240],
            "hypothetical_30min_r": checkpoints[30]["r"],
            "hypothetical_60min_r": checkpoints[60]["r"],
            "hypothetical_120min_r": checkpoints[120]["r"],
            "hypothetical_240min_r": checkpoints[240]["r"],
            "timestamp_logged": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.warning("time_in_trade hypothetical computation failed: %s", e)
        return None


def write_time_in_trade_shadow_log(entry: dict,
                                   log_path: str = SHADOW_LOG_PATH) -> None:
    """Append a time-in-trade shadow row to the JSONL log. Never raises."""
    try:
        path = Path(log_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a") as f:
            f.write(json.dumps(entry) + "\n")
        logger.info(
            "TIME_IN_TRADE_SHADOW: trade=%s actual=%.4fR "
            "30m=%s 60m=%s 120m=%s 240m=%s",
            entry.get("trade_id", "?"),
            entry.get("actual_close_r", 0.0),
            entry.get("hypothetical_30min_r"),
            entry.get("hypothetical_60min_r"),
            entry.get("hypothetical_120min_r"),
            entry.get("hypothetical_240min_r"),
        )
    except Exception as e:
        logger.warning("Failed to write time-in-trade shadow log (non-blocking): %s", e)
