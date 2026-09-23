#!/usr/bin/env python3
"""Build held-replay executions for concrete geometry scorer and avoid tables."""

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

from src.research_infra.moonshot_repaired_proxy_runtime_replay_geometry_table_execution import (
    RUNTIME_REPLAY_GEOMETRY_TABLE_EXECUTION_SURFACE,
    aggregate_table_execution_rows,
    avoid_table_execution_rows,
    research_boundary,
    scorer_table_execution_rows,
    source_gap_rows,
    system_table_execution_rows,
)


TABLE_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_GEOMETRY_TABLES"
IMPL_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_GEOMETRY_IMPLEMENTATION"
GEOM_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_GEOMETRY_REPAIR"
PERF_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_PERFORMANCE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_GEOMETRY_TABLE_EXECUTION"

TABLE_RESULT = ROUTE_DIR / f"{TABLE_PREFIX}_RESULT_2026-05-17.json"
SCORER_TABLE_LEDGER = ROUTE_DIR / f"{TABLE_PREFIX}_SCORER_TABLE_LEDGER_2026-05-17.jsonl"
AVOID_TABLE_LEDGER = ROUTE_DIR / f"{TABLE_PREFIX}_AVOID_INTELLIGENCE_TABLE_LEDGER_2026-05-17.jsonl"
IMPLEMENTATION_ROW_LEDGER = ROUTE_DIR / f"{IMPL_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
GEOMETRY_ROW_LEDGER = ROUTE_DIR / f"{GEOM_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
PERFORMANCE_ROW_LEDGER = ROUTE_DIR / f"{PERF_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_runtime_replay_geometry_table_execution.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_repaired_proxy_runtime_replay_geometry_table_execution_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
SCORER_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SCORER_EXECUTION_LEDGER_2026-05-17.jsonl"
AVOID_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_AVOID_EXECUTION_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
SOURCE_GAP_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_GAP_LEDGER_2026-05-17.jsonl"
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
        (RESULT_PATH, "runtime_replay_geometry_table_execution_result"),
        (SCORER_EXECUTION_LEDGER, "runtime_replay_geometry_scorer_table_execution"),
        (AVOID_EXECUTION_LEDGER, "runtime_replay_geometry_avoid_table_execution"),
        (AGGREGATE_LEDGER, "runtime_replay_geometry_table_execution_aggregates"),
        (SOURCE_GAP_LEDGER, "runtime_replay_geometry_table_execution_source_gaps"),
        (SYSTEM_LEDGER, "runtime_replay_geometry_table_execution_system"),
        (SUMMARY_PATH, "runtime_replay_geometry_table_execution_summary"),
        (BUILDER_MODULE, "runtime_replay_geometry_table_execution_builder"),
        (VERIFIER_MODULE, "runtime_replay_geometry_table_execution_verifier"),
        (HELPER_MODULE, "runtime_replay_geometry_table_execution_helper"),
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
    manifest["latest_branch_local_repaired_proxy_runtime_replay_geometry_table_execution"] = {
        "generated_utc": generated_at,
        "files": entries,
        "result": str(RESULT_PATH.relative_to(REPO)).replace("\\", "/"),
    }
    manifest["last_updated_utc"] = generated_at
    write_json(OUTPUT_MANIFEST, manifest)


