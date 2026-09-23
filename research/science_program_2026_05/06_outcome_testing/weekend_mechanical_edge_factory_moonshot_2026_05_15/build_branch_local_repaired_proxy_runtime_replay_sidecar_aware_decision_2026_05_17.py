#!/usr/bin/env python3
"""Route sidecar-aware runtime replay scores into branch-local decisions."""

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

from src.research_infra.moonshot_repaired_proxy_runtime_replay_sidecar_aware_decision import (
    RUNTIME_REPLAY_SIDECAR_AWARE_DECISION_SURFACE,
    packet_decision_rows,
    research_boundary,
    scope_decision_rows,
    sidecar_decision_bucket_rows,
    sidecar_decision_rows,
    system_decision_rows,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_SIDECAR_AWARE_SCORE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_SIDECAR_AWARE_DECISION"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
PACKET_SCORE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_PACKET_SCORE_LEDGER_2026-05-17.jsonl"
SCOPE_SCORE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SCOPE_SCORE_LEDGER_2026-05-17.jsonl"
SIDECAR_SCORE_IMPACT_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SIDECAR_SCORE_IMPACT_LEDGER_2026-05-17.jsonl"
SYSTEM_SCORE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SYSTEM_SCORE_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_runtime_replay_sidecar_aware_decision.py"
INPUT_HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_runtime_replay_sidecar_aware_score.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_repaired_proxy_runtime_replay_sidecar_aware_decision_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
PACKET_DECISION_LEDGER = ROUTE_DIR / f"{PREFIX}_PACKET_DECISION_LEDGER_2026-05-17.jsonl"
SCOPE_DECISION_LEDGER = ROUTE_DIR / f"{PREFIX}_SCOPE_DECISION_LEDGER_2026-05-17.jsonl"
SIDECAR_DECISION_LEDGER = ROUTE_DIR / f"{PREFIX}_SIDECAR_DECISION_LEDGER_2026-05-17.jsonl"
SYSTEM_DECISION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_DECISION_LEDGER_2026-05-17.jsonl"
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
                "source_manifest_id": f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-SIDECAR-DECISION-SRCMAN-{index:04d}",
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
    output.setdefault("runtime_replay_sidecar_aware_decision_surface", RUNTIME_REPLAY_SIDECAR_AWARE_DECISION_SURFACE)
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
        "# Repaired Proxy Runtime Replay Sidecar-Aware Decision",
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
    lines.extend(["", "## Continuation", "", "Build the final branch-local comparison decision bundle.", ""])
    write_text(path, "\n".join(lines))


def append_checkpoint(generated_at: str, counts: dict[str, int]) -> None:
    marker = "\n## Checkpoint 195 - Runtime Replay Sidecar-Aware Decision\n"
    existing = ""
    if ACTIVE_LEDGER.exists():
        with open(long_path(ACTIVE_LEDGER), "r", encoding="utf-8", errors="replace") as handle:
            existing = handle.read()
    if marker in existing:
        write_text(ACTIVE_LEDGER, existing.split(marker, 1)[0].rstrip() + "\n")
    text = f"""

## Checkpoint 195 - Runtime Replay Sidecar-Aware Decision

Timestamp UTC: `{generated_at}`

Trigger: continuation after Checkpoint 194. Sidecar-aware scores were routed into branch-local packet, scope, and sidecar decisions.

Outputs:

- `{counts['packet_decision_rows']}` packet decision rows from `{counts['input_packet_score_rows']}` packet scores.
- `{counts['scope_decision_rows']}` scope decision rows.
- `{counts['sidecar_decision_rows']}` sidecar decision rows preserving the score-impact denominator.

Boundary: new outputs use concrete branch-local research boundaries and do not add legacy defensive status-token blocks.

Immediate continuation: build the final branch-local comparison decision bundle.
"""
    append_text(ACTIVE_LEDGER, text)


def main() -> None:
    generated_at = now_utc()
    input_result = read_json(INPUT_RESULT)
    packet_score_rows_in = read_jsonl(PACKET_SCORE_LEDGER)
    scope_score_rows_in = read_jsonl(SCOPE_SCORE_LEDGER)
    sidecar_impact_rows_in = read_jsonl(SIDECAR_SCORE_IMPACT_LEDGER)
    system_score_rows_in = read_jsonl(SYSTEM_SCORE_LEDGER)
    source_rows, manifest_hash = source_manifest_rows(
        [
            INPUT_RESULT,
            PACKET_SCORE_LEDGER,
            SCOPE_SCORE_LEDGER,
            SIDECAR_SCORE_IMPACT_LEDGER,
            SYSTEM_SCORE_LEDGER,
            HELPER_MODULE,
            INPUT_HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )
    packet_rows = [with_common(row, generated_at, manifest_hash) for row in packet_decision_rows(packet_score_rows_in)]
    scope_rows = [with_common(row, generated_at, manifest_hash) for row in scope_decision_rows(packet_rows, scope_score_rows_in)]
    sidecar_rows = [with_common(row, generated_at, manifest_hash) for row in sidecar_decision_rows(sidecar_impact_rows_in)]
    system_rows = [
        with_common(row, generated_at, manifest_hash) for row in system_decision_rows(packet_rows, scope_rows, sidecar_rows)
    ]
    bucket_rows = [
        with_common(row, generated_at, manifest_hash)
        for row in sidecar_decision_bucket_rows(packet_rows, scope_rows, sidecar_rows, system_rows)
    ]
    packet_counts = Counter(str(row.get("packet_decision_family")) for row in packet_rows)
    scope_counts = Counter(str(row.get("scope_decision_class")) for row in scope_rows)
    sidecar_counts = Counter(str(row.get("sidecar_decision_family")) for row in sidecar_rows)
    counts = {
        "input_sidecar_score_result_ok": int(bool(input_result.get("ok"))),
        "input_packet_score_rows": len(packet_score_rows_in),
        "input_scope_score_rows": len(scope_score_rows_in),
        "input_sidecar_score_impact_rows": len(sidecar_impact_rows_in),
        "input_system_score_rows": len(system_score_rows_in),
        "packet_decision_rows": len(packet_rows),
        "packet_clear_advance_rows": packet_counts.get("PACKET_DECISION_CLEAR_ADVANCE", 0),
        "packet_context_advance_rows": packet_counts.get("PACKET_DECISION_CONTEXT_ADVANCE", 0),
        "packet_review_hold_rows": packet_counts.get("PACKET_DECISION_REVIEW_HOLD", 0),
        "packet_review_only_rows": packet_counts.get("PACKET_DECISION_REVIEW_ONLY", 0),
        "scope_decision_rows": len(scope_rows),
        "scope_clear_advance_rows": scope_counts.get("SCOPE_DECISION_HAS_CLEAR_ADVANCE_PACKET", 0),
        "scope_context_advance_rows": scope_counts.get("SCOPE_DECISION_HAS_CONTEXT_ADVANCE_PACKET", 0),
        "scope_review_held_rows": scope_counts.get("SCOPE_DECISION_REVIEW_HELD_PACKET_SCOPE", 0),
        "scope_sidecar_only_review_rows": scope_counts.get("SCOPE_DECISION_SIDECAR_ONLY_REVIEW", 0),
        "sidecar_decision_rows": len(sidecar_rows),
        "sidecar_score_damper_rows": sidecar_counts.get("SIDECAR_DECISION_SCORE_DAMPER", 0),
        "sidecar_scope_review_requirement_rows": sidecar_counts.get("SIDECAR_DECISION_SCOPE_REVIEW_REQUIREMENT", 0),
        "system_decision_rows": len(system_rows),
        "bucket_rows": len(bucket_rows),
        "source_manifest_rows": len(source_rows),
    }
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "research_boundary": research_boundary(),
        "counts": counts,
        "source_manifest_hash": manifest_hash,
        "system_decision": system_rows[0]["system_decision"],
        "ok": True,
    }

    write_json(RESULT_PATH, result)
    write_jsonl(PACKET_DECISION_LEDGER, packet_rows)
    write_jsonl(SCOPE_DECISION_LEDGER, scope_rows)
    write_jsonl(SIDECAR_DECISION_LEDGER, sidecar_rows)
    write_jsonl(SYSTEM_DECISION_LEDGER, system_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_rows)
    write_summary(SUMMARY_PATH, generated_at, counts)
    update_output_manifest(
        [
            (RESULT_PATH, "repaired_proxy_runtime_replay_sidecar_aware_decision_result"),
            (PACKET_DECISION_LEDGER, "repaired_proxy_runtime_replay_packet_decision_ledger"),
            (SCOPE_DECISION_LEDGER, "repaired_proxy_runtime_replay_scope_decision_ledger"),
            (SIDECAR_DECISION_LEDGER, "repaired_proxy_runtime_replay_sidecar_decision_ledger"),
            (SYSTEM_DECISION_LEDGER, "repaired_proxy_runtime_replay_system_decision_ledger"),
            (BUCKET_LEDGER, "repaired_proxy_runtime_replay_sidecar_decision_bucket_ledger"),
            (SOURCE_MANIFEST_LEDGER, "repaired_proxy_runtime_replay_sidecar_decision_source_manifest_ledger"),
            (SUMMARY_PATH, "repaired_proxy_runtime_replay_sidecar_decision_summary"),
            (BUILDER_MODULE, "repaired_proxy_runtime_replay_sidecar_decision_builder"),
            (VERIFIER_MODULE, "repaired_proxy_runtime_replay_sidecar_decision_verifier"),
        ]
    )
    replace_sprint_event(
        SPRINT_LEDGER,
        {
            "timestamp_utc": generated_at,
            "event": "repaired_proxy_runtime_replay_sidecar_aware_decision_built",
            "route": PREFIX,
            "counts": counts,
            "research_boundary": research_boundary(),
            "summary": "Routed sidecar-aware packet scores into branch-local decision rows.",
        },
    )
    append_checkpoint(generated_at, counts)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
