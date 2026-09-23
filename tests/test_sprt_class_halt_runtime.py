from __future__ import annotations

import json
from types import SimpleNamespace

from src.components.orchestrator import SessionOrchestrator
from src.components.sprt_class_halt_runtime import (
    SprtClassHaltDecision,
    SprtClassHaltRuntime,
)


def _cfg(*, automation_enabled: bool = True) -> dict:
    return {
        "sprt_halt": {
            "enabled": True,
            "automation_enabled": automation_enabled,
            "trigger_n": 20,
            "early_warning_n": 10,
            "per_class_thresholds": {
                "metals": {
                    "halt_wr_pct": 55.0,
                    "early_warning_wr_pct": 50.0,
                    "instruments": ["XAUUSD", "XAGUSD"],
                },
            },
        }
    }


def test_first_twenty_long_outcomes_trigger_active_halt(tmp_path):
    runtime = SprtClassHaltRuntime(_cfg(), state_path=tmp_path / "sprt_class.json")

    for outcome in [True] * 10 + [False] * 10:
        decision = runtime.record_long_outcome("XAUUSD", was_win=outcome, dispatch=False)

    assert decision.verdict == "HALT_TRIGGERED"
    assert decision.actual_wr == 50.0
    assert decision.threshold_breached == 55.0
    assert decision.should_block is True
    assert decision.would_block is True

    reloaded = SprtClassHaltRuntime(_cfg(), state_path=tmp_path / "sprt_class.json")
    gate = reloaded.evaluate_gate("XAUUSD")
    assert gate.should_block is True
    assert gate.reason == "sprt_class_halt_active_block"

    state = json.loads((tmp_path / "sprt_class.json").read_text(encoding="utf-8"))
    assert len(state["long_outcomes_by_symbol"]["XAUUSD"]) == 20
    assert state["halted_symbols"]["XAUUSD"]["verdict"] == "HALT_TRIGGERED"


def test_automation_flag_controls_effect_not_state(tmp_path):
    runtime = SprtClassHaltRuntime(
        _cfg(automation_enabled=False),
        state_path=tmp_path / "sprt_class.json",
    )

    for outcome in [True] * 10 + [False] * 10:
        decision = runtime.record_long_outcome("XAUUSD", was_win=outcome, dispatch=False)

    assert decision.verdict == "HALT_TRIGGERED"
    assert decision.would_block is True
    assert decision.should_block is False
    assert decision.reason == "shadow_sprt_class_halt_would_block"


def test_first_twenty_sample_is_locked_after_ok_verdict(tmp_path):
    runtime = SprtClassHaltRuntime(_cfg(), state_path=tmp_path / "sprt_class.json")

    for outcome in [True] * 12 + [False] * 8:
        decision = runtime.record_long_outcome("XAUUSD", was_win=outcome, dispatch=False)
    assert decision.verdict == "OK"
    assert decision.should_block is False

    for _ in range(20):
        decision = runtime.record_long_outcome("XAUUSD", was_win=False, dispatch=False)

    assert decision.verdict == "OK"
    state = json.loads((tmp_path / "sprt_class.json").read_text(encoding="utf-8"))
    assert len(state["long_outcomes_by_symbol"]["XAUUSD"]) == 20
    assert sum(1 for row in state["long_outcomes_by_symbol"]["XAUUSD"] if row["win"]) == 12


def test_orchestrator_gate_cancels_pending_and_blocks_when_active():
    decision = SprtClassHaltDecision(
        enabled=True,
        automation_enabled=True,
        symbol="XAUUSD",
        should_block=True,
        would_block=True,
        reason="sprt_class_halt_active_block",
        verdict="HALT_TRIGGERED",
        class_name="metals",
        actual_wr=50.0,
        threshold_breached=55.0,
        n=20,
    )
    cancelled: list[str] = []
    cleared: list[tuple[str, str]] = []
    logged: list[tuple[str, str, str]] = []

    orch = SessionOrchestrator.__new__(SessionOrchestrator)
    orch.config = _cfg()
    orch._symbol = "XAUUSD"
    orch._sprt_class_halt_runtime = SimpleNamespace(
        evaluate_gate=lambda symbol: decision
    )
    orch.execution = SimpleNamespace(
        pending_intent=SimpleNamespace(trade_id="trade-1"),
        cancel_limit_intent=lambda reason: cancelled.append(reason),
    )
    orch._clear_pending_trade_record = lambda trade_id, reason: cleared.append(
        (trade_id, reason)
    )
    orch._log_candle = lambda state, reason, kill_zone: logged.append(
        (state, reason, kill_zone)
    )

    assert orch._check_sprt_class_halt_gate("london") is True
    assert cancelled == ["sprt_class_halt"]
    assert cleared == [("trade-1", "sprt_class_halt")]
    assert logged == [
        ("SPRT_CLASS_HALT", "sprt_class_halt_active_block:HALT_TRIGGERED", "london")
    ]
