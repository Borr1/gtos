#!/usr/bin/env python3
"""B1 — the adversarial test the LIMIT result has to survive: the ENTRY leg.

The adjudication declined to charge the entry leg (RECON §2.2, §4.0) on the argument that it is a
SPREAD-MODEL quantity which cancels in the fair-value edge:

    "if the true entry-side quote is D worse, the true fill is D worse AND the true spread_r --
     hence the fair-value null -- is D more negative"

Measured correlation with the spread-model error was +0.753, on the MARKET arm. **That argument was
never tested on LIMIT, and the LIMIT arm's entry optimism is 3.5x MARKET's**, so it cannot be
inherited. It also has a mechanism MARKET does not: a resting LIMIT is booked AT its level, and the
engine decides the level was touched using a MODELLED ask (bid bar + modelled spread). If the model
understates the spread, the engine manufactures a fill the tape never offered.

Exact algebra, per trade (long; short symmetric):

    edge_booked = booked_gross + spread_r_model                (Lane 1's identity, exact)
    edge_true   = (booked_gross - entry_opt_r) + spread_r_true
    => correction = edge_true - edge_booked
                  = -entry_opt_r + (spread_r_true - spread_r_model)

If the adjudication's cancellation argument holds, this correction is ~0. If it does not, it is a
charge nobody has taken. Measured here for BOTH arms on identical code.

Writes B1_ENTRY_RESIDUAL.json.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

OUT = "/Users/borr/.claude/jobs/adb9e69b/tmp/b1"
SEED = 20260812


def boot(v, days, B=4000, seed=SEED):
    rng = np.random.default_rng(seed)
    v = np.asarray(v, float)
    days = np.asarray(days)
    ok = ~np.isnan(v)
    v, days = v[ok], days[ok]
    ud = pd.unique(days)
    idx = {d: np.where(days == d)[0] for d in ud}
    out = np.empty(B)
    for b in range(B):
        pick = rng.choice(len(ud), len(ud), replace=True)
        sel = np.concatenate([idx[ud[p]] for p in pick])
        out[b] = v[sel].mean()
    return ([float(np.quantile(out, .025)), float(np.quantile(out, .975))],
            float(out.std(ddof=1)))


R = {"schema": "b1_entry_residual_v1",
     "identity": "correction = -entry_opt_r + (spread_r_true - spread_r_model)",
     "note": "+ve correction improves the edge; -ve is an uncharged cost"}

for arm, tag in (("MARKET", "ctrlB_lg_market"), ("LIMIT", "limit")):
    D = pd.read_pickle(f"{OUT}/legs_{tag}.pkl").copy()
    D = D[D.spread_r_row.notna() & D.true_spread_r.notna() & D.entry_opt_r.notna()]
    D["spread_err"] = D.true_spread_r - D.spread_r_row
    D["correction"] = -D.entry_opt_r + D.spread_err
    ci_c, se_c = boot(D.correction.values, D.day.values)
    ci_e, se_e = boot(D.entry_opt_r.values, D.day.values)
    ci_s, se_s = boot(D.spread_err.values, D.day.values)
    R[arm] = {
        "n": int(len(D)),
        "entry_opt_r": dict(mean=float(D.entry_opt_r.mean()), median=float(D.entry_opt_r.median()),
                            CI95=ci_e, se=se_e,
                            frac_adverse=float((D.entry_opt_r > 1e-9).mean())),
        "spread_model_error_true_minus_model": dict(
            mean=float(D.spread_err.mean()), median=float(D.spread_err.median()),
            CI95=ci_s, se=se_s,
            model_mean=float(D.spread_r_row.mean()), true_mean=float(D.true_spread_r.mean())),
        "correction_to_edge": dict(mean=float(D.correction.mean()),
                                   median=float(D.correction.median()),
                                   CI95=ci_c, se=se_c),
        "correlation_entry_opt_vs_spread_err": float(D.entry_opt_r.corr(D.spread_err)),
        "cancellation_holds": bool(abs(float(D.correction.mean())) < 0.005),
    }
    # how much of the entry optimism is explained by the spread-model error
    R[arm]["share_of_entry_opt_explained_by_spread_error"] = (
        float(D.spread_err.mean() / D.entry_opt_r.mean()) if D.entry_opt_r.mean() else None)

# ---- the LIMIT fill-feasibility question, stated as a count ----
D = pd.read_pickle(f"{OUT}/legs_limit.pkl")
D = D[D.entry_opt_r.notna()]
R["LIMIT_fill_feasibility"] = {
    "definition": "entry_opt_r > 0 means the true entry-side quote at the booked fill instant was "
                  "WORSE than the level the engine booked -- i.e. the resting limit was not "
                  "actually available at that price at that instant",
    "frac_rows_infeasible_at_booked_instant": float((D.entry_opt_r > 1e-9).mean()),
    "mean_when_infeasible": float(D[D.entry_opt_r > 1e-9].entry_opt_r.mean()),
    "p95_when_infeasible": float(D[D.entry_opt_r > 1e-9].entry_opt_r.quantile(.95)),
}
Dm = pd.read_pickle(f"{OUT}/legs_ctrlB_lg_market.pkl")
Dm = Dm[Dm.entry_opt_r.notna()]
R["MARKET_fill_feasibility"] = {
    "frac_rows_infeasible_at_booked_instant": float((Dm.entry_opt_r > 1e-9).mean()),
    "mean_when_infeasible": float(Dm[Dm.entry_opt_r > 1e-9].entry_opt_r.mean()),
}

json.dump(R, open(f"{OUT}/B1_ENTRY_RESIDUAL.json", "w"), indent=1)
print(json.dumps(R, indent=1))
