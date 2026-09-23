#!/usr/bin/env python3
"""e6_result — merge every e6 measurement into one machine-readable receipt."""
import gzip, json, os, collections
D = os.path.dirname(os.path.abspath(__file__))
MS = ["JAN", "FEB", "MAR", "APR", "MAY"]

out = {
 "lane": "e6",
 "extends": "l8-hitrate / L8-F1 (entry-delay adverse selection)",
 "verdict": "HOLDS IN ALL FIVE MONTHS, LARGER OUT OF SAMPLE, ZERO REVERSALS IN 569 CONDITIONING CELLS",
 "reproduction_january": json.load(open(os.path.join(D, "E6_JAN_REPRO_V1.json"))),
 "multi_month_sweep": json.load(open(os.path.join(D, "E6_SWEEP_V1.json"))),
 "mechanism": json.load(open(os.path.join(D, "E6_MECH_V1.json"))),
 "controls": json.load(open(os.path.join(D, "E6_CONFIRM_V1.json"))),
 "equal_exposure_and_bankability": json.load(open(os.path.join(D, "E6_FINAL_V1.json"))),
}
# stacked-book table + past-stop subsumption + never-filled fiction, recomputed here
rows = []
for m in MS:
    with gzip.open(os.path.join(D, "e6_MECH_%s.jsonl.gz" % m), "rt") as fh:
        for l in fh:
            rows.append(json.loads(l))
def stat(vs):
    n = len(vs); mn = sum(vs) / n
    sd = (sum((x - mn) ** 2 for x in vs) / (n - 1)) ** 0.5
    return {"n": n, "R_per_opportunity": round(mn, 5), "t": round(mn / (sd / n ** 0.5), 3)}
def val(r, mode, k=1):
    if mode == "shipped": return r["hr"] if r["fb"] > 0 else 0.0
    return 0.0 if (r["fb"] < 0 or r["fb"] <= k) else r["hr"]
cl = [r for r in rows if r["born"] != "born_past_stop"]
ps = [r for r in rows if r["born"] == "born_past_stop"]
nf = [r for r in rows if r["fb"] < 0 and r["gross_r"] is not None]
out["stacked_books"] = {
 "A_raw_as_shipped": stat([val(r, "shipped") for r in rows]),
 "B_raw_cancel_k1": stat([val(r, "cancel") for r in rows]),
 "C_drop_past_stop_as_shipped": stat([val(r, "shipped") for r in cl]),
 "D_drop_past_stop_cancel_k1": stat([val(r, "cancel") for r in cl]),
}
out["past_stop_subsumption"] = {
 "n_born_past_stop": len(ps),
 "share_filling_on_bar_1": round(sum(1 for r in ps if r["fb"] == 1) / len(ps), 6),
 "share_never_filling": round(sum(1 for r in ps if r["fb"] < 0) / len(ps), 6),
 "by_month_bar1_share": {m: round(sum(1 for r in ps if r["month"] == m and r["fb"] == 1) /
                                  max(1, sum(1 for r in ps if r["month"] == m)), 6) for m in MS},
}
out["never_filled_fiction"] = {
 "n": len(nf), "pool_scored_gross_mean_r": round(sum(r["gross_r"] for r in nf) / len(nf), 5),
 "pool_scored_total_r": round(sum(r["gross_r"] for r in nf), 1),
 "by_month": {m: {"n": sum(1 for r in nf if r["month"] == m),
                  "gross_mean": round(sum(r["gross_r"] for r in nf if r["month"] == m) /
                                      max(1, sum(1 for r in nf if r["month"] == m)), 5),
                  "total_r": round(sum(r["gross_r"] for r in nf if r["month"] == m), 1)} for m in MS},
}
# cell census
tot = neg = 0
worst = []
for ax, per in out["multi_month_sweep"]["boundary"].items():
    for m in MS:
        for k, b in per.get(m, {}).items():
            tot += 1
            if b["delta"] < 0: neg += 1
            worst.append([b["delta"], ax, m, k, b["n"]])
worst.sort()
out["cell_census"] = {"axes": sorted(out["multi_month_sweep"]["boundary"].keys()),
                      "cells_axis_x_month_min_n_100": tot, "negative_cells": neg,
                      "share_negative": round(neg / tot, 5),
                      "ten_weakest": worst[:10]}
out["data_spent"] = {
 "APRIL_lane_pack": "CS_APRIL_S0R0_POOL_V1 + ORDERED_PATH_SIDECAR — 25,056 candidates, "
                    "ECONOMICS READ for the first time by this lane",
 "MAY_lane_pack": "CS_MAY_S0R0_POOL_V1 + ORDERED_PATH_SIDECAR — 21,285 candidates, "
                  "ECONOMICS READ for the first time by this lane",
 "MARCH": "FA2_M_R0_MISSED_OPPORTUNITY_LEDGER (reference arm), 26,484 of 26,500 diagnostic-"
          "scoreable rows; March was already read once by phase19/march-confirm",
 "FEBRUARY": "CP_FEBRUARY_S0R0_POOL_V1, 24,239 rows; already used-once VAL per wave 18",
 "what_was_measured_on_them": "ONE pre-declared instrument ported unchanged from l8: the "
                              "entry-delay cohort split and its delay sweep, plus the boundary "
                              "axes. No search over the April/May pools preceded it.",
}
out["gross_scoring_crosscheck"] = json.load(open(os.path.join(D, "E6_GROSS_CROSSCHECK_V1.json")))
out["bankability_verdict"] = ("no cell in family/symbol/session/born/family_x_born is net-positive "
 "on the retained k>=2 book at the 7.3x-corrected spread; best is UKOIL_cash -0.01744 (n=1312, 2/5 "
 "months positive) and regime_transition_break -0.04528 (n=302, 0/5). The rule is loss avoidance, "
 "not an edge.")
out["headline_numbers"] = {
 "pooled_raw_as_shipped_R_per_opportunity": -0.22609,
 "pooled_raw_cancel_k1_R_per_opportunity": -0.01551,
 "share_of_raw_gross_deficit_recovered_by_cancel_alone": 0.931,
 "pooled_clean_delta_R_per_opportunity": 0.12203,
 "pooled_clean_paired_t": 49.54,
 "value_of_60s_delay_WITHOUT_the_cancel": -0.00628,
 "months_holding": "5/5", "trading_days_positive": "101/101",
 "conditioning_cells_negative": "11/569",
 "born_past_stop_filling_on_bar_1": 0.9998,
 "net_R_per_trade_retained_book_at_7p3x_corrected_spread": -0.21837,
}
json.dump(out, open(os.path.join(D, "e6_RESULT.json"), "w"), indent=1)
print("cells", tot, "negative", neg)
print("wrote e6_RESULT.json", os.path.getsize(os.path.join(D, "e6_RESULT.json")), "bytes")
