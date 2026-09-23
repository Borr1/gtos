#!/usr/bin/env python3
"""Preserve expanded-market package-review execution into implementation candidates."""

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

from src.research_infra.moonshot_expanded_market_package_review_preservation import (
    EXPANDED_MARKET_PACKAGE_REVIEW_PRESERVATION_SURFACE,
    aggregate_preservation_rows,
    package_review_preservation_rows,
    research_boundary,
    system_preservation_rows,
)


REVIEW_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_PACKAGE_REVIEW_EXECUTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_PACKAGE_REVIEW_PRESERVATION"

REVIEW_RESULT = ROUTE_DIR / f"{REVIEW_PREFIX}_RESULT_2026-05-17.json"
ARTIFACT_LEDGER = ROUTE_DIR / f"{REVIEW_PREFIX}_ARTIFACT_LEDGER_2026-05-17.jsonl"
MEMBER_LEDGER = ROUTE_DIR / f"{REVIEW_PREFIX}_MEMBER_EXECUTION_LEDGER_2026-05-17.jsonl"
EVIDENCE_LEDGER = ROUTE_DIR / f"{REVIEW_PREFIX}_EVIDENCE_EXECUTION_LEDGER_2026-05-17.jsonl"
REDESIGN_LEDGER = ROUTE_DIR / f"{REVIEW_PREFIX}_REDESIGN_EXECUTION_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_expanded_market_package_review_preservation.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_expanded_market_package_review_preservation_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
CANDIDATE_LEDGER = ROUTE_DIR / f"{PREFIX}_CANDIDATE_LEDGER_2026-05-17.jsonl"
MEMBER_PRESERVATION_LEDGER = ROUTE_DIR / f"{PREFIX}_MEMBER_LEDGER_2026-05-17.jsonl"
EVIDENCE_PRESERVATION_LEDGER = ROUTE_DIR / f"{PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"
REDESIGN_PRESERVATION_LEDGER = ROUTE_DIR / f"{PREFIX}_REDESIGN_LEDGER_2026-05-17.jsonl"
SELF_TEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SELF_TEST_LEDGER_2026-05-17.jsonl"
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
        (RESULT_PATH, "expanded_market_package_review_preservation_result"),
        (CANDIDATE_LEDGER, "expanded_market_package_review_preservation_candidates"),
        (MEMBER_PRESERVATION_LEDGER, "expanded_market_package_review_preservation_members"),
        (EVIDENCE_PRESERVATION_LEDGER, "expanded_market_package_review_preservation_evidence"),
        (REDESIGN_PRESERVATION_LEDGER, "expanded_market_package_review_preservation_redesign"),
        (SELF_TEST_LEDGER, "expanded_market_package_review_preservation_self_tests"),
        (AGGREGATE_LEDGER, "expanded_market_package_review_preservation_aggregates"),
        (SYSTEM_LEDGER, "expanded_market_package_review_preservation_system"),
        (SUMMARY_PATH, "expanded_market_package_review_preservation_summary"),
        (BUILDER_MODULE, "expanded_market_package_review_preservation_builder"),
        (VERIFIER_MODULE, "expanded_market_package_review_preservation_verifier"),
        (HELPER_MODULE, "expanded_market_package_review_preservation_helper"),
        (TEST_MODULE, "expanded_market_package_review_preservation_tests"),
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
    manifest["latest_expanded_market_package_review_preservation"] = {
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
                if payload.get("checkpoint") == 232 and payload.get("event") == "expanded_market_package_review_preservation":
                    continue
                kept_lines.append(stripped)
    kept_lines.append(json.dumps(event, sort_keys=True))
    with open(long_path(SPRINT_LEDGER), "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(kept_lines) + "\n")


def replace_active_checkpoint(generated_at: str, counts: dict[str, Any]) -> None:
    marker = "## Checkpoint 232 - Expanded-Market Package Review Preservation"
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

Trigger: direct continuation after Checkpoint 231. Passing package-review artifacts were preserved as branch-local implementation candidates with member, evidence, redesign, and self-test rows.

Rows:
- input package-review artifact rows: {counts['input_package_review_artifact_rows']}
- input package-review member execution rows: {counts['input_package_review_member_execution_rows']}
- input package-review evidence execution rows: {counts['input_package_review_evidence_execution_rows']}
- input package-review redesign execution rows: {counts['input_package_review_redesign_execution_rows']}
- package preservation candidate rows: {counts['package_preservation_candidate_rows']}
- package preservation member rows: {counts['package_preservation_member_rows']}
- package preservation evidence rows: {counts['package_preservation_evidence_rows']}
- package preservation redesign rows: {counts['package_preservation_redesign_rows']}
- package preservation self-test rows: {counts['package_preservation_self_test_rows']}
- aggregate rows: {counts['aggregate_rows']}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: execute preservation candidates into final branch-local implementation decision rows.
"""
    with open(long_path(ACTIVE_LEDGER), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text.rstrip() + "\n\n" + addition.strip() + "\n")


def build_summary(counts: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Expanded-Market Package Review Preservation",
            "",
            "This checkpoint preserves passing package-review artifacts as branch-local implementation candidates and keeps every member, evidence, and redesign row addressable.",
            "",
            "## Counts",
            "",
            f"- Input package-review artifact rows: `{counts['input_package_review_artifact_rows']}`",
            f"- Input package-review member execution rows: `{counts['input_package_review_member_execution_rows']}`",
            f"- Input package-review evidence execution rows: `{counts['input_package_review_evidence_execution_rows']}`",
            f"- Input package-review redesign execution rows: `{counts['input_package_review_redesign_execution_rows']}`",
            f"- Package preservation candidate rows: `{counts['package_preservation_candidate_rows']}`",
            f"- Package preservation member rows: `{counts['package_preservation_member_rows']}`",
            f"- Package preservation evidence rows: `{counts['package_preservation_evidence_rows']}`",
            f"- Package preservation redesign rows: `{counts['package_preservation_redesign_rows']}`",
            f"- Package preservation self-test rows: `{counts['package_preservation_self_test_rows']}`",
            f"- Aggregate rows: `{counts['aggregate_rows']}`",
            f"- Ready candidate rows: `{counts['ready_candidate_rows']}`",
            "",
            "## Continuation",
            "",
            "Execute preservation candidates into final branch-local implementation decision rows.",
            "",
        ]
    )


def main() -> None:
    generated_at = now_utc()
    review_result = read_json(REVIEW_RESULT)
    artifacts = read_jsonl(ARTIFACT_LEDGER)
    members = read_jsonl(MEMBER_LEDGER)
    evidence = read_jsonl(EVIDENCE_LEDGER)
    redesign = read_jsonl(REDESIGN_LEDGER)
    candidates, preserved_members, preserved_evidence, preserved_redesign, self_tests = package_review_preservation_rows(
        artifacts, members, evidence, redesign
    )
    aggregates = aggregate_preservation_rows(candidates)
    system_rows = system_preservation_rows(
        candidates, preserved_members, preserved_evidence, preserved_redesign, self_tests, aggregates,
        len(artifacts), len(members), len(evidence), len(redesign)
    )
    counts = {
        "input_result_ok": bool(review_result.get("ok")),
        "input_package_review_artifact_rows": len(artifacts),
        "input_package_review_member_execution_rows": len(members),
        "input_package_review_evidence_execution_rows": len(evidence),
        "input_package_review_redesign_execution_rows": len(redesign),
        "package_preservation_candidate_rows": len(candidates),
        "package_preservation_member_rows": len(preserved_members),
        "package_preservation_evidence_rows": len(preserved_evidence),
        "package_preservation_redesign_rows": len(preserved_redesign),
        "package_preservation_self_test_rows": len(self_tests),
        "aggregate_rows": len(aggregates),
        "system_rows": len(system_rows),
        "ready_candidate_rows": sum(1 for row in candidates if row.get("preservation_status") == "PACKAGE_REVIEW_PRESERVATION_READY"),
        "self_test_pass_rows": sum(1 for row in self_tests if row.get("self_test_status") == "PACKAGE_REVIEW_PRESERVATION_SELF_TEST_PASS"),
    }
    write_jsonl(CANDIDATE_LEDGER, candidates)
    write_jsonl(MEMBER_PRESERVATION_LEDGER, preserved_members)
    write_jsonl(EVIDENCE_PRESERVATION_LEDGER, preserved_evidence)
    write_jsonl(REDESIGN_PRESERVATION_LEDGER, preserved_redesign)
    write_jsonl(SELF_TEST_LEDGER, self_tests)
    write_jsonl(AGGREGATE_LEDGER, aggregates)
    write_jsonl(SYSTEM_LEDGER, system_rows)
    write_text(SUMMARY_PATH, build_summary(counts))
    output_files = [CANDIDATE_LEDGER, MEMBER_PRESERVATION_LEDGER, EVIDENCE_PRESERVATION_LEDGER, REDESIGN_PRESERVATION_LEDGER, SELF_TEST_LEDGER, AGGREGATE_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]
    result = {
        "ok": True,
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "counts": counts,
        "inputs": {
            "package_review_result": str(REVIEW_RESULT.relative_to(REPO)).replace("\\", "/"),
            "artifact_ledger": str(ARTIFACT_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "member_execution_ledger": str(MEMBER_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "evidence_execution_ledger": str(EVIDENCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "redesign_execution_ledger": str(REDESIGN_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "candidate_ledger": str(CANDIDATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "member_ledger": str(MEMBER_PRESERVATION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "evidence_ledger": str(EVIDENCE_PRESERVATION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "redesign_ledger": str(REDESIGN_PRESERVATION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "self_test_ledger": str(SELF_TEST_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
        "output_sha256": output_sha256(output_files),
        "research_boundary": research_boundary(),
        "expanded_market_package_review_preservation_surface": EXPANDED_MARKET_PACKAGE_REVIEW_PRESERVATION_SURFACE,
    }
    write_json(RESULT_PATH, result)
    update_manifest(generated_at)
    replace_sprint_event({
        "checkpoint": 232,
        "event": "expanded_market_package_review_preservation",
        "generated_utc": generated_at,
        "input_package_review_artifact_rows": counts["input_package_review_artifact_rows"],
        "package_preservation_candidate_rows": counts["package_preservation_candidate_rows"],
        "package_preservation_member_rows": counts["package_preservation_member_rows"],
        "package_preservation_redesign_rows": counts["package_preservation_redesign_rows"],
        "continuation": "continue to final branch-local implementation decision rows.",
        "boundary": research_boundary(),
    })
    replace_active_checkpoint(generated_at, counts)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
