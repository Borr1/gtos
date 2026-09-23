#!/usr/bin/env python3
"""Focused tests for the NOFILL forward addendum projection plan."""

from __future__ import annotations

import json
from pathlib import Path

import build_nofill_forward_contract_addendum_projection_plan_2026_05_09 as builder


OUT_DIR = Path(__file__).resolve().parent


def test_all_three_blockers_have_closure_decisions() -> None:
    closures = builder.blocker_closures()
    decisions = {item["blocker_id"]: item["closure_decision"] for item in closures}
    assert set(decisions) == {
        "G12-FWD-BLOCKER-001",
        "G12-FWD-BLOCKER-002",
        "G12-FWD-BLOCKER-003",
    }
    assert decisions["G12-FWD-BLOCKER-001"].startswith("CLOSED_BY_ADDENDUM")
    assert decisions["G12-FWD-BLOCKER-002"].startswith("CLOSED_BY_ALLOWLIST")
    assert decisions["G12-FWD-BLOCKER-003"].startswith("CLOSED_BY_SOURCE_SAFE")


def test_projection_schema_contains_required_addendum_fields() -> None:
    schema = builder.projection_field_schema(builder.blocker_closures())
    field_names = {field["field_name"] for field in schema["fields"]}
    assert schema["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert schema["validation_safe"] is False
    assert schema["outcome_review_opened"] is False
    assert schema["live_effect"] is False
    assert "capture_latency_ms" in field_names
    assert "mt5_order_ticket_redaction_status" in field_names
    assert "slippage_label_status" in field_names
    assert "execution_quality_label_status" in field_names
    assert field_names.isdisjoint(builder.FORBIDDEN_OUTPUT_FIELD_NAMES)


def test_dry_run_projection_redacts_ticket_order_fill_and_result_values() -> None:
    raw = {
        "created_at_utc": "2026-05-09T10:00:00+00:00",
        "pending_order_mode": "INTERNAL_CANDLE_POLLED_INTENT",
        "broker_pending_order_created": True,
        "native_pending_order_type": "SELL_LIMIT",
        "mt5_order_ticket": 111222333,
        "pending_ticket": "pending-secret",
        "trade_state_ticket": 444555666,
        "order_send_attempted": True,
        "order_send_success": True,
        "broker_fill_state": "filled",
        "fill_time_utc": "2026-05-09T10:01:00+00:00",
        "slippage_price": 1.23,
        "actual_r": 9.99,
        "synthetic_path_r": -1.0,
        "spread": 7.0,
    }
    projected = builder.project_source_safe_status(
        raw,
        source_root="shadow_logs/pending_limit_lifecycle.jsonl",
    )
    issues = builder.projection_has_forbidden_leak(projected, raw)
    assert issues == []
    text = json.dumps(projected, sort_keys=True)
    assert "111222333" not in text
    assert "pending-secret" not in text
    assert "444555666" not in text
    assert "filled" not in text
    assert projected["mt5_order_ticket_redaction_status"] == "SOURCE_TICKET_VALUE_REDACTED"
    assert projected["slippage_value_redaction_status"] == "RAW_SLIPPAGE_VALUE_PRESENT_REDACTED"
    assert projected["execution_quality_label_status"] == "NOT_OPENED_FOR_SOURCE_CONTROL"
    assert projected["cost_testing_gate_status"] == "COST_TESTING_NOT_OPENED"


def test_generated_json_artifacts_parse_and_preserve_closed_flags() -> None:
    json_names = [
        "NOFILL_FORWARD_CONTRACT_ADDENDUM_2026-05-09.json",
        "NOFILL_FORWARD_PROJECTION_FIELD_SCHEMA_2026-05-09.json",
        "NOFILL_FORWARD_LATENCY_CLOCK_SKEW_CAPTURE_SPEC_2026-05-09.json",
        "NOFILL_FORWARD_SPREAD_SLIPPAGE_EXECUTION_QUALITY_STATUS_SPEC_2026-05-09.json",
        "NOFILL_FORWARD_NO_LEAK_AND_FORBIDDEN_FIELD_AUDIT_2026-05-09.json",
    ]
    for name in json_names:
        data = json.loads((OUT_DIR / name).read_text(encoding="utf-8"))
        assert data["promotion_verdict"] == "NO_PROMOTION_VERDICT"
        assert data["validation_safe"] is False
        assert data["outcome_review_opened"] is False
        assert data["live_effect"] is False
        if "opens_result_scoring" in data:
            assert data["opens_result_scoring"] is False


def test_no_leak_audit_fixture_passes() -> None:
    schema = builder.projection_field_schema(builder.blocker_closures())
    audit = builder.no_leak_audit(schema, builder.blocker_closures())
    assert audit["status"] == "PASS"
    assert audit["dry_run_projection_fixture"]["leak_issues"] == []
    assert audit["output_field_violations"] == []
