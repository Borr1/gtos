"""Stage 3 — book_engine: generation -> admission, default-off, exception-isolated."""
import random
import tempfile
from datetime import datetime, timezone, timedelta

from src.components.ultimate_book.bar_provider import TF_H4, get_closed_bars
from src.components.ultimate_book.book_engine import UltimateBookLiveEngine


# --------------------------------------------------------------------------------------
# TIME-INVARIANCE (do not reintroduce a wall-clock literal here)
#
# This fixture used to pin its FIRST bar at datetime(2026, 6, 1) and let `evaluate()`
# default `now_utc` to the wall clock. With 4 h bars that put the newest CLOSED bar's
# close at 2026-07-14T08:00Z, and the decision-bar recency guard
# (book_engine.py `if (now - bar_close).total_seconds() > 2 * ivl * 60`) then dropped
# EVERY symbol slot from 2026-07-14T16:00Z onward. The file's only assertion of a
# NON-zero intent went red at that instant; the assertions of `n_intents == 0` went
# VACUOUS and stayed green, so any regression in ultimate_book intent generation after
# mid-July was invisible on the declared live decision surface.
#
# The fixture is therefore END-anchored and every test derives `now_utc` from the grid
# the fixture actually serves (`_fixture_now`). Prices stay deterministic; nothing here
# reads the wall clock, so it cannot rot again.
# --------------------------------------------------------------------------------------
_LAST_CANDLE_OPEN = datetime(2026, 7, 14, 8, 0, tzinfo=timezone.utc)


def _momentum_candles(n=300, seed=3, start=60000.0, vol=300.0):
    """AR(1)-autocorrelated up-trending close diffs -> ac60 well above 0.15 + Donchian breakouts.

    END-anchored: the newest (still-forming) candle always opens at `_LAST_CANDLE_OPEN`
    whatever `n` is, so the decision bar — the newest CLOSED bar, the one before it —
    always closes at `_LAST_CANDLE_OPEN`, for any bar count the engine asks for.
    """
    rnd = random.Random(seed)
    out = []
    p = start
    ch = 0.0
    t0 = _LAST_CANDLE_OPEN - timedelta(hours=4 * (n - 1))
    for k in range(n):
        ch = 0.6 * ch + rnd.gauss(0.4 * vol, vol)     # positive-mean AR(1) momentum
        o = p
        c = max(1.0, o + ch)
        wick = abs(rnd.gauss(0, 0.2 * vol))
        h = max(o, c) + wick
        l = min(o, c) - wick
        out.append({"time": (t0 + timedelta(hours=4 * k)).isoformat(),
                    "open": o, "high": h, "low": l, "close": c, "volume": 100})
        p = c
    return out


class _FakeMT5:
    """Momentum series for BTCUSD (fires crypto), flat for others; fixed equity."""
    def __init__(self, equity=100000.0):
        self._equity = equity
    def get_candles(self, symbol, timeframe, count):
        if symbol == "BTCUSD":
            return _momentum_candles(count + 1, seed=3, start=60000.0, vol=300.0)
        return _momentum_candles(count + 1, seed=99, start=100.0, vol=0.05)
    def get_account_equity(self):
        return self._equity


def _fixture_now(mt5=None, *, symbol="BTCUSD", timeframe=TF_H4, count=260):
    """One minute after the CLOSE of the newest CLOSED bar this fixture actually serves.

    Derived through the SAME provider the engine uses, and the bar interval is read off
    the returned grid rather than restated, so the drop-the-forming-candle convention,
    the anchor and the timeframe are all sourced rather than assumed. Reading the wall
    clock here — or pinning a literal — is what made this file's zero-assertions vacuous.
    """
    _bars, times = get_closed_bars(mt5 or _FakeMT5(), symbol, timeframe, count)
    interval = times[-1] - times[-2]
    return times[-1] + interval + timedelta(minutes=1)


