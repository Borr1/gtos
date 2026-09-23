#!/usr/bin/env python3
"""Execute branch-local geometry table code surfaces against observations."""

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

from src.research_infra.moonshot_repaired_proxy_runtime_replay_geometry_table_code_surface_execution import (
    RUNTIME_REPLAY_GEOMETRY_TABLE_CODE_SURFACE_EXECUTION_SURFACE,
    aggregate_code_surface_execution_rows,
    code_surface_execution_rows,
    execution_issue_rows,
    research_boundary,
    system_code_surface_execution_rows,
)


SURF_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_GEOMETRY_TABLE_CODE_SURFACES"
OBS_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_GEOMETRY_TABLE_OBSERVATIONS"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_GEOMETRY_TABLE_CODE_SURFACE_EXECUTION"

SURFACE_RESULT = ROUTE_DIR / f"{SURF_PREFIX}_RESULT_2026-05-17.json"
SCORER_SURFACE_LEDGER = ROUTE_DIR / f"{SURF_PREFIX}_SCORER_SURFACE_LEDGER_2026-05-17.jsonl"
AVOID_SURFACE_LEDGER = ROUTE_DIR / f"{SURF_PREFIX}_AVOID_SURFACE_LEDGER_2026-05-17.jsonl"
SCORER_OBSERVATION_LEDGER = ROUTE_DIR / f"{OBS_PREFIX}_SCORER_OBSERVATION_LEDGER_2026-05-17.jsonl"
AVOID_OBSERVATION_LEDGER = ROUTE_DIR / f"{OBS_PREFIX}_AVOID_OBSERVATION_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_runtime_replay_geometry_table_code_surface_execution.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_repaired_proxy_runtime_replay_geometry_table_code_surface_execution_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_EXECUTION_LEDGER_2026-05-17.jsonl"
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
        (RESULT_PATH, "runtime_replay_geometry_code_surface_execution_result"),
        (EXECUTION_LEDGER, "runtime_replay_geometry_code_surface_execution"),
        (ISSUE_LEDGER, "runtime_replay_geometry_code_surface_execution_issues"),
        (AGGREGATE_LEDGER, "runtime_replay_geometry_code_surface_execution_aggregates"),
        (SYSTEM_LEDGER, "runtime_replay_geometry_code_surface_execution_system"),
        (SUMMARY_PATH, "runtime_replay_geometry_code_surface_execution_summary"),
        (BUILDER_MODULE, "runtime_replay_geometry_code_surface_execution_builder"),
        (VERIFIER_MODULE, "runtime_replay_geometry_code_surface_execution_verifier"),
        (HELPER_MODULE, "runtime_replay_geometry_code_surface_execution_helper"),
    ]
    return [
        {"path": str(path.relative_to(REPO)).replace("\\", "/"), "status": "created", "type": kind}
        for path, kind in entries
    ]


