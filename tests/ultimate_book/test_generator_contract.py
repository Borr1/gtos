"""Generator-contract guard: EVERY registered sleeve generator must accept the engine's uniform call
signature without raising. The book_engine wraps generator calls in try/except (a single sleeve error
must never kill the batch) — which means a SIGNATURE mismatch (e.g. a generator missing the bar_time/
bar_times/aux_* kwargs) is SILENTLY swallowed to None, disabling the sleeve in production with no error.
This test calls each generator DIRECTLY (no try/except) with the exact kwargs book_engine passes, so any
contract drift fails loudly. (This is the guard that catches the class of bug where metals_ob_micro had
no bar_time kwarg and silently never fired through the engine.)"""
from datetime import datetime, timezone, timedelta

import pytest

from src.components.ultimate_book.sleeves.registry import BUILT
from src.components.ultimate_book.primitives import Bar
from src.components.ultimate_book.admission import TradeIntent


def _flat_series(n=260, start=100.0):
    """A long, low-vol flat series — enough bars to clear warmup; unlikely to fire any signal (-> None),
    which is fine: the test asserts the CALL CONTRACT, not a signal."""
    bars, times = [], []
    t0 = datetime(2026, 6, 1, 0, 0, tzinfo=timezone.utc)
    p = start
    for k in range(n):
        o = p; c = p + (0.01 if k % 2 else -0.01)
        bars.append(Bar(o, max(o, c) + 0.02, min(o, c) - 0.02, c, 100.0))
        times.append(t0 + timedelta(hours=4 * k))
        p = c
    return bars, times


@pytest.mark.parametrize("tag", list(BUILT.keys()))
def test_every_generator_accepts_engine_call_signature(tag):
    spec = BUILT[tag]
    bars, times = _flat_series()
    sym = spec.on_surface[0]
    # the EXACT kwargs book_engine._generate_intents passes:
    result = spec.generator(sym, bars, "2026-06-15", bar_time=times[-1], bar_times=times,
                            aux_bars=None, aux_times=None)
    assert result is None or isinstance(result, TradeIntent)


def test_engine_drives_all_built_generators_without_swallowed_errors(tmp_path):
    """End-to-end: run the engine on a fake feed and assert it reaches every sleeve. We detect
    swallowed signature errors by re-driving each generator directly above; here we just confirm the
    engine path itself runs green with the full BUILT registry (8 sleeves). repo_root=tmp_path so the
    governor's high_water/day_anchor persist into the pytest sandbox, not production pipeline_state/."""
    from src.components.ultimate_book.book_engine import UltimateBookLiveEngine

    bars, times = _flat_series()

    class _FakeMT5:
        def get_candles(self, symbol, tf, count):
            # return raw candle dicts the bar_provider expects (it drops the forming bar)
            return [{"time": t.isoformat(), "open": b.o, "high": b.h, "low": b.l,
                     "close": b.c, "volume": b.v} for b, t in zip(bars, times)] + [
                    {"time": (times[-1] + timedelta(hours=4)).isoformat(), "open": bars[-1].c,
                     "high": bars[-1].c, "low": bars[-1].c, "close": bars[-1].c, "volume": 1.0}]
        def get_account_equity(self):
            return 100000.0

    eng = UltimateBookLiveEngine({}, _FakeMT5(), str(tmp_path), namespace="contract_test")
    res = eng.evaluate()
    assert res["ok"] is True, res["reason"]
    # flat series fires no signals; the point is the engine ran the full book with no crash
    assert res["n_intents"] == 0
