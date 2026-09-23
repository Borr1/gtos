from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


FREEZE_DIR = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder"
)
FREEZE_LEDGER = (
    FREEZE_DIR / "GTOS_VNEXT_FINAL_CONVERSION_FREEZE_CLASSIFICATION_LEDGER_2026-05-23.jsonl"
)
FREEZE_SUMMARY = (
    FREEZE_DIR / "GTOS_VNEXT_FINAL_CONVERSION_FREEZE_SUMMARY_2026-05-23.json"
)
FREEZE_REPORT = (
    FREEZE_DIR / "GTOS_VNEXT_FINAL_CONVERSION_FREEZE_REPORT_2026-05-23.md"
)


def _jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_final_conversion_freeze_classifies_all_remaining_residue_without_runtime_pressure():
    rows = _jsonl(FREEZE_LEDGER)
    summary = json.loads(FREEZE_SUMMARY.read_text(encoding="utf-8"))

    assert len(rows) == summary["pre_freeze_open_not_started_units"] == 1639
    assert summary["total_units"] == 13571
    assert summary["pre_freeze_closed_units"] == 11932
    assert summary["final_unclassified_open_units"] == 0
    assert summary["final_freeze_coverage_pct"] == 100.0
    assert summary["freeze_killed_units"] == 1157
    assert summary["freeze_parked_units"] == 482
    assert summary["freeze_post_freeze_candidate_units"] == 0
    assert summary["freeze_class_counts"] == {
        "LEGACY_OR_STALE_NON_OVERRIDE_PARK": 402,
        "NEEDS_USER_DECISION_BEFORE_RUNTIME": 7,
        "REPLAY_ATTRIBUTION_ONLY_PARK": 73,
        "WRAPPER_SUPPORT_CHILDREN_ALREADY_HANDLED_KILL": 1157,
    }
    assert summary["closure_action_counts"] == {
        "kill_with_computed_evidence": 1157,
        "park_for_replay_measurement": 73,
        "park_pending_user_decision": 7,
        "park_without_runtime_pressure": 402,
    }
    assert summary["row_bearing_counts"] == {
        "non_row_bearing": 921,
        "row_bearing": 718,
    }
    assert summary["anchor_quality_counts"] == {
        "anchored": 1434,
        "blank_or_unusable_anchor": 205,
    }
    assert summary["runtime_decision_counts"] == {
        "AVOID": 57896,
        "FOLLOW": 34554,
        "MIXED": 278294,
    }

    assert Counter(row["freeze_class"] for row in rows) == summary[
        "freeze_class_counts"
    ]
    assert Counter(row["closure_action"] for row in rows) == summary[
        "closure_action_counts"
    ]
    assert Counter(row["post_freeze_candidate_signal"] for row in rows) == {
        "": 1136,
        "direct_runtime_surface": 434,
        "source_repair_or_guard": 69,
    }
    assert not any(
        row["freeze_class"]
        in {
            "DIRECT_RUNTIME_CONVERSION_REQUIRED",
            "TESTED_SOURCE_REPAIR_OR_GUARD_REQUIRED",
        }
        for row in rows
    )
    assert all(row["pre_freeze_conversion_state"] == "NOT_STARTED" for row in rows)
    assert all(row["runtime_pressure_allowed"] is False for row in rows)
    assert all(row["candidate_use_allowed_now"] is False for row in rows)
    assert all(row["broker_operation_permitted"] is False for row in rows)
    assert all(row["paid_api_or_vendor_call"] is False for row in rows)
    assert all(row["runtime_trading_or_live_broker_effect"] is False for row in rows)
    assert all(row["legacy_support_override_allowed"] is False for row in rows)
    assert all(row["follow_avoid_mixed_pressure_allowed"] is False for row in rows)
    assert all(
        row["admission_rule"]["not_duplicated_by_converted_fresher_wave"] is False
        for row in rows
    )


def test_final_conversion_freeze_report_is_replay_handoff_not_runtime_wave():
    report = FREEZE_REPORT.read_text(encoding="utf-8")
    summary = json.loads(FREEZE_SUMMARY.read_text(encoding="utf-8"))

    assert summary["executed_wave_count"] == 75
    assert summary["generated_runtime_artifact_count"] == 153
    assert summary["generated_runtime_row_count"] == 661344
    assert summary["batch_open_unit_count_before_freeze"] == 1639
    assert summary["batch_open_wave_count_before_freeze"] == 2
    assert summary["runtime_pressure_allowed_for_freeze_rows"] is False
    assert summary["legacy_support_override_allowed"] is False
    assert "WAVE_LIFECYCLE_EXECUTION_SOURCE_GUARD_RUNTIME" in summary[
        "executed_wave_ids"
    ]
    assert "Start a fresh replay/ablation session from disk" in report
    assert "Do not run replay in this freeze session" in report
    assert "freeze residue cannot add broad MIXED context" in report
