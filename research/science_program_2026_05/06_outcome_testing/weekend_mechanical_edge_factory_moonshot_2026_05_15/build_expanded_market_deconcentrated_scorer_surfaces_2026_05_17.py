#!/usr/bin/env python3
"""Build callable scorer surfaces from deconcentrated implementation selection rows."""

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

from src.research_infra.moonshot_expanded_market_deconcentrated_scorer_surfaces import (
    EXPANDED_MARKET_DECONCENTRATED_SCORER_SURFACES_SURFACE,
    aggregate_surface_rows,
    research_boundary,
    scorer_surface_rows,
    system_surface_rows,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_DECONCENTRATED_IMPLEMENTATION_SELECTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_DECONCENTRATED_SCORER_SURFACES"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
INPUT_SELECTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_expanded_market_deconcentrated_scorer_surfaces.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_expanded_market_deconcentrated_scorer_surfaces_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
SURFACE_LEDGER = ROUTE_DIR / f"{PREFIX}_SURFACE_LEDGER_2026-05-17.jsonl"
MEMBER_LEDGER = ROUTE_DIR / f"{PREFIX}_MEMBER_LEDGER_2026-05-17.jsonl"
EVIDENCE_LEDGER = ROUTE_DIR / f"{PREFIX}_NONIMPLEMENT_EVIDENCE_LEDGER_2026-05-17.jsonl"
SELF_TEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SELF_TEST_LEDGER_2026-05-17.jsonl"
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


def update_manifest(generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    entries = [
        (RESULT_PATH, "expanded_market_deconcentrated_scorer_surfaces_result"),
        (SURFACE_LEDGER, "expanded_market_deconcentrated_scorer_surfaces"),
        (MEMBER_LEDGER, "expanded_market_deconcentrated_scorer_members"),
        (EVIDENCE_LEDGER, "expanded_market_deconcentrated_nonimplement_evidence"),
        (SELF_TEST_LEDGER, "expanded_market_deconcentrated_scorer_self_tests"),
        (AGGREGATE_LEDGER, "expanded_market_deconcentrated_scorer_aggregates"),
        (ISSUE_LEDGER, "expanded_market_deconcentrated_scorer_issues"),
        (SYSTEM_LEDGER, "expanded_market_deconcentrated_scorer_system"),
        (SUMMARY_PATH, "expanded_market_deconcentrated_scorer_summary"),
        (BUILDER_MODULE, "expanded_market_deconcentrated_scorer_builder"),
        (VERIFIER_MODULE, "expanded_market_deconcentrated_scorer_verifier"),
        (HELPER_MODULE, "expanded_market_deconcentrated_scorer_helper"),
        (TEST_MODULE, "expanded_market_deconcentrated_scorer_tests"),
    ]
    rows = [
        {"path": str(path.relative_to(REPO)).replace("\\", "/"), "status": "created", "type": kind}
        for path, kind in entries
    ]
    existing = manifest.setdefault("artifacts", [])
    keys = {(row["path"], row["type"]) for row in rows}
    manifest["artifacts"] = [row for row in existing if (row.get("path"), row.get("type")) not in keys] + rows
    manifest["latest_expanded_market_deconcentrated_scorer_surfaces"] = {
        "generated_utc": generated_at,
        "files": rows,
        "result": str(RESULT_PATH.relative_to(REPO)).replace("\\", "/"),
    }
    manifest["last_updated_utc"] = generated_at
    write_json(OUTPUT_MANIFEST, manifest)


def replace_sprint_event(event: dict[str, Any]) -> None:
    kept_lines: list[str] = []
    if SPRINT_LEDGER.exists():
        with open(long_path(SPRINT_LEDGER), "r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    kept_lines.append(line.rstrip("\n"))
                    continue
                if row.get("event") == event.get("event"):
                    continue
                kept_lines.append(json.dumps(row, sort_keys=True))
    kept_lines.append(json.dumps(event, sort_keys=True))
    write_text(SPRINT_LEDGER, "\n".join(kept_lines) + "\n")


def replace_active_checkpoint(generated_at: str, counts: dict[str, Any]) -> None:
    marker = "## Checkpoint 250 - Expanded-Market Deconcentrated Scorer Surfaces"
    text = ACTIVE_LEDGER.read_text(encoding="utf-8", errors="replace") if ACTIVE_LEDGER.exists() else ""
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n\n"
    addition = f"""{marker}

Generated: {generated_at}

Trigger: direct continuation after Checkpoint 249. Deconcentrated implement rows were materialized as branch-local callable scorer surfaces with member rows and self-tests; non-implement rows were preserved as numeric evidence.

Rows:
- input selection rows: {counts["input_selection_rows"]}
- scorer surface rows: {counts["scorer_surface_rows"]}
- scorer member rows: {counts["scorer_member_rows"]}
- nonimplement evidence rows: {counts["nonimplement_evidence_rows"]}
- self-test rows: {counts["self_test_rows"]}
- issue rows: {counts["issue_rows"]}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: execute scorer surfaces against held selection rows and preserve mismatches or non-implement evidence with numeric proof.
"""
    write_text(ACTIVE_LEDGER, text.rstrip() + "\n\n" + addition)


def build_summary(generated_at: str, counts: dict[str, Any], result: dict[str, Any]) -> str:
    return f"""# Expanded-Market Deconcentrated Scorer Surfaces

Generated: {generated_at}

## Inputs

- Selection rows: `{counts["input_selection_rows"]}`

## Outputs

- Scorer surface rows: `{counts["scorer_surface_rows"]}`
- Scorer member rows: `{counts["scorer_member_rows"]}`
- Non-implement evidence rows: `{counts["nonimplement_evidence_rows"]}`
- Self-test rows: `{counts["self_test_rows"]}`
- Issue rows: `{counts["issue_rows"]}`

## Boundary

Branch-local research artifact only. The run wrote no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path.

## Result

- ok: `{result["ok"]}`
- issues: `{result["issues"]}`
"""


def main() -> None:
    generated_at = now_utc()
    input_result = read_json(INPUT_RESULT)
    selection_input = read_jsonl(INPUT_SELECTION_LEDGER)
    surfaces, members, evidence, self_tests, issues = scorer_surface_rows(selection_input)
    aggregates = aggregate_surface_rows(surfaces, members, evidence)
    metadata = {
        "input_selection_ok": input_result.get("ok"),
        "input_selection_rows": len(selection_input),
    }
    system_rows = system_surface_rows(surfaces, members, evidence, self_tests, aggregates, issues, metadata)
    counts = {
        "input_selection_rows": len(selection_input),
        "scorer_surface_rows": len(surfaces),
        "scorer_member_rows": len(members),
        "nonimplement_evidence_rows": len(evidence),
        "self_test_rows": len(self_tests),
        "self_test_pass_rows": system_rows[0].get("self_test_pass_rows"),
        "aggregate_rows": len(aggregates),
        "issue_rows": len(issues),
        "source_path_count": system_rows[0].get("source_path_count"),
        "symbol_family_count": system_rows[0].get("symbol_family_count"),
        "member_decision_counts": system_rows[0].get("member_decision_counts"),
        "evidence_decision_counts": system_rows[0].get("evidence_decision_counts"),
        "system_rows": len(system_rows),
    }
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "ok": True,
        "issues": [],
        "expanded_market_deconcentrated_scorer_surfaces_surface": (
            EXPANDED_MARKET_DECONCENTRATED_SCORER_SURFACES_SURFACE
        ),
        "research_boundary": research_boundary(),
        "inputs": {
            "selection_result": str(INPUT_RESULT.relative_to(REPO)).replace("\\", "/"),
            "selection_rows": str(INPUT_SELECTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "surface_ledger": str(SURFACE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "member_ledger": str(MEMBER_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "nonimplement_evidence_ledger": str(EVIDENCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "self_test_ledger": str(SELF_TEST_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "issue_ledger": str(ISSUE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
        "counts": counts,
    }

    write_jsonl(SURFACE_LEDGER, surfaces)
    write_jsonl(MEMBER_LEDGER, members)
    write_jsonl(EVIDENCE_LEDGER, evidence)
    write_jsonl(SELF_TEST_LEDGER, self_tests)
    write_jsonl(AGGREGATE_LEDGER, aggregates)
    write_jsonl(ISSUE_LEDGER, issues)
    write_jsonl(SYSTEM_LEDGER, system_rows)
    write_text(SUMMARY_PATH, build_summary(generated_at, counts, result))
    result["output_sha256"] = output_sha256(
        [SURFACE_LEDGER, MEMBER_LEDGER, EVIDENCE_LEDGER, SELF_TEST_LEDGER, AGGREGATE_LEDGER, ISSUE_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]
    )
    write_json(RESULT_PATH, result)
    update_manifest(generated_at)
    replace_sprint_event(
        {
            "event": "expanded_market_deconcentrated_scorer_surfaces",
            "checkpoint": 250,
            "generated_utc": generated_at,
            "result": str(RESULT_PATH.relative_to(REPO)).replace("\\", "/"),
            "counts": counts,
            "boundary": research_boundary(),
        }
    )
    replace_active_checkpoint(generated_at, counts)
    print(json.dumps({"ok": True, "counts": counts}, sort_keys=True))


if __name__ == "__main__":
    main()
