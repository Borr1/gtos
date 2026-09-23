#!/usr/bin/env python3
"""Session AS — append this session's rows to the repair queue.

Append-only, union-merged at the train. Each row states the verdict, the evidence, and the
prescription, and every numeric field is read from a committed artifact rather than typed here.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
AUDIT = REPO / "docs/audits/fable5-vision-audit-20260725"
QUEUE = AUDIT / "phase6/receipts/REPAIR_QUEUE_APPEND.jsonl"

ACT = json.loads((AUDIT / "phase11/receipts/AS_EXIT_CONTRACT_ACTIVATION_V1.json").read_text())
BASIS = json.loads((AUDIT / "phase11/receipts/AS_LIVE_SLEEVE_BASIS_V1.json").read_text())
CONDS = json.loads((AUDIT / "phase11/receipts/FIVE_SLEEVE_STOP_CONDITIONS_V1.json").read_text())
FLEET = json.loads((AUDIT / "phase11/receipts/AS_FLEET_MAP_V1.json").read_text())

A = ACT["regate"]["arms"]
F = CONDS["conditions"]["S1a_risk_floor"]["per_sleeve_account"]
E = CONDS["conditions"]["S1b_evidence_floor"]["per_sleeve_account"]
P = BASIS["live_prior"]["per_sleeve_account"]
S = BASIS["live_prior_significance"]["per_sleeve_account"]

NOW = datetime.now(timezone.utc).isoformat()

ROWS = [
    {
        "session": "AS", "sleeve": "mx_btcusd_d1_donchian_20_breakout",
        "component": "src/components/ultimate_book/execution_packets.py:249-256",
        "verdict": "DEFECT_IN_THE_OBVIOUS_ACTIVATION_PATH",
        "prescription": "THE_NAIVE_final_target_r_EDIT_IS_A_NO_OP_FOR_THE_WHOLE_mx_COHORT",
        "is_primary": True, "gate": None, "margin": None,
        "evidence": {
            "mechanism": ACT["noop"]["mechanism"],
            "committed_resolved_target_r": ACT["noop"]["mx_btcusd"]["committed"]["final_target_r"],
            "after_naive_edit_to_5":
                ACT["noop"]["mx_btcusd"]["naive_edit_final_target_r_5"]["final_target_r"],
            "after_dropping_final_from_intent":
                ACT["noop"]["mx_btcusd"]["correct_edit_drop_final_from_intent"]["final_target_r"],
            "proved": "behaviourally, by driving the real build_book_trade_params under three "
                      "profile states; pinned by tests/ultimate_book/"
                      "test_exit_contract_activation.py::test_the_naive_mx_edit_is_a_noop",
            "cost_if_missed": "the sleeve would be armed on the 2R contract its own evidence "
                              "REJECTS at every band while every spec read and every log said 5R",
        },
        "action": "the activation diff must ALSO remove `final_from_intent` from the mx_btcusd "
                  "profile, or change the generator's TARGET_R (which moves all 14). Route A is "
                  "recommended: blast radius 1 sleeve, 0 armed.",
        "appended_utc": NOW,
    },
    {
        "session": "AS", "sleeve": "sub_xvol_pullback",
        "component": "docs/audits/fable5-vision-audit-20260725/phase8/receipts/"
                     "AK_EXIT_FRONTIER_V2.json",
        "verdict": "REJECT",
        "prescription": "THE_ARMED_SLEEVES_EXIT_UPGRADE_RE_GATED_AT_THE_RATIFIED_RULE__WORTH_MORE"
                        "_AND_STILL_REJECTS",
        "is_primary": True,
        "gate": "significance",
        "margin": A["target_4R|RECORDED|mid|V5_48"]["p_raw"] / (0.10 / 48),
        "evidence": {
            "ak_standard": "ALL_ERAS at the flat 37-day snapshot at the historical 69-look family "
                           "— AK's frontier carries no population and no spread_band key",
            "control_reproduces": ACT["regate"]["control"]["r_per_day_reproduces"]
                                  and ACT["regate"]["control"]["p_reproduces"],
            "delta_at_ak_standard": (A["target_4R|ALL_ERAS|mid|V5_48"]["pooled_oos_mean_r"]
                                     - A["as_walked|ALL_ERAS|mid|V5_48"]["pooled_oos_mean_r"]),
            "delta_at_ratified_rule": (A["target_4R|RECORDED|mid|V5_48"]["pooled_oos_mean_r"]
                                       - A["as_walked|RECORDED|mid|V5_48"]["pooled_oos_mean_r"]),
            "p_raw": A["target_4R|RECORDED|mid|V5_48"]["p_raw"],
            "bh_rank1_bar_at_family_48": 0.10 / 48,
            "n_trades_recorded": A["target_4R|RECORDED|mid|V5_48"]["n_trades"],
            "maxbars_share_as_walked": A["as_walked|RECORDED|mid|V5_48"]["maxbars_share"],
            "maxbars_share_target_4R": A["target_4R|RECORDED|mid|V5_48"]["maxbars_share"],
            "carry_cost": "swap nights mean 4.2692 -> 6.4615, median hold 92 -> 123 h, swap share "
                          "of cost 0.543 -> 0.648 on the sleeve whose largest cost term IS swap",
            "the_widely_misread_number": ACT["regate"]["the_number_that_is_widely_misread"],
        },
        "action": "DO NOT propose. REJECT at every band, 3.8x outside the rank-1 bar, on an ARMED "
                  "sleeve, and it buys carry. The binding constraint is sample (n 85, 3 evaluable "
                  "folds), not a repair on this axis.",
        "appended_utc": NOW,
    },
    {
        "session": "AS", "sleeve": "sub_xvol_pullback",
        "component": "src/components/ultimate_book/execution_packets.py:84",
        "verdict": "EVIDENCE",
        "prescription": "THE_ARMED_SLEEVES_LIVE_3R_CONTRACT_IS_THE_WALK_BASELINE_TO_THE_DIGIT",
        "is_primary": False, "gate": None, "margin": None,
        "evidence": {
            "as_walked_r_per_day": A["as_walked|RECORDED|mid|V5_48"]["pooled_oos_mean_r"],
            "target_3R_live_r_per_day": A["target_3R_live|RECORDED|mid|V5_48"]["pooled_oos_mean_r"],
            "identical": (A["as_walked|RECORDED|mid|V5_48"]["pooled_oos_mean_r"]
                          == A["target_3R_live|RECORDED|mid|V5_48"]["pooled_oos_mean_r"]),
            "why_it_matters": "a live-contract fidelity confirmation on ARMED money: the walk's "
                              "baseline IS what the book runs, so this sleeve's published "
                              "economics do not carry the labelling error AQ's Side-B table found "
                              "on ten others",
        },
        "action": "none — record it. It is the positive half of the contract-fidelity sweep.",
        "appended_utc": NOW,
    },
    {
        "session": "AS", "sleeve": "fx_jpy",
        "component": "docs/audits/fable5-vision-audit-20260725/phase1/w7_forensics/"
                     "LIVE_TRADE_ROWS.jsonl",
        "verdict": "OWNER_DECISION",
        "prescription": "AN_ARMED_SLEEVES_ARCHIVE_EXPECTANCY_IS_NEAR_ZERO_AND_THE_FLOOR_IS_20x_"
                        "FASTER_DOWN_THAN_UP",
        "is_primary": True, "gate": None,
        "margin": F["FTMO::fx_jpy"]["archive_net_r_per_trade_at_measured_carry"],
        "evidence": {
            "archive_net_r_per_trade_ftmo":
                F["FTMO::fx_jpy"]["archive_net_r_per_trade_at_measured_carry"],
            "archive_net_r_per_trade_redacted_account":
                F["redacted_account::fx_jpy"]["archive_net_r_per_trade_at_measured_carry"],
            "fills_to_earn_the_floor_at_archive_rate": [
                F["FTMO::fx_jpy"]["fills_to_trip_at_archive_expectancy"],
                F["redacted_account::fx_jpy"]["fills_to_trip_at_archive_expectancy"]],
            "fills_to_reach_the_floor_at_the_live_prior": [
                F["FTMO::fx_jpy"]["fills_to_trip_at_live_prior"],
                F["redacted_account::fx_jpy"]["fills_to_trip_at_live_prior"]],
            "break_even_nights": [
                CONDS["conditions"]["S3_carry_surprise"]["per_sleeve_account"]
                ["FTMO::fx_jpy"]["break_even_nights"],
                CONDS["conditions"]["S3_carry_surprise"]["per_sleeve_account"]
                ["redacted_account::fx_jpy"]["break_even_nights"]],
            "live_prior_gross_r_total": [P["FTMO::fx_jpy"]["gross_r_total"],
                                         P["redacted_account::fx_jpy"]["gross_r_total"]],
            "live_prior_net_r_total": [P["FTMO::fx_jpy"]["net_r_total"],
                                       P["redacted_account::fx_jpy"]["net_r_total"]],
            "day_blocked_p_vs_zero": [S["FTMO::fx_jpy"]["vs_zero"]["p"],
                                      S["redacted_account::fx_jpy"]["vs_zero"]["p"]],
            "day_blocked_p_vs_archive_gross": [S["FTMO::fx_jpy"]["vs_archive_gross"]["p"],
                                               S["redacted_account::fx_jpy"]["vs_archive_gross"]["p"]],
            "the_honest_reading": "the loss is REAL (money left the accounts) and it is NOT "
                                  "SIGNIFICANT (32 fills over 13 day blocks). That is why the stop "
                                  "conditions are risk bounds and not tests.",
        },
        "action": "no change proposed. The owner armed this deliberately and priced it. What was "
                  "missing was a pre-registered exit, and it now exists: "
                  "phase11/receipts/FIVE_SLEEVE_STOP_CONDITIONS_V1.json, evaluated by "
                  "scripts/book_sleeve_telemetry.py.",
        "appended_utc": NOW,
    },
    {
        "session": "AS", "sleeve": "__estate__",
        "component": "phase4/CANARY_OPERATOR_PAGE.md condition C3",
        "verdict": "INSTRUMENT_CORRECTION",
        "prescription": "A_GROSS_NEGATIVE_TRIPWIRE_MUST_FIRE_ON_BOTH_WEIGHTINGS_AND_PER_ACCOUNT",
        "is_primary": False, "gate": None, "margin": None,
        "evidence": {
            "ftmo_fx_jpy_trade_weighted": P["FTMO::fx_jpy"]["gross_r_per_fill_trade_weighted"],
            "ftmo_fx_jpy_day_weighted": P["FTMO::fx_jpy"]["gross_r_per_fill_day_weighted"],
            "attenuation": 1 - (P["FTMO::fx_jpy"]["gross_r_per_fill_day_weighted"]
                                / P["FTMO::fx_jpy"]["gross_r_per_fill_trade_weighted"]),
            "why": "the losing days carry up to four fills and the winning days carry one; the "
                   "decision day is the dependence unit (Session R, lag-1 rho 0.511). A "
                   "trade-weighted-only tripwire reports a sleeve's WORST reading as its verdict.",
            "and_the_pooling_trap": "pooling the two accounts into one day block flips the pooled "
                                    "day-weighted figure POSITIVE (+0.0563) while both accounts "
                                    "are individually negative — an artifact of the pooling, and "
                                    "the reason every figure is computed per account",
        },
        "action": "S2 in FIVE_SLEEVE_STOP_CONDITIONS_V1.json requires BOTH weightings negative, "
                  "per account, over >= 20 fills and >= 8 day blocks, and publishes the day-blocked "
                  "permutation p with its resolution floor on every trip.",
        "appended_utc": NOW,
    },
    {
        "session": "AS", "sleeve": "__methodology__",
        "component": "scripts/book_sleeve_telemetry.py::signflip_p",
        "verdict": "FIXED_IN_THIS_SESSION",
        "prescription": "A_PERMUTATION_TEST_THAT_RETURNS_NONE_ABOVE_20_BLOCKS_MAKES_MORE_DATA_"
                        "WEAKER",
        "is_primary": False, "gate": None, "margin": None,
        "evidence": {
            "defect": "the first cut returned p=None above 20 day blocks (2**n enumeration), which "
                      "is the NORMAL case after a month of trading, not an edge case",
            "fix": "exact enumeration to 20 blocks, then a Monte Carlo seeded FROM THE DATA so the "
                   "number on the page is reproducible without a wall clock or a global random "
                   "state; the resolution floor is 1/achievable or 1/draws and is always reported",
            "found_by": "a behavioural test that asserted the power disclosure names its floor",
            "pinned_by": "tests/ultimate_book/test_book_sleeve_telemetry.py — determinism, "
                         "agreement with the exact test at the boundary, and shift-equivariance",
        },
        "action": "none — landed.",
        "appended_utc": NOW,
    },
    {
        "session": "AS", "sleeve": "__infrastructure__",
        "component": "research/operations/broker_truth_layer_2026_07_29/",
        "verdict": "CONFIRMS_AN_EARLIER_AR_ROW",
        "prescription": "THE_SPARSE_CHECKOUT_GAP_REPRODUCED_IN_A_SECOND_WORKTREE",
        "is_primary": False, "gate": None, "margin": None,
        "evidence": {
            "what": "BROKER_TRUE_COSTS_V1_1.json is tracked in git but its route directory is "
                    "absent from the sparse-checkout profile, so any cost-true driver dies on "
                    "CostTruthError in a fresh worktree",
            "ar_row": "AR B1473 filed this as fresh-worktree hygiene; it reproduced here exactly",
            "fix_applied_locally": "git sparse-checkout add research/operations/"
                                   "broker_truth_layer_2026_07_29",
            "why_it_matters": "the failure mode is a driver that cannot run, which reads as 'this "
                              "measurement is expensive' rather than 'this worktree is "
                              "incomplete'",
        },
        "action": "add the route to the committed sparse profile so the next worktree does not pay "
                  "for it again. Two sessions have now hit it.",
        "appended_utc": NOW,
    },
    {
        "session": "AS", "sleeve": "__program__",
        "component": "docs/audits/fable5-vision-audit-20260725/phase11/REPLAY_FLEET_MAP.md",
        "verdict": "DECLARED",
        "prescription": "THE_FLEET_IS_18_8_MACHINE_HOURS_AND_THE_CHEAPEST_ITEM_IS_A_PRECONDITION",
        "is_primary": False, "gate": None, "margin": None,
        "evidence": {
            "n_members": FLEET["n_members"],
            "total_machine_hours": FLEET["total_machine_hours"],
            "excluding_the_parked_campaign":
                FLEET["total_machine_hours_excluding_the_parked_campaign"],
            "n_with_a_driver_on_disk": FLEET["n_with_a_driver_on_disk"],
            "n_needing_a_driver_written": FLEET["n_needing_a_driver_written"],
            "top_by_value_per_machine_hour": FLEET["order"][:5],
            "the_headline": "F15 — a read-only copy_rates probe on the two terminals, 0.2 MH — "
                            "decides whether mx_btcusd can be armed AT ALL, because after AQ's "
                            "time-stop repair a short feed makes the backstop INERT rather than "
                            "late. It is the cheapest item on the map and it is a precondition.",
        },
        "action": "schedule from the map. It is generated and it checks every driver path on disk.",
        "appended_utc": NOW,
    },
]

ROWS += [
    {
        "session": "AS", "sleeve": "__estate__",
        "component": "phase11/receipts/FIVE_SLEEVE_STOP_CONDITIONS_V1.json S1",
        "verdict": "DEFECT_IN_MY_OWN_INSTRUMENT",
        "prescription": "A_STOP_CONDITION_WITHOUT_A_MEASURED_FALSE_ALARM_RATE_IS_A_NUMBER_"
                        "SOMEBODY_LIKED",
        "is_primary": True, "gate": None, "margin": None,
        "evidence": {
            "what": "the first cut had ONE floor at -max(3.0, 12 x |expectancy|) justified by an "
                    "UNCOMPUTED claim of a <5 % false-alarm rate. Computing it refuted the claim.",
            "measured_false_trip_within_60_fills": {
                k: F[k]["measured_false_trip_probability_within_60_fills"] for k in sorted(F)},
            "cause": "structural, not a bad constant: fx_jpy's expectancy is +0.041 R/trade against "
                     "a per-trade dispersion of "
                     f"{E['FTMO::fx_jpy']['archive_r_dispersion_sd']:.3f} R. A near-zero-drift walk "
                     "with that step size passes -3 R almost surely. There is NO threshold on that "
                     "sleeve that is both tight and sound.",
            "repair": "split into S1a (risk floor, the owner's tolerance, now carrying its measured "
                      "false-alarm rate on every trip) and S1b (evidence floor, the depth at which "
                      "a trip is informative, solved by bootstrap over each sleeve's OWN centred "
                      "archive R distribution at a <= 10 % false-alarm target)",
            "evidence_floors": {k: E[k]["evidence_floor_r"] for k in sorted(E)},
        },
        "action": "none — landed, and pinned by four tests including one that asserts every floor "
                  "publishes a measured false-trip rate.",
        "appended_utc": NOW,
    },
    {
        "session": "AS", "sleeve": "__runtime__",
        "component": "src/components/execution.py:3003",
        "verdict": "LIVE_DEFECT_ON_ARMED_MONEY__FIXED_IN_THIS_SESSION",
        "prescription": "REHYDRATING_ANY_time_stop_POSITION_RAISED_KeyError_trigger_r",
        "is_primary": True, "gate": None, "margin": None,
        "evidence": {
            "mechanism": "`_vnext_time_stop_params` (execution.py:1532-1562) correctly returns no "
                         "`trigger_r` — a time stop has no break-even trigger — but :3003 read "
                         "`params[\"trigger_r\"]` unconditionally",
            "blast_radius": "FOUR OF THE FIVE ARMED SLEEVES (crypto, sub_xvol_pullback, fx_jpy, "
                            "sub_mid_dn_revert); only energy_agri is partial_be_runner and its "
                            "params carry the key. 28 of the 34 registered profiles are time_stop.",
            "why_fatal_not_degraded": "book_owner.py:2729 calls hyd(rec) with NO try/except when "
                                      "_live_broker_authority() is true — which it is on both "
                                      "funded accounts. The except TypeError at :2733 guards only "
                                      "the observe-only branch, and a KeyError is not a TypeError.",
            "fix": "fall back to the payload's own gtos_vnext_dynamic_be_trigger_r, which is what "
                   "native_policy_instrumentation (execution_packets.py:172) already wrote — the "
                   "intended value, not an invented one",
            "proved_both_ways": "tests/ultimate_book/test_time_stop_rehydration.py, 14 tests; "
                                "reverting the fix makes exactly the four time_stop sleeves fail "
                                "with KeyError('trigger_r') and leaves energy_agri passing",
            "found_by": "an adversarial pass on THIS session's activation dossier — it is not this "
                        "session's defect and it is pre-existing",
            "consequence_of_the_fix": "the adopt path now REACHES the broker TP modification it "
                                      "previously crashed before. For the armed five that is the "
                                      "intended behaviour and the values are exactly what the "
                                      "packet builder wrote (pinned). It is still a live-behaviour "
                                      "change and needs a deploy decision.",
        },
        "action": "ORCHESTRATOR: this is a live-path fix on armed money. src/components/execution.py "
                  "is unbound by all three seal mechanisms, so no seal exposure — but it needs a "
                  "host deploy to take effect, and the books currently run the pre-fix code.",
        "appended_utc": NOW,
    },
    {
        "session": "AS", "sleeve": "mx_btcusd_d1_donchian_20_breakout",
        "component": "src/components/ultimate_book/execution_packets.py:152-181",
        "verdict": "DEFECT",
        "prescription": "TWO_PRODUCTION_RESOLVERS_AND_ONLY_ONE_HONOURS_final_from_intent",
        "is_primary": False, "gate": None, "margin": None,
        "evidence": {
            "what": "`build_book_trade_params` honours `final_from_intent` (:249-256); "
                    "`native_policy_instrumentation` reads `final_target_r` at :165-166 UNGUARDED",
            "consequence": "under the naive edit the two DISAGREE — 2R at the broker, 5R in the "
                           "rehydration payload that book_owner.py:2724 persists",
            "was_inert_now_reachable": "the divergence could not reach a broker while the hydrator "
                                       "raised KeyError('trigger_r') first. This session fixed that "
                                       "(B1535), so it is now reachable.",
            "mitigation": "the RECOMMENDED Route A (drop final_from_intent) makes both resolvers "
                          "agree at 5.0 — pinned, along with a test that no armed sleeve currently "
                          "sits on the divergence",
            "found_by": "an adversarial pass; this session's first blast-radius instrument drove "
                        "only one of the two resolvers",
        },
        "action": "never land the naive edit. If the cohort's profile is ever edited without "
                  "dropping final_from_intent, the two resolvers diverge silently.",
        "appended_utc": NOW,
    },
    {
        "session": "AS", "sleeve": "__estate__",
        "component": "phase7/receipts/AD_CARRY_TIERS_RESTATED_V1.json",
        "verdict": "DEFECT_IN_A_PUBLISHED_ARTIFACT",
        "prescription": "THE_CARRY_ARTIFACT_MIXES_TWO_ARCHIVES_IN_ONE_ROW",
        "is_primary": False, "gate": None, "margin": None,
        "evidence": {
            "what": "`archive_gross_r_per_trade` comes from the W7 recost cache "
                    "(SURVIVOR_BOOK_V1.json) while `n_archive_trades`, holds and nights come from "
                    "the AA estate walk",
            "size_of_the_disagreement": "for fx_jpy the AA walk's own gross is 0.067174 against the "
                                        "W7 cache's 0.28235 — 4.2x on the SAME sleeve",
            "direction": "every expectancy and floor in this session uses the W7 figure, which is "
                         "the MORE FAVOURABLE of the two. The conservative reading makes fx_jpy's "
                         "expectancy smaller still and its floor asymmetry worse, so no conclusion "
                         "here is at risk from the choice — but the row should name its sources.",
            "found_by": "an adversarial pass",
        },
        "action": "AD's artifact should stamp the source per field. This session's basis carries a "
                  "PROVENANCE_WARNING on the block until it does.",
        "appended_utc": NOW,
    },
    {
        "session": "AS", "sleeve": "__estate__",
        "component": "phase11/receipts/CANDIDATE_FAMILY_V5.json",
        "verdict": "DEFECT_IN_A_PUBLISHED_ARTIFACT",
        "prescription": "THE_FAMILY_ARTIFACTS_HIGH_WATER_FIELDS_DISAGREE_WITH_ITS_OWN_MEMBER_LIST",
        "is_primary": False, "gate": None, "margin": None,
        "evidence": {
            "what": "CANDIDATE_BOOK_V1.high_water_size reads 39 against 48 member rows, and "
                    "high_water_looks reads 36 against 45; the note still says '39 declared, 36 "
                    "looks taken'",
            "and_a_second": "candidate_family.py:100 DECLARATION_CHAIN = (V1, V2) — V3, V4 and V5 "
                            "were never appended, so DEFAULT_DECLARATION still resolves to V2's 35 "
                            "for any caller that does not pass an explicit path",
            "impact_here": "none: this session passes the V5 path explicitly and gates at 48. But a "
                           "caller relying on the default is silently gating at 35, which is the "
                           "cheaper bill.",
            "found_by": "an adversarial pass on this session's re-gate",
        },
        "action": "AU/AV or whoever next touches the family: reconcile the high-water fields with "
                  "the member list and append V3-V5 to DECLARATION_CHAIN.",
        "appended_utc": NOW,
    },
]


def main() -> None:
    before = sum(1 for _ in QUEUE.open()) if QUEUE.is_file() else 0
    existing = set()
    if QUEUE.is_file():
        for line in QUEUE.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                existing.add((r.get("session"), r.get("sleeve"), r.get("prescription")))
    collisions = [r["prescription"] for r in ROWS
                  if (r["session"], r["sleeve"], r["prescription"]) in existing]
    if collisions:
        raise SystemExit(f"these rows already exist — the queue is append-only, not idempotent by "
                         f"accident: {collisions}")
    with QUEUE.open("a") as fh:
        for r in ROWS:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    after = sum(1 for _ in QUEUE.open())
    print(f"{QUEUE.relative_to(REPO)}: {before} -> {after} (+{len(ROWS)}), 0 collisions")
    for r in ROWS:
        print(f"  [{r['verdict']}] {r['sleeve']}: {r['prescription']}")


if __name__ == "__main__":
    main()
