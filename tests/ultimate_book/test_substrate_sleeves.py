"""MAXIMUM-RIGOR parity test for the two substrate sleeve generators.

Proof strategy (imports the ACTUAL route oracle):
  - synthetic H4 Bar series + aligned UTC timestamps are crafted (seeded, deterministic) to land in
    each locked cell;
  - the REAL route oracle is driven (substrate.build_states + substrate.cell_coords, with w1.load
    monkeypatched to return the synthetic series — the same call path SUBSTRATE_corrcheck.materialize_cell
    uses) to get, PER BAR, the reference confluence coordinates, the fire/no-fire decision, and the
    reference geometry (direction = dmode from SUBSTRATE_corrcheck.parse_cell; stop_dist = stop_atr*ATR;
    target_dist = target_R*stop_dist);
  - the SRC generator is run on the IDENTICAL bars (truncated to bars[:i+1] so it evaluates the same
    closed bar i, with bar_time = times[i]);
  - we assert: (a) the src vendored state machine's coordinates EQUAL the route's on EVERY bar that
    carries a state; (b) the src generator fires on EXACTLY the bars the oracle's cell matches;
    (c) on each firing bar the emitted (direction, stop_dist, target_dist) equal the oracle reference
    within 1e-9. Plus no-signal (flat -> None), warmup (len<210 -> None), and the sub_mid_dn_revert
    session fail-closed (bar_time=None -> None).

The route oracle is imported LAZILY inside the tests (never at collection) and w1.load is patched via
the auto-restoring `monkeypatch` fixture, so this module has NO global side effects on sibling tests.
If the route oracle cannot be imported the oracle-dependent tests SKIP with the exact import error (it
imports cleanly in .venv-gtos with PYTHONPATH=repo root, which is how this suite runs); the
oracle-free tests (warmup / flat / fail-closed / universe) always run.
"""
from __future__ import annotations
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
ROUTE_DIR = (REPO_ROOT / "research" / "operations"
             / "final_moonshot_v4_ultimate_mechanical_edge_2026_06_10")

# --- import the SRC port (the thing under test); stdlib + src only at module scope ---
from src.components.ultimate_book.primitives import Bar
from src.components.ultimate_book.sleeves import substrate as sl
from src.components.ultimate_book.sleeves import substrate_engine as se

CELL_DIMS = ("vol", "trend", "mtf", "rngpos", "comp", "persist", "session")
_ROUTE_CACHE: dict = {}


def _import_route():
    """Lazily import the ACTUAL route oracle (route dir on sys.path on demand). Cached. The route
    `substrate.py` sets up its own sys.path on import. Skips the calling test on failure."""
    if "mods" in _ROUTE_CACHE:
        return _ROUTE_CACHE["mods"]
    for p in (str(ROUTE_DIR), str(REPO_ROOT)):
        if p not in sys.path:
            sys.path.insert(0, p)
    try:
        import substrate as route_sub
        import SUBSTRATE_corrcheck as route_sc
        import wave1_structure_setups_ict as route_w1
    except Exception as exc:  # pragma: no cover - env-dependent
        pytest.skip(f"route oracle not importable: {exc!r}")
    _ROUTE_CACHE["mods"] = (route_sub, route_sc, route_w1)
    return _ROUTE_CACHE["mods"]


# --------------------------------------------------------------------------------------------- #
# synthetic-series helpers
# --------------------------------------------------------------------------------------------- #
def _times(n: int, start_hour: int = 0) -> list[datetime]:
    """Aligned UTC H4 timestamps (4h step). The session bucket reads the bar's UTC hour."""
    t0 = datetime(2020, 1, 6, start_hour, tzinfo=timezone.utc)
    return [t0 + timedelta(hours=4 * k) for k in range(n)]


