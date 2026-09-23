"""The deployed sleeves gate on BROKER-SERVER hours, not UTC hours (F7 live half, B29/B54).

These pin the repair made on 2026-07-26. They are behavioural: each asserts the UTC instant at
which a sleeve's gate opens, across both DST seasons, rather than asserting that some source
string is present. A source-string test would pass against the very defect this fixes.

What was wrong: every sleeve here was mined on the broker-clock research archive, so its hour
constants are FTMO **server** hours; the live feed delivers **true UTC**
(``mt5_real.py:210-218`` subtracts the detected offset). Comparing ``t.hour`` to a server
constant fired the sleeve 3 h late in summer and 2 h late in winter.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.components.ultimate_book.sleeves import _server_clock as sc
from src.components.ultimate_book.sleeves import (
    asia_pdl_fade as PDL,
    asian_fade as AF,
    kz_london_crypto_low as KLZ,
    liq_asia_up_low_metal as LIQ,
    metal_session_reversion as MSR,
    ny_crypto_momentum as NM,
    ny_index_momentum as NIM,
    orb_crypto_london as ORB,
    session_leadlag as SLL,
    structural_retest as SRS,
    vss_fxcross_london_up_low as VSS,
)

SUMMER = datetime(2026, 7, 15, tzinfo=timezone.utc)   # broker +3
WINTER = datetime(2026, 1, 15, tzinfo=timezone.utc)   # broker +2


def _at(day: datetime, utc_hour: int, minute: int = 0) -> datetime:
    return day.replace(hour=utc_hour, minute=minute)


# --------------------------------------------------------------------------- #
# The converter itself
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("day,offset", [(SUMMER, 3), (WINTER, 2)])
def test_offset_is_three_in_summer_and_two_in_winter(day, offset):
    assert sc.server_hour(_at(day, 9)) == 9 + offset


def test_the_offset_is_not_a_constant():
    """The whole point of a rule over a constant: the two seasons must differ."""
    assert sc.server_hour(_at(SUMMER, 9)) != sc.server_hour(_at(WINTER, 9))


@pytest.mark.parametrize("bad", [None, "", "not-a-timestamp", "2026-13-45T99:99", object()])
def test_unparseable_input_fails_closed(bad):
    assert sc.to_server_local(bad) is None
    assert sc.server_hour(bad) is None
    assert sc.server_day(bad) is None
    assert sc.server_hour_minute(bad) == (None, None)


def test_naive_and_z_suffixed_and_aware_all_agree():
    aware = "2026-07-15T09:00:00+00:00"
    assert (
        sc.server_hour(aware)
        == sc.server_hour("2026-07-15T09:00:00Z")
        == sc.server_hour("2026-07-15T09:00:00")          # naive is treated as UTC
        == sc.server_hour(datetime(2026, 7, 15, 9, tzinfo=timezone.utc))
        == 12
    )


def test_the_day_key_rolls_at_server_midnight_not_utc_midnight():
    """Server midnight in summer is 21:00 UTC, so a 22:00 UTC bar is already the NEXT server day."""
    assert sc.server_day(_at(SUMMER, 20, 30)) == "2026-07-15"
    assert sc.server_day(_at(SUMMER, 21, 30)) == "2026-07-16"


# --------------------------------------------------------------------------- #
# The sleeves. Exact-match gates are pinned to the minute.
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "mod,server_hour",
    [(NM, 17), (KLZ, 12), (NIM, 17)],
    ids=["ny_crypto_momentum", "kz_london_crypto_low", "ny_index_momentum"],
)
@pytest.mark.parametrize("day,offset", [(SUMMER, 3), (WINTER, 2)], ids=["summer", "winter"])
def test_exact_match_sleeves_open_at_the_fitted_utc_hour(mod, server_hour, day, offset):
    """These match on an exact (hour, minute), so before the fix they hit the wrong bar daily."""
    assert mod.DECISION_HOUR == server_hour
    fires_at_utc = server_hour - offset
    assert mod._hm(_at(day, fires_at_utc, mod.DECISION_MIN)) == (server_hour, mod.DECISION_MIN)
    # and NOT at the naive-UTC hour it used to fire at
    assert mod._hm(_at(day, server_hour, mod.DECISION_MIN))[0] != server_hour


@pytest.mark.parametrize(
    "mod",
    [AF, PDL, ORB, MSR, LIQ, VSS, SRS],
    ids=["asian_fade", "asia_pdl_fade", "orb_crypto_london",
         "metal_session_reversion", "liq_asia_up_low_metal", "vss_fxcross_london_up_low",
         "structural_retest"],
)
@pytest.mark.parametrize("day,offset", [(SUMMER, 3), (WINTER, 2)], ids=["summer", "winter"])
def test_window_sleeves_read_server_hours(mod, day, offset):
    for utc_hour in (0, 6, 9, 13, 20):
        expected = (utc_hour + offset) % 24
        assert mod._hour(_at(day, utc_hour)) == expected
    assert mod._hour(None) is None


# --------------------------------------------------------------------------- #
# structural_retest — the tenth sleeve, repaired 2026-07-30 (Session AK, B950).
#
# The B29/B54 pass enumerated the DEPLOYED sleeves and this one is in no registry, so it kept
# `return t.hour` for four more months. Its session boundaries are a verbatim port of
# `wave1_structure_setups_ict.session_id` (`:93-97`), which read the broker-clock research
# archive, so they are server hours and the raw-UTC comparison was F7 exactly.
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("day,offset", [(SUMMER, 3), (WINTER, 2)], ids=["summer", "winter"])
@pytest.mark.parametrize("utc_hour,server_session", [
    (3, "Asian"),      # server 05/06 -> Asian (< 8)
    (6, "London"),     # server 09/08 -> London: the bucket the old clock called Asian
    (14, "NY"),        # server 17/16 -> NY: the bucket the old clock called London
    (20, "NY"),
])
def test_structural_retest_sessions_are_bucketed_on_the_server_clock(day, offset, utc_hour,
                                                                     server_session):
    """The session bucket IS this sleeve's whitelist key, so a shifted bucket changes whether a
    bar can trade AND in which direction — two of its three cells are SHORT and one is LONG."""
    t = _at(day, utc_hour)
    assert SRS._hour(t) == (utc_hour + offset) % 24
    assert SRS._session(SRS._hour(t)) == server_session
    # The naive reading it used to do lands in a different bucket for the two boundary hours.
    if utc_hour in (6, 14):
        assert SRS._session(t.hour) != server_session


def test_structural_retest_fails_closed_on_an_unusable_stamp():
    assert SRS._hour(None) is None
    assert SRS._session(None) is None
    assert SRS.generate("BTCUSD", [], "2026-07-15", bar_time=None) is None


def test_session_leadlag_gates_on_server_hours_from_the_start():
    """Built correct in B960 rather than repaired: `KB5_leadlag_subh4._session_ok`'s windows are
    research-archive (server) hours and its own comment calling them 'winter UTC' is wrong about
    its own data."""
    t = _at(SUMMER, 11)                                  # server 14:00, inside ny_open 13..16
    assert sc.server_hour(t) == 14
    assert SLL.session_ok(sc.server_hour(t), "ny_open")
    assert not SLL.session_ok(t.hour, "ny_open")
    assert not SLL.session_ok(None, "ny_open")


@pytest.mark.parametrize("mod", [AF, PDL, ORB, MSR, LIQ], ids=lambda m: m.__name__.rsplit(".", 1)[-1])
def test_window_sleeves_group_prior_day_levels_on_server_days(mod):
    """PDH/PDL, the Asian range and the opening range were all keyed on the wrong window."""
    assert mod._day(_at(SUMMER, 20, 30)) == "2026-07-15"
    assert mod._day(_at(SUMMER, 21, 30)) == "2026-07-16"
    assert mod._day(None) is None


# --------------------------------------------------------------------------- #
# Scope boundary — B54 Part 2 is deliberately NOT done here.
# --------------------------------------------------------------------------- #

def test_the_correlated_unit_key_is_deliberately_still_utc():
    """`decision_day_of` drives the one-unit-per-cluster-per-day envelope the dial was certified
    on (`book_owner.py:1608-1610`). Moving it is an owner decision about risk, not a clock repair,
    so it is intentionally untouched. This test exists so that changing it is a deliberate act
    that updates a test which says why -- not a silent side effect of a clock cleanup."""
    from src.components.ultimate_book.bar_provider import decision_day_of

    assert decision_day_of(_at(SUMMER, 21, 30)) == "2026-07-15"     # still the UTC date
    assert decision_day_of(_at(SUMMER, 21, 30)) != sc.server_day(_at(SUMMER, 21, 30))


def test_fx_jpy_and_metals_use_the_same_calendar_not_a_second_one():
    """fx_jpy carries its own converter (metals imports it). Both must agree with this module,
    or the package would hold two clocks -- which is how F7 survived as long as it did."""
    from src.components.ultimate_book.sleeves.fx_jpy import _to_server_local

    for day in (SUMMER, WINTER):
        for hour in (0, 7, 13, 22):
            assert _to_server_local(_at(day, hour)) == sc.to_server_local(_at(day, hour))


# --------------------------------------------------------------------------- #
# The clock site the F7/B29/B54 pass ALSO left behind, and it is the one in `BUILT`.
# REPAIRED 2026-07-30 by Session AM (B1200). These tests pinned the defect for AK; they now pin
# the repair, and the historical measurement is retained because it is the size of the correction.
#
# Session AK's first draft of B950 claimed `structural_retest` was the only sleeve in this
# package still reading a raw UTC hour. An adversarial pass refuted it (B971) and the
# refutation measured larger than the repair: `substrate.py` `_utc_hour` returned the raw
# UTC hour and `substrate_engine.py` `_bucket_session` cuts it on the IDENTICAL 8/16
# boundaries — the same pair `structural_retest._session` uses and the same pair
# `wave1_structure_setups_ict.session_id:93-97` mined on the broker-clock archive.
#
# `sub_mid_dn_revert` is backed by that code and it IS in the production generation registry
# (`registry.py:55`, `BUILT`), and `session=ny` is one of its seven cell conditions
# (`substrate.py` `MIDDN_CONDS`). So half its decision bars were tested against the wrong
# session window. AK's own first attempt to dismiss this was ALSO wrong: reasoning on an assumed
# 00/04/08/12/16/20 UTC H4 grid gives no shift at all, but the archive's H4 closes convert to
# UTC 01/02/05/06/09/10/13/14/17/18/21/22 — so the shift is measured, not reasoned.
#
# MEASURED over the archive (`vps-bars-20260727`, 18 of the 20 MIDDN symbols that have bars):
# 185,548 of 370,808 H4 bars — 50.04 % — bucketed differently under the two clocks, entirely at
# UTC close-hours 05, 06, 13, 14, 21 and 22. On the broker grid the three shifted OPENS are
# server 00 (asia, read as ny), 08 (london, read as asia) and 16 (ny, read as london), so the
# unrepaired `session=ny` set was server-hour {20, 00} and the repaired one is {16, 20}.
#
# It was never costing money: the armed `--tags` are crypto/energy_agri/sub_xvol_pullback, and
# `sub_xvol_pullback` is built with `need_hour=False` so it never reads the hour — the last test
# below is what keeps that true. It was one `--tags` change away from mattering, which is the
# hazard `CLAUDE.md` §4 already names ("a book restarted without --tags trades all 32").
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("day,offset", [(SUMMER, 3), (WINTER, 2)], ids=["summer", "winter"])
def test_substrate_buckets_sessions_on_the_server_hour(day, offset):
    from src.components.ultimate_book.sleeves.substrate import _session_hour
    from src.components.ultimate_book.sleeves.substrate_engine import _bucket_session

    # UTC 14 is the one close-hour that crosses the 16:00 boundary in BOTH seasons (13 crosses
    # only at +3). The archive's real H4 closes are 01/02/05/06/09/10/13/14/17/18/21/22 UTC, and
    # 05/06/13/14/21/22 are exactly the hours the measurement found shifted.
    t = _at(day, 14)
    assert _session_hour(t) == 14 + offset       # converted, which is what the rule was mined on
    assert _session_hour(t) == sc.server_hour(t)
    assert _bucket_session(_session_hour(t)) == "ny"        # the bucket it belongs in
    assert _bucket_session(t.hour) == "london"              # what the raw-UTC read gave


@pytest.mark.parametrize("day", [SUMMER, WINTER], ids=["summer", "winter"])
def test_the_three_shifted_h4_opens_are_exactly_the_ones_measured(day):
    """The archive's H4 grid is server 00/04/08/12/16/20; three of the six moved (50.04 %).

    Asserted on the SERVER grid rather than on a UTC grid, because that is the grid the bars are
    actually stamped on and reasoning about the other one is the mistake B971 records.
    """
    from src.components.ultimate_book.sleeves.substrate import _session_hour
    from src.components.ultimate_book.sleeves.substrate_engine import _bucket_session

    offset = 3 if day is SUMMER else 2
    moved, kept = [], []
    for server_open in (0, 4, 8, 12, 16, 20):
        t = day.replace(hour=(server_open - offset) % 24)
        if server_open - offset < 0:                      # the bar belongs to the previous UTC day
            t -= timedelta(days=1)
        assert _session_hour(t) == server_open
        (moved if _bucket_session(server_open) != _bucket_session(t.hour) else kept).append(
            server_open)
    assert moved == [0, 8, 16]
    assert kept == [4, 12, 20]
    # `session=ny` before and after: {20, 00} -> {16, 20}, sharing only server 20.
    ny_now = {h for h in (0, 4, 8, 12, 16, 20) if _bucket_session(h) == "ny"}
    assert ny_now == {16, 20}


def test_the_substrate_boundaries_are_the_same_pair_structural_retest_uses():
    """If these ever diverge, one of the two was changed without the other and the shared lineage
    claim needs re-establishing."""
    from src.components.ultimate_book.sleeves.substrate_engine import _bucket_session

    for h in range(24):
        srs = SRS._session(h)
        sub = _bucket_session(h)
        assert {"Asian": "asia", "London": "london", "NY": "ny"}[srs] == sub


def test_the_armed_clean3_sleeve_does_not_read_the_hour_at_all():
    """Why the repair above cannot move the ARMED book: `sub_xvol_pullback`'s cell has no
    `session` condition, so `need_hour=False` and the session bucket is never consulted for it.

    Behavioural, not a source-string check: the same bars are driven through the armed generator
    at every server hour on the archive's H4 grid AND with `bar_time=None`, and every intent must
    be identical. A clock change that leaked into the armed sleeve would break this.
    """
    from src.components.ultimate_book.sleeves import substrate as SUB

    assert "session" not in SUB.XVOL_CONDS          # the ARMED clean_3 sleeve
    assert SUB.MIDDN_CONDS["session"] == "ny"       # the registered one that does read it

    bars = _xvol_firing_bars()
    day = "2026-07-15"
    base = SUB.generate_sub_xvol_pullback("XAUUSD", bars, day, bar_time=None)
    assert base is not None, "fixture must FIRE, or this test proves nothing"
    for utc_hour in range(24):
        got = SUB.generate_sub_xvol_pullback(
            "XAUUSD", bars, day, bar_time=SUMMER.replace(hour=utc_hour))
        assert got is not None
        assert (got.sleeve, got.symbol, got.direction, got.stop_dist, got.target_dist) == (
            base.sleeve, base.symbol, base.direction, base.stop_dist, base.target_dist)


def test_the_registered_substrate_sleeve_fails_closed_without_a_timestamp():
    """`session=ny` cannot be located without an hour, and guessing one is finding F7."""
    from src.components.ultimate_book.sleeves import substrate as SUB

    bars = _xvol_firing_bars()
    assert SUB.generate_sub_mid_dn_revert("XAUUSD", bars, "2026-07-15", bar_time=None) is None
    assert SUB._session_hour(None) is None
    assert SUB._session_hour("not-a-timestamp") is None


def _xvol_firing_bars():
    """The seeded synthetic series the substrate parity module already proves lands in XVOL_CELL.

    Reused rather than re-crafted: `test_substrate_sleeves._series_xvol(635)` is asserted there to
    produce at least one oracle cell match, so a bespoke fixture here would be a second thing to
    keep true. The prefix is truncated to the first firing bar by the caller's own assertion.
    """
    from tests.ultimate_book.test_substrate_sleeves import _series_xvol
    from src.components.ultimate_book.sleeves import substrate as SUB

    bars, _times = _series_xvol(635)
    for i in range(len(bars) - 1, 209, -1):
        if SUB.generate_sub_xvol_pullback("XAUUSD", bars[: i + 1], "2026-07-15") is not None:
            return bars[: i + 1]
    raise AssertionError("the seeded xvol series no longer fires; fixture and parity test disagree")
