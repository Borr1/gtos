#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROUTE = Path(__file__).resolve().parent
SAMPLE_LEDGER = ROUTE / "MICRO_OBSERVATION_SAMPLE_LEDGER.jsonl"
LATEST_STATUS = ROUTE / "MICRO_OBSERVATION_LATEST_STATUS.json"
SYNTHESIS_JSON = ROUTE / "MICRO_OBSERVATION_SYNTHESIS.json"
STDOUT_LOG = ROUTE / "MICRO_OBSERVER_STDOUT.log"
STDERR_LOG = ROUTE / "MICRO_OBSERVER_STDERR.log"
AI_COMPANION_DIGEST_JSON = ROUTE / "AI_COMPANION_CYCLE_DIGEST.json"
AI_COMPANION_DIGEST_MD = ROUTE / "AI_COMPANION_CYCLE_DIGEST.md"
VERIFICATION_RESULT = ROUTE / "VERIFICATION_RESULT.json"

EXPECTED_BOUNDARY = "read_only_log_pipeline_state_parse_no_broker_mutation_no_order_action_no_runtime_reload"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig", errors="ignore") as handle:
        for line_no, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError as exc:
                errors.append({"line": line_no, "error": str(exc)})
                continue
            if isinstance(parsed, dict):
                rows.append(parsed)
            else:
                errors.append({"line": line_no, "error": "non_object_json"})
    return rows, errors


def compact_bool(value: Any) -> bool:
    return bool(value)