def _cfg(gates_on: bool) -> dict:
    return {
        "ultimate_book_enabled": gates_on,
        "ultimate_book_apply_to_execution": gates_on,
        "ultimate_book_live_activation_allowed": gates_on,
        # The FOURTH authority gate. It was absent, so `_cfg(True)` produced
        # decision_status=shadow_live_broker_authority_false and realized_units==[]
        # even with the other three on (bridge.py `if not live_broker_authority`).
        "ultimate_book_live_broker_authority": gates_on,
        "ultimate_book_disable_broad_selector": True,
        # bridge.REQUIRED_DIAL_KEYS — all nine must be present or an enabled book fails
        # closed with `fail_closed_missing_dial_keys` rather than defaulting the dial.
        "ultimate_book_profile": "clean3_w7_measured_nom1p25",
        "ultimate_book_derisk_mode": "band",
        "ultimate_book_include_clean3": True,
        "ultimate_book_include_candidate_book": False,
        "ultimate_book_include_market_expansion_book": False,
        "ultimate_book_kelly_lite": True,
        "ultimate_book_kelly_conservative": True,
        "ultimate_book_stress_derisk": False,
        "ultimate_book_drop_w7_symbols": True,
        # broad selector OFF so the bridge replacement-invariant passes
        "selector_v4_enabled": True,
        "selector_v4_apply_to_execution": False,
    }


def test_engine_default_off_is_shadow_zero_realized():
    """Zero REALIZED units because the authority gates are off — not because the book
    had nothing to decide. The shadow projection on the same cycle is the stated reason:
    it must be non-empty and sized, which is exactly what an empty/decayed book cannot fake."""
    eng = UltimateBookLiveEngine(_cfg(False), _FakeMT5(), tempfile.mkdtemp())
    res = eng.evaluate(tags=("crypto",), now_utc=_fixture_now())
    assert res["ok"] is True
    assert res["n_intents"] >= 1                              # the book DID evaluate candidates
    assert res["runtime_effect_now"] is False                 # gates off -> no realized effect
    assert res["reason"] == "shadow_book_disabled"            # zero for THIS reason
    assert len(res["decision"].realized_units) == 0
    # shadow projection still computed (would-size telemetry) — and it carries real size
    would = res["decision"].would_units
    assert any(u["sized"] and u["risk_pct_per_trade"] > 0 for u in would)


def test_engine_gates_on_produces_realized_units_for_crypto():
    eng = UltimateBookLiveEngine(_cfg(True), _FakeMT5(), tempfile.mkdtemp())
    res = eng.evaluate(tags=("crypto",), now_utc=_fixture_now())
    assert res["ok"] is True
    assert res["n_intents"] >= 1                               # crypto fired on the trending BTCUSD
    btc = [it for it in res["intents"] if it.symbol == "BTCUSD"]
    assert len(btc) == 1
    assert btc[0].sleeve == "crypto" and btc[0].stop_dist > 0
    assert res["runtime_effect_now"] is True
    realized = res["decision"].realized_units
    assert len(realized) >= 1
    assert any(u["sized"] and u["risk_pct_per_trade"] > 0 for u in realized)
    terminals = res["generation_terminals"]
    assert len(terminals) == res["generation"]["active_symbol_slot_count"] == 3
    assert {(row["sleeve"], row["symbol"], row["timeframe"]) for row in terminals} == {
        ("crypto", "BTCUSD", TF_H4),
        ("crypto", "DASHUSD", TF_H4),
        ("crypto", "ETHUSD", TF_H4),
    }
    assert {row["terminal_status"] for row in terminals} == {"candidate_emitted"}


def test_realized_units_require_the_live_broker_authority_gate():
    """One YAML boolean is the whole difference between shadow and realized risk on the
    live book. Same fixture, same instant, same three other gates ON: with
    `ultimate_book_live_broker_authority` FALSE the engine must return zero realized units
    and say so by name, while still computing the sized shadow projection; flipping only
    that key must produce realized, sized units."""
    now = _fixture_now()
    shadow_cfg = dict(_cfg(True), ultimate_book_live_broker_authority=False)
    shadow = UltimateBookLiveEngine(shadow_cfg, _FakeMT5(), tempfile.mkdtemp()).evaluate(
        tags=("crypto",), now_utc=now)
    assert shadow["n_intents"] >= 1                            # candidates existed to gate
    assert shadow["reason"] == "shadow_live_broker_authority_false"
    assert shadow["runtime_effect_now"] is False
    assert shadow["decision"].realized_units == []
    assert any(u["sized"] and u["risk_pct_per_trade"] > 0 for u in shadow["decision"].would_units)

    live = UltimateBookLiveEngine(_cfg(True), _FakeMT5(), tempfile.mkdtemp()).evaluate(
        tags=("crypto",), now_utc=now)
    assert live["runtime_effect_now"] is True
    assert any(u["sized"] and u["risk_pct_per_trade"] > 0 for u in live["decision"].realized_units)


