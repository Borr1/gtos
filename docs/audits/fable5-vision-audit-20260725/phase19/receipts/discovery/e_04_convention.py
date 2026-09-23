#!/usr/bin/env python3
"""e-coherence step 4 — THE CONVENTION AUDIT.

The swarm agreed W0-F2's fill-BLIND convention manufactures edge, and every lane switched
to the fill-HONEST convention (entry must be TRADED before the walk starts).  Nobody
checked whether the honest convention is right for the 53.9% of rows that are AT-MARKET
orders, where there is nothing to wait for.  If it is not, then part of the "first-minute
adverse selection" every lane found is the convention, not the market.

Three conventions, same rows, same exits:
  BLIND   walk from path bar 1, ignore whether entry ever traded      (W0-F2's fiction)
  HONEST  require entry touch, walk from the touch bar                 (the swarm standard)
  MARKET  no touch requirement, walk from bar 1 at the entry price     (== BLIND for at-market
          rows by algebra, and IMPOSSIBLE for genuine resting limits)
The correct contract is per born state: MARKET for at_limit/marketable, HONEST for resting.
"""
import json, os, pickle
import numpy as np
import pandas as pd

D = os.path.dirname(os.path.abspath(__file__))
df = pickle.load(open("/tmp/ecoh/e_base.pkl", "rb"))
N = len(df)
df["B"] = df["plain_walk_r"].astype(float)
born, b1 = df["born"], df["bars_to_entry_touch"] == 1
OUT = {}

# ---- 1. is BLIND == MARKET for at-market rows?  (L7 asserted identity; verify)
al = born == "at_limit"
OUT["blind_is_market_for_at_limit"] = {
    "n": int(al.sum()),
    "max_abs_diff_gross_vs_blind": float((df.loc[al, "gross_r"] - df.loc[al, "B"]).abs().max()),
    "mean_B": round(float(df.loc[al, "B"].mean()), 6),
    "mean_H": round(float(df.loc[al, "H"].mean()), 6),
    "mean_G": round(float(df.loc[al, "gross_r"].mean()), 6),
}

# ---- 2. the per-born-state convention table
tab = []
for b in ["at_limit", "marketable", "resting", "past_stop"]:
    m = born == b
    tab.append({
        "born": b, "n": int(m.sum()),
        "BLIND": round(float(df.loc[m, "B"].mean()), 6),
        "HONEST": round(float(df.loc[m, "H"].mean()), 6),
        "honest_minus_blind": round(float((df.loc[m, "H"] - df.loc[m, "B"]).mean()), 6),
        "entry_never_touched": int((~df.loc[m, "entry_touched"].astype(bool)).sum()),
        "touch_bar_median": (None if df.loc[m, "bars_to_entry_touch"].isna().all()
                             else float(df.loc[m, "bars_to_entry_touch"].median())),
        "order_type_live_possible": b in ("at_limit", "marketable"),
    })
OUT["convention_by_born"] = tab

# ---- 3. THE CORRECT MIXED CONTRACT: market fill for at-market/marketable, honest for resting
mkt_side = born.isin(["at_limit", "marketable", "past_stop", "unanchored"])
mixed = np.where(mkt_side, df["B"], df["H"])
df["MIXED"] = mixed
OUT["headline_by_convention"] = {
    "pool_n": N,
    "BLIND_all": round(float(df["B"].mean()), 6),
    "HONEST_all": round(float(df["H"].mean()), 6),
    "MIXED_all": round(float(df["MIXED"].mean()), 6),
    "ENGINE_gross_all": round(float(df["gross_r"].mean()), 6),
    "HONEST_ex_past_stop": round(float(df.loc[born != "past_stop", "H"].mean()), 6),
    "MIXED_ex_past_stop": round(float(df.loc[born != "past_stop", "MIXED"].mean()), 6),
}

# ---- 4. how much of the bar-1 penalty survives the convention fix?
res = []
for conv, col in (("HONEST", "H"), ("MIXED", "MIXED")):
    for lbl, m in (("bar1", b1 & (born != "past_stop")), ("not_bar1", (~b1) & (born != "past_stop"))):
        s = df.loc[m, col]
        res.append({"convention": conv, "cohort": lbl, "n": int(m.sum()),
                    "mean": round(float(s.mean()), 6),
                    "se": round(float(s.std(ddof=1) / np.sqrt(len(s))), 6)})
OUT["bar1_penalty_by_convention"] = res
h_gap = (df.loc[b1 & (born != "past_stop"), "H"].mean()
         - df.loc[(~b1) & (born != "past_stop"), "H"].mean())
m_gap = (df.loc[b1 & (born != "past_stop"), "MIXED"].mean()
         - df.loc[(~b1) & (born != "past_stop"), "MIXED"].mean())
OUT["bar1_penalty_size"] = {"under_HONEST": round(float(h_gap), 6),
                            "under_MIXED": round(float(m_gap), 6),
                            "share_of_penalty_that_is_convention": round(float(1 - m_gap / h_gap), 4)}

# ---- 5. within at-market rows ONLY (no limit anywhere): does the touch requirement bite?
sub = df.loc[al]
touched_b1 = sub["bars_to_entry_touch"] == 1
OUT["at_market_touch_conditioning"] = {
    "n": int(len(sub)),
    "touched_bar1_n": int(touched_b1.sum()),
    "touched_bar1_share": round(float(touched_b1.mean()), 5),
    "never_touched_n": int((~sub["entry_touched"].astype(bool)).sum()),
    "MARKET_walk_on_touched_bar1": round(float(sub.loc[touched_b1, "B"].mean()), 6),
    "MARKET_walk_on_NOT_touched_bar1": round(float(sub.loc[~touched_b1, "B"].mean()), 6),
    "HONEST_walk_on_touched_bar1": round(float(sub.loc[touched_b1, "H"].mean()), 6),
    "HONEST_walk_on_NOT_touched_bar1": round(float(sub.loc[~touched_b1, "H"].mean()), 6),
    "interpretation": "if MARKET differs across the touch split, the touch flag is selecting; "
                      "if HONEST differs much more, the difference is the convention",
}

json.dump(OUT, open(f"{D}/E_CONVENTION_V1.json", "w"), indent=1)
print(json.dumps(OUT["blind_is_market_for_at_limit"]))
print("--- convention by born ---")
for t in tab:
    print(f"{t['born']:11s} n={t['n']:6d} BLIND={t['BLIND']:+.5f} HONEST={t['HONEST']:+.5f} H-B={t['honest_minus_blind']:+.5f} untouched={t['entry_never_touched']:4d} livepossible={t['order_type_live_possible']}")
print(json.dumps(OUT["headline_by_convention"], indent=0))
print("--- bar1 penalty ---")
for r in res:
    print(f"  {r['convention']:7s} {r['cohort']:9s} n={r['n']:6d} {r['mean']:+.5f} +-{r['se']:.5f}")
print(json.dumps(OUT["bar1_penalty_size"]))
print(json.dumps(OUT["at_market_touch_conditioning"], indent=0))
