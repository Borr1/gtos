"""Fail-closed partition registry for the offline TRAINER path.

WHAT THIS REPLACES, AND WHY IT IS CODE RATHER THAN A FILE
---------------------------------------------------------
The only partition registry the repository had is
`research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/ULTIMATE_EDGE_PARTITION_REGISTRY.jsonl`
(v1, authored 2026-06-10). It is consumed by `learned_edge_dataset_builder.load_partition_registry`
via an **optional** `--registry` flag. Three properties made it unsafe to hand to a builder, all
measured 2026-07-29 (B510-B513):

  1. Its `TRAIN` partition `train_backfill_2025H2_2026Q1` spans `["2025-06-02", "2026-04-17"]`,
     which **contains all of March 2026** by range — the string "2026-03" appears nowhere in the
     file, so the hazard is invisible to grep. It also swallows B7.5's entire January development
     window and 17 days of its April window.
  2. `partition_role_for_day` returns `(None, None)` for any day no partition covers, and the only
     refusal downstream is `role == "SEALED"`. Unknown days therefore **pass**.
  3. `--registry` is optional. Omitted, every day gets role `None` and the sealed-day check cannot
     fire at all.

This module is the re-authored registry, and it lives in `src/` as **code** on purpose. Sparse
checkout excludes most of `research/operations/` from a working tree (`WAVE_5_WORKING_AGREEMENT.md`
section 5): a registry that ships as a file under that path can be committed, absent from disk, and
leave `git status` clean. A guard whose enforcement depends on a file that may not be present is not
a guard. `DEFAULT_REGISTRY` cannot go missing, cannot de-hydrate to an LFS pointer, and carries a
digest.

FAIL CLOSED — THE THREE RULES
-----------------------------
  * A day covered by **no** partition is REFUSED (`day_outside_every_partition`). Not `None`, not
    silently admitted. This is the inversion of v1's behaviour and it is the whole point.
  * A day inside `reserved_blackout` is REFUSED **whatever role any partition assigns it**. The
    blackout is checked first and no role can override it. March 2026 is therefore unreachable even
    if a future editor re-adds a TRAIN range that spans it.
  * Only `TRAIN` and `TRAIN_DEVELOPMENT_GRADE` are trainable. Every other role — including roles
    added later — must be added to `TRAINABLE_ROLES` deliberately.

Overlapping ranges are rejected at construction. v1 resolved overlaps by file order in a linear
scan, so reordering its lines silently changed which role a day got; a TRAIN row placed above an
overlapping SEALED row would have admitted sealed days.

WHERE MARCH'S PROTECTION COMES FROM, AND WHY THIS IS STRICTER THAN B7.5
-----------------------------------------------------------------------
B7.5's own contract already reserves March correctly:
`B7_5_POST_ACCELERATION_DECISION_CONTRACT.json` binds `untouched_treatment_challenge_march`
`2026-03-01..2026-03-31` with `role: "untouched_for_this_treatment_historical_challenge"`,
`march_outcome_read: false`, `outcomes_previously_inspected_for_this_treatment: false`.

But that contract also records `pristine_model_holdout: false`, and its protection is scoped to
*this treatment*. `CLAUDE.md` section 4 takes the stronger position — March is "the only untouched
month for any future broad-family treatment, and the scarcest resource in the programme". This
registry implements the **stronger** reading: `RESERVED_UNREAD`, no treatment scope, no expiry.
Where two authorities disagree the more restrictive disposition wins and both are recorded on the
partition; that rule is applied throughout `DEFAULT_REGISTRY` and every instance of it is noted.

**The brief for this work said a registry marking March TRAIN "would burn the window". The tense
is wrong and the correction matters** [MEASURED 2026-07-29, B514]. 22 March 2026 days were already
materialized as TRAIN with `status: completed` by the June route, committed at HEAD in
`…/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/train_ledgers/ULTIMATE_EDGE_TRAIN_DAY_PROGRESS_LEDGER.jsonl`
(234 rows, 2025-07-01..2026-05-29, `partition_role: TRAIN` on every one). What is still intact is
the **B7.5 sealed replay** of March, which is unrun and cannot be launched — its
`source_plan_digest_sha256` is `null` and the runner fails closed. So this registry is not
preventing a future burn of a pristine month; it is stopping *further* consumption and making the
already-measured one visible in `Partition.prior_consumption` so the next reader cannot mistake
reserved for virgin. Whether the June fit disqualifies March as a broad-family holdout is an
owner/review judgment and is deliberately not taken here.

SCOPE — READ THIS BEFORE REUSING
---------------------------------
This registry governs the **trainer** path (`learned_edge_dataset_builder` ->
`learned_edge_trainer`), whose substrate is per-day replay ledgers that exist only for 2025-2026.
It is deliberately NOT the authority for the walk-forward admission gate in
`src/research_infra/walkforward/`, which evaluates fixed-rule sleeves over the D1 bars archive back
to 1992 and carries its own blackout in `GateSpec.reserved_blackout`. Days before the earliest
partition here are refused because no replay ledger exists for them, which is correct for a trainer
and would be wrong for the gate. The two blackouts are held equal by
`tests/research_infra/test_trainer_partitions.py::test_blackout_agrees_with_gate_spec` rather than
by assertion in a comment — a coupling that is checked, not merely claimed.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

__all__ = [
    "DEFAULT_REGISTRY",
    "DEFAULT_SURFACE_MAP",
    "Disposition",
    "LANE_ITERABLE_SURFACES",
    "LaneDisposition",
    "Partition",
    "PartitionRefusal",
    "PartitionRegistry",
    "RESERVED_UNREAD_MARCH_2026",
    "ROLES",
    "SURFACES",
    "SurfaceBand",
    "SurfaceDisposition",
    "SurfaceMap",
    "SurfaceRefusal",
    "TRAINABLE_ROLES",
    "UncoveredGap",
    "as_date",
    "lane_disposition_for_day",
]

SCHEMA = "gtos.trainer.partition_registry.v2"

#: Closed role vocabulary. A registry carrying a role outside this set is rejected at load, so a
#: typo ("TRAIN_DEV" for "TRAIN_DEVELOPMENT_GRADE") fails loudly instead of silently becoming an
#: unknown role that no rule admits and no rule refuses.
ROLES = (
    "TRAIN",
    "TRAIN_DEVELOPMENT_GRADE",
    "VALIDATION",
    "SEALED",
    "STRESS",
    "FORWARD",
    "RESERVED_UNREAD",
)

#: The ONLY roles a model may be fitted on. Everything else refuses.
TRAINABLE_ROLES = frozenset({"TRAIN", "TRAIN_DEVELOPMENT_GRADE"})

#: March 2026, from `B7_5_POST_ACCELERATION_DECISION_CONTRACT.json`
#: `window_source_plan_bindings[2]` (`untouched_treatment_challenge_march`, start 2026-03-01,
#: end 2026-03-31). Held equal to `walkforward.spec.GateSpec.reserved_blackout` by test.
RESERVED_UNREAD_MARCH_2026 = ("2026-03-01", "2026-03-31")

OPEN_END = "open"
_FAR_FUTURE = dt.date(9999, 12, 31)


class PartitionRefusal(RuntimeError):
    """A day was refused for training. Carries every offending day, never just the first."""

    def __init__(self, message: str, *, refusals: Sequence["Disposition"] = ()) -> None:
        super().__init__(message)
        self.refusals = tuple(refusals)


def as_date(value: Any) -> dt.date:
    """Accept a date, datetime, or ISO `YYYY-MM-DD` string. Reject anything else loudly."""
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if isinstance(value, str):
        return dt.date.fromisoformat(value[:10])
    raise TypeError(f"not a date: {value!r}")


@dataclass(frozen=True)
class Partition:
    """One contiguous date range with exactly one role.

    `end` may be the literal string `"open"` for a partition with no closing date (the forward
    capture). `excluded_days` punches holes that fall back to the registry's fail-closed default —
    an excluded day is NOT unassigned-and-allowed, it is unassigned-and-refused.
    """

    partition_id: str
    role: str
    start: str
    end: str
    excluded_days: tuple[str, ...] = ()
    source: str = ""
    note: str = ""
    #: When two authorities disagreed about this range, what the other one said. Recorded so the
    #: override is auditable rather than invisible.
    supersedes: str = ""
    #: Measured evidence that this range has ALREADY been consumed by some route, with a receipt.
    #: A reserved range whose reservation arrived too late is a different object from a pristine
    #: one, and the difference must be machine-readable rather than left in prose. Empty means
    #: "no prior consumption measured", NOT "known pristine".
    prior_consumption: str = ""

    def __post_init__(self) -> None:
        if self.role not in ROLES:
            raise ValueError(f"{self.partition_id}: role {self.role!r} not in {ROLES}")
        lo = as_date(self.start)
        hi = _FAR_FUTURE if self.end == OPEN_END else as_date(self.end)
        if hi < lo:
            raise ValueError(f"{self.partition_id}: range reversed {self.start}..{self.end}")
        for d in self.excluded_days:
            ed = as_date(d)
            if not (lo <= ed <= hi):
                raise ValueError(
                    f"{self.partition_id}: excluded day {d} outside range {self.start}..{self.end}"
                )

    @property
    def lo(self) -> dt.date:
        return as_date(self.start)

    @property
    def hi(self) -> dt.date:
        return _FAR_FUTURE if self.end == OPEN_END else as_date(self.end)

    def covers(self, day: dt.date) -> bool:
        return self.lo <= day <= self.hi and day.isoformat() not in set(self.excluded_days)

    def as_dict(self) -> dict[str, Any]:
        d = {
            "row_kind": "partition",
            "partition_id": self.partition_id,
            "role": self.role,
            "date_range": [self.start, self.end],
            "trainable": self.role in TRAINABLE_ROLES,
        }
        if self.excluded_days:
            d["excluded_days"] = list(self.excluded_days)
        if self.source:
            d["source"] = self.source
        if self.note:
            d["notes"] = self.note
        if self.supersedes:
            d["supersedes"] = self.supersedes
        if self.prior_consumption:
            d["prior_consumption"] = self.prior_consumption
        return d


@dataclass(frozen=True)
class Disposition:
    """The answer for one day. `trainable` is the only field a caller should branch on."""

    day: str
    role: str | None
    partition_id: str | None
    trainable: bool
    refusal: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "day": self.day,
            "role": self.role,
            "partition_id": self.partition_id,
            "trainable": self.trainable,
            "refusal": self.refusal,
        }


@dataclass(frozen=True)
class PartitionRegistry:
    registry_id: str
    authored_utc: str
    partitions: tuple[Partition, ...]
    #: Ranges no role can unlock. Checked BEFORE any partition lookup.
    reserved_blackout: tuple[tuple[str, str], ...] = (RESERVED_UNREAD_MARCH_2026,)
    blackout_reason: str = (
        "March 2026 is the only outcome-unread month the programme has left (CLAUDE.md section 4). "
        "No training row may originate inside it and no role may override this."
    )
    schema: str = SCHEMA
    note: str = ""
    _by_role: dict[str, tuple[str, ...]] = field(default_factory=dict, compare=False, repr=False)

    def __post_init__(self) -> None:
        seen: set[str] = set()
        for p in self.partitions:
            if p.partition_id in seen:
                raise ValueError(f"duplicate partition_id {p.partition_id!r}")
            seen.add(p.partition_id)
        # Reject overlaps. v1 resolved them by file order in a linear scan, which made the role a
        # day received a property of line ordering rather than of the data.
        #
        # "Overlap" means a day COVERED BY BOTH, not merely a range intersection: `excluded_days`
        # legitimately punches one partition out of another's span. v1 does exactly this — its
        # validation_walkforward_gate (2026-05-14..05-29) intersects train_touched_may18 (05-18)
        # and resolves it by excluding 05-18 from the former. A range-only check called that a
        # collision and refused to load a file that is in fact unambiguous; caught by loading the
        # real v1 registry through this validator (B516).
        ordered = sorted(self.partitions, key=lambda p: (p.lo, p.hi, p.partition_id))
        for i, a in enumerate(ordered):
            for b in ordered[i + 1 :]:
                if b.lo > a.hi:
                    break  # sorted by lo: nothing later can intersect a
                lo, hi = max(a.lo, b.lo), min(a.hi, b.hi)
                if hi < lo:
                    continue
                clash = next(
                    (
                        lo + dt.timedelta(days=k)
                        for k in range((hi - lo).days + 1)
                        if a.covers(lo + dt.timedelta(days=k))
                        and b.covers(lo + dt.timedelta(days=k))
                    ),
                    None,
                )
                if clash is not None:
                    raise ValueError(
                        f"overlapping partitions: {a.partition_id} ({a.start}..{a.end}) and "
                        f"{b.partition_id} ({b.start}..{b.end}) both cover {clash.isoformat()}"
                    )
        for lo, hi in self.reserved_blackout:
            if as_date(hi) < as_date(lo):
                raise ValueError(f"reserved_blackout range reversed: {lo}..{hi}")

    # -- lookup ---------------------------------------------------------------------------------
    def blackout_hit(self, day: dt.date) -> tuple[str, str] | None:
        for lo, hi in self.reserved_blackout:
            if as_date(lo) <= day <= as_date(hi):
                return (lo, hi)
        return None

    def disposition_for_day(self, day: Any) -> Disposition:
        """The fail-closed lookup. Every path that does not positively establish a trainable role
        returns `trainable=False` with a machine-readable `refusal`."""
        d = as_date(day)
        iso = d.isoformat()

        hit = self.blackout_hit(d)
        if hit is not None:
            return Disposition(
                day=iso,
                role="RESERVED_UNREAD",
                partition_id=f"reserved_blackout:{hit[0]}..{hit[1]}",
                trainable=False,
                refusal="day_inside_reserved_blackout",
            )

        for p in self.partitions:
            if p.covers(d):
                trainable = p.role in TRAINABLE_ROLES
                return Disposition(
                    day=iso,
                    role=p.role,
                    partition_id=p.partition_id,
                    trainable=trainable,
                    refusal=None if trainable else f"role_not_trainable:{p.role}",
                )

        return Disposition(
            day=iso,
            role=None,
            partition_id=None,
            trainable=False,
            refusal="day_outside_every_partition",
        )

    def assert_trainable(self, days: Iterable[Any], *, context: str = "") -> None:
        """Raise `PartitionRefusal` listing EVERY refused day, not just the first."""
        refusals = [
            disp
            for disp in (self.disposition_for_day(x) for x in sorted({as_date(d) for d in days}))
            if not disp.trainable
        ]
        if not refusals:
            return
        by_reason: dict[str, list[str]] = {}
        for r in refusals:
            by_reason.setdefault(r.refusal or "unknown", []).append(r.day)
        detail = "; ".join(
            f"{reason} ({len(ds)} days: {', '.join(ds[:5])}{'...' if len(ds) > 5 else ''})"
            for reason, ds in sorted(by_reason.items())
        )
        raise PartitionRefusal(
            f"{context or 'partition registry'} refuses {len(refusals)} day(s): {detail}",
            refusals=refusals,
        )

    def partition_days_trainable(self, days: Iterable[Any]) -> tuple[list[str], list[Disposition]]:
        """Split days into (trainable_isos, refused_dispositions). For callers that report rather
        than raise."""
        keep: list[str] = []
        drop: list[Disposition] = []
        for d in sorted({as_date(x) for x in days}):
            disp = self.disposition_for_day(d)
            (keep.append(disp.day) if disp.trainable else drop.append(disp))
        return keep, drop

    # -- serialisation --------------------------------------------------------------------------
    def header(self) -> dict[str, Any]:
        return {
            "row_kind": "registry_header",
            "schema_version": self.schema,
            "registry_id": self.registry_id,
            "authored_utc": self.authored_utc,
            "reserved_blackout": [list(r) for r in self.reserved_blackout],
            "blackout_reason": self.blackout_reason,
            "trainable_roles": sorted(TRAINABLE_ROLES),
            "roles": list(ROLES),
            "row_count": len(self.partitions),
            "fail_closed": {
                "day_outside_every_partition": "refused",
                "day_inside_reserved_blackout": "refused_regardless_of_role",
                "role_not_in_trainable_roles": "refused",
            },
            "notes": self.note,
        }

    def to_jsonl(self) -> str:
        lines = [json.dumps(self.header(), sort_keys=True)]
        lines += [
            json.dumps(p.as_dict(), sort_keys=True)
            for p in sorted(self.partitions, key=lambda p: (p.lo, p.partition_id))
        ]
        return "\n".join(lines) + "\n"

    def digest(self) -> str:
        """sha256 over the semantic content — not over the file bytes, so reformatting is not
        drift but a changed range is."""
        payload = {
            "schema": self.schema,
            "registry_id": self.registry_id,
            "reserved_blackout": [list(r) for r in self.reserved_blackout],
            "partitions": [
                [p.partition_id, p.role, p.start, p.end, list(p.excluded_days)]
                for p in sorted(self.partitions, key=lambda p: (p.lo, p.partition_id))
            ],
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()

    @classmethod
    def from_rows(cls, rows: Sequence[Mapping[str, Any]]) -> "PartitionRegistry":
        header: Mapping[str, Any] = {}
        parts: list[Partition] = []
        for row in rows:
            kind = row.get("row_kind")
            if kind == "registry_header":
                header = row
                continue
            if kind != "partition":
                continue
            rng = row.get("date_range") or []
            if len(rng) != 2:
                raise ValueError(f"partition {row.get('partition_id')!r}: bad date_range {rng!r}")
            parts.append(
                Partition(
                    partition_id=str(row.get("partition_id") or ""),
                    role=str(row.get("role") or ""),
                    start=str(rng[0]),
                    end=str(rng[1]),
                    excluded_days=tuple(str(d) for d in (row.get("excluded_days") or ())),
                    source=str(row.get("source") or ""),
                    note=str(row.get("notes") or ""),
                    supersedes=str(row.get("supersedes") or ""),
                )
            )
        blackout = tuple(
            (str(r[0]), str(r[1])) for r in (header.get("reserved_blackout") or ())
        ) or (RESERVED_UNREAD_MARCH_2026,)
        return cls(
            registry_id=str(header.get("registry_id") or "unnamed"),
            authored_utc=str(header.get("authored_utc") or ""),
            partitions=tuple(parts),
            reserved_blackout=blackout,
            note=str(header.get("notes") or ""),
        )

    @classmethod
    def load(cls, path: Path | str) -> "PartitionRegistry":
        """Load an external registry, VALIDATING it. A v1-shaped file loads only if it survives
        the closed vocabulary and the overlap check; `ULTIMATE_EDGE_PARTITION_REGISTRY.jsonl`
        does (its roles are all in `ROLES` and it has no overlaps) — and its TRAIN range then
        collides with the March blackout at lookup time, which is the intended outcome."""
        rows: list[dict[str, Any]] = []
        with Path(path).open("r", encoding="utf-8") as h:
            for line in h:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                if isinstance(row, dict):
                    rows.append(row)
        return cls.from_rows(rows)


# ---------------------------------------------------------------------------------------------
# The re-authored registry (v2).
#
# Built by reconciling v1 (ULTIMATE_EDGE, 2026-06-10) against B7.5's decision contract
# (2026-07-16, later and therefore controlling) window by window. Where they disagree the MORE
# RESTRICTIVE disposition wins and `supersedes` records what was overridden.
#
# B7.5 windows, read from B7_5_POST_ACCELERATION_DECISION_CONTRACT.json window_source_plan_bindings:
#   development_january                 2026-01-01..2026-01-31  development
#   untouched_treatment_challenge_march 2026-03-01..2026-03-31  untouched_for_this_treatment
#   adverse_development_april           2026-04-01..2026-04-30  adverse_development
#   adverse_development_may             2026-05-13..2026-05-17  adverse_development
#   engineering_june_04                 2026-06-04..2026-06-04  parity_and_factorial_smoke_only
#
# Gaps are LEFT UNCOVERED ON PURPOSE. An uncovered day is refused with
# `day_outside_every_partition`. Inventing a permissive partition to "fill" a gap is exactly the
# failure v1 had.
# ---------------------------------------------------------------------------------------------
DEFAULT_REGISTRY = PartitionRegistry(
    registry_id="gtos_trainer_partition_registry_v2_2026_07_29",
    authored_utc="2026-07-29T00:00:00+00:00",
    note=(
        "Re-authored by Session Z (B510-B539). Supersedes ULTIMATE_EDGE_PARTITION_REGISTRY.jsonl "
        "(v1, 2026-06-10), whose TRAIN range 2025-06-02..2026-04-17 covered all of March 2026, "
        "all of B7.5's January development window, and 17 days of its April window. Reconciled "
        "against B7_5_POST_ACCELERATION_DECISION_CONTRACT.json; more restrictive disposition wins."
    ),
    partitions=(
        Partition(
            partition_id="train_backfill_2025H2",
            role="TRAIN",
            start="2025-06-02",
            end="2025-12-31",
            source="bridge_ftmo backfill packages (D1/H4/H1/M15 full range, M1 monthly)",
            note=(
                "The part of v1's train_backfill_2025H2_2026Q1 that no later authority claims. "
                "v1 ran this range to 2026-04-17; truncated at 2025-12-31 because B7.5 claims "
                "January onward."
            ),
            supersedes="ULTIMATE_EDGE v1 train_backfill_2025H2_2026Q1 (2025-06-02..2026-04-17)",
        ),
        Partition(
            partition_id="sealed_b7_5_development_january",
            role="SEALED",
            start="2026-01-01",
            end="2026-01-31",
            source="B7_5_POST_ACCELERATION_DECISION_CONTRACT.json window_source_plan_bindings[1]",
            note=(
                "B7.5 development window: four arms sealed and accepted. v1 had this inside a "
                "TRAIN range. SEALED wins - fitting on a window whose outcomes were read is the "
                "leak the sealed-partition doctrine exists to stop."
            ),
            supersedes="ULTIMATE_EDGE v1 train_backfill_2025H2_2026Q1 marked this TRAIN",
        ),
        Partition(
            partition_id="train_february_2026_unclaimed",
            role="TRAIN",
            start="2026-02-01",
            end="2026-02-28",
            source="bridge_ftmo backfill; inside v1's TRAIN range, unclaimed by B7.5",
            note=(
                "The one stretch of v1's TRAIN range that survives reconciliation unchanged: no "
                "B7.5 window covers February 2026 and no outcome for it has been read."
            ),
        ),
        Partition(
            partition_id="reserved_unread_march_2026",
            role="RESERVED_UNREAD",
            start="2026-03-01",
            end="2026-03-31",
            source=(
                "B7_5_POST_ACCELERATION_DECISION_CONTRACT.json window_source_plan_bindings[2] "
                "(untouched_treatment_challenge_march); CLAUDE.md section 4"
            ),
            note=(
                "THE hazard this registry exists for. v1 marked it TRAIN by range containment. "
                "Also covered by reserved_blackout, so it is refused twice over and no future "
                "edit to this partition alone can unlock it. B7.5 scopes its protection to 'this "
                "treatment' and records pristine_model_holdout: false; CLAUDE.md section 4 takes "
                "the stronger position and that is what is implemented. READ prior_consumption "
                "BEFORE treating this range as pristine - it is reserved, not virgin."
            ),
            supersedes="ULTIMATE_EDGE v1 train_backfill_2025H2_2026Q1 marked this TRAIN",
            prior_consumption=(
                "ALREADY FITTED, MEASURED 2026-07-29 (B514). 22 March 2026 trading days "
                "(2026-03-02..2026-03-31) were materialized as TRAIN with status 'completed' by "
                "the June v4 ultimate-mechanical-edge route and are committed at HEAD: "
                "research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/"
                "train_ledgers/ULTIMATE_EDGE_TRAIN_DAY_PROGRESS_LEDGER.jsonl - 234 rows, "
                "2025-07-01..2026-05-29, partition_role TRAIN on every row, and those rows carry "
                "per-day outcome fields. TWO SENSES OF 'UNREAD' MUST NOT BE CONFLATED: (a) the "
                "B7.5 SEALED REPLAY of March is UNRUN and remains protected - no March arm "
                "artifact exists and b7_5_post_acceleration_runner.py fails closed because the "
                "window's source_plan_digest_sha256 is null; (b) MODEL FITTING on March already "
                "happened, for the mechanical-edge family. CLAUDE.md section 4 reserves March for "
                "a future BROAD-family treatment, which (a) preserves and (b) does not obviously "
                "destroy. Whether the June fit disqualifies March as a holdout is an owner/review "
                "judgment, NOT a session's - it is recorded here, not decided here."
            ),
        ),
        Partition(
            partition_id="sealed_b7_5_adverse_development_april",
            role="SEALED",
            start="2026-04-01",
            end="2026-04-30",
            source="B7_5_POST_ACCELERATION_DECISION_CONTRACT.json window_source_plan_bindings[3]",
            note=(
                "Supersedes THREE conflicting v1 partitions inside April: train_burned_april_"
                "development (04-20..04-26, TRAIN_DEVELOPMENT_GRADE), sealed_april_gap "
                "(04-27..04-28, SEALED) and the tail of the v1 TRAIN backfill (04-01..04-17). "
                "B7.5 is later (2026-07-16 vs 2026-06-10) and claims the whole month; 15 days of "
                "it are sealed and the arm cannot resume."
            ),
            supersedes=(
                "ULTIMATE_EDGE v1 train_backfill_2025H2_2026Q1 / train_burned_april_development "
                "/ sealed_april_gap"
            ),
        ),
        Partition(
            partition_id="stress_calendar_partial_closure",
            role="STRESS",
            start="2026-05-01",
            end="2026-05-04",
            source="existing timewarp_ftmo_20260501_20260504 package",
            note="Partial-market-closure days; guard regression only, never fitting. From v1.",
        ),
        Partition(
            partition_id="sealed_may05",
            role="SEALED",
            start="2026-05-05",
            end="2026-05-05",
            source="existing timewarp_ftmo_20260505 package",
            note="v1 sealed single-shot final-gate day. Unchanged.",
        ),
        Partition(
            partition_id="train_rolling_may_first_half",
            role="TRAIN",
            start="2026-05-06",
            end="2026-05-12",
            source="existing KIAP rolling dynamic ledgers",
            note=(
                "v1 ran this to 2026-05-13. Truncated by one day: B7.5's adverse_development_may "
                "window opens on 05-13, and the more restrictive disposition wins."
            ),
            supersedes="ULTIMATE_EDGE v1 train_rolling_may_first_half (2026-05-06..2026-05-13)",
        ),
        Partition(
            partition_id="sealed_b7_5_adverse_development_may",
            role="SEALED",
            start="2026-05-13",
            end="2026-05-17",
            source="B7_5_POST_ACCELERATION_DECISION_CONTRACT.json window_source_plan_bindings[4]",
            note=(
                "v1 split this range between train_rolling_may_first_half (05-13) and "
                "validation_walkforward_gate (05-14..05-17). B7.5 claims all five days."
            ),
            supersedes=(
                "ULTIMATE_EDGE v1 train_rolling_may_first_half / validation_walkforward_gate"
            ),
        ),
        Partition(
            partition_id="train_touched_may18",
            role="TRAIN_DEVELOPMENT_GRADE",
            start="2026-05-18",
            end="2026-05-18",
            source="existing KIAP rolling ledgers",
            note=(
                "Demoted from validation by v1 after the May-18 degradation analysis touched it. "
                "Development grade: may fit, may never produce a validation claim."
            ),
        ),
        Partition(
            partition_id="validation_walkforward_gate",
            role="VALIDATION",
            start="2026-05-19",
            end="2026-05-29",
            source="bridge backfill",
            note=(
                "v1 ran this 05-14..05-29 excluding 05-18. Opened on 05-19 instead: 05-14..05-17 "
                "is now inside B7.5's sealed May window, which makes the v1 exclusion of 05-18 "
                "redundant - the range no longer contains it."
            ),
            supersedes="ULTIMATE_EDGE v1 validation_walkforward_gate (2026-05-14..2026-05-29)",
        ),
        Partition(
            partition_id="sealed_june_fresh",
            role="SEALED",
            start="2026-06-01",
            end="2026-06-09",
            source="bridge backfill (reserved)",
            note=(
                "v1 reserved this for a final gate. Contains B7.5's engineering_june_04 parity "
                "smoke day, which is also sealed - the two authorities agree here."
            ),
        ),
        Partition(
            partition_id="forward_capture_future",
            role="FORWARD",
            start="2026-06-10",
            end=OPEN_END,
            source="bridge weekly exports",
            note=(
                "Open-ended and NOT trainable. This is what covers the live FTMO trading period "
                "from 2026-07-29 onward: live days can never silently become training rows. v1 "
                "described a weekly roll of forward days into TRAIN; that roll is a deliberate "
                "act and must be performed by editing this registry, not by an open role."
            ),
        ),
    ),
)


# =============================================================================================
# THE TRAINING LANE'S SURFACE AXIS
# =============================================================================================
# Added by Session CC (wave 14, B2200-B2249) implementing `phase14/TRAINING_LANE_RATIFICATION.md`
# section 2, ratified by Borhen 2026-07-31.
#
# TWO AXES, TWO VERBS, AND CONFLATING THEM IS THE WHOLE HAZARD
# ------------------------------------------------------------
# Everything above answers ONE question: **may a model be FITTED on this day's rows?**
# (`Disposition.trainable`, gated by `TRAINABLE_ROLES`). The training lane asks a DIFFERENT
# question: **may a lane session ITERATE against this day — run a variant, read the outcome,
# unbilled?** The two are not the same and neither implies the other:
#
#   * January 2026 is `SEALED` (may NOT be fitted — its four arms' outcomes were read) and
#     lane-`VAL` (MAY be iterated — a window whose outcomes are already read protects nothing
#     by being refused, and Session CD's broad-family regeneration is commissioned on exactly
#     that window).
#   * A day may be lane-`TRAIN` and still absent from every replay ledger (all of 1992-2024),
#     so it is not fittable by the trainer for a reason that has nothing to do with leakage.
#
# So the surface axis is ADDITIVE. It never widens `TRAINABLE_ROLES` and never touches
# `DEFAULT_REGISTRY`; `lane_disposition_for_day` returns both answers side by side so a caller
# physically cannot read one for the other.
#
# WHERE THIS MAP IS MORE RESTRICTIVE THAN THE RATIFICATION'S FRAME, AND WHY
# ------------------------------------------------------------------------
# The ratification's section 2 is explicitly "the frame; CC audits and may tighten, never
# loosen". Five tightenings were made, each recorded on the band that carries it and each
# reproduced in `phase14/receipts/CC_CONTAMINATION_AUDIT_V1.json`:
#
#   T1  **Half of April 2026 is NOT already-read, and the frame would have burned it.** The
#       frame lists "April's 15 sealed days" under TRAIN. Measured (B36, `JANUARY_BANK.md`
#       section 5.1): the sealed partial is 2026-04-01..2026-04-15 and stops there — 2026-04-16
#       has shards but no `COMPACT_EVENT_MANIFEST.json` and contributes zero ledger rows, and
#       2026-04-17..2026-04-30 was prepared and never run. **Fifteen April days have never had
#       an outcome read.** Opening "April" as TRAIN by month name would have consumed them.
#   T2  **The three already-read replay windows are VAL, not TRAIN.** January (2026-01),
#       April's sealed partial and May's 2026-05-13..05-17 all fall inside the frame's own VAL
#       span 2025-01-01..2026-05-31. Two declarations covering the same days is an ambiguity,
#       and the narrower USE wins: VAL is "ranking and gradient checks only", TRAIN is "iterate
#       freely". Both are unbilled and both are logged, so nothing the lane needs is lost — but
#       every figure from those windows now carries the used-once disclosure automatically.
#   T3  **2026-06-01..2026-07-28 is left UNCOVERED, therefore refused.** The frame declares no
#       surface for it. It is not virgin — `GateSpec.global_span` ends 2026-07-27, so every
#       full-history gate walk in the estate has consumed it — so calling it TEST would be a
#       lie that invites a "confirmation" on burned data. Uncovered-is-refused is the rule the
#       fitting registry already uses and it is the honest disposition here: recorded as an
#       `UncoveredGap` with its measured consumption, not silently absent.
#   T4  **TEST opens at the EARLIEST arming date across both accounts, 2026-07-29**, not at
#       each account's own. redacted_account armed 2026-07-30 and `mx_btcusd` 2026-07-31; a per-
#       account cutoff would leave 2026-07-29 iterable for a redacted_account claim while FTMO was
#       already trading it. The per-account dates are carried on the band for reference.
#   T5  **`TRAINABLE_ROLES` is unchanged.** Nothing in this section makes one additional day
#       fittable. See the two-axes note above.
#
# WHAT THIS MAP DOES NOT DO
# -------------------------
# It does not enforce itself on every existing caller. A full-history gate walk legitimately
# spans 1992..2026-07-27 and therefore crosses T3's gap; making `surface_for_day` fatal
# everywhere would break the admission gate, which is frozen. Enforcement lives at the three
# points the ratification names: the iteration ledger refuses to log a TEST look, the
# graduation biller refuses a candidate whose provenance touches TEST, and CB's train engine
# refuses a day outside TRAIN/VAL. `assert_no_test_consumption` is the primitive all three use.

#: Ordered MOST PERMISSIVE FIRST. `dominant_surface` returns the last (most restrictive) one
#: present in a span, which is why the order is data rather than a comparison written by hand.
SURFACES = ("TRAIN", "VAL", "TEST")

#: The surfaces a lane session may iterate against at all. `TEST` is absent and that absence is
#: the point — it is consumed by the sealed gate and by live monitoring, never by the lane.
LANE_ITERABLE_SURFACES = frozenset({"TRAIN", "VAL"})

#: The sealed-holdout cutoff for the live forward stream, in `sealed_holdout.is_sealed`
#: semantics (a day is virgin iff `day > cutoff`). FTMO armed 2026-07-29 12:55 UTC, so
#: 2026-07-29 is the first live day and the cutoff is the day before it. See T4.
LIVE_FORWARD_SEALED_CUTOFF = "2026-07-28"


class SurfaceRefusal(RuntimeError):
    """A day (or a span) was refused by the surface axis. Carries every offending day."""

    def __init__(self, message: str, *, refusals: Sequence["SurfaceDisposition"] = ()) -> None:
        super().__init__(message)
        self.refusals = tuple(refusals)


@dataclass(frozen=True)
class SurfaceBand:
    """One contiguous date range with exactly one training-lane surface.

    `used_once_disclosure` is not documentation. The ratification requires that every figure
    quoted off a used-once surface carries the disclosure, and a disclosure that lives in a
    markdown table is one a tired session forgets. Carried here it travels on every
    `SurfaceDisposition`, into every iteration-ledger row, and into every graduation record.
    """

    band_id: str
    surface: str
    start: str
    end: str
    basis: str = ""
    note: str = ""
    #: What the ratification's own frame said, when this band departs from it. See T1-T5.
    tightened_from: str = ""
    #: Measured evidence that this range has already been consumed, with a receipt. Empty means
    #: "no prior consumption measured", NOT "known pristine" — the same rule as
    #: `Partition.prior_consumption`, for the same reason.
    prior_consumption: str = ""
    #: Non-empty iff a figure from this surface must be published with a caveat.
    used_once_disclosure: str = ""

    def __post_init__(self) -> None:
        if self.surface not in SURFACES:
            raise ValueError(f"{self.band_id}: surface {self.surface!r} not in {SURFACES}")
        lo = as_date(self.start)
        hi = _FAR_FUTURE if self.end == OPEN_END else as_date(self.end)
        if hi < lo:
            raise ValueError(f"{self.band_id}: range reversed {self.start}..{self.end}")

    @property
    def lo(self) -> dt.date:
        return as_date(self.start)

    @property
    def hi(self) -> dt.date:
        return _FAR_FUTURE if self.end == OPEN_END else as_date(self.end)

    def covers(self, day: dt.date) -> bool:
        return self.lo <= day <= self.hi

    def as_dict(self) -> dict[str, Any]:
        d = {
            "row_kind": "surface_band",
            "band_id": self.band_id,
            "surface": self.surface,
            "date_range": [self.start, self.end],
            "lane_iterable": self.surface in LANE_ITERABLE_SURFACES,
        }
        for k in ("basis", "note", "tightened_from", "prior_consumption", "used_once_disclosure"):
            if getattr(self, k):
                d[k] = getattr(self, k)
        return d


@dataclass(frozen=True)
class UncoveredGap:
    """A hole in the surface map that is DECLARED rather than silent.

    An uncovered day is refused either way — `surface_for_day` fails closed. What this record
    adds is the reason and the measured prior consumption, so the next reader does not
    rediscover the gap, assume it is virgin, and "confirm" a result on it. A gap with a
    receipt is a decision; a gap without one is an accident waiting to be filled permissively,
    which is exactly how v1's TRAIN range came to span March.
    """

    gap_id: str
    start: str
    end: str
    reason: str
    prior_consumption: str = ""
    resolution_owner: str = ""

    def __post_init__(self) -> None:
        if as_date(self.end) < as_date(self.start):
            raise ValueError(f"{self.gap_id}: range reversed {self.start}..{self.end}")

    def covers(self, day: dt.date) -> bool:
        return as_date(self.start) <= day <= as_date(self.end)

    def as_dict(self) -> dict[str, Any]:
        return {
            "row_kind": "uncovered_gap",
            "gap_id": self.gap_id,
            "date_range": [self.start, self.end],
            "disposition": "refused_day_outside_every_surface",
            "reason": self.reason,
            "prior_consumption": self.prior_consumption,
            "resolution_owner": self.resolution_owner,
        }


@dataclass(frozen=True)
class SurfaceDisposition:
    """The lane's answer for one day. `iterable` is the only field a caller should branch on."""

    day: str
    surface: str | None
    band_id: str | None
    iterable: bool
    refusal: str | None
    disclosure: str = ""

    def as_dict(self) -> dict[str, Any]:
        d = {
            "day": self.day,
            "surface": self.surface,
            "band_id": self.band_id,
            "iterable": self.iterable,
            "refusal": self.refusal,
        }
        if self.disclosure:
            d["disclosure"] = self.disclosure
        return d


