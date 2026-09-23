#!/usr/bin/env python3
"""Build action-application rows from month-stable expanded-market actions."""

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

from src.research_infra.moonshot_expanded_market_source_expansion_action_application import (
    EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_APPLICATION,
    action_rule_row,
    aggregate_application_rows,
    boundary_row,
    exact_scope_from_execution,
    family_scope_from_execution,
    is_actionable_decision,
    research_boundary,
    rule_self_test_row,
    select_family_rule,
    source_gap_application_row,
    execution_application_row,
)


ACTION_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_EXECUTION"
SOURCE_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_EXECUTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_APPLICATION"

ACTION_RESULT = ROUTE_DIR / f"{ACTION_PREFIX}_RESULT_2026-05-17.json"
ACTION_ROW_LEDGER = ROUTE_DIR / f"{ACTION_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
SOURCE_EXECUTION_LEDGER = ROUTE_DIR / f"{SOURCE_PREFIX}_EXECUTION_LEDGER_2026-05-17.jsonl"
SOURCE_GAP_LEDGER = ROUTE_DIR / f"{SOURCE_PREFIX}_SOURCE_GAP_PROOF_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_expanded_market_source_expansion_action_application.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_expanded_market_source_expansion_action_application_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
ROW_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
RULE_LEDGER = ROUTE_DIR / f"{PREFIX}_RULE_LEDGER_2026-05-17.jsonl"
SELF_TEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SELF_TEST_LEDGER_2026-05-17.jsonl"
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
        (RESULT_PATH, "expanded_market_source_expansion_action_application_result"),
        (ROW_LEDGER, "expanded_market_source_expansion_action_application_rows"),
        (RULE_LEDGER, "expanded_market_source_expansion_action_application_rules"),
        (SELF_TEST_LEDGER, "expanded_market_source_expansion_action_application_self_tests"),
        (AGGREGATE_LEDGER, "expanded_market_source_expansion_action_application_aggregates"),
        (ISSUE_LEDGER, "expanded_market_source_expansion_action_application_issues"),
        (SYSTEM_LEDGER, "expanded_market_source_expansion_action_application_system"),
        (SUMMARY_PATH, "expanded_market_source_expansion_action_application_summary"),
        (BUILDER_MODULE, "expanded_market_source_expansion_action_application_builder"),
        (VERIFIER_MODULE, "expanded_market_source_expansion_action_application_verifier"),
        (HELPER_MODULE, "expanded_market_source_expansion_action_application_helper"),
        (TEST_MODULE, "expanded_market_source_expansion_action_application_tests"),
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
    manifest["latest_expanded_market_source_expansion_action_application"] = {
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
    marker = "## Checkpoint 269 - Expanded-Market Source Expansion Action Application"
    text = ACTIVE_LEDGER.read_text(encoding="utf-8", errors="replace") if ACTIVE_LEDGER.exists() else ""
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n\n"
    addition = f"""{marker}

Generated: {generated_at}

Trigger: direct continuation after Checkpoint 268. Month-stable source-expansion actions were compiled into deterministic branch-local rules and applied across every CP266 execution row, with source-gap proof preserved row by row.

Rows:
- source execution rows consumed: {counts["source_execution_rows"]}
- source gap rows consumed: {counts["source_gap_rows"]}
- action rules compiled: {counts["action_rule_rows"]}
- action application rows: {counts["action_application_rows"]}
- applied action rows: {counts["applied_action_rows"]}
- rows with simulated R: {counts["rows_with_simulated_r"]}
- aggregate rows: {counts["aggregate_rows"]}
- issue rows: {counts["issue_rows"]}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: use applied implement/avoid/kill rows as concrete research-only branch-local action packs and preserve unmatched/source-gap rows as exact source/replay work.
"""
    write_text(ACTIVE_LEDGER, text.rstrip() + "\n\n" + addition)


def build_summary(generated_at: str, counts: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Expanded-Market Source Expansion Action Application",
            "",
            f"Generated: {generated_at}",
            "",
            "This checkpoint compiles CP268 month-stable actions into branch-local rules and applies them across all CP266 source-expansion execution rows. Source-gap rows remain exact row-level replay/source proof.",
            "",
            "## Counts",
            "",
            f"- Source execution rows consumed: `{counts['source_execution_rows']}`",
            f"- Source gap rows consumed: `{counts['source_gap_rows']}`",
            f"- Action rules compiled: `{counts['action_rule_rows']}`",
            f"- Action application rows: `{counts['action_application_rows']}`",
            f"- Applied action rows: `{counts['applied_action_rows']}`",
            f"- Rows with simulated R: `{counts['rows_with_simulated_r']}`",
            f"- Aggregate rows: `{counts['aggregate_rows']}`",
            f"- Issue rows: `{counts['issue_rows']}`",
            "",
            "## Decisions",
            "",
            f"`{json.dumps(counts['decision_counts'], sort_keys=True)}`",
            "",
        ]
    )


