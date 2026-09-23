#!/usr/bin/env python3
"""Stage L -- which label carries information?

Two statistics per label, both out of sample, both on the frozen 43 features,
identical folds, identical estimator:

  SELF      within-decision-window Spearman between the label's prediction and
            the label's own truth.  "Is MFE more predictable than terminal R?"
  TRANSFER  within-decision-window Spearman between the label's prediction and
            REALIZED terminal_net_r.  "Does a model of MFE rank the economics
            better than a model of the economics does?"

Within-window is the decision-relevant form: the funnel ranks INSIDE a window,
so pooled correlation over-credits between-window variation the selector can
never act on.  Both are reported anyway.

Population `_B` -- resolved AND walker-filled -- is the exactly matched
head-to-head. The unmatched F population is reported alongside to price the
censoring gain.
"""
from __future__ import annotations

import json
import math
import pickle
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f2_lib as L

WF = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/f2/wf")
OUTD = Path(__file__).resolve().parent / "receipts"


def ww_rho(meta, rows, pred, truth, min_n=5):
    """Per-window Spearman. Returns (rho list, day list, n list)."""
    by = defaultdict(list)
    for i in rows:
        p, t = pred[i], truth[i]
        if math.isfinite(p) and math.isfinite(t):
            by[meta[i]["win"]].append((p, t, meta[i]["day"]))
    rhos, days, ns = [], [], []
    for win, vals in by.items():
        if len(vals) < min_n:
            continue
        a = np.asarray([v[0] for v in vals]); b = np.asarray([v[1] for v in vals])
        if len(np.unique(a)) < 2 or len(np.unique(b)) < 2:
            continue
        ra, rb = L._rank(a), L._rank(b)
        ra = ra - ra.mean(); rb = rb - rb.mean()
        den = math.sqrt(float((ra ** 2).sum()) * float((rb ** 2).sum()))
        if den <= 0:
            continue
        rhos.append(float((ra * rb).sum() / den))
        days.append(vals[0][2]); ns.append(len(vals))
    return rhos, days, ns


def paired_ww(meta, rows, predA, predB, truth, min_n=5):
    """Paired per-window Spearman difference (A minus B) against a common truth."""
    by = defaultdict(list)
    for i in rows:
        a, b, t = predA[i], predB[i], truth[i]
        if math.isfinite(a) and math.isfinite(b) and math.isfinite(t):
            by[meta[i]["win"]].append((a, b, t, meta[i]["day"]))
    diffs, days = [], []
    for win, vals in by.items():
        if len(vals) < min_n:
            continue
        A = np.asarray([v[0] for v in vals]); B = np.asarray([v[1] for v in vals])
        T = np.asarray([v[2] for v in vals])
        if len(np.unique(T)) < 2:
            continue
        out = []
        for P in (A, B):
            if len(np.unique(P)) < 2:
                out.append(np.nan); continue
            rp, rt = L._rank(P), L._rank(T)
            rp = rp - rp.mean(); rt = rt - rt.mean()
            den = math.sqrt(float((rp ** 2).sum()) * float((rt ** 2).sum()))
            out.append(float((rp * rt).sum() / den) if den > 0 else np.nan)
        if not all(math.isfinite(v) for v in out):
            continue
        diffs.append(out[0] - out[1]); days.append(vals[0][3])
    return diffs, days


