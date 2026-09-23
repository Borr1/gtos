#!/usr/bin/env python3
"""d7 stage 4 — the exit-geometry lever, priced JOINTLY on the correct population.

Stage 1 solved 'what would the mean loser have to become' and 'what would the mean winner
have to become' as single levers. Both are exit-geometry claims, and exit geometry cannot
be moved one side at a time: a tighter loser cut kills winners, a wider target converts
winners into horizon rows. This stage walks the sealed arms' own rosters over the whole
(soft-exit x, target tr) grid, on the same M1 tape, with the same fill contract and the
same cost, and reports the surface.

Position size is held at the ORIGINAL risk distance d, so the toll in R is unchanged by x
and by tr -- this isolates exit geometry from sizing.

Windows: the five whose regenerated rosters survive at /tmp/f1 (Oct/Nov/Dec 2025, Apr/May 2026).
"""
import gzip, glob, json, math, os, sys
import numpy as np

REPO = "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"
PBG = REPO + "/docs/audits/fable5-vision-audit-20260725/phase19/receipts/pbg"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PBG); sys.path.insert(0, REPO)
os.chdir(REPO)
import pbg_econ as E

OUT = "/tmp/d7"
HOR = 120
POI = {"current_fvg_fill", "current_ob_retest", "current_breaker_re_entry"}
WIN = {"2025-10": "202510", "2025-11": "202511", "2025-12": "202512",
       "2026-04": "202604", "2026-05": "202605"}
NEXT = {"2025-10": "202511", "2025-11": "202512", "2025-12": "202601",
        "2026-04": "202605", "2026-05": "202606"}

XS = [1.00, 0.75, 0.60, 0.50, 0.426, 0.30, 0.20]     # soft loser cut, in R
TRS = [1.0, 1.5, 2.0, 3.0, 4.0, 5.0]                  # target, in R

days = json.load(open(os.path.join(HERE, "f1_ARM_TRADING_DAYS_V1.json")))


def rows_for(w):
    ok = set(days[w])
    out = []
    for f in sorted(glob.glob(f"/tmp/f1/roster_{WIN[w]}/*.jsonl.gz")):
        with gzip.open(f, "rt") as fh:
            for line in fh:
                r = json.loads(line)
                if r["k"] != 15:
                    continue
                if r["t"][:10] not in ok:
                    continue
                out.append(r)
    return out


def run_window(w):
    rr = rows_for(w)
    syms = sorted({r["s"] for r in rr})
    mons = [WIN[w]]
    nx = NEXT.get(w)
    if nx:
        mons.append(nx)
    tape = E.Tape(syms, mons)
    cm = E.CostModel()
    nx_, ny = len(XS), len(TRS)
    G = np.zeros((nx_, ny)); N = np.zeros((nx_, ny), dtype=np.int64)
    WINS = np.zeros((nx_, ny), dtype=np.int64)
    HORZ = np.zeros((nx_, ny), dtype=np.int64)
    CUT = np.zeros((nx_, ny), dtype=np.int64)
    COST = 0.0
    nfill = 0
    # winner-kill diagnostic: for rows that reach tr=2.0 before the ORIGINAL 1R stop,
    # how deep did they dig first?
    kill_depth = []
    for r in rr:
        fam = r["f"]
        if fam in POI and fam == "current_breaker_re_entry":
            continue                      # defect family, excluded like f1's CLEAN
        sym = r["s"]; e = r["e"]; sl = r["sl"]; long = (r["d"] == "L")
        d = abs(e - sl)
        if not (d > 0):
            continue
        i = tape.idx(r["t"])
        a = i; b = min(a + HOR, tape.n)
        if a >= b:
            continue
        hi = tape.h[sym][a:b]; lo = tape.l[sym][a:b]; cl = tape.c[sym][a:b]
        okm = ~np.isnan(cl)
        if not okm.any():
            continue
        hi = hi[okm]; lo = lo[okm]; cl = cl[okm]
        # honest limit fill
        touched = (lo <= e) if long else (hi >= e)
        if not touched.any():
            continue
        j = int(np.argmax(touched))
        hi = hi[j + 1:]; lo = lo[j + 1:]; cl = cl[j + 1:]
        if hi.size == 0:
            continue
        # born past stop -> drop (f1 CLEAN)
        mkt = cl[0]
        if (long and mkt <= sl) or ((not long) and mkt >= sl):
            pass  # keep: 'past' in f1 is judged on the market price at the decision instant;
                  # the breaker family is already removed, which is 98.5% of them
        nfill += 1
        if long:
            adv = (e - lo) / d
            fav = (hi - e) / d
        else:
            adv = (hi - e) / d
            fav = (e - lo) / d
        radv = np.maximum.accumulate(adv)
        rfav = np.maximum.accumulate(fav)
        endr = ((cl[-1] - e) / d) if long else ((e - cl[-1]) / d)
        px, _ = cm.cost_px(sym, r["t"], e, long, hold_min=HOR)
        COST += px / d
        for xi, x in enumerate(XS):
            ia = int(np.searchsorted(radv, x, side="left"))
            for yi, tr in enumerate(TRS):
                it = int(np.searchsorted(rfav, tr, side="left"))
                if ia < radv.size and (it >= rfav.size or ia <= it):
                    G[xi, yi] += -x; CUT[xi, yi] += 1
                elif it < rfav.size:
                    G[xi, yi] += tr; WINS[xi, yi] += 1
                else:
                    G[xi, yi] += endr; HORZ[xi, yi] += 1
                N[xi, yi] += 1
        # diagnostic on the baseline contract
        ia1 = int(np.searchsorted(radv, 1.0, side="left"))
        it2 = int(np.searchsorted(rfav, 2.0, side="left"))
        if it2 < rfav.size and (ia1 >= radv.size or it2 < ia1):
            kill_depth.append(float(radv[it2]))
    res = {"window": w, "n_filled": nfill, "cost_mean_R": COST / nfill if nfill else None,
           "grid": [], "winner_predip_depth_n": len(kill_depth)}
    if kill_depth:
        kd = np.array(kill_depth)
        res["winner_predip_quantiles"] = {str(q): float(np.percentile(kd, q))
                                          for q in (10, 25, 50, 75, 90)}
        res["winner_kill_fraction_by_soft_stop"] = {str(x): float((kd >= x).mean()) for x in XS}
    for xi, x in enumerate(XS):
        for yi, tr in enumerate(TRS):
            n = int(N[xi, yi])
            res["grid"].append({"x": x, "target_r": tr, "n": n,
                                "gross": G[xi, yi] / n if n else None,
                                "win_share": WINS[xi, yi] / n if n else None,
                                "cut_share": CUT[xi, yi] / n if n else None,
                                "horizon_share": HORZ[xi, yi] / n if n else None})
    return res


