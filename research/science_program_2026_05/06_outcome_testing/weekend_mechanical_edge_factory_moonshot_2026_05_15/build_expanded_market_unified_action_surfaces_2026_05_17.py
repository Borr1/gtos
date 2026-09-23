#!/usr/bin/env python3
"""Build callable surfaces from expanded-market unified implementation actions."""

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

from src.research_infra.moonshot_expanded_market_unified_action_surfaces import (
    EXPANDED_MARKET_UNIFIED_ACTION_SURFACES_SURFACE,
    research_boundary,
    system_unified_action_surface_rows,
    unified_action_surface_rows,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_UNIFIED_IMPLEMENTATION_ACTIONS"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_UNIFIED_ACTION_SURFACES"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
INPUT_EVIDENCE_ACTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_EVIDENCE_ACTION_LEDGER_2026-05-17.jsonl"
INPUT_DECISION_ACTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_DECISION_ACTION_LEDGER_2026-05-17.jsonl"
INPUT_REDESIGN_ACTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_REDESIGN_ACTION_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_expanded_market_unified_action_surfaces.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_expanded_market_unified_action_surfaces_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
SURFACE_LEDGER = ROUTE_DIR / f"{PREFIX}_SURFACE_LEDGER_2026-05-17.jsonl"
MEMBER_LEDGER = ROUTE_DIR / f"{PREFIX}_MEMBER_LEDGER_2026-05-17.jsonl"
SELF_TEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SELF_TEST_LEDGER_2026-05-17.jsonl"
REDESIGN_LEDGER = ROUTE_DIR / f"{PREFIX}_REDESIGN_LEDGER_2026-05-17.jsonl"
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


def update_manifest(generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    entries = [
        (RESULT_PATH, "expanded_market_unified_action_surface_result"),
        (SURFACE_LEDGER, "expanded_market_unified_action_surfaces"),
        (MEMBER_LEDGER, "expanded_market_unified_action_surface_members"),
        (SELF_TEST_LEDGER, "expanded_market_unified_action_surface_self_tests"),
        (REDESIGN_LEDGER, "expanded_market_unified_action_surface_redesign"),
        (AGGREGATE_LEDGER, "expanded_market_unified_action_surface_aggregates"),
        (SYSTEM_LEDGER, "expanded_market_unified_action_surface_system"),
        (SUMMARY_PATH, "expanded_market_unified_action_surface_summary"),
        (BUILDER_MODULE, "expanded_market_unified_action_surface_builder"),
        (VERIFIER_MODULE, "expanded_market_unified_action_surface_verifier"),
        (HELPER_MODULE, "expanded_market_unified_action_surface_helper"),
        (TEST_MODULE, "expanded_market_unified_action_surface_tests"),
    ]
    rows = [
        {"path": str(path.relative_to(REPO)).replace("\\", "/"), "status": "created", "type": kind}
        for path, kind in entries
    ]
    existing = manifest.setdefault("artifacts", [])
    keys = {(row["path"], row["type"]) for row in rows}
    manifest["artifacts"] = [row for row in existing if (row.get("path"), row.get("type")) not in keys] + rows
    manifest["latest_expanded_market_unified_action_surfaces"] = {
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
                if payload.get("checkpoint") == 241 and payload.get("event") == "expanded_market_unified_action_surfaces":
                    continue
                kept_lines.append(stripped)
    kept_lines.append(json.dumps(event, sort_keys=True))
    with open(long_path(SPRINT_LEDGER), "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(kept_lines) + "\n")


def replace_active_checkpoint(generated_at: str, counts: dict[str, Any]) -> None:
    marker = "## Checkpoint 241 - Expanded-Market Unified Action Surfaces"
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

Trigger: direct continuation after Checkpoint 240. Implementation action rows were collapsed into callable branch-local action surfaces with member and self-test rows; redesign actions were preserved separately.

Rows:
- action surface rows: {counts['action_surface_rows']}
- action surface member rows: {counts['action_surface_member_rows']}
- self-test rows: {counts['action_surface_self_test_rows']}
- redesign rows: {counts['action_surface_redesign_rows']}
- aggregate rows: {counts['aggregate_rows']}
- member match rows: {counts['surface_member_match_rows']}
- self-test pass rows: {counts['self_test_pass_rows']}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: execute callable action surfaces against the held implementation-action rows and preserve mismatches or redesign rows with numeric proof.
"""
    with open(long_path(ACTIVE_LEDGER), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text.rstrip() + "\n\n" + addition.strip() + "\n")


def build_summary(counts: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Expanded-Market Unified Action Surfaces",
            "",
            "This checkpoint turns implementation actions into callable branch-local surfaces with member and self-test rows.",
            "",
            "## Counts",
            "",
            f"- Action surface rows: `{counts['action_surface_rows']}`",
            f"- Action surface member rows: `{counts['action_surface_member_rows']}`",
            f"- Self-test rows: `{counts['action_surface_self_test_rows']}`",
            f"- Redesign rows: `{counts['action_surface_redesign_rows']}`",
            f"- Aggregate rows: `{counts['aggregate_rows']}`",
            f"- Member match rows: `{counts['surface_member_match_rows']}`",
            f"- Self-test pass rows: `{counts['self_test_pass_rows']}`",
            "",
            "## Continuation",
            "",
            "Execute callable action surfaces against the held implementation-action rows and preserve mismatches or redesign rows with numeric proof.",
            "",
        ]
    )


def main() -> None:
    generated_at = now_utc()
    input_result = read_json(INPUT_RESULT)
    evidence_actions = read_jsonl(INPUT_EVIDENCE_ACTION_LEDGER)
    decision_actions = read_jsonl(INPUT_DECISION_ACTION_LEDGER)
    redesign_actions = read_jsonl(INPUT_REDESIGN_ACTION_LEDGER)
    surfaces, members, self_tests, redesign_rows, aggregates = unified_action_surface_rows(
        evidence_actions, decision_actions, redesign_actions
    )
    input_counts = {
        "input_result_ok": input_result.get("ok"),
        "input_evidence_action_rows": len(evidence_actions),
        "input_decision_action_rows": len(decision_actions),
        "input_redesign_action_rows": len(redesign_actions),
    }
    system_rows = system_unified_action_surface_rows(surfaces, members, self_tests, redesign_rows, aggregates, input_counts)
    counts = {
        "input_evidence_action_rows": len(evidence_actions),
        "input_decision_action_rows": len(decision_actions),
        "input_redesign_action_rows": len(redesign_actions),
        "action_surface_rows": len(surfaces),
        "action_surface_member_rows": len(members),
        "action_surface_self_test_rows": len(self_tests),
        "action_surface_redesign_rows": len(redesign_rows),
        "aggregate_rows": len(aggregates),
        "system_rows": len(system_rows),
        "surface_member_match_rows": sum(1 for row in members if row.get("surface_member_match")),
        "self_test_pass_rows": sum(
            1
            for row in self_tests
            if row.get("positive_scope_match") is True and row.get("negative_scope_mismatch_rejected") is True
        ),
    }
    write_jsonl(SURFACE_LEDGER, surfaces)
    write_jsonl(MEMBER_LEDGER, members)
    write_jsonl(SELF_TEST_LEDGER, self_tests)
    write_jsonl(REDESIGN_LEDGER, redesign_rows)
    write_jsonl(AGGREGATE_LEDGER, aggregates)
    write_jsonl(SYSTEM_LEDGER, system_rows)
    write_text(SUMMARY_PATH, build_summary(counts))
    outputs = [SURFACE_LEDGER, MEMBER_LEDGER, SELF_TEST_LEDGER, REDESIGN_LEDGER, AGGREGATE_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "ok": True,
        "expanded_market_unified_action_surfaces_surface": EXPANDED_MARKET_UNIFIED_ACTION_SURFACES_SURFACE,
        "inputs": {
            "input_result": str(INPUT_RESULT.relative_to(REPO)).replace("\\", "/"),
            "input_evidence_action_ledger": str(INPUT_EVIDENCE_ACTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "input_decision_action_ledger": str(INPUT_DECISION_ACTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "input_redesign_action_ledger": str(INPUT_REDESIGN_ACTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "surface_ledger": str(SURFACE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "member_ledger": str(MEMBER_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "self_test_ledger": str(SELF_TEST_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "redesign_ledger": str(REDESIGN_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
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
            "event": "expanded_market_unified_action_surfaces",
            "checkpoint": 241,
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
