#!/usr/bin/env python3
"""Verify NOFILL forward source-capture additive logger implementation artifacts."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

BASE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import build_nofill_forward_source_capture_additive_logger_implementation_2026_05_10 as builder  # noqa: E402
from src.research_infra import forward_capture as fc  # noqa: E402

DATE = "2026-05-10"
RESULT_PATH = BASE / f"NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_VERIFICATION_RESULT_{DATE}.json"


def read_json(name: str) -> dict[str, Any]:
    return json.loads((BASE / name).read_text(encoding="utf-8"))


def git_diff_added_lines(path: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--", path],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return [
        line[1:]
        for line in result.stdout.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    ]


def scan_placeholders() -> list[dict[str, str]]:
    fragments = ("TBD", "TODO", "unknown", "maybe", "later", "not yet decided")
    paths = list(BASE.glob("*.json")) + list(BASE.glob("*.md"))
    hits: list[dict[str, str]] = []
    for path in paths:
        if path.name == RESULT_PATH.name:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        lowered = text.lower()
        for fragment in fragments:
            if fragment.lower() in lowered:
                hits.append({"path": path.name, "fragment": fragment})
    for rel_path in ("src/research_infra/forward_capture.py", "tests/test_forward_capture_shadow_loggers.py"):
        for line in git_diff_added_lines(rel_path):
            lowered = line.lower()
            for fragment in fragments:
                if fragment.lower() in lowered:
                    hits.append({"path": rel_path, "fragment": fragment})
    return hits


def verify_runtime_contract() -> dict[str, Any]:
    row = fc.build_nofill_forward_source_capture_row(**builder.sample_source_fields())
    validation = fc.validate_nofill_forward_source_capture_row(row)
    missing_future = [
        field for field in fc.NOFILL_FORWARD_SOURCE_CAPTURE_FUTURE_LOGGER_FIELDS if field not in row
    ]
    forbidden_row = fc.build_nofill_forward_source_capture_row(
        **builder.sample_source_fields(),
        mt5_order_ticket="SECRET_TICKET_123",
        pending_ticket="SECRET_PENDING_456",
        slippage_price="SECRET_SLIPPAGE",
        execution_quality="SECRET_EXECUTION",
        actual_r="SECRET_RESULT_R",
    )
    payload = json.dumps(forbidden_row, sort_keys=True)
    secret_leaks = [token for token in ("SECRET_TICKET", "SECRET_PENDING", "SECRET_SLIPPAGE", "SECRET_EXECUTION", "SECRET_RESULT") if token in payload]
    forbidden_output_keys = sorted(set(forbidden_row) & fc.NOFILL_FORWARD_SOURCE_CAPTURE_FORBIDDEN_RAW_FIELD_NAMES)
    return {
        "validation": validation,
        "runtime_field_count": len(fc.NOFILL_FORWARD_SOURCE_CAPTURE_FIELDS),
        "runtime_future_logger_field_count": len(fc.NOFILL_FORWARD_SOURCE_CAPTURE_FUTURE_LOGGER_FIELDS),
        "missing_future_fields": missing_future,
        "secret_leaks": secret_leaks,
        "forbidden_output_keys": forbidden_output_keys,
        "redaction_status": forbidden_row["forbidden_field_scan_status"],
    }


def verify_fail_open() -> dict[str, Any]:
    original_append = fc.append_jsonl

    def boom(*_args: Any, **_kwargs: Any) -> None:
        raise OSError("forced writer failure")

    fc.append_jsonl = boom
    try:
        try:
            result = fc.record_nofill_forward_source_capture(builder.sample_source_fields())
            exception_escaped = False
        except Exception:  # noqa: BLE001
            result = "EXCEPTION_ESCAPED"
            exception_escaped = True
    finally:
        fc.append_jsonl = original_append
    return {
        "writer_return_value": result,
        "exception_escaped": exception_escaped,
        "pass": result is None and not exception_escaped,
    }


def main() -> int:
    issues: list[str] = []
    generated_missing = [name for name in builder.REQUIRED_ARTIFACTS if not (BASE / name).exists()]
    if generated_missing:
        issues.append("missing_required_artifacts")

    coverage = read_json(f"NOFILL_FORWARD_SOURCE_CAPTURE_55_FIELD_IMPLEMENTATION_COVERAGE_LEDGER_{DATE}.json")
    noleak = read_json(f"NOFILL_FORWARD_SOURCE_CAPTURE_NOLEAK_REDACTION_AUDIT_{DATE}.json")
    failopen = read_json(f"NOFILL_FORWARD_SOURCE_CAPTURE_FAILOPEN_NO_LIVE_BEHAVIOR_AUDIT_{DATE}.json")
    instruction = read_json(f"NOFILL_FORWARD_SOURCE_CAPTURE_INSTRUCTION_COVERAGE_CHECKLIST_{DATE}.json")
    completion_path = BASE / f"NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_COMPLETION_AUDIT_{DATE}.json"
    completion = json.loads(completion_path.read_text(encoding="utf-8"))
    design = builder.read_json(
        f"{builder.DESIGN_DIR}/NOFILL_FORWARD_SOURCE_CONTRACT_IMPLEMENTATION_MAP_2026-05-10.json"
    )

    if coverage["implemented_field_count"] != 55 or not coverage["field_name_match"]:
        issues.append("field_coverage_not_55")
    if coverage["terminal_status_counts"] != design["terminal_status_counts"]:
        issues.append("terminal_status_counts_mismatch")
    if len(fc.NOFILL_FORWARD_SOURCE_CAPTURE_FUTURE_LOGGER_FIELDS) != 20:
        issues.append("future_logger_field_count_not_20")
    if not noleak["audit_passed"]:
        issues.append("no_leak_audit_failed")
    if not failopen["audit_passed"]:
        issues.append("fail_open_audit_failed")
    if not instruction["all_requirements_covered"]:
        issues.append("instruction_coverage_incomplete")

    unsafe_json_flags: list[str] = []
    for path in BASE.glob("*.json"):
        if path.name == RESULT_PATH.name:
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for flag in ("validation_safe", "outcome_review_opened", "live_effect"):
            if data.get(flag) is True:
                unsafe_json_flags.append(f"{path.name}:{flag}")
    if unsafe_json_flags:
        issues.append("unsafe_json_flags_true")

    runtime = verify_runtime_contract()
    if not runtime["validation"]["ok"]:
        issues.append("runtime_contract_validation_failed")
    if runtime["runtime_field_count"] != 55:
        issues.append("runtime_contract_field_count_not_55")
    if runtime["missing_future_fields"]:
        issues.append("runtime_future_fields_missing")
    if runtime["secret_leaks"] or runtime["forbidden_output_keys"]:
        issues.append("runtime_redaction_failed")

    fail_open_probe = verify_fail_open()
    if not fail_open_probe["pass"]:
        issues.append("runtime_fail_open_failed")

    placeholder_hits = scan_placeholders()
    if placeholder_hits:
        issues.append("placeholder_scan_failed")

    if not issues:
        for item in completion["prompt_to_artifact_checklist"]:
            if item["requirement_id"] == "verifier_result":
                item["status"] = "PASS"
        completion["can_mark_goal_complete_after_verifier_tests_commit_and_closeout"] = True
        completion_path.write_text(json.dumps(completion, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    diff_status = subprocess.run(
        ["git", "status", "--short"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    ).stdout.splitlines()

    result = {
        "artifact": "NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_VERIFICATION_RESULT",
        "route_id": builder.ROUTE_ID,
        "schema_version": f"{builder.SCHEMA_VERSION}_verification_result",
        "ok": not issues,
        "can_mark_goal_complete": not issues,
        "issues": issues,
        "generated_missing": generated_missing,
        "runtime": runtime,
        "fail_open_probe": fail_open_probe,
        "placeholder_hits": placeholder_hits,
        "unsafe_json_flags": unsafe_json_flags,
        "workspace_status_short": diff_status,
        "completion_audit_status": completion["prompt_to_artifact_checklist"],
        "promotion_verdict": builder.PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
