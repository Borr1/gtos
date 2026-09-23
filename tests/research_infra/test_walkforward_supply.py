"""The research-side specs for the four unregistered generators. Session AK.

Everything here is behavioural. Three of these properties are the ones a wrong answer would
be silent about:

  * a PREFILTER that dropped candidates would make every downstream number a statement about a
    smaller sleeve, and it would look like a clean run — so it is fuzzed as a necessary
    condition rather than reasoned about;
  * `authored_clock` monkeypatches a PRODUCTION module, so its restore is asserted including on
    the exception path — a leaked patch surfaces in whichever session runs next;
  * `server_hm_series` memoises a DST-resolving function on the UTC hour, which is exact only
    because the transition is on the hour. That is pinned against the per-bar function on both
    2026 transition days, in both directions.
"""

from __future__ import annotations

import datetime as dt
import random

import pytest

from src.components.ultimate_book.bar_provider import TF_H4, TF_M15
from src.components.ultimate_book.primitives import Bar
from src.components.ultimate_book.sleeves import _server_clock as sc
from src.components.ultimate_book.sleeves import session_leadlag as SL
from src.components.ultimate_book.sleeves import structural_retest as SR
from src.research_infra.walkforward import supply as SUP

FOUR = ("vol_squeeze", "ny_index_momentum", "structural_retest", "session_leadlag_genuine")


# --------------------------------------------------------------------------- #
# the spec table
# --------------------------------------------------------------------------- #

def test_the_table_covers_exactly_the_four_unreachable_sleeves():
    assert set(SUP.SUPPLY_SPECS) == set(FOUR)


@pytest.mark.parametrize("tag", FOUR)
def test_every_spec_resolves_a_real_generator(tag):
    spec = SUP.SUPPLY_SPECS[tag]
    gen = spec.generator()
    assert callable(gen)
    # It must tolerate the engine's own call shape and emit nothing on an empty series rather
    # than raise: a generator that raises on a short window takes the whole cycle down.
    assert gen("BTCUSD", [], "2026-01-01", bar_time=None, bar_times=None,
               aux_bars=None, aux_times=None) is None


@pytest.mark.parametrize("tag", FOUR)
def test_none_of_the_four_is_reachable_from_any_production_spec_table(tag):
    """The whole premise. If this fails, someone applied the registry proposal."""
    from src.components.ultimate_book.sleeves.registry import (
        BUILT,
        CANDIDATE_BUILT,
        MARKET_EXPANSION_BUILT,
    )

    for table in (BUILT, CANDIDATE_BUILT, MARKET_EXPANSION_BUILT):
        assert tag not in table


def test_the_registry_proposal_is_a_proposal_and_names_tables_that_exist():
    from src.components.ultimate_book.sleeves import registry as R

    assert set(SUP.REGISTRY_EDIT_PROPOSAL) == set(FOUR)
    for tag, prop in SUP.REGISTRY_EDIT_PROPOSAL.items():
        if prop["line"] is None:                      # session_leadlag_genuine
            assert prop["table"] == "not yet proposable"
            assert SUP.SUPPLY_SPECS[tag].needs_cross_symbol_feed
            continue
        assert isinstance(getattr(R, prop["table"]), dict)
        assert tag in prop["line"]


def test_the_cross_symbol_gap_is_recorded_against_the_only_sleeve_that_has_it():
    assert SUP.LIVE_WIRING_GAP["sleeve"] == "session_leadlag_genuine"
    needs = {t for t, s in SUP.SUPPLY_SPECS.items() if s.needs_cross_symbol_feed}
    assert needs == {"session_leadlag_genuine"}


def test_none_of_the_four_has_an_exit_profile_so_the_authored_one_is_the_only_contract():
    """`SLEEVE_EXIT_PROFILES` has no row for any of them, so they fall to DEFAULT_EXIT_PROFILE.
    The `authored_exit` field is therefore the only statement of what each sleeve's own research
    validated, and a gate result computed under the default would be about a different contract."""
    from src.components.ultimate_book.execution_packets import SLEEVE_EXIT_PROFILES

    for tag in FOUR:
        assert tag not in SLEEVE_EXIT_PROFILES
        ex = SUP.SUPPLY_SPECS[tag].authored_exit
        assert ex["cite"] and ("target_r" in ex) and ("time_stop_bars" in ex)


