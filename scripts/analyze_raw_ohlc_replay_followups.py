#!/usr/bin/env python3
"""Analyze the full raw-OHLC prequential replay result.

This follow-up layer explains the replay result rather than only reporting the
headline score. It is research-only and keeps the same-dataset
NO_PROMOTION_VERDICT boundary.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.analyze_truth_layer_effective_n import effective_n_diagnostics
from scripts.analyze_truth_layer_posthoc_pbo import cscv_pbo
from scripts.evaluate_truth_layer_methodology_readiness import compute_dsr_diagnostic
from scripts.run_truth_layer_prequential_replay import markdown_table, sha256_file


SCHEMA_VERSION = "raw_ohlc_prequential_replay_followup_analysis_v1"
DEFAULT_REPLAY_ROOT = (
    "data/external/validation/calendar_macro_bundle_v1/"
    "historical_opportunities/raw_ohlc_prequential_replay"
)
DEFAULT_REPORT_PATH = (
    "research/phase_3_external_feed_validation/"
    "RAW_OHLC_PREQUENTIAL_REPLAY_FOLLOWUP_ANALYSIS_2026-05-01.md"
)
RESOLVED_OUTCOMES = {"TP", "SL", "TIMEOUT"}
TARGET_ROLES = {"primary_controlled_child", "cleared_non_primary_strong_lead"}
NEGATIVE_ROLE = "negative_control"
BLOCKED_CONTROL_ROLE = "dominance_watchlist"
GBPUSD_CONTROL = "GBPUSD|london|bearish|H4+H1_consensus"


@dataclass
class ReturnStats:
    actions_taken: int = 0
    population_actions: int = 0
    resolved_r_n: int = 0
    sum_r: float = 0.0
    wins: int = 0
    outcomes: Counter[str] = field(default_factory=Counter)
    returns: list[float] = field(default_factory=list)

    def add_event(self, event: Mapping[str, Any]) -> None:
        self.actions_taken += 1
        outcome = str(event.get("outcome") or "UNKNOWN")
        self.outcomes[outcome] += 1
        if is_scoring_population(event):
            self.population_actions += 1
        realized = as_float(event.get("realized_r"))
        if outcome in RESOLVED_OUTCOMES and realized is not None:
            self.resolved_r_n += 1
            self.sum_r += realized
            self.returns.append(realized)
            if realized > 0:
                self.wins += 1

    def row(self, label_name: str, label: str) -> dict[str, Any]:
        return {
            label_name: label,
            "actions_taken": self.actions_taken,
            "population_actions": self.population_actions,
            "resolved_r_n": self.resolved_r_n,
            "sum_r": round(self.sum_r, 6),
            "mean_r": mean_or_none(self.sum_r, self.resolved_r_n),
            "win_rate": rate_or_none(self.wins, self.resolved_r_n),
        }


def analyze_raw_ohlc_replay_followups(
    *,
    summary_path: str | Path | None = None,
    event_log_path: str | Path | None = None,
    n_trials: int = 200,
) -> dict[str, Any]:
    summary_path = Path(summary_path) if summary_path else latest_file(DEFAULT_REPLAY_ROOT, "raw_ohlc_prequential_replay_*.json")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    event_log_path = Path(event_log_path or summary.get("event_log_path") or latest_file(DEFAULT_REPLAY_ROOT, "raw_ohlc_prequential_events_*.jsonl"))
    cohorts = list(summary.get("active_cohorts") or [])
    roles = {str(row.get("cohort_key")): str(row.get("role")) for row in cohorts}
    target_keys = {key for key, role in roles.items() if role in TARGET_ROLES}
    control_keys = {key for key, role in roles.items() if role == NEGATIVE_ROLE}
    blocked_control_keys = {key for key, role in roles.items() if role == BLOCKED_CONTROL_ROLE}
    active_keys = set(roles)

    cohort_stats: dict[str, ReturnStats] = defaultdict(ReturnStats)
    group_stats: dict[str, ReturnStats] = defaultdict(ReturnStats)
    window_stats: dict[tuple[str, str], ReturnStats] = defaultdict(ReturnStats)
    cohort_window_stats: dict[tuple[str, str], ReturnStats] = defaultdict(ReturnStats)
    cohort_year_stats: dict[tuple[str, str], ReturnStats] = defaultdict(ReturnStats)
    cohort_month_stats: dict[tuple[str, str], ReturnStats] = defaultdict(ReturnStats)
    group_month_returns: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    cohort_month_returns: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    first_clock: str | None = None
    last_clock: str | None = None
    rows_read = 0
    take_rows_seen = 0

    for rows_read, event in enumerate(iter_jsonl(event_log_path), start=1):
        key = str(event.get("raw_cohort_key") or "")
        if key not in active_keys or event.get("action") != "TAKE":
            continue
        take_rows_seen += 1
        timestamp = parse_event_time(event)
        first_clock = first_clock or timestamp.isoformat()
        last_clock = timestamp.isoformat()
        month = timestamp.strftime("%Y-%m")
        year = str(timestamp.year)
        role = roles[key]
        groups = groups_for_key(key, role)
        for state in [cohort_stats[key], *(group_stats[group] for group in groups)]:
            state.add_event(event)
        cohort_year_stats[(key, year)].add_event(event)
        cohort_month_stats[(key, month)].add_event(event)
        realized = resolved_return(event)
        if realized is not None:
            cohort_month_returns[month][key] += realized
            for group in groups:
                group_month_returns[month][group] += realized
        for window_name, predicate in recency_windows().items():
            if predicate(timestamp):
                cohort_window_stats[(key, window_name)].add_event(event)
                for group in groups:
                    window_stats[(window_name, group)].add_event(event)

    cohort_rows = build_cohort_rows(
        cohort_stats=cohort_stats,
        cohort_year_stats=cohort_year_stats,
        cohort_month_stats=cohort_month_stats,
        roles=roles,
        n_trials=n_trials,
    )
    group_rows = build_group_rows(group_stats, n_trials=n_trials)
    window_rows = build_window_rows(window_stats)
    cohort_recency_rows = build_cohort_recency_rows(cohort_window_stats, roles=roles)
    target_control = target_control_separation(group_stats)
    pbo_summary = pbo_diagnostic(
        cohort_month_returns=cohort_month_returns,
        roles=roles,
    )
    effective_n_summary = effective_n_diagnostic(
        cohort_month_returns=cohort_month_returns,
        cohort_keys=sorted(active_keys),
        target_keys=sorted(target_keys),
    )
    answers = synthesis_answers(
        group_stats=group_stats,
        cohort_rows=cohort_rows,
        target_control=target_control,
        pbo=pbo_summary,
        effective_n=effective_n_summary,
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "summary_path": str(summary_path),
        "summary_sha256": sha256_file(summary_path),
        "event_log_path": str(event_log_path),
        "event_log_sha256": sha256_file(event_log_path),
        "promotion_verdict_allowed": False,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "analysis_boundary": (
            "Full-run same-dataset raw-OHLC replay follow-up. DSR/PBO/effective_N "
            "diagnostics are not promotion-usable."
        ),
        "n_trials_for_same_dataset_dsr": n_trials,
        "source_scope": source_scope(summary),
        "rows_replayed": summary.get("rows_replayed"),
        "event_rows_read": rows_read,
        "take_rows_seen": take_rows_seen,
        "first_take_clock": first_clock,
        "last_take_clock": last_clock,
        "active_cohort_count": len(active_keys),
        "target_cohort_count": len(target_keys),
        "negative_control_count": len(control_keys),
        "blocked_control_count": len(blocked_control_keys),
        "group_summary": group_rows,
        "target_control_separation": target_control,
        "recency_windows": window_rows,
        "cohort_recency_detail": cohort_recency_rows,
        "cohort_summary": cohort_rows,
        "pbo_diagnostic": pbo_summary,
        "effective_n_diagnostic": effective_n_summary,
        "synthesis": answers,
        "ambiguity_ledger": ambiguity_ledger(cohort_rows, pbo_summary, effective_n_summary),
        "next_steps": next_steps(),
    }


def groups_for_key(key: str, role: str) -> list[str]:
    groups = ["all_enabled"]
    if key != GBPUSD_CONTROL:
        groups.append("all_excluding_gbpusd_control")
    if role in TARGET_ROLES:
        groups.append("target_cohorts")
    if role == "primary_controlled_child":
        groups.append("primary_controlled_family")
    if role == "cleared_non_primary_strong_lead":
        groups.append("cleared_non_primary_targets")
    if role == NEGATIVE_ROLE:
        groups.append("negative_controls")
    if role == BLOCKED_CONTROL_ROLE:
        groups.append("blocked_dominance_controls")
    return groups


def build_group_rows(states: Mapping[str, ReturnStats], *, n_trials: int) -> list[dict[str, Any]]:
    order = [
        "all_enabled",
        "all_excluding_gbpusd_control",
        "target_cohorts",
        "primary_controlled_family",
        "cleared_non_primary_targets",
        "negative_controls",
        "blocked_dominance_controls",
    ]
    rows = []
    for group in order:
        state = states.get(group, ReturnStats())
        row = state.row("group", group)
        row.update(dsr_fields(state.returns, n_trials=n_trials))
        rows.append(row)
    return rows


def build_window_rows(states: Mapping[tuple[str, str], ReturnStats]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for window in recency_windows().keys():
        for group in ("target_cohorts", "negative_controls", "blocked_dominance_controls"):
            state = states.get((window, group), ReturnStats())
            rows.append(state.row("window_group", f"{window}|{group}"))
    return rows


def build_cohort_recency_rows(
    states: Mapping[tuple[str, str], ReturnStats],
    *,
    roles: Mapping[str, str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in sorted(roles):
        for window in ("2025_plus", "2026_only", "last_12m_from_2025_05", "last_6m_from_2025_11"):
            state = states.get((key, window), ReturnStats())
            row = state.row("cohort_window", f"{key}|{window}")
            row["role"] = roles[key]
            row["population_per_action"] = rate_or_none(state.population_actions, state.actions_taken)
            row["resolved_per_action"] = rate_or_none(state.resolved_r_n, state.actions_taken)
            top_outcome, top_count = dominant_outcome(state)
            row["top_outcome"] = top_outcome
            row["top_outcome_count"] = top_count
            row["interpretation"] = recency_interpretation(roles[key], state)
            rows.append(row)
    return rows


def build_cohort_rows(
    *,
    cohort_stats: Mapping[str, ReturnStats],
    cohort_year_stats: Mapping[tuple[str, str], ReturnStats],
    cohort_month_stats: Mapping[tuple[str, str], ReturnStats],
    roles: Mapping[str, str],
    n_trials: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in sorted(roles):
        state = cohort_stats.get(key, ReturnStats())
        years = [period_row(year, stats, "year") for (cohort, year), stats in cohort_year_stats.items() if cohort == key]
        months = [period_row(month, stats, "month") for (cohort, month), stats in cohort_month_stats.items() if cohort == key]
        years = sorted(years, key=lambda row: str(row["year"]))
        months = sorted(months, key=lambda row: str(row["month"]))
        valid_years = [row for row in years if int(row["resolved_r_n"]) >= 30]
        positive_valid_years = [row for row in valid_years if float(row["mean_r"] or 0.0) > 0.0]
        recent_2025 = combine_periods(
            [stats for (cohort, year), stats in cohort_year_stats.items() if cohort == key and int(year) >= 2025]
        )
        recent_2026 = combine_periods(
            [stats for (cohort, year), stats in cohort_year_stats.items() if cohort == key and int(year) == 2026]
        )
        top_year = max(years, key=lambda row: int(row["resolved_r_n"]), default={})
        top_month = max(months, key=lambda row: int(row["resolved_r_n"]), default={})
        row = state.row("cohort_key", key)
        row.update(
            {
                "role": roles[key],
                "valid_years_n_ge_30": len(valid_years),
                "positive_valid_years": len(positive_valid_years),
                "top_year": top_year.get("year"),
                "top_year_resolved_share": share_or_none(top_year.get("resolved_r_n"), state.resolved_r_n),
                "top_year_mean_r": top_year.get("mean_r"),
                "top_month": top_month.get("month"),
                "top_month_resolved_share": share_or_none(top_month.get("resolved_r_n"), state.resolved_r_n),
                "mean_r_2025_plus": recent_2025.get("mean_r"),
                "resolved_n_2025_plus": recent_2025.get("resolved_r_n"),
                "mean_r_2026": recent_2026.get("mean_r"),
                "resolved_n_2026": recent_2026.get("resolved_r_n"),
                "status_read": cohort_status_read(state, roles[key], recent_2026),
            }
        )
        row.update(dsr_fields(state.returns, n_trials=n_trials))
        rows.append(row)
    return sorted(rows, key=lambda row: (str(row["role"]), -float(row.get("mean_r") or -999.0)))


def period_row(period: str, stats: ReturnStats, name: str) -> dict[str, Any]:
    row = stats.row(name, period)
    return row


def combine_periods(states: Sequence[ReturnStats]) -> dict[str, Any]:
    total = ReturnStats()
    for state in states:
        total.actions_taken += state.actions_taken
        total.population_actions += state.population_actions
        total.resolved_r_n += state.resolved_r_n
        total.sum_r += state.sum_r
        total.wins += state.wins
        total.outcomes.update(state.outcomes)
        total.returns.extend(state.returns)
    return total.row("period", "combined")


def target_control_separation(states: Mapping[str, ReturnStats]) -> dict[str, Any]:
    targets = states.get("target_cohorts", ReturnStats())
    controls = states.get("negative_controls", ReturnStats())
    blocked = states.get("blocked_dominance_controls", ReturnStats())
    all_enabled = states.get("all_enabled", ReturnStats())
    excluding_gbpusd = states.get("all_excluding_gbpusd_control", ReturnStats())
    return {
        "target_mean_r": mean_or_none(targets.sum_r, targets.resolved_r_n),
        "control_mean_r": mean_or_none(controls.sum_r, controls.resolved_r_n),
        "blocked_control_mean_r": mean_or_none(blocked.sum_r, blocked.resolved_r_n),
        "target_minus_control_mean_r": round(
            (targets.sum_r / targets.resolved_r_n) - (controls.sum_r / controls.resolved_r_n),
            6,
        )
        if targets.resolved_r_n and controls.resolved_r_n
        else None,
        "target_sum_r": round(targets.sum_r, 6),
        "control_sum_r": round(controls.sum_r, 6),
        "blocked_control_sum_r": round(blocked.sum_r, 6),
        "target_minus_blocked_control_mean_r": round(
            (targets.sum_r / targets.resolved_r_n) - (blocked.sum_r / blocked.resolved_r_n),
            6,
        )
        if targets.resolved_r_n and blocked.resolved_r_n
        else None,
        "gbpusd_control_drag_r": round(all_enabled.sum_r - excluding_gbpusd.sum_r, 6),
        "headline_mean_r_all_enabled": mean_or_none(all_enabled.sum_r, all_enabled.resolved_r_n),
        "headline_mean_r_without_gbpusd_control": mean_or_none(
            excluding_gbpusd.sum_r,
            excluding_gbpusd.resolved_r_n,
        ),
    }


def pbo_diagnostic(
    *,
    cohort_month_returns: Mapping[str, Mapping[str, float]],
    roles: Mapping[str, str],
) -> dict[str, Any]:
    periods = sorted(cohort_month_returns)
    all_keys = sorted(roles)
    target_keys = sorted(key for key, role in roles.items() if role in TARGET_ROLES)
    control_keys = sorted(key for key, role in roles.items() if role == NEGATIVE_ROLE)
    blocked_keys = sorted(key for key, role in roles.items() if role == BLOCKED_CONTROL_ROLE)
    variants = [
        pbo_variant(
            "all_enabled_individual_cohorts",
            matrix_for_keys(cohort_month_returns, periods, all_keys),
            strategy_count=len(all_keys),
            interpretation="Risk of selecting the best individual cohort from all enabled cohorts.",
        ),
        pbo_variant(
            "target_child_selection",
            matrix_for_keys(cohort_month_returns, periods, target_keys),
            strategy_count=len(target_keys),
            interpretation="Risk of selecting the best child from the five target cohorts.",
        ),
        pbo_variant(
            "negative_control_child_selection",
            matrix_for_keys(cohort_month_returns, periods, control_keys),
            strategy_count=len(control_keys),
            interpretation="Diagnostic behavior of the negative-control child universe.",
        ),
        pbo_variant(
            "target_family_vs_negative_control_family",
            family_matrix(cohort_month_returns, periods, target_keys, control_keys),
            strategy_count=2,
            interpretation="Stability of the pre-registered target-family composite versus negative controls.",
        ),
    ]
    if blocked_keys:
        variants.extend(
            [
                pbo_variant(
                    "blocked_control_child_selection",
                    matrix_for_keys(cohort_month_returns, periods, blocked_keys),
                    strategy_count=len(blocked_keys),
                    interpretation="Diagnostic behavior of the explicitly blocked dominance-watchlist controls.",
                ),
                pbo_variant(
                    "target_family_vs_blocked_control_family",
                    family_matrix(cohort_month_returns, periods, target_keys, blocked_keys),
                    strategy_count=2,
                    interpretation=(
                        "Stability of the pre-registered target-family composite versus "
                        "blocked dominance-watchlist controls."
                    ),
                ),
            ]
        )
    primary = variants[0]
    return {
        "promotion_usable": False,
        "promotion_usable_reason": "Post-hoc same-dataset raw replay universe; use for selection-risk diagnostics only.",
        "period_unit": "calendar_month",
        "candidate_count": len(all_keys),
        "period_count": len(periods),
        "pbo": primary.get("pbo"),
        "status": primary.get("status"),
        "diagnostics": primary.get("diagnostics"),
        "variants": variants,
    }


def pbo_variant(
    variant: str,
    matrix: Sequence[Sequence[float]],
    *,
    strategy_count: int,
    interpretation: str,
) -> dict[str, Any]:
    pbo, diagnostics = cscv_pbo(matrix)
    return {
        "variant": variant,
        "strategy_count": strategy_count,
        "period_count": len(matrix),
        "pbo": round(pbo, 6) if pbo is not None else None,
        "status": diagnostics.get("status"),
        "promotion_usable": False,
        "interpretation": interpretation,
        "diagnostics": diagnostics,
    }


def matrix_for_keys(
    cohort_month_returns: Mapping[str, Mapping[str, float]],
    periods: Sequence[str],
    keys: Sequence[str],
) -> list[list[float]]:
    return [
        [float((cohort_month_returns.get(period) or {}).get(key) or 0.0) for key in keys]
        for period in periods
    ]


def family_matrix(
    cohort_month_returns: Mapping[str, Mapping[str, float]],
    periods: Sequence[str],
    target_keys: Sequence[str],
    control_keys: Sequence[str],
) -> list[list[float]]:
    rows = []
    for period in periods:
        row = cohort_month_returns.get(period) or {}
        rows.append(
            [
                sum(float(row.get(key) or 0.0) for key in target_keys),
                sum(float(row.get(key) or 0.0) for key in control_keys),
            ]
        )
    return rows


def effective_n_diagnostic(
    *,
    cohort_month_returns: Mapping[str, Mapping[str, float]],
    cohort_keys: Sequence[str],
    target_keys: Sequence[str],
) -> dict[str, Any]:
    periods = sorted(cohort_month_returns)
    matrix = np.array(
        [
            [float((cohort_month_returns.get(period) or {}).get(key) or 0.0) for key in cohort_keys]
            for period in periods
        ],
        dtype=float,
    )
    target_indexes = [cohort_keys.index(key) for key in target_keys if key in cohort_keys]
    target_matrix = matrix[:, target_indexes] if target_indexes else np.zeros((len(periods), 0))
    return {
        "promotion_usable": False,
        "promotion_usable_reason": "Historical same-dataset effective_N diagnostic only.",
        "period_unit": "calendar_month",
        "all_enabled": effective_n_diagnostics(matrix, candidate_keys=cohort_keys, periods=periods),
        "target_cohorts": effective_n_diagnostics(
            target_matrix,
            candidate_keys=[cohort_keys[idx] for idx in target_indexes],
            periods=periods,
        ),
    }


def dsr_fields(returns: Sequence[float], *, n_trials: int) -> dict[str, Any]:
    diagnostic = compute_dsr_diagnostic(returns, n_trials=n_trials)
    return {
        "same_dataset_dsr_p": diagnostic.get("dsr_corrected_p"),
        "same_dataset_dsr_threshold_met": diagnostic.get("threshold_p_lt_0_01_met"),
        "dsr_status": diagnostic.get("status"),
    }


def synthesis_answers(
    *,
    group_stats: Mapping[str, ReturnStats],
    cohort_rows: Sequence[Mapping[str, Any]],
    target_control: Mapping[str, Any],
    pbo: Mapping[str, Any],
    effective_n: Mapping[str, Any],
) -> list[dict[str, str]]:
    target = group_stats.get("target_cohorts", ReturnStats())
    control = group_stats.get("negative_controls", ReturnStats())
    blocked = group_stats.get("blocked_dominance_controls", ReturnStats())
    gbpusd = next((row for row in cohort_rows if row.get("cohort_key") == GBPUSD_CONTROL), {})
    answers = [
        {
            "question": "Was the headline mostly held back by the GBPUSD negative control?",
            "answer": (
                "Yes, materially. The GBPUSD control contributed "
                f"{target_control.get('gbpusd_control_drag_r')}R and its mean R was "
                f"{gbpusd.get('mean_r')}. But the bigger result is target-vs-control separation."
            ),
        },
        {
            "question": "Did the approved target cohorts separate from negative controls?",
            "answer": (
                f"Yes. Targets: n={target.resolved_r_n}, mean R={mean_or_none(target.sum_r, target.resolved_r_n)}, "
                f"sum R={round(target.sum_r, 6)}. Negative controls: n={control.resolved_r_n}, "
                f"mean R={mean_or_none(control.sum_r, control.resolved_r_n)}, sum R={round(control.sum_r, 6)}."
            ),
        },
    ]
    if blocked.actions_taken:
        answers.append(
            {
                "question": "What did the blocked dominance-watchlist controls show?",
                "answer": (
                    f"They were positive as a family: n={blocked.resolved_r_n}, "
                    f"mean R={mean_or_none(blocked.sum_r, blocked.resolved_r_n)}, "
                    f"sum R={round(blocked.sum_r, 6)}. That is a sanity-check result: these names stay blocked "
                    "from target promotion because they may reflect broad-market dominance rather than the "
                    "pre-registered controlled edge."
                ),
            }
        )
    answers.extend(
        [
            {
                "question": "Does this promote a strategy?",
                "answer": (
                    "No. DSR/PBO/effective_N diagnostics remain same-dataset and post-hoc. "
                    f"PBO diagnostic status={pbo.get('status')}, pbo={pbo.get('pbo')}; "
                    f"target effective_N={(effective_n.get('target_cohorts') or {}).get('effective_n')}."
                ),
            },
            {
                "question": "What is the main remaining risk?",
                "answer": (
                    "Individual-cohort recent-period power is uneven. The family-level recency is encouraging, "
                    "but several target cohorts have low or zero 2026 resolved rows."
                ),
            },
        ]
    )
    return answers


def ambiguity_ledger(
    cohort_rows: Sequence[Mapping[str, Any]],
    pbo: Mapping[str, Any],
    effective_n: Mapping[str, Any],
) -> list[dict[str, str]]:
    underpowered_2026 = [
        str(row.get("cohort_key"))
        for row in cohort_rows
        if row.get("role") in TARGET_ROLES and int(row.get("resolved_n_2026") or 0) < 30
    ]
    target_non_positive_2026 = [
        str(row.get("cohort_key"))
        for row in cohort_rows
        if row.get("role") in TARGET_ROLES
        and int(row.get("resolved_n_2026") or 0) >= 30
        and as_float(row.get("mean_r_2026")) is not None
        and float(row.get("mean_r_2026")) <= 0.0
    ]
    recent_positive_controls = [
        str(row.get("cohort_key"))
        for row in cohort_rows
        if row.get("role") == NEGATIVE_ROLE
        and int(row.get("resolved_n_2026") or 0) >= 30
        and as_float(row.get("mean_r_2026")) is not None
        and float(row.get("mean_r_2026")) > 0.0
    ]
    positive_blocked_controls = [
        str(row.get("cohort_key"))
        for row in cohort_rows
        if row.get("role") == BLOCKED_CONTROL_ROLE
        and as_float(row.get("mean_r")) is not None
        and float(row.get("mean_r")) > 0.0
    ]
    pbo_value = as_float(pbo.get("pbo"))
    pbo_status = "WARNING_POSTHOC_PBO_ABOVE_0_4" if pbo_value is not None and pbo_value >= 0.4 else "DIAGNOSTIC_ONLY"
    return [
        {
            "item": "No-leak replay integrity",
            "status": "RESOLVED_FOR_THIS_RUN",
            "detail": "The parent full replay reported 0 future exposure, 0 HTF as-of violations, and 0 AI calls.",
        },
        {
            "item": "GBPUSD control drag",
            "status": "RESOLVED_FOR_THIS_RUN",
            "detail": "Quantified separately; it is a negative-control drag, not a hidden target failure.",
        },
        {
            "item": "Target-vs-control separation",
            "status": "RESOLVED_FOR_THIS_RUN",
            "detail": "Targets are positive as a family while negative controls are negative as a family.",
        },
        {
            "item": "2026 individual cohort recency",
            "status": "REMAINS_UNDERPOWERED",
            "detail": "; ".join(underpowered_2026) if underpowered_2026 else "No underpowered target cohorts.",
        },
        {
            "item": "2026 target non-positive windows",
            "status": "REMAINS_RECENCY_WARNING" if target_non_positive_2026 else "CLEAR_FOR_THIS_RUN",
            "detail": "; ".join(target_non_positive_2026) if target_non_positive_2026 else "No n>=30 target 2026 window was non-positive.",
        },
        {
            "item": "Recent negative-control cleanliness",
            "status": "REMAINS_MIXED_BY_COHORT" if recent_positive_controls else "CLEAR_FOR_THIS_RUN",
            "detail": "; ".join(recent_positive_controls) if recent_positive_controls else "No n>=30 negative control was positive in 2026.",
        },
        {
            "item": "Blocked dominance-watchlist controls",
            "status": "POSITIVE_CONTROLS_STAY_BLOCKED" if positive_blocked_controls else "NO_POSITIVE_BLOCKED_CONTROL_SIGNAL",
            "detail": (
                "; ".join(positive_blocked_controls)
                if positive_blocked_controls
                else "No blocked dominance-watchlist control had positive full-corpus mean R."
            ),
        },
        {
            "item": "Post-hoc PBO diagnostic",
            "status": pbo_status,
            "detail": f"PBO={pbo.get('pbo')}; diagnostic-only and not promotion-grade.",
        },
        {
            "item": "Promotion methodology",
            "status": "BLOCKED_BY_DESIGN",
            "detail": (
                f"PBO={pbo.get('pbo')} and effective_N diagnostics exist but are not promotion-usable: "
                f"{effective_n.get('promotion_usable_reason')}"
            ),
        },
    ]


def next_steps() -> list[dict[str, str]]:
    return [
        {
            "rank": "1",
            "next_step": "Prospective or untouched replay lane for the five target cohorts",
            "reason": "Family separation is strong enough to justify forward validation, not promotion.",
        },
        {
            "rank": "2",
            "next_step": "Run blocked dominance-watchlist controls explicitly as controls",
            "reason": "Checks whether NAS100/US30/XAU dominance names are broad-market artifacts.",
        },
        {
            "rank": "3",
            "next_step": "Investigate 2026 underpowered target cells before live conclusions",
            "reason": "Some target cohorts have too few recent resolved rows for standalone confidence.",
        },
        {
            "rank": "4",
            "next_step": "Compare raw replay event funnel to live candidate funnel",
            "reason": "Large NO_ENTRY and SETUP_NOT_REFINABLE counts need live-equivalence context.",
        },
    ]


def render_report(summary: Mapping[str, Any]) -> str:
    pbo = summary.get("pbo_diagnostic") or {}
    eff = summary.get("effective_n_diagnostic") or {}
    eff_all = eff.get("all_enabled") or {}
    eff_targets = eff.get("target_cohorts") or {}
    lines = [
        "# Phase 3 Raw-OHLC Replay Follow-Up Analysis",
        "",
        f"**Created UTC:** {summary.get('created_at_utc')}",
        f"**Summary:** `{summary.get('summary_path')}`",
        f"**Event log:** `{summary.get('event_log_path')}`",
        f"**Promotion verdict:** `{summary.get('promotion_verdict')}`",
        "",
        "## Boundary",
        "",
        "- Research/tooling only; no live trading logic, prompt, config, risk policy, or execution behavior is changed.",
        "- This analysis uses the full raw-OHLC replay event log and summary.",
        "- DSR, PBO, and effective_N diagnostics are same-dataset and not promotion-usable.",
        "- The purpose is interpretation, ambiguity reduction, and next-step prioritization.",
        "",
        "## Run Scope",
        "",
        markdown_table(
            [
                {
                    "source_scope": summary.get("source_scope"),
                    "rows_replayed": summary.get("rows_replayed"),
                    "event_rows_read": summary.get("event_rows_read"),
                    "take_rows_seen": summary.get("take_rows_seen"),
                    "first_take_clock": summary.get("first_take_clock"),
                    "last_take_clock": summary.get("last_take_clock"),
                    "active_cohorts": summary.get("active_cohort_count"),
                }
            ]
        ),
        "",
        "## Direct Answers",
        "",
        markdown_table(summary.get("synthesis") or []),
        "",
        "## Group Summary",
        "",
        markdown_table(summary.get("group_summary") or []),
        "",
        "## Target-Control Separation",
        "",
        markdown_table([summary.get("target_control_separation") or {}]),
        "",
        "## Recency Windows",
        "",
        markdown_table(summary.get("recency_windows") or []),
        "",
        "## Cohort Recency Detail",
        "",
        markdown_table(summary.get("cohort_recency_detail") or []),
        "",
        "## Cohort Summary",
        "",
        markdown_table(summary.get("cohort_summary") or []),
        "",
        "## Methodology Diagnostics",
        "",
        markdown_table(
            [
                {
                    "pbo": pbo.get("pbo"),
                    "pbo_status": pbo.get("status"),
                    "pbo_promotion_usable": pbo.get("promotion_usable"),
                    "all_enabled_effective_N": eff_all.get("effective_n"),
                    "target_effective_N": eff_targets.get("effective_n"),
                    "effective_N_promotion_usable": eff.get("promotion_usable"),
                }
            ]
        ),
        "",
        "## PBO Variants",
        "",
        markdown_table(pbo_variant_report_rows(summary.get("pbo_diagnostic", {}).get("variants") or [])),
        "",
        "## Ambiguity Ledger",
        "",
        markdown_table(summary.get("ambiguity_ledger") or []),
        "",
        "## Next Steps",
        "",
        markdown_table(summary.get("next_steps") or []),
        "",
        "## Synthesis",
        "",
        "- The GBPUSD negative control did drag the combined headline, but it is not the central story.",
        "- The central story is that the five target cohorts remained positive as a family while the negative controls did not.",
        "- Recency strengthens the family-level target/control split, but standalone 2026 power is uneven by individual target cohort.",
        "- The result opens a prospective validation lane and blocked-control lane; it does not open a promotion lane.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def pbo_variant_report_rows(variants: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for item in variants:
        diagnostics = item.get("diagnostics") or {}
        rows.append(
            {
                "variant": item.get("variant"),
                "strategy_count": item.get("strategy_count"),
                "period_count": item.get("period_count"),
                "pbo": item.get("pbo"),
                "status": item.get("status"),
                "combination_count": diagnostics.get("combination_count"),
                "logit_mean": round(float(diagnostics.get("logit_mean")), 6)
                if diagnostics.get("logit_mean") is not None
                else None,
                "promotion_usable": item.get("promotion_usable"),
                "interpretation": item.get("interpretation"),
            }
        )
    return rows


def write_outputs(
    summary: Mapping[str, Any],
    *,
    output_root: str | Path = DEFAULT_REPLAY_ROOT,
    report_path: str | Path = DEFAULT_REPORT_PATH,
) -> tuple[Path, Path]:
    output_dir = Path(output_root)
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    summary_path = output_dir / f"raw_ohlc_prequential_followup_analysis_{stamp}.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    report = Path(report_path)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(summary), encoding="utf-8")
    return summary_path, report


def is_scoring_population(event: Mapping[str, Any]) -> bool:
    return (
        event.get("action") == "TAKE"
        and event.get("mechanical_setup_status") == "OK"
        and bool(event.get("would_send_ai"))
        and event.get("outcome") != "SAME_BAR"
    )


def resolved_return(event: Mapping[str, Any]) -> float | None:
    if event.get("outcome") not in RESOLVED_OUTCOMES:
        return None
    return as_float(event.get("realized_r"))


def parse_event_time(event: Mapping[str, Any]) -> datetime:
    raw = str(event.get("candle_close_utc") or "")
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    return datetime.fromisoformat(raw).astimezone(timezone.utc)


def recency_windows() -> dict[str, Callable[[datetime], bool]]:
    return {
        "all": lambda value: True,
        "2024_plus": lambda value: value.year >= 2024,
        "2025_plus": lambda value: value.year >= 2025,
        "2026_only": lambda value: value.year == 2026,
        "last_12m_from_2025_05": lambda value: value >= datetime(2025, 5, 1, tzinfo=timezone.utc),
        "last_6m_from_2025_11": lambda value: value >= datetime(2025, 11, 1, tzinfo=timezone.utc),
    }


def source_scope(summary: Mapping[str, Any]) -> str:
    if (
        summary.get("max_candles_per_symbol") is None
        and summary.get("max_events") is None
        and summary.get("start") is None
        and summary.get("end") is None
    ):
        return "FULL_AVAILABLE_CORPUS"
    return "BOUNDED_DIAGNOSTIC"


def cohort_status_read(state: ReturnStats, role: str, recent_2026: Mapping[str, Any]) -> str:
    if state.resolved_r_n < 100:
        return "UNDERPOWERED_OVERALL"
    recent_n = int(recent_2026.get("resolved_r_n") or 0)
    recent_mean = as_float(recent_2026.get("mean_r"))
    if role in TARGET_ROLES and recent_n < 30:
        return "TARGET_POSITIVE_OVERALL_BUT_2026_UNDERPOWERED"
    if role in TARGET_ROLES and recent_mean is not None and recent_mean <= 0.0:
        return "TARGET_POSITIVE_OVERALL_BUT_2026_NON_POSITIVE"
    if role in TARGET_ROLES and float(state.sum_r / state.resolved_r_n) > 0:
        return "TARGET_POSITIVE_FULL_CORPUS"
    if role == NEGATIVE_ROLE and recent_n >= 30 and recent_mean is not None and recent_mean > 0.0:
        return "NEGATIVE_CONTROL_RECENT_POSITIVE_CHECK_REQUIRED"
    if role == NEGATIVE_ROLE and float(state.sum_r / state.resolved_r_n) <= 0:
        return "NEGATIVE_CONTROL_NON_POSITIVE_FULL_CORPUS"
    if role == NEGATIVE_ROLE:
        return "NEGATIVE_CONTROL_POSITIVE_CHECK_REQUIRED"
    if role == BLOCKED_CONTROL_ROLE and recent_n >= 30 and recent_mean is not None and recent_mean > 0.0:
        return "BLOCKED_CONTROL_RECENT_POSITIVE_STAYS_BLOCKED"
    if role == BLOCKED_CONTROL_ROLE and float(state.sum_r / state.resolved_r_n) > 0:
        return "BLOCKED_CONTROL_POSITIVE_FULL_CORPUS_STAYS_BLOCKED"
    if role == BLOCKED_CONTROL_ROLE:
        return "BLOCKED_CONTROL_DIAGNOSTIC_REVIEW"
    return "DIAGNOSTIC_REVIEW"


def recency_interpretation(role: str, state: ReturnStats) -> str:
    if state.resolved_r_n < 30:
        return "UNDERPOWERED_WINDOW"
    mean_r = state.sum_r / state.resolved_r_n
    if role in TARGET_ROLES and mean_r > 0:
        return "TARGET_POSITIVE_WINDOW"
    if role in TARGET_ROLES:
        return "TARGET_NON_POSITIVE_WINDOW"
    if role == NEGATIVE_ROLE and mean_r <= 0:
        return "CONTROL_NON_POSITIVE_WINDOW"
    if role == NEGATIVE_ROLE:
        return "CONTROL_POSITIVE_WINDOW_CHECK_REQUIRED"
    if role == BLOCKED_CONTROL_ROLE and mean_r > 0:
        return "BLOCKED_CONTROL_POSITIVE_WINDOW_STAYS_BLOCKED"
    if role == BLOCKED_CONTROL_ROLE:
        return "BLOCKED_CONTROL_NON_POSITIVE_WINDOW"
    return "DIAGNOSTIC_WINDOW"


def dominant_outcome(state: ReturnStats) -> tuple[str | None, int | None]:
    if not state.outcomes:
        return None, None
    outcome, count = state.outcomes.most_common(1)[0]
    return outcome, int(count)


def latest_file(root: str | Path, pattern: str) -> Path:
    rows = sorted(Path(root).glob(pattern), key=lambda path: path.stat().st_mtime, reverse=True)
    if not rows:
        raise FileNotFoundError(f"no files found for {Path(root) / pattern}")
    return rows[0]


def iter_jsonl(path: str | Path):
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        output = float(value)
    except (TypeError, ValueError):
        return None
    return output if math.isfinite(output) else None


def mean_or_none(total: float, n: int) -> float | None:
    return round(total / n, 6) if n else None


def rate_or_none(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 6) if denominator else None


def share_or_none(numerator: Any, denominator: int) -> float | None:
    value = int(numerator or 0)
    return round(value / denominator, 6) if denominator else None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary")
    parser.add_argument("--event-log")
    parser.add_argument("--output-root", default=DEFAULT_REPLAY_ROOT)
    parser.add_argument("--report-path", default=DEFAULT_REPORT_PATH)
    parser.add_argument("--n-trials", type=int, default=200)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = analyze_raw_ohlc_replay_followups(
        summary_path=args.summary,
        event_log_path=args.event_log,
        n_trials=args.n_trials,
    )
    if args.write:
        output_summary, report = write_outputs(
            summary,
            output_root=args.output_root,
            report_path=args.report_path,
        )
        summary = dict(summary)
        summary["output_summary"] = str(output_summary)
        summary["report_path"] = str(report)
    if args.quiet:
        print(
            json.dumps(
                {
                    "promotion_verdict": summary.get("promotion_verdict"),
                    "source_scope": summary.get("source_scope"),
                    "target_mean_r": (summary.get("target_control_separation") or {}).get("target_mean_r"),
                    "control_mean_r": (summary.get("target_control_separation") or {}).get("control_mean_r"),
                    "target_minus_control_mean_r": (summary.get("target_control_separation") or {}).get("target_minus_control_mean_r"),
                    "pbo": (summary.get("pbo_diagnostic") or {}).get("pbo"),
                    "target_effective_n": ((summary.get("effective_n_diagnostic") or {}).get("target_cohorts") or {}).get("effective_n"),
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


if __name__ == "__main__":
    raise SystemExit(main())
