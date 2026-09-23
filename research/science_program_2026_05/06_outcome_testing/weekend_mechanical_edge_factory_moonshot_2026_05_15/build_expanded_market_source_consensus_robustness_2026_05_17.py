#!/usr/bin/env python3
"""Build source-consensus robustness rows from combined expanded-market performance."""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_expanded_market_source_consensus_robustness import (
    EXPANDED_MARKET_SOURCE_CONSENSUS_ROBUSTNESS_SURFACE,
    aggregate_consensus_rows,
    research_boundary,
    source_consensus_rows,
    system_source_consensus_rows,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SUPPLEMENTAL_SOURCE_PERFORMANCE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_CONSENSUS_ROBUSTNESS"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
INPUT_PERFORMANCE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_expanded_market_source_consensus_robustness.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_expanded_market_source_consensus_robustness_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
CONSENSUS_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
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


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with open(long_path(path), "r", encoding="utf-8", errors="replace") as handle:
        return [json.loads(line) for line in handle if line.strip()]


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


def update_manifest(generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    entries = [
        (RESULT_PATH, "expanded_market_source_consensus_robustness_result"),
        (CONSENSUS_LEDGER, "expanded_market_source_consensus_rows"),
        (AGGREGATE_LEDGER, "expanded_market_source_consensus_aggregates"),
        (ISSUE_LEDGER, "expanded_market_source_consensus_issues"),
        (SYSTEM_LEDGER, "expanded_market_source_consensus_system"),
        (SUMMARY_PATH, "expanded_market_source_consensus_summary"),
        (BUILDER_MODULE, "expanded_market_source_consensus_builder"),
        (VERIFIER_MODULE, "expanded_market_source_consensus_verifier"),
        (HELPER_MODULE, "expanded_market_source_consensus_helper"),
        (TEST_MODULE, "expanded_market_source_consensus_tests"),
    ]
    rows = [
        {"path": str(path.relative_to(REPO)).replace("\\", "/"), "status": "created", "type": kind}
        for path, kind in entries
    ]
    existing = manifest.setdefault("artifacts", [])
    keys = {(row["path"], row["type"]) for row in rows}
    manifest["artifacts"] = [row for row in existing if (row.get("path"), row.get("type")) not in keys] + rows
    manifest["latest_expanded_market_source_consensus_robustness"] = {
        "generated_utc": generated_at,
        "files": rows,
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
    marker = "## Checkpoint 247 - Expanded-Market Source Consensus Robustness"
    text = ACTIVE_LEDGER.read_text(encoding="utf-8", errors="replace") if ACTIVE_LEDGER.exists() else ""
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n\n"
    addition = f"""{marker}

Generated: {generated_at}

Trigger: direct continuation after Checkpoint 246. The combined expanded-market performance rows were converted into row-preserving source-consensus robustness rows by symbol family, timeframe, session, horizon, and side.

Rows:
- input combined performance rows: {counts["input_combined_performance_rows"]}
- source-consensus rows: {counts["source_consensus_rows"]}
- aggregate rows: {counts["aggregate_rows"]}
- issue rows: {counts["issue_rows"]}
- rows with simulated R: {counts["rows_with_simulated_r"]}
- symbol families: {counts["symbol_family_count"]}
- source paths: {counts["source_path_count"]}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: use source-consensus rows to drive the next numeric repair, deconcentration, or implementation-selection plate; preserve every row and do not return to wrapper-only work.
"""
    write_text(ACTIVE_LEDGER, text.rstrip() + "\n\n" + addition)


def build_summary(generated_at: str, counts: dict[str, Any], result: dict[str, Any]) -> str:
    decisions = "\n".join(f"- {key}: {value}" for key, value in sorted((counts.get("decision_counts") or {}).items()))
    classes = "\n".join(f"- {key}: {value}" for key, value in sorted((counts.get("class_counts") or {}).items()))
    return f"""# Expanded-Market Source Consensus Robustness

Generated: {generated_at}

## Inputs

- Combined performance rows: `{counts["input_combined_performance_rows"]}`

## Outputs

- Source-consensus rows: `{counts["source_consensus_rows"]}`
- Aggregate rows: `{counts["aggregate_rows"]}`
- Issue rows: `{counts["issue_rows"]}`
- Rows with simulated R: `{counts["rows_with_simulated_r"]}`
- Symbol families: `{counts["symbol_family_count"]}`
- Source paths: `{counts["source_path_count"]}`

## Decisions

{decisions}

## Classes

{classes}

## Boundary

Branch-local research artifact only. The run wrote no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path.

## Result

- ok: `{result["ok"]}`
- issues: `{result["issues"]}`
"""


def main() -> None:
    generated_at = now_utc()
    input_result = read_json(INPUT_RESULT)
    input_rows = read_jsonl(INPUT_PERFORMANCE_LEDGER)
    consensus_rows, issue_rows = source_consensus_rows(input_rows)
    aggregate_rows = aggregate_consensus_rows(consensus_rows)
    metadata = {
        "input_supplemental_ok": input_result.get("ok"),
        "input_combined_performance_rows": len(input_rows),
    }
    system_rows = system_source_consensus_rows(consensus_rows, aggregate_rows, issue_rows, metadata)
    counts = {
        "input_combined_performance_rows": len(input_rows),
        "source_consensus_rows": len(consensus_rows),
        "aggregate_rows": len(aggregate_rows),
        "issue_rows": len(issue_rows),
        "rows_with_simulated_r": sum(1 for row in consensus_rows if not row.get("missing_simulated_fields")),
        "symbol_family_count": len({row.get("symbol_family") for row in consensus_rows}),
        "source_path_count": len({row.get("source_path") for row in consensus_rows}),
        "source_family_count": len({row.get("performance_source_family") for row in consensus_rows}),
        "decision_counts": system_rows[0].get("decision_counts"),
        "class_counts": system_rows[0].get("class_counts"),
        "system_rows": len(system_rows),
    }
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "ok": True,
        "issues": [],
        "expanded_market_source_consensus_robustness_surface": (
            EXPANDED_MARKET_SOURCE_CONSENSUS_ROBUSTNESS_SURFACE
        ),
        "research_boundary": research_boundary(),
        "inputs": {
            "supplemental_source_performance_result": str(INPUT_RESULT.relative_to(REPO)).replace("\\", "/"),
            "supplemental_source_performance_rows": str(INPUT_PERFORMANCE_LEDGER.relative_to(REPO)).replace(
                "\\", "/"
            ),
        },
        "outputs": {
            "source_consensus_ledger": str(CONSENSUS_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "issue_ledger": str(ISSUE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
        "counts": counts,
    }

    write_jsonl(CONSENSUS_LEDGER, consensus_rows)
    write_jsonl(AGGREGATE_LEDGER, aggregate_rows)
    write_jsonl(ISSUE_LEDGER, issue_rows)
    write_jsonl(SYSTEM_LEDGER, system_rows)
    write_text(SUMMARY_PATH, build_summary(generated_at, counts, result))
    result["output_sha256"] = output_sha256(
        [CONSENSUS_LEDGER, AGGREGATE_LEDGER, ISSUE_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]
    )
    write_json(RESULT_PATH, result)
    update_manifest(generated_at)
    replace_sprint_event(
        {
            "event": "expanded_market_source_consensus_robustness",
            "checkpoint": 247,
            "generated_utc": generated_at,
            "result": str(RESULT_PATH.relative_to(REPO)).replace("\\", "/"),
            "counts": counts,
            "boundary": research_boundary(),
        }
    )
    replace_active_checkpoint(generated_at, counts)
    print(json.dumps({"ok": True, "counts": counts}, sort_keys=True))


if __name__ == "__main__":
    main()
