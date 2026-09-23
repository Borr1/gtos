from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from src.components.broker_net_cost_engine import (
    BROKER_TRUE_COMMISSION_MODE,
    LEGACY_ZERO_COMMISSION_COMPARATOR_MODE,
    PRETRADE_COST_PACKET_SCHEMA_VERSION,
    build_pretrade_cost_packet,
    is_vnext_broker_net_cost_required,
    pretrade_cost_refusal_reason,
)
from src.components.permissions import check_permissions
from src.components.execution import ExecutionEngine
from src.components.ultimate_book.minimal_size import (
    MinimalSizeConfig,
    MinimalSizeScaler,
    NotionalLedger,
)
from src.mt5.mt5_mock import MockMT5
from src.research.moonshot_default_off_policy_router import route_moonshot_dynamic_execution


def _runtime_cfg(**overrides):
    cfg = {
        "enabled": True,
        "mode": "production_replacement_vnext_moonshot",
        "apply_to_execution": True,
        "selected_cell_pretrade_cost_model_required": True,
        "selected_cell_pretrade_max_spread_r": 0.10,
        "selected_cell_pretrade_max_total_cost_r": 0.15,
        "selected_cell_commission_model_required": True,
        "selected_cell_profile_namespace_required": True,
        "selected_cell_symbol_spec_required": True,
        "selected_cell_swap_model_required": True,
        "selected_cell_slippage_model_required": True,
        "selected_cell_broker_hours_required": True,
        "selected_cell_default_expected_slippage_r": 0.02,
        "selected_cell_allowed_commission_model_statuses": [
            "SELECTED_CELL_RISK_LEDGER_VERIFIED_NO_EXECUTION_CRITICAL_COMMISSION_GAP",
        ],
    }
    cfg.update(overrides)
    return cfg


def _config(namespace="redacted_account_live_bee34003", *, runtime_overrides=None):
    return {
        "profile_name": "redacted_account",
        "runtime": {"broker_account_namespace": namespace},
        "broker_profile": {
            "broker": "redacted_account",
            "company": "redacted_account Ltd",
            "server": "redacted_account-Server 2",
        },
        "market": {
            "symbol": "XAUUSD",
            "mt5_symbol": "XAUUSD",
            "point": 0.01,
            "trade_tick_size": 0.01,
            "trade_tick_value": 1.0,
            "trade_contract_size": 100.0,
            "volume_min": 0.01,
            "volume_max": 50.0,
            "volume_step": 0.01,
            "trade_stops_level": 0,
            "trade_freeze_level": 0,
            "spread": 53,
            "trade_mode": 4,
            "filling_mode": 3,
            "swap_long": -107.151,
            "swap_short": -46.917,
        },
        "risk": {"max_spread_cents": 1000, "sl_absolute_min": 0.01},
        "deployment": {"phase": 3},
        "gtos_vnext_runtime": _runtime_cfg(**(runtime_overrides or {})),
    }


def _trade_params(**overrides):
    params = {
        "direction": "LONG",
        "entry_price": 4460.0,
        "stop_loss": 4450.0,
        "take_profit_1": 4480.0,
        "risk_reward_ratio": 2.0,
        "gtos_vnext_production_execution_path": True,
        "gtos_vnext_selected_cell_risk_pct": 0.25,
        "gtos_vnext_selected_cell_risk_cell_id": "risk-cell-xau",
        "gtos_vnext_selected_cell_risk_decision_basis": "selected_cell_broker_net_gate",
        "gtos_vnext_commission_model_status": (
            "SELECTED_CELL_RISK_LEDGER_VERIFIED_NO_EXECUTION_CRITICAL_COMMISSION_GAP"
        ),
    }
    params.update(overrides)
    return params


def _points_swap_symbol_info(*, rollover3days=3):
    return SimpleNamespace(
        point=0.01,
        trade_tick_size=0.01,
        trade_tick_value=1.0,
        trade_contract_size=100.0,
        volume_min=0.01,
        volume_max=50.0,
        volume_step=0.01,
        trade_stops_level=0,
        trade_freeze_level=0,
        spread=53,
        trade_mode=4,
        filling_mode=3,
        swap_long=-100.0,
        swap_short=-100.0,
        swap_mode=1,
        swap_rollover3days=rollover3days,
    )


