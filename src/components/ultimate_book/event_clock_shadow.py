"""Default-off, observation-only Q2 transfer for exact live H4 close events.

Production ``decision_bar_iso`` is the decision bar's **open** timestamp.  The
event that Q2 priced is its close, so the classifier derives
``bar_open_utc + timeframe`` and then converts that true-UTC instant with the
measured broker clock.  A per-process latch keys the result to the bar identity;
cycle retries therefore cannot reclassify the event from a later wall clock.

Nothing in this module admits, rejects, sizes, places, modifies, or closes an
order.  ``shadow_would_reject`` is telemetry only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Callable

from src.utils.broker_clock import UnknownBrokerClockError, utc_to_broker_naive

TF_H4 = 16388
H4_MINUTES = 240
H4_BROKER_CLOSE_HOURS = frozenset({0, 4, 8, 12, 16, 20})

__all__ = [
    "ExactH4CloseClassifier",
    "H4EventClockShadowLatch",
    "H4_BROKER_CLOSE_HOURS",
    "H4_MINUTES",
    "TF_H4",
]


def _aware_utc(value: datetime | str, *, field_name: str) -> datetime:
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"{field_name} is not a valid ISO datetime") from exc
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be datetime or ISO string")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware true UTC")
    return value.astimezone(timezone.utc)


def _h4_timeframe(value: int) -> int:
    if type(value) is not int or value != TF_H4:
        raise ValueError(f"timeframe must be MT5 H4 ({TF_H4}), got {value!r}")
    return value


@dataclass(frozen=True)
class ExactH4CloseClassifier:
    """Pure classifier for one measured server rule."""

    server: str
    gate: EventClockGate

    @classmethod
    def for_server(cls, server: str | None) -> "ExactH4CloseClassifier":
        # EventClockGate.for_server is intentionally allowed to raise
        # UnknownBrokerClockError.  A guessed server clock cannot emit an admit.
        from src.research_infra.event_clock_gate import EventClockGate

        gate = EventClockGate.for_server(server)
        return cls(server=str(server), gate=gate)

    def classify(
        self,
        *,
        decision_bar_iso: datetime | str,
        timeframe: int,
    ) -> dict[str, object]:
        """Classify an H4 bar identity; ``decision_bar_iso`` means bar OPEN."""
        _h4_timeframe(timeframe)
        bar_open = _aware_utc(decision_bar_iso, field_name="decision_bar_iso")
        event_close = bar_open + timedelta(minutes=H4_MINUTES)
        broker_wall = utc_to_broker_naive(event_close, self.gate.rule)
        exact_grid_close = (
            broker_wall.hour in H4_BROKER_CLOSE_HOURS
            and broker_wall.minute == 0
            and broker_wall.second == 0
            and broker_wall.microsecond == 0
        )
        q2_hour_rejects = self.gate.rejects(event_close)
        exact_q2_event = bool(exact_grid_close and q2_hour_rejects)
        if not exact_grid_close:
            reason = "not_exact_h4_grid_close"
        elif exact_q2_event:
            reason = "exact_h4_close_in_q2_reject_window"
        else:
            reason = "exact_h4_close_outside_q2_reject_window"
        payload: dict[str, object] = {
            "schema": "gtos.q2_exact_h4_event_shadow.v1",
            "classification_status": "classified",
            "admission_effect": False,
            "server": self.server,
            "decision_bar_iso": bar_open.isoformat(),
            "decision_bar_semantics": "bar_open_utc",
            "timeframe": timeframe,
            "timeframe_minutes": H4_MINUTES,
            "event_close_utc": event_close.isoformat(),
            "event_close_derivation": "decision_bar_iso_plus_timeframe",
            "event_close_broker_wall": broker_wall.isoformat(),
            "broker_hour": broker_wall.hour,
            "broker_minute": broker_wall.minute,
            "exact_h4_grid_close": exact_grid_close,
            "q2_hour_gate_rejects": q2_hour_rejects,
            "shadow_would_reject": exact_q2_event,
            "reason": reason,
        }
        payload.update(self.gate.describe())
        return payload


@dataclass
class H4EventClockShadowLatch:
    """Latch Q2 shadow classifications to ``(timeframe, bar-open UTC)``.

    Unknown servers are latched as ``clock_unavailable_fail_closed`` with no
    hypothetical verdict.  The surrounding book keeps running because this
    observer has no admission authority, while the classification itself never
    guesses or degrades to an admit.
    """

    server_resolver: Callable[[], str | None]
    _latched: dict[tuple[int, str], dict[str, object]] = field(default_factory=dict)

    def observe(
        self,
        *,
        decision_bar_iso: datetime | str,
        timeframe: int,
        observed_at_utc: datetime,
    ) -> dict[str, object]:
        _h4_timeframe(timeframe)
        bar_open = _aware_utc(decision_bar_iso, field_name="decision_bar_iso")
        observed_at = _aware_utc(observed_at_utc, field_name="observed_at_utc")
        key = (timeframe, bar_open.isoformat())
        latch_hit = key in self._latched
        if not latch_hit:
            try:
                server = self.server_resolver()
                classifier = ExactH4CloseClassifier.for_server(server)
                classification = classifier.classify(
                    decision_bar_iso=bar_open,
                    timeframe=timeframe,
                )
            except UnknownBrokerClockError as exc:
                classification = {
                    "schema": "gtos.q2_exact_h4_event_shadow.v1",
                    "classification_status": "clock_unavailable_fail_closed",
                    "admission_effect": False,
                    "server": None if "server" not in locals() else server,
                    "decision_bar_iso": bar_open.isoformat(),
                    "decision_bar_semantics": "bar_open_utc",
                    "timeframe": timeframe,
                    "timeframe_minutes": H4_MINUTES,
                    "event_close_utc": (bar_open + timedelta(minutes=H4_MINUTES)).isoformat(),
                    "event_close_derivation": "decision_bar_iso_plus_timeframe",
                    "broker_hour": None,
                    "broker_minute": None,
                    "exact_h4_grid_close": None,
                    "q2_hour_gate_rejects": None,
                    "shadow_would_reject": None,
                    "reason": "unknown_broker_clock",
                    "error": str(exc),
                }
            classification["latched_at_utc"] = observed_at.isoformat()
            self._latched[key] = classification

        out = dict(self._latched[key])
        out.update(
            {
                "latch_key": f"{timeframe}:{bar_open.isoformat()}",
                "latch_hit": latch_hit,
                "observed_at_utc": observed_at.isoformat(),
            }
        )
        return out

    @property
    def latch_size(self) -> int:
        return len(self._latched)
