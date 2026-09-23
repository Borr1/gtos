"""Pure, default-off exit-overlay replay primitives.

This module deliberately has no runtime integration, broker imports, config
reads, or activation surface.  It replays an already-recorded entry over a
source-bound signed-R path for research and training-lane diagnostics only.

The common envelope is a -1R hard stop, +2R hard target, and a 120-minute
terminal mark.  A protocol cell may replace the current giveback rule with one
break-even, partial-harvest, giveback, time-box, or partial-plus-break-even
alternative.  Costs are charged once, in full, after weighted partial-return
accounting.

Time-box ownership is temporal.  A target observed at a strictly earlier
timestamp wins; a target and executable deadline observation at the same tick
or M1 timestamp belong to the time box.  The retained hard target still caps a
favourable deadline gap, so a quote beyond +2R closes as ``time_box`` at +2R.
"""

from __future__ import annotations

import datetime as dt
import math
import random
from dataclasses import dataclass, replace
from typing import Any, Iterable, Mapping, Sequence


MICROSECONDS_PER_MINUTE = 60_000_000
SUPPORTED_KINDS = frozenset(
    {
        "identity",
        "break_even",
        "partial_harvest",
        "tighter_giveback",
        "time_box",
        "partial_then_break_even",
    }
)


class ExitOverlayError(ValueError):
    """Fail-closed protocol, geometry, or path error."""


@dataclass(frozen=True)
class ExitOverlaySpec:
    """One predeclared, research-only exit-overlay cell."""

    variant_id: str
    kind: str
    trigger_r: float | None = None
    partial_fraction: float = 0.0
    giveback_gap_r: float | None = None
    move_stop_to_break_even: bool = False
    time_box_minutes: int | None = None
    hard_stop_r: float = -1.0
    hard_target_r: float = 2.0
    horizon_minutes: int = 120

    @classmethod
    def from_protocol_cell(
        cls,
        cell: Mapping[str, Any],
        *,
        identity_trigger_r: float = 1.0,
        identity_gap_r: float = 0.4,
    ) -> "ExitOverlaySpec":
        variant_id = str(cell.get("id") or "").strip()
        kind = str(cell.get("kind") or "").strip()
        if not variant_id:
            raise ExitOverlayError("overlay_variant_id_missing")
        if kind not in SUPPORTED_KINDS:
            raise ExitOverlayError(f"overlay_kind_unsupported:{kind}")

        trigger: float | None = None
        fraction = 0.0
        gap: float | None = None
        move_to_be = False
        time_box: int | None = None
        if kind == "identity":
            trigger = float(identity_trigger_r)
            gap = float(identity_gap_r)
        elif kind == "break_even":
            trigger = _required_float(cell, "trigger_r")
            move_to_be = True
        elif kind == "partial_harvest":
            trigger = _required_float(cell, "trigger_r")
            fraction = _required_float(cell, "fraction")
        elif kind == "tighter_giveback":
            trigger = _required_float(cell, "trigger_r")
            gap = _required_float(cell, "giveback_gap_r")
        elif kind == "time_box":
            time_box = _required_int(cell, "minutes")
        elif kind == "partial_then_break_even":
            trigger = _required_float(cell, "trigger_r")
            fraction = _required_float(cell, "fraction")
            move_to_be = True

        spec = cls(
            variant_id=variant_id,
            kind=kind,
            trigger_r=trigger,
            partial_fraction=fraction,
            giveback_gap_r=gap,
            move_stop_to_break_even=move_to_be,
            time_box_minutes=time_box,
        )
        spec.validate()
        return spec

    def validate(self) -> None:
        if self.kind not in SUPPORTED_KINDS:
            raise ExitOverlayError(f"overlay_kind_unsupported:{self.kind}")
        if not self.variant_id:
            raise ExitOverlayError("overlay_variant_id_missing")
        if not self.hard_stop_r < 0 < self.hard_target_r:
            raise ExitOverlayError("overlay_common_envelope_invalid")
        if self.horizon_minutes <= 0:
            raise ExitOverlayError("overlay_horizon_invalid")
        if self.trigger_r is not None and not 0 < self.trigger_r < self.hard_target_r:
            raise ExitOverlayError("overlay_trigger_outside_common_envelope")
        if not 0.0 <= self.partial_fraction < 1.0:
            raise ExitOverlayError("overlay_partial_fraction_invalid")
        if self.partial_fraction and self.trigger_r is None:
            raise ExitOverlayError("overlay_partial_trigger_missing")
        if self.giveback_gap_r is not None:
            if self.trigger_r is None or self.giveback_gap_r <= 0:
                raise ExitOverlayError("overlay_giveback_geometry_invalid")
        if self.move_stop_to_break_even and self.trigger_r is None:
            raise ExitOverlayError("overlay_break_even_trigger_missing")
        if self.time_box_minutes is not None and not (
            0 < self.time_box_minutes <= self.horizon_minutes
        ):
            raise ExitOverlayError("overlay_time_box_invalid")
        shape = (
            self.trigger_r is not None,
            self.partial_fraction > 0.0,
            self.giveback_gap_r is not None,
            self.move_stop_to_break_even,
            self.time_box_minutes is not None,
        )
        expected_shape = {
            "identity": (True, False, True, False, False),
            "break_even": (True, False, False, True, False),
            "partial_harvest": (True, True, False, False, False),
            "tighter_giveback": (True, False, True, False, False),
            "time_box": (False, False, False, False, True),
            "partial_then_break_even": (True, True, False, True, False),
        }[self.kind]
        if shape != expected_shape:
            raise ExitOverlayError(
                f"overlay_kind_shape_invalid:{self.kind}:{shape}"
            )


