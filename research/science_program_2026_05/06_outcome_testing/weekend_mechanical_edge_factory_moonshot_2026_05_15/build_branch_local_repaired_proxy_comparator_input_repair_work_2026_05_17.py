#!/usr/bin/env python3
"""Build branch-local comparator input rows and repair work orders."""

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

from src.research_infra.moonshot_repaired_proxy_comparator_input_repair_work import (
    COMPARATOR_INPUT_SURFACE,
    bucket_rows,
    comparator_input_rows,
    comparator_symbol_queue_rows,
    repair_batch_rows,
    repair_work_order_rows,
    rerun_plan_rows,
    research_boundary,
)


ACTION_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_SCORE_BRIDGE_ACTION_PACKET"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_COMPARATOR_INPUT_REPAIR_WORK"

ACTION_RESULT = ROUTE_DIR / f"{ACTION_PREFIX}_RESULT_2026-05-17.json"
COMPARATOR_PACKET_LEDGER = ROUTE_DIR / f"{ACTION_PREFIX}_COMPARATOR_PACKET_LEDGER_2026-05-17.jsonl"
REPAIR_ROUTING_LEDGER = ROUTE_DIR / f"{ACTION_PREFIX}_REPAIR_ROUTING_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_comparator_input_repair_work.py"
ACTION_HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_score_bridge_action_packet.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_repaired_proxy_comparator_input_repair_work_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
COMPARATOR_INPUT_LEDGER = ROUTE_DIR / f"{PREFIX}_COMPARATOR_INPUT_LEDGER_2026-05-17.jsonl"
COMPARATOR_SYMBOL_QUEUE_LEDGER = ROUTE_DIR / f"{PREFIX}_COMPARATOR_SYMBOL_QUEUE_LEDGER_2026-05-17.jsonl"
REPAIR_WORK_ORDER_LEDGER = ROUTE_DIR / f"{PREFIX}_REPAIR_WORK_ORDER_LEDGER_2026-05-17.jsonl"
REPAIR_BATCH_LEDGER = ROUTE_DIR / f"{PREFIX}_REPAIR_BATCH_LEDGER_2026-05-17.jsonl"
RERUN_PLAN_LEDGER = ROUTE_DIR / f"{PREFIX}_RERUN_PLAN_LEDGER_2026-05-17.jsonl"
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
                "source_manifest_id": f"OHLC-GTOS-REPAIRED-PROXY-COMPARATOR-INPUT-SRC-{index:04d}",
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
    output.setdefault("comparator_input_surface", COMPARATOR_INPUT_SURFACE)
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
            "system_action_row_id": "OHLC-GTOS-REPAIRED-PROXY-COMPARATOR-INPUT-SYSTEM-0001",
            "recommendation": (
                "Use the comparator input ledger as the branch-local comparator assembly source, complete repair "
                "work orders before exact/proxy rerun, and preserve the rerun plan as the next execution checklist."
            ),
            "next_branch_local_actions": [
                "execute_repair_work_orders_against_available_branch_local_sources",
                "rerun_exact_proxy_bridge_after_repair_execution",
                "rebuild_score_bridge_and_action_packet_after_exact_proxy_rerun",
            ],
            **counts,
        },
        generated_at,
        manifest_hash,
    )


def write_summary(path: Path, generated_at: str, counts: dict[str, int]) -> None:
    lines = [
        "# Repaired Proxy Comparator Input And Repair Work",
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
                "Execute repair work orders against available branch-local sources, rerun exact/proxy bridge, "
                "then rebuild score bridge and action packet outputs."
            ),
            "",
        ]
    )
    write_text(path, "\n".join(lines))


def append_checkpoint(generated_at: str, counts: dict[str, int]) -> None:
    marker = "\n## Checkpoint 178 - Comparator Input And Repair Work Orders\n"
    existing = ""
    if ACTIVE_LEDGER.exists():
        with open(long_path(ACTIVE_LEDGER), "r", encoding="utf-8", errors="replace") as handle:
            existing = handle.read()
    if marker in existing:
        write_text(ACTIVE_LEDGER, existing.split(marker, 1)[0].rstrip() + "\n")
    text = f"""

## Checkpoint 178 - Comparator Input And Repair Work Orders

Timestamp UTC: `{generated_at}`

Trigger: continuation after Checkpoint 177. Comparator packet rows were normalized into branch-local comparator input rows, and repair-routing rows were converted into work orders.

Outputs:

- `{counts['comparator_input_rows']}` comparator input rows from the `254` action-packet comparator rows.
- `{counts['comparator_symbol_queue_rows']}` symbol queue rows for branch-local comparator assembly.
- `{counts['repair_work_order_rows']}` repair work orders from the `188` repair-routing rows.
- `{counts['repair_batch_rows']}` repair batch rows, `{counts['rerun_plan_rows']}` rerun-plan rows, `{counts['bucket_rows']}` bucket rows, and `1` system action row.

Boundary: new outputs use concrete branch-local research boundaries and do not add legacy defensive status-token blocks.

Immediate continuation: execute repair work orders against available branch-local sources, rerun exact/proxy bridge after repair execution, then rebuild score bridge and action packet outputs.
"""
    append_text(ACTIVE_LEDGER, text)


