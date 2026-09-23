"""Session AI — the composition test at AD's MEASURED nights, because the first one was circular.

    python3 docs/audits/fable5-vision-audit-20260725/phase8/receipts/ai_measured_carry_books.py

WHY THIS EXISTS
---------------
`BOOKS_MC_V1.json` tested "what is AD's tier restatement worth as a composition change" at the
`fwd_nights_max` cell and reported it NEGATIVE. An adversarial pass over this session's own claims
showed that test is circular, and it is right:

  `row_cost` (`recost_w7_validation.py:869-876`) charges
  `swap_r_per_night x min(nights, SLEEVE_MAX_NIGHTS[sleeve])` and **never consults
  `CARRY_STRUCTURAL`** -- that set appears only in the TIERING code (`:1041`, `:1054`, `:1058`,
  `:1069`), never in the charge. So at `nights = "max"` `fx_jpy` is charged **3 nights** of swap
  against AD's measured mean of **0.0015** nights (`frac_zero` 0.999 over n = 3,984), and
  `sub_mid_dn_revert` **14** against **1.308**.

AD's restatement exists precisely because the modelled carry is wrong. Testing what it is worth at
the modelled MAX carry therefore tests it at the assumption it replaces, and the two sleeves the
restatement promotes are the two the cell overcharges most (2,000x and 10.7x, against 2.8x-4.7x
for the armed three). That is not a fair test in either direction.

WHAT THIS FILE DOES INSTEAD
---------------------------
The same `mc_firm_rules.mc`, the same series construction, the same live sizing -- with the carry
charged **per sleeve at AD's measured nights** rather than at one global scalar. Three carry bases,
all published:

  `measured_mean` -- AD's `nights_measured.mean`, the honest central case
  `measured_p99`  -- AD's `nights_measured.p99`, the tail the tier rule actually tests (R3: the
                     tier is a p100 test, so p99 is the conservative read of a measured hold)
  `modelled_max`  -- the original cell, kept so the difference is visible rather than asserted

A sleeve with no AD row keeps the modelled scalar, and which sleeves those are is published.
"""

from __future__ import annotations

import argparse
import collections
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
sys.path.insert(0, str(REPO))

_p = sys.path[:]
try:
    sys.path[:] = [str(REPO)]
    import research.operations  # noqa: F401
finally:
    sys.path[:] = _p
sys.path.insert(0, str(REPO / "scripts"))

import mc_firm_rules as Q  # noqa: E402
import recost_w7_validation as M  # noqa: E402

AUD = REPO / "docs/audits/fable5-vision-audit-20260725"
TIERS = AUD / "phase7/receipts/AD_CARRY_TIERS_RESTATED_V1.json"
OUT = HERE / "AI_MEASURED_CARRY_BOOKS_V1.json"

ARMED = ["crypto", "energy_agri", "sub_xvol_pullback"]
RESTATED = ["sub_mid_dn_revert", "fx_jpy"]
BOOKS = {
    "FTMO_ARMED_TODAY_3": ARMED,
    "FTMO_ARMED_PLUS_AD_RESTATED_5": ARMED + RESTATED,
}
RULES = ("L4_FIRM_TRUE_PH1", "P2_BOTH_PHASES")


def ad_nights() -> dict:
    """{account: {sleeve: {'mean': x, 'p99': y}}} from AD's own artifact."""
    d = json.loads(TIERS.read_text())
    out = collections.defaultdict(dict)
    for _k, r in (d.get("rows") or {}).items():
        nm = r.get("nights_measured") or {}
        if r.get("account") and r.get("sleeve") and nm.get("mean") is not None:
            out[r["account"]][r["sleeve"]] = {"mean": float(nm["mean"]),
                                             "p99": float(nm.get("p99", nm["mean"]))}
    return dict(out)


