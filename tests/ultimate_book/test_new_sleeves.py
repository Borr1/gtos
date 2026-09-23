"""test_new_sleeves.py — generator-contract checks for the default-off candidate sleeves.

Unit-level: leak-free generator contract, no false-fire on flat/insufficient/wrong-symbol data, and constructed
fires producing well-formed TradeIntent objects. These tests do not prove book promotion by themselves; current
promotion confidence is enforced separately by the daily-unit/unified-MC consistency tests and registry metadata.
"""
import sys
# NOTE 2026-07-26: a hardcoded sys.path.insert(0, "/Users/borr/Documents/gtos/repo/
# ai-trading-agent") was removed here. It prepended a DIFFERENT, stale checkout, so this
# file silently tested that repo instead of the working tree whenever it ran in isolation
# (in a full-suite run sys.modules was already populated, so the same tests exercised the
# real code and could disagree). Tests must import the tree they are checked out in.
from src.components.ultimate_book.primitives import Bar
from src.components.ultimate_book.sleeves import vol_squeeze as VS, vol_compression as VC, asian_fade as AF
from src.components.ultimate_book.sleeves import ny_crypto_momentum as NM
from src.components.ultimate_book.sleeves import ny_index_momentum as NIM
from src.components.ultimate_book.sleeves import structural_retest as SRS
from src.components.ultimate_book.sleeves import metal_session_reversion as MSR
from src.components.ultimate_book.sleeves import asia_pdl_fade as PDL
from src.components.ultimate_book.sleeves import liq_asia_up_low_metal as LIQ
from src.components.ultimate_book.sleeves import orb_crypto_london as ORB
from src.components.ultimate_book.sleeves import kz_london_crypto_low as KLZ
from src.components.ultimate_book.sleeves import vss_fxcross_london_up_low as VSS


def _m15_times(start_iso, n):
    """n consecutive 15-min ISO timestamps from start_iso (no tz; matches the research bar_times)."""
    import datetime as dt
    t0 = dt.datetime.fromisoformat(start_iso)
    return [(t0 + dt.timedelta(minutes=15 * k)).isoformat() for k in range(n)]


def test_asian_fade_contract_no_false_fire():
    # flat M15, off-surface, missing times, insufficient warmup -> all None
    n = 260
    times = _m15_times("2026-06-01T00:00:00", n)
    flat = [Bar(100, 100.02, 99.98, 100, 100) for _ in range(n)]
    assert AF.generate("EURUSD", flat, "2026-06-04", bar_times=times) is None      # flat -> no break
    assert AF.generate("XAUUSD", flat, "2026-06-04", bar_times=times) is None      # off-surface
    assert AF.generate("EURUSD", flat, "2026-06-04", bar_times=None) is None       # needs times
    assert AF.generate("EURUSD", flat[:50], "2026-06-04", bar_times=times[:50]) is None  # warmup


def test_asian_fade_fires_on_rejected_break():
    # 200 prior-day warmup bars (distinct earlier days), then ONE clean test day: a tight Asian range
    # (hours 0-7) and an hour-8 bar that spikes ABOVE the range high then closes back inside (rejection)
    # -> fade SHORT. Times are real 15-min stamps so _hour/_day resolve correctly (incl midnight hour 0).
    bars, times = [], []
    # warmup: 210 bars across prior days, gently varying so atr14 > 0
    warm_t = _m15_times("2026-05-20T00:00:00", 210)
    for k in range(210):
        px = 100.0 + 0.01 * (k % 7)
        bars.append(Bar(px, px + 0.05, px - 0.05, px + 0.01, 100)); times.append(warm_t[k])
    # test day 2026-06-17: 32 Asian bars (00:00..07:45) tight in [99.90, 100.10]
    day_t = _m15_times("2026-06-17T00:00:00", 33)
    for k in range(32):
        c = 100.0 + (0.06 if k % 2 else -0.06)
        bars.append(Bar(c, 100.10, 99.90, c, 100)); times.append(day_t[k])
    # hour-8 bar (08:00): spikes well above the Asian high, closes back inside -> rejection up-break
    bars.append(Bar(100.05, 100.80, 100.00, 100.10, 100)); times.append(day_t[32])
    it = AF.generate("EURUSD", bars, "2026-06-17", bar_times=times)
    assert it is not None, "rejected break above the Asian range must fire a fade"
    assert it.sleeve == "asian_fade" and it.direction == -1, "up-break is faded SHORT"
    assert it.stop_dist > 0 and it.target_dist is None, "trail exit -> target_dist None by design"