@dataclass(frozen=True)
class ExitPathPoint:
    """One executable signed-R observation.

    ``deadline_eligible`` is true for every ordered tick and only for the close
    point of an M1 bar.  This preserves the protocol's different time-box
    semantics without inventing an intrabar timestamp.
    """

    time_us: int
    signed_r: float
    deadline_eligible: bool
    source_index: int


@dataclass(frozen=True)
class SignedM1Bar:
    """One side-normalized M1 bar in signed R."""

    time_us: int
    open_r: float
    high_r: float
    low_r: float
    close_r: float
    source_index: int


@dataclass(frozen=True)
class ExitOverlayReplay:
    variant_id: str
    status: str
    gross_r: float | None
    cost_r: float
    net_r: float | None
    exit_reason: str
    exit_time_us: int | None
    exit_source_index: int | None
    exit_r_on_remaining: float | None
    partial_realized_r: float
    remaining_fraction: float
    mfe_r: float | None
    protective_floor_r: float | None
    trigger_touched: bool
    source_mode: str
    ambiguity: bool = False


@dataclass(frozen=True)
class M1ConservativeReplay:
    """Lower-return result across the two admissible M1 extrema orderings."""

    selected: ExitOverlayReplay
    open_high_low_close: ExitOverlayReplay
    open_low_high_close: ExitOverlayReplay
    outcomes_differ: bool


def _required_float(cell: Mapping[str, Any], key: str) -> float:
    try:
        value = float(cell[key])
    except (KeyError, TypeError, ValueError) as exc:
        raise ExitOverlayError(f"overlay_cell_float_invalid:{key}") from exc
    if not math.isfinite(value):
        raise ExitOverlayError(f"overlay_cell_float_nonfinite:{key}")
    return value


def _required_int(cell: Mapping[str, Any], key: str) -> int:
    try:
        value = int(cell[key])
    except (KeyError, TypeError, ValueError) as exc:
        raise ExitOverlayError(f"overlay_cell_int_invalid:{key}") from exc
    return value


def parse_utc_us(value: Any) -> int:
    """Parse an aware ISO timestamp to integer epoch microseconds."""

    text = str(value or "").strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = dt.datetime.fromisoformat(text)
    except ValueError as exc:
        raise ExitOverlayError(f"overlay_timestamp_invalid:{value}") from exc
    if parsed.tzinfo is None:
        raise ExitOverlayError(f"overlay_timestamp_naive:{value}")
    return int(round(parsed.astimezone(dt.timezone.utc).timestamp() * 1_000_000))


