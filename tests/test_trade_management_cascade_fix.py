"""Regression suite for the 2026-04-28 GBPJPY trade-management cascade.

Locks in the three-bug fix shipped on branch
``feature/fix-trade-management-cascade``:

* BUG #26 (orchestrator): session-end logic must reconcile with
  ``mt5.get_positions()`` (magic-filtered) before declaring no
  active trade. If a position exists, do NOT end the session —
  adopt the orphan and stay in monitoring-only mode.

* BUG #27 (execution): orphan-adopt + handle_timeout_trailing must
  NOT move SL→BE when J46-J49 v2 is active and the position is
  below the configured ``tp1_distance_r`` (default 3.0R). The
  pre-fix code fired BE on any-positive-profit including +0.74R.

* BUG #28 (execution): SL-modification failure must NOT close the
  position. Retry with backoff; if all retries fail, log ERROR,
  notify the CEO, and **leave the existing SL untouched**. The
  pre-fix close-on-failure path threw away an entire +6R upside
  on the GBPJPY 2026-04-28 trade by force-closing at +0.74R.

End-to-end test ``TestCascadeEndToEnd`` simulates the actual
2026-04-28 sequence (session-end + restart + adopt at +0.74R +
mocked SL-modify failure) and asserts the position remains open
with the original SL.

The supporting unit tests for BUG #27 and BUG #28 in isolation
live in ``tests/test_execution.py`` (``TestJ46J49BreakevenGating``
+ ``TestSLModificationFailure``).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import pytest

from src.components import execution as _exec_mod
from src.components import orchestrator as _orch_mod
from src.components.execution import ExecutionEngine
from src.components.orchestrator import SessionOrchestrator
from src.mt5.mt5_interface import MAGIC_NUMBER, PositionInfo
from src.mt5.mt5_mock import MockMT5


def _bare_orchestrator() -> SessionOrchestrator:
    """Build a SessionOrchestrator instance without going through ``__init__``.

    Mirrors the ``TestKillZoneDetection._make_orchestrator`` pattern in
    ``test_orchestrator.py``: we skip the heavyweight init (KB seed,
    LLM backend, lock file, MT5 connect, calendar load, ...) and stitch
    on only the attributes the methods under test touch.
    """
    orch = SessionOrchestrator.__new__(SessionOrchestrator)
    orch._symbol = "GBPJPY"
    orch._mt5_symbol = "GBPJPY"
    orch.session_state = {
        "date": "2026-04-28",
        "trades_today": 0,
        "current_kill_zone": "ny",
    }
    orch.candle_log = []
    orch.session_memory = []
    orch.mode = "demo"
    return orch


def _j46_j49_config() -> dict:
    return {
        "risk": {"risk_per_trade_pct": 1.0},
        "position_mgmt": {
            "j46_j49_v2": {
                "enabled": True,
                "partial_close_ratio": 0.0,
                "be_trigger": "immediate_on_tp1",
                "time_stop_bars": 12,
                "tp1_distance_r": 3.0,
                "higher_target_r": 6.0,
            },
        },
    }


# -----------------------------------------------------------------------
# BUG #26 — session-end reconciliation
# -----------------------------------------------------------------------


class TestSessionEndReconciliation:
    """The orchestrator must NOT end the session when an open broker
    position exists with our magic, even if local ``active_trade`` is
    None.
    """

    def test_session_end_with_no_positions_returns_false(
        self, monkeypatch, tmp_path,
    ):
        """When the broker has no open positions, helper returns False
        (caller will end the session normally).
        """
        orch = _bare_orchestrator()
        mt5 = MockMT5(balance=100000.0)
        mt5.connect()
        orch.mt5 = mt5
        orch.execution = ExecutionEngine(mt5, _j46_j49_config())

        # Isolate the per-symbol pending-intent path so the engine init
        # doesn't trip the production write guard.
        monkeypatch.setattr(
            _exec_mod, "PENDING_INTENT_DIR", str(tmp_path),
        )
        monkeypatch.setattr(
            _exec_mod, "CHECKPOINT_PATH",
            str(tmp_path / "execution_checkpoint.json"),
        )

        result = orch._reconcile_open_positions_or_continue()
        assert result is False
        assert orch.execution.active_trade is None

    def test_session_end_with_open_position_does_not_end_session(
        self, monkeypatch, tmp_path,
    ):
        """When the broker has a position with our magic and local
        ``active_trade`` is None, the helper must adopt the orphan
        and return True (caller stays in the monitoring loop).
        """
        orch = _bare_orchestrator()
        mt5 = MockMT5(balance=100000.0)
        mt5.connect()
        orch.mt5 = mt5
        orch.execution = ExecutionEngine(mt5, _j46_j49_config())

        monkeypatch.setattr(
            _exec_mod, "PENDING_INTENT_DIR", str(tmp_path),
        )
        monkeypatch.setattr(
            _exec_mod, "CHECKPOINT_PATH",
            str(tmp_path / "execution_checkpoint.json"),
        )

        # GBPJPY orphan at +0.74R (the 2026-04-28 production state).
        mt5._positions.append(PositionInfo(
            ticket=233955223, symbol="GBPJPY", type=0, volume=7.76,
            price_open=215.20, sl=214.89, tp=217.06, profit=1390.55,
            magic=MAGIC_NUMBER, comment="orphan",
            time=datetime.now(timezone.utc),
        ))
        orch.execution.symbol = "GBPJPY"
        # Stub _reconnect_trade_record to avoid touching prod KB on the
        # adopted-trade reconnect path.
        orch._reconnect_trade_record = lambda: None  # type: ignore[method-assign]

        result = orch._reconcile_open_positions_or_continue()

        assert result is True, (
            "Helper must return True when an orphan was adopted "
            "(BUG #26 — must not let session-end fire)"
        )
        assert orch.execution.active_trade is not None
        assert orch.execution.active_trade.ticket == 233955223
        # Existing SL preserved through adoption.
        assert orch.execution.active_trade.stop_loss == 214.89

    def test_session_end_with_mt5_error_falls_through(
        self, monkeypatch, tmp_path,
    ):
        """If get_positions raises (broken connection), helper returns
        False so the session ends and the watchdog respawns. The next
        bootstrap will adopt the orphan via reconcile_on_startup.
        """
        orch = _bare_orchestrator()
        mt5 = MockMT5(balance=100000.0)
        mt5.connect()
        orch.mt5 = mt5
        orch.execution = ExecutionEngine(mt5, _j46_j49_config())

        monkeypatch.setattr(
            _exec_mod, "PENDING_INTENT_DIR", str(tmp_path),
        )
        monkeypatch.setattr(
            _exec_mod, "CHECKPOINT_PATH",
            str(tmp_path / "execution_checkpoint.json"),
        )

        def _raise(*_a, **_kw):
            raise RuntimeError("mocked MT5 disconnect")

        mt5.get_positions = _raise  # type: ignore[method-assign]

        result = orch._reconcile_open_positions_or_continue()
        assert result is False


# -----------------------------------------------------------------------
# End-to-end cascade simulation
# -----------------------------------------------------------------------


class TestCascadeEndToEnd:
    """Replays the full 2026-04-28 GBPJPY cascade in one test.

    Sequence:
      1. Open position exists at +0.74R (post-fill state from prior
         orchestrator session).
      2. New orchestrator boots; reconcile_on_startup adopts the orphan.
      3. main loop hits ``_is_after_all_kz`` branch, calls
         ``_manage_timeout_trailing`` → ``handle_timeout_trailing``.
      4. With J46-J49 active and position at +0.74R (< 3R), BE move
         must NOT fire.
      5. Even if some other path attempts SL→BE while the broker is
         rejecting modifies, the position must remain open with the
         original SL.

    Pre-fix: position got force-closed at +0.74R, lost ~$10k upside.
    Post-fix: position remains open with original SL = 214.89.
    """

    def test_full_cascade_position_remains_open_with_original_sl(
        self, monkeypatch, tmp_path, caplog,
    ):
        # --- Setup ---
        mt5 = MockMT5(balance=100000.0)
        mt5.connect()
        config = _j46_j49_config()
        engine = ExecutionEngine(mt5, config)
        engine.symbol = "GBPJPY"

        monkeypatch.setattr(
            _exec_mod, "PENDING_INTENT_DIR", str(tmp_path),
        )
        monkeypatch.setattr(
            _exec_mod, "CHECKPOINT_PATH",
            str(tmp_path / "execution_checkpoint.json"),
        )

        # GBPJPY production state: ticket 233955223, vol 7.76, SL 214.89,
        # TP 6R = 217.06, currently at +$1390.55 profit.
        entry = 215.20
        original_sl = 214.89
        sl_distance = entry - original_sl  # = 0.31 (1R)
        tp_6r = 217.06
        mt5._positions.append(PositionInfo(
            ticket=233955223, symbol="GBPJPY", type=0, volume=7.76,
            price_open=entry, sl=original_sl, tp=tp_6r, profit=1390.55,
            magic=MAGIC_NUMBER, comment="orphan",
            time=datetime.now(timezone.utc),
        ))

        # --- Step 2: orphan adoption ---
        actions = engine.reconcile_on_startup()
        assert any("orphan_adopted" in a for a in actions)
        assert engine.active_trade is not None
        assert engine.active_trade.ticket == 233955223
        assert engine.active_trade.stop_loss == original_sl
        assert engine.active_trade.sl_distance == sl_distance
        # Adopted positions never carry j46_j49_active=True.
        assert engine.active_trade.j46_j49_active is False

        # --- Step 3: tick at +0.74R (the production cascade price) ---
        # current = entry + 0.74 * sl_distance = 215.20 + 0.2294 = 215.4294
        current_long = entry + 0.74 * sl_distance
        mt5.set_tick(bid=current_long, ask=current_long + 0.001)

        # --- Step 4: handle_timeout_trailing should NOT move SL ---
        action = engine.handle_timeout_trailing()
        assert action == "trailing"
        assert not engine.active_trade.sl_at_breakeven, (
            "BUG #27: SL was moved to BE at +0.74R when J46-J49 trigger is +3R"
        )
        assert engine.active_trade.stop_loss == original_sl
        assert engine.active_trade is not None  # NOT closed

        # --- Step 5: even under concurrent SL-modify rejection, position survives ---
        # Now simulate an unrelated/follow-up SL→BE attempt failing on
        # all retries (e.g., reaching +3R but broker rejects). Must NOT
        # close the position (BUG #28).
        original_send = mt5.order_send
        # `_modify_sl` sends TRADE_ACTION_SLTP (= 6, `src/mt5/mt5_interface.py:64`,
        # sent at `src/components/execution.py:9679`). This stub used to gate on a
        # hardcoded `2`, which is not any MetaTrader5 trade action, so it never
        # fired: the SL→BE call below succeeded and the BUG #28 guard never ran.
        # Bind the constant so a renumbering cannot silently disarm it again.
        from src.mt5.mt5_interface import OrderResult, TRADE_ACTION_SLTP

        sltp_requests: list[dict] = []

        def failing_send(request):
            if request.get("action") == TRADE_ACTION_SLTP:
                sltp_requests.append(dict(request))
                return OrderResult(
                    retcode=10011, order=0, volume=0, price=0,
                    comment="freeze_level",
                )
            return original_send(request)

        mt5.order_send = failing_send
        monkeypatch.setattr(engine, "_sl_modify_backoff", lambda _idx: None)

        alerts: list[str] = []
        import src.notifications as _notif_mod
        monkeypatch.setattr(
            _notif_mod, "notify_alert", lambda text: alerts.append(text),
        )

        with caplog.at_level(logging.ERROR, logger="src.components.execution"):
            engine._move_sl_to_breakeven(
                engine.active_trade, engine.active_trade.ticket,
            )

        # Anti-vacuity: the broker-rejection stub MUST have been reached, or
        # every invariant below is asserted against a path that never failed.
        assert sltp_requests, (
            "SL-modify rejection stub never fired — no TRADE_ACTION_SLTP request "
            "reached the broker, so the BUG #28 retry-and-leave path was not "
            "exercised and the assertions below prove nothing."
        )
        assert all(r["position"] == 233955223 for r in sltp_requests)

        # CRITICAL invariants — the cascade is BROKEN if any of these fail:
        assert engine.active_trade is not None, (
            "BUG #28: position was force-closed on SL-modify failure"
        )
        assert engine.active_trade.ticket == 233955223
        assert engine.active_trade.stop_loss == original_sl, (
            "Original SL must be preserved through retry-and-leave path"
        )
        assert not engine.active_trade.sl_at_breakeven
        assert len(alerts) == 1
        assert "[CRITICAL]" in alerts[0]
        # SL→BE error log (renderer encodes the arrow as "SL→BE" in source).
        errs = [r.getMessage() for r in caplog.records if r.levelname == "ERROR"]
        assert any(
            "leaving existing SL" in e and "NOT closing" in e for e in errs
        ), f"Expected error log preserving original SL; got {errs}"
