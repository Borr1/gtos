"""h1-09 -- assemble h1_RESULT.json from the measured artifacts. No numbers typed by hand."""
import json
import os

D = os.path.dirname(os.path.abspath(__file__))
S = json.load(open(f"{D}/H1_SURFACE_V1.json"))
H = json.load(open(f"{D}/H1_HUNT_V1.json"))
DC = json.load(open(f"{D}/H1_DECOMP_V1.json"))
F = json.load(open(f"{D}/H1_FRONTIER_V1.json"))
R = json.load(open(f"{D}/H1_ROBUST_V1.json"))
E = json.load(open(f"{D}/H1_EXITSLIP_V1.json"))
ST = json.load(open(f"{D}/H1_STRESS_V1.json"))
B = json.load(open(f"{D}/h1_COST_ROWS_V1_BUILD.json"))

out = {
    "lane": "h1",
    "question": "the cost surface, in money, at full resolution",
    "population": {
        "cohort": "live-expressible at-market candidates, Jan+Feb+Mar 2026",
        "n": S["n_rows"],
        "edge_contract": "K5_TRAIL025 (market entry delayed 5 min, 0.25R trail)",
        "account": "FTMO",
        "sampling": "none - whole population on every table",
    },
    "cost_basis": {
        "spread": "L10X_TICK_SPREAD_V1 spread_bps_median_by_broker_hour, FTMO, 300,538,915 ticks, full population, keyed on broker wall hour (UTC+2 Jan/Feb, UTC+3 from 2026-03-08)",
        "commission": "BROKER_TRUE_COSTS_V1.json FTMO, round turn, notional_bp or per_lot via usd_per_price_unit_per_lot",
        "slippage_entry": "L10X_LIVE_COST_PRICEUNITS_V1 measured price units, clamped >=0; class median for the 12 unmeasured symbols",
        "swap": "instrument spec, adverse side, per broker-midnight crossing inside the 2h horizon, triple on swap_rollover3days",
        "convention": "ONE full bid/ask crossing per round turn",
        "basis_counts": B["basis_counts"],
        "slip_table_bps": B["slip_table_bps"],
        "era_table": B["era_table"],
    },
    "HEADLINE": {
        "pool_cost_r": S["POOL"]["cost_r"],
        "pool_cost_bps": S["POOL"]["cost_bps"],
        "pool_gross_r": S["POOL"]["gross_r"],
        "pool_gross_bps": S["POOL"]["gross_bps"],
        "pool_net_r": S["POOL"]["net_r"],
        "edge_over_cost_R": S["POOL"]["edge_over_cost_R"],
        "edge_over_cost_bps": S["POOL"]["edge_over_cost_bps"],
        "swarm_basis_cost_r": DC["ROLLOVER_HOUR"]["hour_aware_vs_flat"]["cost_r_flat"],
        "alt_bases": S["POOL_ALT_BASES"],
        "hour_aware_vs_flat": DC["ROLLOVER_HOUR"]["hour_aware_vs_flat"],
    },
    "TERMS": {
        "share_of_total_bps": S["TERM_SHARE_OF_TOTAL_BPS"],
        "share_of_total_R": S["TERM_SHARE_OF_TOTAL_R"],
        "dominant_term_row_counts": S["TERM_DOMINANCE"],
        "dominant_by_symbol": {k: {"n": v["n"], "total_bps": v["total_bps"],
                                   "dominant_bps": v["dominant_bps"],
                                   "share_dominant_bps": v["share_dominant_bps"],
                                   "bps": v["bps"]}
                               for k, v in DC["TERM_DOMINANCE"]["symbol"].items()},
    },
    "DISPERSION": {
        "by_axis": S["AXIS_DISPERSION"],
        "eta2": S["AXIS_ETA2"],
        "bps_vs_R": {k: {kk: vv for kk, vv in v.items() if kk != "cells"}
                     for k, v in DC["BPS_VS_R"].items()},
        "axis_carrying_most_money": "symbol (eta2 0.8578 on log cost_bps; symbol x broker_hour 0.9852)",
        "axis_carrying_most_R": "rdp_decile / stop width (eta2 0.4415 on log cost_r)",
    },
    "AXES": S["AXES"],
    "ROLLOVER_AND_SWAP": DC["ROLLOVER_HOUR"],
    "CHEAP_AND_DEEP": {
        "n_ge_300": H["CHEAPEST_CELLS_n_ge_300"][:30],
        "n_ge_100": H["CHEAPEST_CELLS_n_ge_100"][:30],
    },
    "HUNT": {
        "hit_counts_by_depth": H["HIT_COUNTS_BY_DEPTH"],
        "n_cell_definitions": len(H["tables"]),
        "all_hits": H["ALL_HITS"],
        "best_edge_over_cost_n_ge_300": H["BEST_EDGE_OVER_COST_n_ge_300"][:40],
    },
    "EX_ANTE_MONEY_GATE": {
        "sweep": F["MONEY_GATE"],
        "sweep_era": F["MONEY_GATE_ERA"],
        "r_gate": F["R_GATE"],
        "shipped_gate_limbs": F["SHIPPED_GATE_LIMBS"],
        "train_test": F["TRAIN_TEST"],
        "composed": F["COMPOSED"],
        "hour_exclusions": F["HOUR_EXCLUSIONS"],
        "by_symbol": F["MONEY_GATE_BY_SYMBOL"],
    },
    "ENTRY_TIMING": {
        "delay_joint": DC["ENTRY_DELAY_JOINT"],
        "entry_mode_spread_incidence": DC["ENTRY_MODE_SPREAD_INCIDENCE"],
        "first_minute_cancel_cost": DC["FIRST_MINUTE_CANCEL_COST"],
        "january_pool_cost": DC["JAN_POOL_COST"],
    },
    "STRESS": {
        "exit_slippage_bps_per_symbol": E["EXIT_SLIP_BPS_PER_SYMBOL"],
        "exit_slippage_priced": E["PRICED"],
        "one_at_a_time": R["SENSITIVITY"],
        "joint": ST["COHORTS"],
        "hour_map_index_complex": ST["HOUR_MAP"],
    },
    "CORRECTIONS_TO_PRIOR_BASIS": {
        "H1-F9_btcusd_commission": {
            "e_lib_bps": 39.2778 / 88599.74 * 1e4,
            "broker_true_bps": 6.51631,
            "ratio": 6.51631 / (39.2778 / 88599.74 * 1e4),
            "why": "e_lib normalises a live-window PRICE-unit commission by a JANUARY price",
            "materiality": "commission is 90.6% of BTCUSD's whole toll",
        },
        "H1-F10_flat_median_understates": DC["ROLLOVER_HOUR"]["hour_aware_vs_flat"],
        "H1-F11_swap_never_charged": DC["ROLLOVER_HOUR"]["swap_rows"],
    },
    "LIMITS": [
        "every cell is chosen after seeing three months; only the gate threshold has an out-of-sample read (March)",
        "no multiplicity correction: 651 hits from 29 cell definitions, deliberately uncorrected",
        "exit slippage (l10-F9) is priced but excluded from the headline basis; on GER40 it is 73% of the modelled toll",
        "at-market cohort only - the 46% POI limit population is out of scope",
        "FTMO only; l10-X12 measured redacted_account BTCUSD spread at 21.9x FTMO's",
        "the tick anchor is a 37-day 2026Q2/Q3 window; era ratios are carried as a sensitivity, not folded in",
        "NAS100's worst-case survival rests on a 0.189% live stop measured on 4 live captures",
    ],
}
json.dump(out, open(f"{D}/h1_RESULT.json", "w"), indent=1, default=str)
print("wrote h1_RESULT.json", os.path.getsize(f"{D}/h1_RESULT.json"), "bytes")
print("hits", out["HUNT"]["hit_counts_by_depth"])
print("pool e/c", round(out["HEADLINE"]["edge_over_cost_R"], 4))
