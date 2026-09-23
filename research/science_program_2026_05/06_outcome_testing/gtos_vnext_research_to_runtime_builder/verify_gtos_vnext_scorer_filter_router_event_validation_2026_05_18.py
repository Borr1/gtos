from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_ID = "GTOS_VNEXT_SCORER_FILTER_ROUTER_EVENT_VALIDATION"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]

if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.gtos_vnext_evidence_system import (  # noqa: E402
    SCHEMA_VERSION,
    read_jsonl,
    sha256_path,
)


SOURCE_SUMMARY = ROUTE_DIR / f"{ROUTE_ID}_SOURCE_SUMMARY_LEDGER_{DATE}.jsonl"
SCOPE_ROLLUP = ROUTE_DIR / f"{ROUTE_ID}_SCOPE_ROLLUP_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"{ROUTE_ID}_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"{ROUTE_ID}_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"{ROUTE_ID}_VERIFY_RESULT_{DATE}.json"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def verify() -> dict[str, Any]:
    issues: list[str] = []
    required = [SOURCE_SUMMARY, SCOPE_ROLLUP, SUMMARY, MANIFEST]
    for path in required:
        if not path.exists():
            issues.append(f"missing_output:{path.name}")
    if issues:
        result = {"ok": False, "route_id": ROUTE_ID, "schema_version": SCHEMA_VERSION, "issues": issues}
        write_json(VERIFY_RESULT, result)
        return result

    source_rows = read_jsonl(SOURCE_SUMMARY)
    rollup_rows = read_jsonl(SCOPE_ROLLUP)
    summary = read_json(SUMMARY)
    manifest = read_json(MANIFEST)

    expected_source_rows = 256104
    expected_matched_rows = 254821
    expected_match_rows = 257194
    if len(source_rows) != 7:
        issues.append(f"source_summary_count_mismatch:{len(source_rows)}")
    if summary.get("source_rows_total") != expected_source_rows:
        issues.append(f"source_rows_total_mismatch:{summary.get('source_rows_total')}:{expected_source_rows}")
    if summary.get("matched_event_rows_total") != expected_matched_rows:
        issues.append(f"matched_event_rows_total_mismatch:{summary.get('matched_event_rows_total')}:{expected_matched_rows}")
    if summary.get("registry_match_rows_total") != expected_match_rows:
        issues.append(f"registry_match_rows_total_mismatch:{summary.get('registry_match_rows_total')}:{expected_match_rows}")
    if summary.get("parse_errors_total") != 0:
        issues.append(f"parse_errors_nonzero:{summary.get('parse_errors_total')}")
    if summary.get("event_scope_rollup_rows") != len(rollup_rows):
        issues.append(f"rollup_count_mismatch:{summary.get('event_scope_rollup_rows')}:{len(rollup_rows)}")
    if summary.get("runtime_behavior") != "DEFAULT_OFF_EVENT_VALIDATION_ONLY_NO_LIVE_ENABLEMENT":
        issues.append("runtime_behavior_missing_default_off_boundary")

    if sum(row.get("source_event_rows", 0) for row in rollup_rows) != expected_source_rows:
        issues.append("rollup_source_event_rows_do_not_sum_to_source_total")
    if sum(row.get("registry_match_rows", 0) for row in rollup_rows) != expected_match_rows:
        issues.append("rollup_registry_match_rows_do_not_sum_to_source_total")
    for row in source_rows[:7] + rollup_rows[:10]:
        row_id = row.get("event_source_summary_row_id") or row.get("event_scope_rollup_row_id")
        for field in (
            "candidate_use_allowed_now",
            "runtime_candidate_use_permitted",
            "runtime_score_allowed",
            "runtime_effect_now",
            "paid_api_or_vendor_call",
            "broker_operation",
        ):
            if row.get(field) is not False:
                issues.append(f"default_off_flag_failed:{row_id}:{field}")
                break
        if not row.get("source_row_hashes_sha256"):
            issues.append(f"missing_source_row_hash_rollup:{row_id}")
            break

    manifest_outputs = {row.get("path"): row for row in (manifest.get("outputs") or [])}
    for path in [SOURCE_SUMMARY, SCOPE_ROLLUP, SUMMARY]:
        key = str(path.resolve().relative_to(REPO.resolve())).replace("\\", "/")
        manifest_row = manifest_outputs.get(key)
        if not manifest_row:
            issues.append(f"manifest_missing_output:{path.name}")
            continue
        if manifest_row.get("sha256") != sha256_path(path):
            issues.append(f"manifest_sha_mismatch:{path.name}")

    result = {
        "ok": not issues,
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "issues": issues,
        "event_source_count": len(source_rows),
        "source_rows_total": summary.get("source_rows_total"),
        "matched_event_rows_total": summary.get("matched_event_rows_total"),
        "registry_match_rows_total": summary.get("registry_match_rows_total"),
        "event_scope_rollup_rows": len(rollup_rows),
    }
    write_json(VERIFY_RESULT, result)
    return result


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2, sort_keys=True))
