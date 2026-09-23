#!/usr/bin/env python3
"""Build concrete branch-local tables from geometry implementation candidates."""

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

from src.research_infra.moonshot_repaired_proxy_runtime_replay_geometry_tables import (
    RUNTIME_REPLAY_GEOMETRY_TABLES_SURFACE,
    avoid_intelligence_table_rows,
    kill_table_rows,
    redirection_task_rows,
    research_boundary,
    scorer_table_rows,
    system_table_rows,
)


IMPL_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_GEOMETRY_IMPLEMENTATION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_GEOMETRY_TABLES"

IMPLEMENTATION_RESULT = ROUTE_DIR / f"{IMPL_PREFIX}_RESULT_2026-05-17.json"
IMPLEMENTATION_ROW_LEDGER = ROUTE_DIR / f"{IMPL_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
IMPLEMENTATION_AGGREGATE_LEDGER = ROUTE_DIR / f"{IMPL_PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
IMPLEMENTATION_SELF_TEST_LEDGER = ROUTE_DIR / f"{IMPL_PREFIX}_SELF_TEST_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_runtime_replay_geometry_tables.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_repaired_proxy_runtime_replay_geometry_tables_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
SCORER_TABLE_LEDGER = ROUTE_DIR / f"{PREFIX}_SCORER_TABLE_LEDGER_2026-05-17.jsonl"
AVOID_TABLE_LEDGER = ROUTE_DIR / f"{PREFIX}_AVOID_INTELLIGENCE_TABLE_LEDGER_2026-05-17.jsonl"
KILL_TABLE_LEDGER = ROUTE_DIR / f"{PREFIX}_KILL_TABLE_LEDGER_2026-05-17.jsonl"
REDIRECTION_TASK_LEDGER = ROUTE_DIR / f"{PREFIX}_REDIRECTION_TASK_LEDGER_2026-05-17.jsonl"
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
        (RESULT_PATH, "runtime_replay_geometry_tables_result"),
        (SCORER_TABLE_LEDGER, "runtime_replay_geometry_scorer_table"),
        (AVOID_TABLE_LEDGER, "runtime_replay_geometry_avoid_table"),
        (KILL_TABLE_LEDGER, "runtime_replay_geometry_kill_table"),
        (REDIRECTION_TASK_LEDGER, "runtime_replay_geometry_redirection_tasks"),
        (SYSTEM_LEDGER, "runtime_replay_geometry_tables_system"),
        (SUMMARY_PATH, "runtime_replay_geometry_tables_summary"),
        (BUILDER_MODULE, "runtime_replay_geometry_tables_builder"),
        (VERIFIER_MODULE, "runtime_replay_geometry_tables_verifier"),
        (HELPER_MODULE, "runtime_replay_geometry_tables_helper"),
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
    manifest["latest_branch_local_repaired_proxy_runtime_replay_geometry_tables"] = {
        "generated_utc": generated_at,
        "files": entries,
        "result": str(RESULT_PATH.relative_to(REPO)).replace("\\", "/"),
    }
    manifest["last_updated_utc"] = generated_at
    write_json(OUTPUT_MANIFEST, manifest)


