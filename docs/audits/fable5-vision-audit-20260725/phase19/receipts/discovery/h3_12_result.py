"""h3-12 -- assemble h3_RESULT.json from every sub-receipt, with the findings list."""
import json
import os
import sys

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import h3_lib as H  # noqa: E402

L = {k: json.load(open(os.path.join(D, v))) for k, v in {
    "anchor": "H3_ANCHOR_V1.json", "hours": "H3_HOURS_V1.json",
    "entry": "H3_ENTRY_MECHANICS_V1.json", "entry2": "H3_ENTRY2_V1.json",
    "instruments": "H3_INSTRUMENTS_V1.json", "denom": "H3_DENOM_SWAP_V1.json",
    "cells": "H3_CELLS_V1.json", "rank": "H3_RANK_V1.json",
    "strict": "H3_STRICT_V1.json", "topcell": "H3_TOPCELL_V1.json"}.items()}

A = L["anchor"]
R = L["rank"]
res = {
    "lane": "h3",
    "question": "how much of the 2.457 bps toll can actually be removed",
    "date": "2026-08-06",
    "population": {
        "book": "LIVE-EXPRESSIBLE (at-market entries only; l10-X3: the live engine has no "
                "TRADE_ACTION_PENDING entry path)",
        "n_opportunities": 43755,
        "months": {"2026-01": 14905, "2026-02": 13966, "2026-03": 14884},
        "days": 63, "instruments": 24,
        "contract": "K5_TRAIL025 -- at-market entry delayed 5 min, 0.25R trailing stop, "
                    "the synthesis headline arm",
        "cost_object": "e_lib.real_cost_parts, ported verbatim from l10x_06_recost.py "
                       "(263.9 M ticks)"},
    "anchor_reproduction": A["anchor_check"],
    "headline": A["headline"],

    # ---------------------------------------------------------------- THE ANSWER
    "ANSWER": R["answer_to_the_lane_question"],
    "toll_decomposition_bps": A["toll_decomposition"],
    "toll_ceiling": L["entry"]["toll_ceiling"],
    "exit_side": L["entry"]["exit_side"],

    # ---------------------------------------------------------------- the six items
    "item1_entry_mechanics": {
        "arms": L["entry"]["arms"],
        "abstain_arms": L["entry2"]["abstain_arms"],
        "delay_curve_bps": L["entry2"]["delay_curve_bps"],
        "delay_lever_value_bps": L["entry2"]["delay_lever_value_bps"],
        "cancel_on_resting_cohort": L["entry2"]["cancel_on_resting_cohort"],
        "adverse_selection_by_fill_bar": L["entry"]["passive_u0_by_fill_bar"],
        "quote_convention_bracket": L["strict"]["passive_conventions"],
        "fill_rates": L["strict"]["fill_rates"]},
    "item2_hours": {
        "flat_vs_hour_aware": L["hours"]["flat_vs_hour_aware"],
        "naive_utc_mapping_arm": L["hours"]["naive_utc_mapping_arm"],
        "hour_profile_validation": L["hours"]["hour_profile_validation"],
        "peak_at_ny17_count": L["hours"]["peak_at_ny17_count"],
        "by_ny_hour": L["hours"]["by_ny_hour"],
        "by_session": L["hours"]["by_session"],
        "by_dow": L["hours"]["by_dow"],
        "frontier_exante": L["hours"]["frontier_ny_hour_exante_cost"]["frontier"],
        "frontier_insample": L["hours"]["frontier_ny_hour_insample_net"]["frontier"],
        "hour_cost_rank_spearman_between_months":
            L["hours"]["hour_cost_rank_spearman_between_months"]},
    "item3_instruments": {
        "affordability_census": L["instruments"]["affordability_census"],
        "frontier_exante_cheapest_toll": L["instruments"]["frontier_exante_cheapest_toll"]["frontier"],
        "frontier_insample_best_net": L["instruments"]["frontier_insample_best_net"]["frontier"],
        "frontier_trainjan_cost_testfebmar":
            L["instruments"]["frontier_trainjan_cost_testfebmar"]["frontier"],
        "frontier_trainjan_net_testfebmar":
            L["instruments"]["frontier_trainjan_net_testfebmar"]["frontier"],
        "rank_stability": L["instruments"]["rank_stability"],
        "train_test": L["strict"]["train_test_instrument_choice"],
        "cost_order_jan_vs_pooled_identical_top6":
            L["strict"]["cost_order_jan_vs_pooled_identical_top6"]},
    "item4_stop_width": {
        "log_variance_decomposition": L["denom"]["log_variance_decomposition"],
        "spearman_cost_r_vs_inverse_stop": L["denom"]["spearman_cost_r_vs_inverse_stop"],
        "spearman_cost_r_vs_cost_bps": L["denom"]["spearman_cost_r_vs_cost_bps"],
        "family_dispersion": L["denom"]["family_dispersion"],
        "symbol_dispersion": L["denom"]["symbol_dispersion"],
        "stop_widen_identity": L["denom"]["stop_widen_identity"],
        "rdp_deciles": L["denom"]["rdp_deciles"]},
    "item5_holding_and_swap": {
        "swap": L["denom"]["swap"],
        "holding_time_amortisation": L["denom"]["holding_time_amortisation"],
        "by_realised_hold": L["denom"]["by_realised_hold"],
        "contract_menu_at_k5": L["denom"]["contract_menu_at_k5"]},
    "item6_ranked_levers": sorted(R["levers"],
                                  key=lambda d: -(d["efficiency_toll_bps_per_opportunity_lost"]
                                                  if d["efficiency_toll_bps_per_opportunity_lost"]
                                                  is not None else -1e9)),
    "composites": R["composites"],

    # ---------------------------------------------------------------- the cells
    "cells": {
        "lead_cell": {"spec": L["topcell"]["lead_cell_spec"],
                      "flat_cost": L["topcell"]["lead_cell"],
                      "hour_aware_cost": L["topcell"]["lead_cell_hour_aware"],
                      "by_symbol": L["topcell"]["lead_by_symbol"],
                      "by_month": L["topcell"]["lead_by_month"],
                      "leave_one_symbol_out": L["topcell"]["lead_leave_one_symbol_out"],
                      "leave_one_month_out": L["topcell"]["lead_leave_one_month_out"],
                      "day_concentration": L["topcell"]["lead_day_concentration"],
                      "threshold_curve": L["topcell"]["threshold_curve"]},
        "other_cells": L["topcell"]["other_cells"],
        "symbol_cells": L["cells"]["C_cells_symbol_unconditional"],
        "hour_cells": L["cells"]["C_cells_ny_hour_unconditional"],
        "family_cells": L["cells"]["C_cells_family_unconditional"],
        "symbol_x_noretrace_best": L["cells"]["C_symbol_x_noretrace_best"]},
}

