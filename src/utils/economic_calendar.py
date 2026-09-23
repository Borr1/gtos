"""Economic calendar loader and event-blocking logic.

Blocks new trade entries near high-impact economic events.

**Known limitation**: The calendar filter blocks NEW trades near events.
It does NOT close existing trades. If the system has an open position and
a high-impact event approaches, the existing trade's SL/TP are broker-side
and will execute. However, gap risk through the SL is real — a $40 NFP move
can gap past an $8 SL.

The 2-hour pre-block window means the system won't ENTER a trade within
2 hours of an event, so most trades will have hit TP/SL or timed out
before the event occurs (average hold time ~45 minutes).

Future enhancement: optional pre-event position closing.
"""

from __future__ import annotations

import csv
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Default config values
_DEFAULT_PRE_BLOCK_MINUTES = 120
_DEFAULT_POST_BLOCK_MINUTES = 30
_DEFAULT_IMPACT_LEVELS = ["HIGH"]
_DEFAULT_CURRENCY_MAP = {
    "XAUUSD": ["USD"],
    "GBPUSD": ["USD", "GBP"],
    "EURUSD": ["USD", "EUR"],
    "NAS100": ["USD"],
    "XAGUSD": ["USD"],
}


def load_calendar(filepath: str = "data/economic_calendar.csv") -> list[dict]:
    """Load economic calendar events from CSV.

    Returns list of event dicts with keys:
        datetime_utc, event, impact, currency, estimated
    Rows that fail to parse are skipped with a warning.
    """
    path = Path(filepath)
    if not path.exists():
        logger.warning("No economic calendar file at %s", filepath)
        return []

    events: list[dict] = []
    has_estimated = False

    try:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, start=2):
                try:
                    date_str = row["date"].strip()
                    time_str = row["time_utc"].strip()
                    event_dt = datetime.strptime(
                        f"{date_str} {time_str}", "%Y-%m-%d %H:%M"
                    ).replace(tzinfo=timezone.utc)

                    estimated = row.get("estimated", "").strip().lower() == "true"
                    if estimated:
                        has_estimated = True

                    events.append({
                        "datetime_utc": event_dt,
                        "event": row.get("event", "").strip(),
                        "impact": row.get("impact", "").strip().upper(),
                        "currency": row.get("currency", "").strip().upper(),
                        "estimated": estimated,
                    })
                except (KeyError, ValueError) as e:
                    logger.warning(
                        "Skipping malformed calendar row %d: %s (row=%s)",
                        row_num, e, row,
                    )
    except Exception as e:
        logger.warning("Failed to read economic calendar %s: %s", filepath, e)
        return []

    if has_estimated:
        logger.warning(
            "Calendar contains estimated dates — verify against real calendar "
            "(ForexFactory, Fed schedule, BOE schedule) before live trading"
        )

    if events:
        now = datetime.now(timezone.utc)
        upcoming = [e for e in events if e["datetime_utc"] > now]
        next_7d = [e for e in upcoming
                    if e["datetime_utc"] < now + timedelta(days=7)]
        if not next_7d:
            logger.warning(
                "No upcoming events in calendar within next 7 days — "
                "calendar may be outdated"
            )
        logger.info("Loaded %d economic calendar events (%d upcoming)", len(events), len(upcoming))
    else:
        logger.warning("Economic calendar loaded but contains 0 events")

    return events


def get_blocking_events(
    calendar: list[dict],
    current_time: datetime,
    symbol: str,
    config: dict,
) -> list[dict]:
    """Return events that should block trading for the given symbol right now.

    Logic:
    1. Get relevant currencies for this symbol from config
    2. Filter calendar to those currencies + configured impact levels
    3. Find events within [current_time - post_block, current_time + pre_block]
    4. Return matching events
    """
    if not calendar:
        return []

    cal_cfg = config.get("economic_calendar", {})
    pre_block = cal_cfg.get("block_before_minutes", _DEFAULT_PRE_BLOCK_MINUTES)
    post_block = cal_cfg.get("block_after_minutes", _DEFAULT_POST_BLOCK_MINUTES)
    impact_levels = [lvl.upper() for lvl in
                     cal_cfg.get("block_impact_levels", _DEFAULT_IMPACT_LEVELS)]

    currency_map = cal_cfg.get("currency_map", _DEFAULT_CURRENCY_MAP)
    relevant_currencies = set(
        c.upper() for c in currency_map.get(symbol.upper(), ["USD"])
    )

    window_start = current_time - timedelta(minutes=post_block)
    window_end = current_time + timedelta(minutes=pre_block)

    blocking = []
    for event in calendar:
        if event["impact"] not in impact_levels:
            continue
        if event["currency"] not in relevant_currencies:
            continue
        if window_start <= event["datetime_utc"] <= window_end:
            blocking.append(event)

    return blocking


def should_block_trading(
    calendar: list[dict],
    current_time: datetime,
    symbol: str,
    config: dict,
) -> tuple[bool, Optional[str]]:
    """Check if trading should be blocked for the given symbol right now.

    Returns:
        (should_block, reason_string)
        reason_string example: "NFP in 47 minutes" or "FOMC was 12 minutes ago"
    """
    blocking = get_blocking_events(calendar, current_time, symbol, config)
    if not blocking:
        return False, None

    # Pick the closest event for the reason string
    closest = min(blocking, key=lambda e: abs(
        (e["datetime_utc"] - current_time).total_seconds()
    ))

    delta = closest["datetime_utc"] - current_time
    delta_minutes = int(delta.total_seconds() / 60)

    if delta_minutes > 0:
        reason = f"{closest['event']} in {delta_minutes} minutes"
    elif delta_minutes == 0:
        reason = f"{closest['event']} happening NOW"
    else:
        reason = f"{closest['event']} was {abs(delta_minutes)} minutes ago"

    return True, reason
