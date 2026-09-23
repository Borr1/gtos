"""MACRO-EDGE-02: the reactive temporal de-risk overlay, now FED real leak-free prior-day book P&L.
compute_stress_derisk_state turns the broker's closed BOOK deals into the (consecutive_loss_days,
trailing_neg_frac) the overlay consumes; the overlay only ever SHRINKS size."""
import calendar
import datetime as dt

from src.components.ultimate_book.admission import (
    compute_stress_derisk_state, stress_derisk_multiplier, StressDeriskState,
)

NOW = dt.datetime(2026, 6, 16, 9, 0, tzinfo=dt.timezone.utc)   # offset 0 -> server 'today' = 2026-06-16


def _epoch(y, m, d, h=12):
    return calendar.timegm(dt.datetime(y, m, d, h, 0).timetuple())


def _deal(sleeve, profit, y, m, d):
    return {"sleeve": sleeve, "profit": profit, "time": _epoch(y, m, d)}


def test_empty_state_is_neutral():
    s = compute_stress_derisk_state([], NOW, offset_hours=0)
    assert s.consecutive_loss_days == 0 and s.trailing_neg_frac == 0.0
    assert stress_derisk_multiplier(s)[0] == 1.0          # neutral -> no de-risk


def test_consecutive_loss_days_counted():
    deals = [_deal("crypto", -100, 2026, 6, 15), _deal("idxrev", -50, 2026, 6, 14),
             _deal("crypto", -20, 2026, 6, 13)]
    s = compute_stress_derisk_state(deals, NOW, offset_hours=0)
    assert s.consecutive_loss_days == 3


def test_green_day_resets_streak():
    # 15 loss, 14 GREEN, 13 loss -> streak from most-recent traded day = 1 (resets at 14)
    deals = [_deal("crypto", -100, 2026, 6, 15), _deal("idxrev", +200, 2026, 6, 14),
             _deal("crypto", -30, 2026, 6, 13)]
    assert compute_stress_derisk_state(deals, NOW, offset_hours=0).consecutive_loss_days == 1


def test_today_excluded_leak_free():
    # a loss TODAY (the in-progress server-day) must NOT count toward the streak
    assert compute_stress_derisk_state([_deal("crypto", -100, 2026, 6, 16)], NOW,
                                       offset_hours=0).consecutive_loss_days == 0


def test_trailing_neg_firing_fraction():
    # day 15: a(-),b(-),c(+) -> 2/3 ; day 14: a(-),b(+) -> 1/2 ; mean = 0.5833
    deals = [_deal("a", -1, 2026, 6, 15), _deal("b", -1, 2026, 6, 15), _deal("c", +1, 2026, 6, 15),
             _deal("a", -1, 2026, 6, 14), _deal("b", +1, 2026, 6, 14)]
    s = compute_stress_derisk_state(deals, NOW, offset_hours=0)
    assert round(s.trailing_neg_frac, 4) == round((2 / 3 + 1 / 2) / 2, 4)


def test_multiplier_from_real_losing_streak():
    # 2 consecutive all-negative days -> ladder step2 (x0.60) AND coloss breaker (neg_frac 1.0 >= 0.57)
    deals = [_deal("a", -1, 2026, 6, 15), _deal("a", -1, 2026, 6, 14)]
    s = compute_stress_derisk_state(deals, NOW, offset_hours=0)
    assert s.consecutive_loss_days == 2 and s.trailing_neg_frac == 1.0
    mult, reasons = stress_derisk_multiplier(s)
    assert mult == 0.60 and "ladder_step2" in reasons and "coloss_breaker" in reasons   # floored, shrinks only


def test_offset_shifts_server_today():
    # a deal at 2026-06-16 01:00 UTC is 2026-06-16 04:00 server (+3) -> still today -> excluded;
    # a deal at 2026-06-15 23:00 server is the prior day -> counts.
    now = dt.datetime(2026, 6, 16, 6, 0, tzinfo=dt.timezone.utc)
    deals = [{"sleeve": "x", "profit": -10, "time": _epoch(2026, 6, 16, 1)},   # server 04:00 today -> excluded
             {"sleeve": "x", "profit": -10, "time": _epoch(2026, 6, 15, 20)}]  # prior day -> counts
    assert compute_stress_derisk_state(deals, now, offset_hours=3).consecutive_loss_days == 1


def test_book_engine_gates_and_fails_safe(tmp_path):
    from src.components.ultimate_book.book_engine import UltimateBookLiveEngine
    off = UltimateBookLiveEngine({"ultimate_book_stress_derisk": False}, object(), str(tmp_path))
    assert off._stress_derisk_state(NOW) is None                  # flag off -> no broker work, None
    on = UltimateBookLiveEngine({"ultimate_book_stress_derisk": True}, object(), str(tmp_path))
    assert on._stress_derisk_state(NOW) is None                   # no raw mt5 module -> safe None, no raise


def test_book_engine_real_broker_stress_read_failure_derisks(tmp_path, monkeypatch):
    from src.components.ultimate_book import book_engine as be
    from src.components.ultimate_book.book_engine import UltimateBookLiveEngine

    class _Realish:
        _mt5 = object()
        def get_broker_offset_seconds(self):
            return 3 * 3600

    def _history_down(*_args, **_kwargs):
        raise RuntimeError("history down")

    monkeypatch.setattr(be, "closed_book_deals", _history_down)
    eng = UltimateBookLiveEngine({"ultimate_book_stress_derisk": True}, _Realish(), str(tmp_path))
    state = eng._stress_derisk_state(NOW)
    assert state == StressDeriskState(consecutive_loss_days=2, trailing_neg_frac=1.0)
    assert stress_derisk_multiplier(state)[0] == 0.60
