"""MAXIMUM-RIGOR parity test for the vp_euidx_pocgrav sleeve (REAL money, forward-only-flagged).

Proof strategy — drives the ACTUAL route oracle:
  The LOCKED route generator is KB5_fold_new_sleeves._vp_pocgrav_rows (lines 64-92). It returns only
  the SIMULATED R per firing bar (dict sleeve/sym/date/year/R) — it does NOT expose the entry
  (direction, stop_dist, target_dist). So we capture the SIGNAL directly: monkeypatch the route's
  `simulate` (the OUTCOME labeler, irrelevant to the entry geometry) with a RECORDER that records the
  exact (i, direction, stop_dist, target_dist) `_vp_pocgrav_rows` computes on every bar it fires, while
  the REAL route volume_profile.daily_profiles / prior_profile_at / nearest_node_state / cs.vol_ratio /
  atr14 / VP_confluence.BIN_FRAC do all the profile + gate math. w1.load (H4) and vp.load_m1 (M1) are
  monkeypatched to the synthetic fixture, exactly as the spec agent drove it.

  We then run the SRC generator on the SAME H4 bars (truncated to bars[:i+1] so it evaluates the same
  closed bar i) with the SAME M1 as aux_bars, and assert identical (direction, stop_dist, target_dist).

WARMUP NOTE: the route guard is `len(B) >= 200` on the WHOLE loaded backtest series, then it evaluates
any bar i>=101. The LIVE generator's warmup is the number of CLOSED bars UP TO the decision (len(bars)
>= 200, i.e. the decision bar at index >= 199) — the correct live semantics. So parity is asserted on
every route fire with i >= 199 (where the live warmup is satisfied); for those bars the match is exact.
The route's fires at i in 181..198 are the backtest-only warmup region and the live generator correctly
fails closed there (covered by the explicit warmup test).

FLOAT TOLERANCE: 1e-6 absolute. The SRC path recomputes atr14, vol_ratio and the entire vendored
volume-profile (daily_profiles/build_day_profile/_value_area/_find_nodes/nearest_node_state) with the
SAME byte-faithful float operations over the SAME inputs in the SAME order as the route, so the values
are bit-identical in practice; 1e-6 (~1e-7 of the ~20-1000-unit stop/target magnitudes here) is a
conservative guard against any platform float re-association, not a real disagreement budget.

If the route oracle cannot be imported, the oracle-driven tests fall back to documented anchors CAPTURED
FROM THE REAL ORACLE on this exact fixture (ORACLE_ANCHORS) and assert the SRC generator reproduces
them; the spec's own [RAN] reference (different fixture: i=206 dir=-1 stop=50.912 target=467.073) is
recorded in a comment. The oracle-free tests (fail-closed / leak-free / universe) always run.
"""
from __future__ import annotations
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
ROUTE_DIR = (REPO_ROOT / "research" / "operations"
             / "final_moonshot_v4_ultimate_mechanical_edge_2026_06_10")

# --- SRC port under test (stdlib + src only at module scope) ---
from src.components.ultimate_book.primitives import Bar
from src.components.ultimate_book.sleeves import vp_euidx as VPE
from src.components.ultimate_book.sleeves import volume_profile as VP
from src.components.ultimate_book import admission as ADM

# Anchors captured from the REAL route oracle on the fixture below (firing bar i -> (dir, stop, target)).
# Used only as the documented fallback when the route cannot be imported (it imports cleanly in
# .venv-gtos with PYTHONPATH=repo root). Spec [RAN] ref (different fixture): i=206 dir=-1 stop=50.912
# target=467.073 — same dir/shape, different magnitudes because the spec's synthetic series differs.
ORACLE_ANCHORS = {
    206: (-1, 22.648095, 484.878077),
    220: (-1, 36.905856, 741.038186),
    238: (-1, 41.439167, 1052.424037),
}

_ROUTE_CACHE: dict = {}


def _import_route():
    """Lazily import the ACTUAL route oracle (KB5 _vp_pocgrav_rows + its vp/w1 modules). Cached.
    Skips the calling test on failure (documents the exact import error)."""
    if "mods" in _ROUTE_CACHE:
        return _ROUTE_CACHE["mods"]
    for p in (str(ROUTE_DIR), str(REPO_ROOT)):
        if p not in sys.path:
            sys.path.insert(0, p)
    try:
        import KB5_fold_new_sleeves as kb5
        import volume_profile as route_vp
        import wave1_structure_setups_ict as route_w1
    except Exception as exc:  # pragma: no cover - env-dependent
        pytest.skip(f"route oracle not importable: {exc!r}")
    _ROUTE_CACHE["mods"] = (kb5, route_vp, route_w1)
    return _ROUTE_CACHE["mods"]


