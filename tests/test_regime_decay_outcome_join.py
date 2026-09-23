from __future__ import annotations

from src.research_infra.regime_decay_outcome_join import (
    COMPLETE,
    REGIME_MISSING,
    build_regime_decay_outcome_rows,
    build_rolling_status,
    select_asof_regime,
)


def _candidate(**overrides):
    row = {
        "schema_version": "strategy_follow_candidate_v1",
        "candidate_id": "XAUUSD_2026-05-04T07:15:00+00:00",
        "created_at_utc": "2026-05-04T07:15:25+00:00",
        "decision_time_utc": "2026-05-04T07:15:00+00:00",
        "symbol": "XAUUSD",
        "broker_symbol": "XAUUSD",
        "side": "SHORT",
        "framework": "ob_retest",
        "session": "london",
        "final_outcome_at_log": "LIMIT_PLACED",
        "trade_id": "lim_2026-05-04_0715",
    }
    row.update(overrides)
    return row


def _path(**overrides):
    row = {
        "schema_version": "candidate_path_follow_v1",
        "candidate_id": "XAUUSD_2026-05-04T07:15:00+00:00",
        "created_at_utc": "2026-05-04T19:00:00+00:00",
        "decision_time_utc": "2026-05-04T07:15:00+00:00",
        "asof_latest_candle_utc": "2026-05-04T19:00:00+00:00",
        "symbol": "XAUUSD",
        "path_label": "continued_without_entry_touch_to_tp_area",
        "touched_entry": False,
        "hit_tp1": True,
        "hit_sl": False,
        "path_ambiguity_status": "NO_ENTRY_TOUCH_TP_AREA_NOT_A_FILL",
    }
    row.update(overrides)
    return row


def _regime(**overrides):
    row = {
        "ts": "2026-05-04T07:15:05+00:00",
        "logged_at": "2026-05-04T07:15:06+00:00",
        "symbol": "XAUUSD",
        "regime": "trending_bear",
        "classifier_version": "v1.0-option-a-h4-swing",
        "lookback": 20,
        "reason": "test",
        "raw_features": {"score": -4, "h4_direction": "bearish"},
    }
    row.update(overrides)
    return row


def _ob(**overrides):
    row = {
        "date_utc": "2026-05-04",
        "scope": "XAUUSD",
        "window_size": "50",
        "window_start_date": "2024-04-02",
        "window_end_date": "2026-04-17",
        "continuation_count": "34",
        "total_count": "45",
        "rate_pct": "75.5556",
        "alarm_fired": "false",
        "insufficient_sample": "true",
    }
    row.update(overrides)
    return row


def _portfolio_ob(**overrides):
    row = _ob(
        scope="PORTFOLIO",
        continuation_count="37",
        total_count="50",
        rate_pct="74.0",
        insufficient_sample="false",
    )
    row.update(overrides)
    return row


def _broker(**overrides):
    row = {
        "schema_version": "broker_actual_r_audit_v1",
        "row_key": "broker-row",
        "fill_id": "XAUUSD_2026-05-01_london_0815",
        "trade_id": "XAUUSD_2026-05-01_london_0815",
        "symbol": "XAUUSD",
        "broker_symbol": "XAUUSD",
        "decision_time_utc": "2026-05-01T14:00:05+00:00",
        "audit_scope": "filled_trade_reconciliation",
        "accounting_evidence_class": "ACCOUNT_HISTORY_REALIZED",
        "truth_lane": "ACCOUNT_HISTORY_REALIZED",
        "actual_r_claim_allowed": True,
        "broker_actual_r": -0.7395,
        "created_at_utc": "2026-05-05T00:00:00+00:00",
    }
    row.update(overrides)
    return row


def test_select_asof_regime_allows_same_close_grace_before_candidate_created():
    joined = select_asof_regime(
        symbol="XAUUSD",
        decision_time_utc="2026-05-04T07:15:00+00:00",
        source_row=_candidate(),
        regime_rows=[(1, _regime())],
    )

    assert joined["join_status"] == "REGIME_ASOF_OR_SAME_CLOSE_JOINED"
    assert joined["offset_seconds"] == 5
    assert joined["age_seconds"] == 0


