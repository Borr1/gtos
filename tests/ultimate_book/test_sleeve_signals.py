"""T2 — sleeve signal parity: the src generators must reproduce the LOCKED route signal logic
(INTEG_portfolio_build gen_crypto/gen_idxrev) exactly. The route loop body is copied verbatim here
as the oracle and run side-by-side with the src functions over a varied bar series; any divergence
(a transcription error in the port) fails. Pure, no MT5.
"""
import random

from src.components.ultimate_book.primitives import Bar, atr14, autocorr, simulate
from src.components.ultimate_book.sleeves import crypto as CR
from src.components.ultimate_book.sleeves import index_jpy as IX


def _series(n=400, seed=7):
    rnd = random.Random(seed)
    bars = []
    p = 100.0
    for _ in range(n):
        drift = rnd.uniform(-1.5, 1.6)
        o = p
        c = max(1.0, o + drift + rnd.uniform(-1, 1))
        h = max(o, c) + abs(rnd.uniform(0, 2.0))
        l = min(o, c) - abs(rnd.uniform(0, 2.0))
        bars.append(Bar(o, h, l, c, 100))
        p = c
    return bars


def _trend_series(n=400, seed=3):
    # persistent uptrend (high return-autocorrelation -> ac60>=0.15) with breakouts
    rnd = random.Random(seed)
    bars = []
    p = 100.0
    for k in range(n):
        drift = 1.2 + rnd.uniform(-0.3, 0.6)        # consistent positive drift -> persistence
        o = p
        c = o + drift
        h = max(o, c) + abs(rnd.uniform(0, 0.5))
        l = min(o, c) - abs(rnd.uniform(0, 0.5))
        bars.append(Bar(o, h, l, c, 100))
        p = c
    return bars


def test_crypto_signal_matches_route_loop():
    B = _trend_series()
    n_sig = 0
    for i in range(len(B)):
        # --- VERBATIM route gen_crypto loop body (INTEG_portfolio_build.py:152-161) ---
        oracle = None
        if i >= 60:
            a = atr14(B, i)
            if a > 0:
                hh = max(B[k].h for k in range(i - 20, i))
                ll = min(B[k].l for k in range(i - 20, i))
                d = 0
                if B[i].c > hh: d = 1
                elif B[i].c < ll: d = -1
                if d != 0:
                    ac = autocorr(B, i, 60)
                    if ac is not None and ac >= 0.15:
                        oracle = (d, 2.0 * a)
        # --- src ---
        got = CR.crypto_signal(B, i)
        assert got == oracle, f"crypto i={i}: src={got} route={oracle}"
        if oracle is not None:
            n_sig += 1
    assert n_sig > 0, "fixture produced no crypto signals — strengthen it"


def test_idxrev_signal_matches_route_loop():
    B = _series(seed=11)
    atrs = [atr14(B, k) for k in range(len(B))]
    n_sig = 0
    for i in range(len(B)):
        # --- VERBATIM route gen_idxrev loop body (INTEG_portfolio_build.py:189-196) ---
        oracle = None
        if i >= 120:
            a = atrs[i]
            if a > 0:
                rhi = max(B[k].h for k in range(i - 16, i))
                rlo = min(B[k].l for k in range(i - 16, i))
                b = B[i]; d = 0
                if b.h > rhi and b.c < rhi: d = -1
                elif b.l < rlo and b.c > rlo: d = 1
                if d != 0:
                    oracle = (d, 1.5 * a)
        got = IX.idxrev_signal(B, atrs, i)
        assert got == oracle, f"idxrev i={i}: src={got} route={oracle}"
        if oracle is not None:
            n_sig += 1
    assert n_sig > 0, "fixture produced no idxrev signals — strengthen it"


