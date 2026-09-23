#!/usr/bin/env python3
"""W7 INSTRUMENT RESTATEMENT — part 4: per-sleeve economics and survivor tiers.

Measurement only.  Restates `SURVIVOR_BOOK_V1.json`'s per-account survivor tiers
three ways: as published, at the CURRENT cost layer on the uncorrected instrument,
and at the current cost layer on the quote-side-corrected instrument (B replicates).

A sleeve "survives" when its per-trade net expectancy stays positive at its own
maximum modelled carry -- `recost_w7_validation.sleeve_table(...)['survives_at_max_carry']`,
the same predicate `build_survivor_book.py` and `mc_firm_rules.build_cells` read.
"""
from __future__ import annotations

import collections
import gzip
import json
import math
import random
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[8]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import recost_w7_validation as M   # noqa: E402

HERE = Path(__file__).resolve().parent
AUD = REPO / "docs/audits/fable5-vision-audit-20260725"
R1_ROWS = AUD / "phase20/receipts/r1/R1_ESTATE_ROWS_V1.json.gz"
PUB = REPO / "research/operations/w7_recost_2026_07_27/SURVIVOR_BOOK_V1.json"
B = 300


def calib():
    r1 = json.load(gzip.open(R1_ROWS, "rt"))
    per = {}
    ptg = pmg = 0
    poth = []
    for sl in sorted({r["sleeve"] for r in r1}):
        rs = [r for r in r1 if r["sleeve"] == sl]
        tg = [r for r in rs if r["reason_old"] == "target"]
        mig = [r for r in tg if r["reason_new"] != "target"]
        oth = [r["r_new_mid"] - r["r_old"] for r in rs
               if r["reason_old"] in ("trail", "maxbars")]
        per[sl] = dict(n_target=len(tg), n_migrated=len(mig), other_deltas=oth)
        ptg += len(tg)
        pmg += len(mig)
        poth += oth
    per["_POOLED_"] = dict(n_target=ptg, n_migrated=pmg, other_deltas=poth)
    return per


def classify(rows):
    for r in rows:
        g = r["R"] + r["charged_cost_r"]
        r["_gross"] = g
        if abs(g + 1.0) < 1e-6:
            r["_reason"] = "stop"
        elif g > 0 and abs(g - round(g * 4) / 4) < 1e-6:
            r["_reason"] = "target"
        else:
            r["_reason"] = "other"


def apply_correction(rows, cal, rng):
    rates = {}
    for sl in {r["sleeve"] for r in rows}:
        c = cal.get(sl) or cal["_POOLED_"]
        if not c["n_target"]:
            c = cal["_POOLED_"]
        a, b = c["n_migrated"] + 0.5, c["n_target"] - c["n_migrated"] + 0.5
        x, y = rng.gammavariate(a, 1.0), rng.gammavariate(b, 1.0)
        rates[sl] = x / (x + y)
    out = []
    for r in rows:
        d = 0.0
        if r["_reason"] == "target":
            if rng.random() < rates[r["sleeve"]]:
                d = -1.0 - r["_gross"]
        elif r["_reason"] == "other":
            pool = (cal.get(r["sleeve"]) or {}).get("other_deltas") or cal["_POOLED_"]["other_deltas"]
            d = rng.choice(pool) if pool else 0.0
        q = dict(r)
        q["R_gross"] = r["R_gross"] + d
        out.append(q)
    return out


def pctl(xs, q):
    xs = sorted(xs)
    i = (len(xs) - 1) * q / 100.0
    lo, hi = int(math.floor(i)), int(math.ceil(i))
    return xs[lo] if lo == hi else xs[lo] + (xs[hi] - xs[lo]) * (i - lo)


