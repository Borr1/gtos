#!/usr/bin/env python3
"""Build branch-local code candidates from geometry table observations."""

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

from src.research_infra.moonshot_repaired_proxy_runtime_replay_geometry_table_code_candidates import (
    RUNTIME_REPLAY_GEOMETRY_TABLE_CODE_CANDIDATES_SURFACE,
    aggregate_code_candidate_rows,
    avoid_code_candidate_rows,
    research_boundary,
    scorer_code_candidate_rows,
    source_gap_code_candidate_rows,
    system_code_candidate_rows,
)


OBS_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_GEOMETRY_TABLE_OBSERVATIONS"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_GEOMETRY_TABLE_CODE_CANDIDATES"

OBS_RESULT = ROUTE_DIR / f"{OBS_PREFIX}_RESULT_2026-05-17.json"
SCORER_OBSERVATION_LEDGER = ROUTE_DIR / f"{OBS_PREFIX}_SCORER_OBSERVATION_LEDGER_2026-05-17.jsonl"
AVOID_OBSERVATION_LEDGER = ROUTE_DIR / f"{OBS_PREFIX}_AVOID_OBSERVATION_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_runtime_replay_geometry_table_code_candidates.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_repaired_proxy_runtime_replay_geometry_table_code_candidates_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
SCORER_CODE_CANDIDATE_LEDGER = ROUTE_DIR / f"{PREFIX}_SCORER_CODE_CANDIDATE_LEDGER_2026-05-17.jsonl"
AVOID_CODE_CANDIDATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AVOID_CODE_CANDIDATE_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
SOURCE_GAP_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_GAP_CODE_CANDIDATE_LEDGER_2026-05-17.jsonl"
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
        (RESULT_PATH, "runtime_replay_geometry_table_code_candidates_result"),
        (SCORER_CODE_CANDIDATE_LEDGER, "runtime_replay_geometry_scorer_code_candidates"),
        (AVOID_CODE_CANDIDATE_LEDGER, "runtime_replay_geometry_avoid_code_candidates"),
        (AGGREGATE_LEDGER, "runtime_replay_geometry_table_code_candidate_aggregates"),
        (SOURCE_GAP_LEDGER, "runtime_replay_geometry_table_source_gap_code_candidates"),
        (SYSTEM_LEDGER, "runtime_replay_geometry_table_code_candidates_system"),
        (SUMMARY_PATH, "runtime_replay_geometry_table_code_candidates_summary"),
        (BUILDER_MODULE, "runtime_replay_geometry_table_code_candidates_builder"),
        (VERIFIER_MODULE, "runtime_replay_geometry_table_code_candidates_verifier"),
        (HELPER_MODULE, "runtime_replay_geometry_table_code_candidates_helper"),
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
    manifest["latest_branch_local_repaired_proxy_runtime_replay_geometry_table_code_candidates"] = {
        "generated_utc": generated_at,
        "files": entries,
        "result": str(RESULT_PATH.relative_to(REPO)).replace("\\", "/"),
    }
    manifest["last_updated_utc"] = generated_at
    write_json(OUTPUT_MANIFEST, manifest)


