"""Focused tests for the G0 NOFILL forward projection synthesis route."""

from __future__ import annotations

import json
from pathlib import Path

import build_g0_nofill_forward_projection_synthesis_control_route_2026_05_09 as builder
import verify_g0_nofill_forward_projection_synthesis_control_route_2026_05_09 as verifier


BASE = Path(__file__).resolve().parent


def test_payload_preserves_source_control_boundaries() -> None:
    payload = builder.build_payload()
    for doc in (
        payload["field_matrix"],
        payload["schema_requirements"],
        payload["completion_audit"],
    ):
        assert doc["promotion_verdict"] == "NO_PROMOTION_VERDICT"
        assert doc["validation_safe"] is False
        assert doc["outcome_review_opened"] is False
        assert doc["live_effect"] is False
        assert doc["opens_result_scoring"] is False
        assert doc["opens_live_wiring"] is False
        assert doc["opens_paid_api_or_databento_route"] is False
        assert doc["opens_registry_edit"] is False
        assert doc["changes_live_trading_behavior"] is False


def test_counts_and_g12_terminal_decision_are_reconciled() -> None:
    payload = builder.build_payload()
    schema = payload["schema_requirements"]
    partition = schema["projection_partition"]
    assert schema["terminal_g12_source_projection_decision"] == "ACCEPT_AS_SOURCE_CONTROL_PROJECTION_EVIDENCE_ONLY"
    assert partition["projection_row_count"] == 298
    assert partition["family_counts"] == {
        "accepted": 225,
        "reject": 65,
        "source_control": 4,
        "source_impossible": 4,
    }
    assert partition["row_level_accepted_denominator"] == 225
    assert partition["primary_duplicate_key_denominator"] == 182
    assert partition["secondary_duplicate_group_denominator"] == 139
    assert partition["reject_overlap_rows"] == 47


def test_rank_one_route_is_offline_source_capture_contract() -> None:
    ranking = builder.route_ranking()
    assert ranking[0]["rank"] == 1
    assert ranking[0]["route"] == "NOFILL_FORWARD_SOURCE_CAPTURE_CONTRACT_HARDENING_AND_OFFLINE_PROJECTION_PROTOTYPE"
    assert ranking[0]["opens_result_scoring"] is False
    assert ranking[0]["opens_live_wiring"] is False
    assert "Owner-approved" in ranking[0]["required_gate_before_live_wiring"]
    assert all(route["opens_result_scoring"] is False for route in ranking)
    assert all(route["opens_live_wiring"] is False for route in ranking)


def test_future_schema_contains_required_control_families() -> None:
    payload = builder.build_payload()
    fields = {
        row["field_name"]: row
        for row in payload["schema_requirements"]["future_capture_field_requirements"]
    }
    required = {
        "capture_write_completed_at_utc",
        "capture_latency_ms",
        "capture_clock_skew_ms",
        "capture_timestamp_derivation_rule",
        "pending_order_mode_source_safe",
        "broker_pending_order_created_status",
        "native_pending_order_type_source_safe",
        "raw_ticket_field_present_status",
        "mt5_order_ticket_redaction_status",
        "decision_spread_value_source_safe",
        "entry_touch_spread_value_source_safe",
        "terminal_area_touch_status",
        "terminal_area_first_touch_utc",
        "same_tick_same_bar_ambiguity_status",
        "nofill_duplicate_key_sha256",
        "duplicate_group_id_sha256",
        "forbidden_field_scan_status",
        "regime_context_status",
        "kill_switch_observability_status",
    }
    assert required.issubset(fields)
    assert fields["decision_spread_value_source_safe"]["result_or_cost_label_opened_now"] is False
    assert fields["entry_touch_spread_value_source_safe"]["result_or_cost_label_opened_now"] is False


def test_generated_json_artifacts_parse_after_build() -> None:
    builder.build_artifacts()
    for name in builder.REQUIRED_JSON:
        payload = json.loads((BASE / name).read_text(encoding="utf-8"))
        assert payload["route_id"] == builder.ROUTE_ID
        assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"


def test_verifier_passes_after_build() -> None:
    builder.build_artifacts()
    result = verifier.verify()
    assert result["status"] == "PASS", result["issues"]
    assert result["can_mark_goal_complete_after_commit"] is True
