#!/usr/bin/env python3
"""Select expanded-market final artifacts with portfolio concentration checks."""

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

from src.research_infra.moonshot_expanded_market_portfolio_artifact_selection import (
    EXPANDED_MARKET_PORTFOLIO_ARTIFACT_SELECTION_SURFACE,
    aggregate_selection_rows,
    portfolio_selection_rows,
    research_boundary,
    system_selection_rows,
)


ARTIFACT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_FINAL_BRANCH_ARTIFACTS"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_PORTFOLIO_ARTIFACT_SELECTION"

ARTIFACT_RESULT = ROUTE_DIR / f"{ARTIFACT_PREFIX}_RESULT_2026-05-17.json"
ARTIFACT_LEDGER = ROUTE_DIR / f"{ARTIFACT_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
EVIDENCE_EXECUTION_LEDGER = ROUTE_DIR / f"{ARTIFACT_PREFIX}_EVIDENCE_EXECUTION_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_expanded_market_portfolio_artifact_selection.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_expanded_market_portfolio_artifact_selection_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
SELECTION_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
EVIDENCE_LEDGER = ROUTE_DIR / f"{PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"
CONCENTRATION_LEDGER = ROUTE_DIR / f"{PREFIX}_CONCENTRATION_LEDGER_2026-05-17.jsonl"
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
        (RESULT_PATH, "expanded_market_portfolio_artifact_selection_result"),
        (SELECTION_LEDGER, "expanded_market_portfolio_artifact_selection_rows"),
        (EVIDENCE_LEDGER, "expanded_market_portfolio_artifact_selection_evidence"),
        (CONCENTRATION_LEDGER, "expanded_market_portfolio_concentration_rows"),
        (AGGREGATE_LEDGER, "expanded_market_portfolio_artifact_selection_aggregates"),
        (SYSTEM_LEDGER, "expanded_market_portfolio_artifact_selection_system"),
        (SUMMARY_PATH, "expanded_market_portfolio_artifact_selection_summary"),
        (BUILDER_MODULE, "expanded_market_portfolio_artifact_selection_builder"),
        (VERIFIER_MODULE, "expanded_market_portfolio_artifact_selection_verifier"),
        (HELPER_MODULE, "expanded_market_portfolio_artifact_selection_helper"),
        (TEST_MODULE, "expanded_market_portfolio_artifact_selection_tests"),
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
    manifest["latest_expanded_market_portfolio_artifact_selection"] = {
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
                if payload.get("checkpoint") == 227 and payload.get("event") == "expanded_market_portfolio_artifact_selection":
                    continue
                kept_lines.append(stripped)
    kept_lines.append(json.dumps(event, sort_keys=True))
    with open(long_path(SPRINT_LEDGER), "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(kept_lines) + "\n")


def replace_active_checkpoint(generated_at: str, counts: dict[str, Any]) -> None:
    marker = "## Checkpoint 227 - Expanded-Market Portfolio Artifact Selection"
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

Trigger: direct continuation after Checkpoint 226. Final branch-local artifacts were evaluated for portfolio concentration while preserving every artifact and evidence row.

Rows:
- input final artifact rows: {counts['input_artifact_rows']}
- input evidence execution rows: {counts['input_evidence_execution_rows']}
- portfolio artifact selection rows: {counts['portfolio_artifact_selection_rows']}
- portfolio artifact selection evidence rows: {counts['portfolio_artifact_selection_evidence_rows']}
- portfolio concentration rows: {counts['portfolio_concentration_rows']}
- aggregate rows: {counts['aggregate_rows']}
- selected rows: {counts['selected_rows']}
- preserved redesign/kill rows: {counts['preserved_redesign_or_kill_rows']}
- concentration guard rows: {counts['concentration_guard_rows']}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: deconcentrate guarded rows or preserve them as redesign evidence while carrying selected rows toward branch-local review.
"""
    with open(long_path(ACTIVE_LEDGER), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text.rstrip() + "\n\n" + addition.strip() + "\n")


def build_summary(counts: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Expanded-Market Portfolio Artifact Selection",
            "",
            "This checkpoint evaluates final branch-local artifacts for portfolio concentration and preserves every artifact and evidence row.",
            "",
            "## Counts",
            "",
            f"- Input final artifact rows: `{counts['input_artifact_rows']}`",
            f"- Input evidence execution rows: `{counts['input_evidence_execution_rows']}`",
            f"- Portfolio artifact selection rows: `{counts['portfolio_artifact_selection_rows']}`",
            f"- Portfolio artifact selection evidence rows: `{counts['portfolio_artifact_selection_evidence_rows']}`",
            f"- Portfolio concentration rows: `{counts['portfolio_concentration_rows']}`",
            f"- Aggregate rows: `{counts['aggregate_rows']}`",
            f"- Selected rows: `{counts['selected_rows']}`",
            f"- Preserved redesign/kill rows: `{counts['preserved_redesign_or_kill_rows']}`",
            f"- Concentration guard rows: `{counts['concentration_guard_rows']}`",
            "",
            "## Decisions",
            "",
            f"`{json.dumps(counts['decision_counts'], sort_keys=True)}`",
            "",
            "## Continuation",
            "",
            "Deconcentrate guarded rows or preserve them as redesign evidence while carrying selected rows toward branch-local review.",
            "",
        ]
    )


def main() -> None:
    generated_at = now_utc()
    artifact_result = read_json(ARTIFACT_RESULT)
    artifacts = read_jsonl(ARTIFACT_LEDGER)
    evidence_executions = read_jsonl(EVIDENCE_EXECUTION_LEDGER)
    selections, evidence, concentration = portfolio_selection_rows(artifacts, evidence_executions)
    aggregates = aggregate_selection_rows(selections)
    system_rows = system_selection_rows(selections, evidence, concentration, aggregates, len(artifacts), len(evidence_executions))
    decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in selections)
    counts = {
        "input_result_ok": bool(artifact_result.get("ok")),
        "input_artifact_rows": len(artifacts),
        "input_evidence_execution_rows": len(evidence_executions),
        "portfolio_artifact_selection_rows": len(selections),
        "portfolio_artifact_selection_evidence_rows": len(evidence),
        "portfolio_concentration_rows": len(concentration),
        "aggregate_rows": len(aggregates),
        "system_rows": len(system_rows),
        "selected_rows": sum(1 for row in selections if row.get("portfolio_selection_status") == "PORTFOLIO_ARTIFACT_SELECTED"),
        "preserved_redesign_or_kill_rows": sum(
            1
            for row in selections
            if row.get("portfolio_selection_status") == "PORTFOLIO_ARTIFACT_PRESERVED_FOR_REDESIGN_OR_KILL"
        ),
        "concentration_guard_rows": sum(
            1 for row in concentration if row.get("concentration_status") == "CONCENTRATION_GUARD_REQUIRED"
        ),
        "decision_counts": dict(sorted(decisions.items())),
    }
    write_jsonl(SELECTION_LEDGER, selections)
    write_jsonl(EVIDENCE_LEDGER, evidence)
    write_jsonl(CONCENTRATION_LEDGER, concentration)
    write_jsonl(AGGREGATE_LEDGER, aggregates)
    write_jsonl(SYSTEM_LEDGER, system_rows)
    write_text(SUMMARY_PATH, build_summary(counts))
    output_files = [SELECTION_LEDGER, EVIDENCE_LEDGER, CONCENTRATION_LEDGER, AGGREGATE_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]
    result = {
        "ok": True,
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "counts": counts,
        "inputs": {
            "artifact_result": str(ARTIFACT_RESULT.relative_to(REPO)).replace("\\", "/"),
            "artifact_ledger": str(ARTIFACT_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "evidence_execution_ledger": str(EVIDENCE_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "selection_ledger": str(SELECTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "evidence_ledger": str(EVIDENCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "concentration_ledger": str(CONCENTRATION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
        "output_sha256": output_sha256(output_files),
        "research_boundary": research_boundary(),
        "expanded_market_portfolio_artifact_selection_surface": EXPANDED_MARKET_PORTFOLIO_ARTIFACT_SELECTION_SURFACE,
    }
    write_json(RESULT_PATH, result)
    update_manifest(generated_at)
    replace_sprint_event(
        {
            "checkpoint": 227,
            "event": "expanded_market_portfolio_artifact_selection",
            "generated_utc": generated_at,
            "input_artifact_rows": counts["input_artifact_rows"],
            "portfolio_artifact_selection_rows": counts["portfolio_artifact_selection_rows"],
            "selected_rows": counts["selected_rows"],
            "preserved_redesign_or_kill_rows": counts["preserved_redesign_or_kill_rows"],
            "concentration_guard_rows": counts["concentration_guard_rows"],
            "continuation": "continue to deconcentration or redesign-preservation execution.",
            "boundary": research_boundary(),
        }
    )
    replace_active_checkpoint(generated_at, counts)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
