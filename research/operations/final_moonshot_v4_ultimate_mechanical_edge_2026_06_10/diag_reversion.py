"""Diagnostic: how restrictive is each filter, and what is the raw edge of
reversion entries under different regime gates, BEFORE conjoining everything.
Goal: find a regime definition that admits a usable sample (hundreds of trades)
AND still carries a reversion edge."""
from __future__ import annotations
import sys, os, csv, json, math
from collections import defaultdict

REPO = "/Users/borr/Documents/gtos/repo/ai-trading-agent"
EDGE = REPO + "/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
DATA = REPO + "/data/mt5_research_exports/bridge_ftmo_deep_h4_2022_2026"
sys.path.insert(0, REPO); sys.path.insert(0, EDGE)
from geometry_lib import Bar, atr14, simulate
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL
from hunt_reversion_regime_filtered import (
    load, year_of, ema_series, rsi_series, atr_series, adx_series,
    std_window, efficiency_ratio, summarize, cost_for)

SYMS = [s for s in ASSET_CLASS_BY_SYMBOL if os.path.exists(f"{DATA}/{s}_H4.csv")]

# Precompute everything once per symbol; collect entries with a rich feature row.
def feats(sym):
    bars, times = load(sym)
    if bars is None or len(bars) < 260:
        return [], None, None
    a14 = atr_series(bars, 14); a50 = atr_series(bars, 50)
    ema20 = ema_series(bars, 20); rsi = rsi_series(bars, 14); adx = adx_series(bars, 14)
    rows = []
    for i in range(60, len(bars) - 1):
        a = a14[i]
        if a <= 0 or a50[i] <= 0 or adx[i] is None: continue
        sw = std_window(bars, i, 20)
        if sw is None: continue
        sd, mean = sw
        if sd <= 0: continue
        r = rsi[i]
        if r is None: continue
        er = efficiency_ratio(bars, i, 10)
        rng = bars[i].h - bars[i].l
        if rng <= 0: continue
        rows.append(dict(
            i=i, yr=year_of(times[i]), a=a,
            adx=adx[i], vc=a / a50[i], er=er,
            dist=(bars[i].c - ema20[i]) / a, z=(bars[i].c - mean) / sd, rsi=r,
            rej_lo=(bars[i].c - bars[i].l) / rng, rej_hi=(bars[i].h - bars[i].c) / rng,
        ))
    return rows, bars, times

CACHE = {}
for s in SYMS:
    CACHE[s] = feats(s)

def edge(gate, direction_pick, stop_mult=0.5, target_mult=1.0):
    """gate(row)->bool admits the bar; direction_pick(row)-> +1/-1/0.
    Returns (train_summary, fwd_summary)."""
    tr, fw = [], []
    for s in SYMS:
        rows, bars, times = CACHE[s]
        if not rows: continue
        c = cost_for(s)
        for row in rows:
            if not gate(row): continue
            d = direction_pick(row)
            if d == 0: continue
            R = simulate(bars, row["i"], d, stop_dist=stop_mult * row["a"],
                         target_dist=target_mult * row["a"], cost=c)
            (fw if row["yr"] >= 2025 else tr).append(R)
    return summarize(tr), summarize(fw)

# direction by mean reversion: fade extreme z
def dir_z(thr_z, thr_rsi_lo=35, thr_rsi_hi=65):
    def f(row):
        if row["z"] <= -thr_z and row["rsi"] <= thr_rsi_lo: return +1
        if row["z"] >= thr_z and row["rsi"] >= thr_rsi_hi: return -1
        return 0
    return f

print("=== filter pass-rates (fraction of all bars admitted) ===")
tot = sum(len(CACHE[s][0]) for s in SYMS)
def frac(pred):
    n = sum(1 for s in SYMS for row in CACHE[s][0] if pred(row))
    return n, round(n / tot, 4)
print("total bars:", tot)
for name, pred in [
    ("adx<20", lambda r: r["adx"] < 20),
    ("adx<25", lambda r: r["adx"] < 25),
    ("adx<30", lambda r: r["adx"] < 30),
    ("vc<1.0", lambda r: r["vc"] < 1.0),
    ("vc<1.1", lambda r: r["vc"] < 1.1),
    ("er<0.3", lambda r: r["er"] < 0.3),
    ("er<0.4", lambda r: r["er"] < 0.4),
    ("|z|>=2", lambda r: abs(r["z"]) >= 2.0),
    ("|z|>=1.5", lambda r: abs(r["z"]) >= 1.5),
    ("|z|>=2 & adx<25", lambda r: abs(r["z"]) >= 2.0 and r["adx"] < 25),
    ("|z|>=2 & er<0.4", lambda r: abs(r["z"]) >= 2.0 and r["er"] < 0.4),
    ("|z|>=2 & vc<1.0", lambda r: abs(r["z"]) >= 2.0 and r["vc"] < 1.0),
]:
    n, fr = frac(pred); print(f"  {name:22s}: {n:6d}  ({fr})")

print("\n=== RAW reversion edge (|z|>=2, rsi 35/65), NO regime filter ===")
tr, fw = edge(lambda r: True, dir_z(2.0))
print(f"  TRAIN {tr}\n  FWD   {fw}")

print("\n=== add ONLY adx filter ===")
for amax in (30, 25, 20):
    tr, fw = edge(lambda r, a=amax: r["adx"] < a, dir_z(2.0))
    print(f"  adx<{amax}: TRAIN {tr} | FWD {fw}")

print("\n=== add ONLY efficiency-ratio (range) filter ===")
for emax in (0.5, 0.4, 0.3):
    tr, fw = edge(lambda r, e=emax: r["er"] < e, dir_z(2.0))
    print(f"  er<{emax}: TRAIN {tr} | FWD {fw}")

print("\n=== adx + er combined ===")
for amax in (30, 25):
    for emax in (0.5, 0.4):
        tr, fw = edge(lambda r, a=amax, e=emax: r["adx"] < a and r["er"] < e, dir_z(2.0))
        print(f"  adx<{amax} er<{emax}: TRAIN {tr} | FWD {fw}")

print("\n=== vary z extreme with adx<25 ===")
for zt in (1.5, 2.0, 2.5):
    tr, fw = edge(lambda r: r["adx"] < 25, dir_z(zt))
    print(f"  |z|>={zt} adx<25: TRAIN {tr} | FWD {fw}")
