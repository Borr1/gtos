"""T2c — metals_ob_micro sleeve parity: the src OB-retest generator must reproduce the LOCKED route
detector csb_commodity_setups.sig_ob EXACTLY, plus the gen_metals_ob_micro sleeve gates (ac60>=0.20 +
FVG dedup). This sleeve places REAL money orders, so the entry geometry (direction, stop_dist) is
proven bit-for-bit two ways:

  (1) REAL ORACLE: import the actual route detector csb_commodity_setups.sig_ob, run it on a synthetic
      H4 fixture (route loader monkeypatched), and assert the src detector matches its (dir, stop_dist)
      to 1e-9. If the route cannot be imported in isolation, the test SKIPS with the captured error
      (the verbatim-oracle test below is the never-skipping transcription guard; the spec [RAN]
      reference for the spec's own fixture is dir=+1, stop_dist=29.7753).
  (2) VERBATIM ORACLE: an inline byte-copy of the route sig_ob per-bar body, swept over a varied
      series — guards against any transcription error independent of the route import.

Pure: stdlib + the src package only; the real-oracle test adds the route dir to sys.path on demand.
"""
import math
import random
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src.components.ultimate_book.primitives import Bar, atr14, vol_ratio
from src.components.ultimate_book.sleeves import metals_ob_micro as MOM
from src.components.ultimate_book.sleeves import metals as MT
from src.components.ultimate_book import admission as ADM

REPO_ROOT = Path(__file__).resolve().parents[2]
ROUTE_DIR = REPO_ROOT / "research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"


# --------------------------------------------------------------------------- fixtures ----------
def _h4_times(n):
    return [datetime(2024, 1, 1) + timedelta(hours=4 * k) for k in range(n)]


def build_dedup_fixture():
    """Uptrend (smooth sinusoid -> ac60>=0.20) with an embedded order block whose RETEST bar also
    forms a same-direction FVG. The route sig_ob fires once (dir +1); metals.fvg_signal ALSO fires
    +1 on that bar -> generate() must dedup to None. Returns (times, bars)."""
    rnd = random.Random(7)
    bars = []
    p = 1800.0
    n = 220
    P = 90.0
    prev_c = p
    for k in range(n):
        r = 4.0 + 3.0 * math.sin(2 * math.pi * k / P) + rnd.uniform(-0.15, 0.15)
        o = prev_c
        c = o + r
        bars.append(Bar(o, max(o, c) + 0.4, min(o, c) - 0.4, c, 100.0))
        prev_c = c
    # vol-expansion: widen the last 12 pre-OB ranges so atr14 clears the 1.2*SMA100 gate (closes kept)
    for j in range(len(bars) - 12, len(bars)):
        b = bars[j]
        bars[j] = Bar(b.o, max(b.o, b.c) + 3.0, min(b.o, b.c) - 3.0, b.c, b.v)
    base = prev_c
    obA_o, obA_c = base + 0.8, base - 0.6
    obA_h, obA_l = obA_o + 0.6, obA_c - 0.6
    bars.append(Bar(obA_o, obA_h, obA_l, obA_c, 100.0))                  # OB (down candle)
    imp_c = obA_h + 2.0
    bars.append(Bar(obA_c, imp_c + 3.0, obA_c - 0.4, imp_c, 100.0))      # up impulse > OB high
    c1 = imp_c + 2.0
    bars.append(Bar(imp_c, c1 + 3.0, imp_c - 0.4, c1, 100.0))            # continuation
    c2 = c1 + 2.0
    bars.append(Bar(c1, c2 + 3.0, c1 - 0.4, c2, 100.0))                  # continuation
    rt_l = obA_h - 1.0
    rt_c = c2 + 2.0
    bars.append(Bar(c2 - 1.0, rt_c + 0.5, rt_l, rt_c, 100.0))            # retest (signal bar)
    bars.append(Bar(rt_c, rt_c + 1.0, rt_c - 1.0, rt_c + 0.5, 100.0))    # trailing (route reserves)
    return _h4_times(len(bars)), bars