def test_no_false_fire_flat_or_wrong_symbol():
    flat = [Bar(100, 100.1, 99.9, 100, 100) for _ in range(200)]   # zero-trend, tiny range
    assert VS.generate("GER40", flat, "2026-06-17") is None         # no expansion/trend -> None
    assert VC.generate("BTCUSD", flat, "2026-06-17") is None        # no breakout -> None
    assert VS.generate("XAUUSD", flat, "2026-06-17") is None        # off-surface symbol -> None
    assert VC.generate("XAUUSD", flat, "2026-06-17") is None
    assert VS.generate("GER40", flat[:50], "2026-06-17") is None    # insufficient bars -> None


def test_vol_compression_fires_on_squeeze_breakout():
    # 130 D1 bars: ranges SHRINK over time (so recent ATR is in the low quantile of its history = squeeze),
    # price held in a band ~100, then the LAST bar closes above the prior 20-bar high -> long breakout.
    bars = []
    for k in range(129):
        rng = max(0.4, 3.0 - k * 0.02)          # range shrinks 3.0 -> ~0.4 (compression into the present)
        c = 100.0 + (0.3 if k % 2 else -0.3)    # oscillate tightly in a band (no trend, stays in 20-bar range)
        bars.append(Bar(c, c + rng / 2, c - rng / 2, c, 100))
    hh = max(b.h for b in bars[-20:])
    bars.append(Bar(100.0, hh + 2.0, 99.8, hh + 1.5, 100))   # breakout bar: close above the 20-bar high
    it = VC.generate("BTCUSD", bars, "2026-06-17")
    assert it is not None, "compression+upside-breakout must fire"
    assert it.sleeve == "vol_compression" and it.direction == 1
    assert it.stop_dist > 0 and abs(it.target_dist - VC.TARGET_R * it.stop_dist) < 1e-9


def test_vol_squeeze_fires_on_squeeze_expansion_uptrend():
    # ~95 H4 bars: a slow steady uptrend with SMALL ranges (compressed) so htf_trend(50)=+1 and ATR is low,
    # then a final WIDE up-expansion bar (range >> ATR, big up body) -> long.
    bars = []
    px = 100.0
    for k in range(94):
        px += 0.25                               # steady uptrend (close-close[50] >> ATR -> trend=+1)
        bars.append(Bar(px - 0.1, px + 0.15, px - 0.15, px, 100))   # tight ranges (~0.3) = compression
    # expansion bar: wide range, strong up body, close well above open
    o = px
    bars.append(Bar(o, o + 3.0, o - 0.2, o + 2.6, 100))
    it = VS.generate("GER40", bars, "2026-06-17")
    assert it is not None, "squeeze+up-expansion in uptrend must fire long"
    assert it.sleeve == "vol_squeeze" and it.direction == 1
    assert it.stop_dist > 0 and abs(it.target_dist - VS.TARGET_R * it.stop_dist) < 1e-9


def _times_ending_at(hour, minute, n):
    """n consecutive 15-min UTC stamps whose LAST stamp is at BROKER-SERVER (hour:minute).

    The sleeve session constants are FTMO **server** hours, while the live feed delivers **true
    UTC** (F7/B29). Before 2026-07-26 this helper emitted naive stamps and the sleeves compared
    `.hour` directly, so "server 17:00" and "UTC 17:00" were the same string and the tests could
    not tell the two clocks apart — which is exactly the defect. It now emits real UTC stamps for
    the requested server wall time, so `hour` here means what the sleeve constants mean.

    Derived from the measured rule rather than a fixed offset: `NEW_YORK_PLUS_7` is +3 in summer
    and +2 in winter, so hardcoding either would make this helper wrong for ~4 weeks a year.
    """
    import datetime as dt
    from src.utils.broker_clock import NEW_YORK_PLUS_7, broker_naive_to_utc
    server_end = dt.datetime(2026, 6, 17, hour, minute)          # broker wall clock
    end = broker_naive_to_utc(server_end, NEW_YORK_PLUS_7)       # -> true UTC, tz-aware
    return [(end - dt.timedelta(minutes=15 * (n - 1 - k))).isoformat() for k in range(n)]


