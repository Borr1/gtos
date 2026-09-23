#!/usr/bin/env python3
"""d7 stage 6 — WHERE the negative directional signal lives.

Stage 5 found real - PLACEBO-SIDE is significantly NEGATIVE at all 56 exit-geometry cells.
Two candidate mechanisms, and they land on opposite axes of the wave's verdict:
  SIGNAL  — the setups call the wrong direction.
  USAGE   — the resting-limit entry convention systematically fills you into short-horizon
            momentum, so the mirror of any signal looks better once you condition on fill.
The discriminator is the family split: the POI families rest a limit away from the market,
the at-market families do not. f2 measured real-placebo = +0.00315 on at-market rows.
Also reported: per-family signal, and the fill-lag (bars from decision to fill) as the
direct measure of the conditioning.
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
DEFECT = "current_breaker_re_entry"
WIN = {"2025-10": "202510", "2025-11": "202511", "2025-12": "202512",
       "2026-04": "202604", "2026-05": "202605"}
NEXT = {"2025-10": "202511", "2025-11": "202512", "2025-12": "202601",
        "2026-04": "202605", "2026-05": "202606"}
CELLS = [(1.0, 2.0), (0.5, 2.0), (0.2, 5.0), (0.1, 12.0)]
days = json.load(open(os.path.join(HERE, "f1_ARM_TRADING_DAYS_V1.json")))


def cr(radv, rfav, endr, x, tr):
    ia = int(np.searchsorted(radv, x, side="left"))
    it = int(np.searchsorted(rfav, tr, side="left"))
    if ia < radv.size and (it >= rfav.size or ia <= it):
        return -x
    if it < rfav.size:
        return tr
    return endr


acc = {}     # (group, cell) -> [sum_real, sum_plac, n, sum_cost]
lag = {}     # group -> list of fill lags
dayacc = {}  # (day, group, cell) -> [r, p, n]


def add(gr, cell, vr, vp):
    k = (gr, cell)
    a = acc.setdefault(k, [0.0, 0.0, 0])
    a[0] += vr; a[1] += vp; a[2] += 1


for w in WIN:
    ok = set(days[w])
    rr = []
    for f in sorted(glob.glob(f"/tmp/f1/roster_{WIN[w]}/*.jsonl.gz")):
        with gzip.open(f, "rt") as fh:
            for line in fh:
                r = json.loads(line)
                if r["k"] == 15 and r["t"][:10] in ok:
                    rr.append(r)
    syms = sorted({r["s"] for r in rr})
    tape = E.Tape(syms, [WIN[w]] + ([NEXT[w]] if NEXT.get(w) else []))
    for r in rr:
        fam = r["f"]
        if fam == DEFECT:
            continue
        sym = r["s"]; e = r["e"]; sl = r["sl"]; long = (r["d"] == "L")
        d = abs(e - sl)
        if not (d > 0):
            continue
        i = tape.idx(r["t"]); a0 = i; b = min(a0 + HOR, tape.n)
        if a0 >= b:
            continue
        hi = tape.h[sym][a0:b]; lo = tape.l[sym][a0:b]; cl = tape.c[sym][a0:b]
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
        grp = "POI_limit" if fam in POI else "at_market"
        lag.setdefault(grp, []).append(j)
        lag.setdefault("fam:" + fam, []).append(j)
        for cell in CELLS:
            vr = cr(radv, rfav, endr, *cell)
            vp = cr(rfav, radv, -endr, *cell)
            add(grp, cell, vr, vp)
            add("fam:" + fam, cell, vr, vp)
            add("ALL", cell, vr, vp)
            dk = (r["t"][:10], grp, cell)
            dd = dayacc.setdefault(dk, [0.0, 0.0, 0])
            dd[0] += vr; dd[1] += vp; dd[2] += 1
    print("done", w, file=sys.stderr, flush=True)

rng = np.random.default_rng(23)
out = {"schema": "gtos.wave19.d7.stage6.v1", "cells": [list(c) for c in CELLS], "groups": {}}
for (grp, cell), (sr, sp, n) in sorted(acc.items(), key=lambda kv: str(kv[0])):
    g = out["groups"].setdefault(grp, {"n": n, "cells": {}})
    entry = {"n": n, "gross_real": sr / n, "gross_placebo": sp / n, "signal": (sr - sp) / n}
    if grp in ("POI_limit", "at_market"):
        blocks = [(v[0], v[1], v[2]) for (dk, gg, cc), v in dayacc.items()
                  if gg == grp and cc == cell]
        if blocks:
            R_ = np.array([b[0] for b in blocks]); P_ = np.array([b[1] for b in blocks])
            C_ = np.array([b[2] for b in blocks], dtype=float)
            D = len(blocks)
            bs = np.empty(2000)
            for t in range(2000):
                ix = rng.integers(0, D, D)
                bs[t] = (R_[ix].sum() - P_[ix].sum()) / C_[ix].sum()
            entry["signal_ci95"] = [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]
            entry["n_day_blocks"] = D
    g["cells"][f"x{cell[0]}_tr{cell[1]}"] = entry
for grp, v in lag.items():
    a = np.array(v)
    out.setdefault("fill_lag_bars", {})[grp] = {
        "n": int(a.size), "mean": float(a.mean()), "median": float(np.median(a)),
        "share_fill_in_first_bar": float((a == 0).mean())}
json.dump(out, open(os.path.join(OUT, "D7_STAGE6.json"), "w"), indent=1, default=float)

for grp in ["ALL", "at_market", "POI_limit"] + sorted(k for k in out["groups"] if k.startswith("fam:")):
    g = out["groups"][grp]
    print(f"\n{grp}  n={g['n']}")
    for ck, e in g["cells"].items():
        ci = e.get("signal_ci95")
        cis = f"  CI95 [{ci[0]:+.5f},{ci[1]:+.5f}]" if ci else ""
        print(f"   {ck:<14} real {e['gross_real']:+.5f}  placebo {e['gross_placebo']:+.5f}"
              f"  signal {e['signal']:+.5f}{cis}")
print("\nFILL LAG (M1 bars from decision to fill):")
for k, v in out["fill_lag_bars"].items():
    print(f"   {k:<40} n {v['n']:>7} mean {v['mean']:>7.2f} median {v['median']:>5.1f} "
          f"first-bar {v['share_fill_in_first_bar']*100:>5.1f}%")
