#!/usr/bin/env python3
"""Build implementation candidates from reduced expanded-market executions."""

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

from src.research_infra.moonshot_expanded_market_reduced_implementation_candidates import (
    EXPANDED_MARKET_REDUCED_IMPLEMENTATION_CANDIDATES_SURFACE,
    aggregate_candidate_rows,
    implementation_candidate_rows,
    research_boundary,
    system_candidate_rows,
)


EXECUTION_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_REDUCED_SURFACE_EXECUTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_REDUCED_IMPLEMENTATION_CANDIDATES"

EXECUTION_RESULT = ROUTE_DIR / f"{EXECUTION_PREFIX}_RESULT_2026-05-17.json"
SURFACE_LEDGER = ROUTE_DIR / f"{EXECUTION_PREFIX}_SURFACE_LEDGER_2026-05-17.jsonl"
EXECUTION_LEDGER = ROUTE_DIR / f"{EXECUTION_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
MATCH_LEDGER = ROUTE_DIR / f"{EXECUTION_PREFIX}_MATCH_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_expanded_market_reduced_implementation_candidates.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_expanded_market_reduced_implementation_candidates_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
CANDIDATE_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
EVIDENCE_LEDGER = ROUTE_DIR / f"{PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"
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
        (RESULT_PATH, "expanded_market_reduced_implementation_candidates_result"),
        (CANDIDATE_LEDGER, "expanded_market_reduced_implementation_candidate_rows"),
        (EVIDENCE_LEDGER, "expanded_market_reduced_implementation_candidate_evidence"),
        (AGGREGATE_LEDGER, "expanded_market_reduced_implementation_candidate_aggregates"),
        (SYSTEM_LEDGER, "expanded_market_reduced_implementation_candidate_system"),
        (SUMMARY_PATH, "expanded_market_reduced_implementation_candidates_summary"),
        (BUILDER_MODULE, "expanded_market_reduced_implementation_candidates_builder"),
        (VERIFIER_MODULE, "expanded_market_reduced_implementation_candidates_verifier"),
        (HELPER_MODULE, "expanded_market_reduced_implementation_candidates_helper"),
        (TEST_MODULE, "expanded_market_reduced_implementation_candidates_tests"),
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
    manifest["latest_expanded_market_reduced_implementation_candidates"] = {
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
                if payload.get("checkpoint") == 225 and payload.get("event") == "expanded_market_reduced_implementation_candidates":
                    continue
                kept_lines.append(stripped)
    kept_lines.append(json.dumps(event, sort_keys=True))
    with open(long_path(SPRINT_LEDGER), "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(kept_lines) + "\n")


def replace_active_checkpoint(generated_at: str, counts: dict[str, Any]) -> None:
    marker = "## Checkpoint 225 - Expanded-Market Reduced Implementation Candidates"
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

Trigger: direct continuation after Checkpoint 224. Passing reduced-surface executions were collapsed into row-level branch-local implementation candidates while preserving replay geometry and evidence rows.

Rows:
- input reduced-surface execution rows: {counts['input_execution_rows']}
- input reduced-surface execution match rows: {counts['input_match_rows']}
- implementation candidate rows: {counts['implementation_candidate_rows']}
- implementation candidate evidence rows: {counts['implementation_candidate_evidence_rows']}
- aggregate rows: {counts['aggregate_rows']}
- ready candidate rows: {counts['ready_candidate_rows']}
- redesign candidate rows: {counts['redesign_candidate_rows']}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: execute or package these implementation candidates into final branch-local implementation artifacts with all replay evidence still row-addressable.
"""
    with open(long_path(ACTIVE_LEDGER), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text.rstrip() + "\n\n" + addition.strip() + "\n")


def build_summary(counts: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Expanded-Market Reduced Implementation Candidates",
            "",
            "This checkpoint collapses passing reduced-surface executions into row-level branch-local implementation candidates and evidence rows.",
            "",
            "## Counts",
            "",
            f"- Input reduced-surface execution rows: `{counts['input_execution_rows']}`",
            f"- Input reduced-surface execution match rows: `{counts['input_match_rows']}`",
            f"- Implementation candidate rows: `{counts['implementation_candidate_rows']}`",
            f"- Implementation candidate evidence rows: `{counts['implementation_candidate_evidence_rows']}`",
            f"- Aggregate rows: `{counts['aggregate_rows']}`",
            f"- Ready candidate rows: `{counts['ready_candidate_rows']}`",
            f"- Redesign candidate rows: `{counts['redesign_candidate_rows']}`",
            "",
            "## Decisions",
            "",
            f"`{json.dumps(counts['decision_counts'], sort_keys=True)}`",
            "",
            "## Continuation",
            "",
            "Execute or package these implementation candidates into final branch-local implementation artifacts with all replay evidence row-addressable.",
            "",
        ]
    )


def main() -> None:
    generated_at = now_utc()
    execution_result = read_json(EXECUTION_RESULT)
    surfaces = read_jsonl(SURFACE_LEDGER)
    executions = read_jsonl(EXECUTION_LEDGER)
    matches = read_jsonl(MATCH_LEDGER)
    candidates, evidence = implementation_candidate_rows(surfaces, executions, matches)
    aggregates = aggregate_candidate_rows(candidates)
    system_rows = system_candidate_rows(candidates, evidence, aggregates, len(executions), len(matches))
    decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in candidates)
    counts = {
        "input_result_ok": bool(execution_result.get("ok")),
        "input_surface_rows": len(surfaces),
        "input_execution_rows": len(executions),
        "input_match_rows": len(matches),
        "implementation_candidate_rows": len(candidates),
        "implementation_candidate_evidence_rows": len(evidence),
        "aggregate_rows": len(aggregates),
        "system_rows": len(system_rows),
        "ready_candidate_rows": sum(
            1 for row in candidates if row.get("implementation_candidate_status") == "IMPLEMENTATION_CANDIDATE_READY"
        ),
        "redesign_candidate_rows": sum(
            1 for row in candidates if row.get("implementation_candidate_status") == "IMPLEMENTATION_CANDIDATE_REDESIGN"
        ),
        "decision_counts": dict(sorted(decisions.items())),
    }
    write_jsonl(CANDIDATE_LEDGER, candidates)
    write_jsonl(EVIDENCE_LEDGER, evidence)
    write_jsonl(AGGREGATE_LEDGER, aggregates)
    write_jsonl(SYSTEM_LEDGER, system_rows)
    write_text(SUMMARY_PATH, build_summary(counts))
    output_files = [CANDIDATE_LEDGER, EVIDENCE_LEDGER, AGGREGATE_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]
    result = {
        "ok": True,
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "counts": counts,
        "inputs": {
            "execution_result": str(EXECUTION_RESULT.relative_to(REPO)).replace("\\", "/"),
            "surface_ledger": str(SURFACE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "execution_ledger": str(EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "match_ledger": str(MATCH_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "candidate_ledger": str(CANDIDATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "evidence_ledger": str(EVIDENCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
        "output_sha256": output_sha256(output_files),
        "research_boundary": research_boundary(),
        "expanded_market_reduced_implementation_candidates_surface": (
            EXPANDED_MARKET_REDUCED_IMPLEMENTATION_CANDIDATES_SURFACE
        ),
    }
    write_json(RESULT_PATH, result)
    update_manifest(generated_at)
    replace_sprint_event(
        {
            "checkpoint": 225,
            "event": "expanded_market_reduced_implementation_candidates",
            "generated_utc": generated_at,
            "input_execution_rows": counts["input_execution_rows"],
            "implementation_candidate_rows": counts["implementation_candidate_rows"],
            "implementation_candidate_evidence_rows": counts["implementation_candidate_evidence_rows"],
            "aggregate_rows": counts["aggregate_rows"],
            "ready_candidate_rows": counts["ready_candidate_rows"],
            "redesign_candidate_rows": counts["redesign_candidate_rows"],
            "continuation": "continue to final branch-local implementation artifacts with row-addressable replay evidence.",
            "boundary": research_boundary(),
        }
    )
    replace_active_checkpoint(generated_at, counts)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
