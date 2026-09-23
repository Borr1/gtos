#!/usr/bin/env python3
"""e6_final — the equal-exposure control across all five months, and the bankability search.

 F1  EQUAL-EXPOSURE CONTROL. l8 ran this on January only. Resolve every candidate inside a fixed
     H-bar window measured from its OWN fill bar, discarding any whose window does not fit before
     the 2 h wall. Equal exposure, equal wall distance -> the bar-1 penalty cannot be a
     measurement artifact of the wall if it survives.
 F2  BANKABILITY SEARCH. Is there ANY cell where the retained (k>=2) book is POSITIVE net of
     spread-corrected cost, in all five months independently? That is the difference between
     "recovers a deficit" and "is an edge".
"""
import collections, gzip, json, os, sys

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import e6_build_month as B

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY"]
OUT = os.path.join(D, "E6_FINAL_V1.json")
TOL = B.TOL


def paths_for(month):
    """Re-stream the R paths so the equal-exposure control can walk bounded windows."""
    cfg = B.MONTHS[month]
    filt = cfg.get("filt")
    sidecar = {}
    if cfg["sidecar"]:
        with gzip.open(cfg["sidecar"], "rt") as fh:
            for line in fh:
                s = json.loads(line)
                sidecar[(s["candidate_id"], s["decision_time_utc"])] = s["ordered_path_observations"]
    with gzip.open(cfg["pool"], "rt") as fh:
        for line in fh:
            r = json.loads(line)
            if filt is not None and not filt(r):
                continue
            entry = r.get("entry_price"); stop = r.get("stop_loss")
            side = r.get("side") or r.get("direction")
            if entry is None or stop is None or side is None:
                continue
            rd = abs(entry - stop)
            if rd <= 0:
                continue
            b = B.load_bars(cfg["bars"], r["symbol"])
            obs = sidecar.get((r["candidate_id"], r["decision_time_utc"]))
            if obs is None:
                if b is None:
                    continue
                obs = B.bars_after(b, r["decision_time_utc"])
                if not obs:
                    continue
            fav, adv, cls = B.rpath(obs, entry, rd, side)
            mkt = B.anchor_mkt_r(b, r["decision_time_utc"], entry, rd, side) if b is not None else None
            yield {"fav": fav, "adv": adv, "cls": cls, "born": B.born_state(mkt), "month": month}


def equal_exposure():
    """resWin inside an H-bar window from the fill, bar-1 cohort vs later cohort."""
    HS = [15, 30, 45, 60, 90]
    agg = {H: {"b1": [0, 0], "later": [0, 0]} for H in HS}      # [target, resolved]
    per_month = {m: {H: {"b1": [0, 0], "later": [0, 0]} for H in HS} for m in MONTHS}
    means = {H: {"b1": [], "later": []} for H in HS}
    n_used = 0
    for m in MONTHS:
        for p in paths_for(m):
            if p["born"] == "born_past_stop":
                continue
            fav, adv, cls = p["fav"], p["adv"], p["cls"]
            nb = len(fav)
            start = None
            for i in range(nb):
                if adv[i] <= TOL:
                    start = i; break
            if start is None:
                continue
            n_used += 1
            grp = "b1" if start == 0 else "later"
            for H in HS:
                if start + H > nb:                       # window does not fit before the wall
                    continue
                bt = bs = -1
                for i in range(start, start + H):
                    if bt < 0 and fav[i] >= 2.0 - TOL: bt = i + 1
                    if bs < 0 and adv[i] <= -1.0 + TOL: bs = i + 1
                    if bt > 0 and bs > 0: break
                if bs > 0 and (bt <= 0 or bs <= bt):
                    v, hit = -1.0, 0
                elif bt > 0:
                    v, hit = 2.0, 1
                else:
                    v, hit = cls[start + H - 1], None
                if hit is not None:
                    agg[H][grp][1] += 1; agg[H][grp][0] += hit
                    per_month[m][H][grp][1] += 1; per_month[m][H][grp][0] += hit
                means[H][grp].append(v)
    out = {"n_filled_used": n_used, "pooled": {}, "by_month": {}}
    for H in HS:
        b1t, b1n = agg[H]["b1"]; lt, ln = agg[H]["later"]
        out["pooled"]["H%d" % H] = {
            "bar1_eligible": b1n, "bar1_resWin": round(b1t / b1n, 4) if b1n else None,
            "later_eligible": ln, "later_resWin": round(lt / ln, 4) if ln else None,
            "ratio": round((lt / ln) / (b1t / b1n), 4) if (b1n and ln and b1t) else None,
            "bar1_mean_R": round(sum(means[H]["b1"]) / len(means[H]["b1"]), 5) if means[H]["b1"] else None,
            "later_mean_R": round(sum(means[H]["later"]) / len(means[H]["later"]), 5) if means[H]["later"] else None}
    for m in MONTHS:
        out["by_month"][m] = {}
        for H in HS:
            b1t, b1n = per_month[m][H]["b1"]; lt, ln = per_month[m][H]["later"]
            out["by_month"][m]["H%d" % H] = {
                "bar1_resWin": round(b1t / b1n, 4) if b1n else None,
                "later_resWin": round(lt / ln, 4) if ln else None,
                "ratio": round((lt / ln) / (b1t / b1n), 4) if (b1n and ln and b1t) else None}
    return out


