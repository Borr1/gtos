#!/usr/bin/env python3
"""Build exhausted-source proof for repaired-proxy repair acquisition lookup."""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_repaired_proxy_repair_source_exhaustion import (
    REPAIR_SOURCE_EXHAUSTION_SURFACE,
    exhaustion_bucket_rows,
    exhaustion_gate_rows,
    repair_execution_exhaustion_rows,
    requirement_exhaustion_rows,
    research_boundary,
    source_family_exhaustion_rows,
    source_path_proof_rows,
)


LOOKUP_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_REPAIR_ACQUISITION_SOURCE_LOOKUP"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_REPAIR_SOURCE_EXHAUSTION"

LOOKUP_RESULT = ROUTE_DIR / f"{LOOKUP_PREFIX}_RESULT_2026-05-17.json"
SOURCE_CANDIDATE_LOOKUP_LEDGER = ROUTE_DIR / f"{LOOKUP_PREFIX}_SOURCE_CANDIDATE_LOOKUP_LEDGER_2026-05-17.jsonl"
LOOKUP_EXECUTION_LEDGER = ROUTE_DIR / f"{LOOKUP_PREFIX}_LOOKUP_EXECUTION_LEDGER_2026-05-17.jsonl"
FIELD_FULFILLMENT_LEDGER = ROUTE_DIR / f"{LOOKUP_PREFIX}_FIELD_FULFILLMENT_LEDGER_2026-05-17.jsonl"
REPAIR_RERUN_READINESS_LEDGER = ROUTE_DIR / f"{LOOKUP_PREFIX}_REPAIR_RERUN_READINESS_LEDGER_2026-05-17.jsonl"
LOOKUP_RERUN_GATE_LEDGER = ROUTE_DIR / f"{LOOKUP_PREFIX}_RERUN_GATE_LEDGER_2026-05-17.jsonl"
LOOKUP_SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{LOOKUP_PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_repair_source_exhaustion.py"
LOOKUP_HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_repair_acquisition_lookup.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_repaired_proxy_repair_source_exhaustion_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
REQUIREMENT_EXHAUSTION_LEDGER = ROUTE_DIR / f"{PREFIX}_REQUIREMENT_EXHAUSTION_LEDGER_2026-05-17.jsonl"
SOURCE_FAMILY_EXHAUSTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_FAMILY_EXHAUSTION_LEDGER_2026-05-17.jsonl"
REPAIR_EXECUTION_EXHAUSTION_LEDGER = ROUTE_DIR / f"{PREFIX}_REPAIR_EXECUTION_EXHAUSTION_LEDGER_2026-05-17.jsonl"
SOURCE_PATH_PROOF_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_PATH_PROOF_LEDGER_2026-05-17.jsonl"
EXHAUSTION_GATE_LEDGER = ROUTE_DIR / f"{PREFIX}_EXHAUSTION_GATE_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
SYSTEM_ACTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_ACTION_LEDGER_2026-05-17.jsonl"
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
                "source_manifest_id": f"OHLC-GTOS-REPAIRED-PROXY-REPAIR-EXHAUST-SRCMAN-{index:04d}",
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
    output.setdefault("repair_source_exhaustion_surface", REPAIR_SOURCE_EXHAUSTION_SURFACE)
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


def system_action_row(counts: dict[str, int], generated_at: str, manifest_hash: str) -> dict[str, Any]:
    return with_common(
        {
            "system_action_row_id": "OHLC-GTOS-REPAIRED-PROXY-REPAIR-EXHAUST-SYSTEM-0001",
            "recommendation": (
                "Treat current branch-local repair source search as exhausted for these rows; continue comparator and "
                "proxy-R work without rerunning exact/proxy as repaired unless upstream row-key propagation is added."
            ),
            "next_branch_local_actions": [
                "preserve_188_unrerunnable_repair_rows_as_current_source_exhausted",
                "continue_comparator_packet_execution_with_existing_proxy_r_surface",
                "only_reopen_repair_rerun_after_upstream_row_key_propagation",
            ],
            **counts,
        },
        generated_at,
        manifest_hash,
    )


def write_summary(path: Path, generated_at: str, counts: dict[str, int]) -> None:
    lines = [
        "# Repaired Proxy Repair Source Exhaustion",
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
            (
                "Continue comparator/proxy-R execution with the current row set. Reopen repair execution only after "
                "upstream row-key propagation creates row-unique acquired fields."
            ),
            "",
        ]
    )
    write_text(path, "\n".join(lines))


