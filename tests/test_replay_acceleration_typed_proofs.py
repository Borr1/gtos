from __future__ import annotations

import inspect
import json
from pathlib import Path

from src.research_infra import replay_acceleration_typed_proofs as typed
from src.research_infra import replay_acceleration_typed_proofs_verifier as verifier


ARMS = ("S0R0", "S1R0", "S0R1", "S1R1")


def test_typed_day_shards_round_trip_exact_legacy_projections(tmp_path: Path) -> None:
    result_path = typed.write_typed_proof_result(tmp_path)
    receipt = verifier.verify_typed_proof_result(result_path)
    result = json.loads(result_path.read_text(encoding="utf-8"))

    assert receipt["status"] == "VERIFIED"
    assert receipt["arm_count"] == 4
    assert receipt["record_count"] == 48
    assert receipt["projection_roundtrip_exact"] is True
    assert set(result["arms"]) == set(ARMS)
    for arm in ARMS:
        shard = result["arms"][arm]
        assert shard["record_count"] == 12
        assert len(shard["window_roots"]) == 4
        assert set(shard["ledger_roots"]) == {
            "adaptive",
            "broker",
            "lifecycle",
            "queue",
            "seal",
        }
        assert shard["typed_record_bytes"] < shard["legacy_projection_bytes"]


def test_typed_campaign_roots_are_deterministic_across_fresh_writes(tmp_path: Path) -> None:
    first = typed.write_typed_proof_result(tmp_path / "first")
    second = typed.write_typed_proof_result(tmp_path / "second")
    first_payload = json.loads(first.read_text(encoding="utf-8"))
    second_payload = json.loads(second.read_text(encoding="utf-8"))
    assert first_payload["campaign_root_sha256"] == second_payload[
        "campaign_root_sha256"
    ]
    assert {
        arm: first_payload["arms"][arm]["day_root_sha256"] for arm in ARMS
    } == {arm: second_payload["arms"][arm]["day_root_sha256"] for arm in ARMS}


def test_independent_verifier_does_not_import_writer_or_root_builder() -> None:
    source = inspect.getsource(verifier)
    assert "replay_acceleration_typed_proofs import" not in source
    assert "from src.research_infra" not in source


def test_typed_failure_injection_matrix_rejects_all_mutations(tmp_path: Path) -> None:
    result_path = typed.write_typed_proof_result(tmp_path)
    verdicts = verifier.run_typed_failure_injection_matrix(result_path)
    assert len(verdicts) == 8
    assert {row["status"] for row in verdicts} == {"REJECTED_AS_REQUIRED"}
    assert {row["case"] for row in verdicts} == {
        "append",
        "bit_flip",
        "projection_mismatch",
        "record_reorder",
        "truncation",
        "wrong_arm",
        "wrong_schema",
        "wrong_source",
    }