def true_utc_tick_time_us(row: Mapping[str, Any]) -> int:
    """Return an explicit true-UTC tick timestamp, never a broker epoch.

    Rematerialized lane rows retain raw ``time_msc`` for provenance even when
    that integer encodes broker wall time.  Only the converted textual UTC
    fields are eligible here; multiple supplied fields must agree exactly.
    """

    supplied = [
        (key, row.get(key))
        for key in ("ts_utc", "time_utc", "time")
        if row.get(key) not in (None, "")
    ]
    if not supplied:
        raise ExitOverlayError("overlay_tick_true_utc_timestamp_missing")
    parsed = [(key, parse_utc_us(value)) for key, value in supplied]
    if any(value != parsed[0][1] for _, value in parsed[1:]):
        raise ExitOverlayError("overlay_tick_true_utc_timestamp_disagreement")
    return parsed[0][1]


def _close_replay(
    *,
    spec: ExitOverlaySpec,
    cost_r: float,
    exit_reason: str,
    point: ExitPathPoint,
    exit_r: float,
    partial_realized_r: float,
    remaining_fraction: float,
    mfe_r: float,
    protective_floor_r: float,
    trigger_touched: bool,
    source_mode: str,
) -> ExitOverlayReplay:
    gross = partial_realized_r + remaining_fraction * exit_r
    return ExitOverlayReplay(
        variant_id=spec.variant_id,
        status="REPLAYED",
        gross_r=float(gross),
        cost_r=float(cost_r),
        net_r=float(gross - cost_r),
        exit_reason=exit_reason,
        exit_time_us=point.time_us,
        exit_source_index=point.source_index,
        exit_r_on_remaining=float(exit_r),
        partial_realized_r=float(partial_realized_r),
        remaining_fraction=float(remaining_fraction),
        mfe_r=float(mfe_r),
        protective_floor_r=float(protective_floor_r),
        trigger_touched=bool(trigger_touched),
        source_mode=source_mode,
    )


