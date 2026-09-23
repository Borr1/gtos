"""Behavioral pins for the Q2 broker-wall-clock gate."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.research_infra.event_clock_gate import (
    DEFAULT_REJECT_HOURS,
    EventClockGate,
    broker_hour,
)
from src.utils.broker_clock import (
    NEW_YORK_PLUS_7,
    UnknownBrokerClockError,
    fixed_offset_rule,
    utc_to_broker_naive,
)

SERVER = "FTMO-Server3"


def _utc(year, month, day, hour=0, minute=0):
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


class _HardcodedUtcGate:
    def __init__(self, hours=DEFAULT_REJECT_HOURS):
        self.hours = frozenset(hours)

    def rejects(self, instant):
        return instant.astimezone(timezone.utc).hour in self.hours


def test_servers_resolve_only_to_the_measured_rule():
    assert EventClockGate.for_server(SERVER).rule is NEW_YORK_PLUS_7
    assert EventClockGate.for_server("redacted_account-Server 2").rule is NEW_YORK_PLUS_7
    with pytest.raises(UnknownBrokerClockError):
        EventClockGate.for_server("SomeBroker-Server9")
    with pytest.raises(UnknownBrokerClockError):
        EventClockGate.for_server(None)


@pytest.mark.parametrize("hours", [{24}, {-1}, {True}, {21.0}, {21.9}, {"21"}])
def test_reject_hours_are_strict_literal_integers(hours):
    with pytest.raises(ValueError):
        EventClockGate.for_server(SERVER, reject_hours=hours)


def test_naive_datetime_is_refused_instead_of_silently_called_utc():
    gate = EventClockGate.for_server(SERVER)
    with pytest.raises(ValueError, match="timezone-aware"):
        gate.rejects(datetime(2026, 5, 12, 21, 30))


def test_gate_is_a_thin_reader_of_broker_clock_for_a_full_year_stride():
    gate = EventClockGate.for_server(SERVER)
    instant = _utc(2026, 1, 1)
    end = _utc(2027, 1, 1)
    while instant < end:
        wall_hour = utc_to_broker_naive(instant, NEW_YORK_PLUS_7).hour
        assert gate.broker_hour(instant) == wall_hour
        assert gate.rejects(instant) == (wall_hour in {21, 22, 23, 0})
        instant += timedelta(hours=7, minutes=13)


def test_broker_midnight_moves_between_winter_and_summer_utc():
    assert broker_hour(_utc(2026, 2, 11, 22), NEW_YORK_PLUS_7) == 0
    assert broker_hour(_utc(2026, 2, 11, 21), NEW_YORK_PLUS_7) == 23
    assert broker_hour(_utc(2026, 7, 15, 21), NEW_YORK_PLUS_7) == 0
    assert broker_hour(_utc(2026, 7, 15, 22), NEW_YORK_PLUS_7) == 1


@pytest.mark.parametrize(
    "winter_day,summer_day",
    [
        (_utc(2026, 3, 5), _utc(2026, 3, 12)),
        (_utc(2026, 11, 4), _utc(2026, 10, 28)),
    ],
)
def test_rejected_utc_hours_move_on_both_us_dst_transitions(winter_day, summer_day):
    gate = EventClockGate.for_server(SERVER)
    assert gate.utc_hours_on(winter_day) == [19, 20, 21, 22]
    assert gate.utc_hours_on(summer_day) == [18, 19, 20, 21]


def test_us_eu_disagreement_date_changes_the_boundary_verdict():
    gate = EventClockGate.for_server(SERVER)
    eu_wrong = EventClockGate(
        fixed_offset_rule(2.0, evidence="test-only EU winter proxy"),
        frozenset(DEFAULT_REJECT_HOURS),
    )
    boundary = _utc(2026, 3, 20, 18)
    assert gate.broker_hour(boundary) == 21 and gate.rejects(boundary)
    assert eu_wrong.broker_hour(boundary) == 20 and not eu_wrong.rejects(boundary)


@pytest.mark.parametrize(
    "instant,measured,hardcoded",
    [
        (_utc(2026, 2, 11, 19), True, False),
        (_utc(2026, 2, 11, 23), False, True),
        (_utc(2026, 7, 15, 18), True, False),
        (_utc(2026, 7, 15, 21), True, True),
    ],
)
def test_hardcoded_utc_gate_disagrees_with_measured_gate(instant, measured, hardcoded):
    assert EventClockGate.for_server(SERVER).rejects(instant) is measured
    assert _HardcodedUtcGate().rejects(instant) is hardcoded


@pytest.mark.parametrize(
    "hours,expected_disagreements",
    [
        ({21, 22, 23, 0}, 1936),
        ({19, 20, 21, 22}, 476),
        ({18, 19, 20, 21}, 254),
    ],
)
def test_every_constant_utc_hour_set_is_wrong_somewhere(hours, expected_disagreements):
    gate = EventClockGate.for_server(SERVER)
    wrong = _HardcodedUtcGate(hours)
    instant, end = _utc(2026, 1, 1), _utc(2027, 1, 1)
    disagreements = 0
    while instant < end:
        disagreements += gate.rejects(instant) != wrong.rejects(instant)
        instant += timedelta(hours=1)
    assert disagreements == expected_disagreements


def test_receipt_description_carries_rule_and_never_a_utc_hour_set():
    description = EventClockGate.for_server(SERVER).describe()
    assert description["reject_hours_broker_wall_clock"] == [0, 21, 22, 23]
    assert description["hardcoded_utc_hours"] is None
    assert description["broker_clock_rule"] == "new_york_plus_7"


def test_vector_mask_matches_elementwise_calls():
    gate = EventClockGate.for_server(SERVER)
    instants = [_utc(2026, 2, 11, hour) for hour in range(24)]
    assert gate.reject_mask(instants) == [gate.rejects(instant) for instant in instants]
    assert sum(gate.reject_mask(instants)) == 4
