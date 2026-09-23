#!/usr/bin/env python3
"""Build strict predicate repair rows for expanded-market unified action surfaces."""

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

from src.research_infra.moonshot_expanded_market_unified_strict_action_surface_repair import (
    EXPANDED_MARKET_UNIFIED_STRICT_ACTION_SURFACE_REPAIR_SURFACE,
    research_boundary,
    system_unified_strict_action_surface_repair_rows,
    unified_strict_action_surface_repair_rows,
)


ACTION_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_UNIFIED_IMPLEMENTATION_ACTIONS"
SURFACE_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_UNIFIED_ACTION_SURFACES"
EXECUTION_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_UNIFIED_ACTION_SURFACE_EXECUTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_UNIFIED_STRICT_ACTION_SURFACE_REPAIR"

ACTION_RESULT = ROUTE_DIR / f"{ACTION_PREFIX}_RESULT_2026-05-17.json"
SURFACE_RESULT = ROUTE_DIR / f"{SURFACE_PREFIX}_RESULT_2026-05-17.json"
EXECUTION_RESULT = ROUTE_DIR / f"{EXECUTION_PREFIX}_RESULT_2026-05-17.json"
EVIDENCE_ACTION_LEDGER = ROUTE_DIR / f"{ACTION_PREFIX}_EVIDENCE_ACTION_LEDGER_2026-05-17.jsonl"
DECISION_ACTION_LEDGER = ROUTE_DIR / f"{ACTION_PREFIX}_DECISION_ACTION_LEDGER_2026-05-17.jsonl"
TERMINAL_ACTION_LEDGER = ROUTE_DIR / f"{ACTION_PREFIX}_TERMINAL_ACTION_LEDGER_2026-05-17.jsonl"
SURFACE_LEDGER = ROUTE_DIR / f"{SURFACE_PREFIX}_SURFACE_LEDGER_2026-05-17.jsonl"
MEMBER_LEDGER = ROUTE_DIR / f"{SURFACE_PREFIX}_MEMBER_LEDGER_2026-05-17.jsonl"
EXECUTION_REDESIGN_LEDGER = ROUTE_DIR / f"{EXECUTION_PREFIX}_REDESIGN_EXECUTION_LEDGER_2026-05-17.jsonl"
EXECUTION_ISSUE_LEDGER = ROUTE_DIR / f"{EXECUTION_PREFIX}_ISSUE_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_expanded_market_unified_strict_action_surface_repair.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_expanded_market_unified_strict_action_surface_repair_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
STRICT_SURFACE_LEDGER = ROUTE_DIR / f"{PREFIX}_STRICT_SURFACE_LEDGER_2026-05-17.jsonl"
STRICT_SURFACE_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_STRICT_SURFACE_EXECUTION_LEDGER_2026-05-17.jsonl"
STRICT_MEMBER_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_STRICT_MEMBER_EXECUTION_LEDGER_2026-05-17.jsonl"
STRICT_REDESIGN_PRESERVATION_LEDGER = ROUTE_DIR / f"{PREFIX}_STRICT_REDESIGN_PRESERVATION_LEDGER_2026-05-17.jsonl"
STRICT_REPAIR_PROOF_LEDGER = ROUTE_DIR / f"{PREFIX}_STRICT_REPAIR_PROOF_LEDGER_2026-05-17.jsonl"
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
        (RESULT_PATH, "expanded_market_unified_strict_action_surface_repair_result"),
        (STRICT_SURFACE_LEDGER, "expanded_market_unified_strict_action_surfaces"),
        (STRICT_SURFACE_EXECUTION_LEDGER, "expanded_market_unified_strict_action_surface_executions"),
        (STRICT_MEMBER_EXECUTION_LEDGER, "expanded_market_unified_strict_action_member_executions"),
        (STRICT_REDESIGN_PRESERVATION_LEDGER, "expanded_market_unified_strict_action_redesign_preservation"),
        (STRICT_REPAIR_PROOF_LEDGER, "expanded_market_unified_strict_action_repair_proofs"),
        (AGGREGATE_LEDGER, "expanded_market_unified_strict_action_surface_repair_aggregates"),
        (ISSUE_LEDGER, "expanded_market_unified_strict_action_surface_repair_issues"),
        (SYSTEM_LEDGER, "expanded_market_unified_strict_action_surface_repair_system"),
        (SUMMARY_PATH, "expanded_market_unified_strict_action_surface_repair_summary"),
        (BUILDER_MODULE, "expanded_market_unified_strict_action_surface_repair_builder"),
        (VERIFIER_MODULE, "expanded_market_unified_strict_action_surface_repair_verifier"),
        (HELPER_MODULE, "expanded_market_unified_strict_action_surface_repair_helper"),
        (TEST_MODULE, "expanded_market_unified_strict_action_surface_repair_tests"),
    ]
    rows = [
        {"path": str(path.relative_to(REPO)).replace("\\", "/"), "status": "created", "type": kind}
        for path, kind in entries
    ]
    existing = manifest.setdefault("artifacts", [])
    keys = {(row["path"], row["type"]) for row in rows}
    manifest["artifacts"] = [row for row in existing if (row.get("path"), row.get("type")) not in keys] + rows
    manifest["latest_expanded_market_unified_strict_action_surface_repair"] = {
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
                if payload.get("checkpoint") == 243 and payload.get("event") == "expanded_market_unified_strict_action_surface_repair":
                    continue
                kept_lines.append(stripped)
    kept_lines.append(json.dumps(event, sort_keys=True))
    with open(long_path(SPRINT_LEDGER), "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(kept_lines) + "\n")


def replace_active_checkpoint(generated_at: str, counts: dict[str, Any]) -> None:
    marker = "## Checkpoint 243 - Expanded-Market Unified Strict Action Surface Repair"
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

Trigger: direct continuation after Checkpoint 242. The two broad decision-scope predicates were repaired with hash guards, then every strict surface was re-executed against held action rows.

Rows:
- strict surface rows: {counts['strict_surface_rows']}
- strict surface execution rows: {counts['strict_surface_execution_rows']}
- strict member execution rows: {counts['strict_member_execution_rows']}
- strict redesign preservation rows: {counts['strict_redesign_preservation_rows']}
- repair proof rows: {counts['strict_repair_proof_rows']}
- aggregate rows: {counts['aggregate_rows']}
- issue rows: {counts['issue_rows']}
- strict surface pass rows: {counts['strict_surface_execution_pass_rows']}
- strict member pass rows: {counts['strict_member_execution_pass_rows']}
- hash-guard repaired surface rows: {counts['hash_guard_repaired_surface_rows']}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: consume the strict-pass surfaces and preserved redesign evidence into the next numeric implementation-selection plate without reviving wrapper or registry work.
"""
    with open(long_path(ACTIVE_LEDGER), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text.rstrip() + "\n\n" + addition.strip() + "\n")


def build_summary(counts: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Expanded-Market Unified Strict Action Surface Repair",
            "",
            "This checkpoint hash-guards broad predicates and re-executes every action surface against held action rows.",
            "",
            "## Counts",
            "",
            f"- Strict surface rows: `{counts['strict_surface_rows']}`",
            f"- Strict surface execution rows: `{counts['strict_surface_execution_rows']}`",
            f"- Strict member execution rows: `{counts['strict_member_execution_rows']}`",
            f"- Strict redesign preservation rows: `{counts['strict_redesign_preservation_rows']}`",
            f"- Repair proof rows: `{counts['strict_repair_proof_rows']}`",
            f"- Aggregate rows: `{counts['aggregate_rows']}`",
            f"- Issue rows: `{counts['issue_rows']}`",
            f"- Strict surface pass rows: `{counts['strict_surface_execution_pass_rows']}`",
            f"- Strict member pass rows: `{counts['strict_member_execution_pass_rows']}`",
            f"- Hash-guard repaired surface rows: `{counts['hash_guard_repaired_surface_rows']}`",
            "",
            "## Continuation",
            "",
            "Consume strict-pass surfaces and preserved redesign evidence into the next numeric implementation-selection plate.",
            "",
        ]
    )


def main() -> None:
    generated_at = now_utc()
    action_result = read_json(ACTION_RESULT)
    surface_result = read_json(SURFACE_RESULT)
    execution_result = read_json(EXECUTION_RESULT)
    evidence_actions = read_jsonl(EVIDENCE_ACTION_LEDGER)
    decision_actions = read_jsonl(DECISION_ACTION_LEDGER)
    terminal_actions = read_jsonl(TERMINAL_ACTION_LEDGER)
    surfaces = read_jsonl(SURFACE_LEDGER)
    members = read_jsonl(MEMBER_LEDGER)
    redesign_executions = read_jsonl(EXECUTION_REDESIGN_LEDGER)
    previous_issues = read_jsonl(EXECUTION_ISSUE_LEDGER)
    (
        strict_surfaces,
        strict_executions,
        member_executions,
        redesign_preservations,
        repair_proofs,
        aggregates,
        issues,
    ) = unified_strict_action_surface_repair_rows(
        surfaces,
        members,
        redesign_executions,
        previous_issues,
        evidence_actions,
        decision_actions,
        terminal_actions,
    )
    input_counts = {
        "input_action_result_ok": action_result.get("ok"),
        "input_surface_result_ok": surface_result.get("ok"),
        "input_execution_result_ok": execution_result.get("ok"),
        "input_evidence_action_rows": len(evidence_actions),
        "input_decision_action_rows": len(decision_actions),
        "input_terminal_action_rows": len(terminal_actions),
        "input_surface_rows": len(surfaces),
        "input_surface_member_rows": len(members),
        "input_redesign_execution_rows": len(redesign_executions),
        "input_previous_issue_rows": len(previous_issues),
    }
    system_rows = system_unified_strict_action_surface_repair_rows(
        strict_surfaces,
        strict_executions,
        member_executions,
        redesign_preservations,
        repair_proofs,
        aggregates,
        issues,
        input_counts,
    )
    counts = {
        "input_evidence_action_rows": len(evidence_actions),
        "input_decision_action_rows": len(decision_actions),
        "input_terminal_action_rows": len(terminal_actions),
        "input_surface_rows": len(surfaces),
        "input_surface_member_rows": len(members),
        "input_redesign_execution_rows": len(redesign_executions),
        "input_previous_issue_rows": len(previous_issues),
        "strict_surface_rows": len(strict_surfaces),
        "strict_surface_execution_rows": len(strict_executions),
        "strict_member_execution_rows": len(member_executions),
        "strict_redesign_preservation_rows": len(redesign_preservations),
        "strict_repair_proof_rows": len(repair_proofs),
        "aggregate_rows": len(aggregates),
        "issue_rows": len(issues),
        "system_rows": len(system_rows),
        "strict_surface_execution_pass_rows": sum(
            1
            for row in strict_executions
            if row.get("strict_execution_status") == "STRICT_ACTION_SURFACE_EXECUTION_PASS"
        ),
        "strict_member_execution_pass_rows": sum(
            1
            for row in member_executions
            if row.get("strict_member_execution_status") == "STRICT_ACTION_SURFACE_MEMBER_EXECUTION_PASS"
        ),
        "hash_guard_repaired_surface_rows": sum(
            1
            for row in strict_surfaces
            if row.get("strict_repair_mode") == "HASH_GUARD_REPAIRED_PREDICATE_BREADTH"
        ),
        "member_rows_with_simulated_r": sum(1 for row in member_executions if row.get("missing_simulated_field") is None),
        "redesign_rows_with_simulated_r": sum(
            1 for row in redesign_preservations if row.get("missing_simulated_field") is None
        ),
    }
    write_jsonl(STRICT_SURFACE_LEDGER, strict_surfaces)
    write_jsonl(STRICT_SURFACE_EXECUTION_LEDGER, strict_executions)
    write_jsonl(STRICT_MEMBER_EXECUTION_LEDGER, member_executions)
    write_jsonl(STRICT_REDESIGN_PRESERVATION_LEDGER, redesign_preservations)
    write_jsonl(STRICT_REPAIR_PROOF_LEDGER, repair_proofs)
    write_jsonl(AGGREGATE_LEDGER, aggregates)
    write_jsonl(ISSUE_LEDGER, issues)
    write_jsonl(SYSTEM_LEDGER, system_rows)
    write_text(SUMMARY_PATH, build_summary(counts))
    outputs = [
        STRICT_SURFACE_LEDGER,
        STRICT_SURFACE_EXECUTION_LEDGER,
        STRICT_MEMBER_EXECUTION_LEDGER,
        STRICT_REDESIGN_PRESERVATION_LEDGER,
        STRICT_REPAIR_PROOF_LEDGER,
        AGGREGATE_LEDGER,
        ISSUE_LEDGER,
        SYSTEM_LEDGER,
        SUMMARY_PATH,
    ]
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "ok": True,
        "expanded_market_unified_strict_action_surface_repair_surface": (
            EXPANDED_MARKET_UNIFIED_STRICT_ACTION_SURFACE_REPAIR_SURFACE
        ),
        "inputs": {
            "action_result": str(ACTION_RESULT.relative_to(REPO)).replace("\\", "/"),
            "surface_result": str(SURFACE_RESULT.relative_to(REPO)).replace("\\", "/"),
            "execution_result": str(EXECUTION_RESULT.relative_to(REPO)).replace("\\", "/"),
            "evidence_action_ledger": str(EVIDENCE_ACTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "decision_action_ledger": str(DECISION_ACTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "terminal_action_ledger": str(TERMINAL_ACTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "surface_ledger": str(SURFACE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "member_ledger": str(MEMBER_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "redesign_execution_ledger": str(EXECUTION_REDESIGN_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "previous_issue_ledger": str(EXECUTION_ISSUE_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "strict_surface_ledger": str(STRICT_SURFACE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "strict_surface_execution_ledger": str(STRICT_SURFACE_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "strict_member_execution_ledger": str(STRICT_MEMBER_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "strict_redesign_preservation_ledger": str(STRICT_REDESIGN_PRESERVATION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "strict_repair_proof_ledger": str(STRICT_REPAIR_PROOF_LEDGER.relative_to(REPO)).replace("\\", "/"),
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
            "event": "expanded_market_unified_strict_action_surface_repair",
            "checkpoint": 243,
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
