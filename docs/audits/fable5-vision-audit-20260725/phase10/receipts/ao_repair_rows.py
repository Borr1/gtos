"""Session AO — repair-queue rows, read out of AO's own artifacts rather than typed.

    python3 docs/audits/fable5-vision-audit-20260725/phase10/receipts/ao_repair_rows.py

Append-only into `phase6/receipts/REPAIR_QUEUE_APPEND.jsonl` (110 rows standing after AM).
Idempotent: a row whose (session, sleeve, prescription) triple is already present is skipped,
because AK §7.7 recorded a repair-row script that double-appended on a second run.

Every `evidence` block is READ from the artifact, so a row cannot drift from the measurement
it cites. Where a figure is not in an artifact the row says so rather than carrying a number
this file typed.
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

HERE = Path(__file__).resolve().parent
AUD = REPO / "docs/audits/fable5-vision-audit-20260725"
QUEUE = AUD / "phase6/receipts/REPAIR_QUEUE_APPEND.jsonl"
RC = HERE / "REGIME_CONDITIONING_V1.json"
PP = HERE / "BTC_POWER_POOL_V1.json"
FAM = HERE / "CANDIDATE_FAMILY_V3.json"

NOW = dt.datetime.now(dt.timezone.utc).isoformat()
REL = lambda p: str(p.relative_to(REPO))  # noqa: E731


def rows() -> list[dict]:  # noqa: PLR0915
    rc = json.loads(RC.read_text())
    pp = json.loads(PP.read_text())
    A, PA = rc["arms"], pp["arms"]
    out: list[dict] = []

    def arm(k):
        return A.get(k) or {}

    def parm(k):
        return PA.get(k) or {}

    # ---------------------------------------------------------------- 1. the structural one
    pin = rc["pinning"]
    out.append({
        "session": "AO", "sleeve": "sub_xvol_pullback",
        "component": "src/research_infra/regime_spine/dials.py + AB_REGIME_DIALS_V1.json",
        "prescription": "REGIME_DIALS_ARE_INSIDE_THE_CELL",
        "prescription_in_diagnostics_enum": "REGIME_GATE_OR_PARK",
        "verdict": "REJECT", "gate": "significance", "margin": None, "is_primary": True,
        "action": (
            "The diagnostics prescription `REGIME_GATE_OR_PARK` cannot be executed as a BUCKET "
            "gate for either substrate sleeve, and the reason is arithmetic rather than "
            "empirical. All five of Session AB's published dials take exactly ONE bucket over "
            "every trade both sleeves have ever produced -- measured, not argued: "
            f"{pin['sub_xvol_pullback']['n_dials_pinned']}/5 pinned over "
            f"{pin['sub_xvol_pullback']['n_trades_labelled']} trades for `sub_xvol_pullback` and "
            f"{pin['sub_mid_dn_revert']['n_dials_pinned']}/5 over "
            f"{pin['sub_mid_dn_revert']['n_trades_labelled']} for `sub_mid_dn_revert`. AB's dial "
            "functions ARE `substrate_engine`'s coordinates (max |delta| 0.0, zero bucket "
            "disagreements over 3,448 trades on three sleeves), and `substrate.py:69-79` makes "
            "each of those coordinates a firing CONDITION. A bucket gate on them is the "
            "identity filter. REPAIR, in two parts: (a) `AB_REGIME_DIALS_V1.json`'s "
            "`gates_sleeves` field should carry a PINNED_BY_CELL flag per (dial, sleeve) so no "
            "future session is routed to a no-op -- AL §10 item 2 and this commission both "
            "were; (b) for these two sleeves the conditioning that EXISTS is the free "
            "substrate coordinates (`sub_xvol_pullback` leaves rngpos / comp / session free; "
            "`sub_mid_dn_revert`, depth-7, leaves none) and the dial LEVEL inside the pinned "
            "bucket, which costs no sample and therefore belongs at SIZING rather than "
            "admission."),
        "evidence": {
            "artifact": REL(RC),
            "n_dials_pinned": rc["answer"]["n_dials_pinned_by_the_cell"],
            "dial_parity_max_abs_delta": {s: v["max_abs_delta"]
                                          for s, v in rc["dial_parity"].items()},
            "dial_parity_disagreements": {s: v["disagreements"]
                                          for s, v in rc["dial_parity"].items()},
            "n_free_substrate_coords": {s: v["n_substrate_coords_free"]
                                        for s, v in pin.items()},
            "asia_pdl_fade_is_the_control": pin["asia_pdl_fade"]["n_dials_pinned"],
        },
        "appended_utc": NOW,
    })

    # ---------------------------------------------------------------- 2. the cost band
    repro = rc["controls"]["flat_band_reproduces_AL_and_AM"]["rows"]
    out.append({
        "session": "AO", "sleeve": "asia_pdl_fade",
        "component": ("docs/.../phase9/receipts/al_asia_pdl_frontier.py:104-106 + "
                      "am_submid_reclock.py:457,:528"),
        "prescription": "EXIT_FRONTIER_IS_AT_THE_FLAT_SNAPSHOT_ONLY",
        "prescription_in_diagnostics_enum": "COST_GEOMETRY",
        "verdict": "REJECT", "gate": "significance", "margin": None, "is_primary": True,
        "action": (
            "AL's 120-distinct-cell exit cross and AM's re-clock both set no `spread_band`, so "
            "every figure in `AL_ASIA_PDL_FRONTIER_V1.json` and `SUBMID_RECLOCK_V1.json` is at "
            "`spec.py:82`'s flat_37_day_snapshot. Session AG's own rule is that a cell winning "
            "only at the flat snapshot has not been shown to win. Reproduced here to 1e-12 on "
            "R/day, p_raw AND n for all three published cells, then re-priced at the banded mid "
            "cost: `asia_pdl_fade @ stop_2.5x_tgt_native_ts_none` goes "
            f"{repro['asia_pdl_fade|stop_2.5x_tgt_native_ts_none|ungated']['here_pooled_oos_mean_r']:+.5f}"
            " -> "
            f"{repro['asia_pdl_fade|stop_2.5x_tgt_native_ts_none|ungated']['mid_band_pooled_oos_mean_r']:+.5f}"
            " R/day -- a SIGN FLIP -- and as-walked "
            f"{repro['asia_pdl_fade|as_walked|ungated']['here_pooled_oos_mean_r']:+.5f} -> "
            f"{repro['asia_pdl_fade|as_walked|ungated']['mid_band_pooled_oos_mean_r']:+.5f} "
            "(12.9x). REPAIR: re-run AL's cross at the mid band before any composition decision "
            "quotes '23x from the bar', and stamp the band on every cell of the frontier "
            "artifact. AL's '5/5 OOS folds at the winner' is a flat-snapshot property."),
        "evidence": {"artifact": REL(RC), "rows": repro,
                     "control": "all three reproduce to 1e-12 on R/day, p_raw and n"},
        "appended_utc": NOW,
    })

    # ---------------------------------------------------------------- 3. the re-clock's tier
    sm = repro["sub_mid_dn_revert|as_walked|ungated"]
    mid = arm("sub_mid_dn_revert|as_walked|ungated|band=mid|ALL_ERAS")
    rec = arm("sub_mid_dn_revert|as_walked|ungated|band=mid|RECORDED")
    out.append({
        "session": "AO", "sleeve": "sub_mid_dn_revert",
        "component": "docs/.../phase9/receipts/am_submid_reclock.py + SUBMID_RECLOCK_V1.json",
        "prescription": "RECLOCK_GAIN_IS_FLAT_BAND_ONLY",
        "prescription_in_diagnostics_enum": "COST_GEOMETRY",
        "verdict": "REJECT", "gate": "robustness", "margin": None, "is_primary": True,
        "action": (
            "AM's headline -- p 0.1975 -> 0.0198 and drop-best retention -0.1988 -> +0.3609, "
            "'10x closer to admission' -- is a flat-snapshot measurement. Reproduced here "
            f"exactly ({sm['here_pooled_oos_mean_r']:.17g} R/day, p {sm['here_p_raw']:.17g}, "
            f"n {sm['here_n']}), then re-priced at the banded mid cost: R/day "
            f"{mid.get('pooled_oos_mean_r')}, p {mid.get('p_raw')}, and the robustness statistic "
            f"AM's finding rests on goes to {mid.get('drop_best_retention')} on ALL_ERAS and "
            f"{rec.get('drop_best_retention')} on RECORDED. The re-clock IS a real repair -- it "
            "changes which trades exist and it reproduces bar-for-bar -- but 'the retention "
            "statistic changes sign' is true at the flat band and reverses at the banded one. "
            "REPAIR: re-run the re-clocked population at low/mid/high bands and re-state the "
            "carry tier from AM §1.4 on whichever band the population rule ratifies; the tier "
            "test is on the p99 hold and redacted_account's margin there was +0.0119 R, 1.2 % of a "
            "risk unit, at the flat band."),
        "evidence": {"artifact": REL(RC), "flat": sm,
                     "mid_all_eras": {k: mid.get(k) for k in
                                      ("pooled_oos_mean_r", "p_raw", "drop_best_retention",
                                       "oos_positive_fold_frac", "n_trades")},
                     "mid_recorded": {k: rec.get(k) for k in
                                      ("pooled_oos_mean_r", "p_raw", "drop_best_retention",
                                       "oos_positive_fold_frac", "n_trades")}},
        "appended_utc": NOW,
    })

    # ---------------------------------------------------------------- 4. the pair, and its bill
    comp = rc["composition_at_the_declared_family"]["arms"]
    key = ("btc=target_5R|xvol=target_4R+ac60>=median(0.0141)|band=mid|RECORDED")
    pair = comp.get(key) or {}
    cut = (rc["mechanism_cut_bill"]["rows"].get(
        "sub_xvol_pullback|ac60|target_4R|band=mid|RECORDED") or {})
    out.append({
        "session": "AO", "sleeve": "sub_xvol_pullback",
        "component": "docs/.../phase10/receipts/ao_regime_conditioning.py",
        "prescription": "CONDITIONED_PAIR_ADMITS_ON_A_POST_HOC_CUT_ONLY",
        "prescription_in_diagnostics_enum": "REGIME_GATE_OR_PARK",
        "verdict": "REJECT", "gate": "significance",
        "margin": (cut.get("best_p_raw") or 0) - 0.20 / 39, "is_primary": True,
        "action": (
            "Composed in ONE gate run at the declared 39, `sub_xvol_pullback @ target_4R` "
            "conditioned on `ac60 >= median` ADMITS at BH rank 2 alongside "
            f"`mx_btcusd @ target_5R`: {pair.get('admitted')}, xvol p "
            f"{(pair.get('rows') or {}).get('sub_xvol_pullback', {}).get('p_raw')}, R/day "
            f"{(pair.get('rows') or {}).get('sub_xvol_pullback', {}).get('pooled_oos_mean_r')}, "
            f"retention "
            f"{(pair.get('rows') or {}).get('sub_xvol_pullback', {}).get('drop_best_retention')} "
            "on n 44. THE CUT IS POST HOC and the admission does not survive its own search: at "
            "the same axis's MECHANISM cut -- `ac60 >= 0`, AB's own published `random` boundary "
            f"-- p is {cut.get('cells', {}).get('ac60>=0.0_AB_random_band_centre', {}).get('p_raw')}, "
            f"and Bonferroni-within-2-cut-rules gives {cut.get('bonferroni_within_cut_rules')} "
            f"against a rank-2 bar of {cut.get('rank_2_bar_at_declared_39')}. REPAIR, and it is "
            "one line of a future prompt: a prospective declaration of ONE cut on this axis, "
            "made before the arm is run, in a CANDIDATE_FAMILY successor. A cut chosen because "
            "it admitted cannot become prospective by being written down later, so the honest "
            "options are (a) declare the mechanism cut `ac60 >= 0` and accept p 0.0175, or (b) "
            "find held-out data. There is none: 88 trades is the whole archive."),
        "evidence": {
            "artifact": REL(RC), "pair_arm": key,
            "admitted": pair.get("admitted"),
            "admissible_in_this_session": pair.get("admissible_in_this_session"),
            "cut_bill": cut,
            "declared_cell_that_IS_admissible": {
                "cell": "rngpos==mid",
                "p_raw": arm("sub_xvol_pullback|target_4R|rngpos==mid|band=mid|RECORDED").get(
                    "p_raw"),
                "verdict": arm(
                    "sub_xvol_pullback|target_4R|rngpos==mid|band=mid|RECORDED").get("verdict"),
            },
        },
        "appended_utc": NOW,
    })

    # -------------------------------------------------- 4b. the GATE defect the pair exposed
    ra = rc["resolution_audit"]
    tightest = min(ra["arms_within_2x_of_their_floor"].items(),
                   key=lambda kv: kv[1]["p_floor_headroom"], default=(None, {}))
    out.append({
        "session": "AO", "sleeve": "__estate__",
        "component": "src/research_infra/walkforward/gate.py:851-857 significance gate",
        "prescription": "SIGNIFICANCE_PASSES_A_P_ONE_STEP_ABOVE_ITS_STRUCTURAL_FLOOR",
        "prescription_in_diagnostics_enum": "SAMPLE",
        "verdict": "INFORMATIONAL", "gate": "significance", "margin": None, "is_primary": True,
        "action": (
            "`stats.perm_p_floor` computes the smallest p a B-block sign flip can attain, "
            "`(1 + n_perm * 2**-B) / (n_perm + 1)`, and `gate.py:851-857` refuses ONLY when "
            "`p_raw <= p_floor`, setting `p_floor_binds`. A p one resolution step ABOVE the "
            "floor passes with no flag, and that is exactly the arm this session found "
            f"admitting: `{tightest[0]}` has p_raw {tightest[1].get('p_raw')} against a floor of "
            f"{tightest[1].get('p_floor')} -- headroom {tightest[1].get('p_floor_headroom')}x -- "
            f"on {tightest[1].get('n_oos_days')} OOS days and {tightest[1].get('n_blocks')} "
            "blocks, and the gate's own `p_floor_binds` reads "
            f"{tightest[1].get('p_floor_binds_per_gate')}. At 8 blocks the achievable p range "
            "below the rank-2 bar of 0.005128 is [0.004006, 0.005128] -- one resolution step "
            f"wide -- so an admission there is reachable only by hitting the floor. Of "
            f"{ra['n_arms_with_a_p']} arms with a p in this session, "
            f"{ra['n_arms_within_2x_of_their_floor']} sit within 2x of their own floor and the "
            "admitting one is the tightest. Every other arm's headroom runs 7x-659x. REPAIR: "
            "`significance` should carry `p_floor_headroom` and either fail or flag below a "
            "declared factor (2x is the natural first proposal, and it would have caught this "
            "arm and nothing else in the session). The mechanism is worth naming in the note "
            "too: a regime filter halves the OOS DAYS, days set the block count, and the floor "
            "is 2**-blocks -- so conditioning buys a smaller p by destroying the resolution "
            "that would justify it."),
        "evidence": {
            "artifact": REL(RC), "tightest_arm": tightest[0],
            "audit": {k: ra[k] for k in
                      ("n_arms_with_a_p", "n_arms_within_2x_of_their_floor",
                       "rank_2_bar_at_declared_39")},
            "arms_within_2x": ra["arms_within_2x_of_their_floor"],
            "comparators": {
                "xvol_ungated_target_4R_recorded_headroom": (
                    arm("sub_xvol_pullback|target_4R|ungated|band=mid|RECORDED"
                        ).get("p_floor_headroom")),
                "mx_btcusd_solo_headroom": (parm("solo_btc|target_5R|band=mid|RECORDED"
                                                 ).get("p_floor_headroom")),
                "sub_mid_dn_revert_flat_headroom": (
                    arm("sub_mid_dn_revert|as_walked|ungated|band=flat|ALL_ERAS"
                        ).get("p_floor_headroom")),
            },
        },
        "appended_utc": NOW,
    })

    # ---------------------------------------------------------------- 5. comp==coil by one trade
    coil = (rc["thin_cells_not_gateable"].get("sub_xvol_pullback|as_walked|comp==coil") or {})
    out.append({
        "session": "AO", "sleeve": "sub_xvol_pullback",
        "component": "src/research_infra/walkforward/options.py min_trades_total",
        "prescription": "PRE_DECLARED_CELL_MISSES_THE_FLOOR_BY_ONE_TRADE",
        "prescription_in_diagnostics_enum": "SAMPLE",
        "verdict": "NOT_EVALUABLE", "gate": "sample", "margin": None, "is_primary": False,
        "action": (
            "The mechanism's own pre-declared cell -- a pullback IS a range contraction inside "
            f"an expansion, so `comp == coil` -- holds {coil.get('n_in_cell')} of 88 trades, "
            "which is below every option's `min_trades_total` and therefore ungateable. Its raw "
            f"economics are the best of the three `comp` buckets: mean gross "
            f"{coil.get('mean_r_gross')} and mean net {coil.get('mean_r_net_at_mid_band_as_walked')} "
            f"on {coil.get('n_net_priced')} priced, against `comp == expand`'s "
            "+0.82878 gross / +0.69247 net on 16. So the pre-declared DIRECTION holds "
            "descriptively and cannot be tested. This is AF §8 item 2's case exactly -- an n "
            "floor excluding the mechanistically right bucket -- and the honest repair is NOT "
            "to lower the floor: it is more trades. The only source of more trades that does "
            "not relax the cell is more RECORDED-era surface, and AL measured that relaxing the "
            "cell costs more p than it buys."),
        "evidence": {"artifact": REL(RC), "cell": coil,
                     "comp_expand_comparator": (
                         rc["thin_cells_not_gateable"].get(
                             "sub_xvol_pullback|as_walked|comp==expand") or {})},
        "appended_utc": NOW,
    })

    # ---------------------------------------------------------------- 6. asia level refuted
    lv = rc["levels"]["asia_pdl_fade"]["fields"]["PERSISTENCE"]
    out.append({
        "session": "AO", "sleeve": "asia_pdl_fade",
        "component": "docs/.../phase8/receipts/ah_conditioning.py:90-95 PRE_DECLARED",
        "prescription": "REVERSAL_MECHANISM_WANTS_THE_OPPOSITE_TAPE",
        "prescription_in_diagnostics_enum": "MEMBER_CONDITIONING_NOT_BREADTH",
        "verdict": "REJECT", "gate": "expectancy", "margin": None, "is_primary": False,
        "action": (
            "AH's standing pre-declaration for a reversal mechanism -- 'it needs the exhaustion "
            "to revert, not to trend', hence `PERSISTENCE == revert` -- is REFUTED for this "
            f"sleeve, in the opposite direction, on {lv['n']} priced trades: Spearman rho "
            f"{lv['rho']} against a pre-declared {lv['pre_declared_sign']}, permutation p "
            f"{lv['p_two_sided_permutation']}, and the tertile means run "
            f"{lv['tertile_mean_net_r']} -- the MOST trending third is the least bad. The "
            "bucket gate agrees: the pre-declared cell is worse than ungated at every band. "
            "REPAIR: the mechanism reading that survives is that a prior-day-low sweep in a "
            "mean-reverting tape is a real break rather than a stop-run, so the sleeve wants "
            "the tape to be CONTINUING when it fades -- which inverts AH's precedent for "
            "liquidity-sweep reversals specifically and should be pre-declared that way next "
            "time rather than inherited. Note the whole surface is deeply negative at the "
            "banded cost (see the EXIT_FRONTIER_IS_AT_THE_FLAT_SNAPSHOT_ONLY row), so this is "
            "a direction correction inside a sleeve whose economics are the primary blocker."),
        "evidence": {"artifact": REL(RC), "level": lv,
                     "ah_precedent": "ah_conditioning.py:93-95 volume_surge_reversal"},
        "appended_utc": NOW,
    })

    # ---------------------------------------------------------------- 7. the vol level, at sizing
    vr = rc["levels"]["sub_xvol_pullback"]["fields"]["vr"]
    out.append({
        "session": "AO", "sleeve": "sub_xvol_pullback",
        "component": "src/components/ultimate_book/admission.py conviction weight",
        "prescription": "VOL_LEVEL_IS_A_SIZING_DIAL_NOT_AN_ADMISSION_FILTER",
        "prescription_in_diagnostics_enum": "REGIME_GATE_OR_PARK",
        "verdict": "REJECT", "gate": "significance", "margin": None, "is_primary": False,
        "action": (
            "Inside the pinned `vol=xhi` bucket the vol LEVEL is strongly monotone in net R per "
            f"trade, in the direction pre-declared before any number: rho {vr['rho']} on "
            f"{vr['n']} priced trades, permutation p {vr['p_two_sided_permutation']}, tertile "
            f"means {vr['tertile_mean_net_r']} -- a {round(vr['tertile_mean_net_r']['T3_high'] / vr['tertile_mean_net_r']['T1_low'], 2)}x "
            "spread from the calmest to the most expanded third of the sleeve's own firing "
            "range. It is the session's strongest regime finding and it is NOT usable as an "
            "admission filter: the cell `vr >= median` is NOT_EVALUABLE at n 44 (vol expansions "
            "cluster in calendar time, so the split concentrates trades into fewer folds) and "
            "`vr >= 2.0`, AB's own published `xhi` value, holds 18 of 88. REPAIR: route it at "
            "SIZING. The runtime already has the consumer -- `admission.py`'s Kelly-lite "
            "conviction multiplier -- and a level tilt costs no sample, so it is the one form "
            "of conditioning this sleeve can carry. Note the contrast with the same sleeve's "
            "`ac60` axis, whose rho is ~0 but whose median split moves the DAY-level statistic: "
            "a per-trade rank correlation and a per-day null are different instruments and this "
            "sleeve separates them."),
        "evidence": {"artifact": REL(RC), "level": vr,
                     "ac60_contrast": rc["levels"]["sub_xvol_pullback"]["fields"]["ac60"],
                     "vr_median_cell_not_evaluable": arm(
                         "sub_xvol_pullback|target_4R|vr>=median(1.8381)|band=mid|RECORDED"
                     ).get("verdict"),
                     "vr_ge_2_n": (rc["thin_cells_not_gateable"].get(
                         "sub_xvol_pullback|as_walked|vr>=2.0_AB_published_xhi_band") or {}
                     ).get("n_in_cell")},
        "appended_utc": NOW,
    })

    # ---------------------------------------------------------------- 8. the coverage attribution
    cov = rc["coverage_attribution"]["sub_xvol_pullback"]
    out.append({
        "session": "AO", "sleeve": "sub_xvol_pullback",
        "component": "src/costs/spread_model.py era band + the bar archive",
        "prescription": "DECIDABILITY_LOSS_ATTRIBUTED_TO_ITS_ERA_TERMS",
        "prescription_in_diagnostics_enum": "COVERAGE_OR_SAMPLE_BEFORE_EXIT",
        "verdict": "NOT_EVALUABLE", "gate": "sample", "margin": None, "is_primary": False,
        "action": (
            "AL §4 measured the armed sleeve at n 56 on DECIDABLE against 85 on RECORDED and "
            "asked whether the loss is recoverable. Answered from the era ledger's own variance "
            f"decomposition: {cov['n_recorded_but_undecidable']} of {cov['n_trades_total']} "
            f"trades sit in {cov['n_eras']} eras the model calls RECORDED but UNDECIDABLE, and "
            f"the dominant width term names the repair: {cov['trades_by_repair_class']}. So the "
            "loss is not 'no data' -- the model DID derive an era ratio from bar history -- it "
            "is 'data that disagrees with itself', and the majority term is D1-vs-H4 "
            "disagreement, which is a MODEL repair (AG's timeframe reconciliation) rather than "
            "a capture requirement. REPAIR: reconcile the two timeframe references for these "
            "eras and the sleeve's DECIDABLE n rises without any new tick capture. The other "
            "half of the same fact is AL's unwired hole: an undecidable RECORDED era degrades "
            "`Coverage` not at all (`spread_model.py:440-441`), so these trades price as "
            "MEASURED today."),
        "evidence": {"artifact": REL(RC), "attribution": cov,
                     "same_measurement_on_the_other_two_sleeves": {
                         s: rc["coverage_attribution"][s]["trades_by_repair_class"]
                         for s in ("sub_mid_dn_revert", "asia_pdl_fade")}},
        "appended_utc": NOW,
    })

    # ---------------------------------------------------------------- 9. the pool
    solo = parm("solo_btc|target_5R|band=mid|RECORDED")
    p9 = parm("pool_all9|target_5R|band=mid|RECORDED")
    p100 = parm("pool_n_ge_100|target_5R|band=mid|RECORDED")
    pcoh = parm("pool_coherent_positive|target_5R|band=mid|RECORDED")
    out.append({
        "session": "AO", "sleeve": "mx_btcusd_d1_donchian_20_breakout",
        "component": "docs/.../phase10/receipts/ao_btc_power_pool.py",
        "prescription": "POOLING_FOR_POWER_REFUTED_THE_DAYS_DO_NOT_GROW",
        "prescription_in_diagnostics_enum": "SAMPLE_EXTENSION",
        "verdict": "REJECT", "gate": "significance", "margin": None, "is_primary": True,
        "action": (
            "AL §10 item 1's pooling-for-power question, run. It does not work, and the "
            "mechanism is measured rather than inferred: the null is a block sign-flip on the "
            f"daily OOS series, so DAYS buy resolution and trades do not. Solo n "
            f"{solo.get('n_trades')} / {solo.get('n_oos_days')} days / "
            f"{solo.get('n_blocks')} blocks at p {solo.get('p_raw')} ADMITS; all nine pooled is "
            f"n {p9.get('n_trades')} ({round(p9.get('n_trades', 0) / max(1, solo.get('n_trades', 1)), 2)}x) "
            f"on only {p9.get('n_oos_days')} days "
            f"({round(p9.get('n_oos_days', 0) / max(1, solo.get('n_oos_days', 1)), 2)}x) -- a "
            "donchian-20 breakout is a common-factor event and the crypto members fire on "
            f"overlapping days -- while R/day falls {solo.get('pooled_oos_mean_r')} -> "
            f"{p9.get('pooled_oos_mean_r')}. Net: p {p9.get('p_raw')}, "
            f"{round((p9.get('p_raw') or 1) / (solo.get('p_raw') or 1), 1)}x WORSE. The same "
            "arithmetic AL §2 measured on the threshold variant. And the outcome-independent "
            f"n>=100 pool ({p100.get('p_raw')}) beats the coherent-positive pool that SELECTS "
            f"on the outcome ({pcoh.get('p_raw')}), reproducing AH §4.2's -0.004525 R/trade on "
            "a family AH did not cover. REPAIR: the solo cell's sample cannot be extended by "
            "breadth. What is left for it is (a) the population rule, which AN owns and which "
            "moves its p by 53x, and (b) more BTCUSD history -- the archive starts 2017-08, so "
            "this is a capture requirement with an exact address."),
        "evidence": {
            "artifact": REL(PP),
            "power_accounting": (pp["power_accounting"]["rows"].get(
                "target_5R|band=mid|RECORDED") or {}),
            "band_fragility": pp["band_fragility_the_commission_asked_about"]["rows"],
            "member_two_clause_test": pp["member_basis"]["two_clause_test"],
            "controls": pp["controls"],
        },
        "appended_utc": NOW,
    })

    # ---------------------------------------------------------------- 10. the bill
    fm = json.loads(FAM.read_text())["families"]["CANDIDATE_BOOK_V1"]
    out.append({
        "session": "AO", "sleeve": "CANDIDATE_BOOK_V1",
        "component": "docs/.../phase10/receipts/CANDIDATE_FAMILY_V3.json",
        "prescription": "MULTIPLICITY_BILL_DECLARED",
        "verdict": "INFORMATIONAL", "gate": "", "margin": None, "is_primary": False,
        "action": (
            f"CANDIDATE_BOOK_V1 raised {fm['high_water_size'] - 4} -> {fm['high_water_size']} "
            f"declared and {fm['high_water_looks'] - 4} -> {fm['high_water_looks']} looks taken "
            "by Session AO's three pre-declared regime-conditioning cells plus the power pool. "
            "A regime gate moves which trades exist, so each cell is a distinct hypothesis "
            "under AL §6.3's rule; the pool is nine members judged as one series, which is "
            "neither any member nor the parent. Rank 1 at alpha 0.10 tightens 0.002857 -> "
            "0.002564. `mx_btcusd @ target_5R` still admits at p 0.0011, consuming 4 of the 55 "
            "BH slots and 4 of the 10 Bonferroni slots AL §8.7 measured as its headroom. The "
            "ENUMERATED cells are NOT declared and are priced by a within-enumeration "
            "Bonferroni; `REGIME_CONDITIONING_V1.json.enumeration_bills` prints the count and "
            "the largest admitting family for each so a reader who rejects that split can "
            "re-price without re-running."),
        "evidence": {
            "artifact": REL(FAM), "members_added": [m["name"] for m in fm["members"][-4:]],
            "all_declared": fm["high_water_size"], "looks_taken": fm["high_water_looks"],
            "enumeration_bills": json.loads(RC.read_text())["enumeration_bills"],
        },
        "appended_utc": NOW,
    })
    return out


def main() -> int:
    new = rows()
    existing = [json.loads(l) for l in QUEUE.read_text().splitlines() if l.strip()]
    seen = {(r.get("session"), r.get("sleeve"), r.get("prescription")) for r in existing}
    todo = [r for r in new
            if (r["session"], r["sleeve"], r["prescription"]) not in seen]
    skipped = len(new) - len(todo)
    with QUEUE.open("a") as fh:
        for r in todo:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    after = [json.loads(l) for l in QUEUE.read_text().splitlines() if l.strip()]
    print(f"appended {len(todo)}, skipped {skipped} already present; "
          f"{len(existing)} -> {len(after)} rows")
    # Duplicate control (AK §7.7's double-append), scoped to AO'S OWN rows.
    #
    # The first version checked the WHOLE ledger and refused, which was wrong twice over: it
    # would have failed on other sessions' rows, and (session, sleeve, prescription) is not a
    # unique key in this ledger by design -- AD legitimately files the same prescription for one
    # sleeve at two accounts or two cells. The invariant AO can own is that AO does not
    # double-append; the pre-existing collisions are REPORTED so the observation is not lost.
    keys = [(r.get("session"), r.get("sleeve"), r.get("prescription")) for r in after]
    ao_keys = [k for k in keys if k[0] == "AO"]
    ao_dupes = sorted({k for k in ao_keys if ao_keys.count(k) > 1})
    pre_dupes = sorted({k for k in keys if k[0] != "AO" and keys.count(k) > 1})
    print(f"AO duplicate triples: {ao_dupes or 'none'}")
    print(f"pre-existing duplicate triples from other sessions "
          f"({len(pre_dupes)}, reported not failed): {pre_dupes}")
    ao = [r for r in after if r["session"] == "AO"]
    print(f"AO rows: {len(ao)}; primary: {sum(1 for r in ao if r['is_primary'])}")
    for r in ao:
        print(f"  {r['sleeve']:36s} {r['prescription']}")
    if ao_dupes:
        raise SystemExit(f"REFUSING: AO double-appended {ao_dupes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