def test_pretrade_packet_captures_profile_spec_spread_swap_and_slippage():
    tick = SimpleNamespace(bid=4459.5, ask=4460.0, spread_cents=50.0)

    packet = build_pretrade_cost_packet(
        config=_config(),
        trade_params=_trade_params(),
        tick=tick,
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        entry_price=4460.0,
        stop_loss=4450.0,
        sl_distance=10.0,
        risk_pct=0.25,
    )

    assert is_vnext_broker_net_cost_required(_config(), _trade_params()) is True
    assert packet["schema_version"] == PRETRADE_COST_PACKET_SCHEMA_VERSION
    assert packet["status"] == "PASSED"
    assert packet["profile"]["broker_account_namespace"] == "redacted_account_live_bee34003"
    assert packet["symbol_spec"]["source_status"] == "captured"
    assert packet["swap"]["value"] == pytest.approx(-107.151)
    assert packet["explicit_session_table"]["source_status"] == "source_gap"
    assert packet["explicit_session_table"]["authority_note"] == (
        "trade_mode availability is not explicit trading-session table authority"
    )
    assert packet["expected_slippage_r"] == pytest.approx(0.02)
    assert packet["spread_r"] == pytest.approx(0.05)
    assert packet["model_version"] == "vnext_selected_cell_pretrade_cost_model_v3"
    assert packet["commission_mode"] == BROKER_TRUE_COMMISSION_MODE
    assert packet["commission_cost"]["source_status"] == "captured"
    assert packet["commission_cost"]["artifact"] == "BROKER_TRUE_COSTS_V1.json"
    assert packet["commission_cost"]["usd_per_lot_round_turn"] == pytest.approx(7.1317184)
    assert packet["commission_r"] == pytest.approx(0.0071317184)
    assert packet["total_cost_components"]["commission_r"] == pytest.approx(0.0071317184)
    assert packet["total_cost_components_expected"] == [
        "spread_r", "expected_slippage_r", "swap_cost_r", "commission_r",
    ]
    assert packet["cost_excludes"] == []
    assert packet["total_cost_r"] == pytest.approx(0.0771317184)
    assert packet["forbidden_surface_status"]["order_calls"] == 0
    assert pretrade_cost_refusal_reason(packet) is None


def test_pretrade_packet_uses_symbol_info_swap_when_config_lacks_swap_fields():
    cfg = _config()
    cfg["market"].pop("swap_long")
    cfg["market"].pop("swap_short")
    tick = SimpleNamespace(bid=4459.5, ask=4460.0, spread_cents=50.0)
    symbol_info = SimpleNamespace(
        point=0.01,
        trade_tick_size=0.01,
        trade_tick_value=1.0,
        trade_contract_size=100.0,
        volume_min=0.01,
        volume_max=50.0,
        volume_step=0.01,
        trade_stops_level=0,
        trade_freeze_level=0,
        spread=53,
        trade_mode=4,
        filling_mode=3,
        swap_long=-12.5,
        swap_short=-4.25,
        swap_mode=1,
        swap_rollover3days=3,
        currency_base="XAU",
        currency_profit="USD",
        currency_margin="USD",
    )

    packet = build_pretrade_cost_packet(
        config=cfg,
        trade_params=_trade_params(),
        tick=tick,
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        entry_price=4460.0,
        stop_loss=4450.0,
        sl_distance=10.0,
        risk_pct=0.25,
        symbol_info=symbol_info,
    )

    assert packet["status"] == "PASSED"
    assert packet["swap"]["value"] == pytest.approx(-12.5)
    assert packet["symbol_spec"]["fields"]["swap_long"] == pytest.approx(-12.5)
    assert packet["symbol_spec"]["fields"]["currency_profit"] == "USD"
    assert pretrade_cost_refusal_reason(packet) is None


def test_points_mode_swap_drag_enters_total_cost_r_and_can_refuse():
    tick = SimpleNamespace(bid=4459.5, ask=4460.0, spread_cents=50.0)
    symbol_info = SimpleNamespace(
        point=0.01,
        trade_tick_size=0.01,
        trade_tick_value=1.0,
        trade_contract_size=100.0,
        volume_min=0.01,
        volume_max=50.0,
        volume_step=0.01,
        trade_stops_level=0,
        trade_freeze_level=0,
        spread=53,
        trade_mode=4,
        filling_mode=3,
        swap_long=-100.0,
        swap_short=5.0,
        swap_mode=1,
        swap_rollover3days=3,
    )

    packet = build_pretrade_cost_packet(
        config=_config(runtime_overrides={"selected_cell_swap_cost_model_required": True}),
        trade_params=_trade_params(gtos_vnext_dynamic_time_stop_bars=96),
        tick=tick,
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        entry_price=4460.0,
        stop_loss=4450.0,
        sl_distance=10.0,
        risk_pct=0.25,
        symbol_info=symbol_info,
    )

    assert packet["swap_cost"]["source_status"] == "captured"
    assert packet["swap_cost"]["daily_cost_r"] == pytest.approx(0.1)
    assert packet["swap_cost"]["cost_r"] == pytest.approx(0.1)
    assert packet["total_cost_components"]["swap_cost_r"] == pytest.approx(0.1)
    assert packet["total_cost_r"] == pytest.approx(0.1771317184)
    assert packet["status"] == "REFUSED"
    assert "total_cost_r_exceeds_limit" in " ".join(packet["refusal_reasons"])