def update_manifest(generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    entries = manifest_entries()
    manifest.setdefault("artifacts", []).extend(entries)
    manifest["latest_branch_local_repaired_proxy_runtime_replay_geometry_table_code_surface_execution"] = {
        "generated_utc": generated_at,
        "files": entries,
        "result": str(RESULT_PATH.relative_to(REPO)).replace("\\", "/"),
    }
    manifest["last_updated_utc"] = generated_at
    write_json(OUTPUT_MANIFEST, manifest)


def append_sprint_event(generated_at: str, counts: dict[str, Any]) -> None:
    event = {
        "checkpoint": 211,
        "event": "runtime_replay_geometry_table_code_surface_execution",
        "generated_utc": generated_at,
        "code_surface_execution_rows": counts["code_surface_execution_rows"],
        "code_surface_execution_issue_rows": counts["code_surface_execution_issue_rows"],
        "aggregate_code_surface_execution_rows": counts["aggregate_code_surface_execution_rows"],
        "continuation": "consume code-surface execution rows into decisive branch-local scorer and avoid recommendations.",
        "boundary": research_boundary(),
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")


def append_active_checkpoint(generated_at: str, counts: dict[str, Any]) -> None:
    text = f"""
## Checkpoint 211 - Runtime Replay Geometry Table Code Surface Execution

Generated: {generated_at}

Trigger: continuation after Checkpoint 210. Branch-local code surfaces were executed against their source observations.

Rows:
- code surface execution rows: {counts['code_surface_execution_rows']}
- code surface execution issue rows: {counts['code_surface_execution_issue_rows']}
- aggregate code surface execution rows: {counts['aggregate_code_surface_execution_rows']}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: consume code-surface execution rows into decisive branch-local scorer and avoid recommendations.
"""
    with open(long_path(ACTIVE_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def build_summary(counts: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Runtime Replay Geometry Table Code Surface Execution",
            "",
            "Checkpoint 211 executes branch-local code surfaces against their source observations.",
            "",
            "## Counts",
            "",
            f"- Code surface execution rows: `{counts['code_surface_execution_rows']}`",
            f"- Code surface execution issue rows: `{counts['code_surface_execution_issue_rows']}`",
            f"- Aggregate code surface execution rows: `{counts['aggregate_code_surface_execution_rows']}`",
            "",
            "## Continuation",
            "",
            "Consume code-surface execution rows into decisive branch-local scorer and avoid recommendations.",
            "",
        ]
    )


def main() -> None:
    generated_at = now_utc()
    surface_result = read_json(SURFACE_RESULT)
    surfaces = read_jsonl(SCORER_SURFACE_LEDGER) + read_jsonl(AVOID_SURFACE_LEDGER)
    observations = read_jsonl(SCORER_OBSERVATION_LEDGER) + read_jsonl(AVOID_OBSERVATION_LEDGER)

    execution_rows = code_surface_execution_rows(surfaces, observations)
    issue_rows = execution_issue_rows(execution_rows)
    aggregate_rows = aggregate_code_surface_execution_rows(execution_rows)
    system_rows = system_code_surface_execution_rows(execution_rows, issue_rows, aggregate_rows)

    counts = {
        "input_surface_result_ok": 1 if surface_result.get("ok") else 0,
        "input_code_surface_rows": len(surfaces),
        "input_observation_rows": len(observations),
        "code_surface_execution_rows": len(execution_rows),
        "code_surface_execution_issue_rows": len(issue_rows),
        "aggregate_code_surface_execution_rows": len(aggregate_rows),
        "system_rows": len(system_rows),
        "surface_execution_status_counts": count_by(execution_rows, "surface_execution_status"),
        "aggregate_code_surface_execution_status_counts": count_by(
            aggregate_rows,
            "aggregate_code_surface_execution_status",
        ),
    }

    result = {
        "artifact": PREFIX,
        "ok": True,
        "generated_utc": generated_at,
        "runtime_replay_geometry_table_code_surface_execution_surface": (
            RUNTIME_REPLAY_GEOMETRY_TABLE_CODE_SURFACE_EXECUTION_SURFACE
        ),
        "research_boundary": research_boundary(),
        "counts": counts,
        "inputs": {
            "surface_result": str(SURFACE_RESULT.relative_to(REPO)).replace("\\", "/"),
            "scorer_surface_ledger": str(SCORER_SURFACE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "avoid_surface_ledger": str(AVOID_SURFACE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "scorer_observation_ledger": str(SCORER_OBSERVATION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "avoid_observation_ledger": str(AVOID_OBSERVATION_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "execution_ledger": str(EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "issue_ledger": str(ISSUE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
    }

    write_jsonl(EXECUTION_LEDGER, execution_rows)
    write_jsonl(ISSUE_LEDGER, issue_rows)
    write_jsonl(AGGREGATE_LEDGER, aggregate_rows)
    write_jsonl(SYSTEM_LEDGER, system_rows)
    write_json(RESULT_PATH, result)
    write_text(SUMMARY_PATH, build_summary(counts))
    update_manifest(generated_at)
    append_sprint_event(generated_at, counts)
    append_active_checkpoint(generated_at, counts)

    result["output_sha256"] = {
        "execution_ledger_sha256": sha256_file(EXECUTION_LEDGER),
        "issue_ledger_sha256": sha256_file(ISSUE_LEDGER),
        "aggregate_ledger_sha256": sha256_file(AGGREGATE_LEDGER),
        "system_ledger_sha256": sha256_file(SYSTEM_LEDGER),
    }
    write_json(RESULT_PATH, result)
    print(json.dumps({"artifact": PREFIX, "counts": counts, "generated_utc": generated_at, "ok": True}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
