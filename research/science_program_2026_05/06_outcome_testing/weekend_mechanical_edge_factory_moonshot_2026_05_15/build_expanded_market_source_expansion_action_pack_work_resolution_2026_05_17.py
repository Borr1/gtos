#!/usr/bin/env python3
"""Resolve preserved action-pack work rows into concrete replay/source tasks."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_expanded_market_source_expansion_action_pack_work_resolution import (
    EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_PACK_WORK_RESOLUTION,
    aggregate_work_resolution_rows,
    boundary_row,
    research_boundary,
    work_resolution_row,
)


PACK_EXEC_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_PACK_EXECUTION"
SOURCE_EXEC_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_EXECUTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_PACK_WORK_RESOLUTION"

PACK_EXEC_RESULT = ROUTE_DIR / f"{PACK_EXEC_PREFIX}_RESULT_2026-05-17.json"
WORK_EXECUTION_LEDGER = ROUTE_DIR / f"{PACK_EXEC_PREFIX}_WORK_EXECUTION_LEDGER_2026-05-17.jsonl"
DISCOVERED_SOURCE_LEDGER = ROUTE_DIR / f"{SOURCE_EXEC_PREFIX}_DISCOVERED_OHLC_SOURCE_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_expanded_market_source_expansion_action_pack_work_resolution.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_expanded_market_source_expansion_action_pack_work_resolution_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
ROW_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_ISSUE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
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


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with open(long_path(path), "r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    with open(long_path(path), "w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with open(long_path(path), "w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_text(path: Path, text: str) -> None:
    with open(long_path(path), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def file_sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    hasher = hashlib.sha256()
    with open(long_path(path), "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def output_sha256(paths: list[Path]) -> dict[str, str]:
    digest: dict[str, str] = {}
    for path in paths:
        digest[path.name] = file_sha256(path) or ""
    return digest


def discovered_index() -> dict[tuple[str, str], list[dict[str, Any]]]:
    output: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in iter_jsonl(DISCOVERED_SOURCE_LEDGER):
        output[(str(row.get("source_symbol") or ""), str(row.get("source_timeframe") or ""))].append(row)
    return output


def source_proof_for(
    row: dict[str, Any],
    discovered: dict[tuple[str, str], list[dict[str, Any]]],
    file_hash_cache: dict[str, str | None],
) -> dict[str, Any]:
    rel_path = str(row.get("source_path") or "")
    path = (REPO / rel_path) if rel_path else REPO / "__missing_source_path__"
    cache_key = str(path)
    if cache_key not in file_hash_cache:
        file_hash_cache[cache_key] = file_sha256(path)
    current_hash = file_hash_cache[cache_key]
    same_sources = discovered.get(
        (str(row.get("source_symbol") or ""), str(row.get("market_timeframe") or "")),
        [],
    )
    return {
        "current_source_path_exists": path.exists() and path.is_file(),
        "current_source_file_sha256": current_hash,
        "current_source_file_hash_matches_row": (
            current_hash is not None and current_hash == row.get("source_file_sha256")
        ),
        "discovered_same_symbol_timeframe_source_count": len(same_sources),
        "discovered_same_symbol_timeframe_source_paths": sorted(
            {str(item.get("source_path") or "") for item in same_sources}
        ),
    }


def manifest_entries() -> list[dict[str, str]]:
    entries = [
        (RESULT_PATH, "expanded_market_source_expansion_action_pack_work_resolution_result"),
        (ROW_LEDGER, "expanded_market_source_expansion_action_pack_work_resolution_rows"),
        (AGGREGATE_LEDGER, "expanded_market_source_expansion_action_pack_work_resolution_aggregates"),
        (ISSUE_LEDGER, "expanded_market_source_expansion_action_pack_work_resolution_issues"),
        (SYSTEM_LEDGER, "expanded_market_source_expansion_action_pack_work_resolution_system"),
        (SUMMARY_PATH, "expanded_market_source_expansion_action_pack_work_resolution_summary"),
        (BUILDER_MODULE, "expanded_market_source_expansion_action_pack_work_resolution_builder"),
        (VERIFIER_MODULE, "expanded_market_source_expansion_action_pack_work_resolution_verifier"),
        (HELPER_MODULE, "expanded_market_source_expansion_action_pack_work_resolution_helper"),
        (TEST_MODULE, "expanded_market_source_expansion_action_pack_work_resolution_tests"),
    ]
    return [
        {"path": str(path.relative_to(REPO)).replace("\\", "/"), "status": "created", "type": kind}
        for path, kind in entries
    ]


def update_manifest(generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    entries = manifest_entries()
    types = {entry["type"] for entry in entries}
    existing = manifest.setdefault("artifacts", [])
    manifest["artifacts"] = [row for row in existing if row.get("type") not in types] + entries
    manifest["latest_expanded_market_source_expansion_action_pack_work_resolution"] = {
        "generated_utc": generated_at,
        "files": entries,
        "result": str(RESULT_PATH.relative_to(REPO)).replace("\\", "/"),
    }
    manifest["last_updated_utc"] = generated_at
    write_json(OUTPUT_MANIFEST, manifest)


def replace_sprint_event(event: dict[str, Any]) -> None:
    kept_lines: list[str] = []
    if SPRINT_LEDGER.exists():
        with open(long_path(SPRINT_LEDGER), "r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    kept_lines.append(line.rstrip("\n"))
                    continue
                if row.get("event") == event.get("event"):
                    continue
                kept_lines.append(json.dumps(row, sort_keys=True))
    kept_lines.append(json.dumps(event, sort_keys=True))
    write_text(SPRINT_LEDGER, "\n".join(kept_lines) + "\n")


def replace_active_checkpoint(generated_at: str, counts: dict[str, Any]) -> None:
    marker = "## Checkpoint 272 - Expanded-Market Source Expansion Action Pack Work Resolution"
    text = ACTIVE_LEDGER.read_text(encoding="utf-8", errors="replace") if ACTIVE_LEDGER.exists() else ""
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n\n"
    addition = f"""{marker}

