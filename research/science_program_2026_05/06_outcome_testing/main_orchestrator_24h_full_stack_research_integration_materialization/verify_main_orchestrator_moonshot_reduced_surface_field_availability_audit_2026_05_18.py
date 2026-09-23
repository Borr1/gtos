from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_FIELD_AVAILABILITY_SUMMARY_{DATE}.json"
LEDGER = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_FIELD_AVAILABILITY_LEDGER_{DATE}.jsonl"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_FIELD_AVAILABILITY_OUTPUT_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_FIELD_AVAILABILITY_VERIFY_RESULT_{DATE}.json"


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
    for path in (SUMMARY, LEDGER, MANIFEST):
        if not path.exists():
            issues.append(f"missing_output:{path.name}")

    summary = read_json(SUMMARY) if SUMMARY.exists() else {}
    manifest = read_json(MANIFEST) if MANIFEST.exists() else {}
    rows = read_jsonl(LEDGER) if LEDGER.exists() else []

    if summary.get("contract_rows") != 1748:
        issues.append("contract_rows_unexpected")
    if summary.get("event_source_count") != len(rows):
        issues.append("event_source_count_mismatch")
    if len(rows) != 7:
        issues.append(f"ledger_row_count_unexpected:{len(rows)}")
    if int(summary.get("event_source_rows_total") or 0) <= 0:
        issues.append("event_source_rows_total_zero")
    if int(summary.get("rows_with_leakage_reduced_required_fields_total") or 0) != 0:
        issues.append("current_sources_unexpectedly_feed_full_leakage_contract")

    output_by_name = {Path(item["path"]).name: item for item in manifest.get("outputs") or []}
    for path in (SUMMARY, LEDGER):
        item = output_by_name.get(path.name)
        if not item:
            issues.append(f"manifest_missing_output:{path.name}")
            continue
        if item.get("sha256") != sha256_path(path):
            issues.append(f"manifest_hash_mismatch:{path.name}")

    contract_ledger = Path(summary.get("contract_ledger") or "")
    if contract_ledger.exists():
        if summary.get("contract_ledger_sha256") != sha256_path(contract_ledger):
            issues.append("contract_ledger_hash_mismatch")
    else:
        issues.append("contract_ledger_missing")

    for row in rows:
        if row.get("event_source_exists") is not True:
            issues.append(f"event_source_missing:{row.get('event_source_path')}")
            break
        if int(row.get("parse_error_rows") or 0) != 0:
            issues.append(f"parse_errors:{row.get('event_source_path')}")
            break
        if row.get("runtime_candidate_use_permitted") is not False or row.get("candidate_use_allowed_now") is not False:
            issues.append(f"row_runtime_or_candidate_use_enabled:{row.get('event_source_path')}")
            break
        if row.get("replay_r_reference_counted_as_new_main_result") is not False:
            issues.append(f"row_replay_r_counted:{row.get('event_source_path')}")
            break

    result = {
        "route_id": "MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_FIELD_AVAILABILITY_AUDIT",
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "ledger_rows": len(rows),
        "event_source_rows_total": summary.get("event_source_rows_total"),
        "rows_with_base_required_fields_total": summary.get("rows_with_base_required_fields_total"),
        "rows_with_leakage_reduced_required_fields_total": summary.get(
            "rows_with_leakage_reduced_required_fields_total"
        ),
        "manifest_output_count": len(output_by_name),
        "can_continue_to_next_system_conversion_plate": not issues,
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
