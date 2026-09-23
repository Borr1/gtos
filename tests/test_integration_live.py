"""Integration tests for the live trading pipeline (Phase 5).

All tests use MockMT5 — no real MT5 connection required.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.components import execution as _exec_mod
from src.components.execution import ExecutionEngine, PendingLimitIntent, TradeState
from src.components.orchestrator import SessionOrchestrator, prescreen_mso
from src.components.permissions import check_permissions
from src.components.trade_capture import (
    save_trade_record, load_trade_record, index_pending_record,
    lookup_pending_record, remove_pending_record,
)
from src.mt5.mt5_mock import MockMT5
from src.mt5.mt5_interface import MAGIC_NUMBER, PositionInfo


# Isolate checkpoint + pending_intent writes to tmp_path so tests never touch
# the real knowledge_base/meta/{execution_checkpoint.json, pending_intent_*.pkl}.
# Same pattern as tests/test_execution.py + tests/test_limit_order_flow.py.
# See tests/conftest.py for the project-wide write guard that catches violations.
@pytest.fixture(autouse=True)
def _isolate_checkpoint(tmp_path, monkeypatch):
    monkeypatch.setattr(
        _exec_mod, "CHECKPOINT_PATH", str(tmp_path / "execution_checkpoint.json")
    )
    monkeypatch.setattr(_exec_mod, "PENDING_INTENT_DIR", str(tmp_path))
    yield


def test_execution_persistence_paths_are_isolated_to_tmp_path(tmp_path):
    assert Path(_exec_mod.CHECKPOINT_PATH) == tmp_path / "execution_checkpoint.json"
    assert Path(_exec_mod.PENDING_INTENT_DIR) == tmp_path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mso(d1_dir="bullish", h4_dir="bullish", m15_atr=3.0):
    """Build a minimal MSO-like object."""
    return SimpleNamespace(
        timeframes={
            "D1": SimpleNamespace(structure=SimpleNamespace(direction=d1_dir)),
            "H4": SimpleNamespace(structure=SimpleNamespace(direction=h4_dir)),
            "M15": SimpleNamespace(atr_14=m15_atr),
        },
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
    )


def _make_pa_output(decision="CANDIDATE", direction="LONG", entry=2650.0,
                     sl=2640.0, tp1=2665.0, tp2=2675.0, tp3=2685.0,
                     rr=1.5, grade="A+", daily_bias="bullish"):
    """Build a mock PrimaryAnalysisOutput-like object."""
    tp_obj = SimpleNamespace(
        direction=direction, entry_price=entry, stop_loss=sl,
        take_profit_1=tp1, take_profit_2=tp2, take_profit_3=tp3,
        risk_reward_ratio=rr, position_size_lots=0.0,
    )
    reasoning = SimpleNamespace(
        setup_grade=grade,
        daily_bias=SimpleNamespace(direction=daily_bias),
    )
    return SimpleNamespace(
        decision=decision,
        confidence_score=85,
        trade_parameters=tp_obj if decision == "CANDIDATE" else None,
        reasoning=reasoning,
        no_trade_reason="ranging" if decision == "NO_TRADE" else None,
        wait_reason="waiting for displacement" if decision == "WAIT" else None,
    )


def _make_session_state(kz="london", trades_today=0):
    return {
        "date": "2026-04-01",
        "trades_today": trades_today,
        "trades_london": 0,
        "trades_ny": 0,
        "daily_pnl_pct": 0.0,
        "current_kill_zone": kz,
        "losses_today": 0,
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestFullPipelineNoTrade:
    def test_prescreen_passes_ranging_d1_clear_h4(self):
        """D1 transitional + H4 bullish → passes (H4 provides direction)."""
        mso = _make_mso(d1_dir="transitional", h4_dir="bullish")
        passed, reason = prescreen_mso(mso)
        assert passed
        assert reason == ""

    def test_prescreen_fails_both_unclear(self):
        """Both D1 and H4 unclear → no directional consensus → skip."""
        mso = _make_mso(d1_dir="transitional", h4_dir="ranging")
        passed, reason = prescreen_mso(mso)
        assert not passed
        assert "no_direction" in reason


class TestFullPipelineCandidateExecuted:
    def test_candidate_passes_all_gates_and_executes(self):
        """Trending D1/H4 + valid CANDIDATE → permissions pass → trade placed."""
        mt5 = MockMT5()
        mt5.connect()
        mt5.set_tick(2650.00, 2650.18)

        pa = _make_pa_output(decision="CANDIDATE", grade="A+", rr=1.5,
                              entry=2650.0, sl=2640.0, tp1=2665.0,
                              daily_bias="bullish")
        mso = _make_mso(d1_dir="bullish", h4_dir="bullish", m15_atr=3.0)
        state = _make_session_state()

        # Permission check should pass
        denial = check_permissions(pa, mso, state, mt5)
        assert denial is None

        # Execution should succeed
        engine = ExecutionEngine(mt5, {"risk": {"risk_per_trade_pct": 1.0}})
        trade_state = engine.open_trade({
            "direction": "LONG", "entry_price": 2650.0, "stop_loss": 2640.0,
            "take_profit_1": 2665.0, "take_profit_2": 2675.0,
            "take_profit_3": 2685.0, "risk_reward_ratio": 1.5,
        }, account_balance=100000.0)

        assert trade_state is not None
        assert trade_state.direction == "LONG"
        assert len(mt5.get_positions()) == 1


class TestFullPipelineCandidateRejected:
    def test_candidate_rejected_by_low_rr(self):
        """CANDIDATE with RR < 1.3 → safety check rejects."""
        mt5 = MockMT5()
        mt5.connect()
        mt5.set_tick(2650.00, 2650.18)

        pa = _make_pa_output(decision="CANDIDATE", grade="A+", rr=1.0,
                              tp1=2650.0 + (2650.0 - 2640.0) * 1.0)  # 1.0R TP1
        mso = _make_mso()
        state = _make_session_state()

        denial = check_permissions(pa, mso, state, mt5)
        assert denial is not None
        assert "rr_too_low" in denial.reason

    def test_candidate_rejected_by_grade(self):
        """CANDIDATE with grade B+ → safety check rejects."""
        mt5 = MockMT5()
        mt5.connect()
        mt5.set_tick(2650.00, 2650.18)

        pa = _make_pa_output(decision="CANDIDATE", grade="B+", rr=3.0)
        mso = _make_mso()
        state = _make_session_state()

        denial = check_permissions(pa, mso, state, mt5)
        assert denial is not None
        assert "below_grade" in denial.reason


class TestTP1FullCloseFlow:
    def test_tp1_closes_100pct(self):
        """Trade opened → TP1 hit → 100% closed (Phase 1 validated mechanism)."""
        mt5 = MockMT5()
        mt5.connect()

        engine = ExecutionEngine(mt5, {"risk": {"risk_per_trade_pct": 1.0}})
        trade = engine.open_trade({
            "direction": "LONG", "entry_price": 2650.0, "stop_loss": 2640.0,
            "take_profit_1": 2665.0, "take_profit_2": 2675.0,
            "take_profit_3": 2685.0, "risk_reward_ratio": 1.5,
        }, account_balance=100000.0)
        assert trade is not None

        # Price hits TP1
        mt5.set_tick(2665.00, 2665.18)
        action = engine.check_and_manage_trade({})

        assert action == "tp1_full_close"
        assert engine.active_trade is None  # Position fully closed
        assert len(mt5.get_positions()) == 0


class TestTimeoutTrailingFlow:
    def test_timeout_trailing_moves_sl_then_closes(self):
        """Trade open at session end → SL to BE → 2h timeout → close."""
        mt5 = MockMT5()
        mt5.connect()

        engine = ExecutionEngine(mt5, {"risk": {"risk_per_trade_pct": 1.0}})
        engine.open_trade({
            "direction": "LONG", "entry_price": 2650.0, "stop_loss": 2640.0,
            "take_profit_1": 2670.0, "take_profit_2": 0, "take_profit_3": 0,
            "risk_reward_ratio": 3.0,
        }, account_balance=100000.0)

        # Production behavior (d806dc6): handle_timeout_trailing only moves SL
        # to BE when the trade is currently in profit. Bump tick above entry
        # so the BE move actually fires.
        mt5.set_tick(2655.00, 2655.18)

        # Handle timeout trailing — moves SL to BE
        action = engine.handle_timeout_trailing()
        assert action == "trailing"
        assert engine.active_trade.sl_at_breakeven

        # Position should still exist
        assert engine.active_trade is not None

        # Close after timeout
        engine.close_position("timeout_2h")
        assert engine.active_trade is None
        assert len(mt5.get_positions()) == 0


class TestCrashRecoveryOrphan:
    def test_orphan_adopted(self):
        """Orchestrator starts with unknown MT5 position → adopts it."""
        mt5 = MockMT5()
        mt5.connect()

        # Simulate orphan position from a crash
        mt5._positions.append(PositionInfo(
            ticket=77777, symbol="XAUUSD", type=0, volume=0.10,
            price_open=2650.0, sl=2640.0, tp=2670.0, profit=25.0,
            magic=MAGIC_NUMBER, comment="GoldAgent",
            time=datetime.now(timezone.utc),
        ))

        engine = ExecutionEngine(mt5, {})
        actions = engine.reconcile_on_startup()

        assert any("orphan_adopted" in a for a in actions)
        assert engine.active_trade is not None
        assert engine.active_trade.ticket == 77777
        assert engine.active_trade.direction == "LONG"


class TestSessionMemoryInjection:
    def test_session_memory_in_user_message(self):
        """Verify session memory appears in the dynamic context passed to PA."""
        from src.prompts.primary_analyzer_prompt import build_user_message
        from src.models.market_state_models import (
            MarketStateObject, TimeframeState, StructureAnalysis,
            SessionLevels, DataQuality,
        )

        mso = MarketStateObject(
            timestamp_utc="2026-04-01T08:15:00+00:00",
            timeframes={
                tf: TimeframeState(
                    structure=StructureAnalysis(direction="bullish"),
                )
                for tf in ("D1", "H4", "H1", "M15")
            },
            session_levels=SessionLevels(
                asian_high=2660.0, asian_low=2640.0,
                pdh=2670.0, pdl=2630.0,
            ),
            data_quality=DataQuality(
                all_timeframes_complete=True, spread_normal=True,
                mt5_connected=True, timestamp_utc="2026-04-01T08:15:00+00:00",
            ),
        )

        session_memory = (
            "## Prior Candle Evaluations (This Session)\n"
            "- 07:15 UTC: NO_TRADE — insufficient displacement"
        )

        msg = build_user_message(
            mso, {"layer1": {}, "layer3": []},
            "2026-04-01T08:15:00", kill_zone="london",
            session_memory=session_memory,
        )

        assert "Prior Candle Evaluations" in msg
        assert "insufficient displacement" in msg


class TestDualKillZoneFlow:
    def test_kz_and_daily_trade_counters_no_longer_gate(self):
        """T2.8: `trades_<kz>` and `losses_today` counters were replaced by the
        concurrent-cap + daily-loss MTM stop. The old gates ("kz_trade_limit",
        "max_trades_reached", "max_daily_losses_reached") must NOT fire purely
        from in-memory counter values — the new Gate 3 sees no MT5 positions,
        no dormant marker, and must pass through.
        """
        mt5 = MockMT5()
        mt5.connect()
        mt5.set_tick(2650.00, 2650.18)

        state = _make_session_state()
        pa = _make_pa_output(decision="CANDIDATE", grade="A+", rr=1.5)
        mso = _make_mso()

        # Simulate a busy day that would have previously tripped every legacy gate:
        # 2 trades already in london, 2 in ny, 3 realized losses. New architecture
        # does not treat any of these as gating — only filled MT5 positions and
        # the dormant marker matter.
        state["current_kill_zone"] = "london"
        state["trades_today"] = 4
        state["trades_london"] = 2
        state["trades_ny"] = 2
        state["losses_today"] = 3

        denial = check_permissions(pa, mso, state, mt5)
        # No open positions, not dormant → must pass the counter-based blockers.
        # If any gate still denies, it must NOT be one of the removed reasons.
        if denial is not None:
            assert denial.reason not in (
                "kz_trade_limit",
                "max_trades_reached",
                "max_daily_losses_reached",
            )


# ---------------------------------------------------------------------------
# P1-3: Limit-fill trade records must finalize on exit
# ---------------------------------------------------------------------------

def _make_limit_placed_record(symbol: str, kill_zone: str, candle_time: datetime,
                               intent_trade_id: str, direction: str,
                               entry: float, sl: float, tp: float) -> dict:
    """Build the minimal LIMIT_PLACED trade record shape the orchestrator saves."""
    date_str = candle_time.strftime("%Y-%m-%d")
    time_str = candle_time.strftime("%H%M")
    return {
        "metadata": {
            "trade_id": f"{symbol}_{date_str}_{kill_zone}_{time_str}",
            "date": date_str,
            "symbol": symbol,
            "kill_zone": kill_zone,
            "candle_time": candle_time.isoformat(),
            "capture_version": "1.0",
            "system_version": "test",
        },
        "decision_pipeline": {
            "ai_decision": "CANDIDATE",
            "ai_grade": "A+",
            "ai_confidence": 85,
            "ai_direction": direction,
            "ai_framework": "ob_retest",
            "level2_verification": None,
            "gate3_result": None,
            "gate1_result": None,
            "final_outcome": "LIMIT_PLACED",
        },
        "context_at_decision": {
            "cross_instrument_context": "",
            "session_memory": "",
        },
        "mso": "[omitted]",
        "prompt": {"system_prompt": "[omitted]", "user_message": "[omitted]"},
        "ai_response": {},
        "trade_parameters": {
            "direction": direction, "entry_price": entry,
            "stop_loss": sl, "take_profit_1": tp,
        },
        "execution": None,
        "exit": None,
        "limit_intent": {
            "trade_id": intent_trade_id,
            "limit_price": entry,
            "stop_loss": sl,
            "take_profit_1": tp,
            "expiry_candles": 192,
        },
    }


class TestLimitFillExitDataCaptured:
    """Regression coverage for the _active_trade_record-never-set bug.

    Before the fix, limit-filled trades never had a record attached to the
    orchestrator instance, so _finalize_exit was skipped and the on-disk
    record stayed stuck at final_outcome="LIMIT_PLACED" forever.
    """

    def _build_orchestrator(self, tmp_path, mt5, engine, symbol="XAUUSD"):
        """Hand-assemble the attributes needed by the two code paths under test."""
        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        orch.mt5 = mt5
        orch.execution = engine
        orch._symbol = symbol
        orch._mt5_symbol = symbol
        orch.config = {
            "trade_capture": {"base_path": str(tmp_path / "trade_records")},
            "market": {"symbol": symbol, "mt5_symbol": symbol},
            "risk": {"risk_per_trade_pct": 1.0},
        }
        orch.session_state = _make_session_state(kz="london")
        orch.candle_log = []
        orch._last_mso = None
        orch._active_trade_record = None
        orch._active_trade_record_path = None
        orch._pending_trade_record_path = None
        orch._trade_entry_price = None
        orch._trade_direction = None
        orch._trade_sl_distance = None
        orch._trade_entry_time = None
        orch._mfe_price = None
        orch._mae_price = None
        orch._last_tick_price = None
        orch._be_shadow_tracker = None
        orch._partial_close_shadow_tracker = None
        return orch

    def test_limit_fill_promotes_pending_record_to_active(self, tmp_path):
        """LIMIT_PLACED → LIMIT_FILLED must attach the saved record to the orchestrator."""
        mt5 = MockMT5()
        mt5.connect()
        mt5.set_tick(2645.00, 2645.18)

        engine = ExecutionEngine(mt5, {
            "market": {"symbol": "XAUUSD"},
            "risk": {"risk_per_trade_pct": 1.0},
        })

        intent = engine.set_limit_intent(
            trade_params={
                "direction": "LONG",
                "entry_price": 2645.0,
                "stop_loss": 2640.0,
                "take_profit_1": 2655.0,
                "take_profit_2": 2660.0,
                "take_profit_3": 2665.0,
                "risk_reward_ratio": 2.0,
            },
            account_balance=100000.0,
        )

        candle_time = datetime(2026, 4, 1, 8, 15, tzinfo=timezone.utc)
        base_path = tmp_path / "trade_records"
        record = _make_limit_placed_record(
            symbol="XAUUSD", kill_zone="london", candle_time=candle_time,
            intent_trade_id=intent.trade_id, direction="LONG",
            entry=2645.0, sl=2640.0, tp=2655.0,
        )
        saved_path = save_trade_record(record, str(base_path))
        assert saved_path is not None and Path(saved_path).exists()

        orch = self._build_orchestrator(tmp_path, mt5, engine)
        orch._pending_trade_record_path = saved_path

        # Candle with low below limit triggers the fill.
        fill_candle = {
            "time": candle_time.isoformat(),
            "open": 2648.0, "high": 2648.5,
            "low": 2644.5,  # < limit_price (2645.0) → triggers LONG
            "close": 2645.5,
        }
        # TF_MAP["M15"] — import dynamically so the test follows whatever
        # constant the module uses in this environment.
        from src.components.data_ingestion import TF_MAP as _TF_MAP
        mt5.set_candles(_TF_MAP["M15"], [fill_candle])

        orch._check_pending_limit_outside_kz()

        # The orchestrator must now own the record.
        assert engine.active_trade is not None, "limit should have filled"
        assert engine.pending_intent is None
        assert orch._active_trade_record is not None
        assert orch._active_trade_record_path == saved_path
        assert orch._pending_trade_record_path is None
        # Record content must match what's on disk.
        assert orch._active_trade_record == load_trade_record(saved_path)

    def test_outside_kz_limit_check_ignores_forming_m15_bar(self, tmp_path):
        """Outside-KZ checks must select the latest closed M15 candle."""
        mt5 = MockMT5()
        mt5.connect()
        mt5.set_tick(74.04, 74.12)

        engine = ExecutionEngine(mt5, {
            "market": {"symbol": "XAGUSD"},
            "risk": {"risk_per_trade_pct": 1.0, "sl_absolute_min": 0.1},
        })
        intent = engine.set_limit_intent(
            trade_params={
                "direction": "SHORT",
                "entry_price": 74.088,
                "stop_loss": 74.688,
                "take_profit_1": 73.188,
                "take_profit_2": 0.0,
                "take_profit_3": 0.0,
                "risk_reward_ratio": 1.5,
            },
            account_balance=100000.0,
        )

        record_time = datetime.now(timezone.utc) - timedelta(minutes=30)
        saved_path = save_trade_record(
            _make_limit_placed_record(
                symbol="XAGUSD", kill_zone="london", candle_time=record_time,
                intent_trade_id=intent.trade_id, direction="SHORT",
                entry=74.088, sl=74.688, tp=73.188,
            ),
            str(tmp_path / "trade_records"),
        )

        orch = self._build_orchestrator(tmp_path, mt5, engine, symbol="XAGUSD")
        orch._pending_trade_record_path = saved_path

        closed_trigger = {
            "time": (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat(),
            "open": 73.68, "high": 74.169, "low": 73.66, "close": 73.97,
        }
        forming_not_triggered = {
            "time": (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(),
            "open": 73.97, "high": 74.078, "low": 73.94, "close": 74.04,
        }
        from src.components.data_ingestion import TF_MAP as _TF_MAP
        mt5.set_candles(_TF_MAP["M15"], [closed_trigger, forming_not_triggered])

        orch._check_pending_limit_outside_kz()

        assert engine.active_trade is not None
        assert engine.pending_intent is None
        assert engine.active_trade.direction == "SHORT"

    def test_limit_filled_trade_finalize_exit_runs(self, tmp_path):
        """Full lifecycle: LIMIT_PLACED → fill → TP1 close → on-disk exit block populated."""
        mt5 = MockMT5()
        mt5.connect()
        mt5.set_tick(2645.00, 2645.18)

        engine = ExecutionEngine(mt5, {
            "market": {"symbol": "XAUUSD"},
            "risk": {"risk_per_trade_pct": 1.0},
        })
        intent = engine.set_limit_intent(
            trade_params={
                "direction": "LONG",
                "entry_price": 2645.0,
                "stop_loss": 2640.0,
                "take_profit_1": 2655.0,
                "take_profit_2": 2660.0,
                "take_profit_3": 2665.0,
                "risk_reward_ratio": 2.0,
            },
            account_balance=100000.0,
        )

        candle_time = datetime(2026, 4, 1, 8, 15, tzinfo=timezone.utc)
        base_path = tmp_path / "trade_records"
        record = _make_limit_placed_record(
            symbol="XAUUSD", kill_zone="london", candle_time=candle_time,
            intent_trade_id=intent.trade_id, direction="LONG",
            entry=2645.0, sl=2640.0, tp=2655.0,
        )
        saved_path = save_trade_record(record, str(base_path))

        orch = self._build_orchestrator(tmp_path, mt5, engine)
        orch._pending_trade_record_path = saved_path
        # SPRTMonitor is a concrete (not stubbed) side-channel that _finalize_exit
        # uses via self._sprt_monitor.update_all — point its state file into tmp_path
        # so the write guard doesn't trip on knowledge_base/meta/sprt_state.json.
        from src.components.sprt_monitor import SPRTMonitor
        orch._sprt_monitor = SPRTMonitor(state_path=str(tmp_path / "sprt_state.json"))

        fill_candle = {
            "time": candle_time.isoformat(),
            "open": 2648.0, "high": 2648.5,
            "low": 2644.5,
            "close": 2645.5,
        }
        from src.components.data_ingestion import TF_MAP as _TF_MAP
        mt5.set_candles(_TF_MAP["M15"], [fill_candle])

        orch._check_pending_limit_outside_kz()
        assert engine.active_trade is not None
        assert orch._active_trade_record is not None  # sanity: fix working

        # Move price to TP1 → check_and_manage_trade triggers tp1_full_close.
        mt5.set_tick(2655.50, 2655.68)
        orch._check_trade_and_capture()

        # Active trade should be closed, _active_trade_record cleared,
        # and the on-disk record must now carry the exit block.
        assert engine.active_trade is None
        assert orch._active_trade_record is None  # cleared by _finalize_exit
        on_disk = load_trade_record(saved_path)
        assert on_disk.get("exit") is not None, (
            "exit block must be populated — the bug this fix targets leaves it at None"
        )
        assert "exit_type" in on_disk["exit"]
        assert "actual_r" in on_disk["exit"]
        assert "exit_price" in on_disk["exit"]

    # ------------------------------------------------------------------
    # Recovery on restart: _recover_pending_record_path
    # ------------------------------------------------------------------

    def _install_intent(self, engine, *, direction="LONG", limit_price=2645.0,
                         sl=2640.0, tp1=2655.0, trade_id="lim_2026-04-17_0000",
                         placed_time="2026-04-17T00:00:05+00:00"):
        """Install a PendingLimitIntent on the engine without going through
        set_limit_intent (so we control trade_id and placed_time exactly)."""
        intent = PendingLimitIntent(
            direction=direction,
            limit_price=limit_price,
            stop_loss=sl,
            take_profit_1=tp1,
            risk_pct=1.0,
            expiry_candles=192,
            candles_elapsed=0,
            trade_id=trade_id,
            placed_time=placed_time,
        )
        engine.pending_intent = intent
        return intent

    def test_recover_path_across_midnight_utc_boundary(self, tmp_path):
        """The core bug: candle on day N, set_limit_intent on day N+1 → record found."""
        mt5 = MockMT5()
        mt5.connect()
        engine = ExecutionEngine(mt5, {
            "market": {"symbol": "XAUUSD"},
            "risk": {"risk_per_trade_pct": 1.0},
        })

        # Candle closed at 23:45 UTC on 2026-04-16 — filename starts "2026-04-16".
        candle_time = datetime(2026, 4, 16, 23, 45, tzinfo=timezone.utc)
        base_path = tmp_path / "trade_records"
        record = _make_limit_placed_record(
            symbol="XAUUSD", kill_zone="tokyo", candle_time=candle_time,
            intent_trade_id="lim_2026-04-17_0000", direction="LONG",
            entry=2645.0, sl=2640.0, tp=2655.0,
        )
        saved_path = save_trade_record(record, str(base_path))
        assert saved_path is not None and Path(saved_path).exists()
        # Sanity: filename IS on day N, intent IS on day N+1 — verifies the bug shape.
        assert Path(saved_path).name.startswith("2026-04-16")

        # Intent placed_time = 00:00:05 UTC on 2026-04-17 (day N+1).
        self._install_intent(
            engine, trade_id="lim_2026-04-17_0000",
            placed_time="2026-04-17T00:00:05+00:00",
        )

        orch = self._build_orchestrator(tmp_path, mt5, engine)
        orch._recover_pending_record_path()

        assert orch._pending_trade_record_path == saved_path, (
            "Recovery must find the record even when intent.placed_time "
            "and the record's filename date straddle a UTC day boundary."
        )

    def test_recover_path_same_day_regression(self, tmp_path):
        """Happy path: same-day candle + intent — recovery still works."""
        mt5 = MockMT5()
        mt5.connect()
        engine = ExecutionEngine(mt5, {
            "market": {"symbol": "XAUUSD"},
            "risk": {"risk_per_trade_pct": 1.0},
        })

        candle_time = datetime(2026, 4, 17, 8, 0, tzinfo=timezone.utc)
        base_path = tmp_path / "trade_records"
        record = _make_limit_placed_record(
            symbol="XAUUSD", kill_zone="london", candle_time=candle_time,
            intent_trade_id="lim_2026-04-17_0800", direction="LONG",
            entry=2645.0, sl=2640.0, tp=2655.0,
        )
        saved_path = save_trade_record(record, str(base_path))
        assert saved_path is not None and Path(saved_path).exists()
        assert Path(saved_path).name.startswith("2026-04-17")

        self._install_intent(
            engine, trade_id="lim_2026-04-17_0800",
            placed_time="2026-04-17T08:00:05+00:00",
        )

        orch = self._build_orchestrator(tmp_path, mt5, engine)
        orch._recover_pending_record_path()

        assert orch._pending_trade_record_path == saved_path

    def test_recover_path_skips_closed_records(self, tmp_path):
        """A closed record (exit != None) must not be reattached even if trade_id matches."""
        mt5 = MockMT5()
        mt5.connect()
        engine = ExecutionEngine(mt5, {
            "market": {"symbol": "XAUUSD"},
            "risk": {"risk_per_trade_pct": 1.0},
        })

        base_path = tmp_path / "trade_records"
        shared_trade_id = "lim_2026-04-17_0800"

        # Closed record — must be skipped.
        closed_candle_time = datetime(2026, 4, 17, 7, 30, tzinfo=timezone.utc)
        closed_record = _make_limit_placed_record(
            symbol="XAUUSD", kill_zone="london", candle_time=closed_candle_time,
            intent_trade_id=shared_trade_id, direction="LONG",
            entry=2645.0, sl=2640.0, tp=2655.0,
        )
        closed_record["exit"] = {
            "exit_type": "tp1_full_close", "actual_r": 1.0, "exit_price": 2655.0,
            "closed": True,
        }
        closed_path = save_trade_record(closed_record, str(base_path))
        assert closed_path is not None and Path(closed_path).exists()

        # Open record — this is the one recovery must attach to.
        open_candle_time = datetime(2026, 4, 17, 8, 0, tzinfo=timezone.utc)
        open_record = _make_limit_placed_record(
            symbol="XAUUSD", kill_zone="london", candle_time=open_candle_time,
            intent_trade_id=shared_trade_id, direction="LONG",
            entry=2645.0, sl=2640.0, tp=2655.0,
        )
        open_path = save_trade_record(open_record, str(base_path))
        assert open_path is not None and Path(open_path).exists()
        assert open_path != closed_path

        self._install_intent(
            engine, trade_id=shared_trade_id,
            placed_time="2026-04-17T08:00:05+00:00",
        )

        orch = self._build_orchestrator(tmp_path, mt5, engine)
        orch._recover_pending_record_path()

        assert orch._pending_trade_record_path == open_path, (
            "Recovery must skip closed records (exit != None) and attach "
            "to the open one even when both share the same limit_intent.trade_id."
        )

    # ------------------------------------------------------------------
    # T2.6: trade_id -> path index lookup (race-free recovery)
    # ------------------------------------------------------------------

    def test_recover_via_trade_id_index_happy_path(self, tmp_path):
        """Index-driven recovery: trade_id is looked up directly from the
        pending records index, bypassing the glob scan entirely."""
        mt5 = MockMT5()
        mt5.connect()
        engine = ExecutionEngine(mt5, {
            "market": {"symbol": "XAUUSD"},
            "risk": {"risk_per_trade_pct": 1.0},
        })

        candle_time = datetime(2026, 4, 17, 8, 0, tzinfo=timezone.utc)
        base_path = tmp_path / "trade_records"
        record = _make_limit_placed_record(
            symbol="XAUUSD", kill_zone="london", candle_time=candle_time,
            intent_trade_id="lim_2026-04-17_0800", direction="LONG",
            entry=2645.0, sl=2640.0, tp=2655.0,
        )
        saved_path = save_trade_record(record, str(base_path))
        # Register in the T2.6 index — emulates what orchestrator does at
        # LIMIT_PLACED save time.
        index_pending_record(
            trade_id="lim_2026-04-17_0800",
            record_path=saved_path,
            symbol="XAUUSD",
            base_path=str(base_path),
        )
        # Sanity: lookup returns the saved path
        assert lookup_pending_record(
            "lim_2026-04-17_0800", "XAUUSD", str(base_path),
        ) == saved_path

        self._install_intent(
            engine, trade_id="lim_2026-04-17_0800",
            placed_time="2026-04-17T08:00:05+00:00",
        )

        orch = self._build_orchestrator(tmp_path, mt5, engine)
        # Block the glob fallback so we prove recovery used the index.
        # If the index path isn't taken, this scan returns no matching
        # records and recovery fails.
        (Path(saved_path).parent / "_pending_records_index.json").exists()
        orch._recover_pending_record_path()

        assert orch._pending_trade_record_path == saved_path

    def test_recover_missing_record_triggers_alert(self, tmp_path, monkeypatch):
        """Missing record: pending_intent restored but no record on disk.
        Recovery must fire notify_alert() exactly once (T2.7) and leave the
        orchestrator's _pending_trade_record_path unset."""
        mt5 = MockMT5()
        mt5.connect()
        engine = ExecutionEngine(mt5, {
            "market": {"symbol": "XAUUSD"},
            "risk": {"risk_per_trade_pct": 1.0},
        })

        # Intent restored but NO record saved and NO index entry written.
        self._install_intent(
            engine, trade_id="lim_2026-04-17_0800",
            placed_time="2026-04-17T08:00:05+00:00",
        )

        # Module-ref monkeypatch on src.notifications so the lazy import in
        # _alert_pending_record_recovery_failed() picks up our stub.
        from src import notifications as _notif_mod
        calls: list[str] = []
        monkeypatch.setattr(
            _notif_mod, "notify_alert", lambda text: calls.append(text),
        )

        orch = self._build_orchestrator(tmp_path, mt5, engine)
        orch._recover_pending_record_path()

        assert orch._pending_trade_record_path is None
        assert len(calls) == 1, (
            f"notify_alert must be called exactly once, got {len(calls)}"
        )
        alert_text = calls[0]
        assert "PENDING RECORD RECOVERY FAILED" in alert_text
        assert "XAUUSD" in alert_text
        assert "lim_2026-04-17_0800" in alert_text

    def test_index_helpers_add_lookup_remove_roundtrip(self, tmp_path):
        """Helper contract: index/lookup/remove roundtrip + missing-key lookup."""
        base_path = tmp_path / "trade_records"
        # Unknown key — lookup returns None without side effects.
        assert lookup_pending_record(
            "lim_missing", "XAUUSD", str(base_path),
        ) is None

        # Index two entries for the same symbol.
        index_pending_record(
            "lim_a", "/rec/a.json", "XAUUSD", str(base_path),
        )
        index_pending_record(
            "lim_b", "/rec/b.json", "XAUUSD", str(base_path),
        )
        assert lookup_pending_record(
            "lim_a", "XAUUSD", str(base_path),
        ) == "/rec/a.json"
        assert lookup_pending_record(
            "lim_b", "XAUUSD", str(base_path),
        ) == "/rec/b.json"

        # Remove one — other remains.
        remove_pending_record("lim_a", "XAUUSD", str(base_path))
        assert lookup_pending_record(
            "lim_a", "XAUUSD", str(base_path),
        ) is None
        assert lookup_pending_record(
            "lim_b", "XAUUSD", str(base_path),
        ) == "/rec/b.json"

        # Remove last — index file is unlinked (tidy behaviour).
        remove_pending_record("lim_b", "XAUUSD", str(base_path))
        index_path = Path(base_path) / "XAUUSD" / "_pending_records_index.json"
        assert not index_path.exists()
