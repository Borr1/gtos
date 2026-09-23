"""Session AN — repair-queue rows, appended (never overwritten). [B1290-B1295]

    python3 docs/audits/fable5-vision-audit-20260725/phase10/receipts/an_repair_rows.py

Six rows. Two are CLOSED by this session (the coverage hole and the unwired switch, both filed
by AL); four are open with their prescription and their price attached.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

QUEUE = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts/REPAIR_QUEUE_APPEND.jsonl"
TS = "2026-07-30T18:00:00+00:00"

ROWS = [
    {
        "sleeve": "__estate__",
        "component": "src/costs/spread_model.py Coverage propagation",
        "gate": "cost_coverage",
        "verdict": "CLOSED",
        "prescription": "UNDECIDABLE_ERA_DID_NOT_DEGRADE_COVERAGE",
        "prescription_in_diagnostics_enum": False,
        "action": (
            "CLOSED by B1250. `Coverage` degraded on `era_class` alone, so an UNDECIDABLE "
            "**RECORDED** era matched no branch and kept the anchor's own class: BTCUSD 2020Q1 "
            "returned coverage=MEASURED on a band whose own capture_requirement reads 'band "
            "spans 204058.1x'. Not one quarter -- 182 of the model's 275 undecidable eras are "
            "RECORDED (66.2 %; FTMO 134/195, redacted_account 48/80). `not decidable` now degrades on "
            "EVERY path. Counted exactly: the branch fires on 275 eras and 192 change coverage "
            "CLASS (166 RECORDED MEASURED->MODELLED, 26 QUANTIZED TRANSFERRED->MODELLED); the "
            "other 83 already sat at MODELLED. Monotone by construction. Five behavioural tests, "
            "all verified RED against the pre-repair logic by copy-back. "
            "**And the honest limit: it moves ZERO verdicts today** -- coverage_frac counts "
            "refusals not classes; the field that looks as if it would read the class, "
            "`require_measured_cost_frac`, is declared at spec.py:354 and read by NO code in "
            "src/ at all (stronger than this row first said, which was 'it is 0.0 in all three "
            "options'); and the sleeve-level stamps were already saturated. Its value is that "
            "the per-trade "
            "record stops lying (1,584 trade-level classes corrected across the census, 78 of "
            "mx_btcusd's 232 RECORDED trades among them) and that `require_decidable` now has a "
            "coherent meaning."),
        "evidence": {
            "undecidable_eras_total": 275, "of_which_RECORDED": 182,
            "recorded_share": 0.662,
            "measured_coverage_predicate_needs_four_clauses": (
                "`coverage is MEASURED` <=> anchor MEASURED AND era_gap_quarters == 0 AND "
                "era_class in (RECORDED, NO_BAR_HISTORY, REFERENCE) AND decidable -- 0 "
                "mismatches over 8,748 exhaustive probes. A first version of this session's "
                "claim dropped the gap and class clauses and was refuted: 105 RECORDED+gap "
                "probes, 63 REFERENCE, 23 NO_BAR_HISTORY. On the admitting cell it is 16 of "
                "232 trades (6.9 %)."),
            "by_account": {"FTMO": {"undecidable": 195, "recorded": 134},
                           "redacted_account": {"undecidable": 80, "recorded": 48}},
            "era_cells_changing_coverage_class": 192,
            "breakdown": {"RECORDED_MEASURED_to_MODELLED": 166,
                          "QUANTIZED_TRANSFERRED_to_MODELLED": 26,
                          "already_MODELLED_no_change": 83},
            "verdict_fields_moved": 0, "sleeve_stamp_fields_moved": 0,
            "trade_level_classes_corrected": 1584,
            "btc_recorded_trades_corrected": 78,
            "filed_by": "Session AL, POPULATION_RESTRICTION_USES_THE_WRONG_FIELD",
        },
    },
    {
        "sleeve": "__estate__",
        "component": "walkforward/spec.py + walkforward/era_population.py",
        "gate": "significance",
        "verdict": "CLOSED",
        "prescription": "POPULATION_RULE_WAS_NOT_IN_THE_SEAL",
        "prescription_in_diagnostics_enum": False,
        "action": (
            "CLOSED by B1251-B1252. `SpreadModel.estimate` has taken `require_decidable=` since "
            "AG shipped it and no production path passed it -- its only call sites anywhere were "
            "two tests -- while the restriction it expresses was reimplemented by hand three "
            "times inside one session's drivers, each time BEFORE run_gate, so two runs on two "
            "populations produced the SAME spec_sha256. Now: "
            "`GateSpec.spread_require_decidable` threaded spec -> panel.price_trades -> cost_r "
            "-> spread_price, seal-honest on spread_composition's rule (None == False == the "
            "pre-field seal; only True moves it), verified against the published spec_sha256 "
            "cohort. `era_population.py` names the four rules once with the argument for each, "
            "stamps the rule into spec_id (which canonical() hashes) and sets the flag where the "
            "rule needs it. Zero seal collisions across 240 arms. 14 tests."),
        "evidence": {
            "seal_collisions_after": 0, "arms_checked": 240,
            "redundancy_control_armed_on": 72, "redundancy_control_inert_on": 168,
            "redundancy_control_note": (
                "`decidability_refusals == 0` is a PASS on the 72 armed arms (DECIDABLE + "
                "RECORDED_AND_DECIDABLE at low/mid/high) and a TAUTOLOGY on the other 168 -- "
                "144 have the flag off, 24 have it on at the flat band where the era path is "
                "never entered. Armed on 0 of the 9 ADMIT arms. An earlier version quoted 240."),
            "populations_sealed_separately": 5,
            "population_parity_vs_AL": "IDENTICAL on all 9 published counts",
            "p_raw_parity_vs_AL": "IDENTICAL on all 5 shared arms to 1e-9",
            "published_seals_pinned_by_value": 3,
            "published_seals_pinned_by_count_only": 15,
            "seal_pinning_note": (
                "All 18 published spec_sha256 in the restored cohort DO reproduce at HEAD "
                "(18/18, 0 mismatches). But only 3 are pinned BY VALUE, by "
                "test_candidate_family.py:341-352; the other 15 are pinned only by "
                "`len(seals) >= n` at :515, which an adversarial pass showed still passes when "
                "all 18 are replaced by fabricated hashes. AN adds "
                "test_published_seals_pinned_by_value.py to close it. An earlier version of "
                "this row implied the suite guarded all 18."),
            "filed_by": "Session AL, §10 item 4",
        },
    },
    {
        "sleeve": "__estate__",
        "component": "spread_model decidability rule (the 0.5 log threshold)",
        "gate": "cost_coverage",
        "verdict": "DEFECT",
        "prescription": "DECIDABILITY_IS_SCALE_INCORRECT_MEASURE_IT_IN_R",
        "prescription_in_diagnostics_enum": False,
        "action": (
            "OPEN, with the instrument built and its verdict claim REFUTED by my own placebo -- "
            "read both halves. `decidable` is `max(band_halfwidth_log, class_floor) <= 0.5`, a "
            "threshold on the spread's own LOG width, and an admission is a claim in R. The defect is "
            "the threshold's LEVEL, not its direction -- an earlier version of this row said "
            "the orderings were 'close to INVERTED' and an adversarial pass refuted it. "
            "MEASURED: within every sleeve `decidable` separates narrow from wide in the "
            "CORRECT direction (mx_btcusd 8.83x, sub_xvol_pullback 5.09x, sub_mid_dn_revert "
            "1.55x, pooled over 939 trades 3.02x, Spearman(flag, cost_range_R) = -0.2249). "
            "What IS wrong is that one fixed log threshold means different amounts of R on "
            "different sleeves: sub_mid_dn_revert's ACCEPTED trades sit at 0.0232 R median "
            "while mx_btcusd's REJECTED trades sit at 0.0122 R, so the flag tolerates 1.9x "
            "more cost uncertainty on one sleeve than it refuses on another. The '6.38x' "
            "cross-sleeve figure (SCHEDULE/dec 0.0782 vs RECORDED/UNDEC 0.0122) is rank 1 of "
            "50 group pairs, only 5 of which have accepted wider -- an extreme order statistic, "
            "not a property of the rule. Also true and unchanged: 36.5 % of all 'decidable' "
            "eras are SCHEDULE, where the narrow band is a degeneracy (one backfilled "
            "constant, every dispersion term zero, floored to 0.18229). REPLACEMENT INSTRUMENT: keep a trade if its charged cost range <= tau R. "
            "It is entry-knowable -- verified to be exactly the SPREAD range (max |total_range - "
            "spread_range| = 2.2e-16 over 232 trades) because commission, swap and slippage are "
            "band-independent and cancel -- and it ADMITs mx_btcusd at every tau in [0.02, 0.50] "
            "with a plateau from 0.05. **DO NOT adopt it on the p.** Its 0.0011 -> 0.0008 gain is "
            "NOT identifiable: the 20 trades it drops average -0.10 R against the kept +1.13 R "
            "and all 20 sit in 2018+2020, and a year-matched random 20-trade removal reaches "
            "p <= 0.0008 in 10 of 40 draws (placebo p 0.268). Outcome-independent in assignment, "
            "not outcome-neutral -- AL §3.3's distinction, applied to my own proposal. "
            "NEXT: fix tau on a materiality argument in R, never on a p-value, and re-test on a "
            "sleeve whose spread is a LARGER share of its risk unit, where the two orderings "
            "should separate in the opposite direction."),
        "evidence": {
            "median_cost_range_r": {
                "btc_RECORDED_undecidable_REJECTED_by_flag": 0.012248,
                "submid_SCHEDULE_decidable_ACCEPTED_by_flag": 0.078182,
                "cross_sleeve_extreme_ratio": 6.383,
                "NOT_an_inversion": ("rank 1 of 50 group pairs; only 5 of 50 have accepted "
                                     "wider than rejected")},
            "within_sleeve_ordering_is_CORRECT_everywhere": {
                "mx_btcusd": {"dec": 0.001388, "undec": 0.012248, "ratio": 8.83},
                "sub_xvol_pullback": {"dec": 0.002879, "undec": 0.014644, "ratio": 5.09},
                "sub_mid_dn_revert": {"dec": 0.023166, "undec": 0.035998, "ratio": 1.55},
                "pooled_939_trades": {"dec": 0.006717, "undec": 0.020276, "ratio": 3.02},
                "spearman_flag_vs_cost_range": -0.2249},
            "the_real_defect_is_the_LEVEL": (
                "submid ACCEPTED median 0.0232 R > btc REJECTED median 0.0122 R, i.e. 1.9x "
                "more cost uncertainty tolerated on one sleeve than refused on another"),
            "band_high_tail_on_the_78": ("13 of 78 are charged >1.0 R of cost at band_high, "
                                        "max 2.3461 R -- the +0.5272 R/trade mean is over a "
                                        "distribution containing economically untakeable "
                                        "trades"),
            "schedule_share_of_decidable_eras": 0.365,
            "criterion_is_entry_knowable_to": 2.2e-16,
            "tau_sweep_all_admit": [0.02, 0.05, 0.10, 0.15, 0.20, 0.25, 0.50],
            "p_at_tau_0p05": 0.0008, "p_full_recorded": 0.0011, "n_at_tau_0p05": 212,
            "placebo_P2_year_matched_p": 0.268,
            "placebo_P2_admit_rate": "38/40",
            "verdict": "structural finding STANDS; verdict claim REFUTED",
        },
    },
    {
        "sleeve": "sub_mid_dn_revert",
        "component": "SUBMID_RECLOCK_V1.json headline / AM §1.3",
        "gate": "significance",
        "verdict": "DEFECT",
        "prescription": "ADMISSION_PROXIMITY_IS_A_FLAT_SNAPSHOT_ARTEFACT",
        "prescription_in_diagnostics_enum": False,
        "action": (
            "OPEN, and stated in the form that survived an adversarial pass -- an earlier "
            "version of this row said 'the RE-CLOCK GAIN is a flat-snapshot artefact', which is "
            "a claim about a DELTA supported only by LEVELS, and it is WITHDRAWN. What is "
            "flat-only is the sleeve's NEARNESS TO ADMISSION: AM's p 0.0198 reproduces to the "
            "digit (0.019798) at the flat 37-day snapshot and is 6.93x the BH rank-1 bar; at "
            "the mid band the same 533 trades, same option, same population give p 0.352365 = "
            "123.33x, a 17.80x proximity loss (not '18x'). The RE-CLOCK IMPROVEMENT, measured "
            "at all four bands against the authored-clock arm this session first omitted, does "
            "NOT vanish: 9.975x -> 2.647x -> 2.103x -> 1.605x closer in p, and it GROWS in "
            "R/day (+0.0988 flat, +0.1182 low, +0.1223 mid, +0.1298 high). At low and mid it is "
            "a SIGN FLIP on the expectancy gate that does not exist at flat -- authored fails "
            "expectancy, re-clocked passes. Charging the measured era cost makes AM's B1200 "
            "repair matter MORE. The population axis helps the level but does not rescue it: "
            "RECORDED 0.163, RECORDED_AND_DECIDABLE 0.117 at mid. NEXT: the sleeve's prescription is not more "
            "trades and not a population -- 65.6 % of its SCHEDULE trades and 39.3 % of its "
            "undecidable-RECORDED trades carry a charged cost range OVER 0.05 R, and its "
            "all-population median cost range is 0.0256 R against mx_btcusd's 0.0023 R (11x), "
            "the widest of any candidate cell. So its lever is COST: either a symbol subset "
            "whose era bands are tight, or tick capture on the eras it trades."),
        "evidence": {
            "am_published_p": 0.0198, "reproduced_at_flat": 0.019798,
            "p_at_mid": 0.352365, "p_at_high": 0.533447,
            "x_the_bh_rank1_bar": {"flat": 6.93, "mid": 123.33},
            "proximity_loss_flat_to_mid": 17.798,
            "reclock_delta_by_band": {
                "flat": {"x_closer_in_p": 9.975, "delta_r_per_day": 0.09876,
                         "expectancy_gate_flip": False},
                "low": {"x_closer_in_p": 2.647, "delta_r_per_day": 0.11819,
                        "expectancy_gate_flip": True},
                "mid": {"x_closer_in_p": 2.103, "delta_r_per_day": 0.12232,
                        "expectancy_gate_flip": True},
                "high": {"x_closer_in_p": 1.605, "delta_r_per_day": 0.12984,
                         "expectancy_gate_flip": False}},
            "p_at_mid_by_population": {"ALL_ERAS": 0.352365, "RECORDED": 0.163484,
                                       "DECIDABLE": 0.439856,
                                       "RECORDED_AND_DECIDABLE": 0.117488},
            "frac_trades_with_cost_range_over_0p05R": {"SCHEDULE/dec": 0.6558,
                                                       "RECORDED/UNDEC": 0.3929},
            "like_for_like": ("same 533 re-clocked trades, same B_balanced, same population; "
                              "only the cost band differs. AM's solo-gate p_raw reproduces in "
                              "the 32-sleeve family run, which is the control"),
        },
    },
    {
        "sleeve": "__estate__",
        "component": "SPREAD_MODEL_V1_ERA_SCHEDULE_BAND_WIDENED.json / AM §4.5",
        "gate": "cost_coverage",
        "verdict": "RECOMMEND_ADOPT",
        "prescription": "ADOPT_THE_BAND_WIDENED_ERA_TABLE",
        "prescription_in_diagnostics_enum": False,
        "action": (
            "RECOMMENDED FOR ADOPTION -- merge-train's call, not mine. It moves 0 verdicts "
            "across every standing candidate at every band and population tested (54 arms), "
            "leaves the mid band byte-identical, and its only measured effect is 4 of 54 arms on "
            "sub_mid_dn_revert @ ALL_ERAS moving in BOTH directions (low: p 0.2429 -> 0.2184; "
            "high: 0.5334 -> 0.5797) -- which is what a band widening should do. mx_btcusd's "
            "admission cannot move: BTCUSD has ZERO widened eras, because six of nine cryptos "
            "leave the defect's scope by AM's own §4.1 (their reference window is itself a "
            "nominal constant). **ALL FOUR of AM's published figures reproduce exactly** "
            "(536 eras, mean +0.166 log, 0 become undecidable, mid band unchanged). An earlier "
            "version of this row published a WRONG correction to the first two -- 585 eras at "
            "+0.152322 -- by counting the provenance stamp `band_halfwidth_log_v1` instead of "
            "the movement. 49 of the 585 stamped eras carry a delta of exactly 0.000000, and "
            "536 x 0.166247 / 585 = 0.152322, i.e. the 'correction' was AM's own mean diluted "
            "by 49 zeros. Withdrawn; AM needed no correction. ONE CONDITION SURVIVES: the "
            "widest ACTUALLY-widened half-width is 0.404800 (FTMO AUDUSD 2000Q2) against the "
            "0.5 threshold -- 0.09520 log of headroom, so a hypothesis 1.235x larger starts "
            "flipping eras to UNDECIDABLE, which since B1250 degrades Coverage where before it "
            "would not have. (FTMO CHFJPY 2000Q2 sits higher at 0.43031 but was stamped with "
            "delta 0; reading it as widened understates the margin by 37 %, which is what the "
            "same stamp-vs-movement error did.) Any future re-sizing of AH §6 must check that "
            "coupling."),
        "evidence": {
            "n_eras_widened": 536, "by_account": {"FTMO": 394, "redacted_account": 142},
            "mean_halfwidth_increase_log": 0.166247,
            "n_eras_stamped": 585, "n_stamped_but_delta_zero": 49,
            "withdrawn_wrong_correction": {
                "n_eras": 585, "mean": 0.152322,
                "cause": "counted the provenance stamp, not the movement",
                "arithmetic": "536 * 0.166247 / 585 == 0.152322"},
            "am_claimed": {"n_eras": 536, "mean_increase_log": 0.166},
            "am_claims_reproduce": {"n_eras": True, "mean_increase": True,
                                    "n_become_undecidable": True, "mid_band_unchanged": True},
            "verdicts_moved": 0, "arms_tested": 54, "arms_with_any_number_moved": 4,
            "widest_halfwidth_after": 0.404800, "widest_at": "FTMO AUDUSD 2000Q2",
            "threshold": 0.5,
            "headroom_log": 0.095200, "flip_multiplier": 1.235,
            "btcusd_widened_eras": 0,
            "widened_symbols_ftmo": 14,
        },
    },
    {
        "sleeve": "mx_btcusd_d1_donchian_20_breakout",
        "component": "the admission's band stamp",
        "gate": "significance",
        "verdict": "DEFECT",
        "prescription": "ADMISSION_IS_BAND_CONDITIONAL_STAMP_IT",
        "prescription_in_diagnostics_enum": False,
        "action": (
            "OPEN as a reporting discipline, not a sleeve defect. Across 240 gated arms exactly "
            "9 ADMIT and all nine are this sleeve on RECORDED -- at flat, low and mid. It "
            "REJECTS at band_high (target_5R p 0.005099, target_4R 0.015798). The band "
            "sensitivity is entirely in the 78 undecidable-RECORDED trades: they move -32.5 % "
            "net from low to high (+0.7816 -> +0.5272 R/trade) while the clean 154 move -0.6 % "
            "(+0.7927 -> +0.7883). So 'ADMIT' unqualified is wrong in both directions -- it "
            "understates the clean population's robustness and overstates the whole cell's. "
            "NEXT: every publication of this admission carries 'admits at 2 of 3 bands', and at "
            "band_high its p sits inside the BH rank-2 threshold (0.005714) so the pair "
            "structure returns there. The capture that would close it is tick data for the nine "
            "undecidable BTCUSD quarters, 2018Q2-2025Q3."),
        "evidence": {
            "admit_arms": 9, "arms_total": 240,
            "all_nine_are": "mx_btcusd on RECORDED at flat/low/mid",
            "p_by_band_target_5R": {"flat": 0.001000, "low": 0.001100, "mid": 0.001100,
                                    "high": 0.005099},
            "bh_rank1_bar_at_m35": 0.0028571, "bh_rank2_bar": 0.0057143,
            "bonferroni_bar_at_m35": 0.0014286,
            "net_r_per_trade_low_to_high": {"disputed_78": [0.7816, 0.5272],
                                            "clean_154": [0.7927, 0.7883]},
            "gross_r_per_trade": {"disputed_78": 1.0196, "clean_154": 1.0263},
            "undecidable_quarters": ["2018Q2", "2018Q3", "2019Q3", "2019Q4", "2020Q1",
                                     "2020Q3", "2020Q4", "2021Q1", "2025Q3"],
            "band_high_tail": ("13 of the 78 are charged >1.0 R of total cost at band_high, max "
                               "2.3461 R, so the +0.5272 R/trade mean averages over cells the "
                               "pessimistic band prices out of existence"),
            "chronological_decay_no_gate_can_see": {
                "fold_mean_r_per_day": [1.1341, 1.5118, 1.8663, 0.2838, 0.1124],
                "first_three_mean": 1.5041, "last_two_mean": 0.1981, "ratio": 0.1317,
                "recent_window": "2023-01-17..2025-09-25",
                "n_trades_in_last_two": 80, "share": 0.3448,
                "why_invisible": ("`stability` counts the SIGN of a fold mean, not its level, so "
                                  "min_oos_positive_fold_frac reads 5/5 on a 7.6x decay"),
                "prescription": "SIZE ON THE RECENT FOLDS, NOT THE POOLED FIGURE"},
            "disputed_78_are_fold_concentrated": {
                "n_in_folds_1_2": 53, "fold_2_share": 0.905,
                "folds_with_zero_disputed": [3, 4],
                "reading": ("dropping them removes most of two early folds and takes fold "
                            "positivity 5/5 -> 3/5, which is the mechanism behind p 0.0011 -> "
                            "0.0158; the pooled gross comparison cannot carry it")},
        },
    },
]


def main() -> int:
    existing = [json.loads(x) for x in QUEUE.read_text().splitlines() if x.strip()]
    have = {hashlib.sha256(json.dumps(r, sort_keys=True).encode()).hexdigest()
            for r in existing}
    added = 0
    with QUEUE.open("a") as fh:
        for r in ROWS:
            row = {**r, "session": "AN", "ts": TS, "appended_utc": TS}
            h = hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest()
            if h in have:
                print(f"  SKIP duplicate: {r['prescription']}")
                continue
            fh.write(json.dumps(row, sort_keys=True) + "\n")
            have.add(h)
            added += 1
            print(f"  + {r['verdict']:15s} {r['prescription']}")
    total = sum(1 for x in QUEUE.read_text().splitlines() if x.strip())
    print(f"\nrepair queue: {len(existing)} -> {total} rows ({added} appended by AN)")
    return added


if __name__ == "__main__":
    main()
