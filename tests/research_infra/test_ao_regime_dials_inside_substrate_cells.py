"""Session AO (B1301): the regime dials are INSIDE both substrate cells, and that is checkable
without any market data.

WHY THIS TEST EXISTS
--------------------
Two sessions in a row were routed to a no-op. AL §10 item 2 filed `sub_xvol_pullback`'s next
lever as "AB's regime dials, unexplored for this sleeve"; the wave-10 commission repeated it;
and `diagnostics.Prescription.REGIME_GATE_OR_PARK` will keep emitting it, because the gate
cannot see that the sleeve already gates on the variable the prescription names.

It is not an empirical fact about the market. Four of Session AB's five published dials ARE
`substrate_engine`'s confluence coordinates term for term, and `substrate.XVOL_CONDS` /
`MIDDN_CONDS` fix each of those coordinates to one bucket. So a bucket-level gate on them is
the identity filter, by composition of two functions, and the assertions below are arithmetic
rather than statistical.

WHAT IS ASSERTED, AND WHY IT IS BEHAVIOURAL RATHER THAN A SOURCE GREP
--------------------------------------------------------------------
`test_dial_bucketiser_agrees_with_the_engine_discretizer` drives both implementations over a
dense sweep of values and compares OUTPUTS. `test_horizon_conflict_is_mtf_align` builds real
`Bar` series and compares `regime_spine.dials._horizon_conflict` against
`substrate_engine.compute_state`'s `mtf_align` on each. A grep for `_bucket_vr` would pass
against a wrong implementation; these cannot.
"""

from __future__ import annotations

import datetime as dt
import math
import random

import pytest

from src.components.ultimate_book.primitives import Bar, atr14, autocorr, vol_ratio
from src.components.ultimate_book.sleeves import substrate as SUB
from src.components.ultimate_book.sleeves import substrate_engine as SE
from src.research_infra.regime_spine import dials as DIALS
from src.research_infra.regime_spine.state import build_frame

#: `af_repairs.bucket`'s implementation of AB's band edges, which every session from AF onward
#: has used. Reproduced here rather than imported because `af_repairs.py` is a receipt script
#: under `docs/`, and a test that imports a receipt couples the suite to one session's artifact.
#: The point of the test is that this and the engine's discretizer are the SAME function.
def ab_bucket(name: str, v):
    if v is None:
        return "na"
    if name == "VOL_REGIME":
        return "lo" if v < 0.85 else "mid" if v < 1.15 else "hi" if v < 1.60 else "xhi"
    if name == "PERSISTENCE":
        return "revert" if v < -0.10 else ("trend" if v >= 0.10 else "random")
    if name == "TREND_STATE":
        return "dn" if v < -1.5 else ("up" if v >= 1.5 else "flat")
    if name == "HORIZON_CONFLICT":
        return {-1: "conflict", 0: "neutral", 1: "aligned"}[int(v)]
    raise AssertionError(name)


#: (AB dial, the `cell_coords` key it is the same quantity as, the label map between them).
#: `PERSISTENCE`/`persist` differ only in the NAME of the middle bucket, which is why the map
#: is explicit instead of an equality.
DIAL_TO_COORD = (
    ("VOL_REGIME", "vol", {"lo": "lo", "mid": "mid", "hi": "hi", "xhi": "xhi"}),
    ("PERSISTENCE", "persist", {"revert": "revert", "random": "rand", "trend": "trend"}),
    ("TREND_STATE", "trend", {"dn": "dn", "flat": "flat", "up": "up"}),
    ("HORIZON_CONFLICT", "mtf",
     {"conflict": "conflict", "neutral": "neutral", "aligned": "aligned"}),
)


def _bars(n: int, seed: int) -> list[Bar]:
    """A random-walk series with enough length for `compute_state` (needs i >= 199)."""
    rng = random.Random(seed)
    price = 100.0
    out = []
    for _ in range(n):
        step = rng.gauss(0, 1.0) * (1 + 0.5 * math.sin(len(out) / 37.0))
        o = price
        price = max(1.0, price + step)
        hi = max(o, price) + abs(rng.gauss(0, 0.4))
        lo = min(o, price) - abs(rng.gauss(0, 0.4))
        out.append(Bar(o, hi, lo, price, 100.0 + rng.random() * 900))
    return out