def replay_signed_path(
    spec: ExitOverlaySpec,
    points: Sequence[ExitPathPoint] | Iterable[ExitPathPoint],
    *,
    decision_time_us: int,
    cost_r: float,
    source_mode: str,
) -> ExitOverlayReplay:
    """Replay one cell over an ordered executable signed-R path."""

    spec.validate()
    try:
        charged_cost = float(cost_r)
    except (TypeError, ValueError) as exc:
        raise ExitOverlayError("overlay_cost_invalid") from exc
    if not math.isfinite(charged_cost) or charged_cost < 0:
        raise ExitOverlayError("overlay_cost_invalid")

    path = tuple(points)
    if not path:
        return ExitOverlayReplay(
            variant_id=spec.variant_id,
            status="SOURCE_GAP",
            gross_r=None,
            cost_r=charged_cost,
            net_r=None,
            exit_reason="source_gap_no_postdecision_path",
            exit_time_us=None,
            exit_source_index=None,
            exit_r_on_remaining=None,
            partial_realized_r=0.0,
            remaining_fraction=1.0,
            mfe_r=None,
            protective_floor_r=None,
            trigger_touched=False,
            source_mode=source_mode,
        )

    previous_time = decision_time_us
    for point in path:
        if point.time_us < previous_time:
            raise ExitOverlayError("overlay_path_time_not_monotonic")
        if point.time_us <= decision_time_us:
            raise ExitOverlayError("overlay_path_not_strictly_postdecision")
        if not math.isfinite(float(point.signed_r)):
            raise ExitOverlayError("overlay_path_nonfinite")
        previous_time = point.time_us

    remaining_fraction = 1.0
    partial_realized_r = 0.0
    protective_floor = float(spec.hard_stop_r)
    running_mfe = 0.0
    trigger_touched = False
    partial_done = False
    giveback_armed = False
    deadline = (
        decision_time_us + spec.time_box_minutes * MICROSECONDS_PER_MINUTE
        if spec.time_box_minutes is not None
        else None
    )
    deadline_time_us = (
        next(
            (
                point.time_us
                for point in path
                if point.deadline_eligible and point.time_us >= deadline
            ),
            None,
        )
        if deadline is not None
        else None
    )

    for point in path:
        signed_r = float(point.signed_r)

        # Existing protective orders have priority over all new actions.
        if signed_r <= spec.hard_stop_r:
            return _close_replay(
                spec=spec,
                cost_r=charged_cost,
                exit_reason="hard_stop",
                point=point,
                exit_r=spec.hard_stop_r,
                partial_realized_r=partial_realized_r,
                remaining_fraction=remaining_fraction,
                mfe_r=running_mfe,
                protective_floor_r=protective_floor,
                trigger_touched=trigger_touched,
                source_mode=source_mode,
            )
        if protective_floor > spec.hard_stop_r and signed_r <= protective_floor:
            return _close_replay(
                spec=spec,
                cost_r=charged_cost,
                exit_reason=(
                    "break_even_floor"
                    if abs(protective_floor) <= 1e-12
                    else "giveback_floor"
                ),
                point=point,
                exit_r=protective_floor,
                partial_realized_r=partial_realized_r,
                remaining_fraction=remaining_fraction,
                mfe_r=running_mfe,
                protective_floor_r=protective_floor,
                trigger_touched=trigger_touched,
                source_mode=source_mode,
            )

        # Tick deadlines apply at the first tick at/after the deadline; M1
        # deadlines are marked only on the corresponding bar close.  A retained
        # resting target cannot pay more than its declared level when that
        # executable observation gaps through it.
        if (
            deadline is not None
            and point.deadline_eligible
            and point.time_us >= deadline
        ):
            return _close_replay(
                spec=spec,
                cost_r=charged_cost,
                exit_reason="time_box",
                point=point,
                exit_r=min(signed_r, float(spec.hard_target_r)),
                partial_realized_r=partial_realized_r,
                remaining_fraction=remaining_fraction,
                mfe_r=max(running_mfe, signed_r),
                protective_floor_r=protective_floor,
                trigger_touched=trigger_touched,
                source_mode=source_mode,
            )

        running_mfe = max(running_mfe, signed_r)
        newly_triggered = (
            spec.trigger_r is not None
            and not trigger_touched
            and signed_r >= spec.trigger_r
        )
        if newly_triggered:
            trigger_touched = True
            if spec.partial_fraction and not partial_done:
                # The declared fraction is of original size and is harvested
                # at the trigger, never at a favorable observation overshoot.
                partial_realized_r += spec.partial_fraction * float(spec.trigger_r)
                remaining_fraction -= spec.partial_fraction
                partial_done = True
            if spec.move_stop_to_break_even:
                protective_floor = max(protective_floor, 0.0)
            if spec.giveback_gap_r is not None:
                giveback_armed = True

        # A favorable gap can cross a partial trigger and the target in one
        # observation.  Charging the partial at its lower trigger first is the
        # conservative executable ordering.
        if (
            signed_r >= spec.hard_target_r
            and point.time_us != deadline_time_us
        ):
            return _close_replay(
                spec=spec,
                cost_r=charged_cost,
                exit_reason="hard_target",
                point=point,
                exit_r=spec.hard_target_r,
                partial_realized_r=partial_realized_r,
                remaining_fraction=remaining_fraction,
                mfe_r=running_mfe,
                protective_floor_r=protective_floor,
                trigger_touched=trigger_touched,
                source_mode=source_mode,
            )

        if giveback_armed and spec.giveback_gap_r is not None:
            protective_floor = max(
                protective_floor,
                running_mfe - float(spec.giveback_gap_r),
            )

    last = path[-1]
    return _close_replay(
        spec=spec,
        cost_r=charged_cost,
        exit_reason="horizon_terminal_mark",
        point=last,
        exit_r=float(last.signed_r),
        partial_realized_r=partial_realized_r,
        remaining_fraction=remaining_fraction,
        mfe_r=running_mfe,
        protective_floor_r=protective_floor,
        trigger_touched=trigger_touched,
        source_mode=source_mode,
    )


