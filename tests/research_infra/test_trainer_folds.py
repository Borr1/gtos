"""Purge, embargo and walk-forward direction for the trainer's folds.

Behavioural throughout: each test constructs rows with known spans and asserts on which rows
land in train, never on the source text of the planner.
"""

from __future__ import annotations

import datetime as dt
import math

import pytest

from src.research_infra.trainer_folds import (
    BROKER_DAY_SKEW_HOURS,
    TrainerFoldSpec,
    audit_fold_leakage,
    embargo_days_from_holds,
    plan_folds,
)

DAY0 = dt.date(2025, 7, 1)


def _row(key: str, day: dt.date, *, start_h: int = 9, hold_h: float = 2.0, status: str = "measured"):
    start = dt.datetime.combine(day, dt.time(start_h), tzinfo=dt.timezone.utc)
    return {
        "row_key": key,
        "trading_day": day.isoformat(),
        "label_span_start_utc": start.isoformat(),
        "label_span_end_utc": (start + dt.timedelta(hours=hold_h)).isoformat(),
        "label_span_status": status,
    }


def _dense(n_days: int = 180, per_day: int = 4, hold_h: float = 2.0):
    rows = []
    for i in range(n_days):
        day = DAY0 + dt.timedelta(days=i)
        for j in range(per_day):
            rows.append(_row(f"r{i}_{j}", day, start_h=9 + j, hold_h=hold_h))
    return rows


# --------------------------------------------------------------------------------------------
# Direction: this is a WALK-FORWARD, not leave-one-out
# --------------------------------------------------------------------------------------------
def test_no_future_day_ever_enters_train():
    """The defect being fixed. `fold_key != fold_day` put every future day in train."""
    rows = _dense()
    by_key = {r["row_key"]: r for r in rows}
    folds = plan_folds(rows, TrainerFoldSpec(n_folds=6))
    assert folds
    for f in folds:
        test_end = dt.date.fromisoformat(f.test_end)
        for k in f.train_row_keys:
            assert dt.date.fromisoformat(by_key[k]["trading_day"][:10]) < test_end


def test_train_grows_monotonically_across_folds():
    """Expanding scheme: each later fold sees at least as much past as the one before."""
    folds = plan_folds(_dense(), TrainerFoldSpec(n_folds=6))
    sizes = [len(f.train_row_keys) for f in folds]
    assert sizes == sorted(sizes)
    assert sizes[-1] > sizes[0]


def test_test_folds_are_disjoint_and_ordered():
    folds = plan_folds(_dense(), TrainerFoldSpec(n_folds=6))
    windows = [(dt.date.fromisoformat(f.test_start), dt.date.fromisoformat(f.test_end))
               for f in folds]
    for (_, prev_end), (nxt_start, _) in zip(windows, windows[1:]):
        assert nxt_start > prev_end


# --------------------------------------------------------------------------------------------
# Purge
# --------------------------------------------------------------------------------------------
def test_a_straddling_trade_is_purged_from_train():
    """A position entered before the fold whose label resolves INSIDE the fold must not train."""
    rows = _dense(hold_h=1.0)
    folds = plan_folds(rows, TrainerFoldSpec(n_folds=6))
    fold = folds[1]
    fold_start = dt.date.fromisoformat(fold.test_start)

    # Enter 3 days before the fold, close 5 days later => resolves inside the test window.
    straddler = _row("STRADDLER", fold_start - dt.timedelta(days=3), hold_h=24 * 5)
    replanned = plan_folds(rows + [straddler], TrainerFoldSpec(n_folds=6))
    target = next(f for f in replanned if f.test_start == fold.test_start)
    assert "STRADDLER" not in target.train_row_keys
    assert target.n_purged_overlap > fold.n_purged_overlap


def test_a_trade_spanning_the_entire_fold_is_purged():
    """Longest-hold case: opens before the fold and closes after it ENDS, so it contains the
    whole test window. A predicate that only checked 'ends inside' would miss this."""
    rows = _dense(hold_h=1.0)
    folds = plan_folds(rows, TrainerFoldSpec(n_folds=6))
    fold = folds[1]
    lo = dt.date.fromisoformat(fold.test_start)
    hi = dt.date.fromisoformat(fold.test_end)
    span_days = (hi - lo).days + 20
    engulfer = _row("ENGULF", lo - dt.timedelta(days=10), hold_h=24 * span_days)
    replanned = plan_folds(rows + [engulfer], TrainerFoldSpec(n_folds=6))
    target = next(f for f in replanned if f.test_start == fold.test_start)
    assert "ENGULF" not in target.train_row_keys


