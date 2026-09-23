#!/usr/bin/env python3
"""Build executable branch-local code surfaces from geometry table code candidates."""

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

from src.research_infra.moonshot_repaired_proxy_runtime_replay_geometry_table_code_surfaces import (
    RUNTIME_REPLAY_GEOMETRY_TABLE_CODE_SURFACES_SURFACE,
    aggregate_code_surface_rows,
    avoid_code_surface_rows,
    research_boundary,
    scorer_code_surface_rows,
    surface_self_test_rows,
    system_code_surface_rows,
)


CAND_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_GEOMETRY_TABLE_CODE_CANDIDATES"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_GEOMETRY_TABLE_CODE_SURFACES"

CAND_RESULT = ROUTE_DIR / f"{CAND_PREFIX}_RESULT_2026-05-17.json"
SCORER_CANDIDATE_LEDGER = ROUTE_DIR / f"{CAND_PREFIX}_SCORER_CODE_CANDIDATE_LEDGER_2026-05-17.jsonl"
AVOID_CANDIDATE_LEDGER = ROUTE_DIR / f"{CAND_PREFIX}_AVOID_CODE_CANDIDATE_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_runtime_replay_geometry_table_code_surfaces.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_repaired_proxy_runtime_replay_geometry_table_code_surfaces_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
SCORER_SURFACE_LEDGER = ROUTE_DIR / f"{PREFIX}_SCORER_SURFACE_LEDGER_2026-05-17.jsonl"
AVOID_SURFACE_LEDGER = ROUTE_DIR / f"{PREFIX}_AVOID_SURFACE_LEDGER_2026-05-17.jsonl"
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
        (RESULT_PATH, "runtime_replay_geometry_table_code_surfaces_result"),
        (SCORER_SURFACE_LEDGER, "runtime_replay_geometry_scorer_code_surfaces"),
        (AVOID_SURFACE_LEDGER, "runtime_replay_geometry_avoid_code_surfaces"),
        (SELF_TEST_LEDGER, "runtime_replay_geometry_code_surface_self_tests"),
        (AGGREGATE_LEDGER, "runtime_replay_geometry_code_surface_aggregates"),
        (SYSTEM_LEDGER, "runtime_replay_geometry_code_surfaces_system"),
        (SUMMARY_PATH, "runtime_replay_geometry_code_surfaces_summary"),
        (BUILDER_MODULE, "runtime_replay_geometry_code_surfaces_builder"),
        (VERIFIER_MODULE, "runtime_replay_geometry_code_surfaces_verifier"),
        (HELPER_MODULE, "runtime_replay_geometry_code_surfaces_helper"),
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
    manifest["latest_branch_local_repaired_proxy_runtime_replay_geometry_table_code_surfaces"] = {
        "generated_utc": generated_at,
        "files": entries,
        "result": str(RESULT_PATH.relative_to(REPO)).replace("\\", "/"),
    }
    manifest["last_updated_utc"] = generated_at
    write_json(OUTPUT_MANIFEST, manifest)


