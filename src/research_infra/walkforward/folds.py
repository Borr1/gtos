"""Calendar folds, purging, and an embargo sized off measured holds rather than a nominal.

WHY THE FOLDS ARE CALENDAR-BASED, NOT ROW-BASED
------------------------------------------------
`validation_integrity/walk_forward_oos.py` already implements a purged/embargoed
walk-forward and it is good code — but it cuts at **row indices** (`bounds[i] =
round(i*T/n_folds)`, `embargo = round(embargo_frac * T)` rows). For a leakage argument that
is the wrong axis: equal row counts means unequal calendar time, so a sleeve that fired 200
times in one quiet year and 20 times across the next five gets folds that do not correspond
to anything a trader experienced, and an embargo measured in *rows* has no defined
relationship to how long a position was actually open. This module cuts on dates and
measures the embargo in days. `walk_forward_oos` is still used, on the assembled daily
series, as an independent cross-check — see `gate.py`.

WHAT "TRAIN" MEANS WHEN NOTHING IS FITTED
-----------------------------------------
These sleeves are fixed rules. Donchian-20 does not learn a parameter per fold, so a naive
IS/OOS split would be theatre. What the train side legitimately does here is two things,
and the gate is explicit about both:

  1. **It decides admission.** For each fold, "using only data available before this fold,
     would this sleeve have been admitted?" The OOS result is then what that decision
     actually earned. That is a real walk-forward — of the *decision*, which is the thing
     being validated — and it can fail: a sleeve whose edge is one regime gets admitted on
     the train prefix containing that regime and then loses out of sample.
  2. **It sizes the nuisance parameters** — here, the embargo — without touching test data.

What no fold structure can undo is that the rules were authored by people who had already
seen the history. That is charged for separately, by DSR deflation against a trial count,
and it is the reason `spec.n_trials_basis` is written the way it is.

PURGE AND EMBARGO
-----------------
Purge (Lopez de Prado 2018 ch.7, applied to label spans): a train trade whose open interval
[entry, exit] intersects the test window widened by the embargo is dropped, because its
outcome was determined by price action inside the test period.

Embargo: **measured, not nominal.** The brief for this session is explicit about why a
nominal horizon fails — across twelve live sleeves the used-fraction of the nominal horizon
runs 0.4% to 105%, with three sleeves exceeding their nominal horizon outright, so no
single nominal number is right for all of them. The embargo is therefore the
`embargo_quantile` (default p99) of the sleeve's own realised holds in days, taken from
trades that closed **strictly before the fold opens** — never from the test side — and
floored at `embargo_floor_days`.

That train-side restriction is what makes it leak-free, and it also resolves the apparent
circularity (embargo defines train; train defines embargo): the embargo is computed from
the *naive* pre-fold prefix, which needs no embargo to define.

BLACKOUT
--------
No fold boundary may fall inside a `reserved_blackout` range. If the equal-calendar rule
puts one there, it is pushed to the day after the blackout ends and the move is recorded on
the fold. This keeps March 2026 from silently becoming a fold edge — which is a subtler way
of consuming an unread month than putting it in TRAIN.
"""

from __future__ import annotations

import datetime as dt
import math
import statistics
from dataclasses import dataclass, replace
from typing import Sequence

from src.research_infra.walkforward.panel import PricedTrade
from src.research_infra.walkforward.spec import GateSpec, _d

__all__ = [
    "Fold",
    "FoldSlice",
    "build_fold_calendar",
    "assign_folds",
    "validate_capture_windows",
    "assign_capture_folds",
]

DAY = dt.timedelta(days=1)


@dataclass(frozen=True)
class Fold:
    fold_id: int
    oos_start: dt.date
    oos_end: dt.date
    #: Fold 0 has no past. It is consumed as the initial train block and never scored.
    is_initial_train: bool
    boundary_note: str = ""

    def as_dict(self) -> dict:
        return {
            "fold_id": self.fold_id,
            "oos_start": self.oos_start.isoformat(),
            "oos_end": self.oos_end.isoformat(),
            "is_initial_train": self.is_initial_train,
            "boundary_note": self.boundary_note,
        }


