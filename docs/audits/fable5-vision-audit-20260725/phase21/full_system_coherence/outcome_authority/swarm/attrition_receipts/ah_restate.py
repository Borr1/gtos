#!/usr/bin/env python3
"""AH cell: instrument restatement + selection-aware p-value."""
import sys, json, gzip, statistics, collections, math
from pathlib import Path
import numpy as np
REPO = Path("/Users/borr/GTOSActive/worktrees/claude-opus5-architecture-audit-20260725")
for p in ("", "docs/audits/fable5-vision-audit-20260725/phase7/receipts",
          "docs/audits/fable5-vision-audit-20260725/phase8/receipts"):
    sys.path.insert(0, str(REPO/p))
import af_repairs as AFR, ah_conditioning as AH

art, series, regimes = AH.load_all()
fams = AH.members_of(art); f = "fam_volume_surge_reversal_index_d1"
rows = [dict(r, _m=m) for m in fams[f] for r in AH.reachable(art["trades"].get(m, []))]

costs = json.load(open(REPO/"research/operations/broker_truth_layer_2026_07_29/BROKER_TRUE_COSTS_V1_1.json"))
inst = costs["accounts"]["FTMO"]["instruments"]
def sp50(sym, sess="ny"):
    e = inst.get(sym) or {}
    bys = ((e.get("spread_price") or {}).get("by_session") or {})
    if sess in bys and "p50" in bys[sess]: return float(bys[sess]["p50"])
    ps = (e.get("spread_price") or {}).get("percentiles") or {}
    return float(ps["p50"]) if "p50" in ps else None
SESS = "ny"
for r in rows:
    s = sp50(r["symbol"], SESS)
    r["_spread_r"] = (s / r["sl_distance_price"]) if s else None
    r["_slip_r"] = float((inst.get(r["symbol"]) or {}).get("slippage", {}).get("value_r") or 0.0)

def cell(dial, b):
    return [r for r in rows if AFR.bucket(dial, regimes.get(r["_m"], {})
            .get(r["decision_bar_iso"], {}).get(dial)) == b]
hi = cell("VOL_REGIME", "hi")
srs = np.array([r["_spread_r"] for r in hi if r["_spread_r"] is not None])
print(f"cell n={len(hi)}  spread_r coverage {len(srs)}/{len(hi)}")
print(f"spread_r: mean {srs.mean():.6f} median {np.median(srs):.6f} p90 {np.percentile(srs,90):.6f} max {srs.max():.6f}")
slip = np.array([r["_slip_r"] for r in hi]); print(f"slippage_r (broker-true, transferred): mean {slip.mean():.6f}")

g = np.array([r["r_gross"] for r in hi])
sr = np.array([r["_spread_r"] or 0.0 for r in hi])
print(f"\npublished gross mean {g.mean():.6f} (n {len(g)})")
lvl = g - sr
print(f"quote-frame level correction (gross - spread_r): {lvl.mean():.6f}  (delta {lvl.mean()-g.mean():+.6f})")
# migration bound: SHORT target rows whose MFE cleared 2.0R by less than spread_r
mig = [r for r in hi if r["direction"] < 0 and r["exit_reason"] == "target"
       and r["_spread_r"] is not None and (r["mfe_r"] - 2.0) < r["_spread_r"]]
migL = [r for r in hi if r["direction"] > 0 and r["exit_reason"] == "target"
        and r["_spread_r"] is not None and (r["mfe_r"] - 2.0) < r["_spread_r"]]
n_short = sum(1 for r in hi if r["direction"] < 0); n_long = len(hi)-n_short
print(f"sides: LONG {n_long} SHORT {n_short}; SHORT target rows exposed to migration: {len(mig)} (LONG {len(migL)}, structurally immune)")
worst = lvl.copy()
for i, r in enumerate(hi):
    if r in mig: worst[i] = -1.0 - (r["_spread_r"] or 0.0)
