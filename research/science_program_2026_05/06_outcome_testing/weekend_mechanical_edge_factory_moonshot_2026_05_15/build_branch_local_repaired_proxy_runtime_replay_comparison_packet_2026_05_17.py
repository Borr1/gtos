#!/usr/bin/env python3
"""Materialize runtime replay comparison packet inputs and sidecars."""

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

from src.research_infra.moonshot_repaired_proxy_runtime_replay_comparison_packet import (
    RUNTIME_REPLAY_COMPARISON_PACKET_SURFACE,
    comparison_bucket_rows,
    comparison_packet_rows,
    comparison_scope_rows,
    research_boundary,
    review_sidecar_rows,
    system_comparison_rows,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_ADVANCEMENT"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_COMPARISON_PACKET"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
REPRESENTED_SURFACE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_REPRESENTED_SURFACE_LEDGER_2026-05-17.jsonl"
ACTION_CONFLICT_REVIEW_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_ACTION_CONFLICT_REVIEW_LEDGER_2026-05-17.jsonl"
UNMATCHED_SCOPE_ADVANCEMENT_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_UNMATCHED_SCOPE_ADVANCEMENT_LEDGER_2026-05-17.jsonl"
SYMBOL_ADVANCEMENT_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SYMBOL_ADVANCEMENT_LEDGER_2026-05-17.jsonl"
SYSTEM_ADVANCEMENT_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SYSTEM_ADVANCEMENT_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_runtime_replay_comparison_packet.py"
INPUT_HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_runtime_replay_advancement.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_repaired_proxy_runtime_replay_comparison_packet_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
COMPARISON_PACKET_LEDGER = ROUTE_DIR / f"{PREFIX}_COMPARISON_PACKET_LEDGER_2026-05-17.jsonl"
REVIEW_SIDECAR_LEDGER = ROUTE_DIR / f"{PREFIX}_REVIEW_SIDECAR_LEDGER_2026-05-17.jsonl"
COMPARISON_SCOPE_LEDGER = ROUTE_DIR / f"{PREFIX}_COMPARISON_SCOPE_LEDGER_2026-05-17.jsonl"
SYSTEM_COMPARISON_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_COMPARISON_LEDGER_2026-05-17.jsonl"
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
                "source_manifest_id": f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-COMPARISON-SRCMAN-{index:04d}",
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
    output.setdefault("runtime_replay_comparison_packet_surface", RUNTIME_REPLAY_COMPARISON_PACKET_SURFACE)
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
        "# Repaired Proxy Runtime Replay Comparison Packet",
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
    lines.extend(
        [
            "",
            "## Continuation",
            "",
            "Compare represented packet rows and keep review sidecars attached by scope.",
            "",
        ]
    )
    write_text(path, "\n".join(lines))


def append_checkpoint(generated_at: str, counts: dict[str, int]) -> None:
    marker = "\n## Checkpoint 192 - Runtime Replay Comparison Packet\n"
    existing = ""
    if ACTIVE_LEDGER.exists():
        with open(long_path(ACTIVE_LEDGER), "r", encoding="utf-8", errors="replace") as handle:
            existing = handle.read()
    if marker in existing:
        write_text(ACTIVE_LEDGER, existing.split(marker, 1)[0].rstrip() + "\n")
    text = f"""

## Checkpoint 192 - Runtime Replay Comparison Packet

Timestamp UTC: `{generated_at}`

Trigger: continuation after Checkpoint 191. Represented advancement surfaces were materialized into comparison packet rows while action conflicts and unmatched scopes were carried as sidecars.

Outputs:

- `{counts['comparison_packet_rows']}` represented comparison packet rows from `{counts['input_represented_surface_rows']}` represented surfaces.
- `{counts['review_sidecar_rows']}` review sidecar rows from action-conflict and unmatched-scope inputs.
- `{counts['comparison_scope_rows']}` symbol/session/horizon/family comparison scope rollups.

Boundary: new outputs use concrete branch-local research boundaries and do not add legacy defensive status-token blocks.

Immediate continuation: compare represented packet rows by scope and keep sidecars attached to any downstream comparison summary.
"""
    append_text(ACTIVE_LEDGER, text)


def main() -> None:
    generated_at = now_utc()
    input_result = read_json(INPUT_RESULT)
    represented_rows_in = read_jsonl(REPRESENTED_SURFACE_LEDGER)
    action_conflict_rows_in = read_jsonl(ACTION_CONFLICT_REVIEW_LEDGER)
    unmatched_rows_in = read_jsonl(UNMATCHED_SCOPE_ADVANCEMENT_LEDGER)
    symbol_advancement_rows_in = read_jsonl(SYMBOL_ADVANCEMENT_LEDGER)
    system_advancement_rows_in = read_jsonl(SYSTEM_ADVANCEMENT_LEDGER)
    source_rows, manifest_hash = source_manifest_rows(
        [
            INPUT_RESULT,
            REPRESENTED_SURFACE_LEDGER,
            ACTION_CONFLICT_REVIEW_LEDGER,
            UNMATCHED_SCOPE_ADVANCEMENT_LEDGER,
            SYMBOL_ADVANCEMENT_LEDGER,
            SYSTEM_ADVANCEMENT_LEDGER,
            HELPER_MODULE,
            INPUT_HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )
    packet_rows = [with_common(row, generated_at, manifest_hash) for row in comparison_packet_rows(represented_rows_in)]
    sidecar_rows = [
        with_common(row, generated_at, manifest_hash)
        for row in review_sidecar_rows(action_conflict_rows_in, unmatched_rows_in)
    ]
    scope_rows = [with_common(row, generated_at, manifest_hash) for row in comparison_scope_rows(packet_rows, sidecar_rows)]
    system_rows = [
        with_common(row, generated_at, manifest_hash)
        for row in system_comparison_rows(packet_rows, sidecar_rows, scope_rows)
    ]
    bucket_rows = [
        with_common(row, generated_at, manifest_hash)
        for row in comparison_bucket_rows(packet_rows, sidecar_rows, scope_rows, system_rows)
    ]
    role_counts = Counter(str(row.get("comparison_packet_role")) for row in packet_rows)
    sidecar_counts = Counter(str(row.get("review_sidecar_family")) for row in sidecar_rows)
    counts = {
        "input_advancement_result_ok": int(bool(input_result.get("ok"))),
        "input_represented_surface_rows": len(represented_rows_in),
        "input_action_conflict_review_rows": len(action_conflict_rows_in),
        "input_unmatched_scope_advancement_rows": len(unmatched_rows_in),
        "input_symbol_advancement_rows": len(symbol_advancement_rows_in),
        "input_system_advancement_rows": len(system_advancement_rows_in),
        "comparison_packet_rows": len(packet_rows),
        "default_off_comparison_packet_rows": role_counts.get("DEFAULT_OFF_REPLAY_SIGNAL_COMPARISON_INPUT", 0),
        "avoid_redesign_comparison_packet_rows": role_counts.get("AVOID_REDESIGN_REPLAY_SIGNAL_COMPARISON_INPUT", 0),
        "represented_context_comparison_packet_rows": role_counts.get(
            "REPRESENTED_REPLAY_CONTEXT_COMPARISON_INPUT", 0
        ),
        "review_sidecar_rows": len(sidecar_rows),
        "action_conflict_review_sidecar_rows": sidecar_counts.get("ACTION_CONFLICT_REVIEW_SIDECAR", 0),
        "unmatched_scope_review_sidecar_rows": sidecar_counts.get("UNMATCHED_SCOPE_REVIEW_SIDECAR", 0),
        "comparison_scope_rows": len(scope_rows),
        "system_comparison_rows": len(system_rows),
        "bucket_rows": len(bucket_rows),
        "source_manifest_rows": len(source_rows),
    }
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "research_boundary": research_boundary(),
        "counts": counts,
        "source_manifest_hash": manifest_hash,
        "system_comparison": system_rows[0]["system_comparison"],
        "ok": True,
    }

    write_json(RESULT_PATH, result)
    write_jsonl(COMPARISON_PACKET_LEDGER, packet_rows)
    write_jsonl(REVIEW_SIDECAR_LEDGER, sidecar_rows)
    write_jsonl(COMPARISON_SCOPE_LEDGER, scope_rows)
    write_jsonl(SYSTEM_COMPARISON_LEDGER, system_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_rows)
    write_summary(SUMMARY_PATH, generated_at, counts)
    update_output_manifest(
        [
            (RESULT_PATH, "repaired_proxy_runtime_replay_comparison_packet_result"),
            (COMPARISON_PACKET_LEDGER, "repaired_proxy_runtime_replay_comparison_packet_ledger"),
            (REVIEW_SIDECAR_LEDGER, "repaired_proxy_runtime_replay_comparison_review_sidecar_ledger"),
            (COMPARISON_SCOPE_LEDGER, "repaired_proxy_runtime_replay_comparison_scope_ledger"),
            (SYSTEM_COMPARISON_LEDGER, "repaired_proxy_runtime_replay_system_comparison_ledger"),
            (BUCKET_LEDGER, "repaired_proxy_runtime_replay_comparison_bucket_ledger"),
            (SOURCE_MANIFEST_LEDGER, "repaired_proxy_runtime_replay_comparison_source_manifest_ledger"),
            (SUMMARY_PATH, "repaired_proxy_runtime_replay_comparison_summary"),
            (BUILDER_MODULE, "repaired_proxy_runtime_replay_comparison_builder"),
            (VERIFIER_MODULE, "repaired_proxy_runtime_replay_comparison_verifier"),
        ]
    )
    replace_sprint_event(
        SPRINT_LEDGER,
        {
            "timestamp_utc": generated_at,
            "event": "repaired_proxy_runtime_replay_comparison_packet_built",
            "route": PREFIX,
            "counts": counts,
            "research_boundary": research_boundary(),
            "summary": "Materialized represented runtime replay advancement rows into comparison packet inputs.",
        },
    )
    append_checkpoint(generated_at, counts)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