def test_ny_crypto_momentum_contract_no_false_fire():
    n = 540
    flat = [Bar(100, 100.3, 99.7, 100, 100) for _ in range(n)]
    at_ny = _times_ending_at(17, 0, n)        # last bar IS the NY decision bar
    off_ny = _times_ending_at(11, 0, n)       # last bar is NOT 17:00
    assert NM.generate("BTCUSD", flat, "2026-06-17", bar_times=off_ny) is None    # wrong hour
    assert NM.generate("BTCUSD", flat, "2026-06-17", bar_times=at_ny) is None     # flat window -> |de|<0.5
    assert NM.generate("XAUUSD", flat, "2026-06-17", bar_times=at_ny) is None     # off-surface
    assert NM.generate("BTCUSD", flat, "2026-06-17", bar_times=None) is None      # needs times
    assert NM.generate("BTCUSD", flat[:50], "2026-06-17", bar_times=at_ny[:50]) is None  # warmup


def test_ny_crypto_momentum_fires_on_clean_notlow_ny_uptrend():
    # 540 M15 bars, last bar at 17:00. The history is mostly normal range, then the NY window rises cleanly
    # with wider current ATR, putting ATR14 in the NOT-LOW bucket and firing momentum-continuation LONG.
    n = 540
    bars = []
    for k in range(n - 13):
        px = 100.0 + 0.02 * (k % 5)
        bars.append(Bar(px, px + 0.25, px - 0.25, px, 100))
    for j in range(13):                         # clean up-move 100 -> 104 over the NY window
        c = 100.0 + 4.0 * (j / 12.0)
        bars.append(Bar(c - 0.05, c + 0.6, c - 0.4, c, 100))
    times = _times_ending_at(17, 0, n)
    it = NM.generate("BTCUSD", bars, "2026-06-17", bar_times=times)
    assert it is not None, "clean NY uptrend at the 17:00 decision bar must fire a continuation long"
    assert it.sleeve == "ny_crypto_momentum" and it.direction == 1
    assert it.stop_dist > 0 and it.target_dist is None, "time-stop/hold-to-close exit -> target_dist None"


def test_ny_crypto_momentum_rejects_low_vol_clean_ny_uptrend():
    # Same clean NY directional-efficiency shape as the fire test, but after a high-vol history the current
    # ATR14 ranks LOW, so the refined sleeve must stand aside.
    n = 540
    bars = [Bar(100, 101.5, 98.5, 100, 100) for _ in range(n - 13)]
    for j in range(13):
        c = 100.0 + 0.6 * (j / 12.0)
        bars.append(Bar(c - 0.02, c + 0.05, c - 0.05, c, 100))
    times = _times_ending_at(17, 0, n)
    assert NM.generate("BTCUSD", bars, "2026-06-17", bar_times=times) is None


def test_kz_london_crypto_low_contract_and_fire():
    n = 540
    flat = [Bar(100, 100.3, 99.7, 100, 100) for _ in range(n)]
    london = _times_ending_at(12, 0, n)
    ny = _times_ending_at(17, 0, n)
    assert KLZ.generate("XAUUSD", flat, "2026-06-17", bar_times=london) is None
    assert KLZ.generate("BTCUSD", flat, "2026-06-17", bar_times=ny) is None
    assert KLZ.generate("BTCUSD", flat, "2026-06-17", bar_times=None) is None
    assert KLZ.generate("BTCUSD", flat[:100], "2026-06-17", bar_times=london[:100]) is None

    bars = [Bar(100, 101.5, 98.5, 100, 100) for _ in range(n - 13)]
    for j in range(13):
        c = 100.0 + 0.6 * (j / 12.0)
        bars.append(Bar(c - 0.02, c + 0.05, c - 0.05, c, 100))
    it = KLZ.generate("BTCUSD", bars, "2026-06-17", bar_times=london)
    assert it is not None, "clean low-vol London crypto move at 12:00 must fire"
    assert it.sleeve == "kz_london_crypto_low" and it.direction == 1
    assert it.stop_dist > 0 and it.target_dist is None


