from __future__ import annotations

from pathlib import Path

from src.research_infra.moonshot_frozen_universe_main_consumption import (
    SCHEMA_VERSION,
    build_artifact_consumption_rows,
    build_consumption_order_rows,
    build_count_check_rows,
    summarize_consumption,
)


def _artifact_rows():
    return [
        {
            "checkpoint": 281,
            "artifact_role": "frozen_universe_ready_action_runtime_rules",
            "artifact_path": "route/ready_rules.jsonl",
            "artifact_sha256": "a" * 64,
            "artifact_byte_count": 100,
            "row_count": 461,
            "row_count_basis": "jsonl_rows",
            "frozen_main_handoff_artifact_row_id": "ART-1",
        },
        {
            "checkpoint": 280,
            "artifact_role": "repair_needed_bundle",
            "artifact_path": "route/repair.jsonl",
            "artifact_sha256": "b" * 64,
            "artifact_byte_count": 200,
            "row_count": 243649,
            "row_count_basis": "jsonl_rows",
            "frozen_main_handoff_artifact_row_id": "ART-2",
        },
    ]


def _order_rows():
    return [
        {
            "priority_order": 1,
            "handoff_class": "ready_runtime_rules_first",
            "main_consumption_role": "CP281 executable ready-slice runtime rules",
            "artifact_count": 1,
            "artifact_paths": ["route/ready_rules.jsonl"],
            "artifact_paths_sha256": "c" * 64,
            "frozen_main_consumption_order_row_id": "ORDER-1",
        },
        {
            "priority_order": 4,
            "handoff_class": "repair_needed_bundle_fourth",
            "main_consumption_role": "CP280 preserved repair-needed bundle and repair task source artifacts",
            "artifact_count": 1,
            "artifact_paths": ["route/repair.jsonl"],
            "artifact_paths_sha256": "d" * 64,
            "frozen_main_consumption_order_row_id": "ORDER-4",
        },
    ]


def _count_rows():
    return [
        {
            "check_name": "implementation_ready_rows_consumed",
            "check_pass": True,
            "expected": 461,
            "observed": 461,
            "evidence_path": "route/cp281.json",
            "frozen_main_handoff_count_check_row_id": "CHECK-1",
        }
    ]


def test_artifact_consumption_rows_preserve_owner_and_boundaries():
    rows = build_artifact_consumption_rows(
        _artifact_rows(),
        _order_rows(),
        moonshot_head="abc123",
        moonshot_status_clean=True,
    )

    assert len(rows) == 2
    assert rows[0]["schema_version"] == SCHEMA_VERSION
    assert rows[0]["consumption_priority_order"] == 1
    assert rows[0]["main_consumption_action"] == "CONSUME_CP281_READY_RUNTIME_RULES_FIRST"
    assert rows[0]["row_ownership"]["owner_checkpoint"] == "CP281"
    assert rows[1]["main_consumption_action"] == "PRESERVE_CP280_REPAIR_NEEDED_ROW_OWNERSHIP_FOR_SOURCE_REPAIR"
    assert rows[1]["research_boundary"]["broker_operation"] is False
    assert rows[1]["research_boundary"]["runtime_candidate_use_permitted"] is False


def test_order_and_count_rows_keep_source_checks():
    order_rows = build_consumption_order_rows(
        _order_rows(),
        moonshot_head="abc123",
        moonshot_status_clean=True,
    )
    count_rows = build_count_check_rows(
        _count_rows(),
        moonshot_head="abc123",
        moonshot_status_clean=True,
    )

    assert [row["priority_order"] for row in order_rows] == [1, 4]
    assert order_rows[0]["artifact_count"] == 1
    assert count_rows[0]["check_pass"] is True
    assert count_rows[0]["expected"] == count_rows[0]["observed"] == 461


def test_summary_carries_cp280_cp281_cp282_key_counts():
    packet = {
        "cp280_result": {
            "ok": True,
            "counts": {
                "implementation_ready_rows": 461,
                "repair_needed_rows": 243649,
                "kill_preserve_rows": 25811,
                "coverage_rows": 28474,
            },
        },
        "cp281_result": {
            "ok": True,
            "counts": {
                "rule_rows": 461,
                "self_test_pass_rows": 461,
                "action_class_counts": {"follow_rule": 173, "avoid_filter": 288},
            },
        },
        "cp282_result": {
            "ok": True,
            "counts": {
                "repair_needed_rows_preserved": 243649,
                "kill_preserve_rows_preserved": 25811,
                "coverage_rows_preserved": 28474,
            },
        },
        "cp282_verifier": {"ok": True},
        "source_inventory": {"cp280_result": {"exists": True}},
    }
    artifact_rows = build_artifact_consumption_rows(
        _artifact_rows(),
        _order_rows(),
        moonshot_head="abc123",
        moonshot_status_clean=True,
    )
    summary = summarize_consumption(
        packet=packet,
        artifact_rows=artifact_rows,
        order_rows=[],
        count_rows=build_count_check_rows(_count_rows(), moonshot_head="abc123", moonshot_status_clean=True),
        moonshot_root=Path("C:/tmp/"),
        moonshot_head="abc123",
        moonshot_status_clean=True,
    )

    assert summary["cp280_result_ok"] is True
    assert summary["cp281_result_ok"] is True
    assert summary["cp282_result_ok"] is True
    assert summary["key_counts"]["cp281_ready_runtime_rule_rows"] == 461
    assert summary["key_counts"]["cp281_follow_rule_inputs"] == 173
    assert summary["key_counts"]["cp280_repair_needed_rows"] == 243649
    assert summary["implementation_effect"]["broker_operation"] is False
