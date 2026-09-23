#!/usr/bin/env python3
"""Execute repaired-proxy repair work orders against available row fields."""

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

from src.research_infra.moonshot_repaired_proxy_repair_execution import (
    REPAIR_EXECUTION_SURFACE,
    bucket_rows,
    execution_batch_rows,
    field_coverage_rows,
    repair_execution_rows,
    rerun_gate_rows,
    research_boundary,
)


WORK_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_COMPARATOR_INPUT_REPAIR_WORK"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_REPAIR_WORK_EXECUTION"

WORK_RESULT = ROUTE_DIR / f"{WORK_PREFIX}_RESULT_2026-05-17.json"
REPAIR_WORK_ORDER_LEDGER = ROUTE_DIR / f"{WORK_PREFIX}_REPAIR_WORK_ORDER_LEDGER_2026-05-17.jsonl"
REPAIR_BATCH_LEDGER = ROUTE_DIR / f"{WORK_PREFIX}_REPAIR_BATCH_LEDGER_2026-05-17.jsonl"
RERUN_PLAN_LEDGER = ROUTE_DIR / f"{WORK_PREFIX}_RERUN_PLAN_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_repair_execution.py"
WORK_HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_comparator_input_repair_work.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_repaired_proxy_repair_execution_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
REPAIR_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_REPAIR_EXECUTION_LEDGER_2026-05-17.jsonl"
FIELD_COVERAGE_LEDGER = ROUTE_DIR / f"{PREFIX}_FIELD_COVERAGE_LEDGER_2026-05-17.jsonl"
EXECUTION_BATCH_LEDGER = ROUTE_DIR / f"{PREFIX}_EXECUTION_BATCH_LEDGER_2026-05-17.jsonl"
RERUN_GATE_LEDGER = ROUTE_DIR / f"{PREFIX}_RERUN_GATE_LEDGER_2026-05-17.jsonl"
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
                "source_manifest_id": f"OHLC-GTOS-REPAIRED-PROXY-REPAIR-EXEC-SRC-{index:04d}",
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
    output.setdefault("repair_execution_surface", REPAIR_EXECUTION_SURFACE)
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
            "system_action_row_id": "OHLC-GTOS-REPAIRED-PROXY-REPAIR-EXEC-SYSTEM-0001",
            "recommendation": (
                "Do not rerun exact/proxy bridge as repaired until missing identifier and scope fields are supplied; "
                "use execution rows as the row-level acquisition checklist."
            ),
            "next_branch_local_actions": [
                "acquire_or_regenerate_direct_identifier_fields_for_identifier_linkage_repairs",
                "acquire_or_regenerate_scope_identity_fields_for_unjoined_system_scope_repairs",
                "rerun_repair_execution_after_fields_are_available",
                "rerun_exact_proxy_bridge_only_after_repair_gate_has_eligible_rows",
            ],
            **counts,
        },
        generated_at,
        manifest_hash,
    )


def write_summary(path: Path, generated_at: str, counts: dict[str, int]) -> None:
    lines = [
        "# Repaired Proxy Repair Work Execution",
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
                "Acquire missing identifier and scope fields, rerun repair execution, and only then rerun exact/proxy "
                "bridge with eligible repaired rows."
            ),
            "",
        ]
    )
    write_text(path, "\n".join(lines))


def append_checkpoint(generated_at: str, counts: dict[str, int]) -> None:
    marker = "\n## Checkpoint 179 - Repair Work Execution Attempt\n"
    existing = ""
    if ACTIVE_LEDGER.exists():
        with open(long_path(ACTIVE_LEDGER), "r", encoding="utf-8", errors="replace") as handle:
            existing = handle.read()
    if marker in existing:
        write_text(ACTIVE_LEDGER, existing.split(marker, 1)[0].rstrip() + "\n")
    text = f"""

## Checkpoint 179 - Repair Work Execution Attempt

Timestamp UTC: `{generated_at}`

Trigger: continuation after Checkpoint 178. Repair work orders were executed against available branch-local row fields before deciding whether an exact/proxy bridge rerun is eligible.

Outputs:

- `{counts['repair_execution_rows']}` repair execution rows from the `188` repair work orders.
- `{counts['field_coverage_rows']}` required-field coverage rows proving which fields are present or missing by repair family.
- `{counts['execution_batch_rows']}` execution batch rows and `{counts['rerun_gate_rows']}` rerun gate row.
- `{counts['bucket_rows']}` bucket rows and `1` system action row.

Boundary: new outputs use concrete branch-local research boundaries and do not add legacy defensive status-token blocks.

Immediate continuation: acquire or regenerate missing identifier/scope fields, rerun repair execution, and rerun exact/proxy bridge only after the rerun gate has eligible repaired rows.
"""
    append_text(ACTIVE_LEDGER, text)


