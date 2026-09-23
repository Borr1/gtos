from __future__ import annotations

from types import SimpleNamespace

from src.components.market_whiteboard_v2 import (
    evaluate_market_whiteboard_v2,
    evaluate_source_completeness,
)
from src.components.permissions import check_permissions
from src.mt5.mt5_mock import MockMT5


def _enabled_config() -> dict:
    return {
        "market": {"symbol": "XAUUSD"},
        "market_whiteboard_v2": {
            "enabled": True,
            "source_requirements": {
                "critical_sources": [
                    "m1",
                    "tick",
                    "spread",
                    "session",
                    "volatility",
                    "correlation",
                ],
                "proxy_allowed": ["volatility", "correlation"],
            },
            "damage_rules": {
                "symbol_hard_min_trades": 6,
                "symbol_hard_max_win_rate": 0.35,
                "symbol_hard_max_net_cash": -500.0,
                "symbol_hard_min_losses": 4,
                "cell_hard_min_trades": 2,
                "cell_hard_max_win_rate": 0.0,
                "cell_hard_max_net_cash": -250.0,
            },
            "zero_trade_quality": {
                "no_trade_classifications": [
                    "no_trade_by_evidence",
                    "source_capture_required",
                ],
            },
        },
        "risk": {"max_spread_cents": 30, "min_rr": 1.5, "sl_absolute_min": 5.0},
    }


def _complete_source_status() -> dict:
    return {
        "m1": "decision-available",
        "tick": "decision-available",
        "spread": "decision-available",
        "session": "decision-available",
        "volatility": "proxy",
        "correlation": "proxy",
    }


def _trade_params(context: dict | None = None) -> SimpleNamespace:
    tp = SimpleNamespace(
        direction="LONG",
        entry_price=2650.0,
        stop_loss=2640.0,
        take_profit_1=2665.0,
        risk_reward_ratio=1.5,
    )
    if context is not None:
        tp.gtos_vnext_market_whiteboard_context = context
    return SimpleNamespace(
        trade_parameters=tp,
        reasoning=SimpleNamespace(
            setup_grade="A+",
            daily_bias=SimpleNamespace(direction="bullish"),
        ),
        framework="ob_retest",
    )


def _mso() -> SimpleNamespace:
    return SimpleNamespace(timeframes={"M15": SimpleNamespace(atr_14=3.0)})


def _state() -> dict:
    return {
        "daily_pnl_pct": 0.0,
        "trades_today": 0,
        "current_kill_zone": "london",
        "trades_london": 0,
        "losses_today": 0,
    }


def test_source_completeness_requires_all_critical_sources() -> None:
    source = _complete_source_status()
    source.pop("tick")

    result = evaluate_source_completeness(source, _enabled_config())

    assert result.state == "incomplete"
    assert "tick" in result.missing_sources
    assert result.stale_or_null_reason[0]["capture_or_repair_requirement"]


def test_damage_memory_quarantines_hard_symbol_session_cell() -> None:
    context = {
        "decision_asof_utc": "2026-05-29T04:45:05.621000+00:00",
        "source_status": _complete_source_status(),
        "damage_memory": {
            "symbol_health": {
                "trades": 12,
                "wins": 2,
                "losses": 10,
                "win_rate": 0.166667,
                "net": -1327.23,
            },
            "symbol_session_side_health": {
                "trades": 4,
                "wins": 1,
                "losses": 3,
                "win_rate": 0.25,
                "net": -595.89,
            },
            "supporting_evidence_tags": [
                "dominant_damage_symbol",
                "stop_loss_or_broker_sl_exit",
            ],
        },
    }

    decision = evaluate_market_whiteboard_v2(
        candidate_symbol="XAUUSD",
        candidate_side="LONG",
        context=context,
        config=_enabled_config(),
    )

    assert decision.action == "QUARANTINE"
    assert decision.disposition == "market_system_mismatch"
    assert decision.damage.symbol_state == "hard_quarantine"


def test_zero_trade_quality_fixture_becomes_positive_no_trade_decision() -> None:
    context = {
        "decision_asof_utc": "2026-06-02T21:30:00+00:00",
        "source_status": _complete_source_status(),
        "candidate_quality_classification": "no_trade_by_evidence",
        "final_outcome": "SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC",
        "source_gap": "path_outcome_missing_for_counterfactual_rank",
    }

    decision = evaluate_market_whiteboard_v2(
        candidate_symbol="AUDJPY",
        candidate_side="LONG",
        context=context,
        config=_enabled_config(),
    )

    assert decision.action == "NO_TRADE"
    assert decision.reason == "zero_trade_by_market_state_quality_evidence"
    assert decision.zero_trade_state["zero_trade_is_positive_decision"] is True


def test_permission_gate_blocks_market_whiteboard_quarantine_when_enabled() -> None:
    mt5 = MockMT5()
    mt5.connect()
    mt5.set_tick(2650.00, 2650.18)
    context = {
        "source_status": _complete_source_status(),
        "damage_memory": {
            "symbol_health": {
                "trades": 12,
                "wins": 2,
                "losses": 10,
                "win_rate": 0.166667,
                "net": -1327.23,
            },
            "symbol_session_side_health": {
                "trades": 4,
                "wins": 1,
                "losses": 3,
                "win_rate": 0.25,
                "net": -595.89,
            },
        },
    }

    denial = check_permissions(
        _trade_params(context),
        _mso(),
        _state(),
        mt5,
        config=_enabled_config(),
        symbol="XAUUSD",
    )

    assert denial is not None
    assert denial.reason == "market_whiteboard_v2_symbol_session_quarantine"
    assert denial.details["action"] == "QUARANTINE"
    assert denial.details["broker_runtime_change_status"] is False


def test_permission_gate_is_inert_when_not_explicitly_enabled() -> None:
    mt5 = MockMT5()
    mt5.connect()
    mt5.set_tick(2650.00, 2650.18)
    context = {
        "source_status": {},
        "candidate_quality_classification": "no_trade_by_evidence",
        "damage_memory": {
            "symbol_health": {
                "trades": 12,
                "wins": 2,
                "losses": 10,
                "win_rate": 0.166667,
                "net": -1327.23,
            }
        },
    }

    denial = check_permissions(
        _trade_params(context),
        _mso(),
        _state(),
        mt5,
        config={"risk": {"max_spread_cents": 30}},
        symbol="XAUUSD",
    )

    assert denial is None