@pytest.mark.parametrize(
    ("entry_utc", "rollover3days", "expected_nights"),
    (
        ("2026-06-23T22:00:00+00:00", 3, 0.0),
        ("2026-06-22T20:00:00+00:00", 5, 1.0),
        ("2026-06-23T20:00:00+00:00", 3, 3.0),
    ),
)
def test_pretrade_swap_charges_actual_broker_rollovers_not_fractional_days(
    entry_utc: str,
    rollover3days: int,
    expected_nights: float,
) -> None:
    packet = build_pretrade_cost_packet(
        config=_config(runtime_overrides={"selected_cell_swap_cost_model_required": True}),
        trade_params=_trade_params(gtos_vnext_dynamic_time_stop_bars=32),
        tick=SimpleNamespace(bid=4459.5, ask=4460.0, spread_cents=50.0),
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        entry_price=4460.0,
        stop_loss=4450.0,
        sl_distance=10.0,
        risk_pct=0.25,
        symbol_info=_points_swap_symbol_info(rollover3days=rollover3days),
        asof_utc=entry_utc,
    )

    assert packet["swap_cost"]["model_version"] == (
        "broker_rollover_crossing_swap_cost_r_v2"
    )
    assert packet["swap_cost"]["swap_charge_basis"] == (
        "broker_wall_midnight_crossings"
    )
    assert packet["swap_cost"]["rollover_nights_charged"] == expected_nights
    assert packet["swap_cost"]["cost_r"] == pytest.approx(0.1 * expected_nights)


@pytest.mark.parametrize("f5_target_usd", (None, 10.0))
@pytest.mark.parametrize(
    ("candidate_asof_utc", "expected_nights", "expected_status"),
    (
        # Eight forecast hours beginning after the broker rollover cross no midnight.
        ("2026-06-23T22:00:00+00:00", 0.0, "PASSED"),
        # The same horizon beginning one hour before rollover crosses one midnight.
        ("2026-06-22T20:00:00+00:00", 1.0, "REFUSED"),
    ),
)
def test_execution_cost_gate_uses_candidate_asof_for_rollover_and_is_f5_invariant(
    tmp_path: Path,
    candidate_asof_utc: str,
    expected_nights: float,
    expected_status: str,
    f5_target_usd: float | None,
) -> None:
    """The live execution seam must forward the candidate instant into broker-clock costs.

    ``build_pretrade_cost_packet`` already knows how to count broker rollover crossings, but
    that truth is useless if ``ExecutionEngine`` omits the candidate's bound ``asof_utc`` and
    lets the packet fall back to fractional holding days.  Exercise both the normal engine and
    the $10 F5 engine: the scaler is downstream and must not change this economic decision.
    """

    mt5 = MockMT5(balance=100_000.0)
    mt5.connect()
    symbol_info = _points_swap_symbol_info(rollover3days=5)
    mt5._mt5 = SimpleNamespace(symbol_info=lambda _symbol: symbol_info)

    scaler = None
    if f5_target_usd is not None:
        f5_cfg = MinimalSizeConfig(
            enabled=True,
            target_risk_usd=f5_target_usd,
            notional_initial_usd=100_000.0,
        )
        scaler = MinimalSizeScaler(
            f5_cfg,
            NotionalLedger(tmp_path / "f5_notional_ledger.json", f5_cfg),
        )

    engine = ExecutionEngine(
        mt5,
        _config(runtime_overrides={"selected_cell_swap_cost_model_required": True}),
        f5_scaler=scaler,
    )
    trade_params = _trade_params(
        asof_utc=candidate_asof_utc,
        decision_time_utc=candidate_asof_utc,
        gtos_vnext_dynamic_time_stop_bars=32,
    )
    packet, _reason = engine._vnext_pretrade_cost_model(
        trade_params=trade_params,
        tick=SimpleNamespace(bid=4459.5, ask=4460.0, spread_cents=50.0),
        entry_price=4460.0,
        sl_distance=10.0,
        risk_pct=0.25,
    )

    assert packet["asof_utc"] == candidate_asof_utc
    assert packet["risk_pct"] == pytest.approx(0.25)
    assert packet["swap_cost"]["swap_charge_basis"] == "broker_wall_midnight_crossings"
    assert packet["swap_cost"]["rollover_nights_charged"] == expected_nights
    assert packet["swap_cost"]["cost_r"] == pytest.approx(0.1 * expected_nights)
    assert packet["status"] == expected_status


def test_resolved_schedule_does_not_call_history_deals_get(monkeypatch):
    """A schedule that returns a rate must not pull the terminal's deal history."""

    calls = []

    def history_deals_get(*args, **kwargs):
        calls.append((args, kwargs))
        return []

    monkeypatch.setattr(
        "src.components.broker_net_cost_engine.commission_usd_per_lot_for_packet",
        lambda *args, **kwargs: 5.0,
    )
    mt5 = MockMT5(balance=100_000.0)
    mt5.connect()
    symbol_info = _points_swap_symbol_info()
    mt5._mt5 = SimpleNamespace(
        symbol_info=lambda _symbol: symbol_info,
        history_deals_get=history_deals_get,
    )
    engine = ExecutionEngine(mt5, _config())
    packet, _reason = engine._vnext_pretrade_cost_model(
        trade_params=_trade_params(),
        tick=SimpleNamespace(bid=4459.5, ask=4460.0, spread_cents=50.0),
        entry_price=4460.0,
        sl_distance=10.0,
        risk_pct=0.25,
    )

    assert calls == []
    assert packet["commission_cost"]["usd_per_lot_round_turn"] == pytest.approx(5.0)
    assert packet["commission_cost"]["artifact"] == "BROKER_TRUE_COSTS_V1.json"
    assert packet["commission_cost"]["account_deal_commission"] is None


