from __future__ import annotations

import json
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any


DATE = "2026-05-26"
ROUTE_ID = "vnext_moonshot_production_replacement_activation_2026_05_26"
STAGE_ID = "stage_13_outside_session_risk_reconciliation_verifier"

REPO_ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent

SUMMARY_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_OUTSIDE_SESSION_RISK_RECONCILIATION_SUMMARY_{DATE}.json"
LEDGER_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_OUTSIDE_SESSION_RISK_RECONCILIATION_LEDGER_{DATE}.jsonl"
OUTSIDE_SUMMARY = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_OUTSIDE_SESSION_OPPORTUNITY_SUMMARY_{DATE}.json"
SHARD_MANIFEST = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_OUTSIDE_SESSION_OPPORTUNITY_SHARD_MANIFEST_{DATE}.jsonl"
RISK_SUMMARY = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_redacted_account_BROKER_RISK_GEOMETRY_SUMMARY_{DATE}.json"
RISK_VERIFIER = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_redacted_account_BROKER_RISK_GEOMETRY_VERIFIER_{DATE}.json"
OUTPUT_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_OUTSIDE_SESSION_RISK_RECONCILIATION_VERIFIER_{DATE}.json"

REQUIRED_LEDGER_FIELDS = {
    "entry_sha256",
    "symbol",
    "family",
    "side",
    "route_session",
    "utc_hour_bucket",
    "proof_class",
    "metrics",
    "final_runtime_disposition",
    "exact_runtime_disposition_reason",
    "risk_cell_id",
    "risk_pct",
    "risk_decision_basis",
    "risk_exact_unresolved_or_excluded_reasons",
}

