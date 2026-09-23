#!/usr/bin/env python3
"""Build concrete proxy geometry repair tables for runtime replay performance rows."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_repaired_proxy_runtime_replay_geometry_repair import (
    RUNTIME_REPLAY_GEOMETRY_REPAIR_SURFACE,
    aggregate_geometry_rows,
    geometry_repair_rows,
    missing_geometry_field_rows,
    research_boundary,
    system_geometry_rows,
)


PERF_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_PERFORMANCE"
NUMERIC_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_REPLAY_NUMERIC_EXECUTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_GEOMETRY_REPAIR"

PERFORMANCE_RESULT = ROUTE_DIR / f"{PERF_PREFIX}_RESULT_2026-05-17.json"
PERFORMANCE_ROW_LEDGER = ROUTE_DIR / f"{PERF_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
PERFORMANCE_AGGREGATE_LEDGER = ROUTE_DIR / f"{PERF_PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
REPLAY_NUMERIC_LEDGER = ROUTE_DIR / f"{NUMERIC_PREFIX}_REPLAY_NUMERIC_EVENT_LEDGER_2026-05-17.jsonl"
SOURCE_METRIC_LEDGER = ROUTE_DIR / f"{NUMERIC_PREFIX}_SOURCE_NUMERIC_METRIC_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_runtime_replay_geometry_repair.py"
INPUT_HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_runtime_replay_performance.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_repaired_proxy_runtime_replay_geometry_repair_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
ROW_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
PATH_SCAN_LEDGER = ROUTE_DIR / f"{PREFIX}_PATH_SCAN_LEDGER_2026-05-17.jsonl"
MISSING_FIELD_LEDGER = ROUTE_DIR / f"{PREFIX}_MISSING_GEOMETRY_FIELD_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"
OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"
ACTIVE_LEDGER = ROUTE_DIR / "ABSOLUTE_NORTH_STAR_ACTIVE_DOCTRINE_LEDGER_2026-05-15.md"


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def long_path(path: Path) -> str:
    text = str(path)
    if len(text) >= 240 and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def read_json(path: Path) -> dict[str, Any]:
    with open(long_path(path), "r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with open(long_path(path), "r", encoding="utf-8", errors="replace") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    with open(long_path(path), "w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with open(long_path(path), "w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_text(path: Path, text: str) -> None:
    with open(long_path(path), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(long_path(path), "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_by(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(field)) for row in rows).items()))


def manifest_entries() -> list[dict[str, str]]:
    entries = [
        (RESULT_PATH, "runtime_replay_geometry_repair_result"),
        (ROW_LEDGER, "runtime_replay_geometry_repair_row_ledger"),
        (AGGREGATE_LEDGER, "runtime_replay_geometry_repair_aggregate_ledger"),
        (PATH_SCAN_LEDGER, "runtime_replay_geometry_repair_path_scan_ledger"),
        (MISSING_FIELD_LEDGER, "runtime_replay_geometry_repair_missing_field_ledger"),
        (SYSTEM_LEDGER, "runtime_replay_geometry_repair_system_ledger"),
        (SUMMARY_PATH, "runtime_replay_geometry_repair_summary"),
        (BUILDER_MODULE, "runtime_replay_geometry_repair_builder"),
        (VERIFIER_MODULE, "runtime_replay_geometry_repair_verifier"),
        (HELPER_MODULE, "runtime_replay_geometry_repair_helper"),
    ]
    return [
        {
            "path": str(path.relative_to(REPO)).replace("\\", "/"),
            "status": "created",
            "type": kind,
        }
        for path, kind in entries
    ]


def update_manifest(generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    entries = manifest_entries()
    manifest.setdefault("artifacts", []).extend(entries)
    manifest["latest_branch_local_repaired_proxy_runtime_replay_geometry_repair"] = {
        "generated_utc": generated_at,
        "files": entries,
        "result": str(RESULT_PATH.relative_to(REPO)).replace("\\", "/"),
    }
    manifest["last_updated_utc"] = generated_at
    write_json(OUTPUT_MANIFEST, manifest)


def append_sprint_event(generated_at: str, counts: dict[str, Any]) -> None:
    event = {
        "checkpoint": 204,
        "event": "runtime_replay_geometry_repair",
        "generated_utc": generated_at,
        "geometry_repair_rows": counts["geometry_repair_rows"],
        "aggregate_geometry_rows": counts["aggregate_geometry_rows"],
        "path_scan_rows": counts["path_scan_rows"],
        "deterministic_geometry_r_rows": counts["deterministic_geometry_r_rows"],
        "ambiguous_rows": counts["ambiguous_rows"],
        "continuation": "consume deterministic geometry decisions into implementation or row-level intrabar replay tasks; do not open a new wrapper layer.",
        "boundary": research_boundary(),
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")


def append_active_checkpoint(generated_at: str, counts: dict[str, Any]) -> None:
    text = f"""
## Checkpoint 204 - Runtime Replay Geometry Repair

Generated: {generated_at}

Trigger: continuation after Checkpoint 203. Row-level performance rows were joined to replay numeric source metrics, then seven reachable source CSVs were streamed into proxy entry, target, stop, and path-order repair rows.

