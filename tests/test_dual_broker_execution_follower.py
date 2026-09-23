from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import scripts.dual_broker_execution_follower as follower_mod
import src.components.execution as exec_mod
from scripts.dual_broker_execution_follower import (
    DEFAULT_CONFIG_PATH,
    DEFAULT_PROFILE,
    FollowerRuntime,
    _processed_intent_ids_from_action_log,
    build_symbol_map,
    dual_broker_architecture_contract,
    execution_engine_none_reason,
    load_target_base_config,
    load_target_symbol_config,
    read_intents_with_offsets,
    target_execution_context_errors,
    target_risk_cap_pct,
)
from src.components.execution import ExecutionEngine, TradeState
from src.utils.broker_profile import resolve_mt5_portable_mode
from src.components.dual_broker_intent_bus import (
    MARKET_ENTRY,
    build_intent_from_execution_inputs,
)
from src.mt5.mt5_interface import MAGIC_NUMBER, PositionInfo
from src.mt5.mt5_mock import MockMT5

EXPECTED_LIVE_SYMBOLS = {
    "AUDJPY",
    "AUDUSD",
    "BTCUSD",
    "CHFJPY",
    "ETHUSD",
    "EURGBP",
    "EURJPY",
    "EURUSD",
    "GBPJPY",
    "GBPUSD",
    "GER40",
    "JP225",
    "NAS100",
    "NZDUSD",
    "SPX500",
    "UK100",
    "UKOIL_cash",
    "US30_cash",
    "USDCAD",
    "USDCHF",
    "USDJPY",
    "USOIL_cash",
    "XAGUSD",
    "XAUUSD",
}


def _base_config() -> dict:
    return {
        "risk": {"risk_per_trade_pct": 2.0, "max_concurrent": 2},
        "gtos_vnext_runtime": {
            "prop_safe_selector_initial_balance": 100000.0,
            "prop_safe_selector_external_daily_loss_limit_pct": 5.0,
            "prop_safe_selector_external_overall_max_loss_pct": 10.0,
            "prop_safe_selector_apply_internal_daily_overlay": True,
            "prop_safe_selector_internal_daily_loss_limit_pct": 4.0,
            "prop_safe_selector_min_reduced_risk_pct": 0.1,
            "prop_safe_selector_default_spread_slippage_commission_buffer_pct": 0.0,
        },
        "ftmo_rules": {
            "account_balance_initial_inferred_usd": 100000.0,
            "maximum_daily_loss_pct": 5.0,
            "maximum_loss_pct": 10.0,
            "daily_reset_time": "00:00 CE(S)T",
        },
        "market": {"symbol": "XAUUSD", "mt5_symbol": "XAUUSD"},
        "instruments": {
            "XAUUSD": {
                "market": {
                    "symbol": "XAUUSD",
                    "mt5_symbol": "XAUUSD",
                    "tick_size": 0.01,
                    "point": 0.01,
                    "digits": 2,
                    "trade_tick_size": 0.01,
                    "trade_tick_value": 1.0,
                    "contract_size": 100.0,
                    "volume_min": 0.01,
                    "volume_max": 100.0,
                    "volume_step": 0.01,
                    "trade_stops_level": 0,
                    "trade_freeze_level": 0,
                },
                "risk": {"risk_per_trade_pct": 1.0, "max_concurrent": 2},
            },
            "EURUSD": {
                "market": {
                    "symbol": "EURUSD",
                    "mt5_symbol": "EURUSD",
                    "tick_size": 0.00001,
                    "point": 0.00001,
                    "digits": 5,
                    "trade_tick_size": 0.00001,
                    "trade_tick_value": 1.0,
                    "contract_size": 100000.0,
                    "volume_min": 0.01,
                    "volume_max": 100.0,
                    "volume_step": 0.01,
                    "trade_stops_level": 0,
                    "trade_freeze_level": 0,
                },
                "risk": {"risk_per_trade_pct": 1.0, "max_concurrent": 2},
            },
            "GBPUSD": {
                "market": {
                    "symbol": "GBPUSD",
                    "mt5_symbol": "GBPUSD",
                    "tick_size": 0.00001,
                    "point": 0.00001,
                    "digits": 5,
                    "trade_tick_size": 0.00001,
                    "trade_tick_value": 1.0,
                    "contract_size": 100000.0,
                    "volume_min": 0.01,
                    "volume_max": 100.0,
                    "volume_step": 0.01,
                    "trade_stops_level": 0,
                    "trade_freeze_level": 0,
                },
                "risk": {"risk_per_trade_pct": 1.0, "max_concurrent": 2},
            }
        },
    }


def _intent() -> dict:
    return build_intent_from_execution_inputs(
        intent_type=MARKET_ENTRY,
        source_profile="redacted_account",
        source_runtime_namespace="redacted_account_live_bee34003",
        source_symbol="XAUUSD",
        source_mt5_symbol="XAUUSD",
        trade_params={
            "direction": "LONG",
            "entry_price": 2350.0,
            "stop_loss": 2340.0,
            "take_profit_1": 2370.0,
            "risk_reward_ratio": 2.0,
        },
        source_trade_id="tr_primary",
        effective_risk_pct=0.5,
        trigger="unit_test",
    )


def _attach_order_calc_profit(mt5: MockMT5) -> None:
    geometry = {
        "EURUSD": (0.00001, 1.0),
        "GBPUSD": (0.00001, 1.0),
        "XAUUSD": (0.01, 1.0),
    }

    def order_calc_profit(
        order_type: int,
        symbol: str,
        volume: float,
        price_open: float,
        target_price: float,
    ) -> float:
        tick_size, tick_value = geometry.get(symbol, (0.01, 1.0))
        price_delta = (
            target_price - price_open
            if int(order_type) == 0
            else price_open - target_price
        )
        return (price_delta / tick_size) * tick_value * volume

    mt5._mt5 = SimpleNamespace(order_calc_profit=order_calc_profit)


def _redirect_execution_checkpoint(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        exec_mod,
        "CHECKPOINT_PATH",
        str(tmp_path / "meta" / "execution_checkpoint.json"),
    )


def test_write_json_retries_transient_windows_file_lock(tmp_path: Path, monkeypatch):
    path = tmp_path / "state.json"
    calls = []
    real_replace = follower_mod.os.replace

    def flaky_replace(src: str, dst: str) -> None:
        calls.append((src, dst))
        if len(calls) == 1:
            raise PermissionError(5, "Access is denied", src)
        real_replace(src, dst)

    monkeypatch.setattr(follower_mod.os, "replace", flaky_replace)
    monkeypatch.setattr(follower_mod.time, "sleep", lambda _seconds: None)

    follower_mod._write_json(path, {"ok": True})

    assert json.loads(path.read_text(encoding="utf-8")) == {"ok": True}
    assert len(calls) == 2


def test_write_json_file_lock_failure_does_not_clobber_previous_state(
    tmp_path: Path,
    monkeypatch,
):
    path = tmp_path / "state.json"
    path.write_text('{"previous": true}', encoding="utf-8")

    def locked_replace(src: str, _dst: str) -> None:
        raise PermissionError(5, "Access is denied", src)

    monkeypatch.setattr(follower_mod.os, "replace", locked_replace)
    monkeypatch.setattr(follower_mod.time, "sleep", lambda _seconds: None)

    follower_mod._write_json(path, {"next": True})

    assert json.loads(path.read_text(encoding="utf-8")) == {"previous": True}
    tmp = path.with_suffix(f".{follower_mod.os.getpid()}.tmp")
    assert json.loads(tmp.read_text(encoding="utf-8")) == {"next": True}


