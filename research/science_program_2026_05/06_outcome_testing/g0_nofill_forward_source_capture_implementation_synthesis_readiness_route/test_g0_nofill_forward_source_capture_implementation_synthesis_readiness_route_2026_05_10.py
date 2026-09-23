"""Focused tests for the G0 NOFILL source-capture synthesis/readiness route."""

from __future__ import annotations

import json
from pathlib import Path

import build_g0_nofill_forward_source_capture_implementation_synthesis_readiness_route_2026_05_10 as builder
import verify_g0_nofill_forward_source_capture_implementation_synthesis_readiness_route_2026_05_10 as verifier


BASE = Path(__file__).resolve().parent


def test_payload_preserves_closed_boundaries() -> None:
    payload = builder.build_payload()
    for doc in payload.values():
        assert doc["promotion_verdict"] == "NO_PROMOTION_VERDICT"
        assert doc["validation_safe"] is False
        assert doc["outcome_review_opened"] is False
        assert doc["live_effect"] is False
        assert doc["opens_result_scoring"] is False
        assert doc["opens_validation"] is False
        assert doc["opens_promotion"] is False
        assert doc["opens_registry_edit"] is False
        assert doc["opens_paid_api_or_databento_route"] is False
        assert doc["opens_live_trading_behavior"] is False


def test_g12_accepted_implementation_is_reconciled_on_main() -> None:
    payload = builder.build_payload()
    decision = payload["decision_ledger"]
    summary = decision["accepted_implementation_summary"]
    assert decision["terminal_decision"] == builder.TERMINAL_DECISION
    assert decision["canonical_source_control_implementation_evidence_on_main"] is True
    assert summary["g12_terminal_decision"] == "ACCEPT_AS_SOURCE_CONTROL_IMPLEMENTATION_EVIDENCE_ONLY"
    assert summary["g12_exact_repair_blocker_count"] == 0
    assert summary["g12_runtime_field_count"] == 55
    assert summary["g12_runtime_unique_field_count"] == 55
    assert summary["g12_future_logger_field_count"] == 20
    assert summary["g12_forbidden_output_keys"] == []
    assert summary["g12_secret_marker_leaks"] == []
    assert summary["g12_raw_value_hash_hits"] == []


def test_shadow_readiness_records_no_row_or_rows_present_state() -> None:
    payload = builder.build_payload()
    readiness = payload["readiness_audit"]
    assert readiness["shadow_readiness_state"] in {
        "SOURCE_CONTROL_READY_EXPECTED_NO_ROW_OWNER_RESTART_OR_NEXT_CANDIDATE_CHECK_REQUIRED",
        "ROWS_PRESENT_SCHEMA_AUDIT_REQUIRED",
    }
    assert readiness["code_path_evidence"]["runtime_field_count"] == 55
    assert readiness["code_path_evidence"]["future_logger_field_count"] == 20
    assert readiness["code_path_evidence"]["writer_function_present"] is True
    assert readiness["code_path_evidence"]["additive_call_present_in_forward_shadow_helper"] is True
    assert readiness["broken_logger_evidence_found"] is False


def test_owner_actions_are_exact_and_non_live_mutating() -> None:
    payload = builder.build_payload()
    actions = payload["owner_ledger"]["actions"]
    assert {action["action_id"] for action in actions} == {
        "OWNER-LIVE-001",
        "OWNER-LIVE-002",
        "OWNER-LIVE-003",
    }
    assert all(action["performed_by_this_route"] is False for action in actions)
    assert all(action["changes_trading_logic"] is False for action in actions)


def test_generated_artifacts_parse_and_have_required_completion() -> None:
    builder.build_artifacts()
    for name in builder.REQUIRED_JSON:
        payload = json.loads((BASE / name).read_text(encoding="utf-8"))
        assert payload["route_id"] == builder.ROUTE_ID
        assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"
        assert payload["validation_safe"] is False
    completion = json.loads(
        (BASE / "G0_NOFILL_FORWARD_SOURCE_CAPTURE_COMPLETION_AUDIT_2026-05-10.json").read_text(
            encoding="utf-8"
        )
    )
    assert completion["completion_standard_satisfied"] is True
    assert completion["missing_incomplete_or_weak_requirements"] == []
    assert completion["next_strongest_goal_lane"] == (
        "NOFILL_HISTORICAL_SEALED_VALIDATION_PARTITION_LEDGER_AND_SOURCE_BINDING_ROUTE"
    )


def test_verifier_passes_after_build() -> None:
    builder.build_artifacts()
    result = verifier.verify()
    assert result["status"] == "PASS", result["issues"]
    assert result["can_mark_goal_complete_after_commit"] is True
    assert result["g12_terminal_decision"] == "ACCEPT_AS_SOURCE_CONTROL_IMPLEMENTATION_EVIDENCE_ONLY"
    assert result["g12_exact_repair_blocker_count"] == 0