def _bars(prices: list[float], vols: list[float]) -> list[Bar]:
    """Build OHLC bars: open=prev close, high/low straddle by ~0.4*vol. Same objects feed BOTH the
    route oracle (duck-typed: geometry_lib.atr14 reads only o/h/l/c) and the src generator."""
    bars: list[Bar] = []
    prev = prices[0]
    for k, p in enumerate(prices):
        rng = vols[k]
        o, c = prev, p
        hi = max(o, c) + 0.4 * rng
        lo = min(o, c) - 0.4 * rng
        bars.append(Bar(o, hi, lo, c, 1000.0))
        prev = c
    return bars


def _series_mid_dn(seed: int, n: int = 340) -> tuple[list[Bar], list[datetime]]:
    """Down-recent / up-prior path with mean-reverting (neg-autocorr) noise + mid vol -> lands in the
    sub_mid_dn_revert depth-7 cell. start_hour=0 makes i=232 fall on UTC hour 16 (ny)."""
    rng = random.Random(seed)
    prices: list[float] = []
    rets: list[float] = []
    p = 1000.0
    for k in range(n):
        prices.append(p)
        base = -1.2 if k > n - 55 else (1.2 if k > n - 110 else 0.0)
        alt = -0.9 * (rets[-1] if rets else 0.0)        # alternation -> negative autocorr (revert)
        r = base + rng.gauss(0, 1.0) + alt
        rets.append(r)
        p += r
    vols = [abs(rng.gauss(0, 1)) * 1.0 + (3.0 if k > n - 55 else 1.0) for k in range(n)]
    return _bars(prices, vols), _times(n, 0)


def _series_xvol(seed: int, n: int = 340) -> tuple[list[Bar], list[datetime]]:
    """V-shape (down [n-100..n-50], up [n-50..n]) + end vol spike -> sub_xvol_pullback cell:
    trend=up (slope50), mtf=conflict (slope20 up vs slope100 down), vol=xhi, persist=rand."""
    rng = random.Random(seed)
    prices: list[float] = []
    p = 1000.0
    for k in range(n):
        prices.append(p)
        base = 1.4 if k > n - 50 else (-1.6 if k > n - 100 else 0.0)
        p += base + rng.gauss(0, 1.2)
    vols = [abs(rng.gauss(0, 1)) * 1.0 + (5.0 if k > n - 12 else 1.0) for k in range(n)]
    return _bars(prices, vols), _times(n, 0)


def _oracle_states(monkeypatch, bars: list[Bar], times: list[datetime]):
    """Drive the REAL route oracle on the synthetic series. w1.load is patched via monkeypatch
    (auto-restored), so no global side effect leaks to sibling tests. Returns (route, A, states)."""
    route_sub, route_sc, route_w1 = _import_route()
    monkeypatch.setattr(route_w1, "load", lambda sym: (times, bars))
    built = route_sub.build_states("SYN")
    assert built is not None, "route build_states returned None (series too short)"
    _T, _B, A, states = built
    return (route_sub, route_sc), A, states


def _times_on_the_broker_grid(n: int, server_start_hour: int = 0) -> list[datetime]:
    """True-UTC H4 stamps whose **server-local** hours are the archive's 00/04/08/12/16/20 grid.

    `_times` puts the bars on a UTC-aligned grid, where a +2/+3 shift never crosses the 8 or 16
    session boundary — which is exactly the grid Session AK reasoned about and why the clock defect
    B971 found survived every existing parity test (`SESSION_AK_...RESULT.md` §7.1). The archive is
    on this grid instead, and here three of the six opens change bucket.
    """
    from src.components.ultimate_book.sleeves import _server_clock as sc

    t0 = datetime(2020, 1, 6, 0, tzinfo=timezone.utc)
    probe = sc.server_hour(t0)
    assert probe is not None
    # Shift by whole hours so bar 0 lands EXACTLY on `server_start_hour`. Shifting only within the
    # 4 h block would leave every bar index on the same server hour, which is what the first
    # version of this helper did and it silently removed the test's power (B1200).
    t0 = t0 + timedelta(hours=(server_start_hour - probe) % 24)
    out = [t0 + timedelta(hours=4 * k) for k in range(n)]
    assert sc.server_hour(out[0]) == server_start_hour, (sc.server_hour(out[0]), server_start_hour)
    return out


