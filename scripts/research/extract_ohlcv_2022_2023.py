"""Extract 2022-01-01 -> 2024-02-20 OHLCV for the 5 instruments missing pre-F14 depth.

The F14 backfill (commit a0e39de, output shadow_logs/structure_detector_backfill_2026.jsonl)
closes the 2024-02-20 -> 2026-04-24 gap for all 7 instruments. This script extends
backfill to 2022-01-01 -> 2024-02-20 for XAUUSD, XAGUSD, USDJPY, GBPUSD, NAS100.

Schema mirrors data/historical_2026/{SYMBOL}_{TF}.csv exactly:
  time,open,high,low,close,volume

Output:
  data/historical_2022_2023/{SYMBOL}_{TF}.csv  (5 syms * 4 TFs = up to 20 files)

NAS100 on redacted_account-Server 2 is named "NDX100"; we save it as NAS100_{TF}.csv to
match the project's canonical instrument code (matches OHLCV_STEM in
src/research_infra/dumb_baseline.py:202).

Phase 1 = $0 API. No Anthropic. No production code modification.
"""

from __future__ import annotations

import csv
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(PROJECT_ROOT / ".env")

import MetaTrader5 as mt5  # noqa: E402

# Symbol mapping: canonical -> FN broker symbol
SYMBOL_MAP = {
    "XAUUSD": "XAUUSD",
    "XAGUSD": "XAGUSD",
    "USDJPY": "USDJPY",
    "GBPUSD": "GBPUSD",
    "NAS100": "NDX100",
}

TIMEFRAMES = [
    ("M15", mt5.TIMEFRAME_M15),
    ("H1", mt5.TIMEFRAME_H1),
    ("H4", mt5.TIMEFRAME_H4),
    ("D1", mt5.TIMEFRAME_D1),
]

START = datetime(2022, 1, 1, tzinfo=timezone.utc)
END = datetime(2024, 2, 20, tzinfo=timezone.utc)

OUT_DIR = PROJECT_ROOT / "data" / "historical_2022_2023"


def extract_one(canonical_sym: str, fn_sym: str, tf_name: str, tf: int) -> int:
    """Extract one (sym, tf) into CSV. Chunks by year if range query exceeds N cap.

    Returns number of bars written.
    """
    out_path = OUT_DIR / f"{canonical_sym}_{tf_name}.csv"
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Try whole window in one call first
    rates = mt5.copy_rates_range(fn_sym, tf, START, END)
    err = mt5.last_error()
    if rates is None or len(rates) == 0:
        # Chunk by 6-month windows
        all_rates = []
        chunk = timedelta(days=180)
        cur = START
        while cur < END:
            nxt = min(cur + chunk, END)
            r = mt5.copy_rates_range(fn_sym, tf, cur, nxt)
            if r is not None and len(r) > 0:
                all_rates.extend(list(r))
            cur = nxt
        rates = all_rates
        if not rates:
            print(f"    {tf_name}: NO DATA via range or chunked range, err={err}")
            return 0

    # Sort + dedupe by timestamp
    seen = set()
    rows = []
    for r in rates:
        ts = int(r["time"])
        if ts in seen:
            continue
        seen.add(ts)
        rows.append(r)
    rows.sort(key=lambda r: r["time"])

    # Write CSV with UTF-8
    with out_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["time", "open", "high", "low", "close", "volume"])
        for r in rows:
            ts = datetime.fromtimestamp(int(r["time"]), tz=timezone.utc)
            time_str = ts.strftime("%Y-%m-%d %H:%M:%S")
            # Use tick_volume; that's what the historical_2026 export uses.
            vol = int(r["tick_volume"])
            w.writerow([
                time_str,
                _fmt_price(float(r["open"])),
                _fmt_price(float(r["high"])),
                _fmt_price(float(r["low"])),
                _fmt_price(float(r["close"])),
                vol,
            ])

    if rows:
        first = datetime.fromtimestamp(int(rows[0]["time"]), tz=timezone.utc)
        last = datetime.fromtimestamp(int(rows[-1]["time"]), tz=timezone.utc)
        print(f"    {tf_name}: n={len(rows):>6} | first={first.strftime('%Y-%m-%d %H:%M')} | last={last.strftime('%Y-%m-%d %H:%M')}")
    return len(rows)


def _fmt_price(p: float) -> str:
    """Format price with up to 5 decimals, mirroring historical_2026 style."""
    # Strip trailing zeros to match the original export style
    if p == int(p):
        return str(p)
    s = f"{p:.5f}".rstrip("0").rstrip(".")
    return s if s else "0"


def main() -> int:
    if not mt5.initialize():
        print(f"FAIL: MT5 initialize: {mt5.last_error()}")
        return 1

    acct = mt5.account_info()
    print(f"MT5 OK: server={acct.server}, account={acct.login}, balance=${acct.balance:,.2f}")
    print(f"Target window: {START} -> {END}")
    print(f"Output: {OUT_DIR}")
    print()

    # Force-select all symbols
    for canonical, fn_sym in SYMBOL_MAP.items():
        if not mt5.symbol_select(fn_sym, True):
            print(f"  WARN: cannot select {fn_sym} (canonical {canonical})")
    time.sleep(2)

    summary = {}
    for canonical, fn_sym in SYMBOL_MAP.items():
        print(f"=== {canonical} (broker: {fn_sym}) ===")
        per_tf = {}
        for tf_name, tf in TIMEFRAMES:
            n = extract_one(canonical, fn_sym, tf_name, tf)
            per_tf[tf_name] = n
        summary[canonical] = per_tf
        print()

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for canonical, per_tf in summary.items():
        line = " | ".join(f"{tf}={n}" for tf, n in per_tf.items())
        print(f"  {canonical}: {line}")

    mt5.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