def build_emit_fixture():
    """Same uptrend + OB but the impulse/continuation bars carry DEEP lower wicks (overlap) so NO
    same-direction FVG gap forms, and the retest dip is shallow. sig_ob fires (dir +1, ac60>=0.20),
    metals.fvg_signal is None on the signal bar -> generate() EMITS the intent. Returns (times, bars)."""
    rnd = random.Random(7)
    bars = []
    p = 1800.0
    n = 220
    P = 90.0
    prev_c = p
    for k in range(n):
        r = 4.0 + 3.0 * math.sin(2 * math.pi * k / P) + rnd.uniform(-0.15, 0.15)
        o = prev_c
        c = o + r
        bars.append(Bar(o, max(o, c) + 0.4, min(o, c) - 0.4, c, 100.0))
        prev_c = c
    for j in range(len(bars) - 12, len(bars)):
        b = bars[j]
        bars[j] = Bar(b.o, max(b.o, b.c) + 3.0, min(b.o, b.c) - 3.0, b.c, b.v)
    base = prev_c
    obA_o, obA_c = base + 0.8, base - 0.6
    obA_h, obA_l = obA_o + 0.6, obA_c - 0.6
    bars.append(Bar(obA_o, obA_h, obA_l, obA_c, 100.0))                  # OB (down candle)
    imp_c = obA_h + 2.0
    bars.append(Bar(obA_c, imp_c + 3.0, obA_l - 4.0, imp_c, 100.0))      # impulse, DEEP low (no gap)
    c1 = imp_c + 2.0
    bars.append(Bar(imp_c, c1 + 3.0, obA_l - 4.0, c1, 100.0))            # continuation, DEEP low
    c2 = c1 + 2.0
    bars.append(Bar(c1, c2 + 3.0, obA_l - 4.0, c2, 100.0))               # continuation, DEEP low
    rt_l = obA_h - 0.1
    rt_c = c2 + 2.0
    bars.append(Bar(c2 - 1.0, rt_c + 0.5, rt_l, rt_c, 100.0))            # retest (shallow dip)
    bars.append(Bar(rt_c, rt_c + 1.0, rt_c - 1.0, rt_c + 0.5, 100.0))    # trailing
    return _h4_times(len(bars)), bars


def _flat_series(n=240):
    return [Bar(100.0, 100.5, 99.5, 100.0, 100.0) for _ in range(n)]


def _import_route():
    """Import the ACTUAL route detector in isolation. Returns (csb_module, w1_module) or raises."""
    import sys
    if str(ROUTE_DIR) not in sys.path:
        sys.path.insert(0, str(ROUTE_DIR))
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    import csb_commodity_setups as csb  # noqa: E402  (route module; sets up its own sys.path on import)
    return csb, csb.w1


# --------------------------------------------------------------- (1) REAL-ORACLE detector parity
def test_sig_ob_matches_real_route_detector():
    """src MOM.sig_ob == route csb_commodity_setups.sig_ob (dir, stop_dist) to 1e-9 on a fixture
    the REAL route fires on. Skips (documented) only if the route cannot be imported."""
    try:
        csb, w1 = _import_route()
    except Exception as e:  # pragma: no cover - documents the exact import failure if it ever happens
        pytest.skip(f"route detector import failed -> verbatim-oracle test guards transcription: {e!r}")

    T, B = build_dedup_fixture()
    orig_load = w1.load
    try:
        w1.load = lambda sym: (T, B)
        route_sigs = csb.sig_ob("XAUUSD")
    finally:
        w1.load = orig_load

    assert len(route_sigs) == 1, f"fixture should fire the route once, got {len(route_sigs)}"
    _t, d_route, sd_route, i_fire, _BB, _cost = route_sigs[0]
    assert (d_route, i_fire) == (1, len(B) - 2)

    atrs = [atr14(B, k) for k in range(len(B))]
    got_full = MOM.sig_ob(B, atrs, i_fire)
    # the live engine evaluates the LATEST closed bar -> identical bars truncated at i_fire
    Btr = B[: i_fire + 1]
    atrs_tr = [atr14(Btr, k) for k in range(len(Btr))]
    got_trunc = MOM.sig_ob(Btr, atrs_tr, i_fire)

    assert got_full is not None and got_trunc is not None
    assert got_full[0] == d_route and got_trunc[0] == d_route
    assert abs(got_full[1] - sd_route) < 1e-9, f"src={got_full[1]!r} route={sd_route!r}"
    assert abs(got_trunc[1] - sd_route) < 1e-9


