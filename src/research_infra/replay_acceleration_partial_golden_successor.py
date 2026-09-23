from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from typing import Any, Mapping, Sequence

from src.research_infra.replay_acceleration_immutable_evidence import (
    ImmutableEvidenceError,
    immutable_write_bytes,
    read_regular_nofollow,
)


SUCCESSOR_SCHEMA = (
    "gtos.replay_acceleration.partial_golden_structural_successor.v1"
)
SUCCESSOR_GATE = "PARTIAL_GOLDEN_STRUCTURAL_SUCCESSOR_MATERIALIZED"
MODULE_NAME = (
    "src.research_infra.replay_acceleration_partial_golden_successor"
)
AUTHORIZED_DAYS = tuple(f"2026-01-{day:02d}" for day in range(1, 8))
SOURCE_DIGEST_KEY = "source_plan_digest_sha256"
CANONICAL_SOURCE_DIGEST_KEY = "canonical_source_plan_digest_sha256"


class PartialGoldenSuccessorError(RuntimeError):
    pass


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise PartialGoldenSuccessorError(code)


def _is_sha256(value: Any) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(character in "009abcdef" for character in value)
    )


def _canonical(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )


def _root(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _json_pointer(path: Sequence[str | int]) -> str:
    encoded: list[str] = []
    for item in path:
        encoded.append(str(item).replace("~", "~0").replace("/", "~1"))
    return "/" + "/".join(encoded)


def _changed_leaf_paths(
    predecessor: Any,
    successor: Any,
    *,
    path: tuple[str | int, ...] = (),
) -> list[tuple[str | int, ...]]:
    _require(type(predecessor) is type(successor), "successor_json_type_drift")
    if isinstance(predecessor, Mapping):
        _require(
            set(predecessor) == set(successor),
            "successor_json_mapping_shape_drift",
        )
        changed: list[tuple[str | int, ...]] = []
        for key in sorted(predecessor):
            changed.extend(
                _changed_leaf_paths(
                    predecessor[key],
                    successor[key],
                    path=(*path, str(key)),
                )
            )
        return changed
    if isinstance(predecessor, list):
        _require(
            len(predecessor) == len(successor),
            "successor_json_list_shape_drift",
        )
        changed = []
        for index, (before, after) in enumerate(
            zip(predecessor, successor, strict=True)
        ):
            changed.extend(
                _changed_leaf_paths(
                    before,
                    after,
                    path=(*path, index),
                )
            )
        return changed
    return [path] if predecessor != successor else []


def _strict_mapping(value: Any, code: str) -> Mapping[str, Any]:
    _require(isinstance(value, Mapping), code)
    return value


def _strict_list(value: Any, code: str) -> list[Any]:
    _require(type(value) is list, code)
    return value


def _target_records(
    partial: Mapping[str, Any],
    *,
    bound_source_plan_digest_sha256: str,
) -> tuple[list[tuple[tuple[str | int, ...], Mapping[str, Any]]], list[str]]:
    progress = _strict_list(
        partial.get("progress_rows"),
        "predecessor_progress_rows_missing",
    )
    capacity_contract = _strict_mapping(
        partial.get("capacity_safe_chunk_execution_contract"),
        "predecessor_capacity_contract_missing",
    )
    capacity = _strict_list(
        capacity_contract.get("checkpoints"),
        "predecessor_capacity_checkpoints_missing",
    )
    source_contract = _strict_mapping(
        partial.get("source_authority_chunk_invariance_contract"),
        "predecessor_source_contract_missing",
    )
    source = _strict_list(
        source_contract.get("checkpoints"),
        "predecessor_source_checkpoints_missing",
    )
    _require(
        len(progress) == len(capacity) == len(source) == len(AUTHORIZED_DAYS),
        "predecessor_checkpoint_count_mismatch",
    )
    actual_days = [
        row.get("start_day") if isinstance(row, Mapping) else None
        for row in progress
    ]
    _require(
        actual_days == list(AUTHORIZED_DAYS),
        "predecessor_progress_scope_mismatch",
    )

    targets: list[tuple[tuple[str | int, ...], Mapping[str, Any]]] = []
    transient_digests: list[str] = []
    for index, day in enumerate(AUTHORIZED_DAYS):
        progress_row = _strict_mapping(
            progress[index], f"predecessor_progress_row_invalid:{day}"
        )
        capacity_row = _strict_mapping(
            capacity[index], f"predecessor_capacity_row_invalid:{day}"
        )
        source_row = _strict_mapping(
            source[index], f"predecessor_source_row_invalid:{day}"
        )
        _require(
            progress_row.get("start_day")
            == progress_row.get("end_day")
            == capacity_row.get("start_day")
            == capacity_row.get("end_day")
            == day,
            f"predecessor_checkpoint_day_mismatch:{day}",
        )
        progress_authority = _strict_mapping(
            progress_row.get("source_authority"),
            f"predecessor_progress_source_authority_missing:{day}",
        )
        capacity_authority = _strict_mapping(
            capacity_row.get("source_authority"),
            f"predecessor_capacity_source_authority_missing:{day}",
        )
        projected_transient_digests = {
            progress_authority.get(SOURCE_DIGEST_KEY),
            capacity_authority.get(SOURCE_DIGEST_KEY),
            source_row.get(SOURCE_DIGEST_KEY),
        }
        _require(
            len(projected_transient_digests) == 1,
            f"chunk_source_digest_projection_mismatch:{day}",
        )
        _require(
            progress_authority == capacity_authority == source_row,
            f"chunk_source_authority_projection_mismatch:{day}",
        )
        _require(
            source_row.get("execution_days") == [day],
            f"chunk_source_authority_day_mismatch:{day}",
        )
        _require(
            source_row.get(CANONICAL_SOURCE_DIGEST_KEY)
            == bound_source_plan_digest_sha256,
            f"chunk_canonical_source_digest_mismatch:{day}",
        )
        transient_digest = source_row.get(SOURCE_DIGEST_KEY)
        _require(
            _is_sha256(transient_digest),
            f"predecessor_chunk_digest_invalid:{day}",
        )
        _require(
            transient_digest != bound_source_plan_digest_sha256,
            f"predecessor_chunk_digest_not_transient:{day}",
        )
        transient_digests.append(str(transient_digest))
        targets.extend(
            (
                (
                    (
                        "progress_rows",
                        index,
                        "source_authority",
                        SOURCE_DIGEST_KEY,
                    ),
                    progress_authority,
                ),
                (
                    (
                        "capacity_safe_chunk_execution_contract",
                        "checkpoints",
                        index,
                        "source_authority",
                        SOURCE_DIGEST_KEY,
                    ),
                    capacity_authority,
                ),
                (
                    (
                        "source_authority_chunk_invariance_contract",
                        "checkpoints",
                        index,
                        SOURCE_DIGEST_KEY,
                    ),
                    source_row,
                ),
            )
        )
    _require(
        len(set(transient_digests)) == len(AUTHORIZED_DAYS),
        "predecessor_chunk_digests_not_unique",
    )
    return targets, transient_digests


def rebind_partial_summary_source_plan_digest(
    predecessor_bytes: bytes,
    *,
    bound_source_plan_digest_sha256: str,
) -> tuple[bytes, dict[str, Any]]:
    """Rebind only the 21 P3 structural digest leaves of a Jan 1-7 golden.

    The byte-level substitution preserves the complete serialized predecessor
    outside equal-length SHA-256 leaf values. Economic values are neither
    projected nor returned.
    """

    _require(
        _is_sha256(bound_source_plan_digest_sha256),
        "bound_source_plan_digest_invalid",
    )
    try:
        predecessor = json.loads(predecessor_bytes)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise PartialGoldenSuccessorError(
            "predecessor_partial_summary_invalid_json"
        ) from exc
    predecessor = _strict_mapping(
        predecessor, "predecessor_partial_summary_not_mapping"
    )
    targets, transient_digests = _target_records(
        predecessor,
        bound_source_plan_digest_sha256=bound_source_plan_digest_sha256,
    )
    expected_paths = sorted(path for path, _record in targets)
    successor_bytes = predecessor_bytes
    replacement_count = 0
    bound_bytes = bound_source_plan_digest_sha256.encode("ascii")
    for transient_digest in transient_digests:
        pattern = re.compile(
            rb'("source_plan_digest_sha256"[ \t\r\n]*:[ \t\r\n]*")'
            + transient_digest.encode("ascii")
            + rb'(")'
        )
        successor_bytes, count = pattern.subn(
            lambda match: match.group(1) + bound_bytes + match.group(2),
            successor_bytes,
        )
        _require(count == 3, "serialized_chunk_digest_occurrence_mismatch")
        replacement_count += count
    _require(
        len(successor_bytes) == len(predecessor_bytes),
        "successor_serialized_length_drift",
    )
    try:
        successor = json.loads(successor_bytes)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise PartialGoldenSuccessorError(
            "successor_partial_summary_invalid_json"
        ) from exc
    successor = _strict_mapping(successor, "successor_partial_not_mapping")
    changed_paths = sorted(_changed_leaf_paths(predecessor, successor))
    _require(
        changed_paths == expected_paths,
        "successor_changed_leaf_inventory_mismatch",
    )
    for path, _record in targets:
        value: Any = successor
        for component in path:
            value = value[component]
        _require(
            value == bound_source_plan_digest_sha256,
            "successor_bound_digest_missing",
        )
    pointer_paths = [_json_pointer(path) for path in changed_paths]
    receipt = {
        "schema": SUCCESSOR_SCHEMA,
        "gate": SUCCESSOR_GATE,
        "predecessor_partial_summary_sha256": hashlib.sha256(
            predecessor_bytes
        ).hexdigest(),
        "successor_partial_summary_sha256": hashlib.sha256(
            successor_bytes
        ).hexdigest(),
        "bound_source_plan_digest_sha256": (
            bound_source_plan_digest_sha256
        ),
        "authorized_days": list(AUTHORIZED_DAYS),
        "changed_leaf_count": len(changed_paths),
        "changed_leaf_paths": pointer_paths,
        "changed_leaf_path_root_sha256": _root(pointer_paths),
        "predecessor_transient_digest_root_sha256": _root(
            transient_digests
        ),
        "serialized_replacement_count": replacement_count,
        "serialized_length_preserved": True,
        "all_other_json_values_equal": True,
        "economic_values_exposed": False,
        "parity_continuation_authorized": False,
        "broker_live_authority": False,
    }
    return successor_bytes, receipt


def _read_regular_file(path: Path) -> bytes:
    try:
        raw, _identity = read_regular_nofollow(
            path,
            code="predecessor_file_storage_invalid",
        )
        return raw
    except ImmutableEvidenceError as exc:
        raise PartialGoldenSuccessorError(str(exc)) from None


def _atomic_write(path: Path, payload: bytes) -> None:
    try:
        immutable_write_bytes(path, payload, code="output_exists")
    except ImmutableEvidenceError as exc:
        raise PartialGoldenSuccessorError(str(exc)) from None


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predecessor-partial-summary", type=Path, required=True)
    parser.add_argument("--successor-partial-summary", type=Path, required=True)
    parser.add_argument("--bound-source-plan-digest-sha256", required=True)
    parser.add_argument("--receipt-output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    predecessor = _read_regular_file(args.predecessor_partial_summary)
    successor, evidence = rebind_partial_summary_source_plan_digest(
        predecessor,
        bound_source_plan_digest_sha256=(
            args.bound_source_plan_digest_sha256
        ),
    )
    _atomic_write(args.successor_partial_summary, successor)
    receipt = {
        **evidence,
        "predecessor_partial_summary": str(
            args.predecessor_partial_summary.resolve()
        ),
        "successor_partial_summary": str(
            args.successor_partial_summary.resolve()
        ),
        "command": [sys.executable, "-m", MODULE_NAME, *(argv or sys.argv[1:])],
    }
    receipt["receipt_root_sha256"] = _root(receipt)
    _atomic_write(args.receipt_output, _canonical(receipt))
    print(
        json.dumps(
            {
                "gate": receipt["gate"],
                "receipt_root_sha256": receipt["receipt_root_sha256"],
                "successor_partial_summary_sha256": receipt[
                    "successor_partial_summary_sha256"
                ],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
