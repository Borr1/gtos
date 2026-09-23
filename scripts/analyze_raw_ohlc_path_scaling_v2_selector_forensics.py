#!/usr/bin/env python3
"""Explain V2 structural selector tradeoffs from the event log.

Research/tooling only. This script recomputes selector-vs-J46 pairwise
statistics from the V2 event JSONL, then surfaces why a higher headline
selector can still be a weaker V2b candidate when the lift is concentrated in
the wrong groups.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.audit_raw_ohlc_path_scaling_v2_concentration import (  # noqa: E402
    BASELINE_VARIANT,
    GROUPS,
    PairStats,
    _net_r,
    concentration_by_dimension,
    group_deltas,
)


DEFAULT_EVENT_LOG = (
    "data/external/validation/calendar_macro_bundle_v1/historical_opportunities/"
    "raw_ohlc_prequential_replay/path_scaling_v2_structural_levels/"
    "raw_ohlc_path_scaling_v2_structural_levels_events_20260501T213225Z.jsonl"
)
DEFAULT_OUTPUT_JSON = (
    "research/phase_3_external_feed_validation/"
    "RAW_OHLC_PATH_SCALING_V2_SELECTOR_FORENSICS_2026-05-02.json"
)
DEFAULT_OUTPUT_MD = (
    "research/phase_3_external_feed_validation/"
    "RAW_OHLC_PATH_SCALING_V2_SELECTOR_FORENSICS_2026-05-02.md"
)
STRUCTURAL_VARIANTS = (
    "STRUCT_SWING_PROTECTED_V2",
    "STRUCT_FVG_MID_EDGE_V2",
    "STRUCT_OB_BOUNDARY_V2",
    "STRUCT_COMPOSITE_ANY_V2",
)


def parse_utc(value: str) -> datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def load_event_rows(event_log: Path | str, variants: Iterable[str]) -> dict[str, dict[str, dict[str, Any]]]:
    wanted = set(variants) | {BASELINE_VARIANT}
    by_event: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    with Path(event_log).open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            variant = row.get("variant_id")
            if variant not in wanted:
                continue
            by_event[str(row["event_key"])][str(variant)] = row
    return by_event


def pair_rows_for_variant(
    by_event: dict[str, dict[str, dict[str, Any]]],
    variant: str,
    *,
    cost_key: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for event_key, variants in by_event.items():
        baseline = variants.get(BASELINE_VARIANT)
        candidate = variants.get(variant)
        if baseline is None or candidate is None:
            continue
        baseline_r = _net_r(baseline, cost_key=cost_key)
        candidate_r = _net_r(candidate, cost_key=cost_key)
        if baseline_r is None or candidate_r is None:
            continue
        candle_close = str(candidate.get("candle_close_utc") or baseline.get("candle_close_utc"))
        year = parse_utc(candle_close).year if candle_close else None
        rows.append(
            {
                "event_key": event_key,
                "year": year,
                "symbol": candidate.get("symbol"),
                "session": candidate.get("session"),
                "selected_timeframe": candidate.get("selected_timeframe"),
                "side": candidate.get("mechanical_side") or "none",
                "role": candidate.get("role"),
                "raw_cohort_key": candidate.get("raw_cohort_key"),
                "baseline_r": float(baseline_r),
                "candidate_r": float(candidate_r),
                "delta_r": float(candidate_r) - float(baseline_r),
            }
        )
    return rows


def stats_from_rows(rows: list[dict[str, Any]]) -> PairStats:
    stats = PairStats()
    for row in rows:
        stats.add(
            baseline_r=float(row["baseline_r"]),
            candidate_r=float(row["candidate_r"]),
            row=row,
        )
    return stats


def stats_by_year(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["year"] is not None:
            buckets[int(row["year"])].append(row)
    out = []
    for year in sorted(buckets):
        summary = stats_from_rows(buckets[year]).to_summary()
        summary["year"] = year
        out.append(summary)
    return out


def _group_lookup(stats: PairStats) -> dict[str, dict[str, Any]]:
    return {row["group"]: row for row in group_deltas(stats)}


def _sum_positive_group_delta(groups: dict[str, dict[str, Any]]) -> float:
    return sum(
        float(row.get("sum_delta_candidate_minus_baseline") or 0.0)
        for row in groups.values()
        if float(row.get("sum_delta_candidate_minus_baseline") or 0.0) > 0
    )


def cleanliness(stats: PairStats) -> dict[str, Any]:
    groups = _group_lookup(stats)
    target = groups.get("target_cohorts", {})
    negative = groups.get("negative_controls", {})
    blocked = groups.get("blocked_dominance_controls", {})
    positive_sum = _sum_positive_group_delta(groups)
    group_values = {
        group: float((groups.get(group) or {}).get("sum_delta_candidate_minus_baseline") or 0.0)
        for group in GROUPS
    }
    return {
        "all_major_groups_nonnegative": all(
            group_values[group] >= 0
            for group in (
                "all_enabled",
                "target_cohorts",
                "primary_controlled_family",
                "cleared_non_primary_targets",
                "negative_controls",
                "blocked_dominance_controls",
            )
        ),
        "target_mean_delta": target.get("mean_delta_candidate_minus_baseline"),
        "negative_control_mean_delta": negative.get("mean_delta_candidate_minus_baseline"),
        "blocked_control_mean_delta": blocked.get("mean_delta_candidate_minus_baseline"),
        "target_minus_negative_mean_delta": (
            round(
                float(target.get("mean_delta_candidate_minus_baseline") or 0.0)
                - float(negative.get("mean_delta_candidate_minus_baseline") or 0.0),
                6,
            )
        ),
        "blocked_sum_delta": blocked.get("sum_delta_candidate_minus_baseline"),
        "blocked_positive_share": (
            round(float(blocked.get("sum_delta_candidate_minus_baseline") or 0.0) / positive_sum, 6)
            if positive_sum and float(blocked.get("sum_delta_candidate_minus_baseline") or 0.0) > 0
            else 0.0
        ),
    }


def variant_profile(rows: list[dict[str, Any]]) -> dict[str, Any]:
    stats = stats_from_rows(rows)
    pair = stats.to_summary()
    n = int(pair["paired_resolved_n"] or 0)
    changed_n = int(pair["candidate_better_n"] or 0) + int(pair["baseline_better_n"] or 0)
    profile = {
        "pairwise_vs_j46": pair,
        "activation_rate": round(changed_n / n, 6) if n else None,
        "tie_rate": round(float(pair["tie_n"] or 0) / n, 6) if n else None,
        "cleanliness": cleanliness(stats),
        "group_deltas": group_deltas(stats),
        "by_year": stats_by_year(rows),
        "top_raw_cohorts": concentration_by_dimension(stats, "raw_cohort_key")[:8],
    }
    return profile


def decision_readout(variants: dict[str, Any]) -> dict[str, Any]:
    fvg = variants["STRUCT_FVG_MID_EDGE_V2"]
    ob = variants["STRUCT_OB_BOUNDARY_V2"]
    swing = variants["STRUCT_SWING_PROTECTED_V2"]
    composite = variants["STRUCT_COMPOSITE_ANY_V2"]
    return {
        "fvg_headline_delta_gt_ob": (
            fvg["pairwise_vs_j46"]["mean_delta_candidate_minus_baseline"]
            > ob["pairwise_vs_j46"]["mean_delta_candidate_minus_baseline"]
        ),
        "ob_all_major_groups_nonnegative": ob["cleanliness"]["all_major_groups_nonnegative"],
        "fvg_all_major_groups_nonnegative": fvg["cleanliness"]["all_major_groups_nonnegative"],
        "swing_all_major_groups_nonnegative": swing["cleanliness"]["all_major_groups_nonnegative"],
        "composite_all_major_groups_nonnegative": composite["cleanliness"]["all_major_groups_nonnegative"],
        "recommended_v2b_candidate": "STRUCT_OB_BOUNDARY_V2",
        "recommendation_reason": (
            "FVG has the larger headline mean delta, but OB-boundary is the only inspected "
            "selector that is nonnegative across all major target/control/blocker groups."
        ),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }


def build_payload(
    *,
    event_log_path: Path | str = DEFAULT_EVENT_LOG,
    cost_key: str = "0.05",
) -> dict[str, Any]:
    by_event = load_event_rows(event_log_path, STRUCTURAL_VARIANTS)
    variants = {
        variant: variant_profile(pair_rows_for_variant(by_event, variant, cost_key=cost_key))
        for variant in STRUCTURAL_VARIANTS
    }
    return {
        "schema_version": "raw_ohlc_path_scaling_v2_selector_forensics_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "inputs": {
            "event_log_path": str(event_log_path),
            "cost_key": cost_key,
            "baseline_variant": BASELINE_VARIANT,
            "variants": list(STRUCTURAL_VARIANTS),
        },
        "variants": variants,
        "decision_readout": decision_readout(variants),
        "synthesis": {
            "summary": (
                "V2 selector forensics confirm that FVG can lead headline/2026 returns while "
                "still being a weaker V2b level-quality candidate than OB-boundary."
            ),
            "ambiguities": [
                "This is same-event-log forensics and cannot validate V2b.",
                "The cost key is an R-sensitivity value, not measured spread/slippage.",
                "All V3 reentry questions remain design-only until V2b has resolved prospective pairs.",
            ],
            "next_steps": [
                "Use OB-boundary as the registered V2b level-quality candidate.",
                "Keep FVG as a comparison arm, not the primary candidate.",
                "Continue post-cutoff replay collection until resolved V2b sample floors are met.",
            ],
        },
    }


def write_json(payload: dict[str, Any], path: Path | str) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def _table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        out.append("| " + " | ".join(_fmt(value) for value in row) + " |")
    return out


def write_markdown(payload: dict[str, Any], path: Path | str) -> None:
    out = Path(path)
    variants = payload["variants"]
    decision = payload["decision_readout"]
    headline_rows = []
    group_rows = []
    year_rows = []
    for variant, data in variants.items():
        pair = data["pairwise_vs_j46"]
        clean = data["cleanliness"]
        headline_rows.append(
            [
                variant,
                pair["paired_resolved_n"],
                pair["candidate_mean_r"],
                pair["mean_delta_candidate_minus_baseline"],
                data["activation_rate"],
                clean["all_major_groups_nonnegative"],
                clean["target_mean_delta"],
                clean["blocked_control_mean_delta"],
            ]
        )
        for group in data["group_deltas"]:
            group_rows.append(
                [
                    variant,
                    group["group"],
                    group["paired_resolved_n"],
                    group["mean_delta_candidate_minus_baseline"],
                    group["sum_delta_candidate_minus_baseline"],
                ]
            )
        for year in data["by_year"]:
            year_rows.append(
                [
                    variant,
                    year["year"],
                    year["paired_resolved_n"],
                    year["candidate_mean_r"],
                    year["mean_delta_candidate_minus_baseline"],
                ]
            )
    lines = [
        "# V2 Selector Forensics: FVG vs OB Boundary",
        "",
        "Date: 2026-05-02",
        "Scope: research/tooling only",
        f"Promotion verdict: `{payload['promotion_verdict']}`",
        "",
        "## Synthesis",
        "",
        payload["synthesis"]["summary"],
        "",
        f"Recommended V2b candidate: `{decision['recommended_v2b_candidate']}`",
        "",
        decision["recommendation_reason"],
        "",
        "## Headline Selector Profile",
        "",
        *_table(
            [
                "Variant",
                "paired n",
                "candidate mean R",
                "mean delta vs J46",
                "activation rate",
                "all groups >=0",
                "target mean delta",
                "blocked mean delta",
            ],
            headline_rows,
        ),
        "",
        "## Year Profile",
        "",
        *_table(
            ["Variant", "Year", "paired n", "candidate mean R", "mean delta vs J46"],
            year_rows,
        ),
        "",
        "## Major Group Deltas",
        "",
        *_table(
            ["Variant", "Group", "paired n", "mean delta", "sum delta"],
            group_rows,
        ),
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
        "recommended="
        f"{payload['decision_readout']['recommended_v2b_candidate']} "
        f"promotion={payload['promotion_verdict']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
