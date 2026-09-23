"""Causal decision-time POI lifecycle and execution-fillability contract."""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Mapping

from src.components.poi_state_contract import parse_utc, poi_state_contract_failures


CAUSAL_POI_LIFECYCLE_SCHEMA = "gtos.causal_poi_lifecycle.predecision.v1"
CAUSAL_POI_LIFECYCLE_HASH_CONTRACT = "canonical_sha256_no_outcome_v1"
CAUSAL_POI_LIFECYCLE_SOURCE_BOUNDARY = (
    "closed_poi_state_and_m15_price_asof_decision_no_postdecision_path"
)
PREDECISION_LIMIT_FILLABILITY_SCHEMA = "predecision_limit_fillability_signal_v1"
PREDECISION_LIMIT_FILLABILITY_SOURCE = (
    "predecision_limit_fillability.fill_probability"
)
PREDECISION_LIMIT_FILLABILITY_SOURCE_BOUNDARY = (
    "closed_m15_predecision_asof_no_postdecision_path"
)

CAUSAL_POI_LIFECYCLE_HASH_FIELDS = (
    "schema_version",
    "hash_contract",
    "poi_id",
    "poi_state_hash_sha256",
    "decision_time_utc",
    "poi_lifecycle_state",
    "poi_proximity_state",
    "poi_mitigation_status",
    "poi_age_hours",
    "poi_overlap_bar_count",
    "poi_touch_episode_count",
    "poi_max_mitigation_fraction",
    "poi_filled",
    "poi_invalidated",
    "current_price",
    "entry_price",
    "stop_loss",
    "atr14",
    "distance_to_zone_price",
    "distance_to_zone_atr",
    "distance_to_midpoint_price",
    "distance_to_midpoint_atr",
    "distance_to_limit_price",
    "distance_to_limit_atr",
    "distance_to_limit_risk",
    "limit_marketable_at_decision",
    "execution_fill_probability",
    "execution_fill_probability_source",
    "execution_fill_probability_source_time_utc",
    "execution_fill_probability_source_boundary",
    "scheduler_readiness_min_execution_fill_probability",
    "scheduler_readiness_policy_source",
    "scheduler_readiness_policy_hash_sha256",
    "visible_candidate",
    "scheduler_rankable_now",
    "execution_allowed_by_poi_lifecycle",
    "primary_reason",
    "reasons",
    "source_boundary",
    "uses_outcome_fields",
)


def _stable_sha256(payload: Any) -> str:
    material = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _number(value: Any) -> float | None:
    if value in (None, "") or isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def predecision_fillability_boundary_allowed(value: Any) -> bool:
    text = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    if not text:
        return False
    no_postdecision = any(
        token in text
        for token in (
            "no_postdecision",
            "no_post_decision",
            "without_postdecision",
            "without_post_decision",
        )
    )
    no_outcome = any(
        token in text
        for token in ("no_outcome", "without_outcome")
    )
    unsafe_postdecision = any(
        token in text for token in ("postdecision", "post_decision")
    ) and not no_postdecision
    unsafe_outcome = "outcome" in text and not no_outcome
    if (
        unsafe_postdecision
        or unsafe_outcome
        or any(token in text for token in ("realized", "actual_fill", "broker_live"))
    ):
        return False
    return bool(
        ("predecision" in text or "asof" in text)
        and (no_postdecision or no_outcome)
    )


