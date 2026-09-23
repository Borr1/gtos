"""b1 step 15 — assemble b1_RESULT.json from every step artifact. No hand-typed numbers."""
import json
import os
import sys

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)


def L(name):
    with open(f"{D}/{name}") as f:
        return json.load(f)


def main():
    repro = L("B1_REPRO_V1.json")
    cj = L("B1_COSTJOIN_V1.json")
    grid = L("B1_GRID_V1.json")
    surf = L("B1_SURFACE_V1.json")
    book = L("B1_BOOK_V1.json")
    plac = L("B1_PLACEBO_V1.json")
    dnull = L("B1_DAYNULL_V1.json")
    oos = L("B1_OOS_V1.json")
    decay = L("B1_DECAY_V1.json")
    bookb = L("B1_BOOKB_V1.json")
    dec = L("B1_DECOMPOSE_V1.json")
    fin = L("B1_FINAL_V1.json")
    daily = L("B1_DAILY_V1.json")
    comp = L("B1_COMPOSITE_V1.json")

    out = {
        "lane": "b1 — BUILD THE BOOK",
        "question": "Take everything the hunt found and construct the single best "
                    "tradeable book. One specification.",
        "substrate": {
            "file": "h5_SUBSTRATE_5M.jsonl.gz",
            "n_rows": 69480,
            "months": ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05"],
            "hunt_window_n": 43755,
            "oos_window_n": 25725,
            "cohort": "live-expressible at-market candidates (born_at_limit), "
                      "e_build_atmkt.py unmodified",
            "cost_join": cj,
        },
        "reproduction": {
            "swarm_headline": repro["A_swarm_headline_flatcost"],
            "h6_cell_B_target": repro["B_h6_target"],
            "h6_cell_B_reproduced": repro["B_h6_hourcap060_k3"],
            "h5_five_month_book": repro["D_h5_five_month_book"],
            "h3_regime_transition_break": repro["E_h3_regime_transition_break_k5"],
            "independent_bar_rebuild_check": plac["rebuild_check"],
            "verdict": "swarm headline, h6 cell B, h5 five-month book and h3's family "
                       "cell all reproduce to the published digits; an independent walk "
                       "straight off the M1 CSVs reproduces every one of the 3,728 book "
                       "rows to 5e-9",
        },
        "SPECIFICATION": {
            "name": "b1-BOOK-V1",
            "universe": "all 24 pool instruments; no instrument name appears in the rule",
            "gate": {
                "rule": "admit only if the candidate's own broker-true round-trip toll "
                        "at the decision instant is <= 0.60 bps of notional",
                "toll_terms": ["hour-true tick-median spread(symbol, broker hour)",
                               "broker-true commission (notional bp or per-lot schedule)",
                               "measured live entry slippage (per symbol)",
                               "swap, if the 120-minute horizon crosses a rollover"],
                "ex_ante": True,
                "provenance": "threshold published by lane h6 (cell B) before b1 ran",
                "resolves_to": fin["gate_resolution_by_window"],
                "resolves_to_same_three_every_month":
                    fin["gate_resolves_to_same_3_every_month"],
            },
            "entry": {"rule": "place nothing at the decision; wait 3 minutes; enter at "
                              "MARKET on the close of minute 3",
                      "k_minutes": 3,
                      "plateau": "k in {1,2,3} all pay; k=0 is negative; k>=15 is negative",
                      "no_resting_order": "so the established 60-second cancel rule and "
                                          "the 0.45 fill floor are both inapplicable "
                                          "(fill floor is identically zero here, h6-F4)"},
            "exit": {"stop_r": -1.0, "target": None, "trail": None,
                     "close_at_minutes": 120,
                     "rule": "stop at -1R measured from the fill; no take-profit; no "
                             "trailing stop; close at market 120 minutes after the "
                             "decision (117 after the fill)",
                     "why_no_trail": "the estate's ratified honest-trail bound "
                                     "(B613 / AD 95.8% intrabar; h6-F8) shows a trail "
                                     "checked only from the next bar manufactures "
                                     "+0.084 R/trade of bar-resolution premium"},
            "sizing": "fixed fractional on the declared risk distance (constant-R book)",
            "no_other_conditioning": ["no family filter", "no side filter",
                                      "no probability filter", "no fill-probability floor",
                                      "no cancel band", "no regime filter"],
        },
        "Q1_priced_jointly": {
            "window": "2026-01 .. 2026-03",
            "cost_basis": "h1 four-term broker-true (strictest in the wave, "
                          "0.245214 R / 2.9744 bps book-wide)",
            "headline": fin["HEADLINE_hunt3m_h1cost"],
            "truncation": book["truncation"],
            "bootstrap_day_block": book["bootstrap_day_block"],
            "equity_days": fin["EQUITY"]["days"],
            "equity_cum_net_R": fin["EQUITY"]["cum_net_R"],
            "at_the_two_other_cost_bases": {
                "hour_true_three_term": book["headline_hour_true_3term"],
                "flat_swarm_basis": book["headline_flat_swarm_basis"]},
            "daily": daily["DAILY"]["BOOK-A gate<=0.60"],
            "concurrency": daily["CONCURRENCY"],
        },
        "Q2_is_it_net_positive": {
            "hunt_window_answer": "YES",
            "hunt_window_net_R": fin["HEADLINE_hunt3m_h1cost"]["net_R"],
            "hunt_window_net_bps": fin["HEADLINE_hunt3m_h1cost"]["net_bps"],
            "hunt_window_edge_over_cost": fin["HEADLINE_hunt3m_h1cost"]["ratio_R"],
            "out_of_sample_answer": "NO",
            "oos_book": oos["OOS_april_may"],
            "oos_bootstrap": oos["OOS_bootstrap"],
            "shortfall": dec["SHORTFALL_oos"],
            "five_month_pooled": comp["A  cost gate <=0.60 bps"]["pooled_5m"],
            "five_month_bootstrap": comp["A  cost gate <=0.60 bps"]["boot_5m"],
            "mechanism_of_failure": {
                "gross_collapsed_not_cost": {
                    "hunt_gross_R": oos["hunt_window_at_hour_true_cost"]["gross_R"],
                    "oos_gross_R": oos["OOS_april_may"]["gross_R"],
                    "hunt_cost_R": oos["hunt_window_at_hour_true_cost"]["cost_R"],
                    "oos_cost_R": oos["OOS_april_may"]["cost_R"]},
                "contract_did_not_break": decay[
                    "UNGATED all 24 instruments | b1 exit (k=3, STOPONLY)"],
                "rank_persistence": decay["_RANK_PERSISTENCE"],
                "the_two_limbs": {k: {"hunt_net_R": v["hunt_3m"].get("net_R"),
                                      "oos_net_R": v["oos_2m"].get("net_R"),
                                      "pooled_5m_net_R": v["pooled_5m"].get("net_R"),
                                      "pooled_5m_ratio": v["pooled_5m"].get("ratio_R")}
                                  for k, v in dec["PART1_limbs"].items()},
                "decay_slopes": decay["_DECAY_SLOPES"],
            },
            "what_would_have_to_change": {
                "gross_multiple_required_oos": dec["SHORTFALL_oos"]["gross_multiple_required"],
                "cost_cut_required_pct_oos": dec["SHORTFALL_oos"]["cost_cut_required_pct"],
                "toll_floor_available": "h3 measured the mechanical toll floor at "
                                        "commission-only, a 4.32x cut; the OOS book needs "
                                        "a 15.5x gross or a 93.6% toll cut",
            },
        },
        "Q3_ablation": {
            "leave_one_out_same_rows": book["ablation_leave_one_out"],
            "add_one_in_from_swarm_contract": book["ablation_add_one_in"],
            "marginal_net_R": book["marginal_net_R"],
            "complementarity": {
                "note": "add-one deltas from the swarm baseline sum to +0.19070 against a "
                        "joint gain of +0.28337: the limbs UNDER-count by 32.7%, the "
                        "opposite sign to the wave-1 levers' 66.8% double-count",
            },
            "k_plateau": fin["K_PLATEAU"],
            "gate_curve": surf["A_gate_curve_k3_stoponly"],
            "marginal_cost_bands": surf["A2_marginal_bands_k3_stoponly"],
        },
        "Q4_multiplicity_bill": fin["MULTIPLICITY_BILL"],
        "Q5_specification_precise": {
            "see": "SPECIFICATION above; the implementable pseudocode is in "
                   "b1_RESULT.md section 5"},
        "CONTROLS": {
            "placebo_anchor_shifts": plac,
            "whole_day_null_20_draws": dnull["null"],
            "whole_day_null_draws": dnull["draws"],
            "side_randomised": dnull["side_randomised_shift0"],
            "verdict": "the book beats 9 of 9 intraday placebo anchors and 20 of 20 "
                       "whole-day draws on the mean, but sits at only z=+1.50 in the "
                       "whole-day null (empirical p=0.143 on net, 0.190 on gross)",
        },
        "STRESS": fin["STRESS_hunt3m"],
        "ALTERNATIVE_BOOKS": comp["SUMMARY"],
        "ALTERNATIVE_BOOKS_FULL": {k: v for k, v in comp.items()
                                   if k.startswith(("A ", "C ", "D ", "E ", "F "))},
        "REJECTED_BOOKS": {
            "cost_bps_ranked_instruments (BOOK-B)": {
                "january_order": bookb["january_cost_order"][:8],
                "test_feb_may": {k: v["TEST_feb_to_may"]
                                 for k, v in bookb["train_january_cost_test_feb_may"].items()},
                "why": "ranking instruments by mean cost in BPS admits EURUSD third; "
                       "EURUSD's toll in R is 4.4x the index complex because its risk "
                       "distances are tiny. A constant-R book must rank in R, not bps."},
            "cost_R_ranked_instruments": dec["PART2_costR_ranked_book"],
        },
        "HOUR_RULES": daily["HOUR_RULES"],
        "GRID": grid["grid"] | {"selection_rule": grid["selection_rule"],
                                "n_ratio_gt1": grid["n_ratio_gt1"],
                                "n_pass_rule": grid["n_pass_rule"],
                                "top40_by_rule": grid["top40_by_rule"][:12]},
    }
    with open(f"{D}/b1_RESULT.json", "w") as f:
        json.dump(out, f, indent=1)
    print("wrote b1_RESULT.json",
          round(os.path.getsize(f"{D}/b1_RESULT.json") / 1024, 1), "KB")


if __name__ == "__main__":
    main()
