#!/usr/bin/env python3
"""
Deep-dive: for XAUUSD in the live 168-bar window, what is the agreement
between prod_live touch_count and research touch_number? Also: are there
any research-touch-1 events the gate WOULD incorrectly reject?
"""
import pandas as pd
from pathlib import Path

p = Path(__file__).parent / "live_gate_sim.parquet"
df = pd.read_parquet(p)

print("=" * 70)
print("AGREEMENT ANALYSIS")
print("=" * 70)

for sym in ["XAUUSD", "US30_cash", "USDJPY", "GBPJPY", "GBPUSD"]:
    sub = df[(df["symbol"] == sym) & df["ob_in_168_bar_window"]]
    if sub.empty: continue
    # Research says touch=1, production live-window says >= 2 (would be rejected)
    r1 = sub[sub["touch_number_research"] == 1]
    n_r1 = len(r1)
    prod_agrees = (r1["touch_count_prod_live_window"] < 2).sum()
    print(f"\n{sym}: research_touch=1 events = {n_r1:,}")
    print(f"   prod_live < 2 agrees (gate passes): {prod_agrees:,} ({prod_agrees/n_r1*100:.1f}%)")
    print(f"   WR of agreed-passed: {r1[r1['touch_count_prod_live_window'] < 2]['continuation'].sum()/max(prod_agrees,1)*100:.1f}%")
    # Research says touch >= 2, production says < 2 (gate would erroneously PASS a stale retest)
    r2 = sub[sub["touch_number_research"] >= 2]
    prod_leaks = r2[r2["touch_count_prod_live_window"] < 2]
    n_leak = len(prod_leaks)
    print(f"   research_touch>=2 events = {len(r2):,}")
    print(f"   prod_live < 2 leaks (gate passes a stale retest): {n_leak:,} ({n_leak/max(len(r2),1)*100:.1f}%)")
    if n_leak > 0:
        leak_wr = prod_leaks["continuation"].sum() / n_leak * 100
        print(f"   WR of leaked (research-stale) events: {leak_wr:.1f}%")

print("\n" + "=" * 70)
print("FULL-DATASET AGREEMENT")
print("=" * 70)
live = df[df["ob_in_168_bar_window"]]
r1 = live[live["touch_number_research"] == 1]
r2p = live[live["touch_number_research"] >= 2]

print(f"\nresearch_touch == 1, prod_live < 2: {len(r1[r1['touch_count_prod_live_window'] < 2]):,} / {len(r1):,} = {(r1['touch_count_prod_live_window'] < 2).mean()*100:.2f}% agreement")
print(f"research_touch >= 2, prod_live >= 2: {len(r2p[r2p['touch_count_prod_live_window'] >= 2]):,} / {len(r2p):,} = {(r2p['touch_count_prod_live_window'] >= 2).mean()*100:.2f}% agreement")

# Confusion matrix for the binary {touch=1 vs touch>=2} decision
from_research = (live["touch_number_research"] == 1).astype(int)  # 1 if "fresh"
from_prod     = (live["touch_count_prod_live_window"] < 2).astype(int)  # 1 if "fresh" by prod
tn = int(((from_research==0) & (from_prod==0)).sum())
fp = int(((from_research==0) & (from_prod==1)).sum())
fn = int(((from_research==1) & (from_prod==0)).sum())
tp = int(((from_research==1) & (from_prod==1)).sum())
print(f"\nConfusion matrix (binary 'fresh' classification on live-detectable population n={len(live):,})")
print(f"  [research=stale, prod=stale] TN = {tn:,}")
print(f"  [research=stale, prod=fresh] FP = {fp:,}  <- leakage (gate passes a stale retest)")
print(f"  [research=fresh, prod=stale] FN = {fn:,}  <- miss (gate rejects a first-touch)")
print(f"  [research=fresh, prod=fresh] TP = {tp:,}")
print(f"  Cohen's Kappa ≈ {(tp+tn-((tp+fn)*(tp+fp)+(fp+tn)*(fn+tn))/len(live))/max(1-((tp+fn)*(tp+fp)+(fp+tn)*(fn+tn))/len(live), 1e-9):.3f}")

# WR of the FP cell — if gate passes a stale retest under research, what WR does it get?
fp_rows = live[(from_research==0) & (from_prod==1)]
if len(fp_rows) > 0:
    print(f"  WR of FP (leaked stale retests): {fp_rows['continuation'].sum()/len(fp_rows)*100:.1f}%, n={len(fp_rows)}")

print("\n" + "=" * 70)
print("DIVERGENCE-ON-STATIONARY TEST")
print("=" * 70)
# Reviewer's core claim: 'price sits stationary 5 bars inside a zone -> 5 prod, 1 research'.
# Find OBs where prod_live touch ~= 5+ * research touch. This is the "stationary" signature.
# For research_touch == 2 (smallest non-trivial case), how wide is prod_live distribution?
r2 = live[live["touch_number_research"] == 2]
print(f"\nresearch_touch == 2 (n={len(r2):,}): prod_live distribution:")
print(r2["touch_count_prod_live_window"].describe().to_string())

# How many research touch-2 events have prod_live >= 5 (5x divergence claim)?
divergent = r2[r2["touch_count_prod_live_window"] >= 5]
print(f"research_touch=2 with prod_live >= 5: {len(divergent):,} / {len(r2):,} = {len(divergent)/len(r2)*100:.1f}%")

# How about research touch-1 events where prod_live is high? Would fundamentally show the claim.
r1f = live[live["touch_number_research"] == 1]
hi = r1f[r1f["touch_count_prod_live_window"] >= 3]
print(f"\nresearch_touch=1 with prod_live >= 3 (strong divergence): {len(hi):,} / {len(r1f):,} = {len(hi)/len(r1f)*100:.3f}%")
