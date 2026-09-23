from __future__ import annotations

import datetime as dt
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
import pytest


REPO = Path(__file__).resolve().parents[2]
TOOL = (
    REPO
    / "docs/audits/fable5-vision-audit-20260725/phase18/receipts/"
    "cq_path_pool_grid.py"
)
SPEC = importlib.util.spec_from_file_location("cq_path_pool_grid", TOOL)
assert SPEC and SPEC.loader
cq = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = cq
SPEC.loader.exec_module(cq)


UTC = dt.timezone.utc


def test_m1_slice_is_strictly_after_decision_and_bounded_by_horizon() -> None:
    observations = tuple(
        {
            "time_utc": dt.datetime(2026, 1, 2, 10, minute, tzinfo=UTC).isoformat(),
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.0,
        }
        for minute in range(4)
    )
    series = cq.M1Series(
        tuple(cq._parse_utc(row["time_utc"]) for row in observations),
        observations,
    )

    selected = cq.slice_observations(
        series,
        decision=dt.datetime(2026, 1, 2, 10, 1, tzinfo=UTC),
        horizon=dt.datetime(2026, 1, 2, 10, 2, tzinfo=UTC),
    )

    assert [row["time_utc"] for row in selected] == [observations[2]["time_utc"]]


def test_ohlc_same_bar_is_explicitly_ambiguous_for_conservative_scoring() -> None:
    summary = cq.summarize_ohlc_path(
        observations=[
            {
                "time_utc": "2026-01-02T10:01:00+00:00",
                "open": 100.0,
                "high": 102.0,
                "low": 98.0,
                "close": 100.5,
            }
        ],
        entry=100.0,
        base_distance=1.0,
        side="LONG",
        targets=np.asarray([1.0]),
        stops=np.asarray([1.0]),
        recorded_target_d=1.0,
    )

    assert summary.target_index.tolist() == [0]
    assert summary.stop_index.tolist() == [0]
    assert summary.recorded_target_index == summary.recorded_stop_index == 0
    assert summary.source_mode == "M1_CONSERVATIVE"


def test_ordered_tick_exit_uses_bid_for_long_and_ask_for_short() -> None:
    decision = dt.datetime(2026, 1, 2, 10, 0, tzinfo=UTC)
    series = cq.TickSeries(
        times_us=np.asarray([cq._epoch_us(decision + dt.timedelta(seconds=1))]),
        bid=np.asarray([100.4]),
        ask=np.asarray([101.2]),
    )
    common = {
        "series": series,
        "decision": decision,
        "horizon": decision + dt.timedelta(minutes=120),
        "entry": 100.0,
        "base_distance": 1.0,
        "targets": np.asarray([1.0]),
        "stops": np.asarray([1.0]),
        "recorded_target_d": 1.0,
    }

    long = cq.summarize_tick_path(side="LONG", **common)
    short = cq.summarize_tick_path(side="SHORT", **common)

    assert long is not None and long.target_index.tolist() == [cq.INF_INDEX]
    assert short is not None and short.stop_index.tolist() == [0]


def test_cj_commission_exactly_reprices_through_cn_truth() -> None:
    rows, _ = cq.load_pool_rows()
    masks, _ = cq._split_masks(rows)
    liquidity = np.asarray(
        [
            row["origin_family"] == "liquidity_sweep_reclaim"
            and row["side"] == "LONG"
            for row in rows
        ],
        dtype=bool,
    )

    repriced, report = cq._broker_true_cost_vector(rows, masks, liquidity)

    assert np.array_equal(
        repriced,
        np.asarray([float(row["cost_r"]) for row in rows], dtype=np.float64),
    )
    assert report["status"] == "CJ_COMMISSION_EXACTLY_MATCHES_CN_BROKER_TRUE_REPRICE"
    assert report["rows_repriced"] == report["exact_identity_rows"] == 27_658
    assert report["unpriced_rows"] == report["nonidentity_rows"] == 0
    assert report["token_bound_config_bytes_read"] is False


