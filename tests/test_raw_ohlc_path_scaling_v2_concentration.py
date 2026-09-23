from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import pytest

from scripts import audit_raw_ohlc_path_scaling_v2_concentration as mod


@pytest.fixture
def tmp_path():
    path = Path(".test_tmp") / f"raw_ohlc_v2_concentration_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def _row(event_key: str, variant: str, net: float | None, **extra):
    return {
        "event_key": event_key,
        "variant_id": variant,
        "net_r_by_cost": {"0.05": net},
        "symbol": extra.get("symbol", "NAS100"),
        "session": extra.get("session", "ny"),
        "selected_timeframe": extra.get("selected_timeframe", "M5"),
        "mechanical_side": extra.get("side", "LONG"),
        "role": extra.get("role", "dominance_watchlist"),
        "raw_cohort_key": extra.get("raw_cohort_key", "NAS100|ny|bullish|D1"),
    }


def test_pairwise_stats_recompute_only_paired_resolved_rows():
    by_event = {
        "a": {
            mod.BASELINE_VARIANT: _row("a", mod.BASELINE_VARIANT, 0.5),
            "STRUCT_OB_BOUNDARY_V2": _row("a", "STRUCT_OB_BOUNDARY_V2", 1.0),
        },
        "b": {
            mod.BASELINE_VARIANT: _row("b", mod.BASELINE_VARIANT, -1.0),
            "STRUCT_OB_BOUNDARY_V2": _row("b", "STRUCT_OB_BOUNDARY_V2", -1.0),
        },
        "c": {
            mod.BASELINE_VARIANT: _row("c", mod.BASELINE_VARIANT, 1.0),
            "STRUCT_OB_BOUNDARY_V2": _row("c", "STRUCT_OB_BOUNDARY_V2", None),
        },
    }

    stats = mod.build_pairwise_stats(by_event)["STRUCT_OB_BOUNDARY_V2"].to_summary()

    assert stats["paired_resolved_n"] == 2
    assert stats["sum_delta_candidate_minus_baseline"] == 0.5
    assert stats["mean_delta_candidate_minus_baseline"] == 0.25
    assert stats["candidate_better_n"] == 1
    assert stats["tie_n"] == 1


def test_compare_to_summary_flags_exact_field_mismatch():
    recomputed = {"STRUCT_OB_BOUNDARY_V2": mod.PairStats()}
    recomputed["STRUCT_OB_BOUNDARY_V2"].add(baseline_r=0.0, candidate_r=1.0)
    summary = {
        "STRUCT_OB_BOUNDARY_V2": {
            "paired_resolved_n": 1,
            "mean_delta_candidate_minus_baseline": 0.5,
            "sum_delta_candidate_minus_baseline": 1.0,
            "candidate_better_n": 1,
            "baseline_better_n": 0,
            "tie_n": 0,
        }
    }

    rows = mod.compare_to_summary(recomputed, summary)

    assert rows[0]["all_fields_passed"] is False
    assert rows[0]["field_results"]["mean_delta_candidate_minus_baseline"]["passed"] is False
    assert rows[0]["field_results"]["sum_delta_candidate_minus_baseline"]["passed"] is True


def test_concentration_broadness_reports_top_share():
    rows = [
        {"sum_delta_candidate_minus_baseline": 6.0},
        {"sum_delta_candidate_minus_baseline": 3.0},
        {"sum_delta_candidate_minus_baseline": 1.0},
        {"sum_delta_candidate_minus_baseline": -2.0},
    ]

    broadness = mod.concentration_broadness(rows, "raw_cohort_key")

    assert broadness["positive_bucket_count"] == 3
    assert broadness["negative_bucket_count"] == 1
    assert broadness["positive_sum_delta"] == 10.0
    assert broadness["top_positive_share"] == 0.6
