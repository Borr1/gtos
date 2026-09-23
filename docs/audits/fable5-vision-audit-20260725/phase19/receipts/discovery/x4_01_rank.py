#!/usr/bin/env python3
"""x4 step 1 — rank every intra-bar feature against outcome, at the SAME cohort definition
l3 used (max |d| = 0.152 is the ceiling to beat), plus the honest cohorts and the economics."""
from __future__ import annotations
import json, os, sys
import numpy as np
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import x4_lib as X

recs = X.load_joined()
O = X.outcomes(recs)
names = X.feature_names(recs)
days = np.array([r["_day"] for r in recs])
res = {"n_joined": len(recs), "n_features": len(names)}

take = O["takeable"]
# --- cohort A: l3's BRIEFED cohorts on takeable (ge_target vs full_stop)
A_pos = take & (O["band"] == "ge_target")
A_neg = take & (O["band"] == "full_stop")
# --- cohort B: HONEST first-touch cohorts on takeable
B_pos = take & (O["hon"] == "target")
B_neg = take & (O["hon"] == "stop")
res["cohorts"] = {"takeable_n": int(take.sum()),
                  "A_briefed_pos": int(A_pos.sum()), "A_briefed_neg": int(A_neg.sum()),
                  "B_honest_pos": int(B_pos.sum()), "B_honest_neg": int(B_neg.sum())}
print("takeable", take.sum(), "| A", A_pos.sum(), A_neg.sum(), "| B", B_pos.sum(), B_neg.sum())

# split halves: odd / even calendar day
dnum = np.array([int(d[-2:]) for d in days])
H1 = (dnum % 2 == 1); H2 = ~H1

table = []
for nm in names:
    x = X.col(recs, nm)
    row = {"feature": nm,
           "cls": "CONFIRM" if nm.startswith(X.CONFIRM_PREFIX) else "PRE",
           "cov": float(np.isfinite(x[take]).mean())}
    dA = X.cohens_d(x[A_pos], x[A_neg]); aA = X.auc(x[A_pos], x[A_neg])
    dB = X.cohens_d(x[B_pos], x[B_neg]); aB = X.auc(x[B_pos], x[B_neg])
    row["d_briefed"] = None if not np.isfinite(dA) else round(float(dA), 4)
    row["auc_briefed"] = None if not np.isfinite(aA) else round(float(aA), 4)
    row["d_honest"] = None if not np.isfinite(dB) else round(float(dB), 4)
    row["auc_honest"] = None if not np.isfinite(aB) else round(float(aB), 4)
    # IV against honest binary on the takeable resolved population
    resolved = B_pos | B_neg
    yv = B_pos[resolved].astype(float)
    row["iv_honest"] = None if not np.isfinite(X.iv_deciles(x[resolved], yv)) else \
        round(float(X.iv_deciles(x[resolved], yv)), 4)
    # split-half sign stability of d_honest
    d1 = X.cohens_d(x[B_pos & H1], x[B_neg & H1])
    d2 = X.cohens_d(x[B_pos & H2], x[B_neg & H2])
    row["d_honest_h1"] = None if not np.isfinite(d1) else round(float(d1), 4)
    row["d_honest_h2"] = None if not np.isfinite(d2) else round(float(d2), 4)
    row["sign_stable"] = bool(np.isfinite(d1) and np.isfinite(d2) and (d1 > 0) == (d2 > 0)
                              and np.isfinite(dB))
    # ECONOMICS: spearman-style monotone check on decile means of honest R over takeable
    m = take & np.isfinite(x)
    if m.sum() > 2000:
        xv, yv2 = x[m], O["honr"][m]
        qs = np.unique(np.quantile(xv, np.linspace(0, 1, 11)))
        if len(qs) >= 4:
            idx = np.clip(np.searchsorted(qs, xv, side="right") - 1, 0, len(qs) - 2)
            dm = [float(yv2[idx == b].mean()) for b in range(len(qs) - 1) if (idx == b).sum() > 30]
            row["decile_means_honr"] = [round(v, 5) for v in dm]
            row["decile_spread"] = round(max(dm) - min(dm), 5) if dm else None
            if len(dm) >= 5:
                rk = np.arange(len(dm))
                row["decile_rho"] = round(float(np.corrcoef(rk, dm)[0, 1]), 4)
    table.append(row)

table.sort(key=lambda r: -abs(r["d_honest"] or 0))
res["table"] = table
with open(os.path.join(D, "X4_RANK_V1.json"), "w") as f:
    json.dump(res, f, indent=1)

print("\n%-28s %-7s %7s %7s %7s %7s %7s %6s" % ("feature", "cls", "d_brief", "d_hon", "auc_hon",
                                                "iv_hon", "dec_rho", "stab"))
for r in table[:34]:
    print("%-28s %-7s %7s %7s %7s %7s %7s %6s" % (
        r["feature"], r["cls"], r["d_briefed"], r["d_honest"], r["auc_honest"],
        r["iv_honest"], r.get("decile_rho"), r["sign_stable"]))
print("\nPRE-only top 20 by |d_honest|:")
for r in [t for t in table if t["cls"] == "PRE"][:20]:
    print("  %-28s d=%7s auc=%7s iv=%7s rho=%7s spread=%8s stab=%s" % (
        r["feature"], r["d_honest"], r["auc_honest"], r["iv_honest"],
        r.get("decile_rho"), r.get("decile_spread"), r["sign_stable"]))
