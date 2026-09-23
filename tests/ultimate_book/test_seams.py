"""Stage 1 — live-data seam tests: bar_provider + governor_state. Pure (fake mt5)."""
import os
import tempfile
from datetime import datetime, timezone

from src.components.ultimate_book import bar_provider as BP
from src.components.ultimate_book.governor_state import GovernorStateBuilder


def _candles(n):
    from datetime import timedelta
    out = []
    p = 2000.0
    t0 = datetime(2026, 6, 10, 0, 0, tzinfo=timezone.utc)
    for k in range(n):
        t = t0 + timedelta(hours=4 * k)   # valid H4 spacing
        out.append({"time": t.isoformat(),
                    "open": p, "high": p + 5, "low": p - 4, "close": p + 1, "volume": 100 + k})
        p += 1
    return out


class _FakeMT5:
    def __init__(self, candles=None, equity=100000.0):
        self._candles = candles or []
        self._equity = equity
    def get_candles(self, symbol, timeframe, count):
        return self._candles[-count:]
    def get_account_equity(self):
        return self._equity


def test_candles_to_bars_drops_forming_and_maps():
    c = _candles(10)
    bars, times = BP.candles_to_bars(c, drop_forming=True)
    assert len(bars) == 9                      # forming bar dropped
    assert bars[0].o == 2000.0 and bars[0].h == 2005.0 and bars[0].l == 1996.0 and bars[0].c == 2001.0
    assert times[0].tzinfo is not None
    assert BP.decision_day_of(times[0]) == "2026-06-10"


def test_get_closed_bars_and_warmup():
    mt5 = _FakeMT5(_candles(205))
    bars, times = BP.get_closed_bars(mt5, "XAUUSD", BP.TF_H4, 205)
    assert len(bars) == 204
    assert BP.enough(bars, "metals") is True       # >=200
    assert BP.enough(bars[:150], "metals") is False
    assert BP.enough(bars, "substrate") is False    # needs 210


def test_get_closed_bars_failclosed_on_feed_error():
    class Bad:
        def get_candles(self, *a):
            raise RuntimeError("feed down")
    bars, times = BP.get_closed_bars(Bad(), "XAUUSD", BP.TF_H4, 50)
    assert bars == [] and times == []


def test_governor_high_water_monotonic_and_day_anchor():
    with tempfile.TemporaryDirectory() as d:
        g = GovernorStateBuilder(d, namespace="ftmo_primary")
        now = datetime(2026, 6, 15, 10, 0, tzinfo=timezone.utc)
        s1 = g.build(equity=100000.0, now_utc=now)
        assert s1.high_water == 100000.0 and abs(s1.realized_today_pct) < 1e-12
        # equity rises -> high_water tracks up; realized vs same-day anchor (100000)
        s2 = g.build(equity=101000.0, now_utc=now)
        assert s2.high_water == 101000.0
        assert abs(s2.realized_today_pct - 0.01) < 1e-9
        # equity falls -> high_water STAYS (monotonic); realized negative
        s3 = g.build(equity=98000.0, now_utc=now)
        assert s3.high_water == 101000.0
        assert abs(s3.realized_today_pct - (-0.02)) < 1e-9
        # new UTC day -> anchor resets to current equity
        nxt = datetime(2026, 6, 16, 1, 0, tzinfo=timezone.utc)
        s4 = g.build(equity=98000.0, now_utc=nxt)
        assert abs(s4.realized_today_pct) < 1e-12 and s4.high_water == 101000.0


