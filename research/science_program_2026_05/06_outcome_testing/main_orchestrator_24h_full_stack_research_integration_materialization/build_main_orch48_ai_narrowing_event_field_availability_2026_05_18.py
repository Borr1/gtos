from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_ID = "MAIN_ORCH48_AI_NARROWING_EVENT_FIELD_AVAILABILITY"
SCHEMA_VERSION = "main_orch48_ai_narrowing_event_field_availability_v1"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_expanded_market_reduced_surface_execution import (
    AI_NARROWING_EVENT_REQUIRED_FIELDS,
    AINarrowingPolicyRegistry,
    ai_narrowing_event_from_source_row,
    summarize_ai_narrowing_policy_events,
)


POLICY_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_AI_NARROWING_POLICY_LEDGER_{DATE}.jsonl"
POLICY_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_AI_NARROWING_POLICY_SUMMARY_{DATE}.json"
OUTPUT_LEDGER = ROUTE_DIR / f"{ROUTE_ID}_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"{ROUTE_ID}_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"{ROUTE_ID}_MANIFEST_{DATE}.json"

EVENT_SOURCE_PATHS = [
    Path("shadow_logs/strategy_follow_candidates.jsonl"),
    Path("shadow_logs/live_mechanical_strategy_shadow_outcomes.jsonl"),
    Path("shadow_logs/candidate_features_log.jsonl"),
    Path("shadow_logs/candidate_path_follow.jsonl"),
    Path("shadow_logs/candidate_ltf_path_order.jsonl"),
    Path("shadow_logs/fvg_ob_confluence.jsonl"),
    Path("shadow_logs/fvg_ob_confluence_audit.jsonl"),
]

