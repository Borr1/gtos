from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.research_infra import replay_acceleration_resource_architecture as resources
from src.research_infra import replay_acceleration_resource_architecture_verifier as verifier


def test_resource_inventory_preserves_evidence_and_bounds_each_slice() -> None:
    result = resources.build_resource_result()
    assert result["gate"] == "RESOURCE_STORAGE_ARCHITECTURE_ACCEPTED"
    assert result["retention"]["files_deleted"] == 0
    assert result["retention"]["bytes_reclaimed"] == 0
    assert result["retention"]["unique_proof_evidence_preserved"] is True
    assert all(
        row["allocated_bytes"] < resources.SCRATCH_QUOTA_BYTES
        for row in result["retention"]["bounded_slices"]
    )
    assert result["disk"]["available_bytes"] > resources.DISK_WARNING_BYTES
    assert result["disk"]["hard_floor_respected"] is True


def test_compression_and_hash_measurements_are_narrow_and_honest() -> None:
    result = resources.build_resource_result()
    compression = result["compression_probe"]
    assert compression["scope"] == "typed_structural_shards_in_memory_only"
    assert compression["persistent_compressed_artifact_created"] is False
    assert compression["input_bytes"] > compression["compressed_bytes"] > 0
    assert result["measurements"]["whole_replay_speed_claim"] is False
    assert result["hash_probe"]["bytes_hashed"] > 0
    assert result["verification_probes"]
    assert {row["status"] for row in result["verification_probes"]} == {"VERIFIED"}


@pytest.mark.parametrize(
    ("available", "allocated", "code"),
    [
        (resources.DISK_HARD_FLOOR_BYTES - 1, 1, "disk_hard_floor_threatened"),
        (
            resources.DISK_WARNING_BYTES + 1,
            resources.SCRATCH_QUOTA_BYTES,
            "bounded_slice_quota_not_strictly_below_limit",
        ),
    ],
)
def test_resource_gate_rejects_floor_or_quota_violation(
    available: int, allocated: int, code: str
) -> None:
    with pytest.raises(resources.ResourceError, match=f"^{code}$"):
        resources.enforce_resource_gate(
            available_bytes=available,
            bounded_slice_allocated_bytes=[allocated],
        )


def test_independent_resource_verifier_consumes_persisted_result(
    tmp_path: Path,
) -> None:
    result_path = resources.write_resource_result(tmp_path)
    receipt = verifier.verify_resource_result(result_path)
    assert receipt["status"] == "VERIFIED"

    payload = json.loads(result_path.read_text())
    payload["retention"]["files_deleted"] = 1
    result_path.write_text(json.dumps(payload) + "\n")
    with pytest.raises(verifier.VerificationError, match="result_root_mismatch"):
        verifier.verify_resource_result(result_path)