def test_missing_schedule_calls_history_deals_get_once(monkeypatch):
    """The reader runs once, and only once, when the schedule lookup returns None."""

    calls = []
    entry = SimpleNamespace(
        symbol="XAUUSD", type=0, entry=0, volume=1.0, price=1000.0,
        commission=-5.0, position_id=11,
    )
    exit_deal = SimpleNamespace(
        symbol="XAUUSD", type=1, entry=1, volume=1.0, price=1000.0,
        commission=-5.0, position_id=11,
    )

    def history_deals_get(*args, **kwargs):
        calls.append((args, kwargs))
        return [entry, exit_deal]

    monkeypatch.setattr(
        "src.components.broker_net_cost_engine.commission_usd_per_lot_for_packet",
        lambda *args, **kwargs: None,
    )
    mt5 = MockMT5(balance=100_000.0)
    mt5.connect()
    symbol_info = _points_swap_symbol_info()
    mt5._mt5 = SimpleNamespace(
        symbol_info=lambda _symbol: symbol_info,
        history_deals_get=history_deals_get,
    )
    engine = ExecutionEngine(mt5, _config(runtime_overrides={
        "selected_cell_swap_model_required": False,
        "selected_cell_swap_cost_model_required": False,
        "selected_cell_slippage_model_required": False,
        "selected_cell_default_expected_slippage_r": 0.0,
    }))
    packet, _reason = engine._vnext_pretrade_cost_model(
        trade_params=_trade_params(entry_price=1000.0, stop_loss=990.0),
        tick=SimpleNamespace(bid=1000.0, ask=1000.0),
        entry_price=1000.0,
        sl_distance=10.0,
        risk_pct=0.25,
    )

    assert len(calls) == 1
    assert packet["commission_cost"]["artifact"] == "account_history_deals"
    assert packet["commission_cost"]["usd_per_lot_round_turn"] == pytest.approx(10.0)
    assert packet["commission_cost"]["account_deal_commission"]["n_round_turns"] == 1


def test_required_swap_cost_conversion_fails_closed_when_mode_missing():
    packet = build_pretrade_cost_packet(
        config=_config(runtime_overrides={"selected_cell_swap_cost_model_required": True}),
        trade_params=_trade_params(gtos_vnext_dynamic_time_stop_bars=96),
        tick=SimpleNamespace(bid=4459.5, ask=4460.0, spread_cents=50.0),
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        entry_price=4460.0,
        stop_loss=4450.0,
        sl_distance=10.0,
        risk_pct=0.25,
    )

    assert packet["swap"]["source_status"] == "captured"
    assert packet["swap_cost"]["source_status"] == "source_gap"
    assert "swap_mode" in packet["swap_cost"]["missing_fields"]
    assert packet["status"] == "REFUSED"
    assert "missing_side_aware_swap_cost_r_conversion:swap_mode" in packet["refusal_reasons"]


def test_interest_mode_swap_drag_converts_from_entry_price():
    symbol_info = SimpleNamespace(
        point=0.01,
        trade_tick_size=0.01,
        trade_tick_value=0.01,
        trade_contract_size=1.0,
        volume_min=0.01,
        volume_max=40.0,
        volume_step=0.01,
        trade_stops_level=1,
        trade_freeze_level=0,
        spread=2934,
        trade_mode=4,
        filling_mode=3,
        swap_long=-30.0,
        swap_short=-30.0,
        swap_mode=5,
        swap_rollover3days=3,
    )

    packet = build_pretrade_cost_packet(
        config=_config(runtime_overrides={"selected_cell_swap_cost_model_required": True}),
        trade_params=_trade_params(
            direction="SHORT",
            entry_price=60000.0,
            stop_loss=60500.0,
            gtos_vnext_dynamic_time_stop_bars=96,
        ),
        tick=SimpleNamespace(bid=59990.0, ask=60000.0, spread_cents=1000.0),
        symbol="BTCUSD",
        broker_symbol="BTCUSD",
        entry_price=60000.0,
        stop_loss=60500.0,
        sl_distance=500.0,
        risk_pct=0.25,
        symbol_info=symbol_info,
    )

    assert packet["swap_cost"]["source_status"] == "captured"
    assert packet["swap_cost"]["swap_mode_interpretation"] == "annual_interest_current_or_open_price"
    assert packet["swap_cost"]["daily_price_drag"] == pytest.approx(50.0)
    assert packet["swap_cost"]["daily_cost_r"] == pytest.approx(0.1)
    assert packet["swap_cost"]["cost_r"] == pytest.approx(0.1)


