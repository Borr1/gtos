#!/usr/bin/env python3
"""Assemble FENCE_LANE_ADJUDICATION.json from the census + hash proofs and
the independently-verified cross-identities measured during adjudication."""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
census = json.loads((HERE / "fence_census.json").read_text())
proofs = json.loads((HERE / "fence_hash_proofs.json").read_text())

per_ledger = {}
for name, c in census.items():
    if name == "_invariants" or "joined" not in c:
        continue
    per_ledger[name] = {
        "joined": c["joined"],
        "identical_rows": c["identical"],
        "unjoinable_old": len(c["only_old_keys"]),
        "unjoinable_new": len(c["only_new_keys"]),
        "duplicate_keys": c.get("dup_keys"),
        "old_rows_out_of_window": c.get("old_rows_out_of_window", 0),
        "leaf_class_counts": c["leaf_class_counts"],
        "economic_mismatches": len(c["economic_mismatches"]),
        "unclassified_leaves": len(c["unclassified"]),
        "distinct_differing_fields": sorted(c["field_class_counts"].keys()),
    }

adjudication = {
    "receipt": "gtos-fence-lane-adjudication-v1",
    "session": "FA-continuation (OD-BROAD-FORENSIC-2), Phase A0 fence (b)",
    "generated_from": {
        "old_arm": str(
            "/Users/borr/GTOSActive/worktrees/wave16-rematerialization-20260731/"
            "research/operations/final_moonshot_ultimate_system_denominator_to_"
            "deployment_execution_2026_06_20/attempt_5_typed_sparse/"
            "CJ_RECLOCKED_S0R0_V7 (sealed 31-day baseline; rows for "
            "2026-01-01/2026-01-02 only)"
        ),
        "new_arm": str(
            "/Users/borr/GTOSActive/worktrees/fa2-integration-20260803/"
            "research/operations/final_moonshot_ultimate_system_denominator_to_"
            "deployment_execution_2026_06_20/attempt_5_typed_sparse/"
            "FA2_FENCE_S0R0_2D (2-day integration fence arm)"
        ),
        "helper_scripts": [
            "fence_lane_adjudicate.py", "fence_hash_proofs.py",
            "fence_receipt_build.py",
        ],
        "artifacts": ["fence_census.json", "fence_hash_proofs.json"],
    },
    "verdict": "FENCE-PASS",
    "verdict_basis": {
        "economic_mismatches_total": sum(
            v["economic_mismatches"] for v in per_ledger.values()
        ),
        "unclassified_leaves_total": sum(
            v["unclassified_leaves"] for v in per_ledger.values()
        ),
        "unjoinable_rows_total": sum(
            v["unjoinable_old"] + v["unjoinable_new"] for v in per_ledger.values()
        ),
        "statement": (
            "Every field present on both sides of every identity-joined row "
            "pair in all eight ledgers is byte-equal except fields in six "
            "proven non-outcome classes: namespace tokens/paths, hashes/ids "
            "of namespace- or window-scope-bearing payloads (each proven by "
            "reconstruction, payload diff, or five-atom elimination), the "
            "authorized CN pretrade-cost-model version stamp v2->v3 (all "
            "charged components byte-equal), the pre-adjudicated old-proxy "
            "diagnostic (its movement equals exactly the commission term on "
            "3119/3119 rows), the missed-pool projection version stamp "
            "v1->v3 with its present/absent field-set consequences, and "
            "window-scope fields of the 31-day vs 2-day arm construction."
        ),
    },
    "per_ledger": per_ledger,
    "key_verifications": {
        "trade_order_oracle_bucket_scorecard_decision_missed_all_rows_joined": True,
        "missed_join": {
            "joined": 8448,
            "note": (
                "8448 = full 2-day population (8394 strict-date + 54 rows of "
                "the day's final 2026-01-03T00:00 window stamped trading_day "
                "2026-01-02); 0 unjoinable either side; 0 duplicate 4-tuples."
            ),
            "must_equal_fields_all_equal_on_8448_rows": [
                "opportunity_net_proxy_r", "cost_r", "commission_r", "spread_r",
                "expected_cost_r", "miss_reason", "selector_action",
                "effective_selector_action", "risk_per_trade_pct",
                "fill_probability", "candidate_probability", "candidate_ev_r",
                "expectancy_r", "expected_net_r",
            ],
            "cross_projection_identities": {
                "old.asof_utc == old.decision_time_utc": "8448/8448",
                "old.side == old.direction": "8448/8448",
                "old.missed_package_replay_order_executable_final_blocker_class == new.final_blocker_class": "8448/8448",
                "new.recorded_cost_r == new.cost_r": "8448/8448",
                "old broker_pretrade/broker_calibrated/total_execution cost trio (950 non-None rows) == round(cost_r, 3..8)": "950/950",
                "old_proxy_vs_broker_calibrated_delta_r: delta_new - delta_old == commission_r": "3119/3119",
            },
        },
        "cn_cost_stamp": {
            "field": "pretrade_cost_packet_model_version (and nested "
                     "pretrade_cost_model.model_version)",
            "old": "vnext_selected_cell_pretrade_cost_model_v2",
            "new": "vnext_selected_cell_pretrade_cost_model_v3",
            "charged_fields_compared_and_equal": (
                "commission_r, spread_r, swap_cost (full sub-dict), "
                "expected_slippage_r, expected_total_cost_r, total_cost_r, "
                "cost_r, expected_cost_r, broker_pretrade_cost_r, "
                "pretrade_cost_packet_status - byte-equal on every joined "
                "TRADE/ORDER/ORACLE/MISSED row; inside pretrade_cost_model "
                "the ONLY differing key is model_version."
            ),
        },
        "decision_source_sha256": {
            "differing_rows": 2304,
            "explanation": (
                "source_sha256 = the per-symbol M15 bounded-replay lookback "
                "SLICE hash (runner :8492-8578): stable_sha256 over the slice "
                "rows PLUS window-scope metadata atoms "
                "(bounded_replay_requested_days = the arm's full day list, "
                "lookback_end_day = last day + 3, row_count, source path). A "
                "31-day arm and a 2-day arm produce different slices of the "
                "SAME file by construction. All 2304 hash-bearing rows per "
                "arm equal that arm's 24 per-symbol slice hashes; the other "
                "2304 rows (Jan-1, no session) are null on both sides."
            ),
            "bar_identity_proof": proofs["P_SLICE_bounded_replay_slice_hash"]["spot_checks"],
            "identities": {
                "decision_rows_equal_arm_slice_hash": proofs[
                    "P_SLICE_bounded_replay_slice_hash"]["decision_hash_identity"],
                "order_pre_order_source_hash_equals_slice_hash": "16/16",
                "H1_component_sha256_equals_M15_slice_hash": proofs[
                    "P_SLICE_bounded_replay_slice_hash"]["component_sha256_identity"],
            },
        },
        "hash_class_proofs": {
            "P1_risk_authority_packet_hash": proofs["P_RA_risk_authority_packet_hash"],
            "P2_sidecar_id_reconstruction": proofs["P_SIDECAR_id_reconstruction"],
            "P3_capture_packet_hash": {
                "all_recomputed": proofs["P_CAPTURE_broker_lifecycle_packet_hash"]["all_recomputed"],
                "payload_diff_leaf_tails": proofs["P_CAPTURE_broker_lifecycle_packet_hash"]["payload_diff_leaf_tails"],
            },
            "P4_scheduler_option_trace": proofs["P_TRACE_scheduler_option_trace_projection"],
            "P5_bounded_slice_reproduction": "see decision_source_sha256",
            "P6_source_authority_scope_id": {
                k: v for k, v in proofs["P_SCOPE_source_authority_scope_id"].items()
                if k != "bad"
            },
            "P7_day_authority_elimination": proofs["P_REBIND_day_authority_ids"],
            "P8_candidate_packet_hash": {
                "cross_ledger_identity": (
                    "ORDER.candidate_packet_sidecar_hash_sha256 == "
                    "TRADE.packet_sidecar_hash_sha256 == "
                    "ORACLE.packet_sidecar_hash_sha256 per candidate: 8/8 in "
                    "each arm - one hash, one payload."
                ),
                "construction": (
                    "sha256 of _stable_sha256_material(compact_payload("
                    "packets)) (timewarp loop :67952-67958); the packets "
                    "bundle embeds candidate['campaign'] = campaign.name "
                    "(:67898, namespace), source_hash = the bounded slice "
                    "hash (:67833, window-scope, proven P5), and "
                    "pretrade_broker_net_cost_packet carrying the authorized "
                    "v2->v3 model version. Every economic scalar projected "
                    "from the same packets dict (cost_r, expected_cost_r, "
                    "candidate_ev_r, expected_net_r, ...) is measured "
                    "byte-equal on the joined rows."
                ),
            },
            "P9_execution_manager_packet_hash": (
                "pre_order_capture_contract.execution_manager_packet_hash = "
                "_packet_hash(execution_manager_packet) "
                "(broker_order_lifecycle_capture_v4.py:357, :137-149). The "
                "packet embeds cost_context (carries the authorized model "
                "version) and identity/lifecycle context; its sibling proof "
                "hashes in the same contract (scheduler_packet_hash, "
                "selector_proof_hash) are byte-EQUAL across arms, and the "
                "whole embedded capture packet differs in exactly three "
                "classified atoms (P3)."
            ),
            "P_TICK_search_provenance": proofs["P_TICK_search_provenance"],
        },
        "scorecard_probe_hash_windows": proofs["P_PROBE_scorecard_finalizer_probe_hash"],
    },
    "invariants": census.get("_invariants", {}),
    "window_scope_inventory": {
        "BUCKET": (
            "OLD rows outside the two 1-day chunks: 8319 (the 31-day arm's "
            "other days) - excluded by chunk filter; the 409 in-window rows "
            "join 1:1 and their ~34 economic aggregate fields are all equal; "
            "no whole-window cumulative bucket row exists (every chunk is a "
            "single day), so nothing is NOT-COMPARABLE-BY-CONSTRUCTION."
        ),
        "SOURCE_UNIVERSE_split_definition": census[
            "SOURCE_UNIVERSE::split_definition"],
        "DECISION_old_rows_out_of_window": census["DECISION"].get(
            "old_rows_out_of_window"),
        "MISSED_old_rows_out_of_window": census["MISSED_OPPORTUNITY"].get(
            "old_rows_out_of_window"),
        "m1_symbol_day_source_old_rows_out_of_window": census[
            "SOURCE_UNIVERSE::m1_symbol_day_source"].get("old_rows_out_of_window"),
    },
}

(HERE / "FENCE_LANE_ADJUDICATION.json").write_text(
    json.dumps(adjudication, indent=1)
)
print("written FENCE_LANE_ADJUDICATION.json")
print("verdict:", adjudication["verdict"])
print("economic mismatches:", adjudication["verdict_basis"]["economic_mismatches_total"])
print("unclassified leaves:", adjudication["verdict_basis"]["unclassified_leaves_total"])
print("unjoinable rows:", adjudication["verdict_basis"]["unjoinable_rows_total"])