# --------------------------------------------------------------------------- #
# fidelity — the four are scoreable, and the absence they carry is harder than "thin"
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("tag", FOUR)
def test_the_four_are_scoreable_and_carry_the_no_live_path_stamp(tag):
    """Without a fidelity record the gate returns NOT_EVALUABLE on all four and the whole lane
    is unanswerable for a reason that has nothing to do with fidelity. With one, the verdict is
    reachable — and the stamp has to say the record is structurally EMPTY, not thin."""
    from src.research_infra.walkforward.fidelity import fidelity_for

    f = fidelity_for(tag)
    assert f.scoreable(0.50), f.refusal_reason(0.50)
    assert f.basis.value == "transferred_class"
    assert "NO LIVE PATH" in f.basis_note
    assert "structurally EMPTY" in f.basis_note
    assert "NO LIVE PATH" in f.ceiling_stamp(0.50) or "NO LIVE PATH" in f.basis_note


def test_the_stamp_is_confined_to_the_four_and_no_registered_sleeve_carries_it():
    """A registered sleeve picking up this stamp would mean someone mislabelled a live sleeve as
    unreachable, which reads as a much weaker claim than it is."""
    from src.research_infra.walkforward.fidelity import FIDELITY_REGISTER

    carriers = {s for s, f in FIDELITY_REGISTER.items() if "NO LIVE PATH" in f.basis_note}
    assert carriers == set(FOUR)


def test_ny_index_momentum_inherits_its_measured_siblings_class_not_a_new_one():
    """It is the index sibling of `ny_crypto_momentum`, which IS measured directly in the
    fixed-decision-bar class. Inheriting a different class would be a silent re-classification."""
    from src.research_infra.walkforward.fidelity import fidelity_for

    assert fidelity_for("ny_index_momentum").cls is fidelity_for("ny_crypto_momentum").cls
    assert fidelity_for("ny_index_momentum").live_recall == pytest.approx(
        fidelity_for("ny_crypto_momentum").live_recall)


# --------------------------------------------------------------------------- #
# the server-clock index
# --------------------------------------------------------------------------- #

#: America/New_York transitions at 02:00 local, i.e. 07:00 UTC in both directions. 2026: DST
#: starts 2026-03-08 and ends 2026-11-01.
@pytest.mark.parametrize("day", ["2026-03-08", "2026-11-01", "2026-07-15", "2026-01-15"])
def test_the_hour_memo_matches_the_per_bar_function_across_a_transition(day):
    d0 = dt.datetime.fromisoformat(day).replace(tzinfo=dt.timezone.utc)
    times = [d0 + dt.timedelta(minutes=15 * k) for k in range(96)]
    assert SUP.server_hm_series(times) == [sc.server_hour_minute(t) for t in times]


def test_a_transition_day_actually_changes_offset_inside_the_sample():
    """Guards the test above from being vacuous: if the sampled day had one offset all through,
    a memo keyed on anything at all would pass it."""
    d0 = dt.datetime(2026, 3, 8, tzinfo=dt.timezone.utc)
    times = [d0 + dt.timedelta(minutes=15 * k) for k in range(96)]
    offsets = {(sc.server_hour(t) - t.hour) % 24 for t in times}
    assert len(offsets) == 2, offsets


def test_the_index_fails_closed_on_an_unusable_stamp():
    assert SUP.server_hm_series([None]) == [(None, None)]


# --------------------------------------------------------------------------- #
# the F7 A/B harness
# --------------------------------------------------------------------------- #

def test_authored_clock_restores_the_production_function():
    before = SR._hour
    with SUP.authored_clock("structural_retest"):
        assert SR._hour is not before
    assert SR._hour is before


