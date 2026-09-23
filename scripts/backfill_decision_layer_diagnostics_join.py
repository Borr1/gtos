#!/usr/bin/env python3
"""Backfill append-only LTO-019 decision-layer diagnostics join rows."""

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

from src.research_infra.decision_layer_diagnostics_join import (  # noqa: E402
    ACTION_REQUIRED,
    COMPLETE,
    PARTIAL,
    PROMOTION_VERDICT,
    SCHEMA_VERSION,
    build_decision_layer_diagnostics_rows,
    build_rolling_status,
)


DEFAULT_CANDIDATES = Path("shadow_logs/strategy_follow_candidates.jsonl")
DEFAULT_CANDIDATE_FEATURES = Path("shadow_logs/candidate_features_log.jsonl")
DEFAULT_D1_BIAS_LAG = Path("shadow_logs/d1_bias_lag.jsonl")
DEFAULT_DIRECTION_EMISSION = Path("shadow_logs/direction_emission_xau_audit.jsonl")
DEFAULT_SL_BEYOND_OB = Path("shadow_logs/sl_beyond_ob_decisions.jsonl")
DEFAULT_TOUCH_COUNT = Path("shadow_logs/touch_count_gate_decisions.jsonl")
DEFAULT_CROSS_INSTRUMENT_CORRELATION = Path(
    "shadow_logs/cross_instrument_correlation_decisions.jsonl"
)
DEFAULT_OUTPUT = Path("shadow_logs/decision_layer_diagnostics_join.jsonl")
DEFAULT_REPORT_JSON = Path("research/program_control/LTO019_DECISION_LAYER_DIAGNOSTICS_JOIN_2026-05-05.json")
DEFAULT_REPORT_MD = Path("research/program_control/LTO019_DECISION_LAYER_DIAGNOSTICS_JOIN_2026-05-05.md")


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
    status_counts = Counter(str(row.get("decision_diagnostics_status") or "UNKNOWN") for row in rows)
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
        if row.get("decision_diagnostics_status") == ACTION_REQUIRED or row.get("action_required_codes")
    ]
    return {
        "schema_version": "lto019_decision_layer_diagnostics_join_report_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": PROMOTION_VERDICT,
        "status": "ACTION_REQUIRED" if action_rows else "OK_DECISION_LAYER_DIAGNOSTICS_JOIN_DOCUMENTED",
        "status_log_path": str(output_path),
        "status_log_schema": SCHEMA_VERSION,
        "counts": {
            "rows_computed": len(rows),
            "status_rows_available": len(read_jsonl_with_lines(output_path)),
            "status_rows_appended_this_run": len(appended_rows),
            "complete_joined_rows": status_counts.get(COMPLETE, 0),
            "partial_joined_rows": status_counts.get(PARTIAL, 0),
            "action_required_rows": status_counts.get(ACTION_REQUIRED, 0),
            "candidate_features_joined_rows": rolling["candidate_features_joined_rows"],
            "direction_emission_joined_rows": rolling["direction_emission_joined_rows"],
            "sl_beyond_ob_joined_rows": rolling["sl_beyond_ob_joined_rows"],
            "touch_count_joined_rows": rolling["touch_count_joined_rows"],
            "cross_instrument_correlation_joined_rows": rolling[
                "cross_instrument_correlation_joined_rows"
            ],
            "d1_bias_lag_joined_rows": rolling["d1_bias_lag_joined_rows"],
            "action_required": len(action_rows),
        },
        "source_counts": source_counts,
        "rolling_status": rolling,
        "action_required_examples": action_rows[:25],
        "claim_boundary": (
            "This report joins existing decision-time diagnostics to live candidate rows. "
            "It is ML/research substrate only and does not alter prompts, safety gates, risk, execution, or orders."
        ),
        "ml_goal_contribution": (
            "The lane converts AI direction, candidate features, L2 gate state, touch-count state, "
            "D1/H4/H1 lag context, and direction-emission audit rows into one K55-ready "
            "feature/provenance surface with mismatch codes for target refresh and inference QA."
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
        "# LTO-019 Decision-Layer Diagnostics Join - 2026-05-05",
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
        f"- Candidate-features joined rows: `{counts['candidate_features_joined_rows']}`",
        f"- Direction-emission joined rows: `{counts['direction_emission_joined_rows']}`",
        f"- SL-beyond-OB joined rows: `{counts['sl_beyond_ob_joined_rows']}`",
        f"- Touch-count joined rows: `{counts['touch_count_joined_rows']}`",
        f"- Cross-instrument correlation joined rows: `{counts['cross_instrument_correlation_joined_rows']}`",
        f"- D1-bias-lag joined rows: `{counts['d1_bias_lag_joined_rows']}`",
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
        f"- Diagnostic join counts: `{rolling['diagnostic_join_counts']}`",
        f"- Action-required codes: `{rolling['action_required_code_counts']}`",
        f"- Mismatch codes: `{rolling['mismatch_code_counts']}`",
        f"- Documented limitations: `{rolling['documented_limitation_code_counts']}`",
        "",
        "## Cadence Mix",
        "",
        f"- Daily status mix: `{rolling['daily_status_mix']}`",
        f"- Weekly status mix: `{rolling['weekly_status_mix']}`",
        "",
        "## Boundary",
        "",
        report["claim_boundary"],
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
    parser.add_argument("--candidate-features", type=Path, default=DEFAULT_CANDIDATE_FEATURES)
    parser.add_argument("--d1-bias-lag", type=Path, default=DEFAULT_D1_BIAS_LAG)
    parser.add_argument("--direction-emission", type=Path, default=DEFAULT_DIRECTION_EMISSION)
    parser.add_argument("--sl-beyond-ob", type=Path, default=DEFAULT_SL_BEYOND_OB)
    parser.add_argument("--touch-count", type=Path, default=DEFAULT_TOUCH_COUNT)
    parser.add_argument(
        "--cross-instrument-correlation",
        type=Path,
        default=DEFAULT_CROSS_INSTRUMENT_CORRELATION,
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report-json", type=Path, default=DEFAULT_REPORT_JSON)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    args = parser.parse_args()

    generated_at = datetime.now(timezone.utc).isoformat()
    candidate_rows = read_jsonl_with_lines(args.candidates)
    candidate_feature_rows = read_jsonl_with_lines(args.candidate_features)
    d1_bias_rows = read_jsonl_with_lines(args.d1_bias_lag)
    direction_rows = read_jsonl_with_lines(args.direction_emission)
    sl_rows = read_jsonl_with_lines(args.sl_beyond_ob)
    touch_rows = read_jsonl_with_lines(args.touch_count)
    cross_corr_rows = read_jsonl_with_lines(args.cross_instrument_correlation)
    rows = build_decision_layer_diagnostics_rows(
        candidate_rows,
        candidate_feature_rows=candidate_feature_rows,
        d1_bias_rows=d1_bias_rows,
        direction_emission_rows=direction_rows,
        sl_beyond_ob_rows=sl_rows,
        touch_count_rows=touch_rows,
        cross_instrument_correlation_rows=cross_corr_rows,
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
            "candidate_feature_rows": len(candidate_feature_rows),
            "d1_bias_lag_rows": len(d1_bias_rows),
            "direction_emission_rows": len(direction_rows),
            "sl_beyond_ob_rows": len(sl_rows),
            "touch_count_rows": len(touch_rows),
            "cross_instrument_correlation_rows": len(cross_corr_rows),
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