def main() -> int:
    issues: list[dict[str, Any]] = []
    required = [
        SAMPLE_LEDGER,
        LATEST_STATUS,
        SYNTHESIS_JSON,
        STDOUT_LOG,
        STDERR_LOG,
        AI_COMPANION_DIGEST_JSON,
        AI_COMPANION_DIGEST_MD,
    ]
    for path in required:
        if not path.exists():
            issues.append({"id": "MISSING_ARTIFACT", "path": path.name})

    synthesis: dict[str, Any] = {}
    latest: dict[str, Any] = {}
    digest: dict[str, Any] = {}
    sample_rows: list[dict[str, Any]] = []
    sample_errors: list[dict[str, Any]] = []
    if not issues:
        synthesis = read_json(SYNTHESIS_JSON)
        latest = read_json(LATEST_STATUS)
        digest = read_json(AI_COMPANION_DIGEST_JSON)
        sample_rows, sample_errors = read_jsonl(SAMPLE_LEDGER)

    if sample_errors:
        issues.append({"id": "SAMPLE_LEDGER_PARSE", "count": len(sample_errors), "sample": sample_errors[:5]})
    if synthesis.get("runtime_effect_boundary") != EXPECTED_BOUNDARY:
        issues.append({"id": "SYNTHESIS_RUNTIME_BOUNDARY", "value": synthesis.get("runtime_effect_boundary")})
    if latest.get("runtime_effect_boundary") != EXPECTED_BOUNDARY:
        issues.append({"id": "LATEST_RUNTIME_BOUNDARY", "value": latest.get("runtime_effect_boundary")})
    if digest.get("runtime_effect_boundary") != EXPECTED_BOUNDARY:
        issues.append({"id": "DIGEST_RUNTIME_BOUNDARY", "value": digest.get("runtime_effect_boundary")})
    if not compact_bool(synthesis.get("ok")):
        issues.append({"id": "SYNTHESIS_NOT_OK", "value": synthesis.get("ok")})
    if not compact_bool(latest.get("ok")):
        issues.append({"id": "LATEST_NOT_OK", "value": latest.get("ok")})
    if not compact_bool(digest.get("ok")):
        issues.append({"id": "DIGEST_NOT_OK", "value": digest.get("ok")})
    if synthesis.get("issue_counts"):
        issues.append({"id": "ISSUE_COUNTS_PRESENT", "value": synthesis.get("issue_counts")})
    if latest.get("issues"):
        issues.append({"id": "LATEST_ISSUES_PRESENT", "value": latest.get("issues")})
    if synthesis.get("sample_count") != len(sample_rows):
        issues.append(
            {
                "id": "SAMPLE_COUNT_MISMATCH",
                "synthesis_sample_count": synthesis.get("sample_count"),
                "ledger_rows": len(sample_rows),
            }
        )
    if latest.get("sample_index") != synthesis.get("sample_count"):
        issues.append(
            {
                "id": "LATEST_SAMPLE_MISMATCH",
                "latest_sample_index": latest.get("sample_index"),
                "synthesis_sample_count": synthesis.get("sample_count"),
            }
        )
    if digest.get("cycle_count") != (latest.get("launcher_log", {}) or {}).get("window_row_count"):
        issues.append(
            {
                "id": "DIGEST_CYCLE_COUNT_MISMATCH",
                "digest_cycle_count": digest.get("cycle_count"),
                "latest_launcher_window_rows": (latest.get("launcher_log", {}) or {}).get("window_row_count"),
            }
        )

    latest_packet = latest.get("packet_log") if isinstance(latest.get("packet_log"), dict) else {}
    latest_launcher = latest.get("launcher_log") if isinstance(latest.get("launcher_log"), dict) else {}
    latest_execution = latest.get("execution_manager") if isinstance(latest.get("execution_manager"), dict) else {}
    latest_lifecycle = latest.get("broker_lifecycle") if isinstance(latest.get("broker_lifecycle"), dict) else {}
    latest_trade_records = latest.get("trade_records") if isinstance(latest.get("trade_records"), dict) else {}
    latest_placement = latest.get("placement_ledgers") if isinstance(latest.get("placement_ledgers"), dict) else {}

    zero_count_checks = {
        "packet_parse_error_count": latest_packet.get("parse_error_count"),
        "packet_validation_issue_count": latest_packet.get("validation_issue_count"),
        "launcher_parse_error_count": latest_launcher.get("parse_error_count"),
        "execution_parse_error_count": latest_execution.get("parse_error_count"),
        "broker_lifecycle_parse_error_count": latest_lifecycle.get("parse_error_count"),
        "trade_record_parse_error_count": latest_trade_records.get("parse_error_count"),
        "placement_incomplete_ticket_row_count": latest_placement.get("incomplete_ticket_row_count"),
        "placement_parse_error_count": latest_placement.get("parse_error_count"),
    }
    for check, value in zero_count_checks.items():
        if value != 0:
            issues.append({"id": "NONZERO_COUNTER", "check": check, "value": value})

    stderr_text = STDERR_LOG.read_text(encoding="utf-8", errors="ignore") if STDERR_LOG.exists() else ""
    if stderr_text.strip():
        issues.append({"id": "STDERR_NOT_EMPTY", "sample": stderr_text.strip()[:1000]})

    stdout_tail = []
    if STDOUT_LOG.exists():
        stdout_tail = [line for line in STDOUT_LOG.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip()][-3:]
    if not any('"samples": 61' in line and '"ok": true' in line for line in stdout_tail):
        issues.append({"id": "STDOUT_FINAL_SUMMARY_MISSING", "stdout_tail": stdout_tail})

    result = {
        "schema": "gtos.vps_runtime_ai_companion_micro_observation.verification_result.v1",
        "ok": not issues,
        "issues": issues,
        "checked_artifacts": [path.name for path in required],
        "sample_count": synthesis.get("sample_count"),
        "digest_cycle_count": digest.get("cycle_count"),
        "digest_terminal_cause_counts": digest.get("terminal_cause_counts"),
        "latest_sample_index": latest.get("sample_index"),
        "runtime_effect_boundary": synthesis.get("runtime_effect_boundary"),
        "latest_packet_window_rows": latest_packet.get("window_row_count"),
        "latest_launcher_window_rows": latest_launcher.get("window_row_count"),
        "latest_issue_count": len(latest.get("issues") or []),
        "latest_opportunity_count": len(latest.get("opportunities") or []),
        "zero_count_checks": zero_count_checks,
        "stdout_tail": stdout_tail,
    }
    VERIFICATION_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
