#!/usr/bin/env python3
"""a1 step 90 - assemble a1_RESULT.json from the measurement files."""
from __future__ import annotations
import json
import os

D = os.path.dirname(os.path.abspath(__file__))


def L(n):
    return json.load(open(os.path.join(D, n)))


def main():
    V = L("A1_VALIDATE_V1.json")
    B = L("A1_BOOK_V1.json")
    C = L("A1_COSTGATE_V1.json")
    G = L("A1_DIAG_V1.json")
    F = L("A1_FADE_BAND_V1.json")
    X = L("A1_CRUX_V1.json")
    M = L("A1_MECH_V1.json")

    KS = ("n", "days", "gross_R", "cost_R", "net_R", "gross_bps", "cost_bps", "net_bps",
          "edge_toll", "win_rate_net", "win_rate_gross", "t_trade", "t_day",
          "boot_lo", "boot_hi", "p_net_le0", "total_R", "days_positive", "days_total",
          "R_per_day_mean", "max_drawdown_R", "share_stop", "share_target", "share_bell")

    out = {
        "lane": "a1",
        "headline": ("a1-SCORER-V1 is net-negative in every window - January -0.20588, "
                     "February+March -0.16959, April+May -0.19124 R/trade - and the wave's "
                     "strongest published separator (x4's confirm minute) is worth +0.457 R of "
                     "gross at a fill it cannot have and -0.06..+0.03 R at every fill it can; "
                     "the one anatomy result that travels is the 5-minute entry delay at "
                     "+0.0736/+0.0754/+0.0735/+0.0581/+0.0988 gross in five consecutive months."),
        "spec": B["spec"],
        "substrate": {
            "population": "at-market (live-expressible) cohort, h5_SUBSTRATE_5M",
            "months": {"2026-01": 14905, "2026-02": 13966, "2026-03": 14884,
                       "2026-04": 13837, "2026-05": 11888, "total": 69480},
            "window": "M1 stamps D-15..D+125, true-UTC lane hold bridge_ftmo_m1_2026{01..05}",
            "validation": {
                "at_market_anchor_exact_all_months": True,
                "reproduce_h5_prewalk_max_abs_diff": 4.999968716834502e-09,
                "reproduce_h5_prewalk_share_within_1e6": 1.0,
                "reproduce_b1_cost_bases": V["V3_vs_b1_3month"],
                "confirm_minute_coverage": V["V6_confirm_minute_coverage"],
                "convention_delta_pool": V["V5_convention_delta"],
            },
        },
        "Q1_priced_jointly": {w: {k: B["windows"][w][k] for k in KS if k in B["windows"][w]}
                              for w in ("IS_jan_BOOK", "OOS_febmar_BOOK",
                                        "OOS2_aprmay_BOOK", "ALL5_BOOK")},
        "Q2_per_month_unchanged": {mm: {k: B["per_month"][mm]["BOOK"][k] for k in KS
                                        if k in B["per_month"][mm]["BOOK"]}
                                   for mm in ("202601", "202602", "202603", "202604", "202605")},
        "Q2_gate_shares": {mm: B["per_month"][mm]["gate_shares"] for mm in B["per_month"]},
        "Q3_trap": {
            "decomposition": B["Q3_trap_decomposition"],
            "rank_persistence": {k: {kk: v[kk] for kk in
                                     ("n_instruments", "spearman_cost", "spearman_gross")}
                                 for k, v in B["rank_persistence_IS_vs_OOS"].items()},
            "gates_are_cost_filters": M["M1_separator_is_a_cost_proxy"],
            "cost_stratified_confirm": G["C4_cost_stratified_confirm"],
            "placebo_confirm": G["C3_placebo_confirm"],
        },
        "F2_stale_fill_correction": {
            "gate_gross_gap_by_fill": {mm: {k: {"gap": v["gate_gross_gap"],
                                                "executable": v["executable"]}
                                            for k, v in rec.items()}
                                       for mm, rec in M["M3_gate_marginal_by_fill"].items()},
            "crux_pooled": {w: {a: {k: c[k] for k in ("n", "gross_R", "net_R", "t_day")}
                                for a, c in X["crux_pooled"][w].items()}
                            for w in X["crux_pooled"]},
            "substitution_surface": G["C7_substitution_surface"],
        },
        "F3_delay_lever": {
            "per_month_k5": {mm: C["delay_ladder"][mm]["k5_STOPONLY"] for mm in C["delay_ladder"]},
            "persistence": C["lever_persistence"],
            "equal_hold_control": G["C1_equal_hold"],
            "exact_mirror": G["C2_exact_mirror_of_delay_lever"],
            "cross_section": {k: v for k, v in G["C6_cuts_and_lever_persistence"].items()
                              if k.startswith(("spearman", "n_", "sign_"))},
            "symmetric_stress": F["delay_lever_stress"],
            "info_level_by_k": M["M4_fade_and_info_level"],
        },
        "Q4_ablation": {
            "add_one_in_jan": {k: {"n": B["per_month"]["202601"][k]["n"],
                                   "net_R": B["per_month"]["202601"][k]["net_R"]}
                               for k in ("REF_shipped_k0_INC", "AOI_G", "AOI_C", "AOI_S",
                                         "AOI_K", "AOI_X", "AOI_KX", "AOI_GC", "BOOK")},
            "leave_one_out_jan": {k: {"n": B["per_month"]["202601"][k]["n"],
                                      "gross_R": B["per_month"]["202601"][k]["gross_R"],
                                      "cost_R": B["per_month"]["202601"][k]["cost_R"],
                                      "net_R": B["per_month"]["202601"][k]["net_R"]}
                                  for k in ("BOOK", "LOO_noG", "LOO_noC", "LOO_noS",
                                            "LOO_k0", "LOO_k1", "LOO_k3", "LOO_k10",
                                            "LOO_k30", "LOO_exit_INC", "LOO_exit_T3S1")},
            "add_one_sum_vs_joint": {"sum_of_deltas": 0.29279, "joint_gain": 0.14660,
                                     "over_count_pct": 99.7},
        },
        "Q5_answer": {
            "net_positive_out_of_sample": False,
            "OOS_febmar_net_R": B["windows"]["OOS_febmar_BOOK"]["net_R"],
            "OOS_febmar_n": B["windows"]["OOS_febmar_BOOK"]["n"],
            "OOS_febmar_t_trade": B["windows"]["OOS_febmar_BOOK"]["t_trade"],
            "OOS_febmar_t_day": B["windows"]["OOS_febmar_BOOK"]["t_day"],
            "OOS_febmar_p_net_le0": B["windows"]["OOS_febmar_BOOK"]["p_net_le0"],
            "OOS_febmar_days_positive": B["windows"]["OOS_febmar_BOOK"]["days_positive"],
            "IS_jan_net_R": B["windows"]["IS_jan_BOOK"]["net_R"],
            "shortfall_R_per_trade_OOS": B["windows"]["OOS_febmar_BOOK"]["cost_R"]
            - B["windows"]["OOS_febmar_BOOK"]["gross_R"],
        },
        "F1_entry_convention_on_b1": X["X2_entry_convention_on_b1_book"],
        "b1_reproduction": C["b1_reproduction"],
        "F4_fade": {mm: {"orig_k0": v["orig_k0"], "mirror_k0": v["mirror_k0"]}
                    for mm, v in G["C2_exact_mirror_of_delay_lever"].items()},
        "cost_band_sensitivity_k3_STOPONLY": {
            t: {w: (F["cost_band_sweep"]["%s|ORIG|k3_STOPONLY" % t][w] or {}).get("net_R")
                for w in ("IS_jan", "OOS_febmar", "OOS2_aprmay", "all5")}
            for t in ("0.40", "0.45", "0.50", "0.55", "0.60", "0.65", "0.70", "0.80", "1.00")},
        "band_instrument_composition": F["band_instrument_composition"],
        "files": sorted(f for f in os.listdir(D) if f.startswith(("a1_", "A1_"))),
        "caveats": [
            "horizon hard-capped at decision+120min by the M1 window",
            "at-market cohort only (63% of the true-UTC pool by row count)",
            "modelled broker-true cost, no exit slippage charged",
            "no multiplicity correction anywhere; the cost-band sweep is 14x2x3 cells",
            "median delay-lever delta is 0.0 (47% of rows unchanged); the mean is tail-weighted",
        ],
    }
    with open(os.path.join(D, "a1_RESULT.json"), "w") as f:
        json.dump(out, f, indent=1)
    print("wrote a1_RESULT.json  (%d bytes)" % os.path.getsize(os.path.join(D, "a1_RESULT.json")))


if __name__ == "__main__":
    main()
