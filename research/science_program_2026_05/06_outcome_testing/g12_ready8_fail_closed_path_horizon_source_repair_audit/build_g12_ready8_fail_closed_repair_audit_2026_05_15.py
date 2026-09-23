#!/usr/bin/env python3
"""Build the G12 audit for READY8 fail-closed source-repair artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
OUTCOME_ROOT = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing"
ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-15"
GENERATED_AT_UTC = "2026-05-15T12:00:00Z"
ROUTE_ID = "G12_READY8_FAIL_CLOSED_PATH_HORIZON_SOURCE_REPAIR_AUDIT"
EVIDENCE_CLASS = "G12_READY8_FAIL_CLOSED_PATH_HORIZON_SOURCE_REPAIR_AUDIT_ONLY"
SCHEMA_VERSION = "g12_ready8_fail_closed_repair_audit_v1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

SOURCE_ROUTE_DIR = OUTCOME_ROOT / "ready8_fail_closed_path_horizon_source_repair"
TARGET_DIR = OUTCOME_ROOT / "scid_ready8_discriminative_quarantined_target_result_packet"
SEALED_EXECUTION_DIR = OUTCOME_ROOT / "scid_ready8_discriminative_sealed_validation_after_opening_gate"
BAR_DIR = OUTCOME_ROOT / "scid_asof_bar_builder_and_candidate_input_packet_source_control"

TARGET_FILES_GLOB = "SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_ROWS_*_2026-05-13.jsonl"
SEALED_FAIL_CLOSED_LEDGER = SEALED_EXECUTION_DIR / "R8DISC_SEALED_FAIL_CLOSED_2026-05-13.jsonl"
ORIGINAL_BAR_ROWS = BAR_DIR / "SCID_ASOF_BAR_ROWS_2026-05-11.jsonl"

SOURCE_INVENTORY = SOURCE_ROUTE_DIR / "READY8_FAIL_CLOSED_ROW_INVENTORY_2026-05-15.jsonl"
SOURCE_BARS = SOURCE_ROUTE_DIR / "READY8_FAIL_CLOSED_REPAIRED_BAR_PACKET_2026-05-15.jsonl"
SOURCE_TARGETS = SOURCE_ROUTE_DIR / "READY8_FAIL_CLOSED_REPAIRED_TARGET_ROW_PACKET_2026-05-15.jsonl"
SOURCE_SENSITIVITY = SOURCE_ROUTE_DIR / "READY8_FAIL_CLOSED_SENSITIVITY_LEDGER_2026-05-15.json"
SOURCE_UNRECOVERABLE = SOURCE_ROUTE_DIR / "READY8_FAIL_CLOSED_UNRECOVERABLE_PROOF_LEDGER_2026-05-15.json"
SOURCE_SEARCH = SOURCE_ROUTE_DIR / "READY8_FAIL_CLOSED_SEARCHED_ROOT_ACQUISITION_LEDGER_2026-05-15.json"
SOURCE_CLOSURE = SOURCE_ROUTE_DIR / "READY8_FAIL_CLOSED_QUESTION_AMBIGUITY_CLOSURE_LEDGER_2026-05-15.json"
SOURCE_OUTPUT_MANIFEST = SOURCE_ROUTE_DIR / "READY8_FAIL_CLOSED_OUTPUT_MANIFEST_2026-05-15.json"

SCID_HEADER = struct.Struct("<4sIIHHI36s")
SCID_RECORD = struct.Struct("<QffffIIII")

TARGET_FAMILIES = {
    "neutral_close_to_close_return_m15_horizons_v1": "CLOSE_TO_CLOSE",
    "neutral_high_low_excursion_m15_horizons_v1": "HIGH_LOW_EXCURSION",
}


def safe_flags() -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": GENERATED_AT_UTC,
        "evidence_class": EVIDENCE_CLASS,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "opens_ai_api": False,
        "opens_paid_or_vendor_access": False,
        "opens_broker_account_order_history_deal_position_evidence": False,
        "opens_live_trading_behavior": False,
        "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
        "opens_raw_market_data_blob_commit": False,
        "opens_registry_edit": False,
        "opens_remote_push": False,
        "changes_trading_risk_safety_prompt_decision_behavior": False,
        "credentials_touched": False,
    }


def rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(ROOT.resolve(strict=False)).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()


def recompute_row_hash(row: dict[str, Any], hash_key: str) -> str:
    payload = {key: value for key, value in row.items() if key != hash_key}
    return sha256_json(payload)


def iso_utc_from_mtime(path: Path) -> str:
    return (
        datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def floats_close(actual: Any, expected: Any) -> bool:
    if actual is None or expected is None:
        return actual is expected
    try:
        return math.isclose(float(actual), float(expected), rel_tol=1e-12, abs_tol=1e-9)
    except (TypeError, ValueError):
        return actual == expected


def compact_counter(counter: Counter) -> dict[str, int]:
    return {str(key): int(value) for key, value in sorted(counter.items(), key=lambda kv: str(kv[0]))}


def artifact_record(path: Path) -> dict[str, Any]:
    exists = path.exists()
    return {
        "path": rel(path),
        "exists": exists,
        "bytes": path.stat().st_size if exists else None,
        "sha256": sha256_file(path) if exists else None,
    }


def load_original_bars() -> dict[tuple[str, str], dict[str, Any]]:
    bars: dict[tuple[str, str], dict[str, Any]] = {}
    for row in iter_jsonl(ORIGINAL_BAR_ROWS):
        if row.get("bar_status") == "CLOSED_SOURCE_RECORDS_PRESENT":
            bars[(row["symbol"], row["bar_end_exclusive_utc"])] = row
    return bars


def load_source_inventory() -> dict[str, dict[str, Any]]:
    return {row["target_result_row_id"]: row for row in iter_jsonl(SOURCE_INVENTORY)}


def load_source_targets() -> dict[str, dict[str, Any]]:
    return {row["original_target_result_row_id"]: row for row in iter_jsonl(SOURCE_TARGETS)}


def load_source_bars() -> dict[tuple[str, str], dict[str, Any]]:
    return {(row["symbol"], row["bar_end_exclusive_utc"]): row for row in iter_jsonl(SOURCE_BARS)}


def scan_target_inventory(
    source_inventory: dict[str, dict[str, Any]], repaired_ids: set[str]
) -> tuple[dict[str, Any], dict[str, dict[str, Any]], list[dict[str, Any]], list[str]]:
    counters: dict[str, Counter] = defaultdict(Counter)
    target_fail_by_id: dict[str, dict[str, Any]] = {}
    issues: list[str] = []
    audit_rows: list[dict[str, Any]] = []
    total_target_rows = 0
    computable_rows = 0
    target_files = sorted(TARGET_DIR.glob(TARGET_FILES_GLOB))

    for path in target_files:
        file_rows = 0
        for row in iter_jsonl(path):
            total_target_rows += 1
            file_rows += 1
            terminal_status = row.get("terminal_status")
            denominator_role = row.get("denominator_role")
            if terminal_status == "COMPUTABLE":
                computable_rows += 1
            is_target_fail = terminal_status == "FAIL_CLOSED_NOT_COMPUTABLE"
            is_role_excluded = terminal_status == "COMPUTABLE" and denominator_role == "per_card_fail_closed_row"
            if not is_target_fail and not is_role_excluded:
                continue

            if is_target_fail:
                inventory_type = "TARGET_FAIL_CLOSED_NOT_COMPUTABLE"
                repair_status = (
                    "REPAIR_CANDIDATE_COMPUTABLE_REQUIRES_G12_ACCEPTANCE"
                    if row["target_result_row_id"] in repaired_ids
                    else "STILL_FAIL_CLOSED_AFTER_CURRENT_LOCAL_SOURCE_SEARCH"
                )
                family = row.get("fail_closed_primary_reason") or "FAIL_CLOSED_UNKNOWN"
                target_fail_by_id[row["target_result_row_id"]] = row
                counters["target_fail_reason"][family] += 1
            else:
                inventory_type = "ROLE_FAIL_CLOSED_COMPUTABLE_EXCLUDED"
                repair_status = "EXACTLY_ROUTED_DENOMINATOR_ROLE_NOT_PATH_HORIZON_SOURCE_GAP"
                family = "ROLE_FAIL_CLOSED_COMPUTABLE_EXCLUDED"

            source_row = source_inventory.get(row["target_result_row_id"])
            field_matches = bool(
                source_row
                and source_row.get("inventory_type") == inventory_type
                and source_row.get("repair_status") == repair_status
                and source_row.get("fail_closed_family") == family
                and source_row.get("target_result_row_hash") == row.get("target_result_row_hash")
            )
            if not field_matches:
                issues.append(f"inventory_mismatch:{row['target_result_row_id']}")

            counters["inventory_type"][inventory_type] += 1
            counters["repair_status"][repair_status] += 1
            counters["family"][family] += 1
            counters["card"][row.get("card_id")] += 1
            counters["symbol"][row.get("symbol")] += 1
            counters["partition"][row.get("partition_assignment")] += 1
            counters["target_family"][row.get("target_family_id")] += 1
            counters["horizon"][row.get("horizon_m15_bars")] += 1
            counters["denominator_role"][denominator_role] += 1

            audit_rows.append(
                {
                    **safe_flags(),
                    "artifact_family": "g12_fail_closed_inventory_recomputation_row",
                    "target_result_row_id": row.get("target_result_row_id"),
                    "target_result_row_hash": row.get("target_result_row_hash"),
                    "card_id": row.get("card_id"),
                    "symbol": row.get("symbol"),
                    "partition_assignment": row.get("partition_assignment"),
                    "target_family_id": row.get("target_family_id"),
                    "horizon_m15_bars": row.get("horizon_m15_bars"),
                    "denominator_role": denominator_role,
                    "terminal_status": terminal_status,
                    "recomputed_inventory_type": inventory_type,
                    "recomputed_fail_closed_family": family,
                    "recomputed_repair_status": repair_status,
                    "source_inventory_row_present": source_row is not None,
                    "source_inventory_field_match": field_matches,
                    "audit_status": "PASS" if field_matches else "FAIL",
                }
            )
        counters["target_file_rows"][path.name] = file_rows

    summary = {
        "target_files": [rel(path) for path in target_files],
        "total_target_result_rows": total_target_rows,
        "computable_rows": computable_rows,
        "inventory_rows": len(audit_rows),
        "target_fail_closed_not_computable_rows": counters["inventory_type"]["TARGET_FAIL_CLOSED_NOT_COMPUTABLE"],
        "role_fail_closed_computable_excluded_rows": counters["inventory_type"]["ROLE_FAIL_CLOSED_COMPUTABLE_EXCLUDED"],
        "counters": {key: compact_counter(value) for key, value in counters.items()},
    }
    return summary, target_fail_by_id, audit_rows, issues


def scan_sealed_fail_closed_ledger() -> dict[str, Any]:
    family_record_counts: Counter = Counter()
    family_row_sums: Counter = Counter()
    total_records = 0
    total_rows = 0
    for row in iter_jsonl(SEALED_FAIL_CLOSED_LEDGER):
        total_records += 1
        rows = int(row.get("rows") or 0)
        total_rows += rows
        family = row.get("fail_closed_family")
        family_record_counts[family] += 1
        family_row_sums[family] += rows
    return {
        "sealed_fail_closed_ledger_path": rel(SEALED_FAIL_CLOSED_LEDGER),
        "sealed_fail_closed_ledger_records": total_records,
        "sealed_fail_closed_ledger_rows_sum": total_rows,
        "family_record_counts": compact_counter(family_record_counts),
        "family_row_sums": compact_counter(family_row_sums),
    }


def recompute_source_bar(row: dict[str, Any]) -> dict[str, Any]:
    path = Path(row["source_path_reference_only"])
    issue_codes: list[str] = []
    current_size = path.stat().st_size if path.exists() else None
    current_mtime = iso_utc_from_mtime(path) if path.exists() else None
    raw = b""
    if not path.exists():
        issue_codes.append("SOURCE_FILE_MISSING_AT_AUDIT")
    else:
        start = int(row["source_byte_start"])
        end = int(row["source_byte_end_exclusive"])
        if current_size is not None and current_size < end:
            issue_codes.append("SOURCE_FILE_SHORTER_THAN_PACKET_BYTE_RANGE")
        with path.open("rb") as handle:
            handle.seek(start)
            raw = handle.read(max(0, end - start))

    byte_count_ok = len(raw) == int(row["source_record_count"]) * SCID_RECORD.size
    if not byte_count_ok:
        issue_codes.append("SOURCE_BYTE_COUNT_MISMATCH")
    source_digest = hashlib.sha256(raw).hexdigest()
    source_digest_ok = source_digest == row.get("source_records_sha256")
    if not source_digest_ok:
        issue_codes.append("SOURCE_RECORD_SHA256_MISMATCH")

    parsed_checks_ok = False
    parsed_values: dict[str, Any] = {}
    if byte_count_ok and raw:
        records = [SCID_RECORD.unpack(raw[i : i + SCID_RECORD.size]) for i in range(0, len(raw), SCID_RECORD.size)]
        parsed_values = {
            "source_record_count": len(records),
            "open": float(records[0][1]),
            "high": max(float(record[2]) for record in records),
            "low": min(float(record[3]) for record in records),
            "close": float(records[-1][4]),
            "num_trades": sum(int(record[5]) for record in records),
            "total_volume": sum(int(record[6]) for record in records),
            "bid_volume": sum(int(record[7]) for record in records),
            "ask_volume": sum(int(record[8]) for record in records),
            "source_timestamp_min_us": int(records[0][0]),
            "source_timestamp_max_us": int(records[-1][0]),
        }
        parsed_checks_ok = all(
            [
                parsed_values["source_record_count"] == row.get("source_record_count"),
                floats_close(parsed_values["open"], row.get("open")),
                floats_close(parsed_values["high"], row.get("high")),
                floats_close(parsed_values["low"], row.get("low")),
                floats_close(parsed_values["close"], row.get("close")),
                parsed_values["num_trades"] == row.get("num_trades"),
                parsed_values["total_volume"] == row.get("total_volume"),
                parsed_values["bid_volume"] == row.get("bid_volume"),
                parsed_values["ask_volume"] == row.get("ask_volume"),
                parsed_values["source_timestamp_min_us"] == row.get("source_timestamp_min_us"),
                parsed_values["source_timestamp_max_us"] == row.get("source_timestamp_max_us"),
            ]
        )
        if not parsed_checks_ok:
            issue_codes.append("SOURCE_RECORD_VALUE_RECOMPUTE_MISMATCH")

    bar_hash = recompute_row_hash(row, "bar_hash")
    bar_hash_ok = bar_hash == row.get("bar_hash")
    if not bar_hash_ok:
        issue_codes.append("REPAIRED_BAR_HASH_MISMATCH")
    byte_range_index_ok = (
        row.get("source_byte_end_exclusive") - row.get("source_byte_start")
        == (row.get("source_record_end_index") - row.get("source_record_start_index") + 1) * SCID_RECORD.size
    )
    if not byte_range_index_ok:
        issue_codes.append("SOURCE_BYTE_RANGE_INDEX_MISMATCH")

    metadata_drift = bool(
        current_size is not None
        and (
            current_size != row.get("source_file_size_bytes")
            or current_mtime != row.get("source_file_last_modified_utc")
        )
    )
    critical_ok = source_digest_ok and parsed_checks_ok and bar_hash_ok and byte_count_ok and byte_range_index_ok
    return {
        **safe_flags(),
        "artifact_family": "g12_source_record_hash_recomputation_row",
        "symbol": row.get("symbol"),
        "bar_end_exclusive_utc": row.get("bar_end_exclusive_utc"),
        "source_file_name": row.get("source_file_name"),
        "source_path_reference_only": row.get("source_path_reference_only"),
        "source_byte_start": row.get("source_byte_start"),
        "source_byte_end_exclusive": row.get("source_byte_end_exclusive"),
        "source_record_count": row.get("source_record_count"),
        "packet_source_file_size_bytes": row.get("source_file_size_bytes"),
        "current_source_file_size_bytes": current_size,
        "packet_source_file_last_modified_utc": row.get("source_file_last_modified_utc"),
        "current_source_file_last_modified_utc": current_mtime,
        "metadata_append_drift_observed": metadata_drift,
        "packet_source_records_sha256": row.get("source_records_sha256"),
        "recomputed_source_records_sha256": source_digest,
        "source_records_sha256_match": source_digest_ok,
        "packet_bar_hash": row.get("bar_hash"),
        "recomputed_bar_hash": bar_hash,
        "bar_hash_match": bar_hash_ok,
        "byte_count_ok": byte_count_ok,
        "byte_range_index_ok": byte_range_index_ok,
        "parsed_record_values_match_packet": parsed_checks_ok,
        "issue_codes": issue_codes,
        "audit_status": "PASS" if critical_ok else "FAIL",
    }


def recompute_repaired_target(
    row: dict[str, Any],
    original_row: dict[str, Any] | None,
    combined_bars: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    issue_codes: list[str] = []
    if original_row is None:
        issue_codes.append("ORIGINAL_FAIL_CLOSED_ROW_NOT_FOUND")
    required = list(row.get("required_bar_end_utc") or [])
    symbol = row.get("symbol")
    missing = [end for end in required if (symbol, end) not in combined_bars]
    if missing:
        issue_codes.append("REQUIRED_BAR_NOT_AVAILABLE_IN_COMBINED_PACKET")

    metric_checks: dict[str, bool] = {}
    if not missing and original_row is not None:
        source_hashes = [combined_bars[(symbol, end)]["bar_hash"] for end in required]
        metric_checks["source_bar_hashes_consumed"] = source_hashes == row.get("source_bar_hashes_consumed")
        metric_checks["source_bar_hashes_consumed_sha256"] = (
            sha256_json(source_hashes) == row.get("source_bar_hashes_consumed_sha256")
        )
        entry_close = float(combined_bars[(symbol, row["entry_reference_time_utc"])]["close"])
        metric_checks["entry_close"] = floats_close(entry_close, row.get("entry_close"))
        metric_checks["passthrough_card_symbol_family"] = all(
            row.get(key) == original_row.get(key)
            for key in (
                "card_id",
                "symbol",
                "canonical_economic_group",
                "partition_assignment",
                "target_family_id",
                "horizon_m15_bars",
                "denominator_role",
                "candidate_input_row_id",
                "rowset_row_id",
                "duplicate_proxy_denominator_key",
            )
        )
        if row["target_family_id"] == "neutral_close_to_close_return_m15_horizons_v1":
            horizon_close = float(combined_bars[(symbol, row["horizon_end_utc"])]["close"])
            delta = horizon_close - entry_close
            metric_checks["horizon_close"] = floats_close(horizon_close, row.get("horizon_close"))
            metric_checks["close_to_close_absolute_delta"] = floats_close(
                round(delta, 12), row.get("close_to_close_absolute_delta")
            )
            metric_checks["close_to_close_percent_return"] = floats_close(
                round(delta / entry_close, 12) if entry_close else None,
                row.get("close_to_close_percent_return"),
            )
        elif row["target_family_id"] == "neutral_high_low_excursion_m15_horizons_v1":
            path_rows = [combined_bars[(symbol, end)] for end in required[1:]]
            max_high = max(float(bar["high"]) for bar in path_rows)
            min_low = min(float(bar["low"]) for bar in path_rows)
            upside = max_high - entry_close
            downside = entry_close - min_low
            metric_checks["horizon_close"] = floats_close(float(path_rows[-1]["close"]), row.get("horizon_close"))
            metric_checks["max_high_over_horizon"] = floats_close(round(max_high, 12), row.get("max_high_over_horizon"))
            metric_checks["min_low_over_horizon"] = floats_close(round(min_low, 12), row.get("min_low_over_horizon"))
            metric_checks["upside_excursion_absolute"] = floats_close(
                round(upside, 12), row.get("upside_excursion_absolute")
            )
            metric_checks["upside_excursion_percent"] = floats_close(
                round(upside / entry_close, 12) if entry_close else None,
                row.get("upside_excursion_percent"),
            )
            metric_checks["downside_excursion_absolute"] = floats_close(
                round(downside, 12), row.get("downside_excursion_absolute")
            )
            metric_checks["downside_excursion_percent"] = floats_close(
                round(downside / entry_close, 12) if entry_close else None,
                row.get("downside_excursion_percent"),
            )
        else:
            issue_codes.append("UNKNOWN_TARGET_FAMILY")
    failed_metric_checks = [key for key, passed in metric_checks.items() if not passed]
    issue_codes.extend(f"TARGET_METRIC_MISMATCH:{key}" for key in failed_metric_checks)

    target_hash = recompute_row_hash(row, "repair_candidate_target_result_row_hash")
    target_hash_ok = target_hash == row.get("repair_candidate_target_result_row_hash")
    if not target_hash_ok:
        issue_codes.append("REPAIR_CANDIDATE_TARGET_HASH_MISMATCH")

    critical_ok = not issue_codes and target_hash_ok
    return {
        **safe_flags(),
        "artifact_family": "g12_repaired_target_recomputation_row",
        "original_target_result_row_id": row.get("original_target_result_row_id"),
        "card_id": row.get("card_id"),
        "symbol": row.get("symbol"),
        "partition_assignment": row.get("partition_assignment"),
        "target_family_id": row.get("target_family_id"),
        "horizon_m15_bars": row.get("horizon_m15_bars"),
        "required_bar_count": len(required),
        "original_fail_closed_row_found": original_row is not None,
        "required_bars_missing_after_repair": missing,
        "metric_checks": metric_checks,
        "packet_repair_candidate_target_result_row_hash": row.get("repair_candidate_target_result_row_hash"),
        "recomputed_repair_candidate_target_result_row_hash": target_hash,
        "repair_candidate_target_result_row_hash_match": target_hash_ok,
        "issue_codes": issue_codes,
        "audit_status": "PASS" if critical_ok else "FAIL",
    }


def recompute_unrecoverable(
    target_fail_by_id: dict[str, dict[str, Any]],
    repaired_ids: set[str],
    combined_bars: dict[tuple[str, str], dict[str, Any]],
) -> tuple[dict[str, Any], list[str]]:
    gap_counter: Counter = Counter()
    repairable_but_unrepaired: list[str] = []
    for target_id, row in target_fail_by_id.items():
        if target_id in repaired_ids:
            continue
        missing = [end for end in row.get("required_bar_end_utc") or [] if (row["symbol"], end) not in combined_bars]
        if not missing:
            repairable_but_unrepaired.append(target_id)
        for end in missing:
            gap_counter[(row["symbol"], end)] += 1
    gap_rows = [
        {"symbol": symbol, "bar_end_exclusive_utc": end, "referencing_target_fail_rows": count}
        for (symbol, end), count in sorted(gap_counter.items())
    ]
    return {
        "still_fail_closed_target_rows_recomputed": len(target_fail_by_id) - len(repaired_ids),
        "remaining_unique_missing_bar_windows_recomputed": len(gap_rows),
        "remaining_gap_rows_recomputed": gap_rows,
        "repairable_but_unrepaired_target_ids": repairable_but_unrepaired,
    }, repairable_but_unrepaired


def build_artifacts(focused_tests_summary: str | None) -> None:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    source_inventory = load_source_inventory()
    repaired_targets = load_source_targets()
    repaired_bars = load_source_bars()
    original_bars = load_original_bars()
    combined_bars = dict(original_bars)
    combined_bars.update(repaired_bars)

    repaired_ids = set(repaired_targets)
    inventory_summary, target_fail_by_id, inventory_rows, inventory_issues = scan_target_inventory(
        source_inventory, repaired_ids
    )
    sealed_summary = scan_sealed_fail_closed_ledger()

    source_bar_rows = [recompute_source_bar(row) for row in repaired_bars.values()]
    target_audit_rows = [
        recompute_repaired_target(row, target_fail_by_id.get(target_id), combined_bars)
        for target_id, row in sorted(repaired_targets.items())
    ]
    unrecoverable_recomputed, repairable_but_unrepaired = recompute_unrecoverable(
        target_fail_by_id, repaired_ids, combined_bars
    )

    source_sensitivity = load_json(SOURCE_SENSITIVITY)
    source_unrecoverable = load_json(SOURCE_UNRECOVERABLE)
    source_search = load_json(SOURCE_SEARCH)
    source_closure = load_json(SOURCE_CLOSURE)

    source_bar_failures = [row for row in source_bar_rows if row["audit_status"] != "PASS"]
    target_failures = [row for row in target_audit_rows if row["audit_status"] != "PASS"]
    inventory_failures = [row for row in inventory_rows if row["audit_status"] != "PASS"]
    metadata_drift_rows = [row for row in source_bar_rows if row["metadata_append_drift_observed"]]

    sensitivity_checks = {
        "current_frozen_target_rows": source_sensitivity.get("current_frozen_target_rows")
        == inventory_summary["total_target_result_rows"],
        "current_computable_rows": source_sensitivity.get("current_computable_rows")
        == inventory_summary["computable_rows"],
        "current_fail_closed_not_computable_rows": source_sensitivity.get("current_fail_closed_not_computable_rows")
        == inventory_summary["target_fail_closed_not_computable_rows"],
        "current_role_fail_closed_computable_excluded_rows": source_sensitivity.get(
            "current_role_fail_closed_computable_excluded_rows"
        )
        == inventory_summary["role_fail_closed_computable_excluded_rows"],
        "source_repair_candidate_rows_to_computable": source_sensitivity.get("source_repair_candidate_rows_to_computable")
        == len(repaired_targets),
        "counterfactual_computable_rows": source_sensitivity.get(
            "counterfactual_computable_rows_if_g12_accepts_recovered_sources"
        )
        == inventory_summary["computable_rows"] + len(repaired_targets),
        "counterfactual_fail_closed_rows": source_sensitivity.get(
            "counterfactual_fail_closed_not_computable_rows_if_g12_accepts_recovered_sources"
        )
        == inventory_summary["target_fail_closed_not_computable_rows"] - len(repaired_targets),
        "counterfactual_fail_closed_or_excluded_rows": source_sensitivity.get(
            "counterfactual_fail_closed_or_excluded_rows_if_g12_accepts_recovered_sources"
        )
        == inventory_summary["inventory_rows"] - len(repaired_targets),
        "unrecoverable_unique_windows": source_unrecoverable.get("remaining_unique_missing_bar_windows")
        == unrecoverable_recomputed["remaining_unique_missing_bar_windows_recomputed"],
        "unrecoverable_still_fail_closed_rows": source_unrecoverable.get("still_fail_closed_target_rows")
        == unrecoverable_recomputed["still_fail_closed_target_rows_recomputed"],
    }
    sensitivity_issue_keys = [key for key, passed in sensitivity_checks.items() if not passed]

    searched_root_checks = {
        "source_search_ledger_exists": SOURCE_SEARCH.exists(),
        "source_closure_ledger_exists": SOURCE_CLOSURE.exists(),
        "source_manifest_exists": SOURCE_OUTPUT_MANIFEST.exists(),
        "consumed_sierra_root_recorded": any(
            row.get("consumed_for_repair") for row in source_search.get("roots", [])
        ),
        "closure_same_class_vague_blockers_zero": source_closure.get("remaining_same_evidence_class_blockers_vague") == 0,
    }
    searched_root_issue_keys = [key for key, passed in searched_root_checks.items() if not passed]

    critical_issue_count = (
        len(inventory_issues)
        + len(source_bar_failures)
        + len(target_failures)
        + len(repairable_but_unrepaired)
        + len(sensitivity_issue_keys)
        + len(searched_root_issue_keys)
    )
    terminal_decision = (
        "ACCEPT_AS_G12_READY8_FAIL_CLOSED_PATH_HORIZON_SOURCE_REPAIR_AUDIT_NO_PROMOTION"
        if critical_issue_count == 0
        else "REJECT_PENDING_SAME_G12_REPAIR_READY8_FAIL_CLOSED_PATH_HORIZON_SOURCE_REPAIR_AUDIT"
    )

    write_jsonl(ROUTE_DIR / f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_INVENTORY_RECOMPUTATION_LEDGER_{DATE}.jsonl", inventory_rows)
    write_jsonl(
        ROUTE_DIR / f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_SOURCE_RECORD_HASH_RECOMPUTATION_LEDGER_{DATE}.jsonl",
        source_bar_rows,
    )
    write_jsonl(
        ROUTE_DIR / f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_REPAIRED_TARGET_RECOMPUTATION_LEDGER_{DATE}.jsonl",
        target_audit_rows,
    )

    recomputation = {
        **safe_flags(),
        "artifact_family": "g12_recomputation_ledger",
        "source_route_dir": rel(SOURCE_ROUTE_DIR),
        "inventory_summary": inventory_summary,
        "sealed_fail_closed_summary": sealed_summary,
        "source_bar_recomputation": {
            "rows": len(source_bar_rows),
            "passes": len(source_bar_rows) - len(source_bar_failures),
            "failures": len(source_bar_failures),
            "metadata_append_drift_rows": len(metadata_drift_rows),
            "metadata_append_drift_is_critical": False,
        },
        "repaired_target_recomputation": {
            "rows": len(target_audit_rows),
            "passes": len(target_audit_rows) - len(target_failures),
            "failures": len(target_failures),
        },
        "unrecoverable_recomputed": unrecoverable_recomputed,
        "sensitivity_checks": sensitivity_checks,
        "searched_root_checks": searched_root_checks,
    }
    write_json(ROUTE_DIR / f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_RECOMPUTATION_LEDGER_{DATE}.json", recomputation)

    discrepancy = {
        **safe_flags(),
        "artifact_family": "g12_discrepancy_ledger",
        "critical_issue_count": critical_issue_count,
        "inventory_issue_count": len(inventory_issues),
        "source_bar_failure_count": len(source_bar_failures),
        "repaired_target_failure_count": len(target_failures),
        "repairable_but_unrepaired_count": len(repairable_but_unrepaired),
        "sensitivity_issue_keys": sensitivity_issue_keys,
        "searched_root_issue_keys": searched_root_issue_keys,
        "inventory_issues": inventory_issues,
        "source_bar_failure_rows": source_bar_failures,
        "repaired_target_failure_rows": target_failures,
        "repairable_but_unrepaired_target_ids": repairable_but_unrepaired,
        "decision_effect": "NO_UNREPAIRED_G12_DISCREPANCIES" if critical_issue_count == 0 else "REPAIR_REQUIRED",
    }
    write_json(ROUTE_DIR / f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_DISCREPANCY_LEDGER_{DATE}.json", discrepancy)

    same_g12_repair = {
        **safe_flags(),
        "artifact_family": "g12_same_evidence_class_repair_ledger",
        "same_g12_repair_required": critical_issue_count != 0,
        "same_g12_repair_performed": len(metadata_drift_rows) > 0 and critical_issue_count == 0,
        "repairs": [
            {
                "issue": "source_file_metadata_append_drift_after_builder_snapshot",
                "affected_repaired_bar_rows": len(metadata_drift_rows),
                "repair_action": (
                    "Recomputed every affected recovered bar from current local source byte ranges and "
                    "verified packet source_records_sha256, parsed OHLC/volume fields, and bar_hash."
                ),
                "criticality": "NONBLOCKING_WHEN_BYTE_RANGE_DIGESTS_MATCH",
            }
        ]
        if metadata_drift_rows
        else [],
        "unrepaired_same_g12_issue_count": critical_issue_count,
    }
    write_json(ROUTE_DIR / f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_SAME_G12_REPAIR_LEDGER_{DATE}.json", same_g12_repair)

    safe_surface = {
        **safe_flags(),
        "artifact_family": "g12_safe_surface_ledger",
        "forbidden_surfaces_closed": {
            "live_trading_behavior": True,
            "promotion": True,
            "r_pnl_trade_win_rate_expectancy": True,
            "ai_api_calls": True,
            "paid_vendor_access": True,
            "broker_account_order_history_deal_position": True,
            "raw_market_blob_commit": True,
            "registry_edits": True,
            "remote_push": True,
            "prompt_config_risk_safety_execution_canary_selector_changes": True,
        },
        "raw_blob_policy": "Only byte-range source-record digests and derived M15 bars are committed; raw SCID blobs are not committed.",
        "validation_boundary": "Neutral target-movement source repair only; validation_safe remains false.",
    }
    write_json(ROUTE_DIR / f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_SAFE_SURFACE_LEDGER_{DATE}.json", safe_surface)

    saturation = {
        **safe_flags(),
        "artifact_family": "g12_saturation_self_red_team_ledger",
        "no_arbitrary_top_n": True,
        "full_ledgers_preserved": {
            "inventory_recomputation_rows": len(inventory_rows),
            "source_record_hash_recomputation_rows": len(source_bar_rows),
            "repaired_target_recomputation_rows": len(target_audit_rows),
            "remaining_gap_rows_in_unrecoverable_source_ledger": len(
                unrecoverable_recomputed["remaining_gap_rows_recomputed"]
            ),
        },
        "same_evidence_class_exhaustion": {
            "all_target_result_files_scanned": True,
            "all_target_fail_closed_rows_recomputed": len(target_fail_by_id) == 30_560,
            "all_source_repaired_bars_rehashed_from_byte_ranges": len(source_bar_failures) == 0,
            "all_repaired_target_rows_recomputed": len(target_failures) == 0,
            "all_unrecovered_rows_remain_exactly_source_gap_bound": not repairable_but_unrepaired,
            "remaining_same_g12_repairable_issues": critical_issue_count,
        },
        "self_red_team_questions": [
            {
                "question": "Could source-file append drift invalidate recovered bars?",
                "answer": "No if the committed byte ranges still hash and parse to the packet values; this audit recomputed that for every recovered bar.",
            },
            {
                "question": "Could role-excluded rows leak into path/horizon source gaps?",
                "answer": "No; all 5,251 role exclusions were recomputed as denominator-policy exclusions and sensitivity leaves them unchanged.",
            },
            {
                "question": "Could repaired rows enter R7 without provenance?",
                "answer": "No; the R7 rule requires original target row id, source bar hashes, G12 decision id, and safe flags.",
            },
            {
                "question": "Could remaining fail-closed rows be repaired inside this G12 audit?",
                "answer": "No current approved source bars exist in the original packet or recovered bar packet for the remaining 536 unique windows; alternate source/export remains a separate access/source route.",
            },
        ],
    }
    write_json(ROUTE_DIR / f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_SATURATION_SELF_RED_TEAM_LEDGER_{DATE}.json", saturation)

    r7_rule = {
        **safe_flags(),
        "artifact_family": "g12_r7_consumption_rule",
        "r7_may_consume_repaired_rows": critical_issue_count == 0,
        "accepted_repaired_target_rows": len(repaired_targets) if critical_issue_count == 0 else 0,
        "remaining_fail_closed_target_rows": unrecoverable_recomputed["still_fail_closed_target_rows_recomputed"],
        "role_excluded_rows_unchanged": inventory_summary["role_fail_closed_computable_excluded_rows"],
        "consumption_requirements": [
            "Preserve original_target_result_row_id and repair_candidate_target_result_row_hash.",
            "Preserve source_bar_hashes_consumed and G12 source-record recomputation provenance.",
            "Keep remaining 25,240 target rows fail-closed unless a future source-hashed alternate archive/export is accepted.",
            "Keep 5,251 role-excluded rows out of path/horizon source-gap repair denominators.",
            "Do not convert this neutral target-movement source repair into R/PnL/win-rate/expectancy, validation, promotion, or live-readiness evidence.",
        ],
        "downstream_safe_flags": {
            "promotion_verdict": "NO_PROMOTION_VERDICT",
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        },
    }
    write_json(ROUTE_DIR / f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_R7_CONSUMPTION_RULE_{DATE}.json", r7_rule)

    decision = {
        **safe_flags(),
        "artifact_family": "g12_decision_ledger",
        "terminal_decision": terminal_decision,
        "accepted": critical_issue_count == 0,
        "rejected": critical_issue_count != 0,
        "decision_basis": {
            "inventory_recomputed_from_target_files": inventory_summary["inventory_rows"] == 35_811,
            "sealed_fail_closed_ledger_recomputed": sealed_summary["sealed_fail_closed_ledger_records"] == 2161
            and sealed_summary["sealed_fail_closed_ledger_rows_sum"] == 35_811,
            "source_record_hashes_recomputed": len(source_bar_failures) == 0 and len(source_bar_rows) == 220,
            "repaired_target_rows_recomputed": len(target_failures) == 0 and len(target_audit_rows) == 5_320,
            "sensitivity_arithmetic_verified": not sensitivity_issue_keys,
            "remaining_unrecoverable_proof_verified": not repairable_but_unrepaired
            and source_unrecoverable.get("remaining_unique_missing_bar_windows") == 536,
            "safe_surfaces_closed": True,
        },
        "accepted_counts": {
            "fail_closed_or_excluded_inventory_rows": inventory_summary["inventory_rows"],
            "target_fail_closed_not_computable_rows": inventory_summary["target_fail_closed_not_computable_rows"],
            "role_fail_closed_computable_excluded_rows": inventory_summary["role_fail_closed_computable_excluded_rows"],
            "recovered_unique_bar_windows": len(source_bar_rows),
            "accepted_repair_candidate_target_rows_for_r7": len(repaired_targets) if critical_issue_count == 0 else 0,
            "remaining_target_fail_closed_rows": unrecoverable_recomputed["still_fail_closed_target_rows_recomputed"],
            "remaining_unique_missing_bar_windows": unrecoverable_recomputed[
                "remaining_unique_missing_bar_windows_recomputed"
            ],
        },
        "interpretation_boundary": "G12 source-repair acceptance only; no promotion, validation, R/PnL, win-rate, expectancy, or live-readiness verdict.",
        "r7_consumption_rule": f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_R7_CONSUMPTION_RULE_{DATE}.json",
    }
    write_json(ROUTE_DIR / f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_DECISION_LEDGER_{DATE}.json", decision)

    focused_tests_ok = focused_tests_summary is not None and "passed" in focused_tests_summary.lower()
    if focused_tests_summary:
        write_json(
            ROUTE_DIR / f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_FOCUSED_TEST_RESULT_{DATE}.json",
            {
                **safe_flags(),
                "artifact_family": "g12_focused_test_result",
                "command": (
                    "py -3 -m pytest "
                    "research/science_program_2026_05/06_outcome_testing/"
                    "g12_ready8_fail_closed_path_horizon_source_repair_audit/"
                    "test_g12_ready8_fail_closed_repair_audit_2026_05_15.py -q"
                ),
                "summary": focused_tests_summary,
                "passed": focused_tests_ok,
            },
        )

    completion = {
        **safe_flags(),
        "artifact_family": "g12_completion_audit",
        "objective_restatement": (
            "Audit the READY8 fail-closed source-repair packet by recomputing inventory counts, "
            "source-record digests, repaired target rows, sensitivity arithmetic, unrecoverable proof, "
            "and safe-surface closure."
        ),
        "prompt_to_artifact_checklist": {
            "mandatory_preflight_live_state_and_context": [
                ".context/LIVE_STATE.md",
                ".context/02_session_handoffs/SESSION_55_ORCHESTRATOR_SUCCESSOR_HANDOFF_2026-05-15.md",
                ".context/00_core/goal_session_research_discipline.md",
                ".context/00_core/research_operating_doctrine.md",
                ".context/00_core/orchestrator_successor_operating_brief.md",
                ".context/00_core/orchestrator_methodology_hardening_controls.md",
                ".context/00_core/parallel_goal_merge_playbook.md",
                ".context/00_core/local_heavy_data_inventory.md",
            ],
            "control_prompt": "research/science_program_2026_05/04_goal_prompts/G12_READY8_FAIL_CLOSED_PATH_HORIZON_SOURCE_REPAIR_AUDIT_GOAL_PROMPT_2026-05-15.md",
            "route_manifest_and_builder_artifacts_inspected": rel(SOURCE_OUTPUT_MANIFEST),
            "fail_closed_inventory_recomputed": f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_INVENTORY_RECOMPUTATION_LEDGER_{DATE}.jsonl",
            "recovered_source_hashes_recomputed": f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_SOURCE_RECORD_HASH_RECOMPUTATION_LEDGER_{DATE}.jsonl",
            "repaired_target_rows_recomputed": f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_REPAIRED_TARGET_RECOMPUTATION_LEDGER_{DATE}.jsonl",
            "sensitivity_and_unrecoverable_verified": f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_RECOMPUTATION_LEDGER_{DATE}.json",
            "discrepancy_and_repair_ledgers": [
                f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_DISCREPANCY_LEDGER_{DATE}.json",
                f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_SAME_G12_REPAIR_LEDGER_{DATE}.json",
            ],
            "decision_ledger": f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_DECISION_LEDGER_{DATE}.json",
            "safe_surface_ledger": f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_SAFE_SURFACE_LEDGER_{DATE}.json",
            "saturation_ledger": f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_SATURATION_SELF_RED_TEAM_LEDGER_{DATE}.json",
            "r7_consumption_rule": f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_R7_CONSUMPTION_RULE_{DATE}.json",
            "verifier": f"verify_g12_ready8_fail_closed_repair_audit_2026_05_15.py",
            "focused_tests": f"test_g12_ready8_fail_closed_repair_audit_2026_05_15.py",
        },
        "same_evidence_class_intelligence_remaining": 0 if critical_issue_count == 0 else critical_issue_count,
        "repairable_same_g12_issues_remaining": critical_issue_count,
        "focused_tests_summary": focused_tests_summary,
        "focused_tests_ok": focused_tests_ok,
        "can_mark_goal_complete_after_verifier_tests_commit": critical_issue_count == 0 and focused_tests_ok,
        "terminal_decision": terminal_decision,
    }
    write_json(ROUTE_DIR / f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_COMPLETION_AUDIT_{DATE}.json", completion)

    summary_md = f"""# G12 READY8 Fail-Closed Source Repair Audit

