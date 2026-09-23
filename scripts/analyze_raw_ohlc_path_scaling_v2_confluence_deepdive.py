#!/usr/bin/env python3
"""Deep-dive V2 structural confluence/disagreement diagnostics.

Research/tooling only. This script uses the existing V2 event log and compares
alternative path-management variants on the same event keys. It does not treat
same-dataset selected lifts as validation and never emits a promotion verdict.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import analyze_raw_ohlc_path_scaling_v2_confluence as base

DEFAULT_EVENT_LOG = base.DEFAULT_EVENT_LOG
DEFAULT_OUTPUT_JSON = (
    "research/phase_3_external_feed_validation/"
    "RAW_OHLC_PATH_SCALING_V2_CONFLUENCE_DEEPDIVE_2026-05-03.json"
)
DEFAULT_OUTPUT_MD = (
    "research/phase_3_external_feed_validation/"
    "RAW_OHLC_PATH_SCALING_V2_CONFLUENCE_DEEPDIVE_2026-05-03.md"
)

BASELINE = base.BASELINE
SWING = base.SWING
FVG = base.FVG
OB = base.OB
COMPOSITE = base.COMPOSITE
VARIANTS = base.VARIANTS
EPS = 1e-9
CONCENTRATION_CAP = 0.45


def mean(values: Iterable[float]) -> float | None:
    vals = list(values)
    if not vals:
        return None
    return round(sum(vals) / len(vals), 6)


def sum_round(values: Iterable[float]) -> float:
    return round(sum(values), 6)


def as_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def parse_cohort(raw_cohort_key: str | None) -> dict[str, str | None]:
    parts = str(raw_cohort_key or "").split("|")
    return {
        "cohort_symbol": parts[0] if len(parts) > 0 and parts[0] else None,
        "cohort_session": parts[1] if len(parts) > 1 and parts[1] else None,
        "cohort_bias": parts[2] if len(parts) > 2 and parts[2] else None,
        "regime": parts[3] if len(parts) > 3 and parts[3] else None,
    }


def enrich_event(event: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(event)
    enriched.update(parse_cohort(event.get("raw_cohort_key")))
    dt = base.parse_utc(event.get("candle_close_utc"))
    if dt is not None:
        enriched["quarter"] = f"{dt.year}Q{((dt.month - 1) // 3) + 1}"
        enriched["month"] = dt.strftime("%Y-%m")
    else:
        enriched["quarter"] = None
        enriched["month"] = None
    enriched["improvement_bucket"] = improvement_bucket(enriched)
    enriched["fire_bucket"] = fire_bucket(enriched)
    enriched["sequence_bucket"] = sequence_bucket(enriched)
    return enriched


def load_events(event_log_path: str | Path, cost_key: str) -> list[dict[str, Any]]:
    by_event = base.load_event_rows(event_log_path)
    return [enrich_event(event) for event in base.build_event_profiles(by_event, cost_key=cost_key)]


def value(event: dict[str, Any], variant: str) -> float:
    return float(event["values"][variant])


def delta(event: dict[str, Any], variant: str, against: str = BASELINE) -> float:
    return value(event, variant) - value(event, against)


def improvement_bucket(event: dict[str, Any]) -> str:
    fvg_improves = delta(event, FVG) > EPS
    ob_improves = delta(event, OB) > EPS
    if fvg_improves and ob_improves:
        return "both_improve_vs_j46"
    if fvg_improves:
        return "fvg_only_improves_vs_j46"
    if ob_improves:
        return "ob_only_improves_vs_j46"
    return "neither_improves_vs_j46"


def fire_bucket(event: dict[str, Any]) -> str:
    fvg_fired = bool(event["fired"][FVG])
    ob_fired = bool(event["fired"][OB])
    if fvg_fired and ob_fired:
        return "both_fired"
    if fvg_fired:
        return "fvg_only_fired"
    if ob_fired:
        return "ob_only_fired"
    return "neither_fired"


def sequence_bucket(event: dict[str, Any]) -> str | None:
    fvg = event["first_locks"][FVG]
    ob = event["first_locks"][OB]
    if fvg is None or ob is None:
        return None
    fvg_time = str(fvg.get("confirmed_time") or "")
    ob_time = str(ob.get("confirmed_time") or "")
    if fvg_time < ob_time:
        return "fvg_then_ob"
    if ob_time < fvg_time:
        return "ob_then_fvg"
    return "same_time"


def variant_stats(events: list[dict[str, Any]], variants: Iterable[str] = VARIANTS) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for variant in variants:
        vals = [value(event, variant) for event in events]
        out[variant] = {
            "n": len(vals),
            "mean_r": mean(vals),
            "sum_r": sum_round(vals),
            "win_rate_gt_zero": round(sum(v > 0 for v in vals) / len(vals), 6) if vals else None,
        }
    return out


def slice_metrics(events: list[dict[str, Any]]) -> dict[str, Any]:
    fvg_deltas = [delta(event, FVG) for event in events]
    ob_deltas = [delta(event, OB) for event in events]
    comp_best = [float(event["composite_minus_best_single"]) for event in events]
    fvg_minus_ob = [float(event["fvg_minus_ob"]) for event in events]
    return {
        "n": len(events),
        "variant_stats": variant_stats(events),
        "mean_delta_vs_j46": {
            FVG: mean(fvg_deltas),
            OB: mean(ob_deltas),
            COMPOSITE: mean([delta(event, COMPOSITE) for event in events]),
        },
        "sum_delta_vs_j46": {
            FVG: sum_round(fvg_deltas),
            OB: sum_round(ob_deltas),
            COMPOSITE: sum_round(delta(event, COMPOSITE) for event in events),
        },
        "fvg_minus_ob_mean": mean(fvg_minus_ob),
        "fvg_minus_ob_sum": sum_round(fvg_minus_ob),
        "composite_minus_best_single_mean": mean(comp_best),
        "composite_minus_best_single_sum": sum_round(comp_best),
        "entry_consistency_violations": sum(
            not bool(event["same_entry_sl_tp_all_variants"]) for event in events
        ),
        "bucket_counts": dict(Counter(event["improvement_bucket"] for event in events)),
        "fire_counts": dict(Counter(event["fire_bucket"] for event in events)),
        "sequence_counts": dict(Counter(event["sequence_bucket"] for event in events if event["sequence_bucket"])),
    }


def group_by(events: Iterable[dict[str, Any]], dimensions: tuple[str, ...]) -> dict[tuple[Any, ...], list[dict[str, Any]]]:
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        groups[tuple(event.get(dim) for dim in dimensions)].append(event)
    return groups


def group_rows(
    events: list[dict[str, Any]],
    dimensions: tuple[str, ...],
    metric_fn: Callable[[dict[str, Any]], float],
    *,
    min_n: int = 1,
    limit: int = 20,
) -> list[dict[str, Any]]:
    rows = []
    for key, members in group_by(events, dimensions).items():
        if len(members) < min_n:
            continue
        metrics = [metric_fn(event) for event in members]
        row = {
            "dimensions": dict(zip(dimensions, key)),
            "n": len(members),
            "share_n": round(len(members) / len(events), 6) if events else None,
            "mean_metric": mean(metrics),
            "sum_metric": sum_round(metrics),
            "mean_fvg_minus_ob": mean(float(event["fvg_minus_ob"]) for event in members),
            "mean_fvg_delta_vs_j46": mean(delta(event, FVG) for event in members),
            "mean_ob_delta_vs_j46": mean(delta(event, OB) for event in members),
            "mean_composite_minus_best_single": mean(
                float(event["composite_minus_best_single"]) for event in members
            ),
        }
        rows.append(row)
    return sorted(rows, key=lambda row: (abs(float(row["sum_metric"])), row["n"]), reverse=True)[:limit]


def concentration(
    events: list[dict[str, Any]],
    metric_fn: Callable[[dict[str, Any]], float],
    dimensions: tuple[str, ...],
) -> dict[str, Any]:
    groups = group_by(events, dimensions)
    rows = []
    for key, members in groups.items():
        positive = [max(0.0, metric_fn(event)) for event in members]
        contribution = sum(positive)
        rows.append(
            {
                "dimensions": dict(zip(dimensions, key)),
                "n": len(members),
                "positive_contribution": round(contribution, 6),
            }
        )
    total = sum(row["positive_contribution"] for row in rows)
    rows.sort(key=lambda row: row["positive_contribution"], reverse=True)
    for row in rows:
        row["positive_contribution_share"] = round(row["positive_contribution"] / total, 6) if total > 0 else None
    top = rows[0] if rows else None
    top_share = top.get("positive_contribution_share") if top else None
    return {
        "dimensions": list(dimensions),
        "total_positive_contribution": round(total, 6),
        "top_share": top_share,
        "cap": CONCENTRATION_CAP,
        "cap_exceeded": bool(top_share is not None and top_share > CONCENTRATION_CAP),
        "top_groups": rows[:10],
    }


def concentration_panel(events: list[dict[str, Any]], metric_fn: Callable[[dict[str, Any]], float]) -> list[dict[str, Any]]:
    dimensions = [
        ("symbol",),
        ("session",),
        ("side",),
        ("regime",),
        ("year",),
        ("quarter",),
        ("symbol", "session", "side"),
        ("raw_cohort_key",),
    ]
    return [concentration(events, metric_fn, dims) for dims in dimensions]


def leave_one_stress(events: list[dict[str, Any]], dimensions: tuple[str, ...]) -> dict[str, list[dict[str, Any]]]:
    full = slice_metrics(events)
    out: dict[str, list[dict[str, Any]]] = {}
    for dimension in dimensions:
        values = sorted({event.get(dimension) for event in events}, key=lambda item: str(item))
        rows = []
        for dim_value in values:
            kept = [event for event in events if event.get(dimension) != dim_value]
            metrics = slice_metrics(kept)
            rows.append(
                {
                    "excluded_dimension": dimension,
                    "excluded_value": dim_value,
                    "excluded_n": len(events) - len(kept),
                    "kept_n": len(kept),
                    "fvg_delta_mean": metrics["mean_delta_vs_j46"][FVG],
                    "ob_delta_mean": metrics["mean_delta_vs_j46"][OB],
                    "fvg_minus_ob_mean": metrics["fvg_minus_ob_mean"],
                    "composite_minus_best_single_mean": metrics["composite_minus_best_single_mean"],
                    "fvg_delta_sign_flips": sign_flip(full["mean_delta_vs_j46"][FVG], metrics["mean_delta_vs_j46"][FVG]),
                    "ob_delta_sign_flips": sign_flip(full["mean_delta_vs_j46"][OB], metrics["mean_delta_vs_j46"][OB]),
                    "fvg_minus_ob_sign_flips": sign_flip(full["fvg_minus_ob_mean"], metrics["fvg_minus_ob_mean"]),
                }
            )
        out[dimension] = rows
    return out


def sign_flip(before: float | None, after: float | None) -> bool:
    if before is None or after is None:
        return False
    return (before > 0 and after < 0) or (before < 0 and after > 0)


def first_lock_delta(event: dict[str, Any]) -> dict[str, float | None]:
    fvg = event["first_locks"][FVG] or {}
    ob = event["first_locks"][OB] or {}
    fvg_floor = as_float(fvg.get("floor_r"))
    ob_floor = as_float(ob.get("floor_r"))
    fvg_index = as_float(fvg.get("confirmed_index"))
    ob_index = as_float(ob.get("confirmed_index"))
    return {
        "ob_floor_minus_fvg_floor_r": round(ob_floor - fvg_floor, 6) if fvg_floor is not None and ob_floor is not None else None,
        "ob_confirmed_index_minus_fvg_index": round(ob_index - fvg_index, 6) if fvg_index is not None and ob_index is not None else None,
    }


def sequence_stats(events: list[dict[str, Any]]) -> dict[str, Any]:
    both = [event for event in events if event["sequence_bucket"] is not None]
    rows = []
    for bucket, members in sorted(group_by(both, ("sequence_bucket",)).items()):
        seq_events = members
        deltas = [first_lock_delta(event) for event in seq_events]
        rows.append(
            {
                "sequence": bucket[0],
                "n": len(seq_events),
                "share_of_both_fired": round(len(seq_events) / len(both), 6) if both else None,
                "fvg_mean_r": mean(value(event, FVG) for event in seq_events),
                "ob_mean_r": mean(value(event, OB) for event in seq_events),
                "ob_minus_fvg_mean_r": mean(delta(event, OB, FVG) for event in seq_events),
                "ob_better_share": round(sum(delta(event, OB, FVG) > EPS for event in seq_events) / len(seq_events), 6)
                if seq_events
                else None,
                "mean_ob_floor_minus_fvg_floor_r": mean(
                    item["ob_floor_minus_fvg_floor_r"] for item in deltas if item["ob_floor_minus_fvg_floor_r"] is not None
                ),
                "mean_ob_confirmed_index_minus_fvg_index": mean(
                    item["ob_confirmed_index_minus_fvg_index"]
                    for item in deltas
                    if item["ob_confirmed_index_minus_fvg_index"] is not None
                ),
            }
        )
    return {
        "both_fvg_and_ob_fire_n": len(both),
        "rows": rows,
        "fvg_then_ob_concentration": concentration_panel(
            [event for event in both if event["sequence_bucket"] == "fvg_then_ob"],
            lambda event: max(0.0, delta(event, OB, FVG)),
        ),
    }


def case_row(event: dict[str, Any]) -> dict[str, Any]:
    lock_deltas = first_lock_delta(event)
    return {
        "event_key": event["event_key"],
        "candle_close_utc": event["candle_close_utc"],
        "symbol": event["symbol"],
        "session": event["session"],
        "side": event["side"],
        "regime": event.get("regime"),
        "role": event.get("role"),
        "selected_timeframe": event.get("selected_timeframe"),
        "j46_r": value(event, BASELINE),
        "fvg_r": value(event, FVG),
        "ob_r": value(event, OB),
        "swing_r": value(event, SWING),
        "composite_r": value(event, COMPOSITE),
        "fvg_delta_vs_j46": round(delta(event, FVG), 6),
        "ob_delta_vs_j46": round(delta(event, OB), 6),
        "fvg_minus_ob": event["fvg_minus_ob"],
        "composite_minus_best_single": event["composite_minus_best_single"],
        "improvement_bucket": event["improvement_bucket"],
        "fire_bucket": event["fire_bucket"],
        "sequence_bucket": event["sequence_bucket"],
        "fvg_first_lock": event["first_locks"][FVG],
        "ob_first_lock": event["first_locks"][OB],
        "coherence_flags": {
            "fvg_then_ob": event["sequence_bucket"] == "fvg_then_ob",
            "ob_confirmed_after_fvg": (
                lock_deltas["ob_confirmed_index_minus_fvg_index"] is not None
                and lock_deltas["ob_confirmed_index_minus_fvg_index"] > 0
            ),
            "ob_floor_above_fvg_floor": (
                lock_deltas["ob_floor_minus_fvg_floor_r"] is not None
                and lock_deltas["ob_floor_minus_fvg_floor_r"] > 0
            ),
            "both_structural_variants_locked": event["fired"][FVG] and event["fired"][OB],
        },
    }


def top_cases(
    events: list[dict[str, Any]],
    key_fn: Callable[[dict[str, Any]], float],
    *,
    limit: int = 12,
    reverse: bool = True,
) -> list[dict[str, Any]]:
    return [case_row(event) for event in sorted(events, key=key_fn, reverse=reverse)[:limit]]


def build_casebooks(events: list[dict[str, Any]]) -> dict[str, Any]:
    fvg_only = [event for event in events if event["improvement_bucket"] == "fvg_only_improves_vs_j46"]
    ob_only = [event for event in events if event["improvement_bucket"] == "ob_only_improves_vs_j46"]
    fvg_then_ob = [
        event
        for event in events
        if event["sequence_bucket"] == "fvg_then_ob" and delta(event, OB, FVG) > EPS
    ]
    composite_above = [
        event for event in events if float(event["composite_minus_best_single"]) > EPS
    ]
    return {
        "fvg_only_rescue_examples": top_cases(
            fvg_only, lambda event: value(event, FVG) - max(value(event, BASELINE), value(event, OB))
        ),
        "ob_only_tail_examples": top_cases(
            ob_only, lambda event: value(event, OB) - max(value(event, BASELINE), value(event, FVG))
        ),
        "ob_after_fvg_tail_preservation_examples": top_cases(
            fvg_then_ob, lambda event: delta(event, OB, FVG)
        ),
        "composite_arbitration_positive_examples": top_cases(
            composite_above, lambda event: float(event["composite_minus_best_single"])
        ),
    }


def composite_arbitration(events: list[dict[str, Any]]) -> dict[str, Any]:
    positive = [event for event in events if float(event["composite_minus_best_single"]) > EPS]
    negative = [event for event in events if float(event["composite_minus_best_single"]) < -EPS]
    return {
        "global": {
            "positive_n": len(positive),
            "negative_n": len(negative),
            "match_n": len(events) - len(positive) - len(negative),
            "positive_share": round(len(positive) / len(events), 6) if events else None,
            "negative_share": round(len(negative) / len(events), 6) if events else None,
            "mean_composite_minus_best_single": mean(
                float(event["composite_minus_best_single"]) for event in events
            ),
        },
        "positive_conditions_min_n_10": group_rows(
            positive,
            ("symbol", "session", "side", "regime"),
            lambda event: float(event["composite_minus_best_single"]),
            min_n=10,
            limit=20,
        ),
        "positive_concentration": concentration_panel(
            positive,
            lambda event: float(event["composite_minus_best_single"]),
        ),
    }


def bucket_deep_dive(events: list[dict[str, Any]], bucket: str, metric_fn: Callable[[dict[str, Any]], float]) -> dict[str, Any]:
    members = [event for event in events if event["improvement_bucket"] == bucket]
    return {
        "bucket": bucket,
        "metrics": slice_metrics(members),
        "top_groups_symbol_session_side_regime": group_rows(
            members,
            ("symbol", "session", "side", "regime"),
            metric_fn,
            min_n=5,
            limit=20,
        ),
        "concentration": concentration_panel(members, metric_fn),
    }


def build_payload(event_log_path: str | Path = DEFAULT_EVENT_LOG, cost_key: str = "0.05") -> dict[str, Any]:
    events = load_events(event_log_path, cost_key)
    year_2026 = [event for event in events if event.get("year") == 2026]
    return {
        "schema_version": "raw_ohlc_path_scaling_v2_confluence_deepdive_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "discovery_label": "DISCOVERY_ONLY_NOT_REGISTERED",
        "inputs": {
            "event_log_path": str(event_log_path),
            "cost_key": cost_key,
            "concentration_cap": CONCENTRATION_CAP,
            "baseline_variant": BASELINE,
            "compared_variants": list(VARIANTS),
        },
        "registered_question_before_outputs": (
            "Are V2 FVG/OB/Swing/Composite agreement and disagreement pockets "
            "structurally coherent enough to generate forward-test hypotheses, "
            "or are the same-dataset lifts concentrated artifacts?"
        ),
        "slices": {
            "full_resolved": slice_metrics(events),
            "year_2026": slice_metrics(year_2026),
        },
        "leave_one_stress": {
            "full_resolved": leave_one_stress(events, ("symbol", "session", "side", "year")),
            "year_2026": leave_one_stress(year_2026, ("symbol", "session", "side")),
        },
        "bucket_deep_dives": {
            "fvg_only_improves_vs_j46": bucket_deep_dive(
                events,
                "fvg_only_improves_vs_j46",
                lambda event: value(event, FVG) - max(value(event, BASELINE), value(event, OB)),
            ),
            "ob_only_improves_vs_j46": bucket_deep_dive(
                events,
                "ob_only_improves_vs_j46",
                lambda event: value(event, OB) - max(value(event, BASELINE), value(event, FVG)),
            ),
            "both_improve_vs_j46": bucket_deep_dive(
                events,
                "both_improve_vs_j46",
                lambda event: max(delta(event, FVG), delta(event, OB)),
            ),
        },
        "ob_after_fvg_tail_preservation": {
            "full_resolved": sequence_stats(events),
            "year_2026": sequence_stats(year_2026),
        },
        "composite_arbitration": {
            "full_resolved": composite_arbitration(events),
            "year_2026": composite_arbitration(year_2026),
        },
        "casebooks": {
            "full_resolved": build_casebooks(events),
            "year_2026": build_casebooks(year_2026),
        },
        "market_structure_coherence_definition": {
            "status": "LOG_METADATA_ONLY_NOT_CHART_REVIEW",
            "coherent_ob_after_fvg_flags": [
                "both FVG and OB structural variants fired",
                "FVG first lock confirmed before OB first lock",
                "OB first lock confirmed on a later selected-timeframe index",
                "OB lock floor is above the FVG lock floor for LONG-side R accounting, or otherwise preserves more realized R",
                "OB net R exceeds FVG net R on the same event key",
            ],
            "non_claim": (
                "These flags show structure-sequence coherence in the replay log. They are not "
                "manual chart validation and do not prove a forward edge."
            ),
        },
        "missing_fields": [
            {
                "field": "pre_fill_delivery_path_rows",
                "impact": "Cannot test delivery-leg plus reversal-leg structure from current post-fill event log.",
            },
            {
                "field": "pending_limit_lifecycle_state",
                "impact": "Cannot distinguish broker fill/expiry/cancel/no-trigger states for pre-fill hypotheses.",
            },
            {
                "field": "data_source",
                "impact": "Event rows do not expose an immutable data-source label beyond event-log path and cohort metadata.",
            },
        ],
        "forward_only_fields_for_v2b": [
            "event_key",
            "symbol",
            "session",
            "side",
            "raw_cohort_key",
            "regime",
            "setup_decision_close_utc",
            "pending_limit_created_utc",
            "original_poi_type_and_bounds",
            "fill_or_expiry_state",
            "selected_path_timeframe",
            "lower_tf_available",
            "fvg_fired",
            "ob_fired",
            "swing_fired",
            "composite_fired",
            "fvg_first_lock_time_and_floor_r",
            "ob_first_lock_time_and_floor_r",
            "sequence_bucket",
            "j46_net_r_by_cost",
            "fvg_net_r_by_cost",
            "ob_net_r_by_cost",
            "swing_net_r_by_cost",
            "composite_net_r_by_cost",
            "same_bar_ambiguity_state",
            "actual_broker_r_if_available",
            "synthetic_path_r_if_available",
            "fill_no_fill_label",
            "cost_model_version",
        ],
        "synthesis": synthesize(events, year_2026),
    }


def synthesize(events: list[dict[str, Any]], year_2026: list[dict[str, Any]]) -> dict[str, Any]:
    full = slice_metrics(events)
    y26 = slice_metrics(year_2026)
    fvg_bucket = [event for event in events if event["improvement_bucket"] == "fvg_only_improves_vs_j46"]
    ob_bucket = [event for event in events if event["improvement_bucket"] == "ob_only_improves_vs_j46"]
    return {
        "plain_language_bottom_line": (
            "FVG-only rows are a real discovery pocket but are much larger than OB-only rows "
            "and must be treated as concentration-sensitive. OB-after-FVG behavior is the "
            "cleanest structural pattern: when both fire, FVG usually appears first and OB "
            "often preserves more right tail. Composite is not globally useful, but its "
            "positive rows are worth studying as arbitration examples rather than as a blind "
            "highest-floor rule."
        ),
        "answers": {
            "fvg_only_concentration": (
                f"Full FVG-only improves bucket n={len(fvg_bucket)}; 2026 FVG-only improves "
                f"bucket n={y26['bucket_counts'].get('fvg_only_improves_vs_j46', 0)}. "
                "Use the JSON concentration panels for symbol/session/side/regime/year caps."
            ),
            "ob_after_fvg_tail_preservation": (
                "The both-fired sequence table is the strongest support for the tail-preservation "
                "hypothesis; same-dataset only, not registered validation."
            ),
            "composite_arbitration": (
                f"Composite minus best single is globally negative in full data "
                f"({full['composite_minus_best_single_mean']}) and 2026 ({y26['composite_minus_best_single_mean']}), "
                "so Composite remains an overlock warning. Positive composite rows are arbitration case studies only."
            ),
            "ob_only": (
                f"OB-only improves bucket is small in full data (n={len(ob_bucket)}) and very small in 2026 "
                f"(n={y26['bucket_counts'].get('ob_only_improves_vs_j46', 0)}), so OB-only claims have high small-sample risk."
            ),
        },
        "opened_hypotheses": [
            {
                "id": "V2DD-H1-FVG-ONLY-RESCUE-POCKET",
                "status": "DISCOVERY_ONLY_NOT_REGISTERED",
                "mechanism": "FVG floors may rescue post-entry failures when no qualifying OB floor forms.",
                "risk": "May be concentrated in a few symbol/session/regime/year pockets.",
            },
            {
                "id": "V2DD-H2-FVG-THEN-OB-TAIL-PRESERVATION",
                "status": "DISCOVERY_ONLY_NOT_REGISTERED",
                "mechanism": "FVG appears first as delivery continuation, then OB acts as later protective floor.",
                "risk": "Current event log is post-fill only and cannot prove pre-fill delivery-leg structure.",
            },
            {
                "id": "V2DD-H3-COMPOSITE-ARBITRATION-NOT-BLIND-COMPOSITE",
                "status": "DISCOVERY_ONLY_NOT_REGISTERED",
                "mechanism": "Composite may help only under arbitration conditions where it avoids both single-selector failure modes.",
                "risk": "Global mean is negative and same-dataset positive cases may be selected artifacts.",
            },
        ],
        "next_steps": [
            "Build a forward-only confluence ledger once V2b has resolved post-cutoff pairs.",
            "Use pre-fill delivery-path capture before scoring the two-leg delivery/reversal hypothesis.",
            "Do not promote FVG-only, OB-after-FVG, or Composite arbitration without pre-registered unseen validation.",
        ],
    }


def write_json(payload: dict[str, Any], path: str | Path) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value).replace("|", r"\|")


def table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(fmt(value) for value in row) + " |")
    return lines


def leave_one_rows(stress: dict[str, list[dict[str, Any]]]) -> list[list[Any]]:
    rows = []
    for dimension, items in stress.items():
        for item in items:
            rows.append(
                [
                    dimension,
                    item["excluded_value"],
                    item["excluded_n"],
                    item["kept_n"],
                    item["fvg_delta_mean"],
                    item["ob_delta_mean"],
                    item["fvg_minus_ob_mean"],
                    item["fvg_delta_sign_flips"],
                    item["ob_delta_sign_flips"],
                    item["fvg_minus_ob_sign_flips"],
                ]
            )
    return rows


def concentration_rows(panel: list[dict[str, Any]]) -> list[list[Any]]:
    rows = []
    for item in panel:
        top = item["top_groups"][0] if item["top_groups"] else {}
        rows.append(
            [
                "+".join(item["dimensions"]),
                item["total_positive_contribution"],
                item["top_share"],
                item["cap"],
                item["cap_exceeded"],
                top.get("dimensions"),
                top.get("n"),
                top.get("positive_contribution"),
            ]
        )
    return rows


def case_rows(cases: list[dict[str, Any]], limit: int = 8) -> list[list[Any]]:
    return [
        [
            case["event_key"],
            case["symbol"],
            case["session"],
            case["side"],
            case["regime"],
            case["j46_r"],
            case["fvg_r"],
            case["ob_r"],
            case["composite_r"],
            case["fvg_minus_ob"],
            case["fire_bucket"],
            case["sequence_bucket"],
        ]
        for case in cases[:limit]
    ]


def write_markdown(payload: dict[str, Any], path: str | Path) -> None:
    out = Path(path)
    full = payload["slices"]["full_resolved"]
    y26 = payload["slices"]["year_2026"]
    fvg_bucket = payload["bucket_deep_dives"]["fvg_only_improves_vs_j46"]
    ob_bucket = payload["bucket_deep_dives"]["ob_only_improves_vs_j46"]
    seq_full = payload["ob_after_fvg_tail_preservation"]["full_resolved"]
    seq_2026 = payload["ob_after_fvg_tail_preservation"]["year_2026"]
    comp_full = payload["composite_arbitration"]["full_resolved"]
    comp_2026 = payload["composite_arbitration"]["year_2026"]
    cases_2026 = payload["casebooks"]["year_2026"]

    lines = [
        "# Raw OHLC Path Scaling V2 Confluence Deep Dive",
        "",
        "Date: 2026-05-03",
        "Scope: research/tooling only",
        f"Promotion verdict: `{payload['promotion_verdict']}`",
        f"Discovery label: `{payload['discovery_label']}`",
        "",
        "## Registered Question Before Outputs",
        "",
        payload["registered_question_before_outputs"],
        "",
        "## Bottom Line",
        "",
        payload["synthesis"]["plain_language_bottom_line"],
        "",
        "No result in this report is a promotion, replay registration, or live-logic recommendation.",
        "",
        "## Slice Summary",
        "",
        *table(
            [
                "slice",
                "n",
                "FVG mean delta vs J46",
                "OB mean delta vs J46",
                "Composite mean delta vs J46",
                "FVG-OB mean",
                "Composite-best mean",
                "entry violations",
            ],
            [
                [
                    "full_resolved",
                    full["n"],
                    full["mean_delta_vs_j46"][FVG],
                    full["mean_delta_vs_j46"][OB],
                    full["mean_delta_vs_j46"][COMPOSITE],
                    full["fvg_minus_ob_mean"],
                    full["composite_minus_best_single_mean"],
                    full["entry_consistency_violations"],
                ],
                [
                    "year_2026",
                    y26["n"],
                    y26["mean_delta_vs_j46"][FVG],
                    y26["mean_delta_vs_j46"][OB],
                    y26["mean_delta_vs_j46"][COMPOSITE],
                    y26["fvg_minus_ob_mean"],
                    y26["composite_minus_best_single_mean"],
                    y26["entry_consistency_violations"],
                ],
            ],
        ),
        "",
        "## Direct Answers",
        "",
        f"- FVG-only rescue pockets: {payload['synthesis']['answers']['fvg_only_concentration']}",
        f"- OB-after-FVG tail preservation: {payload['synthesis']['answers']['ob_after_fvg_tail_preservation']}",
        f"- Composite: {payload['synthesis']['answers']['composite_arbitration']}",
        f"- OB-only: {payload['synthesis']['answers']['ob_only']}",
        "",
        "## Leave-One Stress",
        "",
        "Full resolved stress:",
        "",
        *table(
            [
                "dimension",
                "excluded",
                "excluded n",
                "kept n",
                "FVG delta mean",
                "OB delta mean",
                "FVG-OB mean",
                "FVG sign flip",
                "OB sign flip",
                "FVG-OB sign flip",
            ],
            leave_one_rows(payload["leave_one_stress"]["full_resolved"]),
        ),
        "",
        "2026-only stress:",
        "",
        *table(
            [
                "dimension",
                "excluded",
                "excluded n",
                "kept n",
                "FVG delta mean",
                "OB delta mean",
                "FVG-OB mean",
                "FVG sign flip",
                "OB sign flip",
                "FVG-OB sign flip",
            ],
            leave_one_rows(payload["leave_one_stress"]["year_2026"]),
        ),
        "",
        "## FVG-Only Rescue Pocket",
        "",
        f"Full bucket n: `{fvg_bucket['metrics']['n']}`. This is discovery-only and concentration-sensitive.",
        "",
        *table(
            ["dimension", "positive contribution", "top share", "cap", "cap exceeded", "top group", "top n", "top contribution"],
            concentration_rows(fvg_bucket["concentration"]),
        ),
        "",
        "Top full-data FVG-only groups by FVG advantage over J46/OB:",
        "",
        *table(
            ["group", "n", "share n", "mean metric", "sum metric", "mean FVG delta", "mean OB delta"],
            [
                [
                    row["dimensions"],
                    row["n"],
                    row["share_n"],
                    row["mean_metric"],
                    row["sum_metric"],
                    row["mean_fvg_delta_vs_j46"],
                    row["mean_ob_delta_vs_j46"],
                ]
                for row in fvg_bucket["top_groups_symbol_session_side_regime"][:12]
            ],
        ),
        "",
        "## OB-Only Pocket",
        "",
        f"Full bucket n: `{ob_bucket['metrics']['n']}`. The 2026 OB-only bucket is especially small, so this is not a robust standalone branch.",
        "",
        *table(
            ["dimension", "positive contribution", "top share", "cap", "cap exceeded", "top group", "top n", "top contribution"],
            concentration_rows(ob_bucket["concentration"]),
        ),
        "",
        "## OB-After-FVG Tail Preservation",
        "",
        "Sequence stats:",
        "",
        *table(
            [
                "slice",
                "sequence",
                "n",
                "share",
                "FVG mean",
                "OB mean",
                "OB-FVG mean",
                "OB better share",
                "OB floor-FVG floor",
                "OB index-FVG index",
            ],
            [
                [
                    "full_resolved",
                    row["sequence"],
                    row["n"],
                    row["share_of_both_fired"],
                    row["fvg_mean_r"],
                    row["ob_mean_r"],
                    row["ob_minus_fvg_mean_r"],
                    row["ob_better_share"],
                    row["mean_ob_floor_minus_fvg_floor_r"],
                    row["mean_ob_confirmed_index_minus_fvg_index"],
                ]
                for row in seq_full["rows"]
            ]
            + [
                [
                    "year_2026",
                    row["sequence"],
                    row["n"],
                    row["share_of_both_fired"],
                    row["fvg_mean_r"],
                    row["ob_mean_r"],
                    row["ob_minus_fvg_mean_r"],
                    row["ob_better_share"],
                    row["mean_ob_floor_minus_fvg_floor_r"],
                    row["mean_ob_confirmed_index_minus_fvg_index"],
                ]
                for row in seq_2026["rows"]
            ],
        ),
        "",
        "FVG-then-OB positive-contribution concentration:",
        "",
        *table(
            ["dimension", "positive contribution", "top share", "cap", "cap exceeded", "top group", "top n", "top contribution"],
            concentration_rows(seq_full["fvg_then_ob_concentration"]),
        ),
        "",
        "## Composite Arbitration",
        "",
        *table(
            ["slice", "positive n", "negative n", "match n", "positive share", "negative share", "mean comp-best"],
            [
                [
                    "full_resolved",
                    comp_full["global"]["positive_n"],
                    comp_full["global"]["negative_n"],
                    comp_full["global"]["match_n"],
                    comp_full["global"]["positive_share"],
                    comp_full["global"]["negative_share"],
                    comp_full["global"]["mean_composite_minus_best_single"],
                ],
                [
                    "year_2026",
                    comp_2026["global"]["positive_n"],
                    comp_2026["global"]["negative_n"],
                    comp_2026["global"]["match_n"],
                    comp_2026["global"]["positive_share"],
                    comp_2026["global"]["negative_share"],
                    comp_2026["global"]["mean_composite_minus_best_single"],
                ],
            ],
        ),
        "",
        "Composite-positive full-data conditions with n>=10:",
        "",
        *table(
            ["group", "n", "share n", "mean comp-best", "sum comp-best", "mean FVG-OB"],
            [
                [
                    row["dimensions"],
                    row["n"],
                    row["share_n"],
                    row["mean_metric"],
                    row["sum_metric"],
                    row["mean_fvg_minus_ob"],
                ]
                for row in comp_full["positive_conditions_min_n_10"][:12]
            ],
        ),
        "",
        "## Representative 2026 Casebook",
        "",
        "## Market-Structure Coherence Basis",
        "",
        f"Status: `{payload['market_structure_coherence_definition']['status']}`",
        "",
        payload["market_structure_coherence_definition"]["non_claim"],
        "",
        "For OB-after-FVG examples, the coherent replay-log pattern requires:",
        "",
        *[f"- {item}" for item in payload["market_structure_coherence_definition"]["coherent_ob_after_fvg_flags"]],
        "",
        "FVG-only examples:",
        "",
        *table(
            ["event", "symbol", "session", "side", "regime", "J46", "FVG", "OB", "Composite", "FVG-OB", "fire bucket", "sequence"],
            case_rows(cases_2026["fvg_only_rescue_examples"]),
        ),
        "",
        "OB-only examples:",
        "",
        *table(
            ["event", "symbol", "session", "side", "regime", "J46", "FVG", "OB", "Composite", "FVG-OB", "fire bucket", "sequence"],
            case_rows(cases_2026["ob_only_tail_examples"]),
        ),
        "",
        "OB-after-FVG tail-preservation examples:",
        "",
        *table(
            ["event", "symbol", "session", "side", "regime", "J46", "FVG", "OB", "Composite", "FVG-OB", "fire bucket", "sequence"],
            case_rows(cases_2026["ob_after_fvg_tail_preservation_examples"]),
        ),
        "",
        "Composite-positive examples:",
        "",
        *table(
            ["event", "symbol", "session", "side", "regime", "J46", "FVG", "OB", "Composite", "FVG-OB", "fire bucket", "sequence"],
            case_rows(cases_2026["composite_arbitration_positive_examples"]),
        ),
        "",
        "## Missing Fields And Blockers",
        "",
        *[f"- `{item['field']}`: {item['impact']}" for item in payload["missing_fields"]],
        "",
        "## Forward-Only Fields V2b Should Collect",
        "",
        *[f"- `{item}`" for item in payload["forward_only_fields_for_v2b"]],
        "",
        "## Opened Hypotheses",
        "",
        *[
            f"- `{item['id']}` ({item['status']}): {item['mechanism']} Risk: {item['risk']}"
            for item in payload["synthesis"]["opened_hypotheses"]
        ],
        "",
        "## Next Steps",
        "",
        *[f"{idx}. {item}" for idx, item in enumerate(payload["synthesis"]["next_steps"], start=1)],
        "",
    ]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event-log", default=DEFAULT_EVENT_LOG)
    parser.add_argument("--cost-key", default="0.05")
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = build_payload(event_log_path=args.event_log, cost_key=args.cost_key)
    write_json(payload, args.output_json)
    write_markdown(payload, args.output_md)
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")
    print(
        f"full_n={payload['slices']['full_resolved']['n']} "
        f"y2026_n={payload['slices']['year_2026']['n']} "
        f"promotion={payload['promotion_verdict']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
