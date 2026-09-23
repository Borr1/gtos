#!/usr/bin/env python3
"""Join Sierra .depth command-flow proxy rows back to Route C controls.

This consumes the full depth event-window request ledger, preserves every
request row including source gaps, and builds no-promotion command-flow
descriptor controls over the 882 locally replayed .depth windows.
"""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
SOURCE_STAMP = "2026-05-15"
STAMP = "2026-05-16"
ROUTE_ID = "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H"

REQUEST_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_EVENT_WINDOW_REQUEST_LEDGER_{STAMP}.jsonl"
FEATURE_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_EVENT_WINDOW_FEATURE_LEDGER_{STAMP}.jsonl"
SOURCE_GAP_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_EVENT_WINDOW_SOURCE_GAP_LEDGER_{STAMP}.jsonl"
COOCCURRENCE_LEDGER = ROUTE_DIR / f"SIERRA_ROUTE_C_COOCCURRENCE_CONTROL_LEDGER_{STAMP}.jsonl"
DATE_REGIME_LEDGER = ROUTE_DIR / f"SIERRA_ROUTE_C_DATE_REGIME_SPLIT_DATE_LEDGER_{STAMP}.jsonl"
RESIDUAL_FAMILY_LEDGER = ROUTE_DIR / f"SIERRA_ROUTE_C_RESIDUAL_FAMILY_LEDGER_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"SIERRA_DEPTH_ROUTE_C_COMMAND_FLOW_CONTROL_RESULT_{STAMP}.json"
JOIN_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_ROUTE_C_COMMAND_FLOW_JOIN_LEDGER_{STAMP}.jsonl"
BUCKET_CONTROL_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_ROUTE_C_COMMAND_FLOW_BUCKET_CONTROL_LEDGER_{STAMP}.jsonl"
SOURCE_GAP_IMPACT_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_ROUTE_C_COMMAND_FLOW_SOURCE_GAP_IMPACT_LEDGER_{STAMP}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_ROUTE_C_COMMAND_FLOW_QUESTION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"SIERRA_DEPTH_ROUTE_C_COMMAND_FLOW_CONTROL_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Sierra .depth command-flow proxy controls joined to Route C/Sierra descriptors only; "
    "full ladder reconstruction not computed; no strategy validation, trade outcome, "
    "R/PnL, expectancy, live-readiness, or promotion"
)

FULL_LADDER_STATUS = "NOT_COMPUTED_INTERACTIVE_RUNTIME_LIMIT_WINDOW_COMMAND_PROXY_ONLY"

CONTROL_FAMILIES = [
    (
        "feature_bucket_all_local",
        ("feature_bucket",),
        (),
    ),
    (
        "feature_bucket_by_request_family",
        ("feature_bucket", "request_family"),
        ("request_family",),
    ),
    (
        "feature_bucket_by_request_family_source_symbol",
        ("feature_bucket", "request_family", "source_symbol"),
        ("request_family", "source_symbol"),
    ),
    (
        "feature_bucket_by_request_family_proxy_relation",
        ("feature_bucket", "request_family", "proxy_relation"),
        ("request_family", "proxy_relation"),
    ),
    (
        "feature_bucket_by_request_family_route_c_queue",
        ("feature_bucket", "request_family", "route_c_queue_id"),
        ("request_family", "route_c_queue_id"),
    ),
    (
        "feature_bucket_by_request_family_route_c_queue_source_symbol",
        ("feature_bucket", "request_family", "route_c_queue_id", "source_symbol"),
        ("request_family", "route_c_queue_id", "source_symbol"),
    ),
    (
        "event15_imbalance_sign_by_request_family_route_c_queue",
        ("event15_imbalance_sign", "request_family", "route_c_queue_id"),
        ("request_family", "route_c_queue_id"),
    ),
]


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def relative(path: Path) -> str:
    return str(path.relative_to(REPO)).replace("\\", "/")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")


def safe_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(out) or math.isinf(out):
        return None
    return out


