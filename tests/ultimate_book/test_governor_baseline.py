"""Batch 1 — broker-correct daily baseline (balance anchor + deal reconstruction + fail-closed) and the
positive-only value-per-point cache. These guard the hard-halt failure class: anchoring the daily-loss
baseline to first-observed EQUITY (instead of day-start BALANCE) let a real -5% daily breach slip past the
-3% soft stop after a position carried across the boundary or a mid-day restart."""
import tempfile
from datetime import datetime, timedelta, timezone

import pytest

from src.components.ultimate_book.governor_state import GovernorStateBuilder
from src.components.ultimate_book.admission import evaluate_governor


def _now():
    return datetime(2026, 6, 15, 14, 0, tzinfo=timezone.utc)


# ---- broker-time/DST: reset window tracks the LIVE-detected offset (EET<->EEST), not a hardcoded +3 ----

def test_reset_window_uses_live_offset_dst_correct(tmp_path):
    # late-Oct WINTER (EET +2): a live provider reporting +2 must shift the reset-window day vs a static +3.
    now = datetime(2026, 11, 1, 21, 30, tzinfo=timezone.utc)
    g2 = GovernorStateBuilder(str(tmp_path), daily_reset_offset_hours=3.0, offset_provider=lambda: 2.0)
    assert g2.reset_window_date(now) == "2026-11-01"      # +2 -> server 23:30 -> still Nov-01
    g3 = GovernorStateBuilder(str(tmp_path), daily_reset_offset_hours=3.0, offset_provider=lambda: 3.0)
    assert g3.reset_window_date(now) == "2026-11-02"      # +3 -> server 00:30 -> Nov-02 (the DST bug)


def test_reset_window_falls_back_to_config_on_implausible_offset(tmp_path):
    now = datetime(2026, 6, 16, 21, 30, tzinfo=timezone.utc)   # +3 summer -> server 00:30 -> Jun-17
    for bad in (None, 0.0, 9.0, -1.0):                         # not-yet-detected / out-of-band -> config +3
        g = GovernorStateBuilder(str(tmp_path), daily_reset_offset_hours=3.0, offset_provider=lambda b=bad: b)
        assert g.reset_window_date(now) == "2026-06-17"


def test_no_provider_uses_static_config_unchanged(tmp_path):
    now = datetime(2026, 6, 16, 21, 30, tzinfo=timezone.utc)
    g = GovernorStateBuilder(str(tmp_path), daily_reset_offset_hours=3.0)   # back-compat: no provider
    assert g.reset_window_date(now) == "2026-06-17"


# ---- OPS-03 profit-target protect: de-risk hard once the challenge target is hit, keep trading ----

def _gstate(equity, ref=100000.0):
    from src.components.ultimate_book.admission import GovernorState
    return GovernorState(equity=equity, high_water=max(equity, ref), realized_today_pct=0.0,
                         open_risk_pct=0.0, max_dd_reference_equity=ref)


def test_profit_target_derisks_hard_above_target():
    from src.components.ultimate_book.admission import GovernorLimits
    lim = GovernorLimits(profit_target_pct=0.10, profit_target_derisk_mult=0.25)
    d = evaluate_governor(_gstate(110000.0), limits=lim)        # +10% -> target passed
    assert d.allow_new_entries is True                          # keeps trading...
    assert d.size_cap_multiplier == 0.25                        # ...at quarter size (lock in the pass)
    assert d.reason == "profit_target_protect_derisk"


def test_no_profit_derisk_below_target():
    from src.components.ultimate_book.admission import GovernorLimits
    lim = GovernorLimits(profit_target_pct=0.10, profit_target_derisk_mult=0.25)
    d = evaluate_governor(_gstate(105000.0), limits=lim)        # +5% -> below target -> full size
    assert d.size_cap_multiplier == 1.0 and d.reason == "ok"


def test_max_dd_entry_buffer_blocks_before_wall_when_configured():
    from src.components.ultimate_book.admission import GovernorLimits
    lim = GovernorLimits(max_dd_entry_block_pct=0.09)
    d = evaluate_governor(_gstate(91000.0), limits=lim)
    assert d.allow_new_entries is False
    assert d.reason == "max_dd_entry_buffer_reached"


