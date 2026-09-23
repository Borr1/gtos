#!/usr/bin/env python3
"""d7 stage 7 — the fill-contract control that adjudicates SIGNAL vs USAGE.

Stage 6 found at-market families lose to their own mirror by -0.0368 R/trade with a CI
excluding zero. f2 measured +0.00315 +/- 0.01026 for the same family set at a MARKET fill
on 8 windows. The two differ in fill contract and in window set. This stage runs both fill
contracts on the SAME rows, the same 5 windows, with the same paired side placebo:

  C0 MARKET       every candidate is entered at its emitted price, no fill condition at
                  all, walk starts at the next M1 bar. No fill selection exists, so
                  real - placebo is PURE DIRECTION.
  C1 HONEST LIMIT the candidate rests at its emitted price and fills on a touch.

If C0's signal is ~0 and C1's is negative, the deficit is created by the FILL CONVENTION
(usage). If C0 is negative too, the direction call itself is worse than a coin flip (signal).
"""
import gzip, glob, json, os, sys
import numpy as np

REPO = "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"
PBG = REPO + "/docs/audits/fable5-vision-audit-20260725/phase19/receipts/pbg"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PBG); sys.path.insert(0, REPO)
os.chdir(REPO)
import pbg_econ as E

OUT = "/tmp/d7"; HOR = 120
POI = {"current_fvg_fill", "current_ob_retest", "current_breaker_re_entry"}
WIN = {"2025-10": "202510", "2025-11": "202511", "2025-12": "202512",
       "2026-04": "202604", "2026-05": "202605"}
NEXT = {"2025-10": "202511", "2025-11": "202512", "2025-12": "202601",
        "2026-04": "202605", "2026-05": "202606"}
days = json.load(open(os.path.join(HERE, "f1_ARM_TRADING_DAYS_V1.json")))
TR = 2.0


def outcome(radv, rfav, endr, x=1.0, tr=TR):
    ia = int(np.searchsorted(radv, x, side="left"))
    it = int(np.searchsorted(rfav, tr, side="left"))
    if ia < radv.size and (it >= rfav.size or ia <= it):
        return -x
    if it < rfav.size:
        return tr
    return endr


rec = {}          # (contract, group) -> [sr, sp, n]
dayrec = {}       # (contract, group, day) -> [sr, sp, n]
winrec = {}       # (contract, group, window) -> [sr, sp, n]


def add(ct, grp, w, dk, vr, vp):
    for store, key in ((rec, (ct, grp)), (dayrec, (ct, grp, dk)), (winrec, (ct, grp, w))):
        a = store.setdefault(key, [0.0, 0.0, 0])
        a[0] += vr; a[1] += vp; a[2] += 1


for w in WIN:
    ok = set(days[w])
    rr = []
    for f in sorted(glob.glob(f"/tmp/f1/roster_{WIN[w]}/*.jsonl.gz")):
        with gzip.open(f, "rt") as fh:
            for line in fh:
                r = json.loads(line)
                if r["k"] == 15 and r["t"][:10] in ok and r["f"] not in POI:
                    rr.append(r)      # at-market families only
    syms = sorted({r["s"] for r in rr})
    tape = E.Tape(syms, [WIN[w]] + ([NEXT[w]] if NEXT.get(w) else []))
    for r in rr:
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
        dk = r["t"][:10]

        def emit(ct, h2, l2, c2):
            if h2.size == 0:
                return
            if long:
                adv = (e - l2) / d; fav = (h2 - e) / d; endr = (c2[-1] - e) / d
            else:
                adv = (h2 - e) / d; fav = (e - l2) / d; endr = (e - c2[-1]) / d
            ra = np.maximum.accumulate(adv); rf = np.maximum.accumulate(fav)
            vr = outcome(ra, rf, endr); vp = outcome(rf, ra, -endr)
            add(ct, "at_market", w, dk, vr, vp)

        # C0 MARKET: no fill condition, walk from the next bar
        emit("C0_market", hi[1:], lo[1:], cl[1:])
        # C1 HONEST LIMIT
        touched = (lo <= e) if long else (hi >= e)
        if touched.any():
            j = int(np.argmax(touched))
            emit("C1_honest", hi[j + 1:], lo[j + 1:], cl[j + 1:])
    print("done", w, file=sys.stderr, flush=True)

rng = np.random.default_rng(31)
out = {"schema": "gtos.wave19.d7.stage7.v1", "target_r": TR,
       "population": "at-market families only (7), 5 windows, day-restricted", "contracts": {}}
for (ct, grp), (sr, sp, n) in rec.items():
    blocks = [(v[0], v[1], v[2]) for (c2, g2, dk), v in dayrec.items() if c2 == ct and g2 == grp]
    R_ = np.array([x[0] for x in blocks]); P_ = np.array([x[1] for x in blocks])
    C_ = np.array([x[2] for x in blocks], dtype=float); D = len(blocks)
    bs = np.empty(4000)
    for t in range(4000):
        ix = rng.integers(0, D, D)
        bs[t] = (R_[ix].sum() - P_[ix].sum()) / C_[ix].sum()
    pw = [(ww, (v[0] - v[1]) / v[2], v[2]) for (c2, g2, ww), v in winrec.items()
          if c2 == ct and g2 == grp]
    out["contracts"][ct] = {
        "n": n, "gross_real": sr / n, "gross_placebo": sp / n, "signal": (sr - sp) / n,
        "signal_ci95": [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))],
        "n_day_blocks": D,
        "p_signal_ge_0": float((bs >= 0).mean()),
        "by_window": {ww: {"signal": s, "n": nn} for ww, s, nn in sorted(pw)},
        "windows_positive": sum(1 for _, s, _ in pw if s > 0), "windows": len(pw)}
json.dump(out, open(os.path.join(OUT, "D7_STAGE7.json"), "w"), indent=1, default=float)
for ct, v in out["contracts"].items():
    print(f"\n{ct}: n={v['n']}  real {v['gross_real']:+.5f}  placebo {v['gross_placebo']:+.5f}"
          f"  SIGNAL {v['signal']:+.5f}  CI95 [{v['signal_ci95'][0]:+.5f},{v['signal_ci95'][1]:+.5f}]"
          f"  p(signal>=0) {v['p_signal_ge_0']:.4f}  windows+ {v['windows_positive']}/{v['windows']}")
    for ww, e in v["by_window"].items():
        print(f"     {ww}  n {e['n']:>6}  signal {e['signal']:+.5f}")
