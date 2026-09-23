#!/usr/bin/env python3
"""Build and execute final branch-local artifacts from implementation candidates."""

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

from src.research_infra.moonshot_expanded_market_final_branch_artifacts import (
    EXPANDED_MARKET_FINAL_BRANCH_ARTIFACTS_SURFACE,
    aggregate_artifact_rows,
    artifact_evidence_execution_rows,
    final_artifact_rows,
    research_boundary,
    system_artifact_rows,
)


CANDIDATE_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_REDUCED_IMPLEMENTATION_CANDIDATES"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_FINAL_BRANCH_ARTIFACTS"

CANDIDATE_RESULT = ROUTE_DIR / f"{CANDIDATE_PREFIX}_RESULT_2026-05-17.json"
CANDIDATE_LEDGER = ROUTE_DIR / f"{CANDIDATE_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
EVIDENCE_LEDGER = ROUTE_DIR / f"{CANDIDATE_PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_expanded_market_final_branch_artifacts.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_expanded_market_final_branch_artifacts_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
ARTIFACT_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
EVIDENCE_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_EVIDENCE_EXECUTION_LEDGER_2026-05-17.jsonl"
CONTROL_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTROL_LEDGER_2026-05-17.jsonl"
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
        (RESULT_PATH, "expanded_market_final_branch_artifacts_result"),
        (ARTIFACT_LEDGER, "expanded_market_final_branch_artifact_rows"),
        (EVIDENCE_EXECUTION_LEDGER, "expanded_market_final_branch_artifact_evidence_execution"),
        (CONTROL_LEDGER, "expanded_market_final_branch_artifact_controls"),
        (AGGREGATE_LEDGER, "expanded_market_final_branch_artifact_aggregates"),
        (SYSTEM_LEDGER, "expanded_market_final_branch_artifact_system"),
        (SUMMARY_PATH, "expanded_market_final_branch_artifacts_summary"),
        (BUILDER_MODULE, "expanded_market_final_branch_artifacts_builder"),
        (VERIFIER_MODULE, "expanded_market_final_branch_artifacts_verifier"),
        (HELPER_MODULE, "expanded_market_final_branch_artifacts_helper"),
        (TEST_MODULE, "expanded_market_final_branch_artifacts_tests"),
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
    manifest["latest_expanded_market_final_branch_artifacts"] = {
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
                if payload.get("checkpoint") == 226 and payload.get("event") == "expanded_market_final_branch_artifacts":
                    continue
                kept_lines.append(stripped)
    kept_lines.append(json.dumps(event, sort_keys=True))
    with open(long_path(SPRINT_LEDGER), "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(kept_lines) + "\n")


def replace_active_checkpoint(generated_at: str, counts: dict[str, Any]) -> None:
    marker = "## Checkpoint 226 - Expanded-Market Final Branch Artifacts"
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

Trigger: direct continuation after Checkpoint 225. Ready implementation candidates were materialized as final branch-local artifacts and executed against row-addressable replay evidence plus mismatch controls.

Rows:
- input implementation candidate rows: {counts['input_candidate_rows']}
- input implementation evidence rows: {counts['input_evidence_rows']}
- final branch artifact rows: {counts['final_branch_artifact_rows']}
- artifact evidence execution rows: {counts['artifact_evidence_execution_rows']}
- artifact control rows: {counts['artifact_control_rows']}
- aggregate rows: {counts['aggregate_rows']}
- ready artifact rows: {counts['ready_artifact_rows']}
- evidence execution pass rows: {counts['evidence_execution_pass_rows']}
- control rejected rows: {counts['control_rejected_rows']}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: use the final artifact/evidence ledgers for portfolio-level artifact selection, concentration checks, and kill/redesign preservation.
"""
    with open(long_path(ACTIVE_LEDGER), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text.rstrip() + "\n\n" + addition.strip() + "\n")


def build_summary(counts: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Expanded-Market Final Branch Artifacts",
            "",
            "This checkpoint materializes final branch-local artifacts from ready implementation candidates and executes them against replay evidence plus mismatch controls.",
            "",
            "## Counts",
            "",
            f"- Input implementation candidate rows: `{counts['input_candidate_rows']}`",
            f"- Input implementation evidence rows: `{counts['input_evidence_rows']}`",
            f"- Final branch artifact rows: `{counts['final_branch_artifact_rows']}`",
            f"- Artifact evidence execution rows: `{counts['artifact_evidence_execution_rows']}`",
            f"- Artifact control rows: `{counts['artifact_control_rows']}`",
            f"- Aggregate rows: `{counts['aggregate_rows']}`",
            f"- Ready artifact rows: `{counts['ready_artifact_rows']}`",
            f"- Evidence execution pass rows: `{counts['evidence_execution_pass_rows']}`",
            f"- Control rejected rows: `{counts['control_rejected_rows']}`",
            "",
            "## Decisions",
            "",
            f"`{json.dumps(counts['decision_counts'], sort_keys=True)}`",
            "",
            "## Continuation",
            "",
            "Use the final artifact/evidence ledgers for portfolio-level artifact selection, concentration checks, and kill/redesign preservation.",
            "",
        ]
    )


def main() -> None:
    generated_at = now_utc()
    candidate_result = read_json(CANDIDATE_RESULT)
    candidates = read_jsonl(CANDIDATE_LEDGER)
    evidence = read_jsonl(EVIDENCE_LEDGER)
    artifacts = final_artifact_rows(candidates)
    evidence_executions, controls = artifact_evidence_execution_rows(artifacts, evidence)
    aggregates = aggregate_artifact_rows(artifacts)
    system_rows = system_artifact_rows(artifacts, evidence_executions, controls, aggregates, len(candidates), len(evidence))
    decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in artifacts)
    counts = {
        "input_result_ok": bool(candidate_result.get("ok")),
        "input_candidate_rows": len(candidates),
        "input_evidence_rows": len(evidence),
        "final_branch_artifact_rows": len(artifacts),
        "artifact_evidence_execution_rows": len(evidence_executions),
        "artifact_control_rows": len(controls),
        "aggregate_rows": len(aggregates),
        "system_rows": len(system_rows),
        "ready_artifact_rows": sum(
            1 for row in artifacts if row.get("artifact_status") == "FINAL_BRANCH_LOCAL_ARTIFACT_READY"
        ),
        "evidence_execution_pass_rows": sum(
            1 for row in evidence_executions if row.get("artifact_match") is True
        ),
        "control_rejected_rows": sum(1 for row in controls if row.get("control_rejected") is True),
        "decision_counts": dict(sorted(decisions.items())),
    }
    write_jsonl(ARTIFACT_LEDGER, artifacts)
    write_jsonl(EVIDENCE_EXECUTION_LEDGER, evidence_executions)
    write_jsonl(CONTROL_LEDGER, controls)
    write_jsonl(AGGREGATE_LEDGER, aggregates)
    write_jsonl(SYSTEM_LEDGER, system_rows)
    write_text(SUMMARY_PATH, build_summary(counts))
    output_files = [ARTIFACT_LEDGER, EVIDENCE_EXECUTION_LEDGER, CONTROL_LEDGER, AGGREGATE_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]
    result = {
        "ok": True,
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "counts": counts,
        "inputs": {
            "candidate_result": str(CANDIDATE_RESULT.relative_to(REPO)).replace("\\", "/"),
            "candidate_ledger": str(CANDIDATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "evidence_ledger": str(EVIDENCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "artifact_ledger": str(ARTIFACT_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "evidence_execution_ledger": str(EVIDENCE_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "control_ledger": str(CONTROL_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
        "output_sha256": output_sha256(output_files),
        "research_boundary": research_boundary(),
        "expanded_market_final_branch_artifacts_surface": EXPANDED_MARKET_FINAL_BRANCH_ARTIFACTS_SURFACE,
    }
    write_json(RESULT_PATH, result)
    update_manifest(generated_at)
    replace_sprint_event(
        {
            "checkpoint": 226,
            "event": "expanded_market_final_branch_artifacts",
            "generated_utc": generated_at,
            "input_candidate_rows": counts["input_candidate_rows"],
            "final_branch_artifact_rows": counts["final_branch_artifact_rows"],
            "artifact_evidence_execution_rows": counts["artifact_evidence_execution_rows"],
            "artifact_control_rows": counts["artifact_control_rows"],
            "aggregate_rows": counts["aggregate_rows"],
            "ready_artifact_rows": counts["ready_artifact_rows"],
            "continuation": "continue to portfolio-level artifact selection, concentration checks, and kill/redesign preservation.",
            "boundary": research_boundary(),
        }
    )
    replace_active_checkpoint(generated_at, counts)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
