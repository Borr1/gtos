#!/usr/bin/env python3
"""Build branch-local artifacts from strict expanded-market readiness rows."""

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

from src.research_infra.moonshot_expanded_market_unified_strict_artifact_execution import (
    EXPANDED_MARKET_UNIFIED_STRICT_ARTIFACT_EXECUTION_SURFACE,
    research_boundary,
    system_unified_strict_artifact_execution_rows,
    unified_strict_artifact_execution_rows,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_UNIFIED_STRICT_IMPLEMENTATION_READINESS"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_UNIFIED_STRICT_ARTIFACT_EXECUTION"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
SURFACE_READINESS_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SURFACE_READINESS_LEDGER_2026-05-17.jsonl"
MEMBER_READINESS_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_MEMBER_READINESS_LEDGER_2026-05-17.jsonl"
REDESIGN_READINESS_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_REDESIGN_READINESS_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_expanded_market_unified_strict_artifact_execution.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_expanded_market_unified_strict_artifact_execution_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
ARTIFACT_LEDGER = ROUTE_DIR / f"{PREFIX}_ARTIFACT_LEDGER_2026-05-17.jsonl"
MEMBER_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_MEMBER_EXECUTION_LEDGER_2026-05-17.jsonl"
CONTROL_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTROL_LEDGER_2026-05-17.jsonl"
REDESIGN_LEDGER = ROUTE_DIR / f"{PREFIX}_REDESIGN_LEDGER_2026-05-17.jsonl"
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
        (RESULT_PATH, "expanded_market_unified_strict_artifact_execution_result"),
        (ARTIFACT_LEDGER, "expanded_market_unified_strict_artifacts"),
        (MEMBER_EXECUTION_LEDGER, "expanded_market_unified_strict_artifact_member_executions"),
        (CONTROL_LEDGER, "expanded_market_unified_strict_artifact_controls"),
        (REDESIGN_LEDGER, "expanded_market_unified_strict_artifact_redesign"),
        (AGGREGATE_LEDGER, "expanded_market_unified_strict_artifact_aggregates"),
        (ISSUE_LEDGER, "expanded_market_unified_strict_artifact_issues"),
        (SYSTEM_LEDGER, "expanded_market_unified_strict_artifact_system"),
        (SUMMARY_PATH, "expanded_market_unified_strict_artifact_summary"),
        (BUILDER_MODULE, "expanded_market_unified_strict_artifact_builder"),
        (VERIFIER_MODULE, "expanded_market_unified_strict_artifact_verifier"),
        (HELPER_MODULE, "expanded_market_unified_strict_artifact_helper"),
        (TEST_MODULE, "expanded_market_unified_strict_artifact_tests"),
    ]
    rows = [
        {"path": str(path.relative_to(REPO)).replace("\\", "/"), "status": "created", "type": kind}
        for path, kind in entries
    ]
    existing = manifest.setdefault("artifacts", [])
    keys = {(row["path"], row["type"]) for row in rows}
    manifest["artifacts"] = [row for row in existing if (row.get("path"), row.get("type")) not in keys] + rows
    manifest["latest_expanded_market_unified_strict_artifact_execution"] = {
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
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    payload = json.loads(stripped)
                except json.JSONDecodeError:
                    kept_lines.append(stripped)
                    continue
                if payload.get("checkpoint") == 245 and payload.get("event") == "expanded_market_unified_strict_artifact_execution":
                    continue
                kept_lines.append(stripped)
    kept_lines.append(json.dumps(event, sort_keys=True))
    with open(long_path(SPRINT_LEDGER), "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(kept_lines) + "\n")


def replace_active_checkpoint(generated_at: str, counts: dict[str, Any]) -> None:
    marker = "## Checkpoint 245 - Expanded-Market Unified Strict Artifact Execution"
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

Trigger: direct continuation after Checkpoint 244. All strict-ready surfaces were materialized as branch-local artifacts and executed against every member row with mismatch controls; redesign rows were preserved.

Rows:
- artifact rows: {counts['strict_artifact_rows']}
- member execution rows: {counts['strict_artifact_member_execution_rows']}
- control rows: {counts['strict_artifact_control_rows']}
- redesign rows: {counts['strict_artifact_redesign_rows']}
- aggregate rows: {counts['aggregate_rows']}
- issue rows: {counts['issue_rows']}
- artifact ready rows: {counts['artifact_ready_rows']}
- member pass rows: {counts['artifact_member_execution_pass_rows']}
- control pass rows: {counts['artifact_control_pass_rows']}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: consume artifact executions into a final strict implementation decision plate while preserving redesign rows.
"""
    with open(long_path(ACTIVE_LEDGER), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text.rstrip() + "\n\n" + addition.strip() + "\n")


def build_summary(counts: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Expanded-Market Unified Strict Artifact Execution",
            "",
            "This checkpoint materializes strict readiness rows as branch-local artifacts and executes them against member evidence.",
            "",
            "## Counts",
            "",
            f"- Artifact rows: `{counts['strict_artifact_rows']}`",
            f"- Member execution rows: `{counts['strict_artifact_member_execution_rows']}`",
            f"- Control rows: `{counts['strict_artifact_control_rows']}`",
            f"- Redesign rows: `{counts['strict_artifact_redesign_rows']}`",
            f"- Aggregate rows: `{counts['aggregate_rows']}`",
            f"- Issue rows: `{counts['issue_rows']}`",
            f"- Artifact ready rows: `{counts['artifact_ready_rows']}`",
            f"- Member pass rows: `{counts['artifact_member_execution_pass_rows']}`",
            f"- Control pass rows: `{counts['artifact_control_pass_rows']}`",
            "",
        ]
    )


def main() -> None:
    generated_at = now_utc()
    input_result = read_json(INPUT_RESULT)
    surface_rows = read_jsonl(SURFACE_READINESS_LEDGER)
    member_rows = read_jsonl(MEMBER_READINESS_LEDGER)
    redesign_rows = read_jsonl(REDESIGN_READINESS_LEDGER)
    artifacts, member_executions, controls, redesigns, aggregates, issues = unified_strict_artifact_execution_rows(
        surface_rows,
        member_rows,
        redesign_rows,
    )
    input_counts = {
        "input_result_ok": input_result.get("ok"),
        "input_surface_readiness_rows": len(surface_rows),
        "input_member_readiness_rows": len(member_rows),
        "input_redesign_readiness_rows": len(redesign_rows),
    }
    system_rows = system_unified_strict_artifact_execution_rows(
        artifacts,
        member_executions,
        controls,
        redesigns,
        aggregates,
        issues,
        input_counts,
    )
    counts = {
        "input_surface_readiness_rows": len(surface_rows),
        "input_member_readiness_rows": len(member_rows),
        "input_redesign_readiness_rows": len(redesign_rows),
        "strict_artifact_rows": len(artifacts),
        "strict_artifact_member_execution_rows": len(member_executions),
        "strict_artifact_control_rows": len(controls),
        "strict_artifact_redesign_rows": len(redesigns),
        "aggregate_rows": len(aggregates),
        "issue_rows": len(issues),
        "system_rows": len(system_rows),
        "artifact_ready_rows": sum(
            1 for row in artifacts if row.get("artifact_execution_status") == "STRICT_IMPLEMENTATION_ARTIFACT_READY"
        ),
        "artifact_member_execution_pass_rows": sum(
            1
            for row in member_executions
            if row.get("artifact_member_execution_status") == "STRICT_ARTIFACT_MEMBER_EXECUTION_PASS"
        ),
        "artifact_control_pass_rows": sum(
            1 for row in controls if row.get("artifact_control_status") == "STRICT_ARTIFACT_CONTROL_PASS"
        ),
        "artifact_redesign_preserved_rows": sum(
            1 for row in redesigns if row.get("artifact_redesign_status") == "STRICT_ARTIFACT_REDESIGN_EVIDENCE_PRESERVED"
        ),
        "member_rows_with_simulated_r": sum(1 for row in member_executions if row.get("missing_simulated_field") is None),
        "redesign_rows_with_simulated_r": sum(1 for row in redesigns if row.get("missing_simulated_field") is None),
    }
    write_jsonl(ARTIFACT_LEDGER, artifacts)
    write_jsonl(MEMBER_EXECUTION_LEDGER, member_executions)
    write_jsonl(CONTROL_LEDGER, controls)
    write_jsonl(REDESIGN_LEDGER, redesigns)
    write_jsonl(AGGREGATE_LEDGER, aggregates)
    write_jsonl(ISSUE_LEDGER, issues)
    write_jsonl(SYSTEM_LEDGER, system_rows)
    write_text(SUMMARY_PATH, build_summary(counts))
    outputs = [ARTIFACT_LEDGER, MEMBER_EXECUTION_LEDGER, CONTROL_LEDGER, REDESIGN_LEDGER, AGGREGATE_LEDGER, ISSUE_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "ok": True,
        "expanded_market_unified_strict_artifact_execution_surface": (
            EXPANDED_MARKET_UNIFIED_STRICT_ARTIFACT_EXECUTION_SURFACE
        ),
        "inputs": {
            "input_result": str(INPUT_RESULT.relative_to(REPO)).replace("\\", "/"),
            "surface_readiness_ledger": str(SURFACE_READINESS_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "member_readiness_ledger": str(MEMBER_READINESS_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "redesign_readiness_ledger": str(REDESIGN_READINESS_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "artifact_ledger": str(ARTIFACT_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "member_execution_ledger": str(MEMBER_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "control_ledger": str(CONTROL_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "redesign_ledger": str(REDESIGN_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "issue_ledger": str(ISSUE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
        "counts": counts,
        "research_boundary": research_boundary(),
    }
    write_json(RESULT_PATH, result)
    result["output_sha256"] = output_sha256(outputs + [RESULT_PATH])
    write_json(RESULT_PATH, result)
    update_manifest(generated_at)
    replace_sprint_event(
        {
            "event": "expanded_market_unified_strict_artifact_execution",
            "checkpoint": 245,
            "generated_utc": generated_at,
            "counts": counts,
            "result": str(RESULT_PATH.relative_to(REPO)).replace("\\", "/"),
            "boundary": research_boundary(),
        }
    )
    replace_active_checkpoint(generated_at, counts)
    print(json.dumps({"ok": True, "counts": counts}, sort_keys=True))


if __name__ == "__main__":
    main()