def append_sprint_event(generated_at: str, counts: dict[str, Any]) -> None:
    event = {
        "checkpoint": 207,
        "event": "runtime_replay_geometry_table_execution",
        "generated_utc": generated_at,
        "scorer_table_execution_rows": counts["scorer_table_execution_rows"],
        "avoid_table_execution_rows": counts["avoid_table_execution_rows"],
        "aggregate_table_execution_rows": counts["aggregate_table_execution_rows"],
        "source_gap_rows": counts["source_gap_rows"],
        "continuation": "consume held-replay table execution results into branch-local scorer and avoid observations with row-level source gaps closed or preserved.",
        "boundary": research_boundary(),
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")


def append_active_checkpoint(generated_at: str, counts: dict[str, Any]) -> None:
    text = f"""
## Checkpoint 207 - Runtime Replay Geometry Table Execution

Generated: {generated_at}

Trigger: continuation after Checkpoint 206. Concrete scorer and avoid-intelligence tables were executed against held local replay geometry rows.

Rows:
- scorer table execution rows: {counts['scorer_table_execution_rows']}
- avoid table execution rows: {counts['avoid_table_execution_rows']}
- aggregate table execution rows: {counts['aggregate_table_execution_rows']}
- source gap rows: {counts['source_gap_rows']}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: consume held-replay table execution results into branch-local scorer and avoid observations with row-level source gaps closed or preserved.
"""
    with open(long_path(ACTIVE_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def build_summary(counts: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Runtime Replay Geometry Table Execution",
            "",
            "Checkpoint 207 executes concrete geometry scorer and avoid tables against held local replay geometry.",
            "",
            "## Counts",
            "",
            f"- Scorer table execution rows: `{counts['scorer_table_execution_rows']}`",
            f"- Avoid table execution rows: `{counts['avoid_table_execution_rows']}`",
            f"- Aggregate table execution rows: `{counts['aggregate_table_execution_rows']}`",
            f"- Source gap rows: `{counts['source_gap_rows']}`",
            f"- Joined replay geometry rows: `{counts['joined_replay_geometry_rows']}`",
            "",
            "## Continuation",
            "",
            "Consume held-replay table execution results into branch-local scorer and avoid observations with row-level source gaps closed or preserved.",
            "",
        ]
    )


def main() -> None:
    generated_at = now_utc()
    table_result = read_json(TABLE_RESULT)
    scorer_table_rows = read_jsonl(SCORER_TABLE_LEDGER)
    avoid_table_rows = read_jsonl(AVOID_TABLE_LEDGER)
    implementation_rows = read_jsonl(IMPLEMENTATION_ROW_LEDGER)
    geometry_rows = read_jsonl(GEOMETRY_ROW_LEDGER)
    performance_rows = read_jsonl(PERFORMANCE_ROW_LEDGER)

    scorer_exec_rows = scorer_table_execution_rows(
        scorer_table_rows,
        implementation_rows,
        geometry_rows,
        performance_rows,
    )
    avoid_exec_rows = avoid_table_execution_rows(
        avoid_table_rows,
        implementation_rows,
        geometry_rows,
        performance_rows,
    )
    all_exec_rows = scorer_exec_rows + avoid_exec_rows
    gap_rows = source_gap_rows(all_exec_rows)
    aggregate_rows = aggregate_table_execution_rows(all_exec_rows)
    system_rows = system_table_execution_rows(scorer_exec_rows, avoid_exec_rows, aggregate_rows, gap_rows)

    counts = {
        "input_table_result_ok": 1 if table_result.get("ok") else 0,
        "input_scorer_table_rows": len(scorer_table_rows),
        "input_avoid_table_rows": len(avoid_table_rows),
        "input_implementation_rows": len(implementation_rows),
        "input_geometry_rows": len(geometry_rows),
        "input_performance_rows": len(performance_rows),
        "scorer_table_execution_rows": len(scorer_exec_rows),
        "avoid_table_execution_rows": len(avoid_exec_rows),
        "total_table_execution_rows": len(all_exec_rows),
        "aggregate_table_execution_rows": len(aggregate_rows),
        "source_gap_rows": len(gap_rows),
        "system_rows": len(system_rows),
        "joined_replay_geometry_rows": sum(
            1 for row in all_exec_rows if row.get("source_join_status") == "HELD_REPLAY_GEOMETRY_JOINED"
        ),
        "table_execution_class_counts": count_by(all_exec_rows, "table_execution_class"),
        "table_execution_decision_counts": count_by(all_exec_rows, "table_execution_decision"),
        "aggregate_table_execution_decision_counts": count_by(aggregate_rows, "table_execution_decision"),
    }

    result = {
        "artifact": PREFIX,
        "ok": True,
        "generated_utc": generated_at,
        "runtime_replay_geometry_table_execution_surface": RUNTIME_REPLAY_GEOMETRY_TABLE_EXECUTION_SURFACE,
        "research_boundary": research_boundary(),
        "counts": counts,
        "inputs": {
            "table_result": str(TABLE_RESULT.relative_to(REPO)).replace("\\", "/"),
            "scorer_table_ledger": str(SCORER_TABLE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "avoid_table_ledger": str(AVOID_TABLE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "implementation_row_ledger": str(IMPLEMENTATION_ROW_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "geometry_row_ledger": str(GEOMETRY_ROW_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "performance_row_ledger": str(PERFORMANCE_ROW_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "scorer_execution_ledger": str(SCORER_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "avoid_execution_ledger": str(AVOID_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "source_gap_ledger": str(SOURCE_GAP_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
    }

    write_jsonl(SCORER_EXECUTION_LEDGER, scorer_exec_rows)
    write_jsonl(AVOID_EXECUTION_LEDGER, avoid_exec_rows)
    write_jsonl(AGGREGATE_LEDGER, aggregate_rows)
    write_jsonl(SOURCE_GAP_LEDGER, gap_rows)
    write_jsonl(SYSTEM_LEDGER, system_rows)
    write_json(RESULT_PATH, result)
    write_text(SUMMARY_PATH, build_summary(counts))
    update_manifest(generated_at)
    append_sprint_event(generated_at, counts)
    append_active_checkpoint(generated_at, counts)

    result["output_sha256"] = {
        "scorer_execution_sha256": sha256_file(SCORER_EXECUTION_LEDGER),
        "avoid_execution_sha256": sha256_file(AVOID_EXECUTION_LEDGER),
        "aggregate_ledger_sha256": sha256_file(AGGREGATE_LEDGER),
        "source_gap_ledger_sha256": sha256_file(SOURCE_GAP_LEDGER),
        "system_ledger_sha256": sha256_file(SYSTEM_LEDGER),
    }
    write_json(RESULT_PATH, result)
    print(json.dumps({"artifact": PREFIX, "counts": counts, "generated_utc": generated_at, "ok": True}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