def _parity_sweep(monkeypatch, cell_string: str, conds: dict, gen, *,
                  bars: list[Bar], times: list[datetime],
                  oracle_times: list[datetime] | None = None,
                  src_hour=None):
    """Per-bar parity vs the real oracle. Returns (checked, oracle_fires, mine_fires).

    `oracle_times` is what the ROUTE is driven with and defaults to `times`. The route parses naive
    MT5 CSV stamps, so its `T[i].hour` is a **broker wall-clock** hour; passing the broker-local
    projection of `times` while the src generator gets the true-UTC `times` is the exact claim
    `substrate._session_hour` makes, and it is the only configuration in which a wrong clock fails.
    `src_hour(i)` supplies the hour the vendored engine is asked for on the src side.
    """
    (route_sub, route_sc), A, states = _oracle_states(monkeypatch, bars,
                                                      oracle_times if oracle_times else times)
    if src_hour is None:
        def src_hour(i):
            return times[i].hour
    # parse the LOCKED cell string with the ACTUAL route parser -> reference geom/dir/conds
    geom, dmode, parsed_conds = route_sc.parse_cell(cell_string)
    assert parsed_conds == conds, f"route parse {parsed_conds} != module conds {conds}"
    stop_atr, target_R = geom
    n = len(bars)
    checked = oracle_fires = mine_fires = 0
    for i in range(route_sub.WARMUP, n):
        so = states[i]
        if so is None:
            continue
        checked += 1
        co_oracle = route_sub.cell_coords(so)
        st_mine = se.compute_state(bars, i, src_hour(i))
        co_mine = se.cell_coords(st_mine)
        # (a) vendored coordinates match the route on every dim the route produces
        for d in CELL_DIMS:
            assert co_oracle.get(d) == co_mine.get(d), (
                f"coord '{d}' mismatch at bar {i}: oracle={co_oracle.get(d)} mine={co_mine.get(d)}")
        match_oracle = all(co_oracle.get(d) == b for d, b in conds.items())
        match_mine = se.cell_matches(co_mine, conds)
        assert match_oracle == match_mine, f"fire decision disagree at bar {i}"
        oracle_fires += int(match_oracle)
        mine_fires += int(match_mine)
        # (c) THE GENERATOR ITSELF, on every bar and not only the firing ones. Calling it only
        # where the oracle fires checks half the claim: it cannot see a generator that fires where
        # the oracle does not, which is exactly the shape of a wrong session clock (B1200 — the
        # first version of the broker-grid test below passed against the reverted clock for this
        # reason). `bar_time=times[i]` goes through the generator's own hour resolution, so this
        # assertion is where `substrate._session_hour` is under test.
        intent = gen("XAUUSD", bars[: i + 1], "2020-01-01", bar_time=times[i])
        assert (intent is not None) == match_oracle, (
            f"src generator {'fired' if intent else 'did not fire'} at bar {i} "
            f"({times[i].isoformat()}) but the oracle says "
            f"{'fire' if match_oracle else 'no fire'}")
        if match_oracle:
            sd_ref = stop_atr * A[i]
            td_ref = target_R * sd_ref
            assert intent.direction == dmode
            assert abs(intent.stop_dist - sd_ref) < 1e-9, (intent.stop_dist, sd_ref)
            assert abs(intent.target_dist - td_ref) < 1e-9, (intent.target_dist, td_ref)
    return checked, oracle_fires, mine_fires


