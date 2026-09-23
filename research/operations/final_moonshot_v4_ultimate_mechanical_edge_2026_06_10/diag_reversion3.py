"""Diagnostic 3 (final due diligence for the reversion class):
1) Per-asset-class reversion edge (maybe it lives in FX/JPY only).
2) WAIT-FOR-CONFIRMATION: don't catch the knife; enter only after the NEXT bar
   reverses (close back inside band / momentum flip). This is the strongest
   honest form of regime-filtered reversion.
3) Best-case search: across stop/target AND confirmation, is ANY config
   forward-positive with n>=150 AND train-positive (not overfit)?"""
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

# Per-class raw reversion (fade |z|>=2 in range adx<25, stop0.5 tgt1.0)
def per_class(zt, amax, sm, tm):
    buckets_tr = defaultdict(list); buckets_fw = defaultdict(list)
    for s in SYMS:
        ac = ASSET_CLASS_BY_SYMBOL[s]
        rows, bars, times = CACHE[s]
        if not rows: continue
        c = cost_for(s)
        for r in rows:
            if r["adx"] >= amax: continue
            d = 0
            if r["z"]<=-zt and r["rsi"]<=35: d=+1
            elif r["z"]>=zt and r["rsi"]>=65: d=-1
            if d==0: continue
            R = simulate(bars, r["i"], d, stop_dist=sm*r["a"], target_dist=tm*r["a"], cost=c)
            (buckets_fw[ac] if r["yr"]>=2025 else buckets_tr[ac]).append(R)
    return buckets_tr, buckets_fw

print("=== PER-CLASS reversion fade |z|>=2 adx<25 stop0.5 tgt1.0 ===")
tr_b, fw_b = per_class(2.0, 25, 0.5, 1.0)
for ac in sorted(set(ASSET_CLASS_BY_SYMBOL.values())):
    t = summarize(tr_b.get(ac,[])); f = summarize(fw_b.get(ac,[]))
    print(f"  {ac:8s}: TRAIN {t['per_trade_R']:+.3f}/{t['n']:4d} | "
          f"FWD {f['per_trade_R']:+.3f}/{f['n']:4d} win={f['win_rate']:.3f}")

# WAIT-FOR-CONFIRMATION: signal bar i is extreme; enter at i+1 ONLY if bar i+1
# reverses (long: i+1 closes above i's high; short: i+1 closes below i's low).
# Entry is at bar i+1 close -> simulate(bars, i+1, d, ...).
def confirm_run(gate, zt, sm, tm, mode_trail=None):
    tr, fw = [], []; by_year=defaultdict(list)
    for s in SYMS:
        rows, bars, times = CACHE[s]
        if not rows: continue
        c = cost_for(s)
        L = len(bars)
        # need access to bar i+1; rows store i. Build quick index of admitted extremes.
        for r in rows:
            i = r["i"]
            if i+1 >= L-1: continue
            if not gate(r): continue
            d = 0
            if r["z"]<=-zt and r["rsi"]<=35: d=+1
            elif r["z"]>=zt and r["rsi"]>=65: d=-1
            if d==0: continue
            nb = bars[i+1]
            # confirmation: the turn happened
            if d>0 and not (nb.c > bars[i].h): continue
            if d<0 and not (nb.c < bars[i].l): continue
            a = r["a"]
            if mode_trail:
                R = simulate(bars, i+1, d, stop_dist=sm*a,
                             trail_arm=mode_trail[0]*sm*a, trail_gap=mode_trail[1]*sm*a, cost=c)
            else:
                R = simulate(bars, i+1, d, stop_dist=sm*a, target_dist=tm*a, cost=c)
            (fw if r["yr"]>=2025 else tr).append(R)
            by_year[r["yr"]].append(R)
    return summarize(tr), summarize(fw), by_year

print("\n=== WAIT-FOR-CONFIRMATION reversion (enter after the turn) ===")
gate_r = lambda r: r["adx"] < 25
gate_a = lambda r: True
best = None
for gname, gate in [("all",gate_a),("adx<25",gate_r),("adx<20",lambda r:r["adx"]<20)]:
    for zt in (1.5, 2.0):
        for sm in (0.5, 1.0):
            for tm in (1.0, 1.5, 2.0):
                t,f,by = confirm_run(gate, zt, sm, tm)
                fy={y:summarize(by[y]) for y in sorted(by) if y>=2025}
                tag=f"{gname} z>={zt} stop{sm} tgt{tm}"
                print(f"  {tag:26s}: TRAIN {t['per_trade_R']:+.3f}/{t['n']:4d} | "
                      f"FWD {f['per_trade_R']:+.3f}/{f['n']:4d} win={f['win_rate']:.3f}")
                if f['n']>=150 and f['per_trade_R']>0 and t['per_trade_R']>0:
                    if best is None or f['per_trade_R']>best[1]['per_trade_R']:
                        best=(tag,f,t,fy)
# confirmation + trail
for gname, gate in [("adx<25",gate_r)]:
    for zt in (2.0,):
        for arm,gap in ((2.0,1.0),(1.0,0.5)):
            t,f,by=confirm_run(gate,zt,0.5,None,mode_trail=(arm,gap))
            tag=f"{gname} z>={zt} trail{arm}/{gap}"
            print(f"  {tag:26s}: TRAIN {t['per_trade_R']:+.3f}/{t['n']:4d} | "
                  f"FWD {f['per_trade_R']:+.3f}/{f['n']:4d} win={f['win_rate']:.3f}")
            if f['n']>=150 and f['per_trade_R']>0 and t['per_trade_R']>0:
                fy={y:summarize(by[y]) for y in sorted(by) if y>=2025}
                if best is None or f['per_trade_R']>best[1]['per_trade_R']:
                    best=(tag,f,t,fy)

print("\n=== VERDICT ===")
if best:
    print("FOUND forward+train-positive (n>=150):", best[0])
    print("  FWD:", best[1], "TRAIN:", best[2], "fwd_years:", best[3])
else:
    print("NO regime-filtered reversion config is forward-positive AND "
          "train-positive with n>=150. Reversion class is DEAD on this data.")
