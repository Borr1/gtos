#!/usr/bin/env python3
"""Build deconcentration replay rows from CP266 source-expansion execution."""

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

from src.research_infra.moonshot_expanded_market_proxy_r_performance import load_ohlc_rows
from src.research_infra.moonshot_expanded_market_source_expansion_deconcentration import (
    EXPANDED_MARKET_SOURCE_EXPANSION_DECONCENTRATION,
    aggregate_deconcentration_rows,
    boundary_row,
    preserved_noncomputable_row,
    research_boundary,
    scored_deconcentration_row,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_EXECUTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_DECONCENTRATION"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
INPUT_EXECUTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_EXECUTION_LEDGER_2026-05-17.jsonl"
INPUT_GAP_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SOURCE_GAP_PROOF_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_expanded_market_source_expansion_deconcentration.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_expanded_market_source_expansion_deconcentration_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
ROW_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
MONTH_LEDGER = ROUTE_DIR / f"{PREFIX}_MONTH_LEDGER_2026-05-17.jsonl"
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
        (RESULT_PATH, "expanded_market_source_expansion_deconcentration_result"),
        (ROW_LEDGER, "expanded_market_source_expansion_deconcentration_rows"),
        (MONTH_LEDGER, "expanded_market_source_expansion_deconcentration_month_rows"),
        (AGGREGATE_LEDGER, "expanded_market_source_expansion_deconcentration_aggregates"),
        (ISSUE_LEDGER, "expanded_market_source_expansion_deconcentration_issues"),
        (SYSTEM_LEDGER, "expanded_market_source_expansion_deconcentration_system"),
        (SUMMARY_PATH, "expanded_market_source_expansion_deconcentration_summary"),
        (BUILDER_MODULE, "expanded_market_source_expansion_deconcentration_builder"),
        (VERIFIER_MODULE, "expanded_market_source_expansion_deconcentration_verifier"),
        (HELPER_MODULE, "expanded_market_source_expansion_deconcentration_helper"),
        (TEST_MODULE, "expanded_market_source_expansion_deconcentration_tests"),
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
    manifest["latest_expanded_market_source_expansion_deconcentration"] = {
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
    marker = "## Checkpoint 267 - Expanded-Market Source Expansion Deconcentration"
    text = ACTIVE_LEDGER.read_text(encoding="utf-8", errors="replace") if ACTIVE_LEDGER.exists() else ""
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n\n"
    addition = f"""{marker}

Generated: {generated_at}

Trigger: direct continuation after Checkpoint 266. Source-expansion execution rows were replayed through month folds and dominant-month removal; gap and noncomputable rows were preserved.

Rows:
- input source-expansion execution rows: {counts["input_execution_rows"]}
- input source-gap proof rows: {counts["input_gap_rows"]}
- deconcentration rows: {counts["deconcentration_rows"]}
- deconcentration rows with simulated R: {counts["rows_with_deconcentrated_r"]}
- month fold rows: {counts["month_rows"]}
- aggregate rows: {counts["aggregate_rows"]}
- issue rows: {counts["issue_rows"]}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: use deconcentrated implement/avoid/kill/redesign rows for the next numeric replay or source-acquisition plate.
"""
    write_text(ACTIVE_LEDGER, text.rstrip() + "\n\n" + addition)


def build_summary(generated_at: str, counts: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Expanded-Market Source Expansion Deconcentration",
            "",
            f"Generated: {generated_at}",
            "",
            "This checkpoint replays CP266 alternate-source execution rows by month and removes the dominant month before assigning deconcentrated decisions. CP266 source-gap and noncomputable rows remain preserved.",
            "",
            "## Counts",
            "",
            f"- Input execution rows: `{counts['input_execution_rows']}`",
            f"- Input source-gap proof rows: `{counts['input_gap_rows']}`",
            f"- Deconcentration rows: `{counts['deconcentration_rows']}`",
            f"- Rows with deconcentrated simulated R: `{counts['rows_with_deconcentrated_r']}`",
            f"- Month fold rows: `{counts['month_rows']}`",
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
    input_result = read_json(INPUT_RESULT)
    source_cache: dict[str, list[dict[str, Any]]] = {}
    deconcentration_rows: list[dict[str, Any]] = []
    month_rows: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    input_execution_rows = 0
    input_gap_rows = 0
    decisions: Counter[str] = Counter()

    for execution in iter_jsonl(INPUT_EXECUTION_LEDGER):
        input_execution_rows += 1
        if execution.get("score_status") == "EXPANDED_MARKET_PROXY_R_SCORED":
            source_path = str(execution.get("source_expansion_candidate_source_path") or "")
            if source_path not in source_cache:
                source_cache[source_path], _ = load_ohlc_rows(REPO, source_path)
            row, row_months = scored_deconcentration_row(
                execution,
                source_cache[source_path],
                len(deconcentration_rows) + 1,
            )
            deconcentration_rows.append(row)
            month_rows.extend(row_months)
        else:
            deconcentration_rows.append(
                preserved_noncomputable_row(execution, len(deconcentration_rows) + 1, "execution")
            )
        decisions[deconcentration_rows[-1].get("keep_kill_redesign_implement_decision")] += 1

    for gap in iter_jsonl(INPUT_GAP_LEDGER):
        input_gap_rows += 1
        deconcentration_rows.append(
            preserved_noncomputable_row(gap, len(deconcentration_rows) + 1, "source_gap")
        )
        decisions[deconcentration_rows[-1].get("keep_kill_redesign_implement_decision")] += 1

    aggregate_rows = aggregate_deconcentration_rows(deconcentration_rows)
    counts = {
        "input_execution_rows": input_execution_rows,
        "input_gap_rows": input_gap_rows,
        "deconcentration_rows": len(deconcentration_rows),
        "rows_with_deconcentrated_r": sum(
            row.get("deconcentrated_cost_adjusted_simulated_r") is not None
            for row in deconcentration_rows
        ),
        "month_rows": len(month_rows),
        "aggregate_rows": len(aggregate_rows),
        "issue_rows": len(issues),
        "system_rows": 1,
        "source_path_count": len({row.get("source_path") for row in deconcentration_rows}),
        "symbol_count": len({row.get("symbol") for row in deconcentration_rows}),
        "decision_counts": dict(sorted(decisions.items())),
        "input_source_expansion_result_ok": input_result.get("ok"),
    }
    system_rows = [
        boundary_row(
            {
                "expanded_market_source_expansion_deconcentration_system_row_id": (
                    "OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-DECONC-SYSTEM-0001"
                ),
                **counts,
                "metadata": {
                    "input_execution_ledger": str(INPUT_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
                    "input_gap_ledger": str(INPUT_GAP_LEDGER.relative_to(REPO)).replace("\\", "/"),
                    "no_top_n_cutoff": True,
                },
            }
        )
    ]
    output_files = [ROW_LEDGER, MONTH_LEDGER, AGGREGATE_LEDGER, ISSUE_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]
    write_jsonl(ROW_LEDGER, deconcentration_rows)
    write_jsonl(MONTH_LEDGER, month_rows)
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
            "source_expansion_result": str(INPUT_RESULT.relative_to(REPO)).replace("\\", "/"),
            "source_expansion_execution_ledger": str(INPUT_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "source_gap_proof_ledger": str(INPUT_GAP_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "row_ledger": str(ROW_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "month_ledger": str(MONTH_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "issue_ledger": str(ISSUE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
        "output_sha256": output_sha256(output_files),
        "expanded_market_source_expansion_deconcentration_surface": (
            EXPANDED_MARKET_SOURCE_EXPANSION_DECONCENTRATION
        ),
        "research_boundary": research_boundary(),
    }
    write_json(RESULT_PATH, result)
    update_manifest(generated_at)
    replace_sprint_event(
        {
            "checkpoint": 267,
            "event": "checkpoint_267_expanded_market_source_expansion_deconcentration",
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
