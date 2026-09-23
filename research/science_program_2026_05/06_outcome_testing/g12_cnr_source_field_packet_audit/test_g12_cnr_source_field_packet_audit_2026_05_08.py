from __future__ import annotations

import importlib.util
from pathlib import Path


LANE_DIR = Path(__file__).resolve().parent


def load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, LANE_DIR / filename)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_row_decision_accepts_ready_input_only_row() -> None:
    builder = load_module("g12_builder", "build_g12_cnr_source_field_packet_audit_2026_05_08.py")
    row = {
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "account_history_accessed": False,
        "broker_actual_r_accessed": False,
        "live_order_state_accessed": False,
        "live_trade_results_accessed": False,
        "blocked_packet_outcome_source_read": False,
        "mt5_order_calls": 0,
        "order_calls": 0,
        "paid_data_calls": 0,
        "databento_calls": 0,
        "api_calls": 0,
        "canary_calls": 0,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "packet_id": "OTG0-PKT-060",
        "timing_model_family": "CNR_E0_DECISION_CLOSE_MARKET",
        "target_model_family": "CNR_T0_ORIGINAL_TP1",
        "forbidden_field_scan_result": "PASS_PACKET_ROW_INPUT_ONLY_NO_FORBIDDEN_RESULT_FIELDS",
        "blocker_state": "READY_INPUT_ONLY_FOR_G12_G0_AUDIT",
    }
    decision, blockers, requirements = builder.row_decision(row)
    assert decision == builder.ACCEPT
    assert blockers == []
    assert requirements == []


def test_row_decision_blocks_with_exact_requirements() -> None:
    builder = load_module("g12_builder", "build_g12_cnr_source_field_packet_audit_2026_05_08.py")
    row = {
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "account_history_accessed": False,
        "broker_actual_r_accessed": False,
        "live_order_state_accessed": False,
        "live_trade_results_accessed": False,
        "blocked_packet_outcome_source_read": False,
        "mt5_order_calls": 0,
        "order_calls": 0,
        "paid_data_calls": 0,
        "databento_calls": 0,
        "api_calls": 0,
        "canary_calls": 0,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "packet_id": "OTG0-PKT-061",
        "timing_model_family": "CNR_E2_SIGNAL_EMIT_FIRST_VALID_TICK",
        "target_model_family": "CNR_T1_FIXED_R_FROM_EXECUTABLE_ENTRY",
        "forbidden_field_scan_result": "PASS_PACKET_ROW_INPUT_ONLY_NO_FORBIDDEN_RESULT_FIELDS",
        "blocker_state": "BLOCKED_WITH_EXACT_SOURCE_FIELD_REQUIREMENTS",
        "blockers": [
            "BLOCKED_TIMING_TRIGGER_NOT_MATERIALIZED",
            "requires frozen R multiple, stop model, and executable quote binding before outcome opening",
        ],
        "signal_emitted_utc": None,
    }
    decision, blockers, requirements = builder.row_decision(row)
    assert decision == builder.BLOCK
    assert "BLOCKED_TIMING_TRIGGER_NOT_MATERIALIZED" in blockers
    assert any("signal_emitted_utc" in requirement for requirement in requirements)
    assert any("fixed-R target" in requirement or "fixed-R" in requirement for requirement in requirements)


def test_generated_audit_verifier_passes_after_build() -> None:
    verifier = load_module("g12_verifier", "verify_g12_cnr_source_field_packet_audit_2026_05_08.py")
    result = verifier.verify()
    assert result["status"] == "PASS", result