def predecision_limit_fillability_from_geometry(
    *,
    side: Any,
    entry_price: Any,
    stop_loss: Any,
    current_price: Any,
    atr14: Any,
    atr14_basis: Any = None,
    current_price_source: Any = None,
    current_price_source_time_utc: Any = None,
    current_price_source_boundary: Any = None,
    decision_time_utc: Any = None,
) -> dict[str, Any]:
    """Return the single shared ATR/risk-distance limit-fillability signal.

    ``atr14_basis`` names the bar timeframe AND the estimator that produced
    ``atr14`` (e.g. ``"M15|wilder_true_range_14"``).  It is echoed verbatim on
    both return shapes so every ATR-denominated quantity below travels with the
    yardstick that produced it.

    This exists because the key is named ``atr14`` and nothing else in the
    contract said what an ATR-14 *is* here.  Two materially different M15
    estimators feed this function from
    ``broader_origin_generators._current_framework_atr_with_source`` -- Wilder
    true range and a gap-blind mean of high-low -- and they disagree outside
    +/-10 % on 48.30 % of bars (phase20/receipts/r2/R2_ATR_DEFS_V1.json).
    Without the label a consumer cannot tell which one it holds, so a threshold
    on ``distance_to_limit_atr`` or on ``risk / atr14`` silently means different
    things for different candidates.  ``None`` is preserved rather than
    defaulted: an unlabelled ATR must be *visible* as unlabelled, never guessed.
    """

    side_text = str(side or "").strip().upper()
    entry = _number(entry_price)
    stop = _number(stop_loss)
    current = _number(current_price)
    atr = _number(atr14)
    basis = str(atr14_basis or "").strip() or None
    source_boundary = str(current_price_source_boundary or "").strip()
    if (
        side_text not in {"LONG", "SHORT"}
        or entry is None
        or current is None
    ):
        return {
            "schema_version": PREDECISION_LIMIT_FILLABILITY_SCHEMA,
            "available": False,
            "fill_probability": None,
            "reason": "missing_side_entry_or_current_price",
            "source_boundary": source_boundary or None,
            "current_price_source_boundary": source_boundary or None,
            "current_price_source_time_utc": (
                str(current_price_source_time_utc or "").strip() or None
            ),
            "decision_time_utc": str(decision_time_utc or "").strip() or None,
            "used_only_predecision_fields": True,
            "atr14_basis": basis,
        }

    unit_risk = abs(entry - stop) if stop is not None else 0.0
    limit_marketable = (
        (side_text == "LONG" and entry >= current)
        or (side_text == "SHORT" and entry <= current)
    )
    distance_to_limit_price = 0.0 if limit_marketable else abs(entry - current)
    distance_to_limit_atr = (
        distance_to_limit_price / atr if atr is not None and atr > 0.0 else None
    )
    distance_to_limit_risk = (
        distance_to_limit_price / unit_risk if unit_risk > 0.0 else None
    )

    if limit_marketable:
        atr_component = 0.92
        risk_component = 0.92
        reason = "limit_price_marketable_at_decision"
    else:
        atr_component = (
            0.50
            if distance_to_limit_atr is None
            else 1.0 / (1.0 + max(0.0, distance_to_limit_atr) ** 1.35)
        )
        risk_component = (
            0.50
            if distance_to_limit_risk is None
            else 1.0 / (1.0 + max(0.0, distance_to_limit_risk) ** 1.10)
        )
        reason = "limit_distance_scaled_by_predecision_atr_and_stop"

    fill_probability = max(
        0.03,
        min(0.95, atr_component * 0.70 + risk_component * 0.30),
    )
    return {
        "schema_version": PREDECISION_LIMIT_FILLABILITY_SCHEMA,
        "available": True,
        "fill_probability": round(fill_probability, 9),
        "reason": reason,
        "side": side_text,
        "entry_price": round(entry, 8),
        "current_price": round(current, 8),
        "current_price_source": str(current_price_source or "").strip() or None,
        "current_price_source_boundary": source_boundary or None,
        "current_price_source_time_utc": (
            str(current_price_source_time_utc or "").strip() or None
        ),
        "decision_time_utc": str(decision_time_utc or "").strip() or None,
        "stop_loss": round(stop, 8) if stop is not None else None,
        "atr14": round(atr, 12) if atr is not None and atr > 0.0 else None,
        # The yardstick, travelling with the measurement it produced.  Every
        # ATR-denominated field in this dict is denominated in THIS basis.
        "atr14_basis": basis,
        "unit_risk": round(unit_risk, 12) if unit_risk > 0.0 else None,
        "distance_to_limit_price": round(distance_to_limit_price, 12),
        "distance_to_limit_atr": (
            round(distance_to_limit_atr, 12)
            if distance_to_limit_atr is not None
            else None
        ),
        "distance_to_limit_risk": (
            round(distance_to_limit_risk, 12)
            if distance_to_limit_risk is not None
            else None
        ),
        "limit_marketable_at_decision": limit_marketable,
        "used_only_predecision_fields": True,
        "source_boundary": source_boundary or None,
    }


