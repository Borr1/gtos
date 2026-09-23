from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ROUTE = REPO_ROOT / "research" / "operations" / "vps_runtime_active_monitoring_repair_2026_06_19"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_active_supervision_builder_read_json_accepts_utf8_bom(tmp_path):
    module = _load_module(
        "build_vps_active_supervision_repair_artifacts",
        ROUTE / "build_vps_active_supervision_repair_artifacts.py",
    )
    path = tmp_path / "heartbeat.json"
    path.write_text('{"ts":"2026-06-19T04:26:12Z","pid":1456}', encoding="utf-8-sig")

    assert module.read_json(path) == {"ts": "2026-06-19T04:26:12Z", "pid": 1456}


def test_active_supervision_builder_adds_repo_root_to_sys_path():
    module = _load_module(
        "build_vps_active_supervision_repair_artifacts_for_import_path",
        ROUTE / "build_vps_active_supervision_repair_artifacts.py",
    )

    assert str(module.REPO_ROOT) in sys.path


def test_active_supervision_verifier_read_json_path_accepts_utf8_bom(tmp_path):
    module = _load_module(
        "verify_vps_runtime_active_monitoring_repair",
        ROUTE / "verify_vps_runtime_active_monitoring_repair.py",
    )
    path = tmp_path / "verification.json"
    path.write_text('{"ok":true,"issue_count":0}', encoding="utf-8-sig")

    assert module.read_json_path(path) == {"ok": True, "issue_count": 0}


def test_active_supervision_builder_classifies_ignore_new_overlap_as_non_failure():
    module = _load_module(
        "build_vps_active_supervision_repair_artifacts_for_scheduler",
        ROUTE / "build_vps_active_supervision_repair_artifacts.py",
    )
    tasks = [
        {
            "TaskName": "GTOS_W7_BookSupervisor",
            "State": "Running",
            "LastTaskResult": 2147946720,
            "MultipleInstances": "IgnoreNew",
        }
    ]
    heartbeats = {
        "pipeline_state\\supervisor_heartbeat.json": {
            "age_seconds": 22.3,
            "payload": {"pid": 1456},
        }
    }

    annotated = module.annotate_scheduled_task_health(tasks, heartbeats)

    assert annotated[0]["task_health_classification"] == "running_ignore_new_overlap_not_process_failure"
    assert annotated[0]["task_health_evidence"]["last_task_result_hex"] == "0x800710E0"


def test_active_supervision_builder_offsets_recent_deal_history_query_window():
    module = _load_module(
        "build_vps_active_supervision_repair_artifacts_for_deal_offset",
        ROUTE / "build_vps_active_supervision_repair_artifacts.py",
    )
    now = datetime(2026, 6, 19, 5, 19, 46, tzinfo=timezone.utc)

    window = module.broker_history_query_window(
        now,
        lookback_hours=12,
        broker_offset_seconds=10_800,
    )

    assert window["utc_from"] == datetime(2026, 6, 18, 17, 19, 46, tzinfo=timezone.utc)
    assert window["utc_to"] == now
    assert window["mt5_query_from"] == datetime(2026, 6, 18, 20, 19, 46, tzinfo=timezone.utc)
    assert window["mt5_query_to"] == datetime(2026, 6, 19, 8, 19, 46, tzinfo=timezone.utc)


def test_active_supervision_builder_classifies_line_3262_pattern_as_cross_namespace_append_order():
    module = _load_module(
        "build_vps_active_supervision_repair_artifacts_for_chronology",
        ROUTE / "build_vps_active_supervision_repair_artifacts.py",
    )

    assert (
        module.classify_append_order_regression(
            "operator_profile",
            "redacted_account_live_bee34003",
        )
        == "cross_namespace_append_order"
    )
    assert (
        module.classify_append_order_regression(
            "operator_profile",
            "operator_profile",
        )
        == "same_namespace_timestamp_order_regression"
    )


def test_active_supervision_verifier_rejects_pending_completion_status():
    module = _load_module(
        "verify_vps_runtime_active_monitoring_repair_for_pending_status",
        ROUTE / "verify_vps_runtime_active_monitoring_repair.py",
    )
    completion = {
        "broker_mutation_status": "none",
        "instruction_coverage": {"controlling_prompt_read": True},
        "ok": True,
        "runtime_effect_boundary": "read_only_supervision_artifact_refresh_no_reload_no_broker_mutation",
        "self_red_team": [{}, {}, {}, {}, {}],
        "verification_status": "pending_post_generation_verifier_and_tests",
    }

    issues = module.active_supervision_completion_issues(completion, {})

    assert "active_supervision_completion_verification_status_not_green" in issues


def test_active_supervision_verifier_accepts_verified_completion_status():
    module = _load_module(
        "verify_vps_runtime_active_monitoring_repair_for_verified_status",
        ROUTE / "verify_vps_runtime_active_monitoring_repair.py",
    )
    completion = {
        "broker_mutation_status": "none",
        "instruction_coverage": {"controlling_prompt_read": True},
        "ok": True,
        "runtime_effect_boundary": "read_only_supervision_artifact_refresh_no_reload_no_broker_mutation",
        "self_red_team": [{}, {}, {}, {}, {}],
        "verification_results": [{"command": "pytest tests\\test_vps_active_supervision_json_readers.py -q", "status": "passed"}],
        "verification_status": module.VERIFIED_SUPERVISION_STATUS,
        "verified_at_utc": "2026-06-19T04:45:00Z",
    }

    assert module.active_supervision_completion_issues(completion, {}) == []


def test_active_supervision_verifier_rejects_broker_offset_detection_error():
    module = _load_module(
        "verify_vps_runtime_active_monitoring_repair_for_broker_offset",
        ROUTE / "verify_vps_runtime_active_monitoring_repair.py",
    )
    broker_snapshot = {
        "profiles": {
            "operator_profile": {
                "recent_deals_query": {
                    "broker_offset_error": "ModuleNotFoundError(\"No module named 'src'\")",
                    "broker_offset_seconds": 0,
                    "offset_source": "src.components.mt5_daemon_runtime.detect_broker_offset_seconds",
                }
            }
        }
    }

    assert module.active_supervision_broker_snapshot_issues(broker_snapshot) == [
        "active_supervision_recent_deals_broker_offset_error:operator_profile"
    ]


def test_active_supervision_verifier_rejects_same_namespace_chronology_regression():
    module = _load_module(
        "verify_vps_runtime_active_monitoring_repair_for_chronology",
        ROUTE / "verify_vps_runtime_active_monitoring_repair.py",
    )
    packet_audit = {
        "packet_log": {
            "append_order_regression_count": 2,
            "append_order_regression_class_counts": {
                "cross_namespace_append_order": 1,
                "same_namespace_timestamp_order_regression": 1,
            },
            "same_namespace_append_order_regression_count": 1,
        }
    }

    assert module.active_supervision_packet_chronology_issues(packet_audit) == [
        "active_supervision_same_namespace_append_order_regressions"
    ]
