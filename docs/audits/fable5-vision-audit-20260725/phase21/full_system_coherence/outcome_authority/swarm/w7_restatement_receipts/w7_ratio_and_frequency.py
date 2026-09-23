#!/usr/bin/env python3
"""W7 INSTRUMENT RESTATEMENT — part 3: the 14.38x reconciliation and the frequency check.

Measurement only.

Q4  Is the 14.38x gap between the W7 cache and the archive INSTRUMENT, POPULATION or
    PERIOD?  Decomposed exactly, then each factor attributed.

Q(coordinator).4  Does the MC's trade-frequency assumption inflate `p_pass`?
"""
from __future__ import annotations

import collections
import gzip
import json
import math
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[8]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import mc_firm_rules as Q          # noqa: E402
import recost_w7_validation as M   # noqa: E402

HERE = Path(__file__).resolve().parent
AUD = REPO / "docs/audits/fable5-vision-audit-20260725"
BOOKS_MC = AUD / "phase8/receipts/BOOKS_MC_V1.json"
R1_ROWS = AUD / "phase20/receipts/r1/R1_ESTATE_ROWS_V1.json.gz"

ARMED_3 = ["crypto", "energy_agri", "sub_xvol_pullback"]


def main():
    out = {"schema": "gtos.wave21.w7_ratio_and_frequency.v1", "measurement_only": True}

    # ---------------- Q4: exact decomposition of the published ratio ----------------
    bm = json.load(open(BOOKS_MC))["the_population_gap_on_the_armed_book"]
    cache = bm["W7_CACHE_forward_2025_plus_worst_carry"]
    arch = bm["ARCHIVE_whole_span"]
    ab = json.load(open(BOOKS_MC))["archive_books"][
        "CONTROL_FTMO_ARMED_TODAY_3_on_the_archive"]

    cache_bdpm = 6.5      # 117 book-days / 18 calendar months (measured in part 1)
    arch_bdpm = ab["book_days_per_calendar_month"]
    edge_ratio = cache["mean_r_per_book_day"] / arch["mean_r_per_book_day"]
    freq_ratio = cache_bdpm / arch_bdpm
    prod = edge_ratio * freq_ratio
    out["q4_ratio_decomposition"] = dict(
        published_ratio=bm["ratio_monthly_pct"],
        cache=dict(mean_r_per_book_day=cache["mean_r_per_book_day"],
                   book_days=cache["book_days"], book_days_per_month=cache_bdpm,
                   monthly_pct=cache["monthly_pct_calendar"],
                   window="2025-01-02..2026-06-12 (18 calendar months)"),
        archive=dict(mean_r_per_book_day=arch["mean_r_per_book_day"],
                     book_days=arch["book_days"],
                     book_days_per_month=arch_bdpm,
                     monthly_pct=arch["monthly_pct_calendar"],
                     window=ab["window"]),
        factor_edge_per_book_day=edge_ratio,
        factor_book_days_per_month=freq_ratio,
        product=prod,
        reproduces_published=abs(prod - bm["ratio_monthly_pct"]) < 0.02,
        log_share_frequency=math.log(freq_ratio) / math.log(prod),
        log_share_edge=math.log(edge_ratio) / math.log(prod),
        verdict=("the ratio is 7.83x FREQUENCY and 1.84x edge-per-book-day; "
                 "frequency is 77 % of it in log terms"))

    # ---- is the frequency factor PERIOD or POPULATION? measured on the archive walk --
    r1 = json.load(gzip.open(R1_ROWS, "rt"))
    a3 = [r for r in r1 if r["sleeve"] in ARMED_3]
    days_all = sorted({r["entry_utc"][:10] for r in a3})
    days_25 = [d for d in days_all if d >= "2025-01-01"]
    first, last = days_all[0], days_all[-1]
    months_all = ((int(last[:4]) - int(first[:4])) * 12
                  + (int(last[5:7]) - int(first[5:7])) + 1)
    last25 = days_25[-1] if days_25 else None
    months_25 = (((int(last25[:4]) - 2025) * 12 + int(last25[5:7])) if last25 else 0)
    out["q4_is_the_frequency_factor_period_or_population"] = dict(
        source="R1_ESTATE_ROWS_V1.json.gz (the archive walk), armed three only",
        n_trades=len(a3), first_day=first, last_day=last,
        distinct_signal_days_whole_span=len(days_all),
        calendar_months_whole_span=months_all,
        signal_days_per_month_whole_span=len(days_all) / months_all,
        distinct_signal_days_2025_plus=len(days_25),
        calendar_months_2025_plus=months_25,
        signal_days_per_month_2025_plus=(len(days_25) / months_25 if months_25 else None),
        within_archive_period_ratio=((len(days_25) / months_25)
                                     / (len(days_all) / months_all)
                                     if months_25 else None),
        verdict=("if the archive's OWN 2025+ firing rate is far above its whole-span "
                 "rate, the 7.83x frequency factor is a PERIOD/COVERAGE property of the "
                 "archive's thin early history, not an edge claim and not the instrument"))

    # ---------------- frequency sensitivity on the headline -------------------------
    st = M.build([])
    rows = st["rows"]
    for r in rows:
        r["R_legacy"] = r["R"]
    _, _, _, sd_book = M.build_matrix_from(rows, "R_legacy")
    pool = collections.defaultdict(list)
    for r in rows:
        c = r["cost_FTMO"]
        if c["status"] == "priced":
            pool[r["sleeve"]].append(c["cost_ex_swap_r"])
    cm = {k: statistics.median(v) for k, v in pool.items()}
    sub = [r for r in rows if r["sleeve"] in ARMED_3]
    days, comb, risk, _ = Q.series(sub, "FTMO", cm, "max", sd_book, forward=True,
                                   kelly=Q.KELLY_HALF, risk_basis=Q.RISK_LIVE_NOMINAL)
    rules, _ = Q.rule_sets("FTMO")
    P2 = [r for r in rules if r.label == "P2_BOTH_PHASES"][0]
    res = Q.mc(comb, risk, P2, 60_000, seed_base=1)
    mean_r = statistics.fmean(comb)

    # Lane F: 1 signal day per account in ~12.85 d armed -> ~2.33 book-days/month
    lane_f_bdpm = 1 / (12.85 / 30.44)
    scen = {}
    for lab, bdpm in (("MC_ASSUMPTION_in_window_2025_plus", 6.5),
                      ("LIVE_MEASURED_lane_F", lane_f_bdpm),
                      ("ARCHIVE_whole_span", arch_bdpm),
                      ("CLAUDE_MD_expectation_7_book_days_per_month", 7.0)):
        scen[lab] = dict(
            book_days_per_month=bdpm,
            monthly_pct=100.0 * mean_r * risk * bdpm,
            median_calendar_days_to_pass=res["med_days_pass"] / bdpm * 30.44,
            p_pass=res["p_pass"],
            note=("p_pass is INVARIANT to frequency: the MC draws book-days until a "
                  "barrier is hit and p_timeout is 0.0, so frequency scales calendar "
                  "time and the %/month headline, not the probability"))
    out["frequency_sensitivity"] = dict(
        p_pass_at_60k_paths=res["p_pass"], p_timeout=res["p_timeout"],
        median_book_days_to_pass=res["med_days_pass"],
        mean_r_per_book_day=mean_r, risk_fraction=risk,
        scenarios=scen,
        poisson_check=("Lane F: 1 signal day in ~13 d against lambda 2.96 expected, "
                       "P(X<=1) = 0.206 -- underpowered, not yet a contradiction"))

    (HERE / "W7_RATIO_AND_FREQUENCY_V1.json").write_text(
        json.dumps(out, indent=1, default=str))
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
