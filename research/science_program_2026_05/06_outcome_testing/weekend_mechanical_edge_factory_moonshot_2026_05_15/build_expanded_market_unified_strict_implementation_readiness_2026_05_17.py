#!/usr/bin/env python3
"""Build implementation-readiness rows from strict expanded-market surfaces."""

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

from src.research_infra.moonshot_expanded_market_unified_strict_implementation_readiness import (
    EXPANDED_MARKET_UNIFIED_STRICT_IMPLEMENTATION_READINESS_SURFACE,
    research_boundary,
    system_unified_strict_implementation_readiness_rows,
    unified_strict_implementation_readiness_rows,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_UNIFIED_STRICT_ACTION_SURFACE_REPAIR"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_UNIFIED_STRICT_IMPLEMENTATION_READINESS"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
STRICT_SURFACE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_STRICT_SURFACE_LEDGER_2026-05-17.jsonl"
STRICT_SURFACE_EXECUTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_STRICT_SURFACE_EXECUTION_LEDGER_2026-05-17.jsonl"
STRICT_MEMBER_EXECUTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_STRICT_MEMBER_EXECUTION_LEDGER_2026-05-17.jsonl"
STRICT_REDESIGN_PRESERVATION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_STRICT_REDESIGN_PRESERVATION_LEDGER_2026-05-17.jsonl"
STRICT_REPAIR_PROOF_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_STRICT_REPAIR_PROOF_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_expanded_market_unified_strict_implementation_readiness.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_expanded_market_unified_strict_implementation_readiness_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
SURFACE_LEDGER = ROUTE_DIR / f"{PREFIX}_SURFACE_READINESS_LEDGER_2026-05-17.jsonl"
MEMBER_LEDGER = ROUTE_DIR / f"{PREFIX}_MEMBER_READINESS_LEDGER_2026-05-17.jsonl"
REDESIGN_LEDGER = ROUTE_DIR / f"{PREFIX}_REDESIGN_READINESS_LEDGER_2026-05-17.jsonl"
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
        (RESULT_PATH, "expanded_market_unified_strict_implementation_readiness_result"),
        (SURFACE_LEDGER, "expanded_market_unified_strict_implementation_surface_readiness"),
        (MEMBER_LEDGER, "expanded_market_unified_strict_implementation_member_readiness"),
        (REDESIGN_LEDGER, "expanded_market_unified_strict_implementation_redesign_readiness"),
        (AGGREGATE_LEDGER, "expanded_market_unified_strict_implementation_readiness_aggregates"),
        (ISSUE_LEDGER, "expanded_market_unified_strict_implementation_readiness_issues"),
        (SYSTEM_LEDGER, "expanded_market_unified_strict_implementation_readiness_system"),
        (SUMMARY_PATH, "expanded_market_unified_strict_implementation_readiness_summary"),
        (BUILDER_MODULE, "expanded_market_unified_strict_implementation_readiness_builder"),
        (VERIFIER_MODULE, "expanded_market_unified_strict_implementation_readiness_verifier"),
        (HELPER_MODULE, "expanded_market_unified_strict_implementation_readiness_helper"),
        (TEST_MODULE, "expanded_market_unified_strict_implementation_readiness_tests"),
    ]
    rows = [
        {"path": str(path.relative_to(REPO)).replace("\\", "/"), "status": "created", "type": kind}
        for path, kind in entries
    ]
    existing = manifest.setdefault("artifacts", [])
    keys = {(row["path"], row["type"]) for row in rows}
    manifest["artifacts"] = [row for row in existing if (row.get("path"), row.get("type")) not in keys] + rows
    manifest["latest_expanded_market_unified_strict_implementation_readiness"] = {
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
                if payload.get("checkpoint") == 244 and payload.get("event") == "expanded_market_unified_strict_implementation_readiness":
                    continue
                kept_lines.append(stripped)
    kept_lines.append(json.dumps(event, sort_keys=True))
    with open(long_path(SPRINT_LEDGER), "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(kept_lines) + "\n")


def replace_active_checkpoint(generated_at: str, counts: dict[str, Any]) -> None:
    marker = "## Checkpoint 244 - Expanded-Market Unified Strict Implementation Readiness"
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

Trigger: direct continuation after Checkpoint 243. Strict-pass surfaces were converted into implementation-readiness rows while all member evidence and redesign evidence retained simulated-R proof.

Rows:
- surface readiness rows: {counts['strict_implementation_surface_rows']}
- member readiness rows: {counts['strict_implementation_member_rows']}
- redesign readiness rows: {counts['strict_implementation_redesign_rows']}
- aggregate rows: {counts['aggregate_rows']}
- issue rows: {counts['issue_rows']}
- ready surface rows: {counts['implementation_ready_surface_rows']}
- ready member rows: {counts['implementation_ready_member_rows']}
- redesign evidence preserved rows: {counts['redesign_evidence_preserved_rows']}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: select the highest-value strict readiness rows for the next numeric implementation artifact plate, with all redesign evidence still preserved.
"""
    with open(long_path(ACTIVE_LEDGER), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text.rstrip() + "\n\n" + addition.strip() + "\n")


def build_summary(counts: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Expanded-Market Unified Strict Implementation Readiness",
            "",
            "This checkpoint converts strict-pass surfaces into implementation-readiness rows with member and redesign evidence.",
            "",
            "## Counts",
            "",
            f"- Surface readiness rows: `{counts['strict_implementation_surface_rows']}`",
            f"- Member readiness rows: `{counts['strict_implementation_member_rows']}`",
            f"- Redesign readiness rows: `{counts['strict_implementation_redesign_rows']}`",
            f"- Aggregate rows: `{counts['aggregate_rows']}`",
            f"- Issue rows: `{counts['issue_rows']}`",
            f"- Ready surface rows: `{counts['implementation_ready_surface_rows']}`",
            f"- Ready member rows: `{counts['implementation_ready_member_rows']}`",
            f"- Redesign evidence preserved rows: `{counts['redesign_evidence_preserved_rows']}`",
            "",
        ]
    )


def main() -> None:
    generated_at = now_utc()
    input_result = read_json(INPUT_RESULT)
    strict_surfaces = read_jsonl(STRICT_SURFACE_LEDGER)
    strict_executions = read_jsonl(STRICT_SURFACE_EXECUTION_LEDGER)
    member_executions = read_jsonl(STRICT_MEMBER_EXECUTION_LEDGER)
    redesign_preservations = read_jsonl(STRICT_REDESIGN_PRESERVATION_LEDGER)
    repair_proofs = read_jsonl(STRICT_REPAIR_PROOF_LEDGER)
    surface_rows, member_rows, redesign_rows, aggregates, issues = unified_strict_implementation_readiness_rows(
        strict_surfaces,
        strict_executions,
        member_executions,
        redesign_preservations,
    )
    input_counts = {
        "input_result_ok": input_result.get("ok"),
        "input_strict_surface_rows": len(strict_surfaces),
        "input_strict_surface_execution_rows": len(strict_executions),
        "input_strict_member_execution_rows": len(member_executions),
        "input_strict_redesign_preservation_rows": len(redesign_preservations),
        "input_strict_repair_proof_rows": len(repair_proofs),
    }
    system_rows = system_unified_strict_implementation_readiness_rows(
        surface_rows,
        member_rows,
        redesign_rows,
        aggregates,
        issues,
        input_counts,
    )
    counts = {
        **{key: value for key, value in input_counts.items() if key != "input_result_ok"},
        "strict_implementation_surface_rows": len(surface_rows),
        "strict_implementation_member_rows": len(member_rows),
        "strict_implementation_redesign_rows": len(redesign_rows),
        "aggregate_rows": len(aggregates),
        "issue_rows": len(issues),
        "system_rows": len(system_rows),
        "implementation_ready_surface_rows": sum(
            1 for row in surface_rows if row.get("implementation_readiness_status") == "STRICT_IMPLEMENTATION_READY"
        ),
        "implementation_ready_member_rows": sum(
            1 for row in member_rows if row.get("implementation_member_status") == "STRICT_IMPLEMENTATION_MEMBER_READY"
        ),
        "redesign_evidence_preserved_rows": sum(
            1
            for row in redesign_rows
            if row.get("implementation_redesign_status") == "STRICT_IMPLEMENTATION_REDESIGN_EVIDENCE_PRESERVED"
        ),
        "member_rows_with_simulated_r": sum(1 for row in member_rows if row.get("missing_simulated_field") is None),
        "redesign_rows_with_simulated_r": sum(1 for row in redesign_rows if row.get("missing_simulated_field") is None),
    }
    write_jsonl(SURFACE_LEDGER, surface_rows)
    write_jsonl(MEMBER_LEDGER, member_rows)
    write_jsonl(REDESIGN_LEDGER, redesign_rows)
    write_jsonl(AGGREGATE_LEDGER, aggregates)
    write_jsonl(ISSUE_LEDGER, issues)
    write_jsonl(SYSTEM_LEDGER, system_rows)
    write_text(SUMMARY_PATH, build_summary(counts))
    outputs = [SURFACE_LEDGER, MEMBER_LEDGER, REDESIGN_LEDGER, AGGREGATE_LEDGER, ISSUE_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "ok": True,
        "expanded_market_unified_strict_implementation_readiness_surface": (
            EXPANDED_MARKET_UNIFIED_STRICT_IMPLEMENTATION_READINESS_SURFACE
        ),
        "inputs": {
            "input_result": str(INPUT_RESULT.relative_to(REPO)).replace("\\", "/"),
            "strict_surface_ledger": str(STRICT_SURFACE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "strict_surface_execution_ledger": str(STRICT_SURFACE_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "strict_member_execution_ledger": str(STRICT_MEMBER_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "strict_redesign_preservation_ledger": str(STRICT_REDESIGN_PRESERVATION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "strict_repair_proof_ledger": str(STRICT_REPAIR_PROOF_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "surface_readiness_ledger": str(SURFACE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "member_readiness_ledger": str(MEMBER_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "redesign_readiness_ledger": str(REDESIGN_LEDGER.relative_to(REPO)).replace("\\", "/"),
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
            "event": "expanded_market_unified_strict_implementation_readiness",
            "checkpoint": 244,
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
