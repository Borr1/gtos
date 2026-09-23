#!/usr/bin/env python3
"""Materialize deduped SOURCE exact-acquisition windows from local same-resource roots."""

from __future__ import annotations

import csv
import hashlib
import json
from bisect import bisect_left
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]

SOURCE_DETAIL_RESULT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_COST_CAP_ACQUISITION_DETAIL_RESULT_2026-05-16.json"
SOURCE_DETAIL_BRANCH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_COST_CAP_ACQUISITION_DETAIL_BRANCH_LEDGER_2026-05-16.jsonl"
SOURCE_DETAIL_WINDOW = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_COST_CAP_ACQUISITION_DETAIL_WINDOW_LEDGER_2026-05-16.jsonl"
SOURCE_DETAIL_SUPPORT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_COST_CAP_ACQUISITION_DETAIL_SUPPORT_LEDGER_2026-05-16.jsonl"

PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_WINDOW_MATERIALIZATION"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-16.json"
WINDOW_LEDGER = ROUTE_DIR / f"{PREFIX}_WINDOW_LEDGER_2026-05-16.jsonl"
CANDIDATE_LEDGER = ROUTE_DIR / f"{PREFIX}_CANDIDATE_FILE_LEDGER_2026-05-16.jsonl"
BRANCH_JOIN_LEDGER = ROUTE_DIR / f"{PREFIX}_BRANCH_JOIN_LEDGER_2026-05-16.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"{PREFIX}_QUESTION_LEDGER_2026-05-16.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

ROOTS = [
    REPO / "data",
    REPO / "exports",
    REPO / "shadow_logs",
]

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "SOURCE window materialization packet only. It deduplicates SOURCE exact-acquisition "
    "requirements by source_window_key, searches owned local same-resource roots, hashes "
    "found files, and classifies bar/spread proxy availability. It does not change live "
    "behavior and does not claim broker R/PnL, realized expectancy, win-rate, validation, "
    "live-readiness, or promotion."
)

HASH_CACHE: dict[Path, str | None] = {}
CSV_INDEX_CACHE: dict[Path, dict[str, Any]] = {}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"{path}:{line_no}: {exc}") from exc
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def sha256_file(path: Path) -> str | None:
    if path in HASH_CACHE:
        return HASH_CACHE[path]
    if not path.exists():
        HASH_CACHE[path] = None
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    HASH_CACHE[path] = digest.hexdigest()
    return HASH_CACHE[path]


def source_manifest_rows(paths: list[Path], generated_at: str) -> tuple[list[dict[str, Any]], str]:
    rows = []
    for index, path in enumerate(paths, 1):
        rows.append(
            {
                "source_manifest_id": f"OHLC-GTOS-SRC-WINDOW-MAT-SRC-{index:04d}",
                "path": path.relative_to(REPO).as_posix(),
                "sha256": sha256_file(path),
                "status": "HASHED" if path.exists() else "MISSING",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
            }
        )
    manifest_hash = hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest()
    return rows, manifest_hash


def parse_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    text = text.replace("Z", "+00:00")
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            dt = datetime.strptime(text, fmt)
            if dt.tzinfo is not None:
                dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
            return dt
        except ValueError:
            continue
    try:
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    except ValueError:
        return None


def infer_timeframe(path: Path) -> str:
    upper = path.name.upper()
    for tf in ("M15", "M5", "M1", "H4", "H1", "D1"):
        if f"_{tf}" in upper or upper.endswith(f"{tf}.CSV"):
            return tf
    return "UNKNOWN"


def candidate_files(symbols: set[str]) -> list[Path]:
    paths: list[Path] = []
    suffixes = (".csv", ".parquet", ".jsonl")
    for root in ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in suffixes:
                continue
            upper = path.name.upper()
            if any(symbol.upper() in upper for symbol in symbols):
                paths.append(path)
    return sorted(paths)


