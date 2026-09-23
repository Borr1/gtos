#!/usr/bin/env python3
"""Apply rule-match performance rows into concrete action rows."""

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

from src.research_infra.moonshot_expanded_market_source_expansion_rule_match_action_application import (
    EXPANDED_MARKET_SOURCE_EXPANSION_RULE_MATCH_ACTION_APPLICATION,
    action_self_test_row,
    aggregate_action_rows,
    boundary_row,
    replay_task_action_row,
    research_boundary,
    rule_match_action_row,
    source_task_action_row,
    status_counts,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_RULE_MATCH_PERFORMANCE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_RULE_MATCH_ACTION_APPLICATION"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
PERFORMANCE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
REPLAY_PERFORMANCE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_REPLAY_TASK_PERFORMANCE_LEDGER_2026-05-17.jsonl"
SOURCE_PERFORMANCE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SOURCE_TASK_PERFORMANCE_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_expanded_market_source_expansion_rule_match_action_application.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_expanded_market_source_expansion_rule_match_action_application_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
ACTION_LEDGER = ROUTE_DIR / f"{PREFIX}_ACTION_LEDGER_2026-05-17.jsonl"
SELF_TEST_LEDGER = ROUTE_DIR / f"{PREFIX}_ACTION_SELF_TEST_LEDGER_2026-05-17.jsonl"
REPLAY_ACTION_LEDGER = ROUTE_DIR / f"{PREFIX}_REPLAY_TASK_ACTION_LEDGER_2026-05-17.jsonl"
SOURCE_ACTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_TASK_ACTION_LEDGER_2026-05-17.jsonl"
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
        (RESULT_PATH, "expanded_market_source_expansion_rule_match_action_application_result"),
        (ACTION_LEDGER, "expanded_market_source_expansion_rule_match_action_rows"),
        (SELF_TEST_LEDGER, "expanded_market_source_expansion_rule_match_action_self_tests"),
        (REPLAY_ACTION_LEDGER, "expanded_market_source_expansion_replay_task_action_rows"),
        (SOURCE_ACTION_LEDGER, "expanded_market_source_expansion_source_task_action_rows"),
        (AGGREGATE_LEDGER, "expanded_market_source_expansion_rule_match_action_aggregates"),
        (ISSUE_LEDGER, "expanded_market_source_expansion_rule_match_action_issues"),
        (SYSTEM_LEDGER, "expanded_market_source_expansion_rule_match_action_system"),
        (SUMMARY_PATH, "expanded_market_source_expansion_rule_match_action_summary"),
        (BUILDER_MODULE, "expanded_market_source_expansion_rule_match_action_builder"),
        (VERIFIER_MODULE, "expanded_market_source_expansion_rule_match_action_verifier"),
        (HELPER_MODULE, "expanded_market_source_expansion_rule_match_action_helper"),
        (TEST_MODULE, "expanded_market_source_expansion_rule_match_action_tests"),
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
    manifest["latest_expanded_market_source_expansion_rule_match_action_application"] = {
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
    marker = "## Checkpoint 276 - Expanded-Market Source Expansion Rule Match Action Application"
    text = ACTIVE_LEDGER.read_text(encoding="utf-8", errors="replace") if ACTIVE_LEDGER.exists() else ""
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n\n"
    addition = f"""{marker}

Generated: {generated_at}

Trigger: direct continuation after Checkpoint 275. Rule-match performance decisions were converted into concrete follow, avoid, redesign, replay-task, and source-task action rows with self-tests.

Rows:
- input rule match performance rows: {counts["input_rule_match_performance_rows"]}
- rule match action rows: {counts["rule_match_action_rows"]}
- action self-test rows: {counts["action_self_test_rows"]}
- replay task action rows: {counts["replay_task_action_rows"]}
- source task action rows: {counts["source_task_action_rows"]}
- aggregate rows: {counts["aggregate_rows"]}
- issue rows: {counts["issue_rows"]}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: execute the ready follow/avoid action rows against held source-expansion rows and keep redesign/replay/source action rows explicit.
"""
    write_text(ACTIVE_LEDGER, text.rstrip() + "\n\n" + addition)


def build_summary(generated_at: str, counts: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Expanded-Market Source Expansion Rule Match Action Application",
            "",
            f"Generated: {generated_at}",
            "",
            "This checkpoint converts CP275 performance decisions into concrete action rows and self-tests.",
            "",
            f"- Rule match action rows: `{counts['rule_match_action_rows']}`",
            f"- Action self-test rows: `{counts['action_self_test_rows']}`",
            f"- Replay task action rows: `{counts['replay_task_action_rows']}`",
            f"- Source task action rows: `{counts['source_task_action_rows']}`",
            f"- Issue rows: `{counts['issue_rows']}`",
            "",
        ]
    )


def main() -> None:
    generated_at = now_utc()
    input_result = read_json(INPUT_RESULT)
    performance_rows = list(iter_jsonl(PERFORMANCE_LEDGER))
    replay_performance_rows = list(iter_jsonl(REPLAY_PERFORMANCE_LEDGER))
    source_performance_rows = list(iter_jsonl(SOURCE_PERFORMANCE_LEDGER))
    action_rows = [rule_match_action_row(row, index + 1) for index, row in enumerate(performance_rows)]
    self_test_rows = [action_self_test_row(row, index + 1) for index, row in enumerate(action_rows)]
    replay_action_rows = [
        replay_task_action_row(row, index + 1) for index, row in enumerate(replay_performance_rows)
    ]
    source_action_rows = [
        source_task_action_row(row, index + 1) for index, row in enumerate(source_performance_rows)
    ]
    issues = [
        boundary_row(
            {
                "expanded_market_source_expansion_rule_match_action_issue_row_id": (
                    f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-RULE-MATCH-ACTION-ISSUE-{index + 1:07d}"
                ),
                "issue_type": "RULE_MATCH_ACTION_SELF_TEST_REPAIR_REQUIRED",
                "input_rule_match_action_row_id": row.get("input_rule_match_action_row_id"),
                "rule_match_action_kind": row.get("rule_match_action_kind"),
            }
        )
        for index, row in enumerate(self_test_rows)
        if row.get("self_test_status") != "SOURCE_EXPANSION_RULE_MATCH_ACTION_SELF_TEST_PASS"
    ]
    aggregate_rows = aggregate_action_rows(action_rows, replay_action_rows, source_action_rows)
    counts = {
        "input_rule_match_performance_result_ok": input_result.get("ok"),
        "input_rule_match_performance_rows": len(performance_rows),
        "rule_match_action_rows": len(action_rows),
        "action_self_test_rows": len(self_test_rows),
        "action_self_test_pass_rows": sum(
            1
            for row in self_test_rows
            if row.get("self_test_status") == "SOURCE_EXPANSION_RULE_MATCH_ACTION_SELF_TEST_PASS"
        ),
        "replay_task_action_rows": len(replay_action_rows),
        "source_task_action_rows": len(source_action_rows),
        "aggregate_rows": len(aggregate_rows),
        "issue_rows": len(issues),
        "system_rows": 1,
        "action_status_counts": status_counts(action_rows, "rule_match_action_status"),
        "action_decision_counts": status_counts(action_rows, "keep_kill_redesign_implement_decision"),
    }
    system_rows = [
        boundary_row(
            {
                "expanded_market_source_expansion_rule_match_action_system_row_id": (
                    "OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-RULE-MATCH-ACTION-SYSTEM-0001"
                ),
                **counts,
                "metadata": {
                    "performance_ledger": str(PERFORMANCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
                    "no_top_n_cutoff": True,
                },
            }
        )
    ]
    output_files = [
        ACTION_LEDGER,
        SELF_TEST_LEDGER,
        REPLAY_ACTION_LEDGER,
        SOURCE_ACTION_LEDGER,
        AGGREGATE_LEDGER,
        ISSUE_LEDGER,
        SYSTEM_LEDGER,
        SUMMARY_PATH,
    ]
    write_jsonl(ACTION_LEDGER, action_rows)
    write_jsonl(SELF_TEST_LEDGER, self_test_rows)
    write_jsonl(REPLAY_ACTION_LEDGER, replay_action_rows)
    write_jsonl(SOURCE_ACTION_LEDGER, source_action_rows)
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
            "rule_match_performance_result": str(INPUT_RESULT.relative_to(REPO)).replace("\\", "/"),
            "rule_match_performance_ledger": str(PERFORMANCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "replay_task_performance_ledger": str(REPLAY_PERFORMANCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "source_task_performance_ledger": str(SOURCE_PERFORMANCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "rule_match_action_ledger": str(ACTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "action_self_test_ledger": str(SELF_TEST_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "replay_task_action_ledger": str(REPLAY_ACTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "source_task_action_ledger": str(SOURCE_ACTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "issue_ledger": str(ISSUE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
        "output_sha256": output_sha256(output_files),
        "expanded_market_source_expansion_rule_match_action_application_surface": (
            EXPANDED_MARKET_SOURCE_EXPANSION_RULE_MATCH_ACTION_APPLICATION
        ),
        "research_boundary": research_boundary(),
    }
    write_json(RESULT_PATH, result)
    update_manifest(generated_at)
    replace_sprint_event(
        {
            "checkpoint": 276,
            "event": "checkpoint_276_expanded_market_source_expansion_rule_match_action_application",
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
