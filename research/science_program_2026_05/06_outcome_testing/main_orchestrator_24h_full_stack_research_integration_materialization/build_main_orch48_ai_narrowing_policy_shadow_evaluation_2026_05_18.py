from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_ID = "MAIN_ORCH48_AI_NARROWING_POLICY_SHADOW_EVALUATION"
SCHEMA_VERSION = "main_orch48_ai_narrowing_policy_shadow_evaluation_v1"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts import backfill_ai_narrowing_policy_shadow_evaluations as shadow_eval  # noqa: E402


SCRIPT_SOURCE = REPO / "scripts/backfill_ai_narrowing_policy_shadow_evaluations.py"
MAINTENANCE_SOURCE = REPO / "scripts/run_live_monitoring_maintenance.py"
CHECKLIST_SOURCE = REPO / "scripts/build_daily_monitoring_checklist.py"
TEST_SOURCE = REPO / "tests/test_ai_narrowing_policy_shadow_evaluations.py"
RUNTIME_HALT_FLAG = REPO / "pipeline_state/RESEARCH_RUNTIME_HALT.flag"
OUTPUT_LEDGER = ROUTE_DIR / f"{ROUTE_ID}_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"{ROUTE_ID}_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"{ROUTE_ID}_MANIFEST_{DATE}.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="replace")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def run_git_in_repo(*args: str) -> dict[str, Any]:
    result = subprocess.run(["git", *args], cwd=REPO, text=True, capture_output=True, check=False)
    return {
        "args": ["git", *args],
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def synthetic_scope() -> dict[str, Any]:
    return {
        "symbol": "XAUUSD",
        "source_symbol": "XAUUSD",
        "market_timeframe": "M15",
        "route_session": "ny",
        "horizon_id": "live_candidate_decision",
        "source_component": "primary_analyzer_live_candidate",
        "selected_side": "LONG",
    }


def synthetic_policy() -> dict[str, Any]:
    return {
        **synthetic_scope(),
        "ai_narrowing_policy_row_id": "MAIN-ORCH48-AI-NARROWING-SHADOW-POLICY-SYNTH-0001",
        "ai_narrowing_policy_status": "AI_NARROWING_POLICY_DEFAULT_OFF_PRE_AI_MECHANICAL_SELECTOR_READY",
        "ai_role_after_owner_approval": "MECHANICAL_SELECTOR_CAN_PRECEDE_AI_FOR_SCOPE_AFTER_REVIEW",
    }


def synthetic_candidate() -> dict[str, Any]:
    return {
        **synthetic_scope(),
        "candidate_id": "XAUUSD_2026-05-18T13:30:00+00:00",
        "decision_time_utc": "2026-05-18T13:30:00+00:00",
        "schema_version": "strategy_follow_candidate_v1",
    }


def build() -> dict[str, Any]:
    generated = utc_now()
    synthetic_rows = shadow_eval.build_shadow_evaluations(
        candidate_rows=[(1, synthetic_candidate())],
        policy_rows=[synthetic_policy()],
        candidate_source_path=Path("shadow_logs/strategy_follow_candidates.jsonl"),
        candidate_source_sha256="synthetic-candidate-source-sha",
        policy_ledger_path=shadow_eval.DEFAULT_POLICY_LEDGER,
        policy_ledger_sha256="synthetic-policy-ledger-sha",
        generated_at_utc=generated,
    )
    synthetic_report = shadow_eval.build_report(
        rows=synthetic_rows,
        appended_rows=synthetic_rows,
        output_path=shadow_eval.DEFAULT_OUTPUT,
        candidate_rows=1,
        policy_rows=1,
        candidate_source_sha256="synthetic-candidate-source-sha",
        policy_ledger_sha256="synthetic-policy-ledger-sha",
    )
    synthetic_row = synthetic_rows[0]
    script_text = read_text(SCRIPT_SOURCE)
    maintenance_text = read_text(MAINTENANCE_SOURCE)
    checklist_text = read_text(CHECKLIST_SOURCE)
    test_text = read_text(TEST_SOURCE)

    rows = [
        {
            "route_row_id": "MAIN-ORCH48-AI-NARROWING-SHADOW-EVAL-0001",
            "schema_version": SCHEMA_VERSION,
            "check": "SYNTHETIC_STRATEGY_FOLLOW_CANDIDATE_EVALUATES_DEFAULT_OFF_POLICY",
            "event_adapter_status": synthetic_row["event_adapter_status"],
            "missing_required_fields": synthetic_row["missing_required_fields"],
            "ai_narrowing_registry_eval_status": synthetic_row["ai_narrowing_registry_eval_status"],
            "matched_policy_rows": synthetic_row["matched_policy_rows"],
            "ai_narrowing_review_ready": synthetic_row["ai_narrowing_review_ready"],
            "ai_call_skip_allowed_now": synthetic_row["ai_call_skip_allowed_now"],
            "runtime_candidate_use_permitted": synthetic_row["runtime_candidate_use_permitted"],
            "live_ai_runtime_change_now": synthetic_row["live_ai_runtime_change_now"],
            "production_change_opened_now": synthetic_row["production_change_opened_now"],
            "paid_api_or_vendor_call": synthetic_row["paid_api_or_vendor_call"],
        },
        {
            "route_row_id": "MAIN-ORCH48-AI-NARROWING-SHADOW-EVAL-0002",
            "schema_version": SCHEMA_VERSION,
            "check": "BACKFILL_SCRIPT_IS_RESEARCH_ONLY_AND_IDEMPOTENT",
            "source_path": display_path(SCRIPT_SOURCE),
            "source_sha256": sha256_path(SCRIPT_SOURCE),
            "has_existing_row_keys": "existing_row_keys" in script_text,
            "has_append_only_output": "append_jsonl(args.output, appended)" in script_text,
            "has_no_runtime_skip_flags": '"ai_call_skip_allowed_now": False' in script_text,
            "has_no_paid_or_broker_flags": '"paid_api_or_vendor_call": False' in script_text,
            "runtime_candidate_use_permitted": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
        },
        {
            "route_row_id": "MAIN-ORCH48-AI-NARROWING-SHADOW-EVAL-0003",
            "schema_version": SCHEMA_VERSION,
            "check": "MAINTENANCE_AND_CHECKLIST_ROUTE_INCLUDE_BACKFILL",
            "maintenance_source_path": display_path(MAINTENANCE_SOURCE),
            "maintenance_source_sha256": sha256_path(MAINTENANCE_SOURCE),
            "checklist_source_path": display_path(CHECKLIST_SOURCE),
            "checklist_source_sha256": sha256_path(CHECKLIST_SOURCE),
            "maintenance_step_present": "ai_narrowing_policy_shadow_evaluations" in maintenance_text,
            "final_maintenance_step_present": "final_ai_narrowing_policy_shadow_evaluations" in maintenance_text,
            "checklist_command_present": "python scripts/backfill_ai_narrowing_policy_shadow_evaluations.py" in checklist_text,
            "runtime_candidate_use_permitted": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
        },
        {
            "route_row_id": "MAIN-ORCH48-AI-NARROWING-SHADOW-EVAL-0004",
            "schema_version": SCHEMA_VERSION,
            "check": "TEST_AND_HALT_BOUNDARY",
            "test_source_path": display_path(TEST_SOURCE),
            "test_source_sha256": sha256_path(TEST_SOURCE),
            "test_covers_idempotency": "idempotently" in test_text,
            "test_covers_incomplete_keep_ai": "keeps_ai_gate" in test_text,
            "runtime_halt_active": RUNTIME_HALT_FLAG.exists(),
            "live_runtime_restart_now": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
        },
    ]
    write_jsonl(OUTPUT_LEDGER, rows)

    summary = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_utc": generated,
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "route_rows": len(rows),
        "synthetic_event_adapter_status": synthetic_row["event_adapter_status"],
        "synthetic_registry_eval_status": synthetic_row["ai_narrowing_registry_eval_status"],
        "synthetic_matched_policy_rows": synthetic_row["matched_policy_rows"],
        "synthetic_report_status": synthetic_report["status"],
        "maintenance_step_present": rows[2]["maintenance_step_present"],
        "final_maintenance_step_present": rows[2]["final_maintenance_step_present"],
        "checklist_command_present": rows[2]["checklist_command_present"],
        "runtime_halt_active": RUNTIME_HALT_FLAG.exists(),
        "implementation_effect": {
            "current_ai_runtime_behavior": "UNCHANGED_DEFAULT_AI_DECISION_GATE",
            "ai_call_skip_allowed_now": False,
            "production_change_opened_now": False,
            "live_ai_runtime_change_now": False,
            "live_selector_change_now": False,
            "runtime_candidate_use_permitted": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
        },
        "can_continue_to_next_system_conversion_plate": True,
    }
    write_json(OUTPUT_SUMMARY, summary)

    outputs = [OUTPUT_LEDGER, OUTPUT_SUMMARY]
    manifest = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_utc": generated,
        "outputs": [
            {
                "path": display_path(path),
                "bytes": path.stat().st_size,
                "lines": count_lines(path),
                "sha256": sha256_path(path),
            }
            for path in outputs
        ],
    }
    write_json(OUTPUT_MANIFEST, manifest)
    return {
        "ok": True,
        "route_id": ROUTE_ID,
        "route_rows": len(rows),
        "synthetic_event_adapter_status": synthetic_row["event_adapter_status"],
        "synthetic_registry_eval_status": synthetic_row["ai_narrowing_registry_eval_status"],
        "runtime_halt_active": RUNTIME_HALT_FLAG.exists(),
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
