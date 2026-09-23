from __future__ import annotations

import copy
from pathlib import Path

import pytest

from src.research_infra import (
    replay_acceleration_task6_prepared_pack_acceptance as task6,
)
from src.research_infra.replay_prepared_day_pack import seal_prepared_day_pack


def _record(day: str, ordinal: int) -> dict:
    return {
        "schema": "gtos.replay_acceleration.prepared_window.v1",
        "trading_day": day,
        "window_ordinal": ordinal,
        "decision_time_utc": f"{day}T00:{15 * (ordinal + 1):02d}:00+00:00",
        "calendar_no_session_breadth_guard": {"active": False},
        "symbols": [
            {
                "symbol": "XAUUSD",
                "status": "source_skipped",
                "asof_row": {
                    "raw_data_status": (
                        "calendar_no_session_breadth_guard_day_skipped"
                    ),
                    "candidate_count": 0,
                    "decision_time_utc": (
                        f"{day}T00:{15 * (ordinal + 1):02d}:00+00:00"
                    ),
                },
                "mso_payload": None,
                "candidates": [],
            }
        ],
    }


def _bindings(config_root: str = "a" * 64) -> dict:
    return {
        "days": ["2026-01-01"],
        "symbols": ["XAUUSD"],
        "factor_neutral_config_root_sha256": config_root,
        "source_identity_root_sha256": "b" * 64,
        "max_candidates_per_symbol_window": None,
    }


def test_pack_bridge_accepts_byte_identical_records_with_new_factor_root(
    tmp_path: Path,
) -> None:
    old = tmp_path / "old"
    corrected = tmp_path / "corrected"
    old_manifest = seal_prepared_day_pack(
        output_dir=old,
        records=[_record("2026-01-01", 0)],
        bindings=_bindings("a" * 64),
    )
    corrected_manifest = seal_prepared_day_pack(
        output_dir=corrected,
        records=[_record("2026-01-01", 0)],
        bindings=_bindings("c" * 64),
    )

    proof = task6.validate_pack_record_bridge(
        consumed_pack_root=old,
        corrected_pack_root=corrected,
        expected_consumed_pack_root_sha256=old_manifest["pack_root_sha256"],
        expected_corrected_pack_root_sha256=corrected_manifest[
            "pack_root_sha256"
        ],
        expected_factor_neutral_config_root_sha256="c" * 64,
    )

    assert proof["status"] == "EXACT_RECORD_STREAM_BRIDGED_TO_FACTOR_NEUTRAL_PACK"
    assert proof["record_count"] == 1
    assert proof["only_binding_difference"] == (
        "factor_neutral_config_root_sha256"
    )


def test_pack_bridge_rejects_record_or_source_drift(tmp_path: Path) -> None:
    old = tmp_path / "old"
    corrected = tmp_path / "corrected"
    old_manifest = seal_prepared_day_pack(
        output_dir=old,
        records=[_record("2026-01-01", 0)],
        bindings=_bindings(),
    )
    changed = _record("2026-01-01", 0)
    changed["symbols"][0]["asof_row"]["source_marker"] = "changed"
    corrected_manifest = seal_prepared_day_pack(
        output_dir=corrected,
        records=[changed],
        bindings=_bindings("c" * 64),
    )

    with pytest.raises(
        task6.Task6PreparedPackAcceptanceRejected,
        match="task6_pack_record_stream_mismatch",
    ):
        task6.validate_pack_record_bridge(
            consumed_pack_root=old,
            corrected_pack_root=corrected,
            expected_consumed_pack_root_sha256=old_manifest[
                "pack_root_sha256"
            ],
            expected_corrected_pack_root_sha256=corrected_manifest[
                "pack_root_sha256"
            ],
            expected_factor_neutral_config_root_sha256="c" * 64,
        )

    source_changed = tmp_path / "source-changed"
    source_changed_manifest = seal_prepared_day_pack(
        output_dir=source_changed,
        records=[_record("2026-01-01", 0)],
        bindings={**_bindings("c" * 64), "source_identity_root_sha256": "d" * 64},
    )
    with pytest.raises(
        task6.Task6PreparedPackAcceptanceRejected,
        match="task6_pack_binding_difference_unexpected",
    ):
        task6.validate_pack_record_bridge(
            consumed_pack_root=old,
            corrected_pack_root=source_changed,
            expected_consumed_pack_root_sha256=old_manifest[
                "pack_root_sha256"
            ],
            expected_corrected_pack_root_sha256=source_changed_manifest[
                "pack_root_sha256"
            ],
            expected_factor_neutral_config_root_sha256="c" * 64,
        )