def test_kz_london_crypto_low_rejects_not_low_vol():
    n = 540
    bars = [Bar(100, 100.05, 99.95, 100, 100) for _ in range(n - 13)]
    for j in range(13):
        c = 100.0 + 5.0 * (j / 12.0)
        bars.append(Bar(c - 0.2, c + 2.0, c - 2.0, c, 100))
    london = _times_ending_at(12, 0, n)
    assert KLZ.generate("BTCUSD", bars, "2026-06-17", bar_times=london) is None


def test_ny_index_momentum_contract_no_false_fire():
    n = 540
    flat = [Bar(100, 100.3, 99.7, 100, 100) for _ in range(n)]
    at_ny = _times_ending_at(17, 0, n)
    off_ny = _times_ending_at(11, 0, n)
    assert NIM.generate("SPX500", flat, "2026-06-17", bar_times=off_ny) is None      # wrong hour
    assert NIM.generate("BTCUSD", flat, "2026-06-17", bar_times=at_ny) is None        # off-surface (crypto)
    assert NIM.generate("SPX500", flat[:100], "2026-06-17", bar_times=at_ny[:100]) is None  # warmup


def test_ny_index_momentum_fires_mid_vol_clean_uptrend():
    # 540 M15 bars, last at 17:00. Build a TWO-BLOCK vol history so the trailing-480 ATR distribution is
    # spread (low block ~0.5, high block ~1.5); the NY window has range ~1.0 (=> ATR14 lands MID-percentile)
    # AND a clean rising close (|de| >> 0.5) -> continuation LONG, mid-vol gate satisfied.
    n = 540
    bars = []
    for k in range(261):                       # low-vol block: TR ~0.5
        bars.append(Bar(100, 100.25, 99.75, 100, 100))
    for k in range(261, n - 13):               # high-vol block: TR ~1.5
        bars.append(Bar(100, 100.75, 99.25, 100, 100))
    base = 100.0
    for j in range(13):                        # NY window: range ~1.0, close marches up cleanly
        c = base + 0.85 * j
        bars.append(Bar(c - 0.1, c + 0.4, c - 0.6, c, 100))
    times = _times_ending_at(17, 0, n)
    it = NIM.generate("SPX500", bars, "2026-06-17", bar_times=times)
    # the construction targets mid-vol; if the ATR lands mid it must fire a continuation long
    assert it is not None, "clean NY uptrend in mid-vol must fire an index continuation long"
    assert it.sleeve == "ny_index_momentum" and it.direction == 1
    assert it.stop_dist > 0 and it.target_dist is None


def test_structural_retest_contract_no_false_fire():
    # The fire path is proven on 1215/1215 real-data samples across all 3 whitelist cells
    # (verify_structural_retest_sleeve.py, 0 fp). Unit-level: the gates must REJECT — off-surface, insufficient
    # warmup, and a calm low-vol series in a NON-whitelisted (class,session,regime) cell must all return None.
    n = 600
    up = [Bar(100 + 0.1 * k, 100 + 0.1 * k + 0.2, 100 + 0.1 * k - 0.2, 100 + 0.1 * k, 100) for k in range(n)]
    ny = _times_ending_at(18, 0, n)
    assert SRS.generate("EURUSD", up, "2026-06-17", bar_times=ny) is None          # off-surface (no class)
    assert SRS.generate("BTCUSD", up, "2026-06-17", bar_times=ny) is None          # crypto NY uptrend low-vol -> not whitelisted
    assert SRS.generate("BTCUSD", up[:200], "2026-06-17", bar_times=ny[:200]) is None  # warmup
    assert SRS.generate("BTCUSD", up, "2026-06-17", bar_times=None) is None         # needs times


