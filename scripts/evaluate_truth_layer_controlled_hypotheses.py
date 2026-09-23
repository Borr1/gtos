#!/usr/bin/env python3
"""Evaluate pre-registered Phase 3 truth-layer cohort hypotheses.

This is research-only tooling. It locks population accounting and fold
diagnostics for pre-registered truth-layer cohorts. It intentionally does not
compute DSR, PBO, or true effective_N, so it cannot emit a promotion verdict.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence


SCHEMA_VERSION = "truth_layer_controlled_hypothesis_evaluator_v1"
DEFAULT_SPEC_PATH = (
    "research/phase_3_external_feed_validation/"
    "TRUTH_LAYER_CONTROLLED_HYPOTHESES_V1.json"
)
DEFAULT_INPUT_GLOB = (
    "data/external/validation/calendar_macro_bundle_v1/historical_opportunities/"
    "truth_layer/*_truth_layer_v2_*.jsonl"
)
DEFAULT_OUTPUT_ROOT = (
    "data/external/validation/calendar_macro_bundle_v1/historical_opportunities/"
    "truth_layer/controlled_hypotheses"
)
DEFAULT_REPORT_PATH = (
    "research/phase_3_external_feed_validation/"
    "TRUTH_LAYER_CONTROLLED_HYPOTHESIS_REPORT_2026-05-01.md"
)
AMBIGUOUS_OUTCOMES = {"SAME_BAR", "LOWER_TF_GAPPY"}
DEFAULT_RESOLVED_OUTCOMES = {"TP", "SL", "TIMEOUT"}


@dataclass
class RunningStats:
    rows: int = 0
    resolved_r_n: int = 0
    resolved_r_sum: float = 0.0
    wins: int = 0
    outcomes: Counter[str] = field(default_factory=Counter)
    failure_buckets: Counter[str] = field(default_factory=Counter)
    gap_rows: int = 0
    gap_before_resolution: int = 0
    gap_after_resolution: int = 0
    gap_timing_unknown: int = 0
    immediate_stop: int = 0

    def add(self, row: Mapping[str, Any], *, resolved_outcomes: set[str]) -> None:
        self.rows += 1
        outcome = str(row.get("truth_outcome") or "UNKNOWN")
        failure = str(row.get("truth_failure_bucket") or "UNKNOWN")
        self.outcomes[outcome] += 1
        self.failure_buckets[failure] += 1
        if _has_lower_tf_gap(row):
            self.gap_rows += 1
            timing = _selected_gap_timing(row)
            if timing == "before_or_at_resolution":
                self.gap_before_resolution += 1
            elif timing == "after_resolution":
                self.gap_after_resolution += 1
            else:
                self.gap_timing_unknown += 1
        if failure == "FAIL_IMMEDIATE_STOP_AFTER_FILL":
            self.immediate_stop += 1

        realized = _as_float(row.get("truth_realized_r"))
        if realized is not None and outcome in resolved_outcomes:
            self.resolved_r_n += 1
            self.resolved_r_sum += realized
            if realized > 0:
                self.wins += 1

    def to_row(self, key_name: str, key: str) -> dict[str, Any]:
        sl_rows = self.outcomes.get("SL", 0)
        return {
            key_name: key,
            "population_rows": self.rows,
            "resolved_r_n": self.resolved_r_n,
            "sum_r": _round(self.resolved_r_sum),
            "mean_r": _mean(self.resolved_r_sum, self.resolved_r_n),
            "win_rate": _rate(self.wins, self.resolved_r_n),
            "tp": self.outcomes.get("TP", 0),
            "sl": sl_rows,
            "timeout": self.outcomes.get("TIMEOUT", 0),
            "no_entry": self.outcomes.get("NO_ENTRY", 0),
            "no_entry_rate_population": _rate(self.outcomes.get("NO_ENTRY", 0), self.rows),
            "same_bar": self.outcomes.get("SAME_BAR", 0),
            "lower_tf_gappy": self.outcomes.get("LOWER_TF_GAPPY", 0),
            "gap_rows": self.gap_rows,
            "gap_before_resolution": self.gap_before_resolution,
            "gap_after_resolution": self.gap_after_resolution,
            "gap_timing_unknown": self.gap_timing_unknown,
            "immediate_stop": self.immediate_stop,
            "immediate_stop_rate_sl": _rate(self.immediate_stop, sl_rows),
            "max_year_resolved_share": None,
        }


def load_hypothesis_spec(path: str | Path = DEFAULT_SPEC_PATH) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != "truth_layer_controlled_hypotheses_v1":
        raise ValueError(f"unsupported hypothesis schema: {payload.get('schema_version')!r}")
    if payload.get("promotion_verdict_allowed") is not False:
        raise ValueError("controlled truth-layer spec must set promotion_verdict_allowed=false")
    if not payload.get("hypotheses"):
        raise ValueError("controlled truth-layer spec has no hypotheses")
    return payload


def iter_jsonl(path: str | Path) -> Iterator[dict[str, Any]]:
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def find_latest_input(pattern: str = DEFAULT_INPUT_GLOB) -> Path:
    paths = [
        path
        for path in Path().glob(pattern)
        if path.is_file()
        and path.suffix == ".jsonl"
        and "_summary_" not in path.name
        and "_diagnostics_" not in path.name
    ]
    if not paths:
        raise FileNotFoundError(f"no truth-layer JSONL matches {pattern!r}")
    return max(paths, key=lambda path: path.stat().st_mtime)


def evaluate_controlled_hypotheses(
    *,
    input_path: str | Path,
    spec_path: str | Path = DEFAULT_SPEC_PATH,
    include_watchlist: bool = False,
    max_rows: int | None = None,
) -> dict[str, Any]:
    spec = load_hypothesis_spec(spec_path)
    hypotheses = list(spec.get("hypotheses") or [])
    if include_watchlist:
        hypotheses.extend(_watchlist_as_hypotheses(spec))

    default_population = spec.get("default_population") or {}
    states = {
        hypothesis["hypothesis_id"]: _new_state(hypothesis, default_population)
        for hypothesis in hypotheses
    }
    cohort_to_ids: dict[str, list[str]] = defaultdict(list)
    for hypothesis in hypotheses:
        cohort_to_ids[str(hypothesis["cohort_key"])].append(str(hypothesis["hypothesis_id"]))

    rows_scanned = 0
    keys_seen: set[str] = set()
    duplicate_keys = 0
    ai_attempted_rows = 0
    ai_call_count_sum = 0

    for rows_scanned, row in enumerate(iter_jsonl(input_path), start=1):
        key = str(row.get("opportunity_key") or "")
        if key:
            if key in keys_seen:
                duplicate_keys += 1
            keys_seen.add(key)
        if row.get("ai_call_attempted"):
            ai_attempted_rows += 1
        ai_call_count_sum += int(row.get("ai_call_count") or 0)

        for hypothesis_id in cohort_to_ids.get(_row_cohort_key(row), []):
            _add_row(states[hypothesis_id], row)

        if max_rows is not None and rows_scanned >= max_rows:
            break

    evaluated = [_summarize_state(state, spec) for state in states.values()]
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": _utc_now().isoformat(),
        "input_jsonl": str(Path(input_path)),
        "spec_path": str(Path(spec_path)),
        "registry_markdown": spec.get("registry_markdown"),
        "selection_status": spec.get("selection_status"),
        "promotion_verdict_allowed": False,
        "verdict": "NO_PROMOTION_VERDICT",
        "verdict_reason": "DSR, PBO, and true effective_N are not computed by this research-only evaluator.",
        "methodology_gates": {
            "dsr_corrected_p": "NOT_COMPUTED",
            "pbo": "NOT_COMPUTED",
            "effective_n": "NOT_COMPUTED",
        },
        "trial_budget_policy": spec.get("trial_budget_policy"),
        "rows_scanned": rows_scanned,
        "unique_keys": len(keys_seen),
        "duplicate_keys": duplicate_keys,
        "ai_attempted_rows": ai_attempted_rows,
        "ai_call_count_sum": ai_call_count_sum,
        "hypotheses": evaluated,
        "family_preconditions": _family_preconditions(evaluated, duplicate_keys, ai_attempted_rows, ai_call_count_sum),
    }


def render_report(summary: Mapping[str, Any]) -> str:
    hypotheses = list(summary.get("hypotheses") or [])
    lines = [
        "# Phase 3 Controlled Truth-Layer Hypothesis Report",
        "",
        f"**Created UTC:** {summary.get('created_at_utc')}",
        f"**Input:** `{summary.get('input_jsonl')}`",
        f"**Spec:** `{summary.get('spec_path')}`",
        f"**Verdict:** `{summary.get('verdict')}`",
        "",
        "## Boundary",
        "",
        "- Research/tooling only; no live trading logic, prompt, config, risk policy, or execution behavior is changed.",
        "- The cohorts were selected after same-dataset diagnostics, so this report is stability and invalidation evidence only.",
        "- DSR-corrected p, PBO, and true effective_N are not computed here.",
        "- This evaluator must not be used as alpha promotion proof.",
        "",
        "## Data Integrity",
        "",
        _markdown_table(
            [
                {
                    "rows_scanned": summary.get("rows_scanned"),
                    "unique_keys": summary.get("unique_keys"),
                    "duplicate_keys": summary.get("duplicate_keys"),
                    "ai_attempted_rows": summary.get("ai_attempted_rows"),
                    "ai_call_count_sum": summary.get("ai_call_count_sum"),
                    "promotion_verdict_allowed": summary.get("promotion_verdict_allowed"),
                    "verdict": summary.get("verdict"),
                }
            ]
        ),
        "",
        "## Family Preconditions",
        "",
        _markdown_table([summary.get("family_preconditions") or {}]),
        "",
        "## Hypothesis Summary",
        "",
        _markdown_table([_hypothesis_summary_row(item) for item in hypotheses]),
        "",
        "## Year Folds",
        "",
        _markdown_table(_year_rows(hypotheses)),
        "",
        "## Early vs Recent",
        "",
        _markdown_table(_period_rows(hypotheses)),
        "",
        "## Exclusions",
        "",
        _markdown_table(_exclusion_rows(hypotheses)),
        "",
        "## Synthesis",
        "",
        "- The locked populations can be audited with this report.",
        "- A positive diagnostic result here is not out-of-sample validation because selection already used this truth-layer dataset.",
        "- Promotion remains blocked until a separate evaluator computes DSR, PBO, effective_N, and validates on untouched future or prospective data.",
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
    summary_path = output_dir / f"truth_layer_controlled_hypotheses_{stamp}.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    rendered = render_report(summary)
    report = Path(report_path)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(rendered, encoding="utf-8")
    return summary_path, report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="Truth-layer JSONL. Defaults to latest truth-layer artifact.")
    parser.add_argument("--spec-path", default=DEFAULT_SPEC_PATH)
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--report-path", default=DEFAULT_REPORT_PATH)
    parser.add_argument("--include-watchlist", action="store_true")
    parser.add_argument("--max-rows", type=int)
    parser.add_argument("--write", action="store_true", help="Write JSON summary and markdown report.")
    parser.add_argument("--quiet", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    input_path = Path(args.input) if args.input else find_latest_input()
    summary = evaluate_controlled_hypotheses(
        input_path=input_path,
        spec_path=args.spec_path,
        include_watchlist=args.include_watchlist,
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
                    "verdict": summary.get("verdict"),
                    "rows_scanned": summary.get("rows_scanned"),
                    "hypotheses": [
                        _hypothesis_summary_row(item)
                        for item in (summary.get("hypotheses") or [])
                    ],
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


def _new_state(hypothesis: Mapping[str, Any], default_population: Mapping[str, Any]) -> dict[str, Any]:
    population = _population_for_hypothesis(hypothesis, default_population)
    return {
        "hypothesis": dict(hypothesis),
        "population": population,
        "matching_rows": 0,
        "matching_setup_rows": 0,
        "included": RunningStats(),
        "excluded": Counter(),
        "years": defaultdict(RunningStats),
        "periods": defaultdict(RunningStats),
    }


def _population_for_hypothesis(
    hypothesis: Mapping[str, Any],
    default_population: Mapping[str, Any],
) -> dict[str, Any]:
    population = dict(default_population)
    override = hypothesis.get("population") or {}
    if not override.get("inherit_default_population", False):
        population.update(override)
    return population


def _add_row(state: dict[str, Any], row: Mapping[str, Any]) -> None:
    state["matching_rows"] += 1
    if _is_setup_row(row):
        state["matching_setup_rows"] += 1
    included, reasons = _population_inclusion(row, state["population"])
    if not included:
        for reason in reasons:
            state["excluded"][reason] += 1
        return
    resolved_outcomes = set(state["population"].get("primary_resolved_outcomes") or DEFAULT_RESOLVED_OUTCOMES)
    state["included"].add(row, resolved_outcomes=resolved_outcomes)
    year = _row_year(row)
    period = _period_for_year(year)
    state["years"][year].add(row, resolved_outcomes=resolved_outcomes)
    state["periods"][period].add(row, resolved_outcomes=resolved_outcomes)


def _population_inclusion(row: Mapping[str, Any], population: Mapping[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if population.get("setup_only", True) and not _is_setup_row(row):
        reasons.append("not_setup_row")
    confidences = set(population.get("truth_confidences") or [])
    if confidences and str(row.get("truth_confidence") or "") not in confidences:
        reasons.append("truth_confidence_not_allowed")
    excluded_outcomes = set(population.get("exclude_truth_outcomes") or [])
    if str(row.get("truth_outcome") or "") in excluded_outcomes:
        reasons.append("truth_outcome_excluded")
    if population.get("require_resolution_safe", False) and not _is_resolution_safe(row):
        reasons.append("not_resolution_safe")
    return not reasons, reasons


def _summarize_state(state: Mapping[str, Any], spec: Mapping[str, Any]) -> dict[str, Any]:
    hypothesis = state["hypothesis"]
    included = state["included"].to_row("population", (state["population"] or {}).get("scope_name", "custom"))
    year_rows = [
        stats.to_row("year", year)
        for year, stats in sorted(state["years"].items(), key=lambda item: item[0])
    ]
    period_rows = [
        stats.to_row("period", period)
        for period, stats in sorted(state["periods"].items(), key=lambda item: item[0])
    ]
    split_plan = spec.get("split_plan") or {}
    preconditions = _hypothesis_preconditions(
        hypothesis,
        included,
        year_rows,
        min_year_resolved_n=int(split_plan.get("primary_valid_fold_min_resolved_n") or 30),
    )
    included["max_year_resolved_share"] = preconditions["max_year_resolved_share"]
    return {
        "hypothesis_id": hypothesis.get("hypothesis_id"),
        "cohort_key": hypothesis.get("cohort_key"),
        "role": hypothesis.get("role"),
        "selection_reason": hypothesis.get("selection_reason"),
        "population_rule": state["population"],
        "matching_rows": state["matching_rows"],
        "matching_setup_rows": state["matching_setup_rows"],
        "included": included,
        "excluded_counts": dict(sorted(state["excluded"].items())),
        "year_folds": year_rows,
        "period_splits": period_rows,
        "preconditions": preconditions,
        "promotion_verdict": "NOT_ALLOWED_SAME_DATASET_AND_DSR_PBO_EFFECTIVE_N_NOT_COMPUTED",
    }


def _hypothesis_preconditions(
    hypothesis: Mapping[str, Any],
    included: Mapping[str, Any],
    year_rows: Sequence[Mapping[str, Any]],
    *,
    min_year_resolved_n: int,
) -> dict[str, Any]:
    required = hypothesis.get("necessary_not_sufficient_research_preconditions") or {}
    min_total = int(required.get("min_total_resolved_n") or 150)
    min_valid_years = int(required.get("min_valid_year_folds") or 3)
    max_share_limit = float(required.get("max_single_year_resolved_share") or 0.45)
    total_n = int(included.get("resolved_r_n") or 0)
    valid_years = [
        row
        for row in year_rows
        if int(row.get("resolved_r_n") or 0) >= min_year_resolved_n
    ]
    positive_years = [
        row
        for row in valid_years
        if _as_float(row.get("mean_r")) is not None and float(row.get("mean_r") or 0.0) > 0
    ]
    max_share = 0.0
    if total_n and valid_years:
        max_share = max(int(row.get("resolved_r_n") or 0) for row in valid_years) / total_n
    return {
        "sample_floor_met": total_n >= min_total,
        "resolved_r_n": total_n,
        "valid_year_folds": len(valid_years),
        "min_valid_year_folds_met": len(valid_years) >= min_valid_years,
        "positive_valid_year_folds": len(positive_years),
        "all_valid_years_positive": len(valid_years) > 0 and len(positive_years) == len(valid_years),
        "max_year_resolved_share": round(max_share, 6),
        "single_year_dominance_ok": max_share <= max_share_limit if valid_years else False,
        "promotion_blocked_reason": "DSR_PBO_EFFECTIVE_N_NOT_COMPUTED_AND_SELECTION_IS_SAME_DATASET",
    }


def _family_preconditions(
    hypotheses: Sequence[Mapping[str, Any]],
    duplicate_keys: int,
    ai_attempted_rows: int,
    ai_call_count_sum: int,
) -> dict[str, Any]:
    child_flags = [item.get("preconditions") or {} for item in hypotheses if item.get("role") == "primary"]
    necessary_preconditions_met = bool(child_flags) and all(
        flags.get("sample_floor_met")
        and flags.get("min_valid_year_folds_met")
        and flags.get("all_valid_years_positive")
        and flags.get("single_year_dominance_ok")
        for flags in child_flags
    )
    data_integrity_ok = duplicate_keys == 0 and ai_attempted_rows == 0 and ai_call_count_sum == 0
    return {
        "data_integrity_ok": data_integrity_ok,
        "primary_child_count": len(child_flags),
        "necessary_research_preconditions_met": necessary_preconditions_met,
        "promotion_verdict_allowed": False,
        "promotion_blocked_reason": "DSR_PBO_EFFECTIVE_N_NOT_COMPUTED_AND_SAME_DATASET_SELECTION",
    }


def _watchlist_as_hypotheses(spec: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for index, item in enumerate(spec.get("watchlist_cohorts") or [], start=1):
        rows.append(
            {
                "hypothesis_id": f"WATCHLIST-{index:02d}",
                "cohort_key": item.get("cohort_key"),
                "role": "watchlist",
                "selection_reason": item.get("status"),
                "population": {"inherit_default_population": True},
                "necessary_not_sufficient_research_preconditions": {},
            }
        )
    return rows


def _hypothesis_summary_row(item: Mapping[str, Any]) -> dict[str, Any]:
    included = item.get("included") or {}
    preconditions = item.get("preconditions") or {}
    return {
        "hypothesis_id": item.get("hypothesis_id"),
        "cohort_key": item.get("cohort_key"),
        "role": item.get("role"),
        "matching_setup_rows": item.get("matching_setup_rows"),
        "population_rows": included.get("population_rows"),
        "resolved_r_n": included.get("resolved_r_n"),
        "mean_r": included.get("mean_r"),
        "win_rate": included.get("win_rate"),
        "no_entry": included.get("no_entry"),
        "no_entry_rate_population": included.get("no_entry_rate_population"),
        "valid_year_folds": preconditions.get("valid_year_folds"),
        "positive_valid_year_folds": preconditions.get("positive_valid_year_folds"),
        "max_year_resolved_share": preconditions.get("max_year_resolved_share"),
        "promotion_verdict": item.get("promotion_verdict"),
    }


def _year_rows(hypotheses: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in hypotheses:
        for year in item.get("year_folds") or []:
            row = {"hypothesis_id": item.get("hypothesis_id"), "cohort_key": item.get("cohort_key")}
            row.update(year)
            rows.append(row)
    return rows


def _period_rows(hypotheses: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in hypotheses:
        for period in item.get("period_splits") or []:
            row = {"hypothesis_id": item.get("hypothesis_id"), "cohort_key": item.get("cohort_key")}
            row.update(period)
            rows.append(row)
    return rows


def _exclusion_rows(hypotheses: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in hypotheses:
        counts = item.get("excluded_counts") or {}
        if not counts:
            rows.append(
                {
                    "hypothesis_id": item.get("hypothesis_id"),
                    "cohort_key": item.get("cohort_key"),
                    "reason": "none",
                    "rows": 0,
                }
            )
            continue
        for reason, count in counts.items():
            rows.append(
                {
                    "hypothesis_id": item.get("hypothesis_id"),
                    "cohort_key": item.get("cohort_key"),
                    "reason": reason,
                    "rows": count,
                }
            )
    return rows


def _row_cohort_key(row: Mapping[str, Any]) -> str:
    return f"{row.get('symbol') or 'unknown'}|{row.get('session') or 'unknown'}|{row.get('truth_regime') or 'none|none'}"


def _row_year(row: Mapping[str, Any]) -> str:
    year = row.get("year")
    if year not in (None, ""):
        return str(year)
    stamp = str(row.get("candle_close_utc") or "")
    return stamp[:4] if len(stamp) >= 4 and stamp[:4].isdigit() else "unknown"


def _period_for_year(year: str) -> str:
    if year in {"2022", "2023"}:
        return "2022_2023"
    if year in {"2024", "2025", "2026"}:
        return "2024_2026_partial"
    return "unknown"


def _is_setup_row(row: Mapping[str, Any]) -> bool:
    return bool(row.get("would_send_ai")) and row.get("mechanical_setup_status") == "OK"


def _is_resolution_safe(row: Mapping[str, Any]) -> bool:
    if str(row.get("truth_outcome") or "") in AMBIGUOUS_OUTCOMES:
        return False
    timing = _selected_gap_timing(row)
    return timing in {"none", "after_resolution"}


def _has_lower_tf_gap(row: Mapping[str, Any]) -> bool:
    return _selected_gap_count(row) > 0


def _selected_gap_count(row: Mapping[str, Any]) -> int:
    timeframe = str(row.get("truth_source_timeframe") or "").upper()
    if timeframe not in {"M1", "M5"}:
        return 0
    lower_tf_count = _as_int(row.get("lower_tf_gap_count_in_horizon"))
    if lower_tf_count is not None:
        return lower_tf_count
    count = _as_int(row.get(f"{timeframe.lower()}_gap_count_in_horizon"))
    return count or 0


def _selected_gap_timing(row: Mapping[str, Any]) -> str:
    if _selected_gap_count(row) <= 0:
        return "none"
    first_gap = _selected_first_gap_time(row)
    if first_gap is None:
        return "unknown"
    if str(row.get("truth_outcome") or "") == "NO_ENTRY":
        return "before_or_at_resolution"
    exit_time = _selected_exit_time(row)
    if exit_time is None:
        return "unknown"
    return "before_or_at_resolution" if first_gap <= exit_time else "after_resolution"


def _selected_first_gap_time(row: Mapping[str, Any]) -> datetime | None:
    timeframe = str(row.get("truth_source_timeframe") or "").upper()
    value = row.get("lower_tf_first_gap_utc")
    if value in (None, "") and timeframe in {"M1", "M5"}:
        value = row.get(f"{timeframe.lower()}_first_gap_utc")
    return _parse_datetime(value)


def _selected_exit_time(row: Mapping[str, Any]) -> datetime | None:
    timeframe = str(row.get("truth_source_timeframe") or "").upper()
    if timeframe in {"M1", "M5"}:
        return _parse_datetime(row.get(f"{timeframe.lower()}_refined_exit_time"))
    return None


def _as_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _parse_datetime(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    text = str(value).strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _rate(numer: int | float, denom: int | float) -> float:
    return round(float(numer) / float(denom), 6) if denom else 0.0


def _mean(total: float, count: int) -> float | None:
    return round(float(total) / count, 6) if count else None


def _round(value: float | None) -> float | None:
    return round(float(value), 6) if value is not None else None


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _markdown_table(rows: Sequence[Mapping[str, Any]]) -> str:
    if not rows:
        return "_No rows._"
    preferred = (
        "hypothesis_id",
        "cohort_key",
        "role",
        "rows_scanned",
        "unique_keys",
        "duplicate_keys",
        "ai_attempted_rows",
        "ai_call_count_sum",
        "promotion_verdict_allowed",
        "verdict",
        "data_integrity_ok",
        "primary_child_count",
        "necessary_research_preconditions_met",
        "promotion_blocked_reason",
        "matching_setup_rows",
        "population",
        "population_rows",
        "resolved_r_n",
        "sum_r",
        "mean_r",
        "win_rate",
        "tp",
        "sl",
        "timeout",
        "no_entry",
        "no_entry_rate_population",
        "same_bar",
        "lower_tf_gappy",
        "gap_rows",
        "gap_before_resolution",
        "gap_after_resolution",
        "immediate_stop",
        "immediate_stop_rate_sl",
        "valid_year_folds",
        "positive_valid_year_folds",
        "max_year_resolved_share",
        "promotion_verdict",
        "period",
        "year",
        "reason",
        "rows",
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
    return str(value).replace("\n", " ").replace("|", "\\|")


if __name__ == "__main__":
    raise SystemExit(main())