def main() -> None:
    generated_at = now_utc()
    action_result = read_json(ACTION_RESULT)
    packet_rows = read_jsonl(COMPARATOR_PACKET_LEDGER)
    repair_rows = read_jsonl(REPAIR_ROUTING_LEDGER)
    source_rows, manifest_hash = source_manifest_rows(
        [
            ACTION_RESULT,
            COMPARATOR_PACKET_LEDGER,
            REPAIR_ROUTING_LEDGER,
            HELPER_MODULE,
            ACTION_HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )

    input_rows = [with_common(row, generated_at, manifest_hash) for row in comparator_input_rows(packet_rows)]
    symbol_rows = [with_common(row, generated_at, manifest_hash) for row in comparator_symbol_queue_rows(input_rows)]
    work_rows = [with_common(row, generated_at, manifest_hash) for row in repair_work_order_rows(repair_rows)]
    batch_rows = [with_common(row, generated_at, manifest_hash) for row in repair_batch_rows(work_rows)]
    plan_rows = [with_common(row, generated_at, manifest_hash) for row in rerun_plan_rows(input_rows, work_rows)]
    bucket_output_rows = [
        with_common(row, generated_at, manifest_hash) for row in bucket_rows(input_rows, work_rows, batch_rows)
    ]

    counts = {
        "input_comparator_packet_rows": len(packet_rows),
        "input_repair_routing_rows": len(repair_rows),
        "comparator_input_rows": len(input_rows),
        "comparator_symbol_queue_rows": len(symbol_rows),
        "repair_work_order_rows": len(work_rows),
        "repair_batch_rows": len(batch_rows),
        "rerun_plan_rows": len(plan_rows),
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
        "upstream_action_packet_counts": action_result.get("counts", {}),
        "comparator_packet_denominator_preserved": len(input_rows) == len(packet_rows),
        "repair_routing_denominator_preserved": len(work_rows) == len(repair_rows),
        "source_manifest_hash": manifest_hash,
        "system_recommendation": system_rows[0]["recommendation"],
        "ok": True,
    }

    write_json(RESULT_PATH, result)
    write_jsonl(COMPARATOR_INPUT_LEDGER, input_rows)
    write_jsonl(COMPARATOR_SYMBOL_QUEUE_LEDGER, symbol_rows)
    write_jsonl(REPAIR_WORK_ORDER_LEDGER, work_rows)
    write_jsonl(REPAIR_BATCH_LEDGER, batch_rows)
    write_jsonl(RERUN_PLAN_LEDGER, plan_rows)
    write_jsonl(BUCKET_LEDGER, bucket_output_rows)
    write_jsonl(SYSTEM_ACTION_LEDGER, system_rows)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_rows)
    write_summary(SUMMARY_PATH, generated_at, counts)

    update_output_manifest(
        [
            (RESULT_PATH, "repaired_proxy_comparator_input_repair_result"),
            (COMPARATOR_INPUT_LEDGER, "repaired_proxy_comparator_input_ledger"),
            (COMPARATOR_SYMBOL_QUEUE_LEDGER, "repaired_proxy_comparator_symbol_queue_ledger"),
            (REPAIR_WORK_ORDER_LEDGER, "repaired_proxy_repair_work_order_ledger"),
            (REPAIR_BATCH_LEDGER, "repaired_proxy_repair_batch_ledger"),
            (RERUN_PLAN_LEDGER, "repaired_proxy_comparator_rerun_plan_ledger"),
            (BUCKET_LEDGER, "repaired_proxy_comparator_input_bucket_ledger"),
            (SYSTEM_ACTION_LEDGER, "repaired_proxy_comparator_input_system_action_ledger"),
            (SOURCE_MANIFEST_LEDGER, "repaired_proxy_comparator_input_source_manifest_ledger"),
            (SUMMARY_PATH, "repaired_proxy_comparator_input_repair_summary"),
            (BUILDER_MODULE, "repaired_proxy_comparator_input_repair_builder"),
            (VERIFIER_MODULE, "repaired_proxy_comparator_input_repair_verifier"),
        ]
    )
    replace_sprint_event(
        SPRINT_LEDGER,
        {
            "timestamp_utc": generated_at,
            "event": "repaired_proxy_comparator_input_repair_work_built",
            "route": PREFIX,
            "counts": counts,
            "research_boundary": research_boundary(),
            "summary": "Built branch-local comparator input rows and repair work orders.",
        },
    )
    append_checkpoint(generated_at, counts)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
