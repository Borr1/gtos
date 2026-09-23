#!/usr/bin/env python3
"""Build final branch-local implementation decisions from preserved package reviews."""

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

from src.research_infra.moonshot_expanded_market_final_implementation_decisions import (
    EXPANDED_MARKET_FINAL_IMPLEMENTATION_DECISIONS_SURFACE,
    aggregate_final_implementation_decision_rows,
    final_implementation_decision_rows,
    research_boundary,
    system_final_implementation_decision_rows,
)


PRESERVATION_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_PACKAGE_REVIEW_PRESERVATION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_FINAL_IMPLEMENTATION_DECISIONS"

PRESERVATION_RESULT = ROUTE_DIR / f"{PRESERVATION_PREFIX}_RESULT_2026-05-17.json"
CANDIDATE_LEDGER = ROUTE_DIR / f"{PRESERVATION_PREFIX}_CANDIDATE_LEDGER_2026-05-17.jsonl"
MEMBER_LEDGER = ROUTE_DIR / f"{PRESERVATION_PREFIX}_MEMBER_LEDGER_2026-05-17.jsonl"
EVIDENCE_LEDGER = ROUTE_DIR / f"{PRESERVATION_PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"
REDESIGN_LEDGER = ROUTE_DIR / f"{PRESERVATION_PREFIX}_REDESIGN_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_expanded_market_final_implementation_decisions.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_expanded_market_final_implementation_decisions_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
DECISION_LEDGER = ROUTE_DIR / f"{PREFIX}_DECISION_LEDGER_2026-05-17.jsonl"
MEMBER_DECISION_LEDGER = ROUTE_DIR / f"{PREFIX}_MEMBER_LEDGER_2026-05-17.jsonl"
EVIDENCE_DECISION_LEDGER = ROUTE_DIR / f"{PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"
REDESIGN_DECISION_LEDGER = ROUTE_DIR / f"{PREFIX}_REDESIGN_LEDGER_2026-05-17.jsonl"
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
        (RESULT_PATH, "expanded_market_final_implementation_decisions_result"),
        (DECISION_LEDGER, "expanded_market_final_implementation_decisions"),
        (MEMBER_DECISION_LEDGER, "expanded_market_final_implementation_decision_members"),
        (EVIDENCE_DECISION_LEDGER, "expanded_market_final_implementation_decision_evidence"),
        (REDESIGN_DECISION_LEDGER, "expanded_market_final_implementation_decision_redesign"),
        (CONTROL_LEDGER, "expanded_market_final_implementation_decision_controls"),
        (AGGREGATE_LEDGER, "expanded_market_final_implementation_decision_aggregates"),
        (SYSTEM_LEDGER, "expanded_market_final_implementation_decision_system"),
        (SUMMARY_PATH, "expanded_market_final_implementation_decision_summary"),
        (BUILDER_MODULE, "expanded_market_final_implementation_decision_builder"),
        (VERIFIER_MODULE, "expanded_market_final_implementation_decision_verifier"),
        (HELPER_MODULE, "expanded_market_final_implementation_decision_helper"),
        (TEST_MODULE, "expanded_market_final_implementation_decision_tests"),
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
    manifest["latest_expanded_market_final_implementation_decisions"] = {
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
                if payload.get("checkpoint") == 233 and payload.get("event") == "expanded_market_final_implementation_decisions":
                    continue
                kept_lines.append(stripped)
    kept_lines.append(json.dumps(event, sort_keys=True))
    with open(long_path(SPRINT_LEDGER), "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(kept_lines) + "\n")


def replace_active_checkpoint(generated_at: str, counts: dict[str, Any]) -> None:
    marker = "## Checkpoint 233 - Expanded-Market Final Implementation Decisions"
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

Trigger: direct continuation after Checkpoint 232. Preservation candidates were converted into final branch-local implementation decision rows while member, evidence, and terminal redesign rows stayed row-addressable.

Rows:
- input package-preservation candidate rows: {counts['input_package_preservation_candidate_rows']}
- input package-preservation member rows: {counts['input_package_preservation_member_rows']}
- input package-preservation evidence rows: {counts['input_package_preservation_evidence_rows']}
- input package-preservation redesign rows: {counts['input_package_preservation_redesign_rows']}
- final implementation decision rows: {counts['final_implementation_decision_rows']}
- final implementation member rows: {counts['final_implementation_member_rows']}
- final implementation evidence rows: {counts['final_implementation_evidence_rows']}
- final implementation redesign rows: {counts['final_implementation_redesign_rows']}
- final implementation control rows: {counts['final_implementation_control_rows']}
- aggregate rows: {counts['aggregate_rows']}
- ready final implementation decision rows: {counts['ready_final_implementation_decision_rows']}
- unpackaged evidence rows preserved as redesign evidence: {counts['unpackaged_evidence_rows']}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: continue to branch-local implementation-decision evidence export or the next numeric replay plate with all terminal redesign rows preserved.
"""
    with open(long_path(ACTIVE_LEDGER), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text.rstrip() + "\n\n" + addition.strip() + "\n")


def build_summary(counts: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Expanded-Market Final Implementation Decisions",
            "",
            "This checkpoint converts preserved package-review candidates into final branch-local implementation decision rows and keeps every member, evidence, and terminal redesign row addressable.",
            "",
            "## Counts",
            "",
            f"- Input package-preservation candidate rows: `{counts['input_package_preservation_candidate_rows']}`",
            f"- Input package-preservation member rows: `{counts['input_package_preservation_member_rows']}`",
            f"- Input package-preservation evidence rows: `{counts['input_package_preservation_evidence_rows']}`",
            f"- Input package-preservation redesign rows: `{counts['input_package_preservation_redesign_rows']}`",
            f"- Final implementation decision rows: `{counts['final_implementation_decision_rows']}`",
            f"- Final implementation member rows: `{counts['final_implementation_member_rows']}`",
            f"- Final implementation evidence rows: `{counts['final_implementation_evidence_rows']}`",
            f"- Final implementation redesign rows: `{counts['final_implementation_redesign_rows']}`",
            f"- Final implementation control rows: `{counts['final_implementation_control_rows']}`",
            f"- Aggregate rows: `{counts['aggregate_rows']}`",
            f"- Ready final implementation decision rows: `{counts['ready_final_implementation_decision_rows']}`",
            f"- Evidence pass rows: `{counts['evidence_pass_rows']}`",
            f"- Unpackaged evidence rows preserved as redesign evidence: `{counts['unpackaged_evidence_rows']}`",
            f"- Terminal redesign rows: `{counts['terminal_redesign_rows']}`",
            "",
            "## Continuation",
            "",
            "Continue to branch-local implementation-decision evidence export or the next numeric replay plate with all terminal redesign rows preserved.",
            "",
        ]
    )


def main() -> None:
    generated_at = now_utc()
    preservation_result = read_json(PRESERVATION_RESULT)
    candidates = read_jsonl(CANDIDATE_LEDGER)
    members = read_jsonl(MEMBER_LEDGER)
    evidence = read_jsonl(EVIDENCE_LEDGER)
    redesign = read_jsonl(REDESIGN_LEDGER)
    decisions, decision_members, decision_evidence, decision_redesign, controls = final_implementation_decision_rows(
        candidates, members, evidence, redesign
    )
    aggregates = aggregate_final_implementation_decision_rows(decisions)
    system_rows = system_final_implementation_decision_rows(
        decisions,
        decision_members,
        decision_evidence,
        decision_redesign,
        controls,
        aggregates,
        len(candidates),
        len(members),
        len(evidence),
        len(redesign),
    )
    system = system_rows[0]
    counts = {
        "input_result_ok": bool(preservation_result.get("ok")),
        "input_package_preservation_candidate_rows": len(candidates),
        "input_package_preservation_member_rows": len(members),
        "input_package_preservation_evidence_rows": len(evidence),
        "input_package_preservation_redesign_rows": len(redesign),
        "final_implementation_decision_rows": len(decisions),
        "final_implementation_member_rows": len(decision_members),
        "final_implementation_evidence_rows": len(decision_evidence),
        "final_implementation_redesign_rows": len(decision_redesign),
        "final_implementation_control_rows": len(controls),
        "aggregate_rows": len(aggregates),
        "system_rows": len(system_rows),
        "ready_final_implementation_decision_rows": system["ready_final_implementation_decision_rows"],
        "member_pass_rows": system["member_pass_rows"],
        "evidence_pass_rows": system["evidence_pass_rows"],
        "unpackaged_evidence_rows": system["unpackaged_evidence_rows"],
        "terminal_redesign_rows": system["terminal_redesign_rows"],
        "control_pass_rows": system["control_pass_rows"],
    }
    write_jsonl(DECISION_LEDGER, decisions)
    write_jsonl(MEMBER_DECISION_LEDGER, decision_members)
    write_jsonl(EVIDENCE_DECISION_LEDGER, decision_evidence)
    write_jsonl(REDESIGN_DECISION_LEDGER, decision_redesign)
    write_jsonl(CONTROL_LEDGER, controls)
    write_jsonl(AGGREGATE_LEDGER, aggregates)
    write_jsonl(SYSTEM_LEDGER, system_rows)
    write_text(SUMMARY_PATH, build_summary(counts))
    output_files = [
        DECISION_LEDGER,
        MEMBER_DECISION_LEDGER,
        EVIDENCE_DECISION_LEDGER,
        REDESIGN_DECISION_LEDGER,
        CONTROL_LEDGER,
        AGGREGATE_LEDGER,
        SYSTEM_LEDGER,
        SUMMARY_PATH,
    ]
    result = {
        "ok": True,
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "counts": counts,
        "inputs": {
            "package_preservation_result": str(PRESERVATION_RESULT.relative_to(REPO)).replace("\\", "/"),
            "candidate_ledger": str(CANDIDATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "member_ledger": str(MEMBER_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "evidence_ledger": str(EVIDENCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "redesign_ledger": str(REDESIGN_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "decision_ledger": str(DECISION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "member_ledger": str(MEMBER_DECISION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "evidence_ledger": str(EVIDENCE_DECISION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "redesign_ledger": str(REDESIGN_DECISION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "control_ledger": str(CONTROL_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
        "output_sha256": output_sha256(output_files),
        "research_boundary": research_boundary(),
        "expanded_market_final_implementation_decisions_surface": (
            EXPANDED_MARKET_FINAL_IMPLEMENTATION_DECISIONS_SURFACE
        ),
    }
    write_json(RESULT_PATH, result)
    update_manifest(generated_at)
    replace_sprint_event(
        {
            "checkpoint": 233,
            "event": "expanded_market_final_implementation_decisions",
            "generated_utc": generated_at,
            "input_package_preservation_candidate_rows": counts["input_package_preservation_candidate_rows"],
            "final_implementation_decision_rows": counts["final_implementation_decision_rows"],
            "final_implementation_member_rows": counts["final_implementation_member_rows"],
            "final_implementation_evidence_rows": counts["final_implementation_evidence_rows"],
            "final_implementation_redesign_rows": counts["final_implementation_redesign_rows"],
            "unpackaged_evidence_rows": counts["unpackaged_evidence_rows"],
            "continuation": "continue to implementation-decision evidence export or next numeric replay plate.",
            "boundary": research_boundary(),
        }
    )
    replace_active_checkpoint(generated_at, counts)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