def test_exact_file_comparison_rejects_any_byte_or_row_drift(tmp_path: Path) -> None:
    reference = tmp_path / "reference.jsonl"
    corrected = tmp_path / "corrected.jsonl"
    reference.write_bytes(b'{"a":1}\n')
    corrected.write_bytes(reference.read_bytes())
    proof = task6.compare_jsonl_file_exact(
        reference,
        corrected,
        label="source",
    )
    assert proof["row_count"] == 1
    corrected.write_bytes(b'{"a":2}\n')
    with pytest.raises(
        task6.Task6PreparedPackAcceptanceRejected,
        match="task6_source_file_mismatch",
    ):
        task6.compare_jsonl_file_exact(reference, corrected, label="source")


def test_summary_projection_rejects_unclassified_economic_difference() -> None:
    reference = {
        "generated_at_utc": "left",
        "route_id": "left",
        "b7_5_contract_binding": {"implementation": "left"},
        "shared_execution_contract": {"implementation": "left"},
        "source_acceleration_authority": {"implementation": "left"},
        "capacity_safe_chunk_execution_contract": {"runtime": "left"},
        "source_authority_chunk_invariance_contract": {"runtime": "left"},
        "source_authority_preflight_checkpoints": [{"runtime": "left"}],
        "task2_semantic_checkpoint": {"runtime": "left"},
        "progress_rows": [
            {
                "campaign_exact_cache": {"runtime": "left"},
                "candidate_relational_materialization": {},
                "summary": {"cash_pnl": 10.0},
            }
        ],
    }
    accelerated = copy.deepcopy(reference)
    accelerated["generated_at_utc"] = "right"
    accelerated["route_id"] = "right"
    accelerated["progress_rows"][0]["campaign_exact_cache"] = {
        "runtime": "right"
    }
    left, right, classification = task6.project_task6_runtime_envelope_pair(
        reference,
        accelerated,
    )
    assert left == right
    assert classification["causal_or_economic_field_excluded"] is False

    accelerated["progress_rows"][0]["summary"]["cash_pnl"] = 11.0
    left, right, _ = task6.project_task6_runtime_envelope_pair(
        reference,
        accelerated,
    )
    assert left != right


def test_factor_neutral_roots_must_cover_all_four_arms() -> None:
    expected = "a" * 64
    assert task6.validate_four_arm_factor_neutral_roots(
        {arm: expected for arm in ("S0R0", "S1R0", "S0R1", "S1R1")},
        expected_root_sha256=expected,
    )["status"] == "FOUR_ARM_PREPARATION_ROOT_IDENTICAL"
    with pytest.raises(
        task6.Task6PreparedPackAcceptanceRejected,
        match="task6_factor_neutral_root_mismatch:S1R1",
    ):
        task6.validate_four_arm_factor_neutral_roots(
            {
                "S0R0": expected,
                "S1R0": expected,
                "S0R1": expected,
                "S1R1": "b" * 64,
            },
            expected_root_sha256=expected,
        )


