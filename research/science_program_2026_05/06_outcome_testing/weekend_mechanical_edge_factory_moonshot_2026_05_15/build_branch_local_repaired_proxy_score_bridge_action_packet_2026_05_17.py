#!/usr/bin/env python3
"""Materialize score-bridge action scopes and comparator packets."""

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

from src.research_infra.moonshot_repaired_proxy_score_bridge_action_packet import (
    ACTION_PACKET_SURFACE,
    action_scope_rows,
    bucket_rows,
    comparator_packet_rows,
    repair_routing_rows,
    research_boundary,
    symbol_market_packet_rows,
)


SCORE_BRIDGE_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_SCORE_BRIDGE_REBUILD"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_SCORE_BRIDGE_ACTION_PACKET"

SCORE_BRIDGE_RESULT = ROUTE_DIR / f"{SCORE_BRIDGE_PREFIX}_RESULT_2026-05-17.json"
REBUILT_BRIDGE_LEDGER = ROUTE_DIR / f"{SCORE_BRIDGE_PREFIX}_REBUILT_EXACT_PROXY_BRIDGE_LEDGER_2026-05-17.jsonl"
REPAIR_CONTEXT_BRIDGE_LEDGER = ROUTE_DIR / f"{SCORE_BRIDGE_PREFIX}_REPAIR_CONTEXT_BRIDGE_LEDGER_2026-05-17.jsonl"
MISSING_SCORE_SCOPE_LEDGER = ROUTE_DIR / f"{SCORE_BRIDGE_PREFIX}_MISSING_SCORE_SCOPE_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_score_bridge_action_packet.py"
SCORE_BRIDGE_HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_score_bridge_rebuild.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_repaired_proxy_score_bridge_action_packet_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
ACTION_SCOPE_LEDGER = ROUTE_DIR / f"{PREFIX}_ACTION_SCOPE_LEDGER_2026-05-17.jsonl"
COMPARATOR_PACKET_LEDGER = ROUTE_DIR / f"{PREFIX}_COMPARATOR_PACKET_LEDGER_2026-05-17.jsonl"
REPAIR_ROUTING_LEDGER = ROUTE_DIR / f"{PREFIX}_REPAIR_ROUTING_LEDGER_2026-05-17.jsonl"
SYMBOL_MARKET_PACKET_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_MARKET_PACKET_LEDGER_2026-05-17.jsonl"
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
                "source_manifest_id": f"OHLC-GTOS-REPAIRED-PROXY-SCORE-ACTION-SRC-{index:04d}",
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
    output.setdefault("action_packet_surface", ACTION_PACKET_SURFACE)
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
            "system_action_row_id": "OHLC-GTOS-REPAIRED-PROXY-SCORE-ACTION-SYSTEM-0001",
            "recommendation": (
                "Use comparator packet rows as the next branch-local comparator input, repair identifier/scope "
                "routing rows before another exact/proxy bridge pass, and keep all outputs inside the concrete "
                "branch-local research boundary."
            ),
            "next_branch_local_actions": [
                "assemble_branch_local_comparator_packet_from_ready_rows",
                "repair_identifier_geometry_rows_before_exact_proxy_rerun",
                "repair_unjoined_system_scope_rows_before_score_scope_join",
                "rerun_exact_proxy_bridge_after_repairs",
            ],
            **counts,
        },
        generated_at,
        manifest_hash,
    )


def write_summary(path: Path, generated_at: str, counts: dict[str, int]) -> None:
    lines = [
        "# Repaired Proxy Score Bridge Action Packet",
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
                "Assemble comparator packet rows, repair identifier/geometry and unjoined system-scope rows, "
                "then rerun the exact/proxy bridge after those repairs."
            ),
            "",
        ]
    )
    write_text(path, "\n".join(lines))


def append_checkpoint(generated_at: str, counts: dict[str, int]) -> None:
    marker = "\n## Checkpoint 177 - Score Bridge Action Packet Materialized\n"
    existing = ""
    if ACTIVE_LEDGER.exists():
        with open(long_path(ACTIVE_LEDGER), "r", encoding="utf-8", errors="replace") as handle:
            existing = handle.read()
    if marker in existing:
        write_text(ACTIVE_LEDGER, existing.split(marker, 1)[0].rstrip() + "\n")
    text = f"""

## Checkpoint 177 - Score Bridge Action Packet Materialized

Timestamp UTC: `{generated_at}`

Trigger: continuation after Checkpoint 176. Score-bridge rows were aggregated into action scopes, comparator-packet rows, and explicit repair routing rows.

Outputs:

- `{counts['action_scope_rows']}` action-scope rows preserving the full `{counts['input_rebuilt_bridge_rows']}` rebuilt bridge denominator.
- `{counts['comparator_packet_rows']}` branch-local comparator packet rows from score-joined replay scopes.
- `{counts['repair_routing_rows']}` repair routing rows, covering `{counts['input_repair_context_bridge_rows']}` repair-context rows and `{counts['input_missing_score_scope_rows']}` unjoined score-scope rows.
- `{counts['symbol_market_packet_rows']}` symbol/market packet rows, `{counts['bucket_rows']}` bucket rows, and `1` system action row.

Boundary: new outputs use concrete branch-local research boundaries and do not add legacy defensive status-token blocks.

Immediate continuation: assemble the branch-local comparator packet, repair identifier/geometry and unjoined system-scope rows, then rerun the exact/proxy bridge after those repairs.
"""
    append_text(ACTIVE_LEDGER, text)


