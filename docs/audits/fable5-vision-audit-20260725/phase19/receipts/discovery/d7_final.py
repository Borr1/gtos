#!/usr/bin/env python3
"""d7 stage 9 — the artifact-free direction test, the two free repairs, and the owner table.

Stage 8 showed that the at-market cohort's POSITIVE market-fill signal (+0.01777) is carried
entirely by 3.4% of rows whose emitted entry price was never touched -- the same phantom
credit f1 warned about for POI rows. This stage:
  1. isolates the rows where the entry WAS available in the very first bar (93.4% of the
     at-market cohort), where the market and limit contracts are identical by construction,
     and bootstraps the direction test there. That is the cleanest directional measurement
     available on this population.
  2. prices the two repairs that need no new data: dropping current_breaker_re_entry, and
     dropping POI candidates whose level is already at market at the decision instant.
  3. writes the owner table.
"""
import gzip, glob, json, math, os, sys
import numpy as np

REPO = "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"
PBG = REPO + "/docs/audits/fable5-vision-audit-20260725/phase19/receipts/pbg"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PBG); sys.path.insert(0, REPO)
os.chdir(REPO)
import pbg_econ as E

OUT = "/tmp/d7"; HOR = 120; TR = 2.0
POI = {"current_fvg_fill", "current_ob_retest", "current_breaker_re_entry"}
DEFECT = "current_breaker_re_entry"
WIN = {"2025-10": "202510", "2025-11": "202511", "2025-12": "202512",
       "2026-04": "202604", "2026-05": "202605"}
NEXT = {"2025-10": "202511", "2025-11": "202512", "2025-12": "202601",
        "2026-04": "202605", "2026-05": "202606"}
days = json.load(open(os.path.join(HERE, "f1_ARM_TRADING_DAYS_V1.json")))


def outcome(ra, rf, er, x=1.0, tr=TR):
    ia = int(np.searchsorted(ra, x, side="left")); it = int(np.searchsorted(rf, tr, side="left"))
    if ia < ra.size and (it >= rf.size or ia <= it):
        return -x
    if it < rf.size:
        return tr
    return er


# cohort -> day -> [real, placebo, cost, n]
D = {}


def add(coh, dk, vr, vp, cc):
    a = D.setdefault(coh, {}).setdefault(dk, [0.0, 0.0, 0.0, 0])
    a[0] += vr; a[1] += vp; a[2] += cc; a[3] += 1


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
    cm = E.CostModel()
    for r in rr:
        fam = r["f"]; sym = r["s"]; e = r["e"]; sl = r["sl"]; long = (r["d"] == "L")
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
        h2 = hi[j + 1:]; l2 = lo[j + 1:]; c2 = cl[j + 1:]
        if h2.size == 0:
            continue
        if long:
            adv = (e - l2) / d; fav = (h2 - e) / d; er = (c2[-1] - e) / d
        else:
            adv = (h2 - e) / d; fav = (e - l2) / d; er = (e - c2[-1]) / d
        ra = np.maximum.accumulate(adv); rf = np.maximum.accumulate(fav)
        vr = outcome(ra, rf, er); vp = outcome(rf, ra, -er)
        px, _ = cm.cost_px(sym, r["t"], e, long, hold_min=HOR)
        cc = px / d
        dk = r["t"][:10]
        ispoi = fam in POI
        add("ALL_FILLS", dk, vr, vp, cc)
        if fam != DEFECT:
            add("CLEAN", dk, vr, vp, cc)
            if not ispoi:
                add("ATMKT", dk, vr, vp, cc)
                if j == 0:
                    add("ATMKT_ENTRY_AVAILABLE", dk, vr, vp, cc)
                else:
                    add("ATMKT_ENTRY_NOT_AVAILABLE", dk, vr, vp, cc)
            else:
                add("POI", dk, vr, vp, cc)
                if j == 0:
                    add("POI_LEVEL_ALREADY_AT_MARKET", dk, vr, vp, cc)
                else:
                    add("POI_GENUINE_PULLBACK", dk, vr, vp, cc)
                    add("CLEAN_PLUS_REPAIR2", dk, vr, vp, cc)
        if fam != DEFECT and not ispoi:
            add("CLEAN_PLUS_REPAIR2", dk, vr, vp, cc)
    print("done", w, file=sys.stderr, flush=True)

rng = np.random.default_rng(97)
res = {"schema": "gtos.wave19.d7.stage9.v1", "windows": list(WIN), "cohorts": {}}
for coh, dd in D.items():
    ks = sorted(dd)
    Rr = np.array([dd[k][0] for k in ks]); Pp = np.array([dd[k][1] for k in ks])
    Cc = np.array([dd[k][2] for k in ks]); Nn = np.array([dd[k][3] for k in ks], dtype=float)
    n = int(Nn.sum())
    B = len(ks)
    bs = np.empty(4000); bg = np.empty(4000)
    for t in range(4000):
        ix = rng.integers(0, B, B)
        tot = Nn[ix].sum()
        bs[t] = (Rr[ix].sum() - Pp[ix].sum()) / tot
        bg[t] = Rr[ix].sum() / tot
    res["cohorts"][coh] = {
        "n": n, "n_day_blocks": B,
        "gross": float(Rr.sum() / n), "gross_ci95": [float(np.percentile(bg, 2.5)), float(np.percentile(bg, 97.5))],
        "placebo": float(Pp.sum() / n),
        "signal": float((Rr.sum() - Pp.sum()) / n),
        "signal_ci95": [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))],
        "p_signal_ge_0": float((bs >= 0).mean()),
        "toll": float(Cc.sum() / n),
        "net": float((Rr.sum() - Cc.sum()) / n),
    }
json.dump(res, open(os.path.join(OUT, "D7_STAGE9.json"), "w"), indent=1, default=float)
order = ["ALL_FILLS", "CLEAN", "CLEAN_PLUS_REPAIR2", "ATMKT", "ATMKT_ENTRY_AVAILABLE",
         "ATMKT_ENTRY_NOT_AVAILABLE", "POI", "POI_LEVEL_ALREADY_AT_MARKET", "POI_GENUINE_PULLBACK"]
print(f"{'cohort':<30}{'n':>8}{'gross':>10}{'toll':>9}{'net':>10}{'placebo':>10}{'signal':>10}   CI95")
for k in order:
    v = res["cohorts"].get(k)
    if not v:
        continue
    print(f"{k:<30}{v['n']:>8}{v['gross']:>+10.5f}{v['toll']:>9.5f}{v['net']:>+10.5f}"
          f"{v['placebo']:>+10.5f}{v['signal']:>+10.5f}   "
          f"[{v['signal_ci95'][0]:+.5f},{v['signal_ci95'][1]:+.5f}] p{v['p_signal_ge_0']:.4f}")
