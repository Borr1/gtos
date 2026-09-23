from __future__ import annotations

import math
from datetime import datetime, timezone

from src.research_infra.validation_anti_overfit_v4 import (
    brier_score,
    build_purged_embargoed_split_ledger,
    calibration_fixture_rows,
    calibration_metric_result,
    concentration_rows,
    logloss,
    normalize_validation_population,
    reliability_bins,
    source_gap_rows,
)


def test_calibration_metrics_are_computed_from_fixture_without_runtime_flags() -> None:
    rows = calibration_fixture_rows()
    result = calibration_metric_result(rows)

    assert result["validation_result_status"] is False
    assert result["outcome_result_rows_status"] is False
    assert result["broker_runtime_change_status"] is False
    assert set(result["metrics"]) == {"brier", "logloss", "ece", "reliability_bins"}
    assert result["metrics"]["brier"] == brier_score(
        [row["prediction"] for row in rows],
        [row["label"] for row in rows],
    )
    assert result["metrics"]["logloss"] == logloss(
        [row["prediction"] for row in rows],
        [row["label"] for row in rows],
    )
    assert len(result["metrics"]["reliability_bins"]) == 10


def test_reliability_bins_include_probability_one_in_last_bin() -> None:
    bins = reliability_bins([0.0, 0.1, 0.99, 1.0], [0, 0, 1, 1], bin_count=10)

    assert bins[0]["row_count"] == 1
    assert bins[1]["row_count"] == 1
    assert bins[9]["row_count"] == 2
    assert math.isclose(sum(row["row_fraction"] for row in bins), 1.0)


def test_split_ledger_preserves_all_rows_and_embargoes_boundaries() -> None:
    broker_rows = []
    for idx in range(10):
        broker_rows.append(
            {
                "row_id": f"broker:{idx}",
                "symbol": "XAUUSD",
                "side": "BUY" if idx % 2 else "SELL",
                "time_window": {"entry_time_utc": datetime(2026, 1, idx + 1, tzinfo=timezone.utc).isoformat()},
                "evidence_class": "broker-real PnL",
                "metric_fields_used": {"win_loss": "win" if idx % 2 else "loss", "broker_net_cash_from_deals": 10 - idx},
            }
        )
    population = normalize_validation_population(broker_rows, [])
    splits = build_purged_embargoed_split_ledger(population, embargo_minutes=1440)

    assert len(splits) == len(population)
    assert len({row["population_row_id"] for row in splits}) == len(population)
    assert {row["time_split_walk_forward_partition"] for row in splits} >= {
        "discovery_train",
        "validation_selection",
        "sealed_test",
    }
    assert any(row["purge_embargo_status"].startswith("purged") for row in splits)
    assert all(row["broker_runtime_change_status"] is False for row in splits)


def test_concentration_and_source_gap_rows_keep_full_group_context() -> None:
    broker_rows = [
        {
            "row_id": "b1",
            "symbol": "XAUUSD",
            "side": "BUY",
            "time_window": {"entry_time_utc": "2026-01-01T00:00:00+00:00"},
            "evidence_class": "broker-real PnL",
            "metric_fields_used": {"win_loss": "win", "broker_net_cash_from_deals": 100.0},
            "missing_fields": ["exact_r"],
        },
        {
            "row_id": "b2",
            "symbol": "XAUUSD",
            "side": "SELL",
            "time_window": {"entry_time_utc": "2026-01-02T00:00:00+00:00"},
            "evidence_class": "broker-real PnL",
            "metric_fields_used": {"win_loss": "loss", "broker_net_cash_from_deals": -40.0},
            "missing_fields": ["mfe_r"],
        },
    ]
    candidate_rows = [
        {
            "row_id": "c1",
            "symbol": "AUDJPY",
            "side": "LONG",
            "time_window": "2026-01-03T00:00:00Z",
            "source_family": "wave1a_candidate_trade_record",
            "metric_fields_used": {"expectancy_r_source_bound": 0.2},
            "missing_fields": ["counterfactual_path_outcome"],
        }
    ]
    population = normalize_validation_population(broker_rows, candidate_rows)

    groups = concentration_rows(population)
    gaps = source_gap_rows(population)

    assert any(row["group_family"] == "symbol" and row["group_key"] == "XAUUSD" for row in groups)
    assert any(row["gap_family"] == "missing_field:exact_r" for row in gaps)
    assert any(row["gap_family"] == "missing_asof_label_or_non_outcome_source" for row in gaps)
