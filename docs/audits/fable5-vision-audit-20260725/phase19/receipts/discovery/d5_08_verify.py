"""d5-08 — independent verification of the central mechanical claim.

CLAIM UNDER TEST (the fill question, item 3):
  For a resting order placed at the decision instant T at price e, the statement
  "price has run AGAINST the entry by the close of [T, T+1m)"  (c0 < 0)
  is, for every row whose entry sits at price improvement (mkt_r0 > 0), LOGICALLY
  EQUIVALENT to "the order was already filled inside [T, T+1m)".
  Proof sketch: low(minute 0) <= close(minute 0) < e for a LONG => the level traded.
  If true, the observable can never be used to REFUSE the trade: it is a description
  of the fill, not information preceding it.

Also measures WHY x4 saw something different on the counterfactual pool.
"""
import json, sys
import numpy as np
sys.path.insert(0, "/tmp/d5")
from d5_lib import *

R = {"per_window": {}, "note": __doc__}
acc = {k: [] for k in ("c0", "mkt_r0", "j", "g", "net", "cost_r", "reason", "dayi", "win", "fam", "sym")}
for wi, w in enumerate(WINDOWS):
    D = load(w)
    n = D["g"].size
    mk, c0, j = D["mkt_r0"], D["c0"], D["j"]
    honest = mk > 0.0                      # entry strictly at price improvement
    adverse = c0 < 0.0
    m = honest & adverse
    viol = int((m & (j != 0)).sum())
    # the strict identity uses the minute's LOW, which we did not store; c0<0 implies
    # low<close<e so the identity must hold exactly.  count violations.
    R["per_window"][w] = {
        "n": int(n),
        "n_mkt_r0>0": int(honest.sum()),
        "n_mkt_r0>0_and_c0<0": int(m.sum()),
        "violations_j!=0": viol,
        "violation_rate": float(viol / max(m.sum(), 1)),
        "n_mkt_r0<0 (entry beyond market = stop order)": int((mk < 0).sum()),
        "n_mkt_r0==0 (at market)": int((mk == 0).sum()),
        "share_prefilled_j0": float((j == 0).mean()),
        "share_never_filled": float((j < 0).mean()),
    }
    for k in ("c0", "mkt_r0", "j", "g", "net", "cost_r", "reason", "dayi", "fam", "sym"):
        acc[k].append(D[k])
    acc["win"].append(np.full(n, wi))
A = {k: np.concatenate(v) for k, v in acc.items()}
N = A["g"].size
mk, c0, j, g = A["mkt_r0"], A["c0"], A["j"], A["g"]
day = A["dayi"] + 1000 * A["win"]

R["pooled"] = {
    "N": int(N),
    "n_identity_population(mkt_r0>0 & c0<0)": int(((mk > 0) & (c0 < 0)).sum()),
    "violations": int(((mk > 0) & (c0 < 0) & (j != 0)).sum()),
}

# ---- the actionable partition, at three thresholds
part = {}
for th in (-0.30, -0.15, -0.05, 0.0):
    ad = c0 <= th
    pre = j == 0
    pend = j > 0
    nev = j < 0
    part["c0<=%.2f" % th] = {
        "n_adverse": int(ad.sum()),
        "adverse_gross": float(g[ad].mean()),
        "adverse_total_R": float(g[ad].sum()),
        "already_filled_j0": {"n": int((ad & pre).sum()), "share": float((ad & pre).sum() / max(ad.sum(), 1)),
                              "total_R": float(g[ad & pre].sum()), "mean": float(g[ad & pre].mean()) if (ad & pre).any() else None},
        "cancellable_j>=1": {"n": int((ad & pend).sum()), "share": float((ad & pend).sum() / max(ad.sum(), 1)),
                             "total_R": float(g[ad & pend].sum()), "mean": float(g[ad & pend].mean()) if (ad & pend).any() else None},
        "never_filled": {"n": int((ad & nev).sum()), "total_R": float(g[ad & nev].sum())},
    }
    tot = float(g[ad].sum())
    canc = float(g[ad & pend].sum())
    part["c0<=%.2f" % th]["pct_of_adverse_loss_that_a_CANCEL_can_avoid"] = float(canc / tot) if tot else None
R["actionable_partition"] = part

# ---- what a cancel is worth per opportunity (achievable) vs the oracle (not achievable)
for th in (-0.15, -0.05, 0.0):
    ad = c0 <= th
    canc = ad & (j > 0)
    g_or = np.where(ad, 0.0, g)
    g_ca = np.where(canc, 0.0, g)
    R.setdefault("value_per_opportunity", {})["c0<=%.2f" % th] = {
        "baseline": float(g.mean()),
        "oracle_refuse": float(g_or.mean()),
        "achievable_cancel": float(g_ca.mean()),
        "oracle_minus_baseline": float(g_or.mean() - g.mean()),
        "cancel_minus_baseline": float(g_ca.mean() - g.mean()),
        "cancel_ci": dayblock_ci(g_ca - g, day),
    }

# ---- WHY the pool looked different: composition of the refused set by order geometry
def compo(mask, tag):
    return {"tag": tag, "n": int(mask.sum()),
            "share_mkt_r0>0_limit": float((mk[mask] > 0).mean()),
            "share_mkt_r0==0_at_market": float((mk[mask] == 0).mean()),
            "share_mkt_r0<0_stop_entry": float((mk[mask] < 0).mean()),
            "share_born_past_stop_mkt_r0<=-1": float((mk[mask] <= -1.0).mean()),
            "gross": float(g[mask].mean())}
R["composition"] = {
    "roster_all": compo(np.ones(N, bool), "every emission"),
    "roster_c0<=-0.15": compo(c0 <= -0.15, "the refused cohort on the roster"),
    "roster_c0>-0.15": compo(c0 > -0.15, "the kept cohort"),
}

json.dump(R, open("/tmp/d5/out/D5_08_VERIFY.json", "w"), indent=1, default=float)
print(json.dumps(R["pooled"], indent=1))
print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk in
                      ("n_adverse", "adverse_gross", "pct_of_adverse_loss_that_a_CANCEL_can_avoid")}
                  for k, v in part.items()}, indent=1))
print(json.dumps(R["composition"], indent=1))
print("saved")
