"""Tests for the 2026-04-02 bug fixes:
1. File versioning utility
2. TP1 placement validation (prompt + safety check)
3. Outcome simulation exit_substate labeling
4. CANDIDATE with null trade_parameters guard
"""

import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

# Ensure project root on path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.utils.file_versioning import get_versioned_path
from src.models.analysis_models import (
    PrimaryAnalysisOutput,
    PrimaryAnalysisReasoning,
    DailyBiasAnalysis,
    H4AlignmentAnalysis,
    H1SetupAnalysis,
    LiquiditySweepAnalysis,
    M15ConfirmationAnalysis,
    TradeParameters,
)
from src.components.primary_analyzer import guard_candidate_null_params, _warn_tp1_placement
from src.components.permissions import check_permissions, ExecutionDenial
from scripts.backtest_runner import evaluate_hypothetical_outcome


# ═══════════════════════════════════════════════════════════════════════
# File versioning tests
# ═══════════════════════════════════════════════════════════════════════

class TestFileVersioning:
    def test_returns_timestamped_path(self, tmp_path):
        ts = datetime(2026, 4, 2, 17, 30, tzinfo=timezone.utc)
        p = get_versioned_path(tmp_path, "report", ".md", timestamp=ts)
        assert p.name == "report_0_1730.md"
        assert p.parent == tmp_path

    def test_creates_directory_if_missing(self, tmp_path):
        subdir = tmp_path / "new_subdir"
        ts = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
        p = get_versioned_path(subdir, "test", ".json", timestamp=ts)
        assert subdir.exists()
        assert p.parent == subdir

    def test_no_overwrite(self, tmp_path):
        ts = datetime(2026, 4, 2, 17, 30, tzinfo=timezone.utc)
        # Create the first file
        p1 = get_versioned_path(tmp_path, "report", ".md", timestamp=ts)
        p1.touch()
        # Second call should return _2 suffix
        p2 = get_versioned_path(tmp_path, "report", ".md", timestamp=ts)
        assert p2.name == "report_0_1730_2.md"
        assert p2 != p1

    def test_increments_suffix(self, tmp_path):
        ts = datetime(2026, 4, 2, 17, 30, tzinfo=timezone.utc)
        for i in range(3):
            p = get_versioned_path(tmp_path, "report", ".md", timestamp=ts)
            p.touch()
        # 4th call
        p4 = get_versioned_path(tmp_path, "report", ".md", timestamp=ts)
        assert p4.name == "report_0_1730_4.md"


# ═══════════════════════════════════════════════════════════════════════
# TP1 placement validation tests
# ═══════════════════════════════════════════════════════════════════════

def _make_tp(direction="LONG", entry=3023.0, sl=2982.0, tp1=3125.0, rr=2.5):
    return TradeParameters(
        direction=direction, entry_price=entry, stop_loss=sl,
        take_profit_1=tp1, take_profit_2=tp1 + 20, take_profit_3=tp1 + 50,
        risk_reward_ratio=rr,
    )


def _make_pa(tp=None, grade="A", direction="LONG", daily_bias="bullish"):
    return PrimaryAnalysisOutput(
        timestamp_utc="2026-01-01T07:15:00Z",
        model_used="test",
        decision="CANDIDATE" if tp else "NO_TRADE",
        confidence_score=80,
        framework="ob_retest",
        reasoning=PrimaryAnalysisReasoning(
            daily_bias=DailyBiasAnalysis(direction=daily_bias, confidence="high"),
            h4_alignment=H4AlignmentAnalysis(aligned=True),
            h1_setup=H1SetupAnalysis(poi_identified=True),
            liquidity_sweep=LiquiditySweepAnalysis(detected=False),
            m15_confirmation=M15ConfirmationAnalysis(choch_detected=True),
            setup_grade=grade,
        ),
        trade_parameters=tp,
    )


class _MockMSO:
    """Minimal MSO stub for permissions checks."""
    class _TF:
        atr_14 = 10.0
    timeframes = {"M15": _TF()}


class _MockMT5:
    class _Tick:
        spread_cents = 10
    def is_connected(self):
        return True
    def get_tick(self, _):
        return self._Tick()


class TestTP1SafetyCheck:
    """Gate 1 should reject TP1 that is too close or on wrong side."""

    def _run_check(self, tp_params, grade="A", daily_bias="bullish"):
        pa = _make_pa(tp=tp_params, grade=grade, direction=tp_params.direction,
                      daily_bias=daily_bias)
        mso = _MockMSO()
        session = {"trades_today": 0, "current_kill_zone": "london",
                   "trades_london": 0, "losses_today": 0}
        mt5 = _MockMT5()
        return check_permissions(pa, mso, session, mt5)

    def test_tp1_correct_passes(self):
        # TP1 at 1.5R — should pass (within 1.3R-2.0R band)
        tp = _make_tp(entry=3000, sl=2960, tp1=3060, rr=1.5)  # 40 risk, 60 tp1 dist = 1.5R
        denial = self._run_check(tp)
        assert denial is None

    def test_tp1_too_close_rejected(self):
        # TP1 at 0.17R — should be rejected
        tp = _make_tp(entry=3023, sl=2982, tp1=3030, rr=2.5)  # 41 risk, 7 tp1 dist = 0.17R
        denial = self._run_check(tp)
        assert denial is not None
        assert "tp1_too_close" in denial.reason

    def test_tp1_below_entry_long_rejected_by_default(self, monkeypatch):
        # TP1 below entry for LONG is rejected by default. The WF1 inverted
        # TP analysis found corrected inverted candidates averaged -0.325R.
        import src.components.permissions as _perm_mod
        monkeypatch.setattr(_perm_mod, "_log_inverted_tp", lambda *args, **kwargs: None)
        # Original: entry=3031.59, sl=3000.68 (correct side), tp1=3031.00 (below entry).
        tp = _make_tp(direction="LONG", entry=3031.59, sl=3000.68, tp1=3031.00, rr=2.5)
        denial = self._run_check(tp)
        assert denial is not None
        assert denial.reason == "inverted_tp_sl_blocked_negative_expectancy"
        assert tp.take_profit_1 == 3031.00

    def test_tp1_above_entry_short_rejected_by_default(self, monkeypatch):
        # TP1 above entry for SHORT is rejected by default. Auto-correction is
        # now only an explicit rollback policy, not live default behavior.
        import src.components.permissions as _perm_mod
        monkeypatch.setattr(_perm_mod, "_log_inverted_tp", lambda *args, **kwargs: None)
        # Original: entry=3000, sl=3040 (wrong side for SHORT), tp1=3010 (wrong side).
        tp = _make_tp(direction="SHORT", entry=3000, sl=3040, tp1=3010, rr=2.5)
        denial = self._run_check(tp, daily_bias="bearish")
        assert denial is not None
        assert denial.reason == "inverted_tp_sl_blocked_negative_expectancy"
        assert tp.take_profit_1 == 3010
        assert tp.stop_loss == 3040

    def test_tp1_at_2r_passes(self):
        # TP1 at exactly 2.0R — should pass (minimum threshold)
        tp = _make_tp(entry=3000, sl=2960, tp1=3080, rr=2.5)  # 40 risk, 80 dist = 2.0R
        denial = self._run_check(tp)
        assert denial is None


