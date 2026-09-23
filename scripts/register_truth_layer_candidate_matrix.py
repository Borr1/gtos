#!/usr/bin/env python3
"""Register the Phase 3 truth-layer prospective candidate matrix.

The matrix keeps all eligible symbol/session/regime candidates in scope for
future prospective PBO/effective-N work. It is generated from historical
diagnostics, so the registry itself cannot promote alpha.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.analyze_truth_layer_posthoc_pbo import analyze_posthoc_pbo
from scripts.evaluate_truth_layer_controlled_hypotheses import (
    DEFAULT_SPEC_PATH,
    find_latest_input,
    load_hypothesis_spec,
)


SCHEMA_VERSION = "truth_layer_prospective_candidate_matrix_v1"
DEFAULT_MATRIX_PATH = (
    "research/phase_3_external_feed_validation/"
    "TRUTH_LAYER_PROSPECTIVE_CANDIDATE_MATRIX_V1.json"
)
DEFAULT_REPORT_PATH = (
    "research/phase_3_external_feed_validation/"
    "TRUTH_LAYER_PROSPECTIVE_CANDIDATE_MATRIX_2026-05-01.md"
)


def build_candidate_matrix_registry(
    *,
    input_path: str | Path,
    spec_path: str | Path = DEFAULT_SPEC_PATH,
    min_total_resolved_n: int = 150,
    min_valid_year_folds: int = 3,
    min_year_resolved_n: int = 30,
    max_rows: int | None = None,
) -> dict[str, Any]:
    spec = load_hypothesis_spec(spec_path)
    pbo = analyze_posthoc_pbo(
        input_path=input_path,
        spec_path=spec_path,
        min_total_resolved_n=min_total_resolved_n,
        min_valid_year_folds=min_valid_year_folds,
        min_year_resolved_n=min_year_resolved_n,
        max_rows=max_rows,
    )
    primary_keys = {str(item.get("cohort_key")) for item in spec.get("hypotheses") or []}
    watchlist_keys = {str(item.get("cohort_key")) for item in spec.get("watchlist_cohorts") or []}
    candidates = [
        _candidate_row(index, row, primary_keys=primary_keys, watchlist_keys=watchlist_keys)
        for index, row in enumerate(pbo.get("eligible_candidates") or [], start=1)
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "registered_future_prospective_matrix",
        "promotion_verdict_allowed": False,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "promotion_blocked_reason": (
            "Candidate universe was frozen after historical diagnostics; use for future "
            "prospective PBO/effective_N only."
        ),
        "controlled_hypothesis_spec": str(Path(spec_path)),
        "prospective_holdout_plan": spec.get("prospective_holdout_plan"),
        "prospective_cutoff_utc": spec.get("prospective_cutoff_utc"),
        "selection_source": {
            "truth_layer_jsonl": str(Path(input_path)),
            "truth_layer_sha256": sha256_file(input_path),
            "controlled_spec_sha256": sha256_file(spec_path),
        },
        "population": spec.get("default_population"),
        "candidate_unit": "symbol|session|truth_regime",
        "candidate_eligibility": {
            "min_total_resolved_n": min_total_resolved_n,
            "min_valid_year_folds": min_valid_year_folds,
            "min_year_resolved_n": min_year_resolved_n,
        },
        "periodization": "calendar_month",
        "period_performance_metric": "sum_truth_realized_r_on_resolved_rows",
        "missing_period_policy": "zero_return_no_resolved_trade",
        "candidate_count": len(candidates),
        "primary_candidate_count": sum(1 for row in candidates if row["role"] == "primary_controlled_child"),
        "watchlist_candidate_count": sum(1 for row in candidates if row["role"] == "watchlist_from_controlled_spec"),
        "historical_pbo_reference": {
            "status": "POSTHOC_DIAGNOSTIC_ONLY",
            "promotion_usable": False,
            "pbo": pbo.get("pbo"),
            "period_count": pbo.get("period_count"),
            "candidate_universe_n": pbo.get("candidate_universe_n"),
            "eligible_universe_n": pbo.get("eligible_universe_n"),
            "pbo_diagnostics": pbo.get("pbo_diagnostics"),
        },
        "future_use_rules": [
            "Every candidate in this registry must remain in the prospective PBO matrix.",
            "Primary child cohorts remain USDJPY|tokyo|bearish|D1 and GBPJPY|tokyo|bullish|D1.",
            "Selecting only the best future candidate after evaluation is exploratory.",
            "Prospective rows must have candle_close_utc after the registered cutoff.",
            "DSR, PBO, and effective_N must all pass before any promotion claim.",
        ],
        "candidates": candidates,
    }


def render_report(registry: Mapping[str, Any]) -> str:
    lines = [
        "# Phase 3 Truth-Layer Prospective Candidate Matrix",
        "",
        f"**Created UTC:** {registry.get('created_at_utc')}",
        f"**Status:** `{registry.get('status')}`",
        f"**Promotion verdict:** `{registry.get('promotion_verdict')}`",
        "",
        "## Boundary",
        "",
        "- Research/tooling only; no live trading logic, prompt, config, risk policy, or execution behavior is changed.",
        "- This freezes the broad candidate matrix before future prospective rows arrive.",
        "- The historical candidate universe was identified after diagnostics, so historical results remain post-hoc.",
        "- Future PBO/effective_N work must keep every registered candidate in the matrix.",
        "",
        "## Source And Rules",
        "",
        _markdown_table([
            {
                "truth_layer_jsonl": (registry.get("selection_source") or {}).get("truth_layer_jsonl"),
                "truth_layer_sha256": (registry.get("selection_source") or {}).get("truth_layer_sha256"),
                "prospective_cutoff_utc": registry.get("prospective_cutoff_utc"),
                "candidate_unit": registry.get("candidate_unit"),
                "candidate_count": registry.get("candidate_count"),
                "primary_candidate_count": registry.get("primary_candidate_count"),
                "watchlist_candidate_count": registry.get("watchlist_candidate_count"),
                "periodization": registry.get("periodization"),
                "missing_period_policy": registry.get("missing_period_policy"),
            }
        ]),
        "",
        "## Historical PBO Reference",
        "",
        _markdown_table([registry.get("historical_pbo_reference") or {}]),
        "",
        "## Primary Candidates",
        "",
        _markdown_table([row for row in registry.get("candidates", []) if row.get("role") == "primary_controlled_child"]),
        "",
        "## Registered Candidate Matrix",
        "",
        _markdown_table(registry.get("candidates") or []),
        "",
        "## Synthesis",
        "",
        "- The two JPY Tokyo cohorts remain the primary controlled family.",
        "- The wider instrument universe remains registered for prospective PBO/effective_N accounting.",
        "- This prevents accidental narrowing to only the historical winners.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def write_outputs(
    registry: Mapping[str, Any],
    *,
    matrix_path: str | Path = DEFAULT_MATRIX_PATH,
    report_path: str | Path = DEFAULT_REPORT_PATH,
) -> tuple[Path, Path]:
    matrix = Path(matrix_path)
    matrix.parent.mkdir(parents=True, exist_ok=True)
    matrix.write_text(json.dumps(registry, indent=2, sort_keys=True), encoding="utf-8")
    report = Path(report_path)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(registry), encoding="utf-8")
    return matrix, report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="Truth-layer JSONL. Defaults to latest truth-layer artifact.")
    parser.add_argument("--spec-path", default=DEFAULT_SPEC_PATH)
    parser.add_argument("--matrix-path", default=DEFAULT_MATRIX_PATH)
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
    registry = build_candidate_matrix_registry(
        input_path=input_path,
        spec_path=args.spec_path,
        min_total_resolved_n=args.min_total_resolved_n,
        min_valid_year_folds=args.min_valid_year_folds,
        min_year_resolved_n=args.min_year_resolved_n,
        max_rows=args.max_rows,
    )
    if args.write:
        matrix_path, report_path = write_outputs(
            registry,
            matrix_path=args.matrix_path,
            report_path=args.report_path,
        )
        registry = dict(registry)
        registry["matrix_path"] = str(matrix_path)
        registry["report_path"] = str(report_path)
    if args.quiet:
        print(
            json.dumps(
                {
                    "candidate_count": registry.get("candidate_count"),
                    "primary_candidate_count": registry.get("primary_candidate_count"),
                    "historical_pbo": (registry.get("historical_pbo_reference") or {}).get("pbo"),
                    "promotion_verdict": registry.get("promotion_verdict"),
                    "matrix_path": registry.get("matrix_path"),
                    "report_path": registry.get("report_path"),
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(json.dumps(registry, indent=2, sort_keys=True))
    return 0


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _candidate_row(
    index: int,
    row: Mapping[str, Any],
    *,
    primary_keys: set[str],
    watchlist_keys: set[str],
) -> dict[str, Any]:
    key = str(row.get("cohort_key"))
    if key in primary_keys:
        role = "primary_controlled_child"
    elif key in watchlist_keys:
        role = "watchlist_from_controlled_spec"
    else:
        role = "registered_matrix_candidate"
    return {
        "candidate_id": f"P3-TL-MATRIX-{index:03d}",
        "cohort_key": key,
        "role": role,
        "historical_population_rows": row.get("population_rows"),
        "historical_resolved_r_n": row.get("resolved_r_n"),
        "historical_sum_r": row.get("sum_r"),
        "historical_mean_r": row.get("mean_r"),
        "historical_win_rate": row.get("win_rate"),
        "historical_valid_year_folds": row.get("valid_year_folds"),
        "historical_positive_valid_year_folds": row.get("positive_valid_year_folds"),
        "historical_max_year_resolved_share": row.get("max_year_resolved_share"),
        "historical_active_periods": row.get("active_periods"),
    }


def _markdown_table(rows: Sequence[Mapping[str, Any]]) -> str:
    if not rows:
        return "_No rows._"
    preferred = (
        "candidate_id",
        "cohort_key",
        "role",
        "candidate_count",
        "primary_candidate_count",
        "watchlist_candidate_count",
        "prospective_cutoff_utc",
        "candidate_unit",
        "periodization",
        "missing_period_policy",
        "status",
        "promotion_usable",
        "pbo",
        "period_count",
        "candidate_universe_n",
        "eligible_universe_n",
        "historical_population_rows",
        "historical_resolved_r_n",
        "historical_sum_r",
        "historical_mean_r",
        "historical_win_rate",
        "historical_valid_year_folds",
        "historical_positive_valid_year_folds",
        "historical_max_year_resolved_share",
        "historical_active_periods",
        "truth_layer_jsonl",
        "truth_layer_sha256",
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
