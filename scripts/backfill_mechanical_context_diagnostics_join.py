#!/usr/bin/env python3
"""Backfill append-only LTO-020 mechanical/context diagnostics join rows."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research_infra.mechanical_context_diagnostics_join import (  # noqa: E402
    ACTION_REQUIRED,
    COMPLETE,
    PARTIAL,
    PROMOTION_VERDICT,
    SCHEMA_VERSION,
    build_mechanical_context_rows,
    build_rolling_status,
)


DEFAULT_CANDIDATES = Path("shadow_logs/strategy_follow_candidates.jsonl")
DEFAULT_PATH_FOLLOW = Path("shadow_logs/candidate_path_follow.jsonl")
DEFAULT_BROKER_AUDIT = Path("shadow_logs/broker_actual_r_audit.jsonl")
DEFAULT_DUMB_BASELINE = Path("shadow_logs/dumb_baseline_hypotheticals.jsonl")
DEFAULT_PROXIMITY = Path("shadow_logs/proximity_shadow_log.jsonl")
DEFAULT_LIQUIDITY = Path("shadow_logs/liquidity_distance_log.jsonl")
DEFAULT_DISPLACEMENT = Path("shadow_logs/displacement_events.jsonl")
DEFAULT_STRUCTURE_DIVERGENCE = Path("shadow_logs/structure_detector_divergences.jsonl")
DEFAULT_OUTPUT = Path("shadow_logs/mechanical_context_diagnostics_join.jsonl")
DEFAULT_REPORT_JSON = Path("research/program_control/LTO020_MECHANICAL_CONTEXT_DIAGNOSTICS_JOIN_2026-05-05.json")
DEFAULT_REPORT_MD = Path("research/program_control/LTO020_MECHANICAL_CONTEXT_DIAGNOSTICS_JOIN_2026-05-05.md")


def read_jsonl_with_lines(path: Path) -> list[tuple[int, dict[str, Any]]]:
    if not path.exists():
        return []
    rows: list[tuple[int, dict[str, Any]]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                row = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append((line_no, row))
    return rows


def existing_row_keys(path: Path) -> set[str]:
    return {str(row.get("row_key")) for _, row in read_jsonl_with_lines(path) if row.get("row_key")}


def append_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def build_report(
    rows: list[dict[str, Any]],
    appended_rows: list[dict[str, Any]],
    output_path: Path,
    *,
    source_counts: dict[str, int],
) -> dict[str, Any]:
    rolling = build_rolling_status(rows)
    status_counts = Counter(str(row.get("mechanical_context_status") or "UNKNOWN") for row in rows)
    action_rows = [
        {
            "row_key": row.get("row_key"),
            "candidate_id": row.get("candidate_id"),
            "symbol": row.get("symbol"),
            "framework": row.get("framework"),
            "decision_time_utc": row.get("decision_time_utc"),
            "candidate_final_outcome_at_log": row.get("candidate_final_outcome_at_log"),
            "action_required_codes": row.get("action_required_codes") or [],
            "mismatch_codes": row.get("mismatch_codes") or [],
        }
        for row in rows
        if row.get("mechanical_context_status") == ACTION_REQUIRED or row.get("action_required_codes")
    ]
    return {
        "schema_version": "lto020_mechanical_context_diagnostics_join_report_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": PROMOTION_VERDICT,
        "status": "ACTION_REQUIRED" if action_rows else "OK_MECHANICAL_CONTEXT_DIAGNOSTICS_JOIN_DOCUMENTED",
        "status_log_path": str(output_path),
        "status_log_schema": SCHEMA_VERSION,
        "counts": {
            "rows_computed": len(rows),
            "status_rows_available": len(read_jsonl_with_lines(output_path)),
            "status_rows_appended_this_run": len(appended_rows),
            "complete_joined_rows": status_counts.get(COMPLETE, 0),
            "partial_joined_rows": status_counts.get(PARTIAL, 0),
            "action_required_rows": status_counts.get(ACTION_REQUIRED, 0),
            "path_joined_rows": rolling["path_joined_rows"],
            "actual_r_claim_allowed_rows": rolling["actual_r_claim_allowed_rows"],
            "action_required": len(action_rows),
        },
        "source_counts": source_counts,
        "rolling_status": rolling,
        "action_required_examples": action_rows[:25],
        "claim_boundary": (
            "This report joins existing mechanical/context diagnostics to candidate rows. "
            "It is ML/research substrate only and does not alter prompts, safety gates, risk, execution, or orders."
        ),
        "ml_goal_contribution": (
            "The lane turns dumb-baseline comparators, OB proximity, liquidity-distance geometry, "
            "displacement state, structure-detector divergence, path labels, and account-history label status "
            "into one K55-ready feature/provenance/sample-eligibility surface."
        ),
        "discovery_only_correlation_boundary": (
            "Path labels, broker actual-R, and dumb-baseline outcomes are correlation/comparator labels only. "
            "They are not decision-time features and remain NO_PROMOTION_VERDICT."
        ),
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "ai_calls": 0,
        "canary_calls": 0,
        "order_calls": 0,
        "paid_data_calls": 0,
        "paid_fetch_attempted": False,
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    counts = report["counts"]
    rolling = report["rolling_status"]
    lines = [
        "# LTO-020 Mechanical Context Diagnostics Join - 2026-05-05",
        "",
        f"**Schema:** `{report['schema_version']}`",
        f"**Generated:** `{report['generated_at_utc']}`",
        f"**Status:** `{report['status']}`",
        f"**Promotion verdict:** `{report['promotion_verdict']}`",
        "",
        "## Counts",
        "",
        f"- Rows computed: `{counts['rows_computed']}`",
        f"- Status rows available: `{counts['status_rows_available']}`",
        f"- Status rows appended this run: `{counts['status_rows_appended_this_run']}`",
        f"- Complete joined rows: `{counts['complete_joined_rows']}`",
        f"- Partial documented rows: `{counts['partial_joined_rows']}`",
        f"- Action-required rows: `{counts['action_required_rows']}`",
        f"- Path joined rows: `{counts['path_joined_rows']}`",
        f"- Actual-R claim allowed rows: `{counts['actual_r_claim_allowed_rows']}`",
        f"- Action required: `{counts['action_required']}`",
        "",
        "## Source Counts",
        "",
        f"`{report['source_counts']}`",
        "",
        "## Status Breakdown",
        "",
        f"- Status counts: `{rolling['status_counts']}`",
        f"- Symbol counts: `{rolling['symbol_counts']}`",
        f"- Framework counts: `{rolling['framework_counts']}`",
        f"- Final outcome counts: `{rolling['final_outcome_counts']}`",
        f"- ML label eligibility counts: `{rolling['ml_label_eligibility_counts']}`",
        f"- Mechanical context join counts: `{rolling['mechanical_context_join_counts']}`",
        f"- Action-required codes: `{rolling['action_required_code_counts']}`",
        f"- Mismatch codes: `{rolling['mismatch_code_counts']}`",
        f"- Documented limitations: `{rolling['documented_limitation_code_counts']}`",
        "",
        "## Discovery-Only Correlations",
        "",
        f"- Proximity by path label: `{rolling['proximity_by_path_label']}`",
        f"- Dumb-baseline realized R by path label: `{rolling['dumb_baseline_realized_r_by_path_label']}`",
        "",
        "## Boundary",
        "",
        report["claim_boundary"],
        "",
        "## Discovery Boundary",
        "",
        report["discovery_only_correlation_boundary"],
        "",
        "## ML Goal Contribution",
        "",
        report["ml_goal_contribution"],
        "",
        "## Safety Counters",
        "",
        f"- ai_calls: `{report['ai_calls']}`",
        f"- canary_calls: `{report['canary_calls']}`",
        f"- order_calls: `{report['order_calls']}`",
        f"- paid_data_calls: `{report['paid_data_calls']}`",
    ]
    if report["action_required_examples"]:
        lines.extend(["", "## Action Required Examples", "", "```json", json.dumps(report["action_required_examples"], indent=2, sort_keys=True), "```"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--path-follow", type=Path, default=DEFAULT_PATH_FOLLOW)
    parser.add_argument("--broker-audit", type=Path, default=DEFAULT_BROKER_AUDIT)
    parser.add_argument("--dumb-baseline", type=Path, default=DEFAULT_DUMB_BASELINE)
    parser.add_argument("--proximity", type=Path, default=DEFAULT_PROXIMITY)
    parser.add_argument("--liquidity", type=Path, default=DEFAULT_LIQUIDITY)
    parser.add_argument("--displacement", type=Path, default=DEFAULT_DISPLACEMENT)
    parser.add_argument("--structure-divergence", type=Path, default=DEFAULT_STRUCTURE_DIVERGENCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report-json", type=Path, default=DEFAULT_REPORT_JSON)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    args = parser.parse_args()

    generated_at = datetime.now(timezone.utc).isoformat()
    candidate_rows = read_jsonl_with_lines(args.candidates)
    path_rows = read_jsonl_with_lines(args.path_follow)
    broker_rows = read_jsonl_with_lines(args.broker_audit)
    dumb_rows = read_jsonl_with_lines(args.dumb_baseline)
    proximity_rows = read_jsonl_with_lines(args.proximity)
    liquidity_rows = read_jsonl_with_lines(args.liquidity)
    displacement_rows = read_jsonl_with_lines(args.displacement)
    structure_rows = read_jsonl_with_lines(args.structure_divergence)
    rows = build_mechanical_context_rows(
        candidate_rows,
        path_rows=path_rows,
        broker_rows=broker_rows,
        dumb_rows=dumb_rows,
        proximity_rows=proximity_rows,
        liquidity_rows=liquidity_rows,
        displacement_rows=displacement_rows,
        structure_rows=structure_rows,
        generated_at_utc=generated_at,
    )
    existing = existing_row_keys(args.output)
    appended = [row for row in rows if str(row.get("row_key")) not in existing]
    append_jsonl(args.output, appended)

    report = build_report(
        rows,
        appended,
        args.output,
        source_counts={
            "candidate_rows": len(candidate_rows),
            "path_rows": len(path_rows),
            "broker_audit_rows": len(broker_rows),
            "dumb_baseline_rows": len(dumb_rows),
            "proximity_rows": len(proximity_rows),
            "liquidity_distance_rows": len(liquidity_rows),
            "displacement_rows": len(displacement_rows),
            "structure_divergence_rows": len(structure_rows),
        },
    )
    args.report_json.parent.mkdir(parents=True, exist_ok=True)
    args.report_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, args.report_md)
    print(
        json.dumps(
            {
                "status": report["status"],
                "rows_computed": report["counts"]["rows_computed"],
                "status_rows_appended": len(appended),
                "status_rows_available": report["counts"]["status_rows_available"],
                "action_required": report["counts"]["action_required"],
            },
            sort_keys=True,
        )
    )
    return 1 if report["status"] == "ACTION_REQUIRED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
