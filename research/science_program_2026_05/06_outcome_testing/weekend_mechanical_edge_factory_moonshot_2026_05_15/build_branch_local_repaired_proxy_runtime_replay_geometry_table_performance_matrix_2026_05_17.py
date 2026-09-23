#!/usr/bin/env python3
"""Build all-row replay performance matrix after geometry table recommendations."""

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

from src.research_infra.moonshot_repaired_proxy_runtime_replay_geometry_table_performance_matrix import (
    RUNTIME_REPLAY_GEOMETRY_TABLE_PERFORMANCE_MATRIX_SURFACE,
    aggregate_matrix_rows,
    performance_matrix_rows,
    research_boundary,
    simulated_missing_field_rows,
    source_join_issue_rows,
    system_matrix_rows,
)


PERF_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_PERFORMANCE"
GEOM_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_GEOMETRY_REPAIR"
REC_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_GEOMETRY_TABLE_RECOMMENDATIONS"
UNIFIED_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_RECOMMENDATION_MERGE_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_GEOMETRY_TABLE_PERFORMANCE_MATRIX"

PERF_RESULT = ROUTE_DIR / f"{PERF_PREFIX}_RESULT_2026-05-17.json"
PERF_LEDGER = ROUTE_DIR / f"{PERF_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
GEOM_RESULT = ROUTE_DIR / f"{GEOM_PREFIX}_RESULT_2026-05-17.json"
GEOM_LEDGER = ROUTE_DIR / f"{GEOM_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
REC_RESULT = ROUTE_DIR / f"{REC_PREFIX}_RESULT_2026-05-17.json"
REC_LEDGER = ROUTE_DIR / f"{REC_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
UNIFIED_LEDGER = ROUTE_DIR / f"{UNIFIED_PREFIX}_UNIFIED_CANDIDATE_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_runtime_replay_geometry_table_performance_matrix.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_repaired_proxy_runtime_replay_geometry_table_performance_matrix_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
MATRIX_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
MISSING_FIELD_LEDGER = ROUTE_DIR / f"{PREFIX}_SIMULATED_MISSING_FIELD_LEDGER_2026-05-17.jsonl"
JOIN_ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_JOIN_ISSUE_LEDGER_2026-05-17.jsonl"
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
        (RESULT_PATH, "runtime_replay_geometry_table_performance_matrix_result"),
        (MATRIX_LEDGER, "runtime_replay_geometry_table_performance_matrix_rows"),
        (AGGREGATE_LEDGER, "runtime_replay_geometry_table_performance_matrix_aggregates"),
        (MISSING_FIELD_LEDGER, "runtime_replay_geometry_table_performance_matrix_missing_simulated_fields"),
        (JOIN_ISSUE_LEDGER, "runtime_replay_geometry_table_performance_matrix_source_join_issues"),
        (SYSTEM_LEDGER, "runtime_replay_geometry_table_performance_matrix_system"),
        (SUMMARY_PATH, "runtime_replay_geometry_table_performance_matrix_summary"),
        (BUILDER_MODULE, "runtime_replay_geometry_table_performance_matrix_builder"),
        (VERIFIER_MODULE, "runtime_replay_geometry_table_performance_matrix_verifier"),
        (HELPER_MODULE, "runtime_replay_geometry_table_performance_matrix_helper"),
    ]
    return [
        {"path": str(path.relative_to(REPO)).replace("\\", "/"), "status": "created", "type": kind}
        for path, kind in entries
    ]


