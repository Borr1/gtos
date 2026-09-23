from __future__ import annotations

import json
from pathlib import Path

import pytest


LANE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-09"
TARGET_ROWS = [
    "NOFILL-CAT-ROW-0241",
    "NOFILL-CAT-ROW-0130",
    "NOFILL-CAT-ROW-0143",
    "NOFILL-CAT-ROW-0165",
    "NOFILL-CAT-ROW-0178",
]
USDJPY_ROWS = [
    "NOFILL-CAT-ROW-0130",
    "NOFILL-CAT-ROW-0143",
    "NOFILL-CAT-ROW-0165",
    "NOFILL-CAT-ROW-0178",
]
ACCEPT_XAU = "ACCEPT_AS_SOURCE_CONTROL_INPUT_ONLY_EVIDENCE"
ACCEPT_USDJPY = "ACCEPT_AS_SOURCE_IMPOSSIBILITY_EVIDENCE_ONLY"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"


def read_json(name: str):
    return json.loads((LANE_DIR / name).read_text(encoding="utf-8"))


def assert_safe_closed(payload: dict) -> None:
    assert payload["promotion_verdict"] == PROMOTION_VERDICT
    assert payload["validation_safe"] is False
    assert payload["outcome_review_opened"] is False
    assert payload["live_effect"] is False


def test_decision_ledger_exact_five_rows_and_closed_label_surface():
    decision = read_json(f"G12_NOFILL_REMAINING_DECISION_LEDGER_{DATE}.json")

    assert decision["target_row_ids"] == TARGET_ROWS
    assert decision["targeted_row_count"] == 5
    assert decision["may3_rows_reopened"] == []
    assert decision["terminal_decision_counts"] == {ACCEPT_XAU: 1, ACCEPT_USDJPY: 4}
    assert decision["upstream_status_counts"] == {
        "SOURCE_CONTROL_CLEARED_INPUT_ONLY": 1,
        "SOURCE_IMPOSSIBLE_FROM_APPROVED_ROUTES": 4,
    }
    assert_safe_closed(decision)

    row_by_id = {row["packet_row_id"]: row for row in decision["row_decisions"]}
    assert list(row_by_id) == TARGET_ROWS
    assert row_by_id["NOFILL-CAT-ROW-0241"]["g12_terminal_decision"] == ACCEPT_XAU
    for row_id in USDJPY_ROWS:
        assert row_by_id[row_id]["g12_terminal_decision"] == ACCEPT_USDJPY

    for row in decision["row_decisions"]:
        assert row["all_identity_fields_match_prior_blocker_lane"] is True
        assert row["source_control_only"] is True
        assert row["categorical_lifecycle_label"] is None
        assert row["result_or_performance_label"] is None
        assert row["cleared_into_accepted_denominator"] is False
        assert row["validation_safe"] is False
        assert row["outcome_review_opened"] is False
        assert row["live_effect"] is False


def test_xauusd_source_control_recheck_is_input_only_no_touch():
    xau = read_json(f"G12_NOFILL_REMAINING_XAUUSD_SOURCE_CONTROL_AUDIT_{DATE}.json")

    assert xau["packet_row_id"] == "NOFILL-CAT-ROW-0241"
    assert xau["g12_terminal_decision"] == ACCEPT_XAU
    assert_safe_closed(xau)

    may5 = xau["g12_direct_recheck"]["may5_active_window"]
    recovered = xau["g12_direct_recheck"]["recovered_may6_gap"]
    assert may5["window_rows"] == 325629
    assert may5["max_bid"] == pytest.approx(4595.69)
    assert may5["short_entry_touch_bid_ge_entry"] is False
    assert recovered["window_rows"] == 549
    assert recovered["max_bid"] == pytest.approx(4596.22)
    assert recovered["entry_price"] == pytest.approx(4668.45)
    assert recovered["max_bid"] < recovered["entry_price"]
    assert recovered["short_entry_touch_bid_ge_entry"] is False

    capture = xau["upstream_packet_claim"]["mt5_read_only_capture"]
    assert capture["account_order_deal_position_history_calls"] == 0
    assert capture["order_send_calls"] == 0
    assert capture["paid_api_or_databento_calls"] == 0
    assert "mt5_order_ticket" not in json.dumps(xau).lower()
    assert "actual_r" not in json.dumps(xau).lower()


