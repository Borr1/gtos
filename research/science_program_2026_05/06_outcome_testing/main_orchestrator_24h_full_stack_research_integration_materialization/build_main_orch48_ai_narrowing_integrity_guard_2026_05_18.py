from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_ID = "MAIN_ORCH48_AI_NARROWING_INTEGRITY_GUARD"
SCHEMA_VERSION = "main_orch48_ai_narrowing_integrity_guard_v1"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts import backfill_ai_narrowing_policy_shadow_evaluations as shadow_eval  # noqa: E402
from scripts import verify_shadow_log_integrity as integrity  # noqa: E402


INTEGRITY_SOURCE = REPO / "scripts/verify_shadow_log_integrity.py"
INTEGRITY_TEST = REPO / "tests/test_verify_shadow_log_integrity.py"
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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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


def synthetic_candidate() -> dict[str, Any]:
    return {
        "schema_version": "strategy_follow_candidate_v1",
        "created_at_utc": "2026-05-18T13:30:15+00:00",
        "symbol": "XAUUSD",
        "broker_symbol": "XAUUSD",
        "source_symbol": "XAUUSD",
        "candidate_id": "XAUUSD_2026-05-18T13:30:00+00:00",
        "decision_time_utc": "2026-05-18T13:30:00+00:00",
        "side": "LONG",
        "selected_side": "LONG",
        "framework": "ob_retest",
        "analysis_decision": "CANDIDATE",
        "final_outcome_at_log": "REJECTED_L2",
        "market_timeframe": "M15",
        "route_session": "ny",
        "horizon_id": "live_candidate_decision",
        "source_component": "primary_analyzer_live_candidate",
        "trade_parameters": {"entry_price": 2300.0, "stop_loss": 2290.0, "take_profit_1": 2315.0},
        "external_confluence": {"sierra": {"status": "SOURCE_BLOCKED"}, "databento": {"status": "SOURCE_BLOCKED"}},
        "strategy_snapshots": [{"strategy_id": "V2_STRUCT_OB_BOUNDARY"}],
        "no_leak_status": "NO_POST_OUTCOME_FIELDS_IN_DECISION_CONTEXT",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }


def synthetic_policy() -> dict[str, Any]:
    return {
        "symbol": "XAUUSD",
        "source_symbol": "XAUUSD",
        "market_timeframe": "M15",
        "route_session": "ny",
        "horizon_id": "live_candidate_decision",
        "source_component": "primary_analyzer_live_candidate",
        "selected_side": "LONG",
        "ai_narrowing_policy_row_id": "MAIN-ORCH48-AI-NARROWING-INTEGRITY-POLICY-0001",
        "ai_narrowing_policy_status": "AI_NARROWING_POLICY_DEFAULT_OFF_PRE_AI_MECHANICAL_SELECTOR_READY",
        "ai_role_after_owner_approval": "MECHANICAL_SELECTOR_CAN_PRECEDE_AI_FOR_SCOPE_AFTER_REVIEW",
    }


def build_synthetic_eval_row(root: Path) -> dict[str, Any]:
    candidate_path = root / "shadow_logs" / "strategy_follow_candidates.jsonl"
    candidate = synthetic_candidate()
    write_jsonl(candidate_path, [candidate])
    return shadow_eval.build_shadow_evaluations(
        candidate_rows=[(1, candidate)],
        policy_rows=[synthetic_policy()],
        candidate_source_path=candidate_path,
        candidate_source_sha256=shadow_eval.sha256_path(candidate_path),
        policy_ledger_path=Path("policy.jsonl"),
        policy_ledger_sha256="policy-sha",
        generated_at_utc="2026-05-18T13:31:00+00:00",
    )[0]


