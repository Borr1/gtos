from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


MODULE_PATH = Path(__file__).with_name(
    "build_vnext_production_change_stage10_completion_audit_2026_05_25.py"
)
spec = importlib.util.spec_from_file_location("vnext_prod_stage10", MODULE_PATH)
stage10 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = stage10
spec.loader.exec_module(stage10)


def test_all_stage_statuses_complete_allows_stage10_in_progress():
    state = {
        "stage_status_table": {
            "STAGE_00_INPUT_INVENTORY": "complete",
            "STAGE_10_COMPLETION_AUDIT_ACTIVATION_DOSSIER": "in_progress",
        }
    }

    assert stage10.all_stage_statuses_complete(state, allow_stage10_in_progress=True)
    assert not stage10.all_stage_statuses_complete(state, allow_stage10_in_progress=False)


def test_verify_audit_rejects_forbidden_actions():
    audit = {
        "instruction_coverage_ok": True,
        "stage09_headline_metrics": {"candidate_rows": 253234},
        "forbidden_actions": {"live_trading": True},
        "artifact_records": {},
    }

    failures = stage10.verify_audit(audit)

    assert "forbidden action recorded in audit" in failures


def test_verify_audit_requires_instruction_coverage_and_replay_rows():
    audit = {
        "instruction_coverage_ok": False,
        "stage09_headline_metrics": {"candidate_rows": 10},
        "forbidden_actions": {"live_trading": False},
        "artifact_records": {},
    }

    failures = stage10.verify_audit(audit)

    assert "instruction coverage is not complete" in failures
    assert "Stage09 candidate row count missing from audit" in failures


def test_verify_audit_rejects_failed_candidate_and_in_progress_completion():
    audit = {
        "complete": True,
        "instruction_coverage_ok": True,
        "stage_status_table": {
            "STAGE_10_COMPLETION_AUDIT_ACTIVATION_DOSSIER": "in_progress"
        },
        "stage09_headline_metrics": {
            "candidate_rows": 253234,
            "mechanical": {
                "selected_count": 10,
                "performance_count": 10,
                "total_r": -4.999959196997,
                "expectancy_r": -0.4999959197,
                "profit_factor": 0.375005100375,
                "phase1_8pct_pass_proxy": False,
                "phase2_5pct_pass_proxy": False,
                "blocked_trades": 216161,
            },
            "ai_no_paid_call": {
                "selected_count": 0,
            },
        },
        "forbidden_actions": {"live_trading": False},
        "artifact_records": {},
        "remaining_executable_actions_before_owner_activation": [],
    }

    failures = stage10.verify_audit(audit)

    assert any("production_candidate_failed" in failure for failure in failures)
    assert "complete_audit_with_stage10_not_complete" in failures