def test_metal_session_reversion_contract_and_fire():
    # contract: off-surface / non-NY / warmup -> None
    n = 320
    flat = [Bar(100, 100.2, 99.8, 100, 100) for _ in range(n)]
    ny = _times_ending_at(16, 0, n)
    asia = _times_ending_at(3, 0, n)
    assert MSR.generate("BTCUSD", flat, "2026-06-17", bar_times=ny) is None        # off-surface
    assert MSR.generate("XAUUSD", flat, "2026-06-17", bar_times=asia) is None       # not NY
    assert MSR.generate("XAUUSD", flat[:100], "2026-06-17", bar_times=ny[:100]) is None  # warmup
    # fire: a DOWNTREND (regime dn) then today's NY session extends DOWN from the anchor -> FADE LONG.
    bars = []
    for k in range(300):                          # steady downtrend -> ema_f < ema_s -> regime 'dn'
        c = 1000.0 - 1.0 * k
        bars.append(Bar(c + 0.3, c + 0.5, c - 0.5, c, 100))
    a0 = bars[-1].c                               # ~700; today's NY anchor opens here
    bars.append(Bar(a0, a0 + 0.4, a0 - 0.4, a0 - 0.1, 100))   # anchor bar (first NY bar today)
    for j in range(6):                            # a few NY bars hovering near the anchor (no early extension)
        bars.append(Bar(a0 - 0.1, a0 + 0.2, a0 - 0.3, a0 - 0.1, 100))
    bars.append(Bar(a0 - 0.1, a0 + 0.1, a0 - 4.0, a0 - 3.5, 100))   # sharp drop: dev <= -Z*ATR -> first down-ext
    # timestamps: last bar at 16:00 NY; the 8 today-bars (anchor..fire) land in 14:15..16:00
    times = _times_ending_at(16, 0, len(bars))
    it = MSR.generate("XAUUSD", bars, "2026-06-17", bar_times=times)
    assert it is not None, "down-extension from the NY anchor in a downtrend must fire a fade LONG"
    assert it.sleeve == "metal_session_reversion" and it.direction == 1
    assert it.stop_dist > 0 and it.target_dist is None


def test_asia_pdl_fade_contract_and_fire():
    import datetime as dt
    # contract: off-surface / non-Asian hour -> None
    n = 200
    flat = [Bar(100, 100.2, 99.8, 100, 100) for _ in range(n)]
    asia = [(dt.datetime(2026, 6, 17, 1, 0) - dt.timedelta(minutes=15 * (n - 1 - k))).isoformat() for k in range(n)]
    london = [(dt.datetime(2026, 6, 17, 10, 0) - dt.timedelta(minutes=15 * (n - 1 - k))).isoformat() for k in range(n)]
    assert PDL.generate("BTCUSD", flat, "2026-06-17", bar_times=london) is None    # not Asian session
    assert PDL.generate("ZZZ", flat, "2026-06-17", bar_times=asia) is None          # off-surface
    # fire: a prior day with low 99.0, then an Asian bar today pierces below it and reclaims -> LONG fade.
    bars = []
    times = []
    base = dt.datetime(2026, 6, 15, 0, 0)
    # two full prior days (96 bars each), the SECOND (prior day) carries the 99.00 low
    for day in range(2):
        for b in range(96):
            t = base + dt.timedelta(days=day, minutes=15 * b)
            lo = 99.0 if (day == 1 and b == 50) else 99.8     # prior-day low = 99.00
            bars.append(Bar(100.0, 100.2, lo, 100.0, 100)); times.append(t.isoformat())
    # today's Asian bars: a few hovering above PDL (no sweep), then the sweep+reclaim at the last bar
    today = dt.datetime(2026, 6, 17, 0, 0)
    for b in range(4):
        t = today + dt.timedelta(minutes=15 * b)
        bars.append(Bar(100.0, 100.2, 99.7, 100.0, 100)); times.append(t.isoformat())
    t = today + dt.timedelta(minutes=15 * 4)                    # 01:00 sweep bar: dips to 98.5, closes 99.2
    bars.append(Bar(100.0, 100.3, 98.5, 99.2, 100)); times.append(t.isoformat())
    it = PDL.generate("EURUSD", bars, "2026-06-17", bar_times=times)
    assert it is not None, "Asian sweep+reclaim of the prior-day low must fire a LONG fade"
    assert it.sleeve == "asia_pdl_fade" and it.direction == 1
    assert it.stop_dist > 0 and abs(it.target_dist - PDL.TARGET_R * it.stop_dist) < 1e-9