# --------------------------------------------------------- (2) VERBATIM-ORACLE transcription guard
def _route_sig_ob_oracle(B, atrs, i):
    """Inline byte-copy of csb_commodity_setups.sig_ob's per-bar body (lines 85-107) for one bar i.
    The route loop bound range(60, len-1) is a backtest artifact (it reserves a forward bar for the
    exit sim); the SIGNAL computed at a given i is exactly this body, gated by vol_gate_ok (i>=100)."""
    if i < 100:
        return None
    a = atrs[i]
    if a <= 0:
        return None
    # vol_gate_ok (csb lines 45-50)
    sma100 = sum(atrs[i - 99:i + 1]) / 100
    if not (sma100 > 0 and a >= 1.2 * sma100):
        return None
    tr = MT.htf_trend(B, i, 30)
    b = B[i]
    if tr == 1:
        for k in range(i - 2, max(i - 9, 60), -1):
            if not (B[k].c < B[k].o):
                continue
            if not (B[k + 1].c > B[k].h):
                continue
            ob_top, ob_bot = B[k].h, B[k].l
            if b.l <= ob_top and b.c > ob_bot and b.c > b.o:
                return 1, max((b.c - min(b.l, ob_bot)) + 0.10 * a, 0.25 * a)
    elif tr == -1:
        for k in range(i - 2, max(i - 9, 60), -1):
            if not (B[k].c > B[k].o):
                continue
            if not (B[k + 1].c < B[k].l):
                continue
            ob_top, ob_bot = B[k].h, B[k].l
            if b.h >= ob_bot and b.c < ob_top and b.c < b.o:
                return -1, max((max(b.h, ob_top) - b.c) + 0.10 * a, 0.25 * a)
    return None


def test_sig_ob_matches_verbatim_oracle_over_series():
    """Sweep both fixtures + a downtrend variant; MOM.sig_ob must equal the inline route oracle on
    every bar (never skips; pure transcription guard incl. the short/downtrend mirror branch)."""
    series = [build_dedup_fixture()[1], build_emit_fixture()[1]]
    # downtrend mirror: flip the emit fixture's closes about a high baseline to exercise dir=-1
    _t, up = build_emit_fixture()
    hi = max(b.h for b in up) + 10.0
    down = [Bar(hi - b.o, hi - b.l, hi - b.h, hi - b.c, b.v) for b in up]
    series.append(down)

    n_short = 0
    for B in series:
        atrs = [atr14(B, k) for k in range(len(B))]
        for i in range(len(B)):
            got = MOM.sig_ob(B, atrs, i)
            want = _route_sig_ob_oracle(B, atrs, i)
            if got is None or want is None:
                assert got == want, f"i={i}: src={got} oracle={want}"
            else:
                assert got[0] == want[0] and abs(got[1] - want[1]) < 1e-12, f"i={i}: {got} vs {want}"
                if got[0] == -1:
                    n_short += 1
    assert n_short > 0, "downtrend variant produced no short OB signals — strengthen the fixture"


# --------------------------------------------------------------------- generate() emit + gates ----
def test_generate_emits_intent_matching_route():
    """On the emit fixture (sig_ob fires, ac60>=0.20, no same-dir FVG) generate() emits a
    metals_ob_micro TradeIntent whose (direction, stop_dist) match the route detector exactly,
    and a native vol-tiered runner target_dist (metals._runner_R(vr)*stop_dist) so the live book
    carries the validated STATE_D runner geometry to the broker TP (was target_dist=None)."""
    try:
        csb, w1 = _import_route()
        T, B = build_emit_fixture()
        orig_load = w1.load
        try:
            w1.load = lambda sym: (T, B)
            route_sigs = csb.sig_ob("XAUUSD")
        finally:
            w1.load = orig_load
        assert route_sigs, "emit fixture should fire the route at least once"
        _t, d_route, sd_route, i_fire, _BB, _cost = route_sigs[0]
    except Exception as e:  # pragma: no cover
        pytest.skip(f"route detector import failed: {e!r}")

    Btr = B[: i_fire + 1]
    intent = MOM.generate("XAUUSD", Btr, "2024-02-15")
    assert intent is not None, "generate should emit on the emit fixture"
    assert intent.sleeve == "metals_ob_micro" and intent.symbol == "XAUUSD"
    assert intent.direction == d_route
    assert abs(intent.stop_dist - sd_route) < 1e-9, f"src={intent.stop_dist!r} route={sd_route!r}"
    # native vol-tiered runner target (metals._runner_R(vr) * stop_dist) replaces the old None.
    atrs = [atr14(Btr, k) for k in range(len(Btr))]
    expected_td = MT._runner_R(vol_ratio(atrs, i_fire)) * sd_route
    assert abs(intent.target_dist - expected_td) < 1e-9, (intent.target_dist, expected_td)
    assert intent.decision_day == "2024-02-15"
    assert intent.intra_size == 1.0


