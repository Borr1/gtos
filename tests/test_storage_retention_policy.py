from __future__ import annotations

from datetime import datetime, timezone

from src.research_infra.storage_retention_policy import (
    EVIDENCE_LOG,
    RAW_SOURCE,
    REPORT,
    TEMP_CACHE,
    build_status_row,
    classify_path,
    is_within_root,
)


def test_raw_sierra_depth_file_is_protected(tmp_path):
    path = tmp_path / "data" / "sierrachart_exports" / "NQ.depth"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x" * 10)

    decision = classify_path(path, tmp_path)

    assert decision.retention_class == RAW_SOURCE
    assert decision.deletion_allowed is False
    assert decision.archive_required_before_delete is True


def test_shadow_log_is_evidence_protected(tmp_path):
    path = tmp_path / "shadow_logs" / "strategy_follow_candidates.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{}", encoding="utf-8")

    decision = classify_path(path, tmp_path)

    assert decision.retention_class == EVIDENCE_LOG
    assert decision.deletion_allowed is False


def test_research_report_is_protected(tmp_path):
    path = tmp_path / "research" / "program_control" / "report.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{}", encoding="utf-8")

    decision = classify_path(path, tmp_path)

    assert decision.retention_class == REPORT
    assert decision.deletion_allowed is False


def test_temp_cache_allowlist_is_dry_run_deletable(tmp_path):
    path = tmp_path / ".pytest_cache" / "v" / "cache" / "nodeids"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("x", encoding="utf-8")

    decision = classify_path(path, tmp_path)

    assert decision.retention_class == TEMP_CACHE
    assert decision.deletion_allowed is True
    assert decision.archive_required_before_delete is False


def test_outside_workspace_is_not_deletable(tmp_path):
    outside = tmp_path.parent / "outside.tmp"

    assert is_within_root(outside, tmp_path) is False
    decision = classify_path(outside, tmp_path)
    assert decision.deletion_allowed is False


def test_status_row_is_dry_run_and_preserves_protected_classes(tmp_path):
    (tmp_path / "data" / "sierrachart_exports").mkdir(parents=True)
    (tmp_path / "data" / "sierrachart_exports" / "NQ.depth").write_bytes(b"x" * 1024)
    (tmp_path / "shadow_logs").mkdir()
    (tmp_path / "shadow_logs" / "candidate.jsonl").write_text("{}", encoding="utf-8")
    (tmp_path / ".pytest_cache").mkdir()
    (tmp_path / ".pytest_cache" / "cache.bin").write_bytes(b"x")

    row = build_status_row(
        root=tmp_path,
        now_utc=datetime(2026, 5, 5, 3, 0, tzinfo=timezone.utc),
        max_files=1000,
        top_n=10,
    )

    assert row["storage_status"].startswith("OK_") or row["storage_status"].startswith("STORAGE_RETENTION_")
    assert row["dry_run_only"] is True
    assert row["deletion_performed"] is False
    assert row["no_ai_calls"] is True
    assert row["order_calls"] == 0
    assert row["deletion_allowlist_policy"]["raw_source_delete_allowed"] is False
    assert row["deletion_allowlist_policy"]["evidence_log_delete_allowed"] is False
    assert row["inventory"]["dry_run_cleanup_candidate_count"] == 1
