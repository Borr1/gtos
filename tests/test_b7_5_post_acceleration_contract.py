from __future__ import annotations

import argparse
import ast
from collections import Counter
import copy
import json
from pathlib import Path

import pytest

from src.research_infra import (
    b7_5_post_acceleration_runner as phase_c,
)
from src.research_infra import (
    replay_acceleration_attempt5_typed_sparse_runner as replay,
)


ROOT = Path(__file__).resolve().parents[1]
ROUTE = ROOT / (
    "research/operations/"
    "final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16"
)


def _builder():
    from research.operations.final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16 import (  # noqa: E501
        build_b7_5_post_acceleration_contracts as builder,
    )

    return builder


def _terminal_authority_recovery():
    from research.operations.final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16 import (  # noqa: E501
        repair_b7_5_completed_scorecard_authority as recovery,
    )

    return recovery


def _signed_empty_projection_fixture() -> tuple[dict, dict]:
    from src.research.moonshot_scheduler_v4_best_trade_allocator import (
        stamp_package_new_entry_authority,
    )

    candidate_id = "terminal-empty-projection"
    decision_time = "2026-01-20T13:45:00+00:00"
    source_time = "2026-01-20T13:30:00+00:00"
    instance_key = f"{candidate_id}@@{decision_time}"
    source_boundary = (
        "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
    )
    base = {
        "candidate_id": candidate_id,
        "candidate_id_source": "candidate_id",
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": instance_key,
        "source_bound_replay_candidate_instance_key": instance_key,
        "candidate_instance_identity_status": "materialized",
        "source_bound_package_candidate_use_allowed": True,
        "package_replay_order_executable_candidate_use_allowed": True,
        "package_replay_order_executable_candidate_use_allowed_reason": (
            "unit_authorized"
        ),
        "package_replay_order_executable_authority_source": "unit",
        "expected_net_r": 1.0,
        "probability": 0.8,
        "confidence": 0.8,
        "fill_probability": 0.9,
        "entry_quality_fill_probability": 0.9,
        "source_completeness": 1.0,
        "source_completeness_status": "complete",
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "unit",
            "probability": "unit",
            "confidence": "unit",
            "fill_probability": "unit",
            "source_completeness": "unit",
            "limit_fillability_probability": (
                "predecision_limit_fillability.fill_probability"
            ),
            "execution_fill_probability": (
                "predecision_limit_fillability.fill_probability"
            ),
        },
        "candidate_decision_quality_source_boundary": source_boundary,
        "candidate_decision_quality_alias_status": "exact_materialized",
        "candidate_decision_quality_alias_mismatches": [],
        "candidate_decision_quality_provenance_failures": [],
        "pretrade_cost_packet_status": "PASSED",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "cost_authority": "broker_calibrated_replay_cost",
        "candidate_cost_r_fallback_is_authority": False,
        "expected_cost_r": 0.05,
        "matched_member_axis_ids": ["axis1"],
        "predecision_limit_fillability_probability": 0.9,
        "limit_fillability_probability": 0.9,
        "predecision_limit_fillability": {
            "fill_probability": 0.9,
            "source_boundary": "asof_candidate_fields_only_no_postdecision_path",
            "current_price_source_time_utc": source_time,
        },
        "execution_fill_probability": 0.9,
        "execution_fill_probability_source": "predecision_limit_fillability",
        "execution_fill_probability_source_time_utc": source_time,
        "execution_fill_probability_source_boundary": (
            "asof_candidate_fields_only_no_postdecision_path"
        ),
        "execution_fill_probability_authority_class": (
            "signed_predecision_execution_fillability_authority"
        ),
        "selected_policy_for_expected_net_r": "momentum_exhaustion",
        "selected_policy_expected_net_calibration_status": "calibrated",
        "selected_policy_expected_net_calibrated": True,
        "selected_policy_expected_net_calibration_required": True,
        "selected_policy_expected_net_calibration_source": "unit",
        "selected_policy_expected_net_calibration_source_boundary": source_boundary,
        "selected_policy_expected_net_calibration_hash": "a" * 64,
        "selector_action": "open-reduced-risk",
        "scheduler_materialization_selector_action": "open-reduced-risk",
        "scheduler_materialization_action_intent": "new_position",
        "package_replay_executable_candidate_use_allowed": True,
        "replay_candidate_use_allowed_now": True,
    }
    signed = stamp_package_new_entry_authority(
        base,
        selector_action="open-reduced-risk",
        selector_reason="unit",
        authority={
            "applies": True,
            "allowed": True,
            "authority_family": "unit_test_terminal_signed_authority",
            "authority_source": (
                "derived_from_selected_package_executable_bridge_replay_materialization"
            ),
            "source_boundary": source_boundary,
        },
        action_intent="new_position",
    )
    scorecard = {**base, **signed, "selected_candidate_instance_key": instance_key}
    trade = {
        **scorecard,
        "simulated_order_id": "order-1",
        "simulated_trade_id": "trade-1",
        "package_replay_order_executable_transfer_status": "trade_bound",
        "package_replay_order_executable_bound_order_id": "order-1",
        "package_replay_order_executable_bound_trade_id": "trade-1",
    }
    return scorecard, trade


