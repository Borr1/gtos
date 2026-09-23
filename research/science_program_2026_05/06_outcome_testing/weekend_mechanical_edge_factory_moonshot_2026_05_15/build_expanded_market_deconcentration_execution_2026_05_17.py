#!/usr/bin/env python3
"""Execute deconcentration capacity pass over portfolio artifact selections."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_expanded_market_deconcentration_execution import (
    EXPANDED_MARKET_DECONCENTRATION_EXECUTION_SURFACE,
    aggregate_deconcentration_rows,
    deconcentration_rows,
    research_boundary,
    system_deconcentration_rows,
)


SELECTION_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_PORTFOLIO_ARTIFACT_SELECTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_DECONCENTRATION_EXECUTION"

SELECTION_RESULT = ROUTE_DIR / f"{SELECTION_PREFIX}_RESULT_2026-05-17.json"
SELECTION_LEDGER = ROUTE_DIR / f"{SELECTION_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
SELECTION_EVIDENCE_LEDGER = ROUTE_DIR / f"{SELECTION_PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_expanded_market_deconcentration_execution.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_expanded_market_deconcentration_execution_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
ROW_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
EVIDENCE_LEDGER = ROUTE_DIR / f"{PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"
CAPACITY_LEDGER = ROUTE_DIR / f"{PREFIX}_CAPACITY_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
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


def manifest_entries() -> list[dict[str, str]]:
    entries = [
        (RESULT_PATH, "expanded_market_deconcentration_execution_result"),
        (ROW_LEDGER, "expanded_market_deconcentration_rows"),
        (EVIDENCE_LEDGER, "expanded_market_deconcentration_evidence"),
        (CAPACITY_LEDGER, "expanded_market_deconcentration_capacity"),
        (AGGREGATE_LEDGER, "expanded_market_deconcentration_aggregates"),
        (SYSTEM_LEDGER, "expanded_market_deconcentration_system"),
        (SUMMARY_PATH, "expanded_market_deconcentration_summary"),
        (BUILDER_MODULE, "expanded_market_deconcentration_builder"),
        (VERIFIER_MODULE, "expanded_market_deconcentration_verifier"),
        (HELPER_MODULE, "expanded_market_deconcentration_helper"),
        (TEST_MODULE, "expanded_market_deconcentration_tests"),
    ]
    return [
        {"path": str(path.relative_to(REPO)).replace("\\", "/"), "status": "created", "type": kind}
        for path, kind in entries
    ]


def update_manifest(generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    entries = manifest_entries()
    existing = manifest.setdefault("artifacts", [])
    new_keys = {(entry["path"], entry["type"]) for entry in entries}
    manifest["artifacts"] = [entry for entry in existing if (entry.get("path"), entry.get("type")) not in new_keys] + entries
    manifest["latest_expanded_market_deconcentration_execution"] = {
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
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    payload = json.loads(stripped)
                except json.JSONDecodeError:
                    kept_lines.append(stripped)
                    continue
                if payload.get("checkpoint") == 228 and payload.get("event") == "expanded_market_deconcentration_execution":
                    continue
                kept_lines.append(stripped)
    kept_lines.append(json.dumps(event, sort_keys=True))
    with open(long_path(SPRINT_LEDGER), "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(kept_lines) + "\n")


def replace_active_checkpoint(generated_at: str, counts: dict[str, Any]) -> None:
    marker = "## Checkpoint 228 - Expanded-Market Deconcentration Execution"
    text = ""
    if ACTIVE_LEDGER.exists():
        with open(long_path(ACTIVE_LEDGER), "r", encoding="utf-8", errors="replace") as handle:
            text = handle.read()
    start = text.find(marker)
    if start != -1:
        next_start = text.find("\n## Checkpoint ", start + len(marker))
        text = text[:start].rstrip() + ("\n\n" + text[next_start:].lstrip() if next_start != -1 else "\n")
    addition = f"""
{marker}

Generated: {generated_at}

Trigger: direct continuation after Checkpoint 227. Portfolio artifact rows were executed through explicit concentration capacities; every guarded row was selected under capacity or preserved as redesign evidence with blocking dimensions.

