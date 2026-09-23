#!/usr/bin/env python3
"""Execute rule-match actions against held source-expansion performance rows."""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_expanded_market_source_expansion_rule_match_action_execution import (
    EXPANDED_MARKET_SOURCE_EXPANSION_RULE_MATCH_ACTION_EXECUTION,
    READY_ACTION_STATUSES,
    aggregate_execution_rows,
    boundary_row,
    ready_action_execution_row,
    ready_action_match_rows,
    redesign_action_execution_row,
    replay_task_execution_row,
    research_boundary,
    source_task_execution_row,
    status_counts,
)


ACTION_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_RULE_MATCH_ACTION_APPLICATION"
PERFORMANCE_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_RULE_MATCH_PERFORMANCE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_RULE_MATCH_ACTION_EXECUTION"

ACTION_RESULT = ROUTE_DIR / f"{ACTION_PREFIX}_RESULT_2026-05-17.json"
ACTION_LEDGER = ROUTE_DIR / f"{ACTION_PREFIX}_ACTION_LEDGER_2026-05-17.jsonl"
REPLAY_ACTION_LEDGER = ROUTE_DIR / f"{ACTION_PREFIX}_REPLAY_TASK_ACTION_LEDGER_2026-05-17.jsonl"
SOURCE_ACTION_LEDGER = ROUTE_DIR / f"{ACTION_PREFIX}_SOURCE_TASK_ACTION_LEDGER_2026-05-17.jsonl"
PERFORMANCE_LEDGER = ROUTE_DIR / f"{PERFORMANCE_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_expanded_market_source_expansion_rule_match_action_execution.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_expanded_market_source_expansion_rule_match_action_execution_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
READY_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_READY_ACTION_EXECUTION_LEDGER_2026-05-17.jsonl"
READY_MATCH_LEDGER = ROUTE_DIR / f"{PREFIX}_READY_ACTION_MATCH_LEDGER_2026-05-17.jsonl"
REDESIGN_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_REDESIGN_ACTION_EXECUTION_LEDGER_2026-05-17.jsonl"
REPLAY_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_REPLAY_TASK_ACTION_EXECUTION_LEDGER_2026-05-17.jsonl"
SOURCE_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_TASK_ACTION_EXECUTION_LEDGER_2026-05-17.jsonl"
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