def scheduler_readiness_fill_floor(
    config: Mapping[str, Any] | None,
) -> tuple[float, str, str]:
    """Resolve the lowest configured execution floor that can rank a package row."""

    config = config if isinstance(config, Mapping) else {}
    runtime = config.get("gtos_vnext_runtime")
    runtime = runtime if isinstance(runtime, Mapping) else {}
    candidates = (
        (
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_bypass_min_execution_fill_probability",
            runtime.get(
                "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_bypass_min_execution_fill_probability"
            ),
        ),
        (
            "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_fill_probability",
            runtime.get(
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_fill_probability"
            ),
        ),
        (
            "scheduler_v4_best_trade_allocator_dynamic_budget_min_fill_probability",
            runtime.get(
                "scheduler_v4_best_trade_allocator_dynamic_budget_min_fill_probability"
            ),
        ),
    )
    positive = [
        (name, value)
        for name, raw in candidates
        if (value := _number(raw)) is not None and value > 0.0
    ]
    if positive:
        source, floor = min(positive, key=lambda item: item[1])
    else:
        source, floor = (
            "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_fill_probability:default",
            0.45,
        )
    floor = max(0.0, min(1.0, float(floor)))
    policy_hash = _stable_sha256(
        {
            "schema": "gtos.poi_scheduler_readiness_policy.v1",
            "min_execution_fill_probability": round(floor, 12),
            "source": source,
        }
    )
    return floor, source, policy_hash


def causal_poi_lifecycle_hash_payload(
    envelope: Mapping[str, Any],
) -> dict[str, Any]:
    return {field: envelope.get(field) for field in CAUSAL_POI_LIFECYCLE_HASH_FIELDS}


def causal_poi_lifecycle_hash_sha256(envelope: Mapping[str, Any]) -> str:
    return _stable_sha256(causal_poi_lifecycle_hash_payload(envelope))


