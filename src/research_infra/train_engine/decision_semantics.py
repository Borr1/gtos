"""Evidence-only repairs for broad replay decision-cycle rows.

This module sits on the training-lane capture boundary.  It does not change a
candidate, an admission decision, sizing, an order, or an outcome.  It makes
the evidence emitted by those decisions honest and machine-readable:

* legacy cost fallbacks remain recorded but are not promoted to broker-cost
  authority;
* nested packet/repair provenance is flattened before the footprint projector
  drops containers;
* terminal outcomes are separated from mark sources;
* replay-only selector softening is visibly replay-only;
* heuristic/default EV inputs are marked non-authoritative.

The frozen replay loop is decision-contract-bound.  Keeping this repair in the
unbound capture layer preserves that contract while preventing later readers
from silently treating diagnostic placeholders as measurements.
"""

from __future__ import annotations

import math
from numbers import Real
from typing import Any, Iterable, Mapping


SCHEMA = "gtos.train_engine.decision_semantics.v2"

# The order is the pre-HB FD arithmetic order; completeness hardening must not
# introduce even an order-of-addition float delta on already-complete rows.
COST_COMPONENT_FIELDS = (
    "spread_r",
    "expected_slippage_r",
    "swap_cost_r",
    "commission_r",
)
COST_COMPONENT_TOLERANCE_R = 1e-8
_VALUE_ABSENT = object()

TRUSTED_COMMISSION_REPAIR_SOURCE = (
    "broker_true_BROKER_TRUE_COSTS_V1_round_turn_over_stop_distance"
)
_ALLOWED_COMPONENT_SOURCES = {
    "spread_r": frozenset(
        {
            "historical_ftmo_predecision_tick",
            "ultimate_book_historical_spread_floor_template",
            "broker_profile_symbol_spec_spread",
            "broker_profile_max_spread_cents_ceiling",
            "spread_model_v1_hour_aware",
        }
    ),
    "expected_slippage_r": frozenset(
        {
            "trade_params",
            "config.selected_cell_default_expected_slippage_r",
        }
    ),
    "swap_cost_r": frozenset({"points_mode_time_stop_swap_cost_r_v1"}),
    "commission_r": frozenset(
        {
            TRUSTED_COMMISSION_REPAIR_SOURCE,
            "broker_true_commission_cash_to_r_v1",
        }
    ),
}

_RETIRED_COST_DETAIL_FIELDS = (
    "cost_component_commission_delta_r",
    "cost_component_absent_fields",
    "cost_component_null_fields",
    "cost_component_invalid_fields",
    "cost_component_non_finite_fields",
    "cost_component_negative_fields",
    "cost_component_authority_missing_fields",
    "cost_component_authority_invalid_fields",
    "cost_component_authority_non_finite_fields",
    "cost_component_authority_negative_fields",
    "cost_component_inconsistent_fields",
    "cost_component_refusal_reasons",
    "commission_r_repair_total_redecode_invalid_fields",
    "commission_r_repair_total_redecode_non_finite_fields",
    "commission_r_repair_total_redecode_negative_fields",
    "commission_r_repair_total_redecode_authority_missing_fields",
    "commission_r_repair_total_redecode_inconsistent_fields",
    "commission_r_repair_total_redecode_refusal_reasons",
)

_COST_DERIVED_FIELDS = (
    "recorded_cost_r",
    "authoritative_cost_r",
    "legacy_emitter_fallback_cost_r",
    "cost_r_authority_status",
    "cost_capture_contract_status",
    "cost_capture_missing_inputs",
    "cost_capture_redecode_formula",
    "cost_redecode_candidate_r",
    "cost_redecode_authority_status",
    "cost_component_sum_r",
    "cost_component_candidate_sum_r",
    "cost_component_rebase_delta_r",
    "cost_component_state",
    *_RETIRED_COST_DETAIL_FIELDS,
    "cost_decision_authorization_status",
    "cost_decision_refusal_reasons",
    "cost_accounting_status",
)

LEVEL_TERMINAL_OUTCOMES = frozenset(
    {"stop_reached_before_target", "target_reached_before_stop"}
)

# These values come from ``src.components.ultimate_book.admission``.  They are
# historical/template floors applied when no decision-time tick is available;
# exact-value recognition is deliberately labelled an inference, not a quote.
HISTORICAL_SPREAD_FLOOR_TEMPLATES_R: dict[str, float] = {
    "BTCUSD": 0.0001,
    "UKOIL_cash": 0.0258,
    "USOIL_cash": 0.0270,
}

COST_PACKET_KEYS = (
    "pretrade_broker_net_cost_packet",
    "pretrade_cost_packet",
)

REPAIR_PROVENANCE_FIELDS = (
    "pretrade_cost_packet_status",
    "pretrade_cost_packet_model_version",
    "commission_r_broker_true_measured",
    "commission_r_repair_status",
    "commission_r_regated",
    "commission_r_source",
    "commission_r_repair_selection_semantics",
    "commission_r_repair_total_redecode_status",
    "commission_r_repair_total_redecode_missing_fields",
    "cost_component_state",
    "cost_decision_authorization_status",
    "cost_decision_refusal_reasons",
    "commission_r_repair_total_before_r",
    "commission_r_repair_total_after_r",
    "legacy_emitter_fallback_replaced",
    "swap_horizon_repair_status",
    "swap_horizon_bars_used",
    "expected_slippage_source",
    "cost_source_gap_status",
    "source_gap_cost_fallback_blocked",
    "candidate_cost_r_fallback_is_authority",
    "broker_pretrade_cost_executable_block_reason",
)

SEMANTIC_FIELDS = frozenset(
    {
        *REPAIR_PROVENANCE_FIELDS,
        "decision_semantics_schema",
        "candidate_identity_join_contract",
        "candidate_identity_join_status",
        "canonical_replay_candidate_instance_key",
        "final_blocker_class",
        "legacy_cost_quote_source",
        "cost_quote_source",
        "cost_quote_authority_class",
        "cost_quote_measurement_status",
        "cost_quote_provenance_inferred_from_legacy_value",
        "historical_template_spread_floor_r",
        "historical_tick_time_utc",
        "recorded_cost_r",
        "authoritative_cost_r",
        "legacy_emitter_fallback_cost_r",
        "cost_r_authority_status",
        "cost_capture_contract_status",
        "cost_capture_missing_inputs",
        "cost_capture_redecode_formula",
        "cost_redecode_candidate_r",
        "cost_redecode_authority_status",
        "cost_component_sum_r",
        "cost_component_candidate_sum_r",
        "cost_component_rebase_delta_r",
        "cost_component_state",
        "cost_component_capture_evidence",
        "cost_decision_authorization_status",
        "cost_decision_refusal_reasons",
        "cost_accounting_status",
        "legacy_close_mark_source",
        "close_mark_source",
        "close_mark_source_semantics_status",
        "terminal_outcome",
        "legacy_close_reason",
        "close_reason",
        "exit_raw_path_terminal",
        "exit_policy_overlay_close",
        "exit_layers_disagree",
        "close_mark_clamped",
        "close_mark_ambiguity_floor",
        "close_mark_clamp_semantics_status",
        "terminal_scoreability_status",
        "terminal_outcome_scoreability",
        "trade_headline_scoreable",
        "recorded_net_r",
        "authoritative_net_r",
        "expected_slippage_authority",
        "expected_slippage_measurement_status",
        "selector_router_reinjection_applied",
        "selector_router_reinjection_policy_status",
        "selector_router_reinjection_authority",
        "selector_router_reinjection_scope",
        "selector_router_reinjection_original_action",
        "selector_router_reinjection_materialized_action",
        "package_authority_gate_status",
        "package_authority_effective_config_value",
        "package_authority_failures",
        "package_authority_failure_capture_status",
        "package_authority_capture_requirement",
        "ev_cost_context_status",
        "ev_probability_cost_sensitivity_status",
        "ev_direct_cost_term_status",
        "candidate_ev_r_cost_scope",
        "expected_net_r_cost_scope",
        "authoritative_candidate_ev_r",
        "ev_geometry_alignment_status",
        "ev_reward_r_assumed_at_probability_stage",
        "execution_policy_target_r",
        "origin_family_hash_authority_status",
        "authoritative_origin_family_hash_component",
        "candidate_confidence_authority_status",
        "authoritative_candidate_confidence",
        "execution_fill_probability_authority_status",
        "execution_fill_probability_measurement_status",
        "authoritative_execution_fill_probability",
    }
)


