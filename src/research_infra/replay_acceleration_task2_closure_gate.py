#!/usr/bin/env python3
"""Authorize Task 2 only from a recomputed proof and a frozen review snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from src.research_infra import (
    replay_acceleration_task2_semantic_acceptance as semantic_acceptance,
)


ROOT = Path(__file__).resolve().parents[2]
SEMANTIC_VERIFIER = (
    ROOT
    / "src/research_infra/replay_acceleration_task2_semantic_acceptance.py"
)
CLOSURE_VERIFIER = Path(__file__).resolve()
SCHEMA = "gtos.replay_acceleration.task2_closure_gate.v2"
SNAPSHOT_SCHEMA = "gtos.replay_acceleration.task2_review_snapshot.v1"
REVIEW_SCHEMA = "gtos.replay_acceleration.independent_review.v1"
SEMANTIC_SCHEMA = "gtos.replay_acceleration.task2_semantic_acceptance.v1"
GATE = "Replay-Acceleration Task 2 bounded semantic equivalence"
REQUIRED_REVIEW_TYPES = frozenset({"scientific_spec", "code_quality_safety"})
_SNAPSHOT_FIELDS = frozenset(
    {
        "schema",
        "gate",
        "git_head_sha",
        "tracked_diff_sha256",
        "complete_tracked_diff_bound",
        "mutation_barrier_required",
        "reviewed_source_paths",
        "bound_artifact_paths",
        "reviewed_paths",
        "files",
        "snapshot_root_sha256",
    }
)
_SNAPSHOT_FILE_FIELDS = frozenset({"path", "scope", "bytes", "sha256"})
_REVIEW_FIELDS = frozenset(
    {
        "schema",
        "gate",
        "review_type",
        "reviewer_agent",
        "snapshot_root_sha256",
        "reviewed_paths",
        "status",
        "critical_finding_count",
        "important_finding_count",
        "findings",
        "review_root_sha256",
    }
)


class Task2ClosureError(RuntimeError):
    """Fail-closed Task 2 closure error."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Task2ClosureError("closure_input_invalid") from exc
    if not isinstance(value, dict):
        raise Task2ClosureError("closure_input_not_object")
    return value


def require_canonical_root(
    value: Mapping[str, Any],
    *,
    field: str,
    error: str,
) -> None:
    projection = dict(value)
    declared = projection.pop(field, None)
    if declared != canonical_sha256(projection):
        raise Task2ClosureError(error)


def _run_git(*args: str) -> bytes:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise Task2ClosureError("snapshot_git_state_unavailable")
    return result.stdout


def _git_head() -> str:
    value = _run_git("rev-parse", "HEAD").decode("ascii", errors="strict").strip()
    if len(value) != 40 or any(char not in "009abcdef" for char in value):
        raise Task2ClosureError("snapshot_git_head_invalid")
    return value


def _tracked_diff_sha256() -> str:
    unstaged = _run_git("diff", "--binary", "--no-ext-diff", "--")
    staged = _run_git("diff", "--cached", "--binary", "--no-ext-diff", "--")
    digest = hashlib.sha256()
    digest.update(b"unstaged\0")
    digest.update(len(unstaged).to_bytes(8, "big"))
    digest.update(unstaged)
    digest.update(b"staged\0")
    digest.update(len(staged).to_bytes(8, "big"))
    digest.update(staged)
    return digest.hexdigest()


def _relative_regular_path(path: Path) -> tuple[Path, str]:
    absolute_root = Path(os.path.abspath(ROOT))
    absolute = Path(os.path.abspath(path))
    try:
        relative = absolute.relative_to(absolute_root)
    except ValueError:
        raise Task2ClosureError("snapshot_file_outside_worktree") from None
    current = absolute_root
    for component in relative.parts:
        current = current / component
        if current.is_symlink():
            raise Task2ClosureError("snapshot_file_symlink_forbidden")
    try:
        mode = absolute.stat().st_mode
    except OSError as exc:
        raise Task2ClosureError("snapshot_file_missing") from exc
    if not stat.S_ISREG(mode):
        raise Task2ClosureError("snapshot_file_not_regular")
    return absolute, relative.as_posix()


def _snapshot_file_record(path: Path, *, scope: str) -> dict[str, Any]:
    absolute, relative = _relative_regular_path(path)
    return {
        "path": relative,
        "scope": scope,
        "bytes": absolute.stat().st_size,
        "sha256": file_sha256(absolute),
    }


