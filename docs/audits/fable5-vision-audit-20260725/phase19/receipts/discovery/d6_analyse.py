"""d6_analyse — the surviving candidate, gated.

Sections
  1  reproduction of PB's published EARLY5 / AT_MARKET numbers from the rebuilt dataset
  2  the selection: how the five families were chosen, and what that selection is worth
  3  the books (implementable) vs the paired arm (counterfactual)
  4  ablation: family set x timing x contract x geometry x target
  5  separability: can anything observable at T+k tell paired from phantom
  6  truncation / exit mix at the winner
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import d6_lib as D  # noqa: E402


def rows_for(months, fams):
    out = {}
    for m in months:
        out[m] = D.load(m, fams=set(fams))
    return out


def arms(rows):
    """Split a month's rows into the four populations of the contract."""
    paired = [r for r in rows if r.get("C") and r.get("P")]
    phantom = [r for r in rows if r.get("P") and not r.get("C")]
    close_only_only = [r for r in rows if r.get("C") and not r.get("P")]
    return paired, phantom, close_only_only


def book(rows, arm_partial: bool, target=2.0):
    """The implementable book. partial: every partial emission (paired first-k +
    phantom) plus the close-only setups the partial generator never saw.
    close: every close emission."""
    paired, phantom, coo = arms(rows)
    if arm_partial:
        return ([(r, "P") for r in paired] + [(r, "P") for r in phantom]
                + [(r, "C") for r in coo])
    return [(r, "C") for r in paired] + [(r, "C") for r in coo]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--months", default="")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    months = [m for m in args.months.split(",") if m] or D.months_available()

    RES = {"months": months, "generated_utc": __import__("datetime").datetime.now(
        __import__("datetime").timezone.utc).isoformat()}

    atm = rows_for(months, D.AT_MARKET)
    e5 = {m: [r for r in atm[m] if r["e5"]] for m in months}

    # ------------------------------------------------------- 1. reproduction
    rep = {}
    for m in months:
        paired, phantom, coo = arms(e5[m])
        rep[m] = {
            "n_paired": len(paired), "n_phantom": len(phantom), "n_close_only_only": len(coo),
            "paired_close": D.summarise([(r, "C") for r in paired], "paired_close"),
            "paired_partial": D.summarise([(r, "P") for r in paired], "paired_partial"),
            "paired_partial_d0": D.summarise([(r, "D") for r in paired], "paired_partial_d0"),
            "phantom": D.summarise([(r, "P") for r in phantom], "phantom"),
            "close_only_only": D.summarise([(r, "C") for r in coo], "close_only_only"),
            "BOOK_close": D.summarise(book(e5[m], False), "BOOK_close"),
            "BOOK_partial": D.summarise(book(e5[m], True), "BOOK_partial"),
            "delta_net_paired": D.paired_delta(paired, "P", "C"),
            "delta_gross_paired": D.paired_delta_gross(paired, "P", "C"),
            "delta_net_paired_d0": D.paired_delta(paired, "D", "C"),
        }
    RES["EARLY5_by_month"] = rep

    # AT_MARKET whole-cohort, for the composition contrast
    repa = {}
    for m in months:
        paired, phantom, coo = arms(atm[m])
        repa[m] = {
            "n_paired": len(paired), "n_phantom": len(phantom),
            "delta_net_paired": D.paired_delta(paired, "P", "C"),
            "delta_net_paired_d0": D.paired_delta(paired, "D", "C"),
            "BOOK_close": D.summarise(book(atm[m], False), "BOOK_close"),
            "BOOK_partial": D.summarise(book(atm[m], True), "BOOK_partial"),
        }
    RES["AT_MARKET_by_month"] = repa

    # ------------------------------------------------------- 2. the selection
    fam_tbl = {}
    for fam in D.AT_MARKET:
        fam_tbl[fam] = {}
        for m in months:
            rr = [r for r in atm[m] if r["f"] == fam]
            paired, phantom, coo = arms(rr)
            fam_tbl[fam][m] = {
                "n_paired": len(paired), "n_phantom": len(phantom),
                "delta_net_d0": D.paired_delta(paired, "D", "C"),
                "delta_net": D.paired_delta(paired, "P", "C"),
                "phantom_net": D.summarise([(r, "P") for r in phantom], "phantom"),
                "close_net": D.summarise([(r, "C") for r in paired + coo], "close"),
                "book_partial": D.summarise(book(rr, True), "book_partial"),
            }
    RES["by_family"] = fam_tbl

    # every subset of the 7 at-market families: is EARLY5 special, or just the
    # in-sample argmax?  Priced on the IMPLEMENTABLE book, pooled over months.
    def pooled_book_net(fams, ms, partial):
        tot = 0.0
        n = 0
        by_day = defaultdict(lambda: [0.0, 0])
        for m in ms:
            rr = [r for r in atm[m] if r["f"] in fams]
            for r, arm in book(rr, partial):
                a = r.get(arm)
                if not a:
                    continue
                v = a["g2"] - a["cr"]
                tot += v
                n += 1
                day = r["day_part"] if arm == "P" else r["day_close"]
                by_day[m + "|" + day][0] += v
                by_day[m + "|" + day][1] += 1
        return {"n": n, "net_r": (tot / n if n else None), "total": tot,
                "days_positive": sum(1 for d in by_day if by_day[d][0] > 0),
                "n_days": len(by_day)}

    def pooled_paired_delta(fams, ms, d0=False):
        by_day = defaultdict(lambda: [0.0, 0])
        n = 0
        for m in ms:
            rr = [r for r in atm[m] if r["f"] in fams]
            for r in rr:
                A = r.get("D" if d0 else "P")
                B = r.get("C")
                if not A or not B:
                    continue
                v = (A["g2"] - A["cr"]) - (B["g2"] - B["cr"])
                by_day[m + "|" + r["day_close"]][0] += v
                by_day[m + "|" + r["day_close"]][1] += 1
                n += 1
        out = D.bootstrap_days(by_day)
        if out:
            out["n"] = n
        return out

    subs = []
    for k in range(1, 8):
        for combo in itertools.combinations(D.AT_MARKET, k):
            fams = set(combo)
            row = {"fams": sorted(fams), "k": k}
            row["paired_delta_d0_ALL"] = pooled_paired_delta(fams, months, d0=True)
            row["book_partial_ALL"] = pooled_book_net(fams, months, True)
            row["book_close_ALL"] = pooled_book_net(fams, months, False)
            subs.append(row)
    RES["subset_sweep"] = subs

    # ------------------------------------------------------- 3. pooled arms
    def pooled_summary(fams, arm_sel, ms):
        trades = []
        for m in ms:
            rr = [r for r in atm[m] if r["f"] in fams]
            trades += arm_sel(rr)
        return D.summarise(trades)

    E5 = set(D.EARLY5)
    RES["pooled"] = {
        "EARLY5_paired_close": pooled_summary(E5, lambda rr: [(r, "C") for r in arms(rr)[0]], months),
        "EARLY5_paired_partial": pooled_summary(E5, lambda rr: [(r, "P") for r in arms(rr)[0]], months),
        "EARLY5_paired_partial_d0": pooled_summary(E5, lambda rr: [(r, "D") for r in arms(rr)[0]], months),
        "EARLY5_phantom": pooled_summary(E5, lambda rr: [(r, "P") for r in arms(rr)[1]], months),
        "EARLY5_BOOK_close": pooled_summary(E5, lambda rr: book(rr, False), months),
        "EARLY5_BOOK_partial": pooled_summary(E5, lambda rr: book(rr, True), months),
        "EARLY5_paired_delta_net": pooled_paired_delta(E5, months),
        "EARLY5_paired_delta_net_d0": pooled_paired_delta(E5, months, d0=True),
        "ATM_BOOK_close": pooled_summary(set(D.AT_MARKET), lambda rr: book(rr, False), months),
        "ATM_BOOK_partial": pooled_summary(set(D.AT_MARKET), lambda rr: book(rr, True), months),
        "ATM_paired_delta_net_d0": pooled_paired_delta(set(D.AT_MARKET), months, d0=True),
    }

    Path(args.out).write_text(json.dumps(RES, indent=1))
    print("wrote", args.out)


if __name__ == "__main__":
    main()