def test_target_risk_cap_uses_lower_of_source_and_target():
    assert target_risk_cap_pct(_intent(), _base_config()) == 0.5


def test_target_risk_cap_requires_source_intent_risk_cap():
    intent = _intent()
    intent["risk"].pop("effective_risk_pct_cap")

    assert target_risk_cap_pct(intent, _base_config()) is None


def test_ftmo_follower_profile_covers_live_symbols_and_broker_geometry():
    cfg = load_target_base_config(Path(DEFAULT_CONFIG_PATH), DEFAULT_PROFILE)
    symbol_map = build_symbol_map(cfg)

    assert set(symbol_map) == EXPECTED_LIVE_SYMBOLS
    assert len(symbol_map) == 24
    assert (cfg.get("runtime") or {}).get("broker_account_namespace") == "operator_profile"
    assert (cfg.get("mt5") or {}).get("terminal_path") == r"C:\MT5\FTMO\terminal64.exe"
    assert resolve_mt5_portable_mode(cfg) is True
    assert symbol_map["NAS100"] == "US100.cash"
    assert symbol_map["US30_cash"] == "US30.cash"
    assert symbol_map["UKOIL_cash"] == "UKOIL.cash"
    assert symbol_map["USOIL_cash"] == "USOIL.cash"
    risk_cfg = cfg.get("risk") or {}
    assert risk_cfg.get("max_concurrent") in (None, 0, "disabled")
    assert "aggregate_drawdown_budget" in str(risk_cfg.get("risk_policy_source") or "")
    runtime_cfg = cfg.get("gtos_vnext_runtime") or {}
    assert runtime_cfg.get("prop_safe_selector_daily_reset_timezone") == "Europe/Prague"
    contract = dual_broker_architecture_contract(
        cfg,
        target_namespace="operator_profile",
        source_namespace="redacted_account_live_bee34003",
        order_enabled=True,
    )
    assert contract["status"] == "passed"
    assert contract["role"] == "follower_projector_only"
    assert contract["target_authority"]["full_run_agent_fleet"] == "forbidden"
    assert contract["target_authority"]["broker_local_risk_gate"] == "required"
    assert contract["target_authority"]["broker_local_lifecycle_management"] == "required"

    required_market_fields = {
        "mt5_symbol",
        "tick_size",
        "point",
        "digits",
        "trade_tick_size",
        "trade_tick_value",
        "volume_min",
        "volume_max",
        "volume_step",
        "trade_mode",
    }
    for symbol in EXPECTED_LIVE_SYMBOLS:
        symbol_cfg = load_target_symbol_config(cfg, symbol)
        market = symbol_cfg.get("market") or {}
        missing = [key for key in required_market_fields if market.get(key) in (None, "")]
        assert missing == []
        risk = symbol_cfg.get("risk") or {}
        assert float(risk.get("risk_per_trade_pct", cfg["risk"]["risk_per_trade_pct"])) > 0


def test_dual_broker_architecture_contract_blocks_wrong_target_role():
    cfg = {
        "dual_broker": {
            "architecture_id": "unit",
            "runtime_model": "redacted_account_primary_full_ftmo_follower_projector",
            "role": "primary_full_runtime",
            "source_runtime_namespace": "redacted_account_live_bee34003",
            "target_runtime_namespace": "operator_profile",
            "intent_bus_enabled": True,
            "target_authority": {
                "order_source": "canonical_trade_intents_only",
                "broker_local_risk_gate": "required",
                "broker_local_lifecycle_management": "required",
                "broker_local_crash_recovery": "required",
                "full_run_agent_fleet": "forbidden",
                "primary_lot_copy": "forbidden",
                "primary_fill_price_copy": "forbidden",
                "primary_cash_pnl_copy": "forbidden",
                "primary_cost_swap_fee_copy": "forbidden",
                "primary_symbol_spec_session_copy": "forbidden",
                "primary_order_deal_position_lifecycle_copy": "forbidden",
            },
        }
    }

    contract = dual_broker_architecture_contract(
        cfg,
        target_namespace="operator_profile",
        source_namespace="redacted_account_live_bee34003",
        order_enabled=True,
    )

    assert contract["status"] == "failed"
    assert contract["errors"] == [
        "dual_broker.role_not_follower_projector_only:primary_full_runtime"
    ]