def load_csv_index(path: Path) -> dict[str, Any]:
    if path in CSV_INDEX_CACHE:
        return CSV_INDEX_CACHE[path]
    first_time: str | None = None
    last_time: str | None = None
    has_spread_column = False
    has_ohlc_columns = False
    indexed_rows: list[tuple[datetime, float | None]] = []
    try:
        with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                index = {"index_status": "CSV_NO_HEADER"}
                CSV_INDEX_CACHE[path] = index
                return index
            fields = {field.lower(): field for field in reader.fieldnames}
            time_field = fields.get("time") or fields.get("datetime") or fields.get("timestamp")
            spread_field = fields.get("spread")
            has_spread_column = spread_field is not None
            has_ohlc_columns = all(name in fields for name in ("open", "high", "low", "close"))
            if not time_field:
                index = {
                    "index_status": "CSV_NO_TIME_COLUMN",
                    "has_spread_column": has_spread_column,
                    "has_ohlc_columns": has_ohlc_columns,
                }
                CSV_INDEX_CACHE[path] = index
                return index
            for row in reader:
                row_time = parse_dt(row.get(time_field))
                if row_time is None:
                    continue
                first_time = first_time or row.get(time_field)
                last_time = row.get(time_field)
                spread_value = None
                if spread_field and row.get(spread_field) not in (None, ""):
                    try:
                        spread_value = float(row[spread_field])
                    except ValueError:
                        spread_value = None
                indexed_rows.append((row_time, spread_value))
    except OSError as exc:
        index = {"index_status": f"CSV_READ_ERROR:{exc.__class__.__name__}"}
        CSV_INDEX_CACHE[path] = index
        return index
    indexed_rows.sort(key=lambda item: item[0])
    index = {
        "index_status": "CSV_INDEXED",
        "first_time": first_time,
        "last_time": last_time,
        "has_spread_column": has_spread_column,
        "has_ohlc_columns": has_ohlc_columns,
        "indexed_rows": indexed_rows,
        "indexed_time_count": len(indexed_rows),
        "times": [item[0] for item in indexed_rows],
    }
    CSV_INDEX_CACHE[path] = index
    return index


def scan_csv_file(path: Path, start: datetime, reference: datetime, end: datetime) -> dict[str, Any]:
    index = load_csv_index(path)
    if index.get("index_status") != "CSV_INDEXED":
        return {
            "scan_status": index.get("index_status"),
            "has_spread_column": index.get("has_spread_column", False),
            "has_ohlc_columns": index.get("has_ohlc_columns", False),
        }
    times = index["times"]
    rows = index["indexed_rows"]
    start_index = bisect_left(times, start)
    end_index = bisect_left(times, end)
    reference_start = bisect_left(times, reference)
    reference_end = bisect_left(times, reference.replace(microsecond=999999))
    window_slice = rows[start_index:end_index]
    reference_slice = rows[reference_start:reference_end]
    spread_values = [spread for _time, spread in window_slice if spread is not None]
    reference_spread_values = [spread for _time, spread in reference_slice if spread is not None]
    return {
        "scan_status": "CSV_SCANNED",
        "first_time": index.get("first_time"),
        "last_time": index.get("last_time"),
        "has_spread_column": index.get("has_spread_column", False),
        "has_ohlc_columns": index.get("has_ohlc_columns", False),
        "indexed_time_count": index.get("indexed_time_count"),
        "window_rows": len(window_slice),
        "exact_reference_rows": len(reference_slice),
        "spread_values_seen": len(spread_values),
        "spread_min": min(spread_values) if spread_values else None,
        "spread_max": max(spread_values) if spread_values else None,
        "spread_at_reference_values_seen": len(reference_spread_values),
        "spread_at_reference_available": bool(reference_spread_values),
    }


