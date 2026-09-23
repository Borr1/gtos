#!/usr/bin/env python3
"""Audit year/month dominance for pre-registered matrix follow-up cohorts.

This is research-only tooling. It checks whether post-matrix follow-up lanes are
dependent on one year or one month before any deeper replay work is authorized.
It intentionally does not compute DSR, PBO, effective_N, or promotion verdicts.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.evaluate_truth_layer_controlled_hypotheses import (
    _as_float,
    _markdown_cell,
    _population_inclusion,
    _row_cohort_key,
    _row_year,
    find_latest_input,
    iter_jsonl,
)


SCHEMA_VERSION = "truth_layer_matrix_followup_dominance_audit_v1"
DEFAULT_SPEC_PATH = (
    "research/phase_3_external_feed_validation/"
    "TRUTH_LAYER_MATRIX_FOLLOWUP_HYPOTHESES_V1.json"
)
DEFAULT_OUTPUT_ROOT = (
    "data/external/validation/calendar_macro_bundle_v1/historical_opportunities/"
    "truth_layer/matrix_followup_dominance"
)
DEFAULT_REPORT_PATH = (
    "research/phase_3_external_feed_validation/"
    "TRUTH_LAYER_MATRIX_DOMINANCE_AUDIT_2026-05-01.md"
)
RESOLVED_OUTCOMES = {"TP", "SL", "TIMEOUT"}


@dataclass
class Stats:
    population_rows: int = 0
    resolved_r_n: int = 0
    sum_r: float = 0.0
    wins: int = 0
    outcomes: Counter[str] = field(default_factory=Counter)

    def add(self, row: Mapping[str, Any], *, resolved_outcomes: set[str]) -> None:
        self.population_rows += 1
        outcome = str(row.get("truth_outcome") or "UNKNOWN")
        self.outcomes[outcome] += 1
        if outcome not in resolved_outcomes:
            return
        realized = _as_float(row.get("truth_realized_r"))
        if realized is None:
            return
        self.resolved_r_n += 1
        self.sum_r += realized
        if realized > 0:
            self.wins += 1

    def row(self, key_name: str, key: str, *, total_resolved: int | None = None) -> dict[str, Any]:
        return {
            key_name: key,
            "population_rows": self.population_rows,
            "resolved_r_n": self.resolved_r_n,
            "resolved_share": _rate(self.resolved_r_n, total_resolved or 0) if total_resolved else None,
            "sum_r": _round(self.sum_r),
            "mean_r": _mean(self.sum_r, self.resolved_r_n),
            "win_rate": _rate(self.wins, self.resolved_r_n),
            "tp": self.outcomes.get("TP", 0),
            "sl": self.outcomes.get("SL", 0),
            "timeout": self.outcomes.get("TIMEOUT", 0),
            "no_entry": self.outcomes.get("NO_ENTRY", 0),
        }


def load_followup_spec(path: str | Path = DEFAULT_SPEC_PATH) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != "truth_layer_matrix_followup_hypotheses_v1":
        raise ValueError(f"unsupported follow-up schema: {payload.get('schema_version')!r}")
    if payload.get("promotion_verdict_allowed") is not False:
        raise ValueError("matrix follow-up spec must set promotion_verdict_allowed=false")
    if not payload.get("families"):
        raise ValueError("matrix follow-up spec has no families")
    return payload


def analyze_matrix_followup_dominance(
    *,
    input_path: str | Path,
    spec_path: str | Path = DEFAULT_SPEC_PATH,
    max_rows: int | None = None,
) -> dict[str, Any]:
    spec = load_followup_spec(spec_path)
    thresholds = spec.get("audit_thresholds") or {}
    population = spec.get("population") or {}
    resolved_outcomes = set(population.get("primary_resolved_outcomes") or RESOLVED_OUTCOMES)
    target_cohorts = {
        str(cohort["cohort_key"]): {
            "family_id": family.get("family_id"),
            "lane": family.get("lane"),
            "family_status": family.get("status"),
            "candidate_id": cohort.get("candidate_id"),
        }
        for family in spec.get("families") or []
        for cohort in family.get("cohorts") or []
    }
    states = {key: new_state(meta) for key, meta in target_cohorts.items()}
    rows_scanned = 0
    duplicate_keys = 0
    keys_seen: set[str] = set()
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
        if cohort_key in states:
            included, reasons = _population_inclusion(row, population)
            if included:
                add_row(states[cohort_key], row, resolved_outcomes=resolved_outcomes)
            else:
                for reason in reasons:
                    states[cohort_key]["exclusions"][reason] += 1
        if max_rows is not None and rows_scanned >= max_rows:
            break

    cohort_rows = [
        summarize_cohort(key, state, thresholds=thresholds)
        for key, state in states.items()
    ]
    family_rows = summarize_families(cohort_rows)
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_jsonl": str(Path(input_path)),
        "spec_path": str(Path(spec_path)),
        "promotion_verdict_allowed": False,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "promotion_blocked_reason": "Dominance audit does not compute DSR, PBO, effective_N, or prospective confirmation.",
        "rows_scanned": rows_scanned,
        "unique_keys": len(keys_seen),
        "duplicate_keys": duplicate_keys,
        "ai_attempted_rows": ai_attempted_rows,
        "ai_call_count_sum": ai_call_count_sum,
        "audit_thresholds": thresholds,
        "families": family_rows,
        "cohorts": cohort_rows,
        "year_folds": [row for item in cohort_rows for row in item.get("year_folds") or []],
        "month_concentration": [row for item in cohort_rows for row in item.get("top_months") or []],
        "next_session_recommendation": next_session_recommendation(cohort_rows),
    }


def new_state(meta: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "meta": dict(meta),
        "included": Stats(),
        "years": defaultdict(Stats),
        "months": defaultdict(Stats),
        "exclusions": Counter(),
    }


def add_row(
    state: dict[str, Any],
    row: Mapping[str, Any],
    *,
    resolved_outcomes: set[str],
) -> None:
    state["included"].add(row, resolved_outcomes=resolved_outcomes)
    state["years"][_row_year(row)].add(row, resolved_outcomes=resolved_outcomes)
    month = str(row.get("month") or str(row.get("candle_close_utc") or "")[:7] or "unknown")
    state["months"][month].add(row, resolved_outcomes=resolved_outcomes)


def summarize_cohort(
    cohort_key: str,
    state: Mapping[str, Any],
    *,
    thresholds: Mapping[str, Any],
) -> dict[str, Any]:
    total = state["included"].resolved_r_n
    year_rows = [
        stats.row("year", year, total_resolved=total)
        for year, stats in sorted(state["years"].items())
    ]
    month_rows = [
        stats.row("month", month, total_resolved=total)
        for month, stats in sorted(state["months"].items())
    ]
    valid_year_min = int(thresholds.get("min_year_resolved_n") or 30)
    valid_years = [row for row in year_rows if int(row.get("resolved_r_n") or 0) >= valid_year_min]
    positive_valid_years = [row for row in valid_years if (row.get("mean_r") or 0.0) > 0]
    top_year = max(year_rows, key=lambda row: int(row.get("resolved_r_n") or 0), default=None)
    top_month = max(month_rows, key=lambda row: int(row.get("resolved_r_n") or 0), default=None)
    top_year_excluded = exclude_period(state["years"], (top_year or {}).get("year"))
    included = state["included"].row("population", "RESOLUTION_SAFE_HIGH")
    row = {
        "cohort_key": cohort_key,
        "candidate_id": state["meta"].get("candidate_id"),
        "family_id": state["meta"].get("family_id"),
        "lane": state["meta"].get("lane"),
        "family_status": state["meta"].get("family_status"),
        "population_rows": included["population_rows"],
        "resolved_r_n": included["resolved_r_n"],
        "sum_r": included["sum_r"],
        "mean_r": included["mean_r"],
        "win_rate": included["win_rate"],
        "valid_year_folds": len(valid_years),
        "positive_valid_year_folds": len(positive_valid_years),
        "top_year": (top_year or {}).get("year"),
        "top_year_resolved_share": (top_year or {}).get("resolved_share"),
        "top_year_mean_r": (top_year or {}).get("mean_r"),
        "top_year_excluded_resolved_n": top_year_excluded["resolved_r_n"],
        "top_year_excluded_mean_r": top_year_excluded["mean_r"],
        "top_month": (top_month or {}).get("month"),
        "top_month_resolved_share": (top_month or {}).get("resolved_share"),
        "top_month_mean_r": (top_month or {}).get("mean_r"),
        "exclusions": dict(sorted((state.get("exclusions") or {}).items())),
        "year_folds": add_cohort_key(year_rows, cohort_key),
        "top_months": add_cohort_key(top_n_months(month_rows, 5), cohort_key),
    }
    row["audit_status"] = audit_status(row, thresholds)
    row["audit_blockers"] = audit_blockers(row, thresholds)
    row["next_action"] = next_action(row)
    return row


def exclude_period(periods: Mapping[str, Stats], excluded: Any) -> dict[str, Any]:
    stats = Stats()
    for key, item in periods.items():
        if str(key) == str(excluded):
            continue
        stats.population_rows += item.population_rows
        stats.resolved_r_n += item.resolved_r_n
        stats.sum_r += item.sum_r
        stats.wins += item.wins
        stats.outcomes.update(item.outcomes)
    return stats.row("excluded_period", f"not_{excluded}")


def audit_blockers(row: Mapping[str, Any], thresholds: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    if int(row.get("resolved_r_n") or 0) < int(thresholds.get("min_total_resolved_n") or 150):
        blockers.append("min_total_resolved_n")
    if float(row.get("top_year_resolved_share") or 0.0) > float(thresholds.get("max_single_year_resolved_share") or 0.45):
        blockers.append("single_year_dominance")
    if float(row.get("top_month_resolved_share") or 0.0) > float(thresholds.get("max_single_month_resolved_share") or 0.25):
        blockers.append("single_month_concentration")
    if thresholds.get("require_all_valid_years_positive", True):
        if int(row.get("positive_valid_year_folds") or 0) < int(row.get("valid_year_folds") or 0):
            blockers.append("non_positive_valid_year")
    if thresholds.get("require_top_year_excluded_mean_r_positive", True):
        value = row.get("top_year_excluded_mean_r")
        if value is None or float(value) <= 0.0:
            blockers.append("top_year_excluded_non_positive")
    return blockers


def audit_status(row: Mapping[str, Any], thresholds: Mapping[str, Any]) -> str:
    blockers = audit_blockers(row, thresholds)
    if blockers:
        return "BLOCKED_" + "+".join(blockers)
    if row.get("family_status") == "dominance_audit_only":
        return "DOMINANCE_CLEAR_DIAGNOSTIC_ONLY"
    return "CLEARED_FOR_RAW_REPLAY_PRIORITY_DIAGNOSTIC_ONLY"


def next_action(row: Mapping[str, Any]) -> str:
    status = str(row.get("audit_status") or "")
    if status.startswith("CLEARED"):
        return "eligible raw-OHLC adapter target; still not promotion proof"
    if status.startswith("DOMINANCE_CLEAR"):
        return "may be considered for a separate pre-registration; still not promotion proof"
    return "do not deepen until blockers are explained or separate protocol is registered"


def summarize_families(cohort_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in cohort_rows:
        grouped[str(row.get("family_id") or "unknown")].append(row)
    family_rows: list[dict[str, Any]] = []
    for family_id, rows in sorted(grouped.items()):
        resolved = sum(int(row.get("resolved_r_n") or 0) for row in rows)
        sum_r = sum(float(row.get("sum_r") or 0.0) for row in rows)
        blockers = sorted({blocker for row in rows for blocker in row.get("audit_blockers") or []})
        family_rows.append(
            {
                "family_id": family_id,
                "cohort_count": len(rows),
                "resolved_r_n": resolved,
                "sum_r": _round(sum_r),
                "mean_r": _mean(sum_r, resolved),
                "cohorts_clear": sum(1 for row in rows if not row.get("audit_blockers")),
                "cohorts_blocked": sum(1 for row in rows if row.get("audit_blockers")),
                "family_status": "CLEAR_DIAGNOSTIC_ONLY" if not blockers else "BLOCKED_DIAGNOSTIC_ONLY",
                "blockers": ", ".join(blockers),
            }
        )
    return family_rows


def next_session_recommendation(cohort_rows: Sequence[Mapping[str, Any]]) -> list[str]:
    cleared = [
        str(row.get("cohort_key"))
        for row in cohort_rows
        if str(row.get("audit_status") or "").startswith("CLEARED")
    ]
    dominated = [
        str(row.get("cohort_key"))
        for row in cohort_rows
        if "single_year_dominance" in (row.get("audit_blockers") or [])
    ]
    recommendations = []
    if cleared:
        recommendations.append(
            "Start raw-OHLC replay adapter with cleared diagnostic targets: " + ", ".join(cleared)
        )
    if dominated:
        recommendations.append(
            "Keep dominance-watchlist names blocked until a specific dominance/fold-rescue protocol is registered: "
            + ", ".join(dominated)
        )
    recommendations.append("Carry NO_PROMOTION_VERDICT language into the fresh session.")
    return recommendations


def render_report(summary: Mapping[str, Any]) -> str:
    lines = [
        "# Phase 3 Truth-Layer Matrix Dominance Audit",
        "",
        f"**Created UTC:** {summary.get('created_at_utc')}",
        f"**Input:** `{summary.get('input_jsonl')}`",
        f"**Spec:** `{summary.get('spec_path')}`",
        f"**Promotion verdict:** `{summary.get('promotion_verdict')}`",
        "",
        "## Boundary",
        "",
        "- Research/tooling only; no live trading logic, prompt, config, risk policy, or execution behavior is changed.",
        "- This audit exists to decide what should be prioritized for the next raw-OHLC replay session.",
        "- DSR, PBO, effective_N, and prospective confirmation are not computed here.",
        "",
        "## Data Integrity",
        "",
        markdown_table(
            [
                {
                    "rows_scanned": summary.get("rows_scanned"),
                    "unique_keys": summary.get("unique_keys"),
                    "duplicate_keys": summary.get("duplicate_keys"),
                    "ai_attempted_rows": summary.get("ai_attempted_rows"),
                    "ai_call_count_sum": summary.get("ai_call_count_sum"),
                }
            ]
        ),
        "",
        "## Families",
        "",
        markdown_table(summary.get("families") or []),
        "",
        "## Cohort Audit",
        "",
        markdown_table(compact_cohort_rows(summary.get("cohorts") or [])),
        "",
        "## Year Folds",
        "",
        markdown_table(summary.get("year_folds") or []),
        "",
        "## Top Month Concentration",
        "",
        markdown_table(summary.get("month_concentration") or []),
        "",
        "## Next Session Recommendation",
        "",
        "\n".join(f"- {item}" for item in summary.get("next_session_recommendation") or []),
    ]
    return "\n".join(lines).rstrip() + "\n"


def compact_cohort_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    keys = [
        "cohort_key",
        "family_id",
        "resolved_r_n",
        "mean_r",
        "win_rate",
        "valid_year_folds",
        "positive_valid_year_folds",
        "top_year",
        "top_year_resolved_share",
        "top_year_excluded_mean_r",
        "top_month",
        "top_month_resolved_share",
        "audit_status",
        "audit_blockers",
        "next_action",
    ]
    return [{key: row.get(key) for key in keys} for row in rows]


def write_outputs(
    summary: Mapping[str, Any],
    *,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    report_path: str | Path = DEFAULT_REPORT_PATH,
) -> tuple[Path, Path]:
    output_dir = Path(output_root)
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    summary_path = output_dir / f"truth_layer_matrix_dominance_audit_{stamp}.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    report = Path(report_path)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(summary), encoding="utf-8")
    return summary_path, report


def top_n_months(rows: Sequence[Mapping[str, Any]], n: int) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: int(row.get("resolved_r_n") or 0), reverse=True)[:n]


def add_cohort_key(rows: Sequence[Mapping[str, Any]], cohort_key: str) -> list[dict[str, Any]]:
    return [dict({"cohort_key": cohort_key}, **row) for row in rows]


def markdown_table(rows: Sequence[Mapping[str, Any]]) -> str:
    if not rows:
        return "_No rows._"
    columns: list[str] = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(str(key))
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_markdown_cell(row.get(col, "")) for col in columns) + " |")
    return "\n".join(lines)


def _rate(numer: int | float, denom: int | float) -> float | None:
    return round(float(numer) / float(denom), 6) if denom else None


def _mean(total: float, count: int) -> float | None:
    return round(float(total) / count, 6) if count else None


def _round(value: float | None) -> float | None:
    return round(float(value), 6) if value is not None else None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="Truth-layer JSONL. Defaults to latest truth-layer artifact.")
    parser.add_argument("--spec-path", default=DEFAULT_SPEC_PATH)
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--report-path", default=DEFAULT_REPORT_PATH)
    parser.add_argument("--max-rows", type=int)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    input_path = Path(args.input) if args.input else find_latest_input()
    summary = analyze_matrix_followup_dominance(
        input_path=input_path,
        spec_path=args.spec_path,
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
                    "families": summary.get("families"),
                    "cohort_statuses": [
                        {
                            "cohort_key": row.get("cohort_key"),
                            "audit_status": row.get("audit_status"),
                            "audit_blockers": row.get("audit_blockers"),
                        }
                        for row in summary.get("cohorts", [])
                    ],
                    "report_path": summary.get("report_path"),
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