def _shared_contract(*, runner_sha: str = "1" * 64) -> dict:
    semantic_payload = {
        "schema": "gtos.final_moonshot.broad_replay.shared_execution_contract.v1",
        "code_authority": [
            {
                "path": (
                    "src/research_infra/"
                    "replay_acceleration_attempt5_typed_sparse_runner.py"
                ),
                "sha256": runner_sha,
            },
            {
                "path": (
                    "src/research_infra/"
                    "v4_timewarp_simulated_live_research_loop.py"
                ),
                "sha256": "2" * 64,
            },
        ],
        "missing_code_paths": [],
        "effective_profile_config_hashes": {
            "repaired_package_conversion_v3": "3" * 64
        },
        "effective_profile_config_hash_semantics": {
            "projection": (
                "execution_semantic_config_excludes_diagnostic_provenance"
            ),
            "excluded_runtime_fields": ["diagnostic_only"],
            "raw_artifact_sha256_retained_in_runtime_and_ledgers": True,
        },
        "config_file_hashes": {"config/agent_config.yaml": "4" * 64},
        "ultimate_package_runtime_input_contract": {
            "valid": True,
            "live_broker_authority": False,
            "broker_mutation_enabled": False,
            "final_selection_claim": False,
        },
        "active_replay_symbol_universe": [f"SYM{i:02d}" for i in range(24)],
        "execution_options": {
            "source_acceleration": {
                "source_plan_digest_sha256": task6.semantic.EXPECTED_SOURCE_PLAN_DIGEST,
                "policy_execution_entered": False,
                "candidate_cache_enabled": False,
                "policy_state_cache_enabled": False,
            }
        },
        "window_identity_excluded_from_shared_digest": True,
        "broker_live_final_authority": {
            "live_broker_authority": False,
            "broker_mutation_enabled": False,
            "final_selection_claim": False,
        },
    }
    return {
        **semantic_payload,
        "exact_profile_config_roots_sha256": {
            "repaired_package_conversion_v3": "5" * 64
        },
        "exact_risk_profile_bindings": {
            "repaired_package_conversion_v3": {
                "path": "config/profiles/ftmo.yaml",
                "sha256": "6" * 64,
            }
        },
        "valid": True,
        "status": "shared_execution_contract_bound",
        "shared_execution_contract_digest_sha256": task6.replay.stable_sha256(
            semantic_payload
        ),
    }


def _rehash_shared_contract(contract: dict) -> None:
    semantic_payload = {
        key: copy.deepcopy(value)
        for key, value in contract.items()
        if key
        not in {
            "exact_profile_config_roots_sha256",
            "exact_risk_profile_bindings",
            "valid",
            "status",
            "shared_execution_contract_digest_sha256",
        }
    }
    contract["shared_execution_contract_digest_sha256"] = (
        task6.replay.stable_sha256(semantic_payload)
    )


def test_shared_contract_validation_recomputes_digest_and_limits_successor_code() -> None:
    consumed = _shared_contract()
    corrected = _shared_contract(runner_sha="7" * 64)
    proof = task6.validate_shared_contract_successor(consumed, corrected)
    assert proof["allowed_code_path_changes"] == [
        "src/research_infra/replay_acceleration_attempt5_typed_sparse_runner.py"
    ]

    digest_tamper = copy.deepcopy(corrected)
    digest_tamper["execution_options"]["new_causal_option"] = True
    with pytest.raises(
        task6.Task6PreparedPackAcceptanceRejected,
        match="task6_shared_contract_digest_invalid",
    ):
        task6.validate_shared_execution_contract(
            digest_tamper,
            label="digest_tamper",
        )


@pytest.mark.parametrize("tamper", ("reducer", "config", "source"))
def test_shared_contract_successor_rejects_causal_code_config_or_source_drift(
    tamper: str,
) -> None:
    consumed = _shared_contract()
    corrected = _shared_contract(runner_sha="7" * 64)
    if tamper == "reducer":
        corrected["code_authority"][1]["sha256"] = "8" * 64
    elif tamper == "config":
        corrected["exact_profile_config_roots_sha256"][
            "repaired_package_conversion_v3"
        ] = "8" * 64
    else:
        corrected["execution_options"]["source_acceleration"][
            "source_plan_digest_sha256"
        ] = "8" * 64
    _rehash_shared_contract(corrected)
    with pytest.raises(
        task6.Task6PreparedPackAcceptanceRejected,
        match="task6_shared_contract_successor_unexpected_difference",
    ):
        task6.validate_shared_contract_successor(consumed, corrected)


def test_acceptance_rejects_unbound_evidence_roots_before_reading(tmp_path: Path) -> None:
    with pytest.raises(
        task6.Task6PreparedPackAcceptanceRejected,
        match="task6_reference_root_unbound",
    ):
        task6.run_acceptance(
            tmp_path / "reference",
            tmp_path / "execution",
            tmp_path / "corrected",
        )
