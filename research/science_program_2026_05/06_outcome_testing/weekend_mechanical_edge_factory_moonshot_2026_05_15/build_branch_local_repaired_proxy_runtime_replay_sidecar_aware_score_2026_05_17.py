#!/usr/bin/env python3
"""Score runtime replay comparison packet rows with sidecar-aware scope context."""

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

from src.research_infra.moonshot_repaired_proxy_runtime_replay_sidecar_aware_score import (
    RUNTIME_REPLAY_SIDECAR_AWARE_SCORE_SURFACE,
    packet_score_rows,
    research_boundary,
    scope_score_rows,
    sidecar_score_bucket_rows,
    sidecar_score_impact_rows,
    system_score_rows,
)


SUMMARY_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_COMPARISON_SUMMARY"
PACKET_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_COMPARISON_PACKET"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_SIDECAR_AWARE_SCORE"

INPUT_RESULT = ROUTE_DIR / f"{SUMMARY_PREFIX}_RESULT_2026-05-17.json"
COMPARISON_PACKET_LEDGER = ROUTE_DIR / f"{PACKET_PREFIX}_COMPARISON_PACKET_LEDGER_2026-05-17.jsonl"
SCOPE_COMPARISON_LEDGER = ROUTE_DIR / f"{SUMMARY_PREFIX}_SCOPE_COMPARISON_LEDGER_2026-05-17.jsonl"
SIGNAL_COMPARISON_LEDGER = ROUTE_DIR / f"{SUMMARY_PREFIX}_SIGNAL_COMPARISON_LEDGER_2026-05-17.jsonl"
SIDECAR_ATTACHMENT_LEDGER = ROUTE_DIR / f"{SUMMARY_PREFIX}_SIDECAR_ATTACHMENT_LEDGER_2026-05-17.jsonl"
SYSTEM_SUMMARY_LEDGER = ROUTE_DIR / f"{SUMMARY_PREFIX}_SYSTEM_SUMMARY_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_runtime_replay_sidecar_aware_score.py"
INPUT_HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_runtime_replay_comparison_summary.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_repaired_proxy_runtime_replay_sidecar_aware_score_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
PACKET_SCORE_LEDGER = ROUTE_DIR / f"{PREFIX}_PACKET_SCORE_LEDGER_2026-05-17.jsonl"
SCOPE_SCORE_LEDGER = ROUTE_DIR / f"{PREFIX}_SCOPE_SCORE_LEDGER_2026-05-17.jsonl"
SIDECAR_SCORE_IMPACT_LEDGER = ROUTE_DIR / f"{PREFIX}_SIDECAR_SCORE_IMPACT_LEDGER_2026-05-17.jsonl"
SYSTEM_SCORE_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_SCORE_LEDGER_2026-05-17.jsonl"
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
                "source_manifest_id": f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-SIDECAR-SCORE-SRCMAN-{index:04d}",
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
    output.setdefault("runtime_replay_sidecar_aware_score_surface", RUNTIME_REPLAY_SIDECAR_AWARE_SCORE_SURFACE)
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
        "# Repaired Proxy Runtime Replay Sidecar-Aware Score",
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
    lines.extend(["", "## Continuation", "", "Route scored packet rows into sidecar-aware comparison decisions.", ""])
    write_text(path, "\n".join(lines))


def append_checkpoint(generated_at: str, counts: dict[str, int]) -> None:
    marker = "\n## Checkpoint 194 - Runtime Replay Sidecar-Aware Score\n"
    existing = ""
    if ACTIVE_LEDGER.exists():
        with open(long_path(ACTIVE_LEDGER), "r", encoding="utf-8", errors="replace") as handle:
            existing = handle.read()
    if marker in existing:
        write_text(ACTIVE_LEDGER, existing.split(marker, 1)[0].rstrip() + "\n")
    text = f"""

## Checkpoint 194 - Runtime Replay Sidecar-Aware Score

Timestamp UTC: `{generated_at}`

Trigger: continuation after Checkpoint 193. Represented comparison packet rows were scored with sidecar-aware scope classes and every sidecar attachment row received a score-impact classification.

Outputs:

- `{counts['packet_score_rows']}` packet score rows from `{counts['input_comparison_packet_rows']}` comparison packet rows.
- `{counts['scope_score_rows']}` scope score rows.
- `{counts['sidecar_score_impact_rows']}` sidecar score-impact rows preserving the sidecar denominator.

Boundary: new outputs use concrete branch-local research boundaries and do not add legacy defensive status-token blocks.

Immediate continuation: route scored packet rows into sidecar-aware comparison decisions.
"""
    append_text(ACTIVE_LEDGER, text)