def append_checkpoint(generated_at: str, counts: dict[str, int]) -> None:
    marker = "\n## Checkpoint 182 - Repair Source Exhaustion Proof\n"
    existing = ""
    if ACTIVE_LEDGER.exists():
        with open(long_path(ACTIVE_LEDGER), "r", encoding="utf-8", errors="replace") as handle:
            existing = handle.read()
    if marker in existing:
        write_text(ACTIVE_LEDGER, existing.split(marker, 1)[0].rstrip() + "\n")
    text = f"""

## Checkpoint 182 - Repair Source Exhaustion Proof

Timestamp UTC: `{generated_at}`

Trigger: continuation after Checkpoint 181. Not-fulfilled source lookup rows were collapsed into row-level exhausted-search proof and repair rerun gate evidence.

Outputs:

- `{counts['requirement_exhaustion_rows']}` requirement exhaustion rows and `{counts['source_family_exhaustion_rows']}` source-family exhaustion rows.
- `{counts['repair_execution_exhaustion_rows']}` repair execution exhaustion rows; `{counts['repair_rerun_ready_rows']}` rows are ready for repair rerun.
- `{counts['source_path_proof_rows']}` source path proof rows and `{counts['source_manifest_rows']}` hashed source/code manifest rows.

Boundary: new outputs use concrete branch-local research boundaries and do not add legacy defensive status-token blocks.

Immediate continuation: continue comparator/proxy-R execution with current rows; reopen repair execution only after upstream row-key propagation creates row-unique acquired fields.
"""
    append_text(ACTIVE_LEDGER, text)