# --------------------------------------------------------------------------------------------- #
# Synthetic fixture — H4 ramps far above a tight prior-day M1 POC cluster -> POC-gravitation fires
# dir=-1 (price > POC). M1 carries tick volume in Bar.v. Naive datetimes (matches the route loaders).
# --------------------------------------------------------------------------------------------- #
def _h4_fixture(n: int = 240, seed: int = 11):
    rng = random.Random(seed)
    t0 = datetime(2024, 1, 2, 0, 0, 0)
    T = []; B = []
    prevc = 1000.0
    for k in range(n):
        drift = 18.0 if k > n - 60 else 0.0       # ramp price far above the ~1000 M1 cluster
        r = drift + rng.gauss(0, 2.0)
        o = prevc; c = o + r
        wide = 30.0 if k > n - 30 else 6.0        # ATR expansion near the end (vol_ratio >= 1.2)
        hi = max(o, c) + 0.4 * wide; lo = min(o, c) - 0.4 * wide
        B.append(Bar(o, hi, lo, c, 1000.0))
        T.append(t0 + timedelta(hours=4 * k))
        prevc = c
    return T, B


def _m1_fixture(T_h4, seed: int = 23):
    """One tight M1 cluster per UTC day near ~1000 (slow rise) with tick volume -> a stable prior-day
    POC well BELOW the ramped H4 end price (so |d_poc| >> 2 ATR, outside VA)."""
    rng = random.Random(seed)
    days = sorted({t.date() for t in T_h4})
    T = []; B = []
    for di, d in enumerate(days):
        center = 1000.0 + di * 1.0
        base = datetime(d.year, d.month, d.day, 0, 0, 0)
        for m in range(0, 600):
            tt = base + timedelta(minutes=m)
            px = center + rng.gauss(0, 1.2)
            o = px + rng.gauss(0, 0.2); c = px + rng.gauss(0, 0.2)
            hi = max(o, c) + abs(rng.gauss(0, 0.3)); lo = min(o, c) - abs(rng.gauss(0, 0.3))
            v = 50.0 + abs(rng.gauss(0, 20))      # tick volume
            T.append(tt); B.append(Bar(o, hi, lo, c, v))
    return T, B


def _drive_oracle(monkeypatch, T_h4, B_h4, T_m1, B_m1):
    """Drive the REAL route _vp_pocgrav_rows on the fixture; return [(i, dir, stop, target), ...] in
    firing order. `simulate` is replaced by a recorder (the entry geometry is the route's own
    stop_dist/target_dist args; the simulated R is irrelevant to the signal)."""
    kb5, route_vp, route_w1 = _import_route()
    calls: list[tuple] = []

    def rec_simulate(B, i, d, *, stop_dist, target_dist=None, maxbars=60, cost=0.0):
        calls.append((i, d, stop_dist, target_dist))
        return 0.0

    monkeypatch.setattr(route_w1, "load", lambda sym: (T_h4, B_h4))
    monkeypatch.setattr(route_vp, "load_m1", lambda sym: (T_m1, B_m1))
    monkeypatch.setattr(kb5, "simulate", rec_simulate)
    rows = kb5._vp_pocgrav_rows("GER40", far=2.0, vr_min=1.2)
    assert rows is not None
    return calls


# --------------------------------------------------------------------------------------------- #
# (1) PARITY vs the real route oracle
# --------------------------------------------------------------------------------------------- #
def test_vp_euidx_parity_vs_route_oracle(monkeypatch):
    T_h4, B_h4 = _h4_fixture()
    T_m1, B_m1 = _m1_fixture(T_h4)
    calls = _drive_oracle(monkeypatch, T_h4, B_h4, T_m1, B_m1)
    assert calls, "fixture produced no oracle fires — strengthen the fixture"

    fire_i = {i for (i, *_rest) in calls}
    compared = 0
    for (i, d, stop, target) in calls:
        if i < VPE.WARMUP_H4 - 1:        # live warmup: decision bar must be at index >= 199
            continue
        intent = VPE.generate("GER40", B_h4[: i + 1], "2024-01-01",
                              bar_times=T_h4[: i + 1], aux_bars=B_m1, aux_times=T_m1)
        assert intent is not None, f"src returned None on oracle fire i={i} (warmup satisfied)"
        assert intent.sleeve == "vp_euidx_pocgrav" and intent.symbol == "GER40"
        assert intent.direction == d, f"i={i} dir {intent.direction} != route {d}"
        assert abs(intent.stop_dist - stop) < 1e-6, f"i={i} stop {intent.stop_dist} != {stop}"
        assert abs(intent.target_dist - target) < 1e-6, f"i={i} target {intent.target_dist} != {target}"
        compared += 1
    assert compared >= 20, f"too few warmup-satisfied parity bars ({compared})"

    # No EXTRA / MISSED fires across the whole live-evaluable range (decision bar index >= 199).
    for i in range(VPE.WARMUP_H4 - 1, len(B_h4) - 1):
        intent = VPE.generate("GER40", B_h4[: i + 1], "2024-01-01",
                              bar_times=T_h4[: i + 1], aux_bars=B_m1, aux_times=T_m1)
        fired = intent is not None
        assert fired == (i in fire_i), f"fire disagreement at i={i}: src={fired} oracle={i in fire_i}"


