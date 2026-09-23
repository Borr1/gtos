#!/usr/bin/env python3
"""l8_horizonmatch — DECISIVE CONTROL for the entry-delay finding.

Is the bar-1 fill penalty (a) genuine adverse selection, or (b) an artifact of the
bar-1 cohort having more exposure left before the hard 2-hour measurement wall?
Control: resolve EVERY cohort inside a FIXED H-bar window measured from its OWN fill bar,
and drop any candidate that cannot get a full H bars before the wall. Equal exposure,
equal wall distance."""
import json, os, collections
import l8_lib as L
from l8_sweepN import enrich2
import l8_grid as G

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "L8_HORIZONMATCH_V1.json")
TI, SI = G.TGT.index(2.0), G.STP.index(-1.0)


def resolve_h(l, H):
    """Resolve inside [fill_bar, fill_bar+H-1]; None if the window does not fit before the wall."""
    fb = l["fill_bar"]
    if fb < 0:
        return None
    end = fb + H - 1
    if end > l["n_bars"]:
        return None
    bt, bs = l["tfav"][TI], l["tadv"][SI]
    bt = bt if (0 < bt <= end) else -1
    bs = bs if (0 < bs <= end) else -1
    if bs > 0 and (bt <= 0 or bs <= bt):
        return (G.STP[SI], "stop")
    if bt > 0:
        return (G.TGT[TI], "target")
    return (None, "unresolved")


def agg(rows, H):
    out = []
    c = collections.Counter()
    for r in rows:
        z = resolve_h(r["_l"], H)
        if z is None:
            c["window_does_not_fit"] += 1
            continue
        v, o = z
        c[o] += 1
        out.append(0.0 if v is None else v)
    n = len(out)
    if n == 0:
        return None
    m = sum(out) / n
    res = c["target"] + c["stop"]
    return {"n_eligible": n, "excluded_no_window": c["window_does_not_fit"],
            "target": c["target"], "stop": c["stop"], "unresolved": c["unresolved"],
            "res_win": round(c["target"] / res, 4) if res else None, "n_res": res,
            "mean_treating_unresolved_as_0": round(m, 5),
            "target_rate": round(c["target"] / n, 4), "stop_rate": round(c["stop"] / n, 4)}


def main():
    rows = L.load()
    enrich2(rows)
    lad = G.load_ladder()
    for r in rows:
        r["_l"] = lad.get((r["cid"], r["dt"]))
        fb = r["_l"]["fill_bar"]
        r["fs"] = ("never" if fb < 0 else "bar1" if fb == 1 else "b2_5" if fb <= 5
                   else "b6_15" if fb <= 15 else "b16_60" if fb <= 60 else "b61_120")
    clean = [r for r in rows if r["born"] != "born_past_stop"]
    res = {"note": "equal-exposure control on the honest 2R/-1R contract", "H": {}}
    print("=== EQUAL-EXPOSURE CONTROL: resolution win rate inside a fixed H-bar window from the FILL bar ===")
    print("%4s %-9s %9s %9s %8s %8s %9s %9s" % ("H", "fillspeed", "eligible", "excluded", "tgt", "stop", "resWin", "meanR"))
    for H in (15, 30, 45, 60):
        res["H"][H] = {}
        for fs in ["bar1", "b2_5", "b6_15", "b16_60", "b61_120"]:
            sub = [r for r in clean if r["fs"] == fs]
            a = agg(sub, H)
            if not a or a["n_eligible"] < 40:
                continue
            res["H"][H][fs] = a
            print("%4d %-9s %9d %9d %8d %8d %9.4f %+9.5f" % (
                H, fs, a["n_eligible"], a["excluded_no_window"], a["target"], a["stop"],
                a["res_win"] or 0, a["mean_treating_unresolved_as_0"]))
        print()
    # same control, binary: bar1 vs later
    print("=== bar1 vs later, equal exposure ===")
    print("%4s %-8s %9s %8s %8s %9s %9s" % ("H", "cohort", "eligible", "tgt", "stop", "resWin", "meanR"))
    res["binary"] = {}
    for H in (15, 30, 45, 60, 90):
        res["binary"][H] = {}
        for name, pred in (("bar1", lambda r: r["fs"] == "bar1"), ("later", lambda r: r["fs"] not in ("bar1", "never"))):
            a = agg([r for r in clean if pred(r)], H)
            if a:
                res["binary"][H][name] = a
                print("%4d %-8s %9d %8d %8d %9.4f %+9.5f" % (
                    H, name, a["n_eligible"], a["target"], a["stop"], a["res_win"] or 0,
                    a["mean_treating_unresolved_as_0"]))
        print()
    json.dump(res, open(OUT, "w"), indent=1)


if __name__ == "__main__":
    main()
