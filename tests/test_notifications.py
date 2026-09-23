"""Telegram $/R conversion regression — FA-4 Phase 2.5 (session 36).

The bug: ``src/notifications.py`` used to hard-code ``_RISK_DOLLARS = $2000``
(2% of $100K = legacy FTMO). Under redacted_account the correct $/R figures are
$1000 (1% FX) and $500 (XAUUSD 0.5% override). These tests lock in the
``configure_notifications()`` contract so the orchestrator's profile+instrument
overlay propagates into Telegram dollar-formatted messages.

Canonical pattern: module-ref monkeypatch on ``src.notifications`` so
``_send_async`` is stubbed with a capture list; we then assert the rendered
strings contain the correct dollar figures.
"""
from __future__ import annotations

import pytest

from src import notifications as _notif


@pytest.fixture
def captured(monkeypatch, tmp_path):
    """Capture both fire-and-forget _send_async AND queue-routed dispatches.

    H7 (2026-04-26): ``notify_trade_closed`` + ``notify_alert`` now route
    HIGH-priority messages through ``src.utils.notification_queue``. To keep
    these formatting-regression tests valid, we replace BOTH transports with
    the same capture list so test assertions like ``"+$750" in captured[0]``
    keep working regardless of which path the producer takes.
    """
    bucket: list[str] = []
    monkeypatch.setattr(
        _notif, "_send_async", lambda text: bucket.append(text),
    )
    # Route the persistent queue's transport into the same capture list +
    # install a tmp_path-bound singleton so the queue's disk writes don't
    # touch the production pipeline_state/ tree.
    from src.utils import notification_queue as _nq_mod
    _nq_mod._reset_singleton_for_tests()
    _nq_mod._SINGLETON = _nq_mod.PersistentNotificationQueue(
        queue_path=tmp_path / "queue.jsonl",
        transport=lambda text: bucket.append(text) or True,
    )
    # The queue's daemon polls every 30s; run a flush on enqueue so tests
    # see deterministic delivery without waiting on the daemon.
    orig_send = _nq_mod._SINGLETON.send

    def _send_then_flush(message, *, level, alert_id=None):
        result = orig_send(message, level=level, alert_id=alert_id)
        _nq_mod._SINGLETON.flush()
        return result

    _nq_mod._SINGLETON.send = _send_then_flush  # type: ignore[method-assign]

    # Save + restore module-level risk globals so tests don't bleed.
    orig_bal = _notif._ACCOUNT_BALANCE
    orig_pct = _notif._RISK_PCT
    orig_dol = _notif._RISK_DOLLARS
    yield bucket
    _notif._ACCOUNT_BALANCE = orig_bal
    _notif._RISK_PCT = orig_pct
    _notif._RISK_DOLLARS = orig_dol
    _nq_mod._reset_singleton_for_tests()


@pytest.fixture
def temp_pnl(monkeypatch, tmp_path):
    """Redirect daily-pnl state + history to tmp so notify_trade_closed
    doesn't touch the real shadow_logs/daily_pnl{,_history.jsonl}.

    Both paths are module-level constants (``_PNL_PATH``,
    ``_PNL_HISTORY_PATH``) so callers that omit explicit args resolve
    here. The bug-2026-04-29 fix added the history ledger; the existing
    aggregate file is unchanged in writer semantics.
    """
    monkeypatch.setattr(_notif, "_PNL_PATH", tmp_path / "daily_pnl.json")
    monkeypatch.setattr(
        _notif, "_PNL_HISTORY_PATH", tmp_path / "daily_pnl_history.jsonl",
    )


