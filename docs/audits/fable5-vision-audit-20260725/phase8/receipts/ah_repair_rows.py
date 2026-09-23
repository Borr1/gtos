"""Session AH -- append this session's repair-queue rows. Idempotent, append-only.

    python3 .../ah_repair_rows.py

Rows go to `phase6/receipts/REPAIR_QUEUE_APPEND.jsonl` beside AD's 49, and a session-scoped
copy to `phase8/receipts/REPAIR_QUEUE_AH.json`. The shared `REPAIR_QUEUE_V1.json` (134 rows)
is NOT rewritten -- the working agreement says appends, never overwrites, and the append file
is how three concurrent sessions share one queue without a merge conflict.

Idempotence is on `(session, sleeve, prescription)`: re-running replaces nothing and adds
nothing already present, so this can be run after each finding without duplicating rows.
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
sys.path.insert(0, str(REPO))

APPEND = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts/REPAIR_QUEUE_APPEND.jsonl"
MINE = HERE / "REPAIR_QUEUE_AH.json"
SESSION = "AH"


def load(name: str) -> dict:
    return json.loads((HERE / name).read_text())


def build() -> list[dict]:
    ent = load("ENTRY_HOUR_FRONTIER_V1.json")
    attr = load("AH_ENTRY_ATTRIBUTION.json")
    cond = load("CONDITIONING_MAP_V1.json")
    idx = load("AH_IDXREV_INVERSE_V1.json")
    moved = load("AH_VERDICTS_MOVED.json")
    v2 = load("SPREAD_MODEL_V2_VALIDATION.json")
    rows: list[dict] = []

    def add(sleeve, prescription, component, gate, action, evidence, primary=True):
        rows.append({"sleeve": sleeve, "session": SESSION, "verdict": "REJECT",
                     "prescription": prescription, "component": component, "gate": gate,
                     "margin": None, "is_primary": primary, "action": action,
                     "evidence": evidence})

    # ---- 1. the composition defect, closed ------------------------------------------
    add("spread_model_v1", "ERA_MODEL_PRODUCT_REPAIRED", "cost layer", None,
        "AF's ERA_MODEL_PRODUCT_UNVALIDATED row is CLOSED. The composition is now "
        "anchor x era_ratio ** b x hour_mult with b = %.4f (envelope %s), measured on three "
        "axes, and b=1 -- v1's unvalidated product -- is rejected at 5.0 sigma on the affected "
        "class. AF's interim (restrict to era_class == RECORDED) is retired: banded pricing is "
        "available on every era again. What is NOT repaired and IS sized: era_ratio is a ratio "
        "of bar MINIMA while the anchor is a tick p50, which inflates the ratio by 1.50x on "
        "constant-spread FX eras (SPREAD_MODEL_V2_VALIDATION.json -> "
        "min_to_p50_era_ratio_bias). That bias runs the same way as this repair, so every "
        "number here is conservative with respect to it."
        % (v2["composition"]["b"], v2["composition"]["b_envelope"]),
        {"class": "cost_model", "b": v2["composition"]["b"],
         "b_envelope": v2["composition"]["b_envelope"],
         "premium_floor": v2["composition"]["premium_floor"],
         "members_improved": moved["moved"]["member"]["n_improved"],
         "members_worsened": moved["moved"]["member"]["n_worsened"],
         "max_member_delta_r_per_day": moved["moved"]["member"]["pooled_delta_max"],
         "verdicts_changed": moved["moved"]["member"]["n_verdict_changed"],
         "unrepaired_min_to_p50_inflation_fx": v2["min_to_p50_era_ratio_bias"][
             "per_class_median_inflation"].get("fx"),
         "artifact": "phase8/receipts/SPREAD_MODEL_V2_VALIDATION.json"})

    # ---- 2. the FX D1 cohort: the entry hour is a real repair ------------------------
    agg = ent["aggregate"]
    dec = ent["cost_decomposition"]
    add("fam_donchian_20_breakout_fx_d1", "ENTRY_HOUR_SHIFT_TO_H4_CLOSE", "entry convention",
        "expectancy",
        "Every one of the cohort's 20,658 decision bars closes at broker hour 00 -- the "
        "measured 13x-38x hour of the week -- so the fill lands there by construction. Moving "
        "the entry to the first H4 close (broker 04:00) is simulated end to end on 16,337 "
        "decision bars against arm B, the declared control (same entry instant, H4 exit "
        "resolution): cost %.4f -> %.4f R/trade, gross %+.5f -> %+.5f, net %+.4f, cost:gross "
        "%.1f to 1. **That is the CEILING of the cost convention**: cost_r charges one crossing "
        "evaluated entirely at entry_utc (model.py:403, :439) while a round trip crosses twice "
        "and the exit leg's hour is unchanged by the shift, so on a 50/50 split the saving is "
        "%+.4f, net %+.4f, cost:gross %.1f to 1. Cost dominates gross on either reading. The "
        "family pooled OOS mean goes %+.4f -> %+.4f R/day. This is a GENERATION change (the "
        "fill price moves), so it needs a sleeve-side entry convention, not a re-cost."
        % (attr["attribution"]["model_convention"]["cost_B"],
           attr["attribution"]["model_convention"]["cost_C"],
           agg["B_d1close_h4exit"]["mean_r_gross"], agg["C_h4next_h4exit"]["mean_r_gross"],
           attr["attribution"]["model_convention"]["net_delta_r"],
           attr["attribution"]["model_convention"]["cost_over_gross_ratio"],
           attr["attribution"]["half_at_each"]["cost_saving_r"],
           attr["attribution"]["half_at_each"]["net_delta_r"],
           attr["attribution"]["half_at_each"]["cost_over_gross_ratio"],
           ent["runs"]["v2_damped|B_d1close_h4exit|family"]["rows"][
               "fam_donchian_20_breakout_fx_d1"]["pooled_oos_mean_r"],
           ent["runs"]["v2_damped|C_h4next_h4exit|family"]["rows"][
               "fam_donchian_20_breakout_fx_d1"]["pooled_oos_mean_r"]),
        {"class": "entry_geometry", "n_decision_bars": ent["population"][
            "n_decision_bars_all_arms"],
         "arms": list(ent["arms"]),
         "vs_control_arm_B": attr["member_counts_by_baseline"]["B_d1close_h4exit"],
         "vs_arm_A_confounded": attr["member_counts_by_baseline"]["A_d1close_d1exit"],
         "attribution": attr["attribution"],
         "robustness": ("the saving survives where NOTHING is extrapolated: +0.1129 R spread "
                        "saving / +0.1133 R net on the 358 trades whose own era ratio is "
                        "inside [0.9, 1.1], where the effective hour multiplier is exactly "
                        "the tick-measured one; +0.1045 R on 2020s trades. NOTE: the "
                        "era_class == RECORDED cell (+0.1511 R) is NOT era-neutral -- its "
                        "median era ratio is 2.125 -- and citing it as such was an "
                        "overstatement this session caught and corrected. See "
                        "AH_ENTRY_ERA_ROBUSTNESS.json -> cells.era_ratio_band"),
         "artifact": "phase8/receipts/ENTRY_HOUR_FRONTIER_V1.json"})

    add("fam_atr_mean_reversion_fx_d1", "ENTRY_HOUR_SHIFT_HELPS_BUT_MECHANISM_DECAYS",
        "entry convention", "expectancy",
        "The same shift helps this family too (%+.4f -> %+.4f R/day) but it is the ONLY "
        "mechanism whose members lose gross edge by waiting: all three cohort members that get "
        "worse net are atr_mean_reversion (cadjpy, usdjpy, eurusd) and they carry the largest "
        "pre-entry drift (cadjpy 0.096 R). A reversion has already happened four hours after "
        "the close. Prescription: if the entry convention moves, this mechanism needs its own "
        "shorter shift measured, not the cohort's."
        % (ent["runs"]["v2_damped|B_d1close_h4exit|family"]["rows"][
               "fam_atr_mean_reversion_fx_d1"]["pooled_oos_mean_r"],
           ent["runs"]["v2_damped|C_h4next_h4exit|family"]["rows"][
               "fam_atr_mean_reversion_fx_d1"]["pooled_oos_mean_r"]),
        {"class": "entry_geometry",
         "mean_pre_entry_drift_r": agg["C_h4next_h4exit"]["mean_pre_entry_drift_r"],
         "artifact": "phase8/receipts/ENTRY_HOUR_FRONTIER_V1.json"})

    # ---- 3. mx_cadjpy, the named beneficiary ----------------------------------------
    pm = ent["per_member"]["mxf_volume_surge_reversal_cadjpy_d1"]
    add("mx_cadjpy_d1_volume_surge_reversal", "ENTRY_HOUR_MOVES_IT_ACROSS_ZERO",
        "entry convention", "significance",
        "AF's named beneficiary and the estate's closest miss. Its own live rule at the "
        "shifted entry: %+.4f -> %+.4f R/day at mid band, i.e. across zero. Its blocking gate "
        "moves from expectancy to SIGNIFICANCE, which is the same blocker AD found at all 25 "
        "best exit cells and the same one mx_btcusd waits on. Three donchian JPY crosses in "
        "the same cohort also cross zero (nzdjpy +0.083, cadjpy +0.061, audjpy +0.044) and "
        "reject on LIFETIME instead -- their scored window is positive and their pre-2010 "
        "history is not, which is a sample/era question and a different repair."
        % (pm["B_d1close_h4exit"]["pooled_oos_mean_r_v2_damped"],
           pm["C_h4next_h4exit"]["pooled_oos_mean_r_v2_damped"]),
        {"class": "live_sleeve", "armed": [],
         "p_raw_at_shifted_entry": pm["C_h4next_h4exit"]["p_raw_v2_damped"],
         "artifact": "phase8/receipts/ENTRY_HOUR_FRONTIER_V1.json"})

    # ---- 4. member conditioning: refuted as a lever, with the alternative named ------
    s = cond["summary"]
    tw = cond["C1b_carrier_holdout"]["_trade_weighted"]
    add("AF_23_MIXTURE_FAMILIES", "NOT_MEMBER_SELECTION_USE_COST_AND_EXIT_GEOMETRY",
        "mechanism x class", "significance",
        "AF's MEMBER_CONDITIONING_NOT_BREADTH prescription is answered and it does not "
        "deliver. Choosing the carrier set on quintiles 0-3 and scoring quintile 4 helps in "
        "%d of %d scoreable mixtures -- a coin flip -- at a median %+.5f R/trade GROSS, an "
        "equal-weight-per-family mean of %+.4f, and a TRADE-WEIGHTED %+.6f over %d selected "
        "against %d holdout trades. Carrier-set overlap between consecutive quintiles beats "
        "its own (size- and universe-matched) chance baseline in %d of 23 and falls BELOW it "
        "in %d; only %d clear that clause AND a holdout sign agreement of 0.6. And 0 of 30 "
        "families cohere inside the PRE-DECLARED dial bucket. What DOES move these families "
        "is cost geometry: the composition repair is worth up to +0.34 R/day per member and "
        "the entry shift another +0.14 on the FX cohort. Route the 23 to those two levers and "
        "to AD's exit surface, not to member picking."
        % (s["n_carrier_selection_helps_on_holdout"], s["n_mixtures_scoreable_on_holdout"],
           s["median_carrier_selection_gain_on_holdout"],
           sum(cond["C1b_carrier_holdout"][f]["selection_gain_r_gross"]
               for f in cond["mixture_families"]
               if cond["C1b_carrier_holdout"][f]["selection_gain_r_gross"] is not None)
           / max(1, s["n_mixtures_scoreable_on_holdout"]),
           tw["gain"], tw["n_selected"], tw["n_all"],
           s["n_overlap_beats_chance"], s["n_overlap_below_chance"],
           s["n_carrier_stable_two_clause"]),
        {"class": "family_conditioning", "n_families": s["n_mixture_families"],
         "n_overlap_beats_chance": s["n_overlap_beats_chance"],
         "n_overlap_below_chance": s["n_overlap_below_chance"],
         "n_carrier_stable_two_clause": s["n_carrier_stable_two_clause"],
         "trade_weighted_selection_gain_r_gross": tw["gain"],
         "n_coheres_under_pre_declared_dial": s["n_coheres_under_pre_declared_dial"],
         "units_note": ("selection gains are GROSS R per trade, never net of broker-true "
                        "cost. The chance baseline was corrected mid-session after an "
                        "adversarial pass: the first version drew from the lifetime member "
                        "universe rather than each fold's own scored set, which understated "
                        "chance overlap -- see IMPLEMENTATION_STATE B1012."),
         "artifact": "phase8/receipts/CONDITIONING_MAP_V1.json"})

    r = cond["C3_crypto_donchian_split"]["d1_vs_h4_member_ranking"]
    add("fam_crypto_h4_donchian_ac60_crypto_h4", "CARRIER_IS_THE_CELL_NOT_THE_SYMBOL",
        "mechanism x class", "significance",
        "The named per-member split is real at H4 (permutation p 0.0015 against a "
        "shuffled-label null, split-half sign agreement 8 of 9) and NOT real at D1 (p 0.38, "
        "4 of 9). And the same nine symbols rank differently across the two timeframes: "
        "Spearman %.2f, sign agreement %.2f, DASHUSD -0.210 at D1 and +0.883 at H4. So the "
        "carrier is the (symbol x timeframe) CELL and cannot have a symbol-level cause -- "
        "maturity and liquidity are properties of the same instrument in both. Vintage "
        "correlates (r 0.62-0.65, t~2.1) and DASHUSD, the best H4 member at 1.7 years of "
        "history, refutes it as the mechanism. Do not price a crypto cluster on member "
        "selection; the lever left is sample and conditioning on the two armed symbols."
        % (r["spearman_r"], r["sign_agreement"]),
        {"class": "family_conditioning", "spearman_d1_vs_h4": r["spearman_r"],
         "permutation_p_h4": cond["C3_crypto_donchian_split"][
             "fam_crypto_h4_donchian_ac60_crypto_h4"]["noise_null"]["permutation_p"],
         "permutation_p_d1": cond["C3_crypto_donchian_split"][
             "fam_donchian_20_breakout_crypto_d1"]["noise_null"]["permutation_p"],
         "artifact": "phase8/receipts/CONDITIONING_MAP_V1.json"})

    # ---- 5. mx_nzdjpy: the pre-declared gate, rescued by the two repairs -------------
    d = cond["C4b_nzdjpy_under_both_repairs"]["decomposition"]["shared"]
    c = cond["C4b_nzdjpy_under_both_repairs"]["arms"][
        "C_h4next_h4exit|v2_damped|shared"]["gated"]
    add("mx_nzdjpy_d1_donchian_20_breakout", "PRE_DECLARED_REGIME_GATE_NOW_POSITIVE",
        "regime gate", "significance",
        "AF measured the pre-declared PERSISTENCE==trend gate at -0.1953 R/day and concluded "
        "the variable does not explain the sleeve. Reproduced BIT-FOR-BIT (-0.19526803768383966, "
        "p 0.9011098890110989, n=94) on an independently regenerated population. On the 83 "
        "decision bars every arm shares -- the 11 dropped are Friday D1 closes whose next H4 "
        "close is 51-53 h away, and their gross mean is HIGHER, so the 94-trade cell flatters "
        "the middle step -- the chain is %+.5f (AF's baseline) -> %+.5f (composition repair "
        "alone, STILL NEGATIVE) -> **%+.5f R/day, p %.4f, %s of the OOS folds positive on "
        "n=%d**. **THE ENTRY HOUR DOES ALL OF IT.** At broker hour 04 NZDJPY's hour multiplier "
        "is 0.92-1.05, below PREMIUM_FLOOR 1.5, so the two spread compositions are BIT-IDENTICAL "
        "there and arm C returns the same +0.21895 under AF's own unrepaired v1_multiplicative. "
        "The two repairs are one defect reached two ways, not two additive gains. AF's "
        "conclusion was about the worst entry hour of the week, not about the variable. The "
        "post-hoc VOL_REGIME==hi bucket, by contrast, holds in only 2 of 5 eras and should stay "
        "unpromoted."
        % (d["gated_v1_hour00"], d["gated_v2_hour00"], c["pooled_oos_mean_r"], c["p_raw"],
           c["oos_positive_fold_frac"], c["n_trades"]),
        {"class": "live_sleeve_candidate", "dial": "PERSISTENCE", "bucket": "trend",
         "basis": "pre_declared", "decomposition_shared_population": d,
         "composition_repair_worth_at_hour04": d["composition_repair_worth_at_hour04"],
         "post_hoc_bucket_eras_positive": cond["C4_nzdjpy_break_by_era"]["buckets"][
             "VOL_REGIME==hi"]["eras_positive"],
         "artifact": "phase8/receipts/CONDITIONING_MAP_V1.json"})

    # ---- 6. the index volume-surge family: the session's best new cell ---------------
    g = cond["C5_volume_surge_index_folds"]["gate_runs"]["enumerated_best:VOL_REGIME==hi"]
    eb = cond["C5_volume_surge_index_folds"]["enumeration_bill"]
    add("fam_volume_surge_reversal_index_d1", "REGIME_CONDITIONED_ADMIT_PENDING_FAMILY_SIZE",
        "regime gate", "significance",
        "AF's SAMPLE_OR_STABILITY row, answered. The pre-declared PERSISTENCE==revert bucket "
        "lifts fold stability to 0.6 and kills the mean (-0.0324). The ENUMERATED best cell, "
        "VOL_REGIME==hi -- mechanically the regime a volume-surge reversal should want -- is "
        "**%+.4f R/day, %s of OOS folds positive, raw p %.4f on n=%d**, and its only failing "
        "gate is significance. Enumeration bill carried: %d cells, so "
        "Bonferroni-within-enumeration p %.3f. Against the declared family it admits under BH "
        "alpha 0.20 at <= %d looks and Bonferroni 0.05 at <= %d. Same class of owner decision "
        "as mx_btcusd's, on the same unresolved `declared_family_size` question."
        % (g["pooled_oos_mean_r"], g["oos_positive_fold_frac"], g["p_raw"], g["n_trades"],
           eb["n_cells_enumerated"], eb["bonferroni_within_enumeration"],
           eb["declared_family_size_that_would_admit"]["bh_alpha_0.20"],
           eb["declared_family_size_that_would_admit"]["bonferroni_alpha_0.05"]),
        {"class": "family_conditioning", "cell": "VOL_REGIME==hi", "basis": "enumerated_best",
         "n_cells_enumerated": eb["n_cells_enumerated"],
         "fold_test_means": g["fold_test_means"],
         "pre_declared_cell_result": cond["C5_volume_surge_index_folds"]["gate_runs"][
             "pre_declared:PERSISTENCE==revert"]["pooled_oos_mean_r"],
         "owner_decision": "declared_family_size (the same one AF routed for mx_btcusd)",
         "artifact": "phase8/receipts/CONDITIONING_MAP_V1.json"})

    # ---- 7. idxrev: exhausted at this level, with the list ---------------------------
    add("idxrev", "PARK_REPAIR_PATHS_EXHAUSTED_AT_THIS_LEVEL", "direction / regime", "expectancy",
        "AA's standing INVERSE row, closed. Re-simulated (not sign-flipped -- its target/stop "
        "is %.2f, so negating a stored R would describe an instrument that does not exist), "
        "forward parity %d of %d exact on r_gross against AA. forward %+.4f, inverse %+.4f, "
        "and the PRE-DECLARED PERSISTENCE==revert gate -- the tape an index reversion sleeve "
        "was designed for -- makes BOTH worse (%+.4f / %+.4f). With AD's 1,631 exit cells "
        "(best +0.0004) that is exit geometry, direction and regime all exhausted. The "
        "entry-hour lever does not apply: index CFDs carry no quote at the rollover at all. "
        "What is left is a different trigger definition, which is a new sleeve rather than a "
        "repair of this one."
        % (idx["target_over_stop_median"], idx["forward_parity_exact_r_gross"],
           idx["n_rewalked"], idx["runs"]["forward"]["pooled_oos_mean_r"],
           idx["runs"]["inverse"]["pooled_oos_mean_r"],
           idx["runs"]["forward_revert"]["pooled_oos_mean_r"],
           idx["runs"]["inverse_revert"]["pooled_oos_mean_r"]),
        {"class": "live_sleeve", "armed": [],
         "tried": ["exit surface (AD, 1631 cells)", "inverse direction (re-simulated)",
                   "pre-declared PERSISTENCE==revert gate, both directions"],
         "not_applicable": "entry-hour shift (index CFDs do not quote at the rollover)",
         "artifact": "phase8/receipts/AH_IDXREV_INVERSE_V1.json"})

    now = dt.datetime.now(dt.timezone.utc).isoformat()
    for r_ in rows:
        r_["appended_utc"] = now
    return rows


def main() -> int:
    rows = build()
    have = set()
    if APPEND.is_file():
        for line in APPEND.read_text().splitlines():
            if not line.strip():
                continue
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue
            have.add((o.get("session"), o.get("sleeve"), o.get("prescription")))
    new = [r for r in rows
           if (r["session"], r["sleeve"], r["prescription"]) not in have]
    with APPEND.open("a") as fh:
        for r in new:
            fh.write(json.dumps(r, default=str) + "\n")
    MINE.write_text(json.dumps(
        {"schema": "gtos.repair_queue.append.v1", "session": SESSION,
         "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
         "run_label": "AH conditioning + entry economics",
         "note": ("appended to phase6/receipts/REPAIR_QUEUE_APPEND.jsonl beside AD's 49; the "
                  "shared REPAIR_QUEUE_V1.json's 134 rows are untouched"),
         "n_rows": len(rows), "rows": rows}, indent=1, default=str))
    print(f"{len(rows)} AH rows built, {len(new)} appended to "
          f"{APPEND.relative_to(REPO)} (now {sum(1 for _ in APPEND.open())} lines)")
    for r in rows:
        print(f"  {r['sleeve']:44s} {r['prescription']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