def test_swap_cost_horizon_cap_limits_long_time_stop_gate_drag():
    symbol_info = SimpleNamespace(
        point=0.01,
        trade_tick_size=0.01,
        trade_tick_value=1.0,
        trade_contract_size=100.0,
        volume_min=0.01,
        volume_max=50.0,
        volume_step=0.01,
        trade_stops_level=0,
        trade_freeze_level=0,
        spread=53,
        trade_mode=4,
        filling_mode=3,
        swap_long=-100.0,
        swap_short=-100.0,
        swap_mode=1,
        swap_rollover3days=3,
    )

    packet = build_pretrade_cost_packet(
        config=_config(runtime_overrides={"selected_cell_swap_cost_horizon_days_cap": 0.25}),
        trade_params=_trade_params(gtos_vnext_dynamic_time_stop_bars=96),
        tick=SimpleNamespace(bid=4459.5, ask=4460.0, spread_cents=50.0),
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        entry_price=4460.0,
        stop_loss=4450.0,
        sl_distance=10.0,
        risk_pct=0.25,
        symbol_info=symbol_info,
    )

    assert packet["swap_cost"]["uncapped_estimated_holding_days"] == pytest.approx(1.0)
    assert packet["swap_cost"]["estimated_holding_days"] == pytest.approx(0.25)
    assert packet["swap_cost"]["horizon_capped"] is True
    assert packet["swap_cost"]["cost_r"] == pytest.approx(0.025)


def test_pretrade_packet_can_require_explicit_session_table_separately_from_trade_mode():
    packet = build_pretrade_cost_packet(
        config=_config(runtime_overrides={"selected_cell_explicit_session_table_required": True}),
        trade_params=_trade_params(),
        tick=SimpleNamespace(bid=4459.5, ask=4460.0, spread_cents=50.0),
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        entry_price=4460.0,
        stop_loss=4450.0,
        sl_distance=10.0,
        risk_pct=0.25,
    )

    assert packet["broker_hours"]["source_status"] == "captured"
    assert packet["broker_hours"]["trade_mode_allows_deal"] is True
    assert packet["explicit_session_table"]["source_status"] == "source_gap"
    assert packet["status"] == "REFUSED"
    assert "missing_explicit_broker_trading_session_table" in packet["refusal_reasons"]


def test_pretrade_packet_accepts_explicit_session_table_when_required_and_present():
    cfg = _config(runtime_overrides={"selected_cell_explicit_session_table_required": True})
    cfg["market"]["trade_sessions"] = [{"day": "monday", "from": "00:00", "to": "23:59"}]

    packet = build_pretrade_cost_packet(
        config=cfg,
        trade_params=_trade_params(),
        tick=SimpleNamespace(bid=4459.5, ask=4460.0, spread_cents=50.0),
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        entry_price=4460.0,
        stop_loss=4450.0,
        sl_distance=10.0,
        risk_pct=0.25,
    )

    assert packet["explicit_session_table"]["source_status"] == "captured"
    assert packet["explicit_session_table"]["capture_count"] == 1
    assert packet["explicit_session_table"]["captures"][0]["field"] == "trade_sessions"
    assert packet["status"] == "PASSED"
    assert pretrade_cost_refusal_reason(packet) is None


def _wide_spread_args(runtime_overrides=None, sleeve="fx_jpy"):
    # bid/ask spread 2.2 over a 10.0 sl_distance -> spread_r 0.22 (> global 0.10), total 0.24 (> global 0.15)
    return dict(
        config=_config(runtime_overrides=runtime_overrides),
        trade_params=_trade_params(gtos_vnext_source_event_details={"book": "W7", "sleeve": sleeve}),
        tick=SimpleNamespace(bid=4457.8, ask=4460.0, spread_cents=220.0),
        symbol="XAUUSD", broker_symbol="XAUUSD",
        entry_price=4460.0, stop_loss=4450.0, sl_distance=10.0, risk_pct=0.25,
    )


def test_wide_jpy_cross_spread_refused_without_override():
    """Baseline: a JPY-cross-like spread_r 0.22 trips BOTH the spread gate (0.10) and the total-cost
    gate (0.15) under the global ceilings -> REFUSED. (This is exactly the GBPJPY fx_jpy live case.)"""
    packet = build_pretrade_cost_packet(**_wide_spread_args())
    assert packet["spread_r"] == pytest.approx(0.22)
    assert packet["total_cost_r"] == pytest.approx(0.2471317184)
    assert packet["status"] == "REFUSED"
    reasons = " ".join(packet["refusal_reasons"])
    assert "spread_r_exceeds_selected_cell_limit" in reasons
    assert "total_cost_r_exceeds_limit" in reasons


def test_pretrade_cost_gate_tolerates_exact_limit_float_noise():
    packet = build_pretrade_cost_packet(
        config=_config(),
        trade_params=_trade_params(),
        tick=SimpleNamespace(bid=4459.0, ask=4460.000000000002, spread_cents=100.0),
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        entry_price=4460.0,
        stop_loss=4450.0,
        sl_distance=10.0,
        risk_pct=0.25,
    )

    assert packet["spread_r"] == pytest.approx(0.10)
    assert packet["status"] == "PASSED"
    assert not any(
        reason.startswith("spread_r_exceeds_selected_cell_limit")
        for reason in packet["refusal_reasons"]
    )