def test_vp_euidx_matches_oracle_anchors(monkeypatch):
    """Cross-check: the SRC generator reproduces the captured real-oracle anchors on this fixture.
    Doubles as the [RAN] fallback shape when the oracle cannot be imported."""
    T_h4, B_h4 = _h4_fixture()
    T_m1, B_m1 = _m1_fixture(T_h4)
    for i, (d, stop, target) in ORACLE_ANCHORS.items():
        intent = VPE.generate("GER40", B_h4[: i + 1], "2024-01-01",
                              bar_times=T_h4[: i + 1], aux_bars=B_m1, aux_times=T_m1)
        assert intent is not None, f"src None at anchor i={i}"
        assert intent.direction == d
        assert abs(intent.stop_dist - stop) < 1e-6, (i, intent.stop_dist, stop)
        assert abs(intent.target_dist - target) < 1e-6, (i, intent.target_dist, target)


# --------------------------------------------------------------------------------------------- #
# (2) LEAK-FREE prior-day profile — same-day / future M1 mutation must NOT change the decision
# --------------------------------------------------------------------------------------------- #
def test_leak_free_same_day_and_future_m1_mutation():
    """The decision at H4 bar i uses ONLY the PRIOR completed UTC day's M1 profile. Corrupting EVERY
    M1 bar on the decision day OR any later day (price +5000, volume x999) must leave (direction,
    stop_dist, target_dist) bit-identical — proving prior_profile_at never peeks at day-D or the future."""
    T_h4, B_h4 = _h4_fixture()
    T_m1, B_m1 = _m1_fixture(T_h4)
    i = 238                                  # a known fire bar, warmup satisfied
    dec_day = T_h4[i].date()
    base = VPE.generate("GER40", B_h4[: i + 1], "2024-01-01",
                        bar_times=T_h4[: i + 1], aux_bars=B_m1, aux_times=T_m1)
    assert base is not None

    mutated = []
    n_mut = 0
    for tt, b in zip(T_m1, B_m1):
        if tt.date() >= dec_day:             # same-day OR future M1 -> corrupt hard
            mutated.append(Bar(b.o + 5000.0, b.h + 5000.0, b.l + 5000.0, b.c + 5000.0, b.v * 999.0))
            n_mut += 1
        else:
            mutated.append(b)
    assert n_mut > 0
    mut = VPE.generate("GER40", B_h4[: i + 1], "2024-01-01",
                       bar_times=T_h4[: i + 1], aux_bars=mutated, aux_times=T_m1)
    assert mut is not None
    assert mut.direction == base.direction
    assert abs(mut.stop_dist - base.stop_dist) < 1e-12
    assert abs(mut.target_dist - base.target_dist) < 1e-12


def test_leak_free_truncated_m1_matches_full_m1():
    """Dropping all M1 from the decision day and later (the live feed at decision time only holds M1
    up to ~now) yields the IDENTICAL decision as passing the full M1 — the prior-day profile is the
    same object either way (independent proof of leak-freedom from the other direction)."""
    T_h4, B_h4 = _h4_fixture()
    T_m1, B_m1 = _m1_fixture(T_h4)
    i = 238
    dec_day = T_h4[i].date()
    full = VPE.generate("GER40", B_h4[: i + 1], "2024-01-01",
                        bar_times=T_h4[: i + 1], aux_bars=B_m1, aux_times=T_m1)
    tb = [(tt, b) for tt, b in zip(T_m1, B_m1) if tt.date() < dec_day]
    Tt = [tt for tt, _ in tb]; Bt = [b for _, b in tb]
    trunc = VPE.generate("GER40", B_h4[: i + 1], "2024-01-01",
                         bar_times=T_h4[: i + 1], aux_bars=Bt, aux_times=Tt)
    assert full is not None and trunc is not None
    assert trunc.direction == full.direction
    assert abs(trunc.stop_dist - full.stop_dist) < 1e-12
    assert abs(trunc.target_dist - full.target_dist) < 1e-12


