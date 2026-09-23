#!/usr/bin/env python3
"""LANE E pass 3: the specific confirmation steps the concepts require.

Each test below is the code-reading's prediction, declared before the number is
read: if the generator omits a confirmation the concept requires, outcomes
should vary along that confirmation. Per-month sign consistency is the guard
against reading noise.
"""
import gzip
import json
import math
import pickle
from collections import defaultdict

import numpy as np

MONTHS = ["feb", "apr", "may", "jun", "jul"]
F = {"RESOLVED_FILLED_STOP", "RESOLVED_FILLED_TIME_STOP", "RESOLVED_FILLED_TARGET"}
rows_by_month = {}
for m in MONTHS:
    with gzip.open(f"/private/tmp/w21-puzzle-cache/rows_{m}.pkl.gz", "rb") as fh:
        rows_by_month[m] = pickle.load(fh)
pool = [r for m in MONTHS for r in rows_by_month[m]]


def stat(rs):
    ys = [r["terminal_net_r"] for r in rs if r.get("terminal_net_r") is not None]
    if not ys:
        return None
    a = np.asarray(ys, dtype=float)
    per = {}
    for m in MONTHS:
        mm = [r["terminal_net_r"] for r in rs if r["month"] == m and r.get("terminal_net_r") is not None]
        per[m] = round(float(np.mean(mm)), 4) if mm else None
    return {
        "n": len(ys), "mean": round(float(a.mean()), 4),
        "se": round(float(a.std(ddof=1) / math.sqrt(len(a))), 4) if len(a) > 2 else None,
        "per_month": per,
        "months_positive": sum(1 for v in per.values() if v is not None and v > 0),
    }


def fam(name):
    return [r for r in pool if r["origin_family"] == name
            and r.get("lifecycle_label_status") in F
            and r.get("terminal_net_r") is not None]


def num(r, k):
    v = r.get(k)
    return v if isinstance(v, (int, float)) and v is not None and math.isfinite(v) else None


out = {}

# --- T1 liquidity_sweep_reclaim: the reclaim-quality confirmation --------------
# Concept: a sweep is a raid on resting liquidity followed by a decisive reclaim.
# Code tests only "high > prior20high and close < prior20high" — any depth, any
# close location. Proxy for reclaim decisiveness = body/range of the trigger bar.
lsr = fam("liquidity_sweep_reclaim")
br = [(num(r, "trigger_bar_body_atr"), num(r, "trigger_bar_range_atr"), r) for r in lsr]
br = [(b / g, r) for b, g, r in br if b is not None and g not in (None, 0)]
vals = np.array([x for x, _ in br])
qs = np.quantile(vals, [0.25, 0.5, 0.75])
buckets = defaultdict(list)
for v, r in br:
    buckets["Q1" if v <= qs[0] else "Q2" if v <= qs[1] else "Q3" if v <= qs[2] else "Q4"].append(r)
out["T1_lsr_body_over_range"] = {"cutpoints": [round(float(q), 4) for q in qs],
                                 **{k: stat(v) for k, v in sorted(buckets.items())}}

# joint: deep sweep AND decisive reclaim (both confirmations the code omits)
deep = np.quantile([num(r, "sweep_depth_atr") for r in lsr if num(r, "sweep_depth_atr") is not None], 0.75)
sel = [r for v, r in br if v > qs[2] and (num(r, "sweep_depth_atr") or 0) > deep]
out["T1b_lsr_deep_AND_decisive"] = {"depth_cut": round(float(deep), 4),
                                    "bodyrange_cut": round(float(qs[2]), 4), **(stat(sel) or {})}

