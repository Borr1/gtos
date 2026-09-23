#!/usr/bin/env python3
"""Forensic analysis of why Phase 3 path scaling V1 failed promotion.

This report stays inside V1. It does not implement structural levels, reentry,
or any live trading logic. It explains the fixed-R lock-only failure by
comparing the J46-J49 baseline against each V1 lock ladder on the same event
stream.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.analyze_raw_ohlc_replay_followups import groups_for_key, rate_or_none  # noqa: E402
from scripts.run_raw_ohlc_prequential_replay import git_commit_or_unknown, markdown_table, sha256_file  # noqa: E402


SCHEMA_VERSION = "raw_ohlc_path_scaling_v1_failure_forensics_v1"
DEFAULT_EVENT_LOG_PATH = (
    "data/external/validation/calendar_macro_bundle_v1/historical_opportunities/"
    "raw_ohlc_prequential_replay/path_ablation_v1_mtf/"
    "raw_ohlc_path_ablation_v1_mtf_events_20260501T192723Z.jsonl"
)
DEFAULT_REPORT_PATH = (
    "research/phase_3_external_feed_validation/"
    "RAW_OHLC_PATH_SCALING_V1_FAILURE_FORENSICS_2026-05-02.md"
)
DEFAULT_OUTPUT_ROOT = (
    "data/external/validation/calendar_macro_bundle_v1/historical_opportunities/"
    "raw_ohlc_prequential_replay/path_ablation_v1_mtf"
)
J46 = "J46_J49_ONLY"
BASE = "BASE_RAW_FIXED_TP"
LOCK_VARIANTS = [
    "PATH_LOCK_CONSERVATIVE_V0",
    "PATH_LOCK_HALF_GAIN_V0",
    "PATH_LOCK_EARLY_BE_V0",
]
ALL_VARIANTS = [BASE, J46, *LOCK_VARIANTS]
RESOLVED_OUTCOMES = {"TP", "SL", "TIMEOUT", "BE_STOP", "LOCK_STOP"}
LOCK_STOP_OUTCOMES = {"BE_STOP", "LOCK_STOP"}
GROUP_ORDER = [
    "all_enabled",
    "target_cohorts",
    "primary_controlled_family",
    "cleared_non_primary_targets",
    "negative_controls",
    "blocked_dominance_controls",
]
MFE_THRESHOLDS = (1.0, 1.5, 2.0, 3.0, 6.0)
CASEBOOK_LIMIT = 20
EPS = 1e-9
MECHANISMS = [
    "lock_rescued_loss_to_positive",
    "lock_reduced_loss_only",
    "lock_failed_to_improve_j46_nonpositive",
    "winner_truncated_to_nonpositive",
    "winner_truncated_but_positive",
    "lock_improved_positive_winner",
    "same_result",
]
TREATMENTS = ("exclude_unresolved", "samebar_breakeven", "samebar_pessimistic")
COST_R = 0.05


@dataclass
class PairStats:
    n: int = 0
    j46_sum: float = 0.0
    lock_sum: float = 0.0
    delta_sum: float = 0.0
    lock_better_n: int = 0
    lock_better_sum: float = 0.0
    j46_better_n: int = 0
    j46_better_sum: float = 0.0
    tie_n: int = 0
    j46_positive_n: int = 0
    lock_positive_n: int = 0
    both_positive_n: int = 0
    both_nonpositive_n: int = 0
    lock_triggered_n: int = 0
    lock_triggered_positive_n: int = 0
    lock_triggered_nonpositive_n: int = 0
    truncation_n: int = 0
    truncation_lost_r: float = 0.0
    large_truncation_n: int = 0
    rescued_j46_nonpositive_n: int = 0
    rescued_to_positive_n: int = 0
    lock_made_j46_positive_nonpositive_n: int = 0

    def add(self, *, j_row: Mapping[str, Any], lock_row: Mapping[str, Any], j_value: float, lock_value: float) -> None:
        delta = lock_value - j_value
        self.n += 1
        self.j46_sum += j_value
        self.lock_sum += lock_value
        self.delta_sum += delta
        if j_value > 0.0:
            self.j46_positive_n += 1
        if lock_value > 0.0:
            self.lock_positive_n += 1
        if j_value > 0.0 and lock_value > 0.0:
            self.both_positive_n += 1
        if j_value <= 0.0 and lock_value <= 0.0:
            self.both_nonpositive_n += 1
        if lock_row.get("locks_triggered"):
            self.lock_triggered_n += 1
            if lock_value > 0.0:
                self.lock_triggered_positive_n += 1
            else:
                self.lock_triggered_nonpositive_n += 1
        if delta > EPS:
            self.lock_better_n += 1
            self.lock_better_sum += delta
        elif delta < -EPS:
            self.j46_better_n += 1
            self.j46_better_sum += -delta
        else:
            self.tie_n += 1

        lock_outcome = str(lock_row.get("v1_outcome") or "")
        if lock_outcome in LOCK_STOP_OUTCOMES and j_value > lock_value + EPS:
            self.truncation_n += 1
            self.truncation_lost_r += j_value - lock_value
            if j_value >= 3.0:
                self.large_truncation_n += 1
        if j_value <= 0.0 and lock_value > j_value + EPS:
            self.rescued_j46_nonpositive_n += 1
            if lock_value > 0.0:
                self.rescued_to_positive_n += 1
        if j_value > 0.0 and lock_value <= 0.0:
            self.lock_made_j46_positive_nonpositive_n += 1

    def row(self, *, variant_id: str, scope: str, key: str) -> dict[str, Any]:
        return {
            "variant_id": variant_id,
            "scope": scope,
            "key": key,
            "paired_resolved_n": self.n,
            "j46_mean_r": round(self.j46_sum / self.n, 6) if self.n else None,
            "lock_mean_r": round(self.lock_sum / self.n, 6) if self.n else None,
            "mean_delta_lock_minus_j46": round(self.delta_sum / self.n, 6) if self.n else None,
            "sum_delta_lock_minus_j46": round(self.delta_sum, 6),
            "lock_better_rate": rate_or_none(self.lock_better_n, self.n),
            "j46_better_rate": rate_or_none(self.j46_better_n, self.n),
            "lock_better_n": self.lock_better_n,
            "j46_better_n": self.j46_better_n,
            "tie_n": self.tie_n,
            "j46_positive_n": self.j46_positive_n,
            "lock_positive_n": self.lock_positive_n,
            "both_positive_n": self.both_positive_n,
            "both_nonpositive_n": self.both_nonpositive_n,
            "lock_triggered_n": self.lock_triggered_n,
            "lock_triggered_rate": rate_or_none(self.lock_triggered_n, self.n),
            "lock_triggered_positive_n": self.lock_triggered_positive_n,
            "lock_triggered_nonpositive_n": self.lock_triggered_nonpositive_n,
            "truncation_n": self.truncation_n,
            "truncation_lost_r": round(self.truncation_lost_r, 6),
            "truncation_lost_r_per_pair": round(self.truncation_lost_r / self.n, 6) if self.n else None,
            "large_truncation_n": self.large_truncation_n,
            "rescued_j46_nonpositive_n": self.rescued_j46_nonpositive_n,
            "rescued_to_positive_n": self.rescued_to_positive_n,
            "lock_made_j46_positive_nonpositive_n": self.lock_made_j46_positive_nonpositive_n,
        }


@dataclass
class MfeStats:
    resolved_n: int = 0
    nonpositive_n: int = 0
    positive_n: int = 0
    nonpositive_mfe_values: list[float] = None  # type: ignore[assignment]
    threshold_hits: Counter[float] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.nonpositive_mfe_values is None:
            self.nonpositive_mfe_values = []
        if self.threshold_hits is None:
            self.threshold_hits = Counter()

    def add_j46(self, row: Mapping[str, Any]) -> None:
        value = resolved_value(row)
        if value is None:
            return
        self.resolved_n += 1
        if value > 0:
            self.positive_n += 1
            return
        self.nonpositive_n += 1
        mfe = as_float(row.get("mfe_r"))
        if mfe is None:
            return
        self.nonpositive_mfe_values.append(mfe)
        for threshold in MFE_THRESHOLDS:
            if mfe >= threshold:
                self.threshold_hits[threshold] += 1

    def row(self, *, scope: str, key: str) -> dict[str, Any]:
        output = {
            "scope": scope,
            "key": key,
            "j46_resolved_n": self.resolved_n,
            "j46_nonpositive_n": self.nonpositive_n,
            "j46_positive_n": self.positive_n,
            "nonpositive_mfe_avg": round(sum(self.nonpositive_mfe_values) / len(self.nonpositive_mfe_values), 6)
            if self.nonpositive_mfe_values
            else None,
            "nonpositive_mfe_p50": quantile(self.nonpositive_mfe_values, 0.50),
            "nonpositive_mfe_p75": quantile(self.nonpositive_mfe_values, 0.75),
        }
        for threshold in MFE_THRESHOLDS:
            hits = self.threshold_hits[threshold]
            output[f"nonpositive_mfe_ge_{threshold:g}_n"] = hits
            output[f"nonpositive_mfe_ge_{threshold:g}_rate"] = rate_or_none(hits, self.nonpositive_n)
        return output


def run_failure_forensics(
    *,
    event_log_path: str | Path = DEFAULT_EVENT_LOG_PATH,
) -> dict[str, Any]:
    events = load_events(event_log_path)
    pivots = pivot_events(events)
    pair_stats, unresolved_stats = pairwise_failure_stats(pivots)
    mfe_stats = mfe_opportunity_stats(pivots)
    transition_counts = outcome_transition_counts(pivots)
    cohort_rows = cohort_pair_rows(pair_stats)
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "code_commit": git_commit_or_unknown(),
        "event_log_path": str(Path(event_log_path)),
        "event_log_sha256": sha256_file(event_log_path),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "scope": "FULL_AVAILABLE_CORPUS_V1_EVENT_LOG",
        "research_boundary": [
            "Research/tooling only",
            "No live trading logic changes",
            "No prompt edits",
            "No parameter optimization",
            "No paid AI/API calls",
            "No V2/V3 implementation",
        ],
        "event_rows": len(events),
        "unique_setups": len(pivots),
        "variant_outcome_summary": variant_outcome_rows(events),
        "mtf_resolution_summary": mtf_resolution_rows(events),
        "samebar_stress_delta_summary": samebar_stress_delta_rows(events),
        "pairwise_variant_summary": pairwise_variant_rows(pair_stats),
        "pairwise_group_summary": pairwise_group_rows(pair_stats),
        "pairwise_timeframe_summary": pairwise_timeframe_rows(pair_stats),
        "pairwise_cohort_summary": cohort_rows,
        "mechanism_group_summary": mechanism_summary_rows(pivots, scope="group"),
        "mechanism_timeframe_summary": mechanism_summary_rows(pivots, scope="timeframe"),
        "top_j46_better_cohorts": top_cohort_rows(cohort_rows, direction="j46"),
        "top_lock_better_cohorts": top_cohort_rows(cohort_rows, direction="lock"),
        "unresolved_pair_summary": unresolved_pair_rows(unresolved_stats),
        "outcome_transition_summary": transition_rows(transition_counts),
        "mfe_opportunity_summary": mfe_rows(mfe_stats),
        "casebook": casebook_rows(pivots),
    }
    summary["direct_answers"] = direct_answers(summary)
    summary["what_worked"] = what_worked(summary)
    summary["what_failed"] = what_failed(summary)
    summary["root_cause_summary"] = root_cause_summary(summary)
    summary["unanswered_questions_status"] = unanswered_questions_status(summary)
    summary["ambiguity_ledger"] = ambiguity_ledger(summary)
    summary["opened_questions"] = opened_questions(summary)
    summary["limitations"] = limitations(summary)
    summary["deeper_dive_candidates"] = deeper_dive_candidates(summary)
    summary["next_steps"] = next_steps(summary)
    summary["synthesis"] = synthesis(summary)
    return summary


def load_events(path: str | Path) -> list[dict[str, Any]]:
    rows = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    if not rows:
        raise ValueError(f"no rows loaded from {path}")
    return rows


def pivot_events(events: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, Mapping[str, Any]]]:
    pivots: dict[str, dict[str, Mapping[str, Any]]] = defaultdict(dict)
    for row in events:
        event_key = str(row.get("event_key") or "")
        variant = str(row.get("variant_id") or "")
        if event_key and variant:
            pivots[event_key][variant] = row
    return dict(pivots)


def pairwise_failure_stats(
    pivots: Mapping[str, Mapping[str, Mapping[str, Any]]]
) -> tuple[dict[tuple[str, str, str], PairStats], Counter[tuple[str, str]]]:
    stats: dict[tuple[str, str, str], PairStats] = defaultdict(PairStats)
    unresolved: Counter[tuple[str, str]] = Counter()
    for variants in pivots.values():
        j_row = variants.get(J46)
        if not j_row:
            continue
        j_value = resolved_value(j_row)
        metadata_groups = groups_for_row(j_row)
        timeframe = str(j_row.get("v1_selected_timeframe") or "UNKNOWN")
        cohort_key = str(j_row.get("raw_cohort_key") or "UNKNOWN")
        role = str(j_row.get("role") or "unknown")
        for lock_variant in LOCK_VARIANTS:
            lock_row = variants.get(lock_variant)
            if not lock_row:
                continue
            lock_value = resolved_value(lock_row)
            if j_value is not None and lock_value is not None:
                for group in metadata_groups:
                    stats[(lock_variant, "group", group)].add(
                        j_row=j_row,
                        lock_row=lock_row,
                        j_value=j_value,
                        lock_value=lock_value,
                    )
                stats[(lock_variant, "timeframe", timeframe)].add(
                    j_row=j_row,
                    lock_row=lock_row,
                    j_value=j_value,
                    lock_value=lock_value,
                )
                stats[(lock_variant, "cohort", f"{cohort_key}|{role}")].add(
                    j_row=j_row,
                    lock_row=lock_row,
                    j_value=j_value,
                    lock_value=lock_value,
                )
                continue

            j_outcome = str(j_row.get("v1_outcome") or "UNKNOWN")
            lock_outcome = str(lock_row.get("v1_outcome") or "UNKNOWN")
            if j_value is not None and lock_outcome == "SAME_BAR":
                unresolved[(lock_variant, "j46_resolved_lock_samebar")] += 1
                unresolved[(lock_variant, f"j46_resolved_lock_samebar_j46_r_bucket__{bucket_value(j_value)}")] += 1
            elif lock_value is not None and j_outcome == "SAME_BAR":
                unresolved[(lock_variant, "lock_resolved_j46_samebar")] += 1
            elif j_outcome == "SAME_BAR" and lock_outcome == "SAME_BAR":
                unresolved[(lock_variant, "both_samebar")] += 1
            elif j_value is not None and lock_value is None:
                unresolved[(lock_variant, f"j46_resolved_lock_{lock_outcome}")] += 1
            elif lock_value is not None and j_value is None:
                unresolved[(lock_variant, f"lock_resolved_j46_{j_outcome}")] += 1
    return dict(stats), unresolved


def mfe_opportunity_stats(
    pivots: Mapping[str, Mapping[str, Mapping[str, Any]]]
) -> dict[tuple[str, str], MfeStats]:
    stats: dict[tuple[str, str], MfeStats] = defaultdict(MfeStats)
    for variants in pivots.values():
        j_row = variants.get(J46)
        if not j_row:
            continue
        for group in groups_for_row(j_row):
            stats[("group", group)].add_j46(j_row)
        stats[("timeframe", str(j_row.get("v1_selected_timeframe") or "UNKNOWN"))].add_j46(j_row)
        cohort_key = str(j_row.get("raw_cohort_key") or "UNKNOWN")
        role = str(j_row.get("role") or "unknown")
        stats[("cohort", f"{cohort_key}|{role}")].add_j46(j_row)
    return dict(stats)


def outcome_transition_counts(
    pivots: Mapping[str, Mapping[str, Mapping[str, Any]]]
) -> Counter[tuple[str, str, str]]:
    counts: Counter[tuple[str, str, str]] = Counter()
    for variants in pivots.values():
        j_row = variants.get(J46)
        if not j_row:
            continue
        j_outcome = str(j_row.get("v1_outcome") or "UNKNOWN")
        for lock_variant in LOCK_VARIANTS:
            lock_row = variants.get(lock_variant)
            if not lock_row:
                continue
            lock_outcome = str(lock_row.get("v1_outcome") or "UNKNOWN")
            counts[(lock_variant, j_outcome, lock_outcome)] += 1
    return counts


def variant_outcome_rows(events: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    for row in events:
        variant = str(row.get("variant_id") or "")
        if variant not in ALL_VARIANTS:
            continue
        bucket = buckets.setdefault(
            variant,
            {
                "variant_id": variant,
                "event_rows": 0,
                "policy_event_rows": 0,
                "resolved_n": 0,
                "same_bar_n": 0,
                "no_entry_n": 0,
                "setup_not_refinable_n": 0,
                "lock_triggered_n": 0,
                "lock_then_stop_n": 0,
                "selected_M1_n": 0,
                "selected_M5_n": 0,
                "selected_M15_n": 0,
                "_gross_sum": 0.0,
                "_outcomes": Counter(),
            },
        )
        bucket["event_rows"] += 1
        outcome = str(row.get("v1_outcome") or "UNKNOWN")
        bucket["_outcomes"][outcome] += 1
        selected = str(row.get("v1_selected_timeframe") or "")
        if selected in {"M1", "M5", "M15"}:
            bucket[f"selected_{selected}_n"] += 1
        if outcome in RESOLVED_OUTCOMES:
            gross = as_float(row.get("v1_gross_r"))
            if gross is not None:
                bucket["policy_event_rows"] += 1
                bucket["resolved_n"] += 1
                bucket["_gross_sum"] += gross
        elif outcome == "SAME_BAR":
            bucket["policy_event_rows"] += 1
            bucket["same_bar_n"] += 1
        elif outcome == "NO_ENTRY":
            bucket["no_entry_n"] += 1
        elif outcome == "SETUP_NOT_REFINABLE":
            bucket["setup_not_refinable_n"] += 1
        if row.get("locks_triggered"):
            bucket["lock_triggered_n"] += 1
            if outcome in LOCK_STOP_OUTCOMES:
                bucket["lock_then_stop_n"] += 1

    rows = []
    for variant in ALL_VARIANTS:
        bucket = buckets.get(variant)
        if not bucket:
            continue
        row = {key: value for key, value in bucket.items() if not key.startswith("_")}
        row["gross_mean_r"] = (
            round(float(bucket["_gross_sum"]) / int(bucket["resolved_n"]), 6) if bucket["resolved_n"] else None
        )
        row["samebar_rate_over_policy_events"] = rate_or_none(bucket["same_bar_n"], bucket["policy_event_rows"])
        row["lock_trigger_rate_over_policy_events"] = rate_or_none(
            bucket["lock_triggered_n"], bucket["policy_event_rows"]
        )
        row["lock_then_stop_rate_after_trigger"] = rate_or_none(bucket["lock_then_stop_n"], bucket["lock_triggered_n"])
        row["outcomes"] = dict(sorted(bucket["_outcomes"].items()))
        rows.append(row)
    return rows


def mtf_resolution_rows(events: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for variant in ALL_VARIANTS:
        selected_counts: Counter[str] = Counter()
        v0_samebar = 0
        v1_samebar = 0
        resolved_by_mtf = 0
        still_unresolved = 0
        for row in events:
            if row.get("variant_id") != variant:
                continue
            selected_counts[str(row.get("v1_selected_timeframe") or "UNKNOWN")] += 1
            v0_outcome = str(row.get("v0_outcome") or "")
            v1_outcome = str(row.get("v1_outcome") or "")
            if v0_outcome == "SAME_BAR":
                v0_samebar += 1
                if v1_outcome in RESOLVED_OUTCOMES:
                    resolved_by_mtf += 1
                elif v1_outcome == "SAME_BAR":
                    still_unresolved += 1
            if v1_outcome == "SAME_BAR":
                v1_samebar += 1
        rows.append(
            {
                "variant_id": variant,
                "v0_samebar_n": v0_samebar,
                "v1_samebar_n": v1_samebar,
                "v0_samebar_resolved_by_mtf_n": resolved_by_mtf,
                "v0_samebar_still_unresolved_n": still_unresolved,
                "selected_M1_n": selected_counts.get("M1", 0),
                "selected_M5_n": selected_counts.get("M5", 0),
                "selected_M15_n": selected_counts.get("M15", 0),
            }
        )
    return rows


def samebar_stress_delta_rows(events: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    stats: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    for row in events:
        variant = str(row.get("variant_id") or "")
        if variant not in ALL_VARIANTS:
            continue
        for group in groups_for_row(row):
            for treatment in TREATMENTS:
                value = value_for_treatment(row, treatment)
                if value is not None:
                    stats[(treatment, group, variant)].append(value)

    rows = []
    for treatment in TREATMENTS:
        for group in GROUP_ORDER:
            j_values = stats.get((treatment, group, J46), [])
            if not j_values:
                continue
            best_lock = None
            best_lock_mean = None
            best_lock_n = 0
            for lock_variant in LOCK_VARIANTS:
                values = stats.get((treatment, group, lock_variant), [])
                mean_value = sum(values) / len(values) if values else None
                if mean_value is not None and (best_lock_mean is None or mean_value > best_lock_mean):
                    best_lock = lock_variant
                    best_lock_mean = mean_value
                    best_lock_n = len(values)
            j_mean = sum(j_values) / len(j_values)
            rows.append(
                {
                    "treatment": treatment,
                    "group": group,
                    "j46_net_mean_r_cost_0.05": round(j_mean, 6),
                    "j46_n": len(j_values),
                    "best_lock_variant": best_lock,
                    "best_lock_net_mean_r_cost_0.05": round(best_lock_mean, 6) if best_lock_mean is not None else None,
                    "best_lock_n": best_lock_n,
                    "best_lock_minus_j46": round(best_lock_mean - j_mean, 6) if best_lock_mean is not None else None,
                }
            )
    return rows


def value_for_treatment(row: Mapping[str, Any], treatment: str) -> float | None:
    outcome = str(row.get("v1_outcome") or "")
    if outcome in RESOLVED_OUTCOMES:
        gross = as_float(row.get("v1_gross_r"))
        return None if gross is None else gross - COST_R
    if outcome != "SAME_BAR":
        return None
    if treatment == "exclude_unresolved":
        return None
    if treatment == "samebar_breakeven":
        return -COST_R
    if treatment == "samebar_pessimistic":
        return -1.0 - COST_R
    raise ValueError(f"unknown treatment: {treatment}")


def mechanism_summary_rows(
    pivots: Mapping[str, Mapping[str, Mapping[str, Any]]],
    *,
    scope: str,
) -> list[dict[str, Any]]:
    counts: Counter[tuple[str, str, str]] = Counter()
    totals: Counter[tuple[str, str]] = Counter()
    delta_sums: defaultdict[tuple[str, str], float] = defaultdict(float)
    for variants in pivots.values():
        j_row = variants.get(J46)
        if not j_row:
            continue
        j_value = resolved_value(j_row)
        if j_value is None:
            continue
        keys = groups_for_row(j_row) if scope == "group" else [str(j_row.get("v1_selected_timeframe") or "UNKNOWN")]
        for lock_variant in LOCK_VARIANTS:
            lock_row = variants.get(lock_variant)
            if not lock_row:
                continue
            lock_value = resolved_value(lock_row)
            if lock_value is None:
                continue
            mechanism = classify_mechanism(j_value, lock_value)
            for key in keys:
                counts[(lock_variant, key, mechanism)] += 1
                totals[(lock_variant, key)] += 1
                delta_sums[(lock_variant, key)] += lock_value - j_value

    keys = GROUP_ORDER if scope == "group" else ["M1", "M5", "M15"]
    rows = []
    for variant in LOCK_VARIANTS:
        for key in keys:
            total = totals[(variant, key)]
            row: dict[str, Any] = {
                "variant_id": variant,
                "scope": scope,
                "key": key,
                "paired_resolved_n": total,
                "mean_delta_lock_minus_j46": round(delta_sums[(variant, key)] / total, 6) if total else None,
            }
            for mechanism in MECHANISMS:
                n = counts[(variant, key, mechanism)]
                row[f"{mechanism}_n"] = n
                row[f"{mechanism}_rate"] = rate_or_none(n, total)
            rows.append(row)
    return rows


def classify_mechanism(j_value: float, lock_value: float) -> str:
    if abs(lock_value - j_value) <= EPS:
        return "same_result"
    if j_value <= 0.0:
        if lock_value > 0.0:
            return "lock_rescued_loss_to_positive"
        if lock_value > j_value:
            return "lock_reduced_loss_only"
        return "lock_failed_to_improve_j46_nonpositive"
    if lock_value <= 0.0:
        return "winner_truncated_to_nonpositive"
    if lock_value < j_value:
        return "winner_truncated_but_positive"
    return "lock_improved_positive_winner"


def casebook_rows(pivots: Mapping[str, Mapping[str, Mapping[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
    buckets: dict[str, list[dict[str, Any]]] = {
        "largest_j46_better_examples": [],
        "largest_lock_better_examples": [],
        "winner_truncated_to_nonpositive_examples": [],
        "true_rescue_examples": [],
        "missed_favorable_path_examples": [],
        "residual_samebar_examples": [],
    }
    for event_key, variants in pivots.items():
        j_row = variants.get(J46)
        if not j_row:
            continue
        j_value = resolved_value(j_row)
        for lock_variant in LOCK_VARIANTS:
            lock_row = variants.get(lock_variant)
            if not lock_row:
                continue
            lock_value = resolved_value(lock_row)
            if j_value is not None and lock_value is not None:
                delta = lock_value - j_value
                row = casebook_pair_row(event_key, j_row, lock_row, j_value, lock_value, delta)
                if delta < -EPS:
                    buckets["largest_j46_better_examples"].append(row)
                elif delta > EPS:
                    buckets["largest_lock_better_examples"].append(row)
                if j_value > 0.0 and lock_value <= 0.0:
                    buckets["winner_truncated_to_nonpositive_examples"].append(row)
                if j_value <= 0.0 and lock_value > 0.0:
                    buckets["true_rescue_examples"].append(row)
                mfe = as_float(j_row.get("mfe_r"))
                if j_value <= 0.0 and lock_value <= 0.0 and mfe is not None and mfe >= 1.5:
                    buckets["missed_favorable_path_examples"].append(row)
                continue

            j_outcome = str(j_row.get("v1_outcome") or "UNKNOWN")
            lock_outcome = str(lock_row.get("v1_outcome") or "UNKNOWN")
            if j_outcome == "SAME_BAR" or lock_outcome == "SAME_BAR":
                buckets["residual_samebar_examples"].append(
                    {
                        "event_key": event_key,
                        "variant_id": lock_variant,
                        "cohort": str(j_row.get("raw_cohort_key") or "UNKNOWN"),
                        "role": str(j_row.get("role") or "unknown"),
                        "timeframe": str(j_row.get("v1_selected_timeframe") or "UNKNOWN"),
                        "j46_outcome": j_outcome,
                        "j46_r": round_optional(j_value),
                        "lock_outcome": lock_outcome,
                        "lock_r": round_optional(lock_value),
                        "mfe_r": round_optional(as_float(j_row.get("mfe_r"))),
                        "mae_r": round_optional(as_float(j_row.get("mae_r"))),
                        "note": "OHLC cannot order the policy events inside the selected bar.",
                    }
                )

    return {
        "largest_j46_better_examples": sorted(
            buckets["largest_j46_better_examples"],
            key=lambda row: float(row["delta_lock_minus_j46"]),
        )[:CASEBOOK_LIMIT],
        "largest_lock_better_examples": sorted(
            buckets["largest_lock_better_examples"],
            key=lambda row: float(row["delta_lock_minus_j46"]),
            reverse=True,
        )[:CASEBOOK_LIMIT],
        "winner_truncated_to_nonpositive_examples": sorted(
            buckets["winner_truncated_to_nonpositive_examples"],
            key=lambda row: float(row["j46_r"]),
            reverse=True,
        )[:CASEBOOK_LIMIT],
        "true_rescue_examples": sorted(
            buckets["true_rescue_examples"],
            key=lambda row: float(row["delta_lock_minus_j46"]),
            reverse=True,
        )[:CASEBOOK_LIMIT],
        "missed_favorable_path_examples": sorted(
            buckets["missed_favorable_path_examples"],
            key=lambda row: float(row["mfe_r"] or 0.0),
            reverse=True,
        )[:CASEBOOK_LIMIT],
        "residual_samebar_examples": buckets["residual_samebar_examples"][:CASEBOOK_LIMIT],
    }


def casebook_pair_row(
    event_key: str,
    j_row: Mapping[str, Any],
    lock_row: Mapping[str, Any],
    j_value: float,
    lock_value: float,
    delta: float,
) -> dict[str, Any]:
    locks = lock_row.get("locks_triggered") or []
    return {
        "event_key": event_key,
        "variant_id": str(lock_row.get("variant_id") or ""),
        "cohort": str(j_row.get("raw_cohort_key") or "UNKNOWN"),
        "role": str(j_row.get("role") or "unknown"),
        "timeframe": str(j_row.get("v1_selected_timeframe") or "UNKNOWN"),
        "j46_outcome": str(j_row.get("v1_outcome") or "UNKNOWN"),
        "j46_r": round(j_value, 6),
        "lock_outcome": str(lock_row.get("v1_outcome") or "UNKNOWN"),
        "lock_r": round(lock_value, 6),
        "delta_lock_minus_j46": round(delta, 6),
        "mfe_r": round_optional(as_float(j_row.get("mfe_r"))),
        "mae_r": round_optional(as_float(j_row.get("mae_r"))),
        "max_locked_floor_r": round_optional(as_float(lock_row.get("max_locked_floor_r"))),
        "lock_steps": lock_steps_summary(locks),
        "bars_in_trade": lock_row.get("bars_in_trade"),
    }


def lock_steps_summary(locks: Any) -> str:
    if not locks:
        return ""
    parts = []
    for lock in locks:
        if isinstance(lock, Mapping):
            trigger = lock.get("trigger_r")
            floor = lock.get("floor_r")
            parts.append(f"{trigger}->{floor}")
    return ";".join(parts)


def round_optional(value: float | None) -> float | None:
    return round(value, 6) if value is not None else None


def groups_for_row(row: Mapping[str, Any]) -> list[str]:
    return groups_for_key(str(row.get("raw_cohort_key") or ""), str(row.get("role") or ""))


def resolved_value(row: Mapping[str, Any]) -> float | None:
    if row.get("v1_outcome") not in RESOLVED_OUTCOMES:
        return None
    return as_float(row.get("v1_gross_r"))


def as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def bucket_value(value: float) -> str:
    if value <= -1:
        return "le_-1R"
    if value <= 0:
        return "le_0R"
    if value < 1:
        return "0_to_1R"
    if value < 3:
        return "1_to_3R"
    return "ge_3R"


def pairwise_variant_rows(stats: Mapping[tuple[str, str, str], PairStats]) -> list[dict[str, Any]]:
    return [
        stats.get((variant, "group", "all_enabled"), PairStats()).row(
            variant_id=variant,
            scope="all",
            key="all_enabled",
        )
        for variant in LOCK_VARIANTS
    ]


def pairwise_group_rows(stats: Mapping[tuple[str, str, str], PairStats]) -> list[dict[str, Any]]:
    rows = []
    for variant in LOCK_VARIANTS:
        for group in GROUP_ORDER:
            rows.append(
                stats.get((variant, "group", group), PairStats()).row(
                    variant_id=variant,
                    scope="group",
                    key=group,
                )
            )
    return rows


def pairwise_timeframe_rows(stats: Mapping[tuple[str, str, str], PairStats]) -> list[dict[str, Any]]:
    rows = []
    for variant in LOCK_VARIANTS:
        for timeframe in ("M1", "M5", "M15"):
            rows.append(
                stats.get((variant, "timeframe", timeframe), PairStats()).row(
                    variant_id=variant,
                    scope="timeframe",
                    key=timeframe,
                )
            )
    return rows


def cohort_pair_rows(stats: Mapping[tuple[str, str, str], PairStats]) -> list[dict[str, Any]]:
    rows = []
    keys = sorted(key for key in stats if key[1] == "cohort")
    for variant, _scope, cohort_key in keys:
        rows.append(stats[(variant, "cohort", cohort_key)].row(variant_id=variant, scope="cohort", key=cohort_key))
    return rows


def top_cohort_rows(rows: Sequence[Mapping[str, Any]], *, direction: str) -> list[dict[str, Any]]:
    candidates = [row for row in rows if row.get("paired_resolved_n")]
    if direction == "j46":
        ordered = sorted(candidates, key=lambda row: float(row.get("sum_delta_lock_minus_j46") or 0.0))
    else:
        ordered = sorted(candidates, key=lambda row: float(row.get("sum_delta_lock_minus_j46") or 0.0), reverse=True)
    return list(ordered[:15])


def unresolved_pair_rows(unresolved: Counter[tuple[str, str]]) -> list[dict[str, Any]]:
    rows = []
    for variant in LOCK_VARIANTS:
        keys = [key for key in sorted(unresolved) if key[0] == variant]
        row = {"variant_id": variant}
        for _variant, label in keys:
            row[label] = unresolved[(variant, label)]
        rows.append(row)
    return rows


def transition_rows(counts: Counter[tuple[str, str, str]]) -> list[dict[str, Any]]:
    rows = []
    for variant in LOCK_VARIANTS:
        variant_rows = [
            (count, j_outcome, lock_outcome)
            for (item_variant, j_outcome, lock_outcome), count in counts.items()
            if item_variant == variant
        ]
        for count, j_outcome, lock_outcome in sorted(variant_rows, reverse=True)[:20]:
            rows.append(
                {
                    "variant_id": variant,
                    "j46_outcome": j_outcome,
                    "lock_outcome": lock_outcome,
                    "count": count,
                }
            )
    return rows


def mfe_rows(stats: Mapping[tuple[str, str], MfeStats]) -> list[dict[str, Any]]:
    rows = []
    for group in GROUP_ORDER:
        rows.append(stats.get(("group", group), MfeStats()).row(scope="group", key=group))
    for timeframe in ("M1", "M5", "M15"):
        rows.append(stats.get(("timeframe", timeframe), MfeStats()).row(scope="timeframe", key=timeframe))
    cohort_keys = sorted(key for key in stats if key[0] == "cohort")
    for _scope, cohort in cohort_keys:
        rows.append(stats[("cohort", cohort)].row(scope="cohort", key=cohort))
    return rows


def direct_answers(summary: Mapping[str, Any]) -> list[dict[str, str]]:
    variant_rows = {row["variant_id"]: row for row in summary.get("pairwise_variant_summary") or []}
    best_lock = max(
        LOCK_VARIANTS,
        key=lambda variant: float((variant_rows.get(variant) or {}).get("sum_delta_lock_minus_j46") or -1e18),
    )
    best_row = variant_rows.get(best_lock) or {}
    mfe_all = find_mfe_row(summary, "group", "all_enabled")
    group_rows = summary.get("pairwise_group_summary") or []
    target_half = find_pair_row(group_rows, "PATH_LOCK_HALF_GAIN_V0", "target_cohorts")
    target_cons = find_pair_row(group_rows, "PATH_LOCK_CONSERVATIVE_V0", "target_cohorts")
    exclude_all = find_stress_row(summary, "exclude_unresolved", "all_enabled")
    stress_all = find_stress_row(summary, "samebar_pessimistic", "all_enabled")
    stress_target = find_stress_row(summary, "samebar_pessimistic", "target_cohorts")
    mtf_j46 = find_variant_row(summary.get("mtf_resolution_summary") or [], J46)
    outcome_j46 = find_variant_row(summary.get("variant_outcome_summary") or [], J46)
    outcome_early = find_variant_row(summary.get("variant_outcome_summary") or [], "PATH_LOCK_EARLY_BE_V0")
    return [
        {
            "question": "What exactly worked in V1?",
            "answer": (
                "The MTF measurement layer worked as infrastructure: for J46 it resolved "
                f"{mtf_j46.get('v0_samebar_resolved_by_mtf_n')} prior V0 same-bars and reduced J46 same-bars "
                f"from {mtf_j46.get('v0_samebar_n')} to {mtf_j46.get('v1_samebar_n')}. "
                "The J46 exit itself also remained the best global resolved/stressed comparator."
            ),
        },
        {
            "question": "What exactly did not work?",
            "answer": (
                "The fixed-R lock-only exit policies did not work as promotion candidates. "
                f"Under the full-corpus headline treatment, best-lock-minus-J46={exclude_all.get('best_lock_minus_j46')}; "
                f"under samebar-pessimistic stress, best-lock-minus-J46={stress_all.get('best_lock_minus_j46')}."
            ),
        },
        {
            "question": "Did V1 fail because there is no favorable path before failure?",
            "answer": (
                "No. J46 nonpositive outcomes still show meaningful favorable excursions: "
                f"MFE>=1R rate={mfe_all.get('nonpositive_mfe_ge_1_rate')}, "
                f"MFE>=1.5R rate={mfe_all.get('nonpositive_mfe_ge_1.5_rate')}, "
                f"MFE>=2R rate={mfe_all.get('nonpositive_mfe_ge_2_rate')}."
            ),
        },
        {
            "question": "Did fixed-R lock-only beat J46 on paired resolved rows?",
            "answer": (
                "Only narrowly on common paired resolved rows, and only for "
                f"{best_lock}, with mean_delta_lock_minus_J46={best_row.get('mean_delta_lock_minus_j46')} "
                f"over n={best_row.get('paired_resolved_n')} paired resolved rows. "
                "That is diagnostic, not promotion evidence, because the full-corpus and same-bar stress treatments still favor J46."
            ),
        },
        {
            "question": "Was the failure mostly execution?",
            "answer": "No live execution was tested. The failure is research-layer exit logic: fixed-R locks did not robustly improve the same raw setup stream.",
        },
        {
            "question": "Was the failure mostly market structure or fixed-R logic?",
            "answer": "V1 cannot test structure. What it does show is that fixed-R anchors are too blunt; any remaining path-scaling thesis must move to pre-registered structural levels.",
        },
        {
            "question": "Did lock-only truncate winners?",
            "answer": (
                "Yes. All lock variants show truncation where lock/BE stops exited below the J46 result. "
                f"For {best_lock}, truncation_n={best_row.get('truncation_n')} and truncation_lost_R={best_row.get('truncation_lost_r')}."
            ),
        },
        {
            "question": "Did lock-only rescue enough J46 losers?",
            "answer": (
                "It rescued some nonpositive J46 outcomes, but not enough for the registered full-corpus decision metric. "
                f"For {best_lock}, rescued_j46_nonpositive_n={best_row.get('rescued_j46_nonpositive_n')}, "
                f"while j46_better_n={best_row.get('j46_better_n')}; samebar-pessimistic all-enabled best-lock-minus-J46="
                f"{stress_all.get('best_lock_minus_j46')}."
            ),
        },
        {
            "question": "Where did the path-scaling idea still look alive?",
            "answer": (
                "It looked alive only in the headline target-family treatment and lower-timeframe diagnostics, not as robust promotion evidence. "
                f"Target conservative mean delta={target_cons.get('mean_delta_lock_minus_j46')}; "
                f"target half-gain mean delta={target_half.get('mean_delta_lock_minus_j46')}; "
                f"target samebar-pessimistic best-lock-minus-J46={stress_target.get('best_lock_minus_j46')}."
            ),
        },
        {
            "question": "Why did the aggressive early-BE idea fail?",
            "answer": (
                "It protected earlier but created too much path-order ambiguity and reward suppression: "
                f"early-BE same_bar_n={outcome_early.get('same_bar_n')} versus J46 same_bar_n={outcome_j46.get('same_bar_n')}, "
                f"and early-BE gross_mean_r={outcome_early.get('gross_mean_r')} versus J46 gross_mean_r={outcome_j46.get('gross_mean_r')}."
            ),
        },
    ]


def find_pair_row(rows: Sequence[Mapping[str, Any]], variant: str, key: str) -> Mapping[str, Any]:
    return next((row for row in rows if row.get("variant_id") == variant and row.get("key") == key), {})


def find_variant_row(rows: Sequence[Mapping[str, Any]], variant: str) -> Mapping[str, Any]:
    return next((row for row in rows if row.get("variant_id") == variant), {})


def find_stress_row(summary: Mapping[str, Any], treatment: str, group: str) -> Mapping[str, Any]:
    return next(
        (
            row
            for row in (summary.get("samebar_stress_delta_summary") or [])
            if row.get("treatment") == treatment and row.get("group") == group
        ),
        {},
    )


def find_mfe_row(summary: Mapping[str, Any], scope: str, key: str) -> Mapping[str, Any]:
    return next(
        (
            row
            for row in (summary.get("mfe_opportunity_summary") or [])
            if row.get("scope") == scope and row.get("key") == key
        ),
        {},
    )


def what_worked(summary: Mapping[str, Any]) -> list[dict[str, str]]:
    mtf_j46 = find_variant_row(summary.get("mtf_resolution_summary") or [], J46)
    target_exclude = find_stress_row(summary, "exclude_unresolved", "target_cohorts")
    m1m5_conservative = find_pair_row(
        summary.get("pairwise_timeframe_summary") or [],
        "PATH_LOCK_CONSERVATIVE_V0",
        "M5",
    )
    return [
        {
            "item": "MTF path-resolution infrastructure",
            "evidence": (
                f"J46 V0 same-bars={mtf_j46.get('v0_samebar_n')}; "
                f"resolved by MTF={mtf_j46.get('v0_samebar_resolved_by_mtf_n')}; "
                f"remaining V1 same-bars={mtf_j46.get('v1_samebar_n')}."
            ),
            "interpretation": "This worked as a measurement improvement, not as a tradable edge.",
        },
        {
            "item": "J46-J49 comparator robustness",
            "evidence": "J46 stayed best globally under unresolved exclusion and samebar-pessimistic stress.",
            "interpretation": "The delayed 3R-to-BE / 6R-target architecture preserved more right-tail payoff than fixed-R lock ladders.",
        },
        {
            "item": "Target-cohort lock hint under headline exclusion",
            "evidence": (
                f"Target best-lock-minus-J46={target_exclude.get('best_lock_minus_j46')} under exclude_unresolved."
            ),
            "interpretation": "There is a real-looking local hint, but it is not promotion-grade because it fails stress handling.",
        },
        {
            "item": "M5 diagnostic subset",
            "evidence": (
                f"M5 conservative lock mean_delta_lock_minus_J46="
                f"{m1m5_conservative.get('mean_delta_lock_minus_j46')}."
            ),
            "interpretation": "Lower-timeframe coverage can expose useful path mechanics, but coverage skew blocks final inference.",
        },
    ]


def what_failed(summary: Mapping[str, Any]) -> list[dict[str, str]]:
    variant_rows = {row["variant_id"]: row for row in summary.get("pairwise_variant_summary") or []}
    best_lock = max(
        LOCK_VARIANTS,
        key=lambda variant: float((variant_rows.get(variant) or {}).get("sum_delta_lock_minus_j46") or -1e18),
    )
    best_row = variant_rows.get(best_lock) or {}
    early = find_variant_row(summary.get("variant_outcome_summary") or [], "PATH_LOCK_EARLY_BE_V0")
    j46 = find_variant_row(summary.get("variant_outcome_summary") or [], J46)
    all_exclude = find_stress_row(summary, "exclude_unresolved", "all_enabled")
    all_stress = find_stress_row(summary, "samebar_pessimistic", "all_enabled")
    target_stress = find_stress_row(summary, "samebar_pessimistic", "target_cohorts")
    return [
        {
            "item": "Global fixed-R lock-only promotion",
            "evidence": (
                f"Best lock={best_lock}; paired mean_delta_lock_minus_J46="
                f"{best_row.get('mean_delta_lock_minus_j46')}; paired sum_delta="
                f"{best_row.get('sum_delta_lock_minus_j46')}; full-corpus exclude_unresolved best-lock-minus-J46="
                f"{all_exclude.get('best_lock_minus_j46')}; samebar-pessimistic best-lock-minus-J46="
                f"{all_stress.get('best_lock_minus_j46')}."
            ),
            "interpretation": "A small common-row gain did not survive the registered full-corpus treatment or conservative ordering stress.",
        },
        {
            "item": "Aggressive early protection",
            "evidence": (
                f"Early-BE same_bar_n={early.get('same_bar_n')} versus J46 same_bar_n={j46.get('same_bar_n')}; "
                f"early-BE gross_mean_r={early.get('gross_mean_r')} versus J46 gross_mean_r={j46.get('gross_mean_r')}."
            ),
            "interpretation": "Moving locks earlier increased ambiguous policy collisions and compressed payoff.",
        },
        {
            "item": "Target-cohort promotion robustness",
            "evidence": (
                f"Samebar-pessimistic target best-lock-minus-J46={target_stress.get('best_lock_minus_j46')}."
            ),
            "interpretation": "The best-looking local result is not reliable once unresolved ordering is treated conservatively.",
        },
        {
            "item": "Fixed-R abstraction",
            "evidence": "Forensic casebooks contain both true rescues and large winner truncations under the same static thresholds.",
            "interpretation": "The same rule helps some trades and harms others because it ignores structural context.",
        },
    ]


def root_cause_summary(summary: Mapping[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "cause": "Primary",
            "diagnosis": "Fixed-R lock-only is too blunt.",
            "evidence": "Half-gain is slightly positive on common resolved rows, but the registered full-corpus and samebar-pessimistic decision metrics still favor J46.",
        },
        {
            "cause": "Secondary",
            "diagnosis": "Winner truncation is material.",
            "evidence": "Lock/BE stops frequently exit below J46 outcomes; large truncation appears in the top J46-better cohorts and casebook.",
        },
        {
            "cause": "Secondary",
            "diagnosis": "Residual same-bar uncertainty is decision-critical for local target claims.",
            "evidence": "Target-family edge under unresolved exclusion flips negative under samebar-pessimistic stress.",
        },
        {
            "cause": "Not supported",
            "diagnosis": "The market never offers favorable path movement.",
            "evidence": "J46 nonpositive rows still show substantial MFE beyond 1R/1.5R/2R thresholds.",
        },
        {
            "cause": "Not tested",
            "diagnosis": "Structural-level path scaling or reentry.",
            "evidence": "V1 contains no structural lock selector, no reentry engine, and no composite risk accounting.",
        },
    ]


def unanswered_questions_status(summary: Mapping[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "question": "Does favorable movement before failure exist?",
            "status": "ANSWERED_YES",
            "detail": "J46 nonpositive rows often had MFE above early fixed-R thresholds; the opportunity exists, but fixed-R capture failed robustness.",
        },
        {
            "question": "Did fixed-R locks fail by cutting winners?",
            "status": "ANSWERED_YES",
            "detail": "Pairwise truncation counts show lock/BE exits below J46 outcomes across all lock ladders.",
        },
        {
            "question": "Did fixed-R locks rescue losers enough to compensate?",
            "status": "ANSWERED_NO_FOR_REGISTERED_DECISION_METRIC",
            "detail": "Half-gain narrowly compensates on common resolved rows, but not after full-corpus unresolved handling and pessimistic same-bar stress.",
        },
        {
            "question": "Is the broader path-scaling idea dead?",
            "status": "ANSWERED_NO",
            "detail": "Only fixed-R lock-only failed. Structural levels and risk-budgeted reentry remain untested.",
        },
        {
            "question": "Can V1 answer whether structural levels work?",
            "status": "NOT_ANSWERABLE_IN_V1",
            "detail": "The V1 event log has no structural level selector; this requires a fresh registered hypothesis.",
        },
        {
            "question": "Can V1 answer whether reentry works?",
            "status": "NOT_ANSWERABLE_IN_V1",
            "detail": "V1 intentionally contains no reentry or composite risk accounting.",
        },
        {
            "question": "Can V1 answer actual spread/slippage impact?",
            "status": "PARTIALLY_ANSWERED",
            "detail": "V1 reports R-cost sensitivity only. Real execution costs need broker/tick/slippage data, especially before any reentry test.",
        },
        {
            "question": "Which specific cases explain the aggregate result?",
            "status": "ANSWERED_WITH_CASEBOOK",
            "detail": "The report includes largest J46-better, largest lock-better, true-rescue, winner-truncation, missed-MFE, and residual-samebar examples.",
        },
        {
            "question": "Is there any remaining V1 ambiguity that blocks the V1 verdict?",
            "status": "ANSWERED_NO",
            "detail": "Residual OHLC ordering ambiguity remains a data limitation, but it is handled by registered exclusion/stress policy and no longer blocks the V1 rejection.",
        },
    ]


def ambiguity_ledger(summary: Mapping[str, Any]) -> list[dict[str, str]]:
    j46_mtf = find_variant_row(summary.get("mtf_resolution_summary") or [], J46)
    all_stress = find_stress_row(summary, "samebar_pessimistic", "all_enabled")
    return [
        {
            "item": "Paired-row diagnostic versus registered decision metric",
            "status": "CLOSED_BY_SEPARATION",
            "detail": "Half-gain is slightly positive on common resolved rows, but full-corpus unresolved exclusion and pessimistic stress remain the decision lenses.",
        },
        {
            "item": "Residual selected-bar same-bars",
            "status": "CLOSED_BY_REGISTERED_POLICY",
            "detail": (
                f"J46 V1 same-bars={j46_mtf.get('v1_samebar_n')}; samebar-pessimistic all-enabled "
                f"best-lock-minus-J46={all_stress.get('best_lock_minus_j46')}."
            ),
        },
        {
            "item": "Lower-timeframe coverage skew",
            "status": "CLOSED_AS_DIAGNOSTIC_ONLY",
            "detail": "M1/M5 results are useful diagnostics but not final evidence because lower-timeframe availability is not uniform across the full corpus.",
        },
        {
            "item": "Cost realism",
            "status": "CLOSED_AS_SENSITIVITY_ONLY",
            "detail": "V1 uses R-cost sensitivity because historical OHLC lacks reliable commission, spread, and slippage.",
        },
        {
            "item": "Structural-level and reentry questions",
            "status": "OUT_OF_SCOPE_FOR_V1",
            "detail": "V1 has no structural selector, no reentry engine, and no composite risk accounting; these require a fresh pre-registered hypothesis.",
        },
        {
            "item": "V1 promotion verdict",
            "status": "CLOSED_REJECTED",
            "detail": "Fixed-R lock-only remains NO_PROMOTION_VERDICT and is rejected for exit-policy promotion.",
        },
    ]


def opened_questions(summary: Mapping[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "question": "Is any V1-specific question still blocking the V1 verdict?",
            "status": "NO",
            "answer": "No. V1 fixed-R lock-only is rejected, and residual same-bar uncertainty is handled by registered policy.",
        },
        {
            "question": "Can V1 explain what worked?",
            "status": "YES",
            "answer": "MTF resolution worked as measurement infrastructure; J46 remained robust; target and M1/M5 lock hints are diagnostic only.",
        },
        {
            "question": "Can V1 explain what failed?",
            "status": "YES",
            "answer": "Fixed-R locks add small common-row benefit in one ladder but create extra same-bar exposure and truncate winners; promotion metrics stay below J46.",
        },
        {
            "question": "Can V1 decide structural locks?",
            "status": "NO_OUT_OF_SCOPE",
            "answer": "No. Structural locks require a fresh registered hypothesis with pre-declared levels and no parameter sweep.",
        },
        {
            "question": "Can V1 decide reentry?",
            "status": "NO_OUT_OF_SCOPE",
            "answer": "No. Reentry requires structural pullback references plus pre-registered risk and cost accounting.",
        },
        {
            "question": "Should work auto-advance to V2?",
            "status": "NO",
            "answer": "No. A future V2 must be separately registered; V1 does not promote it automatically.",
        },
    ]


def limitations(summary: Mapping[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "limitation": "OHLC order inside selected bars",
            "impact": "Cannot know whether lock trigger, stop, and target happened first inside a single M1/M5/M15 bar.",
            "treatment": "Headline excludes unresolved SAME_BAR rows; decision stress scores SAME_BAR as -1R before any promotion.",
        },
        {
            "limitation": "Historical cost model",
            "impact": "No reliable per-trade spread/commission/slippage in the OHLC corpus.",
            "treatment": "Use R-cost sensitivity only; do not claim measured live execution economics.",
        },
        {
            "limitation": "Same dataset",
            "impact": "Forensics can explain V1 failure but cannot promote a tuned variant from the same corpus.",
            "treatment": "NO_PROMOTION_VERDICT remains; no parameter optimization.",
        },
        {
            "limitation": "No structural levels",
            "impact": "V1 cannot decide whether liquidity/OB/FVG/swing-level locks would work.",
            "treatment": "Any structural test needs a fresh registered hypothesis before data inspection.",
        },
        {
            "limitation": "No reentry accounting",
            "impact": "V1 cannot evaluate the owner thesis that lock + reentry changes the payoff distribution.",
            "treatment": "Reentry stays blocked until a structural lock earns a separate test and cost/risk rules are registered.",
        },
    ]


def deeper_dive_candidates(summary: Mapping[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "rank": "1",
            "candidate": "Structural liquidity lock hypothesis",
            "reason": "Fixed-R anchors are too blunt; the remaining thesis is that locks should occur at market levels known at decision time.",
            "status": "FRESH_HYPOTHESIS_REQUIRED",
        },
        {
            "rank": "2",
            "candidate": "Truncation casebook",
            "reason": "Sample the largest J46-better deltas to see if locks cut real runners or only ambiguous/noisy bars.",
            "status": "OPTIONAL_MANUAL_AUDIT",
        },
        {
            "rank": "3",
            "candidate": "Tick-order audit for M1/M5 same-bars",
            "reason": "Could reduce remaining OHLC ordering uncertainty, but it requires tick coverage and should not be assumed.",
            "status": "DATA_QUALITY_LANE",
        },
        {
            "rank": "4",
            "candidate": "Risk-budgeted reentry",
            "reason": "The owner thesis includes reentry, but reentry should wait until a structural lock/pullback reference exists.",
            "status": "BLOCKED_UNTIL_STRUCTURAL_LOCK_EARNS_IT",
        },
    ]


def next_steps(summary: Mapping[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "rank": "1",
            "next_step": "Archive fixed-R V1 lock-only as rejected.",
            "reason": "The failure mode is now explained: small common-row rescue benefit, material truncation, extra same-bar exposure, and no robustness under the registered stress treatment.",
        },
        {
            "rank": "2",
            "next_step": "If continuing path-scaling, register exactly one structural-level lock hypothesis.",
            "reason": "The remaining plausible thesis is structural timing, not more fixed-R sweeps.",
        },
        {
            "rank": "3",
            "next_step": "Keep the V1 MTF resolver and residual same-bar policy as shared infrastructure.",
            "reason": "The measurement layer worked and should prevent future path studies from fabricating order.",
        },
        {
            "rank": "4",
            "next_step": "Do not implement reentry yet.",
            "reason": "Reentry needs a trusted structural pullback/lock level and strict risk accounting.",
        },
    ]


def synthesis(summary: Mapping[str, Any]) -> list[str]:
    return [
        "The failure is not evidence that the market never offers path opportunity. J46 nonpositive outcomes often had favorable MFE before final failure.",
        "The failure is evidence that fixed-R lock ladders are the wrong first abstraction: half-gain barely improves common resolved rows, but the improvement is too small to survive full-corpus unresolved handling, same-bar stress, and winner-truncation diagnostics.",
        "This is a logic/design failure of fixed-R lock-only, plus a measurement limitation around OHLC same-bars. It is not a live execution failure, prompt failure, or AI failure.",
        "The next credible research step is a freshly registered structural-level hypothesis. Without that, more fixed-R tweaking would become parameter optimization.",
    ]


def quantile(values: Sequence[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(float(value) for value in values)
    if len(ordered) == 1:
        return round(ordered[0], 6)
    pos = (len(ordered) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return round(ordered[int(pos)], 6)
    lower = ordered[lo] * (hi - pos)
    upper = ordered[hi] * (pos - lo)
    return round(lower + upper, 6)


def render_report(summary: Mapping[str, Any]) -> str:
    lines = [
        "# Raw-OHLC Path Scaling V1 Failure Forensics",
        "",
        f"**Created UTC:** {summary.get('created_at_utc')}",
        f"**Event log:** `{summary.get('event_log_path')}`",
        f"**Event log SHA256:** `{summary.get('event_log_sha256')}`",
        f"**Promotion verdict:** `{summary.get('promotion_verdict')}`",
        f"**Scope:** `{summary.get('scope')}`",
        "",
        "## Boundary",
        "",
        "\n".join(f"- {item}" for item in summary.get("research_boundary") or []),
        "",
        "## Direct Answers",
        "",
        markdown_table(summary.get("direct_answers") or []),
        "",
        "## What Worked",
        "",
        markdown_table(summary.get("what_worked") or []),
        "",
        "## What Failed",
        "",
        markdown_table(summary.get("what_failed") or []),
        "",
        "## Root Cause Summary",
        "",
        markdown_table(summary.get("root_cause_summary") or []),
        "",
        "## Variant Outcome Summary",
        "",
        markdown_table(summary.get("variant_outcome_summary") or []),
        "",
        "## MTF Resolution Summary",
        "",
        markdown_table(summary.get("mtf_resolution_summary") or []),
        "",
        "## Same-Bar Stress Delta Summary",
        "",
        markdown_table(summary.get("samebar_stress_delta_summary") or []),
        "",
        "## Pairwise Variant Summary",
        "",
        markdown_table(summary.get("pairwise_variant_summary") or []),
        "",
        "## Pairwise Group Summary",
        "",
        markdown_table(summary.get("pairwise_group_summary") or []),
        "",
        "## Pairwise Timeframe Summary",
        "",
        markdown_table(summary.get("pairwise_timeframe_summary") or []),
        "",
        "## Mechanism Group Summary",
        "",
        markdown_table(summary.get("mechanism_group_summary") or []),
        "",
        "## Mechanism Timeframe Summary",
        "",
        markdown_table(summary.get("mechanism_timeframe_summary") or []),
        "",
        "## Top J46 Better Cohorts",
        "",
        markdown_table(summary.get("top_j46_better_cohorts") or []),
        "",
        "## Top Lock Better Cohorts",
        "",
        markdown_table(summary.get("top_lock_better_cohorts") or []),
        "",
        "## Unresolved Pair Summary",
        "",
        markdown_table(summary.get("unresolved_pair_summary") or []),
        "",
        "## Outcome Transition Summary",
        "",
        markdown_table(summary.get("outcome_transition_summary") or []),
        "",
        "## MFE Opportunity Summary",
        "",
        markdown_table(summary.get("mfe_opportunity_summary") or []),
        "",
        "## Casebook",
        "",
        render_casebook(summary.get("casebook") or {}),
        "",
        "## Unanswered Questions Status",
        "",
        markdown_table(summary.get("unanswered_questions_status") or []),
        "",
        "## Ambiguity Ledger",
        "",
        markdown_table(summary.get("ambiguity_ledger") or []),
        "",
        "## Opened Questions",
        "",
        markdown_table(summary.get("opened_questions") or []),
        "",
        "## Limitations",
        "",
        markdown_table(summary.get("limitations") or []),
        "",
        "## Deeper Dive Candidates",
        "",
        markdown_table(summary.get("deeper_dive_candidates") or []),
        "",
        "## Next Steps",
        "",
        markdown_table(summary.get("next_steps") or []),
        "",
        "## Synthesis",
        "",
        "\n".join(f"- {item}" for item in summary.get("synthesis") or []),
    ]
    return "\n".join(lines).rstrip() + "\n"


def render_casebook(casebook: Mapping[str, Sequence[Mapping[str, Any]]]) -> str:
    if not casebook:
        return "_No casebook rows generated._"
    lines = []
    for key, rows in casebook.items():
        title = key.replace("_", " ").title()
        lines.extend([f"### {title}", "", markdown_table(rows), ""])
    return "\n".join(lines).rstrip()


def write_outputs(
    summary: Mapping[str, Any],
    *,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    report_path: str | Path = DEFAULT_REPORT_PATH,
) -> tuple[Path, Path]:
    output_dir = Path(output_root)
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    summary_path = output_dir / f"raw_ohlc_path_scaling_v1_failure_forensics_{stamp}.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    report = Path(report_path)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(summary), encoding="utf-8")
    return summary_path, report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event-log", default=DEFAULT_EVENT_LOG_PATH)
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--report-path", default=DEFAULT_REPORT_PATH)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = run_failure_forensics(event_log_path=args.event_log)
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
                    "scope": summary.get("scope"),
                    "unique_setups": summary.get("unique_setups"),
                    "output_summary": summary.get("output_summary"),
                    "report_path": summary.get("report_path"),
                    "headline": (summary.get("synthesis") or [None])[0],
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
