from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
REPO = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_EXPANDED_MARKET_LEAKAGE_INTAKE_SUMMARY_{DATE}.json"
LEDGER = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_EXPANDED_MARKET_LEAKAGE_INTAKE_LEDGER_{DATE}.jsonl"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_EXPANDED_MARKET_LEAKAGE_INTAKE_OUTPUT_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_EXPANDED_MARKET_LEAKAGE_INTAKE_VERIFY_RESULT_{DATE}.json"


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

    expected_rows = int((summary.get("moonshot_leakage_result_counts") or {}).get("leakage_reduction_rows") or -1)
    if len(rows) != expected_rows:
        issues.append(f"ledger_row_count_mismatch:{len(rows)}!={expected_rows}")

    intake_summary = summary.get("intake_summary") or {}
    if intake_summary.get("rows") != len(rows):
        issues.append("summary_rows_mismatch")
    if intake_summary.get("proxy_r_reference_counted_as_result_rows") != 0:
        issues.append("proxy_r_references_counted_as_results")
    if intake_summary.get("runtime_candidate_use_permitted_rows") != 0:
        issues.append("runtime_candidate_use_permitted_rows_nonzero")

    decision_counts = summary.get("moonshot_leakage_result_counts", {}).get("decision_counts") or {}
    if decision_counts.get("IMPLEMENT_EXPANDED_MARKET_LEAKAGE_REDUCED_CODE_CANDIDATE") != 1724:
        issues.append("unexpected_reduced_code_candidate_count")
    if decision_counts.get("IMPLEMENT_EXPANDED_MARKET_CODE_CANDIDATE_EXECUTION_PRESERVED") != 24:
        issues.append("unexpected_preserved_code_candidate_count")
    if summary.get("moonshot_leakage_result_counts", {}).get("remaining_repair_rows") != 0:
        issues.append("moonshot_remaining_repair_rows_nonzero")

    output_by_name = {Path(item["path"]).name: item for item in manifest.get("outputs") or []}
    for path in (SUMMARY, LEDGER):
        item = output_by_name.get(path.name)
        if not item:
            issues.append(f"manifest_missing_output:{path.name}")
            continue
        if item.get("sha256") != sha256_path(path):
            issues.append(f"manifest_hash_mismatch:{path.name}")

    source_manifest = summary.get("source_manifest") or []
    for source in source_manifest:
        source_path = Path(source.get("absolute_path") or "")
        if not source_path.exists():
            issues.append(f"missing_source:{source.get('path')}")
            continue
        if source.get("sha256") != sha256_path(source_path):
            issues.append(f"source_hash_mismatch:{source.get('path')}")

    seen_ids = set()
    for row in rows:
        row_id = row.get("intake_row_id")
        if row_id in seen_ids:
            issues.append(f"duplicate_intake_row_id:{row_id}")
            break
        seen_ids.add(row_id)
        boundary = row.get("research_boundary") or {}
        if boundary.get("runtime_candidate_use_permitted") is not False:
            issues.append(f"row_runtime_permitted:{row_id}")
            break
        if row.get("proxy_r_reference_counted_as_result") is not False:
            issues.append(f"row_proxy_r_counted:{row_id}")
            break

    result = {
        "route_id": "MAIN_ORCH48_MOONSHOT_EXPANDED_MARKET_LEAKAGE_INTAKE",
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "ledger_rows": len(rows),
        "expected_rows": expected_rows,
        "source_count": len(source_manifest),
        "manifest_output_count": len(output_by_name),
        "decision_counts": decision_counts,
        "can_continue_to_next_system_conversion_plate": not issues,
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
