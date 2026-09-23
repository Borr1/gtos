#!/usr/bin/env python3
"""Audit V2 structural-selector confluence and disagreement.

Research/tooling only. This script compares V2 structural policies on the same
event keys, so it answers whether selectors agree, disagree, or over-tighten on
the same setup. It does not treat selector variants as independent trade
streams and it does not promote live logic.
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


DEFAULT_EVENT_LOG = (
    "data/external/validation/calendar_macro_bundle_v1/historical_opportunities/"
    "raw_ohlc_prequential_replay/path_scaling_v2_structural_levels/"
    "raw_ohlc_path_scaling_v2_structural_levels_events_20260501T213225Z.jsonl"
)
DEFAULT_OUTPUT_JSON = (
    "research/phase_3_external_feed_validation/"
    "RAW_OHLC_PATH_SCALING_V2_STRUCTURE_CONFLUENCE_AUDIT_2026-05-02.json"
)
DEFAULT_OUTPUT_MD = (
    "research/phase_3_external_feed_validation/"
    "RAW_OHLC_PATH_SCALING_V2_STRUCTURE_CONFLUENCE_AUDIT_2026-05-02.md"
)

BASELINE = "J46_J49_ONLY"
SWING = "STRUCT_SWING_PROTECTED_V2"
FVG = "STRUCT_FVG_MID_EDGE_V2"
OB = "STRUCT_OB_BOUNDARY_V2"
COMPOSITE = "STRUCT_COMPOSITE_ANY_V2"
VARIANTS = (BASELINE, SWING, FVG, OB, COMPOSITE)
STRUCTURAL_SINGLE_VARIANTS = (SWING, FVG, OB)
EPS = 1e-9


def parse_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def load_event_rows(path: Path | str, variants: Iterable[str] = VARIANTS) -> dict[str, dict[str, dict[str, Any]]]:
    wanted = set(variants)
    by_event: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            variant = row.get("variant_id")
            if variant in wanted:
                by_event[str(row["event_key"])][str(variant)] = row
    return by_event


def net_r(row: dict[str, Any], *, cost_key: str) -> float | None:
    value = (row.get("net_r_by_cost") or {}).get(cost_key)
    if value is None:
        return None
    return float(value)


def first_lock(row: dict[str, Any]) -> dict[str, Any] | None:
    locks = row.get("locks_triggered") or []
    if not locks:
        return None
    return sorted(
        locks,
        key=lambda item: (
            item.get("confirmed_time") or "",
            item.get("source_time") or "",
            float(item.get("floor_r") or -999.0),
        ),
    )[0]


def lock_summary(lock: dict[str, Any] | None) -> dict[str, Any] | None:
    if lock is None:
        return None
    return {
        "selector_id": lock.get("selector_id"),
        "event_type": lock.get("event_type"),
        "confirmed_time": lock.get("confirmed_time"),
        "source_time": lock.get("source_time"),
        "confirmed_index": lock.get("confirmed_index"),
        "floor_r": lock.get("floor_r"),
        "price": lock.get("price"),
    }


def _entry_tuple(row: dict[str, Any]) -> tuple[Any, Any, Any, Any]:
    return (
        row.get("mechanical_side"),
        row.get("mechanical_entry"),
        row.get("mechanical_sl"),
        row.get("mechanical_tp"),
    )


def event_profile(event_key: str, rows: dict[str, dict[str, Any]], *, cost_key: str) -> dict[str, Any] | None:
    if not all(variant in rows for variant in VARIANTS):
        return None
    values = {variant: net_r(rows[variant], cost_key=cost_key) for variant in VARIANTS}
    if any(value is None for value in values.values()):
        return None

    base = rows[BASELINE]
    event_time = parse_utc(base.get("candle_close_utc"))
    entries = {variant: _entry_tuple(rows[variant]) for variant in VARIANTS}
    first_locks = {variant: first_lock(rows[variant]) for variant in VARIANTS}
    best_single_variant = max(STRUCTURAL_SINGLE_VARIANTS, key=lambda variant: float(values[variant]))
    best_single_value = float(values[best_single_variant])

    return {
        "event_key": event_key,
        "candle_close_utc": base.get("candle_close_utc"),
        "year": event_time.year if event_time else None,
        "symbol": base.get("symbol"),
        "session": base.get("session"),
        "side": base.get("mechanical_side"),
        "role": base.get("role"),
        "selected_timeframe": base.get("selected_timeframe"),
        "raw_cohort_key": base.get("raw_cohort_key"),
        "values": {variant: float(value) for variant, value in values.items()},
        "delta_vs_j46": {
            variant: round(float(values[variant]) - float(values[BASELINE]), 6)
            for variant in (SWING, FVG, OB, COMPOSITE)
        },
        "fvg_minus_ob": round(float(values[FVG]) - float(values[OB]), 6),
        "best_single_variant": best_single_variant,
        "best_single_value": best_single_value,
        "composite_minus_best_single": round(float(values[COMPOSITE]) - best_single_value, 6),
        "same_entry_sl_tp_all_variants": len(set(entries.values())) == 1,
        "fired": {
            variant: bool(rows[variant].get("locks_triggered"))
            for variant in (SWING, FVG, OB, COMPOSITE)
        },
        "outcomes": {
            variant: rows[variant].get("outcome")
            for variant in VARIANTS
        },
        "first_locks": {
            variant: lock_summary(first_locks[variant])
            for variant in (SWING, FVG, OB, COMPOSITE)
        },
        "mfe_r": base.get("mfe_r"),
        "mae_r": base.get("mae_r"),
    }


def build_event_profiles(by_event: dict[str, dict[str, dict[str, Any]]], *, cost_key: str) -> list[dict[str, Any]]:
    profiles = []
    for event_key, rows in by_event.items():
        profile = event_profile(event_key, rows, cost_key=cost_key)
        if profile is not None:
            profiles.append(profile)
    return profiles


def mean(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 6)


def _variant_stats(events: list[dict[str, Any]], variants: Iterable[str]) -> dict[str, Any]:
    out = {}
    for variant in variants:
        values = [float(event["values"][variant]) for event in events]
        out[variant] = {
            "mean_r": mean(values),
            "sum_r": round(sum(values), 6),
            "win_rate_gt_zero": round(sum(value > 0 for value in values) / len(values), 6) if values else None,
        }
    return out


def _improvement_bucket(event: dict[str, Any]) -> str:
    fvg_improves = float(event["values"][FVG]) > float(event["values"][BASELINE]) + EPS
    ob_improves = float(event["values"][OB]) > float(event["values"][BASELINE]) + EPS
    if fvg_improves and ob_improves:
        return "both_improve_vs_j46"
    if fvg_improves:
        return "fvg_only_improves_vs_j46"
    if ob_improves:
        return "ob_only_improves_vs_j46"
    return "neither_improves_vs_j46"


def _absolute_bucket(event: dict[str, Any]) -> str:
    fvg_positive = float(event["values"][FVG]) > 0
    ob_positive = float(event["values"][OB]) > 0
    if fvg_positive and ob_positive:
        return "both_positive"
    if fvg_positive:
        return "fvg_positive_ob_nonpositive"
    if ob_positive:
        return "ob_positive_fvg_nonpositive"
    return "both_nonpositive"


def _fire_bucket(event: dict[str, Any]) -> str:
    fvg_fired = bool(event["fired"][FVG])
    ob_fired = bool(event["fired"][OB])
    if fvg_fired and ob_fired:
        return "both_fired"
    if fvg_fired:
        return "fvg_only_fired"
    if ob_fired:
        return "ob_only_fired"
    return "neither_fired"


def _sequence_bucket(event: dict[str, Any]) -> str | None:
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


def _composite_bucket(event: dict[str, Any]) -> str:
    diff = float(event["composite_minus_best_single"])
    if diff < -EPS:
        return "composite_below_best_single"
    if diff > EPS:
        return "composite_above_best_single"
    return "composite_matches_best_single"


def bucket_summary(
    events: list[dict[str, Any]],
    classifier: Callable[[dict[str, Any]], str | None],
    *,
    variants: Iterable[str] = (BASELINE, FVG, OB, COMPOSITE),
) -> dict[str, Any]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        bucket = classifier(event)
        if bucket is not None:
            buckets[bucket].append(event)
    out = {}
    for bucket, rows in sorted(buckets.items()):
        out[bucket] = {
            "n": len(rows),
            "share": round(len(rows) / len(events), 6) if events else None,
            "variant_stats": _variant_stats(rows, variants),
            "mean_fvg_minus_ob": mean([float(row["fvg_minus_ob"]) for row in rows]),
            "mean_composite_minus_best_single": mean(
                [float(row["composite_minus_best_single"]) for row in rows]
            ),
            "top_cohorts": [
                {
                    "symbol": key[0],
                    "session": key[1],
                    "side": key[2],
                    "role": key[3],
                    "n": count,
                }
                for key, count in Counter(
                    (row["symbol"], row["session"], row["side"], row["role"])
                    for row in rows
                ).most_common(10)
            ],
        }
    return out


def sequence_summary(events: list[dict[str, Any]]) -> dict[str, Any]:
    both = [event for event in events if _sequence_bucket(event) is not None]
    summary = bucket_summary(both, _sequence_bucket, variants=(BASELINE, FVG, OB, COMPOSITE)) if both else {}
    for bucket, row in summary.items():
        members = [event for event in both if _sequence_bucket(event) == bucket]
        floor_diffs = []
        index_diffs = []
        for event in members:
            fvg = event["first_locks"][FVG] or {}
            ob = event["first_locks"][OB] or {}
            if fvg.get("floor_r") is not None and ob.get("floor_r") is not None:
                floor_diffs.append(float(ob["floor_r"]) - float(fvg["floor_r"]))
            if fvg.get("confirmed_index") is not None and ob.get("confirmed_index") is not None:
                index_diffs.append(float(ob["confirmed_index"]) - float(fvg["confirmed_index"]))
        row["mean_ob_floor_minus_fvg_floor_r"] = mean(floor_diffs)
        row["mean_ob_confirmed_index_minus_fvg_index"] = mean(index_diffs)
    return {
        "both_fvg_and_ob_lock_events": len(both),
        "buckets": summary,
    }


def top_examples(
    events: list[dict[str, Any]],
    *,
    key: Callable[[dict[str, Any]], float],
    reverse: bool = True,
    limit: int = 10,
) -> list[dict[str, Any]]:
    rows = sorted(events, key=key, reverse=reverse)[:limit]
    keep = []
    for event in rows:
        keep.append(
            {
                "event_key": event["event_key"],
                "candle_close_utc": event["candle_close_utc"],
                "symbol": event["symbol"],
                "session": event["session"],
                "side": event["side"],
                "role": event["role"],
                "selected_timeframe": event["selected_timeframe"],
                "j46_r": event["values"][BASELINE],
                "swing_r": event["values"][SWING],
                "fvg_r": event["values"][FVG],
                "ob_r": event["values"][OB],
                "composite_r": event["values"][COMPOSITE],
                "fvg_minus_ob": event["fvg_minus_ob"],
                "best_single_variant": event["best_single_variant"],
                "composite_minus_best_single": event["composite_minus_best_single"],
                "fvg_fired": event["fired"][FVG],
                "ob_fired": event["fired"][OB],
                "fvg_outcome": event["outcomes"][FVG],
                "ob_outcome": event["outcomes"][OB],
                "composite_outcome": event["outcomes"][COMPOSITE],
                "fvg_first_lock": event["first_locks"][FVG],
                "ob_first_lock": event["first_locks"][OB],
                "composite_first_lock": event["first_locks"][COMPOSITE],
            }
        )
    return keep


def slice_summary(events: list[dict[str, Any]]) -> dict[str, Any]:
    fvg_minus_ob = [float(event["fvg_minus_ob"]) for event in events]
    composite_minus_best = [float(event["composite_minus_best_single"]) for event in events]
    return {
        "n": len(events),
        "variant_stats": _variant_stats(events, VARIANTS),
        "fvg_minus_ob": {
            "mean": mean(fvg_minus_ob),
            "sum": round(sum(fvg_minus_ob), 6),
        },
        "entry_consistency_violations": sum(
            not bool(event["same_entry_sl_tp_all_variants"]) for event in events
        ),
        "improvement_vs_j46_buckets": bucket_summary(events, _improvement_bucket),
        "absolute_positive_buckets": bucket_summary(events, _absolute_bucket, variants=(FVG, OB)),
        "lock_firing_buckets": bucket_summary(events, _fire_bucket),
        "sequence_when_both_fvg_and_ob_fire": sequence_summary(events),
        "composite_vs_best_single": {
            "mean": mean(composite_minus_best),
            "sum": round(sum(composite_minus_best), 6),
            "buckets": bucket_summary(events, _composite_bucket),
        },
        "examples": {
            "largest_fvg_over_ob": top_examples(events, key=lambda event: float(event["fvg_minus_ob"])),
            "largest_ob_over_fvg": top_examples(events, key=lambda event: -float(event["fvg_minus_ob"])),
            "largest_composite_below_best_single": top_examples(
                events,
                key=lambda event: -float(event["composite_minus_best_single"]),
            ),
            "largest_composite_above_best_single": top_examples(
                events,
                key=lambda event: float(event["composite_minus_best_single"]),
            ),
        },
    }


def build_payload(
    *,
    event_log_path: Path | str = DEFAULT_EVENT_LOG,
    cost_key: str = "0.05",
) -> dict[str, Any]:
    by_event = load_event_rows(event_log_path)
    events = build_event_profiles(by_event, cost_key=cost_key)
    y2026 = [event for event in events if event["year"] == 2026]
    return {
        "schema_version": "raw_ohlc_path_scaling_v2_structure_confluence_audit_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "inputs": {
            "event_log_path": str(event_log_path),
            "cost_key": cost_key,
            "baseline_variant": BASELINE,
            "compared_variants": list(VARIANTS),
        },
        "slices": {
            "full_resolved": slice_summary(events),
            "year_2026": slice_summary(y2026),
        },
        "approach_leg_assessment": {
            "status": "NOT_ANSWERABLE_FROM_CURRENT_V2_EVENT_LOG",
            "reason": (
                "The V2 event log is a post-fill path-management log. It has same-event "
                "entry/SL/TP and post-fill locks, but it does not retain the full pre-fill "
                "delivery path from setup decision to pending-limit touch."
            ),
            "required_fields_for_future_test": [
                "original_poi_type_and_bounds",
                "pending_limit_created_utc",
                "setup_decision_close_utc",
                "pre_fill_m1_or_m5_path_rows_until_fill_expiry_or_cancel",
                "as_of_delivery_direction_structures_before_fill",
                "delivery_leg_candidate_entry_sl_tp_and_costs",
                "reversal_leg_candidate_entry_sl_tp_and_costs",
                "mutual_exclusion_or_aggregate_risk_budget_policy",
                "broker_fill_or_pending_intent_lifecycle_state",
            ],
        },
        "candidate_hypotheses": [
            {
                "id": "H1_POST_ENTRY_OB_AFTER_FVG_TAIL_PRESERVATION",
                "status": "DISCOVERY_ONLY_NOT_REGISTERED",
                "description": (
                    "When FVG and OB both fire post-entry, FVG usually fires first and OB often "
                    "preserves more right tail; test whether FVG should confirm delivery while OB "
                    "sets the protective floor."
                ),
            },
            {
                "id": "H2_FVG_ONLY_RESCUE_WHEN_OB_DOES_NOT_FORM",
                "status": "DISCOVERY_ONLY_NOT_REGISTERED",
                "description": (
                    "Rows where FVG fires but OB does not may be a separate rescue pocket; test "
                    "for concentration, regime, and forward survival before any rule registration."
                ),
            },
            {
                "id": "H3_COMPOSITE_OVERLOCK_ARBITRATION",
                "status": "DISCOVERY_ONLY_NOT_REGISTERED",
                "description": (
                    "Composite highest-floor policy often underperforms the best single selector; "
                    "future composite logic should require arbitration, not blind highest-floor use."
                ),
            },
            {
                "id": "H4_DELIVERY_LEG_AND_REVERSAL_LEG_DOUBLE_SETUP",
                "status": "DATA_GAP_SPEC_ONLY",
                "description": (
                    "The owner's two-move idea is coherent but needs pre-fill path and risk-budget "
                    "telemetry before it can be scored."
                ),
            },
        ],
        "synthesis": {
            "summary": (
                "Structural variants are alternative management policies on the same setup rows, "
                "not additive trade streams. Agreement/disagreement is informative, especially "
                "FVG-only rescue pockets, OB-after-FVG tail preservation, and Composite overlock."
            ),
            "answered_questions": [
                "The Swing/FVG/OB/Composite R sums cannot be added; they mostly score the same event keys.",
                "Composite is the current 'use all registered selectors' policy, and it is not the sum of single-selector returns.",
                "The current V2 log can audit post-entry confluence and disagreement.",
                "The current V2 log cannot validate a separate pre-fill delivery-leg trade into the POI.",
            ],
            "ambiguities": [
                "Same-event confluence is still discovery-set evidence and cannot validate live logic.",
                "FVG-only and OB-only pockets may be concentrated by symbol/session/side/role.",
                "The event log has first lock metadata but not every pre-fill structure needed for the two-leg delivery/reversal hypothesis.",
                "R costs are still sensitivity assumptions, not broker-reconciled spread/slippage/commission.",
            ],
            "next_steps": [
                "Register a forward-only confluence ledger for FVG/OB agreement and disagreement after V2b resolved rows exist.",
                "Add pre-fill delivery-path capture to future path replay before testing the two-leg setup.",
                "Do not promote Composite; study arbitration rules only as discovery until forward evidence exists.",
                "Keep every confluence hypothesis at NO_PROMOTION_VERDICT until pre-registered unseen validation exists.",
            ],
        },
    }


def write_json(payload: dict[str, Any], path: Path | str) -> None:
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
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        out.append("| " + " | ".join(fmt(value) for value in row) + " |")
    return out


def _bucket_table(bucket_payload: dict[str, Any], *, variants: tuple[str, ...]) -> list[list[Any]]:
    rows = []
    for bucket, data in bucket_payload.items():
        row = [bucket, data["n"], data["share"]]
        for variant in variants:
            row.append(data["variant_stats"][variant]["mean_r"])
        row.extend([data["mean_fvg_minus_ob"], data["mean_composite_minus_best_single"]])
        rows.append(row)
    return rows


def write_markdown(payload: dict[str, Any], path: Path | str) -> None:
    out = Path(path)
    full = payload["slices"]["full_resolved"]
    y2026 = payload["slices"]["year_2026"]
    lines = [
        "# V2 Structural Confluence And Disagreement Audit",
        "",
        "Date: 2026-05-02",
        "Scope: research/tooling only",
        f"Promotion verdict: `{payload['promotion_verdict']}`",
        "",
        "## Synthesis",
        "",
        payload["synthesis"]["summary"],
        "",
        "## Direct Answers",
        "",
        *[f"- {item}" for item in payload["synthesis"]["answered_questions"]],
        "",
        "## Slice Summary",
        "",
        "| Slice | n | entry consistency violations | J46 mean | Swing mean | FVG mean | OB mean | Composite mean | FVG-OB mean | Composite-best-single mean |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, data in (("full_resolved", full), ("year_2026", y2026)):
        stats = data["variant_stats"]
        lines.append(
            "| "
            f"{name} | {data['n']} | {data['entry_consistency_violations']} | "
            f"{fmt(stats[BASELINE]['mean_r'])} | {fmt(stats[SWING]['mean_r'])} | "
            f"{fmt(stats[FVG]['mean_r'])} | {fmt(stats[OB]['mean_r'])} | "
            f"{fmt(stats[COMPOSITE]['mean_r'])} | {fmt(data['fvg_minus_ob']['mean'])} | "
            f"{fmt(data['composite_vs_best_single']['mean'])} |"
        )

    lines.extend(
        [
            "",
            "## FVG vs OB Improvement Buckets",
            "",
            "Full resolved:",
            "",
            *table(
                ["bucket", "n", "share", "J46 mean", "FVG mean", "OB mean", "Composite mean", "FVG-OB mean", "Composite-best mean"],
                _bucket_table(full["improvement_vs_j46_buckets"], variants=(BASELINE, FVG, OB, COMPOSITE)),
            ),
            "",
            "2026 only:",
            "",
            *table(
                ["bucket", "n", "share", "J46 mean", "FVG mean", "OB mean", "Composite mean", "FVG-OB mean", "Composite-best mean"],
                _bucket_table(y2026["improvement_vs_j46_buckets"], variants=(BASELINE, FVG, OB, COMPOSITE)),
            ),
            "",
            "## Lock-Firing Buckets",
            "",
            "Full resolved:",
            "",
            *table(
                ["bucket", "n", "share", "J46 mean", "FVG mean", "OB mean", "Composite mean", "FVG-OB mean", "Composite-best mean"],
                _bucket_table(full["lock_firing_buckets"], variants=(BASELINE, FVG, OB, COMPOSITE)),
            ),
            "",
            "2026 only:",
            "",
            *table(
                ["bucket", "n", "share", "J46 mean", "FVG mean", "OB mean", "Composite mean", "FVG-OB mean", "Composite-best mean"],
                _bucket_table(y2026["lock_firing_buckets"], variants=(BASELINE, FVG, OB, COMPOSITE)),
            ),
            "",
            "## Sequence When Both FVG And OB Fire",
            "",
            f"Full both-lock events: {full['sequence_when_both_fvg_and_ob_fire']['both_fvg_and_ob_lock_events']}",
            "",
            *table(
                [
                    "sequence",
                    "n",
                    "share",
                    "J46 mean",
                    "FVG mean",
                    "OB mean",
                    "Composite mean",
                    "FVG-OB mean",
                    "OB floor - FVG floor",
                    "OB index - FVG index",
                ],
                [
                    [
                        bucket,
                        data["n"],
                        data["share"],
                        data["variant_stats"][BASELINE]["mean_r"],
                        data["variant_stats"][FVG]["mean_r"],
                        data["variant_stats"][OB]["mean_r"],
                        data["variant_stats"][COMPOSITE]["mean_r"],
                        data["mean_fvg_minus_ob"],
                        data["mean_ob_floor_minus_fvg_floor_r"],
                        data["mean_ob_confirmed_index_minus_fvg_index"],
                    ]
                    for bucket, data in full["sequence_when_both_fvg_and_ob_fire"]["buckets"].items()
                ],
            ),
            "",
            f"2026 both-lock events: {y2026['sequence_when_both_fvg_and_ob_fire']['both_fvg_and_ob_lock_events']}",
            "",
            *table(
                [
                    "sequence",
                    "n",
                    "share",
                    "J46 mean",
                    "FVG mean",
                    "OB mean",
                    "Composite mean",
                    "FVG-OB mean",
                    "OB floor - FVG floor",
                    "OB index - FVG index",
                ],
                [
                    [
                        bucket,
                        data["n"],
                        data["share"],
                        data["variant_stats"][BASELINE]["mean_r"],
                        data["variant_stats"][FVG]["mean_r"],
                        data["variant_stats"][OB]["mean_r"],
                        data["variant_stats"][COMPOSITE]["mean_r"],
                        data["mean_fvg_minus_ob"],
                        data["mean_ob_floor_minus_fvg_floor_r"],
                        data["mean_ob_confirmed_index_minus_fvg_index"],
                    ]
                    for bucket, data in y2026["sequence_when_both_fvg_and_ob_fire"]["buckets"].items()
                ],
            ),
            "",
            "## Composite vs Best Single Selector",
            "",
            f"- Full resolved mean Composite minus best single: `{fmt(full['composite_vs_best_single']['mean'])}`, sum `{fmt(full['composite_vs_best_single']['sum'])}`.",
            f"- 2026 mean Composite minus best single: `{fmt(y2026['composite_vs_best_single']['mean'])}`, sum `{fmt(y2026['composite_vs_best_single']['sum'])}`.",
            "",
            "Full resolved:",
            "",
            *table(
                ["bucket", "n", "share", "J46 mean", "FVG mean", "OB mean", "Composite mean", "FVG-OB mean", "Composite-best mean"],
                _bucket_table(full["composite_vs_best_single"]["buckets"], variants=(BASELINE, FVG, OB, COMPOSITE)),
            ),
            "",
            "2026 only:",
            "",
            *table(
                ["bucket", "n", "share", "J46 mean", "FVG mean", "OB mean", "Composite mean", "FVG-OB mean", "Composite-best mean"],
                _bucket_table(y2026["composite_vs_best_single"]["buckets"], variants=(BASELINE, FVG, OB, COMPOSITE)),
            ),
            "",
            "## Example Disagreements",
            "",
            "Largest 2026 FVG-over-OB examples:",
            "",
            *table(
                ["event", "symbol", "session", "side", "J46", "FVG", "OB", "Composite", "FVG-OB", "FVG fired", "OB fired", "FVG outcome", "OB outcome"],
                [
                    [
                        row["event_key"],
                        row["symbol"],
                        row["session"],
                        row["side"],
                        row["j46_r"],
                        row["fvg_r"],
                        row["ob_r"],
                        row["composite_r"],
                        row["fvg_minus_ob"],
                        row["fvg_fired"],
                        row["ob_fired"],
                        row["fvg_outcome"],
                        row["ob_outcome"],
                    ]
                    for row in y2026["examples"]["largest_fvg_over_ob"][:8]
                ],
            ),
            "",
            "Largest 2026 OB-over-FVG examples:",
            "",
            *table(
                ["event", "symbol", "session", "side", "J46", "FVG", "OB", "Composite", "FVG-OB", "FVG fired", "OB fired", "FVG outcome", "OB outcome"],
                [
                    [
                        row["event_key"],
                        row["symbol"],
                        row["session"],
                        row["side"],
                        row["j46_r"],
                        row["fvg_r"],
                        row["ob_r"],
                        row["composite_r"],
                        row["fvg_minus_ob"],
                        row["fvg_fired"],
                        row["ob_fired"],
                        row["fvg_outcome"],
                        row["ob_outcome"],
                    ]
                    for row in y2026["examples"]["largest_ob_over_fvg"][:8]
                ],
            ),
            "",
            "## Approach-Leg Assessment",
            "",
            f"Status: `{payload['approach_leg_assessment']['status']}`",
            "",
            payload["approach_leg_assessment"]["reason"],
            "",
            "Required future fields:",
            "",
            *[f"- `{item}`" for item in payload["approach_leg_assessment"]["required_fields_for_future_test"]],
            "",
            "## Candidate Hypotheses",
            "",
            *[
                f"- `{item['id']}` ({item['status']}): {item['description']}"
                for item in payload["candidate_hypotheses"]
            ],
            "",
            "## Ambiguity Ledger",
            "",
            *[f"- {item}" for item in payload["synthesis"]["ambiguities"]],
            "",
            "## Next Steps",
            "",
            *[f"{idx}. {item}" for idx, item in enumerate(payload["synthesis"]["next_steps"], start=1)],
            "",
        ]
    )
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
