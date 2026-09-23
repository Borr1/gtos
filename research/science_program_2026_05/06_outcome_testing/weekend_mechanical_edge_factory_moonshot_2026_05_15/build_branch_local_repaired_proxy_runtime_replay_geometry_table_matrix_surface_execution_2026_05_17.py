#!/usr/bin/env python3
"""Execute branch-local matrix surfaces against held performance matrix rows."""

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

from src.research_infra.moonshot_repaired_proxy_runtime_replay_geometry_table_matrix_surface_execution import (
    RUNTIME_REPLAY_GEOMETRY_TABLE_MATRIX_SURFACE_EXECUTION_SURFACE,
    aggregate_execution_rows,
    execution_issue_rows,
    research_boundary,
    surface_execution_rows,
    system_execution_rows,
    terminal_execution_rows,
)


SURFACE_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_GEOMETRY_TABLE_MATRIX_SURFACES"
MATRIX_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_GEOMETRY_TABLE_PERFORMANCE_MATRIX"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_GEOMETRY_TABLE_MATRIX_SURFACE_EXECUTION"

SURFACE_RESULT = ROUTE_DIR / f"{SURFACE_PREFIX}_RESULT_2026-05-17.json"
SCORER_SURFACE_LEDGER = ROUTE_DIR / f"{SURFACE_PREFIX}_SCORER_SURFACE_LEDGER_2026-05-17.jsonl"
AVOID_SURFACE_LEDGER = ROUTE_DIR / f"{SURFACE_PREFIX}_AVOID_SURFACE_LEDGER_2026-05-17.jsonl"
TERMINAL_LEDGER = ROUTE_DIR / f"{SURFACE_PREFIX}_TERMINAL_DECISION_LEDGER_2026-05-17.jsonl"
MATRIX_LEDGER = ROUTE_DIR / f"{MATRIX_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_runtime_replay_geometry_table_matrix_surface_execution.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_repaired_proxy_runtime_replay_geometry_table_matrix_surface_execution_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
SURFACE_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SURFACE_EXECUTION_LEDGER_2026-05-17.jsonl"
TERMINAL_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_TERMINAL_EXECUTION_LEDGER_2026-05-17.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_ISSUE_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
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
        (RESULT_PATH, "runtime_replay_geometry_table_matrix_surface_execution_result"),
        (SURFACE_EXECUTION_LEDGER, "runtime_replay_geometry_table_matrix_surface_executions"),
        (TERMINAL_EXECUTION_LEDGER, "runtime_replay_geometry_table_matrix_terminal_executions"),
        (ISSUE_LEDGER, "runtime_replay_geometry_table_matrix_surface_execution_issues"),
        (AGGREGATE_LEDGER, "runtime_replay_geometry_table_matrix_surface_execution_aggregates"),
        (SYSTEM_LEDGER, "runtime_replay_geometry_table_matrix_surface_execution_system"),
        (SUMMARY_PATH, "runtime_replay_geometry_table_matrix_surface_execution_summary"),
        (BUILDER_MODULE, "runtime_replay_geometry_table_matrix_surface_execution_builder"),
        (VERIFIER_MODULE, "runtime_replay_geometry_table_matrix_surface_execution_verifier"),
        (HELPER_MODULE, "runtime_replay_geometry_table_matrix_surface_execution_helper"),
    ]
    return [
        {"path": str(path.relative_to(REPO)).replace("\\", "/"), "status": "created", "type": kind}
        for path, kind in entries
    ]


