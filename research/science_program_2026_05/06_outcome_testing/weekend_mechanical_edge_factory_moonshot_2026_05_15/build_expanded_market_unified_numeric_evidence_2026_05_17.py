#!/usr/bin/env python3
"""Build expanded-market unified numeric evidence checkpoint."""

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

from src.research_infra.moonshot_expanded_market_unified_numeric_evidence import (
    EXPANDED_MARKET_UNIFIED_NUMERIC_EVIDENCE_SURFACE,
    research_boundary,
    system_unified_numeric_evidence_rows,
    unified_numeric_evidence_rows,
)


UNIFIED_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_UNIFIED_FINAL_DECISIONS"
PERFORMANCE_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_PROXY_R_PERFORMANCE"
INTRABAR_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_INTRABAR_GEOMETRY"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_UNIFIED_NUMERIC_EVIDENCE"

UNIFIED_RESULT = ROUTE_DIR / f"{UNIFIED_PREFIX}_RESULT_2026-05-17.json"
UNIFIED_DECISION_LEDGER = ROUTE_DIR / f"{UNIFIED_PREFIX}_DECISION_LEDGER_2026-05-17.jsonl"
UNIFIED_EVIDENCE_LEDGER = ROUTE_DIR / f"{UNIFIED_PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"
UNIFIED_TERMINAL_LEDGER = ROUTE_DIR / f"{UNIFIED_PREFIX}_TERMINAL_REDESIGN_LEDGER_2026-05-17.jsonl"
PERFORMANCE_RESULT = ROUTE_DIR / f"{PERFORMANCE_PREFIX}_RESULT_2026-05-17.json"
PERFORMANCE_LEDGER = ROUTE_DIR / f"{PERFORMANCE_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
INTRABAR_RESULT = ROUTE_DIR / f"{INTRABAR_PREFIX}_RESULT_2026-05-17.json"
INTRABAR_LEDGER = ROUTE_DIR / f"{INTRABAR_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_expanded_market_unified_numeric_evidence.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_expanded_market_unified_numeric_evidence_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
EVIDENCE_LEDGER = ROUTE_DIR / f"{PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"
TERMINAL_LEDGER = ROUTE_DIR / f"{PREFIX}_TERMINAL_LEDGER_2026-05-17.jsonl"
DECISION_LEDGER = ROUTE_DIR / f"{PREFIX}_DECISION_LEDGER_2026-05-17.jsonl"
SOURCE_ACCESS_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_ACCESS_PROOF_LEDGER_2026-05-17.jsonl"
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