Generated: {generated_at}

Trigger: direct continuation after Checkpoint 271. Preserved action-pack work rows were resolved into concrete rule, replay, or source-acquisition task statuses with current disk source path/hash proof.

Rows:
- input work-execution rows: {counts["input_work_execution_rows"]}
- work-resolution rows: {counts["work_resolution_rows"]}
- aggregate rows: {counts["aggregate_rows"]}
- issue rows: {counts["issue_rows"]}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: consume rule-required rows into branch-local rule redesign candidates and source/replay-required rows into acquisition/replay implementation tasks.
"""
    write_text(ACTIVE_LEDGER, text.rstrip() + "\n\n" + addition)


def build_summary(generated_at: str, counts: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Expanded-Market Source Expansion Action Pack Work Resolution",
            "",
            f"Generated: {generated_at}",
            "",
            "This checkpoint resolves preserved CP271 work rows into concrete rule/replay/source task statuses with source path/hash proof.",
            "",
            f"- Input work-execution rows: `{counts['input_work_execution_rows']}`",
            f"- Work-resolution rows: `{counts['work_resolution_rows']}`",
            f"- Aggregate rows: `{counts['aggregate_rows']}`",
            f"- Issue rows: `{counts['issue_rows']}`",
            "",
            "## Status Counts",
            "",
            f"`{json.dumps(counts['resolution_status_counts'], sort_keys=True)}`",
            "",
        ]
    )


def main() -> None:
    generated_at = now_utc()
    pack_exec_result = read_json(PACK_EXEC_RESULT)
    discovered = discovered_index()
    resolution_rows: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    file_hash_cache: dict[str, str | None] = {}
    for row in iter_jsonl(WORK_EXECUTION_LEDGER):
        proof = source_proof_for(row, discovered, file_hash_cache)
        resolution_rows.append(work_resolution_row(row, proof, len(resolution_rows) + 1))

    aggregates = aggregate_work_resolution_rows(resolution_rows)
    status_counts = Counter(row.get("work_resolution_status") for row in resolution_rows)
    decision_counts = Counter(row.get("keep_kill_redesign_implement_decision") for row in resolution_rows)
    counts = {
        "input_pack_execution_result_ok": pack_exec_result.get("ok"),
        "input_work_execution_rows": len(resolution_rows),
        "work_resolution_rows": len(resolution_rows),
        "rows_with_simulated_r": sum(row.get("cost_adjusted_simulated_r") is not None for row in resolution_rows),
        "current_source_path_exists_rows": sum(
            row.get("current_source_path_exists") is True for row in resolution_rows
        ),
        "current_source_file_hash_match_rows": sum(
            row.get("current_source_file_hash_matches_row") is True for row in resolution_rows
        ),
        "aggregate_rows": len(aggregates),
        "issue_rows": len(issues),
        "system_rows": 1,
        "resolution_status_counts": dict(sorted(status_counts.items())),
        "decision_counts": dict(sorted(decision_counts.items())),
    }
    system_rows = [
        boundary_row(
            {
                "expanded_market_source_expansion_action_pack_work_resolution_system_row_id": (
                    "OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-ACTION-PACK-WORK-RES-SYSTEM-0001"
                ),
                **counts,
                "metadata": {
                    "work_execution_ledger": str(WORK_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
                    "discovered_source_ledger": str(DISCOVERED_SOURCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
                    "no_top_n_cutoff": True,
                },
            }
        )
    ]
    output_files = [ROW_LEDGER, AGGREGATE_LEDGER, ISSUE_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]
    write_jsonl(ROW_LEDGER, resolution_rows)
    write_jsonl(AGGREGATE_LEDGER, aggregates)
    write_jsonl(ISSUE_LEDGER, issues)
    write_jsonl(SYSTEM_LEDGER, system_rows)
    write_text(SUMMARY_PATH, build_summary(generated_at, counts))
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "ok": not issues,
        "issues": issues,
        "counts": counts,
        "inputs": {
            "pack_execution_result": str(PACK_EXEC_RESULT.relative_to(REPO)).replace("\\", "/"),
            "work_execution_ledger": str(WORK_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "discovered_source_ledger": str(DISCOVERED_SOURCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "row_ledger": str(ROW_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "issue_ledger": str(ISSUE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
        "output_sha256": output_sha256(output_files),
        "expanded_market_source_expansion_action_pack_work_resolution_surface": (
            EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_PACK_WORK_RESOLUTION
        ),
        "research_boundary": research_boundary(),
    }
    write_json(RESULT_PATH, result)
    update_manifest(generated_at)
    replace_sprint_event(
        {
            "checkpoint": 272,
            "event": "checkpoint_272_expanded_market_source_expansion_action_pack_work_resolution",
            "generated_utc": generated_at,
            "result": str(RESULT_PATH.relative_to(REPO)).replace("\\", "/"),
            "counts": counts,
            "boundary": research_boundary(),
        }
    )
    replace_active_checkpoint(generated_at, counts)
    print(json.dumps({"ok": result["ok"], "counts": counts}, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
