#!/usr/bin/env python3
"""F3 (6b) — is the obstacle-count effect a MECHANISM or a PROXY?

The ex-ante pass found the opposite of the folk theory: the MORE structural levels
sit between entry and target, the BETTER the trade does and the LESS it gives back,
monotonically, in train and again in test.  Every level type points the same way,
including moving averages and round numbers.  That uniformity is the signature of a
proxy, not a mechanism: if the prior day's high specifically caused rejections, then
PDH-in-path would be worse and an SMA-in-path would not.

This script tries to kill it three ways:
  1. STRATIFY on stop width (`risk_over_atr`).  A 2 R span that contains no levels
     may simply be a narrow span, and Lane 2 proved cost in R is a price quantity
     over the stop.
  2. STRATIFY on price extension (`close_position_in_lookback_range`,
     `dist_to_prior_high20_atr`).  "No level in the path" may just mean "price is
     outside the whole recent range", which the corpus already carries as a feature.
  3. Ask whether obstacle count adds anything BEYOND those features, by comparing
     the spread it produces inside their strata against the spread it produces raw.
"""
import gzip, json, pickle
from collections import defaultdict
from pathlib import Path
import numpy as np

TMP = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/f3")
CACHE = "/private/tmp/w21-puzzle-cache/rows_%s.pkl.gz"
OUT = Path(__file__).resolve().parent
FEATS = ["risk_over_atr", "close_position_in_lookback_range", "dist_to_prior_high20_atr",
         "dist_to_prior_low20_atr", "atr14_over_atr50", "risk_fraction_of_entry",
         "stop_distance_atr", "trigger_bar_range_atr"]


def boot(x, n=3000, seed=23):
    x = np.asarray(x, float)
    rng = np.random.default_rng(seed)
    mu = x[rng.integers(0, len(x), (n, len(x)))].mean(axis=1)
    return float(x.mean()), [float(np.percentile(mu, 2.5)), float(np.percentile(mu, 97.5))]


def main():
    d = pickle.load(gzip.open(TMP / "f3_exante_rows.pkl.gz", "rb"))
    rows = d["train"] + d["test"]
    seg = np.array(["train"] * len(d["train"]) + ["test"] * len(d["test"]))
    feat = {}
    for m in ["feb", "apr", "may", "jun", "jul"]:
        for r in pickle.load(gzip.open(CACHE % m, "rb")):
            feat[r["candidate_occurrence_key"]] = r
    X = {f: np.array([float(feat[r["k"]].get(f) or np.nan) for r in rows]) for f in FEATS}
    net = np.array([r["net"] for r in rows])
    gb = np.array([r["gb"] for r in rows])
    ns = np.array([r["n_strong"] for r in rows])
    fam = np.array([r["fam"] for r in rows])
    out = {"schema": "gtos.f3.control.v1", "n": len(rows),
           "raw_spread_none_vs_2plus_R": float(net[ns == 0].mean() - net[ns >= 2].mean())}

    # 1/2. stratify on each candidate confound
    out["stratified"] = {}
    for f in FEATS:
        v = X[f]
        ok = np.isfinite(v)
        if ok.sum() < 5000:
            continue
        q = np.quantile(v[ok], np.linspace(0, 1, 6))
        cells, wts = [], []
        detail = {}
        for a in range(5):
            hi = v <= q[a + 1] if a == 4 else v < q[a + 1]
            m = ok & (v >= q[a]) & hi
            A = net[m & (ns == 0)]; B = net[m & (ns >= 2)]
            if len(A) < 100 or len(B) < 100:
                continue
            cells.append(A.mean() - B.mean()); wts.append(len(A) + len(B))
            detail[f"q{a+1}"] = dict(n_none=len(A), n_2plus=len(B),
                                     none_mean_net_R=float(A.mean()),
                                     two_plus_mean_net_R=float(B.mean()),
                                     diff=float(A.mean() - B.mean()))
        if cells:
            out["stratified"][f] = dict(
                within_stratum_diff_R=float(np.average(cells, weights=wts)),
                n_strata=len(cells), cells=detail,
                correlation_with_n_strong=float(np.corrcoef(v[ok], ns[ok])[0, 1]))

    # how well do the corpus's own extension features separate the same thing?
    out["confound_profile_by_n_strong"] = {}
    for k in [0, 1, 2, 3, 4]:
        m = ns == k if k < 4 else ns >= 4
        out["confound_profile_by_n_strong"][str(k)] = {
            f: float(np.nanmean(X[f][m])) for f in FEATS}
        out["confound_profile_by_n_strong"][str(k)]["n"] = int(m.sum())
        out["confound_profile_by_n_strong"][str(k)]["mean_net_R"] = float(net[m].mean())

    # 3. within family AND within stop-width quintile simultaneously
    v = X["risk_over_atr"]; ok = np.isfinite(v)
    q = np.quantile(v[ok], np.linspace(0, 1, 4))
    cells, wts, det = [], [], {}
    for f in sorted(set(fam)):
        for a in range(3):
            hi = v <= q[a + 1] if a == 2 else v < q[a + 1]
            m = ok & (fam == f) & (v >= q[a]) & hi
            A = net[m & (ns == 0)]; B = net[m & (ns >= 2)]
            if len(A) < 80 or len(B) < 80:
                continue
            cells.append(A.mean() - B.mean()); wts.append(len(A) + len(B))
            det[f"{f}|q{a+1}"] = dict(n_none=len(A), n_2plus=len(B),
                                      diff=float(A.mean() - B.mean()))
    out["family_x_stopwidth"] = dict(
        n_cells=len(cells),
        weighted_diff_R=float(np.average(cells, weights=wts)) if cells else None,
        share_of_cells_same_sign=float(np.mean(np.array(cells) > 0)) if cells else None,
        cells=det)

    # test-segment only version of the headline, for the honest out-of-sample number
    te = seg == "test"
    A = net[te & (ns == 0)]; B = net[te & (ns >= 2)]
    ma, ca = boot(A); mb, cb = boot(B)
    out["test_only"] = dict(none_n=len(A), none_mean_net_R=ma, none_ci95=ca,
                            two_plus_n=len(B), two_plus_mean_net_R=mb, two_plus_ci95=cb,
                            diff=float(ma - mb))
    (OUT / "F3_CONTROL.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({"raw": out["raw_spread_none_vs_2plus_R"],
                      "stratified": {k: v["within_stratum_diff_R"]
                                     for k, v in out["stratified"].items()},
                      "corr": {k: v["correlation_with_n_strong"]
                               for k, v in out["stratified"].items()},
                      "family_x_stopwidth": out["family_x_stopwidth"]["weighted_diff_R"]},
                     indent=1))


if __name__ == "__main__":
    main()
