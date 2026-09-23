#!/usr/bin/env python3
"""Build the final CP282 frozen-universe main handoff packet."""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_frozen_universe_main_handoff import (
    FROZEN_UNIVERSE_MAIN_HANDOFF_SURFACE,
    boundary_row,
    consumption_order_rows,
    count_check_row,
    research_boundary,
)


CP280_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_FROZEN_UNIVERSE_IMPLEMENTATION_CLOSURE"
CP281_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_FROZEN_UNIVERSE_READY_ACTION_RUNTIME"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_FROZEN_UNIVERSE_MAIN_HANDOFF"
DATE = "2026-05-17"

CP280_RESULT = ROUTE_DIR / f"{CP280_PREFIX}_RESULT_{DATE}.json"
CP280_MAIN_HANDOFF = ROUTE_DIR / f"{CP280_PREFIX}_MAIN_HANDOFF_BUNDLE_LEDGER_{DATE}.jsonl"
CP281_RESULT = ROUTE_DIR / f"{CP281_PREFIX}_RESULT_{DATE}.json"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_{DATE}.json"
ARTIFACT_LEDGER = ROUTE_DIR / f"{PREFIX}_ARTIFACT_LEDGER_{DATE}.jsonl"
COUNT_CHECK_LEDGER = ROUTE_DIR / f"{PREFIX}_COUNT_CHECK_LEDGER_{DATE}.jsonl"
CONSUMPTION_ORDER_LEDGER = ROUTE_DIR / f"{PREFIX}_CONSUMPTION_ORDER_LEDGER_{DATE}.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_ISSUE_LEDGER_{DATE}.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_{DATE}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_{DATE}.md"
VERIFIER_RESULT = ROUTE_DIR / f"{PREFIX}_VERIFIER_RESULT_{DATE}.json"

OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"
ACTIVE_LEDGER = ROUTE_DIR / "ABSOLUTE_NORTH_STAR_ACTIVE_DOCTRINE_LEDGER_2026-05-15.md"
HELPER_MODULE = REPO / "src/research_infra/moonshot_frozen_universe_main_handoff.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_frozen_universe_main_handoff_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def long_path(path: Path) -> str:
    text = str(path)
    if len(text) >= 240 and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def rel(path: Path) -> str:
    return str(path.relative_to(REPO)).replace("\\", "/")


def read_json(path: Path) -> dict[str, Any]:
    with open(long_path(path), "r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with open(long_path(path), "r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line.lstrip("\ufeff"))


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