Rows:
- geometry repair rows: {counts['geometry_repair_rows']}
- aggregate geometry rows: {counts['aggregate_geometry_rows']}
- path scan rows: {counts['path_scan_rows']}
- deterministic geometry-R rows: {counts['deterministic_geometry_r_rows']}
- ambiguous rows: {counts['ambiguous_rows']}
- target-first / stop-first / neither: {counts['target_first_rows']} / {counts['stop_first_rows']} / {counts['neither_rows']}
- aggregate decisions: {counts['aggregate_decision_counts']}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: consume deterministic geometry decisions into implementation or row-level intrabar replay tasks; do not open a new wrapper layer.
"""
    with open(long_path(ACTIVE_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def build_summary(counts: dict[str, Any]) -> str:
    lines = [
        "# Runtime Replay Geometry Repair",
        "",
        "Checkpoint 204 streams reachable source CSVs to derive proxy entry, target, stop, and path-order repair rows for every Checkpoint 203 performance row.",
        "",
        "## Counts",
        "",
        f"- Geometry repair rows: `{counts['geometry_repair_rows']}`",
        f"- Aggregate geometry rows: `{counts['aggregate_geometry_rows']}`",
        f"- Source path scan rows: `{counts['path_scan_rows']}`",
        f"- Deterministic geometry-R rows: `{counts['deterministic_geometry_r_rows']}`",
        f"- Ambiguous rows: `{counts['ambiguous_rows']}`",
        f"- No-fill rows: `{counts['no_fill_rows']}`",
        f"- Target-first / stop-first / neither: `{counts['target_first_rows']}` / `{counts['stop_first_rows']}` / `{counts['neither_rows']}`",
        "",
        "## Aggregate Decisions",
        "",
    ]
    for decision, count in counts["aggregate_decision_counts"].items():
        lines.append(f"- `{decision}`: `{count}`")
    lines.extend(
        [
            "",
            "## Repair Boundary",
            "",
            "Rows use source-file first open as proxy entry and one-denominator proxy target/stop levels. Same-bar target/stop hits remain explicit intrabar-order repair tasks with source path, hash, key, and missing field retained.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    generated_at = now_utc()
    perf_result = read_json(PERFORMANCE_RESULT)
    perf_rows = read_jsonl(PERFORMANCE_ROW_LEDGER)
    perf_aggregates = read_jsonl(PERFORMANCE_AGGREGATE_LEDGER)
    replay_numeric_rows = read_jsonl(REPLAY_NUMERIC_LEDGER)
    source_metric_rows = read_jsonl(SOURCE_METRIC_LEDGER)

    rows, path_scans = geometry_repair_rows(perf_rows, replay_numeric_rows, source_metric_rows, REPO)
    aggregates = aggregate_geometry_rows(rows)
    missing_rows = missing_geometry_field_rows(rows)
    system_rows = system_geometry_rows(rows, aggregates, path_scans, missing_rows)

    counts = {
        "input_performance_result_ok": 1 if perf_result.get("ok") else 0,
        "input_performance_rows": len(perf_rows),
        "input_performance_aggregate_rows": len(perf_aggregates),
        "input_replay_numeric_rows": len(replay_numeric_rows),
        "input_source_metric_rows": len(source_metric_rows),
        "geometry_repair_rows": len(rows),
        "aggregate_geometry_rows": len(aggregates),
        "path_scan_rows": len(path_scans),
        "missing_geometry_field_rows": len(missing_rows),
        "system_geometry_rows": len(system_rows),
        "deterministic_geometry_r_rows": sum(row.get("action_adjusted_geometry_r") is not None for row in rows),
        "ambiguous_rows": sum(int(row.get("ambiguous_count") or 0) for row in rows),
        "no_fill_rows": sum(int(row.get("no_fill_count") or 0) for row in rows),
        "target_first_rows": sum(int(row.get("target_first_count") or 0) for row in rows),
        "stop_first_rows": sum(int(row.get("stop_first_count") or 0) for row in rows),
        "neither_rows": sum(int(row.get("neither_count") or 0) for row in rows),
        "geometry_repair_decision_counts": count_by(rows, "geometry_repair_decision"),
        "aggregate_decision_counts": count_by(aggregates, "geometry_keep_kill_redesign_implement_decision"),
        "path_order_counts": count_by(rows, "path_order_result"),
    }

    result = {
        "artifact": PREFIX,
        "ok": True,
        "generated_utc": generated_at,
        "runtime_replay_geometry_repair_surface": RUNTIME_REPLAY_GEOMETRY_REPAIR_SURFACE,
        "research_boundary": research_boundary(),
        "counts": counts,
        "inputs": {
            "performance_result": str(PERFORMANCE_RESULT.relative_to(REPO)).replace("\\", "/"),
            "performance_row_ledger": str(PERFORMANCE_ROW_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "replay_numeric_ledger": str(REPLAY_NUMERIC_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "source_metric_ledger": str(SOURCE_METRIC_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "row_ledger": str(ROW_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "path_scan_ledger": str(PATH_SCAN_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "missing_field_ledger": str(MISSING_FIELD_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
    }

    write_jsonl(ROW_LEDGER, rows)
    write_jsonl(AGGREGATE_LEDGER, aggregates)
    write_jsonl(PATH_SCAN_LEDGER, path_scans)
    write_jsonl(MISSING_FIELD_LEDGER, missing_rows)
    write_jsonl(SYSTEM_LEDGER, system_rows)
    write_json(RESULT_PATH, result)
    write_text(SUMMARY_PATH, build_summary(counts))
    update_manifest(generated_at)
    append_sprint_event(generated_at, counts)
    append_active_checkpoint(generated_at, counts)

    result["output_sha256"] = {
        "row_ledger_sha256": sha256_file(ROW_LEDGER),
        "aggregate_ledger_sha256": sha256_file(AGGREGATE_LEDGER),
        "path_scan_ledger_sha256": sha256_file(PATH_SCAN_LEDGER),
        "missing_field_ledger_sha256": sha256_file(MISSING_FIELD_LEDGER),
        "system_ledger_sha256": sha256_file(SYSTEM_LEDGER),
    }
    write_json(RESULT_PATH, result)
    print(json.dumps({"artifact": PREFIX, "counts": counts, "generated_utc": generated_at, "ok": True}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