def main(variant="base"):
    meta, X, names_col, tgt, filled, ded, info = L.build_dataset()
    Z = np.load(WF / f"preds_{variant}.npz", allow_pickle=True)
    preds = Z["preds"].astype(np.float64)
    names = list(Z["names"])
    scored_days = set(str(d) for d in Z["scored"])
    idx = {nm: k for k, nm in enumerate(names)}

    res = np.asarray([m["res"] for m in meta], dtype=bool)
    both = res & filled
    rows_scored = np.asarray([i for i, m in enumerate(meta)
                              if m["cday"] in scored_days], dtype=np.int64)
    tnr_truth = tgt["tnr"]

    truths = {"tnr": tgt["tnr"], "mfe": tgt["mfe"], "mae": tgt["mae"],
              "ratio": tgt["ratio"], "tmfe": tgt["tmfe"],
              "mfe_capped": tgt["mfe_capped"]}
    for k in L.LADDER:
        truths[f"pol_{k}"] = tgt[f"pol_{k}"]
    truths["fill"] = np.where(res, filled.astype(float), np.nan)

    rep = {"variant": variant, "prereg_sha256": L.PREREG_SHA,
           "n_scored_rows": int(len(rows_scored)),
           "populations": {"resolved": int(res.sum()), "walker_filled": int(filled.sum()),
                           "both_matched": int(both.sum()),
                           "filled_but_sealed_censored": int((filled & ~res).sum())},
           "labels": {}}

    for nm in names:
        base = nm[:-2] if nm.endswith("_B") else nm
        if base not in truths:
            continue
        k = idx[nm]
        pred = preds[:, k]
        pop = both if nm.endswith("_B") else (res if base in ("tnr", "fill") else filled)
        rows = rows_scored[pop[rows_scored]]
        tr = truths[base]
        ok = rows[np.isfinite(pred[rows]) & np.isfinite(tr[rows])]
        if len(ok) < 100:
            continue
        sr, sd_, sn = ww_rho(meta, ok, pred, tr)
        # economic transfer: the same prediction, scored against realized net R
        rows_t = ok[np.isfinite(tnr_truth[ok])]
        tr_r, tr_d, _ = ww_rho(meta, rows_t, pred, tnr_truth)
        gm = float(np.nanmean(tr[ok]))
        rep["labels"][nm] = {
            "population": ("B" if nm.endswith("_B") else
                           ("R" if base in ("tnr", "fill") else "F")),
            "n_scored": int(len(ok)),
            "truth_mean": gm, "truth_sd": float(np.nanstd(tr[ok])),
            "truth_distinct_values": int(len(np.unique(np.round(tr[ok], 6)))),
            "pooled_spearman": L.spearman(pred[ok], tr[ok]),
            "pooled_pearson": L.pearson(pred[ok], tr[ok]),
            "oos_r2_vs_pooled_mean": L.r2_oos(tr[ok], pred[ok], gm),
            "within_window_self": (L.boot_day(sr, sd_) if sr else None),
            "within_window_windows": len(sr),
            "within_window_mean_size": float(np.mean(sn)) if sn else None,
            "within_window_transfer_to_net_r": (L.boot_day(tr_r, tr_d) if tr_r else None),
        }
        print(json.dumps({nm: {kk: vv for kk, vv in rep["labels"][nm].items()
                               if kk in ("n_scored", "truth_distinct_values",
                                         "pooled_spearman", "oos_r2_vs_pooled_mean")}}),
              flush=True)

    # ---- the declared head-to-head: G1 -------------------------------------
    rows_B = rows_scored[both[rows_scored]]
    h2h = {}
    for challenger in ("mfe_B", "mae_B", "ratio_B", "tmfe_B", "mfe_capped_B"):
        if challenger not in idx:
            continue
        d, dd = paired_ww(meta, rows_B, preds[:, idx[challenger]],
                          preds[:, idx["tnr_B"]], tnr_truth)
        h2h[f"{challenger}_minus_tnr_B__transfer_to_net_r"] = L.boot_day(d, dd)
    rep["G1_head_to_head_matched_population"] = h2h

    # self-predictability difference, each label against terminal_net_r's own
    rep["G1_self_predictability"] = {
        nm: rep["labels"][nm]["within_window_self"]["point"]
        for nm in rep["labels"] if nm.endswith("_B") and rep["labels"][nm]["within_window_self"]}

    OUTD.mkdir(parents=True, exist_ok=True)
    (OUTD / f"L1_LABEL_INFORMATION_{variant}.json").write_text(json.dumps(rep, indent=1))
    print(json.dumps(rep["G1_self_predictability"], indent=1))
    print(json.dumps({k: (v and {"point": round(v["point"], 5),
                                 "ci": [round(v["ci95_lo"], 5), round(v["ci95_hi"], 5)],
                                 "p": v["p_two_sided_sign"]})
                      for k, v in h2h.items()}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "base")
