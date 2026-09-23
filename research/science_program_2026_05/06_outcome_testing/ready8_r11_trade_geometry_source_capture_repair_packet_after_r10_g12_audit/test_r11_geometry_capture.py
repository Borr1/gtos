"""Focused tests for the R11 READY8 trade-geometry source-capture packet."""

from __future__ import annotations

import json
from pathlib import Path

import verify_r11_geometry_capture as verifier


ROUTE_DIR = Path(__file__).resolve().parent
DATE = verifier.DATE


def iter_jsonl(name: str):
    with (ROUTE_DIR / name).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def read_json(name: str):
    with (ROUTE_DIR / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_verifier_core_without_external_completion_marks_passes() -> None:
    result = verifier.verify(
        require_focused_tests=False,
        require_artifact_audit=False,
        prompt_hardening_ok=True,
        starter_hardening_ok=True,
    )
    assert result["ok"], result["errors"]
    assert result["checks"]["binding_row_count"] == 5502
    assert result["checks"]["capture_requirement_row_count"] == 5502
    assert result["checks"]["exact_r_rows"] == 0


def test_every_row_has_capture_requirement_and_no_exact_r() -> None:
    binding = list(iter_jsonl(f"R11_GEOMETRY_BINDING_ATTEMPT_LEDGER_{DATE}.jsonl"))
    capture = list(iter_jsonl(f"R11_UNREPAIRED_ROW_CAPTURE_REQUIREMENT_LEDGER_{DATE}.jsonl"))
    repaired = list(iter_jsonl(f"R11_REPAIRED_GEOMETRY_RESULT_LEDGER_{DATE}.jsonl"))
    assert len(binding) == len(capture) == len(repaired) == 5502
    assert all(row["exact_source_bound_repair_status"].startswith("NO_EXACT_SOURCE_BOUND") for row in repaired)
    assert all(row["required_capture_fields"] for row in capture)
    assert all(row["missing_fields"] for row in capture)


def test_expanded_source_roots_preserve_weak_matches_without_promoting_them() -> None:
    source_roots = list(iter_jsonl(f"R11_SOURCE_ROOT_EXPANSION_LEDGER_{DATE}.jsonl"))
    binding = list(iter_jsonl(f"R11_GEOMETRY_BINDING_ATTEMPT_LEDGER_{DATE}.jsonl"))
    assert len(source_roots) >= 50
    weak_rows = [row for row in binding if row["weak_shadow_or_live_symbol_time_match_count"]]
    assert weak_rows
    assert all("REJECTED" in row["weak_match_use_decision"] for row in weak_rows)
    assert all(row["exact_source_bound_repair_status"].startswith("NO_EXACT_SOURCE_BOUND") for row in weak_rows)


def test_safe_flags_and_completion_status_are_closed() -> None:
    decision = read_json(f"R11_DECISION_LEDGER_{DATE}.json")
    completion = read_json(f"R11_COMPLETION_AUDIT_{DATE}.json")
    assert decision["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert decision["validation_safe"] is False
    assert decision["outcome_review_opened"] is False
    assert decision["live_effect"] is False
    assert decision["summary_counts"]["exact_r_expectancy_rows_computed"] == 0
    assert completion["same_evidence_class_repairable_intelligence_remaining"] == 0
    assert completion["all_rows_have_capture_requirement"] is True
