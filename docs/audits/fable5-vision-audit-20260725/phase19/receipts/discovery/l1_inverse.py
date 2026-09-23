#!/usr/bin/env python3
"""l1 pass 13 — price the INVERSE of the negatively-signed families.

Three families carry significantly negative DIRECTION-NEUTRAL signal (displacement_continuation
t -4.60 on n 4,469; session_open_range_break t -3.06 on n 987; volatility_compression_expansion
t -2.82 on n 605).  A negative signal is an edge with the sign flipped, which is the shape CQ's
inverted-breaker candidate was built from -- so it is measured here, not inferred.

Restricted to `born_at_limit` rows, where entry_price EQUALS the decision-instant market price
(mkt_r_prev_close == 0.0 exactly, 14,911 of 27,658).  On those and only those rows the inverse is
unambiguously a market order at the same price, so the R path can be reflected exactly:

    fav' = -adv     adv' = -fav     cls' = -cls

On any other born state the inverse would rest on the opposite side of the book and the fill would
not be comparable, so those rows are excluded rather than assumed.
Costs are charged symmetrically (spread/commission/slippage/swap do not care about direction).
"""
from __future__ import annotations
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import w0_ws  # noqa
from l1_lib import load, mean, q, TOUCH  # noqa

OUT = os.path.join(HERE, "l1_INVERSE_V1.json")


def corrected(r):
    return (r["spread_r"] or 0.0) / 7.3 + (r["commission_r"] or 0.0) + (r["slip_r"] or 0.0) + (r["swap_r"] or 0.0)


def walk(fav, adv, cls, T, S):
    n = len(fav)
    for i in range(n):
        if adv[i] <= -S + 1e-12:
            return -S
        if T is not None and fav[i] >= T - 1e-12:
            return T
    return cls[n - 1]


def ms(xs):
    n = len(xs)
    m = sum(xs) / n
    v = sum((x - m) ** 2 for x in xs) / (n - 1) if n > 1 else 0.0
    return m, (v / n) ** 0.5, n


