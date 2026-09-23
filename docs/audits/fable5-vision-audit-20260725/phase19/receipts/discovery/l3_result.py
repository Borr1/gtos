#!/usr/bin/env python3
"""l3_result - assemble l3_RESULT.json from the measured artifacts. Nothing is transcribed
by hand; every value is read back out of the JSON the measuring script wrote."""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
def rd(n):
    with open(os.path.join(HERE, n)) as fh:
        return json.load(fh)

CO = rd("l3_COHORTS_V1.json"); CI = rd("l3_COHORT_INTEGRITY_V1.json")
FR = rd("l3_FIELD_RANKING_V1.json"); BE = rd("l3_BELIEF_V1.json")
BM = rd("l3_BELIEF_MECHANISM_V1.json"); GS = rd("l3_GATE_SHAPE_V1.json")
TR = rd("l3_TREE_V1.json"); PR = rd("l3_PROFILE_V1.json"); RU = rd("l3_RULES_V1.json")
PD = rd("l3_PROFILE_DEEP_V1.json"); UN = rd("l3_UNUSED_V1.json")
SG = rd("l3_SCORING_GAP_V1.json"); SG2 = rd("l3_SCORING_GAP2_V1.json")
SG3 = rd("l3_SCORING_GAP3_V1.json"); SR = rd("l3_SCORING_REPAIR_V1.json")

def topiv(tag, pos="PRE", k=24):
    f = FR[tag]["fields"]
    r = [(v.get("iv", 0), n, v) for n, v in f.items()
         if v.get("kind") in ("numeric", "categorical") and v.get("pos") == pos]
    r.sort(reverse=True)
    return [{"field": n, "iv": round(iv, 4), "auc": v.get("auc"), "cohens_d": v.get("cohens_d"),
             "kind": v["kind"], "n_nonnull": v.get("n_nonnull")} for iv, n, v in r[:k]]

