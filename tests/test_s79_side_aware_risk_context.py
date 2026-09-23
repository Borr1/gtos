from __future__ import annotations

from src.research_infra.s79_side_aware_risk_context import (
    COMPLETE,
    FILLED_JOINED,
    build_rolling_status,
    build_s79_side_aware_context_rows,
    resolve_risk_context,
)


def _config(**side_aware):
    block = {
        "enabled": True,
        "long_multiplier": 0.5,
        "short_multiplier": 1.0,
        "sprt_window_size": 20,
        "sprt_wr_threshold": 0.5,
    }
    block.update(side_aware)
    return {"risk": {"risk_per_trade_pct": 2.0, "side_aware_sizing": block}}


def _profile():
    return {
        "profile_name": "redacted_account",
        "risk": {"risk_per_trade_pct": 2.0},
        "instruments": {
            "XAUUSD": {"risk": {"risk_per_trade_pct": 1.0}},
            "NAS100": {"risk": {"risk_per_trade_pct": 0.25}},
        },
    }


def _candidate(**overrides):
    row = {
        "schema_version": "strategy_follow_candidate_v1",
        "candidate_id": "XAUUSD_2026-05-04T07:15:00+00:00",
        "created_at_utc": "2026-05-04T07:16:00+00:00",
        "decision_time_utc": "2026-05-04T07:15:00+00:00",
        "symbol": "XAUUSD",
        "broker_symbol": "XAUUSD",
        "side": "LONG",
        "framework": "ob_retest",
        "session": "london",
        "final_outcome_at_log": "LIMIT_PLACED",
        "strategy_snapshots": [
            {"strategy_id": "S79_UNIFORM_FN_RISK_POLICY", "promotion_verdict": "SHIPPED_POLICY_CONTEXT"}
        ],
    }
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
        "created_at_utc": "2026-05-04T22:39:31+00:00",
    }
    row.update(overrides)
    return row


def _j46(**overrides):
    row = {
        "fill_id": "XAUUSD_2026-05-01_london_0815",
        "instrument": "XAUUSD",
        "direction": "SHORT",
        "timestamp_logged": "2026-05-01T14:01:05+00:00",
    }
    row.update(overrides)
    return row


def test_resolve_risk_context_uses_profile_symbol_override_and_side_multiplier():
    ctx = resolve_risk_context(
        symbol="XAUUSD",
        side="LONG",
        config=_config(),
        profile=_profile(),
        sprt_state={"long_outcomes": [], "disabled_at": None, "version": 1},
    )

    assert ctx["profile_name"] == "redacted_account"
    assert ctx["base_risk_per_trade_pct"] == 2.0
    assert ctx["symbol_risk_per_trade_pct"] == 1.0
    assert ctx["side_multiplier_for_row"] == 0.5
    assert ctx["effective_risk_pct_if_side_aware_applied"] == 0.5


def test_candidate_context_snapshot_does_not_claim_actual_r_without_account_history():
    rows = build_s79_side_aware_context_rows(
        [(1, _candidate())],
        config=_config(),
        profile=_profile(),
        sprt_state={"long_outcomes": [{"win": False, "symbol": "NAS100"}], "disabled_at": None, "version": 1},
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    row = rows[0]
    assert row["s79_side_aware_context_status"] == COMPLETE
    assert row["actual_r_claim_allowed"] is False
    assert row["risk_context"]["symbol_risk_per_trade_pct"] == 1.0
    assert row["risk_context"]["effective_risk_pct_if_side_aware_applied"] == 0.5
    assert row["s79_strategy_snapshot_present"] is True
    assert row["ml_label_eligibility"] == "RISK_CONTEXT_ONLY_NO_ACCOUNT_HISTORY_LABEL"


def test_filled_context_joins_account_history_and_uses_j46_side():
    rows = build_s79_side_aware_context_rows(
        [],
        broker_rows=[(1, _broker())],
        j46_rows=[(1, _j46())],
        config=_config(),
        profile=_profile(),
        sprt_state={"long_outcomes": [], "disabled_at": None, "version": 1},
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    row = rows[0]
    assert row["s79_side_aware_context_status"] == FILLED_JOINED
    assert row["side"] == "SHORT"
    assert row["actual_r_claim_allowed"] is True
    assert row["broker_actual_r"] == -0.7395
    assert row["risk_context"]["effective_risk_pct_if_side_aware_applied"] == 1.0
    assert row["ml_label_eligibility"] == "ACCOUNT_HISTORY_LABEL_WITH_RISK_CONTEXT"


def test_row_key_stable_and_rolling_counts():
    kwargs = {
        "candidate_rows": [(1, _candidate())],
        "broker_rows": [(1, _broker())],
        "j46_rows": [(1, _j46())],
        "config": _config(),
        "profile": _profile(),
        "sprt_state": {"long_outcomes": [], "disabled_at": None, "version": 1},
    }
    rows_a = build_s79_side_aware_context_rows(**kwargs, generated_at_utc="2026-05-05T00:00:00+00:00")
    rows_b = build_s79_side_aware_context_rows(**kwargs, generated_at_utc="2026-05-05T01:00:00+00:00")

    assert [row["row_key"] for row in rows_a] == [row["row_key"] for row in rows_b]
    rolling = build_rolling_status(rows_a)
    assert rolling["row_type_counts"]["candidate_risk_context"] == 1
    assert rolling["row_type_counts"]["filled_risk_context"] == 1
    assert rolling["actual_r_claim_allowed_rows"] == 1
