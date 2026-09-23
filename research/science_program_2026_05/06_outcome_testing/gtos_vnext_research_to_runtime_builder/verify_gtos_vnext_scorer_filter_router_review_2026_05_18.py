from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_ID = "GTOS_VNEXT_SCORER_FILTER_ROUTER_REVIEW"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]

if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.gtos_vnext_evidence_system import (  # noqa: E402
    SCHEMA_VERSION,
    read_jsonl,
    sha256_path,
)


REVIEW_LEDGER = ROUTE_DIR / f"{ROUTE_ID}_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"{ROUTE_ID}_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"{ROUTE_ID}_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"{ROUTE_ID}_VERIFY_RESULT_{DATE}.json"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def verify() -> dict[str, Any]:
    issues: list[str] = []
    for path in [REVIEW_LEDGER, SUMMARY, MANIFEST]:
        if not path.exists():
            issues.append(f"missing_output:{path.name}")
    if issues:
        result = {"ok": False, "route_id": ROUTE_ID, "schema_version": SCHEMA_VERSION, "issues": issues}
        write_json(VERIFY_RESULT, result)
        return result

    rows = read_jsonl(REVIEW_LEDGER)
    summary = read_json(SUMMARY)
    manifest = read_json(MANIFEST)
    if len(rows) != 109:
        issues.append(f"review_row_count_mismatch:{len(rows)}")
    if summary.get("review_rows") != len(rows):
        issues.append(f"summary_review_rows_mismatch:{summary.get('review_rows')}:{len(rows)}")
    if summary.get("source_event_rows_total") != 256104:
        issues.append(f"source_event_rows_total_mismatch:{summary.get('source_event_rows_total')}")
    if summary.get("registry_match_rows_total") != 257194:
        issues.append(f"registry_match_rows_total_mismatch:{summary.get('registry_match_rows_total')}")
    if summary.get("registry_match_row_count_verified_rows") != len(rows):
        issues.append("registry_match_row_count_not_verified_for_all_rows")
    if summary.get("all_event_scope_rollups_preserved") is not True:
        issues.append("all_event_scope_rollups_preserved_not_true")
    if summary.get("runtime_behavior") != "DEFAULT_OFF_REVIEW_ONLY_NO_LIVE_ENABLEMENT":
        issues.append("runtime_behavior_missing_default_off_boundary")

    action_counts = dict(sorted(Counter(row.get("review_action") for row in rows).items()))
    if action_counts != summary.get("review_action_counts"):
        issues.append("review_action_counts_mismatch")
    if not action_counts:
        issues.append("review_action_counts_empty")
    if any(row.get("registry_match_row_count_verified") is not True for row in rows):
        issues.append("some_review_rows_failed_match_count_verification")
    if len({row.get("event_scope_rollup_row_id") for row in rows}) != len(rows):
        issues.append("duplicate_or_missing_event_scope_rollup_ids")

    for row in rows[:10]:
        row_id = row.get("review_row_id")
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
        if not row.get("source_row_hashes_sha256") or not row.get("matched_matrix_row_ids_sha256"):
            issues.append(f"missing_hash_anchor:{row_id}")
            break

    manifest_outputs = {row.get("path"): row for row in (manifest.get("outputs") or [])}
    for path in [REVIEW_LEDGER, SUMMARY]:
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
        "review_rows": len(rows),
        "source_event_rows_total": summary.get("source_event_rows_total"),
        "registry_match_rows_total": summary.get("registry_match_rows_total"),
        "review_action_counts": action_counts,
    }
    write_json(VERIFY_RESULT, result)
    return result


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2, sort_keys=True))