def update_manifest(generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    entries = manifest_entries()
    manifest.setdefault("artifacts", []).extend(entries)
    manifest["latest_branch_local_repaired_proxy_runtime_replay_geometry_table_matrix_surface_execution"] = {
        "generated_utc": generated_at,
        "files": entries,
        "result": str(RESULT_PATH.relative_to(REPO)).replace("\\", "/"),
    }
    manifest["last_updated_utc"] = generated_at
    write_json(OUTPUT_MANIFEST, manifest)


def append_sprint_event(generated_at: str, counts: dict[str, Any]) -> None:
    event = {
        "checkpoint": 215,
        "event": "runtime_replay_geometry_table_matrix_surface_execution",
        "generated_utc": generated_at,
        "surface_execution_rows": counts["surface_execution_rows"],
        "terminal_execution_rows": counts["terminal_execution_rows"],
        "execution_issue_rows": counts["execution_issue_rows"],
        "continuation": "consume matrix surface execution into final branch-local implementation bundle.",
        "boundary": research_boundary(),
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")


def append_active_checkpoint(generated_at: str, counts: dict[str, Any]) -> None:
    text = f"""
## Checkpoint 215 - Runtime Replay Geometry Table Matrix Surface Execution

Generated: {generated_at}

Trigger: continuation after Checkpoint 214. Matrix scorer and avoid surfaces were executed against the held performance matrix; terminal kill rows were preserved as terminal executions.

Rows:
- surface execution rows: {counts['surface_execution_rows']}
- terminal execution rows: {counts['terminal_execution_rows']}
- aggregate execution rows: {counts['aggregate_execution_rows']}
- execution issue rows: {counts['execution_issue_rows']}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: consume matrix surface execution into final branch-local implementation bundle.
"""
    with open(long_path(ACTIVE_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def build_summary(counts: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Runtime Replay Geometry Table Matrix Surface Execution",
            "",
            "Checkpoint 215 executes matrix surfaces against held performance rows and preserves terminal kill rows.",
            "",
            "## Counts",
            "",
            f"- Surface execution rows: `{counts['surface_execution_rows']}`",
            f"- Terminal execution rows: `{counts['terminal_execution_rows']}`",
            f"- Aggregate execution rows: `{counts['aggregate_execution_rows']}`",
            f"- Execution issue rows: `{counts['execution_issue_rows']}`",
            "",
            "## Status Counts",
            "",
            f"`{json.dumps(counts['execution_status_counts'], sort_keys=True)}`",
            "",
            "## Continuation",
            "",
            "Consume matrix surface execution into final branch-local implementation bundle.",
            "",
        ]
    )


def main() -> None:
    generated_at = now_utc()
    surface_result = read_json(SURFACE_RESULT)
    matrix_rows = read_jsonl(MATRIX_LEDGER)
    surface_rows = read_jsonl(SCORER_SURFACE_LEDGER) + read_jsonl(AVOID_SURFACE_LEDGER)
    terminal_rows = read_jsonl(TERMINAL_LEDGER)

    surface_exec = surface_execution_rows(surface_rows, matrix_rows)
    terminal_exec = terminal_execution_rows(terminal_rows, matrix_rows)
    issues = execution_issue_rows(surface_exec, terminal_exec)
    aggregates = aggregate_execution_rows(surface_exec, terminal_exec)
    system_rows = system_execution_rows(surface_exec, terminal_exec, issues, aggregates)
    all_exec = surface_exec + terminal_exec

    counts = {
        "input_surface_result_ok": 1 if surface_result.get("ok") else 0,
        "input_matrix_rows": len(matrix_rows),
        "input_surface_rows": len(surface_rows),
        "input_terminal_rows": len(terminal_rows),
        "surface_execution_rows": len(surface_exec),
        "terminal_execution_rows": len(terminal_exec),
        "total_execution_rows": len(all_exec),
        "aggregate_execution_rows": len(aggregates),
        "execution_issue_rows": len(issues),
        "system_rows": len(system_rows),
        "execution_status_counts": count_by(surface_exec, "surface_execution_status"),
        "terminal_execution_status_counts": count_by(terminal_exec, "terminal_execution_status"),
        "decision_counts": count_by(all_exec, "keep_kill_redesign_implement_decision"),
    }
    combined_status = Counter()
    for row in all_exec:
        combined_status[str(row.get("surface_execution_status") or row.get("terminal_execution_status"))] += 1
    counts["combined_execution_status_counts"] = dict(sorted(combined_status.items()))

    result = {
        "artifact": PREFIX,
        "ok": True,
        "generated_utc": generated_at,
        "runtime_replay_geometry_table_matrix_surface_execution_surface": (
            RUNTIME_REPLAY_GEOMETRY_TABLE_MATRIX_SURFACE_EXECUTION_SURFACE
        ),
        "research_boundary": research_boundary(),
        "counts": counts,
        "inputs": {
            "matrix_surface_result": str(SURFACE_RESULT.relative_to(REPO)).replace("\\", "/"),
            "matrix_ledger": str(MATRIX_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "scorer_surface_ledger": str(SCORER_SURFACE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "avoid_surface_ledger": str(AVOID_SURFACE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "terminal_decision_ledger": str(TERMINAL_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "surface_execution_ledger": str(SURFACE_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "terminal_execution_ledger": str(TERMINAL_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "issue_ledger": str(ISSUE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
    }

    write_jsonl(SURFACE_EXECUTION_LEDGER, surface_exec)
    write_jsonl(TERMINAL_EXECUTION_LEDGER, terminal_exec)
    write_jsonl(ISSUE_LEDGER, issues)
    write_jsonl(AGGREGATE_LEDGER, aggregates)
    write_jsonl(SYSTEM_LEDGER, system_rows)
    write_json(RESULT_PATH, result)
    write_text(SUMMARY_PATH, build_summary(counts))
    update_manifest(generated_at)
    append_sprint_event(generated_at, counts)
    append_active_checkpoint(generated_at, counts)

    result["output_sha256"] = {
        "surface_execution_ledger_sha256": sha256_file(SURFACE_EXECUTION_LEDGER),
        "terminal_execution_ledger_sha256": sha256_file(TERMINAL_EXECUTION_LEDGER),
        "issue_ledger_sha256": sha256_file(ISSUE_LEDGER),
        "aggregate_ledger_sha256": sha256_file(AGGREGATE_LEDGER),
        "system_ledger_sha256": sha256_file(SYSTEM_LEDGER),
    }
    write_json(RESULT_PATH, result)
    print(json.dumps({"artifact": PREFIX, "counts": counts, "generated_utc": generated_at, "ok": True}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