class TestConfigureNotifications:
    """``configure_notifications`` must convert percent units → fraction and
    recompute ``_RISK_DOLLARS``."""

    def test_ftmo_default_two_percent(self, captured):
        _notif.configure_notifications(risk_per_trade_pct=2.0, account_balance=100_000)
        assert _notif._RISK_DOLLARS == pytest.approx(2_000.0)
        assert _notif._RISK_PCT == pytest.approx(0.02)

    def test_redacted_account_one_percent(self, captured):
        _notif.configure_notifications(risk_per_trade_pct=1.0, account_balance=100_000)
        assert _notif._RISK_DOLLARS == pytest.approx(1_000.0)

    def test_redacted_account_xauusd_half_percent(self, captured):
        _notif.configure_notifications(risk_per_trade_pct=0.5, account_balance=100_000)
        assert _notif._RISK_DOLLARS == pytest.approx(500.0)


class TestNotifyTradeClosedDollarFormatting:
    """End-to-end: rendered Telegram strings must carry the correct $ figure
    for the configured risk%."""

    def test_xauusd_redacted_account_half_percent_renders_750_for_1p5R(
        self, captured, temp_pnl,
    ):
        _notif.configure_notifications(risk_per_trade_pct=0.5, account_balance=100_000)
        _notif.notify_trade_closed("XAUUSD", "tp_hit", actual_r=1.5)
        assert len(captured) == 1
        msg = captured[0]
        assert "+$750" in msg, f"Expected '+$750' in message, got: {msg!r}"
        assert "+$3,000" not in msg
        assert "+$2,000" not in msg

    def test_fx_redacted_account_one_percent_renders_1500_for_1p5R(
        self, captured, temp_pnl,
    ):
        _notif.configure_notifications(risk_per_trade_pct=1.0, account_balance=100_000)
        _notif.notify_trade_closed("EURUSD", "tp_hit", actual_r=1.5)
        assert len(captured) == 1
        msg = captured[0]
        assert "+$1,500" in msg, f"Expected '+$1,500' in message, got: {msg!r}"
        assert "+$3,000" not in msg

    def test_ftmo_two_percent_backcompat_renders_3000_for_1p5R(
        self, captured, temp_pnl,
    ):
        """Backward compat: original FTMO behavior at 2% must still work."""
        _notif.configure_notifications(risk_per_trade_pct=2.0, account_balance=100_000)
        _notif.notify_trade_closed("XAUUSD", "tp_hit", actual_r=1.5)
        assert len(captured) == 1
        msg = captured[0]
        assert "+$3,000" in msg, f"Expected '+$3,000' at 2% × 1.5R, got: {msg!r}"

    def test_loss_renders_negative_dollars(self, captured, temp_pnl):
        _notif.configure_notifications(risk_per_trade_pct=0.5, account_balance=100_000)
        _notif.notify_trade_closed("XAUUSD", "sl_hit", actual_r=-1.0)
        assert len(captured) == 1
        msg = captured[0]
        assert "-$500" in msg, f"Expected '-$500' on -1R × $500, got: {msg!r}"


class TestNotifyLimitPlacedDollarFormatting:
    """The ``Risk: $X`` line in the LIMIT ORDER message must reflect the
    configured risk%, not the module-load-time default."""

    def test_xauusd_redacted_account_risk_line_shows_500(self, captured):
        _notif.configure_notifications(risk_per_trade_pct=0.5, account_balance=100_000)
        _notif.notify_limit_placed(
            symbol="XAUUSD", direction="LONG",
            entry=2050.00, sl=2045.00, tp=2060.00,
            rr=2.0, kill_zone="london", trade_id="lim_test",
        )
        assert len(captured) == 1
        assert "Risk: $500" in captured[0]
        assert "Risk: $2,000" not in captured[0]

    def test_vnext_limit_metadata_renders_when_supplied(self, captured):
        _notif.configure_notifications(risk_per_trade_pct=0.5, account_balance=100_000)
        _notif.notify_limit_placed(
            symbol="GER40",
            direction="SHORT",
            entry=25240.00,
            sl=25246.00,
            tp=25228.00,
            rr=2.0,
            kill_zone="ny",
            trade_id="lim_test",
            dynamic_policy="be_after_trigger",
            risk_pct=0.50,
            origin_family="cross_asset_lead_lag",
            selector_ref="row-123",
        )

        assert len(captured) == 1
        assert "Lifecycle: limit_placed" in captured[0]
        assert "Risk: pct=0.50%" in captured[0]
        assert "vNext: policy=be_after_trigger" in captured[0]
        assert "Origin: origin=cross_asset_lead_lag" in captured[0]
        assert "Selector/proof: row-123" in captured[0]


