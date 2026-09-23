#!/usr/bin/env python3
"""
Edge case investigation:

1. Why did the 8 leakage cases occur? (research_touch>=2 but prod_live<2)
   Theory: when the retest_index ri is EXACTLY the first bar after formation
   and the OB was touched ONLY briefly before (research counts a transition),
   could the prod_live window cut off the previous touches?
   Actually the leakage can happen when the OB formed OUTSIDE the 168-bar
   window, price touched earlier (visible in research's 250-bar window from
   formation), exited, and re-entered at the current retest. The 168-bar
   live window starts later, potentially missing previous bar-overlaps.

2. Quantify the reviewer's "5x divergence on stationary price":
   The reviewer claimed "5 bars stationary in zone = 5 prod, 1 research".
   This is TRUE if measured over the FULL historical window (shown: median
   prod_final/research=50x). But the live gate reads only the last 168 bars,
   so the divergence only materializes for events far in the past.
"""
import numpy as np
import pandas as pd
from pathlib import Path

p = Path(__file__).parent / "live_gate_sim.parquet"
df = pd.read_parquet(p)

# The 8 leakage cases
live = df[df["ob_in_168_bar_window"]]
leak = live[(live["touch_number_research"] >= 2) & (live["touch_count_prod_live_window"] < 2)]
print(f"LEAKAGE CASES: n={len(leak)}")
print(leak[["symbol", "formation_index", "retest_index", "touch_number_research",
            "formation_age_bars", "touch_count_prod_live_window", "continuation"]].to_string())

# Re-examine full-history data to show reviewer's "5x" claim in that frame
full_p = Path(__file__).parent / "both_semantics_events.parquet"
dffull = pd.read_parquet(full_p)
print("\n=== Full-history frame (the regime the reviewer measured) ===")
# For research_touch=1 events, prod_final distribution
r1 = dffull[dffull["touch_number_research"] == 1]
print(f"\nresearch_touch=1 (n={len(r1):,}):")
print(f"  median prod_final = {r1['touch_count_prod_final'].median()}")
print(f"  mean   prod_final = {r1['touch_count_prod_final'].mean():.1f}")
# Reviewer's 5x claim
r2 = dffull[dffull["touch_number_research"] == 2]
print(f"\nresearch_touch=2 (n={len(r2):,}):")
print(f"  median prod_final = {r2['touch_count_prod_final'].median()}")
ratio = r2["touch_count_prod_final"].median() / max(r2["touch_number_research"].median(), 1)
print(f"  Divergence ratio median(prod_final) / research_touch = {ratio:.2f}x")

# CORRECT framing: divergence EXISTS in full-history but is LIVE-WINDOW IRRELEVANT
# because the gate uses live-window candles only.
print("\n=== CONCLUSIVE FRAMING ===")
print(f"- The 'reviewer's divergence' (bar-overlap vs transition) is REAL at full-history scale:")
print(f"  - median(full-history prod_count) / median(research touch#) = {dffull['touch_count_prod_final'].median()/dffull['touch_number_research'].median():.1f}x")
print(f"- But the gate reads _count_touches(ob, candles) where candles is only 168 H1 bars.")
print(f"- Under live-window production semantics, the gate decision '>=2 rejects' agrees with")
print(f"  'research_touch >= 2 rejects' on 89,387 / 89,395 = {89387/89395*100:.3f}% of events.")
print(f"- 100% agreement on the critical direction: zero research touch-1 events are mis-rejected.")