def build() -> dict[str, Any]:
    generated = utc_now()
    spec = integrity.JSONL_SPECS["ai_narrowing_policy_shadow_evaluations.jsonl"]
    with tempfile.TemporaryDirectory(dir=REPO) as tmp:
        tmp_root = Path(tmp)
        eval_row = build_synthetic_eval_row(tmp_root)
        write_jsonl(tmp_root / "shadow_logs" / "ai_narrowing_policy_shadow_evaluations.jsonl", [eval_row])
        health_issues: list[dict[str, Any]] = []
        health = integrity.audit_ai_narrowing_policy_shadow_evaluations_contract(
            tmp_root / "shadow_logs",
            datetime(2026, 5, 18, 13, 32, tzinfo=timezone.utc),
            health_issues,
        )
        forbidden_row = dict(eval_row)
        forbidden_row["ai_call_skip_allowed_now"] = True
        schema_issues: list[dict[str, Any]] = []
        integrity.validate_schema_row(
            "ai_narrowing_policy_shadow_evaluations.jsonl",
            spec,
            1,
            forbidden_row,
            schema_issues,
        )

    test_text = INTEGRITY_TEST.read_text(encoding="utf-8-sig", errors="replace")
    rows = [
        {
            "route_row_id": "MAIN-ORCH48-AI-NARROWING-INTEGRITY-0001",
            "schema_version": SCHEMA_VERSION,
            "check": "JSONL_SPEC_REGISTERED",
            "source_path": display_path(INTEGRITY_SOURCE),
            "source_sha256": sha256_path(INTEGRITY_SOURCE),
            "expected_schema": spec.expected_schema,
            "empty_list_fields_allowed": sorted(spec.nullable_required_fields),
            "unique_key": list(spec.unique_key),
            "runtime_candidate_use_permitted": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
        },
        {
            "route_row_id": "MAIN-ORCH48-AI-NARROWING-INTEGRITY-0002",
            "schema_version": SCHEMA_VERSION,
            "check": "SYNTHETIC_CURRENT_SOURCE_COVERAGE_HEALTH",
            "health_status": health.get("status"),
            "health_issues": health_issues,
            "candidate_ids": health.get("candidate_ids"),
            "covered_current_candidate_ids": health.get("covered_current_candidate_ids"),
            "forbidden_flag_rows": health.get("forbidden_flag_rows"),
            "runtime_candidate_use_permitted": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
        },
        {
            "route_row_id": "MAIN-ORCH48-AI-NARROWING-INTEGRITY-0003",
            "schema_version": SCHEMA_VERSION,
            "check": "FORBIDDEN_RUNTIME_FLAG_DETECTED",
            "schema_issue_codes": sorted({issue.get("code") for issue in schema_issues}),
            "forbidden_runtime_flag_detected": any(
                issue.get("code") == "AI_NARROWING_FORBIDDEN_RUNTIME_FLAG" for issue in schema_issues
            ),
            "runtime_candidate_use_permitted": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
        },
        {
            "route_row_id": "MAIN-ORCH48-AI-NARROWING-INTEGRITY-0004",
            "schema_version": SCHEMA_VERSION,
            "check": "TEST_AND_RUNTIME_HALT_BOUNDARY",
            "test_source_path": display_path(INTEGRITY_TEST),
            "test_source_sha256": sha256_path(INTEGRITY_TEST),
            "test_covers_health_acceptance": "test_ai_narrowing_shadow_eval_health_accepts_current_source_rows" in test_text,
            "test_covers_missing_candidate": "test_ai_narrowing_shadow_eval_health_flags_missing_current_candidate" in test_text,
            "test_covers_forbidden_flag": "test_ai_narrowing_shadow_eval_health_flags_forbidden_runtime_flag" in test_text,
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
        "jsonl_spec_registered": spec.expected_schema == "ai_narrowing_policy_shadow_evaluation_v1",
        "synthetic_health_status": health.get("status"),
        "synthetic_health_issues": health_issues,
        "forbidden_runtime_flag_detected": rows[2]["forbidden_runtime_flag_detected"],
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
        "synthetic_health_status": health.get("status"),
        "forbidden_runtime_flag_detected": rows[2]["forbidden_runtime_flag_detected"],
        "runtime_halt_active": RUNTIME_HALT_FLAG.exists(),
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
