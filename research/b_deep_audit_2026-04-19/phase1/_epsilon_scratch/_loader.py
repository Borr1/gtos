"""Shared data loader for Agent ε liquidity-arbitrage investigation.

All paths absolute. Read-only.
"""
from __future__ import annotations

import csv
import glob
import json
import os
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(r"C:/Users/MSI/Documents/ai-trading-agent")

# -----------------------------------------------------------------------------
# Per-instrument tick sizes for stop-hunt detection (±2 ticks tolerance)
# -----------------------------------------------------------------------------
# Aligned with session 35 Tier A1 EPSILON_BY_SYMBOL (tick*2 values).
TICK_SIZE = {
    "XAUUSD": 0.10,
    "US30":   1.0,
    "NAS100": 1.0,
    "USDJPY": 0.01,
    "GBPJPY": 0.01,
    "EURUSD": 0.00001,
    "GBPUSD": 0.00001,
}

# Fill epsilon (2x tick by default) — conservative
FILL_EPS = {
    "XAUUSD": 0.20,
    "US30":   2.0,
    "NAS100": 2.0,
    "USDJPY": 0.02,
    "GBPJPY": 0.02,
    "EURUSD": 0.0002,
    "GBPUSD": 0.0002,
}

# -----------------------------------------------------------------------------
# M15 CSV loader — cached
# -----------------------------------------------------------------------------
_CSV_CACHE: Dict[str, List[dict]] = {}