def _liq_asia_up_low_metal_series(*, current_low_vol=True):
    """Build the PDH sweep+reclaim fixture on the BROKER-SERVER clock.

    The datetimes below are server wall clock, which is the clock the sleeve's day key and
    session window use (F7/B29). They are emitted as true-UTC stamps because that is what the
    live feed delivers. Before 2026-07-26 they were emitted naive and the prior-day high was
    selected by slicing the same naive string, so the fixture and the sleeve agreed only because
    both were wrong in the same direction.
    """
    import datetime as dt
    from src.utils.broker_clock import NEW_YORK_PLUS_7, broker_naive_to_utc

    bars = []
    times = []          # true-UTC ISO stamps, as the live feed delivers
    server_days = []    # the SERVER calendar day of each bar, for prior-day selection
    start = dt.datetime(2026, 5, 18, 0, 0)
    for day in range(30):
        base = 100.0 + 2.0 * day
        for b in range(96):
            server_t = start + dt.timedelta(days=day, minutes=15 * b)
            c = base + 0.05 * ((b % 4) - 1.5)
            bars.append(Bar(base, base + 1.0, base - 1.0, c, 100))
            times.append(broker_naive_to_utc(server_t, NEW_YORK_PLUS_7).isoformat())
            server_days.append(server_t.date().isoformat())

    pdh = max(b.h for b, d in zip(bars, server_days) if d == "2026-06-16")
    today = dt.datetime(2026, 6, 17, 0, 0)
    for b in range(24):
        server_t = today + dt.timedelta(minutes=15 * b)
        c = pdh - 0.30 + 0.01 * (b % 3)
        if current_low_vol:
            bars.append(Bar(c, c + 0.08, c - 0.08, c, 100))
        else:
            bars.append(Bar(c, c + 2.0, c - 2.0, c, 100))
        times.append(broker_naive_to_utc(server_t, NEW_YORK_PLUS_7).isoformat())
        server_days.append(server_t.date().isoformat())

    bars[-1] = Bar(pdh - 0.15, pdh + 0.35, pdh - 0.25, pdh - 0.05, 100)
    return bars, times


def test_liq_asia_up_low_metal_contract_and_fire():
    n = 650
    flat = [Bar(100, 100.2, 99.8, 100, 100) for _ in range(n)]
    asia = _times_ending_at(5, 45, n)
    london = _times_ending_at(10, 0, n)
    assert LIQ.generate("EURUSD", flat, "2026-06-17", bar_times=asia) is None
    assert LIQ.generate("XAUUSD", flat, "2026-06-17", bar_times=london) is None
    assert LIQ.generate("XAUUSD", flat[:50], "2026-06-17", bar_times=asia[:50]) is None
    assert LIQ.generate("XAUUSD", flat, "2026-06-17", bar_times=None) is None

    bars, times = _liq_asia_up_low_metal_series(current_low_vol=True)
    it = LIQ.generate("XAUUSD", bars, "2026-06-17", bar_times=times)
    assert it is not None, "low-vol Asian PDH sweep+reclaim in prior-D1 up regime must fire"
    assert it.sleeve == "liq_asia_up_low_metal" and it.direction == -1
    assert it.stop_dist > 0 and abs(it.target_dist - LIQ.TARGET_R * it.stop_dist) < 1e-9


def test_liq_asia_up_low_metal_rejects_nonlow_vol_sweep():
    bars, times = _liq_asia_up_low_metal_series(current_low_vol=False)
    assert LIQ.generate("XAUUSD", bars, "2026-06-17", bar_times=times) is None


def _d1_up_aux(n=60):
    import datetime as dt

    bars = []
    times = []
    start = dt.date(2026, 4, 1)
    for k in range(n):
        close = 100.0 + k
        bars.append(Bar(close, close, close, close, 0))
        times.append((start + dt.timedelta(days=k)).isoformat())
    return bars, times


