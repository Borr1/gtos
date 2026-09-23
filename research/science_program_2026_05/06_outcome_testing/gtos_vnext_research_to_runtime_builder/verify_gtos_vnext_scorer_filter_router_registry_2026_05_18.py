from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_ID = "GTOS_VNEXT_SCORER_FILTER_ROUTER_REGISTRY"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]

if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.gtos_vnext_evidence_system import (  # noqa: E402
    SCHEMA_VERSION,
    read_jsonl,
    sha256_path,
)


CATALOG = ROUTE_DIR / f"{ROUTE_ID}_CATALOG_LEDGER_{DATE}.jsonl"
SELF_CHECK = ROUTE_DIR / f"{ROUTE_ID}_SELF_CHECK_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"{ROUTE_ID}_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"{ROUTE_ID}_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"{ROUTE_ID}_VERIFY_RESULT_{DATE}.json"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def verify() -> dict[str, Any]:
    issues: list[str] = []
    required = [CATALOG, SELF_CHECK, SUMMARY, MANIFEST]
    for path in required:
        if not path.exists():
            issues.append(f"missing_output:{path.name}")
    if issues:
        result = {"ok": False, "route_id": ROUTE_ID, "schema_version": SCHEMA_VERSION, "issues": issues}
        write_json(VERIFY_RESULT, result)
        return result

    catalog_rows = read_jsonl(CATALOG)
    self_check_rows = read_jsonl(SELF_CHECK)
    summary = read_json(SUMMARY)
    manifest = read_json(MANIFEST)

    if len(catalog_rows) != 17496:
        issues.append(f"catalog_count_mismatch:{len(catalog_rows)}")
    if len(self_check_rows) != 17496:
        issues.append(f"self_check_count_mismatch:{len(self_check_rows)}")
    if summary.get("input_registry_rows") != len(catalog_rows):
        issues.append(f"summary_input_rows_mismatch:{summary.get('input_registry_rows')}:{len(catalog_rows)}")
    if summary.get("self_check_rows") != len(self_check_rows):
        issues.append(f"summary_self_check_rows_mismatch:{summary.get('self_check_rows')}:{len(self_check_rows)}")
    if summary.get("runtime_behavior") != "DEFAULT_OFF_REGISTRY_ONLY_NO_LIVE_ENABLEMENT":
        issues.append("runtime_behavior_missing_default_off_boundary")

    status_counts = summary.get("self_check_status_counts") or {}
    if status_counts.get("FAIL_SELF_MATCH_MISSING", 0):
        issues.append(f"self_check_failures:{status_counts.get('FAIL_SELF_MATCH_MISSING')}")
    if status_counts.get("PASS_SELF_MATCH_FOUND", 0) != summary.get("callable_event_match_rows"):
        issues.append("callable_rows_do_not_equal_pass_self_matches")
    if (
        status_counts.get("CATALOG_ONLY_NO_EVENT_SCOPE", 0)
        != summary.get("catalog_only_no_event_scope_rows")
    ):
        issues.append("catalog_only_rows_do_not_equal_catalog_status_count")

    for row in catalog_rows[:10] + self_check_rows[:10]:
        row_id = row.get("registry_catalog_row_id") or row.get("self_check_row_id")
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

    manifest_outputs = {row.get("path"): row for row in (manifest.get("outputs") or [])}
    for path in [CATALOG, SELF_CHECK, SUMMARY]:
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
        "catalog_rows": len(catalog_rows),
        "self_check_rows": len(self_check_rows),
        "self_check_status_counts": status_counts,
        "callable_event_match_rows": summary.get("callable_event_match_rows"),
        "catalog_only_no_event_scope_rows": summary.get("catalog_only_no_event_scope_rows"),
    }
    write_json(VERIFY_RESULT, result)
    return result


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2, sort_keys=True))