def test_profit_target_disabled_when_zero():
    from src.components.ultimate_book.admission import GovernorLimits
    lim = GovernorLimits(profit_target_pct=0.0, profit_target_derisk_mult=0.25)
    d = evaluate_governor(_gstate(120000.0), limits=lim)        # +20% but target logic OFF
    assert d.size_cap_multiplier == 1.0


class _FakeMT5:
    """Deal-capable fake: equity + balance + account-wide deal history."""
    def __init__(self, *, equity, balance, deals=None, candles=None):
        self._equity = equity
        self._balance = balance
        self._deals = deals or []
        self._candles = candles or []
    def get_account_equity(self):
        return self._equity
    def get_account_balance(self):
        return self._balance
    def get_account_history_deals(self, frm, to):
        return self._deals
    def get_candles(self, symbol, timeframe, count):
        return self._candles[-count:] if self._candles else []


def test_balance_anchor_excludes_floating_loss_vs_legacy_equity_anchor():
    """A position carried across the boundary at -500 floating: equity 99_500, day-start balance 100_000.
    The balance anchor must SEE the -0.5% loss; the legacy equity anchor would HIDE it (anchors to 99_500
    => realized 0.0). The hidden-loss case is exactly what let the -5% daily breach slip."""
    with tempfile.TemporaryDirectory() as d:
        g = GovernorStateBuilder(d, namespace="ftmo_bal", daily_reset_offset_hours=3.0)
        s = g.build(equity=99_500.0, day_start_balance=100_000.0, now_utc=_now())
        assert s.realized_today_pct == pytest.approx(-0.005, abs=1e-9)
    with tempfile.TemporaryDirectory() as d2:
        g2 = GovernorStateBuilder(d2, namespace="ftmo_eq", daily_reset_offset_hours=3.0)
        s_legacy = g2.build(equity=99_500.0, now_utc=_now())   # no day_start_balance -> legacy equity anchor
        assert abs(s_legacy.realized_today_pct) < 1e-12        # loss invisible (the OLD, dangerous behavior)


def test_reconstruct_day_start_balance_from_all_trade_deal_cash():
    """The baseline includes entry commission, exit cash, and excludes balance operations."""
    with tempfile.TemporaryDirectory() as d:
        g = GovernorStateBuilder(d, namespace="ftmo_r", daily_reset_offset_hours=3.0)
        boundary = g._reset_window_start_utc(_now())
        deals = [
            {"type": 1, "entry": 1, "profit": -3500.0, "swap": 0.0, "commission": 0.0, "fee": 0.0, "time": boundary + timedelta(hours=2)},
            {"type": 0, "entry": 0, "profit": 0.0, "swap": 0.0, "commission": -2.0, "fee": 0.0, "time": boundary + timedelta(hours=1)},
            {"type": 2, "entry": 0, "profit": 500.0, "swap": 0.0, "commission": 0.0, "fee": 0.0, "time": boundary + timedelta(hours=1)},
            {"type": 1, "entry": 1, "profit": -10.0, "swap": 0.0, "commission": 0.0, "fee": 0.0, "time": boundary - timedelta(hours=1)},
        ]
        mt5 = _FakeMT5(equity=96_498.0, balance=96_498.0, deals=deals)
        dsb = g.reconstruct_day_start_balance(mt5, _now())
        assert dsb == pytest.approx(100_000.0, abs=1e-6)