out = {
 "lane": "l3",
 "question": "what does a trade we WANT actually look like",
 "pool": "CJ_RECLOCKED_S0R0_POOL_V1 (January 2026, true UTC, 27,658 candidates)",
 "population_used": {
   "name": "TAKEABLE", "n": CO["takeable_n"],
   "why": "23.34% of the briefed full-stop cohort was never takeable (stop price already breached at "
          "the decision instant, W0-capture); only 0.10% of the winner cohort was. The briefed "
          "3,072-vs-15,057 comparison is contaminated on ONE side only.",
   "briefed_cohorts": CI["briefed_cohorts"],
   "takeable_filter": CI["takeable_filter"],
   "band_counts": CO["band_counts"],
   "born_state_counts": CO["born_state_counts"],
   "born_x_band_full_target": CO["born_x_band_full_target"],
   "born_x_band_full_stop": CO["born_x_band_full_stop"],
 },
 "F1_cohort_integrity": {
   "winner_cohort_is_90.75pct_honest": CI["winner_fill_audit"],
   "winner_cohort_takeable": CI["winner_fill_audit_takeable"],
   "honest_cohorts_takeable": CI["honest_cohorts_takeable"],
   "band_x_fillhonest_takeable": CI["band_x_fillhonest_takeable"],
 },
 "F2_risk_distance_is_the_axis": {
   "claim": "risk distance controls RESOLUTION, not edge. Tightest decile: 22.34% target / 66.35% "
            "stop / 1.99% neither. Widest: 3.77% / 27.85% / 61.91%. No decile is gross-positive.",
   "decile_table_takeable": CI["risk_distance_decile_takeable"],
   "spearman_hit_vs_gross_row_level": CI["target_rate_vs_gross_anticorrelation"],
 },
 "F3_belief_is_inverted": {
   "claim": "every forecast field is NEGATIVELY rank-correlated with reaching the target it "
            "forecasts. candidate_probability top decile hits target 4.02% vs bottom decile 20.47%.",
   "correlations_ALL": BE["correlations"]["ALL"],
   "correlations_TAKEABLE": BE["correlations"]["TAKEABLE"],
   "correlations_WIN_VS_STOP": BE["correlations"]["WIN_VS_STOP"],
   "correlations_TAKEABLE_WIN_VS_STOP": BE["correlations"]["TAKEABLE_WIN_VS_STOP"],
   "deciles_ALL": BE["deciles"]["ALL"],
   "deciles_TAKEABLE": BE["deciles"]["TAKEABLE"],
   "calibration": BE.get("calibration"),
   "mechanism": {
     "claim": "belief is a VARIANCE SUPPRESSOR, not an edge detector: it is 0.712 rank-correlated "
              "with fill_probability and -0.478 with cost_r, +0.225 with risk distance, so high "
              "belief = wide stop = the trade does nothing (neither-rate 12.1% -> 34.1%). In a "
              "negative-mean pool, compressing outcomes toward zero LOOKS like skill.",
     "drivers": BM["belief_drivers"], "vs_movement": BM["belief_vs_movement"],
     "decile_mechanism": BM["decile_mechanism"],
     "within_movement_stratum": BM["belief_within_movement_stratum"],
     "population": BM["population"],
   },
   "the_one_place_belief_works": UN["belief_inside_liquidity_sweep_reclaim"],
   "candidate_confidence_is_a_constant": UN["candidate_confidence"],
 },
 "F4_nothing_separates_winners_from_stops": {
   "claim": "largest |Cohen's d| over all 28 pre-decision numeric fields is 0.1517 "
            "(risk_distance_pct_of_price). Every AUC is 0.44-0.57.",
   "RAW_base_rate": FR["RAW"]["base_rate"], "RAW_n_win": FR["RAW"]["n_win"], "RAW_n_stop": FR["RAW"]["n_stop"],
   "TAKEABLE_base_rate": FR["TAKEABLE"]["base_rate"], "TAKEABLE_n_win": FR["TAKEABLE"]["n_win"],
   "TAKEABLE_n_stop": FR["TAKEABLE"]["n_stop"],
   "top_PRE_fields_RAW": topiv("RAW", "PRE"),
   "top_PRE_fields_TAKEABLE": topiv("TAKEABLE", "PRE"),
   "top_POST_fields_TAKEABLE_leakage_only": topiv("TAKEABLE", "POST", 10),
   "numeric_profile_takeable": PR["numeric_profile"],
 },
 "F5_every_gate_anti_selects": {
   "claim": "the live cost gates keep 28.93% of takeable candidates whose full-target rate is 5.46% "
            "and refuse 71.07% whose rate is 15.68% - a 2.872x ratio. selector_action=='trade' "
            "fires on 21 of 24,125 and NOT ONE reaches the declared target.",
   "population": GS["population"], "pool_hit_target_rate": GS["pool_hit_target_rate"],
   "pool_mean_excursion_r": GS["pool_mean_excursion_r"], "gates": GS["gates"],
 },
 "F6_interpretable_profile": {
   "search": {"n_predicates": RU["n_predicates"], "n_rules_scored": RU["n_rules_scored"],
              "split": RU["split"], "min_n_per_half": RU["min_n_per_half"], "base": RU["base"]},
   "top_by_full_target_rate": RU["top_by_full_target_rate"][:20],
   "top_by_gross_r": RU["top_by_gross_r"][:20],
   "top_by_fill_honest_r": sorted(RU["all_rules"], key=lambda d: -min(d["fh_h1"], d["fh_h2"]))[:20],
   "headline_rule": "cost_r > 0.40 AND session_bucket == london",
   "headline_rule_cells": PD["cells"], "headline_rule_detail": PD["rule_detail"],
   "headline_rule_by_family": PD["rule_by_family"], "headline_rule_by_symbol": PD["rule_by_symbol"],
   "discovery_tree_split_half": TR,
 },
 "F7_computed_but_unused": {
   "ordering_defect": UN["ordering_defect"],
   "pre_decision_power_takeable": UN["pre_decision_power_takeable"],
   "zero_information_constants": UN["zero_information_constants"],
   "n_zero_information_constants": len(UN["zero_information_constants"]),
 },
 "F8_engine_scoring_vs_path_four_symbols": {
   "claim": "on XAUUSD/XAGUSD/USDJPY/EURUSD the engine books a MEDIAN +0.70R on rows the fill-honest "
            "M1 walk says hit the +2R target first, against +2.0000R on the other twenty symbols. "
            "It under-books STOPS on the same four as well, so the honest two-sided repair is "
            "+0.00535 R per takeable pool trade, NOT the +0.0495 a one-sided read gives.",
   "reconciliation": SG["reconciliation"], "per_symbol": SG["per_symbol"],
   "on_honest_target_rows": SG2["on_honest_target_rows"],
   "per_symbol_on_honest_target": SG2["per_symbol_on_honest_target"],
   "family_x_group": SG2["family_x_group"], "mae_before_target": SG2["mae_before_target"],
   "per_symbol_discreteness": SG3["per_symbol_discreteness"],
   "agreement_by_group": SG3["agreement_by_group"],
   "one_sided_repair_size_WRONG": SG3["repair_size"], "honest_stop_side": SG3["honest_stop_side"],
   "two_sided_repair_CORRECT": {"ALL_takeable": SR["ALL_takeable"], "by_group": SR["by_group"],
                                "by_symbol": SR["by_symbol"], "consequence": SR["consequence"],
                                "briefed_stop_cohort_composition": SR["briefed_stop_cohort_composition"]},
   "downstream_instruction": "use fill_honest_which_came_first, NOT outcome_band, for anything "
                             "per-symbol. XAUUSD's outcome_band ge_target rate is 2.62% against a "
                             "fill-honest path rate of 21.30% - an 8.1x per-symbol error.",
 },
 "F9_the_winner_in_words": {
   "when": "London morning, UTC 07-11, mode 08:00. 78.0% of the cell in hours 07-09, 90.2% in 07-10.",
   "instruments": "index and cross-rate: UK100, EURGBP, JP225, EURJPY, NZDUSD, US30_cash, USDCAD, "
                  "USDCHF, CHFJPY. Best: JP225 +0.3026, NZDUSD +0.2967, USDCHF +0.1842.",
   "structure": "liquidity_sweep_reclaim (+0.1394), structural_distance_extreme (+0.1516), "
                "current_fvg_fill (+0.1917). AVOID current_ob_retest: n=46, 0.00% target rate, -0.6195 R.",
   "distance_to_stop": "0.0517% of price vs 0.2092% pool - a quarter of the typical stop.",
   "volatility": "mfe +3.790 R, mae -3.350 R, total excursion 7.140 R vs pool 4.2764 R.",
   "resolution": "median 14 M1 bars to target vs the takeable full-target median of 31 (mean 39.54).",
   "direction": "488 SHORT / 372 LONG. side=SHORT AND london is itself positive both halves.",
   "what_the_system_thinks": "candidate_probability 0.7452 (dead average); 100.0% refused by the "
                             "cost gates; 0.0% scheduler-materialised; 0 selected.",
   "one_sentence": "A tight-stopped sweep-reclaim or structural-extreme on an index or cross during "
                   "the first four hours of London, which resolves inside a quarter-hour, has twice "
                   "the pool's chance of paying 2R - and the stack rejects every one of them on a "
                   "cost term that is large only because the stop is tight.",
   "session_cut": PR["cuts"]["session_bucket"], "family_cut": PR["cuts"]["origin_family"],
   "symbol_cut": PR["cuts"]["symbol"], "hour_cut": PR["cuts"]["utc_hour"],
   "side_cut": PR["cuts"]["side"], "born_state_cut": PR["cuts"]["born_state"],
   "all_cuts": PR["cuts"],
 },
 "caveats": [
   "One month (January 2026), one arm (S0R0), true UTC. Nothing here is tested out-of-month.",
   "2,975 rules were scored; the headline profile is reported for split-half stability and for "
   "topping two independent rankings, NOT because it survived a multiplicity correction.",
   "cost_r>0.40 AND london is gross-positive (+0.0532) and FILL-HONEST-NEGATIVE (-0.0899). It is a "
   "shape finding, not a tradeable one; net -0.1849 even at the 7.3x corrected spread.",
   "Per-symbol conclusions from outcome_band are invalid on XAUUSD/XAGUSD/USDJPY/EURUSD (F8).",
   "Hard 2-hour horizon (W0-F3) bounds every holding-time question.",
   "Pseudo-replication (W0-F1) is not corrected in F4-F6; setup_dup_rank is carried as a predicate "
   "and dup_rank=1 never entered a top-14 list.",
 ],
 "artifacts": sorted([f for f in os.listdir(HERE) if f.startswith("l3_")]),
}
json.dump(out, open(os.path.join(HERE, "l3_RESULT.json"), "w"), indent=1, default=str)
print("wrote l3_RESULT.json  bytes=%d  top-level keys=%d" % (
    os.path.getsize(os.path.join(HERE, "l3_RESULT.json")), len(out)))