# --- T2 displacement_continuation: trend agreement ----------------------------
# Concept: momentum continuation. Code sets side from the trigger bar's own body
# sign only; nothing requires the displacement to agree with the prevailing trend.
dc = fam("displacement_continuation")
agree, against, neutral = [], [], []
for r in dc:
    t, s = str(r.get("trend_state_m15")), r.get("side")
    if (s == "LONG" and t in {"up", "strong_up"}) or (s == "SHORT" and t in {"down", "strong_down"}):
        agree.append(r)
    elif (s == "LONG" and t in {"down", "strong_down"}) or (s == "SHORT" and t in {"up", "strong_up"}):
        against.append(r)
    else:
        neutral.append(r)
out["T2_displacement_trend_agreement"] = {"with_trend": stat(agree), "against_trend": stat(against),
                                          "flat": stat(neutral)}

# --- T3 structural_distance_extreme: can a range condition even be found? -----
sde = [r for r in pool if r["origin_family"] == "structural_distance_extreme"]
out["T3_sde_population_shape"] = {
    "n_emitted": len(sde),
    "share_emitted_in_flat_trend": round(
        sum(1 for r in sde if str(r.get("trend_state_m15")) == "flat") / len(sde), 4),
    "share_emitted_with_trend_agreeing_with_the_extreme": round(
        sum(1 for r in sde if (r["side"] == "SHORT" and str(r.get("trend_state_m15")) in {"up", "strong_up"})
            or (r["side"] == "LONG" and str(r.get("trend_state_m15")) in {"down", "strong_down"})) / len(sde), 4),
    "flat_only_outcome": stat([r for r in sde if r.get("lifecycle_label_status") in F
                               and str(r.get("trend_state_m15")) == "flat"
                               and r.get("terminal_net_r") is not None]),
}

# --- T4 regime_transition_break: the volatility-expansion confirmation --------
# Concept: a genuine regime change comes with a volatility expansion. Code tests
# a 20-bar trend-score transition + a 20-bar breakout and NOT vol expansion.
rtb = fam("regime_transition_break")
for cut in (1.2, 1.3, 1.4):
    sel = [r for r in rtb if (num(r, "atr14_over_atr50") or 0) >= cut]
    out[f"T4_rtb_atr_ratio_ge_{cut}"] = stat(sel)
out["T4_rtb_all"] = stat(rtb)

# --- T5 current_fvg_fill: freshness, the ICT premise --------------------------
fvg = fam("current_fvg_fill")
for lo, hi, lbl in ((None, 1.0, "age_le_1h"), (1.0, 6.0, "age_1_6h"),
                    (6.0, 24.0, "age_6_24h"), (24.0, None, "age_gt_24h")):
    sel = [r for r in fvg if (a := num(r, "poi_age_hours")) is not None
           and (lo is None or a > lo) and (hi is None or a <= hi)]
    out[f"T5_fvg_{lbl}"] = stat(sel)

# --- T6 the time-stop subset: does the direction have drift at all? -----------
ts = {}
for name in sorted({r["origin_family"] for r in pool}):
    f_all = fam(name)
    sel = [r for r in f_all if r["lifecycle_label_status"] == "RESOLVED_FILLED_TIME_STOP"]
    if len(sel) < 100:
        continue
    s = stat(sel)
    s["mean_gross_r"] = round(float(np.mean(
        [r["terminal_net_r"] + (r.get("deductible_cost_r") or 0.0) for r in sel])), 4)
    s["share_of_filled"] = round(len(sel) / len(f_all), 4)
    ts[name] = s
out["T6_time_stopped_subset"] = ts

# --- T7 cross_asset_lead_lag: liquidity-hours confirmation --------------------
cal = fam("cross_asset_lead_lag")
maj = [r for r in cal if str(r.get("utc_session")) in {"london", "ny"}]
oth = [r for r in cal if str(r.get("utc_session")) not in {"london", "ny"}]
out["T7_cal_london_ny"] = stat(maj)
out["T7_cal_other_hours"] = stat(oth)

Path = __import__("pathlib").Path
Path("/private/tmp/lane_e/LANE_E_CONFIRMATION_TESTS_V1.json").write_text(
    json.dumps(out, indent=1, sort_keys=True))
print(json.dumps(out, indent=1, sort_keys=True))
