#!/usr/bin/env python3
"""Emit branch-local implementation steps from ranked runtime replay packets."""

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

from src.research_infra.moonshot_repaired_proxy_runtime_replay_implementation_steps import (
    RUNTIME_REPLAY_IMPLEMENTATION_STEPS_SURFACE,
    implementation_action_rows,
    implementation_next_step_rows,
    implementation_scope_rollup_rows,
    implementation_step_bucket_rows,
    research_boundary,
    system_implementation_step_rows,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_RANKED_PACKET"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_IMPLEMENTATION_STEPS"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
NEXT_BRANCH_LOCAL_PACKET_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_NEXT_BRANCH_LOCAL_PACKET_LEDGER_2026-05-17.jsonl"
RANKED_ADVANCE_PACKET_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_RANKED_ADVANCE_PACKET_LEDGER_2026-05-17.jsonl"
SYSTEM_RANKED_PACKET_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SYSTEM_RANKED_PACKET_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_runtime_replay_implementation_steps.py"
INPUT_HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_runtime_replay_ranked_packet.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_repaired_proxy_runtime_replay_implementation_steps_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
IMPLEMENTATION_ACTION_LEDGER = ROUTE_DIR / f"{PREFIX}_IMPLEMENTATION_ACTION_LEDGER_2026-05-17.jsonl"
IMPLEMENTATION_SCOPE_ROLLUP_LEDGER = ROUTE_DIR / f"{PREFIX}_SCOPE_ROLLUP_LEDGER_2026-05-17.jsonl"
IMPLEMENTATION_NEXT_STEP_LEDGER = ROUTE_DIR / f"{PREFIX}_NEXT_STEP_LEDGER_2026-05-17.jsonl"
SYSTEM_IMPLEMENTATION_STEP_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
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


def write_text(path: Path, text: str) -> None:
    with open(long_path(path), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with open(long_path(path), "w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def append_text(path: Path, text: str) -> None:
    with open(long_path(path), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def replace_sprint_event(path: Path, row: dict[str, Any]) -> None:
    event = row.get("event")
    route = row.get("route")
    retained: list[str] = []
    if path.exists():
        with open(long_path(path), "r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    existing = json.loads(line)
                except json.JSONDecodeError:
                    retained.append(line.rstrip("\r\n"))
                    continue
                if existing.get("event") == event and existing.get("route") == route:
                    continue
                retained.append(line.rstrip("\r\n"))
    retained.append(json.dumps(row, sort_keys=True))
    write_text(path, "\n".join(retained) + "\n")


def sha256_file(path: Path) -> str | None:
    digest = hashlib.sha256()
    try:
        with open(long_path(path), "rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except FileNotFoundError:
        return None
    return digest.hexdigest()


def source_manifest_rows(paths: list[Path], generated_at: str) -> tuple[list[dict[str, Any]], str]:
    rows: list[dict[str, Any]] = []
    for index, path in enumerate(paths, 1):
        digest = sha256_file(path)
        rows.append(
            {
                "source_manifest_id": f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-IMPL-STEPS-SRCMAN-{index:04d}",
                "path": path.relative_to(REPO).as_posix(),
                "sha256": digest,
                "status": "HASHED" if digest else "MISSING",
                "generated_utc": generated_at,
                "research_boundary": research_boundary(),
            }
        )
    manifest_hash = hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest()
    return rows, manifest_hash


def with_common(row: dict[str, Any], generated_at: str, manifest_hash: str) -> dict[str, Any]:
    output = dict(row)
    output["generated_utc"] = generated_at
    output["source_manifest_hash"] = manifest_hash
    output.setdefault("runtime_replay_implementation_steps_surface", RUNTIME_REPLAY_IMPLEMENTATION_STEPS_SURFACE)
    output.setdefault("research_boundary", research_boundary())
    return output


def update_output_manifest(entries: list[tuple[Path, str]]) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    artifacts = manifest.setdefault("artifacts", [])
    existing = {str(item.get("path")) for item in artifacts}
    for path, artifact_type in entries:
        rel = path.relative_to(REPO).as_posix()
        if rel in existing:
            continue
        artifacts.append({"path": rel, "status": "created", "type": artifact_type})
        existing.add(rel)
    write_json(OUTPUT_MANIFEST, manifest)


def write_summary(path: Path, generated_at: str, counts: dict[str, int]) -> None:
    lines = [
        "# Repaired Proxy Runtime Replay Implementation Steps",
        "",
        f"Generated UTC: `{generated_at}`",
        "",
        "Branch-local research boundary schema: `concrete_branch_local_research_boundary_v1`.",
        "",
        "## Counts",
        "",
    ]
    for key in sorted(counts):
        lines.append(f"- `{key}`: `{counts[key]}`")
    lines.extend(["", "## Continuation", "", "Materialize implementation-step batches into concrete scorer/comparator specs.", ""])
    write_text(path, "\n".join(lines))


def append_checkpoint(generated_at: str, counts: dict[str, int]) -> None:
    marker = "\n## Checkpoint 200 - Runtime Replay Implementation Steps\n"
    existing = ""
    if ACTIVE_LEDGER.exists():
        with open(long_path(ACTIVE_LEDGER), "r", encoding="utf-8", errors="replace") as handle:
            existing = handle.read()
    if marker in existing:
        write_text(ACTIVE_LEDGER, existing.split(marker, 1)[0].rstrip() + "\n")
    text = f"""

## Checkpoint 200 - Runtime Replay Implementation Steps

Timestamp UTC: `{generated_at}`

Trigger: continuation after Checkpoint 199. Ranked branch-local packets were translated into scorer/comparator implementation next steps.

Outputs:

- `{counts['implementation_action_rows']}` implementation action rows.
- `{counts['implementation_scope_rollup_rows']}` implementation scope rollup rows.
- `{counts['implementation_next_step_rows']}` implementation next-step rows.

Boundary: new outputs use concrete branch-local research boundaries and do not add legacy defensive status-token blocks.

Immediate continuation: materialize implementation-step batches into concrete scorer/comparator specs.
"""
    append_text(ACTIVE_LEDGER, text)


def main() -> None:
    generated_at = now_utc()
    input_result = read_json(INPUT_RESULT)
    next_packet_rows_in = read_jsonl(NEXT_BRANCH_LOCAL_PACKET_LEDGER)
    ranked_rows_in = read_jsonl(RANKED_ADVANCE_PACKET_LEDGER)
    system_ranked_rows_in = read_jsonl(SYSTEM_RANKED_PACKET_LEDGER)
    source_rows, manifest_hash = source_manifest_rows(
        [
            INPUT_RESULT,
            NEXT_BRANCH_LOCAL_PACKET_LEDGER,
            RANKED_ADVANCE_PACKET_LEDGER,
            SYSTEM_RANKED_PACKET_LEDGER,
            HELPER_MODULE,
            INPUT_HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )
    action_rows = [with_common(row, generated_at, manifest_hash) for row in implementation_action_rows(next_packet_rows_in)]
    rollup_rows = [with_common(row, generated_at, manifest_hash) for row in implementation_scope_rollup_rows(action_rows)]
    next_step_rows = [with_common(row, generated_at, manifest_hash) for row in implementation_next_step_rows(action_rows)]
    system_rows = [
        with_common(row, generated_at, manifest_hash)
        for row in system_implementation_step_rows(action_rows, rollup_rows, next_step_rows)
    ]
    bucket_rows = [
        with_common(row, generated_at, manifest_hash)
        for row in implementation_step_bucket_rows(action_rows, rollup_rows, next_step_rows, system_rows)
    ]
    family_counts = Counter(str(row.get("implementation_family")) for row in action_rows)
    step_counts = Counter(str(row.get("implementation_step_family")) for row in action_rows)
    counts = {
        "input_ranked_packet_result_ok": int(bool(input_result.get("ok"))),
        "input_next_branch_local_packet_rows": len(next_packet_rows_in),
        "input_ranked_advance_packet_rows": len(ranked_rows_in),
        "input_system_ranked_packet_rows": len(system_ranked_rows_in),
        "implementation_action_rows": len(action_rows),
        "implementation_scope_rollup_rows": len(rollup_rows),
        "implementation_next_step_rows": len(next_step_rows),
        "default_off_scorer_action_rows": family_counts.get("IMPLEMENTATION_FAMILY_DEFAULT_OFF_SCORER", 0),
        "avoid_redesign_comparator_action_rows": family_counts.get(
            "IMPLEMENTATION_FAMILY_AVOID_REDESIGN_COMPARATOR", 0
        ),
        "ready_scorer_batch_rows": step_counts.get("IMPLEMENTATION_STEP_READY_SCORER_BATCH", 0),
        "ready_comparator_batch_rows": step_counts.get("IMPLEMENTATION_STEP_READY_COMPARATOR_BATCH", 0),
        "context_scorer_batch_rows": step_counts.get("IMPLEMENTATION_STEP_CONTEXT_SCORER_BATCH", 0),
        "context_comparator_batch_rows": step_counts.get("IMPLEMENTATION_STEP_CONTEXT_COMPARATOR_BATCH", 0),
        "context_carry_scorer_rows": step_counts.get("IMPLEMENTATION_STEP_CONTEXT_CARRY_SCORER", 0),
        "context_carry_comparator_rows": step_counts.get("IMPLEMENTATION_STEP_CONTEXT_CARRY_COMPARATOR", 0),
        "system_implementation_step_rows": len(system_rows),
        "bucket_rows": len(bucket_rows),
        "source_manifest_rows": len(source_rows),
    }
    result = with_common(
        {
            "artifact": PREFIX,
            "ok": True,
            "generated_utc": generated_at,
            "counts": counts,
            "system_implementation_steps": system_rows[0]["system_implementation_steps"],
        },
        generated_at,
        manifest_hash,
    )
    write_json(RESULT_PATH, result)
    write_jsonl(IMPLEMENTATION_ACTION_LEDGER, action_rows)
    write_jsonl(IMPLEMENTATION_SCOPE_ROLLUP_LEDGER, rollup_rows)
    write_jsonl(IMPLEMENTATION_NEXT_STEP_LEDGER, next_step_rows)
    write_jsonl(SYSTEM_IMPLEMENTATION_STEP_LEDGER, system_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_rows)
    write_summary(SUMMARY_PATH, generated_at, counts)
    update_output_manifest(
        [
            (RESULT_PATH, "runtime_replay_implementation_steps_result"),
            (IMPLEMENTATION_ACTION_LEDGER, "runtime_replay_implementation_action_ledger"),
            (IMPLEMENTATION_SCOPE_ROLLUP_LEDGER, "runtime_replay_implementation_scope_rollup_ledger"),
            (IMPLEMENTATION_NEXT_STEP_LEDGER, "runtime_replay_implementation_next_step_ledger"),
            (SYSTEM_IMPLEMENTATION_STEP_LEDGER, "runtime_replay_implementation_steps_system_ledger"),
            (BUCKET_LEDGER, "runtime_replay_implementation_steps_bucket_ledger"),
            (SOURCE_MANIFEST_LEDGER, "runtime_replay_implementation_steps_source_manifest"),
            (SUMMARY_PATH, "runtime_replay_implementation_steps_summary"),
            (BUILDER_MODULE, "runtime_replay_implementation_steps_builder"),
            (VERIFIER_MODULE, "runtime_replay_implementation_steps_verifier"),
            (HELPER_MODULE, "runtime_replay_implementation_steps_helper"),
        ]
    )
    replace_sprint_event(
        SPRINT_LEDGER,
        {
            "event": "checkpoint_200_runtime_replay_implementation_steps",
            "route": PREFIX,
            "generated_utc": generated_at,
            "counts": counts,
            "result": RESULT_PATH.relative_to(REPO).as_posix(),
            "status": "completed",
        },
    )
    append_checkpoint(generated_at, counts)
    print(json.dumps({"artifact": PREFIX, "counts": counts, "generated_utc": generated_at, "ok": True}, indent=2))


if __name__ == "__main__":
    main()
