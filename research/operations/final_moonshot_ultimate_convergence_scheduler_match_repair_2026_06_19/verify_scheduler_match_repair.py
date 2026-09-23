#!/usr/bin/env python3
"""Verify Scheduler V3 match repair artifacts."""

from __future__ import annotations

import json
import gzip
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROUTE = Path(__file__).resolve().parent


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(name: str) -> Any:
    return json.loads((ROUTE / name).read_text(encoding="utf-8"))


def read_jsonl(name: str) -> list[dict[str, Any]]:
    return [json.loads(line) for line in (ROUTE / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def read_jsonl_gz(name: str) -> list[dict[str, Any]]:
    with gzip.open(ROUTE / name, "rt", encoding="utf-8", errors="replace") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_json(name: str, data: Any) -> None:
    (ROUTE / name).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def stable_verified_utc(result: dict[str, Any]) -> str:
    path = ROUTE / "VERIFICATION_RESULT.json"
    if not path.exists():
        return utc_now()
    try:
        existing = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return utc_now()
    old = {key: value for key, value in existing.items() if key != "verified_utc"}
    new = {key: value for key, value in result.items() if key != "verified_utc"}
    if old == new:
        return existing.get("verified_utc") or utc_now()
    return utc_now()


def main() -> int:
    now = utc_now()
    issues: list[str] = []
    required = [
        "build_scheduler_match_repair.py",
        "verify_scheduler_match_repair.py",
        "SCHEDULER_MATCH_REPAIR_SUMMARY.json",
        "SCHEDULER_MATCH_REPAIR_SOURCE_LEDGER.jsonl",
        "SCHEDULER_MATCH_CANDIDATE_LEDGER.jsonl.gz",
        "SCHEDULER_MATCH_CONTEXT_LEDGER.jsonl",
        "SCHEDULER_MATCH_AGGREGATE_LEDGER.jsonl",
        "SCHEDULER_MATCH_DECISION_LEDGER.jsonl",
        "REPAIR_LEDGER.jsonl",
        "SCHEDULER_MATCH_NEXT_PROMPT.md",
        "COMPLETION_AUDIT.json",
        "FOCUSED_TEST_RESULT.json",
        "SATURATION_SELF_RED_TEAM.md",
        "OUTPUT_MANIFEST.json",
    ]
    for name in required:
        if not (ROUTE / name).exists():
            issues.append(f"missing_required:{name}")

    summary = read_json("SCHEDULER_MATCH_REPAIR_SUMMARY.json")
    source_rows = read_jsonl("SCHEDULER_MATCH_REPAIR_SOURCE_LEDGER.jsonl")
    rows = read_jsonl_gz("SCHEDULER_MATCH_CANDIDATE_LEDGER.jsonl.gz")
    contexts = read_jsonl("SCHEDULER_MATCH_CONTEXT_LEDGER.jsonl")
    aggregates = read_jsonl("SCHEDULER_MATCH_AGGREGATE_LEDGER.jsonl")
    repairs = read_jsonl("REPAIR_LEDGER.jsonl")
    completion = read_json("COMPLETION_AUDIT.json")
    manifest = read_json("OUTPUT_MANIFEST.json")

    if summary.get("status") != "scheduler_v3_candidate_match_repaired_from_committed_blob_final_selection_still_blocked":
        issues.append("summary_status_mismatch")
    if summary.get("scheduler_v3_rows") != len(rows):
        issues.append("summary_scheduler_row_count_mismatch")
    if len(rows) != 179575:
        issues.append(f"scheduler_row_count_not_full:{len(rows)}")
    if summary.get("context_group_rows") != len(contexts):
        issues.append("context_group_count_mismatch")
    if summary.get("git_blob_status") != "readable_committed_blob":
        issues.append("git_blob_status_not_readable")
    if not summary.get("git_blob_sha256"):
        issues.append("missing_git_blob_sha256")
    if source_rows[0].get("git_blob_status") != "readable_committed_blob":
        issues.append("source_ledger_git_blob_not_readable")
    if not source_rows[0].get("git_blob_sha256"):
        issues.append("source_ledger_missing_blob_sha")

    result_sum = 0.0
    missed_sum = 0.0
    positive = 0
    negative = 0
    for row in rows:
        if row.get("broker_runtime_change_status") is not False:
            issues.append(f"broker_runtime_change_status_not_false:{row.get('match_row_id')}")
        if row.get("direct_execution_authority") is not False:
            issues.append(f"direct_execution_authority_not_false:{row.get('match_row_id')}")
        if row.get("candidate_use_allowed_now") is not False:
            issues.append(f"candidate_use_allowed_now_not_false:{row.get('match_row_id')}")
        if row.get("forbidden_surface_crossed") is not False:
            issues.append(f"forbidden_surface_crossed:{row.get('match_row_id')}")
        value = row.get("result_r")
        if isinstance(value, (int, float)):
            result_sum += float(value)
            if value > 0:
                positive += 1
            elif value < 0:
                negative += 1
        missed = row.get("missed_result_r")
        if isinstance(missed, (int, float)):
            missed_sum += float(missed)
    if round(result_sum, 9) != summary.get("result_r_sum"):
        issues.append("result_r_sum_mismatch")
    if round(missed_sum, 9) != summary.get("missed_result_r_sum"):
        issues.append("missed_result_r_sum_mismatch")
    if positive != summary.get("positive_result_r_rows"):
        issues.append("positive_result_count_mismatch")
    if negative != summary.get("negative_result_r_rows"):
        issues.append("negative_result_count_mismatch")
    if not any(row.get("aggregate") == "scheduler_v3_action_class" for row in aggregates):
        issues.append("missing_action_class_aggregate")
    if completion.get("goal_completion_claim") is not False:
        issues.append("completion_claim_not_false")
    if completion.get("instruction_coverage", {}).get("full_scheduler_v3_ledger_preserved") is not True:
        issues.append("full_scheduler_ledger_instruction_not_covered")
    if summary.get("final_package_selected") is not False:
        issues.append("summary_final_package_selected")
    if summary.get("model_training_allowed") is not False:
        issues.append("summary_model_training_allowed")
    if any(value is not False for value in summary.get("forbidden_surface_status", {}).values()):
        issues.append("summary_forbidden_surface_true")
    if not repairs:
        issues.append("empty_repair_ledger")
    if not all(item.get("exists") is True for item in manifest.get("files", [])):
        issues.append("manifest_file_missing")

    result = {
        "schema": "gtos.final_moonshot.scheduler_match_repair.verification_result.v1",
        "verified_utc": now,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "scheduler_v3_rows": len(rows),
        "context_group_rows": len(contexts),
        "git_blob_status": summary.get("git_blob_status"),
        "direct_read_status": summary.get("direct_read_status"),
        "result_r_sum": summary.get("result_r_sum"),
        "missed_result_r_sum": summary.get("missed_result_r_sum"),
        "final_package_selected": summary.get("final_package_selected"),
        "model_training_allowed": summary.get("model_training_allowed"),
    }
    result["verified_utc"] = stable_verified_utc(result)
    write_json("VERIFICATION_RESULT.json", result)
    focused = read_json("FOCUSED_TEST_RESULT.json")
    focused["status"] = "passed" if not issues else "failed"
    focused["verification_result"] = {
        "ok": result["ok"],
        "issue_count": result["issue_count"],
        "verified_utc": result["verified_utc"],
    }
    write_json("FOCUSED_TEST_RESULT.json", focused)
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
