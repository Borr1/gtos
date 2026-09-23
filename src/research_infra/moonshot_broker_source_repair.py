"""Broker/source repair helpers for moonshot numeric rows.

This module consumes the branch-local numeric result rows plus the source repair
queue and performs the next same-resource repair step:

* join repair rows back to their numeric rows;
* attach branch/source context when a matched branch id exists;
* attempt direct exact-R joins against local broker/account/trade sources;
* emit a concrete repair decision without inventing exact broker geometry.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from statistics import mean
from typing import Any, Iterable


BROKER_SOURCE_REPAIR_SURFACE = "src/research_infra/moonshot_broker_source_repair.py"

DIRECT_IDENTIFIER_FIELDS = (
    "trade_id",
    "trade_record_trade_id",
    "candidate_id",
    "fill_id",
    "ticket",
    "pending_ticket",
    "trade_state_ticket",
    "mt5_deal_id",
    "mt5_order_id",
    "limit_intent_trade_id",
)


def to_float(value: Any) -> float | None:
    if isinstance(value, bool) or value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def normalize_session(value: Any) -> str | None:
    if value is None or value == "":
        return None
    text = str(value).lower()
    if text in {"tokyo", "tokyo_kz"}:
        return "tokyo_kz"
    if text in {"london", "london_core"}:
        return "london_core"
    if text in {"ny", "new_york", "ny_core"}:
        return "ny_core"
    if text in {"off_core", "off_core_session", "off_kz"}:
        return "off_core_session"
    return str(value)


def direct_identifiers(row: dict[str, Any] | None) -> dict[str, str]:
    if not row:
        return {}
    output: dict[str, str] = {}
    for field in DIRECT_IDENTIFIER_FIELDS:
        value = row.get(field)
        if value not in (None, "", [], {}):
            output[field] = str(value)
    source_links = row.get("source_links")
    if isinstance(source_links, dict):
        for field in ("mt5_export_deal_id", "mt5_export_order_id", "broker_actual_r_audit_row_key"):
            value = source_links.get(field)
            if value not in (None, "", [], {}):
                output[f"source_links.{field}"] = str(value)
    return output


def best_actual_r(row: dict[str, Any]) -> tuple[float | None, str | None]:
    for field in ("broker_actual_r", "actual_r", "result_r"):
        value = to_float(row.get(field))
        if value is not None:
            return value, field
    return None, None


def source_observation(source_name: str, row: dict[str, Any], index: int, source_path: str | None = None) -> dict[str, Any]:
    actual_r, actual_r_field = best_actual_r(row)
    claim_allowed = row.get("actual_r_claim_allowed")
    usable_actual_r = actual_r if actual_r is not None and claim_allowed is not False else None
    session = normalize_session(row.get("route_session") or row.get("session") or row.get("kill_zone"))
    identifiers = direct_identifiers(row)
    entry = to_float(row.get("entry_price") or row.get("executed_entry_price"))
    stop = to_float(row.get("stop_loss") or row.get("executed_stop_price"))
    target = to_float(row.get("take_profit_1") or row.get("executed_target_price"))
    return {
        "broker_source_observation_row_id": f"OHLC-GTOS-BROKER-SOURCE-OBS-{index:06d}",
        "broker_source_repair_surface": BROKER_SOURCE_REPAIR_SURFACE,
        "source_name": source_name,
        "source_path": source_path,
        "source_row_hash": stable_hash(row),
        "source_row_key": row.get("row_key"),
        "symbol": row.get("symbol") or row.get("broker_symbol"),
        "route_session": session,
        "candidate_id": row.get("candidate_id"),
        "trade_id": row.get("trade_id") or row.get("trade_record_trade_id"),
        "fill_id": row.get("fill_id"),
        "ticket": row.get("ticket") or row.get("pending_ticket") or row.get("trade_state_ticket"),
        "mt5_deal_id": row.get("mt5_deal_id"),
        "mt5_order_id": row.get("mt5_order_id"),
        "decision_time_utc": row.get("decision_time_utc"),
        "fill_time_utc": row.get("fill_time_utc"),
        "source_ts_utc": row.get("source_ts_utc") or row.get("timestamp_utc") or row.get("created_at_utc"),
        "direct_identifiers": identifiers,
        "direct_identifier_count": len(identifiers),
        "actual_r_value": actual_r,
        "actual_r_field": actual_r_field,
        "actual_r_claim_allowed": claim_allowed,
        "usable_exact_r_value": usable_actual_r,
        "geometry_entry_price": entry,
        "geometry_stop_price": stop,
        "geometry_target_price": target,
        "geometry_available": entry is not None and stop is not None,
        "target_geometry_available": target is not None,
        "source_fill_state": row.get("broker_fill_state") or row.get("fill_no_fill_label") or row.get("final_outcome"),
        "source_schema_version": row.get("schema_version"),
    }


def build_source_index(observations: Iterable[dict[str, Any]]) -> dict[str, Any]:
    by_identifier: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_symbol_session: dict[str, list[dict[str, Any]]] = defaultdict(list)
    observations_list = list(observations)
    for obs in observations_list:
        for field, value in obs.get("direct_identifiers", {}).items():
            by_identifier[f"{field}={value}"].append(obs)
            by_identifier[str(value)].append(obs)
        key = f"symbol={obs.get('symbol') or ''}|route_session={obs.get('route_session') or ''}"
        by_symbol_session[key].append(obs)
    return {
        "broker_source_repair_surface": BROKER_SOURCE_REPAIR_SURFACE,
        "observations": observations_list,
        "by_identifier": dict(by_identifier),
        "by_symbol_session": dict(by_symbol_session),
    }


def numeric_proxy_value(numeric_row: dict[str, Any] | None) -> tuple[float | None, str]:
    if not numeric_row:
        return None, "NUMERIC_ROW_MISSING"
    for field in ("proxy_r_value", "decision_proxy_value", "expectancy_proxy_value", "computed_proxy_score"):
        value = to_float(numeric_row.get(field))
        if value is not None:
            return value, f"NUMERIC_{field}"
    return None, "NUMERIC_PROXY_ABSENT"


def branch_proxy_value(branch_row: dict[str, Any] | None) -> tuple[float | None, str]:
    if not branch_row:
        return None, "BRANCH_SOURCE_ABSENT"
    for field in ("primary_selector_score", "next_layer_composite_score", "proxy_score_delta_vs_actionability"):
        value = to_float(branch_row.get(field))
        if value is not None:
            return value, f"BRANCH_{field}"
    return None, "BRANCH_PROXY_ABSENT"


def repair_identifiers(
    repair_row: dict[str, Any],
    numeric_row: dict[str, Any] | None,
    branch_row: dict[str, Any] | None,
) -> dict[str, str]:
    identifiers: dict[str, str] = {}
    for source in (repair_row, numeric_row, branch_row):
        identifiers.update(direct_identifiers(source))
    return identifiers


def exact_join_from_sources(identifiers: dict[str, str], source_index: dict[str, Any]) -> dict[str, Any]:
    matches: list[dict[str, Any]] = []
    for field, value in identifiers.items():
        for key in (f"{field}={value}", value):
            matches.extend(source_index.get("by_identifier", {}).get(key, []))
    unique: dict[str, dict[str, Any]] = {row["broker_source_observation_row_id"]: row for row in matches}
    exact_matches = [row for row in unique.values() if row.get("usable_exact_r_value") is not None]
    if exact_matches:
        if len(exact_matches) == 1:
            match = exact_matches[0]
            return {
                "exact_broker_join_status": "EXACT_R_JOINED_FROM_DIRECT_LOCAL_BROKER_IDENTIFIER",
                "exact_broker_r_value": match.get("usable_exact_r_value"),
                "exact_broker_join_source_row_id": match.get("broker_source_observation_row_id"),
                "exact_broker_join_source_name": match.get("source_name"),
                "direct_identifier_match_count": len(unique),
                "direct_exact_r_match_count": len(exact_matches),
            }
        values = {row.get("usable_exact_r_value") for row in exact_matches}
        status = "EXACT_R_JOIN_CONFLICTING_DIRECT_LOCAL_BROKER_IDENTIFIERS" if len(values) > 1 else "EXACT_R_JOINED_FROM_MULTIPLE_CONSISTENT_LOCAL_BROKER_IDENTIFIERS"
        return {
            "exact_broker_join_status": status,
            "exact_broker_r_value": exact_matches[0].get("usable_exact_r_value") if len(values) == 1 else None,
            "exact_broker_join_source_row_id": ",".join(row.get("broker_source_observation_row_id", "") for row in exact_matches),
            "exact_broker_join_source_name": ",".join(sorted({str(row.get("source_name")) for row in exact_matches})),
            "direct_identifier_match_count": len(unique),
            "direct_exact_r_match_count": len(exact_matches),
        }
    if identifiers:
        return {
            "exact_broker_join_status": "EXACT_R_NOT_JOINABLE_DIRECT_IDENTIFIERS_HAVE_NO_USABLE_LOCAL_EXACT_R",
            "exact_broker_r_value": None,
            "exact_broker_join_source_row_id": None,
            "exact_broker_join_source_name": None,
            "direct_identifier_match_count": len(unique),
            "direct_exact_r_match_count": 0,
        }
    return {
        "exact_broker_join_status": "EXACT_R_NOT_JOINABLE_NO_DIRECT_TRADE_CANDIDATE_OR_TICKET_IDENTIFIER",
        "exact_broker_r_value": None,
        "exact_broker_join_source_row_id": None,
        "exact_broker_join_source_name": None,
        "direct_identifier_match_count": 0,
        "direct_exact_r_match_count": 0,
    }


def source_coverage_counts(row: dict[str, Any], source_index: dict[str, Any]) -> dict[str, int]:
    key = f"symbol={row.get('symbol') or ''}|route_session={normalize_session(row.get('route_session')) or ''}"
    rows = source_index.get("by_symbol_session", {}).get(key, [])
    return {
        "local_source_symbol_session_rows": len(rows),
        "local_source_symbol_session_exact_r_rows": sum(1 for item in rows if item.get("usable_exact_r_value") is not None),
        "local_source_symbol_session_geometry_rows": sum(1 for item in rows if item.get("geometry_available")),
    }


def hard_repair_decision(exact_value: float | None, proxy_value: float | None, repair_row: dict[str, Any]) -> str:
    if exact_value is not None:
        if exact_value > 0:
            return "IMPLEMENT_DEFAULT_OFF_EXACT_R_RESEARCH_SCORER_WITH_SOURCE_GUARDS"
        if exact_value < 0:
            return "IMPLEMENT_AVOID_OR_FAILURE_FILTER_FROM_EXACT_R"
        return "MERGE_FLAT_EXACT_R_AS_CONTEXT_GUARD"
    queue = str(repair_row.get("repair_queue") or "")
    if proxy_value is not None:
        if proxy_value > 0:
            return "KEEP_SOURCE_REPAIRED_PROXY_AS_DEFAULT_OFF_SCORER_OR_GUARD_INPUT"
        if proxy_value < 0:
            return "KEEP_SOURCE_REPAIRED_NEGATIVE_PROXY_AS_AVOID_OR_REDESIGN_INPUT"
        return "MERGE_SOURCE_REPAIRED_FLAT_PROXY_AS_CONTEXT"
    if "SOURCE_JOIN" in queue:
        return "SOURCE_JOIN_REPAIR_REQUIRES_ORIGINAL_EVENT_GEOMETRY_OR_REPLAY_SOURCE"
    if "BROKER" in queue:
        return "BROKER_GEOMETRY_REPAIR_REQUIRES_DIRECT_TRADE_IDENTIFIER"
    return "REPAIR_PATH_NEEDS_SOURCE_OR_GEOMETRY_RECONSTRUCTION"


def repair_result_row(
    repair_row: dict[str, Any],
    numeric_row: dict[str, Any] | None,
    branch_row: dict[str, Any] | None,
    source_index: dict[str, Any],
    index: int,
) -> dict[str, Any]:
    identifiers = repair_identifiers(repair_row, numeric_row, branch_row)
    exact_join = exact_join_from_sources(identifiers, source_index)
    numeric_proxy, numeric_proxy_source = numeric_proxy_value(numeric_row)
    branch_proxy, branch_proxy_source = branch_proxy_value(branch_row)
    if numeric_proxy is not None:
        repaired_proxy = numeric_proxy
        repaired_proxy_status = "NUMERIC_PROXY_ALREADY_PRESENT"
        repaired_proxy_source = numeric_proxy_source
    elif branch_proxy is not None:
        repaired_proxy = branch_proxy
        repaired_proxy_status = "BRANCH_SOURCE_PROXY_ATTACHED_FROM_MATCHED_BRANCH"
        repaired_proxy_source = branch_proxy_source
    else:
        repaired_proxy = None
        repaired_proxy_status = "NO_PROXY_AVAILABLE_AFTER_CURRENT_SOURCE_REPAIR"
        repaired_proxy_source = "NO_PROXY_SOURCE"
    branch_status = (
        "BRANCH_SOURCE_ATTACHED_FROM_MATCHED_BRANCH_QUEUE"
        if branch_row
        else "NO_MATCHED_BRANCH_SOURCE_FOR_THIS_REPAIR_ROW"
    )
    exact_value = exact_join.get("exact_broker_r_value")
    decision = hard_repair_decision(exact_value, repaired_proxy, repair_row)
    coverage = source_coverage_counts(repair_row, source_index)
    return {
        "broker_source_repair_surface": BROKER_SOURCE_REPAIR_SURFACE,
        "broker_source_repair_result_row_id": f"OHLC-GTOS-BROKER-SOURCE-REPAIR-RESULT-{index:06d}",
        "input_source_repair_queue_row_id": repair_row.get("source_repair_queue_row_id"),
        "input_numeric_result_row_id": repair_row.get("input_numeric_result_row_id"),
        "numeric_row_rejoined": numeric_row is not None,
        "symbol": repair_row.get("symbol"),
        "route_session": repair_row.get("route_session"),
        "horizon_id": repair_row.get("horizon_id"),
        "primitive_flag": repair_row.get("primitive_flag"),
        "source_component": repair_row.get("source_component"),
        "source_row_id": repair_row.get("source_row_id"),
        "matched_branch_queue_id": (numeric_row or {}).get("matched_branch_queue_id"),
        "route_candidate_id": (branch_row or {}).get("route_candidate_id"),
        "branch_source_status": branch_status,
        "repair_queue": repair_row.get("repair_queue"),
        "repair_action": repair_row.get("repair_action"),
        "direct_repair_identifiers": identifiers,
        "direct_repair_identifier_count": len(identifiers),
        **exact_join,
        "source_repaired_proxy_value": repaired_proxy,
        "source_repaired_proxy_status": repaired_proxy_status,
        "source_repaired_proxy_source": repaired_proxy_source,
        "numeric_proxy_value": numeric_proxy,
        "branch_proxy_value": branch_proxy,
        "target_stop_order_class": (numeric_row or {}).get("target_stop_order_class") or (branch_row or {}).get("target_stop_result"),
        "target_stop_status_counts": (numeric_row or {}).get("target_stop_status_counts") or {},
        "cost_stress_status": (numeric_row or {}).get("cost_stress_status"),
        "cost_sensitive_share": (numeric_row or {}).get("cost_sensitive_share"),
        "source_coverage_counts": coverage,
        "hard_repair_decision": decision,
        "exact_missing_field_proof": repair_row.get("exact_missing_field_proof") or [],
        "exact_r_missing_after_repair": exact_value is None,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
        "summary_only_terminal": False,
    }


def string_counter(rows: Iterable[dict[str, Any]], key: str) -> dict[str, int]:
    counter = Counter(str(row.get(key)) for row in rows)
    return {value: int(counter[value]) for value in sorted(counter)}


def expectation_summary_row(
    rows: list[dict[str, Any]],
    group_values: tuple[Any, ...],
    group_fields: tuple[str, ...],
    index: int,
    summary_family: str,
) -> dict[str, Any]:
    exact_values = [row.get("exact_broker_r_value") for row in rows if isinstance(row.get("exact_broker_r_value"), (int, float))]
    proxy_values = [
        row.get("source_repaired_proxy_value")
        for row in rows
        if isinstance(row.get("source_repaired_proxy_value"), (int, float))
    ]
    branch_ids = {row.get("matched_branch_queue_id") for row in rows if row.get("matched_branch_queue_id")}
    duplicate_ratio = round(len(rows) / len(branch_ids), 10) if branch_ids else None
    output = {
        "broker_source_expectancy_summary_row_id": f"OHLC-GTOS-BROKER-SOURCE-EXPECTANCY-{index:05d}",
        "broker_source_repair_surface": BROKER_SOURCE_REPAIR_SURFACE,
        "summary_family": summary_family,
        "row_count": len(rows),
        "unique_branch_queue_count": len(branch_ids),
        "duplicate_inflation_ratio_rows_over_unique_branch": duplicate_ratio,
        "exact_r_value_rows": len(exact_values),
        "exact_r_mean": round(mean(exact_values), 10) if exact_values else None,
        "proxy_r_value_rows": len(proxy_values),
        "proxy_r_mean": round(mean(proxy_values), 10) if proxy_values else None,
        "proxy_r_sum": round(sum(proxy_values), 10) if proxy_values else None,
        "hard_repair_decision_counts": string_counter(rows, "hard_repair_decision"),
        "exact_broker_join_status_counts": string_counter(rows, "exact_broker_join_status"),
        "source_repaired_proxy_status_counts": string_counter(rows, "source_repaired_proxy_status"),
        "target_stop_order_class_counts": string_counter(rows, "target_stop_order_class"),
        "repair_queue_counts": string_counter(rows, "repair_queue"),
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
        "summary_only_terminal": False,
    }
    for field, value in zip(group_fields, group_values):
        output[field] = value
    return output


def implementation_decision_row(
    scope_row: dict[str, Any],
    repair_rows: list[dict[str, Any]],
    event_rows: list[dict[str, Any]],
    index: int,
) -> dict[str, Any]:
    exact_rows = [row for row in repair_rows if row.get("exact_broker_r_value") is not None]
    proxy_rows = [row for row in repair_rows if row.get("source_repaired_proxy_value") is not None]
    positive_proxy = [row for row in proxy_rows if row.get("source_repaired_proxy_value", 0) > 0]
    negative_proxy = [row for row in proxy_rows if row.get("source_repaired_proxy_value", 0) < 0]
    event_scores = [row.get("shadow_score") for row in event_rows if isinstance(row.get("shadow_score"), (int, float))]
    if exact_rows:
        decision = "IMPLEMENT_SCOPE_FROM_EXACT_R_REPAIR_WITH_GUARDS"
    elif negative_proxy and len(negative_proxy) >= len(positive_proxy):
        decision = "IMPLEMENT_SCOPE_AVOID_OR_REDESIGN_FROM_REPAIRED_NEGATIVE_PROXY"
    elif positive_proxy:
        decision = "IMPLEMENT_SCOPE_DEFAULT_OFF_PROXY_SCORER_WITH_SOURCE_REPAIR_GUARDS"
    elif repair_rows:
        decision = "SOURCE_OR_BROKER_GEOMETRY_REPAIR_REMAINS_REQUIRED_FOR_SCOPE"
    else:
        decision = "MERGE_SCOPE_CONTEXT_ONLY_NO_REPAIR_ROWS"
    return {
        "broker_source_implementation_decision_row_id": f"OHLC-GTOS-BROKER-SOURCE-IMPLEMENT-DECISION-{index:05d}",
        "broker_source_repair_surface": BROKER_SOURCE_REPAIR_SURFACE,
        "input_scope_score_decision_row_id": scope_row.get("scope_score_decision_row_id"),
        "symbol": scope_row.get("symbol"),
        "route_session": scope_row.get("route_session"),
        "horizon_id": scope_row.get("horizon_id"),
        "source_component": scope_row.get("source_component"),
        "aggregate_scope_key": scope_row.get("aggregate_scope_key"),
        "scope_event_rows": len(event_rows),
        "scope_repair_rows": len(repair_rows),
        "scope_exact_r_repaired_rows": len(exact_rows),
        "scope_proxy_repaired_rows": len(proxy_rows),
        "scope_positive_repaired_proxy_rows": len(positive_proxy),
        "scope_negative_repaired_proxy_rows": len(negative_proxy),
        "scope_event_score_mean": round(mean(event_scores), 10) if event_scores else None,
        "scope_repaired_proxy_mean": round(
            mean([row["source_repaired_proxy_value"] for row in proxy_rows]), 10
        )
        if proxy_rows
        else None,
        "upstream_scope_shadow_decision": scope_row.get("scope_shadow_decision"),
        "implementation_decision": decision,
        "repair_queue_counts": string_counter(repair_rows, "repair_queue"),
        "hard_repair_decision_counts": string_counter(repair_rows, "hard_repair_decision"),
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
        "summary_only_terminal": False,
    }
