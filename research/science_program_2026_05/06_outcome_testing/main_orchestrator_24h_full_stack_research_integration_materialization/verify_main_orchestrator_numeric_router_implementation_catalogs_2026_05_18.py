from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
FAMILY_SPEC_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_FAMILY_ACTION_SPEC_LEDGER_{DATE}.jsonl"
CATALOG_LEDGER_BY_TYPE = {
    "default_off_scorer_registry_catalog_entry": ROUTE_DIR
    / f"MAIN_ORCH48_NUMERIC_ROUTER_SCORER_REGISTRY_CATALOG_LEDGER_{DATE}.jsonl",
    "default_off_avoid_filter_catalog_entry": ROUTE_DIR
    / f"MAIN_ORCH48_NUMERIC_ROUTER_AVOID_FILTER_CATALOG_LEDGER_{DATE}.jsonl",
    "default_off_context_guard_catalog_entry": ROUTE_DIR
    / f"MAIN_ORCH48_NUMERIC_ROUTER_CONTEXT_GUARD_CATALOG_LEDGER_{DATE}.jsonl",
    "source_repair_queue_entry": ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_QUEUE_LEDGER_{DATE}.jsonl",
}
SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_IMPLEMENTATION_CATALOG_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_IMPLEMENTATION_CATALOG_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_IMPLEMENTATION_CATALOG_VERIFY_RESULT_{DATE}.json"


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def verify() -> dict[str, Any]:
    issues: list[str] = []
    for path in [FAMILY_SPEC_LEDGER, SUMMARY, MANIFEST, *CATALOG_LEDGER_BY_TYPE.values()]:
        if not path.exists():
            issues.append(f"missing_output:{path.name}")

    rows_by_type = {
        catalog_type: read_jsonl(path) if path.exists() else []
        for catalog_type, path in CATALOG_LEDGER_BY_TYPE.items()
    }
    rows = [row for catalog_rows in rows_by_type.values() for row in catalog_rows]
    summary = read_json(SUMMARY) if SUMMARY.exists() else {}
    manifest = read_json(MANIFEST) if MANIFEST.exists() else {}

    if summary.get("catalog_rows") != len(rows):
        issues.append("catalog_rows_mismatch")
    if len(rows) != 2191:
        issues.append(f"catalog_rows_unexpected:{len(rows)}")
    if summary.get("input_action_rows") != 28722:
        issues.append(f"input_action_rows_unexpected:{summary.get('input_action_rows')}")

    expected_catalog_counts = {
        "default_off_scorer_registry_catalog_entry": 340,
        "default_off_avoid_filter_catalog_entry": 470,
        "default_off_context_guard_catalog_entry": 262,
        "source_repair_queue_entry": 1119,
    }
    catalog_counts = summary.get("catalog_type_counts") or {}
    for catalog_type, expected in expected_catalog_counts.items():
        if catalog_counts.get(catalog_type) != expected:
            issues.append(f"catalog_count_unexpected:{catalog_type}")
            break
        if len(rows_by_type.get(catalog_type) or []) != expected:
            issues.append(f"ledger_catalog_count_unexpected:{catalog_type}")
            break

    expected_priority_action_counts = {
        "P0_SOURCE_REPAIR_EXACT_R_GEOMETRY": 10597,
        "P0_SOURCE_REPAIR_JOIN_ABSENCE_PROOF": 7045,
        "P0_SOURCE_REPAIR_SPREAD_GEOMETRY_ATTACHMENT": 111,
        "P1_AVOID_AMBIGUOUS_NEGATIVE_PROXY_FAIL_CLOSED": 29,
        "P1_AVOID_STOP_FIRST_PROXY": 932,
        "P2_AVOID_NEGATIVE_PROXY_FAILURE_FEATURE": 3154,
        "P3_SCORER_DEFAULT_OFF_SURFACE": 5341,
        "P4_CONTEXT_STRESS_GUARD_INPUT": 1513,
    }
    bucket_action_counts = summary.get("catalog_priority_bucket_input_action_counts") or {}
    for bucket, expected in expected_priority_action_counts.items():
        if bucket_action_counts.get(bucket) != expected:
            issues.append(f"priority_bucket_action_count_unexpected:{bucket}")
            break

    for key in (
        "live_effect_rows",
        "runtime_score_allowed_rows",
        "runtime_candidate_use_permitted_rows",
        "candidate_use_allowed_now_rows",
        "unconditional_scalar_use_allowed_rows",
        "replay_r_reference_counted_as_new_main_result_rows",
    ):
        if summary.get(key) != 0:
            issues.append(f"{key}_nonzero")
            break

    input_family_spec_ledger = summary.get("input_family_spec_ledger") or {}
    if input_family_spec_ledger.get("sha256") != sha256_path(FAMILY_SPEC_LEDGER):
        issues.append("input_family_spec_ledger_hash_mismatch")
    if input_family_spec_ledger.get("rows") != 2191:
        issues.append("input_family_spec_ledger_rows_unexpected")

    output_by_name = {Path(item["path"]).name: item for item in manifest.get("outputs") or []}
    for path in [*CATALOG_LEDGER_BY_TYPE.values(), SUMMARY]:
        item = output_by_name.get(path.name)
        if not item:
            issues.append(f"manifest_missing_output:{path.name}")
            continue
        if item.get("sha256") != sha256_path(path):
            issues.append(f"manifest_hash_mismatch:{path.name}")
        if path.suffix == ".jsonl" and path.stat().st_size >= 100_000_000:
            issues.append(f"raw_jsonl_over_github_limit:{path.name}")

    expected_type_by_name = {
        path.name: catalog_type for catalog_type, path in CATALOG_LEDGER_BY_TYPE.items()
    }
    for catalog_type, catalog_rows in rows_by_type.items():
        for row in catalog_rows:
            row_id = row.get("numeric_router_catalog_entry_id")
            if "source_row" in row:
                issues.append(f"source_payload_duplicated:{row_id}")
                break
            if row.get("catalog_type") != catalog_type:
                issues.append(f"catalog_type_mismatch:{row_id}")
                break
            if row.get("activation_state") != "DEFAULT_OFF":
                issues.append(f"activation_state_not_default_off:{row_id}")
                break
            if int(row.get("input_action_rows") or 0) <= 0:
                issues.append(f"input_action_rows_empty:{row_id}")
                break
            if not row.get("source_locator_refs"):
                issues.append(f"source_locator_refs_missing:{row_id}")
                break
            if not row.get("recommended_next_step"):
                issues.append(f"recommended_next_step_missing:{row_id}")
                break
            if row.get("runtime_score_allowed") is not False:
                issues.append(f"runtime_score_allowed:{row_id}")
                break
            if row.get("runtime_candidate_use_permitted") is not False or row.get("candidate_use_allowed_now") is not False:
                issues.append(f"runtime_or_candidate_use_enabled:{row_id}")
                break
            if row.get("live_effect") is not False:
                issues.append(f"live_effect_enabled:{row_id}")
                break
            if row.get("replay_r_reference_counted_as_new_main_result") is not False:
                issues.append(f"replay_r_counted:{row_id}")
                break
        if issues:
            break

    result = {
        "route_id": "MAIN_ORCH48_NUMERIC_ROUTER_IMPLEMENTATION_CATALOGS",
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "catalog_rows": len(rows),
        "input_action_rows": summary.get("input_action_rows"),
        "catalog_type_counts": catalog_counts,
        "catalog_priority_bucket_input_action_counts": bucket_action_counts,
        "manifest_output_count": len(output_by_name),
        "expected_type_by_name": expected_type_by_name,
        "can_continue_to_next_system_conversion_plate": not issues,
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
