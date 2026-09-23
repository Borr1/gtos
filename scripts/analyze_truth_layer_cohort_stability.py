#!/usr/bin/env python3
"""Evaluate post-diagnostic Phase 3 truth-layer cohort stability.

This is research-only follow-up over already-built truth-layer rows. It does
not rebuild labels, replay AI calls, tune entries, edit prompts, or change live
trading behavior. Cohorts selected from the first diagnostic report are treated
as same-dataset follow-up targets, not alpha-promotion evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence


SCHEMA_VERSION = "truth_layer_cohort_stability_v1"
DEFAULT_INPUT_GLOB = (
    "data/external/validation/calendar_macro_bundle_v1/historical_opportunities/"
    "truth_layer/*_truth_layer_v2_*.jsonl"
)
DEFAULT_COHORT_PATH = (
    "research/phase_3_external_feed_validation/TRUTH_LAYER_FOLLOWUP_COHORTS_V1.json"
)
DEFAULT_OUTPUT_ROOT = (
    "data/external/validation/calendar_macro_bundle_v1/historical_opportunities/"
    "truth_layer/diagnostics"
)
DEFAULT_REPORT_PATH = (
    "research/phase_3_external_feed_validation/"
    "TRUTH_LAYER_COHORT_STABILITY_2026-05-01.md"
)

RESOLVED_OUTCOMES = {"TP", "SL", "TIMEOUT"}
AMBIGUOUS_OUTCOMES = {"SAME_BAR", "LOWER_TF_GAPPY"}
SCOPE_DEFINITIONS = {
    "HIGH_ONLY": {
        "confidences": {"HIGH"},
        "exclude_ambiguous": False,
        "require_zero_gap": False,
        "require_resolution_safe": False,
    },
    "HIGH_MEDIUM": {
        "confidences": {"HIGH", "MEDIUM"},
        "exclude_ambiguous": False,
        "require_zero_gap": False,
        "require_resolution_safe": False,
    },
    "CLEAN_HIGH": {
        "confidences": {"HIGH"},
        "exclude_ambiguous": True,
        "require_zero_gap": False,
        "require_resolution_safe": False,
    },
    "CLEAN_HIGH_MEDIUM": {
        "confidences": {"HIGH", "MEDIUM"},
        "exclude_ambiguous": True,
        "require_zero_gap": False,
        "require_resolution_safe": False,
    },
    "RESOLUTION_SAFE_HIGH": {
        "confidences": {"HIGH"},
        "exclude_ambiguous": True,
        "require_zero_gap": False,
        "require_resolution_safe": True,
    },
    "RESOLUTION_SAFE_HIGH_MEDIUM": {
        "confidences": {"HIGH", "MEDIUM"},
        "exclude_ambiguous": True,
        "require_zero_gap": False,
        "require_resolution_safe": True,
    },
    "ZERO_GAP_HIGH": {
        "confidences": {"HIGH"},
        "exclude_ambiguous": True,
        "require_zero_gap": True,
        "require_resolution_safe": False,
    },
    "ZERO_GAP_HIGH_MEDIUM": {
        "confidences": {"HIGH", "MEDIUM"},
        "exclude_ambiguous": True,
        "require_zero_gap": True,
        "require_resolution_safe": False,
    },
}


@dataclass(frozen=True)
class CohortSpec:
    cohort_key: str
    symbol: str
    session: str
    regime: str
    role: str = "followup"
    selection_reason: str = ""
    key_questions: tuple[str, ...] = ()

    @classmethod
    def from_mapping(cls, item: Mapping[str, Any]) -> "CohortSpec":
        key = str(item.get("cohort_key") or "")
        symbol, session, regime = parse_cohort_key(key)
        questions = tuple(str(value) for value in item.get("key_questions") or ())
        return cls(
            cohort_key=key,
            symbol=symbol,
            session=session,
            regime=regime,
            role=str(item.get("role") or "followup"),
            selection_reason=str(item.get("selection_reason") or ""),
            key_questions=questions,
        )


@dataclass
class RunningStats:
    rows: int = 0
    setup_rows: int = 0
    resolved_r_n: int = 0
    resolved_r_sum: float = 0.0
    wins: int = 0
    outcomes: Counter[str] = field(default_factory=Counter)
    failure_buckets: Counter[str] = field(default_factory=Counter)
    confidences: Counter[str] = field(default_factory=Counter)
    source_timeframes: Counter[str] = field(default_factory=Counter)
    sides: Counter[str] = field(default_factory=Counter)
    gap_rows: int = 0
    gap_before_resolution: int = 0
    gap_after_resolution: int = 0
    gap_timing_unknown: int = 0
    immediate_stop: int = 0

    def add(self, row: Mapping[str, Any]) -> None:
        self.rows += 1
        if _is_setup_row(row):
            self.setup_rows += 1
        outcome = str(row.get("truth_outcome") or "UNKNOWN")
        failure = str(row.get("truth_failure_bucket") or "UNKNOWN")
        self.outcomes[outcome] += 1
        self.failure_buckets[failure] += 1
        self.confidences[str(row.get("truth_confidence") or "UNKNOWN")] += 1
        self.source_timeframes[str(row.get("truth_source_timeframe") or "UNKNOWN")] += 1
        self.sides[str(row.get("mechanical_side") or "UNKNOWN")] += 1
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
        if realized is not None and outcome in RESOLVED_OUTCOMES:
            self.resolved_r_n += 1
            self.resolved_r_sum += realized
            if realized > 0:
                self.wins += 1

    def to_row(self, key_name: str, key: str) -> dict[str, Any]:
        filled = (
            self.outcomes.get("TP", 0)
            + self.outcomes.get("SL", 0)
            + self.outcomes.get("TIMEOUT", 0)
        )
        ambiguity_rows = _ambiguity_rows(self)
        return {
            key_name: key,
            "rows": self.rows,
            "setup_rows": self.setup_rows,
            "resolved_r_n": self.resolved_r_n,
            "sum_r": _round(self.resolved_r_sum),
            "mean_r": _mean(self.resolved_r_sum, self.resolved_r_n),
            "win_rate": _rate(self.wins, self.resolved_r_n),
            "tp": self.outcomes.get("TP", 0),
            "sl": self.outcomes.get("SL", 0),
            "timeout": self.outcomes.get("TIMEOUT", 0),
            "no_entry": self.outcomes.get("NO_ENTRY", 0),
            "same_bar": self.outcomes.get("SAME_BAR", 0),
            "lower_tf_gappy": self.outcomes.get("LOWER_TF_GAPPY", 0),
            "gap_rows": self.gap_rows,
            "gap_before_resolution": self.gap_before_resolution,
            "gap_after_resolution": self.gap_after_resolution,
            "gap_timing_unknown": self.gap_timing_unknown,
            "immediate_stop": self.immediate_stop,
            "no_entry_rate_setup": _rate(self.outcomes.get("NO_ENTRY", 0), self.setup_rows),
            "sl_rate_filled": _rate(self.outcomes.get("SL", 0), filled),
            "immediate_stop_rate_sl": _rate(self.immediate_stop, self.outcomes.get("SL", 0)),
            "ambiguity_rate_setup": _rate(ambiguity_rows, self.setup_rows),
            "gap_row_rate_setup": _rate(self.gap_rows, self.setup_rows),
            "gap_before_resolution_rate_setup": _rate(self.gap_before_resolution, self.setup_rows),
        }


def parse_cohort_key(cohort_key: str) -> tuple[str, str, str]:
    parts = cohort_key.split("|", 2)
    if len(parts) != 3 or not all(parts):
        raise ValueError(
            f"cohort_key must be 'symbol|session|regime' with regime allowed to contain '|': {cohort_key!r}"
        )
    return parts[0], parts[1], parts[2]


def load_cohort_specs(path: str | Path) -> tuple[dict[str, Any], list[CohortSpec]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    specs = [CohortSpec.from_mapping(item) for item in payload.get("cohorts") or []]
    if not specs:
        raise ValueError(f"no cohorts found in {path}")
    return payload, specs


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


def analyze_cohort_stability(
    *,
    input_path: str | Path,
    cohort_path: str | Path = DEFAULT_COHORT_PATH,
    min_year_resolved_n: int = 30,
    min_total_resolved_n: int = 150,
    max_rows: int | None = None,
) -> dict[str, Any]:
    input_path = Path(input_path)
    cohort_payload, specs = load_cohort_specs(cohort_path)
    states = [_new_cohort_state(spec) for spec in specs]
    key_to_state = {state["spec"].cohort_key: state for state in states}

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

        cohort_key = _row_cohort_key(row)
        state = key_to_state.get(cohort_key)
        if state is not None:
            _add_row_to_state(state, row)
        if max_rows is not None and rows_scanned >= max_rows:
            break

    cohort_summaries = [
        _summarize_state(
            state,
            min_year_resolved_n=min_year_resolved_n,
            min_total_resolved_n=min_total_resolved_n,
        )
        for state in states
    ]
    priorities = _priority_rows(cohort_summaries)
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": _utc_now().isoformat(),
        "input_jsonl": str(input_path),
        "cohort_spec_path": str(Path(cohort_path)),
        "cohort_spec_schema_version": cohort_payload.get("schema_version"),
        "selection_status": cohort_payload.get("selection_status"),
        "source_diagnostics_report": cohort_payload.get("source_diagnostics_report"),
        "source_diagnostics_commit": cohort_payload.get("source_diagnostics_commit"),
        "interpretation_boundary": cohort_payload.get("interpretation_boundary") or [],
        "min_year_resolved_n": min_year_resolved_n,
        "min_total_resolved_n": min_total_resolved_n,
        "max_rows": max_rows,
        "rows_scanned": rows_scanned,
        "unique_keys": len(keys_seen),
        "duplicate_keys": duplicate_keys,
        "ai_attempted_rows": ai_attempted_rows,
        "ai_call_count_sum": ai_call_count_sum,
        "cohorts": cohort_summaries,
        "followup_priorities": priorities,
        "synthesis": _synthesis_bullets(cohort_summaries, priorities),
    }


def render_report(summary: Mapping[str, Any]) -> str:
    priorities = summary.get("followup_priorities") or []
    cohorts = summary.get("cohorts") or []
    lines = [
        "# Phase 3 Truth-Layer Cohort Stability Follow-Up",
        "",
        f"**Created UTC:** {summary.get('created_at_utc')}",
        f"**Input:** `{summary.get('input_jsonl')}`",
        f"**Cohort spec:** `{summary.get('cohort_spec_path')}`",
        f"**Rows scanned:** {summary.get('rows_scanned')}",
        "",
        "## Interpretation Boundary",
        "",
        "- Research/tooling only; no live trading logic, prompt, config, risk policy, or execution behavior is changed.",
        "- No AI/API calls are made. `ai_attempted_rows` and `ai_call_count_sum` must remain zero.",
        "- These cohorts were selected after seeing the diagnostic report, so this is stability and invalidation work, not out-of-sample proof.",
        "- `CLEAN_*` scopes exclude same-bar and lower-timeframe gappy outcomes. Selected-source lower-timeframe gap counts remain visible as diagnostics, not hard exclusions.",
        "- `RESOLUTION_SAFE_*` scopes additionally exclude selected-source gaps before or at the mechanical resolution point.",
        "- `ZERO_GAP_*` scopes additionally require zero selected-source lower-timeframe gap counts in the tested horizon.",
        "- DSR-corrected p, PBO, and true effective_N are not computed here; the report only checks whether a cohort is worth a deeper controlled research run.",
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
                    "selection_status": summary.get("selection_status"),
                }
            ]
        ),
        "",
        "## Follow-Up Priority",
        "",
        _markdown_table(priorities),
        "",
        "## Cohort Scope Summary",
        "",
        _markdown_table(_scope_summary_rows(cohorts)),
        "",
        "## Clean High Year Stability",
        "",
        _markdown_table(_year_stability_rows(cohorts, scope="CLEAN_HIGH")),
        "",
        "## Resolution-Safe High Stability",
        "",
        _markdown_table(_year_stability_rows(cohorts, scope="RESOLUTION_SAFE_HIGH")),
        "",
        "## High-Only Year Stability",
        "",
        _markdown_table(_year_stability_rows(cohorts, scope="HIGH_ONLY")),
        "",
        "## Zero-Gap High Sensitivity",
        "",
        _markdown_table(_year_stability_rows(cohorts, scope="ZERO_GAP_HIGH")),
        "",
        "## Early vs Recent Split",
        "",
        _markdown_table(_period_rows(cohorts, scope="CLEAN_HIGH")),
        "",
        "## Cohort Details",
        "",
    ]
    for cohort in cohorts:
        lines.extend(_render_cohort_detail(cohort))
    lines.extend(["## Synthesis", "", *(summary.get("synthesis") or [])])
    return "\n".join(lines).rstrip() + "\n"


def write_summary(summary: Mapping[str, Any], *, output_root: str | Path, input_path: str | Path) -> Path:
    output_dir = Path(output_root)
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = _utc_now().strftime("%Y%m%dT%H%M%SZ")
    path = output_dir / f"{_short_slug(Path(input_path).stem)}_cohort_stability_{stamp}.json"
    path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return path


def write_report(path: str | Path, content: str) -> Path:
    report_path = Path(path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(content, encoding="utf-8")
    return report_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="Truth-layer JSONL. Defaults to latest truth-layer artifact.")
    parser.add_argument("--cohort-path", default=DEFAULT_COHORT_PATH)
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--report-path", default=DEFAULT_REPORT_PATH)
    parser.add_argument("--min-year-resolved-n", type=int, default=30)
    parser.add_argument("--min-total-resolved-n", type=int, default=150)
    parser.add_argument("--max-rows", type=int)
    parser.add_argument("--write", action="store_true", help="Write markdown report.")
    parser.add_argument("--quiet", action="store_true", help="Print compact run summary.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    input_path = Path(args.input) if args.input else find_latest_input()
    summary = analyze_cohort_stability(
        input_path=input_path,
        cohort_path=args.cohort_path,
        min_year_resolved_n=args.min_year_resolved_n,
        min_total_resolved_n=args.min_total_resolved_n,
        max_rows=args.max_rows,
    )
    summary_path = write_summary(summary, output_root=args.output_root, input_path=input_path)
    summary["output_summary"] = str(summary_path)
    if args.write:
        report_path = write_report(args.report_path, render_report(summary))
        summary["report_path"] = str(report_path)
        summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    if args.quiet:
        print(
            json.dumps(
                {
                    "rows_scanned": summary.get("rows_scanned"),
                    "output_summary": summary.get("output_summary"),
                    "report_path": summary.get("report_path"),
                    "followup_priorities": (summary.get("followup_priorities") or [])[:10],
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def _new_cohort_state(spec: CohortSpec) -> dict[str, Any]:
    return {
        "spec": spec,
        "universe": RunningStats(),
        "scopes": {scope: RunningStats() for scope in SCOPE_DEFINITIONS},
        "years": {scope: defaultdict(RunningStats) for scope in SCOPE_DEFINITIONS},
        "periods": {scope: defaultdict(RunningStats) for scope in SCOPE_DEFINITIONS},
    }


def _add_row_to_state(state: dict[str, Any], row: Mapping[str, Any]) -> None:
    state["universe"].add(row)
    if not _is_setup_row(row):
        return
    confidence = str(row.get("truth_confidence") or "")
    year = _row_year(row)
    period = _period_for_year(year)
    for scope, definition in SCOPE_DEFINITIONS.items():
        if confidence not in definition["confidences"]:
            continue
        if definition["exclude_ambiguous"] and _is_ambiguous_outcome(row):
            continue
        if definition["require_resolution_safe"] and not _is_resolution_safe(row):
            continue
        if definition["require_zero_gap"] and _has_lower_tf_gap(row):
            continue
        stats = state["scopes"][scope]
        stats.add(row)
        state["years"][scope][year].add(row)
        state["periods"][scope][period].add(row)


def _summarize_state(
    state: Mapping[str, Any],
    *,
    min_year_resolved_n: int,
    min_total_resolved_n: int,
) -> dict[str, Any]:
    spec: CohortSpec = state["spec"]
    scopes = {
        scope: stats.to_row("scope", scope)
        for scope, stats in state["scopes"].items()
    }
    years = {
        scope: [
            stats.to_row("year", year)
            for year, stats in sorted(year_stats.items(), key=lambda item: item[0])
        ]
        for scope, year_stats in state["years"].items()
    }
    periods = {
        scope: [
            stats.to_row("period", period)
            for period, stats in sorted(period_stats.items(), key=lambda item: item[0])
        ]
        for scope, period_stats in state["periods"].items()
    }
    stability = {
        scope: _stability_summary(
            years.get(scope) or [],
            scopes.get(scope) or {},
            min_year_resolved_n=min_year_resolved_n,
        )
        for scope in SCOPE_DEFINITIONS
    }
    treatment = _classify_treatment(
        scopes=scopes,
        stability=stability,
        min_total_resolved_n=min_total_resolved_n,
    )
    return {
        "cohort_key": spec.cohort_key,
        "symbol": spec.symbol,
        "session": spec.session,
        "regime": spec.regime,
        "role": spec.role,
        "selection_reason": spec.selection_reason,
        "key_questions": list(spec.key_questions),
        "universe": state["universe"].to_row("scope", "all_matching_rows"),
        "scopes": scopes,
        "stability": stability,
        "years": years,
        "periods": periods,
        "treatment": treatment,
    }


def _stability_summary(
    year_rows: Sequence[Mapping[str, Any]],
    scope_row: Mapping[str, Any],
    *,
    min_year_resolved_n: int,
) -> dict[str, Any]:
    valid = [
        row
        for row in year_rows
        if int(row.get("resolved_r_n") or 0) >= min_year_resolved_n
    ]
    positive = [
        row
        for row in valid
        if row.get("mean_r") is not None and float(row.get("mean_r") or 0.0) > 0
    ]
    total_resolved = int(scope_row.get("resolved_r_n") or 0)
    if not valid:
        return {
            "valid_years": 0,
            "positive_years": 0,
            "positive_year_rate": 0.0,
            "worst_year": None,
            "worst_year_mean_r": None,
            "best_year": None,
            "best_year_mean_r": None,
            "min_valid_year_resolved_n": 0,
            "max_year_resolved_share": 0.0,
            "underpowered_years": len([row for row in year_rows if int(row.get("resolved_r_n") or 0) > 0]),
        }
    worst = min(valid, key=lambda row: float(row.get("mean_r") or 0.0))
    best = max(valid, key=lambda row: float(row.get("mean_r") or 0.0))
    max_year_n = max(int(row.get("resolved_r_n") or 0) for row in valid)
    min_year_n = min(int(row.get("resolved_r_n") or 0) for row in valid)
    underpowered = [
        row
        for row in year_rows
        if 0 < int(row.get("resolved_r_n") or 0) < min_year_resolved_n
    ]
    return {
        "valid_years": len(valid),
        "positive_years": len(positive),
        "positive_year_rate": _rate(len(positive), len(valid)),
        "worst_year": worst.get("year"),
        "worst_year_mean_r": worst.get("mean_r"),
        "best_year": best.get("year"),
        "best_year_mean_r": best.get("mean_r"),
        "min_valid_year_resolved_n": min_year_n,
        "max_year_resolved_share": _rate(max_year_n, total_resolved),
        "underpowered_years": len(underpowered),
    }


def _classify_treatment(
    *,
    scopes: Mapping[str, Mapping[str, Any]],
    stability: Mapping[str, Mapping[str, Any]],
    min_total_resolved_n: int,
) -> dict[str, Any]:
    clean = scopes.get("CLEAN_HIGH") or {}
    high = scopes.get("HIGH_ONLY") or {}
    clean_stability = stability.get("CLEAN_HIGH") or {}
    high_stability = stability.get("HIGH_ONLY") or {}
    clean_n = int(clean.get("resolved_r_n") or 0)
    high_n = int(high.get("resolved_r_n") or 0)
    clean_mean = _as_float(clean.get("mean_r"))
    high_mean = _as_float(high.get("mean_r"))
    clean_positive_rate = float(clean_stability.get("positive_year_rate") or 0.0)
    high_positive_rate = float(high_stability.get("positive_year_rate") or 0.0)
    clean_years = int(clean_stability.get("valid_years") or 0)
    high_years = int(high_stability.get("valid_years") or 0)
    clean_dominance = float(clean_stability.get("max_year_resolved_share") or 0.0)
    reasons: list[str] = []
    score = 0.0

    if high_n < min_total_resolved_n:
        treatment = "DEPRIORITIZE_UNDERPOWERED"
        reasons.append(f"HIGH_ONLY resolved_n {high_n} is below {min_total_resolved_n}.")
    elif clean_n >= min_total_resolved_n and clean_years >= 3 and clean_positive_rate == 1.0 and clean_dominance <= 0.45:
        treatment = "PRIMARY_CONTROLLED_RESEARCH"
        reasons.append("CLEAN_HIGH clears sample, >=3 yearly folds, all valid years positive, and no single-year dominance flag.")
    elif clean_n >= min_total_resolved_n and clean_years >= 3 and clean_positive_rate >= 0.75:
        treatment = "CONTROLLED_RESEARCH_WATCHLIST"
        reasons.append("CLEAN_HIGH has enough sample and mostly positive yearly folds, but at least one stability or dominance caution remains.")
    elif high_years >= 3 and high_positive_rate >= 0.75 and high_mean is not None and high_mean > 0:
        treatment = "EXPLORATORY_SPLIT_REQUIRED"
        reasons.append("HIGH_ONLY is positive across most valid years, but the clean subset did not fully clear stability guards.")
    elif high_mean is not None and high_mean > 0:
        treatment = "EXPLORATORY_ONLY"
        reasons.append("Pooled HIGH_ONLY mean is positive, but fold stability is not strong enough.")
    else:
        treatment = "REJECT_FOR_NOW"
        reasons.append("Pooled HIGH_ONLY mean is non-positive or insufficient after stability checks.")

    if clean_mean is not None:
        score += clean_mean
    elif high_mean is not None:
        score += high_mean * 0.5
    score += min(clean_n, 800) / 800 * 0.20
    score += clean_positive_rate * 0.20
    score -= max(0.0, clean_dominance - 0.45) * 0.50
    score -= float(clean.get("ambiguity_rate_setup") or 0.0) * 0.25
    if clean_n and high_n:
        removed_share = 1.0 - clean_n / high_n
        if removed_share > 0.25:
            reasons.append(f"Clean exclusion removes {removed_share:.1%} of HIGH_ONLY resolved rows.")
            score -= removed_share * 0.10
    return {
        "recommended_treatment": treatment,
        "priority_score": round(score, 6),
        "reasons": reasons,
    }


def _priority_rows(cohorts: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for cohort in cohorts:
        treatment = cohort.get("treatment") or {}
        clean = (cohort.get("scopes") or {}).get("CLEAN_HIGH") or {}
        high = (cohort.get("scopes") or {}).get("HIGH_ONLY") or {}
        stability = (cohort.get("stability") or {}).get("CLEAN_HIGH") or {}
        rows.append(
            {
                "cohort_key": cohort.get("cohort_key"),
                "role": cohort.get("role"),
                "recommended_treatment": treatment.get("recommended_treatment"),
                "priority_score": treatment.get("priority_score"),
                "clean_high_n": clean.get("resolved_r_n"),
                "clean_high_mean_r": clean.get("mean_r"),
                "clean_high_win_rate": clean.get("win_rate"),
                "clean_valid_years": stability.get("valid_years"),
                "clean_positive_years": stability.get("positive_years"),
                "clean_worst_year": stability.get("worst_year"),
                "clean_worst_year_mean_r": stability.get("worst_year_mean_r"),
                "high_only_n": high.get("resolved_r_n"),
                "high_only_mean_r": high.get("mean_r"),
                "high_only_win_rate": high.get("win_rate"),
            }
        )
    return sorted(rows, key=lambda row: float(row.get("priority_score") or 0.0), reverse=True)


def _scope_summary_rows(cohorts: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for cohort in cohorts:
        for scope_name in SCOPE_DEFINITIONS:
            scope = (cohort.get("scopes") or {}).get(scope_name) or {}
            rows.append(
                {
                    "cohort_key": cohort.get("cohort_key"),
                    "scope": scope_name,
                    "setup_rows": scope.get("setup_rows"),
                    "resolved_r_n": scope.get("resolved_r_n"),
                    "mean_r": scope.get("mean_r"),
                    "win_rate": scope.get("win_rate"),
                    "tp": scope.get("tp"),
                    "sl": scope.get("sl"),
                    "timeout": scope.get("timeout"),
                    "no_entry": scope.get("no_entry"),
                    "same_bar": scope.get("same_bar"),
                    "lower_tf_gappy": scope.get("lower_tf_gappy"),
                    "gap_rows": scope.get("gap_rows"),
                    "gap_before_resolution": scope.get("gap_before_resolution"),
                    "gap_after_resolution": scope.get("gap_after_resolution"),
                    "gap_timing_unknown": scope.get("gap_timing_unknown"),
                    "immediate_stop_rate_sl": scope.get("immediate_stop_rate_sl"),
                    "no_entry_rate_setup": scope.get("no_entry_rate_setup"),
                    "ambiguity_rate_setup": scope.get("ambiguity_rate_setup"),
                    "gap_row_rate_setup": scope.get("gap_row_rate_setup"),
                    "gap_before_resolution_rate_setup": scope.get("gap_before_resolution_rate_setup"),
                }
            )
    return rows


def _year_stability_rows(cohorts: Sequence[Mapping[str, Any]], *, scope: str) -> list[dict[str, Any]]:
    rows = []
    for cohort in cohorts:
        stability = (cohort.get("stability") or {}).get(scope) or {}
        rows.append(
            {
                "cohort_key": cohort.get("cohort_key"),
                "scope": scope,
                "valid_years": stability.get("valid_years"),
                "positive_years": stability.get("positive_years"),
                "positive_year_rate": stability.get("positive_year_rate"),
                "worst_year": stability.get("worst_year"),
                "worst_year_mean_r": stability.get("worst_year_mean_r"),
                "best_year": stability.get("best_year"),
                "best_year_mean_r": stability.get("best_year_mean_r"),
                "min_valid_year_resolved_n": stability.get("min_valid_year_resolved_n"),
                "max_year_resolved_share": stability.get("max_year_resolved_share"),
                "underpowered_years": stability.get("underpowered_years"),
            }
        )
    return rows


def _period_rows(cohorts: Sequence[Mapping[str, Any]], *, scope: str) -> list[dict[str, Any]]:
    rows = []
    for cohort in cohorts:
        for period in (cohort.get("periods") or {}).get(scope) or []:
            rows.append(
                {
                    "cohort_key": cohort.get("cohort_key"),
                    "scope": scope,
                    "period": period.get("period"),
                    "resolved_r_n": period.get("resolved_r_n"),
                    "mean_r": period.get("mean_r"),
                    "win_rate": period.get("win_rate"),
                    "tp": period.get("tp"),
                    "sl": period.get("sl"),
                    "timeout": period.get("timeout"),
                    "no_entry": period.get("no_entry"),
                    "same_bar": period.get("same_bar"),
                    "lower_tf_gappy": period.get("lower_tf_gappy"),
                    "gap_rows": period.get("gap_rows"),
                    "gap_before_resolution": period.get("gap_before_resolution"),
                    "gap_after_resolution": period.get("gap_after_resolution"),
                }
            )
    return rows


def _render_cohort_detail(cohort: Mapping[str, Any]) -> list[str]:
    lines = [
        f"### {cohort.get('cohort_key')}",
        "",
        f"- Role: `{cohort.get('role')}`",
        f"- Treatment: `{(cohort.get('treatment') or {}).get('recommended_treatment')}`",
        f"- Selection reason: {cohort.get('selection_reason')}",
        "",
        "Scope rows:",
        "",
        _markdown_table(
            [
                dict({"scope": scope_name}, **scope)
                for scope_name, scope in (cohort.get("scopes") or {}).items()
            ]
        ),
        "",
        "Clean high yearly rows:",
        "",
        _markdown_table((cohort.get("years") or {}).get("CLEAN_HIGH") or []),
        "",
        "Treatment reasons:",
        "",
    ]
    reasons = (cohort.get("treatment") or {}).get("reasons") or []
    if reasons:
        lines.extend([f"- {reason}" for reason in reasons])
    else:
        lines.append("- No treatment reason recorded.")
    lines.append("")
    return lines


def _synthesis_bullets(
    cohorts: Sequence[Mapping[str, Any]],
    priorities: Sequence[Mapping[str, Any]],
) -> list[str]:
    bullets = [
        "- This pass narrows the diagnostics from global anatomy to explicit follow-up cohorts and year/period stability checks.",
        "- It does not answer promotion. The correct use is to decide which cohorts deserve a pre-declared controlled research run with DSR/PBO/effective_N accounting.",
    ]
    if priorities:
        top = priorities[0]
        bullets.append(
            "- Highest follow-up priority by the stability score is "
            f"`{top.get('cohort_key')}` with CLEAN_HIGH n={top.get('clean_high_n')}, "
            f"mean R={_format_signed(top.get('clean_high_mean_r'))}, "
            f"valid years={top.get('clean_valid_years')}, "
            f"positive years={top.get('clean_positive_years')}."
        )
    primary = [
        row
        for row in priorities
        if row.get("recommended_treatment") == "PRIMARY_CONTROLLED_RESEARCH"
    ]
    watch = [
        row
        for row in priorities
        if row.get("recommended_treatment")
        in {"CONTROLLED_RESEARCH_WATCHLIST", "EXPLORATORY_SPLIT_REQUIRED"}
    ]
    bullets.append(
        f"- Treatment split: primary={len(primary)}, watchlist/split-required={len(watch)}, "
        f"other={max(0, len(priorities) - len(primary) - len(watch))}."
    )
    bullets.append(
        "- Remaining open tasks are actual realized-R enrichment, forward external-feed accumulation, "
        "and a true pre-declared validation pass; this artifact should not be used to tune entry offsets."
    )
    return bullets


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


def _has_lower_tf_gap(row: Mapping[str, Any]) -> bool:
    return _selected_gap_count(row) > 0


def _is_ambiguous_outcome(row: Mapping[str, Any]) -> bool:
    return str(row.get("truth_outcome") or "") in AMBIGUOUS_OUTCOMES


def _is_resolution_safe(row: Mapping[str, Any]) -> bool:
    if _is_ambiguous_outcome(row):
        return False
    timing = _selected_gap_timing(row)
    return timing in {"none", "after_resolution"}


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
    outcome = str(row.get("truth_outcome") or "")
    exit_time = _selected_exit_time(row)
    if outcome == "NO_ENTRY":
        return "before_or_at_resolution"
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


def _ambiguity_rows(stats: RunningStats) -> int:
    return stats.outcomes.get("SAME_BAR", 0) + stats.outcomes.get("LOWER_TF_GAPPY", 0)


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


def _short_slug(value: str, *, max_len: int = 72) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_").lower()
    if len(slug) <= max_len:
        return slug
    digest = hashlib.sha1(slug.encode("utf-8")).hexdigest()[:10]
    return f"{slug[: max_len - 11]}_{digest}"


def _format_signed(value: Any) -> str:
    numeric = _as_float(value)
    if numeric is None:
        return "n/a"
    return f"{numeric:+.4f}"


def _markdown_table(rows: Sequence[Mapping[str, Any]]) -> str:
    if not rows:
        return "_No rows._"
    preferred = (
        "cohort_key",
        "role",
        "recommended_treatment",
        "priority_score",
        "scope",
        "period",
        "year",
        "rows_scanned",
        "unique_keys",
        "duplicate_keys",
        "ai_attempted_rows",
        "ai_call_count_sum",
        "selection_status",
        "setup_rows",
        "rows",
        "resolved_r_n",
        "sum_r",
        "mean_r",
        "win_rate",
        "tp",
        "sl",
        "timeout",
        "no_entry",
        "same_bar",
        "lower_tf_gappy",
        "gap_rows",
        "gap_before_resolution",
        "gap_after_resolution",
        "gap_timing_unknown",
        "immediate_stop",
        "immediate_stop_rate_sl",
        "no_entry_rate_setup",
        "sl_rate_filled",
        "ambiguity_rate_setup",
        "gap_row_rate_setup",
        "gap_before_resolution_rate_setup",
        "clean_high_n",
        "clean_high_mean_r",
        "clean_high_win_rate",
        "clean_valid_years",
        "clean_positive_years",
        "clean_worst_year",
        "clean_worst_year_mean_r",
        "high_only_n",
        "high_only_mean_r",
        "high_only_win_rate",
        "valid_years",
        "positive_years",
        "positive_year_rate",
        "worst_year",
        "worst_year_mean_r",
        "best_year",
        "best_year_mean_r",
        "min_valid_year_resolved_n",
        "max_year_resolved_share",
        "underpowered_years",
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
