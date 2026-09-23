#!/usr/bin/env python3
"""x4 — assemble the machine-readable receipt from the measurement files."""
import json, os
D = os.path.dirname(os.path.abspath(__file__))
L = lambda f: json.load(open(os.path.join(D, f)))
rank, econ, ctrl = L("X4_RANK_V1.json"), L("X4_ECON_V1.json"), L("X4_CONTROL_V1.json")
rules, rean, pol = L("X4_RULES_V1.json"), L("X4_REANCHOR_V1.json"), L("X4_POLICY_V1.json")
ver, fin, ticks = L("X4_VERIFY_V1.json"), L("X4_FINAL_V1.json"), L("X4_TICKS_V1.json")
R = {
 "lane": "x4", "schema": "gtos-wave19-discovery-x4-v1",
 "window": "2026-01 true-UTC S0R0 (CJ re-clock)", "pool_rows": 27658,
 "joined_with_intrabar": rank["n_joined"], "features_built": rank["n_features"],
 "evidence_class": "DISCOVERY - January only, no out-of-window test, no multiplicity correction",
 "coverage": econ["coverage"],
 "dropped_rows": {"n": 428, "gross_mean": -0.38899, "kept_gross_mean": -0.21480,
   "concentration": "294 at UTC h22, 94 at h23", "population_optimism_r": 0.0012},
 "F1_ceiling_cross_fitted": pol["CEILING"],
 "F2_best_pre_field": {
   "feature": "stop_dist_over_bar_range",
   "definition": "risk_distance / (high-low of the 15 M1 bars composing the decision M15 bar)",
   "d_briefed_cohorts": -0.1829, "d_honest_cohorts": -0.1723,
   "d_within_confirm_clean": -0.1983, "twin_target_dist_d": -0.2004,
   "prior_estate_ceiling": 0.152, "prior_holder": "risk_distance_pct_of_price (l3, d=-0.1517)",
   "deciles": econ["deciles"]["stop_dist_over_bar_range"]["takeable"],
   "circularity_check": ver["V3_geometry_circularity"]},
 "F3_separator_in_bar1_cohort": rean["BAR1_SPLIT"],
 "F4_identity_with_existing_field": ver["V1_identity_with_anchor"],
 "F5_whole_pool_one_variable": {k: fin[k] for k in
   ("BASE_none","C_c0_le_-0.15","C_c0_le_-0.05","G_geo_le_0.60","G_geo_le_0.80","CG_union")},
 "F6_substitution": {"geometry_given_confirm": fin["G_given_C_clean"],
   "confirm_given_geometry": fin["C_given_G_clean"],
   "joint_surface": fin["JOINT_SURFACE"]},
 "F7_reanchor": {"sweep": rean["reanchor"], "baselines": rean["baselines"],
   "l7_reproduction": {"l7_published_delta_at_5min": 0.0670,
     "x4_measured_delta_at_5min": round(-0.16879 - (-0.23551), 5),
     "construction": "independent - fill-honest first-touch walk on M1 R paths"},
   "conditional_policy": pol["POLICY"],
   "delay0_trap": "k=0 arm is the FILL-BLIND convention (+0.04241), W0-F2 fiction; not a baseline"},
 "F8_substrate_defect_missing_minute": {**rules["MISSING_MINUTE"], **ver["V5_missing_minute"]},
 "F9_what_does_not_separate": {r["feature"]: r["d_honest"] for r in rank["table"]
   if r["cls"] == "PRE" and abs(r["d_honest"] or 0) < 0.09},
 "F9_within_symbol_control": ctrl["C1_within_symbol"][:12],
 "F9_stratified_control": ctrl["C3_stratified_on_geometry"],
 "F10_tick_mechanism_out_of_window": ticks,
 "F11_cost": pol["COST"],
 "F12_metric_warning": {
   "geo_pool_gain": 0.07023, "geo_kept_gain": 0.02053, "geo_refused_mean": -0.30378,
   "c0_pool_gain": 0.19810, "c0_kept_gain": 0.18223, "c0_refused_mean": -0.66506,
   "statement": "pool-R-per-opportunity rises on ANY refusal of a negative-mean subset; report the refused-set mean"},
 "robustness": {"headline_split_by_axis": {k: {"cells": len(v),
     "cells_with_correct_sign": sum(1 for x in v.values() if x["gap"] > 0)}
   for k, v in pol["HEADLINE_SPLIT"].items()},
   "order_type_control": ver["V2_atmkt_split"],
   "pre_only_rule": ver["V6_pre_only_rule"]},
 "multiplicity": ver["V7_multiplicity"],
 "not_established": [
   "no out-of-window month tested (Feb used-once VAL, Mar pre-registered, Apr/May owned by CS)",
   "2-hour path cap bounds every claim; part of the geometry gradient is resolution speed",
   "11.37% of the pool is booked against a fill the substrate cannot see (F8)",
   "no policy reaches positive NET R; mean cost_r 0.65486 is untouched"],
}
with open(os.path.join(D, "x4_RESULT.json"), "w") as f:
    json.dump(R, f, indent=1)
print("wrote x4_RESULT.json", os.path.getsize(os.path.join(D, "x4_RESULT.json")), "bytes")
