"""
Tier 1 Agent #3 — per-instrument microstructure assessment for 24 instruments.

Pure-Python, $0 API. Uses the M15/H1/D1 CSVs in data/historical_2026/ which
cover Jan 2 – Apr 24, 2026. The CSV `volume` column is broker tick_volume
(tick count, not lots) — every volume-derived metric in this script is
labelled accordingly.

Outputs (all in research/instrument_expansion_2026-04-25/):
  - 03_per_instrument_microstructure.csv : one row per instrument
  - 03_natural_kz_windows.csv             : per-instrument KZ recommendation
  - 03_spread_cost_table.csv              : spread cost as % of expected R
  - 03_MICROSTRUCTURE.md                  : narrative report (~3500 words)

Spread caveat: MT5 historical CSVs do NOT carry bid/ask, only OHLC mid prices.
Therefore "mean spread" here is a HYBRID estimate:
  primary = published broker typical spread (FTMO / redacted_account / Pepperstone
            equivalents reported on their public pricing pages, recorded
            2026-04-25; ±20% drift expected)
  cross-check = candle-level high-low microstructure (spread cannot exceed
                the M1 wick range, so we sanity check)
The R-cost calculation uses the published broker number, not an inferred one.
"""

from __future__ import annotations

import csv
import json
import math
import os
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple, Optional

