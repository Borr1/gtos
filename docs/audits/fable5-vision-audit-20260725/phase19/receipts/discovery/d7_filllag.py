#!/usr/bin/env python3
"""d7 stage 8 — WHICH rows the fill convention destroys.

Stage 7: at-market families carry +0.01777 R/trade of directional content at a market fill
and -0.03681 at the honest resting-limit fill, on the same rows and days. 93.4% of those
rows fill in the first bar, where the two contracts are IDENTICAL by construction -- so the
whole 0.0546 R/trade must be carried by the ~6.6% that do not. This measures it directly
instead of inferring it, bucketing by fill lag, and prices the repair.
"""
import gzip, glob, json, os, sys
import numpy as np

REPO = "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"
PBG = REPO + "/docs/audits/fable5-vision-audit-20260725/phase19/receipts/pbg"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PBG); sys.path.insert(0, REPO)
os.chdir(REPO)
import pbg_econ as E

OUT = "/tmp/d7"; HOR = 120; TR = 2.0
POI = {"current_fvg_fill", "current_ob_retest", "current_breaker_re_entry"}
WIN = {"2025-10": "202510", "2025-11": "202511", "2025-12": "202512",
       "2026-04": "202604", "2026-05": "202605"}
NEXT = {"2025-10": "202511", "2025-11": "202512", "2025-12": "202601",
        "2026-04": "202605", "2026-05": "202606"}
days = json.load(open(os.path.join(HERE, "f1_ARM_TRADING_DAYS_V1.json")))


def outcome(ra, rf, endr, x=1.0, tr=TR):
    ia = int(np.searchsorted(ra, x, side="left")); it = int(np.searchsorted(rf, tr, side="left"))
    if ia < ra.size and (it >= rf.size or ia <= it):
        return -x
    if it < rf.size:
        return tr
    return endr


def bucket(j):
    if j is None:
        return "never_fills"
    if j == 0:
        return "lag0_same_bar"
    if j <= 5:
        return "lag1_5"
    if j <= 30:
        return "lag6_30"
    return "lag31plus"


acc = {}   # (grp, bucket, contract) -> [sr, sp, n]
cst = {}   # (grp, bucket) -> [cost_sum, n]


def add(grp, bk, ct, vr, vp):
    a = acc.setdefault((grp, bk, ct), [0.0, 0.0, 0])
    a[0] += vr; a[1] += vp; a[2] += 1


for w in WIN:
    ok = set(days[w])
    rr = []
    for f in sorted(glob.glob(f"/tmp/f1/roster_{WIN[w]}/*.jsonl.gz")):
        with gzip.open(f, "rt") as fh:
            for line in fh:
                r = json.loads(line)
                if r["k"] == 15 and r["t"][:10] in ok and r["f"] != "current_breaker_re_entry":
                    rr.append(r)
    syms = sorted({r["s"] for r in rr})
    tape = E.Tape(syms, [WIN[w]] + ([NEXT[w]] if NEXT.get(w) else []))
    cm = E.CostModel()
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
        grp = "POI_limit" if r["f"] in POI else "at_market"
        touched = (lo <= e) if long else (hi >= e)
        j = int(np.argmax(touched)) if touched.any() else None
        bk = bucket(j)

        def emit(ct, h2, l2, c2):
            if h2.size == 0:
                return
            if long:
                adv = (e - l2) / d; fav = (h2 - e) / d; er = (c2[-1] - e) / d
            else:
                adv = (h2 - e) / d; fav = (e - l2) / d; er = (e - c2[-1]) / d
            ra = np.maximum.accumulate(adv); rf = np.maximum.accumulate(fav)
            add(grp, bk, ct, outcome(ra, rf, er), outcome(rf, ra, -er))

        emit("C0_market", hi[1:], lo[1:], cl[1:])
        if j is not None:
            emit("C1_honest", hi[j + 1:], lo[j + 1:], cl[j + 1:])
            px, _ = cm.cost_px(sym, r["t"], e, long, hold_min=HOR)
            k = cst.setdefault((grp, bk), [0.0, 0])
            k[0] += px / d; k[1] += 1
    print("done", w, file=sys.stderr, flush=True)

out = {"schema": "gtos.wave19.d7.stage8.v1", "target_r": TR, "buckets": {}}
for (grp, bk, ct), (sr, sp, n) in sorted(acc.items()):
    e = out["buckets"].setdefault(grp, {}).setdefault(bk, {})
    e[ct] = {"n": n, "real": sr / n, "placebo": sp / n, "signal": (sr - sp) / n}
    if (grp, bk) in cst and cst[(grp, bk)][1]:
        e["toll_R"] = cst[(grp, bk)][0] / cst[(grp, bk)][1]

# price the repair: at-market rows only, replace the C1 outcome with the C0 outcome
# for every row whose fill lag is > 0
rep = {}
for grp in out["buckets"]:
    tot_n = sum(v.get("C1_honest", {}).get("n", 0) for v in out["buckets"][grp].values())
    cur = sum(v.get("C1_honest", {}).get("real", 0.0) * v.get("C1_honest", {}).get("n", 0)
              for v in out["buckets"][grp].values())
    fixed = 0.0
    for bk, v in out["buckets"][grp].items():
        c1 = v.get("C1_honest")
        if not c1:
            continue
        if bk == "lag0_same_bar":
            fixed += c1["real"] * c1["n"]
        else:
            c0 = v.get("C0_market")
            fixed += (c0["real"] if c0 else c1["real"]) * c1["n"]
    rep[grp] = {"n": tot_n, "gross_as_shipped": cur / tot_n if tot_n else None,
                "gross_if_lagged_fills_entered_at_market": fixed / tot_n if tot_n else None,
                "repair_value_R_per_trade": (fixed - cur) / tot_n if tot_n else None}
out["repair_pricing"] = rep
json.dump(out, open(os.path.join(OUT, "D7_STAGE8.json"), "w"), indent=1, default=float)

for grp in ("at_market", "POI_limit"):
    print(f"\n===== {grp} =====")
    print(f"{'bucket':<16}{'n(C1)':>8}{'toll':>8}{'C1 real':>10}{'C1 plac':>10}{'C1 sig':>10}"
          f"{'C0 real':>10}{'C0 sig':>10}")
    for bk in ("lag0_same_bar", "lag1_5", "lag6_30", "lag31plus", "never_fills"):
        v = out["buckets"][grp].get(bk)
        if not v:
            continue
        c1 = v.get("C1_honest"); c0 = v.get("C0_market")
        print(f"{bk:<16}{(c1['n'] if c1 else 0):>8}{v.get('toll_R', float('nan')):>8.4f}"
              f"{(c1['real'] if c1 else float('nan')):>+10.5f}{(c1['placebo'] if c1 else float('nan')):>+10.5f}"
              f"{(c1['signal'] if c1 else float('nan')):>+10.5f}"
              f"{(c0['real'] if c0 else float('nan')):>+10.5f}{(c0['signal'] if c0 else float('nan')):>+10.5f}")
    print("  repair:", {k: (round(v, 5) if isinstance(v, float) else v) for k, v in rep[grp].items()})
