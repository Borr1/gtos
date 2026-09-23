import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.components import execution as _exec_mod
from src.components.execution import ExecutionEngine, TradeState
from src.components.orchestrator import SessionOrchestrator
from src.components.permissions import check_permissions
from src.components import pending_limit_lifecycle_logger as _pending_log
from src.mt5.mt5_interface import MAGIC_NUMBER, PositionInfo, TRADE_ACTION_DEAL, TRADE_ACTION_SLTP
from src.mt5.mt5_mock import MockMT5
from src.safety.runtime_halt import RuntimeHaltError, read_runtime_halt_state


def _runtime_config(tmp_path: Path) -> dict:
    return {
        "runtime_control": {
            "enabled": True,
            "repo_root": str(tmp_path),
            "halt_flag_paths": [
                "pipeline_state/GTOS_HARD_PRODUCTION_HALT.flag",
                "pipeline_state/RESEARCH_RUNTIME_HALT.flag",
                "knowledge_base/meta/AUTOSTART_DISABLED.flag",
            ],
            "audit_log_path": "audit/runtime_halt.jsonl",
            "fail_closed_on_unreadable_flag_path": True,
        },
        "market": {"symbol": "XAUUSD", "mt5_symbol": "XAUUSD"},
        "risk": {"risk_per_trade_pct": 1.0, "sl_absolute_min": 0.0},
    }


def _touch_flag(tmp_path: Path, rel_path: str) -> Path:
    path = tmp_path / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("halt\n", encoding="utf-8")
    return path


def _engine(tmp_path: Path, monkeypatch) -> tuple[ExecutionEngine, MockMT5, dict]:
    monkeypatch.setattr(
        _exec_mod,
        "CHECKPOINT_PATH",
        str(tmp_path / "meta" / "execution_checkpoint.json"),
    )
    monkeypatch.setattr(_exec_mod, "PENDING_INTENT_DIR", str(tmp_path / "meta"))
    monkeypatch.setattr(
        _pending_log,
        "PENDING_LIMIT_LIFECYCLE_LOG_PATH",
        str(tmp_path / "shadow" / "pending_limit_lifecycle.jsonl"),
    )
    mt5 = MockMT5(balance=100000.0)
    mt5.connect()
    config = _runtime_config(tmp_path)
    return ExecutionEngine(mt5, config), mt5, config


def _trade_params() -> dict:
    return {
        "direction": "LONG",
        "entry_price": 2650.0,
        "stop_loss": 2640.0,
        "take_profit_1": 2670.0,
        "take_profit_2": 0.0,
        "take_profit_3": 0.0,
        "risk_reward_ratio": 2.0,
        "candidate_id": "fixture-candidate",
    }


def _position(ticket: int = 700101) -> PositionInfo:
    return PositionInfo(
        ticket=ticket,
        symbol="XAUUSD",
        type=0,
        volume=0.10,
        price_open=2650.0,
        sl=2640.0,
        tp=2670.0,
        profit=0.0,
        magic=MAGIC_NUMBER,
        comment="fixture",
        time=datetime.now(timezone.utc),
    )


def test_runtime_halt_snapshot_detects_all_current_flag_sources(tmp_path):
    config = _runtime_config(tmp_path)
    for rel_path in config["runtime_control"]["halt_flag_paths"]:
        _touch_flag(tmp_path, rel_path)

    snapshot = read_runtime_halt_state(config)

    assert snapshot.active is True
    assert snapshot.status == "runtime_halt_active"
    assert len(snapshot.active_flags) == 3
    assert snapshot.broker_runtime_change_status is False
    assert snapshot.forbidden_surface_status == (
        "no_broker_account_order_deal_position_mutation_performed"
    )


def test_permissions_gate0_runtime_halt_blocks_before_other_gates(tmp_path):
    config = _runtime_config(tmp_path)
    _touch_flag(tmp_path, "pipeline_state/GTOS_HARD_PRODUCTION_HALT.flag")

    denial = check_permissions(
        trade_params={},
        mso=None,
        session_state={},
        mt5=None,
        config=config,
        symbol="XAUUSD",
    )

    assert denial is not None
    assert denial.gate == "gate0_runtime_halt"
    assert denial.reason == "runtime_halt_active"
    assert denial.details["broker_runtime_change_status"] is False