VALID_FAIL_CLOSED_REASONS = {
    "commission_fields_not_exposed_in_current_symbol_info_snapshot",
    "risk_zero_spread_cost_exceeds_20pct_of_median_sl",
    "risk_zero_selector_metrics_not_positive",
    "selector_metrics_nonpositive_or_missing_expectancy_profit_factor_or_rows",
    "risk_zero_execution_critical_evidence_unresolved",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            row["_line_no"] = line_no
            rows.append(row)
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def metrics_rows(row: dict[str, Any]) -> int:
    metrics = row.get("metrics") or {}
    return int(metrics.get("selected_count") or metrics.get("performance_rows") or 0)


def main() -> None:
    generated_at = utc_now()
    failures: list[str] = []
    warnings: list[str] = []

    required_paths = [SUMMARY_PATH, LEDGER_PATH, OUTSIDE_SUMMARY, SHARD_MANIFEST, RISK_SUMMARY, RISK_VERIFIER]
    missing_paths = [rel(path) for path in required_paths if not path.exists()]
    if missing_paths:
        failures.extend(f"missing required artifact {path}" for path in missing_paths)
        result = {
            "failures": failures,
            "generated_at_utc": generated_at,
            "route_id": ROUTE_ID,
            "schema_version": "vnext_replacement_stage13_outside_session_risk_reconciliation_verifier_v1",
            "stage_id": STAGE_ID,
            "status": "failed",
            "warnings": warnings,
        }
        write_json(OUTPUT_PATH, result)
        print(json.dumps(result, sort_keys=True, ensure_ascii=True))
        return

    summary = read_json(SUMMARY_PATH)
    outside_summary = read_json(OUTSIDE_SUMMARY)
    risk_summary = read_json(RISK_SUMMARY)
    risk_verifier = read_json(RISK_VERIFIER)
    ledger_rows = iter_jsonl(LEDGER_PATH)
    shard_rows = iter_jsonl(SHARD_MANIFEST)

    if summary.get("status") != "passed":
        failures.append(f"outside-session risk reconciliation summary status is {summary.get('status')!r}")
    if risk_verifier.get("status") != "passed":
        failures.append(f"redacted_account broker/risk verifier status is {risk_verifier.get('status')!r}")

    expanded_rows = int(outside_summary.get("disposition_counts", {}).get("expand_production_execution_moonshot_extended_session") or 0)
    ledger_selected_rows = sum(metrics_rows(row) for row in ledger_rows)
    if ledger_selected_rows != expanded_rows:
        failures.append(f"ledger selected rows {ledger_selected_rows} != outside expanded rows {expanded_rows}")
    if summary.get("risk_positive_execution_rows", 0) + summary.get("risk_zero_fail_closed_rows", 0) != expanded_rows:
        failures.append("risk-positive plus risk-zero rows does not equal outside expanded rows")
    if summary.get("entry_counts", {}).get("outside_session_expanded_allowlist_entries") != len(ledger_rows):
        failures.append("summary outside entry count does not equal reconciliation ledger row count")

    risk_summary_positive = int(risk_summary.get("row_counts", {}).get("selected_cell_risk_positive_rows") or 0)
    if risk_summary_positive <= 0:
        failures.append("selected-cell risk summary has no positive risk rows")
    if int(summary.get("risk_positive_execution_rows") or 0) <= 0:
        warnings.append("outside-session expanded rows are currently all fail-closed by selected-cell risk")

    shard_manifest_rows = int(summary.get("outside_session_source", {}).get("row_preserving_shard_manifest_rows") or 0)
    shard_manifest_total = int(summary.get("outside_session_source", {}).get("row_preserving_shards_total_rows") or 0)
    outside_rows_seen = int(outside_summary.get("row_counts", {}).get("outside_session_rows") or 0)
    if shard_manifest_rows != len(shard_rows):
        failures.append("summary shard manifest row count does not match shard manifest file")
    if shard_manifest_total != outside_rows_seen:
        failures.append(f"row-preserving shards total {shard_manifest_total} != outside rows seen {outside_rows_seen}")
    for shard in shard_rows:
        if not shard.get("sha256") or not shard.get("size_bytes"):
            failures.append(f"outside shard manifest row {shard.get('_line_no')} lacks sha256/size_bytes")

    bad_rows = 0
    missing_risk_rows = 0
    invalid_fail_closed_rows = 0
    positive_with_unresolved_rows = 0
    for row in ledger_rows:
        missing = REQUIRED_LEDGER_FIELDS - set(row)
        if missing:
            bad_rows += 1
            if bad_rows <= 5:
                failures.append(f"ledger row {row.get('_line_no')} missing fields {sorted(missing)}")
            continue
        disposition = row.get("final_runtime_disposition")
        risk_pct = float(row.get("risk_pct") or 0.0)
        reasons = set(row.get("risk_exact_unresolved_or_excluded_reasons") or [])
        if not row.get("risk_cell_id"):
            missing_risk_rows += 1
        if disposition == "execute_with_selected_cell_risk":
            if risk_pct <= 0:
                failures.append(f"ledger row {row.get('_line_no')} marked executable with nonpositive risk_pct")
            if reasons & VALID_FAIL_CLOSED_REASONS:
                positive_with_unresolved_rows += 1
        else:
            if risk_pct > 0:
                failures.append(f"ledger row {row.get('_line_no')} fail-closed with positive risk_pct")
            if row.get("exact_runtime_disposition_reason") not in VALID_FAIL_CLOSED_REASONS:
                invalid_fail_closed_rows += 1
    if missing_risk_rows:
        failures.append(f"{missing_risk_rows} outside-session entries lack matching selected-cell risk rows")
    if invalid_fail_closed_rows:
        failures.append(f"{invalid_fail_closed_rows} fail-closed outside-session rows lack exact broker/cost/spec reason")
    if positive_with_unresolved_rows:
        failures.append(f"{positive_with_unresolved_rows} executable outside-session rows still carry execution-critical unresolved reasons")

    output_hashes = {rel(path): file_sha256(path) for path in [SUMMARY_PATH, LEDGER_PATH, OUTSIDE_SUMMARY, SHARD_MANIFEST, RISK_SUMMARY, RISK_VERIFIER]}
    result = {
        "failures": failures,
        "generated_at_utc": generated_at,
        "output_hashes": output_hashes,
        "route_id": ROUTE_ID,
        "row_counts": {
            "outside_expanded_rows": expanded_rows,
            "reconciliation_ledger_entries": len(ledger_rows),
            "reconciliation_selected_rows": ledger_selected_rows,
            "risk_positive_execution_rows": summary.get("risk_positive_execution_rows"),
            "risk_zero_fail_closed_rows": summary.get("risk_zero_fail_closed_rows"),
            "row_preserving_shards_total_rows": shard_manifest_total,
        },
        "schema_version": "vnext_replacement_stage13_outside_session_risk_reconciliation_verifier_v1",
        "stage_id": STAGE_ID,
        "status": "passed" if not failures else "failed",
        "warnings": warnings,
    }
    write_json(OUTPUT_PATH, result)
    print(json.dumps(result, sort_keys=True, ensure_ascii=True))


if __name__ == "__main__":
    main()
