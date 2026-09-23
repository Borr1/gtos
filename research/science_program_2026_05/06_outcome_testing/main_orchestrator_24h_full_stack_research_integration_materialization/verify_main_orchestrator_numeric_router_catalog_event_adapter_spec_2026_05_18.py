from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
FIELD_AVAILABILITY_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_EVENT_FIELD_AVAILABILITY_LEDGER_{DATE}.jsonl"
LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_EVENT_ADAPTER_SPEC_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_EVENT_ADAPTER_SPEC_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_EVENT_ADAPTER_SPEC_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_EVENT_ADAPTER_SPEC_VERIFY_RESULT_{DATE}.json"


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
    for path in (FIELD_AVAILABILITY_LEDGER, LEDGER, SUMMARY, MANIFEST):
        if not path.exists():
            issues.append(f"missing_output:{path.name}")

    rows = read_jsonl(LEDGER) if LEDGER.exists() else []
    summary = read_json(SUMMARY) if SUMMARY.exists() else {}
    manifest = read_json(MANIFEST) if MANIFEST.exists() else {}

    if summary.get("adapter_spec_rows") != len(rows):
        issues.append("adapter_spec_rows_mismatch")
    if len(rows) != 49:
        issues.append(f"adapter_spec_rows_unexpected:{len(rows)}")
    if summary.get("source_count") != 7 or summary.get("required_field_count") != 7:
        issues.append("source_or_field_count_unexpected")

    resolution_counts = summary.get("adapter_resolution_counts") or {}
    if resolution_counts.get("DIRECT_FIELD_PRESENT", 0) <= 0:
        issues.append("no_direct_fields_present")
    if resolution_counts.get("ALIAS_AVAILABLE_NEEDS_ADAPTER_MAPPING", 0) <= 0:
        issues.append("no_alias_mappings_available")
    if resolution_counts.get("MISSING_REQUIRES_UPSTREAM_CAPTURE", 0) <= 0:
        issues.append("no_missing_capture_fields")

    for key in (
        "runtime_score_allowed_rows",
        "runtime_candidate_use_permitted_rows",
        "candidate_use_allowed_now_rows",
        "unconditional_scalar_use_allowed_rows",
        "replay_r_reference_counted_as_new_main_result_rows",
    ):
        if summary.get(key) != 0:
            issues.append(f"{key}_nonzero")
            break

    input_ledger = summary.get("input_field_availability_ledger") or {}
    if input_ledger.get("sha256") != sha256_path(FIELD_AVAILABILITY_LEDGER):
        issues.append("input_field_availability_hash_mismatch")
    if input_ledger.get("rows") != 7:
        issues.append("input_field_availability_rows_unexpected")

    output_by_name = {Path(item["path"]).name: item for item in manifest.get("outputs") or []}
    for path in (LEDGER, SUMMARY):
        item = output_by_name.get(path.name)
        if not item:
            issues.append(f"manifest_missing_output:{path.name}")
            continue
        if item.get("sha256") != sha256_path(path):
            issues.append(f"manifest_hash_mismatch:{path.name}")
        if path.suffix == ".jsonl" and path.stat().st_size >= 100_000_000:
            issues.append(f"raw_jsonl_over_github_limit:{path.name}")

    for row in rows:
        row_id = row.get("adapter_spec_row_id")
        if not row.get("adapter_resolution"):
            issues.append(f"adapter_resolution_missing:{row_id}")
            break
        if not row.get("adapter_action"):
            issues.append(f"adapter_action_missing:{row_id}")
            break
        if not row.get("alias_candidates"):
            issues.append(f"alias_candidates_missing:{row_id}")
            break
        if row.get("runtime_score_allowed") is not False:
            issues.append(f"runtime_score_allowed:{row_id}")
            break
        if row.get("runtime_candidate_use_permitted") is not False or row.get("candidate_use_allowed_now") is not False:
            issues.append(f"runtime_or_candidate_use_enabled:{row_id}")
            break
        if row.get("replay_r_reference_counted_as_new_main_result") is not False:
            issues.append(f"replay_r_counted:{row_id}")
            break

    result = {
        "route_id": "MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_EVENT_ADAPTER_SPEC",
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "adapter_spec_rows": len(rows),
        "adapter_resolution_counts": resolution_counts,
        "field_resolution_counts": summary.get("field_resolution_counts") or {},
        "manifest_output_count": len(output_by_name),
        "can_continue_to_next_system_conversion_plate": not issues,
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