# ═══════════════════════════════════════════════════════════════════════
# Outcome simulation tests
# ═══════════════════════════════════════════════════════════════════════

def _make_candles(prices, start_time="2025-03-18 14:00:00"):
    """Generate fake M15 candles from a list of (open, high, low, close)."""
    candles = []
    for i, (o, h, l, c) in enumerate(prices):
        minute = (i + 1) * 15
        hour = 14 + minute // 60
        mins = minute % 60
        candles.append({
            "time": f"2025-03-18 {hour:02d}:{mins:02d}:00",
            "open": o, "high": h, "low": l, "close": c,
        })
    return candles


class TestOutcomeSimulation:
    def test_sl_hit_uses_candle_low_for_long(self):
        tp = TradeParameters(
            direction="LONG", entry_price=3000, stop_loss=2960,
            take_profit_1=3100, risk_reward_ratio=2.5,
        )
        # Candle low touches SL
        candles = _make_candles([(2990, 2995, 2959, 2970)])
        result = evaluate_hypothetical_outcome(tp, candles)
        assert result["outcome"] == "LOSS"
        assert result["r_multiple"] == -1.0
        assert result["exit_substate"] == "CLOSED_SL"

    def test_tp1_hit_uses_candle_high_for_long(self):
        tp = TradeParameters(
            direction="LONG", entry_price=3000, stop_loss=2960,
            take_profit_1=3100, risk_reward_ratio=2.5,
        )
        # Candle high reaches TP1 (high >= 3100), low doesn't touch SL
        candles = _make_candles([
            (3010, 3020, 3005, 3015),   # candle 1: no hit
            (3015, 3105, 3010, 3090),   # candle 2: TP1 hit (high=3105 >= 3100)
            (3090, 3095, 3080, 3085),   # candle 3: remainder still open
        ])
        result = evaluate_hypothetical_outcome(tp, candles)
        # TP1 hit: 50% closed at 2.5R, remaining 50% timeout
        assert result["r_multiple"] > 0
        # Events should include PARTIAL_TP1
        tp1_events = [e for e in result["events"] if e["type"] == "PARTIAL_TP1"]
        assert len(tp1_events) == 1

    def test_tp1_then_timeout_label(self):
        tp = TradeParameters(
            direction="LONG", entry_price=3000, stop_loss=2960,
            take_profit_1=3100, risk_reward_ratio=2.5,
        )
        candles = _make_candles([
            (3010, 3110, 3005, 3090),   # TP1 hit
            (3090, 3095, 3080, 3085),   # no further TP, no SL
        ])
        result = evaluate_hypothetical_outcome(tp, candles)
        assert result["exit_substate"] == "CLOSED_TP1_THEN_TIMEOUT"

    def test_pure_timeout_label(self):
        tp = TradeParameters(
            direction="LONG", entry_price=3000, stop_loss=2960,
            take_profit_1=3100, risk_reward_ratio=2.5,
        )
        candles = _make_candles([
            (3005, 3010, 2995, 3008),   # no hit
            (3008, 3015, 3000, 3010),   # no hit
        ])
        result = evaluate_hypothetical_outcome(tp, candles)
        assert result["exit_substate"] == "CLOSED_SESSION_TIMEOUT"

    def test_sl_priority_over_tp_same_candle(self):
        """When both SL and TP1 could be hit on same candle, SL wins."""
        tp = TradeParameters(
            direction="LONG", entry_price=3000, stop_loss=2960,
            take_profit_1=3100, risk_reward_ratio=2.5,
        )
        # Candle spans both SL and TP1
        candles = _make_candles([(2990, 3110, 2950, 3050)])
        result = evaluate_hypothetical_outcome(tp, candles)
        # SL checked first → LOSS
        assert result["outcome"] == "LOSS"
        assert result["exit_substate"] == "CLOSED_SL"

    def test_short_trade_tp1_detection(self):
        tp = TradeParameters(
            direction="SHORT", entry_price=3000, stop_loss=3040,
            take_profit_1=2900, risk_reward_ratio=2.5,
        )
        # Candle low reaches TP1 (low <= 2900)
        candles = _make_candles([
            (2990, 3010, 2895, 2920),   # TP1 hit (low=2895 <= 2900)
            (2920, 2930, 2910, 2925),   # remainder
        ])
        result = evaluate_hypothetical_outcome(tp, candles)
        tp1_events = [e for e in result["events"] if e["type"] == "PARTIAL_TP1"]
        assert len(tp1_events) == 1
        assert result["exit_substate"] == "CLOSED_TP1_THEN_TIMEOUT"

    def test_partial_close_math(self):
        """TP1 hit → 50% closed at TP1 R, remaining 50% tracked separately."""
        tp = TradeParameters(
            direction="LONG", entry_price=3000, stop_loss=2960,
            take_profit_1=3100, risk_reward_ratio=2.5,
        )
        # TP1 at 2.5R, then timeout at entry level
        candles = _make_candles([
            (3010, 3110, 3005, 3090),   # TP1 hit at 3100
            (3090, 3095, 2995, 3000),   # timeout, close at 3000 (entry level)
        ])
        result = evaluate_hypothetical_outcome(tp, candles)
        # 50% closed at 2.5R = +1.25R
        # 50% timeout at entry = 0R
        # Total = +1.25R
        assert abs(result["r_multiple"] - 1.25) < 0.05

    def test_replay_trade4_reproduction(self):
        """Reproduce Trade #4 from replay blitz: entry=3023.17, SL=2982.05, TP1=3030.00.
        TP1 is at 0.17R. The simulation SHOULD detect TP1 hit on candle high."""
        tp = TradeParameters(
            direction="LONG", entry_price=3023.17, stop_loss=2982.05,
            take_profit_1=3030.00, risk_reward_ratio=2.5,
        )
        # Simulate: price rises to 3032 on candle high
        candles = _make_candles([
            (3024, 3028, 3020, 3025),   # no hit (high 3028 < tp1 3030)
            (3025, 3032, 3022, 3030),   # TP1 hit (high 3032 >= 3030)
            (3030, 3035, 3025, 3032),   # remainder
        ])
        result = evaluate_hypothetical_outcome(tp, candles)
        tp1_events = [e for e in result["events"] if e["type"] == "PARTIAL_TP1"]
        assert len(tp1_events) == 1, "TP1 should be detected"
        assert result["exit_substate"] == "CLOSED_TP1_THEN_TIMEOUT"


