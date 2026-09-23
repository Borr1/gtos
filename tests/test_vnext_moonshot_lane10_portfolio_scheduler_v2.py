from __future__ import annotations

import sys
from datetime import timedelta
from pathlib import Path


ROUTE_DIR = (
    Path(__file__).resolve().parents[1]
    / "research"
    / "operations"
    / "vnext_moonshot_lane10_portfolio_scheduler_v2_2026_06_01"
)
sys.path.insert(0, str(ROUTE_DIR))

from portfolio_scheduler_v2 import (  # noqa: E402
    PortfolioSchedulerV2Engine,
    SchedulerCandidate,
    SchedulerConfig,
    parse_dt,
)


def candidate(
    row_id: str,
    symbol: str,
    decision: str,
    *,
    risk_pct: float = 1.0,
    result_r: float = 1.0,
    origin: str = "liquidity_sweep_reclaim",
    session: str = "london_broad",
    policy: str = "momentum_exhaustion",
    release_minutes: int = 60,
    exit_minutes: int = 60,
    partial_minutes: int | None = None,
) -> SchedulerCandidate:
    decision_dt = parse_dt(decision)
    assert decision_dt is not None
    exit_dt = decision_dt + timedelta(minutes=exit_minutes)
    release_dt = decision_dt + timedelta(minutes=release_minutes)
    partial_dt = decision_dt + timedelta(minutes=partial_minutes) if partial_minutes else None
    return SchedulerCandidate(
        row_id=row_id,
        candidate_id=row_id,
        selected_row_id=row_id,
        symbol=symbol,
        side="LONG",
        decision_dt=decision_dt,
        entry_dt=decision_dt,
        exit_dt=exit_dt,
        risk_release_dt=release_dt,
        partial_release_dt=partial_dt,
        result_r=result_r,
        result_r_class="source_bound_proxy",
        requested_risk_pct=risk_pct,
        source_scheduler_state="test_scheduler_source",
        source_family="test",
        source_priority_state="test",
        session_bucket=session,
        origin_family=origin,
        framework=origin,
        chosen_policy=policy,
        cost_status="test_cost",
        spread_r_bucket="cost_r_le_0_02",
        broker_ready_state="joined_lane07_symbol_spec",
        no_leak_status="pass",
    )


def test_simultaneous_candidate_priority_accepts_best_without_top_n_shortcut():
    engine = PortfolioSchedulerV2Engine(
        SchedulerConfig(base_portfolio_ceiling_pct=1.1, correlated_cluster_ceiling_pct=10.0)
    )
    weak = candidate(
        "weak",
        "EURUSD",
        "2026-01-01T08:00:00Z",
        origin="unknown_origin",
        session="off_kz_broad",
    )
    strong = candidate(
        "strong",
        "XAUUSD",
        "2026-01-01T08:00:00Z",
        origin="liquidity_sweep_reclaim",
        session="london_broad",
        policy="partial_be_runner",
    )

    decisions = {cand.row_id: dec for cand, dec in engine.decide_batch([weak, strong])}

    assert decisions["strong"].accepted is True
    assert decisions["strong"].priority_rank_in_batch == 1
    assert decisions["weak"].accepted is False
    assert decisions["weak"].reason == "portfolio_total_risk_ceiling_exceeded"
    assert decisions["weak"].priority_components["uses_result_fields"] is False


def test_partial_be_release_frees_open_risk_before_final_close():
    cfg = SchedulerConfig(base_portfolio_ceiling_pct=1.1, correlated_cluster_ceiling_pct=10.0)
    with_release = PortfolioSchedulerV2Engine(cfg)
    first = candidate(
        "first",
        "EURUSD",
        "2026-01-01T08:00:00Z",
        policy="partial_be_runner",
        release_minutes=15,
        partial_minutes=15,
        exit_minutes=120,
    )
    second = candidate("second", "XAUUSD", "2026-01-01T08:30:00Z")

    assert with_release.decide(first).accepted is True
    released_second = with_release.decide(second)
    assert released_second.accepted is True
    assert released_second.open_risk_pct_before == 0.0
    assert released_second.residual_exposure_pct_before > 0.0

    without_release = PortfolioSchedulerV2Engine(cfg)
    first_no_release = candidate(
        "first_no_release",
        "EURUSD",
        "2026-01-01T08:00:00Z",
        release_minutes=120,
        exit_minutes=120,
    )
    assert without_release.decide(first_no_release).accepted is True
    blocked_second = without_release.decide(second)
    assert blocked_second.accepted is False
    assert blocked_second.open_risk_pct_before == 1.0