def _optional_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def cost_number(value: Any) -> tuple[str, float | None]:
    """Parse a JSON cost scalar without Python's permissive numeric coercions.

    Cost evidence is emitted as JSON numbers. Booleans, numeric-looking strings,
    containers, non-finite values, and negative costs are not interchangeable
    with that capture contract. Favorable swap is deliberately clipped to zero
    by the producer, so every component in this four-term cost sum is
    non-negative.
    """

    if _is_blank(value):
        return "null", None
    if isinstance(value, bool) or not isinstance(value, Real):
        return "invalid", None
    number = float(value)
    if not math.isfinite(number):
        return "non_finite", None
    if number < 0.0:
        return "negative", None
    return "valid", number


def cost_component_sum(components: Mapping[str, Any]) -> float | None:
    """Return the exact historical four-term sum, or ``None`` if any term is invalid."""

    values: list[float] = []
    for field in COST_COMPONENT_FIELDS:
        status, number = cost_number(components.get(field, _VALUE_ABSENT))
        if status != "valid":
            return None
        assert number is not None
        values.append(number)
    return values[0] + values[1] + values[2] + values[3]


def _is_legacy_fallback(value: Any) -> bool:
    status, number = cost_number(value)
    return bool(
        status == "valid"
        and number is not None
        and math.isclose(number, 0.12, rel_tol=0.0, abs_tol=1e-12)
    )


def assess_cost_components(
    components: Mapping[str, Any],
    *,
    capture_evidence: Mapping[str, Any] | None = None,
    measured_commission_r: Any = _VALUE_ABSENT,
) -> dict[str, Any]:
    """Classify the four-component cost contract without inventing zeroes.

    A component key is evidence, not authority. Each value must agree with an
    independent numeric capture carrying the producer's exact source contract.
    Commission must additionally agree with the broker-truth measured value.
    The returned candidate sum is diagnostic until the state is ``complete``.
    """

    values: dict[str, float] = {}
    missing_inputs: list[str] = []
    reasons: list[str] = []
    inconsistent: list[str] = []
    for field in COST_COMPONENT_FIELDS:
        if field not in components:
            missing_inputs.append(field)
            reasons.append(f"absent_component:{field}")
            continue
        status, number = cost_number(components[field])
        if status == "valid":
            assert number is not None
            values[field] = number
        else:
            missing_inputs.append(field)
            reasons.append(f"{status}_component:{field}")

    capture_evidence = (
        capture_evidence if isinstance(capture_evidence, Mapping) else {}
    )
    for field in COST_COMPONENT_FIELDS:
        authority_name = f"{field}_capture_authority"
        if field not in capture_evidence:
            missing_inputs.append(authority_name)
            reasons.append(f"missing_authority:{authority_name}")
            continue
        capture = capture_evidence[field]
        if not isinstance(capture, Mapping):
            missing_inputs.append(authority_name)
            reasons.append(f"invalid_authority:{authority_name}")
            continue
        source = capture.get("source")
        source_status = capture.get("source_status")
        source_status_name = f"{field}_capture_source_status"
        if _is_blank(source_status):
            missing_inputs.append(source_status_name)
            reasons.append(f"missing_authority:{source_status_name}")
        elif source_status != "captured":
            missing_inputs.append(source_status_name)
            reasons.append(f"invalid_authority:{source_status_name}")
        source_name = f"{field}_capture_source"
        if _is_blank(source):
            missing_inputs.append(source_name)
            reasons.append(f"missing_authority:{source_name}")
        elif (
            not isinstance(source, str)
            or source != source.strip()
            or source not in _ALLOWED_COMPONENT_SOURCES[field]
        ):
            missing_inputs.append(source_name)
            reasons.append(f"invalid_authority:{source_name}")
        if field == "commission_r" and capture.get("included_in_total_cost_r") is not True:
            missing_inputs.append("commission_r_capture_inclusion")
            reasons.append("invalid_authority:commission_r_capture_inclusion")

        capture_status, capture_number = cost_number(capture.get("value"))
        capture_name = f"{field}_capture_value"
        if capture_status == "null":
            missing_inputs.append(capture_name)
            reasons.append(f"missing_authority:{capture_name}")
        elif capture_status != "valid":
            missing_inputs.append(capture_name)
            reasons.append(f"{capture_status}_authority:{capture_name}")
        elif field in values:
            assert capture_number is not None
            if not math.isclose(
                values[field],
                capture_number,
                rel_tol=0.0,
                abs_tol=COST_COMPONENT_TOLERANCE_R,
            ):
                inconsistent.append(f"{field}_vs_capture_evidence")

    measured_commission: float | None = None
    measured_name = "commission_r_broker_true_measured"
    if measured_commission_r is _VALUE_ABSENT:
        missing_inputs.append(measured_name)
        reasons.append(f"missing_authority:{measured_name}")
    else:
        measured_status, measured_commission = cost_number(measured_commission_r)
        if measured_status == "null":
            missing_inputs.append(measured_name)
            reasons.append(f"missing_authority:{measured_name}")
        elif measured_status != "valid":
            missing_inputs.append(measured_name)
            reasons.append(f"{measured_status}_authority:{measured_name}")

    component_commission = values.get("commission_r")
    if component_commission is not None and measured_commission is not None:
        if not math.isclose(
            component_commission,
            measured_commission,
            rel_tol=0.0,
            abs_tol=COST_COMPONENT_TOLERANCE_R,
        ):
            inconsistent.append(
                "commission_r_vs_commission_r_broker_true_measured"
            )

    state = "refused" if inconsistent else "incomplete" if missing_inputs else "complete"
    candidate_sum = cost_component_sum(components)

    reasons.extend(f"inconsistent_component:{field}" for field in inconsistent)
    return {
        "state": state,
        "candidate_sum_r": candidate_sum,
        "missing_inputs": list(dict.fromkeys(missing_inputs)),
        "refusal_reasons": list(dict.fromkeys(reasons)),
    }


def _first_present(*values: Any) -> Any:
    for value in values:
        if not _is_blank(value):
            return value
    return None


