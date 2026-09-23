#!/usr/bin/env python3
"""Execute source-expansion action packs against candidate application rows."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_expanded_market_source_expansion_action_pack_execution import (
    EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_PACK_EXECUTION,
    aggregate_pack_execution_rows,
    boundary_row,
    pack_execution_row,
    pack_match_rows,
    research_boundary,
    work_execution_row,
)


APPLICATION_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_APPLICATION"
PACK_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_PACKS"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_PACK_EXECUTION"

APPLICATION_ROW_LEDGER = ROUTE_DIR / f"{APPLICATION_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
PACK_RESULT = ROUTE_DIR / f"{PACK_PREFIX}_RESULT_2026-05-17.json"
PACK_LEDGER = ROUTE_DIR / f"{PACK_PREFIX}_PACK_LEDGER_2026-05-17.jsonl"
WORK_LEDGER = ROUTE_DIR / f"{PACK_PREFIX}_WORK_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_expanded_market_source_expansion_action_pack_execution.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_expanded_market_source_expansion_action_pack_execution_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_EXECUTION_LEDGER_2026-05-17.jsonl"
MATCH_LEDGER = ROUTE_DIR / f"{PREFIX}_MATCH_LEDGER_2026-05-17.jsonl"
WORK_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_WORK_EXECUTION_LEDGER_2026-05-17.jsonl"
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


def manifest_entries() -> list[dict[str, str]]:
    entries = [
        (RESULT_PATH, "expanded_market_source_expansion_action_pack_execution_result"),
        (EXECUTION_LEDGER, "expanded_market_source_expansion_action_pack_execution_rows"),
        (MATCH_LEDGER, "expanded_market_source_expansion_action_pack_execution_matches"),
        (WORK_EXECUTION_LEDGER, "expanded_market_source_expansion_action_pack_work_execution_rows"),
        (AGGREGATE_LEDGER, "expanded_market_source_expansion_action_pack_execution_aggregates"),
        (ISSUE_LEDGER, "expanded_market_source_expansion_action_pack_execution_issues"),
        (SYSTEM_LEDGER, "expanded_market_source_expansion_action_pack_execution_system"),
        (SUMMARY_PATH, "expanded_market_source_expansion_action_pack_execution_summary"),
        (BUILDER_MODULE, "expanded_market_source_expansion_action_pack_execution_builder"),
        (VERIFIER_MODULE, "expanded_market_source_expansion_action_pack_execution_verifier"),
        (HELPER_MODULE, "expanded_market_source_expansion_action_pack_execution_helper"),
        (TEST_MODULE, "expanded_market_source_expansion_action_pack_execution_tests"),
    ]
    return [
        {"path": str(path.relative_to(REPO)).replace("\\", "/"), "status": "created", "type": kind}
        for path, kind in entries
    ]


def update_manifest(generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    entries = manifest_entries()
    types = {entry["type"] for entry in entries}
    existing = manifest.setdefault("artifacts", [])
    manifest["artifacts"] = [row for row in existing if row.get("type") not in types] + entries
    manifest["latest_expanded_market_source_expansion_action_pack_execution"] = {
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
    marker = "## Checkpoint 271 - Expanded-Market Source Expansion Action Pack Execution"
    text = ACTIVE_LEDGER.read_text(encoding="utf-8", errors="replace") if ACTIVE_LEDGER.exists() else ""
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n\n"
    addition = f"""{marker}

Generated: {generated_at}

Trigger: direct continuation after Checkpoint 270. Action packs were executed against every CP269 application candidate row with negative mismatch scans, while replay/source work rows were preserved.

