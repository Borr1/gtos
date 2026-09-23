"""Purged, embargoed, walk-forward folds for the offline trainer.

WHAT WAS WRONG, MEASURED
------------------------
`learned_edge_trainer._train_head_with_oof` cut folds like this:

    train_rows = [r for r in eligible if r.get("fold_key") != fold_day]
    test_rows  = [r for r in eligible if r.get("fold_key") == fold_day]

That is leave-one-day-out, so **train contains the days after the test day as well as the days
before it**. It is not a walk-forward at all, and there is no purge and no embargo anywhere in
the module. The trainer's own docstring asserted otherwise --

    "Week blocks keep the purge/embargo boundary at the block edge (>= the 48h label horizon
     except inside-block adjacency, which day folds share anyway)"

-- and no code implemented it. A label horizon of 48h against day folds with a zero-day gap means
a position entered on D-1 and closed on D+1 sits in TRAIN with its outcome decided by price action
inside the test day. The registry that governs this trainer states the intended rule in its own
header doctrine: *"Purge = 48h label horizon; embargo = 1 trading day at every train/validation
boundary."* It was prose in a JSONL file with no enforcement behind it.

WHY THE EMBARGO IS MEASURED RATHER THAN NOMINAL
----------------------------------------------
The same reason `walkforward/folds.py` gives, and the same rule: across twelve live sleeves the
used-fraction of the nominal horizon runs 0.4% to 105%, with three sleeves exceeding their nominal
horizon outright, so no single nominal number is right for all of them. The embargo is the
`embargo_quantile` (default p99) of realised holds **taken only from rows whose label closed
strictly before the fold opens**, floored at `embargo_floor_days`. The train-side restriction is
what keeps it leak-free and it also resolves the apparent circularity (embargo defines train,
train defines embargo): it is computed from the naive pre-fold prefix, which needs no embargo to
define.

`embargo_days_from_holds` is a free function precisely so it can be held identical to
`walkforward.folds._empirical_embargo_days` by test rather than by comment
(`test_trainer_folds.py::test_embargo_matches_walkforward_gate`). Session W's `folds.py` operates
on `PricedTrade` objects from the gate's pricing panel; the trainer's rows are frame dicts with no
cost model attached, so the data shapes genuinely differ and the *rule* is what is shared. That is
the coupling worth having -- `walkforward/spec.py:58-61` records why asserting a coupling that does
not exist is worse than silent duplication.

UNKNOWN SPANS ARE PURGED, NEVER KEPT
------------------------------------
A row whose `label_span_status` is `unknown` cannot be shown not to overlap the test window, so it
is dropped from TRAIN and counted. Fail-closed: the cost of being wrong in the other direction is
a leak that no downstream statistic can detect.

THE BROKER-CLOCK SKEW, AND WHY 3 HOURS
--------------------------------------
`trading_day` is a **broker-calendar** day; the span timestamps are UTC. Broker wall clock is
`America/New_York + 7h` for both servers (`src/utils/broker_clock.py`), so a broker day begins at
21:00Z (US DST) or 22:00Z (US standard) on the previous UTC date. Bounding a fold with UTC
midnight on the same dates is therefore off by up to **3 hours** at each edge. Rather than rely on
the embargo floor happening to absorb it, the fold window is widened by `BROKER_DAY_SKEW_HOURS`
explicitly, so the containment is provable rather than incidental. Widening can only purge more.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
from collections import Counter
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping, Sequence

__all__ = [
    "BROKER_DAY_SKEW_HOURS",
    "TrainerFold",
    "TrainerFoldSpec",
    "audit_fold_leakage",
    "embargo_days_from_holds",
    "plan_folds",
]

#: Max |broker-day boundary - UTC midnight| for the registered servers. See module docstring.
BROKER_DAY_SKEW_HOURS = 3.0

SPAN_UNKNOWN = "unknown"
_UTC = dt.timezone.utc


def _parse_utc(value: Any) -> dt.datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=_UTC)


def _as_date(value: Any) -> dt.date | None:
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if isinstance(value, str) and len(value) >= 10:
        try:
            return dt.date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None


def embargo_days_from_holds(
    hold_days: Sequence[float], *, quantile: float, floor_days: int
) -> int:
    """Nearest-rank quantile of realised holds, in whole days, floored.

    Nearest-rank (not linear interpolation) so the result is deterministic and needs no numpy --
    identical to `walkforward.folds._empirical_embargo_days`, which this is held equal to by test.
    Empty input returns the floor: no evidence means no basis to shrink the gap.
    """
    if not hold_days:
        return floor_days
    ordered = sorted(hold_days)
    idx = min(len(ordered) - 1, max(0, math.ceil(quantile * len(ordered)) - 1))
    return max(floor_days, int(math.ceil(ordered[idx])))


@dataclass(frozen=True)
class TrainerFoldSpec:
    """Everything fixed before the rows are seen. Hash it, then plan."""

    spec_id: str = "trainer_folds_v1"
    #: Expanding (anchored) walk-forward: train is always strictly-past. The alternative the
    #: trainer used -- leave-one-out over all days -- puts the future in train and is not a
    #: walk-forward under any definition.
    scheme: str = "expanding_walk_forward"
    n_folds: int = 6
    embargo_quantile: float = 0.99
    embargo_floor_days: int = 1
    purge_rule: str = "label_span_overlap"
    #: What to do with a row whose label span could not be established.
    unknown_span_policy: str = "purge"
    min_train_rows: int = 50
    min_test_rows: int = 20
    #: Digest of the partition registry the rows were admitted under, so a fold plan carries
    #: evidence of which partitioning produced it.
    registry_digest: str = ""

    def __post_init__(self) -> None:
        if self.scheme != "expanding_walk_forward":
            raise ValueError(f"unsupported scheme {self.scheme!r}")
        if self.unknown_span_policy != "purge":
            raise ValueError(
                f"unknown_span_policy must be 'purge' (fail-closed); got "
                f"{self.unknown_span_policy!r}"
            )
        if not 0.0 < self.embargo_quantile <= 1.0:
            raise ValueError(f"embargo_quantile out of range: {self.embargo_quantile}")
        if self.n_folds < 2:
            raise ValueError("n_folds must be >= 2")

    def digest(self) -> str:
        return hashlib.sha256(json.dumps(asdict(self), sort_keys=True).encode()).hexdigest()


@dataclass(frozen=True)
class TrainerFold:
    fold_id: int
    test_start: str
    test_end: str
    embargo_days: int
    train_row_keys: tuple[str, ...]
    test_row_keys: tuple[str, ...]
    n_purged_overlap: int
    n_purged_unknown_span: int
    status: str  # evaluable | train_thin | test_thin | test_empty | train_empty

    @property
    def evaluable(self) -> bool:
        return self.status == "evaluable"

    def as_dict(self) -> dict[str, Any]:
        return {
            "fold_id": self.fold_id,
            "test_start": self.test_start,
            "test_end": self.test_end,
            "embargo_days": self.embargo_days,
            "n_train_rows": len(self.train_row_keys),
            "n_test_rows": len(self.test_row_keys),
            "n_purged_overlap": self.n_purged_overlap,
            "n_purged_unknown_span": self.n_purged_unknown_span,
            "status": self.status,
        }


def _row_span(row: Mapping[str, Any]) -> tuple[dt.datetime | None, dt.datetime | None, str]:
    """Parse a row's label span, distrusting its self-reported status.

    An INVERTED span (`end` before `start`) is treated as unknown, not as measured. This is not
    hypothetical fastidiousness -- it was a live leak, found by this module's own test suite
    (B522). The purge predicate is `hi >= purge_lo and lo <= purge_hi`; with `hi` far in the past
    the first clause is false, so an inverted span is never purged and lands in TRAIN however
    badly it overlaps. A row claiming `label_span_status: "measured"` with
    `label_span_end_utc: "2020-01-01"` and a 2025 start walked straight into training data.

    `learned_edge_dataset_builder._label_span` already refuses to EMIT such a row, but
    `plan_folds` is a public entry point that accepts rows from anywhere, and a guard that
    trusts its input is not a guard.
    """
    status = str(row.get("label_span_status") or SPAN_UNKNOWN)
    lo = _parse_utc(row.get("label_span_start_utc"))
    hi = _parse_utc(row.get("label_span_end_utc"))
    if lo is None or hi is None or hi < lo:
        return lo, hi, SPAN_UNKNOWN
    return lo, hi, status


def plan_folds(
    rows: Sequence[Mapping[str, Any]],
    spec: TrainerFoldSpec | None = None,
) -> tuple[TrainerFold, ...]:
    """Cut `rows` into expanding purged/embargoed walk-forward folds.

    Rows need `row_key`, `trading_day`, and the three `label_span_*` fields emitted by
    `learned_edge_dataset_builder`. Folds are cut on the CALENDAR between the first and last
    trading day, not on equal row counts: equal row counts mean unequal calendar time, and an
    embargo measured in days has no defined relationship to a row index. Sparse stretches
    therefore produce thin or empty folds, which are reported rather than hidden.
    """
    spec = spec or TrainerFoldSpec()
    days = sorted({d for d in (_as_date(r.get("trading_day")) for r in rows) if d is not None})
    if len(days) < 2:
        return ()

    span_start, span_end = days[0], days[-1]
    total = (span_end - span_start).days + 1
    edges = [span_start + dt.timedelta(days=int(round(i * total / spec.n_folds)))
             for i in range(spec.n_folds)]
    edges.append(span_end + dt.timedelta(days=1))
    edges = sorted(set(edges))

    skew = dt.timedelta(hours=BROKER_DAY_SKEW_HOURS)
    out: list[TrainerFold] = []

    for k in range(len(edges) - 1):
        lo_day, hi_day = edges[k], edges[k + 1] - dt.timedelta(days=1)
        if hi_day < lo_day:
            continue
        # Fold 0 has no past under an expanding scheme; it is the initial train block.
        if k == 0:
            continue

        test_rows = [r for r in rows if (d := _as_date(r.get("trading_day"))) and lo_day <= d <= hi_day]
        past_rows = [r for r in rows if (d := _as_date(r.get("trading_day"))) and d < lo_day]

        # Embargo from holds that CLOSED strictly before the fold opens -- train side only.
        fold_open = dt.datetime.combine(lo_day, dt.time.min, tzinfo=_UTC) - skew
        holds: list[float] = []
        for r in past_rows:
            lo, hi, status = _row_span(r)
            if status == SPAN_UNKNOWN or lo is None or hi is None:
                continue
            if hi < fold_open:
                holds.append((hi - lo).total_seconds() / 86400.0)
        embargo = embargo_days_from_holds(
            holds, quantile=spec.embargo_quantile, floor_days=spec.embargo_floor_days
        )

        gap = dt.timedelta(days=embargo)
        purge_lo = dt.datetime.combine(lo_day, dt.time.min, tzinfo=_UTC) - gap - skew
        purge_hi = dt.datetime.combine(hi_day, dt.time.max, tzinfo=_UTC) + gap + skew

        train_keys: list[str] = []
        n_overlap = n_unknown = 0
        for r in past_rows:
            lo, hi, status = _row_span(r)
            if status == SPAN_UNKNOWN:
                n_unknown += 1
                continue
            assert lo is not None and hi is not None  # status guarantees both
            if hi >= purge_lo and lo <= purge_hi:
                n_overlap += 1
                continue
            train_keys.append(str(r.get("row_key")))

        test_keys = [str(r.get("row_key")) for r in test_rows]
        if not train_keys:
            status_s = "train_empty"
        elif not test_keys:
            status_s = "test_empty"
        elif len(test_keys) < spec.min_test_rows:
            status_s = "test_thin"
        elif len(train_keys) < spec.min_train_rows:
            status_s = "train_thin"
        else:
            status_s = "evaluable"

        out.append(
            TrainerFold(
                fold_id=len(out),
                test_start=lo_day.isoformat(),
                test_end=hi_day.isoformat(),
                embargo_days=embargo,
                train_row_keys=tuple(train_keys),
                test_row_keys=tuple(test_keys),
                n_purged_overlap=n_overlap,
                n_purged_unknown_span=n_unknown,
                status=status_s,
            )
        )
    return tuple(out)


def audit_fold_leakage(
    folds: Sequence[TrainerFold],
    rows: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Independent re-derivation: does any TRAIN row's label span reach the test window?

    Deliberately does not reuse `plan_folds`' internals -- it re-reads the emitted fold and
    re-checks the invariant from the row spans, so a bug in the planner shows up as a violation
    here rather than being reproduced by shared code. Any violation is a leak.
    """
    by_key = {str(r.get("row_key")): r for r in rows}
    violations: list[dict[str, Any]] = []
    reasons: Counter[str] = Counter()
    skew = dt.timedelta(hours=BROKER_DAY_SKEW_HOURS)

    for f in folds:
        gap = dt.timedelta(days=f.embargo_days)
        lo_day = dt.date.fromisoformat(f.test_start)
        hi_day = dt.date.fromisoformat(f.test_end)
        win_lo = dt.datetime.combine(lo_day, dt.time.min, tzinfo=_UTC) - gap - skew
        win_hi = dt.datetime.combine(hi_day, dt.time.max, tzinfo=_UTC) + gap + skew
        test_days = {
            _as_date(by_key[k].get("trading_day")) for k in f.test_row_keys if k in by_key
        }
        for key in f.train_row_keys:
            row = by_key.get(key)
            if row is None:
                reasons["train_key_not_in_rows"] += 1
                continue
            lo, hi, status = _row_span(row)
            if status == SPAN_UNKNOWN:
                violations.append({"fold": f.fold_id, "row_key": key, "why": "unknown_span_in_train"})
                reasons["unknown_span_in_train"] += 1
                continue
            assert lo is not None and hi is not None
            if hi >= win_lo and lo <= win_hi:
                violations.append(
                    {"fold": f.fold_id, "row_key": key, "why": "span_overlaps_embargoed_test_window"}
                )
                reasons["span_overlaps_embargoed_test_window"] += 1
            d = _as_date(row.get("trading_day"))
            if d is not None and d in test_days:
                violations.append({"fold": f.fold_id, "row_key": key, "why": "train_day_is_test_day"})
                reasons["train_day_is_test_day"] += 1
            if d is not None and d > hi_day:
                violations.append({"fold": f.fold_id, "row_key": key, "why": "future_day_in_train"})
                reasons["future_day_in_train"] += 1

    return {
        "clean": not violations,
        "n_violations": len(violations),
        "reasons": dict(reasons),
        "violations": violations[:25],
        "n_folds": len(folds),
        "n_evaluable": sum(1 for f in folds if f.evaluable),
    }
