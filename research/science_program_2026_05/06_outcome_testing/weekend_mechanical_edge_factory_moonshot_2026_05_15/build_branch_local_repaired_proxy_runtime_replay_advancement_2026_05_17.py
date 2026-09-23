#!/usr/bin/env python3
"""Split runtime replay inventory alignment rows into advancement surfaces."""

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

from src.research_infra.moonshot_repaired_proxy_runtime_replay_advancement import (
    RUNTIME_REPLAY_ADVANCEMENT_SURFACE,
    action_conflict_review_rows,
    advancement_bucket_rows,
    advancement_decision_rows,
    represented_surface_rows,
    research_boundary,
    symbol_advancement_rows,
    system_advancement_rows,
    unmatched_scope_advancement_rows,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_INVENTORY_ALIGNMENT"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_ADVANCEMENT"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
SIGNAL_INVENTORY_ALIGNMENT_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SIGNAL_INVENTORY_ALIGNMENT_LEDGER_2026-05-17.jsonl"
SYMBOL_INVENTORY_ALIGNMENT_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SYMBOL_INVENTORY_ALIGNMENT_LEDGER_2026-05-17.jsonl"
SYSTEM_INVENTORY_ALIGNMENT_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SYSTEM_INVENTORY_ALIGNMENT_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_runtime_replay_advancement.py"
INPUT_HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_runtime_replay_inventory_alignment.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_repaired_proxy_runtime_replay_advancement_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
ADVANCEMENT_DECISION_LEDGER = ROUTE_DIR / f"{PREFIX}_ADVANCEMENT_DECISION_LEDGER_2026-05-17.jsonl"
REPRESENTED_SURFACE_LEDGER = ROUTE_DIR / f"{PREFIX}_REPRESENTED_SURFACE_LEDGER_2026-05-17.jsonl"
ACTION_CONFLICT_REVIEW_LEDGER = ROUTE_DIR / f"{PREFIX}_ACTION_CONFLICT_REVIEW_LEDGER_2026-05-17.jsonl"
UNMATCHED_SCOPE_ADVANCEMENT_LEDGER = ROUTE_DIR / f"{PREFIX}_UNMATCHED_SCOPE_ADVANCEMENT_LEDGER_2026-05-17.jsonl"
SYMBOL_ADVANCEMENT_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_ADVANCEMENT_LEDGER_2026-05-17.jsonl"
SYSTEM_ADVANCEMENT_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_ADVANCEMENT_LEDGER_2026-05-17.jsonl"
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
                "source_manifest_id": f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-ADVANCE-SRCMAN-{index:04d}",
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
    output.setdefault("runtime_replay_advancement_surface", RUNTIME_REPLAY_ADVANCEMENT_SURFACE)
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
        "# Repaired Proxy Runtime Replay Advancement",
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
    lines.extend(["", "## Continuation", "", "Build the comparison packet from represented surfaces and review ledgers.", ""])
    write_text(path, "\n".join(lines))


def append_checkpoint(generated_at: str, counts: dict[str, int]) -> None:
    marker = "\n## Checkpoint 191 - Runtime Replay Advancement Split\n"
    existing = ""
    if ACTIVE_LEDGER.exists():
        with open(long_path(ACTIVE_LEDGER), "r", encoding="utf-8", errors="replace") as handle:
            existing = handle.read()
    if marker in existing:
        write_text(ACTIVE_LEDGER, existing.split(marker, 1)[0].rstrip() + "\n")
    text = f"""

## Checkpoint 191 - Runtime Replay Advancement Split

Timestamp UTC: `{generated_at}`

Trigger: continuation after Checkpoint 190. Inventory alignment rows were split into represented surfaces, exact-scope action conflicts, and unmatched scope review rows.

Outputs:

- `{counts['advancement_decision_rows']}` advancement decision rows from `{counts['input_signal_inventory_alignment_rows']}` alignment rows.
- `{counts['represented_surface_rows']}` represented surface rows ready for comparison packet input.
- `{counts['action_conflict_review_rows']}` exact/broad scope action-conflict review rows.
- `{counts['unmatched_scope_advancement_rows']}` unmatched scope review rows.

Boundary: new outputs use concrete branch-local research boundaries and do not add legacy defensive status-token blocks.

Immediate continuation: build a comparison packet from represented surfaces plus explicit conflict/review sidecars.
"""
    append_text(ACTIVE_LEDGER, text)


def main() -> None:
    generated_at = now_utc()
    input_result = read_json(INPUT_RESULT)
    alignment_rows_in = read_jsonl(SIGNAL_INVENTORY_ALIGNMENT_LEDGER)
    symbol_alignment_rows_in = read_jsonl(SYMBOL_INVENTORY_ALIGNMENT_LEDGER)
    system_alignment_rows_in = read_jsonl(SYSTEM_INVENTORY_ALIGNMENT_LEDGER)
    source_rows, manifest_hash = source_manifest_rows(
        [
            INPUT_RESULT,
            SIGNAL_INVENTORY_ALIGNMENT_LEDGER,
            SYMBOL_INVENTORY_ALIGNMENT_LEDGER,
            SYSTEM_INVENTORY_ALIGNMENT_LEDGER,
            HELPER_MODULE,
            INPUT_HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )
    decision_rows = [with_common(row, generated_at, manifest_hash) for row in advancement_decision_rows(alignment_rows_in)]
    represented_rows = [with_common(row, generated_at, manifest_hash) for row in represented_surface_rows(decision_rows)]
    conflict_rows = [with_common(row, generated_at, manifest_hash) for row in action_conflict_review_rows(decision_rows)]
    unmatched_rows = [
        with_common(row, generated_at, manifest_hash) for row in unmatched_scope_advancement_rows(decision_rows)
    ]
    symbol_rows = [with_common(row, generated_at, manifest_hash) for row in symbol_advancement_rows(decision_rows)]
    system_rows = [with_common(row, generated_at, manifest_hash) for row in system_advancement_rows(decision_rows, symbol_rows)]
    bucket_rows = [
        with_common(row, generated_at, manifest_hash)
        for row in advancement_bucket_rows(
            decision_rows,
            represented_rows,
            conflict_rows,
            unmatched_rows,
            symbol_rows,
            system_rows,
        )
    ]
    family_counts = Counter(str(row.get("advancement_family")) for row in decision_rows)
    counts = {
        "input_inventory_alignment_result_ok": int(bool(input_result.get("ok"))),
        "input_signal_inventory_alignment_rows": len(alignment_rows_in),
        "input_symbol_inventory_alignment_rows": len(symbol_alignment_rows_in),
        "input_system_inventory_alignment_rows": len(system_alignment_rows_in),
        "advancement_decision_rows": len(decision_rows),
        "represented_surface_rows": len(represented_rows),
        "represented_signal_advancement_rows": family_counts.get("REPRESENTED_SIGNAL_ADVANCES", 0),
        "represented_context_advancement_rows": family_counts.get("REPRESENTED_CONTEXT_ADVANCES", 0),
        "broad_scope_compatible_advancement_rows": family_counts.get("BROAD_SCOPE_COMPATIBLE_ADVANCES", 0),
        "action_conflict_review_rows": len(conflict_rows),
        "exact_scope_action_conflict_rows": family_counts.get("EXACT_SCOPE_ACTION_CONFLICT_REVIEW", 0),
        "broad_scope_action_conflict_rows": family_counts.get("BROAD_SCOPE_ACTION_CONFLICT_REVIEW", 0),
        "unmatched_scope_advancement_rows": len(unmatched_rows),
        "symbol_advancement_rows": len(symbol_rows),
        "system_advancement_rows": len(system_rows),
        "bucket_rows": len(bucket_rows),
        "source_manifest_rows": len(source_rows),
    }
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "research_boundary": research_boundary(),
        "counts": counts,
        "source_manifest_hash": manifest_hash,
        "system_advancement": system_rows[0]["system_advancement"],
        "ok": True,
    }

    write_json(RESULT_PATH, result)
    write_jsonl(ADVANCEMENT_DECISION_LEDGER, decision_rows)
    write_jsonl(REPRESENTED_SURFACE_LEDGER, represented_rows)
    write_jsonl(ACTION_CONFLICT_REVIEW_LEDGER, conflict_rows)
    write_jsonl(UNMATCHED_SCOPE_ADVANCEMENT_LEDGER, unmatched_rows)
    write_jsonl(SYMBOL_ADVANCEMENT_LEDGER, symbol_rows)
    write_jsonl(SYSTEM_ADVANCEMENT_LEDGER, system_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_rows)
    write_summary(SUMMARY_PATH, generated_at, counts)
    update_output_manifest(
        [
            (RESULT_PATH, "repaired_proxy_runtime_replay_advancement_result"),
            (ADVANCEMENT_DECISION_LEDGER, "repaired_proxy_runtime_replay_advancement_decision_ledger"),
            (REPRESENTED_SURFACE_LEDGER, "repaired_proxy_runtime_replay_represented_surface_ledger"),
            (ACTION_CONFLICT_REVIEW_LEDGER, "repaired_proxy_runtime_replay_action_conflict_review_ledger"),
            (UNMATCHED_SCOPE_ADVANCEMENT_LEDGER, "repaired_proxy_runtime_replay_unmatched_scope_advancement_ledger"),
            (SYMBOL_ADVANCEMENT_LEDGER, "repaired_proxy_runtime_replay_symbol_advancement_ledger"),
            (SYSTEM_ADVANCEMENT_LEDGER, "repaired_proxy_runtime_replay_system_advancement_ledger"),
            (BUCKET_LEDGER, "repaired_proxy_runtime_replay_advancement_bucket_ledger"),
            (SOURCE_MANIFEST_LEDGER, "repaired_proxy_runtime_replay_advancement_source_manifest_ledger"),
            (SUMMARY_PATH, "repaired_proxy_runtime_replay_advancement_summary"),
            (BUILDER_MODULE, "repaired_proxy_runtime_replay_advancement_builder"),
            (VERIFIER_MODULE, "repaired_proxy_runtime_replay_advancement_verifier"),
        ]
    )
    replace_sprint_event(
        SPRINT_LEDGER,
        {
            "timestamp_utc": generated_at,
            "event": "repaired_proxy_runtime_replay_advancement_built",
            "route": PREFIX,
            "counts": counts,
            "research_boundary": research_boundary(),
            "summary": "Split runtime replay inventory alignments into represented, conflict, and unmatched surfaces.",
        },
    )
    append_checkpoint(generated_at, counts)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