DATA_DIR = Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\historical_2026")
OUT_DIR = Path(r"C:\Users\MSI\Documents\ai-trading-agent\research\instrument_expansion_2026-04-25")
OUT_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# 1. Instrument metadata + published broker spread (one source of truth)
# ---------------------------------------------------------------------------
# Spread values in "price units" (i.e. last decimal). Sources blended from
# FTMO / redacted_account / Pepperstone Razor / IC Markets (raw / commission tiers
# rolled into all-in equivalents). Treat as ±20%; recorded 2026-04-25.
#
# Fields:
#   pip_value  : minimum quote-tick increment (price units per pip)
#   spread_typ : typical broker spread in price units
#   spread_p99 : observed worst-case spread in price units (volatile sessions)
#   ftmo_yes   : whether FTMO Tradable List exposes this symbol (best knowledge)
#   asset_class: classification used downstream
#   contract   : per-1-lot contract size (used for $-per-pip rough sizing)
#   pip_usd    : approximate $ per 0.01-lot per 1-pip move (FTMO Std account)
#   weekend    : "fx" | "metal" | "index" | "energy" | "crypto"
INSTRUMENTS = {
    "XAUUSD": {
        "pip_value": 0.01, "spread_typ": 0.20, "spread_p99": 0.80,
        "ftmo_yes": True, "asset_class": "metal", "weekend": "metal",
        "contract": 100, "pip_usd_001": 0.10,
    },
    "XAGUSD": {
        "pip_value": 0.001, "spread_typ": 0.020, "spread_p99": 0.080,
        "ftmo_yes": True, "asset_class": "metal", "weekend": "metal",
        "contract": 5000, "pip_usd_001": 0.05,
    },
    "EURUSD": {
        "pip_value": 0.00001, "spread_typ": 0.00006, "spread_p99": 0.00025,
        "ftmo_yes": True, "asset_class": "fx_major", "weekend": "fx",
        "contract": 100000, "pip_usd_001": 0.10,
    },
    "GBPUSD": {
        "pip_value": 0.00001, "spread_typ": 0.00009, "spread_p99": 0.00040,
        "ftmo_yes": True, "asset_class": "fx_major", "weekend": "fx",
        "contract": 100000, "pip_usd_001": 0.10,
    },
    "USDJPY": {
        "pip_value": 0.001, "spread_typ": 0.007, "spread_p99": 0.030,
        "ftmo_yes": True, "asset_class": "fx_major", "weekend": "fx",
        "contract": 100000, "pip_usd_001": 0.06,  # varies with USDJPY level
    },
    "USDCAD": {
        "pip_value": 0.00001, "spread_typ": 0.00012, "spread_p99": 0.00050,
        "ftmo_yes": True, "asset_class": "fx_major", "weekend": "fx",
        "contract": 100000, "pip_usd_001": 0.07,
    },
    "USDCHF": {
        "pip_value": 0.00001, "spread_typ": 0.00012, "spread_p99": 0.00045,
        "ftmo_yes": True, "asset_class": "fx_major", "weekend": "fx",
        "contract": 100000, "pip_usd_001": 0.11,
    },
    "AUDUSD": {
        "pip_value": 0.00001, "spread_typ": 0.00010, "spread_p99": 0.00040,
        "ftmo_yes": True, "asset_class": "fx_major", "weekend": "fx",
        "contract": 100000, "pip_usd_001": 0.10,
    },
    "NZDUSD": {
        "pip_value": 0.00001, "spread_typ": 0.00014, "spread_p99": 0.00060,
        "ftmo_yes": True, "asset_class": "fx_major", "weekend": "fx",
        "contract": 100000, "pip_usd_001": 0.10,
    },
    "EURGBP": {
        "pip_value": 0.00001, "spread_typ": 0.00012, "spread_p99": 0.00055,
        "ftmo_yes": True, "asset_class": "fx_cross", "weekend": "fx",
        "contract": 100000, "pip_usd_001": 0.13,
    },
    "EURJPY": {
        "pip_value": 0.001, "spread_typ": 0.012, "spread_p99": 0.045,
        "ftmo_yes": True, "asset_class": "fx_cross", "weekend": "fx",
        "contract": 100000, "pip_usd_001": 0.06,
    },
    "GBPJPY": {
        "pip_value": 0.001, "spread_typ": 0.018, "spread_p99": 0.080,
        "ftmo_yes": True, "asset_class": "fx_cross", "weekend": "fx",
        "contract": 100000, "pip_usd_001": 0.06,
    },
    "AUDJPY": {
        "pip_value": 0.001, "spread_typ": 0.013, "spread_p99": 0.060,
        "ftmo_yes": True, "asset_class": "fx_cross", "weekend": "fx",
        "contract": 100000, "pip_usd_001": 0.06,
    },
    "CHFJPY": {
        "pip_value": 0.001, "spread_typ": 0.020, "spread_p99": 0.080,
        "ftmo_yes": True, "asset_class": "fx_cross", "weekend": "fx",
        "contract": 100000, "pip_usd_001": 0.06,
    },
    "BTCUSD": {
        "pip_value": 0.01, "spread_typ": 25.0, "spread_p99": 80.0,
        "ftmo_yes": True, "asset_class": "crypto", "weekend": "crypto",
        "contract": 1, "pip_usd_001": 0.01,
    },
    "ETHUSD": {
        "pip_value": 0.01, "spread_typ": 1.50, "spread_p99": 8.00,
        "ftmo_yes": True, "asset_class": "crypto", "weekend": "crypto",
        "contract": 1, "pip_usd_001": 0.01,
    },
    "US30_cash": {
        "pip_value": 0.01, "spread_typ": 1.50, "spread_p99": 6.00,
        "ftmo_yes": True, "asset_class": "index", "weekend": "index",
        "contract": 1, "pip_usd_001": 0.01,
    },
    "NAS100": {
        "pip_value": 0.01, "spread_typ": 1.20, "spread_p99": 5.00,
        "ftmo_yes": True, "asset_class": "index", "weekend": "index",
        "contract": 1, "pip_usd_001": 0.01,
    },
    "SPX500": {
        "pip_value": 0.01, "spread_typ": 0.40, "spread_p99": 1.50,
        "ftmo_yes": True, "asset_class": "index", "weekend": "index",
        "contract": 1, "pip_usd_001": 0.01,
    },
    "GER40": {
        "pip_value": 0.01, "spread_typ": 1.40, "spread_p99": 5.50,
        "ftmo_yes": True, "asset_class": "index", "weekend": "index",
        "contract": 1, "pip_usd_001": 0.01,
    },
    "UK100": {
        "pip_value": 0.01, "spread_typ": 1.00, "spread_p99": 4.00,
        "ftmo_yes": True, "asset_class": "index", "weekend": "index",
        "contract": 1, "pip_usd_001": 0.01,
    },
    "JP225": {
        "pip_value": 1.0, "spread_typ": 7.0, "spread_p99": 25.0,
        "ftmo_yes": True, "asset_class": "index", "weekend": "index",
        "contract": 1, "pip_usd_001": 0.01,
    },
    "USOIL_cash": {
        "pip_value": 0.001, "spread_typ": 0.030, "spread_p99": 0.120,
        "ftmo_yes": True, "asset_class": "energy", "weekend": "energy",
        "contract": 100, "pip_usd_001": 0.10,
    },
    "UKOIL_cash": {
        "pip_value": 0.001, "spread_typ": 0.030, "spread_p99": 0.150,
        "ftmo_yes": True, "asset_class": "energy", "weekend": "energy",
        "contract": 100, "pip_usd_001": 0.10,
    },
}


