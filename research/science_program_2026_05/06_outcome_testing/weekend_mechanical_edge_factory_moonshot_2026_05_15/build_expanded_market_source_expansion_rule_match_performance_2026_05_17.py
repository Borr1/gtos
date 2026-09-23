#!/usr/bin/env python3
"""Build rule-match performance rows from CP274 source-expansion matches."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_expanded_market_source_expansion_rule_match_performance import (
    EXPANDED_MARKET_SOURCE_EXPANSION_RULE_MATCH_PERFORMANCE,
    aggregate_performance_rows,
    boundary_row,
    new_stats,
    replay_task_performance_row,
    research_boundary,
    rule_match_performance_row,
    source_task_performance_row,
    update_stats,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_RULE_CANDIDATE_EXECUTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_RULE_MATCH_PERFORMANCE"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
RULE_EXECUTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_RULE_EXECUTION_LEDGER_2026-05-17.jsonl"
MATCH_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_MATCH_LEDGER_2026-05-17.jsonl"
REPLAY_TASK_EXECUTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_REPLAY_TASK_EXECUTION_LEDGER_2026-05-17.jsonl"
SOURCE_TASK_EXECUTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SOURCE_TASK_EXECUTION_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_expanded_market_source_expansion_rule_match_performance.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_expanded_market_source_expansion_rule_match_performance_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
PERFORMANCE_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
REPLAY_TASK_PERFORMANCE_LEDGER = ROUTE_DIR / f"{PREFIX}_REPLAY_TASK_PERFORMANCE_LEDGER_2026-05-17.jsonl"
SOURCE_TASK_PERFORMANCE_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_TASK_PERFORMANCE_LEDGER_2026-05-17.jsonl"
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
        (RESULT_PATH, "expanded_market_source_expansion_rule_match_performance_result"),
        (PERFORMANCE_LEDGER, "expanded_market_source_expansion_rule_match_performance_rows"),
        (
            REPLAY_TASK_PERFORMANCE_LEDGER,
            "expanded_market_source_expansion_rule_match_replay_task_performance_rows",
        ),
        (
            SOURCE_TASK_PERFORMANCE_LEDGER,
            "expanded_market_source_expansion_rule_match_source_task_performance_rows",
        ),
        (AGGREGATE_LEDGER, "expanded_market_source_expansion_rule_match_performance_aggregates"),
        (ISSUE_LEDGER, "expanded_market_source_expansion_rule_match_performance_issues"),
        (SYSTEM_LEDGER, "expanded_market_source_expansion_rule_match_performance_system"),
        (SUMMARY_PATH, "expanded_market_source_expansion_rule_match_performance_summary"),
        (BUILDER_MODULE, "expanded_market_source_expansion_rule_match_performance_builder"),
        (VERIFIER_MODULE, "expanded_market_source_expansion_rule_match_performance_verifier"),
        (HELPER_MODULE, "expanded_market_source_expansion_rule_match_performance_helper"),
        (TEST_MODULE, "expanded_market_source_expansion_rule_match_performance_tests"),
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
    manifest["latest_expanded_market_source_expansion_rule_match_performance"] = {
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
    marker = "## Checkpoint 275 - Expanded-Market Source Expansion Rule Match Performance"
    text = ACTIVE_LEDGER.read_text(encoding="utf-8", errors="replace") if ACTIVE_LEDGER.exists() else ""
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n\n"
    addition = f"""{marker}

Generated: {generated_at}

Trigger: direct continuation after Checkpoint 274. Rule-candidate match rows were aggregated into rule-level numeric performance selection rows; replay and source task executions were preserved as concrete implementation inputs.