def test_orchestrator_bootstrap_blocks_before_lock_or_mt5_connect(tmp_path, monkeypatch):
    config = _runtime_config(tmp_path)
    _touch_flag(tmp_path, "pipeline_state/GTOS_HARD_PRODUCTION_HALT.flag")
    calls: list[str] = []
    orch = SessionOrchestrator.__new__(SessionOrchestrator)
    orch.mode = "demo"
    orch.config = config
    orch._symbol = "XAUUSD"
    orch._mt5_symbol = "XAUUSD"
    orch._profile_name = "redacted_account"
    orch._runtime_namespace = "fixture_namespace"
    orch._terminal_path = None
    monkeypatch.setattr(
        SessionOrchestrator,
        "_acquire_lock",
        lambda self: calls.append("lock"),
    )

    with pytest.raises(RuntimeHaltError):
        SessionOrchestrator._bootstrap(orch)

    assert calls == []


def test_safe_place_order_blocks_before_checkpoint_or_mt5_order_send(tmp_path, monkeypatch):
    engine, mt5, _config = _engine(tmp_path, monkeypatch)
    _touch_flag(tmp_path, "pipeline_state/GTOS_HARD_PRODUCTION_HALT.flag")
    request = {
        "action": 1,
        "symbol": "XAUUSD",
        "volume": 0.10,
        "type": 0,
        "price": 2650.18,
        "sl": 2640.0,
        "tp": 2670.0,
    }

    result = engine.safe_place_order(request)

    assert result is not None
    assert result.success is False
    assert result.comment == "runtime_halt_active_no_order_send"
    assert mt5._order_log == []
    assert not Path(_exec_mod.CHECKPOINT_PATH).exists()
    assert engine._last_order_send_diagnostic["status"] == (
        "runtime_halt_blocked_no_order_send"
    )
    audit_rows = (tmp_path / "audit" / "runtime_halt.jsonl").read_text().splitlines()
    assert len(audit_rows) == 1
    assert json.loads(audit_rows[0])["decision"] == "blocked_by_runtime_halt"


def test_set_limit_intent_refuses_under_runtime_halt(tmp_path, monkeypatch):
    engine, mt5, _config = _engine(tmp_path, monkeypatch)
    _touch_flag(tmp_path, "knowledge_base/meta/AUTOSTART_DISABLED.flag")

    intent = engine.set_limit_intent(_trade_params(), 100000.0)

    assert intent is None
    assert engine.pending_intent is None
    assert mt5._order_log == []
    assert not Path(engine._pending_intent_path).exists()
    assert engine._last_runtime_halt_diagnostic["action"] == "set_limit_intent"


def test_check_limit_fill_cancels_existing_intent_without_order_send(tmp_path, monkeypatch):
    engine, mt5, _config = _engine(tmp_path, monkeypatch)
    intent = engine.set_limit_intent(_trade_params(), 100000.0)
    assert intent is not None
    assert engine.pending_intent is not None

    _touch_flag(tmp_path, "pipeline_state/RESEARCH_RUNTIME_HALT.flag")
    trade_state = engine.check_limit_fill(
        {"time": "2026-06-04T12:00:00+00:00", "open": 2655.0, "high": 2656.0, "low": 2649.0, "close": 2651.0},
        telemetry_context={"check_context": "fixture"},
    )

    assert trade_state is None
    assert engine.pending_intent is None
    assert mt5._order_log == []
    lifecycle_path = tmp_path / "shadow" / "pending_limit_lifecycle.jsonl"
    row = json.loads(lifecycle_path.read_text(encoding="utf-8").splitlines()[-1])
    assert row["intent_after_check"] == "runtime_halt_cancelled_no_order_send"
    assert row["fill_no_fill_label"] == "no_fill_runtime_halt_cancelled"


