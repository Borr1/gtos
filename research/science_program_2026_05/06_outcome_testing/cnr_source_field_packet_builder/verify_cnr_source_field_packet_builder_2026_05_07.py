#!/usr/bin/env python
"""Machine checks for the CNR source-field packet-builder lane."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


LANE_DIR = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[4]
DATE = "2026-05-07"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
REQUIRED_FALSE_FLAGS = ("validation_safe", "outcome_review_opened", "live_effect")
REQUIRED_ZERO_CALLS = ("mt5_order_calls", "order_calls", "paid_data_calls", "databento_calls", "api_calls")

REQUIRED_JSON_BASES = [
    "CNR_SOURCE_FIELD_PACKET_BUILDER_CONTEXT_ANCHOR",
    "CNR_SOURCE_FIELD_CAPTURE_LEDGER",
    "CNR_SOURCE_FIELD_PACKET_MANIFEST",
    "CNR_SOURCE_FIELD_SOURCE_HASH_MANIFEST",
    "CNR_SOURCE_FIELD_MULTITIMEFRAME_EVIDENCE_MAP",
    "CNR_SOURCE_FIELD_DATA_EXTRACTION_LEDGER",
    "CNR_SOURCE_FIELD_NOLEAK_FORBIDDEN_FIELD_SCAN",
    "CNR_SOURCE_FIELD_DUPLICATE_DENOMINATOR_REPORT",
    "CNR_SOURCE_FIELD_SAMPLE_FLOOR_AND_EXPANSION_REPORT",
    "CNR_SOURCE_FIELD_ANTI_BOXING_REVIEW",
    "CNR_SOURCE_FIELD_COMPLETION_AUDIT",
]

REQUIRED_MD_BASES = REQUIRED_JSON_BASES + [
    "CNR_SOURCE_FIELD_NEXT_G12_AUDIT_PROMPT_PACK",
]

REQUIRED_ROW_FIELDS = [
    "packet_id",
    "record_id",
    "symbol",
    "side",
    "session",
    "timing_model_family",
    "target_model_family",
    "candidate_close_utc",
    "signal_emitted_utc",
    "decision_asof_utc",
    "quote_timestamp_utc",
    "bid",
    "ask",
    "spread",
    "quote_side_rule",
    "original_entry_price",
    "original_stop_loss",
    "original_take_profit_1",
    "duplicate_group_id",
    "denominator_unit",
    "source_file_paths",
    "source_sha256_hashes",
    "parser_version",
    "timestamp_convention",
    "asof_cutoff_utc",
    "allowed_predecision_context_fields_by_timeframe",
    "terminal_state_policy",
    "blocker_state",
    "forbidden_field_scan_result",
]

REQUIRED_PACKET_IDS = {"OTG0-PKT-060", "OTG0-PKT-061", "OTG0-PKT-062", "OTG0-PKT-063", "OTG0-PKT-066"}
REQUIRED_TIMING = {
    "CNR_E0_DECISION_CLOSE_MARKET",
    "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE",
    "CNR_E2_SIGNAL_EMIT_FIRST_VALID_TICK",
    "CNR_E3_LATENCY_BOUNDED_DECISION_WINDOW",
    "CNR_E4_PRETOUCH_CONTINUATION_TRIGGER",
}
REQUIRED_TARGETS = {
    "CNR_T0_ORIGINAL_TP1",
    "CNR_T1_FIXED_R_FROM_EXECUTABLE_ENTRY",
    "CNR_T2_ASOF_STRUCTURAL_LEVEL",
    "CNR_T3_TIMEBOX_TERMINAL",
}

FORBIDDEN_ROW_KEYS = {
    "synthetic_path_r",
    "synthetic_r",
    "result_status",
    "target_hit_timestamp",
    "stop_hit_timestamp",
    "hit_sl",
    "hit_tp1",
    "first_touch_times",
    "later_path_label",
    "path_label",
    "broker_actual_r",
    "account_history",
}

ALLOWED_FLAG_KEYS = {
    "broker_actual_r_accessed",
    "account_history_accessed",
    "blocked_packet_outcome_source_read",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_rows() -> list[dict[str, Any]]:
    rows_path = LANE_DIR / f"CNR_SOURCE_FIELD_PACKET_ROWS_{DATE}.jsonl"
    rows = []
    with rows_path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            row["_line_number"] = line_number
            rows.append(row)
    return rows


def verify_flags(payload: dict[str, Any], name: str, issues: list[str]) -> None:
    if payload.get("promotion_verdict") != PROMOTION_VERDICT:
        issues.append(f"{name}: promotion_verdict is not {PROMOTION_VERDICT}")
    for flag in REQUIRED_FALSE_FLAGS:
        if payload.get(flag) is not False:
            issues.append(f"{name}: {flag} is not false")
    for field in REQUIRED_ZERO_CALLS:
        value = payload.get(field, 0)
        if value not in (0, None):
            issues.append(f"{name}: {field} is {value}")


def walk_keys(obj: Any, issues: list[str], path: str = "") -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            key_path = f"{path}.{key}" if path else key
            if key in FORBIDDEN_ROW_KEYS and key not in ALLOWED_FLAG_KEYS:
                issues.append(f"forbidden row key {key_path}")
            walk_keys(value, issues, key_path)
    elif isinstance(obj, list):
        for index, item in enumerate(obj):
            walk_keys(item, issues, f"{path}[{index}]")


def verify() -> dict[str, Any]:
    issues: list[str] = []
    warnings: list[str] = []

    for base in REQUIRED_JSON_BASES:
        path = LANE_DIR / f"{base}_{DATE}.json"
        if not path.exists():
            issues.append(f"missing JSON artifact {path.name}")
            continue
        try:
            payload = load_json(path)
        except Exception as exc:
            issues.append(f"cannot parse {path.name}: {type(exc).__name__}: {exc}")
            continue
        verify_flags(payload, path.name, issues)

    for base in REQUIRED_MD_BASES:
        suffix = "" if base.endswith(DATE) else f"_{DATE}"
        path = LANE_DIR / f"{base}{suffix}.md"
        if not path.exists():
            issues.append(f"missing MD artifact {path.name}")
            continue
        text = path.read_text(encoding="utf-8")
        if "NO_PROMOTION_VERDICT" not in text or "Validation safe: `false`" not in text:
            issues.append(f"{path.name}: missing required visible flags")

    rows_path = LANE_DIR / f"CNR_SOURCE_FIELD_PACKET_ROWS_{DATE}.jsonl"
    if not rows_path.exists():
        issues.append("missing packet rows JSONL")
        rows = []
    else:
        rows = load_rows()
    if not rows:
        issues.append("packet rows JSONL has no rows")

    packets = {row.get("packet_id") for row in rows}
    timings = {row.get("timing_model_family") for row in rows}
    targets = {row.get("target_model_family") for row in rows}
    if not REQUIRED_PACKET_IDS.issubset(packets):
        issues.append(f"missing packet IDs: {sorted(REQUIRED_PACKET_IDS - packets)}")
    if timings != REQUIRED_TIMING:
        issues.append(f"timing families mismatch: {sorted(timings)}")
    if targets != REQUIRED_TARGETS:
        issues.append(f"target families mismatch: {sorted(targets)}")

    ready = 0
    quote_rows = 0
    denom_counter = Counter()
    per_packet_records = defaultdict(set)
    for row in rows:
        missing = [field for field in REQUIRED_ROW_FIELDS if field not in row]
        if missing:
            issues.append(f"line {row.get('_line_number')}: missing required fields {missing}")
        verify_flags(row, f"row {row.get('record_id')}", issues)
        if row.get("forbidden_field_scan_result") != "PASS_PACKET_ROW_INPUT_ONLY_NO_FORBIDDEN_RESULT_FIELDS":
            issues.append(f"row {row.get('record_id')}: forbidden_field_scan_result not PASS")
        row_key_issues: list[str] = []
        walk_keys(row, row_key_issues)
        for item in row_key_issues:
            issues.append(f"row {row.get('record_id')}: {item}")
        if row.get("blocker_state") == "READY_INPUT_ONLY_FOR_G12_G0_AUDIT":
            ready += 1
        if row.get("quote_source_status") == "QUOTE_EXTRACTED_SOURCE_HASHED":
            quote_rows += 1
        denom_counter[row.get("duplicate_denominator_key")] += 1
        per_packet_records[row.get("packet_id")].add(row.get("source_record_id"))

    if ready == 0:
        issues.append("no ready input-only rows")
    if quote_rows == 0:
        issues.append("no source-hashed quote rows")
    for packet_id in REQUIRED_PACKET_IDS:
        if len(per_packet_records[packet_id]) == 0:
            issues.append(f"{packet_id}: no source records represented")

    source_manifest_path = LANE_DIR / f"CNR_SOURCE_FIELD_SOURCE_HASH_MANIFEST_{DATE}.json"
    if source_manifest_path.exists():
        manifest = load_json(source_manifest_path)
        missing_hashes = []
        mismatches = []
        for item in manifest.get("source_files", []):
            if not item.get("exists") or item.get("sha256_status") != "HASHED":
                if item.get("required"):
                    missing_hashes.append(item.get("path"))
                continue
            path = Path(item["absolute_path"])
            if path.exists() and path.is_file() and path.stat().st_size <= 25_000_000:
                actual = sha256_file(path)
                if actual != item.get("sha256"):
                    if item.get("strict_hash_reverification") is False:
                        warnings.append(f"dynamic snapshot hash changed since packet build: {item.get('path')}")
                    else:
                        mismatches.append(item.get("path"))
            elif path.exists() and path.is_file():
                warnings.append(f"large hash not recomputed in verifier: {item.get('path')}")
        if missing_hashes:
            issues.append(f"missing required hashes: {missing_hashes[:10]}")
        if mismatches:
            issues.append(f"hash mismatches: {mismatches[:10]}")

    lane_dirs = [p.name.lower() for p in LANE_DIR.iterdir() if p.is_dir()]
    bad_dirs = [name for name in lane_dirs if "result" in name or "quarantine" in name]
    if bad_dirs:
        issues.append(f"result/quarantine-like output directories exist in lane: {bad_dirs}")

    forbidden_scan = LANE_DIR / f"CNR_SOURCE_FIELD_NOLEAK_FORBIDDEN_FIELD_SCAN_{DATE}.json"
    if forbidden_scan.exists():
        scan = load_json(forbidden_scan)
        if scan.get("scan_status") != "PASS":
            issues.append(f"forbidden scan status is {scan.get('scan_status')}")

    return {
        "status": "PASS" if not issues else "FAIL",
        "issues": issues,
        "warnings": warnings,
        "row_count": len(rows),
        "ready_rows": ready,
        "quote_rows": quote_rows,
        "packet_ids": sorted(packets),
        "timing_families": sorted(timings),
        "target_families": sorted(targets),
    }


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS" else 1)
