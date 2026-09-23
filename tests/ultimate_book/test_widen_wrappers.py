"""test_widen_wrappers.py — F5 ceremony 20260825 WIDEN wrapper contracts.

Pins: a wrapper never fires when its incumbent would not; the sleeve name is
replaced; stop scaling matches the shipped constants (asian_fade ATR+5pip
floor, ny 2.75/1.3, orb 1.72); incumbents keep their own names; the WIDEN
registry stays OUT of CANDIDATES (MC pin) while active_specs and the
admission registry pick the tags up under include_candidate_book.
"""
import datetime as dt

from src.components.ultimate_book.primitives import Bar
from src.components.ultimate_book.admission import (
    TradeIntent, WIDEN_ADMISSION_CONFIDENCE, widen_registry, cluster_of,
)
from src.components.ultimate_book.sleeves import asian_fade as AF
from src.components.ultimate_book.sleeves import asian_fade_widen as AFW
from src.components.ultimate_book.sleeves import ny_crypto_momentum as NM
from src.components.ultimate_book.sleeves import ny_crypto_momentum_widen as NMW
from src.components.ultimate_book.sleeves import orb_crypto_london as ORB
from src.components.ultimate_book.sleeves import orb_crypto_london_widen as ORBW
from src.components.ultimate_book.sleeves.registry import (
    BUILT, CANDIDATE_BUILT, WIDEN_BUILT, active_specs,
)
from src.components.ultimate_book.execution_packets import SLEEVE_EXIT_PROFILES


def _m15_times(start_iso, n):
    t0 = dt.datetime.fromisoformat(start_iso)
    return [(t0 + dt.timedelta(minutes=15 * k)).isoformat() for k in range(n)]


def _asian_fade_fire_fixture():
    """The proven rejected-break fixture from test_new_sleeves (fires SHORT)."""
    bars, times = [], []
    warm_t = _m15_times("2026-05-20T00:00:00", 210)
    for k in range(210):
        px = 100.0 + 0.01 * (k % 7)
        bars.append(Bar(px, px + 0.05, px - 0.05, px + 0.01, 100)); times.append(warm_t[k])
    day_t = _m15_times("2026-06-17T00:00:00", 33)
    for k in range(32):
        c = 100.0 + (0.06 if k % 2 else -0.06)
        bars.append(Bar(c, 100.10, 99.90, c, 100)); times.append(day_t[k])
    bars.append(Bar(100.05, 100.80, 100.00, 100.10, 100)); times.append(day_t[32])
    return bars, times


def test_widen_no_fire_when_incumbent_none():
    n = 260
    times = _m15_times("2026-06-01T00:00:00", n)
    flat = [Bar(100, 100.02, 99.98, 100, 100) for _ in range(n)]
    assert AFW.generate("EURUSD", flat, "2026-06-04", bar_times=times) is None
    assert AFW.generate("XAUUSD", flat, "2026-06-04", bar_times=times) is None
    flat_c = [Bar(100, 100.1, 99.9, 100, 100) for _ in range(600)]
    assert NMW.generate("BTCUSD", flat_c, "2026-06-17") is None
    assert ORBW.generate("BTCUSD", flat_c, "2026-06-17") is None
    assert NMW.generate("XAUUSD", flat_c, "2026-06-17") is None


def test_asian_fade_widen_scales_and_renames():
    bars, times = _asian_fade_fire_fixture()
    base = AF.generate("EURUSD", bars, "2026-06-17", bar_times=times)
    wide = AFW.generate("EURUSD", bars, "2026-06-17", bar_times=times)
    assert base is not None and wide is not None
    assert base.sleeve == "asian_fade", "incumbent keeps its own name"
    assert wide.sleeve == "asian_fade_widen"
    assert wide.direction == base.direction and wide.symbol == base.symbol
    atr = base.stop_dist / AF.STOP_K
    pip_floor = 5.0 * 0.0001  # MARKET_STOP_MIN_PIPS * EURUSD pip
    expect = max(1.0 * atr, pip_floor, base.stop_dist)
    assert abs(wide.stop_dist - expect) < 1e-12
    assert wide.stop_dist >= base.stop_dist, "WIDEN may never narrow"
    assert wide.stop_dist >= pip_floor
    assert wide.target_dist is not None and abs(wide.target_dist - AFW.TARGET_R * wide.stop_dist) < 1e-12