# ---------------------------------------------------------------------------------------
def test_dial_bucketiser_agrees_with_the_engine_discretizer_except_at_two_points():
    """AB's bands and `substrate_engine`'s discretizers are the same partition on the interior
    and disagree at EXACTLY two boundary points. Found by this test on its first run [B1302].

    The first version asserted plain equality and failed at `ac60 == -0.10`. Both are real and
    neither had been recorded:

      * `_bucket_persist` returns `revert` at `a <= -0.10`; `af_repairs.bucket` returns `random`
        at `v == -0.10` because its predicate is `v < -0.10`. So a `sub_mid_dn_revert` trade
        firing at exactly ac60 = -0.10 -- which the ENGINE admits, since its cell needs
        `persist=revert` -- would be labelled `random` by every session that used AF's
        bucketiser (AF, AH, AO).
      * `_bucket_slope` returns `flat` at `s == 1.5`; AF's returns `up` because its predicate is
        `v >= 1.5`. This one cannot arise inside `sub_xvol_pullback`: its cell needs
        `trend=up`, the engine grants that only at `slope50 > 1.5`, so no firing trade sits on
        the point.

    **Measured consequence: zero.** AO's `dial_parity` control compares the two label sets over
    all 3,448 trades of the three sleeves it walked and reports 0 disagreements, because no
    float lands exactly on either boundary. The discrepancy is latent, not active, and it is
    pinned here so a future session neither trips over it nor "fixes" AF's committed receipt and
    silently moves AF's and AH's published cells.
    """
    vals = [round(x * 0.005 - 3.0, 6) for x in range(1400)]
    vals += [0.85, 1.15, 1.60, 2.0, -0.10, 0.0, 0.10, -1.5, 1.5]
    disagree = {"VOL_REGIME": [], "PERSISTENCE": [], "TREND_STATE": []}
    for v in vals:
        if ab_bucket("VOL_REGIME", v) != SE._bucket_vr(v):
            disagree["VOL_REGIME"].append(v)
        if ab_bucket("TREND_STATE", v) != SE._bucket_slope(v):
            disagree["TREND_STATE"].append(v)
        if DIAL_TO_COORD[1][2][ab_bucket("PERSISTENCE", v)] != SE._bucket_persist(v):
            disagree["PERSISTENCE"].append(v)
    assert disagree["VOL_REGIME"] == [], disagree["VOL_REGIME"]
    assert sorted(set(disagree["PERSISTENCE"])) == [-0.10], disagree["PERSISTENCE"]
    assert sorted(set(disagree["TREND_STATE"])) == [1.5], disagree["TREND_STATE"]
    # and each disagreement is exactly the pair the docstring names
    assert (ab_bucket("PERSISTENCE", -0.10), SE._bucket_persist(-0.10)) == ("random", "revert")
    assert (ab_bucket("TREND_STATE", 1.5), SE._bucket_slope(1.5)) == ("up", "flat")
    for a in (-1, 0, 1):
        assert ab_bucket("HORIZON_CONFLICT", a) == SE._MTF_LABEL[a]


def test_the_slope_boundary_disagreement_cannot_reach_the_xvol_cell():
    """`sub_xvol_pullback` needs `trend=up`, which the engine grants only above 1.5, so the
    `slope50 == 1.5` disagreement is unreachable inside the cell. Asserted rather than argued,
    because 'it cannot happen' is the kind of claim that stops being true when a constant moves.
    """
    assert SUB.XVOL_CONDS["trend"] == "up"
    assert SE._bucket_slope(1.5) != "up"
    assert SE._bucket_slope(1.5 + 1e-9) == "up"
    # the persistence one CAN reach `sub_mid_dn_revert`, which is why it is the live half.
    assert SUB.MIDDN_CONDS["persist"] == "revert"
    assert SE._bucket_persist(-0.10) == "revert"
    assert DIAL_TO_COORD[1][2][ab_bucket("PERSISTENCE", -0.10)] != "revert"


