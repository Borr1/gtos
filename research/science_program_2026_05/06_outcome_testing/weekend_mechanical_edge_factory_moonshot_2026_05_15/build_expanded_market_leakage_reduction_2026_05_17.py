#!/usr/bin/env python3
"""Reduce expanded-market code-candidate leakage with concrete replay predicates."""

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

from src.research_infra.moonshot_expanded_market_leakage_reduction import (
    EXPANDED_MARKET_LEAKAGE_REDUCTION_SURFACE,
    aggregate_reduction_rows,
    leakage_reduction_rows,
    research_boundary,
    system_reduction_rows,
)


CANDIDATE_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_CODE_CANDIDATES"
EXECUTION_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_CODE_CANDIDATE_EXECUTION"
SELECTION_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_IMPLEMENTATION_SELECTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_LEAKAGE_REDUCTION"

CANDIDATE_LEDGER = ROUTE_DIR / f"{CANDIDATE_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
EXECUTION_RESULT = ROUTE_DIR / f"{EXECUTION_PREFIX}_RESULT_2026-05-17.json"
EXECUTION_LEDGER = ROUTE_DIR / f"{EXECUTION_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
SELECTION_LEDGER = ROUTE_DIR / f"{SELECTION_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_expanded_market_leakage_reduction.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_expanded_market_leakage_reduction_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
ROW_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
MATCH_LEDGER = ROUTE_DIR / f"{PREFIX}_MATCH_LEDGER_2026-05-17.jsonl"
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
        (RESULT_PATH, "expanded_market_leakage_reduction_result"),
        (ROW_LEDGER, "expanded_market_leakage_reduction_rows"),
        (MATCH_LEDGER, "expanded_market_leakage_reduction_match_rows"),
        (AGGREGATE_LEDGER, "expanded_market_leakage_reduction_aggregates"),
        (SYSTEM_LEDGER, "expanded_market_leakage_reduction_system"),
        (SUMMARY_PATH, "expanded_market_leakage_reduction_summary"),
        (BUILDER_MODULE, "expanded_market_leakage_reduction_builder"),
        (VERIFIER_MODULE, "expanded_market_leakage_reduction_verifier"),
        (HELPER_MODULE, "expanded_market_leakage_reduction_helper"),
        (TEST_MODULE, "expanded_market_leakage_reduction_tests"),
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
    manifest["latest_expanded_market_leakage_reduction"] = {
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
                if payload.get("checkpoint") == 223 and payload.get("event") == "expanded_market_leakage_reduction":
                    continue
                kept_lines.append(stripped)
    kept_lines.append(json.dumps(event, sort_keys=True))
    with open(long_path(SPRINT_LEDGER), "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(kept_lines) + "\n")


def replace_active_checkpoint(generated_at: str, counts: dict[str, Any]) -> None:
    marker = "## Checkpoint 223 - Expanded-Market Leakage Reduction"
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

Trigger: direct continuation after Checkpoint 222. Code-candidate execution leakage rows were narrowed with source path/hash and replay-performance thresholds from their originating implementation-selection rows.

Rows:
- input code-candidate execution rows: {counts['input_code_candidate_execution_rows']}
- input code-candidate rows: {counts['input_code_candidate_rows']}
- input implementation-selection rows: {counts['input_selection_rows']}
- leakage-reduction rows: {counts['leakage_reduction_rows']}
- leakage-reduction match rows: {counts['leakage_reduction_match_rows']}
- aggregate rows: {counts['aggregate_rows']}
- preserved execution-pass rows: {counts['preserved_pass_rows']}
- reduced execution-pass rows: {counts['reduced_pass_rows']}
- remaining repair rows: {counts['remaining_repair_rows']}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: consume reduced and preserved leakage-reduction rows into concrete branch-local candidate execution surfaces or terminal redesign evidence.
"""
    with open(long_path(ACTIVE_LEDGER), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text.rstrip() + "\n\n" + addition.strip() + "\n")


def build_summary(counts: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Expanded-Market Leakage Reduction",
            "",
            "This checkpoint narrows code-candidate execution leakage with source path/hash and replay-performance thresholds.",
            "",
            "## Counts",
            "",
            f"- Input code-candidate execution rows: `{counts['input_code_candidate_execution_rows']}`",
            f"- Input code-candidate rows: `{counts['input_code_candidate_rows']}`",
            f"- Input implementation-selection rows: `{counts['input_selection_rows']}`",
            f"- Leakage-reduction rows: `{counts['leakage_reduction_rows']}`",
            f"- Leakage-reduction match rows: `{counts['leakage_reduction_match_rows']}`",
            f"- Aggregate rows: `{counts['aggregate_rows']}`",
            f"- Preserved execution-pass rows: `{counts['preserved_pass_rows']}`",
            f"- Reduced execution-pass rows: `{counts['reduced_pass_rows']}`",
            f"- Remaining repair rows: `{counts['remaining_repair_rows']}`",
            "",
            "## Decisions",
            "",
            f"`{json.dumps(counts['decision_counts'], sort_keys=True)}`",
            "",
            "## Continuation",
            "",
            "Consume reduced and preserved rows into concrete branch-local execution surfaces or terminal redesign evidence.",
            "",
        ]
    )


def main() -> None:
    generated_at = now_utc()
    execution_result = read_json(EXECUTION_RESULT)
    candidates = read_jsonl(CANDIDATE_LEDGER)
    executions = read_jsonl(EXECUTION_LEDGER)
    selections = read_jsonl(SELECTION_LEDGER)
    reduction_rows, match_rows = leakage_reduction_rows(candidates, executions, selections)
    aggregate_rows = aggregate_reduction_rows(reduction_rows)
    system_rows = system_reduction_rows(reduction_rows, match_rows, aggregate_rows, len(executions))
    decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in reduction_rows)
    counts = {
        "input_result_ok": bool(execution_result.get("ok")),
        "input_code_candidate_execution_rows": len(executions),
        "input_code_candidate_rows": len(candidates),
        "input_selection_rows": len(selections),
        "leakage_reduction_rows": len(reduction_rows),
        "leakage_reduction_match_rows": len(match_rows),
        "aggregate_rows": len(aggregate_rows),
        "system_rows": len(system_rows),
        "preserved_pass_rows": decisions.get("IMPLEMENT_EXPANDED_MARKET_CODE_CANDIDATE_EXECUTION_PRESERVED", 0),
        "reduced_pass_rows": decisions.get("IMPLEMENT_EXPANDED_MARKET_LEAKAGE_REDUCED_CODE_CANDIDATE", 0),
        "remaining_repair_rows": sum(count for decision, count in decisions.items() if str(decision).startswith("REDESIGN")),
        "decision_counts": dict(sorted(decisions.items())),
    }
    write_jsonl(ROW_LEDGER, reduction_rows)
    write_jsonl(MATCH_LEDGER, match_rows)
    write_jsonl(AGGREGATE_LEDGER, aggregate_rows)
    write_jsonl(SYSTEM_LEDGER, system_rows)
    write_text(SUMMARY_PATH, build_summary(counts))
    output_files = [ROW_LEDGER, MATCH_LEDGER, AGGREGATE_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]
    result = {
        "ok": True,
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "counts": counts,
        "inputs": {
            "execution_result": str(EXECUTION_RESULT.relative_to(REPO)).replace("\\", "/"),
            "execution_ledger": str(EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "candidate_ledger": str(CANDIDATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "selection_ledger": str(SELECTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "row_ledger": str(ROW_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "match_ledger": str(MATCH_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
        "output_sha256": output_sha256(output_files),
        "research_boundary": research_boundary(),
        "expanded_market_leakage_reduction_surface": EXPANDED_MARKET_LEAKAGE_REDUCTION_SURFACE,
    }
    write_json(RESULT_PATH, result)
    update_manifest(generated_at)
    replace_sprint_event(
        {
            "checkpoint": 223,
            "event": "expanded_market_leakage_reduction",
            "generated_utc": generated_at,
            "input_code_candidate_execution_rows": counts["input_code_candidate_execution_rows"],
            "leakage_reduction_rows": counts["leakage_reduction_rows"],
            "leakage_reduction_match_rows": counts["leakage_reduction_match_rows"],
            "aggregate_rows": counts["aggregate_rows"],
            "reduced_pass_rows": counts["reduced_pass_rows"],
            "remaining_repair_rows": counts["remaining_repair_rows"],
            "continuation": "continue to branch-local execution surfaces or terminal redesign evidence.",
            "boundary": research_boundary(),
        }
    )
    replace_active_checkpoint(generated_at, counts)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
