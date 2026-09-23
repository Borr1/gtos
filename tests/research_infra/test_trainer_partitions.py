"""Fail-closed behaviour of the trainer partition registry.

These are BEHAVIOURAL tests: they call the lookup and assert on what it returns, never on the
source text. A test that greps a module for "RESERVED_UNREAD" passes against an implementation
that computes the wrong answer (`CLAUDE.md` section 6).
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pytest

from src.research_infra.trainer_partitions import (
    DEFAULT_REGISTRY,
    Partition,
    PartitionRefusal,
    PartitionRegistry,
    RESERVED_UNREAD_MARCH_2026,
    TRAINABLE_ROLES,
)

V1_REGISTRY = Path(
    "research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/"
    "ULTIMATE_EDGE_PARTITION_REGISTRY.jsonl"
)


# --------------------------------------------------------------------------------------------
# The March hazard
# --------------------------------------------------------------------------------------------
@pytest.mark.parametrize("day", ["2026-03-01", "2026-03-02", "2026-03-16", "2026-03-30", "2026-03-31"])
def test_every_march_2026_day_is_refused(day):
    disp = DEFAULT_REGISTRY.disposition_for_day(day)
    assert disp.trainable is False
    assert disp.refusal == "day_inside_reserved_blackout"


def test_march_refusal_survives_a_partition_that_says_train():
    """The blackout is checked BEFORE partitions, so a TRAIN range spanning March cannot unlock it.

    This is the exact shape of the v1 defect: `train_backfill_2025H2_2026Q1` covered
    2025-06-02..2026-04-17 and therefore all of March, and nothing overrode it.
    """
    hostile = PartitionRegistry(
        registry_id="hostile",
        authored_utc="2026-07-29T00:00:00+00:00",
        partitions=(
            Partition(
                partition_id="swallows_march",
                role="TRAIN",
                start="2025-06-02",
                end="2026-04-17",
            ),
        ),
    )
    assert hostile.disposition_for_day("2026-03-16").trainable is False
    assert hostile.disposition_for_day("2026-03-16").refusal == "day_inside_reserved_blackout"
    # ... and the same registry DOES admit a day outside the blackout, so the refusal above is
    # not just "this registry refuses everything".
    assert hostile.disposition_for_day("2026-02-16").trainable is True


def test_v1_registry_loads_and_still_cannot_leak_march():
    """The real v1 file, through the validating loader, is neutered rather than trusted."""
    v1 = PartitionRegistry.load(V1_REGISTRY)
    assert len(v1.partitions) == 10
    for day in ("2026-03-01", "2026-03-16", "2026-03-31"):
        assert v1.disposition_for_day(day).trainable is False


def test_v1_raw_lookup_really_did_say_train():
    """Guards the claim the rewrite is justified by. If this ever fails, the story changed."""
    from src.research_infra.learned_edge_dataset_builder import (
        load_partition_registry,
        partition_role_for_day,
    )

    rows = load_partition_registry(V1_REGISTRY)
    assert partition_role_for_day("2026-03-16", rows) == (
        "TRAIN",
        "train_backfill_2025H2_2026Q1",
    )


def test_march_partition_records_its_prior_consumption():
    """March is reserved but NOT pristine, and the registry must say so in a machine-readable
    field rather than only in prose. 22 March 2026 days were already fitted (B514)."""
    march = next(p for p in DEFAULT_REGISTRY.partitions if p.role == "RESERVED_UNREAD")
    assert march.prior_consumption
    assert "ULTIMATE_EDGE_TRAIN_DAY_PROGRESS_LEDGER" in march.prior_consumption
    assert march.as_dict()["prior_consumption"]


# --------------------------------------------------------------------------------------------
# Fail-closed, in general
# --------------------------------------------------------------------------------------------
def test_day_covered_by_no_partition_is_refused_not_none():
    """The inversion of v1's behaviour. v1 returned (None, None) and the only downstream check
    was `role == "SEALED"`, so uncovered days passed."""
    for day in ("2025-01-01", "2026-05-30", "2026-05-31"):
        disp = DEFAULT_REGISTRY.disposition_for_day(day)
        assert disp.trainable is False
        assert disp.refusal == "day_outside_every_partition"
        assert disp.role is None


@pytest.mark.parametrize(
    "day,role",
    [
        ("2026-01-15", "SEALED"),
        ("2026-04-10", "SEALED"),
        ("2026-05-14", "SEALED"),
        ("2026-06-04", "SEALED"),
        ("2026-05-02", "STRESS"),
        ("2026-05-25", "VALIDATION"),
        ("2026-07-29", "FORWARD"),
    ],
)
def test_non_trainable_roles_are_refused(day, role):
    disp = DEFAULT_REGISTRY.disposition_for_day(day)
    assert disp.role == role
    assert disp.trainable is False
    assert disp.refusal == f"role_not_trainable:{role}"


def test_live_trading_period_is_forward_and_never_trainable():
    """FTMO went live 2026-07-29. Live days must not be able to become training rows."""
    for day in ("2026-07-29", "2026-08-15", "2027-01-01", "2030-06-01"):
        assert DEFAULT_REGISTRY.disposition_for_day(day).role == "FORWARD"
        assert DEFAULT_REGISTRY.disposition_for_day(day).trainable is False


def test_trainable_days_exist_so_the_registry_is_not_vacuous():
    """A registry that refuses everything would pass every test above and be useless."""
    ok = [d for d in ("2025-07-15", "2026-02-14", "2026-05-07", "2026-05-18")
          if DEFAULT_REGISTRY.disposition_for_day(d).trainable]
    assert len(ok) == 4


def test_assert_trainable_reports_every_offender_not_just_the_first():
    with pytest.raises(PartitionRefusal) as exc:
        DEFAULT_REGISTRY.assert_trainable(
            ["2026-02-10", "2026-03-05", "2026-03-06", "2026-01-15", "2025-01-01"]
        )
    assert len(exc.value.refusals) == 4
    reasons = {r.refusal for r in exc.value.refusals}
    assert reasons == {
        "day_inside_reserved_blackout",
        "role_not_trainable:SEALED",
        "day_outside_every_partition",
    }


def test_partition_days_trainable_splits_without_raising():
    keep, drop = DEFAULT_REGISTRY.partition_days_trainable(
        ["2026-02-10", "2026-03-05", "2026-01-15"]
    )
    assert keep == ["2026-02-10"]
    assert {d.day for d in drop} == {"2026-03-05", "2026-01-15"}


# --------------------------------------------------------------------------------------------
# Validation at construction
# --------------------------------------------------------------------------------------------
def test_overlapping_partitions_are_rejected():
    with pytest.raises(ValueError, match="overlapping partitions"):
        PartitionRegistry(
            registry_id="bad",
            authored_utc="",
            partitions=(
                Partition("a", "TRAIN", "2025-01-01", "2025-06-30"),
                Partition("b", "SEALED", "2025-06-01", "2025-12-31"),
            ),
        )


def test_excluded_days_make_a_range_intersection_legal():
    """Overlap means a day covered by BOTH, not a bare range intersection. v1 relies on this and
    a range-only check wrongly refused to load it (B516)."""
    reg = PartitionRegistry(
        registry_id="ok",
        authored_utc="",
        partitions=(
            Partition("outer", "VALIDATION", "2025-06-01", "2025-06-30",
                      excluded_days=("2025-06-15",)),
            Partition("inner", "TRAIN", "2025-06-15", "2025-06-15"),
        ),
    )
    assert reg.disposition_for_day("2025-06-15").partition_id == "inner"
    assert reg.disposition_for_day("2025-06-14").partition_id == "outer"


def test_role_outside_the_closed_vocabulary_is_rejected():
    with pytest.raises(ValueError, match="not in"):
        Partition("x", "TRAIN_DEV", "2025-01-01", "2025-01-02")


def test_reversed_range_and_stray_excluded_day_are_rejected():
    with pytest.raises(ValueError, match="reversed"):
        Partition("x", "TRAIN", "2025-06-30", "2025-01-01")
    with pytest.raises(ValueError, match="outside range"):
        Partition("x", "TRAIN", "2025-01-01", "2025-01-31", excluded_days=("2025-02-05",))


def test_duplicate_partition_id_is_rejected():
    with pytest.raises(ValueError, match="duplicate"):
        PartitionRegistry(
            registry_id="bad",
            authored_utc="",
            partitions=(
                Partition("same", "TRAIN", "2025-01-01", "2025-01-31"),
                Partition("same", "TRAIN", "2025-02-01", "2025-02-28"),
            ),
        )


def test_default_registry_has_no_overlaps_and_a_stable_digest():
    # Construction already enforces non-overlap; assert the digest is deterministic so a
    # silently-edited range is detectable.
    assert DEFAULT_REGISTRY.digest() == DEFAULT_REGISTRY.digest()
    reloaded = PartitionRegistry.from_rows(
        [json.loads(line) for line in DEFAULT_REGISTRY.to_jsonl().splitlines()]
    )
    assert reloaded.digest() == DEFAULT_REGISTRY.digest()


def test_only_train_roles_are_trainable():
    assert TRAINABLE_ROLES == frozenset({"TRAIN", "TRAIN_DEVELOPMENT_GRADE"})


# --------------------------------------------------------------------------------------------
# The coupling to Session W's gate, CHECKED rather than asserted in a comment
# --------------------------------------------------------------------------------------------
def test_blackout_agrees_with_gate_spec():
    """`walkforward.spec.GateSpec` carries the same March blackout for the admission gate. The
    two are independent modules with independent defaults; if they ever diverge, one of the two
    lanes silently stops protecting March. `spec.py:58-61` records why a coupling should be
    checked, not claimed."""
    from src.research_infra.walkforward.spec import GateSpec

    gate_default = GateSpec.__dataclass_fields__["reserved_blackout"].default
    assert tuple(tuple(r) for r in gate_default) == (RESERVED_UNREAD_MARCH_2026,)
    assert DEFAULT_REGISTRY.reserved_blackout == (RESERVED_UNREAD_MARCH_2026,)


def test_march_blackout_matches_the_b7_5_contract_window():
    """The dates are not a choice; they come from B7.5's own window binding."""
    contract = Path(
        "research/operations/final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16/"
        "B7_5_POST_ACCELERATION_DECISION_CONTRACT.json"
    )
    if not contract.is_file():  # sparse checkout may exclude it
        pytest.skip("B7.5 contract not hydrated in this worktree")
    data = json.loads(contract.read_text())
    march = next(
        b for b in data["window_source_plan_bindings"]
        if b["window_id"] == "untouched_treatment_challenge_march"
    )
    assert (march["start"], march["end"]) == RESERVED_UNREAD_MARCH_2026
    assert march["role"] == "untouched_for_this_treatment_historical_challenge"
    assert data["march_outcome_read"] is False


def test_date_types_are_accepted_consistently():
    for value in ("2026-03-16", dt.date(2026, 3, 16), dt.datetime(2026, 3, 16, 13, 5)):
        assert DEFAULT_REGISTRY.disposition_for_day(value).trainable is False