def append_sprint_event(generated_at: str, counts: dict[str, Any]) -> None:
    event = {
        "checkpoint": 206,
        "event": "runtime_replay_geometry_tables",
        "generated_utc": generated_at,
        "scorer_table_rows": counts["scorer_table_rows"],
        "avoid_intelligence_table_rows": counts["avoid_intelligence_table_rows"],
        "kill_table_rows": counts["kill_table_rows"],
        "redirection_task_rows": counts["redirection_task_rows"],
        "continuation": "execute scorer and avoid tables against held local replay rows or emit row-level source gaps.",
        "boundary": research_boundary(),
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")


def append_active_checkpoint(generated_at: str, counts: dict[str, Any]) -> None:
    text = f"""
## Checkpoint 206 - Runtime Replay Geometry Tables

Generated: {generated_at}

Trigger: continuation after Checkpoint 205. Branch-local implementation candidates were split into concrete scorer, avoid-intelligence, kill, and redirection task tables.

Rows:
- scorer table rows: {counts['scorer_table_rows']}
- avoid-intelligence table rows: {counts['avoid_intelligence_table_rows']}
- kill table rows: {counts['kill_table_rows']}
- redirection task rows: {counts['redirection_task_rows']}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: execute scorer and avoid tables against held local replay rows or emit row-level source gaps.
"""
    with open(long_path(ACTIVE_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def build_summary(counts: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Runtime Replay Geometry Tables",
            "",
            "Checkpoint 206 splits branch-local geometry implementation candidates into concrete scorer, avoid-intelligence, kill, and redirection task tables.",
            "",
            "## Counts",
            "",
            f"- Scorer table rows: `{counts['scorer_table_rows']}`",
            f"- Avoid-intelligence table rows: `{counts['avoid_intelligence_table_rows']}`",
            f"- Kill table rows: `{counts['kill_table_rows']}`",
            f"- Redirection task rows: `{counts['redirection_task_rows']}`",
            "",
            "## Continuation",
            "",
            "Execute scorer and avoid tables against held local replay rows or emit row-level source gaps.",
            "",
        ]
    )


def main() -> None:
    generated_at = now_utc()
    impl_result = read_json(IMPLEMENTATION_RESULT)
    impl_rows = read_jsonl(IMPLEMENTATION_ROW_LEDGER)
    aggregate_rows = read_jsonl(IMPLEMENTATION_AGGREGATE_LEDGER)
    self_test_rows = read_jsonl(IMPLEMENTATION_SELF_TEST_LEDGER)

    scorer_rows = scorer_table_rows(impl_rows)
    avoid_rows = avoid_intelligence_table_rows(impl_rows)
    kill_rows = kill_table_rows(impl_rows)
    redirection_rows = redirection_task_rows(aggregate_rows)
    system_rows = system_table_rows(scorer_rows, avoid_rows, kill_rows, redirection_rows)

    counts = {
        "input_implementation_result_ok": 1 if impl_result.get("ok") else 0,
        "input_implementation_rows": len(impl_rows),
        "input_aggregate_implementation_rows": len(aggregate_rows),
        "input_self_test_rows": len(self_test_rows),
        "scorer_table_rows": len(scorer_rows),
        "avoid_intelligence_table_rows": len(avoid_rows),
        "kill_table_rows": len(kill_rows),
        "redirection_task_rows": len(redirection_rows),
        "system_rows": len(system_rows),
        "table_application_status_counts": count_by(
            scorer_rows + avoid_rows + kill_rows + redirection_rows,
            "table_application_status",
        ),
    }

    result = {
        "artifact": PREFIX,
        "ok": True,
        "generated_utc": generated_at,
        "runtime_replay_geometry_tables_surface": RUNTIME_REPLAY_GEOMETRY_TABLES_SURFACE,
        "research_boundary": research_boundary(),
        "counts": counts,
        "inputs": {
            "implementation_result": str(IMPLEMENTATION_RESULT.relative_to(REPO)).replace("\\", "/"),
            "implementation_row_ledger": str(IMPLEMENTATION_ROW_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "implementation_aggregate_ledger": str(IMPLEMENTATION_AGGREGATE_LEDGER.relative_to(REPO)).replace(
                "\\",
                "/",
            ),
            "implementation_self_test_ledger": str(IMPLEMENTATION_SELF_TEST_LEDGER.relative_to(REPO)).replace(
                "\\",
                "/",
            ),
        },
        "outputs": {
            "scorer_table_ledger": str(SCORER_TABLE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "avoid_intelligence_table_ledger": str(AVOID_TABLE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "kill_table_ledger": str(KILL_TABLE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "redirection_task_ledger": str(REDIRECTION_TASK_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
    }

    write_jsonl(SCORER_TABLE_LEDGER, scorer_rows)
    write_jsonl(AVOID_TABLE_LEDGER, avoid_rows)
    write_jsonl(KILL_TABLE_LEDGER, kill_rows)
    write_jsonl(REDIRECTION_TASK_LEDGER, redirection_rows)
    write_jsonl(SYSTEM_LEDGER, system_rows)
    write_json(RESULT_PATH, result)
    write_text(SUMMARY_PATH, build_summary(counts))
    update_manifest(generated_at)
    append_sprint_event(generated_at, counts)
    append_active_checkpoint(generated_at, counts)

    result["output_sha256"] = {
        "scorer_table_sha256": sha256_file(SCORER_TABLE_LEDGER),
        "avoid_table_sha256": sha256_file(AVOID_TABLE_LEDGER),
        "kill_table_sha256": sha256_file(KILL_TABLE_LEDGER),
        "redirection_task_sha256": sha256_file(REDIRECTION_TASK_LEDGER),
        "system_ledger_sha256": sha256_file(SYSTEM_LEDGER),
    }
    write_json(RESULT_PATH, result)
    print(json.dumps({"artifact": PREFIX, "counts": counts, "generated_utc": generated_at, "ok": True}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