def materialization_status(candidates: list[dict[str, Any]]) -> str:
    if any(row.get("exact_reference_rows", 0) > 0 and row.get("has_spread_column") for row in candidates):
        return "BAR_REFERENCE_WITH_SPREAD_PROXY_MATERIALIZED"
    if any(row.get("window_rows", 0) > 0 and row.get("has_spread_column") for row in candidates):
        return "BAR_WINDOW_WITH_SPREAD_PROXY_MATERIALIZED"
    if any(row.get("window_rows", 0) > 0 for row in candidates):
        return "BAR_WINDOW_OHLC_ONLY_MATERIALIZED"
    return "NO_LOCAL_SAME_RESOURCE_BAR_SOURCE_FOUND"


def recompute_state(status: str) -> str:
    if status == "BAR_REFERENCE_WITH_SPREAD_PROXY_MATERIALIZED":
        return "BAR_SPREAD_PROXY_MATERIALIZED_EXACT_TICK_STILL_UNAVAILABLE"
    if status in {"BAR_WINDOW_WITH_SPREAD_PROXY_MATERIALIZED", "BAR_WINDOW_OHLC_ONLY_MATERIALIZED"}:
        return "LOCAL_BAR_PROXY_MATERIALIZED_EXACT_TICK_STILL_UNAVAILABLE"
    return "FAIL_CLOSED_LOW_HIGH_STRESS_ONLY"


def window_scope(branches: list[dict[str, Any]], source_rows: list[dict[str, Any]]) -> str:
    branch_statuses = {row.get("branch_result_binary") for row in branches}
    has_unmatched = any(row.get("source_detail_window_scope") == "SOURCE_DETAIL_UNMATCHED_WINDOW_CONTEXT" for row in source_rows)
    if branch_statuses == {"ACCEPTED"} and not has_unmatched:
        return "ACCEPTED_WINDOW"
    if branch_statuses == {"REJECTED"} and not has_unmatched:
        return "REPAIR_WINDOW"
    if branch_statuses:
        return "MIXED_WINDOW"
    return "UNMATCHED_SIDECAR_WINDOW"


def compact_counter(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): int(counter[key]) for key in sorted(counter, key=lambda item: str(item))}


