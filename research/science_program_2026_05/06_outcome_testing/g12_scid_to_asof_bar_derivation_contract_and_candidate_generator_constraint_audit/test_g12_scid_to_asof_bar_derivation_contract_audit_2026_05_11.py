from __future__ import annotations

import json
import sys
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROUTE_DIR))

import build_g12_scid_to_asof_bar_derivation_contract_audit_2026_05_11 as builder


def test_forbidden_scan_detects_win_window_fail_closed_warning() -> None:
    fields = ["bar_window_start_utc", "bar_window_end_utc", "decision_asof_utc"]
    collisions = builder.scan_forbidden_pattern_collisions(fields, ["win", "path_label"])

    warning_fields = {row["field"] for row in collisions if row["pattern"] == "win"}
    assert warning_fields == {"bar_window_start_utc", "bar_window_end_utc"}
    assert all(row["severity"] == "FAIL_CLOSED_FALSE_POSITIVE_WARNING" for row in collisions)


def test_fixture_review_records_hard_floor_warning_not_blocker() -> None:
    builder.build_all()
    fixture = json.loads(
        (ROUTE_DIR / f"G12_SCID_ASOF_CONTRACT_AUDIT_FIXTURE_COVERAGE_REVIEW_{builder.DATE_TAG}.json").read_text(
            encoding="utf-8"
        )
    )

    assert fixture["checks"]["hard_floor_upstream_source_control_closed"] is True
    assert fixture["checks"]["hard_floor_executable_gap_recorded_as_warning"] is True
    assert fixture["summary"]["warning_count"] == 1


def test_decision_accepts_source_control_only_with_exact_warnings() -> None:
    builder.build_all()
    decision = json.loads(
        (ROUTE_DIR / f"G12_SCID_ASOF_CONTRACT_AUDIT_DECISION_LEDGER_{builder.DATE_TAG}.json").read_text(
            encoding="utf-8"
        )
    )

    assert decision["terminal_decision"] == "ACCEPT_WITH_EXACT_CONTRACT_WARNINGS"
    assert decision["accepted_source_control_scid_asof_contract_only"] is True
    assert decision["accepted_validation_execution"] is False
    assert decision["accepted_result_scoring"] is False
    assert decision["validation_safe"] is False
    assert decision["outcome_review_opened"] is False
    assert decision["live_effect"] is False
    assert len(decision["exact_contract_warnings"]) == 2


def test_next_prompt_preserves_source_control_boundaries() -> None:
    builder.build_all()
    text = builder.NEXT_PROMPT.read_text(encoding="utf-8")

    assert "source-control bar-builder and candidate input-packet materialization only" in text
    assert "must not execute sealed validation" in text
    assert "FORBIDDEN_SCAN_OVERMATCH_WIN_WINDOW" in text
    assert "TARGET_TESTS_DO_NOT_EXECUTE_HARD_FLOOR_CASE" in text
    assert "NO_PROMOTION_VERDICT" in text
    assert "validation_safe=false" in text


def test_required_artifacts_are_emitted() -> None:
    result = builder.build_all()

    required = [
        "decision_ledger",
        "parser_timestamp_review",
        "asof_noleak_review",
        "duplicate_proxy_review",
        "fixture_coverage_review",
        "forbidden_field_review",
        "blocker_ledger",
        "completion_audit",
        "output_manifest",
    ]
    for key in required:
        assert key in result["artifacts"]
    assert (ROUTE_DIR / f"G12_SCID_ASOF_CONTRACT_AUDIT_COMPLETION_AUDIT_{builder.DATE_TAG}.md").exists()
