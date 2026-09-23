#!/usr/bin/env python3
"""l1 pass 10 — verify the survivors.

Every fit that survived the Jan 01-15 -> Jan 16-31 split shares one shape: a stop MUCH
wider than the declared -1R.  This pass takes the durable candidates apart: outcome
census, day-by-day concentration, a 3-fold split instead of a 2-fold, and the re-sized
figure (a 3R stop means 1/3 the size at the same account risk, so every R scales by S).
Also measures the pool-wide value of simply widening the stop, which is the structural
claim underneath all 19 survivors.
"""
from __future__ import annotations
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from l1_lib import *  # noqa

OUT = os.path.join(HERE, "l1_VERIFY_V1.json")
N_ORIG = 27658


def corrected(r):
    return (r["spread_r"] or 0.0) / 7.3 + (r["commission_r"] or 0.0) + (r["slip_r"] or 0.0) + (r["swap_r"] or 0.0)


def census(rows, T, S):
    n = len(rows)
    g = 0.0
    net = 0.0
    why = {}
    days = {}
    for r in rows:
        v, w, ib = cell(r, T, S, "r")
        g += v
        net += v - r["_c"]
        why[w] = why.get(w, 0) + 1
        days.setdefault(r["_day"], [0.0, 0])
        days[r["_day"]][0] += v - r["_c"]
        days[r["_day"]][1] += 1
    dm = {d: round(v[0] / v[1], 5) for d, v in sorted(days.items())}
    daily = sorted(((v[0]) for v in days.values()), reverse=True)
    tot = sum(daily)
    return {"n": n, "T": T, "S": S,
            "gross_per_trade": round(g / n, 5), "net_per_trade": round(net / n, 5),
            "outcome_shares": {k: round(v / n, 5) for k, v in why.items()},
            "win_rate": round(sum(1 for r in rows if cell(r, T, S, "r")[0] > 0) / n, 5),
            "n_days": len(days),
            "days_positive_net": sum(1 for v in days.values() if v[0] > 0),
            "top_day_share_of_total_net": round(daily[0] / tot, 4) if tot > 0 else None,
            "net_per_trade_by_day": dm,
            "resized_scale": round(1.0 / S, 3),
            "net_per_trade_resized": round(net / n / S, 5),
            "net_per_ORIGINAL_candidate": round(net / N_ORIG, 6)}


def main():
    recs = pop(load(), "TAKEABLE")
    for r in recs:
        r["_c"] = corrected(r)
        r["_day"] = int(r["decision_time_utc"][8:10])
    res = {}
    cands = {
        "XAUUSD_T0.75_S3.00": (lambda r: r["symbol"] == "XAUUSD", 0.75, 3.00),
        "XAUUSD_declared_T2_S1": (lambda r: r["symbol"] == "XAUUSD", 2.0, 1.0),
        "born_resting_LONG_cheap_T0.75_S3.00":
            (lambda r: r["born"] == "born_resting" and r["side"] == "LONG" and r["_c"] <= 0.10, 0.75, 3.00),
        "cross_asset_lead_lag_LONG_cheap_T6_S1":
            (lambda r: r["family"] == "cross_asset_lead_lag" and r["side"] == "LONG" and r["_c"] <= 0.10, 6.0, 1.0),
        "POOL_T0.75_S3.00": (lambda r: True, 0.75, 3.00),
        "POOL_T2_S1": (lambda r: True, 2.0, 1.0),
        "POOL_T0.75_S0.25": (lambda r: True, 0.75, 0.25),
    }
    for name, (pred, T, S) in cands.items():
        rows = [r for r in recs if pred(r)]
        blk = census(rows, T, S)
        # 3-fold
        folds = {"f1": [r for r in rows if r["_day"] <= 10],
                 "f2": [r for r in rows if 11 <= r["_day"] <= 20],
                 "f3": [r for r in rows if r["_day"] >= 21]}
        blk["threefold_net_per_trade"] = {k: (round(mean(cell(r, T, S, "r")[0] - r["_c"] for r in v), 5)
                                              if len(v) >= 30 else None) for k, v in folds.items()}
        blk["threefold_n"] = {k: len(v) for k, v in folds.items()}
        res[name] = blk

    # the structural claim: widen the stop, pool-wide, at every target
    wide = {}
    for T in (0.5, 0.75, 1.0, 1.5, 2.0, 3.0):
        for S in ADV:
            g = mean(cell(r, T, S, "r")[0] for r in recs)
            net = mean(cell(r, T, S, "r")[0] - r["_c"] for r in recs)
            wide["T%.2f_S%.2f" % (T, S)] = {"gross": round(g, 5), "net73": round(net, 5)}
    res["POOL_WIDEN_STOP_SURFACE_NET"] = wide
    bn = max(wide.items(), key=lambda kv: kv[1]["net73"])
    res["POOL_BEST_NET_CELL"] = {"cell": bn[0], **bn[1]}

    # what the 54.4% full-stop rate becomes as the stop widens
    fl = [r for r in recs if r.get("tf_r") is not None]
    res["STOP_HIT_RATE_BY_WIDTH"] = {("S%.2f" % S): round(sum(1 for r in fl if r["ta_r"][AI[S]] is not None) / len(fl), 5)
                                     for S in ADV}
    with open(OUT, "w") as fh:
        json.dump(res, fh, indent=1)

    for name in cands:
        b = res[name]
        print("%-38s n%5d T%.2f/S%.2f gross %+.4f NET %+.4f win %.3f | days %d pos %d topday %s | 3fold %s"
              % (name[:38], b["n"], b["T"], b["S"], b["gross_per_trade"], b["net_per_trade"],
                 b["win_rate"], b["n_days"], b["days_positive_net"], b["top_day_share_of_total_net"],
                 json.dumps(b["threefold_net_per_trade"])))
        print("      outcomes %s  resized(x%.2f) NET %+.5f  perORIG %+.6f"
              % (json.dumps(b["outcome_shares"]), b["resized_scale"], b["net_per_trade_resized"],
                 b["net_per_ORIGINAL_candidate"]))
    print("POOL BEST NET CELL %s gross %+.5f net %+.5f" % (bn[0], bn[1]["gross"], bn[1]["net73"]))
    print("STOP HIT RATE BY WIDTH:", json.dumps(res["STOP_HIT_RATE_BY_WIDTH"]))


if __name__ == "__main__":
    main()
