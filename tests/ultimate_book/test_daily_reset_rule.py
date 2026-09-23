"""The daily-loss reset window follows THE ACCOUNT'S rule, not one global clock (B56).

The two firms do not share a rule, and the repo previously used one clock for both:

* **redacted_account** resets at **00:00 server time** — GMT+3 under DST, GMT+2 otherwise
  (help.redacted_account.com/en/articles/8394309-when-does-the-daily-loss-limit-reset-with-redacted_account-cfd).
* **FTMO** resets at **00:00 CE(S)T** (academy.ftmo.com/lesson/maximum-daily-loss/, recorded at
  ``config/profiles/ftmo.yaml:102``) — Central European time, which is *not* its MT5 server clock.
  FTMO's server runs the **US** DST calendar (measured, ``broker_clock.NEW_YORK_PLUS_7``) while
  CE(S)T runs the **EU** one.

Consequence of the old behaviour, and why the direction matters: using server midnight for FTMO
reset the window **early** — 1 h normally, 2 h during the ~4 weeks a year the calendars disagree.
In that gap the governor believed the daily-loss budget was fresh while FTMO was still counting
losses against the previous day, which is the wrong way round for a funded account.
"""
from __future__ import annotations

import tempfile
from datetime import datetime, timedelta, timezone

import pytest
import yaml

from src.components.ultimate_book.governor_state import GovernorStateBuilder
from src.utils.broker_clock import (
    NEW_YORK_PLUS_7,
    UnknownBrokerClockError,
    daily_reset_offset_hours,
    offset_seconds_at_utc,
)

# 2026-03-20 sits inside a disagreement window: US on summer time, EU not yet.
DISAGREE = datetime(2026, 3, 20, 12, tzinfo=timezone.utc)
SUMMER = datetime(2026, 7, 15, 12, tzinfo=timezone.utc)
WINTER = datetime(2026, 1, 15, 12, tzinfo=timezone.utc)


def _builder(tmp, ns, **kw):
    return GovernorStateBuilder(tmp, namespace=ns, daily_reset_offset_hours=3.0, **kw)


# --------------------------------------------------------------------------- #
# The calendar
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("when,expected", [(WINTER, 1.0), (SUMMER, 2.0), (DISAGREE, 1.0)])
def test_prague_is_cet_in_winter_and_cest_in_summer(when, expected):
    assert daily_reset_offset_hours(when, "Europe/Prague") == expected


@pytest.mark.parametrize("alias", ["Europe/Prague", "europe_prague", "CE(S)T", "cet", " CEST "])
def test_the_profile_spelling_resolves(alias):
    """config/profiles/ftmo.yaml declares 'Europe/Prague'; the rule must accept it verbatim."""
    assert daily_reset_offset_hours(DISAGREE, alias) == 1.0


@pytest.mark.parametrize("name", ["server", "broker_server", "mt5_server", None, ""])
def test_server_midnight_returns_none_so_the_caller_uses_the_detected_offset(name):
    assert daily_reset_offset_hours(DISAGREE, name) is None


def test_an_unknown_rule_raises_rather_than_guessing():
    with pytest.raises(UnknownBrokerClockError):
        daily_reset_offset_hours(DISAGREE, "Europe/Atlantis")


def test_the_prague_calendar_is_not_the_server_calendar():
    """If these ever coincide the test is worthless -- assert they genuinely differ."""
    server = offset_seconds_at_utc(DISAGREE, NEW_YORK_PLUS_7) / 3600.0
    prague = daily_reset_offset_hours(DISAGREE, "Europe/Prague")
    assert server == 3.0 and prague == 1.0, "2026-03-20: server UTC+3 (US DST), Prague UTC+1 (EU not yet)"


@pytest.mark.skipif(
    __import__("importlib").util.find_spec("zoneinfo") is None, reason="no zoneinfo"
)
def test_the_arithmetic_prague_rule_matches_zoneinfo_all_year():
    """Computed arithmetically because the live Windows host has no IANA tz database. That is only
    safe if it provably agrees with the real thing wherever the real thing is available."""
    from zoneinfo import ZoneInfo

    try:
        tz = ZoneInfo("Europe/Prague")
    except Exception:  # pragma: no cover - no tzdata installed
        pytest.skip("tzdata not installed")
    day = datetime(2026, 1, 1, 12, tzinfo=timezone.utc)
    while day.year == 2026:
        assert daily_reset_offset_hours(day, "Europe/Prague") == \
            tz.utcoffset(day.replace(tzinfo=None)).total_seconds() / 3600.0, day.date()
        day += timedelta(days=1)


