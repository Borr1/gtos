#!/usr/bin/env python3
"""LANE E: generator-logic review — measured cross-checks.

For each origin family, measure (a) the geometry the generator attaches,
(b) how the trade actually resolves in its 2 h label window, and (c) whether
outcomes vary along the conditioning variable the family's CONCEPT implies but
its TRIGGER omits. Read-only over the five-month cached populations.
"""
import gzip
import json
import math
import pickle
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

CACHE = Path("/private/tmp/w21-puzzle-cache")
OUT = Path("/private/tmp/lane_e")
OUT.mkdir(exist_ok=True)
MONTHS = ["feb", "apr", "may", "jun", "jul"]

FILLED = {"RESOLVED_FILLED_STOP", "RESOLVED_FILLED_TIME_STOP", "RESOLVED_FILLED_TARGET"}


def med(xs):
    xs = [x for x in xs if x is not None and isinstance(x, (int, float)) and math.isfinite(x)]
    return round(float(np.median(xs)), 4) if xs else None


def mean(xs):
    xs = [x for x in xs if x is not None and isinstance(x, (int, float)) and math.isfinite(x)]
    return round(float(np.mean(xs)), 4) if xs else None


def se(xs):
    xs = [x for x in xs if x is not None and isinstance(x, (int, float)) and math.isfinite(x)]
    return round(float(np.std(xs, ddof=1) / math.sqrt(len(xs))), 4) if len(xs) > 2 else None


all_rows = {}
for m in MONTHS:
    with gzip.open(CACHE / f"rows_{m}.pkl.gz", "rb") as fh:
        all_rows[m] = pickle.load(fh)
    print(f"loaded {m}: {len(all_rows[m])}", flush=True)

pool = [r for m in MONTHS for r in all_rows[m]]
families = sorted({r["origin_family"] for r in pool})

report = {"n_pool": len(pool), "months": MONTHS, "families": {}}

for fam in families:
    fr = [r for r in pool if r["origin_family"] == fam]
    fil = [r for r in fr if r.get("lifecycle_label_status") in FILLED]
    ent = {
        "n_emitted_5mo": len(fr),
        "n_filled_5mo": len(fil),
        "fill_rate": round(len(fil) / len(fr), 4) if fr else None,
        "order_type": dict(Counter(r.get("proposed_order_type") for r in fr)),
        "side_mix": dict(Counter(r.get("side") for r in fr)),
        "label_mix": {k: round(v / len(fr), 4) for k, v in Counter(
            r.get("lifecycle_label_status") for r in fr).most_common()},
    }
    # geometry
    ent["geometry"] = {
        "median_stop_distance_atr": med([r.get("stop_distance_atr") for r in fr]),
        "median_target_distance_atr": med([r.get("target_distance_atr") for r in fr]),
        "median_risk_over_atr": med([r.get("risk_over_atr") for r in fr]),
        "median_risk_frac_of_entry_bps": (
            round(med([r.get("risk_fraction_of_entry") for r in fr]) * 10000, 2)
            if med([r.get("risk_fraction_of_entry") for r in fr]) is not None else None),
    }
    # cost, on filled rows with complete cost
    cc = [r for r in fil if r.get("cost_label_status") == "COMPLETE"]
    ent["cost_R"] = {
        "n_complete": len(cc),
        "median_total_cost_r": med([r.get("cost_r") for r in cc]),
        "median_spread_r": med([r.get("spread_r") for r in cc]),
        "median_commission_r": med([r.get("commission_r") for r in cc]),
    }
    # resolution among filled
    if fil:
        lab = Counter(r["lifecycle_label_status"] for r in fil)
        ent["resolution_of_filled"] = {
            "stop": round(lab["RESOLVED_FILLED_STOP"] / len(fil), 4),
            "target": round(lab["RESOLVED_FILLED_TARGET"] / len(fil), 4),
            "time_stop": round(lab["RESOLVED_FILLED_TIME_STOP"] / len(fil), 4),
        }
        net = [r.get("terminal_net_r") for r in fil]
        ent["net_R"] = {"mean": mean(net), "se": se(net), "median": med(net)}
        ent["net_R_inverted"] = {"mean": mean([-x for x in net if x is not None])}
        per_m = {}
        for m in MONTHS:
            mn = [r.get("terminal_net_r") for r in all_rows[m]
                  if r["origin_family"] == fam and r.get("lifecycle_label_status") in FILLED]
            per_m[m] = {"n": len(mn), "mean": mean(mn)}
        ent["net_R_per_month"] = per_m
    report["families"][fam] = ent

