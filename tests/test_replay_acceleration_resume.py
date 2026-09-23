from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.research_infra import replay_acceleration_resume as resume
from src.research_infra import replay_acceleration_resume_verifier as verifier


ARMS = ("S0R0", "S1R0", "S0R1", "S1R1")


def test_resume_scenarios_converge_and_bound_unsealed_loss(tmp_path: Path) -> None:
    result_path = resume.write_resume_result(tmp_path)
    result = json.loads(result_path.read_text(encoding="utf-8"))

    assert result["gate"] == "COMPLETE_RESUME_SEMANTICS_ACCEPTED"
    assert result["max_events_per_atomic_shard"] == 4
    for arm in ARMS:
        scenarios = result["arms"][arm]["scenarios"]
        roots = {row["final_state_root_sha256"] for row in scenarios.values()}
        assert roots == {result["arms"][arm]["expected_final_state_root_sha256"]}
        assert scenarios["interruption_before_seal"]["replayed_event_count"] <= 4
        assert scenarios["interruption_before_seal"]["orphan_checkpoint_count"] == 1
        assert scenarios["interruption_after_seal"]["replayed_event_count"] == 0
        assert scenarios["interruption_after_seal"]["orphan_checkpoint_count"] == 0


def test_checkpoint_contains_full_canonical_arm_state(tmp_path: Path) -> None:
    result_path = resume.write_resume_result(tmp_path)
    result = json.loads(result_path.read_text(encoding="utf-8"))
    entry = result["arms"]["S0R0"]["scenarios"]["uninterrupted"][
        "checkpoints"
    ][-1]
    checkpoint = json.loads((tmp_path / entry["checkpoint_path"]).read_text())
    state = checkpoint["state"]
    assert {
        "account",
        "adaptive_memory",
        "broker",
        "candidate_orders",
        "closed",
        "ledger",
        "open",
        "pending",
        "queue",
        "replacement",
        "reservations",
        "risk_counters",
    }.issubset(state)
    assert checkpoint["sealed_shard_boundary"] is True
    assert checkpoint["state_root_sha256"] == resume.stable_sha256(state)


def test_stale_wrong_and_interruption_failure_matrix(tmp_path: Path) -> None:
    verdicts = resume.run_resume_failure_injections(tmp_path)
    assert len(verdicts) == 10
    assert {row["status"] for row in verdicts} == {"REJECTED_AS_REQUIRED"}
    assert {row["case"] for row in verdicts} == {
        "append_after_seal",
        "bit_flip",
        "interruption_before_seal",
        "seal_mismatch",
        "stale_candidate",
        "stale_code",
        "stale_config",
        "stale_proof_route",
        "stale_source",
        "wrong_arm",
    }


def test_independent_resume_verifier_consumes_persisted_checkpoints(
    tmp_path: Path,
) -> None:
    result_path = resume.write_resume_result(tmp_path)
    receipt = verifier.verify_resume_result(result_path)
    assert receipt["status"] == "VERIFIED"
    assert receipt["arm_count"] == 4
    assert receipt["scenario_count"] == 12

    result = json.loads(result_path.read_text())
    entry = result["arms"]["S0R0"]["scenarios"]["uninterrupted"][
        "checkpoints"
    ][0]
    checkpoint_path = tmp_path / entry["checkpoint_path"]
    checkpoint_path.write_bytes(checkpoint_path.read_bytes() + b"X")
    with pytest.raises(verifier.VerificationError, match="checkpoint_file_hash_mismatch"):
        verifier.verify_resume_result(result_path)


def test_resume_route_root_is_deterministic(tmp_path: Path) -> None:
    first = json.loads(
        resume.write_resume_result(tmp_path / "first").read_text(encoding="utf-8")
    )
    second = json.loads(
        resume.write_resume_result(tmp_path / "second").read_text(encoding="utf-8")
    )
    assert first["resume_route_root_sha256"] == second["resume_route_root_sha256"]
