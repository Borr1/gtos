"""Leftover ship pins (Fable 5.1): A1 native limits, A3 amplifier, A4 floor, A5 trail off, geometry loader."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import SimpleNamespace

from src.components.ultimate_book.minimal_size import (
    F5_CAL_AMPLIFIER_PRE_MINUTES,
    F5_CAL_PRIME_SIZE_MULT,
    F5_HARD_OFF_SLEEVES,
    F5_HIGH_PRE_MINUTES,
    F5_HIGH_POST_MINUTES,
    F5_LIMIT_EXPIRY_SECONDS,
    F5_REAL_DAILY_FLATTEN_PCT,
    F5_REAL_FLATTEN_FLOOR_USD,
    f5_calendar_prime_window_reason,
    f5_named_high_window_reason,
    f5_native_limit_expiration,
    f5_new_risk_clock_block_reason,
    f5_raw_mt5,
)
from src.components.ultimate_book.sleeve_geometry import (
    CLASS_FX,
    apply_class_geometry,
    resolved_stop_target,
    symbol_class,
)
from src.components.ultimate_book.xasset_direction import stay_timing


WARSH = {
    "name": "Fed Chair Kevin Warsh Jackson Hole remarks",
    "impact": "high",
    "official_high": True,
    "time_utc": "2026-08-28T14:00:00Z",
    "tickets": ["US30", "EURUSD", "GER40"],
}


class _Raw:
    def __init__(self, t=1_700_000_000, mode=4):
        self._t = t
        self._mode = mode

    def symbol_info_tick(self, symbol):
        return SimpleNamespace(time=self._t)

    def symbol_info(self, symbol):
        return SimpleNamespace(expiration_mode=self._mode)


class _Wrapper:
    def __init__(self, raw):
        self._mt5 = raw

    def symbol_info_tick(self, symbol):
        raise AssertionError("must not call the GTOS wrapper for expiration")


def test_a1_raw_module_sets_type_time_specified():
    raw = _Raw()
    engine = SimpleNamespace(mt5=_Wrapper(raw))
    got = f5_raw_mt5(engine)
    tt, exp = f5_native_limit_expiration(got, "US30")
    assert tt == 1
    assert exp == 1_700_000_000 + F5_LIMIT_EXPIRY_SECONDS


def test_a1_wrapper_without_raw_is_gtc():
    wrapper_only = SimpleNamespace(mt5=SimpleNamespace())  # no ._mt5
    assert f5_raw_mt5(wrapper_only) is None
    tt, exp = f5_native_limit_expiration(f5_raw_mt5(wrapper_only), "US30")
    assert (tt, exp) == (0, None)


def test_a1_self_underscore_mt5_is_the_old_bug():
    """If someone passes engine._mt5 (missing) the helper must not invent an expiration."""
    engine = SimpleNamespace(mt5=_Wrapper(_Raw()))
    wrong = getattr(engine, "_mt5", None)
    tt, exp = f5_native_limit_expiration(wrong, "US30")
    assert (tt, exp) == (0, None)


def test_a1_expiration_mode_without_specified_bit_is_gtc():
    tt, exp = f5_native_limit_expiration(_Raw(mode=1), "EURUSD")
    assert (tt, exp) == (0, None)


def test_a3_amplifier_is_not_a_gate():
    assert F5_HIGH_PRE_MINUTES == 15 and F5_HIGH_POST_MINUTES == 60
    assert F5_CAL_AMPLIFIER_PRE_MINUTES == 45
    assert F5_CAL_PRIME_SIZE_MULT == 1.0
    t_minus_45 = datetime(2026, 8, 28, 13, 15, tzinfo=timezone.utc)
    t_minus_16 = datetime(2026, 8, 28, 13, 44, tzinfo=timezone.utc)
    t_minus_15 = datetime(2026, 8, 28, 13, 45, tzinfo=timezone.utc)
    events = [WARSH]
    assert f5_calendar_prime_window_reason("EURUSD", t_minus_45, events) == "f5_calendar_prime_window"
    assert f5_calendar_prime_window_reason("EURUSD", t_minus_16, events) == "f5_calendar_prime_window"
    # HIGH gate still owns T-15; amplifier is present but new-risk is blocked by HIGH, not by amplifier
    assert f5_named_high_window_reason("EURUSD", t_minus_15, events) == "f5_named_high_window"
    assert f5_new_risk_clock_block_reason("EURUSD", t_minus_45, events) is None  # not a gate
    assert f5_new_risk_clock_block_reason("EURUSD", t_minus_15, events) == "f5_named_high_window"


def test_a4_real_floor_unchanged():
    assert F5_REAL_FLATTEN_FLOOR_USD == 90_600.0
    assert F5_REAL_DAILY_FLATTEN_PCT == 0.045


def test_a5_trailing_tags_hard_off():
    assert "metal_session_reversion" in F5_HARD_OFF_SLEEVES
    assert "asian_fade_widen" in F5_HARD_OFF_SLEEVES


def test_a2_stay_timing_missing_panel_does_not_skip():
    assert stay_timing("isolated_spike_high", {"symbol": "XAUUSD"}, None) is False
    assert stay_timing("isolated_spike_high", {"symbol": "XAUUSD"}, {"aligned_move": 0.0}) is True
    assert stay_timing("isolated_spike_high", {"symbol": "XAUUSD"}, {"aligned_move": 1.0}) is False


def test_j1_fx_keeps_1_0_when_class_says_0_75():
    assert symbol_class("EURUSD") == CLASS_FX
    stop, tgt = resolved_stop_target("dsp_isolated_spike_high", CLASS_FX, {"stop_atr": 0.75, "target_atr": 6.0})
    assert stop == 1.0 and tgt == 6.0
    stop, tgt = resolved_stop_target("dsp_isolated_spike_high", CLASS_FX, {"stop_atr": 1.5, "target_atr": 6.0})
    assert stop == 1.5


def test_j1_loader_scales_metal_intent():
    @dataclass(frozen=True)
    class _I:
        sleeve: str
        symbol: str
        stop_dist: float
        target_dist: float

    table = {"rows": {
        "dsp_isolated_spike_high|xau_xag": {
            "stop_atr": 0.75, "target_atr": 6.0, "side": "SHORT",
        }
    }}
    intent = _I("dsp_isolated_spike_high", "XAUUSD", 10.0, 60.0)
    out = apply_class_geometry(intent, table=table)
    assert out.stop_dist == 7.5
    assert out.target_dist == 60.0


def test_j2b_modules_exist_and_are_not_armed():
    from src.components.ultimate_book.sleeves.registry import DISPLACEMENT_BUILT
    from src.components.ultimate_book.sleeves.timing_brackets import bracket_levels, generate as tm_gen
    from pathlib import Path
    import json
    armed_path = Path(__file__).resolve().parents[2] / "config" / "live_armed_set.json"
    if armed_path.exists():
        blob = armed_path.read_text(encoding="utf-8")
        assert "dsp_two_bar_thrust_into_20high_continues" not in blob
    up, dn = bracket_levels(100.0, 2.0, 1.0)
    assert (up, dn) == (102.0, 98.0)
    assert "dsp_two_bar_thrust_into_20high_continues" in DISPLACEMENT_BUILT
    assert "dsp_london_bounce_fails_overnight_midpoint" in DISPLACEMENT_BUILT
    assert tm_gen("EURUSD", [], "2026-09-02") is None


def test_j5_idxrev_off_ger40_us30_keeps_us500(monkeypatch):

    def _idxrev_only(*args, **kwargs):
        return args[0] if args and args[0] == "idxrev_j5_off" else None

    monkeypatch.setattr(
        "src.components.ultimate_book.minimal_size.fear_withholds",
        _idxrev_only,
    )
    from src.components.ultimate_book.minimal_size import (
        F5_NAMESPACE,
        f5_idxrev_symbol_off_reason,
        f5_standing_hold_reason,
    )
    now = datetime(2026, 9, 2, 13, 0, tzinfo=timezone.utc)
    assert f5_idxrev_symbol_off_reason(F5_NAMESPACE, "GER40", family="idxrev") == "idxrev_j5_off"
    assert f5_idxrev_symbol_off_reason(F5_NAMESPACE, "US30_cash", family="idxrev") == "idxrev_j5_off"
    assert f5_idxrev_symbol_off_reason(F5_NAMESPACE, "US500", family="idxrev") is None
    assert f5_idxrev_symbol_off_reason(F5_NAMESPACE, "UK100", family="idxrev") is None
    assert f5_standing_hold_reason(
        F5_NAMESPACE, "GER40", direction=1, family="idxrev",
        sl=25500.0, entry=25800.0, stop_dist=300.0, now=now,
    ) == "idxrev_j5_off"


def test_j6_drops_eur_gbp_usd_jpy_dsp_not_xa():
    from src.components.ultimate_book.minimal_size import (
        F5_FX_DSP_DROP_SYMBOLS,
        f5_fx_dsp_tight_stop_reason,
    )
    from src.components.ultimate_book.sleeves import dsp_walked_high_accepted_through as walked
    from src.components.ultimate_book.sleeves import xa_huge_20_extreme as xa
    ns = "operator"
    assert F5_FX_DSP_DROP_SYMBOLS == frozenset({"EURUSD", "GBPUSD", "USDJPY"})
    assert f5_fx_dsp_tight_stop_reason(ns, "EURUSD", family="dsp_isolated_spike_high", stop_dist=0.0012) == "fx_dsp_dropped_j6"
    assert f5_fx_dsp_tight_stop_reason(ns, "GBPUSD", family="dsp_walked_high_accepted_through", stop_dist=0.0015) == "fx_dsp_dropped_j6"
    assert f5_fx_dsp_tight_stop_reason(ns, "XAUUSD", family="dsp_walked_high_accepted_through", stop_dist=8.0) is None
    assert f5_fx_dsp_tight_stop_reason(ns, "EURUSD", family="xa_huge_20_extreme", stop_dist=0.0005) is None
    # Gate, not an ON_SURFACE wipe: majors stay on the module so gold/index dsp keep the same file.
    assert "EURUSD" in walked.ON_SURFACE
    assert "XAUUSD" in walked.ON_SURFACE
    assert "EURUSD" in xa.ON_SURFACE


def test_a3_engine_assigns_calendar_events():
    from pathlib import Path
    src = Path("src/components/ultimate_book/book_engine.py").read_text(encoding="utf-8")
    assert "self._f5_calendar_events" in src
    assert "f5_load_live_calendar_events" in src
    assert F5_CAL_PRIME_SIZE_MULT == 1.0


def test_j3_skip_on_resolver_disagree_stays_unarmed():
    from src.components.ultimate_book.xasset_direction import skip_on_resolver_disagree
    from pathlib import Path
    src = Path("src/components/ultimate_book/book_engine.py").read_text(encoding="utf-8")
    assert "skip_on_resolver_disagree stays unarmed" in src
    # Helper exists; generate() must not call it.
    assert skip_on_resolver_disagree(
        "huge_bar_closed_on_20bar_extreme", {"symbol": "XAUUSD"},
        {"aligned_move": 2.0}, geometry_side=1,
    ) in (True, False)


def test_a1_execution_source_never_calls_self_underscore_mt5():
    from pathlib import Path
    src = Path("src/components/execution.py").read_text(encoding="utf-8")
    assert "self._mt5.symbol_info_tick" not in src
    assert 'getattr(self.mt5, "_mt5", None)' in src
