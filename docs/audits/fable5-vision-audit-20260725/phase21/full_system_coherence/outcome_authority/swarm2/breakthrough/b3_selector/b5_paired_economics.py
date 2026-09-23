#!/usr/bin/env python3
"""B3 step 5 -- the PREREG_V1_3 primary metric, plus the Q3 embargo measurement.

E1  per-day paired difference in realized book R against the shipped rule
E2  mean R per ranked window and the within-window selection term
E3  ceiling capture
Q3  how many training rows carry a label that closes AFTER the day they are
    absorbed with -- the label-availability leak, measured on B3's own basis
"""
from __future__ import annotations

import gzip
import json
import pickle
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

import b3_lib as L

LANE3 = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/lane3/out/preds_daily.pkl.gz")
T0 = time.time()


def log(**kw):
    print(json.dumps({"t": round(time.time() - T0, 1), **kw}, sort_keys=True), flush=True)


def day_books(meta, selected):
    out = defaultdict(float)
    for i in selected:
        if meta[i]["res"]:
            out[meta[i]["day"]] += meta[i]["net"]
    return out


def main() -> None:
    with (L.OUT / "dataset.pkl").open("rb") as fh:
        data = pickle.load(fh)
    meta = data["meta"]
    n = len(meta)
    keypos = {m["key"]: i for i, m in enumerate(meta)}
    midx = defaultdict(list)
    for i, m in enumerate(meta):
        if m["month"] in L.MONTHS:
            midx[m["month"]].append(i)
    idx_all = [i for mm in L.MONTHS for i in midx[mm]]
    all_days = sorted({meta[i]["day"] for i in idx_all})

    # ---- Q3: the label-availability measurement --------------------------
    q3 = {}
    late = 0
    horizon = defaultdict(int)
    for m in meta:
        end = L.at(m["t1"])
        day_end = datetime.fromisoformat(m["day"] + "T00:00:00+00:00") + timedelta(days=1)
        if end >= day_end:
            late += 1
            horizon[(end.date() - datetime.fromisoformat(m["day"]).date()).days] += 1
    q3["rows_total"] = n
    q3["rows_whose_label_closes_after_their_own_trading_day"] = late
    q3["fraction"] = round(late / n, 6)
    q3["by_days_late"] = {str(k): v for k, v in sorted(horizon.items())}
    q3["definition"] = ("label_span_end_utc (or expiry for censored/no-fill) at or after 00:00 UTC "
                        "of the day AFTER the row's own trading_day. Such a row is absorbed into "
                        "training by the frozen chain the moment its day ends, but its label was "
                        "not knowable then.")
    log(stage="Q3", **{k: v for k, v in q3.items() if k != "by_days_late"})

    # ---- arms -------------------------------------------------------------
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
    for name, num, den in (("PFILL_RIDGE", "A2", "A1"), ("PFILL_HGB", "A5", "A4")):
        if num in arrays and den in arrays:
            with np.errstate(divide="ignore", invalid="ignore"):
                r = arrays[num] / arrays[den]
            r[~np.isfinite(r)] = np.nan
            arrays[name] = r

    shipped_days = None
    out = {"Q3_label_availability": q3, "arms": {}}
    order = ["SHIPPED_SEALED"] + [a for a in sorted(arrays) if a != "SHIPPED_SEALED"]
    for arm in order:
        windows, selected = L.run_windows(meta, idx_all, arrays[arm])
        db = day_books(meta, selected)
        if arm == "SHIPPED_SEALED":
            shipped_days = db
        rec = {"trades": len(selected)}
        # E1 paired per-day difference against the shipped rule
        diffs = [db.get(d, 0.0) - shipped_days.get(d, 0.0) for d in all_days]
        rec["E1_paired_vs_shipped"] = {
            "days": len(all_days), "sum_r": round(float(np.sum(diffs)), 4),
            "boot": L.boot_day(diffs, all_days, 4000)}
        rec["book_actual_r"] = round(float(sum(db.values())), 4)
        # E2 window-level
        pick = [w["pick_actual"] for w in windows if w["pick_actual"] is not None]
        pd_ = [w["trading_day"] for w in windows if w["pick_actual"] is not None]
        sel = [(w["pick_actual"] - w["mean_actual"], w["trading_day"]) for w in windows
               if w["pick_actual"] is not None and w["mean_actual"] is not None]
        rec["E2_mean_r_per_window"] = L.boot_day(pick, pd_, 4000)
        rec["E2_selection_term"] = L.boot_day([a for a, _ in sel], [d for _, d in sel], 4000)
        rec["E2_no_fill_share_of_picks"] = round(float(np.mean(
            [1.0 if (w["pick_actual"] is not None and w["pick_actual"] == 0.0) else 0.0
             for w in windows])), 4)
        rec["E2_market_top_share"] = round(float(np.mean(
            [1.0 if w["top_order_type"] == "MARKET" else 0.0 for w in windows])), 4)
        # E3
        rnd = [w["mean_actual"] for w in windows if w["mean_actual"] is not None]
        orc = [w["oracle_max_actual"] for w in windows if w["oracle_max_actual"] is not None]
        mp, mr, mo = float(np.mean(pick)), float(np.mean(rnd)), float(np.mean(orc))
        rec["E3_ceiling_capture"] = round((mp - mr) / (mo - mr), 6)
        rec["E3_terms"] = {"pick": mp, "random": mr, "oracle": mo}
        # per split
        for tag, months in (("DEV", L.DEV_MONTHS), ("CONF", L.CONF_MONTHS)):
            sub = [w for w in windows if w["month"] in months]
            s = [(w["pick_actual"] - w["mean_actual"], w["trading_day"]) for w in sub
                 if w["pick_actual"] is not None and w["mean_actual"] is not None]
            rec[f"E2_selection_term_{tag}"] = L.boot_day([a for a, _ in s], [d for _, d in s], 2000)
        out["arms"][arm] = rec
        log(arm=arm, E1=rec["E1_paired_vs_shipped"]["sum_r"],
            E1p=rec["E1_paired_vs_shipped"]["boot"]["p_two_sided_sign"],
            sel=round(rec["E2_selection_term"]["point"], 5),
            selp=rec["E2_selection_term"]["p_two_sided_sign"],
            nofill=rec["E2_no_fill_share_of_picks"], mkt=rec["E2_market_top_share"],
            cap=rec["E3_ceiling_capture"])
    (L.OUT / "PAIRED_ECONOMICS_V1.json").write_text(
        json.dumps(out, indent=1, sort_keys=True, default=float))
    log(stage="DONE", arms=len(out["arms"]))


if __name__ == "__main__":
    main()
