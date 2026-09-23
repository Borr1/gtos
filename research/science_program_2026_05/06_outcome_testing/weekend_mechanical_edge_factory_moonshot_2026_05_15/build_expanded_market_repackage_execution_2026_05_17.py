#!/usr/bin/env python3
"""Execute expanded-market unpackaged repackage candidates with source proof."""

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

from src.research_infra.moonshot_expanded_market_repackage_execution import (
    EXPANDED_MARKET_REPACKAGE_EXECUTION_SURFACE,
    expanded_market_repackage_execution_rows,
    research_boundary,
    system_repackage_execution_rows,
)


UNPACKAGED_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_UNPACKAGED_EVIDENCE_RESOLUTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_REPACKAGE_EXECUTION"

UNPACKAGED_RESULT = ROUTE_DIR / f"{UNPACKAGED_PREFIX}_RESULT_2026-05-17.json"
REPACKAGE_CANDIDATE_LEDGER = ROUTE_DIR / f"{UNPACKAGED_PREFIX}_REPACKAGE_CANDIDATE_LEDGER_2026-05-17.jsonl"
RESOLUTION_LEDGER = ROUTE_DIR / f"{UNPACKAGED_PREFIX}_RESOLUTION_LEDGER_2026-05-17.jsonl"
TERMINAL_REDESIGN_LEDGER = ROUTE_DIR / f"{UNPACKAGED_PREFIX}_TERMINAL_REDESIGN_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_expanded_market_repackage_execution.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_expanded_market_repackage_execution_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_EXECUTION_LEDGER_2026-05-17.jsonl"
REPACKAGE_EVIDENCE_LEDGER = ROUTE_DIR / f"{PREFIX}_REPACKAGE_EVIDENCE_LEDGER_2026-05-17.jsonl"
EXISTING_EVIDENCE_LEDGER = ROUTE_DIR / f"{PREFIX}_EXISTING_EVIDENCE_LEDGER_2026-05-17.jsonl"
TERMINAL_REDESIGN_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_TERMINAL_REDESIGN_LEDGER_2026-05-17.jsonl"
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
        (RESULT_PATH, "expanded_market_repackage_execution_result"),
        (EXECUTION_LEDGER, "expanded_market_repackage_execution_rows"),
        (REPACKAGE_EVIDENCE_LEDGER, "expanded_market_repackage_evidence_execution_rows"),
        (EXISTING_EVIDENCE_LEDGER, "expanded_market_existing_evidence_preservation_rows"),
        (TERMINAL_REDESIGN_EXECUTION_LEDGER, "expanded_market_repackage_terminal_redesign_rows"),
        (AGGREGATE_LEDGER, "expanded_market_repackage_execution_aggregates"),
        (SYSTEM_LEDGER, "expanded_market_repackage_execution_system"),
        (SUMMARY_PATH, "expanded_market_repackage_execution_summary"),
        (BUILDER_MODULE, "expanded_market_repackage_execution_builder"),
        (VERIFIER_MODULE, "expanded_market_repackage_execution_verifier"),
        (HELPER_MODULE, "expanded_market_repackage_execution_helper"),
        (TEST_MODULE, "expanded_market_repackage_execution_tests"),
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
    manifest["latest_expanded_market_repackage_execution"] = {
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
                if payload.get("checkpoint") == 235 and payload.get("event") == "expanded_market_repackage_execution":
                    continue
                kept_lines.append(stripped)
    kept_lines.append(json.dumps(event, sort_keys=True))
    with open(long_path(SPRINT_LEDGER), "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(kept_lines) + "\n")


def replace_active_checkpoint(generated_at: str, counts: dict[str, Any]) -> None:
    marker = "## Checkpoint 235 - Expanded-Market Repackage Execution"
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

Trigger: direct continuation after Checkpoint 234. Unpackaged repackage candidates were executed against source-path/hash proof and their evidence rows.

Rows:
- input unpackaged repackage candidate rows: {counts['input_unpackaged_repackage_candidate_rows']}
- input unpackaged evidence resolution rows: {counts['input_unpackaged_evidence_resolution_rows']}
- input terminal redesign rows: {counts['input_terminal_redesign_rows']}
- repackage execution rows: {counts['repackage_execution_rows']}
- repackage evidence execution rows: {counts['repackage_evidence_execution_rows']}
- existing evidence preservation rows: {counts['existing_evidence_preservation_rows']}
- terminal redesign execution rows: {counts['terminal_redesign_execution_rows']}
- aggregate rows: {counts['aggregate_rows']}
- repackage execution pass rows: {counts['repackage_execution_pass_rows']}
- source proof pass rows: {counts['source_proof_pass_rows']}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: package the passing repackage executions into final branch-local decisions or preserve any repair rows with exact source proof.
"""
    with open(long_path(ACTIVE_LEDGER), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text.rstrip() + "\n\n" + addition.strip() + "\n")


def build_summary(counts: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Expanded-Market Repackage Execution",
            "",
            "This checkpoint executes unpackaged repackage candidates against source-path and source-hash proof while preserving every evidence and terminal redesign row.",
            "",
            "## Counts",
            "",
            f"- Input unpackaged repackage candidate rows: `{counts['input_unpackaged_repackage_candidate_rows']}`",
            f"- Input unpackaged evidence resolution rows: `{counts['input_unpackaged_evidence_resolution_rows']}`",
            f"- Input terminal redesign rows: `{counts['input_terminal_redesign_rows']}`",
            f"- Repackage execution rows: `{counts['repackage_execution_rows']}`",
            f"- Repackage evidence execution rows: `{counts['repackage_evidence_execution_rows']}`",
            f"- Existing evidence preservation rows: `{counts['existing_evidence_preservation_rows']}`",
            f"- Terminal redesign execution rows: `{counts['terminal_redesign_execution_rows']}`",
            f"- Aggregate rows: `{counts['aggregate_rows']}`",
            f"- Repackage execution pass rows: `{counts['repackage_execution_pass_rows']}`",
            f"- Source proof pass rows: `{counts['source_proof_pass_rows']}`",
            "",
            "## Continuation",
            "",
            "Package the passing repackage executions into final branch-local decisions or preserve any repair rows with exact source proof.",
            "",
        ]
    )


def main() -> None:
    generated_at = now_utc()
    unpackaged_result = read_json(UNPACKAGED_RESULT)
    candidates = read_jsonl(REPACKAGE_CANDIDATE_LEDGER)
    resolution = read_jsonl(RESOLUTION_LEDGER)
    terminal_redesign = read_jsonl(TERMINAL_REDESIGN_LEDGER)
    executions, repackage_evidence, existing_evidence, terminal_execution, aggregates = (
        expanded_market_repackage_execution_rows(candidates, resolution, terminal_redesign, REPO)
    )
    system_rows = system_repackage_execution_rows(
        executions,
        repackage_evidence,
        existing_evidence,
        terminal_execution,
        aggregates,
        len(candidates),
        len(resolution),
        len(terminal_redesign),
    )
    system = system_rows[0]
    counts = {
        "input_result_ok": bool(unpackaged_result.get("ok")),
        "input_unpackaged_repackage_candidate_rows": len(candidates),
        "input_unpackaged_evidence_resolution_rows": len(resolution),
        "input_terminal_redesign_rows": len(terminal_redesign),
        "repackage_execution_rows": len(executions),
        "repackage_evidence_execution_rows": len(repackage_evidence),
        "existing_evidence_preservation_rows": len(existing_evidence),
        "terminal_redesign_execution_rows": len(terminal_execution),
        "aggregate_rows": len(aggregates),
        "system_rows": len(system_rows),
        "repackage_execution_pass_rows": system["repackage_execution_pass_rows"],
        "repackage_execution_repair_rows": system["repackage_execution_repair_rows"],
        "source_proof_pass_rows": system["source_proof_pass_rows"],
        "terminal_redesign_source_proof_pass_rows": system["terminal_redesign_source_proof_pass_rows"],
    }
    write_jsonl(EXECUTION_LEDGER, executions)
    write_jsonl(REPACKAGE_EVIDENCE_LEDGER, repackage_evidence)
    write_jsonl(EXISTING_EVIDENCE_LEDGER, existing_evidence)
    write_jsonl(TERMINAL_REDESIGN_EXECUTION_LEDGER, terminal_execution)
    write_jsonl(AGGREGATE_LEDGER, aggregates)
    write_jsonl(SYSTEM_LEDGER, system_rows)
    write_text(SUMMARY_PATH, build_summary(counts))
    output_files = [EXECUTION_LEDGER, REPACKAGE_EVIDENCE_LEDGER, EXISTING_EVIDENCE_LEDGER, TERMINAL_REDESIGN_EXECUTION_LEDGER, AGGREGATE_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]
    result = {
        "ok": True,
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "counts": counts,
        "inputs": {
            "unpackaged_result": str(UNPACKAGED_RESULT.relative_to(REPO)).replace("\\", "/"),
            "repackage_candidate_ledger": str(REPACKAGE_CANDIDATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "resolution_ledger": str(RESOLUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "terminal_redesign_ledger": str(TERMINAL_REDESIGN_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "execution_ledger": str(EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "repackage_evidence_ledger": str(REPACKAGE_EVIDENCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "existing_evidence_ledger": str(EXISTING_EVIDENCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "terminal_redesign_execution_ledger": str(TERMINAL_REDESIGN_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
        "output_sha256": output_sha256(output_files),
        "research_boundary": research_boundary(),
        "expanded_market_repackage_execution_surface": EXPANDED_MARKET_REPACKAGE_EXECUTION_SURFACE,
    }
    write_json(RESULT_PATH, result)
    update_manifest(generated_at)
    replace_sprint_event(
        {
            "checkpoint": 235,
            "event": "expanded_market_repackage_execution",
            "generated_utc": generated_at,
            "input_unpackaged_repackage_candidate_rows": counts["input_unpackaged_repackage_candidate_rows"],
            "repackage_execution_rows": counts["repackage_execution_rows"],
            "repackage_evidence_execution_rows": counts["repackage_evidence_execution_rows"],
            "existing_evidence_preservation_rows": counts["existing_evidence_preservation_rows"],
            "terminal_redesign_execution_rows": counts["terminal_redesign_execution_rows"],
            "repackage_execution_pass_rows": counts["repackage_execution_pass_rows"],
            "continuation": "continue to final branch-local decisions for passing repackage executions.",
            "boundary": research_boundary(),
        }
    )
    replace_active_checkpoint(generated_at, counts)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