def test_authored_clock_restores_on_an_exception():
    before = SR._hour
    with pytest.raises(RuntimeError):
        with SUP.authored_clock("structural_retest"):
            raise RuntimeError("boom")
    assert SR._hour is before


def test_authored_clock_refuses_modules_this_session_did_not_change():
    with pytest.raises(ValueError, match="refused"):
        with SUP.authored_clock("metals"):
            pass


def test_authored_clock_covers_substrate_and_restores_it():
    """B1200 added `substrate` — the third module whose clock this programme repaired. The A/B
    reads through `_session_hour`, so the swap has to land on that attribute and be given back."""
    from src.components.ultimate_book.sleeves import substrate as SUB
    from src.components.ultimate_book.sleeves import substrate_engine as SE

    before = SUB._session_hour
    t = dt.datetime(2026, 7, 15, 14, tzinfo=dt.timezone.utc)     # server 17 -> ny; raw 14 -> london
    assert SE._bucket_session(SUB._session_hour(t)) == "ny"
    with SUP.authored_clock("substrate"):
        assert SUB._session_hour(t) == 14
        assert SE._bucket_session(SUB._session_hour(t)) == "london"
    assert SUB._session_hour is before

    with pytest.raises(RuntimeError):
        with SUP.authored_clock("substrate"):
            raise RuntimeError("boom")
    assert SUB._session_hour is before


def test_authored_clock_swaps_every_module_at_once():
    """All three together, because the driver A/Bs one sleeve at a time and a partial swap would
    silently mix clocks across a shared walk."""
    from src.components.ultimate_book.sleeves import substrate as SUB

    saved = (SR._hour, SL.server_hour, SUB._session_hour)
    with SUP.authored_clock("structural_retest", "session_leadlag", "substrate") as note:
        assert set(note) == {"structural_retest", "session_leadlag", "substrate"}
        assert (SR._hour, SL.server_hour, SUB._session_hour) != saved
        assert SR._hour is SL.server_hour is SUB._session_hour
    assert (SR._hour, SL.server_hour, SUB._session_hour) == saved


@pytest.mark.parametrize("utc_hour,day,authored_session,repaired_session", [
    # Summer, broker +3. 06:00 UTC is 09:00 server: authored reads 6 -> Asian, repaired reads
    # 9 -> London. The metal SHORT cell is (metal, London, dn, high), so this bar is
    # untradeable under the old clock and tradeable under the new one.
    (6, "2026-07-15", "Asian", "London"),
    # 14:00 UTC is 17:00 server: authored London, repaired NY -> the crypto SHORT cell.
    (14, "2026-07-15", "London", "NY"),
    # Winter, broker +2: 06:00 UTC is 08:00 server -> also crosses the 8 boundary.
    (6, "2026-01-15", "Asian", "London"),
])
def test_the_f7_repair_moves_bars_between_session_buckets(utc_hour, day, authored_session,
                                                          repaired_session):
    """The repair is not cosmetic: the session bucket IS the whitelist key, so a shifted bucket
    changes whether a bar can trade and in which direction."""
    t = dt.datetime.fromisoformat(day).replace(hour=utc_hour, tzinfo=dt.timezone.utc)
    assert SR._session(SR._hour(t)) == repaired_session
    with SUP.authored_clock("structural_retest"):
        assert SR._session(SR._hour(t)) == authored_session


def test_the_repaired_clock_is_the_one_the_nine_deployed_sleeves_use():
    """`structural_retest` was the only sleeve in the package still on raw UTC."""
    t = dt.datetime(2026, 7, 15, 9, 0, tzinfo=dt.timezone.utc)
    assert SR._hour(t) == sc.server_hour(t) == 12


# --------------------------------------------------------------------------- #
# the prefilters, fuzzed as necessary conditions
# --------------------------------------------------------------------------- #

