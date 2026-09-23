#!/usr/bin/env python3
"""B3 step 1b -- the KNOWN-LEAKY regime block, built deliberately.

PREREG_V1_1 declares two negative-control arms (A10L, A11L).  Their feature
block F1_LEAK is identical to F1 except that the day-level regime aggregates
are the SAME trading day's medians and shares -- the construction that was
found to be lookahead.  Family momentum stays strictly prior in both, so the
contrast isolates exactly one thing: the day aggregate's timing.

Also emits the PAST/FUTURE split aggregates (PREREG_V1_1 test T2): the same
aggregate built from only the candidates strictly BEFORE a within-day cutoff,
and from only those at or AFTER it.
"""
from __future__ import annotations

import json
import pickle
import time
from collections import defaultdict

import numpy as np
import pandas as pd

import b3_lib as L

T0 = time.time()
MED = {"reg_vol": "atr14_over_atr50", "reg_ccvol": "close_to_close_vol_8_over_48",
       "reg_comp": "compression_ratio_prior_bar", "reg_spread": "spread_r",
       "reg_cost": "cost_r", "reg_risk": "risk_over_atr"}


def aggregates(frame, cday, mask=None):
    tmp = pd.DataFrame({"d": cday})
    for out_key, col in MED.items():
        tmp[out_key] = frame[col].to_numpy(dtype=float)
    trend = frame["trend_state_m15"].astype(str).to_numpy()
    tmp["reg_trendshare"] = np.isin(trend, ["strong_up", "strong_down"]).astype(float)
    tmp["reg_upshare"] = np.isin(trend, ["strong_up", "up"]).astype(float)
    if mask is not None:
        tmp = tmp[mask]
    return tmp.groupby("d", observed=True).agg(
        {**{k: "median" for k in MED}, "reg_trendshare": "mean", "reg_upshare": "mean"})


def main() -> None:
    with (L.OUT / "dataset.pkl").open("rb") as fh:
        data = pickle.load(fh)
    meta, frame = data["meta"], data["frame"]
    cday = np.asarray([m["cday"] for m in meta])
    hour = np.asarray([int(str(m["t0"])[11:13]) for m in meta])
    n = len(meta)

    same = aggregates(frame, cday)
    past = aggregates(frame, cday, mask=(hour < 12))
    future = aggregates(frame, cday, mask=(hour >= 12))

    cols = {}
    for tag, agg in (("LEAK", same), ("PAST", past), ("FUTURE", future)):
        for key in ["reg_vol", "reg_ccvol", "reg_comp", "reg_spread", "reg_cost",
                    "reg_risk", "reg_trendshare", "reg_upshare"]:
            series = agg[key] if key in agg else None
            cols[f"{key}__{tag}"] = np.asarray(
                [float(series.get(d, np.nan)) if series is not None else np.nan for d in cday],
                dtype=np.float32)

    # family x same-day-regime buckets, cut on the SAME day (the leaky construction)
    fam = np.asarray([m["fam"] for m in meta])
    days = sorted(set(cday.tolist()))
    vol = np.asarray([float(same["reg_vol"].get(d, np.nan)) for d in days])
    tsh = np.asarray([float(same["reg_trendshare"].get(d, np.nan)) for d in days])
    vcut = np.nanpercentile(vol, [33.3, 66.7])
    tcut = np.nanpercentile(tsh, [33.3, 66.7])
    lut_v = {d: ("MISSING" if not np.isfinite(v) else
                 "LO" if v <= vcut[0] else "MID" if v <= vcut[1] else "HI")
             for d, v in zip(days, vol)}
    lut_t = {d: ("MISSING" if not np.isfinite(v) else
                 "LO" if v <= tcut[0] else "MID" if v <= tcut[1] else "HI")
             for d, v in zip(days, tsh)}
    vb = np.array([fam[i] + "|" + lut_v[cday[i]] for i in range(n)], dtype=object)
    tb = np.array([fam[i] + "|" + lut_t[cday[i]] for i in range(n)], dtype=object)

    payload = {"cols": cols, "family_x_volbucket__LEAK": vb, "family_x_trendbucket__LEAK": tb}
    with (L.OUT / "leak_features.pkl").open("wb") as fh:
        pickle.dump(payload, fh, protocol=5)
    print(json.dumps({"t": round(time.time() - T0, 1), "stage": "DONE", "n": n,
                      "cols": len(cols), "days": len(days),
                      "n_past_rows": int((hour < 12).sum()),
                      "n_future_rows": int((hour >= 12).sum())}), flush=True)


if __name__ == "__main__":
    main()