def build_review_snapshot(
    *,
    reviewed_paths: Sequence[Path],
    artifact_paths: Sequence[Path],
) -> dict[str, Any]:
    records = [
        *(
            _snapshot_file_record(path, scope="reviewed_source")
            for path in reviewed_paths
        ),
        *(
            _snapshot_file_record(path, scope="bound_artifact")
            for path in artifact_paths
        ),
    ]
    records.sort(key=lambda row: row["path"])
    paths = [row["path"] for row in records]
    if not records or len(paths) != len(set(paths)):
        raise Task2ClosureError("snapshot_file_inventory_invalid")
    reviewed_source_paths = [
        row["path"] for row in records if row["scope"] == "reviewed_source"
    ]
    bound_artifact_paths = [
        row["path"] for row in records if row["scope"] == "bound_artifact"
    ]
    core = {
        "schema": SNAPSHOT_SCHEMA,
        "gate": GATE,
        "git_head_sha": _git_head(),
        "tracked_diff_sha256": _tracked_diff_sha256(),
        "complete_tracked_diff_bound": True,
        "mutation_barrier_required": True,
        "reviewed_source_paths": reviewed_source_paths,
        "bound_artifact_paths": bound_artifact_paths,
        "reviewed_paths": paths,
        "files": records,
    }
    return {**core, "snapshot_root_sha256": canonical_sha256(core)}