def build_causal_poi_lifecycle_envelope(
    *,
    poi_state: Mapping[str, Any],
    decision_time_utc: Any,
    fillability: Mapping[str, Any],
    distance_to_zone_price: Any,
    distance_to_zone_atr: Any,
    distance_to_midpoint_price: Any,
    distance_to_midpoint_atr: Any,
    scheduler_readiness_floor: Any,
    scheduler_readiness_policy_source: Any,
    scheduler_readiness_policy_hash_sha256: Any,
    visible_candidate: bool = True,
) -> dict[str, Any]:
    """Build a separately signed lifecycle overlay without mutating POI-state v1."""

    state = dict(poi_state) if isinstance(poi_state, Mapping) else {}
    fill = dict(fillability) if isinstance(fillability, Mapping) else {}
    decision_time = str(decision_time_utc or "").strip()
    floor = _number(scheduler_readiness_floor)
    floor = max(0.0, min(1.0, floor if floor is not None else 0.45))
    fill_probability = _number(fill.get("fill_probability"))
    state_failures = list(
        poi_state_contract_failures(state, decision_time_utc=decision_time)
    )
    filled = state.get("poi_filled") is True
    invalidated = state.get("poi_invalidated") is True
    mitigation_status = str(state.get("poi_mitigation_status") or "").strip()
    overlap_count = int(
        _number(
            state.get("poi_overlap_bar_count")
            if state.get("poi_overlap_bar_count") is not None
            else state.get("poi_touch_count")
        )
        or 0
    )
    touch_episode_count = int(
        _number(state.get("poi_touch_episode_count"))
        or (1 if overlap_count > 0 else 0)
    )
    max_mitigation_fraction = _number(state.get("poi_max_mitigation_fraction"))
    max_mitigation_fraction = (
        max(0.0, min(1.0, max_mitigation_fraction))
        if max_mitigation_fraction is not None
        else 0.0
    )

    reasons: list[str] = []
    if state_failures:
        lifecycle_state = "invalid"
        reasons.extend(f"poi_state_contract:{reason}" for reason in state_failures)
    elif invalidated:
        lifecycle_state = "invalidated"
        reasons.append("poi_invalidated_before_decision")
    elif filled:
        lifecycle_state = "filled"
        reasons.append("poi_filled_before_decision")
    elif mitigation_status == "partially_mitigated" or overlap_count > 0:
        lifecycle_state = "partially_mitigated"
    else:
        lifecycle_state = "unmitigated"

    distance_zone = _number(distance_to_zone_price)
    if distance_zone is not None and distance_zone <= 0:
        proximity_state = "inside_zone"
    elif fill_probability is not None and fill_probability >= floor:
        proximity_state = "near_touch"
    else:
        proximity_state = "dormant"

    scheduler_rankable = bool(
        visible_candidate
        and not state_failures
        and lifecycle_state not in {"filled", "invalidated", "invalid"}
        and fill_probability is not None
        and fill_probability >= floor
    )
    if not reasons and fill_probability is None:
        reasons.append("execution_fillability_missing_source_bound_input")
    elif not reasons and not scheduler_rankable:
        reasons.append(
            "execution_fillability_below_poi_scheduler_readiness_floor"
        )
    elif not reasons:
        reasons.append("poi_scheduler_readiness_passed")

    envelope: dict[str, Any] = {
        "schema_version": CAUSAL_POI_LIFECYCLE_SCHEMA,
        "hash_contract": CAUSAL_POI_LIFECYCLE_HASH_CONTRACT,
        "poi_id": str(state.get("poi_id") or "").strip(),
        "poi_state_hash_sha256": str(
            state.get("poi_state_hash_sha256") or ""
        ).strip(),
        "decision_time_utc": decision_time,
        "poi_lifecycle_state": lifecycle_state,
        "poi_proximity_state": proximity_state,
        "poi_mitigation_status": mitigation_status,
        "poi_age_hours": _number(state.get("poi_age_hours")),
        "poi_overlap_bar_count": overlap_count,
        "poi_touch_episode_count": touch_episode_count,
        "poi_max_mitigation_fraction": round(max_mitigation_fraction, 12),
        "poi_filled": filled,
        "poi_invalidated": invalidated,
        "current_price": _number(fill.get("current_price")),
        "entry_price": _number(fill.get("entry_price")),
        "stop_loss": _number(fill.get("stop_loss")),
        "atr14": _number(fill.get("atr14")),
        "distance_to_zone_price": _number(distance_to_zone_price),
        "distance_to_zone_atr": _number(distance_to_zone_atr),
        "distance_to_midpoint_price": _number(distance_to_midpoint_price),
        "distance_to_midpoint_atr": _number(distance_to_midpoint_atr),
        "distance_to_limit_price": _number(fill.get("distance_to_limit_price")),
        "distance_to_limit_atr": _number(fill.get("distance_to_limit_atr")),
        "distance_to_limit_risk": _number(fill.get("distance_to_limit_risk")),
        "limit_marketable_at_decision": fill.get("limit_marketable_at_decision")
        is True,
        "execution_fill_probability": fill_probability,
        "execution_fill_probability_source": PREDECISION_LIMIT_FILLABILITY_SOURCE,
        "execution_fill_probability_source_time_utc": str(
            fill.get("current_price_source_time_utc") or ""
        ).strip(),
        "execution_fill_probability_source_boundary": str(
            fill.get("current_price_source_boundary")
            or fill.get("source_boundary")
            or ""
        ).strip(),
        "scheduler_readiness_min_execution_fill_probability": round(floor, 12),
        "scheduler_readiness_policy_source": str(
            scheduler_readiness_policy_source or ""
        ).strip(),
        "scheduler_readiness_policy_hash_sha256": str(
            scheduler_readiness_policy_hash_sha256 or ""
        ).strip(),
        "visible_candidate": bool(visible_candidate),
        "scheduler_rankable_now": scheduler_rankable,
        "execution_allowed_by_poi_lifecycle": scheduler_rankable,
        "primary_reason": reasons[0],
        "reasons": list(dict.fromkeys(reasons)),
        "source_boundary": CAUSAL_POI_LIFECYCLE_SOURCE_BOUNDARY,
        "uses_outcome_fields": False,
    }
    envelope["lifecycle_hash_sha256"] = causal_poi_lifecycle_hash_sha256(
        envelope
    )
    failures = causal_poi_lifecycle_contract_failures(
        envelope,
        poi_state=state,
        decision_time_utc=decision_time,
    )
    envelope["contract_status"] = (
        "valid_predecision_poi_lifecycle"
        if not failures
        else "invalid_predecision_poi_lifecycle"
    )
    envelope["contract_failures"] = list(failures)
    return envelope