@dataclass(frozen=True)
class FoldSlice:
    fold: Fold
    embargo_days: int
    train_days: tuple[dt.date, ...]
    test_days: tuple[dt.date, ...]
    train_r: tuple[float, ...]
    test_r: tuple[float, ...]
    n_train_trades: int
    n_test_trades: int
    n_purged_trades: int
    status: str  # evaluable | test_empty | test_thin | train_empty

    @property
    def evaluable(self) -> bool:
        return self.status == "evaluable"

    def as_dict(self) -> dict:
        return {
            **self.fold.as_dict(),
            "embargo_days": self.embargo_days,
            "n_train_days": len(self.train_days),
            "n_test_days": len(self.test_days),
            "n_train_trades": self.n_train_trades,
            "n_test_trades": self.n_test_trades,
            "n_purged_trades": self.n_purged_trades,
            "status": self.status,
            "train_mean_r": (sum(self.train_r) / len(self.train_r)) if self.train_r else None,
            "test_mean_r": (sum(self.test_r) / len(self.test_r)) if self.test_r else None,
        }


def _push_out_of_blackout(d: dt.date, spec: GateSpec) -> tuple[dt.date, str]:
    """Move a boundary that lands inside a blackout to the day after it ends."""
    note = ""
    for _ in range(len(spec.reserved_blackout) + 1):
        hits = spec.blackout_hits(d, d)
        if not hits:
            break
        lo, hi = hits[0]
        moved = _d(hi) + DAY
        note = (
            f"boundary {d.isoformat()} fell inside reserved blackout {lo}..{hi}; "
            f"pushed to {moved.isoformat()}"
        )
        d = moved
    return d, note


