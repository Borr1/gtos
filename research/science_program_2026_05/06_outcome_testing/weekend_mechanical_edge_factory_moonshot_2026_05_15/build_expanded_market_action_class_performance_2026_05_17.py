#!/usr/bin/env python3
"""Build action-class performance rows from scorer-surface execution evidence."""

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

from src.research_infra.moonshot_expanded_market_action_class_performance import (
    EXPANDED_MARKET_ACTION_CLASS_PERFORMANCE,
    action_class_performance_rows,
    aggregate_action_class_rows,
    research_boundary,
    system_action_class_rows,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_DECON_SCORER_EXEC"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_ACTION_CLASS_PERF"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
INPUT_MEMBER_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_MEMBER_EXECUTION_LEDGER_2026-05-17.jsonl"
INPUT_EVIDENCE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_NONIMPLEMENT_EVIDENCE_EXECUTION_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_expanded_market_action_class_performance.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_expanded_market_action_class_performance_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
ROW_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
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
        (RESULT_PATH, "expanded_market_action_class_performance_result"),
        (ROW_LEDGER, "expanded_market_action_class_performance_rows"),
        (AGGREGATE_LEDGER, "expanded_market_action_class_performance_aggregates"),
        (ISSUE_LEDGER, "expanded_market_action_class_performance_issues"),
        (SYSTEM_LEDGER, "expanded_market_action_class_performance_system"),
        (SUMMARY_PATH, "expanded_market_action_class_performance_summary"),
        (BUILDER_MODULE, "expanded_market_action_class_performance_builder"),
        (VERIFIER_MODULE, "expanded_market_action_class_performance_verifier"),
        (HELPER_MODULE, "expanded_market_action_class_performance_helper"),
        (TEST_MODULE, "expanded_market_action_class_performance_tests"),
    ]
    rows = [
        {"path": str(path.relative_to(REPO)).replace("\\", "/"), "status": "created", "type": kind}
        for path, kind in entries
    ]
    existing = manifest.setdefault("artifacts", [])
    types = {row["type"] for row in rows}
    manifest["artifacts"] = [row for row in existing if row.get("type") not in types] + rows
    manifest["latest_expanded_market_action_class_performance"] = {
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
    marker = "## Checkpoint 252 - Expanded-Market Action-Class Performance"
    text = ACTIVE_LEDGER.read_text(encoding="utf-8", errors="replace") if ACTIVE_LEDGER.exists() else ""
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n\n"
    addition = f"""{marker}

Generated: {generated_at}

Trigger: direct continuation after Checkpoint 251. Clean follow rows and preserved non-implement rows were converted into action-class performance rows with observed R, saved-R, proxy-inverse R where available, and explicit redesign action-missing fields.

Rows:
- input member execution rows: {counts["input_member_execution_rows"]}
- input evidence execution rows: {counts["input_evidence_execution_rows"]}
- action-class performance rows: {counts["action_class_performance_rows"]}
- scored action rows: {counts["scored_action_rows"]}
- missing action rows: {counts["missing_action_rows"]}
- aggregate rows: {counts["aggregate_rows"]}
- issue rows: {counts["issue_rows"]}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: use action-class performance aggregates to drive concrete source-repair or implementation-priority execution; preserve every row.
"""
    write_text(ACTIVE_LEDGER, text.rstrip() + "\n\n" + addition)


def build_summary(generated_at: str, counts: dict[str, Any], result: dict[str, Any]) -> str:
    return f"""# Expanded-Market Action-Class Performance

Generated: {generated_at}

## Inputs

- Member execution rows: `{counts["input_member_execution_rows"]}`
- Evidence execution rows: `{counts["input_evidence_execution_rows"]}`

## Outputs

- Action-class performance rows: `{counts["action_class_performance_rows"]}`
- Scored action rows: `{counts["scored_action_rows"]}`
- Missing action rows: `{counts["missing_action_rows"]}`
- Aggregate rows: `{counts["aggregate_rows"]}`
- Issue rows: `{counts["issue_rows"]}`

## Result

- ok: `{result["ok"]}`
- issues: `{result["issues"]}`
"""


def main() -> None:
    generated_at = now_utc()
    input_result = read_json(INPUT_RESULT)
    member_rows = read_jsonl(INPUT_MEMBER_LEDGER)
    evidence_rows = read_jsonl(INPUT_EVIDENCE_LEDGER)
    action_rows, issue_rows = action_class_performance_rows(member_rows, evidence_rows)
    aggregate_rows = aggregate_action_class_rows(action_rows)
    metadata = {
        "input_scorer_surface_execution_result_ok": input_result.get("ok"),
        "input_member_execution_rows": len(member_rows),
        "input_evidence_execution_rows": len(evidence_rows),
    }
    system_rows = system_action_class_rows(action_rows, aggregate_rows, issue_rows, metadata)
    counts = {
        "input_member_execution_rows": len(member_rows),
        "input_evidence_execution_rows": len(evidence_rows),
        "action_class_performance_rows": len(action_rows),
        "scored_action_rows": system_rows[0].get("scored_action_rows"),
        "missing_action_rows": system_rows[0].get("missing_action_rows"),
        "aggregate_rows": len(aggregate_rows),
        "issue_rows": len(issue_rows),
        "action_class_counts": system_rows[0].get("action_class_counts"),
        "decision_counts": system_rows[0].get("decision_counts"),
        "source_path_count": system_rows[0].get("source_path_count"),
        "symbol_family_count": system_rows[0].get("symbol_family_count"),
        "system_rows": len(system_rows),
    }
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "ok": not issue_rows,
        "issues": issue_rows,
        "expanded_market_action_class_performance_surface": EXPANDED_MARKET_ACTION_CLASS_PERFORMANCE,
        "research_boundary": research_boundary(),
        "inputs": {
            "scorer_surface_execution_result": str(INPUT_RESULT.relative_to(REPO)).replace("\\", "/"),
            "member_execution_rows": str(INPUT_MEMBER_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "nonimplement_evidence_execution_rows": str(INPUT_EVIDENCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "row_ledger": str(ROW_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "issue_ledger": str(ISSUE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
        "counts": counts,
    }

    write_jsonl(ROW_LEDGER, action_rows)
    write_jsonl(AGGREGATE_LEDGER, aggregate_rows)
    write_jsonl(ISSUE_LEDGER, issue_rows)
    write_jsonl(SYSTEM_LEDGER, system_rows)
    write_text(SUMMARY_PATH, build_summary(generated_at, counts, result))
    result["output_sha256"] = output_sha256([ROW_LEDGER, AGGREGATE_LEDGER, ISSUE_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH])
    write_json(RESULT_PATH, result)
    update_manifest(generated_at)
    replace_sprint_event(
        {
            "event": "checkpoint_252_expanded_market_action_class_performance",
            "generated_utc": generated_at,
            "result": str(RESULT_PATH.relative_to(REPO)).replace("\\", "/"),
            "counts": counts,
            "boundary": research_boundary(),
        }
    )
    replace_active_checkpoint(generated_at, counts)
    print(json.dumps({"ok": result["ok"], "counts": counts}, indent=2, sort_keys=True))
    if issue_rows:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