def append_sprint_event(generated_at: str, counts: dict[str, Any]) -> None:
    event = {
        "checkpoint": 209,
        "event": "runtime_replay_geometry_table_code_candidates",
        "generated_utc": generated_at,
        "scorer_code_candidate_rows": counts["scorer_code_candidate_rows"],
        "avoid_code_candidate_rows": counts["avoid_code_candidate_rows"],
        "aggregate_code_candidate_rows": counts["aggregate_code_candidate_rows"],
        "source_gap_code_candidate_rows": counts["source_gap_code_candidate_rows"],
        "continuation": "materialize concrete branch-local scorer and avoid candidate code surfaces from retained code candidates.",
        "boundary": research_boundary(),
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")


def append_active_checkpoint(generated_at: str, counts: dict[str, Any]) -> None:
    text = f"""
## Checkpoint 209 - Runtime Replay Geometry Table Code Candidates

Generated: {generated_at}

Trigger: continuation after Checkpoint 208. Scorer and avoid observations were consumed into branch-local code-candidate ledgers.

Rows:
- scorer code candidate rows: {counts['scorer_code_candidate_rows']}
- avoid code candidate rows: {counts['avoid_code_candidate_rows']}
- aggregate code candidate rows: {counts['aggregate_code_candidate_rows']}
- source gap code candidate rows: {counts['source_gap_code_candidate_rows']}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: materialize concrete branch-local scorer and avoid candidate code surfaces from retained code candidates.
"""
    with open(long_path(ACTIVE_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def build_summary(counts: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Runtime Replay Geometry Table Code Candidates",
            "",
            "Checkpoint 209 consumes scorer and avoid observations into branch-local code-candidate ledgers.",
            "",
            "## Counts",
            "",
            f"- Scorer code candidate rows: `{counts['scorer_code_candidate_rows']}`",
            f"- Avoid code candidate rows: `{counts['avoid_code_candidate_rows']}`",
            f"- Aggregate code candidate rows: `{counts['aggregate_code_candidate_rows']}`",
            f"- Source gap code candidate rows: `{counts['source_gap_code_candidate_rows']}`",
            "",
            "## Continuation",
            "",
            "Materialize concrete branch-local scorer and avoid candidate code surfaces from retained code candidates.",
            "",
        ]
    )


def main() -> None:
    generated_at = now_utc()
    obs_result = read_json(OBS_RESULT)
    scorer_observation_rows = read_jsonl(SCORER_OBSERVATION_LEDGER)
    avoid_observation_rows = read_jsonl(AVOID_OBSERVATION_LEDGER)

    scorer_rows = scorer_code_candidate_rows(scorer_observation_rows)
    avoid_rows = avoid_code_candidate_rows(avoid_observation_rows)
    all_rows = scorer_rows + avoid_rows
    gap_rows = source_gap_code_candidate_rows(all_rows)
    aggregate_rows = aggregate_code_candidate_rows(all_rows)
    system_rows = system_code_candidate_rows(scorer_rows, avoid_rows, aggregate_rows, gap_rows)

    counts = {
        "input_observation_result_ok": 1 if obs_result.get("ok") else 0,
        "input_scorer_observation_rows": len(scorer_observation_rows),
        "input_avoid_observation_rows": len(avoid_observation_rows),
        "scorer_code_candidate_rows": len(scorer_rows),
        "avoid_code_candidate_rows": len(avoid_rows),
        "total_code_candidate_rows": len(all_rows),
        "aggregate_code_candidate_rows": len(aggregate_rows),
        "source_gap_code_candidate_rows": len(gap_rows),
        "system_rows": len(system_rows),
        "code_candidate_action_counts": count_by(all_rows, "code_candidate_action"),
        "aggregate_code_candidate_action_counts": count_by(aggregate_rows, "aggregate_code_candidate_action"),
    }

    result = {
        "artifact": PREFIX,
        "ok": True,
        "generated_utc": generated_at,
        "runtime_replay_geometry_table_code_candidates_surface": (
            RUNTIME_REPLAY_GEOMETRY_TABLE_CODE_CANDIDATES_SURFACE
        ),
        "research_boundary": research_boundary(),
        "counts": counts,
        "inputs": {
            "observation_result": str(OBS_RESULT.relative_to(REPO)).replace("\\", "/"),
            "scorer_observation_ledger": str(SCORER_OBSERVATION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "avoid_observation_ledger": str(AVOID_OBSERVATION_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "scorer_code_candidate_ledger": str(SCORER_CODE_CANDIDATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "avoid_code_candidate_ledger": str(AVOID_CODE_CANDIDATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "source_gap_code_candidate_ledger": str(SOURCE_GAP_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
    }

    write_jsonl(SCORER_CODE_CANDIDATE_LEDGER, scorer_rows)
    write_jsonl(AVOID_CODE_CANDIDATE_LEDGER, avoid_rows)
    write_jsonl(AGGREGATE_LEDGER, aggregate_rows)
    write_jsonl(SOURCE_GAP_LEDGER, gap_rows)
    write_jsonl(SYSTEM_LEDGER, system_rows)
    write_json(RESULT_PATH, result)
    write_text(SUMMARY_PATH, build_summary(counts))
    update_manifest(generated_at)
    append_sprint_event(generated_at, counts)
    append_active_checkpoint(generated_at, counts)

    result["output_sha256"] = {
        "scorer_code_candidate_sha256": sha256_file(SCORER_CODE_CANDIDATE_LEDGER),
        "avoid_code_candidate_sha256": sha256_file(AVOID_CODE_CANDIDATE_LEDGER),
        "aggregate_ledger_sha256": sha256_file(AGGREGATE_LEDGER),
        "source_gap_code_candidate_sha256": sha256_file(SOURCE_GAP_LEDGER),
        "system_ledger_sha256": sha256_file(SYSTEM_LEDGER),
    }
    write_json(RESULT_PATH, result)
    print(json.dumps({"artifact": PREFIX, "counts": counts, "generated_utc": generated_at, "ok": True}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
