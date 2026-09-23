#!/usr/bin/env python3
"""Build branch-local code candidates from expanded-market implementation-selection rows."""

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

from src.research_infra.moonshot_expanded_market_code_candidates import (
    EXPANDED_MARKET_CODE_CANDIDATES_SURFACE,
    aggregate_code_candidate_rows,
    code_candidate_rows,
    research_boundary,
    system_code_candidate_rows,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_IMPLEMENTATION_SELECTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_CODE_CANDIDATES"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
INPUT_SELECTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_expanded_market_code_candidates.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_expanded_market_code_candidates_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
CODE_CANDIDATE_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
EVIDENCE_LEDGER = ROUTE_DIR / f"{PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"
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
        (RESULT_PATH, "expanded_market_code_candidates_result"),
        (CODE_CANDIDATE_LEDGER, "expanded_market_code_candidate_rows"),
        (EVIDENCE_LEDGER, "expanded_market_code_evidence_rows"),
        (SELF_TEST_LEDGER, "expanded_market_code_candidate_self_tests"),
        (AGGREGATE_LEDGER, "expanded_market_code_candidate_aggregates"),
        (SYSTEM_LEDGER, "expanded_market_code_candidate_system"),
        (SUMMARY_PATH, "expanded_market_code_candidate_summary"),
        (BUILDER_MODULE, "expanded_market_code_candidate_builder"),
        (VERIFIER_MODULE, "expanded_market_code_candidate_verifier"),
        (HELPER_MODULE, "expanded_market_code_candidate_helper"),
        (TEST_MODULE, "expanded_market_code_candidate_tests"),
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
    manifest["artifacts"] = [
        entry for entry in existing if (entry.get("path"), entry.get("type")) not in new_keys
    ] + entries
    manifest["latest_expanded_market_code_candidates"] = {
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
                if payload.get("checkpoint") == 221 and payload.get("event") == "expanded_market_code_candidates":
                    continue
                kept_lines.append(stripped)
    kept_lines.append(json.dumps(event, sort_keys=True))
    with open(long_path(SPRINT_LEDGER), "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(kept_lines) + "\n")


def replace_active_checkpoint(generated_at: str, counts: dict[str, Any]) -> None:
    marker = "## Checkpoint 221 - Expanded-Market Code Candidates"
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

Trigger: direct continuation after Checkpoint 220. Implementation-selection rows were split into branch-local code candidates and row-level non-implement evidence.

Rows:
- input implementation-selection rows: {counts['input_selection_rows']}
- code-candidate rows: {counts['code_candidate_rows']}
- code-evidence rows: {counts['code_evidence_rows']}
- self-test rows: {counts['self_test_rows']}
- aggregate rows: {counts['aggregate_rows']}
- self-test pass rows: {counts['self_test_pass_rows']}
- implement code-candidate rows: {counts['implement_rows']}
- avoid evidence rows: {counts['avoid_rows']}
- kill evidence rows: {counts['kill_rows']}
- redesign evidence rows: {counts['redesign_rows']}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: execute code candidates against held selection rows and preserve all pass/fail rows.
"""
    with open(long_path(ACTIVE_LEDGER), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text.rstrip() + "\n\n" + addition.strip() + "\n")


def build_summary(counts: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Expanded-Market Code Candidates",
            "",
            "This checkpoint materializes implementation-selection rows into branch-local code candidates and non-implement evidence rows.",
            "",
            "## Counts",
            "",
            f"- Input implementation-selection rows: `{counts['input_selection_rows']}`",
            f"- Code-candidate rows: `{counts['code_candidate_rows']}`",
            f"- Code-evidence rows: `{counts['code_evidence_rows']}`",
            f"- Self-test rows: `{counts['self_test_rows']}`",
            f"- Aggregate rows: `{counts['aggregate_rows']}`",
            f"- Self-test pass rows: `{counts['self_test_pass_rows']}`",
            "",
            "## Decisions",
            "",
            f"`{json.dumps(counts['decision_counts'], sort_keys=True)}`",
            "",
            "## Continuation",
            "",
            "Execute code candidates against held selection rows and preserve pass/fail rows.",
            "",
        ]
    )


def main() -> None:
    generated_at = now_utc()
    input_result = read_json(INPUT_RESULT)
    selection_rows = read_jsonl(INPUT_SELECTION_LEDGER)
    candidates, evidence, self_tests = code_candidate_rows(selection_rows)
    aggregates = aggregate_code_candidate_rows(candidates, evidence)
    system_rows = system_code_candidate_rows(candidates, evidence, self_tests, aggregates, len(selection_rows))
    decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in candidates + evidence)
    classes = Counter(row.get("follow_inverse_default_off_avoid_class") for row in candidates + evidence)
    counts = {
        "input_result_ok": bool(input_result.get("ok")),
        "input_selection_rows": len(selection_rows),
        "code_candidate_rows": len(candidates),
        "code_evidence_rows": len(evidence),
        "self_test_rows": len(self_tests),
        "aggregate_rows": len(aggregates),
        "system_rows": len(system_rows),
        "self_test_pass_rows": sum(
            1 for row in self_tests if row.get("self_test_status") == "CODE_CANDIDATE_SELF_TEST_PASS"
        ),
        "source_path_count": len({row.get("source_path") for row in candidates + evidence}),
        "symbol_count": len({row.get("symbol") for row in candidates + evidence}),
        "decision_counts": dict(sorted(decisions.items())),
        "class_counts": dict(sorted(classes.items())),
        "implement_rows": sum(str(decision).startswith("IMPLEMENT") for decision in decisions.elements()),
        "avoid_rows": sum("AVOID" in str(decision) for decision in decisions.elements()),
        "kill_rows": sum(str(decision).startswith("KILL") for decision in decisions.elements()),
        "redesign_rows": sum(str(decision).startswith("REDESIGN") for decision in decisions.elements()),
    }

    write_jsonl(CODE_CANDIDATE_LEDGER, candidates)
    write_jsonl(EVIDENCE_LEDGER, evidence)
    write_jsonl(SELF_TEST_LEDGER, self_tests)
    write_jsonl(AGGREGATE_LEDGER, aggregates)
    write_jsonl(SYSTEM_LEDGER, system_rows)
    write_text(SUMMARY_PATH, build_summary(counts))
    output_files = [CODE_CANDIDATE_LEDGER, EVIDENCE_LEDGER, SELF_TEST_LEDGER, AGGREGATE_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]
    result = {
        "ok": True,
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "counts": counts,
        "inputs": {
            "input_result": str(INPUT_RESULT.relative_to(REPO)).replace("\\", "/"),
            "input_selection_ledger": str(INPUT_SELECTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "code_candidate_ledger": str(CODE_CANDIDATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "evidence_ledger": str(EVIDENCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "self_test_ledger": str(SELF_TEST_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
        "output_sha256": output_sha256(output_files),
        "research_boundary": research_boundary(),
        "expanded_market_code_candidates_surface": EXPANDED_MARKET_CODE_CANDIDATES_SURFACE,
    }
    write_json(RESULT_PATH, result)
    update_manifest(generated_at)
    replace_sprint_event(
        {
            "checkpoint": 221,
            "event": "expanded_market_code_candidates",
            "generated_utc": generated_at,
            "input_selection_rows": counts["input_selection_rows"],
            "code_candidate_rows": counts["code_candidate_rows"],
            "code_evidence_rows": counts["code_evidence_rows"],
            "self_test_rows": counts["self_test_rows"],
            "aggregate_rows": counts["aggregate_rows"],
            "continuation": "continue to branch-local code-candidate execution rows.",
            "boundary": research_boundary(),
        }
    )
    replace_active_checkpoint(generated_at, counts)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