def signed_m1_bars(
    rows: Sequence[Mapping[str, Any]] | Iterable[Mapping[str, Any]],
    *,
    entry_price: float,
    stop_loss: float,
    side: str,
) -> tuple[SignedM1Bar, ...]:
    """Convert raw OHLC rows to side-normalized signed-R bars."""

    entry = float(entry_price)
    distance = abs(entry - float(stop_loss))
    if not math.isfinite(distance) or distance <= 0:
        raise ExitOverlayError("overlay_entry_stop_geometry_invalid")
    normalized_side = side.upper()
    if normalized_side not in {"LONG", "SHORT"}:
        raise ExitOverlayError(f"overlay_side_invalid:{side}")

    def signed(price: float) -> float:
        return (
            (price - entry) / distance
            if normalized_side == "LONG"
            else (entry - price) / distance
        )

    result: list[SignedM1Bar] = []
    for index, row in enumerate(rows):
        try:
            raw_open = float(row["open"])
            raw_high = float(row["high"])
            raw_low = float(row["low"])
            raw_close = float(row["close"])
            time_us = parse_utc_us(row.get("time_utc", row.get("time")))
        except (KeyError, TypeError, ValueError) as exc:
            raise ExitOverlayError(f"overlay_m1_row_invalid:{index}") from exc
        if raw_low > raw_high or not all(
            math.isfinite(value)
            for value in (raw_open, raw_high, raw_low, raw_close)
        ):
            raise ExitOverlayError(f"overlay_m1_range_invalid:{index}")
        signed_values = tuple(
            signed(value) for value in (raw_open, raw_high, raw_low, raw_close)
        )
        result.append(
            SignedM1Bar(
                time_us=time_us,
                open_r=signed_values[0],
                high_r=max(signed_values[1], signed_values[2]),
                low_r=min(signed_values[1], signed_values[2]),
                close_r=signed_values[3],
                source_index=index,
            )
        )
    return tuple(result)


def m1_points(
    bars: Sequence[SignedM1Bar] | Iterable[SignedM1Bar],
    *,
    high_first: bool,
) -> tuple[ExitPathPoint, ...]:
    """Expand bars into one of the two admissible extrema orderings."""

    points: list[ExitPathPoint] = []
    for bar in bars:
        middle = (
            (bar.high_r, bar.low_r)
            if high_first
            else (bar.low_r, bar.high_r)
        )
        values = (bar.open_r, *middle, bar.close_r)
        for position, value in enumerate(values):
            points.append(
                ExitPathPoint(
                    time_us=bar.time_us,
                    signed_r=float(value),
                    deadline_eligible=position == 3,
                    source_index=bar.source_index,
                )
            )
    return tuple(points)


def replay_m1_conservative(
    spec: ExitOverlaySpec,
    bars: Sequence[SignedM1Bar] | Iterable[SignedM1Bar],
    *,
    decision_time_us: int,
    cost_r: float,
    source_mode: str = "M1_CONSERVATIVE",
) -> M1ConservativeReplay:
    """Replay both M1 extrema orderings and retain the lower return."""

    bar_tuple = tuple(bars)
    high_first = replay_signed_path(
        spec,
        m1_points(bar_tuple, high_first=True),
        decision_time_us=decision_time_us,
        cost_r=cost_r,
        source_mode=source_mode,
    )
    low_first = replay_signed_path(
        spec,
        m1_points(bar_tuple, high_first=False),
        decision_time_us=decision_time_us,
        cost_r=cost_r,
        source_mode=source_mode,
    )
    differing = (
        high_first.status != low_first.status
        or high_first.exit_reason != low_first.exit_reason
        or high_first.gross_r != low_first.gross_r
    )
    candidates = (high_first, low_first)
    selected = min(
        candidates,
        key=lambda result: (
            math.inf if result.net_r is None else result.net_r,
            result.exit_reason,
        ),
    )
    return M1ConservativeReplay(
        selected=replace(selected, ambiguity=differing),
        open_high_low_close=high_first,
        open_low_high_close=low_first,
        outcomes_differ=differing,
    )


