from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any


DATE = "2026-05-26"
ROUTE_ID = "vnext_moonshot_production_replacement_activation_2026_05_26"
STAGE_ID = "stage_13_outside_session_risk_reconciliation"

REPO_ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent

BROADER_ALLOWLIST = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_BROADER_ORIGIN_ACTIVATION_ALLOWLIST_{DATE}.json"
OUTSIDE_SUMMARY = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_OUTSIDE_SESSION_OPPORTUNITY_SUMMARY_{DATE}.json"
OUTSIDE_GROUP_LEDGER = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_OUTSIDE_SESSION_OPPORTUNITY_GROUP_LEDGER_{DATE}.jsonl"
OUTSIDE_SHARD_MANIFEST = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_OUTSIDE_SESSION_OPPORTUNITY_SHARD_MANIFEST_{DATE}.jsonl"
RISK_LEDGER = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_redacted_account_SELECTED_CELL_RISK_LEDGER_{DATE}.jsonl"
RISK_SUMMARY = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_redacted_account_BROKER_RISK_GEOMETRY_SUMMARY_{DATE}.json"

OUTPUT_LEDGER = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_OUTSIDE_SESSION_RISK_RECONCILIATION_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_OUTSIDE_SESSION_RISK_RECONCILIATION_SUMMARY_{DATE}.json"


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


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def canonical_hash(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


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


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")


def metrics_rows(entry: dict[str, Any]) -> int:
    metrics = entry.get("metrics") or {}
    return int(metrics.get("selected_count") or metrics.get("performance_rows") or 0)


def is_outside_entry(entry: dict[str, Any]) -> bool:
    route_session = str(entry.get("route_session") or "")
    proof_class = str(entry.get("proof_class") or "")
    session_contract = str(entry.get("session_expansion_contract") or "")
    return (
        route_session.startswith("moonshot_h")
        or "outside_session" in proof_class
        or session_contract == "named_moonshot_hour_bucket_allowlist"
    )


def risk_bucket(row: dict[str, Any] | None) -> tuple[str, str]:
    if row is None:
        return ("missing_selected_cell_risk_row", "missing_selected_cell_risk_row")
    risk_pct = float(row.get("effective_risk_per_trade_pct") or 0.0)
    if risk_pct > 0:
        return ("execute_with_selected_cell_risk", row.get("risk_decision_basis") or "risk_positive")
    reasons = row.get("exact_unresolved_or_excluded_reasons") or []
    if "commission_fields_not_exposed_in_current_symbol_info_snapshot" in reasons:
        return ("fail_closed_unresolved_commission_evidence", "commission_fields_not_exposed_in_current_symbol_info_snapshot")
    if "risk_zero_spread_cost_exceeds_20pct_of_median_sl" in reasons:
        return ("fail_closed_spread_slippage_cost_negative_ev", "risk_zero_spread_cost_exceeds_20pct_of_median_sl")
    if "risk_zero_selector_metrics_not_positive" in reasons or row.get("nonpositive_expectancy_or_pf_for_risk_gt_zero"):
        return ("fail_closed_selector_metrics_not_positive", "risk_zero_selector_metrics_not_positive")
    if "selector_metrics_nonpositive_or_missing_expectancy_profit_factor_or_rows" in reasons:
        return (
            "fail_closed_selector_metrics_missing_or_nonpositive",
            "selector_metrics_nonpositive_or_missing_expectancy_profit_factor_or_rows",
        )
    if "risk_zero_execution_critical_evidence_unresolved" in reasons:
        return ("fail_closed_execution_critical_evidence_unresolved", "risk_zero_execution_critical_evidence_unresolved")
    basis = row.get("risk_decision_basis") or "risk_zero_exact_reason_recorded"
    return ("fail_closed_risk_zero_exact_reason_recorded", str(basis))


def main() -> None:
    generated_at = utc_now()
    allowlist = read_json(BROADER_ALLOWLIST)
    outside_summary = read_json(OUTSIDE_SUMMARY)
    risk_summary = read_json(RISK_SUMMARY)
    outside_group_rows = iter_jsonl(OUTSIDE_GROUP_LEDGER)
    risk_rows = iter_jsonl(RISK_LEDGER)
    shard_manifest_rows = iter_jsonl(OUTSIDE_SHARD_MANIFEST)

    risk_by_hash = {row.get("source_selector_entry_sha256"): row for row in risk_rows}
    outside_entries = [entry for entry in allowlist.get("entries", []) if is_outside_entry(entry)]

    output_rows: list[dict[str, Any]] = []
    disposition_rows = Counter()
    disposition_entries = Counter()
    exact_reason_rows = Counter()
    exact_reason_entries = Counter()
    symbol_rows: dict[str, Counter[str]] = defaultdict(Counter)
    family_rows: dict[str, Counter[str]] = defaultdict(Counter)
    session_rows: dict[str, Counter[str]] = defaultdict(Counter)
    missing_risk_rows: list[str] = []
    risk_positive_rows = 0
    risk_positive_entries = 0
    risk_zero_rows = 0
    risk_zero_entries = 0

    for entry in outside_entries:
        entry_hash = canonical_hash(entry)
        risk_row = risk_by_hash.get(entry_hash)
        disposition, exact_reason = risk_bucket(risk_row)
        row_count = metrics_rows(entry)
        if risk_row is None:
            missing_risk_rows.append(entry_hash)

        if disposition == "execute_with_selected_cell_risk":
            risk_positive_rows += row_count
            risk_positive_entries += 1
        else:
            risk_zero_rows += row_count
            risk_zero_entries += 1

        disposition_rows[disposition] += row_count
        disposition_entries[disposition] += 1
        exact_reason_rows[exact_reason] += row_count
        exact_reason_entries[exact_reason] += 1
        symbol_rows[str(entry.get("symbol"))][disposition] += row_count
        family_rows[str(entry.get("origin_family"))][disposition] += row_count
        session_rows[str(entry.get("route_session"))][disposition] += row_count

        output_rows.append(
            {
                "activation_action": entry.get("activation_action"),
                "candidate_origin_family": entry.get("candidate_origin_family"),
                "entry_sha256": entry_hash,
                "exact_runtime_disposition_reason": exact_reason,
                "family": entry.get("origin_family"),
                "final_runtime_disposition": disposition,
                "metrics": entry.get("metrics") or {},
                "proof_class": entry.get("proof_class"),
                "risk_cell_id": None if risk_row is None else risk_row.get("risk_cell_id"),
                "risk_decision_basis": None if risk_row is None else risk_row.get("risk_decision_basis"),
                "risk_exact_unresolved_or_excluded_reasons": []
                if risk_row is None
                else risk_row.get("exact_unresolved_or_excluded_reasons") or [],
                "risk_pct": None if risk_row is None else risk_row.get("effective_risk_per_trade_pct"),
                "route_id": ROUTE_ID,
                "route_session": entry.get("route_session"),
                "schema_version": "vnext_replacement_stage13_outside_session_risk_reconciliation_v1",
                "selected_policy": entry.get("selected_policy"),
                "session_expansion_contract": entry.get("session_expansion_contract"),
                "session_proof_class_counts": entry.get("session_proof_class_counts") or {},
                "side": entry.get("side"),
                "source_allowlist_path": rel(BROADER_ALLOWLIST),
                "source_outside_group_ledger_path": rel(OUTSIDE_GROUP_LEDGER),
                "source_outside_shard_manifest_path": rel(OUTSIDE_SHARD_MANIFEST),
                "source_risk_ledger_path": rel(RISK_LEDGER),
                "stage_id": STAGE_ID,
                "symbol": entry.get("symbol"),
                "utc_hour_bucket": entry.get("utc_hour_bucket"),
            }
        )

    expanded_rows_expected = int(outside_summary.get("disposition_counts", {}).get("expand_production_execution_moonshot_extended_session") or 0)
    expanded_group_count_expected = int(
        read_json(ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_FULL_MOONSHOT_PRODUCTION_SELECTOR_SUMMARY_{DATE}.json").get(
            "broader_origin_outside_session_expanded_group_count"
        )
        or 0
    )
    outside_rows_seen = int(outside_summary.get("row_counts", {}).get("outside_session_rows") or 0)

    failures: list[str] = []
    if missing_risk_rows:
        failures.append(f"{len(missing_risk_rows)} outside-session allowlist entries missing selected-cell risk rows")
    if sum(disposition_rows.values()) != expanded_rows_expected:
        failures.append(
            f"outside-session risk reconciliation rows {sum(disposition_rows.values())} != expanded outside rows {expanded_rows_expected}"
        )
    if len(outside_entries) != expanded_group_count_expected:
        failures.append(
            f"outside-session risk reconciliation entries {len(outside_entries)} != expanded group count {expanded_group_count_expected}"
        )
    if not shard_manifest_rows:
        failures.append("outside-session row-preserving shard manifest is empty")
    if not outside_group_rows:
        failures.append("outside-session group ledger is empty")
    if risk_positive_rows + risk_zero_rows != expanded_rows_expected:
        failures.append("risk-positive plus risk-zero outside rows does not match expanded outside rows")

    write_jsonl(OUTPUT_LEDGER, output_rows)

    summary = {
        "broker_risk_summary": {
            "selected_cell_risk_positive_rows": risk_summary.get("row_counts", {}).get("selected_cell_risk_positive_rows"),
            "selected_cell_risk_rows": risk_summary.get("row_counts", {}).get("selected_cell_risk_rows"),
            "selected_cell_risk_zero_rows": risk_summary.get("row_counts", {}).get("selected_cell_risk_zero_rows"),
        },
        "deterministic_build": False,
        "entry_counts": {
            "outside_session_expanded_allowlist_entries": len(outside_entries),
            "risk_positive_entries": risk_positive_entries,
            "risk_zero_or_fail_closed_entries": risk_zero_entries,
        },
        "failures": failures,
        "generated_at_utc": generated_at,
        "input_hashes": {
            rel(BROADER_ALLOWLIST): file_sha256(BROADER_ALLOWLIST),
            rel(OUTSIDE_GROUP_LEDGER): file_sha256(OUTSIDE_GROUP_LEDGER),
            rel(OUTSIDE_SHARD_MANIFEST): file_sha256(OUTSIDE_SHARD_MANIFEST),
            rel(OUTSIDE_SUMMARY): file_sha256(OUTSIDE_SUMMARY),
            rel(RISK_LEDGER): file_sha256(RISK_LEDGER),
            rel(RISK_SUMMARY): file_sha256(RISK_SUMMARY),
        },
        "outside_session_source": {
            "expanded_group_count_expected": expanded_group_count_expected,
            "expanded_rows_expected": expanded_rows_expected,
            "outside_rows_seen": outside_rows_seen,
            "row_preserving_shard_manifest_rows": len(shard_manifest_rows),
            "row_preserving_shards_total_rows": sum(int(row.get("rows") or 0) for row in shard_manifest_rows),
            "row_preserving_shards_total_size_bytes": sum(int(row.get("size_bytes") or 0) for row in shard_manifest_rows),
        },
        "output_hashes": {
            rel(OUTPUT_LEDGER): file_sha256(OUTPUT_LEDGER),
        },
        "output_paths": {
            "ledger": rel(OUTPUT_LEDGER),
            "summary": rel(OUTPUT_SUMMARY),
        },
        "risk_disposition_entry_counts": dict(sorted(disposition_entries.items())),
        "risk_disposition_row_counts": dict(sorted(disposition_rows.items())),
        "risk_exact_reason_entry_counts": dict(sorted(exact_reason_entries.items())),
        "risk_exact_reason_row_counts": dict(sorted(exact_reason_rows.items())),
        "risk_positive_execution_rows": risk_positive_rows,
        "risk_zero_fail_closed_rows": risk_zero_rows,
        "route_id": ROUTE_ID,
        "schema_version": "vnext_replacement_stage13_outside_session_risk_reconciliation_summary_v1",
        "stage_id": STAGE_ID,
        "status": "passed" if not failures else "failed",
        "summary_by_family_rows": {key: dict(sorted(value.items())) for key, value in sorted(family_rows.items())},
        "summary_by_route_session_rows": {key: dict(sorted(value.items())) for key, value in sorted(session_rows.items())},
        "summary_by_symbol_rows": {key: dict(sorted(value.items())) for key, value in sorted(symbol_rows.items())},
    }
    write_json(OUTPUT_SUMMARY, summary)
    print(json.dumps(summary, sort_keys=True, ensure_ascii=True))


if __name__ == "__main__":
    main()
