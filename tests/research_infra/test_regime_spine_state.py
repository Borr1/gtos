"""The frame must equal the production statistics, bar for bar, with no tolerance.

`state.build_frame` recomputes what `primitives`, `metals` and `substrate_engine` compute,
because a threshold sweep needs the numbers thousands of times and calling the production
functions per cell is the difference between a five-second sweep and a five-hour one. That
is a re-implementation, and re-implementations are how this programme's worst findings
happened. So these tests compare against the production functions themselves and demand
**exact equality**, not `approx`: `build_frame` deliberately uses the same builtin `sum`
over the same slices rather than a rolling accumulator, so exactness is achievable and a
tolerance would only hide a drift.

Synthetic bars, not archive bars: the archive lives outside the repo and a test that skips
when it is absent is a test that silently stops running.
"""

from __future__ import annotations

import datetime as dt
import math

import pytest

from src.components.ultimate_book.primitives import Bar, atr14, autocorr, vol_ratio
from src.components.ultimate_book.sleeves import crypto as prod_crypto
from src.components.ultimate_book.sleeves import energy_agri as prod_energy
from src.components.ultimate_book.sleeves import metals as prod_metals
from src.components.ultimate_book.sleeves import substrate_engine as prod_se
from src.research_infra.regime_spine.state import build_frame, fvg_at, htf_trend_sign


def _bars(n: int = 900, seed: int = 7) -> list[Bar]:
    """A deterministic pseudo-random walk with vol clustering and gaps.

    Vol clustering matters: a constant-vol series never exercises the ATR-ratio gates, and
    the gaps are what produce FVGs at all.
    """
    rng = _Lcg(seed)
    px = 1000.0
    out = []
    vol = 1.0
    for i in range(n):
        vol = max(0.2, vol * (0.97 + 0.06 * rng.next()))
        step = (rng.next() - 0.5) * 4.0 * vol
        o = px
        c = px + step
        hi = max(o, c) + abs(rng.next()) * vol
        lo = min(o, c) - abs(rng.next()) * vol
        out.append(Bar(o, hi, lo, c, 100.0 + 10 * rng.next()))
        px = c
        if i % 97 == 0:            # occasional jump -> creates fair-value gaps
            px += (rng.next() - 0.5) * 20.0 * vol
    return out


class _Lcg:
    """Tiny deterministic RNG — no dependence on the platform's `random` implementation."""

    def __init__(self, seed: int) -> None:
        self.s = seed & 0xFFFFFFFF

    def next(self) -> float:
        self.s = (1103515245 * self.s + 12345) & 0x7FFFFFFF
        return self.s / 0x7FFFFFFF


@pytest.fixture(scope="module")
def frame():
    bars = _bars()
    t0 = dt.datetime(2020, 1, 1, tzinfo=dt.timezone.utc)
    times = [t0 + dt.timedelta(hours=4 * i) for i in range(len(bars))]
    return bars, times, build_frame("TESTSYM", 16388, bars, times)


def test_atr_and_vol_ratio_are_exact(frame):
    bars, _t, f = frame
    atrs = [atr14(bars, i) for i in range(len(bars))]
    for i in range(len(bars)):
        assert f.atr[i] == atrs[i], f"atr mismatch at {i}"
        assert f.vr[i] == vol_ratio(atrs, i), f"vol_ratio mismatch at {i}"


def test_autocorr_both_flavours_are_exact(frame):
    """The two production autocorrelations differ (statistics.mean vs sum/n). Keep both."""
    bars, _t, f = frame
    closes = [b.c for b in bars]
    for i in range(61, len(bars)):
        assert f.ac60_prim[i] == autocorr(bars, i, 60), f"primitives.autocorr at {i}"
        rets = [closes[k] - closes[k - 1] for k in range(i - 59, i + 1)]
        assert f.ac60_sub[i] == prod_se._ac(rets), f"substrate _ac at {i}"


def test_substrate_state_is_exact(frame):
    bars, _t, f = frame
    n = 0
    for i in range(209, len(bars)):
        st = prod_se.compute_state(bars, i, hour=None)
        if st is None:
            assert f.atr[i] <= 0
            continue
        n += 1
        assert f.vr[i] == st["vr"]
        assert f.slope20[i] == st["slope20"]
        assert f.slope50[i] == st["slope50"]
        assert f.slope100[i] == st["slope100"]
        assert f.rng_pos[i] == st["rng_pos"]
        assert f.comp[i] == st["compression"]
        assert f.ac60_sub[i] == st["ac60"]
    assert n > 500, "the fixture must exercise the substrate state on most bars"


def test_htf_trend_and_fvg_match_production(frame):
    """The FVG factorisation is the load-bearing claim: the gap search ignores `gate_k`."""
    bars, _t, f = frame
    atrs = [atr14(bars, i) for i in range(len(bars))]
    seen_signal = 0
    for i in range(100, len(bars)):
        assert htf_trend_sign(f, i) == prod_metals.htf_trend(bars, i, 30), f"htf at {i}"
        for gate_k in (1.0, 1.2, 1.5, 2.0):
            got = fvg_at(f, i, gate_k)
            want = prod_metals.fvg_signal(bars, atrs, i, gate_k)
            assert got == want, f"fvg at {i} gate_k={gate_k}: {got} != {want}"
            if want is not None:
                seen_signal += 1
    assert seen_signal > 0, "the fixture must produce at least one FVG signal"


def test_donchian_and_energy_slope_match_production(frame):
    bars, _t, f = frame
    for i in range(100, len(bars)):
        assert f.don_hh[i] == max(b.h for b in bars[i - 20:i])
        assert f.don_ll[i] == min(b.l for b in bars[i - 20:i])
        assert f.eslope30[i] == pytest.approx(
            prod_energy.trend_slope(bars, i, 30), rel=0, abs=1e-12)


def test_crypto_signal_reconstructs_from_the_frame(frame):
    """`crypto.crypto_signal` is a pure function of quantities the frame stores."""
    from src.research_infra.regime_spine import conditions as C

    bars, _t, f = frame
    cond = C.SLEEVES["crypto"]
    p = dict(cond.defaults)
    n_fire = 0
    for i in range(60, len(bars)):
        want = prod_crypto.crypto_signal(bars, i)
        fired = all(g.test(f, i, p) for g in cond.gates)
        assert fired == (want is not None), f"crypto fire disagreement at {i}"
        if want is not None:
            n_fire += 1
            got = cond.intent(f, i, p)
            assert got["direction"] == want[0]
            assert got["stop_dist"] == want[1]
    assert n_fire > 0, "the fixture must fire crypto at least once"


def test_frame_sentinels_are_production_sentinels(frame):
    """Warmup values must be the production sentinel, never an imputed number."""
    _b, _t, f = frame
    assert all(f.atr[i] == 0.0 for i in range(14))
    assert all(f.vr[i] == 1.0 for i in range(100))          # vol_ratio's own early return
    assert all(f.vr_raw[i] is None for i in range(100))      # but distinguishable
    assert all(f.ac60_prim[i] is None for i in range(61))
    assert all(f.don_hh[i] is None for i in range(20))
    assert not any(isinstance(v, float) and math.isnan(v)
                   for v in f.atr + list(f.vr))
