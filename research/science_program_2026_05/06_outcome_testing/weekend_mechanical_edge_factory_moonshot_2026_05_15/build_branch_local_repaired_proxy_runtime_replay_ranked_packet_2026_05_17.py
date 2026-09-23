#!/usr/bin/env python3
"""Rank advance runtime replay packets with held-scope context."""

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

from src.research_infra.moonshot_repaired_proxy_runtime_replay_ranked_packet import (
    RUNTIME_REPLAY_RANKED_PACKET_SURFACE,
    held_scope_context_rows,
    next_branch_local_packet_rows,
    ranked_advance_packet_rows,
    ranked_packet_bucket_rows,
    research_boundary,
    system_ranked_packet_rows,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_DECISION_APPLICATION_COMPARISON"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_RANKED_PACKET"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
ADVANCE_PACKET_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_ADVANCE_PACKET_LEDGER_2026-05-17.jsonl"
HELD_REVIEW_SCOPE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_HELD_REVIEW_SCOPE_LEDGER_2026-05-17.jsonl"
SYSTEM_COMPARISON_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SYSTEM_REVIEW_COMPARISON_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_runtime_replay_ranked_packet.py"
INPUT_HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_runtime_replay_decision_application_comparison.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_repaired_proxy_runtime_replay_ranked_packet_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
RANKED_ADVANCE_PACKET_LEDGER = ROUTE_DIR / f"{PREFIX}_RANKED_ADVANCE_PACKET_LEDGER_2026-05-17.jsonl"
HELD_SCOPE_CONTEXT_LEDGER = ROUTE_DIR / f"{PREFIX}_HELD_SCOPE_CONTEXT_LEDGER_2026-05-17.jsonl"
NEXT_BRANCH_LOCAL_PACKET_LEDGER = ROUTE_DIR / f"{PREFIX}_NEXT_BRANCH_LOCAL_PACKET_LEDGER_2026-05-17.jsonl"
SYSTEM_RANKED_PACKET_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_RANKED_PACKET_LEDGER_2026-05-17.jsonl"
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
                "source_manifest_id": f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-RANKED-PACKET-SRCMAN-{index:04d}",
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
    output.setdefault("runtime_replay_ranked_packet_surface", RUNTIME_REPLAY_RANKED_PACKET_SURFACE)
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
        "# Repaired Proxy Runtime Replay Ranked Packet",
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
            "Join ranked branch-local packets to scorer/comparator action families and emit implementation next steps.",
            "",
        ]
    )
    write_text(path, "\n".join(lines))


def append_checkpoint(generated_at: str, counts: dict[str, int]) -> None:
    marker = "\n## Checkpoint 199 - Runtime Replay Ranked Packet\n"
    existing = ""
    if ACTIVE_LEDGER.exists():
        with open(long_path(ACTIVE_LEDGER), "r", encoding="utf-8", errors="replace") as handle:
            existing = handle.read()
    if marker in existing:
        write_text(ACTIVE_LEDGER, existing.split(marker, 1)[0].rstrip() + "\n")
    text = f"""

## Checkpoint 199 - Runtime Replay Ranked Packet

Timestamp UTC: `{generated_at}`

Trigger: continuation after Checkpoint 198. Advance packets were ranked with held-scope context and carried into the next branch-local packet.

Outputs:

- `{counts['ranked_advance_packet_rows']}` ranked advance packet rows.
- `{counts['held_scope_context_rows']}` held-scope context rows.
- `{counts['next_branch_local_packet_rows']}` next branch-local packet rows.

Boundary: new outputs use concrete branch-local research boundaries and do not add legacy defensive status-token blocks.

Immediate continuation: join ranked branch-local packets to scorer/comparator action families and emit implementation next steps.
"""
    append_text(ACTIVE_LEDGER, text)


