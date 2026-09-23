"""The partition gate must fail closed. These tests are the proof, not the docstring.

Behavioural throughout: every assertion drives the real
`trainer_partitions.DEFAULT_REGISTRY` rather than a fixture that could drift
from it, and none of them greps a source string.
"""

from __future__ import annotations

import pytest

from src.research_infra import trainer_partitions
from src.research_infra.train_engine import guard


# --------------------------------------------------------------------------
# the absolute blackout -- no purpose, no flag, no argument unlocks March
# --------------------------------------------------------------------------


@pytest.mark.parametrize("purpose", list(guard.PURPOSES))
def test_march_is_refused_under_every_purpose(purpose: str) -> None:
    with pytest.raises(guard.WindowRefused) as excinfo:
        guard.authorize_window(start="2026-03-10", end="2026-03-11", purpose=purpose)
    assert "reserved blackout" in str(excinfo.value)


@pytest.mark.parametrize("purpose", list(guard.PURPOSES))
def test_a_window_that_only_touches_march_at_one_end_is_refused(purpose: str) -> None:
    """A window is refused for the days it CONTAINS, not for where it starts."""

    with pytest.raises(guard.WindowRefused):
        guard.authorize_window(start="2026-02-25", end="2026-03-02", purpose=purpose)
    with pytest.raises(guard.WindowRefused):
        guard.authorize_window(start="2026-03-30", end="2026-04-03", purpose=purpose)


def test_march_refusal_names_every_offending_day_not_just_the_first() -> None:
    with pytest.raises(guard.WindowRefused) as excinfo:
        guard.authorize_window(
            start="2026-03-01", end="2026-03-05", purpose=guard.PURPOSE_TRAINING
        )
    assert "5 day(s)" in str(excinfo.value)


def test_assert_no_blackout_is_callable_on_its_own_and_passes_clean_days() -> None:
    guard.assert_no_blackout(["2026-02-10", "2026-02-11"])


# --------------------------------------------------------------------------
# the trainable gate -- applies to TRAINING only, and January is SEALED
# --------------------------------------------------------------------------


def test_sealed_january_is_refused_for_training() -> None:
    with pytest.raises(guard.WindowRefused) as excinfo:
        guard.authorize_window(
            start="2026-01-01", end="2026-01-02", purpose=guard.PURPOSE_TRAINING
        )
    assert "role_not_trainable:SEALED" in str(excinfo.value)


def test_refusal_from_the_delegate_is_reraised_as_this_modules_type() -> None:
    """`assert_trainable` raises the BASE class; a caller catching WindowRefused
    would otherwise miss it. Regression pin for a bug this module shipped and the
    first smoke test caught."""

    with pytest.raises(guard.WindowRefused):
        guard.authorize_window(
            start="2026-01-01", end="2026-01-02", purpose=guard.PURPOSE_TRAINING
        )
    # ...and it is still a PartitionRefusal, so one except catches both.
    assert issubclass(guard.WindowRefused, trainer_partitions.PartitionRefusal)


def test_sealed_january_is_allowed_for_reproduction_but_cannot_emit_training() -> None:
    authorization = guard.authorize_window(
        start="2026-01-01", end="2026-01-02", purpose=guard.PURPOSE_REPRODUCTION
    )
    assert authorization.roles == {"2026-01-01": "SEALED", "2026-01-02": "SEALED"}
    assert authorization.trainable_checked is False
    assert authorization.may_emit_training_evidence is False


def test_a_trainable_window_authorizes_and_may_emit() -> None:
    authorization = guard.authorize_window(
        start="2026-02-02", end="2026-02-04", purpose=guard.PURPOSE_TRAINING
    )
    assert authorization.trainable_checked is True
    assert authorization.may_emit_training_evidence is True
    assert set(authorization.roles.values()) == {"TRAIN"}


@pytest.mark.parametrize(
    "start,end",
    [
        ("2026-04-02", "2026-04-03"),  # SEALED april
        ("2026-05-20", "2026-05-21"),  # VALIDATION
        ("2026-05-02", "2026-05-03"),  # STRESS
        ("2026-07-30", "2026-07-31"),  # FORWARD -- the live stream
        ("2025-01-02", "2025-01-03"),  # outside every partition
    ],
)
def test_every_non_trainable_role_refuses_training(start: str, end: str) -> None:
    with pytest.raises(guard.WindowRefused):
        guard.authorize_window(start=start, end=end, purpose=guard.PURPOSE_TRAINING)


def test_the_live_forward_stream_can_never_become_a_training_row() -> None:
    """The open-ended FORWARD partition covers every day from 2026-06-10 on."""

    with pytest.raises(guard.WindowRefused):
        guard.authorize_window(
            start="2027-01-01", end="2027-01-02", purpose=guard.PURPOSE_TRAINING
        )


# --------------------------------------------------------------------------
# fail-closed mechanics
# --------------------------------------------------------------------------


def test_an_unknown_purpose_refuses_rather_than_defaulting() -> None:
    with pytest.raises(guard.WindowRefused):
        guard.authorize_window(
            start="2026-02-02", end="2026-02-03", purpose="whatever_i_felt_like"
        )


def test_purpose_is_case_sensitive_and_lowercase_refuses() -> None:
    with pytest.raises(guard.WindowRefused):
        guard.authorize_window(start="2026-02-02", end="2026-02-03", purpose="training")


def test_the_guard_enumerates_days_itself_so_a_caller_cannot_narrow_the_audit() -> None:
    """Bounds in, calendar out. A caller hands over a range, never a day list."""

    days = guard.calendar_days("2026-02-26", "2026-03-02")
    assert days == (
        "2026-02-26",
        "2026-02-27",
        "2026-02-28",
        "2026-03-01",
        "2026-03-02",
    )


def test_a_reversed_window_raises_rather_than_returning_nothing() -> None:
    with pytest.raises(ValueError):
        guard.calendar_days("2026-02-10", "2026-02-01")


def test_trainable_ranges_are_read_from_the_registry_not_restated() -> None:
    ranges = guard.trainable_ranges()
    ids = {row["partition_id"] for row in ranges}
    assert ids == {
        "train_backfill_2025H2",
        "train_february_2026_unclaimed",
        "train_rolling_may_first_half",
        "train_touched_may18",
    }
    assert all(row["role"] in trainer_partitions.TRAINABLE_ROLES for row in ranges)


def test_march_stays_refused_even_if_a_registry_marks_it_trainable() -> None:
    """`reserved_blackout` is checked BEFORE partition lookup, so a future edit
    to the March partition alone cannot unlock it. Pinned behaviourally by
    building a registry that tries."""

    hostile = trainer_partitions.PartitionRegistry(
        registry_id="hostile_test_registry",
        authored_utc="2026-07-31T00:00:00+00:00",
        partitions=(
            trainer_partitions.Partition(
                partition_id="march_marked_trainable",
                role="TRAIN",
                start="2026-03-01",
                end="2026-03-31",
            ),
        ),
    )
    assert hostile.disposition_for_day("2026-03-15").trainable is False
    with pytest.raises(guard.WindowRefused):
        guard.authorize_window(
            start="2026-03-15",
            end="2026-03-16",
            purpose=guard.PURPOSE_TRAINING,
            registry=hostile,
        )