def main() -> None:
    generated_at = now_utc()
    score_bridge_result = read_json(SCORE_BRIDGE_RESULT)
    bridge_rows = read_jsonl(REBUILT_BRIDGE_LEDGER)
    repair_context_rows = read_jsonl(REPAIR_CONTEXT_BRIDGE_LEDGER)
    missing_score_rows = read_jsonl(MISSING_SCORE_SCOPE_LEDGER)
    source_rows, manifest_hash = source_manifest_rows(
        [
            SCORE_BRIDGE_RESULT,
            REBUILT_BRIDGE_LEDGER,
            REPAIR_CONTEXT_BRIDGE_LEDGER,
            MISSING_SCORE_SCOPE_LEDGER,
            HELPER_MODULE,
            SCORE_BRIDGE_HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )

    action_rows = [with_common(row, generated_at, manifest_hash) for row in action_scope_rows(bridge_rows)]
    comparator_rows = [with_common(row, generated_at, manifest_hash) for row in comparator_packet_rows(action_rows)]
    repair_rows = [with_common(row, generated_at, manifest_hash) for row in repair_routing_rows(bridge_rows)]
    symbol_market_rows = [
        with_common(row, generated_at, manifest_hash) for row in symbol_market_packet_rows(action_rows)
    ]
    bucket_output_rows = [
        with_common(row, generated_at, manifest_hash)
        for row in bucket_rows(action_rows, comparator_rows, repair_rows)
    ]

    counts = {
        "input_rebuilt_bridge_rows": len(bridge_rows),
        "input_repair_context_bridge_rows": len(repair_context_rows),
        "input_missing_score_scope_rows": len(missing_score_rows),
        "action_scope_rows": len(action_rows),
        "comparator_packet_rows": len(comparator_rows),
        "repair_routing_rows": len(repair_rows),
        "symbol_market_packet_rows": len(symbol_market_rows),
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
        "upstream_score_bridge_counts": score_bridge_result.get("counts", {}),
        "bridge_denominator_preserved": sum(int(row.get("bridge_rows") or 0) for row in action_rows)
        == len(bridge_rows),
        "repair_routing_denominator_preserved": len(repair_rows)
        == len(repair_context_rows) + len(missing_score_rows),
        "source_manifest_hash": manifest_hash,
        "system_recommendation": system_rows[0]["recommendation"],
        "ok": True,
    }

    write_json(RESULT_PATH, result)
    write_jsonl(ACTION_SCOPE_LEDGER, action_rows)
    write_jsonl(COMPARATOR_PACKET_LEDGER, comparator_rows)
    write_jsonl(REPAIR_ROUTING_LEDGER, repair_rows)
    write_jsonl(SYMBOL_MARKET_PACKET_LEDGER, symbol_market_rows)
    write_jsonl(BUCKET_LEDGER, bucket_output_rows)
    write_jsonl(SYSTEM_ACTION_LEDGER, system_rows)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_rows)
    write_summary(SUMMARY_PATH, generated_at, counts)

    update_output_manifest(
        [
            (RESULT_PATH, "repaired_proxy_score_bridge_action_packet_result"),
            (ACTION_SCOPE_LEDGER, "repaired_proxy_score_bridge_action_scope_ledger"),
            (COMPARATOR_PACKET_LEDGER, "repaired_proxy_score_bridge_comparator_packet_ledger"),
            (REPAIR_ROUTING_LEDGER, "repaired_proxy_score_bridge_repair_routing_ledger"),
            (SYMBOL_MARKET_PACKET_LEDGER, "repaired_proxy_score_bridge_symbol_market_packet_ledger"),
            (BUCKET_LEDGER, "repaired_proxy_score_bridge_action_bucket_ledger"),
            (SYSTEM_ACTION_LEDGER, "repaired_proxy_score_bridge_action_system_ledger"),
            (SOURCE_MANIFEST_LEDGER, "repaired_proxy_score_bridge_action_source_manifest_ledger"),
            (SUMMARY_PATH, "repaired_proxy_score_bridge_action_summary"),
            (BUILDER_MODULE, "repaired_proxy_score_bridge_action_builder"),
            (VERIFIER_MODULE, "repaired_proxy_score_bridge_action_verifier"),
        ]
    )
    replace_sprint_event(
        SPRINT_LEDGER,
        {
            "timestamp_utc": generated_at,
            "event": "repaired_proxy_score_bridge_action_packet_built",
            "route": PREFIX,
            "counts": counts,
            "research_boundary": research_boundary(),
            "summary": "Aggregated score-bridge rows into action scopes, comparator packets, and repair routes.",
        },
    )
    append_checkpoint(generated_at, counts)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
