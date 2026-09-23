#!/usr/bin/env python3
"""Build implementation handoff packet from final artifact executions."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_expanded_market_repair_implementation_handoff import (
    EXPANDED_MARKET_REPAIR_IMPLEMENTATION_HANDOFF,
    aggregate_key,
    aggregate_rows_from_buckets,
    boundary_row,
    empty_bucket,
    evidence_handoff_row,
    handoff_control_row,
    handoff_row,
    issue_rows,
    research_boundary,
    update_bucket,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_REPAIR_FINAL_ARTIFACT_EXECUTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_REPAIR_IMPLEMENTATION_HANDOFF"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
INPUT_ARTIFACT_EXECUTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_ARTIFACT_EXECUTION_LEDGER_2026-05-17.jsonl"
INPUT_EVIDENCE_EXECUTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_EVIDENCE_EXECUTION_LEDGER_2026-05-17.jsonl"
INPUT_CONTROL_EXECUTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_CONTROL_EXECUTION_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_expanded_market_repair_implementation_handoff.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_expanded_market_repair_implementation_handoff_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
HANDOFF_LEDGER = ROUTE_DIR / f"{PREFIX}_HANDOFF_LEDGER_2026-05-17.jsonl"
EVIDENCE_LEDGER = ROUTE_DIR / f"{PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"
CONTROL_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTROL_LEDGER_2026-05-17.jsonl"
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


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with open(long_path(path), "r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


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


def load_controls() -> dict[str, dict[str, Any]]:
    return {
        str(row.get("input_repair_final_artifact_execution_row_id") or ""): row
        for row in iter_jsonl(INPUT_CONTROL_EXECUTION_LEDGER)
    }


def update_manifest(generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    entries = [
        (RESULT_PATH, "expanded_market_repair_implementation_handoff_result"),
        (HANDOFF_LEDGER, "expanded_market_repair_implementation_handoff_rows"),
        (EVIDENCE_LEDGER, "expanded_market_repair_implementation_handoff_evidence"),
        (CONTROL_LEDGER, "expanded_market_repair_implementation_handoff_controls"),
        (AGGREGATE_LEDGER, "expanded_market_repair_implementation_handoff_aggregates"),
        (ISSUE_LEDGER, "expanded_market_repair_implementation_handoff_issues"),
        (SYSTEM_LEDGER, "expanded_market_repair_implementation_handoff_system"),
        (SUMMARY_PATH, "expanded_market_repair_implementation_handoff_summary"),
        (BUILDER_MODULE, "expanded_market_repair_implementation_handoff_builder"),
        (VERIFIER_MODULE, "expanded_market_repair_implementation_handoff_verifier"),
        (HELPER_MODULE, "expanded_market_repair_implementation_handoff_helper"),
        (TEST_MODULE, "expanded_market_repair_implementation_handoff_tests"),
    ]
    rows = [
        {"path": str(path.relative_to(REPO)).replace("\\", "/"), "status": "created", "type": kind}
        for path, kind in entries
    ]
    existing = manifest.setdefault("artifacts", [])
    types = {row["type"] for row in rows}
    manifest["artifacts"] = [row for row in existing if row.get("type") not in types] + rows
    manifest["latest_expanded_market_repair_implementation_handoff"] = {
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
    marker = "## Checkpoint 262 - Expanded-Market Repair Implementation Handoff"
    text = ACTIVE_LEDGER.read_text(encoding="utf-8", errors="replace") if ACTIVE_LEDGER.exists() else ""
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n\n"
    addition = f"""{marker}

Generated: {generated_at}

Trigger: direct continuation after Checkpoint 261. Passing final artifact executions were packaged as branch-local implementation handoff rows with acceptance signatures and controls; evidence rows were preserved.

Rows:
- implementation handoff rows: {counts["implementation_handoff_rows"]}
- ready implementation handoff rows: {counts["ready_implementation_handoff_rows"]}
- evidence rows: {counts["evidence_rows"]}
- control rows: {counts["control_rows"]}
- control pass rows: {counts["control_pass_rows"]}
- aggregate rows: {counts["aggregate_rows"]}
- issue rows: {counts["issue_rows"]}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: execute the implementation handoff packet against held final artifact executions and preserve all evidence rows.
"""
    write_text(ACTIVE_LEDGER, text.rstrip() + "\n\n" + addition)


def build_summary(generated_at: str, counts: dict[str, Any], result: dict[str, Any]) -> str:
    return f"""# Expanded-Market Repair Implementation Handoff

Generated: {generated_at}

## Outputs

- Implementation handoff rows: `{counts["implementation_handoff_rows"]}`
- Ready implementation handoff rows: `{counts["ready_implementation_handoff_rows"]}`
- Evidence rows: `{counts["evidence_rows"]}`
- Control rows: `{counts["control_rows"]}`
- Issue rows: `{counts["issue_rows"]}`

## Result