def tick_points(
    rows: Sequence[Mapping[str, Any]] | Iterable[Mapping[str, Any]],
    *,
    entry_price: float,
    stop_loss: float,
    side: str,
    decision_time_us: int,
    horizon_time_us: int,
    path_start_time_us: int | None = None,
) -> tuple[ExitPathPoint, ...]:
    """Build executable bid/ask signed-R points inside the frozen horizon.

    An executed order may fill after its decision.  ``path_start_time_us``
    keeps the frozen decision-based horizon while preventing an exit overlay
    from observing or acting on quotes that occurred before the recorded fill.
    """

    entry = float(entry_price)
    distance = abs(entry - float(stop_loss))
    if not math.isfinite(distance) or distance <= 0:
        raise ExitOverlayError("overlay_entry_stop_geometry_invalid")
    normalized_side = side.upper()
    if normalized_side not in {"LONG", "SHORT"}:
        raise ExitOverlayError(f"overlay_side_invalid:{side}")
    path_start = (
        int(decision_time_us)
        if path_start_time_us is None
        else int(path_start_time_us)
    )
    if not decision_time_us <= path_start < horizon_time_us:
        raise ExitOverlayError("overlay_path_start_outside_decision_horizon")
    quote_key = "bid" if normalized_side == "LONG" else "ask"

    points: list[ExitPathPoint] = []
    for index, row in enumerate(rows):
        try:
            time_us = true_utc_tick_time_us(row)
            price = float(row[quote_key])
        except (KeyError, TypeError, ValueError) as exc:
            raise ExitOverlayError(f"overlay_tick_row_invalid:{index}") from exc
        if time_us <= path_start or time_us > horizon_time_us:
            continue
        signed_r = (
            (price - entry) / distance
            if normalized_side == "LONG"
            else (entry - price) / distance
        )
        points.append(
            ExitPathPoint(
                time_us=time_us,
                signed_r=signed_r,
                deadline_eligible=True,
                source_index=index,
            )
        )
    return tuple(points)


def shuffle_signed_increments(
    points: Sequence[ExitPathPoint] | Iterable[ExitPathPoint],
    *,
    seed: int,
) -> tuple[ExitPathPoint, ...]:
    """Shuffle within-path signed returns and reconstruct from 0R."""

    original = tuple(points)
    if not original:
        return ()
    previous = 0.0
    increments: list[float] = []
    for point in original:
        increments.append(float(point.signed_r) - previous)
        previous = float(point.signed_r)
    random.Random(int(seed)).shuffle(increments)
    reconstructed = 0.0
    result: list[ExitPathPoint] = []
    for point, increment in zip(original, increments, strict=True):
        reconstructed += increment
        result.append(replace(point, signed_r=reconstructed))
    return tuple(result)


def shuffle_m1_blocks(
    bars: Sequence[SignedM1Bar] | Iterable[SignedM1Bar],
    *,
    seed: int,
) -> tuple[SignedM1Bar, ...]:
    """Shuffle complete M1 return blocks and reconnect them from 0R."""

    original = tuple(bars)
    order = list(range(len(original)))
    random.Random(int(seed)).shuffle(order)
    level = 0.0
    result: list[SignedM1Bar] = []
    for time_slot, source_position in enumerate(order):
        source = original[source_position]
        open_to_close = source.close_r - source.open_r
        high_offset = source.high_r - source.open_r
        low_offset = source.low_r - source.open_r
        slot = original[time_slot]
        result.append(
            SignedM1Bar(
                time_us=slot.time_us,
                open_r=level,
                high_r=level + high_offset,
                low_r=level + low_offset,
                close_r=level + open_to_close,
                source_index=slot.source_index,
            )
        )
        level += open_to_close
    return tuple(result)
