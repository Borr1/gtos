"""FrozenPriceIntent V1 — F5-only, default-off, quote-dependent cost skips stay live."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.components.ultimate_book.admission import TradeIntent
from src.components.ultimate_book.book_owner import UltimateBookOwner
from src.components.ultimate_book.frozen_price_intent import (
    PACKET_CLASS_MODEL_INPUT,
    PACKET_CLASS_NONE,
    PACKET_CLASS_QUOTE_DEPENDENT,
    PACKET_CLASS_STRUCTURAL,
    STATE_EXPIRED,
    STATE_FILLED,
    STATE_PRICE_INVALIDATED,
    STATE_REFUSED_COST,
    build_frozen_price_intent,
    chase_stop_fraction,
    classify_cost_refusal,
    geometry_from_intent_tick,
    immutable_floor_clear,
    is_blow_through,
    is_market_stop,
    quote_series_rollup,
)
from src.components.ultimate_book.minimal_size import MinimalSizeConfig


BAR = "2026-08-16T05:00:00+00:00"
START = datetime(2026, 8, 16, 5, 0, tzinfo=timezone.utc)
EURUSD_COMMISSION_R = 0.427


class _MT5:
    def __init__(self, spread: float = 0.08):
        self.spread = spread
        self.bid = 100.0

    def get_tick(self, _symbol):
        # Stale-tick gate measures age against wall-clock now, not cycle-top now_utc.
        return SimpleNamespace(
            bid=self.bid,
            ask=self.bid + self.spread,
            time=datetime.now(timezone.utc),
        )

    def get_account_balance(self):
        return 100_000.0

    def get_account_equity(self):
        return 100_000.0


class _RecordingEngine:
    def __init__(self):
        self.calls = []
        self.active_trade = None
        self._last_open_trade_block_reason = None
        self._f5_scaler = None

    def open_trade(self, trade_params, balance, **_kwargs):
        self.calls.append(dict(trade_params))
        state = SimpleNamespace(
            ticket=9100 + len(self.calls),
            entry_price=float(trade_params["entry_price"]),
            stop_loss=float(trade_params["stop_loss"]),
            take_profit_1=float(trade_params.get("take_profit_1") or 0.0),
            initial_volume=0.01,
        )
        self.active_trade = state
        self._last_open_trade_block_reason = None
        return state


class _CostPacketEngine:
    def __init__(self, packet):
        self.packet = packet
        self.calls = []
        self.active_trade = None
        self._last_open_trade_block_reason = "exec_mgr_v4:missing_cost:pretrade_cost_model_status_passed"

    def open_trade(self, trade_params, balance, **_kwargs):
        self.calls.append(dict(trade_params))
        trade_params["gtos_vnext_pretrade_cost_model"] = dict(self.packet)
        return None


class _FrozenEvalEngine:
    def __init__(self, intent, unit, bar=BAR):
        self.intent = intent
        self.unit = unit
        self.bar = bar
        self.config = {"ultimate_book_max_entry_lateness_frac": 10.0}
        self.evaluate_count = 0

    def evaluate(self, *, now_utc=None, tags=None):
        self.evaluate_count += 1
        decision = SimpleNamespace(
            realized_units=[dict(self.unit)],
            would_units=[dict(self.unit)],
            runtime_effect_now=True,
            candidate_use_allowed_now=True,
            decision_status="admitted_book_authority",
            kelly_running_count=False,
            kelly_lite=True,
            governor={"available_gross_risk_pct": 4.0},
        )
        return {
            "ok": True,
            "reason": "admitted_book_authority",
            "n_intents": 1,
            "runtime_effect_now": True,
            "decision": decision,
            "intents": [self.intent],
            "meta": [{
                "tag": self.intent.sleeve,
                "symbol": self.intent.symbol,
                "decision_bar_iso": self.bar,
                "timeframe": 16388,
            }],
            "generation": {},
            "generation_skips": [],
            "lane_weights": {},
            "governor_state": SimpleNamespace(equity=100_000.0, realized_today_pct=0.0),
        }

    def reset_window_date(self, _now):
        return "2026-08-16"

    def broker_day_start_balance(self, _now):
        return 100_000.0

    def record_placement_conviction(self, _intent):
        return None


def _runtime():
    return {
        "ultimate_book_enabled": True,
        "ultimate_book_apply_to_execution": True,
        "ultimate_book_live_activation_allowed": True,
        "ultimate_book_live_broker_authority": True,
        "ultimate_book_disable_broad_selector": True,
        "ultimate_book_profile": "clean3_w7_measured_nom1p25",
        "ultimate_book_include_clean3": True,
        "ultimate_book_derisk_mode": "band",
        "ultimate_book_include_candidate_book": False,
        "ultimate_book_include_market_expansion_book": False,
        "ultimate_book_stress_derisk": False,
        "ultimate_book_kelly_lite": True,
        "ultimate_book_kelly_conservative": True,
        "ultimate_book_drop_w7_symbols": True,
        "ultimate_book_max_entry_lateness_frac": 10.0,
        "selector_v4_enabled": True,
        "selector_v4_apply_to_execution": False,
        "selected_cell_pretrade_max_spread_r": 0.10,
        "selected_cell_pretrade_max_total_cost_r": 0.15,
    }


def _config():
    return {
        "market": {"symbol": "XAUUSD", "mt5_symbol": "XAUUSD"},
        "gtos_vnext_runtime": _runtime(),
    }


def _intent():
    return TradeIntent(
        sleeve="crypto",
        symbol="XAUUSD",
        direction=1,
        decision_day="2026-08-16",
        stop_dist=1.0,
        target_dist=2.0,
    )


def _unit(sleeve_members=None):
    members = list(sleeve_members or ["crypto"])
    return {
        "cluster": members[0],
        "sleeve_members": members,
        "n_trades": 1,
        "confidence": 0.9,
        "risk_pct_per_trade": 0.02,
        "unit_risk_pct": 0.02,
        "sized": True,
        "reason": "fixture_admitted",
        "unrounded": 0.013,
    }


def _quiet_owner(owner):
    owner._send_card = lambda _message: None
    owner._emit_cycle_runtime_learning = lambda *args, **kwargs: None
    owner._f5_emit_slate = lambda *args, **kwargs: None
    owner._f5_on_open = lambda *args, **kwargs: None
    owner._notify_cost_skip = lambda *args, **kwargs: None
    owner._notify_placed = lambda *args, **kwargs: None
    owner._notify_reject = lambda *args, **kwargs: None
    owner._spread_sample_sleep = lambda _seconds: None
    owner._spread_sample_extra_ticks_override = []
    return owner


def _f5_owner(tmp_path, mt5, execution_engine, *, flag=True, namespace="operator",
              intent=None, unit=None):
    owner = UltimateBookOwner(
        _config(),
        mt5,
        str(tmp_path),
        namespace=namespace,
        engine_factory=lambda _symbol: execution_engine,
        minimal_size=MinimalSizeConfig(
            enabled=True,
            target_risk_usd=10.0,
            notional_initial_usd=100_000.0,
        ),
        frozen_intent_reprice=flag,
    )
    stub = _FrozenEvalEngine(intent or _intent(), unit or _unit())
    owner.engine.evaluate = stub.evaluate
    owner.engine.reset_window_date = stub.reset_window_date
    owner.engine.broker_day_start_balance = stub.broker_day_start_balance
    owner.engine.config = stub.config
    owner.engine.record_placement_conviction = stub.record_placement_conviction
    return _quiet_owner(owner)


def _production_owner(tmp_path, mt5, execution_engine, *, flag=False):
    owner = UltimateBookOwner(
        _config(),
        mt5,
        str(tmp_path),
        namespace="operator_profile",
        engine_factory=lambda _symbol: execution_engine,
        frozen_intent_reprice=flag,
    )
    stub = _FrozenEvalEngine(_intent(), _unit())
    owner.engine.evaluate = stub.evaluate
    owner.engine.reset_window_date = stub.reset_window_date
    owner.engine.config = stub.config
    return _quiet_owner(owner)


# ---------------------------------------------------------------------------
# classifier (no owner)
# ---------------------------------------------------------------------------
def test_spread_screen_reason_is_quote_dependent():
    assert classify_cost_refusal(
        screen_reason="cost_screen_spread_r:0.230>0.100 (spread 0.23 vs crypto stop 1.0000)"
    ) == PACKET_CLASS_QUOTE_DEPENDENT


def test_spread_packet_reason_is_quote_dependent():
    assert classify_cost_refusal(
        reasons=["spread_r_exceeds_selected_cell_limit:0.200000>0.100000"],
        packet={"status": "REFUSED", "max_total_cost_r": 0.15, "total_cost_components": {
            "spread_r": 0.20, "commission_r": 0.01, "swap_cost_r": 0.0, "expected_slippage_r": 0.0,
        }},
    ) == PACKET_CLASS_QUOTE_DEPENDENT


def test_eurusd_class_commission_is_structural_and_never_quote_dependent():
    packet = {
        "status": "REFUSED",
        "max_total_cost_r": 0.15,
        "refusal_reasons": [f"total_cost_r_exceeds_limit:{EURUSD_COMMISSION_R:.6f}>0.150000"],
        "total_cost_components": {
            "spread_r": 0.02,
            "commission_r": EURUSD_COMMISSION_R,
            "swap_cost_r": 0.0,
            "expected_slippage_r": 0.0,
        },
        "commission_r": EURUSD_COMMISSION_R,
    }
    assert immutable_floor_clear(packet) is False
    assert classify_cost_refusal(packet=packet) == PACKET_CLASS_STRUCTURAL


def test_mixed_quote_and_missing_swap_is_structural():
    assert classify_cost_refusal(
        reasons=[
            "spread_r_exceeds_selected_cell_limit:0.200000>0.100000",
            "missing_side_aware_swap_cost_r_conversion:swap_mode",
        ]
    ) == PACKET_CLASS_STRUCTURAL


def test_unknown_family_is_structural_not_a_prefix_allowlist():
    assert classify_cost_refusal(reasons=["vnext_policy:geometry"]) == PACKET_CLASS_STRUCTURAL
    assert classify_cost_refusal(reasons=["something_spread_r_exceeds_selected_cell_limit"]) == (
        PACKET_CLASS_STRUCTURAL
    )


def test_no_reasons_is_none():
    assert classify_cost_refusal() == PACKET_CLASS_NONE


def test_blow_through_and_chase_are_price_gates():
    intent = _intent()
    tick = SimpleNamespace(bid=98.9, ask=99.1)
    geom = geometry_from_intent_tick(intent, SimpleNamespace(bid=100.0, ask=100.08))
    assert geom is not None
    assert is_blow_through(direction=1, tick=tick, stop_loss=geom["stop_loss"]) is True
    chase = chase_stop_fraction(
        direction=1, tick=SimpleNamespace(bid=100.15, ask=100.20),
        frozen_entry=100.08, stop_dist=1.0,
    )
    assert chase == pytest.approx(0.12)
    assert chase > 0.10


# ---------------------------------------------------------------------------
# owner wiring
# ---------------------------------------------------------------------------
def test_flag_off_production_consumes_the_bar(tmp_path):
    engine = _RecordingEngine()
    owner = _production_owner(tmp_path, _MT5(spread=0.20), engine, flag=False)
    summary = owner.run_cycle(now_utc=START)
    assert summary["placed"] == []
    assert engine.calls == []
    assert summary["bar_consumable"] is True
    assert owner._frozen_intents == {}
    assert owner._frozen_intent_reprice is False
    assert any(
        isinstance(row, dict) and str(row.get("reason", "")).startswith("cost_screen_spread_r")
        for row in summary["skipped"]
    )


def test_flag_on_production_book_is_inert(tmp_path):
    engine = _RecordingEngine()
    owner = _production_owner(tmp_path, _MT5(spread=0.20), engine, flag=True)
    summary = owner.run_cycle(now_utc=START)
    assert owner._frozen_intent_reprice_requested is True
    assert owner._frozen_intent_reprice is False
    assert owner._frozen_intents == {}
    assert summary["bar_consumable"] is True
    assert engine.calls == []


def test_cost_skip_enqueues_and_does_not_consume_the_bar(tmp_path):
    engine = _RecordingEngine()
    owner = _f5_owner(tmp_path, _MT5(spread=0.20), engine, flag=True)
    summary = owner.run_cycle(now_utc=START)
    assert owner._frozen_intent_reprice is True
    assert len(owner._frozen_intents) == 1
    item = next(iter(owner._frozen_intents.values()))
    assert item.state == STATE_REFUSED_COST
    assert item.packet_class == PACKET_CLASS_QUOTE_DEPENDENT
    assert item.frozen_entry == pytest.approx(100.20)
    assert item.frozen_stop == pytest.approx(99.20)
    assert summary["bar_consumable"] is False
    assert engine.calls == []
    assert any(row.get("frozen_price_intent_status") == STATE_REFUSED_COST for row in summary["skipped"])


def test_first_occurrence_only(tmp_path):
    engine = _RecordingEngine()
    owner = _f5_owner(tmp_path, _MT5(spread=0.20), engine, flag=True)
    first = owner.run_cycle(now_utc=START)
    second = owner.run_cycle(now_utc=START + timedelta(seconds=30))
    assert len(owner._frozen_intents) == 1
    assert first["bar_consumable"] is False
    assert second["bar_consumable"] is False
    item = next(iter(owner._frozen_intents.values()))
    assert item.frozen_entry == pytest.approx(100.20)


def test_blow_through_kills_without_enqueue(tmp_path):
    engine = _RecordingEngine()
    owner = _f5_owner(tmp_path, _MT5(spread=1.20), engine, flag=True)
    summary = owner.run_cycle(now_utc=START)
    assert owner._frozen_intents == {}
    assert summary["bar_consumable"] is True
    assert engine.calls == []
    assert any(
        row.get("frozen_price_intent_status") == "killed_blow_through"
        for row in summary["skipped"]
        if isinstance(row, dict)
    )


def test_structural_commission_never_enqueues(tmp_path):
    packet = {
        "status": "REFUSED",
        "max_total_cost_r": 0.15,
        "refusal_reasons": [f"total_cost_r_exceeds_limit:{EURUSD_COMMISSION_R:.6f}>0.150000"],
        "total_cost_components": {
            "spread_r": 0.02,
            "commission_r": EURUSD_COMMISSION_R,
            "swap_cost_r": 0.0,
            "expected_slippage_r": 0.0,
        },
        "commission_r": EURUSD_COMMISSION_R,
    }
    engine = _CostPacketEngine(packet)
    owner = _f5_owner(tmp_path, _MT5(spread=0.02), engine, flag=True)
    summary = owner.run_cycle(now_utc=START)
    assert owner._frozen_intents == {}
    assert engine.calls, "authoritative place path must run when the spread screen clears"
    assert summary["bar_consumable"] is True
    assert any(
        row.get("frozen_price_intent_status") == "killed_structural"
        for row in summary["skipped"]
        if isinstance(row, dict)
    )


def test_original_geometry_frozen_before_wait_and_fresh_clock_published(tmp_path):
    engine = _RecordingEngine()
    mt5 = _MT5(spread=0.20)
    owner = _f5_owner(tmp_path, mt5, engine, flag=True)
    first = owner.run_cycle(now_utc=START)
    assert first["bar_consumable"] is False
    item = next(iter(owner._frozen_intents.values()))
    frozen_entry = item.frozen_entry
    frozen_stop = item.frozen_stop
    mt5.spread = 0.02
    second = owner.run_cycle(now_utc=START + timedelta(seconds=15))
    assert second["placed"], second
    assert engine.calls
    sent = engine.calls[0]
    assert sent["entry_price"] == pytest.approx(frozen_entry)
    assert sent["stop_loss"] == pytest.approx(frozen_stop)
    assert sent["entry_price"] != pytest.approx(100.02)
    assert sent["decision_close_to_send_ms"] is not None
    assert sent["frozen_price_intent"] is True
    assert second["placed"][0]["decision_close_to_send_ms"] == sent["decision_close_to_send_ms"]
    assert next(iter(owner._frozen_intents.values())).state == STATE_FILLED


def test_chase_beyond_tenth_of_stop_invalidates(tmp_path):
    engine = _RecordingEngine()
    mt5 = _MT5(spread=0.20)
    owner = _f5_owner(tmp_path, mt5, engine, flag=True)
    owner.run_cycle(now_utc=START)
    item = next(iter(owner._frozen_intents.values()))
    # Move the whole quote 0.15 against the long (more than 0.10 R) while
    # keeping spread tight enough that the cost screen would pass.
    mt5.spread = 0.02

    def _chased(_symbol):
        # Frozen entry was 100.20. An ask of 100.35 is +0.15 R adverse (> 0.10).
        return SimpleNamespace(bid=100.33, ask=100.35, time=datetime.now(timezone.utc))

    mt5.get_tick = _chased
    summary = owner.run_cycle(now_utc=START + timedelta(seconds=10))
    assert engine.calls == []
    assert item.state == STATE_PRICE_INVALIDATED
    assert "chase_stop_fraction" in item.last_reason
    assert summary["placed"] == []


def test_hard_expiry_is_120s_not_half_timeframe(tmp_path):
    engine = _RecordingEngine()
    owner = _f5_owner(tmp_path, _MT5(spread=0.20), engine, flag=True)
    owner.run_cycle(now_utc=START)
    item = next(iter(owner._frozen_intents.values()))
    still_open = owner.run_cycle(now_utc=START + timedelta(seconds=119))
    assert item.is_open
    assert still_open["bar_consumable"] is False
    expired = owner.run_cycle(now_utc=START + timedelta(seconds=121))
    assert item.state == STATE_EXPIRED
    assert engine.calls == []
    assert any(
        row.get("frozen_price_intent_status") == STATE_EXPIRED
        for row in expired["skipped"]
        if isinstance(row, dict)
    )


def test_f5_flag_absent_does_not_enqueue(tmp_path):
    engine = _RecordingEngine()
    owner = _f5_owner(tmp_path, _MT5(spread=0.20), engine, flag=False)
    summary = owner.run_cycle(now_utc=START)
    assert owner._frozen_intent_reprice is False
    assert owner._frozen_intents == {}
    assert summary["bar_consumable"] is True
    assert engine.calls == []


def test_supervisor_named_tap_is_ftmo_f5_only():
    """The committed supervisor arms the seam for NOBODY; the tap moved to host argv.

    STALE EXPECTATION repaired 2026-08-25. b8f56ea35 (2026-08-16) armed
    `frozenIntentReprice=$true` on the committed operator supervisor row and
    this test pinned that wiring. The f5max-base overlay (338553883, 2026-08-25)
    replaced scripts/ with the live host surface (f5-live@68bad3751), where the F5
    book is launched by the HOST-ONLY wrapper `run_f5_ftmo.ps1` (uncommitted VPS
    bytes beside the repo) which passes `--frozen-intent-reprice` itself — measured
    running argv: docs/audits/fable-20260824/AUDIT-FINDINGS.md ("--frozen-intent-
    reprice ON", F5 row) and docs/audits/fable-20260824/RECEIPT.md ("ON on F5
    only"). The committed supervisor therefore carries no frozen-intent wiring at
    all, and what this test now keeps of the original protection is:
      (1) production stays off — NO committed row (production above all) can arm
          the seam through the supervisor;
      (2) the engine wire still exists for the host wrapper to pull: run_book.py
          exposes `--frozen-intent-reprice` (default OFF; book_owner.py keeps it
          F5-only — behaviourally pinned by test_flag_on_production_book_is_inert
          and test_f5_flag_absent_does_not_enqueue above).
    """
    text = Path("scripts/run_book_supervisor.ps1").read_text(encoding="utf-8")
    # (1) No committed row arms the seam. Both the launch-arg wire and any row key
    # must be absent — reappearance of either is a contract change to re-review.
    assert "--frozen-intent-reprice" not in text
    assert "frozenIntentReprice" not in text
    # Shape check, updated 2026-08-25: THREE namespaces now — the redacted_account_f5_minimal
    # row was REMOVED (pair down by decision, CEREMONY-RECEIPT-20260825; a committed row
    # that could re-arm a decided-down book on supervisor restart was a hazard). Its
    # reappearance is a contract change to re-review, exactly like the seam keys above.
    start = text.index("$books = @(")
    end = text.index("function Test-BookRunning", start)
    books = text[start:end]
    rows = [line for line in books.splitlines() if "ns=" in line]
    assert any('ns="operator"' in line for line in rows)
    assert any('ns="operator_profile"' in line for line in rows)
    assert any('ns="redacted_account_live_bee34003"' in line for line in rows)
    assert not any('ns="redacted_account_f5_minimal"' in line for line in rows), (
        "FN F5 row reappeared — that pair is down by decision; re-adding needs an "
        "owner word + receipt (CEREMONY-RECEIPT-20260825)")
    # (2) The wire exists in the launcher the wrapper drives (argparse registers it).
    import subprocess
    import sys

    entrypoint = Path(__file__).resolve().parents[2] / "run_book.py"
    completed = subprocess.run(
        [sys.executable, str(entrypoint), "--help"],
        cwd=entrypoint.parent,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    assert "--frozen-intent-reprice" in completed.stdout


# ---------------------------------------------------------------------------
# tight-floor / MODEL_INPUT_INVALID (the eight August IDs)
# ---------------------------------------------------------------------------
# asia_pdl_fade stop = (close-low) + 0.10*ATR. asian_fade stop = 0.6*ATR.
# The model emitted 2-4 pips. Not a 10x point-vs-pip rewrite.

TIGHT_FLOOR_EIGHT = (
    ("W7_BOOK::liquidity_sweep::NZDUSD::2026-08-12::LONG::asia_pdl_fade", "NZDUSD", "asia_pdl_fade", 1, 0.0002),
    ("W7_BOOK::fx_reversion::GBPUSD::2026-08-12::SHORT::asian_fade", "GBPUSD", "asian_fade", -1, 0.0002),
    ("W7_BOOK::liquidity_sweep::GBPUSD::2026-08-12::LONG::asia_pdl_fade", "GBPUSD", "asia_pdl_fade", 1, 0.0004),
    ("W7_BOOK::liquidity_sweep::NZDUSD::2026-08-13::LONG::asia_pdl_fade", "NZDUSD", "asia_pdl_fade", 1, 0.0002),
    ("W7_BOOK::fx_reversion::EURUSD::2026-08-13::LONG::asian_fade", "EURUSD", "asian_fade", 1, 0.0002),
    ("W7_BOOK::fx_reversion::GBPUSD::2026-08-13::LONG::asian_fade", "GBPUSD", "asian_fade", 1, 0.0002),
    ("W7_BOOK::liquidity_sweep::USDCAD::2026-08-13::LONG::asia_pdl_fade", "USDCAD", "asia_pdl_fade", 1, 0.0003),
    ("W7_BOOK::fx_reversion::GBPUSD::2026-08-14::SHORT::asian_fade", "GBPUSD", "asian_fade", -1, 0.0002),
)


def test_five_digit_two_to_four_pip_is_not_a_market_stop():
    for _cid, symbol, _sleeve, _direction, stop_dist in TIGHT_FLOOR_EIGHT:
        assert is_market_stop(stop_dist, digits=5, point=0.00001, symbol=symbol) is False
        assert is_market_stop(stop_dist, symbol=symbol) is False


def test_jpy_atr_stop_is_a_market_stop():
    assert is_market_stop(0.0616, digits=3, point=0.001, symbol="GBPJPY") is True
    assert is_market_stop(0.0515, digits=3, point=0.001, symbol="USDJPY") is True


def test_gold_and_missing_geometry_are_not_this_class():
    assert is_market_stop(1.0, digits=2, point=0.01, symbol="XAUUSD") is True
    assert is_market_stop(1.0, symbol="XAUUSD") is True
    assert is_market_stop(None, symbol="EURUSD") is True


def test_tight_floor_reason_is_model_input_not_quote_dependent():
    for _cid, symbol, sleeve, _direction, stop_dist in TIGHT_FLOOR_EIGHT:
        reason = (
            f"cost_screen_spread_r:0.200>0.100 "
            f"(spread 0.0000 vs {sleeve} stop {stop_dist:.4f})"
        )
        assert classify_cost_refusal(
            screen_reason=reason,
            stop_dist=stop_dist,
            digits=5,
            point=0.00001,
            symbol=symbol,
        ) == PACKET_CLASS_MODEL_INPUT


def test_model_input_family_is_not_quote_dependent():
    assert classify_cost_refusal(
        screen_reason="model_input_invalid_stop:0.00020000 (2.00 pip not a market on EURUSD bid 1.17000 ask 1.17004)",
        symbol="EURUSD",
    ) == PACKET_CLASS_MODEL_INPUT


def test_existing_xau_spread_skip_stays_quote_dependent():
    assert classify_cost_refusal(
        screen_reason="cost_screen_spread_r:0.230>0.100 (spread 0.23 vs crypto stop 1.0000)",
        stop_dist=1.0,
        symbol="XAUUSD",
    ) == PACKET_CLASS_QUOTE_DEPENDENT


def test_tight_floor_eight_never_enqueue(tmp_path):
    for cid, symbol, sleeve, direction, stop_dist in TIGHT_FLOOR_EIGHT:
        engine = _RecordingEngine()
        mt5 = _MT5(spread=0.00004)
        mt5.bid = 1.17000
        intent = TradeIntent(
            sleeve=sleeve,
            symbol=symbol,
            direction=direction,
            decision_day="2026-08-16",
            stop_dist=stop_dist,
            target_dist=3.0 * stop_dist,
        )
        owner = _f5_owner(
            tmp_path, mt5, engine, flag=True, intent=intent, unit=_unit([sleeve]),
        )
        tick = mt5.get_tick(symbol)
        reason = owner._spread_cost_screen(intent, tick)
        assert reason and reason.startswith("model_input_invalid_stop"), (cid, reason)
        skipped_row = {
            "symbol": symbol,
            "sleeve": sleeve,
            "decision_bar_iso": BAR,
            "reason": reason,
        }
        summary = {"skipped": [], "bar_consumable": True}
        enqueued = owner._maybe_enqueue_frozen_price_intent(
            now=START,
            intent=intent,
            unit=_unit([sleeve]),
            tick=tick,
            dbar=BAR,
            dday="2026-08-16",
            ee=engine,
            account_state=None,
            reason=reason,
            packet=None,
            skipped_row=skipped_row,
            summary=summary,
        )
        assert enqueued is False, cid
        assert owner._frozen_intents == {}, cid
        assert engine.calls == [], cid
        assert skipped_row["frozen_price_intent_class"] == PACKET_CLASS_MODEL_INPUT
        assert skipped_row["frozen_price_intent_status"] == "killed_model_input"


@pytest.mark.parametrize(
    ("symbol", "sleeve", "stop_dist", "target_dist"),
    [
        ("EURUSD", "vss_fxcross_london_up_low", 0.00018814, None),
        ("GBPUSD", "vss_fxcross_london_up_low", 0.00023529, None),
        ("USDCAD", "vss_fxcross_london_up_low", 0.00032693, 3.0 * 0.00032693),
    ],
)
def test_f5_preorder_floor_widens_tight_fx_stop_before_router(
    tmp_path, symbol, sleeve, stop_dist, target_dist
):
    engine = _RecordingEngine()
    mt5 = _MT5(spread=0.00001)
    intent = TradeIntent(
        sleeve=sleeve,
        symbol=symbol,
        direction=1,
        decision_day="2026-08-16",
        stop_dist=stop_dist,
        target_dist=target_dist,
    )
    owner = _f5_owner(
        tmp_path,
        mt5,
        engine,
        flag=True,
        intent=intent,
        unit=_unit([sleeve]),
    )
    owner._profile_supports_symbol = lambda _symbol: True

    summary = owner.run_cycle(now_utc=START)

    assert summary["placed"], summary
    assert engine.calls, "the widened intent must reach the router/open_trade seam"
    params = engine.calls[0]
    floor = params["f5_market_stop_floor"]
    assert floor["namespace"] == "operator"
    assert floor["stop_dist_before"] == pytest.approx(stop_dist)
    assert floor["stop_dist_after"] == pytest.approx(0.0005)
    assert abs(params["entry_price"] - params["stop_loss"]) == pytest.approx(0.0005)
    assert not any(
        str(row.get("reason", "")).startswith("model_input_invalid_stop")
        for row in summary["skipped"]
        if isinstance(row, dict)
    )
    if target_dist is None:
        assert floor["target_policy"] == "dynamic_exit_profile"
    else:
        assert floor["target_policy"] == "preserve_r_multiple"
        assert floor["target_dist_after"] / floor["stop_dist_after"] == pytest.approx(3.0)


def test_f5_preorder_refuses_fx_dsp_stop_le_8pip_instead_of_widening(tmp_path):
    engine = _RecordingEngine()
    mt5 = _MT5(spread=0.00001)
    intent = TradeIntent(
        sleeve="dsp_expanding_up_staircase",
        symbol="EURUSD",
        direction=1,
        decision_day="2026-08-16",
        stop_dist=0.0005,
        target_dist=0.0015,
    )
    owner = _f5_owner(
        tmp_path, mt5, engine, flag=True, intent=intent,
        unit=_unit(["dsp_expanding_up_staircase"]),
    )
    owner._profile_supports_symbol = lambda _symbol: True
    summary = owner.run_cycle(now_utc=START)
    assert not engine.calls
    assert not summary.get("placed")
    reasons = [
        str(row.get("reason", ""))
        for row in summary.get("skipped", [])
        if isinstance(row, dict)
    ]
    assert any("fx_dsp_stop_le_8pip" in reason for reason in reasons), reasons


def test_preorder_floor_is_inert_outside_exact_ftmo_f5_namespace(tmp_path):
    intent = TradeIntent(
        sleeve="asian_fade",
        symbol="EURUSD",
        direction=1,
        decision_day="2026-08-16",
        stop_dist=0.00018814,
        target_dist=None,
    )
    owner = _production_owner(tmp_path, _MT5(spread=0.00001), _RecordingEngine())

    unchanged, observation = owner._f5_preorder_market_stop_floor(intent)

    assert unchanged is intent
    assert observation is None


def test_spr_reason_keeps_price_precision_and_bid_ask(tmp_path):
    engine = _RecordingEngine()
    mt5 = _MT5(spread=0.20)
    owner = _f5_owner(tmp_path, mt5, engine, flag=True)
    owner.run_cycle(now_utc=START)
    item = next(iter(owner._frozen_intents.values()))
    reason = item.last_reason or item.refusal_reasons[0]
    assert "bid " in reason and "ask " in reason
    assert "spread 0.2000" in reason or "spread 0.20000000" in reason
    obs = next(iter(owner._spread_observations.values()))
    assert obs["spr"] == pytest.approx(0.20)
    assert obs["bid"] == pytest.approx(100.0)
    assert obs["ask"] == pytest.approx(100.20)
    assert obs["spread_sample_kind"] == "min_over_ms"
    assert obs["spread_r_source"] == "book_owner._spread_cost_screen_min_over_ms"


# ---------------------------------------------------------------------------
# owner sample: min-over-N-ms. 0.35 stays. Aug-12 GBPJPY tape.
# ---------------------------------------------------------------------------
GBPJPY_STOP = 0.0616
GBPJPY_CAP = 0.35  # existing fx_jpy sleeve cap, not a new number
GBPJPY_NEED = GBPJPY_CAP * GBPJPY_STOP  # 0.02156 = 2.16 pips = $3.50


def _gbpjpy_owner(tmp_path, engine):
    intent = TradeIntent(
        sleeve="fx_jpy",
        symbol="GBPJPY",
        direction=-1,
        decision_day="2026-08-12",
        stop_dist=GBPJPY_STOP,
        target_dist=None,
    )
    owner = _f5_owner(tmp_path, _MT5(spread=0.015), engine, flag=True, intent=intent)
    rt = owner.base_config.setdefault("gtos_vnext_runtime", {})
    rt["selected_cell_pretrade_max_spread_r_by_sleeve"] = {
        "fx_jpy": 0.35,
        "fx_jpy_ny": 0.35,
    }
    return owner, intent


def test_gbpjpy_060000459_already_inside(tmp_path):
    """06:00:00.459 was 1.50 pips / $2.44. Already inside the $3.50 cap."""
    owner, intent = _gbpjpy_owner(tmp_path, _RecordingEngine())
    tick = SimpleNamespace(bid=215.293, ask=215.308, time=START)
    assert owner._spread_cost_screen(intent, tick) is None
    obs = next(iter(owner._spread_observations.values()))
    assert obs["spread_price"] == pytest.approx(0.015)
    assert obs["spread_r"] == pytest.approx(0.015 / GBPJPY_STOP)
    assert obs["spread_r"] < GBPJPY_CAP
    assert (0.015 / GBPJPY_STOP) * 10 == pytest.approx(2.435, abs=0.01)
    assert obs["spread_sample_kind"] == "min_over_ms"
    assert obs["spread_sample_ticks"] == 1


def test_gbpjpy_060022_flicker_is_not_a_refuse(tmp_path):
    """Owner snapshot 06:00:22.208 is $4.06. Min-over sees 06:00:23.105 at $3.41."""
    owner, intent = _gbpjpy_owner(tmp_path, _RecordingEngine())
    owner._spread_sample_extra_ticks_override = [
        SimpleNamespace(bid=215.303, ask=215.327, time=START),  # 2.40
        SimpleNamespace(bid=215.302, ask=215.326, time=START),  # 2.40
        SimpleNamespace(bid=215.305, ask=215.326, time=START),  # 2.10 inside
    ]
    tick = SimpleNamespace(bid=215.304, ask=215.329, time=START)  # 2.50 / $4.06
    first_r = 0.025 / GBPJPY_STOP
    assert first_r > GBPJPY_CAP
    assert owner._spread_cost_screen(intent, tick) is None
    obs = next(iter(owner._spread_observations.values()))
    assert obs["spread_price"] == pytest.approx(0.021)
    assert obs["spread_r"] == pytest.approx(0.021 / GBPJPY_STOP)
    assert obs["spread_r"] < GBPJPY_CAP
    assert (0.021 / GBPJPY_STOP) * 10 == pytest.approx(3.409, abs=0.01)
    assert obs["spread_sample_ticks"] == 4
    assert obs["spread_r_limit"] == pytest.approx(0.35)


def test_gbpjpy_hour_open_widen_still_refuses(tmp_path, monkeypatch):
    monkeypatch.setattr("src.judgment.cost_choices.withholds", lambda *args, **kwargs: True)
    """06:00:02.108 hour-open 3.30 pips / $5.36 stays a refuse. Cap is still 0.35."""
    owner, intent = _gbpjpy_owner(tmp_path, _RecordingEngine())
    owner._spread_sample_extra_ticks_override = [
        SimpleNamespace(bid=215.291, ask=215.325, time=START),  # 3.40
        SimpleNamespace(bid=215.290, ask=215.323, time=START),  # 3.30
    ]
    tick = SimpleNamespace(bid=215.288, ask=215.321, time=START)  # 3.30
    reason = owner._spread_cost_screen(intent, tick)
    assert reason and reason.startswith("cost_screen_spread_r:")
    obs = next(iter(owner._spread_observations.values()))
    assert obs["spread_price"] == pytest.approx(0.033)
    assert obs["spread_r"] > GBPJPY_CAP
    assert obs["spread_r_limit"] == pytest.approx(0.35)
    assert (0.033 / GBPJPY_STOP) * 10 == pytest.approx(5.357, abs=0.01)


def test_gbpjpy_hour_open_widen_does_not_restore_the_boolean(tmp_path, monkeypatch):
    """The spread number stays a fact. A non-winning side does not withhold."""
    monkeypatch.setattr("src.judgment.cost_choices.withholds", lambda *args, **kwargs: False)
    owner, intent = _gbpjpy_owner(tmp_path, _RecordingEngine())
    owner._spread_sample_extra_ticks_override = [
        SimpleNamespace(bid=215.291, ask=215.325, time=START),
        SimpleNamespace(bid=215.290, ask=215.323, time=START),
    ]
    tick = SimpleNamespace(bid=215.288, ask=215.321, time=START)
    assert owner._spread_cost_screen(intent, tick) is None
    obs = next(iter(owner._spread_observations.values()))
    assert obs["spread_r"] > GBPJPY_CAP



# ---------------------------------------------------------------------------
# series persist: harvest can tell poll from tax
# ---------------------------------------------------------------------------
AUG12 = datetime(2026, 8, 12, 6, 0, tzinfo=timezone.utc)


def _refusal_quote_rows(tmp_path, namespace="operator"):
    path = Path(tmp_path) / "shadow_logs" / "f5_minimal" / namespace / "events.jsonl"
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("event") == "f5_refusal_quote":
            rows.append(row)
    return rows


def _aug12_gbpjpy_ticks():
    return [
        SimpleNamespace(bid=215.293, ask=215.308, time=datetime(2026, 8, 12, 6, 0, 0, 459000, tzinfo=timezone.utc)),
        SimpleNamespace(bid=215.288, ask=215.321, time=datetime(2026, 8, 12, 6, 0, 2, 108000, tzinfo=timezone.utc)),
        SimpleNamespace(bid=215.291, ask=215.325, time=datetime(2026, 8, 12, 6, 0, 3, 157000, tzinfo=timezone.utc)),
        SimpleNamespace(bid=215.304, ask=215.329, time=datetime(2026, 8, 12, 6, 0, 22, 208000, tzinfo=timezone.utc)),
        SimpleNamespace(bid=215.305, ask=215.326, time=datetime(2026, 8, 12, 6, 0, 23, 105000, tzinfo=timezone.utc)),
    ]


def test_gbpjpy_aug12_series_is_poll_not_a_send(tmp_path):
    """06:00:22 series: min $2.44 / max $5.52, cap inside, not a send."""
    ticks = _aug12_gbpjpy_ticks()
    rollup = quote_series_rollup(
        ticks,
        need_spr=GBPJPY_NEED,
        stop_dist=GBPJPY_STOP,
        direction=-1,
        frozen_entry=215.293,
    )
    assert rollup["series_n"] >= 5
    assert rollup["min_usd"] == pytest.approx(2.44, abs=0.02)
    assert rollup["max_usd"] == pytest.approx(5.52, abs=0.02)
    assert rollup["cap_inside_oscillation"] is True
    assert rollup["first_clear_lag_s"] != "never"
    assert rollup["min_spr"] == pytest.approx(0.015)
    assert rollup["max_spr"] == pytest.approx(0.034)

    engine = _RecordingEngine()
    owner, intent = _gbpjpy_owner(tmp_path, engine)
    owner._spread_quote_series[("fx_jpy", "GBPJPY")] = [
        {
            "bid": t.bid,
            "ask": t.ask,
            "spread_price": t.ask - t.bid,
            "quote_at_utc": t.time,
        }
        for t in ticks
    ]
    skipped = {
        "symbol": "GBPJPY",
        "sleeve": "fx_jpy",
        "decision_bar_iso": "2026-08-12T06:00:00+00:00",
        "reason": "cost_screen_spread_r:0.406>0.350",
    }
    owner._persist_f5_refusal_quote(
        now=AUG12,
        intent=intent,
        unit=_unit(["fx_jpy"]),
        tick=ticks[3],
        dbar="2026-08-12T06:00:00+00:00",
        dday="2026-08-12",
        reason=skipped["reason"],
        packet=None,
        skipped_row=skipped,
    )
    assert engine.calls == []
    rows = _refusal_quote_rows(tmp_path)
    assert len(rows) == 1
    row = rows[0]
    assert row["spread_sample_kind"] == "min_over_ms"
    assert row["series_n"] >= 5
    assert row["min_usd"] == pytest.approx(2.44, abs=0.02)
    assert row["max_usd"] == pytest.approx(5.52, abs=0.02)
    assert row["cap_inside_oscillation"] is True
    assert row["cap_usd"] == pytest.approx(3.50, abs=0.01)
    assert row["need_spr"] == pytest.approx(GBPJPY_NEED)
    assert row["broker_mutation"] is False
    assert row["sleeve"] == "fx_jpy"
    assert row["symbol"] == "GBPJPY"
    assert row["side"] == "SHORT"


def test_eth_style_session_tax_series_never_clears():
    quotes = [
        SimpleNamespace(bid=2400.00, ask=2400.60, time=START + timedelta(seconds=i))
        for i in range(4)
    ]
    rollup = quote_series_rollup(
        quotes,
        need_spr=0.582,
        stop_dist=1.0,
        direction=1,
        frozen_entry=2400.60,
    )
    assert rollup["unique_n"] == 1
    assert rollup["min_spr"] == pytest.approx(0.60)
    assert rollup["max_spr"] == pytest.approx(0.60)
    assert rollup["first_clear_utc"] is None
    assert rollup["first_clear_lag_s"] == "never"
    assert rollup["cap_inside_oscillation"] is False


def test_one_tick_owner_is_live_tick_not_a_book(tmp_path):
    engine = _RecordingEngine()
    owner = _f5_owner(tmp_path, _MT5(spread=0.20), engine, flag=True)
    owner.run_cycle(now_utc=START)
    rows = _refusal_quote_rows(tmp_path)
    assert len(rows) == 1
    assert rows[0]["series_n"] == 1
    assert rows[0]["spread_sample_kind"] == "live_tick"
    assert rows[0]["bid"] == pytest.approx(100.0)
    assert rows[0]["ask"] == pytest.approx(100.20)
    assert rows[0]["packet_class"] == PACKET_CLASS_QUOTE_DEPENDENT
    assert rows[0]["broker_mutation"] is False


def test_production_namespace_does_not_persist_series(tmp_path):
    engine = _RecordingEngine()
    owner = _production_owner(tmp_path, _MT5(spread=0.20), engine, flag=False)
    summary = owner.run_cycle(now_utc=START)
    assert summary["bar_consumable"] is True
    assert _refusal_quote_rows(tmp_path, namespace="operator_profile") == []
    shadow = Path(tmp_path) / "shadow_logs" / "f5_minimal"
    assert not shadow.exists() or not any(shadow.rglob("events.jsonl"))


def test_persist_does_not_flip_bar_consumable(tmp_path):
    off = _f5_owner(tmp_path / "off", _MT5(spread=0.20), _RecordingEngine(), flag=False)
    off_summary = off.run_cycle(now_utc=START)
    assert off._frozen_intent_reprice is False
    assert off._frozen_intents == {}
    assert off_summary["bar_consumable"] is True
    rows = _refusal_quote_rows(tmp_path / "off")
    assert len(rows) == 1
    assert rows[0]["series_n"] == 1


def test_tight_floor_eurusd_widens_instead_of_persisting_model_input(tmp_path):
    engine = _RecordingEngine()
    mt5 = _MT5(spread=0.00004)
    mt5.bid = 1.17000
    intent = TradeIntent(
        sleeve="asian_fade",
        symbol="EURUSD",
        direction=1,
        decision_day="2026-08-16",
        stop_dist=0.0002,
        target_dist=0.0006,
    )
    owner = _f5_owner(
        tmp_path, mt5, engine, flag=True, intent=intent, unit=_unit(["asian_fade"]),
    )
    owner._profile_supports_symbol = lambda _symbol: True
    summary = owner.run_cycle(now_utc=START)
    assert owner._frozen_intents == {}
    assert len(engine.calls) == 1
    assert summary["placed"]
    assert summary["bar_consumable"] is True
    rows = _refusal_quote_rows(tmp_path)
    assert rows == []
    floor = engine.calls[0]["f5_market_stop_floor"]
    assert floor["stop_dist_before"] == pytest.approx(0.0002)
    assert floor["stop_dist_after"] == pytest.approx(0.0005)
    assert floor["target_dist_after"] == pytest.approx(0.0015)


def test_watch_tick_appends_series_and_updates_rollup(tmp_path):
    engine = _RecordingEngine()
    mt5 = _MT5(spread=0.20)
    owner = _f5_owner(tmp_path, mt5, engine, flag=True)
    owner.run_cycle(now_utc=START)
    first = _refusal_quote_rows(tmp_path)
    assert len(first) == 1
    assert first[0]["series_n"] == 1
    assert first[0]["event_kind"] == "lookback"
    owner.run_cycle(now_utc=START + timedelta(seconds=15))
    rows = _refusal_quote_rows(tmp_path)
    assert len(rows) >= 2
    last = rows[-1]
    assert last["event_kind"] == "watch_tick"
    assert last["series_n"] >= 2
    assert last["max_spr"] == pytest.approx(0.20)
    assert engine.calls == []


def test_flag_off_f5_still_persists_series(tmp_path):
    engine = _RecordingEngine()
    owner = _f5_owner(tmp_path, _MT5(spread=0.20), engine, flag=False)
    summary = owner.run_cycle(now_utc=START)
    assert owner._frozen_intent_reprice is False
    assert owner._frozen_intents == {}
    assert summary["bar_consumable"] is True
    rows = _refusal_quote_rows(tmp_path)
    assert len(rows) == 1
    assert rows[0]["bid"] == pytest.approx(100.0)
    assert rows[0]["ask"] == pytest.approx(100.20)
    assert rows[0]["packet_class"] == PACKET_CLASS_QUOTE_DEPENDENT
    assert rows[0]["spread_sample_kind"] == "live_tick"
    assert rows[0]["series_n"] == 1
    assert engine.calls == []


def test_as_row_includes_quote_snapshot():
    intent = _intent()
    tick = SimpleNamespace(bid=100.0, ask=100.20, time=START)
    item = build_frozen_price_intent(
        intent=intent,
        unit=_unit(),
        tick=tick,
        decision_bar_iso=BAR,
        decision_day="2026-08-16",
        now=START,
        reasons=["cost_screen_spread_r:0.200>0.100"],
        frozen_max_lots=0.01,
    )
    assert item is not None
    row = item.as_row()
    assert row["bid"] == pytest.approx(100.0)
    assert row["ask"] == pytest.approx(100.20)
    assert row["spread"] == pytest.approx(0.20)
    assert row["spread_r"] == pytest.approx(0.20)
    assert row["stop"] == pytest.approx(99.20)
    assert row["unrounded"] == pytest.approx(0.013)
    assert row["quote_at_utc"] == START.isoformat()
    assert row["side"] == "LONG"
    assert row["refusal_reasons"] == ["cost_screen_spread_r:0.200>0.100"]