def build_fold_calendar(
    spec: GateSpec,
    span_start: dt.date,
    span_end: dt.date,
) -> tuple[Fold, ...]:
    """Equal calendar folds over the span, boundaries pushed clear of any blackout.

    The span is the sleeve's DATA AVAILABILITY window (first to last bar it could have
    traded on), never a window chosen from its results — availability is a property of the
    archive. Under `fold_rule="fixed_global_calendar"` the spec's `global_span` is used
    instead, identically for every sleeve.
    """
    if spec.fold_rule == "fixed_global_calendar":
        span_start, span_end = _d(spec.global_span[0]), _d(spec.global_span[1])
    if span_end < span_start:
        raise ValueError(f"span reversed: {span_start}..{span_end}")

    total = (span_end - span_start).days + 1
    if total < spec.n_folds * spec.min_fold_days:
        # Not enough calendar to cut n_folds of the required width. Cut as many as fit,
        # never fewer than 2 boundaries, and let the gate refuse on min_folds_evaluable.
        n = max(2, total // max(1, spec.min_fold_days))
    else:
        n = spec.n_folds

    edges: list[dt.date] = []
    for i in range(n + 1):
        raw = span_start + dt.timedelta(days=int(round(i * total / n)))
        if i == 0:
            edges.append(span_start)
            continue
        if i == n:
            edges.append(span_end + DAY)
            continue
        moved, _note = _push_out_of_blackout(raw, spec)
        edges.append(moved)
    edges = sorted(set(edges))

    folds: list[Fold] = []
    for k in range(len(edges) - 1):
        lo = edges[k]
        hi = edges[k + 1] - DAY
        if hi < lo:
            continue
        note = ""
        hits = spec.blackout_hits(lo, hi)
        if hits:
            note = f"fold overlaps reserved blackout {hits}; overlapping trades are dropped"
        folds.append(Fold(len(folds), lo, hi, is_initial_train=(k == 0), boundary_note=note))
    return tuple(folds)


def _empirical_embargo_days(
    trades: Sequence[PricedTrade],
    before: dt.date,
    spec: GateSpec,
) -> int:
    """p-quantile of realised holds, in days, over trades that CLOSED before `before`."""
    holds = [
        p.trade.holding_hours / 24.0
        for p in trades
        if p.status == "priced" and p.trade.exit_utc.date() < before
    ]
    if not holds:
        return spec.embargo_floor_days
    holds.sort()
    # Nearest-rank quantile: deterministic, no interpolation, no numpy.
    idx = min(len(holds) - 1, max(0, math.ceil(spec.embargo_quantile * len(holds)) - 1))
    return max(spec.embargo_floor_days, int(math.ceil(holds[idx])))


def assign_folds(
    trades: Sequence[PricedTrade],
    daily: dict[dt.date, float],
    folds: Sequence[Fold],
    spec: GateSpec,
) -> tuple[FoldSlice, ...]:
    """Cut one sleeve's priced trades and daily series into purged/embargoed fold slices."""
    priced = [p for p in trades if p.status == "priced"]
    out: list[FoldSlice] = []

    for f in folds:
        if f.is_initial_train:
            continue
        embargo = _empirical_embargo_days(priced, f.oos_start, spec)
        gap = dt.timedelta(days=embargo)
        # The purge window: the test fold widened by the embargo on both sides.
        purge_lo = f.oos_start - gap
        purge_hi = f.oos_end + gap

        train_r: list[float] = []
        train_days: list[dt.date] = []
        test_r: list[float] = []
        test_days: list[dt.date] = []
        n_train_tr = n_test_tr = n_purged = 0

        # Trade-level purge, on label spans. Survivors are collected PER DAY and the train
        # day-value is re-aggregated from them, rather than read out of the pre-computed
        # panel. Reading the panel re-admitted a purged trade's R through any surviving
        # trade sharing its entry day: two trades on 2023-12-20, one kept and one purged for
        # closing inside the fold, produced a train value of 1.5 = mean(-1.0, +4.0) with the
        # receipt reporting `n_purged_trades: 1`. Zero occurrences on the one-symbol D1
        # family, and guaranteed on any sleeve that fires more than once a day
        # (`sub_xvol_pullback` reaches 12).
        train_day_vals: dict[dt.date, list[float]] = {}
        for p in priced:
            e_lo, e_hi = p.trade.spans()
            key = p.trade.day(spec.day_key)
            if f.oos_start <= key <= f.oos_end:
                n_test_tr += 1
                continue
            if key > f.oos_end:
                continue  # strictly future relative to this fold: not train, not test
            # Candidate train trade. Purge if its span reaches into the widened window.
            if e_hi >= purge_lo and e_lo <= purge_hi:
                n_purged += 1
                continue
            n_train_tr += 1
            if p.r_net is not None:
                train_day_vals.setdefault(key, []).append(p.r_net)

        agg = statistics.fmean if spec.day_aggregation == "mean" else sum
        for d, r in sorted(daily.items()):
            if f.oos_start <= d <= f.oos_end:
                test_days.append(d)
                test_r.append(r)
        for d, vals in sorted(train_day_vals.items()):
            train_days.append(d)
            train_r.append(float(agg(vals)))

        if not train_r:
            status = "train_empty"
        elif not test_r:
            status = "test_empty"
        elif n_test_tr < spec.min_trades_per_fold:
            status = "test_thin"
        else:
            status = "evaluable"

        out.append(
            FoldSlice(
                fold=f,
                embargo_days=embargo,
                train_days=tuple(train_days),
                test_days=tuple(test_days),
                train_r=tuple(train_r),
                test_r=tuple(test_r),
                n_train_trades=n_train_tr,
                n_test_trades=n_test_tr,
                n_purged_trades=n_purged,
                status=status,
            )
        )
    return tuple(out)


def validate_capture_windows(
    spec: GateSpec,
    capture_windows: Sequence[Sequence[str | dt.date]],
) -> tuple[tuple[dt.date, dt.date], ...]:
    """Validate prospectively declared, independently captured data windows.

    A capture window is data authority, not an alternative fold algorithm.  The
    unchanged equal-calendar builder is applied inside each window by
    :func:`assign_capture_folds`.  Windows must therefore be ordered,
    non-overlapping, and entirely clear of the gate's reserved blackout.
    """

    if spec.fold_rule != "equal_calendar_folds_over_sleeve_span":
        raise ValueError(
            "capture windows require fold_rule="
            "equal_calendar_folds_over_sleeve_span"
        )
    if not capture_windows:
        raise ValueError("capture_windows must contain at least one window")
    normalized: list[tuple[dt.date, dt.date]] = []
    for index, raw in enumerate(capture_windows, start=1):
        if len(raw) != 2:
            raise ValueError(f"capture window {index} must contain [start, end]")
        lo, hi = _d(raw[0]), _d(raw[1])
        if hi < lo:
            raise ValueError(f"capture window {index} is reversed: {lo}..{hi}")
        if hi == lo:
            raise ValueError(
                f"capture window {index} must span at least two calendar days: "
                f"{lo}..{hi}"
            )
        if spec.blackout_hits(lo, hi):
            raise ValueError(
                f"capture window {index} overlaps reserved blackout: {lo}..{hi}"
            )
        if normalized and lo <= normalized[-1][1]:
            raise ValueError(
                "capture windows must be strictly ordered and non-overlapping: "
                f"{normalized[-1][0]}..{normalized[-1][1]} then {lo}..{hi}"
            )
        normalized.append((lo, hi))
    return tuple(normalized)


def assign_capture_folds(
    trades: Sequence[PricedTrade],
    daily: dict[dt.date, float],
    capture_windows: Sequence[tuple[dt.date, dt.date]],
    spec: GateSpec,
) -> tuple[tuple[FoldSlice, ...], dict]:
    """Apply the unchanged fold builder independently inside each capture.

    This is for non-contiguous validation captures whose empty gaps are not data.
    Treating the gap as calendar would manufacture empty folds and change which
    observations are local train versus OOS.  Every priced/unpriced input row must
    belong to exactly one declared capture; anything outside is a caller error.
    Only the scored slices are concatenated, with composite ids assigned for
    reporting.  Purging, embargo measurement, aggregation, and fold thresholds all
    remain those of ``GateSpec`` and ``assign_folds``.
    """

    windows = validate_capture_windows(spec, capture_windows)

    def owner(day: dt.date) -> int | None:
        matches = [i for i, (lo, hi) in enumerate(windows) if lo <= day <= hi]
        if len(matches) > 1:
            raise ValueError(f"trade day belongs to multiple capture windows: {day}")
        return matches[0] if matches else None

    outside = sorted(
        {
            p.trade.day(spec.day_key)
            for p in trades
            if owner(p.trade.day(spec.day_key)) is None
        }
    )
    if outside:
        raise ValueError(
            "trade days outside declared capture windows: "
            + ",".join(day.isoformat() for day in outside[:10])
        )
    escaped: list[str] = []
    for priced_trade in trades:
        key_day = priced_trade.trade.day(spec.day_key)
        capture_index = owner(key_day)
        if capture_index is None:  # already reported above
            continue
        lo, hi = windows[capture_index]
        label_lo, label_hi = priced_trade.trade.spans()
        if label_lo < lo or label_hi > hi:
            escaped.append(
                f"{priced_trade.trade.sleeve}:{key_day}:{label_lo}..{label_hi}"
            )
    if escaped:
        raise ValueError(
            "trade label spans exit their owning capture window: "
            + ",".join(escaped[:10])
        )

    scored: list[FoldSlice] = []
    captures: list[dict] = []
    initial_train_ranges: list[list[str]] = []
    for capture_index, (lo, hi) in enumerate(windows, start=1):
        local_trades = [
            p for p in trades if lo <= p.trade.day(spec.day_key) <= hi
        ]
        local_daily = {day: value for day, value in daily.items() if lo <= day <= hi}
        local_calendar = build_fold_calendar(spec, lo, hi)
        if not local_calendar or not local_calendar[0].is_initial_train:
            raise ValueError(
                f"capture {capture_index} produced no initial train fold: {lo}..{hi}"
            )
        initial = local_calendar[0]
        initial_train_ranges.append(
            [initial.oos_start.isoformat(), initial.oos_end.isoformat()]
        )
        local_slices = assign_folds(
            local_trades,
            local_daily,
            local_calendar,
            spec,
        )
        composite_ids: list[int] = []
        for local_slice in local_slices:
            composite_id = len(scored) + 1
            note_parts = [
                f"capture {capture_index} {lo.isoformat()}..{hi.isoformat()}",
                f"local fold {local_slice.fold.fold_id}",
            ]
            if local_slice.fold.boundary_note:
                note_parts.append(local_slice.fold.boundary_note)
            scored.append(
                replace(
                    local_slice,
                    fold=replace(
                        local_slice.fold,
                        fold_id=composite_id,
                        boundary_note="; ".join(note_parts),
                    ),
                )
            )
            composite_ids.append(composite_id)
        captures.append(
            {
                "capture_id": capture_index,
                "window": [lo.isoformat(), hi.isoformat()],
                "local_calendar": [fold.as_dict() for fold in local_calendar],
                "initial_train": initial_train_ranges[-1],
                "composite_scored_fold_ids": composite_ids,
                "n_input_rows": len(local_trades),
                "n_daily_observations": len(local_daily),
            }
        )

    return tuple(scored), {
        "mode": "equal_calendar_folds_over_each_predeclared_capture_window",
        "windows": [[lo.isoformat(), hi.isoformat()] for lo, hi in windows],
        "captures": captures,
        "initial_train_ranges": initial_train_ranges,
        "n_scored_slices": len(scored),
        "contract_note": (
            "Capture windows are data authority. GateSpec, equal-calendar fold "
            "construction, purge, train-side empirical embargo, daily aggregation, "
            "pooling, and all thresholds are unchanged."
        ),
    }