def main():
    meta = {}
    for r in load(TOUCH):
        meta[(r["candidate_id"], r["decision_time_utc"])] = r
    acc = {}
    for rp in w0_ws.iter_rpaths():
        k = (rp["candidate_id"], rp["decision_time_utc"])
        m = meta.get(k)
        if m is None or m["born"] != "born_at_limit":
            continue
        fav, adv, cls = rp["fav"], rp["adv"], rp["cls"]
        ifav = [-x for x in adv]
        iadv = [-x for x in fav]
        icls = [-x for x in cls]
        c = corrected(m)
        row = {"fam": m["family"], "side": m["side"], "day": int(k[1][8:10]), "c": c,
               "fwd_drift": cls[-1], "inv_drift": icls[-1],
               "fwd_T2S1": walk(fav, adv, cls, 2.0, 1.0), "inv_T2S1": walk(ifav, iadv, icls, 2.0, 1.0),
               "fwd_T075S3": walk(fav, adv, cls, 0.75, 3.0), "inv_T075S3": walk(ifav, iadv, icls, 0.75, 3.0),
               "fwd_T3S1": walk(fav, adv, cls, 3.0, 1.0), "inv_T3S1": walk(ifav, iadv, icls, 3.0, 1.0)}
        acc.setdefault(m["family"], []).append(row)
    allrows = [r for v in acc.values() for r in v]
    res = {"population": "born_at_limit only (entry_price == decision price exactly)",
           "n": len(allrows),
           "note": "inverse is the exact reflection of the same M1 path; costs charged symmetrically"}

    def blk(rows):
        out = {"n": len(rows)}
        for tag in ("drift", "T2S1", "T075S3", "T3S1"):
            for d in ("fwd", "inv"):
                key = "%s_%s" % (d, tag)
                g = [r[key] for r in rows]
                net = [r[key] - r["c"] for r in rows]
                mg, _, _ = ms(g)
                mn, se, n = ms(net)
                out["%s_%s_gross" % (d, tag)] = round(mg, 5)
                out["%s_%s_net" % (d, tag)] = round(mn, 5)
                out["%s_%s_net_t" % (d, tag)] = round(mn / se, 3) if se > 0 else None
        # direction-neutral signal on the inverse at the declared contract
        L = [r["inv_T2S1"] - r["c"] for r in rows if r["side"] == "LONG"]
        S = [r["inv_T2S1"] - r["c"] for r in rows if r["side"] == "SHORT"]
        if len(L) >= 30 and len(S) >= 30:
            mL, sL, _ = ms(L)
            mS, sS, _ = ms(S)
            se = 0.5 * ((sL ** 2 + sS ** 2) ** 0.5)
            out["inv_T2S1_net_SIGNAL"] = round((mL + mS) / 2, 5)
            out["inv_T2S1_net_SIGNAL_t"] = round(((mL + mS) / 2) / se, 3) if se > 0 else None
            out["inv_T2S1_net_DIRECTION"] = round((mL - mS) / 2, 5)
        # date split on the inverse declared contract, net
        tr = [r["inv_T2S1"] - r["c"] for r in rows if r["day"] <= 15]
        te = [r["inv_T2S1"] - r["c"] for r in rows if r["day"] >= 16]
        out["inv_T2S1_net_train"] = round(mean(tr), 5) if len(tr) >= 30 else None
        out["inv_T2S1_net_test"] = round(mean(te), 5) if len(te) >= 30 else None
        out["n_train"] = len(tr); out["n_test"] = len(te)
        out["mean_cost73"] = round(mean(r["c"] for r in rows), 5)
        return out

    res["POOL"] = blk(allrows)
    res["by_family"] = {f: blk(v) for f, v in sorted(acc.items()) if len(v) >= 60}
    with open(OUT, "w") as fh:
        json.dump(res, fh, indent=1)

    p = res["POOL"]
    print("born_at_limit n=%d meancost73 %.4f" % (p["n"], p["mean_cost73"]))
    print("POOL  fwd drift %+.4f / inv drift %+.4f | fwd T2S1 net %+.4f (t%s) / INV T2S1 net %+.4f (t%s)"
          % (p["fwd_drift_gross"], p["inv_drift_gross"], p["fwd_T2S1_net"], p["fwd_T2S1_net_t"],
             p["inv_T2S1_net"], p["inv_T2S1_net_t"]))
    print("POOL  INV signal %+.5f (t %s) direction %+.5f | train %+.4f test %+.4f"
          % (p["inv_T2S1_net_SIGNAL"], p["inv_T2S1_net_SIGNAL_t"], p["inv_T2S1_net_DIRECTION"],
             p["inv_T2S1_net_train"], p["inv_T2S1_net_test"]))
    print("--- per family: INVERSE at the declared T2/S1, net of corrected cost ---")
    for f, b in sorted(res["by_family"].items(), key=lambda kv: -kv[1]["inv_T2S1_net"]):
        print("  %-32s n%5d cost %.3f | FWD net %+.4f | INV net %+.4f (t%7s) SIG %s (t%s) | tr %+.4f te %+.4f"
              % (f[:32], b["n"], b["mean_cost73"], b["fwd_T2S1_net"], b["inv_T2S1_net"],
                 b["inv_T2S1_net_t"], b.get("inv_T2S1_net_SIGNAL"), b.get("inv_T2S1_net_SIGNAL_t"),
                 b["inv_T2S1_net_train"] or 0, b["inv_T2S1_net_test"] or 0))
    print("--- INVERSE at T3/S1 and T0.75/S3 (net) ---")
    for f, b in sorted(res["by_family"].items(), key=lambda kv: -kv[1]["inv_T3S1_net"]):
        print("  %-32s n%5d INV T3S1 %+.4f (t%7s) | INV T0.75S3 %+.4f (t%s)"
              % (f[:32], b["n"], b["inv_T3S1_net"], b["inv_T3S1_net_t"],
                 b["inv_T075S3_net"], b["inv_T075S3_net_t"]))


if __name__ == "__main__":
    main()