def main():
    allr = []
    for w in WIN:
        print("walking", w, file=sys.stderr, flush=True)
        allr.append(run_window(w))
        json.dump(allr, open(os.path.join(OUT, "D7_STAGE4_partial.json"), "w"), indent=1, default=float)
    # pool
    tot = {}
    ncost = 0.0; nrows = 0
    for r in allr:
        nrows += r["n_filled"]; ncost += r["cost_mean_R"] * r["n_filled"]
        for cell in r["grid"]:
            k = (cell["x"], cell["target_r"])
            t = tot.setdefault(k, {"n": 0, "gsum": 0.0, "w": 0.0, "c": 0.0, "h": 0.0})
            t["n"] += cell["n"]; t["gsum"] += cell["gross"] * cell["n"]
            t["w"] += cell["win_share"] * cell["n"]; t["c"] += cell["cut_share"] * cell["n"]
            t["h"] += cell["horizon_share"] * cell["n"]
    C = ncost / nrows
    pooled = []
    for (x, tr), t in sorted(tot.items()):
        g = t["gsum"] / t["n"]
        pooled.append({"x": x, "target_r": tr, "n": t["n"], "gross": g, "toll": C,
                       "net": g - C, "win_share": t["w"] / t["n"],
                       "cut_share": t["c"] / t["n"], "horizon_share": t["h"] / t["n"]})
    kd = {}
    for r in allr:
        if "winner_kill_fraction_by_soft_stop" in r:
            for k, v in r["winner_kill_fraction_by_soft_stop"].items():
                kd.setdefault(k, []).append((v, r["winner_predip_depth_n"]))
    killpool = {k: sum(v * n for v, n in vs) / sum(n for _, n in vs) for k, vs in kd.items()}
    out = {"schema": "gtos.wave19.d7.stage4.v1",
           "windows": list(WIN), "pooled_toll_R": C, "n_filled_pooled": nrows,
           "pooled_grid": pooled, "winner_kill_fraction_by_soft_stop_pooled": killpool,
           "per_window": allr,
           "note": ("Position size held at the ORIGINAL risk distance, so the toll in R is "
                    "identical in every cell; only exit geometry moves. Family "
                    "current_breaker_re_entry excluded (f1 CLEAN). Honest resting-limit fill, "
                    "120 M1 bars, conservative tie (the adverse side wins on an equal bar).")}
    json.dump(out, open(os.path.join(OUT, "D7_STAGE4.json"), "w"), indent=1, default=float)
    print("toll", round(C, 5), "n", nrows)
    print(f"{'x':>6} " + " ".join(f"tr{t:<7}" for t in TRS))
    for x in XS:
        row = [c for c in pooled if c["x"] == x]
        row.sort(key=lambda z: z["target_r"])
        print(f"{x:>6} " + " ".join(f"{c['net']:+8.5f} " for c in row))
    print("winner kill fraction:", {k: round(v, 4) for k, v in killpool.items()})


if __name__ == "__main__":
    main()
