#!/usr/bin/env python3
"""Build acquisition requirements for blocked repaired-proxy repair executions."""

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

from src.research_infra.moonshot_repaired_proxy_repair_acquisition import (
    REPAIR_ACQUISITION_SURFACE,
    acquisition_batch_rows,
    acquisition_requirement_rows,
    bucket_rows,
    research_boundary,
    source_candidate_rows,
    unblock_plan_rows,
)


EXEC_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_REPAIR_WORK_EXECUTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_REPAIR_FIELD_ACQUISITION"

EXEC_RESULT = ROUTE_DIR / f"{EXEC_PREFIX}_RESULT_2026-05-17.json"
REPAIR_EXECUTION_LEDGER = ROUTE_DIR / f"{EXEC_PREFIX}_REPAIR_EXECUTION_LEDGER_2026-05-17.jsonl"
FIELD_COVERAGE_LEDGER = ROUTE_DIR / f"{EXEC_PREFIX}_FIELD_COVERAGE_LEDGER_2026-05-17.jsonl"
RERUN_GATE_LEDGER = ROUTE_DIR / f"{EXEC_PREFIX}_RERUN_GATE_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_repair_acquisition.py"
EXEC_HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_repair_execution.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_repaired_proxy_repair_acquisition_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
ACQUISITION_REQUIREMENT_LEDGER = ROUTE_DIR / f"{PREFIX}_ACQUISITION_REQUIREMENT_LEDGER_2026-05-17.jsonl"
ACQUISITION_BATCH_LEDGER = ROUTE_DIR / f"{PREFIX}_ACQUISITION_BATCH_LEDGER_2026-05-17.jsonl"
SOURCE_CANDIDATE_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_CANDIDATE_LEDGER_2026-05-17.jsonl"
UNBLOCK_PLAN_LEDGER = ROUTE_DIR / f"{PREFIX}_UNBLOCK_PLAN_LEDGER_2026-05-17.jsonl"
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
                "source_manifest_id": f"OHLC-GTOS-REPAIRED-PROXY-REPAIR-ACQ-SRCMAN-{index:04d}",
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
    output.setdefault("repair_acquisition_surface", REPAIR_ACQUISITION_SURFACE)
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
            "system_action_row_id": "OHLC-GTOS-REPAIRED-PROXY-REPAIR-ACQ-SYSTEM-0001",
            "recommendation": (
                "Run branch-local lookups for each acquisition requirement, rerun repair execution after fields are "
                "supplied, and keep exact/proxy rerun gated until repaired rows become eligible."
            ),
            "next_branch_local_actions": [
                "lookup_candidate_or_decision_identifiers",
                "lookup_broker_order_deal_tickets",
                "lookup_candidate_lock_or_decision_metadata",
                "lookup_scope_identity_fields",
                "rerun_repair_execution_after_acquisition",
            ],
            **counts,
        },
        generated_at,
        manifest_hash,
    )


def write_summary(path: Path, generated_at: str, counts: dict[str, int]) -> None:
    lines = [
        "# Repaired Proxy Repair Field Acquisition",
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
                "Run branch-local source lookups for acquisition requirements, rerun repair execution, then rerun "
                "exact/proxy bridge only if the repair gate has eligible rows."
            ),
            "",
        ]
    )
    write_text(path, "\n".join(lines))


def append_checkpoint(generated_at: str, counts: dict[str, int]) -> None:
    marker = "\n## Checkpoint 180 - Repair Field Acquisition Requirements\n"
    existing = ""
    if ACTIVE_LEDGER.exists():
        with open(long_path(ACTIVE_LEDGER), "r", encoding="utf-8", errors="replace") as handle:
            existing = handle.read()
    if marker in existing:
        write_text(ACTIVE_LEDGER, existing.split(marker, 1)[0].rstrip() + "\n")
    text = f"""

## Checkpoint 180 - Repair Field Acquisition Requirements

Timestamp UTC: `{generated_at}`

Trigger: continuation after Checkpoint 179. Blocked repair execution rows were expanded into missing-field acquisition requirements and source-candidate lookup queues.

Outputs:

- `{counts['acquisition_requirement_rows']}` acquisition requirement rows from the `188` blocked repair execution rows.
- `{counts['acquisition_batch_rows']}` field/family acquisition batches and `{counts['source_candidate_rows']}` source-candidate rows.
- `{counts['unblock_plan_rows']}` unblock-plan rows, `{counts['bucket_rows']}` bucket rows, and `1` system action row.

Boundary: new outputs use concrete branch-local research boundaries and do not add legacy defensive status-token blocks.

Immediate continuation: run branch-local source lookups for each acquisition requirement, rerun repair execution after fields are supplied, and keep exact/proxy rerun gated until repaired rows become eligible.
"""
    append_text(ACTIVE_LEDGER, text)


