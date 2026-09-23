from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path

import pytest

from src.research_infra.replay_acceleration_partial_golden_successor import (
    PartialGoldenSuccessorError,
    main,
    rebind_partial_summary_source_plan_digest,
)


BOUND_SOURCE_PLAN_DIGEST = "a" * 64
DAYS = tuple(f"2026-01-{day:02d}" for day in range(1, 8))


def _chunk_authority(day: str, transient_digest: str) -> dict[str, object]:
    return {
        "profile": "repaired_package_conversion_v3",
        "split": "development",
        "execution_days": [day],
        "execution_days_subset_of_source_authority": True,
        "source_plan_valid": True,
        "source_plan_matches_canonical": True,
        "static_sources_match_canonical": True,
        "tick_component_sources_match_canonical": True,
        "m1_execution_day_authority_matches_canonical": True,
        "source_plan_resolved_symbol_count": 24,
        "source_plan_missing_symbols": [],
        "canonical_source_plan_digest_sha256": BOUND_SOURCE_PLAN_DIGEST,
        "source_plan_digest_sha256": transient_digest,
    }


def _partial_summary_bytes() -> bytes:
    progress_rows: list[dict[str, object]] = []
    capacity_checkpoints: list[dict[str, object]] = []
    source_checkpoints: list[dict[str, object]] = []
    for index, day in enumerate(DAYS, start=1):
        transient_digest = hashlib.sha256(day.encode("ascii")).hexdigest()
        authority = _chunk_authority(day, transient_digest)
        progress_rows.append(
            {
                "chunk_id": f"profile:development:{day}:{day}",
                "profile": "profile",
                "split": "development",
                "start_day": day,
                "end_day": day,
                "day_count": 1,
                "source_authority": copy.deepcopy(authority),
            }
        )
        capacity_checkpoints.append(
            {
                "chunk_id": f"profile:development:{day}:{day}",
                "profile": "profile",
                "split": "development",
                "start_day": day,
                "end_day": day,
                "day_count": 1,
                "starting_order_sequence": index - 1,
                "ending_order_sequence": index,
                "source_authority": copy.deepcopy(authority),
            }
        )
        source_checkpoints.append(copy.deepcopy(authority))
    payload = {
        "status": "partial_in_progress_not_final_proof",
        "output_prefix": "BOUNDED_S0R0",
        "progress_rows": progress_rows,
        "capacity_safe_chunk_execution_contract": {
            "checkpoints": capacity_checkpoints,
        },
        "source_authority_chunk_invariance_contract": {
            "checkpoints": source_checkpoints,
        },
        "b7_5_contract_binding": {
            "actual_source_plan_digests_sha256": [BOUND_SOURCE_PLAN_DIGEST],
            "expected_source_plan_digest_sha256": BOUND_SOURCE_PLAN_DIGEST,
        },
        "opaque_economic_payload": {
            "cash": -123.45,
            "physical_r": 7.25,
            "nested": ["must", "remain", "byte-stable"],
        },
    }
    return (
        json.dumps(payload, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    )


def test_rebinds_only_the_twenty_one_structural_digest_leaves() -> None:
    predecessor = _partial_summary_bytes()

    successor, receipt = rebind_partial_summary_source_plan_digest(
        predecessor,
        bound_source_plan_digest_sha256=BOUND_SOURCE_PLAN_DIGEST,
    )

    predecessor_value = json.loads(predecessor)
    successor_value = json.loads(successor)
    assert successor != predecessor
    assert len(successor) == len(predecessor)
    assert (
        successor_value["opaque_economic_payload"]
        == predecessor_value["opaque_economic_payload"]
    )
    assert receipt["changed_leaf_count"] == 21
    assert receipt["serialized_replacement_count"] == 21
    assert receipt["all_other_json_values_equal"] is True
    assert receipt["economic_values_exposed"] is False
    for index in range(7):
        assert (
            successor_value["progress_rows"][index]["source_authority"][
                "source_plan_digest_sha256"
            ]
            == BOUND_SOURCE_PLAN_DIGEST
        )
        assert (
            successor_value["capacity_safe_chunk_execution_contract"][
                "checkpoints"
            ][index]["source_authority"]["source_plan_digest_sha256"]
            == BOUND_SOURCE_PLAN_DIGEST
        )
        assert (
            successor_value["source_authority_chunk_invariance_contract"][
                "checkpoints"
            ][index]["source_plan_digest_sha256"]
            == BOUND_SOURCE_PLAN_DIGEST
        )


def test_rejects_cross_projection_transient_digest_disagreement() -> None:
    value = json.loads(_partial_summary_bytes())
    value["progress_rows"][3]["source_authority"][
        "source_plan_digest_sha256"
    ] = "b" * 64
    raw = json.dumps(value, indent=2, sort_keys=True).encode("utf-8") + b"\n"

    with pytest.raises(
        PartialGoldenSuccessorError,
        match="chunk_source_digest_projection_mismatch:2026-01-04",
    ):
        rebind_partial_summary_source_plan_digest(
            raw,
            bound_source_plan_digest_sha256=BOUND_SOURCE_PLAN_DIGEST,
        )


def test_rejects_already_bound_or_non_january_scope() -> None:
    value = json.loads(_partial_summary_bytes())
    for record in (
        value["progress_rows"][0]["source_authority"],
        value["capacity_safe_chunk_execution_contract"]["checkpoints"][0][
            "source_authority"
        ],
        value["source_authority_chunk_invariance_contract"]["checkpoints"][0],
    ):
        record["source_plan_digest_sha256"] = BOUND_SOURCE_PLAN_DIGEST
    already_bound = (
        json.dumps(value, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    )
    with pytest.raises(
        PartialGoldenSuccessorError,
        match="predecessor_chunk_digest_not_transient:2026-01-01",
    ):
        rebind_partial_summary_source_plan_digest(
            already_bound,
            bound_source_plan_digest_sha256=BOUND_SOURCE_PLAN_DIGEST,
        )

    non_january = json.loads(_partial_summary_bytes())
    non_january["progress_rows"][6]["start_day"] = "2026-01-08"
    raw = (
        json.dumps(non_january, indent=2, sort_keys=True).encode("utf-8")
        + b"\n"
    )
    with pytest.raises(
        PartialGoldenSuccessorError,
        match="predecessor_progress_scope_mismatch",
    ):
        rebind_partial_summary_source_plan_digest(
            raw,
            bound_source_plan_digest_sha256=BOUND_SOURCE_PLAN_DIGEST,
        )


def test_cli_records_canonical_module_and_never_clobbers_outputs(
    tmp_path: Path,
) -> None:
    predecessor = tmp_path / "predecessor.json"
    successor = tmp_path / "successor.json"
    receipt = tmp_path / "receipt.json"
    predecessor.write_bytes(_partial_summary_bytes())
    argv = [
        "--predecessor-partial-summary",
        str(predecessor),
        "--successor-partial-summary",
        str(successor),
        "--bound-source-plan-digest-sha256",
        BOUND_SOURCE_PLAN_DIGEST,
        "--receipt-output",
        str(receipt),
    ]

    assert main(argv) == 0
    evidence = json.loads(receipt.read_bytes())
    assert evidence["command"][2] == (
        "src.research_infra.replay_acceleration_partial_golden_successor"
    )

    with pytest.raises(PartialGoldenSuccessorError, match="output_exists"):
        main(argv)


@pytest.mark.parametrize("storage", ["hardlink", "symlink_parent"])
def test_cli_rejects_aliased_predecessor_storage(
    tmp_path: Path,
    storage: str,
) -> None:
    original_parent = tmp_path / "original"
    original_parent.mkdir()
    original = original_parent / "predecessor.json"
    original.write_bytes(_partial_summary_bytes())
    if storage == "hardlink":
        predecessor = tmp_path / "hardlink.json"
        os.link(original, predecessor)
    else:
        alias_parent = tmp_path / "alias"
        alias_parent.symlink_to(original_parent, target_is_directory=True)
        predecessor = alias_parent / original.name

    with pytest.raises(
        PartialGoldenSuccessorError,
        match="predecessor_file_storage_invalid",
    ):
        main(
            [
                "--predecessor-partial-summary",
                str(predecessor),
                "--successor-partial-summary",
                str(tmp_path / "successor.json"),
                "--bound-source-plan-digest-sha256",
                BOUND_SOURCE_PLAN_DIGEST,
                "--receipt-output",
                str(tmp_path / "receipt.json"),
            ]
        )
