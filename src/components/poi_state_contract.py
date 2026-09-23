"""Stable, causal point-of-interest state shared by replay and live paths."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping


POI_IDENTITY_SCHEMA = "gtos.poi_identity.v1"
POI_STATE_SCHEMA = "gtos.poi_state.predecision.v1"
POI_STATE_HASH_CONTRACT = "canonical_sha256_no_outcome_v1"
POI_STATE_SOURCE_BOUNDARY = (
    "closed_market_state_candles_asof_decision_no_postdecision_path"
)
POI_STATE_ATOMIC_FIELDS = (
    "poi_state_schema",
    "poi_state_hash_contract",
    "poi_id",
    "poi_type",
    "poi_timeframe",
    "poi_direction",
    "poi_zone_low",
    "poi_zone_high",
    "poi_source_candle_times",
    "poi_created_at_utc",
    "poi_state_asof_utc",
    "poi_age_hours",
    "poi_touch_count",
    "poi_first_touch_time_utc",
    "poi_last_touch_time_utc",
    "poi_mitigation_status",
    "poi_filled",
    "poi_invalidated",
    "poi_invalidation_time_utc",
    "poi_invalidation_reason",
    "poi_state_source_boundary",
    "poi_state_uses_outcome_fields",
)


def parse_utc(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        parsed = value
    else:
        text = str(value or "").strip()
        if not text:
            return None
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def iso_utc(value: Any) -> str:
    parsed = parse_utc(value)
    return parsed.isoformat() if parsed is not None else ""


def candle_close_utc(value: Any, timeframe_minutes: int) -> str:
    parsed = parse_utc(value)
    if parsed is None:
        return ""
    return (parsed + timedelta(minutes=max(0, int(timeframe_minutes)))).isoformat()


def _stable_sha256(payload: Any) -> str:
    material = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def stable_poi_id(
    *,
    symbol: Any,
    timeframe: Any,
    poi_type: Any,
    direction: Any,
    source_candle_times: list[Any] | tuple[Any, ...],
    zone_low: Any,
    zone_high: Any,
) -> str:
    times = [iso_utc(value) for value in source_candle_times]
    times = [value for value in times if value]
    try:
        low, high = sorted((float(zone_low), float(zone_high)))
    except (TypeError, ValueError):
        return ""
    if not times or not math.isfinite(low) or not math.isfinite(high) or high <= low:
        return ""
    payload = {
        "schema": POI_IDENTITY_SCHEMA,
        "symbol": str(symbol or "").strip().upper(),
        "timeframe": str(timeframe or "").strip().upper(),
        "poi_type": str(poi_type or "").strip().lower(),
        "direction": str(direction or "").strip().lower(),
        "source_candle_times": times,
        "zone_low": round(low, 10),
        "zone_high": round(high, 10),
    }
    return f"poi_{_stable_sha256(payload)[:24]}"


def poi_state_hash_payload(state: Mapping[str, Any]) -> dict[str, Any]:
    return {field: state.get(field) for field in POI_STATE_ATOMIC_FIELDS}


def poi_state_hash_sha256(state: Mapping[str, Any]) -> str:
    return _stable_sha256(poi_state_hash_payload(state))


def finalize_poi_state(state: Mapping[str, Any]) -> dict[str, Any]:
    materialized = dict(state)
    declared_hash = str(materialized.get("poi_state_hash_sha256") or "").strip()
    materialized.setdefault("poi_state_schema", POI_STATE_SCHEMA)
    materialized.setdefault("poi_state_hash_contract", POI_STATE_HASH_CONTRACT)
    materialized.setdefault("poi_state_source_boundary", POI_STATE_SOURCE_BOUNDARY)
    materialized.setdefault("poi_state_uses_outcome_fields", False)
    materialized["poi_source_candle_times"] = [
        iso_utc(value)
        for value in materialized.get("poi_source_candle_times") or ()
        if iso_utc(value)
    ]
    for field in (
        "poi_created_at_utc",
        "poi_state_asof_utc",
        "poi_first_touch_time_utc",
        "poi_last_touch_time_utc",
        "poi_invalidation_time_utc",
        "poi_terminal_time_utc",
    ):
        materialized[field] = iso_utc(materialized.get(field))
    try:
        low, high = sorted(
            (
                float(materialized.get("poi_zone_low")),
                float(materialized.get("poi_zone_high")),
            )
        )
        materialized["poi_zone_low"] = round(low, 10)
        materialized["poi_zone_high"] = round(high, 10)
    except (TypeError, ValueError):
        pass
    try:
        materialized["poi_age_hours"] = round(
            float(materialized.get("poi_age_hours")),
            8,
        )
    except (TypeError, ValueError):
        pass
    try:
        materialized["poi_touch_count"] = int(
            materialized.get("poi_touch_count") or 0
        )
    except (TypeError, ValueError):
        materialized["poi_touch_count"] = 0
    for field in ("poi_overlap_bar_count", "poi_touch_episode_count"):
        try:
            materialized[field] = int(materialized.get(field) or 0)
        except (TypeError, ValueError):
            materialized[field] = 0
    try:
        materialized["poi_max_mitigation_fraction"] = round(
            max(
                0.0,
                min(
                    1.0,
                    float(materialized.get("poi_max_mitigation_fraction") or 0.0),
                ),
            ),
            12,
        )
    except (TypeError, ValueError):
        materialized["poi_max_mitigation_fraction"] = 0.0
    materialized["poi_filled"] = bool(materialized.get("poi_filled"))
    materialized["poi_invalidated"] = bool(materialized.get("poi_invalidated"))
    materialized["poi_terminal_frozen"] = bool(
        materialized.get("poi_terminal_frozen")
    )
    materialized["poi_state_uses_outcome_fields"] = bool(
        materialized.get("poi_state_uses_outcome_fields")
    )
    materialized["poi_state_hash_sha256"] = (
        declared_hash or poi_state_hash_sha256(materialized)
    )
    failures = poi_state_contract_failures(materialized)
    materialized["poi_state_contract_status"] = (
        "valid_predecision_poi_state"
        if not failures
        else "invalid_predecision_poi_state"
    )
    materialized["poi_state_contract_failures"] = list(failures)
    return materialized


def poi_state_contract_failures(
    state: Mapping[str, Any],
    *,
    decision_time_utc: Any = None,
) -> tuple[str, ...]:
    state = state if isinstance(state, Mapping) else {}
    failures: list[str] = []
    for field in (
        "poi_id",
        "poi_type",
        "poi_timeframe",
        "poi_direction",
        "poi_created_at_utc",
        "poi_state_asof_utc",
        "poi_mitigation_status",
    ):
        if state.get(field) in (None, ""):
            failures.append(f"{field}_missing")
    if state.get("poi_state_schema") != POI_STATE_SCHEMA:
        failures.append("poi_state_schema_invalid")
    if state.get("poi_state_hash_contract") != POI_STATE_HASH_CONTRACT:
        failures.append("poi_state_hash_contract_invalid")
    if state.get("poi_state_source_boundary") != POI_STATE_SOURCE_BOUNDARY:
        failures.append("poi_state_source_boundary_invalid")
    if state.get("poi_state_uses_outcome_fields") is not False:
        failures.append("poi_state_uses_outcome_fields")
    if not state.get("poi_source_candle_times"):
        failures.append("poi_source_candle_times_missing")
    try:
        low = float(state.get("poi_zone_low"))
        high = float(state.get("poi_zone_high"))
        if not math.isfinite(low) or not math.isfinite(high) or high <= low:
            failures.append("poi_zone_geometry_invalid")
    except (TypeError, ValueError):
        failures.append("poi_zone_geometry_missing")
    created = parse_utc(state.get("poi_created_at_utc"))
    asof = parse_utc(state.get("poi_state_asof_utc"))
    decision = parse_utc(decision_time_utc) if decision_time_utc not in (None, "") else None
    if created is None:
        failures.append("poi_created_at_invalid")
    if asof is None:
        failures.append("poi_state_asof_invalid")
    if created is not None and asof is not None:
        if created > asof:
            failures.append("poi_created_after_state_asof")
        expected_age = max(0.0, (asof - created).total_seconds() / 3600.0)
        try:
            observed_age = float(state.get("poi_age_hours"))
        except (TypeError, ValueError):
            observed_age = math.nan
        if not math.isfinite(observed_age):
            failures.append("poi_age_hours_missing")
        elif abs(observed_age - expected_age) > 1e-6:
            failures.append("poi_age_hours_mismatch")
    if asof is not None and decision is not None and asof > decision:
        failures.append("poi_state_asof_after_decision")
    try:
        touch_count = int(state.get("poi_touch_count"))
        if touch_count < 0:
            failures.append("poi_touch_count_negative")
    except (TypeError, ValueError):
        failures.append("poi_touch_count_invalid")
        touch_count = 0
    first_touch = parse_utc(state.get("poi_first_touch_time_utc"))
    last_touch = parse_utc(state.get("poi_last_touch_time_utc"))
    if touch_count == 0 and (first_touch is not None or last_touch is not None):
        failures.append("poi_touch_time_without_touch")
    if touch_count > 0 and (first_touch is None or last_touch is None):
        failures.append("poi_touch_time_missing")
    if first_touch is not None and last_touch is not None and first_touch > last_touch:
        failures.append("poi_touch_time_order_invalid")
    if created is not None and first_touch is not None and first_touch < created:
        failures.append("poi_touch_before_creation")
    if asof is not None and last_touch is not None and last_touch > asof:
        failures.append("poi_touch_after_state_asof")
    status = str(state.get("poi_mitigation_status") or "")
    filled = state.get("poi_filled") is True
    invalidated = state.get("poi_invalidated") is True
    if filled and invalidated:
        failures.append("poi_terminal_state_not_exclusive")
    if filled and status != "filled":
        failures.append("poi_filled_status_mismatch")
    if not filled and touch_count == 0 and status != "untouched":
        failures.append("poi_untouched_status_mismatch")
    if not filled and touch_count > 0 and status != "partially_mitigated":
        failures.append("poi_partial_mitigation_status_mismatch")
    invalidation_time = parse_utc(state.get("poi_invalidation_time_utc"))
    if invalidated and invalidation_time is None:
        failures.append("poi_invalidation_time_missing")
    if invalidated and not str(state.get("poi_invalidation_reason") or "").strip():
        failures.append("poi_invalidation_reason_missing")
    if not invalidated and (
        invalidation_time is not None
        or str(state.get("poi_invalidation_reason") or "").strip()
    ):
        failures.append("poi_invalidation_detail_without_invalidation")
    declared_hash = str(state.get("poi_state_hash_sha256") or "").strip()
    if len(declared_hash) != 64:
        failures.append("poi_state_hash_missing_or_invalid")
    elif declared_hash != poi_state_hash_sha256(state):
        failures.append("poi_state_hash_mismatch")
    return tuple(dict.fromkeys(failures))


def poi_state_required(row: Mapping[str, Any]) -> bool:
    source_fields = row.get("source_fields") if isinstance(row, Mapping) else None
    source_fields = source_fields if isinstance(source_fields, Mapping) else {}
    origin = str(
        row.get("origin_family")
        or row.get("candidate_origin_family")
        or source_fields.get("origin_family")
        or source_fields.get("generation_rule")
        or ""
    ).lower()
    framework = str(
        row.get("current_framework")
        or row.get("framework")
        or source_fields.get("current_framework")
        or source_fields.get("framework")
        or ""
    ).lower()
    return bool(
        row.get("poi_state_required") is True
        or source_fields.get("poi_state_required") is True
        or row.get("poi_id")
        or row.get("poi_state")
        or source_fields.get("poi_id")
        or source_fields.get("poi_state")
        or "current_fvg_fill" in origin
        or framework == "fvg_fill"
    )


__all__ = [
    "POI_IDENTITY_SCHEMA",
    "POI_STATE_ATOMIC_FIELDS",
    "POI_STATE_HASH_CONTRACT",
    "POI_STATE_SCHEMA",
    "POI_STATE_SOURCE_BOUNDARY",
    "candle_close_utc",
    "finalize_poi_state",
    "iso_utc",
    "parse_utc",
    "poi_state_contract_failures",
    "poi_state_hash_sha256",
    "poi_state_required",
    "stable_poi_id",
]
