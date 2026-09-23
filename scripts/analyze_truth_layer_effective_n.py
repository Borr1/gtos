#!/usr/bin/env python3
"""Compute effective-N diagnostics for the Phase 3 truth-layer matrix.

This uses the registered candidate matrix and a path-level return matrix. The
historical run is diagnostic-only because the candidate matrix was frozen after
historical discovery; the same code is intended for future prospective rows.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.analyze_truth_layer_posthoc_pbo import _row_month
from scripts.evaluate_truth_layer_controlled_hypotheses import (
    _as_float,
    _population_inclusion,
    _row_cohort_key,
    find_latest_input,
    iter_jsonl,
)


SCHEMA_VERSION = "truth_layer_effective_n_diagnostic_v1"
DEFAULT_MATRIX_PATH = (
    "research/phase_3_external_feed_validation/"
    "TRUTH_LAYER_PROSPECTIVE_CANDIDATE_MATRIX_V1.json"
)
DEFAULT_OUTPUT_ROOT = (
    "data/external/validation/calendar_macro_bundle_v1/historical_opportunities/"
    "truth_layer/effective_n"
)
DEFAULT_REPORT_PATH = (
    "research/phase_3_external_feed_validation/"
    "TRUTH_LAYER_EFFECTIVE_N_DIAGNOSTIC_2026-05-01.md"
)
RESOLVED_OUTCOMES = {"TP", "SL", "TIMEOUT"}


def load_matrix_registry(path: str | Path = DEFAULT_MATRIX_PATH) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != "truth_layer_prospective_candidate_matrix_v1":
        raise ValueError(f"unsupported matrix schema: {payload.get('schema_version')!r}")
    if payload.get("promotion_verdict_allowed") is not False:
        raise ValueError("truth-layer candidate matrix must set promotion_verdict_allowed=false")
    if not payload.get("candidates"):
        raise ValueError("truth-layer candidate matrix has no candidates")
    return payload


def analyze_effective_n(
    *,
    input_path: str | Path,
    matrix_path: str | Path = DEFAULT_MATRIX_PATH,
    analysis_context: str = "historical_after_discovery",
    max_rows: int | None = None,
) -> dict[str, Any]:
    registry = load_matrix_registry(matrix_path)
    candidates = list(registry.get("candidates") or [])
    candidate_keys = [str(row["cohort_key"]) for row in candidates]
    candidate_set = set(candidate_keys)
    population = registry.get("population") or {}
    period_returns: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    period_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    periods: set[str] = set()
    rows_scanned = 0
    ai_attempted_rows = 0
    ai_call_count_sum = 0

    for rows_scanned, row in enumerate(iter_jsonl(input_path), start=1):
        if row.get("ai_call_attempted"):
            ai_attempted_rows += 1
        ai_call_count_sum += int(row.get("ai_call_count") or 0)
        key = _row_cohort_key(row)
        if key in candidate_set:
            included, _ = _population_inclusion(row, population)
            if included:
                period = _row_month(row)
                periods.add(period)
                if str(row.get("truth_outcome") or "") in RESOLVED_OUTCOMES:
                    realized = _as_float(row.get("truth_realized_r"))
                    if realized is not None:
                        period_returns[period][key] += realized
                        period_counts[period][key] += 1
        if max_rows is not None and rows_scanned >= max_rows:
            break

    all_periods = sorted(periods)
    matrix = build_return_matrix(
        candidate_keys=candidate_keys,
        periods=all_periods,
        period_returns=period_returns,
    )
    diagnostics = effective_n_diagnostics(matrix, candidate_keys=candidate_keys, periods=all_periods)
    primary_keys = [
        str(row["cohort_key"])
        for row in candidates
        if row.get("role") == "primary_controlled_child"
    ]
    primary_matrix = select_columns(matrix, candidate_keys, primary_keys)
    primary_diagnostics = effective_n_diagnostics(
        primary_matrix,
        candidate_keys=primary_keys,
        periods=all_periods,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_jsonl": str(Path(input_path)),
        "matrix_path": str(Path(matrix_path)),
        "promotion_verdict_allowed": False,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "promotion_usable": False,
        "promotion_usable_reason": _promotion_usable_reason(analysis_context),
        "analysis_context": analysis_context,
        "rows_scanned": rows_scanned,
        "ai_attempted_rows": ai_attempted_rows,
        "ai_call_count_sum": ai_call_count_sum,
        "period_count": len(all_periods),
        "candidate_count": len(candidate_keys),
        "primary_candidate_count": len(primary_keys),
        "path_definition": {
            "path_unit": "calendar_month",
            "return_metric": "sum_truth_realized_r_on_resolved_rows",
            "missing_period_policy": "zero_return_no_resolved_trade",
        },
        "effective_n_method": {
            "primary": "correlation_eigenvalue_participation_ratio",
            "formula": "(sum(lambda)^2) / sum(lambda^2) on the candidate return correlation matrix",
            "promotion_threshold": 3,
        },
        "matrix_effective_n": diagnostics,
        "primary_children_effective_n": primary_diagnostics,
        "candidate_activity": candidate_activity_rows(
            candidate_keys=candidate_keys,
            matrix=matrix,
            period_counts=period_counts,
            periods=all_periods,
            registry_candidates=candidates,
        ),
    }


def build_return_matrix(
    *,
    candidate_keys: Sequence[str],
    periods: Sequence[str],
    period_returns: Mapping[str, Mapping[str, float]],
) -> np.ndarray:
    matrix = np.zeros((len(periods), len(candidate_keys)), dtype=float)
    for row_idx, period in enumerate(periods):
        row = period_returns.get(period) or {}
        for col_idx, key in enumerate(candidate_keys):
            matrix[row_idx, col_idx] = float(row.get(key) or 0.0)
    return matrix


def effective_n_diagnostics(
    matrix: np.ndarray,
    *,
    candidate_keys: Sequence[str],
    periods: Sequence[str],
) -> dict[str, Any]:
    if matrix.size == 0 or matrix.shape[0] < 2 or matrix.shape[1] < 1:
        return {
            "status": "BLOCKED_INSUFFICIENT_MATRIX",
            "period_count": int(matrix.shape[0]) if matrix.ndim == 2 else 0,
            "candidate_count": int(matrix.shape[1]) if matrix.ndim == 2 else 0,
            "effective_n": None,
        }
    variances = np.var(matrix, axis=0, ddof=1)
    active_idx = [idx for idx, var in enumerate(variances) if math.isfinite(float(var)) and var > 1e-12]
    if len(active_idx) < 1:
        return {
            "status": "BLOCKED_ZERO_VARIANCE",
            "period_count": int(matrix.shape[0]),
            "candidate_count": int(matrix.shape[1]),
            "active_candidate_count": 0,
            "effective_n": None,
        }
    active = matrix[:, active_idx]
    if active.shape[1] == 1:
        corr = np.ones((1, 1), dtype=float)
    else:
        corr = np.corrcoef(active, rowvar=False)
        corr = np.nan_to_num(corr, nan=0.0, posinf=0.0, neginf=0.0)
        corr = (corr + corr.T) / 2.0
        np.fill_diagonal(corr, 1.0)
    effective_n, eigenvalues = effective_n_participation_ratio(corr)
    avg_corr, avg_abs_corr = average_pairwise_correlations(corr)
    threshold_met = effective_n >= 3.0
    return {
        "status": "COMPUTED_DIAGNOSTIC_ONLY",
        "period_count": int(matrix.shape[0]),
        "candidate_count": int(matrix.shape[1]),
        "active_candidate_count": len(active_idx),
        "inactive_candidate_count": int(matrix.shape[1] - len(active_idx)),
        "effective_n": round(effective_n, 6),
        "threshold_effective_n_gte_3_met": threshold_met,
        "average_pairwise_correlation": round(avg_corr, 6) if avg_corr is not None else None,
        "average_abs_pairwise_correlation": round(avg_abs_corr, 6) if avg_abs_corr is not None else None,
        "eigenvalues": [round(float(value), 6) for value in eigenvalues],
        "active_candidates": [candidate_keys[idx] for idx in active_idx],
        "path_start": periods[0] if periods else None,
        "path_end": periods[-1] if periods else None,
    }


def effective_n_participation_ratio(corr: np.ndarray) -> tuple[float, list[float]]:
    if corr.size == 0:
        return 0.0, []
    eigenvalues = np.linalg.eigvalsh(corr)
    eigenvalues = np.clip(eigenvalues.astype(float), 0.0, None)
    total = float(eigenvalues.sum())
    denom = float(np.square(eigenvalues).sum())
    if total <= 0 or denom <= 0:
        return 0.0, [float(value) for value in eigenvalues]
    return float((total * total) / denom), [float(value) for value in eigenvalues]


def average_pairwise_correlations(corr: np.ndarray) -> tuple[float | None, float | None]:
    n = corr.shape[0]
    if n < 2:
        return None, None
    values = [float(corr[i, j]) for i in range(n) for j in range(i + 1, n)]
    if not values:
        return None, None
    return sum(values) / len(values), sum(abs(value) for value in values) / len(values)


def select_columns(matrix: np.ndarray, candidate_keys: Sequence[str], selected_keys: Sequence[str]) -> np.ndarray:
    indexes = [candidate_keys.index(key) for key in selected_keys if key in candidate_keys]
    if not indexes:
        return np.zeros((matrix.shape[0], 0), dtype=float)
    return matrix[:, indexes]


def candidate_activity_rows(
    *,
    candidate_keys: Sequence[str],
    matrix: np.ndarray,
    period_counts: Mapping[str, Mapping[str, int]],
    periods: Sequence[str],
    registry_candidates: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    roles = {str(row["cohort_key"]): row.get("role") for row in registry_candidates}
    rows = []
    for col_idx, key in enumerate(candidate_keys):
        series = matrix[:, col_idx] if matrix.size else np.array([], dtype=float)
        active_periods = int(np.sum(np.abs(series) > 1e-12)) if len(series) else 0
        resolved_count = sum(int((period_counts.get(period) or {}).get(key) or 0) for period in periods)
        rows.append(
            {
                "cohort_key": key,
                "role": roles.get(key),
                "active_periods": active_periods,
                "resolved_r_n": resolved_count,
                "sum_r": round(float(series.sum()), 6) if len(series) else 0.0,
                "mean_period_sum_r": round(float(series.mean()), 6) if len(series) else None,
                "std_period_sum_r": round(float(series.std(ddof=1)), 6) if len(series) > 1 else None,
            }
        )
    return rows


def _promotion_usable_reason(analysis_context: str) -> str:
    if analysis_context == "prospective_registered_matrix":
        return (
            "Prospective registered-matrix diagnostic only; promotion still requires "
            "DSR, PBO, effective_N, and primary-family prerequisites together."
        )
    return "Historical diagnostic only; candidate matrix was registered after historical discovery."


def render_report(summary: Mapping[str, Any]) -> str:
    lines = [
        "# Phase 3 Truth-Layer Effective-N Diagnostic",
        "",
        f"**Created UTC:** {summary.get('created_at_utc')}",
        f"**Input:** `{summary.get('input_jsonl')}`",
        f"**Matrix:** `{summary.get('matrix_path')}`",
        f"**Promotion verdict:** `{summary.get('promotion_verdict')}`",
        "",
        "## Boundary",
        "",
        "- Research/tooling only; no live trading logic, prompt, config, risk policy, or execution behavior is changed.",
        "- Historical effective_N is diagnostic-only because the matrix was registered after historical discovery.",
        "- Future promotion use requires prospective rows, frozen matrix membership, DSR, PBO, and effective_N together.",
        "",
        "## Method",
        "",
        _markdown_table([summary.get("effective_n_method") or {}]),
        "",
        "## Matrix Effective-N",
        "",
        _markdown_table([_effective_n_row(summary.get("matrix_effective_n") or {})]),
        "",
        "## Primary Children Effective-N",
        "",
        _markdown_table([_effective_n_row(summary.get("primary_children_effective_n") or {})]),
        "",
        "## Candidate Activity",
        "",
        _markdown_table(summary.get("candidate_activity") or []),
        "",
        "## Synthesis",
        "",
        "- The matrix-level effective_N tells us whether the broader instrument universe carries independent validation paths.",
        "- The primary-child effective_N is expected to be small because it contains only two selected cohorts.",
        "- This diagnostic fills the infrastructure gap; it does not rescue historical evidence into promotion proof.",
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
    summary_path = output_dir / f"truth_layer_effective_n_{stamp}.json"
    serializable = dict(summary)
    summary_path.write_text(json.dumps(serializable, indent=2, sort_keys=True), encoding="utf-8")
    report = Path(report_path)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(summary), encoding="utf-8")
    return summary_path, report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="Truth-layer JSONL. Defaults to latest truth-layer artifact.")
    parser.add_argument("--matrix-path", default=DEFAULT_MATRIX_PATH)
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--report-path", default=DEFAULT_REPORT_PATH)
    parser.add_argument("--max-rows", type=int)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    input_path = Path(args.input) if args.input else find_latest_input()
    summary = analyze_effective_n(
        input_path=input_path,
        matrix_path=args.matrix_path,
        max_rows=args.max_rows,
    )
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
        print(
            json.dumps(
                {
                    "promotion_verdict": summary.get("promotion_verdict"),
                    "period_count": summary.get("period_count"),
                    "candidate_count": summary.get("candidate_count"),
                    "matrix_effective_n": _effective_n_row(summary.get("matrix_effective_n") or {}),
                    "primary_children_effective_n": _effective_n_row(summary.get("primary_children_effective_n") or {}),
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
        "status",
        "period_count",
        "candidate_count",
        "active_candidate_count",
        "effective_n",
        "threshold_effective_n_gte_3_met",
        "average_pairwise_correlation",
        "average_abs_pairwise_correlation",
        "path_start",
        "path_end",
        "primary",
        "formula",
        "promotion_threshold",
        "cohort_key",
        "role",
        "active_periods",
        "resolved_r_n",
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


def _markdown_cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        value = json.dumps(value, sort_keys=True)
    return str(value).replace("\n", " ").replace("|", "\\|")


if __name__ == "__main__":
    raise SystemExit(main())
