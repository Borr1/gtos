#!/usr/bin/env python3
"""Execute branch-local implementation review over expanded-market package slices."""

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

from src.research_infra.moonshot_expanded_market_package_review_execution import (
    EXPANDED_MARKET_PACKAGE_REVIEW_EXECUTION_SURFACE,
    aggregate_review_artifact_rows,
    package_review_execution_rows,
    research_boundary,
    system_review_execution_rows,
)


PACKAGE_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_PACKAGE_SLICES"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_PACKAGE_REVIEW_EXECUTION"

PACKAGE_RESULT = ROUTE_DIR / f"{PACKAGE_PREFIX}_RESULT_2026-05-17.json"
PACKAGE_SLICE_LEDGER = ROUTE_DIR / f"{PACKAGE_PREFIX}_SLICE_LEDGER_2026-05-17.jsonl"
PACKAGE_MEMBER_LEDGER = ROUTE_DIR / f"{PACKAGE_PREFIX}_MEMBER_LEDGER_2026-05-17.jsonl"
PACKAGE_EVIDENCE_LEDGER = ROUTE_DIR / f"{PACKAGE_PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"
PACKAGE_REDESIGN_LEDGER = ROUTE_DIR / f"{PACKAGE_PREFIX}_REDESIGN_CARRY_LEDGER_2026-05-17.jsonl"
PACKAGE_CONTROL_LEDGER = ROUTE_DIR / f"{PACKAGE_PREFIX}_CONTROL_LEDGER_2026-05-17.jsonl"
PACKAGE_SELF_TEST_LEDGER = ROUTE_DIR / f"{PACKAGE_PREFIX}_SELF_TEST_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_expanded_market_package_review_execution.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_expanded_market_package_review_execution_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
ARTIFACT_LEDGER = ROUTE_DIR / f"{PREFIX}_ARTIFACT_LEDGER_2026-05-17.jsonl"
MEMBER_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_MEMBER_EXECUTION_LEDGER_2026-05-17.jsonl"
EVIDENCE_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_EVIDENCE_EXECUTION_LEDGER_2026-05-17.jsonl"
REDESIGN_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_REDESIGN_EXECUTION_LEDGER_2026-05-17.jsonl"
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
        (RESULT_PATH, "expanded_market_package_review_result"),
        (ARTIFACT_LEDGER, "expanded_market_package_review_artifacts"),
        (MEMBER_EXECUTION_LEDGER, "expanded_market_package_review_members"),
        (EVIDENCE_EXECUTION_LEDGER, "expanded_market_package_review_evidence"),
        (REDESIGN_EXECUTION_LEDGER, "expanded_market_package_review_redesign"),
        (CONTROL_LEDGER, "expanded_market_package_review_controls"),
        (AGGREGATE_LEDGER, "expanded_market_package_review_aggregates"),
        (SYSTEM_LEDGER, "expanded_market_package_review_system"),
        (SUMMARY_PATH, "expanded_market_package_review_summary"),
        (BUILDER_MODULE, "expanded_market_package_review_builder"),
        (VERIFIER_MODULE, "expanded_market_package_review_verifier"),
        (HELPER_MODULE, "expanded_market_package_review_helper"),
        (TEST_MODULE, "expanded_market_package_review_tests"),
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
    manifest["latest_expanded_market_package_review_execution"] = {
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
                if payload.get("checkpoint") == 231 and payload.get("event") == "expanded_market_package_review_execution":
                    continue
                kept_lines.append(stripped)
    kept_lines.append(json.dumps(event, sort_keys=True))
    with open(long_path(SPRINT_LEDGER), "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(kept_lines) + "\n")


def replace_active_checkpoint(generated_at: str, counts: dict[str, Any]) -> None:
    marker = "## Checkpoint 231 - Expanded-Market Package Review Execution"
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

Trigger: direct continuation after Checkpoint 230. Package slices were executed into branch-local implementation-review artifacts with member, evidence, redesign, and control execution rows.

Rows:
- input package slice rows: {counts['input_package_slice_rows']}
- input package member rows: {counts['input_package_member_rows']}
- input package evidence rows: {counts['input_package_evidence_rows']}
- input package redesign carry rows: {counts['input_package_redesign_carry_rows']}
- package review artifact rows: {counts['package_review_artifact_rows']}
- package review member execution rows: {counts['package_review_member_execution_rows']}
- package review evidence execution rows: {counts['package_review_evidence_execution_rows']}
- package review redesign execution rows: {counts['package_review_redesign_execution_rows']}
- package review control rows: {counts['package_review_control_rows']}
- aggregate rows: {counts['aggregate_rows']}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: consume package-review artifacts into implementation-review recommendations or branch-local execution preservation rows.
"""
    with open(long_path(ACTIVE_LEDGER), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text.rstrip() + "\n\n" + addition.strip() + "\n")


def build_summary(counts: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Expanded-Market Package Review Execution",
            "",
            "This checkpoint executes package slices into branch-local implementation-review artifacts and preserves every member, evidence, and redesign row.",
            "",
            "## Counts",
            "",
            f"- Input package slice rows: `{counts['input_package_slice_rows']}`",
            f"- Input package member rows: `{counts['input_package_member_rows']}`",
            f"- Input package evidence rows: `{counts['input_package_evidence_rows']}`",
            f"- Input package redesign carry rows: `{counts['input_package_redesign_carry_rows']}`",
            f"- Package review artifact rows: `{counts['package_review_artifact_rows']}`",
            f"- Package review member execution rows: `{counts['package_review_member_execution_rows']}`",
            f"- Package review evidence execution rows: `{counts['package_review_evidence_execution_rows']}`",
            f"- Package review redesign execution rows: `{counts['package_review_redesign_execution_rows']}`",
            f"- Package review control rows: `{counts['package_review_control_rows']}`",
            f"- Aggregate rows: `{counts['aggregate_rows']}`",
            f"- Artifact pass rows: `{counts['artifact_pass_rows']}`",
            "",
            "## Continuation",
            "",
            "Consume package-review artifacts into implementation-review recommendations or branch-local execution preservation rows.",
            "",
        ]
    )


def main() -> None:
    generated_at = now_utc()
    package_result = read_json(PACKAGE_RESULT)
    packages = read_jsonl(PACKAGE_SLICE_LEDGER)
    members = read_jsonl(PACKAGE_MEMBER_LEDGER)
    evidence = read_jsonl(PACKAGE_EVIDENCE_LEDGER)
    redesign = read_jsonl(PACKAGE_REDESIGN_LEDGER)
    controls = read_jsonl(PACKAGE_CONTROL_LEDGER)
    self_tests = read_jsonl(PACKAGE_SELF_TEST_LEDGER)
    artifacts, member_exec, evidence_exec, redesign_exec, control_exec = package_review_execution_rows(
        packages, members, evidence, redesign, controls, self_tests
    )
    aggregates = aggregate_review_artifact_rows(artifacts)
    system_rows = system_review_execution_rows(
        artifacts, member_exec, evidence_exec, redesign_exec, control_exec, aggregates,
        len(packages), len(members), len(evidence), len(redesign)
    )
    counts = {
        "input_result_ok": bool(package_result.get("ok")),
        "input_package_slice_rows": len(packages),
        "input_package_member_rows": len(members),
        "input_package_evidence_rows": len(evidence),
        "input_package_redesign_carry_rows": len(redesign),
        "package_review_artifact_rows": len(artifacts),
        "package_review_member_execution_rows": len(member_exec),
        "package_review_evidence_execution_rows": len(evidence_exec),
        "package_review_redesign_execution_rows": len(redesign_exec),
        "package_review_control_rows": len(control_exec),
        "aggregate_rows": len(aggregates),
        "system_rows": len(system_rows),
        "artifact_pass_rows": sum(1 for row in artifacts if row.get("package_review_execution_status") == "PACKAGE_REVIEW_EXECUTION_PASS"),
        "member_pass_rows": sum(1 for row in member_exec if row.get("package_review_member_execution_status") == "PACKAGE_REVIEW_MEMBER_EXECUTION_PASS"),
        "evidence_pass_rows": sum(1 for row in evidence_exec if row.get("package_review_evidence_execution_status") == "PACKAGE_REVIEW_EVIDENCE_EXECUTION_PASS"),
    }
    write_jsonl(ARTIFACT_LEDGER, artifacts)
    write_jsonl(MEMBER_EXECUTION_LEDGER, member_exec)
    write_jsonl(EVIDENCE_EXECUTION_LEDGER, evidence_exec)
    write_jsonl(REDESIGN_EXECUTION_LEDGER, redesign_exec)
    write_jsonl(CONTROL_LEDGER, control_exec)
    write_jsonl(AGGREGATE_LEDGER, aggregates)
    write_jsonl(SYSTEM_LEDGER, system_rows)
    write_text(SUMMARY_PATH, build_summary(counts))
    output_files = [ARTIFACT_LEDGER, MEMBER_EXECUTION_LEDGER, EVIDENCE_EXECUTION_LEDGER, REDESIGN_EXECUTION_LEDGER, CONTROL_LEDGER, AGGREGATE_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]
    result = {
        "ok": True,
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "counts": counts,
        "inputs": {
            "package_result": str(PACKAGE_RESULT.relative_to(REPO)).replace("\\", "/"),
            "package_slice_ledger": str(PACKAGE_SLICE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "package_member_ledger": str(PACKAGE_MEMBER_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "package_evidence_ledger": str(PACKAGE_EVIDENCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "package_redesign_ledger": str(PACKAGE_REDESIGN_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "artifact_ledger": str(ARTIFACT_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "member_execution_ledger": str(MEMBER_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "evidence_execution_ledger": str(EVIDENCE_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "redesign_execution_ledger": str(REDESIGN_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "control_ledger": str(CONTROL_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
        "output_sha256": output_sha256(output_files),
        "research_boundary": research_boundary(),
        "expanded_market_package_review_execution_surface": EXPANDED_MARKET_PACKAGE_REVIEW_EXECUTION_SURFACE,
    }
    write_json(RESULT_PATH, result)
    update_manifest(generated_at)
    replace_sprint_event({
        "checkpoint": 231,
        "event": "expanded_market_package_review_execution",
        "generated_utc": generated_at,
        "input_package_slice_rows": counts["input_package_slice_rows"],
        "package_review_artifact_rows": counts["package_review_artifact_rows"],
        "package_review_member_execution_rows": counts["package_review_member_execution_rows"],
        "package_review_redesign_execution_rows": counts["package_review_redesign_execution_rows"],
        "continuation": "continue to package-review recommendations or execution preservation.",
        "boundary": research_boundary(),
    })
    replace_active_checkpoint(generated_at, counts)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