def manifest_entries() -> list[dict[str, str]]:
    entries = [
        (RESULT_PATH, "expanded_market_unified_numeric_evidence_result"),
        (EVIDENCE_LEDGER, "expanded_market_unified_numeric_evidence_rows"),
        (TERMINAL_LEDGER, "expanded_market_unified_numeric_terminal_rows"),
        (DECISION_LEDGER, "expanded_market_unified_numeric_decision_rows"),
        (SOURCE_ACCESS_LEDGER, "expanded_market_unified_numeric_source_access"),
        (AGGREGATE_LEDGER, "expanded_market_unified_numeric_aggregates"),
        (ISSUE_LEDGER, "expanded_market_unified_numeric_issues"),
        (SYSTEM_LEDGER, "expanded_market_unified_numeric_system"),
        (SUMMARY_PATH, "expanded_market_unified_numeric_summary"),
        (BUILDER_MODULE, "expanded_market_unified_numeric_builder"),
        (VERIFIER_MODULE, "expanded_market_unified_numeric_verifier"),
        (HELPER_MODULE, "expanded_market_unified_numeric_helper"),
        (TEST_MODULE, "expanded_market_unified_numeric_tests"),
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
    manifest["latest_expanded_market_unified_numeric_evidence"] = {
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
                if payload.get("checkpoint") == 238 and payload.get("event") == "expanded_market_unified_numeric_evidence":
                    continue
                kept_lines.append(stripped)
    kept_lines.append(json.dumps(event, sort_keys=True))
    with open(long_path(SPRINT_LEDGER), "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(kept_lines) + "\n")


def replace_active_checkpoint(generated_at: str, counts: dict[str, Any]) -> None:
    marker = "## Checkpoint 238 - Expanded-Market Unified Numeric Evidence"
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

Trigger: direct correction after Checkpoint 237. Unified final decisions were joined back to expanded-market proxy-R and intrabar geometry rows so final evidence and terminal redesign rows carry numeric replay performance, not another artifact wrapper.

Rows:
- input unified final decision rows: {counts['input_unified_final_decision_rows']}
- input unified final evidence rows: {counts['input_unified_final_evidence_rows']}
- input unified terminal redesign rows: {counts['input_unified_terminal_redesign_rows']}
- unified numeric evidence rows: {counts['unified_numeric_evidence_rows']}
- unified numeric terminal rows: {counts['unified_numeric_terminal_rows']}
- unified numeric decision rows: {counts['unified_numeric_decision_rows']}
- source/access proof rows: {counts['source_access_proof_rows']}
- aggregate rows: {counts['aggregate_rows']}
- issue rows: {counts['issue_rows']}
- rows with simulated R: {counts['rows_with_simulated_r']}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: continue to the next highest-value numeric plate using the joined unified numeric evidence rows; do not continue the package-wrapper chain.
"""
    with open(long_path(ACTIVE_LEDGER), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text.rstrip() + "\n\n" + addition.strip() + "\n")


def build_summary(counts: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Expanded-Market Unified Numeric Evidence",
            "",
            "This checkpoint joins unified final evidence and terminal redesign rows back to expanded-market proxy-R and intrabar geometry rows.",
            "",
            "## Counts",
            "",
            f"- Input unified final decision rows: `{counts['input_unified_final_decision_rows']}`",
            f"- Input unified final evidence rows: `{counts['input_unified_final_evidence_rows']}`",
            f"- Input unified terminal redesign rows: `{counts['input_unified_terminal_redesign_rows']}`",
            f"- Unified numeric evidence rows: `{counts['unified_numeric_evidence_rows']}`",
            f"- Unified numeric terminal rows: `{counts['unified_numeric_terminal_rows']}`",
            f"- Unified numeric decision rows: `{counts['unified_numeric_decision_rows']}`",
            f"- Source/access proof rows: `{counts['source_access_proof_rows']}`",
            f"- Aggregate rows: `{counts['aggregate_rows']}`",
            f"- Issue rows: `{counts['issue_rows']}`",
            f"- Rows with simulated R: `{counts['rows_with_simulated_r']}`",
            "",
            "## Decisions",
            "",
            f"`{json.dumps(counts['decision_counts'], sort_keys=True)}`",
            "",
            "## Continuation",
            "",
            "Continue to the next highest-value numeric plate using this joined evidence, not a package-wrapper continuation.",
            "",
        ]
    )


def main() -> None:
    generated_at = now_utc()
    unified_result = read_json(UNIFIED_RESULT)
    performance_result = read_json(PERFORMANCE_RESULT)
    intrabar_result = read_json(INTRABAR_RESULT)
    decisions = read_jsonl(UNIFIED_DECISION_LEDGER)
    evidence = read_jsonl(UNIFIED_EVIDENCE_LEDGER)
    terminal = read_jsonl(UNIFIED_TERMINAL_LEDGER)
    performance = read_jsonl(PERFORMANCE_LEDGER)
    intrabar = read_jsonl(INTRABAR_LEDGER)

    evidence_rows, terminal_rows, decision_rows, source_access_rows, aggregate_rows, issue_rows = (
        unified_numeric_evidence_rows(decisions, evidence, terminal, performance, intrabar, REPO)
    )
    input_counts = {
        "unified_result_ok": unified_result.get("ok"),
        "performance_result_ok": performance_result.get("ok"),
        "intrabar_result_ok": intrabar_result.get("ok"),
        "unified_decision_rows": len(decisions),
        "unified_evidence_rows": len(evidence),
        "unified_terminal_rows": len(terminal),
        "performance_rows": len(performance),
        "intrabar_rows": len(intrabar),
    }
    system_rows = system_unified_numeric_evidence_rows(
        evidence_rows,
        terminal_rows,
        decision_rows,
        source_access_rows,
        aggregate_rows,
        issue_rows,
        input_counts,
    )
    decision_counts = Counter(row.get("keep_kill_redesign_implement_decision") for row in evidence_rows + terminal_rows + decision_rows)
    counts = {
        "input_unified_final_decision_rows": len(decisions),
        "input_unified_final_evidence_rows": len(evidence),
        "input_unified_terminal_redesign_rows": len(terminal),
        "input_performance_rows": len(performance),
        "input_intrabar_rows": len(intrabar),
        "unified_numeric_evidence_rows": len(evidence_rows),
        "unified_numeric_terminal_rows": len(terminal_rows),
        "unified_numeric_decision_rows": len(decision_rows),
        "source_access_proof_rows": len(source_access_rows),
        "source_access_confirmed_rows": sum(
            1 for row in source_access_rows if row.get("source_access_status") == "SOURCE_PATH_HASH_CONFIRMED"
        ),
        "aggregate_rows": len(aggregate_rows),
        "issue_rows": len(issue_rows),
        "system_rows": len(system_rows),
        "rows_with_simulated_r": sum(1 for row in evidence_rows + terminal_rows if not row.get("missing_simulated_fields")),
        "rows_without_simulated_r": sum(1 for row in evidence_rows + terminal_rows if row.get("missing_simulated_fields")),
        "decision_counts": dict(sorted(decision_counts.items())),
    }

    write_jsonl(EVIDENCE_LEDGER, evidence_rows)
    write_jsonl(TERMINAL_LEDGER, terminal_rows)
    write_jsonl(DECISION_LEDGER, decision_rows)
    write_jsonl(SOURCE_ACCESS_LEDGER, source_access_rows)
    write_jsonl(AGGREGATE_LEDGER, aggregate_rows)
    write_jsonl(ISSUE_LEDGER, issue_rows)
    write_jsonl(SYSTEM_LEDGER, system_rows)
    write_text(SUMMARY_PATH, build_summary(counts))

    outputs = [
        EVIDENCE_LEDGER,
        TERMINAL_LEDGER,
        DECISION_LEDGER,
        SOURCE_ACCESS_LEDGER,
        AGGREGATE_LEDGER,
        ISSUE_LEDGER,
        SYSTEM_LEDGER,
        SUMMARY_PATH,
    ]
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "ok": not issue_rows,
        "expanded_market_unified_numeric_evidence_surface": EXPANDED_MARKET_UNIFIED_NUMERIC_EVIDENCE_SURFACE,
        "inputs": {
            "unified_result": str(UNIFIED_RESULT.relative_to(REPO)).replace("\\", "/"),
            "unified_decision_ledger": str(UNIFIED_DECISION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "unified_evidence_ledger": str(UNIFIED_EVIDENCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "unified_terminal_ledger": str(UNIFIED_TERMINAL_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "performance_result": str(PERFORMANCE_RESULT.relative_to(REPO)).replace("\\", "/"),
            "performance_ledger": str(PERFORMANCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "intrabar_result": str(INTRABAR_RESULT.relative_to(REPO)).replace("\\", "/"),
            "intrabar_ledger": str(INTRABAR_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "evidence_ledger": str(EVIDENCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "terminal_ledger": str(TERMINAL_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "decision_ledger": str(DECISION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "source_access_ledger": str(SOURCE_ACCESS_LEDGER.relative_to(REPO)).replace("\\", "/"),
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
            "event": "expanded_market_unified_numeric_evidence",
            "checkpoint": 238,
            "generated_utc": generated_at,
            "counts": counts,
            "result": str(RESULT_PATH.relative_to(REPO)).replace("\\", "/"),
            "boundary": research_boundary(),
        }
    )
    replace_active_checkpoint(generated_at, counts)
    print(json.dumps({"ok": result["ok"], "counts": counts}, sort_keys=True))


if __name__ == "__main__":
    main()
