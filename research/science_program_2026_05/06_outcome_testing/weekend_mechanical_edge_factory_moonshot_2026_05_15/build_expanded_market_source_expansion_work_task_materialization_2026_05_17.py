#!/usr/bin/env python3
"""Materialize source-expansion work-resolution rows into concrete task ledgers."""

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

from src.research_infra.moonshot_expanded_market_source_expansion_work_task_materialization import (
    EXPANDED_MARKET_SOURCE_EXPANSION_WORK_TASK_MATERIALIZATION,
    aggregate_task_rows,
    boundary_row,
    replay_task_row,
    research_boundary,
    rule_candidate_row,
    rule_candidate_self_test_row,
    source_task_row,
)


WORK_RES_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_PACK_WORK_RESOLUTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_WORK_TASK_MATERIALIZATION"

WORK_RES_RESULT = ROUTE_DIR / f"{WORK_RES_PREFIX}_RESULT_2026-05-17.json"
WORK_RES_ROW_LEDGER = ROUTE_DIR / f"{WORK_RES_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_expanded_market_source_expansion_work_task_materialization.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_expanded_market_source_expansion_work_task_materialization_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
RULE_LEDGER = ROUTE_DIR / f"{PREFIX}_RULE_CANDIDATE_LEDGER_2026-05-17.jsonl"
RULE_SELF_TEST_LEDGER = ROUTE_DIR / f"{PREFIX}_RULE_SELF_TEST_LEDGER_2026-05-17.jsonl"
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
        (RESULT_PATH, "expanded_market_source_expansion_work_task_materialization_result"),
        (RULE_LEDGER, "expanded_market_source_expansion_rule_candidates"),
        (RULE_SELF_TEST_LEDGER, "expanded_market_source_expansion_rule_candidate_self_tests"),
        (REPLAY_TASK_LEDGER, "expanded_market_source_expansion_replay_tasks"),
        (SOURCE_TASK_LEDGER, "expanded_market_source_expansion_source_tasks"),
        (AGGREGATE_LEDGER, "expanded_market_source_expansion_work_task_aggregates"),
        (ISSUE_LEDGER, "expanded_market_source_expansion_work_task_issues"),
        (SYSTEM_LEDGER, "expanded_market_source_expansion_work_task_system"),
        (SUMMARY_PATH, "expanded_market_source_expansion_work_task_summary"),
        (BUILDER_MODULE, "expanded_market_source_expansion_work_task_builder"),
        (VERIFIER_MODULE, "expanded_market_source_expansion_work_task_verifier"),
        (HELPER_MODULE, "expanded_market_source_expansion_work_task_helper"),
        (TEST_MODULE, "expanded_market_source_expansion_work_task_tests"),
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
    manifest["latest_expanded_market_source_expansion_work_task_materialization"] = {
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
    marker = "## Checkpoint 273 - Expanded-Market Source Expansion Work Task Materialization"
    text = ACTIVE_LEDGER.read_text(encoding="utf-8", errors="replace") if ACTIVE_LEDGER.exists() else ""
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n\n"
    addition = f"""{marker}

Generated: {generated_at}

Trigger: direct continuation after Checkpoint 272. Work-resolution rows were materialized into rule candidates, replay implementation tasks, and source-acquisition tasks with no row dropped.

Rows:
- input work-resolution rows: {counts["input_work_resolution_rows"]}
- rule candidate rows: {counts["rule_candidate_rows"]}
- rule self-test rows: {counts["rule_self_test_rows"]}
- replay task rows: {counts["replay_task_rows"]}
- source task rows: {counts["source_task_rows"]}
- aggregate rows: {counts["aggregate_rows"]}
- issue rows: {counts["issue_rows"]}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: execute rule candidates against held rows and keep replay/source task ledgers as concrete implementation inputs.
"""
    write_text(ACTIVE_LEDGER, text.rstrip() + "\n\n" + addition)


def build_summary(generated_at: str, counts: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Expanded-Market Source Expansion Work Task Materialization",
            "",
            f"Generated: {generated_at}",
            "",
            "This checkpoint materializes CP272 work-resolution rows into rule candidates, replay tasks, and source-acquisition tasks.",
            "",
            f"- Input work-resolution rows: `{counts['input_work_resolution_rows']}`",
            f"- Rule candidate rows: `{counts['rule_candidate_rows']}`",
            f"- Rule self-test rows: `{counts['rule_self_test_rows']}`",
            f"- Replay task rows: `{counts['replay_task_rows']}`",
            f"- Source task rows: `{counts['source_task_rows']}`",
            f"- Aggregate rows: `{counts['aggregate_rows']}`",
            f"- Issue rows: `{counts['issue_rows']}`",
            "",
            "## Rule Classes",
            "",
            f"`{json.dumps(counts['rule_candidate_class_counts'], sort_keys=True)}`",
            "",
        ]
    )