def test_a_distant_past_trade_is_kept():
    """Purge must not be vacuous: something has to survive, or the test above proves nothing."""
    folds = plan_folds(_dense(), TrainerFoldSpec(n_folds=6))
    assert all(len(f.train_row_keys) > 0 for f in folds)
    assert folds[-1].n_purged_overlap < len(folds[-1].train_row_keys)


def test_unknown_spans_are_purged_and_counted():
    rows = _dense()
    unknown = [
        {**_row(f"U{i}", DAY0 + dt.timedelta(days=i * 3)),
         "label_span_start_utc": None, "label_span_end_utc": None,
         "label_span_status": "unknown"}
        for i in range(20)
    ]
    folds = plan_folds(rows + unknown, TrainerFoldSpec(n_folds=6))
    for f in folds:
        assert not any(k.startswith("U") for k in f.train_row_keys)
    assert sum(f.n_purged_unknown_span for f in folds) > 0


@pytest.mark.parametrize("bad_end", [None, "", "not-a-date", "2020-01-01T00:00:00+00:00"])
def test_incoherent_spans_never_reach_train(bad_end):
    """Null, unparseable, or end-before-start. Each must be treated as unknown, not as safe."""
    rows = _dense()
    hostile = {**_row("HOSTILE", DAY0 + dt.timedelta(days=5)),
               "label_span_end_utc": bad_end, "label_span_status": "measured"}
    folds = plan_folds(rows + [hostile], TrainerFoldSpec(n_folds=6))
    for f in folds:
        assert "HOSTILE" not in f.train_row_keys


# --------------------------------------------------------------------------------------------
# The audit
# --------------------------------------------------------------------------------------------
def test_audit_is_clean_on_a_planned_split():
    rows = _dense()
    folds = plan_folds(rows, TrainerFoldSpec(n_folds=6))
    assert audit_fold_leakage(folds, rows)["clean"] is True


def test_audit_catches_a_leak_injected_into_the_plan():
    """The audit must not merely reproduce the planner. Force a leaking key into a fold and
    confirm the independent re-derivation rejects it."""
    import dataclasses

    rows = _dense()
    folds = plan_folds(rows, TrainerFoldSpec(n_folds=6))
    fold = folds[1]
    leaking = next(
        r["row_key"] for r in rows
        if r["trading_day"] == fold.test_start
    )
    tampered = dataclasses.replace(
        fold, train_row_keys=fold.train_row_keys + (leaking,)
    )
    result = audit_fold_leakage([tampered], rows)
    assert result["clean"] is False
    assert result["n_violations"] > 0
    assert "train_day_is_test_day" in result["reasons"]


def test_audit_catches_an_unknown_span_forced_into_train():
    import dataclasses

    rows = _dense()
    rows.append({**_row("U", DAY0 + dt.timedelta(days=2)),
                 "label_span_end_utc": None, "label_span_status": "unknown"})
    folds = plan_folds(rows, TrainerFoldSpec(n_folds=6))
    tampered = dataclasses.replace(folds[2], train_row_keys=folds[2].train_row_keys + ("U",))
    result = audit_fold_leakage([tampered], rows)
    assert result["clean"] is False
    assert "unknown_span_in_train" in result["reasons"]


# --------------------------------------------------------------------------------------------
# Embargo
# --------------------------------------------------------------------------------------------
def test_embargo_matches_walkforward_gate():
    """Session W's gate and this trainer must size the embargo identically. They operate on
    different data shapes (PricedTrade vs frame dict) so the RULE is what is shared; this test
    is the coupling. `walkforward/spec.py:58-61` on why it is a test and not a comment."""
    from src.research_infra.walkforward import folds as wf
    from src.research_infra.walkforward.spec import GateSpec

    class _T:
        def __init__(self, h, exit_dt):
            self.holding_hours = h
            self.exit_utc = exit_dt

    class _P:
        status = "priced"

        def __init__(self, h, exit_dt):
            self.trade = _T(h, exit_dt)

    before = dt.date(2026, 1, 1)
    for hold_set in ([1.0], [0.5, 1.2, 3.9, 0.1, 27.0, 2.2, 8.8], [24.0 * k for k in range(1, 40)]):
        priced = [_P(h, dt.datetime(2025, 6, 1, tzinfo=dt.timezone.utc)) for h in hold_set]
        spec = GateSpec(spec_id="t", authored_utc="", embargo_quantile=0.99, embargo_floor_days=1)
        theirs = wf._empirical_embargo_days(priced, before, spec)
        mine = embargo_days_from_holds(
            [h / 24.0 for h in hold_set], quantile=0.99, floor_days=1
        )
        assert mine == theirs, f"divergence on {hold_set}: {mine} vs {theirs}"


