"""F5 post-fill deviation guard + thin-hour limit-at-level routing (2026-08-25).

Broker-truth motivating case: LTCUSD ticket 178351323, sleeve asia_pdl_fade, market BUY
3.69 lots at thin Asian open. Intended entry ~51.51 / SL 51.3069 (stop distance 0.2031,
sized $74.93); FILLED at 51.81 -- entry slippage +1.48R, born at ~2.46x intended risk;
net -$307.53 = -4.10R on a $75 unit. Median |entry slippage| across 52 joined fills is
0.002R -- the tail is the problem, and these two guards are the tail's fixes.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.components.ultimate_book.admission import TradeIntent
from src.components.ultimate_book.book_owner import UltimateBookOwner
from src.components.ultimate_book.minimal_size import (
    F5_FX_DSP_SL_COOLDOWN_SYMBOLS,
    F5_FX_SL_COOLDOWN_HOURS,
    F5_MAX_FILL_DEVIATION_R,
    F5_METAL_INDEX_SIBLING_MINUTES,
    F5_STANDING_HOLD_SYMBOLS,
    F5_THIN_HOUR_LIMIT_EXPIRY_BARS,
    MinimalSizeConfig,
    THIN_HOUR_LIMIT_SLEEVES,
    f5_cooldown_minutes_for_close,
    f5_just_closed_sibling_reason,
    f5_just_closed_siblings_path,
    f5_record_just_closed,
    f5_standing_hold_reason,
)
from src.components.ultimate_book.order_router import native_pending_order_spec

F5_NS = "operator"

# The LTCUSD 178351323 broker truth, verbatim.
INTENDED = 51.51
SL = 51.3069
FILL = 51.81
STOP_DIST = INTENDED - SL            # 0.2031
VOLUME = 3.69
PRE_SEND_RISK = 74.93


class _MT5:
    def __init__(self, bid=51.51, ask=51.53, vpp=100.0):
        self.bid, self.ask, self._vpp = bid, ask, vpp

    def get_tick(self, _symbol):
        return SimpleNamespace(bid=self.bid, ask=self.ask, time=datetime.now(timezone.utc))

    def get_account_balance(self):
        return 100_000.0

    def get_account_equity(self):
        return 100_000.0

    def get_symbol_value_per_point(self, _symbol):
        return self._vpp


class _GuardEE:
    """The minimum of an execution engine the deviation guard touches."""

    def __init__(self, close_result=True, raise_on_close=False):
        self.active_trade = SimpleNamespace(
            entry_price=FILL, stop_loss=SL, direction="LONG",
            initial_volume=VOLUME, current_volume=VOLUME, sl_distance=STOP_DIST,
        )
        self.closed = []
        self._close_result = close_result
        self._raise = raise_on_close

    def close_position(self, reason):
        if self._raise:
            raise RuntimeError("broker exploded")
        self.closed.append(reason)
        if self._close_result:
            self.active_trade = None
        return self._close_result


def _config(authority=True):
    return {
        "market": {"symbol": "XAUUSD", "mt5_symbol": "XAUUSD"},
        "gtos_vnext_runtime": {
            "ultimate_book_enabled": True,
            "ultimate_book_apply_to_execution": True,
            "ultimate_book_live_activation_allowed": True,
            "ultimate_book_live_broker_authority": authority,
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
            "selector_v4_enabled": True,
            "selector_v4_apply_to_execution": False,
        },
    }


def _owner(tmp_path, namespace=F5_NS, authority=True, mt5=None):
    return UltimateBookOwner(
        _config(authority=authority),
        mt5 or _MT5(),
        str(tmp_path),
        namespace=namespace,
        engine_factory=lambda _symbol: _GuardEE(),
        minimal_size=MinimalSizeConfig(
            enabled=True, target_risk_usd=75.0, notional_initial_usd=100_000.0,
        ),
    )


def _events(tmp_path, namespace=F5_NS):
    p = Path(tmp_path) / "shadow_logs" / "f5_minimal" / namespace / "events.jsonl"
    if not p.is_file():
        return []
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


def _trade_params(**over):
    p = {
        "direction": "LONG", "entry_price": INTENDED, "stop_loss": SL,
        "symbol": "LTCUSD", "f5_actual_risk_usd": PRE_SEND_RISK,
        "f5_intended_risk_usd": 75.0,
    }
    p.update(over)
    return p


def _fill_result(fill=FILL):
    return {"trade_state": SimpleNamespace(
        entry_price=fill, stop_loss=SL, sl_distance=STOP_DIST,
        initial_volume=VOLUME, current_volume=VOLUME,
    )}


# ---------------------------------------------------------------------------
# 1. the honest fields
# ---------------------------------------------------------------------------
def test_fill_truth_fields_reproduce_the_ltcusd_forensic(tmp_path):
    owner = _owner(tmp_path)
    tp = _trade_params()
    owner._f5_fill_truth_fields(tp, _fill_result())
    # +1.48R adverse deviation, exactly the broker-truth number.
    assert tp["f5_fill_deviation_r"] == pytest.approx((FILL - INTENDED) / STOP_DIST, rel=1e-9)
    assert tp["f5_fill_deviation_r"] == pytest.approx(1.477, abs=0.01)
    # Born at ~2.48x the pre-send risk: |fill-SL|/|intended-SL| scaling of broker truth.
    expected = PRE_SEND_RISK * (FILL - SL) / STOP_DIST
    assert tp["f5_actual_risk_at_fill_usd"] == pytest.approx(expected, rel=1e-9)
    assert tp["f5_actual_risk_at_fill_usd"] / tp["f5_actual_risk_usd"] == pytest.approx(2.48, abs=0.01)
    # The pre-send field is KEPT, not replaced.
    assert tp["f5_actual_risk_usd"] == PRE_SEND_RISK


def test_fill_truth_fields_short_direction_sign(tmp_path):
    owner = _owner(tmp_path)
    # SHORT intended 100.00, SL 101.00; fill at 99.70 is ADVERSE for a short.
    tp = _trade_params(direction="SHORT", entry_price=100.0, stop_loss=101.0)
    result = {"trade_state": SimpleNamespace(
        entry_price=99.70, stop_loss=101.0, sl_distance=1.0,
        initial_volume=1.0, current_volume=1.0)}
    owner._f5_fill_truth_fields(tp, result)
    assert tp["f5_fill_deviation_r"] == pytest.approx(0.30, abs=1e-9)


def test_fill_truth_fields_vpp_fallback_when_presend_absent(tmp_path):
    owner = _owner(tmp_path, mt5=_MT5(vpp=100.0))
    tp = _trade_params()
    del tp["f5_actual_risk_usd"]
    owner._f5_fill_truth_fields(tp, _fill_result())
    assert tp["f5_actual_risk_at_fill_usd"] == pytest.approx((FILL - SL) * VOLUME * 100.0, rel=1e-9)


def test_fill_truth_fields_never_raise_on_garbage(tmp_path):
    owner = _owner(tmp_path)
    tp = _trade_params(entry_price="not-a-number")
    owner._f5_fill_truth_fields(tp, _fill_result())          # must not raise
    assert "f5_fill_deviation_r" not in tp
    owner._f5_fill_truth_fields(None, None)                  # must not raise
    owner._f5_fill_truth_fields({}, {"trade_state": None})   # must not raise


def test_fill_truth_fields_inert_without_f5(tmp_path):
    owner = UltimateBookOwner(_config(), _MT5(), str(tmp_path),
                              namespace="operator_profile")
    tp = _trade_params()
    owner._f5_fill_truth_fields(tp, _fill_result())
    assert "f5_fill_deviation_r" not in tp                   # no F5 ledger -> no stamp


# ---------------------------------------------------------------------------
# 2. the deviation guard
# ---------------------------------------------------------------------------
def test_guard_closes_a_breach_fill_and_emits(tmp_path):
    owner = _owner(tmp_path)
    ee = _GuardEE(close_result=True)
    tp = _trade_params(f5_fill_deviation_r=1.477, f5_actual_risk_at_fill_usd=185.6)
    owner._f5_fill_deviation_guard(ee=ee, ticket=178351323, sleeve="asia_pdl_fade",
                                   symbol="LTCUSD", trade_params=tp,
                                   decision_bar_iso="2026-08-24T23:00:00+00:00")
    assert ee.closed == ["f5_fill_deviation_breach"]
    events = [e for e in _events(tmp_path) if e["event"] == "f5_fill_deviation_breach"]
    assert len(events) == 1
    breach = events[0]
    assert breach["ticket"] == 178351323
    assert breach["close_status"] == "closed"
    assert breach["broker_mutation"] is True
    assert breach["f5_fill_deviation_r"] == pytest.approx(1.477)
    assert breach["f5_max_fill_deviation_r"] == F5_MAX_FILL_DEVIATION_R


def test_guard_leaves_a_normal_fill_alone(tmp_path):
    owner = _owner(tmp_path)
    ee = _GuardEE()
    # 0.138R is the measured max NORMAL slippage -- inside the cap, no action.
    tp = _trade_params(f5_fill_deviation_r=0.138)
    owner._f5_fill_deviation_guard(ee=ee, ticket=1, sleeve="s", symbol="LTCUSD",
                                   trade_params=tp, decision_bar_iso=None)
    assert ee.closed == []
    assert _events(tmp_path) == []


def test_guard_ignores_favourable_deviation(tmp_path):
    owner = _owner(tmp_path)
    ee = _GuardEE()
    tp = _trade_params(f5_fill_deviation_r=-2.0)             # filled BETTER than intended
    owner._f5_fill_deviation_guard(ee=ee, ticket=1, sleeve="s", symbol="LTCUSD",
                                   trade_params=tp, decision_bar_iso=None)
    assert ee.closed == []


def test_guard_no_action_when_unstamped(tmp_path):
    owner = _owner(tmp_path)
    ee = _GuardEE()
    owner._f5_fill_deviation_guard(ee=ee, ticket=1, sleeve="s", symbol="LTCUSD",
                                   trade_params=_trade_params(), decision_bar_iso=None)
    assert ee.closed == []                                    # absent input = no action


def test_guard_is_namespace_gated(tmp_path):
    # Same F5 config, but a NON-F5 namespace: the guard must never fire.
    owner = _owner(tmp_path, namespace="redacted_account_live_bee34003")
    ee = _GuardEE()
    tp = _trade_params(f5_fill_deviation_r=9.9)
    owner._f5_fill_deviation_guard(ee=ee, ticket=1, sleeve="s", symbol="LTCUSD",
                                   trade_params=tp, decision_bar_iso=None)
    assert ee.closed == []
    assert _events(tmp_path, namespace="redacted_account_live_bee34003") == []


def test_guard_suppresses_close_when_authority_false_but_still_emits(tmp_path):
    owner = _owner(tmp_path, authority=False)
    ee = _GuardEE()
    tp = _trade_params(f5_fill_deviation_r=1.0)
    owner._f5_fill_deviation_guard(ee=ee, ticket=7, sleeve="s", symbol="LTCUSD",
                                   trade_params=tp, decision_bar_iso=None)
    assert ee.closed == []                                    # H8: no mutation through the gate
    events = [e for e in _events(tmp_path) if e["event"] == "f5_fill_deviation_breach"]
    assert len(events) == 1
    assert events[0]["close_status"] == "close_suppressed_live_broker_authority_false"
    assert events[0]["broker_mutation"] is False


def test_guard_never_raises_and_reports_a_failed_close(tmp_path):
    owner = _owner(tmp_path)
    ee = _GuardEE(raise_on_close=True)
    tp = _trade_params(f5_fill_deviation_r=2.0)
    owner._f5_fill_deviation_guard(ee=ee, ticket=7, sleeve="s", symbol="LTCUSD",
                                   trade_params=tp, decision_bar_iso=None)   # must not raise
    events = [e for e in _events(tmp_path) if e["event"] == "f5_fill_deviation_breach"]
    assert len(events) == 1
    assert events[0]["close_status"] == "close_failed_position_still_open"
    assert "broker exploded" in events[0]["close_error"]


def test_guard_threshold_is_strictly_greater(tmp_path):
    owner = _owner(tmp_path)
    ee = _GuardEE()
    tp = _trade_params(f5_fill_deviation_r=F5_MAX_FILL_DEVIATION_R)   # exactly at the cap
    owner._f5_fill_deviation_guard(ee=ee, ticket=1, sleeve="s", symbol="LTCUSD",
                                   trade_params=tp, decision_bar_iso=None)
    assert ee.closed == []


# ---------------------------------------------------------------------------
# 3. thin-hour limit-at-level routing
# ---------------------------------------------------------------------------
def _intent(sleeve="asia_pdl_fade", direction=1, entry_price=None, expiry_bars=None):
    return TradeIntent(sleeve=sleeve, symbol="LTCUSD", direction=direction,
                       decision_day="2026-08-24", stop_dist=0.2031, target_dist=0.6093,
                       entry_price=entry_price, expiry_bars=expiry_bars)


def _tick(bid=51.51, ask=51.53):
    return SimpleNamespace(bid=bid, ask=ask)


def test_thin_hour_sleeve_gets_a_limit_at_the_passive_side(tmp_path):
    owner = _owner(tmp_path)
    routed = owner._f5_thin_hour_limit_intent(_intent(), _tick())
    assert routed.entry_price == pytest.approx(51.51)        # LONG -> bid, never crosses
    assert routed.expiry_bars == F5_THIN_HOUR_LIMIT_EXPIRY_BARS
    # ...and that stamp is exactly what arms T4's native pending rail.
    spec = native_pending_order_spec(routed)
    assert spec == {"entry_price": pytest.approx(51.51), "order_type": "BUY_LIMIT",
                    "expiry_bars": F5_THIN_HOUR_LIMIT_EXPIRY_BARS}


def test_thin_hour_short_uses_the_ask(tmp_path):
    owner = _owner(tmp_path)
    routed = owner._f5_thin_hour_limit_intent(_intent(direction=-1), _tick())
    assert routed.entry_price == pytest.approx(51.53)
    assert native_pending_order_spec(routed)["order_type"] == "SELL_LIMIT"


def test_thin_hour_only_the_named_sleeves(tmp_path):
    owner = _owner(tmp_path)
    assert "asia_pdl_fade" in THIN_HOUR_LIMIT_SLEEVES
    routed = owner._f5_thin_hour_limit_intent(_intent(sleeve="crypto"), _tick())
    assert routed.entry_price is None                        # untouched -> market as today


def test_thin_hour_is_namespace_gated(tmp_path):
    owner = _owner(tmp_path, namespace="operator_profile")
    routed = owner._f5_thin_hour_limit_intent(_intent(), _tick())
    assert routed.entry_price is None


def test_thin_hour_never_overrides_a_sleeve_stamped_level(tmp_path):
    owner = _owner(tmp_path)
    routed = owner._f5_thin_hour_limit_intent(_intent(entry_price=50.00), _tick())
    assert routed.entry_price == 50.00


def test_thin_hour_keeps_an_existing_expiry(tmp_path):
    owner = _owner(tmp_path)
    routed = owner._f5_thin_hour_limit_intent(_intent(expiry_bars=8), _tick())
    assert routed.expiry_bars == 8



def test_f5_standing_usdjpy_hold_blocks_f5_only(tmp_path, monkeypatch):
    owner = _owner(tmp_path)

    monkeypatch.setattr(
        "src.components.ultimate_book.minimal_size.fear_withholds",
        lambda *a, **k: a[0],
    )
    intent = TradeIntent(
        sleeve="dsp_climax_into_high_then_dump",
        symbol="USDJPY",
        direction=-1,
        decision_day="2026-08-26",
        stop_dist=0.08,
        target_dist=0.48,
    )
    hold, dec = owner._f5_standing_symbol_hold(intent)
    assert hold is True
    assert dec["action"] == "HOLD"
    assert dec["reason"] == "usdjpy_verification_hold_5pip_dsp_stop"
    assert dec.get("writer_block") is True
    flow_hold, flow_dec = owner._judgment_flow_hold(
        intent, {}, None, None, None, datetime.now(timezone.utc)
    )
    assert flow_hold is True
    assert "STANDING::" in str(flow_dec.get("join_key") or "")
    assert flow_dec["reason"] == "usdjpy_verification_hold_5pip_dsp_stop"
    assert flow_dec.get("writer_block") is True


def test_f5_standing_usdjpy_hold_leaves_other_symbols(tmp_path):
    from src.components.ultimate_book.minimal_size import f5_standing_hold_reason
    now = datetime(2026, 8, 26, 13, 0, tzinfo=timezone.utc)
    reason = f5_standing_hold_reason(
        F5_NS,
        "XAUUSD",
        direction=-1,
        family="dsp_wide_down_then_micro_bounce_then_through",
        sl=4340.0,
        entry=4330.0,
        stop_dist=10.0,
        now=now,
    )
    assert reason is None


def test_f5_standing_usdjpy_hold_is_namespace_gated(tmp_path):
    owner = _owner(tmp_path, namespace="operator_profile")
    intent = TradeIntent(
        sleeve="dsp_isolated_spike_high",
        symbol="USDJPY",
        direction=-1,
        decision_day="2026-08-26",
        stop_dist=0.08,
        target_dist=0.48,
    )
    hold, _dec = owner._f5_standing_symbol_hold(intent)
    assert hold is False


def test_usdjpy_writer_hold_beats_inbox_approve(tmp_path, monkeypatch):
    """USDJPY is a writer block. Inbox APPROVE must not arm place()."""

    monkeypatch.setattr(
        "src.components.ultimate_book.minimal_size.fear_withholds",
        lambda *a, **k: a[0],
    )
    owner = _owner(tmp_path)
    monkeypatch.setattr(
        owner,
        "_judgment_flow_decision",
        lambda *a, **k: {"action": "APPROVE", "reason": "inbox_would_fire", "verdict": "approve"},
    )
    intent = TradeIntent(
        sleeve="dsp_wide_down_then_micro_bounce_then_through",
        symbol="USDJPY",
        direction=-1,
        decision_day="2026-08-29",
        stop_dist=0.12,
        target_dist=0.48,
    )
    flow_hold, flow_dec = owner._judgment_flow_hold(
        intent, {}, None, None, None, datetime(2026, 8, 29, 10, 0, tzinfo=timezone.utc)
    )
    assert flow_hold is True
    assert flow_dec["reason"] == "usdjpy_verification_hold_5pip_dsp_stop"
    assert flow_dec.get("writer_block") is True
    assert F5_STANDING_HOLD_SYMBOLS == frozenset({"USDJPY"})


def test_writer_place_paths_are_behind_flow_hold():
    text = Path(
        r"host-local\redacted_host\repo\src\components\ultimate_book\book_owner.py"
    ).read_text(encoding="utf-8")
    assert text.count("self.router.place(") == 3
    assert text.count("if flow_hold:") == 2
    live_chunk, frozen_chunk = text.split("if flow_hold:", 2)[1], text.split("if flow_hold:", 2)[2]
    assert "continue" in live_chunk[:500]
    assert "return" in frozen_chunk[:500]
    assert live_chunk.find("continue") < live_chunk.find("self.router.place(")
    assert frozen_chunk.find("return") < frozen_chunk.find("self.router.place(")


def test_fx_sl_cooldown_is_4h_metals_are_15m():
    assert F5_FX_SL_COOLDOWN_HOURS == 4.0
    assert F5_METAL_INDEX_SIBLING_MINUTES == 15.0
    assert F5_FX_DSP_SL_COOLDOWN_SYMBOLS == frozenset({
        "USDJPY", "GBPUSD", "EURUSD", "USDCHF", "USDCAD", "EURGBP", "GBPJPY", "EURJPY",
    })
    assert f5_cooldown_minutes_for_close("GBPUSD", "stop_loss") == 240.0
    assert f5_cooldown_minutes_for_close("EURUSD", "stop_loss") == 240.0
    assert f5_cooldown_minutes_for_close("XAUUSD", "stop_loss") == 15.0
    assert f5_cooldown_minutes_for_close("US30", "stop_loss") == 15.0
    assert f5_cooldown_minutes_for_close("GBPUSD", "take_profit") == 15.0
    assert f5_cooldown_minutes_for_close("AUDUSD", "stop_loss") == 15.0


def test_writer_15m_sibling_and_fx_4h_sl_cooldown(tmp_path, monkeypatch):
    """Launcher block from just_closed_siblings.json. Not inbox HOLD."""

    def _cooldown_only(*args, **kwargs):
        if args and args[0] in {"just_closed_sibling", "fx_sl_same_symbol_cooldown", "standing_reason_hold"}:
            return args[0]
        return None

    monkeypatch.setattr(
        "src.components.ultimate_book.minimal_size.fear_withholds",
        _cooldown_only,
    )
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    path = f5_just_closed_siblings_path(repo_root=tmp_path, namespace=F5_NS)
    owner = _owner(tmp_path)
    monkeypatch.setattr(
        owner,
        "_judgment_flow_decision",
        lambda *a, **k: {"action": "APPROVE", "reason": "inbox_would_fire", "verdict": "approve"},
    )
    monkeypatch.setattr(
        "src.components.ultimate_book.minimal_size.f5_high_print_hold_reason",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(
        "src.components.ultimate_book.minimal_size.f5_clock_hold_reason",
        lambda *a, **k: None,
    )
    ns = F5_NS
    fam = "dsp_wide_down_then_micro_bounce_then_through"

    f5_record_just_closed(
        "XAUUSD", ticket=11, closed_utc=(now - timedelta(minutes=5)).isoformat(),
        path=path, extra={"close_action": "stop_loss", "broker_net_pnl_usd": -80},
    )
    assert f5_just_closed_sibling_reason("XAUUSD", now=now, path=path) == "just_closed_sibling"
    assert f5_standing_hold_reason(ns, "XAUUSD", direction=1, family=fam, sl=3300, now=now, path=path) == (
        "just_closed_sibling"
    )
    gold_later = f5_standing_hold_reason(
        ns, "XAUUSD", direction=1, family=fam, sl=3300,
        now=now + timedelta(minutes=16), path=path,
    )
    assert gold_later is None  # isolated re-entry after 15m paid on gold

    f5_record_just_closed(
        "GBPUSD", ticket=22, closed_utc=(now - timedelta(minutes=37)).isoformat(),
        path=path, extra={"close_action": "stop_loss", "broker_net_pnl_usd": -905},
    )
    assert f5_just_closed_sibling_reason("GBPUSD", now=now, path=path) == "fx_sl_same_symbol_cooldown"
    gbp_intent = TradeIntent(
        sleeve=fam, symbol="GBPUSD", direction=1, decision_day="2026-08-29",
        stop_dist=0.0012, target_dist=0.003,
    )
    hold, dec = owner._f5_standing_symbol_hold(gbp_intent, now=now)
    assert hold is True
    assert dec["reason"] == "fx_sl_same_symbol_cooldown"
    assert dec.get("writer_block") is True
    flow_hold, flow_dec = owner._judgment_flow_hold(gbp_intent, {}, None, None, None, now)
    assert flow_hold is True
    assert flow_dec["reason"] == "fx_sl_same_symbol_cooldown"
    gbp_after = f5_standing_hold_reason(
        ns, "GBPUSD", direction=1, family=fam, sl=1.35,
        now=now + timedelta(hours=4, minutes=1), path=path,
    )
    assert gbp_after is None

    us30_intent = TradeIntent(
        sleeve="idxrev", symbol="US30", direction=1, decision_day="2026-08-29",
        stop_dist=80.0, target_dist=200.0,
    )
    f5_record_just_closed(
        "US30", ticket=33, closed_utc=(now - timedelta(minutes=16)).isoformat(),
        path=path, extra={"close_action": "stop_loss"},
    )
    hold_us30, dec_us30 = owner._f5_standing_symbol_hold(us30_intent, now=now)
    assert hold_us30 is False
    assert dec_us30["action"] == "PASS"


def test_unmatched_ledger_close_still_records_sibling(tmp_path):
    owner = _owner(tmp_path)
    owner._f5_on_close(
        44, -12.5, symbol="EURUSD", sleeve="dsp_isolated_spike_high",
        close_action="stop_loss",
        closed_utc="2026-08-29T09:50:00+00:00",
    )
    path = f5_just_closed_siblings_path(repo_root=tmp_path, namespace=F5_NS)
    now = datetime(2026, 8, 29, 10, 0, tzinfo=timezone.utc)
    assert f5_just_closed_sibling_reason("EURUSD", now=now, path=path) == "fx_sl_same_symbol_cooldown"


def test_thin_hour_bad_tick_leaves_the_intent_alone(tmp_path):
    owner = _owner(tmp_path)
    routed = owner._f5_thin_hour_limit_intent(_intent(), SimpleNamespace(bid=None, ask=None))
    assert routed.entry_price is None
    routed = owner._f5_thin_hour_limit_intent(_intent(), SimpleNamespace(bid=-1.0, ask=0.0))
    assert routed.entry_price is None


# ---------------------------------------------------------------------------
# 4. persistence-gap probes (17/169 outcome rows flagged trade_record_missing)
# ---------------------------------------------------------------------------
def test_f5_fill_event_stamps_trade_record_presence_and_dir(tmp_path):
    owner = _owner(tmp_path)
    owner._persist_trade_record(178351323, _trade_params(), SimpleNamespace(
        sleeve="asia_pdl_fade", symbol="LTCUSD"), decision_bar_iso="b", decision_day="d")
    owner._f5_on_open(ticket=178351323, sleeve="asia_pdl_fade", symbol="LTCUSD",
                      trade_params=_trade_params(f5_nominal_risk_usd=299.3,
                                                 f5_actual_risk_usd=74.93,
                                                 f5_intended_risk_usd=75.0),
                      candidate_id="cid", decision_day="2026-08-24",
                      decision_bar_iso="2026-08-24T23:00:00+00:00")
    fills = [e for e in _events(tmp_path) if e["event"] == "f5_fill"]
    assert len(fills) == 1
    assert fills[0]["f5_trade_record_on_disk"] is True
    assert fills[0]["f5_trade_record_dir"].replace("\\", "/").endswith(
        "pipeline_state/ultimate_book/operator/trade_records")


def test_f5_fill_event_says_when_the_record_is_absent(tmp_path):
    owner = _owner(tmp_path)
    owner._f5_on_open(ticket=999, sleeve="s", symbol="LTCUSD",
                      trade_params=_trade_params(f5_nominal_risk_usd=1.0,
                                                 f5_actual_risk_usd=1.0,
                                                 f5_intended_risk_usd=1.0),
                      candidate_id="cid", decision_day="d", decision_bar_iso="b")
    fills = [e for e in _events(tmp_path) if e["event"] == "f5_fill"]
    assert fills[0]["f5_trade_record_on_disk"] is False


def test_lost_trade_record_write_emits_a_visible_event(tmp_path, monkeypatch):
    owner = _owner(tmp_path)
    monkeypatch.setattr(owner, "_write_trade_record", lambda *a, **k: False)
    owner._persist_trade_record(42, _trade_params(), SimpleNamespace(sleeve="s", symbol="X"),
                                decision_bar_iso="b", decision_day="d")
    events = [e for e in _events(tmp_path) if e["event"] == "f5_trade_record_persist_failed"]
    assert len(events) == 1
    assert events[0]["ticket"] == 42
    assert events[0]["error"] == "write_returned_false"


def test_trade_record_persist_exception_emits_and_never_raises(tmp_path, monkeypatch):
    owner = _owner(tmp_path)

    def _boom(*_a, **_k):
        raise RuntimeError("disk on fire")

    monkeypatch.setattr(owner, "_normalize_trade_record", _boom)
    owner._persist_trade_record(43, _trade_params(), SimpleNamespace(sleeve="s", symbol="X"),
                                decision_bar_iso="b", decision_day="d")   # must not raise
    events = [e for e in _events(tmp_path) if e["event"] == "f5_trade_record_persist_failed"]
    assert len(events) == 1
    assert "disk on fire" in events[0]["error"]


# ---------------------------------------------------------------------------
# WEEK-REPAIR 2026-08-29 writer admission
# ---------------------------------------------------------------------------
def test_week_repair_hard_off_asia_pdl_and_climax():
    from src.components.ultimate_book.minimal_size import f5_standing_hold_reason
    now = datetime(2026, 8, 26, 13, 0, tzinfo=timezone.utc)
    assert f5_standing_hold_reason(
        F5_NS, "UK100", direction=1, family="asia_pdl_fade",
        sl=10800, entry=10840, now=now,
    ) == "hard_off_sleeve"
    assert f5_standing_hold_reason(
        F5_NS, "XAUUSD", direction=1, family="dsp_climax_flush_to_96low_then_snap",
        sl=4578, entry=4583, now=now,
    ) == "hard_off_sleeve"


def test_week_repair_keep_paid_dsp_in_overlap():
    from src.components.ultimate_book.minimal_size import f5_standing_hold_reason
    now = datetime(2026, 8, 26, 13, 0, tzinfo=timezone.utc)
    assert f5_standing_hold_reason(
        F5_NS, "US30", direction=-1, family="dsp_expanding_up_staircase",
        sl=53678, entry=53653, stop_dist=25.0, now=now,
    ) is None


def test_week_repair_dead_window_and_friday_cutoff():
    from src.components.ultimate_book.minimal_size import f5_standing_hold_reason
    dead = datetime(2026, 8, 26, 21, 15, tzinfo=timezone.utc)
    assert f5_standing_hold_reason(
        F5_NS, "EURUSD", direction=1, family="dsp_bleed_accept_fresh_20low_second_push",
        sl=1.1635, entry=1.1647, stop_dist=0.0012, now=dead,
    ) == "f5_dead_window"
    friday = datetime(2026, 8, 28, 17, 0, tzinfo=timezone.utc)
    assert f5_standing_hold_reason(
        F5_NS, "SPX500", direction=-1, family="idxrev",
        sl=7747, entry=7707, stop_dist=40.0, now=friday,
    ) == "f5_friday_weekend_cutoff"


def test_week_repair_size_by_sleeve():
    from src.components.ultimate_book.minimal_size import f5_intended_risk_usd
    assert f5_intended_risk_usd("US30", "dsp_expanding_up_staircase") == 250.0
    assert f5_intended_risk_usd("XAUUSD", "dsp_wide_down_then_micro_bounce_then_through") == 250.0
    assert f5_intended_risk_usd("EURUSD", "dsp_bleed_accept_fresh_20low_second_push") == 250.0
    assert f5_intended_risk_usd("GBPUSD", "dsp_expanding_up_staircase") == 250.0


def test_week_repair_fx_dsp_8pip_refuse():
    from src.components.ultimate_book.minimal_size import f5_standing_hold_reason
    now = datetime(2026, 8, 26, 13, 0, tzinfo=timezone.utc)
    assert f5_standing_hold_reason(
        F5_NS, "EURUSD", direction=1, family="dsp_isolated_spike_high",
        sl=1.1655, entry=1.1650, stop_dist=0.00016, now=now,
    ) == "fx_dsp_dropped_j6"


def test_week_repair_high_window_by_symbol():
    from src.components.ultimate_book.minimal_size import f5_high_print_hold_reason
    warsh = datetime(2026, 8, 28, 14, 2, tzinfo=timezone.utc)
    assert f5_high_print_hold_reason(F5_NS, "GBPUSD", now=warsh) == "f5_named_high_window"
    far = datetime(2026, 8, 26, 13, 0, tzinfo=timezone.utc)
    assert f5_high_print_hold_reason(F5_NS, "GBPUSD", now=far) is None