def test_geometry_look_accounting_is_one_per_cell_not_one_per_stratum() -> None:
    populations = {
        name: {
            "verdict": "NET_NEGATIVE_BOTH_SPLITS",
            "splits": {
                split: {"n": 1, "mean_net_r": -1.0}
                for split in ("TRAIN", "HOLDOUT", "FULL")
            },
        }
        for name in (
            "FULL_POOL",
            "CURRENT_BREAKER_RE_ENTRY",
            "LIQUIDITY_SWEEP_RECLAIM_LONG",
        )
    }
    cells = [
        {
            "cell_id": f"cell-{index}",
            "orientation": "as_declared" if index < 99 else "inverted",
            "target_distance_D": float(index + 1),
            "stop_distance_D": 1.0,
            "populations": populations,
        }
        for index in range(198)
    ]
    recorded = {
        split: {"mean_net_r": -1.0}
        for split in ("TRAIN", "HOLDOUT", "FULL")
    }
    result = {
        "cells": cells,
        "current_breaker_suppression": {"after": recorded, "verdict": "DOES_NOT_SURVIVE"},
        "liquidity_sweep_reclaim_long_broker_true": {
            "recorded_geometry_broker_true": recorded,
        },
        "first_touch_ambiguity": {"frequency": 0.1},
    }

    looks = cq.make_looks(result, {"dates": ["2026-01-02"]})

    assert len(looks) == 201
    geometry = [look for look in looks if look["kind"] == "frozen_geometry"]
    assert len(geometry) == 198
    assert set(geometry[0]["extra"]["populations"]) == set(populations)


@pytest.mark.parametrize("date", ["2026-02-01T00:00:00+00:00", "2026-03-01T00:00:00+00:00"])
def test_forbidden_months_fail_before_analysis(date: str) -> None:
    with pytest.raises(cq.CQRefusal):
        cq._require_january(date, context="test")


def test_repair_fidelity_is_only_the_conservative_per_bar_class_transfer() -> None:
    from src.research_infra.walkforward.fidelity import (
        FidelityBasis,
        FidelityClass,
        fidelity_for,
    )

    record = fidelity_for(cq.REPAIR_SLEEVE)

    assert record.cls is FidelityClass.PER_BAR
    assert record.basis is FidelityBasis.TRANSFERRED_CLASS
    assert record.live_recall == pytest.approx(160 / 167)
    assert record.scoreable(0.50)
    assert "DEFAULT-OFF AND NOT MEASURED DIRECTLY" in record.basis_note
    assert "no live record of its own" in record.basis_note


def test_committed_cq_receipts_close_looks_and_forbidden_boundaries() -> None:
    receipts = TOOL.parent
    grid = json.loads((receipts / "CQ_FROZEN_99_CELL_GRID_V1.json").read_text())
    looks = json.loads((receipts / "CQ_LOOK_LEDGER_RECEIPT_V1.json").read_text())
    gate = json.loads(
        (receipts / "CQ_CURRENT_BREAKER_RATIFIED_GATE_V1.json").read_text()
    )

    assert grid["reported_cells"] == 198
    assert grid["every_declared_cell_reported"] is True
    assert looks["expected_looks"] == looks["session_cq_rows_after"] == 201
    assert looks["all_expected_present"] is True
    assert looks["billed_true_rows"] == looks["non_val_rows"] == 0
    assert looks["february_rows"] == looks["march_rows"] == 0
    assert gate["february_2026_economics_read"] is False
    assert gate["march_2026_outcomes_read"] is False
    assert gate["token_bound_config_bytes_read"] is False
    assert gate["gate_result"]["summary"]["not_evaluable"] == [cq.REPAIR_SLEEVE]
    assert gate["ceremony"]["status"] == "NOT_QUEUED"


def test_cq_graduation_is_one_bill_with_portable_paths() -> None:
    ledger = (
        REPO
        / "docs/audits/fable5-vision-audit-20260725/phase14/receipts/"
        "TRAINING_LANE_GRADUATION_LEDGER.jsonl"
    )
    rows = [json.loads(line) for line in ledger.read_text().splitlines() if line.strip()]
    cq_rows = [row for row in rows if row.get("session") == "Session CQ (wave 18)"]

    assert len(cq_rows) == 1
    row = cq_rows[0]
    assert row["member_name"] == cq.REPAIR_SLEEVE
    assert row["billed_looks"] == 1
    assert row["declared_family_size"] == 58
    assert row["looks_taken_size"] == 56
    assert not Path(row["declaration_path"]).is_absolute()
    assert not Path(row["superseded_declaration"]).is_absolute()