# ---------------------------------------------------------------- conditioning
# For each family, the conditioning variable its CONCEPT implies but its
# TRIGGER does not test. Buckets are declared here, before reading outcomes.
COND = {
    "structural_distance_extreme": [("trend_state_m15", "categorical"),
                                    ("dist_to_prior_high20_atr", "quartile"),
                                    ("atr14_over_atr50", "quartile")],
    "liquidity_sweep_reclaim": [("trend_state_m15", "categorical"),
                                ("sweep_depth_atr", "quartile"),
                                ("trigger_bar_body_atr", "quartile")],
    "displacement_continuation": [("trend_state_m15", "categorical"),
                                  ("trigger_bar_body_atr", "quartile"),
                                  ("utc_session", "categorical")],
    "session_open_range_break": [("session_open_range_width_atr", "quartile"),
                                 ("bars_since_session_open", "quartile"),
                                 ("trend_state_m15", "categorical")],
    "volatility_compression_expansion": [("compression_ratio_prior_bar", "quartile"),
                                         ("trend_state_m15", "categorical")],
    "regime_transition_break": [("trend_state_m15", "categorical"),
                                ("atr14_over_atr50", "quartile")],
    "cross_asset_lead_lag": [("utc_session", "categorical"),
                             ("atr14_over_atr50", "quartile")],
    "current_fvg_fill": [("poi_age_hours", "quartile"),
                         ("poi_touch_count", "quartile"),
                         ("poi_distance_to_zone_atr", "quartile"),
                         ("trend_state_m15", "categorical")],
    "current_ob_retest": [("poi_touch_count", "quartile"),
                          ("poi_age_hours", "quartile"),
                          ("trend_state_m15", "categorical")],
    "current_breaker_re_entry": [("poi_age_hours", "quartile"),
                                 ("trend_state_m15", "categorical")],
}

cond_out = {}
for fam, specs in COND.items():
    fil = [r for r in pool if r["origin_family"] == fam
           and r.get("lifecycle_label_status") in FILLED
           and r.get("terminal_net_r") is not None]
    fam_out = {"n_filled": len(fil), "overall_mean_net_r": mean([r["terminal_net_r"] for r in fil])}
    for var, kind in specs:
        if kind == "categorical":
            groups = defaultdict(list)
            for r in fil:
                groups[str(r.get(var))].append(r["terminal_net_r"])
            fam_out[var] = {k: {"n": len(v), "mean": mean(v), "se": se(v)}
                            for k, v in sorted(groups.items()) if len(v) >= 30}
        else:
            vals = [(r.get(var), r["terminal_net_r"]) for r in fil]
            vals = [(v, y) for v, y in vals
                    if isinstance(v, (int, float)) and v is not None and math.isfinite(v)]
            if len(vals) < 120:
                fam_out[var] = {"note": f"insufficient/absent (n={len(vals)})"}
                continue
            arr = np.array([v for v, _ in vals])
            qs = np.quantile(arr, [0.25, 0.5, 0.75])
            buckets = defaultdict(list)
            for v, y in vals:
                b = ("Q1" if v <= qs[0] else "Q2" if v <= qs[1]
                     else "Q3" if v <= qs[2] else "Q4")
                buckets[b].append(y)
            fam_out[var] = {"cutpoints": [round(float(q), 4) for q in qs]}
            fam_out[var].update({k: {"n": len(v), "mean": mean(v), "se": se(v)}
                                 for k, v in sorted(buckets.items())})
            # monotonicity of the sorted quartile means
            ms = [mean(buckets[k]) for k in ("Q1", "Q2", "Q3", "Q4") if k in buckets]
            if len(ms) == 4 and all(x is not None for x in ms):
                fam_out[var]["monotone"] = (
                    "increasing" if ms == sorted(ms) else
                    "decreasing" if ms == sorted(ms, reverse=True) else "no")
                fam_out[var]["spread_Q4_minus_Q1"] = round(ms[3] - ms[0], 4)
    cond_out[fam] = fam_out