def bool_value(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    return None


def mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def share(values: list[bool]) -> float | None:
    return sum(1 for value in values if value) / len(values) if values else None


def hhi(values: list[str]) -> float | None:
    if not values:
        return None
    counts = Counter(values)
    total = len(values)
    return sum((count / total) ** 2 for count in counts.values())


def counter_dict(values: list[Any]) -> dict[str, int]:
    return dict(sorted(Counter(str(value) for value in values).items()))


def delta(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return left - right


def compact_command_counts(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    out: dict[str, int] = {}
    for key, raw in value.items():
        number = safe_float(raw)
        if number is not None:
            out[str(key)] = int(number)
    return dict(sorted(out.items()))


def descriptor_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    route_alignment: list[bool] = []
    sierra_delta_alignment: list[bool] = []
    sierra_price_alignment: list[bool] = []
    route_abs: list[float] = []
    route_per_range: list[float] = []
    sierra_abs: list[float] = []
    sierra_per_range: list[float] = []
    event15_bid_share: list[float] = []
    event15_qty_delta: list[float] = []
    event15_command_count: list[float] = []
    pre60_bid_share: list[float] = []
    pre60_qty_delta: list[float] = []
    clear_seen: list[bool] = []
    no_prior_clear_rows = 0
    for row in rows:
        if (value := bool_value(row.get("route_c_delta_aligned_with_future"))) is not None:
            route_alignment.append(value)
        if (value := bool_value(row.get("sierra_future_follows_delta_sign"))) is not None:
            sierra_delta_alignment.append(value)
        if (value := bool_value(row.get("sierra_future_follows_price_sign"))) is not None:
            sierra_price_alignment.append(value)
        for key, target in [
            ("route_c_future_abs_change", route_abs),
            ("route_c_future_change_per_current_range", route_per_range),
            ("sierra_abs_future_change", sierra_abs),
            ("sierra_future_change_per_current_range", sierra_per_range),
            ("event15_depth_bid_quantity_share", event15_bid_share),
            ("event15_depth_bid_minus_ask_quantity_sum", event15_qty_delta),
            ("event15_depth_command_record_count", event15_command_count),
            ("pre60_depth_bid_quantity_share", pre60_bid_share),
            ("pre60_depth_bid_minus_ask_quantity_sum", pre60_qty_delta),
        ]:
            number = safe_float(row.get(key))
            if number is not None:
                target.append(number)
        if (value := bool_value(row.get("clear_book_seen_at_or_before_window_start"))) is not None:
            clear_seen.append(value)
            if not value:
                no_prior_clear_rows += 1
    row_count = len(rows)
    return {
        "n": row_count,
        "request_family_counts": counter_dict([row.get("request_family") for row in rows]),
        "feature_bucket_counts": counter_dict([row.get("feature_bucket") for row in rows]),
        "source_symbol_counts": counter_dict([row.get("source_symbol") for row in rows]),
        "source_date_count": len({str(row.get("source_date")) for row in rows if row.get("source_date")}),
        "source_date_hhi": hhi([str(row.get("source_date")) for row in rows if row.get("source_date")]),
        "route_c_queue_count": len({str(row.get("route_c_queue_id")) for row in rows if row.get("route_c_queue_id")}),
        "replay_count": len({str(row.get("replay_id")) for row in rows if row.get("replay_id")}),
        "event15_imbalance_sign_counts": counter_dict([row.get("event15_imbalance_sign") for row in rows]),
        "proxy_relation_counts": counter_dict([row.get("proxy_relation") for row in rows]),
        "route_c_delta_alignment_descriptor_share": share(route_alignment),
        "route_c_delta_alignment_descriptor_n": len(route_alignment),
        "sierra_delta_alignment_descriptor_share": share(sierra_delta_alignment),
        "sierra_delta_alignment_descriptor_n": len(sierra_delta_alignment),
        "sierra_price_alignment_descriptor_share": share(sierra_price_alignment),
        "sierra_price_alignment_descriptor_n": len(sierra_price_alignment),
        "mean_route_c_abs_future_change_descriptor": mean(route_abs),
        "mean_route_c_future_change_per_current_range_descriptor": mean(route_per_range),
        "mean_sierra_abs_future_change_descriptor": mean(sierra_abs),
        "mean_sierra_future_change_per_current_range_descriptor": mean(sierra_per_range),
        "mean_event15_depth_bid_quantity_share": mean(event15_bid_share),
        "mean_event15_depth_bid_minus_ask_quantity_sum": mean(event15_qty_delta),
        "mean_event15_depth_command_record_count": mean(event15_command_count),
        "mean_pre60_depth_bid_quantity_share": mean(pre60_bid_share),
        "mean_pre60_depth_bid_minus_ask_quantity_sum": mean(pre60_qty_delta),
        "prior_clear_seen_share": share(clear_seen),
        "no_prior_clear_rows": no_prior_clear_rows,
        "no_prior_clear_share": no_prior_clear_rows / row_count if row_count else None,
        "full_ladder_reconstruction_status": FULL_LADDER_STATUS,
    }


def control_basis(rows: list[dict[str, Any]], keys: tuple[str, ...]) -> dict[tuple[Any, ...], list[dict[str, Any]]]:
    out: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        out[tuple(row.get(key) for key in keys)].append(row)
    return out


def classify_control(group_stats: dict[str, Any], denom_stats: dict[str, Any], source_gap_share: float | None) -> str:
    if group_stats["n"] < 20:
        return "UNDERPOWERED_DEPTH_COMMAND_GROUP_N_LT_20"
    if source_gap_share is not None and source_gap_share >= 0.80:
        return "SOURCE_GAP_DOMINATES_CONTEXT"
    if group_stats.get("no_prior_clear_share") is not None and group_stats["no_prior_clear_share"] >= 0.50:
        return "NO_PRIOR_CLEAR_REPLAY_CAUTION_DOMINATES"
    route_delta = delta(
        group_stats.get("route_c_delta_alignment_descriptor_share"),
        denom_stats.get("route_c_delta_alignment_descriptor_share"),
    )
    sierra_delta = delta(
        group_stats.get("sierra_delta_alignment_descriptor_share"),
        denom_stats.get("sierra_delta_alignment_descriptor_share"),
    )
    usable = [value for value in [route_delta, sierra_delta] if value is not None]
    if not usable:
        return "NO_DIRECTIONAL_DESCRIPTOR_AVAILABLE"
    strongest = max(usable, key=abs)
    if strongest >= 0.10:
        return "COMMAND_BUCKET_ALIGNMENT_ABOVE_DENOMINATOR_DESCRIPTIVE"
    if strongest <= -0.10:
        return "COMMAND_BUCKET_BELOW_DENOMINATOR_AVOID_OR_WEAKENING_DESCRIPTOR"
    if abs(strongest) <= 0.05:
        return "COMMAND_BUCKET_NEAR_DENOMINATOR_GENERIC_CONTEXT"
    return "COMMAND_BUCKET_MIXED_SMALL_DESCRIPTOR_DIFFERENCE"


def source_gap_impact_bucket(total: int, local: int, missing: int) -> str:
    if total == 0:
        return "NO_REQUEST_ROWS_FOR_CONTEXT"
    if local == 0 and missing > 0:
        return "EXACT_SOURCE_DATE_DEPTH_GAP_NO_LOCAL_COMMAND_FLOW"
    if missing == 0 and local > 0:
        return "LOCAL_DEPTH_COMPLETE_FOR_CONTEXT"
    if missing > local:
        return "DEPTH_GAP_DOMINATES_CONTEXT"
    if local > 0 and missing > 0:
        return "MIXED_LOCAL_DEPTH_AND_SOURCE_GAP_CONTEXT"
    return "UNCLASSIFIED_DEPTH_SOURCE_GAP_IMPACT"


def next_action_for_gap(bucket: str) -> str:
    if bucket == "EXACT_SOURCE_DATE_DEPTH_GAP_NO_LOCAL_COMMAND_FLOW":
        return "search alternate owned Sierra depth roots or preserve exact source-date capture requirement before depth interpretation"
    if bucket == "DEPTH_GAP_DOMINATES_CONTEXT":
        return "treat command-flow control as source-limited; split local rows from gap rows before any route implication"
    if bucket == "MIXED_LOCAL_DEPTH_AND_SOURCE_GAP_CONTEXT":
        return "use local command-flow rows as partial descriptors and preserve missing rows as source-gap blockers"
    if bucket == "LOCAL_DEPTH_COMPLETE_FOR_CONTEXT":
        return "eligible for same-source command-flow descriptor controls only, still no promotion"
    return "manual source-gap impact review required"


def command_bucket_next_action(bucket: str) -> str:
    if bucket == "COMMAND_BUCKET_ALIGNMENT_ABOVE_DENOMINATOR_DESCRIPTIVE":
        return "deepen with same-date neighbor windows and source-symbol intraday offset controls before any candidate rule"
    if bucket == "COMMAND_BUCKET_BELOW_DENOMINATOR_AVOID_OR_WEAKENING_DESCRIPTOR":
        return "test as avoid/filter intelligence against same-source neighbors, not as an entry edge"
    if bucket == "NO_PRIOR_CLEAR_REPLAY_CAUTION_DOMINATES":
        return "repair ladder reconstruction or isolate clean prior-clear rows before using the descriptor"
    if bucket == "SOURCE_GAP_DOMINATES_CONTEXT":
        return "repair/source-capture missing depth dates before interpreting the group"
    if bucket == "UNDERPOWERED_DEPTH_COMMAND_GROUP_N_LT_20":
        return "aggregate to a broader non-arbitrary family or acquire more same-source rows"
    if bucket == "COMMAND_BUCKET_NEAR_DENOMINATOR_GENERIC_CONTEXT":
        return "preserve as generic context/control evidence; do not promote as unique signal"
    return "split by request family, source date, and Route C residual family for the next same-resource packet"


def compact_cooccurrence(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if not row:
        return None
    observed = row.get("observed_cooccurrence") or {}
    intraday = row.get("intraday_shift_within15_distribution") or {}
    date_rotation = row.get("date_rotation_within15_distribution") or {}
    return {
        "cooccurrence_control_bucket": row.get("cooccurrence_control_bucket"),
        "event_replay_bucket": row.get("event_replay_bucket"),
        "same_date_share": observed.get("same_date_share"),
        "within_15m_share": observed.get("within_15m_share"),
        "intraday_observed_minus_control_max": intraday.get("observed_minus_control_max"),
        "date_observed_minus_control_max": date_rotation.get("observed_minus_control_max"),
    }


def compact_residual(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if not row:
        return None
    return {
        "route_c_mechanism_family": row.get("route_c_mechanism_family"),
        "placebo_bucket": row.get("placebo_bucket"),
        "residual_transfer_class": row.get("residual_transfer_class"),
        "full_control_bucket": row.get("full_control_bucket"),
        "movement_status": row.get("movement_status"),
        "same_session_horizon_transfer_pattern": row.get("same_session_horizon_transfer_pattern"),
        "same_horizon_session_transfer_pattern": row.get("same_horizon_session_transfer_pattern"),
    }


def build_join_rows(
    requests: list[dict[str, Any]],
    features_by_request: dict[str, dict[str, Any]],
    cooccurrence_by_replay: dict[str, dict[str, Any]],
    date_regime_by_key: dict[tuple[str, str], dict[str, Any]],
    residual_by_queue: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for request in requests:
        request_id = str(request["request_id"])
        feature = features_by_request.get(request_id)
        residual = residual_by_queue.get(str(request.get("route_c_queue_id")))
        date_key = (str(request.get("replay_id")), str(request.get("source_date")))
        joined = {
            "route_id": ROUTE_ID,
            "request_id": request_id,
            "request_family": request.get("request_family"),
            "request_status": request.get("request_status"),
            "depth_join_status": "LOCAL_DEPTH_FEATURE_JOINED" if feature else "NO_LOCAL_DEPTH_FEATURE_FOR_REQUEST",
            "feature_available": feature is not None,
            "replay_id": request.get("replay_id"),
            "route_c_queue_id": request.get("route_c_queue_id"),
            "route_c_symbol": request.get("route_c_symbol"),
            "route_c_primitive_flag": request.get("route_c_primitive_flag"),
            "sierra_primitive_flag": request.get("sierra_primitive_flag"),
            "horizon_id": request.get("horizon_id"),
            "source_symbol": request.get("source_symbol"),
            "source_proxy_family": request.get("source_proxy_family"),
            "proxy_relation": request.get("proxy_relation"),
            "source_date": request.get("source_date"),
            "bar_start_utc": request.get("bar_start_utc"),
            "canonical_m15_close_utc": request.get("canonical_m15_close_utc"),
            "depth_file_exists": request.get("depth_file_exists"),
            "depth_path": request.get("depth_path"),
            "within_exact_bar": request.get("within_exact_bar"),
            "within_15m": request.get("within_15m"),
            "within_60m": request.get("within_60m"),
            "route_c_delta_aligned_with_future": request.get("route_c_delta_aligned_with_future"),
            "route_c_future_change_per_current_range": request.get("route_c_future_change_per_current_range"),
            "route_c_future_abs_change": request.get("route_c_future_abs_change"),
            "sierra_future_follows_delta_sign": request.get("sierra_future_follows_delta_sign"),
            "sierra_future_follows_price_sign": request.get("sierra_future_follows_price_sign"),
            "sierra_future_change_per_current_range": request.get("sierra_future_change_per_current_range"),
            "sierra_abs_future_change": request.get("sierra_abs_future_change"),
            "cooccurrence_context": compact_cooccurrence(cooccurrence_by_replay.get(str(request.get("replay_id")))),
            "date_regime_bucket": (date_regime_by_key.get(date_key) or {}).get("date_regime_bucket"),
            "route_c_residual_context": compact_residual(residual),
            "full_ladder_reconstruction_status": FULL_LADDER_STATUS,
            "evidence_boundary": EVIDENCE_BOUNDARY,
            "safe_flags": SAFE_FLAGS,
        }
        if feature:
            joined.update(
                {
                    "feature_bucket": feature.get("feature_bucket"),
                    "event15_imbalance_sign": feature.get("event15_imbalance_sign"),
                    "event15_depth_command_record_count": feature.get("event15_depth_command_record_count"),
                    "event15_depth_bid_quantity_share": feature.get("event15_depth_bid_quantity_share"),
                    "event15_depth_bid_minus_ask_quantity_sum": feature.get("event15_depth_bid_minus_ask_quantity_sum"),
                    "event15_depth_command_counts": compact_command_counts(feature.get("event15_depth_command_counts")),
                    "pre60_depth_command_record_count": feature.get("pre60_depth_command_record_count"),
                    "pre60_depth_bid_quantity_share": feature.get("pre60_depth_bid_quantity_share"),
                    "pre60_depth_bid_minus_ask_quantity_sum": feature.get("pre60_depth_bid_minus_ask_quantity_sum"),
                    "pre60_depth_command_counts": compact_command_counts(feature.get("pre60_depth_command_counts")),
                    "clear_book_seen_at_or_before_window_start": feature.get("clear_book_seen_at_or_before_window_start"),
                    "replay_start_reason": feature.get("replay_start_reason"),
                    "sample_method": feature.get("sample_method"),
                }
            )
        rows.append(joined)
    return rows


def build_source_gap_impact_rows(
    requests: list[dict[str, Any]],
    features_by_request: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], Counter[str], dict[tuple[Any, ...], float]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in requests:
        key = (
            row.get("replay_id"),
            row.get("request_family"),
            row.get("route_c_queue_id"),
            row.get("route_c_symbol"),
            row.get("route_c_primitive_flag"),
            row.get("sierra_primitive_flag"),
            row.get("horizon_id"),
            row.get("source_symbol"),
            row.get("source_date"),
        )
        grouped[key].append(row)
    rows: list[dict[str, Any]] = []
    bucket_counts: Counter[str] = Counter()
    gap_share_by_broad_key: dict[tuple[Any, ...], float] = {}
    for index, (key, group) in enumerate(sorted(grouped.items(), key=lambda item: tuple(str(x) for x in item[0])), 1):
        local = [row for row in group if str(row.get("request_id")) in features_by_request]
        missing = [row for row in group if not row.get("depth_file_exists")]
        bucket = source_gap_impact_bucket(len(group), len(local), len(missing))
        bucket_counts[bucket] += 1
        feature_buckets = Counter(str(features_by_request[str(row["request_id"])].get("feature_bucket")) for row in local)
        gap_share = len(missing) / len(group) if group else None
        broad_key = (key[1], key[2], key[7])
        if gap_share is not None:
            prior = gap_share_by_broad_key.get(broad_key)
            gap_share_by_broad_key[broad_key] = max(prior, gap_share) if prior is not None else gap_share
        rows.append(
            {
                "route_id": ROUTE_ID,
                "source_gap_impact_id": f"SIERRA-DEPTH-CF-GAP-{index:05d}",
                "replay_id": key[0],
                "request_family": key[1],
                "route_c_queue_id": key[2],
                "route_c_symbol": key[3],
                "route_c_primitive_flag": key[4],
                "sierra_primitive_flag": key[5],
                "horizon_id": key[6],
                "source_symbol": key[7],
                "source_date": key[8],
                "request_rows": len(group),
                "local_depth_feature_rows": len(local),
                "missing_depth_file_rows": len(missing),
                "source_gap_share": gap_share,
                "request_status_counts": counter_dict([row.get("request_status") for row in group]),
                "feature_bucket_counts": dict(sorted(feature_buckets.items())),
                "source_gap_impact_bucket": bucket,
                "next_same_resource_action": next_action_for_gap(bucket),
                "full_ladder_reconstruction_status": FULL_LADDER_STATUS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    return rows, bucket_counts, gap_share_by_broad_key


def build_bucket_control_rows(
    feature_rows: list[dict[str, Any]],
    source_gap_share_by_broad_key: dict[tuple[Any, ...], float],
) -> tuple[list[dict[str, Any]], Counter[str]]:
    rows: list[dict[str, Any]] = []
    bucket_counts: Counter[str] = Counter()
    group_index = 0
    for family, group_keys, denom_keys in CONTROL_FAMILIES:
        group_map = control_basis(feature_rows, group_keys)
        denom_map = control_basis(feature_rows, denom_keys)
        for group_key, group in sorted(group_map.items(), key=lambda item: tuple(str(x) for x in item[0])):
            group_index += 1
            denom_key = tuple(group_key[group_keys.index(key)] for key in denom_keys)
            denom = denom_map.get(denom_key, [])
            stats = descriptor_stats(group)
            denom_stats = descriptor_stats(denom)
            sample = group[0]
            broad_gap_key = (
                sample.get("request_family"),
                sample.get("route_c_queue_id"),
                sample.get("source_symbol"),
            )
            source_gap_share = source_gap_share_by_broad_key.get(broad_gap_key)
            bucket = classify_control(stats, denom_stats, source_gap_share)
            bucket_counts[bucket] += 1
            rows.append(
                {
                    "route_id": ROUTE_ID,
                    "command_flow_control_id": f"SIERRA-DEPTH-CF-CONTROL-{group_index:05d}",
                    "control_family": family,
                    "group_keys": list(group_keys),
                    "group_values": {key: value for key, value in zip(group_keys, group_key, strict=True)},
                    "denominator_keys": list(denom_keys),
                    "denominator_values": {key: value for key, value in zip(denom_keys, denom_key, strict=True)},
                    "group_descriptor_stats": stats,
                    "denominator_descriptor_stats": denom_stats,
                    "descriptor_deltas": {
                        "route_c_delta_alignment_descriptor_share_minus_denominator": delta(
                            stats.get("route_c_delta_alignment_descriptor_share"),
                            denom_stats.get("route_c_delta_alignment_descriptor_share"),
                        ),
                        "sierra_delta_alignment_descriptor_share_minus_denominator": delta(
                            stats.get("sierra_delta_alignment_descriptor_share"),
                            denom_stats.get("sierra_delta_alignment_descriptor_share"),
                        ),
                        "event15_bid_quantity_share_minus_denominator": delta(
                            stats.get("mean_event15_depth_bid_quantity_share"),
                            denom_stats.get("mean_event15_depth_bid_quantity_share"),
                        ),
                        "event15_bid_minus_ask_quantity_sum_minus_denominator": delta(
                            stats.get("mean_event15_depth_bid_minus_ask_quantity_sum"),
                            denom_stats.get("mean_event15_depth_bid_minus_ask_quantity_sum"),
                        ),
                    },
                    "context_source_gap_share": source_gap_share,
                    "command_flow_control_bucket": bucket,
                    "next_same_resource_action": command_bucket_next_action(bucket),
                    "full_ladder_reconstruction_status": FULL_LADDER_STATUS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "safe_flags": SAFE_FLAGS,
                }
            )
    return rows, bucket_counts


def build_questions(
    command_bucket_counts: Counter[str],
    gap_bucket_counts: Counter[str],
    counts: dict[str, int],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    question_index = 0
    for bucket, count in sorted(command_bucket_counts.items()):
        question_index += 1
        rows.append(
            {
                "question_id": f"SIERRA-DEPTH-CF-Q-{question_index:03d}",
                "question_family": "command_flow_control_bucket",
                "bucket": bucket,
                "row_count": count,
                "question": f"What same-source neighbor, intraday-offset, or avoid-filter test follows for all {count} command-flow control rows in {bucket}?",
                "next_same_resource_action": command_bucket_next_action(bucket),
                "counts_context": counts,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
            }
        )
    for bucket, count in sorted(gap_bucket_counts.items()):
        question_index += 1
        rows.append(
            {
                "question_id": f"SIERRA-DEPTH-CF-Q-{question_index:03d}",
                "question_family": "source_gap_impact_bucket",
                "bucket": bucket,
                "row_count": count,
                "question": f"Which exact source repair, alternate-root search, or forward-capture route follows for all {count} source-gap impact rows in {bucket}?",
                "next_same_resource_action": next_action_for_gap(bucket),
                "counts_context": counts,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
            }
        )
    question_index += 1
    rows.append(
        {
            "question_id": f"SIERRA-DEPTH-CF-Q-{question_index:03d}",
            "question_family": "full_ladder_blocker",
            "bucket": FULL_LADDER_STATUS,
            "row_count": counts["local_depth_feature_rows"],
            "question": "Can full ladder reconstruction be made feasible by per-file state checkpoints, narrower event slices, or compiled/vectorized replay?",
            "next_same_resource_action": "prototype a lower-memory depth-ladder snapshotter or prove runtime impossibility under current interactive constraints",
            "counts_context": counts,
            "safe_flags": SAFE_FLAGS,
            "evidence_boundary": EVIDENCE_BOUNDARY,
        }
    )
    return rows


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "sierra_depth_route_c_command_flow_control_builder", "created"),
        (RESULT_PATH, "sierra_depth_route_c_command_flow_control_result", "created"),
        (JOIN_LEDGER, "sierra_depth_route_c_command_flow_join_ledger", "created"),
        (BUCKET_CONTROL_LEDGER, "sierra_depth_route_c_command_flow_bucket_control_ledger", "created"),
        (SOURCE_GAP_IMPACT_LEDGER, "sierra_depth_route_c_command_flow_source_gap_impact_ledger", "created"),
        (QUESTION_LEDGER, "sierra_depth_route_c_command_flow_question_ledger", "created"),
        (SUMMARY_PATH, "sierra_depth_route_c_command_flow_control_summary", "created"),
    ]
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    known = {relative(path) for path, _, _ in artifacts}
    manifest["artifacts"] = [item for item in manifest["artifacts"] if item.get("path") not in known]
    for path, artifact_type, status in artifacts:
        manifest["artifacts"].append({"path": relative(path), "type": artifact_type, "status": status})
    manifest["last_updated_utc"] = generated_utc
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def append_sprint_ledger(generated_utc: str, counts: dict[str, int], bucket_counts: dict[str, dict[str, int]]) -> None:
    event = {
        "ts_utc": generated_utc,
        "event_type": "sierra_depth_route_c_command_flow_controls",
        "status": "done",
        "route": "sierra_depth_source_gap_repair",
        "details": "Joined every Sierra .depth event-window request to Route C/Sierra context and built command-flow proxy descriptor controls over all locally replayed depth windows.",
        "counts": counts,
        "bucket_counts": bucket_counts,
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(JOIN_LEDGER),
            relative(BUCKET_CONTROL_LEDGER),
            relative(SOURCE_GAP_IMPACT_LEDGER),
            relative(QUESTION_LEDGER),
            relative(SUMMARY_PATH),
        ],
        "commands": [f"py -3 {relative(Path(__file__).resolve())}"],
        "safe_flags": SAFE_FLAGS,
    }
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=False) + "\n")


def write_summary(
    generated_utc: str,
    counts: dict[str, int],
    command_bucket_counts: Counter[str],
    gap_bucket_counts: Counter[str],
) -> None:
    lines = [
        "# Sierra Depth Route C Command-Flow Controls",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: Sierra `.depth` command-flow proxy descriptor controls joined to Route C/Sierra context. No strategy validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.",
        "",
        f"Full ladder reconstruction status: `{FULL_LADDER_STATUS}`",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Command-Flow Control Buckets", ""])
    for key, value in sorted(command_bucket_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Source-Gap Impact Buckets", ""])
    for key, value in sorted(gap_bucket_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Interpretation Boundary",
            "",
            "- The join ledger preserves every depth request row, including all missing source-date gaps.",
            "- Bucket controls are descriptor comparisons against same-family denominators, not trade validation.",
            "- Source gaps and no-prior-clear replay rows remain active blockers for any stronger interpretation.",
            "- Full ladder depth10/wall/thinness features remain not computed in this packet.",
            "",
            "## Next Same-Resource Work",
            "",
            "- Run same-source neighbor and intraday-offset controls for command buckets that differ from denominators.",
            "- Search alternate owned Sierra depth roots for exact missing source-date gaps.",
            "- Prototype a feasible ladder snapshotter or prove the remaining ladder route impossible under current resources.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = utc_now()
    requests = read_jsonl(REQUEST_LEDGER)
    feature_rows = read_jsonl(FEATURE_LEDGER)
    features_by_request = {str(row["request_id"]): row for row in feature_rows}
    cooccurrence_by_replay = {str(row["replay_id"]): row for row in read_jsonl(COOCCURRENCE_LEDGER)}
    date_regime_by_key = {
        (str(row["replay_id"]), str(row["event_date"])): row
        for row in read_jsonl(DATE_REGIME_LEDGER)
    }
    residual_by_queue = {
        str(row["queue_id"]): row
        for row in read_jsonl(RESIDUAL_FAMILY_LEDGER)
    }
    source_gap_rows = read_jsonl(SOURCE_GAP_LEDGER)

    join_rows = build_join_rows(
        requests,
        features_by_request,
        cooccurrence_by_replay,
        date_regime_by_key,
        residual_by_queue,
    )
    gap_impact_rows, gap_bucket_counts, gap_share_by_broad_key = build_source_gap_impact_rows(
        requests,
        features_by_request,
    )
    command_control_rows, command_bucket_counts = build_bucket_control_rows(
        feature_rows,
        gap_share_by_broad_key,
    )
    counts = {
        "request_rows": len(requests),
        "join_rows": len(join_rows),
        "local_depth_feature_rows": len(feature_rows),
        "missing_depth_request_rows": sum(1 for row in requests if not row.get("depth_file_exists")),
        "source_gap_rows_from_prior_packet": len(source_gap_rows),
        "source_gap_impact_rows": len(gap_impact_rows),
        "command_flow_control_rows": len(command_control_rows),
        "command_flow_control_family_count": len(CONTROL_FAMILIES),
        "question_rows": 0,
    }
    question_rows = build_questions(command_bucket_counts, gap_bucket_counts, counts)
    counts["question_rows"] = len(question_rows)

    write_jsonl(JOIN_LEDGER, join_rows)
    write_jsonl(BUCKET_CONTROL_LEDGER, command_control_rows)
    write_jsonl(SOURCE_GAP_IMPACT_LEDGER, gap_impact_rows)
    write_jsonl(QUESTION_LEDGER, question_rows)

    bucket_counts = {
        "command_flow_control_bucket_counts": dict(sorted(command_bucket_counts.items())),
        "source_gap_impact_bucket_counts": dict(sorted(gap_bucket_counts.items())),
    }
    result = {
        "schema": "sierra_depth_route_c_command_flow_control_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "SIERRA_DEPTH_ROUTE_C_COMMAND_FLOW_CONTROL_DIAGNOSTIC_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "full_ladder_reconstruction_status": FULL_LADDER_STATUS,
        "counts": counts,
        **bucket_counts,
        "control_families": [
            {"control_family": family, "group_keys": list(group_keys), "denominator_keys": list(denom_keys)}
            for family, group_keys, denom_keys in CONTROL_FAMILIES
        ],
        "next_same_resource_work": [
            "same-source neighbor and intraday-offset controls for command buckets",
            "alternate-root search for exact missing depth source-date gaps",
            "feasible ladder snapshotter prototype or exact impossibility proof",
        ],
        "not_completion": "This command-flow packet deepens Route C/Sierra depth diagnostics but does not complete the 60-hour objective.",
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, bucket_counts)
    write_summary(generated_utc, counts, command_bucket_counts, gap_bucket_counts)
    print(
        json.dumps(
            {
                "ok": True,
                "counts": counts,
                **bucket_counts,
                "result": str(RESULT_PATH),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