def load_m15(symbol: str) -> List[dict]:
    """Load M15 OHLCV for a symbol. Returns list sorted by time (UTC).

    Each row: {"t": datetime (UTC naive), "open", "high", "low", "close", "volume"}.
    """
    if symbol in _CSV_CACHE:
        return _CSV_CACHE[symbol]
    # Handle US30 filename quirk
    filename_map = {"US30": "US30_cash_M15.csv"}
    fn = filename_map.get(symbol, f"{symbol}_M15.csv")
    p = ROOT / "data" / "historical_2026" / fn
    out: List[dict] = []
    with open(p, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            t = datetime.strptime(row["time"], "%Y-%m-%d %H:%M:%S")
            out.append({
                "t": t,
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"]),
            })
    out.sort(key=lambda x: x["t"])
    _CSV_CACHE[symbol] = out
    return out


def _parse_iso(ts: str) -> datetime:
    # Normalize Z / +00:00 to naive UTC
    if ts.endswith("Z"):
        return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
    # drop tz info
    if "+" in ts:
        ts = ts.split("+")[0]
    if "." in ts:
        ts = ts.split(".")[0]
    return datetime.fromisoformat(ts)


def candles_between(symbol: str, t_start: datetime, t_end: datetime) -> List[dict]:
    """Inclusive-exclusive slice of M15 between t_start (inclusive) and t_end (exclusive)."""
    candles = load_m15(symbol)
    times = [c["t"] for c in candles]
    a = bisect_left(times, t_start)
    b = bisect_left(times, t_end)
    return candles[a:b]


def first_candle_at_or_after(symbol: str, t: datetime) -> Optional[Tuple[int, dict]]:
    candles = load_m15(symbol)
    times = [c["t"] for c in candles]
    i = bisect_left(times, t)
    if i >= len(candles):
        return None
    return i, candles[i]


def candles_forward(symbol: str, t_start: datetime, n_candles: int) -> List[dict]:
    """Return up to n_candles candles AFTER t_start."""
    candles = load_m15(symbol)
    times = [c["t"] for c in candles]
    i = bisect_right(times, t_start)
    return candles[i:i + n_candles]


# -----------------------------------------------------------------------------
# T7 simulation JSON loaders
# -----------------------------------------------------------------------------
def load_xauusd_t7() -> List[dict]:
    with open(ROOT / "research" / "t7_live_simulation" / "all_results_jan_apr10.json", "r", encoding="utf-8") as f:
        d = json.load(f)
    for r in d["results"]:
        r["_symbol"] = "XAUUSD"
    return d["results"]


def load_nas100_t7() -> List[dict]:
    """NAS100 is split into 5 slices under t3_1_eurusd_nas100_validation_2026-04-19."""
    out: List[dict] = []
    base = ROOT / "research" / "t3_1_eurusd_nas100_validation_2026-04-19"
    for i in range(1, 6):
        p = base / f"nas100_slice_{i}" / "NAS100_t7_simulation.json"
        with open(p, "r", encoding="utf-8") as f:
            d = json.load(f)
        for r in d["results"]:
            r["_symbol"] = "NAS100"
            r["_slice"] = i
            out.append(r)
    return out


def load_eurusd_t7() -> List[dict]:
    with open(ROOT / "research" / "t7_live_simulation" / "EURUSD_t7_simulation.json", "r", encoding="utf-8") as f:
        d = json.load(f)
    for r in d["results"]:
        r["_symbol"] = "EURUSD"
    return d["results"]


def load_all_t7() -> Dict[str, List[dict]]:
    return {
        "XAUUSD": load_xauusd_t7(),
        "NAS100": load_nas100_t7(),
        "EURUSD": load_eurusd_t7(),
    }


def extract_candidates(results: List[dict]) -> List[dict]:
    return [r for r in results if r.get("decision") == "CANDIDATE"]


def is_degenerate(r: dict) -> bool:
    """Record is degenerate if entry/SL/TP collapse — per epsilon revalidation doc."""
    e = r.get("entry_price")
    s = r.get("stop_loss")
    t = r.get("take_profit_1")
    if None in (e, s, t):
        return True
    try:
        e, s, t = float(e), float(s), float(t)
    except Exception:
        return True
    return e == s or e == t or s == t


# -----------------------------------------------------------------------------
# Backtest sessions — cumulative trades per instrument
# -----------------------------------------------------------------------------
def load_backtest_trades(symbol: str) -> List[dict]:
    sub_map = {"US30": "US30_cash"}
    sub = sub_map.get(symbol, symbol)
    base = ROOT / "knowledge_base_backtest" / "sessions" / sub
    if not base.exists():
        return []
    out: List[dict] = []
    for fn in sorted(base.glob("*.json")):
        with open(fn, "r", encoding="utf-8") as f:
            d = json.load(f)
        ts = d.get("trade_summary", {})
        if not (ts and ts.get("trade_taken")):
            continue
        for sub_trade in ts.get("trades", []):
            t = dict(sub_trade)
            t["date"] = d.get("date")
            t["symbol"] = symbol
            out.append(t)
    return out


def load_all_backtest() -> Dict[str, List[dict]]:
    return {s: load_backtest_trades(s) for s in ["XAUUSD", "US30", "USDJPY", "GBPJPY", "GBPUSD", "NZDUSD"]}


# -----------------------------------------------------------------------------
# Live trade index
# -----------------------------------------------------------------------------
def load_trade_index() -> List[dict]:
    with open(ROOT / "knowledge_base" / "index" / "_trade_index.json", "r", encoding="utf-8") as f:
        d = json.load(f)
    return d.get("trades", [])


# -----------------------------------------------------------------------------
# Quarter bucketing
# -----------------------------------------------------------------------------
def quarter_of(date_str: str) -> str:
    """ '2026-01-15' -> '2026Q1' """
    y, m = date_str[:4], int(date_str[5:7])
    q = (m - 1) // 3 + 1
    return f"{y}Q{q}"


def median(values: List[float]) -> Optional[float]:
    if not values:
        return None
    s = sorted(values)
    n = len(s)
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


def percentile(values: List[float], p: float) -> Optional[float]:
    if not values:
        return None
    s = sorted(values)
    k = (len(s) - 1) * p / 100.0
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    if lo == hi:
        return s[lo]
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


if __name__ == "__main__":
    # Sanity
    for s in ["XAUUSD", "EURUSD", "NAS100", "US30", "USDJPY", "GBPJPY", "GBPUSD"]:
        c = load_m15(s)
        print(f"{s}: M15 n={len(c)} range={c[0]['t']} .. {c[-1]['t']}")
    all_t7 = load_all_t7()
    for sym, rs in all_t7.items():
        cands = extract_candidates(rs)
        degen = sum(1 for c in cands if is_degenerate(c))
        print(f"{sym} T7 total={len(rs)} CAND={len(cands)} degen={degen}")
    bt = load_all_backtest()
    for sym, ts in bt.items():
        print(f"{sym} backtest n={len(ts)}")
    idx = load_trade_index()
    print(f"live trade_index n={len(idx)}")
