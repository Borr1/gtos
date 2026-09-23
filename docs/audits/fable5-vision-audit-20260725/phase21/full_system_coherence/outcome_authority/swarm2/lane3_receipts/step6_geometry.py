#!/usr/bin/env python3
"""LANE 3 step 6: what the cost gate is REALLY gating, and whether any
ungated axis carries positive expectancy.

cost_r = modelled cost / |entry - stop|, so MAX_COST_R = 0.20 is a floor on
stop width in cost units. The population cost curve may therefore be a
GEOMETRY curve wearing a cost label. Measured here on the resolved population:
E[net] by stop width, by R:R, and by cost, marginally and jointly.

Also: P(the ranker's pick is positive) against the uniform baseline, with a
day-clustered interval - the robust version of the best-pick rate.
"""
import gzip
import json
import pickle
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import funnel_lib as F

OUT = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/lane3/out")
PRED_KEY = sys.argv[1] if len(sys.argv) > 1 else "pred_month_boundary"
TAG = "daily" if PRED_KEY == "pred_daily" else "monthfit"
RNG = np.random.default_rng(20260812)


def boot(vals, days, nboot=1000):
    if not len(vals):
        return None
    by = defaultdict(list)
    for v, d in zip(vals, days):
        by[d].append(v)
    arrs = [np.asarray(by[k], dtype=float) for k in sorted(by)]
    n = len(arrs)
    o = np.asarray([np.concatenate([arrs[i] for i in RNG.integers(0, n, n)]).mean()
                    for _ in range(nboot)])
    return {"point": float(np.mean(vals)), "n": int(len(vals)),
            "ci95_lo": float(np.percentile(o, 2.5)),
            "ci95_hi": float(np.percentile(o, 97.5)),
            "p_two_sided_sign": float(2 * min((o <= 0).mean(), (o >= 0).mean()))}


def curve(recs, field, edges, label):
    out = []
    for lo, hi in zip(edges, edges[1:]):
        g = [r for r in recs if r[field] is not None and lo <= r[field] < hi]
        if len(g) < 200:
            continue
        v = [r["net"] for r in g]
        d = [r["day"] for r in g]
        row = {"lo": lo, "hi": hi, "n": len(g), "mean": float(np.mean(v)),
               "sum": float(np.sum(v)), "boot": boot(v, d, 400),
               "target_rate": float(np.mean([r["state"] == "TARGET" for r in g])),
               "stop_rate": float(np.mean([r["state"] == "STOP" for r in g])),
               "time_stop_rate": float(np.mean([r["state"] == "TIME_STOP" for r in g])),
               "mean_cost_r": float(np.mean([r["cost"] for r in g if r["cost"] is not None]))}
        out.append(row)
    return {"field": field, "label": label, "bins": out}


