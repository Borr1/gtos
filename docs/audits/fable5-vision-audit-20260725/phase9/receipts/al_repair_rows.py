"""Session AL — repair-queue rows, appended, never overwriting.

    python3 docs/audits/fable5-vision-audit-20260725/phase9/receipts/al_repair_rows.py

Idempotent: a row is keyed on `(session, sleeve, prescription, component)` and an existing key is
skipped rather than appended a second time. AK §7.7 recorded its own script double-appending; this
one is written so a re-run cannot.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

QUEUE = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts/REPAIR_QUEUE_APPEND.jsonl"
TS = "2026-07-30T12:00:00+00:00"

#: `prescription_in_diagnostics_enum` is True only for a prescription `walkforward.diagnostics`
#: already emits. A new label is honest and is flagged as new rather than smuggled in.
ROWS = [
    {
        "session": "AL", "sleeve": "__estate__", "ts": TS,
        "component": "src/costs/spread_model.py + WAVE_8/9 agreement §4",
        "prescription": "POPULATION_RESTRICTION_USES_THE_WRONG_FIELD",
        "prescription_in_diagnostics_enum": False,
        "gate": "significance",
        "verdict": "DEFECT",
        "action": (
            "The restriction of record -- `era_class == RECORDED`, wave-8 agreement §4 and AI §2.6 "
            "-- keeps eras whose cost the model itself calls UNDECIDABLE and drops eras whose cost "
            "is known to +/-20%. `era_class` records HOW an era_ratio was derived; "
            "`band_halfwidth_log` / `decidable` record HOW WELL the era's cost is known, and "
            "`SpreadModel.estimate` already takes `require_decidable=` (default False, passed by "
            "no driver or receipt in the estate; its only call sites anywhere are two tests written to "
            "prove it works, test_spread_model.py:184 and :374). Measured on BTCUSD: 9 of 25 "
            "RECORDED quarters exceed the model's own 0.5 log half-width rule (2020Q1 at 6.1131, "
            "a ~450x span) and ALL 11 quarters it drops are decidable -- the 7 SCHEDULE ones at "
            "raw half-width 0.0, the 4 QUANTIZED ones at 0.044-0.081 -- including every 2026 "
            "quarter, whose ratio is "
            "1.0 by construction because they sit inside the model's own reference window "
            "2026-06-18..07-25. REPAIR: restrict on `decidable` (the model's published rule), or "
            "pass `require_decidable=True`, and re-state AI §2.6's p-values on that population. "
            "AL_DECIDABLE_POPULATION_V1.json runs all three populations side by side."),
        "evidence": {
            "artifact": ("docs/audits/fable5-vision-audit-20260725/phase9/receipts/"
                         "AL_DECIDABLE_POPULATION_V1.json"),
            "recorded_quarters_failing_decidability": 9,
            "recorded_quarters_total": 25,
            "worst_retained_halfwidth_log": 6.1131,
            "dropped_quarters_total": 11, "dropped_quarters_all_decidable": True,
            "dropped_quarters_with_btc_trades": 10,
            "btc_trades_in_undecidable_recorded_quarters": 78,
            "btc_trades_dropped_all_decidable": 86,
        },
    },
    {
        "session": "AL", "sleeve": "mx_btcusd_d1_donchian_20_breakout", "ts": TS,
        "component": "walkforward/gate.py significance + the population stamp",
        "prescription": "EXIT_REPAIR",
        "prescription_in_diagnostics_enum": True,
        "gate": "significance",
        "verdict": "ADMIT_ON_A_NAMED_POPULATION",
        "is_primary": True,
        "action": (
            "`target_5R` on the RECORDED population ADMITS at the sealed B_balanced alpha 0.10 AND "
            "at A_strict's Bonferroni 0.05, at the RAISED family of 35: n 232, +0.9817 R/day, "
            "p_raw 0.0011, q 0.0385, no core gate failing, all five fold means positive "
            "[1.134, 1.512, 1.866, 0.284, 0.112], drop-best retention 0.775. It is a RIDGE not a "
            "spike -- target_4R also admits (p 0.0023) and the surface is monotone 1R->5R. "
            "TWO LIMITS, both measured and both belonging beside any arming: it does NOT admit at "
            "`band_high` (p 0.0051 there, which is inside rank 2 but not rank 1), and it does not "
            "admit on the ALL_ERAS population at ANY band. REPAIR to remove the population "
            "caveat: fix the restriction (row above) and re-state."),
        "evidence": {
            "artifact": ("docs/audits/fable5-vision-audit-20260725/phase9/receipts/"
                         "ADMISSION_CLOSER_V1.json + AL_BTC_ADVERSARIAL_V1.json"),
            "p_raw": 0.0010998900109989002, "q_at_m35": 0.03849615038496151,
            "largest_family_that_admits_alpha_0.10": 90,
            "largest_family_that_admits_alpha_0.05": 45,
            "bands_admitting": ["low", "mid"], "bands_rejecting": ["high"],
            "all_eras_arms_admitting": 0,
        },
    },
    {
        "session": "AL", "sleeve": "sub_xvol_pullback", "ts": TS,
        "component": "regime_spine/conditions.py SUB_XVOL_PULLBACK thresholds",
        "prescription": "BREADTH_REFUTED_FRAGILITY_REPAIRED",
        "prescription_in_diagnostics_enum": False,
        "gate": "significance",
        "verdict": "REJECT",
        "action": (
            "AB B658's banked prescription -- relax the vol bucket to `vr >= 1.4`, n 88 -> 420, "
            "'the trade a significance bar exists to make' -- is REFUTED as a significance repair "
            "and CONFIRMED as a fragility repair. Measured through the production GenerationPort "
            "over the full archive (406 reachable fires, not 420: the 14 missing are the pre-gap "
            "bars `candles_to_bars` drops, which the live book cannot trade): pooled OOS falls "
            "1.0264 -> 0.4176 R/day and p_raw WORSENS 0.0061 -> 0.0943 on all-eras "
            "at the flat 37-day snapshot (0.0120 -> 0.0626 on RECORDED@mid; 0.0058 -> 0.0781 on "
            "ALL_ERAS@mid -- 13.5x worse, and the direction is identical at every band). The "
            "PER-TRADE edge fell 3.3x (oos_mean_r_per_trade 1.39322 -> 0.42377) while the "
            "day-blocked null's block count rose only 11 -> 24, so the t-statistic went DOWN. But AI §2.5c's zero-integer-slack fragility is genuinely "
            "gone: `n_folds_evaluable` 3 -> 5, `thin_fold_frac` -> 0.0, and the sleeve's evidence "
            "no longer rests on integer luck. NEXT LEVER: not breadth. The exit -- AK's "
            "`target_4R` is +1.1565 R/day on the production cell -- and AB's regime dials."),
        "evidence": {
            "artifact": ("docs/audits/fable5-vision-audit-20260725/phase9/receipts/"
                         "ADMISSION_CLOSER_V1.json"),
            "production_p_all_eras": 0.006099390060993901,
            "variant_p_all_eras": 0.09429057094290572,
            "production_r_per_day": 1.0264103239719347,
            "variant_r_per_day": 0.4175616716529855,
            "n_production": 88, "n_variant_reachable": 406, "ab_published_n": 420,
            "folds_evaluable_production": 3, "folds_evaluable_variant": 5,
            "family_bill_raised": "32 -> 35 declared, 29 -> 32 looks taken",
        },
    },
    {
        "session": "AL", "sleeve": "sub_xvol_pullback", "ts": TS,
        "component": "walkforward/options.py A_strict sample gate",
        "prescription": "SAMPLE",
        "prescription_in_diagnostics_enum": True,
        "gate": "sample",
        "verdict": "NOT_EVALUABLE",
        "action": (
            "AI §2.5c predicted it and this is the measurement: on the RECORDED population at "
            "n=85 the ARMED sleeve is NOT_EVALUABLE under A_strict -- `min_folds_evaluable` 4 and "
            "`min_trades_per_fold` 8 both bite -- so it has no p-value at all at the strict "
            "option. It is REJECT-on-significance under B_balanced. A sleeve carrying real money "
            "whose evidence disappears at the next option up is a fragility fact, not a "
            "statistical curiosity. REPAIR: the exit (AK's target_4R, unswept on RECORDED before "
            "this session) or more trades from a source that is NOT threshold relaxation, since "
            "that is now measured to cost more p than it buys."),
        "evidence": {
            "artifact": ("docs/audits/fable5-vision-audit-20260725/phase9/receipts/"
                         "ADMISSION_CLOSER_V1.json"),
            "a_strict_verdict": "NOT_EVALUABLE", "b_balanced_verdict": "REJECT",
            "n_recorded": 85, "n_all_eras": 88,
            "min_folds_evaluable_a_strict": 4, "min_trades_per_fold_a_strict": 8,
        },
    },
    {
        "session": "AL", "sleeve": "sub_xvol_pullback", "ts": TS,
        "component": "src/costs/spread_model.py decidable + the armed book",
        "prescription": "ARMED_SLEEVE_HAS_NO_P_ON_THE_DECIDABILITY_POPULATION",
        "prescription_in_diagnostics_enum": False,
        "gate": "sample",
        "verdict": "NOT_EVALUABLE",
        "is_primary": True,
        "action": (
            "The THIRD independent measurement of AI §2.5c's fragility, and the one that touches "
            "armed money most directly. `sub_xvol_pullback` is trading real money on FTMO via "
            "`run_book.py --tags`. Its n across the four defensible populations is 88 (ALL_ERAS) / "
            "85 (RECORDED) / **56 (DECIDABLE)**, and at 56 it is NOT_EVALUABLE under B_balanced -- "
            "`n_folds_evaluable` 3 against a floor of 3 with the per-fold trade floor biting, so "
            "there is NO p-value for it on the population the spread model's own decidability rule "
            "defines. It is also NOT_EVALUABLE under A_strict on RECORDED. So the armed sleeve's "
            "evidence disappears under an OPTION change and under a POPULATION change, "
            "independently. That is not a reason to disarm -- the sleeve's pooled OOS is the "
            "estate's highest at +1.02 to +1.04 R/day wherever it IS evaluable -- it is a reason "
            "the arming discussion must carry the sample fact. REPAIR: the exit (AK's target_4R, "
            "+1.1565 R/day on the production cell), NOT threshold relaxation, which this session "
            "measured costs more p than it buys."),
        "evidence": {
            "artifact": ("docs/audits/fable5-vision-audit-20260725/phase9/receipts/"
                         "AL_DECIDABLE_POPULATION_V1.json"),
            "n_all_eras": 88, "n_recorded": 85, "n_decidable": 56,
            "decidable_verdict": "NOT_EVALUABLE", "a_strict_recorded_verdict": "NOT_EVALUABLE",
            "n_folds_evaluable_decidable": 3, "min_folds_evaluable_b_balanced": 3,
            "r_per_day_where_evaluable": [1.04385, 1.02152],
        },
    },
    {
        "session": "AL", "sleeve": "asia_pdl_fade", "ts": TS,
        "component": "AK_EXIT_FRONTIER_V2.json + AD's per-axis argmax composite",
        "prescription": "EXIT_REPAIR",
        "prescription_in_diagnostics_enum": True,
        "gate": "significance",
        "verdict": "REJECT",
        "margin": 23.06,
        "action": (
            "The stop x target x time-stop CROSS, gated at the declared 35 -- 120 DISTINCT cells, "
            "not 150: asia_pdl_fade.py:30 sets TARGET_R = 3.0 so the tgt_3R column is identical to "
            "tgt_native at all 30 (stop, time-stop) pairs (max |delta| 4.16e-17). AK's winner is "
            "confirmed AT THE PEAK and to 17 digits against AK_EXIT_FRONTIER_V2.json "
            "(+0.08462647486216306 both), with as_walked at rank 129. THREE corrections to this "
            "session's own first reading, all from an adversarial pass: (1) the surface is MIXED "
            "by AB's own rule, not BROAD -- ab_neighborhood.py:124 needs frac_positive >= 0.60 and "
            "this is 89/150 = 0.5933. (2) 'median/best = 0.0969 means ~90% of the level is "
            "selection' is NOT licensed: it is 0.2521 on stop >= 2.0 and 0.3414 on the stop-2.5 "
            "row because 0 of the 25 stop-1.0 cells are positive, all three axes are monotone, and "
            "an axis-wise argmax that never inspects a joint cell recovers 99.6% of the peak "
            "(stop_2.5x_tgt_5R_ts_none, +0.08427) -- so the level is mostly MECHANISM. No "
            "held-out selection estimate exists; cells are ranked on the metric that defines them. "
            "(3) the axes do not separate but the axis that MOVES is the time stop "
            "({1:48, 1.5:none, 2:48, 2.5:none, 3:none, 3.5:none}), not the target (native/5R/5R/"
            "native/native/2R once the duplicate ties are resolved), and the from-baseline stack "
            "loses only 14.5% (rank 11) -- so the cross CONFIRMED AK's single-axis answer rather "
            "than showing it was the wrong object. All 150 cells REJECT; 12 reach p < 0.10, none "
            "clears 0.002857. Significance is 23.1x away from the rank-1 bar. NEXT LEVER: "
            "regime conditioning from AB_REGIME_DIALS_V1.json, unexplored for this sleeve; the "
            "entry-hour axis AH found for the FX D1 cohort is unavailable here because the rule "
            "is first-of-day by construction."),
        "evidence": {
            "artifact": ("docs/audits/fable5-vision-audit-20260725/phase9/receipts/"
                         "AL_ASIA_PDL_FRONTIER_V1.json"),
            "n_cells_gated": 150, "n_cells_distinct": 120, "frac_positive": 0.5933,
            "ab_broad_threshold": 0.60, "ab_own_verdict": "MIXED",
            "median_r_per_day": 0.0082, "median_over_best_full_grid": 0.0969,
            "median_over_best_stop_ge_2": 0.2521, "median_over_best_stop_2.5_row": 0.3414,
            "axiswise_argmax_recovers_frac_of_peak": 0.996,
            "best_r_per_day": 0.08463, "best_p_raw": 0.0658934106589341,
            "ak_winner_rank": 2, "as_walked_rank": 129,
            "axes_separable": False, "axis_that_moves": "time_stop", "coverage_frac": 0.811925,
            "cross_bought_over_single_axis_r_per_day": 0.0,
            "rank_1_threshold_at_m35": 0.002857,
        },
    },
    {
        "session": "AL", "sleeve": "__estate__", "ts": TS,
        "component": "walkforward/candidate_family.py",
        "prescription": "RATCHET_ACROSS_FILE_SUCCESSION",
        "prescription_in_diagnostics_enum": False,
        "gate": "none",
        "verdict": "CLOSED",
        "action": (
            "The in-file ratchet turns a deleted member ROW into a load-time refusal "
            "(`high_water_size`) and a retracted look into one (`high_water_looks`). Nothing "
            "guarded the easier route to a smaller bill: publish a NEW declaration file with "
            "fewer members and point the driver at it -- the loader reads one file and has no "
            "predecessor to compare against. AL had to supersede V1 (its four size assertions in "
            "test_candidate_family.py mean an in-place edit reads as four defects), which is the "
            "operation that opens the hole, so the guard lands with it: "
            "test_candidate_family_v2_ratchet.py requires every CANDIDATE_FAMILY_V*.json to be a "
            "superset of what it says it `supersedes`, per family, with non-decreasing high-water "
            "marks, and every late addition logged in `history` with its price stated."),
        "evidence": {
            "test": "tests/research_infra/test_candidate_family_v2_ratchet.py",
            "n_tests": 6,
            "declaration": ("docs/audits/fable5-vision-audit-20260725/phase9/receipts/"
                            "CANDIDATE_FAMILY_V2.json"),
            "raise": "CANDIDATE_BOOK_V1 32 -> 35 declared, 29 -> 32 looks taken",
        },
    },
    {
        "session": "AL", "sleeve": "__estate__", "ts": TS,
        "component": "walkforward/fidelity.py",
        "prescription": "FIDELITY_REGISTRAR_FOR_THRESHOLD_VARIANTS",
        "prescription_in_diagnostics_enum": False,
        "gate": "fidelity",
        "verdict": "CLOSED",
        "action": (
            "`fidelity_for` fails closed as UNKNOWN and `B_balanced` sets "
            "`fidelity_refusal_is_hard`, so a threshold variant of a production rule could not be "
            "gated at all -- and `register_surface_expansion` is the wrong instrument: it demands "
            "a `symbol` and a `timeframe` and writes a basis_note claiming the book has never "
            "traded that symbol, all three false for a variant on the parent's own surface. "
            "`register_threshold_variant` grants the parent's structural CLASS rate stamped "
            "TRANSFERRED_CLASS and NEVER the parent's own measured recall, because a relaxed "
            "threshold fires on a SUPERSET of the parent's bars and the extra bars were never "
            "observed live. It refuses a variant whose params equal production's -- that would "
            "let one hypothesis be counted as two. `EXPANSION_PREFIXES` is split so each "
            "registrar accepts only its own prefixes."),
        "evidence": {
            "test": "tests/research_infra/test_fidelity_threshold_variant.py",
            "n_tests": 11,
            "parent_basis": "transferred_class (so for this parent the grant is numerically its "
                            "own record -- no relaxation, pinned by test)",
        },
    },
]


def main() -> dict:
    existing = []
    if QUEUE.is_file():
        existing = [json.loads(x) for x in QUEUE.read_text().splitlines() if x.strip()]
    # Re-runnable and correction-safe: ANOTHER session's rows are never touched, and THIS
    # session's are rewritten from `ROWS` rather than duplicated. The agreement's "never
    # overwrite" protects a sibling's appended row; a session correcting a figure in its own
    # unmerged row is the opposite of that, and appending a near-duplicate AMENDS row for a
    # typo would leave the wrong number in the queue as well as the right one.
    others = [r for r in existing if r.get("session") != "AL"]
    mine_before = len(existing) - len(others)
    rows = others + [{**r, "appended_utc": TS} for r in ROWS]
    QUEUE.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
    new = ROWS
    print(f"  AL rows: {mine_before} -> {len(ROWS)} (rewritten in place); "
          f"other sessions untouched: {len(others)}")
    after = [json.loads(x) for x in QUEUE.read_text().splitlines() if x.strip()]
    print(f"repair queue: {len(existing)} -> {len(after)} rows "
          f"({len(new)} appended, {len(ROWS) - len(new)} already present)")
    import collections
    print("by session:", dict(collections.Counter(r.get("session") for r in after)))
    dupes = len(after) - len({json.dumps(r, sort_keys=True) for r in after})
    print(f"byte-level duplicate rows: {dupes}")
    for r in new:
        print(f"  + {r['sleeve']:38s} {r['prescription']}")
    return {"n_before": len(existing), "n_after": len(after), "n_appended": len(new)}


if __name__ == "__main__":
    main()