Rows:
- candidate application rows scanned per pack: {counts["candidate_application_rows"]}
- action pack execution rows: {counts["action_pack_execution_rows"]}
- action pack match rows: {counts["match_rows"]}
- work execution rows: {counts["work_execution_rows"]}
- aggregate rows: {counts["aggregate_rows"]}
- issue rows: {counts["issue_rows"]}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: promote passing pack-execution evidence into branch-local research bundle rows and keep work-execution rows as concrete replay/source tasks.
"""
    write_text(ACTIVE_LEDGER, text.rstrip() + "\n\n" + addition)


def build_summary(generated_at: str, counts: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Expanded-Market Source Expansion Action Pack Execution",
            "",
            f"Generated: {generated_at}",
            "",
            "This checkpoint executes CP270 action packs against the full CP269 application candidate set and preserves replay/source work rows.",
            "",
            "## Counts",
            "",
            f"- Candidate application rows scanned per pack: `{counts['candidate_application_rows']}`",
            f"- Action pack execution rows: `{counts['action_pack_execution_rows']}`",
            f"- Action pack match rows: `{counts['match_rows']}`",
            f"- Work execution rows: `{counts['work_execution_rows']}`",
            f"- Aggregate rows: `{counts['aggregate_rows']}`",
            f"- Issue rows: `{counts['issue_rows']}`",
            "",
        ]
    )


def main() -> None:
    generated_at = now_utc()
    pack_result = read_json(PACK_RESULT)
    application_rows = list(iter_jsonl(APPLICATION_ROW_LEDGER))
    application_by_id = {
        str(row.get("expanded_market_source_expansion_action_application_row_id") or ""): row
        for row in application_rows
    }
    pack_rows = list(iter_jsonl(PACK_LEDGER))
    work_rows = list(iter_jsonl(WORK_LEDGER))
    execution_rows: list[dict[str, Any]] = []
    match_rows: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []

    for pack in pack_rows:
        execution = pack_execution_row(pack, application_rows, len(execution_rows) + 1)
        execution_rows.append(execution)
        new_matches = pack_match_rows(pack, execution, application_by_id, len(match_rows) + 1)
        match_rows.extend(new_matches)
        if execution.get("action_pack_execution_status") != "ACTION_PACK_EXECUTION_PASS":
            issues.append(
                boundary_row(
                    {
                        "expanded_market_source_expansion_action_pack_execution_issue_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-ACTION-PACK-EXEC-ISSUE-{len(issues) + 1:07d}"
                        ),
                        "issue_type": "ACTION_PACK_EXECUTION_REPAIR_REQUIRED",
                        "input_action_pack_row_id": pack.get(
                            "expanded_market_source_expansion_action_pack_row_id"
                        ),
                        "match_count": execution.get("match_count"),
                        "decision_leak_count": execution.get("decision_leak_count"),
                        "class_leak_count": execution.get("class_leak_count"),
                        "cost_mismatch_count": execution.get("cost_mismatch_count"),
                    }
                )
            )

    work_execution_rows = [
        work_execution_row(row, index + 1) for index, row in enumerate(work_rows)
    ]
    aggregates = aggregate_pack_execution_rows(execution_rows, work_execution_rows)
    status_counts = Counter(row.get("action_pack_execution_status") for row in execution_rows)
    work_status_counts = Counter(row.get("work_status") for row in work_execution_rows)
    counts = {
        "input_pack_result_ok": pack_result.get("ok"),
        "candidate_application_rows": len(application_rows),
        "input_action_pack_rows": len(pack_rows),
        "input_work_rows": len(work_rows),
        "action_pack_execution_rows": len(execution_rows),
        "action_pack_execution_pass_rows": status_counts.get("ACTION_PACK_EXECUTION_PASS", 0),
        "match_rows": len(match_rows),
        "work_execution_rows": len(work_execution_rows),
        "work_rows_with_simulated_r": sum(
            row.get("cost_adjusted_simulated_r") is not None for row in work_execution_rows
        ),
        "aggregate_rows": len(aggregates),
        "issue_rows": len(issues),
        "system_rows": 1,
        "total_negative_mismatch_scans": sum(
            int(row.get("negative_mismatch_count") or 0) for row in execution_rows
        ),
        "execution_status_counts": dict(sorted(status_counts.items())),
        "work_status_counts": dict(sorted(work_status_counts.items())),
    }
    system_rows = [
        boundary_row(
            {
                "expanded_market_source_expansion_action_pack_execution_system_row_id": (
                    "OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-ACTION-PACK-EXEC-SYSTEM-0001"
                ),
                **counts,
                "metadata": {
                    "application_row_ledger": str(APPLICATION_ROW_LEDGER.relative_to(REPO)).replace("\\", "/"),
                    "pack_ledger": str(PACK_LEDGER.relative_to(REPO)).replace("\\", "/"),
                    "work_ledger": str(WORK_LEDGER.relative_to(REPO)).replace("\\", "/"),
                    "no_top_n_cutoff": True,
                },
            }
        )
    ]
    output_files = [
        EXECUTION_LEDGER,
        MATCH_LEDGER,
        WORK_EXECUTION_LEDGER,
        AGGREGATE_LEDGER,
        ISSUE_LEDGER,
        SYSTEM_LEDGER,
        SUMMARY_PATH,
    ]
    write_jsonl(EXECUTION_LEDGER, execution_rows)
    write_jsonl(MATCH_LEDGER, match_rows)
    write_jsonl(WORK_EXECUTION_LEDGER, work_execution_rows)
    write_jsonl(AGGREGATE_LEDGER, aggregates)
    write_jsonl(ISSUE_LEDGER, issues)
    write_jsonl(SYSTEM_LEDGER, system_rows)
    write_text(SUMMARY_PATH, build_summary(generated_at, counts))
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "ok": not issues,
        "issues": issues,
        "counts": counts,
        "inputs": {
            "pack_result": str(PACK_RESULT.relative_to(REPO)).replace("\\", "/"),
            "pack_ledger": str(PACK_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "work_ledger": str(WORK_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "application_row_ledger": str(APPLICATION_ROW_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "execution_ledger": str(EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "match_ledger": str(MATCH_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "work_execution_ledger": str(WORK_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "issue_ledger": str(ISSUE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
        "output_sha256": output_sha256(output_files),
        "expanded_market_source_expansion_action_pack_execution_surface": (
            EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_PACK_EXECUTION
        ),
        "research_boundary": research_boundary(),
    }
    write_json(RESULT_PATH, result)
    update_manifest(generated_at)
    replace_sprint_event(
        {
            "checkpoint": 271,
            "event": "checkpoint_271_expanded_market_source_expansion_action_pack_execution",
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
