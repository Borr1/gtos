from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


builder = _load_module(
    "g12_mech_replay_audit_builder",
    ROUTE_DIR / "build_g12_no_api_mechanical_replay_engine_source_control_audit_2026_05_10.py",
)
verifier = _load_module(
    "g12_mech_replay_audit_verifier",
    ROUTE_DIR / "verify_g12_no_api_mechanical_replay_engine_source_control_audit_2026_05_10.py",
)


def _read(stem: str) -> dict:
    return json.loads((ROUTE_DIR / f"G12_NO_API_MECHANICAL_REPLAY_{stem}_2026-05-10.json").read_text())


def test_completion_and_decision_are_source_control_acceptance_only() -> None:
    completion = _read("COMPLETION_AUDIT")
    decision = _read("DECISION_LEDGER")
    assert completion["can_mark_goal_complete"] is True
    assert completion["missing_incomplete_or_weak_requirements"] == []
    assert decision["terminal_decision"] == "ACCEPT_AS_NO_API_MECHANICAL_REPLAY_SOURCE_CONTROL_SUBSTRATE"
    for payload in (completion, decision):
        assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"
        assert payload["validation_safe"] is False
        assert payload["outcome_review_opened"] is False
        assert payload["live_effect"] is False


def test_counts_reconcile_and_duplicates_are_explicit() -> None:
    candidate = _read("CANDIDATE_INVENTORY_AUDIT")
    path = _read("DISCOVERY_PATH_LABEL_INVENTORY_AUDIT")
    assert candidate["candidate_row_count_raw_attempts"] == 13_540_033
    assert candidate["duplicate_candidate_keys_reported"] == 687_275
    assert candidate["unique_candidate_denominator"] == 12_852_758
    assert candidate["candidate_rows_written_recomputed"] == 120_000
    assert candidate["dimension_sums_equal_unique_candidate_denominator"] is True
    assert path["path_label_row_count"] == 12_852_758
    assert path["path_label_rows_written_recomputed"] == 120_000
    assert path["no_result_language_in_rows"] is True


def test_lfs_storage_and_dirty_scope_are_safe() -> None:
    lfs = _read("GIT_LFS_STORAGE_AUDIT")
    assert lfs["status"] == "PASS"
    assert lfs["git_lfs_fsck_returncode"] == 0
    assert lfs["raw_blob_violations_over_100mb"] == []
    assert len(lfs["large_jsonl_records"]) == 2
    for record in lfs["large_jsonl_records"]:
        assert record["head_blob_is_lfs_pointer"] is True
        assert record["head_blob_size"] <= 512
        assert record["local_materialized_for_jsonl_parsing"] is True
        assert record["pointer_matches_local_worktree"] is True

    dirty = _read("DIRTY_STATE_SCOPE_AUDIT")
    assert dirty["status"] == "PASS"
    assert dirty["target_route_dirty_overlap_entries"] == []


def test_verifier_accepts_generated_audit_artifacts() -> None:
    result = verifier.verify(ROUTE_DIR)
    assert result["ok"] is True, result["failures"]
    assert result["can_mark_goal_complete"] is True