def main() -> None:
    generated_at = now_utc()
    work_result = read_json(WORK_RESULT)
    work_rows = read_jsonl(REPAIR_WORK_ORDER_LEDGER)
    batch_input_rows = read_jsonl(REPAIR_BATCH_LEDGER)
    plan_input_rows = read_jsonl(RERUN_PLAN_LEDGER)
    source_rows, manifest_hash = source_manifest_rows(
        [
            WORK_RESULT,
            REPAIR_WORK_ORDER_LEDGER,
            REPAIR_BATCH_LEDGER,
            RERUN_PLAN_LEDGER,
            HELPER_MODULE,
            WORK_HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )

    execution_rows = [with_common(row, generated_at, manifest_hash) for row in repair_execution_rows(work_rows)]
    field_rows = [with_common(row, generated_at, manifest_hash) for row in field_coverage_rows(execution_rows)]
    batch_rows = [with_common(row, generated_at, manifest_hash) for row in execution_batch_rows(execution_rows)]
    gate_rows = [with_common(row, generated_at, manifest_hash) for row in rerun_gate_rows(execution_rows)]
    bucket_output_rows = [
        with_common(row, generated_at, manifest_hash) for row in bucket_rows(execution_rows, field_rows, gate_rows)
    ]

    counts = {
        "input_repair_work_order_rows": len(work_rows),
        "input_repair_batch_rows": len(batch_input_rows),
        "input_rerun_plan_rows": len(plan_input_rows),
        "repair_execution_rows": len(execution_rows),
        "field_coverage_rows": len(field_rows),
        "execution_batch_rows": len(batch_rows),
        "rerun_gate_rows": len(gate_rows),
        "rerun_eligible_rows": sum(1 for row in execution_rows if row.get("exact_proxy_rerun_eligible") is True),
        "blocked_repair_rows": sum(1 for row in execution_rows if row.get("exact_proxy_rerun_eligible") is not True),
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
        "upstream_work_counts": work_result.get("counts", {}),
        "repair_work_order_denominator_preserved": len(execution_rows) == len(work_rows),
        "exact_proxy_rerun_gate_status": gate_rows[0].get("rerun_gate_status"),
        "source_manifest_hash": manifest_hash,
        "system_recommendation": system_rows[0]["recommendation"],
        "ok": True,
    }

    write_json(RESULT_PATH, result)
    write_jsonl(REPAIR_EXECUTION_LEDGER, execution_rows)
    write_jsonl(FIELD_COVERAGE_LEDGER, field_rows)
    write_jsonl(EXECUTION_BATCH_LEDGER, batch_rows)
    write_jsonl(RERUN_GATE_LEDGER, gate_rows)
    write_jsonl(BUCKET_LEDGER, bucket_output_rows)
    write_jsonl(SYSTEM_ACTION_LEDGER, system_rows)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_rows)
    write_summary(SUMMARY_PATH, generated_at, counts)

    update_output_manifest(
        [
            (RESULT_PATH, "repaired_proxy_repair_execution_result"),
            (REPAIR_EXECUTION_LEDGER, "repaired_proxy_repair_execution_ledger"),
            (FIELD_COVERAGE_LEDGER, "repaired_proxy_repair_field_coverage_ledger"),
            (EXECUTION_BATCH_LEDGER, "repaired_proxy_repair_execution_batch_ledger"),
            (RERUN_GATE_LEDGER, "repaired_proxy_repair_rerun_gate_ledger"),
            (BUCKET_LEDGER, "repaired_proxy_repair_execution_bucket_ledger"),
            (SYSTEM_ACTION_LEDGER, "repaired_proxy_repair_execution_system_action_ledger"),
            (SOURCE_MANIFEST_LEDGER, "repaired_proxy_repair_execution_source_manifest_ledger"),
            (SUMMARY_PATH, "repaired_proxy_repair_execution_summary"),
            (BUILDER_MODULE, "repaired_proxy_repair_execution_builder"),
            (VERIFIER_MODULE, "repaired_proxy_repair_execution_verifier"),
        ]
    )
    replace_sprint_event(
        SPRINT_LEDGER,
        {
            "timestamp_utc": generated_at,
            "event": "repaired_proxy_repair_work_execution_built",
            "route": PREFIX,
            "counts": counts,
            "research_boundary": research_boundary(),
            "summary": "Executed repair work orders against available branch-local row fields.",
        },
    )
    append_checkpoint(generated_at, counts)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
