#!/usr/bin/env python3
"""Build stress qualification for expanded-market unified numeric evidence."""

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

from src.research_infra.moonshot_expanded_market_unified_stress_qualification import (
    EXPANDED_MARKET_UNIFIED_STRESS_QUALIFICATION_SURFACE,
    research_boundary,
    system_unified_stress_qualification_rows,
    unified_stress_qualification_rows,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_UNIFIED_NUMERIC_EVIDENCE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_UNIFIED_STRESS_QUALIFICATION"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
INPUT_EVIDENCE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"
INPUT_TERMINAL_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_TERMINAL_LEDGER_2026-05-17.jsonl"
INPUT_DECISION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_DECISION_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_expanded_market_unified_stress_qualification.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_expanded_market_unified_stress_qualification_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
EVIDENCE_LEDGER = ROUTE_DIR / f"{PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"
TERMINAL_LEDGER = ROUTE_DIR / f"{PREFIX}_TERMINAL_LEDGER_2026-05-17.jsonl"
DECISION_LEDGER = ROUTE_DIR / f"{PREFIX}_DECISION_LEDGER_2026-05-17.jsonl"
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


def manifest_entries() -> list[dict[str, str]]:
    entries = [
        (RESULT_PATH, "expanded_market_unified_stress_result"),
        (EVIDENCE_LEDGER, "expanded_market_unified_stress_evidence_rows"),
        (TERMINAL_LEDGER, "expanded_market_unified_stress_terminal_rows"),
        (DECISION_LEDGER, "expanded_market_unified_stress_decision_rows"),
        (AGGREGATE_LEDGER, "expanded_market_unified_stress_aggregates"),
        (ISSUE_LEDGER, "expanded_market_unified_stress_issues"),
        (SYSTEM_LEDGER, "expanded_market_unified_stress_system"),
        (SUMMARY_PATH, "expanded_market_unified_stress_summary"),
        (BUILDER_MODULE, "expanded_market_unified_stress_builder"),
        (VERIFIER_MODULE, "expanded_market_unified_stress_verifier"),
        (HELPER_MODULE, "expanded_market_unified_stress_helper"),
        (TEST_MODULE, "expanded_market_unified_stress_tests"),
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
    manifest["latest_expanded_market_unified_stress_qualification"] = {
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
                if payload.get("checkpoint") == 239 and payload.get("event") == "expanded_market_unified_stress_qualification":
                    continue
                kept_lines.append(stripped)
    kept_lines.append(json.dumps(event, sort_keys=True))
    with open(long_path(SPRINT_LEDGER), "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(kept_lines) + "\n")


def replace_active_checkpoint(generated_at: str, counts: dict[str, Any]) -> None:
    marker = "## Checkpoint 239 - Expanded-Market Unified Stress Qualification"
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

Trigger: direct continuation after Checkpoint 238. Joined unified numeric evidence rows were stress-qualified with cost, stress, effective-N, path-edge, ambiguity, concentration, and source-access flags.

Rows:
- stress evidence rows: {counts['stress_evidence_rows']}
- stress terminal rows: {counts['stress_terminal_rows']}
- stress decision rows: {counts['stress_decision_rows']}
- aggregate rows: {counts['aggregate_rows']}
- issue rows: {counts['issue_rows']}
- qualified evidence rows: {counts['qualified_evidence_rows']}
- qualified decision rows: {counts['qualified_decision_rows']}
- terminal capacity rows: {counts['terminal_capacity_rows']}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: consume stress-qualified rows into the next numeric implementation/redesign plate; keep terminal-capacity rows separate from numeric failures.
"""
    with open(long_path(ACTIVE_LEDGER), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text.rstrip() + "\n\n" + addition.strip() + "\n")


def build_summary(counts: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Expanded-Market Unified Stress Qualification",
            "",
            "This checkpoint stress-qualifies every CP238 numeric evidence, terminal, and decision row.",
            "",
            "## Counts",
            "",
            f"- Stress evidence rows: `{counts['stress_evidence_rows']}`",
            f"- Stress terminal rows: `{counts['stress_terminal_rows']}`",
            f"- Stress decision rows: `{counts['stress_decision_rows']}`",
            f"- Aggregate rows: `{counts['aggregate_rows']}`",
            f"- Issue rows: `{counts['issue_rows']}`",
            f"- Qualified evidence rows: `{counts['qualified_evidence_rows']}`",
            f"- Qualified decision rows: `{counts['qualified_decision_rows']}`",
            f"- Terminal capacity rows: `{counts['terminal_capacity_rows']}`",
            "",
            "## Decisions",
            "",
            f"`{json.dumps(counts['decision_counts'], sort_keys=True)}`",
            "",
            "## Continuation",
            "",
            "Consume stress-qualified rows into the next numeric implementation/redesign plate.",
            "",
        ]
    )


def main() -> None:
    generated_at = now_utc()
    input_result = read_json(INPUT_RESULT)
    input_evidence = read_jsonl(INPUT_EVIDENCE_LEDGER)
    input_terminal = read_jsonl(INPUT_TERMINAL_LEDGER)
    input_decisions = read_jsonl(INPUT_DECISION_LEDGER)
    evidence_rows, terminal_rows, decision_rows, aggregate_rows, issue_rows = unified_stress_qualification_rows(
        input_evidence, input_terminal, input_decisions
    )
    input_counts = {
        "input_result_ok": input_result.get("ok"),
        "input_evidence_rows": len(input_evidence),
        "input_terminal_rows": len(input_terminal),
        "input_decision_rows": len(input_decisions),
    }
    system_rows = system_unified_stress_qualification_rows(
        evidence_rows, terminal_rows, decision_rows, aggregate_rows, issue_rows, input_counts
    )
    decision_counts = Counter(
        row.get("keep_kill_redesign_implement_decision")
        for row in evidence_rows + terminal_rows + decision_rows
    )
    counts = {
        "input_evidence_rows": len(input_evidence),
        "input_terminal_rows": len(input_terminal),
        "input_decision_rows": len(input_decisions),
        "stress_evidence_rows": len(evidence_rows),
        "stress_terminal_rows": len(terminal_rows),
        "stress_decision_rows": len(decision_rows),
        "aggregate_rows": len(aggregate_rows),
        "issue_rows": len(issue_rows),
        "system_rows": len(system_rows),
        "qualified_evidence_rows": sum(
            1
            for row in evidence_rows
            if row.get("keep_kill_redesign_implement_decision")
            == "IMPLEMENT_EXPANDED_MARKET_UNIFIED_STRESS_QUALIFIED"
        ),
        "qualified_decision_rows": sum(
            1
            for row in decision_rows
            if row.get("keep_kill_redesign_implement_decision")
            == "IMPLEMENT_EXPANDED_MARKET_UNIFIED_STRESS_QUALIFIED"
        ),
        "terminal_capacity_rows": sum(
            1
            for row in terminal_rows
            if row.get("keep_kill_redesign_implement_decision")
            == "REDESIGN_EXPANDED_MARKET_UNIFIED_STRESS_TERMINAL_CAPACITY"
        ),
        "decision_counts": dict(sorted(decision_counts.items())),
    }
    write_jsonl(EVIDENCE_LEDGER, evidence_rows)
    write_jsonl(TERMINAL_LEDGER, terminal_rows)
    write_jsonl(DECISION_LEDGER, decision_rows)
    write_jsonl(AGGREGATE_LEDGER, aggregate_rows)
    write_jsonl(ISSUE_LEDGER, issue_rows)
    write_jsonl(SYSTEM_LEDGER, system_rows)
    write_text(SUMMARY_PATH, build_summary(counts))
    outputs = [EVIDENCE_LEDGER, TERMINAL_LEDGER, DECISION_LEDGER, AGGREGATE_LEDGER, ISSUE_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "ok": True,
        "expanded_market_unified_stress_qualification_surface": (
            EXPANDED_MARKET_UNIFIED_STRESS_QUALIFICATION_SURFACE
        ),
        "inputs": {
            "input_result": str(INPUT_RESULT.relative_to(REPO)).replace("\\", "/"),
            "input_evidence_ledger": str(INPUT_EVIDENCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "input_terminal_ledger": str(INPUT_TERMINAL_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "input_decision_ledger": str(INPUT_DECISION_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "evidence_ledger": str(EVIDENCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "terminal_ledger": str(TERMINAL_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "decision_ledger": str(DECISION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "issue_ledger": str(ISSUE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
        "counts": counts,
        "research_boundary": research_boundary(),
    }
    write_json(RESULT_PATH, result)
    result["output_sha256"] = output_sha256(outputs + [RESULT_PATH])
    write_json(RESULT_PATH, result)
    update_manifest(generated_at)
    replace_sprint_event(
        {
            "event": "expanded_market_unified_stress_qualification",
            "checkpoint": 239,
            "generated_utc": generated_at,
            "counts": counts,
            "result": str(RESULT_PATH.relative_to(REPO)).replace("\\", "/"),
            "boundary": research_boundary(),
        }
    )
    replace_active_checkpoint(generated_at, counts)
    print(json.dumps({"ok": True, "counts": counts}, sort_keys=True))


if __name__ == "__main__":
    main()
