from __future__ import annotations

from src.research_infra.context_control_audit import (
    ACTION_REQUIRED,
    COMPLETE_WITH_LIMITATIONS,
    DIRECT_VALIDATION_STATUS,
    STRATEGY_VALIDATION_STATUS,
    build_context_control_audit_rows,
    build_rolling_status,
)


def _context_row(**overrides):
    row = {
        "schema_version": "context_control_forward_v1",
        "created_at_utc": "2026-05-04T07:15:25+00:00",
        "symbol": "NAS100",
        "broker_symbol": "NDX100",
        "candidate_id": "NAS100_2026-05-04T07:15:00+00:00",
        "decision_time_utc": "2026-05-04T07:15:00+00:00",
        "side": "LONG",
        "context_question_id": "LIVE_CANDIDATE_CONTEXT_CONTROLS_V1",
        "context_family": "CL_ZN_VIX_CONTROL_CONTEXT",
        "context_values": {"status": "CONTROL_CONTEXT_NOT_JOINED_AT_DECISION_TIME"},
        "control_only": True,
        "evidence_class": "CROSS_INSTRUMENT_CONTEXT",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }
    row.update(overrides)
    return row


def _path_row(**overrides):
    row = {
        "schema_version": "candidate_path_follow_v1",
        "created_at_utc": "2026-05-04T08:00:00+00:00",
        "candidate_id": "NAS100_2026-05-04T07:15:00+00:00",
        "symbol": "NAS100",
        "decision_time_utc": "2026-05-04T07:15:00+00:00",
        "asof_latest_candle_utc": "2026-05-04T08:00:00+00:00",
        "path_label": "continued_without_entry_touch_to_tp_area",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }
    row.update(overrides)
    return row


def test_context_control_audit_marks_legacy_control_row_with_documented_limitations():
    rows = build_context_control_audit_rows(
        [(1, _context_row())],
        [(1, _path_row())],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    assert len(rows) == 1
    row = rows[0]
    assert row["context_control_audit_status"] == COMPLETE_WITH_LIMITATIONS
    assert row["control_role"] == "CONTROL_ONLY"
    assert row["direct_strategy_validation_status"] == DIRECT_VALIDATION_STATUS
    assert row["strategy_validation_status"] == STRATEGY_VALIDATION_STATUS
    assert row["validation_scope"] == "EXPLORATORY_CONTEXT_ONLY"
    assert row["exploratory_outcome_context"]["comparison_role"] == "EXPLORATORY_CONTEXT_ONLY"
    assert row["exploratory_outcome_context"]["candidate_path_label"] == "continued_without_entry_touch_to_tp_area"
    assert "LEGACY_EVIDENCE_CLASS_CROSS_INSTRUMENT_CONTEXT" in row["documented_limitation_codes"]
    assert row["context_family_source_statuses"]["CL"] == "SOURCE_NOT_CAPTURED_AT_DECISION_TIME"
    assert row["context_event_window_snapshot"]["window_anchor_utc"] == "2026-05-04T07:15:00+00:00"


def test_context_control_audit_flags_direct_strategy_validation_claim():
    rows = build_context_control_audit_rows(
        [
            (
                1,
                _context_row(
                    context_values={
                        "strategy_validation_status": "VALIDATED",
                        "actual_r": 1.2,
                    }
                ),
            )
        ],
        [(1, _path_row())],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    row = rows[0]
    assert row["context_control_audit_status"] == ACTION_REQUIRED
    assert "DIRECT_STRATEGY_VALIDATION_FORBIDDEN_IN_CONTEXT_CONTROL" in row["action_required_codes"]
    assert row["direct_strategy_validation_status"] == "DIRECT_STRATEGY_VALIDATION_FORBIDDEN"


def test_context_control_rolling_status_counts_control_boundary():
    rows = build_context_control_audit_rows(
        [(1, _context_row()), (2, _context_row(candidate_id="XAUUSD_2026-05-04T07:15:00+00:00", symbol="XAUUSD"))],
        [(1, _path_row())],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    rolling = build_rolling_status(rows)

    assert rolling["context_rows"] == 2
    assert rolling["control_only_rows"] == 2
    assert rolling["no_promotion_rows"] == 2
    assert rolling["context_family_source_status_counts"]["CL:SOURCE_NOT_CAPTURED_AT_DECISION_TIME"] == 2