def test_fx_jpy_sleeve_override_passes_wide_spread():
    """OWNER-APPROVED JPY-cross trial: the per-sleeve override raises fx_jpy's ceilings (0.35 spread /
    0.45 total) so the same spread_r 0.22 PASSES, while every gate stays evidence-bound."""
    packet = build_pretrade_cost_packet(**_wide_spread_args(runtime_overrides={
        "selected_cell_pretrade_max_spread_r_by_sleeve": {"fx_jpy": 0.35, "fx_jpy_ny": 0.35},
        "selected_cell_pretrade_max_total_cost_r_by_sleeve": {"fx_jpy": 0.45, "fx_jpy_ny": 0.45},
    }))
    assert packet["max_spread_r"] == pytest.approx(0.35)
    assert packet["max_total_cost_r"] == pytest.approx(0.45)
    assert packet["spread_r"] == pytest.approx(0.22)
    assert packet["status"] == "PASSED"
    assert pretrade_cost_refusal_reason(packet) is None


def test_sleeve_override_is_scoped_other_sleeves_still_refused():
    """The override is per-sleeve: a NON-fx_jpy sleeve (crypto) with the same wide spread keeps the strict
    0.10/0.15 ceilings and is still REFUSED, even with the fx_jpy override present in config."""
    packet = build_pretrade_cost_packet(**_wide_spread_args(sleeve="crypto", runtime_overrides={
        "selected_cell_pretrade_max_spread_r_by_sleeve": {"fx_jpy": 0.35},
        "selected_cell_pretrade_max_total_cost_r_by_sleeve": {"fx_jpy": 0.45},
    }))
    assert packet["max_spread_r"] == pytest.approx(0.10)   # crypto NOT in the override map
    assert packet["status"] == "REFUSED"
    assert "spread_r_exceeds_selected_cell_limit" in " ".join(packet["refusal_reasons"])


def test_old_zero_commission_behavior_requires_the_explicit_named_comparator():
    args = _wide_spread_args(runtime_overrides={
        "selected_cell_pretrade_max_spread_r": 0.25,
        "selected_cell_pretrade_max_total_cost_r": 0.245,
    })
    truth = build_pretrade_cost_packet(**args)
    comparator = build_pretrade_cost_packet(
        **args,
        commission_mode=LEGACY_ZERO_COMMISSION_COMPARATOR_MODE,
    )

    assert truth["status"] == "REFUSED"
    assert truth["commission_r"] == pytest.approx(0.0071317184)
    assert truth["commission_cost"]["included_in_total_cost_r"] is True
    assert comparator["status"] == "PASSED"
    assert comparator["commission_mode"] == LEGACY_ZERO_COMMISSION_COMPARATOR_MODE
    assert comparator["commission_cost"]["comparator_only"] is True
    assert comparator["commission_cost"]["included_in_total_cost_r"] is False
    assert comparator["commission_r"] is None
    assert comparator["cost_excludes"] == ["commission"]
    assert comparator["total_cost_r"] == pytest.approx(0.24)


def test_broker_true_commission_gap_refuses_instead_of_becoming_zero():
    cfg = _config(namespace="unregistered_namespace")
    cfg["broker_profile"]["server"] = "Unregistered-Live"
    packet = build_pretrade_cost_packet(
        config=cfg,
        trade_params=_trade_params(),
        tick=SimpleNamespace(bid=4459.5, ask=4460.0, spread_cents=50.0),
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        entry_price=4460.0,
        stop_loss=4450.0,
        sl_distance=10.0,
        risk_pct=0.25,
    )

    assert packet["commission_cost"]["source_status"] == "source_gap"
    assert packet["commission_r"] is None
    assert packet["total_cost_r"] is None
    assert packet["status"] == "REFUSED"
    assert any(
        reason.startswith("missing_broker_true_commission_cost_r_conversion")
        for reason in packet["refusal_reasons"]
    )


def _gbpusd_round_turn_deals():
    """Login 11, position 19. Entry and exit both charged.

    The third row is position 11, an entry with no closing deal, so it must not count.
    """
    entry = {
        "symbol": "GBPUSD",
        "type": 0,
        "entry": 0,
        "volume": 2.83,
        "price": 1.33651,
        "commission": -7.08,
        "position_id": 19,
    }
    return [
        entry,
        {**entry, "entry": 1, "type": 1, "price": 1.33589},
        {**entry, "position_id": 11},
    ]