# ═══════════════════════════════════════════════════════════════════════
# Null trade_parameters guard tests
# ═══════════════════════════════════════════════════════════════════════

class TestNullTradeParamsGuard:
    def test_candidate_with_null_params_demoted(self):
        result = PrimaryAnalysisOutput(
            timestamp_utc="2026-01-01T07:15:00Z",
            model_used="test",
            decision="CANDIDATE",
            confidence_score=80,
            framework="ob_retest",
            reasoning=PrimaryAnalysisReasoning(
                daily_bias=DailyBiasAnalysis(direction="bullish", confidence="high"),
                h4_alignment=H4AlignmentAnalysis(aligned=True),
                h1_setup=H1SetupAnalysis(poi_identified=True),
                liquidity_sweep=LiquiditySweepAnalysis(detected=False),
                m15_confirmation=M15ConfirmationAnalysis(choch_detected=True),
                setup_grade="A",
            ),
            trade_parameters=None,
        )
        guarded = guard_candidate_null_params(result)
        assert guarded.decision == "NO_TRADE"
        assert guarded.no_trade_reason == "ai_output_malformed"
        assert "[SYSTEM: Demoted" in guarded.reasoning.overall_reasoning

    def test_candidate_with_valid_params_unchanged(self):
        tp = _make_tp()
        result = _make_pa(tp=tp)
        guarded = guard_candidate_null_params(result)
        assert guarded.decision == "CANDIDATE"
        assert guarded.trade_parameters is not None

    def test_no_trade_unchanged(self):
        result = _make_pa(tp=None)
        result.decision = "NO_TRADE"
        guarded = guard_candidate_null_params(result)
        assert guarded.decision == "NO_TRADE"


# ═══════════════════════════════════════════════════════════════════════
# 2026-04-23 Thursday live-audit bug fixes
# ═══════════════════════════════════════════════════════════════════════

