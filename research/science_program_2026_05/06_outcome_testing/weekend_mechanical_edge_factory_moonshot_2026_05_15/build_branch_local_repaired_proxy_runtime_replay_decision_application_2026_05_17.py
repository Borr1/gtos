#!/usr/bin/env python3
"""Apply runtime replay decision-bundle rows to branch-local comparison inputs."""

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

from src.research_infra.moonshot_repaired_proxy_runtime_replay_decision_application import (
    RUNTIME_REPLAY_DECISION_APPLICATION_SURFACE,
    application_bucket_rows,
    packet_application_rows,
    research_boundary,
    scope_application_rows,
    sidecar_application_rows,
    system_application_rows,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_DECISION_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_DECISION_APPLICATION"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
FINAL_PACKET_BUNDLE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_FINAL_PACKET_BUNDLE_LEDGER_2026-05-17.jsonl"
FINAL_SCOPE_BUNDLE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_FINAL_SCOPE_BUNDLE_LEDGER_2026-05-17.jsonl"
FINAL_SIDECAR_BUNDLE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_FINAL_SIDECAR_BUNDLE_LEDGER_2026-05-17.jsonl"
SYSTEM_BUNDLE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SYSTEM_BUNDLE_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_runtime_replay_decision_application.py"
INPUT_HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_runtime_replay_decision_bundle.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_repaired_proxy_runtime_replay_decision_application_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
PACKET_APPLICATION_LEDGER = ROUTE_DIR / f"{PREFIX}_PACKET_APPLICATION_LEDGER_2026-05-17.jsonl"
SCOPE_APPLICATION_LEDGER = ROUTE_DIR / f"{PREFIX}_SCOPE_APPLICATION_LEDGER_2026-05-17.jsonl"
SIDECAR_APPLICATION_LEDGER = ROUTE_DIR / f"{PREFIX}_SIDECAR_APPLICATION_LEDGER_2026-05-17.jsonl"
SYSTEM_APPLICATION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_APPLICATION_LEDGER_2026-05-17.jsonl"
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
                "source_manifest_id": f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-DECISION-APPLICATION-SRCMAN-{index:04d}",
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
    output.setdefault("runtime_replay_decision_application_surface", RUNTIME_REPLAY_DECISION_APPLICATION_SURFACE)
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
        "# Repaired Proxy Runtime Replay Decision Application",
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
    lines.extend(["", "## Continuation", "", "Compare applied clear/context packets against held review scopes.", ""])
    write_text(path, "\n".join(lines))


def append_checkpoint(generated_at: str, counts: dict[str, int]) -> None:
    marker = "\n## Checkpoint 197 - Runtime Replay Decision Application\n"
    existing = ""
    if ACTIVE_LEDGER.exists():
        with open(long_path(ACTIVE_LEDGER), "r", encoding="utf-8", errors="replace") as handle:
            existing = handle.read()
    if marker in existing:
        write_text(ACTIVE_LEDGER, existing.split(marker, 1)[0].rstrip() + "\n")
    text = f"""

## Checkpoint 197 - Runtime Replay Decision Application

Timestamp UTC: `{generated_at}`

Trigger: continuation after Checkpoint 196. Final bundle packet, scope, and sidecar rows were applied as branch-local comparison inputs or review requirements.

Outputs:

- `{counts['packet_application_rows']}` packet application rows.
- `{counts['scope_application_rows']}` scope application rows.
- `{counts['sidecar_application_rows']}` sidecar application rows.

Boundary: new outputs use concrete branch-local research boundaries and do not add legacy defensive status-token blocks.

Immediate continuation: compare applied clear/context packets against held review scopes.
"""
    append_text(ACTIVE_LEDGER, text)


def main() -> None:
    generated_at = now_utc()
    input_result = read_json(INPUT_RESULT)
    packet_bundle_rows_in = read_jsonl(FINAL_PACKET_BUNDLE_LEDGER)
    scope_bundle_rows_in = read_jsonl(FINAL_SCOPE_BUNDLE_LEDGER)
    sidecar_bundle_rows_in = read_jsonl(FINAL_SIDECAR_BUNDLE_LEDGER)
    system_bundle_rows_in = read_jsonl(SYSTEM_BUNDLE_LEDGER)
    source_rows, manifest_hash = source_manifest_rows(
        [
            INPUT_RESULT,
            FINAL_PACKET_BUNDLE_LEDGER,
            FINAL_SCOPE_BUNDLE_LEDGER,
            FINAL_SIDECAR_BUNDLE_LEDGER,
            SYSTEM_BUNDLE_LEDGER,
            HELPER_MODULE,
            INPUT_HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )
    packet_rows = [with_common(row, generated_at, manifest_hash) for row in packet_application_rows(packet_bundle_rows_in)]
    scope_rows = [with_common(row, generated_at, manifest_hash) for row in scope_application_rows(scope_bundle_rows_in, packet_rows)]
    sidecar_rows = [with_common(row, generated_at, manifest_hash) for row in sidecar_application_rows(sidecar_bundle_rows_in)]
    system_rows = [
        with_common(row, generated_at, manifest_hash) for row in system_application_rows(packet_rows, scope_rows, sidecar_rows)
    ]
    bucket_rows = [
        with_common(row, generated_at, manifest_hash)
        for row in application_bucket_rows(packet_rows, scope_rows, sidecar_rows, system_rows)
    ]
    packet_counts = Counter(str(row.get("packet_application_family")) for row in packet_rows)
    scope_counts = Counter(str(row.get("scope_application_family")) for row in scope_rows)
    sidecar_counts = Counter(str(row.get("sidecar_application_family")) for row in sidecar_rows)
    counts = {
        "input_decision_bundle_result_ok": int(bool(input_result.get("ok"))),
        "input_final_packet_bundle_rows": len(packet_bundle_rows_in),
        "input_final_scope_bundle_rows": len(scope_bundle_rows_in),
        "input_final_sidecar_bundle_rows": len(sidecar_bundle_rows_in),
        "input_system_bundle_rows": len(system_bundle_rows_in),
        "packet_application_rows": len(packet_rows),
        "packet_clear_advance_application_rows": packet_counts.get("PACKET_APPLICATION_CLEAR_ADVANCE", 0),
        "packet_context_advance_application_rows": packet_counts.get("PACKET_APPLICATION_CONTEXT_ADVANCE", 0),
        "packet_review_hold_application_rows": packet_counts.get("PACKET_APPLICATION_REVIEW_HOLD", 0),
        "packet_review_only_application_rows": packet_counts.get("PACKET_APPLICATION_REVIEW_ONLY", 0),
        "scope_application_rows": len(scope_rows),
        "scope_clear_advance_application_rows": scope_counts.get("SCOPE_APPLICATION_CLEAR_ADVANCE", 0),
        "scope_context_advance_application_rows": scope_counts.get("SCOPE_APPLICATION_CONTEXT_ADVANCE", 0),
        "scope_review_hold_application_rows": scope_counts.get("SCOPE_APPLICATION_REVIEW_HOLD", 0),
        "scope_sidecar_only_review_application_rows": scope_counts.get("SCOPE_APPLICATION_SIDECAR_ONLY_REVIEW", 0),
        "sidecar_application_rows": len(sidecar_rows),
        "sidecar_score_damper_application_rows": sidecar_counts.get("SIDECAR_APPLICATION_SCORE_DAMPER", 0),
        "sidecar_scope_review_requirement_application_rows": sidecar_counts.get(
            "SIDECAR_APPLICATION_SCOPE_REVIEW_REQUIREMENT", 0
        ),
        "system_application_rows": len(system_rows),
        "bucket_rows": len(bucket_rows),
        "source_manifest_rows": len(source_rows),
    }
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "research_boundary": research_boundary(),
        "counts": counts,
        "source_manifest_hash": manifest_hash,
        "system_application": system_rows[0]["system_application"],
        "ok": True,
    }

    write_json(RESULT_PATH, result)
    write_jsonl(PACKET_APPLICATION_LEDGER, packet_rows)
    write_jsonl(SCOPE_APPLICATION_LEDGER, scope_rows)
    write_jsonl(SIDECAR_APPLICATION_LEDGER, sidecar_rows)
    write_jsonl(SYSTEM_APPLICATION_LEDGER, system_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_rows)
    write_summary(SUMMARY_PATH, generated_at, counts)
    update_output_manifest(
        [
            (RESULT_PATH, "repaired_proxy_runtime_replay_decision_application_result"),
            (PACKET_APPLICATION_LEDGER, "repaired_proxy_runtime_replay_packet_application_ledger"),
            (SCOPE_APPLICATION_LEDGER, "repaired_proxy_runtime_replay_scope_application_ledger"),
            (SIDECAR_APPLICATION_LEDGER, "repaired_proxy_runtime_replay_sidecar_application_ledger"),
            (SYSTEM_APPLICATION_LEDGER, "repaired_proxy_runtime_replay_system_application_ledger"),
            (BUCKET_LEDGER, "repaired_proxy_runtime_replay_decision_application_bucket_ledger"),
            (SOURCE_MANIFEST_LEDGER, "repaired_proxy_runtime_replay_decision_application_source_manifest_ledger"),
            (SUMMARY_PATH, "repaired_proxy_runtime_replay_decision_application_summary"),
            (BUILDER_MODULE, "repaired_proxy_runtime_replay_decision_application_builder"),
            (VERIFIER_MODULE, "repaired_proxy_runtime_replay_decision_application_verifier"),
        ]
    )
    replace_sprint_event(
        SPRINT_LEDGER,
        {
            "timestamp_utc": generated_at,
            "event": "repaired_proxy_runtime_replay_decision_application_built",
            "route": PREFIX,
            "counts": counts,
            "research_boundary": research_boundary(),
            "summary": "Applied runtime replay decision bundle rows as branch-local comparison inputs.",
        },
    )
    append_checkpoint(generated_at, counts)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