def output_sha256(paths: list[Path]) -> dict[str, str]:
    digest: dict[str, str] = {}
    for path in paths:
        hasher = hashlib.sha256()
        with open(long_path(path), "rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                hasher.update(chunk)
        digest[path.name] = hasher.hexdigest()
    return digest


def manifest_entries() -> list[dict[str, str]]:
    entries = [
        (RESULT_PATH, "expanded_market_source_expansion_rule_match_action_execution_result"),
        (READY_EXECUTION_LEDGER, "expanded_market_source_expansion_ready_action_execution_rows"),
        (READY_MATCH_LEDGER, "expanded_market_source_expansion_ready_action_match_rows"),
        (REDESIGN_EXECUTION_LEDGER, "expanded_market_source_expansion_redesign_action_execution_rows"),
        (REPLAY_EXECUTION_LEDGER, "expanded_market_source_expansion_replay_task_action_execution_rows"),
        (SOURCE_EXECUTION_LEDGER, "expanded_market_source_expansion_source_task_action_execution_rows"),
        (AGGREGATE_LEDGER, "expanded_market_source_expansion_rule_match_action_execution_aggregates"),
        (ISSUE_LEDGER, "expanded_market_source_expansion_rule_match_action_execution_issues"),
        (SYSTEM_LEDGER, "expanded_market_source_expansion_rule_match_action_execution_system"),
        (SUMMARY_PATH, "expanded_market_source_expansion_rule_match_action_execution_summary"),
        (BUILDER_MODULE, "expanded_market_source_expansion_rule_match_action_execution_builder"),
        (VERIFIER_MODULE, "expanded_market_source_expansion_rule_match_action_execution_verifier"),
        (HELPER_MODULE, "expanded_market_source_expansion_rule_match_action_execution_helper"),
        (TEST_MODULE, "expanded_market_source_expansion_rule_match_action_execution_tests"),
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
    manifest["latest_expanded_market_source_expansion_rule_match_action_execution"] = {
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
    marker = "## Checkpoint 277 - Expanded-Market Source Expansion Rule Match Action Execution"
    text = ACTIVE_LEDGER.read_text(encoding="utf-8", errors="replace") if ACTIVE_LEDGER.exists() else ""
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n\n"
    addition = f"""{marker}

Generated: {generated_at}

Trigger: direct continuation after Checkpoint 276. Ready follow/avoid actions were executed against every held CP275 performance row; redesign, replay-task, and source-task actions were preserved as execution rows.

Rows:
- held performance rows scanned per ready action: {counts["held_performance_rows"]}
- ready action execution rows: {counts["ready_action_execution_rows"]}
- ready action match rows: {counts["ready_action_match_rows"]}
- redesign action execution rows: {counts["redesign_action_execution_rows"]}
- replay task action execution rows: {counts["replay_task_action_execution_rows"]}
- source task action execution rows: {counts["source_task_action_execution_rows"]}
- aggregate rows: {counts["aggregate_rows"]}
- issue rows: {counts["issue_rows"]}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: convert ready action executions into concrete branch-local follow/avoid implementation candidates and preserve redesign/replay/source execution rows.
"""
    write_text(ACTIVE_LEDGER, text.rstrip() + "\n\n" + addition)


def build_summary(generated_at: str, counts: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Expanded-Market Source Expansion Rule Match Action Execution",
            "",
            f"Generated: {generated_at}",
            "",
            "This checkpoint executes ready CP276 actions against held performance rows and preserves redesign/replay/source action rows.",
            "",
            f"- Ready action execution rows: `{counts['ready_action_execution_rows']}`",
            f"- Ready action match rows: `{counts['ready_action_match_rows']}`",
            f"- Redesign action execution rows: `{counts['redesign_action_execution_rows']}`",
            f"- Replay task action execution rows: `{counts['replay_task_action_execution_rows']}`",
            f"- Source task action execution rows: `{counts['source_task_action_execution_rows']}`",
            f"- Issue rows: `{counts['issue_rows']}`",
            "",
        ]
    )


def main() -> None:
    generated_at = now_utc()
    action_result = read_json(ACTION_RESULT)
    action_rows = list(iter_jsonl(ACTION_LEDGER))
    replay_action_rows = list(iter_jsonl(REPLAY_ACTION_LEDGER))
    source_action_rows = list(iter_jsonl(SOURCE_ACTION_LEDGER))
    performance_rows = list(iter_jsonl(PERFORMANCE_LEDGER))
    performance_rows_by_id = {
        str(row.get("expanded_market_source_expansion_rule_match_performance_row_id") or ""): row
        for row in performance_rows
    }
    ready_actions = [
        row for row in action_rows if row.get("rule_match_action_status") in READY_ACTION_STATUSES
    ]
    redesign_actions = [
        row for row in action_rows if row.get("rule_match_action_status") not in READY_ACTION_STATUSES
    ]
    ready_execution_rows: list[dict[str, Any]] = []
    ready_match_rows: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    for action in ready_actions:
        execution = ready_action_execution_row(action, performance_rows, len(ready_execution_rows) + 1)
        ready_execution_rows.append(execution)
        ready_match_rows.extend(
            ready_action_match_rows(action, execution, performance_rows_by_id, len(ready_match_rows) + 1)
        )
        if execution.get("ready_action_execution_status") != "SOURCE_EXPANSION_RULE_MATCH_READY_ACTION_EXECUTION_PASS":
            issues.append(
                boundary_row(
                    {
                        "expanded_market_source_expansion_rule_match_action_execution_issue_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-RULE-MATCH-ACTION-EXEC-ISSUE-{len(issues) + 1:07d}"
                        ),
                        "issue_type": "READY_ACTION_EXECUTION_REPAIR_REQUIRED",
                        "input_rule_match_action_row_id": action.get(
                            "expanded_market_source_expansion_rule_match_action_row_id"
                        ),
                        "match_count": execution.get("match_count"),
                        "cost_mismatch_count": execution.get("cost_mismatch_count"),
                        "stress_mismatch_count": execution.get("stress_mismatch_count"),
                    }
                )
            )

    redesign_execution_rows = [
        redesign_action_execution_row(row, index + 1) for index, row in enumerate(redesign_actions)
    ]
    replay_execution_rows = [
        replay_task_execution_row(row, index + 1) for index, row in enumerate(replay_action_rows)
    ]
    source_execution_rows = [
        source_task_execution_row(row, index + 1) for index, row in enumerate(source_action_rows)
    ]
    aggregate_rows = aggregate_execution_rows(
        ready_execution_rows, redesign_execution_rows, replay_execution_rows, source_execution_rows
    )
    counts = {
        "input_rule_match_action_result_ok": action_result.get("ok"),
        "input_rule_match_action_rows": len(action_rows),
        "held_performance_rows": len(performance_rows),
        "ready_action_rows": len(ready_actions),
        "ready_action_execution_rows": len(ready_execution_rows),
        "ready_action_execution_pass_rows": sum(
            1
            for row in ready_execution_rows
            if row.get("ready_action_execution_status")
            == "SOURCE_EXPANSION_RULE_MATCH_READY_ACTION_EXECUTION_PASS"
        ),
        "ready_action_match_rows": len(ready_match_rows),
        "redesign_action_execution_rows": len(redesign_execution_rows),
        "replay_task_action_execution_rows": len(replay_execution_rows),
        "source_task_action_execution_rows": len(source_execution_rows),
        "aggregate_rows": len(aggregate_rows),
        "issue_rows": len(issues),
        "system_rows": 1,
        "total_negative_mismatch_scans": sum(
            int(row.get("negative_mismatch_count") or 0) for row in ready_execution_rows
        ),
        "ready_action_execution_status_counts": status_counts(
            ready_execution_rows, "ready_action_execution_status"
        ),
        "redesign_action_execution_status_counts": status_counts(
            redesign_execution_rows, "redesign_action_execution_status"
        ),
    }
    system_rows = [
        boundary_row(
            {
                "expanded_market_source_expansion_rule_match_action_execution_system_row_id": (
                    "OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-RULE-MATCH-ACTION-EXEC-SYSTEM-0001"
                ),
                **counts,
                "metadata": {
                    "action_ledger": str(ACTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
                    "performance_ledger": str(PERFORMANCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
                    "no_top_n_cutoff": True,
                },
            }
        )
    ]
    output_files = [
        READY_EXECUTION_LEDGER,
        READY_MATCH_LEDGER,
        REDESIGN_EXECUTION_LEDGER,
        REPLAY_EXECUTION_LEDGER,
        SOURCE_EXECUTION_LEDGER,
        AGGREGATE_LEDGER,
        ISSUE_LEDGER,
        SYSTEM_LEDGER,
        SUMMARY_PATH,
    ]
    write_jsonl(READY_EXECUTION_LEDGER, ready_execution_rows)
    write_jsonl(READY_MATCH_LEDGER, ready_match_rows)
    write_jsonl(REDESIGN_EXECUTION_LEDGER, redesign_execution_rows)
    write_jsonl(REPLAY_EXECUTION_LEDGER, replay_execution_rows)
    write_jsonl(SOURCE_EXECUTION_LEDGER, source_execution_rows)
    write_jsonl(AGGREGATE_LEDGER, aggregate_rows)
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
            "rule_match_action_result": str(ACTION_RESULT.relative_to(REPO)).replace("\\", "/"),
            "rule_match_action_ledger": str(ACTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "replay_task_action_ledger": str(REPLAY_ACTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "source_task_action_ledger": str(SOURCE_ACTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "rule_match_performance_ledger": str(PERFORMANCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "ready_action_execution_ledger": str(READY_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "ready_action_match_ledger": str(READY_MATCH_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "redesign_action_execution_ledger": str(REDESIGN_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "replay_task_action_execution_ledger": str(REPLAY_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "source_task_action_execution_ledger": str(SOURCE_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "issue_ledger": str(ISSUE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
        "output_sha256": output_sha256(output_files),
        "expanded_market_source_expansion_rule_match_action_execution_surface": (
            EXPANDED_MARKET_SOURCE_EXPANSION_RULE_MATCH_ACTION_EXECUTION
        ),
        "research_boundary": research_boundary(),
    }
    write_json(RESULT_PATH, result)
    update_manifest(generated_at)
    replace_sprint_event(
        {
            "checkpoint": 277,
            "event": "checkpoint_277_expanded_market_source_expansion_rule_match_action_execution",
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
