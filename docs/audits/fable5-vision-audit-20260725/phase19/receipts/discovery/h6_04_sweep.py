"""h6 step 4 — JOINT sweep of the repaired contract's own parameters.

Full factorial over the exit/entry contract:
    k       x 16   entry re-timing (the cancel window), minutes after the decision
    trail   x 10   trailing-stop distance behind the running MFE
    target  x  6   take-profit
    stop    x  5   initial stop
    maxbars x  6   time stop
  = 28,800 contracts, each walked over all 43,755 live-expressible candidates.

Each contract is then scored on four cost-gate populations. Month-level splits are
carried so the optimum can be chosen on TRAIN and read on TEST.

Output: h6_SWEEP_V1.jsonl.gz (one record per contract x gate cell).
"""
import gzip, json, os, sys, time

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import h6_lib as H  # noqa: E402

KS = [0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 30, 45, 60]
TRAILS = [None, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.75, 1.00]
TARGETS = [None, 1.0, 1.5, 2.0, 3.0, 5.0]
STOPS = [-0.5, -0.75, -1.0, -1.5, -2.0]
MAXBARS = [None, 15, 30, 60, 90, 120]
GATES = {"ungated": (None, None),
         "shipped": (0.10, 0.15),
         "tot_le_005": (None, 0.05),
         "tot_le_002": (None, 0.02)}


def main():
    t0 = time.time()
    P, M = H.load()
    n = P["F"].shape[0]
    cost = M["cost_true"]
    bf = M["bpsfac"]
    fincost = np.isfinite(cost)
    month = M["month"]
    mmask = {m: (month == m) for m in ("2026-01", "2026-02", "2026-03")}
    gmask = {}
    for name, (gs, gt) in GATES.items():
        s = fincost.copy()
        if gs is not None:
            s &= M["spread_r"] <= gs + 1e-12
        if gt is not None:
            s &= cost <= gt + 1e-12
        gmask[name] = s
        print("gate", name, int(s.sum()), flush=True)

    out = gzip.open(f"{D}/h6_SWEEP_V1.jsonl.gz", "wt")
    ncfg = 0
    tot = len(KS) * len(TRAILS) * len(TARGETS) * len(STOPS) * len(MAXBARS)
    for k in KS:
        for st in STOPS:
            for tg in TARGETS:
                for tr in TRAILS:
                    for mb in MAXBARS:
                        r, reason, ebar, trd, c0 = H.walk_all(
                            P, k=k, target=tg, stop=st, trail=tr, maxbars=mb)
                        for gname, gm in gmask.items():
                            sel = trd & gm
                            nn = int(sel.sum())
                            if nn < 50:
                                continue
                            g = r[sel]; c = cost[sel]; nt = g - c
                            gm_ = float(g.mean()); nm = float(nt.mean())
                            gse = float(g.std(ddof=1) / np.sqrt(nn))
                            nse = float(nt.std(ddof=1) / np.sqrt(nn))
                            eb = float((g * bf[sel]).mean())
                            cb = float((c * bf[sel]).mean())
                            rec = {"k": k, "trail": tr, "target": tg, "stop": st,
                                   "maxbars": mb, "gate": gname, "n": nn,
                                   "gross": round(gm_, 6), "cost": round(float(c.mean()), 6),
                                   "net": round(nm, 6),
                                   "tg": round(gm_ / gse, 3) if gse else None,
                                   "tn": round(nm / nse, 3) if nse else None,
                                   "eb": round(eb, 5), "cb": round(cb, 5),
                                   "rb": round(eb / cb, 5) if cb else None,
                                   "rr": round(gm_ / float(c.mean()), 5) if c.mean() else None,
                                   "trunc": round(float(((reason[sel] == 3) |
                                                         (reason[sel] == 4)).mean()), 5)}
                            for mn, mmk in mmask.items():
                                s2 = sel & mmk
                                n2 = int(s2.sum())
                                rec["n_" + mn[-2:]] = n2
                                if n2:
                                    rec["g_" + mn[-2:]] = round(float(r[s2].mean()), 6)
                                    rec["nt_" + mn[-2:]] = round(
                                        float((r[s2] - cost[s2]).mean()), 6)
                            out.write(json.dumps(rec) + "\n")
                        ncfg += 1
                        if ncfg % 500 == 0:
                            el = time.time() - t0
                            print(f"  {ncfg}/{tot} {el:.0f}s eta {el/ncfg*(tot-ncfg):.0f}s",
                                  flush=True)
    out.close()
    rec = {"contracts": ncfg, "gates": list(GATES), "seconds": round(time.time() - t0, 1),
           "ks": KS, "trails": TRAILS, "targets": TARGETS, "stops": STOPS,
           "maxbars": MAXBARS, "n_rows": n}
    print(json.dumps(rec), flush=True)
    json.dump(rec, open(f"{D}/H6_SWEEP_BUILD_V1.json", "w"), indent=1)


if __name__ == "__main__":
    main()