def test_generation_telemetry_exposes_profile_unsupported_symbols():
    """Zero intents because every symbol slot was REJECTED as broker-unsupported — proven
    by the identical engine with a supporting resolver, which fires on the same bars. Without
    that control `n_intents == 0` is satisfied by a book that generated nothing at all, and
    by a book that records the skip in telemetry and then trades the symbol anyway."""
    class _Resolver:
        def __init__(self, supported):
            self._supported = supported
        def __call__(self, symbol):
            return symbol
        def supports(self, symbol):
            return self._supported

    now = _fixture_now()
    control = UltimateBookLiveEngine(_cfg(True), _FakeMT5(), tempfile.mkdtemp(),
                                     broker_symbol=_Resolver(True)).evaluate(tags=("crypto",), now_utc=now)
    assert control["n_intents"] >= 1                    # positive control: these slots DO fire
    assert control["generation"]["broker_unsupported_symbol_slot_count"] == 0

    eng = UltimateBookLiveEngine(_cfg(True), _FakeMT5(), tempfile.mkdtemp(),
                                 broker_symbol=_Resolver(False))
    res = eng.evaluate(tags=("crypto",), now_utc=now)
    telemetry = res["generation"]
    assert telemetry["active_symbol_slot_count"] == control["generation"]["active_symbol_slot_count"]
    assert telemetry["broker_unsupported_symbol_slot_count"] == telemetry["active_symbol_slot_count"]
    assert telemetry["profile_supported_symbol_slot_count"] == 0
    assert "BTCUSD" in telemetry["broker_unsupported_unique_symbols"]
    assert {s["reason"] for s in res["generation_skips"]} == {"profile_missing_instrument_config"}
    # the load-bearing one: recorded as skipped MUST mean not generated
    assert res["n_intents"] == 0
    assert len(res["generation_terminals"]) == telemetry["active_symbol_slot_count"]
    assert {row["terminal_status"] for row in res["generation_terminals"]} == {
        "profile_unsupported"
    }


def test_generation_terminals_conserve_silent_no_candidate_slots():
    class _FlatMT5(_FakeMT5):
        def get_candles(self, _symbol, _timeframe, count):
            return _momentum_candles(count + 1, seed=1, start=100.0, vol=0.0)

    mt5 = _FlatMT5()
    res = UltimateBookLiveEngine(_cfg(True), mt5, tempfile.mkdtemp()).evaluate(
        tags=("crypto",), now_utc=_fixture_now(mt5)
    )
    assert res["n_intents"] == 0
    assert (
        len(res["generation_terminals"])
        == res["generation"]["active_symbol_slot_count"]
        == 3
    )
    assert {row["terminal_status"] for row in res["generation_terminals"]} == {"no_candidate"}


def test_engine_exception_isolated_safe_noop():
    """Zero intents + safe no-op because the FEED blew up — proven by the identical engine
    on a healthy feed at the same instant, which fires. `n_intents == 0` alone is satisfied
    by an engine that generates nothing under any conditions."""
    class Boom:
        def get_candles(self, *a): raise RuntimeError("feed blew up")
        def get_account_equity(self): raise RuntimeError("equity blew up")

    now = _fixture_now()
    control = UltimateBookLiveEngine(_cfg(True), _FakeMT5(), tempfile.mkdtemp()).evaluate(
        tags=("crypto",), now_utc=now)
    assert control["ok"] is True and control["n_intents"] >= 1   # positive control: healthy feed fires

    res = UltimateBookLiveEngine(_cfg(True), Boom(), tempfile.mkdtemp()).evaluate(
        tags=("crypto",), now_utc=now)
    # generation swallows per-sleeve errors -> no intents; equity unavailable -> safe no-op, never raises
    assert res["ok"] is False
    assert res["runtime_effect_now"] is False and res["n_intents"] == 0
    assert "unavailable" in res["reason"] or "exception" in res["reason"]
    assert len(res["generation_terminals"]) == res["generation"]["active_symbol_slot_count"]
    assert {row["terminal_status"] for row in res["generation_terminals"]} == {
        "bars_unavailable"
    }


