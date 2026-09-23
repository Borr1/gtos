from __future__ import annotations

from src.research_infra.cross_instrument_correlation_decision_status import (
    build_cross_instrument_correlation_decision_report,
    build_cross_instrument_correlation_decision_status,
    summarize_cross_instrument_correlation_decisions,
)


def _config(*, gate_enabled=True, logger_enabled=True):
    return {
        "risk": {
            "cross_instrument_correlation_enabled": gate_enabled,
            "cross_instrument_correlation_threshold": 0.4,
            "cross_instrument_correlation_min_positions": 2,
        },
        "shadow_loggers": {
            "cross_instrument_correlation_decisions_logger": {"enabled": logger_enabled},
        },
    }


def _decision(action="NONE", *, symbol="XAUUSD", context="permissions_gate3_5_reject_check"):
    return {
        "timestamp_utc": "2026-05-18T13:00:00+00:00",
        "candidate_symbol": symbol,
        "candidate_direction": "LONG",
        "evaluation_context": context,
        "gate_action": action,
        "risk_multiplier": 1.0 if action == "NONE" else 0.5,
    }


def test_summarize_cross_instrument_correlation_decisions_counts_actions_and_contexts():
    summary = summarize_cross_instrument_correlation_decisions(
        [
            _decision("NONE", symbol="XAUUSD"),
            _decision("RISK_REDUCE_HALF", symbol="GBPUSD", context="orchestrator_sizing_risk_adjustment"),
            _decision("REJECT", symbol="GBPUSD"),
        ]
    )

    assert summary["decision_rows"] == 3
    assert summary["none_action_rows"] == 1
    assert summary["risk_reduce_half_rows"] == 1
    assert summary["reject_rows"] == 1
    assert summary["candidate_symbol_counts"] == {"GBPUSD": 2, "XAUUSD": 1}
    assert summary["evaluation_context_counts"] == {
        "orchestrator_sizing_risk_adjustment": 1,
        "permissions_gate3_5_reject_check": 2,
    }


def test_runtime_halt_empty_decision_log_is_documented_not_action_required():
    row = build_cross_instrument_correlation_decision_status(
        config=_config(),
        decision_rows=[],
        decision_log_path="shadow_logs/cross_instrument_correlation_decisions.jsonl",
        decision_log_exists=False,
        runtime_halt_active=True,
        generated_at_utc="2026-05-18T00:00:00+00:00",
    )

    assert row["status"] == "OK_NO_CROSS_INSTRUMENT_CORRELATION_ROWS_RUNTIME_HALTED"
    assert row["decision_rows"] == 0
    assert row["action_required_codes"] == []
    assert row["documented_limitation_codes"] == ["NO_DECISION_ROWS_EXPECTED_WHILE_RESEARCH_RUNTIME_HALTED"]


def test_rows_present_status_preserves_gate_action_counts():
    row = build_cross_instrument_correlation_decision_status(
        config=_config(),
        decision_rows=[_decision("NONE"), _decision("REJECT")],
        decision_log_path="shadow_logs/cross_instrument_correlation_decisions.jsonl",
        decision_log_exists=True,
        runtime_halt_active=False,
        generated_at_utc="2026-05-18T00:00:00+00:00",
    )

    assert row["status"] == "OK_CROSS_INSTRUMENT_CORRELATION_DECISION_ROWS_PRESENT"
    assert row["gate_action_counts"] == {"NONE": 1, "REJECT": 1}
    assert row["reject_rows"] == 1
    assert row["runtime_halt_active"] is False


def test_gate_enabled_with_logger_disabled_is_action_required():
    row = build_cross_instrument_correlation_decision_status(
        config=_config(logger_enabled=False),
        decision_rows=[],
        decision_log_path="shadow_logs/cross_instrument_correlation_decisions.jsonl",
        decision_log_exists=False,
        runtime_halt_active=True,
        generated_at_utc="2026-05-18T00:00:00+00:00",
    )

    assert row["status"] == "ACTION_REQUIRED_CROSS_INSTRUMENT_CORRELATION_DECISION_LOGGER_DISABLED"
    assert row["action_required_codes"] == ["CROSS_INSTRUMENT_CORRELATION_DECISION_LOGGER_DISABLED"]
    report = build_cross_instrument_correlation_decision_report(row)
    assert report["status"] == "ACTION_REQUIRED"


def test_row_key_is_stable_across_generated_at_time():
    kwargs = {
        "config": _config(),
        "decision_rows": [_decision("NONE")],
        "decision_log_path": "shadow_logs/cross_instrument_correlation_decisions.jsonl",
        "decision_log_exists": True,
        "runtime_halt_active": False,
    }
    row_a = build_cross_instrument_correlation_decision_status(
        **kwargs,
        generated_at_utc="2026-05-18T00:00:00+00:00",
    )
    row_b = build_cross_instrument_correlation_decision_status(
        **kwargs,
        generated_at_utc="2026-05-18T01:00:00+00:00",
    )

    assert row_a["row_key"] == row_b["row_key"]
    assert row_a["source_dependency_signature"] == row_b["source_dependency_signature"]