def test_embargo_floors_when_there_is_no_history():
    assert embargo_days_from_holds([], quantile=0.99, floor_days=3) == 3


def test_embargo_grows_with_longer_holds():
    short = embargo_days_from_holds([0.1] * 100, quantile=0.99, floor_days=1)
    long = embargo_days_from_holds([0.1] * 98 + [11.4, 12.0], quantile=0.99, floor_days=1)
    assert long > short


def test_p99_embargo_is_blind_to_a_lone_tail_observation():
    """A RECORDED PROPERTY, not an endorsement. Nearest-rank p99 at n=100 selects index
    ceil(0.99*100)-1 = 98, so the single largest hold is excluded by construction: one 11.4-day
    hold among 100 intraday ones moves the embargo not at all. Two do.

    This matters because the embargo's justification is that three of twelve live sleeves exceed
    their nominal horizon -- i.e. the tail is exactly the population it is sized for. It is
    survivable here only because the embargo is a MARGIN on top of an exact per-row purge on
    actual label spans (`test_a_straddling_trade_is_purged_from_train`), which catches the long
    hold regardless of the embargo width. If the per-row purge were ever removed, this property
    would become a leak. Session W's gate shares the rule and therefore the property.
    """
    lone = embargo_days_from_holds(
        [0.1] * 99 + [11.4], quantile=0.99, floor_days=1
    )
    assert lone == 1
    assert embargo_days_from_holds([0.1] * 98 + [11.4, 12.0], quantile=0.99, floor_days=1) == 12
    # Taking the max instead is tail-complete; kept as the documented alternative.
    assert embargo_days_from_holds([0.1] * 99 + [11.4], quantile=1.0, floor_days=1) == 12


def test_longer_holds_widen_the_purge():
    """End to end: a population of multi-day holds must purge more than an intraday one."""
    intraday = plan_folds(_dense(hold_h=2.0), TrainerFoldSpec(n_folds=6))
    multiday = plan_folds(_dense(hold_h=24 * 6), TrainerFoldSpec(n_folds=6))
    assert max(f.embargo_days for f in multiday) > max(f.embargo_days for f in intraday)
    assert sum(f.n_purged_overlap for f in multiday) > sum(f.n_purged_overlap for f in intraday)


# --------------------------------------------------------------------------------------------
# Spec and degenerate inputs
# --------------------------------------------------------------------------------------------
def test_spec_refuses_an_unsafe_unknown_span_policy():
    with pytest.raises(ValueError, match="fail-closed"):
        TrainerFoldSpec(unknown_span_policy="keep")


def test_spec_refuses_a_non_walkforward_scheme():
    with pytest.raises(ValueError, match="unsupported scheme"):
        TrainerFoldSpec(scheme="leave_one_day_out")


def test_spec_digest_changes_with_the_embargo():
    a = TrainerFoldSpec(embargo_quantile=0.99)
    b = TrainerFoldSpec(embargo_quantile=0.95)
    assert a.digest() != b.digest()


def test_too_few_days_produces_no_folds_rather_than_a_bad_one():
    assert plan_folds([_row("a", DAY0)], TrainerFoldSpec(n_folds=6)) == ()
    assert plan_folds([], TrainerFoldSpec(n_folds=6)) == ()


def test_broker_skew_is_applied_to_both_edges():
    """The fold window is widened by the broker/UTC day-boundary offset, so containment is
    provable rather than incidental on the embargo floor."""
    assert BROKER_DAY_SKEW_HOURS >= 3.0
    rows = _dense(hold_h=1.0)
    folds = plan_folds(rows, TrainerFoldSpec(n_folds=6))
    fold = folds[1]
    lo = dt.date.fromisoformat(fold.test_start)
    # A row closing inside the skew band before the fold's UTC midnight must still be purged.
    edge = _row("EDGE", lo - dt.timedelta(days=fold.embargo_days), start_h=22, hold_h=1.0)
    replanned = plan_folds(rows + [edge], TrainerFoldSpec(n_folds=6))
    target = next(f for f in replanned if f.test_start == fold.test_start)
    assert "EDGE" not in target.train_row_keys