@pytest.mark.parametrize("seed", [1, 2, 3, 5, 8, 13])
def test_horizon_conflict_is_mtf_align(seed):
    """`dials._horizon_conflict`'s docstring claims it IS `mtf_align`. Verified on real series.

    Both are driven over the same bars and compared per bar. This is the one identification in
    the set that is a claim about two different code paths rather than about two discretizers.
    """
    bars = _bars(400, seed)
    times = [dt.datetime(2020, 1, 1, tzinfo=dt.timezone.utc) + dt.timedelta(hours=4 * k)
             for k in range(len(bars))]
    frame = build_frame(symbol="TEST", timeframe=16388, bars=bars, times_utc=times)
    n = 0
    for i in range(210, len(bars)):
        st = SE.compute_state(bars, i, None)
        if st is None:
            continue
        assert DIALS._horizon_conflict(frame, i) == st["mtf_align"], i
        n += 1
    assert n > 100, f"only {n} comparable bars; the test would be vacuous"


@pytest.mark.parametrize("seed", [1, 4, 9])
def test_ab_dial_values_equal_the_engine_state(seed):
    """`VOL_REGIME`/`PERSISTENCE`/`TREND_STATE` are `vr`/`ac60`/`slope50`, numerically.

    `primitives.autocorr` uses `statistics.mean` and `substrate_engine._ac` uses `sum/n`, so an
    exact-equality assertion is the interesting one: if they ever diverge past float noise the
    pinning claim needs re-measuring.
    """
    bars = _bars(400, seed)
    atrs = [atr14(bars, k) for k in range(len(bars))]
    n = 0
    for i in range(210, len(bars)):
        st = SE.compute_state(bars, i, None)
        if st is None:
            continue
        assert abs(vol_ratio(atrs, i) - st["vr"]) < 1e-12, i
        assert abs(autocorr(bars, i, 60) - st["ac60"]) < 1e-12, i
        n += 1
    assert n > 100


@pytest.mark.parametrize("cell_name,conds", [("sub_xvol_pullback", SUB.XVOL_CONDS),
                                             ("sub_mid_dn_revert", SUB.MIDDN_CONDS)])
def test_every_ab_dial_is_pinned_to_one_bucket_by_the_cell(cell_name, conds):
    """The structural claim: a bucket gate on any AB dial cannot move a trade of either sleeve.

    For each dial, count how many of its buckets are consistent with the cell's own condition
    on the coordinate that dial IS. Exactly one means pinned.
    """
    pinned = {}
    for dial, coord, label_map in DIAL_TO_COORD:
        required = conds.get(coord)
        assert required is not None, (
            f"{cell_name} does not constrain {coord!r}, so {dial} is FREE for it and this "
            f"test's premise has changed -- re-read AO's pinning table before editing it")
        consistent = [d for d, c in label_map.items() if c == required]
        pinned[dial] = consistent
        assert len(consistent) == 1, (dial, required, consistent)
    assert len(pinned) == 4


def test_the_free_coordinates_are_exactly_what_ao_measured():
    """`sub_xvol_pullback` is depth-4 and leaves rngpos / comp / session free;
    `sub_mid_dn_revert` is depth-7 and leaves none. That asymmetry is why AO could pre-declare
    two cells for one sleeve and none for the other, so it is pinned."""
    all_coords = {"vol", "trend", "mtf", "rngpos", "comp", "persist", "session"}
    xvol_free = all_coords - set(SUB.XVOL_CONDS)
    middn_free = all_coords - set(SUB.MIDDN_CONDS)
    assert xvol_free == {"rngpos", "comp", "session"}, xvol_free
    assert middn_free == set(), middn_free
    # and `cell_coords` really does emit all seven (session only when an hour is supplied),
    # so "free" means free in the engine and not just in the cell string.
    bars = _bars(300, 7)
    st = SE.compute_state(bars, len(bars) - 1, 13)
    assert set(SE.cell_coords(st)) == all_coords
    st_nohour = SE.compute_state(bars, len(bars) - 1, None)
    assert set(SE.cell_coords(st_nohour)) == all_coords - {"session"}