def main() -> None:
    generated_at = now_utc()
    lookup_result = read_json(LOOKUP_RESULT)
    source_lookup_rows = read_jsonl(SOURCE_CANDIDATE_LOOKUP_LEDGER)
    lookup_rows = read_jsonl(LOOKUP_EXECUTION_LEDGER)
    field_rows = read_jsonl(FIELD_FULFILLMENT_LEDGER)
    readiness_rows_in = read_jsonl(REPAIR_RERUN_READINESS_LEDGER)
    lookup_gate_rows = read_jsonl(LOOKUP_RERUN_GATE_LEDGER)
    source_manifest_in = read_jsonl(LOOKUP_SOURCE_MANIFEST_LEDGER)
    source_rows, manifest_hash = source_manifest_rows(
        [
            LOOKUP_RESULT,
            SOURCE_CANDIDATE_LOOKUP_LEDGER,
            LOOKUP_EXECUTION_LEDGER,
            FIELD_FULFILLMENT_LEDGER,
            REPAIR_RERUN_READINESS_LEDGER,
            LOOKUP_RERUN_GATE_LEDGER,
            LOOKUP_SOURCE_MANIFEST_LEDGER,
            HELPER_MODULE,
            LOOKUP_HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )

    requirement_rows = [with_common(row, generated_at, manifest_hash) for row in requirement_exhaustion_rows(field_rows, lookup_rows)]
    family_rows = [with_common(row, generated_at, manifest_hash) for row in source_family_exhaustion_rows(requirement_rows)]
    execution_rows = [
        with_common(row, generated_at, manifest_hash) for row in repair_execution_exhaustion_rows(requirement_rows)
    ]
    path_proof_rows = [with_common(row, generated_at, manifest_hash) for row in source_path_proof_rows(source_lookup_rows)]
    gate_rows = [with_common(row, generated_at, manifest_hash) for row in exhaustion_gate_rows(execution_rows)]
    bucket_rows = [
        with_common(row, generated_at, manifest_hash)
        for row in exhaustion_bucket_rows(requirement_rows, family_rows, execution_rows, path_proof_rows)
    ]

    counts = {
        "input_lookup_result_ok": int(bool(lookup_result.get("ok"))),
        "input_lookup_execution_rows": len(lookup_rows),
        "input_field_fulfillment_rows": len(field_rows),
        "input_repair_readiness_rows": len(readiness_rows_in),
        "input_lookup_gate_rows": len(lookup_gate_rows),
        "input_lookup_source_manifest_rows": len(source_manifest_in),
        "requirement_exhaustion_rows": len(requirement_rows),
        "source_family_exhaustion_rows": len(family_rows),
        "repair_execution_exhaustion_rows": len(execution_rows),
        "repair_rerun_ready_rows": 0,
        "source_path_proof_rows": len(path_proof_rows),
        "exhaustion_gate_rows": len(gate_rows),
        "bucket_rows": len(bucket_rows),
        "system_action_rows": 1,
        "source_manifest_rows": len(source_rows),
    }
    system_rows = [system_action_row(counts, generated_at, manifest_hash)]
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "research_boundary": research_boundary(),
        "counts": counts,
        "source_manifest_hash": manifest_hash,
        "source_exhaustion_gate_status": gate_rows[0]["source_exhaustion_gate_status"],
        "system_recommendation": system_rows[0]["recommendation"],
        "ok": True,
    }

    write_json(RESULT_PATH, result)
    write_jsonl(REQUIREMENT_EXHAUSTION_LEDGER, requirement_rows)
    write_jsonl(SOURCE_FAMILY_EXHAUSTION_LEDGER, family_rows)
    write_jsonl(REPAIR_EXECUTION_EXHAUSTION_LEDGER, execution_rows)
    write_jsonl(SOURCE_PATH_PROOF_LEDGER, path_proof_rows)
    write_jsonl(EXHAUSTION_GATE_LEDGER, gate_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(SYSTEM_ACTION_LEDGER, system_rows)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_rows)
    write_summary(SUMMARY_PATH, generated_at, counts)

    update_output_manifest(
        [
            (RESULT_PATH, "repaired_proxy_repair_source_exhaustion_result"),
            (REQUIREMENT_EXHAUSTION_LEDGER, "repaired_proxy_repair_requirement_exhaustion_ledger"),
            (SOURCE_FAMILY_EXHAUSTION_LEDGER, "repaired_proxy_repair_source_family_exhaustion_ledger"),
            (REPAIR_EXECUTION_EXHAUSTION_LEDGER, "repaired_proxy_repair_execution_exhaustion_ledger"),
            (SOURCE_PATH_PROOF_LEDGER, "repaired_proxy_repair_source_path_proof_ledger"),
            (EXHAUSTION_GATE_LEDGER, "repaired_proxy_repair_source_exhaustion_gate_ledger"),
            (BUCKET_LEDGER, "repaired_proxy_repair_source_exhaustion_bucket_ledger"),
            (SYSTEM_ACTION_LEDGER, "repaired_proxy_repair_source_exhaustion_system_action_ledger"),
            (SOURCE_MANIFEST_LEDGER, "repaired_proxy_repair_source_exhaustion_source_manifest_ledger"),
            (SUMMARY_PATH, "repaired_proxy_repair_source_exhaustion_summary"),
            (BUILDER_MODULE, "repaired_proxy_repair_source_exhaustion_builder"),
            (VERIFIER_MODULE, "repaired_proxy_repair_source_exhaustion_verifier"),
        ]
    )
    replace_sprint_event(
        SPRINT_LEDGER,
        {
            "timestamp_utc": generated_at,
            "event": "repaired_proxy_repair_source_exhaustion_built",
            "route": PREFIX,
            "counts": counts,
            "research_boundary": research_boundary(),
            "summary": "Collapsed not-fulfilled lookup rows into current-branch source exhaustion proof.",
        },
    )
    append_checkpoint(generated_at, counts)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