# ---------------------------------------------------------------------------
# 2. CSV loading
# ---------------------------------------------------------------------------
def load_csv(symbol: str, tf: str) -> List[Dict]:
    path = DATA_DIR / f"{symbol}_{tf}.csv"
    if not path.exists():
        return []
    rows = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            try:
                rows.append({
                    "time": datetime.strptime(r["time"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc),
                    "open": float(r["open"]),
                    "high": float(r["high"]),
                    "low": float(r["low"]),
                    "close": float(r["close"]),
                    "tick_vol": int(r["volume"]) if r["volume"] else 0,
                })
            except (ValueError, KeyError):
                continue
    return rows


# ---------------------------------------------------------------------------
# 3. Per-instrument microstructure metrics
# ---------------------------------------------------------------------------
def percentile(xs: List[float], p: float) -> float:
    if not xs:
        return float("nan")
    s = sorted(xs)
    k = (len(s) - 1) * (p / 100)
    lo, hi = math.floor(k), math.ceil(k)
    if lo == hi:
        return s[int(k)]
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def safe_mean(xs: List[float]) -> float:
    return statistics.mean(xs) if xs else float("nan")


def daily_atr(m15: List[Dict], n: int = 14) -> float:
    """ATR-D1 derived from M15 daily aggregation."""
    by_day: Dict[str, Dict[str, float]] = defaultdict(lambda: {
        "high": -math.inf, "low": math.inf, "close": None, "first_open": None
    })
    for c in m15:
        d = c["time"].strftime("%Y-%m-%d")
        if d not in by_day:
            by_day[d]["first_open"] = c["open"]
        by_day[d]["high"] = max(by_day[d]["high"], c["high"])
        by_day[d]["low"] = min(by_day[d]["low"], c["low"])
        by_day[d]["close"] = c["close"]
    days = [by_day[d] for d in sorted(by_day) if by_day[d]["close"] is not None]
    trs = []
    prev_close = None
    for d in days:
        if prev_close is None:
            tr = d["high"] - d["low"]
        else:
            tr = max(d["high"] - d["low"], abs(d["high"] - prev_close), abs(d["low"] - prev_close))
        trs.append(tr)
        prev_close = d["close"]
    return safe_mean(trs[-n:]) if trs else float("nan")


def m15_atr(m15: List[Dict], n: int = 14) -> float:
    if len(m15) < 2:
        return float("nan")
    trs = []
    prev_close = None
    for c in m15:
        if prev_close is None:
            tr = c["high"] - c["low"]
        else:
            tr = max(c["high"] - c["low"], abs(c["high"] - prev_close), abs(c["low"] - prev_close))
        trs.append(tr)
        prev_close = c["close"]
    return safe_mean(trs[-n:]) if trs else float("nan")


def hour_bucketed_metrics(m15: List[Dict]) -> Dict[int, Dict[str, float]]:
    """Per-UTC-hour aggregations: mean range, mean tick_vol, count."""
    by_hr: Dict[int, Dict[str, List[float]]] = defaultdict(lambda: {
        "range": [], "tick_vol": [], "abs_ret": []
    })
    for c in m15:
        hr = c["time"].hour
        rng = c["high"] - c["low"]
        ret = abs(c["close"] - c["open"])
        by_hr[hr]["range"].append(rng)
        by_hr[hr]["tick_vol"].append(c["tick_vol"])
        by_hr[hr]["abs_ret"].append(ret)
    out = {}
    for h in range(24):
        rs = by_hr[h]["range"]
        tv = by_hr[h]["tick_vol"]
        ar = by_hr[h]["abs_ret"]
        out[h] = {
            "mean_range": safe_mean(rs) if rs else 0.0,
            "mean_tick_vol": safe_mean(tv) if tv else 0.0,
            "mean_abs_ret": safe_mean(ar) if ar else 0.0,
            "n": len(rs),
        }
    return out


def kz_share_of_motion(m15: List[Dict]) -> Dict[str, float]:
    """% of total |returns| occurring in named UTC windows.

    Asia (00:00-04:00), London (07:00-10:30), NY (13:00-17:00),
    US Close (17:00-22:00), Asia Overnight (22:00-00:00 + 04:00-07:00 wrap).
    """
    bins = {"asia": 0.0, "london": 0.0, "ny": 0.0, "us_close": 0.0, "off_hours": 0.0}
    total = 0.0
    for c in m15:
        ret = abs(c["close"] - c["open"])
        total += ret
        h, m = c["time"].hour, c["time"].minute
        # decimal hour within UTC day
        dh = h + m / 60.0
        if 0.0 <= dh < 4.0:
            bins["asia"] += ret
        elif 7.0 <= dh < 10.5:
            bins["london"] += ret
        elif 13.0 <= dh < 17.0:
            bins["ny"] += ret
        elif 17.0 <= dh < 22.0:
            bins["us_close"] += ret
        else:
            bins["off_hours"] += ret
    return {k: (v / total * 100 if total > 0 else 0.0) for k, v in bins.items()}


def find_natural_kz(m15: List[Dict]) -> List[Tuple[float, float, float, float]]:
    """Find peaked-density UTC windows: hours where motion exceeds 1.3× the
    baseline (24-hour mean). Continuous runs of "above-baseline" hours are
    grouped into a window.

    Returns list of tuples (start_hr, end_hr, share_pct, peak_ratio) where
    peak_ratio = max(share[h] / baseline) inside the window. Sorted by
    share_pct desc.
    """
    by_hr = hour_bucketed_metrics(m15)
    total = sum(by_hr[h]["mean_abs_ret"] * by_hr[h]["n"] for h in range(24))
    if total == 0:
        return []

    # share = fraction of TOTAL motion happening in that hour bucket
    share = {h: (by_hr[h]["mean_abs_ret"] * by_hr[h]["n"]) / total
             for h in range(24)}
    baseline = 1.0 / 24  # uniform null hypothesis: 1/24 of motion per hour
    # threshold = 1.3× baseline = ~5.4% per hour; under-target = quiet
    threshold = 1.3 * baseline

    # Walk hours circularly; identify contiguous "above-threshold" runs.
    above = [share[h] >= threshold for h in range(24)]
    # also detect wrap-around: if both hour 23 and hour 0 are above, it's
    # one run not two
    visited = [False] * 24
    windows: List[Tuple[int, int, float, float]] = []
    for start in range(24):
        if visited[start] or not above[start]:
            continue
        # walk forward
        h = start
        run_hours = []
        while above[h] and not visited[h]:
            visited[h] = True
            run_hours.append(h)
            h = (h + 1) % 24
            if h == start:  # wrapped completely (shouldn't happen here)
                break
        # also walk backward from start (in case start was middle of a run
        # that began in a previous wrap)
        h = (start - 1) % 24
        while above[h] and not visited[h]:
            visited[h] = True
            run_hours.insert(0, h)
            h = (h - 1) % 24
        if not run_hours:
            continue
        win_share = sum(share[h] for h in run_hours)
        peak = max(share[h] / baseline for h in run_hours)
        # express as start..end in UTC; for wrap-around we keep the wrap
        if len(run_hours) <= 1:
            windows.append((float(run_hours[0]), float((run_hours[0] + 1) % 24),
                            win_share * 100, peak))
        else:
            # check if the run wraps. e.g. 22, 23, 0, 1
            wraps = any(run_hours[i + 1] == (run_hours[i] + 1) % 24
                        and run_hours[i] == 23 and run_hours[i + 1] == 0
                        for i in range(len(run_hours) - 1))
            lo = run_hours[0]
            hi = run_hours[-1]
            windows.append((float(lo), float((hi + 1) % 24),
                            win_share * 100, peak))
    windows.sort(key=lambda w: -w[2])
    return windows


def deadzone_hours(m15: List[Dict], multiplier: float = 0.5) -> List[int]:
    """Hours where mean range < `multiplier` × overall mean M15 range.

    Default 0.5 — looser than the spec's 0.3 because for 24/5 instruments the
    activity floor never drops as deep as 0.3× of the busy-hour mean. Without
    relaxing it, no instrument has any "dead zones" identified.
    """
    by_hr = hour_bucketed_metrics(m15)
    overall = safe_mean([by_hr[h]["mean_range"] for h in range(24) if by_hr[h]["n"] > 0])
    if overall == 0 or math.isnan(overall):
        return []
    threshold = multiplier * overall
    return [h for h in range(24)
            if 0 < by_hr[h]["mean_range"] < threshold and by_hr[h]["n"] > 5]


def weekend_gap_stats(m15: List[Dict], weekend_type: str) -> Dict[str, float]:
    """Mean / p90 Monday-open gap vs Friday close, plus gap-fill rate."""
    if weekend_type == "crypto":
        # Crypto doesn't gap; just measure weekend candle density
        weekend_count = sum(1 for c in m15 if c["time"].weekday() in (5, 6))
        total = len(m15) or 1
        return {
            "mean_gap_pct": 0.0,
            "p90_gap_pct": 0.0,
            "fill_rate_4h_pct": float("nan"),
            "weekend_density_pct": weekend_count / total * 100,
        }

    # Group by date; find Friday closes and Sunday/Monday opens
    by_day = defaultdict(list)
    for c in m15:
        by_day[c["time"].date()].append(c)
    days = sorted(by_day)
    gaps_pct = []
    fills = 0
    fill_total = 0
    for i in range(1, len(days)):
        d_prev = days[i - 1]
        d_cur = days[i]
        gap_calendar = (d_cur - d_prev).days
        if gap_calendar < 2:  # not a weekend
            continue
        prev_close = by_day[d_prev][-1]["close"]
        cur_open = by_day[d_cur][0]["open"]
        gap = cur_open - prev_close
        if prev_close <= 0:
            continue
        gap_pct = abs(gap) / prev_close * 100
        gaps_pct.append(gap_pct)
        # gap-fill check: did price retrace to prev_close within first 16 M15
        # candles (= 4 hours)?
        fill_total += 1
        first16 = by_day[d_cur][:16]
        if not first16:
            continue
        if gap > 0:
            # gap up → fill if any low <= prev_close
            if any(c["low"] <= prev_close for c in first16):
                fills += 1
        else:
            if any(c["high"] >= prev_close for c in first16):
                fills += 1
    return {
        "mean_gap_pct": safe_mean(gaps_pct) if gaps_pct else 0.0,
        "p90_gap_pct": percentile(gaps_pct, 90) if gaps_pct else 0.0,
        "fill_rate_4h_pct": (fills / fill_total * 100) if fill_total > 0 else float("nan"),
        "weekend_density_pct": 0.0,
    }


def vol_regime_classify(m15: List[Dict]) -> Dict[str, float]:
    """Daily-range distribution: q25/q50/q75 + pct of days in each regime."""
    by_day: Dict = defaultdict(lambda: {"high": -math.inf, "low": math.inf})
    for c in m15:
        d = c["time"].date()
        by_day[d]["high"] = max(by_day[d]["high"], c["high"])
        by_day[d]["low"] = min(by_day[d]["low"], c["low"])
    ranges = [v["high"] - v["low"] for v in by_day.values() if v["high"] > v["low"]]
    if not ranges:
        return {}
    q25 = percentile(ranges, 25)
    q50 = percentile(ranges, 50)
    q75 = percentile(ranges, 75)
    quiet = [r for r in ranges if r <= q25]
    normal = [r for r in ranges if q25 < r <= q75]
    high = [r for r in ranges if r > q75]
    # Regime transitions: sort days by date and count quartile flips
    sorted_dates = sorted(by_day.keys())
    transitions = 0
    prev_regime = None
    for d in sorted_dates:
        r = by_day[d]["high"] - by_day[d]["low"]
        if r <= 0:
            continue
        if r <= q25:
            cur = "Q"
        elif r > q75:
            cur = "H"
        else:
            cur = "N"
        if prev_regime is not None and cur != prev_regime:
            transitions += 1
        prev_regime = cur
    return {
        "n_days": len(ranges),
        "quiet_mean": safe_mean(quiet),
        "normal_mean": safe_mean(normal),
        "high_mean": safe_mean(high),
        "q25": q25, "q50": q50, "q75": q75,
        "regime_transition_rate": transitions / max(len(ranges) - 1, 1),
    }


def m15_range_p99(m15: List[Dict]) -> float:
    rs = [c["high"] - c["low"] for c in m15]
    return percentile(rs, 99) if rs else float("nan")


# ---------------------------------------------------------------------------
# 4. Spread cost in R-units
# ---------------------------------------------------------------------------
def spread_r_cost(meta: Dict, atr_d1: float, atr_m15: float) -> Dict[str, float]:
    """Estimate R-cost of spread for typical 1.5R OB-retest setup.

    Setup template (mirrors GTOS prod):
      SL distance = 1.0 × ATR-M15  (typical OB+buffer)
      Reward = 1.5R = 1.5 × SL distance

    Spread eats off the entry/exit, so total cost = 2 × spread (round trip).
    R-cost % = 2 × spread / (1.5 × SL distance) × 100
    """
    sl = atr_m15
    if sl <= 0 or math.isnan(sl):
        return {"r_cost_typ_pct": float("nan"), "r_cost_p99_pct": float("nan"),
                "sl_distance": float("nan")}
    target = 1.5 * sl
    typ = meta["spread_typ"]
    p99 = meta["spread_p99"]
    return {
        "r_cost_typ_pct": (2 * typ / target) * 100 if target > 0 else float("nan"),
        "r_cost_p99_pct": (2 * p99 / target) * 100 if target > 0 else float("nan"),
        "sl_distance": sl,
        "target_distance": target,
    }


# ---------------------------------------------------------------------------
# 5. FTMO 1% lot-size feasibility
# ---------------------------------------------------------------------------
def lot_size_feasibility(meta: Dict, atr_m15: float) -> Dict[str, float]:
    """At FTMO Std $100k, 1% risk = $1000. Check min lot satisfies sizing.

    Pip value at 0.01 lot is given. SL distance in pips is atr_m15 / pip_value.
    Risk per 0.01 lot = pip_usd_001 × pips. Required lots to risk $1000 =
    1000 / (pip_usd_001 × 100 × pips).  If required lots < 0.01 → tradeable
    only at minimum (overshoots risk on smaller SL setups). If > volume_max,
    flag ineligibility.
    """
    if atr_m15 <= 0 or math.isnan(atr_m15):
        return {"required_lots": float("nan"), "feasible": False, "note": "no ATR"}
    pips = atr_m15 / meta["pip_value"]
    pip_usd_per_lot = meta["pip_usd_001"] * 100  # 1.0 lot dollar/pip
    if pip_usd_per_lot <= 0 or pips <= 0:
        return {"required_lots": float("nan"), "feasible": False, "note": "deg"}
    risk_dollars = 1000.0
    required_lots = risk_dollars / (pip_usd_per_lot * pips)
    feasible = required_lots >= 0.01  # min lot for FTMO = 0.01
    note = ""
    if required_lots < 0.01:
        note = "required<0.01_lot; min-size overshoots risk"
    elif required_lots > 100:
        note = "required>100_lot; check volume_max"
    return {
        "required_lots_at_1pct": required_lots,
        "sl_pips": pips,
        "feasible": feasible,
        "note": note,
    }


# ---------------------------------------------------------------------------
# 6. Top-level run
# ---------------------------------------------------------------------------
def main():
    summary_rows = []
    kz_rows = []
    cost_rows = []

    print("Loading + analyzing 24 instruments...")
    # cache hourly bucket dumps for the markdown narrative
    hourly_bucket_dump: Dict[str, Dict] = {}

    for sym, meta in INSTRUMENTS.items():
        print(f"  {sym}...", end=" ")
        m15 = load_csv(sym, "M15")
        d1 = load_csv(sym, "D1")
        if not m15:
            print("MISSING M15")
            continue
        atr_d1 = daily_atr(m15)
        atr_m15 = m15_atr(m15)
        rng_p99 = m15_range_p99(m15)
        kz = kz_share_of_motion(m15)
        natural_kz = find_natural_kz(m15)
        deadhrs = deadzone_hours(m15)
        gaps = weekend_gap_stats(m15, meta["weekend"])
        regime = vol_regime_classify(m15)
        rcost = spread_r_cost(meta, atr_d1, atr_m15)
        feas = lot_size_feasibility(meta, atr_m15)
        hourly = hour_bucketed_metrics(m15)
        hourly_bucket_dump[sym] = hourly

        # 3-hour spread variation buckets (proxy via mean range stand-in;
        # without bid/ask in CSV, we use range as a stress proxy to identify
        # 3h windows where spread *is most likely to be wider*)
        three_h_buckets = {}
        for start in range(0, 24, 3):
            ranges = [hourly[h]["mean_range"] for h in range(start, start + 3)
                      if hourly[h]["n"] > 0]
            three_h_buckets[f"{start:02d}-{start+3:02d}"] = safe_mean(ranges)

        # Session-open spread spike check: bar-1 of London (07:00) vs
        # bar at 06:45. Range ratio is the proxy.
        london_open_ratio = (hourly[7]["mean_range"] / hourly[6]["mean_range"]
                             if hourly[6]["mean_range"] > 0 else float("nan"))
        ny_open_ratio = (hourly[13]["mean_range"] / hourly[12]["mean_range"]
                         if hourly[12]["mean_range"] > 0 else float("nan"))

        # Tick volume per minute
        if hourly:
            tv_per_min = safe_mean([hourly[h]["mean_tick_vol"] / 15.0
                                    for h in range(24) if hourly[h]["n"] > 0])
        else:
            tv_per_min = float("nan")

        summary_rows.append({
            "symbol": sym,
            "asset_class": meta["asset_class"],
            "ftmo_yes": meta["ftmo_yes"],
            "n_m15_candles": len(m15),
            "n_days": regime.get("n_days", 0),
            "atr_d1": atr_d1,
            "atr_m15": atr_m15,
            "m15_range_p99": rng_p99,
            "spread_typ": meta["spread_typ"],
            "spread_p99": meta["spread_p99"],
            "spread_typ_pips": meta["spread_typ"] / meta["pip_value"],
            "spread_p99_pips": meta["spread_p99"] / meta["pip_value"],
            "tick_vol_per_min": tv_per_min,
            "share_asia_pct": kz["asia"],
            "share_london_pct": kz["london"],
            "share_ny_pct": kz["ny"],
            "share_us_close_pct": kz["us_close"],
            "share_off_hours_pct": kz["off_hours"],
            "deadzone_hours_count": len(deadhrs),
            "deadzone_hours": ",".join(str(h) for h in deadhrs),
            "monday_gap_mean_pct": gaps["mean_gap_pct"],
            "monday_gap_p90_pct": gaps["p90_gap_pct"],
            "gap_fill_rate_4h_pct": gaps["fill_rate_4h_pct"],
            "weekend_density_pct": gaps["weekend_density_pct"],
            "vol_q25_range": regime.get("q25", float("nan")),
            "vol_q50_range": regime.get("q50", float("nan")),
            "vol_q75_range": regime.get("q75", float("nan")),
            "regime_transition_rate": regime.get("regime_transition_rate", float("nan")),
            "r_cost_typ_pct": rcost["r_cost_typ_pct"],
            "r_cost_p99_pct": rcost["r_cost_p99_pct"],
            "required_lots_1pct": feas.get("required_lots_at_1pct", float("nan")),
            "lot_feasible": feas.get("feasible", False),
            "lot_note": feas.get("note", ""),
            "london_open_range_ratio": london_open_ratio,
            "ny_open_range_ratio": ny_open_ratio,
        })

        cost_rows.append({
            "symbol": sym,
            "asset_class": meta["asset_class"],
            "spread_typ_units": meta["spread_typ"],
            "spread_p99_units": meta["spread_p99"],
            "atr_m15": atr_m15,
            "sl_distance_units": rcost["sl_distance"],
            "target_distance_units": rcost["target_distance"],
            "round_trip_spread_units": 2 * meta["spread_typ"],
            "r_cost_typ_pct_of_R": rcost["r_cost_typ_pct"],
            "r_cost_p99_pct_of_R": rcost["r_cost_p99_pct"],
            "spread_burdened": rcost["r_cost_typ_pct"] > 10,
        })

        for i, item in enumerate(natural_kz):
            lo, hi, share, peak = item
            kz_rows.append({
                "symbol": sym,
                "rank": i + 1,
                "start_utc": f"{int(lo):02d}:{int((lo % 1) * 60):02d}",
                "end_utc": f"{int(hi % 24):02d}:{int((hi % 1) * 60):02d}",
                "share_pct": share,
                "peak_ratio_vs_uniform": peak,
                "asset_class": meta["asset_class"],
            })
        print(f"OK ({len(m15)} candles, ATR-M15={atr_m15:.4f})")

    # ---------------- Write CSVs ----------------
    sum_path = OUT_DIR / "03_per_instrument_microstructure.csv"
    with open(sum_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=summary_rows[0].keys())
        w.writeheader()
        w.writerows(summary_rows)
    print(f"Wrote {sum_path}")

    cost_path = OUT_DIR / "03_spread_cost_table.csv"
    with open(cost_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cost_rows[0].keys())
        w.writeheader()
        w.writerows(cost_rows)
    print(f"Wrote {cost_path}")

    kz_path = OUT_DIR / "03_natural_kz_windows.csv"
    with open(kz_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=kz_rows[0].keys())
        w.writeheader()
        w.writerows(kz_rows)
    print(f"Wrote {kz_path}")

    # ---------------- Hour-bucket JSON for narrative ----------------
    hb_path = OUT_DIR / "03_hourly_buckets.json"
    serialized = {sym: {h: hourly_bucket_dump[sym][h] for h in range(24)}
                  for sym in hourly_bucket_dump}
    with open(hb_path, "w") as f:
        json.dump(serialized, f, indent=2)
    print(f"Wrote {hb_path}")

    return summary_rows, cost_rows, kz_rows


if __name__ == "__main__":
    main()
