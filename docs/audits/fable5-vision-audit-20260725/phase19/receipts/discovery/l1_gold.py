#!/usr/bin/env python3
"""l1 pass 11 — is the XAUUSD find an exit-geometry finding or a January-gold-direction bet?

Splits it by side, born state and family, and then applies ONE fixed shape
(T=0.75 / S=3.00 -- chosen once, not fitted per symbol) across all 24 symbols so the
multiplicity of the per-symbol table is a single cell choice.
"""
from __future__ import annotations
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from l1_lib import *  # noqa

OUT = os.path.join(HERE, "l1_GOLD_V1.json")


def corrected(r):
    return (r["spread_r"] or 0.0) / 7.3 + (r["commission_r"] or 0.0) + (r["slip_r"] or 0.0) + (r["swap_r"] or 0.0)


def blk(rows, T, S):
    if not rows:
        return None
    n = len(rows)
    g = [cell(r, T, S, "r")[0] for r in rows]
    net = [g[i] - rows[i]["_c"] for i in range(n)]
    m = sum(net) / n
    sd = (sum((x - m) ** 2 for x in net) / (n - 1)) ** 0.5 if n > 1 else 0.0
    se = sd / (n ** 0.5) if n > 1 else 0.0
    days = {}
    for i, r in enumerate(rows):
        days.setdefault(r["_day"], []).append(net[i])
    return {"n": n, "gross": round(sum(g) / n, 5), "net": round(m, 5),
            "t": round(m / se, 3) if se > 0 else None,
            "win": round(sum(1 for x in g if x > 0) / n, 5),
            "n_days": len(days),
            "days_pos": sum(1 for v in days.values() if sum(v) > 0),
            "mean_2h_drift": round(mean(r["cls_end"] for r in rows if r.get("tf_r") is not None), 5)}


def main():
    recs = pop(load(), "TAKEABLE")
    for r in recs:
        r["_c"] = corrected(r)
        r["_day"] = int(r["decision_time_utc"][8:10])
    T, S = 0.75, 3.00
    res = {"fixed_shape": {"T": T, "S": S},
           "note": "ONE cell, chosen once from the fit-and-test survivors, applied unfitted "
                   "to every stratum below. The per-symbol table therefore carries one look, "
                   "not 24."}
    xau = [r for r in recs if r["symbol"] == "XAUUSD"]
    res["XAUUSD"] = {"ALL": blk(xau, T, S), "ALL_declared": blk(xau, 2.0, 1.0)}
    for dim, kf in (("side", lambda r: r["side"]),
                    ("born", lambda r: r["born"]),
                    ("family", lambda r: r["family"]),
                    ("side_born", lambda r: "%s|%s" % (r["side"], r["born"]))):
        d = {}
        g = {}
        for r in xau:
            g.setdefault(kf(r), []).append(r)
        for k, v in sorted(g.items(), key=str):
            if len(v) >= 30:
                d[str(k)] = {"shape": blk(v, T, S), "declared": blk(v, 2.0, 1.0)}
        res["XAUUSD_by_" + dim] = d
    # one fixed shape across all symbols
    sym = {}
    g = {}
    for r in recs:
        g.setdefault(r["symbol"], []).append(r)
    for k, v in sorted(g.items()):
        if len(v) >= 60:
            sym[k] = {"shape": blk(v, T, S), "declared": blk(v, 2.0, 1.0)}
    res["ALL_SYMBOLS_fixed_shape"] = sym
    pos = [k for k, v in sym.items() if v["shape"]["net"] > 0]
    res["symbols_net_positive_at_fixed_shape"] = pos
    res["n_symbols_tested"] = len(sym)
    # and the same fixed shape split LONG/SHORT per symbol, for the top few
    ls = {}
    for k, v in sorted(g.items()):
        if len(v) < 60:
            continue
        L = [r for r in v if r["side"] == "LONG"]
        H = [r for r in v if r["side"] == "SHORT"]
        ls[k] = {"LONG": blk(L, T, S) if len(L) >= 30 else None,
                 "SHORT": blk(H, T, S) if len(H) >= 30 else None}
    res["ALL_SYMBOLS_fixed_shape_by_side"] = ls
    with open(OUT, "w") as fh:
        json.dump(res, fh, indent=1)

    a = res["XAUUSD"]["ALL"]; b = res["XAUUSD"]["ALL_declared"]
    print("XAUUSD  shape T0.75/S3.00 n%d net %+.4f t %s win %.3f days %d/%d drift2h %+.4f"
          % (a["n"], a["net"], a["t"], a["win"], a["days_pos"], a["n_days"], a["mean_2h_drift"]))
    print("XAUUSD  declared T2/S1    n%d net %+.4f t %s win %.3f days %d/%d"
          % (b["n"], b["net"], b["t"], b["win"], b["days_pos"], b["n_days"]))
    for dim in ("side", "born", "family"):
        print("--- XAUUSD by %s (shape | declared) ---" % dim)
        for k, v in res["XAUUSD_by_" + dim].items():
            s, d = v["shape"], v["declared"]
            print("  %-30s n%5d shape %+.4f t%6s win %.3f drift %+.4f | declared %+.4f"
                  % (k[:30], s["n"], s["net"], s["t"], s["win"], s["mean_2h_drift"], d["net"]))
    print("--- ALL SYMBOLS at the ONE fixed shape (sorted by net) ---")
    for k, v in sorted(sym.items(), key=lambda kv: -kv[1]["shape"]["net"]):
        s, d = v["shape"], v["declared"]
        L = ls[k]["LONG"]; H = ls[k]["SHORT"]
        print("  %-12s n%5d shape %+.4f t%7s win %.3f | declared %+.4f | L %s S %s"
              % (k, s["n"], s["net"], s["t"], s["win"], d["net"],
                 ("%+.4f/n%d" % (L["net"], L["n"])) if L else "-",
                 ("%+.4f/n%d" % (H["net"], H["n"])) if H else "-"))
    print("net-positive at the fixed shape: %d of %d symbols: %s" % (len(pos), len(sym), ",".join(pos)))


if __name__ == "__main__":
    main()
