#!/usr/bin/env python3
"""Build final branch-local decisions from passing repackage executions."""

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

from src.research_infra.moonshot_expanded_market_repackage_final_decisions import (
    EXPANDED_MARKET_REPACKAGE_FINAL_DECISIONS_SURFACE,
    repackage_final_decision_rows,
    research_boundary,
    system_repackage_final_decision_rows,
)


EXECUTION_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_REPACKAGE_EXECUTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_REPACKAGE_FINAL_DECISIONS"

EXECUTION_RESULT = ROUTE_DIR / f"{EXECUTION_PREFIX}_RESULT_2026-05-17.json"
EXECUTION_LEDGER = ROUTE_DIR / f"{EXECUTION_PREFIX}_EXECUTION_LEDGER_2026-05-17.jsonl"
REPACKAGE_EVIDENCE_LEDGER = ROUTE_DIR / f"{EXECUTION_PREFIX}_REPACKAGE_EVIDENCE_LEDGER_2026-05-17.jsonl"
EXISTING_EVIDENCE_LEDGER = ROUTE_DIR / f"{EXECUTION_PREFIX}_EXISTING_EVIDENCE_LEDGER_2026-05-17.jsonl"
TERMINAL_REDESIGN_LEDGER = ROUTE_DIR / f"{EXECUTION_PREFIX}_TERMINAL_REDESIGN_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_expanded_market_repackage_final_decisions.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_expanded_market_repackage_final_decisions_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
DECISION_LEDGER = ROUTE_DIR / f"{PREFIX}_DECISION_LEDGER_2026-05-17.jsonl"
EVIDENCE_LEDGER = ROUTE_DIR / f"{PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"
EXISTING_CARRY_LEDGER = ROUTE_DIR / f"{PREFIX}_EXISTING_EVIDENCE_LEDGER_2026-05-17.jsonl"
TERMINAL_CARRY_LEDGER = ROUTE_DIR / f"{PREFIX}_TERMINAL_REDESIGN_LEDGER_2026-05-17.jsonl"
CONTROL_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTROL_LEDGER_2026-05-17.jsonl"
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
        (RESULT_PATH, "expanded_market_repackage_final_decisions_result"),
        (DECISION_LEDGER, "expanded_market_repackage_final_decisions"),
        (EVIDENCE_LEDGER, "expanded_market_repackage_final_evidence"),
        (EXISTING_CARRY_LEDGER, "expanded_market_repackage_final_existing_evidence"),
        (TERMINAL_CARRY_LEDGER, "expanded_market_repackage_final_terminal_redesign"),
        (CONTROL_LEDGER, "expanded_market_repackage_final_controls"),
        (AGGREGATE_LEDGER, "expanded_market_repackage_final_aggregates"),
        (SYSTEM_LEDGER, "expanded_market_repackage_final_system"),
        (SUMMARY_PATH, "expanded_market_repackage_final_summary"),
        (BUILDER_MODULE, "expanded_market_repackage_final_builder"),
        (VERIFIER_MODULE, "expanded_market_repackage_final_verifier"),
        (HELPER_MODULE, "expanded_market_repackage_final_helper"),
        (TEST_MODULE, "expanded_market_repackage_final_tests"),
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
    manifest["latest_expanded_market_repackage_final_decisions"] = {
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
                if payload.get("checkpoint") == 236 and payload.get("event") == "expanded_market_repackage_final_decisions":
                    continue
                kept_lines.append(stripped)
    kept_lines.append(json.dumps(event, sort_keys=True))
    with open(long_path(SPRINT_LEDGER), "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(kept_lines) + "\n")


def replace_active_checkpoint(generated_at: str, counts: dict[str, Any]) -> None:
    marker = "## Checkpoint 236 - Expanded-Market Repackage Final Decisions"
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

Trigger: direct continuation after Checkpoint 235. Passing repackage executions were converted into final branch-local decisions while every evidence and terminal redesign row remained addressable.

Rows:
- input repackage execution rows: {counts['input_repackage_execution_rows']}
- input repackage evidence execution rows: {counts['input_repackage_evidence_execution_rows']}
- input existing evidence preservation rows: {counts['input_existing_evidence_preservation_rows']}
- input terminal redesign execution rows: {counts['input_terminal_redesign_execution_rows']}
- repackage final decision rows: {counts['repackage_final_decision_rows']}
- repackage final evidence rows: {counts['repackage_final_evidence_rows']}
- repackage final existing evidence rows: {counts['repackage_final_existing_evidence_rows']}
- repackage final terminal redesign rows: {counts['repackage_final_terminal_redesign_rows']}
- repackage final control rows: {counts['repackage_final_control_rows']}
- aggregate rows: {counts['aggregate_rows']}
- ready repackage final decision rows: {counts['ready_repackage_final_decision_rows']}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: merge final package decisions and final repackage decisions into a single branch-local implementation decision plate.
"""
    with open(long_path(ACTIVE_LEDGER), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text.rstrip() + "\n\n" + addition.strip() + "\n")


def build_summary(counts: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Expanded-Market Repackage Final Decisions",
            "",
            "This checkpoint converts passing repackage executions into final branch-local decision rows and preserves every associated evidence row.",
            "",
            "## Counts",
            "",
            f"- Input repackage execution rows: `{counts['input_repackage_execution_rows']}`",
            f"- Input repackage evidence execution rows: `{counts['input_repackage_evidence_execution_rows']}`",
            f"- Input existing evidence preservation rows: `{counts['input_existing_evidence_preservation_rows']}`",
            f"- Input terminal redesign execution rows: `{counts['input_terminal_redesign_execution_rows']}`",
            f"- Repackage final decision rows: `{counts['repackage_final_decision_rows']}`",
            f"- Repackage final evidence rows: `{counts['repackage_final_evidence_rows']}`",
            f"- Repackage final existing evidence rows: `{counts['repackage_final_existing_evidence_rows']}`",
            f"- Repackage final terminal redesign rows: `{counts['repackage_final_terminal_redesign_rows']}`",
            f"- Repackage final control rows: `{counts['repackage_final_control_rows']}`",
            f"- Aggregate rows: `{counts['aggregate_rows']}`",
            f"- Ready repackage final decision rows: `{counts['ready_repackage_final_decision_rows']}`",
            "",
            "## Continuation",
            "",
            "Merge final package decisions and final repackage decisions into a single branch-local implementation decision plate.",
            "",
        ]
    )


def main() -> None:
    generated_at = now_utc()
    execution_result = read_json(EXECUTION_RESULT)
    executions = read_jsonl(EXECUTION_LEDGER)
    evidence = read_jsonl(REPACKAGE_EVIDENCE_LEDGER)
    existing = read_jsonl(EXISTING_EVIDENCE_LEDGER)
    terminal = read_jsonl(TERMINAL_REDESIGN_LEDGER)
    decisions, final_evidence, final_existing, final_terminal, controls, aggregates = repackage_final_decision_rows(
        executions, evidence, existing, terminal
    )
    system_rows = system_repackage_final_decision_rows(
        decisions, final_evidence, final_existing, final_terminal, controls, aggregates,
        len(executions), len(evidence), len(existing), len(terminal)
    )
    system = system_rows[0]
    counts = {
        "input_result_ok": bool(execution_result.get("ok")),
        "input_repackage_execution_rows": len(executions),
        "input_repackage_evidence_execution_rows": len(evidence),
        "input_existing_evidence_preservation_rows": len(existing),
        "input_terminal_redesign_execution_rows": len(terminal),
        "repackage_final_decision_rows": len(decisions),
        "repackage_final_evidence_rows": len(final_evidence),
        "repackage_final_existing_evidence_rows": len(final_existing),
        "repackage_final_terminal_redesign_rows": len(final_terminal),
        "repackage_final_control_rows": len(controls),
        "aggregate_rows": len(aggregates),
        "system_rows": len(system_rows),
        "ready_repackage_final_decision_rows": system["ready_repackage_final_decision_rows"],
        "repair_repackage_final_decision_rows": system["repair_repackage_final_decision_rows"],
        "evidence_pass_rows": system["evidence_pass_rows"],
        "control_pass_rows": system["control_pass_rows"],
        "terminal_redesign_rows": system["terminal_redesign_rows"],
    }
    write_jsonl(DECISION_LEDGER, decisions)
    write_jsonl(EVIDENCE_LEDGER, final_evidence)
    write_jsonl(EXISTING_CARRY_LEDGER, final_existing)
    write_jsonl(TERMINAL_CARRY_LEDGER, final_terminal)
    write_jsonl(CONTROL_LEDGER, controls)
    write_jsonl(AGGREGATE_LEDGER, aggregates)
    write_jsonl(SYSTEM_LEDGER, system_rows)
    write_text(SUMMARY_PATH, build_summary(counts))
    output_files = [DECISION_LEDGER, EVIDENCE_LEDGER, EXISTING_CARRY_LEDGER, TERMINAL_CARRY_LEDGER, CONTROL_LEDGER, AGGREGATE_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]
    result = {
        "ok": True,
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "counts": counts,
        "inputs": {
            "repackage_execution_result": str(EXECUTION_RESULT.relative_to(REPO)).replace("\\", "/"),
            "execution_ledger": str(EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "repackage_evidence_ledger": str(REPACKAGE_EVIDENCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "existing_evidence_ledger": str(EXISTING_EVIDENCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "terminal_redesign_ledger": str(TERMINAL_REDESIGN_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "decision_ledger": str(DECISION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "evidence_ledger": str(EVIDENCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "existing_evidence_ledger": str(EXISTING_CARRY_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "terminal_redesign_ledger": str(TERMINAL_CARRY_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "control_ledger": str(CONTROL_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
        "output_sha256": output_sha256(output_files),
        "research_boundary": research_boundary(),
        "expanded_market_repackage_final_decisions_surface": EXPANDED_MARKET_REPACKAGE_FINAL_DECISIONS_SURFACE,
    }
    write_json(RESULT_PATH, result)
    update_manifest(generated_at)
    replace_sprint_event({
        "checkpoint": 236,
        "event": "expanded_market_repackage_final_decisions",
        "generated_utc": generated_at,
        "input_repackage_execution_rows": counts["input_repackage_execution_rows"],
        "repackage_final_decision_rows": counts["repackage_final_decision_rows"],
        "repackage_final_evidence_rows": counts["repackage_final_evidence_rows"],
        "repackage_final_existing_evidence_rows": counts["repackage_final_existing_evidence_rows"],
        "repackage_final_terminal_redesign_rows": counts["repackage_final_terminal_redesign_rows"],
        "ready_repackage_final_decision_rows": counts["ready_repackage_final_decision_rows"],
        "continuation": "continue to unified final branch-local implementation decision plate.",
        "boundary": research_boundary(),
    })
    replace_active_checkpoint(generated_at, counts)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