# --------------------------------------------------------------------------------------------- #
# parity tests (real route oracle)
# --------------------------------------------------------------------------------------------- #
def test_sub_xvol_pullback_parity_vs_route_oracle(monkeypatch):
    bars, times = _series_xvol(635)
    checked, of, mf = _parity_sweep(
        monkeypatch, sl.XVOL_CELL, sl.XVOL_CONDS, sl.generate_sub_xvol_pullback,
        bars=bars, times=times)
    assert checked > 100, f"too few bars compared ({checked})"
    assert of == mf, f"oracle fires {of} != src fires {mf}"
    assert of >= 1, "crafted xvol series produced no oracle cell match"


def test_sub_mid_dn_revert_parity_vs_route_oracle(monkeypatch):
    bars, times = _series_mid_dn(75)
    checked, of, mf = _parity_sweep(
        monkeypatch, sl.MIDDN_CELL, sl.MIDDN_CONDS, sl.generate_sub_mid_dn_revert,
        bars=bars, times=times)
    assert checked > 100, f"too few bars compared ({checked})"
    assert of == mf, f"oracle fires {of} != src fires {mf}"
    assert of >= 1, "crafted mid_dn series produced no oracle cell match"


def test_substrate_engine_is_byte_identical_to_the_deployed_lineage():
    """The vendored oracle must not diverge from `redacted_host` — not even in a docstring.

    `substrate_engine._bucket_session`'s own docstring still says *"h is the bar's UTC hour"*, which
    B1200 made wrong on mainline: the caller (`substrate._session_hour`) now passes a SERVER hour.
    Correcting it there was the obvious move and it is the wrong one, twice over:

      * `substrate_engine`'s own contract is *"READ-ONLY oracle, do NOT diverge ... Do NOT 'improve'
        anything in this module"*, because it is a byte-faithful copy of the locked route file; and
      * `replay_policy.generation_lineage`'s live-lineage register derives "which sleeve modules
        diverged from the deployed tree" from `git diff --name-only`, which cannot tell a docstring
        from behaviour. A cosmetic edit here puts `substrate_engine` in that set and forces a
        register entry for a module that owns no clock.

    So the statement lives in `substrate._session_hour`, which is the function that owns the clock
    and is registered, and this test pins the file instead. If the vendored copy ever needs a real
    change, the register entry has to be argued at the same time.
    """
    import hashlib
    import subprocess

    path = "src/components/ultimate_book/sleeves/substrate_engine.py"
    probe = subprocess.run(["git", "cat-file", "-e", f"redacted_host:{path}"], capture_output=True)
    if probe.returncode != 0:
        pytest.skip("live-lineage commit redacted_host not present in this clone")
    live = subprocess.run(["git", "show", f"redacted_host:{path}"],
                          check=True, capture_output=True).stdout
    here = (REPO_ROOT / path).read_bytes()
    assert hashlib.sha256(here).hexdigest() == hashlib.sha256(live).hexdigest(), (
        "substrate_engine.py has diverged from the deployed lineage; if that is deliberate, add "
        "the generation_lineage classification in the same change")
    # And the docstring the repair could not fix is still the one to read with care.
    assert "h is the bar's UTC hour" in here.decode()


