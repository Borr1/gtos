#!/usr/bin/env python3
"""l1 pass 12 — separate SIGNAL from DIRECTION.

Within a stratum, a market that moved by d over the window contributes +d to every LONG
and -d to every SHORT, while genuine predictive content s contributes +s to BOTH.  So

    signal    = (drift_LONG + drift_SHORT) / 2      direction-neutral
    direction = (drift_LONG - drift_SHORT) / 2      the month's move, not an edge

Applied to the 2-hour mark-to-market drift (no exit logic) and to the realized R of the
fixed shape.  This is the instrument that says whether the XAUUSD result is an edge or a
January gold rally.
"""
from __future__ import annotations
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from l1_lib import *  # noqa


OUT = os.path.join(HERE, "l1_SIGNAL_V1.json")


def corrected(r):
    return (r["spread_r"] or 0.0) / 7.3 + (r["commission_r"] or 0.0) + (r["slip_r"] or 0.0) + (r["swap_r"] or 0.0)


def ms(xs):
    n = len(xs)
    if n < 2:
        return None, None, n
    m = sum(xs) / n
    v = sum((x - m) ** 2 for x in xs) / (n - 1)
    return m, (v / n) ** 0.5, n


def decomp(rows, valf, min_n=30):
    L = [valf(r) for r in rows if r["side"] == "LONG"]
    S = [valf(r) for r in rows if r["side"] == "SHORT"]
    if len(L) < min_n or len(S) < min_n:
        return None
    mL, sL, nL = ms(L)
    mS, sS, nS = ms(S)
    sig = (mL + mS) / 2.0
    dir_ = (mL - mS) / 2.0
    se = 0.5 * ((sL ** 2 + sS ** 2) ** 0.5)
    return {"n_long": nL, "n_short": nS,
            "drift_long": round(mL, 5), "drift_short": round(mS, 5),
            "SIGNAL": round(sig, 5), "signal_se": round(se, 5),
            "signal_t": round(sig / se, 3) if se > 0 else None,
            "DIRECTION": round(dir_, 5), "direction_t": round(dir_ / se, 3) if se > 0 else None}


def main():
    recs = pop(load(), "TAKEABLE")
    recs = [r for r in recs if r.get("tf_r") is not None]
    for r in recs:
        r["_c"] = corrected(r)
    drift = lambda r: r["cls_end"]
    shape = lambda r: cell(r, 0.75, 3.00, "r")[0] - r["_c"]
    declared = lambda r: cell(r, 2.0, 1.0, "r")[0] - r["_c"]
    res = {"note": "signal = (LONG + SHORT)/2 is direction-neutral; direction = (LONG - SHORT)/2 "
                   "is the month's move. Both measured on the 2-hour mark-to-market drift and on "
                   "the realized net R of the fixed T0.75/S3.00 shape and the declared T2/S1."}
    for label, vf in (("DRIFT_2H", drift), ("NET_shape_T0.75_S3.00", shape), ("NET_declared_T2_S1", declared)):
        blk = {"POOL": decomp(recs, vf)}
        for dim, kf in (("family", lambda r: r["family"]),
                        ("symbol", lambda r: r["symbol"]),
                        ("born", lambda r: r["born"]),
                        ("session", lambda r: r["session"])):
            g = {}
            for r in recs:
                g.setdefault(kf(r), []).append(r)
            d = {}
            for k, v in sorted(g.items(), key=str):
                x = decomp(v, vf)
                if x:
                    d[str(k)] = x
            blk[dim] = d
        res[label] = blk
    # symbol-level signal estimates aggregated: how many symbols have SIGNAL > 0
    for label in ("DRIFT_2H", "NET_shape_T0.75_S3.00", "NET_declared_T2_S1"):
        syms = res[label]["symbol"]
        vals = [v["SIGNAL"] for v in syms.values()]
        res[label]["symbol_SUMMARY"] = {
            "n_symbols": len(syms),
            "n_signal_positive": sum(1 for x in vals if x > 0),
            "mean_signal": round(mean(vals), 5),
            "median_signal": round(q(vals, .5), 5),
            "n_signal_t_gt_2": sum(1 for v in syms.values() if (v["signal_t"] or 0) > 2),
            "n_direction_t_gt_2": sum(1 for v in syms.values() if abs(v["direction_t"] or 0) > 2),
        }
    with open(OUT, "w") as fh:
        json.dump(res, fh, indent=1)

    for label in ("DRIFT_2H", "NET_shape_T0.75_S3.00", "NET_declared_T2_S1"):
        p = res[label]["POOL"]
        s = res[label]["symbol_SUMMARY"]
        print("%-24s POOL L %+.4f S %+.4f -> SIGNAL %+.5f (t %s) DIRECTION %+.5f (t %s)"
              % (label, p["drift_long"], p["drift_short"], p["SIGNAL"], p["signal_t"],
                 p["DIRECTION"], p["direction_t"]))
        print("    symbols: %d, signal>0 %d, signal t>2 %d, |direction| t>2 %d, mean signal %+.5f"
              % (s["n_symbols"], s["n_signal_positive"], s["n_signal_t_gt_2"],
                 s["n_direction_t_gt_2"], s["mean_signal"]))
    print("--- DRIFT_2H by family (SIGNAL is the edge, DIRECTION is the month) ---")
    for k, v in sorted(res["DRIFT_2H"]["family"].items(), key=lambda kv: -kv[1]["SIGNAL"]):
        print("  %-32s nL%5d nS%5d L %+.4f S %+.4f SIGNAL %+.4f (t %6s) DIR %+.4f"
              % (k[:32], v["n_long"], v["n_short"], v["drift_long"], v["drift_short"],
                 v["SIGNAL"], v["signal_t"], v["DIRECTION"]))
    print("--- DRIFT_2H top/bottom symbols by SIGNAL ---")
    ss = sorted(res["DRIFT_2H"]["symbol"].items(), key=lambda kv: -kv[1]["SIGNAL"])
    for k, v in ss[:6] + ss[-4:]:
        print("  %-12s nL%5d nS%5d SIGNAL %+.4f (t %6s) DIRECTION %+.4f (t %s)"
              % (k, v["n_long"], v["n_short"], v["SIGNAL"], v["signal_t"], v["DIRECTION"], v["direction_t"]))
    print("--- NET_shape by born ---")
    for k, v in sorted(res["NET_shape_T0.75_S3.00"]["born"].items(), key=lambda kv: -kv[1]["SIGNAL"]):
        print("  %-20s SIGNAL %+.5f (t %6s) DIRECTION %+.5f" % (k, v["SIGNAL"], v["signal_t"], v["DIRECTION"]))


if __name__ == "__main__":
    main()