def file_sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with open(long_path(path), "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def jsonl_count(path: Path) -> int:
    return sum(1 for _ in iter_jsonl(path))


def text_line_count(path: Path) -> int:
    with open(long_path(path), "r", encoding="utf-8", errors="replace") as handle:
        return sum(1 for _ in handle)


def row_count(path: Path) -> tuple[int, str]:
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        return jsonl_count(path), "jsonl_rows"
    if suffix == ".json":
        return 1, "json_document"
    return text_line_count(path), "text_lines"


def manifest_entries_for(prefix_key: str) -> list[dict[str, str]]:
    manifest = read_json(OUTPUT_MANIFEST)
    entry = manifest.get(prefix_key) or {}
    return list(entry.get("files") or [])


def artifact_rows(entries: list[dict[str, str]], checkpoint: int, sequence_start: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for offset, entry in enumerate(entries):
        path = REPO / str(entry["path"])
        count, basis = row_count(path)
        rows.append(
            boundary_row(
                {
                    "frozen_main_handoff_artifact_row_id": (
                        f"FROZEN-MOONSHOT-MAIN-HANDOFF-ARTIFACT-{sequence_start + offset:04d}"
                    ),
                    "checkpoint": checkpoint,
                    "artifact_path": entry["path"],
                    "artifact_role": entry.get("type"),
                    "artifact_status": entry.get("status"),
                    "artifact_sha256": file_sha256(path),
                    "artifact_byte_count": Path(long_path(path)).stat().st_size,
                    "row_count": count,
                    "row_count_basis": basis,
                }
            )
        )
    return rows


def output_sha256(paths: list[Path]) -> dict[str, str]:
    return {path.name: file_sha256(path) for path in paths}


def manifest_entries() -> list[dict[str, str]]:
    entries = [
        (RESULT_PATH, "frozen_universe_main_handoff_result"),
        (ARTIFACT_LEDGER, "frozen_universe_main_handoff_artifacts"),
        (COUNT_CHECK_LEDGER, "frozen_universe_main_handoff_count_checks"),
        (CONSUMPTION_ORDER_LEDGER, "frozen_universe_main_handoff_consumption_order"),
        (ISSUE_LEDGER, "frozen_universe_main_handoff_issues"),
        (SYSTEM_LEDGER, "frozen_universe_main_handoff_system"),
        (SUMMARY_PATH, "frozen_universe_main_handoff_summary"),
        (VERIFIER_RESULT, "frozen_universe_main_handoff_verifier_result"),
        (BUILDER_MODULE, "frozen_universe_main_handoff_builder"),
        (VERIFIER_MODULE, "frozen_universe_main_handoff_verifier"),
        (HELPER_MODULE, "frozen_universe_main_handoff_helper"),
        (TEST_MODULE, "frozen_universe_main_handoff_tests"),
    ]
    return [{"path": rel(path), "status": "created", "type": role} for path, role in entries]


def update_manifest(generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    entries = manifest_entries()
    types = {entry["type"] for entry in entries}
    manifest["artifacts"] = [
        row for row in manifest.setdefault("artifacts", []) if row.get("type") not in types
    ] + entries
    manifest["latest_frozen_universe_main_handoff"] = {
        "generated_utc": generated_at,
        "result": rel(RESULT_PATH),
        "files": entries,
    }
    manifest["last_updated_utc"] = generated_at
    write_json(OUTPUT_MANIFEST, manifest)


def replace_sprint_event(event: dict[str, Any]) -> None:
    kept: list[str] = []
    if SPRINT_LEDGER.exists():
        with open(long_path(SPRINT_LEDGER), "r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if not line.strip():
                    continue
                row = json.loads(line.lstrip("\ufeff"))
                if row.get("event") == event.get("event"):
                    continue
                kept.append(json.dumps(row, sort_keys=True))
    kept.append(json.dumps(event, sort_keys=True))
    write_text(SPRINT_LEDGER, "\n".join(kept) + "\n")


def replace_active_checkpoint(generated_at: str, counts: dict[str, Any]) -> None:
    marker = "## Checkpoint 282 - Frozen-Universe Main Handoff"
    text = ACTIVE_LEDGER.read_text(encoding="utf-8", errors="replace") if ACTIVE_LEDGER.exists() else ""
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n\n"
    addition = f"""{marker}

Generated: {generated_at}

CP280 is the frozen universe map. CP281 is the executable ready-slice materialization. CP282 ties both together for direct main consumption and preserves repair, kill/preserve, and coverage maps for main-prioritized implementation.

Rows:
- CP280 artifacts recorded: {counts["cp280_artifact_rows"]}
- CP281 artifacts recorded: {counts["cp281_artifact_rows"]}
- implementation-ready rows consumed by CP281: {counts["implementation_ready_rows_consumed"]}
- follow-rule scorer inputs: {counts["follow_rule_inputs"]}
- avoid-filter inputs: {counts["avoid_filter_inputs"]}
- aggregate scopes: {counts["aggregate_scopes"]}
- represented source rows: {counts["represented_source_rows"]}
- repair-needed rows preserved: {counts["repair_needed_rows_preserved"]}
- kill/preserve rows preserved: {counts["kill_preserve_rows_preserved"]}
- coverage rows preserved: {counts["coverage_rows_preserved"]}
- main handoff rows preserved: {counts["main_handoff_rows"]}
- issue rows: {counts["issue_rows"]}

Main consumption order:
1. ready runtime rules
2. rule-performance evidence
3. action/execution proof
4. repair-needed bundle
5. full frozen closure
"""
    write_text(ACTIVE_LEDGER, text.rstrip() + "\n\n" + addition)


def main() -> None:
    generated_at = now_utc()
    cp280_result = read_json(CP280_RESULT)
    cp281_result = read_json(CP281_RESULT)
    cp280_counts = cp280_result.get("counts") or {}
    cp281_counts = cp281_result.get("counts") or {}
    cp280_entries = manifest_entries_for("latest_frozen_universe_implementation_closure")
    cp281_entries = manifest_entries_for("latest_frozen_universe_ready_action_runtime")
    cp280_artifacts = artifact_rows(cp280_entries, 280, 1)
    cp281_artifacts = artifact_rows(cp281_entries, 281, 1 + len(cp280_artifacts))
    artifact_rows_out = cp280_artifacts + cp281_artifacts
    cp280_handoff_rows = list(iter_jsonl(CP280_MAIN_HANDOFF))
    cp281_artifact_paths = [entry["path"] for entry in cp281_entries]
    order_rows = consumption_order_rows(cp280_handoff_rows, cp281_artifact_paths)

    checks = [
        ("cp280_result_ok", cp280_result.get("ok"), True, rel(CP280_RESULT)),
        ("cp281_result_ok", cp281_result.get("ok"), True, rel(CP281_RESULT)),
        ("implementation_ready_rows_consumed", cp281_counts.get("input_ready_rows"), 461, rel(CP281_RESULT)),
        ("follow_rule_inputs", (cp281_counts.get("action_class_counts") or {}).get("follow_rule"), 173, rel(CP281_RESULT)),
        ("avoid_filter_inputs", (cp281_counts.get("action_class_counts") or {}).get("avoid_filter"), 288, rel(CP281_RESULT)),
        ("aggregate_scopes", cp281_counts.get("aggregate_rows"), 107, rel(CP281_RESULT)),
        ("represented_source_rows", cp281_counts.get("source_rows_represented"), 6428, rel(CP281_RESULT)),
        ("repair_needed_rows_preserved", cp280_counts.get("repair_needed_rows"), 243649, rel(CP280_RESULT)),
        ("kill_preserve_rows_preserved", cp280_counts.get("kill_preserve_rows"), 25811, rel(CP280_RESULT)),
        ("coverage_rows_preserved", cp280_counts.get("coverage_rows"), 28474, rel(CP280_RESULT)),
        ("main_handoff_rows", len(cp280_handoff_rows), 5, rel(CP280_MAIN_HANDOFF)),
        ("consumption_order_rows", len(order_rows), 5, rel(CONSUMPTION_ORDER_LEDGER)),
    ]
    check_rows = [
        count_check_row(name, observed, expected, evidence, index)
        for index, (name, observed, expected, evidence) in enumerate(checks, start=1)
    ]
    issues = [
        boundary_row(
            {
                "frozen_main_handoff_issue_row_id": (
                    f"FROZEN-MOONSHOT-MAIN-HANDOFF-ISSUE-{index:03d}"
                ),
                "check_name": row.get("check_name"),
                "observed": row.get("observed"),
                "expected": row.get("expected"),
                "issue": "count_check_failed",
            }
        )
        for index, row in enumerate(check_rows, start=1)
        if row.get("check_pass") is not True
    ]
    counts = {
        "cp280_artifact_rows": len(cp280_artifacts),
        "cp281_artifact_rows": len(cp281_artifacts),
        "artifact_rows": len(artifact_rows_out),
        "count_check_rows": len(check_rows),
        "consumption_order_rows": len(order_rows),
        "implementation_ready_rows_consumed": cp281_counts.get("input_ready_rows"),
        "follow_rule_inputs": (cp281_counts.get("action_class_counts") or {}).get("follow_rule"),
        "avoid_filter_inputs": (cp281_counts.get("action_class_counts") or {}).get("avoid_filter"),
        "aggregate_scopes": cp281_counts.get("aggregate_rows"),
        "represented_source_rows": cp281_counts.get("source_rows_represented"),
        "repair_needed_rows_preserved": cp280_counts.get("repair_needed_rows"),
        "kill_preserve_rows_preserved": cp280_counts.get("kill_preserve_rows"),
        "coverage_rows_preserved": cp280_counts.get("coverage_rows"),
        "main_handoff_rows": len(cp280_handoff_rows),
        "issue_rows": len(issues),
    }
    system = boundary_row(
        {
            "system_row_id": "FROZEN-MOONSHOT-MAIN-HANDOFF-SYSTEM-0000001",
            "generated_utc": generated_at,
            "cp280_result": rel(CP280_RESULT),
            "cp281_result": rel(CP281_RESULT),
            "builder": rel(BUILDER_MODULE),
            "helper": FROZEN_UNIVERSE_MAIN_HANDOFF_SURFACE,
            "counts": counts,
            "boundary": research_boundary(),
        }
    )
    write_jsonl(ARTIFACT_LEDGER, artifact_rows_out)
    write_jsonl(COUNT_CHECK_LEDGER, check_rows)
    write_jsonl(CONSUMPTION_ORDER_LEDGER, order_rows)
    write_jsonl(ISSUE_LEDGER, issues)
    write_jsonl(SYSTEM_LEDGER, [system])
    outputs = [ARTIFACT_LEDGER, COUNT_CHECK_LEDGER, CONSUMPTION_ORDER_LEDGER, ISSUE_LEDGER, SYSTEM_LEDGER]
    result = boundary_row(
        {
            "ok": not issues,
            "generated_utc": generated_at,
            "cp280_role": "universe_freeze",
            "cp281_role": "executable_ready_slice_materialization",
            "terminal_state": (
                "moonshot current universe closed; ready slice materialized; repair, coverage, and kill/preserve maps preserved for main"
            ),
            "counts": counts,
            "output_sha256": output_sha256(outputs),
        }
    )
    write_json(RESULT_PATH, result)
    write_text(
        SUMMARY_PATH,
        f"""# Frozen Universe Main Handoff

Generated: {generated_at}

CP280 is the universe freeze. CP281 is the executable ready-slice materialization. CP282 is the exact handoff packet for main.

## Counts
- CP280 artifacts recorded: {counts["cp280_artifact_rows"]}
- CP281 artifacts recorded: {counts["cp281_artifact_rows"]}
- Implementation-ready rows consumed: {counts["implementation_ready_rows_consumed"]}
- Follow-rule scorer inputs: {counts["follow_rule_inputs"]}
- Avoid-filter inputs: {counts["avoid_filter_inputs"]}
- Aggregate scopes: {counts["aggregate_scopes"]}
- Represented source rows: {counts["represented_source_rows"]}
- Repair-needed rows preserved: {counts["repair_needed_rows_preserved"]}
- Kill/preserve rows preserved: {counts["kill_preserve_rows_preserved"]}
- Coverage rows preserved: {counts["coverage_rows_preserved"]}
- Main handoff rows: {counts["main_handoff_rows"]}

## Main Consumption Order
1. Ready runtime rules
2. Rule-performance evidence
3. Action/execution proof
4. Repair-needed bundle
5. Full frozen closure
""",
    )
    update_manifest(generated_at)
    replace_sprint_event(
        {
            "event": "checkpoint_282_frozen_universe_main_handoff",
            "checkpoint": 282,
            "generated_utc": generated_at,
            "result": rel(RESULT_PATH),
            "counts": counts,
            "boundary": research_boundary(),
        }
    )
    replace_active_checkpoint(generated_at, counts)
    print(json.dumps({"ok": result["ok"], "counts": counts}, sort_keys=True))


if __name__ == "__main__":
    main()
