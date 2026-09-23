from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
SOURCE_REPAIR_PLAN_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_EXECUTION_PLAN_LEDGER_{DATE}.jsonl"
SOURCE_REPAIR_PROOF_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_PROOF_LEDGER_{DATE}.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_LOCAL_FIELD_AVAILABILITY_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_LOCAL_FIELD_AVAILABILITY_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_LOCAL_FIELD_AVAILABILITY_MANIFEST_{DATE}.json"

LOCAL_SOURCE_ROOTS = [
    Path("shadow_logs"),
    Path("knowledge_base/index"),
    Path("knowledge_base/trade_records"),
    Path("research/live_intelligence"),
]
LOCAL_SOURCE_SUFFIXES = {".json", ".jsonl"}
REPAIR_ACTION_REQUIRED_SOURCE_CLASS = {
    "join_or_reconstruct_broker_execution_geometry_fields": "broker_execution_geometry_fields",
    "acquire_or_rebuild_missing_source_join_before_exact_r": "source_join_keys_or_original_packet_rows",
    "attach_broker_execution_geometry_to_exact_spread_proxy": "broker_spread_or_quote_geometry_fields",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_lines(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def discover_local_source_candidates() -> list[Path]:
    candidates: set[Path] = set()
    for root in LOCAL_SOURCE_ROOTS:
        abs_root = REPO / root
        if not abs_root.exists():
            continue
        for path in abs_root.rglob("*"):
            if path.is_file() and path.suffix.lower() in LOCAL_SOURCE_SUFFIXES:
                candidates.add(path.relative_to(REPO))
    return sorted(candidates, key=lambda path: str(path).replace("\\", "/"))


def nested_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            keys.add(str(key))
            keys.update(nested_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.update(nested_keys(item))
    return keys


def scan_json_path_for_fields(path: Path, fields: set[str]) -> tuple[int, int, Counter[str]]:
    records_scanned = 0
    parse_errors = 0
    field_rows: Counter[str] = Counter()
    if path.suffix == ".jsonl":
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    parse_errors += 1
                    continue
                records_scanned += 1
                for field in fields & nested_keys(payload):
                    field_rows[field] += 1
        return records_scanned, parse_errors, field_rows
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        records_scanned = 1
        for field in fields & nested_keys(payload):
            field_rows[field] += 1
        return records_scanned, parse_errors, field_rows
    except json.JSONDecodeError:
        return records_scanned, 1, field_rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def run_git_in_repo(*args: str) -> dict[str, Any]:
    result = subprocess.run(["git", *args], cwd=REPO, text=True, capture_output=True, check=False)
    return {
        "args": ["git", *args],
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def build() -> dict[str, Any]:
    plan_rows = read_jsonl(SOURCE_REPAIR_PLAN_LEDGER)
    proof_rows = read_jsonl(SOURCE_REPAIR_PROOF_LEDGER)
    missing_field_counts: Counter[str] = Counter()
    missing_field_plan_counts: Counter[str] = Counter()
    repair_action_counts: defaultdict[str, Counter[str]] = defaultdict(Counter)
    source_repair_decision_counts: defaultdict[str, Counter[str]] = defaultdict(Counter)
    source_repair_execution_status_counts: defaultdict[str, Counter[str]] = defaultdict(Counter)
    required_source_class_counts: defaultdict[str, Counter[str]] = defaultdict(Counter)
    symbol_counts: defaultdict[str, Counter[str]] = defaultdict(Counter)
    proof_fields_by_line_no: dict[int, set[str]] = {}
    for line_no, row in enumerate(proof_rows, start=1):
        source_row = row.get("source_row") if isinstance(row.get("source_row"), dict) else {}
        repair_action = str(source_row.get("repair_action") or row.get("repair_action") or "")
        source_repair_decision = str(source_row.get("source_repair_system_decision") or "")
        source_repair_execution_status = str(source_row.get("source_repair_execution_status") or "")
        required_source_class = REPAIR_ACTION_REQUIRED_SOURCE_CLASS.get(repair_action, "unknown_source_class")
        symbol = str(source_row.get("symbol") or "")
        line_fields: set[str] = set()
        for field in source_row.get("exact_missing_field_proof") or []:
            field = str(field)
            missing_field_counts[field] += 1
            line_fields.add(field)
            repair_action_counts[field][repair_action] += 1
            source_repair_decision_counts[field][source_repair_decision] += 1
            source_repair_execution_status_counts[field][source_repair_execution_status] += 1
            required_source_class_counts[field][required_source_class] += 1
            symbol_counts[field][symbol] += 1
        proof_fields_by_line_no[line_no] = line_fields

    for plan in plan_rows:
        plan_fields: set[str] = set()
        for locator in plan.get("source_locator_refs") or []:
            first_line = int(locator.get("first_line") or 0)
            last_line = int(locator.get("last_line") or 0)
            for line_no in range(first_line, last_line + 1):
                plan_fields.update(proof_fields_by_line_no.get(line_no, set()))
        for field in plan_fields:
            missing_field_plan_counts[field] += 1

    source_scan_summaries = []
    field_file_counts: defaultdict[str, Counter[str]] = defaultdict(Counter)
    field_file_source_kinds: defaultdict[str, Counter[str]] = defaultdict(Counter)
    field_row_counts: Counter[str] = Counter()
    parse_errors = 0
    records_scanned_total = 0
    local_source_candidates = discover_local_source_candidates()
    fields = set(missing_field_counts)
    for rel_path in local_source_candidates:
        path = REPO / rel_path
        if not path.exists():
            source_scan_summaries.append({"path": str(rel_path).replace("\\", "/"), "exists": False})
            continue
        records_scanned, errors, local_field_rows = scan_json_path_for_fields(path, fields)
        parse_errors += errors
        records_scanned_total += records_scanned
        source_kind = str(rel_path.parts[0]) if rel_path.parts else "unknown"
        for field, count in local_field_rows.items():
            field_row_counts[field] += int(count)
            field_file_counts[field][str(rel_path).replace("\\", "/")] = count
            field_file_source_kinds[field][source_kind] += 1
        source_scan_summaries.append(
            {
                "path": str(rel_path).replace("\\", "/"),
                "exists": True,
                "records_scanned": records_scanned,
                "parse_errors": errors,
                "sha256": sha256_path(path),
                "matched_missing_fields": dict(sorted(local_field_rows.items())),
            }
        )

    output_rows = []
    for index, (field, missing_count) in enumerate(sorted(missing_field_counts.items()), start=1):
        local_rows = int(field_row_counts.get(field, 0))
        status = (
            "CURRENT_LOCAL_FIELD_PRESENT_BUT_NOT_BOUND_TO_NUMERIC_ROUTER_ROWS"
            if local_rows
            else "NOT_PRESENT_IN_SELECTED_LOCAL_SOURCE_FILES"
        )
        output_rows.append(
            {
                "field_availability_row_id": f"MAIN-ORCH48-NUMERIC-ROUTER-SOURCE-REPAIR-FIELD-{index:04d}",
                "schema_version": "main_orch48_numeric_router_source_repair_local_field_availability_v1",
                "missing_field": field,
                "source_repair_proof_rows_missing_field": missing_count,
                "source_repair_plan_rows_requiring_field": int(missing_field_plan_counts.get(field, 0)),
                "repair_action_counts": dict(sorted(repair_action_counts[field].items())),
                "source_repair_system_decision_counts": dict(sorted(source_repair_decision_counts[field].items())),
                "source_repair_execution_status_counts": dict(
                    sorted(source_repair_execution_status_counts[field].items())
                ),
                "required_source_class_counts": dict(sorted(required_source_class_counts[field].items())),
                "symbol_counts": dict(sorted(symbol_counts[field].items())),
                "local_candidate_files_scanned": len(source_scan_summaries),
                "local_rows_with_field_name": local_rows,
                "local_files_with_field_name": dict(sorted(field_file_counts[field].items())),
                "local_source_kind_file_match_counts": dict(sorted(field_file_source_kinds[field].items())),
                "local_field_availability_status": status,
                "source_operation": "read_only_local_json_key_scan",
                "field_key_scan_only": True,
                "row_identity_bound_to_numeric_router_source_repair_queue": False,
                "runtime_score_allowed": False,
                "runtime_candidate_use_permitted": False,
                "candidate_use_allowed_now": False,
                "unconditional_scalar_use_allowed": False,
                "replay_r_reference_counted_as_new_main_result": False,
            }
        )
    write_jsonl(OUTPUT_LEDGER, output_rows)

    status_counts = Counter(row["local_field_availability_status"] for row in output_rows)
    summary = {
        "route_id": "MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_LOCAL_FIELD_AVAILABILITY",
        "schema_version": "main_orch48_numeric_router_source_repair_local_field_availability_v1",
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "input_source_repair_plan_ledger": {
            "path": str(SOURCE_REPAIR_PLAN_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "rows": len(plan_rows),
            "sha256": sha256_path(SOURCE_REPAIR_PLAN_LEDGER),
        },
        "input_source_repair_proof_ledger": {
            "path": str(SOURCE_REPAIR_PROOF_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "rows": len(proof_rows),
            "sha256": sha256_path(SOURCE_REPAIR_PROOF_LEDGER),
        },
        "local_source_root_scan_policy": {
            "roots": [str(path).replace("\\", "/") for path in LOCAL_SOURCE_ROOTS],
            "suffixes": sorted(LOCAL_SOURCE_SUFFIXES),
            "operation": "read_only_json_key_scan",
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
        },
        "local_source_scan_summaries": source_scan_summaries,
        "local_source_candidate_files": len(source_scan_summaries),
        "local_source_records_scanned_total": records_scanned_total,
        "local_source_parse_errors": parse_errors,
        "rows": len(output_rows),
        "source_repair_plan_rows": len(plan_rows),
        "source_repair_proof_rows": len(proof_rows),
        "unique_missing_field_count": len(missing_field_counts),
        "local_field_availability_status_counts": dict(sorted(status_counts.items())),
        "local_fields_present_count": sum(
            row["local_field_availability_status"]
            == "CURRENT_LOCAL_FIELD_PRESENT_BUT_NOT_BOUND_TO_NUMERIC_ROUTER_ROWS"
            for row in output_rows
        ),
        "local_fields_absent_count": sum(
            row["local_field_availability_status"] == "NOT_PRESENT_IN_SELECTED_LOCAL_SOURCE_FILES"
            for row in output_rows
        ),
        "missing_field_proof_rows_total": sum(missing_field_counts.values()),
        "local_rows_with_any_missing_field_name": sum(int(row["local_rows_with_field_name"]) for row in output_rows),
        "all_field_key_scan_only_rows": sum(bool(row.get("field_key_scan_only")) for row in output_rows),
        "row_identity_bound_to_numeric_router_source_repair_queue_rows": sum(
            bool(row.get("row_identity_bound_to_numeric_router_source_repair_queue")) for row in output_rows
        ),
        "runtime_score_allowed_rows": sum(bool(row.get("runtime_score_allowed")) for row in output_rows),
        "runtime_candidate_use_permitted_rows": sum(bool(row.get("runtime_candidate_use_permitted")) for row in output_rows),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in output_rows),
        "unconditional_scalar_use_allowed_rows": sum(bool(row.get("unconditional_scalar_use_allowed")) for row in output_rows),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            bool(row.get("replay_r_reference_counted_as_new_main_result")) for row in output_rows
        ),
        "implementation_effect": {
            "runtime_or_live_effect": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
        },
        "can_continue_to_next_system_conversion_plate": True,
    }
    write_json(OUTPUT_SUMMARY, summary)

    outputs = [OUTPUT_LEDGER, OUTPUT_SUMMARY]
    manifest = {
        "route_id": summary["route_id"],
        "generated_utc": summary["generated_utc"],
        "outputs": [
            {
                "path": str(path.relative_to(REPO)).replace("\\", "/"),
                "bytes": path.stat().st_size,
                "lines": count_lines(path),
                "sha256": sha256_path(path),
            }
            for path in outputs
        ],
    }
    write_json(OUTPUT_MANIFEST, manifest)
    return {
        "ok": True,
        "route_id": summary["route_id"],
        "rows": summary["rows"],
        "unique_missing_field_count": summary["unique_missing_field_count"],
        "local_field_availability_status_counts": summary["local_field_availability_status_counts"],
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
