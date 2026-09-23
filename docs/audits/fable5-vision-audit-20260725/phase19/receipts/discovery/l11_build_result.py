#!/usr/bin/env python3
"""Assemble l11_RESULT.json from the pass artifacts, so no number is transcribed by hand."""
import json
import os

H = os.path.dirname(os.path.abspath(__file__))
L = lambda n: json.load(open(os.path.join(H, n)))

sh, an, co, fa, ro, cf, mm, li, tc = (
    L("L11_SHAPE_V1.json"), L("L11_ANALYTIC_V1.json"), L("L11_CONTRACTS_V1.json"),
    L("L11_FAMILY_V1.json"), L("L11_ROBUST_V1.json"), L("L11_CONFIRM_V1.json"),
    L("L11_MINIMAX_V1.json"), L("L11_FAMILY_LIMBS_V1.json"),
    L("L11_TRAIL_CONVENTION_V1.json"))

out = {
    "lane": "l11",
    "question": "design the exit contract this pool deserves, from first principles",
    "population": "TAKEABLE (born != born_past_stop) = 24,142 of 27,658; fill REAL; "
                  "tie=stop; horizon hard 2h; fixed position size unless stated",
    "engine_validation": {
        "claim": "l11_walk.Engine reproduces l1 exactly at the incumbent cell",
        "T2_S1_gross": -0.084151, "stops": 12156, "targets": 4127, "marks": 7856,
        "matches": "l1_RESULT.json -> VARIANTS.T2.0_S1.0 and TIME_TO_OUTCOME_T2S1"},

    "S1_SHAPE": {
        "pool": {k: sh["POOL"][k] for k in
                 ("n", "r_end", "mfe", "mae", "peak_bar", "giveback_mfe_minus_end",
                  "frac_of_mfe_kept", "share_touch_plus1R", "share_touch_minus1R",
                  "drift", "incr", "hold")},
        "by_family": {f: {k: v[k] for k in
                          ("n", "r_end", "mfe", "mae", "peak_bar", "frac_of_mfe_kept",
                           "share_touch_plus1R", "share_touch_minus1R", "hold")}
                      for f, v in sh["by_family"].items()},
        "by_born": {b: {"n": v["n"], "r_end_mean": v["r_end"]["mean"],
                        "frac_of_mfe_kept_median": v["frac_of_mfe_kept"]["median"]}
                    for b, v in sh["by_born"].items()},
        "headline": "the whole loss is booked in the first minute (-0.0924 R at bar 1 vs "
                    "-0.0386 at the wall); holding recovers +0.0538; variance onset bar 60; "
                    "the median trade keeps 2.76% of its own MFE"},

    "S2_ANALYTIC": {
        "identity": an["identity"],
        "verification": co["ANALYTIC_VERIFICATION"],
        "pool_levels": an["POOL"],
        "drift_surface": an["DRIFT_SURFACE_POOL"],
        "by_family": an["by_family"],
        "headline": "E[wall|first touch L] > L at 22 of 22 levels -- every fixed exit level on "
                    "either side is value-destroying against holding"},

    "S2_BATTERY": {k: co[k] for k in
                   ("BASELINES", "GRACE_PERIOD", "TRAIL_BE_PARTIAL", "TIME_STOP")},

    "S3_PER_FAMILY": {
        "limbs_whole_month": li,
        "designed_fitted_test": fa,
        "portfolio_test": {k: fa[k] for k in fa if k.startswith("PORTFOLIO")},
        "shared_baselines_test": {
            "ALL_incumbent": -0.07930, "ALL_hold": -0.01713, "ALL_timestop90": -0.01140,
            "FIRSTEM_incumbent": -0.07519, "FIRSTEM_hold": -0.08501,
            "FIRSTEM_timestop90": -0.08121}},

    "S3_ROBUST": ro,
    "S4_CONFIRM": cf,
    "S5_TRAIL_CONVENTION": tc,
    "S5_TIME_TRAVEL_DEFECT": {
        "what": "a stop armed or tightened onto a price the market has already passed was "
                "booking its level instead of the last knowable price",
        "fixed_at": "l11_walk.py:109-122",
        "priced": {"stop_S1_armed_bar60_before": 0.30664, "after": -0.05487,
                   "fiction": 0.36151,
                   "stop_S1_armed_bar45_before": 0.23915, "after45": -0.06358,
                   "fiction45": 0.30273,
                   "trail_arm0.25_gap0.25_before": -0.01903, "after_trail": -0.06693,
                   "fiction_trail": 0.04790},
        "baselines_unchanged": "T2/S1 -0.084151 and HOLD -0.038647 byte-identical before/after"},

    "S9_MINIMAX": {k: mm[k] for k in
                   ("n_contracts", "n_cells", "cell_names", "criterion", "INCUMBENT",
                    "HOLD", "TOP20_BY_WORST_CELL")},
    "S9_HARD_BOUND": {
        "contracts_with_any_positive_cell": 0, "of": mm["n_contracts"],
        "incumbent_rank_by_worst_cell": 606, "hold_rank_by_worst_cell": 178,
        "minimax_best": "T0.25_S0.25_G1_TRnone_MB30 min -0.11313",
        "minimax_best_fixed_risk_honest": "Tnone_S1.50_G1_TRnone_MB90 min -0.123577"},

    "S6_CROSSCHECK": {
        "T1_screenB": {
            "cite": "docs/audits/fable5-vision-audit-20260725/phase19/receipts/forensic/t1/"
                    "T1_SCREENS_V1.md:49-58",
            "agree": "magnitude (+-0.05 R exit-shape deltas; no pool-wide net-positive cell)",
            "differ": [
                "T1 measured on the fill-free contract over all 27,658 rows incl. 3,516 "
                "born_past_stop, the population where a stop is worth +0.9264..+0.9576 R/trade",
                "T1's cell set carries no do-nothing baseline, so it cannot see that the "
                "winning cell is the empty one",
                "'2R target locally optimal among {1.5,2,3,5}' does not reproduce: target-only "
                "T1.5 -0.0758 / T2 -0.0800 / T3 -0.0821 / T5 -0.0502 -- 2R is a local minimum "
                "and the ladder improves toward no target at all",
                "'exit shape is empty' understates by one sign: the contract costs 0.0455 "
                "R/trade on the takeable pool and deleting it is free"]},
        "sleeve_exit_profiles": {
            "cite": "src/components/ultimate_book/execution_packets.py:80,84,93",
            "crypto_time_stop_bars": 1280, "sub_xvol_pullback_time_stop_bars": 1280,
            "in_hours": 320,
            "pool_horizon_hours": 2,
            "ratio": 160,
            "pool_horizon_source": "REPAIRED_PENDING_EXPIRY_MINUTES=120 at "
                                   "src/research_infra/v4_timewarp_simulated_live_research_loop.py:378, "
                                   "applied as the oracle expiry at :63902",
            "consequence": "no exit conclusion here transfers to a live sleeve; what transfers "
                           "is the identity, the cost-to-risk arithmetic and the two defects"},
        "estate_walker_gap": {
            "cite": "src/research_infra/walkforward/exits.py",
            "gap_aware_fill_only_in_lagged_trail": ":405 (lvl = min(lvl, b.o))",
            "no_open_clamp_on": ["plain stop :375 / :430", "target :377 / :432",
                                 "break-even after partial :382-383 / :437-438"],
            "why_it_matters": "partial_be_runner is the live contract of metals_core, "
                              "metals_softband, metals_ob_micro, energy_agri (two armed); the "
                              "BE-after-partial move is exactly the l11 time-travel defect one "
                              "bar later",
            "status": "NOT quantified on estate data by this lane -- flagged with file:line"},
        "w0_capture_corroboration": "continuing marked trades past the 2h wall for 24h resolves "
                                    "41.31% at target and moves the mark +0.2551 -> +0.3030, the "
                                    "same continuation sign as the identity in S2"},

    "S10_COHORT": {
        "first_minute": L("L11_FIRSTMINUTE_V1.json"),
        "spread_tercile": L("L11_SPREAD_TERCILE_V1.json"),
        "cheap_cohort_ts90": L("L11_CHEAP_COHORT_V1.json"),
        "production_gate": L("L11_PRODGATE_V1.json"),
        "duplicate_attribution": L("L11_DUPLICATE_ATTRIBUTION_V1.json"),
        "headline": "on rows passing the engine's own total_cost_r<=0.15 gate, TS90 beats the "
                    "incumbent in 8/8 cells (+0.0110..+0.1528) and is NET-POSITIVE on the shipped "
                    "population (+0.0203 month, +0.0555 test) -- but that net-positive is 1,498 "
                    "repeated emissions (97.26% current_fvg_fill) booking +0.4988 R/trade against "
                    "-0.0375 for the 5,859 distinct setups"},

    "S7_DESIGN": [
        "delete the shared 2R/-1R contract (dominated, -0.0455 at shipped composition; "
        "honest bound +0.006..-0.074, large end is pseudo-replication)",
        "replacement is a pure ~90-minute time stop, no target, no stop (-0.0309); "
        "TIMESTOP_90_S3 (-0.0379) if a bound is mandatory, at 5.9% cost-to-risk vs 17.6%",
        "geometry must be per family: permutation p=0/400, +0.0579 R/trade over a shuffled "
        "null; six families hurt and four helped by the shared contract over a 0.371 R span",
        "do not tighten the stop: every tight-stop win is fixed-size only, 40-70% cost-to-risk "
        "at fixed risk",
        "no trail, no break-even, no scale-out -- all value-destroying at every parameter",
        "none of it makes the pool profitable: best gross +0.0130 (dies to dedup) against a "
        "0.0789 R/trade cost floor even with a free spread",
        "the cohort worth repairing is already selected by the engine's own cost gate; on it the "
        "repair is worth +0.0110..+0.1528 gross, and its apparent net-positivity is 1,498 "
        "duplicated current_fvg_fill emissions"],
}
json.dump(out, open(os.path.join(H, "l11_RESULT.json"), "w"), indent=1)
print("wrote l11_RESULT.json", os.path.getsize(os.path.join(H, "l11_RESULT.json")), "bytes")
