#!/usr/bin/env python3
"""B3 step 6 -- adversarial checks against this lane's own positive.

The A1 family's within-window selection term is positive and significant.  Its
no-fill share of picks tracks it almost perfectly, which is exactly what a
"skill" that is really just abstention would look like.  Three controls:

  C1  NOFILL_PICKER  -- zero model.  Pick any available candidate that will not
                        fill (lowest key among them); else the lowest key.  This
                        is the pure value of declining to transact, and it is an
                        ORACLE control (it uses the outcome), so it is an upper
                        bound, not a strategy.
  C2  FAR_LIMIT      -- zero model, one feature.  Rank by distance_to_limit_atr
                        descending: the limit least likely to fill.  Causally
                        clean and executable.
  C3  conditional    -- each arm's selection term restricted to the windows where
                        its pick ACTUALLY FILLED.  If the term vanishes there,
                        the arm has no skill beyond abstention.
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
T0 = time.time()


def log(**kw):
    print(json.dumps({"t": round(time.time() - T0, 1), **kw}, sort_keys=True), flush=True)


def main() -> None:
    with (L.OUT / "dataset.pkl").open("rb") as fh:
        data = pickle.load(fh)
    meta, frame = data["meta"], data["frame"]
    n = len(meta)
    keypos = {m["key"]: i for i, m in enumerate(meta)}
    idx_all = [i for i, m in enumerate(meta) if m["month"] in L.MONTHS]

    arrays = {}
    if LANE3.exists():
        with gzip.open(LANE3, "rb") as fh:
            sealed = pickle.load(fh)
        a = np.full(n, np.nan)
        for k, v in sealed.items():
            j = keypos.get(k)
            if j is not None:
                a[j] = v
        arrays["SHIPPED_SEALED"] = a
    for stage in L.complete_stages():
        p = L.OUT / f"preds_{stage}.npz"
        if p.exists():
            blob = np.load(p)
            for arm in blob.files:
                if np.isfinite(blob[arm]).sum() >= 100000:
                    arrays[arm] = blob[arm]

    # C1 -- the abstention ORACLE (uses the outcome; an upper bound, not a rule)
    c1 = np.full(n, np.nan)
    for i in idx_all:
        c1[i] = 1.0 if (meta[i]["res"] and meta[i]["net"] == 0.0) else 0.0
    arrays["C1_NOFILL_PICKER_ORACLE"] = c1
    # C2 -- one causally clean feature, no model
    dist = frame["distance_to_limit_atr"].to_numpy(dtype=float)
    c2 = np.full(n, np.nan)
    for i in idx_all:
        c2[i] = dist[i] if np.isfinite(dist[i]) else -1.0
    arrays["C2_FAR_LIMIT"] = c2

    out = {}
    for arm, arr in sorted(arrays.items()):
        windows, _sel = L.run_windows(meta, idx_all, arr)
        allsel = [(w["pick_actual"] - w["mean_actual"], w["trading_day"]) for w in windows
                  if w["pick_actual"] is not None and w["mean_actual"] is not None]
        filled = [(a, d) for (a, d), w in zip(allsel, [w for w in windows
                  if w["pick_actual"] is not None and w["mean_actual"] is not None])
                  if w["pick_actual"] != 0.0]
        nofill = [(a, d) for (a, d), w in zip(allsel, [w for w in windows
                  if w["pick_actual"] is not None and w["mean_actual"] is not None])
                  if w["pick_actual"] == 0.0]
        pool_mean = float(np.mean([w["mean_actual"] for w in windows
                                   if w["mean_actual"] is not None]))
        share_nf = len(nofill) / max(1, len(allsel))
        out[arm] = {
            "n_windows": len(allsel),
            "selection_term_all": L.boot_day([a for a, _ in allsel], [d for _, d in allsel], 4000),
            "selection_term_on_FILLED_picks": (
                L.boot_day([a for a, _ in filled], [d for _, d in filled], 4000) if filled else None),
            "selection_term_on_NOFILL_picks": (
                L.boot_day([a for a, _ in nofill], [d for _, d in nofill], 2000) if nofill else None),
            "share_of_picks_that_never_filled": round(share_nf, 4),
            "pool_mean_r": round(pool_mean, 5),
            "abstention_accounting": {
                "predicted_term_if_ONLY_abstention": round(share_nf * (0.0 - pool_mean), 5),
                "note": "a no-fill books exactly 0.0 in a pool whose mean is negative, so picking "
                        "one is worth (0 - pool_mean) with no skill of any kind"},
        }
        term = out[arm]["selection_term_all"]["point"]
        pred = out[arm]["abstention_accounting"]["predicted_term_if_ONLY_abstention"]
        out[arm]["abstention_accounting"]["share_of_term_explained"] = (
            round(pred / term, 4) if term else None)
        fl = out[arm]["selection_term_on_FILLED_picks"]
        log(arm=arm, term=round(term, 5), abst_pred=pred,
            explained=out[arm]["abstention_accounting"]["share_of_term_explained"],
            filled_term=round(fl["point"], 5) if fl else None,
            filled_p=fl["p_two_sided_sign"] if fl else None, nf=share_nf)
    (L.OUT / "ADVERSARIAL_V1.json").write_text(json.dumps(out, indent=1, sort_keys=True, default=float))
    log(stage="DONE", arms=len(out))


if __name__ == "__main__":
    main()