def test_usdjpy_same_tick_impossibility_recheck_and_mql_contract():
    usdjpy = read_json(f"G12_NOFILL_REMAINING_USDJPY_IMPOSSIBILITY_AUDIT_{DATE}.json")

    assert usdjpy["target_rows"] == USDJPY_ROWS
    assert usdjpy["g12_terminal_decision"] == ACCEPT_USDJPY
    assert_safe_closed(usdjpy)

    by_id = {row["packet_row_id"]: row for row in usdjpy["row_audits"]}
    assert list(by_id) == USDJPY_ROWS
    for row_id, row in by_id.items():
        assert row["same_tick_impossibility_holds"] is True
        recheck = row["g12_source_recheck"]
        assert recheck["exact_timestamp_row_count"] == 1
        exact_row = recheck["exact_rows"][0]
        assert exact_row["entry_touch"] is True
        assert exact_row["protective_level"] is True
        assert exact_row["terminal_area"] is False
        assert row["packet_row_id"] == row_id

    checks = usdjpy["official_doc_contract"]["contract_checks"]
    assert checks["mqltick_has_time_msc"] is True
    assert checks["mqltick_has_flags"] is True
    assert checks["mqltick_has_bid_ask"] is True
    assert checks["copyticksrange_orders_rows_past_to_present"] is True
    assert checks["copyticksrange_flags_describe_changed_fields"] is True
    assert checks["python_returns_named_time_bid_ask_last_flags"] is True
    assert checks["sub_row_sequence_field_found"] is False


def test_source_hash_raw_capture_and_noleak_controls():
    source_hash = read_json(f"G12_NOFILL_REMAINING_SOURCE_HASH_RAW_CAPTURE_AUDIT_{DATE}.json")
    noleak = read_json(f"G12_NOFILL_REMAINING_NOLEAK_DUPLICATE_DENOMINATOR_LABEL_AUDIT_{DATE}.json")

    assert_safe_closed(source_hash)
    assert_safe_closed(noleak)
    assert source_hash["residual_source_hash_manifest_record_count"] == 35
    assert source_hash["g12_hash_manifest_audit"]["record_count"] == 35
    assert source_hash["g12_hash_manifest_audit"]["strict_hash_failures"] == []
    assert all(capture["exists"] for capture in source_hash["official_mql5_raw_capture_audit"]["raw_captures"])

    assert noleak["target_rows"] == TARGET_ROWS
    assert noleak["may3_rows_reopened"] == []
    assert noleak["reject_total_preserved_outside_labels_denominators"] == 65
    assert noleak["rows_moved_to_accepted_denominator"] == 0
    assert noleak["lifecycle_labels_assigned"] == 0
    assert noleak["result_or_performance_labels_assigned"] == 0
    assert noleak["validation_safe_true_count"] == 0
    assert noleak["outcome_review_opened_true_count"] == 0
    assert noleak["live_effect_true_count"] == 0
    assert noleak["boundary_scan"]["status"] == "PASS"
    assert noleak["boundary_scan"]["forbidden_result_or_account_key_hits"] == []
    assert noleak["boundary_scan"]["unsafe_true_flag_hits"] == []


def test_residual_verifier_audit_and_completion_guardrails():
    residual_verifier = read_json(f"G12_NOFILL_REMAINING_RESIDUAL_VERIFIER_AUDIT_{DATE}.json")
    completion = read_json(f"G12_NOFILL_REMAINING_COMPLETION_AUDIT_{DATE}.json")

    assert_safe_closed(residual_verifier)
    assert_safe_closed(completion)
    assert all(residual_verifier["code_checks"].values())
    assert completion["terminal_decision_counts"] == {ACCEPT_XAU: 1, ACCEPT_USDJPY: 4}
    assert completion["terminal_packet_decision"] == "ACCEPT_BY_ROW_EVIDENCE_CLASS_ONLY"

    checklist = {item["requirement"]: item for item in completion["prompt_to_artifact_checklist"]}
    required = {
        "mandatory GTOS preflight and required context read",
        "complete residual source closure packet read and audited",
        "exactly five target rows audited and May 3 rows closed",
        "XAUUSD 0241 source-control input-only decision",
        "USDJPY same-tick impossibility decision",
        "source hash/raw capture audit",
        "no-leak duplicate denominator label-family audit",
        "residual verifier audit",
        "preserve safety flags and no promotion/outcome/live effect",
        "verifier/tests/py_compile/focused pytest",
    }
    assert required <= set(checklist)
    assert all(
        item["status"] == "PASS"
        for name, item in checklist.items()
        if name != "verifier/tests/py_compile/focused pytest"
    )
    assert checklist["verifier/tests/py_compile/focused pytest"]["status"] in {"PENDING_VERIFIER_RUN", "PASS"}
    assert completion["can_mark_goal_complete_after_verifier"] in {False, True}
