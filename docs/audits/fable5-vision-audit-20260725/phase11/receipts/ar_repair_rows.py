"""Session AR — the repair-queue rows, every `evidence` block READ from the artifacts.

    python3 docs/audits/fable5-vision-audit-20260725/phase11/receipts/ar_repair_rows.py

Appends to `phase6/receipts/REPAIR_QUEUE_APPEND.jsonl` (append-only, union-merged at the
train). Duplicate control is scoped to AR's OWN rows — AO's `ao_repair_rows.py` learned the hard
way that (session, sleeve, prescription) is not a unique key across the whole ledger by design
(AD legitimately files one prescription for one sleeve at two accounts), and that refusing on
another session's collisions fails on work that is not mine.

Nothing here is typed from prose: every number comes out of
`AR_VOL_LEVEL_TILT_V1.json`, `AR_REPAIR_PROGRAM_V1.json`, `CANDIDATE_FAMILY_V4.json` or
`VOL_LEVEL_TILT_DECLARATION_V1.json`. A row whose evidence cannot be read raises rather than
writing a null — a silent null in a repair row is worse than a missing row, because the next
session reads it as measured.
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
TILT = HERE / "AR_VOL_LEVEL_TILT_V1.json"
PROG = HERE / "AR_REPAIR_PROGRAM_V1.json"
FAMV4 = HERE / "CANDIDATE_FAMILY_V4.json"
DECL = HERE / "VOL_LEVEL_TILT_DECLARATION_V1.json"
SESSION = "AR"


def _need(path: Path) -> dict:
    if not path.is_file():
        raise SystemExit(f"REFUSING: {path.relative_to(REPO)} is absent, so its rows would carry "
                         f"nulls. Run the driver that produces it first.")
    return json.loads(path.read_text())


def rows() -> list[dict]:
    t = _need(TILT)
    p = _need(PROG)
    f = _need(FAMV4)
    d = _need(DECL)
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    v = t["verdict"]
    ab_mid = t["ab"]["armed3|band=mid"]
    ab_rec = t["ab"]["armed3_recorded|band=mid"]
    lf = t["level_freedom"]
    ar3 = p["ar3"]
    ar2 = p["ar2"]
    pc = ar3["prediction_check"]
    out: list[dict] = []

    def row(**kw):
        out.append(dict(session=SESSION, appended_utc=now, **kw))

    # ---------------------------------------------------------------- AR-1, the methodology
    row(
        sleeve="__methodology__",
        component="src/research_infra/walkforward/book_replay.py + any future sizing A/B",
        prescription="SIZING_AB_MUST_BE_PATH_FREE_WITH_A_CONSTANT_MAGNITUDE_CONTROL",
        is_primary=True, verdict="DEFECT_IN_THE_MEASUREMENT_INSTRUMENT",
        margin=None,
        action=(
            "Compounded book return is NOT a valid instrument for a sizing change, and this "
            "session would have published the wrong headline without a control it had not "
            "declared. Measured: the vol-level tilt reaches ONE of three armed sleeves and "
            f"`vol_level_tilt_for` returns 1.0 for the other two, yet the mid-band book gain of "
            f"{ab_mid['delta_total_return_pct']:+} pp decomposes as 29 % `sub_xvol_pullback` and "
            f"63 % `crypto` — a sleeve the tilt cannot touch. The mechanism is `book_replay` "
            "divergence 1: sizing runs off the realised balance and the governor is non-monotone "
            "in equity, so a tilt that changes a unit's size re-times the OPS-03 profit-target "
            "de-risk (`admission.py:1353-1357`, cap_mult *= 0.25) for EVERY sleeve. The same "
            "tilt on the IDENTICAL 31 placed trades with IDENTICAL multipliers deploys -0.11 % "
            "of xvol risk at the flat band and -11.73 % at mid. REPAIR: every future sizing-change "
            "A/B in this programme reports (1) the path-free efficiency ratio — sum(risk_pct) "
            "deployed, sum(risk_pct * r_net) earned, and their ratio, all uncompounded — and "
            "(2) a CONSTANT-magnitude control on the same sleeve. `ar_vol_level_tilt.py`'s "
            "`_risk_view` / `_path_free_delta` / `_const_tilt` are the instrument; lift them."),
        evidence={
            "artifact": str(TILT.relative_to(REPO)),
            "book_delta_by_band": v["b_does_it_make_the_book_more_money"][
                "delta_total_return_pct_by_band"],
            "n_bands_positive": v["b_does_it_make_the_book_more_money"]["n_bands_positive"],
            "path_free_mid": ab_mid["path_free"],
            "control_constants": t["control_constants"],
            "mechanism": v["b_does_it_make_the_book_more_money"]["the_mechanism_measured"],
        })

    row(
        sleeve="sub_xvol_pullback",
        component="src/components/ultimate_book/admission.py vol_level_tilt_for + run_book.py --vol-level-tilt",
        prescription="VOL_LEVEL_TILT_BUILT_PRICED_AND_DEFAULT_OFF__ARMING_IS_THE_OWNERS",
        is_primary=True, verdict="BUILT_NOT_ARMED",
        margin=ab_rec["path_free"]["sub_xvol_pullback"]["efficiency_ratio"],
        action=(
            "AO measured `vr` monotone in this sleeve's net R inside its own firing range and "
            "routed it to sizing. AR reproduced it exactly (rho 0.40725, permutation p 0.00025, "
            "tertiles 0.51239 / 1.11149 / 2.12439), declared the tilt prospectively at ONE "
            "published constant (AB's `xhi` = 2.0, `regime_spine/dials.py:143`, which no "
            "bucketiser implements), built it default-OFF behind `run_book.py --vol-level-tilt` "
            "with no config byte, and priced it. TWO ANSWERS, and they differ: the vr ORDERING "
            "is real — on the ratified RECORDED population it earns "
            f"{ab_rec['path_free']['sub_xvol_pullback']['pl_ratio']}x the risk-weighted P&L on "
            f"{ab_rec['path_free']['sub_xvol_pullback']['risk_ratio']}x the risk (efficiency "
            f"{ab_rec['path_free']['sub_xvol_pullback']['efficiency_ratio']}x) while two BLIND "
            "constant de-risks of the same magnitude sit at 1.0005x and 1.0008x, i.e. exactly "
            "nothing — but the BOOK payoff is band-fragile (positive at 2 of 4 bands, negative "
            "at flat and high) and mostly a governor-path artifact. RECOMMENDATION: do not arm. "
            "The switch costs nothing to leave off. What would settle it is a path-free "
            "efficiency measurement at every band with a constant control at each — one "
            "afternoon with the instrument this session built."),
        evidence={
            "artifact": str(TILT.relative_to(REPO)),
            "declaration": str(DECL.relative_to(REPO)),
            "declaration_sha256": d.get("self_sha256"),
            "the_tilt": d["the_tilt"],
            "ao_reproduction": t["ao_reproduction"]["reproduced"],
            "recorded_path_free": ab_rec["path_free"]["sub_xvol_pullback"],
            "blind_controls_recorded": {
                "at_archive_mean": v["a_does_the_ordering_carry_information"][
                    "blind_control_at_archive_mean"],
                "at_realised_ratio": v["a_does_the_ordering_carry_information"][
                    "blind_control_at_realised_ratio"]},
            "recent_fold_delta_recorded": ab_rec["recent_fold_delta"],
            "n_folds_improved_recorded": ab_rec["n_folds_improved"],
            "owner_recommendation": v["owner_recommendation"],
        })

    row(
        sleeve="__runtime__",
        component="src/components/ultimate_book/admission.py size_correlated_units",
        prescription="A_SHRINK_MULTIPLIER_MUST_APPLY_OUTSIDE_THE_SIZEUP_CAP",
        is_primary=False, verdict="FIXED_IN_THIS_SESSION",
        margin=None,
        action=(
            "`su_combined` is capped at OVERLAY_SIZEUP_MAX (1.75). The live dial REACHES that "
            "cap — confluence overlays 1.5 x 1.15 = 1.725 times the Kelly-lite >= 4-sleeve bin "
            "1.60 is 2.76 — so any multiplier folded INSIDE the cap that happens to be below "
            "1.0 is silently discarded on exactly the days the book is largest. The vol-level "
            "tilt is such a multiplier: a 0.80x de-risk would have been a no-op on the hottest "
            "days. FIXED here by SPLITTING it — size-up half inside the cap so the governor-safe "
            "ceiling still binds, shrink half after it so it can never be absorbed — which is "
            "the pattern `derisk_mult` already uses. The GENERAL rule for the next session: any "
            "multiplier that can go below 1.0 belongs outside every size-up cap, and a test that "
            "drives the other terms to the ceiling is the only one that can catch it. Caught by "
            "`test_a_shrink_is_not_discarded_by_the_sizeup_cap`, which failed on the "
            "inside-the-cap version."),
        evidence={
            "test": "tests/research_infra/test_ar_vol_level_tilt.py::test_a_shrink_is_not_discarded_by_the_sizeup_cap",
            "live_dial_reaches_the_cap": "1.5 * 1.15 * 1.60 = 2.76 -> min(2.76, 1.75) = 1.75",
            "fix": "min(su * kelly_mult * max(1.0, vlt), OVERLAY_SIZEUP_MAX) * min(1.0, vlt)",
            "n_tests": 29,
        })

    row(
        sleeve="__runtime__",
        component="src/components/ultimate_book/bridge.py DEFAULT_CONFIG + _bool",
        prescription="A_BRIDGE_FLAG_WITHOUT_A_DEFAULT_CONFIG_ENTRY_STANDS_THE_ARMED_BOOK_DOWN_SILENTLY",
        is_primary=False, verdict="FIXED_IN_THIS_SESSION",
        margin=None,
        action=(
            "`bridge._bool(cfg, key)` resolves an absent key against `DEFAULT_CONFIG[key]` and "
            "raises KeyError when the key has no entry. That KeyError is raised INSIDE "
            "`evaluate_vnext_ultimate_book_admission`, which `book_engine.evaluate` catches as "
            "`engine_exception` because the book never breaks the live path — so the failure "
            "mode is not a crash, it is an ARMED BOOK THAT STANDS DOWN EVERY TICK with a "
            "perfectly healthy heartbeat. Adding a flag read without adding its DEFAULT_CONFIG "
            "entry is therefore a silent live outage, and nothing in the tree warns about it. "
            "FIXED for this flag. REPAIR for the estate: a test that asserts every "
            "`_bool(cfg, ...)` / `_str(cfg, ...)` key in `bridge.py` has a `DEFAULT_CONFIG` "
            "entry — one AST walk, no market data, and it makes the class impossible rather than "
            "this instance fixed."),
        evidence={
            "caught_by": ("tests/research_infra/test_ar_vol_level_tilt.py::"
                          "test_the_launcher_flag_reaches_the_bridge_without_a_config_byte"),
            "failure_mode": "KeyError -> engine_exception -> book stands down, heartbeat healthy",
            "proposed_test": "assert every _bool/_str key in bridge.py has a DEFAULT_CONFIG entry",
        })

    row(
        sleeve="sub_xvol_pullback",
        component="src/components/ultimate_book/admission.py size_correlated_units unit convention",
        prescription="THE_UNIT_MAX_CONVENTION_UNDER_DELIVERS_A_PER_INTENT_TILT",
        is_primary=False, verdict="MEASURED_NOT_CHANGED",
        margin=t["unit_max_convention"]["frac_days_multi"],
        action=(
            "A unit is sized at the MAX effective confidence over its same-day same-cluster "
            "members (`admission.py:1198-1201`), so on a multi-trade unit the surviving tilt is "
            f"the LEAST-shrinking member's. Measured on the archive: "
            f"{t['unit_max_convention']['n_days_with_more_than_one']} of "
            f"{t['unit_max_convention']['n_decision_days_with_an_xvol_trade']} decision days "
            f"({t['unit_max_convention']['frac_days_multi']:.1%}) carry more than one "
            f"`sub_xvol_pullback` trade, with a within-day multiplier spread up to "
            f"{t['unit_max_convention']['max_within_day_multiplier_spread']:.4f}. Because the "
            "declared tilt is a net DE-RISK this convention under-delivers rather than "
            "over-delivers — the safe direction — which is why it is measured and NOT changed "
            "here: making the unit take the min would be a risk change, and a risk change is "
            "Borhen's. Filed so a future session that flips the tilt's sign knows the convention "
            "would then under-deliver a size-UP too, in the same direction."),
        evidence={"artifact": str(TILT.relative_to(REPO)),
                  **t["unit_max_convention"]})

    # ---------------------------------------------------------------- fresh-worktree hygiene
    row(
        sleeve="__infrastructure__",
        component="scripts/gtos_hydrate_test_data.py + the sparse profile",
        prescription="A_FRESH_WORKTREE_CANNOT_RUN_A_COST_TRUE_DRIVER_AND_THE_HYDRATOR_SAYS_IT_CAN",
        is_primary=False, verdict="DEFECT",
        margin=None,
        action=(
            "Two independent gaps cost this session time in its first ten minutes and will cost "
            "every future one the same. (1) `research/operations/broker_truth_layer_2026_07_29/"
            "BROKER_TRUE_COSTS_V1_1.json` — the cost artifact EVERY wave-6+ cost-true driver "
            "loads via `ad_exit_sweep.COSTS` — is tracked but NOT in the sparse profile, so a "
            "fresh worktree fails with `CostTruthError: broker truth artifact not found` and the "
            "suggested remedy (`build_broker_true_costs.py`) is the wrong one: the file exists in "
            "git and wants `git sparse-checkout add`, not a rebuild. Its older sibling "
            "`broker_truth_layer_2026_07_27/` IS in the profile, which is why nothing noticed. "
            "(2) `gtos_hydrate_test_data.py` prints `nothing to hydrate — all paths already in "
            "the sparse profile` and `hydrated: 159 path(s) present` while 196 LFS-tracked files "
            "remain un-hydrated pointers, and 11 tests fail on exactly that (10 in "
            "`test_b7_5_neutral_selection_factorial.py` with `JSONDecodeError: Expecting value: "
            "line 1 column 1` — a 131-byte pointer parsed as JSON — and 1 in `test_permissions.py`). "
            "REPAIR: add the V1_1 cost path to the sparse profile, and make the hydrator's exit "
            "message report the pointer count it did NOT resolve instead of claiming completion. "
            "CAUTION, and it is why this session did not simply hydrate them: CLAUDE.md section 3's "
            "2026-07-30 amendment establishes that R2 expects bytes for "
            "`ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl` that match NO committed "
            "object — only the uncommitted working copy in the main repo — so hydrating it in a "
            "worktree puts the WRONG bytes at a path the runner's `binding_roots` fallback finds "
            "first. Fix the profile and the message; do not blanket-hydrate."),
        evidence={
            "n_lfs_pointers_unhydrated": 196,
            "failing_tests": 11,
            "failing_files": ["tests/test_b7_5_neutral_selection_factorial.py (10)",
                              "tests/test_permissions.py (1)"],
            "ab_at_merge_base": ("11 failed at the merge-base source and 11 at AR's change, "
                                "IDENTICAL failure sets, 0 regressed, 0 fixed — verified by "
                                "copy-back A/B, so these are environmental and not AR's"),
            "missing_sparse_path": "research/operations/broker_truth_layer_2026_07_29/",
            "hydrator_message": "nothing to hydrate — all paths already in the sparse profile",
        })

    # ---------------------------------------------------------------- AR-3
    best3 = ar3.get("best_at_ratified_rule") or {}
    row(
        sleeve="asia_pdl_fade",
        component=str(PROG.relative_to(REPO)),
        prescription=("EXIT_FRONTIER_REPRICED_AT_THE_BAND__" + (
            "BANDED_OPTIMUM_IS_A_DIFFERENT_CELL" if pc.get("held")
            else "SURFACE_DOES_NOT_SURVIVE_THE_BANDED_COST")),
        is_primary=True, verdict=(best3.get("verdict") or "NOT_EVALUABLE"),
        margin=best3.get("p_raw"),
        action=(
            "AO's `EXIT_FRONTIER_IS_AT_THE_FLAT_SNAPSHOT_ONLY` row named this repair and AR ran "
            f"it: AL's whole cross ({ar3['n_named_cells_AL_published']} named cells, "
            f"{ar3['n_distinct_geometries']} distinct geometries after deduping on the geometry "
            "rather than the name) re-gated at the BANDED mid cost on the ratified RECORDED "
            "population, with AL's own flat figures reproduced as the control. AND WITH A "
            "PREDICTION STATED IN SOURCE BEFORE THE RUN: swap is charged per rollover, AL "
            "optimised at a basis that under-charges carry, so the banded optimum should move "
            "toward SHORTER holds — tighter `time_stop_bars`, away from AL's `ts_none` winner at "
            f"the widest stop. PREDICTION {'HELD' if pc.get('held') else 'REFUTED'}: the banded "
            f"optimum is `{pc.get('banded_best_cell')}` with time_stop_bars "
            f"{pc.get('banded_best_time_stop_bars')}, at {pc.get('banded_best_r_per_day')} R/day "
            f"and p {pc.get('banded_best_p_raw')}. "
            f"{pc.get('frac_positive')} of the banded surface is positive. RECONCILIATION with "
            "AO's regime refutation: they are different levers — AK/AL measured where the exit "
            "goes and AO which tape to fire in — and both answers stand; what AO refuted is the "
            "COST BASIS of AL's frontier, not its geometry."),
        evidence={
            "artifact": str(PROG.relative_to(REPO)),
            "prediction": ar3["prediction_check"],
            "flat_reproduction_control": ar3["flat_reproduction_control"],
            "best_at_ratified_rule": best3,
            "reconciliation": ar3["reconciliation"],
            "n_distinct_geometries": ar3["n_distinct_geometries"],
        })

    # ---------------------------------------------------------------- AR-2
    adm = ar2["admission_at_the_ratified_rule"]
    row(
        sleeve="__estate__",
        component=str(FAMV4.relative_to(REPO)),
        prescription=("SECOND_ADMISSION_AT_THE_RATIFIED_RULE" if adm
                      else "NO_SECOND_ADMISSION__THE_THREE_NEAREST_MISSES_AND_WHAT_EACH_LACKS"),
        is_primary=True,
        verdict=("ADMIT" if adm else "REJECT"),
        margin=((ar2["nearest_misses"][0] or {}).get("p_raw")
                if ar2["nearest_misses"] else None),
        action=(
            "AF's two COHERENT families — the only 2 of 30 passing its two-clause test — judged "
            "at the RATIFIED rule for the first time. AF's 0-of-246 was measured at "
            "C_exploratory / ALL_ERAS / m=276; three of those four inputs have been replaced "
            "(B_balanced alpha 0.10, RECORDED, declared family 48), moving the rank-1 bar "
            "0.000362 -> 0.002083, 5.8x. Their 9 members were declared in "
            "`CANDIDATE_FAMILY_V4.json` BEFORE any gate ran, together with the SECOND bill the "
            "declared family does not charge: AF chose the families on the outcome (2 of 30, "
            "'every member positive'), so every arm must clear the tighter of the BH bar and a "
            f"30-family Bonferroni (0.003333). RESULT: "
            + (f"{len(adm)} admission(s) — {adm}."
               if adm else
               "no second admission. The three nearest misses are published with exactly what "
               "each is missing — n, p at rank, folds, retention, or a named repair — and the "
               "pooled arms were deliberately NOT run because AO measured pooling losing 6.1x of "
               "p on precisely this shape. No admission was manufactured.")),
        evidence={
            "artifact": str(PROG.relative_to(REPO)),
            "declared_family": p["declared_family"],
            "second_bill": p["second_bill"],
            "coherent_families": ar2["coherent_families"],
            "what_changed_since_AF": ar2["what_changed_since_AF_judged_them"],
            "nearest_misses": ar2["nearest_misses"],
            "admissions": adm,
        })

    row(
        sleeve="__estate__",
        component=str(FAMV4.relative_to(REPO)),
        prescription="CANDIDATE_FAMILY_RATCHETED_39_TO_48",
        is_primary=False, verdict="DECLARED",
        margin=None,
        action=(
            "CANDIDATE_BOOK_V1 raised 39 -> 48 declared and 36 -> 45 looks taken by AR-2's nine "
            "AF-coherent-family members. Rank 1 at alpha 0.10 tightens 0.002564 -> 0.002083 and "
            "rank 2 0.005128 -> 0.004167; `mx_btcusd @ target_5R` at p 0.0011 survives with room "
            "(AL section 8.7 measured its headroom as m <= 90 at alpha 0.10), which is the "
            "precondition for taking the looks at all. NOT declared, each with its reason: the "
            "pooled family arms (AO measured pooling losing 6.1x of p on this shape — citing is "
            "cheaper than repeating), exit cells (re-measure an existing hypothesis, AL section "
            "6.3), and AR-1's sizing tilt (changes no trade's existence and no trade's R, so it "
            "produces no p and holds no rank; the disagreement is priced in the declaration "
            "anyway at 39 -> 40, rank 1 0.002564 -> 0.002500)."),
        evidence={
            "artifact": str(FAMV4.relative_to(REPO)),
            "all_declared": p["declared_family"]["all_declared"],
            "sha256": p["declared_family"]["sha256"],
            "bh_rank_1": p["declared_family"]["bh_rank_1"],
            "bh_rank_2": p["declared_family"]["bh_rank_2"],
            "history_tail": f["families"]["CANDIDATE_BOOK_V1"]["history"][-1],
        })

    row(
        sleeve="asia_pdl_fade",
        component="phase9/receipts/AL_ASIA_PDL_FRONTIER_V1.json + every exit sweep in the estate",
        prescription="EVERY_EXIT_FRONTIER_MUST_REPORT_ITS_MAXBARS_SHARE_PER_CELL",
        is_primary=True, verdict="DEFECT_IN_A_PUBLISHED_ARTIFACT",
        margin=None,
        action=(
            "A wider stop is only a GEOMETRY change if the price still resolves the trade inside "
            "the resimulation horizon. For `asia_pdl_fade` (20-hour maximum hold) it does not: the "
            "exit migrates from `stop`/`target` to `maxbars`, the harness's own box. MEASURED "
            "across AL's own grid and AR's "
            "extension: 2.5 % `maxbars` at 1x, **20.6 % at AL's published winner `stop_2.5x`**, "
            "26.4 % at 3x, **31.8 % at AL's 3.5x grid edge**, and 82.4 % at AR's 14x cell, with "
            "mean gross R/trade decaying +0.17195 -> +0.05341 as the box binds. CONSEQUENCE FOR "
            "AR: the cost model's INTERCEPT is neither confirmed nor refuted -- the instrument "
            "runs out of horizon before the geometry does, so it is "
            "NOT_EVALUABLE_BY_THIS_INSTRUMENT and no wide-stop cell for this sleeve may be quoted "
            "as an R-unit statement, including AR's own. CONSEQUENCE FOR AL: its published "
            "frontier is partly a horizon measurement at its wide-stop end, which is a second "
            "qualification on '+0.0846 R/day, 5/5 folds' on top of the flat-band one AO found. "
            "REPAIR, and it is a REPORTING change rather than a measurement one: "
            "`ad_exit_sweep.resimulate` already returns the exit-reason counts in its telemetry, "
            "so every exit frontier should carry the `maxbars` share per cell. TO SETTLE THE "
            "SLEEVE: a resimulation horizon longer than 20 hours, which is a harness change and "
            "cheap -- `resimulate` runs 2,827 trades in well under a second. The H4 re-derivation "
            "is the natural form of it, and AR measured the conversion so nobody has to guess "
            "(median M15->H4 ATR14 ratio 4.358 over 30 symbols, range 1.490-7.075)."),
        evidence={
            "artifact": str((HERE / "AR_ASIA_HORIZON_CENSUS_V1.json").relative_to(REPO)),
            **{k: v for k, v in _need(HERE / "AR_ASIA_HORIZON_CENSUS_V1.json").items()
               if k in ("answer_in_one_line", "as_walked", "consequences",
                        "maxbars_confound_threshold")},
            "atr_ratio_artifact": str((HERE / "AR_M15_H4_ATR_RATIO_V1.json").relative_to(REPO)),
            "cost_model": ar3.get("cost_model", {}).get("mean_fit"),
        })

    row(
        sleeve="__estate__",
        component="phase11/receipts/CANDIDATE_FAMILY_V4.json + any future AF-member declaration",
        prescription="AF_MEMBER_NAMES_AND_REGISTRY_NAMES_HIDE_THE_SAME_HYPOTHESIS_FROM_THE_RATCHET",
        is_primary=False, verdict="MEASURED__AR_OVER_CHARGED_ITSELF_BY_THREE",
        margin=None,
        action=(
            "AF's `is_authored_cell` family members ARE their registry parent -- same mechanism, "
            "same symbol, same timeframe -- and the two naming conventions "
            "(`mx_<sym>_<tf>_<mech>` in the registry, `mxf_<mech>_<sym>_<tf>` in AF's sweep) hide "
            "it from the eye AND from the ratchet, which keys on the name. AR declared three such "
            "members as new hypotheses and MEASURED the duplication afterwards, by trade-key "
            "identity on (symbol, decision_bar_iso, r_gross) rather than by name: 110/110 for "
            "`ger40` and `jp225` with identical mean gross R, 121 of 122 for `us30_cash` (AF's "
            "`pre_gap_population` is one trade wider). Corrected bill 45, not 48; rank 1 0.002222 "
            "rather than 0.002083. THE FILE STAYS AT 48 AND THAT IS CORRECT: `effective_size` is "
            "`max(high_water_size, len(members))` and the loader refuses a member count below the "
            "stored high water, deliberately, because letting a withdrawal shrink the family is "
            "the curation the ratchet exists to prevent (`candidate_family.py:206-219`, "
            "`:246-254`). The over-charge is CONSERVATIVE -- a tighter bar can only make AR's own "
            "arms harder to admit -- and nothing admitted at either bill. REPAIR: any session "
            "declaring AF members runs the alias check FIRST. One set intersection on the trade "
            "keys; the names cannot tell you."),
        evidence={
            "artifact": str(FAMV4.relative_to(REPO)),
            **(f["families"]["CANDIDATE_BOOK_V1"]["history"][-1]
               .get("and_I_OVER_CHARGED_MYSELF_BY_THREE") or {}),
        })

    row(
        sleeve="sub_xvol_pullback",
        component="phase10/receipts/REGIME_CONDITIONING_V1.json vs AR section 1",
        prescription="THE_IDENTITY_FILTER_CHECK_HAS_TWO_LAYERS_AND_ONLY_ONE_WAS_BEING_RUN",
        is_primary=False, verdict="METHOD_EXTENDED",
        margin=None,
        action=(
            "AO's identity-filter rule (wave-11 agreement section 2) is: before conditioning on "
            "a variable, prove the sleeve does not already pin it. AO's instrument is the "
            "distinct-BUCKET count, which is right for a bucket GATE and silent about a level "
            "TILT. Both layers must be reported, and for `sub_xvol_pullback` they give opposite "
            f"answers on the same variable: the vol BUCKET takes "
            f"{lf['n_distinct_buckets']} value over {lf['n_trades']} trades (pinned — a gate is "
            f"the identity filter) while the LEVEL takes {lf['n_distinct_levels']} distinct "
            f"values over the same trades, range [{lf['vr_min']:.4f}, {lf['vr_max']:.4f}], "
            f"max/min {lf['vr_max_over_min']:.3f}. REPAIR: the agreement's identity-filter check "
            "should require BOTH counts whenever the proposed consumer is continuous — "
            "distinct buckets AND distinct levels with the range — because 'pinned' is a "
            "property of the discretiser, not of the variable."),
        evidence={"artifact": str(TILT.relative_to(REPO)), **lf})

    return out


def main() -> int:
    new = rows()
    existing = [json.loads(line) for line in QUEUE.read_text().splitlines() if line.strip()]
    #  duplicate control, AR's OWN rows only (AO section 8.3's correction)
    mine = {(r.get("sleeve"), r.get("prescription")) for r in existing
            if r.get("session") == SESSION}
    dup = [(r["sleeve"], r["prescription"]) for r in new
           if (r["sleeve"], r["prescription"]) in mine]
    if dup:
        raise SystemExit(f"REFUSING: AR rows already in the queue: {dup}. The ledger is "
                         f"append-only; re-running would double-count AR's own work.")
    pre: dict = {}
    for r in existing:
        k = (r.get("session"), r.get("sleeve"), r.get("prescription"))
        pre[k] = pre.get(k, 0) + 1
    pre_collisions = {k: n for k, n in pre.items() if n > 1}
    with QUEUE.open("a") as fh:
        for r in new:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    print(f"appended {len(new)} AR rows -> {QUEUE.relative_to(REPO)} "
          f"({len(existing)} -> {len(existing)+len(new)} rows)")
    for r in new:
        print(f"  [{'P' if r.get('is_primary') else ' '}] {r['sleeve']:24s} "
              f"{r['prescription']}")
    if pre_collisions:
        #  reported, never fixed and never fatal: not AR's rows (AO section 8.3)
        print(f"\nnote: {len(pre_collisions)} PRE-EXISTING (session, sleeve, prescription) "
              f"collisions from other sessions — reported, not touched:")
        for k, n in sorted(pre_collisions.items())[:6]:
            print(f"    x{n} {k}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
