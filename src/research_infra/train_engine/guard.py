"""CB-3 gate 4 -- the partition gate. Fail closed, on every path.

Imports `src.research_infra.trainer_partitions` and never restates a boundary.
Session CC owns that module this wave; this one is a consumer, so a boundary
moves in exactly one place.

## The measured tension this module resolves, recorded rather than smoothed over

The ratification (5) says the lane structurally cannot touch March or the
blackouts. The acceptance test the same commission mandates (CB-3 gate 1) is
outcome identity against the frozen engine **on the sealed 2-day January S1R1
fixture** -- and `trainer_partitions.DEFAULT_REGISTRY` puts 2026-01-01..01-31 in
`sealed_b7_5_development_january`, role `SEALED`, which is **not trainable**. A
single `assert_trainable` on every path would refuse the session's own
acceptance gate; a single blanket exemption for "the engine" would make the gate
decorative.

Per the ratification's own rule ("the builder records the disagreement in
writing and the more restrictive disposition wins"), the split is:

| gate | applies to | refuses |
|---|---|---|
| `assert_no_blackout` | **every** path, no exception, no flag | the reserved blackout (March 2026) |
| `assert_trainable` | training runs only | every non-trainable role, blackout included |

and the exemption is made structurally harmless rather than trusted: a
`REPRODUCTION` window **cannot produce a training artifact**, because
`runner.write_training_outputs` refuses any authorization whose purpose is not
`TRAINING`. So the sealed fixture can be reproduced, and the reproduction can
never be fed to the iteration ledger.

## Why the guard derives its own days

A caller that hands over a day list is promising something. The engine replays
whatever the args say. So `authorize_window` takes the window bounds the ENGINE
will use and enumerates the calendar itself -- a caller cannot narrow the audit
by narrowing what it declares. Calendar days, not trading days: a superset can
only make the gate stricter, never looser.

## The SECOND axis, added by Session CD (B2250)

Session CC landed `trainer_partitions.SurfaceMap` after this module was written,
and it answers a different verb. `Disposition.trainable` says whether a model may
be **FITTED** on a day; `SurfaceMap.surface_for_day` says whether the lane may
**ITERATE** against it. They disagree on purpose: January 2026 is `SEALED` on the
first axis and `VAL` on the second, which is exactly why Session CD's
regeneration is legal at all.

So there are now three gates, and the surface gate is on **every** path:

| gate | applies to | refuses |
|---|---|---|
| `assert_no_blackout` | every path | the reserved blackout (March 2026) |
| `SurfaceMap.assert_iterable` | every path | TEST, and any day covered by no surface |
| `assert_trainable` | `TRAINING` only | every non-trainable role |

The surface gate is unconditional rather than purpose-scoped, and that is the
ratification's own tie-break ("the more restrictive disposition wins"): a
reproduction of a day is still a read of that day, and there is no purpose under
which reading the live forward stream is acceptable. It is also strictly a
tightening -- it can refuse a window this module used to allow, and can never
allow one it used to refuse.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Any, Iterable

from src.research_infra import trainer_partitions
from src.research_infra.train_engine import march_one_shot
from src.research_infra.trainer_partitions import (
    DEFAULT_REGISTRY,
    DEFAULT_SURFACE_MAP,
    PartitionRefusal,
    PartitionRegistry,
    SurfaceMap,
    SurfaceRefusal,
    as_date,
    lane_disposition_for_day,
)

#: The three things a window may be authorized FOR. There is no fourth, and no
#: "skip the gate" value -- an unknown purpose refuses.
PURPOSE_TRAINING = "TRAINING"
PURPOSE_REPRODUCTION = "ACCEPTANCE_REPRODUCTION"
#: Session CD (B2250). A look the lane takes on an ITERABLE surface: it may read
#: a `SEALED`-role window (January is VAL on the surface axis), it logs itself to
#: CC's iteration ledger, it bills nothing, and it can never emit a TRAINING
#: artifact -- because "may I fit here" is the other axis and this purpose does
#: not check it.
PURPOSE_LANE_ITERATION = "LANE_ITERATION"
PURPOSES = (PURPOSE_TRAINING, PURPOSE_REPRODUCTION, PURPOSE_LANE_ITERATION)


class WindowRefused(PartitionRefusal):
    """The window was refused. Subclasses PartitionRefusal so one except catches both."""


@dataclass(frozen=True)
class WindowAuthorization:
    """Proof that a window passed the gate, and the record of what it passed."""

    purpose: str
    start: str
    end: str
    days: tuple[str, ...]
    registry_id: str
    #: Per-day role, so a receipt can show the reader what the lane actually ran
    #: on rather than asserting it was fine.
    roles: dict[str, str] = field(default_factory=dict)
    blackout_checked: bool = True
    trainable_checked: bool = False
    note: str = ""
    #: The second axis (Session CD). Per-day lane surface, and the map that said
    #: so, both recorded -- a receipt that names only the role is the receipt that
    #: let the two verbs become interchangeable.
    surfaces: dict[str, str] = field(default_factory=dict)
    surface_map_id: str = ""
    surface_map_digest: str = ""
    surface_checked: bool = False
    dominant_surface: str = ""
    disclosures: tuple[str, ...] = ()

    @property
    def may_emit_training_evidence(self) -> bool:
        return self.purpose == PURPOSE_TRAINING and self.trainable_checked

    @property
    def may_emit_iteration_evidence(self) -> bool:
        """A lane look may emit a lane artifact -- and never a training one.

        The split is the same structural trick CB used for reproduction: the
        emitter checks the AUTHORIZATION, not the caller's intent, so a purpose
        that never checked the fitting axis cannot produce an artifact whose
        stamp claims it did.
        """

        return self.purpose == PURPOSE_LANE_ITERATION and self.surface_checked

    def as_dict(self) -> dict[str, Any]:
        return {
            "purpose": self.purpose,
            "window": [self.start, self.end],
            "day_count": len(self.days),
            "days": list(self.days),
            "registry_id": self.registry_id,
            "roles": dict(self.roles),
            "blackout_checked": self.blackout_checked,
            "trainable_checked": self.trainable_checked,
            "may_emit_training_evidence": self.may_emit_training_evidence,
            "note": self.note,
            "surfaces": dict(self.surfaces),
            "surface_map_id": self.surface_map_id,
            "surface_map_digest": self.surface_map_digest,
            "surface_checked": self.surface_checked,
            "dominant_surface": self.dominant_surface,
            "disclosures": list(self.disclosures),
            "may_emit_iteration_evidence": self.may_emit_iteration_evidence,
            "two_axis_note": (
                "roles == may this be FITTED on (partition registry); surfaces "
                "== may the lane ITERATE against it (surface map). January 2026 "
                "is SEALED on the first and VAL on the second; they disagree on "
                "purpose."
            ),
        }


def calendar_days(start: Any, end: Any) -> tuple[str, ...]:
    """Every calendar day in [start, end]. A superset of the replayed days."""

    lo, hi = as_date(start), as_date(end)
    if hi < lo:
        raise ValueError(f"window_reversed:{lo.isoformat()}..{hi.isoformat()}")
    return tuple(
        (lo + dt.timedelta(days=offset)).isoformat()
        for offset in range((hi - lo).days + 1)
    )


def assert_no_blackout(
    days: Iterable[Any],
    *,
    registry: PartitionRegistry = DEFAULT_REGISTRY,
    context: str = "train_engine",
) -> None:
    """Refuse the reserved blackout on every path. No purpose unlocks this."""

    hits = []
    for day in sorted({as_date(item) for item in days}):
        window = registry.blackout_hit(day)
        if window is not None:
            hits.append((day.isoformat(), window))
    if not hits:
        return
    listed = ", ".join(day for day, _ in hits[:8])
    raise WindowRefused(
        f"{context}: {len(hits)} day(s) inside the reserved blackout "
        f"({registry.reserved_blackout}): {listed}"
        f"{'...' if len(hits) > 8 else ''}. {registry.blackout_reason}",
        refusals=tuple(registry.disposition_for_day(day) for day, _ in hits),
    )


def assert_lane_iterable(
    days: Iterable[Any],
    *,
    surfaces: SurfaceMap = DEFAULT_SURFACE_MAP,
    context: str = "train_engine",
) -> None:
    """Refuse any day the lane may not ITERATE against. On every path.

    Delegates to `SurfaceMap.assert_iterable` and re-raises as this module's
    type. The delegate raises `SurfaceRefusal`, which is NOT a `PartitionRefusal`
    -- so a caller writing `except WindowRefused`, which this module's own
    docstring invites, would have let a TEST-surface refusal escape as an
    unrelated error. That is bit-for-bit the bug CB shipped into the trainable
    delegate and caught on the first smoke test (`SESSION_CB_TRAIN_ENGINE_RESULT`
    section 5.1); repeating it one function later would be unforgivable.
    """

    try:
        surfaces.assert_iterable(days, context=context)
    except SurfaceRefusal as refusal:
        raise WindowRefused(
            str(refusal), refusals=tuple(getattr(refusal, "refusals", ()))
        ) from refusal


def authorize_window(
    *,
    start: Any,
    end: Any,
    purpose: str,
    registry: PartitionRegistry = DEFAULT_REGISTRY,
    surfaces: SurfaceMap = DEFAULT_SURFACE_MAP,
    context: str = "train_engine",
    note: str = "",
) -> WindowAuthorization:
    """The one entry point. Fails closed on an unknown purpose."""

    if purpose not in PURPOSES:
        raise WindowRefused(
            f"{context}: unknown run purpose {purpose!r}; expected one of {PURPOSES}"
        )
    days = calendar_days(start, end)

    # The one March exception, and it is not a bypass: `march_one_shot.current()`
    # returns None unless this process was armed with the prereg's own digest,
    # the swap happens only for LANE_ITERATION, only against the DEFAULT objects
    # a caller did not override, and the replacements clear exactly the March
    # span and nothing else (`authorized_*` refuse a wider blackout). Both
    # replacements rename themselves, so the `registry_id` and `surface_map_id`
    # on the authorization this function returns -- and therefore every receipt
    # and ledger row downstream -- say the one-shot was armed without anyone
    # having to remember to disclose it. `TRAINABLE_ROLES` is untouched, so the
    # TRAINING branch below still refuses every March day.
    one_shot = march_one_shot.current()
    if (
        one_shot is not None
        and purpose == PURPOSE_LANE_ITERATION
        and any(registry.blackout_hit(as_date(day)) is not None for day in days)
    ):
        if registry is DEFAULT_REGISTRY:
            registry = march_one_shot.authorized_registry(one_shot)
        if surfaces is DEFAULT_SURFACE_MAP:
            surfaces = march_one_shot.authorized_surfaces(one_shot)

    # Blackout first, unconditionally: a reproduction of March is still March.
    assert_no_blackout(days, registry=registry, context=context)

    # Surface second, also unconditionally. Reading a day is reading it whatever
    # the purpose says, and there is no purpose under which the live forward
    # stream is readable. Strictly a tightening of what this function used to
    # allow -- see the module docstring's three-gate table.
    assert_lane_iterable(days, surfaces=surfaces, context=context)

    trainable_checked = False
    if purpose == PURPOSE_TRAINING:
        try:
            registry.assert_trainable(days, context=f"{context}:{purpose}")
        except PartitionRefusal as refusal:
            # Re-raise as this module's type. The delegate raises the BASE
            # class, so a caller writing `except WindowRefused` -- which this
            # module's own docstring invites -- would have missed it and let a
            # refusal escape as an unrelated error. Caught by the smoke test on
            # the first run, which is the only reason it is not shipped.
            raise WindowRefused(
                str(refusal), refusals=getattr(refusal, "refusals", ())
            ) from refusal
        trainable_checked = True

    roles: dict[str, str] = {}
    surface_by_day: dict[str, str] = {}
    disclosures: set[str] = set()
    for day in days:
        # Both axes, from the one call that returns them together, so a receipt
        # can never carry a role without the surface that goes with it.
        lane = lane_disposition_for_day(day, surfaces=surfaces, registry=registry)
        roles[day] = lane.fitting.role or "UNASSIGNED"
        surface_by_day[day] = lane.surface.surface or "UNCOVERED"
        if lane.surface.disclosure:
            disclosures.add(lane.surface.disclosure)

    stamp = surfaces.classify_days(days, span=(days[0], days[-1]))

    return WindowAuthorization(
        purpose=purpose,
        start=days[0],
        end=days[-1],
        days=days,
        registry_id=registry.registry_id,
        roles=roles,
        trainable_checked=trainable_checked,
        note=note,
        surfaces=surface_by_day,
        surface_map_id=surfaces.map_id,
        surface_map_digest=surfaces.digest(),
        surface_checked=True,
        dominant_surface=str(stamp.get("dominant_surface") or ""),
        disclosures=tuple(sorted(disclosures)),
    )


def trainable_ranges(
    registry: PartitionRegistry = DEFAULT_REGISTRY,
) -> list[dict[str, Any]]:
    """Every range this lane may fit on. Used by the receipt and by the handoff.

    Written as a query rather than a constant so that when Session CC tightens
    the registry, this answer moves with it instead of going stale.
    """

    return [
        {
            "partition_id": partition.partition_id,
            "role": partition.role,
            "start": partition.start,
            "end": partition.end,
            "prior_consumption": bool(partition.prior_consumption),
        }
        for partition in registry.partitions
        if partition.role in trainer_partitions.TRAINABLE_ROLES
    ]