def main() -> None:
    generated_at = now_utc()
    input_result = read_json(INPUT_RESULT)
    comparison_packet_rows_in = read_jsonl(COMPARISON_PACKET_LEDGER)
    scope_comparison_rows_in = read_jsonl(SCOPE_COMPARISON_LEDGER)
    signal_comparison_rows_in = read_jsonl(SIGNAL_COMPARISON_LEDGER)
    sidecar_attachment_rows_in = read_jsonl(SIDECAR_ATTACHMENT_LEDGER)
    system_summary_rows_in = read_jsonl(SYSTEM_SUMMARY_LEDGER)
    source_rows, manifest_hash = source_manifest_rows(
        [
            INPUT_RESULT,
            COMPARISON_PACKET_LEDGER,
            SCOPE_COMPARISON_LEDGER,
            SIGNAL_COMPARISON_LEDGER,
            SIDECAR_ATTACHMENT_LEDGER,
            SYSTEM_SUMMARY_LEDGER,
            HELPER_MODULE,
            INPUT_HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )
    packet_scores = [
        with_common(row, generated_at, manifest_hash)
        for row in packet_score_rows(comparison_packet_rows_in, scope_comparison_rows_in, signal_comparison_rows_in)
    ]
    scope_scores = [with_common(row, generated_at, manifest_hash) for row in scope_score_rows(packet_scores, scope_comparison_rows_in)]
    impact_rows = [
        with_common(row, generated_at, manifest_hash)
        for row in sidecar_score_impact_rows(sidecar_attachment_rows_in, scope_comparison_rows_in)
    ]
    system_rows = [
        with_common(row, generated_at, manifest_hash) for row in system_score_rows(packet_scores, scope_scores, impact_rows)
    ]
    bucket_rows = [
        with_common(row, generated_at, manifest_hash)
        for row in sidecar_score_bucket_rows(packet_scores, scope_scores, impact_rows, system_rows)
    ]
    score_classes = Counter(str(row.get("sidecar_aware_score_class")) for row in packet_scores)
    impact_classes = Counter(str(row.get("sidecar_score_impact_class")) for row in impact_rows)
    counts = {
        "input_comparison_summary_result_ok": int(bool(input_result.get("ok"))),
        "input_comparison_packet_rows": len(comparison_packet_rows_in),
        "input_scope_comparison_rows": len(scope_comparison_rows_in),
        "input_signal_comparison_rows": len(signal_comparison_rows_in),
        "input_sidecar_attachment_rows": len(sidecar_attachment_rows_in),
        "input_system_summary_rows": len(system_summary_rows_in),
        "packet_score_rows": len(packet_scores),
        "score_high_clear_rows": score_classes.get("COMPARISON_SCORE_HIGH_CLEAR", 0),
        "score_usable_with_context_rows": score_classes.get("COMPARISON_SCORE_USABLE_WITH_CONTEXT", 0),
        "score_context_or_damped_rows": score_classes.get("COMPARISON_SCORE_CONTEXT_ONLY_OR_SIDECAR_DAMPED", 0),
        "score_review_only_rows": score_classes.get("COMPARISON_SCORE_REVIEW_ONLY", 0),
        "scope_score_rows": len(scope_scores),
        "sidecar_score_impact_rows": len(impact_rows),
        "sidecar_damps_represented_scope_rows": impact_classes.get("SIDECAR_DAMPS_REPRESENTED_SCOPE_SCORE", 0),
        "sidecar_held_for_scope_review_rows": impact_classes.get("SIDECAR_HELD_FOR_SCOPE_REVIEW", 0),
        "system_score_rows": len(system_rows),
        "bucket_rows": len(bucket_rows),
        "source_manifest_rows": len(source_rows),
    }
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "research_boundary": research_boundary(),
        "counts": counts,
        "source_manifest_hash": manifest_hash,
        "system_score": system_rows[0]["system_score"],
        "ok": True,
    }

    write_json(RESULT_PATH, result)
    write_jsonl(PACKET_SCORE_LEDGER, packet_scores)
    write_jsonl(SCOPE_SCORE_LEDGER, scope_scores)
    write_jsonl(SIDECAR_SCORE_IMPACT_LEDGER, impact_rows)
    write_jsonl(SYSTEM_SCORE_LEDGER, system_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_rows)
    write_summary(SUMMARY_PATH, generated_at, counts)
    update_output_manifest(
        [
            (RESULT_PATH, "repaired_proxy_runtime_replay_sidecar_aware_score_result"),
            (PACKET_SCORE_LEDGER, "repaired_proxy_runtime_replay_packet_score_ledger"),
            (SCOPE_SCORE_LEDGER, "repaired_proxy_runtime_replay_scope_score_ledger"),
            (SIDECAR_SCORE_IMPACT_LEDGER, "repaired_proxy_runtime_replay_sidecar_score_impact_ledger"),
            (SYSTEM_SCORE_LEDGER, "repaired_proxy_runtime_replay_system_score_ledger"),
            (BUCKET_LEDGER, "repaired_proxy_runtime_replay_sidecar_score_bucket_ledger"),
            (SOURCE_MANIFEST_LEDGER, "repaired_proxy_runtime_replay_sidecar_score_source_manifest_ledger"),
            (SUMMARY_PATH, "repaired_proxy_runtime_replay_sidecar_score_summary"),
            (BUILDER_MODULE, "repaired_proxy_runtime_replay_sidecar_score_builder"),
            (VERIFIER_MODULE, "repaired_proxy_runtime_replay_sidecar_score_verifier"),
        ]
    )
    replace_sprint_event(
        SPRINT_LEDGER,
        {
            "timestamp_utc": generated_at,
            "event": "repaired_proxy_runtime_replay_sidecar_aware_score_built",
            "route": PREFIX,
            "counts": counts,
            "research_boundary": research_boundary(),
            "summary": "Scored runtime replay comparison packet rows with sidecar-aware scope classes.",
        },
    )
    append_checkpoint(generated_at, counts)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
