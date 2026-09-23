#!/usr/bin/env python3
"""Execute final branch-local repair artifacts against held repair executions."""

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

from src.research_infra.moonshot_expanded_market_repair_final_artifact_execution import (
    EXPANDED_MARKET_REPAIR_FINAL_ARTIFACT_EXECUTION,
    aggregate_key,
    aggregate_rows_from_buckets,
    boundary_row,
    control_execution_row,
    empty_bucket,
    evidence_execution_row,
    final_artifact_execution_row,
    issue_rows,
    research_boundary,
    update_bucket,
)


INPUT_ARTIFACT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_REPAIR_FINAL_ARTIFACTS"
INPUT_EXECUTION_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_REPAIR_APPLICATION_EXECUTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_REPAIR_FINAL_ARTIFACT_EXECUTION"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_ARTIFACT_PREFIX}_RESULT_2026-05-17.json"
INPUT_ARTIFACT_LEDGER = ROUTE_DIR / f"{INPUT_ARTIFACT_PREFIX}_ARTIFACT_LEDGER_2026-05-17.jsonl"
INPUT_EVIDENCE_LEDGER = ROUTE_DIR / f"{INPUT_ARTIFACT_PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"
INPUT_CONTROL_LEDGER = ROUTE_DIR / f"{INPUT_ARTIFACT_PREFIX}_CONTROL_LEDGER_2026-05-17.jsonl"
HELD_EXECUTION_LEDGER = ROUTE_DIR / f"{INPUT_EXECUTION_PREFIX}_APPLICATION_EXECUTION_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_expanded_market_repair_final_artifact_execution.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_expanded_market_repair_final_artifact_execution_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
ARTIFACT_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_ARTIFACT_EXECUTION_LEDGER_2026-05-17.jsonl"
EVIDENCE_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_EVIDENCE_EXECUTION_LEDGER_2026-05-17.jsonl"
CONTROL_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTROL_EXECUTION_LEDGER_2026-05-17.jsonl"
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


def load_by_id(path: Path, field: str) -> dict[str, dict[str, Any]]:
    return {str(row.get(field) or ""): row for row in iter_jsonl(path)}


