"""h6 step 7 — THE HUNT. Every (instrument x contract x cost-gate x cancel-band) cell,
scored for edge:cost in BOTH denominations, with month stability and truncation share.

A cell "pays" when edge > cost. Two denominations, and they disagree:
    ratio_R   = mean(gross R) / mean(cost R)          <- what an R-sized book earns
    ratio_bps = mean(edge bps) / mean(cost bps)        <- the swarm's 9.4% headline basis

Emits h6_HUNT_V1.jsonl.gz (every cell with n >= 40) and H6_HUNT_TOP_V1.json.
"""
import gzip, json, os, sys, time

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import h6_lib as H  # noqa: E402

KS = [0, 1, 2, 3, 5, 8, 10, 15, 20, 30]
TRAILS = [None, 0.10, 0.15, 0.25, 0.40, 0.75]
TARGETS = [None, 2.0]
MAXBARS = [None, 60]
RG = [None, 0.10, 0.05, 0.03, 0.02, 0.015, 0.01]
BG = [None, 1.0, 0.7, 0.6]
BANDS = [("none", None, None), ("c0<=+0.05", None, 0.05), ("|c0|<=0.10", -0.10, 0.10)]
MONTHS = ("2026-01", "2026-02", "2026-03")


def main():
    t0 = time.time()
    P, M = H.load()
    cost = M["cost_true"]; bf = M["bpsfac"]
    fin = np.isfinite(cost)
    syms = sorted(set(M["symbol"].tolist()))
    sidx = {s: (M["symbol"] == s) for s in syms}
    midx = {m: (M["month"] == m) for m in MONTHS}
    gates = {}
    for g in RG:
        gates[("R", g)] = fin if g is None else (fin & (cost <= g + 1e-12))
    for g in BG:
        if g is None:
            continue
        gates[("bps", g)] = fin & (cost * bf <= g + 1e-12)

    out = gzip.open(f"{D}/h6_HUNT_V1.jsonl.gz", "wt")
    nw = 0
    ncontract = 0
    for k in KS:
        for tg in TARGETS:
            for tr in TRAILS:
                for mb in MAXBARS:
                    r, reason, _e, trd, c0 = H.walk_all(P, k=k, target=tg, stop=-1.0,
                                                        trail=tr, maxbars=mb)
                    trunc = (reason == 3) | (reason == 4)
                    ncontract += 1
                    for bn, blo, bhi in BANDS:
                        bm = trd.copy()
                        if blo is not None:
                            bm &= c0 >= blo - 1e-12
                        if bhi is not None:
                            bm &= c0 <= bhi + 1e-12
                        for (gk, gv), gm in gates.items():
                            pop = bm & gm
                            if not pop.any():
                                continue
                            for scope, sm in [("ALL", None)] + [(s, sidx[s]) for s in syms]:
                                sel = pop if sm is None else (pop & sm)
                                nn = int(sel.sum())
                                if nn < 40:
                                    continue
                                g_ = r[sel]; c_ = cost[sel]; b_ = bf[sel]
                                gmn = float(g_.mean()); cmn = float(c_.mean())
                                nt = g_ - c_
                                nmn = float(nt.mean())
                                nse = float(nt.std(ddof=1) / np.sqrt(nn)) if nn > 1 else np.nan
                                gse = float(g_.std(ddof=1) / np.sqrt(nn)) if nn > 1 else np.nan
                                eb = float((g_ * b_).mean()); cb = float((c_ * b_).mean())
                                rec = {"sym": scope, "k": k, "target": tg, "trail": tr,
                                       "maxbars": mb, "band": bn, "gk": gk, "gv": gv,
                                       "n": nn, "gross": round(gmn, 6),
                                       "cost": round(cmn, 6), "net": round(nmn, 6),
                                       "tn": round(nmn / nse, 3) if nse else None,
                                       "tg": round(gmn / gse, 3) if gse else None,
                                       "rr": round(gmn / cmn, 4) if cmn else None,
                                       "rb": round(eb / cb, 4) if cb else None,
                                       "eb": round(eb, 4), "cb": round(cb, 4),
                                       "trunc": round(float(trunc[sel].mean()), 4),
                                       "totR": round(float(nt.sum()), 3)}
                                mp = 0
                                for m in MONTHS:
                                    s2 = sel & midx[m]
                                    n2 = int(s2.sum())
                                    rec["n" + m[-2:]] = n2
                                    if n2:
                                        v = float((r[s2] - cost[s2]).mean())
                                        rec["nt" + m[-2:]] = round(v, 6)
                                        mp += (v > 0)
                                rec["months_pos"] = mp
                                out.write(json.dumps(rec) + "\n")
                                nw += 1
                    if ncontract % 20 == 0:
                        print(f"  contracts {ncontract}/{len(KS)*len(TARGETS)*len(TRAILS)*len(MAXBARS)}"
                              f" cells {nw} {time.time()-t0:.0f}s", flush=True)
    out.close()
    print("cells", nw, round(time.time() - t0, 1), flush=True)
    json.dump({"cells": nw, "contracts": ncontract, "seconds": round(time.time() - t0, 1),
               "ks": KS, "trails": TRAILS, "targets": TARGETS, "maxbars": MAXBARS,
               "gates_R": RG, "gates_bps": BG, "bands": [b[0] for b in BANDS],
               "symbols": syms},
              open(f"{D}/H6_HUNT_BUILD_V1.json", "w"), indent=1)


if __name__ == "__main__":
    main()