# ---- gross 4% open-risk cap (running cap + conviction-ordered drop) ----
class _Pos:
    def __init__(self, symbol, volume, price_open, sl):
        self.symbol = symbol; self.volume = volume; self.price_open = price_open; self.sl = sl


class _FakeMT5Pos(_FakeMT5):
    def __init__(self, positions, vpp, equity=100000.0):
        super().__init__(equity); self._positions = positions; self._vpp = vpp
    def get_open_positions(self):
        return self._positions
    def get_symbol_value_per_point(self, symbol):
        return self._vpp.get(symbol)


def test_open_risk_pct_sums_worst_case_stop():
    eng = UltimateBookLiveEngine(_cfg(False),
        _FakeMT5Pos([_Pos("GER40", 1.0, 25000.0, 25200.0)], {"GER40": 1.0}), tempfile.mkdtemp())
    # risk$ = vol(1.0) * |open-sl|(200) * vpp(1.0) = 200 ; /100000 = 0.002
    assert abs(eng._open_risk_pct(100000.0) - 0.002) < 1e-12


def test_open_risk_pct_failsafe_zero_without_broker_accessors():
    eng = UltimateBookLiveEngine(_cfg(False), _FakeMT5(), tempfile.mkdtemp())  # no position accessors
    assert eng._open_risk_pct(100000.0) == 0.0      # test/mock missing accessors -> legacy inert
    assert eng._open_risk_pct(0.0) == 0.0            # non-positive equity -> 0.0


def test_open_risk_pct_fails_closed_when_live_position_risk_is_unpriced():
    eng2 = UltimateBookLiveEngine(_cfg(False),
        _FakeMT5Pos([_Pos("WAT", 1.0, 10.0, 9.0)], {}), tempfile.mkdtemp())
    assert eng2._open_risk_pct(100000.0) == 0.04


def test_gross_cap_drops_lowest_conviction_first():
    from src.components.ultimate_book.admission import SizedUnit, _enforce_gross_open_risk_cap
    metals = SizedUnit("metals", ("metals_core",), 1, 1.00, 0.009, 0.009, True, "ok")
    idx = SizedUnit("index", ("idxrev",), 1, 0.15, 0.0014, 0.0014, True, "ok")
    # natural order puts the LOW-conviction 'index' first (alphabetical); available fits metals (0.009)
    # but then NOT idx (0.0014 > 0.001 left). The fix must keep metals_core and drop idxrev.
    out = _enforce_gross_open_risk_cap([idx, metals], available_gross_risk_pct=0.010)
    by = {u["sleeve_members"][0]: u for u in out}
    assert by["metals_core"]["sized"] is True and by["metals_core"]["unit_risk_pct"] == 0.009
    assert by["idxrev"]["sized"] is False and by["idxrev"]["reason"] == "gross_risk_cap_would_exceed"
    assert [u["sleeve_members"][0] for u in out] == ["idxrev", "metals_core"]  # original order preserved


def test_gross_cap_inert_with_ample_headroom():
    from src.components.ultimate_book.admission import SizedUnit, _enforce_gross_open_risk_cap
    units = [SizedUnit("index", ("idxrev",), 1, 0.15, 0.0014, 0.0014, True, "ok"),
             SizedUnit("metals", ("metals_core",), 1, 1.00, 0.009, 0.009, True, "ok")]
    out = _enforce_gross_open_risk_cap(units, available_gross_risk_pct=0.04)
    assert all(u["sized"] for u in out)   # nothing dropped when gross headroom is ample


# ---- DF-1: generation gated to the active book (dropped clean_3 must not generate/inflate conviction) ----

def test_generation_gated_to_active_registry_df1():
    """DF-1: when include_clean3=False the 3 clean_3 sleeves must NOT be in the generated set, else their
    phantom firing inflates the Kelly-lite conviction count and over-sizes the real units."""
    CLEAN3 = {"sub_xvol_pullback", "sub_mid_dn_revert", "vp_euidx_pocgrav"}
    CORE = {"metals_core", "metals_softband", "metals_ob_micro", "crypto",
            "energy_agri", "idxrev", "fx_jpy", "fx_jpy_ny"}
    eng_off = UltimateBookLiveEngine({"ultimate_book_include_clean3": False}, _FakeMT5(),
                                     tempfile.mkdtemp())
    names_off = eng_off._active_sleeve_names()
    assert not (CLEAN3 & names_off), f"clean_3 must not generate when dropped: {CLEAN3 & names_off}"
    assert CORE <= names_off, "all 8 core sleeves must still generate"

    eng_on = UltimateBookLiveEngine({"ultimate_book_include_clean3": True}, _FakeMT5(),
                                    tempfile.mkdtemp())
    assert CLEAN3 <= eng_on._active_sleeve_names(), "clean_3 must generate when included"


