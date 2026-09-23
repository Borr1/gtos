#!/usr/bin/env python3
"""Close Phase 3 raw-OHLC path scaling V1 with treatment diagnostics.

This script reads the V1 MTF event log, answers the residual ambiguity
questions, and renders a final V1 disposition report. It is research/tooling
only and does not call AI or touch live trading behavior.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.analyze_raw_ohlc_replay_followups import groups_for_key, rate_or_none  # noqa: E402
from scripts.run_raw_ohlc_prequential_replay import git_commit_or_unknown, markdown_table, sha256_file  # noqa: E402


SCHEMA_VERSION = "raw_ohlc_path_scaling_v1_disposition_v1"
DEFAULT_EVENT_LOG_PATH = (
    "data/external/validation/calendar_macro_bundle_v1/historical_opportunities/"
    "raw_ohlc_prequential_replay/path_ablation_v1_mtf/"
    "raw_ohlc_path_ablation_v1_mtf_events_20260501T192723Z.jsonl"
)
DEFAULT_REPORT_PATH = (
    "research/phase_3_external_feed_validation/"
    "RAW_OHLC_PATH_SCALING_V1_FINAL_DISPOSITION_2026-05-02.md"
)
DEFAULT_OUTPUT_ROOT = (
    "data/external/validation/calendar_macro_bundle_v1/historical_opportunities/"
    "raw_ohlc_prequential_replay/path_ablation_v1_mtf"
)
RESOLVED_OUTCOMES = {"TP", "SL", "TIMEOUT", "BE_STOP", "LOCK_STOP"}
VARIANTS = [
    "BASE_RAW_FIXED_TP",
    "J46_J49_ONLY",
    "PATH_LOCK_CONSERVATIVE_V0",
    "PATH_LOCK_HALF_GAIN_V0",
    "PATH_LOCK_EARLY_BE_V0",
]
GROUPS = [
    "all_enabled",
    "target_cohorts",
    "primary_controlled_family",
    "cleared_non_primary_targets",
    "negative_controls",
    "blocked_dominance_controls",
]
TREATMENTS = ["exclude_unresolved", "samebar_breakeven", "samebar_pessimistic"]
COVERAGE_SUBSETS = {
    "M1_M5_ONLY": {"M1", "M5"},
    "M1_ONLY": {"M1"},
    "M5_ONLY": {"M5"},
    "M15_ONLY": {"M15"},
}


def run_disposition_analysis(
    *,
    event_log_path: str | Path = DEFAULT_EVENT_LOG_PATH,
) -> dict[str, Any]:
    events = load_events(event_log_path)
    treatment_stats = {}
    treatment_group_stats = {}
    treatment_cohort_stats = {}
    for treatment in TREATMENTS:
        stats, group_stats, cohort_stats = summarize(events, treatment=treatment)
        treatment_stats[treatment] = stats
        treatment_group_stats[treatment] = group_stats
        treatment_cohort_stats[treatment] = cohort_stats

    subset_stats = {}
    subset_group_stats = {}
    for name, timeframes in COVERAGE_SUBSETS.items():
        stats, group_stats, _cohort_stats = summarize(
            events,
            treatment="exclude_unresolved",
            selected_timeframes=timeframes,
        )
        subset_stats[name] = stats
        subset_group_stats[name] = group_stats

    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "code_commit": git_commit_or_unknown(),
        "event_log_path": str(Path(event_log_path)),
        "event_log_sha256": sha256_file(event_log_path),
        "promotion_verdict_allowed": False,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "v1_final_verdict": "REJECTED_FOR_EXIT_POLICY_PROMOTION",
        "v1_completion_status": "CLOSED_NO_BLOCKING_AMBIGUITY",
        "v1_path_resolution_layer_status": "ACCEPTED_AS_DIAGNOSTIC_INFRASTRUCTURE",
        "v2_gate": "NOT_AUTO_PROMOTED_FROM_V1",
        "research_boundary": [
            "Research/tooling only",
            "No live trading logic changes",
            "No prompt edits",
            "No parameter optimization",
            "No paid AI/API calls",
            "No V2/V3 implementation started",
        ],
        "registered_residual_same_bar_policy": {
            "headline": "Keep unresolved selected-row SAME_BAR outcomes excluded from mean-R headline metrics.",
            "decision_gate": "Use samebar_pessimistic (-1R) as the conservative stress treatment before considering any V1 exit-policy promotion.",
            "coverage_subsets": "M1/M5-only and M1-only views are diagnostic only, not final evidence, because lower-timeframe coverage is period-skewed.",
            "do_not_do": "Do not fabricate order inside M1/M5/M15 OHLC bars; do not silently drop same-bars without reporting counts; do not use M1/M5 coverage subset as final full-corpus evidence.",
        },
        "event_rows": len(events),
        "unique_setups": len({str(row.get("event_key")) for row in events}),
        "samebar_breakdown": samebar_breakdown(events),
        "treatment_variant_summary": treatment_variant_rows(treatment_stats),
        "treatment_group_delta_summary": treatment_group_delta_rows(treatment_group_stats),
        "coverage_subset_variant_summary": coverage_subset_variant_rows(subset_stats),
        "coverage_subset_group_delta_summary": coverage_subset_group_delta_rows(subset_group_stats),
        "cohort_best_summary": cohort_best_rows(treatment_cohort_stats),
    }
    summary["direct_answers"] = direct_answers(summary)
    summary["ambiguity_ledger"] = ambiguity_ledger(summary)
    summary["closed_questions"] = closed_questions(summary)
    summary["next_steps"] = next_steps()
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


def summarize(
    events: Sequence[Mapping[str, Any]],
    *,
    treatment: str,
    selected_timeframes: set[str] | None = None,
) -> tuple[dict[str, dict[str, Any]], dict[tuple[str, str], dict[str, Any]], dict[tuple[str, str, str], dict[str, Any]]]:
    stats: dict[str, dict[str, Any]] = defaultdict(new_state)
    group_stats: dict[tuple[str, str], dict[str, Any]] = defaultdict(new_state)
    cohort_stats: dict[tuple[str, str, str], dict[str, Any]] = defaultdict(new_state)
    for row in events:
        if selected_timeframes and row.get("v1_selected_timeframe") not in selected_timeframes:
            continue
        value = treated_value(row, treatment=treatment)
        if value is None:
            continue
        variant = str(row.get("variant_id") or "")
        cohort_key = str(row.get("raw_cohort_key") or "")
        role = str(row.get("role") or "unknown")
        add(stats[variant], value)
        for group in groups_for_key(cohort_key, role):
            add(group_stats[(variant, group)], value)
        add(cohort_stats[(variant, cohort_key, role)], value)
    return dict(stats), dict(group_stats), dict(cohort_stats)


def new_state() -> dict[str, Any]:
    return {"n": 0, "sum_r": 0.0, "wins": 0}


def add(state: dict[str, Any], value: float) -> None:
    state["n"] += 1
    state["sum_r"] += float(value)
    if value > 0:
        state["wins"] += 1


def treated_value(row: Mapping[str, Any], *, treatment: str) -> float | None:
    outcome = row.get("v1_outcome")
    gross = row.get("v1_gross_r")
    if outcome in RESOLVED_OUTCOMES and gross is not None:
        return float(gross)
    if outcome == "SAME_BAR" and treatment == "samebar_pessimistic":
        return -1.0
    if outcome == "SAME_BAR" and treatment == "samebar_breakeven":
        return 0.0
    return None


def samebar_breakdown(events: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    by_timeframe = Counter()
    unique_by_timeframe: dict[str, set[str]] = defaultdict(set)
    by_variant_timeframe = Counter()
    by_group = Counter()
    unique_by_group: dict[str, set[str]] = defaultdict(set)
    resolved_from_v0_by_timeframe = Counter()
    unique_resolved_from_v0_by_timeframe: dict[str, set[str]] = defaultdict(set)
    for row in events:
        timeframe = str(row.get("v1_selected_timeframe") or "")
        event_key = str(row.get("event_key") or "")
        if row.get("v0_outcome") == "SAME_BAR" and row.get("v1_outcome") in RESOLVED_OUTCOMES:
            resolved_from_v0_by_timeframe[timeframe] += 1
            unique_resolved_from_v0_by_timeframe[timeframe].add(event_key)
        if row.get("v1_outcome") != "SAME_BAR":
            continue
        by_timeframe[timeframe] += 1
        unique_by_timeframe[timeframe].add(event_key)
        by_variant_timeframe[(str(row.get("variant_id")), timeframe)] += 1
        for group in groups_for_key(str(row.get("raw_cohort_key") or ""), str(row.get("role") or "")):
            by_group[group] += 1
            unique_by_group[group].add(event_key)
    return {
        "policy_event_rows_by_timeframe": dict(sorted(by_timeframe.items())),
        "unique_setup_rows_by_timeframe": {key: len(value) for key, value in sorted(unique_by_timeframe.items())},
        "policy_event_rows_by_variant_timeframe": {
            f"{variant}|{timeframe}": count
            for (variant, timeframe), count in sorted(by_variant_timeframe.items())
        },
        "policy_event_rows_by_group": dict(sorted(by_group.items())),
        "unique_setup_rows_by_group": {key: len(value) for key, value in sorted(unique_by_group.items())},
        "v0_samebar_resolved_policy_rows_by_timeframe": dict(sorted(resolved_from_v0_by_timeframe.items())),
        "v0_samebar_resolved_unique_rows_by_timeframe": {
            key: len(value) for key, value in sorted(unique_resolved_from_v0_by_timeframe.items())
        },
    }


def treatment_variant_rows(treatment_stats: Mapping[str, Mapping[str, Mapping[str, Any]]]) -> list[dict[str, Any]]:
    rows = []
    for treatment in TREATMENTS:
        stats = treatment_stats.get(treatment) or {}
        best = best_variant(stats)
        for variant in VARIANTS:
            state = stats.get(variant) or new_state()
            rows.append(
                {
                    "treatment": treatment,
                    "variant_id": variant,
                    "n": state["n"],
                    "net_mean_r_cost_0.05": net_mean(state),
                    "net_sum_r_cost_0.05": net_sum(state),
                    "win_rate": rate_or_none(state["wins"], state["n"]),
                    "is_best": best == variant,
                }
            )
    return rows


def treatment_group_delta_rows(
    treatment_group_stats: Mapping[str, Mapping[tuple[str, str], Mapping[str, Any]]]
) -> list[dict[str, Any]]:
    rows = []
    for treatment in TREATMENTS:
        group_stats = treatment_group_stats.get(treatment) or {}
        for group in GROUPS:
            delta = best_lock_delta(group_stats, group)
            if delta:
                rows.append({"treatment": treatment, **delta})
    return rows


def coverage_subset_variant_rows(
    subset_stats: Mapping[str, Mapping[str, Mapping[str, Any]]]
) -> list[dict[str, Any]]:
    rows = []
    for subset_name in COVERAGE_SUBSETS:
        stats = subset_stats.get(subset_name) or {}
        best = best_variant(stats)
        for variant in VARIANTS:
            state = stats.get(variant) or new_state()
            rows.append(
                {
                    "subset": subset_name,
                    "variant_id": variant,
                    "n": state["n"],
                    "net_mean_r_cost_0.05": net_mean(state),
                    "net_sum_r_cost_0.05": net_sum(state),
                    "is_best": best == variant,
                }
            )
    return rows


def coverage_subset_group_delta_rows(
    subset_group_stats: Mapping[str, Mapping[tuple[str, str], Mapping[str, Any]]]
) -> list[dict[str, Any]]:
    rows = []
    for subset_name in COVERAGE_SUBSETS:
        group_stats = subset_group_stats.get(subset_name) or {}
        for group in GROUPS:
            delta = best_lock_delta(group_stats, group)
            if delta:
                rows.append({"subset": subset_name, **delta})
    return rows


def cohort_best_rows(
    treatment_cohort_stats: Mapping[str, Mapping[tuple[str, str, str], Mapping[str, Any]]]
) -> list[dict[str, Any]]:
    rows = []
    for treatment in ("exclude_unresolved", "samebar_pessimistic"):
        cohort_stats = treatment_cohort_stats.get(treatment) or {}
        cohorts = sorted({key[1:] for key in cohort_stats})
        for cohort_key, role in cohorts:
            candidates = []
            for variant in VARIANTS:
                state = cohort_stats.get((variant, cohort_key, role)) or new_state()
                if state["n"]:
                    candidates.append((float(net_mean(state)), variant, state["n"]))
            if not candidates:
                continue
            mean, variant, n = max(candidates)
            rows.append(
                {
                    "treatment": treatment,
                    "cohort_key": cohort_key,
                    "role": role,
                    "best_variant": variant,
                    "best_net_mean_r_cost_0.05": round(mean, 6),
                    "n": n,
                }
            )
    return rows


def best_variant(stats: Mapping[str, Mapping[str, Any]]) -> str | None:
    candidates = []
    for variant in VARIANTS:
        state = stats.get(variant) or new_state()
        if state["n"]:
            candidates.append((float(net_mean(state)), variant))
    return max(candidates)[1] if candidates else None


def best_lock_delta(
    group_stats: Mapping[tuple[str, str], Mapping[str, Any]],
    group: str,
) -> dict[str, Any] | None:
    j46 = group_stats.get(("J46_J49_ONLY", group)) or new_state()
    if not j46["n"]:
        return None
    locks = []
    for variant in VARIANTS:
        if not variant.startswith("PATH_LOCK"):
            continue
        state = group_stats.get((variant, group)) or new_state()
        if state["n"]:
            locks.append((float(net_mean(state)), variant, state))
    if not locks:
        return None
    lock_mean, lock_variant, lock_state = max(locks)
    j46_mean = float(net_mean(j46))
    return {
        "group": group,
        "j46_net_mean_r_cost_0.05": round(j46_mean, 6),
        "best_lock_variant": lock_variant,
        "best_lock_net_mean_r_cost_0.05": round(lock_mean, 6),
        "best_lock_minus_j46": round(lock_mean - j46_mean, 6),
        "j46_n": j46["n"],
        "best_lock_n": lock_state["n"],
    }


def net_mean(state: Mapping[str, Any], *, cost: float = 0.05) -> float | None:
    n = int(state.get("n") or 0)
    if not n:
        return None
    return round(float(state.get("sum_r") or 0.0) / n - cost, 6)


def net_sum(state: Mapping[str, Any], *, cost: float = 0.05) -> float | None:
    n = int(state.get("n") or 0)
    if not n:
        return None
    return round(float(state.get("sum_r") or 0.0) - cost * n, 6)


def direct_answers(summary: Mapping[str, Any]) -> list[dict[str, str]]:
    treatment_rows = summary.get("treatment_variant_summary") or []
    exclude_best = next(
        (row for row in treatment_rows if row.get("treatment") == "exclude_unresolved" and row.get("is_best")),
        {},
    )
    pess_best = next(
        (row for row in treatment_rows if row.get("treatment") == "samebar_pessimistic" and row.get("is_best")),
        {},
    )
    group_deltas = summary.get("treatment_group_delta_summary") or []
    target_exclude = find_group_delta(group_deltas, "exclude_unresolved", "target_cohorts")
    target_pess = find_group_delta(group_deltas, "samebar_pessimistic", "target_cohorts")
    same = summary.get("samebar_breakdown") or {}
    by_tf = same.get("policy_event_rows_by_timeframe") or {}
    resolved_by_tf = same.get("v0_samebar_resolved_policy_rows_by_timeframe") or {}
    return [
        {
            "question": "Is V1 promoted as an exit-policy candidate?",
            "answer": "No. V1 fixed-R lock-only is rejected for exit-policy promotion and remains NO_PROMOTION_VERDICT.",
        },
        {
            "question": "Is the V1 MTF path-resolution layer usable as diagnostic infrastructure?",
            "answer": "Yes. It is accepted as diagnostic infrastructure with a registered residual same-bar policy, not as alpha.",
        },
        {
            "question": "What wins under the headline unresolved-exclusion treatment?",
            "answer": f"{exclude_best.get('variant_id')} with net_mean_r_cost_0.05={exclude_best.get('net_mean_r_cost_0.05')}.",
        },
        {
            "question": "What wins under conservative same-bar pessimistic stress?",
            "answer": f"{pess_best.get('variant_id')} with net_mean_r_cost_0.05={pess_best.get('net_mean_r_cost_0.05')}.",
        },
        {
            "question": "Does the target-family lock-only advantage survive pessimistic stress?",
            "answer": (
                f"No. Exclude-unresolved target best-lock-minus-J46={target_exclude.get('best_lock_minus_j46')}; "
                f"samebar_pessimistic target best-lock-minus-J46={target_pess.get('best_lock_minus_j46')}."
            ),
        },
        {
            "question": "Are residual same-bars still ambiguous?",
            "answer": (
                "They are no longer an unclassified ambiguity: they are registered as unresolved headline exclusions "
                f"and -1R stress rows. Counts by selected timeframe are {by_tf}; V0 same-bars resolved by MTF are {resolved_by_tf}."
            ),
        },
        {
            "question": "Should V2 start automatically from V1?",
            "answer": "No. V1 does not auto-promote to V2; a future V2 would need a fresh registered structural-level hypothesis.",
        },
    ]


def find_group_delta(rows: Sequence[Mapping[str, Any]], treatment: str, group: str) -> Mapping[str, Any]:
    return next((row for row in rows if row.get("treatment") == treatment and row.get("group") == group), {})


def ambiguity_ledger(summary: Mapping[str, Any]) -> list[dict[str, str]]:
    same = summary.get("samebar_breakdown") or {}
    by_tf = same.get("policy_event_rows_by_timeframe") or {}
    return [
        {
            "item": "Residual same-bar handling",
            "status": "CLOSED_BY_REGISTERED_POLICY",
            "detail": (
                "Headline metrics keep SAME_BAR unresolved; decision-gate stress scores them as -1R. "
                f"Counts by selected timeframe: {by_tf}."
            ),
        },
        {
            "item": "M15 fallback coverage",
            "status": "CLOSED_AS_DATA_LIMITATION",
            "detail": "M15 fallback rows are not resolved or fabricated. They remain unresolved in headline metrics and pessimistic in stress metrics.",
        },
        {
            "item": "M5 without M1 coverage",
            "status": "CLOSED_AS_DATA_LIMITATION",
            "detail": "M5 same-bars are not accepted as ordered. They use the same unresolved/stress treatment.",
        },
        {
            "item": "M1 same-bars",
            "status": "CLOSED_AS_OHLC_GRANULARITY_LIMIT",
            "detail": "M1 OHLC cannot order intra-minute events. V1 does not fabricate tick order.",
        },
        {
            "item": "Coverage subset temptation",
            "status": "CLOSED_DIAGNOSTIC_ONLY",
            "detail": "M1/M5-only subsets are reported but not used as final evidence because coverage is period-skewed.",
        },
        {
            "item": "Promotion",
            "status": "REJECTED_FOR_EXIT_POLICY_PROMOTION",
            "detail": "J46-J49 remains best globally; target-family lock advantage does not survive samebar_pessimistic stress.",
        },
    ]


def closed_questions(summary: Mapping[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "question": "Should V2 proceed with M15 fallback same-bars carried as resolved?",
            "answer": "No. Carry them only as unresolved headline exclusions and pessimistic stress rows.",
            "status": "CLOSED",
        },
        {
            "question": "Should M5 same-bars be accepted where M1 coverage is absent?",
            "answer": "No. M5 same-bars remain unresolved/stressed; M5 does not establish intra-bar order.",
            "status": "CLOSED",
        },
        {
            "question": "Should M1 same-bars be dropped, pessimistically scored, or retained as unresolved?",
            "answer": "Retain as unresolved in headline metrics and score as -1R in stress metrics. Do not silently drop them.",
            "status": "CLOSED",
        },
        {
            "question": "Should V2 be limited to M1/M5-covered windows?",
            "answer": "No for final evidence. M1/M5-only is diagnostic because it sacrifices full-corpus comparability and is period-skewed.",
            "status": "CLOSED",
        },
    ]


def next_steps() -> list[dict[str, str]]:
    return [
        {
            "rank": "1",
            "next_step": "Stop V1 fixed-R lock-only promotion work.",
            "reason": "It does not beat J46-J49 globally and the target-family lock edge fails conservative same-bar stress.",
        },
        {
            "rank": "2",
            "next_step": "Do not start V2 automatically from V1.",
            "reason": "A future V2 must be registered as a new structural-level hypothesis, not as a promoted V1 continuation.",
        },
        {
            "rank": "3",
            "next_step": "If V2 is later approved, inherit V1's residual same-bar policy.",
            "reason": "This prevents structural levels from repairing V1 ambiguity post hoc.",
        },
    ]


def synthesis(summary: Mapping[str, Any]) -> list[str]:
    return [
        "V1 is closed. The MTF resolver is useful diagnostic infrastructure, but fixed-R lock-only V1 is rejected for exit-policy promotion.",
        "The ambiguity is no longer open-ended: residual selected-row SAME_BAR cases have a registered treatment, and coverage subsets are explicitly diagnostic-only.",
        "The decisive result is robustness failure. Under headline unresolved-exclusion, J46-J49 remains the best global variant; under samebar_pessimistic stress, J46-J49 still leads globally and the target-family lock-only advantage flips negative.",
        "V1 therefore does not auto-promote to V2. Any V2 work must be a separately registered structural-level hypothesis.",
    ]


def render_report(summary: Mapping[str, Any]) -> str:
    lines = [
        "# Raw-OHLC Path Scaling V1 Final Disposition",
        "",
        f"**Created UTC:** {summary.get('created_at_utc')}",
        f"**Event log:** `{summary.get('event_log_path')}`",
        f"**Event log SHA256:** `{summary.get('event_log_sha256')}`",
        f"**Promotion verdict:** `{summary.get('promotion_verdict')}`",
        f"**V1 final verdict:** `{summary.get('v1_final_verdict')}`",
        f"**V1 completion status:** `{summary.get('v1_completion_status')}`",
        f"**V2 gate:** `{summary.get('v2_gate')}`",
        "",
        "## Boundary",
        "",
        "\n".join(f"- {item}" for item in summary.get("research_boundary") or []),
        "",
        "## Registered Residual Same-Bar Policy",
        "",
        markdown_table([summary.get("registered_residual_same_bar_policy") or {}]),
        "",
        "## Direct Answers",
        "",
        markdown_table(summary.get("direct_answers") or []),
        "",
        "## Same-Bar Breakdown",
        "",
        markdown_table(flatten_samebar_rows(summary.get("samebar_breakdown") or {})),
        "",
        "## Treatment Variant Summary",
        "",
        markdown_table(summary.get("treatment_variant_summary") or []),
        "",
        "## Treatment Group Delta Summary",
        "",
        markdown_table(summary.get("treatment_group_delta_summary") or []),
        "",
        "## Coverage Subset Variant Summary",
        "",
        markdown_table(summary.get("coverage_subset_variant_summary") or []),
        "",
        "## Coverage Subset Group Delta Summary",
        "",
        markdown_table(summary.get("coverage_subset_group_delta_summary") or []),
        "",
        "## Cohort Best Summary",
        "",
        markdown_table(summary.get("cohort_best_summary") or []),
        "",
        "## Ambiguity Ledger",
        "",
        markdown_table(summary.get("ambiguity_ledger") or []),
        "",
        "## Closed Questions",
        "",
        markdown_table(summary.get("closed_questions") or []),
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


def flatten_samebar_rows(samebar: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = []
    by_tf = samebar.get("policy_event_rows_by_timeframe") or {}
    unique_by_tf = samebar.get("unique_setup_rows_by_timeframe") or {}
    resolved_by_tf = samebar.get("v0_samebar_resolved_policy_rows_by_timeframe") or {}
    resolved_unique_by_tf = samebar.get("v0_samebar_resolved_unique_rows_by_timeframe") or {}
    for timeframe in sorted(set(by_tf) | set(unique_by_tf) | set(resolved_by_tf)):
        rows.append(
            {
                "scope": "timeframe",
                "key": timeframe,
                "v1_samebar_policy_rows": by_tf.get(timeframe, 0),
                "v1_samebar_unique_setups": unique_by_tf.get(timeframe, 0),
                "v0_samebar_resolved_policy_rows": resolved_by_tf.get(timeframe, 0),
                "v0_samebar_resolved_unique_setups": resolved_unique_by_tf.get(timeframe, 0),
            }
        )
    by_group = samebar.get("policy_event_rows_by_group") or {}
    unique_by_group = samebar.get("unique_setup_rows_by_group") or {}
    for group in GROUPS:
        rows.append(
            {
                "scope": "group",
                "key": group,
                "v1_samebar_policy_rows": by_group.get(group, 0),
                "v1_samebar_unique_setups": unique_by_group.get(group, 0),
                "v0_samebar_resolved_policy_rows": None,
                "v0_samebar_resolved_unique_setups": None,
            }
        )
    return rows


def write_outputs(
    summary: Mapping[str, Any],
    *,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    report_path: str | Path = DEFAULT_REPORT_PATH,
) -> tuple[Path, Path]:
    output_dir = Path(output_root)
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    summary_path = output_dir / f"raw_ohlc_path_scaling_v1_disposition_{stamp}.json"
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
    summary = run_disposition_analysis(event_log_path=args.event_log)
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
                    "v1_final_verdict": summary.get("v1_final_verdict"),
                    "v1_completion_status": summary.get("v1_completion_status"),
                    "v2_gate": summary.get("v2_gate"),
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