# --------------------------------------------------------------------------- #
# The governor, per account
# --------------------------------------------------------------------------- #

def test_ftmo_and_redacted_account_roll_their_day_at_different_instants():
    tmp = tempfile.mkdtemp()
    ftmo = _builder(tmp, "ftmo_t", reset_rule="Europe/Prague")
    fn = _builder(tmp, "fn_t", offset_provider=lambda: 3.0)          # server midnight
    at = lambda h: DISAGREE.replace(hour=h, minute=30)

    # 21:00 UTC is redacted_account's midnight; FTMO is still on the previous day until 23:00 UTC.
    assert fn.reset_window_date(at(21)) == "2026-03-21"
    assert ftmo.reset_window_date(at(21)) == "2026-03-20"
    assert ftmo.reset_window_date(at(22)) == "2026-03-20"
    assert ftmo.reset_window_date(at(23)) == "2026-03-21"


def test_the_ftmo_window_would_have_been_two_hours_early_before_the_fix():
    """Pins the defect itself: the old behaviour is what `offset_provider` alone produces."""
    tmp = tempfile.mkdtemp()
    old = _builder(tmp, "old_t", offset_provider=lambda: 3.0)
    new = _builder(tmp, "new_t", reset_rule="Europe/Prague", offset_provider=lambda: 3.0)
    boundary = DISAGREE.replace(hour=21, minute=30)
    assert old.reset_window_date(boundary) == "2026-03-21", "old: server midnight, already 'tomorrow'"
    assert new.reset_window_date(boundary) == "2026-03-20", "new: FTMO still counting the old day"
    assert old.reset_window_date(boundary) != new.reset_window_date(boundary)


def test_a_declared_rule_beats_a_detected_offset_that_disagrees():
    """The firm's stated rule is authority; a detected server offset must not override it."""
    tmp = tempfile.mkdtemp()
    b = _builder(tmp, "prec_t", reset_rule="Europe/Prague", offset_provider=lambda: 3.0)
    assert b.reset_window_date(DISAGREE.replace(hour=22)) == "2026-03-20"


def test_an_unknown_rule_falls_back_and_does_not_raise_into_the_decision_path(caplog):
    """A misconfigured rule name must not crash the live decision path -- but it must be LOUD.
    A silent fallback to the wrong reset window is the failure this whole change exists to fix."""
    import logging

    tmp = tempfile.mkdtemp()
    b = _builder(tmp, "bad_t", reset_rule="Europe/Atlantis", offset_provider=lambda: 3.0)
    with caplog.at_level(logging.ERROR, logger="src.components.ultimate_book.governor_state"):
        window = b.reset_window_date(DISAGREE)
    assert window == "2026-03-20"                      # detected offset, not a crash
    messages = [r.getMessage() for r in caplog.records if r.levelno >= logging.ERROR]
    assert any("unknown daily-reset rule" in m for m in messages), messages
    assert any("Europe/Atlantis" in m for m in messages), messages


def test_no_rule_preserves_the_previous_behaviour_exactly():
    """Backward compatibility: accounts whose profile is silent must be unchanged."""
    tmp = tempfile.mkdtemp()
    before = _builder(tmp, "compat_a", offset_provider=lambda: 3.0)
    after = _builder(tmp, "compat_b", offset_provider=lambda: 3.0, reset_rule=None)
    for h in (20, 21, 22, 23):
        at = DISAGREE.replace(hour=h)
        assert before.reset_window_date(at) == after.reset_window_date(at)


# --------------------------------------------------------------------------- #
# The shipped profiles
# --------------------------------------------------------------------------- #

def _find(obj, key):
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for value in obj.values():
            found = _find(value, key)
            if found is not None:
                return found
    return None