def main():
    preds = None
    if PRED_KEY == "pred_daily":
        with gzip.open(OUT / "preds_daily.pkl.gz", "rb") as fh:
            preds = pickle.load(fh)
    rep = {"pred_key": PRED_KEY}
    recs = []
    picks = []
    for month in F.MONTHS:
        rows = F.load_month(month)
        if preds is not None:
            for r_ in rows:
                r_["pred_daily"] = preds.get(r_["candidate_occurrence_key"])
        _sel, _d, _death, windows = F.run_funnel(rows, pred_key=PRED_KEY, diagnose=True)
        for w in windows:
            w["month"] = month
        picks.extend(windows)
        for r_ in rows:
            if not r_["resolved"] or not r_["predecision_geometry_valid"]:
                continue
            def num(k):
                v = r_.get(k)
                try:
                    v = float(v)
                except (TypeError, ValueError):
                    return None
                return v if np.isfinite(v) else None
            sd, td = num("stop_distance_atr"), num("target_distance_atr")
            recs.append({
                "net": F.net_actual(r_), "day": r_["trading_day"], "state": r_["state"],
                "ot": r_["proposed_order_type"], "fam": r_["origin_family"],
                "cost": num("cost_r"), "stop_atr": sd, "tgt_atr": td,
                "rr": (td / sd) if (sd and td and sd > 0) else None,
                "roa": num("risk_over_atr"),
            })
        print(json.dumps({"month": month, "recs": len(recs)}), flush=True)

    mkt = [r for r in recs if r["ot"] == "MARKET"]
    lmt = [r for r in recs if r["ot"] == "LIMIT"]
    rep["n"] = {"all": len(recs), "MARKET": len(mkt), "LIMIT": len(lmt)}
    rep["curves"] = {
        "MARKET_by_cost_r": curve(mkt, "cost", [0, .02, .04, .06, .08, .10, .12, .15, .20,
                                                .25, .30, .40, .60, 1.0, 1e9], "MARKET E[net] by cost_r"),
        "MARKET_by_stop_atr": curve(mkt, "stop_atr", [0, .25, .5, .75, 1.0, 1.5, 2.0, 3.0,
                                                      5.0, 10.0, 1e9], "MARKET E[net] by stop width (ATR)"),
        "MARKET_by_rr": curve(mkt, "rr", [0, .5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 6.0, 1e9],
                              "MARKET E[net] by target/stop ratio"),
        "LIMIT_by_cost_r": curve(lmt, "cost", [0, .02, .04, .06, .08, .10, .12, .15, .20,
                                               .25, .30, .40, .60, 1.0, 1e9], "LIMIT E[net] by cost_r"),
        "LIMIT_by_rr": curve(lmt, "rr", [0, .5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 6.0, 1e9],
                             "LIMIT E[net] by target/stop ratio"),
    }
    # joint: does cost survive conditioning on stop width?
    joint = []
    sedges = [0, .5, 1.0, 2.0, 1e9]
    cedges = [0, .08, .15, .20, 1e9]
    for slo, shi in zip(sedges, sedges[1:]):
        for clo, chi in zip(cedges, cedges[1:]):
            g = [r for r in mkt if r["stop_atr"] is not None and slo <= r["stop_atr"] < shi
                 and r["cost"] is not None and clo <= r["cost"] < chi]
            if len(g) < 200:
                continue
            joint.append({"stop_atr": [slo, shi], "cost_r": [clo, chi], "n": len(g),
                          "mean_net": float(np.mean([r["net"] for r in g]))})
    rep["joint_market_stopwidth_x_cost"] = joint

    # ---- family x order type expectancy, the ungated axis -----------------
    fam = {}
    for f in sorted({r["fam"] for r in recs}):
        g = [r for r in recs if r["fam"] == f]
        fam[f] = {"n": len(g), "ot": g[0]["ot"],
                  "mean_net": float(np.mean([r["net"] for r in g])),
                  "sum_net": float(np.sum([r["net"] for r in g])),
                  "boot": boot([r["net"] for r in g], [r["day"] for r in g], 400),
                  "target_rate": float(np.mean([r["state"] == "TARGET" for r in g]))}
    rep["family_expectancy"] = fam

    # ---- P(pick is positive) vs uniform ----------------------------------
    strict = [w for w in picks if w["oracle_max_actual"] is not None]
    hit = [1.0 if (w["pick_actual"] or 0) > 0 else 0.0 for w in strict
           if w["pick_actual"] is not None]
    hd = [w["trading_day"] for w in strict if w["pick_actual"] is not None]
    base = [w["n_positive_available"] / w["n_available"] for w in strict
            if w["pick_actual"] is not None]
    diff = [h - b for h, b in zip(hit, base)]
    rep["pick_positive_rate"] = {
        "windows": len(hit),
        "ranker": boot(hit, hd, 2000),
        "uniform_baseline": float(np.mean(base)),
        "ranker_minus_uniform": boot(diff, hd, 2000),
    }
    bestw = [w for w in picks if w["oracle_max_actual"] is not None and w["oracle_max_actual"] > 0]
    bh = [1.0 if w["pick_is_window_best"] else 0.0 for w in bestw]
    bb = [1.0 / w["n_available"] for w in bestw]
    rep["pick_best_rate_strict"] = {
        "windows": len(bestw),
        "ranker": boot(bh, [w["trading_day"] for w in bestw], 2000),
        "uniform_baseline": float(np.mean(bb)),
        "ranker_minus_uniform": boot([a - b for a, b in zip(bh, bb)],
                                     [w["trading_day"] for w in bestw], 2000),
    }
    (OUT / f"geometry_{TAG}.json").write_text(json.dumps(rep, indent=1, sort_keys=True, default=float))
    print("WROTE", OUT / f"geometry_{TAG}.json")


if __name__ == "__main__":
    main()
