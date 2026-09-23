from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_ID = "MAIN_ORCH48_CP281_BRANCH_SCOPE_EVENT_ADAPTER"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]

LEDGER = ROUTE_DIR / f"{ROUTE_ID}_SOURCE_ROLLUP_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"{ROUTE_ID}_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"{ROUTE_ID}_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"{ROUTE_ID}_VERIFY_RESULT_{DATE}.json"


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_lines(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def verify() -> dict[str, Any]:
    issues: list[str] = []
    for path in [LEDGER, SUMMARY, MANIFEST]:
        if not path.exists():
            issues.append(f"missing_output:{path.name}")
    if issues:
        result = {"ok": False, "route_id": ROUTE_ID, "issues": issues}
        write_json(VERIFY_RESULT, result)
        return result

    rows = read_jsonl(LEDGER)
    summary = read_json(SUMMARY)
    manifest = read_json(MANIFEST)

    if len(rows) != 12:
        issues.append(f"event_source_count_mismatch:{len(rows)}")
    if summary.get("event_source_count") != 12:
        issues.append(f"summary_event_source_count_mismatch:{summary.get('event_source_count')}")
    if summary.get("branch_decision_rows") != 107:
        issues.append(f"branch_decision_rows_mismatch:{summary.get('branch_decision_rows')}")
    if summary.get("event_source_rows_total") != 273519:
        issues.append(f"event_source_rows_total_mismatch:{summary.get('event_source_rows_total')}")
    if summary.get("parse_error_rows_total") != 0:
        issues.append(f"parse_errors_nonzero:{summary.get('parse_error_rows_total')}")
    if summary.get("source_rows_with_cp281_branch_scope_events_total") != 8058:
        issues.append(
            "source_rows_with_cp281_branch_scope_events_total_mismatch:"
            f"{summary.get('source_rows_with_cp281_branch_scope_events_total')}"
        )
    if summary.get("derived_cp281_branch_scope_event_rows_total") != 24174:
        issues.append(
            "derived_cp281_branch_scope_event_rows_total_mismatch:"
            f"{summary.get('derived_cp281_branch_scope_event_rows_total')}"
        )
    if summary.get("registry_matched_event_rows_total") != 0:
        issues.append(f"registry_matched_event_rows_nonzero:{summary.get('registry_matched_event_rows_total')}")
    if summary.get("registry_match_rows_total") != 0:
        issues.append(f"registry_match_rows_nonzero:{summary.get('registry_match_rows_total')}")
    if summary.get("adapter_status_counts") != {
        "CP281_BRANCH_SCOPE_EVENTS_DERIVED_WITHOUT_REGISTRY_MATCHES": 3,
        "CP281_BRANCH_SCOPE_EVENTS_NOT_DERIVABLE_FROM_SOURCE": 9,
    }:
        issues.append(f"adapter_status_counts_unexpected:{summary.get('adapter_status_counts')}")
    if summary.get("expected_test_names_covered_rows") != 1:
        issues.append(f"expected_test_names_covered_rows_mismatch:{summary.get('expected_test_names_covered_rows')}")

    for row in rows:
        row_id = row.get("branch_scope_event_adapter_row_id")
        if row.get("parse_error_rows") != 0:
            issues.append(f"parse_error_row:{row_id}")
            break
        if row.get("runtime_candidate_use_permitted") is not False or row.get("candidate_use_allowed_now") is not False:
            issues.append(f"default_off_controls_failed:{row_id}")
            break
        if row.get("production_change_approved") is not False:
            issues.append(f"production_change_not_false:{row_id}")
            break
        if int(row.get("registry_match_rows") or 0) != 0:
            issues.append(f"unexpected_registry_match_rows:{row_id}")
            break

    manifest_outputs = manifest.get("outputs") or []
    if len(manifest_outputs) != 2:
        issues.append(f"manifest_output_count_mismatch:{len(manifest_outputs)}")
    for item in manifest_outputs:
        output_path = REPO / item["path"]
        if not output_path.exists():
            issues.append(f"manifest_missing_path:{item['path']}")
            continue
        if sha256_path(output_path) != item.get("sha256"):
            issues.append(f"manifest_sha_mismatch:{item['path']}")
        if count_lines(output_path) != item.get("lines"):
            issues.append(f"manifest_line_mismatch:{item['path']}")

    effect = summary.get("implementation_effect") or {}
    for field in [
        "broker_operation",
        "paid_api_or_vendor_call",
        "runtime_candidate_use_permitted",
        "candidate_use_allowed_now",
        "production_import_path",
        "mutates_order_risk_prompt_safety_or_mt5",
    ]:
        if effect.get(field) is not False:
            issues.append(f"implementation_effect_not_false:{field}")

    result = {
        "ok": not issues,
        "route_id": ROUTE_ID,
        "generated_from": "verify_main_orch48_cp281_branch_scope_event_adapter_2026_05_18.py",
        "event_source_count": len(rows),
        "event_source_rows_total": summary.get("event_source_rows_total"),
        "source_rows_with_cp281_branch_scope_events_total": summary.get(
            "source_rows_with_cp281_branch_scope_events_total"
        ),
        "derived_cp281_branch_scope_event_rows_total": summary.get(
            "derived_cp281_branch_scope_event_rows_total"
        ),
        "registry_match_rows_total": summary.get("registry_match_rows_total"),
        "adapter_status_counts": summary.get("adapter_status_counts"),
        "manifest_output_count": len(manifest_outputs),
        "issues": issues,
        "can_continue_to_next_system_conversion_plate": not issues,
    }
    write_json(VERIFY_RESULT, result)
    return result


if __name__ == "__main__":
    print(json.dumps(verify(), sort_keys=True))
