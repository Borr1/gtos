#!/usr/bin/env python3
"""Deterministically reconcile the additive live-flow blocks in the runtime packet ledger."""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.components.ultimate_book.live_flow import reconcile_live_flow_rows
from src.components.ultimate_book.runtime_learning_packet import DEFAULT_LOG_PATH


def load_rows(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    parse_issues: list[dict[str, Any]] = []
    legacy_rows = 0
    total_lines = 0
    legacy_generation_cycles: dict[tuple[str, str], tuple[int | None, int | None]] = {}
    legacy_generation_conflicts: list[dict[str, Any]] = []
    legacy_empty_cycles = 0
    legacy_empty_cycles_missing_bar = 0
    if not path.exists():
        return [], {
            "status": "FAIL",
            "path": str(path),
            "lines_total": 0,
            "legacy_rows_without_live_flow": 0,
            "parse_issues": [{"issue": "ledger_path_missing"}],
        }
    opener = gzip.open if path.suffix.lower() == ".gz" else Path.open
    with opener(path, "rt", encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, start=1):
            if not raw.strip():
                continue
            total_lines += 1
            try:
                row = json.loads(raw)
            except json.JSONDecodeError as exc:
                parse_issues.append({
                    "line": line_no,
                    "issue": "invalid_json",
                    "message": str(exc),
                })
                continue
            if not isinstance(row, dict):
                parse_issues.append({"line": line_no, "issue": "row_not_object"})
                continue
            if "live_flow" not in row:
                legacy_rows += 1
                event_type = str(row.get("event_type") or "unknown")
                if event_type == "cycle_no_candidates":
                    legacy_empty_cycles += 1
                    if row.get("decision_bar_iso") in (None, ""):
                        legacy_empty_cycles_missing_bar += 1
                bridge = row.get("bridge") if isinstance(row.get("bridge"), dict) else {}
                generation = (
                    bridge.get("broker_profile_generation")
                    if isinstance(bridge.get("broker_profile_generation"), dict)
                    else None
                )
                if generation is not None:
                    key = (str(row.get("namespace") or ""), str(row.get("created_at_utc") or ""))
                    active_slots = generation.get("active_symbol_slot_count")
                    candidate_in = bridge.get("n_candidates_in")
                    value = (
                        active_slots if isinstance(active_slots, int) else None,
                        candidate_in if isinstance(candidate_in, int) else None,
                    )
                    previous = legacy_generation_cycles.setdefault(key, value)
                    if previous != value:
                        legacy_generation_conflicts.append({
                            "namespace": key[0],
                            "created_at_utc": key[1],
                            "first": previous,
                            "later": value,
                        })
                continue
            rows.append(row)
    expected_slots = sum(
        value[0] for value in legacy_generation_cycles.values() if value[0] is not None
    )
    candidate_in = sum(
        value[1] for value in legacy_generation_cycles.values() if value[1] is not None
    )
    return rows, {
        "status": "PASS" if not parse_issues else "FAIL",
        "path": str(path),
        "lines_total": total_lines,
        "legacy_rows_without_live_flow": legacy_rows,
        "live_flow_rows_loaded": len(rows),
        "live_flow_coverage_status": (
            "LIVE_FLOW_ONLY"
            if rows and not legacy_rows
            else "MIXED_LEGACY_AND_LIVE_FLOW"
            if rows
            else "LEGACY_ONLY_NO_LIVE_FLOW"
            if legacy_rows
            else "EMPTY"
        ),
        "legacy_native_generation_census": {
            "status": (
                "MEASURED_AGGREGATE_CYCLES_SLOT_TERMINALS_ABSENT"
                if legacy_generation_cycles and not legacy_generation_conflicts
                else "CONFLICTING_AGGREGATE_CYCLE_ROWS"
                if legacy_generation_conflicts
                else "NO_LEGACY_GENERATION_ROWS"
            ),
            "unique_generation_cycles": len(legacy_generation_cycles),
            "aggregate_active_symbol_slots": expected_slots,
            "aggregate_bridge_candidates_in": candidate_in,
            "slot_minus_bridge_candidate_in_arithmetic": expected_slots - candidate_in,
            "cycle_no_candidates_rows": legacy_empty_cycles,
            "cycle_no_candidates_missing_decision_bar": legacy_empty_cycles_missing_bar,
            "generation_cycle_conflicts": legacy_generation_conflicts,
            "claim_boundary": (
                "Aggregate configured slot and candidate-in counts are measured. Per-slot terminal "
                "status, exact non-emission identity, and stream schedule are absent and cannot be "
                "reconstructed from these legacy packets."
            ),
        },
        "parse_issues": parse_issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", default=DEFAULT_LOG_PATH)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    rows, ingestion = load_rows(Path(args.path))
    reconciliation = reconcile_live_flow_rows(rows)
    coverage = ingestion.get("live_flow_coverage_status")
    if ingestion["status"] != "PASS" or reconciliation["status"] != "PASS":
        status = "FAIL"
    elif coverage == "LEGACY_ONLY_NO_LIVE_FLOW":
        status = "LEGACY_CENSUS_ONLY_LIVE_FLOW_NOT_EVALUABLE"
    elif coverage == "EMPTY":
        status = "FAIL"
    else:
        status = "PASS"
    report = {
        "schema_version": "gtos.live_flow.reconciliation.v1",
        "status": status,
        "evidence_coverage_status": coverage,
        "ingestion": ingestion,
        "reconciliation": reconciliation,
    }
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 2 if args.strict and report["status"] != "PASS" else 0


if __name__ == "__main__":
    raise SystemExit(main())
