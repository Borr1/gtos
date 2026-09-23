from __future__ import annotations

import copy

import pytest

from src.research_infra import (
    replay_acceleration_task5_compact_sink_acceptance as task5,
)


def _summary() -> dict[str, object]:
    checkpoints = []
    progress = []
    for index, counts in enumerate(task5.EXPECTED_ROLE_COUNTS):
        day = f"2026-01-0{index + 1}"
        checkpoint = {
            "enabled": True,
            "profile": "repaired_package_conversion_v3",
            "split": "development",
            "chunk_id": (
                "repaired_package_conversion_v3:development:"
                f"{day}:{day}"
            ),
            "economic_hot_path_seconds": 1.0,
            "proof_finalization_seconds": 2.0,
            "authority": {
                "status": "sealed",
                "resident_canonical_row_count": 0,
                "row_counts": dict(counts),
            },
        }
        checkpoints.append(checkpoint)
        progress.append(
            {
                "economic_hot_path_seconds": 1.0,
                "proof_finalization_seconds": 2.0,
                "compact_event_sink": checkpoint,
                "candidate_relational_materialization": {
                    "schema": task5.TASK5_RELATIONAL_SCHEMA,
                    "exact": True,
                },
            }
        )
    return {
        "compact_event_sink_enabled": True,
        "compact_event_sink_checkpoints": checkpoints,
        "progress_rows": progress,
        "semantic": "preserved",
    }


def test_task5_summary_projection_is_finite_and_noncausal() -> None:
    source = _summary()
    source_before = copy.deepcopy(source)

    projected, proof = task5.project_task5_summary(source)

    assert source == source_before
    assert projected["semantic"] == "preserved"
    assert "compact_event_sink_enabled" not in projected
    assert "compact_event_sink_checkpoints" not in projected
    for row in projected["progress_rows"]:
        assert "economic_hot_path_seconds" not in row
        assert "proof_finalization_seconds" not in row
        assert "compact_event_sink" not in row
        relational = row["candidate_relational_materialization"]
        assert relational["schema"] == task5.LEGACY_RELATIONAL_SCHEMA
        assert relational["status"] == (
            "exact_candidate_equals_missed_order_trade_union"
        )
    assert proof["causal_or_economic_field_excluded"] is False
    assert proof["unknown_field_excluded"] is False


def test_task5_summary_projection_rejects_unknown_or_invalid_proof_shape() -> None:
    missing = _summary()
    missing.pop("compact_event_sink_checkpoints")
    with pytest.raises(
        task5.Task5CompactSinkAcceptanceRejected,
        match="task5_summary_proof_envelope_invalid",
    ):
        task5.project_task5_summary(missing)

    mismatch = _summary()
    mismatch["progress_rows"][0]["economic_hot_path_seconds"] = 0.0
    with pytest.raises(
        task5.Task5CompactSinkAcceptanceRejected,
        match="task5_progress_proof_envelope_invalid:0",
    ):
        task5.project_task5_summary(mismatch)


def test_task5_summary_projection_preserves_current_legacy_relational_schema() -> None:
    summary = _summary()
    for row in summary["progress_rows"]:
        row["candidate_relational_materialization"] = {
            "schema": task5.LEGACY_RELATIONAL_SCHEMA,
            "status": "exact_candidate_equals_missed_order_trade_union",
            "exact": True,
        }
    projected, _proof = task5.project_task5_summary(summary)
    assert all(
        row["candidate_relational_materialization"]["schema"]
        == task5.LEGACY_RELATIONAL_SCHEMA
        for row in projected["progress_rows"]
    )


def test_task5_manifest_must_bind_its_execution_receipt_shared_contract() -> None:
    digest = "a" * 64
    assert task5.validate_manifest_receipt_shared_contract_binding(
        {"shared_execution_contract_digest_sha256": digest},
        {"shared_execution_contract_digest_sha256": digest},
        label="accelerated",
    ) == {
        "label": "accelerated",
        "shared_execution_contract_digest_sha256": digest,
    }
    with pytest.raises(
        task5.Task5CompactSinkAcceptanceRejected,
        match="task5_manifest_receipt_shared_contract_mismatch:accelerated",
    ):
        task5.validate_manifest_receipt_shared_contract_binding(
            {"shared_execution_contract_digest_sha256": digest},
            {"shared_execution_contract_digest_sha256": "b" * 64},
            label="accelerated",
        )