def test_candidate_join_keeps_actual_r_false_and_adds_decay_context():
    rows = build_regime_decay_outcome_rows(
        [(1, _candidate())],
        path_rows=[(1, _path())],
        regime_rows=[(1, _regime())],
        ob_rows=[(1, _ob()), (2, _portfolio_ob())],
        monthly_decay_report={"status": "MONTHLY_DECAY_REPORT_PRESENT", "path": "report.md", "mtime_utc": "2026-05-04T00:00:00+00:00", "age_days": 1.0},
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    row = rows[0]
    assert row["regime_decay_context_status"] == COMPLETE
    assert row["actual_r_claim_allowed"] is False
    assert row["regime_context"]["regime"] == "trending_bear"
    assert row["ob_continuation_context"]["symbol_scope_snapshot"]["rate_pct"] == 75.5556
    assert row["ml_label_eligibility"] == "NO_ACTUAL_R_LABEL_PATH_CONTEXT_WITH_REGIME_DECAY"


def test_missing_regime_is_documented_not_action_required():
    rows = build_regime_decay_outcome_rows(
        [(1, _candidate())],
        path_rows=[(1, _path())],
        regime_rows=[],
        ob_rows=[(1, _ob()), (2, _portfolio_ob())],
        monthly_decay_report={"status": "MONTHLY_DECAY_REPORT_PRESENT"},
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    row = rows[0]
    assert row["regime_decay_context_status"] == REGIME_MISSING
    assert row["action_required_codes"] == []
    assert "REGIME_JOIN_MISSING_WITHIN_ASOF_WINDOW" in row["documented_limitation_codes"]


def test_filled_context_joins_account_history_and_portfolio_fallback_for_missing_symbol_scope():
    rows = build_regime_decay_outcome_rows(
        [],
        broker_rows=[(1, _broker(symbol="NAS100", broker_symbol="NAS100"))],
        regime_rows=[(1, _regime(symbol="NAS100", ts="2026-05-01T14:00:05+00:00", regime="trending_bull"))],
        ob_rows=[(1, _portfolio_ob(date_utc="2026-05-01"))],
        monthly_decay_report={"status": "MONTHLY_DECAY_REPORT_PRESENT"},
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    row = rows[0]
    assert row["actual_r_claim_allowed"] is True
    assert row["broker_actual_r"] == -0.7395
    assert row["ob_continuation_context"]["symbol_scope_status"] == "OB_CONTINUATION_SYMBOL_SCOPE_UNAVAILABLE_PORTFOLIO_ONLY"
    assert row["ob_continuation_context"]["portfolio_scope_snapshot"]["rate_pct"] == 74.0
    assert row["ml_label_eligibility"] == "ACCOUNT_HISTORY_LABEL_WITH_REGIME_DECAY_CONTEXT"


def test_row_key_stable_and_rolling_status_counts():
    kwargs = {
        "candidate_rows": [(1, _candidate())],
        "path_rows": [(1, _path())],
        "regime_rows": [(1, _regime())],
        "ob_rows": [(1, _ob()), (2, _portfolio_ob())],
        "monthly_decay_report": {"status": "MONTHLY_DECAY_REPORT_PRESENT"},
    }
    rows_a = build_regime_decay_outcome_rows(**kwargs, generated_at_utc="2026-05-05T00:00:00+00:00")
    rows_b = build_regime_decay_outcome_rows(**kwargs, generated_at_utc="2026-05-05T01:00:00+00:00")

    assert [row["row_key"] for row in rows_a] == [row["row_key"] for row in rows_b]
    rolling = build_rolling_status(rows_a)
    assert rolling["status_counts"][COMPLETE] == 1
    assert rolling["daily_regime_mix"]["2026-05-04"]["trending_bear"] == 1
    assert rolling["weekly_regime_mix"]["2026-W19"]["trending_bear"] == 1