def update_manifest(generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    entries = [
        (RESULT_PATH, "expanded_market_repair_final_artifact_execution_result"),
        (ARTIFACT_EXECUTION_LEDGER, "expanded_market_repair_final_artifact_execution_rows"),
        (EVIDENCE_EXECUTION_LEDGER, "expanded_market_repair_final_artifact_execution_evidence"),
        (CONTROL_EXECUTION_LEDGER, "expanded_market_repair_final_artifact_execution_controls"),
        (AGGREGATE_LEDGER, "expanded_market_repair_final_artifact_execution_aggregates"),
        (ISSUE_LEDGER, "expanded_market_repair_final_artifact_execution_issues"),
        (SYSTEM_LEDGER, "expanded_market_repair_final_artifact_execution_system"),
        (SUMMARY_PATH, "expanded_market_repair_final_artifact_execution_summary"),
        (BUILDER_MODULE, "expanded_market_repair_final_artifact_execution_builder"),
        (VERIFIER_MODULE, "expanded_market_repair_final_artifact_execution_verifier"),
        (HELPER_MODULE, "expanded_market_repair_final_artifact_execution_helper"),
        (TEST_MODULE, "expanded_market_repair_final_artifact_execution_tests"),
    ]
    rows = [
        {"path": str(path.relative_to(REPO)).replace("\\", "/"), "status": "created", "type": kind}
        for path, kind in entries
    ]
    existing = manifest.setdefault("artifacts", [])
    types = {row["type"] for row in rows}
    manifest["artifacts"] = [row for row in existing if row.get("type") not in types] + rows
    manifest["latest_expanded_market_repair_final_artifact_execution"] = {
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
    marker = "## Checkpoint 261 - Expanded-Market Repair Final Artifact Execution"
    text = ACTIVE_LEDGER.read_text(encoding="utf-8", errors="replace") if ACTIVE_LEDGER.exists() else ""
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n\n"
    addition = f"""{marker}

Generated: {generated_at}

Trigger: direct continuation after Checkpoint 260. Final branch-local repair artifacts were executed against held repair-application execution rows; evidence rows were preserved.

Rows:
- final artifact execution rows: {counts["artifact_execution_rows"]}
- final artifact execution pass rows: {counts["artifact_execution_pass_rows"]}
- evidence execution rows: {counts["evidence_execution_rows"]}
- control execution rows: {counts["control_execution_rows"]}
- control execution pass rows: {counts["control_execution_pass_rows"]}
- aggregate rows: {counts["aggregate_rows"]}
- issue rows: {counts["issue_rows"]}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: use the passing final artifact executions as the implementation handoff packet while preserving all evidence rows.
"""
    write_text(ACTIVE_LEDGER, text.rstrip() + "\n\n" + addition)


def build_summary(generated_at: str, counts: dict[str, Any], result: dict[str, Any]) -> str:
    return f"""# Expanded-Market Repair Final Artifact Execution

Generated: {generated_at}

## Outputs

- Final artifact execution rows: `{counts["artifact_execution_rows"]}`
- Final artifact execution pass rows: `{counts["artifact_execution_pass_rows"]}`
- Evidence execution rows: `{counts["evidence_execution_rows"]}`
- Control execution rows: `{counts["control_execution_rows"]}`
- Issue rows: `{counts["issue_rows"]}`

## Result

- ok: `{result["ok"]}`
- issues: `{result["issues"]}`
"""


def main() -> None:
    generated_at = now_utc()
    input_result = read_json(INPUT_RESULT)
    held_by_id = load_by_id(HELD_EXECUTION_LEDGER, "expanded_market_repair_application_execution_row_id")
    controls_by_artifact_id = load_by_id(INPUT_CONTROL_LEDGER, "input_repair_final_artifact_row_id")
    buckets: dict[tuple[str, ...], dict[str, Any]] = defaultdict(empty_bucket)
    issues: list[dict[str, Any]] = []
    artifact_execution_rows = 0
    artifact_execution_pass_rows = 0
    evidence_execution_rows = 0
    control_execution_rows = 0
    control_execution_pass_rows = 0
    decisions: Counter[str] = Counter()

    with (
        open(long_path(ARTIFACT_EXECUTION_LEDGER), "w", encoding="utf-8", newline="\n") as artifact_handle,
        open(long_path(CONTROL_EXECUTION_LEDGER), "w", encoding="utf-8", newline="\n") as control_handle,
    ):
        for artifact in iter_jsonl(INPUT_ARTIFACT_LEDGER):
            held = held_by_id.get(str(artifact.get("input_repair_application_execution_row_id") or ""))
            artifact_execution_rows += 1
            execution = final_artifact_execution_row(artifact, held, artifact_execution_rows)
            artifact_handle.write(json.dumps(execution, sort_keys=True) + "\n")
            decisions[execution.get("keep_kill_redesign_implement_decision")] += 1
            if execution.get("final_artifact_execution_status") == "EXPANDED_MARKET_REPAIR_FINAL_ARTIFACT_EXECUTION_PASS":
                artifact_execution_pass_rows += 1
            update_bucket(buckets[aggregate_key(execution, "artifact_execution")], execution, "artifact_execution")
            control_execution_rows += 1
            control = controls_by_artifact_id.get(str(artifact.get("expanded_market_repair_final_artifact_row_id") or ""))
            execution_control = control_execution_row(execution, control, control_execution_rows)
            control_handle.write(json.dumps(execution_control, sort_keys=True) + "\n")
            decisions[execution_control.get("keep_kill_redesign_implement_decision")] += 1
            if execution_control.get("control_status") == "EXPANDED_MARKET_REPAIR_FINAL_ARTIFACT_EXECUTION_CONTROL_PASS":
                control_execution_pass_rows += 1
            update_bucket(buckets[aggregate_key(execution_control, "control_execution")], execution_control, "control_execution")
            issues.extend(issue_rows([execution], [execution_control]))

    with open(long_path(EVIDENCE_EXECUTION_LEDGER), "w", encoding="utf-8", newline="\n") as evidence_handle:
        for evidence in iter_jsonl(INPUT_EVIDENCE_LEDGER):
            evidence_execution_rows += 1
            evidence_execution = evidence_execution_row(evidence, evidence_execution_rows)
            evidence_handle.write(json.dumps(evidence_execution, sort_keys=True) + "\n")
            decisions[evidence_execution.get("keep_kill_redesign_implement_decision")] += 1
            update_bucket(buckets[aggregate_key(evidence_execution, "evidence_execution")], evidence_execution, "evidence")

    aggregate_rows = aggregate_rows_from_buckets(buckets)
    system_rows = [
        boundary_row(
            {
                "expanded_market_repair_final_artifact_execution_system_row_id": (
                    "OHLC-GTOS-EXPANDED-MARKET-REPAIR-FINAL-ARTIFACT-EXEC-SYSTEM-0001"
                ),
                "artifact_execution_rows": artifact_execution_rows,
                "artifact_execution_pass_rows": artifact_execution_pass_rows,
                "evidence_execution_rows": evidence_execution_rows,
                "control_execution_rows": control_execution_rows,
                "control_execution_pass_rows": control_execution_pass_rows,
                "aggregate_rows": len(aggregate_rows),
                "issue_rows": len(issues),
                "decision_counts": dict(sorted(decisions.items())),
                "metadata": {
                    "input_repair_final_artifacts_result_ok": input_result.get("ok"),
                    "no_top_n_cutoff": True,
                },
            }
        )
    ]
    counts = {
        "artifact_execution_rows": artifact_execution_rows,
        "artifact_execution_pass_rows": artifact_execution_pass_rows,
        "evidence_execution_rows": evidence_execution_rows,
        "control_execution_rows": control_execution_rows,
        "control_execution_pass_rows": control_execution_pass_rows,
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
        "expanded_market_repair_final_artifact_execution_surface": EXPANDED_MARKET_REPAIR_FINAL_ARTIFACT_EXECUTION,
        "research_boundary": research_boundary(),
        "inputs": {
            "repair_final_artifacts_result": str(INPUT_RESULT.relative_to(REPO)).replace("\\", "/"),
            "repair_final_artifact_rows": str(INPUT_ARTIFACT_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "repair_final_artifact_evidence_rows": str(INPUT_EVIDENCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "repair_final_artifact_control_rows": str(INPUT_CONTROL_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "held_repair_application_execution_rows": str(HELD_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "artifact_execution_ledger": str(ARTIFACT_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "evidence_execution_ledger": str(EVIDENCE_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "control_execution_ledger": str(CONTROL_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
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
    result["output_sha256"] = output_sha256([ARTIFACT_EXECUTION_LEDGER, EVIDENCE_EXECUTION_LEDGER, CONTROL_EXECUTION_LEDGER, AGGREGATE_LEDGER, ISSUE_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH])
    write_json(RESULT_PATH, result)
    update_manifest(generated_at)
    replace_sprint_event(
        {
            "event": "checkpoint_261_expanded_market_repair_final_artifact_execution",
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
