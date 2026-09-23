#!/usr/bin/env python3
"""Evaluate registered V2b OB-boundary validation on prospective event rows.

Research/tooling only. This script deliberately refuses to validate the V2b
hypothesis on the same event rows that discovered it. It reads a V2 structural
event JSONL, filters to rows strictly after the registered cutoff, recomputes
pairwise deltas for STRUCT_OB_BOUNDARY_V2, and writes an explicit gate ledger.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.analyze_raw_ohlc_replay_followups import groups_for_key  # noqa: E402
from scripts.audit_raw_ohlc_path_scaling_v2_concentration import (  # noqa: E402
    BASELINE_VARIANT,
    GROUPS,
    PairStats,
    _net_r,
    group_deltas,
)


DEFAULT_SPEC = (
    "research/phase_3_external_feed_validation/"
    "RAW_OHLC_PATH_SCALING_V2B_OB_BOUNDARY_VALIDATION_SPEC_V1.json"
)
DEFAULT_EVENT_LOG = (
    "data/external/validation/calendar_macro_bundle_v1/historical_opportunities/"
    "raw_ohlc_prequential_replay/path_scaling_v2_structural_levels/"
    "raw_ohlc_path_scaling_v2_structural_levels_events_20260501T213225Z.jsonl"
)
DEFAULT_SUMMARY_JSON = (
    "data/external/validation/calendar_macro_bundle_v1/historical_opportunities/"
    "raw_ohlc_prequential_replay/path_scaling_v2_structural_levels/"
    "raw_ohlc_path_scaling_v2_structural_levels_20260501T223136Z.json"
)
DEFAULT_OUTPUT_JSON = (
    "research/phase_3_external_feed_validation/"
    "RAW_OHLC_PATH_SCALING_V2B_PROSPECTIVE_VALIDATION_2026-05-02.json"
)
DEFAULT_OUTPUT_MD = (
    "research/phase_3_external_feed_validation/"
    "RAW_OHLC_PATH_SCALING_V2B_PROSPECTIVE_VALIDATION_2026-05-02.md"
)

PRIMARY_VARIANT = "STRUCT_OB_BOUNDARY_V2"
DEFAULT_COMPARATORS = (
    BASELINE_VARIANT,
    "STRUCT_SWING_PROTECTED_V2",
    "STRUCT_FVG_MID_EDGE_V2",
    "PATH_LOCK_HALF_GAIN_V0",
)
DEFAULT_MIN_ALL_ENABLED = 150
DEFAULT_MIN_TARGET = 75
MAX_SINGLE_COHORT_SHARE = 0.45


def parse_utc(value: str) -> datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def load_json(path: Path | str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def cutoff_from_spec(spec: dict[str, Any]) -> datetime:
    lane = str((spec.get("validation_data_policy") or {}).get("preferred_lane") or "")
    match = re.search(r"prospective_after_([^ ]+)$", lane)
    if not match:
        raise ValueError(f"could not parse preferred_lane cutoff from spec: {lane!r}")
    return parse_utc(match.group(1))


def _wanted_variants(spec: dict[str, Any]) -> set[str]:
    primary = ((spec.get("primary_candidate") or {}).get("variant_id")) or PRIMARY_VARIANT
    comparisons = set(spec.get("comparison_arms") or DEFAULT_COMPARATORS)
    comparisons.add(BASELINE_VARIANT)
    comparisons.add(primary)
    return comparisons


def _counter_dict(counter: Counter[str]) -> dict[str, int]:
    return {key: counter[key] for key in sorted(counter)}


def _missing_net_r_reason(row: dict[str, Any]) -> str:
    outcome = row.get("outcome") or "none"
    skip_reason = row.get("skip_reason") or "none"
    fallback_reason = row.get("fallback_reason") or "none"
    return f"outcome={outcome}|skip={skip_reason}|fallback={fallback_reason}"


def load_event_rows_after_cutoff(
    event_log_path: Path | str,
    *,
    cutoff: datetime,
    wanted_variants: Iterable[str],
    cost_key: str,
) -> tuple[dict[str, dict[str, dict[str, Any]]], dict[str, Any], dict[str, Any]]:
    wanted = set(wanted_variants)
    by_event: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    selected_tf_after_cutoff: Counter[str] = Counter()
    selected_tf_wanted_after_cutoff: Counter[str] = Counter()
    selected_tf_wanted_resolved_after_cutoff: Counter[str] = Counter()
    missing_net_r_by_variant: Counter[str] = Counter()
    missing_net_r_by_outcome: Counter[str] = Counter()
    missing_net_r_by_skip_reason: Counter[str] = Counter()
    missing_net_r_by_fallback_reason: Counter[str] = Counter()
    missing_net_r_by_selected_timeframe: Counter[str] = Counter()
    missing_net_r_by_reason: Counter[str] = Counter()
    missing_net_r_examples: list[dict[str, Any]] = []
    counters = {
        "total_rows_seen": 0,
        "wanted_variant_rows_seen": 0,
        "rows_after_cutoff": 0,
        "wanted_rows_after_cutoff": 0,
        "wanted_resolved_rows_after_cutoff": 0,
        "rows_rejected_at_or_before_cutoff": 0,
        "rows_missing_candle_close": 0,
        "rows_missing_net_r": 0,
        "first_candle_close_utc": None,
        "last_candle_close_utc": None,
        "first_prospective_candle_close_utc": None,
        "last_prospective_candle_close_utc": None,
    }
    with Path(event_log_path).open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            counters["total_rows_seen"] += 1
            row = json.loads(line)
            candle = row.get("candle_close_utc")
            if not candle:
                counters["rows_missing_candle_close"] += 1
                continue
            candle_dt = parse_utc(str(candle))
            candle_iso = candle_dt.isoformat()
            counters["first_candle_close_utc"] = counters["first_candle_close_utc"] or candle_iso
            counters["last_candle_close_utc"] = candle_iso
            if row.get("variant_id") in wanted:
                counters["wanted_variant_rows_seen"] += 1
            if candle_dt <= cutoff:
                counters["rows_rejected_at_or_before_cutoff"] += 1
                continue
            counters["rows_after_cutoff"] += 1
            selected_timeframe = str(row.get("selected_timeframe") or "UNKNOWN")
            selected_tf_after_cutoff[selected_timeframe] += 1
            counters["first_prospective_candle_close_utc"] = (
                counters["first_prospective_candle_close_utc"] or candle_iso
            )
            counters["last_prospective_candle_close_utc"] = candle_iso
            variant = row.get("variant_id")
            if variant not in wanted:
                continue
            counters["wanted_rows_after_cutoff"] += 1
            selected_tf_wanted_after_cutoff[selected_timeframe] += 1
            if _net_r(row, cost_key=cost_key) is None:
                counters["rows_missing_net_r"] += 1
                missing_net_r_by_variant[str(variant)] += 1
                missing_net_r_by_outcome[str(row.get("outcome") or "none")] += 1
                missing_net_r_by_skip_reason[str(row.get("skip_reason") or "none")] += 1
                missing_net_r_by_fallback_reason[str(row.get("fallback_reason") or "none")] += 1
                missing_net_r_by_selected_timeframe[selected_timeframe] += 1
                missing_net_r_by_reason[_missing_net_r_reason(row)] += 1
                if len(missing_net_r_examples) < 10:
                    missing_net_r_examples.append(
                        {
                            "event_key": row.get("event_key"),
                            "variant_id": variant,
                            "candle_close_utc": candle_iso,
                            "selected_timeframe": selected_timeframe,
                            "outcome": row.get("outcome"),
                            "skip_reason": row.get("skip_reason"),
                            "fallback_reason": row.get("fallback_reason"),
                        }
                    )
                continue
            counters["wanted_resolved_rows_after_cutoff"] += 1
            selected_tf_wanted_resolved_after_cutoff[selected_timeframe] += 1
            by_event[str(row["event_key"])][str(variant)] = row
    wanted_tf_counts = _counter_dict(selected_tf_wanted_after_cutoff)
    wanted_tf_resolved_counts = _counter_dict(selected_tf_wanted_resolved_after_cutoff)
    wanted_lower_tf_n = sum(
        selected_tf_wanted_after_cutoff[tf] for tf in ("M1", "M5")
    )
    wanted_resolved_lower_tf_n = sum(
        selected_tf_wanted_resolved_after_cutoff[tf] for tf in ("M1", "M5")
    )
    row_diagnostics = {
        "lower_tf_availability": {
            "selected_timeframe_counts_after_cutoff": _counter_dict(selected_tf_after_cutoff),
            "wanted_selected_timeframe_counts_after_cutoff": wanted_tf_counts,
            "wanted_resolved_selected_timeframe_counts_after_cutoff": wanted_tf_resolved_counts,
            "wanted_lower_tf_rows_after_cutoff": wanted_lower_tf_n,
            "wanted_lower_tf_rate_after_cutoff": round(
                wanted_lower_tf_n / counters["wanted_rows_after_cutoff"], 6
            )
            if counters["wanted_rows_after_cutoff"]
            else None,
            "wanted_resolved_lower_tf_rows_after_cutoff": wanted_resolved_lower_tf_n,
            "wanted_resolved_lower_tf_rate_after_cutoff": round(
                wanted_resolved_lower_tf_n / counters["wanted_resolved_rows_after_cutoff"], 6
            )
            if counters["wanted_resolved_rows_after_cutoff"]
            else None,
        },
        "missing_net_r": {
            "rows_missing_net_r": counters["rows_missing_net_r"],
            "by_variant": _counter_dict(missing_net_r_by_variant),
            "by_outcome": _counter_dict(missing_net_r_by_outcome),
            "by_skip_reason": _counter_dict(missing_net_r_by_skip_reason),
            "by_fallback_reason": _counter_dict(missing_net_r_by_fallback_reason),
            "by_selected_timeframe": _counter_dict(missing_net_r_by_selected_timeframe),
            "by_reason": _counter_dict(missing_net_r_by_reason),
            "examples": missing_net_r_examples,
        },
    }
    return by_event, counters, row_diagnostics


def pairwise_candidate_vs_comparator(
    by_event: dict[str, dict[str, dict[str, Any]]],
    *,
    candidate_variant: str,
    comparator_variant: str,
    cost_key: str,
) -> PairStats:
    stats = PairStats()
    for variants in by_event.values():
        baseline = variants.get(comparator_variant)
        candidate = variants.get(candidate_variant)
        if baseline is None or candidate is None:
            continue
        baseline_r = _net_r(baseline, cost_key=cost_key)
        candidate_r = _net_r(candidate, cost_key=cost_key)
        if baseline_r is None or candidate_r is None:
            continue
        stats.add(
            baseline_r=baseline_r,
            candidate_r=candidate_r,
            row={
                "event_key": candidate.get("event_key"),
                "symbol": candidate.get("symbol"),
                "session": candidate.get("session"),
                "selected_timeframe": candidate.get("selected_timeframe"),
                "side": candidate.get("mechanical_side") or "none",
                "role": candidate.get("role"),
                "raw_cohort_key": candidate.get("raw_cohort_key"),
                "baseline_r": baseline_r,
                "candidate_r": candidate_r,
                "delta_r": candidate_r - baseline_r,
            },
        )
    return stats


def _gate(status: str, *, passed: bool | None, detail: str, metrics: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "status": status,
        "passed": passed,
        "detail": detail,
        "metrics": metrics or {},
    }


def _group_lookup(stats: PairStats) -> dict[str, dict[str, Any]]:
    return {row["group"]: row for row in group_deltas(stats)}


def _raw_cohort_rows(stats: PairStats) -> list[dict[str, Any]]:
    buckets: dict[str, PairStats] = defaultdict(PairStats)
    roles: dict[str, set[str]] = defaultdict(set)
    for row in stats.rows:
        key = str(row.get("raw_cohort_key") or "none")
        roles[key].add(str(row.get("role") or "none"))
        buckets[key].add(baseline_r=float(row["baseline_r"]), candidate_r=float(row["candidate_r"]))
    out = []
    for key, bucket in buckets.items():
        summary = bucket.to_summary()
        summary["raw_cohort_key"] = key
        summary["roles"] = sorted(roles[key])
        group_names = set()
        for role in roles[key]:
            group_names.update(groups_for_key(key, role))
        summary["groups"] = sorted(group_names)
        out.append(summary)
    return sorted(out, key=lambda item: item["sum_delta_candidate_minus_baseline"], reverse=True)


def _cohort_breadth_metrics(cohort_rows: list[dict[str, Any]]) -> dict[str, Any]:
    positives = [row for row in cohort_rows if row["sum_delta_candidate_minus_baseline"] > 0]
    positive_sum = sum(row["sum_delta_candidate_minus_baseline"] for row in positives)
    top_positive = positives[0]["sum_delta_candidate_minus_baseline"] if positives else 0.0
    non_blocked_positive = [
        row for row in positives if "blocked_dominance_controls" not in set(row.get("groups") or [])
    ]
    return {
        "positive_raw_cohort_count": len(positives),
        "non_blocked_positive_raw_cohort_count": len(non_blocked_positive),
        "positive_sum_delta": round(positive_sum, 6),
        "largest_positive_raw_cohort_share": round(top_positive / positive_sum, 6) if positive_sum else None,
        "top_positive_raw_cohort": positives[0]["raw_cohort_key"] if positives else None,
    }


def _no_leak_gate(summary_json: dict[str, Any] | None) -> dict[str, Any]:
    if not summary_json:
        return _gate(
            "NOT_EVALUABLE_FROM_EVENT_LOG",
            passed=None,
            detail="No runner summary JSON supplied; event JSONL alone cannot prove lower-TF start discipline.",
        )
    coverage = summary_json.get("coverage_diagnostics") or {}
    violations = coverage.get("lower_tf_start_violations")
    if violations is None:
        return _gate(
            "NOT_EVALUABLE_FROM_SUMMARY",
            passed=None,
            detail="Runner summary lacks coverage_diagnostics.lower_tf_start_violations.",
            metrics={"coverage_diagnostics": coverage},
        )
    passed = int(violations) == 0
    return _gate(
        "PASS" if passed else "FAIL",
        passed=passed,
        detail="Runner summary lower-TF no-leak diagnostic checked.",
        metrics={"lower_tf_start_violations": int(violations)},
    )


def evaluate_gates(
    candidate_stats: PairStats,
    *,
    min_all_enabled_n: int,
    min_target_n: int,
    no_leak_gate: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    pair = candidate_stats.to_summary()
    groups = _group_lookup(candidate_stats)
    cohort_rows = _raw_cohort_rows(candidate_stats)
    cohort_metrics = _cohort_breadth_metrics(cohort_rows)
    if pair["paired_resolved_n"] == 0:
        not_eval = {
            name: _gate(
                "NOT_EVALUABLE_NO_PROSPECTIVE_PAIRS",
                passed=None,
                detail="No resolved prospective OB-boundary/J46 pairs exist after the registered cutoff.",
            )
            for name in (
                "global_pairwise_positive",
                "all_major_groups_nonnegative",
                "target_not_weaker_than_negative_controls",
                "blocked_controls_not_driver",
                "cohort_breadth",
                "single_cohort_cap",
                "sample_floor",
            )
        }
        not_eval["no_leak"] = no_leak_gate
        diagnostics = {
            "pairwise_vs_j46": pair,
            "group_deltas": [groups.get(group) | {"group": group} for group in GROUPS if groups.get(group)],
            "raw_cohort_rows": cohort_rows,
            "cohort_breadth": cohort_metrics,
        }
        return not_eval, diagnostics

    target = groups.get("target_cohorts") or {}
    negative = groups.get("negative_controls") or {}
    blocked = groups.get("blocked_dominance_controls") or {}

    all_groups_to_check = [
        "all_enabled",
        "target_cohorts",
        "primary_controlled_family",
        "cleared_non_primary_targets",
        "negative_controls",
        "blocked_dominance_controls",
    ]

    all_enabled_delta = pair["sum_delta_candidate_minus_baseline"]
    group_sums = {
        "all_enabled": all_enabled_delta,
        **{
            group: (groups.get(group) or {}).get("sum_delta_candidate_minus_baseline")
            for group in all_groups_to_check
            if group != "all_enabled"
        },
    }
    all_major_nonnegative = all(value is not None and value >= 0 for value in group_sums.values())

    target_mean = target.get("mean_delta_candidate_minus_baseline")
    negative_mean = negative.get("mean_delta_candidate_minus_baseline")
    target_sum = target.get("sum_delta_candidate_minus_baseline")
    blocked_sum = blocked.get("sum_delta_candidate_minus_baseline")

    gates = {
        "global_pairwise_positive": _gate(
            "PASS" if pair["mean_delta_candidate_minus_baseline"] is not None and pair["mean_delta_candidate_minus_baseline"] > 0 else "FAIL",
            passed=pair["mean_delta_candidate_minus_baseline"] is not None
            and pair["mean_delta_candidate_minus_baseline"] > 0,
            detail="OB-boundary pairwise mean delta vs J46 at selected cost must be positive.",
            metrics={
                "paired_resolved_n": pair["paired_resolved_n"],
                "mean_delta_candidate_minus_baseline": pair["mean_delta_candidate_minus_baseline"],
                "sum_delta_candidate_minus_baseline": pair["sum_delta_candidate_minus_baseline"],
            },
        ),
        "all_major_groups_nonnegative": _gate(
            "PASS" if all_major_nonnegative else "FAIL",
            passed=all_major_nonnegative,
            detail="All major group-family deltas must be nonnegative.",
            metrics=group_sums,
        ),
        "target_not_weaker_than_negative_controls": _gate(
            "PASS" if target_mean is not None and negative_mean is not None and target_mean > negative_mean else "FAIL",
            passed=target_mean is not None and negative_mean is not None and target_mean > negative_mean,
            detail="Target-cohort mean delta must exceed negative-controls mean delta.",
            metrics={
                "target_cohorts_mean_delta": target_mean,
                "negative_controls_mean_delta": negative_mean,
            },
        ),
        "blocked_controls_not_driver": _gate(
            "PASS" if blocked_sum is not None and target_sum is not None and blocked_sum < target_sum else "FAIL",
            passed=blocked_sum is not None and target_sum is not None and blocked_sum < target_sum,
            detail="Blocked-control sum lift must be smaller than target-cohort sum lift.",
            metrics={
                "blocked_dominance_controls_sum_delta": blocked_sum,
                "target_cohorts_sum_delta": target_sum,
            },
        ),
        "cohort_breadth": _gate(
            "PASS"
            if cohort_metrics["positive_raw_cohort_count"] >= 5
            and cohort_metrics["non_blocked_positive_raw_cohort_count"] >= 3
            else "FAIL",
            passed=cohort_metrics["positive_raw_cohort_count"] >= 5
            and cohort_metrics["non_blocked_positive_raw_cohort_count"] >= 3,
            detail="At least 5 raw cohorts positive, with at least 3 non-blocked-control positive cohorts.",
            metrics=cohort_metrics,
        ),
        "single_cohort_cap": _gate(
            "PASS"
            if cohort_metrics["largest_positive_raw_cohort_share"] is not None
            and cohort_metrics["largest_positive_raw_cohort_share"] <= MAX_SINGLE_COHORT_SHARE
            else "FAIL",
            passed=cohort_metrics["largest_positive_raw_cohort_share"] is not None
            and cohort_metrics["largest_positive_raw_cohort_share"] <= MAX_SINGLE_COHORT_SHARE,
            detail=f"Largest positive raw cohort must contribute <= {MAX_SINGLE_COHORT_SHARE:.0%} of positive lift.",
            metrics=cohort_metrics,
        ),
        "sample_floor": _gate(
            "PASS"
            if pair["paired_resolved_n"] >= min_all_enabled_n
            and (target.get("paired_resolved_n") or 0) >= min_target_n
            else "FAIL",
            passed=pair["paired_resolved_n"] >= min_all_enabled_n
            and (target.get("paired_resolved_n") or 0) >= min_target_n,
            detail="Prospective interim sample floor must be met before validation readout.",
            metrics={
                "all_enabled_paired_resolved_n": pair["paired_resolved_n"],
                "target_cohorts_paired_resolved_n": target.get("paired_resolved_n") or 0,
                "min_all_enabled_n": min_all_enabled_n,
                "min_target_cohorts_n": min_target_n,
            },
        ),
        "no_leak": no_leak_gate,
    }

    diagnostics = {
        "pairwise_vs_j46": pair,
        "group_deltas": [groups.get(group) | {"group": group} for group in GROUPS if groups.get(group)],
        "raw_cohort_rows": cohort_rows,
        "cohort_breadth": cohort_metrics,
    }
    return gates, diagnostics


def validation_status(
    *,
    prospective_rows_n: int,
    prospective_wanted_rows_n: int,
    prospective_pair_n: int,
    gates: dict[str, Any],
) -> str:
    if prospective_rows_n == 0:
        return "BLOCKED_NO_POST_CUTOFF_ROWS"
    if prospective_wanted_rows_n == 0:
        return "BLOCKED_NO_WANTED_POST_CUTOFF_ROWS"
    if prospective_pair_n == 0:
        return "BLOCKED_NO_RESOLVED_PROSPECTIVE_PAIRS"
    failed = [name for name, gate in gates.items() if gate.get("passed") is False]
    unknown = [name for name, gate in gates.items() if gate.get("passed") is None]
    if failed:
        if failed == ["sample_floor"] or "sample_floor" in failed:
            return "INTERIM_NOT_EVALUABLE_SAMPLE_FLOOR"
        return "RESEARCH_VALIDATION_FAIL_NO_PROMOTION"
    if unknown:
        return "BLOCKED_BY_UNVERIFIED_METHODOLOGY_DIAGNOSTIC"
    return "RESEARCH_VALIDATION_PASS_NO_PROMOTION"


def status_ladder(
    *,
    counters: dict[str, Any],
    prospective_pair_n: int,
    gates: dict[str, Any],
) -> list[dict[str, Any]]:
    rows_after_cutoff = int(counters.get("rows_after_cutoff") or 0)
    wanted_rows_after_cutoff = int(counters.get("wanted_rows_after_cutoff") or 0)
    sample_gate = gates.get("sample_floor") or {}
    sample_passed = sample_gate.get("passed")
    if prospective_pair_n == 0:
        sample_status = "NOT_EVALUABLE_NO_RESOLVED_PAIRS"
    elif sample_passed is True:
        sample_status = "SAMPLE_FLOOR_REACHED"
    else:
        sample_status = "BELOW_SAMPLE_FLOOR"
    return [
        {
            "step": "post_cutoff_rows",
            "status": "PASS" if rows_after_cutoff > 0 else "BLOCKED_NO_POST_CUTOFF_ROWS",
            "passed": rows_after_cutoff > 0,
            "count": rows_after_cutoff,
        },
        {
            "step": "wanted_post_cutoff_rows",
            "status": "PASS" if wanted_rows_after_cutoff > 0 else "BLOCKED_NO_WANTED_POST_CUTOFF_ROWS",
            "passed": wanted_rows_after_cutoff > 0,
            "count": wanted_rows_after_cutoff,
        },
        {
            "step": "resolved_pairs",
            "status": "PASS" if prospective_pair_n > 0 else "BLOCKED_NO_RESOLVED_PROSPECTIVE_PAIRS",
            "passed": prospective_pair_n > 0,
            "count": prospective_pair_n,
        },
        {
            "step": "sample_floor",
            "status": sample_status,
            "passed": sample_passed,
            "metrics": sample_gate.get("metrics") or {},
        },
    ]


def build_payload(
    *,
    spec_path: Path | str,
    event_log_path: Path | str,
    runner_summary_path: Path | str | None,
    cutoff: datetime | None = None,
    cost_key: str = "0.05",
    min_all_enabled_n: int = DEFAULT_MIN_ALL_ENABLED,
    min_target_n: int = DEFAULT_MIN_TARGET,
) -> dict[str, Any]:
    spec = load_json(spec_path)
    cutoff = cutoff or cutoff_from_spec(spec)
    wanted = _wanted_variants(spec)
    by_event, counters, row_diagnostics = load_event_rows_after_cutoff(
        event_log_path,
        cutoff=cutoff,
        wanted_variants=wanted,
        cost_key=cost_key,
    )
    runner_summary = load_json(runner_summary_path) if runner_summary_path and Path(runner_summary_path).exists() else None

    pairwise = {
        comparator: pairwise_candidate_vs_comparator(
            by_event,
            candidate_variant=PRIMARY_VARIANT,
            comparator_variant=comparator,
            cost_key=cost_key,
        ).to_summary()
        for comparator in DEFAULT_COMPARATORS
        if comparator != PRIMARY_VARIANT
    }
    candidate_stats = pairwise_candidate_vs_comparator(
        by_event,
        candidate_variant=PRIMARY_VARIANT,
        comparator_variant=BASELINE_VARIANT,
        cost_key=cost_key,
    )
    gates, diagnostics = evaluate_gates(
        candidate_stats,
        min_all_enabled_n=min_all_enabled_n,
        min_target_n=min_target_n,
        no_leak_gate=_no_leak_gate(runner_summary),
    )
    status = validation_status(
        prospective_rows_n=int(counters.get("rows_after_cutoff") or 0),
        prospective_wanted_rows_n=int(counters.get("wanted_rows_after_cutoff") or 0),
        prospective_pair_n=candidate_stats.paired_resolved_n,
        gates=gates,
    )
    has_prospective_rows = int(counters.get("rows_after_cutoff") or 0) > 0
    has_wanted_rows = int(counters.get("wanted_rows_after_cutoff") or 0) > 0
    has_resolved_pairs = candidate_stats.paired_resolved_n > 0
    if not has_prospective_rows:
        summary = (
            "V2b remains unvalidated because the current V2 event log contains no event rows "
            "strictly after the registered cutoff."
        )
    elif not has_wanted_rows:
        summary = (
            "V2b remains unvalidated because post-cutoff event rows exist, but none are in "
            "the registered OB-boundary/J46 comparison set."
        )
    elif not has_resolved_pairs:
        summary = (
            "V2b remains unvalidated because post-cutoff OB-boundary/J46 rows exist, but no "
            "resolved STRUCT_OB_BOUNDARY_V2/J46 pairs exist after the registered cutoff."
        )
    else:
        summary = "V2b prospective rows were evaluated against the registered research-only gates."
    payload = {
        "schema_version": "raw_ohlc_path_scaling_v2b_prospective_validation_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_status": status,
        "inputs": {
            "spec_path": str(spec_path),
            "event_log_path": str(event_log_path),
            "runner_summary_path": str(runner_summary_path) if runner_summary_path else None,
            "cutoff_utc": cutoff.isoformat(),
            "cutoff_policy": "strictly_after_cutoff",
            "cost_key": cost_key,
            "primary_variant": PRIMARY_VARIANT,
            "comparators": list(DEFAULT_COMPARATORS),
            "min_all_enabled_n": min_all_enabled_n,
            "min_target_n": min_target_n,
        },
        "scope_counters": counters,
        "pairwise_candidate_vs_comparators": pairwise,
        "acceptance_gates": gates,
        "status_ladder": status_ladder(
            counters=counters,
            prospective_pair_n=candidate_stats.paired_resolved_n,
            gates=gates,
        ),
        "diagnostics": diagnostics,
        "row_diagnostics": row_diagnostics,
        "synthesis": {
            "summary": summary,
            "answered_questions": [
                (
                    "Does the current available V2 event log contain any prospective event rows after the registered cutoff? "
                    + ("Yes." if has_prospective_rows else "No.")
                ),
                (
                    "Does it contain registered V2b OB-boundary/J46 rows after the cutoff? "
                    + ("Yes." if has_wanted_rows else "No.")
                ),
                (
                    "Does it contain resolved STRUCT_OB_BOUNDARY_V2/J46 pairs after the cutoff? "
                    + ("Yes." if has_resolved_pairs else "No.")
                ),
                "Can same-event V2 rows validate V2b? No; rows at or before the cutoff are explicitly excluded.",
                "Does the evaluator log missing net-R reasons and lower-TF availability? Yes; see row_diagnostics.",
                "Can V2b promote live logic from this evaluator? No; every output keeps NO_PROMOTION_VERDICT.",
            ],
            "ambiguity_ledger": [
                "Prospective V2b validation depends on future event rows after the cutoff; discovery-set lift remains non-promotional.",
                "Cost remains an R-sensitivity model, not true broker spread/slippage reconstruction.",
                "No-leak discipline can be checked only when the runner summary exposes lower-TF start diagnostics.",
                "Sample floors are intentionally conservative; small positive forward samples must remain interim only.",
            ],
            "opened_questions": [
                "Will OB-boundary remain positive once enough post-cutoff rows accumulate?",
                "Will target cohorts still beat negative controls outside the discovery event log?",
                "Will raw-cohort breadth survive, or collapse into one symbol/session pocket?",
                "Does OB-boundary keep lower right-tail truncation than swing/FVG on future rows?",
            ],
            "next_steps": [
                "Keep collecting/replaying prospective rows after 2026-04-30T17:00:00+00:00 until sample floors are met or the hypothesis fails early.",
                "Do not treat V3 reentry discovery results as validation until this V2b level-quality question is answered on unseen rows.",
                "If broad V2b fails but one cohort persists, register a fresh cohort-specific hypothesis before testing it.",
                "Preserve NO_PROMOTION_VERDICT until a separate promotion dossier exists.",
            ],
        },
    }
    return payload


def write_json(payload: dict[str, Any], path: Path | str) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.6f}"
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True).replace("|", r"\|")
    return str(value).replace("|", r"\|")


def _table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        out.append("| " + " | ".join(_fmt(value) for value in row) + " |")
    return out


def write_markdown(payload: dict[str, Any], path: Path | str) -> None:
    out = Path(path)
    synth = payload["synthesis"]
    gates = payload["acceptance_gates"]
    pairwise = payload["pairwise_candidate_vs_comparators"]
    lines = [
        "# V2b OB-Boundary Rolling Status Tool",
        "",
        "Date: 2026-05-02",
        "Scope: research/tooling only",
        f"Promotion verdict: `{payload['promotion_verdict']}`",
        f"Validation status: `{payload['validation_status']}`",
        "",
        "## Synthesis",
        "",
        synth["summary"],
        "",
        "## Scope Counters",
        "",
        *_table(
            ["Metric", "Value"],
            [[key, value] for key, value in payload["scope_counters"].items()],
        ),
        "",
        "## Rolling Status Ladder",
        "",
        *_table(
            ["Step", "Status", "Passed", "Count", "Metrics"],
            [
                [
                    row["step"],
                    row["status"],
                    row.get("passed"),
                    row.get("count"),
                    row.get("metrics"),
                ]
                for row in payload["status_ladder"]
            ],
        ),
        "",
        "## Missing Net-R Diagnostics",
        "",
        *_table(
            ["Metric", "Value"],
            [[key, value] for key, value in payload["row_diagnostics"]["missing_net_r"].items() if key != "examples"],
        ),
        "",
        "## Lower-Timeframe Availability",
        "",
        *_table(
            ["Metric", "Value"],
            [[key, value] for key, value in payload["row_diagnostics"]["lower_tf_availability"].items()],
        ),
        "",
        "## Pairwise Candidate Versus Comparators",
        "",
        *_table(
            ["Comparator", "paired n", "mean delta", "sum delta", "candidate better", "comparator better"],
            [
                [
                    comparator,
                    row["paired_resolved_n"],
                    row["mean_delta_candidate_minus_baseline"],
                    row["sum_delta_candidate_minus_baseline"],
                    row["candidate_better_n"],
                    row["baseline_better_n"],
                ]
                for comparator, row in pairwise.items()
            ],
        ),
        "",
        "## Acceptance Gates",
        "",
        *_table(
            ["Gate", "Status", "Passed", "Detail"],
            [[name, gate["status"], gate["passed"], gate["detail"]] for name, gate in gates.items()],
        ),
        "",
        "## OB Boundary Group Deltas",
        "",
        *_table(
            ["Group", "paired n", "mean delta", "sum delta"],
            [
                [
                    row["group"],
                    row["paired_resolved_n"],
                    row["mean_delta_candidate_minus_baseline"],
                    row["sum_delta_candidate_minus_baseline"],
                ]
                for row in payload["diagnostics"]["group_deltas"]
            ],
        ),
        "",
        "## Top Raw Cohorts",
        "",
        *_table(
            ["Cohort", "paired n", "mean delta", "sum delta", "groups"],
            [
                [
                    row["raw_cohort_key"],
                    row["paired_resolved_n"],
                    row["mean_delta_candidate_minus_baseline"],
                    row["sum_delta_candidate_minus_baseline"],
                    ",".join(row.get("groups") or []),
                ]
                for row in payload["diagnostics"]["raw_cohort_rows"][:10]
            ],
        ),
        "",
        "## Answered Questions",
        "",
        *[f"- {item}" for item in synth["answered_questions"]],
        "",
        "## Ambiguity Ledger",
        "",
        *[f"- {item}" for item in synth["ambiguity_ledger"]],
        "",
        "## Opened Questions",
        "",
        *[f"{idx}. {item}" for idx, item in enumerate(synth["opened_questions"], start=1)],
        "",
        "## Next Steps",
        "",
        *[f"{idx}. {item}" for idx, item in enumerate(synth["next_steps"], start=1)],
        "",
    ]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", default=DEFAULT_SPEC)
    parser.add_argument("--event-log", default=DEFAULT_EVENT_LOG)
    parser.add_argument("--runner-summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--cutoff")
    parser.add_argument("--cost-key", default="0.05")
    parser.add_argument("--min-all-enabled-n", type=int, default=DEFAULT_MIN_ALL_ENABLED)
    parser.add_argument("--min-target-n", type=int, default=DEFAULT_MIN_TARGET)
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = build_payload(
        spec_path=args.spec,
        event_log_path=args.event_log,
        runner_summary_path=args.runner_summary_json,
        cutoff=parse_utc(args.cutoff) if args.cutoff else None,
        cost_key=args.cost_key,
        min_all_enabled_n=args.min_all_enabled_n,
        min_target_n=args.min_target_n,
    )
    write_json(payload, args.output_json)
    write_markdown(payload, args.output_md)
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")
    print(
        f"status={payload['validation_status']} "
        f"pairs={payload['diagnostics']['pairwise_vs_j46']['paired_resolved_n']} "
        f"cutoff={payload['inputs']['cutoff_utc']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