def _text_list(value: Any) -> list[str]:
    if _is_blank(value):
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, Iterable) and not isinstance(value, Mapping):
        return [str(item) for item in value if not _is_blank(item)]
    return [str(value)]


def _cost_packet(row: Mapping[str, Any]) -> Mapping[str, Any]:
    for key in COST_PACKET_KEYS:
        value = row.get(key)
        if isinstance(value, Mapping):
            return value
    return {}


def _canonical_spread_source(value: Any) -> Any:
    if value == "ultimate_book_measured_tick_spread_floor":
        return "ultimate_book_historical_spread_floor_template"
    return value


def cost_component_capture_evidence_from_packet(
    packet: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    """Extract the independent numeric/source witnesses from a cost packet.

    ``total_cost_components`` is the accounting vector. These child structures
    are the independent producer evidence that makes each term usable. Keeping
    this extraction in one function lets packet repair and row normalization use
    the same authority definition.
    """

    evidence: dict[str, dict[str, Any]] = {}
    quote = packet.get("quote_authority")
    quote = quote if isinstance(quote, Mapping) else {}
    tick_cost = packet.get("tick_cost")
    if isinstance(tick_cost, Mapping):
        evidence["spread_r"] = {
            "value": tick_cost.get("spread_r"),
            "source": _canonical_spread_source(
                _first_present(
                    quote.get("quote_source"),
                    packet.get("cost_quote_source"),
                )
            ),
            "source_status": tick_cost.get("source_status"),
        }

    evidence["expected_slippage_r"] = {
        "value": packet.get("expected_slippage_r"),
        "source": packet.get("expected_slippage_source"),
        "source_status": (
            "captured"
            if not _is_blank(packet.get("expected_slippage_source"))
            else "source_gap"
        ),
    }

    swap_cost = packet.get("swap_cost")
    if isinstance(swap_cost, Mapping):
        evidence["swap_cost_r"] = {
            "value": swap_cost.get("cost_r"),
            "source": swap_cost.get("model_version"),
            "source_status": swap_cost.get("source_status"),
        }

    commission_cost = packet.get("commission_cost")
    if isinstance(commission_cost, Mapping):
        evidence["commission_r"] = {
            "value": commission_cost.get("cost_r"),
            "source": _first_present(
                commission_cost.get("repair_source"),
                commission_cost.get("model_version"),
            ),
            "source_status": commission_cost.get("source_status"),
            "included_in_total_cost_r": commission_cost.get(
                "included_in_total_cost_r"
            ),
        }
    return evidence


def _cost_values_conflict(left: Any, right: Any) -> bool:
    left_status, left_number = cost_number(left)
    right_status, right_number = cost_number(right)
    if left_status != "valid" or right_status != "valid":
        return left_status != "null" or right_status != "null"
    assert left_number is not None and right_number is not None
    return not math.isclose(
        left_number,
        right_number,
        rel_tol=0.0,
        abs_tol=COST_COMPONENT_TOLERANCE_R,
    )


def _capture_evidence_conflicts(
    left: Mapping[str, Any],
    right: Mapping[str, Any],
) -> list[str]:
    conflicts: list[str] = []
    for field in COST_COMPONENT_FIELDS:
        if field not in left or field not in right:
            continue
        left_entry = left[field]
        right_entry = right[field]
        if not isinstance(left_entry, Mapping) or not isinstance(
            right_entry, Mapping
        ):
            conflicts.append(f"{field}_capture_top_level_vs_packet")
            continue
        if (
            _cost_values_conflict(
                left_entry.get("value"), right_entry.get("value")
            )
            or left_entry.get("source") != right_entry.get("source")
            or left_entry.get("source_status")
            != right_entry.get("source_status")
            or (
                field == "commission_r"
                and left_entry.get("included_in_total_cost_r")
                is not right_entry.get("included_in_total_cost_r")
            )
        ):
            conflicts.append(f"{field}_capture_top_level_vs_packet")
    return conflicts


def _mappings_equal(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    try:
        result = left == right
    except (TypeError, ValueError):
        return False
    return result is True


def _flatten_cost_packet(out: dict[str, Any]) -> None:
    packet = _cost_packet(out)
    scalar_fields = packet.get("scalar_fields")
    scalar_fields = scalar_fields if isinstance(scalar_fields, Mapping) else {}

    for output_name, packet_name in (
        ("pretrade_cost_packet_status", "status"),
        ("pretrade_cost_packet_model_version", "model_version"),
    ):
        value = _first_present(out.get(output_name), packet.get(packet_name))
        if value is not None:
            out[output_name] = value

    for field in REPAIR_PROVENANCE_FIELDS:
        value = _first_present(
            out.get(field),
            packet.get(field),
            scalar_fields.get(field),
        )
        if value is not None:
            out[field] = value

    quote = packet.get("quote_authority")
    quote = quote if isinstance(quote, Mapping) else {}
    quote_source = _first_present(
        out.get("cost_quote_source"),
        quote.get("quote_source"),
        packet.get("cost_quote_source"),
    )
    if quote_source is not None:
        out["cost_quote_source"] = str(quote_source)
    historical_tick_time = _first_present(
        out.get("historical_tick_time_utc"),
        quote.get("historical_tick_time_utc"),
        packet.get("historical_tick_time_utc"),
    )
    if historical_tick_time is not None:
        out["historical_tick_time_utc"] = historical_tick_time
    floor = _optional_float(
        _first_present(
            out.get("historical_template_spread_floor_r"),
            quote.get("measured_tick_spread_floor_r"),
            packet.get("measured_tick_spread_floor_r"),
            out.get("measured_tick_spread_floor_r"),
        )
    )
    if floor is not None:
        out["historical_template_spread_floor_r"] = floor


def _repair_quote_semantics(out: dict[str, Any]) -> None:
    source = str(out.get("cost_quote_source") or "").strip()
    if source == "ultimate_book_measured_tick_spread_floor":
        out["legacy_cost_quote_source"] = source
        out["cost_quote_source"] = (
            "ultimate_book_historical_spread_floor_template"
        )
        out["cost_quote_authority_class"] = "historical_template_floor"
        out["cost_quote_measurement_status"] = (
            "templated_not_decision_measured"
        )
        out["cost_quote_provenance_inferred_from_legacy_value"] = False
        return
    if source == "ultimate_book_historical_spread_floor_template":
        out["cost_quote_authority_class"] = "historical_template_floor"
        out["cost_quote_measurement_status"] = (
            "templated_not_decision_measured"
        )
        out.setdefault("cost_quote_provenance_inferred_from_legacy_value", False)
        return
    if source == "historical_ftmo_predecision_tick":
        out["cost_quote_authority_class"] = "historical_predecision_tick"
        out["cost_quote_measurement_status"] = "decision_asof_tick_measured"
        out["cost_quote_provenance_inferred_from_legacy_value"] = False
        return
    if source.startswith("broker_profile_"):
        out["cost_quote_authority_class"] = "broker_profile_template"
        out["cost_quote_measurement_status"] = (
            "configured_not_decision_measured"
        )
        out["cost_quote_provenance_inferred_from_legacy_value"] = False
        return
    if source == "conservative_default_spread_r_no_tick_or_symbol_spec":
        out["cost_quote_authority_class"] = "unmeasured_fallback"
        out["cost_quote_measurement_status"] = "fallback_not_measured"
        out["cost_quote_provenance_inferred_from_legacy_value"] = False
        return

    symbol = str(out.get("symbol") or "")
    spread = _optional_float(out.get("spread_r"))
    template = HISTORICAL_SPREAD_FLOOR_TEMPLATES_R.get(symbol)
    if (
        not source
        and spread is not None
        and template is not None
        and math.isclose(spread, template, rel_tol=0.0, abs_tol=1e-9)
    ):
        out["cost_quote_source"] = (
            "ultimate_book_historical_spread_floor_template"
        )
        out["historical_template_spread_floor_r"] = template
        out["cost_quote_authority_class"] = "historical_template_floor"
        out["cost_quote_measurement_status"] = (
            "templated_not_decision_measured"
        )
        out["cost_quote_provenance_inferred_from_legacy_value"] = True


def _commission_capture_missing_inputs(out: Mapping[str, Any]) -> list[str]:
    missing: list[str] = []
    repair_status = str(out.get("commission_r_repair_status") or "")
    if repair_status.startswith("unpriced:"):
        missing.append(repair_status.split(":", 1)[1])
    packet = _cost_packet(out)
    commission_cost = packet.get("commission_cost")
    commission_cost = (
        commission_cost if isinstance(commission_cost, Mapping) else {}
    )
    missing.extend(_text_list(commission_cost.get("missing_fields")))
    if not missing:
        missing.append("broker_true_commission_capture")
    return list(dict.fromkeys(missing))


def _recorded_cost(
    out: Mapping[str, Any],
) -> tuple[float | None, bool, list[str]]:
    present = [
        (name, out[name])
        for name in ("cost_r", "expected_cost_r")
        if name in out and not _is_blank(out[name])
    ]
    valid: list[tuple[str, float]] = []
    conflicts: list[str] = []
    for name, value in present:
        status, number = cost_number(value)
        if status != "valid":
            conflicts.append(f"{name}_invalid_{status}")
        else:
            assert number is not None
            valid.append((name, number))
    if len(valid) == 2 and not math.isclose(
        valid[0][1],
        valid[1][1],
        rel_tol=0.0,
        abs_tol=COST_COMPONENT_TOLERANCE_R,
    ):
        conflicts.append("cost_r_vs_expected_cost_r")
    return (valid[0][1] if valid else None), bool(present), conflicts


def _cost_inputs(
    out: dict[str, Any],
) -> tuple[dict[str, Any], Mapping[str, Any], Any, list[str]]:
    conflicts: list[str] = []
    packet_candidates = [
        (key, out[key])
        for key in COST_PACKET_KEYS
        if key in out and not _is_blank(out[key])
    ]
    mappings = [
        (key, value)
        for key, value in packet_candidates
        if isinstance(value, Mapping)
    ]
    if len(mappings) != len(packet_candidates):
        conflicts.append("cost_packet_container_invalid")
    if len(mappings) > 1 and any(
        not _mappings_equal(mappings[0][1], value)
        for _, value in mappings[1:]
    ):
        conflicts.append("conflicting_cost_packet_aliases")
    packet = mappings[0][1] if mappings else {}
    if mappings:
        raw_components = packet.get("total_cost_components")
        packet_components = (
            raw_components if isinstance(raw_components, Mapping) else {}
        )
        components = {
            field: packet_components[field]
            for field in COST_COMPONENT_FIELDS
            if field in packet_components
        }
        for field, value in components.items():
            out.setdefault(field, value)
        for field in COST_COMPONENT_FIELDS:
            if field in packet and field in packet_components and _cost_values_conflict(
                packet[field], packet_components[field]
            ):
                conflicts.append(f"{field}_packet_scalar_vs_components")
            if field in out and field in packet_components and _cost_values_conflict(
                out[field], packet_components[field]
            ):
                conflicts.append(f"{field}_top_level_vs_packet")

        nested_capture = cost_component_capture_evidence_from_packet(packet)
        existing_capture = out.get("cost_component_capture_evidence")
        if isinstance(existing_capture, Mapping):
            conflicts.extend(
                _capture_evidence_conflicts(existing_capture, nested_capture)
            )
        capture_evidence: Mapping[str, Any] = nested_capture
        out["cost_component_capture_evidence"] = nested_capture
    else:
        components = {
            field: out[field] for field in COST_COMPONENT_FIELDS if field in out
        }
        existing_capture = out.get("cost_component_capture_evidence")
        capture_evidence = (
            existing_capture if isinstance(existing_capture, Mapping) else {}
        )

        source_fields = {
            "spread_r": "cost_quote_source",
            "expected_slippage_r": "expected_slippage_source",
            "commission_r": "commission_r_source",
        }
        for field, source_field in source_fields.items():
            capture = capture_evidence.get(field)
            if not isinstance(capture, Mapping) or _is_blank(out.get(source_field)):
                continue
            expected_source = _canonical_spread_source(out.get(source_field))
            if capture.get("source") != expected_source:
                conflicts.append(f"{field}_source_vs_capture_evidence")

        commission_capture = capture_evidence.get("commission_r")
        if (
            isinstance(commission_capture, Mapping)
            and commission_capture.get("source") == TRUSTED_COMMISSION_REPAIR_SOURCE
            and (
                out.get("commission_r_repair_status") != "applied"
                or out.get("commission_r_repair_total_redecode_status")
                != "complete_component_sum"
            )
        ):
            capture_evidence = dict(capture_evidence)
            commission_capture = dict(commission_capture)
            commission_capture["source_status"] = "source_gap"
            capture_evidence["commission_r"] = commission_capture

    commission_cost = packet.get("commission_cost")
    commission_cost = (
        commission_cost if isinstance(commission_cost, Mapping) else {}
    )
    measured_sources = [
        value
        for present, value in (
            (
                "commission_r_broker_true_measured" in out,
                out.get("commission_r_broker_true_measured"),
            ),
            (
                "commission_r_broker_true_measured" in packet,
                packet.get("commission_r_broker_true_measured"),
            ),
            (
                "broker_true_measured_cost_r" in commission_cost,
                commission_cost.get("broker_true_measured_cost_r"),
            ),
        )
        if present and not _is_blank(value)
    ]
    for index, left in enumerate(measured_sources):
        for right in measured_sources[index + 1 :]:
            if _cost_values_conflict(left, right):
                conflicts.append("commission_r_broker_true_measured_sources")
                break
    measured = measured_sources[0] if measured_sources else _VALUE_ABSENT
    return components, capture_evidence, measured, list(dict.fromkeys(conflicts))


def _add_cost_conflicts(
    assessment: dict[str, Any],
    conflicts: Iterable[str],
    *,
    reasons: Iterable[str] = (),
) -> None:
    conflicts = list(dict.fromkeys(conflicts))
    assessment["state"] = "refused"
    assessment["refusal_reasons"] = list(
        dict.fromkeys(
            [
                *assessment["refusal_reasons"],
                *(f"inconsistent_component:{item}" for item in conflicts),
                *reasons,
            ]
        )
    )


def publish_cost_assessment(
    out: dict[str, Any], assessment: Mapping[str, Any]
) -> None:
    for field in _RETIRED_COST_DETAIL_FIELDS:
        out.pop(field, None)
    out["cost_component_state"] = assessment["state"]
    state = str(assessment["state"])
    out["cost_decision_authorization_status"] = (
        "authorized_complete_component_cost"
        if state == "complete"
        else "refused_incomplete_component_cost"
        if state == "incomplete"
        else "refused_inconsistent_component_cost"
    )
    out["cost_decision_refusal_reasons"] = list(
        assessment["refusal_reasons"]
    )


def _refuse_cost(
    out: dict[str, Any],
    assessment: Mapping[str, Any],
    *,
    accounting_status: str,
) -> None:
    state = str(assessment["state"])
    out["authoritative_cost_r"] = None
    out["cost_r_authority_status"] = (
        "component_cost_incomplete_non_authoritative"
        if state == "incomplete"
        else "component_cost_inconsistent_non_authoritative"
    )
    out["cost_capture_contract_status"] = (
        "missing_capture_inputs"
        if state == "incomplete"
        else "refused_inconsistent_components"
    )
    out["cost_capture_missing_inputs"] = list(assessment["missing_inputs"])
    out["cost_accounting_status"] = accounting_status


def _geometry_rebase_valid(
    out: Mapping[str, Any],
    *,
    component_sum: float,
    recorded: float,
) -> bool:
    if out.get("marketable_limit_cost_r_rebased_to_effective_fill_geometry") is not True:
        return False
    original_status, original = cost_number(
        out.get("marketable_limit_original_expected_cost_r")
    )
    effective_status, effective = cost_number(
        out.get("marketable_limit_effective_expected_cost_r")
    )
    if original_status != "valid" or effective_status != "valid":
        return False
    assert original is not None and effective is not None
    if not math.isclose(
        original,
        component_sum,
        rel_tol=0.0,
        abs_tol=COST_COMPONENT_TOLERANCE_R,
    ) or not math.isclose(
        effective,
        recorded,
        rel_tol=0.0,
        abs_tol=COST_COMPONENT_TOLERANCE_R,
    ):
        return False
    raw_multiplier = out.get("limit_immediate_marketable_cost_r_rebase_multiplier")
    if _is_blank(raw_multiplier):
        return True
    multiplier_status, multiplier = cost_number(raw_multiplier)
    return bool(
        multiplier_status == "valid"
        and multiplier is not None
        and multiplier > 0.0
        and math.isclose(
            original * multiplier,
            effective,
            rel_tol=0.0,
            abs_tol=COST_COMPONENT_TOLERANCE_R,
        )
    )


def _repair_cost_semantics(out: dict[str, Any]) -> None:
    packet = _cost_packet(out)
    raw_legacy_fallback = _first_present(
        out.get("legacy_emitter_fallback_cost_r"),
        packet.get("legacy_emitter_fallback_cost_r"),
    )
    for field in _COST_DERIVED_FIELDS:
        out.pop(field, None)

    recorded, recorded_present, recorded_conflicts = _recorded_cost(out)
    if recorded is not None:
        out["recorded_cost_r"] = recorded

    components, capture_evidence, measured, source_conflicts = _cost_inputs(out)
    cost_surface_present = any(
        key in out and not _is_blank(out[key])
        for key in (*COST_PACKET_KEYS, *COST_COMPONENT_FIELDS)
    )
    if not recorded_present and not components and not cost_surface_present:
        return
    assessment = assess_cost_components(
        components,
        capture_evidence=capture_evidence,
        measured_commission_r=measured,
    )
    conflicts = list(dict.fromkeys([*recorded_conflicts, *source_conflicts]))
    if conflicts:
        _add_cost_conflicts(assessment, conflicts)
    publish_cost_assessment(out, assessment)

    component_sum = assessment["candidate_sum_r"]
    if component_sum is not None:
        out["cost_component_candidate_sum_r"] = component_sum
    delta = (
        recorded - component_sum
        if recorded is not None and component_sum is not None
        else None
    )
    if delta is not None:
        out["cost_component_rebase_delta_r"] = delta

    packet_components = packet.get("total_cost_components")
    packet_components = (
        packet_components if isinstance(packet_components, Mapping) else {}
    )
    preserved_legacy = _is_legacy_fallback(raw_legacy_fallback)
    named_fallback = bool(
        _is_legacy_fallback(recorded)
        and (
            "cost_missing" in str(out.get("miss_reason") or "")
            or _is_legacy_fallback(
                packet_components.get("authority_fallback_total_cost_r")
            )
            or (
                out.get("legacy_emitter_fallback_replaced") is True
                and preserved_legacy
            )
        )
    )
    if named_fallback or preserved_legacy:
        out["legacy_emitter_fallback_cost_r"] = 0.12
    if named_fallback:
        out["cost_capture_redecode_formula"] = (
            "spread_r + expected_slippage_r + swap_cost_r + "
            "broker_true_commission_r"
        )
        if component_sum is not None:
            out["cost_redecode_candidate_r"] = component_sum

    fallback_binding = packet if packet else out
    current_fallback_binding = bool(
        fallback_binding.get("legacy_emitter_fallback_replaced") is True
        and _is_legacy_fallback(
            fallback_binding.get("legacy_emitter_fallback_cost_r")
        )
        and fallback_binding.get("commission_r_repair_status") == "applied"
        and fallback_binding.get("commission_r_repair_total_redecode_status")
        == "complete_component_sum"
        and fallback_binding.get("commission_r_source")
        == TRUSTED_COMMISSION_REPAIR_SOURCE
    )
    if assessment["state"] != "complete":
        _refuse_cost(
            out,
            assessment,
            accounting_status=(
                "legacy_fallback_applied_components_not_authoritative_total"
                if named_fallback
                else "recorded_cost_without_complete_component_capture"
                if assessment["state"] == "incomplete"
                else "component_sum_residual_refused"
            ),
        )
        if named_fallback:
            out["cost_r_authority_status"] = (
                "legacy_emitter_fallback_non_authoritative"
            )
            out["cost_redecode_authority_status"] = (
                "blocked_incomplete_components"
                if assessment["state"] == "incomplete"
                else "refused_inconsistent_components"
            )
            out["cost_capture_missing_inputs"] = list(
                dict.fromkeys(
                    [
                        *out["cost_capture_missing_inputs"],
                        *_commission_capture_missing_inputs(out),
                    ]
                )
            )
        return

    if named_fallback and not current_fallback_binding:
        reason = "legacy_fallback_requires_current_capture_binding"
        _add_cost_conflicts(
            assessment,
            ["legacy_emitter_fallback_cost_r"],
            reasons=[reason],
        )
        publish_cost_assessment(out, assessment)
        _refuse_cost(
            out,
            assessment,
            accounting_status=(
                "legacy_fallback_with_complete_components_not_row_authorized"
            ),
        )
        out["cost_r_authority_status"] = (
            "legacy_emitter_fallback_non_authoritative"
        )
        out["cost_redecode_authority_status"] = (
            "candidate_only_requires_arm_receipt_binding"
        )
        return

    component_mismatch = bool(
        delta is not None
        and not math.isclose(
            delta,
            0.0,
            rel_tol=0.0,
            abs_tol=COST_COMPONENT_TOLERANCE_R,
        )
    )
    valid_rebase = bool(
        recorded is not None
        and component_sum is not None
        and component_mismatch
        and _geometry_rebase_valid(
            out,
            component_sum=component_sum,
            recorded=recorded,
        )
    )
    if component_mismatch and not valid_rebase and not current_fallback_binding:
        reason = "recorded_total_component_sum_mismatch"
    else:
        reason = None
    if reason is not None:
        _add_cost_conflicts(
            assessment,
            [
                "recorded_cost_r_vs_cost_component_candidate_sum_r"
            ],
            reasons=[reason],
        )
        publish_cost_assessment(out, assessment)
        _refuse_cost(
            out,
            assessment,
            accounting_status="component_sum_residual_refused",
        )
        return

    assert component_sum is not None
    authoritative = (
        component_sum
        if recorded is None or current_fallback_binding
        else recorded
    )
    out["cost_component_sum_r"] = component_sum
    out["authoritative_cost_r"] = authoritative
    out["cost_capture_contract_status"] = (
        "complete_components_redecoded"
        if current_fallback_binding
        else "complete_components_captured"
    )
    out["cost_capture_missing_inputs"] = []
    if current_fallback_binding:
        out["cost_r_authority_status"] = (
            "legacy_emitter_fallback_redecoded_from_captured_components"
        )
        out["cost_redecode_authority_status"] = (
            "authorized_by_row_level_commission_repair_provenance"
        )
        out["cost_accounting_status"] = (
            "legacy_fallback_replaced_by_complete_component_sum"
        )
        return
    if recorded is None:
        out["cost_r_authority_status"] = "complete_component_sum_authoritative"
        out["cost_accounting_status"] = "component_sum_without_recorded_total"
        return

    status = str(out.get("pretrade_cost_packet_status") or "").upper()
    broker_executable = out.get("broker_pretrade_cost_executable")
    if broker_executable is True:
        out["cost_r_authority_status"] = "broker_pretrade_cost_authoritative"
    elif status == "REFUSED" or broker_executable is False:
        out["cost_r_authority_status"] = (
            "broker_cost_diagnostic_authoritative_nonexecutable"
        )
    else:
        out["cost_r_authority_status"] = (
            "recorded_cost_authority_status_not_captured"
        )
    out["cost_accounting_status"] = (
        "component_sum_plus_explicit_geometry_rebase"
        if valid_rebase
        else "component_sum_exact"
    )


def _repair_slippage_semantics(out: dict[str, Any]) -> None:
    slippage = _optional_float(out.get("expected_slippage_r"))
    if slippage is None:
        return
    source = str(out.get("expected_slippage_source") or "").strip()
    if math.isclose(slippage, 0.02, rel_tol=0.0, abs_tol=1e-12) and (
        not source or source == "config.selected_cell_default_expected_slippage_r"
    ):
        out["expected_slippage_authority"] = (
            "config.selected_cell_default_expected_slippage_r"
        )
        out["expected_slippage_measurement_status"] = (
            "modeled_constant_not_measured"
        )
    elif "realized" in source or "broker" in source:
        out["expected_slippage_authority"] = source
        out["expected_slippage_measurement_status"] = "measured"
    else:
        out["expected_slippage_authority"] = source or "model_input_unspecified"
        out["expected_slippage_measurement_status"] = "modeled_not_measured"


def _repair_terminal_semantics(out: dict[str, Any], *, row_kind: str | None) -> None:
    source = str(out.get("close_mark_source") or "").strip()
    terminal = str(out.get("terminal_outcome") or "").strip()
    if source in LEVEL_TERMINAL_OUTCOMES:
        out["legacy_close_mark_source"] = source
        out["terminal_outcome"] = terminal or source
        out["close_mark_source"] = None
        out["close_mark_source_semantics_status"] = (
            "legacy_terminal_outcome_overload_repaired"
        )
    elif source == "time_stop_close_mark_from_m1":
        out["legacy_close_mark_source"] = source
        out["close_mark_source"] = "m1"
        out["close_mark_source_semantics_status"] = (
            "legacy_time_stop_label_normalized_to_source"
        )
    elif source == "time_stop_close_mark_from_tick":
        out["legacy_close_mark_source"] = source
        out["close_mark_source"] = "tick"
        out["close_mark_source_semantics_status"] = (
            "legacy_time_stop_label_normalized_to_source"
        )
    elif source:
        out["close_mark_source_semantics_status"] = "source_semantics_preserved"
    elif row_kind == "trade" or terminal:
        out["close_mark_source_semantics_status"] = "source_not_recorded"

    close_reason = str(out.get("close_reason") or "").strip()
    exclusion = str(out.get("headline_result_exclusion_reason") or "").strip()
    close_reason_is_unscoreable = bool(
        "unscoreable" in close_reason
        or "ordered_tick_sequence_required" in close_reason
        or "terminal_r_ordered" in close_reason
    )
    exclusion_is_unscoreable = bool(
        "unscoreable" in exclusion
        or "ordered_tick_sequence_required" in exclusion
        or "terminal_r_ordered" in exclusion
    )
    unscoreable_reason = _first_present(
        exclusion if exclusion_is_unscoreable else None,
        close_reason if close_reason_is_unscoreable else None,
    )
    if unscoreable_reason:
        out["terminal_scoreability_status"] = str(unscoreable_reason)
        if close_reason_is_unscoreable:
            out["legacy_close_reason"] = close_reason
            out["close_reason"] = None
        out["terminal_outcome_scoreability"] = "unscoreable_diagnostic_only"
        out["trade_headline_scoreable"] = False
        recorded_net = _optional_float(
            _first_present(out.get("net_r"), out.get("final_r"))
        )
        if recorded_net is not None:
            out["recorded_net_r"] = recorded_net
        out["authoritative_net_r"] = None
    elif row_kind == "trade":
        recorded_net = _optional_float(
            _first_present(out.get("net_r"), out.get("final_r"))
        )
        headline_eligible = exclusion in {"", "headline_result_eligible"}
        out["trade_headline_scoreable"] = headline_eligible
        if not headline_eligible:
            out["terminal_scoreability_status"] = exclusion
            out["terminal_outcome_scoreability"] = (
                "diagnostic_not_headline_authority"
            )
        if recorded_net is not None:
            out["recorded_net_r"] = recorded_net
            out["authoritative_net_r"] = recorded_net if headline_eligible else None


#: The exact close-reason emitted by the frozen walker's same-bar ambiguity
#: branch (v4_timewarp `path_final_r`), where -1.0 is ASSIGNED conservatively
#: rather than marked from a close price.
_AMBIGUITY_FLOOR_CLOSE_REASON = "same_bar_ambiguity_conservative_stop_close"

#: Close-reason prefixes whose final R passed through the frozen walker's
#: `bounded_close_r = max(-1.0, min(close_mark_r, target_r))` bound.
_MARK_CLOSE_REASON_PREFIXES = (
    "time_stop_close_mark_from_",
    "time_stop_close_after_partial_harvest_from_",
)


def _exit_reason_surface(out: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(
        str(value or "").strip()
        for value in (
            out.get("terminal_outcome"),
            out.get("close_reason"),
            out.get("legacy_close_reason"),
            out.get("opportunity_close_reason"),
            out.get("raw_opportunity_close_reason"),
        )
    )


def _stamp_exit_vocabulary_layers(out: dict[str, Any]) -> None:
    """Name the two exit vocabularies explicitly (R-SCHEMA, walk trade 4).

    ``terminal_outcome`` describes the raw contract walk (what the ordered
    path did: e.g. ``stop_reached_before_target``) while ``close_reason``
    describes the selected-policy overlay (how the replayed policy actually
    closed: e.g. ``selected_policy_replay:giveback_close``).  The two DISAGREE
    legitimately -- walk trade 4 hit its stop on the raw path after the
    policy overlay had already harvested +0.778 at the giveback trigger.
    These additive companions name the layers so no reader conflates them;
    the original fields stay byte-identical.
    """

    raw_terminal = str(out.get("terminal_outcome") or "").strip()
    overlay = str(
        _first_present(
            out.get("close_reason"),
            out.get("legacy_close_reason"),
            out.get("opportunity_close_reason"),
        )
        or ""
    ).strip()
    if not raw_terminal and not overlay:
        return
    out["exit_raw_path_terminal"] = raw_terminal or None
    out["exit_policy_overlay_close"] = overlay or None
    out["exit_layers_disagree"] = bool(
        raw_terminal and overlay and raw_terminal != overlay
    )


def _stamp_close_mark_clamp_semantics(out: dict[str, Any]) -> None:
    """Derive the frozen walker's close-mark clamp at the evidence layer.

    The engine file is R2-bound, so the two silent relabel paths in
    ``path_final_r`` are stamped here from row fields instead of edited
    there: (a) same-bar ambiguity assigns exactly -1.0 while keeping a
    non-stop close reason; (b) ``bounded_close_r = max(-1.0, min(mark,
    target))`` can land a time-stop mark exactly on an endpoint.  Phase 1
    open question Q3 measured zero clamp firings on the fence arm and still
    asked for the flag by construction, so future windows stay separable.

    Derivability is honest, never guessed: the low bound needs only the mark;
    the high bound needs the target, and when a row carries disagreeing
    target fields (raw vs policy re-target) whose pairing with the mark is
    ambiguous, the stamp refuses with ``target_pairing_ambiguous_not_derivable``
    rather than picking one.
    """

    reasons = _exit_reason_surface(out)
    if any(reason == _AMBIGUITY_FLOOR_CLOSE_REASON for reason in reasons):
        out["close_mark_ambiguity_floor"] = True
        out["close_mark_clamped"] = False
        out["close_mark_clamp_semantics_status"] = (
            "ambiguity_conservative_floor_assigned_no_mark"
        )
        return
    mark_based = any(
        reason == "filled_time_stop_close_mark"
        or reason.startswith(_MARK_CLOSE_REASON_PREFIXES)
        for reason in reasons
    )
    if not mark_based:
        return
    out["close_mark_ambiguity_floor"] = False
    mark = _optional_float(
        _first_present(
            out.get("close_mark_r"),
            out.get("counterfactual_order_close_mark_r"),
        )
    )
    if mark is None:
        out["close_mark_clamped"] = None
        out["close_mark_clamp_semantics_status"] = (
            "close_mark_input_absent_not_derivable"
        )
        return
    if mark < -1.0:
        out["close_mark_clamped"] = True
        out["close_mark_clamp_semantics_status"] = "clamped_at_stop_floor"
        return
    targets = [
        target
        for target in (
            _optional_float(out.get("policy_target_r")),
            _optional_float(out.get("raw_target_r")),
            _optional_float(out.get("target_r")),
        )
        # The frozen walker disables the ceiling on a falsy target
        # (`target_r if target_r else close_mark_r`); mirror that exactly.
        if target is not None and target != 0.0
    ]
    if not targets:
        out["close_mark_clamped"] = False
        out["close_mark_clamp_semantics_status"] = "not_clamped_no_target_bound"
        return
    if max(targets) - min(targets) <= 1e-9:
        clamped = mark > targets[0]
        out["close_mark_clamped"] = clamped
        out["close_mark_clamp_semantics_status"] = (
            "clamped_at_target_ceiling" if clamped else "not_clamped"
        )
        return
    if mark <= min(targets):
        # Every candidate pairing agrees the ceiling did not bind.
        out["close_mark_clamped"] = False
        out["close_mark_clamp_semantics_status"] = "not_clamped"
        return
    out["close_mark_clamped"] = None
    out["close_mark_clamp_semantics_status"] = (
        "target_pairing_ambiguous_not_derivable"
    )


def _repair_selector_semantics(out: dict[str, Any]) -> None:
    raw_action = str(out.get("selector_action") or "").strip()
    effective_action = str(out.get("effective_selector_action") or "").strip()
    reason = str(out.get("selector_reason") or "").strip()
    status = str(out.get("scheduler_materialization_status") or "").strip()
    if not any((raw_action, effective_action, reason, status)):
        return
    replay_softened = bool(
        (
            raw_action == "reject"
            and effective_action == "open-reduced-risk"
            and status == "scheduler_option_materialized"
        )
        or reason == "source_bound_router_refusal_open_reduced_materialized_for_replay"
    )
    out["selector_router_reinjection_applied"] = replay_softened
    if not replay_softened:
        return
    out["selector_router_reinjection_policy_status"] = (
        "deliberate_replay_softening"
    )
    out["selector_router_reinjection_authority"] = (
        "selector_reject_open_reduced_materialization_detail"
    )
    out["selector_router_reinjection_scope"] = (
        "local_replay_only_no_broker_authority"
    )
    out["selector_router_reinjection_original_action"] = raw_action or "reject"
    out["selector_router_reinjection_materialized_action"] = (
        effective_action or "open-reduced-risk"
    )


def _authority_failures(out: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    failure_keys = (
        "package_new_entry_authority_failures",
        "signed_package_new_entry_authority_failures",
        "scheduler_materialization_exact_member_axis_provisional_authority_failures",
    )
    for key in failure_keys:
        failures.extend(_text_list(out.get(key)))
    for key in (
        "ultimate_candidate_package_reduce_risk_authority",
        "ultimate_candidate_package_open_reduced_risk_authority",
    ):
        authority = out.get(key)
        if not isinstance(authority, Mapping):
            continue
        for failure_key in (
            "package_new_entry_authority_failures",
            "failures",
        ):
            failures.extend(_text_list(authority.get(failure_key)))
    return list(dict.fromkeys(failures))


def _repair_authority_gate_semantics(out: dict[str, Any]) -> None:
    reason = str(out.get("miss_reason") or "")
    failures = _authority_failures(out)
    if failures:
        out["package_authority_failures"] = failures
        out["package_authority_failure_capture_status"] = "captured"

    if "package_positive_reduce_risk_signed_authority_invalid" in reason:
        out["package_authority_gate_status"] = "blocked_signature_invalid"
        if not failures:
            out["package_authority_failures"] = []
            out["package_authority_failure_capture_status"] = (
                "missing_failure_payload"
            )
            out["package_authority_capture_requirement"] = (
                "emit package_new_entry_authority_failures and immutable-payload "
                "validation failures on the missed row"
            )
    elif "numeric_disagreement_open_reduced_risk_disabled_by_config" in reason:
        out["package_authority_gate_status"] = (
            "intentional_repaired_profile_demotion"
        )
        out["package_authority_effective_config_value"] = False
    elif "signed_package_new_entry_authority_surface_missing" in reason:
        out["package_authority_gate_status"] = "blocked_authority_surface_missing"
        if not failures:
            out["package_authority_failures"] = [
                "signed_package_new_entry_authority_surface_missing"
            ]
            out["package_authority_failure_capture_status"] = (
                "captured_in_reason_only"
            )


def _repair_ev_semantics(out: dict[str, Any]) -> None:
    ev = _optional_float(
        _first_present(
            out.get("candidate_ev_r"),
            out.get("ev_r"),
            out.get("expectancy_r"),
        )
    )
    if ev is not None:
        out["ev_cost_context_status"] = (
            "indirect_probability_cost_sensitivity_present_"
            "direct_ev_cost_term_unwired"
        )
        out["ev_probability_cost_sensitivity_status"] = (
            "cost_affects_base_probability_and_source_weights"
        )
        out["ev_direct_cost_term_status"] = (
            "probability_context_omits_cost_r_so_debate_cost_r_is_zero"
        )
        out["candidate_ev_r_cost_scope"] = (
            "cost_sensitive_probability_ev_before_explicit_pretrade_"
            "cost_subtraction"
        )
        out["authoritative_candidate_ev_r"] = None
        cost = _optional_float(
            _first_present(out.get("cost_r"), out.get("expected_cost_r"))
        )
        expected_net = _optional_float(out.get("expected_net_r"))
        if (
            cost is not None
            and expected_net is not None
            and math.isclose(expected_net, ev - cost, rel_tol=0.0, abs_tol=1e-8)
        ):
            out["expected_net_r_cost_scope"] = (
                "cost_sensitive_probability_ev_minus_recorded_"
                "pretrade_cost_once"
            )

    target = _optional_float(
        _first_present(
            out.get("policy_target_r"),
            out.get("raw_target_r"),
            out.get("risk_reward_ratio"),
        )
    )
    if ev is not None and target is not None:
        out["execution_policy_target_r"] = target
        if math.isclose(target, 2.0, rel_tol=0.0, abs_tol=1e-9):
            out["ev_reward_r_assumed_at_probability_stage"] = 1.5
            out["ev_geometry_alignment_status"] = (
                "pre_rewrite_1p5r_ev_vs_2p0r_execution_geometry"
            )
        else:
            out["ev_geometry_alignment_status"] = (
                "probability_stage_reward_geometry_not_captured"
            )

    if out.get("origin_family") not in (None, ""):
        out["origin_family_hash_authority_status"] = (
            "deterministic_name_hash_heuristic_non_authoritative"
        )
        out["authoritative_origin_family_hash_component"] = None

    confidence = _optional_float(
        _first_present(
            out.get("candidate_confidence"),
            out.get("confidence"),
            out.get("scheduler_confidence"),
        )
    )
    if (
        confidence is not None
        and math.isclose(confidence, 0.55, rel_tol=0.0, abs_tol=1e-12)
        and bool(
            out.get("confidence_default_applied")
            or out.get("confidence_missing_degraded_default_applied")
        )
    ):
        out["candidate_confidence_authority_status"] = (
            "missing_confidence_constant_default_non_authoritative"
        )
        out["authoritative_candidate_confidence"] = None
    elif confidence is not None:
        out["candidate_confidence_authority_status"] = (
            "confidence_source_not_validated_by_capture_layer"
        )
        out["authoritative_candidate_confidence"] = confidence

    execution_fill = _optional_float(out.get("execution_fill_probability"))
    fill_source = str(out.get("execution_fill_probability_source") or "")
    marketable_template = bool(
        execution_fill is not None
        and math.isclose(execution_fill, 0.92, rel_tol=0.0, abs_tol=1e-12)
        and (
            out.get("limit_marketable_at_decision") is True
            or "marketable" in fill_source
            or fill_source in {"", "predecision_limit_fillability"}
        )
    )
    if marketable_template:
        out["execution_fill_probability_authority_status"] = (
            "marketable_limit_constant_template_non_authoritative"
        )
        out["execution_fill_probability_measurement_status"] = (
            "modeled_template_not_measured"
        )
        out["authoritative_execution_fill_probability"] = None
    elif execution_fill is not None:
        out["execution_fill_probability_authority_status"] = (
            "geometry_model_probability_not_empirical_measurement"
        )
        out["execution_fill_probability_measurement_status"] = (
            "modeled_not_measured"
        )
        out["authoritative_execution_fill_probability"] = None


def _repair_identity_and_aliases(out: dict[str, Any]) -> None:
    candidate_id = str(out.get("candidate_id") or "").strip()
    decision_time = str(
        _first_present(
            out.get("decision_time_utc"),
            out.get("candidate_instance_time_utc"),
        )
        or ""
    ).strip()
    expected = f"{candidate_id}@@{decision_time}" if candidate_id and decision_time else ""
    declared = str(out.get("canonical_replay_candidate_instance_key") or "").strip()
    out["candidate_identity_join_contract"] = (
        "candidate_id_plus_decision_time_utc"
    )
    if declared and expected and declared != expected:
        out["candidate_identity_join_status"] = "declared_composite_key_conflict"
    elif declared:
        out["candidate_identity_join_status"] = "declared_composite_key_valid"
    elif expected:
        out["canonical_replay_candidate_instance_key"] = expected
        out["candidate_identity_join_status"] = "derived_composite_key"
    else:
        out["candidate_identity_join_status"] = "composite_identity_incomplete"

    if out.get("final_blocker_class") in (None, ""):
        blocker = out.get(
            "missed_package_replay_order_executable_final_blocker_class"
        )
        if blocker not in (None, ""):
            out["final_blocker_class"] = blocker


def normalize_evidence_row(
    row: Mapping[str, Any],
    *,
    row_kind: str | None = None,
) -> dict[str, Any]:
    """Return a semantics-correct, backward-compatible evidence row.

    Existing numeric and outcome fields are retained.  Where a legacy field is
    semantically false (for example an outcome stored as a mark source), its
    original value is copied to a ``legacy_*`` field before the canonical field
    is repaired.
    """

    out = dict(row)
    out["decision_semantics_schema"] = SCHEMA
    _flatten_cost_packet(out)
    _repair_identity_and_aliases(out)
    _repair_quote_semantics(out)
    _repair_cost_semantics(out)
    _repair_slippage_semantics(out)
    _repair_terminal_semantics(out, row_kind=row_kind)
    _stamp_exit_vocabulary_layers(out)
    _stamp_close_mark_clamp_semantics(out)
    _repair_selector_semantics(out)
    _repair_authority_gate_semantics(out)
    _repair_ev_semantics(out)
    return out


def authoritative_cost_value(row: Mapping[str, Any]) -> float | None:
    """Return the cost value safe for cost claims after semantic repair."""

    normalized = normalize_evidence_row(row)
    status, number = cost_number(normalized.get("authoritative_cost_r"))
    return number if status == "valid" else None


__all__ = [
    "COST_COMPONENT_FIELDS",
    "COST_COMPONENT_TOLERANCE_R",
    "HISTORICAL_SPREAD_FLOOR_TEMPLATES_R",
    "LEVEL_TERMINAL_OUTCOMES",
    "REPAIR_PROVENANCE_FIELDS",
    "SCHEMA",
    "SEMANTIC_FIELDS",
    "TRUSTED_COMMISSION_REPAIR_SOURCE",
    "assess_cost_components",
    "authoritative_cost_value",
    "cost_component_capture_evidence_from_packet",
    "cost_component_sum",
    "cost_number",
    "normalize_evidence_row",
    "publish_cost_assessment",
]
