"""Replay-ready candidate records for ultimate convergence matching.

This module normalizes runtime-learning packets and historical/replay candidate
rows into one per-candidate schema. It is observation-only: records can feed
matching, replay, and training, but they do not admit, size, place, manage, or
mutate broker/account/order/deal/position state.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from .runtime_learning_packet import stable_hash


SCHEMA_VERSION = "ultimate_convergence_candidate_replay_record_v1"

RAW_BROKER_KEYS = {
    "account_login",
    "login",
    "password",
    "token",
    "api_key",
    "server",
    "ticket",
    "order_ticket",
    "deal_ticket",
    "position_ticket",
}

RESULT_FIELD_KEYS = {
    "actual_r",
    "broker_actual_r",
    "broker_real_net_r",
    "broker_realized_net_r",
    "close_reason",
    "cost_adjusted_r",
    "delta_v4_minus_be_after_trigger",
    "delta_v4_minus_fixed_1_5r",
    "delta_v4_minus_promoted_router",
    "exact_r",
    "final_r",
    "gross_r",
    "legacy_fixed_1_5r_r",
    "mae_r",
    "mfe_r",
    "missed_result_r",
    "net_r",
    "promoted_router_replay_r",
    "proxy_r",
    "result_r",
    "source_bound_proxy_r",
    "stress_simulated_r",
    "v3_be_after_trigger_r",
    "win_rate",
}

MATCH_INPUT_KEYS = (
    "namespace",
    "event_type",
    "decision_asof_utc",
    "decision_bar_iso",
    "decision_day",
    "symbol",
    "broker_symbol",
    "source_symbol",
    "symbol_family",
    "side",
    "direction",
    "sleeve",
    "cluster",
    "candidate_id",
    "decision_window_id",
    "ultimate_book_intent_id",
    "timeframe",
    "market_timeframe",
    "session_bucket",
    "route_session",
    "horizon_id",
    "framework",
    "origin_family",
    "mechanism_family",
    "source_path_sha256",
    "source_file_sha256",
)


def _first_nonempty(*values: Any) -> Any | None:
    for value in values:
        if value not in (None, ""):
            return value
    return None


def _as_mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _contains_raw_key(value: Any) -> list[str]:
    found: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key).lower() in RAW_BROKER_KEYS:
                found.append(str(key))
            found.extend(_contains_raw_key(item))
    elif isinstance(value, list):
        for item in value:
            found.extend(_contains_raw_key(item))
    return found


def _drop_none(data: Mapping[str, Any]) -> dict[str, Any]:
    return {str(k): v for k, v in data.items() if v not in (None, "")}


def canonical_side(direction: Any = None, side: Any = None) -> str | None:
    raw = _first_nonempty(side, direction)
    if raw is None:
        return None
    text = str(raw).strip().upper()
    if text in {"1", "+1", "LONG", "BUY", "BULL", "UP"}:
        return "LONG"
    if text in {"-1", "SHORT", "SELL", "BEAR", "DOWN"}:
        return "SHORT"
    return text


def canonical_direction(direction: Any = None, side: Any = None) -> int | None:
    resolved = canonical_side(direction, side)
    if resolved == "LONG":
        return 1
    if resolved == "SHORT":
        return -1
    return None


def build_match_inputs(record: Mapping[str, Any]) -> dict[str, Any]:
    inputs = _drop_none({key: record.get(key) for key in MATCH_INPUT_KEYS})
    forbidden = sorted(set(inputs).intersection(RESULT_FIELD_KEYS))
    if forbidden:
        raise ValueError("result_fields_in_match_inputs:" + ",".join(forbidden))
    return inputs


def _record_id(material: Mapping[str, Any]) -> str:
    return stable_hash(
        {
            key: value
            for key, value in material.items()
            if key not in {"record_id", "reservoir_matches", "match_summary"}
        },
        prefix="ultimate_convergence_candidate_replay_record",
    )


def build_replay_record(
    *,
    source_kind: str,
    namespace: str | None = None,
    event_type: str | None = None,
    source_path: str | None = None,
    source_line_no: int | None = None,
    packet: Mapping[str, Any] | None = None,
    unit: Mapping[str, Any] | None = None,
    outcome: Mapping[str, Any] | None = None,
    bridge: Mapping[str, Any] | None = None,
    advisory: Mapping[str, Any] | None = None,
    row: Mapping[str, Any] | None = None,
    sleeve: str | None = None,
    sleeve_members: Iterable[Any] | None = None,
    unit_member_index: int | None = None,
) -> dict[str, Any]:
    packet = _as_mapping(packet)
    unit = _as_mapping(unit)
    outcome = _as_mapping(outcome)
    bridge = _as_mapping(bridge)
    advisory = _as_mapping(advisory)
    row = _as_mapping(row)
    join_keys = _as_mapping(advisory.get("join_keys"))

    direction = _first_nonempty(
        row.get("direction"),
        outcome.get("direction"),
        unit.get("direction"),
        packet.get("direction"),
        join_keys.get("direction"),
        row.get("side"),
    )
    side = canonical_side(direction=direction, side=row.get("side"))
    members = [str(item) for item in (sleeve_members or _as_list(unit.get("sleeve_members"))) if str(item)]
    if sleeve and sleeve not in members:
        members.append(str(sleeve))
    selected_sleeve = _first_nonempty(
        sleeve,
        row.get("sleeve"),
        outcome.get("sleeve"),
        packet.get("sleeve"),
        join_keys.get("sleeve"),
        members[0] if members else None,
    )
    if selected_sleeve and not members:
        members = [str(selected_sleeve)]

    material: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "source_kind": source_kind,
        "source_path": source_path,
        "source_line_no": source_line_no,
        "namespace": _first_nonempty(namespace, packet.get("namespace"), join_keys.get("namespace")),
        "event_type": _first_nonempty(event_type, packet.get("event_type"), join_keys.get("event_type")),
        "created_at_utc": _first_nonempty(row.get("created_at_utc"), packet.get("created_at_utc")),
        "decision_asof_utc": _first_nonempty(
            row.get("decision_asof_utc"),
            row.get("asof_utc"),
            row.get("candidate_time_utc"),
            packet.get("created_at_utc"),
        ),
        "decision_bar_iso": _first_nonempty(
            row.get("decision_bar_iso"),
            row.get("decision_time_utc"),
            row.get("candidate_time_utc"),
            packet.get("decision_bar_iso"),
            outcome.get("decision_bar_iso"),
            join_keys.get("decision_bar_iso"),
        ),
        "decision_day": _first_nonempty(row.get("decision_day"), packet.get("decision_day"), join_keys.get("decision_day")),
        "symbol": _first_nonempty(row.get("symbol"), outcome.get("symbol"), packet.get("symbol"), unit.get("symbol"), join_keys.get("symbol")),
        "broker_symbol": _first_nonempty(row.get("broker_symbol"), packet.get("broker_symbol"), outcome.get("broker_symbol")),
        "source_symbol": _first_nonempty(row.get("source_symbol"), outcome.get("source_symbol"), unit.get("source_symbol")),
        "symbol_family": _first_nonempty(row.get("symbol_family"), outcome.get("symbol_family"), unit.get("symbol_family")),
        "side": side,
        "direction": canonical_direction(direction=direction, side=side),
        "sleeve": str(selected_sleeve) if selected_sleeve is not None else None,
        "sleeve_members": members,
        "unit_member_index": unit_member_index,
        "unit_member_count": len(members) if members else None,
        "cluster": _first_nonempty(row.get("cluster"), outcome.get("cluster"), packet.get("cluster"), unit.get("cluster"), join_keys.get("cluster")),
        "candidate_id": _first_nonempty(row.get("candidate_id"), outcome.get("candidate_id"), packet.get("candidate_id"), unit.get("candidate_id"), join_keys.get("candidate_id")),
        "decision_window_id": _first_nonempty(row.get("decision_window_id"), packet.get("decision_window_id")),
        "ultimate_book_intent_id": _first_nonempty(row.get("ultimate_book_intent_id"), packet.get("ultimate_book_intent_id")),
        "source_event_hash_sha256": _first_nonempty(row.get("source_event_hash_sha256"), packet.get("source_event_hash_sha256")),
        "packet_hash_sha256": _first_nonempty(row.get("packet_hash_sha256"), packet.get("packet_hash_sha256")),
        "timeframe": _first_nonempty(row.get("timeframe"), outcome.get("timeframe"), packet.get("timeframe")),
        "market_timeframe": _first_nonempty(row.get("market_timeframe"), outcome.get("market_timeframe"), unit.get("market_timeframe")),
        "session_bucket": _first_nonempty(row.get("session_bucket"), outcome.get("session_bucket"), unit.get("session_bucket")),
        "route_session": _first_nonempty(row.get("route_session"), outcome.get("route_session"), unit.get("route_session")),
        "horizon_id": _first_nonempty(row.get("horizon_id"), outcome.get("horizon_id"), unit.get("horizon_id")),
        "framework": _first_nonempty(row.get("framework"), outcome.get("framework"), unit.get("framework")),
        "origin_family": _first_nonempty(row.get("origin_family"), outcome.get("origin_family"), unit.get("origin_family")),
        "mechanism_family": _first_nonempty(row.get("mechanism_family"), outcome.get("mechanism_family"), unit.get("mechanism_family")),
        "placement_status": _first_nonempty(row.get("placement_status"), packet.get("placement_status"), outcome.get("placement_status"), join_keys.get("placement_status")),
        "skip_reason": _first_nonempty(row.get("skip_reason"), packet.get("skip_reason"), outcome.get("skip_reason"), join_keys.get("skip_reason")),
        "decision_reason": _first_nonempty(row.get("decision_reason"), packet.get("decision_reason"), outcome.get("decision_reason")),
        "admission_reason": _first_nonempty(row.get("admission_reason"), packet.get("admission_reason"), outcome.get("admission_reason")),
        "n_trades": _first_nonempty(row.get("n_trades"), unit.get("n_trades")),
        "confidence": _first_nonempty(row.get("confidence"), unit.get("confidence")),
        "risk_pct_per_trade": _first_nonempty(row.get("risk_pct_per_trade"), unit.get("risk_pct_per_trade")),
        "unit_risk_pct": _first_nonempty(row.get("unit_risk_pct"), unit.get("unit_risk_pct")),
        "sized": _first_nonempty(row.get("sized"), unit.get("sized")),
        "overlays_applied": _as_list(_first_nonempty(row.get("overlays_applied"), unit.get("overlays_applied"))),
        "entry_price": _first_nonempty(row.get("entry_price"), outcome.get("entry_price"), unit.get("entry_price")),
        "stop_loss": _first_nonempty(row.get("stop_loss"), outcome.get("stop_loss"), unit.get("stop_loss")),
        "take_profit_1": _first_nonempty(row.get("take_profit_1"), outcome.get("take_profit_1"), unit.get("take_profit_1")),
        "stop_dist": _first_nonempty(row.get("stop_dist"), outcome.get("stop_dist"), unit.get("stop_dist")),
        "target_dist": _first_nonempty(row.get("target_dist"), outcome.get("target_dist"), unit.get("target_dist")),
        "pretrade_spread_r": _first_nonempty(row.get("pretrade_spread_r"), outcome.get("pretrade_spread_r"), packet.get("spread_r")),
        "pretrade_expected_slippage_r": _first_nonempty(row.get("pretrade_expected_slippage_r"), outcome.get("pretrade_expected_slippage_r")),
        "pretrade_total_cost_r": _first_nonempty(row.get("pretrade_total_cost_r"), outcome.get("pretrade_total_cost_r")),
        "source_completeness_status": _first_nonempty(row.get("source_completeness_status"), packet.get("source_completeness_status")),
        "slippage_source_status": _first_nonempty(row.get("slippage_source_status"), packet.get("slippage_source_status")),
        "swap_source_status": _first_nonempty(row.get("swap_source_status"), packet.get("swap_source_status")),
        "commission_source_status": _first_nonempty(row.get("commission_source_status"), packet.get("commission_source_status")),
        "source_path_sha256": _first_nonempty(row.get("source_path_sha256"), outcome.get("source_path_sha256"), unit.get("source_path_sha256")),
        "source_file_sha256": _first_nonempty(row.get("source_file_sha256"), outcome.get("source_file_sha256"), unit.get("source_file_sha256")),
        "bridge_context": bridge,
        "unit": unit,
        "outcome": outcome,
        "advisory": advisory,
        "reservoir_matches": [],
        "broker_runtime_change_status": False,
        "direct_execution_authority": False,
    }
    material["match_inputs"] = build_match_inputs(material)
    material["record_id"] = _record_id(material)
    return material


def normalize_runtime_packet(
    packet: Mapping[str, Any],
    *,
    source_path: str | None = None,
    source_line_no: int | None = None,
) -> list[dict[str, Any]]:
    unit = _as_mapping(packet.get("unit"))
    outcome = _as_mapping(packet.get("outcome"))
    bridge = _as_mapping(packet.get("bridge"))
    advisory = _as_mapping(packet.get("ultimate_convergence_advisory"))
    members = [str(item) for item in _as_list(unit.get("sleeve_members")) if str(item)]
    packet_sleeve = _first_nonempty(packet.get("sleeve"), outcome.get("sleeve"), _as_mapping(advisory.get("join_keys")).get("sleeve"))
    if packet_sleeve and str(packet_sleeve) not in members:
        members.append(str(packet_sleeve))
    if not members:
        members = [None]
    records: list[dict[str, Any]] = []
    for idx, member in enumerate(members):
        records.append(build_replay_record(
            source_kind="runtime_packet",
            source_path=source_path,
            source_line_no=source_line_no,
            packet=packet,
            unit=unit,
            outcome=outcome,
            bridge=bridge,
            advisory=advisory,
            sleeve=str(member) if member is not None else None,
            sleeve_members=[m for m in members if m is not None],
            unit_member_index=idx if member is not None else None,
        ))
    return records


def normalize_historical_candidate(
    row: Mapping[str, Any],
    *,
    source_kind: str = "historical_replay_candidate",
    source_path: str | None = None,
    source_line_no: int | None = None,
) -> dict[str, Any]:
    return build_replay_record(
        source_kind=source_kind,
        source_path=source_path,
        source_line_no=source_line_no,
        row=row,
        sleeve=str(row.get("sleeve")) if row.get("sleeve") is not None else None,
    )


def validate_replay_record(record: Mapping[str, Any]) -> tuple[bool, list[str]]:
    issues: list[str] = []
    if record.get("schema_version") != SCHEMA_VERSION:
        issues.append("schema_version_mismatch")
    for key in ("record_id", "source_kind", "match_inputs", "broker_runtime_change_status", "direct_execution_authority"):
        if key not in record:
            issues.append(f"missing_required:{key}")
    if record.get("broker_runtime_change_status") is not False:
        issues.append("broker_runtime_change_status_must_be_false")
    if record.get("direct_execution_authority") is not False:
        issues.append("direct_execution_authority_must_be_false")
    match_inputs = record.get("match_inputs")
    if not isinstance(match_inputs, Mapping):
        issues.append("match_inputs_not_mapping")
    else:
        forbidden = sorted(set(str(key) for key in match_inputs).intersection(RESULT_FIELD_KEYS))
        if forbidden:
            issues.append("result_fields_in_match_inputs:" + ",".join(forbidden))
    raw_keys = _contains_raw_key(record)
    if raw_keys:
        issues.append("forbidden_raw_keys:" + ",".join(sorted(set(raw_keys))))
    expected = _record_id(record)
    if record.get("record_id") != expected:
        issues.append("record_id_mismatch")
    return not issues, issues


__all__ = [
    "MATCH_INPUT_KEYS",
    "RESULT_FIELD_KEYS",
    "SCHEMA_VERSION",
    "build_match_inputs",
    "build_replay_record",
    "canonical_direction",
    "canonical_side",
    "normalize_historical_candidate",
    "normalize_runtime_packet",
    "validate_replay_record",
]
