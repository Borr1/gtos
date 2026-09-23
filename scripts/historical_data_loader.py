"""Pre-compute Market State Objects from TradingView CSV exports or MT5.

Usage:
    # From TradingView CSV (one file per timeframe)
    python scripts/historical_data_loader.py --source csv \
        --m15 data/raw/XAUUSD_M15.csv \
        --h1  data/raw/XAUUSD_H1.csv \
        --h4  data/raw/XAUUSD_H4.csv \
        --d1  data/raw/XAUUSD_D1.csv

    # From MT5 (requires MetaTrader5 package — Windows only)
    python scripts/historical_data_loader.py --source mt5 \
        --start 2025-10-01 --end 2026-03-28

    # Replay a single day's London Open
    python scripts/historical_data_loader.py --replay 2026-01-15
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Generator, Optional

# ---------------------------------------------------------------------------
# Ensure the project root is importable when running as a script
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DATA_DIR = _PROJECT_ROOT / "data"
HISTORICAL_DIR = DATA_DIR / "historical"
SESSIONS_DIR = DATA_DIR / "sessions"

TIMEFRAMES = ("D1", "H4", "H1", "M15")

# Lookback counts from agent_config.yaml → data.lookback
LOOKBACK = {"D1": 30, "H4": 80, "H1": 168, "M15": 672}

# M15 candle count per hour = 4
# Asian session: 00:00–07:00 UTC  →  M15 indices for that window
ASIAN_START = time(0, 0)
ASIAN_END = time(7, 0)

# London Open session window for replay
LONDON_OPEN_START = time(7, 0)
LONDON_OPEN_END = time(9, 30)

# Full London session for H/L computation (used as liquidity for NY window)
LONDON_SESSION_START = time(7, 0)
LONDON_SESSION_END = time(13, 0)

# NY Open session window for replay
NY_OPEN_START = time(13, 0)
NY_OPEN_END = time(15, 30)

# Minutes per candle close inside London Open: 07:15, 07:30, … 09:30 → 10 candles
M15_MINUTES = 15


# ═══════════════════════════════════════════════════════════════════════
# 1. CSV Parsing (TradingView format)
# ═══════════════════════════════════════════════════════════════════════

def parse_tradingview_csv(filepath: str | Path) -> list[dict]:
    """Parse a TradingView-exported CSV into a list of candle dicts.

    TradingView CSV columns (typical):
        time, open, high, low, close, Volume  (header varies)

    The ``time`` field may be:
      - ISO-8601 string  (e.g. ``2025-10-01T00:00:00Z``)
      - Unix timestamp   (integer or float)
      - ``YYYY-MM-DD``   (daily)

    Returns a list of dicts sorted by time ascending:
        [{"time": "ISO-string", "open": float, "high": float,
          "low": float, "close": float, "volume": float}, ...]
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"CSV not found: {filepath}")

    candles: list[dict] = []
    with open(filepath, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        # Normalise headers to lowercase
        if reader.fieldnames is None:
            raise ValueError(f"Empty or headerless CSV: {filepath}")
        header_map = {h.strip().lower(): h for h in reader.fieldnames}

        # Find the actual column names (case-insensitive)
        def _col(name: str) -> str:
            for candidate in (name, name.capitalize(), name.upper()):
                if candidate.lower() in header_map:
                    return header_map[candidate.lower()]
            raise KeyError(f"Column '{name}' not found in {list(header_map.values())}")

        time_col = _col("time")
        open_col = _col("open")
        high_col = _col("high")
        low_col = _col("low")
        close_col = _col("close")
        # Volume column is optional
        try:
            vol_col = _col("volume")
        except KeyError:
            vol_col = None

        for row in reader:
            raw_time = row[time_col].strip()
            t = _parse_time(raw_time)
            candle = {
                "time": t,
                "open": float(row[open_col]),
                "high": float(row[high_col]),
                "low": float(row[low_col]),
                "close": float(row[close_col]),
                "volume": float(row[vol_col]) if vol_col and row.get(vol_col) else 0.0,
            }
            candles.append(candle)

    candles.sort(key=lambda c: c["time"])
    logger.info("Parsed %d candles from %s", len(candles), filepath.name)
    return candles


def _parse_time(raw: str) -> str:
    """Normalise a time value to ISO-8601 UTC string."""
    # Try unix timestamp first (integer or float string)
    try:
        ts = float(raw)
        if ts > 1e12:
            ts /= 1000  # milliseconds
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        pass

    # Try ISO-like parse
    for fmt in (
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
    ):
        try:
            dt = datetime.strptime(raw, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            continue

    raise ValueError(f"Cannot parse time value: {raw!r}")


# ═══════════════════════════════════════════════════════════════════════
# 2. MT5 data loading (optional — Windows only)
# ═══════════════════════════════════════════════════════════════════════

_MT5_TF_MAP: dict[str, object] = {}  # populated lazily if MT5 available


def _init_mt5() -> None:
    """Initialise MT5 connection; raises ImportError if not available."""
    import MetaTrader5 as mt5  # type: ignore[import-untyped]

    global _MT5_TF_MAP
    _MT5_TF_MAP = {
        "M15": mt5.TIMEFRAME_M15,
        "H1": mt5.TIMEFRAME_H1,
        "H4": mt5.TIMEFRAME_H4,
        "D1": mt5.TIMEFRAME_D1,
    }
    if not mt5.initialize():
        raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")


def load_mt5_candles(
    symbol: str,
    timeframe: str,
    start: datetime,
    end: datetime,
) -> list[dict]:
    """Pull candles from MT5 for *symbol* / *timeframe* between *start* and *end*."""
    import MetaTrader5 as mt5  # type: ignore[import-untyped]

    tf = _MT5_TF_MAP[timeframe]
    rates = mt5.copy_rates_range(symbol, tf, start, end)
    if rates is None or len(rates) == 0:
        logger.warning("No MT5 data for %s %s", symbol, timeframe)
        return []

    candles = []
    for r in rates:
        dt = datetime.fromtimestamp(r["time"], tz=timezone.utc)
        candles.append({
            "time": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "open": float(r["open"]),
            "high": float(r["high"]),
            "low": float(r["low"]),
            "close": float(r["close"]),
            "volume": float(r["tick_volume"]),
        })
    candles.sort(key=lambda c: c["time"])
    logger.info("MT5: %d %s candles for %s", len(candles), timeframe, symbol)
    return candles


# ═══════════════════════════════════════════════════════════════════════
# 3. Validation
# ═══════════════════════════════════════════════════════════════════════

def validate_candles(candles: list[dict], timeframe: str) -> list[str]:
    """Return a list of warning strings for data quality issues.

    Checks:
      - OHLC relationship: high >= max(open, close), low <= min(open, close)
      - No duplicate timestamps
      - No M15 gaps during London Open weekday hours
      - Missing weekday trading days
    """
    warnings: list[str] = []
    seen_times: set[str] = set()

    for i, c in enumerate(candles):
        t = c["time"]
        o, h, l, cl = c["open"], c["high"], c["low"], c["close"]

        # OHLC integrity
        if h < max(o, cl) - 1e-6:
            warnings.append(f"[{timeframe}] {t}: high {h} < max(open,close) {max(o, cl)}")
        if l > min(o, cl) + 1e-6:
            warnings.append(f"[{timeframe}] {t}: low {l} > min(open,close) {min(o, cl)}")
        if h < l:
            warnings.append(f"[{timeframe}] {t}: high {h} < low {l}")

        # Duplicates
        if t in seen_times:
            warnings.append(f"[{timeframe}] Duplicate timestamp: {t}")
        seen_times.add(t)

    # M15 gap detection during London Open (weekdays only)
    if timeframe == "M15":
        _check_london_gaps(candles, warnings)

    return warnings


def _check_london_gaps(candles: list[dict], warnings: list[str]) -> None:
    """Check for missing M15 candles during London Open on weekdays."""
    london_candles: dict[str, set[str]] = {}  # date_str → set of times
    for c in candles:
        dt = datetime.fromisoformat(c["time"].replace("Z", "+00:00"))
        if dt.weekday() >= 5:  # skip weekends
            continue
        t = dt.time()
        if LONDON_OPEN_START <= t < LONDON_OPEN_END:
            day_str = dt.strftime("%Y-%m-%d")
            london_candles.setdefault(day_str, set()).add(c["time"])

    for day_str, times in sorted(london_candles.items()):
        # Expected: 07:00, 07:15, 07:30, 07:45, 08:00, 08:15, 08:30, 08:45, 09:00, 09:15
        # That's 10 candles (09:30 is the candle that *closes* at 09:30 → opens at 09:15)
        expected = 10
        if len(times) < expected:
            warnings.append(
                f"[M15] {day_str}: only {len(times)}/{expected} "
                f"London Open candles present"
            )


def check_missing_trading_days(
    candles_m15: list[dict],
    start_date: date,
    end_date: date,
) -> list[str]:
    """Warn on weekdays with zero M15 candles."""
    warnings: list[str] = []
    dates_present: set[str] = set()
    for c in candles_m15:
        dt = datetime.fromisoformat(c["time"].replace("Z", "+00:00"))
        dates_present.add(dt.strftime("%Y-%m-%d"))

    d = start_date
    while d <= end_date:
        if d.weekday() < 5:  # weekday
            if d.isoformat() not in dates_present:
                warnings.append(f"Missing trading day: {d.isoformat()}")
        d += timedelta(days=1)
    return warnings


# ═══════════════════════════════════════════════════════════════════════
# 4. Session-level computation
# ═══════════════════════════════════════════════════════════════════════

def compute_session_levels(
    m15_candles: list[dict],
    target_date: date,
) -> dict:
    """Compute Asian session H/L and PDH/PDL for *target_date*.

    Asian session: 00:00–07:00 UTC on *target_date* (from M15 candles).
    PDH/PDL: high/low of the previous trading day.
    """
    prev_day_candles: list[dict] = []
    asian_candles: list[dict] = []

    prev_date = _previous_weekday(target_date)

    for c in m15_candles:
        dt = datetime.fromisoformat(c["time"].replace("Z", "+00:00"))
        c_date = dt.date()
        c_time = dt.time()

        if c_date == prev_date:
            prev_day_candles.append(c)
        elif c_date == target_date and ASIAN_START <= c_time < ASIAN_END:
            asian_candles.append(c)

    asian_high = max((c["high"] for c in asian_candles), default=0.0)
    asian_low = min((c["low"] for c in asian_candles), default=0.0)

    pdh = max((c["high"] for c in prev_day_candles), default=0.0)
    pdl = min((c["low"] for c in prev_day_candles), default=0.0)

    return {
        "asian_high": asian_high,
        "asian_low": asian_low,
        "pdh": pdh,
        "pdl": pdl,
        "session_high": None,
        "session_low": None,
        "london_high": None,
        "london_low": None,
    }


def _previous_weekday(d: date) -> date:
    """Return the previous weekday (Mon–Fri) before *d*."""
    prev = d - timedelta(days=1)
    while prev.weekday() >= 5:
        prev -= timedelta(days=1)
    return prev


# ═══════════════════════════════════════════════════════════════════════
# 5. Equal levels detection (for H4 / H1)
# ═══════════════════════════════════════════════════════════════════════

def detect_equal_levels(
    candles: list[dict],
    side: str,
    tolerance: float = 2.50,
) -> list[dict]:
    """Find equal highs or equal lows within *tolerance* dollars.

    *side*: ``"high"`` or ``"low"``.
    Returns list of ``{"price": float, "count": int, "candle_indices": [int, ...]}``.
    """
    key = "high" if side == "high" else "low"
    levels: list[dict] = []
    used: set[int] = set()

    for i in range(len(candles)):
        if i in used:
            continue
        price_i = candles[i][key]
        group = [i]
        for j in range(i + 1, len(candles)):
            if j in used:
                continue
            if abs(candles[j][key] - price_i) <= tolerance:
                group.append(j)
        if len(group) >= 2:
            avg_price = sum(candles[k][key] for k in group) / len(group)
            levels.append({
                "price": round(avg_price, 2),
                "count": len(group),
                "candle_indices": group,
            })
            used.update(group)

    return levels


# ═══════════════════════════════════════════════════════════════════════
# 6. Build raw_data dict (01_raw_data.json format)
# ═══════════════════════════════════════════════════════════════════════

def build_raw_data(
    all_candles: dict[str, list[dict]],
    target_date: date,
    candle_time: str,
    session_levels: dict,
    equal_level_tolerance: float = 2.50,
    *,
    symbol: str | None = None,
) -> dict:
    """Build the raw_data dict matching Component 1 output format.

    *all_candles* maps timeframe → full sorted candle list.
    *candle_time* is the ISO timestamp of the M15 candle being evaluated.
    Slices each timeframe to the correct lookback ending at *candle_time*.

    *symbol* is the CANONICAL instrument identifier (e.g., ``"XAUUSD"``,
    ``"US30_cash"``) — NOT the broker-specific alias. Stored in the
    returned dict under ``"symbol"`` so downstream consumers can
    distinguish per-instrument behavior (shadow divergence logger
    classification, XAUUSD session-ATR gate in
    ``compute_market_state``). Defaults to ``None`` → an empty-string
    ``symbol`` field is emitted to preserve the pre-fix schema for
    callers that cannot yet thread the symbol through; new callers
    SHOULD pass it explicitly.
    """
    sliced: dict[str, list[dict]] = {}
    for tf in TIMEFRAMES:
        full = all_candles.get(tf, [])
        # Take candles up to and including candle_time
        cutoff = [c for c in full if c["time"] <= candle_time]
        lookback = LOOKBACK.get(tf, len(cutoff))
        sliced[tf] = cutoff[-lookback:]

    # Compute session high/low from M15 candles within the current session window
    session_m15 = []
    london_m15 = []
    candle_dt = datetime.fromisoformat(candle_time.replace("Z", "+00:00"))

    for c in sliced.get("M15", []):
        dt = datetime.fromisoformat(c["time"].replace("Z", "+00:00"))
        if dt.date() == target_date and LONDON_OPEN_START <= dt.time() <= LONDON_OPEN_END:
            session_m15.append(c)
        # London session H/L: 07:00-13:00 UTC, only candles up to current time
        if dt.date() == target_date and LONDON_SESSION_START <= dt.time() < LONDON_SESSION_END:
            if dt <= candle_dt:
                london_m15.append(c)

    updated_levels = dict(session_levels)
    if session_m15:
        updated_levels["session_high"] = max(c["high"] for c in session_m15)
        updated_levels["session_low"] = min(c["low"] for c in session_m15)
    if london_m15:
        updated_levels["london_high"] = max(c["high"] for c in london_m15)
        updated_levels["london_low"] = min(c["low"] for c in london_m15)

    # Equal levels
    h4_candles = sliced.get("H4", [])
    h1_candles = sliced.get("H1", [])

    return {
        "symbol": symbol if symbol is not None else "",
        "timestamp_utc": candle_time,
        "candles": sliced,
        "session_levels": updated_levels,
        "equal_highs_H4": detect_equal_levels(h4_candles, "high", equal_level_tolerance),
        "equal_lows_H4": detect_equal_levels(h4_candles, "low", equal_level_tolerance),
        "equal_highs_H1": detect_equal_levels(h1_candles, "high", equal_level_tolerance),
        "equal_lows_H1": detect_equal_levels(h1_candles, "low", equal_level_tolerance),
        "spread_cents": 20.0,  # historical approximation
        "high_impact_events": [],
        "data_quality": {
            "all_timeframes_complete": all(
                len(sliced.get(tf, [])) >= int(LOOKBACK[tf] * 0.9)
                for tf in TIMEFRAMES
            ),
            "spread_normal": True,
            "mt5_connected": False,
            "timestamp_utc": candle_time,
        },
    }


# ═══════════════════════════════════════════════════════════════════════
# 7. Replay mode — core of the backtesting harness
# ═══════════════════════════════════════════════════════════════════════

def replay_london_open(
    target_date_str: str,
    all_candles: dict[str, list[dict]],
    equal_level_tolerance: float = 2.50,
    *,
    symbol: str | None = None,
) -> Generator[dict, None, None]:
    """Yield one raw_data dict per M15 candle close from 07:00 to 09:30 UTC.

    Each yield contains the FULL lookback data (as if Component 1 ran at that
    moment) plus session levels computed up to that point.  This simulates what
    Component 1 would produce in real time.

    The yielded M15 close times are:
        07:15, 07:30, 07:45, 08:00, 08:15, 08:30, 08:45, 09:00, 09:15, 09:30

    (A candle that *opens* at 07:00 *closes* at 07:15, etc.)

    *symbol* — optional canonical instrument identifier threaded through to
    ``build_raw_data``. See ``build_raw_data`` docstring.
    """
    target_date = date.fromisoformat(target_date_str)

    # Pre-compute session levels (Asian H/L, PDH/PDL)
    m15_all = all_candles.get("M15", [])
    session_levels = compute_session_levels(m15_all, target_date)

    # Generate M15 close times: 07:15, 07:30, … , 09:30
    dt_start = datetime(
        target_date.year, target_date.month, target_date.day,
        7, M15_MINUTES, tzinfo=timezone.utc,
    )
    dt_end = datetime(
        target_date.year, target_date.month, target_date.day,
        9, 30, tzinfo=timezone.utc,
    )

    current = dt_start
    while current <= dt_end:
        candle_time = current.strftime("%Y-%m-%dT%H:%M:%SZ")

        raw_data = build_raw_data(
            all_candles,
            target_date,
            candle_time,
            session_levels,
            equal_level_tolerance,
            symbol=symbol,
        )
        yield raw_data

        current += timedelta(minutes=M15_MINUTES)


def replay_ny_open(
    target_date_str: str,
    all_candles: dict[str, list[dict]],
    equal_level_tolerance: float = 2.50,
    *,
    symbol: str | None = None,
) -> Generator[dict, None, None]:
    """Yield one raw_data dict per M15 candle close from 13:00 to 15:30 UTC.

    Similar to replay_london_open but for the NY Open kill zone.
    The yielded M15 close times are:
        13:15, 13:30, 13:45, 14:00, 14:15, 14:30, 14:45, 15:00, 15:15, 15:30

    *symbol* — optional canonical instrument identifier threaded through to
    ``build_raw_data``. See ``build_raw_data`` docstring.
    """
    target_date = date.fromisoformat(target_date_str)

    # Pre-compute session levels (Asian H/L, PDH/PDL — same as London)
    m15_all = all_candles.get("M15", [])
    session_levels = compute_session_levels(m15_all, target_date)

    # Generate M15 close times: 13:15, 13:30, … , 15:30
    dt_start = datetime(
        target_date.year, target_date.month, target_date.day,
        13, M15_MINUTES, tzinfo=timezone.utc,
    )
    dt_end = datetime(
        target_date.year, target_date.month, target_date.day,
        15, 30, tzinfo=timezone.utc,
    )

    current = dt_start
    while current <= dt_end:
        candle_time = current.strftime("%Y-%m-%dT%H:%M:%SZ")

        raw_data = build_raw_data(
            all_candles,
            target_date,
            candle_time,
            session_levels,
            equal_level_tolerance,
            symbol=symbol,
        )
        yield raw_data

        current += timedelta(minutes=M15_MINUTES)


def _parse_hhmm(hhmm: str) -> tuple[int, int]:
    """Parse 'HH:MM' string into (hour, minute) tuple."""
    parts = hhmm.split(":")
    return int(parts[0]), int(parts[1])


def replay_kill_zone(
    target_date_str: str,
    all_candles: dict[str, list[dict]],
    kz_start: str = "07:00",
    kz_end: str = "09:30",
    equal_level_tolerance: float = 2.50,
    *,
    symbol: str | None = None,
) -> Generator[dict, None, None]:
    """Yield one raw_data dict per M15 candle close within a configurable window.

    *kz_start* and *kz_end* are 'HH:MM' UTC strings.  The first candle
    yielded closes at kz_start + 15 min; the last closes at kz_end.

    This is the generic replacement for replay_london_open / replay_ny_open.

    *symbol* — optional canonical instrument identifier threaded through to
    ``build_raw_data``. See ``build_raw_data`` docstring.
    """
    target_date = date.fromisoformat(target_date_str)

    m15_all = all_candles.get("M15", [])
    session_levels = compute_session_levels(m15_all, target_date)

    sh, sm = _parse_hhmm(kz_start)
    eh, em = _parse_hhmm(kz_end)

    # First candle closes at start + 15 min
    dt_start = datetime(
        target_date.year, target_date.month, target_date.day,
        sh, sm, tzinfo=timezone.utc,
    ) + timedelta(minutes=M15_MINUTES)

    dt_end = datetime(
        target_date.year, target_date.month, target_date.day,
        eh, em, tzinfo=timezone.utc,
    )

    current = dt_start
    while current <= dt_end:
        candle_time = current.strftime("%Y-%m-%dT%H:%M:%SZ")

        raw_data = build_raw_data(
            all_candles,
            target_date,
            candle_time,
            session_levels,
            equal_level_tolerance,
            symbol=symbol,
        )
        yield raw_data

        current += timedelta(minutes=M15_MINUTES)


# ═══════════════════════════════════════════════════════════════════════
# 8. Pre-compute session files for full date range
# ═══════════════════════════════════════════════════════════════════════

def precompute_sessions(
    all_candles: dict[str, list[dict]],
    start_date: date,
    end_date: date,
    output_dir: Path | None = None,
    equal_level_tolerance: float = 2.50,
    *,
    symbol: str | None = None,
) -> int:
    """Pre-compute one JSON file per trading day in *output_dir*.

    Each file contains the replay data for all London Open M15 candles
    on that day.  Returns the number of session files written.
    """
    output_dir = output_dir or SESSIONS_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    m15_all = all_candles.get("M15", [])
    count = 0
    d = start_date
    while d <= end_date:
        if d.weekday() >= 5:
            d += timedelta(days=1)
            continue

        # Check that we have any M15 data for this day
        day_str = d.isoformat()
        has_data = any(
            c["time"].startswith(day_str)
            for c in m15_all
        )
        if not has_data:
            d += timedelta(days=1)
            continue

        session_levels = compute_session_levels(m15_all, d)

        snapshots = list(replay_london_open(
            day_str, all_candles, equal_level_tolerance, symbol=symbol,
        ))

        session_data = {
            "date": day_str,
            "session_levels": session_levels,
            "candle_count": len(snapshots),
            "snapshots": snapshots,
        }

        outpath = output_dir / f"{day_str}.json"
        with open(outpath, "w") as fh:
            json.dump(session_data, fh, indent=2)
        count += 1

        if count % 20 == 0:
            logger.info("  … %d sessions written", count)
        d += timedelta(days=1)

    logger.info("Wrote %d session files to %s", count, output_dir)
    return count


# ═══════════════════════════════════════════════════════════════════════
# 9. Save historical CSV (unified internal format)
# ═══════════════════════════════════════════════════════════════════════

def save_candles_csv(candles: list[dict], filepath: Path) -> None:
    """Write candles to CSV in the internal canonical format."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["time", "open", "high", "low", "close", "volume"])
        writer.writeheader()
        for c in candles:
            writer.writerow(c)
    logger.info("Saved %d candles → %s", len(candles), filepath)


# ═══════════════════════════════════════════════════════════════════════
# 10. CLI
# ═══════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Load historical XAUUSD data for backtesting.",
    )
    parser.add_argument(
        "--source", choices=["csv", "mt5"], default="csv",
        help="Data source (default: csv)",
    )

    # CSV source args
    parser.add_argument("--m15", type=str, help="Path to M15 CSV")
    parser.add_argument("--h1", type=str, help="Path to H1 CSV")
    parser.add_argument("--h4", type=str, help="Path to H4 CSV")
    parser.add_argument("--d1", type=str, help="Path to D1 CSV")
    # Shortcut: single --input for M15-only (derives others if missing)
    parser.add_argument("--input", type=str, help="Path to M15 CSV (shortcut for --m15)")

    # MT5 source args
    parser.add_argument("--start", type=str, default="2025-10-01")
    parser.add_argument("--end", type=str, default="2026-03-28")
    parser.add_argument("--symbol", type=str, default="XAUUSD")

    # Replay single day
    parser.add_argument("--replay", type=str, help="Replay a single day (YYYY-MM-DD)")

    # Output control
    parser.add_argument("--out-historical", type=str, default=str(HISTORICAL_DIR))
    parser.add_argument("--out-sessions", type=str, default=str(SESSIONS_DIR))
    parser.add_argument("--skip-sessions", action="store_true",
                        help="Skip pre-computing session files")

    args = parser.parse_args()

    start_date = date.fromisoformat(args.start)
    end_date = date.fromisoformat(args.end)
    hist_dir = Path(args.out_historical)
    sess_dir = Path(args.out_sessions)

    # ── Load candles ──────────────────────────────────────────────
    all_candles: dict[str, list[dict]] = {}

    if args.source == "mt5":
        logger.info("Loading from MT5 …")
        try:
            _init_mt5()
        except (ImportError, RuntimeError) as exc:
            logger.error("MT5 not available: %s", exc)
            logger.error("Use --source csv with TradingView exports instead.")
            sys.exit(1)

        dt_start = datetime(start_date.year, start_date.month, start_date.day,
                            tzinfo=timezone.utc)
        dt_end = datetime(end_date.year, end_date.month, end_date.day,
                          23, 59, 59, tzinfo=timezone.utc)

        for tf in TIMEFRAMES:
            candles = load_mt5_candles(args.symbol, tf, dt_start, dt_end)
            all_candles[tf] = candles
            save_candles_csv(candles, hist_dir / f"XAUUSD_{tf}.csv")

    elif args.source == "csv":
        m15_path = args.m15 or args.input
        if not m15_path:
            parser.error("--m15 (or --input) is required with --source csv")

        all_candles["M15"] = parse_tradingview_csv(m15_path)
        save_candles_csv(all_candles["M15"], hist_dir / "XAUUSD_M15.csv")

        for tf, arg_val in [("H1", args.h1), ("H4", args.h4), ("D1", args.d1)]:
            if arg_val:
                all_candles[tf] = parse_tradingview_csv(arg_val)
                save_candles_csv(all_candles[tf], hist_dir / f"XAUUSD_{tf}.csv")
            else:
                logger.warning("No %s CSV provided — that timeframe will be empty", tf)
                all_candles[tf] = []

    # ── Validate ──────────────────────────────────────────────────
    logger.info("Validating candle data …")
    total_warnings = 0
    for tf in TIMEFRAMES:
        warns = validate_candles(all_candles.get(tf, []), tf)
        for w in warns[:10]:
            logger.warning(w)
        if len(warns) > 10:
            logger.warning("  … and %d more %s warnings", len(warns) - 10, tf)
        total_warnings += len(warns)

    day_warns = check_missing_trading_days(
        all_candles.get("M15", []), start_date, end_date,
    )
    for w in day_warns[:20]:
        logger.warning(w)
    if len(day_warns) > 20:
        logger.warning("  … and %d more missing-day warnings", len(day_warns) - 20)
    total_warnings += len(day_warns)

    logger.info("Validation complete: %d total warnings", total_warnings)

    # ── Replay single day ────────────────────────────────────────
    if args.replay:
        logger.info("Replaying London Open for %s …", args.replay)
        for i, raw_data in enumerate(
            replay_london_open(args.replay, all_candles, symbol=args.symbol)
        ):
            logger.info(
                "  Candle %02d: %s  M15=%d  H1=%d  H4=%d  D1=%d",
                i + 1,
                raw_data["timestamp_utc"],
                len(raw_data["candles"].get("M15", [])),
                len(raw_data["candles"].get("H1", [])),
                len(raw_data["candles"].get("H4", [])),
                len(raw_data["candles"].get("D1", [])),
            )
        return

    # ── Pre-compute session files ─────────────────────────────────
    if not args.skip_sessions:
        logger.info("Pre-computing session files …")
        n = precompute_sessions(
            all_candles, start_date, end_date, sess_dir,
            symbol=args.symbol,
        )
        logger.info("Done. %d sessions ready for backtesting.", n)
    else:
        logger.info("Skipping session pre-computation (--skip-sessions).")

    logger.info("Historical data loading complete.")


if __name__ == "__main__":
    main()
