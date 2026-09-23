#!/usr/bin/env python3
"""Evaluate prospective Phase 3 truth-layer files against the frozen matrix.

This is the next research-only evaluator after the candidate matrix registry.
It refuses historical rows, keeps all registered matrix candidates in scope for
PBO/effective-N, and reports the two primary children without allowing alpha
promotion.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.analyze_truth_layer_effective_n import (
    DEFAULT_MATRIX_PATH,
    RESOLVED_OUTCOMES,
    analyze_effective_n,
    build_return_matrix,
    load_matrix_registry,
)
from scripts.analyze_truth_layer_posthoc_pbo import _row_month, cscv_pbo
from scripts.evaluate_truth_layer_controlled_hypotheses import (
    DEFAULT_SPEC_PATH,
    _as_float,
    _hypothesis_summary_row,
    _markdown_cell,
    _population_inclusion,
    _row_cohort_key,
    evaluate_controlled_hypotheses,
    iter_jsonl,
)
from scripts.evaluate_truth_layer_prospective_holdout import (
    PROSPECTIVE_CUTOFF_UTC,
    validate_prospective_input,
)


SCHEMA_VERSION = "truth_layer_prospective_matrix_evaluator_v1"
DEFAULT_OUTPUT_ROOT = (
    "data/external/validation/calendar_macro_bundle_v1/historical_opportunities/"
    "truth_layer/prospective_matrix"
)
DEFAULT_REPORT_PATH = (
    "research/phase_3_external_feed_validation/"
    "TRUTH_LAYER_PROSPECTIVE_MATRIX_REPORT_2026-05-01.md"
)


def evaluate_prospective_matrix(
    *,
    input_path: str | Path,
    spec_path: str | Path = DEFAULT_SPEC_PATH,
    matrix_path: str | Path = DEFAULT_MATRIX_PATH,
    cutoff_utc: datetime = PROSPECTIVE_CUTOFF_UTC,
    max_rows: int | None = None,
) -> dict[str, Any]:
    validation = validate_prospective_input(
        input_path,
        cutoff_utc=cutoff_utc,
        max_rows=max_rows,
    )
    if not validation["prospective_input_valid"]:
        raise ValueError(_invalid_reason(validation))

    controlled = evaluate_controlled_hypotheses(
        input_path=input_path,
        spec_path=spec_path,
        max_rows=max_rows,
    )
    matrix_eval = evaluate_registered_matrix_pbo(
        input_path=input_path,
        matrix_path=matrix_path,
        max_rows=max_rows,
    )
    effective_n = analyze_effective_n(
        input_path=input_path,
        matrix_path=matrix_path,
        analysis_context="prospective_registered_matrix",
        max_rows=max_rows,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_validation": validation,
        "controlled_summary": controlled,
        "matrix_pbo": matrix_eval,
        "effective_n": {
            "matrix_effective_n": effective_n.get("matrix_effective_n"),
            "primary_children_effective_n": effective_n.get("primary_children_effective_n"),
            "candidate_activity": effective_n.get("candidate_activity"),
            "promotion_usable": effective_n.get("promotion_usable"),
            "promotion_usable_reason": effective_n.get("promotion_usable_reason"),
        },
        "promotion_verdict_allowed": False,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "promotion_blocked_reason": "Prospective matrix evaluator does not compute DSR-corrected p.",
        "methodology_gates": {
            "prospective_input": "PASS",
            "dsr_corrected_p": "NOT_COMPUTED",
            "pbo": _gate_status_pbo(matrix_eval),
            "effective_n": _gate_status_effective_n(effective_n.get("matrix_effective_n") or {}),
        },
    }


def evaluate_registered_matrix_pbo(
    *,
    input_path: str | Path,
    matrix_path: str | Path = DEFAULT_MATRIX_PATH,
    max_rows: int | None = None,
) -> dict[str, Any]:
    registry = load_matrix_registry(matrix_path)
    candidates = list(registry.get("candidates") or [])
    candidate_keys = [str(row["cohort_key"]) for row in candidates]
    population = registry.get("population") or {}
    period_returns: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    periods: set[str] = set()
    rows_scanned = 0
    included_rows = 0
    resolved_rows = 0

    candidate_set = set(candidate_keys)
    for rows_scanned, row in enumerate(iter_jsonl(input_path), start=1):
        key = _row_cohort_key(row)
        if key in candidate_set:
            included, _ = _population_inclusion(row, population)
            if included:
                included_rows += 1
                period = _row_month(row)
                periods.add(period)
                if str(row.get("truth_outcome") or "") in RESOLVED_OUTCOMES:
                    realized = _as_float(row.get("truth_realized_r"))
                    if realized is not None:
                        resolved_rows += 1
                        period_returns[period][key] += realized
        if max_rows is not None and rows_scanned >= max_rows:
            break

    all_periods = sorted(periods)
    matrix = build_return_matrix(
        candidate_keys=candidate_keys,
        periods=all_periods,
        period_returns=period_returns,
    )
    pbo, diagnostic = cscv_pbo(matrix.tolist())
    status = diagnostic.get("status")
    if status == "COMPUTED_POSTHOC_DIAGNOSTIC_ONLY":
        status = "COMPUTED_PROSPECTIVE_MATRIX_DIAGNOSTIC_ONLY"
    return {
        "status": status,
        "promotion_usable": False,
        "promotion_usable_reason": "Prospective matrix PBO still requires DSR and full promotion prerequisites.",
        "pbo": pbo,
        "threshold_pbo_lt_0_4_met": pbo is not None and pbo < 0.4,
        "period_count": len(all_periods),
        "candidate_count": len(candidate_keys),
        "rows_scanned": rows_scanned,
        "included_matrix_rows": included_rows,
        "resolved_matrix_rows": resolved_rows,
        "path_start": all_periods[0] if all_periods else None,
        "path_end": all_periods[-1] if all_periods else None,
        "diagnostics": diagnostic,
    }


def render_report(summary: Mapping[str, Any]) -> str:
    validation = summary.get("input_validation") or {}
    controlled = summary.get("controlled_summary") or {}
    effective_n = summary.get("effective_n") or {}
    lines = [
        "# Phase 3 Prospective Truth-Layer Matrix Report",
        "",
        f"**Created UTC:** {summary.get('created_at_utc')}",
        f"**Input:** `{validation.get('input_jsonl')}`",
        f"**Prospective cutoff UTC:** `{validation.get('prospective_cutoff_utc')}`",
        f"**Promotion verdict:** `{summary.get('promotion_verdict')}`",
        "",
        "## Boundary",
        "",
        "- Research/tooling only; no live trading logic, prompt, config, risk policy, or execution behavior is changed.",
        "- This evaluator refuses same-dataset rows at or before the registered cutoff.",
        "- It evaluates the full frozen candidate matrix, not only the two primary children.",
        "- DSR-corrected p is not computed here, so alpha promotion remains blocked.",
        "",
        "## Input Validation",
        "",
        _markdown_table([validation]),
        "",
        "## Gate Matrix",
        "",
        _markdown_table([summary.get("methodology_gates") or {}]),
        "",
        "## Primary Child Summary",
        "",
        _markdown_table([
            _hypothesis_summary_row(item)
            for item in controlled.get("hypotheses", [])
        ]),
        "",
        "## Matrix PBO",
        "",
        _markdown_table([_matrix_pbo_row(summary.get("matrix_pbo") or {})]),
        "",
        "## Matrix Effective-N",
        "",
        _markdown_table([_effective_n_row(effective_n.get("matrix_effective_n") or {})]),
        "",
        "## Primary Children Effective-N",
        "",
        _markdown_table([_effective_n_row(effective_n.get("primary_children_effective_n") or {})]),
        "",
        "## Candidate Activity",
        "",
        _markdown_table(effective_n.get("candidate_activity") or []),
        "",
        "## Synthesis",
        "",
        "- This is the evaluator to use once genuine prospective truth-layer rows exist.",
        "- If PBO or effective_N are blocked because too few periods exist, keep collecting rows.",
        "- Promotion remains impossible until a separate DSR-capable evaluator is added and all gates pass.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def write_outputs(
    summary: Mapping[str, Any],
    *,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    report_path: str | Path = DEFAULT_REPORT_PATH,
) -> tuple[Path, Path]:
    output_dir = Path(output_root)
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    summary_path = output_dir / f"truth_layer_prospective_matrix_{stamp}.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    report = Path(report_path)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(summary), encoding="utf-8")
    return summary_path, report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Prospective truth-layer JSONL to evaluate.")
    parser.add_argument("--spec-path", default=DEFAULT_SPEC_PATH)
    parser.add_argument("--matrix-path", default=DEFAULT_MATRIX_PATH)
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--report-path", default=DEFAULT_REPORT_PATH)
    parser.add_argument("--cutoff-utc", default=PROSPECTIVE_CUTOFF_UTC.isoformat())
    parser.add_argument("--max-rows", type=int)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    cutoff = datetime.fromisoformat(args.cutoff_utc.replace("Z", "+00:00"))
    try:
        summary = evaluate_prospective_matrix(
            input_path=args.input,
            spec_path=args.spec_path,
            matrix_path=args.matrix_path,
            cutoff_utc=cutoff,
            max_rows=args.max_rows,
        )
    except ValueError as exc:
        print(json.dumps({"error": str(exc), "promotion_verdict": "BLOCKED"}, indent=2, sort_keys=True))
        return 2
    if args.write:
        summary_path, report_path = write_outputs(
            summary,
            output_root=args.output_root,
            report_path=args.report_path,
        )
        summary = dict(summary)
        summary["output_summary"] = str(summary_path)
        summary["report_path"] = str(report_path)
    if args.quiet:
        effective_n = summary.get("effective_n") or {}
        print(
            json.dumps(
                {
                    "promotion_verdict": summary.get("promotion_verdict"),
                    "methodology_gates": summary.get("methodology_gates"),
                    "matrix_pbo": _matrix_pbo_row(summary.get("matrix_pbo") or {}),
                    "matrix_effective_n": _effective_n_row(effective_n.get("matrix_effective_n") or {}),
                    "primary_children_effective_n": _effective_n_row(
                        effective_n.get("primary_children_effective_n") or {}
                    ),
                    "output_summary": summary.get("output_summary"),
                    "report_path": summary.get("report_path"),
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def _gate_status_pbo(matrix_eval: Mapping[str, Any]) -> str:
    if matrix_eval.get("pbo") is None:
        return str(matrix_eval.get("status") or "BLOCKED")
    return "PASS_DIAGNOSTIC_ONLY" if matrix_eval.get("threshold_pbo_lt_0_4_met") else "FAIL_DIAGNOSTIC_ONLY"


def _gate_status_effective_n(diagnostic: Mapping[str, Any]) -> str:
    if diagnostic.get("effective_n") is None:
        return str(diagnostic.get("status") or "BLOCKED")
    return "PASS_DIAGNOSTIC_ONLY" if diagnostic.get("threshold_effective_n_gte_3_met") else "FAIL_DIAGNOSTIC_ONLY"


def _invalid_reason(validation: Mapping[str, Any]) -> str:
    return (
        "prospective input is invalid: "
        f"rows={validation.get('rows_scanned')}, "
        f"stale_rows_at_or_before_cutoff={validation.get('stale_rows_at_or_before_cutoff')}, "
        f"missing_timestamp_rows={validation.get('missing_timestamp_rows')}, "
        f"duplicate_keys={validation.get('duplicate_keys')}, "
        f"ai_attempted_rows={validation.get('ai_attempted_rows')}, "
        f"ai_call_count_sum={validation.get('ai_call_count_sum')}"
    )


def _matrix_pbo_row(matrix_pbo: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "status": matrix_pbo.get("status"),
        "period_count": matrix_pbo.get("period_count"),
        "candidate_count": matrix_pbo.get("candidate_count"),
        "resolved_matrix_rows": matrix_pbo.get("resolved_matrix_rows"),
        "pbo": matrix_pbo.get("pbo"),
        "threshold_pbo_lt_0_4_met": matrix_pbo.get("threshold_pbo_lt_0_4_met"),
        "path_start": matrix_pbo.get("path_start"),
        "path_end": matrix_pbo.get("path_end"),
        "promotion_usable": matrix_pbo.get("promotion_usable"),
    }


def _effective_n_row(diagnostic: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "status": diagnostic.get("status"),
        "period_count": diagnostic.get("period_count"),
        "candidate_count": diagnostic.get("candidate_count"),
        "active_candidate_count": diagnostic.get("active_candidate_count"),
        "effective_n": diagnostic.get("effective_n"),
        "threshold_effective_n_gte_3_met": diagnostic.get("threshold_effective_n_gte_3_met"),
        "average_pairwise_correlation": diagnostic.get("average_pairwise_correlation"),
        "average_abs_pairwise_correlation": diagnostic.get("average_abs_pairwise_correlation"),
        "path_start": diagnostic.get("path_start"),
        "path_end": diagnostic.get("path_end"),
    }


def _markdown_table(rows: Sequence[Mapping[str, Any]]) -> str:
    if not rows:
        return "_No rows._"
    preferred = (
        "prospective_input_valid",
        "rows_scanned",
        "unique_keys",
        "duplicate_keys",
        "missing_timestamp_rows",
        "stale_rows_at_or_before_cutoff",
        "ai_attempted_rows",
        "ai_call_count_sum",
        "min_candle_close_utc",
        "max_candle_close_utc",
        "prospective_input",
        "dsr_corrected_p",
        "pbo",
        "effective_n",
        "hypothesis_id",
        "cohort_key",
        "role",
        "matching_setup_rows",
        "population_rows",
        "resolved_r_n",
        "mean_r",
        "win_rate",
        "no_entry",
        "status",
        "period_count",
        "candidate_count",
        "active_candidate_count",
        "resolved_matrix_rows",
        "threshold_pbo_lt_0_4_met",
        "threshold_effective_n_gte_3_met",
        "average_pairwise_correlation",
        "average_abs_pairwise_correlation",
        "path_start",
        "path_end",
        "promotion_usable",
        "active_periods",
        "sum_r",
        "mean_period_sum_r",
        "std_period_sum_r",
    )
    keys = list(rows[0].keys())
    columns = [key for key in preferred if key in keys]
    columns.extend(key for key in keys if key not in columns)
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_markdown_cell(row.get(col, "")) for col in columns) + " |")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
