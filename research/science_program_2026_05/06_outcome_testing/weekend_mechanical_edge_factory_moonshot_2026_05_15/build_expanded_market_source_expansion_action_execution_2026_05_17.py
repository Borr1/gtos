#!/usr/bin/env python3
"""Build monthly action-execution rows from CP267 deconcentrated source expansion."""

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

from src.research_infra.moonshot_expanded_market_source_expansion_action_execution import (
    EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_EXECUTION,
    action_execution_row,
    aggregate_action_rows,
    boundary_row,
    research_boundary,
)


DECON_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_DECONCENTRATION"
SOURCE_EXEC_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_EXECUTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_EXECUTION"

DECON_RESULT = ROUTE_DIR / f"{DECON_PREFIX}_RESULT_2026-05-17.json"
DECON_ROW_LEDGER = ROUTE_DIR / f"{DECON_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
DECON_MONTH_LEDGER = ROUTE_DIR / f"{DECON_PREFIX}_MONTH_LEDGER_2026-05-17.jsonl"
SOURCE_EXECUTION_LEDGER = ROUTE_DIR / f"{SOURCE_EXEC_PREFIX}_EXECUTION_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_expanded_market_source_expansion_action_execution.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_expanded_market_source_expansion_action_execution_2026_05_17.py"
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
        (RESULT_PATH, "expanded_market_source_expansion_action_execution_result"),
        (ROW_LEDGER, "expanded_market_source_expansion_action_execution_rows"),
        (AGGREGATE_LEDGER, "expanded_market_source_expansion_action_execution_aggregates"),
        (ISSUE_LEDGER, "expanded_market_source_expansion_action_execution_issues"),
        (SYSTEM_LEDGER, "expanded_market_source_expansion_action_execution_system"),
        (SUMMARY_PATH, "expanded_market_source_expansion_action_execution_summary"),
        (BUILDER_MODULE, "expanded_market_source_expansion_action_execution_builder"),
        (VERIFIER_MODULE, "expanded_market_source_expansion_action_execution_verifier"),
        (HELPER_MODULE, "expanded_market_source_expansion_action_execution_helper"),
        (TEST_MODULE, "expanded_market_source_expansion_action_execution_tests"),
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
    manifest["latest_expanded_market_source_expansion_action_execution"] = {
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
    marker = "## Checkpoint 268 - Expanded-Market Source Expansion Action Execution"
    text = ACTIVE_LEDGER.read_text(encoding="utf-8", errors="replace") if ACTIVE_LEDGER.exists() else ""
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n\n"
    addition = f"""{marker}

Generated: {generated_at}

Trigger: direct continuation after Checkpoint 267. Deconcentrated source-expansion rows were executed into month-stability action rows with original proxy geometry joined where available.

Rows:
- input deconcentration rows: {counts["input_deconcentration_rows"]}
- source execution rows joined: {counts["source_execution_rows_joined"]}
- action execution rows: {counts["action_execution_rows"]}
- rows with simulated R: {counts["rows_with_simulated_r"]}
- aggregate rows: {counts["aggregate_rows"]}
- issue rows: {counts["issue_rows"]}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: consume month-stable action rows into branch-local scorer/avoid/kill artifacts and keep source-gap rows as row-level acquisition proof.
"""
    write_text(ACTIVE_LEDGER, text.rstrip() + "\n\n" + addition)


def build_summary(generated_at: str, counts: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Expanded-Market Source Expansion Action Execution",
            "",
            f"Generated: {generated_at}",
            "",
            "This checkpoint consumes every CP267 deconcentration row into an action-execution row. Actionable rows are checked against month-fold stability; source-gap and noncomputable rows retain exact missing-field proof.",
            "",
            "## Counts",
            "",
            f"- Input deconcentration rows: `{counts['input_deconcentration_rows']}`",
            f"- Source execution rows joined: `{counts['source_execution_rows_joined']}`",
            f"- Action execution rows: `{counts['action_execution_rows']}`",
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
    decon_result = read_json(DECON_RESULT)
    source_execution_by_id = {
        str(row.get("expanded_market_source_expansion_execution_row_id") or ""): row
        for row in iter_jsonl(SOURCE_EXECUTION_LEDGER)
    }
    month_rows_by_execution_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for month_row in iter_jsonl(DECON_MONTH_LEDGER):
        month_rows_by_execution_id[str(month_row.get("input_source_expansion_execution_row_id") or "")].append(
            month_row
        )

    action_rows: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    joined_source_execution_ids: set[str] = set()
    decisions: Counter[str] = Counter()
    input_rows = 0
    for decon_row in iter_jsonl(DECON_ROW_LEDGER):
        input_rows += 1
        source_execution_id = str(decon_row.get("input_source_expansion_execution_row_id") or "")
        source_execution = source_execution_by_id.get(source_execution_id)
        if source_execution:
            joined_source_execution_ids.add(source_execution_id)
        action = action_execution_row(
            decon_row,
            source_execution,
            month_rows_by_execution_id.get(source_execution_id, []),
            len(action_rows) + 1,
        )
        action_rows.append(action)
        decisions[action.get("keep_kill_redesign_implement_decision")] += 1

    aggregate_rows = aggregate_action_rows(action_rows)
    counts = {
        "input_deconcentration_rows": input_rows,
        "source_execution_rows_joined": len(joined_source_execution_ids),
        "action_execution_rows": len(action_rows),
        "rows_with_simulated_r": sum(row.get("cost_adjusted_simulated_r") is not None for row in action_rows),
        "aggregate_rows": len(aggregate_rows),
        "issue_rows": len(issues),
        "system_rows": 1,
        "source_path_count": len({row.get("source_path") for row in action_rows}),
        "symbol_count": len({row.get("symbol") for row in action_rows}),
        "decision_counts": dict(sorted(decisions.items())),
        "input_deconcentration_result_ok": decon_result.get("ok"),
    }
    system_rows = [
        boundary_row(
            {
                "expanded_market_source_expansion_action_execution_system_row_id": (
                    "OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-ACTION-SYSTEM-0001"
                ),
                **counts,
                "metadata": {
                    "deconcentration_row_ledger": str(DECON_ROW_LEDGER.relative_to(REPO)).replace("\\", "/"),
                    "deconcentration_month_ledger": str(DECON_MONTH_LEDGER.relative_to(REPO)).replace("\\", "/"),
                    "source_execution_ledger": str(SOURCE_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
                    "no_top_n_cutoff": True,
                },
            }
        )
    ]
    output_files = [ROW_LEDGER, AGGREGATE_LEDGER, ISSUE_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]
    write_jsonl(ROW_LEDGER, action_rows)
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
            "deconcentration_result": str(DECON_RESULT.relative_to(REPO)).replace("\\", "/"),
            "deconcentration_row_ledger": str(DECON_ROW_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "deconcentration_month_ledger": str(DECON_MONTH_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "source_execution_ledger": str(SOURCE_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "row_ledger": str(ROW_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "issue_ledger": str(ISSUE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
        "output_sha256": output_sha256(output_files),
        "expanded_market_source_expansion_action_execution_surface": (
            EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_EXECUTION
        ),
        "research_boundary": research_boundary(),
    }
    write_json(RESULT_PATH, result)
    update_manifest(generated_at)
    replace_sprint_event(
        {
            "checkpoint": 268,
            "event": "checkpoint_268_expanded_market_source_expansion_action_execution",
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
