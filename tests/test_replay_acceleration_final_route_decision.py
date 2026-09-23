from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.research_infra import replay_acceleration_final_route_decision as final_route
from src.research_infra import replay_acceleration_final_route_decision_verifier as verifier


def test_all_bounded_layers_are_accepted_before_final_decision() -> None:
    layers = final_route.load_accepted_layers()

    assert [row["stage"] for row in layers] == list(final_route.STAGE_PATHS)
    assert all(row["status"] == "ACCEPTED" for row in layers)
    assert all(row["gate"] == final_route.STAGE_PATHS[row["stage"]][1] for row in layers)


def test_fastest_tested_safe_route_is_single_worker_without_speedup_claim() -> None:
    decision = final_route.measured_route_decision()

    assert decision["fastest_tested_run_label"] == "cold_w1_a"
    assert decision["immutable_prebarrier_worker_count"] == 1
    assert decision["candidate_generation_worker_count"] == 1
    assert decision["whole_replay_speedup_claim"] is False
    assert decision["warm_speedup_claim"] is False
    assert decision["dominant_stage"] == "all_symbol_snapshot"


def test_golden_availability_probe_is_structural_only() -> None:
    observation = final_route.observe_legacy_golden_availability()

    assert observation["progress_rows_read"] is False
    assert observation["forbidden_output_fields_read"] == []
    assert observation["modified_or_signaled"] is False
    assert observation["expected_output_prefix_present_in_process"] is True
    assert observation["sealed_golden_artifact_count_in_worktree"] == 0


def test_prospective_amendment_remains_non_authoritative() -> None:
    amendment = final_route.build_prospective_amendment()

    assert amendment["status"] == "DRAFT_NOT_AUTHORITY_DO_NOT_EXECUTE"
    assert amendment["successor_arm_authority"] is False
    assert amendment["broker_or_live_authority"] is False
    assert amendment["full_accelerated_s0r0_authority"] is False
    assert amendment["bounded_preprocessing_authority"] is True


def test_final_route_artifacts_are_independently_verified() -> None:
    result_path = final_route.OUTPUT_DIR / "FINAL_ACCELERATION_ROUTE_DECISION.json"
    if not result_path.exists():
        pytest.skip("final decision is materialized by the integration command")

    receipt = verifier.verify_final_route_decision(result_path)
    result = json.loads(result_path.read_bytes())
    assert receipt["status"] == "VERIFIED"
    assert receipt["result_root_sha256"] == result["result_root_sha256"]
    assert result["gate"] == "HUMAN_OR_EXTERNAL_BLOCKER"
    assert result["whole_replay_speedup_claim"] is False
    assert result["successor_arm_execution_launched"] is False


def test_final_verifier_rejects_authority_tamper(tmp_path: Path) -> None:
    result_path = final_route.OUTPUT_DIR / "FINAL_ACCELERATION_ROUTE_DECISION.json"
    if not result_path.exists():
        pytest.skip("final decision is materialized by the integration command")
    tampered = json.loads(result_path.read_bytes())
    tampered["execution_authority"]["successor_arms"] = True
    target = tmp_path / "tampered.json"
    target.write_text(json.dumps(tampered) + "\n", encoding="ascii")
    with pytest.raises(verifier.VerificationError):
        verifier.verify_final_route_decision(target)