def test_from_mt5_reconstructs_and_soft_stop_trips():
    """End-to-end: account -3.5% on the day (closed) -> reconstructed baseline 100_000 -> realized -3.5%
    -> soft daily stop (-3%) blocks new entries. Without the deal history it would anchor to equity and
    read 0% (allow)."""
    with tempfile.TemporaryDirectory() as d:
        g = GovernorStateBuilder(d, namespace="ftmo_e2e", static_initial_balance=100_000.0,
                                 daily_reset_offset_hours=3.0)
        boundary = g._reset_window_start_utc(_now())
        deals = [{"type": 1, "entry": 1, "profit": -3500.0, "swap": 0.0, "commission": 0.0, "fee": 0.0,
                  "time": boundary + timedelta(hours=3)}]
        mt5 = _FakeMT5(equity=96_500.0, balance=96_500.0, deals=deals)
        gs = g.from_mt5(mt5, now_utc=_now())
        assert gs is not None
        assert gs.realized_today_pct == pytest.approx(-0.035, abs=1e-9)
        assert evaluate_governor(gs).allow_new_entries is False  # soft daily stop reached


def test_from_mt5_without_deals_falls_back_to_equity_anchor():
    """A mt5 lacking deal history (mock) keeps the legacy equity anchor — NOT fail-closed — so existing
    callers/tests are unaffected."""
    class _EquityOnly:
        def get_account_equity(self):
            return 100_000.0
    with tempfile.TemporaryDirectory() as d:
        g = GovernorStateBuilder(d, namespace="ftmo_legacy", daily_reset_offset_hours=3.0)
        gs = g.from_mt5(_EquityOnly(), now_utc=_now())
        assert gs is not None and abs(gs.realized_today_pct) < 1e-12


def test_reconstruct_returns_none_when_balance_or_deals_unreadable():
    with tempfile.TemporaryDirectory() as d:
        g = GovernorStateBuilder(d, namespace="ftmo_fc", daily_reset_offset_hours=3.0)

        class _NoBal:
            def get_account_balance(self):
                raise RuntimeError("blind")
            def get_account_history_deals(self, frm, to):
                return []
        assert g.reconstruct_day_start_balance(_NoBal(), _now()) is None

        class _BadDeals:
            def get_account_balance(self):
                return 100_000.0
            def get_account_history_deals(self, frm, to):
                raise RuntimeError("history down")
        assert g.reconstruct_day_start_balance(_BadDeals(), _now()) is None


def test_reconstruct_fails_closed_on_unaccountable_trade_deal(tmp_path):
    g = GovernorStateBuilder(str(tmp_path), namespace="ftmo_bad_deal", daily_reset_offset_hours=3.0)
    boundary = g._reset_window_start_utc(_now())
    mt5 = _FakeMT5(
        equity=99_000.0,
        balance=99_000.0,
        deals=[{"entry": 1, "profit": -1000.0, "time": boundary + timedelta(hours=1)}],
    )
    assert g.reconstruct_day_start_balance(mt5, _now()) is None


def test_book_engine_fail_closed_when_deal_capable_and_baseline_unreadable():
    """Live path: a deal-capable broker that cannot return deal history must FAIL CLOSED (no decision),
    not silently trade on a wrong baseline."""
    from src.components.ultimate_book.book_engine import UltimateBookLiveEngine

    class _DealCapableButBroken:
        def get_account_equity(self):
            return 100_000.0
        def get_account_balance(self):
            return 100_000.0
        def get_account_history_deals(self, frm, to):
            raise RuntimeError("history down")
        def get_candles(self, symbol, timeframe, count):
            return []   # no bars -> no intents; isolate the baseline path
    with tempfile.TemporaryDirectory() as d:
        eng = UltimateBookLiveEngine({}, _DealCapableButBroken(), d, namespace="ftmo_fc2")
        res = eng.evaluate(now_utc=_now())
        assert res["ok"] is False and res["decision"] is None
        assert res["reason"] == "day_baseline_unavailable"


def test_reset_window_start_utc_offset():
    with tempfile.TemporaryDirectory() as d:
        g = GovernorStateBuilder(d, namespace="ftmo_w", daily_reset_offset_hours=3.0)
        start = g._reset_window_start_utc(datetime(2026, 6, 15, 14, 0, tzinfo=timezone.utc))
        assert start == datetime(2026, 6, 14, 21, 0, tzinfo=timezone.utc)
        # just after the boundary the window is the new day
        start2 = g._reset_window_start_utc(datetime(2026, 6, 15, 21, 30, tzinfo=timezone.utc))
        assert start2 == datetime(2026, 6, 15, 21, 0, tzinfo=timezone.utc)