def test_completed_scorecard_recovery_repairs_only_terminal_authority_projection(
    tmp_path: Path,
) -> None:
    recovery = _terminal_authority_recovery()
    scorecard, trade = _signed_empty_projection_fixture()
    ledgers = {
        "candidate": [],
        "scorecard": [scorecard],
        "order": [],
        "trade": [trade],
    }
    replay.timewarp_loop.reconcile_terminal_package_execution_truth(ledgers)
    replay.normalize_replay_result_ledgers({"ledgers": ledgers})
    replay.normalize_replay_result_ledgers({"ledgers": ledgers})
    assert scorecard["package_new_entry_authority_valid"] is False
    assert any(
        reason.startswith("authority_payload_projection_missing:")
        for reason in (
            replay.timewarp_loop.package_new_entry_authority_immutable_payload_failures(
                scorecard
            )
        )
    )

    scorecard_path = tmp_path / "SCORECARD.jsonl"
    order_path = tmp_path / "ORDER.jsonl"
    trade_path = tmp_path / "TRADE.jsonl"
    scorecard_path.write_text(
        json.dumps(scorecard, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    order_path.write_text("", encoding="utf-8")
    trade_path.write_text(
        json.dumps(trade, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    partial_path = tmp_path / "PARTIAL_SUMMARY.json"
    partial_path.write_text(
        json.dumps(
            {
                "status": "partial_in_progress_not_final_proof",
                "ledger_write_row_counts_so_far": {"scorecard": 1},
                "ledger_file_bytes_flushed_before_partial_summary": {
                    "scorecard": scorecard_path.stat().st_size
                },
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    receipt = recovery.repair_scorecard_authority(
        scorecard_path=scorecard_path,
        order_path=order_path,
        trade_path=trade_path,
    )
    checkpoint = recovery.rebind_partial_scorecard_checkpoint(
        partial_summary_path=partial_path,
        recovery_receipt=receipt,
    )
    repaired = json.loads(scorecard_path.read_text(encoding="utf-8"))
    rebound_partial = json.loads(partial_path.read_text(encoding="utf-8"))

    assert receipt["valid"] is True
    assert receipt["repaired_row_count"] == 1
    assert receipt["non_authority_projection_change_count"] == 0
    assert checkpoint["valid"] is True
    assert rebound_partial["ledger_file_bytes_flushed_before_partial_summary"][
        "scorecard"
    ] == scorecard_path.stat().st_size
    assert repaired["package_new_entry_authority_valid"] is True
    assert repaired["package_new_entry_authority_status"] == (
        "valid_signed_predecision_new_entry_authority"
    )
    assert repaired[
        "package_new_entry_authority_candidate_decision_quality_alias_mismatches"
    ] == []
    assert repaired[
        "package_new_entry_authority_candidate_decision_quality_provenance_failures"
    ] == []
    assert (
        replay.timewarp_loop.package_new_entry_authority_immutable_payload_failures(
            repaired
        )
        == []
    )
    replay.current_summary_v2_contract_for_rows([("scorecard", repaired)])


def test_post_acceleration_decision_contract_is_deterministic_and_outcome_blind() -> None:
    builder = _builder()

    first = builder.build_decision_contract()
    second = builder.build_decision_contract()

    assert first == second
    assert builder.verify_self_hash(first)
    assert first["schema"] == builder.DECISION_SCHEMA
    assert first["status"] == builder.DECISION_STATUS
    assert first["valid"] is True
    assert first["replay_free_builder"] is True
    assert first["run_campaign_call_count"] == 0
    assert first["outcome_ledger_read_count"] == 0
    assert first["outcome_artifact_read_count"] == 0
    assert first["march_outcome_read"] is False
    assert first["predecessor_contract_binding"] == {
        "path": builder.PREDECESSOR_RELATIVE_PATH,
        "file_sha256": builder.PREDECESSOR_FILE_SHA256,
        "self_hash_sha256": builder.PREDECESSOR_SELF_HASH_SHA256,
        "schema": "gtos.b7_5.selection_sizing_decision_contract.v2",
        "status": "SEALED_REPLAY_FREE_DECISION_CONTRACT_VALID",
        "preserved_immutable": True,
        "regeneration_forbidden": True,
    }
    acceleration = first["acceleration_acceptance_binding"]
    assert acceleration["task9_acceptance"]["file_sha256"] == (
        builder.TASK9_ACCEPTANCE_FILE_SHA256
    )
    assert acceleration["task9_acceptance"]["mission_phase_c_authorized"] is True
    assert acceleration["task9_review_rebind"]["file_sha256"] == (
        builder.TASK9_REBIND_FILE_SHA256
    )
    assert acceleration["task9_review_rebind"]["exact_semantic_parity_all_trials"] is True
    assert acceleration["performance_target_pass_claimed"] is False
    assert acceleration["owner_adjusted_correctness_first_continuation"] is True
    assert first["source_plan_authority"]["engineering_june_04"] == (
        "2a5f9e2444a8aebb039f78a7865e70cbffd9797f6da81c7c3172d24108bea434"
    )
    assert first["source_plan_authority"]["development_january"] == (
        "85663876fababc9b69c1bd7041c2bd043b286b456c2e635b2a6fc2289192d4e5"
    )
    arms = first["factorial_contract"]["arms"]
    assert [row["arm_id"] for row in arms] == ["S0R0", "S1R0", "S0R1", "S1R1"]
    assert len({row["arm_fingerprint_sha256"] for row in arms}) == 4
    assert all(row["window_and_outcome_fields_excluded_from_arm_fingerprint"] for row in arms)
    assert first["authority_boundary"] == {
        "decision_contract_only": True,
        "replay_launched": False,
        "outcomes_evaluated": False,
        "broker_live_final_authority": False,
        "broker_mutation_enabled": False,
        "real_order_transmission_possible": False,
    }


def test_post_acceleration_contract_binds_current_accelerator_and_full_runtime() -> None:
    builder = _builder()
    contract = builder.build_decision_contract()
    inputs = {
        row["input_id"]: row
        for group in ("common_behavior_inputs", "package_authority_inputs")
        for row in contract["input_bindings"][group]
    }

    for input_id in (
        "post_acceleration_runner",
        "task2_semantic_acceptance",
        "attempt5_typed_sparse_runner",
        "compact_event_sink",
        "prepared_day_pack",
        "task7_isolated_runner",
        "task9_final_validation",
        "selector_v4",
        "scheduler_v4",
        "execution_manager_v4",
        "broker_net_cost_engine",
        "same_symbol_lifecycle_v4",
        "pending_nofill_lifecycle_v4",
        "exit_policy_v4",
        "cap_lifecycle_repair_audit_r1",
    ):
        assert input_id in inputs
        assert len(inputs[input_id]["sha256"]) == 64
        assert inputs[input_id]["bytes"] > 0

    assert inputs["ultimate_candidate_package_sleeve_registry"]["bytes"] == 205754
    assert inputs["ultimate_candidate_package_member_axis"]["bytes"] == 5995223


def test_attempt5_runtime_accepts_successor_and_rejects_predecessor_chain_tamper(
    tmp_path: Path,
) -> None:
    builder = _builder()
    contract = builder.build_decision_contract()
    contract_path = tmp_path / "B7_5_POST_ACCELERATION_DECISION_CONTRACT.json"
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    arm = contract["factorial_contract"]["arms"][3]
    args = argparse.Namespace(
        decision_contract=contract_path,
        arm_id="S1R1",
        expected_arm_fingerprint_sha256=arm["arm_fingerprint_sha256"],
        runtime_evidence_root=replay.ATTEMPT5_RUNTIME_EVIDENCE_ROOT,
    )

    # Runtime contracts must be inside the repository.  The pure validator is
    # exercised through the final checked-in path below; this temporary copy
    # proves the containment boundary stays fail closed.
    with pytest.raises(ValueError, match="decision_contract_outside_repo"):
        replay.selection_sizing_factorial_binding_from_args(args)

    checked_path = builder.DECISION_OUTPUT_PATH
    if not checked_path.is_file():
        pytest.skip("generated successor contract not present yet")
    checked = json.loads(checked_path.read_text(encoding="utf-8"))
    checked_arm = checked["factorial_contract"]["arms"][3]
    args.decision_contract = checked_path
    args.expected_arm_fingerprint_sha256 = checked_arm["arm_fingerprint_sha256"]
    binding = replay.selection_sizing_factorial_binding_from_args(args)
    assert binding is not None
    assert binding["arm_id"] == "S1R1"
    assert binding["decision_contract_sha256"] == checked["self_hash"]["sha256"]

    tampered = copy.deepcopy(checked)
    tampered["predecessor_contract_binding"]["file_sha256"] = "f" * 64
    tampered["self_hash"]["sha256"] = builder.canonical_self_hash(tampered)
    tampered_path = ROUTE / ".test-tampered-post-acceleration-contract.json"
    try:
        tampered_path.write_text(json.dumps(tampered), encoding="utf-8")
        args.decision_contract = tampered_path
        with pytest.raises(ValueError, match="predecessor_binding_invalid"):
            replay.selection_sizing_factorial_binding_from_args(args)
    finally:
        tampered_path.unlink(missing_ok=True)


def test_execution_seal_separates_decision_self_hash_from_shared_digests() -> None:
    assert phase_c.EXECUTION_SEAL_SCHEMA == (
        "gtos.b7_5.post_acceleration_execution_seal.v1"
    )
    assert phase_c.ARM_ORDER == ("S0R0", "S1R0", "S0R1", "S1R1")
    assert phase_c.RUNNER_OPTIONS["chunk_size"] == 1
    assert phase_c.RUNNER_OPTIONS["compact_event_sink"] is True
    assert phase_c.RUNNER_OPTIONS["prepared_day_pack"] is True
    assert phase_c.RUNNER_OPTIONS["omit_candidate_ledger"] is True
    assert phase_c.RUNNER_OPTIONS["candidate_relational_union"] is True
    assert phase_c.RUNNER_OPTIONS["broker_live_authority"] is False
    assert phase_c.RUNNER_OPTIONS["real_order_transmission_possible"] is False


def test_standard_args_bind_the_selection_sealed_tick_authority(
    tmp_path: Path,
) -> None:
    source_ledger = tmp_path / "SOURCE_UNIVERSE_LEDGER.jsonl"
    source_ledger.write_text("{}\n", encoding="utf-8")
    selection = tmp_path / "selection.json"
    selection.write_text(
        json.dumps(
            {
                "source_ledger": {
                    "path": str(source_ledger),
                    "sha256": phase_c.file_sha256(source_ledger),
                    "byte_count": source_ledger.stat().st_size,
                    "consumed_row_counts": {"tick_symbol_source": 1},
                }
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    args = phase_c.build_standard_args(
        output_dir=tmp_path / "output",
        output_prefix="BROAD_LIVE_AS_IF_REPLAY_B7_5_TICK_AUTHORITY_REGRESSION",
        window_id="development_january",
        start="2026-01-01",
        end="2026-01-31",
        arm_id="S0R0",
        decision_contract_path=_builder().DECISION_OUTPUT_PATH,
        source_bundle_dir=tmp_path / "bundle",
        source_selection_path=selection,
        source_authority_path=tmp_path / "authority.json",
        source_authority_file_sha256="1" * 64,
        source_authority_root_sha256="2" * 64,
        source_bundle_root_sha256="3" * 64,
        source_plan_digest_sha256=(
            "85663876fababc9b69c1bd7041c2bd043b286b456c2e635b2a6fc2289192d4e5"
        ),
        typed_cache_root=tmp_path / "typed-cache",
        tick_sparse_cache_root=tmp_path / "tick-cache",
        prepared_day_pack_root=None,
    )

    assert args.tick_source_manifest is None
    assert args.expected_tick_source_manifest_sha256 is None
    assert args.tick_diagnostic_manifests == []
    assert args.expected_tick_diagnostic_manifest_sha256s == []
    assert args.sealed_tick_source_ledger == source_ledger
    assert args.expected_sealed_tick_source_ledger_sha256 == (
        phase_c.file_sha256(source_ledger)
    )
    assert args.sealed_tick_full_component_set is True


def test_pack_bootstrap_seal_is_accepted_only_for_pack_build(
    tmp_path: Path,
) -> None:
    decision_path = tmp_path / "decision.json"
    decision_path.write_text('{"sealed":true}\n', encoding="utf-8")
    core = {
        "schema": phase_c.PACK_BUILD_SEAL_SCHEMA,
        "status": phase_c.PACK_BUILD_SEAL_STATUS,
        "valid": True,
        "runner_options": copy.deepcopy(phase_c.RUNNER_OPTIONS),
        "decision_contract_binding": {
            "file_sha256": phase_c.file_sha256(decision_path),
        },
        "prepared_day_pack_binding": {
            "required": True,
            "arm_neutral": True,
            "factor_reads_forbidden": True,
            "bootstrap_pack_build_only": True,
            "root_sealed_after_contract_before_first_arm": True,
            "policy_execution_forbidden": True,
        },
        "arms": {"S1R1": {}},
        "pack_build_execution_binding": {
            "arm_id_used_only_for_full_config_construction": "S1R1",
            "shared_execution_contract_digest_sha256": "a" * 64,
            "code_authority_root_sha256": "b" * 64,
            "exact_profile_config_root_sha256": "c" * 64,
            "factorial_binding_payload_sha256": "d" * 64,
            "prepared_day_pack_build_enabled": True,
            "policy_execution_forbidden": True,
        },
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
        "real_order_transmission_possible": False,
        "economic_values_exposed": False,
    }
    seal = {
        **core,
        "pack_build_seal_root_sha256": phase_c.stable_sha256(core),
    }
    seal_path = tmp_path / "pack-bootstrap-seal.json"
    seal_path.write_text(json.dumps(seal), encoding="utf-8")

    assert (
        phase_c.validate_pack_build_seal(
            seal_path,
            decision_contract_path=decision_path,
            arm_id="S1R1",
        )
        == seal
    )
    with pytest.raises(
        phase_c.PostAccelerationRunnerError,
        match="execution_seal_invalid",
    ):
        phase_c.validate_execution_seal(
            seal_path,
            decision_contract_path=decision_path,
            arm_id="S1R1",
        )


def test_pack_build_execution_must_match_the_sealed_build_mode_digest() -> None:
    actual = {
        "arm_id_used_only_for_full_config_construction": "S1R1",
        "shared_execution_contract_digest_sha256": "a" * 64,
        "code_authority_root_sha256": "b" * 64,
        "exact_profile_config_root_sha256": "c" * 64,
        "factorial_binding_payload_sha256": "d" * 64,
        "prepared_day_pack_build_enabled": True,
        "policy_execution_forbidden": True,
    }
    seal = {"pack_build_execution_binding": copy.deepcopy(actual)}

    assert phase_c.validate_pack_build_execution_binding(
        seal=seal,
        actual=actual,
    ) == actual

    drifted = dict(actual)
    drifted["shared_execution_contract_digest_sha256"] = "e" * 64
    with pytest.raises(
        phase_c.PostAccelerationRunnerError,
        match="prepared_pack_build_execution_binding_mismatch",
    ):
        phase_c.validate_pack_build_execution_binding(
            seal=seal,
            actual=drifted,
        )


def test_discover_prepared_pack_roots_uses_canonical_manifest_layout(
    tmp_path: Path,
) -> None:
    packs = tmp_path / "packs"
    pack_root = packs / "development" / "2026-06-04_2026-06-04"
    shard_dir = pack_root / "shards"
    shard_dir.mkdir(parents=True)
    shard_path = shard_dir / "shard-00000.jsonl.zst"
    shard_path.write_bytes(b"x")
    manifest_core = {
        "schema": "gtos.replay_acceleration.prepared_day_pack.v1",
        "status": "SEALED",
        "format": "ordered_canonical_jsonl_shards",
        "compression": "zstd_level_1",
        "max_shard_bytes": 128 * 1024 * 1024,
        "max_record_bytes": 128 * 1024 * 1024,
        "target_raw_shard_bytes": 32 * 1024 * 1024,
        "bindings": {
            "days": ["2026-06-04"],
            "symbols": ["XAUUSD"],
            "factor_neutral_config_root_sha256": "b" * 64,
            "source_identity_root_sha256": "c" * 64,
            "max_candidates_per_symbol_window": 0,
        },
        "window_inventory": [],
        "record_count": 0,
        "ordered_record_root_sha256": "d" * 64,
        "shards": [
            {
                "path": "shards/shard-00000.jsonl.zst",
                "shard_index": 0,
                "row_count": 1,
                "first_record_ordinal": 0,
                "last_record_ordinal": 0,
                "raw_bytes": 1,
                "compressed_bytes": 1,
                "raw_sha256": "e" * 64,
                "compressed_sha256": "f" * 64,
            }
        ],
    }
    expected_root = phase_c.stable_sha256(manifest_core)
    (pack_root / "PREPARED_DAY_PACK_MANIFEST.json").write_text(
        json.dumps(
            {
                **manifest_core,
                "pack_root_sha256": expected_root,
            }
        ),
        encoding="utf-8",
    )
    (pack_root / "SEALED").write_text(f"{expected_root}\n", encoding="ascii")

    assert phase_c.discover_prepared_pack_roots(packs) == {
        ("development", "2026-06-04", "2026-06-04"): expected_root
    }

    (packs / "unexpected.txt").write_text("not pack evidence\n", encoding="utf-8")
    with pytest.raises(
        phase_c.PostAccelerationRunnerError,
        match="prepared_pack_root_tree_invalid",
    ):
        phase_c.discover_prepared_pack_roots(packs)


def test_source_selection_rebind_projection_excludes_only_declared_volatility() -> None:
    partition = {
        "partition_id": "XAUUSD:M1",
        "source_file_sha256": "a" * 64,
        "source_path": "/sealed/XAUUSD_M1.csv",
        "source_stat": {
            "device": 1,
            "inode": 2,
            "byte_count": 3,
            "mtime_ns": 4,
            "ctime_ns": 5,
        },
        "source_identity": {
            "source_file_sha256": "a" * 64,
            "source_stat": {
                "device": 1,
                "inode": 2,
                "byte_count": 3,
                "mtime_ns": 4,
                "ctime_ns": 5,
            },
        },
    }
    predecessor = {
        "schema": "gtos.replay_acceleration.slice_selection.v1",
        "status": "PROSPECTIVE_SOURCE_SELECTION_SEALED",
        "selection_root_sha256": "b" * 64,
        "selection_command": ["python", "select", "--output", "/old/selection.json"],
        "source_stat_identity_contract": {
            "content_identity_fields": ["device", "inode", "byte_count", "mtime_ns"],
            "content_sha256_required": True,
            "observational_noncausal_fields": ["ctime_ns"],
        },
        "physical_partitions": [partition],
        "source_only": True,
        "policy_execution_entered": False,
    }
    current = copy.deepcopy(predecessor)
    current["selection_root_sha256"] = "c" * 64
    current["selection_command"][-1] = "/new/selection.json"
    current["physical_partitions"][0]["source_stat"]["ctime_ns"] = 50
    current["physical_partitions"][0]["source_identity"]["source_stat"][
        "ctime_ns"
    ] = 50

    predecessor_projection = phase_c.source_selection_rebind_projection(
        predecessor
    )
    current_projection = phase_c.source_selection_rebind_projection(current)

    assert predecessor_projection == current_projection
    assert predecessor_projection["physical_partitions"][0]["source_stat"] == {
        "device": 1,
        "inode": 2,
        "byte_count": 3,
        "mtime_ns": 4,
    }

    current["physical_partitions"][0]["source_file_sha256"] = "d" * 64
    assert phase_c.source_selection_rebind_projection(current) != (
        predecessor_projection
    )


def test_prepared_pack_source_identity_binding_preserves_each_day_root() -> None:
    rows = [
        {
            "split": "development",
            "days": ["2026-01-01"],
            "source_identity_root_sha256": "a" * 64,
        },
        {
            "split": "development",
            "days": ["2026-01-02"],
            "source_identity_root_sha256": "b" * 64,
        },
    ]

    binding = phase_c.build_prepared_pack_source_identity_binding(rows)

    assert binding["roots_by_scope"] == {
        "development:2026-01-01:2026-01-01": "a" * 64,
        "development:2026-01-02:2026-01-02": "b" * 64,
    }
    assert binding["scope_count"] == 2
    assert binding["all_scope_roots_explicitly_bound"] is True
    assert binding["binding_root_sha256"] == phase_c.stable_sha256(
        binding["roots_by_scope"]
    )

    with pytest.raises(
        phase_c.PostAccelerationRunnerError,
        match="prepared_pack_source_identity_scope_duplicate",
    ):
        phase_c.build_prepared_pack_source_identity_binding([rows[0], rows[0]])

    invalid = [dict(rows[0], source_identity_root_sha256="not-a-hash")]
    with pytest.raises(
        phase_c.PostAccelerationRunnerError,
        match="prepared_pack_source_identity_root_invalid",
    ):
        phase_c.build_prepared_pack_source_identity_binding(invalid)


def test_execution_seal_requires_exact_pack_source_cross_binding() -> None:
    source = {
        "path": "/authority.json",
        "file_sha256": "a" * 64,
        "authority_root_sha256": "b" * 64,
        "bundle_root_sha256": "c" * 64,
        "selection_root_sha256": "d" * 64,
        "source_plan_digest_sha256": "e" * 64,
        "binding_root_sha256": "f" * 64,
    }
    pack = {"source_authority_binding": copy.deepcopy(source)}

    assert phase_c.validate_pack_source_cross_binding(
        pack_authority=pack,
        execution_source_binding=source,
    ) == source

    drifted = copy.deepcopy(pack)
    drifted["source_authority_binding"]["selection_root_sha256"] = "0" * 64
    with pytest.raises(
        phase_c.PostAccelerationRunnerError,
        match="execution_seal_prepared_pack_source_mismatch",
    ):
        phase_c.validate_pack_source_cross_binding(
            pack_authority=drifted,
            execution_source_binding=source,
        )


def _phase_c_identity_expectations(character: str) -> dict[str, str]:
    return {
        "arm_fingerprint_sha256": character * 64,
        "binding_payload_sha256": chr(ord(character) + 1) * 64,
        "common_execution_input_digest_sha256": chr(ord(character) + 2) * 64,
        "decision_contract_sha256": chr(ord(character) + 3) * 64,
    }


def _phase_c_identity_fields(expectations: dict[str, str]) -> dict[str, str]:
    return {
        "b7_5_selection_sizing_factorial_arm_fingerprint_sha256": expectations[
            "arm_fingerprint_sha256"
        ],
        "b7_5_selection_sizing_factorial_binding_payload_sha256": expectations[
            "binding_payload_sha256"
        ],
        "b7_5_selection_sizing_factorial_common_execution_input_digest_sha256": expectations[
            "common_execution_input_digest_sha256"
        ],
        "b7_5_selection_sizing_factorial_decision_contract_sha256": expectations[
            "decision_contract_sha256"
        ],
    }


def test_phase_c_projection_requires_bound_contract_identities() -> None:
    from src.research_infra import (
        b7_5_post_acceleration_semantic_verifier as verifier,
    )

    expected = _phase_c_identity_expectations("a")
    observed: Counter[str] = Counter()
    row = {
        **_phase_c_identity_fields(expected),
        "b7_5_selection_sizing_factorial_binding": {
            "arm_fingerprint_sha256": expected["arm_fingerprint_sha256"],
            "binding_payload_sha256": expected["binding_payload_sha256"],
            "common_execution_input_digest_sha256": expected[
                "common_execution_input_digest_sha256"
            ],
            "decision_contract_sha256": expected["decision_contract_sha256"],
        },
        "economic_value": 1.25,
    }
    projected = verifier._project_phase_c_row(
        row,
        role="scorecard",
        side_expectations=expected,
        observed=observed,
    )

    assert projected["economic_value"] == 1.25
    assert projected[
        "b7_5_selection_sizing_factorial_arm_fingerprint_sha256"
    ] == verifier.CONTRACT_IDENTITY_SENTINEL
    assert projected["b7_5_selection_sizing_factorial_binding"][
        "decision_contract_sha256"
    ] == verifier.CONTRACT_IDENTITY_SENTINEL

    tampered = copy.deepcopy(row)
    tampered["b7_5_selection_sizing_factorial_binding"][
        "decision_contract_sha256"
    ] = "f" * 64
    with pytest.raises(verifier.PhaseCSemanticError, match="unbound_contract_identity"):
        verifier._project_phase_c_row(
            tampered,
            role="scorecard",
            side_expectations=expected,
            observed=Counter(),
        )


def test_phase_c_source_projection_removes_only_bound_discovery_transport() -> None:
    from src.research_infra import (
        b7_5_post_acceleration_semantic_verifier as verifier,
    )

    expected = _phase_c_identity_expectations("a")
    parent: list[dict] = []
    successor: list[dict] = []
    for index in range(24):
        symbol = f"S{index:02d}"
        common = {
            **_phase_c_identity_fields(expected),
            "symbol": symbol,
            "trading_day": "2026-06-04",
            "timeframe": "M1",
            "evidence_class": "source_bound_asof_timewarp_decision_input",
            "source_truth_scope": (
                "ordered_price_path_only_not_broker_order_lifecycle_truth"
            ),
            "source_path": f"/accepted/{symbol}.csv",
            "live_broker_authority": False,
            "broker_mutation_enabled": False,
        }
        parent.append(
            {
                **common,
                "row_type": "m1_source_overlap_validation",
                "status": "m1_source_overlap_consistent",
                "candidate_source_paths": [
                    f"/accepted/{symbol}.csv",
                    f"/equivalent/{symbol}.csv",
                ],
                "candidate_day_sha256": "e" * 64,
            }
        )
        selected = {
            **common,
            "row_type": "m1_symbol_day_source",
            "status": "selected_day_source_meets_absolute_floor",
            "source_overlap_consistent": True,
            "sha256": "f" * 64,
        }
        parent.append(
            {
                **selected,
                "candidate_source_count": 2,
                "populated_candidate_source_count": 2,
            }
        )
        successor.append(
            {
                **selected,
                "candidate_source_count": 1,
                "populated_candidate_source_count": 1,
            }
        )

    left, left_receipt = verifier._project_source_rows(
        parent,
        side="parent",
        expectations=expected,
    )
    right, right_receipt = verifier._project_source_rows(
        successor,
        side="successor",
        expectations=expected,
    )

    assert left == right
    assert left_receipt["raw_row_count"] == 48
    assert left_receipt["excluded_overlap_diagnostic_row_count"] == 24
    assert right_receipt["raw_row_count"] == 24
    assert right_receipt["excluded_overlap_diagnostic_row_count"] == 0


def test_phase_c_capped_conflict_projection_keeps_count_and_keys_causal() -> None:
    from src.research_infra import (
        b7_5_post_acceleration_semantic_verifier as verifier,
    )

    expected = _phase_c_identity_expectations("a")
    row = {
        **_phase_c_identity_fields(expected),
        "probability": 0.75,
        "risk_finalizer_stale_surface_conflict_count": 1,
        "risk_finalizer_stale_surface_conflict_keys": ["probability"],
        "risk_finalizer_stale_surface_conflicts": [
            {
                "key": "probability",
                "canonical_source": "scheduler_decision_inputs",
                "stale_source": "candidate",
                "canonical_value": 0.75,
                "stale_value": 0.5,
            }
        ],
    }
    projected = verifier._project_phase_c_row(
        row,
        role="scorecard",
        side_expectations=expected,
        observed=Counter(),
    )

    assert projected["risk_finalizer_stale_surface_conflict_count"] == 1
    assert projected["risk_finalizer_stale_surface_conflict_keys"] == ["probability"]
    assert projected["risk_finalizer_stale_surface_conflicts"] == (
        verifier.CAPPED_DIAGNOSTIC_SENTINEL
    )

    tampered = copy.deepcopy(row)
    tampered["risk_finalizer_stale_surface_conflicts"][0]["canonical_value"] = 0.9
    with pytest.raises(
        verifier.PhaseCSemanticError,
        match="capped_conflict_canonical_value_mismatch",
    ):
        verifier._project_phase_c_row(
            tampered,
            role="scorecard",
            side_expectations=expected,
            observed=Counter(),
        )

    explicit_alias = {
        **_phase_c_identity_fields(expected),
        "package_replay_executable_candidate_use_allowed_reason": (
            "broker_cost_and_scheduler_action_executable"
        ),
        "risk_finalizer_stale_surface_conflict_count": 1,
        "risk_finalizer_stale_surface_conflict_keys": [
            "replay_candidate_use_allowed_now_reason"
        ],
        "risk_finalizer_stale_surface_conflicts": [
            {
                "key": "replay_candidate_use_allowed_now_reason",
                "canonical_source": "scheduler_decision_inputs",
                "stale_source": "candidate",
                "canonical_value": "broker_cost_and_scheduler_action_executable",
                "stale_value": "selector_not_risk_bearing",
            }
        ],
    }
    alias_observed: Counter[str] = Counter()
    verifier._project_phase_c_row(
        explicit_alias,
        role="scorecard",
        side_expectations=expected,
        observed=alias_observed,
    )
    assert (
        alias_observed[
            "capped_conflict_diagnostic:chain_connected_tuple_count"
        ]
        == 1
    )

    tampered_alias = copy.deepcopy(explicit_alias)
    tampered_alias["risk_finalizer_stale_surface_conflicts"][0][
        "canonical_value"
    ] = "different_executable_reason"
    with pytest.raises(
        verifier.PhaseCSemanticError,
        match="capped_conflict_canonical_value_mismatch",
    ):
        verifier._project_phase_c_row(
            tampered_alias,
            role="scorecard",
            side_expectations=expected,
            observed=Counter(),
        )


def test_phase_c_window_binding_is_canonical_and_rejects_aliases() -> None:
    decision = json.loads(
        (ROUTE / "B7_5_POST_ACCELERATION_DECISION_CONTRACT.json").read_text(
            encoding="utf-8"
        )
    )
    expected = phase_c.resolve_canonical_window_binding(
        decision,
        window_id="engineering_june_04",
        start="2026-06-04",
        end="2026-06-04",
        source_plan_digest_sha256=(
            "2a5f9e2444a8aebb039f78a7865e70cbffd9797f6da81c7c3172d24108bea434"
        ),
    )
    assert expected["window_id"] == "engineering_june_04"

    with pytest.raises(
        phase_c.PostAccelerationRunnerError,
        match="execution_window_not_canonical",
    ):
        phase_c.resolve_canonical_window_binding(
            decision,
            window_id="engineering_june_04_2026",
            start="2026-06-04",
            end="2026-06-04",
            source_plan_digest_sha256=(
                "2a5f9e2444a8aebb039f78a7865e70cbffd9797f6da81c7c3172d24108bea434"
            ),
        )


@pytest.mark.parametrize(
    "prefix",
    (
        "../BROAD_LIVE_AS_IF_REPLAY_B7_5_ESCAPE",
        "/tmp/BROAD_LIVE_AS_IF_REPLAY_B7_5_ESCAPE",
        "BROAD_LIVE_AS_IF_REPLAY_B7_5_..",
        "BROAD_LIVE_AS_IF_REPLAY_B7_5_BAD/CHILD",
        "BROAD_LIVE_AS_IF_REPLAY_B7_5_BAD\\CHILD",
    ),
)
def test_phase_c_output_prefix_rejects_namespace_escape(prefix: str) -> None:
    with pytest.raises(
        phase_c.PostAccelerationRunnerError,
        match="post_acceleration_prefix_invalid",
    ):
        phase_c.validate_output_prefix(prefix)


def test_phase_c_output_namespace_must_be_fresh_and_attempt5_owned(
    tmp_path: Path,
) -> None:
    outside = tmp_path / "PHASE_C_OUTSIDE"
    with pytest.raises(
        phase_c.PostAccelerationRunnerError,
        match="post_acceleration_output_namespace_outside_attempt5",
    ):
        phase_c.validate_fresh_output_namespace(outside)

    existing = replay.ATTEMPT5_NAMESPACE_ROOT / ".phase-c-existing-test"
    existing.mkdir(parents=True, exist_ok=True)
    try:
        with pytest.raises(
            phase_c.PostAccelerationRunnerError,
            match="post_acceleration_output_namespace_not_fresh",
        ):
            phase_c.validate_fresh_output_namespace(existing)
    finally:
        existing.rmdir()


def test_phase_c_arm_inventory_is_complete_and_summary_reconciled(
    tmp_path: Path,
) -> None:
    prefix = "BROAD_LIVE_AS_IF_REPLAY_B7_5_TEST"
    row_counts = {
        "source": 1,
        "decision": 1,
        "scorecard": 1,
        "order": 1,
        "trade": 1,
        "oracle": 1,
        "missed": 1,
        "bucket": 1,
        "comparison": 0,
    }
    for role, suffix in phase_c.ARM_ARTIFACT_SUFFIXES.items():
        path = tmp_path / f"{prefix}{suffix}"
        if role in row_counts:
            path.write_text(
                "" if row_counts[role] == 0 else '{"row":1}\n',
                encoding="utf-8",
            )
        elif role == "partial_summary":
            path.write_text(
                json.dumps({"status": "partial_in_progress_not_final_proof"}),
                encoding="utf-8",
            )
        else:
            path.write_text(
                json.dumps(
                        {
                            "status": phase_c.COMPLETED_REPLAY_STATUS,
                            "date_start": "2026-06-04",
                            "date_end": "2026-06-04",
                            "ledger_write_row_counts": row_counts,
                            "live_broker_authority": False,
                            "broker_mutation_enabled": False,
                            "profiles": ["repaired_package_conversion_v3"],
                            "profile_count": 1,
                            "order_send_attempts": {
                                "repaired_package_conversion_v3": 0
                            },
                        }
                ),
                encoding="utf-8",
            )

    inventory = phase_c.build_arm_artifact_inventory(
        namespace=tmp_path,
        output_prefix=prefix,
        start="2026-06-04",
        end="2026-06-04",
    )
    assert inventory["all_expected_artifacts_present"] is True
    assert inventory["completed_summary_status"] == phase_c.COMPLETED_REPLAY_STATUS
    assert inventory["ledger_row_counts"] == row_counts
    assert inventory["zero_real_order_send_attempts_reconciled"] is True

    summary_path = (
        tmp_path
        / f"{prefix}{phase_c.ARM_ARTIFACT_SUFFIXES['summary']}"
    )
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["order_send_attempts"]["repaired_package_conversion_v3"] = 1
    summary_path.write_text(json.dumps(summary), encoding="utf-8")
    with pytest.raises(
        phase_c.PostAccelerationRunnerError,
        match="arm_completed_summary_reconciliation_invalid",
    ):
        phase_c.build_arm_artifact_inventory(
            namespace=tmp_path,
            output_prefix=prefix,
            start="2026-06-04",
            end="2026-06-04",
        )
    summary["order_send_attempts"]["repaired_package_conversion_v3"] = 0
    summary_path.write_text(json.dumps(summary), encoding="utf-8")

    (tmp_path / f"{prefix}_UNKNOWN.json").write_text("{}", encoding="utf-8")
    with pytest.raises(
        phase_c.PostAccelerationRunnerError,
        match="post_acceleration_output_artifact_set_invalid",
    ):
        phase_c.build_arm_artifact_inventory(
            namespace=tmp_path,
            output_prefix=prefix,
            start="2026-06-04",
            end="2026-06-04",
        )


def test_phase_c_pack_authority_rejects_caller_manifest_root_tamper(
    tmp_path: Path,
) -> None:
    pack_root = tmp_path / "packs"
    manifest_dir = pack_root / "holdout" / "2026-06-04_2026-06-04"
    shard_dir = manifest_dir / "shards"
    shard_dir.mkdir(parents=True)
    (shard_dir / "shard-00000.jsonl.zst").write_bytes(b"x")
    manifest_path = manifest_dir / "PREPARED_DAY_PACK_MANIFEST.json"
    manifest_core = {
        "schema": "gtos.replay_acceleration.prepared_day_pack.v1",
        "status": "SEALED",
        "format": "ordered_canonical_jsonl_shards",
        "compression": "zstd_level_1",
        "max_shard_bytes": 128 * 1024 * 1024,
        "max_record_bytes": 128 * 1024 * 1024,
        "target_raw_shard_bytes": 32 * 1024 * 1024,
        "bindings": {
            "days": ["2026-06-04"],
            "symbols": ["XAUUSD"],
            "factor_neutral_config_root_sha256": "c" * 64,
            "source_identity_root_sha256": "d" * 64,
            "max_candidates_per_symbol_window": 0,
        },
        "window_inventory": [],
        "record_count": 0,
        "ordered_record_root_sha256": "e" * 64,
        "shards": [
            {
                "path": "shards/shard-00000.jsonl.zst",
                "shard_index": 0,
                "row_count": 1,
                "first_record_ordinal": 0,
                "last_record_ordinal": 0,
                "raw_bytes": 1,
                "compressed_bytes": 1,
                "raw_sha256": "f" * 64,
                "compressed_sha256": "0" * 64,
            }
        ],
    }
    actual_root = phase_c.stable_sha256(manifest_core)
    manifest_path.write_text(
        json.dumps(
            {
                **manifest_core,
                "pack_root_sha256": actual_root,
            }
        ),
        encoding="utf-8",
    )
    (manifest_dir / "SEALED").write_text(
        f"{actual_root}\n",
        encoding="ascii",
    )
    authority = {
        "prepared_day_pack_root": str(pack_root.resolve()),
        "prepared_day_pack_roots": {
            "holdout:2026-06-04:2026-06-04": "b" * 64
        },
    }
    with pytest.raises(
        phase_c.PostAccelerationRunnerError,
        match="prepared_pack_authority_manifest_root_mismatch",
    ):
        phase_c.validate_prepared_pack_authority_manifest_roots(authority)


def test_phase_c_hash_closure_rejects_cross_ledger_alias_tamper() -> None:
    from src.research_infra import (
        b7_5_post_acceleration_semantic_verifier as verifier,
    )

    key = "candidate@@2026-06-04T01:00:00Z"
    base = {
        "canonical_replay_candidate_instance_key": key,
        "candidate_id": "candidate",
        "decision_time_utc": "2026-06-04T01:00:00Z",
        "candidate_packet_sidecar_hash_sha256": "a" * 64,
        "risk_authority_packet_hash_sha256": "b" * 64,
    }
    rows = {
        "missed": [],
        "order": [base],
        "trade": [dict(base)],
        "oracle": [dict(base)],
        "scorecard": [],
    }
    state = verifier._collect_phase_c_hash_alias_state(rows, side="successor")
    assert state["selected_identity_count"] == 1

    tampered = copy.deepcopy(rows)
    tampered["trade"][0]["candidate_packet_sidecar_hash_sha256"] = "c" * 64
    with pytest.raises(
        verifier.PhaseCSemanticError,
        match="candidate_packet_alias_mismatch",
    ):
        verifier._collect_phase_c_hash_alias_state(tampered, side="successor")


def test_phase_c_hash_producer_binding_is_format_independent() -> None:
    from src.research_infra import (
        b7_5_post_acceleration_semantic_verifier as verifier,
    )

    valid = ast.parse(
        """
def evaluate_symbol_candidates_with_batched_proof_hashes(campaign, packets, executor):
    for candidate, packets, future in pending:
        packet_sidecar_material = _stable_sha256_material(
            compact_payload(
                packets,
                max_bytes=campaign.candidate_ledger_packet_max_bytes,
            )
        ).encode("utf-8")
        packet_sidecar_future = executor.submit(
            _sha256_hexdigest,
            packet_sidecar_material,
        )
"""
    )
    wrong_input = ast.parse(
        """
def evaluate_symbol_candidates_with_batched_proof_hashes(
    campaign, other_packets, executor
):
    for candidate, other_packets, future in pending:
        packet_sidecar_material = _stable_sha256_material(
            compact_payload(
                other_packets,
                max_bytes=campaign.candidate_ledger_packet_max_bytes,
            )
        ).encode("utf-8")
        packet_sidecar_future = executor.submit(
            _sha256_hexdigest,
            packet_sidecar_material,
        )
"""
    )
    nested_but_unselected = ast.parse(
        """
def evaluate_symbol_candidates_with_batched_proof_hashes(campaign, packets, executor):
    for candidate, packets, future in pending:
        packet_sidecar_material = (
            _stable_sha256_material(
                compact_payload(
                    packets,
                    max_bytes=campaign.candidate_ledger_packet_max_bytes,
                )
            ),
            malicious_material,
        )[1].encode("utf-8")
        packet_sidecar_future = executor.submit(
            _sha256_hexdigest,
            packet_sidecar_material,
        )
"""
    )
    extra_keyword = ast.parse(
        """
def evaluate_symbol_candidates_with_batched_proof_hashes(campaign, packets, executor):
    for candidate, packets, future in pending:
        packet_sidecar_material = _stable_sha256_material(
            compact_payload(
                packets,
                max_bytes=campaign.candidate_ledger_packet_max_bytes,
                unsafe=True,
            )
        ).encode("utf-8")
        packet_sidecar_future = executor.submit(
            _sha256_hexdigest,
            packet_sidecar_material,
        )
"""
    )
    reassigned = ast.parse(
        """
def evaluate_symbol_candidates_with_batched_proof_hashes(campaign, packets, executor):
    for candidate, packets, future in pending:
        packet_sidecar_material = _stable_sha256_material(
            compact_payload(
                packets,
                max_bytes=campaign.candidate_ledger_packet_max_bytes,
            )
        ).encode("utf-8")
        packet_sidecar_material = malicious_material
        packet_sidecar_future = executor.submit(
            _sha256_hexdigest,
            packet_sidecar_material,
        )
"""
    )
    dead_decoy = ast.parse(
        """
def decoy(campaign, packets):
    packet_sidecar_material = _stable_sha256_material(
        compact_payload(
            packets,
            max_bytes=campaign.candidate_ledger_packet_max_bytes,
        )
    ).encode("utf-8")

def evaluate_symbol_candidates_with_batched_proof_hashes(campaign, packets, executor):
    for candidate, packets, future in pending:
        packet_sidecar_material = malicious_material
        packet_sidecar_future = executor.submit(
            _sha256_hexdigest,
            packet_sidecar_material,
        )
"""
    )
    inner_function_decoy = ast.parse(
        """
def evaluate_symbol_candidates_with_batched_proof_hashes(campaign, packets, executor):
    def decoy(campaign, packets, executor):
        for candidate, packets, future in pending:
            packet_sidecar_material = _stable_sha256_material(
                compact_payload(
                    packets,
                    max_bytes=campaign.candidate_ledger_packet_max_bytes,
                )
            ).encode("utf-8")
            packet_sidecar_future = executor.submit(
                _sha256_hexdigest,
                packet_sidecar_material,
            )
    for candidate, packets, future in pending:
        packet_sidecar_material = malicious_material
        packet_sidecar_future = executor.submit(
            _sha256_hexdigest,
            packet_sidecar_material,
        )
"""
    )
    dead_branch_decoy = ast.parse(
        """
def evaluate_symbol_candidates_with_batched_proof_hashes(campaign, packets, executor):
    for candidate, packets, future in pending:
        if False:
            packet_sidecar_material = _stable_sha256_material(
                compact_payload(
                    packets,
                    max_bytes=campaign.candidate_ledger_packet_max_bytes,
                )
            ).encode("utf-8")
            packet_sidecar_future = executor.submit(
                _sha256_hexdigest,
                packet_sidecar_material,
            )
        packet_sidecar_material = malicious_material
        packet_sidecar_future = executor.submit(
            _sha256_hexdigest,
            packet_sidecar_material,
        )
"""
    )

    assert verifier._has_packet_sidecar_material_compact_packets_call(valid)
    for rejected in (
        wrong_input,
        nested_but_unselected,
        extra_keyword,
        reassigned,
        dead_decoy,
        inner_function_decoy,
        dead_branch_decoy,
    ):
        assert not verifier._has_packet_sidecar_material_compact_packets_call(
            rejected
        )
    # The AST predicate above is what "format independent" means and is the subject of this
    # test. The end-to-end contract call additionally requires the PRODUCER FILE to be at its
    # sealed bytes, and `v4_timewarp_simulated_live_research_loop.py` is one of the
    # owner-authorized forward R2 breaks (CLAUDE.md §4; the same six paths are enumerated with
    # their authority in `tests/test_b7_5_post_acceleration_contract_r2_verification_split.py`
    # :: AUTHORIZED_FORWARD_BREAKS). So assert the contract's behaviour in whichever state the
    # tree is in -- bound when sealed, and failing CLOSED with the specific code when not,
    # which is the verifier working rather than the verifier broken.
    import hashlib
    import json as _json

    producer = verifier.ROOT / "src/research_infra/v4_timewarp_simulated_live_research_loop.py"
    sealed = {
        row.get("input_id"): row.get("sha256")
        for row in _json.loads(verifier.DECISION_CONTRACT_PATH.read_bytes())
        .get("input_bindings", {})
        .get("common_behavior_inputs", [])
    }.get("v4_timewarp_reducer")
    at_sealed_bytes = hashlib.sha256(producer.read_bytes()).hexdigest() == sealed

    if at_sealed_bytes:
        assert (
            verifier._phase_c_historical_hash_noncausal_contract()["status"]
            == "PHASE_C_HISTORICAL_HASH_ONLY_NONCAUSAL_PRODUCER_BOUND"
        )
    else:
        with pytest.raises(
            verifier.PhaseCSemanticError, match="historical_hash_producer_contract_changed"
        ):
            verifier._phase_c_historical_hash_noncausal_contract()
        # ...and it is the SHA that moved, not one of the structural clauses -- otherwise the
        # producer's shape changed and the authorized-break story does not cover it.
        source = producer.read_text(encoding="utf-8")
        for clause in (
            "packet_sidecar_omitted_compact_broad_replay_hash_only",
            '"payload_hash_sha256": stable_sha256(payload)',
            'packet["packet_hash_sha256"] = stable_sha256(packet)',
        ):
            assert clause in source, f"the producer lost {clause!r}, which is not a re-seal"


def test_phase_c_summary_field_classification_rejects_unknown_difference() -> None:
    from src.research_infra import (
        b7_5_post_acceleration_semantic_verifier as verifier,
    )

    receipt = verifier._classify_summary_fields(
        {"status": phase_c.COMPLETED_REPLAY_STATUS, "candidate_rows": 1},
        {"status": phase_c.COMPLETED_REPLAY_STATUS, "candidate_rows": 1},
    )
    assert receipt["unknown_difference_count"] == 0

    with pytest.raises(
        verifier.PhaseCSemanticError,
        match="summary_unknown_successor_field",
    ):
        verifier._classify_summary_fields(
            {"status": phase_c.COMPLETED_REPLAY_STATUS, "candidate_rows": 1},
            {
                "status": phase_c.COMPLETED_REPLAY_STATUS,
                "candidate_rows": 1,
                "unclassified_runtime_value": 2,
            },
        )


def test_top_level_research_package_survives_src_on_sys_path() -> None:
    """`import research.operations...` must keep working with `<repo>/src` on the path.

    This module reaches its contract-construction authority through
    `research.operations.final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16`
    (`:28`, `:36`). `<repo>/research` is a *namespace* package. Until 2026-07-27
    `<repo>/src/research/__init__.py` made `src/research` a **regular** package,
    and a regular package always wins the sys.path scan over namespace portions —
    order-independently. Four test modules put `<repo>/src` on `sys.path` at import
    time (`tests/research_infra/test_vig_perm_null.py:20`, `test_vig_regime_inflation.py:23`,
    `test_vig_trial_budget.py:17`, `test_validation_integrity_gauntlet.py:36`), so
    whenever one of them ran first in a process, every `research.operations` import
    in this file raised `ModuleNotFoundError` for the rest of that process.
    Measured: 1 failed / 26 passed alone, 5 failed / 30 passed after one poisoner.

    Subprocess, because `research` is already imported in the pytest process and
    the shadowing is decided at first import. Both spellings are asserted: the
    top-level route namespace **and** `src.research.*`, which is what the replay
    runtime imports and what the R2 contract binds.
    """
    import subprocess
    import sys

    probe = (
        "import sys;"
        f" sys.path.insert(0, {str(ROOT)!r});"
        f" sys.path.insert(0, {str(ROOT / 'src')!r});"
        " import research.operations."
        "final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16 as route;"
        " import src.research.moonshot_scheduler_v4_best_trade_allocator as alloc;"
        " print('ROUTE_OK', route.__name__);"
        " print('ALLOC_OK', alloc.__file__)"
    )
    done = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=str(ROOT), capture_output=True, text=True, timeout=300,
    )
    assert done.returncode == 0, (
        "`<repo>/src` on sys.path shadowed the top-level `research` namespace "
        f"package again; stderr={done.stderr!r}"
    )
    assert "ROUTE_OK" in done.stdout, done.stdout
    assert "ALLOC_OK" in done.stdout, done.stdout
