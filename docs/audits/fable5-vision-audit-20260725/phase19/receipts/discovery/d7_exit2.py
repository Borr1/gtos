#!/usr/bin/env python3
"""d7 stage 5 — the exit-geometry surface, extended, WITH the paired side placebo.

Stage 4 found the exit surface's best cell is worth +0.083 R/trade of gross over the
shipped geometry. This wave has already killed three headline results that turned out to
be reproducible by a coin flip, so the same control is applied here: PLACEBO-SIDE keeps
every row, every fill instant and every risk distance and only flips the direction of the
walk (adverse <-> favourable). If the placebo gains the same amount, the exit lever is a
property of the payoff contract, not of the signal.

Also extends the grid past stage 4's corner to test whether the optimum is interior.
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
POI_DEFECT = "current_breaker_re_entry"
WIN = {"2025-10": "202510", "2025-11": "202511", "2025-12": "202512",
       "2026-04": "202604", "2026-05": "202605"}
NEXT = {"2025-10": "202511", "2025-11": "202512", "2025-12": "202601",
        "2026-04": "202605", "2026-05": "202606"}

XS = [1.00, 0.75, 0.50, 0.426, 0.30, 0.20, 0.15, 0.10]
TRS = [1.0, 1.5, 2.0, 3.0, 5.0, 8.0, 12.0]
days = json.load(open(os.path.join(HERE, "f1_ARM_TRADING_DAYS_V1.json")))
NX, NY = len(XS), len(TRS)


def cell_r(radv, rfav, endr, x, tr):
    ia = int(np.searchsorted(radv, x, side="left"))
    it = int(np.searchsorted(rfav, tr, side="left"))
    if ia < radv.size and (it >= rfav.size or ia <= it):
        return -x
    if it < rfav.size:
        return tr
    return endr


def run_window(w):
    ok = set(days[w])
    rr = []
    for f in sorted(glob.glob(f"/tmp/f1/roster_{WIN[w]}/*.jsonl.gz")):
        with gzip.open(f, "rt") as fh:
            for line in fh:
                r = json.loads(line)
                if r["k"] != 15 or r["t"][:10] not in ok or r["f"] == POI_DEFECT:
                    continue
                rr.append(r)
    syms = sorted({r["s"] for r in rr})
    mons = [WIN[w]] + ([NEXT[w]] if NEXT.get(w) else [])
    tape = E.Tape(syms, mons)
    cm = E.CostModel()
    GR = np.zeros((NX, NY)); GP = np.zeros((NX, NY)); N = 0
    # per-day accumulation for a day-block bootstrap at every cell
    daykeys = []
    dayR = {}; dayP = {}; dayN = {}
    COST = 0.0
    for r in rr:
        sym = r["s"]; e = r["e"]; sl = r["sl"]; long = (r["d"] == "L")
        d = abs(e - sl)
        if not (d > 0):
            continue
        i = tape.idx(r["t"])
        a = i; b = min(a + HOR, tape.n)
        if a >= b:
            continue
        hi = tape.h[sym][a:b]; lo = tape.l[sym][a:b]; cl = tape.c[sym][a:b]
        m = ~np.isnan(cl)
        if not m.any():
            continue
        hi = hi[m]; lo = lo[m]; cl = cl[m]
        touched = (lo <= e) if long else (hi >= e)
        if not touched.any():
            continue
        j = int(np.argmax(touched))
        hi = hi[j + 1:]; lo = lo[j + 1:]; cl = cl[j + 1:]
        if hi.size == 0:
            continue
        if long:
            adv = (e - lo) / d; fav = (hi - e) / d; endr = (cl[-1] - e) / d
        else:
            adv = (hi - e) / d; fav = (e - lo) / d; endr = (e - cl[-1]) / d
        radv = np.maximum.accumulate(adv); rfav = np.maximum.accumulate(fav)
        # PLACEBO-SIDE: same rows, same fill bar, same risk distance, direction flipped
        padv, pfav, pend = rfav, radv, -endr
        px, _ = cm.cost_px(sym, r["t"], e, long, hold_min=HOR)
        COST += px / d
        N += 1
        dk = r["t"][:10]
        if dk not in dayN:
            dayN[dk] = 0; dayR[dk] = np.zeros((NX, NY)); dayP[dk] = np.zeros((NX, NY))
            daykeys.append(dk)
        dayN[dk] += 1
        for xi, x in enumerate(XS):
            for yi, tr in enumerate(TRS):
                vr = cell_r(radv, rfav, endr, x, tr)
                vp = cell_r(padv, pfav, pend, x, tr)
                GR[xi, yi] += vr; GP[xi, yi] += vp
                dayR[dk][xi, yi] += vr; dayP[dk][xi, yi] += vp
    return dict(window=w, n=N, cost=COST, GR=GR, GP=GP,
                dayR={k: v for k, v in dayR.items()}, dayP=dayP, dayN=dayN, daykeys=daykeys)


def main():
    parts = [run_window(w) for w in WIN]
    for p in parts:
        print("done", p["window"], p["n"], file=sys.stderr, flush=True)
    N = sum(p["n"] for p in parts)
    C = sum(p["cost"] for p in parts) / N
    GR = sum(p["GR"] for p in parts) / N
    GP = sum(p["GP"] for p in parts) / N
    # day-block bootstrap on real - placebo at every cell
    allday = []
    for p in parts:
        for k in p["daykeys"]:
            allday.append((p["dayR"][k], p["dayP"][k], p["dayN"][k]))
    rng = np.random.default_rng(11)
    D = len(allday)
    sumsR = np.stack([a for a, _, _ in allday]); sumsP = np.stack([b for _, b, _ in allday])
    cnts = np.array([c for _, _, c in allday], dtype=float)
    boot = np.zeros((1500, NX, NY))
    for t in range(1500):
        idx = rng.integers(0, D, D)
        boot[t] = (sumsR[idx].sum(axis=0) - sumsP[idx].sum(axis=0)) / cnts[idx].sum()
    lo = np.percentile(boot, 2.5, axis=0); hi = np.percentile(boot, 97.5, axis=0)
    grid = []
    for xi, x in enumerate(XS):
        for yi, tr in enumerate(TRS):
            grid.append({"x": x, "target_r": tr,
                         "gross_real": GR[xi, yi], "gross_placebo": GP[xi, yi],
                         "signal": GR[xi, yi] - GP[xi, yi],
                         "signal_ci95": [lo[xi, yi], hi[xi, yi]],
                         "net_real": GR[xi, yi] - C,
                         "placebo_share_of_gain": None})
    base = next(g for g in grid if g["x"] == 1.0 and g["target_r"] == 2.0)
    for g in grid:
        dr = g["gross_real"] - base["gross_real"]
        dp = g["gross_placebo"] - base["gross_placebo"]
        g["gain_vs_shipped_real"] = dr
        g["gain_vs_shipped_placebo"] = dp
        g["placebo_share_of_gain"] = (dp / dr) if abs(dr) > 1e-9 else None
    out = {"schema": "gtos.wave19.d7.stage5.v1", "windows": list(WIN),
           "n_filled": N, "toll_R": C, "n_day_blocks": D,
           "shipped_cell": {"x": 1.0, "target_r": 2.0, **{k: base[k] for k in
                            ("gross_real", "gross_placebo", "signal", "net_real")}},
           "grid": grid,
           "note": ("PLACEBO-SIDE is exactly paired: same rows, same fill bar, same risk "
                    "distance, same toll, adverse<->favourable swapped. 1500 day-block "
                    "bootstrap draws over all day blocks in the five windows.")}
    json.dump(out, open(os.path.join(OUT, "D7_STAGE5.json"), "w"), indent=1, default=float)
    print(f"n={N} toll={C:.5f}  shipped gross real {base['gross_real']:+.5f} "
          f"placebo {base['gross_placebo']:+.5f}")
    print("\nGROSS REAL")
    print(f"{'x':>6} " + " ".join(f"{'tr'+str(t):>9}" for t in TRS))
    for xi, x in enumerate(XS):
        print(f"{x:>6} " + " ".join(f"{GR[xi,yi]:>+9.5f}" for yi in range(NY)))
    print("\nGROSS PLACEBO-SIDE")
    for xi, x in enumerate(XS):
        print(f"{x:>6} " + " ".join(f"{GP[xi,yi]:>+9.5f}" for yi in range(NY)))
    print("\nSIGNAL (real - placebo)")
    for xi, x in enumerate(XS):
        print(f"{x:>6} " + " ".join(f"{GR[xi,yi]-GP[xi,yi]:>+9.5f}" for yi in range(NY)))
    print("\nPLACEBO SHARE OF THE GAIN OVER THE SHIPPED CELL")
    for xi, x in enumerate(XS):
        r = []
        for yi in range(NY):
            g = next(z for z in grid if z["x"] == x and z["target_r"] == TRS[yi])
            r.append("   n/a   " if g["placebo_share_of_gain"] is None
                     else f"{g['placebo_share_of_gain']*100:>8.1f}%")
        print(f"{x:>6} " + " ".join(r))


if __name__ == "__main__":
    main()