def _sample_vnext_context(**overrides):
    context = {
        "gtos_vnext_dynamic_policy_selected": "momentum_exhaustion",
        "gtos_vnext_execution_policy_id": "vnext_exec_momentum_1r_pullback_04r_cap_2r",
        "gtos_vnext_origin_family": "liquidity_sweep_reclaim",
        "gtos_vnext_selector_row_id": "selector-row-123",
        "gtos_vnext_selector_proof_hash": "proof-hash-456",
        "gtos_vnext_source_event_hash": "event-hash-789",
        "gtos_vnext_dynamic_be_trigger_r": 1.0,
        "gtos_vnext_dynamic_final_target_r": 2.0,
        "gtos_vnext_dynamic_momentum_pullback_r": 0.4,
        "gtos_vnext_dynamic_trail_gap_r": 0.5,
        "gtos_vnext_selected_cell_risk_pct": 0.5,
        "gtos_vnext_selected_cell_risk_cell_id": "cell-liquidity-sweep",
        "gtos_vnext_selected_cell_risk_decision_basis": "selected_cell_risk",
        "gtos_vnext_dynamic_policy_prop_action": "prop_safe_allow",
        "gtos_vnext_dynamic_policy_replaced_policy": "retired_static_baseline_comparator",
        "gtos_vnext_production_execution_path": True,
    }
    context.update(overrides)
    return context


def _assert_vnext_truth_rendered(message: str, *, lifecycle: str) -> None:
    assert f"Lifecycle: {lifecycle}" in message
    assert "vNext: policy=momentum_exhaustion" in message
    assert "id=vnext_exec_momentum_1r_pullback_04r_cap_2r" in message
    assert "Origin: origin=liquidity_sweep_reclaim" in message
    assert "Selector/proof: selector-row-123" in message
    assert "Dynamic: trigger=1.00R | final=2.00R | pullback=0.40R" in message
    assert "Risk: pct=0.50% | cell=cell-liquidity-sweep" in message
    assert "Prop/risk: prop=prop_safe_allow" in message
    assert "J46" not in message
    assert "J49" not in message
    assert "retired_static_baseline_comparator" not in message
    assert "fixed 1.5" not in message.lower()
    assert "fixed-1.5" not in message.lower()


