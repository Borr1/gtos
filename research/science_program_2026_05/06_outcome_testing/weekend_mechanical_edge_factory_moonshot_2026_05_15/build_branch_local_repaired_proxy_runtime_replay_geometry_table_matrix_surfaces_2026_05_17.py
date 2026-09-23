#!/usr/bin/env python3
"""Build branch-local surfaces from the all-row replay performance matrix."""

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

from src.research_infra.moonshot_repaired_proxy_runtime_replay_geometry_table_matrix_surfaces import (
    RUNTIME_REPLAY_GEOMETRY_TABLE_MATRIX_SURFACES_SURFACE,
    aggregate_surface_rows,
    avoid_surface_rows,
    research_boundary,
    scorer_surface_rows,
    surface_self_test_rows,
    system_surface_rows,
    terminal_decision_rows,
)


MATRIX_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_GEOMETRY_TABLE_PERFORMANCE_MATRIX"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_GEOMETRY_TABLE_MATRIX_SURFACES"

MATRIX_RESULT = ROUTE_DIR / f"{MATRIX_PREFIX}_RESULT_2026-05-17.json"
MATRIX_LEDGER = ROUTE_DIR / f"{MATRIX_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_runtime_replay_geometry_table_matrix_surfaces.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_repaired_proxy_runtime_replay_geometry_table_matrix_surfaces_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
SCORER_SURFACE_LEDGER = ROUTE_DIR / f"{PREFIX}_SCORER_SURFACE_LEDGER_2026-05-17.jsonl"
AVOID_SURFACE_LEDGER = ROUTE_DIR / f"{PREFIX}_AVOID_SURFACE_LEDGER_2026-05-17.jsonl"
TERMINAL_LEDGER = ROUTE_DIR / f"{PREFIX}_TERMINAL_DECISION_LEDGER_2026-05-17.jsonl"
SELF_TEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SELF_TEST_LEDGER_2026-05-17.jsonl"
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
        (RESULT_PATH, "runtime_replay_geometry_table_matrix_surfaces_result"),
        (SCORER_SURFACE_LEDGER, "runtime_replay_geometry_table_matrix_scorer_surfaces"),
        (AVOID_SURFACE_LEDGER, "runtime_replay_geometry_table_matrix_avoid_surfaces"),
        (TERMINAL_LEDGER, "runtime_replay_geometry_table_matrix_terminal_decisions"),
        (SELF_TEST_LEDGER, "runtime_replay_geometry_table_matrix_surface_self_tests"),
        (AGGREGATE_LEDGER, "runtime_replay_geometry_table_matrix_surface_aggregates"),
        (SYSTEM_LEDGER, "runtime_replay_geometry_table_matrix_surfaces_system"),
        (SUMMARY_PATH, "runtime_replay_geometry_table_matrix_surfaces_summary"),
        (BUILDER_MODULE, "runtime_replay_geometry_table_matrix_surfaces_builder"),
        (VERIFIER_MODULE, "runtime_replay_geometry_table_matrix_surfaces_verifier"),
        (HELPER_MODULE, "runtime_replay_geometry_table_matrix_surfaces_helper"),
    ]
    return [
        {"path": str(path.relative_to(REPO)).replace("\\", "/"), "status": "created", "type": kind}
        for path, kind in entries
    ]