Rows:
- input portfolio artifact selection rows: {counts['input_selection_rows']}
- input portfolio artifact selection evidence rows: {counts['input_evidence_rows']}
- deconcentration rows: {counts['deconcentration_rows']}
- deconcentration evidence rows: {counts['deconcentration_evidence_rows']}
- deconcentration capacity rows: {counts['deconcentration_capacity_rows']}
- aggregate rows: {counts['aggregate_rows']}
- capacity selected rows: {counts['capacity_selected_rows']}
- capacity added rows: {counts['capacity_added_rows']}
- redesign preserved rows: {counts['redesign_preserved_rows']}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: carry capacity-selected rows forward and preserve capacity-blocked rows as redesign evidence in the final branch-local review bundle.
"""
    with open(long_path(ACTIVE_LEDGER), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text.rstrip() + "\n\n" + addition.strip() + "\n")


def build_summary(counts: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Expanded-Market Deconcentration Execution",
            "",
            "This checkpoint executes portfolio artifact rows through explicit concentration capacities and preserves every row.",
            "",
            "## Counts",
            "",
            f"- Input portfolio artifact selection rows: `{counts['input_selection_rows']}`",
            f"- Input portfolio artifact selection evidence rows: `{counts['input_evidence_rows']}`",
            f"- Deconcentration rows: `{counts['deconcentration_rows']}`",
            f"- Deconcentration evidence rows: `{counts['deconcentration_evidence_rows']}`",
            f"- Deconcentration capacity rows: `{counts['deconcentration_capacity_rows']}`",
            f"- Aggregate rows: `{counts['aggregate_rows']}`",
            f"- Capacity selected rows: `{counts['capacity_selected_rows']}`",
            f"- Capacity added rows: `{counts['capacity_added_rows']}`",
            f"- Redesign preserved rows: `{counts['redesign_preserved_rows']}`",
            "",
            "## Decisions",
            "",
            f"`{json.dumps(counts['decision_counts'], sort_keys=True)}`",
            "",
            "## Continuation",
            "",
            "Carry capacity-selected rows forward and preserve capacity-blocked rows as redesign evidence in the final branch-local review bundle.",
            "",
        ]
    )


def main() -> None:
    generated_at = now_utc()
    selection_result = read_json(SELECTION_RESULT)
    selections = read_jsonl(SELECTION_LEDGER)
    input_evidence = read_jsonl(SELECTION_EVIDENCE_LEDGER)
    rows, evidence, capacity_rows = deconcentration_rows(selections, input_evidence)
    aggregates = aggregate_deconcentration_rows(rows)
    system_rows = system_deconcentration_rows(rows, evidence, capacity_rows, aggregates, len(selections), len(input_evidence))
    decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in rows)
    counts = {
        "input_result_ok": bool(selection_result.get("ok")),
        "input_selection_rows": len(selections),
        "input_evidence_rows": len(input_evidence),
        "deconcentration_rows": len(rows),
        "deconcentration_evidence_rows": len(evidence),
        "deconcentration_capacity_rows": len(capacity_rows),
        "aggregate_rows": len(aggregates),
        "system_rows": len(system_rows),
        "capacity_selected_rows": sum(1 for row in rows if row.get("capacity_selected") is True),
        "base_selected_rows": sum(1 for row in rows if row.get("base_selected_input") is True),
        "capacity_added_rows": sum(
            1 for row in rows if row.get("capacity_selected") is True and row.get("base_selected_input") is not True
        ),
        "redesign_preserved_rows": sum(1 for row in rows if row.get("capacity_selected") is not True),
        "capacity_filled_rows": sum(
            1 for row in capacity_rows if row.get("capacity_status") == "CAPACITY_FILLED_OR_EXCEEDED_INPUT"
        ),
        "decision_counts": dict(sorted(decisions.items())),
    }
    write_jsonl(ROW_LEDGER, rows)
    write_jsonl(EVIDENCE_LEDGER, evidence)
    write_jsonl(CAPACITY_LEDGER, capacity_rows)
    write_jsonl(AGGREGATE_LEDGER, aggregates)
    write_jsonl(SYSTEM_LEDGER, system_rows)
    write_text(SUMMARY_PATH, build_summary(counts))
    output_files = [ROW_LEDGER, EVIDENCE_LEDGER, CAPACITY_LEDGER, AGGREGATE_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]
    result = {
        "ok": True,
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "counts": counts,
        "inputs": {
            "selection_result": str(SELECTION_RESULT.relative_to(REPO)).replace("\\", "/"),
            "selection_ledger": str(SELECTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "selection_evidence_ledger": str(SELECTION_EVIDENCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "row_ledger": str(ROW_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "evidence_ledger": str(EVIDENCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "capacity_ledger": str(CAPACITY_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
        "output_sha256": output_sha256(output_files),
        "research_boundary": research_boundary(),
        "expanded_market_deconcentration_execution_surface": EXPANDED_MARKET_DECONCENTRATION_EXECUTION_SURFACE,
    }
    write_json(RESULT_PATH, result)
    update_manifest(generated_at)
    replace_sprint_event(
        {
            "checkpoint": 228,
            "event": "expanded_market_deconcentration_execution",
            "generated_utc": generated_at,
            "input_selection_rows": counts["input_selection_rows"],
            "deconcentration_rows": counts["deconcentration_rows"],
            "capacity_selected_rows": counts["capacity_selected_rows"],
            "redesign_preserved_rows": counts["redesign_preserved_rows"],
            "continuation": "continue to final branch-local review bundle.",
            "boundary": research_boundary(),
        }
    )
    replace_active_checkpoint(generated_at, counts)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