res["findings"] = [
    {"id": "h3-F1",
     "claim": "The toll cannot be cut ten-fold. The mechanical floor is commission-only and "
              "that is a 4.32x cut, not 10.63x -- and at that unreachable floor the pooled "
              "edge still earns only 41% of its toll.",
     "numbers": {"toll_bps": 2.4571, "spread_bps": 1.8104, "commission_bps": 0.5686,
                 "slippage_bps": 0.0782, "floor_bps": 0.5686, "max_reduction_x": 4.3216,
                 "max_removable_pct": 0.7686,
                 "reduction_required_at_current_edge_x": 10.6281,
                 "edge_over_toll_at_floor": 0.4066},
     "confidence": "measured", "n": 43755},
    {"id": "h3-F2",
     "claim": "Passive entry is the largest removable component and it does not pay under "
              "EITHER quote convention. Resting a limit at the decision price removes 0.905 bps "
              "(mid convention) or 1.810 bps (bid convention) of toll and destroys 2.02 bps or "
              "3.07 bps of edge respectively. The archive does not record the quote side "
              "(bar header is time,open,high,low,close,volume) so both were measured; the sign "
              "is the same both ways.",
     "numbers": {"mid_toll_bps": 1.4799, "mid_edge_bps": -1.7915, "mid_net_bps": -3.2714,
                 "bid_toll_bps": 0.5791, "bid_edge_bps": -2.8415, "bid_net_bps": -3.4206,
                 "baseline_net_bps": -2.2259,
                 "share_of_passive_fills_in_first_60s": 0.762,
                 "first_60s_fill_edge_bps": -2.6402},
     "confidence": "measured", "n": 43755},
    {"id": "h3-F3",
     "claim": "Instrument selection is the only large toll lever, it is EX ANTE, and its "
              "ranking is deterministic: the per-symbol cost rank correlates 0.994-0.999 across "
              "the three months while the per-symbol EDGE rank correlates 0.008-0.174.",
     "numbers": {"cost_rank_spearman": [0.9948, 0.9939, 0.9991],
                 "edge_rank_spearman": [0.1739, 0.1226, 0.0078],
                 "net_rank_spearman": [0.7930, 0.8600, 0.6835],
                 "toll_saved_dropping_6_dearest_bps": 1.4827,
                 "opportunity_lost": 0.2323,
                 "efficiency_bps_per_unit_opportunity": 6.3804},
     "confidence": "measured", "n": 43755},
    {"id": "h3-F4",
     "claim": "Hour selection is the weakest lever by an order of magnitude. The cheapest "
              "single NY hour cuts the toll 15.9% for 91.9% of the book, an efficiency of 0.4633 "
              "bps per unit of opportunity against the instrument lever's 6.3804 -- a 13.8x gap. "
              "The whole ex-ante hour frontier sits in an efficiency band of 0.447-0.511 and "
              "never buys more than 0.4255 bps of toll.",
     "numbers": {"toll_all_hours_bps": 2.6692, "toll_cheapest_hour_bps": 2.2437,
                 "keep_rate_at_cheapest_hour": 0.0815,
                 "best_efficiency_bps_per_unit_opportunity_hour_consistent": 0.4633,
                 "hour_frontier_efficiency_band": [0.4469, 0.5112],
                 "instrument_lever_efficiency_for_comparison": 6.3804,
                 "gap_x": 13.77},
     "confidence": "measured", "n": 43755},
    {"id": "h3-F5",
     "claim": "Hour-aware costing RAISES the toll 8.63%: the pool sits in hours that are more "
              "expensive than the flat per-symbol median the whole estate charges. The mapping "
              "is validated independently -- the tick spread peaks at NY 17:00, broker midnight, "
              "on 13 of 24 instruments.",
     "numbers": {"flat_toll_bps": 2.4571, "hour_aware_toll_bps": 2.6692, "ratio": 1.0863,
                 "naive_broker_minus_3_arm_bps": 2.6247,
                 "rollover_hour_toll_bps": 8.5091, "rollover_hour_flat_bps": 1.8826,
                 "rollover_hour_share_of_book": 0.0212},
     "confidence": "measured", "n": 43755},
    {"id": "h3-F6",
     "claim": "Stop width is 100% denominational and the estate's famous 12.1x family cost "
              "dispersion is mostly the stop, not the money. Widening the stop by any factor f "
              "divides cost_r by exactly f and leaves cost_bps EXACTLY unchanged. Across "
              "families cost_r disperses 12.40x while real cost_bps disperses only 2.81x; across "
              "INSTRUMENTS it inverts -- 7.35x in R against 24.41x in bps.",
     "numbers": {"family_cost_r_spread_x": 12.402, "family_cost_bps_spread_x_all10": 2.805,
                 "family_cost_bps_spread_x_n_ge_100": 1.230,
                 "family_rdp_spread_x": 14.85, "symbol_cost_r_spread_x": 7.35,
                 "symbol_cost_bps_spread_x": 24.41,
                 "var_ln_cost_r": 1.1435, "var_ln_rdp": 1.4228, "var_ln_cost_bps": 0.8665,
                 "stop_width_share_of_var": 1.2442, "identity_residual": -2.2e-16,
                 "max_edge_over_toll_across_10_rdp_deciles": 0.320},
     "confidence": "measured", "n": 43755},
    {"id": "h3-F7",
     "claim": "l10-X7.2's 'regime_transition_break pays 0.0405 R, the closest thing to breakeven "
              "in the estate' is right about the verdict and wrong about the reason. In price "
              "space that family pays 2.6255 bps, ABOVE the 2.4571 pool mean. It looks cheap "
              "only because it emits the widest stops in the pool (97.85 bps of price against "
              "structural_distance_extreme's 6.59). Its edge:toll of 1.375 is entirely edge.",
     "numbers": {"cost_r": 0.0339, "cost_bps": 2.6255, "pool_cost_bps": 2.4571,
                 "rdp_bps": 97.85, "edge_bps": 3.6099, "edge_over_toll": 1.375},
     "confidence": "measured", "n": 828},
    {"id": "h3-F8",
     "claim": "Swap is exactly zero on this horizon and the frozen model charges 0.173 bps of it "
              "anyway. Only 0.83% of trades have a holding window that can even reach a broker "
              "rollover; broker-true swap charged is 0.0 bps; the frozen model bills 2.70% of "
              "its own toll as carry that cannot be incurred. There is no swap lever here.",
     "numbers": {"share_reaching_rollover": 0.0083, "broker_true_swap_bps": 0.0,
                 "frozen_swap_bps": 0.1727, "frozen_total_bps": 6.3891,
                 "frozen_swap_share": 0.0270},
     "confidence": "measured", "n": 43755},
    {"id": "h3-F9",
     "claim": "bps space and R space DISAGREE IN SIGN on several apparently paying cells, and R "
              "is the space that compounds. NY hour 13 reads +1.410 bps net and -0.130 R/trade; "
              "the two cheapest instruments read +0.186 bps and -0.001 R. Any cell reported in "
              "bps alone can be an artifact of wide-stop trades carrying the price-space average.",
     "numbers": {"ny13_net_bps": 1.4103, "ny13_net_r": -0.1301,
                 "cheap2_net_bps": 0.1859, "cheap2_net_r": -0.00107,
                 "leadcell_net_bps": 0.6887, "leadcell_net_r": 0.014213},
     "confidence": "measured", "n": 43755},
    {"id": "h3-F10",
     "claim": "CELL: `regime_transition_break` at the plain headline arm is the most robust cell "
              "found. edge:toll 1.375 flat / 1.297 hour-aware, POSITIVE IN BOTH SPACES and BOTH "
              "cost bases, 3 of 3 months above 1, spread over all 24 instruments, and net R stays "
              "positive in all 24 leave-one-instrument-out arms. Caveat: n=828, bootstrap "
              "p(net R <= 0) = 0.156, 32 of 63 days positive, top day 29.0% of the R total, and "
              "it is 1 of 10 families so it carries a 10-look bill it has not been charged.",
     "numbers": {"n": 828, "edge_bps": 3.6099, "toll_bps": 2.6255, "edge_over_toll": 1.375,
                 "net_r": 0.01526, "hour_aware_edge_over_toll": 1.297,
                 "hour_aware_net_r": 0.00874,
                 "months_e_over_t": [1.339, 1.715, 1.129],
                 "months_net_r": [0.01100, 0.02226, 0.01345],
                 "boot_p_net_r_le_0": 0.156, "boot_p_net_bps_le_0": 0.277,
                 "leave_one_out_net_r_range": [0.00617, 0.02498],
                 "days_positive_R": 32, "days": 63, "top_day_share_R": 0.290},
     "confidence": "measured"},
    {"id": "h3-F11",
     "claim": "CELL: a NO-RETRACE filter plus the six cheapest instruments, entered at MARKET on "
              "the touch, reaches edge:toll 2.105 and is convention-invariant and implementable "
              "with the engine that exists today. Rule: at the decision, watch; if price has NOT "
              "traded back through the decision price for 10 minutes, buy at market the moment "
              "it does. Caveat: n=814, in-sample threshold chosen from ~30, top 3 days carry "
              "56.6% of the bps total, and dropping GER40 takes net R to -0.00035.",
     "numbers": {"n": 814, "edge_bps": 1.3118, "toll_bps": 0.6231, "edge_over_toll": 2.1052,
                 "net_bps": 0.6887, "net_r": 0.014213,
                 "hour_aware_edge_over_toll": 1.4750, "hour_aware_net_r": -0.023865,
                 "boot_p_net_bps_le_0": 0.0625, "boot_p_net_r_le_0": 0.2825,
                 "months_e_over_t": [1.331, 2.149, 2.888],
                 "days_positive": 33, "days": 63, "top3_day_share": 0.566,
                 "drop_GER40_net_r": -0.00035},
     "confidence": "measured"},
    {"id": "h3-F12",
     "claim": "CELL: the two cheapest instruments chosen by JANUARY COST ONLY hold out of sample "
              "-- edge:toll 1.157 on the training month and 1.544 on the never-used Feb+Mar. The "
              "selection uses no outcome data and the cost order is 0.994-stable, so it travels "
              "by construction. Caveat: it is positive in bps and NEGATIVE in R (-0.00107/trade), "
              "and hour-aware costing takes it from 1.412 to 1.053.",
     "numbers": {"train_jan_n": 1299, "train_jan_e_over_t": 1.157,
                 "test_febmar_n": 2501, "test_febmar_e_over_t": 1.544,
                 "test_febmar_net_bps": 0.2459, "pooled_e_over_t": 1.412,
                 "pooled_net_r": -0.00107, "hour_aware_e_over_t": 1.053,
                 "k3_test_e_over_t": 0.919},
     "confidence": "measured"},
    {"id": "h3-F13",
     "claim": "The entry-timing delay is a bigger bps lever than the entire removable half-spread "
              "and it costs no opportunity at all: +0.734 bps of edge from minute 0 to minute 20, "
              "against 0.905 bps of removable entry spread that cannot be captured. Toll is "
              "IDENTICAL at every delay.",
     "numbers": {"k0_edge_bps": -0.5030, "k5_edge_bps": 0.2312, "k20_edge_bps": 0.5395,
                 "gain_k0_to_k5_bps": 0.7342, "gain_k0_to_k20_bps": 1.0425, "toll_bps_at_every_k": 2.4571,
                 "months_at_k20": [0.306, 0.636, 0.683]},
     "confidence": "measured", "n": 43755},
    {"id": "h3-F14",
     "claim": "The 60-second CANCEL is worth +0.449 bps of EDGE and 0.005 bps of toll -- it is "
              "not a cost lever at all -- and it lives on a cohort the live engine cannot place. "
              "On born_resting (29.9% of the pool) refusing fills touched inside 60 s moves edge "
              "0.937 -> 1.386 bps at an 88.1% keep rate.",
     "numbers": {"all_resting_edge_bps": 0.9371, "survivors_edge_bps": 1.3863,
                 "early_touch_edge_bps": -2.3877, "toll_change_bps": 0.0053,
                 "keep_rate": 0.8810, "n_resting": 23426},
     "confidence": "measured"},
    {"id": "h3-F15",
     "claim": "Under the headline trailing contract there is no exit-side spread to save: 93.7% "
              "of exits are stops and 0% are limit-able targets. The 0.905 bps exit half-spread "
              "is only addressable under a target contract, where 19.5% of exits rest, worth "
              "0.176 bps -- and that contract's edge is 0.526 bps WORSE.",
     "numbers": {"trail025_stop_share": 0.9370, "trail025_target_share": 0.0,
                 "inc_target_share": 0.1948, "inc_exit_saving_bps": 0.1763,
                 "inc_edge_bps": -0.2954, "trail025_edge_bps": 0.2312},
     "confidence": "measured", "n": 43755},
]

res["scripts"] = ["h3_lib.py", "h3_01_anchor.py", "h3_02_passive_build.py", "h3_03_hours.py",
                  "h3_04_passive.py", "h3_05_entry2.py", "h3_06_instruments.py",
                  "h3_07_cells.py", "h3_08_denom_swap.py", "h3_09_rank.py",
                  "h3_10_strict.py", "h3_11_topcell.py", "h3_12_result.py"]
res["artifacts"] = ["H3_ANCHOR_V1.json", "H3_HOURS_V1.json", "H3_ENTRY_MECHANICS_V1.json",
                    "H3_ENTRY2_V1.json", "H3_INSTRUMENTS_V1.json", "H3_DENOM_SWAP_V1.json",
                    "H3_CELLS_V1.json", "H3_RANK_V1.json", "H3_STRICT_V1.json",
                    "H3_TOPCELL_V1.json", "H3_PASSIVE_ROWS_2026{01,02,03}.jsonl.gz",
                    "H3_STRICT_ROWS_V1.jsonl.gz", "h3_RESULT.md", "h3_RESULT.json"]

p = H.dump(res, "h3_RESULT.json")
print("findings:", len(res["findings"]), "->", p, os.path.getsize(p), "bytes")