def update_manifest(generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    entries = manifest_entries()
    manifest.setdefault("artifacts", []).extend(entries)
    manifest["latest_branch_local_repaired_proxy_runtime_replay_geometry_table_performance_matrix"] = {
        "generated_utc": generated_at,
        "files": entries,
        "result": str(RESULT_PATH.relative_to(REPO)).replace("\\", "/"),
    }
    manifest["last_updated_utc"] = generated_at
    write_json(OUTPUT_MANIFEST, manifest)


def append_sprint_event(generated_at: str, counts: dict[str, Any]) -> None:
    event = {
        "checkpoint": 213,
        "event": "runtime_replay_geometry_table_performance_matrix",
        "generated_utc": generated_at,
        "matrix_rows": counts["matrix_rows"],
        "aggregate_rows": counts["aggregate_rows"],
        "rows_with_simulated_r": counts["rows_with_simulated_r"],
        "rows_without_simulated_r": counts["rows_without_simulated_r"],
        "source_join_issue_rows": counts["source_join_issue_rows"],
        "continuation": "use all-row matrix decisions for concrete branch-local scorer and avoid implementation surfaces.",
        "boundary": research_boundary(),
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")


def append_active_checkpoint(generated_at: str, counts: dict[str, Any]) -> None:
    text = f"""
## Checkpoint 213 - Runtime Replay Geometry Table Performance Matrix

Generated: {generated_at}

Trigger: continuation after Checkpoint 212. Performance rows, deterministic replay geometry, retained geometry-table recommendations, and sanitized broader branch-local recommendation scope counts were merged into one all-row replay performance decision matrix.

Rows:
- matrix rows: {counts['matrix_rows']}
- aggregate rows: {counts['aggregate_rows']}
- rows with simulated R: {counts['rows_with_simulated_r']}
- rows without simulated R: {counts['rows_without_simulated_r']}
- source join issue rows: {counts['source_join_issue_rows']}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: use all-row matrix decisions for concrete branch-local scorer and avoid implementation surfaces.
"""
    with open(long_path(ACTIVE_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def build_summary(counts: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Runtime Replay Geometry Table Performance Matrix",
            "",
            "Checkpoint 213 preserves every executed performance row and attaches deterministic replay geometry, retained table recommendations, and sanitized broader recommendation scope counts.",
            "",
            "## Counts",
            "",
            f"- Matrix rows: `{counts['matrix_rows']}`",
            f"- Aggregate rows: `{counts['aggregate_rows']}`",
            f"- Rows with simulated R: `{counts['rows_with_simulated_r']}`",
            f"- Rows without simulated R: `{counts['rows_without_simulated_r']}`",
            f"- Simulated missing-field rows: `{counts['simulated_missing_field_rows']}`",
            f"- Source join issue rows: `{counts['source_join_issue_rows']}`",
            "",
            "## Decision Counts",
            "",
            f"`{json.dumps(counts['decision_counts'], sort_keys=True)}`",
            "",
            "## Continuation",
            "",
            "Use all-row matrix decisions for concrete branch-local scorer and avoid implementation surfaces.",
            "",
        ]
    )


def main() -> None:
    generated_at = now_utc()
    perf_result = read_json(PERF_RESULT)
    geom_result = read_json(GEOM_RESULT)
    rec_result = read_json(REC_RESULT)
    perf_rows = read_jsonl(PERF_LEDGER)
    geom_rows = read_jsonl(GEOM_LEDGER)
    rec_rows = read_jsonl(REC_LEDGER)
    unified_rows = read_jsonl(UNIFIED_LEDGER)

    rows = performance_matrix_rows(perf_rows, geom_rows, rec_rows, unified_rows)
    aggregates = aggregate_matrix_rows(rows)
    missing_rows = simulated_missing_field_rows(rows)
    join_rows = source_join_issue_rows(rows)
    system_rows = system_matrix_rows(rows, aggregates, missing_rows, join_rows)

    counts = {
        "input_performance_result_ok": 1 if perf_result.get("ok") else 0,
        "input_geometry_result_ok": 1 if geom_result.get("ok") else 0,
        "input_recommendation_result_ok": 1 if rec_result.get("ok") else 0,
        "input_performance_rows": len(perf_rows),
        "input_geometry_rows": len(geom_rows),
        "input_recommendation_rows": len(rec_rows),
        "input_broader_inventory_rows": len(unified_rows),
        "matrix_rows": len(rows),
        "aggregate_rows": len(aggregates),
        "simulated_missing_field_rows": len(missing_rows),
        "source_join_issue_rows": len(join_rows),
        "system_rows": len(system_rows),
        "rows_with_simulated_r": sum(row.get("cost_adjusted_simulated_r") is not None for row in rows),
        "rows_without_simulated_r": sum(row.get("cost_adjusted_simulated_r") is None for row in rows),
        "rows_with_table_recommendation": sum(bool(row.get("input_geometry_table_recommendation_row_id")) for row in rows),
        "rows_without_table_recommendation": sum(not row.get("input_geometry_table_recommendation_row_id") for row in rows),
        "decision_counts": count_by(rows, "keep_kill_redesign_implement_decision"),
        "aggregate_decision_counts": count_by(aggregates, "keep_kill_redesign_implement_decision"),
        "path_order_counts": count_by(rows, "path_order_result"),
        "broader_scope_status_counts": count_by(rows, "broader_recommendation_scope_status"),
    }

    result = {
        "artifact": PREFIX,
        "ok": True,
        "generated_utc": generated_at,
        "runtime_replay_geometry_table_performance_matrix_surface": (
            RUNTIME_REPLAY_GEOMETRY_TABLE_PERFORMANCE_MATRIX_SURFACE
        ),
        "research_boundary": research_boundary(),
        "counts": counts,
        "inputs": {
            "performance_result": str(PERF_RESULT.relative_to(REPO)).replace("\\", "/"),
            "performance_ledger": str(PERF_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "geometry_result": str(GEOM_RESULT.relative_to(REPO)).replace("\\", "/"),
            "geometry_ledger": str(GEOM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "recommendation_result": str(REC_RESULT.relative_to(REPO)).replace("\\", "/"),
            "recommendation_ledger": str(REC_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "broader_inventory_ledger": str(UNIFIED_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "matrix_ledger": str(MATRIX_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "simulated_missing_field_ledger": str(MISSING_FIELD_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "source_join_issue_ledger": str(JOIN_ISSUE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
    }

    write_jsonl(MATRIX_LEDGER, rows)
    write_jsonl(AGGREGATE_LEDGER, aggregates)
    write_jsonl(MISSING_FIELD_LEDGER, missing_rows)
    write_jsonl(JOIN_ISSUE_LEDGER, join_rows)
    write_jsonl(SYSTEM_LEDGER, system_rows)
    write_json(RESULT_PATH, result)
    write_text(SUMMARY_PATH, build_summary(counts))
    update_manifest(generated_at)
    append_sprint_event(generated_at, counts)
    append_active_checkpoint(generated_at, counts)

    result["output_sha256"] = {
        "matrix_ledger_sha256": sha256_file(MATRIX_LEDGER),
        "aggregate_ledger_sha256": sha256_file(AGGREGATE_LEDGER),
        "simulated_missing_field_ledger_sha256": sha256_file(MISSING_FIELD_LEDGER),
        "source_join_issue_ledger_sha256": sha256_file(JOIN_ISSUE_LEDGER),
        "system_ledger_sha256": sha256_file(SYSTEM_LEDGER),
    }
    write_json(RESULT_PATH, result)
    print(json.dumps({"artifact": PREFIX, "counts": counts, "generated_utc": generated_at, "ok": True}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
