#!/usr/bin/env python3
"""Build row-level and aggregate simulated-R performance from executed specs."""

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

from src.research_infra.moonshot_repaired_proxy_runtime_replay_performance import (
    RUNTIME_REPLAY_PERFORMANCE_SURFACE,
    aggregate_performance_rows,
    missing_simulated_field_rows,
    performance_rows,
    research_boundary,
    system_performance_rows,
)


SPEC_EXEC_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_SPEC_EXECUTION"
NUMERIC_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_REPLAY_NUMERIC_EXECUTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_PERFORMANCE"

SPEC_EXEC_RESULT = ROUTE_DIR / f"{SPEC_EXEC_PREFIX}_RESULT_2026-05-17.json"
SCORER_EXECUTION_LEDGER = ROUTE_DIR / f"{SPEC_EXEC_PREFIX}_SCORER_EXECUTION_LEDGER_2026-05-17.jsonl"
COMPARATOR_EXECUTION_LEDGER = ROUTE_DIR / f"{SPEC_EXEC_PREFIX}_COMPARATOR_EXECUTION_LEDGER_2026-05-17.jsonl"
SPEC_EXEC_RESULT_LEDGER = ROUTE_DIR / f"{SPEC_EXEC_PREFIX}_RESULT_LEDGER_2026-05-17.jsonl"
REPLAY_NUMERIC_LEDGER = ROUTE_DIR / f"{NUMERIC_PREFIX}_REPLAY_NUMERIC_EVENT_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_runtime_replay_performance.py"
INPUT_HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_runtime_replay_spec_execution.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_repaired_proxy_runtime_replay_performance_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
ROW_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
MISSING_FIELD_LEDGER = ROUTE_DIR / f"{PREFIX}_MISSING_SIMULATED_FIELD_LEDGER_2026-05-17.jsonl"
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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(long_path(path), "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_by(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(field)) for row in rows).items()))


def manifest_entries() -> list[dict[str, str]]:
    entries = [
        (RESULT_PATH, "runtime_replay_performance_result"),
        (ROW_LEDGER, "runtime_replay_performance_row_ledger"),
        (AGGREGATE_LEDGER, "runtime_replay_performance_aggregate_ledger"),
        (MISSING_FIELD_LEDGER, "runtime_replay_performance_missing_field_ledger"),
        (SYSTEM_LEDGER, "runtime_replay_performance_system_ledger"),
        (SUMMARY_PATH, "runtime_replay_performance_summary"),
        (BUILDER_MODULE, "runtime_replay_performance_builder"),
        (VERIFIER_MODULE, "runtime_replay_performance_verifier"),
        (HELPER_MODULE, "runtime_replay_performance_helper"),
    ]
    return [
        {
            "path": str(path.relative_to(REPO)).replace("\\", "/"),
            "status": "created",
            "type": kind,
        }
        for path, kind in entries
    ]


def update_manifest(generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    entries = manifest_entries()
    manifest.setdefault("artifacts", []).extend(entries)
    manifest["latest_branch_local_repaired_proxy_runtime_replay_performance"] = {
        "generated_utc": generated_at,
        "files": entries,
        "result": str(RESULT_PATH.relative_to(REPO)).replace("\\", "/"),
    }
    manifest["last_updated_utc"] = generated_at
    write_json(OUTPUT_MANIFEST, manifest)


def append_sprint_event(generated_at: str, counts: dict[str, Any]) -> None:
    event = {
        "checkpoint": 203,
        "event": "runtime_replay_performance_tables",
        "generated_utc": generated_at,
        "row_level_performance_rows": counts["performance_rows"],
        "aggregate_performance_rows": counts["aggregate_rows"],
        "rows_with_proxy_r": counts["rows_with_proxy_r"],
        "rows_without_proxy_r": counts["rows_without_proxy_r"],
        "continuation": "inspect aggregate keep/kill/redesign/implement decisions and run concrete replay implementation only for rows still missing proxy-R or exact geometry.",
        "boundary": research_boundary(),
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")


def append_active_checkpoint(generated_at: str, counts: dict[str, Any]) -> None:
    marker = "\n## Checkpoint 203 - Runtime Replay Performance Tables\n"
    text = f"""{marker}
Generated: {generated_at}

Trigger: owner correction after Checkpoint 202. Executed scorer/comparator specs were converted directly into row-level and aggregate historical replay/simulated-R performance tables instead of another routing/spec layer.

Rows:
- row-level performance rows: {counts['performance_rows']}
- aggregate performance rows: {counts['aggregate_rows']}
- rows with proxy-R: {counts['rows_with_proxy_r']}
- rows without proxy-R: {counts['rows_without_proxy_r']}
- win/loss/flat/no-fill: {counts['win_rows']} / {counts['loss_rows']} / {counts['flat_rows']} / {counts['no_fill_rows']}
- aggregate decisions: {counts['aggregate_decision_counts']}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: inspect aggregate keep/kill/redesign/implement decisions and run concrete replay implementation only for rows still missing proxy-R or exact geometry.
"""
    with open(long_path(ACTIVE_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def build_summary(counts: dict[str, Any], aggregate_rows: list[dict[str, Any]]) -> str:
    top_decisions = count_by(aggregate_rows, "keep_kill_redesign_implement_decision")
    lines = [
        "# Runtime Replay Performance Tables",
        "",
        "Checkpoint 203 converts executed repaired-proxy scorer/comparator specs into row-level and aggregate historical replay/simulated-R performance rows.",
        "",
        "## Counts",
        "",
        f"- Row-level performance rows: `{counts['performance_rows']}`",
        f"- Aggregate performance rows: `{counts['aggregate_rows']}`",
        f"- Rows with proxy-R: `{counts['rows_with_proxy_r']}`",
        f"- Rows without proxy-R: `{counts['rows_without_proxy_r']}`",
        f"- Win/loss/flat/no-fill rows: `{counts['win_rows']}` / `{counts['loss_rows']}` / `{counts['flat_rows']}` / `{counts['no_fill_rows']}`",
        f"- Target-first/stop-first/neither/ambiguous rows: `{counts['target_first_rows']}` / `{counts['stop_first_rows']}` / `{counts['neither_rows']}` / `{counts['ambiguous_rows']}`",
        "",
        "## Aggregate Decisions",
        "",
    ]
    for decision, count in top_decisions.items():
        lines.append(f"- `{decision}`: `{count}`")
    lines.extend(
        [
            "",
            "## Geometry Boundary",
            "",
            "Exact trade side, timestamp, entry, stop, target, and target/stop ordering are not present in the executed-spec inputs. Rows therefore use replay proxy-R from source close return over the replay denominator, with exact missing fields retained on every row. Rows lacking a usable proxy denominator are emitted with a concrete missing-field disposition.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    generated_at = now_utc()
    spec_result = read_json(SPEC_EXEC_RESULT)
    scorer_rows = read_jsonl(SCORER_EXECUTION_LEDGER)
    comparator_rows = read_jsonl(COMPARATOR_EXECUTION_LEDGER)
    spec_result_rows = read_jsonl(SPEC_EXEC_RESULT_LEDGER)
    replay_numeric_rows = read_jsonl(REPLAY_NUMERIC_LEDGER)

    row_level = performance_rows(scorer_rows, comparator_rows, replay_numeric_rows)
    aggregate_rows = aggregate_performance_rows(row_level)
    missing_rows = missing_simulated_field_rows(row_level)
    system_rows = system_performance_rows(row_level, aggregate_rows, missing_rows)

    counts = {
        "input_spec_execution_result_ok": 1 if spec_result.get("ok") else 0,
        "input_spec_execution_result_rows": len(spec_result_rows),
        "input_scorer_execution_rows": len(scorer_rows),
        "input_comparator_execution_rows": len(comparator_rows),
        "input_replay_numeric_rows": len(replay_numeric_rows),
        "performance_rows": len(row_level),
        "aggregate_rows": len(aggregate_rows),
        "missing_simulated_field_rows": len(missing_rows),
        "system_rows": len(system_rows),
        "rows_with_proxy_r": sum(row.get("gross_simulated_r") is not None for row in row_level),
        "rows_without_proxy_r": sum(row.get("gross_simulated_r") is None for row in row_level),
        "win_rows": sum(int(row.get("win_count") or 0) for row in row_level),
        "loss_rows": sum(int(row.get("loss_count") or 0) for row in row_level),
        "flat_rows": sum(int(row.get("flat_count") or 0) for row in row_level),
        "no_fill_rows": sum(int(row.get("no_fill_count") or 0) for row in row_level),
        "target_first_rows": sum(int(row.get("target_first_count") or 0) for row in row_level),
        "stop_first_rows": sum(int(row.get("stop_first_count") or 0) for row in row_level),
        "neither_rows": sum(int(row.get("neither_count") or 0) for row in row_level),
        "ambiguous_rows": sum(int(row.get("ambiguous_count") or 0) for row in row_level),
        "row_disposition_counts": count_by(row_level, "row_disposition"),
        "aggregate_decision_counts": count_by(aggregate_rows, "keep_kill_redesign_implement_decision"),
    }

    result = {
        "artifact": PREFIX,
        "ok": True,
        "generated_utc": generated_at,
        "runtime_replay_performance_surface": RUNTIME_REPLAY_PERFORMANCE_SURFACE,
        "research_boundary": research_boundary(),
        "counts": counts,
        "inputs": {
            "spec_execution_result": str(SPEC_EXEC_RESULT.relative_to(REPO)).replace("\\", "/"),
            "scorer_execution_ledger": str(SCORER_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "comparator_execution_ledger": str(COMPARATOR_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "replay_numeric_ledger": str(REPLAY_NUMERIC_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "row_ledger": str(ROW_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "missing_field_ledger": str(MISSING_FIELD_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
    }

    write_jsonl(ROW_LEDGER, row_level)
    write_jsonl(AGGREGATE_LEDGER, aggregate_rows)
    write_jsonl(MISSING_FIELD_LEDGER, missing_rows)
    write_jsonl(SYSTEM_LEDGER, system_rows)
    write_json(RESULT_PATH, result)
    write_text(SUMMARY_PATH, build_summary(counts, aggregate_rows))
    update_manifest(generated_at)
    append_sprint_event(generated_at, counts)
    append_active_checkpoint(generated_at, counts)

    sha_payload = {
        "row_ledger_sha256": sha256_file(ROW_LEDGER),
        "aggregate_ledger_sha256": sha256_file(AGGREGATE_LEDGER),
        "system_ledger_sha256": sha256_file(SYSTEM_LEDGER),
    }
    result["output_sha256"] = sha_payload
    write_json(RESULT_PATH, result)
    print(json.dumps({"artifact": PREFIX, "counts": counts, "generated_utc": generated_at, "ok": True}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