@dataclass(frozen=True)
class LaneDisposition:
    """Both axes for one day, returned together so neither can be mistaken for the other.

    `may_fit` comes from the partition registry (`TRAINABLE_ROLES`); `may_iterate` from the
    surface map. They disagree on purpose — see the two-axes note at the top of this section.
    """

    day: str
    surface: SurfaceDisposition
    fitting: Disposition

    @property
    def may_iterate(self) -> bool:
        return self.surface.iterable

    @property
    def may_fit(self) -> bool:
        return self.fitting.trainable

    def as_dict(self) -> dict[str, Any]:
        return {
            "day": self.day,
            "may_iterate": self.may_iterate,
            "may_fit": self.may_fit,
            "surface": self.surface.as_dict(),
            "fitting": self.fitting.as_dict(),
        }


@dataclass(frozen=True)
class SurfaceMap:
    """The training lane's three surfaces, fail-closed.

    Three refusal rules, mirroring the partition registry's so a reader who knows one knows
    both:

      * a day covered by **no** band is REFUSED (`day_outside_every_surface`);
      * a day inside `blackout` is REFUSED whatever any band says, and is reported as `TEST`
        because that is what the ratification calls it — March is not merely un-iterable, it
        is the sealed gate's and nobody else's;
      * only surfaces in `LANE_ITERABLE_SURFACES` are iterable.

    The blackout defaults to the partition registry's, not to a second literal. A second
    literal is how two lanes silently stop protecting the same month.
    """

    map_id: str
    authored_utc: str
    bands: tuple[SurfaceBand, ...]
    gaps: tuple[UncoveredGap, ...] = ()
    blackout: tuple[tuple[str, str], ...] = (RESERVED_UNREAD_MARCH_2026,)
    schema: str = "gtos.training_lane.surface_map.v1"
    note: str = ""

    def __post_init__(self) -> None:
        seen: set[str] = set()
        for b in self.bands:
            if b.band_id in seen:
                raise ValueError(f"duplicate band_id {b.band_id!r}")
            seen.add(b.band_id)
        ordered = sorted(self.bands, key=lambda b: (b.lo, b.hi, b.band_id))
        for i, a in enumerate(ordered):
            for c in ordered[i + 1 :]:
                if c.lo > a.hi:
                    break
                raise ValueError(
                    f"overlapping surface bands: {a.band_id} ({a.start}..{a.end}) and "
                    f"{c.band_id} ({c.start}..{c.end}) both cover "
                    f"{max(a.lo, c.lo).isoformat()}"
                )
        for g in self.gaps:
            for b in self.bands:
                if not (as_date(g.end) < b.lo or as_date(g.start) > b.hi):
                    raise ValueError(
                        f"declared gap {g.gap_id!r} ({g.start}..{g.end}) intersects band "
                        f"{b.band_id!r} ({b.start}..{b.end}). A gap that a band covers is not a "
                        f"gap; one of the two is wrong and guessing which is how a permissive "
                        f"range gets invented to 'fill' a hole."
                    )
        for lo, hi in self.blackout:
            if as_date(hi) < as_date(lo):
                raise ValueError(f"blackout range reversed: {lo}..{hi}")

    # -- lookup ---------------------------------------------------------------------------
    def blackout_hit(self, day: dt.date) -> tuple[str, str] | None:
        for lo, hi in self.blackout:
            if as_date(lo) <= day <= as_date(hi):
                return (lo, hi)
        return None

    def surface_for_day(self, day: Any) -> SurfaceDisposition:
        d = as_date(day)
        iso = d.isoformat()

        hit = self.blackout_hit(d)
        if hit is not None:
            return SurfaceDisposition(
                day=iso,
                surface="TEST",
                band_id=f"blackout:{hit[0]}..{hit[1]}",
                iterable=False,
                refusal="day_inside_reserved_blackout",
            )

        for b in self.bands:
            if b.covers(d):
                iterable = b.surface in LANE_ITERABLE_SURFACES
                return SurfaceDisposition(
                    day=iso,
                    surface=b.surface,
                    band_id=b.band_id,
                    iterable=iterable,
                    refusal=None if iterable else f"surface_not_iterable:{b.surface}",
                    disclosure=b.used_once_disclosure,
                )

        gap = next((g for g in self.gaps if g.covers(d)), None)
        return SurfaceDisposition(
            day=iso,
            surface=None,
            band_id=(f"gap:{gap.gap_id}" if gap else None),
            iterable=False,
            refusal="day_outside_every_surface",
        )

    def band(self, band_id: str) -> SurfaceBand:
        try:
            return next(b for b in self.bands if b.band_id == band_id)
        except StopIteration:
            raise KeyError(f"unknown band {band_id!r}; declared are {[b.band_id for b in self.bands]}") from None

    # -- spans ----------------------------------------------------------------------------
    def _days(self, start: Any, end: Any) -> list[dt.date]:
        lo, hi = as_date(start), as_date(end)
        if hi < lo:
            raise ValueError(f"span reversed: {lo}..{hi}")
        if (hi - lo).days > 200 * 366:
            raise ValueError(
                f"span {lo}..{hi} exceeds 200 years; this is a typo, not a research window"
            )
        return [lo + dt.timedelta(days=k) for k in range((hi - lo).days + 1)]

    def classify_span(self, start: Any, end: Any) -> dict[str, Any]:
        """The surface composition of a date span, with every TEST day named.

        Named rather than counted because the graduation biller's refusal must be able to say
        *which* days leaked; "your provenance touches TEST" that cannot say where is a refusal
        nobody can act on.
        """
        return self.classify_days(self._days(start, end), span=(str(start)[:10], str(end)[:10]))

    def classify_days(self, days: Iterable[Any], *, span: tuple[str, str] | None = None) -> dict[str, Any]:
        dispositions = [self.surface_for_day(d) for d in sorted({as_date(x) for x in days})]
        by_surface: dict[str, int] = {}
        test_days: list[str] = []
        uncovered: list[str] = []
        disclosures: set[str] = set()
        for disp in dispositions:
            key = disp.surface or "UNCOVERED"
            by_surface[key] = by_surface.get(key, 0) + 1
            if disp.surface == "TEST":
                test_days.append(disp.day)
            if disp.surface is None:
                uncovered.append(disp.day)
            if disp.disclosure:
                disclosures.add(disp.disclosure)
        present = [s for s in SURFACES if by_surface.get(s)]
        return {
            "schema": "gtos.training_lane.surface_stamp.v1",
            "surface_map_id": self.map_id,
            "surface_map_digest": self.digest(),
            "span": list(span) if span else (
                [dispositions[0].day, dispositions[-1].day] if dispositions else []
            ),
            "n_days": len(dispositions),
            "surfaces_present": present + (["UNCOVERED"] if uncovered else []),
            # The most restrictive DECLARED surface present, by `SURFACES` order. This is the
            # value a ledger row's `surface` field carries: a look that touched one VAL day is
            # a VAL look, because VAL is what drags the used-once disclosure along with it.
            #
            # `UNCOVERED` is deliberately NOT a possible value here. It is not a surface, and
            # the estate's standard full-history walk crosses the one declared gap by
            # construction — a `surface` field whose commonest value was `UNCOVERED` would
            # train every reader to ignore the field and would bury the TRAIN/VAL distinction
            # that decides whether a disclosure applies. Uncoveredness is loud in three other
            # keys instead: it appears in `surfaces_present`, it is counted in `n_uncovered`,
            # and it forces `clean_for_iteration` false.
            "dominant_surface": (
                "TEST" if test_days else (present[-1] if present else None)
            ),
            "n_by_surface": dict(sorted(by_surface.items())),
            "n_uncovered": len(uncovered),
            "test_days": test_days,
            "uncovered_days": uncovered,
            "disclosures": sorted(disclosures),
            "clean_for_iteration": not test_days and not uncovered,
        }

    # -- assertions -----------------------------------------------------------------------
    def assert_no_test_consumption(self, days: Iterable[Any], *, context: str = "") -> None:
        """Raise if ANY day is on the TEST surface. The primitive all three enforcement
        points share, so `sealed_holdout` semantics cannot drift between them."""
        offenders = [
            disp
            for disp in (self.surface_for_day(d) for d in sorted({as_date(x) for x in days}))
            if disp.surface == "TEST"
        ]
        if not offenders:
            return
        shown = ", ".join(d.day for d in offenders[:5])
        raise SurfaceRefusal(
            f"{context or 'training lane'}: {len(offenders)} day(s) are on the TEST surface "
            f"({shown}{'...' if len(offenders) > 5 else ''}). TEST is consumed by the sealed "
            f"gate and by live monitoring only.",
            refusals=offenders,
        )

    def assert_iterable(self, days: Iterable[Any], *, context: str = "") -> None:
        """Raise `SurfaceRefusal` listing EVERY non-iterable day, not just the first."""
        offenders = [
            disp
            for disp in (self.surface_for_day(d) for d in sorted({as_date(x) for x in days}))
            if not disp.iterable
        ]
        if not offenders:
            return
        by_reason: dict[str, list[str]] = {}
        for r in offenders:
            by_reason.setdefault(r.refusal or "unknown", []).append(r.day)
        detail = "; ".join(
            f"{reason} ({len(ds)} days: {', '.join(ds[:5])}{'...' if len(ds) > 5 else ''})"
            for reason, ds in sorted(by_reason.items())
        )
        raise SurfaceRefusal(
            f"{context or 'training lane'} refuses {len(offenders)} day(s): {detail}",
            refusals=offenders,
        )

    # -- serialisation --------------------------------------------------------------------
    def header(self) -> dict[str, Any]:
        return {
            "row_kind": "surface_map_header",
            "schema_version": self.schema,
            "map_id": self.map_id,
            "authored_utc": self.authored_utc,
            "surfaces": list(SURFACES),
            "lane_iterable_surfaces": sorted(LANE_ITERABLE_SURFACES),
            "blackout": [list(r) for r in self.blackout],
            "live_forward_sealed_cutoff": LIVE_FORWARD_SEALED_CUTOFF,
            "band_count": len(self.bands),
            "gap_count": len(self.gaps),
            "digest": self.digest(),
            "fail_closed": {
                "day_outside_every_surface": "refused",
                "day_inside_reserved_blackout": "refused_regardless_of_band",
                "surface_not_in_lane_iterable_surfaces": "refused",
            },
            "notes": self.note,
        }

    def to_jsonl(self) -> str:
        lines = [json.dumps(self.header(), sort_keys=True)]
        lines += [
            json.dumps(b.as_dict(), sort_keys=True)
            for b in sorted(self.bands, key=lambda b: (b.lo, b.band_id))
        ]
        lines += [
            json.dumps(g.as_dict(), sort_keys=True)
            for g in sorted(self.gaps, key=lambda g: g.start)
        ]
        return "\n".join(lines) + "\n"

    def digest(self) -> str:
        """sha256 over the semantic content only — band ranges, surfaces, gaps, blackout — so
        improving a `note` is not drift and moving a boundary is. Same rule as
        `PartitionRegistry.digest`, and the same reason `candidate_family._membership_hash`
        excludes prose."""
        payload = {
            "schema": self.schema,
            "map_id": self.map_id,
            "blackout": [list(r) for r in self.blackout],
            "bands": [
                [b.band_id, b.surface, b.start, b.end]
                for b in sorted(self.bands, key=lambda b: (b.lo, b.band_id))
            ],
            "gaps": [[g.gap_id, g.start, g.end] for g in sorted(self.gaps, key=lambda g: g.start)],
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def lane_disposition_for_day(
    day: Any,
    *,
    surfaces: "SurfaceMap | None" = None,
    registry: PartitionRegistry | None = None,
) -> LaneDisposition:
    """Both axes for one day. Use this rather than either lookup alone when the answer will be
    written down — a record that says only "trainable" is the record that made the two verbs
    interchangeable in the first place."""
    smap = surfaces if surfaces is not None else DEFAULT_SURFACE_MAP
    reg = registry if registry is not None else DEFAULT_REGISTRY
    return LaneDisposition(
        day=as_date(day).isoformat(),
        surface=smap.surface_for_day(day),
        fitting=reg.disposition_for_day(day),
    )


# ---------------------------------------------------------------------------------------------
# The ratified surface map. Every band's `basis` names the artifact it was measured from;
# `tightened_from` names what the ratification's frame said where this departs from it.
# ---------------------------------------------------------------------------------------------
DEFAULT_SURFACE_MAP = SurfaceMap(
    map_id="gtos_training_lane_surface_map_v1_2026_07_31",
    authored_utc="2026-07-31T00:00:00+00:00",
    note=(
        "Session CC (B2200-B2249) implementing TRAINING_LANE_RATIFICATION.md section 2, ratified "
        "by Borhen 2026-07-31. Five tightenings vs the ratified frame (T1-T5), each recorded on "
        "the band or gap that carries it and reproduced in "
        "phase14/receipts/CC_CONTAMINATION_AUDIT_V1.json. Loosens the frame nowhere."
    ),
    bands=(
        SurfaceBand(
            band_id="train_archive_history_through_2024",
            surface="TRAIN",
            start="1992-02-18",
            end="2024-12-31",
            basis=(
                "TRAINING_LANE_RATIFICATION.md section 2 TRAIN row ('all bar/archive history "
                "through 2024-12-31'). Lower bound is walkforward.spec.GateSpec.global_span[0] "
                "(1992-02-18) — the archive's own first bar, so this band is exactly the history "
                "the estate's full-history gate walks already read."
            ),
            prior_consumption=(
                "CONSUMED, and by construction rather than by accident: every walk-forward gate "
                "run in the estate walks GateSpec.global_span = ('1992-02-18','2026-07-27'), so "
                "all of it has been read many times over (AA's 22,324 walked trades, AF's 134,027, "
                "AK, AD, AN, AQ, AU). There is nothing here to protect and that is precisely why "
                "the ratification opens it: it is the lane's free surface."
            ),
            note=(
                "Iterate freely, unbilled. Days before 1992-02-18 are uncovered and therefore "
                "refused — no bar archive exists for them, and a band with no data behind it is "
                "an invitation to fabricate one."
            ),
        ),
        SurfaceBand(
            band_id="val_selection_surface_2025_2026H1",
            surface="VAL",
            start="2025-01-01",
            end="2026-05-31",
            basis=(
                "TRAINING_LANE_RATIFICATION.md section 2 VAL row. The used-once fact is measured "
                "at two call sites: scripts/build_survivor_book.py:74 ('d.year >= 2025') and "
                "research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/"
                "KB7_growth_kelly_sizing.py:130 (the same predicate, building the forward mask "
                "the growth-Kelly dial was fitted on)."
            ),
            prior_consumption=(
                "SELECTION SURFACE. The W7 survivor book and the growth-Kelly sizing dial were "
                "both chosen on days >= 2025-01-01, so this range is the window that PICKED the "
                "armed sleeves. Also fitted day-by-day by the June v4 mechanical-edge route "
                "(ULTIMATE_EDGE_TRAIN_DAY_PROGRESS_LEDGER.jsonl, 234 rows 2025-07-01..2026-05-29, "
                "partition_role TRAIN and status completed on every row) and read as sealed replay "
                "outcomes for 2026-01-01..01-31 (four B7.5 arms) and 2026-04-01..04-15 (the 15-day "
                "S1R1 partial) and 2026-05-13..05-17."
            ),
            used_once_disclosure=(
                "VAL is the survivor book's own selection surface (d.year >= 2025, "
                "build_survivor_book.py:74 / KB7_growth_kelly_sizing.py:130). Ranking and gradient "
                "checks only; headline expectancy is never quoted from VAL alone."
            ),
            tightened_from=(
                "T2: the ratified frame lists the January / April-sealed / May replay windows "
                "under TRAIN ('iterate freely') while its own VAL row claims the same calendar "
                "days. Two declarations over one range is an ambiguity, and the narrower USE wins "
                "— those windows are VAL here. Nothing the lane needs is lost (both surfaces are "
                "unbilled and both are logged); what is gained is that every figure off them "
                "carries the used-once disclosure automatically instead of by memory. "
                "T1 lives here too: the frame's 'April's 15 sealed days' would, read as 'April', "
                "have opened 2026-04-16..2026-04-30 — fifteen days whose outcomes have NEVER been "
                "read (2026-04-16 has shards but no COMPACT_EVENT_MANIFEST.json and zero ledger "
                "rows; 04-17 onward was prepared and never run; B36, JANUARY_BANK.md section 5.1). "
                "Under VAL they are ranking-only rather than free, which is the disposition that "
                "keeps them worth something."
            ),
            note=(
                "March 2026 sits inside this range by date and is REFUSED anyway: the blackout is "
                "checked before any band. That is the one boundary no tightening or loosening can "
                "reach."
            ),
        ),
        SurfaceBand(
            band_id="test_live_forward_stream",
            surface="TEST",
            start="2026-07-29",
            end=OPEN_END,
            basis=(
                "TRAINING_LANE_RATIFICATION.md section 2 TEST row ('the live forward stream from "
                "each arming date, sealed_holdout cutoff semantics'). Arming dates from CLAUDE.md "
                "section 4: FTMO 2026-07-29 12:55 UTC (three sleeves from 14:25), redacted_account "
                "2026-07-30 ~05:18 UTC, mx_btcusd @ target_5R on FTMO 2026-07-31 ~01:26 UTC "
                "(phase13/receipts/MX_ACTIVATION_20260731.md)."
            ),
            prior_consumption=(
                "VIRGIN, and measurably so: GateSpec.global_span ends 2026-07-27, two days before "
                "the first arming, so no gate walk in the estate has read a single live day. This "
                "is the only genuinely untouched confirmation surface the programme has."
            ),
            tightened_from=(
                "T4: opened at the EARLIEST arming date across both accounts rather than at each "
                "account's own. A per-account cutoff would leave 2026-07-29 and 2026-07-30 "
                "iterable for a redacted_account-scoped claim while FTMO was already trading them, and "
                "the two books share sleeves."
            ),
            note=(
                "Open-ended and never iterable. Equivalent to "
                "sealed_holdout.is_sealed(day, '2026-07-28'), which is asserted rather than "
                "claimed — see tests/research_infra/test_training_lane_protocol.py."
            ),
        ),
    ),
    gaps=(
        UncoveredGap(
            gap_id="gap_2026H1_tail_pre_arming",
            start="2026-06-01",
            end="2026-07-28",
            reason=(
                "T3. The ratified frame declares no surface for it: VAL ends 2026-05-31 and TEST "
                "opens at the first arming date, 2026-07-29. Uncovered means REFUSED, which is the "
                "safe direction and is left in place deliberately rather than papered over."
            ),
            prior_consumption=(
                "NOT VIRGIN. GateSpec.global_span = ('1992-02-18','2026-07-27'), so every "
                "full-history gate walk in the estate has already read 2026-06-01..2026-07-27. "
                "Calling this range TEST would therefore be false and actively dangerous — it "
                "would invite a 'confirmation' on data the candidate was already scored against. "
                "The partition registry independently marks 2026-06-01..06-09 SEALED "
                "(sealed_june_fresh) and 2026-06-10 onward FORWARD."
            ),
            resolution_owner=(
                "Opening this range for lane iteration is an orchestrator/owner decision, not a "
                "session's. It is ~41 trading days of already-burned history; the honest label if "
                "it is ever opened is TRAIN, never TEST."
            ),
        ),
    ),
)