def series_per_sleeve_nights(sub, acct, cm, nights_of, sd_book, *, forward, kelly, risk_basis,
                             fallback):
    """`Q.series` with the carry charged PER SLEEVE.

    Deliberately a copy of `Q.series`'s body rather than a new model: the only line that differs
    is the one that resolves `n`, so any other difference would be a bug in this file. Everything
    downstream -- `row_cost`, `build_matrix_from`, the Kelly bins, the vol match -- is Q's.
    """
    km = Q.kelly_fn(kelly)
    used = {}
    for r in sub:
        sl = r["sleeve"]
        n = nights_of.get(sl)
        if n is None:
            n = M.SLEEVE_MAX_NIGHTS[sl] if fallback == "max" else float(fallback)
        used[sl] = n
        c, _ = M.row_cost(r, acct, n, "sleeve_median", cm)
        r["R_s"] = None if c is None else r["R_gross"] - c
    days, _, Mx, _ = M.build_matrix_from(sub, "R_s")
    nact = [sum(1 for v in row if abs(v) > 1e-9) for row in Mx]
    Mk = [[v * km(nact[i]) for v in Mx[i]] for i in range(len(Mx))]
    comb = [sum(r) for r in Mk]
    if forward:
        pair = [(v, d) for v, d in zip(comb, days) if d.year >= 2025]
        comb = [v for v, _ in pair]
        days = [d for _, d in pair]
    sd = statistics.pstdev(comb)
    vs = sd_book / sd if sd else 0.0
    risk = Q.DIAL * vs if risk_basis == Q.RISK_VOL_MATCHED else Q.DIAL
    return days, comb, risk, vs, used


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--paths", type=int, default=60_000)
    a = ap.parse_args(argv)

    st = M.build([])
    rows = st["rows"]
    for r in rows:
        r["R_legacy"] = r["R"]
    _, _, _, sd_book = M.build_matrix_from(rows, "R_legacy")
    adn = ad_nights()

    doc = {
        "schema": "gtos.w7_recost.measured_carry_books.v1",
        "generated_by": ("docs/audits/fable5-vision-audit-20260725/phase8/receipts/"
                         "ai_measured_carry_books.py"),
        "question": ("What is AD's tier restatement worth as a composition change AT THE CARRY "
                     "AD MEASURED, rather than at the modelled max carry the restatement exists "
                     "to replace?"),
        "why_the_first_test_was_circular": (
            "`recost_w7_validation.row_cost:873` charges swap at "
            "min(nights, SLEEVE_MAX_NIGHTS[sleeve]) and never consults CARRY_STRUCTURAL, which "
            "appears only in the tiering code. So `nights_max` charges fx_jpy 3 nights against "
            "AD's measured mean of 0.0015 (frac_zero 0.999, n=3,984) and sub_mid_dn_revert 14 "
            "against 1.308 -- 2,000x and 10.7x -- while charging the armed three only 2.8x-4.7x. "
            "The cell overcharges exactly the two sleeves the restatement promotes."),
        "n_paths": a.paths,
        "sizing": "live_nominal_per_unit + live_half_bins (what admission.py:1424 implements)",
        "ad_measured_nights": adn,
        "sleeves_with_no_AD_row_keep_the_modelled_scalar": sorted(
            set(ARMED + RESTATED) - set(adn.get("FTMO", {}))),
        "cells": {},
    }

    for basis in ("measured_mean", "measured_p99", "modelled_max"):
        doc["cells"][basis] = {}
        for acct in ("FTMO", "redacted_account"):
            cm = {k: statistics.median(v)
                  for k, v in Q._priced_pool(rows, acct).items()}
            per = adn.get(acct, {})
            nights_of = ({} if basis == "modelled_max"
                         else {s: v["mean" if basis == "measured_mean" else "p99"]
                               for s, v in per.items()})
            doc["cells"][basis][acct] = {}
            for name, keep in BOOKS.items():
                sub = [r for r in rows if r["sleeve"] in keep]
                days, comb, risk, vs, used = series_per_sleeve_nights(
                    sub, acct, cm, nights_of, sd_book, forward=True,
                    kelly=Q.KELLY_HALF, risk_basis=Q.RISK_LIVE_NOMINAL, fallback="max")
                lo, hi = min(days), max(days)
                sess = Q.weekday_sessions(lo, hi)
                months = (hi.year - lo.year) * 12 + (hi.month - lo.month) + 1
                cell = {"book_days": len(days), "weekday_sessions": sess,
                        "book_days_per_calendar_month": len(days) / months,
                        "mean_r_per_book_day": statistics.fmean(comb),
                        "worst_day_unit_r": min(comb),
                        "risk": risk}   # Q._derived reads it
                res = {}
                for r in Q.rule_sets(acct)[0]:
                    if r.label not in RULES:
                        continue
                    m = Q.mc(comb, risk, r, a.paths, seed_base=1)
                    res[r.label] = {"p_pass": round(m["p_pass"], 6),
                                    "se_p_pass": round(m["se_p_pass"], 6),
                                    "p_fail_dd": round(m["p_fail_dd"], 6),
                                    "p_timeout": round(m["p_timeout"], 6),
                                    **Q._derived(cell, m)}
                    print(f"  {basis:14s} {acct:11s} {name:32s} {r.label:18s} "
                          f"p={m['p_pass']:.5f}", flush=True)
                doc["cells"][basis][acct][name] = {
                    "sleeves": sorted(keep), "nights_charged": used,
                    "eff_risk_pct": round(risk * 100, 4),
                    **{k: (round(v, 5) if isinstance(v, float) else v)
                       for k, v in cell.items() if k != "risk"},
                    "rules": res}

    # ---- the answer, per account, so nobody has to read the grid ---------------------
    ans = {}
    for acct in ("FTMO", "redacted_account"):
        ans[acct] = {}
        for basis in doc["cells"]:
            c3 = doc["cells"][basis][acct]["FTMO_ARMED_TODAY_3"]
            c5 = doc["cells"][basis][acct]["FTMO_ARMED_PLUS_AD_RESTATED_5"]
            p2_3 = c3["rules"]["P2_BOTH_PHASES"]
            p2_5 = c5["rules"]["P2_BOTH_PHASES"]
            ans[acct][basis] = {
                "p_pass_3": p2_3["p_pass"], "p_pass_5": p2_5["p_pass"],
                "delta_p_pass": round(p2_5["p_pass"] - p2_3["p_pass"], 6),
                "monthly_pct_3": p2_3["monthly_pct_calendar"],
                "monthly_pct_5": p2_5["monthly_pct_calendar"],
                "monthly_pct_ratio": (round(p2_5["monthly_pct_calendar"]
                                            / p2_3["monthly_pct_calendar"], 4)
                                      if p2_3["monthly_pct_calendar"] else None),
                "cal_days_3": p2_3["median_calendar_days_to_pass"],
                "cal_days_5": p2_5["median_calendar_days_to_pass"],
                "mean_r_per_book_day_3": c3["mean_r_per_book_day"],
                "mean_r_per_book_day_5": c5["mean_r_per_book_day"],
            }
    doc["answer"] = {
        "by_account_and_carry_basis": ans,
        "reading": (
            "At the MEASURED carry the restatement's composition change earns more per calendar "
            "month and reaches a two-phase pass sooner, at a cost in p_pass. At the MODELLED max "
            "carry it looks strictly bad. Both are in the table and the difference is one "
            "modelling choice -- which nights the two added sleeves are charged. The measured "
            "basis is the one AD's own artifact supports and the one the restatement is ABOUT; "
            "the modelled basis is the assumption it replaces, so quoting only the modelled "
            "figure tests the restatement against the thing it corrects."),
        "what_this_does_NOT_settle": (
            "Whether to ARM them. p_pass still falls on every basis, `fx_jpy` still fails all "
            "five core gates and `sub_mid_dn_revert` two on the archive walk, and a faster book "
            "that is more likely to touch the drawdown floor is a risk-preference question, not "
            "a measurement. Composition is Borhen's; what changed is that the honest number is "
            "no longer one-sided."),
    }
    OUT.write_text(json.dumps(doc, indent=1, default=str))
    print(f"\nwrote {OUT.relative_to(REPO)}")
    for acct, per in ans.items():
        for basis, v in per.items():
            print(f"  {acct:11s} {basis:14s} P2 {v['p_pass_3']:.4f} -> {v['p_pass_5']:.4f} "
                  f"({v['delta_p_pass']:+.4f})  %/mo {v['monthly_pct_3']} -> "
                  f"{v['monthly_pct_5']} (x{v['monthly_pct_ratio']})  "
                  f"cal-d {v['cal_days_3']} -> {v['cal_days_5']}")


if __name__ == "__main__":
    main()