CODE_SURFACES = [
    Path("src/research_infra/moonshot_expanded_market_reduced_surface_execution.py"),
    Path("tests/research_infra/test_moonshot_expanded_market_reduced_surface_execution.py"),
    Path(
        "research/science_program_2026_05/06_outcome_testing/"
        "main_orchestrator_24h_full_stack_research_integration_materialization/"
        "build_main_orch48_ai_narrowing_event_field_availability_2026_05_18.py"
    ),
    Path(
        "research/science_program_2026_05/06_outcome_testing/"
        "main_orchestrator_24h_full_stack_research_integration_materialization/"
        "verify_main_orch48_ai_narrowing_event_field_availability_2026_05_18.py"
    ),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_lines(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


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


def code_surface_summary() -> list[dict[str, Any]]:
    return [
        {
            "path": str(path).replace("\\", "/"),
            "bytes": (REPO / path).stat().st_size,
            "lines": count_lines(REPO / path),
            "sha256": sha256_path(REPO / path),
        }
        for path in CODE_SURFACES
    ]


def audit_source(path: Path, registry: AINarrowingPolicyRegistry) -> dict[str, Any]:
    absolute = REPO / path
    row_count = 0
    parse_error_rows = 0
    events: list[dict[str, Any]] = []
    required_field_presence_counts = Counter()
    missing_required_field_counts = Counter()
    eval_status_counts = Counter()
    complete_events_matched_policy_rows = 0
    complete_events_review_ready_rows = 0

    source_sha = sha256_path(absolute) if absolute.exists() else None
    if absolute.exists():
        with absolute.open("r", encoding="utf-8", errors="replace") as handle:
            for line_no, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                row_count += 1
                try:
                    source_row = json.loads(line)
                except json.JSONDecodeError:
                    parse_error_rows += 1
                    continue
                event = ai_narrowing_event_from_source_row(
                    source_row,
                    event_row_id=f"{path.as_posix()}:{line_no}",
                    source_kind="current_shadow_or_research_log_row",
                    source_artifact=path.as_posix(),
                    source_line_no=line_no,
                    source_sha256=source_sha,
                )
                events.append(event)
                for field in AI_NARROWING_EVENT_REQUIRED_FIELDS:
                    if event.get(field):
                        required_field_presence_counts[field] += 1
                missing_required_field_counts.update(event.get("missing_required_fields") or [])
                if event.get("event_adapter_status") == "AI_NARROWING_EVENT_CONTRACT_COMPLETE":
                    evaluation = registry.evaluate_event(
                        event,
                        evaluation_row_id=f"MAIN-ORCH48-AI-NARROWING-FIELD-EVAL-{row_count:08d}",
                    )
                    eval_status_counts[evaluation.get("ai_narrowing_registry_eval_status")] += 1
                    if int(evaluation.get("matched_policy_rows") or 0) > 0:
                        complete_events_matched_policy_rows += 1
                    if evaluation.get("ai_narrowing_review_ready"):
                        complete_events_review_ready_rows += 1

    event_summary = summarize_ai_narrowing_policy_events(events)
    rows_with_complete_contract = int(event_summary.get("contract_complete_rows") or 0)
    if parse_error_rows:
        status = "CURRENT_SOURCE_PARSE_ERRORS_BEFORE_AI_NARROWING_EVAL"
    elif rows_with_complete_contract == 0:
        status = "CURRENT_SOURCE_MISSING_AI_NARROWING_BASE_SCOPE_FIELDS"
    elif complete_events_matched_policy_rows == 0:
        status = "CURRENT_SOURCE_HAS_AI_NARROWING_BASE_SCOPE_BUT_NO_POLICY_MATCH"
    else:
        status = "CURRENT_SOURCE_CAN_FEED_DEFAULT_OFF_AI_NARROWING_REGISTRY"

    return {
        "field_availability_status": status,
        "event_source_path": path.as_posix(),
        "event_source_exists": absolute.exists(),
        "event_source_sha256": source_sha,
        "event_source_bytes": absolute.stat().st_size if absolute.exists() else None,
        "event_source_rows": row_count,
        "parse_error_rows": parse_error_rows,
        "required_event_fields": list(AI_NARROWING_EVENT_REQUIRED_FIELDS),
        "required_field_presence_counts": dict(sorted(required_field_presence_counts.items())),
        "missing_required_field_counts": dict(sorted(missing_required_field_counts.items())),
        "event_adapter_status_counts": event_summary.get("event_adapter_status_counts"),
        "rows_with_ai_narrowing_required_fields": rows_with_complete_contract,
        "complete_events_matched_policy_rows": complete_events_matched_policy_rows,
        "complete_events_review_ready_rows": complete_events_review_ready_rows,
        "complete_event_eval_status_counts": dict(sorted(eval_status_counts.items())),
        "current_ai_runtime_behavior": "UNCHANGED_DEFAULT_AI_DECISION_GATE",
        "ai_call_skip_allowed_now": False,
        "production_change_opened_now": False,
        "live_ai_runtime_change_now": False,
        "live_selector_change_now": False,
        "paid_api_or_vendor_call": False,
        "runtime_candidate_use_permitted": False,
        "candidate_use_allowed_now": False,
        "replay_r_reference_counted_as_new_main_result": False,
    }


def build() -> dict[str, Any]:
    policy_rows = read_jsonl(POLICY_LEDGER)
    policy_summary = read_json(POLICY_SUMMARY)
    registry = AINarrowingPolicyRegistry(policy_rows)
    policy_sha = sha256_path(POLICY_LEDGER)
    policy_summary_sha = sha256_path(POLICY_SUMMARY)

    rows = [
        {
            "field_availability_row_id": f"MAIN-ORCH48-AI-NARROWING-FIELD-AUDIT-{index:04d}",
            "schema_version": SCHEMA_VERSION,
            **audit_source(path, registry),
        }
        for index, path in enumerate(EVENT_SOURCE_PATHS, start=1)
    ]
    write_jsonl(OUTPUT_LEDGER, rows)

    status_counts = Counter(row["field_availability_status"] for row in rows)
    adapter_status_counts = Counter()
    missing_field_counts = Counter()
    for row in rows:
        adapter_status_counts.update(row.get("event_adapter_status_counts") or {})
        missing_field_counts.update(row.get("missing_required_field_counts") or {})

    summary = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "input_ai_narrowing_policy_ledger": {
            "path": display_path(POLICY_LEDGER),
            "rows": count_lines(POLICY_LEDGER),
            "sha256": policy_sha,
        },
        "input_ai_narrowing_policy_summary": {
            "path": display_path(POLICY_SUMMARY),
            "sha256": policy_summary_sha,
            "policy_rows": policy_summary.get("rows"),
            "ai_narrowing_review_ready_rows": policy_summary.get("ai_narrowing_review_ready_rows"),
            "policy_status_counts": policy_summary.get("ai_narrowing_policy_status_counts"),
        },
        "required_event_fields": list(AI_NARROWING_EVENT_REQUIRED_FIELDS),
        "event_source_count": len(rows),
        "event_source_rows_total": sum(int(row.get("event_source_rows") or 0) for row in rows),
        "parse_error_rows_total": sum(int(row.get("parse_error_rows") or 0) for row in rows),
        "rows_with_ai_narrowing_required_fields_total": sum(
            int(row.get("rows_with_ai_narrowing_required_fields") or 0) for row in rows
        ),
        "complete_events_matched_policy_rows_total": sum(
            int(row.get("complete_events_matched_policy_rows") or 0) for row in rows
        ),
        "complete_events_review_ready_rows_total": sum(
            int(row.get("complete_events_review_ready_rows") or 0) for row in rows
        ),
        "field_availability_status_counts": dict(sorted(status_counts.items())),
        "event_adapter_status_counts": dict(sorted(adapter_status_counts.items())),
        "missing_required_field_counts": dict(sorted(missing_field_counts.items())),
        "source_paths": [row["event_source_path"] for row in rows],
        "code_surfaces": code_surface_summary(),
        "implementation_effect": {
            "default_off_ai_narrowing_event_adapter_available": True,
            "current_ai_runtime_behavior": "UNCHANGED_DEFAULT_AI_DECISION_GATE",
            "ai_call_skip_allowed_now": False,
            "production_change_opened_now": False,
            "live_ai_runtime_change_now": False,
            "live_selector_change_now": False,
            "runtime_trading_or_live_broker_effect": False,
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
        "generated_utc": summary["generated_utc"],
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
        "event_source_count": len(rows),
        "event_source_rows_total": summary["event_source_rows_total"],
        "rows_with_ai_narrowing_required_fields_total": summary[
            "rows_with_ai_narrowing_required_fields_total"
        ],
        "ai_call_skip_allowed_now": summary["implementation_effect"]["ai_call_skip_allowed_now"],
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
