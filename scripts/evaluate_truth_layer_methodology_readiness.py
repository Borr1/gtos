#!/usr/bin/env python3
"""Assess methodology-gate readiness for controlled truth-layer hypotheses.

This is a research-only guardrail layer above
``evaluate_truth_layer_controlled_hypotheses.py``. It computes only metrics that
can be computed honestly from the locked truth-layer population and marks the
remaining promotion gates as blocked when required inputs are absent.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.evaluate_truth_layer_controlled_hypotheses import (
    DEFAULT_SPEC_PATH,
    _as_float,
    _population_inclusion,
    _row_cohort_key,
    _row_year,
    evaluate_controlled_hypotheses,
    find_latest_input,
    iter_jsonl,
    load_hypothesis_spec,
)


SCHEMA_VERSION = "truth_layer_methodology_readiness_v1"
DEFAULT_OUTPUT_ROOT = (
    "data/external/validation/calendar_macro_bundle_v1/historical_opportunities/"
    "truth_layer/methodology_readiness"
)
DEFAULT_REPORT_PATH = (
    "research/phase_3_external_feed_validation/"
    "TRUTH_LAYER_METHODOLOGY_GATE_READINESS_2026-05-01.md"
)
MATRIX_EFFECTIVE_N_DIAGNOSTIC_PATH = (
    "research/phase_3_external_feed_validation/"
    "TRUTH_LAYER_EFFECTIVE_N_DIAGNOSTIC_2026-05-01.md"
)
RESOLVED_OUTCOMES = {"TP", "SL", "TIMEOUT"}
EULER_MASCHERONI = 0.5772156649015329


def expected_max_sharpe(n_trials: int) -> float:
    if n_trials <= 1:
        return 0.0
    value = math.sqrt(2.0 * math.log(n_trials))
    return value - EULER_MASCHERONI / value if value > 0 else 0.0


def dsr_p_value(
    *,
    sharpe_observed: float,
    n_observations: int,
    n_trials: int,
    skewness: float,
    kurtosis: float,
) -> tuple[float, float, float, float]:
    """Return one-sided DSR p, probability of skill, sigma_SR, and expected max SR."""
    if n_observations <= 1:
        return 1.0, 0.0, float("nan"), float("nan")
    variance_inner = (
        1.0
        - skewness * sharpe_observed
        + (kurtosis - 1.0) / 4.0 * sharpe_observed * sharpe_observed
    )
    variance_inner = max(variance_inner, 1e-12)
    sigma_sr = math.sqrt(variance_inner / (n_observations - 1))
    if sigma_sr <= 0 or not math.isfinite(sigma_sr):
        return 1.0, 0.0, sigma_sr, float("nan")
    expected_max_z = expected_max_sharpe(n_trials)
    expected_max_sr = sigma_sr * expected_max_z
    z_score = (sharpe_observed - expected_max_sr) / sigma_sr
    probability_skill = _normal_cdf(z_score)
    return 1.0 - probability_skill, probability_skill, sigma_sr, expected_max_sr


def evaluate_methodology_readiness(
    *,
    input_path: str | Path,
    spec_path: str | Path = DEFAULT_SPEC_PATH,
    n_trials: int | None = None,
    max_rows: int | None = None,
) -> dict[str, Any]:
    spec = load_hypothesis_spec(spec_path)
    controlled = evaluate_controlled_hypotheses(
        input_path=input_path,
        spec_path=spec_path,
        max_rows=max_rows,
    )
    trial_cfg = ((spec.get("methodology_gates") or {}).get("required_for_any_promotion_claim") or {})
    n_trials = int(n_trials or trial_cfg.get("cumulative_program_trial_count_floor") or 200)
    resolved_by_hypothesis = _collect_resolved_returns(
        input_path=input_path,
        spec=spec,
        max_rows=max_rows,
    )

    gate_rows = []
    for hypothesis in controlled.get("hypotheses") or []:
        hypothesis_id = str(hypothesis.get("hypothesis_id"))
        returns = resolved_by_hypothesis.get(hypothesis_id, [])
        dsr = compute_dsr_diagnostic(returns, n_trials=n_trials)
        preconditions = hypothesis.get("preconditions") or {}
        gate_rows.append(
            {
                "hypothesis_id": hypothesis_id,
                "cohort_key": hypothesis.get("cohort_key"),
                "role": hypothesis.get("role"),
                "same_dataset_dsr": dsr,
                "fold_proxy": {
                    "valid_year_folds": preconditions.get("valid_year_folds"),
                    "positive_valid_year_folds": preconditions.get("positive_valid_year_folds"),
                    "max_year_resolved_share": preconditions.get("max_year_resolved_share"),
                    "proxy_effective_n_note": (
                        "Calendar-year fold count is a stability proxy only; it is not true "
                        "ONC/CPCV effective_N."
                    ),
                },
                "promotion_gate_status": "BLOCKED",
                "promotion_blockers": [
                    "same_dataset_post_diagnostic_selection",
                    "pbo_not_computable_without_preselection_strategy_matrix",
                    "true_effective_n_not_computed",
                    "no_untouched_holdout_or_prospective_confirmation",
                ],
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": _utc_now().isoformat(),
        "input_jsonl": str(Path(input_path)),
        "spec_path": str(Path(spec_path)),
        "controlled_report_verdict": controlled.get("verdict"),
        "promotion_verdict": "BLOCKED",
        "promotion_verdict_allowed": False,
        "trial_budget_n_used_for_dsr_diagnostic": n_trials,
        "expected_max_sharpe_at_n_trials": expected_max_sharpe(n_trials),
        "methodology_gate_matrix": {
            "same_dataset_dsr_diagnostic": "COMPUTED_DIAGNOSTIC_ONLY",
            "pbo": "BLOCKED_NOT_COMPUTABLE_FROM_PRIMARY_TWO_ONLY",
            "true_effective_n": "BLOCKED_HISTORICAL_MATRIX_DIAGNOSTIC_ONLY",
            "untouched_holdout": "ABSENT",
            "prospective_validation": "ABSENT",
        },
        "pbo_blocker": pbo_blocker(),
        "effective_n_blocker": effective_n_blocker(),
        "hypotheses": gate_rows,
        "next_actions": next_actions(),
    }


def compute_dsr_diagnostic(returns: Sequence[float], *, n_trials: int) -> dict[str, Any]:
    values = [float(value) for value in returns if math.isfinite(float(value))]
    n = len(values)
    if n < 2:
        return {
            "status": "INSUFFICIENT_RESOLVED_RETURNS",
            "n": n,
            "promotion_usable": False,
        }
    mean_r = sum(values) / n
    variance = sum((value - mean_r) ** 2 for value in values) / (n - 1)
    std_r = math.sqrt(max(variance, 0.0))
    if std_r <= 0:
        return {
            "status": "ZERO_VARIANCE_RETURNS",
            "n": n,
            "mean_r": round(mean_r, 6),
            "promotion_usable": False,
        }
    sharpe = mean_r / std_r
    skewness, kurtosis = _moments(values, mean_r, std_r)
    dsr_p, probability_skill, sigma_sr, expected_max_sr = dsr_p_value(
        sharpe_observed=sharpe,
        n_observations=n,
        n_trials=n_trials,
        skewness=skewness,
        kurtosis=kurtosis,
    )
    return {
        "status": "COMPUTED_SAME_DATASET_DIAGNOSTIC_ONLY",
        "n": n,
        "mean_r": round(mean_r, 6),
        "std_r": round(std_r, 6),
        "sharpe_observed": round(sharpe, 6),
        "skewness": round(skewness, 6),
        "kurtosis": round(kurtosis, 6),
        "n_trials": n_trials,
        "expected_max_sr": round(expected_max_sr, 6),
        "sigma_sr": round(sigma_sr, 6),
        "dsr_corrected_p": round(dsr_p, 12),
        "probability_skill": round(probability_skill, 12),
        "threshold_p_lt_0_01_met": dsr_p < 0.01,
        "promotion_usable": False,
        "promotion_usable_reason": (
            "DSR is computed on the same dataset that selected the cohorts; use as "
            "a diagnostic only."
        ),
    }


def pbo_blocker() -> dict[str, Any]:
    return {
        "status": "BLOCKED_NOT_COMPUTABLE_HONESTLY_FROM_CURRENT_PRIMARY_TWO_ONLY",
        "reason": (
            "PBO estimates overfit risk from selecting a best strategy or hyperparameter "
            "from a candidate matrix. The current artifact has two already-selected "
            "primary cohorts and an explicit rule to report both, so there is no valid "
            "IS-best/OOS-rank selection matrix."
        ),
        "minimum_inputs_for_posthoc_diagnostic": [
            "Full pre-selection cohort universe, not only the two selected primary cohorts",
            "Frozen selection metric used to choose cohorts",
            "Periodized performance matrix with a documented missing-period policy",
            "At least two candidate strategies and enough periods for CSCV splits",
            "Explicit label that any result is post-hoc and not promotion-grade",
        ],
        "minimum_inputs_for_promotion_grade_pbo": [
            "Selection universe and metric frozen before evaluation",
            "Untouched holdout or prospective period not used for cohort discovery",
            "CSCV/PBO run on all candidates in the registered universe",
        ],
    }


def effective_n_blocker() -> dict[str, Any]:
    return {
        "status": "BLOCKED_HISTORICAL_MATRIX_DIAGNOSTIC_ONLY",
        "available_proxy": "calendar_year_valid_fold_count",
        "separate_matrix_diagnostic": MATRIX_EFFECTIVE_N_DIAGNOSTIC_PATH,
        "why_proxy_is_insufficient": (
            "Year-fold count shows temporal spread, but promotion-grade effective_N "
            "requires dependence-adjusted path or candidate-matrix returns. A separate "
            "historical matrix diagnostic now exists, but it is not promotion-usable "
            "because the matrix was frozen after historical discovery."
        ),
        "minimum_inputs": [
            "Registered validation path definitions",
            "Path-level return or score vectors for every registered candidate",
            "Correlation matrix across paths/candidates",
            "ONC or equivalent dependence-adjustment method",
        ],
    }


def next_actions() -> list[dict[str, str]]:
    return [
        {
            "rank": "1",
            "action": "Review post-hoc PBO diagnostic before any prospective spend",
            "purpose": "Quantify same-dataset selection pressure without treating it as promotion-grade PBO.",
        },
        {
            "rank": "2",
            "action": "Use prospective holdout plan for future rows",
            "purpose": "Create the first promotion-eligible validation surface.",
        },
        {
            "rank": "3",
            "action": "Add true effective_N infrastructure for Phase 3 candidate matrices",
            "purpose": "Replace year-fold proxy with correlation-adjusted path independence.",
        },
        {
            "rank": "4",
            "action": "Enrich actual realized-R records separately",
            "purpose": "Bridge mechanical truth-layer diagnostics to live architecture evidence.",
        },
    ]


def render_report(summary: Mapping[str, Any]) -> str:
    lines = [
        "# Phase 3 Truth-Layer Methodology Gate Readiness",
        "",
        f"**Created UTC:** {summary.get('created_at_utc')}",
        f"**Input:** `{summary.get('input_jsonl')}`",
        f"**Spec:** `{summary.get('spec_path')}`",
        f"**Promotion verdict:** `{summary.get('promotion_verdict')}`",
        "",
        "## Boundary",
        "",
        "- Research/tooling only; no live trading logic, prompt, config, risk policy, or execution behavior is changed.",
        "- Same-dataset DSR is computed as a diagnostic only.",
        "- PBO is not computable honestly from the two selected primary cohorts alone.",
        "- Historical matrix effective_N is available only as a separate diagnostic; prospective effective_N is still absent.",
        "- No alpha promotion or live improvement is authorized by this report.",
        "",
        "## Gate Matrix",
        "",
        _markdown_table([
            {
                "same_dataset_dsr_diagnostic": (summary.get("methodology_gate_matrix") or {}).get("same_dataset_dsr_diagnostic"),
                "pbo": (summary.get("methodology_gate_matrix") or {}).get("pbo"),
                "true_effective_n": (summary.get("methodology_gate_matrix") or {}).get("true_effective_n"),
                "untouched_holdout": (summary.get("methodology_gate_matrix") or {}).get("untouched_holdout"),
                "prospective_validation": (summary.get("methodology_gate_matrix") or {}).get("prospective_validation"),
            }
        ]),
        "",
        "## Same-Dataset DSR Diagnostics",
        "",
        _markdown_table(_dsr_rows(summary.get("hypotheses") or [])),
        "",
        "## Fold Proxy",
        "",
        _markdown_table(_fold_rows(summary.get("hypotheses") or [])),
        "",
        "## PBO Blocker",
        "",
        _markdown_table([summary.get("pbo_blocker") or {}]),
        "",
        "## Effective-N Blocker",
        "",
        _markdown_table([summary.get("effective_n_blocker") or {}]),
        "",
        "## Next Actions",
        "",
        _markdown_table(summary.get("next_actions") or []),
        "",
        "## Synthesis",
        "",
        "- The two primary cohorts remain controlled-research candidates, not deployable alpha.",
        "- The same-dataset DSR diagnostic is allowed to inform priority, but it cannot override the selection-bias boundary.",
        "- The next non-ambiguous work is future-row collection through the prospective holdout plan plus true effective_N infrastructure.",
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
    summary_path = output_dir / f"truth_layer_methodology_readiness_{stamp}.json"
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
    parser.add_argument("--n-trials", type=int)
    parser.add_argument("--max-rows", type=int)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    input_path = Path(args.input) if args.input else find_latest_input()
    summary = evaluate_methodology_readiness(
        input_path=input_path,
        spec_path=args.spec_path,
        n_trials=args.n_trials,
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
                    "gate_matrix": summary.get("methodology_gate_matrix"),
                    "hypotheses": _dsr_rows(summary.get("hypotheses") or []),
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


def _collect_resolved_returns(
    *,
    input_path: str | Path,
    spec: Mapping[str, Any],
    max_rows: int | None,
) -> dict[str, list[float]]:
    states = {
        str(hypothesis.get("hypothesis_id")): {
            "cohort_key": str(hypothesis.get("cohort_key")),
            "population": spec.get("default_population") or {},
            "returns": [],
        }
        for hypothesis in spec.get("hypotheses") or []
    }
    cohort_to_ids: dict[str, list[str]] = defaultdict(list)
    for hypothesis_id, state in states.items():
        cohort_to_ids[state["cohort_key"]].append(hypothesis_id)

    for row_number, row in enumerate(iter_jsonl(input_path), start=1):
        for hypothesis_id in cohort_to_ids.get(_row_cohort_key(row), []):
            state = states[hypothesis_id]
            included, _ = _population_inclusion(row, state["population"])
            if not included or str(row.get("truth_outcome") or "") not in RESOLVED_OUTCOMES:
                continue
            realized = _as_float(row.get("truth_realized_r"))
            if realized is not None:
                state["returns"].append(realized)
        if max_rows is not None and row_number >= max_rows:
            break
    return {hypothesis_id: state["returns"] for hypothesis_id, state in states.items()}


def _moments(values: Sequence[float], mean: float, std: float) -> tuple[float, float]:
    n = len(values)
    if n < 3 or std <= 0:
        return 0.0, 3.0
    centered = [(value - mean) / std for value in values]
    skewness = sum(value ** 3 for value in centered) / n
    kurtosis = sum(value ** 4 for value in centered) / n
    return skewness, max(kurtosis, 1.0)


def _normal_cdf(value: float) -> float:
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _dsr_rows(hypotheses: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for hypothesis in hypotheses:
        dsr = hypothesis.get("same_dataset_dsr") or {}
        rows.append(
            {
                "hypothesis_id": hypothesis.get("hypothesis_id"),
                "cohort_key": hypothesis.get("cohort_key"),
                "status": dsr.get("status"),
                "n": dsr.get("n"),
                "mean_r": dsr.get("mean_r"),
                "std_r": dsr.get("std_r"),
                "sharpe_observed": dsr.get("sharpe_observed"),
                "dsr_corrected_p": dsr.get("dsr_corrected_p"),
                "threshold_p_lt_0_01_met": dsr.get("threshold_p_lt_0_01_met"),
                "promotion_usable": dsr.get("promotion_usable"),
            }
        )
    return rows


def _fold_rows(hypotheses: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for hypothesis in hypotheses:
        fold = hypothesis.get("fold_proxy") or {}
        rows.append(
            {
                "hypothesis_id": hypothesis.get("hypothesis_id"),
                "cohort_key": hypothesis.get("cohort_key"),
                "valid_year_folds": fold.get("valid_year_folds"),
                "positive_valid_year_folds": fold.get("positive_valid_year_folds"),
                "max_year_resolved_share": fold.get("max_year_resolved_share"),
                "proxy_effective_n_note": fold.get("proxy_effective_n_note"),
            }
        )
    return rows


def _markdown_table(rows: Sequence[Mapping[str, Any]]) -> str:
    if not rows:
        return "_No rows._"
    preferred = (
        "rank",
        "action",
        "purpose",
        "hypothesis_id",
        "cohort_key",
        "status",
        "n",
        "mean_r",
        "std_r",
        "sharpe_observed",
        "dsr_corrected_p",
        "threshold_p_lt_0_01_met",
        "promotion_usable",
        "valid_year_folds",
        "positive_valid_year_folds",
        "max_year_resolved_share",
        "same_dataset_dsr_diagnostic",
        "pbo",
        "true_effective_n",
        "untouched_holdout",
        "prospective_validation",
        "reason",
        "available_proxy",
        "why_proxy_is_insufficient",
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
    if isinstance(value, list):
        value = "; ".join(str(item) for item in value)
    return str(value).replace("\n", " ").replace("|", "\\|")


if __name__ == "__main__":
    raise SystemExit(main())