def append_sprint_event(generated_at: str, counts: dict[str, Any]) -> None:
    event = {
        "checkpoint": 210,
        "event": "runtime_replay_geometry_table_code_surfaces",
        "generated_utc": generated_at,
        "scorer_code_surface_rows": counts["scorer_code_surface_rows"],
        "avoid_code_surface_rows": counts["avoid_code_surface_rows"],
        "surface_self_test_rows": counts["surface_self_test_rows"],
        "self_test_pass_rows": counts["self_test_pass_rows"],
        "continuation": "execute branch-local code surfaces against candidate observations and preserve pass/fail rows.",
        "boundary": research_boundary(),
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")


def append_active_checkpoint(generated_at: str, counts: dict[str, Any]) -> None:
    text = f"""
## Checkpoint 210 - Runtime Replay Geometry Table Code Surfaces

Generated: {generated_at}

Trigger: continuation after Checkpoint 209. Retained code candidates were materialized as executable branch-local scorer and avoid code surfaces with self-tests.

Rows:
- scorer code surface rows: {counts['scorer_code_surface_rows']}
- avoid code surface rows: {counts['avoid_code_surface_rows']}
- surface self-test rows: {counts['surface_self_test_rows']}
- self-test pass rows: {counts['self_test_pass_rows']}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: execute branch-local code surfaces against candidate observations and preserve pass/fail rows.
"""
    with open(long_path(ACTIVE_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def build_summary(counts: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Runtime Replay Geometry Table Code Surfaces",
            "",
            "Checkpoint 210 materializes retained scorer and avoid code candidates as executable branch-local code surfaces.",
            "",
            "## Counts",
            "",
            f"- Scorer code surface rows: `{counts['scorer_code_surface_rows']}`",
            f"- Avoid code surface rows: `{counts['avoid_code_surface_rows']}`",
            f"- Surface self-test rows: `{counts['surface_self_test_rows']}`",
            f"- Self-test pass rows: `{counts['self_test_pass_rows']}`",
            "",
            "## Continuation",
            "",
            "Execute branch-local code surfaces against candidate observations and preserve pass/fail rows.",
            "",
        ]
    )


def main() -> None:
    generated_at = now_utc()
    cand_result = read_json(CAND_RESULT)
    scorer_candidate_rows = read_jsonl(SCORER_CANDIDATE_LEDGER)
    avoid_candidate_rows = read_jsonl(AVOID_CANDIDATE_LEDGER)

    scorer_rows = scorer_code_surface_rows(scorer_candidate_rows)
    avoid_rows = avoid_code_surface_rows(avoid_candidate_rows)
    all_rows = scorer_rows + avoid_rows
    self_tests = surface_self_test_rows(all_rows)
    aggregate_rows = aggregate_code_surface_rows(all_rows, self_tests)
    system_rows = system_code_surface_rows(scorer_rows, avoid_rows, self_tests, aggregate_rows)

    counts = {
        "input_candidate_result_ok": 1 if cand_result.get("ok") else 0,
        "input_scorer_code_candidate_rows": len(scorer_candidate_rows),
        "input_avoid_code_candidate_rows": len(avoid_candidate_rows),
        "scorer_code_surface_rows": len(scorer_rows),
        "avoid_code_surface_rows": len(avoid_rows),
        "total_code_surface_rows": len(all_rows),
        "surface_self_test_rows": len(self_tests),
        "self_test_pass_rows": sum(
            1 for row in self_tests if row.get("surface_self_test_status") == "GEOMETRY_CODE_SURFACE_SELF_TEST_PASS"
        ),
        "self_test_repair_rows": sum(
            1 for row in self_tests if row.get("surface_self_test_status") != "GEOMETRY_CODE_SURFACE_SELF_TEST_PASS"
        ),
        "aggregate_code_surface_rows": len(aggregate_rows),
        "system_rows": len(system_rows),
        "surface_action_counts": count_by(all_rows, "surface_action"),
        "surface_self_test_status_counts": count_by(self_tests, "surface_self_test_status"),
        "aggregate_code_surface_action_counts": count_by(aggregate_rows, "aggregate_code_surface_action"),
    }

    result = {
        "artifact": PREFIX,
        "ok": True,
        "generated_utc": generated_at,
        "runtime_replay_geometry_table_code_surfaces_surface": RUNTIME_REPLAY_GEOMETRY_TABLE_CODE_SURFACES_SURFACE,
        "research_boundary": research_boundary(),
        "counts": counts,
        "inputs": {
            "candidate_result": str(CAND_RESULT.relative_to(REPO)).replace("\\", "/"),
            "scorer_code_candidate_ledger": str(SCORER_CANDIDATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "avoid_code_candidate_ledger": str(AVOID_CANDIDATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "scorer_surface_ledger": str(SCORER_SURFACE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "avoid_surface_ledger": str(AVOID_SURFACE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "self_test_ledger": str(SELF_TEST_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
    }

    write_jsonl(SCORER_SURFACE_LEDGER, scorer_rows)
    write_jsonl(AVOID_SURFACE_LEDGER, avoid_rows)
    write_jsonl(SELF_TEST_LEDGER, self_tests)
    write_jsonl(AGGREGATE_LEDGER, aggregate_rows)
    write_jsonl(SYSTEM_LEDGER, system_rows)
    write_json(RESULT_PATH, result)
    write_text(SUMMARY_PATH, build_summary(counts))
    update_manifest(generated_at)
    append_sprint_event(generated_at, counts)
    append_active_checkpoint(generated_at, counts)

    result["output_sha256"] = {
        "scorer_surface_sha256": sha256_file(SCORER_SURFACE_LEDGER),
        "avoid_surface_sha256": sha256_file(AVOID_SURFACE_LEDGER),
        "self_test_sha256": sha256_file(SELF_TEST_LEDGER),
        "aggregate_ledger_sha256": sha256_file(AGGREGATE_LEDGER),
        "system_ledger_sha256": sha256_file(SYSTEM_LEDGER),
    }
    write_json(RESULT_PATH, result)
    print(json.dumps({"artifact": PREFIX, "counts": counts, "generated_utc": generated_at, "ok": True}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
