#!/usr/bin/env python3
"""B3 step 3 -- evaluate every completed arm under PREREG_V1's metrics.

Also validates the instrument: replaying Lane 3's sealed daily predictions
through this funnel must reproduce the sealed dispositions and books exactly.

Writes one JSON per arm (resumable) plus EVAL_V1.json.
"""
from __future__ import annotations

import gzip
import json
import pickle
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

import b3_lib as L

LANE3 = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/lane3/out/preds_daily.pkl.gz")
T0 = time.time()


def log(**kw):
    print(json.dumps({"t": round(time.time() - T0, 1), **kw}, sort_keys=True), flush=True)


def month_idx(meta):
    out = defaultdict(list)
    for i, m in enumerate(meta):
        if m["month"] in L.MONTHS:
            out[m["month"]].append(i)
    return out


def evaluate(meta, midx, pred, name, *, nboot=4000):
    idx_all = [i for m in L.MONTHS for i in midx[m]]
    windows, selected = L.run_windows(meta, idx_all, pred)
    out = {"arm": name, "n_windows_ranked": len(windows)}
    for tag, months in (("ALL", L.MONTHS), ("DEV", L.DEV_MONTHS), ("CONF", L.CONF_MONTHS)):
        sub = [w for w in windows if w["month"] in months]
        out[tag] = L.rank_skill(sub, nboot=nboot)
        out[tag + "_fixed_window"] = L.rank_skill(sub, fixed_window=True, nboot=nboot)
    out["book_shipped_policy"] = L.book(meta, selected)
    out["book_by_month"] = {}
    for m in L.MONTHS:
        w_m, s_m = L.run_windows(meta, midx[m], pred)
        out["book_by_month"][m] = L.book(meta, s_m)
        out["book_by_month"][m]["mean_pick_r"] = L.rank_skill(w_m, nboot=200)["P3_r_per_window"]["mean_pick_r"]
    disp = defaultdict(int)
    for w in windows:
        disp[w["outcome_gate"] or "unranked"] += 1
    out["dispositions"] = dict(sorted(disp.items()))
    return out, windows


def reference_arms(windows):
    """Policy-free reference arms computed from the window records themselves."""
    def agg(key):
        vals = [w[key] for w in windows if w.get(key) is not None]
        days = [w["trading_day"] for w in windows if w.get(key) is not None]
        return L.boot_day(vals, days, 2000)
    return {"ORACLE": agg("oracle_max_actual"), "RANDOM": agg("mean_actual"),
            "ANTI_ORACLE": agg("oracle_min_actual"), "RANK2": agg("rank2_actual"),
            "PICK": agg("pick_actual")}


def main() -> None:
    with (L.OUT / "dataset.pkl").open("rb") as fh:
        data = pickle.load(fh)
    meta = data["meta"]
    midx = month_idx(meta)
    n = len(meta)
    keypos = {m["key"]: i for i, m in enumerate(meta)}
    results = {}

    # ---- instrument validation against the sealed reproduction --------------
    val_path = L.OUT / "eval_INSTRUMENT.json"
    if val_path.exists():
        results["INSTRUMENT"] = json.loads(val_path.read_text())
    elif LANE3.exists():
        with gzip.open(LANE3, "rb") as fh:
            sealed = pickle.load(fh)
        arr = np.full(n, np.nan)
        for k, v in sealed.items():
            j = keypos.get(k)
            if j is not None:
                arr[j] = v
        res, windows = evaluate(meta, midx, arr, "SHIPPED_SEALED", nboot=4000)
        res["reference_arms"] = reference_arms(windows)
        res["expected_sealed"] = {
            "feb": {"top_below_0p10": 1164, "top_limit_abstain": 601, "trade": 106,
                    "actual_net_r": 14.168399},
            "apr": {"actual_net_r": -7.742114}, "may": {"actual_net_r": 5.130257},
            "jun": {"actual_net_r": 3.963843}, "jul": {"actual_net_r": -14.566020}}
        val_path.write_text(json.dumps(res, indent=1, sort_keys=True, default=float))
        results["INSTRUMENT"] = res
        log(stage="instrument", book=res["book_shipped_policy"])
        with gzip.open(L.OUT / "windows_SHIPPED.pkl.gz", "wb") as fh:
            pickle.dump(windows, fh, protocol=5)

    # ---- every completed arm ------------------------------------------------
    want = set(sys.argv[1:]) or None
    for stage in L.complete_stages():
        path = L.OUT / f"preds_{stage}.npz"
        ck = L.OUT / f"ck_{stage}.json"
        if not path.exists():
            continue
        state = json.loads(ck.read_text())
        blob = np.load(path)
        for arm in blob.files:
            if want and arm not in want:
                continue
            out_path = L.OUT / f"eval_{arm}.json"
            if out_path.exists():
                results[arm] = json.loads(out_path.read_text())
                continue
            arr = blob[arm]
            scored = int(np.isfinite(arr).sum())
            if scored < 100000:
                log(stage="skip_partial", arm=arm, scored=scored,
                    days_done=len(state["days_done"]))
                continue
            res, windows = evaluate(meta, midx, arr, arm)
            res["stage"] = stage
            res["days_complete"] = len(state["days_done"])
            res["candidates_scored"] = scored
            out_path.write_text(json.dumps(res, indent=1, sort_keys=True, default=float))
            results[arm] = res
            log(stage="arm", arm=arm, days=len(state["days_done"]),
                P1=res["ALL"]["P1_pick_positive"]["ranker"]["point"],
                P1_base=res["ALL"]["P1_pick_positive"]["uniform_baseline"],
                book=res["book_shipped_policy"]["actual_net_r"])

    (L.OUT / "EVAL_V1.json").write_text(json.dumps(results, indent=1, sort_keys=True, default=float))
    log(stage="DONE", arms=sorted(results))


if __name__ == "__main__":
    main()