def test_dry_run_follower_consumes_intent_without_order_send(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("GTOS_RUNTIME_NAMESPACE", "operator_profile")
    mt5 = MockMT5()
    mt5.connect()
    _attach_order_calc_profit(mt5)
    mt5.set_tick(2350.10, 2350.20)
    action_log = tmp_path / "actions.jsonl"
    runtime = FollowerRuntime(
        mt5=mt5,
        base_config=_base_config(),
        target_namespace="operator_profile",
        source_namespace="redacted_account_live_bee34003",
        order_enabled=False,
        action_log=action_log,
        symbol_map={"XAUUSD": "XAUUSD"},
    )

    runtime.process_intent(_intent())

    rows = [json.loads(line) for line in action_log.read_text(encoding="utf-8").splitlines()]
    assert rows[-1]["event"] == "dry_run_intent_ready"
    assert rows[-1]["target_namespace"] == "operator_profile"
    assert mt5._order_log == []


def test_follower_rejects_unsanitized_source_broker_truth_payload(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setenv("GTOS_RUNTIME_NAMESPACE", "operator_profile")
    mt5 = MockMT5()
    mt5.connect()
    action_log = tmp_path / "actions.jsonl"
    runtime = FollowerRuntime(
        mt5=mt5,
        base_config=_base_config(),
        target_namespace="operator_profile",
        source_namespace="redacted_account_live_bee34003",
        order_enabled=True,
        action_log=action_log,
        symbol_map={"XAUUSD": "XAUUSD"},
    )
    intent = _intent()
    intent["primary_order"] = {
        "record_path": "knowledge_base/redacted_account_live_bee34003/trade_records/XAUUSD/record.json",
        "entry_order_ticket": 12345,
        "entry_deal_ticket": 12346,
        "entry_price": 2350.25,
        "initial_volume": 0.42,
    }

    consumed = runtime.process_intent(intent)

    rows = [json.loads(line) for line in action_log.read_text(encoding="utf-8").splitlines()]
    assert consumed is True
    assert rows[-1]["event"] == "intent_source_target_boundary_violation"
    assert rows[-1]["reason"] == "source_broker_truth_not_allowed_in_target_execution_payload"
    assert rows[-1]["boundary_violations"] == [
        "primary_order_forbidden_source_field:entry_deal_ticket",
        "primary_order_forbidden_source_field:entry_order_ticket",
        "primary_order_forbidden_source_field:entry_price",
        "primary_order_forbidden_source_field:initial_volume",
    ]
    assert mt5._order_log == []


def test_order_enabled_follower_defers_market_intent_when_target_tick_invalid(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setenv("GTOS_RUNTIME_NAMESPACE", "operator_profile")
    mt5 = MockMT5()
    mt5.connect()
    mt5.set_tick(0.0, 0.0)
    action_log = tmp_path / "actions.jsonl"
    runtime = FollowerRuntime(
        mt5=mt5,
        base_config=_base_config(),
        target_namespace="operator_profile",
        source_namespace="redacted_account_live_bee34003",
        order_enabled=True,
        action_log=action_log,
        symbol_map={"XAUUSD": "XAUUSD"},
    )

    consumed = runtime.process_intent(_intent())

    rows = [json.loads(line) for line in action_log.read_text(encoding="utf-8").splitlines()]
    assert consumed is False
    assert rows[-1]["event"] == "market_intent_deferred_target_tick_unavailable"
    assert rows[-1]["reason"] == "target_tick_nonpositive_bid_ask"
    assert runtime.processed_intent_ids == set()
    assert mt5._order_log == []


def test_order_enabled_follower_expires_old_market_intent_with_invalid_target_tick(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setenv("GTOS_RUNTIME_NAMESPACE", "operator_profile")
    mt5 = MockMT5()
    mt5.connect()
    mt5.set_tick(0.0, 0.0)
    action_log = tmp_path / "actions.jsonl"
    runtime = FollowerRuntime(
        mt5=mt5,
        base_config=_base_config(),
        target_namespace="operator_profile",
        source_namespace="redacted_account_live_bee34003",
        order_enabled=True,
        action_log=action_log,
        symbol_map={"XAUUSD": "XAUUSD"},
    )
    intent = _intent()
    intent["recorded_at_utc"] = (
        datetime.now(timezone.utc) - timedelta(minutes=10)
    ).isoformat()

    consumed = runtime.process_intent(intent)

    rows = [json.loads(line) for line in action_log.read_text(encoding="utf-8").splitlines()]
    assert consumed is True
    assert rows[-1]["event"] == "market_intent_expired_target_tick_unavailable"
    assert intent["intent_id"] in runtime.processed_intent_ids
    assert mt5._order_log == []


def test_order_enabled_follower_retries_market_intent_when_target_order_returns_none(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setenv("GTOS_RUNTIME_NAMESPACE", "operator_profile")
    monkeypatch.setattr(
        ExecutionEngine,
        "open_trade",
        lambda self, *args, **kwargs: None,
    )
    mt5 = MockMT5()
    mt5.connect()
    _attach_order_calc_profit(mt5)
    mt5.set_tick(2350.10, 2350.20)
    action_log = tmp_path / "actions.jsonl"
    runtime = FollowerRuntime(
        mt5=mt5,
        base_config=_base_config(),
        target_namespace="operator_profile",
        source_namespace="redacted_account_live_bee34003",
        order_enabled=True,
        action_log=action_log,
        symbol_map={"XAUUSD": "XAUUSD"},
    )
    intent = _intent()

    consumed = runtime.process_intent(intent)

    rows = [json.loads(line) for line in action_log.read_text(encoding="utf-8").splitlines()]
    assert consumed is False
    assert rows[-1]["event"] == "market_intent_deferred_no_target_order"
    assert rows[-1]["reason"] == "execution_engine_returned_none"
    failure_snapshot = rows[-1]["target_execution_failure_snapshot"]
    assert failure_snapshot["broker_symbol"] == "XAUUSD"
    assert "symbol_info" in failure_snapshot
    assert failure_snapshot["tick"]["available"] is True
    assert isinstance(failure_snapshot["positions"], list)
    assert intent["intent_id"] not in runtime.processed_intent_ids


def test_order_enabled_follower_logs_pretrade_refusal_when_target_order_returns_none(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setenv("GTOS_RUNTIME_NAMESPACE", "operator_profile")

    def _refusing_open_trade(self, params, *args, **kwargs):  # noqa: ANN001, ARG001
        params["gtos_vnext_pretrade_cost_model"] = {
            "status": "REFUSED",
            "refusal_reason": "spread_r_exceeds_selected_cell_limit:0.200000>0.100000",
            "spread_r": 0.2,
            "max_spread_r": 0.1,
        }
        return None

    monkeypatch.setattr(ExecutionEngine, "open_trade", _refusing_open_trade)
    mt5 = MockMT5()
    mt5.connect()
    _attach_order_calc_profit(mt5)
    mt5.set_tick(2350.10, 2350.20)
    action_log = tmp_path / "actions.jsonl"
    runtime = FollowerRuntime(
        mt5=mt5,
        base_config=_base_config(),
        target_namespace="operator_profile",
        source_namespace="redacted_account_live_bee34003",
        order_enabled=True,
        action_log=action_log,
        symbol_map={"XAUUSD": "XAUUSD"},
    )
    intent = _intent()

    consumed = runtime.process_intent(intent)

    rows = [json.loads(line) for line in action_log.read_text(encoding="utf-8").splitlines()]
    assert consumed is False
    assert rows[-1]["event"] == "market_intent_deferred_no_target_order"
    assert rows[-1]["reason"] == (
        "gtos_vnext_pretrade_cost_model_refused:"
        "spread_r_exceeds_selected_cell_limit:0.200000>0.100000"
    )
    assert rows[-1]["pretrade_cost_model_status"] == "REFUSED"
    assert rows[-1]["pretrade_cost_model"]["spread_r"] == 0.2


def test_execution_engine_none_reason_falls_back_without_cost_model():
    assert execution_engine_none_reason({}) == "execution_engine_returned_none"


def test_processed_intent_recovery_keeps_successes_and_reopens_recent_failures(
    tmp_path: Path,
):
    action_log = tmp_path / "actions.jsonl"
    rows = [
        {
            "event": "market_intent_processed",
            "intent_id": "copied",
            "result": {"ticket": 123},
        },
        {
            "event": "market_intent_expired_no_target_order",
            "intent_id": "failed",
        },
        {
            "event": "market_intent_processed",
            "intent_id": "failed",
            "result": None,
        },
        {
            "event": "risk_guard_rejected",
            "intent_id": "risk_blocked",
        },
    ]
    action_log.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n",
        encoding="utf-8",
    )

    normal = _processed_intent_ids_from_action_log(action_log)
    replay_failed = _processed_intent_ids_from_action_log(
        action_log,
        reprocess_failed_intents=True,
    )

    assert normal == {"copied", "failed", "risk_blocked"}
    assert replay_failed == {"copied", "risk_blocked"}


def test_action_log_intent_outcome_summary_separates_latest_statuses(
    tmp_path: Path,
):
    action_log = tmp_path / "actions.jsonl"
    rows = [
        {
            "event": "market_intent_processed",
            "intent_id": "copied",
            "result": {"ticket": 123},
        },
        {
            "event": "risk_guard_rejected",
            "intent_id": "risk_blocked",
        },
        {
            "event": "market_intent_processed",
            "intent_id": "failed",
            "result": None,
        },
        {
            "event": "market_intent_skipped_outside_live_recovery_window",
            "intent_id": "stale",
        },
        {
            "event": "market_intent_target_position_detected_before_retry",
            "intent_id": "detected",
        },
    ]
    action_log.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n",
        encoding="utf-8",
    )

    summary = follower_mod._action_log_intent_outcome_summary(action_log)

    assert summary["intent_count"] == 5
    assert summary["outcome_counts"] == {
        "copied": 1,
        "failed_retryable": 1,
        "risk_blocked": 1,
        "stale_skipped": 1,
        "target_position_detected": 1,
    }
    assert summary["latest_intents"]["copied"]["event"] == "market_intent_processed"


def test_reprocess_failed_reopens_repairable_failure_even_after_age_skip(
    tmp_path: Path,
):
    action_log = tmp_path / "actions.jsonl"
    rows = [
        {
            "event": "market_intent_missing_target_execution_context",
            "intent_id": "failed_then_skipped",
        },
        {
            "event": "market_intent_skipped_outside_live_recovery_window",
            "intent_id": "failed_then_skipped",
        },
        {
            "event": "market_intent_skipped_outside_live_recovery_window",
            "intent_id": "old_never_failed",
        },
    ]
    action_log.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n",
        encoding="utf-8",
    )

    processed, reprocessable = follower_mod._intent_recovery_state_from_action_log(
        action_log,
        reprocess_failed_intents=True,
    )

    assert "failed_then_skipped" not in processed
    assert "failed_then_skipped" in reprocessable
    assert "old_never_failed" in processed
    assert "old_never_failed" not in reprocessable


def test_follower_skips_stale_market_intent_in_live_recovery_window(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setenv("GTOS_RUNTIME_NAMESPACE", "operator_profile")
    mt5 = MockMT5()
    mt5.connect()
    action_log = tmp_path / "actions.jsonl"
    runtime = FollowerRuntime(
        mt5=mt5,
        base_config=_base_config(),
        target_namespace="operator_profile",
        source_namespace="redacted_account_live_bee34003",
        order_enabled=True,
        action_log=action_log,
        symbol_map={"XAUUSD": "XAUUSD"},
        max_live_recovery_intent_age_seconds=30.0,
    )
    intent = _intent()
    intent["recorded_at_utc"] = (
        datetime.now(timezone.utc) - timedelta(minutes=5)
    ).isoformat()

    consumed = runtime.process_intent(intent)

    rows = [json.loads(line) for line in action_log.read_text(encoding="utf-8").splitlines()]
    assert consumed is True
    assert rows[-1]["event"] == "market_intent_skipped_outside_live_recovery_window"
    assert mt5._order_log == []


def test_follower_reprocess_failed_recent_intent_before_live_recovery_skip(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setenv("GTOS_RUNTIME_NAMESPACE", "operator_profile")
    calls = {"open_trade": 0}

    def _successful_open_trade(self, *args, **kwargs):  # noqa: ANN001, ARG001
        calls["open_trade"] += 1
        trade = TradeState(
            ticket=70004,
            direction="LONG",
            entry_price=2350.0,
            stop_loss=2340.0,
            take_profit_1=2370.0,
            take_profit_2=0.0,
            take_profit_3=0.0,
            initial_volume=0.10,
            current_volume=0.10,
            sl_distance=10.0,
        )
        self.active_trade = trade
        return trade

    monkeypatch.setattr(ExecutionEngine, "open_trade", _successful_open_trade)
    mt5 = MockMT5()
    mt5.connect()
    mt5.set_tick(2350.10, 2350.20)
    action_log = tmp_path / "actions.jsonl"
    runtime = FollowerRuntime(
        mt5=mt5,
        base_config=_base_config(),
        target_namespace="operator_profile",
        source_namespace="redacted_account_live_bee34003",
        order_enabled=True,
        action_log=action_log,
        symbol_map={"XAUUSD": "XAUUSD"},
        max_live_recovery_intent_age_seconds=30.0,
    )
    intent = _intent()
    source_record = tmp_path / "source_trade_record.json"
    source_record.write_text(
        json.dumps(
            {
                "execution": {
                    "broker_fill_state": "filled",
                    "fill_time_utc": datetime.now(timezone.utc).isoformat(),
                    "ticket": 2420001,
                    "position_ticket": 2420001,
                    "entry_order_ticket": 2420001,
                    "current_volume": 0.10,
                }
            }
        ),
        encoding="utf-8",
    )
    intent["primary_order"] = {"record_path": str(source_record)}
    runtime.reprocessable_failed_intent_ids.add(intent["intent_id"])
    intent["recorded_at_utc"] = (
        datetime.now(timezone.utc) - timedelta(seconds=5)
    ).isoformat()

    consumed = runtime.process_intent(intent)

    rows = [json.loads(line) for line in action_log.read_text(encoding="utf-8").splitlines()]
    assert consumed is True
    assert calls["open_trade"] == 1
    assert rows[-2]["event"] == "market_intent_reprocess_failed_retry_started"
    assert rows[-2]["source_record_retry_state"] == {}
    assert rows[-1]["event"] == "market_intent_processed"
    assert intent["intent_id"] in runtime.processed_intent_ids
    assert intent["intent_id"] not in runtime.reprocessable_failed_intent_ids


def test_follower_reprocess_failed_stale_intent_does_not_open_late_source_still_open(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setenv("GTOS_RUNTIME_NAMESPACE", "operator_profile")
    calls = {"open_trade": 0}

    def _unexpected_open_trade(self, *args, **kwargs):  # noqa: ANN001, ARG001
        calls["open_trade"] += 1
        return None

    monkeypatch.setattr(ExecutionEngine, "open_trade", _unexpected_open_trade)
    mt5 = MockMT5()
    mt5.connect()
    mt5.set_tick(2350.10, 2350.20)
    action_log = tmp_path / "actions.jsonl"
    runtime = FollowerRuntime(
        mt5=mt5,
        base_config=_base_config(),
        target_namespace="operator_profile",
        source_namespace="redacted_account_live_bee34003",
        order_enabled=True,
        action_log=action_log,
        symbol_map={"XAUUSD": "XAUUSD"},
        max_live_recovery_intent_age_seconds=30.0,
    )
    source_record = tmp_path / "open_source_trade_record.json"
    source_record.write_text(
        json.dumps(
            {
                "execution": {
                    "broker_fill_state": "filled",
                    "fill_time_utc": datetime.now(timezone.utc).isoformat(),
                    "ticket": 2420004,
                    "position_ticket": 2420004,
                    "entry_order_ticket": 2420004,
                    "current_volume": 0.10,
                }
            }
        ),
        encoding="utf-8",
    )
    intent = _intent()
    intent["primary_order"] = {"record_path": str(source_record)}
    runtime.reprocessable_failed_intent_ids.add(intent["intent_id"])
    intent["recorded_at_utc"] = (
        datetime.now(timezone.utc) - timedelta(minutes=5)
    ).isoformat()

    consumed = runtime.process_intent(intent)

    rows = [json.loads(line) for line in action_log.read_text(encoding="utf-8").splitlines()]
    assert consumed is True
    assert calls["open_trade"] == 0
    assert rows[-1]["event"] == (
        "market_intent_reprocess_failed_retry_skipped_outside_live_recovery_window"
    )
    assert rows[-1]["reason"] == (
        "stale_market_entry_not_opened_late_even_with_unclosed_source_record"
    )
    assert rows[-1]["source_record_retry_state"]["allow_retry"] is True
    assert intent["intent_id"] in runtime.processed_intent_ids
    assert intent["intent_id"] not in runtime.reprocessable_failed_intent_ids


def test_follower_reprocess_failed_stale_intent_skips_closed_source_record(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setenv("GTOS_RUNTIME_NAMESPACE", "operator_profile")
    calls = {"open_trade": 0}

    def _unexpected_open_trade(self, *args, **kwargs):  # noqa: ANN001, ARG001
        calls["open_trade"] += 1
        return None

    monkeypatch.setattr(ExecutionEngine, "open_trade", _unexpected_open_trade)
    mt5 = MockMT5()
    mt5.connect()
    mt5.set_tick(2350.10, 2350.20)
    action_log = tmp_path / "actions.jsonl"
    runtime = FollowerRuntime(
        mt5=mt5,
        base_config=_base_config(),
        target_namespace="operator_profile",
        source_namespace="redacted_account_live_bee34003",
        order_enabled=True,
        action_log=action_log,
        symbol_map={"XAUUSD": "XAUUSD"},
        max_live_recovery_intent_age_seconds=30.0,
    )
    source_record = tmp_path / "closed_source_trade_record.json"
    source_record.write_text(
        json.dumps(
            {
                "execution": {
                    "broker_fill_state": "filled",
                    "fill_time_utc": datetime.now(timezone.utc).isoformat(),
                    "ticket": 2420002,
                    "position_ticket": 2420002,
                    "entry_order_ticket": 2420002,
                    "current_volume": 0.0,
                    "terminal_exit_type": "broker_closed",
                    "terminal_exit_time_utc": datetime.now(timezone.utc).isoformat(),
                },
                "exit": {
                    "exit_type": "broker_closed",
                    "exit_time": datetime.now(timezone.utc).isoformat(),
                    "broker_close_order_id": 2420003,
                },
            }
        ),
        encoding="utf-8",
    )
    intent = _intent()
    intent["primary_order"] = {"record_path": str(source_record)}
    runtime.reprocessable_failed_intent_ids.add(intent["intent_id"])
    intent["recorded_at_utc"] = (
        datetime.now(timezone.utc) - timedelta(minutes=5)
    ).isoformat()

    consumed = runtime.process_intent(intent)

    rows = [json.loads(line) for line in action_log.read_text(encoding="utf-8").splitlines()]
    assert consumed is True
    assert calls["open_trade"] == 0
    assert rows[-1]["event"] == "market_intent_reprocess_failed_retry_skipped_source_not_open"
    assert rows[-1]["source_record_retry_state"]["status"] == "source_record_terminal"
    assert intent["intent_id"] in runtime.processed_intent_ids
    assert intent["intent_id"] not in runtime.reprocessable_failed_intent_ids


def test_order_enabled_follower_consumes_retry_when_target_position_appears(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setenv("GTOS_RUNTIME_NAMESPACE", "operator_profile")
    calls = {"open_trade": 0}

    def _none_open_trade(self, *args, **kwargs):  # noqa: ANN001, ARG001
        calls["open_trade"] += 1
        return None

    monkeypatch.setattr(ExecutionEngine, "open_trade", _none_open_trade)
    mt5 = MockMT5()
    mt5.connect()
    _attach_order_calc_profit(mt5)
    mt5.set_tick(2350.10, 2350.20)
    action_log = tmp_path / "actions.jsonl"
    runtime = FollowerRuntime(
        mt5=mt5,
        base_config=_base_config(),
        target_namespace="operator_profile",
        source_namespace="redacted_account_live_bee34003",
        order_enabled=True,
        action_log=action_log,
        symbol_map={"XAUUSD": "XAUUSD"},
    )
    intent = _intent()

    first = runtime.process_intent(intent)
    mt5.set_positions(
        [
            PositionInfo(
                ticket=70003,
                symbol="XAUUSD",
                type=0,
                volume=0.10,
                price_open=2350.0,
                sl=2340.0,
                tp=2370.0,
                profit=0.0,
                magic=MAGIC_NUMBER,
                comment="dual_follower",
                time=datetime.now(timezone.utc),
            )
        ]
    )
    second = runtime.process_intent(intent)

    rows = [json.loads(line) for line in action_log.read_text(encoding="utf-8").splitlines()]
    assert first is False
    assert second is True
    assert calls["open_trade"] == 1
    assert rows[-1]["event"] == "market_intent_target_position_detected_before_retry"
    assert intent["intent_id"] in runtime.processed_intent_ids


def test_order_enabled_follower_expires_old_market_intent_when_target_order_returns_none(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setenv("GTOS_RUNTIME_NAMESPACE", "operator_profile")
    monkeypatch.setattr(
        ExecutionEngine,
        "open_trade",
        lambda self, *args, **kwargs: None,
    )
    mt5 = MockMT5()
    mt5.connect()
    _attach_order_calc_profit(mt5)
    mt5.set_tick(2350.10, 2350.20)
    action_log = tmp_path / "actions.jsonl"
    runtime = FollowerRuntime(
        mt5=mt5,
        base_config=_base_config(),
        target_namespace="operator_profile",
        source_namespace="redacted_account_live_bee34003",
        order_enabled=True,
        action_log=action_log,
        symbol_map={"XAUUSD": "XAUUSD"},
    )
    intent = _intent()
    intent["recorded_at_utc"] = (
        datetime.now(timezone.utc) - timedelta(minutes=10)
    ).isoformat()

    consumed = runtime.process_intent(intent)

    rows = [json.loads(line) for line in action_log.read_text(encoding="utf-8").splitlines()]
    assert consumed is True
    assert rows[-2]["event"] == "market_intent_expired_no_target_order"
    assert rows[-1]["event"] == "market_intent_processed"
    assert rows[-1]["result"] is None
    assert intent["intent_id"] in runtime.processed_intent_ids


def test_order_enabled_follower_allows_many_positions_when_drawdown_budget_allows(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setenv("GTOS_RUNTIME_NAMESPACE", "operator_profile")
    _redirect_execution_checkpoint(monkeypatch, tmp_path)
    mt5 = MockMT5()
    mt5.connect()
    _attach_order_calc_profit(mt5)
    mt5.set_tick(2350.10, 2350.20)
    mt5.set_positions([
        PositionInfo(
            ticket=70001,
            symbol="EURUSD",
            type=0,
            volume=0.10,
            price_open=1.10000,
            sl=1.10000,
            tp=1.12000,
            profit=0.0,
            magic=MAGIC_NUMBER,
            comment="dual_follower",
            time=datetime.now(timezone.utc),
        ),
        PositionInfo(
            ticket=70002,
            symbol="GBPUSD",
            type=1,
            volume=0.10,
            price_open=1.27000,
            sl=1.27000,
            tp=1.25000,
            profit=0.0,
            magic=MAGIC_NUMBER,
            comment="dual_follower",
            time=datetime.now(timezone.utc),
        ),
    ])
    action_log = tmp_path / "actions.jsonl"
    runtime = FollowerRuntime(
        mt5=mt5,
        base_config=_base_config(),
        target_namespace="operator_profile",
        source_namespace="redacted_account_live_bee34003",
        order_enabled=True,
        action_log=action_log,
        symbol_map={"EURUSD": "EURUSD", "GBPUSD": "GBPUSD", "XAUUSD": "XAUUSD"},
    )

    intent = _intent()
    consumed = runtime.process_intent(intent)

    rows = [json.loads(line) for line in action_log.read_text(encoding="utf-8").splitlines()]
    assert consumed is True
    assert rows[-1]["event"] == "market_intent_processed"
    assert rows[-1]["target_risk_budget"]["action"] == "ALLOW"
    assert rows[-1]["target_risk_budget"]["open_position_risk_amount"] == 0.0
    assert intent["intent_id"] in runtime.processed_intent_ids
    assert mt5._order_log


def test_order_enabled_follower_blocks_open_position_risk_without_broker_profit_model(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setenv("GTOS_RUNTIME_NAMESPACE", "operator_profile")
    mt5 = MockMT5()
    mt5.connect()
    mt5.set_tick(2350.10, 2350.20)
    mt5.set_positions(
        [
            PositionInfo(
                ticket=70004,
                symbol="XAUUSD",
                type=0,
                volume=0.10,
                price_open=2350.0,
                sl=2340.0,
                tp=2370.0,
                profit=25.0,
                magic=MAGIC_NUMBER,
                comment="dual_follower",
                time=datetime.now(timezone.utc),
            )
        ]
    )
    action_log = tmp_path / "actions.jsonl"
    runtime = FollowerRuntime(
        mt5=mt5,
        base_config=_base_config(),
        target_namespace="operator_profile",
        source_namespace="redacted_account_live_bee34003",
        order_enabled=True,
        action_log=action_log,
        symbol_map={"XAUUSD": "XAUUSD"},
    )

    consumed = runtime.process_intent(_intent())

    rows = [json.loads(line) for line in action_log.read_text(encoding="utf-8").splitlines()]
    assert consumed is True
    assert rows[-1]["event"] == "risk_guard_rejected"
    assert rows[-1]["reason"] == "target_open_position_sl_risk_unavailable"
    assert rows[-1]["target_risk_budget"]["open_position_risk_errors"] == [
        "open_position_sl_risk_unresolved:70004:broker_order_calc_profit_required_unavailable"
    ]
    assert mt5._order_log == []


def test_order_enabled_follower_reduces_risk_when_daily_budget_is_tight(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setenv("GTOS_RUNTIME_NAMESPACE", "operator_profile")
    _redirect_execution_checkpoint(monkeypatch, tmp_path)
    mt5 = MockMT5()
    mt5.connect()
    mt5._equity = 96300.0
    mt5.set_tick(2350.10, 2350.20)
    action_log = tmp_path / "actions.jsonl"
    runtime = FollowerRuntime(
        mt5=mt5,
        base_config=_base_config(),
        target_namespace="operator_profile",
        source_namespace="redacted_account_live_bee34003",
        order_enabled=True,
        action_log=action_log,
        symbol_map={"XAUUSD": "XAUUSD"},
    )

    consumed = runtime.process_intent(_intent())

    rows = [json.loads(line) for line in action_log.read_text(encoding="utf-8").splitlines()]
    assert consumed is True
    assert rows[-1]["event"] == "market_intent_processed"
    assert rows[-1]["target_risk_budget"]["action"] == "REDUCE_RISK"
    assert 0.0 < rows[-1]["risk_pct"] < 0.5
    assert mt5._order_log[0]["volume"] < 0.5


def test_order_enabled_follower_blocks_when_daily_budget_exhausted(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setenv("GTOS_RUNTIME_NAMESPACE", "operator_profile")
    mt5 = MockMT5()
    mt5.connect()
    mt5._equity = 96050.0
    mt5.set_tick(2350.10, 2350.20)
    action_log = tmp_path / "actions.jsonl"
    runtime = FollowerRuntime(
        mt5=mt5,
        base_config=_base_config(),
        target_namespace="operator_profile",
        source_namespace="redacted_account_live_bee34003",
        order_enabled=True,
        action_log=action_log,
        symbol_map={"XAUUSD": "XAUUSD"},
    )

    consumed = runtime.process_intent(_intent())

    rows = [json.loads(line) for line in action_log.read_text(encoding="utf-8").splitlines()]
    assert consumed is True
    assert rows[-1]["event"] == "risk_guard_rejected"
    assert rows[-1]["reason"] == (
        "target_account_drawdown_budget_blocked_by:internal_daily_drawdown_overlay"
    )
    assert mt5._order_log == []


def test_target_execution_context_errors_classifies_incomplete_vnext_intent():
    params = {
        "direction": "LONG",
        "entry_price": 2350.0,
        "stop_loss": 2340.0,
        "take_profit_1": 2370.0,
        "gtos_vnext_dynamic_policy_selected": "partial_be_runner",
        "gtos_vnext_selected_cell_risk_cell_id": "STAGE13-FN-RISK-CELL-EARLY",
        "gtos_vnext_selected_cell_risk_pct": 0.25,
    }

    errors = target_execution_context_errors(params)

    assert "missing:gtos_vnext_dynamic_policy_applied" in errors
    assert "missing:gtos_vnext_selected_cell_risk_selected_policy" in errors
    assert "selected_cell_commission_status_not_verified" in errors


def test_target_execution_context_allows_known_non_fatal_projection_reason():
    params = {
        "direction": "LONG",
        "entry_price": 2350.0,
        "stop_loss": 2340.0,
        "take_profit_1": 2370.0,
        "gtos_vnext_production_execution_path": True,
        "gtos_vnext_dynamic_policy_selected": "partial_be_runner",
        "gtos_vnext_execution_policy_id": "vnext_exec_partial_50_at_1r_be_runner_to_3r",
        "gtos_vnext_dynamic_policy_applied": True,
        "gtos_vnext_dynamic_policy_replaced_policy": "retired_static_baseline_comparator",
        "gtos_vnext_selected_cell_risk_pct": 0.25,
        "gtos_vnext_selected_cell_risk_cell_id": "STAGE13-FN-RISK-CELL-000305",
        "gtos_vnext_selected_cell_risk_selected_policy": "partial_be_runner",
        "gtos_vnext_selected_cell_risk_policy_identity_status": (
            "policy_invariant_broker_geometry_for_selected_execution_policy"
        ),
        "gtos_vnext_selected_cell_risk_unresolved_reasons": [
            "condition_challenger_cell_join_missing_for_broader_origin_allowlist_entry"
        ],
        "gtos_vnext_commission_model_status": (
            "SELECTED_CELL_RISK_LEDGER_VERIFIED_NO_EXECUTION_CRITICAL_COMMISSION_GAP"
        ),
    }

    assert target_execution_context_errors(params) == []


def test_target_execution_context_still_blocks_fatal_unresolved_reason():
    params = {
        "direction": "LONG",
        "entry_price": 2350.0,
        "stop_loss": 2340.0,
        "take_profit_1": 2370.0,
        "gtos_vnext_production_execution_path": True,
        "gtos_vnext_dynamic_policy_selected": "partial_be_runner",
        "gtos_vnext_execution_policy_id": "vnext_exec_partial_50_at_1r_be_runner_to_3r",
        "gtos_vnext_dynamic_policy_applied": True,
        "gtos_vnext_dynamic_policy_replaced_policy": "retired_static_baseline_comparator",
        "gtos_vnext_selected_cell_risk_pct": 0.25,
        "gtos_vnext_selected_cell_risk_cell_id": "STAGE13-FN-RISK-CELL-FATAL",
        "gtos_vnext_selected_cell_risk_selected_policy": "partial_be_runner",
        "gtos_vnext_selected_cell_risk_policy_identity_status": (
            "policy_invariant_broker_geometry_for_selected_execution_policy"
        ),
        "gtos_vnext_selected_cell_risk_execution_critical_unresolved_reasons": [
            "commission_model_unverified"
        ],
        "gtos_vnext_commission_model_status": (
            "SELECTED_CELL_RISK_LEDGER_VERIFIED_NO_EXECUTION_CRITICAL_COMMISSION_GAP"
        ),
    }

    errors = target_execution_context_errors(params)

    assert errors == ["selected_cell_unresolved:commission_model_unverified"]


def test_follower_offset_reader_exposes_row_end_for_retryable_deferral(tmp_path: Path):
    path = tmp_path / "intents.jsonl"
    first = _intent()
    second = _intent()
    second["source"]["trade_id"] = "tr_primary_2"
    second["intent_id"] = "second"
    path.write_text(
        json.dumps(first, sort_keys=True) + "\n" + json.dumps(second, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    rows, end_offset = read_intents_with_offsets(path, 0)

    assert len(rows) == 2
    assert rows[0][0]["intent_id"] == first["intent_id"]
    assert rows[0][1] < rows[1][1] == end_offset


def test_startup_recovery_instantiates_only_symbols_with_target_positions(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setenv("GTOS_RUNTIME_NAMESPACE", "operator_profile")
    monkeypatch.setattr(exec_mod, "PENDING_INTENT_DIR", str(tmp_path / "meta"))
    monkeypatch.setattr(follower_mod, "PENDING_INTENT_DIR", str(tmp_path / "meta"))
    mt5 = MockMT5()
    mt5.connect()
    opened_at = datetime.now(timezone.utc)
    mt5.set_positions(
        [
            PositionInfo(
                ticket=70001,
                symbol="XAUUSD",
                type=0,
                volume=0.10,
                price_open=2350.0,
                sl=2340.0,
                tp=2370.0,
                profit=25.0,
                magic=MAGIC_NUMBER,
                comment="dual_follower",
                time=opened_at,
            )
        ]
    )
    action_log = tmp_path / "actions.jsonl"
    runtime = FollowerRuntime(
        mt5=mt5,
        base_config={
            **_base_config(),
            "instruments": {
                **_base_config()["instruments"],
                "EURUSD": {
                    "market": {
                        "symbol": "EURUSD",
                        "mt5_symbol": "EURUSD",
                        "tick_size": 0.00001,
                        "point": 0.00001,
                        "digits": 5,
                        "trade_tick_size": 0.00001,
                        "trade_tick_value": 1.0,
                        "contract_size": 100000.0,
                        "volume_min": 0.01,
                        "volume_max": 100.0,
                        "volume_step": 0.01,
                        "trade_stops_level": 0,
                        "trade_freeze_level": 0,
                    }
                },
            },
        },
        target_namespace="operator_profile",
        source_namespace="redacted_account_live_bee34003",
        order_enabled=True,
        action_log=action_log,
        symbol_map={"EURUSD": "EURUSD", "XAUUSD": "XAUUSD"},
        target_trade_state_path=tmp_path / "target_state.json",
    )

    summary = runtime.recover_target_state_on_startup()

    assert sorted(runtime.engines) == ["XAUUSD"]
    assert summary["symbols_with_positions"] == ["XAUUSD"]
    assert summary["engine_symbols"] == ["XAUUSD"]
    assert runtime.engines["XAUUSD"].active_trade is not None
    assert runtime.engines["XAUUSD"].active_trade.ticket == 70001


def _dynamic_target_trade_state(
    ticket: int = 70001,
    *,
    tp1_hit: bool = True,
    sl_at_breakeven: bool = True,
    current_volume: float = 0.10,
) -> TradeState:
    return TradeState(
        ticket=ticket,
        direction="LONG",
        entry_price=2350.0,
        stop_loss=2340.0,
        take_profit_1=2360.0,
        take_profit_2=2380.0,
        take_profit_3=0.0,
        initial_volume=0.20,
        current_volume=current_volume,
        sl_distance=10.0,
        trade_id="tr_ftmo_target",
        entry_time=datetime.now(timezone.utc).isoformat(),
        tp1_hit=tp1_hit,
        sl_at_breakeven=sl_at_breakeven,
        gtos_vnext_dynamic_policy_selected="partial_be_runner",
        gtos_vnext_dynamic_policy_applied=True,
        gtos_vnext_execution_policy_id="vnext_exec_partial_50_at_1r_be_runner_to_3r",
        gtos_vnext_dynamic_be_trigger_r=1.0,
        gtos_vnext_dynamic_final_target_r=3.0,
        gtos_vnext_dynamic_be_trigger_price=2360.0,
        gtos_vnext_dynamic_final_target_price=2380.0,
        position_confirmed=True,
    )


def test_persist_target_trade_state_refreshes_blank_cash_risk_provenance_from_broker(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setenv("GTOS_RUNTIME_NAMESPACE", "operator_profile")
    mt5 = MockMT5()
    mt5.connect()
    _attach_order_calc_profit(mt5)
    mt5.set_positions(
        [
            PositionInfo(
                ticket=70008,
                symbol="XAUUSD",
                type=0,
                volume=0.10,
                price_open=2350.0,
                sl=2340.0,
                tp=2380.0,
                profit=25.0,
                magic=MAGIC_NUMBER,
                comment="dual_follower",
                time=datetime.now(timezone.utc),
            )
        ]
    )
    action_log = tmp_path / "actions.jsonl"
    runtime = FollowerRuntime(
        mt5=mt5,
        base_config=_base_config(),
        target_namespace="operator_profile",
        source_namespace="redacted_account_live_bee34003",
        order_enabled=True,
        action_log=action_log,
        symbol_map={"XAUUSD": "XAUUSD"},
        target_trade_state_path=tmp_path / "target_state.json",
    )
    engine = ExecutionEngine(mt5, _base_config())
    trade = _dynamic_target_trade_state(ticket=70008, current_volume=0.10)
    trade.cash_risk_amount = 200.0
    trade.cash_risk_amount_source = ""
    trade.cash_risk_amount_status = ""
    engine.active_trade = trade
    runtime.engines["XAUUSD"] = engine
    runtime.active_trade_intent_ids["70008"] = "intent_70008"

    state = runtime.persist_target_trade_state(reason="live_loop")

    persisted = state["active_trades_by_ticket"]["70008"]["trade_state"]
    assert persisted["cash_risk_amount_status"] == "LEGACY_AMOUNT_CURRENT_SL_RISK_VERIFIED"
    assert persisted["cash_risk_amount_source"] == (
        "legacy_target_state_amount_current_sl_broker_order_calc_profit_checked"
    )
    assert state["active_trades_by_ticket"]["70008"]["intent_id"] == "intent_70008"


def test_startup_recovery_restores_persisted_target_trade_state_snapshot(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setenv("GTOS_RUNTIME_NAMESPACE", "operator_profile")
    monkeypatch.setattr(exec_mod, "PENDING_INTENT_DIR", str(tmp_path / "meta"))
    monkeypatch.setattr(follower_mod, "PENDING_INTENT_DIR", str(tmp_path / "meta"))
    mt5 = MockMT5()
    mt5.connect()
    opened_at = datetime.now(timezone.utc)
    mt5.set_positions(
        [
            PositionInfo(
                ticket=70001,
                symbol="XAUUSD",
                type=0,
                volume=0.10,
                price_open=2350.0,
                sl=2350.0,
                tp=2380.0,
                profit=75.0,
                magic=MAGIC_NUMBER,
                comment="dual_follower",
                time=opened_at,
            )
        ]
    )
    state_path = tmp_path / "target_state.json"
    trade = _dynamic_target_trade_state()
    trade.cash_risk_amount = 200.0
    action_log = tmp_path / "actions.jsonl"
    action_log.write_text(
        json.dumps(
            {
                "event": "market_intent_processed",
                "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
                "symbol": "XAUUSD",
                "intent_id": "intent_70001",
                "result": trade.__dict__,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    state_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "target_namespace": "operator_profile",
                "active_trades_by_ticket": {
                    "70001": {
                        "schema_version": 1,
                        "symbol": "XAUUSD",
                        "broker_symbol": "XAUUSD",
                        "ticket": 70001,
                        "source": "unit_test",
                        "trade_state": trade.__dict__,
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    runtime = FollowerRuntime(
        mt5=mt5,
        base_config=_base_config(),
        target_namespace="operator_profile",
        source_namespace="redacted_account_live_bee34003",
        order_enabled=True,
        action_log=action_log,
        symbol_map={"XAUUSD": "XAUUSD"},
        target_trade_state_path=state_path,
    )

    summary = runtime.recover_target_state_on_startup()

    restored = runtime.engines["XAUUSD"].active_trade
    assert restored is not None
    assert restored.trade_id == "tr_ftmo_target"
    assert restored.gtos_vnext_dynamic_policy_selected == "partial_be_runner"
    assert restored.gtos_vnext_dynamic_policy_applied is True
    assert restored.take_profit_2 == 2380.0
    assert restored.sl_distance == 10.0
    assert restored.stop_loss == 2350.0
    assert restored.sl_at_breakeven is True
    assert restored.cash_risk_amount == 200.0
    assert restored.cash_risk_amount_status == (
        "LEGACY_AMOUNT_CURRENT_SL_ZERO_RISK_TICK_METADATA_CHECKED"
    )
    assert restored.cash_risk_amount_source == (
        "legacy_target_state_amount_current_sl_symbol_tick_metadata_fallback"
        "_zero_risk_checked"
    )
    assert restored.broker_lot_sizing_diagnostic is not None
    assert (
        restored.broker_lot_sizing_diagnostic[
            "target_state_restore_cash_risk_provenance"
        ]["current_stop_cash_risk_amount"]
        == 0.0
    )
    restore_status = summary["recovered_actions"][0]["target_trade_state_restore"]
    assert restore_status["status"] == "target_trade_state_restored"
    assert restore_status["intent_id"] == "intent_70001"
    state_after = json.loads(state_path.read_text(encoding="utf-8"))
    assert state_after["active_trades_by_ticket"]["70001"]["intent_id"] == "intent_70001"


def test_startup_recovery_infers_partial_residual_from_broker_state(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setenv("GTOS_RUNTIME_NAMESPACE", "operator_profile")
    monkeypatch.setattr(exec_mod, "PENDING_INTENT_DIR", str(tmp_path / "meta"))
    monkeypatch.setattr(follower_mod, "PENDING_INTENT_DIR", str(tmp_path / "meta"))
    mt5 = MockMT5()
    mt5.connect()
    opened_at = datetime.now(timezone.utc)
    mt5.set_positions(
        [
            PositionInfo(
                ticket=70003,
                symbol="XAUUSD",
                type=0,
                volume=0.10,
                price_open=2350.0,
                sl=2350.0,
                tp=2380.0,
                profit=50.0,
                magic=MAGIC_NUMBER,
                comment="TP1_vnext_partia",
                time=opened_at,
            )
        ]
    )
    mt5.set_tick(2365.0, 2365.2)
    action_log = tmp_path / "actions.jsonl"
    trade = _dynamic_target_trade_state(
        ticket=70003,
        tp1_hit=False,
        sl_at_breakeven=False,
        current_volume=0.20,
    )
    action_log.write_text(
        json.dumps(
            {
                "event": "market_intent_processed",
                "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
                "symbol": "XAUUSD",
                "intent_id": "intent_70003",
                "result": trade.__dict__,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    runtime = FollowerRuntime(
        mt5=mt5,
        base_config=_base_config(),
        target_namespace="operator_profile",
        source_namespace="redacted_account_live_bee34003",
        order_enabled=True,
        action_log=action_log,
        symbol_map={"XAUUSD": "XAUUSD"},
        target_trade_state_path=tmp_path / "target_state.json",
    )

    runtime.recover_target_state_on_startup()
    restored = runtime.engines["XAUUSD"].active_trade

    assert restored is not None
    assert restored.current_volume == 0.10
    assert restored.sl_at_breakeven is True
    assert restored.tp1_hit is True
    assert any(
        event.get("type") == "TARGET_STATE_RECOVERED_BROKER_RESIDUAL"
        for event in restored.partial_close_events
    )
    runtime.manage_live_state()
    assert mt5._order_log == []


def test_startup_recovery_can_restore_target_trade_state_from_action_log(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setenv("GTOS_RUNTIME_NAMESPACE", "operator_profile")
    monkeypatch.setattr(exec_mod, "PENDING_INTENT_DIR", str(tmp_path / "meta"))
    monkeypatch.setattr(follower_mod, "PENDING_INTENT_DIR", str(tmp_path / "meta"))
    mt5 = MockMT5()
    mt5.connect()
    opened_at = datetime.now(timezone.utc)
    mt5.set_positions(
        [
            PositionInfo(
                ticket=70002,
                symbol="XAUUSD",
                type=0,
                volume=0.20,
                price_open=2350.0,
                sl=2340.0,
                tp=2380.0,
                profit=10.0,
                magic=MAGIC_NUMBER,
                comment="dual_follower",
                time=opened_at,
            )
        ]
    )
    action_log = tmp_path / "actions.jsonl"
    trade = _dynamic_target_trade_state(ticket=70002)
    action_log.write_text(
        json.dumps(
            {
                "event": "market_intent_processed",
                "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
                "symbol": "XAUUSD",
                "intent_id": "intent_70002",
                "result": trade.__dict__,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    runtime = FollowerRuntime(
        mt5=mt5,
        base_config=_base_config(),
        target_namespace="operator_profile",
        source_namespace="redacted_account_live_bee34003",
        order_enabled=True,
        action_log=action_log,
        symbol_map={"XAUUSD": "XAUUSD"},
        target_trade_state_path=tmp_path / "target_state.json",
    )

    summary = runtime.recover_target_state_on_startup()

    restored = runtime.engines["XAUUSD"].active_trade
    assert restored is not None
    assert restored.ticket == 70002
    assert restored.gtos_vnext_dynamic_policy_selected == "partial_be_runner"
    assert restored.gtos_vnext_dynamic_final_target_r == 3.0
    restore_status = summary["recovered_actions"][0]["target_trade_state_restore"]
    assert restore_status["source"] == "dual_broker_execution_follower_action_log"
    assert restore_status["intent_id"] == "intent_70002"
    assert runtime.active_trade_intent_ids["70002"] == "intent_70002"
    state_after = json.loads(
        (tmp_path / "target_state.json").read_text(encoding="utf-8")
    )
    assert state_after["active_trades_by_ticket"]["70002"]["intent_id"] == "intent_70002"


def test_startup_recovery_restores_persisted_target_pending_intent(
    tmp_path: Path,
    monkeypatch,
):
    pending_dir = tmp_path / "meta"
    monkeypatch.setenv("GTOS_RUNTIME_NAMESPACE", "operator_profile")
    monkeypatch.setattr(exec_mod, "PENDING_INTENT_DIR", str(pending_dir))
    monkeypatch.setattr(follower_mod, "PENDING_INTENT_DIR", str(pending_dir))
    mt5 = MockMT5()
    mt5.connect()
    cfg = _base_config()
    seed_engine = ExecutionEngine(mt5, cfg)
    pending = seed_engine.set_limit_intent(
        {
            "direction": "LONG",
            "entry_price": 2350.0,
            "stop_loss": 2340.0,
            "take_profit_1": 2370.0,
            "risk_reward_ratio": 2.0,
        },
        account_balance=100000.0,
        risk_pct_override=0.5,
    )
    assert pending is not None

    action_log = tmp_path / "actions.jsonl"
    runtime = FollowerRuntime(
        mt5=mt5,
        base_config=cfg,
        target_namespace="operator_profile",
        source_namespace="redacted_account_live_bee34003",
        order_enabled=True,
        action_log=action_log,
        symbol_map={"XAUUSD": "XAUUSD"},
        target_trade_state_path=tmp_path / "target_state.json",
    )

    summary = runtime.recover_target_state_on_startup()

    assert summary["symbols_with_pending_intents"] == ["XAUUSD"]
    assert sorted(runtime.engines) == ["XAUUSD"]
    assert runtime.engines["XAUUSD"].pending_intent is not None
    assert runtime.engines["XAUUSD"].pending_intent.trade_id == pending.trade_id