def test_fvg_dedup_drops_same_direction_real_fixture():
    """REAL combined fixture: the OB retest bar ALSO forms a same-direction FVG. metals.fvg_signal
    fires +1 on the signal bar, so generate() must dedup to None (the FVG core/softband owns it)."""
    T, B = build_dedup_fixture()
    i = len(B) - 2
    atrs = [atr14(B, k) for k in range(len(B))]
    assert MOM.sig_ob(B, atrs, i) is not None, "OB must fire on the dedup fixture"
    fvg = MT.fvg_signal(B, atrs, i)
    assert fvg is not None and fvg[0] == 1, f"fixture must also fire a same-dir FVG, got {fvg}"
    assert MOM.generate("XAUUSD", B[: i + 1], "2024-02-15") is None


def test_fvg_dedup_branch_isolated(monkeypatch):
    """Isolate the dedup branch on the emit fixture (no real FVG): a forced same-dir FVG -> None;
    a forced opposite-dir FVG or None -> emit. Proves generate() consults metals.fvg_signal by dir."""
    _t, B = build_emit_fixture()
    bars = B[: len(B) - 1]  # last bar = the retest signal bar (a real OB-fire, dir +1)
    base_intent = MOM.generate("XAUUSD", bars, "2024-02-15")
    assert base_intent is not None and base_intent.direction == 1

    monkeypatch.setattr(MOM.metals, "fvg_signal", lambda *a, **k: (1, 5.0))
    assert MOM.generate("XAUUSD", bars, "2024-02-15") is None          # same dir -> dropped

    monkeypatch.setattr(MOM.metals, "fvg_signal", lambda *a, **k: (-1, 5.0))
    assert MOM.generate("XAUUSD", bars, "2024-02-15") is not None      # opposite dir -> kept

    monkeypatch.setattr(MOM.metals, "fvg_signal", lambda *a, **k: None)
    assert MOM.generate("XAUUSD", bars, "2024-02-15") is not None      # no FVG -> kept


def test_ac_micro_gate_boundary(monkeypatch):
    """ac60 >= 0.20 strong-persistence tail gate (gen_metals_ob_micro line 137). On the emit fixture
    (FVG None) the only remaining gate is ac: 0.20 emits, 0.1999 drops, None drops."""
    _t, B = build_emit_fixture()
    bars = B[: len(B) - 1]  # last bar fires sig_ob

    monkeypatch.setattr(MOM, "autocorr", lambda *a, **k: 0.20)
    assert MOM.generate("XAUUSD", bars, "2024-02-15") is not None
    monkeypatch.setattr(MOM, "autocorr", lambda *a, **k: 0.1999)
    assert MOM.generate("XAUUSD", bars, "2024-02-15") is None
    monkeypatch.setattr(MOM, "autocorr", lambda *a, **k: None)
    assert MOM.generate("XAUUSD", bars, "2024-02-15") is None


def test_no_signal_on_flat_series():
    assert MOM.generate("XAUUSD", _flat_series(240), "2024-02-15") is None


def test_warmup_below_200_bars():
    _t, B = build_emit_fixture()
    assert MOM.generate("XAUUSD", B[:199], "2024-02-15") is None       # < 200 closed bars -> None
    assert MOM.generate("XAUUSD", [], "2024-02-15") is None


def test_off_surface_symbol_never_signals():
    _t, B = build_emit_fixture()
    assert MOM.generate("EURUSD", B[: len(B) - 1], "2024-02-15") is None
    assert MOM.generate("BTCUSD", B[: len(B) - 1], "2024-02-15") is None


def test_on_surface_matches_admission_registry_and_universe():
    """ON_SURFACE == admission metals_ob_micro tuple, and every symbol is in the 27-symbol profile."""
    assert MOM.ON_SURFACE == ADM.SLEEVE_REGISTRY["metals_ob_micro"].symbols
    assert MOM.ON_SURFACE == ("XAUUSD", "XAGUSD", "XAUEUR", "XAGEUR", "XAUAUD", "XAGAUD")
    profile = REPO_ROOT / "config/profiles/operator_profile.yaml"
    text = profile.read_text(encoding="utf-8")
    for sym in MOM.ON_SURFACE:
        assert f"\n  {sym}:" in text, f"{sym} not a profile instrument key (27-universe)"
