from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.research_infra import (
    replay_acceleration_task3_exact_cache_acceptance as task3,
)
from src.research_infra import (
    replay_acceleration_task4_shared_preparation_acceptance as task4,
)


def _task4_summary() -> dict:
    rows = []
    for index, expected in enumerate(task3._EXPECTED_CACHE_ROWS):
        audit = {
            "schema": "gtos.replay_acceleration.campaign_exact_cache.v1",
            "status": "exact_cache_boundary_valid",
            "config_root_sha256": "a" * 64,
            "risk_profile_path": "config/profiles/ftmo.yaml",
            "risk_profile_sha256": "b" * 64,
            "expected_risk_profile_sha256": "b" * 64,
            "risk_profile_payload_root_sha256": "c" * 64,
            "miss_counts": copy.deepcopy(expected["miss_counts"]),
            "cached_symbol_counts": copy.deepcopy(
                expected["cached_symbol_counts"]
            ),
            "live_broker_authority": False,
            "broker_mutation_enabled": False,
        }
        if index == 1:
            audit[task4.MARKET_STATE_CACHE_KEY] = copy.deepcopy(
                task4.EXPECTED_MARKET_STATE_CACHE
            )
        rows.append(
            {
                "start_day": expected["day"],
                "end_day": expected["day"],
                "campaign_exact_cache": audit,
            }
        )
    return {"progress_rows": rows}


def test_task4_cache_audit_reconciles_every_dense_symbol_window() -> None:
    result = task4.validate_task4_cache_audits(_task4_summary())

    assert result["status"] == (
        "TASK4_SHARED_MARKET_STATE_CACHE_BOUNDED_AND_EXACT"
    )
    assert result["m15_cache_enabled"] is False
    assert result["dense_symbol_window_count"] == 2304
    assert result["closed_timeframe_request_count"] == 6912
    assert result["closed_timeframe_build_count"] == 799
    assert result["closed_timeframe_cache_hit_count"] == 6113
    assert result["per_timeframe"]["D1"]["exact_state_builds"] == 48
    assert result["per_timeframe"]["H4"]["exact_state_builds"] == 168
    assert result["per_timeframe"]["H1"]["exact_state_builds"] == 583


@pytest.mark.parametrize(
    "mutate",
    (
        lambda summary: summary["progress_rows"][0][
            "campaign_exact_cache"
        ].update({task4.MARKET_STATE_CACHE_KEY: {}}),
        lambda summary: summary["progress_rows"][1][
            "campaign_exact_cache"
        ][task4.MARKET_STATE_CACHE_KEY].update({"h1_builds": 575}),
        lambda summary: summary["progress_rows"][1][
            "campaign_exact_cache"
        ][task4.MARKET_STATE_CACHE_KEY].update({"future_cache_mode": True}),
    ),
)
def test_task4_cache_audit_fails_closed_on_unknown_or_unreconciled_state(
    mutate,
) -> None:
    summary = _task4_summary()
    mutate(summary)

    with pytest.raises(task3.Task3ExactCacheRejected, match="task4_"):
        task4.validate_task4_cache_audits(summary)


def test_task4_expected_counts_are_recomputed_from_reference_source_identity(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    expected = {
        "d1_hits": 1,
        "d1_misses": 1,
        "d1_builds": 1,
        "d1_evictions": 0,
        "d1_entries": 1,
        "h4_hits": 1,
        "h4_misses": 1,
        "h4_builds": 1,
        "h4_evictions": 0,
        "h4_entries": 1,
        "h1_hits": 0,
        "h1_misses": 2,
        "h1_builds": 2,
        "h1_evictions": 1,
        "h1_entries": 1,
    }
    monkeypatch.setattr(task4, "DENSE_SYMBOL_WINDOWS", 2)
    monkeypatch.setattr(task4, "EXPECTED_MARKET_STATE_CACHE", expected)
    path = task4.semantic._role_path(tmp_path, "decision")
    common = {
        "raw_data_status": (
            "live_equivalent_raw_data_built_and_mso_computed"
        ),
        "symbol": "XAUUSD",
        "source_hashes_by_timeframe": {
            "D1": "a" * 64,
            "H4": "b" * 64,
            "H1": "c" * 64,
        },
        "source_paths_by_timeframe": {
            "D1": "/fixture/d1.csv",
            "H4": "/fixture/h4.csv",
            "H1": "/fixture/h1.csv",
        },
        "decision_rows_used_by_timeframe": {
            "D1": 30,
            "H4": 80,
            "H1": 168,
        },
    }
    rows = [
        {
            **common,
            "decision_max_source_time_utc_by_timeframe": {
                "D1": "2026-01-01T00:00:00+00:00",
                "H4": "2026-01-02T00:00:00+00:00",
                "H1": "2026-01-02T00:00:00+00:00",
            },
        },
        {
            **common,
            "decision_max_source_time_utc_by_timeframe": {
                "D1": "2026-01-01T00:00:00+00:00",
                "H4": "2026-01-02T00:00:00+00:00",
                "H1": "2026-01-02T01:00:00+00:00",
            },
        },
    ]
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )

    actual, source = task4.derive_expected_market_state_cache(tmp_path)

    assert actual == expected
    assert source["successful_symbol_window_rows"] == 2
    assert source["causal_or_economic_fields_read"] is False
    assert len(source["sha256"]) == 64
