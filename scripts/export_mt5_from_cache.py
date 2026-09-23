"""
Export MT5 historical data from local HC cache files (bypasses Python API).
Reads FTMO-Demo binary cache files directly — no MT5 API connection required.

Output: data/historical/<SYMBOL>_<TF>.csv (20 files)
"""

import struct
import os
import sys
from datetime import datetime, timezone, timedelta

# ─── Config ─────────────────────────────────────────────────────────────────

MT5_BASE = (
    r"C:\Users\MSI\AppData\Roaming\MetaQuotes\Terminal"
    r"\D0E8209F77C8CF37AD8BF550E51FF075\bases\FTMO-Demo\history"
)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "historical")

START_TS = int(datetime(2026, 3, 1, tzinfo=timezone.utc).timestamp())
END_TS   = int(datetime(2026, 4, 14, tzinfo=timezone.utc).timestamp())  # exclusive

SYMBOLS = {
    "XAUUSD":    "XAUUSD",
    "US30_cash": "US30.cash",
    "USDJPY":    "USDJPY",
    "GBPJPY":    "GBPJPY",
    "GBPUSD":    "GBPUSD",
}

TIMEFRAMES = {
    "M15":  ("M15.hc",    "%Y-%m-%d %H:%M:%S"),
    "H1":   ("H1.hc",     "%Y-%m-%d %H:%M:%S"),
    "H4":   ("H4.hc",     "%Y-%m-%d %H:%M:%S"),
    "D1":   ("Daily.hc",  "%Y-%m-%d"),
}

HEADER_BYTES = 432  # copyright string header (confirmed across all symbols/TFs)

# ─── Parser ──────────────────────────────────────────────────────────────────

def read_hc(path):
    """
    Parse an MT5 .hc timeframe cache file.

    File layout (all little-endian):
      [504 bytes]  copyright header
      [N_TS × 8]  Unix timestamps (uint64), weekday bars only
      [4]          count field = N_DATA
      [N_DATA × 8] open prices  (double)
      [4]          count field = N_DATA
      [N_DATA × 8] high prices  (double)
      [4]          count field = N_DATA
      [N_DATA × 8] low prices   (double)
      [4]          count field = N_DATA
      [N_DATA × 8] close prices (double)
      [4+...]      volume data  (not parsed)

    Alignment: OHLCV_idx = TS_idx + (N_DATA - N_TS + 2)
    """
    with open(path, "rb") as f:
        data = f.read()

    # ── Timestamps ──────────────────────────────────────────────────────────
    offset = HEADER_BYTES
    timestamps = []
    while offset + 8 <= len(data):
        ts = struct.unpack_from("<Q", data, offset)[0]
        if ts < 500_000_000 or ts > 9_999_999_999:
            break
        try:
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            if not (2000 <= dt.year <= 2030):
                break
        except (OSError, OverflowError, ValueError):
            break
        timestamps.append(ts)
        offset += 8

    N_TS = len(timestamps)
    if N_TS == 0:
        raise ValueError("No timestamps found")

    # ── Count field → N_DATA ────────────────────────────────────────────────
    count_offset = HEADER_BYTES + N_TS * 8
    N_DATA = struct.unpack_from("<I", data, count_offset)[0]

    # ── Column offsets ───────────────────────────────────────────────────────
    #  Each column:  4-byte count field  +  N_DATA × 8-byte doubles
    col_stride = 4 + N_DATA * 8
    O_START = count_offset          + 4          # Opens start (right after count)
    H_START = O_START + N_DATA * 8  + 4          # Highs start (skip opens + count)
    L_START = H_START + N_DATA * 8  + 4          # Lows start
    C_START = L_START + N_DATA * 8  + 4          # Closes start

    # ── OHLCV offset: align TS index to OHLCV index ─────────────────────────
    ohlcv_offset = N_DATA - N_TS + 2  # OHLCV_idx = TS_idx + ohlcv_offset

    # ── Build output rows ────────────────────────────────────────────────────
    rows = []
    for ts_idx, ts in enumerate(timestamps):
        if not (START_TS <= ts < END_TS):
            continue

        ohlcv_idx = ts_idx + ohlcv_offset
        if ohlcv_idx < 0 or ohlcv_idx >= N_DATA:
            continue  # no OHLCV data for this timestamp

        byte_off = ohlcv_idx * 8
        try:
            o = struct.unpack_from("<d", data, O_START + byte_off)[0]
            h = struct.unpack_from("<d", data, H_START + byte_off)[0]
            l = struct.unpack_from("<d", data, L_START + byte_off)[0]
            c = struct.unpack_from("<d", data, C_START + byte_off)[0]
        except struct.error:
            continue

        # Sanity check: valid price range and OHLC consistency
        if not (0 < l <= h and min(o, c) >= l and max(o, c) <= h):
            continue  # bad data

        rows.append((ts, o, h, l, c))

    return rows, N_TS, N_DATA


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    results = []
    errors  = []

    for alias, dir_name in SYMBOLS.items():
        symbol_path = os.path.join(MT5_BASE, dir_name)
        if not os.path.isdir(symbol_path):
            # Try alternate casing for US30
            alt = os.path.join(MT5_BASE, alias.replace("_", "."))
            if os.path.isdir(alt):
                symbol_path = alt
            else:
                msg = f"  SKIP  {alias:12s} — directory not found"
                print(msg)
                errors.append(msg)
                continue

        cache_path = os.path.join(symbol_path, "cache")
        if not os.path.isdir(cache_path):
            msg = f"  SKIP  {alias:12s} — cache directory not found"
            print(msg)
            errors.append(msg)
            continue

        for tf_name, (hc_file, time_fmt) in TIMEFRAMES.items():
            hc_path = os.path.join(cache_path, hc_file)
            if not os.path.isfile(hc_path):
                msg = f"  MISS  {alias:12s} {tf_name:4s} — {hc_file} not found"
                print(msg)
                errors.append(msg)
                continue

            try:
                rows, n_ts, n_data = read_hc(hc_path)
            except Exception as e:
                msg = f"  ERR   {alias:12s} {tf_name:4s} — {e}"
                print(msg)
                errors.append(msg)
                continue

            if not rows:
                msg = f"  EMPTY {alias:12s} {tf_name:4s} — no bars in date range"
                print(msg)
                errors.append(msg)
                continue

            fname = f"{alias}_{tf_name}.csv"
            fpath = os.path.join(OUTPUT_DIR, fname)

            with open(fpath, "w", newline="") as f:
                f.write("time,open,high,low,close,volume\n")
                for (ts, o, h, l, c) in sorted(rows):
                    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                    time_str = dt.strftime(time_fmt)
                    f.write(f"{time_str},{o},{h},{l},{c},0\n")

            n = len(rows)
            first = datetime.fromtimestamp(rows[0][0],  tz=timezone.utc).strftime(time_fmt)
            last  = datetime.fromtimestamp(rows[-1][0], tz=timezone.utc).strftime(time_fmt)
            print(f"  OK    {alias:12s} {tf_name:4s}  {n:5d} candles  {first}  ->  {last}")
            results.append((alias, tf_name, n, first, last))

    print(f"\n{'='*60}")
    print(f"Done.  {len(results)} files written, {len(errors)} issues.")
    if errors:
        print("\nIssues:")
        for e in errors:
            print(e)


if __name__ == "__main__":
    main()
