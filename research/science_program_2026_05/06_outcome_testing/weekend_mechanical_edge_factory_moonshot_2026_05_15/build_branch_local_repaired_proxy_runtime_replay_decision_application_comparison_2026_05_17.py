#!/usr/bin/env python3
"""Compare decision-application packets against held review scopes."""

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

from src.research_infra.moonshot_repaired_proxy_runtime_replay_decision_application_comparison import (
    RUNTIME_REPLAY_DECISION_APPLICATION_COMPARISON_SURFACE,
    advance_packet_rows,
    comparison_bucket_rows,
    held_review_scope_rows,
    packet_scope_comparison_rows,
    research_boundary,
    scope_review_comparison_rows,
    sidecar_scope_comparison_rows,
    system_review_comparison_rows,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_DECISION_APPLICATION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_DECISION_APPLICATION_COMPARISON"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
PACKET_APPLICATION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_PACKET_APPLICATION_LEDGER_2026-05-17.jsonl"
SCOPE_APPLICATION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SCOPE_APPLICATION_LEDGER_2026-05-17.jsonl"
SIDECAR_APPLICATION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SIDECAR_APPLICATION_LEDGER_2026-05-17.jsonl"
SYSTEM_APPLICATION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SYSTEM_APPLICATION_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_runtime_replay_decision_application_comparison.py"
INPUT_HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_runtime_replay_decision_application.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_repaired_proxy_runtime_replay_decision_application_comparison_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
SCOPE_REVIEW_COMPARISON_LEDGER = ROUTE_DIR / f"{PREFIX}_SCOPE_REVIEW_COMPARISON_LEDGER_2026-05-17.jsonl"
PACKET_SCOPE_COMPARISON_LEDGER = ROUTE_DIR / f"{PREFIX}_PACKET_SCOPE_COMPARISON_LEDGER_2026-05-17.jsonl"
SIDECAR_SCOPE_COMPARISON_LEDGER = ROUTE_DIR / f"{PREFIX}_SIDECAR_SCOPE_COMPARISON_LEDGER_2026-05-17.jsonl"
ADVANCE_PACKET_LEDGER = ROUTE_DIR / f"{PREFIX}_ADVANCE_PACKET_LEDGER_2026-05-17.jsonl"
HELD_REVIEW_SCOPE_LEDGER = ROUTE_DIR / f"{PREFIX}_HELD_REVIEW_SCOPE_LEDGER_2026-05-17.jsonl"
SYSTEM_REVIEW_COMPARISON_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_REVIEW_COMPARISON_LEDGER_2026-05-17.jsonl"
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
                "source_manifest_id": (
                    f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-APPLICATION-COMPARISON-SRCMAN-{index:04d}"
                ),
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
    output.setdefault(
        "runtime_replay_decision_application_comparison_surface",
        RUNTIME_REPLAY_DECISION_APPLICATION_COMPARISON_SURFACE,
    )
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
        "# Repaired Proxy Runtime Replay Decision Application Comparison",
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
            "Rank advance packets with held-scope context and materialize the next branch-local packet.",
            "",
        ]
    )
    write_text(path, "\n".join(lines))


def append_checkpoint(generated_at: str, counts: dict[str, int]) -> None:
    marker = "\n## Checkpoint 198 - Runtime Replay Decision Application Comparison\n"
    existing = ""
    if ACTIVE_LEDGER.exists():
        with open(long_path(ACTIVE_LEDGER), "r", encoding="utf-8", errors="replace") as handle:
            existing = handle.read()
    if marker in existing:
        write_text(ACTIVE_LEDGER, existing.split(marker, 1)[0].rstrip() + "\n")
    text = f"""

## Checkpoint 198 - Runtime Replay Decision Application Comparison

Timestamp UTC: `{generated_at}`

Trigger: continuation after Checkpoint 197. Clear/context packet applications were compared with held packet scopes and sidecar-only review scopes.

Outputs:

- `{counts['scope_review_comparison_rows']}` scope review-comparison rows.
- `{counts['packet_scope_comparison_rows']}` packet scope-comparison rows.
- `{counts['sidecar_scope_comparison_rows']}` sidecar scope-comparison rows.
- `{counts['advance_packet_rows']}` advance packet rows selected for the next branch-local packet.
- `{counts['held_review_scope_rows']}` held review scope rows retained as comparison context.

Boundary: new outputs use concrete branch-local research boundaries and do not add legacy defensive status-token blocks.

Immediate continuation: rank advance packets with held-scope context and materialize the next branch-local packet.
"""
    append_text(ACTIVE_LEDGER, text)


