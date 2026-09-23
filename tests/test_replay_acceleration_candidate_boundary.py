from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.research_infra import replay_acceleration_candidate_boundary as boundary
from src.research_infra import replay_acceleration_candidate_boundary_verifier as verifier


ARMS = ("S0R0", "S1R0", "S0R1", "S1R1")


def test_four_arm_candidate_probe_is_nonempty_equal_and_factor_free() -> None:
    receipt = boundary.probe_candidate_boundary()

    assert tuple(receipt["arm_order"]) == ARMS
    roots = {
        receipt["arms"][arm]["candidate_base_root_sha256"] for arm in ARMS
    }
    read_sets = {
        tuple(receipt["arms"][arm]["candidate_base_config_read_set"])
        for arm in ARMS
    }
    assert len(roots) == 1
    assert len(read_sets) == 1
    assert receipt["candidate_base_count"] > 0
    assert receipt["candidate_base_factor_read_intersection"] == []
    assert receipt["shared_boundary_stage"] == "candidate_base_materialized"
    assert receipt["cross_symbol_barrier_required"] is True


def test_scheduler_factor_probe_forces_factor_and_state_stages_arm_local() -> None:
    receipt = boundary.probe_candidate_boundary()

    for arm in ARMS:
        arm_receipt = receipt["arms"][arm]
        assert arm_receipt["factor_binding_valid"] is True
        assert arm_receipt["scheduler_factor_read_set"]
        assert arm_receipt["scheduler_factor_projection_sha256"]
    assert receipt["stage_classification"] == {
        "normalized_source": "shared_immutable",
        "closed_bar_snapshot": "shared_before_cross_symbol_barrier",
        "candidate_origin_generation": "shared_after_read_set_and_root_equality",
        "candidate_base_materialization": "shared_after_read_set_and_root_equality",
        "candidate_evaluation": "arm_local",
        "scheduler_eligibility": "arm_local",
        "risk_and_order_materialization": "arm_local",
        "portfolio_lifecycle": "arm_local",
    }
    assert receipt["mutable_state_surfaces"] == [
        "account",
        "open_positions",
        "pending_orders",
        "reservations",
    ]
    assert receipt["successor_arm_execution_launched"] is False


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        ({"cross_symbol_barrier_required": False}, "cross_symbol_barrier_missing"),
        ({"candidate_roots_equal": False}, "candidate_base_root_mismatch"),
        ({"candidate_read_sets_equal": False}, "candidate_base_read_set_mismatch"),
        ({"candidate_factor_reads": ["factor.path"]}, "candidate_factor_read_detected"),
        ({"mutable_state_read": True}, "candidate_mutable_state_read_detected"),
    ],
)
def test_shareability_contract_rejects_unsafe_boundary(
    mutation: dict[str, object], code: str
) -> None:
    facts: dict[str, object] = {
        "cross_symbol_barrier_required": True,
        "candidate_roots_equal": True,
        "candidate_read_sets_equal": True,
        "candidate_factor_reads": [],
        "mutable_state_read": False,
    }
    facts.update(mutation)
    with pytest.raises(boundary.CandidateBoundaryError, match=f"^{code}$"):
        boundary.enforce_candidate_base_shareability(**facts)


def test_independent_verifier_consumes_persisted_bytes(tmp_path: Path) -> None:
    result_path = tmp_path / "result.json"
    result = boundary.write_candidate_boundary_result(result_path)
    verified = verifier.verify_candidate_boundary_result(result_path)

    assert verified["status"] == "VERIFIED"
    assert verified["result_root_sha256"] == result["result_root_sha256"]

    tampered = json.loads(result_path.read_text(encoding="utf-8"))
    tampered["candidate_probe"]["shared_boundary_stage"] = "scheduler_eligibility"
    result_path.write_text(json.dumps(tampered) + "\n", encoding="utf-8")
    with pytest.raises(verifier.VerificationError, match="result_root_mismatch"):
        verifier.verify_candidate_boundary_result(result_path)


def test_production_failure_injection_matrix_is_complete() -> None:
    verdicts = boundary.run_candidate_boundary_failure_injections()
    assert len(verdicts) == 5
    assert {item["status"] for item in verdicts} == {"REJECTED_AS_REQUIRED"}