def test_governor_static_max_dd_floor_via_reference():
    """Max-DD wall is a FLAT 90k (initial-10%): it does NOT sink on a drawdown-seeded first run and
    does NOT trail up with profit. high_water is now a pure trailing peak (no clamp)."""
    from src.components.ultimate_book.admission import evaluate_governor
    with tempfile.TemporaryDirectory() as d:
        g = GovernorStateBuilder(d, namespace="ftmo_x", static_initial_balance=100000.0)
        now = datetime(2026, 6, 15, 10, 0, tzinfo=timezone.utc)
        # first-run in drawdown (FTMO -2.9%): high_water is pure-trailing (NOT clamped to 100k), but the
        # STATIC reference is 100000 so the max-DD basis is the initial balance (wall = 90k).
        s = g.build(equity=97100.0, now_utc=now)
        assert s.high_water == 97100.0 and s.max_dd_reference_equity == 100000.0
        dec = evaluate_governor(s)
        assert dec.allow_new_entries is True and dec.size_cap_multiplier == 1.0  # 2.9% dd < 7% -> full
        # profit above the initial balance: the wall STAYS pinned at 90k (does NOT trail to 0.9*peak)
        s2 = g.build(equity=108000.0, now_utc=now)
        assert s2.high_water == 108000.0 and s2.max_dd_reference_equity == 100000.0
        dec2 = evaluate_governor(s2)
        assert dec2.allow_new_entries is True and dec2.size_cap_multiplier == 1.0  # in profit -> full


def test_governor_static_wall_and_band_pinned_to_initial():
    """Wall at the static 90k floor + de-risk band anchored to the initial balance, regardless of peak;
    back-compat (no reference) preserves the old trailing-high_water behavior."""
    from src.components.ultimate_book.admission import evaluate_governor, GovernorState
    # equity AT the 90k static floor -> max-DD limit reached, even with a high prior peak
    s_wall = GovernorState(equity=90000.0, high_water=120000.0, realized_today_pct=0.0,
                           open_risk_pct=0.0, max_dd_reference_equity=100000.0)
    assert evaluate_governor(s_wall).reason == "max_dd_limit_reached"
    # equity in the 93k->90k de-risk band -> shrinking multiplier (anchored to static 100k, not peak)
    s_band = GovernorState(equity=92900.0, high_water=120000.0, realized_today_pct=0.0,
                           open_risk_pct=0.0, max_dd_reference_equity=100000.0)
    db = evaluate_governor(s_band)
    assert db.allow_new_entries is True and 0.0 < db.size_cap_multiplier < 1.0
    # back-compat: NO static reference -> trailing high_water drives dd (old behavior preserved)
    s_trail = GovernorState(equity=108000.0, high_water=120000.0, realized_today_pct=0.0, open_risk_pct=0.0)
    assert evaluate_governor(s_trail).reason == "max_dd_limit_reached"  # (120000-108000)/120000 = 0.10


def test_governor_daily_reset_offset_keys_on_server_local_day():
    """Broker daily window resets at server midnight (UTC+3=21:00 UTC), not UTC midnight."""
    with tempfile.TemporaryDirectory() as d:
        g = GovernorStateBuilder(d, namespace="srv", daily_reset_offset_hours=3.0)
        # 20:00 UTC = 23:00 server (still 15th server) -> anchor equity 100000
        t1 = datetime(2026, 6, 15, 20, 0, tzinfo=timezone.utc)
        s1 = g.build(equity=100000.0, now_utc=t1)
        assert abs(s1.realized_today_pct) < 1e-12
        # 21:30 UTC = 00:30 server next day (16th server) -> NEW window: re-anchors despite same UTC day
        t2 = datetime(2026, 6, 15, 21, 30, tzinfo=timezone.utc)
        s2 = g.build(equity=99000.0, now_utc=t2)
        assert abs(s2.realized_today_pct) < 1e-12          # fresh server-day anchor, not -1%
        # later in the same server window a loss IS measured against the new anchor
        t3 = datetime(2026, 6, 15, 23, 0, tzinfo=timezone.utc)
        s3 = g.build(equity=98010.0, now_utc=t3)
        assert abs(s3.realized_today_pct - (-0.01)) < 1e-9


def test_governor_from_mt5_failclosed():
    g = GovernorStateBuilder(tempfile.mkdtemp(), namespace="ftmo_primary")
    class NoEq:
        def get_account_equity(self):
            raise RuntimeError("mt5 down")
    assert g.from_mt5(NoEq()) is None
    class ZeroEq:
        def get_account_equity(self):
            return 0.0
    assert g.from_mt5(ZeroEq()) is None