def main() -> None:
    generated_at = now_utc()
    work_result = read_json(WORK_RES_RESULT)
    rule_rows: list[dict[str, Any]] = []
    rule_self_tests: list[dict[str, Any]] = []
    replay_rows: list[dict[str, Any]] = []
    source_rows: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    input_count = 0

    for row in iter_jsonl(WORK_RES_ROW_LEDGER):
        input_count += 1
        status = row.get("work_resolution_status")
        if status == "ACTION_PACK_WORK_RESOLUTION_RULE_REDESIGN_NUMERIC_AVAILABLE":
            candidate = rule_candidate_row(row, len(rule_rows) + 1)
            rule_rows.append(candidate)
            self_test = rule_candidate_self_test_row(candidate, row, len(rule_self_tests) + 1)
            rule_self_tests.append(self_test)
            if self_test.get("self_test_status") != "SOURCE_EXPANSION_RULE_CANDIDATE_SELF_TEST_PASS":
                issues.append(
                    boundary_row(
                        {
                            "expanded_market_source_expansion_work_task_issue_row_id": (
                                f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-WORK-TASK-ISSUE-{len(issues) + 1:07d}"
                            ),
                            "issue_type": "RULE_CANDIDATE_SELF_TEST_FAILURE",
                            "input_rule_candidate_row_id": candidate.get(
                                "expanded_market_source_expansion_rule_candidate_row_id"
                            ),
                        }
                    )
                )
        elif status == "ACTION_PACK_WORK_RESOLUTION_REPLAY_IMPLEMENTATION_REQUIRED":
            replay_rows.append(replay_task_row(row, len(replay_rows) + 1))
        elif status == "ACTION_PACK_WORK_RESOLUTION_SOURCE_ACQUISITION_REQUIRED":
            source_rows.append(source_task_row(row, len(source_rows) + 1))
        else:
            issues.append(
                boundary_row(
                    {
                        "expanded_market_source_expansion_work_task_issue_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-WORK-TASK-ISSUE-{len(issues) + 1:07d}"
                        ),
                        "issue_type": "UNKNOWN_WORK_RESOLUTION_STATUS",
                        "input_work_resolution_row_id": row.get(
                            "expanded_market_source_expansion_action_pack_work_resolution_row_id"
                        ),
                        "work_resolution_status": status,
                    }
                )
            )

    aggregate_rows = aggregate_task_rows(rule_rows, replay_rows, source_rows)
    rule_classes = Counter(row.get("rule_candidate_class") for row in rule_rows)
    decisions = Counter(
        [row.get("keep_kill_redesign_implement_decision") for row in rule_rows]
        + [row.get("keep_kill_redesign_implement_decision") for row in replay_rows]
        + [row.get("keep_kill_redesign_implement_decision") for row in source_rows]
    )
    counts = {
        "input_work_resolution_result_ok": work_result.get("ok"),
        "input_work_resolution_rows": input_count,
        "rule_candidate_rows": len(rule_rows),
        "rule_self_test_rows": len(rule_self_tests),
        "rule_self_test_pass_rows": sum(
            row.get("self_test_status") == "SOURCE_EXPANSION_RULE_CANDIDATE_SELF_TEST_PASS"
            for row in rule_self_tests
        ),
        "replay_task_rows": len(replay_rows),
        "source_task_rows": len(source_rows),
        "aggregate_rows": len(aggregate_rows),
        "issue_rows": len(issues),
        "system_rows": 1,
        "rows_with_simulated_r": sum(row.get("cost_adjusted_simulated_r") is not None for row in rule_rows),
        "rule_candidate_class_counts": dict(sorted(rule_classes.items())),
        "decision_counts": dict(sorted(decisions.items())),
    }
    system_rows = [
        boundary_row(
            {
                "expanded_market_source_expansion_work_task_system_row_id": (
                    "OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-WORK-TASK-SYSTEM-0001"
                ),
                **counts,
                "metadata": {
                    "work_resolution_row_ledger": str(WORK_RES_ROW_LEDGER.relative_to(REPO)).replace("\\", "/"),
                    "no_top_n_cutoff": True,
                },
            }
        )
    ]
    output_files = [
        RULE_LEDGER,
        RULE_SELF_TEST_LEDGER,
        REPLAY_TASK_LEDGER,
        SOURCE_TASK_LEDGER,
        AGGREGATE_LEDGER,
        ISSUE_LEDGER,
        SYSTEM_LEDGER,
        SUMMARY_PATH,
    ]
    write_jsonl(RULE_LEDGER, rule_rows)
    write_jsonl(RULE_SELF_TEST_LEDGER, rule_self_tests)
    write_jsonl(REPLAY_TASK_LEDGER, replay_rows)
    write_jsonl(SOURCE_TASK_LEDGER, source_rows)
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
            "work_resolution_result": str(WORK_RES_RESULT.relative_to(REPO)).replace("\\", "/"),
            "work_resolution_row_ledger": str(WORK_RES_ROW_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "rule_candidate_ledger": str(RULE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "rule_self_test_ledger": str(RULE_SELF_TEST_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "replay_task_ledger": str(REPLAY_TASK_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "source_task_ledger": str(SOURCE_TASK_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "issue_ledger": str(ISSUE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
        "output_sha256": output_sha256(output_files),
        "expanded_market_source_expansion_work_task_materialization_surface": (
            EXPANDED_MARKET_SOURCE_EXPANSION_WORK_TASK_MATERIALIZATION
        ),
        "research_boundary": research_boundary(),
    }
    write_json(RESULT_PATH, result)
    update_manifest(generated_at)
    replace_sprint_event(
        {
            "checkpoint": 273,
            "event": "checkpoint_273_expanded_market_source_expansion_work_task_materialization",
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