@pytest.mark.parametrize("profile_name", [
    "operator_profile",   # THE LIVE ONE -- run_book_supervisor.ps1:86 launches with this
    "ftmo",
])
def test_the_shipped_ftmo_profiles_declare_the_prague_rule(profile_name):
    """If this key is ever removed, FTMO silently reverts to server midnight -- so pin it.

    Both profiles are covered on purpose. `operator_profile` is the one the supervisor
    actually launches, so testing only `ftmo.yaml` would leave the LIVE account unpinned --
    which is exactly the kind of near-miss that makes a green test meaningless.
    """
    profile = yaml.safe_load(open(f"config/profiles/{profile_name}.yaml"))
    assert _find(profile, "prop_safe_selector_daily_reset_timezone") == "Europe/Prague"
    assert "CE(S)T" in str(_find(profile, "daily_reset_time"))


def test_the_live_ftmo_profile_resolves_to_prague_end_to_end():
    """Read the live profile exactly as book_engine does, and check the resolved offset."""
    profile = yaml.safe_load(open("config/profiles/operator_profile.yaml"))
    declared = _find(profile, "prop_safe_selector_daily_reset_timezone")
    assert daily_reset_offset_hours(DISAGREE, declared) == 1.0     # Prague, not the server's +3


def test_the_redacted_account_profile_declares_no_rule_which_means_server_midnight():
    """redacted_account resets at server midnight, so silence is CORRECT here -- not an oversight.
    This test exists so that adding a rule to that profile is a deliberate, reviewed act."""
    profile = yaml.safe_load(open("config/profiles/redacted_account.yaml"))
    assert _find(profile, "prop_safe_selector_daily_reset_timezone") is None


# --------------------------------------------------------------------------- #
# redacted_account's SERVER clock, registered 2026-07-26 on VPS measurement.
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("server", ["redacted_account-Server 2", "redacted_account-Server2", "redacted_account", "FTMO-Server3"])
def test_both_brokers_resolve_to_the_measured_us_calendar(server):
    """Session B refused to resolve redacted_account because its calendar was unmeasured -- correct then.
    Measured on the VPS over 81 weekly session boundaries per broker: the two servers are identical
    across all 81 weeks and all three transitions, every one on a US DST date."""
    from src.utils.broker_clock import resolve_rule

    assert resolve_rule(server).name == "new_york_plus_7"


def test_an_unmeasured_server_still_fails_closed():
    """Registering redacted_account must not turn the registry into a guesser."""
    from src.utils.broker_clock import resolve_rule

    with pytest.raises(UnknownBrokerClockError):
        resolve_rule("SomeOtherBroker-Server1")


@pytest.mark.parametrize("week_open,offset", [
    ("2025-03-03", 2), ("2025-03-10", 3),      # US spring forward 2025-03-09
    ("2025-10-27", 3), ("2025-11-03", 2),      # US fall back 2025-11-02 (EU fell back 2025-10-26)
    ("2026-03-02", 2), ("2026-03-09", 3),      # US spring forward 2026-03-08
])
@pytest.mark.parametrize("server", ["FTMO-Server3", "redacted_account-Server 2"])
def test_the_rule_reproduces_every_vps_measured_transition(server, week_open, offset):
    """2025-10-27 is the decisive week: the EU had already fallen back, both servers still read +3.
    An EU-calendar rule would say +2 there and be wrong for both brokers."""
    from src.utils.broker_clock import resolve_rule

    when = datetime.fromisoformat(week_open + "T12:00:00+00:00")
    assert offset_seconds_at_utc(when, resolve_rule(server)) / 3600.0 == offset


def test_the_server_clock_and_the_reset_rule_stay_separate_questions():
    """redacted_account's SERVER is now registered; its daily-RESET rule is still server midnight.
    Registering the former must not accidentally give it a reset calendar."""
    assert daily_reset_offset_hours(DISAGREE, None) is None


# ---------------------------------------------------------------------------------------------
# The DST seams. Added 2026-07-29 (Session AC, B566) after a refuter measured the window START
# moving by an hour twice a year — in the SHORTENING direction at the autumn seam, which drops an
# hour of realized loss out of the daily budget. Same direction as the defect B56 exists to fix.
# ---------------------------------------------------------------------------------------------