def main() -> None:
    generated_at = now_utc()
    input_result = read_json(INPUT_RESULT)
    advance_packet_rows_in = read_jsonl(ADVANCE_PACKET_LEDGER)
    held_review_scope_rows_in = read_jsonl(HELD_REVIEW_SCOPE_LEDGER)
    system_comparison_rows_in = read_jsonl(SYSTEM_COMPARISON_LEDGER)
    source_rows, manifest_hash = source_manifest_rows(
        [
            INPUT_RESULT,
            ADVANCE_PACKET_LEDGER,
            HELD_REVIEW_SCOPE_LEDGER,
            SYSTEM_COMPARISON_LEDGER,
            HELPER_MODULE,
            INPUT_HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )

    held_context_rows = [
        with_common(row, generated_at, manifest_hash) for row in held_scope_context_rows(held_review_scope_rows_in)
    ]
    ranked_rows = [
        with_common(row, generated_at, manifest_hash)
        for row in ranked_advance_packet_rows(advance_packet_rows_in, held_context_rows)
    ]
    next_packet_rows = [
        with_common(row, generated_at, manifest_hash) for row in next_branch_local_packet_rows(ranked_rows)
    ]
    system_rows = [
        with_common(row, generated_at, manifest_hash)
        for row in system_ranked_packet_rows(ranked_rows, held_context_rows, next_packet_rows)
    ]
    bucket_rows = [
        with_common(row, generated_at, manifest_hash)
        for row in ranked_packet_bucket_rows(ranked_rows, held_context_rows, next_packet_rows, system_rows)
    ]

    tier_counts = Counter(str(row.get("packet_rank_tier")) for row in ranked_rows)
    counts = {
        "input_decision_application_comparison_result_ok": int(bool(input_result.get("ok"))),
        "input_advance_packet_rows": len(advance_packet_rows_in),
        "input_held_review_scope_rows": len(held_review_scope_rows_in),
        "input_system_comparison_rows": len(system_comparison_rows_in),
        "ranked_advance_packet_rows": len(ranked_rows),
        "held_scope_context_rows": len(held_context_rows),
        "next_branch_local_packet_rows": len(next_packet_rows),
        "ranked_direct_clear_batch_rows": tier_counts.get("RANKED_PACKET_DIRECT_CLEAR_BATCH", 0),
        "ranked_advance_ready_batch_rows": tier_counts.get("RANKED_PACKET_ADVANCE_READY_BATCH", 0),
        "ranked_advance_with_context_batch_rows": tier_counts.get("RANKED_PACKET_ADVANCE_WITH_CONTEXT_BATCH", 0),
        "ranked_advance_with_held_scope_pressure_rows": tier_counts.get(
            "RANKED_PACKET_ADVANCE_WITH_HELD_SCOPE_PRESSURE", 0
        ),
        "ranked_advance_low_priority_context_rows": tier_counts.get(
            "RANKED_PACKET_ADVANCE_LOW_PRIORITY_CONTEXT", 0
        ),
        "system_ranked_packet_rows": len(system_rows),
        "bucket_rows": len(bucket_rows),
        "source_manifest_rows": len(source_rows),
    }
    result = with_common(
        {
            "artifact": PREFIX,
            "ok": True,
            "generated_utc": generated_at,
            "counts": counts,
            "system_ranked_packet": system_rows[0]["system_ranked_packet"],
        },
        generated_at,
        manifest_hash,
    )

    write_json(RESULT_PATH, result)
    write_jsonl(RANKED_ADVANCE_PACKET_LEDGER, ranked_rows)
    write_jsonl(HELD_SCOPE_CONTEXT_LEDGER, held_context_rows)
    write_jsonl(NEXT_BRANCH_LOCAL_PACKET_LEDGER, next_packet_rows)
    write_jsonl(SYSTEM_RANKED_PACKET_LEDGER, system_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_rows)
    write_summary(SUMMARY_PATH, generated_at, counts)
    update_output_manifest(
        [
            (RESULT_PATH, "runtime_replay_ranked_packet_result"),
            (RANKED_ADVANCE_PACKET_LEDGER, "runtime_replay_ranked_advance_packet_ledger"),
            (HELD_SCOPE_CONTEXT_LEDGER, "runtime_replay_ranked_packet_held_scope_context_ledger"),
            (NEXT_BRANCH_LOCAL_PACKET_LEDGER, "runtime_replay_next_branch_local_packet_ledger"),
            (SYSTEM_RANKED_PACKET_LEDGER, "runtime_replay_ranked_packet_system_ledger"),
            (BUCKET_LEDGER, "runtime_replay_ranked_packet_bucket_ledger"),
            (SOURCE_MANIFEST_LEDGER, "runtime_replay_ranked_packet_source_manifest"),
            (SUMMARY_PATH, "runtime_replay_ranked_packet_summary"),
            (BUILDER_MODULE, "runtime_replay_ranked_packet_builder"),
            (VERIFIER_MODULE, "runtime_replay_ranked_packet_verifier"),
            (HELPER_MODULE, "runtime_replay_ranked_packet_helper"),
        ]
    )
    replace_sprint_event(
        SPRINT_LEDGER,
        {
            "event": "checkpoint_199_runtime_replay_ranked_packet",
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