print(f"worst-case (every exposed SHORT target migrates to stop): {worst.mean():.6f}")
net = lvl - slip
print(f"minus broker-true slippage: {net.mean():.6f}   (commission on index = 0.0, MEASURED)")

# ---------- selection-aware p on the 9-cell enumeration
enum = []
for dial in AFR.DIALS:
    for b in ("lo","mid","hi","xhi","revert","random","trend","dn","flat","up"):
        s = cell(dial, b)
        if len(s) >= 60: enum.append((f"{dial}=={b}", s))
print(f"\nenumerated cells with n>=60: {len(enum)} (published 9): {[k for k,_ in enum]}")

def folds5(idx, gv):
    order = np.argsort(idx); size = math.ceil(len(order)/5)
    return [gv[order[i*size:(i+1)*size]] for i in range(5)]
allrows = rows
gv = np.array([r["r_gross"] for r in allrows])
tv = np.array([r["entry_utc"] for r in allrows])
labels = {}
for dial in AFR.DIALS:
    labels[dial] = np.array([AFR.bucket(dial, regimes.get(r["_m"], {})
                    .get(r["decision_bar_iso"], {}).get(dial)) for r in allrows])
tsort = np.argsort(tv)
def stat_for(mask):
    if mask.sum() < 60: return None
    sub = np.array([i for i in tsort if mask[i]])
    size = math.ceil(len(sub)/5)
    fmeans = [gv[sub[i*size:(i+1)*size]].mean() for i in range(5) if len(sub[i*size:(i+1)*size])]
    return (sum(1 for x in fmeans if x > 0)/len(fmeans), gv[mask].mean())
obs = {}
for dial in AFR.DIALS:
    for b in set(labels[dial]):
        s = stat_for(labels[dial] == b)
        if s: obs[f"{dial}=={b}"] = s
best_key = max(obs, key=lambda k: obs[k]); print("observed best:", best_key, obs[best_key])
rng = np.random.default_rng(20260812); NP = 20000
ge_mean = 0; ge_55 = 0; ge_both = 0
obs_fp, obs_mean = obs[best_key]
for _ in range(NP):
    perm = rng.permutation(len(allrows))
    bm, b55 = -9e9, 0
    for dial in AFR.DIALS:
        lab = labels[dial][perm]
        for b in set(lab):
            m = lab == b
            if m.sum() < 60: continue
            sub = np.array([i for i in tsort if m[i]])
            size = math.ceil(len(sub)/5)
            fm = [gv[sub[i*size:(i+1)*size]].mean() for i in range(5) if len(sub[i*size:(i+1)*size])]
            fp = sum(1 for x in fm if x > 0)/len(fm)
            mu = gv[m].mean()
            bm = max(bm, mu)
            if fp >= 1.0: b55 = 1
    if bm >= obs_mean: ge_mean += 1
    if b55: ge_55 += 1
print(f"\nmax-T over the enumeration ({NP} label permutations):")
print(f"  P(best enumerated cell mean_r_gross >= {obs_mean:.5f}) = {ge_mean/NP:.5f}")
print(f"  P(ANY enumerated cell shows 5/5 positive chronological folds) = {ge_55/NP:.5f}")
json.dump(dict(n=len(hi), gross=float(g.mean()), spread_r_mean=float(srs.mean()),
  level_corrected=float(lvl.mean()), worst_case_migration=float(worst.mean()),
  minus_slippage=float(net.mean()), n_long=n_long, n_short=n_short,
  n_short_target_exposed=len(mig), enumerated_cells=[k for k,_ in enum],
  maxT_p_mean=ge_mean/NP, maxT_p_5of5=ge_55/NP, n_perm=NP,
  published_raw_p=0.012698730126987301, published_bonferroni_within_enum=0.11428857114288571),
  open("/private/tmp/AH_RESTATE.json","w"), indent=1)
