#!/usr/bin/env python3
"""Execute deconcentrated scorer surfaces against held selection rows."""

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

from src.research_infra.moonshot_expanded_market_deconcentrated_scorer_surface_execution import (
    EXPANDED_MARKET_DECONCENTRATED_SCORER_SURFACE_EXECUTION,
    aggregate_execution_rows,
    research_boundary,
    surface_execution_rows,
    system_execution_rows,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_DECONCENTRATED_SCORER_SURFACES"
SELECTION_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_DECONCENTRATED_IMPLEMENTATION_SELECTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_DECON_SCORER_EXEC"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
INPUT_SURFACE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SURFACE_LEDGER_2026-05-17.jsonl"
INPUT_MEMBER_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_MEMBER_LEDGER_2026-05-17.jsonl"
INPUT_EVIDENCE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_NONIMPLEMENT_EVIDENCE_LEDGER_2026-05-17.jsonl"
INPUT_SELECTION_LEDGER = ROUTE_DIR / f"{SELECTION_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_expanded_market_deconcentrated_scorer_surface_execution.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_expanded_market_deconcentrated_scorer_surface_execution_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
SURFACE_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SURFACE_EXECUTION_LEDGER_2026-05-17.jsonl"
MEMBER_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_MEMBER_EXECUTION_LEDGER_2026-05-17.jsonl"
EVIDENCE_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_NONIMPLEMENT_EVIDENCE_EXECUTION_LEDGER_2026-05-17.jsonl"
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
        (RESULT_PATH, "expanded_market_deconcentrated_scorer_surface_execution_result"),
        (SURFACE_EXECUTION_LEDGER, "expanded_market_deconcentrated_scorer_surface_executions"),
        (MEMBER_EXECUTION_LEDGER, "expanded_market_deconcentrated_scorer_member_executions"),
        (EVIDENCE_EXECUTION_LEDGER, "expanded_market_deconcentrated_nonimplement_evidence_executions"),
        (AGGREGATE_LEDGER, "expanded_market_deconcentrated_scorer_surface_execution_aggregates"),
        (ISSUE_LEDGER, "expanded_market_deconcentrated_scorer_surface_execution_issues"),
        (SYSTEM_LEDGER, "expanded_market_deconcentrated_scorer_surface_execution_system"),
        (SUMMARY_PATH, "expanded_market_deconcentrated_scorer_surface_execution_summary"),
        (BUILDER_MODULE, "expanded_market_deconcentrated_scorer_surface_execution_builder"),
        (VERIFIER_MODULE, "expanded_market_deconcentrated_scorer_surface_execution_verifier"),
        (HELPER_MODULE, "expanded_market_deconcentrated_scorer_surface_execution_helper"),
        (TEST_MODULE, "expanded_market_deconcentrated_scorer_surface_execution_tests"),
    ]
    rows = [
        {"path": str(path.relative_to(REPO)).replace("\\", "/"), "status": "created", "type": kind}
        for path, kind in entries
    ]
    existing = manifest.setdefault("artifacts", [])
    keys = {(row["path"], row["type"]) for row in rows}
    types = {row["type"] for row in rows}
    manifest["artifacts"] = [
        row for row in existing if row.get("type") not in types and (row.get("path"), row.get("type")) not in keys
    ] + rows
    manifest["latest_expanded_market_deconcentrated_scorer_surface_execution"] = {
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
    marker = "## Checkpoint 251 - Expanded-Market Deconcentrated Scorer Surface Execution"
    text = ACTIVE_LEDGER.read_text(encoding="utf-8", errors="replace") if ACTIVE_LEDGER.exists() else ""
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n\n"
    addition = f"""{marker}

Generated: {generated_at}

Trigger: direct continuation after Checkpoint 250. Scorer surfaces were executed against all held selection rows, with member matches compared to the expected surface-member ledger and non-implement rows preserved as numeric evidence.

Rows:
- input scorer surface rows: {counts["input_scorer_surface_rows"]}
- input scorer member rows: {counts["input_scorer_member_rows"]}
- input non-implement evidence rows: {counts["input_nonimplement_evidence_rows"]}
- held selection rows: {counts["input_selection_rows"]}
- surface execution rows: {counts["surface_execution_rows"]}
- surface execution pass rows: {counts["surface_execution_pass_rows"]}
- member execution rows: {counts["member_execution_rows"]}
- non-implement evidence execution rows: {counts["nonimplement_evidence_execution_rows"]}
- issue rows: {counts["issue_rows"]}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: use the pass execution rows and preserved non-implement evidence for the next numeric implementation or repair plate; do not stop at surface execution inventory.
"""
    write_text(ACTIVE_LEDGER, text.rstrip() + "\n\n" + addition)


def build_summary(generated_at: str, counts: dict[str, Any], result: dict[str, Any]) -> str:
    return f"""# Expanded-Market Deconcentrated Scorer Surface Execution

Generated: {generated_at}

## Inputs

- Scorer surfaces: `{counts["input_scorer_surface_rows"]}`
- Scorer members: `{counts["input_scorer_member_rows"]}`
- Non-implement evidence rows: `{counts["input_nonimplement_evidence_rows"]}`
- Held selection rows: `{counts["input_selection_rows"]}`

## Outputs

- Surface execution rows: `{counts["surface_execution_rows"]}`
- Surface execution pass rows: `{counts["surface_execution_pass_rows"]}`
- Member execution rows: `{counts["member_execution_rows"]}`
- Non-implement evidence execution rows: `{counts["nonimplement_evidence_execution_rows"]}`
- Aggregate rows: `{counts["aggregate_rows"]}`
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
    surfaces = read_jsonl(INPUT_SURFACE_LEDGER)
    members = read_jsonl(INPUT_MEMBER_LEDGER)
    evidence = read_jsonl(INPUT_EVIDENCE_LEDGER)
    selection_rows = read_jsonl(INPUT_SELECTION_LEDGER)
    surface_exec, member_exec, evidence_exec, issues = surface_execution_rows(surfaces, members, evidence, selection_rows)
    aggregates = aggregate_execution_rows(surface_exec, member_exec, evidence_exec)
    metadata = {
        "input_scorer_surface_result_ok": input_result.get("ok"),
        "input_scorer_surface_rows": len(surfaces),
        "input_scorer_member_rows": len(members),
        "input_nonimplement_evidence_rows": len(evidence),
        "input_selection_rows": len(selection_rows),
    }
    system_rows = system_execution_rows(
        surfaces,
        members,
        evidence,
        surface_exec,
        member_exec,
        evidence_exec,
        aggregates,
        issues,
        metadata,
    )
    counts = {
        "input_scorer_surface_rows": len(surfaces),
        "input_scorer_member_rows": len(members),
        "input_nonimplement_evidence_rows": len(evidence),
        "input_selection_rows": len(selection_rows),
        "surface_execution_rows": len(surface_exec),
        "surface_execution_pass_rows": system_rows[0].get("surface_execution_pass_rows"),
        "surface_execution_redesign_rows": system_rows[0].get("surface_execution_redesign_rows"),
        "member_execution_rows": len(member_exec),
        "nonimplement_evidence_execution_rows": len(evidence_exec),
        "aggregate_rows": len(aggregates),
        "issue_rows": len(issues),
        "source_path_count": system_rows[0].get("source_path_count"),
        "symbol_family_count": system_rows[0].get("symbol_family_count"),
        "surface_decision_counts": system_rows[0].get("surface_decision_counts"),
        "member_decision_counts": system_rows[0].get("member_decision_counts"),
        "evidence_decision_counts": system_rows[0].get("evidence_decision_counts"),
        "system_rows": len(system_rows),
    }
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "ok": not issues,
        "issues": issues,
        "expanded_market_deconcentrated_scorer_surface_execution_surface": (
            EXPANDED_MARKET_DECONCENTRATED_SCORER_SURFACE_EXECUTION
        ),
        "research_boundary": research_boundary(),
        "inputs": {
            "scorer_surface_result": str(INPUT_RESULT.relative_to(REPO)).replace("\\", "/"),
            "surface_rows": str(INPUT_SURFACE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "member_rows": str(INPUT_MEMBER_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "nonimplement_evidence_rows": str(INPUT_EVIDENCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "selection_rows": str(INPUT_SELECTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "surface_execution_ledger": str(SURFACE_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "member_execution_ledger": str(MEMBER_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "nonimplement_evidence_execution_ledger": str(EVIDENCE_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "issue_ledger": str(ISSUE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
        "counts": counts,
    }

    write_jsonl(SURFACE_EXECUTION_LEDGER, surface_exec)
    write_jsonl(MEMBER_EXECUTION_LEDGER, member_exec)
    write_jsonl(EVIDENCE_EXECUTION_LEDGER, evidence_exec)
    write_jsonl(AGGREGATE_LEDGER, aggregates)
    write_jsonl(ISSUE_LEDGER, issues)
    write_jsonl(SYSTEM_LEDGER, system_rows)
    write_text(SUMMARY_PATH, build_summary(generated_at, counts, result))
    result["output_sha256"] = output_sha256(
        [
            SURFACE_EXECUTION_LEDGER,
            MEMBER_EXECUTION_LEDGER,
            EVIDENCE_EXECUTION_LEDGER,
            AGGREGATE_LEDGER,
            ISSUE_LEDGER,
            SYSTEM_LEDGER,
            SUMMARY_PATH,
        ]
    )
    write_json(RESULT_PATH, result)
    update_manifest(generated_at)
    replace_sprint_event(
        {
            "event": "checkpoint_251_expanded_market_deconcentrated_scorer_surface_execution",
            "generated_utc": generated_at,
            "result": str(RESULT_PATH.relative_to(REPO)).replace("\\", "/"),
            "counts": counts,
            "boundary": research_boundary(),
        }
    )
    replace_active_checkpoint(generated_at, counts)
    print(json.dumps({"ok": result["ok"], "counts": counts}, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