def main() -> None:
    generated_at = now_utc()
    input_result = read_json(INPUT_RESULT)
    packet_application_rows_in = read_jsonl(PACKET_APPLICATION_LEDGER)
    scope_application_rows_in = read_jsonl(SCOPE_APPLICATION_LEDGER)
    sidecar_application_rows_in = read_jsonl(SIDECAR_APPLICATION_LEDGER)
    system_application_rows_in = read_jsonl(SYSTEM_APPLICATION_LEDGER)
    source_rows, manifest_hash = source_manifest_rows(
        [
            INPUT_RESULT,
            PACKET_APPLICATION_LEDGER,
            SCOPE_APPLICATION_LEDGER,
            SIDECAR_APPLICATION_LEDGER,
            SYSTEM_APPLICATION_LEDGER,
            HELPER_MODULE,
            INPUT_HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )

    scope_rows = [
        with_common(row, generated_at, manifest_hash)
        for row in scope_review_comparison_rows(
            scope_application_rows_in,
            packet_application_rows_in,
            sidecar_application_rows_in,
        )
    ]
    packet_rows = [
        with_common(row, generated_at, manifest_hash)
        for row in packet_scope_comparison_rows(packet_application_rows_in, scope_rows)
    ]
    sidecar_rows = [
        with_common(row, generated_at, manifest_hash)
        for row in sidecar_scope_comparison_rows(sidecar_application_rows_in, scope_rows)
    ]
    advance_rows = [with_common(row, generated_at, manifest_hash) for row in advance_packet_rows(packet_rows)]
    held_scope_rows = [with_common(row, generated_at, manifest_hash) for row in held_review_scope_rows(scope_rows)]
    system_rows = [
        with_common(row, generated_at, manifest_hash)
        for row in system_review_comparison_rows(scope_rows, packet_rows, sidecar_rows, advance_rows, held_scope_rows)
    ]
    bucket_rows = [
        with_common(row, generated_at, manifest_hash)
        for row in comparison_bucket_rows(
            scope_rows,
            packet_rows,
            sidecar_rows,
            advance_rows,
            held_scope_rows,
            system_rows,
        )
    ]

    scope_counts = Counter(str(row.get("scope_review_comparison_class")) for row in scope_rows)
    packet_counts = Counter(str(row.get("packet_scope_comparison_family")) for row in packet_rows)
    sidecar_counts = Counter(str(row.get("sidecar_scope_comparison_family")) for row in sidecar_rows)
    counts = {
        "input_decision_application_result_ok": int(bool(input_result.get("ok"))),
        "input_packet_application_rows": len(packet_application_rows_in),
        "input_scope_application_rows": len(scope_application_rows_in),
        "input_sidecar_application_rows": len(sidecar_application_rows_in),
        "input_system_application_rows": len(system_application_rows_in),
        "scope_review_comparison_rows": len(scope_rows),
        "packet_scope_comparison_rows": len(packet_rows),
        "sidecar_scope_comparison_rows": len(sidecar_rows),
        "advance_packet_rows": len(advance_rows),
        "held_review_scope_rows": len(held_scope_rows),
        "scope_clear_ready_rows": scope_counts.get("SCOPE_REVIEW_COMPARISON_CLEAR_ADVANCE_READY", 0),
        "scope_clear_with_review_context_rows": scope_counts.get(
            "SCOPE_REVIEW_COMPARISON_CLEAR_ADVANCE_WITH_ATTACHED_REVIEW_CONTEXT", 0
        ),
        "scope_context_ready_rows": scope_counts.get("SCOPE_REVIEW_COMPARISON_CONTEXT_ADVANCE_READY", 0),
        "scope_context_with_review_context_rows": scope_counts.get(
            "SCOPE_REVIEW_COMPARISON_CONTEXT_ADVANCE_WITH_ATTACHED_REVIEW_CONTEXT", 0
        ),
        "scope_held_packet_rows": scope_counts.get("SCOPE_REVIEW_COMPARISON_HELD_SCOPE_WITH_HELD_PACKETS", 0),
        "scope_sidecar_only_held_rows": scope_counts.get("SCOPE_REVIEW_COMPARISON_SIDECAR_ONLY_HELD_SCOPE", 0),
        "packet_advance_with_advance_scope_rows": packet_counts.get(
            "PACKET_SCOPE_COMPARISON_ADVANCE_PACKET_WITH_ADVANCE_SCOPE", 0
        ),
        "packet_advance_against_held_scope_rows": packet_counts.get(
            "PACKET_SCOPE_COMPARISON_ADVANCE_PACKET_AGAINST_HELD_SCOPE", 0
        ),
        "packet_held_with_held_scope_rows": packet_counts.get(
            "PACKET_SCOPE_COMPARISON_HELD_PACKET_WITH_HELD_SCOPE", 0
        ),
        "packet_held_attached_to_advance_scope_rows": packet_counts.get(
            "PACKET_SCOPE_COMPARISON_HELD_PACKET_ATTACHED_TO_ADVANCE_SCOPE", 0
        ),
        "sidecar_score_damper_on_advance_scope_rows": sidecar_counts.get(
            "SIDECAR_SCOPE_COMPARISON_SCORE_DAMPER_ON_ADVANCE_SCOPE", 0
        ),
        "sidecar_score_damper_on_held_scope_rows": sidecar_counts.get(
            "SIDECAR_SCOPE_COMPARISON_SCORE_DAMPER_ON_HELD_SCOPE", 0
        ),
        "sidecar_requirement_on_advance_scope_rows": sidecar_counts.get(
            "SIDECAR_SCOPE_COMPARISON_REVIEW_REQUIREMENT_ON_ADVANCE_SCOPE", 0
        ),
        "sidecar_requirement_on_held_scope_rows": sidecar_counts.get(
            "SIDECAR_SCOPE_COMPARISON_REVIEW_REQUIREMENT_ON_HELD_SCOPE", 0
        ),
        "system_review_comparison_rows": len(system_rows),
        "bucket_rows": len(bucket_rows),
        "source_manifest_rows": len(source_rows),
    }
    result = with_common(
        {
            "artifact": PREFIX,
            "ok": True,
            "generated_utc": generated_at,
            "counts": counts,
            "system_review_comparison": system_rows[0]["system_review_comparison"],
        },
        generated_at,
        manifest_hash,
    )

    write_json(RESULT_PATH, result)
    write_jsonl(SCOPE_REVIEW_COMPARISON_LEDGER, scope_rows)
    write_jsonl(PACKET_SCOPE_COMPARISON_LEDGER, packet_rows)
    write_jsonl(SIDECAR_SCOPE_COMPARISON_LEDGER, sidecar_rows)
    write_jsonl(ADVANCE_PACKET_LEDGER, advance_rows)
    write_jsonl(HELD_REVIEW_SCOPE_LEDGER, held_scope_rows)
    write_jsonl(SYSTEM_REVIEW_COMPARISON_LEDGER, system_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_rows)
    write_summary(SUMMARY_PATH, generated_at, counts)
    update_output_manifest(
        [
            (RESULT_PATH, "runtime_replay_decision_application_comparison_result"),
            (SCOPE_REVIEW_COMPARISON_LEDGER, "runtime_replay_decision_application_comparison_scope_ledger"),
            (PACKET_SCOPE_COMPARISON_LEDGER, "runtime_replay_decision_application_comparison_packet_ledger"),
            (SIDECAR_SCOPE_COMPARISON_LEDGER, "runtime_replay_decision_application_comparison_sidecar_ledger"),
            (ADVANCE_PACKET_LEDGER, "runtime_replay_decision_application_comparison_advance_packet_ledger"),
            (HELD_REVIEW_SCOPE_LEDGER, "runtime_replay_decision_application_comparison_held_scope_ledger"),
            (SYSTEM_REVIEW_COMPARISON_LEDGER, "runtime_replay_decision_application_comparison_system_ledger"),
            (BUCKET_LEDGER, "runtime_replay_decision_application_comparison_bucket_ledger"),
            (SOURCE_MANIFEST_LEDGER, "runtime_replay_decision_application_comparison_source_manifest"),
            (SUMMARY_PATH, "runtime_replay_decision_application_comparison_summary"),
            (BUILDER_MODULE, "runtime_replay_decision_application_comparison_builder"),
            (VERIFIER_MODULE, "runtime_replay_decision_application_comparison_verifier"),
            (HELPER_MODULE, "runtime_replay_decision_application_comparison_helper"),
        ]
    )
    replace_sprint_event(
        SPRINT_LEDGER,
        {
            "event": "checkpoint_198_runtime_replay_decision_application_comparison",
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