Rows:
- input rule execution rows: {counts["input_rule_execution_rows"]}
- input rule match rows: {counts["input_rule_match_rows"]}
- rule match performance rows: {counts["rule_match_performance_rows"]}
- replay task performance rows: {counts["replay_task_performance_rows"]}
- source task performance rows: {counts["source_task_performance_rows"]}
- aggregate rows: {counts["aggregate_rows"]}
- issue rows: {counts["issue_rows"]}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: apply rule-match performance decisions into concrete branch-local implementation and avoid/source tasks, preserving every replay/source row.
"""
    write_text(ACTIVE_LEDGER, text.rstrip() + "\n\n" + addition)


def build_summary(generated_at: str, counts: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Expanded-Market Source Expansion Rule Match Performance",
            "",
            f"Generated: {generated_at}",
            "",
            "This checkpoint computes rule-level performance from CP274 match rows and preserves replay/source task executions.",
            "",
            f"- Input rule execution rows: `{counts['input_rule_execution_rows']}`",
            f"- Input rule match rows: `{counts['input_rule_match_rows']}`",
            f"- Rule match performance rows: `{counts['rule_match_performance_rows']}`",
            f"- Replay task performance rows: `{counts['replay_task_performance_rows']}`",
            f"- Source task performance rows: `{counts['source_task_performance_rows']}`",
            f"- Issue rows: `{counts['issue_rows']}`",
            "",
        ]
    )


def main() -> None:
    generated_at = now_utc()
    input_result = read_json(INPUT_RESULT)
    rule_execution_rows = list(iter_jsonl(RULE_EXECUTION_LEDGER))
    replay_execution_rows = list(iter_jsonl(REPLAY_TASK_EXECUTION_LEDGER))
    source_execution_rows = list(iter_jsonl(SOURCE_TASK_EXECUTION_LEDGER))
    stats_by_execution_id: dict[str, dict[str, Any]] = {}
    input_match_rows = 0
    for match_row in iter_jsonl(MATCH_LEDGER):
        input_match_rows += 1
        execution_id = str(match_row.get("input_rule_candidate_execution_row_id") or "")
        stats = stats_by_execution_id.setdefault(execution_id, new_stats())
        update_stats(stats, match_row)

    performance_rows: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    for index, rule_row in enumerate(rule_execution_rows, start=1):
        execution_id = str(
            rule_row.get("expanded_market_source_expansion_rule_candidate_execution_row_id") or ""
        )
        stats = stats_by_execution_id.get(execution_id) or new_stats()
        performance = rule_match_performance_row(rule_row, stats, index)
        performance_rows.append(performance)
        if int(performance.get("observed_match_rows") or 0) != int(rule_row.get("match_count") or 0):
            issues.append(
                boundary_row(
                    {
                        "expanded_market_source_expansion_rule_match_performance_issue_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-RULE-MATCH-PERF-ISSUE-{len(issues) + 1:07d}"
                        ),
                        "issue_type": "RULE_MATCH_COUNT_MISMATCH",
                        "input_rule_candidate_execution_row_id": execution_id,
                        "reported_match_count": rule_row.get("match_count"),
                        "observed_match_rows": performance.get("observed_match_rows"),
                    }
                )
            )

    replay_performance_rows = [
        replay_task_performance_row(row, index + 1)
        for index, row in enumerate(replay_execution_rows)
    ]
    source_performance_rows = [
        source_task_performance_row(row, index + 1)
        for index, row in enumerate(source_execution_rows)
    ]
    aggregate_rows = aggregate_performance_rows(
        performance_rows, replay_performance_rows, source_performance_rows
    )
    decision_counts = Counter(row.get("keep_kill_redesign_implement_decision") for row in performance_rows)
    action_counts = Counter(row.get("follow_inverse_default_off_avoid_class") for row in performance_rows)
    counts = {
        "input_rule_candidate_execution_result_ok": input_result.get("ok"),
        "input_rule_execution_rows": len(rule_execution_rows),
        "input_rule_match_rows": input_match_rows,
        "rule_match_performance_rows": len(performance_rows),
        "replay_task_performance_rows": len(replay_performance_rows),
        "source_task_performance_rows": len(source_performance_rows),
        "aggregate_rows": len(aggregate_rows),
        "issue_rows": len(issues),
        "system_rows": 1,
        "matched_rows_preserved": sum(int(row.get("observed_match_rows") or 0) for row in performance_rows),
        "decision_counts": dict(sorted(decision_counts.items())),
        "action_class_counts": dict(sorted(action_counts.items())),
    }
    system_rows = [
        boundary_row(
            {
                "expanded_market_source_expansion_rule_match_performance_system_row_id": (
                    "OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-RULE-MATCH-PERF-SYSTEM-0001"
                ),
                **counts,
                "metadata": {
                    "rule_execution_ledger": str(RULE_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
                    "match_ledger": str(MATCH_LEDGER.relative_to(REPO)).replace("\\", "/"),
                    "no_top_n_cutoff": True,
                },
            }
        )
    ]
    output_files = [
        PERFORMANCE_LEDGER,
        REPLAY_TASK_PERFORMANCE_LEDGER,
        SOURCE_TASK_PERFORMANCE_LEDGER,
        AGGREGATE_LEDGER,
        ISSUE_LEDGER,
        SYSTEM_LEDGER,
        SUMMARY_PATH,
    ]
    write_jsonl(PERFORMANCE_LEDGER, performance_rows)
    write_jsonl(REPLAY_TASK_PERFORMANCE_LEDGER, replay_performance_rows)
    write_jsonl(SOURCE_TASK_PERFORMANCE_LEDGER, source_performance_rows)
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
            "rule_candidate_execution_result": str(INPUT_RESULT.relative_to(REPO)).replace("\\", "/"),
            "rule_execution_ledger": str(RULE_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "match_ledger": str(MATCH_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "replay_task_execution_ledger": str(REPLAY_TASK_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "source_task_execution_ledger": str(SOURCE_TASK_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "rule_match_performance_ledger": str(PERFORMANCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "replay_task_performance_ledger": str(REPLAY_TASK_PERFORMANCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "source_task_performance_ledger": str(SOURCE_TASK_PERFORMANCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "issue_ledger": str(ISSUE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
        "output_sha256": output_sha256(output_files),
        "expanded_market_source_expansion_rule_match_performance_surface": (
            EXPANDED_MARKET_SOURCE_EXPANSION_RULE_MATCH_PERFORMANCE
        ),
        "research_boundary": research_boundary(),
    }
    write_json(RESULT_PATH, result)
    update_manifest(generated_at)
    replace_sprint_event(
        {
            "checkpoint": 275,
            "event": "checkpoint_275_expanded_market_source_expansion_rule_match_performance",
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
