#!/usr/bin/env python3
"""ATTRITION RECOVERY target 2 — AH volume_surge_reversal x index x D1 @ VOL_REGIME==hi.
Reproduce the cell from raw inputs, measure the instrument, restate honestly."""
import sys, json, gzip, statistics, collections, math
from pathlib import Path
REPO = Path("/Users/borr/GTOSActive/worktrees/claude-opus5-architecture-audit-20260725")
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO/"docs/audits/fable5-vision-audit-20260725/phase7/receipts"))
sys.path.insert(0, str(REPO/"docs/audits/fable5-vision-audit-20260725/phase8/receipts"))
import af_repairs as AFR
import ah_conditioning as AH

art, series, regimes = AH.load_all()
fams = AH.members_of(art)
f = "fam_volume_surge_reversal_index_d1"
mem = fams[f]
rows = [dict(r, _m=m) for m in mem for r in AH.reachable(art["trades"].get(m, []))]
print("family", f, "members", len(mem), "reachable rows", len(rows))

sel_hi = [r for r in rows if AFR.bucket("VOL_REGIME",
          regimes.get(r["_m"], {}).get(r["decision_bar_iso"], {}).get("VOL_REGIME")) == "hi"]
print("VOL_REGIME==hi n =", len(sel_hi), "(published 203)")
print("mean_r_gross  =", round(statistics.mean(r["r_gross"] for r in sel_hi), 5), "(published 0.2266)")
fl = AH.folds_of(sel_hi)
fm = [round(statistics.mean(c["r_gross"] for c in ch), 5) for ch in fl if ch]
print("chronological quintile means:", fm, "(published [0.09756,0.46341,0.17073,0.09756,0.30769])")

# ---- instrument identity: is r_gross spread-free?
vals = collections.Counter(round(r["r_gross"], 9) for r in rows)
print("\nINSTRUMENT — distinct r_gross values over the whole family:", dict(vals))
print("exit_reason:", dict(collections.Counter(r["exit_reason"] for r in rows)))

# ---- broker-true spread in R units for these trades
costs = json.load(open(REPO/"research/operations/broker_truth_layer_2026_07_29/BROKER_TRUE_COSTS_V1_1.json"))
inst = costs["accounts"]["FTMO"]["instruments"]
def spread_price(symbol):
    ent = inst.get(symbol)
    if not ent: return None
    sp = ent.get("spread_price") or {}
    bys = sp.get("by_session") or {}
    vals = [v.get("mid") if isinstance(v, dict) else v for v in bys.values()]
    vals = [float(v) for v in vals if isinstance(v, (int, float))]
    if vals: return sum(vals)/len(vals)
    for k in ("mid", "value", "all"):
        if isinstance(sp.get(k), (int, float)): return float(sp[k])
    return None
syms = sorted({r["symbol"] for r in rows})
sp_by = {s: spread_price(s) for s in syms}
print("\nbroker-true mid spread (price units):", sp_by)
srs = []
for r in rows:
    sp = sp_by.get(r["symbol"])
    if sp is None: continue
    srs.append(sp / r["sl_distance_price"])
if srs:
    srs_sorted = sorted(srs)
    print("spread_r over the family: n=%d mean %.6f median %.6f p90 %.6f max %.6f"
          % (len(srs), sum(srs)/len(srs), srs_sorted[len(srs)//2],
             srs_sorted[int(0.9*len(srs))], srs_sorted[-1]))
srs_hi = []
for r in sel_hi:
    sp = sp_by.get(r["symbol"])
    if sp is not None: srs_hi.append(sp / r["sl_distance_price"])
if srs_hi:
    print("spread_r on the VOL_REGIME==hi cell: n=%d mean %.6f median %.6f"
          % (len(srs_hi), sum(srs_hi)/len(srs_hi), sorted(srs_hi)[len(srs_hi)//2]))

# ---- how close were the target/stop touches to the spread? (migration exposure)
# mfe_r / mae_r are the realised excursions in R; a target row whose MFE only just cleared 2.0
# would migrate if the executable quote is one spread worse.
tgt = [r for r in sel_hi if r["exit_reason"] == "target"]
print("\nMIGRATION EXPOSURE on the cell: %d target rows" % len(tgt))
for thr in (0.001, 0.005, 0.01, 0.02, 0.05):
    n = sum(1 for r in tgt if (r["mfe_r"] - 2.0) < thr)
    print("  target rows whose MFE cleared 2.0R by less than %.3f R: %d (%.1f%%)"
          % (thr, n, 100*n/len(tgt) if tgt else 0))

out = dict(n_hi=len(sel_hi), mean_r_gross_hi=statistics.mean(r["r_gross"] for r in sel_hi),
           quintile_means=fm, r_gross_values={str(k): v for k, v in vals.items()},
           spread_r_family=dict(n=len(srs), mean=sum(srs)/len(srs) if srs else None),
           spread_r_cell=dict(n=len(srs_hi), mean=sum(srs_hi)/len(srs_hi) if srs_hi else None),
           spread_price_by_symbol=sp_by,
           n_target_rows=len(tgt),
           migration_exposure={str(t): sum(1 for r in tgt if (r["mfe_r"]-2.0) < t) for t in (0.001,0.005,0.01,0.02,0.05)})
json.dump(out, open("/private/tmp/AH_REPRO.json", "w"), indent=1)
