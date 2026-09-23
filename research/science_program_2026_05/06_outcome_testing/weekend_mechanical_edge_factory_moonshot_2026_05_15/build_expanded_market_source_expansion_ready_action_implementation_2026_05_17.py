#!/usr/bin/env python3
"""Build branch-local implementation candidates from ready action executions."""

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

from src.research_infra.moonshot_expanded_market_source_expansion_ready_action_implementation import (
    EXPANDED_MARKET_SOURCE_EXPANSION_READY_ACTION_IMPLEMENTATION,
    aggregate_implementation_rows,
    boundary_row,
    implementation_self_test_row,
    ready_implementation_candidate_row,
    redesign_implementation_task_row,
    replay_implementation_task_row,
    research_boundary,
    source_implementation_task_row,
    status_counts,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_RULE_MATCH_ACTION_EXECUTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_READY_ACTION_IMPLEMENTATION"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
READY_EXECUTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_READY_ACTION_EXECUTION_LEDGER_2026-05-17.jsonl"
REDESIGN_EXECUTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_REDESIGN_ACTION_EXECUTION_LEDGER_2026-05-17.jsonl"
REPLAY_EXECUTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_REPLAY_TASK_ACTION_EXECUTION_LEDGER_2026-05-17.jsonl"
SOURCE_EXECUTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SOURCE_TASK_ACTION_EXECUTION_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_expanded_market_source_expansion_ready_action_implementation.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_expanded_market_source_expansion_ready_action_implementation_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
CANDIDATE_LEDGER = ROUTE_DIR / f"{PREFIX}_CANDIDATE_LEDGER_2026-05-17.jsonl"
SELF_TEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SELF_TEST_LEDGER_2026-05-17.jsonl"
REDESIGN_TASK_LEDGER = ROUTE_DIR / f"{PREFIX}_REDESIGN_TASK_LEDGER_2026-05-17.jsonl"
REPLAY_TASK_LEDGER = ROUTE_DIR / f"{PREFIX}_REPLAY_TASK_LEDGER_2026-05-17.jsonl"
SOURCE_TASK_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_TASK_LEDGER_2026-05-17.jsonl"
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
        (RESULT_PATH, "expanded_market_source_expansion_ready_action_implementation_result"),
        (CANDIDATE_LEDGER, "expanded_market_source_expansion_ready_action_implementation_candidates"),
        (SELF_TEST_LEDGER, "expanded_market_source_expansion_ready_action_implementation_self_tests"),
        (REDESIGN_TASK_LEDGER, "expanded_market_source_expansion_redesign_implementation_tasks"),
        (REPLAY_TASK_LEDGER, "expanded_market_source_expansion_replay_implementation_tasks"),
        (SOURCE_TASK_LEDGER, "expanded_market_source_expansion_source_implementation_tasks"),
        (AGGREGATE_LEDGER, "expanded_market_source_expansion_ready_action_implementation_aggregates"),
        (ISSUE_LEDGER, "expanded_market_source_expansion_ready_action_implementation_issues"),
        (SYSTEM_LEDGER, "expanded_market_source_expansion_ready_action_implementation_system"),
        (SUMMARY_PATH, "expanded_market_source_expansion_ready_action_implementation_summary"),
        (BUILDER_MODULE, "expanded_market_source_expansion_ready_action_implementation_builder"),
        (VERIFIER_MODULE, "expanded_market_source_expansion_ready_action_implementation_verifier"),
        (HELPER_MODULE, "expanded_market_source_expansion_ready_action_implementation_helper"),
        (TEST_MODULE, "expanded_market_source_expansion_ready_action_implementation_tests"),
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
    manifest["latest_expanded_market_source_expansion_ready_action_implementation"] = {
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
    marker = "## Checkpoint 278 - Expanded-Market Source Expansion Ready Action Implementation"
    text = ACTIVE_LEDGER.read_text(encoding="utf-8", errors="replace") if ACTIVE_LEDGER.exists() else ""
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n\n"
    addition = f"""{marker}

Generated: {generated_at}

Trigger: direct continuation after Checkpoint 277. Passing ready action executions were converted into branch-local follow/avoid implementation candidate rows with self-tests, while redesign/replay/source execution rows were preserved as concrete implementation tasks.

Rows:
- ready implementation candidate rows: {counts["ready_implementation_candidate_rows"]}
- implementation self-test rows: {counts["implementation_self_test_rows"]}
- redesign implementation task rows: {counts["redesign_implementation_task_rows"]}
- replay implementation task rows: {counts["replay_implementation_task_rows"]}
- source implementation task rows: {counts["source_implementation_task_rows"]}
- aggregate rows: {counts["aggregate_rows"]}
- issue rows: {counts["issue_rows"]}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: execute the branch-local follow/avoid implementation candidates against held ready-action execution rows and preserve all task rows.
"""
    write_text(ACTIVE_LEDGER, text.rstrip() + "\n\n" + addition)


def build_summary(generated_at: str, counts: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Expanded-Market Source Expansion Ready Action Implementation",
            "",
            f"Generated: {generated_at}",
            "",
            "This checkpoint builds branch-local follow/avoid implementation candidates from CP277 ready executions.",
            "",
            f"- Ready implementation candidate rows: `{counts['ready_implementation_candidate_rows']}`",
            f"- Implementation self-test rows: `{counts['implementation_self_test_rows']}`",
            f"- Redesign implementation task rows: `{counts['redesign_implementation_task_rows']}`",
            f"- Replay implementation task rows: `{counts['replay_implementation_task_rows']}`",
            f"- Source implementation task rows: `{counts['source_implementation_task_rows']}`",
            f"- Issue rows: `{counts['issue_rows']}`",
            "",
        ]
    )


def main() -> None:
    generated_at = now_utc()
    input_result = read_json(INPUT_RESULT)
    ready_rows = list(iter_jsonl(READY_EXECUTION_LEDGER))
    redesign_rows = list(iter_jsonl(REDESIGN_EXECUTION_LEDGER))
    replay_rows = list(iter_jsonl(REPLAY_EXECUTION_LEDGER))
    source_rows = list(iter_jsonl(SOURCE_EXECUTION_LEDGER))
    candidate_rows = [
        ready_implementation_candidate_row(row, index + 1) for index, row in enumerate(ready_rows)
    ]
    self_test_rows = [
        implementation_self_test_row(row, index + 1) for index, row in enumerate(candidate_rows)
    ]
    redesign_task_rows = [
        redesign_implementation_task_row(row, index + 1) for index, row in enumerate(redesign_rows)
    ]
    replay_task_rows = [
        replay_implementation_task_row(row, index + 1) for index, row in enumerate(replay_rows)
    ]
    source_task_rows = [
        source_implementation_task_row(row, index + 1) for index, row in enumerate(source_rows)
    ]
    issues = [
        boundary_row(
            {
                "expanded_market_source_expansion_ready_action_implementation_issue_row_id": (
                    f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-READY-ACTION-IMPL-ISSUE-{index + 1:07d}"
                ),
                "issue_type": "READY_ACTION_IMPLEMENTATION_SELF_TEST_REPAIR_REQUIRED",
                "input_ready_action_implementation_candidate_row_id": row.get(
                    "input_ready_action_implementation_candidate_row_id"
                ),
                "ready_action_implementation_kind": row.get("ready_action_implementation_kind"),
            }
        )
        for index, row in enumerate(self_test_rows)
        if row.get("self_test_status") != "SOURCE_EXPANSION_READY_ACTION_IMPLEMENTATION_SELF_TEST_PASS"
    ]
    aggregate_rows = aggregate_implementation_rows(
        candidate_rows, redesign_task_rows, replay_task_rows, source_task_rows
    )
    counts = {
        "input_rule_match_action_execution_result_ok": input_result.get("ok"),
        "input_ready_action_execution_rows": len(ready_rows),
        "ready_implementation_candidate_rows": len(candidate_rows),
        "implementation_self_test_rows": len(self_test_rows),
        "implementation_self_test_pass_rows": sum(
            1
            for row in self_test_rows
            if row.get("self_test_status")
            == "SOURCE_EXPANSION_READY_ACTION_IMPLEMENTATION_SELF_TEST_PASS"
        ),
        "redesign_implementation_task_rows": len(redesign_task_rows),
        "replay_implementation_task_rows": len(replay_task_rows),
        "source_implementation_task_rows": len(source_task_rows),
        "aggregate_rows": len(aggregate_rows),
        "issue_rows": len(issues),
        "system_rows": 1,
        "candidate_status_counts": status_counts(candidate_rows, "ready_action_implementation_status"),
        "candidate_decision_counts": status_counts(candidate_rows, "keep_kill_redesign_implement_decision"),
    }
    system_rows = [
        boundary_row(
            {
                "expanded_market_source_expansion_ready_action_implementation_system_row_id": (
                    "OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-READY-ACTION-IMPL-SYSTEM-0001"
                ),
                **counts,
                "metadata": {
                    "ready_execution_ledger": str(READY_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
                    "no_top_n_cutoff": True,
                },
            }
        )
    ]
    output_files = [
        CANDIDATE_LEDGER,
        SELF_TEST_LEDGER,
        REDESIGN_TASK_LEDGER,
        REPLAY_TASK_LEDGER,
        SOURCE_TASK_LEDGER,
        AGGREGATE_LEDGER,
        ISSUE_LEDGER,
        SYSTEM_LEDGER,
        SUMMARY_PATH,
    ]
    write_jsonl(CANDIDATE_LEDGER, candidate_rows)
    write_jsonl(SELF_TEST_LEDGER, self_test_rows)
    write_jsonl(REDESIGN_TASK_LEDGER, redesign_task_rows)
    write_jsonl(REPLAY_TASK_LEDGER, replay_task_rows)
    write_jsonl(SOURCE_TASK_LEDGER, source_task_rows)
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
            "rule_match_action_execution_result": str(INPUT_RESULT.relative_to(REPO)).replace("\\", "/"),
            "ready_action_execution_ledger": str(READY_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "redesign_action_execution_ledger": str(REDESIGN_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "replay_task_action_execution_ledger": str(REPLAY_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "source_task_action_execution_ledger": str(SOURCE_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "ready_implementation_candidate_ledger": str(CANDIDATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "implementation_self_test_ledger": str(SELF_TEST_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "redesign_task_ledger": str(REDESIGN_TASK_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "replay_task_ledger": str(REPLAY_TASK_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "source_task_ledger": str(SOURCE_TASK_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "issue_ledger": str(ISSUE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
        "output_sha256": output_sha256(output_files),
        "expanded_market_source_expansion_ready_action_implementation_surface": (
            EXPANDED_MARKET_SOURCE_EXPANSION_READY_ACTION_IMPLEMENTATION
        ),
        "research_boundary": research_boundary(),
    }
    write_json(RESULT_PATH, result)
    update_manifest(generated_at)
    replace_sprint_event(
        {
            "checkpoint": 278,
            "event": "checkpoint_278_expanded_market_source_expansion_ready_action_implementation",
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