def validate_review_snapshot(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    if set(snapshot) != _SNAPSHOT_FIELDS:
        raise Task2ClosureError("snapshot_schema_invalid")
    require_canonical_root(
        snapshot,
        field="snapshot_root_sha256",
        error="snapshot_root_mismatch",
    )
    if (
        snapshot.get("schema") != SNAPSHOT_SCHEMA
        or snapshot.get("gate") != GATE
        or snapshot.get("complete_tracked_diff_bound") is not True
        or snapshot.get("mutation_barrier_required") is not True
    ):
        raise Task2ClosureError("snapshot_contract_invalid")
    if snapshot.get("git_head_sha") != _git_head():
        raise Task2ClosureError("snapshot_git_head_stale")
    if snapshot.get("tracked_diff_sha256") != _tracked_diff_sha256():
        raise Task2ClosureError("snapshot_tracked_diff_stale")
    rows = snapshot.get("files")
    reviewed = snapshot.get("reviewed_source_paths")
    artifacts = snapshot.get("bound_artifact_paths")
    all_paths = snapshot.get("reviewed_paths")
    if (
        not isinstance(rows, list)
        or not rows
        or not isinstance(reviewed, list)
        or not isinstance(artifacts, list)
        or not isinstance(all_paths, list)
        or any(type(path) is not str or not path for path in all_paths)
        or all_paths != sorted(all_paths)
        or len(all_paths) != len(set(all_paths))
    ):
        raise Task2ClosureError("snapshot_file_inventory_invalid")
    recomputed = []
    for row in rows:
        if (
            not isinstance(row, Mapping)
            or set(row) != _SNAPSHOT_FILE_FIELDS
            or row.get("scope") not in {"reviewed_source", "bound_artifact"}
            or type(row.get("path")) is not str
            or Path(row["path"]).is_absolute()
            or ".." in Path(row["path"]).parts
        ):
            raise Task2ClosureError("snapshot_file_record_invalid")
        recomputed.append(
            _snapshot_file_record(
                ROOT / row["path"], scope=str(row["scope"])
            )
        )
    recomputed.sort(key=lambda row: row["path"])
    if canonical_bytes(rows) != canonical_bytes(recomputed):
        raise Task2ClosureError("snapshot_file_stale")
    expected_reviewed = [
        row["path"] for row in recomputed if row["scope"] == "reviewed_source"
    ]
    expected_artifacts = [
        row["path"] for row in recomputed if row["scope"] == "bound_artifact"
    ]
    expected_all = [row["path"] for row in recomputed]
    if (
        reviewed != expected_reviewed
        or artifacts != expected_artifacts
        or all_paths != expected_all
    ):
        raise Task2ClosureError("snapshot_path_partition_invalid")
    return dict(snapshot)


def _recompute_semantic_receipt(fresh_root: Path) -> dict[str, Any]:
    return semantic_acceptance.run_acceptance(Path(fresh_root))


def validate_semantic_receipt(
    receipt_path: Path,
    *,
    fresh_root: Path,
) -> dict[str, Any]:
    receipt = load_json(receipt_path)
    recomputed = _recompute_semantic_receipt(fresh_root)
    if canonical_bytes(receipt) != canonical_bytes(recomputed):
        raise Task2ClosureError("semantic_receipt_recomputation_mismatch")
    try:
        persisted = Path(receipt_path).read_bytes()
    except OSError as exc:
        raise Task2ClosureError("semantic_receipt_unreadable") from exc
    if persisted != canonical_bytes(receipt) + b"\n":
        raise Task2ClosureError("semantic_receipt_persisted_bytes_invalid")
    require_canonical_root(
        receipt,
        field="receipt_root_sha256",
        error="semantic_receipt_root_mismatch",
    )
    if (
        receipt.get("schema") != SEMANTIC_SCHEMA
        or receipt.get("status")
        != "TASK2_OWNER_APPROVED_SEMANTIC_EQUIVALENCE_VERIFIED"
        or receipt.get("acceptance_authorized") is not False
        or receipt.get("meaningful_difference_count") != 0
        or receipt.get("unknown_difference_count") != 0
        or receipt.get("causal_or_economic_field_normalized") is not False
        or receipt.get("broker_live_authority") is not False
        or receipt.get("broker_mutation_enabled") is not False
        or receipt.get("semantic_acceptance_verifier_sha256")
        != file_sha256(SEMANTIC_VERIFIER)
    ):
        raise Task2ClosureError("semantic_receipt_not_eligible")
    physical = receipt.get("physical_reference_disposition")
    if physical is not None and (
        not isinstance(physical, Mapping)
        or physical.get("jan2_post_cleanup_checkpoint_sealed") is not False
        or physical.get("physical_semantic_comparator_used") is not False
        or physical.get("automatic_relaunch_permitted") is not False
    ):
        raise Task2ClosureError("semantic_physical_disposition_invalid")
    return receipt


def _validate_review(
    review: Mapping[str, Any],
    *,
    expected_snapshot_root: str,
    expected_reviewed_paths: Sequence[str],
) -> tuple[str, str]:
    if set(review) != _REVIEW_FIELDS:
        raise Task2ClosureError("review_schema_invalid")
    require_canonical_root(
        review,
        field="review_root_sha256",
        error="review_root_mismatch",
    )
    review_type = review.get("review_type")
    reviewer = review.get("reviewer_agent")
    if (
        review.get("schema") != REVIEW_SCHEMA
        or review.get("gate") != GATE
        or review_type not in REQUIRED_REVIEW_TYPES
        or type(reviewer) is not str
        or not reviewer.strip()
        or review.get("snapshot_root_sha256") != expected_snapshot_root
        or review.get("reviewed_paths") != list(expected_reviewed_paths)
        or review.get("status") != "PASS"
        or review.get("critical_finding_count") != 0
        or review.get("important_finding_count") != 0
        or review.get("findings") != []
    ):
        if review.get("reviewed_paths") != list(expected_reviewed_paths):
            raise Task2ClosureError("review_path_coverage_invalid")
        raise Task2ClosureError("independent_review_not_eligible")
    return str(review_type), reviewer


def validate_review_pair(
    reviews: Sequence[Mapping[str, Any]],
    *,
    expected_snapshot_root: str,
    expected_reviewed_paths: Sequence[str],
) -> dict[str, Mapping[str, Any]]:
    if len(reviews) != 2:
        raise Task2ClosureError("independent_review_coverage_invalid")
    validated: dict[str, Mapping[str, Any]] = {}
    reviewers = set()
    for review in reviews:
        review_type, reviewer = _validate_review(
            review,
            expected_snapshot_root=expected_snapshot_root,
            expected_reviewed_paths=expected_reviewed_paths,
        )
        if review_type in validated:
            raise Task2ClosureError("independent_review_coverage_invalid")
        validated[review_type] = review
        reviewers.add(reviewer)
    if set(validated) != REQUIRED_REVIEW_TYPES:
        raise Task2ClosureError("independent_review_coverage_invalid")
    if len(reviewers) != 2:
        raise Task2ClosureError("reviewer_independence_invalid")
    return validated


def build_closure_receipt(
    *,
    semantic_receipt_path: Path,
    fresh_root: Path,
    review_paths: Sequence[Path],
    snapshot_manifest_path: Path,
) -> dict[str, Any]:
    snapshot = validate_review_snapshot(load_json(snapshot_manifest_path))
    _, semantic_relative = _relative_regular_path(semantic_receipt_path)
    _, semantic_verifier_relative = _relative_regular_path(SEMANTIC_VERIFIER)
    _, closure_verifier_relative = _relative_regular_path(CLOSURE_VERIFIER)
    if (
        semantic_relative not in snapshot["bound_artifact_paths"]
        or semantic_verifier_relative not in snapshot["reviewed_source_paths"]
        or closure_verifier_relative not in snapshot["reviewed_source_paths"]
    ):
        raise Task2ClosureError("closure_required_snapshot_binding_missing")
    semantic = validate_semantic_receipt(
        semantic_receipt_path, fresh_root=fresh_root
    )
    reviews = [load_json(path) for path in review_paths]
    validated_reviews = validate_review_pair(
        reviews,
        expected_snapshot_root=snapshot["snapshot_root_sha256"],
        expected_reviewed_paths=snapshot["reviewed_paths"],
    )
    core = {
        "schema": SCHEMA,
        "status": "TASK2_BOUNDED_SEMANTIC_EQUIVALENCE_ACCEPTED",
        "task": "Replay-Acceleration Task 2",
        "mission_phase": "Replay Acceleration Phase A",
        "acceptance_authorized": True,
        "acceptance_basis": (
            "owner_narrowed_bounded_semantic_equivalence_plus_exact_"
            "recomputation_and_two_independent_bound_reviews"
        ),
        "semantic_report_acceptance_authorized": False,
        "semantic_receipt_sha256": file_sha256(semantic_receipt_path),
        "semantic_receipt_root_sha256": semantic["receipt_root_sha256"],
        "semantic_verifier_sha256": semantic[
            "semantic_acceptance_verifier_sha256"
        ],
        "closure_verifier_sha256": file_sha256(CLOSURE_VERIFIER),
        "review_snapshot_manifest_sha256": file_sha256(snapshot_manifest_path),
        "review_snapshot_root_sha256": snapshot["snapshot_root_sha256"],
        "review_roots_by_type": {
            review_type: review["review_root_sha256"]
            for review_type, review in sorted(validated_reviews.items())
        },
        "reviewer_agents_by_type": {
            review_type: review["reviewer_agent"]
            for review_type, review in sorted(validated_reviews.items())
        },
        "meaningful_difference_count": 0,
        "unknown_difference_count": 0,
        "physical_reference_jan2_claimed_complete": False,
        "withdrawn_gates_claimed_passed": False,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
        "next_task": "Replay-Acceleration Task 3 campaign-scoped exact caches",
    }
    return {**core, "receipt_root_sha256": canonical_sha256(core)}


def atomic_write_json(path: Path, value: Mapping[str, Any]) -> None:
    path = Path(os.path.abspath(path))
    if path.exists() or path.is_symlink():
        raise Task2ClosureError("closure_output_must_be_new")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("xb") as handle:
        handle.write(canonical_bytes(value) + b"\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    snapshot = subparsers.add_parser("snapshot")
    snapshot.add_argument("--reviewed-path", type=Path, action="append", required=True)
    snapshot.add_argument("--artifact-path", type=Path, action="append", required=True)
    snapshot.add_argument("--output", type=Path, required=True)
    close = subparsers.add_parser("close")
    close.add_argument("--semantic-receipt", type=Path, required=True)
    close.add_argument("--fresh-root", type=Path, required=True)
    close.add_argument("--snapshot-manifest", type=Path, required=True)
    close.add_argument("--science-review", type=Path, required=True)
    close.add_argument("--safety-review", type=Path, required=True)
    close.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "snapshot":
        receipt = build_review_snapshot(
            reviewed_paths=args.reviewed_path,
            artifact_paths=args.artifact_path,
        )
    else:
        receipt = build_closure_receipt(
            semantic_receipt_path=args.semantic_receipt,
            fresh_root=args.fresh_root,
            review_paths=(args.science_review, args.safety_review),
            snapshot_manifest_path=args.snapshot_manifest,
        )
    atomic_write_json(args.output, receipt)
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