# --------------------------------------------------------------------------------------------- #
# (3) FAIL-CLOSED (always run)
# --------------------------------------------------------------------------------------------- #
def test_fail_closed_no_aux_m1():
    T_h4, B_h4 = _h4_fixture()
    assert VPE.generate("GER40", B_h4, "2024-01-01", bar_times=T_h4, aux_bars=None, aux_times=None) is None
    assert VPE.generate("GER40", B_h4, "2024-01-01", bar_times=T_h4, aux_bars=[], aux_times=[]) is None


def test_fail_closed_below_200_h4():
    T_h4, B_h4 = _h4_fixture()
    T_m1, B_m1 = _m1_fixture(T_h4)
    assert VPE.generate("GER40", B_h4[:199], "2024-01-01",
                        bar_times=T_h4[:199], aux_bars=B_m1, aux_times=T_m1) is None
    assert VPE.generate("GER40", [], "2024-01-01", aux_bars=B_m1, aux_times=T_m1) is None


def test_fail_closed_no_prior_day_profile():
    """When every M1 bar is on (or after) the decision day, there is NO prior completed day -> the
    `t.date() <= fday` / prior_profile_at None paths fail closed."""
    T_h4, B_h4 = _h4_fixture()
    i = 238
    dec_day = T_h4[i].date()
    # M1 only on the decision day (no strictly-prior day exists)
    base = datetime(dec_day.year, dec_day.month, dec_day.day, 0, 0, 0)
    T_m1 = [base + timedelta(minutes=m) for m in range(600)]
    B_m1 = [Bar(1000.0, 1001.0, 999.0, 1000.0, 50.0) for _ in range(600)]
    assert VPE.generate("GER40", B_h4[: i + 1], "2024-01-01",
                        bar_times=T_h4[: i + 1], aux_bars=B_m1, aux_times=T_m1) is None


def test_fail_closed_missing_bar_time():
    T_h4, B_h4 = _h4_fixture()
    T_m1, B_m1 = _m1_fixture(T_h4)
    # no bar_times AND no bar_time -> cannot establish the decision day -> None
    assert VPE.generate("GER40", B_h4, "2024-01-01", aux_bars=B_m1, aux_times=T_m1) is None


def test_off_surface_symbol_returns_none():
    T_h4, B_h4 = _h4_fixture()
    T_m1, B_m1 = _m1_fixture(T_h4)
    for sym in ("EURUSD", "XAUUSD", "BTCUSD"):
        assert VPE.generate(sym, B_h4, "2024-01-01",
                            bar_times=T_h4, aux_bars=B_m1, aux_times=T_m1) is None


def test_flat_series_returns_none():
    """No POC-gravitation when price sits on the prior-day POC (|d_poc| ~ 0): fail closed."""
    flat = [Bar(1000.0, 1000.5, 999.5, 1000.0, 1.0) for _ in range(240)]
    t0 = datetime(2024, 1, 2)
    T_h4 = [t0 + timedelta(hours=4 * k) for k in range(240)]
    days = sorted({t.date() for t in T_h4})
    T_m1 = []; B_m1 = []
    for d in days:
        base = datetime(d.year, d.month, d.day)
        for m in range(300):
            T_m1.append(base + timedelta(minutes=m))
            B_m1.append(Bar(1000.0, 1000.3, 999.7, 1000.0, 50.0))
    assert VPE.generate("GER40", flat, "2024-01-01",
                        bar_times=T_h4, aux_bars=B_m1, aux_times=T_m1) is None


# --------------------------------------------------------------------------------------------- #
# (4) Registration surface / universe
# --------------------------------------------------------------------------------------------- #
def test_on_surface_matches_admission_registry_and_universe():
    assert VPE.ON_SURFACE == ADM.CLEAN3_REGISTRY["vp_euidx_pocgrav"].symbols
    assert VPE.ON_SURFACE == ("GER40", "UK100")
    profile = REPO_ROOT / "config/profiles/operator_profile.yaml"
    text = profile.read_text(encoding="utf-8")
    for sym in VPE.ON_SURFACE:
        assert f"\n  {sym}:" in text, f"{sym} not a profile instrument key (27-universe)"


def test_vendored_bin_frac_matches_route():
    """The vendored BIN_FRAC must equal the route VP_confluence.BIN_FRAC the VP sleeve passes (0.03)."""
    assert VP.BIN_FRAC == 0.03
