from __future__ import annotations

from datetime import datetime, timezone

from scripts import build_vnext_lane02_broad_selected_portfolio_replay_stress as lane02


def dt(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)


def selected_row(
    *,
    selected_row_id: str,
    symbol: str,
    decision: str,
    exit_time: str,
    risk_release: str,
    partial_release: str | None = None,
    final_r: float = 1.0,
) -> dict:
    return {
        "chosen_policy": "partial_be_runner",
        "date": decision[:10],
        "day_of_week": "Mon",
        "decision_dt": dt(decision),
        "entry_dt": dt(decision),
        "exit_dt": dt(exit_time),
        "final_r": final_r,
        "framework": "broader_origin",
        "holding_hours": 1.0,
        "m1_availability_status": "local_m1_bar_available_for_entry_minute",
        "market_type": "fx",
        "month": decision[:7],
        "ordered_path_status": "ordered_path_not_ambiguous_in_m15_replay",
        "origin_family": "liquidity_sweep_reclaim",
        "partial_fraction": 0.5,
        "partial_release_dt": dt(partial_release) if partial_release else None,
        "partial_release_source_status": (
            "exact_be_trigger_time_from_dynamic_policy_trace"
            if partial_release
            else "partial_trigger_probable_but_exact_time_missing_strict_risk_released_at_exit"
        ),
        "recent_vs_old": "recent_2025_2026",
        "regime": "up|normal_recent_vs_baseline|low_disp",
        "residual_exposure_fraction_after_partial": 0.5 if partial_release else None,
        "risk_cell_id": f"{symbol}|cell",
        "risk_release_dt": dt(risk_release),
        "same_bar_ambiguity": False,
        "selected_cell_risk_pct": 1.0,
        "selected_row_id": selected_row_id,
        "selector_component": "broader_origin_configured_session",
        "session_bucket": "london_broad",
        "side": "LONG",
        "source_mode": "OHLC_M15_CSV_ASOF_REPLAY",
        "source_quality_status": "m1_entry_minute_available",
        "source_window_complete": True,
        "spread_r_bucket": "spread_or_cost_r_missing",
        "stop_freeze_feasibility_status": "broker_geometry_positive_stop_freeze_feasible_proxy",
        "symbol": symbol,
        "tick_availability_status": "local_tick_source_date_absent_after_data_ticks_search",
        "trend_state_20": "up",
        "volatility_state_14_vs_50": "normal_recent_vs_baseline",
        "year": decision[:4],
    }


def contract(ceiling_pct: float = 1.5) -> dict:
    return {
        "per_candidate_buffer_pct": 0.0,
        "portfolio_open_risk_ceiling_pct": ceiling_pct,
    }


def test_source_partial_release_changes_open_risk_stress_acceptance():
    rows = [
        selected_row(
            selected_row_id="A1",
            symbol="EURUSD",
            decision="2026-01-01T00:00:00Z",
            partial_release="2026-01-01T00:15:00Z",
            risk_release="2026-01-01T00:15:00Z",
            exit_time="2026-01-01T01:00:00Z",
        ),
        selected_row(
            selected_row_id="B1",
            symbol="GBPUSD",
            decision="2026-01-01T00:30:00Z",
            risk_release="2026-01-01T01:30:00Z",
            exit_time="2026-01-01T01:30:00Z",
        ),
    ]

    partial = lane02.simulate_scheduler(
        rows,
        contract(),
        scenario_id="partial",
        same_symbol_conflict=True,
        partial_release_enabled=True,
    )["scenario_summary"]
    worst_case = lane02.simulate_scheduler(
        rows,
        contract(),
        scenario_id="worst",
        same_symbol_conflict=True,
        partial_release_enabled=False,
    )["scenario_summary"]

    assert partial["stats"]["accepted_rows"] == 2
    assert worst_case["stats"]["accepted_rows"] == 1
    assert worst_case["rejected_reason_counts"] == {
        "portfolio_open_pending_new_risk_ceiling_exceeded_after_buffer": 1
    }


def test_same_symbol_conflict_persists_after_partial_risk_release():
    rows = [
        selected_row(
            selected_row_id="A1",
            symbol="EURUSD",
            decision="2026-01-01T00:00:00Z",
            partial_release="2026-01-01T00:15:00Z",
            risk_release="2026-01-01T00:15:00Z",
            exit_time="2026-01-01T01:00:00Z",
        ),
        selected_row(
            selected_row_id="A2",
            symbol="EURUSD",
            decision="2026-01-01T00:30:00Z",
            risk_release="2026-01-01T01:30:00Z",
            exit_time="2026-01-01T01:30:00Z",
        ),
    ]

    result = lane02.simulate_scheduler(
        rows,
        contract(ceiling_pct=2.0),
        scenario_id="partial",
        same_symbol_conflict=True,
        partial_release_enabled=True,
    )["scenario_summary"]

    assert result["stats"]["accepted_rows"] == 1
    assert result["rejected_reason_counts"] == {
        "same_symbol_conflict_strict_lane01_semantics": 1
    }