def test_static_max_dd_unchanged_with_balance_anchor():
    """B2 regression: the static 90k wall and its consumption are unchanged by the balance-anchor work."""
    with tempfile.TemporaryDirectory() as d:
        g = GovernorStateBuilder(d, namespace="ftmo_dd", static_initial_balance=100_000.0,
                                 daily_reset_offset_hours=3.0)
        s_ok = g.build(equity=92_000.0, day_start_balance=92_000.0, now_utc=_now())
        assert s_ok.max_dd_reference_equity == 100_000.0
        assert evaluate_governor(s_ok).allow_new_entries is True      # 8% dd < 10% wall
        s_wall = g.build(equity=89_999.0, day_start_balance=89_999.0, now_utc=_now())
        assert evaluate_governor(s_wall).reason == "max_dd_limit_reached"


def test_vpp_cache_positive_only():
    """A transient 0/None value-per-point must NOT poison the cache for the process lifetime."""
    from src.mt5.mt5_real import RealMT5

    adapter = RealMT5.__new__(RealMT5)   # bypass connect

    class _Info:
        def __init__(self, tv, ts):
            self.trade_tick_value = tv
            self.trade_tick_size = ts

    seq = [_Info(0.0, 0.01), _Info(1.0, 0.01)]   # first transient-bad (->0), then good (->100)

    class _M:
        def symbol_info(self, s):
            return seq.pop(0)
    adapter._mt5 = _M()
    assert not adapter.get_symbol_value_per_point("GER40")   # bad read returned, NOT cached
    assert adapter.get_symbol_value_per_point("GER40") == pytest.approx(100.0)  # good read now populates


# ---- broker-time integrity (audit: offset-from-stale-tick + history-failure-masks-as-empty) ----

def test_offset_guard_rejects_stale_tick_latches_fresh():
    """A market-closed/weekend restart returns a STALE tick whose implied offset is grossly wrong; it must
    NOT be latched (else the daily-loss window + deal queries mis-time all process-life). A FRESH tick in
    the sane band IS latched."""
    from src.mt5.mt5_real import RealMT5
    import datetime as _dt
    a = RealMT5.__new__(RealMT5)
    a._broker_offset_seconds = 0
    a._broker_offset_detected = False
    now = _dt.datetime.now(_dt.timezone.utc).timestamp()

    class _T:
        pass
    stale = _T(); stale.time = now - 12 * 3600; stale.bid = 2000.0; stale.ask = 2000.1
    a._detect_offset_from_tick(stale)
    assert a._broker_offset_detected is False    # out-of-band stale offset NOT latched

    fresh = _T(); fresh.time = now + 3 * 3600; fresh.bid = 2000.0; fresh.ask = 2000.1
    a._detect_offset_from_tick(fresh)
    assert a._broker_offset_detected is True and a._broker_offset_seconds == 3 * 3600


def test_account_history_deals_none_on_error_empty_on_no_deals():
    """A FETCH ERROR (MT5 None) must propagate as None so the governor fails closed; a genuine no-deals
    window (MT5 ()) returns [] (realized 0)."""
    from src.mt5.mt5_real import RealMT5
    import datetime as _dt
    a = RealMT5.__new__(RealMT5)
    a._broker_offset_detected = True
    a._broker_offset_seconds = 0
    frm = _dt.datetime(2026, 6, 15, tzinfo=_dt.timezone.utc)
    to = _dt.datetime(2026, 6, 15, 12, tzinfo=_dt.timezone.utc)

    class _Err:
        def history_deals_get(self, x, y):
            return None
    a._mt5 = _Err()
    assert a.get_account_history_deals(frm, to) is None      # error -> None -> fail-closed upstream

    class _Empty:
        def history_deals_get(self, x, y):
            return ()
    a._mt5 = _Empty()
    assert a.get_account_history_deals(frm, to) == []        # genuine no-deals -> []