report["conditioning"] = cond_out

# --------------------------------------------------- SDE trend joint, by side
sde = [r for r in pool if r["origin_family"] == "structural_distance_extreme"]
joint = defaultdict(list)
for r in sde:
    joint[(r.get("side"), str(r.get("trend_state_m15")))].append(
        r.get("terminal_net_r") if r.get("lifecycle_label_status") in FILLED else None)
report["sde_side_x_trend"] = {
    f"{s}|{t}": {"n_emitted": len(v), "n_filled": len([x for x in v if x is not None]),
                 "mean_net_r": mean([x for x in v if x is not None])}
    for (s, t), v in sorted(joint.items())}

# -------------------------------- LSR: is the "sweep" a sweep? depth + reclaim
lsr = [r for r in pool if r["origin_family"] == "liquidity_sweep_reclaim"]
depths = [r.get("sweep_depth_atr") for r in lsr]
depths = [d for d in depths if isinstance(d, (int, float)) and d is not None and math.isfinite(d)]
report["lsr_sweep_depth_atr"] = {
    "n": len(depths),
    "p05": round(float(np.quantile(depths, 0.05)), 4) if depths else None,
    "p25": round(float(np.quantile(depths, 0.25)), 4) if depths else None,
    "p50": round(float(np.quantile(depths, 0.50)), 4) if depths else None,
    "p75": round(float(np.quantile(depths, 0.75)), 4) if depths else None,
    "p95": round(float(np.quantile(depths, 0.95)), 4) if depths else None,
    "share_below_0p10_atr": round(float(np.mean([d < 0.10 for d in depths])), 4) if depths else None,
    "share_below_0p25_atr": round(float(np.mean([d < 0.25 for d in depths])), 4) if depths else None,
}
lsr_trend = defaultdict(list)
for r in lsr:
    if r.get("lifecycle_label_status") in FILLED:
        lsr_trend[(r.get("side"), str(r.get("trend_state_m15")))].append(r["terminal_net_r"])
report["lsr_side_x_trend"] = {f"{s}|{t}": {"n": len(v), "mean": mean(v), "se": se(v)}
                              for (s, t), v in sorted(lsr_trend.items()) if len(v) >= 30}

# ---------------------------------- time-stop pressure: is the target reachable
tp = {}
for fam in families:
    fil = [r for r in pool if r["origin_family"] == fam
           and r.get("lifecycle_label_status") in FILLED]
    if not fil:
        continue
    ts = [r for r in fil if r["lifecycle_label_status"] == "RESOLVED_FILLED_TIME_STOP"]
    tp[fam] = {
        "time_stop_share_of_filled": round(len(ts) / len(fil), 4),
        "median_target_distance_atr": med([r.get("target_distance_atr") for r in fil]),
        "mean_net_r_of_time_stopped": mean([r.get("terminal_net_r") for r in ts]),
        "mean_net_r_of_all_filled": mean([r.get("terminal_net_r") for r in fil]),
    }
report["horizon_pressure"] = tp

(OUT / "LANE_E_FAMILY_MEASURES_V1.json").write_text(json.dumps(report, indent=1, sort_keys=True))
print("written", OUT / "LANE_E_FAMILY_MEASURES_V1.json")
