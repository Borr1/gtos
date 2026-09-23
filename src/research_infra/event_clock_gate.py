"""DST-correct broker-wall-clock classification for the Q2 event window.

Q2 is defined on broker wall hours, never on a constant UTC-hour set.  Both
registered live servers use the measured ``America/New_York + 7 h`` rule in
``src.utils.broker_clock``.  This module is deliberately policy-free: it only
classifies an aware true-UTC instant and carries no live authority.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.utils.broker_clock import BrokerClockRule, resolve_rule, utc_to_broker_naive

__all__ = ["DEFAULT_REJECT_HOURS", "EventClockGate", "broker_hour"]


DEFAULT_REJECT_HOURS: tuple[int, ...] = (21, 22, 23, 0)


def _as_aware_utc(instant: datetime) -> datetime:
    """Return ``instant`` in UTC, refusing timestamps whose basis is unstated."""
    if not isinstance(instant, datetime):
        raise TypeError(f"instant must be datetime, got {type(instant).__name__}")
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise ValueError("instant must be timezone-aware true UTC; naive timestamps are refused")
    return instant.astimezone(timezone.utc)


def broker_hour(instant_utc: datetime, rule: BrokerClockRule) -> int:
    """Broker wall-clock hour (0..23) of one aware true-UTC instant."""
    return utc_to_broker_naive(_as_aware_utc(instant_utc), rule).hour


@dataclass(frozen=True)
class EventClockGate:
    """Classify the measured Q2 broker-hour window.

    ``for_server`` is the production constructor.  It inherits broker-clock's
    fail-closed behavior for missing or unregistered MT5 server names.
    """

    rule: BrokerClockRule
    reject_hours: frozenset[int] = field(
        default_factory=lambda: frozenset(DEFAULT_REJECT_HOURS)
    )

    def __post_init__(self) -> None:
        bad = [
            value
            for value in self.reject_hours
            if type(value) is not int or not 0 <= value <= 23
        ]
        if bad:
            raise ValueError(
                "reject_hours must be literal integers in 0..23; "
                f"got {bad!r}"
            )

    @classmethod
    def for_server(
        cls,
        server: str | None,
        reject_hours: Iterable[int] = DEFAULT_REJECT_HOURS,
    ) -> "EventClockGate":
        """Resolve a measured server rule without coercing malformed hour values."""
        return cls(rule=resolve_rule(server), reject_hours=frozenset(reject_hours))

    def broker_hour(self, instant_utc: datetime) -> int:
        return broker_hour(instant_utc, self.rule)

    def rejects(self, instant_utc: datetime) -> bool:
        return self.broker_hour(instant_utc) in self.reject_hours

    def admits(self, instant_utc: datetime) -> bool:
        return not self.rejects(instant_utc)

    def reject_mask(self, instants_utc: Sequence[datetime]) -> list[bool]:
        return [self.rejects(instant) for instant in instants_utc]

    def describe(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "gate": "event_clock_reject_broker_hours",
            "reject_hours_broker_wall_clock": sorted(self.reject_hours),
            "clock_basis": "broker_wall_clock",
            "hardcoded_utc_hours": None,
        }
        payload.update(self.rule.provenance())
        return payload

    def utc_hours_on(self, day_utc: datetime) -> list[int]:
        """Diagnostic UTC-hour projection for one date; never a runtime rule."""
        base = _as_aware_utc(day_utc).replace(minute=0, second=0, microsecond=0)
        return [hour for hour in range(24) if self.rejects(base.replace(hour=hour))]