def test_joint_daily_gate_tightens_gross_cap_with_realized_loss():
    """JOINT gate: realized daily loss + worst-case new open stop must not breach the -5% daily limit.
    Flat day = unchanged; as the day's loss grows the new-entry gross cap shrinks (-> 0 near the limit)."""
    from src.components.ultimate_book.book_engine import UltimateBookLiveEngine as E
    from src.components.ultimate_book.admission import GovernorLimits, GovernorState
    base = GovernorLimits()
    hard = base.hard_daily_limit_pct

    def _gs(realized):
        return GovernorState(equity=100000.0, high_water=100000.0, realized_today_pct=realized,
                             open_risk_pct=0.0, max_dd_reference_equity=100000.0)

    # flat -> no tightening (validated full-size envelope preserved)
    assert E._joint_daily_limits(base, _gs(0.0)).gross_open_risk_cap_pct == base.gross_open_risk_cap_pct
    # down 2.9% -> cap = min(4%, hard - 2.9% - 0.5%)
    lim = E._joint_daily_limits(base, _gs(-0.029))
    expected = min(base.gross_open_risk_cap_pct, max(0.0, hard - 0.029 - 0.005))
    assert abs(lim.gross_open_risk_cap_pct - expected) < 1e-9
    # realized loss + permitted new gross stays inside the hard limit (minus buffer)
    assert lim.gross_open_risk_cap_pct + 0.029 <= hard - 0.005 + 1e-9
    # near the limit -> zero new open risk
    assert E._joint_daily_limits(base, _gs(-(hard))).gross_open_risk_cap_pct == 0.0


def test_governor_limits_use_flatten_maxdd_as_entry_buffer():
    eng = UltimateBookLiveEngine(
        {"ultimate_book_flatten_maxdd_pct": 0.09},
        _FakeMT5(),
        tempfile.mkdtemp(),
    )
    assert eng._governor_limits().max_dd_entry_block_pct == 0.09


def test_decision_bar_recency_skips_stale_bar():
    """Chronological guard: the SAME firing signal generates a crypto intent on a FRESH bar but is SKIPPED
    when that bar is grossly stale (symbol market closed / not advanced at the reference trigger)."""
    import datetime as dt
    import random as _r
    from src.components.ultimate_book.book_engine import UltimateBookLiveEngine
    now = dt.datetime(2026, 6, 15, 13, 0, tzinfo=dt.timezone.utc)

    def momo(n, anchor_last):
        rnd = _r.Random(3); out = []; p = 60000.0; ch = 0.0
        t0 = anchor_last - dt.timedelta(hours=4 * (n - 1))
        for k in range(n):
            ch = 0.6 * ch + rnd.gauss(0.4 * 300, 300); o = p; c = max(1.0, o + ch); w = abs(rnd.gauss(0, 60))
            out.append({"time": (t0 + dt.timedelta(hours=4 * k)).isoformat(),
                        "open": o, "high": max(o, c) + w, "low": min(o, c) - w, "close": c, "volume": 100})
            p = c
        return out

    class _MT5:
        def __init__(self, anchor): self.anchor = anchor
        def get_candles(self, symbol, tf, count): return momo(count + 1, self.anchor)
        def get_account_equity(self): return 100000.0

    fresh, _ = UltimateBookLiveEngine({"ultimate_book_include_clean3": False}, _MT5(now),
                                      tempfile.mkdtemp())._generate_intents(("crypto",), now)
    stale, _ = UltimateBookLiveEngine({"ultimate_book_include_clean3": False},
                                      _MT5(now - dt.timedelta(days=2)),
                                      tempfile.mkdtemp())._generate_intents(("crypto",), now)
    assert any(getattr(it, "symbol", None) == "BTCUSD" for it in fresh), "control: fresh bar should fire"
    assert not any(getattr(it, "symbol", None) == "BTCUSD" for it in stale), "stale bar must be skipped"
