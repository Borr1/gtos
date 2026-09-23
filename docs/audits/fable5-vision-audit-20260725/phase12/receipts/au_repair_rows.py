"""Session AU — append this session's repair rows to the append-only queue.

    python3 docs/audits/fable5-vision-audit-20260725/phase12/receipts/au_repair_rows.py
    ... --dry-run

Append-only and union-merged at the train (agreement §3). Rows that CORRECT an earlier row carry a
`corrects` block naming their subject; the wrong row and its correction sit side by side, which is what
a reader needs (AR §8.14 learned that the hard way by editing a row in place).

Every figure here is READ from a committed artifact rather than transcribed, and the script dies if an
artifact is missing -- a repair row quoting a number nobody can reproduce is worse than no row.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
HERE = REPO / "docs/audits/fable5-vision-audit-20260725/phase12/receipts"
P6 = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts"
QUEUE = P6 / "REPAIR_QUEUE_APPEND.jsonl"

WIRING = HERE / "AU_EXIT_WIRING_V1.json"
RESTAMP = HERE / "AU_ESTATE_RESTAMP_V1.json"
HORIZONS = HERE / "AU_D1_HORIZONS_V1.json"
DOSSIER_R = HERE / "AU_DOSSIER_RESTAMP_V1.json"
SUBMID_F = HERE / "AU_SUBMID_FRONTIER_V1.json"

BTC = "mx_btcusd_d1_donchian_20_breakout"
XVOL = "sub_xvol_pullback"


def load(p: Path) -> dict:
    if not p.is_file():
        raise SystemExit(f"missing artifact {p.relative_to(REPO)} — run its driver first")
    return json.loads(p.read_text(encoding="utf-8"))


def rows() -> list[dict]:
    w = load(WIRING)
    r = load(RESTAMP)
    h = load(HORIZONS)
    d = load(DOSSIER_R)
    sf = load(SUBMID_F) if SUBMID_F.is_file() else None
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    out: list[dict] = []

    def row(**kw):
        out.append({"appended_utc": now, "session": "AU", **kw})

    # ---------------------------------------------------------------- AU-1
    def arm(sleeve, name, band="mid"):
        for a in w["gate_rows"][sleeve]["arms"]:
            if a["arm"] == name and a["band"] == band:
                return a
        raise KeyError(f"{sleeve}/{name}/{band}")

    btc5 = arm(BTC, "target_5R")
    xv4, xvw = arm(XVOL, "target_4R"), arm(XVOL, "as_walked")
    idw = w["identity"]
    row(prescription="THE_TWO_FRONTIER_EXIT_CONTRACTS_ARE_NOW_RUNNABLE_AND_DEFAULT_OFF",
        sleeve=f"{BTC},{XVOL}", component="src/components/ultimate_book/execution_packets.py",
        verdict="WIRED_AND_PROVED_IDENTICAL_TO_THE_RESEARCH_CELL", is_primary=True, margin=None,
        action=("`FRONTIER_EXIT_OVERRIDES` + `resolve_exit_profile` + `parse_frontier_exits`, reached "
                "from `run_book.py --frontier-exits <sleeve>[,<sleeve>]` through the owner, the order "
                "router and the adopt-rehydration path. A SET OF SLEEVE NAMES, not a boolean, because "
                "the two are in opposite live states: `mx_btcusd` is in neither account's `--tags` so "
                "its 5R contract is inert, while `sub_xvol_pullback` is ARMED on both accounts at 3R. "
                "An empty selection is REFUSED rather than read as 'all' (the `--tags` fail-open, "
                "B359) and an unknown name is REFUSED rather than dropped (`registry.py:144`). "
                "Explicitly NOT a config key: it never reaches `bridge._bool`, so it cannot produce "
                "AR's KeyError-against-DEFAULT_CONFIG outage, and no byte of either live YAML moves. "
                "43 behavioural tests. Default selection is empty and the placement is asserted "
                "byte-identical on the sized output."),
        evidence={"identity_control_translator_reproduces_AA":
                      {s: idw[s]["control_translator_reproduces_AA"]["identical"] for s in idw},
                  "committed_profile_is_as_walked":
                      {s: idw[s]["committed_is_as_walked"]["identical"] for s in idw},
                  "frontier_profile_is_the_research_cell":
                      {s: idw[s]["frontier_is_the_research_cell"]["identical"] for s in idw},
                  "only_expected_relabel_maxbars_to_time_stop":
                      {s: idw[s]["frontier_is_the_research_cell"]["exit_reason_relabelled"]
                       for s in idw},
                  "artifact": str(WIRING.relative_to(REPO)),
                  "tests": "tests/ultimate_book/test_frontier_exit_contracts.py"})

    row(prescription="THE_ADMISSION_SURVIVES_THE_ROUND_TRIP_INTO_THE_LIVE_SPEC",
        sleeve=BTC, component=str(WIRING.relative_to(REPO)),
        verdict="ADMIT_AT_TWO_OF_THREE_COST_BANDS", is_primary=True,
        margin=btc5["p_raw"],
        action=("Gated through the WIRED contract rather than through AD's research variant: "
                f"p_raw {btc5['p_raw']}, R/day {btc5['pooled_oos_mean_r']}, n {btc5['n_trades']}, "
                "which reproduces the ratified decision to the digit. It also holds at the V5 "
                "declaration (48) rather than AQ's V3 (39) — a TIGHTER bar. So the estate's one "
                "standing admission now describes a contract `run_book.py` can be told to run. "
                "Arming remains Borhen's."),
        evidence={"bands": {a["band"]: a["verdict"] for a in w["gate_rows"][BTC]["arms"]
                            if a["arm"] == "target_5R"},
                  "fold_means": btc5["fold_means"],
                  "size_on_the_recent_folds": btc5["fold_means"][-2:] if btc5["fold_means"] else None,
                  "maxbars_share": btc5["maxbars_maxbars_share"],
                  "horizon_share": btc5["maxbars_horizon_share"]})

    row(prescription="AKS_TARGET_4R_WINNER_DOES_NOT_ADMIT_AT_THE_RATIFIED_RULE__DO_NOT_ARM_IT",
        sleeve=XVOL, component="docs/audits/fable5-vision-audit-20260725/phase8/receipts/"
                               "AK_EXIT_FRONTIER_V2.json",
        verdict="REJECT_AT_ALL_FOUR_BANDS", is_primary=True, margin=xv4["p_raw"],
        action=("`sub_xvol_pullback @ target_4R` is AK's frontier winner and it had never been gated "
                "at the ratified rule: `ak_supply_gate.py` sets NO `spread_band` and NO era "
                "population, so its verdict is at the flat 37-day snapshot on ALL_ERAS against AA's "
                "69-look bill — the two qualifications AO and AR established, on the one sleeve in "
                "the estate that is ARMED and trading real money. Re-gated on RECORDED at "
                f"B_balanced alpha 0.10 against the V5 family: REJECT at all four bands, p "
                f"{xv4['p_raw']} against a BH rank-1 bar of 0.002083 (3.8x short). The exit repair "
                f"is real and insufficient: R/day {xvw['pooled_oos_mean_r']:.4f} -> "
                f"{xv4['pooled_oos_mean_r']:.4f} (+{xv4['pooled_oos_mean_r'] - xvw['pooled_oos_mean_r']:.4f}) "
                f"and p {xvw['p_raw']} -> {xv4['p_raw']}. The contract is WIRED and OFF; arming it is "
                "not supported by the evidence."),
        evidence={"in_sample_mean_is_r": xv4["in_sample_mean_is_r"],
                  "in_sample_mean_oos_r": xv4["in_sample_mean_oos_r"],
                  "in_sample_sign_inversion": xv4["in_sample_sign_inversion"],
                  "recommended_magnitude_haircut": xv4["recommended_magnitude_haircut"],
                  "haircut_binding_term": xv4["haircut_binding_term"],
                  "fold_means_chronological": xv4["fold_means"],
                  "note": ("the folds RISE (+0.581, +1.198, +2.316) — the opposite of mx_btcusd's "
                           "7.6x decay — but only 3 are evaluable, 1 is thin, and n is 85"),
                  "band_envelope": {a["band"]: a["pooled_oos_mean_r"]
                                    for a in w["gate_rows"][XVOL]["arms"]
                                    if a["arm"] == "target_4R"}})

    row(prescription="AN_ARMED_SLEEVE_CARRIES_A_TRAIN_TEST_SIGN_INVERSION_AND_NO_RECEIPT_HAD_SHOWN_IT",
        sleeve=XVOL, component="src/research_infra/walkforward/gate.py",
        verdict="PUBLISHED_FOR_THE_FIRST_TIME", is_primary=True,
        margin=xv4["in_sample_mean_is_r"],
        action=("AR handoff item 2 asked for `regime_inflation` and `in_sample` on every gate "
                "receipt. The first receipt to publish them found this: `sub_xvol_pullback`'s "
                f"train-window mean is {xv4['in_sample_mean_is_r']:.4f} R while its test-window mean "
                f"is {xv4['in_sample_mean_oos_r']:.4f} — a SIGN INVERSION on a sleeve trading real "
                "money on two funded accounts, the highest per-trade gross R in the survivor book, "
                "and the sleeve `ultimate_book_include_clean3: true` was flipped to admit. Same shape "
                "AR found on `mx_us30_cash` (IS -0.2477 / OOS +0.3398), one register up: that was a "
                "candidate, this is armed. The regime-inflation verdict reads CLEAN with a "
                f"magnitude haircut of x{xv4['recommended_magnitude_haircut']} on the regime basis. "
                "Not a gate and not an argument to disarm; it is the number an owner sizing off "
                "`pooled_oos_mean_r` has never been shown."),
        evidence={"as_walked": {"is": xvw["in_sample_mean_is_r"], "oos": xvw["in_sample_mean_oos_r"],
                                "haircut": xvw["recommended_magnitude_haircut"]},
                  "target_4R": {"is": xv4["in_sample_mean_is_r"], "oos": xv4["in_sample_mean_oos_r"],
                                "haircut": xv4["recommended_magnitude_haircut"]},
                  "sweep_the_other_sessions_receipts": True})

    row(prescription="THE_REGIME_INFLATION_VERDICT_CALLED_A_FLOOR_APPROXIMATELY_ONE",
        sleeve="ALL", component="src/research_infra/validation_integrity/regime_inflation.py",
        verdict="REPAIRED_AND_TEST_PINNED", is_primary=True, margin=None,
        action=("The CLEAN branch printed a HARDCODED `(~1.0)` beside an INTERPOLATED "
                "`recommended_magnitude_haircut`, so an arm whose haircut had fallen to the 0.05 "
                "floor published `recommended magnitude haircut x0.050 (~1.0)` — a 20x misstatement "
                "inside the sentence that quotes the number. It landed on the estate's STANDING "
                "ADMISSION: `mx_btcusd @ target_5R` on RECORDED/mid reads haircut 0.05 with "
                "`selection_surface_penalty` 0.0, because the expected max-of-128 Sharpe (0.551) "
                "exceeds the arm's own window Sharpe (0.323). Same class as the PARTIAL UNIVERSE "
                "stamp AP repaired in `gate.py`: prose asserting what the fields beside it deny. "
                "FIXED: the branch now names the binding term and says FLOOR when it is one, and "
                "three new fields (`haircut_binding_term`, `haircut_at_floor`, "
                "`selection_surface_evaluable`) travel through `gate.py`'s telemetry. NO FIELD'S "
                "VALUE MOVED, so no published verdict moves."),
        evidence={"standing_admission_row": {
                      "recommended_magnitude_haircut": btc5["recommended_magnitude_haircut"],
                      "haircut_at_floor": btc5["haircut_at_floor"],
                      "haircut_binding_term": btc5["haircut_binding_term"],
                      "selection_surface_penalty": btc5["selection_surface_penalty"],
                      "selection_surface_evaluable": btc5["selection_surface_evaluable"]},
                  "resolution_caveat": ("the penalty rests on a cross-period SR variance estimated "
                                        "from TWO full years (2020 SR 0.536, 2024 SR 0.164), which "
                                        "is the module's bare minimum — so the 0.0 is not strong "
                                        "evidence either, and `selection_surface_evaluable` now "
                                        "says so. Do not quote the floor as 'shrink 20x' NOR as "
                                        "'~1.0'."),
                  "tests": "tests/research_infra/test_vig_regime_inflation_sign.py"})

    row(prescription="A_RUNTIME_FLAG_READ_WITHOUT_A_DEFAULT_IS_NOW_IMPOSSIBLE_NOT_JUST_FIXED",
        sleeve="ALL", component="tests/ultimate_book/test_runtime_flag_defaults_complete.py",
        verdict="CLOSES_AR_HANDOFF_ITEM_4", is_primary=False, margin=None,
        action=("`bridge._bool(cfg, key)` indexes `DEFAULT_CONFIG[key]`, and an absent key raises "
                "KeyError inside `evaluate_vnext_ultimate_book_admission`, which `book_engine.evaluate` "
                "catches as `engine_exception` — an armed book standing down every tick with a healthy "
                "heartbeat. AR hit it on the first run of `--vol-level-tilt` and filed the AST walk "
                "rather than building it. Built: the test DISCOVERS the resolvers (any function that "
                "indexes its module's `DEFAULT_CONFIG` by a parameter) and checks every literal key "
                "handed to one, over `bridge.py` AND `convergence_advisory.py`, so a new key or a new "
                "resolver is covered without editing the test. Includes a negative case proving the "
                "walk detects the defect, and records that `replay_policy/sleeve_book.py`'s reader is "
                "fail-OPEN by construction so the guarantee does not extend there."),
        evidence={"modules_covered": ["src/components/ultimate_book/bridge.py",
                                      "src/components/ultimate_book/convergence_advisory.py"]})

    row(prescription="THE_LEARNING_LANE_RAISE_GUARD_IS_NOW_A_PROPERTY_OVER_EVERY_BRANCH",
        sleeve="ALL", component="tests/ultimate_book/test_learning_actuator_live.py",
        verdict="AP_FIX_CONFIRMED_AND_GENERALISED", is_primary=False, margin=None,
        action=("AP repaired the raise guard (`_braking = (\"GATE\", \"DOWN_WEIGHT\")`) and pinned the "
                "two instances it found. The guard is a hardcoded membership tuple, which is what "
                "decays. Added the property over the WHOLE branch set: one fixture per reachable "
                "branch of `_backtest_verdict`, each offered a spectacular live record, asserting "
                "that anything the backtest half deployed BELOW 1.0 is not raised — and that the "
                "three branches at 1.0 still ARE, so it cannot pass by braking everything. Verified "
                "the fix and the test are both already in the tree; this session added the "
                "exhaustive form, not the repair. Branch coverage is asserted against the full "
                "verdict vocabulary so the enumeration cannot silently shrink."),
        evidence={"branches": ["every_neg->GATE", "mixed_neg_heavy->DOWN_WEIGHT",
                              "mixed_hold_flag->HOLD_FLAG", "every_pos_material->SIZE_UP",
                              "every_pos_thin->KEEP", "insufficient->INSUFFICIENT_EVIDENCE"],
                  "commission_item_was_stale": ("AU-4 asked to 'fix with a test'; AP had already "
                                                "fixed it AND tested the two instances")})

    # ---------------------------------------------------------------- AU-2
    st = r["restamp"]
    af, ms, ea = st["asian_fade"]["bands"]["mid"], st["metal_session_reversion"]["bands"]["mid"], \
        st["energy_agri"]["bands"]["mid"]
    row(prescription="CORRECTION__AQS_LARGEST_LABELLING_ERROR_IS_A_CONSTRUCTION_ARTIFACT",
        sleeve="asian_fade,metal_session_reversion", component=str(RESTAMP.relative_to(REPO)),
        verdict="CORRECTS_AN_EARLIER_AQ_ROW", is_primary=True,
        margin=af["construction_artifact"],
        corrects={"session": "AQ",
                  "prescription": "RESTAMP_PUBLISHED_ECONOMICS_AT_THE_LIVE_CONTRACT",
                  "what_was_wrong": ("AQ's Side-B `error` column for the two `trailing_runner` "
                                     "sleeves measures 'the trail deleted AND a time stop added', "
                                     "not 'the time stop added'. Its `LIVE_TRUE` arm is "
                                     "`AD.Variant(family=\"time_stop\", target_mode=\"native\")` "
                                     "and `Variant` defaults `trail_arm_r`/`trail_gap_r`/"
                                     "`partial_at_r` to None, so it drops the sleeve's own exit "
                                     "policy. AQ named the mechanism and routed the measurement; "
                                     "this is it.")},
        action=("Measured with the WHOLE live profile translated (trail AND scale-out AND target AND "
                f"time stop): `asian_fade`'s true restamp error is {af['restamp_error']:+.4f} R/day "
                f"— ZERO — against AQ's published {af['ts_only_error']:+.4f}, so 100 % of the "
                "estate's 'largest single labelling error' is the dropped trail. Its truncation "
                "fraction of 0.0 was the tell: a time stop that never fires cannot cost 0.88 R/day. "
                f"`metal_session_reversion` is the same shape: true error {ms['restamp_error']:+.4f}, "
                f"artifact {ms['construction_artifact']:+.4f}. AA's own metadata settles the "
                "published contract — `exit_contracts[sleeve].applied_here == "
                "'trail+stop+target+maxbars'`. THE REAL QUALIFICATION ON `asian_fade` IS A DIFFERENT "
                f"ONE: at B613's honest trail bound it loses {af['intrabar_trail_credit']:+.4f} "
                "R/day, i.e. the published -0.1528 becomes -0.4893, which is AD's 95.8 %-intrabar "
                "finding priced at the ratified rule."),
        evidence={"asian_fade": af, "metal_session_reversion": ms,
                  "control_published_reproduces_AA_for_all_29_sleeves": True,
                  "translator": "phase12/receipts/au_live_contract.py"})

    row(prescription="THE_ARMED_SCALE_OUT_COSTS_0_23_R_PER_DAY_AND_AQS_ARM_REPORTED_ZERO",
        sleeve="energy_agri", component=str(RESTAMP.relative_to(REPO)),
        verdict="RESTAMPED", is_primary=True, margin=ea["restamp_error"],
        action=("`energy_agri` is ARMED on both accounts and its live policy is `partial_be_runner` "
                "(trigger 2.0R, half off, stop to breakeven). AQ's time-stop-only arm drops the "
                "partial, which for a `partial_be_runner` sleeve accidentally REPRODUCES AA's plain "
                f"walk — so its error cancelled to exactly 0.0000 and the sleeve is absent from the "
                f"ten restamp rows. The true error is {ea['restamp_error']:+.4f} R/day at mid "
                f"(published {ea['published_r_per_day']:+.4f} -> live {ea['live_true_r_per_day']:+.4f}) "
                "and it holds at all four bands. It corroborates AD §6.2's -0.308 R/day on the same "
                "sleeve through a different instrument. The other three `partial_be_runner` sleeves "
                "are affected too and the sign runs BOTH ways — `metals_core`'s scale-out HELPS by "
                "0.0777 R/day, `metals_softband`'s costs 0.0372."),
        evidence={"all_four_partial_be_runner_sleeves": {
                      s: st[s]["bands"]["mid"]["restamp_error"] for s in
                      ("energy_agri", "metals_core", "metals_ob_micro", "metals_softband")},
                  "ad_independent_measurement": "-0.308 R/day, n=67 (AD §6.2)"})

    row(prescription="THE_RESTAMP_MOVES_MAGNITUDES_AND_NOT_ONE_VERDICT",
        sleeve="ALL", component=str(RESTAMP.relative_to(REPO)),
        verdict="NO_VERDICT_MOVED_AT_ANY_BAND", is_primary=False, margin=None,
        action=("29 sleeves x 4 contracts x 4 bands at the ratified rule: not a single gated verdict "
                "differs between the published contract and the live one. The restamp is a "
                "magnitude correction, not a verdict correction — which is the honest headline and "
                "is only worth saying because the alternative was assumed. The TARGET axis is clean "
                "on all 29 sleeves (the live `final_target_r` equals the walked target ratio "
                "everywhere), so the restamp's whole surface is the management policy and the time "
                "stop."),
        evidence={"n_sleeves": r["targets"]["n_sleeves"],
                  "n_target_axis_agree": r["targets"]["n_agree"],
                  "maxbars_share_now_on_every_cell": True,
                  "notable_horizon_shares_under_the_live_contract": {
                      s: st[s]["bands"]["mid"]["horizon_share"]["LIVE_TRUE"]
                      for s in ("crypto", "ny_crypto_momentum", "kz_london_crypto_low")}})

    # ---------------------------------------------------------------- AU-3
    pres = h["prescriptions"]
    declared = {s: p for s, p in pres.items() if p["prescription"] == "DECLARE_SHORT_HORIZON"}
    row(prescription="SIX_SLEEVES_HAVE_A_DELIBERATE_SHORT_HORIZON_DECLARED_ON_THE_EVIDENCE",
        sleeve=",".join(sorted(declared)), component=str(HORIZONS.relative_to(REPO)),
        verdict="DECLARED_AND_WIRED_DEFAULT_OFF", is_primary=True, margin=None,
        action=("AQ measured that on five of the ten generating `mx_*` D1 sleeves the accidental "
                "one-bar stop was BETTER than the 80-bar research horizon, and routed the follow-up "
                "as an exit-frontier decision at the ratified rule (AD's existing grid is at the "
                "flat band on ALL_ERAS, where `mx_btcusd`'s delta reads 1.9x smaller). Ladder "
                "{1,2,3,5,10,20,40,80} own D1 bars, DECLARED BEFORE GATING, gated on RECORDED at "
                "B_balanced alpha 0.10 with the band column and a flat control. Six sleeves clear "
                "all four pre-declared prescription clauses. FOR FOUR OF THEM THE DECLARED VALUE IS "
                "`time_stop_m15(1, \"D1\") == 96` — the integer AQ removed. That is not a revert: "
                "AQ's was a UNIT repair and 96 had to go whatever its economics; what changes is "
                "that 96 stops being an accident and becomes a declaration with a gated measurement "
                "behind it, in a map that is OFF by default. NONE OF THE SIX IS ARMED."),
        evidence={"declared": {s: {"h": p["horizon_own_bars"],
                                   "r_per_day": p["r_per_day_at_mid"],
                                   "delta_vs_80": p["delta_vs_research_horizon"],
                                   "folds": p["folds"], "verdict": p["verdict_at_mid"],
                                   "horizon_share": p["horizon_share"]}
                               for s, p in sorted(declared.items())},
                  "refused_and_why": {s: p["clauses_failed"] for s, p in pres.items()
                                      if p["prescription"] == "MEASURED_BUT_NOT_PRESCRIBED"},
                  "control_sleeve_vol_compression_ladder_is_monotone_rising_not_short_biased": True,
                  "the_search_is_priced": {s: {"p_min": p["p_min_over_grid"],
                                               "E_min_p_null":
                                                   p["expected_min_p_under_global_null"]}
                                           for s, p in sorted(declared.items())}})

    row(prescription="EVERY_D1_HORIZON_CELL_REJECTS__THESE_ARE_CONTRACTS_NOT_EDGES",
        sleeve="ALL_D1", component=str(HORIZONS.relative_to(REPO)),
        verdict="REJECT_EVERYWHERE", is_primary=False, margin=None,
        action=("All 11 cohort sleeves x 8 horizons x 4 bands: zero admissions, and the min-p over "
                "each sleeve's ladder is what the global null returns 22-92 % of the time. So the "
                "short-horizon declarations make the SPEC describe the evidence; they are not "
                "edges, not admissions and not a recommendation to arm. At h=1 the horizon is also "
                "the DOMINANT exit (77-90 % of trades), so those sleeves become one-day-hold "
                "contracts rather than geometries that resolve — a property to know before arming."),
        evidence={"p_min_vs_null": {s: [p["p_min_over_grid"],
                                        p["expected_min_p_under_global_null"]]
                                    for s, p in pres.items() if p.get("p_min_over_grid")}})

    # ---------------------------------------------------------------- AU-4
    row(prescription="CLOSED__THE_ONE_TRUTH_PER_SLEEVE_ARTIFACT_IS_STALE_ON_THE_REPAIRED_FIELD",
        sleeve="12 mx_* sleeves", component=str(DOSSIER_R.relative_to(REPO)),
        verdict="CLOSED", is_primary=False, margin=None,
        corrects={"session": "AQ",
                  "prescription": "THE_ONE_TRUTH_PER_SLEEVE_ARTIFACT_IS_STALE_ON_THE_REPAIRED_FIELD",
                  "what_was_wrong": "nothing — the row was right and this closes it"},
        action=(f"`SLEEVE_DOSSIER_V1.json` carried `time_stop_bars_m15: 96` for "
                f"{d['n_restamped']} sleeves as a current claim with three derived fields false "
                "with it. Restamped from the LIVE spec, with all three derived fields RECOMPUTED "
                "(the truncation fraction is not linear in the horizon, so it is re-run over AA's "
                "trades rather than scaled) and the superseded values kept under `restamped_from`. "
                "`AD_TIMESTOP_UNITS_V1.json` is deliberately NOT rewritten: it is AD's measurement "
                "of the defect at B750 and is correct as one — AQ's own lesson that a measurement "
                "which dies when the defect is fixed is not a measurement. The defect here was "
                "presenting a historical snapshot as a current claim."),
        evidence={"n_restamped": d["n_restamped"], "n_already_current": d["n_unchanged"],
                  "receipt": str(DOSSIER_R.relative_to(REPO))})

    if sf:
        _bands = (((sf.get("frontier") or {}).get("best_cell_at_spread_bands") or {}).get("bands")
                  or {})
        _new = {b: {"r_per_day": v.get("pooled_oos_mean_r"), "p_raw": v.get("p_raw"),
                    "failing": v.get("failing_gates")} for b, v in _bands.items()}
        _oldsl = ((json.loads((REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts/"
                               "EXIT_FRONTIER_V1.json").read_text(encoding="utf-8"))
                   .get("sleeves") or {}).get("sub_mid_dn_revert") or {})
        _oldb = ((_oldsl.get("best_cell_at_spread_bands") or {}).get("bands") or {})
        _old = {b: {"r_per_day": v.get("pooled_oos_mean_r"), "p_raw": v.get("p_raw"),
                    "failing": v.get("failing_gates")} for b, v in _oldb.items()}
        row(prescription="PARTIALLY_CLOSED__REBUILD_THE_DOWNSTREAM_ARTIFACTS_ON_THE_REPAIRED_CLOCK",
            sleeve="sub_mid_dn_revert", component=str(SUBMID_F.relative_to(REPO)),
            verdict="ONE_OF_FOUR_REBUILT__AND_THE_ARTIFACT_WAS_MATERIALLY_WRONG",
            is_primary=True, margin=None,
            action=("`EXIT_FRONTIER_V1_SUBMID_V2.json` rebuilt on AQ's re-clocked population (503 -> "
                    f"{sf['n_trades_after']} trades) using `ad_exit_sweep.main()` UNMODIFIED with only "
                    "its input and output paths substituted, so any difference is the sleeve and not "
                    "the instrument. It merges through `ad_frontier_analysis.py`'s glob, later files "
                    "winning per sleeve — AD's own designed mechanism. STILL OPEN: "
                    "`AD_CARRY_TIERS_RESTATED_V1.json` and `SURVIVOR_BOOK_V1.json` (arithmetic "
                    "downstream of this), and `AA_ESTATE_WALK.json`, whose ratified-rule band table "
                    "AQ §3 already published."),
            evidence={
                "the_rebuild_changes_the_answer": {
                    "old_clock_503_trades": {"best_cell": (_oldsl.get("best_cell_at_spread_bands")
                                                           or {}).get("cell"), "bands": _old},
                    "reclocked_533_trades": {"best_cell": ((sf.get("frontier") or {})
                                                           .get("best_cell_at_spread_bands")
                                                           or {}).get("cell"), "bands": _new},
                    "reading": ("the best banded cell moves time_stop_20 -> time_stop_40 and the "
                                "sleeve goes from NEGATIVE with `expectancy` FAILING (-0.1064 R/day "
                                "at low, p 0.795) to POSITIVE at all three bands with expectancy "
                                "PASSING (+0.0918 / +0.0587 / +0.0079, p 0.192 / 0.290 / 0.466). "
                                "Still REJECT everywhere on stability + robustness + significance, "
                                "so no verdict moves -- but the published frontier for this sleeve "
                                "was wrong in sign and in winner, which is why the row existed."),
                },
                "moved_by_this_swap": sf["moved_by_this_swap"],
                "pre_existing_parity_drift_not_created_here":
                    sf["baseline_parity_moved_in_ADs_committed_frontier_on_the_unmodified_input"],
                "caveat": sf["caveat"]})

    row(prescription="CLOSED__BROKER_TRUE_COSTS_IS_IN_THE_SPARSE_PROFILE",
        sleeve="ALL", component="scripts/gtos_hydrate_test_data.py",
        verdict="CLOSED", is_primary=False, margin=None,
        corrects={"session": "AR", "prescription": "FRESH_WORKTREE_HYGIENE",
                  "what_was_wrong": "nothing — one line of the two AR filed is now closed"},
        action=("`research/operations/broker_truth_layer_2026_07_29/BROKER_TRUE_COSTS_V1_1.json` was "
                "absent from the sparse profile, so every cost-true driver died on a fresh worktree "
                "with an error recommending a re-capture of the broker-truth layer rather than a "
                "checkout. Confirmed absent again at the start of this session in a worktree where "
                "the hydrator had already reported completion. Added to `EXTRA_HYDRATIONS`. AR's "
                "OTHER line — 196 LFS pointers standing after the hydrator reports done — stays "
                "open, and deliberately: CLAUDE.md §3's amendment makes one of those pointers "
                "actively dangerous to resolve here."),
        evidence={"line": "scripts/gtos_hydrate_test_data.py EXTRA_HYDRATIONS"})

    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    rs = rows()
    before = sum(1 for _ in QUEUE.open(encoding="utf-8")) if QUEUE.is_file() else 0
    if not a.dry_run:
        with QUEUE.open("a", encoding="utf-8") as fh:
            for r in rs:
                fh.write(json.dumps(r, sort_keys=True) + "\n")
    print(f"{'would append' if a.dry_run else 'appended'} {len(rs)} row(s); "
          f"queue {before} -> {before + (0 if a.dry_run else len(rs))}")
    for r in rs:
        print(f"  [{'P' if r.get('is_primary') else ' '}] {r['prescription']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
