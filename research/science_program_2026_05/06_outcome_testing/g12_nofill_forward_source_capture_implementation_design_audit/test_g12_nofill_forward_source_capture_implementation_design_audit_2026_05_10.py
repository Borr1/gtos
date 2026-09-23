from __future__ import annotations

import copy

import build_g12_nofill_forward_source_capture_implementation_design_audit_2026_05_10 as builder
import verify_g12_nofill_forward_source_capture_implementation_design_audit_2026_05_10 as verifier


def test_field_closure_recomputes_55_fields_and_status_counts() -> None:
    field_map = builder.read_json(builder.FIELD_MAP)
    audit, blockers = builder.field_closure_audit(field_map)
    assert blockers == []
    assert audit["field_count_actual"] == 55
    assert audit["unique_field_count"] == 55
    assert audit["terminal_status_counts"] == builder.EXPECTED_STATUS_COUNTS


def test_future_logger_rows_have_required_columns_and_owner_gate() -> None:
    field_map = builder.read_json(builder.FIELD_MAP)
    future_design = builder.read_json(builder.FUTURE_LOGGER)
    audit, blockers = builder.future_logger_audit(field_map, future_design)
    assert blockers == []
    assert audit["future_logger_field_count"] == 20
    assert audit["all_future_logger_fields_implementation_ready"] is True
    assert all(row["implementation_ready_without_reinterpretation"] for row in audit["per_field"])


def test_future_logger_audit_rejects_missing_required_column() -> None:
    field_map = copy.deepcopy(builder.read_json(builder.FIELD_MAP))
    for row in field_map["fields"]:
        if row["terminal_implementation_design_status"] == "FUTURE_LOGGER_FIELD_REQUIRED":
            row["rollback_rule"] = ""
            break
    future_design = builder.read_json(builder.FUTURE_LOGGER)
    audit, blockers = builder.future_logger_audit(field_map, future_design)
    assert blockers
    assert audit["all_future_logger_fields_implementation_ready"] is False


def test_schema_failclosed_fixture_coverage_is_exact() -> None:
    audit, blockers = builder.schema_failclosed_audit(
        builder.read_json(builder.FIELD_MAP),
        builder.read_json(builder.FAIL_CLOSED),
        builder.read_json(builder.PARSER_SCHEMA),
        builder.read_json(builder.FIXTURE_MATRIX),
    )
    assert blockers == []
    assert audit["schema_field_count"] == 55
    assert audit["fixture_covered_field_count"] == 55
    assert audit["bad_fail_closed_statuses"] == []


def test_owner_dependency_audit_keeps_wiring_approval_closed() -> None:
    audit, blockers = builder.owner_dependency_audit(
        builder.read_json(builder.OWNER_GATE_LEDGER),
        builder.read_json(builder.DEPENDENCY_GRAPH),
    )
    assert blockers == []
    assert audit["approval_gate_count"] == 5
    assert audit["all_owner_gates_closed_now"] is True
    assert audit["shadow_logger_wiring_requires_owner_approval_chain"] is True


def test_verifier_control_flag_check_rejects_open_validation_flag() -> None:
    failures: list[dict[str, object]] = []
    payload = {
        "promotion_verdict": builder.PROMOTION_VERDICT,
        "validation_safe": True,
        "outcome_review_opened": False,
        "live_effect": False,
        "opens_result_scoring": False,
        "opens_live_wiring": False,
        "opens_paid_api_or_databento_route": False,
        "opens_registry_edit": False,
        "changes_live_trading_behavior": False,
    }
    verifier.verify_control_flags("synthetic.json", payload, failures)
    assert failures
    assert failures[0]["check"] == "required_closed_flag"


def test_saturation_pass_answers_all_required_questions() -> None:
    saturation = builder.saturation_pass()
    assert saturation["question_count"] == 8
    assert saturation["all_saturation_questions_answered"] is True
    assert saturation["same_evidence_class_gaps_exposed"] == []
    assert all(item["status"] == "CLEARED" for item in saturation["questions"])