def _vss_fire_series():
    n = 260
    bars = []
    for k in range(220):
        c = 40.0 + 0.30 * k
        bars.append(Bar(c - 0.05, c + 0.20, c - 0.20, c, 100))
    for k in range(39):
        c = 100.0 + 0.02 * ((k % 4) - 1.5)
        bars.append(Bar(c, c + 0.08, c - 0.08, c, 100))
    bars.append(Bar(100.05, 100.48, 100.02, 100.45, 100))
    return bars, _times_ending_at(10, 0, n)


def test_vss_fxcross_london_up_low_contract_and_fire():
    n = 260
    flat = [Bar(100, 100.2, 99.8, 100, 100) for _ in range(n)]
    london = _times_ending_at(10, 0, n)
    asia = _times_ending_at(3, 0, n)
    aux_bars, aux_times = _d1_up_aux()
    assert VSS.generate("BTCUSD", flat, "2026-06-17", bar_times=london, aux_bars=aux_bars, aux_times=aux_times) is None
    assert VSS.generate("EURJPY", flat, "2026-06-17", bar_times=asia, aux_bars=aux_bars, aux_times=aux_times) is None
    assert VSS.generate("EURJPY", flat, "2026-06-17", bar_times=london) is None
    assert VSS.generate("EURJPY", flat[:100], "2026-06-17", bar_times=london[:100], aux_bars=aux_bars, aux_times=aux_times) is None

    bars, times = _vss_fire_series()
    it = VSS.generate("EURJPY", bars, "2026-06-17", bar_times=times, aux_bars=aux_bars, aux_times=aux_times)
    assert it is not None, "London D1-up low-vol squeeze breakout must fire"
    assert it.sleeve == "vss_fxcross_london_up_low" and it.direction == 1
    assert it.stop_dist > 0 and abs(it.target_dist - VSS.TGT_ATR * it.stop_dist) < 1e-9


def test_vss_fxcross_london_up_low_requires_d1_up_aux():
    bars, times = _vss_fire_series()
    down_aux = [Bar(200 - k, 200 - k, 200 - k, 200 - k, 0) for k in range(60)]
    aux_times = _d1_up_aux()[1]
    assert VSS.generate("EURJPY", bars, "2026-06-17", bar_times=times, aux_bars=down_aux, aux_times=aux_times) is None


def test_orb_crypto_london_contract_no_false_fire():
    # Fire path proven on 160/160 real-data samples (verify_orb_crypto_london_sleeve.py). Unit-level: the gates
    # must REJECT — off-surface, non-London-window hour, insufficient warmup, and a calm low-vol RANGE (no trend
    # / no breakout) must all return None.
    import datetime as dt
    n = 560
    flat = [Bar(100, 100.1, 99.9, 100, 100) for _ in range(n)]
    lon = [(dt.datetime(2026, 6, 17, 9, 0) - dt.timedelta(minutes=15 * (n - 1 - k))).isoformat() for k in range(n)]
    asia = [(dt.datetime(2026, 6, 17, 2, 0) - dt.timedelta(minutes=15 * (n - 1 - k))).isoformat() for k in range(n)]
    assert ORB.generate("XAUUSD", flat, "2026-06-17", bar_times=lon) is None      # off-surface (not crypto)
    assert ORB.generate("BTCUSD", flat, "2026-06-17", bar_times=asia) is None      # not the London break window
    assert ORB.generate("BTCUSD", flat, "2026-06-17", bar_times=lon) is None       # flat range, no trend/breakout
    assert ORB.generate("BTCUSD", flat[:300], "2026-06-17", bar_times=lon[:300]) is None  # warmup
    assert ORB.generate("BTCUSD", flat, "2026-06-17", bar_times=None) is None       # needs times


if __name__ == "__main__":
    import traceback
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    p = 0
    for fn in fns:
        try:
            fn(); p += 1; print(f"PASS {fn.__name__}")
        except Exception:
            print(f"FAIL {fn.__name__}"); traceback.print_exc()
    print(f"\n{p}/{len(fns)} new-sleeve tests passed")
    assert p == len(fns)
