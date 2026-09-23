#!/usr/bin/env python3
"""Execute source-expansion rule candidates against held work-resolution rows."""

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

from src.research_infra.moonshot_expanded_market_source_expansion_rule_candidate_execution import (
    EXPANDED_MARKET_SOURCE_EXPANSION_RULE_CANDIDATE_EXECUTION,
    aggregate_rule_execution_rows,
    boundary_row,
    replay_task_execution_row,
    research_boundary,
    rule_candidate_execution_row,
    rule_match_rows,
    source_task_execution_row,
)


TASK_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_WORK_TASK_MATERIALIZATION"
WORK_RES_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_PACK_WORK_RESOLUTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_RULE_CANDIDATE_EXECUTION"

TASK_RESULT = ROUTE_DIR / f"{TASK_PREFIX}_RESULT_2026-05-17.json"
RULE_LEDGER = ROUTE_DIR / f"{TASK_PREFIX}_RULE_CANDIDATE_LEDGER_2026-05-17.jsonl"
REPLAY_TASK_LEDGER = ROUTE_DIR / f"{TASK_PREFIX}_REPLAY_TASK_LEDGER_2026-05-17.jsonl"
SOURCE_TASK_LEDGER = ROUTE_DIR / f"{TASK_PREFIX}_SOURCE_TASK_LEDGER_2026-05-17.jsonl"
WORK_RES_ROW_LEDGER = ROUTE_DIR / f"{WORK_RES_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_expanded_market_source_expansion_rule_candidate_execution.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_expanded_market_source_expansion_rule_candidate_execution_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
RULE_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_RULE_EXECUTION_LEDGER_2026-05-17.jsonl"
MATCH_LEDGER = ROUTE_DIR / f"{PREFIX}_MATCH_LEDGER_2026-05-17.jsonl"
REPLAY_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_REPLAY_TASK_EXECUTION_LEDGER_2026-05-17.jsonl"
SOURCE_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_TASK_EXECUTION_LEDGER_2026-05-17.jsonl"
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
        (RESULT_PATH, "expanded_market_source_expansion_rule_candidate_execution_result"),
        (RULE_EXECUTION_LEDGER, "expanded_market_source_expansion_rule_candidate_execution_rows"),
        (MATCH_LEDGER, "expanded_market_source_expansion_rule_candidate_match_rows"),
        (REPLAY_EXECUTION_LEDGER, "expanded_market_source_expansion_replay_task_execution_rows"),
        (SOURCE_EXECUTION_LEDGER, "expanded_market_source_expansion_source_task_execution_rows"),
        (AGGREGATE_LEDGER, "expanded_market_source_expansion_rule_candidate_execution_aggregates"),
        (ISSUE_LEDGER, "expanded_market_source_expansion_rule_candidate_execution_issues"),
        (SYSTEM_LEDGER, "expanded_market_source_expansion_rule_candidate_execution_system"),
        (SUMMARY_PATH, "expanded_market_source_expansion_rule_candidate_execution_summary"),
        (BUILDER_MODULE, "expanded_market_source_expansion_rule_candidate_execution_builder"),
        (VERIFIER_MODULE, "expanded_market_source_expansion_rule_candidate_execution_verifier"),
        (HELPER_MODULE, "expanded_market_source_expansion_rule_candidate_execution_helper"),
        (TEST_MODULE, "expanded_market_source_expansion_rule_candidate_execution_tests"),
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
    manifest["latest_expanded_market_source_expansion_rule_candidate_execution"] = {
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
    marker = "## Checkpoint 274 - Expanded-Market Source Expansion Rule Candidate Execution"
    text = ACTIVE_LEDGER.read_text(encoding="utf-8", errors="replace") if ACTIVE_LEDGER.exists() else ""
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n\n"
    addition = f"""{marker}

Generated: {generated_at}

Trigger: direct continuation after Checkpoint 273. Rule candidates were executed against every CP272 work-resolution row with negative mismatch scans; replay and source task rows were preserved as execution rows.

Rows:
- work-resolution rows scanned per candidate: {counts["candidate_work_resolution_rows"]}
- rule candidate execution rows: {counts["rule_candidate_execution_rows"]}
- rule match rows: {counts["match_rows"]}
- replay task execution rows: {counts["replay_task_execution_rows"]}
- source task execution rows: {counts["source_task_execution_rows"]}
- aggregate rows: {counts["aggregate_rows"]}
- issue rows: {counts["issue_rows"]}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: collapse passing rule-execution rows into branch-local research bundles and keep replay/source task execution rows as concrete implementation inputs.
"""
    write_text(ACTIVE_LEDGER, text.rstrip() + "\n\n" + addition)


def build_summary(generated_at: str, counts: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Expanded-Market Source Expansion Rule Candidate Execution",
            "",
            f"Generated: {generated_at}",
            "",
            "This checkpoint executes CP273 rule candidates against every CP272 work-resolution row and preserves replay/source task execution rows.",
            "",
            f"- Work-resolution rows scanned per candidate: `{counts['candidate_work_resolution_rows']}`",
            f"- Rule candidate execution rows: `{counts['rule_candidate_execution_rows']}`",
            f"- Rule match rows: `{counts['match_rows']}`",
            f"- Replay task execution rows: `{counts['replay_task_execution_rows']}`",
            f"- Source task execution rows: `{counts['source_task_execution_rows']}`",
            f"- Issue rows: `{counts['issue_rows']}`",
            "",
        ]
    )


