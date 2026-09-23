#!/usr/bin/env python3
"""Adversarial controls on the Stage-L result.

B3's most important finding was that a ZERO-MODEL, single-feature ranker
(`distance_to_limit_atr` descending) beat every fitted arm it built.  Any claim
that a fitted model carries information must therefore be measured against the
raw features it was fitted on, on the identical windows and the identical
statistic.  This runs:

  C-ZERO   every one of the 29 numeric features, and its negation, as a ranking
           statistic, scored by within-window Spearman against realized net R
  C-EARLY  the same statistic split into the first and second half of each
           trading day -- the applicable remnant of T2, since no feature in the
           frozen 43 is a same-day aggregate and B6's construction has no
           analogue here
  C-OT     the statistic computed separately for MARKET and LIMIT candidates,
           because B2 established that the book is monotone in MARKET-top share
           and any ranker that merely sorts order types will look skilled
  C-PERM   day-block permutation null (declared NECESSARY AND NOT SUFFICIENT)
"""
from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f2_lib as L
from f2_stageL import ww_rho, paired_ww

WF = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/f2/wf")
OUTD = Path(__file__).resolve().parent / "receipts"


def main(variant="base"):
    meta, X, names_col, tgt, filled, ded, info = L.build_dataset()
    import pickle
    with (L.B3OUT / "dataset.pkl").open("rb") as fh:
        frame = pickle.load(fh)["frame"]
    Z = np.load(WF / f"preds_{variant}.npz", allow_pickle=True)
    preds = Z["preds"].astype(np.float64)
    names = list(Z["names"]); idx = {n: k for k, n in enumerate(names)}
    scored_days = set(str(d) for d in Z["scored"])

    res = np.asarray([m["res"] for m in meta], dtype=bool)
    both = res & filled
    rows = np.asarray([i for i, m in enumerate(meta)
                       if m["cday"] in scored_days and both[i]], dtype=np.int64)
    tnr = tgt["tnr"]
    rep = {"variant": variant, "prereg_sha256": L.PREREG_SHA, "n_rows": int(len(rows))}

    # ---------------- C-ZERO: single raw features as rankers -----------------
    zero = {}
    for c in L.NUM0:
        v = frame[c].to_numpy(dtype=np.float64)
        if not np.isfinite(v[rows]).any() or len(np.unique(v[rows][np.isfinite(v[rows])])) < 3:
            continue
        r, d, _ = ww_rho(meta, rows, v, tnr)
        if not r:
            continue
        b = L.boot_day(r, d)
        zero[c] = {"point": b["point"], "ci95_lo": b["ci95_lo"], "ci95_hi": b["ci95_hi"],
                   "p": b["p_two_sided_sign"], "windows": len(r)}
    rep["C_ZERO_single_feature_transfer_to_net_r"] = dict(
        sorted(zero.items(), key=lambda kv: -abs(kv[1]["point"])))

    # the fitted arms on the same windows
    fitted = {}
    for nm in ("tnr_B", "mfe_B", "mae_B", "ratio_B", "tmfe_B", "mfe_capped_B", "fill"):
        if nm not in idx:
            continue
        r, d, _ = ww_rho(meta, rows, preds[:, idx[nm]], tnr)
        if r:
            b = L.boot_day(r, d)
            fitted[nm] = {"point": b["point"], "ci95_lo": b["ci95_lo"],
                          "ci95_hi": b["ci95_hi"], "p": b["p_two_sided_sign"]}
    rep["FITTED_transfer_to_net_r"] = fitted

    best_zero = max(zero.items(), key=lambda kv: kv[1]["point"]) if zero else None
    rep["VERDICT_best_positive_zero_model"] = (
        {"feature": best_zero[0], **best_zero[1]} if best_zero else None)

    # paired: does the fitted MAE model beat its best single-feature rival?
    if best_zero:
        v = frame[best_zero[0]].to_numpy(dtype=np.float64)
        for nm in ("mae_B", "tnr_B"):
            if nm not in idx:
                continue
            dfs, dys = paired_ww(meta, rows, preds[:, idx[nm]], v, tnr)
            rep[f"PAIRED_{nm}_minus_best_zero_model"] = L.boot_day(dfs, dys)

    # ---------------- C-EARLY: first vs second half of the day ---------------
    minute = {}
    for i in rows:
        minute[i] = str(meta[i]["t0"])
    by_day = defaultdict(list)
    for i in rows:
        by_day[meta[i]["day"]].append(i)
    early, late = [], []
    for d, ii in by_day.items():
        ii = sorted(ii, key=lambda x: minute[x])
        cut = len(ii) // 2
        early += ii[:cut]; late += ii[cut:]
    early = np.asarray(early, dtype=np.int64); late = np.asarray(late, dtype=np.int64)
    half = {}
    for nm in ("tnr_B", "mfe_B", "mae_B"):
        if nm not in idx:
            continue
        half[nm] = {}
        for tag, sub in (("early", early), ("late", late)):
            r, d, _ = ww_rho(meta, sub, preds[:, idx[nm]], tnr)
            half[nm][tag] = L.boot_day(r, d) if r else None
    rep["C_EARLY_intraday_split"] = half

    # ---------------- C-OT: by order type ------------------------------------
    ot = np.asarray([m["ot"] for m in meta], dtype=object)
    byot = {}
    for tag in ("MARKET", "LIMIT"):
        sub = rows[ot[rows] == tag]
        byot[tag] = {"n": int(len(sub))}
        for nm in ("tnr_B", "mfe_B", "mae_B"):
            if nm not in idx:
                continue
            r, d, _ = ww_rho(meta, sub, preds[:, idx[nm]], tnr)
            byot[tag][nm] = L.boot_day(r, d) if r else None
    rep["C_OT_by_order_type"] = byot

    # ---------------- C-PERM: day-block permutation --------------------------
    rng = np.random.default_rng(L.SEED)
    days = sorted({meta[i]["day"] for i in rows})
    rows_by_day = defaultdict(list)
    for i in rows:
        rows_by_day[meta[i]["day"]].append(i)
    perm = {}
    for nm in ("mae_B", "mfe_B", "tnr_B"):
        if nm not in idx:
            continue
        draws = []
        for _ in range(200):
            shuffled = list(days); rng.shuffle(shuffled)
            tnr_p = tnr.copy()
            for a, b in zip(days, shuffled):
                ra = np.asarray(rows_by_day[a]); rb = np.asarray(rows_by_day[b])
                k = min(len(ra), len(rb))
                tnr_p[ra[:k]] = tnr[rb[:k]]
            r, d, _ = ww_rho(meta, rows, preds[:, idx[nm]], tnr_p)
            if r:
                draws.append(float(np.mean(r)))
        obs = fitted[nm]["point"]
        perm[nm] = {"observed": obs, "null_mean": float(np.mean(draws)),
                    "null_sd": float(np.std(draws)),
                    "p_one_sided_ge": float((np.asarray(draws) >= obs).mean()),
                    "p_one_sided_le": float((np.asarray(draws) <= obs).mean()),
                    "draws": len(draws),
                    "NOTE": "necessary, not sufficient -- a permutation null cannot "
                            "see a leak present in every permutation (PREREG T4)"}
    rep["C_PERM_day_block"] = perm

    OUTD.mkdir(parents=True, exist_ok=True)
    (OUTD / f"L2_CONTROLS_{variant}.json").write_text(json.dumps(rep, indent=1))
    top = list(rep["C_ZERO_single_feature_transfer_to_net_r"].items())[:10]
    print("TOP SINGLE-FEATURE RANKERS (within-window transfer to net R):")
    for k, v in top:
        print(f"  {k:<34}{v['point']:+.5f}  [{v['ci95_lo']:+.5f},{v['ci95_hi']:+.5f}]  p={v['p']:.4f}")
    print("\nFITTED ARMS, same windows:")
    for k, v in fitted.items():
        print(f"  {k:<34}{v['point']:+.5f}  [{v['ci95_lo']:+.5f},{v['ci95_hi']:+.5f}]  p={v['p']:.4f}")
    print("\nBEST POSITIVE ZERO-MODEL:", json.dumps(rep["VERDICT_best_positive_zero_model"]))
    for k in rep:
        if k.startswith("PAIRED_"):
            v = rep[k]
            print(f"  {k}: {v['point']:+.5f} [{v['ci95_lo']:+.5f},{v['ci95_hi']:+.5f}] p={v['p_two_sided_sign']:.4f}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "base")
