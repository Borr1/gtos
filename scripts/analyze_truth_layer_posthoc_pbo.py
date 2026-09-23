#!/usr/bin/env python3
"""Post-hoc PBO diagnostic for Phase 3 truth-layer cohort selection risk.

This quantifies same-dataset selection risk over a frozen cohort universe. It
is explicitly non-promotion-grade because the universe and diagnostic exist
after cohort discovery.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.evaluate_truth_layer_controlled_hypotheses import (
    DEFAULT_SPEC_PATH,
    _as_float,
    _population_inclusion,
    _row_cohort_key,
    _row_year,
    find_latest_input,
    iter_jsonl,
    load_hypothesis_spec,
)


SCHEMA_VERSION = "truth_layer_posthoc_pbo_v1"
DEFAULT_OUTPUT_ROOT = (
    "data/external/validation/calendar_macro_bundle_v1/historical_opportunities/"
    "truth_layer/posthoc_pbo"
)
DEFAULT_REPORT_PATH = (
    "research/phase_3_external_feed_validation/"
    "TRUTH_LAYER_POSTHOC_PBO_DIAGNOSTIC_2026-05-01.md"
)
RESOLVED_OUTCOMES = {"TP", "SL", "TIMEOUT"}


def analyze_posthoc_pbo(
    *,
    input_path: str | Path,
    spec_path: str | Path = DEFAULT_SPEC_PATH,
    min_total_resolved_n: int = 150,
    min_valid_year_folds: int = 3,
    min_year_resolved_n: int = 30,
    max_rows: int | None = None,
) -> dict[str, Any]:
    spec = load_hypothesis_spec(spec_path)
    population = spec.get("default_population") or {}
    primary_keys = [str(item.get("cohort_key")) for item in spec.get("hypotheses") or []]

    states: dict[str, dict[str, Any]] = defaultdict(_new_state)
    periods: set[str] = set()
    rows_scanned = 0
    ai_attempted_rows = 0
    ai_call_count_sum = 0

    for rows_scanned, row in enumerate(iter_jsonl(input_path), start=1):
        if row.get("ai_call_attempted"):
            ai_attempted_rows += 1
        ai_call_count_sum += int(row.get("ai_call_count") or 0)
        included, _ = _population_inclusion(row, population)
        if included:
            key = _row_cohort_key(row)
            states[key]["population_rows"] += 1
            states[key]["years"][_row_year(row)]["population_rows"] += 1
            period = _row_month(row)
            periods.add(period)
            states[key]["periods"][period]["population_rows"] += 1
            if str(row.get("truth_outcome") or "") in RESOLVED_OUTCOMES:
                realized = _as_float(row.get("truth_realized_r"))
                if realized is not None:
                    _add_resolved(states[key], row, realized, period)
        if max_rows is not None and rows_scanned >= max_rows:
            break

    all_periods = sorted(periods)
    candidate_rows = [
        _cohort_summary(
            key,
            state,
            min_year_resolved_n=min_year_resolved_n,
            all_periods=all_periods,
        )
        for key, state in states.items()
    ]
    eligible = [
        row
        for row in candidate_rows
        if int(row["resolved_r_n"]) >= min_total_resolved_n
        and int(row["valid_year_folds"]) >= min_valid_year_folds
    ]
    eligible = sorted(eligible, key=lambda row: row["cohort_key"])
    matrix = _build_period_matrix(eligible, states, all_periods)
    pbo, pbo_diag = cscv_pbo(matrix)
    primary_rows = _primary_rows(candidate_rows, eligible, primary_keys)

    return {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": _utc_now().isoformat(),
        "input_jsonl": str(Path(input_path)),
        "spec_path": str(Path(spec_path)),
        "promotion_verdict_allowed": False,
        "promotion_verdict": "NOT_ALLOWED_POSTHOC_DIAGNOSTIC_ONLY",
        "rows_scanned": rows_scanned,
        "ai_attempted_rows": ai_attempted_rows,
        "ai_call_count_sum": ai_call_count_sum,
        "assumptions": {
            "selection_status": "posthoc_after_same_dataset_cohort_discovery",
            "population_scope": population.get("scope_name"),
            "candidate_unit": "symbol|session|truth_regime",
            "periodization": "calendar_month",
            "period_performance_metric": "sum_truth_realized_r_on_resolved_rows",
            "missing_period_policy": "zero_return_no_resolved_trade",
            "eligibility": {
                "min_total_resolved_n": min_total_resolved_n,
                "min_valid_year_folds": min_valid_year_folds,
                "min_year_resolved_n": min_year_resolved_n,
            },
            "selection_metric_mismatch": (
                "Original primary cohorts were selected by diagnostics/stability, not by this "
                "monthly-sum-R PBO metric. Treat this as selection-risk evidence only."
            ),
        },
        "period_count": len(all_periods),
        "candidate_universe_n": len(candidate_rows),
        "eligible_universe_n": len(eligible),
        "candidate_universe": sorted(candidate_rows, key=lambda row: row["cohort_key"]),
        "eligible_candidates": eligible,
        "pbo": pbo,
        "pbo_diagnostics": pbo_diag,
        "pbo_promotion_usable": False,
        "pbo_promotion_usable_reason": "Universe and metric were frozen after cohort discovery.",
        "primary_cohorts": primary_rows,
        "top_eligible_by_total_sum_r": sorted(
            eligible,
            key=lambda row: float(row.get("sum_r") or 0.0),
            reverse=True,
        )[:20],
        "top_eligible_by_mean_r": sorted(
            eligible,
            key=lambda row: float(row.get("mean_r") or 0.0),
            reverse=True,
        )[:20],
    }


def cscv_pbo(matrix: Sequence[Sequence[float]]) -> tuple[float | None, dict[str, Any]]:
    """CSCV PBO over T periods x N strategies.

    The splitter uses balanced contiguous subperiods and assigns every period
    exactly once. This avoids silent tail-period loss when the period count is
    not divisible by the chosen subperiod count.
    """
    if not matrix:
        return None, {"status": "BLOCKED_EMPTY_MATRIX"}
    t_count = len(matrix)
    n_strategies = len(matrix[0]) if t_count else 0
    if t_count < 4 or n_strategies < 2:
        return None, {
            "status": "BLOCKED_INSUFFICIENT_PERIODS_OR_STRATEGIES",
            "period_count": t_count,
            "strategy_count": n_strategies,
        }
    s = _choose_subperiod_count(t_count)
    if s < 4:
        return None, {
            "status": "BLOCKED_CANNOT_FORM_CSCV_SUBPERIODS",
            "period_count": t_count,
            "strategy_count": n_strategies,
        }
    subperiods = _balanced_subperiods(t_count, s)
    half = s // 2
    logits: list[float] = []
    records: list[dict[str, Any]] = []
    combos = list(combinations(range(s), half))
    for combo in combos:
        is_rows = [row_idx for sub_idx in combo for row_idx in subperiods[sub_idx]]
        oos_rows = [
            row_idx
            for sub_idx in range(s)
            if sub_idx not in combo
            for row_idx in subperiods[sub_idx]
        ]
        is_perf = [_mean([matrix[row_idx][col] for row_idx in is_rows]) for col in range(n_strategies)]
        oos_perf = [_mean([matrix[row_idx][col] for row_idx in oos_rows]) for col in range(n_strategies)]
        best_is = max(range(n_strategies), key=lambda col: is_perf[col])
        sorted_oos = sorted(range(n_strategies), key=lambda col: oos_perf[col])
        oos_rank = sorted_oos.index(best_is) + 1
        denominator = max(1, n_strategies + 1 - oos_rank)
        logit = math.log(max(oos_rank, 1) / denominator)
        logits.append(logit)
        records.append(
            {
                "is_subperiods": list(combo),
                "is_best_strategy_index": best_is,
                "is_best_oos_rank": oos_rank,
                "below_median": logit < 0,
            }
        )
    pbo = sum(1 for value in logits if value < 0) / len(logits) if logits else None
    return pbo, {
        "status": "COMPUTED_POSTHOC_DIAGNOSTIC_ONLY",
        "period_count": t_count,
        "strategy_count": n_strategies,
        "subperiod_count": s,
        "subperiod_policy": "balanced_contiguous_all_periods",
        "subperiod_sizes": [len(rows) for rows in subperiods],
        "periods_used": sum(len(rows) for rows in subperiods),
        "combination_count": len(combos),
        "logit_min": min(logits) if logits else None,
        "logit_max": max(logits) if logits else None,
        "logit_mean": _mean(logits) if logits else None,
        "sample_records": records[:20],
    }


def render_report(summary: Mapping[str, Any]) -> str:
    lines = [
        "# Phase 3 Truth-Layer Post-Hoc PBO Diagnostic",
        "",
        f"**Created UTC:** {summary.get('created_at_utc')}",
        f"**Input:** `{summary.get('input_jsonl')}`",
        f"**Spec:** `{summary.get('spec_path')}`",
        f"**Promotion verdict:** `{summary.get('promotion_verdict')}`",
        "",
        "## Boundary",
        "",
        "- Research/tooling only; no live trading logic, prompt, config, risk policy, or execution behavior is changed.",
        "- This is a post-hoc selection-risk diagnostic. It is not promotion-grade PBO.",
        "- The original cohorts were selected by diagnostics/stability before this PBO universe was frozen.",
        "- A future promotion-grade PBO needs a pre-registered universe and untouched/prospective data.",
        "",
        "## Assumptions",
        "",
        _markdown_table([summary.get("assumptions") or {}]),
        "",
        "## PBO Result",
        "",
        _markdown_table([
            {
                "period_count": summary.get("period_count"),
                "candidate_universe_n": summary.get("candidate_universe_n"),
                "eligible_universe_n": summary.get("eligible_universe_n"),
                "pbo": summary.get("pbo"),
                "pbo_status": (summary.get("pbo_diagnostics") or {}).get("status"),
                "promotion_usable": summary.get("pbo_promotion_usable"),
                "promotion_usable_reason": summary.get("pbo_promotion_usable_reason"),
            }
        ]),
        "",
        "## Primary Cohorts",
        "",
        _markdown_table(summary.get("primary_cohorts") or []),
        "",
        "## Top Eligible By Total Sum R",
        "",
        _markdown_table(summary.get("top_eligible_by_total_sum_r") or []),
        "",
        "## Top Eligible By Mean R",
        "",
        _markdown_table(summary.get("top_eligible_by_mean_r") or []),
        "",
        "## Synthesis",
        "",
        "- This report quantifies selection-risk pressure over a transparent post-hoc universe.",
        "- It cannot rescue same-dataset evidence into a promotion claim.",
        "- If the PBO diagnostic is weak, the next step is still prospective validation; if it is strong, it only prioritizes the frozen cohorts.",
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
    stamp = _utc_now().strftime("%Y%m%dT%H%M%SZ")
    summary_path = output_dir / f"truth_layer_posthoc_pbo_{stamp}.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    report = Path(report_path)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(summary), encoding="utf-8")
    return summary_path, report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="Truth-layer JSONL. Defaults to latest truth-layer artifact.")
    parser.add_argument("--spec-path", default=DEFAULT_SPEC_PATH)
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--report-path", default=DEFAULT_REPORT_PATH)
    parser.add_argument("--min-total-resolved-n", type=int, default=150)
    parser.add_argument("--min-valid-year-folds", type=int, default=3)
    parser.add_argument("--min-year-resolved-n", type=int, default=30)
    parser.add_argument("--max-rows", type=int)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    input_path = Path(args.input) if args.input else find_latest_input()
    summary = analyze_posthoc_pbo(
        input_path=input_path,
        spec_path=args.spec_path,
        min_total_resolved_n=args.min_total_resolved_n,
        min_valid_year_folds=args.min_valid_year_folds,
        min_year_resolved_n=args.min_year_resolved_n,
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
                    "eligible_universe_n": summary.get("eligible_universe_n"),
                    "pbo": summary.get("pbo"),
                    "pbo_status": (summary.get("pbo_diagnostics") or {}).get("status"),
                    "primary_cohorts": summary.get("primary_cohorts"),
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


def _new_state() -> dict[str, Any]:
    return {
        "population_rows": 0,
        "resolved_r_n": 0,
        "sum_r": 0.0,
        "wins": 0,
        "outcomes": Counter(),
        "years": defaultdict(_new_year),
        "periods": defaultdict(_new_period),
    }


def _new_year() -> dict[str, Any]:
    return {
        "population_rows": 0,
        "resolved_r_n": 0,
        "sum_r": 0.0,
        "wins": 0,
        "outcomes": Counter(),
    }


def _new_period() -> dict[str, Any]:
    return {
        "population_rows": 0,
        "resolved_r_n": 0,
        "sum_r": 0.0,
        "wins": 0,
        "outcomes": Counter(),
    }


def _add_resolved(state: dict[str, Any], row: Mapping[str, Any], realized: float, period: str) -> None:
    outcome = str(row.get("truth_outcome") or "")
    state["resolved_r_n"] += 1
    state["sum_r"] += realized
    state["wins"] += 1 if realized > 0 else 0
    state["outcomes"][outcome] += 1
    year_state = state["years"][_row_year(row)]
    year_state["resolved_r_n"] += 1
    year_state["sum_r"] += realized
    year_state["wins"] += 1 if realized > 0 else 0
    year_state["outcomes"][outcome] += 1
    period_state = state["periods"][period]
    period_state["resolved_r_n"] += 1
    period_state["sum_r"] += realized
    period_state["wins"] += 1 if realized > 0 else 0
    period_state["outcomes"][outcome] += 1


def _cohort_summary(
    key: str,
    state: Mapping[str, Any],
    *,
    min_year_resolved_n: int,
    all_periods: Sequence[str],
) -> dict[str, Any]:
    total_n = int(state.get("resolved_r_n") or 0)
    valid_years = [
        year
        for year, year_state in (state.get("years") or {}).items()
        if int(year_state.get("resolved_r_n") or 0) >= min_year_resolved_n
    ]
    positive_valid_years = [
        year
        for year in valid_years
        if float((state.get("years") or {})[year].get("sum_r") or 0.0)
        / max(1, int((state.get("years") or {})[year].get("resolved_r_n") or 0))
        > 0
    ]
    max_year_share = 0.0
    if total_n and valid_years:
        max_year_share = max(
            int((state.get("years") or {})[year].get("resolved_r_n") or 0)
            for year in valid_years
        ) / total_n
    active_periods = [
        period
        for period in all_periods
        if int((state.get("periods") or {}).get(period, {}).get("resolved_r_n") or 0) > 0
    ]
    sum_r = float(state.get("sum_r") or 0.0)
    return {
        "cohort_key": key,
        "population_rows": int(state.get("population_rows") or 0),
        "resolved_r_n": total_n,
        "sum_r": round(sum_r, 6),
        "mean_r": round(sum_r / total_n, 6) if total_n else None,
        "win_rate": round(float(state.get("wins") or 0) / total_n, 6) if total_n else 0.0,
        "valid_year_folds": len(valid_years),
        "positive_valid_year_folds": len(positive_valid_years),
        "max_year_resolved_share": round(max_year_share, 6),
        "active_periods": len(active_periods),
    }


def _build_period_matrix(
    eligible: Sequence[Mapping[str, Any]],
    states: Mapping[str, Mapping[str, Any]],
    all_periods: Sequence[str],
) -> list[list[float]]:
    matrix: list[list[float]] = []
    for period in all_periods:
        row: list[float] = []
        for cohort in eligible:
            state = states[str(cohort["cohort_key"])]
            period_state = (state.get("periods") or {}).get(period) or {}
            row.append(float(period_state.get("sum_r") or 0.0))
        matrix.append(row)
    return matrix


def _primary_rows(
    candidate_rows: Sequence[Mapping[str, Any]],
    eligible: Sequence[Mapping[str, Any]],
    primary_keys: Sequence[str],
) -> list[dict[str, Any]]:
    all_by_key = {row["cohort_key"]: row for row in candidate_rows}
    eligible_keys = {row["cohort_key"] for row in eligible}
    rank_sum = {
        row["cohort_key"]: idx + 1
        for idx, row in enumerate(sorted(eligible, key=lambda r: float(r.get("sum_r") or 0.0), reverse=True))
    }
    rank_mean = {
        row["cohort_key"]: idx + 1
        for idx, row in enumerate(sorted(eligible, key=lambda r: float(r.get("mean_r") or 0.0), reverse=True))
    }
    rows = []
    for key in primary_keys:
        row = dict(all_by_key.get(key) or {"cohort_key": key})
        row["eligible_for_posthoc_pbo_universe"] = key in eligible_keys
        row["rank_by_total_sum_r"] = rank_sum.get(key)
        row["rank_by_mean_r"] = rank_mean.get(key)
        rows.append(row)
    return rows


def _row_month(row: Mapping[str, Any]) -> str:
    stamp = str(row.get("candle_close_utc") or "")
    if len(stamp) >= 7 and stamp[4] == "-":
        return stamp[:7]
    year = _row_year(row)
    return f"{year}-01"


def _mean(values: Sequence[float]) -> float:
    return float(sum(values) / len(values)) if values else 0.0


def _choose_subperiod_count(period_count: int) -> int:
    """Choose an even CSCV subperiod count with at least two periods per fold."""
    upper = min(14, period_count)
    if upper % 2:
        upper -= 1
    for candidate in range(upper, 2, -2):
        if period_count // candidate >= 2:
            return candidate
    return 0


def _balanced_subperiods(period_count: int, subperiod_count: int) -> list[list[int]]:
    base_size, remainder = divmod(period_count, subperiod_count)
    subperiods: list[list[int]] = []
    cursor = 0
    for index in range(subperiod_count):
        size = base_size + (1 if index < remainder else 0)
        subperiods.append(list(range(cursor, cursor + size)))
        cursor += size
    return subperiods


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _markdown_table(rows: Sequence[Mapping[str, Any]]) -> str:
    if not rows:
        return "_No rows._"
    preferred = (
        "cohort_key",
        "period_count",
        "candidate_universe_n",
        "eligible_universe_n",
        "pbo",
        "pbo_status",
        "promotion_usable",
        "promotion_usable_reason",
        "eligible_for_posthoc_pbo_universe",
        "rank_by_total_sum_r",
        "rank_by_mean_r",
        "population_rows",
        "resolved_r_n",
        "sum_r",
        "mean_r",
        "win_rate",
        "valid_year_folds",
        "positive_valid_year_folds",
        "max_year_resolved_share",
        "active_periods",
        "selection_status",
        "population_scope",
        "candidate_unit",
        "periodization",
        "period_performance_metric",
        "missing_period_policy",
        "selection_metric_mismatch",
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
    if isinstance(value, dict):
        value = json.dumps(value, sort_keys=True)
    if isinstance(value, list):
        value = "; ".join(str(item) for item in value)
    return str(value).replace("\n", " ").replace("|", "\\|")


if __name__ == "__main__":
    raise SystemExit(main())
