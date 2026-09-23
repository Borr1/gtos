from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-17"
INPUT_ACTION_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_ENTRY_OFFSET_CONCENTRATION_GUARD_LEDGER_{DATE}.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_EXACT_R_MATERIALIZATION_LEDGER_{DATE}.jsonl"
ALIAS_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_EXACT_R_ALIAS_SEARCH_LEDGER_{DATE}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_EXACT_R_MATERIALIZATION_SUMMARY_{DATE}.json"
MANIFEST_PATH = ROUTE_DIR / f"MAIN_ORCH24_EXACT_R_MATERIALIZATION_OUTPUT_MANIFEST_{DATE}.json"
VERIFY_PATH = ROUTE_DIR / f"MAIN_ORCH24_EXACT_R_MATERIALIZATION_VERIFICATION_RESULT_{DATE}.json"


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


def main() -> None:
    input_rows = read_jsonl(INPUT_ACTION_LEDGER)
    rows = read_jsonl(OUTPUT_LEDGER)
    alias_rows = read_jsonl(ALIAS_LEDGER)
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    issues: list[str] = []
    if len(rows) != len(input_rows) or summary.get("output_rows") != len(rows):
        issues.append("row_count_mismatch")
    if len(alias_rows) != len({row.get("candidate_id") for row in input_rows if row.get("candidate_id")}):
        issues.append("alias_candidate_count_mismatch")
    for path in (OUTPUT_LEDGER, ALIAS_LEDGER, SUMMARY_PATH):
        recorded = manifest.get("outputs", {}).get(str(path), {}).get("sha256")
        if recorded != sha256_file(path):
            issues.append(f"output_hash_mismatch:{path.name}")
    if manifest.get("source_hash_manifest_sha256") != sha256_json(manifest.get("source_hashes", {})):
        issues.append("source_hash_manifest_mismatch")

    status_counts = Counter(row.get("exact_r_materialization_status") for row in rows)
    if dict(sorted(status_counts.items())) != summary.get("status_counts"):
        issues.append("status_counts_mismatch")
    if status_counts.get("EXACT_R_NOT_LOCAL_COMPUTABLE_ACCOUNT_HISTORY_CLOSE_DEAL_MISSING", 0):
        issues.append("missing_close_deal_status_not_resolved")
    if status_counts.get("EXACT_R_NOT_LOCAL_COMPUTABLE_IDENTIFIER_ABSENT_AFTER_FULL_LOCAL_SEARCH", 0):
        issues.append("generic_missing_identifier_status_not_repaired")
    if status_counts.get("EXACT_R_PENDING_SOURCE_CAPTURE_NO_FILLED_POSITION_KEY", 0):
        issues.append("source_capture_rows_not_consumed_into_proxy_or_noncomputable_disposition")

    owner_rows = [row for row in rows if row.get("exact_r_materialization_status") == "EXACT_R_OWNER_MATERIALIZED"]
    if len(owner_rows) != 2:
        issues.append("owner_count_mismatch")
    else:
        owner_by_candidate = {row.get("candidate_id"): row for row in owner_rows}
        gbpjpy_owner = owner_by_candidate.get("GBPJPY_2026-05-11T07:30:00+00:00")
        xagusd_owner = owner_by_candidate.get("XAGUSD_2026-05-14T13:15:00+00:00")
        if not gbpjpy_owner:
            issues.append("gbpjpy_owner_missing")
        else:
            if gbpjpy_owner.get("row_id") != "MAIN-ORCH24-ACTION-SRCM15-00082":
                issues.append("gbpjpy_owner_row_id_mismatch")
            if abs(float(gbpjpy_owner.get("exact_r")) - 0.615) > 1e-9:
                issues.append("gbpjpy_owner_exact_r_mismatch")
            if abs(float(gbpjpy_owner.get("materialized_proxy_r")) - 1.5) > 1e-9:
                issues.append("gbpjpy_owner_proxy_mismatch")
            if abs(float(gbpjpy_owner.get("exact_proxy_delta")) + 0.885) > 1e-9:
                issues.append("gbpjpy_owner_exact_proxy_delta_mismatch")
        if not xagusd_owner:
            issues.append("xagusd_owner_missing")
        else:
            if abs(float(xagusd_owner.get("exact_r")) - 0.0289) > 1e-9:
                issues.append("xagusd_owner_exact_r_mismatch")
            if xagusd_owner.get("exact_r_source_type") not in {"ACCOUNT_HISTORY_REALIZED_R", "BROKER_ACTUAL_R_AUDIT"}:
                issues.append("xagusd_owner_source_type_mismatch")
            if xagusd_owner.get("exact_r_mt5_deal_id") != 222552477:
                issues.append("xagusd_owner_mt5_deal_mismatch")
        if any(row.get("exact_r_duplicate_policy") != "COUNT_ON_OWNER_ROW_ONLY" for row in owner_rows):
            issues.append("owner_duplicate_policy_mismatch")

    reference_rows = [row for row in rows if numeric(row.get("exact_r_reference")) is not None]
    if len(reference_rows) != 24:
        issues.append("reference_count_mismatch")
    if sum(1 for row in reference_rows if numeric(row.get("exact_r")) is not None) != 2:
        issues.append("reference_duplicate_counting_mismatch")
    if round(sum(float(row["exact_r_reference"]) for row in reference_rows), 10) != 7.7268:
        issues.append("reference_sum_mismatch")
    if summary.get("exact_proxy_overlap_rows") != 5 or abs(float(summary.get("exact_proxy_delta_sum")) - 3.2306) > 1e-9:
        issues.append("exact_proxy_summary_mismatch")
    if summary.get("proxy_r_rows") != 718:
        issues.append("proxy_row_count_mismatch")
    if abs(float(summary.get("proxy_r_sum")) - 35.50010387) > 1e-9:
        issues.append("proxy_sum_mismatch")

    source_no_scalar_rows = [
        row
        for row in rows
        if row.get("source_no_scalar_rstyle_proxy_repair_status")
        == "SOURCE_NO_SCALAR_RSTYLE_PROXY_MATERIALIZED"
    ]
    if len(source_no_scalar_rows) != 7:
        issues.append("source_no_scalar_rstyle_proxy_count_mismatch")
    if round(sum(float(row.get("materialized_proxy_r") or 0.0) for row in source_no_scalar_rows), 10) != 1.80199:
        issues.append("source_no_scalar_rstyle_proxy_sum_mismatch")
    if summary.get("source_no_scalar_rstyle_proxy_repaired_rows") != 7:
        issues.append("source_no_scalar_summary_count_mismatch")
    if summary.get("source_no_scalar_rstyle_proxy_target_first_rows") != 4:
        issues.append("source_no_scalar_target_first_count_mismatch")
    if summary.get("source_no_scalar_rstyle_proxy_descriptor_conflict_rows") != 3:
        issues.append("source_no_scalar_descriptor_conflict_count_mismatch")
    for row in source_no_scalar_rows:
        ref = row.get("source_no_scalar_rstyle_proxy_reference")
        if not isinstance(ref, dict):
            issues.append("source_no_scalar_reference_missing")
            break
        if not ref.get("source_path") or not ref.get("source_sha256") or not ref.get("source_line"):
            issues.append("source_no_scalar_reference_source_missing")
            break
        if row.get("exact_r_materialization_status") != "EXACT_R_PROXY_RESULT_ROW_NO_BROKER_FILL_EVIDENCE":
            issues.append("source_no_scalar_status_mismatch")
            break
        if row.get("exact_r_duplicate_policy") != "PROXY_R_COUNTS_ONLY_EXACT_R_NOT_COUNTED":
            issues.append("source_no_scalar_duplicate_policy_mismatch")
            break
        if row.get("source_no_scalar_rstyle_proxy_reference_counted_as_proxy_r") is not True:
            issues.append("source_no_scalar_proxy_count_policy_missing")
            break
        target_stop = ref.get("target_stop_result")
        if target_stop == "TARGET_FIRST_PROXY_DOMINANT":
            if row.get("branch_decision") != "IMPLEMENT_DEFAULT_OFF_SOURCE_PROVENANCE_CONTEXT_FEATURE_WITH_RSTYLE_PROXY":
                issues.append("source_no_scalar_target_first_decision_mismatch")
                break
        elif row.get("branch_decision") != "REDESIGN_SOURCE_PROVENANCE_CONTEXT_FEATURE_DESCRIPTOR_CONFLICT_WITH_RSTYLE_PROXY":
            issues.append("source_no_scalar_descriptor_conflict_decision_mismatch")
            break

    xagusd_rows = [
        row
        for row in rows
        if row.get("candidate_id") == "XAGUSD_2026-05-14T13:15:00+00:00"
        and row.get("exact_r_materialization_status")
        == "EXACT_R_NOT_LOCAL_COMPUTABLE_ACCOUNT_HISTORY_CLOSE_DEAL_MISSING"
    ]
    if xagusd_rows:
        issues.append("xagusd_missing_close_rows_not_resolved")

    missing_rows = [row for row in rows if row.get("exact_r_source_search_exhausted")]
    if len(missing_rows) != 3402:
        issues.append("missing_rows_count_mismatch")
    for row in missing_rows:
        keys = row.get("exact_r_identifier_search_keys")
        if not isinstance(keys, dict) or not keys.get("candidate_aliases") or not keys.get("symbol_time_keys"):
            issues.append("missing_row_search_keys_absent")
            break
        if not row.get("exact_r_source_hash_manifest_sha256") or not row.get("exact_r_source_search_manifest_ref"):
            issues.append("missing_row_manifest_reference_absent")
            break
        if not row.get("exact_r_alias_search_row_id"):
            issues.append("missing_row_alias_reference_absent")
            break
        disposition = row.get("exact_r_unresolved_disposition")
        if not isinstance(disposition, dict) or not disposition.get("status") or not disposition.get("immediate_path"):
            issues.append("missing_row_disposition_absent")
            break
    banned_markers = (
        "_".join(("NO", "PROMOTION", "VERDICT")),
        "_".join(("validation", "safe")),
        "_".join(("outcome", "review", "opened")),
        "_".join(("live", "effect")),
        " ".join(("safe", "flags")),
        " ".join(("no", "promotion")),
        " ".join(("promotion", "claims")),
        "_".join(("validation", "result", "status")),
        "_".join(("outcome", "result", "rows", "status")),
    )
    for path in (OUTPUT_LEDGER, ALIAS_LEDGER, SUMMARY_PATH, MANIFEST_PATH):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for marker in banned_markers:
            if marker in text:
                issues.append(f"retired_marker_present:{path.name}:{marker}")
                break

    result = {
        "verified": not issues,
        "issues": issues,
        "rows": len(rows),
        "alias_rows": len(alias_rows),
        "source_paths_scanned": summary.get("source_paths_scanned"),
        "source_rows_scanned": summary.get("source_rows_scanned"),
        "exact_r_owner_rows": summary.get("exact_r_owner_rows"),
        "exact_r_owner_sum": summary.get("exact_r_owner_sum"),
        "exact_r_reference_rows": summary.get("exact_r_reference_rows"),
        "exact_r_reference_sum": summary.get("exact_r_reference_sum"),
        "proxy_r_rows": summary.get("proxy_r_rows"),
        "proxy_r_sum": summary.get("proxy_r_sum"),
        "missing_r_rows": summary.get("missing_r_rows"),
        "xagusd_position_238316913_missing_close_rows": summary.get(
            "xagusd_position_238316913_missing_close_rows"
        ),
    }
    VERIFY_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