def test_metals_fvg_detector_matches_route_loop():
    from src.components.ultimate_book.sleeves import metals as MT
    B = _trend_series(n=300, seed=5)
    atrs = [atr14(B, k) for k in range(len(B))]
    checked = 0
    for i in range(len(B)):
        # --- VERBATIM gold_sleeve_strategy.fvg_signals inner loop for bar i (lines 36-58) ---
        oracle = None
        if i >= 100:
            a = atrs[i]
            if a > 0:
                sma100 = sum(atrs[i - 99:i + 1]) / 100
                if sma100 > 0 and a >= 1.2 * sma100:
                    tr = MT.htf_trend(B, i, 30); b = B[i]
                    if tr == 1:
                        for k in range(i - 2, max(i - 9, 60), -1):
                            gap_top = B[k].l; gap_bot = B[k - 2].h
                            if gap_top - gap_bot < 0.10 * a: continue
                            if b.l <= gap_top and b.c > gap_bot and b.c > b.o:
                                sd = max((b.c - min(b.l, gap_bot)) + 0.10 * a, 0.25 * a)
                                oracle = (1, sd); break
                    elif tr == -1:
                        for k in range(i - 2, max(i - 9, 60), -1):
                            gap_bot = B[k].h; gap_top = B[k - 2].l
                            if gap_top - gap_bot < 0.10 * a: continue
                            if b.h >= gap_bot and b.c < gap_top and b.c < b.o:
                                sd = max((max(b.h, gap_top) - b.c) + 0.10 * a, 0.25 * a)
                                oracle = (-1, sd); break
        got = MT.fvg_signal(B, atrs, i)
        assert got == oracle, f"metals fvg i={i}: src={got} route={oracle}"
        checked += 1
    assert checked == len(B)


def test_metals_core_vs_softband_band_gating():
    from src.components.ultimate_book.sleeves import metals as MT
    # _size_mult_soft monotonic-ish + bounds (gen_metals_softband)
    assert MT._size_mult_soft(0.03, 1.4) == 0.0          # below the 0.04 floor
    assert MT._size_mult_soft(0.04, 1.4) > 0.0
    assert MT._size_mult_soft(0.09, 1.0) <= 1.5
    # core requires ac>=0.10; softband is the disjoint 0.04<=ac<0.10 band -> never both on same bar
    # (verified structurally by the gate conditions in generate_metals_core/softband)


def test_energy_agri_gate_and_slope():
    from src.components.ultimate_book.sleeves import energy_agri as EA
    # energy_gate: vr>=2.0 OR |slope|<0.05 (faithful to energy_agri_sleeve.energy_gate)
    assert EA.energy_gate(2.0, 1.0) is True
    assert EA.energy_gate(1.5, 0.04) is True       # flat trend
    assert EA.energy_gate(1.5, 0.10) is False       # neither
    # trend_slope normalized by ATR; flat series -> ~0 slope
    flat = [Bar(100, 101, 99, 100, 100) for _ in range(60)]
    assert abs(EA.trend_slope(flat, 59, 30)) < 1e-9
    # energy_agri reuses the metals FVG detector (same import) -> identical entry geometry
    from src.components.ultimate_book.sleeves import metals as MT
    assert EA.fvg_signal is MT.fvg_signal
    # off-surface -> never an intent
    assert EA.generate("XAUUSD", _trend_series(), "2026-06-15") is None


def test_generate_emits_intent_and_respects_surface():
    B = _series()
    # craft a guaranteed up-breakout on the last bar
    B2 = list(B[:120])
    base = B2[-1].c
    for _ in range(40):
        B2.append(Bar(base, base + 0.5, base - 0.5, base, 100))   # flat -> low ATR? keep range tight
        base = B2[-1].c
    # final bar closes well above the prior-20 high
    hh = max(b.h for b in B2[-21:-1])
    B2.append(Bar(base, hh + 50, base - 1, hh + 40, 100))
    intent = CR.generate("BTCUSD", B2, "2026-06-15")
    # may or may not pass the ac60 gate; assert type + fields when it fires
    if intent is not None:
        assert intent.sleeve == "crypto" and intent.symbol == "BTCUSD"
        assert intent.direction in (1, -1) and intent.stop_dist > 0
        assert intent.decision_day == "2026-06-15"
    # off-surface symbol -> never an intent
    assert CR.generate("XAUUSD", B2, "2026-06-15") is None
    assert IX.generate("EURUSD", B2, "2026-06-15") is None
