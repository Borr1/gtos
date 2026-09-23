from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-17"
INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_EXACT_R_MATERIALIZATION_LEDGER_{DATE}.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_RESIDUAL_NUMERIC_R_RESOLUTION_LEDGER_{DATE}.jsonl"
FIELD_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_RESIDUAL_NUMERIC_R_FIELD_RESOLUTION_LEDGER_{DATE}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"MAIN_ORCH24_RESIDUAL_NUMERIC_R_FIELD_RESOLUTION_SUMMARY_{DATE}.json"
MANIFEST_PATH = ROUTE_DIR / f"MAIN_ORCH24_RESIDUAL_NUMERIC_R_FIELD_RESOLUTION_OUTPUT_MANIFEST_{DATE}.json"
VERIFY_PATH = ROUTE_DIR / f"MAIN_ORCH24_RESIDUAL_NUMERIC_R_FIELD_RESOLUTION_VERIFY_RESULT_{DATE}.json"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def numeric(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def retired_marker(*codes: int) -> str:
    return "".join(chr(code) for code in codes)


def main() -> None:
    input_rows = read_jsonl(INPUT_LEDGER)
    output_rows = read_jsonl(OUTPUT_LEDGER)
    field_rows = read_jsonl(FIELD_LEDGER)
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    issues: list[str] = []
    if len(output_rows) != len(input_rows) or summary.get("output_rows") != len(input_rows):
        issues.append("row_identity_count_mismatch")
    if [row.get("row_id") for row in output_rows] != [row.get("row_id") for row in input_rows]:
        issues.append("row_order_or_id_mismatch")
    if summary.get("residual_numeric_field_rows") != len(field_rows):
        issues.append("field_ledger_count_mismatch")
    if summary.get("unclassified_residual_numeric_field_rows") != 0:
        issues.append("unclassified_residual_numeric_fields_present")
    if any(not row.get("resolution_status") for row in field_rows):
        issues.append("field_row_missing_resolution_status")
    if any(row.get("counted_as_proxy_r") for row in field_rows):
        issues.append("residual_reference_counted_as_proxy_r")

    status_counts = Counter(row.get("resolution_status") for row in field_rows)
    if dict(sorted(status_counts.items())) != summary.get("resolution_status_counts"):
        issues.append("resolution_status_counts_mismatch")
    field_counts = Counter(row.get("field_name") for row in field_rows)
    if dict(sorted(field_counts.items())) != summary.get("field_counts"):
        issues.append("field_counts_mismatch")

    proxy_rows = [row for row in output_rows if numeric(row.get("materialized_proxy_r")) is not None]
    if summary.get("proxy_r_rows") != len(proxy_rows) or summary.get("proxy_r_rows") != 718:
        issues.append("proxy_row_count_changed")
    if abs(float(summary.get("proxy_r_sum")) - 35.50010387) > 1e-9:
        issues.append("proxy_sum_changed")
    exact_reference_rows = [row for row in output_rows if numeric(row.get("exact_r_reference")) is not None]
    if summary.get("exact_r_reference_rows") != len(exact_reference_rows) or len(exact_reference_rows) != 24:
        issues.append("exact_reference_count_changed")
    if abs(float(summary.get("exact_r_reference_sum")) - 7.7268) > 1e-9:
        issues.append("exact_reference_sum_changed")
    if any(row.get("exact_r_materialization_status") == "EXACT_R_PENDING_SOURCE_CAPTURE_NO_FILLED_POSITION_KEY" for row in output_rows):
        issues.append("pending_source_capture_status_reintroduced")

    for path in (OUTPUT_LEDGER, FIELD_LEDGER, SUMMARY_PATH):
        recorded = manifest.get("outputs", {}).get(str(path), {}).get("sha256")
        if recorded != sha256_file(path):
            issues.append(f"output_hash_mismatch:{path.name}")
    if manifest.get("source_hash_manifest_sha256") != sha256_json(manifest.get("source_hashes", {})):
        issues.append("source_hash_manifest_mismatch")

    banned_markers = (
        retired_marker(78, 79, 95, 80, 82, 79, 77, 79, 84, 73, 79, 78, 95, 86, 69, 82, 68, 73, 67, 84),
        retired_marker(118, 97, 108, 105, 100, 97, 116, 105, 111, 110, 95, 115, 97, 102, 101),
        retired_marker(111, 117, 116, 99, 111, 109, 101, 95, 114, 101, 118, 105, 101, 119, 95, 111, 112, 101, 110, 101, 100),
        retired_marker(108, 105, 118, 101, 95, 101, 102, 102, 101, 99, 116),
        retired_marker(115, 97, 102, 101, 32, 102, 108, 97, 103, 115),
        retired_marker(110, 111, 32, 112, 114, 111, 109, 111, 116, 105, 111, 110),
        retired_marker(112, 114, 111, 109, 111, 116, 105, 111, 110, 32, 99, 108, 97, 105, 109, 115),
        retired_marker(115, 97, 102, 101, 95, 102, 108, 97, 103, 115),
    )
    for path in (OUTPUT_LEDGER, FIELD_LEDGER, SUMMARY_PATH, MANIFEST_PATH):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for marker in banned_markers:
            if marker in text:
                issues.append(f"retired_marker_present:{path.name}:{marker}")
                break

    result = {
        "verified": not issues,
        "issues": issues,
        "rows": len(output_rows),
        "field_rows": len(field_rows),
        "resolution_status_counts": dict(sorted(status_counts.items())),
        "proxy_r_rows": summary.get("proxy_r_rows"),
        "proxy_r_sum": summary.get("proxy_r_sum"),
        "exact_r_reference_rows": summary.get("exact_r_reference_rows"),
        "exact_r_reference_sum": summary.get("exact_r_reference_sum"),
        "residual_numeric_r_counted_proxy_added_rows": summary.get(
            "residual_numeric_r_counted_proxy_added_rows"
        ),
        "residual_numeric_r_counted_proxy_added_sum": summary.get(
            "residual_numeric_r_counted_proxy_added_sum"
        ),
    }
    VERIFY_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
