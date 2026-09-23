"""P1 — M1 OHLCV backfill from MT5 (redacted_account) for the production 7 instruments.

Strategy
========
For each production instrument:
1. Map canonical -> broker symbol (per ``config/profiles/redacted_account.yaml``).
2. Step backward via ``mt5.copy_rates_from(symbol, M1, end_dt, count=10000)``
   chunks until the broker's M1 history floor is reached (``oldest`` repeats).
3. De-duplicate, sort ascending, and write to
   ``data/historical_2026/{INSTRUMENT}_M1.csv`` in the canonical schema:
   ``time,open,high,low,close,volume`` (UTC, naive ISO ``YYYY-MM-DD HH:MM:SS``).

Hard rules
==========
* No fabrication: if MT5 fails to initialize, ABORT and report.
* No third-party data: MT5 only.
* Existing M15-fallback CSVs in ``data/historical_2026/`` are *NOT* touched
  (only the ``_M1.csv`` outputs are written, separate filenames).
* Document broker M1 cap empirically observed during pull, not assumed.

Empirical broker probe (2026-04-27 22:25 UTC, redacted_account-Server 2):
* All 7 symbols cap M1 history at ~2026-01-14 to 2026-01-20.
* So usable M1 window is ~2026-01-14 -> 2026-04-27 (~3.5 months).
* Older history will be reported as "BROKER_CAP" in the log.

This is not a bug; per the task brief: "If MT5 returns less than 1 year of M1
history (some brokers cap), document the cap + use what's available."
"""

from __future__ import annotations

import csv
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Ensure repo root on path for any imports + .env load
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(str(ROOT / ".env"))

import MetaTrader5 as mt5

# ---------------------------------------------------------------------------
# Configuration — canonical -> broker symbol per FN profile
# ---------------------------------------------------------------------------

SYMBOL_MAP = [
    # (canonical_repo_name, broker_symbol)
    ("XAUUSD",    "XAUUSD"),
    ("US30_cash", "US30"),
    ("USDJPY",    "USDJPY"),
    ("GBPJPY",    "GBPJPY"),
    ("GBPUSD",    "GBPUSD"),
    ("XAGUSD",    "XAGUSD"),
    ("NAS100",    "NDX100"),
]

# Pull range (will clamp at broker's M1 floor automatically)
START_DT = datetime(2024, 3, 1, 0, 0, 0, tzinfo=timezone.utc)
END_DT   = datetime(2026, 4, 28, 0, 0, 0, tzinfo=timezone.utc)

CHUNK_SIZE = 10_000          # broker max per copy_rates_from call
MAX_CHUNKS = 200             # safety cap (200 * 10k = 2M bars / sym)

DATA_DIR = ROOT / "data" / "historical_2026"
LOG_PATH = ROOT / "research" / "m1_backfill_e24_e26_rerun" / "m1_backfill_log.csv"


def pull_m1_history(broker_sym: str, start_dt: datetime, end_dt: datetime) -> list[dict]:
    """Step backward from ``end_dt`` in 10k-bar chunks until ``start_dt`` is
    crossed or the broker's history floor is reached.

    Returns a list of bar dicts (sorted ascending by time, deduplicated).
    """
    seen_times: set[int] = set()
    bars: list[dict] = []
    cursor = end_dt
    last_oldest: datetime | None = None

    for ck in range(1, MAX_CHUNKS + 1):
        rates = mt5.copy_rates_from(broker_sym, mt5.TIMEFRAME_M1, cursor, CHUNK_SIZE)
        if rates is None or len(rates) == 0:
            break
        # Each row is a numpy structured record (time, open, high, low, close, ...)
        oldest_ts = int(rates[0]["time"])
        latest_ts = int(rates[-1]["time"])
        oldest_dt = datetime.fromtimestamp(oldest_ts, tz=timezone.utc)
        latest_dt = datetime.fromtimestamp(latest_ts, tz=timezone.utc)

        new_count = 0
        for row in rates:
            t = int(row["time"])
            if t in seen_times:
                continue
            seen_times.add(t)
            bars.append({
                "time": datetime.fromtimestamp(t, tz=timezone.utc),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low":  float(row["low"]),
                "close": float(row["close"]),
                "volume": int(row["tick_volume"]),
            })
            new_count += 1

        print(f"    chunk {ck:>3d}: got={len(rates)}, new={new_count}, "
              f"oldest={oldest_dt}, latest={latest_dt}, total_bars={len(bars)}")

        # Stop conditions:
        # 1. Reached the requested start
        if oldest_dt <= start_dt:
            print(f"    reached requested start_dt={start_dt}; stopping")
            break
        # 2. Same oldest as previous chunk -> broker's history floor reached
        if last_oldest is not None and oldest_dt == last_oldest:
            print(f"    BROKER_CAP: oldest didn't advance ({oldest_dt}); stopping")
            break
        last_oldest = oldest_dt
        cursor = oldest_dt
        # Tiny pause to avoid MT5 RPC pressure
        time.sleep(0.05)

    # Sort ascending + filter to [start_dt, end_dt]
    bars.sort(key=lambda b: b["time"])
    bars = [b for b in bars if start_dt <= b["time"] <= end_dt]
    return bars