def main() -> int:
    generated_at = now_utc()
    source_detail_result = read_json(SOURCE_DETAIL_RESULT)
    branch_rows = read_jsonl(SOURCE_DETAIL_BRANCH)
    window_rows = read_jsonl(SOURCE_DETAIL_WINDOW)
    support_rows = read_jsonl(SOURCE_DETAIL_SUPPORT)
    branch_by_id = {row["branch_queue_id"]: row for row in branch_rows if row.get("branch_queue_id")}
    windows_by_key: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in window_rows:
        windows_by_key[str(row["source_window_key"])].append(row)
    support_by_key: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in support_rows:
        if row.get("source_window_key"):
            support_by_key[str(row["source_window_key"])].append(row)
    symbols = {row.get("symbol") for row in window_rows if row.get("symbol")}
    local_candidates = candidate_files({str(symbol) for symbol in symbols})
    source_manifest, manifest_hash = source_manifest_rows(
        [SOURCE_DETAIL_RESULT, SOURCE_DETAIL_BRANCH, SOURCE_DETAIL_WINDOW, SOURCE_DETAIL_SUPPORT] + local_candidates,
        generated_at,
    )

    window_materialization_rows: list[dict[str, Any]] = []
    candidate_rows: list[dict[str, Any]] = []
    branch_join_rows: list[dict[str, Any]] = []
    bucket_counters: dict[str, Counter[Any]] = defaultdict(Counter)
    for source_window_key, rows_for_key in sorted(windows_by_key.items()):
        symbol = rows_for_key[0].get("symbol")
        reference = parse_dt(rows_for_key[0].get("reference_time_utc"))
        start = parse_dt(rows_for_key[0].get("extract_start_utc"))
        end = parse_dt(rows_for_key[0].get("extract_end_utc"))
        matched_branch_ids = sorted({branch_id for row in rows_for_key for branch_id in row.get("matched_source_detail_branches", [])})
        matched_branches = [branch_by_id[branch_id] for branch_id in matched_branch_ids if branch_id in branch_by_id]
        key_candidates = [path for path in local_candidates if symbol and str(symbol).upper() in path.name.upper()]
        scanned_rows = []
        for path in key_candidates:
            if path.suffix.lower() != ".csv" or not start or not reference or not end:
                scan = {
                    "scan_status": "NON_CSV_OR_BAD_TIME_SKIPPED",
                    "window_rows": 0,
                    "exact_reference_rows": 0,
                    "has_spread_column": False,
                    "has_ohlc_columns": False,
                }
            else:
                scan = scan_csv_file(path, start, reference, end)
            candidate = {
                "source_window_candidate_id": f"OHLC-GTOS-SRC-WINDOW-MAT-CAND-{len(candidate_rows) + 1:05d}",
                "source_window_key": source_window_key,
                "symbol": symbol,
                "reference_time_utc": rows_for_key[0].get("reference_time_utc"),
                "extract_start_utc": rows_for_key[0].get("extract_start_utc"),
                "extract_end_utc": rows_for_key[0].get("extract_end_utc"),
                "candidate_path": path.relative_to(REPO).as_posix(),
                "candidate_sha256": sha256_file(path),
                "candidate_timeframe": infer_timeframe(path),
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "not_completion": True,
                "generated_utc": generated_at,
                "source_manifest_hash": manifest_hash,
                **scan,
            }
            candidate_rows.append(candidate)
            scanned_rows.append(candidate)
        status = materialization_status(scanned_rows)
        exact_reference_file_count = sum(1 for row in scanned_rows if row.get("exact_reference_rows", 0) > 0)
        window_row_file_count = sum(1 for row in scanned_rows if row.get("window_rows", 0) > 0)
        spread_proxy_file_count = sum(1 for row in scanned_rows if row.get("window_rows", 0) > 0 and row.get("has_spread_column"))
        best = next((row for row in scanned_rows if row.get("exact_reference_rows", 0) > 0 and row.get("has_spread_column")), None)
        best = best or next((row for row in scanned_rows if row.get("window_rows", 0) > 0), None)
        scope = window_scope(matched_branches, rows_for_key)
        accepted_branch_count = sum(1 for row in matched_branches if row.get("branch_result_binary") == "ACCEPTED")
        repair_branch_count = sum(1 for row in matched_branches if row.get("branch_result_binary") == "REJECTED")
        row_out = {
            "source_window_materialization_id": f"OHLC-GTOS-SRC-WINDOW-MAT-WINDOW-{len(window_materialization_rows) + 1:05d}",
            "source_window_key": source_window_key,
            "symbol": symbol,
            "reference_time_utc": rows_for_key[0].get("reference_time_utc"),
            "source_time_utc": rows_for_key[0].get("source_time_utc"),
            "extract_start_utc": rows_for_key[0].get("extract_start_utc"),
            "extract_end_utc": rows_for_key[0].get("extract_end_utc"),
            "source_window_input_rows": len(rows_for_key),
            "support_rows_for_window": len(support_by_key.get(source_window_key, [])),
            "matched_source_detail_branch_count": len(matched_branch_ids),
            "accepted_branch_count": accepted_branch_count,
            "repair_branch_count": repair_branch_count,
            "window_scope_class": scope,
            "candidate_file_count": len(key_candidates),
            "exact_reference_file_count": exact_reference_file_count,
            "window_row_file_count": window_row_file_count,
            "spread_proxy_file_count": spread_proxy_file_count,
            "materialization_status": status,
            "source_descriptor_recompute_state": recompute_state(status),
            "best_candidate_path": best.get("candidate_path") if best else None,
            "best_candidate_timeframe": best.get("candidate_timeframe") if best else None,
            "best_candidate_window_rows": best.get("window_rows") if best else None,
            "best_candidate_exact_reference_rows": best.get("exact_reference_rows") if best else None,
            "best_candidate_spread_min": best.get("spread_min") if best else None,
            "best_candidate_spread_max": best.get("spread_max") if best else None,
            "next_same_resource_action": (
                "RECOMPUTE_DESCRIPTOR_WITH_BAR_SPREAD_PROXY_AND_KEEP_TICK_EXACT_GAP"
                if status == "BAR_REFERENCE_WITH_SPREAD_PROXY_MATERIALIZED"
                else "PRESERVE_LOW_HIGH_STRESS_ONLY_AND_KEEP_SOURCE_ACQUISITION_REQUIREMENT"
            ),
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
            "not_completion": True,
            "generated_utc": generated_at,
            "source_manifest_hash": manifest_hash,
        }
        window_materialization_rows.append(row_out)
        for branch in matched_branches:
            branch_join_rows.append(
                {
                    "source_window_branch_join_id": f"OHLC-GTOS-SRC-WINDOW-MAT-BRANCH-{len(branch_join_rows) + 1:05d}",
                    "source_window_key": source_window_key,
                    "branch_queue_id": branch.get("branch_queue_id"),
                    "branch_result_binary": branch.get("branch_result_binary"),
                    "source_cost_cap_detail_status": branch.get("source_cost_cap_detail_status"),
                    "source_cost_interval_sign_class": branch.get("source_cost_interval_sign_class"),
                    "window_scope_class": scope,
                    "materialization_status": status,
                    "source_descriptor_recompute_state": recompute_state(status),
                    "route_candidate_id": branch.get("route_candidate_id"),
                    "symbol": branch.get("symbol"),
                    "route_session": branch.get("route_session"),
                    "side": branch.get("side"),
                    "entry_variant": branch.get("entry_variant"),
                    "target_stop_contract_id": branch.get("target_stop_contract_id"),
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "not_completion": True,
                    "generated_utc": generated_at,
                    "source_manifest_hash": manifest_hash,
                }
            )
        for category in [
            "symbol",
            "window_scope_class",
            "materialization_status",
            "source_descriptor_recompute_state",
            "next_same_resource_action",
        ]:
            bucket_counters[category][row_out.get(category)] += 1
    for row in candidate_rows:
        bucket_counters["candidate_timeframe"][row.get("candidate_timeframe")] += 1
        bucket_counters["candidate_scan_status"][row.get("scan_status")] += 1
        if row.get("window_rows", 0) > 0:
            bucket_counters["candidate_window_hit_timeframe"][row.get("candidate_timeframe")] += 1

    bucket_rows = []
    for category, counter in sorted(bucket_counters.items()):
        total = sum(counter.values())
        for bucket, count in sorted(counter.items(), key=lambda item: str(item[0])):
            bucket_rows.append(
                {
                    "bucket_id": f"OHLC-GTOS-SRC-WINDOW-MAT-BUCKET-{len(bucket_rows) + 1:05d}",
                    "bucket_category": category,
                    "bucket": str(bucket),
                    "row_count": int(count),
                    "share": round(count / total, 9) if total else None,
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                    "source_manifest_hash": manifest_hash,
                }
            )
    question_rows = [
        {"question_id": "OHLC-GTOS-SRC-WINDOW-MAT-QUESTION-001", "question": "Which deduped source windows have local bar-spread proxy materialized?", "answer_route": "Use window ledger materialization_status and best_candidate fields."},
        {"question_id": "OHLC-GTOS-SRC-WINDOW-MAT-QUESTION-002", "question": "Which source windows remain exact tick fail-closed after local root search?", "answer_route": "All materialized bar proxies still carry source_descriptor_recompute_state exact tick unavailable unless a tick file appears."},
        {"question_id": "OHLC-GTOS-SRC-WINDOW-MAT-QUESTION-003", "question": "Which windows mix accepted and repair branches?", "answer_route": "Use window_scope_class and branch join ledger."},
        {"question_id": "OHLC-GTOS-SRC-WINDOW-MAT-QUESTION-004", "question": "What next computation follows materialized SOURCE windows?", "answer_route": "Recompute source descriptors with bar-spread proxy where exact reference spread exists, then continue M1/M15 detail builders."},
    ]
    for row in question_rows:
        row.update({"safe_flags": SAFE_FLAGS, "claim_boundary": CLAIM_BOUNDARY, "not_completion": True, "generated_utc": generated_at, "source_manifest_hash": manifest_hash})

    result = {
        "artifact": RESULT_PATH.name,
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_WINDOW_MATERIALIZATION",
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "counts": {
            "input_source_detail_branch_rows": len(branch_rows),
            "input_source_detail_window_rows": len(window_rows),
            "input_source_detail_support_rows": len(support_rows),
            "unique_source_window_rows": len(window_materialization_rows),
            "candidate_file_rows": len(candidate_rows),
            "branch_join_rows": len(branch_join_rows),
            "bucket_rows": len(bucket_rows),
            "question_rows": len(question_rows),
            "source_manifest_rows": len(source_manifest),
        },
        "upstream_source_detail_counts": source_detail_result.get("counts", {}),
        "bucket_distributions": {category: compact_counter(counter) for category, counter in sorted(bucket_counters.items())},
        "system_decision": {
            "system_recommendation": (
                "SOURCE_WINDOW_MATERIALIZATION_RESULT: use local bar-spread proxy rows where "
                "reference bars exist, keep exact tick source gap explicit, and continue M1/M15 "
                "detail builders while preserving low/high stress-only status for windows without "
                "exact tick materialization."
            ),
            "unique_source_window_rows": len(window_materialization_rows),
            "bar_reference_spread_proxy_windows": int(bucket_counters["materialization_status"]["BAR_REFERENCE_WITH_SPREAD_PROXY_MATERIALIZED"]),
            "fail_closed_low_high_only_windows": int(bucket_counters["source_descriptor_recompute_state"]["FAIL_CLOSED_LOW_HIGH_STRESS_ONLY"]),
            "candidate_file_rows": len(candidate_rows),
        },
        "source_manifest_hash": manifest_hash,
    }

    outputs = [
        (WINDOW_LEDGER, window_materialization_rows),
        (CANDIDATE_LEDGER, candidate_rows),
        (BRANCH_JOIN_LEDGER, branch_join_rows),
        (BUCKET_LEDGER, bucket_rows),
        (QUESTION_LEDGER, question_rows),
        (SOURCE_MANIFEST_LEDGER, source_manifest),
    ]
    for path, rows in outputs:
        write_jsonl(path, rows)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    SUMMARY_PATH.write_text(
        "\n".join(
            [
                "# Historical OHLC GTOS Replay Branch SOURCE Window Materialization",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                CLAIM_BOUNDARY,
                "",
                f"- Unique source windows: `{len(window_materialization_rows)}`",
                f"- Candidate file rows scanned: `{len(candidate_rows)}`",
                f"- Branch join rows: `{len(branch_join_rows)}`",
            ]
        ),
        encoding="utf-8",
    )
    manifest = read_json(OUTPUT_MANIFEST) if OUTPUT_MANIFEST.exists() else {"schema": "weekend_mechanical_edge_factory_output_manifest_v1", "artifacts": []}
    output_paths = [RESULT_PATH, SUMMARY_PATH] + [path for path, _rows in outputs]
    path_strings = {path.relative_to(REPO).as_posix() for path in output_paths}
    manifest["artifacts"] = [item for item in manifest.get("artifacts", []) if item.get("path") not in path_strings]
    for path in output_paths:
        manifest["artifacts"].append(
            {
                "path": path.relative_to(REPO).as_posix(),
                "status": "created",
                "type": "branch_source_window_materialization",
                "generated_utc": generated_at,
                "counts": result["counts"],
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    manifest["safe_flags"] = SAFE_FLAGS
    OUTPUT_MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "timestamp_utc": generated_at,
                    "event_type": "branch_source_window_materialization_built",
                    "route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H",
                    "artifact": RESULT_PATH.relative_to(REPO).as_posix(),
                    "counts": result["counts"],
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "not_completion": True,
                },
                sort_keys=True,
            )
            + "\n"
        )
    print(json.dumps({"ok": True, "counts": result["counts"], "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