@pytest.mark.parametrize("server_start_hour", [0, 4, 8, 12, 16, 20])
def test_sub_mid_dn_revert_parity_on_the_broker_grid(monkeypatch, server_start_hour):
    """The parity that actually covers the clock repair (B1200), and the one AK's grid could not.

    The route is driven with the BROKER-LOCAL stamps it would have parsed out of an MT5 CSV; the src
    generator is driven with the TRUE-UTC stamps the live `bar_provider` delivers for the same
    instants. Parity holds only if `substrate._session_hour` converts.

    Rotated through all six server start hours because the seeded series carries exactly ONE
    six-condition match: the rotation walks that bar through every session bucket, so the sweep sees
    both failure directions of a wrong clock — a MISSED fire where the server hour is NY but raw UTC
    reads `london`, and a SPURIOUS fire where raw UTC reads `ny` and the server hour is not.
    **Verified against the defect**: with `_session_hour` monkeypatched back to the pre-B1200
    raw-UTC read, 2 of these 6 rotations fail (start 0 and start 8) and the rest are hours on which
    the two clocks agree for this bar. Without the rotation, and without asserting the generator on
    NON-firing bars too, this test passed against the defect — both were added because it did.
    """
    from src.components.ultimate_book.sleeves import _server_clock as sc

    bars, _ = _series_mid_dn(75)
    times_utc = _times_on_the_broker_grid(len(bars), server_start_hour=server_start_hour)
    oracle_times = [sc.to_server_local(t) for t in times_utc]
    # The grid must actually contain bars whose two clocks disagree, or this proves nothing.
    disagree = sum(1 for t, o in zip(times_utc, oracle_times)
                   if se._bucket_session(t.hour) != se._bucket_session(o.hour))
    assert disagree >= len(bars) // 3

    checked, of, mf = _parity_sweep(
        monkeypatch, sl.MIDDN_CELL, sl.MIDDN_CONDS, sl.generate_sub_mid_dn_revert,
        bars=bars, times=times_utc, oracle_times=oracle_times,
        src_hour=lambda i: sc.server_hour(times_utc[i]))
    assert checked > 100, f"too few bars compared ({checked})"
    assert of == mf, f"oracle fires {of} != src fires {mf}"

    # And the rotation must fire exactly when the six non-session conditions land on an NY bar —
    # computed here rather than assumed, because which rotation that is depends on the matching
    # bar's index mod 6 and the first version of this test guessed it wrong.
    non_session = {k: v for k, v in sl.MIDDN_CONDS.items() if k != "session"}
    six = [i for i in range(se.WARMUP, len(bars))
           if (st := se.compute_state(bars, i, None)) is not None
           and all(se.cell_coords(st).get(d) == b for d, b in non_session.items())]
    assert six, "the seeded mid_dn series no longer matches the six non-session conditions"
    ny = [i for i in six if se._bucket_session(sc.server_hour(times_utc[i])) == "ny"]
    assert of == len(ny), (of, len(ny), [sc.server_hour(times_utc[i]) for i in six])


def test_sub_mid_dn_revert_session_is_ny_on_firing_bar(monkeypatch):
    """The matched mid_dn bar must be in the NY session — the cell's session=ny gate.

    NY is `server` hour >= 16 after B1200. The oracle is driven with UTC-aligned stamps here (the
    original fixture), so on the oracle's own clock the assertion is `hour >= 16`; the second
    assertion is the one that carries the repair — the src generator agrees using the server hour.
    """
    from src.components.ultimate_book.sleeves import _server_clock as sc

    bars, times = _series_mid_dn(75)
    (route_sub, _sc), _A, states = _oracle_states(monkeypatch, bars, times)
    fired = [i for i in range(route_sub.WARMUP, len(bars))
             if states[i] is not None
             and all(route_sub.cell_coords(states[i]).get(d) == b for d, b in sl.MIDDN_CONDS.items())]
    assert fired, "no firing bar"
    for i in fired:
        assert times[i].hour >= 16, f"firing bar {i} hour {times[i].hour} not NY on the oracle clock"
    # And the live generator's own bucket: it fires only where the SERVER hour is NY.
    for i in range(route_sub.WARMUP, len(bars)):
        got = sl.generate_sub_mid_dn_revert("XAUUSD", bars[: i + 1], "2020-01-01",
                                           bar_time=times[i])
        if got is not None:
            assert se._bucket_session(sc.server_hour(times[i])) == "ny"


