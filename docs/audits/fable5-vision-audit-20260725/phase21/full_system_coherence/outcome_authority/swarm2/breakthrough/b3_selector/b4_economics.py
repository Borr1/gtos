#!/usr/bin/env python3
"""B3 step 4 -- scale-matched economics, the R2 cap factorial, and R3 bases.

The shipped 0.10 floor is NOT scale-invariant: an arm whose statistic is
P(fill) * E[net|fill] lives on a different scale from one predicting E[net]
directly, so "book R under the shipped policy" is not an arm comparison.  The
comparable rules are:

  * TOP-N       : trade the N decision windows with the highest statistic
                  (N = the shipped rule's own 290, and 100 / 50 / 600)
  * MATCHED     : sweep the floor until the trade count matches the shipped 290
  * CAP         : PREREG's R2 grid, applied on each arm's own quantile scale

R3 is reported as two bases side by side (actual, worst-case), never merged.
"""
from __future__ import annotations

import gzip
import json
import pickle
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

import b3_lib as L

LANE3 = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/lane3/out/preds_daily.pkl.gz")
CAP_Q = [None, 0.99, 0.98, 0.95, 0.90]      # quantile caps on the arm's own scale
TOPN = [50, 100, 290, 600, 1230]
T0 = time.time()


def log(**kw):
    print(json.dumps({"t": round(time.time() - T0, 1), **kw}, sort_keys=True), flush=True)


def topn_book(windows, n, *, market_only=False, cap_q=None):
    pool = [w for w in windows if w["top_pred"] is not None]
    if market_only:
        pool = [w for w in pool if w["top_order_type"] == "MARKET"]
    if cap_q is not None and pool:
        cut = float(np.quantile([w["top_pred"] for w in pool], cap_q))
        pool = [w for w in pool if w["top_pred"] <= cut]
    pool = sorted(pool, key=lambda w: -w["top_pred"])[:n]
    act = [w["pick_actual"] for w in pool if w["pick_actual"] is not None]
    wc = [w["pick_wc"] for w in pool]
    days = [w["trading_day"] for w in pool if w["pick_actual"] is not None]
    by_day = defaultdict(float)
    for w in pool:
        if w["pick_actual"] is not None:
            by_day[w["trading_day"]] += w["pick_actual"]
    return {"n_windows": len(pool), "n_resolved": len(act),
            "actual_net_r": round(float(np.sum(act)), 4) if act else 0.0,
            "worst_case_net_r": round(float(np.sum(wc)), 4) if wc else 0.0,
            "mean_r": float(np.mean(act)) if act else None,
            "positive_days": sum(1 for v in by_day.values() if v > 0),
            "negative_days": sum(1 for v in by_day.values() if v < 0),
            "boot": L.boot_day(act, days, 1000) if act else None}


def main() -> None:
    with (L.OUT / "dataset.pkl").open("rb") as fh:
        data = pickle.load(fh)
    meta = data["meta"]
    keypos = {m["key"]: i for i, m in enumerate(meta)}
    n = len(meta)
    midx = defaultdict(list)
    for i, m in enumerate(meta):
        if m["month"] in L.MONTHS:
            midx[m["month"]].append(i)
    idx_all = [i for mm in L.MONTHS for i in midx[mm]]

    arrays = {}
    if LANE3.exists():
        with gzip.open(LANE3, "rb") as fh:
            sealed = pickle.load(fh)
        arr = np.full(n, np.nan)
        for k, v in sealed.items():
            j = keypos.get(k)
            if j is not None:
                arr[j] = v
        arrays["SHIPPED_SEALED"] = arr
    for stage in L.complete_stages():
        path = L.OUT / f"preds_{stage}.npz"
        if not path.exists():
            continue
        blob = np.load(path)
        for arm in blob.files:
            a = blob[arm]
            if np.isfinite(a).sum() >= 100000:  # stage already gated on 100 days
                arrays[arm] = a
    # derived diagnostic controls: the pure fill probability, recovered exactly
    # from the composed arms (A2 = pfill_ridge * A1, A5 = pfill_hgb * A4)
    for name, num, den in (("PFILL_RIDGE", "A2", "A1"), ("PFILL_HGB", "A5", "A4")):
        if num in arrays and den in arrays:
            with np.errstate(divide="ignore", invalid="ignore"):
                r = arrays[num] / arrays[den]
            r[~np.isfinite(r)] = np.nan
            arrays[name] = r

    out = {}
    for arm, arr in sorted(arrays.items()):
        windows, selected = L.run_windows(meta, idx_all, arr)
        rec = {"n_windows_ranked": len(windows),
               "shipped_policy": L.book(meta, selected),
               "topn": {}, "topn_market_only": {}, "cap_factorial": {},
               "by_month_topn290": {}}
        for k in TOPN:
            rec["topn"][str(k)] = topn_book(windows, k)
            rec["topn_market_only"][str(k)] = topn_book(windows, k, market_only=True)
        for q in CAP_Q:
            rec["cap_factorial"][str(q)] = topn_book(windows, 290, cap_q=q)
        for mm in L.MONTHS:
            sub = [w for w in windows if w["month"] == mm]
            rec["by_month_topn290"][mm] = topn_book(sub, max(1, round(290 * len(sub) / max(1, len(windows)))))
        out[arm] = rec
        log(arm=arm, top290=rec["topn"]["290"]["actual_net_r"],
            top290_mkt=rec["topn_market_only"]["290"]["actual_net_r"],
            shipped=rec["shipped_policy"]["actual_net_r"])
    (L.OUT / "ECONOMICS_V1.json").write_text(json.dumps(out, indent=1, sort_keys=True, default=float))
    log(stage="DONE", arms=sorted(out))


if __name__ == "__main__":
    main()
