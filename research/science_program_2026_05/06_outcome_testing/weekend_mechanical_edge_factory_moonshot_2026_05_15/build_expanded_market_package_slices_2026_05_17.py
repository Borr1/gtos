#!/usr/bin/env python3
"""Build branch-local package slices from final-review expanded-market rows."""

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

from src.research_infra.moonshot_expanded_market_package_slices import (
    EXPANDED_MARKET_PACKAGE_SLICES_SURFACE,
    aggregate_package_rows,
    package_slice_rows,
    research_boundary,
    system_package_rows,
)


FINAL_REVIEW_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_FINAL_REVIEW_EXECUTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_PACKAGE_SLICES"

FINAL_REVIEW_RESULT = ROUTE_DIR / f"{FINAL_REVIEW_PREFIX}_RESULT_2026-05-17.json"
FINAL_REVIEW_LEDGER = ROUTE_DIR / f"{FINAL_REVIEW_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
FINAL_REVIEW_EVIDENCE_LEDGER = ROUTE_DIR / f"{FINAL_REVIEW_PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_expanded_market_package_slices.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_expanded_market_package_slices_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
SLICE_LEDGER = ROUTE_DIR / f"{PREFIX}_SLICE_LEDGER_2026-05-17.jsonl"
MEMBER_LEDGER = ROUTE_DIR / f"{PREFIX}_MEMBER_LEDGER_2026-05-17.jsonl"
EVIDENCE_LEDGER = ROUTE_DIR / f"{PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"
REDESIGN_LEDGER = ROUTE_DIR / f"{PREFIX}_REDESIGN_CARRY_LEDGER_2026-05-17.jsonl"
CONTROL_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTROL_LEDGER_2026-05-17.jsonl"
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
        (RESULT_PATH, "expanded_market_package_slices_result"),
        (SLICE_LEDGER, "expanded_market_package_slices"),
        (MEMBER_LEDGER, "expanded_market_package_members"),
        (EVIDENCE_LEDGER, "expanded_market_package_evidence"),
        (REDESIGN_LEDGER, "expanded_market_package_redesign_carry"),
        (CONTROL_LEDGER, "expanded_market_package_controls"),
        (SELF_TEST_LEDGER, "expanded_market_package_self_tests"),
        (AGGREGATE_LEDGER, "expanded_market_package_aggregates"),
        (SYSTEM_LEDGER, "expanded_market_package_system"),
        (SUMMARY_PATH, "expanded_market_package_summary"),
        (BUILDER_MODULE, "expanded_market_package_builder"),
        (VERIFIER_MODULE, "expanded_market_package_verifier"),
        (HELPER_MODULE, "expanded_market_package_helper"),
        (TEST_MODULE, "expanded_market_package_tests"),
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
    manifest["latest_expanded_market_package_slices"] = {
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
                if payload.get("checkpoint") == 230 and payload.get("event") == "expanded_market_package_slices":
                    continue
                kept_lines.append(stripped)
    kept_lines.append(json.dumps(event, sort_keys=True))
    with open(long_path(SPRINT_LEDGER), "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(kept_lines) + "\n")


def replace_active_checkpoint(generated_at: str, counts: dict[str, Any]) -> None:
    marker = "## Checkpoint 230 - Expanded-Market Package Slices"
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

Trigger: direct continuation after Checkpoint 229. Final-review implement rows were converted into executable branch-local package slices with member, evidence, control, and self-test rows.

Rows:
- input final-review rows: {counts['input_final_review_rows']}
- input final-review evidence rows: {counts['input_final_review_evidence_rows']}
- package slice rows: {counts['package_slice_rows']}
- package member rows: {counts['package_member_rows']}
- package evidence rows: {counts['package_evidence_rows']}
- package redesign carry rows: {counts['package_redesign_carry_rows']}
- package control rows: {counts['package_control_rows']}
- package self-test rows: {counts['package_self_test_rows']}
- aggregate rows: {counts['aggregate_rows']}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: execute package slices into branch-local implementation-review artifacts or preserve package concentration evidence.
"""
    with open(long_path(ACTIVE_LEDGER), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text.rstrip() + "\n\n" + addition.strip() + "\n")


def build_summary(counts: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Expanded-Market Package Slices",
            "",
            "This checkpoint converts final-review implement rows into executable branch-local package slices and preserves redesign rows as capacity evidence.",
            "",
            "## Counts",
            "",
            f"- Input final-review rows: `{counts['input_final_review_rows']}`",
            f"- Input final-review evidence rows: `{counts['input_final_review_evidence_rows']}`",
            f"- Package slice rows: `{counts['package_slice_rows']}`",
            f"- Package member rows: `{counts['package_member_rows']}`",
            f"- Package evidence rows: `{counts['package_evidence_rows']}`",
            f"- Package redesign carry rows: `{counts['package_redesign_carry_rows']}`",
            f"- Package control rows: `{counts['package_control_rows']}`",
            f"- Package self-test rows: `{counts['package_self_test_rows']}`",
            f"- Aggregate rows: `{counts['aggregate_rows']}`",
            f"- Self-test pass rows: `{counts['self_test_pass_rows']}`",
            f"- Control pass rows: `{counts['control_pass_rows']}`",
            "",
            "## Continuation",
            "",
            "Execute package slices into branch-local implementation-review artifacts or preserve package concentration evidence.",
            "",
        ]
    )


def main() -> None:
    generated_at = now_utc()
    final_review_result = read_json(FINAL_REVIEW_RESULT)
    review_rows = read_jsonl(FINAL_REVIEW_LEDGER)
    review_evidence = read_jsonl(FINAL_REVIEW_EVIDENCE_LEDGER)
    package_rows, members, evidence, redesign, controls, self_tests = package_slice_rows(review_rows, review_evidence)
    aggregates = aggregate_package_rows(package_rows)
    system_rows = system_package_rows(
        package_rows, members, evidence, redesign, controls, self_tests, aggregates, len(review_rows), len(review_evidence)
    )
    counts = {
        "input_result_ok": bool(final_review_result.get("ok")),
        "input_final_review_rows": len(review_rows),
        "input_final_review_evidence_rows": len(review_evidence),
        "package_slice_rows": len(package_rows),
        "package_member_rows": len(members),
        "package_evidence_rows": len(evidence),
        "package_redesign_carry_rows": len(redesign),
        "package_control_rows": len(controls),
        "package_self_test_rows": len(self_tests),
        "aggregate_rows": len(aggregates),
        "system_rows": len(system_rows),
        "self_test_pass_rows": sum(1 for row in self_tests if row.get("self_test_status") == "PACKAGE_SLICE_SELF_TEST_PASS"),
        "control_pass_rows": sum(1 for row in controls if row.get("control_status") == "PACKAGE_CONTROL_PASS"),
    }
    write_jsonl(SLICE_LEDGER, package_rows)
    write_jsonl(MEMBER_LEDGER, members)
    write_jsonl(EVIDENCE_LEDGER, evidence)
    write_jsonl(REDESIGN_LEDGER, redesign)
    write_jsonl(CONTROL_LEDGER, controls)
    write_jsonl(SELF_TEST_LEDGER, self_tests)
    write_jsonl(AGGREGATE_LEDGER, aggregates)
    write_jsonl(SYSTEM_LEDGER, system_rows)
    write_text(SUMMARY_PATH, build_summary(counts))
    output_files = [
        SLICE_LEDGER,
        MEMBER_LEDGER,
        EVIDENCE_LEDGER,
        REDESIGN_LEDGER,
        CONTROL_LEDGER,
        SELF_TEST_LEDGER,
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
            "final_review_result": str(FINAL_REVIEW_RESULT.relative_to(REPO)).replace("\\", "/"),
            "final_review_ledger": str(FINAL_REVIEW_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "final_review_evidence_ledger": str(FINAL_REVIEW_EVIDENCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "slice_ledger": str(SLICE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "member_ledger": str(MEMBER_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "evidence_ledger": str(EVIDENCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "redesign_ledger": str(REDESIGN_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "control_ledger": str(CONTROL_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "self_test_ledger": str(SELF_TEST_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
        "output_sha256": output_sha256(output_files),
        "research_boundary": research_boundary(),
        "expanded_market_package_slices_surface": EXPANDED_MARKET_PACKAGE_SLICES_SURFACE,
    }
    write_json(RESULT_PATH, result)
    update_manifest(generated_at)
    replace_sprint_event(
        {
            "checkpoint": 230,
            "event": "expanded_market_package_slices",
            "generated_utc": generated_at,
            "input_final_review_rows": counts["input_final_review_rows"],
            "package_slice_rows": counts["package_slice_rows"],
            "package_member_rows": counts["package_member_rows"],
            "package_redesign_carry_rows": counts["package_redesign_carry_rows"],
            "continuation": "continue to package-slice implementation review execution.",
            "boundary": research_boundary(),
        }
    )
    replace_active_checkpoint(generated_at, counts)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
