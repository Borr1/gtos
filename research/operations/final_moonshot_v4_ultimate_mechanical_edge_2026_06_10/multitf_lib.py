"""MULTITF — multi-timeframe entry-refinement primitives (track: mtf_refine).

H4 sets regime + setup (the audited commodity FVG-retest continuation with persistence
gate); H1/M15 TIMES the entry inside the H4 window AFTER the signal bar closes.

NO LOOKAHEAD: the H4 signal at bar i is only actionable from T_h4[i]+4h onward (signal bar
must close). Lower-TF entry triggers use only closed lower-TF bars at-or-after that instant.
Outcomes are scored on the SAME lower-TF stream via geometry_lib.simulate (leak-free).

Wall-clock horizon is matched to H4: H4 maxbars=80 (=320h). On H1 that is 320 bars; on
M15 that is 1280 bars. trail/scale geometry held identical in R-space.
"""
from __future__ import annotations
import sys, os, csv
from datetime import datetime, timedelta
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(HERE))
from geometry_lib import Bar, atr14, simulate
import wave1_structure_setups_ict as w1
import gold_sleeve_strategy as g
import compounding_sleeve as cs

DATA = str(ROOT) + "/data/mt5_research_exports"

# ---- lower-TF source map (deep history where available, forward-only otherwise) ----
# XAUUSD has deep H1 + M15 (2015-2026). Other metals: H1/M15 forward-only (2025-06+).
LTF_PATHS = {
    ("XAUUSD", "H1"):  [DATA + "/gold_multitf_d1h1_2015_2026/XAUUSD_H1.csv"],
    ("XAUUSD", "M15"): [DATA + "/gold_multitf_m15_2015_2026/XAUUSD_M15.csv"],
    ("XAGUSD", "H1"):  [DATA + "/bridge_ftmo_htf_20250601_20260610/XAGUSD_H1.csv"],
    ("XAUEUR", "H1"):  [DATA + "/bridge_ftmo_ext_htf_20250601_20260611/XAUEUR_H1.csv"],
    ("XAGEUR", "H1"):  [DATA + "/bridge_ftmo_ext_htf_20250601_20260611/XAGEUR_H1.csv"],
    ("XAUAUD", "H1"):  [DATA + "/bridge_ftmo_ext_htf_20250601_20260611/XAUAUD_H1.csv"],
    ("XAGAUD", "H1"):  [DATA + "/bridge_ftmo_ext_htf_20250601_20260611/XAGAUD_H1.csv"],
    ("XAUUSD_fwd", "H1"): [DATA + "/bridge_ftmo_htf_20250601_20260610/XAUUSD_H1.csv"],
    # ---- M15 (track mtf_refine EXP6/7): XAUUSD deep, rest forward-only 2025-06+ ----
    ("XAGUSD", "M15"): [DATA + "/bridge_ftmo_m15_20250601_20260610/XAGUSD_M15.csv"],
    ("XAUEUR", "M15"): [DATA + "/bridge_ftmo_ext_m15_20250601_20260611/XAUEUR_M15.csv"],
    ("XAGEUR", "M15"): [DATA + "/bridge_ftmo_ext_m15_20250601_20260611/XAGEUR_M15.csv"],
    ("XAUAUD", "M15"): [DATA + "/bridge_ftmo_ext_m15_20250601_20260611/XAUAUD_M15.csv"],
    ("XAGAUD", "M15"): [DATA + "/bridge_ftmo_ext_m15_20250601_20260611/XAGAUD_M15.csv"],
}
TF_HOURS = {"H1": 1, "M15": 0.25, "H4": 4}

def _load_csv(p):
    T = []; B = []
    if not os.path.exists(p): return T, B
    with open(p) as f:
        for row in csv.DictReader(f):
            try:
                t = datetime.strptime(row["time"], "%Y-%m-%d %H:%M:%S")
                b = Bar(float(row["open"]), float(row["high"]), float(row["low"]),
                        float(row["close"]), float(row.get("volume", 0) or 0))
                T.append(t); B.append(b)
            except Exception:
                continue
    return T, B

_LTF_CACHE = {}
def load_ltf(sym, tf):
    key = (sym, tf)
    if key in _LTF_CACHE: return _LTF_CACHE[key]
    paths = LTF_PATHS.get(key, [])
    merged = {}
    for p in paths:
        T, B = _load_csv(p)
        for t, b in zip(T, B): merged[t] = b
    items = sorted(merged.items(), key=lambda kv: kv[0])
    res = ([k for k, _ in items], [v for _, v in items])
    _LTF_CACHE[key] = res
    return res

def ltf_atr(B, i, n=14):
    return atr14(B, i)  # reuse 14-period ATR on the lower-TF stream

def first_ltf_index_after(Tl, ts):
    """First lower-TF bar index whose open time is >= ts (binary search)."""
    lo, hi = 0, len(Tl)
    while lo < hi:
        mid = (lo + hi) // 2
        if Tl[mid] < ts: lo = mid + 1
        else: hi = mid
    return lo if lo < len(Tl) else None
