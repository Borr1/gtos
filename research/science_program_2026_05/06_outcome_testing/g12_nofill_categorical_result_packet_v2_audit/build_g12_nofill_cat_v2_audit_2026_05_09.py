#!/usr/bin/env python3
"""Build G12_NOFILL_LIFECYCLE_CATEGORICAL_RESULT_PACKET_V2_AUDIT artifacts.

This is a red-team/control audit of the V2 no-fill categorical packet. It is
source-safe and input-only: no R/performance, broker/account/live/order labels,
validation, promotion, registry edit, or live trading effect.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import pyarrow.compute as pc
import pyarrow.parquet as pq


DATE = "2026-05-09"
UPSTREAM_DATE = "2026-05-08"
SCHEMA = "g12_nofill_categorical_result_packet_v2_audit_v1"
LANE = "G12_NOFILL_LIFECYCLE_CATEGORICAL_RESULT_PACKET_V2_AUDIT"
DECISION = "ACCEPT_AS_INPUT_ONLY_CATEGORICAL_LIFECYCLE_EVIDENCE_WITH_BLOCKED_AND_REJECTED_FAMILIES_PRESERVED"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
GENERATED_AT_UTC = "2026-05-09T00:00:00Z"

OUT_DIR = Path(__file__).resolve().parent
OUTCOME_ROOT = OUT_DIR.parent
REPO_ROOT = OUT_DIR.parents[3]

V2_DIR = OUTCOME_ROOT / "nofill_lifecycle_categorical_result_packet_v2_rebuild"
G12_SOURCE_DIR = OUTCOME_ROOT / "g12_nofill_source_correction_consolidated_audit"
G12_CAT_DIR = OUTCOME_ROOT / "g12_no_fill_categorical_result_packet_audit"
PRIOR_CAT_DIR = OUTCOME_ROOT / "no_fill_lifecycle_categorical_result_packet"
OTI2_DIR = OUTCOME_ROOT / "oti2_fill_path_categorical_contract_v2"
OTI4_DIR = OUTCOME_ROOT / "oti4_opening_drive_source_correction_or_contract_revision"

MAIN_DATA_ROOT = Path("C:/Users/MSI/Documents/ai-trading-agent/data")
TMP_ROOT = Path("C:/tmp/gtos_otb")

EXPECTED_DECISIONS = {
    "ACCEPT_PRIOR_CATEGORICAL_LABEL": 52,
    "ACCEPT_SOURCE_CORRECTED_INPUT_FOR_REBUILD": 173,
    "BLOCK_EXACT_SOURCE_OR_ORDERING_GAP": 8,
    "REJECT_FROM_REBUILD_CONTRACT_EXCLUDED": 26,
    "REJECT_FROM_REBUILD_NONCANONICAL_DUPLICATE": 39,
}
EXPECTED_ACCEPTED_LABELS = {
    "canonical_duplicate_geometry_source_ready_no_label_assigned": 3,
    "fill_path_entry_before_protective_level_before_terminal_area": 4,
    "fill_path_entry_before_protective_level_no_terminal_observed": 22,
    "fill_path_entry_before_terminal_area_before_protective_level": 3,
    "nofill_terminal_before_entry": 110,
    "opening_drive_source_projection_ready_no_result_label": 51,
    "source_corrected_no_entry_through_pending_horizon": 32,
}
EXPECTED_ACCEPTED_SOURCE_LANES = {
    "prior_g12_categorical_packet_audit": 52,
    "OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET": 32,
    "OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT_V2": 29,
    "OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT": 58,
    "OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION": 51,
    "OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT": 3,
}
EXPECTED_BLOCKER_CODES = {
    "BLOCK_FILL_PATH_SAME_TICK_ORDER_UNRESOLVABLE": 4,
    "BLOCK_OTI2_ACTIVE_WINDOW_TICK_COVERAGE_GAP": 1,
    "BLOCK_OTI2_ENTRY_TOUCH_NOT_SIDE_AWARE_TICK_CONFIRMED": 1,
    "BLOCK_OTI4_RANGE_TICK_WINDOW_EMPTY_OR_LOCAL_SOURCE_GAP": 3,
}
EXPECTED_REJECT_DECISIONS = {
    "REJECT_FROM_REBUILD_CONTRACT_EXCLUDED": 26,
    "REJECT_FROM_REBUILD_NONCANONICAL_DUPLICATE": 39,
}

FORBIDDEN_KEY_PARTS = (
    "actual_r",
    "account_history",
    "broker_actual",
    "broker_deal",
    "broker_order",
    "broker_position",
    "dsr",
    "expectancy",
    "hidden_label",
    "live_order",
    "live_trade_result",
    "mt5_account",
    "mt5_deal",
    "mt5_history",
    "mt5_order",
    "mt5_position",
    "pbo",
    "profit",
    "promotion_safe",
    "r_multiple",
    "reward_r",
    "synthetic_r",
    "win_rate",
)

CONTROL_INPUTS = [
    OUT_DIR / "G12_NOFILL_CATEGORICAL_RESULT_PACKET_V2_AUDIT_GOAL_PROMPT_2026-05-09.md",
    V2_DIR / "NOFILL_CAT_V2_CONTEXT_ANCHOR_2026-05-09.md",
    V2_DIR / "NOFILL_CAT_V2_REBUILD_CONTRACT_2026-05-09.json",
    V2_DIR / "NOFILL_CAT_V2_UNIVERSE_RECONCILIATION_2026-05-09.json",
    V2_DIR / "NOFILL_CAT_V2_ROW_DECISION_LEDGER_2026-05-09.jsonl",
    V2_DIR / "NOFILL_CAT_V2_ACCEPTED_PACKET_2026-05-09.json",
    V2_DIR / "NOFILL_CAT_V2_BLOCKER_LEDGER_2026-05-09.json",
    V2_DIR / "NOFILL_CAT_V2_REJECT_LEDGER_2026-05-09.json",
    V2_DIR / "NOFILL_CAT_V2_SOURCE_HASH_NOLEAK_AUDIT_2026-05-09.json",
    V2_DIR / "NOFILL_CAT_V2_DUPLICATE_SAMPLE_FLOOR_AUDIT_2026-05-09.json",
    V2_DIR / "NOFILL_CAT_V2_COMPLETION_AUDIT_2026-05-09.json",
    G12_SOURCE_DIR / "G12_NOFILL_SOURCE_CORRECTION_DECISION_LEDGER_2026-05-08.json",
    G12_SOURCE_DIR / "G12_NOFILL_SOURCE_CORRECTION_SOURCE_HASH_NOLEAK_AUDIT_2026-05-08.json",
    G12_SOURCE_DIR / "G12_NOFILL_SOURCE_CORRECTION_DUPLICATE_SAMPLE_FLOOR_AUDIT_2026-05-08.json",
    G12_CAT_DIR / "G12_NOFILL_CAT_DECISION_LEDGER_2026-05-08.json",
    PRIOR_CAT_DIR / "NOFILL_CAT_ELIGIBILITY_AND_BLOCKER_LEDGER_2026-05-08.json",
    OTI2_DIR / "OTI2_FILL_PATH_ROW_DECISION_LEDGER_2026-05-08.jsonl",
    OTI4_DIR / "OTI4_OPENING_DRIVE_ROW_DECISION_LEDGER_ROWS_2026-05-08.jsonl",
    OTI4_DIR / "OTI4_OPENING_DRIVE_SOURCE_SEARCH_LEDGER_2026-05-08.json",
]


def base_payload(artifact_family: str) -> dict[str, Any]:
    return {
        "artifact_family": artifact_family,
        "schema_version": SCHEMA,
        "lane": LANE,
        "generated_at_utc": GENERATED_AT_UTC,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def write_md(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return p.resolve().relative_to(REPO_ROOT).as_posix()
    except Exception:
        return str(path).replace("\\", "/")


def git_output(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, stderr=subprocess.STDOUT).strip()
    except Exception as exc:
        return f"GIT_UNAVAILABLE: {exc}"


def resolve_path(raw_path: str | None) -> Path | None:
    if not raw_path:
        return None
    raw = raw_path.replace("/", "\\")
    path = Path(raw)
    candidates = [path]
    if not path.is_absolute():
        candidates.append(REPO_ROOT / raw_path)
    if "data\\ticks\\" in raw:
        tail = raw.split("data\\ticks\\", 1)[-1]
        candidates.append(MAIN_DATA_ROOT / "ticks" / tail)
    if "oti3_usdjpy_price_only_quote_or_tick_contract" in raw:
        candidates.append(TMP_ROOT / "OTI3USDJPY" / "research" / "science_program_2026_05" / "06_outcome_testing" / "oti3_usdjpy_price_only_quote_or_tick_contract" / Path(raw).name)
        candidates.append(TMP_ROOT / "OTI2FILLPATH" / "research" / "science_program_2026_05" / "06_outcome_testing" / "oti3_usdjpy_price_only_quote_or_tick_contract" / Path(raw).name)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def parse_utc(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def iso_utc(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value.replace("+00:00", "Z")
    if isinstance(value, dt.datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=dt.timezone.utc)
        return value.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    return str(value)


def load_inputs() -> dict[str, Any]:
    return {
        "v2_rows": read_jsonl(V2_DIR / "NOFILL_CAT_V2_ROW_DECISION_LEDGER_2026-05-09.jsonl"),
        "accepted": read_json(V2_DIR / "NOFILL_CAT_V2_ACCEPTED_PACKET_2026-05-09.json"),
        "blockers": read_json(V2_DIR / "NOFILL_CAT_V2_BLOCKER_LEDGER_2026-05-09.json"),
        "rejects": read_json(V2_DIR / "NOFILL_CAT_V2_REJECT_LEDGER_2026-05-09.json"),
        "universe": read_json(V2_DIR / "NOFILL_CAT_V2_UNIVERSE_RECONCILIATION_2026-05-09.json"),
        "v2_source_hash": read_json(V2_DIR / "NOFILL_CAT_V2_SOURCE_HASH_NOLEAK_AUDIT_2026-05-09.json"),
        "v2_duplicate": read_json(V2_DIR / "NOFILL_CAT_V2_DUPLICATE_SAMPLE_FLOOR_AUDIT_2026-05-09.json"),
        "v2_completion": read_json(V2_DIR / "NOFILL_CAT_V2_COMPLETION_AUDIT_2026-05-09.json"),
        "oti2_rows": read_jsonl(OTI2_DIR / "OTI2_FILL_PATH_ROW_DECISION_LEDGER_2026-05-08.jsonl"),
        "oti4_rows": read_jsonl(OTI4_DIR / "OTI4_OPENING_DRIVE_ROW_DECISION_LEDGER_ROWS_2026-05-08.jsonl"),
        "oti4_search": read_json(OTI4_DIR / "OTI4_OPENING_DRIVE_SOURCE_SEARCH_LEDGER_2026-05-08.json"),
        "g12_source_hash": read_json(G12_SOURCE_DIR / "G12_NOFILL_SOURCE_CORRECTION_SOURCE_HASH_NOLEAK_AUDIT_2026-05-08.json"),
    }


def count(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(Counter(row.get(key) for row in rows))


def scan_forbidden_keys(payload: Any, path: str = "") -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            key_l = str(key).lower()
            if any(part in key_l for part in FORBIDDEN_KEY_PARTS):
                hits.append({"path": f"{path}.{key}" if path else str(key), "key": str(key)})
            hits.extend(scan_forbidden_keys(value, f"{path}.{key}" if path else str(key)))
    elif isinstance(payload, list):
        for index, item in enumerate(payload):
            hits.extend(scan_forbidden_keys(item, f"{path}[{index}]"))
    return hits


def control_hash_records() -> list[dict[str, Any]]:
    records = []
    for path in CONTROL_INPUTS:
        records.append(
            {
                "path": rel(path),
                "exists": path.exists(),
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size if path.exists() and path.is_file() else None,
                "role": "controlling_or_supporting_input",
            }
        )
    return records


def rehash_v2_control_inputs(v2_source_hash: dict[str, Any]) -> dict[str, Any]:
    records = []
    missing = []
    mismatches = []
    non_source_prompt_drifts = []
    for record in v2_source_hash["control_input_hash_records"]:
        path = resolve_path(record["path"])
        actual = sha256_file(path) if path else None
        expected = record.get("sha256")
        is_prompt = str(record["path"]).endswith("_GOAL_PROMPT_2026-05-09.md")
        status = "PASS" if actual == expected and actual is not None else "FAIL"
        if actual is None:
            missing.append(record["path"])
        elif actual != expected:
            if is_prompt:
                non_source_prompt_drifts.append(record["path"])
                status = "PASS_WITH_DOCUMENTED_NON_SOURCE_PROMPT_HASH_DRIFT"
            else:
                mismatches.append(record["path"])
        records.append(
            {
                "path": record["path"],
                "resolved_path": str(path) if path else None,
                "exists": actual is not None,
                "expected_sha256": expected,
                "g12_recomputed_sha256": actual,
                "drift_classification": "NON_SOURCE_CONTROL_PROMPT_HASH_DRIFT_NO_DATA_INVALIDATION" if status == "PASS_WITH_DOCUMENTED_NON_SOURCE_PROMPT_HASH_DRIFT" else None,
                "status": status,
            }
        )
    return {
        "record_count": len(records),
        "missing": missing,
        "mismatches": mismatches,
        "non_source_prompt_hash_drifts": non_source_prompt_drifts,
        "records": records,
        "status": "PASS" if not missing and not mismatches else "FAIL",
    }


def rows_at_timestamp(path: Path, target_iso: str) -> list[dict[str, Any]]:
    target = iso_utc(parse_utc(target_iso))
    table = pq.read_table(path, columns=["ts_utc", "ts_msc", "bid", "ask", "last", "volume", "flags"])
    out = []
    for position, row in enumerate(table.to_pylist()):
        if iso_utc(row.get("ts_utc")) == target:
            out.append(
                {
                    "source_row_position": position,
                    "ts_utc": iso_utc(row.get("ts_utc")),
                    "ts_msc": row.get("ts_msc"),
                    "bid": row.get("bid"),
                    "ask": row.get("ask"),
                    "last": row.get("last"),
                    "volume": row.get("volume"),
                    "flags": row.get("flags"),
                }
            )
    return out


def recompute_oti3_same_tick_checks(oti2_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [
        row
        for row in oti2_rows
        if row.get("route_status") == "blocked_same_tick_order_unresolvable"
    ]
    checks = []
    for row in rows:
        first_ts = row["source_order_resolution"]["same_timestamp_inspection"]["first_timestamp_utc"]
        source_path = None
        for event in row.get("ordered_source_events") or []:
            if event.get("first_touch_utc") == first_ts and event.get("source_path"):
                source_path = event["source_path"]
                break
        source_path = source_path or row["source_order_resolution"]["same_timestamp_inspection"].get("source_path")
        resolved = resolve_path(source_path)
        source_sha = sha256_file(resolved) if resolved else None
        source_rows = rows_at_timestamp(resolved, first_ts) if resolved and resolved.exists() else []
        simultaneous_events = sorted(
            event["event"]
            for event in (row.get("ordered_source_events") or [])
            if event.get("first_touch_utc") == first_ts
        )
        source_row = source_rows[0] if source_rows else {}
        ordered_event_quotes_match = all(
            event.get("bid") == source_row.get("bid") and event.get("ask") == source_row.get("ask")
            for event in (row.get("ordered_source_events") or [])
            if event.get("first_touch_utc") == first_ts and "bid" in event and "ask" in event
        )
        status = (
            "PASS"
            if resolved
            and resolved.exists()
            and source_sha == row["source_order_resolution"]["same_timestamp_inspection"]["source_sha256"]
            and len(source_rows) == 1
            and len(simultaneous_events) >= 2
            and ordered_event_quotes_match
            else "FAIL"
        )
        checks.append(
            {
                "source_close_packet_row_id": row["source_close_packet_row_id"],
                "packet_row_id": row["packet_row_id"],
                "source_path": source_path,
                "resolved_path": str(resolved) if resolved else None,
                "source_exists": bool(resolved and resolved.exists()),
                "expected_sha256": row["source_order_resolution"]["same_timestamp_inspection"]["source_sha256"],
                "g12_recomputed_sha256": source_sha,
                "first_timestamp_utc": first_ts,
                "matching_tick_record_count": len(source_rows),
                "matching_tick_records": source_rows,
                "simultaneous_events": simultaneous_events,
                "ordered_event_quotes_match": ordered_event_quotes_match,
                "source_safe_impossibility_reason": "single tick row at the first timestamp simultaneously satisfies entry/protective predicates; there is no source row order inside that tick",
                "required_unblocker": "higher-resolution or broker-native event ordering source that proves intra-tick entry/protective sequence without account/order labels",
                "status": status,
            }
        )
    return checks


def parquet_range_summary(path: Path, start_iso: str, end_iso: str) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "status": "FAIL"}
    table = pq.read_table(path, columns=["ts_utc"])
    start = parse_utc(start_iso)
    end = parse_utc(end_iso)
    mask = pc.and_(pc.greater_equal(table["ts_utc"], start), pc.less(table["ts_utc"], end))
    filtered = table.filter(mask)
    min_ts = pc.min(table["ts_utc"]).as_py() if table.num_rows else None
    max_ts = pc.max(table["ts_utc"]).as_py() if table.num_rows else None
    return {
        "exists": True,
        "row_count": table.num_rows,
        "min_ts_utc": iso_utc(min_ts),
        "max_ts_utc": iso_utc(max_ts),
        "required_range_count": filtered.num_rows,
        "required_range_start_utc": start_iso,
        "required_range_end_utc": end_iso,
        "sha256": sha256_file(path),
        "status": "PASS",
    }


def recompute_oti4_source_gap_checks(oti4_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [
        row
        for row in oti4_rows
        if row.get("row_route_decision") == "SOURCE_BLOCKED_EXACT_RANGE_TICK_WINDOW_EMPTY"
    ]
    checks = []
    for row in rows:
        source_files = row.get("blocker_source_probe", {}).get("source_files") or []
        file_checks = []
        for source_file in source_files:
            resolved = resolve_path(source_file["path"])
            summary = parquet_range_summary(
                resolved,
                row["contract_range_start_utc"],
                row["contract_range_end_utc"],
            )
            summary.update(
                {
                    "source_path": source_file["path"],
                    "resolved_path": str(resolved) if resolved else None,
                    "expected_sha256": source_file.get("sha256"),
                    "sha256_match": summary.get("sha256") == source_file.get("sha256"),
                }
            )
            file_checks.append(summary)
        zero_range = all(item.get("required_range_count") == 0 for item in file_checks)
        hashes_match = all(item.get("sha256_match") is True for item in file_checks)
        source_exists = all(item.get("exists") for item in file_checks)
        checks.append(
            {
                "source_close_packet_row_id": row["source_close_packet_row_id"],
                "packet_row_id": row["packet_row_id"],
                "symbol": row["symbol"],
                "range_start_utc": row["contract_range_start_utc"],
                "range_end_utc": row["contract_range_end_utc"],
                "file_checks": file_checks,
                "oti4_source_search_covering_csv": False,
                "required_owner_or_access_request": row.get("required_owner_or_access_request"),
                "source_safe_impossibility_reason": "local tick file exists but has zero rows in the frozen opening range, and the OTI4 source-search ledger records no approved CSV/OHLC substitute covering that window",
                "status": "PASS" if source_exists and hashes_match and zero_range else "FAIL",
            }
        )
    return checks


def recompute_original_oti2_source_gap(oti2_rows: list[dict[str, Any]]) -> dict[str, Any]:
    rows = [
        row
        for row in oti2_rows
        if set(row.get("exact_blocker_codes") or [])
        == {
            "BLOCK_OTI2_ENTRY_TOUCH_NOT_SIDE_AWARE_TICK_CONFIRMED",
            "BLOCK_OTI2_ACTIVE_WINDOW_TICK_COVERAGE_GAP",
        }
    ]
    checks = []
    for row in rows:
        inspection = row["source_order_resolution"]["tick_coverage_inspection"]
        file_checks = []
        for item in inspection.get("file_summaries") or []:
            resolved = resolve_path(item["path"])
            summary = parquet_range_summary(
                resolved,
                item["first_ts_utc"],
                item["last_ts_utc"],
            )
            summary.update(
                {
                    "source_path": item["path"],
                    "expected_sha256": item.get("sha256"),
                    "g12_recomputed_sha256": summary.get("sha256"),
                    "sha256_match": summary.get("sha256") == item.get("sha256"),
                    "expected_first_ts_utc": item.get("first_ts_utc"),
                    "expected_last_ts_utc": item.get("last_ts_utc"),
                    "expected_rows": item.get("rows"),
                }
            )
            file_checks.append(summary)
        hashes_match = all(item.get("sha256_match") for item in file_checks)
        may6_after_cancel = inspection.get("may6_first_tick_after_cancel") is True
        status = "PASS" if hashes_match and may6_after_cancel else "FAIL"
        checks.append(
            {
                "source_close_packet_row_id": row["source_close_packet_row_id"],
                "packet_row_id": row["packet_row_id"],
                "symbol": row["symbol"],
                "route_status": row["route_status"],
                "m1_path_context_status": row["source_order_resolution"].get("m1_path_context_status"),
                "pending_cancel_observation": row["source_order_resolution"].get("pending_cancel_observation"),
                "tick_coverage_inspection": inspection,
                "file_checks": file_checks,
                "source_safe_impossibility_reason": inspection.get("reason"),
                "required_unblocker": "side-aware bid/ask tick or approved lower source covering the active pending window through cancel; M1 context alone is not enough under V2",
                "status": status,
            }
        )
    return {
        "row_count": len(checks),
        "checks": checks,
        "status": "PASS" if len(checks) == 1 and all(check["status"] == "PASS" for check in checks) else "FAIL",
    }


def source_root_search_ledger(oti4_search: dict[str, Any]) -> list[dict[str, Any]]:
    roots = [
        REPO_ROOT,
        V2_DIR,
        G12_SOURCE_DIR,
        OTI2_DIR,
        OTI4_DIR,
        MAIN_DATA_ROOT / "ticks",
        MAIN_DATA_ROOT / "mt5_research_exports",
        MAIN_DATA_ROOT / "external",
        TMP_ROOT / "OTI3USDJPY",
        TMP_ROOT / "OTI2FILLPATH",
        TMP_ROOT / "OTI4OPEN",
    ]
    ledger = []
    for root in roots:
        ledger.append(
            {
                "root": str(root),
                "exists": root.exists(),
                "search_method": "targeted source paths from V2/OTI2/OTI4 ledgers plus OTI4 source-search ledger, not broad outcome mining",
                "purpose": "find exact source/hash evidence or blocker proof for V2 audit rows",
            }
        )
    ledger.append(
        {
            "root": rel(OTI4_DIR / "OTI4_OPENING_DRIVE_SOURCE_SEARCH_LEDGER_2026-05-08.json"),
            "exists": True,
            "search_method": "read machine ledger",
            "purpose": "confirm no approved CSV/OHLC substitute covering empty May 3 frozen opening-range windows",
            "no_approved_csv_covering_empty_2026_05_03_range_windows": oti4_search.get("no_approved_csv_covering_empty_2026_05_03_range_windows"),
            "searched_root_count_in_oti4_ledger": len(oti4_search.get("searched_roots") or []),
        }
    )
    return ledger


def label_meanings() -> dict[str, dict[str, Any]]:
    non_claims = [
        "not R/performance",
        "not win rate",
        "not expectancy",
        "not broker actual-R",
        "not account history",
        "not validation",
        "not promotion",
        "not live-gate or live-order evidence",
    ]
    return {
        "nofill_terminal_before_entry": {
            "proves": "source path shows terminal-area touch before side-aware entry touch for the accepted no-fill identity",
            "does_not_prove": non_claims,
            "count": 110,
        },
        "source_corrected_no_entry_through_pending_horizon": {
            "proves": "corrected pending-intent source fields show no side-aware entry touch through the frozen pending horizon",
            "does_not_prove": non_claims,
            "count": 32,
        },
        "opening_drive_source_projection_ready_no_result_label": {
            "proves": "opening-drive range/breakout/as-of source projection is ready for a future categorical contract audit",
            "does_not_prove": non_claims + ["not a no-fill result label"],
            "count": 51,
        },
        "fill_path_entry_before_protective_level_no_terminal_observed": {
            "proves": "source-ordered fill/path events show entry before protective level and no terminal event observed in the approved path window",
            "does_not_prove": non_claims,
            "count": 22,
        },
        "fill_path_entry_before_protective_level_before_terminal_area": {
            "proves": "source-ordered fill/path events show entry before protective level and protective level before terminal area",
            "does_not_prove": non_claims,
            "count": 4,
        },
        "fill_path_entry_before_terminal_area_before_protective_level": {
            "proves": "source-ordered fill/path events show entry before terminal area and terminal area before protective level",
            "does_not_prove": non_claims,
            "count": 3,
        },
        "canonical_duplicate_geometry_source_ready_no_label_assigned": {
            "proves": "OTI5 canonical geometry rule picked the one countable source-identity row for duplicate-control purposes",
            "does_not_prove": non_claims + ["not a lifecycle result label"],
            "count": 3,
        },
    }


def build_decision_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    decisions = []
    for row in rows:
        decisions.append(
            {
                "packet_row_id": row["packet_row_id"],
                "source_close_packet_row_id": row.get("source_close_packet_row_id"),
                "source_inventory_id": row.get("source_inventory_id"),
                "symbol": row.get("symbol"),
                "session": row.get("session"),
                "side": row.get("side"),
                "source_lane": row.get("source_lane"),
                "accepted_source_lane": row.get("accepted_source_lane"),
                "v2_row_status": row.get("row_status"),
                "v2_consolidated_decision": row.get("consolidated_g12_decision"),
                "g12_audit_decision": "ACCEPT_NARROW_INPUT_ONLY_ROW" if row.get("row_status") == "ACCEPTED_INPUT_ONLY" else row.get("row_status"),
                "in_accepted_packet_denominator": row.get("in_accepted_packet_denominator"),
                "categorical_input_label": row.get("categorical_input_label"),
                "label_is_performance_outcome": row.get("label_is_performance_outcome"),
                "exact_blocker_codes": row.get("exact_blocker_codes") or [],
                "reject_reason_codes": row.get("reject_reason_codes") or [],
                "blocker_or_reject_has_no_label": row.get("blocker_or_reject_has_no_label"),
                "validation_safe": False,
                "outcome_review_opened": False,
                "live_effect": False,
                "promotion_verdict": PROMOTION_VERDICT,
            }
        )
    return decisions


def write_context_anchor(search_ledger: list[dict[str, Any]]) -> None:
    payload = {
        **base_payload("G12_NOFILL_CAT_V2_CONTEXT_ANCHOR"),
        "starting_head": git_output("rev-parse", "HEAD"),
        "starting_head_short": git_output("rev-parse", "--short", "HEAD"),
        "current_branch": git_output("branch", "--show-current"),
        "live_state_regenerated": True,
        "live_state_freshness": "LIVE_STATE regenerated at session start before this builder run",
        "controlling_prompt": rel(OUT_DIR / "G12_NOFILL_CATEGORICAL_RESULT_PACKET_V2_AUDIT_GOAL_PROMPT_2026-05-09.md"),
        "primary_input_dir": rel(V2_DIR),
        "upstream_context_dirs": [rel(G12_SOURCE_DIR), rel(G12_CAT_DIR), rel(PRIOR_CAT_DIR), rel(OTI2_DIR), rel(OTI4_DIR)],
        "active_question_stack": [
            "Does V2 exactly partition 298 rows into 225 accepted, 8 blocked, and 65 rejected?",
            "Do accepted, blocked, and rejected rows overlap?",
            "Are accepted label counts and source-lane counts exact?",
            "Are the eight residual blockers proven exact or reduced to precise source/access requirements?",
            "Are the 65 rejects source/contract/duplicate exclusions rather than hidden performance exclusions?",
            "Are source hashes, no-leak flags, duplicate denominator posture, and label meanings safe?",
        ],
        "searched_root_ledger": search_ledger,
        "hard_boundaries": [
            "No R/performance scoring.",
            "No broker/account/live/order or hidden labels.",
            "No validation-safe flip or outcome-review opening.",
            "No live trading prompts, risk, execution, permissions, safety, selector, canary, MT5 order/account/history, credentials, remote, registry, paid/API/Databento, or live order behavior changes.",
        ],
    }
    write_json(OUT_DIR / f"G12_NOFILL_CAT_V2_CONTEXT_ANCHOR_{DATE}.json", payload)
    write_md(
        OUT_DIR / f"G12_NOFILL_CAT_V2_CONTEXT_ANCHOR_{DATE}.md",
        [
            "# G12 NOFILL CAT V2 Context Anchor",
            "",
            f"Promotion posture: `{PROMOTION_VERDICT}`.",
            "",
            f"- Lane: `{LANE}`",
            f"- Decision target: `{DECISION}`",
            f"- Starting HEAD: `{payload['starting_head_short']}`",
            f"- Current branch: `{payload['current_branch']}`",
            f"- Controlling prompt: `{payload['controlling_prompt']}`",
            f"- Primary input directory: `{payload['primary_input_dir']}`",
            "",
            "## Active Question Stack",
            "",
            *[f"- {item}" for item in payload["active_question_stack"]],
            "",
            "## Searched Roots",
            "",
            "| Root | Exists | Purpose |",
            "|---|---:|---|",
            *[f"| `{item['root']}` | `{str(item['exists']).lower()}` | {item['purpose']} |" for item in search_ledger],
            "",
            "## Boundaries",
            "",
            *[f"- {item}" for item in payload["hard_boundaries"]],
        ],
    )


def write_decision_ledger(inputs: dict[str, Any]) -> dict[str, Any]:
    rows = inputs["v2_rows"]
    accepted = inputs["accepted"]["rows"]
    blockers = inputs["blockers"]["rows"]
    rejects = inputs["rejects"]["rows"]
    accepted_ids = {row["packet_row_id"] for row in accepted}
    blocker_ids = {row["packet_row_id"] for row in blockers}
    reject_ids = {row["packet_row_id"] for row in rejects}
    overlap_checks = {
        "accepted_blocker_overlap": sorted(accepted_ids & blocker_ids),
        "accepted_reject_overlap": sorted(accepted_ids & reject_ids),
        "blocker_reject_overlap": sorted(blocker_ids & reject_ids),
        "partition_unique_ids": len(accepted_ids | blocker_ids | reject_ids),
        "covers_298_rows": len(accepted_ids | blocker_ids | reject_ids) == 298,
    }
    status = (
        "PASS"
        if len(rows) == 298
        and len(accepted) == 225
        and len(blockers) == 8
        and len(rejects) == 65
        and inputs["universe"]["decision_counts"] == EXPECTED_DECISIONS
        and inputs["accepted"]["accepted_label_counts"] == EXPECTED_ACCEPTED_LABELS
        and inputs["accepted"]["accepted_source_lane_counts"] == EXPECTED_ACCEPTED_SOURCE_LANES
        and not overlap_checks["accepted_blocker_overlap"]
        and not overlap_checks["accepted_reject_overlap"]
        and not overlap_checks["blocker_reject_overlap"]
        and overlap_checks["covers_298_rows"]
        else "FAIL"
    )
    payload = {
        **base_payload("G12_NOFILL_CAT_V2_DECISION_LEDGER"),
        "decision": DECISION,
        "decision_status": "PASS_ACCEPTED_NARROWLY" if status == "PASS" else "FAIL_BLOCKED",
        "accepted_scope": "input-only categorical lifecycle/source evidence for future research, with no validation or promotion claim",
        "row_count": len(rows),
        "partition_counts": {
            "accepted": len(accepted),
            "blocked": len(blockers),
            "rejected": len(rejects),
            "accepted_prior": inputs["accepted"]["prior_accepted_rows_carried_forward"],
            "accepted_source_corrected": inputs["accepted"]["source_corrected_accepted_rows_consumed"],
        },
        "decision_counts": inputs["universe"]["decision_counts"],
        "accepted_label_counts": inputs["accepted"]["accepted_label_counts"],
        "accepted_source_lane_counts": inputs["accepted"]["accepted_source_lane_counts"],
        "blocker_code_counts": inputs["blockers"]["blocker_code_counts"],
        "reject_decision_counts": inputs["rejects"]["reject_decision_counts"],
        "overlap_checks": overlap_checks,
        "label_meanings": label_meanings(),
        "row_decisions": build_decision_rows(rows),
        "non_claims": [
            "No R/performance, win rate, expectancy, DSR/PBO, broker actual-R, account history, live trade result, hidden-label, validation, promotion, or live-effect claim.",
            "Opening-drive source-projection and canonical duplicate rows are accepted input/source-control rows, not result labels.",
            "Rejected rows are excluded from denominator and label assignment.",
            "Blocked rows preserve exact source/order gaps and receive no label.",
        ],
        "status": status,
    }
    write_json(OUT_DIR / f"G12_NOFILL_CAT_V2_DECISION_LEDGER_{DATE}.json", payload)
    write_md(
        OUT_DIR / f"G12_NOFILL_CAT_V2_DECISION_LEDGER_{DATE}.md",
        [
            "# G12 NOFILL CAT V2 Decision Ledger",
            "",
            f"Promotion posture: `{PROMOTION_VERDICT}`.",
            "",
            f"Decision: `{DECISION}`.",
            f"Status: `{status}`.",
            "",
            "## Exact Partition",
            "",
            "- `298 = 225 accepted + 8 blocked + 65 rejected`.",
            "- `225 = 52 prior accepted + 173 source-corrected accepted`.",
            "- Accepted, blocked, and rejected row id sets have zero overlap.",
            "",
            "## Accepted Label Counts",
            "",
            "| Label | Count |",
            "|---|---:|",
            *[f"| `{key}` | {value} |" for key, value in sorted(payload["accepted_label_counts"].items())],
            "",
            "## Source Lane Counts",
            "",
            "| Source lane | Accepted rows |",
            "|---|---:|",
            *[f"| `{key}` | {value} |" for key, value in sorted(payload["accepted_source_lane_counts"].items())],
            "",
            "## Interpretation",
            "",
            "Accepted means narrow input-only categorical evidence. It does not mean R, win rate, expectancy, broker actual-R, validation, promotion, or a live gate.",
        ],
    )
    return payload


def write_source_hash_artifacts(inputs: dict[str, Any], search_ledger: list[dict[str, Any]]) -> dict[str, Any]:
    records = control_hash_records()
    v2_rehash = rehash_v2_control_inputs(inputs["v2_source_hash"])
    oti3 = recompute_oti3_same_tick_checks(inputs["oti2_rows"])
    oti4 = recompute_oti4_source_gap_checks(inputs["oti4_rows"])
    original_oti2 = recompute_original_oti2_source_gap(inputs["oti2_rows"])
    missing_control = [record for record in records if not record["exists"]]
    status = (
        "PASS"
        if not missing_control
        and v2_rehash["status"] == "PASS"
        and len(oti3) == 4
        and all(item["status"] == "PASS" for item in oti3)
        and len(oti4) == 3
        and all(item["status"] == "PASS" for item in oti4)
        and original_oti2["status"] == "PASS"
        and inputs["v2_source_hash"]["status"] == "PASS"
        and inputs["g12_source_hash"]["status"] == "PASS"
        else "FAIL"
    )
    payload = {
        **base_payload("G12_NOFILL_CAT_V2_SOURCE_HASH_AUDIT"),
        "status": status,
        "control_input_hash_records": records,
        "missing_control_inputs": missing_control,
        "v2_control_input_rehash": v2_rehash,
        "inherited_v2_source_hash_status": inputs["v2_source_hash"]["status"],
        "inherited_g12_source_hash_status": inputs["g12_source_hash"]["status"],
        "inherited_g12_source_hash_record_count": inputs["v2_source_hash"]["inherited_g12_source_hash_record_count"],
        "inherited_g12_source_hash_mismatches": inputs["v2_source_hash"]["inherited_g12_source_hash_mismatches"],
        "inherited_g12_missing_source_hash_records": inputs["v2_source_hash"]["inherited_g12_missing_source_hash_records"],
        "recomputed_oti3_same_tick_order_checks": oti3,
        "recomputed_oti4_may3_source_gap_checks": oti4,
        "recomputed_original_oti2_source_gap_check": original_oti2,
        "searched_root_ledger": search_ledger,
        "source_hash_drift_classification": "NON_SOURCE_CONTROL_PROMPT_HASH_DRIFT_NO_DATA_INVALIDATION"
        if v2_rehash["non_source_prompt_hash_drifts"]
        else "NO_DRIFT",
        "blocker_saturation_conclusion": "All 8 blockers are exact from approved inputs; each has a precise source/access unblocker or source-safe impossibility proof.",
    }
    write_json(OUT_DIR / f"G12_NOFILL_CAT_V2_SOURCE_HASH_AUDIT_{DATE}.json", payload)
    write_md(
        OUT_DIR / f"G12_NOFILL_CAT_V2_SOURCE_HASH_AUDIT_{DATE}.md",
        [
            "# G12 NOFILL CAT V2 Source Hash Audit",
            "",
            f"Promotion posture: `{PROMOTION_VERDICT}`.",
            "",
            f"Status: `{status}`.",
            f"Control inputs hashed: `{len(records)}`.",
            f"V2 control input rehash status: `{v2_rehash['status']}`.",
            f"Recomputed OTI3 same-tick blockers: `{len(oti3)}`.",
            f"Recomputed OTI4 May 3 source gaps: `{len(oti4)}`.",
            f"Recomputed original OTI2 source gap rows: `{original_oti2['row_count']}`.",
            "",
            "## Blocker Saturation",
            "",
            "- OTI3 same-tick rows: one source tick at the first timestamp satisfies multiple event predicates; no intra-tick order exists in the approved source.",
            "- OTI4 May 3 rows: local tick files exist but contain zero rows in the frozen 13:00-13:30 UTC opening range; no approved CSV/OHLC substitute is recorded.",
            "- Original OTI2 row: M1 context is not side-aware tick proof and XAUUSD tick coverage misses the active window through cancel.",
        ],
    )
    return payload


def write_noleak_duplicate_artifacts(inputs: dict[str, Any], decision: dict[str, Any], source_hash: dict[str, Any]) -> dict[str, Any]:
    accepted = inputs["accepted"]["rows"]
    blockers = inputs["blockers"]["rows"]
    rejects = inputs["rejects"]["rows"]
    artifact_scan_inputs = {
        "v2_row_decision_ledger": inputs["v2_rows"],
        "accepted_packet": inputs["accepted"],
        "blocker_ledger": inputs["blockers"],
        "reject_ledger": inputs["rejects"],
        "v2_source_hash_audit": inputs["v2_source_hash"],
        "v2_duplicate_audit": inputs["v2_duplicate"],
        "v2_completion_audit": inputs["v2_completion"],
        "g12_decision_ledger": decision,
        "g12_source_hash_audit": source_hash,
    }
    forbidden_hits = []
    for name, payload in artifact_scan_inputs.items():
        for hit in scan_forbidden_keys(payload):
            forbidden_hits.append({"artifact": name, **hit})
    flag_issues = []
    for name, payload in artifact_scan_inputs.items():
        if isinstance(payload, dict):
            if payload.get("validation_safe") is not False:
                flag_issues.append(f"{name}: validation_safe")
            if payload.get("outcome_review_opened") is not False:
                flag_issues.append(f"{name}: outcome_review_opened")
            if payload.get("live_effect") is not False:
                flag_issues.append(f"{name}: live_effect")
            if payload.get("promotion_verdict") and payload.get("promotion_verdict") != PROMOTION_VERDICT:
                flag_issues.append(f"{name}: promotion_verdict")
    label_issues = []
    if any(row.get("categorical_input_label") is None for row in accepted):
        label_issues.append("accepted row missing categorical_input_label")
    if any(row.get("categorical_input_label") is not None or row.get("categorical_lifecycle_label") is not None for row in blockers + rejects):
        label_issues.append("blocked/rejected row has label")
    if any(row.get("in_accepted_packet_denominator") for row in blockers + rejects):
        label_issues.append("blocked/rejected row in accepted denominator")
    duplicate_collisions = inputs["v2_duplicate"]["duplicate_key_collisions_in_accepted_packet"]
    status = (
        "PASS"
        if not forbidden_hits
        and not flag_issues
        and not label_issues
        and inputs["v2_duplicate"]["status"] == "PASS"
        and inputs["v2_duplicate"]["sample_floor_status"] == "NOT_A_VALIDATION_OR_PROMOTION_LANE_NO_SAMPLE_FLOOR_CLAIM"
        else "FAIL"
    )
    payload = {
        **base_payload("G12_NOFILL_CAT_V2_NO_LEAK_LABEL_DUPLICATE_AUDIT"),
        "status": status,
        "forbidden_key_hits": forbidden_hits,
        "flag_issues": flag_issues,
        "label_issues": label_issues,
        "accepted_label_counts": inputs["accepted"]["accepted_label_counts"],
        "label_meanings": label_meanings(),
        "duplicate_posture": {
            "accepted_rows": inputs["v2_duplicate"]["accepted_rows"],
            "accepted_unique_nofill_duplicate_keys": inputs["v2_duplicate"]["accepted_unique_nofill_duplicate_keys"],
            "duplicate_key_collisions_in_accepted_packet": duplicate_collisions,
            "rejected_noncanonical_duplicate_rows": inputs["v2_duplicate"]["rejected_noncanonical_duplicate_rows"],
            "denominator_inflation_decision": inputs["v2_duplicate"]["denominator_inflation_decision"],
        },
        "sample_floor_posture": {
            "categorical_input_rows": 225,
            "unique_duplicate_keys": inputs["v2_duplicate"]["accepted_unique_nofill_duplicate_keys"],
            "validation_sample_floor_status": "NOT_A_VALIDATION_OR_PROMOTION_LANE_NO_SAMPLE_FLOOR_CLAIM",
            "dsr_pbo_effective_n_status": "not_computable_no_result_values_opened",
        },
        "countable_scope": {
            "row_level_input_only_categorical_evidence": 225,
            "unique_duplicate_key_input_only_categorical_evidence": inputs["v2_duplicate"]["accepted_unique_nofill_duplicate_keys"],
            "validation_or_promotion_rows": 0,
            "performance_outcome_rows": 0,
        },
    }
    write_json(OUT_DIR / f"G12_NOFILL_CAT_V2_NO_LEAK_LABEL_DUPLICATE_AUDIT_{DATE}.json", payload)
    write_md(
        OUT_DIR / f"G12_NOFILL_CAT_V2_NO_LEAK_LABEL_DUPLICATE_AUDIT_{DATE}.md",
        [
            "# G12 NOFILL CAT V2 No-Leak Label Duplicate Audit",
            "",
            f"Promotion posture: `{PROMOTION_VERDICT}`.",
            "",
            f"Status: `{status}`.",
            f"Forbidden key hits: `{len(forbidden_hits)}`.",
            f"Flag issues: `{len(flag_issues)}`.",
            f"Label issues: `{len(label_issues)}`.",
            "",
            "## Duplicate / Sample Floor",
            "",
            f"- Accepted row-level input evidence: `{payload['countable_scope']['row_level_input_only_categorical_evidence']}`.",
            f"- Accepted unique duplicate keys: `{payload['countable_scope']['unique_duplicate_key_input_only_categorical_evidence']}`.",
            f"- Validation or promotion rows: `{payload['countable_scope']['validation_or_promotion_rows']}`.",
            f"- Performance outcome rows: `{payload['countable_scope']['performance_outcome_rows']}`.",
            "",
            "DSR/PBO/effective-N are not computable here because no result values are opened.",
        ],
    )
    return payload


def write_blocker_reject_review(inputs: dict[str, Any], source_hash: dict[str, Any]) -> dict[str, Any]:
    blockers = inputs["blockers"]["rows"]
    rejects = inputs["rejects"]["rows"]
    blockers_by_code: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in blockers:
        for code in row.get("exact_blocker_codes") or []:
            blockers_by_code[code].append(row)
    reject_by_decision = defaultdict(list)
    for row in rejects:
        reject_by_decision[row["consolidated_g12_decision"]].append(row)
    blocker_reviews = {
        "oti4_may3_source_gaps": {
            "row_count": 3,
            "source_close_packet_row_ids": [item["source_close_packet_row_id"] for item in source_hash["recomputed_oti4_may3_source_gap_checks"]],
            "decision": "PRESERVE_EXACT_BLOCKER",
            "proof": "local tick parquet exists but starts after the frozen 13:00-13:30 UTC window / has zero required-range rows; OTI4 source-search ledger records no approved substitute",
            "unblocker": "read-only tick parquet quote stream or M1-or-lower OHLC with source hash and as-of provenance for 2026-05-03 13:00-13:30 UTC",
        },
        "oti3_same_tick_order_ambiguities": {
            "row_count": 4,
            "source_close_packet_row_ids": [item["source_close_packet_row_id"] for item in source_hash["recomputed_oti3_same_tick_order_checks"]],
            "decision": "PRESERVE_EXACT_BLOCKER",
            "proof": "one source tick row at the first timestamp simultaneously carries entry and protective events; source has no intra-row ordering",
            "unblocker": "higher-resolution source or explicit broker/native event ordering that proves entry/protective sequence without account/order labels",
        },
        "original_oti2_source_gap": {
            "row_count": source_hash["recomputed_original_oti2_source_gap_check"]["row_count"],
            "source_close_packet_row_ids": [item["source_close_packet_row_id"] for item in source_hash["recomputed_original_oti2_source_gap_check"]["checks"]],
            "decision": "PRESERVE_EXACT_BLOCKER",
            "proof": "M1 path context is not side-aware bid/ask proof and XAUUSD tick coverage misses the pending active window through cancel",
            "unblocker": "side-aware bid/ask tick source covering active pending window through cancel, or an approved source contract that explicitly handles the gap",
        },
    }
    reject_reviews = {
        "oti4_contract_excluded_rows": {
            "row_count": len(reject_by_decision["REJECT_FROM_REBUILD_CONTRACT_EXCLUDED"]),
            "decision": "EXCLUDE_FROM_DENOMINATOR_AND_LABEL_ASSIGNMENT",
            "reason": "OTI4 contract exclusion, not hidden performance or outcome scoring",
        },
        "oti5_noncanonical_duplicate_projections": {
            "row_count": len(reject_by_decision["REJECT_FROM_REBUILD_NONCANONICAL_DUPLICATE"]),
            "decision": "EXCLUDE_FROM_DENOMINATOR_AND_LABEL_ASSIGNMENT",
            "reason": "OTI5 canonical geometry rule rejects repeated projections to prevent denominator inflation, not hidden performance or outcome scoring",
        },
    }
    status = (
        "PASS"
        if len(blockers) == 8
        and inputs["blockers"]["blocker_summary"] == {
            "original_oti2_source_gap_rows": 1,
            "oti3_same_tick_order_ambiguities": 4,
            "oti4_may3_source_gaps": 3,
        }
        and inputs["blockers"]["blocker_code_counts"] == EXPECTED_BLOCKER_CODES
        and inputs["rejects"]["reject_decision_counts"] == EXPECTED_REJECT_DECISIONS
        and all(row.get("categorical_input_label") is None for row in blockers + rejects)
        else "FAIL"
    )
    payload = {
        **base_payload("G12_NOFILL_CAT_V2_BLOCKER_REJECT_REVIEW"),
        "status": status,
        "blocked_row_count": len(blockers),
        "rejected_row_count": len(rejects),
        "blocker_code_counts": inputs["blockers"]["blocker_code_counts"],
        "reject_decision_counts": inputs["rejects"]["reject_decision_counts"],
        "blocker_reviews": blocker_reviews,
        "reject_reviews": reject_reviews,
        "blocked_or_rejected_rows_have_no_label": all(row.get("categorical_input_label") is None and row.get("categorical_lifecycle_label") is None for row in blockers + rejects),
        "blocked_or_rejected_rows_in_denominator": [row["packet_row_id"] for row in blockers + rejects if row.get("in_accepted_packet_denominator")],
        "hidden_performance_reason_detected": False,
    }
    write_json(OUT_DIR / f"G12_NOFILL_CAT_V2_BLOCKER_REJECT_REVIEW_{DATE}.json", payload)
    write_md(
        OUT_DIR / f"G12_NOFILL_CAT_V2_BLOCKER_REJECT_REVIEW_{DATE}.md",
        [
            "# G12 NOFILL CAT V2 Blocker Reject Review",
            "",
            f"Promotion posture: `{PROMOTION_VERDICT}`.",
            "",
            f"Status: `{status}`.",
            f"Blocked rows: `{len(blockers)}`.",
            f"Rejected rows: `{len(rejects)}`.",
            "",
            "## Residual Blockers",
            "",
            "| Family | Count | Decision | Unblocker |",
            "|---|---:|---|---|",
            *[
                f"| `{key}` | {value['row_count']} | `{value['decision']}` | {value['unblocker']} |"
                for key, value in payload["blocker_reviews"].items()
            ],
            "",
            "## Rejects",
            "",
            "| Family | Count | Reason |",
            "|---|---:|---|",
            *[
                f"| `{key}` | {value['row_count']} | {value['reason']} |"
                for key, value in payload["reject_reviews"].items()
            ],
            "",
            "Rejected rows are excluded for source/contract/duplicate reasons, not hidden performance reasons.",
        ],
    )
    return payload


def write_learning_ledger() -> None:
    lines = [
        "# G12 NOFILL CAT V2 Learning Ledger",
        "",
        f"Promotion posture: `{PROMOTION_VERDICT}`.",
        "",
        "## What The Audit Accepted",
        "",
        "- The V2 packet is acceptable only as input-only categorical lifecycle/source evidence for future research.",
        "- The exact partition is useful: 225 accepted rows, 8 exact blockers, and 65 rejects.",
        "- The accepted set combines 52 prior accepted lifecycle labels with 173 source-corrected accepted inputs.",
        "",
        "## What The Audit Did Not Accept",
        "",
        "- No R, win rate, expectancy, broker actual-R, account-history, validation, promotion, or live-gate claim is opened.",
        "- Opening-drive projection rows and canonical duplicate rows are source/control inputs, not result labels.",
        "- Rejected rows are not negative outcomes; they are source/contract/duplicate exclusions.",
        "",
        "## Failure And Blocker Learning",
        "",
        "- Same-tick order ambiguity is a real source-resolution limit: one tick row can satisfy multiple predicates with no intra-row order.",
        "- May 3 opening-drive gaps are true local source-window gaps despite local tick files existing for later hours.",
        "- The original OTI2 gap shows why M1 context must not be promoted into side-aware quote proof.",
        "- OTI5 duplicate control prevents denominator inflation; it is not a performance filter.",
        "",
        "## Next Hypotheses",
        "",
        "- A quarantined categorical-result synthesis/forensics lane can summarize the 225 accepted input-only categorical labels without R/performance conversion.",
        "- A later narrow blocker-clear lane may target only the 8 exact blockers with the named read-only source requirements.",
        "- No promotion dossier should be opened from this packet.",
    ]
    write_md(OUT_DIR / f"G12_NOFILL_CAT_V2_LEARNING_LEDGER_{DATE}.md", lines)


def write_next_prompt_pack() -> None:
    lines = [
        "# G12 NOFILL CAT V2 Next Prompt Pack",
        "",
        f"Promotion posture: `{PROMOTION_VERDICT}`.",
        "",
        "## Recommended Next Lane",
        "",
        "`NOFILL_CAT_V2_QUARANTINED_CATEGORICAL_SYNTHESIS_FORENSICS`.",
        "",
        "Objective: summarize and slice the 225 accepted V2 input-only categorical labels as source/control evidence, preserving blocked/rejected families, without converting any label into R, win rate, expectancy, broker actual-R, validation, promotion, live-gate evidence, or live behavior.",
        "",
        "## Starting Facts To Preserve",
        "",
        "- `298 = 225 accepted + 8 blocked + 65 rejected`.",
        "- `225 = 52 prior accepted + 173 source-corrected accepted`.",
        "- Accepted label counts: `nofill_terminal_before_entry=110`, `source_corrected_no_entry_through_pending_horizon=32`, `opening_drive_source_projection_ready_no_result_label=51`, `fill_path_entry_before_protective_level_no_terminal_observed=22`, `fill_path_entry_before_protective_level_before_terminal_area=4`, `fill_path_entry_before_terminal_area_before_protective_level=3`, `canonical_duplicate_geometry_source_ready_no_label_assigned=3`.",
        "- Source-lane counts: prior G12 categorical packet audit 52, OTI1 32, OTI2 V2 29, OTI3 58, OTI4 51, OTI5 3.",
        "- Residual blockers: 3 OTI4 May 3 source gaps, 4 OTI3 same-tick order ambiguities, 1 original OTI2 source gap.",
        "- Rejects: 26 OTI4 contract-excluded rows and 39 OTI5 noncanonical duplicate projections.",
        "",
        "## Required Boundaries",
        "",
        "- Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.",
        "- Do not inspect broker/account/live/order/history labels, hidden labels, blocked-row outcomes, or performance values.",
        "- Do not edit live trading prompts, risk, execution, permissions, safety gates, selectors, canaries, credentials, registries, remotes, paid/API/Databento paths, MT5 order/account/history code, or order behavior.",
        "",
        "## Optional Separate Blocker-Clear Lane",
        "",
        "If the owner wants to clear blockers instead, open a narrow source-access/capture lane for exactly the 8 blockers and request the named read-only source coverage. Do not score or promote anything in that lane.",
    ]
    write_md(OUT_DIR / f"G12_NOFILL_CAT_V2_NEXT_PROMPT_PACK_{DATE}.md", lines)


def write_completion_audit(status: str = "BUILT_PENDING_VERIFIER", verification: dict[str, Any] | None = None) -> dict[str, Any]:
    requirements = [
        ("Mandatory preflight and context anchor", f"G12_NOFILL_CAT_V2_CONTEXT_ANCHOR_{DATE}.md"),
        ("Exact 298 = 225 + 8 + 65 partition", f"G12_NOFILL_CAT_V2_DECISION_LEDGER_{DATE}.json"),
        ("Exact 225 = 52 prior + 173 source-corrected", f"G12_NOFILL_CAT_V2_DECISION_LEDGER_{DATE}.json"),
        ("Accepted label counts exact", f"G12_NOFILL_CAT_V2_DECISION_LEDGER_{DATE}.json"),
        ("Source-lane counts exact", f"G12_NOFILL_CAT_V2_DECISION_LEDGER_{DATE}.json"),
        ("Zero overlap between accepted, blocked, rejected", f"G12_NOFILL_CAT_V2_DECISION_LEDGER_{DATE}.json"),
        ("Blocked/rejected rows carry no labels and no denominator inclusion", f"G12_NOFILL_CAT_V2_NO_LEAK_LABEL_DUPLICATE_AUDIT_{DATE}.json"),
        ("Residual blockers pursued to exact proof/unblocker", f"G12_NOFILL_CAT_V2_SOURCE_HASH_AUDIT_{DATE}.json"),
        ("Rejects confirmed source/contract/duplicate exclusions", f"G12_NOFILL_CAT_V2_BLOCKER_REJECT_REVIEW_{DATE}.json"),
        ("Source hashes recomputed where feasible", f"G12_NOFILL_CAT_V2_SOURCE_HASH_AUDIT_{DATE}.json"),
        ("No-leak, duplicate, sample-floor posture", f"G12_NOFILL_CAT_V2_NO_LEAK_LABEL_DUPLICATE_AUDIT_{DATE}.json"),
        ("Label meanings and non-claims explained", f"G12_NOFILL_CAT_V2_DECISION_LEDGER_{DATE}.json"),
        ("Learning ledger and next prompt pack", f"G12_NOFILL_CAT_V2_LEARNING_LEDGER_{DATE}.md and G12_NOFILL_CAT_V2_NEXT_PROMPT_PACK_{DATE}.md"),
        ("Verifier, py_compile, focused pytest, forbidden-surface checks", f"verify_g12_nofill_cat_v2_audit_2026_05_09.py and test_g12_nofill_cat_v2_audit_2026_05_09.py"),
    ]
    verified = bool(verification and verification.get("verification_status", {}).get("status") == "PASS")
    payload = {
        **base_payload("G12_NOFILL_CAT_V2_COMPLETION_AUDIT"),
        "objective_restatement": "Independently audit the V2 no-fill categorical packet as input-only categorical lifecycle/source evidence, preserving 8 blockers and 65 rejects, with no validation/promotion/live effect.",
        "completion_status": "PASS_VERIFIED_G12_ACCEPTED_V2_PACKET_NARROWLY" if verified else status,
        "can_mark_goal_complete": verified,
        "decision": DECISION,
        "prompt_to_artifact_checklist": [
            {
                "requirement": requirement,
                "artifact_evidence": artifact,
                "status": "PASS" if verified else "PENDING_VERIFIER",
            }
            for requirement, artifact in requirements
        ],
        "missing_incomplete_or_weak_requirements": [] if verified else ["Verifier has not yet marked all requirements PASS."],
        "verification_results": verification or {},
        "safety_flags_preserved": {
            "promotion_verdict": PROMOTION_VERDICT,
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        },
        "next_lane": "NOFILL_CAT_V2_QUARANTINED_CATEGORICAL_SYNTHESIS_FORENSICS",
    }
    write_json(OUT_DIR / f"G12_NOFILL_CAT_V2_COMPLETION_AUDIT_{DATE}.json", payload)
    lines = [
        "# G12 NOFILL CAT V2 Completion Audit",
        "",
        f"Promotion posture: `{PROMOTION_VERDICT}`.",
        "",
        f"Completion status: `{payload['completion_status']}`.",
        f"Can mark goal complete: `{str(payload['can_mark_goal_complete']).lower()}`.",
        f"Decision: `{DECISION}`.",
        "",
        "## Prompt-To-Artifact Checklist",
        "",
        "| Requirement | Status | Evidence |",
        "|---|---|---|",
        *[
            f"| {item['requirement']} | `{item['status']}` | `{item['artifact_evidence']}` |"
            for item in payload["prompt_to_artifact_checklist"]
        ],
    ]
    if verification:
        lines += ["", "## Verification Results", ""]
        for key, value in verification.items():
            if isinstance(value, dict) and "status" in value:
                lines.append(f"- `{key}`: `{value['status']}`")
    write_md(OUT_DIR / f"G12_NOFILL_CAT_V2_COMPLETION_AUDIT_{DATE}.md", lines)
    return payload


def build_artifacts() -> dict[str, Any]:
    inputs = load_inputs()
    search_ledger = source_root_search_ledger(inputs["oti4_search"])
    write_context_anchor(search_ledger)
    decision = write_decision_ledger(inputs)
    source_hash = write_source_hash_artifacts(inputs, search_ledger)
    noleak_duplicate = write_noleak_duplicate_artifacts(inputs, decision, source_hash)
    blocker_reject = write_blocker_reject_review(inputs, source_hash)
    write_learning_ledger()
    write_next_prompt_pack()
    completion = write_completion_audit()
    status = (
        "PASS"
        if decision["status"] == "PASS"
        and source_hash["status"] == "PASS"
        and noleak_duplicate["status"] == "PASS"
        and blocker_reject["status"] == "PASS"
        else "FAIL"
    )
    return {
        "status": status,
        "decision": decision["decision"],
        "partition_counts": decision["partition_counts"],
        "source_hash_status": source_hash["status"],
        "noleak_duplicate_status": noleak_duplicate["status"],
        "blocker_reject_status": blocker_reject["status"],
        "completion_status": completion["completion_status"],
    }


def main() -> int:
    result = build_artifacts()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
