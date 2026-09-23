"""Shared data loaders and feature builders for agent η alternative pattern discovery.

All feature computation is done at candle close time (no look-ahead).
Forward replay uses ONLY candles that close AFTER the signal candle.
"""
from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent")

XAUUSD_PATH = ROOT / "research/t7_live_simulation/all_results_jan_apr10.json"
EURUSD_PATH = ROOT / "research/t7_live_simulation/EURUSD_t7_simulation.json"
NAS100_SLICE_PATHS = [
    ROOT / f"research/t3_1_eurusd_nas100_validation_2026-04-19/nas100_slice_{i}/NAS100_t7_simulation.json"
    for i in range(1, 6)
]

# Per-instrument fill geometry (honest epsilon, per Tier A1).
_EPSILON_BY_SYMBOL = {
    "XAUUSD": 0.20,
    "US30": 2.0,
    "NAS100": 2.0,
    "USDJPY": 0.02,
    "GBPJPY": 0.02,
    "EURUSD": 0.0002,
    "GBPUSD": 0.0002,
}

# Kill zones in UTC (from CLAUDE.md).
# list of (start_hour_utc, start_min, end_hour_utc, end_min, label)
KZ_BY_SYMBOL = {
    "XAUUSD": [(7, 0, 10, 30, "london"), (13, 0, 17, 0, "ny")],
    "US30":   [(8, 0, 10, 30, "london"), (13, 30, 16, 0, "ny")],
    "USDJPY": [(0, 0, 3, 0, "tokyo"), (7, 0, 9, 30, "london"), (13, 0, 15, 30, "ny")],
    "GBPJPY": [(0, 0, 3, 0, "tokyo"), (7, 0, 9, 30, "london"), (13, 0, 15, 30, "ny")],
    "GBPUSD": [(7, 0, 12, 0, "london"), (13, 0, 15, 30, "ny")],
    "EURUSD": [(7, 0, 12, 0, "london"), (13, 0, 15, 30, "ny")],
    "NAS100": [(13, 30, 16, 0, "ny")],   # NAS100 has an NY session (approx.)
}

_FENCE_RE = re.compile(r"^```(?:json)?\s*\n?|\n?```\s*$", re.MULTILINE)


def parse_raw_response(s):
    """Parse raw_response which may be fenced markdown json."""
    if s is None:
        return None
    if isinstance(s, dict):
        return s
    if not isinstance(s, str):
        return None
    cleaned = _FENCE_RE.sub("", s.strip()).strip()
    if not cleaned:
        return None
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        i = cleaned.find("{")
        j = cleaned.rfind("}")
        if i == -1 or j == -1:
            return None
        try:
            return json.loads(cleaned[i : j + 1])
        except json.JSONDecodeError:
            return None


def load_t7_json(path):
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    if isinstance(d, dict) and "results" in d:
        return d["results"]
    return d


def load_xauusd():
    return load_t7_json(XAUUSD_PATH)


def load_eurusd():
    return load_t7_json(EURUSD_PATH)


def load_nas100():
    all_records = []
    for p in NAS100_SLICE_PATHS:
        if not p.exists():
            continue
        d = load_t7_json(p)
        all_records.extend(d)
    seen = set()
    out = []
    for r in all_records:
        key = (r.get("candle_time"), r.get("kill_zone"))
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def parse_time(s):
    """Parse ISO time string to timezone-aware UTC datetime."""
    if s is None:
        return None
    s = s.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
    except Exception:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _parse_csv_time(s):
    """Parse '2026-01-02 01:15:00' → UTC-aware datetime (MT5 broker time assumed UTC here per CSV export)."""
    try:
        dt = datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        try:
            dt = datetime.strptime(s, "%Y-%m-%d")
        except ValueError:
            return None
    return dt.replace(tzinfo=timezone.utc)


