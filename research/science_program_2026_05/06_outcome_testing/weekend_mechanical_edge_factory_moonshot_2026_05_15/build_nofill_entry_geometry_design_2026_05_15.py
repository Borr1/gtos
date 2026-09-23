#!/usr/bin/env python3
"""Build no-fill entry-geometry design artifacts from forward shadow path rows.

The artifact is a design/control packet only. It uses post-decision forward path
observations to define future mechanical challengers and capture needs, but it
does not claim realized performance or validation.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
SOURCE_PATH = REPO / "shadow_logs" / "candidate_path_follow.jsonl"
UTC_NOW = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}


def read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                yield {"_parse_error": True, "_line_no": line_no, "_raw": line[:500]}


def sort_key(row: dict[str, Any]) -> tuple[str, str]:
    return (
        str(row.get("asof_latest_candle_utc") or ""),
        str(row.get("created_at_utc") or ""),
    )


def latest_candidate_path_rows() -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for row in read_jsonl(SOURCE_PATH):
        if row.get("_parse_error"):
            continue
        candidate_id = row.get("candidate_id")
        if not candidate_id:
            continue
        current = latest.get(candidate_id)
        if current is None or sort_key(row) >= sort_key(current):
            latest[candidate_id] = row
    return latest


def get_nested(row: dict[str, Any], path: list[str], default: Any = None) -> Any:
    cur: Any = row
    for part in path:
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def numeric(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def median_or_none(values: list[float]) -> float | None:
    values = [value for value in values if value is not None]
    if not values:
        return None
    return round(float(median(values)), 6)


def mean_or_none(values: list[float]) -> float | None:
    values = [value for value in values if value is not None]
    if not values:
        return None
    return round(sum(values) / len(values), 6)


def nofill_row(row: dict[str, Any]) -> dict[str, Any]:
    distance = numeric(row.get("nearest_distance_to_entry"))
    trade_params = row.get("trade_parameters") or {}
    sierra_features = get_nested(row, ["external_confluence", "sierra", "features"], {}) or {}
    return {
        "candidate_id": row.get("candidate_id"),
        "symbol": row.get("symbol"),
        "broker_symbol": row.get("broker_symbol"),
        "side": row.get("side"),
        "framework": row.get("framework"),
        "decision_time_utc": row.get("decision_time_utc"),
        "asof_latest_candle_utc": row.get("asof_latest_candle_utc"),
        "trade_id": row.get("trade_id"),
        "path_label": row.get("path_label"),
        "path_status": "NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH",
        "entry_price": trade_params.get("entry_price"),
        "stop_loss": trade_params.get("stop_loss"),
        "take_profit_1": trade_params.get("take_profit_1"),
        "nearest_distance_to_entry": distance,
        "abs_nearest_distance_to_entry": abs(distance) if distance is not None else None,
        "last_close": row.get("last_close"),
        "max_high": row.get("max_high"),
        "min_low": row.get("min_low"),
        "sierra_status": get_nested(row, ["external_confluence", "sierra", "status"]),
        "sierra_event15_thin_depth10_rate": sierra_features.get("event15_thin_depth10_rate"),
        "sierra_event15_median_total_depth10": sierra_features.get("event15_median_total_depth10"),
        "sierra_event15_mid_change_ticks": sierra_features.get("event15_mid_change_ticks"),
        "databento_status": get_nested(row, ["external_confluence", "databento", "status"]),
        "no_leak_status": row.get("no_leak_status"),
        "promotion_verdict": row.get("promotion_verdict"),
        "evidence_class": "FORWARD_SHADOW_PATH_FOLLOW_RESEARCH_ONLY",
        "claim_boundary": "Path intelligence only; this row is not a filled trade or strategy result.",
    }


def build_group_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(str(row["symbol"]), str(row["side"]), str(row["framework"]))].append(row)

    output: list[dict[str, Any]] = []
    for (symbol, side, framework), items in sorted(groups.items()):
        distances = [numeric(item.get("abs_nearest_distance_to_entry")) for item in items]
        thin_rates = [numeric(item.get("sierra_event15_thin_depth10_rate")) for item in items]
        total_depth = [numeric(item.get("sierra_event15_median_total_depth10")) for item in items]
        mid_change = [numeric(item.get("sierra_event15_mid_change_ticks")) for item in items]
        output.append(
            {
                "symbol": symbol,
                "side": side,
                "framework": framework,
                "nofill_tp_area_count": len(items),
                "median_abs_nearest_distance_to_entry": median_or_none(distances),
                "avg_abs_nearest_distance_to_entry": mean_or_none(distances),
                "sierra_feature_count": sum(1 for item in items if item.get("sierra_status") == "FEATURES_EXTRACTED"),
                "avg_sierra_event15_thin_depth10_rate": mean_or_none(thin_rates),
                "avg_sierra_event15_median_total_depth10": mean_or_none(total_depth),
                "avg_sierra_event15_mid_change_ticks": mean_or_none(mid_change),
                "example_candidate_ids": [item["candidate_id"] for item in items[:5]],
                "evidence_class": "DESCRIPTIVE_DIAGNOSTIC",
                "claim_boundary": "Group describes no-fill-to-TP-area path behavior only.",
            }
        )
    return output


def build_path_context(latest_rows: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    groups: Counter[tuple[str, str, str, str]] = Counter()
    for row in latest_rows.values():
        groups[
            (
                str(row.get("symbol")),
                str(row.get("side")),
                str(row.get("framework")),
                str(row.get("path_label")),
            )
        ] += 1
    return [
        {
            "symbol": symbol,
            "side": side,
            "framework": framework,
            "path_label": path_label,
            "candidate_count": count,
            "evidence_class": "DESCRIPTIVE_DIAGNOSTIC",
        }
        for (symbol, side, framework, path_label), count in sorted(groups.items())
    ]


def build_branch_specs(group_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    for group in group_rows:
        base = {
            "symbol": group["symbol"],
            "side": group["side"],
            "framework": group["framework"],
            "source_nofill_tp_area_count": group["nofill_tp_area_count"],
            "median_abs_nearest_distance_to_entry": group["median_abs_nearest_distance_to_entry"],
        }
        for fraction in (0.25, 0.5, 0.75, 1.0):
            specs.append(
                {
                    **base,
                    "branch_id": f"ENTRY_OFFSET_{int(fraction * 100):03d}PCT_MISS_DISTANCE",
                    "branch_type": "future_strategy_projection_design",
                    "mechanical_rule": "Move the candidate limit entry toward the decision-time/path-side current price by the stated fraction of the observed miss distance, then recompute fill, stop, target, cost, and path ordering on a frozen same-denominator packet.",
                    "offset_fraction_of_observed_miss_distance": fraction,
                    "why": "Tests whether the current limit is too deep for contexts where the original path reached TP-area without touching entry.",
                    "required_before_scoring": [
                        "decision-time tradable bid/ask or source-safe current price",
                        "frozen original candidate denominator",
                        "spread/slippage/commission assumptions",
                        "tick or conservative path ordering",
                        "same-denominator incumbent comparison",
                    ],
                    "controls": [
                        "neighbor-window continuation control",
                        "generic movement control",
                        "duplicate-effective-N and concentration",
                        "source-bias and fail-closed sensitivity",
                        "cost/friction stress",
                    ],
                    "claim_boundary": "Design branch only; not scored and not a recommendation.",
                }
            )
        specs.append(
            {
                **base,
                "branch_id": "MARKET_OR_TOUCH_ENTRY_ROUTER_DESIGN",
                "branch_type": "future_strategy_projection_design",
                "mechanical_rule": "Route no-fill-prone contexts to a market-at-confirmation or first-touch entry model only if decision-time spread/slippage and kill-zone rules pass.",
                "offset_fraction_of_observed_miss_distance": None,
                "why": "Tests whether delivery failure is entry placement rather than signal direction.",
                "required_before_scoring": [
                    "decision-time spread",
                    "market-order cost model",
                    "min distance/stop constraints",
                    "same-denominator original-limit comparison",
                    "owner-approved research-only projection scope",
                ],
                "controls": [
                    "execution friction stress",
                    "stop-first conservative path ordering",
                    "same-symbol/session generic movement control",
                ],
                "claim_boundary": "Design branch only; not scored and not a live execution proposal.",
            }
        )
    return specs


def build_capture_requirements() -> list[dict[str, Any]]:
    return [
        {
            "requirement_id": "NOFILL-GEOM-CAP-001",
            "field_family": "decision_time_price",
            "fields": ["bid", "ask", "mid", "spread", "source_timestamp_utc"],
            "why": "Offset or market-entry challengers need the tradable decision-time price; path-follow latest close is insufficient.",
        },
        {
            "requirement_id": "NOFILL-GEOM-CAP-002",
            "field_family": "candidate_geometry",
            "fields": ["original_entry", "stop_loss", "take_profit_1", "risk_distance", "min_distance_constraint", "order_type"],
            "why": "Same-denominator challenger projection needs frozen original geometry before path outcome opening.",
        },
        {
            "requirement_id": "NOFILL-GEOM-CAP-003",
            "field_family": "path_ordering",
            "fields": ["tick_or_m1_bid_ask_path", "entry_touch_time", "tp_touch_time", "sl_touch_time", "ambiguity_flag"],
            "why": "OHLC-only path can overstate fill/order sequence; ambiguous rows must fail closed or use conservative ordering.",
        },
        {
            "requirement_id": "NOFILL-GEOM-CAP-004",
            "field_family": "cost_and_execution",
            "fields": ["spread_model", "slippage_model", "commission", "reject_or_min_distance_status"],
            "why": "A shallower or market entry can turn path movement into a trade only if costs and order constraints survive.",
        },
    ]


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def main() -> int:
    latest_rows = latest_candidate_path_rows()
    nofill_rows = [
        nofill_row(row)
        for row in latest_rows.values()
        if row.get("path_label") == "continued_without_entry_touch_to_tp_area"
    ]
    group_rows = build_group_rows(nofill_rows)
    path_context = build_path_context(latest_rows)
    branch_specs = build_branch_specs(group_rows)
    capture_requirements = build_capture_requirements()

    summary = {
        "schema": "nofill_entry_geometry_design_packet_v1",
        "generated_utc": UTC_NOW,
        "route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H",
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "DESCRIPTIVE_DIAGNOSTIC_AND_FUTURE_STRATEGY_PROJECTION_DESIGN_ONLY",
        "claim_boundary": "No-fill-to-TP-area rows are post-decision path intelligence. This packet designs future same-denominator tests; it does not score an entry-offset strategy or claim performance.",
        "source": {
            "path": str(SOURCE_PATH),
            "duplicate_policy": "latest candidate_path_follow row per candidate_id",
        },
        "counts": {
            "latest_candidate_path_rows": len(latest_rows),
            "nofill_tp_area_rows": len(nofill_rows),
            "nofill_group_rows": len(group_rows),
            "path_context_rows": len(path_context),
            "branch_spec_rows": len(branch_specs),
            "capture_requirement_rows": len(capture_requirements),
        },
        "controls_inherited_from_worker_d": [
            "same-denominator incumbent comparison required",
            "duplicate-effective-N and concentration required",
            "neighbor-window/placebo and generic movement controls required",
            "fill/path ordering and cost/friction stress required before strategy metrics",
            "neutral/path movement language only until full strategy projection exists",
        ],
        "primary_findings": [
            "No-fill-to-TP-area is frequent enough in the latest candidate_path_follow denominator to justify a dedicated entry-geometry challenger design.",
            "Observed miss distance varies sharply by symbol/side/framework, so offset branches must be symbol/session/regime scoped rather than global.",
            "Sierra depth features are available for a subset of metals/index no-fill rows and should become context descriptors, not causal claims yet.",
            "Decision-time bid/ask and conservative path ordering are required before converting this design into a strategy projection.",
        ],
    }

    write_json(ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_DESIGN_RESULT_2026-05-15.json", summary)
    write_jsonl(ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_SOURCE_ROWS_2026-05-15.jsonl", nofill_rows)
    write_jsonl(ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_GROUP_LEDGER_2026-05-15.jsonl", group_rows)
    write_jsonl(ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_PATH_CONTEXT_LEDGER_2026-05-15.jsonl", path_context)
    write_jsonl(ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_BRANCH_SPECS_2026-05-15.jsonl", branch_specs)
    write_jsonl(ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_CAPTURE_REQUIREMENTS_2026-05-15.jsonl", capture_requirements)

    md_lines = [
        "# No-Fill Entry Geometry Design Packet",
        "",
        f"Generated UTC: `{UTC_NOW}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: `DESCRIPTIVE_DIAGNOSTIC_AND_FUTURE_STRATEGY_PROJECTION_DESIGN_ONLY`",
        "",
        "This packet does not score an entry-offset strategy. It turns no-fill-to-TP-area path behavior into frozen future branch specs and capture requirements.",
        "",
        "## Counts",
        "",
    ]
    for key, value in summary["counts"].items():
        md_lines.append(f"- `{key}`: `{value}`")
    md_lines.extend(["", "## Primary Findings", ""])
    for finding in summary["primary_findings"]:
        md_lines.append(f"- {finding}")
    md_lines.extend(["", "## Required Before Scoring", ""])
    for requirement in capture_requirements:
        md_lines.append(
            f"- `{requirement['requirement_id']}` {requirement['field_family']}: {', '.join(requirement['fields'])}"
        )
    (ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_DESIGN_SUMMARY_2026-05-15.md").write_text(
        "\n".join(md_lines) + "\n", encoding="utf-8"
    )

    print(json.dumps({"ok": True, "generated_utc": UTC_NOW, "counts": summary["counts"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