def test_demo_server_prices_gbpusd_from_closed_round_turns_and_ignores_entry_only():
    cfg = _config(namespace="friend_a_f5_minimal", runtime_overrides={
        "selected_cell_swap_model_required": False,
        "selected_cell_swap_cost_model_required": False,
        "selected_cell_slippage_model_required": False,
        "selected_cell_default_expected_slippage_r": 0.0,
    })
    cfg["broker_profile"]["server"] = "FTMO-Demo"
    cfg["market"].update({
        "symbol": "GBPUSD",
        "mt5_symbol": "GBPUSD",
        "point": 0.00001,
        "trade_tick_size": 0.00001,
        "trade_tick_value": 1.0,
        "trade_contract_size": 100000.0,
        "swap_long": 0.0,
        "swap_short": 0.0,
    })
    entry_fill = 1.33651
    exit_fill = 1.33589
    distance = abs(entry_fill - exit_fill)
    packet = build_pretrade_cost_packet(
        config=cfg,
        trade_params=_trade_params(entry_price=entry_fill, stop_loss=exit_fill),
        tick=SimpleNamespace(bid=entry_fill, ask=entry_fill),
        symbol="GBPUSD",
        broker_symbol="GBPUSD",
        entry_price=entry_fill,
        stop_loss=exit_fill,
        sl_distance=distance,
        risk_pct=0.25,
        commission_deals=_gbpusd_round_turn_deals(),
    )
    per_lot = 14.16 / 2.83
    assert packet["commission_cost"]["usd_per_lot_round_turn"] == pytest.approx(per_lot)
    assert packet["commission_cost"]["artifact"] == "account_history_deals"
    assert packet["commission_cost"]["account_deal_commission"]["n_round_turns"] == 1
    assert packet["commission_cost"]["account_deal_commission"]["charge_side"] == "both_sides"
    assert packet["commission_r"] == pytest.approx(per_lot / (distance * (1.0 / 0.00001)))
    assert not any(
        reason.startswith("missing_broker_true_commission_cost_r_conversion")
        for reason in packet["refusal_reasons"]
    )
    assert pretrade_cost_refusal_reason(packet) is None


def _xauusd_round_turns():
    """Two closed turns, positions 11 and 19. Prices differ, so notional bp is the tighter fit."""
    turns = (
        (11, 0.24, 4401.15, -0.74),
        (19, 0.15, 4331.72, -0.45),
    )
    deals = []
    for position_id, volume, price, commission in turns:
        deals.append({
            "symbol": "XAUUSD", "type": 0, "entry": 0, "volume": volume,
            "price": price, "commission": commission, "position_id": position_id,
        })
        deals.append({
            "symbol": "XAUUSD", "type": 1, "entry": 1, "volume": volume,
            "price": price, "commission": commission, "position_id": position_id,
        })
    return deals


def test_demo_server_prices_xauusd_from_closed_round_turns():
    cfg = _config(namespace="ftmo_redacted_account_f5_minimal", runtime_overrides={
        "selected_cell_swap_model_required": False,
        "selected_cell_swap_cost_model_required": False,
        "selected_cell_slippage_model_required": False,
        "selected_cell_default_expected_slippage_r": 0.0,
    })
    cfg["broker_profile"]["server"] = "FTMO-Demo"
    cfg["market"]["swap_long"] = 0.0
    cfg["market"]["swap_short"] = 0.0
    entry_fill = 4401.15
    exit_fill = 4407.07
    packet = build_pretrade_cost_packet(
        config=cfg,
        trade_params=_trade_params(entry_price=entry_fill, stop_loss=exit_fill),
        tick=SimpleNamespace(bid=entry_fill, ask=entry_fill),
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        entry_price=entry_fill,
        stop_loss=exit_fill,
        sl_distance=abs(entry_fill - exit_fill),
        risk_pct=0.25,
        commission_deals=_xauusd_round_turns(),
    )
    fitted = packet["commission_cost"]["account_deal_commission"]
    assert fitted["kind"] == "notional_bp"
    assert fitted["n_round_turns"] == 2
    assert packet["commission_r"] is not None
    assert packet["commission_r"] > 0
    assert not any(
        reason.startswith("missing_broker_true_commission_cost_r_conversion")
        for reason in packet["refusal_reasons"]
    )
    assert pretrade_cost_refusal_reason(packet) is None


def test_symbol_with_no_closed_round_turn_stays_unset():
    cfg = _config(namespace="friend_a_f5_minimal")
    cfg["broker_profile"]["server"] = "FTMO-Demo"
    entry_fill = 4401.15
    exit_fill = 4407.07
    packet = build_pretrade_cost_packet(
        config=cfg,
        trade_params=_trade_params(entry_price=entry_fill, stop_loss=exit_fill),
        tick=SimpleNamespace(bid=entry_fill, ask=entry_fill),
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        entry_price=entry_fill,
        stop_loss=exit_fill,
        sl_distance=abs(entry_fill - exit_fill),
        risk_pct=0.25,
        commission_deals=_gbpusd_round_turn_deals(),
    )
    assert packet["commission_r"] is None
    assert packet["commission_cost"]["account_deal_commission"]["status"] == "no_closed_round_turn"
    assert any(
        reason.startswith("missing_broker_true_commission_cost_r_conversion")
        for reason in packet["refusal_reasons"]
    )


def test_pretrade_packet_refuses_missing_profile_when_required():
    cfg = _config(namespace="")
    packet = build_pretrade_cost_packet(
        config=cfg,
        trade_params=_trade_params(),
        tick=SimpleNamespace(bid=4459.5, ask=4460.0, spread_cents=50.0),
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        entry_price=4460.0,
        stop_loss=4450.0,
        sl_distance=10.0,
        risk_pct=0.25,
    )

    assert packet["status"] == "REFUSED"
    assert "missing_broker_account_profile_namespace" in packet["refusal_reasons"]


