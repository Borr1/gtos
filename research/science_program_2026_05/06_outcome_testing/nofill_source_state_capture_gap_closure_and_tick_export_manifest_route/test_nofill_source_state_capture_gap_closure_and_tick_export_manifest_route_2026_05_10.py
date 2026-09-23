"""Focused tests for the NOFILL source-state gap closure route artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import build_nofill_source_state_capture_gap_closure_and_tick_export_manifest_route_2026_05_10 as builder
import verify_nofill_source_state_capture_gap_closure_and_tick_export_manifest_route_2026_05_10 as verifier


ROUTE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(builder.REPO_ROOT))
from src.research_infra import forward_capture as fc  # noqa: E402


def _json(name: str) -> dict:
    return json.loads((ROUTE_DIR / name).read_text(encoding="utf-8"))


def test_counts_and_safe_flags_are_preserved() -> None:
    decision = _json(f"{builder.PREFIX}_DECISION_LEDGER_{builder.DATE}.json")
    assert decision["terminal_decision"] == builder.TERMINAL_DECISION
    assert decision["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert decision["validation_safe"] is False
    assert decision["outcome_review_opened"] is False
    assert decision["live_effect"] is False
    assert decision["accepted_upstream_counts"] == {
        "admitted_source_bound_rows": 2,
        "blocked_rows": 37,
        "duplicate_denominators": "2/2/2",
        "rejected_rows": 9,
        "repaired_packet_hash": builder.EXPECTED_PACKET_SHA,
    }
    assert decision["required_fact_preservation"]["tick_export_dependent_blockers"] == 31
    assert decision["required_fact_preservation"]["contamination_embargo_blockers"] == 17


def test_all_blockers_have_allowed_terminal_status_and_ladder() -> None:
    pursuit = _json(f"{builder.PREFIX}_ACTIVE_PURSUIT_LADDER_LEDGER_{builder.DATE}.json")
    assert pursuit["row_count"] == 37
    assert pursuit["all_terminal_statuses_allowed"] is True
    statuses = {row["terminal_status"] for row in pursuit["rows"]}
    assert statuses <= builder.ALLOWED_TERMINAL_STATUSES
    assert pursuit["terminal_status_counts"] == {
        "CONTAMINATION_EMBARGO_EXCLUDED": 17,
        "FORWARD_CAPTURE_REQUIRED_NON_GENERATABLE_HISTORICAL_STATE": 1,
        "RECOVERABLE_MARKET_DATA_EXTRACTION_SPECIFIED": 19,
    }
    for row in pursuit["rows"]:
        assert len(row["active_pursuit_ladder"]) == 6
        assert row["requires_forward_capture"] is True
        assert row["exact_next_action"]


def test_55_field_contract_closure_matches_runtime_contract() -> None:
    closure = _json(f"{builder.PREFIX}_55_FIELD_CLOSURE_LEDGER_{builder.DATE}.json")
    assert closure["field_count"] == 55
    assert closure["required_field_count"] == 55
    assert closure["all_fields_closed"] is True
    assert {row["field_name"] for row in closure["rows"]} == set(fc.NOFILL_FORWARD_SOURCE_CAPTURE_FIELDS)
    assert "exact_forward_capture_requirement" in closure["closure_class_counts"]
    assert "forbidden_redacted_status_only" in closure["closure_class_counts"]
    assert "schema_only_control" in closure["closure_class_counts"]


def test_tick_owner_and_contamination_manifests_are_exact() -> None:
    tick = _json(f"{builder.PREFIX}_TICK_EXPORT_EXTRACTION_MANIFEST_{builder.DATE}.json")
    owner = _json(f"{builder.PREFIX}_OWNER_ACTION_MANIFEST_{builder.DATE}.json")
    contamination = _json(f"{builder.PREFIX}_CONTAMINATION_EMBARGO_HANDLING_LEDGER_{builder.DATE}.json")
    recovered = _json(f"{builder.PREFIX}_RECOVERED_SOURCE_STATE_MANIFEST_{builder.DATE}.json")

    assert tick["tick_export_dependent_blocker_count"] == 31
    assert len(tick["rows"]) == 31
    assert owner["owner_tick_export_request_count"] == len(tick["unique_export_requests"])
    assert owner["forward_capture_owner_approval_required"] is True
    assert contamination["contamination_embargo_blocker_count"] == 17
    assert all(row["handling_status"] == "CONTAMINATION_EMBARGO_EXCLUDED" for row in contamination["rows"])
    assert recovered["recovered_source_state_count"] == 0
    assert recovered["negative_evidence_row_count"] == 37


def test_verifier_accepts_generated_route() -> None:
    result = verifier.verify()
    assert result["ok"] is True
    assert result["can_mark_goal_complete"] is True
    assert result["failures"] == []