def causal_poi_lifecycle_contract_failures(
    envelope: Mapping[str, Any],
    *,
    poi_state: Mapping[str, Any] | None = None,
    decision_time_utc: Any = None,
) -> tuple[str, ...]:
    envelope = envelope if isinstance(envelope, Mapping) else {}
    failures: list[str] = []
    if envelope.get("schema_version") != CAUSAL_POI_LIFECYCLE_SCHEMA:
        failures.append("poi_lifecycle_schema_invalid")
    if envelope.get("hash_contract") != CAUSAL_POI_LIFECYCLE_HASH_CONTRACT:
        failures.append("poi_lifecycle_hash_contract_invalid")
    if envelope.get("source_boundary") != CAUSAL_POI_LIFECYCLE_SOURCE_BOUNDARY:
        failures.append("poi_lifecycle_source_boundary_invalid")
    if envelope.get("uses_outcome_fields") is not False:
        failures.append("poi_lifecycle_uses_outcome_fields")
    if not str(envelope.get("poi_id") or "").strip():
        failures.append("poi_lifecycle_poi_id_missing")
    if len(str(envelope.get("poi_state_hash_sha256") or "").strip()) != 64:
        failures.append("poi_lifecycle_poi_state_hash_missing")
    decision = parse_utc(
        decision_time_utc
        if decision_time_utc not in (None, "")
        else envelope.get("decision_time_utc")
    )
    if decision is None:
        failures.append("poi_lifecycle_decision_time_invalid")
    source_time = parse_utc(
        envelope.get("execution_fill_probability_source_time_utc")
    )
    if source_time is None:
        failures.append("poi_lifecycle_fillability_source_time_invalid")
    elif decision is not None and source_time >= decision:
        failures.append("poi_lifecycle_fillability_source_time_not_predecision")
    if not predecision_fillability_boundary_allowed(
        envelope.get("execution_fill_probability_source_boundary")
    ):
        failures.append("poi_lifecycle_fillability_source_boundary_invalid")
    if _number(envelope.get("execution_fill_probability")) is None:
        failures.append("poi_lifecycle_execution_fillability_missing")
    if _number(
        envelope.get("scheduler_readiness_min_execution_fill_probability")
    ) is None:
        failures.append("poi_lifecycle_readiness_floor_missing")
    if len(
        str(envelope.get("scheduler_readiness_policy_hash_sha256") or "").strip()
    ) != 64:
        failures.append("poi_lifecycle_readiness_policy_hash_missing")
    declared_hash = str(envelope.get("lifecycle_hash_sha256") or "").strip()
    if len(declared_hash) != 64:
        failures.append("poi_lifecycle_hash_missing")
    elif declared_hash != causal_poi_lifecycle_hash_sha256(envelope):
        failures.append("poi_lifecycle_hash_mismatch")
    state = poi_state if isinstance(poi_state, Mapping) else {}
    if state:
        if str(envelope.get("poi_id") or "").strip() != str(
            state.get("poi_id") or ""
        ).strip():
            failures.append("poi_lifecycle_poi_id_mismatch")
        if str(envelope.get("poi_state_hash_sha256") or "").strip() != str(
            state.get("poi_state_hash_sha256") or ""
        ).strip():
            failures.append("poi_lifecycle_poi_state_hash_mismatch")
    if envelope.get("scheduler_rankable_now") is True:
        if envelope.get("poi_lifecycle_state") in {"filled", "invalidated", "invalid"}:
            failures.append("terminal_poi_lifecycle_marked_scheduler_rankable")
        fill_probability = _number(envelope.get("execution_fill_probability"))
        floor = _number(
            envelope.get("scheduler_readiness_min_execution_fill_probability")
        )
        if fill_probability is None or floor is None or fill_probability < floor:
            failures.append("poi_lifecycle_rankable_below_execution_fill_floor")
    if bool(envelope.get("execution_allowed_by_poi_lifecycle")) != bool(
        envelope.get("scheduler_rankable_now")
    ):
        failures.append("poi_lifecycle_execution_rank_projection_mismatch")
    if envelope.get("poi_filled") is True and envelope.get("poi_invalidated") is True:
        failures.append("poi_lifecycle_terminal_state_not_exclusive")
    lifecycle_state = str(envelope.get("poi_lifecycle_state") or "").strip()
    if lifecycle_state == "filled" and envelope.get("poi_filled") is not True:
        failures.append("poi_lifecycle_filled_projection_mismatch")
    if lifecycle_state == "invalidated" and envelope.get("poi_invalidated") is not True:
        failures.append("poi_lifecycle_invalidated_projection_mismatch")
    reasons = envelope.get("reasons")
    if not isinstance(reasons, list) or not reasons:
        failures.append("poi_lifecycle_reasons_missing")
    elif str(envelope.get("primary_reason") or "").strip() != str(reasons[0] or "").strip():
        failures.append("poi_lifecycle_primary_reason_projection_mismatch")
    return tuple(dict.fromkeys(failures))