- ok: `{result["ok"]}`
- issues: `{result["issues"]}`
"""


def main() -> None:
    generated_at = now_utc()
    input_result = read_json(INPUT_RESULT)
    controls_by_execution_id = load_controls()
    buckets: dict[tuple[str, ...], dict[str, Any]] = defaultdict(empty_bucket)
    issues: list[dict[str, Any]] = []
    handoff_rows = 0
    ready_handoff_rows = 0
    evidence_rows = 0
    control_rows = 0
    control_pass_rows = 0
    decisions: Counter[str] = Counter()

    with (
        open(long_path(HANDOFF_LEDGER), "w", encoding="utf-8", newline="\n") as handoff_handle,
        open(long_path(CONTROL_LEDGER), "w", encoding="utf-8", newline="\n") as control_handle,
    ):
        for execution in iter_jsonl(INPUT_ARTIFACT_EXECUTION_LEDGER):
            handoff_rows += 1
            handoff = handoff_row(execution, handoff_rows)
            handoff_handle.write(json.dumps(handoff, sort_keys=True) + "\n")
            decisions[handoff.get("keep_kill_redesign_implement_decision")] += 1
            if handoff.get("implementation_handoff_status") == "BRANCH_LOCAL_REPAIR_IMPLEMENTATION_HANDOFF_READY":
                ready_handoff_rows += 1
            update_bucket(buckets[aggregate_key(handoff, "handoff")], handoff, "handoff")
            control_rows += 1
            execution_control = controls_by_execution_id.get(
                str(execution.get("expanded_market_repair_final_artifact_execution_row_id") or "")
            )
            control = handoff_control_row(handoff, execution, execution_control, control_rows)
            control_handle.write(json.dumps(control, sort_keys=True) + "\n")
            decisions[control.get("keep_kill_redesign_implement_decision")] += 1
            if control.get("control_status") == "EXPANDED_MARKET_REPAIR_IMPLEMENTATION_HANDOFF_CONTROL_PASS":
                control_pass_rows += 1
            update_bucket(buckets[aggregate_key(control, "control")], control, "control")
            issues.extend(issue_rows([handoff], [control]))

    with open(long_path(EVIDENCE_LEDGER), "w", encoding="utf-8", newline="\n") as evidence_handle:
        for evidence_execution in iter_jsonl(INPUT_EVIDENCE_EXECUTION_LEDGER):
            evidence_rows += 1
            evidence = evidence_handoff_row(evidence_execution, evidence_rows)
            evidence_handle.write(json.dumps(evidence, sort_keys=True) + "\n")
            decisions[evidence.get("keep_kill_redesign_implement_decision")] += 1
            update_bucket(buckets[aggregate_key(evidence, "evidence")], evidence, "evidence")

    aggregate_rows = aggregate_rows_from_buckets(buckets)
    system_rows = [
        boundary_row(
            {
                "expanded_market_repair_implementation_handoff_system_row_id": (
                    "OHLC-GTOS-EXPANDED-MARKET-REPAIR-IMPLEMENTATION-HANDOFF-SYSTEM-0001"
                ),
                "implementation_handoff_rows": handoff_rows,
                "ready_implementation_handoff_rows": ready_handoff_rows,
                "evidence_rows": evidence_rows,
                "control_rows": control_rows,
                "control_pass_rows": control_pass_rows,
                "aggregate_rows": len(aggregate_rows),
                "issue_rows": len(issues),
                "decision_counts": dict(sorted(decisions.items())),
                "metadata": {
                    "input_final_artifact_execution_result_ok": input_result.get("ok"),
                    "no_top_n_cutoff": True,
                },
            }
        )
    ]
    counts = {
        "implementation_handoff_rows": handoff_rows,
        "ready_implementation_handoff_rows": ready_handoff_rows,
        "evidence_rows": evidence_rows,
        "control_rows": control_rows,
        "control_pass_rows": control_pass_rows,
        "aggregate_rows": len(aggregate_rows),
        "issue_rows": len(issues),
        "decision_counts": dict(sorted(decisions.items())),
        "system_rows": len(system_rows),
    }
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "ok": not issues,
        "issues": issues,
        "expanded_market_repair_implementation_handoff_surface": EXPANDED_MARKET_REPAIR_IMPLEMENTATION_HANDOFF,
        "research_boundary": research_boundary(),
        "inputs": {
            "final_artifact_execution_result": str(INPUT_RESULT.relative_to(REPO)).replace("\\", "/"),
            "final_artifact_execution_rows": str(INPUT_ARTIFACT_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "final_artifact_evidence_execution_rows": str(INPUT_EVIDENCE_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "final_artifact_execution_controls": str(INPUT_CONTROL_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "handoff_ledger": str(HANDOFF_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "evidence_ledger": str(EVIDENCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "control_ledger": str(CONTROL_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "issue_ledger": str(ISSUE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
        "counts": counts,
    }
    write_jsonl(AGGREGATE_LEDGER, aggregate_rows)
    write_jsonl(ISSUE_LEDGER, issues)
    write_jsonl(SYSTEM_LEDGER, system_rows)
    write_text(SUMMARY_PATH, build_summary(generated_at, counts, result))
    result["output_sha256"] = output_sha256([HANDOFF_LEDGER, EVIDENCE_LEDGER, CONTROL_LEDGER, AGGREGATE_LEDGER, ISSUE_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH])
    write_json(RESULT_PATH, result)
    update_manifest(generated_at)
    replace_sprint_event(
        {
            "event": "checkpoint_262_expanded_market_repair_implementation_handoff",
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