def load_m15(symbol):
    """Load M15 CSV as list[{time, open, high, low, close, volume}], time-sorted."""
    path = ROOT / f"data/historical_2026/{symbol}_M15.csv"
    if not path.exists():
        # Handle US30_cash variant
        if symbol == "US30":
            path = ROOT / "data/historical_2026/US30_cash_M15.csv"
        if not path.exists():
            return []
    rows = []
    with open(path, "r", encoding="utf-8", newline="") as f:
        rdr = csv.DictReader(f)
        for r in rdr:
            t = _parse_csv_time(r["time"])
            if t is None:
                continue
            rows.append({
                "time": t,
                "open": float(r["open"]),
                "high": float(r["high"]),
                "low": float(r["low"]),
                "close": float(r["close"]),
                "volume": float(r["volume"]),
            })
    rows.sort(key=lambda x: x["time"])
    return rows


def load_h1(symbol):
    path = ROOT / f"data/historical_2026/{symbol}_H1.csv"
    if symbol == "US30" and not path.exists():
        path = ROOT / "data/historical_2026/US30_cash_H1.csv"
    rows = []
    with open(path, "r", encoding="utf-8", newline="") as f:
        rdr = csv.DictReader(f)
        for r in rdr:
            t = _parse_csv_time(r["time"])
            if t is None:
                continue
            rows.append({
                "time": t,
                "open": float(r["open"]),
                "high": float(r["high"]),
                "low": float(r["low"]),
                "close": float(r["close"]),
                "volume": float(r["volume"]),
            })
    rows.sort(key=lambda x: x["time"])
    return rows


def load_h4(symbol):
    path = ROOT / f"data/historical_2026/{symbol}_H4.csv"
    if symbol == "US30" and not path.exists():
        path = ROOT / "data/historical_2026/US30_cash_H4.csv"
    rows = []
    with open(path, "r", encoding="utf-8", newline="") as f:
        rdr = csv.DictReader(f)
        for r in rdr:
            t = _parse_csv_time(r["time"])
            if t is None:
                continue
            rows.append({
                "time": t,
                "open": float(r["open"]),
                "high": float(r["high"]),
                "low": float(r["low"]),
                "close": float(r["close"]),
                "volume": float(r["volume"]),
            })
    rows.sort(key=lambda x: x["time"])
    return rows


def load_d1(symbol):
    path = ROOT / f"data/historical_2026/{symbol}_D1.csv"
    if symbol == "US30" and not path.exists():
        path = ROOT / "data/historical_2026/US30_cash_D1.csv"
    rows = []
    with open(path, "r", encoding="utf-8", newline="") as f:
        rdr = csv.DictReader(f)
        for r in rdr:
            t = _parse_csv_time(r["time"])
            if t is None:
                continue
            rows.append({
                "time": t,
                "open": float(r["open"]),
                "high": float(r["high"]),
                "low": float(r["low"]),
                "close": float(r["close"]),
                "volume": float(r["volume"]),
            })
    rows.sort(key=lambda x: x["time"])
    return rows


def in_any_kz(dt, symbol):
    """Return KZ label or 'out' for a UTC-aware datetime against a symbol."""
    if dt is None:
        return "out"
    kz_list = KZ_BY_SYMBOL.get(symbol, [])
    h, m = dt.hour, dt.minute
    cur = h * 60 + m
    for sh, sm, eh, em, label in kz_list:
        if sh * 60 + sm <= cur < eh * 60 + em:
            return label
    return "out"


def atr_14(candles, end_idx):
    """Compute ATR-14 on a candle list; end_idx is the last candle to include (inclusive).
    Returns None if not enough data."""
    if end_idx < 14:
        return None
    trs = []
    for i in range(end_idx - 13, end_idx + 1):
        h = candles[i]["high"]
        l = candles[i]["low"]
        pc = candles[i - 1]["close"] if i > 0 else candles[i]["close"]
        tr = max(h - l, abs(h - pc), abs(l - pc))
        trs.append(tr)
    return sum(trs) / len(trs) if trs else None


def find_candle_idx(candles, target_time):
    """Binary search. Returns the idx of the candle whose time equals target, else None."""
    lo, hi = 0, len(candles) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if candles[mid]["time"] == target_time:
            return mid
        if candles[mid]["time"] < target_time:
            lo = mid + 1
        else:
            hi = mid - 1
    return None


def find_candle_idx_at_or_before(candles, target_time):
    """Returns idx of last candle with time <= target_time, else None."""
    lo, hi = 0, len(candles) - 1
    out = None
    while lo <= hi:
        mid = (lo + hi) // 2
        if candles[mid]["time"] <= target_time:
            out = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return out