def update_manifest(generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    entries = manifest_entries()
    manifest.setdefault("artifacts", []).extend(entries)
    manifest["latest_branch_local_repaired_proxy_runtime_replay_geometry_table_matrix_surfaces"] = {
        "generated_utc": generated_at,
        "files": entries,
        "result": str(RESULT_PATH.relative_to(REPO)).replace("\\", "/"),
    }
    manifest["last_updated_utc"] = generated_at
    write_json(OUTPUT_MANIFEST, manifest)


def append_sprint_event(generated_at: str, counts: dict[str, Any]) -> None:
    event = {
        "checkpoint": 214,
        "event": "runtime_replay_geometry_table_matrix_surfaces",
        "generated_utc": generated_at,
        "scorer_surface_rows": counts["scorer_surface_rows"],
        "avoid_surface_rows": counts["avoid_surface_rows"],
        "terminal_decision_rows": counts["terminal_decision_rows"],
        "self_test_pass_rows": counts["self_test_pass_rows"],
        "continuation": "execute matrix surfaces against held performance rows and preserve terminal kill rows.",
        "boundary": research_boundary(),
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")


def append_active_checkpoint(generated_at: str, counts: dict[str, Any]) -> None:
    text = f"""
## Checkpoint 214 - Runtime Replay Geometry Table Matrix Surfaces

Generated: {generated_at}

Trigger: continuation after Checkpoint 213. All-row performance matrix decisions were materialized into branch-local scorer surfaces, avoid-intelligence surfaces, and terminal kill decisions.

Rows:
- scorer surface rows: {counts['scorer_surface_rows']}
- avoid surface rows: {counts['avoid_surface_rows']}
- terminal decision rows: {counts['terminal_decision_rows']}
- surface self-test rows: {counts['surface_self_test_rows']}
- self-test pass rows: {counts['self_test_pass_rows']}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: execute matrix surfaces against held performance rows and preserve terminal kill rows.
"""
    with open(long_path(ACTIVE_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def build_summary(counts: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Runtime Replay Geometry Table Matrix Surfaces",
            "",
            "Checkpoint 214 turns the all-row performance matrix into concrete branch-local implementation surfaces and terminal replay decisions.",
            "",
            "## Counts",
            "",
            f"- Scorer surface rows: `{counts['scorer_surface_rows']}`",
            f"- Avoid surface rows: `{counts['avoid_surface_rows']}`",
            f"- Terminal decision rows: `{counts['terminal_decision_rows']}`",
            f"- Surface self-test rows: `{counts['surface_self_test_rows']}`",
            f"- Self-test pass rows: `{counts['self_test_pass_rows']}`",
            f"- Aggregate rows: `{counts['aggregate_surface_rows']}`",
            "",
            "## Decision Counts",
            "",
            f"`{json.dumps(counts['decision_counts'], sort_keys=True)}`",
            "",
            "## Continuation",
            "",
            "Execute matrix surfaces against held performance rows and preserve terminal kill rows.",
            "",
        ]
    )


def main() -> None:
    generated_at = now_utc()
    matrix_result = read_json(MATRIX_RESULT)
    matrix_rows = read_jsonl(MATRIX_LEDGER)

    scorer_rows = scorer_surface_rows(matrix_rows)
    avoid_rows = avoid_surface_rows(matrix_rows)
    terminal_rows = terminal_decision_rows(matrix_rows)
    self_tests = surface_self_test_rows(scorer_rows + avoid_rows)
    aggregates = aggregate_surface_rows(scorer_rows, avoid_rows, terminal_rows, self_tests)
    system_rows = system_surface_rows(scorer_rows, avoid_rows, terminal_rows, self_tests, aggregates)

    counts = {
        "input_matrix_result_ok": 1 if matrix_result.get("ok") else 0,
        "input_matrix_rows": len(matrix_rows),
        "scorer_surface_rows": len(scorer_rows),
        "avoid_surface_rows": len(avoid_rows),
        "terminal_decision_rows": len(terminal_rows),
        "total_rows_consumed": len(scorer_rows) + len(avoid_rows) + len(terminal_rows),
        "surface_self_test_rows": len(self_tests),
        "self_test_pass_rows": sum(
            row.get("surface_self_test_status") == "PERFORMANCE_MATRIX_SURFACE_SELF_TEST_PASS"
            for row in self_tests
        ),
        "self_test_repair_rows": sum(
            row.get("surface_self_test_status") != "PERFORMANCE_MATRIX_SURFACE_SELF_TEST_PASS"
            for row in self_tests
        ),
        "aggregate_surface_rows": len(aggregates),
        "system_rows": len(system_rows),
        "decision_counts": count_by(scorer_rows + avoid_rows + terminal_rows, "keep_kill_redesign_implement_decision"),
        "surface_action_counts": count_by(scorer_rows + avoid_rows, "surface_action"),
        "terminal_action_counts": count_by(terminal_rows, "terminal_action"),
        "path_order_counts": count_by(scorer_rows + avoid_rows + terminal_rows, "path_order_result"),
    }

    result = {
        "artifact": PREFIX,
        "ok": True,
        "generated_utc": generated_at,
        "runtime_replay_geometry_table_matrix_surfaces_surface": (
            RUNTIME_REPLAY_GEOMETRY_TABLE_MATRIX_SURFACES_SURFACE
        ),
        "research_boundary": research_boundary(),
        "counts": counts,
        "inputs": {
            "performance_matrix_result": str(MATRIX_RESULT.relative_to(REPO)).replace("\\", "/"),
            "performance_matrix_ledger": str(MATRIX_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "scorer_surface_ledger": str(SCORER_SURFACE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "avoid_surface_ledger": str(AVOID_SURFACE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "terminal_decision_ledger": str(TERMINAL_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "self_test_ledger": str(SELF_TEST_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
    }

    write_jsonl(SCORER_SURFACE_LEDGER, scorer_rows)
    write_jsonl(AVOID_SURFACE_LEDGER, avoid_rows)
    write_jsonl(TERMINAL_LEDGER, terminal_rows)
    write_jsonl(SELF_TEST_LEDGER, self_tests)
    write_jsonl(AGGREGATE_LEDGER, aggregates)
    write_jsonl(SYSTEM_LEDGER, system_rows)
    write_json(RESULT_PATH, result)
    write_text(SUMMARY_PATH, build_summary(counts))
    update_manifest(generated_at)
    append_sprint_event(generated_at, counts)
    append_active_checkpoint(generated_at, counts)

    result["output_sha256"] = {
        "scorer_surface_ledger_sha256": sha256_file(SCORER_SURFACE_LEDGER),
        "avoid_surface_ledger_sha256": sha256_file(AVOID_SURFACE_LEDGER),
        "terminal_decision_ledger_sha256": sha256_file(TERMINAL_LEDGER),
        "self_test_ledger_sha256": sha256_file(SELF_TEST_LEDGER),
        "aggregate_ledger_sha256": sha256_file(AGGREGATE_LEDGER),
        "system_ledger_sha256": sha256_file(SYSTEM_LEDGER),
    }
    write_json(RESULT_PATH, result)
    print(json.dumps({"artifact": PREFIX, "counts": counts, "generated_utc": generated_at, "ok": True}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
