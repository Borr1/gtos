#!/usr/bin/env python3
"""Materialize branch-local scorer/comparator specs from implementation steps."""

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

from src.research_infra.moonshot_repaired_proxy_runtime_replay_spec_materialization import (
    RUNTIME_REPLAY_SPEC_MATERIALIZATION_SURFACE,
    comparator_spec_rows,
    research_boundary,
    scorer_spec_rows,
    spec_batch_rows,
    spec_materialization_bucket_rows,
    system_spec_materialization_rows,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_IMPLEMENTATION_STEPS"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_SPEC_MATERIALIZATION"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
IMPLEMENTATION_ACTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_IMPLEMENTATION_ACTION_LEDGER_2026-05-17.jsonl"
IMPLEMENTATION_NEXT_STEP_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_NEXT_STEP_LEDGER_2026-05-17.jsonl"
SYSTEM_IMPLEMENTATION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_runtime_replay_spec_materialization.py"
INPUT_HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_runtime_replay_implementation_steps.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_repaired_proxy_runtime_replay_spec_materialization_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
SCORER_SPEC_LEDGER = ROUTE_DIR / f"{PREFIX}_SCORER_SPEC_LEDGER_2026-05-17.jsonl"
COMPARATOR_SPEC_LEDGER = ROUTE_DIR / f"{PREFIX}_COMPARATOR_SPEC_LEDGER_2026-05-17.jsonl"
SPEC_BATCH_LEDGER = ROUTE_DIR / f"{PREFIX}_SPEC_BATCH_LEDGER_2026-05-17.jsonl"
SYSTEM_SPEC_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
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
    rows = []
    for index, path in enumerate(paths, 1):
        digest = sha256_file(path)
        rows.append(
            {
                "source_manifest_id": f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-SPEC-MAT-SRCMAN-{index:04d}",
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
    output.setdefault("runtime_replay_spec_materialization_surface", RUNTIME_REPLAY_SPEC_MATERIALIZATION_SURFACE)
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
    lines = ["# Repaired Proxy Runtime Replay Spec Materialization", "", f"Generated UTC: `{generated_at}`", ""]
    lines.extend(["Branch-local research boundary schema: `concrete_branch_local_research_boundary_v1`.", "", "## Counts", ""])
    for key in sorted(counts):
        lines.append(f"- `{key}`: `{counts[key]}`")
    lines.extend(["", "## Continuation", "", "Execute materialized scorer/comparator specs against replay rows.", ""])
    write_text(path, "\n".join(lines))


def append_checkpoint(generated_at: str, counts: dict[str, int]) -> None:
    marker = "\n## Checkpoint 201 - Runtime Replay Spec Materialization\n"
    existing = ""
    if ACTIVE_LEDGER.exists():
        with open(long_path(ACTIVE_LEDGER), "r", encoding="utf-8", errors="replace") as handle:
            existing = handle.read()
    if marker in existing:
        write_text(ACTIVE_LEDGER, existing.split(marker, 1)[0].rstrip() + "\n")
    text = f"""

## Checkpoint 201 - Runtime Replay Spec Materialization

Timestamp UTC: `{generated_at}`

Trigger: continuation after Checkpoint 200. Implementation next-step rows were materialized into branch-local scorer and comparator spec rows.

Outputs:

- `{counts['scorer_spec_rows']}` scorer spec rows.
- `{counts['comparator_spec_rows']}` comparator spec rows.
- `{counts['spec_batch_rows']}` spec batch rows.

Boundary: new outputs use concrete branch-local research boundaries and do not add legacy defensive status-token blocks.

Immediate continuation: execute materialized scorer/comparator specs against replay rows.
"""
    append_text(ACTIVE_LEDGER, text)


def main() -> None:
    generated_at = now_utc()
    input_result = read_json(INPUT_RESULT)
    action_rows_in = read_jsonl(IMPLEMENTATION_ACTION_LEDGER)
    next_step_rows_in = read_jsonl(IMPLEMENTATION_NEXT_STEP_LEDGER)
    system_rows_in = read_jsonl(SYSTEM_IMPLEMENTATION_LEDGER)
    source_rows, manifest_hash = source_manifest_rows(
        [INPUT_RESULT, IMPLEMENTATION_ACTION_LEDGER, IMPLEMENTATION_NEXT_STEP_LEDGER, SYSTEM_IMPLEMENTATION_LEDGER,
         HELPER_MODULE, INPUT_HELPER_MODULE, BUILDER_MODULE, VERIFIER_MODULE, TEST_MODULE],
        generated_at,
    )
    scorer_rows = [with_common(row, generated_at, manifest_hash) for row in scorer_spec_rows(action_rows_in)]
    comparator_rows = [with_common(row, generated_at, manifest_hash) for row in comparator_spec_rows(action_rows_in)]
    batch_rows = [with_common(row, generated_at, manifest_hash) for row in spec_batch_rows(scorer_rows, comparator_rows)]
    system_rows = [
        with_common(row, generated_at, manifest_hash)
        for row in system_spec_materialization_rows(scorer_rows, comparator_rows, batch_rows)
    ]
    bucket_rows = [
        with_common(row, generated_at, manifest_hash)
        for row in spec_materialization_bucket_rows(scorer_rows, comparator_rows, batch_rows, system_rows)
    ]
    context_counts = Counter(str(row.get("spec_context_mode")) for row in scorer_rows + comparator_rows)
    counts = {
        "input_implementation_steps_result_ok": int(bool(input_result.get("ok"))),
        "input_implementation_action_rows": len(action_rows_in),
        "input_implementation_next_step_rows": len(next_step_rows_in),
        "input_system_implementation_step_rows": len(system_rows_in),
        "scorer_spec_rows": len(scorer_rows),
        "comparator_spec_rows": len(comparator_rows),
        "spec_batch_rows": len(batch_rows),
        "ready_batch_spec_rows": context_counts.get("SPEC_CONTEXT_READY_BATCH", 0),
        "attached_context_spec_rows": context_counts.get("SPEC_CONTEXT_ATTACHED_CONTEXT_BATCH", 0),
        "carry_forward_spec_rows": context_counts.get("SPEC_CONTEXT_CARRY_FORWARD_BATCH", 0),
        "system_spec_materialization_rows": len(system_rows),
        "bucket_rows": len(bucket_rows),
        "source_manifest_rows": len(source_rows),
    }
    result = with_common(
        {"artifact": PREFIX, "ok": True, "generated_utc": generated_at, "counts": counts,
         "system_spec_materialization": system_rows[0]["system_spec_materialization"]},
        generated_at,
        manifest_hash,
    )
    write_json(RESULT_PATH, result)
    write_jsonl(SCORER_SPEC_LEDGER, scorer_rows)
    write_jsonl(COMPARATOR_SPEC_LEDGER, comparator_rows)
    write_jsonl(SPEC_BATCH_LEDGER, batch_rows)
    write_jsonl(SYSTEM_SPEC_LEDGER, system_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_rows)
    write_summary(SUMMARY_PATH, generated_at, counts)
    update_output_manifest(
        [(RESULT_PATH, "runtime_replay_spec_materialization_result"), (SCORER_SPEC_LEDGER, "runtime_replay_scorer_spec_ledger"),
         (COMPARATOR_SPEC_LEDGER, "runtime_replay_comparator_spec_ledger"), (SPEC_BATCH_LEDGER, "runtime_replay_spec_batch_ledger"),
         (SYSTEM_SPEC_LEDGER, "runtime_replay_spec_materialization_system_ledger"), (BUCKET_LEDGER, "runtime_replay_spec_materialization_bucket_ledger"),
         (SOURCE_MANIFEST_LEDGER, "runtime_replay_spec_materialization_source_manifest"), (SUMMARY_PATH, "runtime_replay_spec_materialization_summary"),
         (BUILDER_MODULE, "runtime_replay_spec_materialization_builder"), (VERIFIER_MODULE, "runtime_replay_spec_materialization_verifier"),
         (HELPER_MODULE, "runtime_replay_spec_materialization_helper")]
    )
    replace_sprint_event(
        SPRINT_LEDGER,
        {"event": "checkpoint_201_runtime_replay_spec_materialization", "route": PREFIX, "generated_utc": generated_at,
         "counts": counts, "result": RESULT_PATH.relative_to(REPO).as_posix(), "status": "completed"},
    )
    append_checkpoint(generated_at, counts)
    print(json.dumps({"artifact": PREFIX, "counts": counts, "generated_utc": generated_at, "ok": True}, indent=2))


if __name__ == "__main__":
    main()