def test_mid_dn_fail_closed_without_bar_time(monkeypatch):
    """sub_mid_dn_revert needs the session hour; without bar_time it MUST fail closed even on a bar
    that otherwise matches the cell. WITH the timestamp it fires (control)."""
    bars, times = _series_mid_dn(75)
    (route_sub, _sc), _A, states = _oracle_states(monkeypatch, bars, times)
    fired = [i for i in range(route_sub.WARMUP, len(bars))
             if states[i] is not None
             and all(route_sub.cell_coords(states[i]).get(d) == b for d, b in sl.MIDDN_CONDS.items())]
    assert fired
    i = fired[0]
    assert sl.generate_sub_mid_dn_revert("XAUUSD", bars[: i + 1], "2020-01-01", bar_time=None) is None
    assert sl.generate_sub_mid_dn_revert("XAUUSD", bars[: i + 1], "2020-01-01",
                                         bar_time=times[i]) is not None


# --------------------------------------------------------------------------------------------- #
# oracle-free tests (always run): no-signal / warmup / off-surface / universe
# --------------------------------------------------------------------------------------------- #
def test_flat_series_returns_none():
    flat = [Bar(100.0, 100.1, 99.9, 100.0, 1.0) for _ in range(260)]
    t = _times(260, 16)
    assert sl.generate_sub_xvol_pullback("XAUUSD", flat, "2020-01-01") is None
    assert sl.generate_sub_mid_dn_revert("XAUUSD", flat, "2020-01-01", bar_time=t[-1]) is None


def test_random_series_returns_none_when_no_cell():
    """A plain low-vol random walk should not land in either (narrow) cell -> None."""
    rng = random.Random(11)
    prices, p = [], 1000.0
    for _ in range(260):
        prices.append(p)
        p += rng.gauss(0, 0.5)
    vols = [abs(rng.gauss(0, 1)) * 0.5 + 1.0 for _ in range(260)]
    bars = _bars(prices, vols)
    t = _times(260, 16)
    assert sl.generate_sub_xvol_pullback("XAUUSD", bars, "2020-01-01") is None
    assert sl.generate_sub_mid_dn_revert("XAUUSD", bars, "2020-01-01", bar_time=t[-1]) is None


def test_warmup_below_210_returns_none():
    bars, times = _series_mid_dn(75)
    assert len(bars) >= 210
    assert sl.generate_sub_xvol_pullback("XAUUSD", bars[:209], "2020-01-01") is None
    assert sl.generate_sub_mid_dn_revert("XAUUSD", bars[:209], "2020-01-01", bar_time=times[208]) is None
    assert sl.generate_sub_xvol_pullback("XAUUSD", [], "2020-01-01") is None


def test_off_surface_symbol_returns_none():
    bars, times = _series_xvol(635)
    assert sl.generate_sub_xvol_pullback("EURUSD", bars, "2020-01-01") is None
    assert sl.generate_sub_mid_dn_revert("EURUSD", bars, "2020-01-01", bar_time=times[-1]) is None


def test_on_surface_within_27_universe():
    """Every ON_SURFACE symbol (admission CLEAN3 universe minus W7-dropped) is in the verified FTMO
    27-symbol universe, and the W7 illiquid legs are excluded."""
    universe = {
        "AUDJPY", "BTCUSD", "CHFJPY", "ETHUSD", "EURJPY", "GBPJPY", "GER40", "JP225", "NAS100",
        "SPX500", "UK100", "UKOIL_cash", "US30_cash", "USDJPY", "USOIL_cash", "XAGUSD", "XAUUSD",
        "XAUEUR", "XAGEUR", "XAUAUD", "XAGAUD", "DASHUSD", "CORN_c", "COTTON_c",
        "EU50_cash", "FRA40_cash", "US2000_cash",
    }
    assert len(universe) == 27
    for s in sl.XVOL_ON_SURFACE + sl.MIDDN_ON_SURFACE:
        assert s in universe, f"{s} outside the verified 27-universe"
    for dropped in ("NATGAS_cash", "HEATOIL_c"):
        assert dropped not in sl.XVOL_ON_SURFACE
        assert dropped not in sl.MIDDN_ON_SURFACE