#: (now, expected window start). Each `now` sits just after an EU DST transition (01:00 UTC), when
#: the offset at `now` differs from the offset that was in force at the local midnight the window
#: began at. Subtracting the offset at `now` -- which is what the code did -- lands an hour out.
_EU_SEAMS = [
    # spring forward 2026-03-29 01:00Z (CET +1 -> CEST +2). Midnight was CET.
    ("2026-03-29T02:00:00+00:00", "2026-03-28T23:00:00+00:00"),
    ("2026-03-29T12:00:00+00:00", "2026-03-28T23:00:00+00:00"),
    # fall back 2026-10-25 01:00Z (CEST +2 -> CET +1). Midnight was CEST.
    ("2026-10-25T02:00:00+00:00", "2026-10-24T22:00:00+00:00"),
    ("2026-10-25T12:00:00+00:00", "2026-10-24T22:00:00+00:00"),
    ("2027-03-28T02:00:00+00:00", "2027-03-27T23:00:00+00:00"),
    ("2027-10-31T02:00:00+00:00", "2027-10-30T22:00:00+00:00"),
]


@pytest.mark.parametrize("now_iso,expected", _EU_SEAMS)
def test_the_reset_window_start_is_right_across_an_eu_dst_seam(now_iso, expected, tmp_path):
    builder = GovernorStateBuilder(
        str(tmp_path), namespace="operator_profile",
        daily_reset_offset_hours=3.0, offset_provider=lambda: 3.0,
        reset_rule="Europe/Prague")
    got = builder._reset_window_start_utc(datetime.fromisoformat(now_iso))
    assert got.astimezone(timezone.utc) == datetime.fromisoformat(expected)


def test_the_reset_window_start_is_always_local_midnight_and_never_moves_backwards(tmp_path):
    """Hourly over two full years, including all four EU seams.

    Two properties, because the seam defect broke the first and a naive repair could break the
    second: the window must begin at exactly 00:00 CE(S)T, and as `now` advances the window start
    must never go backwards (a backwards step would re-open a window that had already closed, and
    the day-start balance anchor keys on it).
    """
    from src.utils.broker_clock import EUROPE_PRAGUE

    builder = GovernorStateBuilder(
        str(tmp_path), namespace="operator_profile",
        daily_reset_offset_hours=3.0, offset_provider=lambda: 3.0,
        reset_rule="Europe/Prague")
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    end = datetime(2028, 1, 1, tzinfo=timezone.utc)
    previous = None
    off_by_hours, went_backwards = [], []
    while now < end:
        start = builder._reset_window_start_utc(now).astimezone(timezone.utc)
        offset = offset_seconds_at_utc(start, EUROPE_PRAGUE) / 3600.0
        local = start + timedelta(hours=offset)
        if (local.hour, local.minute, local.second) != (0, 0, 0):
            off_by_hours.append((now.isoformat(), local.isoformat()))
        if previous is not None and start < previous:
            went_backwards.append((now.isoformat(), previous.isoformat(), start.isoformat()))
        previous = start
        now += timedelta(hours=1)
    assert not off_by_hours, f"{len(off_by_hours)} probes not at 00:00 CE(S)T, first: {off_by_hours[:3]}"
    assert not went_backwards, f"{len(went_backwards)} backwards steps, first: {went_backwards[:3]}"


def test_the_seam_repair_does_not_touch_the_detected_offset_path(tmp_path):
    """redacted_account resolves through ``offset_provider``, which takes no instant, so the correction
    pass is a no-op there by construction. Pinned so a later change to the provider signature
    cannot silently start moving redacted_account's window."""
    builder = GovernorStateBuilder(
        str(tmp_path), namespace="redacted_account_live_bee34003",
        daily_reset_offset_hours=3.0, offset_provider=lambda: 3.0)
    for iso in ("2026-10-25T02:00:00+00:00", "2026-03-29T02:00:00+00:00",
                "2026-07-15T23:30:00+00:00"):
        now = datetime.fromisoformat(iso)
        start = builder._reset_window_start_utc(now).astimezone(timezone.utc)
        assert (start + timedelta(hours=3)).hour == 0
        assert (now - start).total_seconds() < 24 * 3600
