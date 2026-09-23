#!/usr/bin/env python3
"""Build supplemental expanded-market proxy-R performance from local source-bound bars."""

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

from src.research_infra.moonshot_expanded_market_supplemental_source_performance import (
    EXPANDED_MARKET_SUPPLEMENTAL_SOURCE_PERFORMANCE_SURFACE,
    aggregate_supplemental_performance_rows,
    copy_seed_floor_performance_rows,
    missing_simulated_field_rows,
    research_boundary,
    source_bound_m15_rows,
    supplemental_performance_rows,
    system_supplemental_performance_rows,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_PROXY_R_PERFORMANCE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SUPPLEMENTAL_SOURCE_PERFORMANCE"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
INPUT_PERFORMANCE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
COST_SYMBOL_LEDGER = (
    ROUTE_DIR
    / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_EXECUTION_SPECS_COST_SYMBOL_LEDGER_2026-05-17.jsonl"
)
SIERRA_SOURCE_BOUND_BAR_LEDGER = ROUTE_DIR / "SIERRA_SCID_M15_SOURCE_BOUND_BAR_LEDGER_2026-05-16.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_expanded_market_supplemental_source_performance.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_expanded_market_supplemental_source_performance_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
PERFORMANCE_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
SOURCE_LEDGER = ROUTE_DIR / f"{PREFIX}_ADDITIONAL_SOURCE_LEDGER_2026-05-17.jsonl"
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


def output_sha256(paths: list[Path]) -> dict[str, str]:
    digest: dict[str, str] = {}
    for path in paths:
        hasher = hashlib.sha256()
        with open(long_path(path), "rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                hasher.update(chunk)
        digest[path.name] = hasher.hexdigest()
    return digest


def cost_index(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("symbol")).upper(): row for row in rows if row.get("symbol")}


def update_manifest(generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    entries = [
        (RESULT_PATH, "expanded_market_supplemental_source_performance_result"),
        (PERFORMANCE_LEDGER, "expanded_market_supplemental_source_performance_rows"),
        (SOURCE_LEDGER, "expanded_market_supplemental_source_access"),
        (AGGREGATE_LEDGER, "expanded_market_supplemental_source_performance_aggregates"),
        (MISSING_FIELD_LEDGER, "expanded_market_supplemental_source_missing_simulated_fields"),
        (SYSTEM_LEDGER, "expanded_market_supplemental_source_performance_system"),
        (SUMMARY_PATH, "expanded_market_supplemental_source_performance_summary"),
        (BUILDER_MODULE, "expanded_market_supplemental_source_performance_builder"),
        (VERIFIER_MODULE, "expanded_market_supplemental_source_performance_verifier"),
        (HELPER_MODULE, "expanded_market_supplemental_source_performance_helper"),
        (TEST_MODULE, "expanded_market_supplemental_source_performance_tests"),
    ]
    rows = [
        {"path": str(path.relative_to(REPO)).replace("\\", "/"), "status": "created", "type": kind}
        for path, kind in entries
    ]
    existing = manifest.setdefault("artifacts", [])
    keys = {(row["path"], row["type"]) for row in rows}
    manifest["artifacts"] = [row for row in existing if (row.get("path"), row.get("type")) not in keys] + rows
    manifest["latest_expanded_market_supplemental_source_performance"] = {
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
    marker = "## Checkpoint 246 - Expanded-Market Supplemental Source Performance"
    text = ACTIVE_LEDGER.read_text(encoding="utf-8", errors="replace") if ACTIVE_LEDGER.exists() else ""
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n\n"
    addition = f"""{marker}

Generated: {generated_at}

Trigger: correction after Checkpoint 245. The next checkpoint pivots back to numeric expanded-market performance by preserving CP216 seed-floor replay rows and adding every reachable Sierra source-bound M15 bar symbol discovered in the local bar substrate.

Rows:
- input CP216 seed-floor performance rows: {counts["input_seed_floor_performance_rows"]}
- additional source rows: {counts["additional_source_rows"]}
- additional source performance rows: {counts["additional_source_performance_rows"]}
- combined performance rows: {counts["combined_performance_rows"]}
- aggregate rows: {counts["aggregate_rows"]}
- missing simulated-field rows: {counts["missing_simulated_field_rows"]}
- rows with simulated R: {counts["rows_with_simulated_r"]}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: continue with the next highest-value numeric robustness or implementation plate over the combined expanded-market performance rows; do not resume wrapper-only final-decision work.
"""
    write_text(ACTIVE_LEDGER, text.rstrip() + "\n\n" + addition)


def build_summary(generated_at: str, counts: dict[str, Any], result: dict[str, Any]) -> str:
    decision_counts = counts.get("decision_counts") or {}
    decision_lines = "\n".join(f"- {key}: {value}" for key, value in sorted(decision_counts.items()))
    return f"""# Expanded-Market Supplemental Source Performance

Generated: {generated_at}

## Inputs

- CP216 seed-floor performance rows: `{counts["input_seed_floor_performance_rows"]}`
- Sierra source-bound M15 source rows: `{counts["additional_source_rows"]}`

## Outputs

- Combined performance rows: `{counts["combined_performance_rows"]}`
- Additional source performance rows: `{counts["additional_source_performance_rows"]}`
- Aggregate rows: `{counts["aggregate_rows"]}`
- Missing simulated-field rows: `{counts["missing_simulated_field_rows"]}`
- Rows with simulated R: `{counts["rows_with_simulated_r"]}`

## Decisions

{decision_lines}

## Boundary

Branch-local research artifact only. The run wrote no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path.

## Result

- ok: `{result["ok"]}`
- issues: `{result["issues"]}`
"""


def main() -> None:
    generated_at = now_utc()
    input_result = read_json(INPUT_RESULT)
    seed_floor_input = read_jsonl(INPUT_PERFORMANCE_LEDGER)
    cost_rows = read_jsonl(COST_SYMBOL_LEDGER)
    source_rows, grouped_bars = source_bound_m15_rows(
        REPO,
        str(SIERRA_SOURCE_BOUND_BAR_LEDGER.relative_to(REPO)).replace("\\", "/"),
    )
    seed_floor_rows = copy_seed_floor_performance_rows(seed_floor_input)
    additional_rows = supplemental_performance_rows(
        source_rows,
        grouped_bars,
        cost_index(cost_rows),
        sequence_start=len(seed_floor_rows) + 1,
    )
    performance_rows = seed_floor_rows + additional_rows
    aggregate_rows = aggregate_supplemental_performance_rows(performance_rows)
    missing_rows = missing_simulated_field_rows(performance_rows)
    metadata = {
        "input_cp216_ok": input_result.get("ok"),
        "input_cp216_performance_rows": len(seed_floor_input),
        "sierra_source_bound_bar_ledger": str(SIERRA_SOURCE_BOUND_BAR_LEDGER.relative_to(REPO)).replace("\\", "/"),
    }
    system_rows = system_supplemental_performance_rows(
        performance_rows,
        aggregate_rows,
        source_rows,
        missing_rows,
        metadata,
    )
    counts = {
        "input_seed_floor_performance_rows": len(seed_floor_input),
        "additional_source_rows": len(source_rows),
        "additional_source_performance_rows": len(additional_rows),
        "combined_performance_rows": len(performance_rows),
        "aggregate_rows": len(aggregate_rows),
        "missing_simulated_field_rows": len(missing_rows),
        "rows_with_simulated_r": len(performance_rows) - len(missing_rows),
        "source_path_count": len({row.get("source_path") for row in performance_rows}),
        "symbol_count": len({row.get("symbol") for row in performance_rows}),
        "timeframe_count": len({row.get("market_timeframe") for row in performance_rows}),
        "decision_counts": dict(
            sorted(Counter(row.get("keep_kill_redesign_implement_decision") for row in performance_rows).items())
        ),
        "system_rows": len(system_rows),
    }
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "ok": True,
        "issues": [],
        "expanded_market_supplemental_source_performance_surface": (
            EXPANDED_MARKET_SUPPLEMENTAL_SOURCE_PERFORMANCE_SURFACE
        ),
        "research_boundary": research_boundary(),
        "inputs": {
            "cp216_result": str(INPUT_RESULT.relative_to(REPO)).replace("\\", "/"),
            "cp216_performance_ledger": str(INPUT_PERFORMANCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "cost_symbol_ledger": str(COST_SYMBOL_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "sierra_source_bound_bar_ledger": str(SIERRA_SOURCE_BOUND_BAR_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "performance_ledger": str(PERFORMANCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "additional_source_ledger": str(SOURCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "missing_simulated_field_ledger": str(MISSING_FIELD_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
        "counts": counts,
    }

    write_jsonl(PERFORMANCE_LEDGER, performance_rows)
    write_jsonl(SOURCE_LEDGER, source_rows)
    write_jsonl(AGGREGATE_LEDGER, aggregate_rows)
    write_jsonl(MISSING_FIELD_LEDGER, missing_rows)
    write_jsonl(SYSTEM_LEDGER, system_rows)
    write_text(SUMMARY_PATH, build_summary(generated_at, counts, result))
    result["output_sha256"] = output_sha256(
        [PERFORMANCE_LEDGER, SOURCE_LEDGER, AGGREGATE_LEDGER, MISSING_FIELD_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]
    )
    write_json(RESULT_PATH, result)
    update_manifest(generated_at)
    replace_sprint_event(
        {
            "event": "expanded_market_supplemental_source_performance",
            "checkpoint": 246,
            "generated_utc": generated_at,
            "result": str(RESULT_PATH.relative_to(REPO)).replace("\\", "/"),
            "counts": counts,
            "boundary": research_boundary(),
        }
    )
    replace_active_checkpoint(generated_at, counts)
    print(json.dumps({"ok": True, "counts": counts}, sort_keys=True))


if __name__ == "__main__":
    main()