def test_open_pending_new_risk_blocks_oversized_candidate():
    engine = PortfolioSchedulerV2Engine(
        SchedulerConfig(base_portfolio_ceiling_pct=1.1, correlated_cluster_ceiling_pct=10.0)
    )
    first = candidate("first", "EURUSD", "2026-01-01T08:00:00Z", exit_minutes=120)
    second = candidate("second", "XAUUSD", "2026-01-01T08:15:00Z")

    assert engine.decide(first).accepted is True
    decision = engine.decide(second)

    assert decision.accepted is False
    assert decision.open_risk_pct_before == 1.0
    assert decision.total_risk_pct_after > decision.dynamic_portfolio_ceiling_pct


def test_realized_cushion_expands_available_portfolio_budget():
    engine = PortfolioSchedulerV2Engine(
        SchedulerConfig(
            base_portfolio_ceiling_pct=7.23983929,
            correlated_cluster_ceiling_pct=20.0,
        )
    )
    winner = candidate(
        "winner",
        "EURUSD",
        "2026-01-01T08:00:00Z",
        risk_pct=1.0,
        result_r=10.0,
        release_minutes=1,
        exit_minutes=1,
    )
    large_follow = candidate(
        "large_follow",
        "XAUUSD",
        "2026-01-01T08:02:00Z",
        risk_pct=8.0,
    )

    assert engine.decide(winner).accepted is True
    decision = engine.decide(large_follow)

    assert decision.accepted is True
    assert decision.dynamic_portfolio_ceiling_pct > 8.0
    assert decision.realized_proxy_pnl > 0


def test_drawdown_compression_blocks_when_account_cushion_is_breached():
    engine = PortfolioSchedulerV2Engine(
        SchedulerConfig(base_portfolio_ceiling_pct=7.23983929, correlated_cluster_ceiling_pct=20.0)
    )
    loser = candidate(
        "loser",
        "EURUSD",
        "2026-01-01T08:00:00Z",
        risk_pct=1.0,
        result_r=-8.0,
        release_minutes=1,
        exit_minutes=1,
    )
    follow = candidate("follow", "XAUUSD", "2026-01-01T08:02:00Z", risk_pct=1.0)

    assert engine.decide(loser).accepted is True
    decision = engine.decide(follow)

    assert decision.accepted is False
    assert decision.reason == "account_daily_or_overall_limit_exceeded"
    assert decision.account_available_risk_pct < 0


def test_stale_count_cap_is_replaced_by_money_risk_and_oversized_trade_rejects():
    engine = PortfolioSchedulerV2Engine(
        SchedulerConfig(base_portfolio_ceiling_pct=3.2, correlated_cluster_ceiling_pct=10.0)
    )
    smalls = [
        candidate("small1", "EURUSD", "2026-01-01T08:00:00Z", exit_minutes=180),
        candidate("small2", "XAUUSD", "2026-01-01T08:01:00Z", exit_minutes=180),
        candidate("small3", "NAS100", "2026-01-01T08:02:00Z", exit_minutes=180),
    ]
    for item in smalls:
        assert engine.decide(item).accepted is True

    oversized = candidate("oversized", "ETHUSD", "2026-01-01T08:03:00Z", risk_pct=6.0)
    decision = engine.decide(oversized)

    assert engine.stats.accepted_rows == 3
    assert decision.accepted is False
    assert "count" not in decision.reason
    assert decision.reason == "portfolio_total_risk_ceiling_exceeded"


def test_correlated_cluster_exposure_rejects_before_total_portfolio_limit():
    engine = PortfolioSchedulerV2Engine(
        SchedulerConfig(base_portfolio_ceiling_pct=10.0, correlated_cluster_ceiling_pct=1.5)
    )
    first = candidate("gold", "XAUUSD", "2026-01-01T08:00:00Z", exit_minutes=180)
    second = candidate("silver", "XAGUSD", "2026-01-01T08:01:00Z", exit_minutes=180)

    assert engine.decide(first).accepted is True
    decision = engine.decide(second)

    assert decision.accepted is False
    assert decision.reason == "correlated_cluster_exposure_ceiling_exceeded"
    assert decision.correlated_cluster_risk_pct_before == 1.0
