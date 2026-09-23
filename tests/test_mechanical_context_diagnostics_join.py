from __future__ import annotations

from src.research_infra.mechanical_context_diagnostics_join import (
    COMPLETE,
    PARTIAL,
    build_mechanical_context_rows,
    build_rolling_status,
    select_displacement_context,
    select_liquidity_context,
)


def _candidate(**overrides):
    row = {
        "schema_version": "strategy_follow_candidate_v1",
        "candidate_id": "NAS100_2026-05-04T17:00:00+00:00",
        "created_at_utc": "2026-05-04T17:00:26+00:00",
        "decision_time_utc": "2026-05-04T17:00:00+00:00",
        "symbol": "NAS100",
        "broker_symbol": "NDX100",
        "side": "LONG",
        "framework": "ob_retest",
        "session": "ny",
        "final_outcome_at_log": "REJECTED_GATE1_SAFETY",
        "trade_parameters": {
            "direction": "LONG",
            "entry_price": 27446.2,
            "stop_loss": 27387.1,
            "take_profit_1": 27534.8,
        },
    }
    row.update(overrides)
    return row


def _path(**overrides):
    row = {
        "candidate_id": "NAS100_2026-05-04T17:00:00+00:00",
        "created_at_utc": "2026-05-04T19:00:00+00:00",
        "decision_time_utc": "2026-05-04T17:00:00+00:00",
        "asof_latest_candle_utc": "2026-05-04T19:00:00+00:00",
        "path_label": "continued_without_entry_touch_to_tp_area",
        "touched_entry": False,
        "hit_tp1": True,
        "hit_sl": False,
        "path_ambiguity_status": "NO_ENTRY_TOUCH_TP_AREA_NOT_A_FILL",
    }
    row.update(overrides)
    return row


def _dumb(**overrides):
    row = {
        "hypothesis_id": "NAS100_dumb_2026_05_04T17_00_00_00_00",
        "timestamp_utc": "2026-05-04T17:00:05+00:00",
        "candle_time": "2026-05-04T17:00:00+00:00",
        "symbol": "NAS100",
        "kz": "ny",
        "direction": "LONG",
        "bos_direction": "bullish",
        "bos_h1_time": "2026-05-04T14:00:00+00:00",
        "entry": 27446.2,
        "sl": 27387.1,
        "tp": 27534.8,
        "atr_m15": 64.16,
        "impulse_range": 200.0,
        "retrace_pct": 0.8,
        "outcome": "TP",
        "realized_r": 1.5,
        "time_in_trade_bars": 4,
        "exit_time": "2026-05-04T18:00:00+00:00",
    }
    row.update(overrides)
    return row


def _proximity(**overrides):
    row = {
        "trade_id": "unknown",
        "symbol": "NAS100",
        "kill_zone": "ny",
        "candle_time": "2026-05-04T17:00:05+00:00",
        "trade_direction": "LONG",
        "proximity": "inside",
        "distance_to_ob": 0.0,
        "distance_atr_ratio": 0.0,
        "atr_used": 64.2,
        "atr_source": "m15",
        "h1_ob_count": 7,
        "m15_ob_count": 9,
        "relevant_ob_count": 16,
        "timestamp_logged": "2026-05-04T17:00:26+00:00",
    }
    row.update(overrides)
    return row


def _liquidity(**overrides):
    row = {
        "timestamp": "2026-05-04T17:00:26+00:00",
        "direction": "LONG",
        "entry_price": 27446.2,
        "stop_loss": 27387.1,
        "take_profit_1": 27534.8,
        "framework": "ob_retest",
        "setup_grade": "A+",
        "m15_atr": 64.16,
        "margin_required": 32.08,
        "pools_checked": [
            {"type": "pdl", "side": "low", "price": 27407.52, "distance_to_sl": 20.42, "violating": True},
            {"type": "equal_lows", "side": "low", "price": 27317.43, "distance_to_sl": 69.67, "violating": False},
        ],
        "decision": "would_reject",
    }
    row.update(overrides)
    return row


def _displacement(**overrides):
    row = {
        "timestamp_utc": "2026-05-04T17:00:00+00:00",
        "logged_at": "2026-05-04T17:00:20+00:00",
        "symbol": "NAS100",
        "direction": "bullish",
        "classification": "strong",
        "displacement_ratio": 2.1,
        "body": 100.0,
        "avg_body_20": 48.0,
        "body_to_atr": 1.2,
        "atr_14": 80.0,
        "kill_zone": "ny",
        "correlated_with": [],
        "correlation_count": 1,
    }
    row.update(overrides)
    return row


