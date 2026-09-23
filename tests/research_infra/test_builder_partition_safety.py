"""The builder's partition refusal and label-span emission, end to end.

Complements `test_trainer_partitions.py` (registry logic) and `test_trainer_folds.py` (fold logic)
by exercising the path a user actually invokes: ledgers on disk -> frame.
"""

from __future__ import annotations

import json

import pytest

from src.research_infra.learned_edge_dataset_builder import (
    SealedPartitionError,
    build_training_frame,
)
from src.research_infra.trainer_partitions import DEFAULT_REGISTRY

CANDIDATE = "TESTROUTE_{day}_CANDIDATE_MICROSCOPE_LEDGER.jsonl"
MISSED = "TESTROUTE_{day}_MISSED_OPPORTUNITY_LEDGER.jsonl"


def _write_day(route_dir, day: str, *, n: int = 3, filled: bool = True):
    """One replay day's candidate + missed ledgers, in the real field shapes."""
    iso = f"{day[:4]}-{day[4:6]}-{day[6:]}"
    cands, misses = [], []
    for i in range(n):
        cid = f"c_{day}_{i}"
        cands.append(
            {
                "candidate_id": cid,
                "trading_day": iso,
                "decision_time_utc": f"{iso}T09:{i:02d}:00+00:00",
                "symbol": "EURUSD",
                "side": "LONG",
                "entry_price": 1.1,
                "stop_loss": 1.09,
                "entry_reference": 1.1,
                "candidate_probability": 0.5,
                "candidate_ev_r": 0.1,
                "expected_cost_r": 0.1,
                "risk_reward_ratio": 1.5,
            }
        )
        row = {
            "candidate_id": cid,
            "trading_day": iso,
            "decision_time_utc": f"{iso}T09:{i:02d}:00+00:00",
            "chunk_end_day": iso,
            "opportunity_path_scored": True,
            "net_proxy_r": 1.2,
        }
        if filled:
            row["opportunity_close_reason"] = "target_reached_before_stop"
            row["counterfactual_order_close_time_utc"] = f"{iso}T11:{i:02d}:00+00:00"
        else:
            # The real never-filled shape: no close instant, resolved inside the chunk.
            row["opportunity_close_reason"] = "not_filled_no_trade"
        misses.append(row)

    (route_dir / CANDIDATE.format(day=day)).write_text(
        "\n".join(json.dumps(r) for r in cands) + "\n"
    )
    (route_dir / MISSED.format(day=day)).write_text(
        "\n".join(json.dumps(r) for r in misses) + "\n"
    )


# --------------------------------------------------------------------------------------------
# Refusal
# --------------------------------------------------------------------------------------------
def test_a_march_2026_day_is_refused_by_default(tmp_path):
    """The headline guarantee, through the real entry point with no registry argument at all.

    The old default (`registry_path=None`) DISABLED the check; this asserts the new default
    enforces it.
    """
    _write_day(tmp_path, "20260316")
    with pytest.raises(SealedPartitionError, match="refused partition class"):
        build_training_frame([tmp_path])


def test_a_sealed_b7_5_window_day_is_refused(tmp_path):
    _write_day(tmp_path, "20260115")  # inside B7.5's sealed January development window
    with pytest.raises(SealedPartitionError):
        build_training_frame([tmp_path])


def test_a_day_no_partition_covers_is_refused(tmp_path):
    """The fail-open case the original admitted silently: role None != 'SEALED', so it passed."""
    _write_day(tmp_path, "20240101")
    with pytest.raises(SealedPartitionError, match="day_outside_every_partition"):
        build_training_frame([tmp_path])


def test_the_refusal_names_every_offending_day_not_just_one(tmp_path):
    for day in ("20260316", "20260317", "20260318"):
        _write_day(tmp_path, day)
    with pytest.raises(SealedPartitionError) as exc:
        build_training_frame([tmp_path])
    for day in ("2026-03-16", "2026-03-17", "2026-03-18"):
        assert day in str(exc.value)


def test_passing_the_v1_registry_still_cannot_admit_march(tmp_path):
    """v1 resolves March to TRAIN. Loading it through the validating loader does not help it:
    the reserved blackout is a property of the registry class, not of the file."""
    _write_day(tmp_path, "20260316")
    v1 = (
        "research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/"
        "ULTIMATE_EDGE_PARTITION_REGISTRY.jsonl"
    )
    with pytest.raises(SealedPartitionError):
        build_training_frame([tmp_path], registry_path=v1)


# --------------------------------------------------------------------------------------------
# Admission, so the refusals above are not vacuous
# --------------------------------------------------------------------------------------------
def test_a_trainable_day_builds_and_is_annotated(tmp_path):
    _write_day(tmp_path, "20260210")  # February 2026 is TRAIN
    result = build_training_frame([tmp_path])
    rows = result["rows"]
    assert rows
    for row in rows:
        assert row["partition_role"] == "TRAIN"
        assert row["partition_trainable"] is True
        assert row["partition_refusal"] is None
    header = result["header"]
    assert header["partition_registry_id"] == DEFAULT_REGISTRY.registry_id
    assert header["partition_registry_digest_sha256"] == DEFAULT_REGISTRY.digest()


def test_a_validation_day_is_admitted_but_not_trainable(tmp_path):
    """VALIDATION rows belong in a frame (analysis) but must never be fitted on."""
    _write_day(tmp_path, "20260520")
    rows = build_training_frame([tmp_path])["rows"]
    assert rows
    assert all(r["partition_role"] == "VALIDATION" for r in rows)
    assert all(r["partition_trainable"] is False for r in rows)


# --------------------------------------------------------------------------------------------
# Label spans
# --------------------------------------------------------------------------------------------
def test_filled_rows_carry_a_measured_label_span(tmp_path):
    _write_day(tmp_path, "20260210", filled=True)
    rows = build_training_frame([tmp_path])["rows"]
    assert rows
    for row in rows:
        assert row["label_span_status"] == "measured"
        assert row["label_span_start_utc"] < row["label_span_end_utc"]


def test_never_filled_rows_are_bounded_by_the_chunk_day(tmp_path):
    """4,909 of 4,910 real rows without a close time are never-filled. Their label still resolves
    inside the chunk, so the span end is derivable rather than unknown."""
    _write_day(tmp_path, "20260210", filled=False)
    rows = build_training_frame([tmp_path])["rows"]
    assert rows
    for row in rows:
        assert row["label_span_status"] == "bounded_by_chunk_day"
        assert row["label_span_end_utc"].startswith("2026-02-10T23:59:59")


def test_the_header_counts_span_statuses(tmp_path):
    _write_day(tmp_path, "20260210", n=2, filled=True)
    _write_day(tmp_path, "20260211", n=2, filled=False)
    header = build_training_frame([tmp_path])["header"]
    counts = header["label_span_status_counts"]
    assert counts.get("measured") == 2
    assert counts.get("bounded_by_chunk_day") == 2