def bankability():
    """Net-of-corrected-cost economics of the RETAINED book, by cell, with 5-month agreement."""
    rows = []
    for m in MONTHS:
        with gzip.open(os.path.join(D, "e6_MECH_%s.jsonl.gz" % m), "rt") as fh:
            for l in fh:
                r = json.loads(l)
                if r["born"] == "born_past_stop":
                    continue
                rows.append(r)

    def net(r, div=7.3):
        c = r.get("cost_r"); sp = r.get("spread_r")
        if c is None: return None
        if sp is not None: c = c - sp + sp / div
        return r["hr"] - c

    kept = [r for r in rows if r["fb"] > 1]
    for r in rows:
        r["_net"] = net(r)
    axes = {"family": lambda r: r["fam"], "symbol": lambda r: r["sym"],
            "session": lambda r: r["sess"], "born": lambda r: r["born"],
            "family_x_born": lambda r: "%s|%s" % (r["fam"], r["born"])}
    out = {"n_kept": len(kept), "cells": {}}
    for ax, fn in axes.items():
        g = collections.defaultdict(list)
        for r in kept:
            if r["_net"] is not None:
                g[str(fn(r))].append(r)
        tab = {}
        for v, sub in g.items():
            if len(sub) < 300: continue
            vs = [r["_net"] for r in sub]
            n = len(vs); mn = sum(vs) / n
            sd = (sum((x - mn) ** 2 for x in vs) / (n - 1)) ** 0.5
            bym = {}
            for m in MONTHS:
                s2 = [r["_net"] for r in sub if r["month"] == m]
                bym[m] = round(sum(s2) / len(s2), 5) if s2 else None
            npos = sum(1 for m in MONTHS if bym[m] is not None and bym[m] > 0)
            tab[v] = {"n": n, "net_R_per_trade": round(mn, 5),
                      "t": round(mn / (sd / n ** 0.5), 3) if sd else 0.0,
                      "months_positive": npos, "by_month": bym}
        out["cells"][ax] = dict(sorted(tab.items(), key=lambda kv: -kv[1]["net_R_per_trade"])[:12])
    return out


def main():
    res = {}
    print("=== F1 EQUAL-EXPOSURE CONTROL (all five months, clean, fixed H bars from own fill) ===")
    ee = equal_exposure()
    res["F1_equal_exposure"] = ee
    print("%-6s %12s %12s %12s %12s %8s %12s %12s" % ("H", "b1_elig", "b1_resWin", "later_elig", "later_resWin", "ratio", "b1_meanR", "later_meanR"))
    for k, v in ee["pooled"].items():
        print("%-6s %12d %12s %12d %12s %8s %+12s %+12s" % (
            k, v["bar1_eligible"], v["bar1_resWin"], v["later_eligible"], v["later_resWin"],
            v["ratio"], v["bar1_mean_R"], v["later_mean_R"]))
    print("\nH30 ratio by month:", {m: ee["by_month"][m]["H30"]["ratio"] for m in MONTHS})
    print("H60 ratio by month:", {m: ee["by_month"][m]["H60"]["ratio"] for m in MONTHS})

    print("\n=== F2 BANKABILITY: retained book (fb>=2) net of 7.3x-corrected spread ===")
    bk = bankability()
    res["F2_bankability"] = bk
    print("n_kept=%d" % bk["n_kept"])
    for ax in ["family", "born", "symbol", "family_x_born"]:
        print("-- %s (top by net R/trade) --" % ax)
        print("%-40s %7s %12s %8s %8s" % ("cell", "n", "net/trade", "t", "mo>0"))
        for v, b in list(bk["cells"][ax].items())[:8]:
            print("%-40s %7d %+12.5f %+8.2f %5d/5" % (v[:40], b["n"], b["net_R_per_trade"], b["t"], b["months_positive"]))
    json.dump(res, open(OUT, "w"), indent=1)
    print("->", OUT)


if __name__ == "__main__":
    main()