def main() -> None:
    generated_at = now_utc()
    exec_result = read_json(EXEC_RESULT)
    execution_rows = read_jsonl(REPAIR_EXECUTION_LEDGER)
    field_rows_in = read_jsonl(FIELD_COVERAGE_LEDGER)
    gate_rows_in = read_jsonl(RERUN_GATE_LEDGER)
    source_rows, manifest_hash = source_manifest_rows(
        [
            EXEC_RESULT,
            REPAIR_EXECUTION_LEDGER,
            FIELD_COVERAGE_LEDGER,
            RERUN_GATE_LEDGER,
            HELPER_MODULE,
            EXEC_HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )

    requirement_rows = [with_common(row, generated_at, manifest_hash) for row in acquisition_requirement_rows(execution_rows)]
    batch_rows = [with_common(row, generated_at, manifest_hash) for row in acquisition_batch_rows(requirement_rows)]
    candidate_rows = [with_common(row, generated_at, manifest_hash) for row in source_candidate_rows(batch_rows)]
    plan_rows = [with_common(row, generated_at, manifest_hash) for row in unblock_plan_rows(requirement_rows, batch_rows)]
    bucket_output_rows = [
        with_common(row, generated_at, manifest_hash) for row in bucket_rows(requirement_rows, batch_rows, candidate_rows)
    ]

    counts = {
        "input_repair_execution_rows": len(execution_rows),
        "input_field_coverage_rows": len(field_rows_in),
        "input_rerun_gate_rows": len(gate_rows_in),
        "acquisition_requirement_rows": len(requirement_rows),
        "acquisition_batch_rows": len(batch_rows),
        "source_candidate_rows": len(candidate_rows),
        "unblock_plan_rows": len(plan_rows),
        "bucket_rows": len(bucket_output_rows),
        "system_action_rows": 1,
        "source_manifest_rows": len(source_rows),
    }
    system_rows = [system_action_row(counts, generated_at, manifest_hash)]
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "research_boundary": research_boundary(),
        "counts": counts,
        "upstream_repair_execution_counts": exec_result.get("counts", {}),
        "blocked_execution_rows_expanded": counts["input_repair_execution_rows"] == exec_result.get("counts", {}).get("blocked_repair_rows"),
        "source_manifest_hash": manifest_hash,
        "system_recommendation": system_rows[0]["recommendation"],
        "ok": True,
    }

    write_json(RESULT_PATH, result)
    write_jsonl(ACQUISITION_REQUIREMENT_LEDGER, requirement_rows)
    write_jsonl(ACQUISITION_BATCH_LEDGER, batch_rows)
    write_jsonl(SOURCE_CANDIDATE_LEDGER, candidate_rows)
    write_jsonl(UNBLOCK_PLAN_LEDGER, plan_rows)
    write_jsonl(BUCKET_LEDGER, bucket_output_rows)
    write_jsonl(SYSTEM_ACTION_LEDGER, system_rows)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_rows)
    write_summary(SUMMARY_PATH, generated_at, counts)

    update_output_manifest(
        [
            (RESULT_PATH, "repaired_proxy_repair_acquisition_result"),
            (ACQUISITION_REQUIREMENT_LEDGER, "repaired_proxy_repair_acquisition_requirement_ledger"),
            (ACQUISITION_BATCH_LEDGER, "repaired_proxy_repair_acquisition_batch_ledger"),
            (SOURCE_CANDIDATE_LEDGER, "repaired_proxy_repair_acquisition_source_candidate_ledger"),
            (UNBLOCK_PLAN_LEDGER, "repaired_proxy_repair_acquisition_unblock_plan_ledger"),
            (BUCKET_LEDGER, "repaired_proxy_repair_acquisition_bucket_ledger"),
            (SYSTEM_ACTION_LEDGER, "repaired_proxy_repair_acquisition_system_action_ledger"),
            (SOURCE_MANIFEST_LEDGER, "repaired_proxy_repair_acquisition_source_manifest_ledger"),
            (SUMMARY_PATH, "repaired_proxy_repair_acquisition_summary"),
            (BUILDER_MODULE, "repaired_proxy_repair_acquisition_builder"),
            (VERIFIER_MODULE, "repaired_proxy_repair_acquisition_verifier"),
        ]
    )
    replace_sprint_event(
        SPRINT_LEDGER,
        {
            "timestamp_utc": generated_at,
            "event": "repaired_proxy_repair_field_acquisition_built",
            "route": PREFIX,
            "counts": counts,
            "research_boundary": research_boundary(),
            "summary": "Expanded blocked repair execution rows into field acquisition requirements.",
        },
    )
    append_checkpoint(generated_at, counts)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