def main():
    st = M.build([])
    rows = st["rows"]
    classify(rows)
    cms = {}
    for acct in ("FTMO", "redacted_account"):
        pool = collections.defaultdict(list)
        for r in rows:
            c = r[f"cost_{acct}"]
            if c["status"] == "priced":
                pool[r["sleeve"]].append(c["cost_ex_swap_r"])
        cms[acct] = {k: statistics.median(v) for k, v in pool.items()}

    pub = json.load(open(PUB))
    out = {"schema": "gtos.wave21.w7_survivor_tiers.v1", "measurement_only": True,
           "predicate": "recost_w7_validation.sleeve_table(...)['survives_at_max_carry']",
           "replicates": B}

    # published
    published = {}
    for acct in ("FTMO", "redacted_account"):
        blk = pub["accounts"][acct]
        published[acct] = dict(
            survivors=sorted(blk.get("survivors", [])),
            tiers={sl: v.get("survivor_tier") for sl, v in blk["sleeves"].items()})
    out["as_published_2026_07_29"] = published

    # current cost layer, uncorrected instrument
    cur = {}
    for acct in ("FTMO", "redacted_account"):
        tab = M.sleeve_table(rows, acct, cms[acct])
        cur[acct] = dict(
            survivors=sorted(sl for sl, v in tab.items() if v["survives_at_max_carry"]),
            per_sleeve={sl: dict(n=v.get("n"),
                                 mean_gross=v.get("mean_gross"),
                                 mean_true=v.get("mean_true"),
                                 survives_at_max_carry=v["survives_at_max_carry"])
                        for sl, v in tab.items()})
    out["current_cost_layer_uncorrected_instrument"] = cur

    # corrected instrument, B replicates
    cal = calib()
    rng = random.Random(20260811)
    surv_count = {a: collections.Counter() for a in ("FTMO", "redacted_account")}
    mean_true = {a: collections.defaultdict(list) for a in ("FTMO", "redacted_account")}
    for _ in range(B):
        crows = apply_correction(rows, cal, rng)
        for acct in ("FTMO", "redacted_account"):
            tab = M.sleeve_table(crows, acct, cms[acct])
            for sl, v in tab.items():
                if v["survives_at_max_carry"]:
                    surv_count[acct][sl] += 1
                if v.get("mean_true") is not None:
                    mean_true[acct][sl].append(v["mean_true"])
    corr = {}
    for acct in ("FTMO", "redacted_account"):
        per = {}
        for sl in cur[acct]["per_sleeve"]:
            v = mean_true[acct].get(sl, [])
            per[sl] = dict(
                p_survives=surv_count[acct][sl] / B,
                mean_true_median=(pctl(v, 50) if v else None),
                mean_true_ci95=([pctl(v, 2.5), pctl(v, 97.5)] if v else None),
                uncorrected_mean_true=cur[acct]["per_sleeve"][sl]["mean_true"],
                uncorrected_survives=cur[acct]["per_sleeve"][sl]["survives_at_max_carry"])
        corr[acct] = dict(
            survivors_at_p_ge_0_5=sorted(sl for sl, v in per.items()
                                         if v["p_survives"] >= 0.5),
            per_sleeve=per)
    out["corrected_instrument"] = corr

    (HERE / "W7_SURVIVOR_TIERS_V1.json").write_text(json.dumps(out, indent=1, default=str))

    for acct in ("FTMO", "redacted_account"):
        print(f"\n=== {acct} ===")
        print("  published survivors      :", published[acct]["survivors"])
        print("  current-cost uncorrected :", cur[acct]["survivors"])
        print("  corrected (p>=0.5)       :", corr[acct]["survivors_at_p_ge_0_5"])
        print(f"  {'sleeve':22s} {'net(uncorr)':>11s} {'net(corr med)':>13s} "
              f"{'ci95':>26s} {'P(survive)':>10s}")
        for sl, v in sorted(corr[acct]["per_sleeve"].items()):
            ci = v["mean_true_ci95"]
            cis = f"[{ci[0]:+.4f},{ci[1]:+.4f}]" if ci else "n/a"
            mu = v["uncorrected_mean_true"]
            md = v["mean_true_median"]
            print(f"  {sl:22s} {('%+0.4f'%mu) if mu is not None else 'n/a':>11s} "
                  f"{('%+0.4f'%md) if md is not None else 'n/a':>13s} {cis:>26s} "
                  f"{v['p_survives']:10.3f}")


if __name__ == "__main__":
    main()
