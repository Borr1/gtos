#!/usr/bin/env python3
"""Register and route repaired-proxy execution specs branch-locally."""

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

from src.research_infra.moonshot_repaired_proxy_execution_registry import (
    EXECUTION_REGISTRY_SURFACE,
    avoid_comparator_execution_row,
    build_execution_registry,
    bucket_rows,
    execution_event_application_row,
    market_replay_population_row,
    registry_symbol_counts,
    repair_execution_row,
    research_boundary,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_EXECUTION_SPECS"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_EXECUTION_REGISTRY"

DEFAULT_SPEC_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_DEFAULT_OFF_SCORER_SPEC_LEDGER_2026-05-17.jsonl"
AVOID_SPEC_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_AVOID_COMPARATOR_SPEC_LEDGER_2026-05-17.jsonl"
REPAIR_TASK_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_REPAIR_TASK_LEDGER_2026-05-17.jsonl"
EXACT_PROXY_BRIDGE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_EXACT_PROXY_BRIDGE_LEDGER_2026-05-17.jsonl"
MARKET_POPULATION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_MARKET_EXPANSION_POPULATION_LEDGER_2026-05-17.jsonl"
INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"

HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_execution_registry.py"
SPEC_HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_execution_specs.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_repaired_proxy_execution_registry_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
DEFAULT_SCOPE_REGISTRY_LEDGER = ROUTE_DIR / f"{PREFIX}_DEFAULT_SCOPE_REGISTRY_LEDGER_2026-05-17.jsonl"
AVOID_SCOPE_REGISTRY_LEDGER = ROUTE_DIR / f"{PREFIX}_AVOID_SCOPE_REGISTRY_LEDGER_2026-05-17.jsonl"
EVENT_REGISTRY_APPLICATION_LEDGER = ROUTE_DIR / f"{PREFIX}_EVENT_REGISTRY_APPLICATION_LEDGER_2026-05-17.jsonl"
AVOID_COMPARATOR_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_AVOID_COMPARATOR_EXECUTION_LEDGER_2026-05-17.jsonl"
REPAIR_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_REPAIR_EXECUTION_LEDGER_2026-05-17.jsonl"
MARKET_REPLAY_NUMERIC_LEDGER = ROUTE_DIR / f"{PREFIX}_MARKET_REPLAY_NUMERIC_POPULATION_LEDGER_2026-05-17.jsonl"
SYMBOL_ACTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_ACTION_LEDGER_2026-05-17.jsonl"
SYSTEM_ACTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_ACTION_LEDGER_2026-05-17.jsonl"
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


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    with open(long_path(path), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def append_text(path: Path, text: str) -> None:
    with open(long_path(path), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


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
                "source_manifest_id": f"OHLC-GTOS-REPAIRED-PROXY-EXEC-REG-SRC-{index:04d}",
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
    output.setdefault("execution_registry_surface", EXECUTION_REGISTRY_SURFACE)
    output.setdefault("research_boundary", research_boundary())
    return output


def row_by_key(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    return {str(row.get(key) or ""): row for row in rows}


def symbol_action_rows(
    symbol_counts: dict[str, dict[str, int]],
    market_rows: list[dict[str, Any]],
    generated_at: str,
    manifest_hash: str,
) -> list[dict[str, Any]]:
    market_counter = Counter(str(row.get("symbol") or "") for row in market_rows)
    output: list[dict[str, Any]] = []
    for index, symbol in enumerate(sorted(symbol_counts), 1):
        counts = symbol_counts[symbol]
        output.append(
            with_common(
                {
                    "symbol_action_row_id": f"OHLC-GTOS-REPAIRED-PROXY-EXEC-REG-SYMBOL-{index:04d}",
                    "symbol": symbol,
                    "registered_default_event_rows": counts.get("default_event_rows", 0),
                    "registered_avoid_event_rows": counts.get("avoid_event_rows", 0),
                    "repair_event_rows": counts.get("repair_event_rows", 0),
                    "registered_default_scope_rows": counts.get("default_scope_rows", 0),
                    "registered_avoid_scope_rows": counts.get("avoid_scope_rows", 0),
                    "repair_scope_rows": counts.get("repair_scope_rows", 0),
                    "market_population_rows_available": int(market_counter[symbol]),
                    "symbol_action": (
                        "EXECUTE_REGISTERED_SCOPES_WITH_MARKET_REPLAY_POPULATION"
                        if market_counter[symbol]
                        else "KEEP_REGISTERED_SCOPE_FOR_SOURCE_ACQUISITION_OR_TRANSFER"
                    ),
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def system_action_row(counts: dict[str, int], generated_at: str, manifest_hash: str) -> dict[str, Any]:
    return with_common(
        {
            "system_action_row_id": "OHLC-GTOS-REPAIRED-PROXY-EXEC-REG-SYSTEM-0001",
            "recommendation": (
                "Use the registered default-off scorer scopes and avoid/redesign comparator scopes as branch-local "
                "callable research registries, execute repair rows until direct identifiers or broker geometry exist, "
                "and feed market replay population rows into the next numeric replay pass."
            ),
            "next_branch_local_actions": [
                "execute_default_off_registry_against_replay_population",
                "execute_avoid_comparator_registry_against_replay_population",
                "batch_repair_direct_identifier_and_broker_geometry_gaps",
                "rerun_exact_proxy_bridge_after_repair_batches",
            ],
            **counts,
        },
        generated_at,
        manifest_hash,
    )


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
        "# Repaired Proxy Execution Registry",
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
                "Execute the registered scope rows against market replay populations, repair direct identifier and broker "
                "geometry gaps, and rerun the exact/proxy bridge after each repair batch."
            ),
            "",
        ]
    )
    write_text(path, "\n".join(lines))


def append_checkpoint(generated_at: str, counts: dict[str, int]) -> None:
    text = f"""

## Checkpoint 172 - Repaired Proxy Execution Specs Registered And Routed

Timestamp UTC: `{generated_at}`

Trigger: continuation after Checkpoint 171. The generated execution specs were converted into callable branch-local registry rows and routed back over the full exact/proxy bridge denominator.

Outputs:

- `{counts['default_scope_registry_rows']}` default-off scorer scope registry rows from the `12,303` event specs.
- `{counts['avoid_scope_registry_rows']}` avoid/redesign comparator scope registry rows from the `5,443` comparator specs.
- `{counts['event_registry_application_rows']}` event registry application rows, preserving the full `17,916` exact/proxy bridge denominator.
- `{counts['avoid_comparator_execution_rows']}` avoid comparator execution rows and `{counts['repair_execution_rows']}` repair execution rows.
- `{counts['market_replay_numeric_population_rows']}` market replay/numeric population rows and `{counts['symbol_action_rows']}` symbol action rows for the next replay pass.

Boundary: new outputs use concrete branch-local research boundaries and do not add legacy defensive status-token blocks.

Immediate continuation: execute the registered default-off and avoid/redesign registries against replay populations, batch-repair direct identifier and broker-geometry gaps, and rerun the exact/proxy bridge after each repair batch.
"""
    append_text(ACTIVE_LEDGER, text)


def main() -> None:
    generated_at = now_utc()
    input_result = read_json(INPUT_RESULT)
    default_specs = read_jsonl(DEFAULT_SPEC_LEDGER)
    avoid_specs = read_jsonl(AVOID_SPEC_LEDGER)
    repair_tasks = read_jsonl(REPAIR_TASK_LEDGER)
    bridge_rows = read_jsonl(EXACT_PROXY_BRIDGE_LEDGER)
    market_rows = read_jsonl(MARKET_POPULATION_LEDGER)

    source_rows, manifest_hash = source_manifest_rows(
        [
            INPUT_RESULT,
            DEFAULT_SPEC_LEDGER,
            AVOID_SPEC_LEDGER,
            REPAIR_TASK_LEDGER,
            EXACT_PROXY_BRIDGE_LEDGER,
            MARKET_POPULATION_LEDGER,
            HELPER_MODULE,
            SPEC_HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )

    registry = build_execution_registry(default_specs, avoid_specs, repair_tasks)
    default_scope_rows = [
        with_common(row, generated_at, manifest_hash) for row in registry["default_scope_rows"]
    ]
    avoid_scope_rows = [with_common(row, generated_at, manifest_hash) for row in registry["avoid_scope_rows"]]

    bridge_by_event = row_by_key(bridge_rows, "input_repaired_proxy_event_application_row_id")
    event_application_rows = [
        with_common(execution_event_application_row(row, registry, index), generated_at, manifest_hash)
        for index, row in enumerate(bridge_rows, 1)
    ]
    avoid_comparator_rows = [
        with_common(
            avoid_comparator_execution_row(
                row,
                registry["default_scopes_by_key"].get(str(row.get("aggregate_scope_key") or "")),
                bridge_by_event.get(str(row.get("input_repaired_proxy_event_application_row_id") or "")),
                index,
            ),
            generated_at,
            manifest_hash,
        )
        for index, row in enumerate(avoid_specs, 1)
    ]
    repair_execution_rows = [
        with_common(repair_execution_row(row, index), generated_at, manifest_hash)
        for index, row in enumerate(repair_tasks, 1)
    ]
    symbol_counts = registry_symbol_counts(default_specs, avoid_specs, repair_tasks)
    market_replay_rows = [
        with_common(market_replay_population_row(row, symbol_counts, index), generated_at, manifest_hash)
        for index, row in enumerate(market_rows, 1)
    ]
    symbol_rows = symbol_action_rows(symbol_counts, market_replay_rows, generated_at, manifest_hash)
    bucket_output_rows = [
        with_common(row, generated_at, manifest_hash)
        for row in bucket_rows(
            {
                "event_applications": event_application_rows,
                "avoid_comparators": avoid_comparator_rows,
                "repair_executions": repair_execution_rows,
                "market_populations": market_replay_rows,
            }
        )
    ]

    counts = {
        "input_default_spec_rows": len(default_specs),
        "input_avoid_spec_rows": len(avoid_specs),
        "input_repair_task_rows": len(repair_tasks),
        "input_exact_proxy_bridge_rows": len(bridge_rows),
        "input_market_population_rows": len(market_rows),
        "default_scope_registry_rows": len(default_scope_rows),
        "avoid_scope_registry_rows": len(avoid_scope_rows),
        "event_registry_application_rows": len(event_application_rows),
        "avoid_comparator_execution_rows": len(avoid_comparator_rows),
        "repair_execution_rows": len(repair_execution_rows),
        "market_replay_numeric_population_rows": len(market_replay_rows),
        "symbol_action_rows": len(symbol_rows),
        "system_action_rows": 1,
        "bucket_rows": len(bucket_output_rows),
        "source_manifest_rows": len(source_rows),
    }

    system_rows = [system_action_row(counts, generated_at, manifest_hash)]
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "research_boundary": research_boundary(),
        "counts": counts,
        "upstream_counts": input_result.get("counts", {}),
        "input_denominator_preserved": counts["event_registry_application_rows"]
        == input_result.get("counts", {}).get("exact_proxy_bridge_rows"),
        "registered_scope_counts": {
            "default_off": counts["default_scope_registry_rows"],
            "avoid_redesign": counts["avoid_scope_registry_rows"],
        },
        "system_recommendation": system_rows[0]["recommendation"],
        "source_manifest_hash": manifest_hash,
        "ok": True,
    }

    write_json(RESULT_PATH, result)
    write_jsonl(DEFAULT_SCOPE_REGISTRY_LEDGER, default_scope_rows)
    write_jsonl(AVOID_SCOPE_REGISTRY_LEDGER, avoid_scope_rows)
    write_jsonl(EVENT_REGISTRY_APPLICATION_LEDGER, event_application_rows)
    write_jsonl(AVOID_COMPARATOR_EXECUTION_LEDGER, avoid_comparator_rows)
    write_jsonl(REPAIR_EXECUTION_LEDGER, repair_execution_rows)
    write_jsonl(MARKET_REPLAY_NUMERIC_LEDGER, market_replay_rows)
    write_jsonl(SYMBOL_ACTION_LEDGER, symbol_rows)
    write_jsonl(SYSTEM_ACTION_LEDGER, system_rows)
    write_jsonl(BUCKET_LEDGER, bucket_output_rows)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_rows)
    write_summary(SUMMARY_PATH, generated_at, counts)

    output_entries = [
        (RESULT_PATH, "repaired_proxy_execution_registry_result"),
        (DEFAULT_SCOPE_REGISTRY_LEDGER, "repaired_proxy_execution_registry_default_scope_ledger"),
        (AVOID_SCOPE_REGISTRY_LEDGER, "repaired_proxy_execution_registry_avoid_scope_ledger"),
        (EVENT_REGISTRY_APPLICATION_LEDGER, "repaired_proxy_execution_registry_application_ledger"),
        (AVOID_COMPARATOR_EXECUTION_LEDGER, "repaired_proxy_execution_registry_avoid_comparator_ledger"),
        (REPAIR_EXECUTION_LEDGER, "repaired_proxy_execution_registry_repair_execution_ledger"),
        (MARKET_REPLAY_NUMERIC_LEDGER, "repaired_proxy_execution_registry_market_population_ledger"),
        (SYMBOL_ACTION_LEDGER, "repaired_proxy_execution_registry_symbol_action_ledger"),
        (SYSTEM_ACTION_LEDGER, "repaired_proxy_execution_registry_system_action_ledger"),
        (BUCKET_LEDGER, "repaired_proxy_execution_registry_bucket_ledger"),
        (SOURCE_MANIFEST_LEDGER, "repaired_proxy_execution_registry_source_manifest_ledger"),
        (SUMMARY_PATH, "repaired_proxy_execution_registry_summary"),
        (BUILDER_MODULE, "repaired_proxy_execution_registry_builder"),
        (VERIFIER_MODULE, "repaired_proxy_execution_registry_verifier"),
    ]
    update_output_manifest(output_entries)
    append_jsonl(
        SPRINT_LEDGER,
        {
            "timestamp_utc": generated_at,
            "event": "repaired_proxy_execution_registry_built",
            "route": PREFIX,
            "counts": counts,
            "research_boundary": research_boundary(),
            "summary": (
                "Converted repaired-proxy execution specs into branch-local registry rows, comparator executions, "
                "repair executions, and market replay population rows."
            ),
        },
    )
    append_checkpoint(generated_at, counts)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
