"""Materialize pending-lifecycle decision-spread source-capture repair."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-17"
ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
ROUTE_DIR = Path(__file__).resolve().parent
SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

INPUT_PENDING_REPAIR_SUMMARY = (
    ROUTE_DIR / "MAIN_ORCH24_PENDING_LIFECYCLE_LTF_FIRST_TOUCH_REPAIR_SUMMARY_2026-05-16.json"
)
INPUT_CURRENT_ACTION_SUMMARY = (
    ROUTE_DIR / "MAIN_ORCH24_ACTION_AFTER_STRUCTURAL_METADATA_REPAIR_SUMMARY_2026-05-17.json"
)
INPUT_EXECUTION = Path("src/components/execution.py")
INPUT_PENDING_TESTS = Path("tests/test_pending_limit_lifecycle_logger.py")

OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_DECISION_SPREAD_CAPTURE_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_DECISION_SPREAD_CAPTURE_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_DECISION_SPREAD_CAPTURE_OUTPUT_MANIFEST_{DATE}.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def token_presence(path: Path, tokens: list[str]) -> dict[str, bool]:
    text = path.read_text(encoding="utf-8")
    return {token: token in text for token in tokens}


def build_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    generated = utc_now()
    pending_summary = read_json(INPUT_PENDING_REPAIR_SUMMARY)
    action_summary = read_json(INPUT_CURRENT_ACTION_SUMMARY)
    missing = pending_summary.get("missing_field_counts", {})
    rows = [
        {
            "row_id": "MAIN-ORCH24-PENDING-LIFECYCLE-SPREAD-CAPTURE-001",
            "route_id": ROUTE_ID,
            "generated_utc": generated,
            "field_family": "decision_spread_value_source_safe",
            "before_source_capture_behavior": "CHECK_TELEMETRY_ONLY_NOT_PERSISTED_ON_PENDING_INTENT",
            "after_source_capture_behavior": "PERSISTED_ON_PENDING_INTENT_AND_REUSED_BY_LIFECYCLE_CHECK",
            "current_missing_rows_before": missing.get("decision_spread_value_source_safe", 0),
            "current_missing_rows_after": missing.get("decision_spread_value_source_safe", 0),
            "current_row_delta": 0,
            "implementation_decision": "IMPLEMENT_PENDING_INTENT_DECISION_SPREAD_SOURCE_CAPTURE",
            "current_proxy_r_delta": 0.0,
            "exact_r_delta": 0,
            "safe_flags": SAFE_FLAGS,
        },
        {
            "row_id": "MAIN-ORCH24-PENDING-LIFECYCLE-SPREAD-CAPTURE-002",
            "route_id": ROUTE_ID,
            "generated_utc": generated,
            "field_family": "decision_spread_unit",
            "before_source_capture_behavior": "UNIT_ONLY_PRESENT_WHEN_CHECK_TELEMETRY_REPEATED_DECISION_SPREAD",
            "after_source_capture_behavior": "UNIT_PERSISTED_ON_PENDING_INTENT_WITH_SPREAD_CENTS_DEFAULT",
            "current_missing_rows_before": missing.get("decision_spread_unit", 0),
            "current_missing_rows_after": missing.get("decision_spread_unit", 0),
            "current_row_delta": 0,
            "implementation_decision": "IMPLEMENT_PENDING_INTENT_DECISION_SPREAD_UNIT_CAPTURE",
            "current_proxy_r_delta": 0.0,
            "exact_r_delta": 0,
            "safe_flags": SAFE_FLAGS,
        },
        {
            "row_id": "MAIN-ORCH24-PENDING-LIFECYCLE-SPREAD-CAPTURE-003",
            "route_id": ROUTE_ID,
            "generated_utc": generated,
            "field_family": "entry_touch_spread",
            "before_source_capture_behavior": "CAPTURED_FROM_TRIGGER_TICK_WHEN_TRIGGER_AND_TICK_AVAILABLE",
            "after_source_capture_behavior": "UNCHANGED_ALREADY_SOURCE_SAFE_TICK_SNAPSHOT_CAPTURE",
            "current_missing_rows_before": missing.get("entry_touch_spread_value_source_safe", 0),
            "current_missing_rows_after": missing.get("entry_touch_spread_value_source_safe", 0),
            "current_row_delta": 0,
            "implementation_decision": "KEEP_ENTRY_TOUCH_SPREAD_TICK_CAPTURE_NO_CODE_DELTA",
            "current_proxy_r_delta": 0.0,
            "exact_r_delta": 0,
            "safe_flags": SAFE_FLAGS,
        },
        {
            "row_id": "MAIN-ORCH24-PENDING-LIFECYCLE-SPREAD-CAPTURE-004",
            "route_id": ROUTE_ID,
            "generated_utc": generated,
            "field_family": "terminal_protective_first_touch_utc",
            "before_source_capture_behavior": "CAPTURED_ONLY_FOR_EVENT_ROWS_OR_DERIVED_FROM_LTF_WHEN_PRESENT",
            "after_source_capture_behavior": "UNCHANGED_CURRENT_LOCAL_LTF_HAS_NO_ADDITIONAL_FIRST_TOUCH_REPAIR_ROWS",
            "current_missing_rows_before": (
                missing.get("terminal_area_first_touch_utc", 0)
                + missing.get("protective_area_first_touch_utc", 0)
            ),
            "current_missing_rows_after": (
                missing.get("terminal_area_first_touch_utc", 0)
                + missing.get("protective_area_first_touch_utc", 0)
            ),
            "current_row_delta": 0,
            "implementation_decision": "PRESERVE_EXACT_FIRST_TOUCH_SOURCE_REQUIREMENTS_FOR_CURRENT_ROWS",
            "current_proxy_r_delta": 0.0,
            "exact_r_delta": 0,
            "safe_flags": SAFE_FLAGS,
        },
    ]
    summary = {
        "route_id": ROUTE_ID,
        "evidence_class": "MAIN_ORCH24_PENDING_LIFECYCLE_DECISION_SPREAD_SOURCE_CAPTURE",
        "generated_utc": generated,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": (
            "Pending-limit lifecycle source-capture implementation for future rows: decision spread "
            "is now persisted on PendingLimitIntent and reused by lifecycle checks. Current historical "
            "rows are not backfilled because the decision-time spread was not captured on disk."
        ),
        "rows": len(rows),
        "implemented_source_capture_fields": [
            "PendingLimitIntent.decision_spread_value_source_safe",
            "PendingLimitIntent.decision_spread_unit",
            "ExecutionEngine.set_limit_intent decision-spread persistence",
            "ExecutionEngine._record_pending_limit_lifecycle intent fallback",
        ],
        "current_pending_rows": pending_summary.get("rows"),
        "current_internal_pending_lifecycle_rows": pending_summary.get(
            "internal_pending_lifecycle_rows"
        ),
        "current_numeric_proxy_rows_before": pending_summary.get("after_numeric_proxy_rows"),
        "current_numeric_proxy_rows_after": pending_summary.get("after_numeric_proxy_rows"),
        "current_proxy_r_sum_before": pending_summary.get("after_proxy_r_sum"),
        "current_proxy_r_sum_after": pending_summary.get("after_proxy_r_sum"),
        "current_proxy_r_sum_delta": 0.0,
        "current_missing_field_counts_before": missing,
        "current_missing_field_counts_after": missing,
        "current_missing_field_delta": 0,
        "action_queue_proxy_after": action_summary.get("proxy_after"),
        "exact_r_rows": 0,
        "plate_decision": "PENDING_LIFECYCLE_DECISION_SPREAD_SOURCE_CAPTURE_IMPLEMENTED_CURRENT_ROWS_UNCHANGED",
        "code_evidence": {
            "execution": {
                "path": str(INPUT_EXECUTION),
                "sha256": sha256_file(INPUT_EXECUTION),
                "required_token_presence": token_presence(
                    INPUT_EXECUTION,
                    [
                        "decision_spread_value_source_safe: float | None = None",
                        "decision_spread_unit: str | None = None",
                        "decision_spread_value = getattr(",
                    ],
                ),
            },
            "tests": {
                "path": str(INPUT_PENDING_TESTS),
                "sha256": sha256_file(INPUT_PENDING_TESTS),
                "required_token_presence": token_presence(
                    INPUT_PENDING_TESTS,
                    ["test_execution_persists_decision_spread_from_limit_intent"],
                ),
            },
        },
    }
    return rows, summary


def build_manifest(summary: dict[str, Any]) -> dict[str, Any]:
    inputs = {
        "pending_lifecycle_ltf_first_touch_summary": INPUT_PENDING_REPAIR_SUMMARY,
        "current_action_summary": INPUT_CURRENT_ACTION_SUMMARY,
        "execution": INPUT_EXECUTION,
        "pending_lifecycle_tests": INPUT_PENDING_TESTS,
    }
    outputs = {
        "ledger": OUTPUT_LEDGER,
        "summary": OUTPUT_SUMMARY,
    }
    return {
        "route_id": ROUTE_ID,
        "evidence_class": summary["evidence_class"],
        "generated_utc": summary["generated_utc"],
        "safe_flags": SAFE_FLAGS,
        "inputs": {
            name: {
                "path": str(path),
                "exists": path.exists(),
                "sha256": sha256_file(path) if path.exists() else None,
                "bytes": path.stat().st_size if path.exists() else None,
            }
            for name, path in inputs.items()
        },
        "outputs": {
            name: {"path": str(path), "sha256": sha256_file(path), "bytes": path.stat().st_size}
            for name, path in outputs.items()
        },
        "summary_counts": {
            "rows": summary["rows"],
            "current_proxy_r_sum_delta": summary["current_proxy_r_sum_delta"],
            "current_missing_field_delta": summary["current_missing_field_delta"],
            "exact_r_rows": summary["exact_r_rows"],
        },
    }


def main() -> None:
    rows, summary = build_rows()
    write_jsonl(OUTPUT_LEDGER, rows)
    write_json(OUTPUT_SUMMARY, summary)
    write_json(OUTPUT_MANIFEST, build_manifest(summary))
    print(
        json.dumps(
            {
                "ok": True,
                "rows": summary["rows"],
                "current_proxy_r_sum_delta": summary["current_proxy_r_sum_delta"],
                "current_missing_field_delta": summary["current_missing_field_delta"],
                "plate_decision": summary["plate_decision"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