class TestLimitFillNoNameError:
    """Bug 1 (P0) — ``kz_trades`` NameError on every limit-order fill.

    Thursday 2026-04-23 live trading produced two limit fills (USDJPY 09:00
    UTC + GBPJPY 13:16 UTC). Both hit NameError at
    ``orchestrator.py:492`` because T2.8 (commit ``dc4cec2``) removed the
    ``kz_trades`` binding at the top of ``_process_candle`` but left a stale
    ``kz_trades + 1`` reference inside the pending-fill branch. When the
    NameError fires inside the ``if trade_state:`` block, the Telegram
    ``notify_limit_filled``, ``_promote_pending_record_on_fill``, and
    ``_init_trade_tracking`` callbacks never run.

    Regression test: synthesize a pending-limit fill and assert the per-KZ
    counter increments without raising and the downstream callbacks fire.
    """

    def _make_orch(self, trade_state_to_return, *, kz_key_preseed=None):
        """Construct a minimal orchestrator for the pending-fill path.

        We skip ``__init__`` and wire only the attributes that ``_process_candle``
        touches on the limit-fill branch. ``_update_daily_pnl`` is stubbed out
        so the test doesn't need a live MT5 seam; ``_check_and_trigger_daily_loss_stop``
        is stubbed to return False (no dormant trip).
        """
        from unittest.mock import MagicMock
        from src.components.orchestrator import SessionOrchestrator

        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        orch._symbol = "USDJPY"
        orch._mt5_symbol = "USDJPY"
        orch.config = {"risk": {"max_portfolio_drawdown_pct": 4.0,
                                "max_consecutive_losses": 5}}
        orch.candle_log = []
        orch.session_state = {
            "date": "2026-04-23",
            "trades_today": 0,
            "daily_pnl_pct": 0.0,
            "portfolio_drawdown_pct": 0.0,
            "consecutive_losses": 0,
            "losses_today": 0,
            "current_kill_zone": "london",
            "trades_london": 0,
            "trades_ny": 0,
        }
        if kz_key_preseed is not None:
            orch.session_state["trades_london"] = kz_key_preseed
        orch._pending_trade_record_path = None
        orch._active_trade_record = None
        orch._active_trade_record_path = None
        orch.mt5 = MagicMock()
        orch.mt5.get_tick.return_value = None

        # Execution with pending_intent + check_limit_fill returning TradeState
        orch.execution = MagicMock()
        intent = MagicMock()
        intent.trade_id = "lim_2026-04-23_0900"
        orch.execution.pending_intent = intent
        orch.execution.check_limit_fill.return_value = trade_state_to_return

        # Stubs for methods that touch KB / disk / MT5
        orch._update_daily_pnl = MagicMock()
        orch._check_and_trigger_daily_loss_stop = MagicMock(return_value=False)
        orch._should_skip_first_ny_candle = MagicMock(return_value=False)
        orch._write_chart_signal = MagicMock()
        orch._init_trade_tracking = MagicMock()
        orch._promote_pending_record_on_fill = MagicMock()

        return orch

    def _make_trade_state(self):
        from src.components.execution import TradeState
        return TradeState(
            ticket=123456,
            direction="LONG",
            entry_price=149.75,
            stop_loss=149.50,
            take_profit_1=150.25,
            take_profit_2=150.50,
            take_profit_3=150.75,
            initial_volume=0.1,
            current_volume=0.1,
            sl_distance=0.25,
            trade_id="lim_2026-04-23_0900",
            entry_time="2026-04-23T09:00:00+00:00",
        )

    def test_limit_fill_does_not_raise_name_error(self, monkeypatch):
        """Drive the exact limit-fill branch that failed Thursday — assert
        no NameError and downstream callbacks fire."""
        from unittest.mock import MagicMock
        from src.components import orchestrator as _orch_mod
        from src.components import data_ingestion as _di_mod

        ts = self._make_trade_state()
        orch = self._make_orch(ts)

        # Patch data ingestion to return a candle payload
        fake_candle = {"time": "2026-04-23T09:00:00+00:00", "open": 149.80,
                       "high": 149.85, "low": 149.70, "close": 149.76}
        monkeypatch.setattr(
            _orch_mod, "ingest_live_data",
            lambda mt5, config: {"candles": {"M15": [fake_candle]}},
        )
        # Neutralize the Telegram notify call so the test doesn't hit the
        # network. Record it so we can assert it fired.
        notify_mock = MagicMock()
        monkeypatch.setattr(_orch_mod, "notify_limit_filled", notify_mock)

        # Should NOT raise NameError
        orch._process_candle("london")

        # Per-KZ counter incremented
        assert orch.session_state["trades_london"] == 1
        assert orch.session_state["trades_today"] == 1
        # LIMIT_FILLED candle logged
        assert any(e["decision"] == "LIMIT_FILLED" for e in orch.candle_log)
        # Downstream callbacks fired (all three were blocked when NameError
        # escaped — this is what caused the forensic symptom Thursday)
        notify_mock.assert_called_once()
        orch._promote_pending_record_on_fill.assert_called_once()
        orch._init_trade_tracking.assert_called_once_with(ts)

    def test_limit_fill_preserves_preexisting_counter(self, monkeypatch):
        """If the per-KZ counter was already non-zero (e.g., restart after
        earlier fill), the new fill should add 1 — not overwrite."""
        from unittest.mock import MagicMock
        from src.components import orchestrator as _orch_mod

        ts = self._make_trade_state()
        orch = self._make_orch(ts, kz_key_preseed=2)
        # This regression isolates the counter increment. The current runtime
        # emergency stop blocks the third same-KZ trade by default, so disable
        # that unrelated cap in this narrow fixture.
        orch.config["risk"]["max_trades_per_kill_zone_enabled"] = False

        fake_candle = {"time": "2026-04-23T09:00:00+00:00", "open": 149.80,
                       "high": 149.85, "low": 149.70, "close": 149.76}
        monkeypatch.setattr(
            _orch_mod, "ingest_live_data",
            lambda mt5, config: {"candles": {"M15": [fake_candle]}},
        )
        monkeypatch.setattr(_orch_mod, "notify_limit_filled", MagicMock())

        orch._process_candle("london")

        # 2 + 1 = 3 (would have been stale `kz_trades + 1 = 0 + 1 = 1` pre-fix)
        assert orch.session_state["trades_london"] == 3

    def test_pending_limit_checks_latest_closed_m15_not_forming_bar(self, monkeypatch):
        """Inside-KZ pending-limit polling must not inspect MT5's forming M15.

        MT5 can expose the new in-progress bar at index [-1] immediately after
        an M15 close. Pending fills must be checked against the latest closed
        candle, otherwise a valid touch in the just-closed candle can be missed.
        """
        from src.components import orchestrator as _orch_mod

        orch = self._make_orch(None)

        now = datetime.now(timezone.utc)
        forming_open = now.replace(
            minute=(now.minute // 15) * 15,
            second=0,
            microsecond=0,
        )
        closed_open = forming_open - timedelta(minutes=15)
        older_open = forming_open - timedelta(minutes=30)

        older_candle = {
            "time": older_open.isoformat(),
            "open": 149.90,
            "high": 149.95,
            "low": 149.80,
            "close": 149.85,
        }
        closed_candle = {
            "time": closed_open.isoformat(),
            "open": 149.85,
            "high": 149.88,
            "low": 149.70,
            "close": 149.76,
        }
        forming_candle = {
            "time": forming_open.isoformat(),
            "open": 149.76,
            "high": 149.77,
            "low": 149.76,
            "close": 149.76,
        }

        monkeypatch.setattr(
            _orch_mod, "ingest_live_data",
            lambda mt5, config: {
                "candles": {"M15": [older_candle, closed_candle, forming_candle]},
            },
        )

        orch._process_candle("london")

        orch.execution.check_limit_fill.assert_called_once()
        called_candle = orch.execution.check_limit_fill.call_args.args[0]
        telemetry = orch.execution.check_limit_fill.call_args.kwargs["telemetry_context"]
        assert called_candle is closed_candle
        assert telemetry["latest_m15_time_utc"] == closed_candle["time"]
        assert telemetry["raw_data_latest_m15_time_utc"] == forming_candle["time"]


class TestSessionStatePersistenceAcrossBootstrap:
    """Bug 2 (P1) — ``_new_day`` auto-cancels pending limits on every bootstrap.

    Before fix: ``session_state["date"]`` initialized to None in __init__;
    first tick of _main_loop compared to current UTC date → treated as
    "new day" → all pending limits cancelled. Thursday USDJPY had
    ``lim_2026-04-22_1515`` cancelled at 2026-04-23 07:46:07 with reason
    "new_day" even though no real date rollover had occurred at that
    bootstrap (bootstrap was at 07:46 UTC, the lim was from the previous
    day's 15:15 — actual day rollover already handled by prior process).

    Fix: persist session_state["date"] per-symbol to pipeline_state/
    session_state_<SYMBOL>.json. _bootstrap loads it; _new_day writes it.
    A mid-day restart reads today's date → skips _new_day → limits
    preserved. A bootstrap across a real UTC boundary still fires
    _new_day because persisted date < today.
    """

    @pytest.fixture(autouse=True)
    def _isolate_state_dir(self, tmp_path, monkeypatch):
        """Redirect SESSION_STATE_DIR to tmp_path so tests never touch
        pipeline_state/ on the real filesystem."""
        from src.components import orchestrator as _orch_mod
        state_dir = tmp_path / "pipeline_state"
        state_dir.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr(_orch_mod, "SESSION_STATE_DIR", state_dir)
        self.state_dir = state_dir
        self.orch_mod = _orch_mod
        yield

    def test_load_persisted_date_none_when_missing(self):
        """First-ever boot (no file on disk) → None, which falls back to
        'new day' behavior (safe default, matches pre-persistence)."""
        result = self.orch_mod._load_persisted_session_date("USDJPY")
        assert result is None

    def test_persist_and_load_roundtrip(self):
        self.orch_mod._persist_session_date("USDJPY", "2026-04-23")
        result = self.orch_mod._load_persisted_session_date("USDJPY")
        assert result == "2026-04-23"

    def test_per_symbol_isolation(self):
        """Two symbols on the same machine must not overwrite each other's
        persisted state."""
        self.orch_mod._persist_session_date("USDJPY", "2026-04-23")
        self.orch_mod._persist_session_date("XAUUSD", "2026-04-22")
        assert self.orch_mod._load_persisted_session_date("USDJPY") == "2026-04-23"
        assert self.orch_mod._load_persisted_session_date("XAUUSD") == "2026-04-22"

    def test_malformed_file_treated_as_absent(self):
        """A corrupt state file must NOT crash — fall back to None so
        _new_day fires (safe default)."""
        path = self.state_dir / "session_state_USDJPY.json"
        path.write_text("{not valid json", encoding="utf-8")
        assert self.orch_mod._load_persisted_session_date("USDJPY") is None

    def test_bootstrap_loads_same_day_date_prevents_new_day(self):
        """Mid-day restart: persisted date == today → session_state["date"]
        matches today → _main_loop's ``if session_state["date"] != today``
        is False → _new_day does NOT fire → pending limits preserved.

        This is the scenario that broke Thursday USDJPY's
        lim_2026-04-22_1515 limit.
        """
        from unittest.mock import MagicMock
        from src.components.orchestrator import SessionOrchestrator

        # Simulate prior process persisted today's date
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self.orch_mod._persist_session_date("USDJPY", today)

        # Minimal orchestrator that exercises the bootstrap restore path
        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        orch._symbol = "USDJPY"
        orch.session_state = {"date": None, "trades_today": 0}

        # Exercise just the restore snippet from _bootstrap
        persisted = self.orch_mod._load_persisted_session_date(orch._symbol)
        assert persisted == today
        if persisted:
            orch.session_state["date"] = persisted

        # Now simulate first _main_loop tick check
        assert orch.session_state["date"] == today
        # In _main_loop: ``if self.session_state["date"] != today`` → False
        # → _new_day would NOT be called
        would_fire_new_day = orch.session_state["date"] != today
        assert would_fire_new_day is False

    def test_bootstrap_across_midnight_still_fires_new_day(self):
        """Real UTC date rollover: persisted date was yesterday → restore
        sets session_state["date"] to yesterday → first tick today sees
        mismatch → _new_day fires and cancels pending limits (the correct
        behavior — the limit's analysis is stale)."""
        from src.components.orchestrator import SessionOrchestrator

        # Simulate prior process persisted yesterday's date
        today = datetime.now(timezone.utc)
        yesterday = (today - timedelta(days=1)).strftime("%Y-%m-%d")
        today_str = today.strftime("%Y-%m-%d")
        self.orch_mod._persist_session_date("USDJPY", yesterday)

        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        orch._symbol = "USDJPY"
        orch.session_state = {"date": None, "trades_today": 0}

        persisted = self.orch_mod._load_persisted_session_date(orch._symbol)
        assert persisted == yesterday
        orch.session_state["date"] = persisted

        # First _main_loop tick check
        would_fire_new_day = orch.session_state["date"] != today_str
        assert would_fire_new_day is True  # legitimate rollover

    def test_new_day_writes_persisted_date(self):
        """_new_day must persist the new date so the NEXT bootstrap sees it."""
        from unittest.mock import MagicMock
        from types import SimpleNamespace
        from src.components.orchestrator import SessionOrchestrator

        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        orch._symbol = "USDJPY"
        orch.session_state = {"date": None, "trades_today": 0}
        orch.session_memory = []
        orch.candle_log = []
        orch._kz_windows = {
            "london": {"start_min": 420, "end_min": 570,
                       "core_end_min": 570, "crosses_midnight": False},
            "ny": {"start_min": 780, "end_min": 930,
                   "core_end_min": 930, "crosses_midnight": False},
        }
        orch._ci_context_text = ""
        orch.execution = SimpleNamespace(pending_intent=None)
        orch.mt5 = SimpleNamespace(
            get_account_balance=lambda: 100000.0,
            get_account_equity=lambda: 100000.0,
        )

        orch._new_day("2026-04-23")

        assert self.orch_mod._load_persisted_session_date("USDJPY") == "2026-04-23"

    def test_new_day_persistence_failure_does_not_crash(self, monkeypatch):
        """If the persistence write fails, _new_day MUST NOT raise — on
        next boot the absent/bad file falls back to 'new day' (safe)."""
        from types import SimpleNamespace
        from src.components.orchestrator import SessionOrchestrator

        def boom(*_args, **_kwargs):
            raise OSError("disk full simulation")

        # Patch atomic_write (used by _persist_session_date) — module-ref
        monkeypatch.setattr(self.orch_mod, "atomic_write", boom)

        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        orch._symbol = "USDJPY"
        orch.session_state = {"date": None, "trades_today": 0}
        orch.session_memory = []
        orch.candle_log = []
        orch._kz_windows = {
            "london": {"start_min": 420, "end_min": 570,
                       "core_end_min": 570, "crosses_midnight": False},
            "ny": {"start_min": 780, "end_min": 930,
                   "core_end_min": 930, "crosses_midnight": False},
        }
        orch._ci_context_text = ""
        orch.execution = SimpleNamespace(pending_intent=None)
        orch.mt5 = SimpleNamespace(
            get_account_balance=lambda: 100000.0,
            get_account_equity=lambda: 100000.0,
        )

        # Should not raise even though atomic_write blows up inside
        # _persist_session_date
        orch._new_day("2026-04-23")


class TestApiCallsMadeExclusions:
    """Bug 3 (P3) — ``api_calls_made`` session-summary counter over-reports.

    Thursday 2026-04-23 session summaries reported api_calls_made=7
    (XAUUSD) and 30 (GBPUSD) when actual API calls were 0. Cause: the
    ``_save_session_summary`` detail-prefix filter excluded
    ``pre_screen:`` and ``deterministic_no_bias:`` but NOT
    ``pre_ai_gate:`` (the H1 POI availability gate shipped 2026-04-20
    that emits NO_TRADE with that prefix BEFORE the AI call). Also
    missing: ``SKIP_DORMANT`` decision (T2.8 daily-loss stop gate fires
    before any API call).

    Regression test: synthesize a candle_log with pre_ai_gate + dormant
    + other pre-API skips; assert api_calls_made counts only the rows
    where an API call truly happened.
    """

    def _make_orch(self, tmp_path, monkeypatch):
        from unittest.mock import MagicMock
        from src.components import orchestrator as _orch_mod
        from src.components.orchestrator import SessionOrchestrator

        # Redirect session summary writes to tmp_path
        summary_root = tmp_path / "knowledge_base" / "live_sessions"
        summary_root.mkdir(parents=True, exist_ok=True)

        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        orch._symbol = "GBPUSD"
        orch.session_state = {"date": "2026-04-23"}
        orch.session_memory = []
        orch._last_mso = None
        orch._london_start = (7, 0)
        orch._london_core_end = (9, 30)
        orch._ny_start = (13, 0)
        orch._ny_end = (15, 30)

        # Patch _write_session_summary_file to capture the summary dict
        captured = {}
        def capture(_date, _kz, summary):
            captured["summary"] = summary
        orch._write_session_summary_file = capture
        return orch, captured

    def test_pre_ai_gate_skips_not_counted_as_api_calls(self, tmp_path, monkeypatch):
        orch, captured = self._make_orch(tmp_path, monkeypatch)
        # 30 pre_ai_gate skips (the GBPUSD Thursday scenario) + 0 real API calls
        orch.candle_log = [
            {"time": f"2026-04-23T07:{15+i:02d}:00Z", "kill_zone": "london",
             "decision": "NO_TRADE",
             "detail": "pre_ai_gate:no_unmitigated_h1_pois"}
            for i in range(30)
        ]

        orch._save_session_summary("london")

        assert captured["summary"]["api_calls_made"] == 0, (
            f"Expected 0 API calls (all 30 were pre-AI-gate skips), "
            f"got {captured['summary']['api_calls_made']}"
        )

    def test_dormant_skip_not_counted_as_api_call(self, tmp_path, monkeypatch):
        orch, captured = self._make_orch(tmp_path, monkeypatch)
        orch.candle_log = [
            {"time": "2026-04-23T07:15:00Z", "kill_zone": "london",
             "decision": "SKIP_DORMANT",
             "detail": "daily_loss_stop active — no AI call until 00:00 UTC"},
            {"time": "2026-04-23T07:30:00Z", "kill_zone": "london",
             "decision": "SKIP_DORMANT",
             "detail": "daily_loss_stop active — no AI call until 00:00 UTC"},
        ]

        orch._save_session_summary("london")

        assert captured["summary"]["api_calls_made"] == 0

    def test_mixed_skips_and_real_calls_counted_correctly(
        self, tmp_path, monkeypatch
    ):
        orch, captured = self._make_orch(tmp_path, monkeypatch)
        orch.candle_log = [
            # Pre-AI skips (should NOT count)
            {"time": "2026-04-23T07:15:00Z", "kill_zone": "london",
             "decision": "NO_TRADE", "detail": "pre_screen: no_direction"},
            {"time": "2026-04-23T07:30:00Z", "kill_zone": "london",
             "decision": "NO_TRADE",
             "detail": "deterministic_no_bias: D1=ranging, H4=ranging, H1=ranging"},
            {"time": "2026-04-23T07:45:00Z", "kill_zone": "london",
             "decision": "NO_TRADE",
             "detail": "pre_ai_gate:no_unmitigated_h1_pois"},
            {"time": "2026-04-23T08:00:00Z", "kill_zone": "london",
             "decision": "SKIP_DORMANT", "detail": "daily_loss_stop active"},
            {"time": "2026-04-23T08:15:00Z", "kill_zone": "london",
             "decision": "EMERGENCY_STOP", "detail": "portfolio_drawdown=5%"},
            {"time": "2026-04-23T08:30:00Z", "kill_zone": "london",
             "decision": "BLOCKED_CALENDAR", "detail": "NFP"},
            # Real API-consuming evaluations (SHOULD count)
            {"time": "2026-04-23T09:00:00Z", "kill_zone": "london",
             "decision": "NO_TRADE",
             "detail": "AI returned NO_TRADE on liquidity sweep"},
            {"time": "2026-04-23T09:15:00Z", "kill_zone": "london",
             "decision": "CANDIDATE", "detail": "grade=A"},
            {"time": "2026-04-23T09:30:00Z", "kill_zone": "london",
             "decision": "REJECTED_L2",
             "detail": "h1_poi_exists: POI not in unmitigated OB"},
        ]

        orch._save_session_summary("london")

        # Only the last 3 rows should count (NO_TRADE from AI, CANDIDATE,
        # REJECTED_L2 — all are post-API-call terminal states)
        assert captured["summary"]["api_calls_made"] == 3


class TestCandidateCountingInSessionSummary:
    """Bug 4 (P3) — session summary reports CANDIDATE: 0 when raw evaluations
    show CANDIDATEs exist. Cause: when analysis.decision == CANDIDATE, the
    orchestrator skips logging CANDIDATE as the primary decision and instead
    logs the downstream outcome (REJECTED_L2, LIMIT_PLACED, EXECUTED). The
    summary's decision-name count then misses all CANDIDATEs that didn't
    reach EXECUTED.

    Fix: every post-CANDIDATE _log_candle call carries a
    ``produced_candidate=True`` flag. Session summary counts CANDIDATE by
    the flag, not by ``decision == CANDIDATE``. ``decision`` still holds
    the terminal outcome (REJECTED_L2 etc.) so existing readers that only
    consume ``decision`` are unchanged. Thursday US30 case: 6 CANDIDATEs
    in raw jsonl but 0 in summary.
    """

    def _make_orch(self, tmp_path):
        from src.components.orchestrator import SessionOrchestrator

        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        orch._symbol = "US30"
        orch.session_state = {"date": "2026-04-23"}
        orch.session_memory = []
        orch._last_mso = None
        orch._london_start = (7, 0)
        orch._london_core_end = (9, 30)
        orch._ny_start = (13, 0)
        orch._ny_end = (15, 30)

        captured = {}
        def capture(_date, _kz, summary):
            captured["summary"] = summary
        orch._write_session_summary_file = capture
        return orch, captured

    def test_log_candle_preserves_produced_candidate_flag(self):
        """Unit test: _log_candle with produced_candidate=True writes the
        flag into the log entry; default keeps entries clean (no flag)."""
        from unittest.mock import MagicMock
        from src.components.orchestrator import SessionOrchestrator

        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        orch.candle_log = []
        orch._write_chart_signal = MagicMock()

        orch._log_candle("NO_TRADE", "pre_screen: no_direction", "london")
        orch._log_candle("REJECTED_L2", "h1_poi_exists", "london",
                          produced_candidate=True)

        assert len(orch.candle_log) == 2
        assert "produced_candidate" not in orch.candle_log[0]
        assert orch.candle_log[1].get("produced_candidate") is True
        # Decision remains the terminal outcome (downstream-reader contract)
        assert orch.candle_log[1]["decision"] == "REJECTED_L2"

    def test_candidate_rejected_l2_still_counts_as_candidate(self, tmp_path):
        """The US30 Thursday scenario: 6 CANDIDATEs that all failed L2.
        Before fix: CANDIDATE=0 in summary. After fix: CANDIDATE=6."""
        orch, captured = self._make_orch(tmp_path)
        orch.candle_log = [
            {"time": f"2026-04-23T13:{i:02d}:00Z", "kill_zone": "ny",
             "decision": "REJECTED_L2", "produced_candidate": True,
             "detail": "h1_poi_exists: POI not in unmitigated OB"}
            for i in (15, 30, 45, 50, 55, 58)
        ]

        orch._save_session_summary("ny")

        assert captured["summary"]["decisions"]["CANDIDATE"] == 6, (
            f"Expected 6 CANDIDATE (all 6 rows produced one), got "
            f"{captured['summary']['decisions']['CANDIDATE']}"
        )
        # Still visible in candidate_details with post_decision_result
        assert len(captured["summary"]["candidate_details"]) == 6
        assert all(
            d["post_decision_result"] == "REJECTED_L2"
            for d in captured["summary"]["candidate_details"]
        )

    def test_legacy_candidate_decision_still_counted(self, tmp_path):
        """A CANDIDATE logged as ``decision='CANDIDATE'`` (e.g., if analysis
        falls through without further downstream logging) must also count."""
        orch, captured = self._make_orch(tmp_path)
        orch.candle_log = [
            {"time": "2026-04-23T13:30:00Z", "kill_zone": "ny",
             "decision": "CANDIDATE", "detail": "grade=A"},
        ]

        orch._save_session_summary("ny")

        assert captured["summary"]["decisions"]["CANDIDATE"] == 1

    def test_mixed_no_trade_and_candidate_counts(self, tmp_path):
        """Mix: 4 NO_TRADE (no AI produced) + 2 CANDIDATE-that-got-rejected.
        Summary should show NO_TRADE=4, CANDIDATE=2."""
        orch, captured = self._make_orch(tmp_path)
        orch.candle_log = [
            # Pure NO_TRADE (AI said NO_TRADE)
            {"time": "2026-04-23T13:00:00Z", "kill_zone": "ny",
             "decision": "NO_TRADE", "detail": "liquidity sweep absent"},
            {"time": "2026-04-23T13:15:00Z", "kill_zone": "ny",
             "decision": "NO_TRADE", "detail": "no m15 choch"},
            # CANDIDATE but rejected L2
            {"time": "2026-04-23T13:30:00Z", "kill_zone": "ny",
             "decision": "REJECTED_L2", "produced_candidate": True,
             "detail": "h1_poi_exists"},
            # Pre-screen skip (no AI call — NOT a CANDIDATE)
            {"time": "2026-04-23T13:45:00Z", "kill_zone": "ny",
             "decision": "NO_TRADE", "detail": "pre_screen: no_direction"},
            # CANDIDATE + LIMIT_PLACED (ultimate positive)
            {"time": "2026-04-23T14:00:00Z", "kill_zone": "ny",
             "decision": "LIMIT_PLACED", "produced_candidate": True,
             "detail": "lim_2026-04-23_1400"},
        ]

        orch._save_session_summary("ny")

        assert captured["summary"]["decisions"]["NO_TRADE"] == 3
        assert captured["summary"]["decisions"]["CANDIDATE"] == 2

    def test_candidate_produced_flag_on_limit_placed(self, tmp_path):
        """A LIMIT_PLACED entry (terminal positive CANDIDATE) counts."""
        orch, captured = self._make_orch(tmp_path)
        orch.candle_log = [
            {"time": "2026-04-23T13:30:00Z", "kill_zone": "ny",
             "decision": "LIMIT_PLACED", "produced_candidate": True,
             "detail": "lim_2026-04-23_1330"},
        ]
        orch._save_session_summary("ny")
        assert captured["summary"]["decisions"]["CANDIDATE"] == 1
        assert captured["summary"]["candidate_details"][0]["trade_id"] == "lim_2026-04-23_1330"


class TestCandidateFeaturesLoggedOnPreAiGate:
    """Bug 5 (P3) — ``log_candidate_features`` was positioned AFTER the
    pre-AI gate, so candles skipped by the gate were invisible to
    ``shadow_logs/candidate_features_log.jsonl``. Thursday 2026-04-23
    GBPUSD example: all 30 candles gated, zero rows in candidate features
    log.

    Fix: invoke ``log_candidate_features`` with ``pa_output=None`` and
    ``pre_ai_gate_skipped=True`` inside the pre-AI-gate branch BEFORE the
    return. Downstream consumers filter on ``pre_ai_gate_skipped``.

    Tests exercise the full gate-fire path through _process_candle so that
    a future re-positioning of the logger call site (or removal of the
    gate) is caught.
    """

    def _build_mso_with_no_h1_pois(self):
        """Build an MSO where H1 has zero unmitigated OBs and zero
        unretested breakers — matches the pre_ai_gates.h1_poi_availability
        short-circuit condition exactly."""
        from types import SimpleNamespace

        h1 = SimpleNamespace(
            order_blocks=[],         # zero unmitigated OBs
            breaker_blocks=[],       # zero unretested breakers
            fair_value_gaps=[],
            structure=SimpleNamespace(direction="bullish"),
            atr_14=20.0,
        )
        m15 = SimpleNamespace(
            order_blocks=[],
            breaker_blocks=[],
            fair_value_gaps=[],
            structure=SimpleNamespace(direction="bullish"),
            atr_14=4.0,
            clv_current=0.0, clv_avg_5=0.0, bvc_buy_fraction=0.5,
            net_flow_5=0, session_vol_ratio=1.0,
        )
        h4 = SimpleNamespace(
            order_blocks=[], breaker_blocks=[], fair_value_gaps=[],
            structure=SimpleNamespace(direction="bullish"), atr_14=40.0,
        )
        d1 = SimpleNamespace(
            order_blocks=[], breaker_blocks=[], fair_value_gaps=[],
            structure=SimpleNamespace(direction="bullish"), atr_14=80.0,
        )
        return SimpleNamespace(
            timeframes={"M15": m15, "H1": h1, "H4": h4, "D1": d1},
            liquidity_pools=[], detected_sweeps=[], session_levels=None,
            timestamp_utc="2026-04-23T07:15:00+00:00",
        )

    def test_pre_ai_gate_skip_writes_candidate_features_row(
        self, tmp_path, monkeypatch
    ):
        """The exact GBPUSD Thursday scenario: pre-AI gate fires → a
        candidate_features row IS written with pre_ai_gate_skipped=True
        and the MSO features populated."""
        import json
        from unittest.mock import MagicMock
        from src.components import orchestrator as _orch_mod
        from src.components import candidate_features_logger as _cf_mod
        from src.components.orchestrator import SessionOrchestrator

        # Redirect shadow log + session_state persistence + lock dir
        shadow_log = tmp_path / "candidate_features_log.jsonl"
        monkeypatch.setattr(_cf_mod, "SHADOW_LOG_PATH", str(shadow_log))
        monkeypatch.setattr(
            _orch_mod, "SESSION_STATE_DIR", tmp_path / "pipeline_state"
        )

        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        orch._symbol = "GBPUSD"
        orch._mt5_symbol = "GBPUSD"
        orch.config = {
            "risk": {"max_portfolio_drawdown_pct": 4.0,
                     "max_consecutive_losses": 5},
            "model_a": {"enabled_frameworks": ["ob_retest"]},
            "pre_ai_gates": {"h1_poi_availability_enabled": True},
            "session_memory_enabled": False,
        }
        orch.candle_log = []
        orch.session_state = {
            "date": "2026-04-23",
            "trades_today": 0,
            "daily_pnl_pct": 0.0,
            "portfolio_drawdown_pct": 0.0,
            "consecutive_losses": 0,
            "losses_today": 0,
            "current_kill_zone": "london",
            "trades_london": 0, "trades_ny": 0,
        }
        orch.mt5 = MagicMock()
        orch.execution = MagicMock()
        orch.execution.pending_intent = None

        orch._update_daily_pnl = MagicMock()
        orch._check_and_trigger_daily_loss_stop = MagicMock(return_value=False)
        orch._should_skip_first_ny_candle = MagicMock(return_value=False)
        orch._write_chart_signal = MagicMock()
        orch._compute_deterministic_bias = MagicMock(return_value={
            "bias": "bullish", "d1": "bullish", "h4": "bullish", "h1": "bullish",
        })
        orch._log_ob_retest_event = MagicMock()
        # News calendar disabled (not enabled → falls to the should_block_trading
        # path, which we stub by setting _calendar to an empty calendar and
        # monkeypatching should_block_trading to return False)
        orch._news_calendar = MagicMock()
        orch._news_calendar.enabled = False
        orch._calendar = []
        monkeypatch.setattr(
            _orch_mod, "should_block_trading",
            lambda *_a, **_kw: (False, None),
        )

        # Patch MSO computation to return the no-POI MSO
        fake_mso = self._build_mso_with_no_h1_pois()
        monkeypatch.setattr(_orch_mod, "compute_market_state",
                            lambda *_a, **_kw: fake_mso)
        # Patch pre-screen to pass
        monkeypatch.setattr(_orch_mod, "prescreen_mso",
                            lambda _mso: (True, ""))
        # Fake data ingest
        fake_candle = {"time": "2026-04-23T07:15:00+00:00",
                       "open": 1.25, "high": 1.252, "low": 1.248, "close": 1.251}
        monkeypatch.setattr(
            _orch_mod, "ingest_live_data",
            lambda mt5, config: {"candles": {"M15": [fake_candle]}},
        )

        # Run the candle — should hit pre-AI gate and return
        orch._process_candle("london")

        # Verify the gate fired (NO_TRADE with pre_ai_gate:... detail)
        assert any(
            e["decision"] == "NO_TRADE" and str(e.get("detail", "")).startswith("pre_ai_gate:")
            for e in orch.candle_log
        ), orch.candle_log

        # The critical assertion: shadow log was written BEFORE the return
        assert shadow_log.exists(), (
            "candidate_features_log.jsonl not written — pre-AI gate skipped "
            "the logger call (the Thursday GBPUSD observability gap)"
        )
        lines = shadow_log.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 1
        row = json.loads(lines[0])
        assert row["pre_ai_gate_skipped"] is True
        # Multi-framework reason format (broadened 2026-04-25): bias direction
        # appears first, framework set appears after the underscore. Old format
        # was "no_unmitigated_bullish_h1_pois" (ob_retest single-framework).
        assert row["pre_ai_gate_reason"] == "no_bullish_pois_for_ob_retest"
        assert row["symbol"] == "GBPUSD"
        assert row["kill_zone"] == "london"
        # AI-output fields are None (pa_output was None) but MSO fields present
        assert row["decision"] is None
        # MSO features were populated even on the gated path
        assert row["mso_h1_unmitigated_ob_count"] == 0
        assert row["mso_m15_atr_14"] == 4.0

    def test_pre_ai_gate_not_fired_still_logs_with_flag_false(
        self, tmp_path, monkeypatch
    ):
        """Regular AI-evaluated candle: existing log_candidate_features call
        (post-analysis) emits ``pre_ai_gate_skipped=False`` (default)."""
        import json
        from src.components import candidate_features_logger as cf

        shadow_log = tmp_path / "candidate_features_log.jsonl"
        monkeypatch.setattr(cf, "SHADOW_LOG_PATH", str(shadow_log))

        # Build a minimal MSO + fake pa_output
        from types import SimpleNamespace
        mso = SimpleNamespace(
            timeframes={}, liquidity_pools=[], detected_sweeps=[],
            session_levels=None,
        )
        pa = SimpleNamespace(
            decision="NO_TRADE", framework="ob_retest",
            reasoning=SimpleNamespace(
                daily_bias=SimpleNamespace(direction="bullish", confidence="high"),
                h4_alignment=SimpleNamespace(aligned=True),
                h1_setup=SimpleNamespace(poi_identified=False),
                liquidity_sweep=SimpleNamespace(detected=False),
                m15_confirmation=SimpleNamespace(choch_detected=False),
                setup_grade="B",
            ),
            trade_parameters=None, kill_zone="london",
        )

        cf.log_candidate_features(
            pa_output=pa, mso=mso, symbol="XAUUSD",
            timestamp_utc="2026-04-23T07:15:00+00:00",
            session_state={"kill_zone": "london"},
        )

        row = json.loads(shadow_log.read_text(encoding="utf-8").strip())
        assert row["pre_ai_gate_skipped"] is False
        assert row["pre_ai_gate_reason"] is None
        assert row["decision"] == "NO_TRADE"


class TestOrchestratorDataIncompleteRecovery:
    def test_live_ingest_retries_after_mt5_reconnect(self, monkeypatch):
        from src.components import orchestrator as orch_mod
        from src.components.data_ingestion import DataIncompleteError
        from src.components.orchestrator import SessionOrchestrator

        calls = []

        def fake_ingest(mt5, config):
            calls.append("ingest")
            if len(calls) == 1:
                raise DataIncompleteError("Insufficient D1 candles: got 0, need 30")
            return {"candles": {"M15": []}}

        class _MT5:
            def __init__(self):
                self.events = []

            def disconnect(self):
                self.events.append("disconnect")

            def connect(self):
                self.events.append("connect")
                return True

        monkeypatch.setattr(orch_mod, "ingest_live_data", fake_ingest)

        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        orch.mt5 = _MT5()
        orch.config = {}
        orch._symbol = "XAUUSD"

        result = orch._ingest_live_data_with_reconnect("ny")

        assert result == {"candles": {"M15": []}}
        assert calls == ["ingest", "ingest"]
        assert orch.mt5.events == ["disconnect", "connect"]

    def test_repeated_data_incomplete_exits_without_graceful_marker(self):
        from types import SimpleNamespace
        from src.components.data_ingestion import DataIncompleteError
        from src.components.orchestrator import SessionOrchestrator

        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        orch.config = {"risk": {}}
        orch.session_state = {
            "portfolio_drawdown_pct": 0.0,
            "consecutive_losses": 0,
        }
        orch.execution = SimpleNamespace(pending_intent=None)
        orch.running = True
        orch._data_incomplete_streak = 2
        orch._data_incomplete_restart_threshold = 3
        orch._abnormal_shutdown_reason = None
        logged = []

        orch._update_daily_pnl = lambda: None
        orch._check_and_trigger_daily_loss_stop = lambda _kz: False

        def fail_ingest(_kz):
            raise DataIncompleteError("Insufficient D1 candles: got 0, need 30")

        orch._ingest_live_data_with_reconnect = fail_ingest
        orch._log_candle = lambda decision, detail, kz, **_kw: logged.append((decision, detail, kz))

        orch._process_candle("ny")

        assert orch.running is False
        assert orch._abnormal_shutdown_reason.startswith("data_incomplete_streak_3")
        assert logged[0][0] == "NO_TRADE"
        assert "data_incomplete" in logged[0][1]

    def test_abnormal_shutdown_skips_graceful_marker(self):
        from types import SimpleNamespace
        from src.components.orchestrator import SessionOrchestrator

        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        orch._symbol = "XAUUSD"
        orch._abnormal_shutdown_reason = "data_incomplete_streak_3"
        events = []
        orch.mt5 = SimpleNamespace(disconnect=lambda: events.append("disconnect"))
        orch._end_session = lambda: events.append("end_session")
        orch._release_lock = lambda: events.append("release_lock")
        orch._write_graceful_shutdown_marker = lambda: events.append("marker")

        orch._shutdown()

        assert events == ["end_session", "disconnect", "release_lock"]
