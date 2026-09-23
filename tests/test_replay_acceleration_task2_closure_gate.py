from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.research_infra import replay_acceleration_task2_closure_gate as gate


def _rooted(value: dict[str, object], field: str) -> dict[str, object]:
    result = copy.deepcopy(value)
    result[field] = gate.canonical_sha256(result)
    return result


def _semantic() -> dict[str, object]:
    return _rooted(
        {
            "schema": gate.SEMANTIC_SCHEMA,
            "status": "TASK2_OWNER_APPROVED_SEMANTIC_EQUIVALENCE_VERIFIED",
            "acceptance_authorized": False,
            "meaningful_difference_count": 0,
            "unknown_difference_count": 0,
            "causal_or_economic_field_normalized": False,
            "broker_live_authority": False,
            "broker_mutation_enabled": False,
            "semantic_acceptance_verifier_sha256": "a" * 64,
            "full_proof_inventory": {"persisted_role_count": 8},
        },
        "receipt_root_sha256",
    )


def _review(
    review_type: str,
    snapshot: str,
    reviewed_paths: list[str],
    *,
    reviewer: str,
    findings: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    findings = list(findings or [])
    return _rooted(
        {
            "schema": gate.REVIEW_SCHEMA,
            "gate": gate.GATE,
            "review_type": review_type,
            "reviewer_agent": reviewer,
            "snapshot_root_sha256": snapshot,
            "reviewed_paths": reviewed_paths,
            "status": "PASS" if not findings else "FAIL",
            "critical_finding_count": 0,
            "important_finding_count": len(findings),
            "findings": findings,
        },
        "review_root_sha256",
    )


def _patch_repo(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> tuple[Path, Path]:
    source = tmp_path / "verifier.py"
    source.write_text("# verifier\n", encoding="utf-8")
    artifact = tmp_path / "semantic.json"
    artifact.write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(gate, "ROOT", tmp_path)
    monkeypatch.setattr(gate, "SEMANTIC_VERIFIER", source)
    monkeypatch.setattr(gate, "CLOSURE_VERIFIER", source)
    monkeypatch.setattr(gate, "_git_head", lambda: "1" * 40)
    monkeypatch.setattr(gate, "_tracked_diff_sha256", lambda: "2" * 64)
    return source, artifact


def test_snapshot_recomputes_head_diff_and_every_bound_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    source, artifact = _patch_repo(monkeypatch, tmp_path)
    snapshot = gate.build_review_snapshot(
        reviewed_paths=[source], artifact_paths=[artifact]
    )
    gate.validate_review_snapshot(snapshot)

    source.write_text("# changed\n", encoding="utf-8")
    with pytest.raises(gate.Task2ClosureError, match="snapshot_file_stale"):
        gate.validate_review_snapshot(snapshot)


def test_snapshot_rejects_stale_tracked_diff(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    source, artifact = _patch_repo(monkeypatch, tmp_path)
    snapshot = gate.build_review_snapshot(
        reviewed_paths=[source], artifact_paths=[artifact]
    )
    monkeypatch.setattr(gate, "_tracked_diff_sha256", lambda: "3" * 64)
    with pytest.raises(gate.Task2ClosureError, match="snapshot_tracked_diff_stale"):
        gate.validate_review_snapshot(snapshot)


def test_semantic_receipt_must_equal_fresh_independent_recomputation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    semantic = _semantic()
    path = tmp_path / "semantic.json"
    path.write_bytes(gate.canonical_bytes(semantic) + b"\n")
    monkeypatch.setattr(
        gate, "_recompute_semantic_receipt", lambda _fresh_root: semantic
    )
    monkeypatch.setattr(gate, "file_sha256", lambda _path: "a" * 64)
    gate.validate_semantic_receipt(path, fresh_root=tmp_path)

    synthetic = {
        key: value
        for key, value in semantic.items()
        if key
        in {
            "schema",
            "status",
            "acceptance_authorized",
            "meaningful_difference_count",
            "unknown_difference_count",
            "causal_or_economic_field_normalized",
            "broker_live_authority",
            "broker_mutation_enabled",
            "semantic_acceptance_verifier_sha256",
        }
    }
    synthetic = _rooted(synthetic, "receipt_root_sha256")
    path.write_bytes(gate.canonical_bytes(synthetic) + b"\n")
    with pytest.raises(
        gate.Task2ClosureError, match="semantic_receipt_recomputation_mismatch"
    ):
        gate.validate_semantic_receipt(path, fresh_root=tmp_path)


def test_reviews_require_distinct_reviewers_exact_paths_and_empty_findings() -> None:
    paths = ["src/a.py", "tests/test_a.py"]
    snapshot = "b" * 64
    science = _review(
        "scientific_spec", snapshot, paths, reviewer="reviewer-one"
    )
    safety = _review(
        "code_quality_safety", snapshot, paths, reviewer="reviewer-one"
    )
    with pytest.raises(gate.Task2ClosureError, match="reviewer_independence_invalid"):
        gate.validate_review_pair(
            [science, safety],
            expected_snapshot_root=snapshot,
            expected_reviewed_paths=paths,
        )

    safety = _review(
        "code_quality_safety", snapshot, paths[:-1], reviewer="reviewer-two"
    )
    with pytest.raises(gate.Task2ClosureError, match="review_path_coverage_invalid"):
        gate.validate_review_pair(
            [science, safety],
            expected_snapshot_root=snapshot,
            expected_reviewed_paths=paths,
        )

    safety = _review(
        "code_quality_safety",
        snapshot,
        paths,
        reviewer="reviewer-two",
        findings=[{"severity": "IMPORTANT", "path": "src/a.py"}],
    )
    with pytest.raises(gate.Task2ClosureError, match="independent_review_not_eligible"):
        gate.validate_review_pair(
            [science, safety],
            expected_snapshot_root=snapshot,
            expected_reviewed_paths=paths,
        )


def test_review_receipt_has_exact_schema() -> None:
    paths = ["src/a.py"]
    review = _review(
        "scientific_spec", "b" * 64, paths, reviewer="reviewer-one"
    )
    review["unreviewed_extra"] = True
    review["review_root_sha256"] = gate.canonical_sha256(
        {key: value for key, value in review.items() if key != "review_root_sha256"}
    )
    with pytest.raises(gate.Task2ClosureError, match="review_schema_invalid"):
        gate.validate_review_pair(
            [
                review,
                _review(
                    "code_quality_safety",
                    "b" * 64,
                    paths,
                    reviewer="reviewer-two",
                ),
            ],
            expected_snapshot_root="b" * 64,
            expected_reviewed_paths=paths,
        )
