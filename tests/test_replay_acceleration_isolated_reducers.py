from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.research_infra import replay_acceleration_isolated_reducers as reducers
from src.research_infra import replay_acceleration_isolated_reducers_verifier as verifier


ARMS = ("S0R0", "S1R0", "S0R1", "S1R1")


def test_four_arm_state_allocations_have_no_mutable_aliases() -> None:
    states = reducers.allocate_arm_states(
        candidate_base_root="a" * 64,
        source_barrier_root="b" * 64,
        selected_day="2026-01-02",
    )
    reducers.assert_arm_state_isolation(states)

    states["S1R0"].queue = states["S0R0"].queue
    with pytest.raises(reducers.ReducerError, match="^arm_state_mutable_alias_detected$"):
        reducers.assert_arm_state_isolation(states)


def test_chronological_reducers_cover_required_state_and_arm_order_permutations() -> None:
    forward = reducers.run_structural_reducer_probe(arm_order=ARMS)
    reverse = reducers.run_structural_reducer_probe(arm_order=tuple(reversed(ARMS)))

    assert forward["arm_order"] == list(ARMS)
    assert forward["cross_symbol_barrier"]["symbol_count"] == 24
    assert forward["cross_symbol_barrier"]["logical_partition_count"] == 120
    assert forward["mutable_reducers_parallelized"] is False
    assert forward["policy_callbacks_invoked"] is False
    for arm in ARMS:
        assert forward["arms"][arm]["final_state_root_sha256"] == reverse["arms"][arm][
            "final_state_root_sha256"
        ]
        state = forward["arms"][arm]["final_state"]
        assert state["sealed"] is True
        assert state["order_sequence"] == 3
        assert state["queue"] == []
        assert len(state["pending"]) == 0
        assert len(state["open"]) == 1
        assert len(state["closed"]) == 1
        assert len(state["reservations"]) == 1
        assert len(state["replacement"]) == 1
        assert state["adaptive_memory"]
        assert state["risk_counters"]["open_slots"] == 1
    assert len(
        {forward["arms"][arm]["final_state_root_sha256"] for arm in ARMS}
    ) == 4
    assert len(
        {forward["arms"][arm]["neutral_state_root_sha256"] for arm in ARMS}
    ) == 1


@pytest.mark.parametrize(
    ("case", "code"),
    [
        ("out_of_order", "event_cursor_not_strictly_increasing"),
        ("after_seal", "event_after_seal"),
        ("wrong_barrier", "source_barrier_root_mismatch"),
        ("wrong_candidate_root", "candidate_base_root_mismatch"),
        ("wrong_arm", "arm_namespace_mismatch"),
        ("missing_pending_replacement", "replacement_pending_order_missing"),
    ],
)
def test_reducer_failure_injections_reject_stably(case: str, code: str) -> None:
    with pytest.raises(reducers.ReducerError, match=f"^{code}$"):
        reducers.execute_failure_injection(case)


def test_independent_verifier_replays_persisted_shards(tmp_path: Path) -> None:
    result_path = reducers.write_isolated_reducer_result(tmp_path)
    receipt = verifier.verify_isolated_reducer_result(result_path)
    assert receipt["status"] == "VERIFIED"
    assert receipt["arm_count"] == 4

    payload = json.loads(result_path.read_text(encoding="utf-8"))
    shard_path = tmp_path / payload["arms"]["S0R0"]["path"]
    shard = json.loads(shard_path.read_text(encoding="utf-8"))
    shard["final_state"]["order_sequence"] += 1
    shard_path.write_text(json.dumps(shard) + "\n", encoding="utf-8")
    with pytest.raises(verifier.VerificationError, match="arm_shard_file_hash_mismatch"):
        verifier.verify_isolated_reducer_result(result_path)


def test_production_failure_matrix_covers_alias_and_transition_rejections() -> None:
    verdicts = reducers.run_reducer_failure_injections()
    assert len(verdicts) == 7
    assert {row["status"] for row in verdicts} == {"REJECTED_AS_REQUIRED"}