def test_asian_fade_widen_pip_floor_binds_when_atr_tiny(monkeypatch):
    # R1 case: if the incumbent stop (0.6*ATR) is microscopic, the 5-pip floor
    # must carry the widened stop.
    tiny = TradeIntent(sleeve="asian_fade", symbol="EURUSD", direction=-1,
                       decision_day="2026-06-17", stop_dist=0.00006, target_dist=None)
    monkeypatch.setattr(AF, "generate", lambda *a, **k: tiny)
    wide = AFW.generate("EURUSD", [], "2026-06-17", bar_times=[])
    assert wide is not None
    assert abs(wide.stop_dist - 0.0005) < 1e-15, "5-pip floor must bind"


def test_ny_and_orb_scale_constants(monkeypatch):
    proto = TradeIntent(sleeve="ny_crypto_momentum", symbol="BTCUSD", direction=1,
                        decision_day="2026-06-17", stop_dist=120.0, target_dist=None)
    monkeypatch.setattr(NM, "generate", lambda *a, **k: proto)
    w = NMW.generate("BTCUSD", [], "2026-06-17")
    assert w.sleeve == "ny_crypto_momentum_widen"
    assert abs(w.stop_dist - 120.0 * (2.75 / NM.STOP_MULT)) < 1e-9
    assert w.target_dist is None

    proto2 = TradeIntent(sleeve="orb_crypto_london", symbol="ETHUSD", direction=-1,
                         decision_day="2026-06-17", stop_dist=30.0, target_dist=60.0)
    monkeypatch.setattr(ORB, "generate", lambda *a, **k: proto2)
    w2 = ORBW.generate("ETHUSD", [], "2026-06-17")
    assert w2.sleeve == "orb_crypto_london_widen"
    assert abs(w2.stop_dist - 30.0 * 1.72) < 1e-9
    assert abs(w2.target_dist - 60.0 * 1.72) < 1e-9


def test_widen_wiring_parallel_to_candidates():
    widen_names = {"asian_fade_widen", "ny_crypto_momentum_widen", "orb_crypto_london_widen"}
    # MC pin: WIDEN stays out of CANDIDATE_BUILT and out of the default BUILT book.
    assert not (widen_names & set(CANDIDATE_BUILT))
    assert not (widen_names & set(BUILT))
    assert set(WIDEN_BUILT) == widen_names
    # active_specs picks them up only under include_candidate_book (Q16).
    # (registry SleeveSpec keys on .tag, admission SleeveSpec on .name)
    default_names = {s.tag for s in active_specs(None)}
    assert not (widen_names & default_names)
    cb_names = {s.tag for s in active_specs(None, include_candidate_book=True)}
    assert widen_names <= cb_names
    # admission registry + cluster resolution.
    reg = widen_registry()
    assert set(reg) == widen_names == set(WIDEN_ADMISSION_CONFIDENCE)
    assert cluster_of("asian_fade_widen") == "fx_reversion"
    assert cluster_of("ny_crypto_momentum_widen") == "crypto"
    # exit contracts declared for all three.
    assert widen_names <= set(SLEEVE_EXIT_PROFILES)
    assert SLEEVE_EXIT_PROFILES["asian_fade_widen"]["policy"] == "time_stop"
    assert SLEEVE_EXIT_PROFILES["asian_fade_widen"]["final_target_r"] == 2.0
    assert SLEEVE_EXIT_PROFILES["asian_fade_widen"]["time_stop_bars"] == 48