def _structure(**overrides):
    row = {
        "ts": "2026-05-04T17:00:05+00:00",
        "logged_at": "2026-05-04T17:00:06+00:00",
        "symbol": "NAS100",
        "timeframe": "H1",
        "v1_direction": "bullish",
        "v2_direction": "transitional",
        "production_label": "transitional",
        "v2_score": 2,
        "v2_dead_zone": 2,
        "counts": {"hh": 1, "hl": 1, "lh": 0, "ll": 0},
    }
    row.update(overrides)
    return row


def test_liquidity_context_matches_symbolless_row_by_time_and_geometry():
    joined = select_liquidity_context(candidate=_candidate(), rows=[(1, _liquidity(entry_price=1.0)), (2, _liquidity())])

    assert joined["join_status"] == "CONTEXT_NEAR_TIME_GEOMETRY_JOINED"
    assert joined["source_line"] == 2


def test_displacement_respects_observable_logged_at_boundary():
    joined = select_displacement_context(
        candidate=_candidate(created_at_utc="2026-05-04T17:00:26+00:00"),
        rows=[(1, _displacement(logged_at="2026-05-04T18:00:00+00:00"))],
    )

    assert joined["join_status"] == "DISPLACEMENT_JOIN_MISSING_WITHIN_ASOF_WINDOW"


def test_mechanical_context_join_builds_complete_feature_and_label_surface():
    rows = build_mechanical_context_rows(
        [(1, _candidate())],
        path_rows=[(1, _path())],
        dumb_rows=[(1, _dumb())],
        proximity_rows=[(1, _proximity())],
        liquidity_rows=[(1, _liquidity())],
        displacement_rows=[(1, _displacement())],
        structure_rows=[(1, _structure()), (2, _structure(timeframe="M15", v2_score=5))],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    row = rows[0]
    assert row["mechanical_context_status"] == COMPLETE
    assert row["path_context"]["path_label"] == "continued_without_entry_touch_to_tp_area"
    assert row["liquidity_distance_context"]["pool_summary"]["violating_pool_count"] == 1
    assert row["dumb_baseline_context"]["post_decision_comparator_outcome"]["feature_safe"] is False
    assert set(row["structure_divergence_context"]["timeframes"]) == {"H1", "M15"}
    assert row["ml_label_eligibility"] == "SYNTHETIC_PATH_LABEL_WITH_MECHANICAL_CONTEXT_NOT_ACCOUNT_HISTORY"


def test_missing_optional_context_is_documented_not_action_required():
    rows = build_mechanical_context_rows(
        [(1, _candidate(framework="breaker_re_entry"))],
        path_rows=[],
        dumb_rows=[],
        proximity_rows=[],
        liquidity_rows=[],
        displacement_rows=[],
        structure_rows=[],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    row = rows[0]
    assert row["mechanical_context_status"] == PARTIAL
    assert row["action_required_codes"] == []
    assert "PROXIMITY_CONTEXT_MISSING_WITHIN_ASOF_WINDOW" in row["documented_limitation_codes"]


def test_contra_side_displacement_is_context_not_action_required():
    rows = build_mechanical_context_rows(
        [(1, _candidate())],
        path_rows=[(1, _path())],
        dumb_rows=[(1, _dumb())],
        proximity_rows=[(1, _proximity())],
        liquidity_rows=[(1, _liquidity())],
        displacement_rows=[(1, _displacement(direction="bearish"))],
        structure_rows=[(1, _structure())],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    row = rows[0]
    assert row["action_required_codes"] == []
    assert "DISPLACEMENT_DIRECTION_DIFFERS_FROM_SIDE_CONTEXT" in row["mismatch_codes"]


def test_row_key_stable_and_rolling_status_counts():
    kwargs = {
        "candidate_rows": [(1, _candidate())],
        "path_rows": [(1, _path())],
        "dumb_rows": [(1, _dumb())],
        "proximity_rows": [(1, _proximity())],
        "liquidity_rows": [(1, _liquidity())],
        "displacement_rows": [(1, _displacement())],
        "structure_rows": [(1, _structure())],
    }
    rows_a = build_mechanical_context_rows(**kwargs, generated_at_utc="2026-05-05T00:00:00+00:00")
    rows_b = build_mechanical_context_rows(**kwargs, generated_at_utc="2026-05-05T01:00:00+00:00")

    assert [row["row_key"] for row in rows_a] == [row["row_key"] for row in rows_b]
    rolling = build_rolling_status(rows_a)
    assert rolling["status_counts"][COMPLETE] == 1
    assert rolling["mechanical_context_join_counts"]["liquidity_distance"]["CONTEXT_NEAR_TIME_GEOMETRY_JOINED"] == 1
    assert rolling["dumb_baseline_realized_r_by_path_label"]["continued_without_entry_touch_to_tp_area"]["mean_r"] == 1.5
