#!/usr/bin/env python3
"""Resolve unpackaged final-decision evidence into row-level actions."""

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

from src.research_infra.moonshot_expanded_market_unpackaged_evidence_resolution import (
    EXPANDED_MARKET_UNPACKAGED_EVIDENCE_RESOLUTION_SURFACE,
    research_boundary,
    system_resolution_rows,
    unpackaged_evidence_resolution_rows,
)


FINAL_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_FINAL_IMPLEMENTATION_DECISIONS"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_UNPACKAGED_EVIDENCE_RESOLUTION"

FINAL_RESULT = ROUTE_DIR / f"{FINAL_PREFIX}_RESULT_2026-05-17.json"
FINAL_EVIDENCE_LEDGER = ROUTE_DIR / f"{FINAL_PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"
FINAL_REDESIGN_LEDGER = ROUTE_DIR / f"{FINAL_PREFIX}_REDESIGN_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_expanded_market_unpackaged_evidence_resolution.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_expanded_market_unpackaged_evidence_resolution_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
RESOLUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_RESOLUTION_LEDGER_2026-05-17.jsonl"
REPACKAGE_CANDIDATE_LEDGER = ROUTE_DIR / f"{PREFIX}_REPACKAGE_CANDIDATE_LEDGER_2026-05-17.jsonl"
TERMINAL_REDESIGN_LEDGER = ROUTE_DIR / f"{PREFIX}_TERMINAL_REDESIGN_LEDGER_2026-05-17.jsonl"
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
        (RESULT_PATH, "expanded_market_unpackaged_evidence_resolution_result"),
        (RESOLUTION_LEDGER, "expanded_market_unpackaged_evidence_resolution_rows"),
        (REPACKAGE_CANDIDATE_LEDGER, "expanded_market_unpackaged_repackage_candidates"),
        (TERMINAL_REDESIGN_LEDGER, "expanded_market_unpackaged_terminal_redesign"),
        (AGGREGATE_LEDGER, "expanded_market_unpackaged_evidence_resolution_aggregates"),
        (SYSTEM_LEDGER, "expanded_market_unpackaged_evidence_resolution_system"),
        (SUMMARY_PATH, "expanded_market_unpackaged_evidence_resolution_summary"),
        (BUILDER_MODULE, "expanded_market_unpackaged_evidence_resolution_builder"),
        (VERIFIER_MODULE, "expanded_market_unpackaged_evidence_resolution_verifier"),
        (HELPER_MODULE, "expanded_market_unpackaged_evidence_resolution_helper"),
        (TEST_MODULE, "expanded_market_unpackaged_evidence_resolution_tests"),
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
    manifest["latest_expanded_market_unpackaged_evidence_resolution"] = {
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
                if payload.get("checkpoint") == 234 and payload.get("event") == "expanded_market_unpackaged_evidence_resolution":
                    continue
                kept_lines.append(stripped)
    kept_lines.append(json.dumps(event, sort_keys=True))
    with open(long_path(SPRINT_LEDGER), "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(kept_lines) + "\n")


def replace_active_checkpoint(generated_at: str, counts: dict[str, Any]) -> None:
    marker = "## Checkpoint 234 - Expanded-Market Unpackaged Evidence Resolution"
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

Trigger: direct continuation after Checkpoint 233. The final-decision evidence ledger was resolved row by row so unpackaged evidence becomes concrete repackage/redesign work rather than a carried bucket.

Rows:
- input final implementation evidence rows: {counts['input_final_implementation_evidence_rows']}
- input final implementation redesign rows: {counts['input_final_implementation_redesign_rows']}
- unpackaged evidence resolution rows: {counts['unpackaged_evidence_resolution_rows']}
- already implemented evidence rows: {counts['already_implemented_evidence_rows']}
- repackage-required evidence rows: {counts['repackage_required_evidence_rows']}
- unpackaged repackage candidate rows: {counts['unpackaged_repackage_candidate_rows']}
- terminal redesign rows: {counts['terminal_redesign_rows']}
- aggregate rows: {counts['aggregate_rows']}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: execute the unpackaged repackage candidates or close them as terminal redesign rows with source-path proof.
"""
    with open(long_path(ACTIVE_LEDGER), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text.rstrip() + "\n\n" + addition.strip() + "\n")


def build_summary(counts: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Expanded-Market Unpackaged Evidence Resolution",
            "",
            "This checkpoint resolves every final-decision evidence row and turns untied positive evidence into explicit branch-local repackage work.",
            "",
            "## Counts",
            "",
            f"- Input final implementation evidence rows: `{counts['input_final_implementation_evidence_rows']}`",
            f"- Input final implementation redesign rows: `{counts['input_final_implementation_redesign_rows']}`",
            f"- Unpackaged evidence resolution rows: `{counts['unpackaged_evidence_resolution_rows']}`",
            f"- Already implemented evidence rows: `{counts['already_implemented_evidence_rows']}`",
            f"- Repackage-required evidence rows: `{counts['repackage_required_evidence_rows']}`",
            f"- Unpackaged repackage candidate rows: `{counts['unpackaged_repackage_candidate_rows']}`",
            f"- Terminal redesign rows: `{counts['terminal_redesign_rows']}`",
            f"- Aggregate rows: `{counts['aggregate_rows']}`",
            "",
            "## Continuation",
            "",
            "Execute the unpackaged repackage candidates or close them as terminal redesign rows with source-path proof.",
            "",
        ]
    )


def main() -> None:
    generated_at = now_utc()
    final_result = read_json(FINAL_RESULT)
    evidence = read_jsonl(FINAL_EVIDENCE_LEDGER)
    redesign = read_jsonl(FINAL_REDESIGN_LEDGER)
    resolution, candidates, terminal_redesign, aggregates = unpackaged_evidence_resolution_rows(evidence, redesign)
    system_rows = system_resolution_rows(resolution, candidates, terminal_redesign, aggregates, len(evidence), len(redesign))
    system = system_rows[0]
    counts = {
        "input_result_ok": bool(final_result.get("ok")),
        "input_final_implementation_evidence_rows": len(evidence),
        "input_final_implementation_redesign_rows": len(redesign),
        "unpackaged_evidence_resolution_rows": len(resolution),
        "unpackaged_repackage_candidate_rows": len(candidates),
        "terminal_redesign_rows": len(terminal_redesign),
        "aggregate_rows": len(aggregates),
        "system_rows": len(system_rows),
        "already_implemented_evidence_rows": system["already_implemented_evidence_rows"],
        "repackage_required_evidence_rows": system["repackage_required_evidence_rows"],
        "underpowered_evidence_rows": system["underpowered_evidence_rows"],
        "kill_evidence_rows": system["kill_evidence_rows"],
        "missing_simulated_r_rows": system["missing_simulated_r_rows"],
    }
    write_jsonl(RESOLUTION_LEDGER, resolution)
    write_jsonl(REPACKAGE_CANDIDATE_LEDGER, candidates)
    write_jsonl(TERMINAL_REDESIGN_LEDGER, terminal_redesign)
    write_jsonl(AGGREGATE_LEDGER, aggregates)
    write_jsonl(SYSTEM_LEDGER, system_rows)
    write_text(SUMMARY_PATH, build_summary(counts))
    output_files = [RESOLUTION_LEDGER, REPACKAGE_CANDIDATE_LEDGER, TERMINAL_REDESIGN_LEDGER, AGGREGATE_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]
    result = {
        "ok": True,
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "counts": counts,
        "inputs": {
            "final_decision_result": str(FINAL_RESULT.relative_to(REPO)).replace("\\", "/"),
            "final_evidence_ledger": str(FINAL_EVIDENCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "final_redesign_ledger": str(FINAL_REDESIGN_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "resolution_ledger": str(RESOLUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "repackage_candidate_ledger": str(REPACKAGE_CANDIDATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "terminal_redesign_ledger": str(TERMINAL_REDESIGN_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
        "output_sha256": output_sha256(output_files),
        "research_boundary": research_boundary(),
        "expanded_market_unpackaged_evidence_resolution_surface": (
            EXPANDED_MARKET_UNPACKAGED_EVIDENCE_RESOLUTION_SURFACE
        ),
    }
    write_json(RESULT_PATH, result)
    update_manifest(generated_at)
    replace_sprint_event(
        {
            "checkpoint": 234,
            "event": "expanded_market_unpackaged_evidence_resolution",
            "generated_utc": generated_at,
            "input_final_implementation_evidence_rows": counts["input_final_implementation_evidence_rows"],
            "unpackaged_evidence_resolution_rows": counts["unpackaged_evidence_resolution_rows"],
            "repackage_required_evidence_rows": counts["repackage_required_evidence_rows"],
            "unpackaged_repackage_candidate_rows": counts["unpackaged_repackage_candidate_rows"],
            "terminal_redesign_rows": counts["terminal_redesign_rows"],
            "continuation": "continue to execute unpackaged repackage candidates or terminal redesign closure.",
            "boundary": research_boundary(),
        }
    )
    replace_active_checkpoint(generated_at, counts)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