def test_permissions_gate_refuses_vnext_broker_net_cost_before_gate1():
    mt5 = MockMT5()
    mt5.connect()
    mt5.set_tick(4458.0, 4460.0)
    pa = SimpleNamespace(
        reasoning=SimpleNamespace(
            setup_grade="A+",
            daily_bias=SimpleNamespace(direction="bullish"),
        ),
        trade_parameters=SimpleNamespace(**_trade_params()),
    )
    mso = SimpleNamespace(timeframes={"M15": SimpleNamespace(atr_14=0.0)})

    denial = check_permissions(
        pa,
        mso,
        {"daily_pnl_pct": 0},
        mt5,
        config=_config(runtime_overrides={"selected_cell_pretrade_max_spread_r": 0.05}),
        symbol="XAUUSD",
    )

    assert denial is not None
    assert denial.reason == "vnext_broker_net_pretrade_cost_refused"
    assert "spread_r_exceeds_selected_cell_limit" in denial.details["refusal_reason"]


def _selector_event(packet):
    return {
        "symbol": "XAUUSD",
        "side": "LONG",
        "framework": "fvg_fill",
        "candidate_origin_family": "origin_current_fvg_fill",
        "route_session": "london",
        "session_bucket": "london",
        "branch_label": "FOLLOW",
        "broker_native_eligible": True,
        "runtime_instrument_configured": True,
        "selected_cell_risk_required": True,
        "selected_cell_risk_allowed": True,
        "selected_cell_risk_pct": 0.25,
        "source_path_feature_status": "raw_data_m15_asof_complete",
        "source_mode": "LIVE_RAW_M15",
        "source_window_complete": True,
        "ordered_path_status": "ordered_path_not_ambiguous_in_live_closed_m15_generation",
        "selected_policy_ordered_path_status": "ordered_path_not_ambiguous_in_live_closed_m15_generation",
        "kill_zone_position": "in_london_runtime_configured_kill_zone",
        "gtos_vnext_pretrade_cost_model": packet,
        "broker_net_cost_selector_apply_to_execution": True,
    }


def test_selector_router_consumes_broker_net_packet_before_candidate_permission():
    packet = build_pretrade_cost_packet(
        config=_config(),
        trade_params=_trade_params(),
        tick=SimpleNamespace(bid=4459.5, ask=4460.0, spread_cents=50.0),
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        entry_price=4460.0,
        stop_loss=4450.0,
        sl_distance=10.0,
        risk_pct=0.25,
    )

    decision = route_moonshot_dynamic_execution(
        _selector_event(packet),
        enabled=True,
        apply_to_execution=True,
    )

    assert decision.candidate_use_allowed_now is True
    cost = decision.route_dimensions["broker_net_cost_selector"]
    assert cost["classification"] == "tradeable_now"
    assert packet["authority"] == "broker_calibrated_replay_cost"
    assert packet["cost_source_gap_status"] == "source_bound_cost_authority_present"
    assert packet["candidate_cost_r_fallback_is_authority"] is False
    assert packet["source_gap_cost_fallback_blocked"] is False
    assert cost["runtime_effect_boundary"] == "selector_consumes_existing_packet_no_broker_io"


def test_selector_router_refuses_proxy_cost_authority_even_when_numeric_cost_passes():
    packet = build_pretrade_cost_packet(
        config=_config(),
        trade_params=_trade_params(),
        tick=SimpleNamespace(bid=4459.5, ask=4460.0, spread_cents=50.0),
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        entry_price=4460.0,
        stop_loss=4450.0,
        sl_distance=10.0,
        risk_pct=0.25,
    )
    packet["authority"] = "timewarp_candidate_cost_proxy"
    packet["cost_authority"] = "timewarp_candidate_cost_proxy"
    packet["candidate_cost_r_fallback_is_authority"] = True

    decision = route_moonshot_dynamic_execution(
        _selector_event(packet),
        enabled=True,
        apply_to_execution=True,
    )

    assert decision.candidate_use_allowed_now is False
    cost = decision.route_dimensions["broker_net_cost_selector"]
    assert cost["classification"] == "source_capture_required"
    assert cost["refusal_reason"] == (
        "broker_net_cost_authority_not_executable:timewarp_candidate_cost_proxy"
    )


def test_selector_router_refuses_broker_net_packet_source_or_cost_failure():
    packet = build_pretrade_cost_packet(
        config=_config(runtime_overrides={"selected_cell_pretrade_max_total_cost_r": 0.04}),
        trade_params=_trade_params(),
        tick=SimpleNamespace(bid=4459.5, ask=4460.0, spread_cents=50.0),
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        entry_price=4460.0,
        stop_loss=4450.0,
        sl_distance=10.0,
        risk_pct=0.25,
    )

    decision = route_moonshot_dynamic_execution(
        _selector_event(packet),
        enabled=True,
        apply_to_execution=True,
    )

    assert decision.candidate_use_allowed_now is False
    assert any(
        reason.startswith("broker_net_pretrade_packet_refused:")
        for reason in decision.refusal_reasons
    )
    assert decision.route_dimensions["broker_net_cost_selector"]["classification"] == "no_trade_by_evidence"