def test_halt_blocks_new_entries_but_allows_risk_reducing_management(tmp_path, monkeypatch):
    engine, mt5, _config = _engine(tmp_path, monkeypatch)
    lifecycle_log = tmp_path / "shadow" / "broker_lifecycle.jsonl"
    _config["gtos_vnext_runtime"] = {
        "broker_order_lifecycle_capture_v4_enabled": True,
        "broker_order_lifecycle_capture_v4_log_enabled": True,
        "broker_order_lifecycle_capture_v4_log_path": str(lifecycle_log),
    }
    trade = TradeState(
        ticket=700101,
        direction="LONG",
        entry_price=2650.0,
        stop_loss=2640.0,
        take_profit_1=2670.0,
        take_profit_2=0.0,
        take_profit_3=0.0,
        initial_volume=0.10,
        current_volume=0.10,
        sl_distance=10.0,
        trade_id="fixture-trade",
        entry_time=datetime.now(timezone.utc).isoformat(),
        position_confirmed=True,
    )
    engine.active_trade = trade
    mt5.set_positions([_position(trade.ticket)])
    _touch_flag(tmp_path, "pipeline_state/GTOS_HARD_PRODUCTION_HALT.flag")

    assert engine._modify_sl(trade.ticket, 2650.0, trade=trade) is True
    assert engine._modify_tp(trade.ticket, 2680.0, trade=trade) is True
    assert mt5.get_positions("XAUUSD")[0].sl == 2650.0
    assert mt5.get_positions("XAUUSD")[0].tp == 2680.0
    assert engine.close_position("manual") is True
    assert engine.active_trade is None
    assert any(req.get("action") == TRADE_ACTION_SLTP for req in mt5._order_log)
    assert any(req.get("action") == 1 and req.get("position") == trade.ticket for req in mt5._order_log)
    rows = [json.loads(line) for line in lifecycle_log.read_text(encoding="utf-8").splitlines()]
    stages = [row["stage"] for row in rows]
    assert stages.count("sltp_modify_result") >= 2
    assert "close_position_result" in stages
    assert all(row["schema_version"] == "broker_order_lifecycle_capture_v4_runtime_event_v1" for row in rows)


def test_halt_position_field_requires_true_broker_reduction(tmp_path, monkeypatch):
    engine, mt5, _config = _engine(tmp_path, monkeypatch)
    ticket = 700101
    mt5.set_positions([_position(ticket)])
    _touch_flag(tmp_path, "pipeline_state/GTOS_HARD_PRODUCTION_HALT.flag")

    same_side = {
        "action": TRADE_ACTION_DEAL,
        "symbol": "XAUUSD",
        "position": ticket,
        "volume": 0.10,
        "type": 0,
        "price": 2650.18,
    }
    oversized_close = {
        "action": TRADE_ACTION_DEAL,
        "symbol": "XAUUSD",
        "position": ticket,
        "volume": 0.20,
        "type": 1,
        "price": 2649.82,
    }

    assert engine.safe_place_order(same_side).comment == "runtime_halt_active_no_order_send"
    assert engine.safe_place_order(oversized_close).comment == "runtime_halt_active_no_order_send"
    assert mt5._order_log == []
    assert mt5.get_positions("XAUUSD")[0].volume == 0.10


def test_halt_blocks_sl_loosening(tmp_path, monkeypatch):
    engine, mt5, _config = _engine(tmp_path, monkeypatch)
    trade = TradeState(
        ticket=700101,
        direction="LONG",
        entry_price=2650.0,
        stop_loss=2640.0,
        take_profit_1=2670.0,
        take_profit_2=0.0,
        take_profit_3=0.0,
        initial_volume=0.10,
        current_volume=0.10,
        sl_distance=10.0,
        trade_id="fixture-trade",
        entry_time=datetime.now(timezone.utc).isoformat(),
        position_confirmed=True,
    )
    engine.active_trade = trade
    mt5.set_positions([_position(trade.ticket)])
    _touch_flag(tmp_path, "pipeline_state/GTOS_HARD_PRODUCTION_HALT.flag")

    assert engine._modify_sl(trade.ticket, 2635.0, trade=trade) is False
    assert mt5.get_positions("XAUUSD")[0].sl == 2640.0
    assert engine._last_sltp_modify_diagnostic["failure_reason"] == (
        "runtime_halt_active_sl_modify_not_risk_reducing"
    )