def write_csv(bars: list[dict], out_path: Path) -> int:
    """Write bars to CSV in canonical schema. Returns bytes written."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["time", "open", "high", "low", "close", "volume"])
        for b in bars:
            # Naive ISO YYYY-MM-DD HH:MM:SS to match existing M15 schema
            ts = b["time"].strftime("%Y-%m-%d %H:%M:%S")
            w.writerow([ts, b["open"], b["high"], b["low"], b["close"], b["volume"]])
    return out_path.stat().st_size


def validate_bars(bars: list[dict]) -> dict:
    """Return validation metrics: count, span, weekday-trading-hour gap detection."""
    if not bars:
        return {"rows": 0, "first_ts": None, "last_ts": None, "max_gap_min": None,
                "long_gaps": 0}
    times = [b["time"] for b in bars]
    first = times[0]
    last = times[-1]
    long_gap_threshold = timedelta(hours=4)
    long_gaps = 0
    max_gap = timedelta(0)
    for i in range(1, len(times)):
        delta = times[i] - times[i - 1]
        if delta > max_gap:
            max_gap = delta
        # Only count as "long gap during weekday trading hours" if not weekend
        # Weekend = Friday 21:00 UTC to Sunday 22:00 UTC roughly. Simple heuristic:
        # count gaps > 4h that don't span a Saturday.
        if delta > long_gap_threshold:
            mid = times[i - 1] + delta / 2
            if mid.weekday() != 5:  # not Saturday
                long_gaps += 1
    return {
        "rows": len(bars),
        "first_ts": first.isoformat(),
        "last_ts": last.isoformat(),
        "max_gap_min": int(max_gap.total_seconds() / 60),
        "long_gaps": long_gaps,
    }


def main() -> int:
    print("=" * 70)
    print("M1 BACKFILL — redacted_account-Server 2")
    print("=" * 70)
    print(f"Range: {START_DT} -> {END_DT}")
    print(f"Out dir: {DATA_DIR}")
    print()

    if not mt5.initialize():
        print(f"ABORT: mt5.initialize() failed: {mt5.last_error()}")
        return 1

    acct = mt5.account_info()
    print(f"Account: {acct.login} server={acct.server} balance={acct.balance:.2f}")
    print(f"Trade mode: {acct.trade_mode} (0=demo, 2=real)")
    print()

    log_rows = []
    for canon, broker in SYMBOL_MAP:
        print(f"[{canon}] broker={broker}")
        info = mt5.symbol_info(broker)
        if info is None:
            print(f"  SKIP: broker symbol {broker!r} not found in MT5")
            log_rows.append({
                "canonical_symbol": canon,
                "broker_symbol": broker,
                "status": "BROKER_SYMBOL_NOT_FOUND",
                "rows": 0, "bytes": 0,
                "first_ts": None, "last_ts": None,
                "max_gap_min": None, "long_gaps": None,
                "out_path": None,
            })
            continue

        # Make sure symbol is selected (visible in MarketWatch) so MT5 can serve history
        if not info.visible:
            mt5.symbol_select(broker, True)

        out_path = DATA_DIR / f"{canon}_M1.csv"
        print(f"  Pulling M1 history...")
        bars = pull_m1_history(broker, START_DT, END_DT)
        if not bars:
            print(f"  No M1 bars returned")
            log_rows.append({
                "canonical_symbol": canon,
                "broker_symbol": broker,
                "status": "NO_BARS_RETURNED",
                "rows": 0, "bytes": 0,
                "first_ts": None, "last_ts": None,
                "max_gap_min": None, "long_gaps": None,
                "out_path": str(out_path),
            })
            continue

        nbytes = write_csv(bars, out_path)
        v = validate_bars(bars)
        status = "OK"
        if v["first_ts"] and datetime.fromisoformat(v["first_ts"]) > START_DT + timedelta(days=30):
            status = "BROKER_CAP_PARTIAL"
        print(f"  Wrote {len(bars)} bars ({nbytes/1024:.1f} KB) to {out_path}")
        print(f"  First: {v['first_ts']}  Last: {v['last_ts']}")
        print(f"  Max gap: {v['max_gap_min']} min  Long gaps (weekday>4h): {v['long_gaps']}")
        print(f"  Status: {status}")
        log_rows.append({
            "canonical_symbol": canon,
            "broker_symbol": broker,
            "status": status,
            "rows": v["rows"],
            "bytes": nbytes,
            "first_ts": v["first_ts"],
            "last_ts": v["last_ts"],
            "max_gap_min": v["max_gap_min"],
            "long_gaps": v["long_gaps"],
            "out_path": str(out_path),
        })
        print()

    mt5.shutdown()

    # Write summary log
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "w", newline="") as fh:
        cols = ["canonical_symbol", "broker_symbol", "status", "rows", "bytes",
                "first_ts", "last_ts", "max_gap_min", "long_gaps", "out_path"]
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in log_rows:
            w.writerow(r)
    print(f"Wrote log to {LOG_PATH}")

    print()
    print("=" * 70)
    print("BACKFILL SUMMARY")
    print("=" * 70)
    print(f"{'symbol':<12} {'rows':>10} {'bytes':>12} {'first_ts':<25} {'last_ts':<25} status")
    for r in log_rows:
        print(f"{r['canonical_symbol']:<12} {r['rows']:>10} {r['bytes']:>12} "
              f"{str(r['first_ts'] or '-'):<25} {str(r['last_ts'] or '-'):<25} {r['status']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