def main() -> None:
    generated_at = now_utc()
    task_result = read_json(TASK_RESULT)
    work_rows = list(iter_jsonl(WORK_RES_ROW_LEDGER))
    work_rows_by_id = {
        str(row.get("expanded_market_source_expansion_action_pack_work_resolution_row_id") or ""): row
        for row in work_rows
    }
    rule_rows = list(iter_jsonl(RULE_LEDGER))
    replay_tasks = list(iter_jsonl(REPLAY_TASK_LEDGER))
    source_tasks = list(iter_jsonl(SOURCE_TASK_LEDGER))
    rule_execution_rows: list[dict[str, Any]] = []
    match_rows: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []

    for candidate in rule_rows:
        execution = rule_candidate_execution_row(candidate, work_rows, len(rule_execution_rows) + 1)
        rule_execution_rows.append(execution)
        match_rows.extend(rule_match_rows(candidate, execution, work_rows_by_id, len(match_rows) + 1))
        if execution.get("rule_candidate_execution_status") != "SOURCE_EXPANSION_RULE_CANDIDATE_EXECUTION_PASS":
            issues.append(
                boundary_row(
                    {
                        "expanded_market_source_expansion_rule_candidate_execution_issue_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-RULE-CAND-EXEC-ISSUE-{len(issues) + 1:07d}"
                        ),
                        "issue_type": "RULE_CANDIDATE_EXECUTION_REPAIR_REQUIRED",
                        "input_rule_candidate_row_id": candidate.get(
                            "expanded_market_source_expansion_rule_candidate_row_id"
                        ),
                        "match_count": execution.get("match_count"),
                        "cost_mismatch_count": execution.get("cost_mismatch_count"),
                    }
                )
            )

    replay_execution_rows = [
        replay_task_execution_row(row, index + 1) for index, row in enumerate(replay_tasks)
    ]
    source_execution_rows = [
        source_task_execution_row(row, index + 1) for index, row in enumerate(source_tasks)
    ]
    aggregates = aggregate_rule_execution_rows(
        rule_execution_rows, replay_execution_rows, source_execution_rows
    )
    status_counts = Counter(row.get("rule_candidate_execution_status") for row in rule_execution_rows)
    counts = {
        "input_task_result_ok": task_result.get("ok"),
        "candidate_work_resolution_rows": len(work_rows),
        "input_rule_candidate_rows": len(rule_rows),
        "rule_candidate_execution_rows": len(rule_execution_rows),
        "rule_candidate_execution_pass_rows": status_counts.get(
            "SOURCE_EXPANSION_RULE_CANDIDATE_EXECUTION_PASS", 0
        ),
        "match_rows": len(match_rows),
        "replay_task_execution_rows": len(replay_execution_rows),
        "source_task_execution_rows": len(source_execution_rows),
        "aggregate_rows": len(aggregates),
        "issue_rows": len(issues),
        "system_rows": 1,
        "total_negative_mismatch_scans": sum(
            int(row.get("negative_mismatch_count") or 0) for row in rule_execution_rows
        ),
        "execution_status_counts": dict(sorted(status_counts.items())),
    }
    system_rows = [
        boundary_row(
            {
                "expanded_market_source_expansion_rule_candidate_execution_system_row_id": (
                    "OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-RULE-CAND-EXEC-SYSTEM-0001"
                ),
                **counts,
                "metadata": {
                    "rule_candidate_ledger": str(RULE_LEDGER.relative_to(REPO)).replace("\\", "/"),
                    "work_resolution_ledger": str(WORK_RES_ROW_LEDGER.relative_to(REPO)).replace("\\", "/"),
                    "no_top_n_cutoff": True,
                },
            }
        )
    ]
    output_files = [
        RULE_EXECUTION_LEDGER,
        MATCH_LEDGER,
        REPLAY_EXECUTION_LEDGER,
        SOURCE_EXECUTION_LEDGER,
        AGGREGATE_LEDGER,
        ISSUE_LEDGER,
        SYSTEM_LEDGER,
        SUMMARY_PATH,
    ]
    write_jsonl(RULE_EXECUTION_LEDGER, rule_execution_rows)
    write_jsonl(MATCH_LEDGER, match_rows)
    write_jsonl(REPLAY_EXECUTION_LEDGER, replay_execution_rows)
    write_jsonl(SOURCE_EXECUTION_LEDGER, source_execution_rows)
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
            "task_result": str(TASK_RESULT.relative_to(REPO)).replace("\\", "/"),
            "rule_candidate_ledger": str(RULE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "replay_task_ledger": str(REPLAY_TASK_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "source_task_ledger": str(SOURCE_TASK_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "work_resolution_ledger": str(WORK_RES_ROW_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "rule_execution_ledger": str(RULE_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "match_ledger": str(MATCH_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "replay_task_execution_ledger": str(REPLAY_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "source_task_execution_ledger": str(SOURCE_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "issue_ledger": str(ISSUE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
        "output_sha256": output_sha256(output_files),
        "expanded_market_source_expansion_rule_candidate_execution_surface": (
            EXPANDED_MARKET_SOURCE_EXPANSION_RULE_CANDIDATE_EXECUTION
        ),
        "research_boundary": research_boundary(),
    }
    write_json(RESULT_PATH, result)
    update_manifest(generated_at)
    replace_sprint_event(
        {
            "checkpoint": 274,
            "event": "checkpoint_274_expanded_market_source_expansion_rule_candidate_execution",
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