def row_causal_poi_lifecycle_required(row: Mapping[str, Any]) -> bool:
    if not isinstance(row, Mapping):
        return False
    if row.get("poi_state_required") is True:
        return True
    source_fields = row.get("source_fields")
    return bool(
        isinstance(source_fields, Mapping)
        and source_fields.get("poi_state_required") is True
    )


def row_causal_poi_lifecycle_envelope(
    row: Mapping[str, Any],
) -> Mapping[str, Any]:
    if not isinstance(row, Mapping):
        return {}
    containers: list[Mapping[str, Any]] = [row]
    for key in (
        "source_fields",
        "candidate_source_fields",
        "candidate_decision_inputs",
        "scheduler_candidate_decision_inputs",
        "trade_parameters",
    ):
        value = row.get(key)
        if isinstance(value, Mapping):
            containers.append(value)
    for container in containers:
        envelope = container.get("causal_poi_lifecycle")
        if isinstance(envelope, Mapping) and envelope:
            return envelope
    return {}


__all__ = [
    "CAUSAL_POI_LIFECYCLE_HASH_CONTRACT",
    "CAUSAL_POI_LIFECYCLE_HASH_FIELDS",
    "CAUSAL_POI_LIFECYCLE_SCHEMA",
    "CAUSAL_POI_LIFECYCLE_SOURCE_BOUNDARY",
    "PREDECISION_LIMIT_FILLABILITY_SCHEMA",
    "PREDECISION_LIMIT_FILLABILITY_SOURCE",
    "PREDECISION_LIMIT_FILLABILITY_SOURCE_BOUNDARY",
    "build_causal_poi_lifecycle_envelope",
    "causal_poi_lifecycle_contract_failures",
    "causal_poi_lifecycle_hash_payload",
    "causal_poi_lifecycle_hash_sha256",
    "predecision_limit_fillability_from_geometry",
    "predecision_fillability_boundary_allowed",
    "row_causal_poi_lifecycle_envelope",
    "row_causal_poi_lifecycle_required",
    "scheduler_readiness_fill_floor",
]