class TestVNextNotificationParity:
    def test_limit_filled_renders_execution_truth(self, captured):
        _notif.notify_limit_filled(
            symbol="XAUUSD",
            direction="LONG",
            entry=2350.12,
            trade_id="vnext-fill-1",
            vnext_context=_sample_vnext_context(),
        )

        assert len(captured) == 1
        assert "FILLED" in captured[0]
        _assert_vnext_truth_rendered(captured[0], lifecycle="fill")

    def test_trade_closed_renders_and_records_execution_truth(
        self, captured, temp_pnl, tmp_path,
    ):
        _notif.notify_trade_closed(
            symbol="XAUUSD",
            result="vnext_momentum_exhaustion_pullback",
            actual_r=1.62,
            trade_id="vnext-close-1",
            entry_price=2350.0,
            exit_price=2358.1,
            vnext_context=_sample_vnext_context(),
        )

        assert len(captured) == 1
        _assert_vnext_truth_rendered(
            captured[0],
            lifecycle="vnext_momentum_exhaustion_pullback",
        )
        import json
        history = [
            json.loads(line)
            for line in (tmp_path / "daily_pnl_history.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line
        ]
        assert history[0]["gtos_vnext_notification_context"]["selected_policy"] == (
            "momentum_exhaustion"
        )
        assert history[0]["gtos_vnext_notification_context"]["execution_policy_id"] == (
            "vnext_exec_momentum_1r_pullback_04r_cap_2r"
        )

    def test_limit_expired_renders_execution_truth(self, captured):
        _notif.notify_limit_expired(
            symbol="XAUUSD",
            trade_id="vnext-expiry-1",
            reason="48h clock expiry",
            vnext_context=_sample_vnext_context(),
        )

        assert len(captured) == 1
        assert "EXPIRED" in captured[0]
        _assert_vnext_truth_rendered(captured[0], lifecycle="expiry")

    def test_runtime_lifecycle_event_renders_requested_event_type(self, captured):
        _notif.notify_vnext_lifecycle_event(
            symbol="XAUUSD",
            lifecycle_event="dynamic final close",
            trade_id="vnext-final-1",
            direction="LONG",
            price=2362.50,
            result_r=2.0,
            detail="tp2_final_target_vnext_momentum_exhaustion",
            vnext_context=_sample_vnext_context(),
        )

        assert len(captured) == 1
        assert "vNext LIFECYCLE" in captured[0]
        assert "Event: dynamic final close" in captured[0]
        assert "Position: LONG | price=2362.50 | result=+2.00R" in captured[0]
        _assert_vnext_truth_rendered(captured[0], lifecycle="dynamic final close")

    @pytest.mark.parametrize(
        "event",
        [
            "partial close",
            "BE transition",
            "momentum pullback close",
            "dynamic final close",
            "rejected order",
            "broker/deal reconciliation",
        ],
    )
    def test_runtime_lifecycle_event_type_matrix_is_vnext_aware(
        self, captured, event,
    ):
        _notif.notify_vnext_lifecycle_event(
            symbol="XAUUSD",
            lifecycle_event=event,
            trade_id=f"vnext-{event.replace(' ', '-')}",
            direction="LONG",
            price=2362.50,
            vnext_context=_sample_vnext_context(),
        )

        assert len(captured) == 1
        assert f"Event: {event}" in captured[0]
        _assert_vnext_truth_rendered(captured[0], lifecycle=event)


class TestNotifyLimitExpiredPersistentQueue:
    def test_limit_expired_routes_high_priority_through_queue(self, monkeypatch):
        from src.utils import notification_queue as _nq_mod

        calls = []

        def fake_send(message, *, level, alert_id=None):
            calls.append(
                {"message": message, "level": level, "alert_id": alert_id}
            )
            return alert_id or "generated"

        monkeypatch.setattr(_nq_mod, "send", fake_send)
        monkeypatch.setattr(
            _notif,
            "_send_async",
            lambda _text: pytest.fail("fire-and-forget path should not run"),
        )

        _notif.notify_limit_expired(
            "XAUUSD",
            "XAUUSD_2026-04-26_london_0700",
            "48h clock",
        )

        assert len(calls) == 1
        assert calls[0]["level"] is _nq_mod.Level.HIGH
        assert calls[0]["alert_id"] == (
            "limit_expired:XAUUSD:XAUUSD_2026-04-26_london_0700:48h clock"
        )
        assert "EXPIRED" in calls[0]["message"]
        assert "No fill" in calls[0]["message"]

    def test_limit_expired_falls_back_to_async_if_queue_fails(self, monkeypatch):
        from src.utils import notification_queue as _nq_mod

        captured = []

        def broken_send(*_args, **_kwargs):
            raise RuntimeError("queue unavailable")

        monkeypatch.setattr(_nq_mod, "send", broken_send)
        monkeypatch.setattr(_notif, "_send_async", lambda text: captured.append(text))

        _notif.notify_limit_expired("US30", "order-1", "new_day")

        assert len(captured) == 1
        assert "US30" in captured[0]
        assert "new_day" in captured[0]


class TestDailyPnlLogger:
    """Bug 2026-04-29 fix: ``_record_trade`` must:

    * Accumulate multiple closes per day (append, not overwrite).
    * Idempotent on ``trade_id`` so the orchestrator's exit-detection
      path AND the BUG #31 ``_notify_close_if_unsent`` fallback don't
      double-count the same close in ``daily_pnl.json``.
    * Always append to the audit-grade ``daily_pnl_history.jsonl``
      ledger (NOT deduplicated — duplicate dispatches still leave one
      row per dispatch for forensic reconstruction).
    * Capture per-trade metadata: ``trade_id``, ``realized_usd``,
      ``entry_price``, ``exit_price``, ``hold_minutes``.
    * Survive an existing legacy entry in ``daily_pnl.json`` that has
      no ``trade_id`` (back-compat with files written pre-fix).
    """

    def _read_pnl(self, path):
        import json
        return json.loads(path.read_text(encoding="utf-8"))

    def _read_history(self, path):
        import json
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]

    def test_two_distinct_closes_accumulate(self, captured, temp_pnl, tmp_path):
        """Two real closes (different trade_ids) on the same day must both
        land in ``trades`` and aggregate ``total_r`` correctly."""
        _notif.configure_notifications(risk_per_trade_pct=2.0, account_balance=100_000)
        _notif.notify_trade_closed(
            "GBPJPY", "broker_closed", actual_r=-0.0365,
            trade_id="GBPJPY_2026-04-28_london_0900",
            entry_price=215.274, exit_price=215.260,
        )
        _notif.notify_trade_closed(
            "GBPJPY", "sl_modification_failed", actual_r=0.742,
            trade_id="adopted_233955223",
            entry_price=215.274, exit_price=215.559,
        )
        pnl = self._read_pnl(tmp_path / "daily_pnl.json")
        assert len(pnl["trades"]) == 2
        ids = {t["trade_id"] for t in pnl["trades"]}
        assert "GBPJPY_2026-04-28_london_0900" in ids
        assert "adopted_233955223" in ids
        # 2% / $100k → $2000/R; -0.0365 + 0.742 = +0.7055
        assert pnl["total_r"] == pytest.approx(0.7055, abs=1e-4)
        # Merged from the VPS live lineage 2026-07-26: realized_usd / total_usd are now
        # BROKER-NET TRUTH ONLY and stay None unless the deal is broker-reconciled. The
        # R x $2,000 figure is a projection and now lives under local_projected_usd.
        # These assertions previously reported the projection under the name 'realized'.
        assert pnl["total_usd"] is None
        assert pnl["total_local_projected_usd"] == pytest.approx(0.7055 * 2000.0, abs=1.0)
        assert pnl["wins"] == 1
        assert pnl["losses"] == 1

    def test_dedup_orchestrator_then_execution_engine(
        self, captured, temp_pnl, tmp_path,
    ):
        """When orchestrator's exit path fires notify_trade_closed AND the
        execution engine's _notify_close_if_unsent fallback ALSO fires
        for the same close, ``daily_pnl.json`` must record only one
        entry. (Both paths are correct by design — see BUG #31 — but
        the user-facing ledger should not double-count.)"""
        _notif.configure_notifications(risk_per_trade_pct=2.0, account_balance=100_000)
        # Pretend the orchestrator's path fired first.
        _notif.notify_trade_closed(
            "GBPJPY", "tp_hit", actual_r=1.5,
            trade_id="GBPJPY_2026-04-28_london_0900",
        )
        # Now the BUG #31 fallback fires for the same trade_id (different
        # exit-reason free-form string but same position).
        _notif.notify_trade_closed(
            "GBPJPY", "tp", actual_r=1.5,
            trade_id="GBPJPY_2026-04-28_london_0900",
        )
        pnl = self._read_pnl(tmp_path / "daily_pnl.json")
        assert len(pnl["trades"]) == 1, (
            f"Expected dedup on trade_id but got {len(pnl['trades'])} entries: "
            f"{pnl['trades']}"
        )
        assert pnl["wins"] == 1
        assert pnl["losses"] == 0
        assert pnl["total_r"] == pytest.approx(1.5)

    def test_history_jsonl_records_every_dispatch_including_dups(
        self, captured, temp_pnl, tmp_path,
    ):
        """``daily_pnl_history.jsonl`` is the audit-grade ledger and is
        intentionally NOT deduplicated. Both dispatches for the same
        close land as separate rows so a post-hoc audit can reconstruct
        the dispatch timeline."""
        _notif.configure_notifications(risk_per_trade_pct=2.0, account_balance=100_000)
        _notif.notify_trade_closed(
            "GBPJPY", "tp_hit", actual_r=1.5,
            trade_id="dup_test",
        )
        _notif.notify_trade_closed(
            "GBPJPY", "tp", actual_r=1.5,
            trade_id="dup_test",
        )
        history = self._read_history(tmp_path / "daily_pnl_history.jsonl")
        assert len(history) == 2, (
            f"Expected both dispatches in history (audit ledger is not "
            f"deduplicated) but got {len(history)} rows"
        )
        assert all(row["trade_id"] == "dup_test" for row in history)

    def test_dedup_skip_when_trade_id_empty(
        self, captured, temp_pnl, tmp_path,
    ):
        """Legacy callers that omit trade_id must still record both
        events (no string to dedup on). This preserves backward
        compatibility with smoke-test scripts that don't propagate a
        trade_id."""
        _notif.configure_notifications(risk_per_trade_pct=2.0, account_balance=100_000)
        _notif.notify_trade_closed("XAUUSD", "tp_hit", actual_r=1.5)
        _notif.notify_trade_closed("XAUUSD", "tp_hit", actual_r=1.5)
        pnl = self._read_pnl(tmp_path / "daily_pnl.json")
        assert len(pnl["trades"]) == 2
        assert pnl["wins"] == 2

    def test_safety_handler_force_close_recorded(
        self, captured, temp_pnl, tmp_path,
    ):
        """Force-closes from the safety/cascade path (e.g.
        ``sl_modification_failed``, ``j46_j49_time_stop``) are NOT in
        the legacy exit_map but must still be recorded — the writer
        treats unknown exit_types as raw strings, no whitelist."""
        _notif.configure_notifications(risk_per_trade_pct=2.0, account_balance=100_000)
        for exit_type in (
            "sl_modification_failed",
            "j46_j49_time_stop",
            "broker_closed",
            "manual",
        ):
            _notif.notify_trade_closed(
                "GBPJPY", exit_type, actual_r=0.5,
                trade_id=f"trade_{exit_type}",
            )
        pnl = self._read_pnl(tmp_path / "daily_pnl.json")
        assert len(pnl["trades"]) == 4
        recorded_types = {t["exit_type"] for t in pnl["trades"]}
        assert recorded_types == {
            "sl_modification_failed", "j46_j49_time_stop",
            "broker_closed", "manual",
        }

    def test_realized_usd_field_populated(
        self, captured, temp_pnl, tmp_path,
    ):
        """``realized_usd`` must reflect the configured risk_dollars
        contract — 1.5R × $2000 = $3000 at 2%/$100k."""
        _notif.configure_notifications(risk_per_trade_pct=2.0, account_balance=100_000)
        _notif.notify_trade_closed(
            "XAUUSD", "tp_hit", actual_r=1.5, trade_id="realized_usd_test",
        )
        pnl = self._read_pnl(tmp_path / "daily_pnl.json")
        # Merged from the VPS live lineage 2026-07-26: realized_usd / total_usd are now
        # BROKER-NET TRUTH ONLY and stay None unless the deal is broker-reconciled. The
        # R x $2,000 figure is a projection and now lives under local_projected_usd.
        # These assertions previously reported the projection under the name 'realized'.
        assert pnl["trades"][0]["realized_usd"] is None
        assert pnl["trades"][0]["local_projected_usd"] == pytest.approx(3000.0)
        assert pnl["total_usd"] is None
        assert pnl["total_local_projected_usd"] == pytest.approx(3000.0)

    def test_broker_reconciled_close_uses_broker_profit_truth(
        self, captured, temp_pnl, tmp_path,
    ):
        """Broker close-deal profit must override local dollar projection."""
        _notif.configure_notifications(risk_per_trade_pct=0.25, account_balance=100_000)
        _notif.notify_trade_closed(
            "BTCUSD",
            "broker_closed",
            actual_r=0.0,
            trade_id="BTCUSD_2026-06-01_off_configured_session_1200",
            entry_price=72300.67,
            exit_price=70778.26,
            broker_profit=380.6,
            broker_deal_reconciled=True,
            broker_deal_id=226130424,
            broker_close_order_id=242318933,
        )

        assert len(captured) == 1
        msg = captured[0]
        assert "Broker P&L: +$380.60" in msg
        assert "Broker deal: 226130424" in msg
        assert "P&L: +$0" not in msg
        assert "Today: +0.00R (+$380.60) | 1W 0L" in msg

        pnl = self._read_pnl(tmp_path / "daily_pnl.json")
        row = pnl["trades"][0]
        assert row["realized_usd"] == pytest.approx(380.6)
        assert row["local_projected_usd"] == pytest.approx(0.0)
        assert row["dollar_evidence_class"] == "BROKER_DEAL_RECONCILED_PROFIT"
        assert row["actual_dollar_claim_allowed"] is True
        assert row["account_truth_status"] == "BROKER_DEAL_RECONCILED_AT_NOTIFICATION_TIME"
        assert row["broker_deal_reconciled"] is True
        assert row["broker_deal_id"] == 226130424
        assert pnl["total_usd"] == pytest.approx(380.6)
        assert pnl["wins"] == 1
        assert pnl["losses"] == 0

    def test_broker_reconciled_close_prefers_position_net_profit_truth(
        self, captured, temp_pnl, tmp_path,
    ):
        """Partial/final broker closes must report whole-position net P&L."""
        _notif.configure_notifications(risk_per_trade_pct=0.25, account_balance=100_000)
        _notif.notify_trade_closed(
            "BTCUSD",
            "broker_closed",
            actual_r=2.02,
            trade_id="BTCUSD_NET",
            entry_price=72300.67,
            exit_price=70778.26,
            broker_profit=380.6,
            broker_net_profit=496.09,
            broker_deal_reconciled=True,
            broker_deal_id=226130424,
            broker_close_order_id=242318933,
            broker_commission=-14.46,
            broker_swap=0.0,
        )

        msg = captured[0]
        assert "Broker P&L: +$496.09" in msg
        pnl = self._read_pnl(tmp_path / "daily_pnl.json")
        row = pnl["trades"][0]
        assert row["realized_usd"] == pytest.approx(496.09)
        assert row["broker_profit"] == pytest.approx(380.6)
        assert row["broker_net_profit"] == pytest.approx(496.09)
        assert pnl["total_usd"] == pytest.approx(496.09)

    def test_back_compat_legacy_entries_without_trade_id(
        self, captured, temp_pnl, tmp_path,
    ):
        """Production ``daily_pnl.json`` carried entries without
        ``trade_id`` before this fix. New writes must coexist with
        them — dedup must NOT match legacy entries (whose ``trade_id``
        is missing/None) against new entries with an explicit
        ``trade_id``."""
        import json
        legacy = {
            "date": _notif.datetime.now(_notif.timezone.utc).strftime("%Y-%m-%d"),
            "trades": [
                {
                    "symbol": "GBPJPY", "result_r": -0.0365,
                    "exit_type": "broker_closed", "time": "09:30",
                },
            ],
            "total_r": -0.0365, "wins": 0, "losses": 1,
        }
        (tmp_path / "daily_pnl.json").write_text(
            json.dumps(legacy), encoding="utf-8",
        )
        _notif.configure_notifications(risk_per_trade_pct=2.0, account_balance=100_000)
        _notif.notify_trade_closed(
            "GBPJPY", "tp_hit", actual_r=0.74,
            trade_id="adopted_233955223",
        )
        pnl = self._read_pnl(tmp_path / "daily_pnl.json")
        assert len(pnl["trades"]) == 2, (
            "Legacy entry (no trade_id) and new entry (with trade_id) "
            "must coexist — dedup must not match across that boundary"
        )
        assert pnl["wins"] == 1  # The new +0.74R win
        assert pnl["losses"] == 1  # Legacy entry still counted

    def test_aggregate_recomputed_from_trades_list(
        self, captured, temp_pnl, tmp_path,
    ):
        """``total_r`` and ``total_usd`` must be derived from
        ``trades`` list, not from independent counters that could drift."""
        _notif.configure_notifications(risk_per_trade_pct=2.0, account_balance=100_000)
        _notif.notify_trade_closed(
            "XAUUSD", "tp_hit", actual_r=1.5, trade_id="t1",
        )
        _notif.notify_trade_closed(
            "GBPJPY", "sl_hit", actual_r=-1.0, trade_id="t2",
        )
        _notif.notify_trade_closed(
            "USDJPY", "tp_hit", actual_r=2.0, trade_id="t3",
        )
        pnl = self._read_pnl(tmp_path / "daily_pnl.json")
        # Independently recompute aggregates.
        sum_r = sum(t["result_r"] for t in pnl["trades"])
        assert pnl["total_r"] == pytest.approx(sum_r)
        assert pnl["total_r"] == pytest.approx(2.5)

    def test_history_row_has_audit_metadata(
        self, captured, temp_pnl, tmp_path,
    ):
        """Each history row must carry the per-event metadata required
        for offline reconstruction: ts_utc, symbol, trade_id, result_r,
        realized_usd, exit_type."""
        _notif.configure_notifications(risk_per_trade_pct=2.0, account_balance=100_000)
        _notif.notify_trade_closed(
            "GBPJPY", "sl_modification_failed", actual_r=0.742,
            trade_id="adopted_233955223",
            entry_price=215.274, exit_price=215.559,
            hold_minutes=361.0,
        )
        history = self._read_history(tmp_path / "daily_pnl_history.jsonl")
        assert len(history) == 1
        row = history[0]
        for required in (
            "ts_utc", "symbol", "trade_id", "result_r",
            "realized_usd", "exit_type", "entry_price",
            "exit_price", "hold_minutes", "risk_dollars",
            "r_evidence_class", "dollar_evidence_class",
            "actual_r_claim_allowed", "actual_dollar_claim_allowed",
            "account_truth_status",
        ):
            assert required in row, f"history row missing field: {required}"
        assert row["symbol"] == "GBPJPY"
        assert row["trade_id"] == "adopted_233955223"
        assert row["result_r"] == pytest.approx(0.742)
        # Merged from the VPS live lineage 2026-07-26: realized_usd / total_usd are now
        # BROKER-NET TRUTH ONLY and stay None unless the deal is broker-reconciled. The
        # R x $2,000 figure is a projection and now lives under local_projected_usd.
        # These assertions previously reported the projection under the name 'realized'.
        assert row["realized_usd"] is None
        assert row["local_projected_usd"] == pytest.approx(0.742 * 2000.0, abs=1.0)
        assert row["entry_price"] == pytest.approx(215.274)
        assert row["exit_price"] == pytest.approx(215.559)
        assert row["hold_minutes"] == pytest.approx(361.0)
        assert row["r_evidence_class"] == "LOCAL_NOTIFICATION_R_INPUT"
        assert row["dollar_evidence_class"] == "LOCAL_RISK_DOLLAR_PROJECTION"
        assert row["actual_r_claim_allowed"] is False
        assert row["actual_dollar_claim_allowed"] is False
