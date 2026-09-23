"""Selector V4 broker-net admission authority.

Challenge admission decisions are Choices. The POST lives in
src.judgment.selector_choices and does not send an order. This module
performs no MT5, broker, account, order, deal, or position operations. Callers pass an as-of
candidate packet that already contains probability/debate, numeric
confluence, broker-net/cost, and lifecycle evidence. Selector V4 returns a
structured admission decision for the active V4 local authority path.

The only file access is the default-OFF learned-edge admission mode: when
``selector_v4_learned_edge_enabled`` is explicitly true, the module reads one
frozen local learned-edge artifact JSON (cached) through
``src.components.learned_edge_layer_v4``. With the learned-edge keys absent or
false, behavior is byte-identical to the pre-learned-mode module.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from itertools import islice
from typing import Any, Mapping, Sequence

from src.judgment.selector_choices import (
    load_selector_choices,
    selector_side as _selector_side,
)
from src.components.learned_edge_layer_v4 import (
    extract_runtime_features,
    load_learned_edge_artifact_cached,
    score_learned_edge,
)
from src.components.ultimate_candidate_package import (
    evaluate_ultimate_candidate_selector_shadow,
    load_ultimate_candidate_package_registry,
)
from src.components.poi_execution_lifecycle import (
    causal_poi_lifecycle_contract_failures,
    row_causal_poi_lifecycle_envelope,
    row_causal_poi_lifecycle_required,
)
from src.research.reduced_risk_action_reason_contract import (
    OPEN_REDUCED_SELECTOR_REASONS as SHARED_OPEN_REDUCED_SELECTOR_REASONS,
)


SELECTOR_V4_ACTIONS = (
    "trade",
    "no-trade",
    "source-required",
    "reduce-risk",
    "open-reduced-risk",
    "queue",
    "reject",
)

RISK_BEARING_SELECTOR_V4_ACTIONS = frozenset(
    {"trade", "reduce-risk", "open-reduced-risk"}
)
BLOCKING_SELECTOR_V4_ACTIONS = frozenset(
    {"no-trade", "source-required", "queue", "reject"}
)
SELECTOR_V4_OPEN_REDUCED_SELECTOR_REASONS = SHARED_OPEN_REDUCED_SELECTOR_REASONS

FORBIDDEN_SELECTOR_V4_RUNTIME_FIELDS = (
    "actual_r",
    "actual_exact_r",
    "actual_broker_real_pnl_cash",
    "broker_actual_r",
    "broker_cash_pnl",
    "broker_real_net_r",
    "broker_realized_net_r",
    "close_reason",
    "correct_rejection",
    "exact_r",
    "final_r",
    "final_target_reached",
    "giveback_r",
    "gross_r",
    "hindsight_best_action",
    "hindsight_best_policy",
    "hindsight_best_r",
    "mae_r",
    "mfe_r",
    "missed_opportunity",
    "net_r",
    "one_r_reached",
    "path_outcome",
    "profit_after_entry",
    "proxy_r",
    "realized_pnl",
    "result_r",
    "sl_before_1r",
    "source_bound_proxy_r",
    "time_to_1r_seconds",
    "time_to_sl_seconds",
    "win_rate_after_decision",
)

_ACTIONS_REQUIRING_THESES = (
    "long",
    "short",
    "no-trade",
    "wait",
    "scale",
    "reduce",
    "close",
    "reverse",
)

DEFAULT_REQUIRED_CONFLUENCE_SOURCE_FAMILIES = (
    "selector",
    "market_state",
    "cost",
    "lifecycle",
    "source_completeness",
)
PACKAGE_NON_EXECUTABLE_ROLE_DISPOSITIONS = frozenset(
    {
        "source_required_hold",
        "redesign_repair_hold",
        "avoid_feature_only_veto",
    }
)
PACKAGE_REDUCED_RISK_ROLE_DISPOSITIONS = frozenset(
    {
        "admission_with_avoid_feature_risk_control",
        "admission_with_redesign_context",
    }
)
FORBIDDEN_SOURCE_EVIDENCE_TOKENS = (
    "actual",
    "broker_real_cash",
    "broker_real_pnl",
    "exact_r",
    "final_r",
    "hindsight",
    "outcome",
    "post_decision",
    "realized",
    "result_row",
    "validation_result",
)


SELECTOR_HASH_MAX_COLLECTION_ITEMS = 50
SELECTOR_HASH_MAX_DEPTH = 6
SELECTOR_HASH_MAX_TEXT_BYTES = 512


def _canonical_selector_reason(reasons: Sequence[str]) -> str:
    unique = sorted({str(reason) for reason in reasons if str(reason or "").strip()})
    if (_sv_155 := _selector_side(
        'sv4_155_selector_v4_reason_missing',
        bool(not unique),
        'selector_v4_reason_missing',
        'other_side',
        'Condition: not unique. Which side of this condition is the decision?',
        true_text='The label on this side is selector_v4_reason_missing.',
        false_text='The label on the other side is other_side.',
    )) == "true":
        return "selector_v4_reason_missing"
    if _sv_155 is None:
        return None


    def priority(reason: str) -> tuple[int, str]:
        normalized = reason.lower()
        if (
            (_sv_160 := _selector_side(
        'sv4_160_label',
        bool("pretrade_cost" in normalized
            or "broker_cost" in normalized
            or "cost_packet_refused" in normalized
            or "negative_after_cost" in normalized
            or "cost_above" in normalized),
        'label',
        'other_side',
        'Condition: "pretrade_cost" in normalized\n            or "broker_cost" in normalized\n            or "cost_packet_refused" in normalized\n            or "negative_after_cost" in normalized\n            or "cost_above" in normalized. Which side of this condition is the decision?',
        true_text='The label on this side is label.',
        false_text='The label on the other side is other_side.',
    )) == "true"
        ):
            return (0, reason)
        if _sv_160 is None:
            return (20, reason)

        if (_sv_168 := _selector_side(
        'sv4_168_label',
        bool("broker_net_admission_ev_negative" in normalized),
        'label',
        'other_side',
        'Condition: "broker_net_admission_ev_negative" in normalized. Which side of this condition is the decision?',
        true_text='The label on this side is label.',
        false_text='The label on the other side is other_side.',
    )) == "true":
            return (1, reason)
        if _sv_168 is None:
            return (20, reason)

        if (_sv_170 := _selector_side(
        'sv4_170_label',
        bool("source_required" in normalized),
        'label',
        'other_side',
        'Condition: "source_required" in normalized. Which side of this condition is the decision?',
        true_text='The label on this side is label.',
        false_text='The label on the other side is other_side.',
    )) == "true":
            return (2, reason)
        if _sv_170 is None:
            return (20, reason)

        if (_sv_172 := _selector_side(
        'sv4_172_label',
        bool("dynamic_router_refused" in normalized),
        'label',
        'other_side',
        'Condition: "dynamic_router_refused" in normalized. Which side of this condition is the decision?',
        true_text='The label on this side is label.',
        false_text='The label on the other side is other_side.',
    )) == "true":
            return (50, reason)
        if _sv_172 is None:
            return (20, reason)

        if (_sv_174 := _selector_side(
        'sv4_174_label',
        bool("off_configured_session" in normalized),
        'label',
        'other_side',
        'Condition: "off_configured_session" in normalized. Which side of this condition is the decision?',
        true_text='The label on this side is label.',
        false_text='The label on the other side is other_side.',
    )) == "true":
            return (60, reason)
        if _sv_174 is None:
            return (20, reason)

        return (20, reason)

    return min(unique, key=priority)


def _selector_hash_digest(payload: Any) -> str:
    material = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _compact_selector_hash_shape(value: Any, *, depth: int) -> dict[str, Any]:
    if isinstance(value, Mapping):
        keys = sorted(str(key) for key in value.keys())
        scalar_sample: dict[str, Any] = {}
        for key in sorted(value.keys(), key=lambda item: str(item))[:20]:
            item = value.get(key)
            if item is None or isinstance(item, (str, int, float, bool)):
                scalar_sample[str(key)] = _compact_selector_hash_payload(
                    item,
                    depth=depth + 1,
                )
        summary = {
            "payload_compacted_for_selector_hash": True,
            "payload_compaction_reason": "large_mapping_shape",
            "payload_type": "mapping",
            "key_count": len(value),
            "keys_sample": keys[:50],
            "scalar_sample": scalar_sample,
        }
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        item_sample: list[str] = []
        for item in islice(value, 20):
            if isinstance(item, Mapping):
                item_sample.append(
                    str(
                        item.get("candidate_id")
                        or item.get("simulated_order_id")
                        or item.get("id")
                        or item.get("row_type")
                        or ""
                    )
                )
            elif item is None or isinstance(item, (str, int, float, bool)):
                item_sample.append(str(item)[:80])
            else:
                item_sample.append(type(item).__name__)
        summary = {
            "payload_compacted_for_selector_hash": True,
            "payload_compaction_reason": "large_sequence_shape",
            "payload_type": type(value).__name__,
            "item_count": len(value),
            "item_id_sample": [item for item in item_sample if item],
        }
    else:
        summary = {
            "payload_compacted_for_selector_hash": True,
            "payload_compaction_reason": "large_text_or_object_shape",
            "payload_type": type(value).__name__,
        }
    summary["payload_shape_hash_sha256"] = _selector_hash_digest(summary)
    return summary


def _compact_selector_hash_payload(value: Any, *, depth: int = 0) -> Any:
    if value is None or isinstance(value, (int, float, bool)):
        return value
    if isinstance(value, str):
        if len(value.encode("utf-8")) <= SELECTOR_HASH_MAX_TEXT_BYTES:
            return value
        return {
            "payload_compacted_for_selector_hash": True,
            "payload_compaction_reason": "large_text",
            "text_bytes": len(value.encode("utf-8")),
            "text_hash_sha256": hashlib.sha256(value.encode("utf-8")).hexdigest(),
            "text_prefix": value[:120],
        }
    if isinstance(value, bytes):
        if len(value) <= SELECTOR_HASH_MAX_TEXT_BYTES:
            return value.decode("utf-8", errors="replace")
        return {
            "payload_compacted_for_selector_hash": True,
            "payload_compaction_reason": "large_bytes",
            "byte_count": len(value),
            "bytes_hash_sha256": hashlib.sha256(value).hexdigest(),
        }
    if depth >= SELECTOR_HASH_MAX_DEPTH:
        return _compact_selector_hash_shape(value, depth=depth)
    if isinstance(value, Mapping):
        if len(value) > SELECTOR_HASH_MAX_COLLECTION_ITEMS:
            return _compact_selector_hash_shape(value, depth=depth)
        compacted: dict[str, Any] = {}
        for key in sorted(value.keys(), key=lambda item: str(item)):
            key_text = str(key)
            item = value.get(key)
            if key_text in {
                "all_options_preserved",
                "component_scores",
                "rejected_alternatives",
                "source_records",
                "sources",
                "ultimate_candidate_package",
            }:
                compacted[key_text] = _compact_selector_hash_shape(
                    item,
                    depth=depth + 1,
                )
                continue
            compacted[key_text] = _compact_selector_hash_payload(
                item,
                depth=depth + 1,
            )
        return compacted
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        if len(value) > SELECTOR_HASH_MAX_COLLECTION_ITEMS:
            return _compact_selector_hash_shape(value, depth=depth)
        return [
            _compact_selector_hash_payload(item, depth=depth + 1)
            for item in value
        ]
    return _compact_selector_hash_shape(value, depth=depth)


def _stable_sha256(payload: Any) -> str:
    return _selector_hash_digest(_compact_selector_hash_payload(payload))


def _selector_packet_hash_payload(record: Mapping[str, Any]) -> dict[str, Any]:
    compacted = {
        key: value
        for key, value in record.items()
        if key not in {"packet_hash_sha256"}
    }
    compacted["component_scores"] = _compact_selector_hash_payload(
        record.get("component_scores") or {}
    )
    return compacted


def _selector_source_event_hash_payload(record: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "component_scores": _compact_selector_hash_payload(
            record.get("component_scores") or {}
        ),
        "semantic_owner_handoffs": record.get("semantic_owner_handoffs"),
        "ignored_forbidden_fields": record.get("ignored_forbidden_fields"),
    }


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def _lower(value: Any) -> str:
    return _text(value).strip().lower().replace("_", "-")


def _upper(value: Any) -> str:
    return _text(value).strip().upper()


def _float(value: Any) -> float | None:
    if value in (None, "") or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return _lower(value) in {"1", "true", "yes", "y", "enabled", "on"}


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _score01(value: Any) -> float | None:
    if isinstance(value, Mapping):
        for key in (
            "score",
            "freshness_score",
            "reliability_score",
            "cost_sensitivity_score",
            "source_completeness_score",
            "confidence",
            "value",
        ):
            if key in value:
                return _score01(value.get(key))
        status = _lower(value.get("status"))
        if status in {
            "complete",
            "timestamp-present",
            "fresh",
            "high",
            "verified",
            "reliability-metric-present",
        }:
            return 1.0
        if status in {"partial", "mixed", "bounded"}:
            return 0.5
        if status in {"missing", "source-gap", "stale", "low"}:
            return 0.0
        return None
    raw = _float(value)
    if raw is not None:
        if 1.0 < raw <= 100.0:
            raw = raw / 100.0
        return _clamp(raw, 0.0, 1.0)
    token = _lower(value)
    if not token:
        return None
    if token in {"complete", "fresh", "high", "verified", "source-complete"}:
        return 1.0
    if token in {"medium", "mixed", "partial", "bounded"}:
        return 0.5
    if token in {"low", "stale", "missing", "gap", "source-gap", "blocked"}:
        return 0.0
    return None


def _first_score01(*values: Any) -> float | None:
    for value in values:
        score = _score01(value)
        if score is not None:
            return score
    return None


def _max_score01(*values: Any) -> float | None:
    scores = [score for value in values if (score := _score01(value)) is not None]
    return max(scores) if scores else None


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _first_mapping(event: Mapping[str, Any], *keys: str) -> Mapping[str, Any]:
    for key in keys:
        value = event.get(key)
        if isinstance(value, Mapping):
            return value
    return {}


def _first_value(mapping: Mapping[str, Any], *keys: str) -> Any:
    if mapping is None:
        return None
    get_value = getattr(mapping, "get", None)
    if get_value is None:
        return None
    for key in keys:
        value = get_value(key)
        if value not in (None, ""):
            return value
    return None


def _first_present_value(*values: Any) -> Any:
    for value in values:
        if value not in (None, ""):
            return value
    return None


def _candidate_decision_inputs(event: Mapping[str, Any]) -> Mapping[str, Any]:
    direct = _first_mapping(event, "candidate_decision_inputs")
    if direct:
        return direct
    score_components = _first_mapping(event, "score_components")
    return _first_mapping(score_components, "candidate_decision_inputs")


def _complete_execution_fillability_atom(
    *surfaces: Mapping[str, Any],
) -> dict[str, Any]:
    """Select one complete value/provenance tuple without cross-stitching."""

    for surface in surfaces:
        if not isinstance(surface, Mapping):
            continue
        nested = _mapping(surface.get("predecision_limit_fillability"))
        value = _float(surface.get("execution_fill_probability"))
        nested_value = _float(
            _first_value(
                nested,
                "fill_probability",
                "expected_fill_probability",
                "limit_fill_probability",
            )
        )
        if value is None:
            value = nested_value
        if value is None:
            continue
        nested_matches = bool(
            nested_value is not None
            and abs(float(value) - float(nested_value)) <= 1e-12
        )
        source = _text(surface.get("execution_fill_probability_source")).strip()
        source_time = _first_present_value(
            surface.get("execution_fill_probability_source_time_utc"),
            nested.get("current_price_source_time_utc") if nested_matches else None,
            nested.get("source_time_utc") if nested_matches else None,
        )
        source_boundary = _first_present_value(
            surface.get("execution_fill_probability_source_boundary"),
            nested.get("current_price_source_boundary") if nested_matches else None,
            nested.get("source_boundary") if nested_matches else None,
        )
        authority_class = _text(
            surface.get("execution_fill_probability_authority_class")
        ).strip()
        if nested_matches:
            source = source or _text(
                _first_present_value(
                    nested.get("execution_fill_probability_source"),
                    nested.get("fill_probability_source"),
                    "predecision_limit_fillability.fill_probability",
                )
            ).strip()
            authority_class = authority_class or _text(
                _first_present_value(
                    nested.get("execution_fill_probability_authority_class"),
                    nested.get("fill_probability_authority_class"),
                    "predecision_passive_limit_fillability_authority",
                )
            ).strip()
        if not source or source_time in (None, "") or source_boundary in (None, ""):
            continue
        clamped_value = _clamp(float(value), 0.0, 1.0)
        atom = {
            "execution_fill_probability": clamped_value,
            "limit_fillability_probability": clamped_value,
            "predecision_limit_fillability_probability": clamped_value,
            "execution_fill_probability_source": source,
            "execution_fill_probability_source_time_utc": source_time,
            "execution_fill_probability_source_boundary": source_boundary,
            "execution_fill_probability_authority_class": (
                authority_class or "predecision_execution_fillability_alias"
            ),
            "execution_fillability_atomic_surface": (
                surface.get("execution_fillability_atomic_surface")
                or "selector_v4.complete_execution_fillability_atom"
            ),
            "execution_fillability_atomic_failure": None,
            "execution_fillability_atomic_conflicts": [],
        }
        for key in (
            "execution_fill_probability_authority_hash_sha256",
            "execution_fillability_signed_value_selected",
        ):
            if surface.get(key) not in (None, ""):
                atom[key] = surface.get(key)
        if nested:
            atom["predecision_limit_fillability"] = dict(nested)
        return atom
    return {}


PACKAGE_NEW_ENTRY_AUTHORITY_HASH_FIELDS = (
    "package_new_entry_authority_hash_sha256",
    "new_entry_authority_hash_sha256",
    "replay_new_entry_authority_hash_sha256",
)
EXPECTED_PACKAGE_NEW_ENTRY_AUTHORITY_HASH_FIELDS = (
    "expected_package_new_entry_authority_hash_sha256",
    "expected_new_entry_authority_hash_sha256",
    "expected_replay_new_entry_authority_hash_sha256",
)
PACKAGE_NEW_ENTRY_AUTHORITY_SOURCE_BOUNDARY_FIELDS = (
    "package_new_entry_authority_source_boundary",
    "new_entry_authority_source_boundary",
    "replay_new_entry_authority_source_boundary",
)
PACKAGE_NEW_ENTRY_AUTHORITY_USES_OUTCOME_FIELDS = (
    "package_new_entry_authority_uses_outcome_fields",
    "new_entry_authority_uses_outcome_fields",
    "replay_new_entry_authority_uses_outcome_fields",
)
PACKAGE_NEW_ENTRY_AUTHORITY_CANDIDATE_ID_FIELDS = (
    "package_new_entry_authority_candidate_id",
    "new_entry_authority_candidate_id",
    "replay_new_entry_authority_candidate_id",
)
PACKAGE_NEW_ENTRY_AUTHORITY_DECISION_TIME_FIELDS = (
    "package_new_entry_authority_decision_time_utc",
    "new_entry_authority_decision_time_utc",
    "replay_new_entry_authority_decision_time_utc",
)
PACKAGE_NEW_ENTRY_AUTHORITY_CANONICAL_INSTANCE_KEY_FIELDS = (
    "package_new_entry_authority_canonical_replay_candidate_instance_key",
    "new_entry_authority_canonical_replay_candidate_instance_key",
    "replay_new_entry_authority_canonical_replay_candidate_instance_key",
)
PACKAGE_NEW_ENTRY_AUTHORITY_SOURCE_BOUND_INSTANCE_KEY_FIELDS = (
    "package_new_entry_authority_source_bound_replay_candidate_instance_key",
    "new_entry_authority_source_bound_replay_candidate_instance_key",
    "replay_new_entry_authority_source_bound_replay_candidate_instance_key",
)


def _sha256_hex(value: str) -> bool:
    if len(value) != 64:
        return False
    return all(char in "009abcdefABCDEF" for char in value)


def _replay_candidate_instance_key(candidate_id: str, decision_time: str) -> str:
    if not candidate_id or not decision_time:
        return ""
    return f"{candidate_id}@@{decision_time}"


def _package_new_entry_signed_authority_detail(
    event: Mapping[str, Any],
    decision_inputs: Mapping[str, Any],
    ultimate_package: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Return predecision package new-entry signature status for replay authority.

    The selector may soften package fill-floor rejects only when the row already
    carries a signed package new-entry authority hash. Later scheduler/timewarp
    stages can still materialize and sign candidates; until then selector-level
    fill-floor softening remains diagnostic instead of risk-bearing.
    """

    from src.research.moonshot_scheduler_v4_best_trade_allocator import (
        PACKAGE_NEW_ENTRY_AUTHORITY_IMMUTABLE_PAYLOAD_CONTRACT,
        PACKAGE_NEW_ENTRY_AUTHORITY_PAYLOAD_SCHEMA,
        package_new_entry_authority_payload_hash_sha256,
        package_new_entry_authority_scope_for_action_intent,
    )

    sources: tuple[tuple[str, Mapping[str, Any]], ...] = (
        ("event", event),
        ("candidate_decision_inputs", decision_inputs),
        ("ultimate_candidate_package", ultimate_package or {}),
    )
    current_candidate_id_hint = _text(
        _first_present_value(
            _first_value(event, "candidate_id", "replay_candidate_id"),
            _first_value(decision_inputs, "candidate_id", "replay_candidate_id"),
            _first_value(ultimate_package or {}, "candidate_id", "replay_candidate_id"),
        )
    )
    current_decision_time_hint = _text(
        _first_present_value(
            _first_value(
                event,
                "decision_time_utc",
                "candle_close_utc",
                "source_candle_time_utc",
            ),
            _first_value(
                decision_inputs,
                "decision_time_utc",
                "candle_close_utc",
                "source_candle_time_utc",
            ),
            _first_value(
                ultimate_package or {},
                "decision_time_utc",
                "candle_close_utc",
                "source_candle_time_utc",
            ),
        )
    )

    nested_authority_fields = (
        "ultimate_candidate_package_open_reduced_risk_authority",
        "ultimate_candidate_package_reduce_risk_authority",
        "ultimate_candidate_package_reduced_risk_authority",
        "selector_reduced_risk_new_position_signed_authority",
        "package_new_entry_authority",
        "signed_new_entry_authority",
        "candidate_decision_inputs",
        "scheduler_candidate_decision_inputs",
        "score_components",
        "component_scores",
        "selector_packet",
    )

    def candidate_authority_surfaces(
        source_name: str,
        root: Mapping[str, Any],
    ) -> list[tuple[str, Mapping[str, Any]]]:
        pending: list[tuple[str, Mapping[str, Any]]] = [(source_name, root)]
        seen: set[int] = set()
        found: list[tuple[str, Mapping[str, Any]]] = []
        while pending:
            path, candidate_surface = pending.pop(0)
            if id(candidate_surface) in seen:
                continue
            seen.add(id(candidate_surface))
            found.append((path, candidate_surface))
            for nested_field in nested_authority_fields:
                nested = candidate_surface.get(nested_field)
                if isinstance(nested, Mapping):
                    pending.append((f"{path}.{nested_field}", nested))
        return found

    def independently_valid_envelope(candidate_surface: Mapping[str, Any]) -> bool:
        payload = candidate_surface.get("package_new_entry_authority_payload")
        if not isinstance(payload, Mapping):
            return False
        authority_hash = _text(
            _first_value(candidate_surface, *PACKAGE_NEW_ENTRY_AUTHORITY_HASH_FIELDS)
        )
        expected_hash = _text(
            _first_value(
                candidate_surface,
                *EXPECTED_PACKAGE_NEW_ENTRY_AUTHORITY_HASH_FIELDS,
            )
        )
        payload_hash = package_new_entry_authority_payload_hash_sha256(payload)
        payload_candidate_id = _text(payload.get("candidate_id"))
        payload_decision_time = _text(payload.get("decision_time_utc"))
        payload_instance_key = _replay_candidate_instance_key(
            payload_candidate_id,
            payload_decision_time,
        )
        payload_action = _text(payload.get("target_action_intent"))
        status = _text(
            _first_present_value(
                candidate_surface.get("package_new_entry_authority_status"),
                candidate_surface.get("status"),
            )
        )
        required = _truthy(
            _first_present_value(
                candidate_surface.get("package_new_entry_authority_required"),
                candidate_surface.get("required"),
            )
        )
        valid = _truthy(
            _first_present_value(
                candidate_surface.get("package_new_entry_authority_valid"),
                candidate_surface.get("valid"),
            )
        )
        failures = _first_present_value(
            candidate_surface.get("package_new_entry_authority_failures"),
            candidate_surface.get("failures"),
        )
        return bool(
            required
            and valid
            and status == "valid_signed_predecision_new_entry_authority"
            and not failures
            and authority_hash == payload_hash
            and expected_hash == payload_hash
            and candidate_surface.get("package_new_entry_authority_payload_contract")
            == PACKAGE_NEW_ENTRY_AUTHORITY_IMMUTABLE_PAYLOAD_CONTRACT
            and payload.get("payload_contract")
            == PACKAGE_NEW_ENTRY_AUTHORITY_IMMUTABLE_PAYLOAD_CONTRACT
            and payload.get("payload_schema")
            == PACKAGE_NEW_ENTRY_AUTHORITY_PAYLOAD_SCHEMA
            and payload.get("scope")
            == package_new_entry_authority_scope_for_action_intent(payload_action)
            and _predecision_no_outcome_boundary(payload.get("source_boundary"))
            and payload.get("uses_outcome_fields") is False
            and payload.get("authority_applies") is True
            and payload.get("authority_allowed") is True
            and payload_instance_key
            and payload.get("canonical_replay_candidate_instance_key")
            == payload_instance_key
            and payload.get("source_bound_replay_candidate_instance_key")
            == payload_instance_key
            and payload.get("candidate_instance_identity_status") == "materialized"
            and (
                not current_candidate_id_hint
                or payload_candidate_id == current_candidate_id_hint
            )
            and (
                not current_decision_time_hint
                or payload_decision_time == current_decision_time_hint
            )
        )

    authority_surface: Mapping[str, Any] = {}
    authority_surface_source = ""
    hash_only_surface: Mapping[str, Any] = {}
    hash_only_surface_source = ""
    first_payload_surface: Mapping[str, Any] = {}
    first_payload_surface_source = ""
    for source_name, source in sources:
        for candidate_source, candidate_surface in candidate_authority_surfaces(
            source_name,
            source,
        ):
            if not hash_only_surface and _first_value(
                candidate_surface,
                *PACKAGE_NEW_ENTRY_AUTHORITY_HASH_FIELDS,
            ) not in (None, ""):
                hash_only_surface = candidate_surface
                hash_only_surface_source = candidate_source
            if isinstance(
                candidate_surface.get("package_new_entry_authority_payload"),
                Mapping,
            ):
                if not first_payload_surface:
                    first_payload_surface = candidate_surface
                    first_payload_surface_source = candidate_source
                if independently_valid_envelope(candidate_surface):
                    authority_surface = candidate_surface
                    authority_surface_source = candidate_source
                    break
        if authority_surface:
            break
    if not authority_surface:
        authority_surface = first_payload_surface or hash_only_surface
        authority_surface_source = (
            first_payload_surface_source or hash_only_surface_source
        )

    authority_hash = _text(
        _first_value(authority_surface, *PACKAGE_NEW_ENTRY_AUTHORITY_HASH_FIELDS)
    )
    expected_hash = _text(
        _first_value(
            authority_surface,
            *EXPECTED_PACKAGE_NEW_ENTRY_AUTHORITY_HASH_FIELDS,
        )
    )
    source_boundary = _text(
        _first_value(
            authority_surface,
            *PACKAGE_NEW_ENTRY_AUTHORITY_SOURCE_BOUNDARY_FIELDS,
        )
    )
    uses_outcome_fields = _first_value(
        authority_surface,
        *PACKAGE_NEW_ENTRY_AUTHORITY_USES_OUTCOME_FIELDS,
    )
    signed_candidate_id = _text(
        _first_value(
            authority_surface,
            *PACKAGE_NEW_ENTRY_AUTHORITY_CANDIDATE_ID_FIELDS,
        )
    )
    signed_decision_time = _text(
        _first_value(
            authority_surface,
            *PACKAGE_NEW_ENTRY_AUTHORITY_DECISION_TIME_FIELDS,
        )
    )
    signed_canonical_instance_key = _text(
        _first_value(
            authority_surface,
            *PACKAGE_NEW_ENTRY_AUTHORITY_CANONICAL_INSTANCE_KEY_FIELDS,
        )
    )
    signed_source_bound_instance_key = _text(
        _first_value(
            authority_surface,
            *PACKAGE_NEW_ENTRY_AUTHORITY_SOURCE_BOUND_INSTANCE_KEY_FIELDS,
        )
    )
    current_candidate_id = _text(
        _first_present_value(
            _first_value(event, "candidate_id", "replay_candidate_id"),
            _first_value(decision_inputs, "candidate_id", "replay_candidate_id"),
            _first_value(ultimate_package or {}, "candidate_id", "replay_candidate_id"),
        )
    )
    current_decision_time = _text(
        _first_present_value(
            _first_value(
                event,
                "decision_time_utc",
                "candle_close_utc",
                "source_candle_time_utc",
            ),
            _first_value(
                decision_inputs,
                "decision_time_utc",
                "candle_close_utc",
                "source_candle_time_utc",
            ),
            _first_value(
                ultimate_package or {},
                "decision_time_utc",
                "candle_close_utc",
                "source_candle_time_utc",
            ),
        )
    )
    current_canonical_instance_key = _text(
        _first_present_value(
            _first_value(event, "canonical_replay_candidate_instance_key"),
            _first_value(decision_inputs, "canonical_replay_candidate_instance_key"),
            _first_value(ultimate_package or {}, "canonical_replay_candidate_instance_key"),
            _replay_candidate_instance_key(current_candidate_id, current_decision_time),
        )
    )
    current_source_bound_instance_key = _text(
        _first_present_value(
            _first_value(event, "source_bound_replay_candidate_instance_key"),
            _first_value(decision_inputs, "source_bound_replay_candidate_instance_key"),
            _first_value(
                ultimate_package or {},
                "source_bound_replay_candidate_instance_key",
            ),
            _replay_candidate_instance_key(current_candidate_id, current_decision_time),
        )
    )
    failures: list[str] = []
    declared_required = _truthy(
        _first_present_value(
            authority_surface.get("package_new_entry_authority_required"),
            authority_surface.get("required"),
        )
    )
    declared_valid = _truthy(
        _first_present_value(
            authority_surface.get("package_new_entry_authority_valid"),
            authority_surface.get("valid"),
        )
    )
    declared_status = _text(
        _first_present_value(
            authority_surface.get("package_new_entry_authority_status"),
            authority_surface.get("status"),
        )
    )
    declared_failures = _first_present_value(
        authority_surface.get("package_new_entry_authority_failures"),
        authority_surface.get("failures"),
    )
    if (_sv_903 := _selector_side(
        'sv4_903_package_new_entry_authority_required_not_true',
        bool(not declared_required),
        'package_new_entry_authority_required_not_true',
        'other_side',
        'Condition: not declared_required. Which side of this condition is the decision?',
        true_text='package_new_entry_authority_required_not_true rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true":
        failures.append("package_new_entry_authority_required_not_true")
    if (_sv_905 := _selector_side(
        'sv4_905_package_new_entry_authority_valid_not_true',
        bool(not declared_valid),
        'package_new_entry_authority_valid_not_true',
        'other_side',
        'Condition: not declared_valid. Which side of this condition is the decision?',
        true_text='package_new_entry_authority_valid_not_true rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true":
        failures.append("package_new_entry_authority_valid_not_true")
    if (_sv_907 := _selector_side(
        'sv4_907_package_new_entry_authority_status_invalid',
        bool(declared_status != "valid_signed_predecision_new_entry_authority"),
        'package_new_entry_authority_status_invalid',
        'other_side',
        'Condition: declared_status != "valid_signed_predecision_new_entry_authority". Which side of this condition is the decision?',
        true_text='package_new_entry_authority_status_invalid rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true":
        failures.append("package_new_entry_authority_status_invalid")
    if (_sv_909 := _selector_side(
        'sv4_909_package_new_entry_authority_declared_failures_pr',
        bool(declared_failures),
        'package_new_entry_authority_declared_failures_pr',
        'other_side',
        'Condition: declared_failures. Which side of this condition is the decision?',
        true_text='package_new_entry_authority_declared_failures_pr rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true":
        failures.append("package_new_entry_authority_declared_failures_present")
    signed_payload = authority_surface.get("package_new_entry_authority_payload")
    if not isinstance(signed_payload, Mapping):
        if _selector_side(
            'sv4_913_payload_missing',
            True,
            "payload_missing",
            "payload_missing_is_a_fact",
            'The signed payload is not a mapping. Which side of that condition is the decision?',
            true_text="The missing payload rejects this candidate.",
            false_text="The missing payload is a fact. It does not reject this candidate.",
        ) == "true":
            failures.append("package_new_entry_authority_payload_missing")
        signed_payload = {}
    else:
        payload_hash = package_new_entry_authority_payload_hash_sha256(
            signed_payload
        )
        if (
            (_sv_919 := _selector_side(
        'sv4_919_package_new_entry_authority_payload_contract_inv',
        bool(authority_surface.get("package_new_entry_authority_payload_contract")
            != PACKAGE_NEW_ENTRY_AUTHORITY_IMMUTABLE_PAYLOAD_CONTRACT
            or signed_payload.get("payload_contract")
            != PACKAGE_NEW_ENTRY_AUTHORITY_IMMUTABLE_PAYLOAD_CONTRACT),
        'package_new_entry_authority_payload_contract_inv',
        'other_side',
        'Condition: authority_surface.get("package_new_entry_authority_payload_contract")\n            != PACKAGE_NEW_ENTRY_AUTHORITY_IMMUTABLE_PAYLOAD_CONTRACT\n            or signed_payload.get("payload_contract")\n            != PACKAGE_NEW. Which side of this condition is the decision?',
        true_text='package_new_entry_authority_payload_contract_inv rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true"
        ):
            failures.append("package_new_entry_authority_payload_contract_invalid")
        if (
            (_sv_926 := _selector_side(
        'sv4_926_package_new_entry_authority_payload_schema_inval',
        bool(signed_payload.get("payload_schema")
            != PACKAGE_NEW_ENTRY_AUTHORITY_PAYLOAD_SCHEMA),
        'package_new_entry_authority_payload_schema_inval',
        'other_side',
        'Condition: signed_payload.get("payload_schema")\n            != PACKAGE_NEW_ENTRY_AUTHORITY_PAYLOAD_SCHEMA. Which side of this condition is the decision?',
        true_text='package_new_entry_authority_payload_schema_inval rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true"
        ):
            failures.append("package_new_entry_authority_payload_schema_invalid")
        if (_sv_931 := _selector_side(
        'sv4_931_package_new_entry_authority_payload_hash_mismatc',
        bool(authority_hash != payload_hash or expected_hash != payload_hash),
        'package_new_entry_authority_payload_hash_mismatc',
        'other_side',
        'Condition: authority_hash != payload_hash or expected_hash != payload_hash. Which side of this condition is the decision?',
        true_text='package_new_entry_authority_payload_hash_mismatc rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true":
            failures.append("package_new_entry_authority_payload_hash_mismatch")
        payload_action = _text(signed_payload.get("target_action_intent"))
        if (
            (_sv_934 := _selector_side(
        'sv4_934_package_new_entry_authority_payload_scope_invali',
        bool(not payload_action
            or signed_payload.get("scope")
            != package_new_entry_authority_scope_for_action_intent(payload_action)),
        'package_new_entry_authority_payload_scope_invali',
        'other_side',
        'Condition: not payload_action\n            or signed_payload.get("scope")\n            != package_new_entry_authority_scope_for_action_intent(payload_action). Which side of this condition is the decision?',
        true_text='package_new_entry_authority_payload_scope_invali rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true"
        ):
            failures.append("package_new_entry_authority_payload_scope_invalid")
        payload_boundary = _text(signed_payload.get("source_boundary"))
        if (
            (_sv_941 := _selector_side(
        'sv4_941_package_new_entry_authority_payload_boundary_inv',
        bool(not _predecision_no_outcome_boundary(payload_boundary)
            or signed_payload.get("uses_outcome_fields") is not False
            or signed_payload.get("authority_applies") is not True
            or signed_payload.get("authority_allowed") is not True),
        'package_new_entry_authority_payload_boundary_inv',
        'other_side',
        'Condition: not _predecision_no_outcome_boundary(payload_boundary)\n            or signed_payload.get("uses_outcome_fields") is not False\n            or signed_payload.get("authority_applies") is not True\n            or signed_payloa. Which side of this condition is the decision?',
        true_text='package_new_entry_authority_payload_boundary_inv rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true"
        ):
            failures.append("package_new_entry_authority_payload_boundary_invalid")
        for projected_value, payload_key in (
            (signed_candidate_id, "candidate_id"),
            (signed_decision_time, "decision_time_utc"),
            (
                signed_canonical_instance_key,
                "canonical_replay_candidate_instance_key",
            ),
            (
                signed_source_bound_instance_key,
                "source_bound_replay_candidate_instance_key",
            ),
            (source_boundary, "source_boundary"),
        ):
            if (_sv_961 := _selector_side(
        'sv4_961_package_new_entry_authority_payload_projection_m',
        bool(_text(signed_payload.get(payload_key)) != projected_value),
        'package_new_entry_authority_payload_projection_m',
        'other_side',
        'Condition: _text(signed_payload.get(payload_key)) != projected_value. Which side of this condition is the decision?',
        true_text='package_new_entry_authority_payload_projection_m rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true":
                failures.append(
                    f"package_new_entry_authority_payload_projection_mismatch:{payload_key}"
                )
    if (_sv_965 := _selector_side(
        'sv4_965_package_new_entry_authority_hash_missing',
        bool(not authority_hash),
        'package_new_entry_authority_hash_missing',
        'other_side',
        'Condition: not authority_hash. Which side of this condition is the decision?',
        true_text='package_new_entry_authority_hash_missing rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true":
        failures.append("package_new_entry_authority_hash_missing")
    elif _sv_965 is not None and (_sv_965 := _selector_side(
        'sv4_967_package_new_entry_authority_hash_not_sha256_hex',
        bool(not _sha256_hex(authority_hash)),
        'package_new_entry_authority_hash_not_sha256_hex',
        'other_side',
        'Condition: not _sha256_hex(authority_hash). Which side of this condition is the decision?',
        true_text='package_new_entry_authority_hash_not_sha256_hex rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true":
        failures.append("package_new_entry_authority_hash_not_sha256_hex")
    if (_sv_969 := _selector_side(
        'sv4_969_expected_package_new_entry_authority_hash_missin',
        bool(not expected_hash),
        'expected_package_new_entry_authority_hash_missin',
        'other_side',
        'Condition: not expected_hash. Which side of this condition is the decision?',
        true_text='expected_package_new_entry_authority_hash_missin rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true":
        failures.append("expected_package_new_entry_authority_hash_missing")
    elif _sv_969 is not None and (_sv_969 := _selector_side(
        'sv4_971_expected_package_new_entry_authority_hash_not_sh',
        bool(not _sha256_hex(expected_hash)),
        'expected_package_new_entry_authority_hash_not_sh',
        'other_side',
        'Condition: not _sha256_hex(expected_hash). Which side of this condition is the decision?',
        true_text='expected_package_new_entry_authority_hash_not_sh rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true":
        failures.append("expected_package_new_entry_authority_hash_not_sha256_hex")
    if (_sv_973 := _selector_side(
        'sv4_973_package_new_entry_authority_hash_mismatch',
        bool(authority_hash and expected_hash and authority_hash != expected_hash),
        'package_new_entry_authority_hash_mismatch',
        'other_side',
        'Condition: authority_hash and expected_hash and authority_hash != expected_hash. Which side of this condition is the decision?',
        true_text='package_new_entry_authority_hash_mismatch rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true":
        failures.append("package_new_entry_authority_hash_mismatch")
    if (_sv_975 := _selector_side(
        'sv4_975_package_new_entry_authority_candidate_id_missing',
        bool(not signed_candidate_id),
        'package_new_entry_authority_candidate_id_missing',
        'other_side',
        'Condition: not signed_candidate_id. Which side of this condition is the decision?',
        true_text='package_new_entry_authority_candidate_id_missing rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true":
        failures.append("package_new_entry_authority_candidate_id_missing")
    elif _sv_975 is not None and (_sv_975 := _selector_side(
        'sv4_977_current_candidate_id_missing',
        bool(not current_candidate_id),
        'current_candidate_id_missing',
        'other_side',
        'Condition: not current_candidate_id. Which side of this condition is the decision?',
        true_text='current_candidate_id_missing rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true":
        failures.append("current_candidate_id_missing")
    elif _sv_975 is not None and (_sv_975 := _selector_side(
        'sv4_979_package_new_entry_authority_candidate_id_mismatc',
        bool(signed_candidate_id != current_candidate_id),
        'package_new_entry_authority_candidate_id_mismatc',
        'other_side',
        'Condition: signed_candidate_id != current_candidate_id. Which side of this condition is the decision?',
        true_text='package_new_entry_authority_candidate_id_mismatc rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true":
        failures.append("package_new_entry_authority_candidate_id_mismatch")
    if (_sv_981 := _selector_side(
        'sv4_981_package_new_entry_authority_decision_time_utc_mi',
        bool(not signed_decision_time),
        'package_new_entry_authority_decision_time_utc_mi',
        'other_side',
        'Condition: not signed_decision_time. Which side of this condition is the decision?',
        true_text='package_new_entry_authority_decision_time_utc_mi rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true":
        failures.append("package_new_entry_authority_decision_time_utc_missing")
    elif _sv_981 is not None and (_sv_981 := _selector_side(
        'sv4_983_current_decision_time_utc_missing',
        bool(not current_decision_time),
        'current_decision_time_utc_missing',
        'other_side',
        'Condition: not current_decision_time. Which side of this condition is the decision?',
        true_text='current_decision_time_utc_missing rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true":
        failures.append("current_decision_time_utc_missing")
    elif _sv_981 is not None and (_sv_981 := _selector_side(
        'sv4_985_package_new_entry_authority_decision_time_utc_mi',
        bool(signed_decision_time != current_decision_time),
        'package_new_entry_authority_decision_time_utc_mi',
        'other_side',
        'Condition: signed_decision_time != current_decision_time. Which side of this condition is the decision?',
        true_text='package_new_entry_authority_decision_time_utc_mi rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true":
        failures.append("package_new_entry_authority_decision_time_utc_mismatch")
    if (_sv_987 := _selector_side(
        'sv4_987_package_new_entry_authority_canonical_replay_can',
        bool(not signed_canonical_instance_key),
        'package_new_entry_authority_canonical_replay_can',
        'other_side',
        'Condition: not signed_canonical_instance_key. Which side of this condition is the decision?',
        true_text='package_new_entry_authority_canonical_replay_can rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true":
        failures.append(
            "package_new_entry_authority_canonical_replay_candidate_instance_key_missing"
        )
    elif _sv_987 is not None and (_sv_987 := _selector_side(
        'sv4_991_package_new_entry_authority_canonical_replay_can',
        bool(signed_canonical_instance_key != current_canonical_instance_key),
        'package_new_entry_authority_canonical_replay_can',
        'other_side',
        'Condition: signed_canonical_instance_key != current_canonical_instance_key. Which side of this condition is the decision?',
        true_text='package_new_entry_authority_canonical_replay_can rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true":
        failures.append(
            "package_new_entry_authority_canonical_replay_candidate_instance_key_mismatch"
        )
    if (_sv_995 := _selector_side(
        'sv4_995_package_new_entry_authority_source_bound_replay_',
        bool(not signed_source_bound_instance_key),
        'package_new_entry_authority_source_bound_replay_',
        'other_side',
        'Condition: not signed_source_bound_instance_key. Which side of this condition is the decision?',
        true_text='package_new_entry_authority_source_bound_replay_ rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true":
        failures.append(
            "package_new_entry_authority_source_bound_replay_candidate_instance_key_missing"
        )
    elif _sv_995 is not None and (_sv_995 := _selector_side(
        'sv4_999_package_new_entry_authority_source_bound_replay_',
        bool(signed_source_bound_instance_key != current_source_bound_instance_key),
        'package_new_entry_authority_source_bound_replay_',
        'other_side',
        'Condition: signed_source_bound_instance_key != current_source_bound_instance_key. Which side of this condition is the decision?',
        true_text='package_new_entry_authority_source_bound_replay_ rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true":
        failures.append(
            "package_new_entry_authority_source_bound_replay_candidate_instance_key_mismatch"
        )
    if (_sv_1003 := _selector_side(
        'sv4_1003_package_new_entry_authority_source_boundary_miss',
        bool(not source_boundary),
        'package_new_entry_authority_source_boundary_miss',
        'other_side',
        'Condition: not source_boundary. Which side of this condition is the decision?',
        true_text='package_new_entry_authority_source_boundary_miss rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true":
        failures.append("package_new_entry_authority_source_boundary_missing")
    elif _sv_1003 is not None and (_sv_1003 := _selector_side(
        'sv4_1005_package_new_entry_authority_source_boundary_not_',
        bool(not _predecision_no_outcome_boundary(source_boundary)),
        'package_new_entry_authority_source_boundary_not_',
        'other_side',
        'Condition: not _predecision_no_outcome_boundary(source_boundary). Which side of this condition is the decision?',
        true_text='package_new_entry_authority_source_boundary_not_ rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true":
        failures.append("package_new_entry_authority_source_boundary_not_predecision_no_outcome")
    if (_sv_1007 := _selector_side(
        'sv4_1007_package_new_entry_authority_uses_outcome_fields_',
        bool(uses_outcome_fields is not False),
        'package_new_entry_authority_uses_outcome_fields_',
        'other_side',
        'Condition: uses_outcome_fields is not False. Which side of this condition is the decision?',
        true_text='package_new_entry_authority_uses_outcome_fields_ rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true":
        failures.append("package_new_entry_authority_uses_outcome_fields_not_false")
    failure_priority = (
        "package_new_entry_authority_required_not_true",
        "package_new_entry_authority_valid_not_true",
        "package_new_entry_authority_status_invalid",
        "package_new_entry_authority_declared_failures_present",
        "package_new_entry_authority_hash_missing",
        "expected_package_new_entry_authority_hash_missing",
        "package_new_entry_authority_hash_not_sha256_hex",
        "expected_package_new_entry_authority_hash_not_sha256_hex",
        "package_new_entry_authority_hash_mismatch",
        "package_new_entry_authority_candidate_id_missing",
        "current_candidate_id_missing",
        "package_new_entry_authority_candidate_id_mismatch",
        "package_new_entry_authority_decision_time_utc_missing",
        "current_decision_time_utc_missing",
        "package_new_entry_authority_decision_time_utc_mismatch",
        "package_new_entry_authority_canonical_replay_candidate_instance_key_missing",
        "package_new_entry_authority_canonical_replay_candidate_instance_key_mismatch",
        "package_new_entry_authority_source_bound_replay_candidate_instance_key_missing",
        "package_new_entry_authority_source_bound_replay_candidate_instance_key_mismatch",
        "package_new_entry_authority_source_boundary_missing",
        "package_new_entry_authority_source_boundary_not_predecision_no_outcome",
        "package_new_entry_authority_uses_outcome_fields_not_false",
        "package_new_entry_authority_payload_missing",
        "package_new_entry_authority_payload_contract_invalid",
        "package_new_entry_authority_payload_schema_invalid",
        "package_new_entry_authority_payload_hash_mismatch",
        "package_new_entry_authority_payload_scope_invalid",
        "package_new_entry_authority_payload_boundary_invalid",
    )
    status = "package_new_entry_authority_hash_matched"
    if failures:
        status = next(
            (failure for failure in failure_priority if failure in failures),
            failures[0],
        )
    signed = not failures
    return {
        "signed": signed,
        "status": status,
        "failures": failures,
        "package_new_entry_authority_hash_sha256": authority_hash or None,
        "expected_package_new_entry_authority_hash_sha256": expected_hash or None,
        "authority_hash_source": authority_surface_source or None,
        "expected_hash_source": authority_surface_source or None,
        "source_boundary": source_boundary or None,
        "package_new_entry_authority_uses_outcome_fields": uses_outcome_fields,
        "package_new_entry_authority_candidate_id": signed_candidate_id or None,
        "package_new_entry_authority_decision_time_utc": signed_decision_time or None,
        "package_new_entry_authority_canonical_replay_candidate_instance_key": (
            signed_canonical_instance_key or None
        ),
        "package_new_entry_authority_source_bound_replay_candidate_instance_key": (
            signed_source_bound_instance_key or None
        ),
        "current_candidate_id": current_candidate_id or None,
        "current_decision_time_utc": current_decision_time or None,
        "current_canonical_replay_candidate_instance_key": (
            current_canonical_instance_key or None
        ),
        "current_source_bound_replay_candidate_instance_key": (
            current_source_bound_instance_key or None
        ),
        "package_new_entry_authority_payload": (
            dict(signed_payload) if signed and isinstance(signed_payload, Mapping) else None
        ),
    }


QUALITY_CONTRACT_FIELDS = (
    "expected_net_r",
    "probability",
    "confidence",
    "fill_probability",
    "source_completeness",
)
REQUIRED_QUALITY_CONTRACT_FIELDS = (
    "expected_net_r",
    "probability",
    "fill_probability",
    "source_completeness",
)
OPTIONAL_QUALITY_CONTRACT_FIELDS = ("confidence",)


def _predecision_no_outcome_boundary(value: Any) -> bool:
    text = _lower(value).replace("-", "_").replace(" ", "_")
    return bool("predecision" in text and "no_outcome" in text)


SELECTED_POLICY_AUTHORITY_FIELD_ALIASES = {
    "selected_policy_expected_net_calibration_status": (
        "package_new_entry_authority_selected_policy_expected_net_calibration_status",
        "selected_policy_expected_net_calibration_status",
        "selected_policy_expected_net_r_calibration_status",
        "expected_net_r_selected_policy_calibration_status",
    ),
    "selected_policy_expected_net_calibrated": (
        "package_new_entry_authority_selected_policy_expected_net_calibrated",
        "selected_policy_expected_net_calibrated",
        "selected_policy_expected_net_r_calibrated",
        "expected_net_r_selected_policy_calibrated",
    ),
    "selected_policy_expected_net_calibration_source_boundary": (
        "package_new_entry_authority_selected_policy_expected_net_calibration_source_boundary",
        "selected_policy_expected_net_calibration_source_boundary",
        "selected_policy_expected_net_calibration_boundary",
        "selected_policy_expected_net_r_calibration_source_boundary",
        "selected_policy_expected_net_r_calibration_boundary",
        "expected_net_r_selected_policy_calibration_boundary",
    ),
}


def _selected_policy_authority_value(
    key: str,
    *surfaces: Mapping[str, Any] | None,
) -> Any:
    aliases = SELECTED_POLICY_AUTHORITY_FIELD_ALIASES.get(key, (key,))
    for surface in surfaces:
        if not isinstance(surface, Mapping):
            continue
        for alias in aliases:
            value = surface.get(alias)
            if value not in (None, ""):
                return value
    return None


def _selected_policy_expected_net_calibration(
    *surfaces: Mapping[str, Any] | None,
) -> tuple[str, str, bool]:
    status = _lower(
        _selected_policy_authority_value(
            "selected_policy_expected_net_calibration_status",
            *surfaces,
        )
    ).replace("-", "_").replace(" ", "_")
    boundary = _text(
        _selected_policy_authority_value(
            "selected_policy_expected_net_calibration_source_boundary",
            *surfaces,
        )
    )
    explicit_calibrated = _truthy(
        _selected_policy_authority_value(
            "selected_policy_expected_net_calibrated",
            *surfaces,
        )
    )
    status_bad = bool(
        status
        and any(
            token in status
            for token in (
                "missing",
                "stale",
                "legacy",
                "uncalibrated",
                "mismatch",
                "diagnostic",
                "bridge_proxy",
                "not_required",
            )
        )
    )
    status_calibrated = bool(
        status
        and not status_bad
        and (
            "calibrated" in status
            or "owner_approved" in status
            or "aligned" in status
            or status.endswith("_present")
        )
    )
    boundary_ok = bool(not boundary or _predecision_no_outcome_boundary(boundary))
    return status, boundary, bool(boundary_ok and (explicit_calibrated or status_calibrated))


def _quality_contract_detail(surface: Mapping[str, Any]) -> dict[str, Any]:
    sources = dict(_mapping(surface.get("candidate_decision_quality_field_sources")))
    boundary = _text(surface.get("candidate_decision_quality_source_boundary"))
    alias_status = (
        _lower(surface.get("candidate_decision_quality_alias_status"))
        .replace("-", "_")
        .replace(" ", "_")
    )
    failures: list[str] = []
    warnings: list[str] = []
    required_sources_present = True
    for field in REQUIRED_QUALITY_CONTRACT_FIELDS:
        if (_sv_1201 := _selector_side(
        'sv4_1201_source_missing',
        bool(not _text(sources.get(field))),
        'source_missing',
        'other_side',
        'Condition: not _text(sources.get(field)). Which side of this condition is the decision?',
        true_text='source_missing rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true":
            failures.append(f"{field}_source_missing")
            required_sources_present = False
    for field in OPTIONAL_QUALITY_CONTRACT_FIELDS:
        source_label = _text(sources.get(field))
        if (_sv_1206 := _selector_side(
        'sv4_1206_source_inferred',
        bool(source_label and any(
            token in source_label.lower()
            for token in ("inferred", "heuristic", "fallback", "default")
        )),
        'source_inferred',
        'other_side',
        'Condition: source_label and any(\n            token in source_label.lower()\n            for token in ("inferred", "heuristic", "fallback", "default")\n        ). Which side of this condition is the decision?',
        true_text='This side stands: source_inferred.',
        false_text='The other side stands: other_side.',
    )) == "true":
            warnings.append(f"{field}_source_inferred:{source_label}")
    fill_probability_source = _text(sources.get("fill_probability"))
    if (_sv_1212 := _selector_side(
        'sv4_1212_fill_probability_source_is_execution_fillability',
        bool(fill_probability_source and any(
        token in fill_probability_source.lower()
        for token in (
            "predecision_limit_fillability",
            "limit_fillability",
            "execution_fill_probability",
            "pending_limit_fillability",
        )
    )),
        'fill_probability_source_is_execution_fillability',
        'other_side',
        'Condition: fill_probability_source and any(\n        token in fill_probability_source.lower()\n        for token in (\n            "predecision_limit_fillability",\n            "limit_fillability",\n            "execution_fill_probabili. Which side of this condition is the decision?',
        true_text='fill_probability_source_is_execution_fillability rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true":
        failures.append(
            "fill_probability_source_is_execution_fillability:"
            f"{fill_probability_source}"
        )
    boundary_is_predecision = True
    if (_sv_1226 := _selector_side(
        'sv4_1226_candidate_decision_quality_source_boundary_missi',
        bool(not boundary),
        'candidate_decision_quality_source_boundary_missi',
        'other_side',
        'Condition: not boundary. Which side of this condition is the decision?',
        true_text='candidate_decision_quality_source_boundary_missi rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true":
        failures.append("candidate_decision_quality_source_boundary_missing")
        boundary_is_predecision = False
    elif _sv_1226 is not None and (_sv_1226 := _selector_side(
        'sv4_1229_candidate_decision_quality_source_boundary_not_p',
        bool(not _predecision_no_outcome_boundary(boundary)),
        'candidate_decision_quality_source_boundary_not_p',
        'other_side',
        'Condition: not _predecision_no_outcome_boundary(boundary). Which side of this condition is the decision?',
        true_text='candidate_decision_quality_source_boundary_not_p rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true":
        failures.append("candidate_decision_quality_source_boundary_not_predecision")
        boundary_is_predecision = False
    if (_sv_1232 := _selector_side(
        'sv4_1232_candidate_decision_quality_alias_status',
        bool(alias_status not in {
        "exact_materialized",
        "exact_materialized_from_complete_predecision_quality_sources",
    } and not (
        alias_status == "materialized"
        and required_sources_present
        and boundary_is_predecision
    )),
        'candidate_decision_quality_alias_status',
        'other_side',
        'Condition: alias_status not in {\n        "exact_materialized",\n        "exact_materialized_from_complete_predecision_quality_sources",\n    } and not (\n        alias_status == "materialized"\n        and required_sources_present\n    . Which side of this condition is the decision?',
        true_text='candidate_decision_quality_alias_status rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true":
        failures.append(
            f"candidate_decision_quality_alias_status:{alias_status or 'missing'}"
        )
    for field in surface.get("candidate_decision_quality_alias_mismatches") or ():
        field_text = _text(field)
        if (_sv_1245 := _selector_side(
        'sv4_1245_candidate_decision_quality_alias_mismatch',
        bool(field_text),
        'candidate_decision_quality_alias_mismatch',
        'other_side',
        'Condition: field_text. Which side of this condition is the decision?',
        true_text='candidate_decision_quality_alias_mismatch rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true":
            failures.append(f"candidate_decision_quality_alias_mismatch:{field_text}")
    for failure in surface.get("candidate_decision_quality_provenance_failures") or ():
        failure_text = _text(failure)
        if (_sv_1249 := _selector_side(
        'sv4_1249_failures_append',
        bool(failure_text),
        'failures_append',
        'other_side',
        'Condition: failure_text. Which side of this condition is the decision?',
        true_text='failures_append rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true":
            failures.append(failure_text)
    for warning in surface.get(
        "candidate_decision_quality_optional_provenance_warnings"
    ) or ():
        warning_text = _text(warning)
        if (_sv_1255 := _selector_side(
        'sv4_1255_warnings_append',
        bool(warning_text),
        'warnings_append',
        'other_side',
        'Condition: warning_text. Which side of this condition is the decision?',
        true_text='This side stands: warnings_append.',
        false_text='The other side stands: other_side.',
    )) == "true":
            warnings.append(warning_text)
    return {
        "valid": not failures,
        "field_sources": sources,
        "source_boundary": boundary,
        "alias_status": alias_status,
        "failures": tuple(dict.fromkeys(failures)),
        "warnings": tuple(dict.fromkeys(warnings)),
    }


def _alias_value_present(value: Any) -> bool:
    return value is not None and value != "" and value != [] and value != {}


def _config(config: Mapping[str, Any] | None) -> Mapping[str, Any]:
    root = _mapping(config)
    runtime = root.get("gtos_vnext_runtime")
    return runtime if isinstance(runtime, Mapping) else root


def _candidate_side(event: Mapping[str, Any]) -> str:
    decision_inputs = _candidate_decision_inputs(event)
    side = _upper(
        _first_present_value(
            _first_value(event, "side", "direction", "candidate_side", "selected_side"),
            _first_value(decision_inputs, "side", "direction", "candidate_side", "selected_side"),
            _first_value(
                _first_mapping(event, "ultimate_candidate_package"),
                "side",
                "direction",
                "candidate_side",
                "selected_side",
            ),
            _first_value(
                _first_mapping(event, "ultimate_package"),
                "side",
                "direction",
                "candidate_side",
                "selected_side",
            ),
        )
    )
    if (_sv_1299 := _selector_side(
        'sv4_1299_long',
        bool(side in {"BUY", "BULL", "BULLISH", "LONG"}),
        'long',
        'other_side',
        'Condition: side in {"BUY", "BULL", "BULLISH", "LONG"}. Which side of this condition is the decision?',
        true_text='The label on this side is long.',
        false_text='The label on the other side is other_side.',
    )) == "true":
        return "LONG"
    if (_sv_1301 := _selector_side(
        'sv4_1301_short',
        bool(side in {"SELL", "BEAR", "BEARISH", "SHORT"}),
        'short',
        'other_side',
        'Condition: side in {"SELL", "BEAR", "BEARISH", "SHORT"}. Which side of this condition is the decision?',
        true_text='The label on this side is short.',
        false_text='The label on the other side is other_side.',
    )) == "true":
        return "SHORT"
    return side


def _direction(value: Any) -> str:
    text = _upper(value)
    if (_sv_1308 := _selector_side(
        'sv4_1308_long',
        bool(text in {"BUY", "BULL", "BULLISH", "LONG", "UP"}),
        'long',
        'other_side',
        'Condition: text in {"BUY", "BULL", "BULLISH", "LONG", "UP"}. Which side of this condition is the decision?',
        true_text='The label on this side is long.',
        false_text='The label on the other side is other_side.',
    )) == "true":
        return "LONG"
    if (_sv_1310 := _selector_side(
        'sv4_1310_short',
        bool(text in {"SELL", "BEAR", "BEARISH", "SHORT", "DOWN"}),
        'short',
        'other_side',
        'Condition: text in {"SELL", "BEAR", "BEARISH", "SHORT", "DOWN"}. Which side of this condition is the decision?',
        true_text='The label on this side is short.',
        false_text='The label on the other side is other_side.',
    )) == "true":
        return "SHORT"
    if (_sv_1312 := _selector_side(
        'sv4_1312_neutral',
        bool(text in {"BOTH", "NEUTRAL", "NONE", "FLAT", "MIXED"}),
        'neutral',
        'other_side',
        'Condition: text in {"BOTH", "NEUTRAL", "NONE", "FLAT", "MIXED"}. Which side of this condition is the decision?',
        true_text='The label on this side is neutral.',
        false_text='The label on the other side is other_side.',
    )) == "true":
        return "NEUTRAL"
    return text


def _action_from_side(side: str) -> str:
    if (_sv_1318 := _selector_side(
        'sv4_1318_long',
        bool(side == "LONG"),
        'long',
        'other_side',
        'Condition: side == "LONG". Which side of this condition is the decision?',
        true_text='The label on this side is long.',
        false_text='The label on the other side is other_side.',
    )) == "true":
        return "long"
    if (_sv_1320 := _selector_side(
        'sv4_1320_short',
        bool(side == "SHORT"),
        'short',
        'other_side',
        'Condition: side == "SHORT". Which side of this condition is the decision?',
        true_text='The label on this side is short.',
        false_text='The label on the other side is other_side.',
    )) == "true":
        return "short"
    return _lower(side)


def _normalize_selected_action(value: Any) -> str:
    action = _lower(value)
    aliases = {
        "buy": "long",
        "bull": "long",
        "bullish": "long",
        "sell": "short",
        "bear": "short",
        "bearish": "short",
        "flat": "no-trade",
        "skip": "no-trade",
        "skip-trade": "no-trade",
        "notrade": "no-trade",
        "source-required": "source-required",
        "source-required-admission": "source-required",
    }
    return aliases.get(action, action)


def _source_contract_violation(evidence_class: Any) -> str | None:
    text = _lower(evidence_class).replace("-", "_").replace(" ", "_")
    if not text:
        return "missing_evidence_class"
    for token in FORBIDDEN_SOURCE_EVIDENCE_TOKENS:
        if token in {"broker_real_cash", "broker_real_pnl"} and (
            f"not_{token}" in text or "not_broker_real" in text
        ):
            continue
        if token in text:
            return f"forbidden_future_or_result_evidence_class:{token}"
    return None


def ignored_forbidden_runtime_fields(event: Mapping[str, Any]) -> tuple[str, ...]:
    """Return future/result fields present in the caller packet.

    Selector V4 never consumes these fields. Returning them makes no-leak
    auditing explicit without silently hiding a bad packet.
    """

    return tuple(
        field
        for field in FORBIDDEN_SELECTOR_V4_RUNTIME_FIELDS
        if event.get(field) not in (None, "")
    )


def selector_v4_action_is_risk_bearing(action: Any) -> bool:
    """Return whether a Selector V4 action can carry positive risk."""

    return _normalize_selected_action(action) in RISK_BEARING_SELECTOR_V4_ACTIONS


def selector_v4_action_blocks_execution(action: Any) -> bool:
    """Return whether a Selector V4 action must block new order intent."""

    normalized = _normalize_selected_action(action)
    return bool(normalized and normalized in BLOCKING_SELECTOR_V4_ACTIONS)


def _confluence_sources(raw: Any) -> tuple[Mapping[str, Any], ...]:
    if isinstance(raw, Mapping):
        sources = raw.get("sources") or raw.get("source_scores")
        if isinstance(sources, Sequence) and not isinstance(sources, (str, bytes, bytearray)):
            return tuple(source for source in sources if isinstance(source, Mapping))
        if raw.get("source_id"):
            return (raw,)
    if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes, bytearray)):
        return tuple(source for source in raw if isinstance(source, Mapping))
    return ()


def _source_family(source: Mapping[str, Any]) -> str:
    explicit = _first_value(source, "source_family", "family", "source_kind")
    if explicit not in (None, ""):
        return _text(explicit).strip().lower().replace("-", "_")
    source_id = _text(source.get("source_id")).lower()
    schema = _text(source.get("schema_version")).lower()
    material = f"{source_id} {schema}"
    if (_sv_1404 := _selector_side(
        'sv4_1404_market_state',
        bool("market" in material or "whiteboard" in material),
        'market_state',
        'other_side',
        'Condition: "market" in material or "whiteboard" in material. Which side of this condition is the decision?',
        true_text='The label on this side is market_state.',
        false_text='The label on the other side is other_side.',
    )) == "true":
        return "market_state"
    if (_sv_1406 := _selector_side(
        'sv4_1406_cost',
        bool("cost" in material or "swap" in material or "slippage" in material),
        'cost',
        'other_side',
        'Condition: "cost" in material or "swap" in material or "slippage" in material. Which side of this condition is the decision?',
        true_text='The label on this side is cost.',
        false_text='The label on the other side is other_side.',
    )) == "true":
        return "cost"
    if (_sv_1408 := _selector_side(
        'sv4_1408_lifecycle',
        bool("lifecycle" in material or "ticket" in material or "position" in material),
        'lifecycle',
        'other_side',
        'Condition: "lifecycle" in material or "ticket" in material or "position" in material. Which side of this condition is the decision?',
        true_text='The label on this side is lifecycle.',
        false_text='The label on the other side is other_side.',
    )) == "true":
        return "lifecycle"
    if (_sv_1410 := _selector_side(
        'sv4_1410_source_completeness',
        bool("source_complete" in material or "source_completeness" in material),
        'source_completeness',
        'other_side',
        'Condition: "source_complete" in material or "source_completeness" in material. Which side of this condition is the decision?',
        true_text='The label on this side is source_completeness.',
        false_text='The label on the other side is other_side.',
    )) == "true":
        return "source_completeness"
    if (_sv_1412 := _selector_side(
        'sv4_1412_selector',
        bool("selector" in material or "framework" in material or "numeric_confluence" in material),
        'selector',
        'other_side',
        'Condition: "selector" in material or "framework" in material or "numeric_confluence" in material. Which side of this condition is the decision?',
        true_text='The label on this side is selector.',
        false_text='The label on the other side is other_side.',
    )) == "true":
        return "selector"
    return "selector"


def _required_confluence_source_families(
    *,
    raw: Any,
    cfg: Mapping[str, Any],
) -> tuple[str, ...]:
    if not _truthy(cfg.get("selector_v4_require_confluence_source_families", True)):
        return ()
    configured = cfg.get("selector_v4_required_confluence_source_families")
    if configured is None and isinstance(raw, Mapping):
        configured = raw.get("required_source_families")
    if configured is None:
        configured = DEFAULT_REQUIRED_CONFLUENCE_SOURCE_FAMILIES
    if isinstance(configured, str):
        configured = [configured]
    if not isinstance(configured, Sequence):
        return DEFAULT_REQUIRED_CONFLUENCE_SOURCE_FAMILIES
    families = []
    for item in configured:
        family = _text(item).strip().lower().replace("-", "_")
        if family:
            families.append(family)
    return tuple(dict.fromkeys(families))


def _source_completeness(value: Any) -> float:
    score = _score01(value)
    return 0.0 if score is None else score


def _evaluate_confluence(
    event: Mapping[str, Any],
    *,
    side: str,
    cfg: Mapping[str, Any],
) -> dict[str, Any]:
    raw = (
        event.get("numeric_confluence")
        or event.get("follow_avoid_mixed_numeric_confluence")
        or event.get("confluence")
    )
    sources = _confluence_sources(raw)
    required_families = _required_confluence_source_families(raw=raw, cfg=cfg)
    missing: list[str] = []
    source_scores: list[dict[str, Any]] = []
    hard_avoid: list[str] = []
    present_families: set[str] = set()
    mixed_count = 0
    score_sum = 0.0
    weight_sum = 0.0
    min_source_completeness = _float(cfg.get("selector_v4_min_confluence_source_completeness"))
    if min_source_completeness is None:
        min_source_completeness = 0.65
    hard_avoid_strength = _float(cfg.get("selector_v4_hard_avoid_strength"))
    if hard_avoid_strength is None:
        hard_avoid_strength = 0.8

    if not sources:
        return {
            "status": "missing_numeric_confluence_sources",
            "score": None,
            "source_count": 0,
            "source_scores": [],
            "hard_avoid_reasons": [],
            "mixed_count": 0,
            "average_source_completeness": 0.0,
            "required_source_families": list(required_families),
            "present_source_families": [],
            "missing_required_source_families": list(required_families),
            "missing_fields": ["numeric_confluence.sources"]
            + [
                f"numeric_confluence.required_source_families.{family}"
                for family in required_families
            ],
        }

    for index, source in enumerate(sources):
        prefix = f"numeric_confluence.sources[{index}]"
        source_id = _text(source.get("source_id")) or f"source_{index}"
        family = _source_family(source)
        label = _upper(
            _first_value(
                source,
                "label",
                "classification",
                "fam_label",
                "state",
                "categorical_label",
            )
        )
        if label not in {"FOLLOW", "AVOID", "MIXED"}:
            missing.append(f"{prefix}.label")
        direction = _direction(_first_value(source, "direction", "side", "bias_direction"))
        if not direction:
            missing.append(f"{prefix}.direction")
        strength = _score01(source.get("strength"))
        confidence = _score01(source.get("confidence"))
        reliability = _score01(_first_value(source, "reliability_history", "reliability"))
        freshness = _score01(source.get("freshness"))
        completeness = _source_completeness(source.get("source_completeness"))
        cost_sensitivity = _score01(source.get("cost_sensitivity"))
        for field_name, value in (
            ("strength", strength),
            ("confidence", confidence),
            ("reliability_history", reliability),
            ("freshness", freshness),
            ("source_completeness", completeness),
            ("cost_sensitivity", cost_sensitivity),
        ):
            if value is None:
                missing.append(f"{prefix}.{field_name}")
        if completeness < min_source_completeness:
            missing.append(f"{prefix}.source_completeness_below_floor")
        invalidation_type = _first_value(
            source,
            "invalidation_type",
            "avoid_invalidation_type",
        )
        if label == "AVOID" and not _text(invalidation_type):
            missing.append(f"{prefix}.invalidation_type")
        if label == "MIXED" and not _text(source.get("conflict_reason")):
            missing.append(f"{prefix}.conflict_reason")

        strength = 0.0 if strength is None else strength
        confidence = 0.0 if confidence is None else confidence
        reliability = 0.0 if reliability is None else reliability
        freshness = 0.0 if freshness is None else freshness
        cost_sensitivity = 0.0 if cost_sensitivity is None else cost_sensitivity
        contract_violation = _source_contract_violation(source.get("evidence_class"))
        if contract_violation:
            missing.append(f"{prefix}.evidence_class_contract_violation:{contract_violation}")
        elif family != "unknown":
            present_families.add(family)
        weight = (
            strength * 0.35
            + confidence * 0.25
            + reliability * 0.20
            + freshness * 0.10
            + completeness * 0.10
        )
        weight *= 1.0 - (0.35 * cost_sensitivity)
        if contract_violation:
            weight = 0.0
        alignment = 0
        if direction == side:
            alignment = 1
        elif direction in {"LONG", "SHORT"} and side in {"LONG", "SHORT"}:
            alignment = -1
        if label == "FOLLOW":
            signed = alignment * weight
        elif label == "AVOID":
            signed = -alignment * weight if alignment else -weight
            if (_sv_1568 := _selector_side(
        'sv4_1568_avoid',
        bool(alignment == 1 and strength >= hard_avoid_strength and confidence >= hard_avoid_strength),
        'avoid',
        'other_side',
        'Condition: alignment == 1 and strength >= hard_avoid_strength and confidence >= hard_avoid_strength. Which side of this condition is the decision?',
        true_text='avoid rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true":
                    hard_avoid.append(f"{source_id}:avoid_{invalidation_type}")
        elif label == "MIXED":
            mixed_count += 1
            signed = alignment * weight * 0.25
        else:
            signed = 0.0
        score_sum += signed
        weight_sum += max(weight, 0.000001)
        source_scores.append(
            {
                "source_id": source_id,
                "source_family": family,
                "label": label or "MISSING",
                "direction": direction or "MISSING",
                "signed_score": round(signed, 12),
                "weight": round(weight, 12),
                "source_completeness": round(completeness, 12),
                "evidence_class": source.get("evidence_class"),
                "source_contract_status": (
                    "source_contract_violation"
                    if contract_violation
                    else "predecision_source_allowed"
                ),
                "source_contract_violation": contract_violation,
                "conflict_reason": source.get("conflict_reason"),
                "invalidation_type": invalidation_type,
            }
        )

    missing_families = [
        family for family in required_families if family not in present_families
    ]
    missing.extend(
        f"numeric_confluence.required_source_families.{family}"
        for family in missing_families
    )
    average_completeness = sum(row["source_completeness"] for row in source_scores) / len(source_scores)
    score = score_sum / weight_sum if weight_sum else 0.0
    return {
        "status": "numeric_confluence_scored",
        "score": round(_clamp(score, -1.0, 1.0), 12),
        "source_count": len(sources),
        "source_scores": source_scores,
        "hard_avoid_reasons": hard_avoid,
        "mixed_count": mixed_count,
        "average_source_completeness": round(average_completeness, 12),
        "required_source_families": list(required_families),
        "present_source_families": sorted(present_families),
        "missing_required_source_families": missing_families,
        "missing_fields": sorted(set(missing)),
    }


def _theses_from_probability_debate(probability_debate: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    raw = (
        probability_debate.get("theses")
        or probability_debate.get("action_theses")
        or probability_debate.get("actions")
        or {}
    )
    theses: dict[str, Mapping[str, Any]] = {}
    if isinstance(raw, Mapping):
        for key, value in raw.items():
            if isinstance(value, Mapping):
                theses[_normalize_selected_action(key)] = value
    elif isinstance(raw, Sequence) and not isinstance(raw, (str, bytes, bytearray)):
        for value in raw:
            if not isinstance(value, Mapping):
                continue
            action = _normalize_selected_action(
                _first_value(value, "action", "thesis_action", "selected_action")
            )
            if action:
                theses[action] = value
    return theses


def _evaluate_probability_debate(
    event: Mapping[str, Any],
    *,
    candidate_action: str,
    cfg: Mapping[str, Any],
) -> dict[str, Any]:
    decision_inputs = _candidate_decision_inputs(event)
    probability_debate = _first_mapping(
        event,
        "probability_debate",
        "probability_debate_packet",
        "debate",
    )
    if not probability_debate:
        probability_debate = _first_mapping(
            decision_inputs,
            "probability_debate",
            "probability_debate_packet",
            "debate",
        )
    if not probability_debate:
        return {
            "status": "missing_probability_debate_packet",
            "selected_action": None,
            "candidate_thesis": {},
            "all_actions_present": [],
            "missing_fields": ["probability_debate"],
            "vetoes": [],
        }

    selected_action = _normalize_selected_action(
        _first_value(probability_debate, "selected_action", "final_action", "action")
    )
    theses = _theses_from_probability_debate(probability_debate)
    candidate_thesis = theses.get(candidate_action) or {}
    missing: list[str] = []
    if not selected_action:
        missing.append("probability_debate.selected_action")
    for action in _ACTIONS_REQUIRING_THESES:
        if action not in theses:
            missing.append(f"probability_debate.theses.{action}")
    if not candidate_thesis:
        missing.append(f"probability_debate.theses.{candidate_action}")
    probability = _score01(candidate_thesis.get("probability"))
    ev = _float(_first_value(candidate_thesis, "EV", "ev", "expected_value_r", "ev_r"))
    uncertainty = _score01(candidate_thesis.get("uncertainty"))
    missing_source_penalty = _score01(
        _first_value(candidate_thesis, "missing_source_penalty", "source_penalty")
    )
    completeness = _source_completeness(candidate_thesis.get("source_completeness"))
    calibration = _score01(
        _first_value(candidate_thesis, "confidence_calibration", "calibration")
    )
    for field_name, value in (
        ("probability", probability),
        ("EV", ev),
        ("uncertainty", uncertainty),
        ("missing_source_penalty", missing_source_penalty),
        ("source_completeness", completeness),
        ("confidence_calibration", calibration),
    ):
        if value is None:
            missing.append(f"probability_debate.theses.{candidate_action}.{field_name}")
    thesis_contract_violation = _source_contract_violation(candidate_thesis.get("evidence_class"))
    if thesis_contract_violation:
        missing.append(
            f"probability_debate.theses.{candidate_action}.evidence_class_contract_violation:{thesis_contract_violation}"
        )
    vetoes = candidate_thesis.get("vetoes") or probability_debate.get("vetoes") or []
    if isinstance(vetoes, str):
        vetoes = [vetoes]
    if not isinstance(vetoes, Sequence):
        vetoes = []
    max_missing_penalty = _float(cfg.get("selector_v4_max_missing_source_penalty"))
    if max_missing_penalty is None:
        max_missing_penalty = 0.25
    if (missing_source_penalty or 0.0) > max_missing_penalty:
        missing.append(f"probability_debate.theses.{candidate_action}.missing_source_penalty_above_floor")
    return {
        "status": "probability_debate_scored",
        "selected_action": selected_action,
        "candidate_action": candidate_action,
        "candidate_thesis": {
            "probability": probability,
            "EV": ev,
            "uncertainty": uncertainty,
            "missing_source_penalty": missing_source_penalty,
            "source_completeness": completeness,
            "confidence_calibration": calibration,
            "evidence_class": candidate_thesis.get("evidence_class"),
            "source_contract_status": (
                "source_contract_violation"
                if thesis_contract_violation
                else "predecision_source_allowed"
            ),
            "source_contract_violation": thesis_contract_violation,
            "disagreement_state": candidate_thesis.get("disagreement_state"),
            "vetoes": list(vetoes),
            "rejected_alternatives": candidate_thesis.get("rejected_alternatives") or [],
        },
        "all_actions_present": sorted(theses),
        "missing_fields": sorted(set(missing)),
        "vetoes": list(vetoes),
    }


def _evaluate_broker_net(event: Mapping[str, Any], *, cfg: Mapping[str, Any]) -> dict[str, Any]:
    selected_cell = _first_mapping(
        event,
        "broker_net_selected_cell",
        "selected_cell",
        "selected_cell_admission",
        "broker_net",
    )
    if not selected_cell:
        selected_cell = {
            key: event.get(key)
            for key in (
                "broker_net_expectancy_r",
                "cost_adjusted_expectancy_r",
                "stress_expectancy_r",
                "selected_cell_risk_pct",
                "risk_pct",
                "selected_cell_id",
                "source_completeness",
                "evidence_class",
            )
            if event.get(key) not in (None, "")
        }
    missing: list[str] = []
    broker_net_ev = _float(
        _first_value(
            selected_cell,
            "broker_net_expectancy_r",
            "broker_net_ev_r",
            "cost_adjusted_expectancy_r",
            "selected_cell_expectancy_r",
            "expectancy_r",
        )
    )
    stress_ev = _float(
        _first_value(selected_cell, "stress_expectancy_r", "broker_net_stress_ev_r")
    )
    risk_pct = _float(
        _first_value(selected_cell, "risk_pct", "selected_cell_risk_pct", "approved_risk_pct")
    )
    completeness = _source_completeness(selected_cell.get("source_completeness"))
    evidence_class = selected_cell.get("evidence_class")
    source_contract_violation = _source_contract_violation(evidence_class)
    if broker_net_ev is None:
        missing.append("selected_cell.broker_net_expectancy_r")
    if risk_pct is None:
        missing.append("selected_cell.risk_pct")
    if not evidence_class:
        missing.append("selected_cell.evidence_class")
    elif source_contract_violation:
        missing.append(
            f"selected_cell.evidence_class_contract_violation:{source_contract_violation}"
        )
    if completeness <= 0.0:
        missing.append("selected_cell.source_completeness")
    min_completeness = _float(cfg.get("selector_v4_min_selected_cell_source_completeness"))
    if min_completeness is None:
        min_completeness = 0.7
    if completeness < min_completeness:
        missing.append("selected_cell.source_completeness_below_floor")
    return {
        "status": "broker_net_selected_cell_scored" if selected_cell else "missing_selected_cell",
        "selected_cell_id": _first_value(selected_cell, "selected_cell_id", "cell_id"),
        "broker_net_expectancy_r": broker_net_ev,
        "stress_expectancy_r": stress_ev,
        "risk_pct": risk_pct,
        "source_completeness": completeness,
        "evidence_class": evidence_class,
        "rows": _first_value(selected_cell, "rows", "selected_cell_rows", "effective_n"),
        "source_status": _first_value(selected_cell, "source_status", "result_use_status"),
        "source_contract_status": (
            "source_contract_violation"
            if source_contract_violation
            else "predecision_source_allowed"
        ),
        "source_contract_violation": source_contract_violation,
        "missing_fields": sorted(set(missing)),
    }


def _evaluate_cost(event: Mapping[str, Any], *, cfg: Mapping[str, Any]) -> dict[str, Any]:
    cost = dict(_first_mapping(event, "broker_cost", "cost", "cost_swap_slippage"))
    flat_cost_aliases = {
        "expected_total_cost_r": _first_value(
            event,
            "expected_total_cost_r",
            "total_cost_r",
            "total_execution_cost_r",
            "broker_calibrated_expected_cost_r",
            "broker_pretrade_cost_r",
            "expected_cost_r",
            "cost_r",
        ),
        "pretrade_cost_packet_status": _first_value(
            event,
            "pretrade_cost_packet_status",
            "broker_net_cost_packet_status",
        ),
        "pretrade_cost_refusal_reasons": event.get(
            "pretrade_cost_refusal_reasons"
        ),
        "cost_source_gap_status": _first_value(
            event,
            "cost_source_gap_status",
            "broker_net_cost_source_gap_status",
        ),
        "cost_authority": _first_value(
            event,
            "cost_authority",
            "execution_cost_authority",
        ),
        "candidate_cost_r_fallback_is_authority": _first_value(
            event,
            "candidate_cost_r_fallback_is_authority",
            "source_gap_cost_fallback_is_authority",
        ),
        "source_completeness": _first_value(event, "cost_source_completeness"),
        "evidence_class": _first_value(event, "cost_evidence_class"),
    }
    for key, value in flat_cost_aliases.items():
        if value not in (None, "", [], {}) and cost.get(key) in (None, "", [], {}):
            cost[key] = value
    flat_pretrade_packet = _first_mapping(
        event,
        "pretrade_broker_net_cost_packet",
        "broker_net_cost_packet",
    )
    if flat_pretrade_packet and not isinstance(
        cost.get("pretrade_broker_net_cost_packet"), Mapping
    ):
        cost["pretrade_broker_net_cost_packet"] = flat_pretrade_packet
    pretrade_packet = _first_mapping(
        cost,
        "pretrade_broker_net_cost_packet",
        "broker_net_cost_packet",
    )
    missing: list[str] = []
    total = _float(
        _first_present_value(
            _first_value(cost, "expected_total_cost_r", "total_cost_r", "broker_net_cost_r"),
            _first_value(
                pretrade_packet,
                "expected_total_cost_r",
                "total_cost_r",
                "broker_net_cost_r",
            ),
        )
    )
    if total is None:
        pieces = [
            abs(_float(cost.get(key)) or 0.0)
            for key in ("spread_r", "commission_r", "swap_r", "slippage_stress_r")
        ]
        total = sum(pieces) if any(pieces) else None
    completeness = _source_completeness(cost.get("source_completeness"))
    evidence_class = cost.get("evidence_class")
    source_contract_violation = _source_contract_violation(evidence_class)
    if total is None:
        missing.append("cost.expected_total_cost_r")
    if completeness <= 0.0:
        missing.append("cost.source_completeness")
    if _truthy(cfg.get("selector_v4_require_pretrade_cost_model", True)) and not cost:
        missing.append("cost.pretrade_cost_model")
    elif source_contract_violation:
        missing.append(f"cost.evidence_class_contract_violation:{source_contract_violation}")
    packet_status = _upper(
        pretrade_packet.get("status")
        or _first_value(cost, "pretrade_cost_packet_status", "broker_net_cost_packet_status")
    )
    cost_source_gap_status = (
        pretrade_packet.get("cost_source_gap_status")
        or _first_value(cost, "cost_source_gap_status", "broker_net_cost_source_gap_status")
    )
    cost_authority = (
        pretrade_packet.get("authority")
        or _first_value(cost, "cost_authority", "pretrade_cost_packet_authority")
    )
    execution_cost_authority = _first_value(
        cost,
        "execution_cost_authority",
        "execution_cost_scope",
    )
    fallback_is_authority = _truthy(
        pretrade_packet.get("candidate_cost_r_fallback_is_authority")
        if pretrade_packet.get("candidate_cost_r_fallback_is_authority") is not None
        else _first_value(
            cost,
            "candidate_cost_r_fallback_is_authority",
            "source_gap_cost_fallback_is_authority",
        )
    )
    raw_refusal_reasons = (
        pretrade_packet.get("refusal_reasons")
        or cost.get("pretrade_cost_refusal_reasons")
        or []
    )
    if isinstance(raw_refusal_reasons, str):
        refusal_reasons = [raw_refusal_reasons]
    else:
        refusal_reasons = [str(item) for item in raw_refusal_reasons if item not in (None, "")]
    source_gap_cost_fallback_blocked = _truthy(
        pretrade_packet.get("source_gap_cost_fallback_blocked")
        if pretrade_packet.get("source_gap_cost_fallback_blocked") is not None
        else _first_value(cost, "source_gap_cost_fallback_blocked")
    )
    cost_authority_block_reason = None
    cost_packet_present = bool(cost) or bool(pretrade_packet)
    if cost_packet_present:
        if (_sv_1960 := _selector_side(
        'sv4_1960_broker_net_pretrade_cost_packet_refused',
        bool(packet_status and packet_status not in {"PASSED", "PASS", "OK"}),
        'broker_net_pretrade_cost_packet_refused',
        'other_side',
        'Condition: packet_status and packet_status not in {"PASSED", "PASS", "OK"}. Which side of this condition is the decision?',
        true_text='This side stands: broker_net_pretrade_cost_packet_refused.',
        false_text='The other side stands: other_side.',
    )) == "true":
            cost_authority_block_reason = (
                "broker_net_pretrade_cost_packet_refused"
                if packet_status == "REFUSED"
                else f"broker_net_pretrade_cost_packet_status_not_passed:{packet_status}"
            )
        elif _sv_1960 is not None and (_sv_1960 := _selector_side(
        'sv4_1966_broker_net_cost_authority_not_executable',
        bool(cost_authority != "broker_calibrated_replay_cost"),
        'broker_net_cost_authority_not_executable',
        'other_side',
        'Condition: cost_authority != "broker_calibrated_replay_cost". Which side of this condition is the decision?',
        true_text='This side stands: broker_net_cost_authority_not_executable.',
        false_text='The other side stands: other_side.',
    )) == "true":
            cost_authority_block_reason = (
                "broker_net_cost_authority_not_executable:"
                f"{cost_authority or 'missing'}"
            )
        elif _sv_1960 is not None and (_sv_1960 := _selector_side(
        'sv4_1971_broker_net_cost_source_gap_not_executable',
        bool(cost_source_gap_status != "source_bound_cost_authority_present"),
        'broker_net_cost_source_gap_not_executable',
        'other_side',
        'Condition: cost_source_gap_status != "source_bound_cost_authority_present". Which side of this condition is the decision?',
        true_text='This side stands: broker_net_cost_source_gap_not_executable.',
        false_text='The other side stands: other_side.',
    )) == "true":
            cost_authority_block_reason = (
                "broker_net_cost_source_gap_not_executable:"
                f"{cost_source_gap_status or 'missing'}"
            )
        elif _sv_1960 is not None and (_sv_1960 := _selector_side(
        'sv4_1976_broker_net_candidate_cost_fallback_not_order_aut',
        bool(fallback_is_authority),
        'broker_net_candidate_cost_fallback_not_order_aut',
        'other_side',
        'Condition: fallback_is_authority. Which side of this condition is the decision?',
        true_text='This side stands: broker_net_candidate_cost_fallback_not_order_aut.',
        false_text='The other side stands: other_side.',
    )) == "true":
            cost_authority_block_reason = (
                "broker_net_candidate_cost_fallback_not_order_authority"
            )
        elif _sv_1960 is not None and (_sv_1960 := _selector_side(
        'sv4_1980_broker_net_source_gap_cost_fallback_blocked',
        bool(source_gap_cost_fallback_blocked),
        'broker_net_source_gap_cost_fallback_blocked',
        'other_side',
        'Condition: source_gap_cost_fallback_blocked. Which side of this condition is the decision?',
        true_text='This side stands: broker_net_source_gap_cost_fallback_blocked.',
        false_text='The other side stands: other_side.',
    )) == "true":
            cost_authority_block_reason = "broker_net_source_gap_cost_fallback_blocked"
    return {
        "status": "cost_model_scored" if cost else "missing_cost_model",
        "expected_total_cost_r": total,
        "slippage_stress_r": _float(cost.get("slippage_stress_r")),
        "swap_r": _float(cost.get("swap_r")),
        "commission_r": _float(cost.get("commission_r")),
        "pretrade_cost_packet_status": packet_status or None,
        "pretrade_cost_packet_refused": packet_status == "REFUSED",
        "pretrade_cost_refusal_reasons": refusal_reasons,
        "cost_source_gap_status": cost_source_gap_status,
        "cost_authority": cost_authority,
        "execution_cost_authority": execution_cost_authority,
        "candidate_cost_r_fallback_is_authority": fallback_is_authority,
        "source_gap_cost_fallback_blocked": source_gap_cost_fallback_blocked,
        "cost_authority_block_reason": cost_authority_block_reason,
        "source_completeness": completeness,
        "evidence_class": evidence_class,
        "source_contract_status": (
            "source_contract_violation"
            if source_contract_violation
            else "predecision_source_allowed"
        ),
        "source_contract_violation": source_contract_violation,
        "missing_fields": sorted(set(missing)),
    }


def _evaluate_lifecycle(event: Mapping[str, Any]) -> dict[str, Any]:
    lifecycle = _first_mapping(event, "lifecycle", "same_symbol_lifecycle", "position_lifecycle")
    missing: list[str] = []
    duplicate = _truthy(_first_value(lifecycle, "duplicate_exposure", "duplicate_symbol_exposure"))
    same_conflict = _lower(
        _first_value(lifecycle, "same_symbol_conflict", "same_instrument_conflict")
    )
    open_competition = _lower(
        _first_value(lifecycle, "open_trade_competition_status", "open_trade_competition")
    )
    completeness = _source_completeness(lifecycle.get("source_completeness"))
    evidence_class = lifecycle.get("evidence_class")
    source_contract_violation = _source_contract_violation(evidence_class)
    for field_name, value in (
        ("duplicate_exposure", lifecycle.get("duplicate_exposure")),
        ("same_symbol_conflict", lifecycle.get("same_symbol_conflict")),
        ("open_trade_competition_status", lifecycle.get("open_trade_competition_status")),
        ("source_completeness", lifecycle.get("source_completeness")),
    ):
        if value in (None, ""):
            missing.append(f"lifecycle.{field_name}")
    if source_contract_violation:
        missing.append(
            f"lifecycle.evidence_class_contract_violation:{source_contract_violation}"
        )
    return {
        "status": "lifecycle_scored" if lifecycle else "missing_lifecycle_packet",
        "duplicate_exposure": duplicate,
        "same_symbol_conflict": same_conflict,
        "open_trade_competition_status": open_competition,
        "ticket_bound_state": lifecycle.get("ticket_bound_state"),
        "pending_partial_be_trailing_stale_state": lifecycle.get(
            "pending_partial_be_trailing_stale_state"
        ),
        "source_completeness": completeness,
        "evidence_class": evidence_class,
        "source_contract_status": (
            "source_contract_violation"
            if source_contract_violation
            else "predecision_source_allowed"
        ),
        "source_contract_violation": source_contract_violation,
        "missing_fields": sorted(set(missing)),
    }


def _policy_key(value: Any) -> str:
    return _lower(value).replace("-", "_").replace(" ", "_")


def _dynamic_policy(event: Mapping[str, Any]) -> str:
    router = _first_mapping(
        event,
        "moonshot_dynamic_execution_router_v4",
        "dynamic_policy",
        "dynamic_execution_policy",
    )
    return _policy_key(
        _first_value(
            event,
            "dynamic_geometry_policy",
            "selected_policy",
            "gtos_vnext_dynamic_policy_selected",
        )
        or router.get("selected_policy")
        or router.get("dynamic_policy_selected")
    )


def _route_session(event: Mapping[str, Any]) -> str:
    return _policy_key(
        _first_value(
            event,
            "route_session",
            "session_bucket",
            "session",
            "kill_zone",
        )
    ).removesuffix("_broad")


def _package_session_tokens(event: Mapping[str, Any]) -> tuple[str, ...]:
    tokens = []
    decision_inputs = _candidate_decision_inputs(event)
    for source in (
        event,
        decision_inputs,
        _first_mapping(event, "ultimate_candidate_package"),
        _first_mapping(event, "ultimate_package"),
        _first_mapping(event, "candidate_ultimate_package"),
        _first_mapping(decision_inputs, "ultimate_candidate_package"),
        _first_mapping(decision_inputs, "ultimate_package"),
        _first_mapping(decision_inputs, "candidate_ultimate_package"),
    ):
        for key_name in (
            "package_session_tokens",
            "authority_session_tokens",
            "session_tokens",
        ):
            for value in _text_values(source.get(key_name)):
                key = _policy_key(value)
                if key:
                    tokens.append(key)
    return tuple(dict.fromkeys(tokens))


def _configured_package_session(token: str) -> str | None:
    key = _policy_key(token).removesuffix("_broad")
    if key in {"tokyo", "london", "ny"}:
        return key
    if key.startswith("in_") and key.endswith("_timewarp_configured_session"):
        middle = key.removeprefix("in_").removesuffix("_timewarp_configured_session")
        if middle in {"tokyo", "london", "ny"}:
            return middle
    return None


def _package_session_authority(
    event: Mapping[str, Any],
    *,
    cfg: Mapping[str, Any],
    raw_route_session: str,
) -> dict[str, Any]:
    tokens = _package_session_tokens(event)
    normalized_tokens = tuple(
        token.removesuffix("_broad") for token in tokens if token
    )
    configured_sessions = tuple(
        dict.fromkeys(
            session
            for token in tokens
            if (session := _configured_package_session(token)) is not None
        )
    )
    enabled = bool(
        _truthy(cfg.get("selector_v4_package_session_token_authority_enabled"))
        or _truthy(cfg.get("ultimate_candidate_package_session_token_authority_enabled"))
    )
    applied_session = (
        configured_sessions[0]
        if enabled
        and raw_route_session in {"off_configured_session", "off_kz"}
        and configured_sessions
        else None
    )
    return {
        "enabled": enabled,
        "raw_route_session": raw_route_session or None,
        "route_session": applied_session or raw_route_session or None,
        "applied": applied_session is not None,
        "applied_session": applied_session,
        "package_session_tokens": list(tokens),
        "normalized_package_session_tokens": list(normalized_tokens),
        "configured_package_sessions": list(configured_sessions),
        "source_boundary": (
            "local_replay_package_session_tokens_not_live_broker_authority"
            if enabled
            else "disabled_default_selector_route_session_only"
        ),
    }


GENERIC_PACKAGE_ORIGIN_KEYS = frozenset(
    {
        "",
        "unknown",
        "none",
        "null",
        "broader_origin",
        "origin_broader_origin",
        "package",
        "ultimate_candidate_package",
    }
)


def _normalize_origin_family_key(value: Any) -> str:
    key = _policy_key(value)
    if key.startswith("origin_"):
        key = key.removeprefix("origin_")
    return key


def _router_refusal_origin_family_aliases(value: Any) -> tuple[str, ...]:
    key = _normalize_origin_family_key(value)
    if not key or key in GENERIC_PACKAGE_ORIGIN_KEYS:
        return ()
    aliases = [key.removeprefix("current_"), key] if key.startswith("current_") else [key]
    return tuple(dict.fromkeys(alias for alias in aliases if alias))


def _package_sleeve_ids(event: Mapping[str, Any]) -> tuple[str, ...]:
    values: list[str] = []
    decision_inputs = _candidate_decision_inputs(event)
    for source in (
        event,
        decision_inputs,
        _first_mapping(event, "ultimate_candidate_package"),
        _first_mapping(event, "ultimate_package"),
        _first_mapping(event, "candidate_ultimate_package"),
        _first_mapping(decision_inputs, "ultimate_candidate_package"),
        _first_mapping(decision_inputs, "ultimate_package"),
        _first_mapping(decision_inputs, "candidate_ultimate_package"),
    ):
        for key in (
            "ultimate_package_matched_sleeve_ids",
            "matched_sleeve_ids",
            "package_matched_sleeve_ids",
            "ultimate_package_matched_member_axis_ids",
            "matched_member_axis_ids",
            "matched_sleeves",
            "package_matched_sleeves",
            "ultimate_package_matched_sleeves",
        ):
            for value in _sleeve_id_text_values(source.get(key)):
                if value:
                    values.append(value)
    return tuple(dict.fromkeys(values))


def _sleeve_id_text_values(value: Any) -> tuple[str, ...]:
    if value in (None, ""):
        return ()
    if isinstance(value, str):
        return tuple(part.strip() for part in value.split(",") if part.strip())
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        text = str(value).strip()
        return (text,) if text else ()
    if isinstance(value, (list, tuple, set, frozenset)):
        values: list[str] = []
        for item in value:
            if isinstance(item, str):
                values.extend(part.strip() for part in item.split(",") if part.strip())
            elif isinstance(item, (int, float)) and not isinstance(item, bool):
                text = str(item).strip()
                if text:
                    values.append(text)
            elif isinstance(item, Mapping):
                values.extend(_sleeve_id_text_values(item))
        return tuple(values)
    if isinstance(value, Mapping):
        values: list[str] = []
        for key in (
            "sleeve_id",
            "id",
            "package_sleeve_id",
            "member_axis_id",
            "axis_id",
            "source_member_axis_id",
            "ultimate_package_sleeve_id",
        ):
            values.extend(_sleeve_id_text_values(value.get(key)))
        for key in (
            "matched_sleeves",
            "sleeves",
            "package_matched_sleeves",
            "ultimate_package_matched_sleeves",
            "matched_member_axes",
        ):
            values.extend(_sleeve_id_text_values(value.get(key)))
        return tuple(dict.fromkeys(item for item in values if item))
    return ()


def _package_sleeve_origin_families(event: Mapping[str, Any]) -> tuple[str, ...]:
    families: list[str] = []
    for sleeve_id in _package_sleeve_ids(event):
        parts = [_policy_key(part) for part in str(sleeve_id).split("__")]
        parts = [part for part in parts if part]
        if len(parts) >= 3 and parts[-1] in {"long", "short"}:
            family = _normalize_origin_family_key(parts[-2])
            if family and family not in GENERIC_PACKAGE_ORIGIN_KEYS:
                families.append(family)
                continue
        for part in parts:
            family = _normalize_origin_family_key(part)
            if (
                family
                and family not in GENERIC_PACKAGE_ORIGIN_KEYS
                and not family.endswith("sleeve")
                and family not in {"long", "short", "buy", "sell"}
            ):
                families.append(family)
                break
    return tuple(dict.fromkeys(families))


def _origin_family(event: Mapping[str, Any]) -> str:
    value = (
        _first_value(event, "origin_family", "candidate_origin_family", "framework")
        or ""
    )
    key = _normalize_origin_family_key(value)
    derived = _package_sleeve_origin_families(event)
    if derived and key in GENERIC_PACKAGE_ORIGIN_KEYS:
        key = derived[0]
    if (_sv_2305 := _selector_side(
        'sv4_2305_unknown',
        bool(key in GENERIC_PACKAGE_ORIGIN_KEYS),
        'unknown',
        'other_side',
        'Condition: key in GENERIC_PACKAGE_ORIGIN_KEYS. Which side of this condition is the decision?',
        true_text='The label on this side is unknown.',
        false_text='The label on the other side is other_side.',
    )) == "true":
        return "unknown"
    return key


def _origin_family_candidates(event: Mapping[str, Any]) -> tuple[str, ...]:
    candidates = [_origin_family(event), *_package_sleeve_origin_families(event)]
    return tuple(
        dict.fromkeys(
            key
            for key in (_normalize_origin_family_key(value) for value in candidates)
            if key and key not in GENERIC_PACKAGE_ORIGIN_KEYS
        )
    )


def _candidate_symbol(event: Mapping[str, Any]) -> str:
    decision_inputs = _candidate_decision_inputs(event)
    return _policy_key(
        _first_present_value(
            _first_value(
                event,
                "symbol",
                "broker_symbol",
                "candidate_symbol",
                "instrument",
                "trade_symbol",
            ),
            _first_value(
                decision_inputs,
                "symbol",
                "broker_symbol",
                "candidate_symbol",
                "instrument",
                "trade_symbol",
            ),
            _first_value(
                _first_mapping(event, "ultimate_candidate_package"),
                "symbol",
                "broker_symbol",
                "candidate_symbol",
                "instrument",
                "trade_symbol",
            ),
            _first_value(
                _first_mapping(event, "ultimate_package"),
                "symbol",
                "broker_symbol",
                "candidate_symbol",
                "instrument",
                "trade_symbol",
            ),
        )
    )


def _text_values(value: Any) -> tuple[str, ...]:
    if value in (None, ""):
        return ()
    if isinstance(value, str):
        return tuple(part.strip() for part in value.split(",") if part.strip())
    try:
        return tuple(str(part).strip() for part in value if str(part).strip())
    except TypeError:
        text = str(value).strip()
        return (text,) if text else ()


def _evaluate_learned_edge(
    event: Mapping[str, Any], *, cfg: Mapping[str, Any]
) -> dict[str, Any] | None:
    """Score the candidate with the frozen learned-edge artifact (default OFF).

    Returns ``None`` when ``selector_v4_learned_edge_enabled`` is not true so
    default behavior stays byte-identical. Refusals are NEVER silent:

    - ``selector_v4_learned_edge_required`` true -> the block carries a
      source-required missing field (``learned_edge_artifact_unavailable_or_refused``);
    - otherwise the block carries an explicit
      ``learned_edge_unavailable_static_floor_fallback:<detail>`` reason and the
      existing static-floor behavior applies unchanged.
    """

    if not _truthy(cfg.get("selector_v4_learned_edge_enabled", False)):
        return None
    required = _truthy(cfg.get("selector_v4_learned_edge_required", False))
    sizing_enabled = _truthy(cfg.get("selector_v4_learned_risk_sizing_enabled", False))
    block: dict[str, Any] = {
        "enabled": True,
        "required": required,
        "sizing_enabled": sizing_enabled,
        "status": "not_scored",
        "fill_probability": None,
        "probability": None,
        "expected_net_r": None,
        "artifact_hash_sha256": None,
        "fallback_reason": None,
        "thresholds": {},
        "segment_shrinkage_weights": {},
        "applied_to_floors": False,
        "applied_to_sizing": False,
        "source_required_fields": [],
    }

    def _refuse(detail: str) -> dict[str, Any]:
        if (_sv_2410 := _selector_side(
        'sv4_2410_refused_source_required',
        bool(required),
        'refused_source_required',
        'fallback_static_floor',
        'Condition: required. Which side of this condition is the decision?',
        true_text='This side stands: refused_source_required.',
        false_text='The other side stands: fallback_static_floor.',
    )) == "true":
            block["status"] = "refused_source_required"
            block["source_required_fields"] = [
                "learned_edge_artifact_unavailable_or_refused"
            ]
            block["fallback_reason"] = f"learned_edge_unavailable_required:{detail}"
        elif _sv_2410 is not None and _sv_2410 == "false":
            block["status"] = "fallback_static_floor"
            block["fallback_reason"] = (
                f"learned_edge_unavailable_static_floor_fallback:{detail}"
            )
        return block

    artifact_path = _text(cfg.get("selector_v4_learned_edge_artifact_path")).strip()
    if (_sv_2424 := _selector_side(
        'sv4_2424_artifact_path_not_configured',
        bool(not artifact_path),
        'artifact_path_not_configured',
        'other_side',
        'Condition: not artifact_path. Which side of this condition is the decision?',
        true_text='This side returns artifact_path_not_configured.',
        false_text='The other side of the condition is the decision.',
    )) == "true":
        return _refuse("artifact_path_not_configured")
    if _sv_2424 is None:
        return None

    try:
        artifact = load_learned_edge_artifact_cached(artifact_path)
    except Exception as exc:  # fail closed on any load failure, never silent
        return _refuse(f"artifact_load_failed_{type(exc).__name__}")
    try:
        scored = score_learned_edge(extract_runtime_features(event), artifact)
    except Exception as exc:
        # Schema-valid but type-corrupt artifacts (non-numeric coefficients,
        # malformed feature specs) must surface as an explicit refusal, not a
        # crash out of the candidate loop.
        return _refuse(f"scorer_exception_{type(exc).__name__}")
    if (_sv_2437 := _selector_side(
        'sv4_2437_scorer_refused',
        bool(scored.get("status") != "scored"),
        'scorer_refused',
        'other_side',
        'Condition: scored.get("status") != "scored". Which side of this condition is the decision?',
        true_text='This side returns scorer_refused.',
        false_text='The other side of the condition is the decision.',
    )) == "true":
        detail = str(scored.get("status") or "scorer_refused")
        refusal_items = scored.get("errors") or scored.get("missing_required_features") or []
        if refusal_items:
            detail += ":" + "|".join(str(item) for item in list(refusal_items)[:4])
        return _refuse(detail)
    block.update(
        {
            "status": "scored",
            "fill_probability": _float(scored.get("fill_probability")),
            "probability": _float(scored.get("probability")),
            "expected_net_r": _float(scored.get("expected_net_r")),
            "artifact_hash_sha256": scored.get("artifact_hash_sha256"),
            "thresholds": dict(_mapping(artifact.get("thresholds"))),
            "segment_shrinkage_weights": dict(
                _mapping(scored.get("segment_shrinkage_weights"))
            ),
            "applied_to_floors": True,
        }
    )
    return block


def _evaluate_admission_quality_guard(
    event: Mapping[str, Any],
    *,
    cfg: Mapping[str, Any],
    broker_net_admission_ev: float | None,
    total_cost_r: float,
    probability: float | None,
    fill_probability: float | None,
    source_completeness: float | None,
    learned: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    enabled = _truthy(cfg.get("selector_v4_admission_quality_guard_enabled", False))
    dynamic_policy = _dynamic_policy(event)
    raw_route_session = _route_session(event)
    package_session_authority = _package_session_authority(
        event,
        cfg=cfg,
        raw_route_session=raw_route_session,
    )
    route_session = _policy_key(
        package_session_authority.get("route_session")
    ).removesuffix("_broad")
    exact_rule_route_session = raw_route_session
    origin_family = _origin_family(event)
    candidate_symbol = _candidate_symbol(event)
    candidate_side = _policy_key(_candidate_side(event))
    utc_hour_bucket = _policy_key(
        _first_value(event, "utc_hour_bucket", "hour_bucket", "decision_hour_bucket")
    )
    hard_reject_reasons: list[str] = []
    reduced_risk_reasons: list[str] = []
    diagnostic_reasons: list[str] = []
    source_required_fields: list[str] = []
    router = _first_mapping(event, "moonshot_dynamic_execution_router_v4")
    router_status = _policy_key(router.get("decision_status"))
    router_candidate_allowed = router.get("candidate_use_allowed_now")
    router_runtime_effect = router.get("runtime_effect_now")
    router_refused_candidate = bool(
        router
        and (
            router_candidate_allowed is False
            or "refuse" in router_status
            or "held_for_source_or_branch_repair" in _policy_key(router.get("candidate_action"))
        )
    )
    exact_rule_mode = _policy_key(
        cfg.get("selector_v4_admission_quality_exact_block_rules_mode")
        or cfg.get("selector_v4_admission_quality_rule_enforcement_mode")
        or "enforce"
    )
    exact_rules_are_diagnostic = exact_rule_mode in {"diagnostic", "observe", "shadow"}

    def add_exact_rule_reason(reason: str) -> None:
        if (_sv_2513 := _selector_side(
        'sv4_2513_diagnostic_reasons_append',
        bool(exact_rules_are_diagnostic),
        'diagnostic_reasons_append',
        'other_side',
        'Condition: exact_rules_are_diagnostic. Which side of this condition is the decision?',
        true_text='This side stands: diagnostic_reasons_append.',
        false_text='The other side stands: other_side.',
    )) == "true":
            diagnostic_reasons.append(reason)
        elif _sv_2513 is not None and _sv_2513 == "false":
            hard_reject_reasons.append(reason)

    if enabled:
        if (_sv_2519 := _selector_side(
        'sv4_2519_admission_quality_dynamic_router_refused_candida',
        bool(router_refused_candidate and _truthy(
            cfg.get("selector_v4_enforce_dynamic_router_refusal", False)
        )),
        'admission_quality_dynamic_router_refused_candida',
        'other_side',
        'Condition: router_refused_candidate and _truthy(\n            cfg.get("selector_v4_enforce_dynamic_router_refusal", False)\n        ). Which side of this condition is the decision?',
        true_text='The label on this side is admission_quality_dynamic_router_refused_candida.',
        false_text='The label on the other side is other_side.',
    )) == "true":
            reason = "admission_quality_dynamic_router_refused_candidate_use"
            action = _policy_key(
                cfg.get("selector_v4_dynamic_router_refusal_action") or "reject"
            )
            if (_sv_2526 := _selector_side(
        'sv4_2526_source_required_fields_append',
        bool(action == "source_required"),
        'source_required_fields_append',
        'other_side',
        'Condition: action == "source_required". Which side of this condition is the decision?',
        true_text='This side stands: source_required_fields_append.',
        false_text='The other side stands: other_side.',
    )) == "true":
                source_required_fields.append(reason)
            elif _sv_2526 is not None and (_sv_2526 := _selector_side(
        'sv4_2528_admission_quality_dynamic_router_refusal_open_re',
        bool(action in {"open-reduced-risk", "open_reduced_risk"}),
        'admission_quality_dynamic_router_refusal_open_re',
        'other_side',
        'Condition: action in {"open-reduced-risk", "open_reduced_risk"}. Which side of this condition is the decision?',
        true_text='admission_quality_dynamic_router_refusal_open_re reduces this candidate.',
        false_text='other_side does not reduce this candidate.',
    )) == "true":
                reduced_risk_reasons.append(
                    "admission_quality_dynamic_router_refusal_open_reduced_risk_configured"
                )
            elif _sv_2526 is not None and (_sv_2526 := _selector_side(
        'sv4_2532_reduced_risk_reasons_append',
        bool(action in {"reduce-risk", "reduce_risk"}),
        'reduced_risk_reasons_append',
        'other_side',
        'Condition: action in {"reduce-risk", "reduce_risk"}. Which side of this condition is the decision?',
        true_text='reduced_risk_reasons_append reduces this candidate.',
        false_text='other_side does not reduce this candidate.',
    )) == "true":
                reduced_risk_reasons.append(reason)
            elif _sv_2526 is not None and _sv_2526 == "false":
                hard_reject_reasons.append(reason)
        if (
            (_sv_2536 := _selector_side(
        'sv4_2536_admission_quality_partial_be_runner_blocked_afte',
        bool(dynamic_policy == "partial_be_runner"
            and _truthy(cfg.get("selector_v4_block_partial_be_runner", True))),
        'admission_quality_partial_be_runner_blocked_afte',
        'other_side',
        'Condition: dynamic_policy == "partial_be_runner"\n            and _truthy(cfg.get("selector_v4_block_partial_be_runner", True)). Which side of this condition is the decision?',
        true_text='admission_quality_partial_be_runner_blocked_afte rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true"
        ):
            hard_reject_reasons.append(
                "admission_quality_partial_be_runner_blocked_after_kiap_weak_accepted_drag"
            )
        if (
            (_sv_2543 := _selector_side(
        'sv4_2543_admission_quality_off_session_partial_be_runner_',
        bool(route_session in {"off_configured_session", "off_kz"}
            and dynamic_policy == "partial_be_runner"
            and _truthy(
                cfg.get("selector_v4_block_off_configured_session_partial_be_runner", True)
            )),
        'admission_quality_off_session_partial_be_runner_',
        'other_side',
        'Condition: route_session in {"off_configured_session", "off_kz"}\n            and dynamic_policy == "partial_be_runner"\n            and _truthy(\n                cfg.get("selector_v4_block_off_configured_session_partial_be_runner", T. Which side of this condition is the decision?',
        true_text='admission_quality_off_session_partial_be_runner_ rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true"
        ):
            hard_reject_reasons.append(
                "admission_quality_off_session_partial_be_runner_blocked_after_kiap_drag"
            )
        if (_sv_2553 := _selector_side(
        'sv4_2553_admission_quality_off_configured_session_entry_b',
        bool(route_session in {"off_configured_session", "off_kz"} and _truthy(
            cfg.get("selector_v4_block_off_configured_session_entries", False)
        )),
        'admission_quality_off_configured_session_entry_b',
        'other_side',
        'Condition: route_session in {"off_configured_session", "off_kz"} and _truthy(\n            cfg.get("selector_v4_block_off_configured_session_entries", False)\n        ). Which side of this condition is the decision?',
        true_text='The label on this side is admission_quality_off_configured_session_entry_b.',
        false_text='The label on the other side is other_side.',
    )) == "true":
            reason = "admission_quality_off_configured_session_entry_blocked"
            action = _policy_key(
                cfg.get("selector_v4_off_configured_session_entry_action")
                or "reject"
            )
            if (_sv_2561 := _selector_side(
        'sv4_2561_source_required_fields_append',
        bool(action == "source_required"),
        'source_required_fields_append',
        'other_side',
        'Condition: action == "source_required". Which side of this condition is the decision?',
        true_text='This side stands: source_required_fields_append.',
        false_text='The other side stands: other_side.',
    )) == "true":
                source_required_fields.append(reason)
            elif _sv_2561 is not None and (_sv_2561 := _selector_side(
        'sv4_2563_admission_quality_off_configured_session_open_re',
        bool(action in {"open-reduced-risk", "open_reduced_risk"}),
        'admission_quality_off_configured_session_open_re',
        'other_side',
        'Condition: action in {"open-reduced-risk", "open_reduced_risk"}. Which side of this condition is the decision?',
        true_text='admission_quality_off_configured_session_open_re reduces this candidate.',
        false_text='other_side does not reduce this candidate.',
    )) == "true":
                reduced_risk_reasons.append(
                    "admission_quality_off_configured_session_open_reduced_risk_configured"
                )
            elif _sv_2561 is not None and (_sv_2561 := _selector_side(
        'sv4_2567_reduced_risk_reasons_append',
        bool(action in {"reduce-risk", "reduce_risk"}),
        'reduced_risk_reasons_append',
        'other_side',
        'Condition: action in {"reduce-risk", "reduce_risk"}. Which side of this condition is the decision?',
        true_text='reduced_risk_reasons_append reduces this candidate.',
        false_text='other_side does not reduce this candidate.',
    )) == "true":
                reduced_risk_reasons.append(reason)
            elif _sv_2561 is not None and _sv_2561 == "false":
                hard_reject_reasons.append(reason)
        off_session_max_cost = _float(cfg.get("selector_v4_off_configured_session_max_cost_r"))
        if (
            (_sv_2572 := _selector_side(
        'sv4_2572_admission_quality_off_session_cost_above_full_ri',
        bool(route_session in {"off_configured_session", "off_kz"}
            and off_session_max_cost is not None
            and total_cost_r > off_session_max_cost),
        'admission_quality_off_session_cost_above_full_ri',
        'other_side',
        'Condition: route_session in {"off_configured_session", "off_kz"}\n            and off_session_max_cost is not None\n            and total_cost_r > off_session_max_cost. Which side of this condition is the decision?',
        true_text='admission_quality_off_session_cost_above_full_ri reduces this candidate.',
        false_text='other_side does not reduce this candidate.',
    )) == "true"
        ):
            reduced_risk_reasons.append(
                "admission_quality_off_session_cost_above_full_risk_floor"
            )
        blocked_session_origin_rules = cfg.get(
            "selector_v4_admission_quality_blocked_session_origin_families"
        )
        if isinstance(blocked_session_origin_rules, Sequence) and not isinstance(
            blocked_session_origin_rules,
            (str, bytes),
        ):
            for rule in blocked_session_origin_rules:
                if not isinstance(rule, Mapping):
                    continue
                rule_session = _policy_key(
                    _first_value(rule, "route_session", "session", "session_bucket")
                ).removesuffix("_broad")
                rule_families = {
                    _policy_key(item).removeprefix("origin_")
                    for item in _text_values(rule.get("origin_families"))
                }
                if (
                    (_sv_2597 := _selector_side(
        'sv4_2597_admission_quality_session_origin_family_blocked_',
        bool(rule_session
                    and rule_session == exact_rule_route_session
                    and origin_family in rule_families),
        'admission_quality_session_origin_family_blocked_',
        'other_side',
        'Condition: rule_session\n                    and rule_session == exact_rule_route_session\n                    and origin_family in rule_families. Which side of this condition is the decision?',
        true_text='This side stands: admission_quality_session_origin_family_blocked_.',
        false_text='The other side stands: other_side.',
    )) == "true"
                ):
                    add_exact_rule_reason(
                        str(
                            rule.get("reason")
                            or "admission_quality_session_origin_family_blocked_after_kiap_drag"
                        )
                    )
        blocked_session_origin_symbol_rules = cfg.get(
            "selector_v4_admission_quality_blocked_session_origin_symbols"
        )
        if isinstance(
            blocked_session_origin_symbol_rules, Sequence
        ) and not isinstance(blocked_session_origin_symbol_rules, (str, bytes)):
            for rule in blocked_session_origin_symbol_rules:
                if not isinstance(rule, Mapping):
                    continue
                rule_session = _policy_key(
                    _first_value(rule, "route_session", "session", "session_bucket")
                ).removesuffix("_broad")
                rule_families = {
                    _policy_key(item).removeprefix("origin_")
                    for item in _text_values(rule.get("origin_families"))
                }
                rule_symbols = {
                    _policy_key(item)
                    for item in _text_values(
                        rule.get("symbols")
                        or rule.get("broker_symbols")
                        or rule.get("instruments")
                    )
                }
                rule_sides = {
                    _policy_key(item)
                    for item in _text_values(
                        rule.get("sides") or rule.get("directions")
                    )
                }
                if (
                    (_sv_2638 := _selector_side(
        'sv4_2638_admission_quality_broad_dynamic_accepted_loss_sy',
        bool(rule_session
                    and rule_session == exact_rule_route_session
                    and origin_family in rule_families
                    and candidate_symbol
                    and candidate_symbol in rule_symbols
                    and (not rule_sides or candidate_side in rule_sides)),
        'admission_quality_broad_dynamic_accepted_loss_sy',
        'other_side',
        'Condition: rule_session\n                    and rule_session == exact_rule_route_session\n                    and origin_family in rule_families\n                    and candidate_symbol\n                    and candidate_symbol in ru. Which side of this condition is the decision?',
        true_text='This side stands: admission_quality_broad_dynamic_accepted_loss_sy.',
        false_text='The other side stands: other_side.',
    )) == "true"
                ):
                    add_exact_rule_reason(
                        str(
                            rule.get("reason")
                            or "admission_quality_broad_dynamic_accepted_loss_symbol_family_blocked"
                        )
                    )
        blocked_hours = {
            _policy_key(item)
            for item in _text_values(
                cfg.get("selector_v4_admission_quality_blocked_utc_hour_buckets")
            )
        }
        if (_sv_2658 := _selector_side(
        'sv4_2658_admission_quality_utc_hour_bucket_blocked_after_',
        bool(utc_hour_bucket and utc_hour_bucket in blocked_hours),
        'admission_quality_utc_hour_bucket_blocked_after_',
        'other_side',
        'Condition: utc_hour_bucket and utc_hour_bucket in blocked_hours. Which side of this condition is the decision?',
        true_text='This side stands: admission_quality_utc_hour_bucket_blocked_after_.',
        false_text='The other side stands: other_side.',
    )) == "true":
            add_exact_rule_reason(
                "admission_quality_utc_hour_bucket_blocked_after_kiap_drag"
            )
    learned_mapping = _mapping(learned)
    learned_floor_active = learned_mapping.get("status") == "scored"
    calibrated_enabled = bool(
        (
            enabled
            and _truthy(cfg.get("selector_v4_calibrated_admission_enabled", False))
        )
        or learned_floor_active
    )
    calibrated_floor_failures: list[str] = []
    if calibrated_enabled:
        if learned_floor_active:
            # Learned-edge admission mode: the floors evaluate the LEARNED
            # probability / expected net R / fill probability instead of the
            # packet heuristics (heuristics stay in the packet as shadow
            # fields on the learned_edge block).
            floor_expected_net_r = _float(learned_mapping.get("expected_net_r"))
            floor_probability = _float(learned_mapping.get("probability"))
            floor_fill_probability = _float(learned_mapping.get("fill_probability"))
            learned_thresholds = _mapping(learned_mapping.get("thresholds"))
        else:
            floor_expected_net_r = broker_net_admission_ev
            floor_probability = probability
            floor_fill_probability = fill_probability
            learned_thresholds = {}
        min_expected_net = _float(
            cfg.get("selector_v4_calibrated_min_expected_net_r")
        )
        if min_expected_net is None:
            min_expected_net = _float(
                learned_thresholds.get("t_reduce_expected_net_r")
            )
        if min_expected_net is None:
            min_expected_net = 0.10
        min_probability = _float(
            cfg.get("selector_v4_calibrated_min_probability")
        )
        if min_probability is None:
            min_probability = _float(learned_thresholds.get("min_probability"))
        if min_probability is None:
            min_probability = 0.58
        min_fill_probability = _float(
            cfg.get("selector_v4_calibrated_min_fill_probability")
        )
        if min_fill_probability is None:
            min_fill_probability = _float(
                learned_thresholds.get("min_fill_probability")
            )
        if min_fill_probability is None:
            min_fill_probability = 0.45
        min_source_completeness = _float(
            cfg.get("selector_v4_calibrated_min_source_completeness")
        )
        if min_source_completeness is None:
            min_source_completeness = 0.65
        if (_sv_2717 := _selector_side(
        'sv4_2717_selector_v4_calibrated_admission_expected_net_r',
        bool(floor_expected_net_r is None),
        'selector_v4_calibrated_admission_expected_net_r',
        'other_side',
        'Condition: floor_expected_net_r is None. Which side of this condition is the decision?',
        true_text='This side stands: selector_v4_calibrated_admission_expected_net_r.',
        false_text='The other side stands: other_side.',
    )) == "true":
            source_required_fields.append("selector_v4_calibrated_admission.expected_net_r")
        elif _sv_2717 is not None and (_sv_2717 := _selector_side(
        'sv4_2719_calibrated_admission_expected_net_r_below_genera',
        bool(floor_expected_net_r < min_expected_net),
        'calibrated_admission_expected_net_r_below_genera',
        'other_side',
        'Condition: floor_expected_net_r < min_expected_net. Which side of this condition is the decision?',
        true_text='This side stands: calibrated_admission_expected_net_r_below_genera.',
        false_text='The other side stands: other_side.',
    )) == "true":
            calibrated_floor_failures.append(
                "calibrated_admission_expected_net_r_below_generalized_floor"
            )
        if (_sv_2723 := _selector_side(
        'sv4_2723_selector_v4_calibrated_admission_probability',
        bool(floor_probability is None),
        'selector_v4_calibrated_admission_probability',
        'other_side',
        'Condition: floor_probability is None. Which side of this condition is the decision?',
        true_text='This side stands: selector_v4_calibrated_admission_probability.',
        false_text='The other side stands: other_side.',
    )) == "true":
            source_required_fields.append("selector_v4_calibrated_admission.probability")
        elif _sv_2723 is not None and (_sv_2723 := _selector_side(
        'sv4_2725_calibrated_admission_probability_below_generaliz',
        bool(floor_probability < min_probability),
        'calibrated_admission_probability_below_generaliz',
        'other_side',
        'Condition: floor_probability < min_probability. Which side of this condition is the decision?',
        true_text='This side stands: calibrated_admission_probability_below_generaliz.',
        false_text='The other side stands: other_side.',
    )) == "true":
            calibrated_floor_failures.append(
                "calibrated_admission_probability_below_generalized_floor"
            )
        require_fill_probability = _truthy(
            cfg.get("selector_v4_calibrated_admission_require_fill_probability", False)
        )
        if floor_fill_probability is None:
            if (_sv_2733 := _selector_side(
        'sv4_2733_selector_v4_calibrated_admission_fill_probabilit',
        bool(require_fill_probability),
        'selector_v4_calibrated_admission_fill_probabilit',
        'other_side',
        'Condition: require_fill_probability. Which side of this condition is the decision?',
        true_text='This side stands: selector_v4_calibrated_admission_fill_probabilit.',
        false_text='The other side stands: other_side.',
    )) == "true":
                source_required_fields.append(
                    "selector_v4_calibrated_admission.fill_probability"
                )
        elif floor_fill_probability < min_fill_probability:
            calibrated_floor_failures.append(
                "calibrated_admission_fill_probability_below_generalized_floor"
            )
        if (_sv_2741 := _selector_side(
        'sv4_2741_selector_v4_calibrated_admission_source_complete',
        bool(source_completeness is None),
        'selector_v4_calibrated_admission_source_complete',
        'other_side',
        'Condition: source_completeness is None. Which side of this condition is the decision?',
        true_text='This side stands: selector_v4_calibrated_admission_source_complete.',
        false_text='The other side stands: other_side.',
    )) == "true":
            source_required_fields.append(
                "selector_v4_calibrated_admission.source_completeness"
            )
        elif _sv_2741 is not None and (_sv_2741 := _selector_side(
        'sv4_2745_calibrated_admission_source_completeness_below_g',
        bool(source_completeness < min_source_completeness),
        'calibrated_admission_source_completeness_below_g',
        'other_side',
        'Condition: source_completeness < min_source_completeness. Which side of this condition is the decision?',
        true_text='This side stands: calibrated_admission_source_completeness_below_g.',
        false_text='The other side stands: other_side.',
    )) == "true":
            calibrated_floor_failures.append(
                "calibrated_admission_source_completeness_below_generalized_floor"
            )
        floor_failure_action = _policy_key(
            cfg.get("selector_v4_calibrated_admission_floor_failure_action")
            or "reject"
        )
        if (_sv_2753 := _selector_side(
        'sv4_2753_reduced_risk_reasons_extend',
        bool(floor_failure_action in {"reduce-risk", "reduce_risk"}),
        'reduced_risk_reasons_extend',
        'other_side',
        'Condition: floor_failure_action in {"reduce-risk", "reduce_risk"}. Which side of this condition is the decision?',
        true_text='reduced_risk_reasons_extend reduces this candidate.',
        false_text='other_side does not reduce this candidate.',
    )) == "true":
            reduced_risk_reasons.extend(calibrated_floor_failures)
        elif _sv_2753 is not None and _sv_2753 == "false":
            hard_reject_reasons.extend(calibrated_floor_failures)
    result = {
        "status": "admission_quality_guard_scored" if enabled else "not_enabled",
        "enabled": enabled,
        "calibrated_admission_enabled": calibrated_enabled,
        "exact_block_rules_mode": exact_rule_mode,
        "dynamic_geometry_policy": dynamic_policy or None,
        "raw_route_session": raw_route_session or None,
        "route_session": route_session or None,
        "exact_rule_route_session": exact_rule_route_session or None,
        "package_session_authority": package_session_authority,
        "origin_family": origin_family or None,
        "symbol": candidate_symbol or None,
        "side": candidate_side or None,
        "utc_hour_bucket": utc_hour_bucket or None,
        "broker_net_admission_ev_r": (
            round(broker_net_admission_ev, 12)
            if broker_net_admission_ev is not None
            else None
        ),
        "total_cost_r": round(total_cost_r, 12),
        "probability": round(probability, 12) if probability is not None else None,
        "fill_probability": (
            round(fill_probability, 12) if fill_probability is not None else None
        ),
        "source_completeness": (
            round(source_completeness, 12)
            if source_completeness is not None
            else None
        ),
        "dynamic_router_refusal_enforced": bool(
            enabled
            and router_refused_candidate
            and _truthy(cfg.get("selector_v4_enforce_dynamic_router_refusal", False))
        ),
        "dynamic_router_candidate_use_allowed_now": router_candidate_allowed,
        "dynamic_router_runtime_effect_now": router_runtime_effect,
        "dynamic_router_decision_status": router.get("decision_status"),
        "dynamic_router_candidate_action": router.get("candidate_action"),
        "calibrated_floor_failures": sorted(set(calibrated_floor_failures)),
        "hard_reject_reasons": sorted(set(hard_reject_reasons)),
        "reduced_risk_reasons": sorted(set(reduced_risk_reasons)),
        "diagnostic_reasons": sorted(set(diagnostic_reasons)),
        "source_required_fields": sorted(set(source_required_fields)),
        "evidence_source": cfg.get("selector_v4_admission_quality_guard_source"),
        "calibrated_admission_source": cfg.get(
            "selector_v4_calibrated_admission_source"
        ),
    }
    if learned is not None:
        result["learned_edge_floor_active"] = learned_floor_active
    return result


def _evaluate_ultimate_candidate_package(
    event: Mapping[str, Any],
    *,
    cfg: Mapping[str, Any],
    generated_utc: str | None = None,
) -> dict[str, Any] | None:
    enabled = _truthy(cfg.get("ultimate_candidate_package_enabled", False))
    shadow_enabled = _truthy(cfg.get("ultimate_candidate_package_shadow_enabled", False))
    if not enabled and not shadow_enabled:
        return None
    registry_path = cfg.get("ultimate_candidate_package_registry_path")
    try:
        registry_rows = load_ultimate_candidate_package_registry(registry_path)
        if not registry_rows:
            return {
                "schema": "gtos.final_moonshot.ultimate_candidate_package.selector_packet.v1",
                "component": "ultimate_candidate_package",
                "decision_status": "ultimate_candidate_package_registry_missing",
                "matched_sleeve_count": 0,
                "matched_scheduler_lifecycle_merge_sleeves": 0,
                "matched_promote_default_off_sleeves": 0,
                "selector_shadow_score": 0.0,
                "registry_path": registry_path,
                "runtime_effect_now": False,
                "candidate_use_allowed_now": False,
                "live_execution_activation_allowed": False,
                "broker_account_order_history_deal_position_mutation_allowed": False,
                "order_calls": 0,
            }
        package_event = dict(event)
        derived_origin_families = _package_sleeve_origin_families(package_event)
        if derived_origin_families:
            package_event["package_sleeve_origin_families"] = list(
                derived_origin_families
            )
            if (
                _normalize_origin_family_key(package_event.get("origin_family"))
                in GENERIC_PACKAGE_ORIGIN_KEYS
            ):
                package_event["origin_family"] = derived_origin_families[0]
            if (
                _normalize_origin_family_key(
                    package_event.get("candidate_origin_family")
                )
                in GENERIC_PACKAGE_ORIGIN_KEYS
            ):
                package_event["candidate_origin_family"] = (
                    f"origin_{derived_origin_families[0]}"
                )
        cost = _first_mapping(event, "broker_cost", "cost", "cost_swap_slippage")
        pretrade_packet = _first_mapping(
            event,
            "pretrade_broker_net_cost_packet",
            "broker_net_cost_packet",
        ) or _first_mapping(cost, "pretrade_broker_net_cost_packet", "broker_net_cost_packet")
        decision_inputs = _candidate_decision_inputs(event)
        event_fillability = _first_mapping(event, "predecision_limit_fillability")
        decision_fillability = _first_mapping(
            decision_inputs,
            "predecision_limit_fillability",
        )
        execution_fillability_atom = _complete_execution_fillability_atom(
            event,
            decision_inputs,
        )
        selected_cell = _first_mapping(event, "selected_cell", "broker_net_selected_cell")
        probability_debate = _first_mapping(
            event,
            "probability_debate",
            "probability_debate_packet",
            "debate",
        )
        if not probability_debate:
            probability_debate = _first_mapping(
                decision_inputs,
                "probability_debate",
                "probability_debate_packet",
                "debate",
            )
        candidate_action = _normalize_selected_action(
            _first_value(
                event,
                "candidate_action",
                "action",
                "side",
                "direction",
            )
        )
        selected_action = _normalize_selected_action(
            _first_value(probability_debate, "selected_action", "final_action", "action")
        )
        theses = _theses_from_probability_debate(probability_debate)
        candidate_thesis = theses.get(candidate_action) if candidate_action else None
        candidate_thesis = (
            candidate_thesis if isinstance(candidate_thesis, Mapping) else {}
        )
        selected_thesis = theses.get(selected_action) if selected_action else None
        selected_thesis = (
            selected_thesis if isinstance(selected_thesis, Mapping) else {}
        )
        if candidate_thesis:
            package_quality_thesis = candidate_thesis
            package_quality_thesis_source = "probability_debate_candidate_action_thesis"
        elif selected_thesis and selected_action == candidate_action:
            package_quality_thesis = selected_thesis
            package_quality_thesis_source = "probability_debate_selected_action_thesis"
        else:
            package_quality_thesis = {}
            package_quality_thesis_source = (
                "probability_debate_candidate_action_thesis_missing"
            )
        explicit_quality_sources = {}
        for source in (event, decision_inputs):
            mapped = _mapping(source.get("candidate_decision_quality_field_sources"))
            if mapped:
                explicit_quality_sources.update(mapped)

        def _quality_source_label(field: str, *candidates: tuple[str, Any]) -> str:
            for label, value in candidates:
                if _alias_value_present(value):
                    explicit_label = _text(explicit_quality_sources.get(field))
                    if label.startswith("selector_v4.candidate_decision_inputs") and explicit_label:
                        return explicit_label
                    return label
            return ""

        quality_source_boundary = _text(
            _first_present_value(
                event.get("candidate_decision_quality_source_boundary"),
                decision_inputs.get("candidate_decision_quality_source_boundary"),
                "predecision_selector_v4_package_quality_aliases_no_outcome_fields",
            )
        )
        quality_field_sources = {
            "source_completeness": _quality_source_label(
                "source_completeness",
                (
                    "selector_v4.event.source_completeness",
                    _first_value(event, "source_completeness", "selected_cell_source_completeness"),
                ),
                (
                    "selector_v4.candidate_decision_inputs.source_completeness",
                    _first_value(decision_inputs, "source_completeness"),
                ),
                (
                    "selector_v4.selected_cell.source_completeness",
                    _first_value(selected_cell, "source_completeness"),
                ),
                (
                    "selector_v4.cost.source_completeness",
                    _first_value(cost, "source_completeness"),
                ),
                (
                    f"selector_v4.{package_quality_thesis_source}.source_completeness",
                    _first_value(package_quality_thesis, "source_completeness"),
                ),
            ),
            "probability": _quality_source_label(
                "probability",
                (
                    "selector_v4.event.probability",
                    _first_value(event, "probability", "candidate_probability"),
                ),
                (
                    "selector_v4.candidate_decision_inputs.probability",
                    _first_value(decision_inputs, "probability", "candidate_probability"),
                ),
                (
                    f"selector_v4.{package_quality_thesis_source}.probability",
                    _first_value(package_quality_thesis, "probability"),
                ),
            ),
            "confidence": _quality_source_label(
                "confidence",
                (
                    "selector_v4.event.confidence",
                    _first_value(event, "confidence", "candidate_confidence"),
                ),
                (
                    "selector_v4.candidate_decision_inputs.confidence",
                    _first_value(decision_inputs, "confidence", "candidate_confidence"),
                ),
                (
                    "selector_v4.selected_cell.confidence",
                    _first_value(selected_cell, "confidence", "candidate_confidence"),
                ),
                (
                    f"selector_v4.{package_quality_thesis_source}.confidence",
                    _first_value(package_quality_thesis, "confidence", "candidate_confidence"),
                ),
            ),
            "expected_net_r": _quality_source_label(
                "expected_net_r",
                (
                    "selector_v4.event.expected_net_r",
                    _first_value(event, "expected_net_r", "candidate_expected_net_r"),
                ),
                (
                    "selector_v4.candidate_decision_inputs.expected_net_r",
                    _first_value(
                        decision_inputs,
                        "expected_net_r",
                        "candidate_expected_net_r",
                    ),
                ),
                (
                    "selector_v4.selected_cell.broker_net_expectancy_r",
                    _first_value(selected_cell, "broker_net_expectancy_r"),
                ),
            ),
            "fill_probability": _quality_source_label(
                "fill_probability",
                (
                    "selector_v4.event.entry_quality_fill_probability",
                    _first_value(
                        event,
                        "entry_quality_fill_probability",
                        "heuristic_fill_probability",
                        "candidate_fill_probability",
                    ),
                ),
                ("selector_v4.event.fill_probability", _first_value(event, "fill_probability")),
                (
                    "selector_v4.candidate_decision_inputs.entry_quality_fill_probability",
                    _first_value(
                        decision_inputs,
                        "entry_quality_fill_probability",
                        "heuristic_fill_probability",
                        "candidate_fill_probability",
                    ),
                ),
                (
                    "selector_v4.candidate_decision_inputs.fill_probability",
                    _first_value(decision_inputs, "fill_probability"),
                ),
                (
                    "selector_v4.selected_cell.fill_probability",
                    _first_value(selected_cell, "fill_probability"),
                ),
                (
                    f"selector_v4.{package_quality_thesis_source}.fill_probability",
                    _first_value(package_quality_thesis, "fill_probability"),
                ),
            ),
            "entry_quality_fill_probability": _quality_source_label(
                "entry_quality_fill_probability",
                (
                    "selector_v4.event.entry_quality_fill_probability",
                    _first_value(
                        event,
                        "entry_quality_fill_probability",
                        "heuristic_fill_probability",
                        "candidate_fill_probability",
                    ),
                ),
                ("selector_v4.event.fill_probability", _first_value(event, "fill_probability")),
                (
                    "selector_v4.candidate_decision_inputs.entry_quality_fill_probability",
                    _first_value(
                        decision_inputs,
                        "entry_quality_fill_probability",
                        "heuristic_fill_probability",
                        "candidate_fill_probability",
                    ),
                ),
                (
                    "selector_v4.candidate_decision_inputs.fill_probability",
                    _first_value(decision_inputs, "fill_probability"),
                ),
                (
                    "selector_v4.selected_cell.fill_probability",
                    _first_value(selected_cell, "fill_probability"),
                ),
            ),
            "limit_fillability_probability": _quality_source_label(
                "limit_fillability_probability",
                (
                    "selector_v4.candidate_decision_inputs.limit_fillability_probability",
                    _first_value(
                        decision_inputs,
                        "limit_fillability_probability",
                        "predecision_limit_fillability_probability",
                    ),
                ),
                (
                    "selector_v4.event.limit_fillability_probability",
                    _first_value(
                        event,
                        "limit_fillability_probability",
                        "predecision_limit_fillability_probability",
                    ),
                ),
                (
                    "selector_v4.candidate_decision_inputs.predecision_limit_fillability.fill_probability",
                    _first_value(
                        decision_fillability,
                        "fill_probability",
                        "expected_fill_probability",
                        "limit_fill_probability",
                    ),
                ),
                (
                    "selector_v4.event.predecision_limit_fillability.fill_probability",
                    _first_value(
                        event_fillability,
                        "fill_probability",
                        "expected_fill_probability",
                        "limit_fill_probability",
                    ),
                ),
            ),
            "execution_fill_probability": _quality_source_label(
                "execution_fill_probability",
                (
                    _text(
                        execution_fillability_atom.get(
                            "execution_fill_probability_source"
                        )
                    ),
                    execution_fillability_atom.get(
                        "execution_fill_probability"
                    ),
                ),
            ),
        }
        quality_field_sources = {
            field: source
            for field, source in quality_field_sources.items()
            if _text(source)
        }
        quality_sources_complete = all(
            _text(quality_field_sources.get(field))
            for field in REQUIRED_QUALITY_CONTRACT_FIELDS
        )
        alias_values = {
            "expected_cost_r": _first_value(
                cost,
                "expected_total_cost_r",
                "total_cost_r",
                "broker_net_cost_r",
                "broker_pretrade_cost_r",
                "expected_cost_r",
                "cost_r",
            ),
            "pretrade_cost_packet_status": (
                pretrade_packet.get("status")
                or _first_value(
                    cost,
                    "pretrade_cost_packet_status",
                    "broker_net_cost_packet_status",
                )
            ),
            "cost_source_gap_status": (
                pretrade_packet.get("cost_source_gap_status")
                or _first_value(
                    cost,
                    "cost_source_gap_status",
                    "broker_net_cost_source_gap_status",
                )
            ),
            "cost_authority": (
                pretrade_packet.get("authority")
                or _first_value(cost, "cost_authority", "pretrade_cost_packet_authority")
            ),
            "candidate_cost_r_fallback_is_authority": (
                pretrade_packet.get("candidate_cost_r_fallback_is_authority")
                if pretrade_packet.get("candidate_cost_r_fallback_is_authority")
                is not None
                else _first_value(
                    cost,
                    "candidate_cost_r_fallback_is_authority",
                    "source_gap_cost_fallback_is_authority",
                )
            ),
            "source_completeness": _first_present_value(
                _first_value(event, "source_completeness", "selected_cell_source_completeness"),
                _first_value(decision_inputs, "source_completeness"),
                _first_value(selected_cell, "source_completeness"),
                _first_value(cost, "source_completeness"),
                _first_value(package_quality_thesis, "source_completeness"),
            ),
            "source_completeness_status": _first_present_value(
                _first_value(event, "source_completeness_status", "source_status"),
                _first_value(
                    decision_inputs,
                    "source_completeness_status",
                    "source_status",
                ),
                _first_value(selected_cell, "source_status", "result_use_status"),
            ),
            "candidate_probability": _first_present_value(
                _first_value(event, "candidate_probability", "probability"),
                _first_value(decision_inputs, "candidate_probability", "probability"),
                _first_value(package_quality_thesis, "probability"),
            ),
            "probability": _first_present_value(
                _first_value(event, "probability", "candidate_probability"),
                _first_value(decision_inputs, "probability", "candidate_probability"),
                _first_value(package_quality_thesis, "probability"),
            ),
            "candidate_ev_r": _first_present_value(
                _first_value(event, "candidate_ev_r", "ev_r"),
                _first_value(package_quality_thesis, "EV"),
            ),
            "candidate_expected_net_r": _first_present_value(
                _first_value(event, "candidate_expected_net_r", "expected_net_r"),
                _first_value(
                    decision_inputs,
                    "candidate_expected_net_r",
                    "expected_net_r",
                ),
                _first_value(selected_cell, "broker_net_expectancy_r"),
            ),
            "expected_net_r": _first_present_value(
                _first_value(event, "expected_net_r", "candidate_expected_net_r"),
                _first_value(
                    decision_inputs,
                    "expected_net_r",
                    "candidate_expected_net_r",
                ),
                _first_value(selected_cell, "broker_net_expectancy_r"),
            ),
            "candidate_fill_probability": _first_present_value(
                _first_value(
                    event,
                    "entry_quality_fill_probability",
                    "heuristic_fill_probability",
                    "candidate_fill_probability",
                    "fill_probability",
                ),
                _first_value(
                    decision_inputs,
                    "entry_quality_fill_probability",
                    "heuristic_fill_probability",
                    "candidate_fill_probability",
                    "fill_probability",
                ),
                _first_value(selected_cell, "fill_probability"),
                _first_value(package_quality_thesis, "fill_probability"),
            ),
            "fill_probability": _first_present_value(
                _first_value(
                    event,
                    "entry_quality_fill_probability",
                    "heuristic_fill_probability",
                    "fill_probability",
                    "candidate_fill_probability",
                ),
                _first_value(
                    decision_inputs,
                    "entry_quality_fill_probability",
                    "heuristic_fill_probability",
                    "fill_probability",
                    "candidate_fill_probability",
                ),
                _first_value(selected_cell, "fill_probability"),
                _first_value(package_quality_thesis, "fill_probability"),
            ),
            "entry_quality_fill_probability": _first_present_value(
                _first_value(
                    event,
                    "entry_quality_fill_probability",
                    "heuristic_fill_probability",
                    "fill_probability",
                    "candidate_fill_probability",
                ),
                _first_value(
                    decision_inputs,
                    "entry_quality_fill_probability",
                    "heuristic_fill_probability",
                    "fill_probability",
                    "candidate_fill_probability",
                ),
                _first_value(selected_cell, "fill_probability"),
                _first_value(package_quality_thesis, "fill_probability"),
            ),
            "limit_fillability_probability": _first_present_value(
                execution_fillability_atom.get(
                    "limit_fillability_probability"
                ),
            ),
            "predecision_limit_fillability_probability": _first_present_value(
                execution_fillability_atom.get(
                    "predecision_limit_fillability_probability"
                ),
            ),
            "execution_fill_probability": _first_present_value(
                execution_fillability_atom.get("execution_fill_probability"),
            ),
            **{
                key: value
                for key, value in execution_fillability_atom.items()
                if key
                in {
                    "execution_fill_probability_source",
                    "execution_fill_probability_source_time_utc",
                    "execution_fill_probability_source_boundary",
                    "execution_fill_probability_authority_class",
                    "execution_fill_probability_authority_hash_sha256",
                    "execution_fillability_signed_value_selected",
                    "execution_fillability_atomic_surface",
                    "execution_fillability_atomic_failure",
                    "execution_fillability_atomic_conflicts",
                    "predecision_limit_fillability",
                }
            },
            "candidate_confidence": _first_present_value(
                _first_value(event, "candidate_confidence", "confidence"),
                _first_value(decision_inputs, "candidate_confidence", "confidence"),
                _first_value(selected_cell, "confidence", "candidate_confidence"),
                _first_value(package_quality_thesis, "confidence", "candidate_confidence"),
            ),
            "confidence": _first_present_value(
                _first_value(event, "confidence", "candidate_confidence"),
                _first_value(decision_inputs, "confidence", "candidate_confidence"),
                _first_value(selected_cell, "confidence", "candidate_confidence"),
                _first_value(package_quality_thesis, "confidence", "candidate_confidence"),
            ),
            "candidate_package_quality_thesis_source": package_quality_thesis_source,
            "candidate_decision_quality_field_sources": quality_field_sources,
            "candidate_decision_quality_source_boundary": quality_source_boundary,
            "candidate_decision_quality_alias_status": (
                "exact_materialized"
                if quality_sources_complete
                else "partially_materialized"
            ),
            "candidate_decision_quality_alias_mismatches": [],
        }
        for key, value in alias_values.items():
            if _alias_value_present(value) and not _alias_value_present(
                package_event.get(key)
            ):
                package_event[key] = value
        packet = evaluate_ultimate_candidate_selector_shadow(
            package_event,
            registry_rows,
            cfg,
            generated_utc=generated_utc,
        )
        if not _alias_value_present(packet.get("candidate_package_quality_thesis_source")):
            packet["candidate_package_quality_thesis_source"] = package_quality_thesis_source
        packet["registry_path"] = registry_path
        return packet
    except Exception as exc:  # pragma: no cover - defensive fail-closed runtime guard
        return {
            "schema": "gtos.final_moonshot.ultimate_candidate_package.selector_packet.v1",
            "component": "ultimate_candidate_package",
            "decision_status": "ultimate_candidate_package_shadow_error_fail_closed",
            "error_type": type(exc).__name__,
            "matched_sleeve_count": 0,
            "matched_scheduler_lifecycle_merge_sleeves": 0,
            "matched_promote_default_off_sleeves": 0,
            "selector_shadow_score": 0.0,
            "registry_path": registry_path,
            "runtime_effect_now": False,
            "candidate_use_allowed_now": False,
            "live_execution_activation_allowed": False,
            "broker_account_order_history_deal_position_mutation_allowed": False,
            "order_calls": 0,
        }


@dataclass(frozen=True)
class SelectorV4AdmissionDecision:
    schema_version: str
    component: str
    enabled: bool
    apply_to_execution: bool
    live_activation_allowed_by_config: bool
    action: str
    would_action: str
    decision_status: str
    reason: str
    runtime_effect_now: bool
    candidate_use_allowed_now: bool
    source_bound_candidate_use_allowed_now: bool
    replay_candidate_use_allowed_now: bool
    risk_multiplier: float
    final_risk_pct: float | None
    selector_action: str = ""
    selector_reason: str = ""
    candidate_use_allowed_now_semantics: str = "live_runtime_effect"
    evidence_class: str = "production_code_integration_active_admission_authority"
    result_use_status: str = "admission_authority_not_validation_or_broker_truth"
    validation_result_status: bool = False
    outcome_result_rows_status: bool = False
    broker_runtime_change_status: bool = False
    broker_operation: bool = False
    order_calls: int = 0
    paid_api_or_vendor_call: bool = False
    ignored_forbidden_fields: tuple[str, ...] = ()
    source_required_fields: tuple[str, ...] = ()
    hard_reject_reasons: tuple[str, ...] = ()
    reduced_risk_reasons: tuple[str, ...] = ()
    queue_reasons: tuple[str, ...] = ()
    semantic_owner_handoffs: dict[str, str] = field(default_factory=dict)
    component_scores: dict[str, Any] = field(default_factory=dict)
    rejected_alternatives: tuple[str, ...] = ()

    def to_record(self) -> dict[str, Any]:
        record = asdict(self)
        record["selector_action"] = self.selector_action or self.would_action or self.action
        record["selector_reason"] = self.selector_reason or self.reason
        record["candidate_use_allowed_now_semantics"] = (
            self.candidate_use_allowed_now_semantics
        )
        record["ignored_forbidden_fields"] = list(self.ignored_forbidden_fields)
        record["source_required_fields"] = list(self.source_required_fields)
        record["hard_reject_reasons"] = list(self.hard_reject_reasons)
        record["reduced_risk_reasons"] = list(self.reduced_risk_reasons)
        record["queue_reasons"] = list(self.queue_reasons)
        record["rejected_alternatives"] = list(self.rejected_alternatives)
        component_scores = record.get("component_scores") or {}
        record["field_group_statuses"] = {
            "numeric_confluence": {
                "status": (component_scores.get("numeric_confluence") or {}).get("status"),
                "source_count": (component_scores.get("numeric_confluence") or {}).get(
                    "source_count"
                ),
                "missing_fields": (component_scores.get("numeric_confluence") or {}).get(
                    "missing_fields", []
                ),
            },
            "probability_debate": {
                "status": (component_scores.get("probability_debate") or {}).get("status"),
                "selected_action": (component_scores.get("probability_debate") or {}).get(
                    "selected_action"
                ),
                "all_actions_present": (
                    component_scores.get("probability_debate") or {}
                ).get("all_actions_present", []),
                "missing_fields": (component_scores.get("probability_debate") or {}).get(
                    "missing_fields", []
                ),
            },
            "broker_net_selected_cell": {
                "status": (component_scores.get("broker_net_selected_cell") or {}).get(
                    "status"
                ),
                "missing_fields": (
                    component_scores.get("broker_net_selected_cell") or {}
                ).get("missing_fields", []),
            },
            "cost": {
                "status": (component_scores.get("cost") or {}).get("status"),
                "missing_fields": (component_scores.get("cost") or {}).get(
                    "missing_fields", []
                ),
            },
            "lifecycle": {
                "status": (component_scores.get("lifecycle") or {}).get("status"),
                "missing_fields": (component_scores.get("lifecycle") or {}).get(
                    "missing_fields", []
                ),
            },
            "admission_quality": {
                "status": (component_scores.get("admission_quality") or {}).get(
                    "status"
                ),
                "calibrated_admission_enabled": (
                    component_scores.get("admission_quality") or {}
                ).get("calibrated_admission_enabled"),
                "exact_block_rules_mode": (
                    component_scores.get("admission_quality") or {}
                ).get("exact_block_rules_mode"),
                "dynamic_geometry_policy": (
                    component_scores.get("admission_quality") or {}
                ).get("dynamic_geometry_policy"),
                "route_session": (component_scores.get("admission_quality") or {}).get(
                    "route_session"
                ),
                "origin_family": (component_scores.get("admission_quality") or {}).get(
                    "origin_family"
                ),
                "symbol": (component_scores.get("admission_quality") or {}).get(
                    "symbol"
                ),
                "side": (component_scores.get("admission_quality") or {}).get("side"),
                "utc_hour_bucket": (
                    component_scores.get("admission_quality") or {}
                ).get("utc_hour_bucket"),
                "dynamic_router_refusal_enforced": (
                    component_scores.get("admission_quality") or {}
                ).get("dynamic_router_refusal_enforced"),
                "dynamic_router_candidate_use_allowed_now": (
                    component_scores.get("admission_quality") or {}
                ).get("dynamic_router_candidate_use_allowed_now"),
                "dynamic_router_runtime_effect_now": (
                    component_scores.get("admission_quality") or {}
                ).get("dynamic_router_runtime_effect_now"),
                "dynamic_router_decision_status": (
                    component_scores.get("admission_quality") or {}
                ).get("dynamic_router_decision_status"),
                "dynamic_router_candidate_action": (
                    component_scores.get("admission_quality") or {}
                ).get("dynamic_router_candidate_action"),
                "hard_reject_reasons": (
                    component_scores.get("admission_quality") or {}
                ).get("hard_reject_reasons", []),
                "reduced_risk_reasons": (
                    component_scores.get("admission_quality") or {}
                ).get("reduced_risk_reasons", []),
                "diagnostic_reasons": (
                    component_scores.get("admission_quality") or {}
                ).get("diagnostic_reasons", []),
                "calibrated_floor_failures": (
                    component_scores.get("admission_quality") or {}
                ).get("calibrated_floor_failures", []),
            },
        }
        learned_scores = component_scores.get("learned_edge")
        if isinstance(learned_scores, Mapping):
            # Only present when selector_v4_learned_edge_enabled is true so
            # default-off decisions stay byte-identical to pre-learned-mode.
            record["learned_edge"] = {
                "status": learned_scores.get("status"),
                "fill_probability": learned_scores.get("fill_probability"),
                "probability": learned_scores.get("probability"),
                "expected_net_r": learned_scores.get("expected_net_r"),
                "artifact_hash_sha256": learned_scores.get("artifact_hash_sha256"),
                "fallback_reason": learned_scores.get("fallback_reason"),
                "applied_to_floors": bool(learned_scores.get("applied_to_floors")),
                "applied_to_sizing": bool(learned_scores.get("applied_to_sizing")),
            }
        record["source_event_hash_sha256"] = _stable_sha256(
            _selector_source_event_hash_payload(record)
        )
        record["packet_hash_sha256"] = _stable_sha256(
            _selector_packet_hash_payload(record)
        )
        return record



def _selector_unanswered() -> SelectorV4AdmissionDecision:
    """Empty or tied Choice. Does not restore the old boolean and does not place."""

    return SelectorV4AdmissionDecision(
        schema_version="selector_v4_broker_net_admission_v1",
        component="selector_v4",
        enabled=False,
        apply_to_execution=False,
        live_activation_allowed_by_config=False,
        action="no-trade",
        would_action="no-trade",
        decision_status="admission_label_unanswered",
        reason="admission_label_unanswered",
        runtime_effect_now=False,
        candidate_use_allowed_now=False,
        source_bound_candidate_use_allowed_now=False,
        replay_candidate_use_allowed_now=False,
        risk_multiplier=0.0,
        final_risk_pct=None,
    )


def evaluate_selector_v4_admission(
    event: Mapping[str, Any],
    config: Mapping[str, Any] | None = None,
    *,
    enabled: bool | None = None,
    apply_to_execution: bool | None = None,
    package_generated_utc: str | None = None,
) -> SelectorV4AdmissionDecision:
    """Evaluate broker-net selected-cell admission from as-of V4 packets."""

    cfg = _config(config)
    enabled_value = _truthy(cfg.get("selector_v4_enabled", False)) if enabled is None else enabled
    apply_value = (
        _truthy(cfg.get("selector_v4_apply_to_execution", False))
        if apply_to_execution is None
        else apply_to_execution
    )
    live_allowed = _truthy(cfg.get("selector_v4_live_activation_allowed", False))
    side = _candidate_side(event)
    candidate_action = _action_from_side(side)
    forbidden = ignored_forbidden_runtime_fields(event)
    semantic_handoffs = {
        "same_symbol_lifecycle": "same_symbol_same_instrument_lifecycle_v4",
        "probability_debate": "probability_debate_team_engine_v4",
        "numeric_confluence": "follow_avoid_mixed_numeric_confluence_v4",
        "cost_swap_slippage": "cost_swap_slippage_broker_constraint_engine",
        "scheduler_allocator": "scheduler_v4_best_trade_allocator",
        "ultimate_candidate_package": "ultimate_candidate_package_shadow_selector_scheduler_surface",
        "ml_feature_label": "wave4_wave5_feature_label_store_and_model_registry",
    }

    if (_sv_3574 := _selector_side(
        'sv4_3574_selector_v4_broker_net_admission_v1',
        bool(not enabled_value),
        'selector_v4_broker_net_admission_v1',
        'other_side',
        'Condition: not enabled_value. Which side of this condition is the decision?',
        true_text='This side returns selector_v4_broker_net_admission_v1.',
        false_text='The other side of the condition is the decision.',
    )) == "true":
        return SelectorV4AdmissionDecision(
            schema_version="selector_v4_broker_net_admission_v1",
            component="selector_v4",
            enabled=False,
            apply_to_execution=False,
            live_activation_allowed_by_config=False,
            action="source-required",
            would_action="source-required",
            decision_status="selector_v4_disabled_by_config",
            reason="selector_v4_config_disabled",
            runtime_effect_now=False,
            candidate_use_allowed_now=False,
            source_bound_candidate_use_allowed_now=False,
            replay_candidate_use_allowed_now=False,
            risk_multiplier=0.0,
            final_risk_pct=None,
            selector_action="source-required",
            selector_reason="selector_v4_config_disabled",
            ignored_forbidden_fields=forbidden,
            source_required_fields=("selector_v4_enabled",),
            semantic_owner_handoffs=semantic_handoffs,
        )
    if _sv_3574 is None:
        return _selector_unanswered()


    confluence = _evaluate_confluence(event, side=side, cfg=cfg)
    probability = _evaluate_probability_debate(event, candidate_action=candidate_action, cfg=cfg)
    broker_net = _evaluate_broker_net(event, cfg=cfg)
    cost = _evaluate_cost(event, cfg=cfg)
    lifecycle = _evaluate_lifecycle(event)
    ultimate_package = _evaluate_ultimate_candidate_package(
        event,
        cfg=cfg,
        generated_utc=package_generated_utc,
    )
    ultimate_package_apply = bool(
        ultimate_package is not None
        and _truthy(cfg.get("ultimate_candidate_package_apply_to_execution", False))
    )
    ultimate_package_replay_admission_enabled = bool(
        ultimate_package is not None
        and _truthy(
            cfg.get(
                "ultimate_candidate_package_replay_admission_enabled",
                cfg.get("ultimate_candidate_package_shadow_enabled", False),
            )
        )
    )
    ultimate_package_match_count = (
        int(ultimate_package.get("matched_sleeve_count") or 0)
        if isinstance(ultimate_package, Mapping)
        else 0
    )
    ultimate_package_admission_count = (
        int(ultimate_package.get("admission_sleeve_match_count") or 0)
        if isinstance(ultimate_package, Mapping)
        else 0
    )
    ultimate_package_role_disposition = (
        _policy_key(ultimate_package.get("role_disposition"))
        if isinstance(ultimate_package, Mapping)
        else ""
    )
    ultimate_package_source_bound_raw_allowed = bool(
        isinstance(ultimate_package, Mapping)
        and ultimate_package.get("source_bound_package_candidate_use_allowed") is True
    )
    ultimate_package_explicit_executable = (
        ultimate_package.get("package_replay_executable_candidate_use_allowed")
        if isinstance(ultimate_package, Mapping)
        and "package_replay_executable_candidate_use_allowed" in ultimate_package
        else ultimate_package.get("replay_candidate_use_allowed_now")
        if isinstance(ultimate_package, Mapping)
        and "replay_candidate_use_allowed_now" in ultimate_package
        else None
    )
    ultimate_package_explicit_executable_reason = (
        str(
            ultimate_package.get("package_replay_executable_candidate_use_allowed_reason")
            or ultimate_package.get("replay_candidate_use_allowed_now_reason")
            or ""
        )
        if isinstance(ultimate_package, Mapping)
        else ""
    )
    ultimate_package_quality_contract = (
        _quality_contract_detail(ultimate_package)
        if isinstance(ultimate_package, Mapping)
        else {"valid": False, "failures": ("ultimate_package_packet_missing",)}
    )
    if isinstance(ultimate_package, Mapping) and ultimate_package_quality_contract.get(
        "failures"
    ):
        ultimate_package = dict(ultimate_package)
        existing_quality_failures = [
            _text(failure)
            for failure in (
                ultimate_package.get("candidate_decision_quality_provenance_failures")
                or ()
            )
            if _text(failure)
        ]
        ultimate_package["candidate_decision_quality_provenance_failures"] = list(
            dict.fromkeys(
                [
                    *existing_quality_failures,
                    *[
                        _text(failure)
                        for failure in ultimate_package_quality_contract.get(
                            "failures"
                        )
                        or ()
                        if _text(failure)
                    ],
                ]
            )
        )
        if _truthy(
            ultimate_package.get("package_replay_executable_candidate_use_allowed")
        ):
            ultimate_package[
                "raw_package_replay_executable_candidate_use_allowed_before_quality_contract"
            ] = ultimate_package.get("package_replay_executable_candidate_use_allowed")
            ultimate_package["package_replay_executable_candidate_use_allowed"] = False
            first_quality_failure = (
                ultimate_package["candidate_decision_quality_provenance_failures"][0]
                if ultimate_package["candidate_decision_quality_provenance_failures"]
                else "candidate_decision_quality_contract_failed"
            )
            ultimate_package[
                "package_replay_executable_candidate_use_allowed_reason"
            ] = f"candidate_decision_quality_contract_failed:{first_quality_failure}"
    ultimate_package_quality_contract_valid = bool(
        ultimate_package_quality_contract.get("valid")
    )
    ultimate_package_source_bound_allowed = bool(
        ultimate_package_source_bound_raw_allowed
        and ultimate_package_explicit_executable is not None
        and _truthy(ultimate_package_explicit_executable)
        and ultimate_package_quality_contract_valid
    )
    ultimate_package_soft_admission_override_allowed = bool(
        ultimate_package_replay_admission_enabled
        and ultimate_package_match_count > 0
        and ultimate_package_admission_count > 0
        and ultimate_package_source_bound_allowed
        and ultimate_package_role_disposition
        not in PACKAGE_NON_EXECUTABLE_ROLE_DISPOSITIONS
    )
    ultimate_package_source_bound_replay_authority_allowed = bool(
        ultimate_package_replay_admission_enabled
        and ultimate_package_match_count > 0
        and ultimate_package_admission_count > 0
        and ultimate_package_source_bound_raw_allowed
        and ultimate_package_quality_contract_valid
        and ultimate_package_role_disposition
        not in PACKAGE_NON_EXECUTABLE_ROLE_DISPOSITIONS
        and not live_allowed
        and not _truthy(cfg.get("ultimate_candidate_package_live_activation_allowed", False))
        and not _truthy(cfg.get("ultimate_candidate_package_final_package_selected", False))
    )
    ultimate_package_replay_allowed_sides = tuple(
        dict.fromkeys(
            normalized
            for item in _text_values(
                cfg.get("ultimate_candidate_package_replay_execution_allowed_sides")
                or cfg.get("ultimate_candidate_package_repaired_profile_allowed_sides")
            )
            if (normalized := _direction(item))
        )
    )
    ultimate_package_side_policy_applies = bool(
        ultimate_package_replay_allowed_sides
        and ultimate_package_match_count > 0
        and (ultimate_package_replay_admission_enabled or ultimate_package_apply)
    )
    ultimate_package_replay_side_allowed = bool(
        not ultimate_package_side_policy_applies
        or side in ultimate_package_replay_allowed_sides
    )

    source_required = sorted(
        set(
            confluence["missing_fields"]
            + probability["missing_fields"]
            + broker_net["missing_fields"]
            + cost["missing_fields"]
            + lifecycle["missing_fields"]
        )
    )
    hard_reject: list[str] = []
    reduce_reasons: list[str] = []
    queue_reasons: list[str] = []

    if (_sv_3767 := _selector_side(
        'sv4_3767_ultimate_candidate_package_side_not_allowed_by_r',
        bool(ultimate_package_side_policy_applies and not ultimate_package_replay_side_allowed),
        'ultimate_candidate_package_side_not_allowed_by_r',
        'other_side',
        'Condition: ultimate_package_side_policy_applies and not ultimate_package_replay_side_allowed. Which side of this condition is the decision?',
        true_text='ultimate_candidate_package_side_not_allowed_by_r rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true":
        hard_reject.append("ultimate_candidate_package_side_not_allowed_by_repaired_profile")

    if (_sv_3770 := _selector_side(
        'sv4_3770_same_symbol_duplicate_exposure',
        bool(lifecycle["duplicate_exposure"]),
        'same_symbol_duplicate_exposure',
        'other_side',
        'Condition: lifecycle["duplicate_exposure"]. Which side of this condition is the decision?',
        true_text='same_symbol_duplicate_exposure rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true":
        hard_reject.append("same_symbol_duplicate_exposure")
    if (_sv_3772 := _selector_side(
        'sv4_3772_same_symbol_conflict',
        bool(lifecycle["same_symbol_conflict"] in {
        "opposite-direction-open",
        "long-short-conflict",
        "ambiguous-hedge",
        "duplicate-exposure",
    }),
        'same_symbol_conflict',
        'other_side',
        'Condition: lifecycle["same_symbol_conflict"] in {\n        "opposite-direction-open",\n        "long-short-conflict",\n        "ambiguous-hedge",\n        "duplicate-exposure",\n    }. Which side of this condition is the decision?',
        true_text='same_symbol_conflict rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true":
        hard_reject.append(f"same_symbol_conflict:{lifecycle['same_symbol_conflict']}")
    hard_reject.extend(confluence["hard_avoid_reasons"])
    if (_sv_3780 := _selector_side(
        'sv4_3780_probability_debate_veto',
        bool(probability["vetoes"]),
        'probability_debate_veto',
        'other_side',
        'Condition: probability["vetoes"]. Which side of this condition is the decision?',
        true_text='probability_debate_veto rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true":
        hard_reject.extend(f"probability_debate_veto:{item}" for item in probability["vetoes"])

    selected_action = probability["selected_action"]
    if (_sv_3784 := _selector_side(
        'sv4_3784_probability_debate_selected_opposite_action',
        bool(selected_action in {"long", "short"} and selected_action != candidate_action),
        'probability_debate_selected_opposite_action',
        'other_side',
        'Condition: selected_action in {"long", "short"} and selected_action != candidate_action. Which side of this condition is the decision?',
        true_text='probability_debate_selected_opposite_action rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true":
        hard_reject.append(f"probability_debate_selected_opposite_action:{selected_action}")
    if (_sv_3786 := _selector_side(
        'sv4_3786_probability_debate_selected_wait',
        bool(selected_action == "wait"),
        'probability_debate_selected_wait',
        'other_side',
        'Condition: selected_action == "wait". Which side of this condition is the decision?',
        true_text='probability_debate_selected_wait queues this candidate.',
        false_text='other_side does not queue this candidate.',
    )) == "true":
        queue_reasons.append("probability_debate_selected_wait")
    if (_sv_3788 := _selector_side(
        'sv4_3788_probability_debate_selected_source_required',
        bool(selected_action == "source-required"),
        'probability_debate_selected_source_required',
        'other_side',
        'Condition: selected_action == "source-required". Which side of this condition is the decision?',
        true_text='This side stands: probability_debate_selected_source_required.',
        false_text='The other side stands: other_side.',
    )) == "true":
        source_required.append("probability_debate_selected_source_required")

    broker_ev = broker_net["broker_net_expectancy_r"]
    stress_ev = broker_net["stress_expectancy_r"]
    thesis = probability["candidate_thesis"]
    thesis_ev = thesis.get("EV")
    thesis_probability = _score01(thesis.get("probability"))
    uncertainty = thesis.get("uncertainty") or 0.0
    confluence_score = confluence["score"]
    total_cost = cost["expected_total_cost_r"] or 0.0
    min_trade_ev = _float(cfg.get("selector_v4_min_broker_net_trade_ev_r"))
    if min_trade_ev is None:
        min_trade_ev = 0.10
    min_no_trade_ev = _float(cfg.get("selector_v4_min_no_trade_ev_r"))
    if min_no_trade_ev is None:
        min_no_trade_ev = 0.02
    min_confluence = _float(cfg.get("selector_v4_min_confluence_score"))
    if min_confluence is None:
        min_confluence = 0.15
    max_uncertainty = _float(cfg.get("selector_v4_max_uncertainty_for_full_risk"))
    if max_uncertainty is None:
        max_uncertainty = 0.35
    max_cost_r = _float(cfg.get("selector_v4_max_expected_cost_r"))
    if max_cost_r is None:
        max_cost_r = 0.20
    reduce_multiplier = _float(cfg.get("selector_v4_reduce_risk_multiplier"))
    if reduce_multiplier is None:
        reduce_multiplier = 0.5

    ev_candidates: list[tuple[str, float]] = []
    if isinstance(broker_ev, (float, int)):
        ev_candidates.append(("broker_net_expectancy_r", float(broker_ev)))
    if isinstance(stress_ev, (float, int)):
        ev_candidates.append(("stress_expectancy_r", float(stress_ev)))
    if isinstance(thesis_ev, (float, int)):
        ev_candidates.append(
            ("probability_thesis_ev_after_cost", float(thesis_ev) - total_cost)
        )
    broker_net_admission_ev = min(
        (value for _source, value in ev_candidates),
        default=None,
    )
    if (_sv_3831 := _selector_side(
        'sv4_3831_broker_net_admission_ev_negative_after_cost',
        bool(broker_net_admission_ev is not None and broker_net_admission_ev < 0.0),
        'broker_net_admission_ev_negative_after_cost',
        'other_side',
        'Condition: broker_net_admission_ev is not None and broker_net_admission_ev < 0.0. Which side of this condition is the decision?',
        true_text='broker_net_admission_ev_negative_after_cost rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true":
        hard_reject.append("broker_net_admission_ev_negative_after_cost")
    if (
        cost.get("pretrade_cost_packet_refused")
        and _truthy(cfg.get("selector_v4_enforce_broker_net_cost_packet_refusal", True))
    ):
        reasons = cost.get("pretrade_cost_refusal_reasons") or []
        if (_sv_3838 := _selector_side(
        'sv4_3838_broker_net_pretrade_cost_packet_refused',
        bool(reasons),
        'broker_net_pretrade_cost_packet_refused',
        'broker_net_pretrade_cost_packet_refused_not',
        'Condition: reasons. Which side of this condition is the decision?',
        true_text='broker_net_pretrade_cost_packet_refused rejects this candidate.',
        false_text='broker_net_pretrade_cost_packet_refused_not does not reject this candidate.',
    )) == "true":
            hard_reject.extend(
                f"broker_net_pretrade_cost_packet_refused:{reason}" for reason in reasons
            )
        elif _sv_3838 is not None and _sv_3838 == "false":
            hard_reject.append("broker_net_pretrade_cost_packet_refused")
    if (_sv_3844 := _selector_side(
        'sv4_3844_cost_authority_block_reason',
        bool(cost.get("cost_authority_block_reason")),
        'cost_authority_block_reason',
        'other_side',
        'Condition: cost.get("cost_authority_block_reason"). Which side of this condition is the decision?',
        true_text='cost_authority_block_reason rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true":
        hard_reject.append(str(cost.get("cost_authority_block_reason")))
    if (_sv_3846 := _selector_side(
        'sv4_3846_pretrade_cost_above_selector_v4_ceiling',
        bool(total_cost > max_cost_r),
        'pretrade_cost_above_selector_v4_ceiling',
        'other_side',
        'Condition: total_cost > max_cost_r. Which side of this condition is the decision?',
        true_text='pretrade_cost_above_selector_v4_ceiling rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true":
        hard_reject.append("pretrade_cost_above_selector_v4_ceiling")
    decision_inputs = _candidate_decision_inputs(event)
    package_new_entry_signed_authority = (
        _package_new_entry_signed_authority_detail(
            event,
            decision_inputs,
            ultimate_package if isinstance(ultimate_package, Mapping) else None,
        )
    )
    package_new_entry_signed_authority_ok = bool(
        package_new_entry_signed_authority.get("signed")
    )
    package_new_entry_signed_payload = package_new_entry_signed_authority.get(
        "package_new_entry_authority_payload"
    )
    package_new_entry_signed_payload = (
        package_new_entry_signed_payload
        if package_new_entry_signed_authority_ok
        and isinstance(package_new_entry_signed_payload, Mapping)
        else {}
    )
    selected_cell = _first_mapping(event, "selected_cell", "broker_net_selected_cell")
    event_fillability = _first_mapping(event, "predecision_limit_fillability")
    decision_fillability = _first_mapping(
        decision_inputs,
        "predecision_limit_fillability",
    )
    packet_limit_fillability_probability = _first_score01(
        _first_value(
            decision_inputs,
            "limit_fillability_probability",
            "predecision_limit_fillability_probability",
        ),
        _first_value(
            event,
            "limit_fillability_probability",
            "predecision_limit_fillability_probability",
        ),
        _first_value(
            decision_fillability,
            "fill_probability",
            "expected_fill_probability",
            "limit_fill_probability",
        ),
        _first_value(
            event_fillability,
            "fill_probability",
            "expected_fill_probability",
            "limit_fill_probability",
        ),
    )
    packet_fill_probability = _first_score01(
        _first_value(
            event,
            "entry_quality_fill_probability",
            "heuristic_fill_probability",
            "fill_probability",
            "candidate_fill_probability",
            "selected_fill_probability",
        ),
        _first_value(
            decision_inputs,
            "entry_quality_fill_probability",
            "heuristic_fill_probability",
            "fill_probability",
            "candidate_fill_probability",
            "selected_fill_probability",
        ),
        _first_value(selected_cell, "fill_probability"),
    )
    learned = _evaluate_learned_edge(event, cfg=cfg)
    if (_sv_3918 := _selector_side(
        'sv4_3918_heuristic_probability',
        bool(learned is not None),
        'heuristic_probability',
        'other_side',
        'Condition: learned is not None. Which side of this condition is the decision?',
        true_text='This side stands: heuristic_probability.',
        false_text='The other side stands: other_side.',
    )) == "true":
        # Heuristic values stay in the packet as shadow fields next to the
        # learned scores they were replaced by.
        learned["heuristic_probability"] = thesis_probability
        learned["heuristic_ev_r"] = broker_net_admission_ev
        learned["heuristic_fill_probability"] = packet_fill_probability
        source_required.extend(learned["source_required_fields"])
    selector_source_completeness = _first_score01(
        _first_value(
            event,
            "source_completeness",
            "selected_cell_source_completeness",
        ),
        _first_value(
            decision_inputs,
            "source_completeness",
            "selected_cell_source_completeness",
        ),
        _first_value(
            _first_mapping(event, "candidate_feature_signal"),
            "source_completeness",
        ),
        thesis.get("source_completeness"),
        _first_value(selected_cell, "source_completeness"),
        1.0 if event.get("source_window_complete") is True else None,
        0.0 if event.get("source_window_complete") is False else None,
    )
    admission_quality = _evaluate_admission_quality_guard(
        event,
        cfg=cfg,
        broker_net_admission_ev=broker_net_admission_ev,
        total_cost_r=total_cost,
        probability=thesis_probability,
        fill_probability=packet_fill_probability,
        learned=learned,
        source_completeness=selector_source_completeness,
    )
    if (
        (_sv_3955 := _selector_side(
        'sv4_3955_ultimate_candidate_package_no_shadow_sleeve_matc',
        bool(ultimate_package is not None
        and _truthy(cfg.get("ultimate_candidate_package_require_shadow_match_for_selector_v4"))
        and int(ultimate_package.get("matched_sleeve_count") or 0) <= 0),
        'ultimate_candidate_package_no_shadow_sleeve_matc',
        'other_side',
        'Condition: ultimate_package is not None\n        and _truthy(cfg.get("ultimate_candidate_package_require_shadow_match_for_selector_v4"))\n        and int(ultimate_package.get("matched_sleeve_count") or 0) <= 0. Which side of this condition is the decision?',
        true_text='ultimate_candidate_package_no_shadow_sleeve_matc rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true"
    ):
        hard_reject.append("ultimate_candidate_package_no_shadow_sleeve_match")
    source_required.extend(admission_quality["source_required_fields"])
    admission_quality_hard_reject = list(admission_quality["hard_reject_reasons"])
    admission_quality_reduced_risk = list(admission_quality["reduced_risk_reasons"])
    router_refusal_reason = "admission_quality_dynamic_router_refused_candidate_use"
    cost_packet_status = _upper(cost.get("pretrade_cost_packet_status"))
    cost_source_gap_status = str(cost.get("cost_source_gap_status") or "")
    cost_authority = str(cost.get("cost_authority") or "")
    broker_cost_passed_for_package_router = bool(
        not cost.get("pretrade_cost_packet_refused")
        and total_cost <= max_cost_r
        and cost_packet_status in {"PASSED", "PASS", "OK"}
        and cost_source_gap_status == "source_bound_cost_authority_present"
        and cost_authority == "broker_calibrated_replay_cost"
        and not _truthy(cost.get("candidate_cost_r_fallback_is_authority"))
    )
    ultimate_package_fields = (
        ultimate_package if isinstance(ultimate_package, Mapping) else {}
    )
    package_quality_expected_net_r = _float(
        _first_present_value(
            package_new_entry_signed_payload.get("expected_net_r"),
            ultimate_package_fields.get("expected_net_r"),
            ultimate_package_fields.get("candidate_expected_net_r"),
        )
    )
    if package_quality_expected_net_r is None:
        package_quality_expected_net_r = broker_net_admission_ev
    package_quality_probability = _first_score01(
        package_new_entry_signed_payload.get("probability"),
        ultimate_package_fields.get("probability"),
        ultimate_package_fields.get("candidate_probability"),
    )
    if package_quality_probability is None:
        package_quality_probability = thesis_probability
    package_quality_fill_probability = _first_score01(
        package_new_entry_signed_payload.get("fill_probability"),
        ultimate_package_fields.get("entry_quality_fill_probability"),
        ultimate_package_fields.get("heuristic_fill_probability"),
        ultimate_package_fields.get("fill_probability"),
        ultimate_package_fields.get("candidate_fill_probability"),
    )
    if package_quality_fill_probability is None:
        package_quality_fill_probability = packet_fill_probability
    package_router_refusal_execution_fill_probability = _first_score01(
        package_new_entry_signed_payload.get("execution_fill_probability"),
        package_new_entry_signed_payload.get(
            "predecision_limit_fillability_probability"
        ),
        package_new_entry_signed_payload.get("limit_fillability_probability"),
        ultimate_package_fields.get("execution_fill_probability"),
        ultimate_package_fields.get("predecision_limit_fillability_probability"),
        ultimate_package_fields.get("limit_fillability_probability"),
    )
    package_execution_fill_probability = (
        package_router_refusal_execution_fill_probability
    )
    package_poi_lifecycle = package_new_entry_signed_payload.get(
        "causal_poi_lifecycle"
    )
    if not isinstance(package_poi_lifecycle, Mapping):
        package_poi_lifecycle = row_causal_poi_lifecycle_envelope(event)
    package_poi_lifecycle_required = bool(
        package_new_entry_signed_payload.get("causal_poi_lifecycle_required") is True
        or row_causal_poi_lifecycle_required(event)
    )
    package_poi_lifecycle_failures = (
        list(
            causal_poi_lifecycle_contract_failures(
                package_poi_lifecycle,
                decision_time_utc=_first_present_value(
                    event.get("decision_time_utc"),
                    event.get("candle_close_utc"),
                    event.get("source_candle_time_utc"),
                    package_poi_lifecycle.get("decision_time_utc"),
                ),
            )
        )
        if package_poi_lifecycle_required
        else []
    )
    package_poi_scheduler_rankable_now = bool(
        not package_poi_lifecycle_required
        or (
            not package_poi_lifecycle_failures
            and package_poi_lifecycle.get("scheduler_rankable_now") is True
        )
    )
    package_source_completeness = _first_score01(
        package_new_entry_signed_payload.get("source_completeness"),
        ultimate_package_fields.get("source_completeness"),
    )
    if package_source_completeness is None:
        package_source_completeness = selector_source_completeness
    positive_predecision_package_edge = bool(
        broker_ev is not None
        and broker_ev > 0.0
        and stress_ev is not None
        and stress_ev > 0.0
        and package_quality_expected_net_r is not None
        and package_quality_expected_net_r > 0.0
    )
    ultimate_package_derived_executable_min_source_completeness = _float(
        cfg.get(
            "ultimate_candidate_package_derived_executable_min_source_completeness",
            cfg.get(
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_source_completeness",
                cfg.get("selector_v4_calibrated_min_source_completeness"),
            ),
        )
    )
    if ultimate_package_derived_executable_min_source_completeness is None:
        ultimate_package_derived_executable_min_source_completeness = 0.65
    ultimate_package_derived_executable_quality_authority = bool(
        (
            ultimate_package_explicit_executable is None
            or (
                not _truthy(ultimate_package_explicit_executable)
                and (
                    ultimate_package_explicit_executable_reason
                    in {
                        "broker_cost_packet_status_missing",
                        "broker_cost_source_gap_status_missing",
                    }
                    or ultimate_package_explicit_executable_reason.startswith(
                        "source_completeness_below_floor:"
                    )
                    or ultimate_package_explicit_executable_reason.startswith(
                        "source_completeness_status_"
                    )
                )
            )
        )
        and broker_cost_passed_for_package_router
        and package_quality_expected_net_r is not None
        and package_quality_expected_net_r > 0.0
        and package_quality_probability is not None
        and package_execution_fill_probability is not None
        and package_source_completeness is not None
        and package_source_completeness
        >= ultimate_package_derived_executable_min_source_completeness
        and ultimate_package_quality_contract_valid
        and package_poi_scheduler_rankable_now
    )
    ultimate_package_source_bound_allowed = bool(
        ultimate_package_source_bound_raw_allowed
        and (
            (
                ultimate_package_explicit_executable is not None
                and _truthy(ultimate_package_explicit_executable)
                and ultimate_package_quality_contract_valid
            )
            or ultimate_package_derived_executable_quality_authority
        )
    )
    ultimate_package_soft_admission_override_allowed = bool(
        ultimate_package_replay_admission_enabled
        and ultimate_package_match_count > 0
        and ultimate_package_admission_count > 0
        and ultimate_package_source_bound_allowed
        and ultimate_package_role_disposition
        not in PACKAGE_NON_EXECUTABLE_ROLE_DISPOSITIONS
    )
    router_refusal_min_expected_net_r = _float(
        cfg.get(
            "ultimate_candidate_package_positive_predecision_router_refusal_min_expected_net_r"
        )
    )
    if router_refusal_min_expected_net_r is None:
        router_refusal_min_expected_net_r = 1.10
    router_refusal_min_probability = _float(
        cfg.get(
            "ultimate_candidate_package_positive_predecision_router_refusal_min_probability"
        )
    )
    if router_refusal_min_probability is None:
        router_refusal_min_probability = 0.90
    router_refusal_min_fill_probability = _float(
        cfg.get(
            "ultimate_candidate_package_positive_predecision_router_refusal_min_fill_probability"
        )
    )
    if router_refusal_min_fill_probability is None:
        router_refusal_min_fill_probability = 0.90
    router_refusal_min_source_completeness = _float(
        cfg.get(
            "ultimate_candidate_package_positive_predecision_router_refusal_min_source_completeness"
        )
    )
    if router_refusal_min_source_completeness is None:
        router_refusal_min_source_completeness = 0.95
    (
        selected_policy_expected_net_calibration_status,
        selected_policy_expected_net_calibration_source_boundary,
        selected_policy_expected_net_calibrated,
    ) = _selected_policy_expected_net_calibration(
        ultimate_package,
        decision_inputs,
        event,
    )
    router_refusal_expected_net_policy_calibration_required = _truthy(
        cfg.get(
            "selector_v4_router_refusal_expected_net_policy_calibration_required",
            cfg.get(
                "scheduler_v4_best_trade_allocator_selected_policy_expected_net_calibration_required_for_new_risk",
                False,
            ),
        )
    )
    router_refusal_expected_net_policy_calibration_allowed = bool(
        not router_refusal_expected_net_policy_calibration_required
        or selected_policy_expected_net_calibrated
    )
    router_refusal_quality_allowed = bool(
        package_quality_expected_net_r is not None
        and package_quality_expected_net_r >= router_refusal_min_expected_net_r
        and package_quality_probability is not None
        and package_quality_probability >= router_refusal_min_probability
        and package_router_refusal_execution_fill_probability is not None
        and package_router_refusal_execution_fill_probability
        >= router_refusal_min_fill_probability
        and package_source_completeness is not None
        and package_source_completeness >= router_refusal_min_source_completeness
        and router_refusal_expected_net_policy_calibration_allowed
        and package_poi_scheduler_rankable_now
    )
    router_refusal_softening_allowed_origin_families = tuple(
        dict.fromkeys(
            alias
            for item in _text_values(
                cfg.get(
                    "ultimate_candidate_package_dynamic_router_refusal_softening_allowed_origin_families"
                )
                or cfg.get(
                    "ultimate_candidate_package_router_refusal_softening_allowed_origin_families"
                )
            )
            for alias in _router_refusal_origin_family_aliases(item)
        )
    )
    router_refusal_raw_origin_family_candidates = _origin_family_candidates(event)
    router_refusal_origin_family_candidates = tuple(
        dict.fromkeys(
            alias
            for family in router_refusal_raw_origin_family_candidates
            for alias in _router_refusal_origin_family_aliases(family)
        )
    )
    router_refusal_origin_family = (
        router_refusal_origin_family_candidates[0]
        if router_refusal_origin_family_candidates
        else _origin_family(event)
    )
    router_refusal_origin_family_allowed = bool(
        not router_refusal_softening_allowed_origin_families
        or any(
            family in router_refusal_softening_allowed_origin_families
            for family in router_refusal_origin_family_candidates
        )
    )
    source_bound_router_refusal_package_role_materialization_allowed = (
        ultimate_package_role_disposition == "admission_candidate"
        or ultimate_package_role_disposition in PACKAGE_REDUCED_RISK_ROLE_DISPOSITIONS
    )
    router_refusal_was_present = (
        router_refusal_reason in admission_quality["hard_reject_reasons"]
        or router_refusal_reason in admission_quality["reduced_risk_reasons"]
    )
    positive_package_router_refusal_softening_allowed = bool(
        ultimate_package_soft_admission_override_allowed
        and _truthy(
            cfg.get(
                "ultimate_candidate_package_positive_predecision_router_refusal_softening_enabled",
                True,
            )
        )
        and broker_cost_passed_for_package_router
        and positive_predecision_package_edge
        and router_refusal_quality_allowed
        and router_refusal_origin_family_allowed
    )
    source_bound_router_refusal_materialization_min_expected_net_r = _float(
        cfg.get(
            "ultimate_candidate_package_source_bound_router_refusal_materialization_min_expected_net_r",
            cfg.get(
                "scheduler_v4_best_trade_allocator_source_bound_router_refusal_replay_materialization_min_expected_net_r",
            ),
        )
    )
    if source_bound_router_refusal_materialization_min_expected_net_r is None:
        source_bound_router_refusal_materialization_min_expected_net_r = 0.55
    source_bound_router_refusal_materialization_min_probability = _float(
        cfg.get(
            "ultimate_candidate_package_source_bound_router_refusal_materialization_min_probability",
            cfg.get(
                "scheduler_v4_best_trade_allocator_source_bound_router_refusal_replay_materialization_min_probability",
            ),
        )
    )
    if source_bound_router_refusal_materialization_min_probability is None:
        source_bound_router_refusal_materialization_min_probability = 0.70
    source_bound_router_refusal_materialization_min_fill_probability = _float(
        cfg.get(
            "ultimate_candidate_package_source_bound_router_refusal_materialization_min_fill_probability",
            cfg.get(
                "scheduler_v4_best_trade_allocator_source_bound_router_refusal_replay_materialization_min_fill_probability",
            ),
        )
    )
    if source_bound_router_refusal_materialization_min_fill_probability is None:
        source_bound_router_refusal_materialization_min_fill_probability = 0.55
    source_bound_router_refusal_materialization_min_source_completeness = _float(
        cfg.get(
            "ultimate_candidate_package_source_bound_router_refusal_materialization_min_source_completeness",
            cfg.get(
                "scheduler_v4_best_trade_allocator_source_bound_router_refusal_replay_materialization_min_source_completeness",
            ),
        )
    )
    if source_bound_router_refusal_materialization_min_source_completeness is None:
        source_bound_router_refusal_materialization_min_source_completeness = 0.95
    source_bound_router_refusal_materialization_fill_probability = (
        package_router_refusal_execution_fill_probability
    )
    source_bound_router_refusal_materialization_quality_allowed = bool(
        package_quality_expected_net_r is not None
        and package_quality_expected_net_r
        >= source_bound_router_refusal_materialization_min_expected_net_r
        and package_quality_probability is not None
        and package_quality_probability
        >= source_bound_router_refusal_materialization_min_probability
        and source_bound_router_refusal_materialization_fill_probability is not None
        and source_bound_router_refusal_materialization_fill_probability
        >= source_bound_router_refusal_materialization_min_fill_probability
        and package_source_completeness is not None
        and package_source_completeness
        >= source_bound_router_refusal_materialization_min_source_completeness
        and router_refusal_expected_net_policy_calibration_allowed
        and package_poi_scheduler_rankable_now
    )
    source_bound_router_refusal_authority_allowed = bool(
        ultimate_package_source_bound_replay_authority_allowed
        and source_bound_router_refusal_package_role_materialization_allowed
    )
    source_bound_router_refusal_open_reduced_materialization_allowed = bool(
        router_refusal_was_present
        and (
            ultimate_package_soft_admission_override_allowed
            or source_bound_router_refusal_authority_allowed
        )
        and _truthy(
            cfg.get(
                "ultimate_candidate_package_source_bound_router_refusal_open_reduced_materialization_enabled",
                cfg.get(
                    "ultimate_candidate_package_source_bound_router_refusal_replay_materialization_enabled",
                    False,
                ),
            )
        )
        and broker_cost_passed_for_package_router
        and positive_predecision_package_edge
        and source_bound_router_refusal_materialization_quality_allowed
        and source_bound_router_refusal_package_role_materialization_allowed
    )
    positive_package_router_refusal_full_trade_release_requested = bool(
        positive_package_router_refusal_softening_allowed
        and _truthy(
            cfg.get(
                "ultimate_candidate_package_positive_predecision_router_refusal_full_trade_allowed",
                False,
            )
        )
    )
    positive_package_router_refusal_full_trade_release_allowed = bool(
        positive_package_router_refusal_full_trade_release_requested
        and positive_package_router_refusal_softening_allowed
        and ultimate_package_soft_admission_override_allowed
        and broker_cost_passed_for_package_router
        and positive_predecision_package_edge
        and router_refusal_quality_allowed
        and router_refusal_origin_family_allowed
        and router_refusal_expected_net_policy_calibration_allowed
        and ultimate_package_quality_contract_valid
        and not live_allowed
        and not _truthy(cfg.get("ultimate_candidate_package_live_activation_allowed", False))
        and not _truthy(cfg.get("ultimate_candidate_package_final_package_selected", False))
    )
    positive_package_router_refusal_open_reduced_allowed = bool(
        positive_package_router_refusal_softening_allowed
        and _truthy(
            cfg.get(
                "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk_allowed",
                False,
            )
        )
    )
    router_refusal_softening_allowed = bool(
        positive_package_router_refusal_softening_allowed
        or source_bound_router_refusal_open_reduced_materialization_allowed
        or (
            ultimate_package_soft_admission_override_allowed
            and _truthy(
                cfg.get(
                    "ultimate_candidate_package_soften_dynamic_router_refusal_enabled",
                    False,
                )
            )
            and (
                not _truthy(
                    cfg.get(
                        "ultimate_candidate_package_soften_dynamic_router_refusal_requires_broker_cost_pass",
                        True,
                    )
                )
                or broker_cost_passed_for_package_router
            )
            and router_refusal_origin_family_allowed
            and router_refusal_expected_net_policy_calibration_allowed
        )
    )
    if router_refusal_softening_allowed:
        admission_quality_hard_reject = [
            reason
            for reason in admission_quality_hard_reject
            if reason != router_refusal_reason
        ]
        admission_quality_reduced_risk = [
            reason
            for reason in admission_quality_reduced_risk
            if reason != router_refusal_reason
        ]
        if positive_package_router_refusal_softening_allowed and router_refusal_was_present:
            if positive_package_router_refusal_full_trade_release_allowed:
                pass
            elif positive_package_router_refusal_open_reduced_allowed:
                admission_quality_reduced_risk.append(
                    "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk"
                )
            elif not positive_package_router_refusal_full_trade_release_allowed:
                admission_quality_reduced_risk.append(
                    "ultimate_candidate_package_dynamic_router_refusal_softened_reduce_risk"
                )
        elif source_bound_router_refusal_open_reduced_materialization_allowed:
            admission_quality_reduced_risk.append(
                "source_bound_router_refusal_open_reduced_materialized_for_replay"
            )
        elif router_refusal_was_present:
            admission_quality_reduced_risk.append(
                "ultimate_candidate_package_dynamic_router_refusal_softened_reduce_risk"
            )
    hard_reject.extend(admission_quality_hard_reject)
    reduce_reasons.extend(admission_quality_reduced_risk)
    off_session_entry_reason = "admission_quality_off_configured_session_entry_blocked"
    off_session_softening_min_expected_net_r = (
        _float(
            cfg.get(
                "ultimate_candidate_package_positive_predecision_off_session_min_expected_net_r"
            )
        )
        or 0.80
    )
    off_session_softening_min_probability = (
        _float(
            cfg.get(
                "ultimate_candidate_package_positive_predecision_off_session_min_probability"
            )
        )
        or 0.75
    )
    off_session_softening_min_fill_probability = (
        _float(
            cfg.get(
                "ultimate_candidate_package_positive_predecision_off_session_min_fill_probability"
            )
        )
        or 0.70
    )
    off_session_softening_min_source_completeness = (
        _float(
            cfg.get(
                "ultimate_candidate_package_positive_predecision_off_session_min_source_completeness"
            )
        )
        or 0.95
    )
    off_session_softening_quality_allowed = bool(
        package_quality_expected_net_r is not None
        and package_quality_expected_net_r >= off_session_softening_min_expected_net_r
        and package_quality_probability is not None
        and package_quality_probability >= off_session_softening_min_probability
        and package_execution_fill_probability is not None
        and package_execution_fill_probability >= off_session_softening_min_fill_probability
        and package_source_completeness is not None
        and package_source_completeness >= off_session_softening_min_source_completeness
    )
    off_session_open_reduced_min_probability = _float(
        cfg.get(
            "ultimate_candidate_package_positive_predecision_off_session_open_reduced_risk_min_probability"
        )
    )
    if off_session_open_reduced_min_probability is None:
        off_session_open_reduced_min_probability = 0.80
    positive_package_off_session_softening_allowed = bool(
        ultimate_package_soft_admission_override_allowed
        and _truthy(
            cfg.get(
                "ultimate_candidate_package_positive_predecision_off_session_softening_enabled",
                False,
            )
        )
        and broker_cost_passed_for_package_router
        and positive_predecision_package_edge
        and off_session_softening_quality_allowed
    )
    positive_package_off_session_open_reduced_allowed = bool(
        positive_package_off_session_softening_allowed
        and package_quality_probability is not None
        and package_quality_probability >= off_session_open_reduced_min_probability
    )
    off_session_entry_was_present = (
        off_session_entry_reason in hard_reject
        or off_session_entry_reason in reduce_reasons
    )
    off_session_reduce_risk_reason = (
        "ultimate_candidate_package_positive_predecision_off_session_reduce_risk"
    )
    if (_sv_4486 := _selector_side(
        'sv4_4486_ultimate_candidate_package_positive_predecision_',
        bool(positive_package_off_session_softening_allowed and off_session_entry_was_present),
        'ultimate_candidate_package_positive_predecision_',
        'other_side',
        'Condition: positive_package_off_session_softening_allowed and off_session_entry_was_present. Which side of this condition is the decision?',
        true_text='ultimate_candidate_package_positive_predecision_ reduces this candidate.',
        false_text='other_side does not reduce this candidate.',
    )) == "true":
        hard_reject = [
            reason for reason in hard_reject if reason != off_session_entry_reason
        ]
        reduce_reasons = [
            reason for reason in reduce_reasons if reason != off_session_entry_reason
        ]
        reduce_reasons.append(
            "ultimate_candidate_package_positive_predecision_off_session_open_reduced_risk"
            if positive_package_off_session_open_reduced_allowed
            else off_session_reduce_risk_reason
        )
    if ultimate_package_apply:
        if (_sv_4499 := _selector_side(
        'sv4_4499_ultimate_candidate_package_no_shadow_sleeve_matc',
        bool(ultimate_package_match_count <= 0),
        'ultimate_candidate_package_no_shadow_sleeve_matc',
        'other_side',
        'Condition: ultimate_package_match_count <= 0. Which side of this condition is the decision?',
        true_text='ultimate_candidate_package_no_shadow_sleeve_matc rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true":
            hard_reject.append("ultimate_candidate_package_no_shadow_sleeve_match")
        elif _sv_4499 is not None and (_sv_4499 := _selector_side(
        'sv4_4501_ultimate_candidate_package_source_required_hold',
        bool(ultimate_package_role_disposition == "source_required_hold"),
        'ultimate_candidate_package_source_required_hold',
        'other_side',
        'Condition: ultimate_package_role_disposition == "source_required_hold". Which side of this condition is the decision?',
        true_text='This side stands: ultimate_candidate_package_source_required_hold.',
        false_text='The other side stands: other_side.',
    )) == "true":
            source_required.append("ultimate_candidate_package_source_required_hold")
        elif _sv_4499 is not None and (_sv_4499 := _selector_side(
        'sv4_4503_ultimate_candidate_package_non_admission_sleeve_',
        bool(ultimate_package_admission_count <= 0),
        'ultimate_candidate_package_non_admission_sleeve_',
        'other_side',
        'Condition: ultimate_package_admission_count <= 0. Which side of this condition is the decision?',
        true_text='ultimate_candidate_package_non_admission_sleeve_ rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true":
            hard_reject.append("ultimate_candidate_package_non_admission_sleeve_only")
    if (_sv_4505 := _selector_side(
        'sv4_4505_selected_cell_risk_nonpositive',
        bool((broker_net["risk_pct"] or 0.0) <= 0.0 and "selected_cell.risk_pct" not in source_required),
        'selected_cell_risk_nonpositive',
        'other_side',
        'Condition: (broker_net["risk_pct"] or 0.0) <= 0.0 and "selected_cell.risk_pct" not in source_required. Which side of this condition is the decision?',
        true_text='selected_cell_risk_nonpositive rejects this candidate.',
        false_text='other_side does not reject this candidate.',
    )) == "true":
        hard_reject.append("selected_cell_risk_nonpositive")

    if confluence_score is not None and confluence_score < min_confluence:
        if (_sv_4509 := _selector_side(
        'sv4_4509_numeric_confluence_negative',
        bool(confluence_score < 0.0),
        'numeric_confluence_negative',
        'numeric_confluence_below_full_trade_floor',
        'Condition: confluence_score < 0.0. Which side of this condition is the decision?',
        true_text='numeric_confluence_negative rejects this candidate.',
        false_text='numeric_confluence_below_full_trade_floor does not reject this candidate.',
    )) == "true":
            hard_reject.append("numeric_confluence_negative")
        elif _sv_4509 is not None and _sv_4509 == "false":
            reduce_reasons.append("numeric_confluence_below_full_trade_floor")
    numeric_disagreement_min_expected_net_r = _float(
        cfg.get(
            "ultimate_candidate_package_numeric_disagreement_open_reduced_risk_min_expected_net_r"
        )
    )
    if numeric_disagreement_min_expected_net_r is None:
        numeric_disagreement_min_expected_net_r = 1.10
    numeric_disagreement_min_probability = _float(
        cfg.get(
            "ultimate_candidate_package_numeric_disagreement_open_reduced_risk_min_probability"
        )
    )
    if numeric_disagreement_min_probability is None:
        numeric_disagreement_min_probability = 0.90
    numeric_disagreement_min_fill_probability = _float(
        cfg.get(
            "ultimate_candidate_package_numeric_disagreement_open_reduced_risk_min_fill_probability"
        )
    )
    if numeric_disagreement_min_fill_probability is None:
        numeric_disagreement_min_fill_probability = 0.90
    numeric_disagreement_min_source_completeness = _float(
        cfg.get(
            "ultimate_candidate_package_numeric_disagreement_open_reduced_risk_min_source_completeness"
        )
    )
    if numeric_disagreement_min_source_completeness is None:
        numeric_disagreement_min_source_completeness = 0.95
    (
        selected_policy_expected_net_calibration_status,
        selected_policy_expected_net_calibration_source_boundary,
        selected_policy_expected_net_calibrated,
    ) = _selected_policy_expected_net_calibration(
        ultimate_package,
        decision_inputs,
        event,
    )
    numeric_expected_net_policy_calibration_required = _truthy(
        cfg.get(
            "selector_v4_numeric_disagreement_expected_net_policy_calibration_required",
            cfg.get(
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_open_reduced_expected_net_policy_calibration_required",
                False,
            ),
        )
    )
    numeric_expected_net_policy_calibration_allowed = bool(
        not numeric_expected_net_policy_calibration_required
        or selected_policy_expected_net_calibrated
    )
    numeric_disagreement_quality_allowed = bool(
        package_quality_expected_net_r is not None
        and package_quality_expected_net_r >= numeric_disagreement_min_expected_net_r
        and package_quality_probability is not None
        and package_quality_probability >= numeric_disagreement_min_probability
        and package_execution_fill_probability is not None
        and package_execution_fill_probability >= numeric_disagreement_min_fill_probability
        and package_source_completeness is not None
        and package_source_completeness >= numeric_disagreement_min_source_completeness
        and numeric_expected_net_policy_calibration_allowed
    )
    package_numeric_disagreement_open_reduced_risk_allowed = bool(
        ultimate_package_soft_admission_override_allowed
        and _truthy(
            cfg.get(
                "ultimate_candidate_package_numeric_disagreement_open_reduced_risk_enabled",
                False,
            )
        )
        and broker_cost_passed_for_package_router
        and positive_predecision_package_edge
        and numeric_disagreement_quality_allowed
    )
    numeric_reduce_risk_authority_min_expected_net_r = _float(
        cfg.get(
            "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_expected_net_r"
        )
    )
    if numeric_reduce_risk_authority_min_expected_net_r is None:
        numeric_reduce_risk_authority_min_expected_net_r = 0.70
    numeric_reduce_risk_authority_min_probability = _float(
        cfg.get(
            "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_probability"
        )
    )
    if numeric_reduce_risk_authority_min_probability is None:
        numeric_reduce_risk_authority_min_probability = 0.70
    numeric_reduce_risk_authority_min_fill_probability = _float(
        cfg.get(
            "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_fill_probability"
        )
    )
    if numeric_reduce_risk_authority_min_fill_probability is None:
        numeric_reduce_risk_authority_min_fill_probability = 0.25
    numeric_reduce_risk_authority_min_source_completeness = _float(
        cfg.get(
            "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_source_completeness"
        )
    )
    if numeric_reduce_risk_authority_min_source_completeness is None:
        numeric_reduce_risk_authority_min_source_completeness = 0.65
    numeric_reduce_risk_authority_quality_allowed = bool(
        package_quality_expected_net_r is not None
        and package_quality_expected_net_r >= numeric_reduce_risk_authority_min_expected_net_r
        and package_quality_probability is not None
        and package_quality_probability >= numeric_reduce_risk_authority_min_probability
        and package_execution_fill_probability is not None
        and package_execution_fill_probability >= numeric_reduce_risk_authority_min_fill_probability
        and package_source_completeness is not None
        and package_source_completeness >= numeric_reduce_risk_authority_min_source_completeness
        and numeric_expected_net_policy_calibration_allowed
    )
    package_numeric_disagreement_reduce_risk_authority_allowed = bool(
        ultimate_package_soft_admission_override_allowed
        and _truthy(
            cfg.get(
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_authority_enabled",
                False,
            )
        )
        and _truthy(
            cfg.get(
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_numeric_disagreement_package_new_entry_authority_enabled",
                False,
            )
        )
        and not live_allowed
        and broker_cost_passed_for_package_router
        and positive_predecision_package_edge
        and numeric_reduce_risk_authority_quality_allowed
    )
    if (_sv_4644 := _selector_side(
        'sv4_4644_ultimate_candidate_package_numeric_disagreement_',
        bool(confluence["mixed_count"]),
        'ultimate_candidate_package_numeric_disagreement_',
        'other_side',
        'Condition: confluence["mixed_count"]. Which side of this condition is the decision?',
        true_text='ultimate_candidate_package_numeric_disagreement_ reduces this candidate.',
        false_text='other_side does not reduce this candidate.',
    )) == "true":
        reduce_reasons.append(
            "ultimate_candidate_package_numeric_disagreement_open_reduced_risk"
            if package_numeric_disagreement_open_reduced_risk_allowed
            else "numeric_confluence_structured_disagreement"
        )
    if (_sv_4650 := _selector_side(
        'sv4_4650_probability_debate_uncertainty_above_full_risk_f',
        bool(uncertainty > max_uncertainty),
        'probability_debate_uncertainty_above_full_risk_f',
        'other_side',
        'Condition: uncertainty > max_uncertainty. Which side of this condition is the decision?',
        true_text='probability_debate_uncertainty_above_full_risk_f reduces this candidate.',
        false_text='other_side does not reduce this candidate.',
    )) == "true":
        reduce_reasons.append("probability_debate_uncertainty_above_full_risk_floor")
    if (_sv_4652 := _selector_side(
        'sv4_4652_open_trade_competition',
        bool(lifecycle["open_trade_competition_status"] in {"stale-open-wins", "new-candidate-not-best"}),
        'open_trade_competition',
        'other_side',
        'Condition: lifecycle["open_trade_competition_status"] in {"stale-open-wins", "new-candidate-not-best"}. Which side of this condition is the decision?',
        true_text='open_trade_competition queues this candidate.',
        false_text='other_side does not queue this candidate.',
    )) == "true":
        queue_reasons.append(f"open_trade_competition:{lifecycle['open_trade_competition_status']}")

    fill_floor_softening_min_fill_probability = None
    fill_floor_softening_fillability_ok = False
    fill_floor_softening_signed_authority_ok = False
    if ultimate_package_soft_admission_override_allowed and _truthy(
        cfg.get("ultimate_candidate_package_soften_selector_fill_floor_enabled", False)
    ):
        softened_rejects: list[str] = []
        retained_rejects: list[str] = []
        fill_floor_softening_requires_broker_cost_pass = _truthy(
            cfg.get(
                "ultimate_candidate_package_soften_selector_fill_floor_requires_broker_cost_pass",
                True,
            )
        )
        fill_floor_softening_requires_positive_edge = _truthy(
            cfg.get(
                "ultimate_candidate_package_soften_selector_fill_floor_requires_positive_predecision_edge",
                True,
            )
        )
        fill_floor_softening_min_fill_probability = _float(
            cfg.get(
                "ultimate_candidate_package_soften_selector_fill_floor_min_fill_probability",
                cfg.get(
                    "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_fill_probability",
                    cfg.get("selector_reduce_risk_package_fill_floor_min_fill_probability"),
                ),
            )
        )
        if fill_floor_softening_min_fill_probability is None:
            fill_floor_softening_min_fill_probability = 0.20
        fill_floor_softening_broker_cost_ok = (
            broker_cost_passed_for_package_router
            or not fill_floor_softening_requires_broker_cost_pass
        )
        fill_floor_softening_edge_ok = (
            positive_predecision_package_edge
            or not fill_floor_softening_requires_positive_edge
        )
        fill_floor_softening_signed_authority_ok = (
            package_new_entry_signed_authority_ok
        )
        fill_floor_softening_fillability_ok = bool(
            package_execution_fill_probability is not None
            and package_execution_fill_probability >= fill_floor_softening_min_fill_probability
            and package_poi_scheduler_rankable_now
        )
        broker_cost_hard_reject_present = any(
            reason.startswith("broker_net_pretrade_cost_packet_refused")
            or reason == "pretrade_cost_above_selector_v4_ceiling"
            or "source_gap_cost_fallback" in reason
            for reason in hard_reject
        )
        for reason in hard_reject:
            is_soft_package_reject = (
                reason
                == "calibrated_admission_fill_probability_below_generalized_floor"
                and not broker_cost_hard_reject_present
                and fill_floor_softening_broker_cost_ok
                and fill_floor_softening_edge_ok
                and fill_floor_softening_signed_authority_ok
                and fill_floor_softening_fillability_ok
            )
            if (_sv_4718 := _selector_side(
        'sv4_4718_softened_rejects_append',
        bool(is_soft_package_reject),
        'softened_rejects_append',
        'other_side',
        'Condition: is_soft_package_reject. Which side of this condition is the decision?',
        true_text='This side stands: softened_rejects_append.',
        false_text='The other side stands: other_side.',
    )) == "true":
                softened_rejects.append(reason)
            elif _sv_4718 is not None and _sv_4718 == "false":
                retained_rejects.append(reason)
        if (_sv_4722 := _selector_side(
        'sv4_4722_ultimate_candidate_package_admission_softened_se',
        bool(softened_rejects),
        'ultimate_candidate_package_admission_softened_se',
        'other_side',
        'Condition: softened_rejects. Which side of this condition is the decision?',
        true_text='ultimate_candidate_package_admission_softened_se reduces this candidate.',
        false_text='other_side does not reduce this candidate.',
    )) == "true":
            hard_reject = retained_rejects
            reduce_reasons.append(
                "ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay"
            )
            if (_sv_4727 := _selector_side(
        'sv4_4727_ultimate_candidate_package_selector_fill_floor_s',
        bool(fill_floor_softening_broker_cost_ok),
        'ultimate_candidate_package_selector_fill_floor_s',
        'other_side',
        'Condition: fill_floor_softening_broker_cost_ok. Which side of this condition is the decision?',
        true_text='ultimate_candidate_package_selector_fill_floor_s reduces this candidate.',
        false_text='other_side does not reduce this candidate.',
    )) == "true":
                reduce_reasons.append(
                    "ultimate_candidate_package_selector_fill_floor_softening_broker_cost_passed"
                )
            if (_sv_4731 := _selector_side(
        'sv4_4731_ultimate_candidate_package_selector_fill_floor_s',
        bool(fill_floor_softening_edge_ok),
        'ultimate_candidate_package_selector_fill_floor_s',
        'other_side',
        'Condition: fill_floor_softening_edge_ok. Which side of this condition is the decision?',
        true_text='ultimate_candidate_package_selector_fill_floor_s reduces this candidate.',
        false_text='other_side does not reduce this candidate.',
    )) == "true":
                reduce_reasons.append(
                    "ultimate_candidate_package_selector_fill_floor_softening_positive_predecision_edge"
                )
            reduce_reasons.extend(
                f"ultimate_candidate_package_soft_admission:{reason}"
                for reason in softened_rejects
            )

    if (
        ultimate_package_soft_admission_override_allowed
        and _truthy(
            cfg.get("ultimate_candidate_package_strong_fill_floor_bypass_enabled")
        )
    ):
        min_bypass_ev = _float(
            cfg.get("ultimate_candidate_package_strong_fill_floor_bypass_min_expected_net_r")
        )
        min_bypass_probability = _float(
            cfg.get("ultimate_candidate_package_strong_fill_floor_bypass_min_probability")
        )
        min_bypass_fill_probability = _float(
            cfg.get("ultimate_candidate_package_strong_fill_floor_bypass_min_fill_probability")
        )
        min_bypass_source_completeness = _float(
            cfg.get(
                "ultimate_candidate_package_strong_fill_floor_bypass_min_source_completeness",
                cfg.get(
                    "ultimate_candidate_package_derived_executable_min_source_completeness",
                    cfg.get(
                        "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_source_completeness",
                        cfg.get("selector_v4_calibrated_min_source_completeness"),
                    ),
                ),
            )
        )
        min_bypass_ev = 0.70 if min_bypass_ev is None else min_bypass_ev
        min_bypass_probability = (
            0.70 if min_bypass_probability is None else min_bypass_probability
        )
        min_bypass_fill_probability = (
            0.20
            if min_bypass_fill_probability is None
            else min_bypass_fill_probability
        )
        min_bypass_source_completeness = (
            0.65
            if min_bypass_source_completeness is None
            else min_bypass_source_completeness
        )
        strong_fill_floor_bypass = (
            package_new_entry_signed_authority_ok
            and package_quality_expected_net_r is not None
            and package_quality_expected_net_r >= min_bypass_ev
            and package_quality_probability is not None
            and package_quality_probability >= min_bypass_probability
            and package_execution_fill_probability is not None
            and package_execution_fill_probability >= min_bypass_fill_probability
            and package_poi_scheduler_rankable_now
            and package_source_completeness is not None
            and package_source_completeness >= min_bypass_source_completeness
        )
        full_trade_fill_floor_bypass_allowed = _truthy(
            cfg.get("ultimate_candidate_package_strong_fill_floor_bypass_full_trade_allowed")
        )
        cost_refusal_softened = any(
            reason.startswith(
                "ultimate_candidate_package_soft_admission:"
                "broker_net_pretrade_cost_packet_refused"
            )
            or reason
            in {
                "ultimate_candidate_package_soft_admission:"
                "pretrade_cost_above_selector_v4_ceiling",
                "pretrade_cost_above_selector_v4_ceiling",
            }
            for reason in reduce_reasons
        )
        if strong_fill_floor_bypass and not cost_refusal_softened:
            fill_floor_reasons = {
                "calibrated_admission_fill_probability_below_generalized_floor",
                "ultimate_candidate_package_soft_admission:"
                "calibrated_admission_fill_probability_below_generalized_floor",
            }
            fill_floor_reason_present = any(
                reason in fill_floor_reasons for reason in reduce_reasons
            )
            if full_trade_fill_floor_bypass_allowed:
                retained_reduce_reasons = [
                    reason for reason in reduce_reasons if reason not in fill_floor_reasons
                ]
                if len(retained_reduce_reasons) != len(reduce_reasons):
                    reduce_reasons = [
                        reason
                        for reason in retained_reduce_reasons
                        if reason
                        not in {
                            "ultimate_candidate_package_admission_softened_selector_cost_or_fill_floor_in_replay",
                            "ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay",
                        }
                    ]
            elif fill_floor_reason_present:
                reduce_reasons.append(
                    "ultimate_candidate_package_fill_floor_bypass_reduce_risk_only"
                )

    broker_net_gradient_open_reduced_authority_pre_allowed = bool(
        broker_net_admission_ev is not None
        and broker_net_admission_ev < min_trade_ev
        and ultimate_package_soft_admission_override_allowed
        and _truthy(
            cfg.get(
                "ultimate_candidate_package_broker_net_gradient_open_reduced_risk_enabled",
                False,
            )
        )
        and broker_cost_passed_for_package_router
        and positive_predecision_package_edge
        and ultimate_package_quality_contract_valid
    )

    would_action = "no-trade"
    reason = "admission_label_unanswered"
    if (_sv_4852 := _selector_side(
        'sv4_4852_source_required',
        bool(source_required),
        'source_required',
        'other_side',
        'Condition: source_required. Which side of this condition is the decision?',
        true_text='The label on this side is source_required.',
        false_text='The label on the other side is other_side.',
    )) == "true":
        would_action = "source-required"
        reason = sorted(set(source_required))[0]
    elif _sv_4852 is not None and (_sv_4852 := _selector_side(
        'sv4_4855_reject',
        bool(hard_reject),
        'reject',
        'other_side',
        'Condition: hard_reject. Which side of this condition is the decision?',
        true_text='The label on this side is reject.',
        false_text='The label on the other side is other_side.',
    )) == "true":
        would_action = "reject"
        reason = _canonical_selector_reason(hard_reject)
    elif _sv_4852 is not None and (_sv_4852 := _selector_side(
        'sv4_4858_no_trade',
        bool(selected_action == "no-trade"),
        'no_trade',
        'other_side',
        'Condition: selected_action == "no-trade". Which side of this condition is the decision?',
        true_text='The label on this side is no_trade.',
        false_text='The label on the other side is other_side.',
    )) == "true":
        would_action = "no-trade"
        reason = "probability_debate_selected_no_trade"
    elif _sv_4852 is not None and (_sv_4852 := _selector_side(
        'sv4_4861_queue',
        bool(queue_reasons),
        'queue',
        'other_side',
        'Condition: queue_reasons. Which side of this condition is the decision?',
        true_text='The label on this side is queue.',
        false_text='The label on the other side is other_side.',
    )) == "true":
        would_action = "queue"
        reason = sorted(set(queue_reasons))[0]
    elif _sv_4852 is not None and (_sv_4852 := _selector_side(
        'sv4_4864_source_required',
        bool(broker_net_admission_ev is None),
        'source_required',
        'other_side',
        'Condition: broker_net_admission_ev is None. Which side of this condition is the decision?',
        true_text='The label on this side is source_required.',
        false_text='The label on the other side is other_side.',
    )) == "true":
        would_action = "source-required"
        reason = "broker_net_admission_ev_not_computable"
        source_required.append("broker_net_admission_ev")
    elif _sv_4852 is not None and (_sv_4852 := _selector_side(
        'sv4_4868_no_trade',
        bool(broker_net_admission_ev < min_no_trade_ev),
        'no_trade',
        'other_side',
        'Condition: broker_net_admission_ev < min_no_trade_ev. Which side of this condition is the decision?',
        true_text='The label on this side is no_trade.',
        false_text='The label on the other side is other_side.',
    )) == "true":
        would_action = "no-trade"
        reason = "broker_net_admission_ev_below_no_trade_floor"
    elif _sv_4852 is not None and (_sv_4852 := _selector_side(
        'sv4_4871_broker_net_admission_ev_below_full_trade_floor',
        bool(broker_net_admission_ev < min_trade_ev or reduce_reasons),
        'broker_net_admission_ev_below_full_trade_floor',
        'trade',
        'Condition: broker_net_admission_ev < min_trade_ev or reduce_reasons. Which side of this condition is the decision?',
        true_text='The label on this side is broker_net_admission_ev_below_full_trade_floor.',
        false_text='The label on the other side is trade.',
    )) == "true":
        open_reduced_risk_entry_reasons = set(
            SELECTOR_V4_OPEN_REDUCED_SELECTOR_REASONS
        )
        # Broker-net EV below the full-trade floor is reduce-risk by default.
        # It may only become open-reduced through the explicit broker-gradient
        # package authority checked below.
        open_reduced_risk_entry_reasons.discard(
            "broker_net_admission_ev_below_full_trade_floor"
        )
        if not positive_package_off_session_open_reduced_allowed:
            open_reduced_risk_entry_reasons.discard(
                "ultimate_candidate_package_positive_predecision_off_session_open_reduced_risk"
            )
        if broker_net_gradient_open_reduced_authority_pre_allowed:
            open_reduced_risk_entry_reasons.add(
                "broker_net_admission_ev_below_full_trade_floor"
            )
        reduce_reason_set = set(reduce_reasons)
        prioritized_open_reduced_reason = next(
            (
                candidate_reason
                for candidate_reason in (
                    "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk",
                    "admission_quality_dynamic_router_refusal_open_reduced_risk_configured",
                    "source_bound_router_refusal_open_reduced_materialized_for_replay",
                    "ultimate_candidate_package_positive_predecision_off_session_open_reduced_risk",
                    "admission_quality_off_configured_session_open_reduced_risk_configured",
                    off_session_reduce_risk_reason,
                    "ultimate_candidate_package_numeric_disagreement_open_reduced_risk",
                    "ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay",
                    "ultimate_candidate_package_admission_softened_selector_cost_or_fill_floor_in_replay",
                    "ultimate_candidate_package_fill_floor_bypass_reduce_risk_only",
                    "ultimate_candidate_package_soft_admission:calibrated_admission_fill_probability_below_generalized_floor",
                    "admission_quality_off_configured_session_entry_blocked",
                )
                if candidate_reason in reduce_reason_set
            ),
            None,
        )
        if (
            (_sv_4911 := _selector_side(
        'sv4_4911_assign_reason',
        bool(prioritized_open_reduced_reason
            and prioritized_open_reduced_reason in open_reduced_risk_entry_reasons),
        'assign_reason',
        'other_side',
        'Condition: prioritized_open_reduced_reason\n            and prioritized_open_reduced_reason in open_reduced_risk_entry_reasons. Which side of this condition is the decision?',
        true_text='The label on this side is assign_reason.',
        false_text='The label on the other side is other_side.',
    )) == "true"
        ):
            reason = prioritized_open_reduced_reason
        elif _sv_4911 is not None and (_sv_4911 := _selector_side(
        'sv4_4916_broker_net_admission_ev_below_full_trade_floor',
        bool(broker_net_admission_ev < min_trade_ev),
        'broker_net_admission_ev_below_full_trade_floor',
        'other_side',
        'Condition: broker_net_admission_ev < min_trade_ev. Which side of this condition is the decision?',
        true_text='The label on this side is broker_net_admission_ev_below_full_trade_floor.',
        false_text='The label on the other side is other_side.',
    )) == "true":
            reason = "broker_net_admission_ev_below_full_trade_floor"
        elif _sv_4911 is not None and _sv_4911 == "false":
            reason = prioritized_open_reduced_reason or sorted(reduce_reason_set)[0]
        would_action = (
            "open-reduced-risk"
            if reason in open_reduced_risk_entry_reasons
            else "reduce-risk"
        )
    elif _sv_4852 is not None and _sv_4852 == "false":
        would_action = "trade"
        reason = "broker_net_probability_confluence_lifecycle_admission_passed"

    risk_pct = broker_net["risk_pct"]
    risk_multiplier = 0.0
    if (_sv_4930 := _selector_side(
        'sv4_4930_assign_risk_multiplier',
        bool(would_action == "trade"),
        'assign_risk_multiplier',
        'other_side',
        'Condition: would_action == "trade". Which side of this condition is the decision?',
        true_text='This side stands: assign_risk_multiplier.',
        false_text='The other side stands: other_side.',
    )) == "true":
        risk_multiplier = 1.0
    elif _sv_4930 is not None and (_sv_4930 := _selector_side(
        'sv4_4932_assign_risk_multiplier',
        bool(would_action in {"reduce-risk", "open-reduced-risk"}),
        'assign_risk_multiplier',
        'other_side',
        'Condition: would_action in {"reduce-risk", "open-reduced-risk"}. Which side of this condition is the decision?',
        true_text='This side stands: assign_risk_multiplier.',
        false_text='The other side stands: other_side.',
    )) == "true":
        risk_multiplier = reduce_multiplier
    elif _sv_4930 is not None and _sv_4930 == "false":
        risk_multiplier = 0.0
    if (
        learned is not None
        and learned["sizing_enabled"]
        and learned["status"] == "scored"
        and would_action in RISK_BEARING_SELECTOR_V4_ACTIONS
    ):
        # Learned risk sizing replaces the binary 1.0/0.5 multiplier with a
        # threshold-gradient multiplier shrunk by segment reliability.
        learned_thresholds = _mapping(learned.get("thresholds"))
        t_trade = _float(learned_thresholds.get("t_trade_expected_net_r"))
        t_reduce = _float(learned_thresholds.get("t_reduce_expected_net_r"))
        learned_expected_net_r = _float(learned.get("expected_net_r"))
        if (
            (_sv_4948 := _selector_side(
        'sv4_4948_segment_shrinkage_weights',
        bool(t_trade is not None
            and t_reduce is not None
            and learned_expected_net_r is not None
            and t_trade > t_reduce),
        'segment_shrinkage_weights',
        'fallback_reason',
        'Condition: t_trade is not None\n            and t_reduce is not None\n            and learned_expected_net_r is not None\n            and t_trade > t_reduce. Which side of this condition is the decision?',
        true_text='This side stands: segment_shrinkage_weights.',
        false_text='The other side stands: fallback_reason.',
    )) == "true"
        ):
            shrinkage_weights = _mapping(learned.get("segment_shrinkage_weights"))
            fill_weight = _float(shrinkage_weights.get("fill"))
            outcome_weight = _float(shrinkage_weights.get("outcome"))
            segment_weight = min(
                1.0 if fill_weight is None else fill_weight,
                1.0 if outcome_weight is None else outcome_weight,
            )
            gradient = _clamp(
                (learned_expected_net_r - t_reduce) / (t_trade - t_reduce), 0.0, 1.0
            )
            risk_multiplier = _clamp(
                gradient * (0.5 + 0.5 * segment_weight), 0.0, 1.0
            )
            learned["applied_to_sizing"] = True
        elif _sv_4948 is not None and _sv_4948 == "false":
            learned["fallback_reason"] = learned.get("fallback_reason") or (
                "learned_edge_unavailable_static_floor_fallback:"
                "sizing_thresholds_invalid"
            )
    final_risk_pct = round(risk_pct * risk_multiplier, 12) if risk_pct is not None else None
    runtime_effect = bool(
        live_allowed
        and apply_value
        and would_action in RISK_BEARING_SELECTOR_V4_ACTIONS
        and final_risk_pct is not None
        and final_risk_pct > 0.0
    )
    source_bound_candidate_use_allowed_now = bool(
        would_action in RISK_BEARING_SELECTOR_V4_ACTIONS
        and final_risk_pct is not None
        and final_risk_pct > 0.0
    )
    replay_candidate_authority_available = bool(
        source_bound_candidate_use_allowed_now
        and (
            apply_value
            or (
                ultimate_package_replay_admission_enabled
                and (
                    ultimate_package_source_bound_allowed
                    or ultimate_package_source_bound_replay_authority_allowed
                )
            )
        )
    )
    replay_candidate_use_allowed_now = bool(
        replay_candidate_authority_available
    )
    status = (
        "selector_v4_runtime_effect_enabled_by_config"
        if runtime_effect
        else "selector_v4_no_runtime_effect_for_this_decision"
    )
    package_open_reduced_authority_family = None
    if would_action == "open-reduced-risk":
        if reason in {
            "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk",
            "source_bound_router_refusal_open_reduced_materialized_for_replay",
        }:
            package_open_reduced_authority_family = "router_refusal_softening"
        elif reason == "ultimate_candidate_package_positive_predecision_off_session_open_reduced_risk":
            package_open_reduced_authority_family = "off_session_softening"
        elif reason == "ultimate_candidate_package_numeric_disagreement_open_reduced_risk":
            package_open_reduced_authority_family = "numeric_disagreement_softening"
        elif reason in {
            "ultimate_candidate_package_admission_softened_selector_cost_or_fill_floor_in_replay",
            "ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay",
            "ultimate_candidate_package_soft_admission:calibrated_admission_fill_probability_below_generalized_floor",
        }:
            package_open_reduced_authority_family = "fill_floor_softening"
        elif reason == "ultimate_candidate_package_fill_floor_bypass_reduce_risk_only":
            package_open_reduced_authority_family = "fill_floor_bypass"
        elif (
            reason == "broker_net_admission_ev_below_full_trade_floor"
            and positive_predecision_package_edge
        ):
            package_open_reduced_authority_family = "broker_net_admission_gradient"
        elif reason in {
            "admission_quality_dynamic_router_refused_candidate_use",
            "admission_quality_dynamic_router_refusal_open_reduced_risk_configured",
            "admission_quality_off_configured_session_entry_blocked",
            "admission_quality_off_configured_session_open_reduced_risk_configured",
        }:
            package_open_reduced_authority_family = "legacy_admission_quality_softening"
    package_open_reduced_authority_allowed = bool(
        package_open_reduced_authority_family
        and (
            ultimate_package_soft_admission_override_allowed
            or (
                reason == "source_bound_router_refusal_open_reduced_materialized_for_replay"
                and source_bound_router_refusal_open_reduced_materialization_allowed
            )
        )
        and broker_cost_passed_for_package_router
        and source_bound_candidate_use_allowed_now
    )
    package_open_reduced_authority_current_config_allowed = True
    package_open_reduced_authority_config_block_reason = None
    if (
        package_open_reduced_authority_family == "router_refusal_softening"
        and not (
            _truthy(
                cfg.get(
                    "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk_allowed",
                    False,
                )
            )
            or (
                reason
                == "source_bound_router_refusal_open_reduced_materialized_for_replay"
                and source_bound_router_refusal_open_reduced_materialization_allowed
            )
        )
    ):
        package_open_reduced_authority_current_config_allowed = False
        package_open_reduced_authority_config_block_reason = (
            "router_refusal_open_reduced_risk_disabled_by_config"
        )
    elif (
        package_open_reduced_authority_family == "off_session_softening"
        and not positive_package_off_session_open_reduced_allowed
    ):
        package_open_reduced_authority_current_config_allowed = False
        package_open_reduced_authority_config_block_reason = (
            "off_session_open_reduced_risk_predecision_quality_floor_not_met"
        )
    elif (
        package_open_reduced_authority_family == "numeric_disagreement_softening"
        and not _truthy(
            cfg.get(
                "ultimate_candidate_package_numeric_disagreement_open_reduced_risk_enabled",
                True,
            )
        )
    ):
        package_open_reduced_authority_current_config_allowed = False
        package_open_reduced_authority_config_block_reason = (
            "numeric_disagreement_open_reduced_risk_disabled_by_config"
        )
    elif (
        package_open_reduced_authority_family
        in {"fill_floor_softening", "fill_floor_bypass"}
        and not _truthy(
            cfg.get("ultimate_candidate_package_soften_selector_fill_floor_enabled", False)
        )
    ):
        package_open_reduced_authority_current_config_allowed = False
        package_open_reduced_authority_config_block_reason = (
            "fill_floor_open_reduced_risk_disabled_by_config"
        )
    elif (
        package_open_reduced_authority_family == "broker_net_admission_gradient"
        and not _truthy(
            cfg.get(
                "ultimate_candidate_package_broker_net_gradient_open_reduced_risk_enabled",
                False,
            )
        )
    ):
        package_open_reduced_authority_current_config_allowed = False
        package_open_reduced_authority_config_block_reason = (
            "broker_net_gradient_open_reduced_risk_disabled_by_config"
        )
    elif (
        package_open_reduced_authority_family == "legacy_admission_quality_softening"
        and not _truthy(
            cfg.get(
                "ultimate_candidate_package_legacy_admission_quality_open_reduced_risk_allowed",
                False,
            )
        )
    ):
        package_open_reduced_authority_current_config_allowed = False
        package_open_reduced_authority_config_block_reason = (
            "legacy_admission_quality_open_reduced_risk_not_package_authority"
        )
    if (
        package_open_reduced_authority_family
        in {"fill_floor_softening", "fill_floor_bypass"}
        and package_open_reduced_authority_current_config_allowed
        and not package_new_entry_signed_authority_ok
    ):
        package_open_reduced_authority_current_config_allowed = False
        package_open_reduced_authority_config_block_reason = (
            package_new_entry_signed_authority.get("status")
            or "package_new_entry_authority_hash_missing"
        )
    package_open_reduced_authority_allowed = bool(
        package_open_reduced_authority_allowed
        and package_open_reduced_authority_current_config_allowed
    )
    package_reduce_risk_authority_family = None
    if would_action == "reduce-risk":
        if reason == "ultimate_candidate_package_dynamic_router_refusal_softened_reduce_risk":
            package_reduce_risk_authority_family = "router_refusal_softening"
        elif (
            reason == "numeric_confluence_structured_disagreement"
            and package_numeric_disagreement_reduce_risk_authority_allowed
        ):
            package_reduce_risk_authority_family = "numeric_disagreement_softening"
        elif reason in {
            "ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay",
            "ultimate_candidate_package_soft_admission:calibrated_admission_fill_probability_below_generalized_floor",
        }:
            package_reduce_risk_authority_family = "fill_floor_softening"
        elif reason == "ultimate_candidate_package_fill_floor_bypass_reduce_risk_only":
            package_reduce_risk_authority_family = "fill_floor_bypass"
        elif (
            reason == "broker_net_admission_ev_below_full_trade_floor"
            and positive_predecision_package_edge
        ):
            package_reduce_risk_authority_family = "broker_net_admission_gradient"
    package_reduce_risk_authority_allowed = bool(
        package_reduce_risk_authority_family
        and (
            ultimate_package_soft_admission_override_allowed
            or (
                package_reduce_risk_authority_family
                == "numeric_disagreement_softening"
                and ultimate_package_source_bound_replay_authority_allowed
            )
        )
        and broker_cost_passed_for_package_router
        and positive_predecision_package_edge
        and source_bound_candidate_use_allowed_now
    )
    package_reduce_risk_authority_current_config_allowed = True
    package_reduce_risk_authority_config_block_reason = None
    if (
        package_reduce_risk_authority_family == "router_refusal_softening"
        and not _truthy(
            cfg.get(
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_router_refusal_package_new_entry_authority_enabled",
                cfg.get(
                    "selector_reduce_risk_router_refusal_package_new_entry_authority_enabled",
                    False,
                ),
            )
        )
    ):
        package_reduce_risk_authority_current_config_allowed = False
        package_reduce_risk_authority_config_block_reason = (
            "router_refusal_reduce_risk_new_entry_authority_disabled_by_config"
        )
    elif (
        package_reduce_risk_authority_family == "fill_floor_softening"
        and not _truthy(
            cfg.get("ultimate_candidate_package_soften_selector_fill_floor_enabled", False)
        )
    ):
        package_reduce_risk_authority_current_config_allowed = False
        package_reduce_risk_authority_config_block_reason = (
            "fill_floor_reduce_risk_softening_disabled_by_config"
        )
    elif (
        package_reduce_risk_authority_family == "fill_floor_bypass"
        and not _truthy(
            cfg.get("ultimate_candidate_package_strong_fill_floor_bypass_enabled", False)
        )
    ):
        package_reduce_risk_authority_current_config_allowed = False
        package_reduce_risk_authority_config_block_reason = (
            "fill_floor_reduce_risk_bypass_disabled_by_config"
        )
    elif (
        (
            package_reduce_risk_authority_family == "numeric_disagreement_softening"
            or reason == "numeric_confluence_structured_disagreement"
            or reason == "ultimate_candidate_package_numeric_disagreement_open_reduced_risk"
        )
        and not _truthy(
            cfg.get(
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_numeric_disagreement_package_new_entry_authority_enabled",
                cfg.get(
                    "ultimate_candidate_package_numeric_disagreement_open_reduced_risk_enabled",
                    True,
                ),
            )
        )
    ):
        package_reduce_risk_authority_current_config_allowed = False
        package_reduce_risk_authority_config_block_reason = (
            "numeric_disagreement_reduce_risk_authority_disabled_by_config"
        )
    if (
        package_reduce_risk_authority_family
        in {"fill_floor_softening", "fill_floor_bypass"}
        and package_reduce_risk_authority_current_config_allowed
        and not package_new_entry_signed_authority_ok
    ):
        package_reduce_risk_authority_current_config_allowed = False
        package_reduce_risk_authority_config_block_reason = (
            package_new_entry_signed_authority.get("status")
            or "package_new_entry_authority_hash_missing"
        )
    package_reduce_risk_authority_allowed = bool(
        package_reduce_risk_authority_allowed
        and package_reduce_risk_authority_current_config_allowed
    )
    component_scores: dict[str, Any] = {
        "side": side,
        "candidate_action": candidate_action,
        "numeric_confluence": confluence,
        "probability_debate": probability,
        "broker_net_selected_cell": broker_net,
        "cost": cost,
        "lifecycle": lifecycle,
        "ultimate_candidate_package_new_entry_signed_authority": dict(
            package_new_entry_signed_authority
        ),
        "broker_net_admission_ev_r": (
            round(broker_net_admission_ev, 12)
            if broker_net_admission_ev is not None
            else None
        ),
        "broker_net_admission_ev_components": [
            {"source": source, "net_ev_r": round(value, 12)}
            for source, value in ev_candidates
        ],
        "admission_quality": admission_quality,
        "ultimate_candidate_package_open_reduced_risk_authority": {
            "applies": would_action == "open-reduced-risk",
            "allowed": package_open_reduced_authority_allowed,
            "authority_family": package_open_reduced_authority_family,
            "current_config_allowed": (
                package_open_reduced_authority_current_config_allowed
            ),
            "config_block_reason": package_open_reduced_authority_config_block_reason,
            "selector_reason": reason,
            "package_new_entry_signed_authority": dict(
                package_new_entry_signed_authority
            ),
            "ultimate_package_soft_admission_override_allowed": (
                ultimate_package_soft_admission_override_allowed
            ),
            "ultimate_package_source_bound_replay_authority_allowed": (
                ultimate_package_source_bound_replay_authority_allowed
            ),
            "source_bound_router_refusal_authority_allowed": (
                source_bound_router_refusal_authority_allowed
            ),
            "ultimate_package_replay_admission_enabled": (
                ultimate_package_replay_admission_enabled
            ),
            "ultimate_package_apply_to_execution": ultimate_package_apply,
            "broker_cost_passed_for_package_router": broker_cost_passed_for_package_router,
            "positive_predecision_package_edge": positive_predecision_package_edge,
            "source_bound_candidate_use_allowed_now": (
                source_bound_candidate_use_allowed_now
            ),
            "package_source_completeness": (
                round(package_source_completeness, 12)
                if package_source_completeness is not None
                else None
            ),
            "derived_executable_min_source_completeness": (
                ultimate_package_derived_executable_min_source_completeness
            ),
            "derived_executable_quality_authority": (
                ultimate_package_derived_executable_quality_authority
            ),
            "causal_poi_lifecycle_required": package_poi_lifecycle_required,
            "poi_scheduler_rankable_now": package_poi_scheduler_rankable_now,
            "causal_poi_lifecycle_hash_sha256": (
                package_poi_lifecycle.get("lifecycle_hash_sha256")
                if package_poi_lifecycle
                else None
            ),
            "causal_poi_lifecycle_failures": list(
                package_poi_lifecycle_failures
            ),
            "fill_floor_softening_min_fill_probability": (
                fill_floor_softening_min_fill_probability
                if "fill_floor_softening_min_fill_probability" in locals()
                else None
            ),
            "fill_floor_softening_fillability_ok": (
                fill_floor_softening_fillability_ok
                if "fill_floor_softening_fillability_ok" in locals()
                else None
            ),
            "fill_floor_softening_signed_authority_ok": (
                fill_floor_softening_signed_authority_ok
                if "fill_floor_softening_signed_authority_ok" in locals()
                else None
            ),
            "reduced_risk_reasons": sorted(set(reduce_reasons)),
            "source_boundary": (
                "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
            ),
            "quality_contract": dict(ultimate_package_quality_contract),
            "broker_net_gradient_open_reduced_pre_allowed": (
                broker_net_gradient_open_reduced_authority_pre_allowed
            ),
        },
        "ultimate_candidate_package_reduce_risk_authority": {
            "applies": would_action == "reduce-risk",
            "allowed": package_reduce_risk_authority_allowed,
            "authority_family": package_reduce_risk_authority_family,
            "current_config_allowed": (
                package_reduce_risk_authority_current_config_allowed
            ),
            "config_block_reason": package_reduce_risk_authority_config_block_reason,
            "selector_reason": reason,
            "package_new_entry_signed_authority": dict(
                package_new_entry_signed_authority
            ),
            "ultimate_package_soft_admission_override_allowed": (
                ultimate_package_soft_admission_override_allowed
            ),
            "ultimate_package_source_bound_replay_authority_allowed": (
                ultimate_package_source_bound_replay_authority_allowed
            ),
            "ultimate_package_replay_admission_enabled": (
                ultimate_package_replay_admission_enabled
            ),
            "ultimate_package_apply_to_execution": ultimate_package_apply,
            "broker_cost_passed_for_package_router": broker_cost_passed_for_package_router,
            "positive_predecision_package_edge": positive_predecision_package_edge,
            "source_bound_candidate_use_allowed_now": (
                source_bound_candidate_use_allowed_now
            ),
            "package_source_completeness": (
                round(package_source_completeness, 12)
                if package_source_completeness is not None
                else None
            ),
            "derived_executable_min_source_completeness": (
                ultimate_package_derived_executable_min_source_completeness
            ),
            "derived_executable_quality_authority": (
                ultimate_package_derived_executable_quality_authority
            ),
            "reduced_risk_reasons": sorted(set(reduce_reasons)),
            "numeric_disagreement_reduce_risk_authority": {
                "allowed": package_numeric_disagreement_reduce_risk_authority_allowed,
                "quality_allowed": numeric_reduce_risk_authority_quality_allowed,
                "explicit_config_enabled": _truthy(
                    cfg.get(
                        "scheduler_v4_best_trade_allocator_selector_reduce_risk_numeric_disagreement_package_new_entry_authority_enabled",
                        False,
                    )
                ),
                "replay_only_no_live_runtime_effect": not live_allowed,
                "min_expected_net_r": numeric_reduce_risk_authority_min_expected_net_r,
                "min_probability": numeric_reduce_risk_authority_min_probability,
                "min_fill_probability": numeric_reduce_risk_authority_min_fill_probability,
                "min_source_completeness": numeric_reduce_risk_authority_min_source_completeness,
                "expected_net_r": (
                    round(package_quality_expected_net_r, 12)
                    if package_quality_expected_net_r is not None
                    else None
                ),
                "probability": (
                    round(package_quality_probability, 12)
                    if package_quality_probability is not None
                    else None
                ),
                "fill_probability": (
                    round(package_execution_fill_probability, 12)
                    if package_execution_fill_probability is not None
                    else None
                ),
                "entry_quality_fill_probability": (
                    round(package_quality_fill_probability, 12)
                    if package_quality_fill_probability is not None
                    else None
                ),
                "source_completeness": (
                    round(package_source_completeness, 12)
                    if package_source_completeness is not None
                    else None
                ),
                "selected_policy_expected_net_calibration_required": (
                    numeric_expected_net_policy_calibration_required
                ),
                "selected_policy_expected_net_calibration_status": (
                    selected_policy_expected_net_calibration_status or None
                ),
                "selected_policy_expected_net_calibrated": (
                    selected_policy_expected_net_calibrated
                ),
                "selected_policy_expected_net_calibration_source_boundary": (
                    selected_policy_expected_net_calibration_source_boundary or None
                ),
                "selected_policy_expected_net_calibration_allowed": (
                    numeric_expected_net_policy_calibration_allowed
                ),
                "source_boundary": (
                    "predecision_package_reduce_risk_numeric_authority_no_outcome_fields"
                ),
            },
            "source_boundary": (
                "predecision_package_reduce_risk_new_order_authority_no_outcome_fields"
            ),
            "quality_contract": dict(ultimate_package_quality_contract),
        },
        "ultimate_candidate_package_quality_contract": dict(
            ultimate_package_quality_contract
        ),
        "ultimate_candidate_package_replay_side_authority": {
            "policy_applies": ultimate_package_side_policy_applies,
            "side": side or None,
            "allowed": ultimate_package_replay_side_allowed,
            "allowed_sides": list(ultimate_package_replay_allowed_sides),
            "matched_sleeve_count": ultimate_package_match_count,
            "ultimate_package_replay_admission_enabled": (
                ultimate_package_replay_admission_enabled
            ),
            "ultimate_package_apply_to_execution": ultimate_package_apply,
            "source_boundary": (
                "predecision_package_side_authority_no_outcome_fields"
            ),
        },
        "ultimate_candidate_package_router_refusal_release": {
            "router_refusal_was_present": router_refusal_was_present,
            "softening_allowed": router_refusal_softening_allowed,
            "source_bound_open_reduced_materialization_allowed": (
                source_bound_router_refusal_open_reduced_materialization_allowed
            ),
            "source_bound_router_refusal_authority_allowed": (
                source_bound_router_refusal_authority_allowed
            ),
            "ultimate_package_source_bound_replay_authority_allowed": (
                ultimate_package_source_bound_replay_authority_allowed
            ),
            "source_bound_materialization_quality_allowed": (
                source_bound_router_refusal_materialization_quality_allowed
            ),
            "origin_family": router_refusal_origin_family or None,
            "origin_family_candidates": list(router_refusal_origin_family_candidates),
            "origin_family_raw_candidates": list(
                router_refusal_raw_origin_family_candidates
            ),
            "package_sleeve_origin_families": list(
                _package_sleeve_origin_families(event)
            ),
            "allowed_origin_families": list(
                router_refusal_softening_allowed_origin_families
            ),
            "origin_family_allowed": router_refusal_origin_family_allowed,
            "source_bound_package_role_materialization_allowed": (
                source_bound_router_refusal_package_role_materialization_allowed
            ),
            "role_disposition": ultimate_package_role_disposition or None,
            "role_disposition_executable": (
                ultimate_package_role_disposition
                not in PACKAGE_NON_EXECUTABLE_ROLE_DISPOSITIONS
            ),
            "role_disposition_reduced_risk": (
                ultimate_package_role_disposition
                in PACKAGE_REDUCED_RISK_ROLE_DISPOSITIONS
            ),
            "quality_allowed": router_refusal_quality_allowed,
            "min_expected_net_r": router_refusal_min_expected_net_r,
            "min_probability": router_refusal_min_probability,
            "min_fill_probability": router_refusal_min_fill_probability,
            "min_source_completeness": router_refusal_min_source_completeness,
            "source_bound_materialization_min_expected_net_r": (
                source_bound_router_refusal_materialization_min_expected_net_r
            ),
            "source_bound_materialization_min_probability": (
                source_bound_router_refusal_materialization_min_probability
            ),
            "source_bound_materialization_min_fill_probability": (
                source_bound_router_refusal_materialization_min_fill_probability
            ),
            "source_bound_materialization_min_source_completeness": (
                source_bound_router_refusal_materialization_min_source_completeness
            ),
            "expected_net_r": (
                round(package_quality_expected_net_r, 12)
                if package_quality_expected_net_r is not None
                else None
            ),
            "probability": (
                round(package_quality_probability, 12)
                if package_quality_probability is not None
                else None
            ),
            "fill_probability": (
                round(package_execution_fill_probability, 12)
                if package_execution_fill_probability is not None
                else None
            ),
            "entry_quality_fill_probability": (
                round(package_quality_fill_probability, 12)
                if package_quality_fill_probability is not None
                else None
            ),
            "execution_fill_probability": (
                round(package_router_refusal_execution_fill_probability, 12)
                if package_router_refusal_execution_fill_probability is not None
                else None
            ),
            "source_bound_materialization_fill_probability": (
                round(source_bound_router_refusal_materialization_fill_probability, 12)
                if source_bound_router_refusal_materialization_fill_probability is not None
                else None
            ),
            "source_completeness": (
                round(package_source_completeness, 12)
                if package_source_completeness is not None
                else None
            ),
            "positive_predecision_package_edge": positive_predecision_package_edge,
            "broker_cost_passed_for_package_router": broker_cost_passed_for_package_router,
            "full_trade_release_allowed": (
                positive_package_router_refusal_full_trade_release_allowed
            ),
            "full_trade_release_requested": (
                positive_package_router_refusal_full_trade_release_requested
            ),
            "full_trade_release_block_reason": (
                "router_refusal_full_trade_release_quality_or_authority_blocked"
                if (
                    positive_package_router_refusal_full_trade_release_requested
                    and not positive_package_router_refusal_full_trade_release_allowed
                )
                else None
            ),
            "full_trade_release_reason": (
                "positive_predecision_router_refusal_full_trade_released_by_config_and_quality"
                if positive_package_router_refusal_full_trade_release_allowed
                else None
            ),
            "open_reduced_risk_allowed": (
                positive_package_router_refusal_open_reduced_allowed
            ),
            "source_boundary": (
                "predecision_package_edge_cost_and_router_status_no_outcome_fields"
            ),
        },
        "ultimate_candidate_package_numeric_disagreement_open_reduced_risk": {
            "allowed": package_numeric_disagreement_open_reduced_risk_allowed,
            "quality_allowed": numeric_disagreement_quality_allowed,
            "min_expected_net_r": numeric_disagreement_min_expected_net_r,
            "min_probability": numeric_disagreement_min_probability,
            "min_fill_probability": numeric_disagreement_min_fill_probability,
            "min_source_completeness": numeric_disagreement_min_source_completeness,
            "broker_cost_passed_for_package_router": broker_cost_passed_for_package_router,
            "positive_predecision_package_edge": positive_predecision_package_edge,
            "selected_policy_expected_net_calibration_required": (
                numeric_expected_net_policy_calibration_required
            ),
            "selected_policy_expected_net_calibration_status": (
                selected_policy_expected_net_calibration_status or None
            ),
            "selected_policy_expected_net_calibrated": (
                selected_policy_expected_net_calibrated
            ),
            "selected_policy_expected_net_calibration_source_boundary": (
                selected_policy_expected_net_calibration_source_boundary or None
            ),
            "selected_policy_expected_net_calibration_allowed": (
                numeric_expected_net_policy_calibration_allowed
            ),
            "source_completeness": (
                round(package_source_completeness, 12)
                if package_source_completeness is not None
                else None
            ),
            "expected_net_r": (
                round(package_quality_expected_net_r, 12)
                if package_quality_expected_net_r is not None
                else None
            ),
            "probability": (
                round(package_quality_probability, 12)
                if package_quality_probability is not None
                else None
            ),
            "fill_probability": (
                round(package_execution_fill_probability, 12)
                if package_execution_fill_probability is not None
                else None
            ),
            "entry_quality_fill_probability": (
                round(package_quality_fill_probability, 12)
                if package_quality_fill_probability is not None
                else None
            ),
            "source_boundary": (
                "predecision_package_fill_floor_authority_without_outcome_fields"
            ),
        },
        "ultimate_candidate_package_numeric_disagreement_reduce_risk_authority": {
            "allowed": package_numeric_disagreement_reduce_risk_authority_allowed,
            "quality_allowed": numeric_reduce_risk_authority_quality_allowed,
            "explicit_config_enabled": _truthy(
                cfg.get(
                    "scheduler_v4_best_trade_allocator_selector_reduce_risk_numeric_disagreement_package_new_entry_authority_enabled",
                    False,
                )
            ),
            "package_fill_floor_authority_enabled": _truthy(
                cfg.get(
                    "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_authority_enabled",
                    False,
                )
            ),
            "replay_only_no_live_runtime_effect": not live_allowed,
            "selected_policy_expected_net_calibration_required": (
                numeric_expected_net_policy_calibration_required
            ),
            "selected_policy_expected_net_calibration_status": (
                selected_policy_expected_net_calibration_status or None
            ),
            "selected_policy_expected_net_calibrated": (
                selected_policy_expected_net_calibrated
            ),
            "selected_policy_expected_net_calibration_source_boundary": (
                selected_policy_expected_net_calibration_source_boundary or None
            ),
            "selected_policy_expected_net_calibration_allowed": (
                numeric_expected_net_policy_calibration_allowed
            ),
            "min_expected_net_r": numeric_reduce_risk_authority_min_expected_net_r,
            "min_probability": numeric_reduce_risk_authority_min_probability,
            "min_fill_probability": numeric_reduce_risk_authority_min_fill_probability,
            "min_source_completeness": numeric_reduce_risk_authority_min_source_completeness,
            "expected_net_r": (
                round(package_quality_expected_net_r, 12)
                if package_quality_expected_net_r is not None
                else None
            ),
            "probability": (
                round(package_quality_probability, 12)
                if package_quality_probability is not None
                else None
            ),
            "fill_probability": (
                round(package_execution_fill_probability, 12)
                if package_execution_fill_probability is not None
                else None
            ),
            "entry_quality_fill_probability": (
                round(package_quality_fill_probability, 12)
                if package_quality_fill_probability is not None
                else None
            ),
            "source_completeness": (
                round(package_source_completeness, 12)
                if package_source_completeness is not None
                else None
            ),
            "broker_cost_passed_for_package_router": broker_cost_passed_for_package_router,
            "positive_predecision_package_edge": positive_predecision_package_edge,
            "source_boundary": (
                "predecision_package_reduce_risk_numeric_authority_no_outcome_fields"
            ),
        },
    }
    if learned is not None:
        component_scores["learned_edge"] = learned
    if ultimate_package is not None:
        component_scores["ultimate_candidate_package"] = ultimate_package
    return SelectorV4AdmissionDecision(
        schema_version="selector_v4_broker_net_admission_v1",
        component="selector_v4",
        enabled=True,
        apply_to_execution=bool(apply_value),
        live_activation_allowed_by_config=live_allowed,
        action=would_action,
        would_action=would_action,
        decision_status=status,
        reason=reason,
        runtime_effect_now=runtime_effect,
        candidate_use_allowed_now=runtime_effect,
        source_bound_candidate_use_allowed_now=source_bound_candidate_use_allowed_now,
        replay_candidate_use_allowed_now=replay_candidate_use_allowed_now,
        risk_multiplier=round(risk_multiplier, 12),
        final_risk_pct=final_risk_pct,
        selector_action=would_action,
        selector_reason=reason,
        ignored_forbidden_fields=forbidden,
        source_required_fields=tuple(sorted(set(source_required))),
        hard_reject_reasons=tuple(sorted(set(hard_reject))),
        reduced_risk_reasons=tuple(sorted(set(reduce_reasons))),
        queue_reasons=tuple(sorted(set(queue_reasons))),
        semantic_owner_handoffs=semantic_handoffs,
        component_scores=component_scores,
        rejected_alternatives=tuple(
            str(item) for item in thesis.get("rejected_alternatives", []) or []
        ),
    )


__all__ = [
    "FORBIDDEN_SELECTOR_V4_RUNTIME_FIELDS",
    "BLOCKING_SELECTOR_V4_ACTIONS",
    "RISK_BEARING_SELECTOR_V4_ACTIONS",
    "SELECTOR_V4_ACTIONS",
    "SelectorV4AdmissionDecision",
    "evaluate_selector_v4_admission",
    "ignored_forbidden_runtime_fields",
    "selector_v4_action_blocks_execution",
    "selector_v4_action_is_risk_bearing",
]

SELECTOR_CHOICE_SPOTS = [{'spot': 'sv4_155_selector_v4_reason_missing', 'line': 155, 'func': '_canonical_selector_reason', 'question': 'Condition: not unique. Which side of this condition is the decision?', 'true_side': 'selector_v4_reason_missing', 'false_side': 'other_side', 'effects': ['label']}, {'spot': 'sv4_160_label', 'line': 160, 'func': 'priority', 'question': 'Condition: "pretrade_cost" in normalized\n            or "broker_cost" in normalized\n            or "cost_packet_refused" in normalized\n            or "negative_after_cost" in normalized\n            or "cost_above" in normalized. Which side of this condition is the decision?', 'true_side': 'label', 'false_side': 'other_side', 'effects': ['label']}, {'spot': 'sv4_168_label', 'line': 168, 'func': 'priority', 'question': 'Condition: "broker_net_admission_ev_negative" in normalized. Which side of this condition is the decision?', 'true_side': 'label', 'false_side': 'other_side', 'effects': ['label']}, {'spot': 'sv4_170_label', 'line': 170, 'func': 'priority', 'question': 'Condition: "source_required" in normalized. Which side of this condition is the decision?', 'true_side': 'label', 'false_side': 'other_side', 'effects': ['label']}, {'spot': 'sv4_172_label', 'line': 172, 'func': 'priority', 'question': 'Condition: "dynamic_router_refused" in normalized. Which side of this condition is the decision?', 'true_side': 'label', 'false_side': 'other_side', 'effects': ['label']}, {'spot': 'sv4_174_label', 'line': 174, 'func': 'priority', 'question': 'Condition: "off_configured_session" in normalized. Which side of this condition is the decision?', 'true_side': 'label', 'false_side': 'other_side', 'effects': ['label']}, {'spot': 'sv4_903_package_new_entry_authority_required_not_true', 'line': 903, 'func': '_package_new_entry_signed_authority_detail', 'question': 'Condition: not declared_required. Which side of this condition is the decision?', 'true_side': 'package_new_entry_authority_required_not_true', 'false_side': 'other_side', 'effects': ['failures.append']}, {'spot': 'sv4_905_package_new_entry_authority_valid_not_true', 'line': 905, 'func': '_package_new_entry_signed_authority_detail', 'question': 'Condition: not declared_valid. Which side of this condition is the decision?', 'true_side': 'package_new_entry_authority_valid_not_true', 'false_side': 'other_side', 'effects': ['failures.append']}, {'spot': 'sv4_907_package_new_entry_authority_status_invalid', 'line': 907, 'func': '_package_new_entry_signed_authority_detail', 'question': 'Condition: declared_status != "valid_signed_predecision_new_entry_authority". Which side of this condition is the decision?', 'true_side': 'package_new_entry_authority_status_invalid', 'false_side': 'other_side', 'effects': ['failures.append']}, {'spot': 'sv4_909_package_new_entry_authority_declared_failures_pr', 'line': 909, 'func': '_package_new_entry_signed_authority_detail', 'question': 'Condition: declared_failures. Which side of this condition is the decision?', 'true_side': 'package_new_entry_authority_declared_failures_pr', 'false_side': 'other_side', 'effects': ['failures.append']}, {'spot': 'sv4_919_package_new_entry_authority_payload_contract_inv', 'line': 919, 'func': '_package_new_entry_signed_authority_detail', 'question': 'Condition: authority_surface.get("package_new_entry_authority_payload_contract")\n            != PACKAGE_NEW_ENTRY_AUTHORITY_IMMUTABLE_PAYLOAD_CONTRACT\n            or signed_payload.get("payload_contract")\n            != PACKAGE_NEW. Which side of this condition is the decision?', 'true_side': 'package_new_entry_authority_payload_contract_inv', 'false_side': 'other_side', 'effects': ['failures.append']}, {'spot': 'sv4_926_package_new_entry_authority_payload_schema_inval', 'line': 926, 'func': '_package_new_entry_signed_authority_detail', 'question': 'Condition: signed_payload.get("payload_schema")\n            != PACKAGE_NEW_ENTRY_AUTHORITY_PAYLOAD_SCHEMA. Which side of this condition is the decision?', 'true_side': 'package_new_entry_authority_payload_schema_inval', 'false_side': 'other_side', 'effects': ['failures.append']}, {'spot': 'sv4_931_package_new_entry_authority_payload_hash_mismatc', 'line': 931, 'func': '_package_new_entry_signed_authority_detail', 'question': 'Condition: authority_hash != payload_hash or expected_hash != payload_hash. Which side of this condition is the decision?', 'true_side': 'package_new_entry_authority_payload_hash_mismatc', 'false_side': 'other_side', 'effects': ['failures.append']}, {'spot': 'sv4_934_package_new_entry_authority_payload_scope_invali', 'line': 934, 'func': '_package_new_entry_signed_authority_detail', 'question': 'Condition: not payload_action\n            or signed_payload.get("scope")\n            != package_new_entry_authority_scope_for_action_intent(payload_action). Which side of this condition is the decision?', 'true_side': 'package_new_entry_authority_payload_scope_invali', 'false_side': 'other_side', 'effects': ['failures.append']}, {'spot': 'sv4_941_package_new_entry_authority_payload_boundary_inv', 'line': 941, 'func': '_package_new_entry_signed_authority_detail', 'question': 'Condition: not _predecision_no_outcome_boundary(payload_boundary)\n            or signed_payload.get("uses_outcome_fields") is not False\n            or signed_payload.get("authority_applies") is not True\n            or signed_payloa. Which side of this condition is the decision?', 'true_side': 'package_new_entry_authority_payload_boundary_inv', 'false_side': 'other_side', 'effects': ['failures.append']}, {'spot': 'sv4_961_package_new_entry_authority_payload_projection_m', 'line': 961, 'func': '_package_new_entry_signed_authority_detail', 'question': 'Condition: _text(signed_payload.get(payload_key)) != projected_value. Which side of this condition is the decision?', 'true_side': 'package_new_entry_authority_payload_projection_m', 'false_side': 'other_side', 'effects': ['failures.append']}, {'spot': 'sv4_965_package_new_entry_authority_hash_missing', 'line': 965, 'func': '_package_new_entry_signed_authority_detail', 'question': 'Condition: not authority_hash. Which side of this condition is the decision?', 'true_side': 'package_new_entry_authority_hash_missing', 'false_side': 'other_side', 'effects': ['failures.append']}, {'spot': 'sv4_967_package_new_entry_authority_hash_not_sha256_hex', 'line': 967, 'func': '_package_new_entry_signed_authority_detail', 'question': 'Condition: not _sha256_hex(authority_hash). Which side of this condition is the decision?', 'true_side': 'package_new_entry_authority_hash_not_sha256_hex', 'false_side': 'other_side', 'effects': ['failures.append']}, {'spot': 'sv4_969_expected_package_new_entry_authority_hash_missin', 'line': 969, 'func': '_package_new_entry_signed_authority_detail', 'question': 'Condition: not expected_hash. Which side of this condition is the decision?', 'true_side': 'expected_package_new_entry_authority_hash_missin', 'false_side': 'other_side', 'effects': ['failures.append']}, {'spot': 'sv4_971_expected_package_new_entry_authority_hash_not_sh', 'line': 971, 'func': '_package_new_entry_signed_authority_detail', 'question': 'Condition: not _sha256_hex(expected_hash). Which side of this condition is the decision?', 'true_side': 'expected_package_new_entry_authority_hash_not_sh', 'false_side': 'other_side', 'effects': ['failures.append']}, {'spot': 'sv4_973_package_new_entry_authority_hash_mismatch', 'line': 973, 'func': '_package_new_entry_signed_authority_detail', 'question': 'Condition: authority_hash and expected_hash and authority_hash != expected_hash. Which side of this condition is the decision?', 'true_side': 'package_new_entry_authority_hash_mismatch', 'false_side': 'other_side', 'effects': ['failures.append']}, {'spot': 'sv4_975_package_new_entry_authority_candidate_id_missing', 'line': 975, 'func': '_package_new_entry_signed_authority_detail', 'question': 'Condition: not signed_candidate_id. Which side of this condition is the decision?', 'true_side': 'package_new_entry_authority_candidate_id_missing', 'false_side': 'other_side', 'effects': ['failures.append']}, {'spot': 'sv4_977_current_candidate_id_missing', 'line': 977, 'func': '_package_new_entry_signed_authority_detail', 'question': 'Condition: not current_candidate_id. Which side of this condition is the decision?', 'true_side': 'current_candidate_id_missing', 'false_side': 'other_side', 'effects': ['failures.append']}, {'spot': 'sv4_979_package_new_entry_authority_candidate_id_mismatc', 'line': 979, 'func': '_package_new_entry_signed_authority_detail', 'question': 'Condition: signed_candidate_id != current_candidate_id. Which side of this condition is the decision?', 'true_side': 'package_new_entry_authority_candidate_id_mismatc', 'false_side': 'other_side', 'effects': ['failures.append']}, {'spot': 'sv4_981_package_new_entry_authority_decision_time_utc_mi', 'line': 981, 'func': '_package_new_entry_signed_authority_detail', 'question': 'Condition: not signed_decision_time. Which side of this condition is the decision?', 'true_side': 'package_new_entry_authority_decision_time_utc_mi', 'false_side': 'other_side', 'effects': ['failures.append']}, {'spot': 'sv4_983_current_decision_time_utc_missing', 'line': 983, 'func': '_package_new_entry_signed_authority_detail', 'question': 'Condition: not current_decision_time. Which side of this condition is the decision?', 'true_side': 'current_decision_time_utc_missing', 'false_side': 'other_side', 'effects': ['failures.append']}, {'spot': 'sv4_985_package_new_entry_authority_decision_time_utc_mi', 'line': 985, 'func': '_package_new_entry_signed_authority_detail', 'question': 'Condition: signed_decision_time != current_decision_time. Which side of this condition is the decision?', 'true_side': 'package_new_entry_authority_decision_time_utc_mi', 'false_side': 'other_side', 'effects': ['failures.append']}, {'spot': 'sv4_987_package_new_entry_authority_canonical_replay_can', 'line': 987, 'func': '_package_new_entry_signed_authority_detail', 'question': 'Condition: not signed_canonical_instance_key. Which side of this condition is the decision?', 'true_side': 'package_new_entry_authority_canonical_replay_can', 'false_side': 'other_side', 'effects': ['failures.append']}, {'spot': 'sv4_991_package_new_entry_authority_canonical_replay_can', 'line': 991, 'func': '_package_new_entry_signed_authority_detail', 'question': 'Condition: signed_canonical_instance_key != current_canonical_instance_key. Which side of this condition is the decision?', 'true_side': 'package_new_entry_authority_canonical_replay_can', 'false_side': 'other_side', 'effects': ['failures.append']}, {'spot': 'sv4_995_package_new_entry_authority_source_bound_replay_', 'line': 995, 'func': '_package_new_entry_signed_authority_detail', 'question': 'Condition: not signed_source_bound_instance_key. Which side of this condition is the decision?', 'true_side': 'package_new_entry_authority_source_bound_replay_', 'false_side': 'other_side', 'effects': ['failures.append']}, {'spot': 'sv4_999_package_new_entry_authority_source_bound_replay_', 'line': 999, 'func': '_package_new_entry_signed_authority_detail', 'question': 'Condition: signed_source_bound_instance_key != current_source_bound_instance_key. Which side of this condition is the decision?', 'true_side': 'package_new_entry_authority_source_bound_replay_', 'false_side': 'other_side', 'effects': ['failures.append']}, {'spot': 'sv4_1003_package_new_entry_authority_source_boundary_miss', 'line': 1003, 'func': '_package_new_entry_signed_authority_detail', 'question': 'Condition: not source_boundary. Which side of this condition is the decision?', 'true_side': 'package_new_entry_authority_source_boundary_miss', 'false_side': 'other_side', 'effects': ['failures.append']}, {'spot': 'sv4_1005_package_new_entry_authority_source_boundary_not_', 'line': 1005, 'func': '_package_new_entry_signed_authority_detail', 'question': 'Condition: not _predecision_no_outcome_boundary(source_boundary). Which side of this condition is the decision?', 'true_side': 'package_new_entry_authority_source_boundary_not_', 'false_side': 'other_side', 'effects': ['failures.append']}, {'spot': 'sv4_1007_package_new_entry_authority_uses_outcome_fields_', 'line': 1007, 'func': '_package_new_entry_signed_authority_detail', 'question': 'Condition: uses_outcome_fields is not False. Which side of this condition is the decision?', 'true_side': 'package_new_entry_authority_uses_outcome_fields_', 'false_side': 'other_side', 'effects': ['failures.append']}, {'spot': 'sv4_1201_source_missing', 'line': 1201, 'func': '_quality_contract_detail', 'question': 'Condition: not _text(sources.get(field)). Which side of this condition is the decision?', 'true_side': 'source_missing', 'false_side': 'other_side', 'effects': ['failures.append']}, {'spot': 'sv4_1206_source_inferred', 'line': 1206, 'func': '_quality_contract_detail', 'question': 'Condition: source_label and any(\n            token in source_label.lower()\n            for token in ("inferred", "heuristic", "fallback", "default")\n        ). Which side of this condition is the decision?', 'true_side': 'source_inferred', 'false_side': 'other_side', 'effects': ['warnings.append']}, {'spot': 'sv4_1212_fill_probability_source_is_execution_fillability', 'line': 1212, 'func': '_quality_contract_detail', 'question': 'Condition: fill_probability_source and any(\n        token in fill_probability_source.lower()\n        for token in (\n            "predecision_limit_fillability",\n            "limit_fillability",\n            "execution_fill_probabili. Which side of this condition is the decision?', 'true_side': 'fill_probability_source_is_execution_fillability', 'false_side': 'other_side', 'effects': ['failures.append']}, {'spot': 'sv4_1226_candidate_decision_quality_source_boundary_missi', 'line': 1226, 'func': '_quality_contract_detail', 'question': 'Condition: not boundary. Which side of this condition is the decision?', 'true_side': 'candidate_decision_quality_source_boundary_missi', 'false_side': 'other_side', 'effects': ['failures.append']}, {'spot': 'sv4_1229_candidate_decision_quality_source_boundary_not_p', 'line': 1229, 'func': '_quality_contract_detail', 'question': 'Condition: not _predecision_no_outcome_boundary(boundary). Which side of this condition is the decision?', 'true_side': 'candidate_decision_quality_source_boundary_not_p', 'false_side': 'other_side', 'effects': ['failures.append']}, {'spot': 'sv4_1232_candidate_decision_quality_alias_status', 'line': 1232, 'func': '_quality_contract_detail', 'question': 'Condition: alias_status not in {\n        "exact_materialized",\n        "exact_materialized_from_complete_predecision_quality_sources",\n    } and not (\n        alias_status == "materialized"\n        and required_sources_present\n    . Which side of this condition is the decision?', 'true_side': 'candidate_decision_quality_alias_status', 'false_side': 'other_side', 'effects': ['failures.append']}, {'spot': 'sv4_1245_candidate_decision_quality_alias_mismatch', 'line': 1245, 'func': '_quality_contract_detail', 'question': 'Condition: field_text. Which side of this condition is the decision?', 'true_side': 'candidate_decision_quality_alias_mismatch', 'false_side': 'other_side', 'effects': ['failures.append']}, {'spot': 'sv4_1249_failures_append', 'line': 1249, 'func': '_quality_contract_detail', 'question': 'Condition: failure_text. Which side of this condition is the decision?', 'true_side': 'failures_append', 'false_side': 'other_side', 'effects': ['failures.append']}, {'spot': 'sv4_1255_warnings_append', 'line': 1255, 'func': '_quality_contract_detail', 'question': 'Condition: warning_text. Which side of this condition is the decision?', 'true_side': 'warnings_append', 'false_side': 'other_side', 'effects': ['warnings.append']}, {'spot': 'sv4_1299_long', 'line': 1299, 'func': '_candidate_side', 'question': 'Condition: side in {"BUY", "BULL", "BULLISH", "LONG"}. Which side of this condition is the decision?', 'true_side': 'long', 'false_side': 'other_side', 'effects': ['label']}, {'spot': 'sv4_1301_short', 'line': 1301, 'func': '_candidate_side', 'question': 'Condition: side in {"SELL", "BEAR", "BEARISH", "SHORT"}. Which side of this condition is the decision?', 'true_side': 'short', 'false_side': 'other_side', 'effects': ['label']}, {'spot': 'sv4_1308_long', 'line': 1308, 'func': '_direction', 'question': 'Condition: text in {"BUY", "BULL", "BULLISH", "LONG", "UP"}. Which side of this condition is the decision?', 'true_side': 'long', 'false_side': 'other_side', 'effects': ['label']}, {'spot': 'sv4_1310_short', 'line': 1310, 'func': '_direction', 'question': 'Condition: text in {"SELL", "BEAR", "BEARISH", "SHORT", "DOWN"}. Which side of this condition is the decision?', 'true_side': 'short', 'false_side': 'other_side', 'effects': ['label']}, {'spot': 'sv4_1312_neutral', 'line': 1312, 'func': '_direction', 'question': 'Condition: text in {"BOTH", "NEUTRAL", "NONE", "FLAT", "MIXED"}. Which side of this condition is the decision?', 'true_side': 'neutral', 'false_side': 'other_side', 'effects': ['label']}, {'spot': 'sv4_1318_long', 'line': 1318, 'func': '_action_from_side', 'question': 'Condition: side == "LONG". Which side of this condition is the decision?', 'true_side': 'long', 'false_side': 'other_side', 'effects': ['label']}, {'spot': 'sv4_1320_short', 'line': 1320, 'func': '_action_from_side', 'question': 'Condition: side == "SHORT". Which side of this condition is the decision?', 'true_side': 'short', 'false_side': 'other_side', 'effects': ['label']}, {'spot': 'sv4_1404_market_state', 'line': 1404, 'func': '_source_family', 'question': 'Condition: "market" in material or "whiteboard" in material. Which side of this condition is the decision?', 'true_side': 'market_state', 'false_side': 'other_side', 'effects': ['label']}, {'spot': 'sv4_1406_cost', 'line': 1406, 'func': '_source_family', 'question': 'Condition: "cost" in material or "swap" in material or "slippage" in material. Which side of this condition is the decision?', 'true_side': 'cost', 'false_side': 'other_side', 'effects': ['label']}, {'spot': 'sv4_1408_lifecycle', 'line': 1408, 'func': '_source_family', 'question': 'Condition: "lifecycle" in material or "ticket" in material or "position" in material. Which side of this condition is the decision?', 'true_side': 'lifecycle', 'false_side': 'other_side', 'effects': ['label']}, {'spot': 'sv4_1410_source_completeness', 'line': 1410, 'func': '_source_family', 'question': 'Condition: "source_complete" in material or "source_completeness" in material. Which side of this condition is the decision?', 'true_side': 'source_completeness', 'false_side': 'other_side', 'effects': ['label']}, {'spot': 'sv4_1412_selector', 'line': 1412, 'func': '_source_family', 'question': 'Condition: "selector" in material or "framework" in material or "numeric_confluence" in material. Which side of this condition is the decision?', 'true_side': 'selector', 'false_side': 'other_side', 'effects': ['label']}, {'spot': 'sv4_1568_avoid', 'line': 1568, 'func': '_evaluate_confluence', 'question': 'Condition: alignment == 1 and strength >= hard_avoid_strength and confidence >= hard_avoid_strength. Which side of this condition is the decision?', 'true_side': 'avoid', 'false_side': 'other_side', 'effects': ['hard_avoid.append']}, {'spot': 'sv4_1960_broker_net_pretrade_cost_packet_refused', 'line': 1960, 'func': '_evaluate_cost', 'question': 'Condition: packet_status and packet_status not in {"PASSED", "PASS", "OK"}. Which side of this condition is the decision?', 'true_side': 'broker_net_pretrade_cost_packet_refused', 'false_side': 'other_side', 'effects': ['assign:cost_authority_block_reason']}, {'spot': 'sv4_1966_broker_net_cost_authority_not_executable', 'line': 1966, 'func': '_evaluate_cost', 'question': 'Condition: cost_authority != "broker_calibrated_replay_cost". Which side of this condition is the decision?', 'true_side': 'broker_net_cost_authority_not_executable', 'false_side': 'other_side', 'effects': ['assign:cost_authority_block_reason']}, {'spot': 'sv4_1971_broker_net_cost_source_gap_not_executable', 'line': 1971, 'func': '_evaluate_cost', 'question': 'Condition: cost_source_gap_status != "source_bound_cost_authority_present". Which side of this condition is the decision?', 'true_side': 'broker_net_cost_source_gap_not_executable', 'false_side': 'other_side', 'effects': ['assign:cost_authority_block_reason']}, {'spot': 'sv4_1976_broker_net_candidate_cost_fallback_not_order_aut', 'line': 1976, 'func': '_evaluate_cost', 'question': 'Condition: fallback_is_authority. Which side of this condition is the decision?', 'true_side': 'broker_net_candidate_cost_fallback_not_order_aut', 'false_side': 'other_side', 'effects': ['assign:cost_authority_block_reason']}, {'spot': 'sv4_1980_broker_net_source_gap_cost_fallback_blocked', 'line': 1980, 'func': '_evaluate_cost', 'question': 'Condition: source_gap_cost_fallback_blocked. Which side of this condition is the decision?', 'true_side': 'broker_net_source_gap_cost_fallback_blocked', 'false_side': 'other_side', 'effects': ['assign:cost_authority_block_reason']}, {'spot': 'sv4_2305_unknown', 'line': 2305, 'func': '_origin_family', 'question': 'Condition: key in GENERIC_PACKAGE_ORIGIN_KEYS. Which side of this condition is the decision?', 'true_side': 'unknown', 'false_side': 'other_side', 'effects': ['label']}, {'spot': 'sv4_2410_refused_source_required', 'line': 2410, 'func': '_refuse', 'question': 'Condition: required. Which side of this condition is the decision?', 'true_side': 'refused_source_required', 'false_side': 'fallback_static_floor', 'effects': ['assign:block', 'assign:block', 'assign:block']}, {'spot': 'sv4_2424_artifact_path_not_configured', 'line': 2424, 'func': '_evaluate_learned_edge', 'question': 'Condition: not artifact_path. Which side of this condition is the decision?', 'true_side': 'artifact_path_not_configured', 'false_side': 'other_side', 'effects': ['return:_refuse']}, {'spot': 'sv4_2437_scorer_refused', 'line': 2437, 'func': '_evaluate_learned_edge', 'question': 'Condition: scored.get("status") != "scored". Which side of this condition is the decision?', 'true_side': 'scorer_refused', 'false_side': 'other_side', 'effects': ['return:_refuse']}, {'spot': 'sv4_2513_diagnostic_reasons_append', 'line': 2513, 'func': 'add_exact_rule_reason', 'question': 'Condition: exact_rules_are_diagnostic. Which side of this condition is the decision?', 'true_side': 'diagnostic_reasons_append', 'false_side': 'other_side', 'effects': ['diagnostic_reasons.append']}, {'spot': 'sv4_2519_admission_quality_dynamic_router_refused_candida', 'line': 2519, 'func': '_evaluate_admission_quality_guard', 'question': 'Condition: router_refused_candidate and _truthy(\n            cfg.get("selector_v4_enforce_dynamic_router_refusal", False)\n        ). Which side of this condition is the decision?', 'true_side': 'admission_quality_dynamic_router_refused_candida', 'false_side': 'other_side', 'effects': ['assign:reason']}, {'spot': 'sv4_2526_source_required_fields_append', 'line': 2526, 'func': '_evaluate_admission_quality_guard', 'question': 'Condition: action == "source_required". Which side of this condition is the decision?', 'true_side': 'source_required_fields_append', 'false_side': 'other_side', 'effects': ['source_required_fields.append']}, {'spot': 'sv4_2528_admission_quality_dynamic_router_refusal_open_re', 'line': 2528, 'func': '_evaluate_admission_quality_guard', 'question': 'Condition: action in {"open-reduced-risk", "open_reduced_risk"}. Which side of this condition is the decision?', 'true_side': 'admission_quality_dynamic_router_refusal_open_re', 'false_side': 'other_side', 'effects': ['reduced_risk_reasons.append']}, {'spot': 'sv4_2532_reduced_risk_reasons_append', 'line': 2532, 'func': '_evaluate_admission_quality_guard', 'question': 'Condition: action in {"reduce-risk", "reduce_risk"}. Which side of this condition is the decision?', 'true_side': 'reduced_risk_reasons_append', 'false_side': 'other_side', 'effects': ['reduced_risk_reasons.append']}, {'spot': 'sv4_2536_admission_quality_partial_be_runner_blocked_afte', 'line': 2536, 'func': '_evaluate_admission_quality_guard', 'question': 'Condition: dynamic_policy == "partial_be_runner"\n            and _truthy(cfg.get("selector_v4_block_partial_be_runner", True)). Which side of this condition is the decision?', 'true_side': 'admission_quality_partial_be_runner_blocked_afte', 'false_side': 'other_side', 'effects': ['hard_reject_reasons.append']}, {'spot': 'sv4_2543_admission_quality_off_session_partial_be_runner_', 'line': 2543, 'func': '_evaluate_admission_quality_guard', 'question': 'Condition: route_session in {"off_configured_session", "off_kz"}\n            and dynamic_policy == "partial_be_runner"\n            and _truthy(\n                cfg.get("selector_v4_block_off_configured_session_partial_be_runner", T. Which side of this condition is the decision?', 'true_side': 'admission_quality_off_session_partial_be_runner_', 'false_side': 'other_side', 'effects': ['hard_reject_reasons.append']}, {'spot': 'sv4_2553_admission_quality_off_configured_session_entry_b', 'line': 2553, 'func': '_evaluate_admission_quality_guard', 'question': 'Condition: route_session in {"off_configured_session", "off_kz"} and _truthy(\n            cfg.get("selector_v4_block_off_configured_session_entries", False)\n        ). Which side of this condition is the decision?', 'true_side': 'admission_quality_off_configured_session_entry_b', 'false_side': 'other_side', 'effects': ['assign:reason']}, {'spot': 'sv4_2561_source_required_fields_append', 'line': 2561, 'func': '_evaluate_admission_quality_guard', 'question': 'Condition: action == "source_required". Which side of this condition is the decision?', 'true_side': 'source_required_fields_append', 'false_side': 'other_side', 'effects': ['source_required_fields.append']}, {'spot': 'sv4_2563_admission_quality_off_configured_session_open_re', 'line': 2563, 'func': '_evaluate_admission_quality_guard', 'question': 'Condition: action in {"open-reduced-risk", "open_reduced_risk"}. Which side of this condition is the decision?', 'true_side': 'admission_quality_off_configured_session_open_re', 'false_side': 'other_side', 'effects': ['reduced_risk_reasons.append']}, {'spot': 'sv4_2567_reduced_risk_reasons_append', 'line': 2567, 'func': '_evaluate_admission_quality_guard', 'question': 'Condition: action in {"reduce-risk", "reduce_risk"}. Which side of this condition is the decision?', 'true_side': 'reduced_risk_reasons_append', 'false_side': 'other_side', 'effects': ['reduced_risk_reasons.append']}, {'spot': 'sv4_2572_admission_quality_off_session_cost_above_full_ri', 'line': 2572, 'func': '_evaluate_admission_quality_guard', 'question': 'Condition: route_session in {"off_configured_session", "off_kz"}\n            and off_session_max_cost is not None\n            and total_cost_r > off_session_max_cost. Which side of this condition is the decision?', 'true_side': 'admission_quality_off_session_cost_above_full_ri', 'false_side': 'other_side', 'effects': ['reduced_risk_reasons.append']}, {'spot': 'sv4_2597_admission_quality_session_origin_family_blocked_', 'line': 2597, 'func': '_evaluate_admission_quality_guard', 'question': 'Condition: rule_session\n                    and rule_session == exact_rule_route_session\n                    and origin_family in rule_families. Which side of this condition is the decision?', 'true_side': 'admission_quality_session_origin_family_blocked_', 'false_side': 'other_side', 'effects': ['add_exact_rule_reason']}, {'spot': 'sv4_2638_admission_quality_broad_dynamic_accepted_loss_sy', 'line': 2638, 'func': '_evaluate_admission_quality_guard', 'question': 'Condition: rule_session\n                    and rule_session == exact_rule_route_session\n                    and origin_family in rule_families\n                    and candidate_symbol\n                    and candidate_symbol in ru. Which side of this condition is the decision?', 'true_side': 'admission_quality_broad_dynamic_accepted_loss_sy', 'false_side': 'other_side', 'effects': ['add_exact_rule_reason']}, {'spot': 'sv4_2658_admission_quality_utc_hour_bucket_blocked_after_', 'line': 2658, 'func': '_evaluate_admission_quality_guard', 'question': 'Condition: utc_hour_bucket and utc_hour_bucket in blocked_hours. Which side of this condition is the decision?', 'true_side': 'admission_quality_utc_hour_bucket_blocked_after_', 'false_side': 'other_side', 'effects': ['add_exact_rule_reason']}, {'spot': 'sv4_2717_selector_v4_calibrated_admission_expected_net_r', 'line': 2717, 'func': '_evaluate_admission_quality_guard', 'question': 'Condition: floor_expected_net_r is None. Which side of this condition is the decision?', 'true_side': 'selector_v4_calibrated_admission_expected_net_r', 'false_side': 'other_side', 'effects': ['source_required_fields.append']}, {'spot': 'sv4_2719_calibrated_admission_expected_net_r_below_genera', 'line': 2719, 'func': '_evaluate_admission_quality_guard', 'question': 'Condition: floor_expected_net_r < min_expected_net. Which side of this condition is the decision?', 'true_side': 'calibrated_admission_expected_net_r_below_genera', 'false_side': 'other_side', 'effects': ['calibrated_floor_failures.append']}, {'spot': 'sv4_2723_selector_v4_calibrated_admission_probability', 'line': 2723, 'func': '_evaluate_admission_quality_guard', 'question': 'Condition: floor_probability is None. Which side of this condition is the decision?', 'true_side': 'selector_v4_calibrated_admission_probability', 'false_side': 'other_side', 'effects': ['source_required_fields.append']}, {'spot': 'sv4_2725_calibrated_admission_probability_below_generaliz', 'line': 2725, 'func': '_evaluate_admission_quality_guard', 'question': 'Condition: floor_probability < min_probability. Which side of this condition is the decision?', 'true_side': 'calibrated_admission_probability_below_generaliz', 'false_side': 'other_side', 'effects': ['calibrated_floor_failures.append']}, {'spot': 'sv4_2733_selector_v4_calibrated_admission_fill_probabilit', 'line': 2733, 'func': '_evaluate_admission_quality_guard', 'question': 'Condition: require_fill_probability. Which side of this condition is the decision?', 'true_side': 'selector_v4_calibrated_admission_fill_probabilit', 'false_side': 'other_side', 'effects': ['source_required_fields.append']}, {'spot': 'sv4_2741_selector_v4_calibrated_admission_source_complete', 'line': 2741, 'func': '_evaluate_admission_quality_guard', 'question': 'Condition: source_completeness is None. Which side of this condition is the decision?', 'true_side': 'selector_v4_calibrated_admission_source_complete', 'false_side': 'other_side', 'effects': ['source_required_fields.append']}, {'spot': 'sv4_2745_calibrated_admission_source_completeness_below_g', 'line': 2745, 'func': '_evaluate_admission_quality_guard', 'question': 'Condition: source_completeness < min_source_completeness. Which side of this condition is the decision?', 'true_side': 'calibrated_admission_source_completeness_below_g', 'false_side': 'other_side', 'effects': ['calibrated_floor_failures.append']}, {'spot': 'sv4_2753_reduced_risk_reasons_extend', 'line': 2753, 'func': '_evaluate_admission_quality_guard', 'question': 'Condition: floor_failure_action in {"reduce-risk", "reduce_risk"}. Which side of this condition is the decision?', 'true_side': 'reduced_risk_reasons_extend', 'false_side': 'other_side', 'effects': ['reduced_risk_reasons.extend']}, {'spot': 'sv4_3574_selector_v4_broker_net_admission_v1', 'line': 3574, 'func': 'evaluate_selector_v4_admission', 'question': 'Condition: not enabled_value. Which side of this condition is the decision?', 'true_side': 'selector_v4_broker_net_admission_v1', 'false_side': 'other_side', 'effects': ['return:SelectorV4AdmissionDecision']}, {'spot': 'sv4_3767_ultimate_candidate_package_side_not_allowed_by_r', 'line': 3767, 'func': 'evaluate_selector_v4_admission', 'question': 'Condition: ultimate_package_side_policy_applies and not ultimate_package_replay_side_allowed. Which side of this condition is the decision?', 'true_side': 'ultimate_candidate_package_side_not_allowed_by_r', 'false_side': 'other_side', 'effects': ['hard_reject.append']}, {'spot': 'sv4_3770_same_symbol_duplicate_exposure', 'line': 3770, 'func': 'evaluate_selector_v4_admission', 'question': 'Condition: lifecycle["duplicate_exposure"]. Which side of this condition is the decision?', 'true_side': 'same_symbol_duplicate_exposure', 'false_side': 'other_side', 'effects': ['hard_reject.append']}, {'spot': 'sv4_3772_same_symbol_conflict', 'line': 3772, 'func': 'evaluate_selector_v4_admission', 'question': 'Condition: lifecycle["same_symbol_conflict"] in {\n        "opposite-direction-open",\n        "long-short-conflict",\n        "ambiguous-hedge",\n        "duplicate-exposure",\n    }. Which side of this condition is the decision?', 'true_side': 'same_symbol_conflict', 'false_side': 'other_side', 'effects': ['hard_reject.append']}, {'spot': 'sv4_3780_probability_debate_veto', 'line': 3780, 'func': 'evaluate_selector_v4_admission', 'question': 'Condition: probability["vetoes"]. Which side of this condition is the decision?', 'true_side': 'probability_debate_veto', 'false_side': 'other_side', 'effects': ['hard_reject.extend']}, {'spot': 'sv4_3784_probability_debate_selected_opposite_action', 'line': 3784, 'func': 'evaluate_selector_v4_admission', 'question': 'Condition: selected_action in {"long", "short"} and selected_action != candidate_action. Which side of this condition is the decision?', 'true_side': 'probability_debate_selected_opposite_action', 'false_side': 'other_side', 'effects': ['hard_reject.append']}, {'spot': 'sv4_3786_probability_debate_selected_wait', 'line': 3786, 'func': 'evaluate_selector_v4_admission', 'question': 'Condition: selected_action == "wait". Which side of this condition is the decision?', 'true_side': 'probability_debate_selected_wait', 'false_side': 'other_side', 'effects': ['queue_reasons.append']}, {'spot': 'sv4_3788_probability_debate_selected_source_required', 'line': 3788, 'func': 'evaluate_selector_v4_admission', 'question': 'Condition: selected_action == "source-required". Which side of this condition is the decision?', 'true_side': 'probability_debate_selected_source_required', 'false_side': 'other_side', 'effects': ['source_required.append']}, {'spot': 'sv4_3831_broker_net_admission_ev_negative_after_cost', 'line': 3831, 'func': 'evaluate_selector_v4_admission', 'question': 'Condition: broker_net_admission_ev is not None and broker_net_admission_ev < 0.0. Which side of this condition is the decision?', 'true_side': 'broker_net_admission_ev_negative_after_cost', 'false_side': 'other_side', 'effects': ['hard_reject.append']}, {'spot': 'sv4_3838_broker_net_pretrade_cost_packet_refused', 'line': 3838, 'func': 'evaluate_selector_v4_admission', 'question': 'Condition: reasons. Which side of this condition is the decision?', 'true_side': 'broker_net_pretrade_cost_packet_refused', 'false_side': 'broker_net_pretrade_cost_packet_refused_not', 'effects': ['hard_reject.extend']}, {'spot': 'sv4_3844_cost_authority_block_reason', 'line': 3844, 'func': 'evaluate_selector_v4_admission', 'question': 'Condition: cost.get("cost_authority_block_reason"). Which side of this condition is the decision?', 'true_side': 'cost_authority_block_reason', 'false_side': 'other_side', 'effects': ['hard_reject.append']}, {'spot': 'sv4_3846_pretrade_cost_above_selector_v4_ceiling', 'line': 3846, 'func': 'evaluate_selector_v4_admission', 'question': 'Condition: total_cost > max_cost_r. Which side of this condition is the decision?', 'true_side': 'pretrade_cost_above_selector_v4_ceiling', 'false_side': 'other_side', 'effects': ['hard_reject.append']}, {'spot': 'sv4_3918_heuristic_probability', 'line': 3918, 'func': 'evaluate_selector_v4_admission', 'question': 'Condition: learned is not None. Which side of this condition is the decision?', 'true_side': 'heuristic_probability', 'false_side': 'other_side', 'effects': ['source_required.extend']}, {'spot': 'sv4_3955_ultimate_candidate_package_no_shadow_sleeve_matc', 'line': 3955, 'func': 'evaluate_selector_v4_admission', 'question': 'Condition: ultimate_package is not None\n        and _truthy(cfg.get("ultimate_candidate_package_require_shadow_match_for_selector_v4"))\n        and int(ultimate_package.get("matched_sleeve_count") or 0) <= 0. Which side of this condition is the decision?', 'true_side': 'ultimate_candidate_package_no_shadow_sleeve_matc', 'false_side': 'other_side', 'effects': ['hard_reject.append']}, {'spot': 'sv4_4486_ultimate_candidate_package_positive_predecision_', 'line': 4486, 'func': 'evaluate_selector_v4_admission', 'question': 'Condition: positive_package_off_session_softening_allowed and off_session_entry_was_present. Which side of this condition is the decision?', 'true_side': 'ultimate_candidate_package_positive_predecision_', 'false_side': 'other_side', 'effects': ['reduce_reasons.append']}, {'spot': 'sv4_4499_ultimate_candidate_package_no_shadow_sleeve_matc', 'line': 4499, 'func': 'evaluate_selector_v4_admission', 'question': 'Condition: ultimate_package_match_count <= 0. Which side of this condition is the decision?', 'true_side': 'ultimate_candidate_package_no_shadow_sleeve_matc', 'false_side': 'other_side', 'effects': ['hard_reject.append']}, {'spot': 'sv4_4501_ultimate_candidate_package_source_required_hold', 'line': 4501, 'func': 'evaluate_selector_v4_admission', 'question': 'Condition: ultimate_package_role_disposition == "source_required_hold". Which side of this condition is the decision?', 'true_side': 'ultimate_candidate_package_source_required_hold', 'false_side': 'other_side', 'effects': ['source_required.append']}, {'spot': 'sv4_4503_ultimate_candidate_package_non_admission_sleeve_', 'line': 4503, 'func': 'evaluate_selector_v4_admission', 'question': 'Condition: ultimate_package_admission_count <= 0. Which side of this condition is the decision?', 'true_side': 'ultimate_candidate_package_non_admission_sleeve_', 'false_side': 'other_side', 'effects': ['hard_reject.append']}, {'spot': 'sv4_4505_selected_cell_risk_nonpositive', 'line': 4505, 'func': 'evaluate_selector_v4_admission', 'question': 'Condition: (broker_net["risk_pct"] or 0.0) <= 0.0 and "selected_cell.risk_pct" not in source_required. Which side of this condition is the decision?', 'true_side': 'selected_cell_risk_nonpositive', 'false_side': 'other_side', 'effects': ['hard_reject.append']}, {'spot': 'sv4_4509_numeric_confluence_negative', 'line': 4509, 'func': 'evaluate_selector_v4_admission', 'question': 'Condition: confluence_score < 0.0. Which side of this condition is the decision?', 'true_side': 'numeric_confluence_negative', 'false_side': 'numeric_confluence_below_full_trade_floor', 'effects': ['hard_reject.append']}, {'spot': 'sv4_4644_ultimate_candidate_package_numeric_disagreement_', 'line': 4644, 'func': 'evaluate_selector_v4_admission', 'question': 'Condition: confluence["mixed_count"]. Which side of this condition is the decision?', 'true_side': 'ultimate_candidate_package_numeric_disagreement_', 'false_side': 'other_side', 'effects': ['reduce_reasons.append']}, {'spot': 'sv4_4650_probability_debate_uncertainty_above_full_risk_f', 'line': 4650, 'func': 'evaluate_selector_v4_admission', 'question': 'Condition: uncertainty > max_uncertainty. Which side of this condition is the decision?', 'true_side': 'probability_debate_uncertainty_above_full_risk_f', 'false_side': 'other_side', 'effects': ['reduce_reasons.append']}, {'spot': 'sv4_4652_open_trade_competition', 'line': 4652, 'func': 'evaluate_selector_v4_admission', 'question': 'Condition: lifecycle["open_trade_competition_status"] in {"stale-open-wins", "new-candidate-not-best"}. Which side of this condition is the decision?', 'true_side': 'open_trade_competition', 'false_side': 'other_side', 'effects': ['queue_reasons.append']}, {'spot': 'sv4_4718_softened_rejects_append', 'line': 4718, 'func': 'evaluate_selector_v4_admission', 'question': 'Condition: is_soft_package_reject. Which side of this condition is the decision?', 'true_side': 'softened_rejects_append', 'false_side': 'other_side', 'effects': ['softened_rejects.append']}, {'spot': 'sv4_4722_ultimate_candidate_package_admission_softened_se', 'line': 4722, 'func': 'evaluate_selector_v4_admission', 'question': 'Condition: softened_rejects. Which side of this condition is the decision?', 'true_side': 'ultimate_candidate_package_admission_softened_se', 'false_side': 'other_side', 'effects': ['reduce_reasons.append', 'reduce_reasons.extend']}, {'spot': 'sv4_4727_ultimate_candidate_package_selector_fill_floor_s', 'line': 4727, 'func': 'evaluate_selector_v4_admission', 'question': 'Condition: fill_floor_softening_broker_cost_ok. Which side of this condition is the decision?', 'true_side': 'ultimate_candidate_package_selector_fill_floor_s', 'false_side': 'other_side', 'effects': ['reduce_reasons.append']}, {'spot': 'sv4_4731_ultimate_candidate_package_selector_fill_floor_s', 'line': 4731, 'func': 'evaluate_selector_v4_admission', 'question': 'Condition: fill_floor_softening_edge_ok. Which side of this condition is the decision?', 'true_side': 'ultimate_candidate_package_selector_fill_floor_s', 'false_side': 'other_side', 'effects': ['reduce_reasons.append']}, {'spot': 'sv4_4852_source_required', 'line': 4852, 'func': 'evaluate_selector_v4_admission', 'question': 'Condition: source_required. Which side of this condition is the decision?', 'true_side': 'source_required', 'false_side': 'other_side', 'effects': ['assign:would_action', 'assign:reason']}, {'spot': 'sv4_4855_reject', 'line': 4855, 'func': 'evaluate_selector_v4_admission', 'question': 'Condition: hard_reject. Which side of this condition is the decision?', 'true_side': 'reject', 'false_side': 'other_side', 'effects': ['assign:would_action', 'assign:reason']}, {'spot': 'sv4_4858_no_trade', 'line': 4858, 'func': 'evaluate_selector_v4_admission', 'question': 'Condition: selected_action == "no-trade". Which side of this condition is the decision?', 'true_side': 'no_trade', 'false_side': 'other_side', 'effects': ['assign:would_action', 'assign:reason']}, {'spot': 'sv4_4861_queue', 'line': 4861, 'func': 'evaluate_selector_v4_admission', 'question': 'Condition: queue_reasons. Which side of this condition is the decision?', 'true_side': 'queue', 'false_side': 'other_side', 'effects': ['assign:would_action', 'assign:reason']}, {'spot': 'sv4_4864_source_required', 'line': 4864, 'func': 'evaluate_selector_v4_admission', 'question': 'Condition: broker_net_admission_ev is None. Which side of this condition is the decision?', 'true_side': 'source_required', 'false_side': 'other_side', 'effects': ['assign:would_action', 'assign:reason', 'source_required.append']}, {'spot': 'sv4_4868_no_trade', 'line': 4868, 'func': 'evaluate_selector_v4_admission', 'question': 'Condition: broker_net_admission_ev < min_no_trade_ev. Which side of this condition is the decision?', 'true_side': 'no_trade', 'false_side': 'other_side', 'effects': ['assign:would_action', 'assign:reason']}, {'spot': 'sv4_4871_broker_net_admission_ev_below_full_trade_floor', 'line': 4871, 'func': 'evaluate_selector_v4_admission', 'question': 'Condition: broker_net_admission_ev < min_trade_ev or reduce_reasons. Which side of this condition is the decision?', 'true_side': 'broker_net_admission_ev_below_full_trade_floor', 'false_side': 'trade', 'effects': ['assign:would_action']}, {'spot': 'sv4_4911_assign_reason', 'line': 4911, 'func': 'evaluate_selector_v4_admission', 'question': 'Condition: prioritized_open_reduced_reason\n            and prioritized_open_reduced_reason in open_reduced_risk_entry_reasons. Which side of this condition is the decision?', 'true_side': 'assign_reason', 'false_side': 'other_side', 'effects': ['assign:reason']}, {'spot': 'sv4_4916_broker_net_admission_ev_below_full_trade_floor', 'line': 4916, 'func': 'evaluate_selector_v4_admission', 'question': 'Condition: broker_net_admission_ev < min_trade_ev. Which side of this condition is the decision?', 'true_side': 'broker_net_admission_ev_below_full_trade_floor', 'false_side': 'other_side', 'effects': ['assign:reason']}, {'spot': 'sv4_4930_assign_risk_multiplier', 'line': 4930, 'func': 'evaluate_selector_v4_admission', 'question': 'Condition: would_action == "trade". Which side of this condition is the decision?', 'true_side': 'assign_risk_multiplier', 'false_side': 'other_side', 'effects': ['assign:risk_multiplier']}, {'spot': 'sv4_4932_assign_risk_multiplier', 'line': 4932, 'func': 'evaluate_selector_v4_admission', 'question': 'Condition: would_action in {"reduce-risk", "open-reduced-risk"}. Which side of this condition is the decision?', 'true_side': 'assign_risk_multiplier', 'false_side': 'other_side', 'effects': ['assign:risk_multiplier']}, {'spot': 'sv4_4948_segment_shrinkage_weights', 'line': 4948, 'func': 'evaluate_selector_v4_admission', 'question': 'Condition: t_trade is not None\n            and t_reduce is not None\n            and learned_expected_net_r is not None\n            and t_trade > t_reduce. Which side of this condition is the decision?', 'true_side': 'segment_shrinkage_weights', 'false_side': 'fallback_reason', 'effects': ['assign:risk_multiplier']}, {'spot': 'sv4_913_payload_missing', 'line': 913, 'func': '_package_new_entry_signed_authority_detail', 'question': 'The signed payload is not a mapping. Which side of that condition is the decision?', 'true_side': 'payload_missing', 'false_side': 'payload_missing_is_a_fact', 'effects': ['failures.append']}]

load_selector_choices(SELECTOR_CHOICE_SPOTS)