def main() -> None:
    generated_at = now_utc()
    action_result = read_json(ACTION_RESULT)
    rule_rows: list[dict[str, Any]] = []
    for action_row in iter_jsonl(ACTION_ROW_LEDGER):
        decision = str(action_row.get("keep_kill_redesign_implement_decision") or "")
        if is_actionable_decision(decision):
            rule_rows.append(action_rule_row(action_row, len(rule_rows) + 1))

    exact_rules: dict[tuple[str, ...], dict[str, Any]] = {}
    family_rules: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for rule in rule_rows:
        exact_key = tuple(rule["rule_expression"]["exact_scope"])
        if exact_key not in exact_rules:
            exact_rules[exact_key] = rule
        family_rules[tuple(rule["rule_expression"]["family_scope"])].append(rule)

    application_rows: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    rule_application_counts: Counter[str] = Counter()
    source_execution_rows = 0
    status_counts: Counter[str] = Counter()

    for execution in iter_jsonl(SOURCE_EXECUTION_LEDGER):
        source_execution_rows += 1
        exact_rule = exact_rules.get(exact_scope_from_execution(execution))
        family_scope_rules = family_rules.get(family_scope_from_execution(execution), [])
        if exact_rule is not None:
            status = "ACTION_APPLICATION_EXACT_RULE_APPLIED"
            selected_rule = exact_rule
        else:
            selected_rule, family_status = select_family_rule(family_scope_rules)
            if family_status == "FAMILY_SCOPE_UNANIMOUS":
                status = "ACTION_APPLICATION_SCOPE_RULE_APPLIED"
            elif family_status == "FAMILY_SCOPE_CONFLICT":
                status = "ACTION_APPLICATION_SCOPE_CONFLICT_PRESERVED"
            else:
                status = "ACTION_APPLICATION_NO_MONTH_STABLE_RULE"
        app_row = execution_application_row(
            execution,
            selected_rule,
            status,
            len(application_rows) + 1,
            len(family_scope_rules),
        )
        application_rows.append(app_row)
        status_counts[status] += 1
        if selected_rule is not None:
            rule_application_counts[
                selected_rule["expanded_market_source_expansion_action_application_rule_row_id"]
            ] += 1

    source_gap_rows = 0
    for gap in iter_jsonl(SOURCE_GAP_LEDGER):
        source_gap_rows += 1
        app_row = source_gap_application_row(gap, len(application_rows) + 1)
        application_rows.append(app_row)
        status_counts[app_row["action_application_status"]] += 1

    self_test_rows = [
        rule_self_test_row(
            rule,
            rule_application_counts.get(
                rule["expanded_market_source_expansion_action_application_rule_row_id"], 0
            ),
            index + 1,
        )
        for index, rule in enumerate(rule_rows)
    ]
    issues.extend(
        boundary_row(
            {
                "expanded_market_source_expansion_action_application_issue_row_id": (
                    f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-ACTION-APP-ISSUE-{index + 1:07d}"
                ),
                "issue_type": "ACTION_APPLICATION_RULE_WITHOUT_SOURCE_EXECUTION_MATCH",
                "input_action_application_rule_row_id": rule.get(
                    "expanded_market_source_expansion_action_application_rule_row_id"
                ),
                "keep_kill_redesign_implement_decision": rule.get(
                    "keep_kill_redesign_implement_decision"
                ),
            }
        )
        for index, rule in enumerate(rule_rows)
        if rule_application_counts.get(
            rule["expanded_market_source_expansion_action_application_rule_row_id"], 0
        )
        == 0
    )

    aggregate_rows = aggregate_application_rows(application_rows)
    decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in application_rows)
    counts = {
        "input_action_result_ok": action_result.get("ok"),
        "source_execution_rows": source_execution_rows,
        "source_gap_rows": source_gap_rows,
        "action_rule_rows": len(rule_rows),
        "action_application_rows": len(application_rows),
        "applied_action_rows": sum(
            count
            for status, count in status_counts.items()
            if status in {"ACTION_APPLICATION_EXACT_RULE_APPLIED", "ACTION_APPLICATION_SCOPE_RULE_APPLIED"}
        ),
        "exact_applied_action_rows": status_counts.get("ACTION_APPLICATION_EXACT_RULE_APPLIED", 0),
        "scope_applied_action_rows": status_counts.get("ACTION_APPLICATION_SCOPE_RULE_APPLIED", 0),
        "scope_conflict_rows": status_counts.get("ACTION_APPLICATION_SCOPE_CONFLICT_PRESERVED", 0),
        "no_month_stable_rule_rows": status_counts.get("ACTION_APPLICATION_NO_MONTH_STABLE_RULE", 0),
        "source_gap_preserved_rows": status_counts.get("ACTION_APPLICATION_SOURCE_GAP_PRESERVED", 0),
        "rows_with_simulated_r": sum(row.get("cost_adjusted_simulated_r") is not None for row in application_rows),
        "aggregate_rows": len(aggregate_rows),
        "self_test_rows": len(self_test_rows),
        "self_test_pass_rows": sum(
            row.get("self_test_status") == "ACTION_APPLICATION_RULE_SELF_TEST_PASS"
            for row in self_test_rows
        ),
        "issue_rows": len(issues),
        "system_rows": 1,
        "symbol_count": len({row.get("symbol") for row in application_rows}),
        "source_path_count": len({row.get("source_path") for row in application_rows}),
        "status_counts": dict(sorted(status_counts.items())),
        "decision_counts": dict(sorted(decisions.items())),
    }

    system_rows = [
        boundary_row(
            {
                "expanded_market_source_expansion_action_application_system_row_id": (
                    "OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-ACTION-APP-SYSTEM-0001"
                ),
                **counts,
                "metadata": {
                    "action_row_ledger": str(ACTION_ROW_LEDGER.relative_to(REPO)).replace("\\", "/"),
                    "source_execution_ledger": str(SOURCE_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
                    "source_gap_ledger": str(SOURCE_GAP_LEDGER.relative_to(REPO)).replace("\\", "/"),
                    "no_top_n_cutoff": True,
                },
            }
        )
    ]

    output_files = [
        ROW_LEDGER,
        RULE_LEDGER,
        SELF_TEST_LEDGER,
        AGGREGATE_LEDGER,
        ISSUE_LEDGER,
        SYSTEM_LEDGER,
        SUMMARY_PATH,
    ]
    write_jsonl(ROW_LEDGER, application_rows)
    write_jsonl(RULE_LEDGER, rule_rows)
    write_jsonl(SELF_TEST_LEDGER, self_test_rows)
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
            "action_result": str(ACTION_RESULT.relative_to(REPO)).replace("\\", "/"),
            "action_row_ledger": str(ACTION_ROW_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "source_execution_ledger": str(SOURCE_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "source_gap_ledger": str(SOURCE_GAP_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "row_ledger": str(ROW_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "rule_ledger": str(RULE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "self_test_ledger": str(SELF_TEST_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "issue_ledger": str(ISSUE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
        "output_sha256": output_sha256(output_files),
        "expanded_market_source_expansion_action_application_surface": (
            EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_APPLICATION
        ),
        "research_boundary": research_boundary(),
    }
    write_json(RESULT_PATH, result)
    update_manifest(generated_at)
    replace_sprint_event(
        {
            "checkpoint": 269,
            "event": "checkpoint_269_expanded_market_source_expansion_action_application",
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
