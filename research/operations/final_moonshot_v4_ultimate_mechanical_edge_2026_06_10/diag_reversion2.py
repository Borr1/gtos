"""Diagnostic 2: the fixed 2:1 target is wrong for reversion. Test exits sized
to the actual reversion distance (back toward the mean), tighter targets, and
the inverse (continuation) hypothesis. Also confirm: is regime-filtered
reversion EVER forward-positive, or is the whole class dead?"""
from __future__ import annotations
import sys, os, json
from collections import defaultdict
REPO = "/Users/borr/Documents/gtos/repo/ai-trading-agent"
EDGE = REPO + "/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
DATA = REPO + "/data/mt5_research_exports/bridge_ftmo_deep_h4_2022_2026"
sys.path.insert(0, REPO); sys.path.insert(0, EDGE)
from geometry_lib import simulate
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL
from diag_reversion import CACHE, SYMS
from hunt_reversion_regime_filtered import summarize, cost_for

def run(gate, dirpick, stop_mult, target_mult=None, trail=None):
    tr, fw = [], []
    by_year = defaultdict(list)
    for s in SYMS:
        rows, bars, times = CACHE[s]
        if not rows: continue
        c = cost_for(s)
        for row in rows:
            if not gate(row): continue
            d = dirpick(row)
            if d == 0: continue
            sd = stop_mult * row["a"]
            if trail:
                R = simulate(bars, row["i"], d, stop_dist=sd,
                             trail_arm=trail[0]*sd, trail_gap=trail[1]*sd, cost=c)
            else:
                R = simulate(bars, row["i"], d, stop_dist=sd,
                             target_dist=target_mult*row["a"], cost=c)
            (fw if row["yr"]>=2025 else tr).append(R)
            by_year[row["yr"]].append(R)
    return summarize(tr), summarize(fw), by_year

# reversion fade
def fade(zt, rsi_lo, rsi_hi):
    def f(r):
        if r["z"]<=-zt and r["rsi"]<=rsi_lo: return +1
        if r["z"]>=zt and r["rsi"]>=rsi_hi: return -1
        return 0
    return f
# continuation (inverse): trade WITH the extreme
def cont(zt, rsi_lo, rsi_hi):
    def f(r):
        if r["z"]<=-zt and r["rsi"]<=rsi_lo: return -1  # extreme down -> short (continue)
        if r["z"]>=zt and r["rsi"]>=rsi_hi: return +1
        return 0
    return f

gate_range = lambda r: r["adx"] < 25
gate_all = lambda r: True

print("=== FADE, vary stop/target ratio (gate adx<25, |z|>=2, rsi35/65) ===")
g = fade(2.0, 35, 65)
for sm in (0.5, 1.0):
    for tm in (0.5, 0.75, 1.0, 1.5):
        tr, fw, _ = run(gate_range, g, sm, target_mult=tm)
        print(f"  stop={sm} tgt={tm}: TRAIN {tr['per_trade_R']:+.3f}/{tr['n']} | "
              f"FWD {fw['per_trade_R']:+.3f}/{fw['n']} win={fw['win_rate']:.3f}")

print("\n=== FADE with trail (gate adx<25, |z|>=2) ===")
for arm, gap in ((2.0,1.0),(1.5,1.0),(1.0,0.5)):
    tr, fw, _ = run(gate_range, g, 0.5, trail=(arm,gap))
    print(f"  trail arm={arm} gap={gap}: TRAIN {tr['per_trade_R']:+.3f}/{tr['n']} | "
          f"FWD {fw['per_trade_R']:+.3f}/{fw['n']} win={fw['win_rate']:.3f}")

print("\n=== INVERSE: CONTINUATION at extremes (the real edge?) ===")
gc = cont(2.0, 35, 65)
for gate_name, gate in [("all", gate_all), ("adx<25 range", gate_range),
                        ("adx>30 trend", lambda r: r["adx"]>30)]:
    for tm in (1.0, 1.5, 2.0):
        tr, fw, _ = run(gate, gc, 0.5, target_mult=tm)
        print(f"  {gate_name:14s} tgt={tm}: TRAIN {tr['per_trade_R']:+.3f}/{tr['n']} | "
              f"FWD {fw['per_trade_R']:+.3f}/{fw['n']} win={fw['win_rate']:.3f}")
print("  -- continuation with trail (adx>30 trend) --")
for arm, gap in ((2.0,1.0),(3.0,1.5)):
    tr, fw, _ = run(lambda r: r["adx"]>30, gc, 0.5, trail=(arm,gap))
    print(f"  trend trail arm={arm}/{gap}: TRAIN {tr['per_trade_R']:+.3f}/{tr['n']} | "
          f"FWD {fw['per_trade_R']:+.3f}/{fw['n']} win={fw['win_rate']:.3f}")

print("\n=== FADE: require price OUTSIDE band but regime contracting, small tgt 0.5 ===")
# best shot for reversion: tiny target (just the snap-back)
for zt in (1.5, 2.0):
    for amax in (20, 25, 30):
        gg = fade(zt, 40, 60)
        tr, fw, by = run(lambda r,a=amax: r["adx"]<a, gg, 0.5, target_mult=0.5)
        fy = {y:summarize(by[y]) for y in sorted(by) if y>=2025}
        print(f"  z>={zt} adx<{amax} tgt0.5: TRAIN {tr['per_trade_R']:+.3f}/{tr['n']} | "
              f"FWD {fw['per_trade_R']:+.3f}/{fw['n']} win={fw['win_rate']:.3f} | "
              f"yrs {[(y,fy[y]['per_trade_R']) for y in fy]}")
