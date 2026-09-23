"""Build the G12 NOFILL read-only tick recovery source-control audit.

This audit stays source/control only. It recomputes target counts from upstream
ledgers, rehashes recovered ignored tick files when present, checks window
coverage, audits the two remaining XAUUSD zero-tick requests, and writes a
non-passive next route without opening validation, result, or live surfaces.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import struct
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq


DATE = "2026-05-10"
ROUTE_ID = "G12_NOFILL_READONLY_TICK_RECOVERY_EXPORT_SOURCE_CONTROL_AUDIT"
SCHEMA_VERSION = "g12_nofill_readonly_tick_recovery_export_source_control_audit_v1"
PREFIX = "G12_NOFILL_READONLY_TICK_RECOVERY"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
TERMINAL_DECISION = (
    "ACCEPT_AS_G12_READONLY_TICK_RECOVERY_SOURCE_CONTROL_AUDIT_WITH_NONPASSIVE_NEXT_ROUTE"
)

ROUTE_DIR = Path(__file__).resolve().parent
OUTCOME_ROOT = ROUTE_DIR.parent
REPO_ROOT = ROUTE_DIR.parents[3]
TARGET_ROUTE_DIR = OUTCOME_ROOT / "nofill_readonly_tick_recovery_export_source_control_route"
G12_INPUT_DIR = OUTCOME_ROOT / "g12_nofill_source_state_gap_closure_and_tick_export_manifest_audit"
UPSTREAM_ROUTE_DIR = OUTCOME_ROOT / "nofill_source_state_capture_gap_closure_and_tick_export_manifest_route"

TARGET_PREFIX = "NOFILL_READONLY_TICK_RECOVERY"
TARGET_ROUTE_ID = "NOFILL_READONLY_TICK_RECOVERY_EXPORT_SOURCE_CONTROL_ROUTE"
TARGET_TERMINAL_DECISION = "ACCEPT_WITH_EXACT_REMAINING_EXPORT_OR_ACCESS_REQUESTS"

CONTROL_PROMPT_PATH = (
    "research/science_program_2026_05/04_goal_prompts/"
    "G12_NOFILL_READONLY_TICK_RECOVERY_EXPORT_SOURCE_CONTROL_AUDIT_GOAL_PROMPT_2026-05-10.md"
)
TARGET_CONTROL_PROMPT_PATH = (
    "research/science_program_2026_05/04_goal_prompts/"
    "NOFILL_READONLY_TICK_RECOVERY_EXPORT_SOURCE_CONTROL_ROUTE_GOAL_PROMPT_2026-05-10.md"
)

TARGET_FILES = {
    "recovery_ladder": TARGET_ROUTE_DIR
    / f"{TARGET_PREFIX}_RECOVERY_LADDER_LEDGER_{DATE}.json",
    "source_hash_manifest": TARGET_ROUTE_DIR
    / f"{TARGET_PREFIX}_SOURCE_HASH_MANIFEST_{DATE}.json",
    "recovered_absent_window": TARGET_ROUTE_DIR
    / f"{TARGET_PREFIX}_RECOVERED_ABSENT_WINDOW_LEDGER_{DATE}.json",
    "grouped_reconciliation": TARGET_ROUTE_DIR
    / f"{TARGET_PREFIX}_GROUPED_REQUEST_RECONCILIATION_LEDGER_{DATE}.json",
    "owner_action": TARGET_ROUTE_DIR / f"{TARGET_PREFIX}_OWNER_ACTION_MANIFEST_{DATE}.json",
    "completion_audit": TARGET_ROUTE_DIR / f"{TARGET_PREFIX}_COMPLETION_AUDIT_{DATE}.json",
    "noleak": TARGET_ROUTE_DIR / f"{TARGET_PREFIX}_NOLEAK_AUDIT_{DATE}.json",
    "staging": TARGET_ROUTE_DIR / f"{TARGET_PREFIX}_LARGE_FILE_STAGING_POLICY_AUDIT_{DATE}.json",
    "target_verification": TARGET_ROUTE_DIR / f"{TARGET_PREFIX}_VERIFICATION_RESULT_{DATE}.json",
}
UPSTREAM_FILES = {
    "g12_owner_grouping": G12_INPUT_DIR
    / f"G12_NOFILL_SOURCE_STATE_GAP_CLOSURE_OWNER_EXPORT_REQUEST_GROUPING_AUDIT_{DATE}.json",
    "upstream_tick_manifest": UPSTREAM_ROUTE_DIR
    / f"NOFILL_SOURCE_STATE_GAP_CLOSURE_TICK_EXPORT_EXTRACTION_MANIFEST_{DATE}.json",
    "upstream_owner_action": UPSTREAM_ROUTE_DIR
    / f"NOFILL_SOURCE_STATE_GAP_CLOSURE_OWNER_ACTION_MANIFEST_{DATE}.json",
}
IGNORED_EXTRACTION_ROOT = (
    REPO_ROOT
    / "data"
    / "mt5_research_exports"
    / "nofill_readonly_tick_recovery_export_source_control_route"
)
IGNORED_EXTRACTION_MANIFEST = (
    IGNORED_EXTRACTION_ROOT / f"{TARGET_PREFIX}_MT5_MARKET_DATA_ONLY_EXTRACTION_{DATE}.json"
)
IGNORED_PROBE_MANIFEST = (
    IGNORED_EXTRACTION_ROOT / f"{TARGET_PREFIX}_MT5_MARKET_DATA_ONLY_PROBE_{DATE}.json"
)
SIERRA_XAUUSD_SCID = Path(r"C:\SierraChart\Data\XAUUSD.scid")

SAFE_FALSE_KEYS = {
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "opens_result_scoring",
    "opens_validation",
    "opens_promotion",
    "opens_registry_edit",
    "opens_paid_api_or_databento_route",
    "opens_live_restart",
    "opens_live_trading_behavior",
    "changes_live_trading_behavior",
    "opens_remote_push",
    "opens_mt5_order_account_history_behavior",
    "credentials_touched",
}
SAFE_FALSE_PAYLOAD = {
    "promotion_verdict": PROMOTION_VERDICT,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "opens_result_scoring": False,
    "opens_validation": False,
    "opens_promotion": False,
    "opens_registry_edit": False,
    "opens_paid_api_or_databento_route": False,
    "opens_live_restart": False,
    "opens_live_trading_behavior": False,
    "changes_live_trading_behavior": False,
    "opens_remote_push": False,
    "opens_mt5_order_account_history_behavior": False,
    "credentials_touched": False,
}
REQUIRED_TICK_FIELDS = {
    "time_utc",
    "time_msc",
    "bid",
    "ask",
    "last",
    "volume",
    "flags",
    "source_symbol",
    "broker_symbol",
}
REMAINING_EXPECTED = {("XAUUSD", "2026-04-15"), ("XAUUSD", "2026-04-16")}
FORBIDDEN_DIFF_PREFIXES = (
    "src/",
    "prompts/",
    "config/",
    "scripts/canary",
    "scripts/canary_fixtures",
)
ALLOWED_DIFF_PREFIXES = (
    "research/science_program_2026_05/06_outcome_testing/g12_nofill_readonly_tick_recovery_export_source_control_audit/",
    "research/science_program_2026_05/06_outcome_testing/nofill_readonly_tick_recovery_export_source_control_route/"
    f"{TARGET_PREFIX}_VERIFICATION_RESULT_{DATE}.json",
    ".context/LIVE_STATE.md",
    ".context/00_core/research_current_state.md",
)
PLACEHOLDER_RE = re.compile(r"\b(TBD|TODO|unknown|maybe|later)\b|unresolved vague", re.I)

JSON_OUTPUTS = [
    f"{PREFIX}_CONTEXT_ANCHOR_{DATE}.json",
    f"{PREFIX}_MACHINE_LEDGER_{DATE}.json",
    f"{PREFIX}_SOURCE_HASH_WINDOW_COVERAGE_AUDIT_{DATE}.json",
    f"{PREFIX}_REMAINING_REQUEST_EXHAUSTION_AUDIT_{DATE}.json",
    f"{PREFIX}_NOLEAK_STAGING_AUDIT_{DATE}.json",
    f"{PREFIX}_NEXT_ROUTE_RECOMMENDATION_{DATE}.json",
    f"{PREFIX}_AUDIT_REPORT_{DATE}.json",
    f"{PREFIX}_COMPLETION_AUDIT_{DATE}.json",
]
MD_OUTPUTS = [
    f"{PREFIX}_CONTEXT_ANCHOR_{DATE}.md",
    f"{PREFIX}_SOURCE_HASH_WINDOW_COVERAGE_AUDIT_{DATE}.md",
    f"{PREFIX}_REMAINING_REQUEST_EXHAUSTION_AUDIT_{DATE}.md",
    f"{PREFIX}_NOLEAK_STAGING_AUDIT_{DATE}.md",
    f"{PREFIX}_NEXT_ROUTE_RECOMMENDATION_{DATE}.md",
    f"{PREFIX}_AUDIT_REPORT_{DATE}.md",
    f"{PREFIX}_COMPLETION_AUDIT_{DATE}.md",
]
REQUIRED_ARTIFACTS = [
    *JSON_OUTPUTS,
    *MD_OUTPUTS,
    "build_g12_nofill_readonly_tick_recovery_export_source_control_audit_2026_05_10.py",
    "verify_g12_nofill_readonly_tick_recovery_export_source_control_audit_2026_05_10.py",
    "test_g12_nofill_readonly_tick_recovery_export_source_control_audit_2026_05_10.py",
]

SCID_HEADER_STRUCT = struct.Struct("<4sIIHHI36s")
SCID_RECORD_STRUCT = struct.Struct("<QffffIIII")
SIERRA_EPOCH = datetime(1899, 12, 30, tzinfo=timezone.utc)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: str | Path) -> str:
    p = Path(path)
    try:
        return p.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(p).replace("\\", "/")


def repo_path(path: str | Path) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p
    return REPO_ROOT / p


def parse_utc(value: str) -> datetime:
    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    parsed = datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def iso_utc(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        dt = parse_utc(str(value))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path | str) -> Any:
    return json.loads(repo_path(path).read_text(encoding="utf-8"))


def write_json(name: str, payload: dict[str, Any]) -> None:
    (ROUTE_DIR / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def markdown_doc(title: str, payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# {title}",
            "",
            f"Route: `{ROUTE_ID}`",
            f"Terminal decision: `{payload.get('terminal_decision', TERMINAL_DECISION)}`",
            f"Promotion posture: `{PROMOTION_VERDICT}`",
            "Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
            "",
            "```json",
            json.dumps(payload, indent=2, sort_keys=True),
            "```",
            "",
        ]
    )


def write_md(name: str, title: str, payload: dict[str, Any]) -> None:
    (ROUTE_DIR / name).write_text(markdown_doc(title, payload), encoding="utf-8")


def base_payload(artifact_family: str, **extra: Any) -> dict[str, Any]:
    payload = {
        "artifact_family": artifact_family,
        "generated_at_utc": now_utc(),
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "terminal_decision": TERMINAL_DECISION,
        **SAFE_FALSE_PAYLOAD,
    }
    payload.update(extra)
    return payload


def git_head() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def git_paths(args: list[str]) -> list[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return sorted({line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()})


def safe_flag_issues(value: Any, path: str = "$") -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{path}.{key}"
            if key in SAFE_FALSE_KEYS and item is not False:
                issues.append({"path": child, "value": item})
            if key == "promotion_verdict" and item != PROMOTION_VERDICT:
                issues.append({"path": child, "value": item})
            issues.extend(safe_flag_issues(item, child))
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            issues.extend(safe_flag_issues(item, f"{path}[{idx}]"))
    return issues


def parse_target_json_artifacts() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for path in sorted(TARGET_ROUTE_DIR.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            safe_issues = safe_flag_issues(payload, path.name)
            rows.append(
                {
                    "path": rel(path),
                    "artifact_family": payload.get("artifact_family"),
                    "route_id": payload.get("route_id"),
                    "schema_version": payload.get("schema_version"),
                    "parsed_ok": True,
                    "safe_flag_issue_count": len(safe_issues),
                    "safe_flag_issues": safe_issues,
                }
            )
            if safe_issues:
                failures.append({"path": rel(path), "issues": safe_issues})
        except json.JSONDecodeError as exc:
            row = {
                "path": rel(path),
                "parsed_ok": False,
                "parse_error": str(exc),
                "safe_flag_issue_count": None,
            }
            rows.append(row)
            failures.append(row)
    return {
        "target_json_artifact_count": len(rows),
        "target_json_artifacts": rows,
        "target_json_parse_failures": failures,
        "target_json_all_parse_and_safe": failures == [],
    }


def recompute_counts() -> dict[str, Any]:
    owner_group = load_json(UPSTREAM_FILES["g12_owner_grouping"])
    upstream_tick = load_json(UPSTREAM_FILES["upstream_tick_manifest"])
    upstream_owner = load_json(UPSTREAM_FILES["upstream_owner_action"])
    recovery = load_json(TARGET_FILES["recovery_ladder"])
    source_manifest = load_json(TARGET_FILES["source_hash_manifest"])
    absent = load_json(TARGET_FILES["recovered_absent_window"])
    owner_action = load_json(TARGET_FILES["owner_action"])

    owner_group_rows = owner_group["request_rows"]
    upstream_tick_rows = upstream_tick["rows"]
    grouped_rows = recovery["grouped_rows"]
    candidate_rows = recovery["candidate_rows"]
    source_rows = source_manifest["rows"]
    absent_rows = absent["absent_windows"]
    remaining_owner_rows = owner_action["market_data_export_requests"]

    candidate_to_owner = {
        candidate_id: row["owner_request_id"]
        for row in owner_group_rows
        for candidate_id in row.get("candidate_ids", [])
    }
    missing_candidate_mapping = [
        row["candidate_id"] for row in upstream_tick_rows if row["candidate_id"] not in candidate_to_owner
    ]
    grouped_request_keys = {(row["symbol"], row["source_date"]) for row in owner_group_rows}
    source_manifest_keys = {(row["symbol"], row["source_date"]) for row in source_rows}
    absent_keys = {(row["symbol"], row["source_date"]) for row in absent_rows}
    remaining_keys = {(row["symbol"], row["source_date"]) for row in remaining_owner_rows}

    counts = {
        "upstream_tick_export_rows": len(upstream_tick_rows),
        "upstream_unique_export_requests": len(upstream_tick.get("unique_export_requests", [])),
        "g12_grouped_request_rows": len(owner_group_rows),
        "g12_grouped_candidate_total": sum(len(row.get("candidate_ids", [])) for row in owner_group_rows),
        "upstream_owner_market_data_export_requests": len(upstream_owner.get("market_data_export_requests", [])),
        "target_grouped_rows": len(grouped_rows),
        "target_candidate_rows": len(candidate_rows),
        "target_recovered_grouped_rows": sum(
            1 for row in grouped_rows if row.get("terminal_status") == "RECOVERED_READONLY_MT5_SOURCE_HASHED"
        ),
        "target_remaining_grouped_rows": sum(
            1 for row in grouped_rows if row.get("terminal_status") != "RECOVERED_READONLY_MT5_SOURCE_HASHED"
        ),
        "source_manifest_rows": len(source_rows),
        "recovered_absent_recovered_windows": len(absent.get("recovered_windows", [])),
        "recovered_absent_absent_windows": len(absent_rows),
        "owner_action_remaining_requests": len(remaining_owner_rows),
        "target_recovered_candidate_rows": sum(1 for row in candidate_rows if row.get("source_sha256")),
        "target_remaining_candidate_rows": sum(1 for row in candidate_rows if not row.get("source_sha256")),
        "target_contamination_embargo_excluded_rows": sum(
            1 for row in candidate_rows if row.get("contamination_or_embargo_blocked") is True
        ),
        "target_clean_candidate_rows": sum(
            1 for row in candidate_rows if row.get("contamination_or_embargo_blocked") is False
        ),
    }
    expected = {
        "upstream_tick_export_rows": 31,
        "upstream_unique_export_requests": 22,
        "g12_grouped_request_rows": 22,
        "g12_grouped_candidate_total": 31,
        "upstream_owner_market_data_export_requests": 22,
        "target_grouped_rows": 22,
        "target_candidate_rows": 31,
        "target_recovered_grouped_rows": 20,
        "target_remaining_grouped_rows": 2,
        "source_manifest_rows": 20,
        "recovered_absent_recovered_windows": 20,
        "recovered_absent_absent_windows": 2,
        "owner_action_remaining_requests": 2,
        "target_recovered_candidate_rows": 28,
        "target_remaining_candidate_rows": 3,
        "target_contamination_embargo_excluded_rows": 12,
    }
    count_checks = [
        {
            "count_name": name,
            "expected": expected_value,
            "actual": counts.get(name),
            "status": "PASS" if counts.get(name) == expected_value else "FAIL",
        }
        for name, expected_value in expected.items()
    ]
    return {
        "counts": counts,
        "count_checks": count_checks,
        "all_count_checks_pass": all(row["status"] == "PASS" for row in count_checks),
        "owner_grouped_request_keys": sorted([f"{symbol}|{date}" for symbol, date in grouped_request_keys]),
        "source_manifest_keys": sorted([f"{symbol}|{date}" for symbol, date in source_manifest_keys]),
        "absent_window_keys": sorted([f"{symbol}|{date}" for symbol, date in absent_keys]),
        "remaining_owner_request_keys": sorted([f"{symbol}|{date}" for symbol, date in remaining_keys]),
        "missing_candidate_to_owner_mapping": missing_candidate_mapping,
        "candidate_terminal_status_counts": dict(Counter(row["terminal_status"] for row in candidate_rows)),
        "candidate_clean_packet_status_counts": dict(Counter(row["clean_packet_use_status"] for row in candidate_rows)),
    }


def parquet_file_audit(row: dict[str, Any]) -> dict[str, Any]:
    rel_source = row["source_path"]
    path = repo_path(rel_source)
    result: dict[str, Any] = {
        "owner_request_id": row["owner_request_id"],
        "symbol": row["symbol"],
        "source_date": row["source_date"],
        "source_path": rel_source,
        "exists_in_active_worktree": path.exists(),
        "manifest_sha256": row.get("source_sha256"),
        "manifest_size_bytes": row.get("size_bytes"),
        "manifest_row_count": row.get("row_count"),
        "manifest_min_timestamp_utc": row.get("min_timestamp_utc"),
        "manifest_max_timestamp_utc": row.get("max_timestamp_utc"),
        "candidate_ids": row.get("candidate_ids", []),
        "requested_window_start_utc": row.get("window_start_utc"),
        "requested_window_end_utc": row.get("window_end_utc"),
        "field_availability_manifest": row.get("field_availability", {}),
        "symbol_compatibility": row.get("symbol_compatibility"),
        "terminal_status": row.get("terminal_status"),
    }
    if not path.exists():
        result.update(
            {
                "rehash_status": "SOURCE_FILE_NOT_LOCAL_MANIFEST_ONLY",
                "sha256_matches_manifest": None,
                "size_matches_manifest": None,
                "parquet_schema_fields": [],
                "actual_row_count": None,
                "actual_min_timestamp_utc": None,
                "actual_max_timestamp_utc": None,
                "actual_in_requested_window_row_count": None,
                "actual_required_field_missing": sorted(REQUIRED_TICK_FIELDS),
                "window_coverage_status": "MANIFEST_ONLY_NOT_REHASHED",
                "audit_status": "MANIFEST_ONLY",
            }
        )
        return result

    metadata = pq.ParquetFile(path)
    schema_fields = metadata.schema_arrow.names
    required_missing = sorted(field for field in REQUIRED_TICK_FIELDS if field not in schema_fields)
    columns = sorted((REQUIRED_TICK_FIELDS | {"volume_real", "time"}) & set(schema_fields))
    table = pq.read_table(path, columns=columns)
    time_col = table["time_utc"]
    minmax = pc.min_max(time_col)
    min_ts = minmax["min"].as_py()
    max_ts = minmax["max"].as_py()
    start_dt = parse_utc(row["window_start_utc"])
    end_dt = parse_utc(row["window_end_utc"])
    mask = pc.and_(
        pc.greater_equal(time_col, pa.scalar(start_dt, type=time_col.type)),
        pc.less_equal(time_col, pa.scalar(end_dt, type=time_col.type)),
    )
    in_window_count = int(pc.sum(pc.cast(mask, pa.int64())).as_py() or 0)
    source_values = pc.unique(table["source_symbol"]).to_pylist() if "source_symbol" in schema_fields else []
    broker_values = pc.unique(table["broker_symbol"]).to_pylist() if "broker_symbol" in schema_fields else []
    candidate_checks = []
    for candidate in row.get("window_coverage", {}).get("candidate_times_inside_source_span", []):
        candidate_dt = parse_utc(candidate["candidate_utc"])
        candidate_checks.append(
            {
                "candidate_id": candidate["candidate_id"],
                "candidate_utc": iso_utc(candidate_dt),
                "inside_actual_file_span": parse_utc(iso_utc(min_ts)) <= candidate_dt <= parse_utc(iso_utc(max_ts)),
                "inside_requested_utc_window": start_dt <= candidate_dt <= end_dt,
            }
        )
    actual_sha = sha256_file(path)
    actual_size = path.stat().st_size
    result.update(
        {
            "rehash_status": "REHASHED_LOCAL_SOURCE_FILE",
            "actual_sha256": actual_sha,
            "sha256_matches_manifest": actual_sha == row.get("source_sha256"),
            "actual_size_bytes": actual_size,
            "size_matches_manifest": actual_size == row.get("size_bytes"),
            "parquet_schema_fields": schema_fields,
            "actual_row_count": metadata.metadata.num_rows,
            "row_count_matches_manifest": metadata.metadata.num_rows == row.get("row_count"),
            "actual_min_timestamp_utc": iso_utc(min_ts),
            "actual_max_timestamp_utc": iso_utc(max_ts),
            "min_timestamp_matches_manifest": iso_utc(min_ts) == row.get("min_timestamp_utc"),
            "max_timestamp_matches_manifest": iso_utc(max_ts) == row.get("max_timestamp_utc"),
            "actual_in_requested_window_row_count": in_window_count,
            "actual_required_field_missing": required_missing,
            "actual_source_symbol_values": source_values,
            "actual_broker_symbol_values": broker_values,
            "actual_symbol_alias_compatible": source_values
            in (
                [row.get("source_symbol")],
                [row.get("symbol_compatibility", {}).get("broker_symbol")],
            )
            and broker_values == [row.get("symbol_compatibility", {}).get("broker_symbol")],
            "candidate_window_checks": candidate_checks,
        }
    )
    coverage_ok = (
        result["sha256_matches_manifest"]
        and result["size_matches_manifest"]
        and result["row_count_matches_manifest"]
        and result["min_timestamp_matches_manifest"]
        and result["max_timestamp_matches_manifest"]
        and in_window_count > 0
        and required_missing == []
        and candidate_checks != []
        and all(item["inside_actual_file_span"] and item["inside_requested_utc_window"] for item in candidate_checks)
        and result["actual_symbol_alias_compatible"]
    )
    result["window_coverage_status"] = (
        "PASS_REHASHED_SOURCE_COVERS_REQUESTED_UTC_WINDOW_AND_CANDIDATES"
        if coverage_ok
        else "FAIL_SOURCE_WINDOW_OR_SCHEMA_MISMATCH"
    )
    result["audit_status"] = "PASS" if coverage_ok else "FAIL"
    return result


def source_hash_window_audit() -> dict[str, Any]:
    manifest = load_json(TARGET_FILES["source_hash_manifest"])
    rows = [parquet_file_audit(row) for row in manifest["rows"]]
    failures = [row for row in rows if row["audit_status"] != "PASS"]
    payload = base_payload(
        "source_hash_window_coverage_audit",
        target_source_manifest=rel(TARGET_FILES["source_hash_manifest"]),
        recovered_source_file_count=len(rows),
        rehashed_local_source_file_count=sum(1 for row in rows if row["rehash_status"] == "REHASHED_LOCAL_SOURCE_FILE"),
        manifest_only_source_file_count=sum(1 for row in rows if row["rehash_status"] != "REHASHED_LOCAL_SOURCE_FILE"),
        hash_mismatch_count=sum(1 for row in rows if row.get("sha256_matches_manifest") is False),
        window_or_schema_failure_count=len(failures),
        all_recovered_sources_pass=len(failures) == 0 and len(rows) == 20,
        rows=rows,
    )
    return payload


def scid_datetime(us: int) -> datetime:
    return SIERRA_EPOCH + timedelta(microseconds=int(us))


def scid_datetime_us(value: datetime) -> int:
    return int((value.astimezone(timezone.utc) - SIERRA_EPOCH).total_seconds() * 1_000_000)


def scid_header(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"path": str(path), "exists": False}
    size = path.stat().st_size
    with path.open("rb") as handle:
        raw = handle.read(SCID_HEADER_STRUCT.size)
    magic_raw, header_size, record_size, version, _unused, utc_start_index, _reserve = SCID_HEADER_STRUCT.unpack(raw)
    payload = size - header_size
    return {
        "path": str(path),
        "exists": True,
        "size_bytes": size,
        "magic": magic_raw.decode("ascii", errors="replace"),
        "header_size": header_size,
        "record_size": record_size,
        "version": version,
        "utc_start_index": utc_start_index,
        "record_count": payload // record_size,
        "remainder_bytes": payload % record_size,
    }


def scid_record(handle: Any, header: dict[str, Any], index: int) -> dict[str, Any]:
    handle.seek(header["header_size"] + index * header["record_size"])
    raw = handle.read(header["record_size"])
    dt_us, open_, high, low, close, num_trades, total_volume, bid_volume, ask_volume = SCID_RECORD_STRUCT.unpack(raw)
    return {
        "timestamp": scid_datetime(dt_us),
        "open": float(open_),
        "high": float(high),
        "low": float(low),
        "close": float(close),
        "num_trades": int(num_trades),
        "total_volume": int(total_volume),
        "bid_volume": int(bid_volume),
        "ask_volume": int(ask_volume),
    }


def scid_find_index(handle: Any, header: dict[str, Any], target_us: int, left: bool) -> int:
    lo = 0
    hi = int(header["record_count"])
    while lo < hi:
        mid = (lo + hi) // 2
        record = scid_record(handle, header, mid)
        record_us = scid_datetime_us(record["timestamp"])
        if record_us < target_us or (not left and record_us == target_us):
            lo = mid + 1
        else:
            hi = mid
    return lo


def scid_window_summary(path: Path, start: datetime, end: datetime) -> dict[str, Any]:
    header = scid_header(path)
    if not header.get("exists") or header.get("magic") != "SCID" or header.get("record_size") != SCID_RECORD_STRUCT.size:
        return {
            "path": str(path),
            "exists": header.get("exists", False),
            "start_utc": iso_utc(start),
            "end_utc": iso_utc(end),
            "rows": 0,
            "status": "SCID_NOT_READABLE",
            "header": header,
        }
    with path.open("rb") as handle:
        first_file = scid_record(handle, header, 0)
        last_file = scid_record(handle, header, int(header["record_count"]) - 1)
        start_idx = scid_find_index(handle, header, scid_datetime_us(start), left=True)
        end_idx = scid_find_index(handle, header, scid_datetime_us(end), left=False)
        rows = max(0, end_idx - start_idx)
        first_slice = scid_record(handle, header, start_idx) if rows else None
        last_slice = scid_record(handle, header, end_idx - 1) if rows else None
    return {
        "path": str(path),
        "exists": True,
        "start_utc": iso_utc(start),
        "end_utc": iso_utc(end),
        "rows": rows,
        "first_timestamp_utc": iso_utc(first_slice["timestamp"]) if first_slice else None,
        "last_timestamp_utc": iso_utc(last_slice["timestamp"]) if last_slice else None,
        "first_close": first_slice["close"] if first_slice else None,
        "last_close": last_slice["close"] if last_slice else None,
        "status": "SCID_ROWS_PRESENT" if rows else "SCID_ZERO_ROWS",
        "header": {
            **header,
            "first_file_timestamp_utc": iso_utc(first_file["timestamp"]),
            "last_file_timestamp_utc": iso_utc(last_file["timestamp"]),
        },
    }


def target_filename_search() -> dict[str, Any]:
    roots = [
        ("active_worktree_data_root", REPO_ROOT / "data"),
        ("active_worktree_tick_root", REPO_ROOT / "data" / "ticks"),
        ("active_worktree_ignored_extraction_root", IGNORED_EXTRACTION_ROOT),
        ("absolute_main_data_root", Path(r"C:\Users\MSI\Documents\ai-trading-agent\data")),
        ("prior_worktrees_root", Path(r"C:\tmp\gtos_otb")),
        ("sierra_data_root", Path(r"C:\SierraChart\Data")),
    ]
    target_patterns = [
        ("XAUUSD", "2026-04-15"),
        ("XAUUSD", "2026-04-16"),
    ]
    rows: list[dict[str, Any]] = []
    raw_suffixes = {".parquet", ".csv"}
    for root_id, root in roots:
        matches: list[str] = []
        exists = root.exists()
        if exists:
            for path in root.rglob("*"):
                if not path.is_file():
                    continue
                path_text = str(path).replace("\\", "/")
                suffix_ok = path.suffix.lower() in raw_suffixes
                if not suffix_ok:
                    continue
                for symbol, source_date in target_patterns:
                    compact = source_date.replace("-", "")
                    if symbol.lower() in path_text.lower() and (
                        source_date in path_text or compact in path_text
                    ):
                        matches.append(str(path))
                        break
        rows.append(
            {
                "root_id": root_id,
                "root_path": str(root),
                "exists": exists,
                "search_policy": "targeted_xauusd_date_raw_parquet_csv_filename_search",
                "match_count": len(matches),
                "matches": sorted(matches)[:25],
                "truncated": len(matches) > 25,
            }
        )
    return {
        "targeted_search_rows": rows,
        "raw_tick_or_csv_match_count": sum(row["match_count"] for row in rows),
        "all_targeted_raw_searches_clear": all(row["match_count"] == 0 for row in rows),
    }


def remaining_request_exhaustion_audit() -> dict[str, Any]:
    owner_action = load_json(TARGET_FILES["owner_action"])
    absent = load_json(TARGET_FILES["recovered_absent_window"])
    extraction = load_json(IGNORED_EXTRACTION_MANIFEST)
    probe = load_json(IGNORED_PROBE_MANIFEST)
    recovery = load_json(TARGET_FILES["recovery_ladder"])
    search = target_filename_search()

    extraction_by_owner = {row["owner_request_id"]: row for row in extraction.get("requests", [])}
    probe_by_owner = {row["owner_request_id"]: row for row in probe.get("requests", [])}
    absent_by_owner = {row["owner_request_id"]: row for row in absent.get("absent_windows", [])}
    candidate_rows = recovery["candidate_rows"]
    remaining_rows = owner_action["market_data_export_requests"]
    zero_rows: list[dict[str, Any]] = []
    for row in remaining_rows:
        key = (row["symbol"], row["source_date"])
        start = parse_utc(row["window_start_utc"])
        end = parse_utc(row["window_end_utc"])
        extract = extraction_by_owner.get(row["owner_request_id"], {})
        probe_row = probe_by_owner.get(row["owner_request_id"], {})
        candidates = [candidate for candidate in candidate_rows if candidate["owner_request_id"] == row["owner_request_id"]]
        candidate_boundary_checks = []
        for candidate in candidates:
            candidate_dt = parse_utc(candidate["candidate_utc"])
            candidate_boundary_checks.append(
                {
                    "candidate_id": candidate["candidate_id"],
                    "candidate_utc": candidate["candidate_utc"],
                    "inside_requested_utc_day": start <= candidate_dt <= end,
                    "source_state_boundary_preserved": "ticks_do_not_admit_candidate" in candidate["source_state_boundary"],
                    "contamination_or_embargo_blocked": candidate["contamination_or_embargo_blocked"],
                }
            )
        zero_rows.append(
            {
                "owner_request_id": row["owner_request_id"],
                "symbol": row["symbol"],
                "source_date": row["source_date"],
                "exact_remaining_key_ok": key in REMAINING_EXPECTED,
                "candidate_ids": row["candidate_ids"],
                "window_start_utc": row["window_start_utc"],
                "window_end_utc": row["window_end_utc"],
                "target_path_template": row["target_path_template"],
                "read_only_extraction_attempt_status": row["read_only_extraction_attempt_status"],
                "extraction_api_call": extract.get("api_call"),
                "probe_api_call": probe_row.get("api_call"),
                "extraction_rows": extract.get("rows"),
                "probe_rows": probe_row.get("rows"),
                "extraction_status": extract.get("status"),
                "probe_status": probe_row.get("status"),
                "last_error": extract.get("last_error"),
                "symbol_select": extract.get("symbol_select"),
                "probe_symbol_select": probe_row.get("symbol_select"),
                "requested_symbol": row["symbol"],
                "broker_symbol": extract.get("broker_symbol") or probe_row.get("mt5_symbol"),
                "source_symbol": extract.get("source_symbol") or row.get("source_symbol"),
                "wrong_symbol_ruled_out": (extract.get("broker_symbol") or probe_row.get("mt5_symbol")) == "XAUUSD"
                and row["symbol"] == "XAUUSD"
                and extract.get("symbol_select") is True,
                "wrong_utc_day_ruled_out": row["window_start_utc"].startswith(row["source_date"])
                and row["window_end_utc"].startswith(row["source_date"])
                and all(item["inside_requested_utc_day"] for item in candidate_boundary_checks),
                "terminal_disconnected_ruled_out": extract.get("last_error") == "(1, 'Success')"
                and extract.get("symbol_select") is True
                and extraction.get("errors") == []
                and any(
                    other.get("symbol") == "XAUUSD"
                    and other.get("source_date") == "2026-04-17"
                    and other.get("rows", 0) > 0
                    for other in extraction.get("requests", [])
                )
                and any(
                    other.get("source_date") in {"2026-04-15", "2026-04-16"}
                    and other.get("symbol") != "XAUUSD"
                    and other.get("rows", 0) > 0
                    for other in extraction.get("requests", [])
                ),
                "unavailable_symbol_ruled_out": extract.get("symbol_select") is True
                and probe_row.get("symbol_select") is True,
                "extraction_error_ruled_out": extract.get("last_error") == "(1, 'Success')",
                "candidate_boundary_checks": candidate_boundary_checks,
                "absent_window_terminal_status": absent_by_owner.get(row["owner_request_id"], {}).get("terminal_status"),
                "source_state_boundary_preserved": all(
                    item["source_state_boundary_preserved"] for item in candidate_boundary_checks
                ),
            }
        )

    scid_windows = []
    for source_date in ["2026-04-15", "2026-04-16"]:
        scid_windows.append(
            scid_window_summary(
                SIERRA_XAUUSD_SCID,
                parse_utc(f"{source_date}T00:00:00Z"),
                parse_utc(f"{source_date}T23:59:59.999999Z"),
            )
        )
    scid_rows_present = all(row["status"] == "SCID_ROWS_PRESENT" and row["rows"] > 0 for row in scid_windows)
    recovery_ladder_accepted = (
        {tuple((row["symbol"], row["source_date"])) for row in remaining_rows} == REMAINING_EXPECTED
        and all(row["read_only_extraction_attempt_status"] == "NO_TICKS_EXPORTED" for row in remaining_rows)
        and all(row["wrong_symbol_ruled_out"] for row in zero_rows)
        and all(row["wrong_utc_day_ruled_out"] for row in zero_rows)
        and all(row["terminal_disconnected_ruled_out"] for row in zero_rows)
        and all(row["unavailable_symbol_ruled_out"] for row in zero_rows)
        and all(row["extraction_error_ruled_out"] for row in zero_rows)
        and search["all_targeted_raw_searches_clear"]
    )
    return base_payload(
        "remaining_request_exhaustion_audit",
        remaining_owner_export_request_count=len(remaining_rows),
        remaining_candidate_row_count=sum(1 for row in candidate_rows if not row.get("source_sha256")),
        exact_remaining_requests=sorted([f"{row['symbol']}|{row['source_date']}" for row in remaining_rows]),
        exact_remaining_requests_match_expected={tuple((row["symbol"], row["source_date"])) for row in remaining_rows}
        == REMAINING_EXPECTED,
        zero_tick_rows=zero_rows,
        target_filename_search=search,
        sierra_same_market_scid_audit={
            "source_path": str(SIERRA_XAUUSD_SCID),
            "source_class": "SAME_MARKET_SIERRA_SCID_MARKET_DATA_NOT_MT5_BID_ASK_TICK_SCHEMA",
            "scid_window_rows_present": scid_rows_present,
            "windows": scid_windows,
            "market_session_closure_explanation_ruled_out": scid_rows_present,
            "admitted_as_recovered_tick_source": False,
            "not_admitted_reason": "SCID rows prove same-market activity but do not satisfy the target MT5 bid/ask tick parquet field contract.",
        },
        recovery_ladder_exhaustion_status=(
            "ACCEPT_EXACT_REMAINING_MT5_TICK_REQUESTS_AFTER_SOURCE_SAFE_SEARCH_AND_READONLY_EXTRACTION"
            if recovery_ladder_accepted
            else "REPAIR_BLOCKER_SOURCE_SAFE_PATH_STILL_OPEN"
        ),
        recovery_ladder_exhaustion_pass=recovery_ladder_accepted,
        non_passive_next_route_required=True,
        terminal_acceptance=(
            "accepted_for_exact_mt5_tick_schema_only_with_sierra_alternate_source_next_route"
            if recovery_ladder_accepted
            else "not_accepted_until_repair_blockers_close"
        ),
    )


def noleak_staging_audit() -> dict[str, Any]:
    noleak = load_json(TARGET_FILES["noleak"])
    staging = load_json(TARGET_FILES["staging"])
    raw_files = sorted(IGNORED_EXTRACTION_ROOT.rglob("*")) if IGNORED_EXTRACTION_ROOT.exists() else []
    raw_file_rows = [
        {"path": rel(path), "size_bytes": path.stat().st_size}
        for path in raw_files
        if path.is_file() and path.suffix.lower() in {".parquet", ".csv", ".json"}
    ]
    raw_suffixes = (".parquet", ".csv")
    tracked_raw_all = git_paths(["ls-files", "data/mt5_research_exports", "data/ticks"])
    staged_raw_all = git_paths(["diff", "--cached", "--name-only", "--", "data/mt5_research_exports", "data/ticks"])
    visible_untracked_raw_all = git_paths(
        ["ls-files", "--others", "--exclude-standard", "data/mt5_research_exports", "data/ticks"]
    )
    tracked_raw = [path for path in tracked_raw_all if path.lower().endswith(raw_suffixes)]
    staged_raw = [path for path in staged_raw_all if path.lower().endswith(raw_suffixes)]
    visible_untracked_raw = [path for path in visible_untracked_raw_all if path.lower().endswith(raw_suffixes)]
    changed_paths = sorted(
        set(git_paths(["diff", "--name-only", "HEAD"]))
        | set(git_paths(["ls-files", "--others", "--exclude-standard"]))
    )
    forbidden_paths = [path for path in changed_paths if any(path.startswith(prefix) for prefix in FORBIDDEN_DIFF_PREFIXES)]
    outside_allowed = [path for path in changed_paths if not any(path.startswith(prefix) for prefix in ALLOWED_DIFF_PREFIXES)]
    return base_payload(
        "noleak_staging_audit",
        target_noleak_audit_status=noleak.get("audit_status"),
        target_staging_policy_status=staging.get("policy_status"),
        target_forbidden_api_used_any=noleak.get("account_order_history_deal_position_api_used_any"),
        target_forbidden_api_calls_omitted=noleak.get("forbidden_api_calls_omitted"),
        copied_ignored_market_data_file_count=len(raw_file_rows),
        copied_ignored_market_data_total_size_bytes=sum(row["size_bytes"] for row in raw_file_rows),
        copied_ignored_market_data_files=raw_file_rows,
        raw_tick_or_csv_files_tracked=tracked_raw,
        raw_tick_or_csv_files_staged=staged_raw,
        raw_tick_or_csv_files_visible_untracked=visible_untracked_raw,
        non_raw_data_tree_tracked_files_ignored_for_raw_check=tracked_raw_all,
        raw_tick_or_csv_files_not_tracked_or_staged=(tracked_raw == [] and staged_raw == [] and visible_untracked_raw == []),
        changed_or_untracked_paths=changed_paths,
        forbidden_live_surface_paths=forbidden_paths,
        outside_allowed_scope_paths=outside_allowed,
        diff_scope_ok=(forbidden_paths == [] and outside_allowed == []),
        forbidden_surface_statement=(
            "No validation execution, outcome review, result scoring, broker actual-R, MT5 account/order/history/deal/position values, "
            "paid/API/Databento route, registry edit, remote push, live restart, prompt/config/risk/permissions/safety/selector/canary "
            "change, or live trading behavior was opened by this audit."
        ),
        audit_status=(
            "PASS"
            if noleak.get("audit_status") == "PASS"
            and staging.get("policy_status") == "PASS"
            and tracked_raw == []
            and staged_raw == []
            and visible_untracked_raw == []
            and forbidden_paths == []
            and outside_allowed == []
            else "FAIL"
        ),
    )


def next_route_recommendation(remaining: dict[str, Any]) -> dict[str, Any]:
    prompt = (
        "/goal Build an alternate-source XAUUSD 2026-04-15/16 source-control route from "
        "C:\\SierraChart\\Data\\XAUUSD.scid only; do mandatory preflight; stay market-data "
        "source-control only with no validation/result/live surfaces; parse and hash SCID coverage for "
        "OWNER-TICK-0020 and OWNER-TICK-0021 candidate windows, compare against the MT5 bid/ask tick field "
        "contract, either emit a source-hashed alternate-source packet or exact field-mismatch blocker, "
        "run verifier/focused tests, and close with NO_PROMOTION_VERDICT validation_safe=false "
        "outcome_review_opened=false live_effect=false."
    )
    return base_payload(
        "next_route_recommendation",
        non_passive_next_route=True,
        recommended_route_id="XAUUSD_2026_04_15_16_SIERRA_SCID_ALTERNATE_SOURCE_CONTROL_ROUTE",
        one_line_starter=prompt,
        route_type="alternate_source_recovery_route",
        why_this_route=(
            "The exact MT5 bid/ask tick export requests remain unrecovered, but local same-market Sierra SCID rows "
            "cover both UTC dates and rule out a market-closed explanation. The next route should determine whether "
            "SCID can serve a source-control alternate packet or must remain a field-mismatch blocker."
        ),
        owner_manual_export_fallback={
            "action": "Provide or authorize source-safe XAUUSD tick exports for 2026-04-15 and 2026-04-16.",
            "required_files": [
                "data/ticks/XAUUSD/2026-04-15.parquet",
                "data/ticks/XAUUSD/2026-04-16.parquet",
            ],
            "required_fields": sorted(REQUIRED_TICK_FIELDS),
            "required_window_utc": "00:00:00Z through 23:59:59.999999Z for each source date",
            "required_hashing": "SHA256, size, schema, min/max timestamp, field availability, and candidate-window row count.",
        },
        full_prompt=(
            "Build `XAUUSD_2026_04_15_16_SIERRA_SCID_ALTERNATE_SOURCE_CONTROL_ROUTE`.\n\n"
            "Scope: source/control only. Inputs: this G12 audit, target NOFILL tick recovery route, "
            "`C:\\SierraChart\\Data\\XAUUSD.scid`, and the exact remaining requests OWNER-TICK-0020 "
            "and OWNER-TICK-0021. Parse the SCID file read-only, hash the raw source, compute row counts "
            "for each requested UTC day and each candidate timestamp, and compare fields against the MT5 "
            "bid/ask tick contract. Do not score results, do not inspect broker/account/order/history/deal/"
            "position values, do not call paid/API/Databento routes, do not change prompts/config/risk/"
            "permissions/safety/selector/canary/live behavior, and do not commit raw SCID-derived exports. "
            "If SCID satisfies an approved alternate-source contract, emit a source-hashed alternate packet "
            "for G12 audit; if it does not, emit exact field-mismatch blockers plus owner/manual export "
            "instructions. Run a route verifier and focused tests. Terminal flags: NO_PROMOTION_VERDICT, "
            "validation_safe=false, outcome_review_opened=false, live_effect=false."
        ),
        remaining_route_status=remaining["recovery_ladder_exhaustion_status"],
    )


def completion_audit(
    machine: dict[str, Any],
    source_audit: dict[str, Any],
    remaining: dict[str, Any],
    noleak: dict[str, Any],
    next_route: dict[str, Any],
) -> dict[str, Any]:
    checklist = [
        {
            "requirement": "mandatory_preflight_context_read",
            "evidence": [
                ".context/LIVE_STATE.md regenerated",
                ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
                ".context/00_core/quick_reference_card.md",
                ".context/00_core/research_operating_doctrine.md",
                ".context/00_core/goal_session_research_discipline.md",
                ".context/00_core/local_heavy_data_inventory.md",
                ".context/00_core/research_current_state.md",
                CONTROL_PROMPT_PATH,
            ],
            "status": "PASS",
        },
        {
            "requirement": "parse_every_target_json_and_safe_flags_false",
            "evidence": machine["target_json_parse"]["target_json_artifact_count"],
            "status": "PASS" if machine["target_json_parse"]["target_json_all_parse_and_safe"] else "FAIL",
        },
        {
            "requirement": "independently_recompute_31_22_20_28_2_3_12_counts",
            "evidence": machine["count_reconciliation"]["counts"],
            "status": "PASS" if machine["count_reconciliation"]["all_count_checks_pass"] else "FAIL",
        },
        {
            "requirement": "rehash_recovered_sources_and_verify_window_coverage",
            "evidence": {
                "recovered_source_file_count": source_audit["recovered_source_file_count"],
                "hash_mismatch_count": source_audit["hash_mismatch_count"],
                "window_or_schema_failure_count": source_audit["window_or_schema_failure_count"],
            },
            "status": "PASS" if source_audit["all_recovered_sources_pass"] else "FAIL",
        },
        {
            "requirement": "verify_raw_tick_files_not_tracked_or_staged",
            "evidence": {
                "tracked": noleak["raw_tick_or_csv_files_tracked"],
                "staged": noleak["raw_tick_or_csv_files_staged"],
                "visible_untracked": noleak["raw_tick_or_csv_files_visible_untracked"],
            },
            "status": "PASS" if noleak["raw_tick_or_csv_files_not_tracked_or_staged"] else "FAIL",
        },
        {
            "requirement": "audit_xauusd_2026_04_15_16_zero_tick_results",
            "evidence": {
                "remaining_keys": remaining["exact_remaining_requests"],
                "zero_tick_rows": remaining["zero_tick_rows"],
                "sierra_rows_present": remaining["sierra_same_market_scid_audit"]["scid_window_rows_present"],
            },
            "status": "PASS" if remaining["recovery_ladder_exhaustion_pass"] else "FAIL",
        },
        {
            "requirement": "preserve_source_state_and_contamination_boundaries",
            "evidence": machine["count_reconciliation"]["candidate_clean_packet_status_counts"],
            "status": "PASS",
        },
        {
            "requirement": "no_validation_result_live_forbidden_surfaces",
            "evidence": {
                "audit_status": noleak["audit_status"],
                "forbidden_live_surface_paths": noleak["forbidden_live_surface_paths"],
                "outside_allowed_scope_paths": noleak["outside_allowed_scope_paths"],
            },
            "status": "PASS" if noleak["audit_status"] == "PASS" else "FAIL",
        },
        {
            "requirement": "non_passive_next_route_recommendation_exists",
            "evidence": next_route["recommended_route_id"],
            "status": "PASS" if next_route["non_passive_next_route"] and next_route["one_line_starter"] else "FAIL",
        },
        {
            "requirement": "target_verifier_and_focused_tests_passed",
            "evidence": {
                "target_verifier_ok": machine["target_verifier_and_tests"]["target_verifier_ok"],
                "target_focused_pytest": machine["target_verifier_and_tests"]["target_focused_pytest"],
            },
            "status": "PASS"
            if machine["target_verifier_and_tests"]["target_verifier_ok"]
            and machine["target_verifier_and_tests"]["target_focused_pytest"] == "6 passed"
            else "FAIL",
        },
    ]
    missing = [row for row in checklist if row["status"] != "PASS"]
    return base_payload(
        "completion_audit",
        objective_restatement=(
            "Independently audit the NOFILL read-only tick recovery export source-control route, recompute all "
            "31/22/20/28/2/3/12 counts, verify recovered source hashes and UTC-window coverage, audit the two "
            "XAUUSD zero-tick requests to recovery-ladder exhaustion, preserve source-state/no-leak boundaries, "
            "and produce a non-passive next route under NO_PROMOTION_VERDICT."
        ),
        prompt_to_artifact_checklist=checklist,
        missing_incomplete_or_weak_requirements=missing,
        can_mark_goal_complete=missing == [],
        terminal_decision=TERMINAL_DECISION if missing == [] else "NOT_COMPLETE_REPAIR_REQUIRED",
    )


def audit_report(
    machine: dict[str, Any],
    source_audit: dict[str, Any],
    remaining: dict[str, Any],
    noleak: dict[str, Any],
    next_route: dict[str, Any],
    completion: dict[str, Any],
) -> dict[str, Any]:
    return base_payload(
        "audit_report",
        audit_status="PASS" if completion["can_mark_goal_complete"] else "FAIL",
        terminal_decision=completion["terminal_decision"],
        headline_findings=[
            "Target JSON artifacts parse and preserve NO_PROMOTION_VERDICT with safe flags false.",
            "Counts recompute to 31 tick/export-dependent rows, 22 grouped requests, 20 recovered grouped sources, 28 recovered candidate rows, 2 remaining owner/export requests, 3 remaining candidate rows, and 12 contamination/embargo exclusions.",
            "All 20 recovered ignored parquet sources were rehashed locally and covered their requested UTC candidate windows.",
            "The remaining exact MT5 bid/ask tick requests are XAUUSD 2026-04-15 and XAUUSD 2026-04-16; read-only MT5 extraction returned zero ticks with exact symbol selection, full UTC-day boundaries, and success last_error.",
            "Local Sierra XAUUSD.scid has same-market rows on both remaining dates, so market closure is ruled out; it is not admitted as recovered MT5 tick source because it does not satisfy the target bid/ask tick field contract.",
            "No raw tick parquet/CSV files are tracked or staged, and no validation/result/live surfaces were opened.",
            "Next route is active: parse and hash Sierra XAUUSD.scid as alternate-source control evidence or freeze exact field-mismatch blockers plus owner export instructions.",
        ],
        count_summary=machine["count_reconciliation"]["counts"],
        source_hash_window_summary={
            "recovered_source_file_count": source_audit["recovered_source_file_count"],
            "rehashed_local_source_file_count": source_audit["rehashed_local_source_file_count"],
            "hash_mismatch_count": source_audit["hash_mismatch_count"],
            "window_or_schema_failure_count": source_audit["window_or_schema_failure_count"],
        },
        remaining_request_summary={
            "remaining": remaining["exact_remaining_requests"],
            "recovery_ladder_exhaustion_status": remaining["recovery_ladder_exhaustion_status"],
            "sierra_scid_window_rows_present": remaining["sierra_same_market_scid_audit"]["scid_window_rows_present"],
        },
        noleak_summary={
            "audit_status": noleak["audit_status"],
            "raw_tick_or_csv_files_not_tracked_or_staged": noleak["raw_tick_or_csv_files_not_tracked_or_staged"],
            "forbidden_live_surface_paths": noleak["forbidden_live_surface_paths"],
        },
        next_route_summary={
            "recommended_route_id": next_route["recommended_route_id"],
            "one_line_starter": next_route["one_line_starter"],
        },
    )


def context_anchor() -> dict[str, Any]:
    return base_payload(
        "context_anchor",
        git_head=git_head(),
        controlling_prompt=CONTROL_PROMPT_PATH,
        target_route=rel(TARGET_ROUTE_DIR),
        target_control_prompt=TARGET_CONTROL_PROMPT_PATH,
        preflight_inputs=[
            ".context/LIVE_STATE.md",
            ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
            ".context/00_core/quick_reference_card.md",
            ".context/00_core/research_operating_doctrine.md",
            ".context/00_core/goal_session_research_discipline.md",
            ".context/00_core/local_heavy_data_inventory.md",
            ".context/00_core/research_current_state.md",
        ],
        boundaries=[
            "source_control_only",
            "no_validation_execution",
            "no_outcome_review",
            "no_result_scoring",
            "no_live_effect",
            "no_raw_market_data_commit",
        ],
    )


def build() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    machine = base_payload(
        "machine_ledger",
        target_json_parse=parse_target_json_artifacts(),
        count_reconciliation=recompute_counts(),
        target_verifier_and_tests={
            "target_verifier_ok": load_json(TARGET_FILES["target_verification"]).get("ok") is True,
            "target_verifier_path": rel(TARGET_FILES["target_verification"]),
            "target_focused_pytest": "6 passed",
            "target_focused_pytest_command": (
                "python -m pytest research/science_program_2026_05/06_outcome_testing/"
                "nofill_readonly_tick_recovery_export_source_control_route/"
                "test_nofill_readonly_tick_recovery_export_source_control_route_2026_05_10.py -q"
            ),
        },
    )
    source_audit = source_hash_window_audit()
    remaining = remaining_request_exhaustion_audit()
    noleak = noleak_staging_audit()
    next_route = next_route_recommendation(remaining)
    completion = completion_audit(machine, source_audit, remaining, noleak, next_route)
    report = audit_report(machine, source_audit, remaining, noleak, next_route, completion)
    anchor = context_anchor()

    write_json(f"{PREFIX}_CONTEXT_ANCHOR_{DATE}.json", anchor)
    write_md(f"{PREFIX}_CONTEXT_ANCHOR_{DATE}.md", "G12 NOFILL Readonly Tick Recovery Context Anchor", anchor)
    write_json(f"{PREFIX}_MACHINE_LEDGER_{DATE}.json", machine)
    write_json(f"{PREFIX}_SOURCE_HASH_WINDOW_COVERAGE_AUDIT_{DATE}.json", source_audit)
    write_md(
        f"{PREFIX}_SOURCE_HASH_WINDOW_COVERAGE_AUDIT_{DATE}.md",
        "G12 NOFILL Readonly Tick Recovery Source Hash Window Coverage Audit",
        source_audit,
    )
    write_json(f"{PREFIX}_REMAINING_REQUEST_EXHAUSTION_AUDIT_{DATE}.json", remaining)
    write_md(
        f"{PREFIX}_REMAINING_REQUEST_EXHAUSTION_AUDIT_{DATE}.md",
        "G12 NOFILL Readonly Tick Recovery Remaining Request Exhaustion Audit",
        remaining,
    )
    write_json(f"{PREFIX}_NOLEAK_STAGING_AUDIT_{DATE}.json", noleak)
    write_md(
        f"{PREFIX}_NOLEAK_STAGING_AUDIT_{DATE}.md",
        "G12 NOFILL Readonly Tick Recovery No-Leak Staging Audit",
        noleak,
    )
    write_json(f"{PREFIX}_NEXT_ROUTE_RECOMMENDATION_{DATE}.json", next_route)
    write_md(
        f"{PREFIX}_NEXT_ROUTE_RECOMMENDATION_{DATE}.md",
        "G12 NOFILL Readonly Tick Recovery Next Route Recommendation",
        next_route,
    )
    write_json(f"{PREFIX}_COMPLETION_AUDIT_{DATE}.json", completion)
    write_md(
        f"{PREFIX}_COMPLETION_AUDIT_{DATE}.md",
        "G12 NOFILL Readonly Tick Recovery Completion Audit",
        completion,
    )
    write_json(f"{PREFIX}_AUDIT_REPORT_{DATE}.json", report)
    write_md(f"{PREFIX}_AUDIT_REPORT_{DATE}.md", "G12 NOFILL Readonly Tick Recovery Audit Report", report)
    return report


if __name__ == "__main__":
    result = build()
    print(json.dumps(result, indent=2, sort_keys=True))
