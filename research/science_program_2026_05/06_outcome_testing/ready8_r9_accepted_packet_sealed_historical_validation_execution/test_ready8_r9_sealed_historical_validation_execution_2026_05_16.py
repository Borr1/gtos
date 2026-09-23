import json
from pathlib import Path

import verify_ready8_r9_sealed_historical_validation_execution_2026_05_16 as verifier


ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-16"


def read_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def count_jsonl(name: str) -> int:
    return sum(1 for _ in iter_jsonl(ROUTE_DIR / name))


def test_required_row_counts():
    assert count_jsonl(f"R10_PARTITION_FREEZE_LEDGER_{DATE}.jsonl") == 182
    assert count_jsonl(f"R10_PACKET_ROW_ADMISSION_EXECUTION_STATUS_LEDGER_{DATE}.jsonl") == 182
    assert count_jsonl(f"R10_HAZ001_VALIDATION_RETEST_RESULT_LEDGER_{DATE}.jsonl") == 143
    assert count_jsonl(f"R10_MAC_INVERSE_AVOID_FILTER_DIAGNOSTIC_RESULT_LEDGER_{DATE}.jsonl") == 32
    assert count_jsonl(f"R10_HAZ005_REPAIRED_ROW_SOURCE_CONTROL_LEDGER_{DATE}.jsonl") == 5
    assert count_jsonl(f"R10_UNC004_SOURCE_CAPTURE_DIAGNOSTIC_IMPLICATION_LEDGER_{DATE}.jsonl") == 1154
    assert count_jsonl(f"R10_REPAIRED_TARGET_CARRY_FORWARD_LEDGER_{DATE}.jsonl") == 5320
    assert count_jsonl(f"R10_REPAIRED_TARGET_NEUTRAL_MOVEMENT_METRIC_LEDGER_{DATE}.jsonl") == 5320
    assert count_jsonl(f"R10_FAILURE_INTELLIGENCE_LEDGER_{DATE}.jsonl") == 2641
    assert count_jsonl(f"R10_PROXY_R_EXPECTANCY_GEOMETRY_COVERAGE_LEDGER_{DATE}.jsonl") == 5502
    assert count_jsonl(f"R10_TARGET_STOP_HIT_MISS_AMBIGUOUS_FAIL_CLOSED_LEDGER_{DATE}.jsonl") == 5502


def test_partition_status_coverage_and_safe_flags():
    expected_flags = {
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    statuses = set()
    for row in iter_jsonl(ROUTE_DIR / f"R10_PACKET_ROW_ADMISSION_EXECUTION_STATUS_LEDGER_{DATE}.jsonl"):
        for key, value in expected_flags.items():
            assert row[key] == value
        statuses.update(row["execution_statuses"])
    assert "SEALED_HISTORICAL_VALIDATION_EXECUTABLE" in statuses
    assert "STRESS_ROBUSTNESS_EXECUTABLE" in statuses
    assert "FORWARD_SHADOW_CAPTURE_REQUIRED" in statuses
    assert "SOURCE_CONTROL_ONLY" in statuses
    assert "INVERSE_AVOID_FILTER_DIAGNOSTIC_ONLY" in statuses
    assert "CONTROL_RESIDUAL_FAILURE_INTELLIGENCE_ONLY" in statuses


def test_repaired_target_neutral_metrics_and_r_geometry_boundaries():
    rows = list(iter_jsonl(ROUTE_DIR / f"R10_REPAIRED_TARGET_NEUTRAL_MOVEMENT_METRIC_LEDGER_{DATE}.jsonl"))
    assert len(rows) == 5320
    assert all(row["neutral_metric_status"] == "SOURCE_BOUND_NEUTRAL_TARGET_MOVEMENT_COMPUTED" for row in rows)
    assert all(row["r_style_geometry_status"] == "FAIL_CLOSED_MISSING_SIDE_STOP_TARGET_FILLABILITY_FOR_R_STYLE_RESULT" for row in rows)
    assert any(row["target_family_id"] == "neutral_high_low_excursion_m15_horizons_v1" for row in rows)
    assert any(row["target_family_id"] == "neutral_close_to_close_return_m15_horizons_v1" for row in rows)


def test_target_stop_rows_are_ambiguous_not_fabricated():
    rows = list(iter_jsonl(ROUTE_DIR / f"R10_TARGET_STOP_HIT_MISS_AMBIGUOUS_FAIL_CLOSED_LEDGER_{DATE}.jsonl"))
    assert len(rows) == 5502
    assert all(row["hit_miss_ambiguous_fail_closed"] == "AMBIGUOUS" for row in rows)
    assert all(row["target_hit"] is None and row["stop_hit"] is None for row in rows)


def test_terminal_decision_and_completion():
    decision = read_json(ROUTE_DIR / f"R10_DECISION_LEDGER_{DATE}.json")
    assert decision["terminal_decision"] == "MATERIALIZED_READY8_R9_ACCEPTED_PACKET_SEALED_HISTORICAL_VALIDATION_RESULT_G12_AUDIT_REQUIRED_NO_PROMOTION"
    assert decision["can_promote"] is False
    assert decision["validation_or_live_use_allowed"] is False

    completion = read_json(ROUTE_DIR / f"R10_COMPLETION_AUDIT_{DATE}.json")
    assert completion["completion_standard_met"] is True
    assert completion["same_evidence_class_intelligence_remaining"] == 0


def test_verifier_passes_current_artifacts_without_recorded_test_gate():
    result = verifier.verify(update=False, require_focused_tests=False)
    assert result["ok"], result["errors"]