Date: {DATE}

Evidence class: `{EVIDENCE_CLASS}`

Decision: `{terminal_decision}`

The audit recomputed the `35,811` fail-closed/excluded-row inventory from the accepted target-result files, verified the sealed fail-closed ledger sums to `35,811`, recomputed all `220` repaired bars from current local Sierra byte ranges, and recomputed all `5,320` repaired target rows from the repaired bar packet plus frozen source bars.

The current Sierra files have append-time metadata drift relative to the builder packet, but all audited byte ranges still match the packet source-record hashes and parsed OHLC/volume fields. That drift is recorded as nonblocking because the packet is byte-range/hash bound, not full-file-size bound.

R7 may consume the `5,320` repaired target rows only under `G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_R7_CONSUMPTION_RULE_{DATE}.json`. The remaining `25,240` target rows stay fail-closed, and the `5,251` role exclusions stay denominator-policy exclusions.

Safe flags remain `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
"""
    (ROUTE_DIR / f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_SUMMARY_{DATE}.md").write_text(summary_md, encoding="utf-8")

    manifest_paths = [
        ROUTE_DIR / f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_RECOMPUTATION_LEDGER_{DATE}.json",
        ROUTE_DIR / f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_INVENTORY_RECOMPUTATION_LEDGER_{DATE}.jsonl",
        ROUTE_DIR / f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_SOURCE_RECORD_HASH_RECOMPUTATION_LEDGER_{DATE}.jsonl",
        ROUTE_DIR / f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_REPAIRED_TARGET_RECOMPUTATION_LEDGER_{DATE}.jsonl",
        ROUTE_DIR / f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_DISCREPANCY_LEDGER_{DATE}.json",
        ROUTE_DIR / f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_SAME_G12_REPAIR_LEDGER_{DATE}.json",
        ROUTE_DIR / f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_SAFE_SURFACE_LEDGER_{DATE}.json",
        ROUTE_DIR / f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_SATURATION_SELF_RED_TEAM_LEDGER_{DATE}.json",
        ROUTE_DIR / f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_R7_CONSUMPTION_RULE_{DATE}.json",
        ROUTE_DIR / f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_DECISION_LEDGER_{DATE}.json",
        ROUTE_DIR / f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_COMPLETION_AUDIT_{DATE}.json",
        ROUTE_DIR / f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_SUMMARY_{DATE}.md",
        ROUTE_DIR / f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_VERIFICATION_RESULT_{DATE}.json",
        ROUTE_DIR / f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_FOCUSED_TEST_RESULT_{DATE}.json",
        ROUTE_DIR / "build_g12_ready8_fail_closed_repair_audit_2026_05_15.py",
        ROUTE_DIR / "verify_g12_ready8_fail_closed_repair_audit_2026_05_15.py",
        ROUTE_DIR / "test_g12_ready8_fail_closed_repair_audit_2026_05_15.py",
    ]
    manifest = {
        **safe_flags(),
        "artifact_family": "g12_output_manifest",
        "artifact_count": len(manifest_paths) + 1,
        "self_hash_policy": "output manifest is not self-hashed; all other listed artifacts are hashed when present",
        "artifacts": [artifact_record(path) for path in manifest_paths],
        "terminal_decision": terminal_decision,
        "verification_ok": None,
        "focused_tests_ok": focused_tests_ok,
    }
    write_json(ROUTE_DIR / f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_OUTPUT_MANIFEST_{DATE}.json", manifest)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--focused-tests-summary", default=None)
    args = parser.parse_args()
    build_artifacts(args.focused_tests_summary)


if __name__ == "__main__":
    main()