def _series(n: int, seed: int, *, vol_bursts: bool = True,
            drift: float = 0.0) -> tuple[list[Bar], list]:
    """A random walk with occasional volatility bursts, so the high-vol gates can open.

    `drift` exists for the `structural_retest` index cell, whose whitelist entry is
    `(index, Asian, up, high)` — it needs an UP higher-timeframe regime to be reachable at all,
    and a zero-drift walk supplies one only by accident.
    """
    rng = random.Random(seed)
    px = 100.0
    bars: list[Bar] = []
    for k in range(n):
        scale = 0.8 if (vol_bursts and (k // 37) % 5 == 0) else 0.12
        o = px
        c = max(0.5, o + drift + rng.gauss(0, scale))
        h = max(o, c) + abs(rng.gauss(0, scale)) * 0.6
        low = min(o, c) - abs(rng.gauss(0, scale)) * 0.6
        bars.append(Bar(o, h, max(0.1, low), c, 1000.0 + rng.random() * 500))
        px = c
    t0 = dt.datetime(2025, 1, 6, tzinfo=dt.timezone.utc)
    times = [t0 + dt.timedelta(minutes=15 * k) for k in range(n)]
    return bars, times


#: `structural_retest` needs a long series before its (vol AND session AND regime AND detector)
#: conjunction fires often enough for the fuzz to mean anything — at 900 bars it emitted zero,
#: which would have made the safety assertion vacuous. 2,300 gives tens of emissions per symbol.
@pytest.mark.parametrize("tag,symbol,n,seed,drift", [
    ("structural_retest", "XAUUSD", 2300, 11, 0.0),      # the metal SHORT cell
    ("structural_retest", "BTCUSD", 2300, 12, 0.0),      # the crypto SHORT cell
    ("structural_retest", "SPX500", 2300, 13, 0.05),     # the index LONG cell — needs an uptrend
    ("ny_index_momentum", "SPX500", 1100, 14, 0.0),
    ("vol_squeeze", "GER40", 700, 15, 0.0),
])
def test_the_prefilter_never_drops_a_bar_the_generator_would_have_taken(tag, symbol, n, seed,
                                                                       drift):
    """The safety property. Run the generator on EVERY bar past the floor, unfiltered, and
    assert the prefilter passed each bar that emitted. A prefilter that is merely *sufficient*
    would silently shrink the sleeve."""
    spec = SUP.SUPPLY_SPECS[tag]
    gen = spec.generator()
    bars, times = _series(n, seed, drift=drift)
    ctx = SUP.build_series_context(symbol, spec.timeframe, bars, times, **spec.needs())
    L = spec.bar_count
    n_emit = n_pass = 0
    for i in range(L - 1, len(bars) - 2):
        lo = i - (L - 1)
        w, wt = bars[lo:i + 1], times[lo:i + 1]
        intent = gen(symbol, w, "2025-01-06", bar_time=times[i], bar_times=wt,
                     aux_bars=None, aux_times=None)
        passed = spec.prefilter(ctx, i)
        n_pass += bool(passed)
        if intent is not None:
            n_emit += 1
            assert passed, f"{tag} {symbol}: prefilter dropped an emitting bar at {i}"
    # A prefilter that passes everything is trivially safe and useless; a fuzz that emits
    # nothing proves nothing. Both are checked so the assertion above cannot be vacuous.
    assert n_emit > 0, f"{tag} {symbol}: fuzz produced no intents — the test proves nothing"
    assert n_pass < (len(bars) - L), f"{tag} {symbol}: prefilter rejects nothing"


# --------------------------------------------------------------------------- #
# the structural_retest HTF window-phase dependence
# --------------------------------------------------------------------------- #

def test_the_htf_reference_block_is_the_16_bars_before_i_only_at_the_513_phase():
    """`_htf_trend_at` chunks from index 0 of the WINDOW, so the absolute bars it reads depend on
    the window length mod 16. This pins that 513 is the aligned phase and that a misaligned one
    reads a staler block — the reason `bar_count` is not a free parameter for this generator."""
    bars, _ = _series(900, 21)

    def ref_block(L: int) -> tuple[int, int]:
        """(first, last) WINDOW indices of the block `_htf_trend_at` compares against."""
        i = L - 1
        blk = i // SR.HTF_BARS - 1
        return blk * SR.HTF_BARS, blk * SR.HTF_BARS + SR.HTF_BARS - 1

    _, hi513 = ref_block(513)
    assert (513 - 1) - hi513 == 1, "at 513 the reference block ends on the bar just before i"
    _, hi528 = ref_block(528)
    assert (528 - 1) - hi528 == 16, "at 528 it ends 16 bars before i — a staler HTF bar"

    # And the trend VALUE differs on real-shaped data, which is what makes this a defect rather
    # than a curiosity: the same absolute bar, two window lengths, two regimes — hence possibly
    # two whitelist cells and two trade DIRECTIONS.
    disagree = 0
    for abs_i in range(700, 900):
        v513 = SR._htf_trend_at(bars[abs_i - 512:abs_i + 1], 512)
        v528 = SR._htf_trend_at(bars[abs_i - 527:abs_i + 1], 527)
        disagree += (v513 != v528)
    assert disagree > 0, (
        "the two window phases agreed on all 200 bars — either the fuzz is degenerate or the "
        "chunking is phase-independent after all, and this note should be withdrawn")


# --------------------------------------------------------------------------- #
# session_leadlag_genuine
# --------------------------------------------------------------------------- #

def test_the_legs_are_the_four_LL_FWD_rows_in_declared_order():
    assert [(l.leader, l.follower, l.look, l.zthr, l.thesis, l.geom, l.session) for l in SL.LEGS] == [
        ("US30_cash", "GER40", 8, 1.5, "momentum", "TRAIL", "ny_open"),
        ("USDJPY", "AUDJPY", 8, 2.5, "momentum", "T2.0", "london_ny"),
        ("US30_cash", "USDJPY", 4, 2.0, "momentum", "T2.0", "ny_open"),
        ("US30_cash", "AUDJPY", 8, 1.5, "reversion", "T2.0", "ny_open"),
    ]
    assert SL.FOLLOWERS == ("GER40", "AUDJPY", "USDJPY")


def test_the_registry_surface_is_wider_than_the_tradeable_one():
    """Six registered symbols, three followers. Recorded so nobody reads six as six legs."""
    from src.components.ultimate_book.admission import CLEAN4_REGISTRY

    registered = set(CLEAN4_REGISTRY["session_leadlag_genuine"].symbols)
    assert registered == {"US30_cash", "GER40", "USDJPY", "AUDJPY", "SPX500", "NAS100"}
    assert set(SL.FOLLOWERS) < registered
    assert registered - set(SL.FOLLOWERS) - set(SL.LEADERS) == {"SPX500", "NAS100"}


def _leader_feed(n: int, seed: int, times) -> SL.LeaderImpulse:
    rng = random.Random(seed)
    px, closes = 100.0, []
    for _ in range(n):
        px = max(1.0, px * (1.0 + rng.gauss(0, 0.004)))
        closes.append(px)
    return SL.LeaderImpulse(times, closes)


def test_it_fails_closed_without_a_leader_feed_and_fires_with_one():
    """The property that makes this module safe to land while the engine has no leader channel."""
    n = 600
    bars, times = _series(n, 31)
    i = n - 3
    w, wt = bars[: i + 1], times[: i + 1]
    # 14:00 UTC in July is server 17:00 -> inside ny_open (13..16)? No: 17 is outside. Pick a
    # bar whose SERVER hour lands in ny_open, so the session gate is not what is being tested.
    j = next(k for k in range(400, i) if sc.server_hour(times[k]) == 14)
    w, wt = bars[: j + 1], times[: j + 1]
    assert SL.generate("GER40", w, "2025-01-06", bar_time=times[j], bar_times=wt) is None

    feeds = {"US30_cash": _leader_feed(n, 32, times)}
    fired = None
    for k in range(400, i):
        if sc.server_hour(times[k]) not in (13, 14, 15):
            continue
        got = SL.generate("GER40", bars[: k + 1], "2025-01-06", bar_time=times[k],
                          bar_times=times[: k + 1], leader_feeds=feeds)
        if got is not None:
            fired = got
            break
    assert fired is not None, "no leg fired anywhere in the fuzz — the test proves nothing"
    assert fired.sleeve == "session_leadlag_genuine"
    assert fired.ll_impulse == "US30_cash->GER40@TRAIL"
    assert fired.target_dist is None            # the TRAIL leg carries no target
    assert fired.stop_dist > 0


def test_the_T2_geometry_is_four_R_and_not_two():
    """`mine_pair` scales the stop by 0.5*ATR and the target by 2.0*ATR independently, so the
    target sits at 4 R. Misreading it as 2 R would halve every T2.0 leg's upside."""
    atr, stop = 1.6, 0.8
    assert SL.target_dist_for("T2.0", atr, stop) == pytest.approx(3.2)
    assert SL.target_dist_for("T2.0", atr, stop) / stop == pytest.approx(4.0)
    assert SL.target_dist_for("TRAIL", atr, stop) is None
    assert SL.trail_for("TRAIL", stop) == (1.6, 0.8)
    assert SL.trail_for("T2.0", stop) == (None, None)


def test_leader_z_matches_the_KB5_formula():
    """`leader_signal` z-scores against the POPULATION sd of the VOLWIN sums strictly before i.
    A sample sd would give a smaller divisor, a larger z, and would let more trades through
    every `zthr` gate — so the divisor is not a detail."""
    import math
    import statistics

    look = 4
    n = SL.VOLWIN + look + 40
    rng = random.Random(77)
    closes = [100.0]
    for _ in range(n - 1):
        closes.append(max(1.0, closes[-1] * (1.0 + rng.gauss(0, 0.003))))
    t0 = dt.datetime(2025, 1, 6, tzinfo=dt.timezone.utc)
    times = [t0 + dt.timedelta(minutes=15 * k) for k in range(n)]
    feed = SL.LeaderImpulse(times, closes)

    lr = [0.0] + [math.log(closes[k] / closes[k - 1]) for k in range(1, n)]
    cum = [0.0] * n
    for k in range(look, n):
        cum[k] = sum(lr[k - look + 1:k + 1])
    i = n - 1
    win = cum[i - SL.VOLWIN:i]
    m = statistics.fmean(win)
    sd = statistics.pstdev(win)
    assert feed.z(times[i], look) == pytest.approx((cum[i] - m) / sd, rel=1e-12)
    # strictly-before-i window: a lookahead version would include cum[i] in the moments
    sd_leaky = statistics.pstdev(cum[i - SL.VOLWIN + 1:i + 1])
    assert sd != pytest.approx(sd_leaky, rel=1e-9)


def test_the_session_gate_is_on_the_server_clock():
    """`_session_ok`'s windows are research-archive (server) hours; the live feed is UTC."""
    t_summer = dt.datetime(2026, 7, 15, 11, 0, tzinfo=dt.timezone.utc)   # server 14:00
    assert sc.server_hour(t_summer) == 14
    assert SL.session_ok(sc.server_hour(t_summer), "ny_open")
    assert not SL.session_ok(t_summer.hour, "ny_open")        # 11 is outside 13..16
    assert not SL.session_ok(None, "ny_open")                 # fails closed


def test_min_gap_is_not_enforced_inside_the_generator():
    """It is per-series state; keeping it out is what makes the generator a pure function of the
    decision bar. The driver applies it and publishes both counts."""
    assert SL.MIN_GAP_BARS == 4
    n = 600
    bars, times = _series(n, 41)
    feeds = {"US30_cash": _leader_feed(n, 42, times), "USDJPY": _leader_feed(n, 43, times)}
    fires = [k for k in range(300, n - 3)
             if SL.generate("AUDJPY", bars[: k + 1], "2025-01-06", bar_time=times[k],
                            bar_times=times[: k + 1], leader_feeds=feeds) is not None]
    assert fires, "fuzz produced no fires"
    # If min_gap were enforced in the generator, no two fires could be < 4 bars apart. It is
    # not, so the driver has to do it — which is the point of the assertion.
    assert any(b - a < SL.MIN_GAP_BARS for a, b in zip(fires, fires[1:])) or len(fires) < 2
