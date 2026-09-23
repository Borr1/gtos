from __future__ import annotations

from datetime import timedelta

import pytest

from src.research import moonshot_scheduler_v4_best_trade_allocator as scheduler
from src.research_infra import v4_timewarp_simulated_live_research_loop as timewarp


def _selector_packet(reason: str, action: str = "reduce-risk") -> dict:
    return {
        "action": action,
        "reason": reason,
        "final_risk_pct": 0.25,
        "component_scores": {
            "broker_net_admission_ev_r": 0.72,
            "broker_net_selected_cell": {
                "broker_net_expectancy_r": 0.72,
                "stress_expectancy_r": 0.31,
            },
            "ultimate_candidate_package": {
                "source_bound_package_candidate_use_allowed": True,
                "admission_sleeve_match_count": 1,
                "matched_sleeve_count": 2,
                "admission_member_axis_match_count": 1,
                "matched_member_axis_count": 1,
                "matched_member_axis_ids": ["fixture-selector-member-axis"],
                "matched_sleeves": [
                    {
                        "sleeve_id": "fixture-sleeve",
                        "combined_source_bound_signal_r": 12.5,
                    }
                ],
            },
        },
    }


def _cost_packet(status: str = "PASSED") -> dict:
    return {
        "status": status,
        "authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "candidate_cost_r_fallback_is_authority": False,
        "total_cost_r": 0.05,
    }


def _add_strict_limit_fillability(row: dict, fill_probability: float | None = None) -> dict:
    fill = (
        fill_probability
        if fill_probability is not None
        else row.get("predecision_limit_fillability_probability")
        or row.get("limit_fillability_probability")
        or row.get("execution_fill_probability")
        or row.get("candidate_fill_probability")
        or row.get("fill_probability")
    )
    if fill in (None, ""):
        return row
    row["predecision_limit_fillability_probability"] = fill
    row["limit_fillability_probability"] = fill
    row["execution_fill_probability"] = fill
    row.setdefault(
        "execution_fill_probability_source",
        "predecision_limit_fillability.fill_probability",
    )
    fillability = row.get("predecision_limit_fillability")
    fillability = dict(fillability) if isinstance(fillability, dict) else {}
    fillability.setdefault("fill_probability", fill)
    safe_source_boundary = "closed_m15_predecision_asof_no_postdecision_path"
    fillability.setdefault(
        "source_boundary",
        safe_source_boundary,
    )
    decision_time = timewarp.parse_utc(
        row.get("decision_time_utc") or row.get("asof_utc")
    )
    source_time = (
        fillability.get("current_price_source_time_utc")
        or row.get("execution_fill_probability_source_time_utc")
    )
    if source_time in (None, "") and decision_time is not None:
        source_time = (decision_time - timedelta(minutes=15)).isoformat()
        fillability["current_price_source_time_utc"] = source_time
    source_boundary = str(
        fillability.get("current_price_source_boundary")
        or fillability.get("source_boundary")
        or row.get("execution_fill_probability_source_boundary")
        or safe_source_boundary
    )
    row["execution_fill_probability_source_boundary"] = source_boundary
    row["predecision_limit_fillability_source_boundary"] = source_boundary
    quality = row.get("candidate_decision_quality")
    quality = dict(quality) if isinstance(quality, dict) else {}
    quality["execution_fill_probability_source_boundary"] = source_boundary
    if source_time not in (None, ""):
        row["execution_fill_probability_source_time_utc"] = str(source_time)
        row["predecision_limit_fillability_source_time_utc"] = str(source_time)
        quality["execution_fill_probability_source_time_utc"] = str(source_time)
    row["candidate_decision_quality"] = quality
    row["predecision_limit_fillability"] = fillability
    sources = row.get("candidate_decision_quality_field_sources")
    sources = dict(sources) if isinstance(sources, dict) else {}
    sources["fill_probability"] = (
        "fixture.predecision.predecision_limit_fillability_probability"
    )
    sources["limit_fillability_probability"] = (
        "predecision_limit_fillability.fill_probability"
    )
    sources["execution_fill_probability"] = (
        "predecision_limit_fillability.fill_probability"
    )
    row["candidate_decision_quality_field_sources"] = sources
    return row


def _ensure_fixture_quality_aliases(row: dict) -> dict:
    expected_net_r = (
        row.get("expected_net_r")
        if row.get("expected_net_r") not in (None, "")
        else row.get("candidate_expected_net_r")
        if row.get("candidate_expected_net_r") not in (None, "")
        else row.get("scheduler_expected_net_r")
    )
    probability = (
        row.get("probability")
        if row.get("probability") not in (None, "")
        else row.get("candidate_probability")
        if row.get("candidate_probability") not in (None, "")
        else row.get("scheduler_probability")
    )
    confidence = (
        row.get("confidence")
        if row.get("confidence") not in (None, "")
        else row.get("candidate_confidence")
        if row.get("candidate_confidence") not in (None, "")
        else row.get("scheduler_confidence")
    )
    source_completeness = (
        row.get("source_completeness")
        if row.get("source_completeness") not in (None, "")
        else row.get("candidate_source_completeness")
    )
    if expected_net_r not in (None, ""):
        row.setdefault("expected_net_r", expected_net_r)
        row.setdefault("candidate_expected_net_r", expected_net_r)
    if probability not in (None, ""):
        row.setdefault("probability", probability)
        row.setdefault("candidate_probability", probability)
    if confidence not in (None, ""):
        row.setdefault("confidence", confidence)
        row.setdefault("candidate_confidence", confidence)
        row.setdefault("scheduler_confidence", confidence)
    if source_completeness not in (None, ""):
        row.setdefault("source_completeness", source_completeness)
        row.setdefault("candidate_source_completeness", source_completeness)
    row.setdefault("source_completeness_status", "source_completeness_present")
    sources = row.get("candidate_decision_quality_field_sources")
    sources = dict(sources) if isinstance(sources, dict) else {}
    for key, source in (
        ("expected_net_r", "fixture.predecision.expected_net_r"),
        ("probability", "fixture.predecision.probability"),
        ("confidence", "fixture.predecision.confidence"),
        ("source_completeness", "fixture.predecision.source_completeness"),
    ):
        sources.setdefault(key, source)
    row["candidate_decision_quality_field_sources"] = sources
    row.setdefault(
        "candidate_decision_quality_source_boundary",
        "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields",
    )
    row.setdefault("candidate_decision_quality_alias_status", "exact_materialized")
    return row


def _ensure_exact_package_member_axis_identity(row: dict) -> dict:
    candidate_id = str(row.get("candidate_id") or "fixture-candidate").strip()
    stable_id = f"fixture-member-axis:{candidate_id}"
    member_axis_ids = row.get("ultimate_package_matched_member_axis_ids")
    if not isinstance(member_axis_ids, list) or not member_axis_ids:
        member_axis_ids = [stable_id]
        row["ultimate_package_matched_member_axis_ids"] = member_axis_ids
    row.setdefault("matched_stable_member_axis_ids", list(member_axis_ids))
    row.setdefault("ultimate_package_matched_member_axis_count", len(member_axis_ids))
    row.setdefault("ultimate_package_admission_member_axis_match_count", 1)
    return row


def _add_exact_member_axis_execution_evidence(
    row: dict,
    *,
    source_bound_r: float = 12.5,
) -> dict:
    _ensure_exact_package_member_axis_identity(row)
    row["ultimate_package_member_axis_evidence_class"] = (
        timewarp.EXACT_MEMBER_AXIS_EXECUTION_EVIDENCE_CLASS
    )
    row["ultimate_package_member_axis_match_status"] = (
        timewarp.EXACT_MEMBER_AXIS_CURRENT_MATCH_STATUS
    )
    row["ultimate_package_member_axis_source_bound_signal_r_sum"] = source_bound_r
    row["ultimate_package_member_axis_max_source_bound_signal_r"] = source_bound_r
    row.setdefault("source_bound_package_candidate_use_allowed", True)
    row.setdefault("ultimate_package_source_bound_candidate_use_allowed", True)
    return row


def _sign_package_new_entry_authority(
    row: dict,
    *,
    action_intent: str = "new_position",
    config: dict | None = None,
) -> dict:
    _ensure_fixture_quality_aliases(row)
    _ensure_exact_package_member_axis_identity(row)
    row.setdefault("decision_time_utc", "2026-05-15T07:45:00+00:00")
    row.setdefault(
        "source_boundary",
        "predecision_fixture_quality_and_order_authority_no_outcome_fields",
    )
    row.setdefault("source_bound_package_candidate_use_allowed", True)
    row.setdefault("ultimate_package_source_bound_candidate_use_allowed", True)
    row.setdefault("package_replay_executable_candidate_use_allowed", True)
    row.setdefault(
        "package_replay_executable_candidate_use_allowed_reason",
        "fixture_signed_package_candidate_executable",
    )
    row.setdefault("package_replay_order_executable_candidate_use_allowed", True)
    row.setdefault(
        "package_replay_order_executable_candidate_use_allowed_reason",
        "fixture_signed_order_executable_allowed",
    )
    row.setdefault(
        "package_replay_order_executable_authority_source",
        "fixture_signed_package_new_entry_authority",
    )
    candidate_id = str(row.get("candidate_id") or "").strip()
    decision_time = str(
        row.get("decision_time_utc")
        or row.get("candle_close_utc")
        or row.get("source_candle_time_utc")
        or ""
    ).strip()
    if candidate_id:
        row.setdefault("candidate_id_source", "candidate_id")
    if candidate_id and decision_time:
        instance_key = f"{candidate_id}@@{decision_time}"
        row.setdefault("canonical_replay_candidate_instance_key", instance_key)
        row.setdefault("source_bound_replay_candidate_instance_key", instance_key)
        row.setdefault("candidate_instance_identity_status", "materialized")
    entry_fill = (
        row.get("entry_quality_fill_probability")
        or row.get("candidate_fill_probability")
        or row.get("fill_probability")
        or row.get("execution_fill_probability")
    )
    execution_fill = (
        row.get("predecision_limit_fillability_probability")
        or row.get("limit_fillability_probability")
        or row.get("execution_fill_probability")
        or entry_fill
    )
    if entry_fill not in (None, ""):
        row.setdefault("entry_quality_fill_probability", entry_fill)
        row.setdefault("candidate_fill_probability", entry_fill)
    if execution_fill not in (None, ""):
        row.setdefault("predecision_limit_fillability_probability", execution_fill)
        row.setdefault("limit_fillability_probability", execution_fill)
        row.setdefault("execution_fill_probability", execution_fill)
        row.setdefault(
            "execution_fill_probability_source",
            "predecision_limit_fillability.fill_probability",
        )
        _add_strict_limit_fillability(row, execution_fill)
    row.setdefault("candidate_decision_quality_field_sources", {
        "expected_net_r": "fixture.predecision.expected_net_r",
        "probability": "fixture.predecision.probability",
        "confidence": "fixture.predecision.confidence",
        "fill_probability": (
            "fixture.predecision.predecision_limit_fillability_probability"
        ),
        "entry_quality_fill_probability": "fixture.predecision.entry_quality_fill_probability",
        "limit_fillability_probability": (
            "fixture.predecision.predecision_limit_fillability_probability"
        ),
        "execution_fill_probability": (
            "fixture.predecision.predecision_limit_fillability_probability"
        ),
        "source_completeness": "fixture.predecision.source_completeness",
    })
    row.setdefault(
        "candidate_decision_quality_source_boundary",
        "predecision_fixture_quality_and_order_fillability_no_outcome_fields",
    )
    row.setdefault("candidate_decision_quality_alias_status", "exact_materialized")
    selector_action = str(row.get("selector_action") or "").strip()
    authority_field = (
        "ultimate_candidate_package_reduce_risk_authority"
        if selector_action == "reduce-risk"
        else "ultimate_candidate_package_open_reduced_risk_authority"
    )
    authority = dict(row.get(authority_field) or {})
    authority.setdefault("selector_reason", row.get("selector_reason"))
    authority.setdefault("authority_source", "fixture_signed_package_new_entry_authority")
    authority.setdefault(
        "source_boundary",
        "predecision_fixture_quality_and_order_authority_no_outcome_fields",
    )
    row[authority_field] = authority
    signed = scheduler.stamp_package_new_entry_authority(
        row,
        selector_action=selector_action,
        selector_reason=row.get("selector_reason"),
        authority=authority,
        action_intent=action_intent,
        config=config,
    )
    row[authority_field] = signed
    row[scheduler.PACKAGE_NEW_ENTRY_AUTHORITY_HASH_FIELD] = signed[
        scheduler.PACKAGE_NEW_ENTRY_AUTHORITY_HASH_FIELD
    ]
    row.update(timewarp.package_new_entry_authority_attribution_fields(signed))
    return row


def _attach_signed_open_reduced_authority(
    row: dict,
    selector_packet: dict,
    *,
    reason: str,
    decision_time: str,
    action_intent: str = "new_position",
    authority_family: str = "fill_floor_softening",
    authority_overrides: dict | None = None,
    config: dict | None = None,
    bind_selected_policy_calibration_hash: bool = False,
) -> dict:
    _ensure_fixture_quality_aliases(row)
    _ensure_exact_package_member_axis_identity(row)
    candidate_id = row["candidate_id"]
    instance_key = f"{candidate_id}@@{decision_time}"
    row.setdefault("decision_time_utc", decision_time)
    row.setdefault("canonical_replay_candidate_instance_key", instance_key)
    row.setdefault("source_bound_replay_candidate_instance_key", instance_key)
    row.setdefault("candidate_instance_identity_status", "materialized")
    row.setdefault("source_bound_package_candidate_use_allowed", True)
    row.setdefault("ultimate_package_source_bound_candidate_use_allowed", True)
    row.setdefault("source_completeness", 1.0)
    row.setdefault("source_completeness_status", "source_completeness_present")
    row.setdefault("pretrade_cost_packet_status", "PASSED")
    row.setdefault("cost_authority", "broker_calibrated_replay_cost")
    row.setdefault("cost_source_gap_status", "source_bound_cost_authority_present")
    row.setdefault("candidate_cost_r_fallback_is_authority", False)
    row.setdefault("package_replay_order_executable_candidate_use_allowed", True)
    row.setdefault(
        "package_replay_order_executable_candidate_use_allowed_reason",
        "fixture_signed_order_executable_allowed",
    )
    row.setdefault(
        "package_replay_order_executable_authority_source",
        "fixture_signed_package_new_entry_authority",
    )
    row.setdefault(
        "source_boundary",
        "predecision_fixture_quality_and_order_authority_no_outcome_fields",
    )
    row.setdefault("candidate_decision_quality_field_sources", {
        "expected_net_r": "fixture.predecision.expected_net_r",
        "probability": "fixture.predecision.probability",
        "fill_probability": (
            "fixture.predecision.predecision_limit_fillability_probability"
        ),
        "entry_quality_fill_probability": "fixture.predecision.entry_quality_fill_probability",
        "limit_fillability_probability": (
            "fixture.predecision.predecision_limit_fillability_probability"
        ),
        "execution_fill_probability": (
            "fixture.predecision.predecision_limit_fillability_probability"
        ),
        "source_completeness": "fixture.predecision.source_completeness",
    })
    row.setdefault(
        "candidate_decision_quality_source_boundary",
        "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields",
    )
    row.setdefault("candidate_decision_quality_alias_status", "exact_materialized")
    entry_fill = (
        row.get("entry_quality_fill_probability")
        or row.get("candidate_fill_probability")
        or row.get("fill_probability")
        or row.get("execution_fill_probability")
    )
    execution_fill = (
        row.get("predecision_limit_fillability_probability")
        or row.get("limit_fillability_probability")
        or row.get("execution_fill_probability")
        or entry_fill
    )
    if entry_fill not in (None, ""):
        row.setdefault("entry_quality_fill_probability", entry_fill)
        row.setdefault("candidate_fill_probability", entry_fill)
    if execution_fill not in (None, ""):
        row.setdefault("predecision_limit_fillability_probability", execution_fill)
        row.setdefault("limit_fillability_probability", execution_fill)
        row.setdefault("execution_fill_probability", execution_fill)
        row.setdefault(
            "execution_fill_probability_source",
            "predecision_limit_fillability.fill_probability",
        )
        _add_strict_limit_fillability(row, execution_fill)
    row.setdefault("selected_policy_for_expected_net_r", "momentum_exhaustion")
    row.setdefault(
        "selected_policy_expected_net_calibration_status",
        "calibrated",
    )
    row.setdefault("selected_policy_expected_net_calibrated", True)
    row.setdefault(
        "selected_policy_expected_net_calibration_source",
        "selected_policy_replay_calibration_packet",
    )
    row.setdefault(
        "selected_policy_expected_net_calibration_source_boundary",
        "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields",
    )
    if bind_selected_policy_calibration_hash:
        calibration_hash = timewarp.stable_sha256(
            {
                "selected_policy": row["selected_policy_for_expected_net_r"],
                "expected_net_r": row["expected_net_r"],
                "expected_net_r_source": row[
                    "selected_policy_expected_net_calibration_source"
                ],
                "source_boundary": row[
                    "selected_policy_expected_net_calibration_source_boundary"
                ],
                "status": row["selected_policy_expected_net_calibration_status"],
                "evidence_class": timewarp.SIM_EVIDENCE_CLASS,
                "calibration_source_class": (
                    "predecision_selected_policy_expected_net_runtime_proxy"
                ),
            }
        )
        row.setdefault("selected_policy_expected_net_assumption_hash", calibration_hash)
        row.setdefault("selected_policy_expected_net_calibration_hash", calibration_hash)
    authority = {
        "applies": True,
        "allowed": True,
        "authority_family": authority_family,
        "selector_reason": reason,
        "current_config_allowed": True,
        "ultimate_package_soft_admission_override_allowed": True,
        "source_bound_candidate_use_allowed_now": True,
        "broker_cost_passed_for_package_router": True,
        "positive_predecision_package_edge": True,
        "source_boundary": (
            "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
        ),
    }
    if authority_overrides:
        authority.update(authority_overrides)
    router_floors = authority.get("source_bound_router_refusal_materialization_floors")
    if isinstance(router_floors, dict):
        row["source_bound_router_refusal_materialization_floors"] = dict(
            router_floors
        )
    signed = scheduler.stamp_package_new_entry_authority(
        row,
        selector_action="open-reduced-risk",
        selector_reason=reason,
        authority=authority,
        action_intent=action_intent,
        config=config,
    )
    row["ultimate_candidate_package_open_reduced_risk_authority"] = signed
    row["package_open_reduced_authority_allowed"] = True
    row["package_open_reduced_authority_family"] = authority_family
    row.update(timewarp.package_new_entry_authority_attribution_fields(signed))
    selector_packet["component_scores"][
        "ultimate_candidate_package_open_reduced_risk_authority"
    ] = signed
    selector_packet["component_scores"][
        "selector_reduced_risk_new_position_signed_authority"
    ] = signed
    return signed


def _open_reduced_selector_packet(
    reason: str,
    *,
    authority_family: str = "router_refusal_softening",
) -> dict:
    packet = _selector_packet(reason, action="open-reduced-risk")
    packet["component_scores"][
        "ultimate_candidate_package_open_reduced_risk_authority"
    ] = {
        "applies": True,
        "allowed": True,
        "authority_family": authority_family,
        "selector_reason": reason,
    }
    return packet


def test_scheduler_lifecycle_action_aliases_are_canonicalized() -> None:
    assert scheduler._normalize_action_intent("close-and-reverse") == "close_and_reverse"
    assert scheduler._normalize_action_intent("replace pending") == "replace_pending"
    assert scheduler._normalize_action_intent("cancel-pending") == "cancel_pending"
    assert timewarp.normalize_scheduler_action_intent("hold-existing") == "hold_existing"
    assert timewarp.normalize_scheduler_action_intent("replace pending") == "replace_pending"
    assert timewarp.normalize_scheduler_action_intent("cancel") == "cancel_pending"
    assert timewarp.normalize_scheduler_action_intent("no_trade_duplicate") is None
    assert (
        timewarp.scheduler_terminal_no_new_order_action("no_trade_duplicate")
        == "no_trade_duplicate"
    )
    assert (
        timewarp.scheduler_terminal_no_new_order_action(
            "invalid_action_intent:no_trade_duplicate"
        )
        == "no_trade_duplicate"
    )
    assert timewarp.selector_action_allows_scheduler_action(
        "open-reduced-risk",
        "replace-pending",
    )
    fields = timewarp.scheduler_lifecycle_authority_alias_fields(
        {
            "scheduler_materialization_action_intent": "new_position",
            "same_symbol_lifecycle_action": "replace_pending",
            "lifecycle_action": "replace_pending",
            "package_lifecycle_root_authority": {
                "applies": True,
                "allowed": True,
                "root_action": "replace_pending",
                "effective_action_intent": "replace_pending",
            },
        }
    )
    assert fields["scheduler_materialization_action_intent"] == "replace_pending"
    assert fields["effective_action_intent"] == "replace_pending"
    assert fields["scheduler_materialization_original_action_intent"] == "new_position"


def test_signed_scheduler_payload_binds_execution_fill_probability_source() -> None:
    reason = "ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay"

    def signed_authority(fill_source: str) -> dict:
        row = {
            "candidate_id": "candidate-fill-source-hash",
            "decision_time_utc": "2026-05-15T07:45:00+00:00",
            "selector_action": "open-reduced-risk",
            "selector_reason": reason,
            "action_intent": "new_position",
            "expected_net_r": 0.91,
            "probability": 0.78,
            "confidence": 0.82,
            "fill_probability": 0.81,
            "execution_fill_probability": 0.81,
            "execution_fill_probability_source": fill_source,
            "execution_fill_probability_source_time_utc": (
                "2026-05-15T07:30:00+00:00"
            ),
            "execution_fill_probability_source_boundary": (
                "asof_candidate_fields_only_no_postdecision_path"
            ),
            "source_completeness": 1.0,
            "source_completeness_status": "source_completeness_present",
            "source_bound_package_candidate_use_allowed": True,
            "ultimate_package_source_bound_candidate_use_allowed": True,
            "pretrade_cost_packet_status": "PASSED",
            "cost_authority": "broker_calibrated_replay_cost",
            "cost_source_gap_status": "source_bound_cost_authority_present",
            "candidate_cost_r_fallback_is_authority": False,
            "ultimate_candidate_package_open_reduced_risk_authority": {
                "applies": True,
                "allowed": True,
                "authority_family": "fill_floor_softening",
            },
        }
        _sign_package_new_entry_authority(row)
        return row["ultimate_candidate_package_open_reduced_risk_authority"]

    passive_limit = signed_authority("predecision_limit_fillability")
    alternate_source = signed_authority("predecision_pending_fillability")

    assert passive_limit["package_new_entry_authority_payload"][
        "execution_fill_probability_source"
    ] == "predecision_limit_fillability"
    assert alternate_source["package_new_entry_authority_payload"][
        "execution_fill_probability_source"
    ] == "predecision_pending_fillability"
    assert passive_limit[scheduler.PACKAGE_NEW_ENTRY_AUTHORITY_HASH_FIELD] != (
        alternate_source[scheduler.PACKAGE_NEW_ENTRY_AUTHORITY_HASH_FIELD]
    )


def test_ledger_normalization_strips_provisional_markers_recursively() -> None:
    marker = timewarp.PACKAGE_NEW_ENTRY_AUTHORITY_PROVISIONAL_MARKER
    row = {
        marker: True,
        "nested": {
            marker: True,
            "items": [{marker: True}],
        },
    }

    normalized = timewarp.normalize_package_new_entry_authority_ledger_row(row)

    assert marker not in normalized
    assert marker not in normalized["nested"]
    assert marker not in normalized["nested"]["items"][0]
    assert normalized["package_new_entry_authority_provisional_marker_strip_count"] == 3
    assert normalized["package_new_entry_authority_provisional_marker_strip_status"] == (
        "stripped_at_ledger_serialization_boundary"
    )


def test_ledger_normalization_finalizes_concrete_blocked_authority_false() -> None:
    base = {
        "source_bound_package_candidate_use_allowed": True,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "package_replay_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed": True,
        "replay_candidate_use_allowed_now": True,
        "ledger_namespace_synthesized_executable_candidate_use_allowed": True,
        "package_replay_order_executable_candidate_use_allowed": True,
        "ultimate_package_effective_executable_authority_allowed": True,
    }
    blocked_rows = [
        {
            **base,
            "package_replay_executable_candidate_use_allowed": False,
            "package_replay_executable_candidate_use_allowed_reason": (
                "broker_cost_packet_refused"
            ),
        },
        {
            **base,
            "package_replay_order_executable_transfer_status": "final_blocked",
            "package_replay_order_executable_final_blocker_reason": (
                "broker_cost_packet_refused"
            ),
        },
    ]

    for row in blocked_rows:
        normalized = timewarp.normalize_package_new_entry_authority_ledger_row(row)
        assert all(
            normalized[field] is False
            for field in (
                "package_replay_candidate_use_allowed",
                "package_replay_executable_candidate_use_allowed",
                "package_replay_order_executable_candidate_use_allowed",
                "replay_candidate_use_allowed_now",
                "ledger_namespace_synthesized_executable_candidate_use_allowed",
                "ultimate_package_effective_executable_authority_allowed",
                "executable_finalized",
                "missed_row_executable_finalized",
            )
        )
        assert normalized[
            "package_replay_order_executable_candidate_use_allowed_pre_finalization"
        ] is True
        assert normalized[
            "package_replay_effective_executable_alias_reconciliation_status"
        ] == (
            "final_blocked_aliases_demoted_preserving_signed_predecision_envelope"
        )
        assert normalized["ultimate_package_effective_executable_authority_allowed"] is False
        assert normalized["ultimate_package_effective_executable_authority_status"] == (
            "finalized_non_executable_diagnostic"
        )
        assert normalized[
            "ultimate_package_pre_finalization_executable_authority_allowed"
        ] is True


def test_timewarp_rederives_only_source_or_cost_gap_package_false_reasons() -> None:
    for reason in (
        "broker_cost_packet_status_missing",
        "broker_cost_source_gap_status_missing",
        "source_completeness_below_floor:0.900000",
        "source_completeness_status_source_gap",
        (
            "explicit_package_replay_executable_rejected:"
            "candidate_decision_quality_provenance_missing:"
            "candidate_decision_quality_alias_status:partially_materialized"
        ),
        (
            "explicit_package_replay_executable_rejected:"
            "candidate_decision_quality_provenance_missing:"
            "confidence_source_inferred:scheduler_default_missing_confidence_0_55"
        ),
        "source_bound_package_replay_not_allowed",
    ):
        assert timewarp.explicit_package_false_reason_can_be_rederived(reason)
    for reason in (
        "missing_explicit_package_executable_authority",
        "package_executable_authority_missing_or_false",
        "explicit_package_replay_executable_authority_false",
        "selector_reduce_risk_not_new_entry_authority",
    ):
        assert not timewarp.explicit_package_false_reason_can_be_rederived(reason)


def test_package_replay_row_missing_lifecycle_action_is_diagnostic_not_new_entry(
    monkeypatch,
) -> None:
    captured = {}

    def fake_allocate(window, config, *, raw_config=None):
        captured["window"] = window
        return {"selected_candidate_id": None, "selected_candidate_ids": [], "option_trace": []}

    monkeypatch.setattr(timewarp, "allocate_decision_window", fake_allocate)
    candidate = {
        "candidate_id": "candidate-missing-package-action",
        "symbol": "XAUUSD",
        "side": "LONG",
        "risk_reward_ratio": 2.0,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "candidate_expected_net_r": 0.91,
        "probability": 0.78,
        "confidence": 0.82,
        "candidate_confidence": 0.82,
        "scheduler_confidence": 0.82,
        "fill_probability": 0.32,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "fixture.predecision.expected_net_r",
            "probability": "fixture.predecision.probability",
            "confidence": "fixture",
            "fill_probability": "fixture.predecision.fill_probability",
            "source_completeness": "fixture.predecision.source_completeness",
        },
        "candidate_decision_quality_alias_status": "exact_materialized",
        "candidate_decision_quality_source_boundary": "predecision_fixture",
        "source_window_complete": True,
    }
    packets = {
        "candidate-missing-package-action": {
            "selector_packet": _open_reduced_selector_packet(
                "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk",
            ),
            "probability_packet": {
                "theses": [{"action": "long", "probability": 0.80, "EV": 0.96}]
            },
            "selector_event": {
                "predecision_limit_fillability": {"fill_probability": 0.55}
            },
            "pretrade_broker_net_cost_packet": _cost_packet(),
            "expected_net_r": 0.91,
        }
    }

    timewarp.materialize_scheduler_window(
        asof_utc="2025-06-11T08:15:00+00:00",
        candidates=[candidate],
        v4_packets=packets,
        config={"gtos_vnext_runtime": {}},
        open_positions=[
            {
                "exposure_id": "open:xau-long",
                "symbol": "XAUUSD",
                "side": "LONG",
                "risk_pct": 0.25,
            }
        ],
    )

    assert captured["window"]["candidates"] == []
    assert candidate["scheduler_materialization_skip_reason"] == (
        "invalid_scheduler_action_intent"
    )
    assert candidate.get("scheduler_materialization_action_intent") != "new_position"


def test_package_replay_cancel_replace_selector_spelling_is_not_defaulted_to_new_entry(
    monkeypatch,
) -> None:
    captured = {}

    def fake_allocate(window, config, *, raw_config=None):
        captured["window"] = window
        return {"selected_candidate_id": None, "selected_candidate_ids": [], "option_trace": []}

    monkeypatch.setattr(timewarp, "allocate_decision_window", fake_allocate)
    candidate = {
        "candidate_id": "candidate-cancel-replace-selector-spelling",
        "symbol": "XAUUSD",
        "side": "LONG",
        "selector_action": "cancel_replace",
        "risk_reward_ratio": 2.0,
        "source_bound_package_candidate_use_allowed": True,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "candidate_expected_net_r": 0.91,
        "probability": 0.78,
        "confidence": 0.82,
        "candidate_confidence": 0.82,
        "scheduler_confidence": 0.82,
        "fill_probability": 0.32,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "fixture.predecision.expected_net_r",
            "probability": "fixture.predecision.probability",
            "confidence": "fixture.predecision.confidence",
            "fill_probability": "fixture.predecision.fill_probability",
            "source_completeness": "fixture.predecision.source_completeness",
        },
        "candidate_decision_quality_alias_status": "exact_materialized",
        "candidate_decision_quality_source_boundary": "predecision_fixture",
        "source_window_complete": True,
    }

    timewarp.materialize_scheduler_window(
        asof_utc="2025-06-11T08:15:00+00:00",
        candidates=[candidate],
        v4_packets={
            "candidate-cancel-replace-selector-spelling": {
                "selector_packet": {"action": "cancel_replace"},
                "pretrade_broker_net_cost_packet": _cost_packet(),
                "expected_net_r": 0.91,
            }
        },
        config={"gtos_vnext_runtime": {}},
    )

    assert captured["window"]["candidates"] == []
    assert candidate["scheduler_materialization_skip_reason"] == (
        "selector_not_risk_bearing"
    )
    assert candidate.get("scheduler_materialization_action_intent") != "new_position"


def test_package_replay_order_policy_delay_queue_is_not_defaulted_to_new_entry(
    monkeypatch,
) -> None:
    captured = {}

    def fake_allocate(window, config, *, raw_config=None):
        captured["window"] = window
        return {"selected_candidate_id": None, "selected_candidate_ids": [], "option_trace": []}

    monkeypatch.setattr(timewarp, "allocate_decision_window", fake_allocate)
    candidate = {
        "candidate_id": "candidate-order-policy-delay",
        "symbol": "XAUUSD",
        "side": "LONG",
        "order_policy_action": "limit_first_delay_queue",
        "risk_reward_ratio": 2.0,
        "source_bound_package_candidate_use_allowed": True,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "candidate_expected_net_r": 0.91,
        "probability": 0.78,
        "confidence": 0.82,
        "candidate_confidence": 0.82,
        "scheduler_confidence": 0.82,
        "fill_probability": 0.32,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "fixture.predecision.expected_net_r",
            "probability": "fixture.predecision.probability",
            "confidence": "fixture.predecision.confidence",
            "fill_probability": "fixture.predecision.fill_probability",
            "source_completeness": "fixture.predecision.source_completeness",
        },
        "candidate_decision_quality_alias_status": "exact_materialized",
        "candidate_decision_quality_source_boundary": "predecision_fixture",
        "source_window_complete": True,
    }

    timewarp.materialize_scheduler_window(
        asof_utc="2025-06-11T08:15:00+00:00",
        candidates=[candidate],
        v4_packets={
            "candidate-order-policy-delay": {
                "selector_packet": {"action": "trade"},
                "pretrade_broker_net_cost_packet": _cost_packet(),
                "expected_net_r": 0.91,
            }
        },
        config={"gtos_vnext_runtime": {}},
    )

    assert captured["window"]["candidates"] == []
    assert candidate["scheduler_materialization_skip_reason"] == (
        "invalid_scheduler_action_intent"
    )
    assert candidate["scheduler_materialization_action_intent"] == (
        "invalid_action_intent:missing_scheduler_action_intent"
    )


def test_replay_loss_bucket_guard_blocks_only_uncalibrated_full_trade_class() -> None:
    limits = {
        "replay_loss_bucket_guard_enabled": True,
        "replay_loss_bucket_guard_policy_id": "unit_replay_calibration_guard",
        "replay_loss_bucket_guard_rules": [
            {
                "enabled": True,
                "rule_id": "demote_selector_trade_full_admission_uncalibrated",
                "symbol": "*",
                "side": "*",
                "session": "*",
                "selector_action": "trade",
                "selector_reason": (
                    "broker_net_probability_confluence_lifecycle_admission_passed"
                ),
                "numeric_mixed_count": 0,
                "reason": "selector_trade_full_admission_uncalibrated_replay_guard",
            }
        ],
    }
    candidate = {
        "symbol": "XAGUSD",
        "side": "LONG",
        "route_session": "london",
        "trading_day": "2026-05-14",
    }
    packets = {
        "selector_packet": {
            "action": "trade",
            "reason": "broker_net_probability_confluence_lifecycle_admission_passed",
            "component_scores": {"numeric_confluence": {"mixed_count": 0}},
        },
        "candidate_probability": 0.93,
        "candidate_ev_r": 1.25,
        "cost_r": 0.05,
    }

    blocked = timewarp.build_replay_loss_bucket_guard(
        candidate=candidate,
        packets=packets,
        limits=limits,
    )

    assert blocked["status"] == "blocked"
    assert (
        blocked["matched_rule_id"]
        == "demote_selector_trade_full_admission_uncalibrated"
    )
    assert blocked["live_broker_authority"] is False
    assert blocked["symbol"] == "XAGUSD"

    reduce_risk_packets = {
        **packets,
        "selector_packet": {
            **packets["selector_packet"],
            "action": "reduce-risk",
        },
    }

    clear = timewarp.build_replay_loss_bucket_guard(
        candidate=candidate,
        packets=reduce_risk_packets,
        limits=limits,
    )

    assert clear["status"] == "clear"
    assert clear["matched_rule_id"] is None


def test_allocator_close_reverse_authority_applies_quality_floors() -> None:
    result = scheduler.allocate_decision_window(
        {
            "decision_window_id": "window:close-reverse-floor",
            "candidate_set_id": "candidate-set:close-reverse-floor",
            "asof_utc": "2026-05-05T08:15:00+00:00",
            "open_positions": [
                {
                    "position_id": "open-short",
                    "symbol": "XAUUSD",
                    "side": "SHORT",
                    "risk_pct": 0.40,
                    "source_completeness": 1.0,
                }
            ],
            "candidates": [
                {
                    "candidate_id": "weak-close-reverse",
                    "symbol": "XAUUSD",
                    "side": "LONG",
                    "risk_reward_ratio": 2.0,
                    "action_intent": "new_position",
                    "ultimate_package_source_bound_candidate_use_allowed": True,
                    "ultimate_package_effective_source_bound_candidate_use_allowed": True,
                    "expected_net_r": 0.20,
                    "candidate_expected_net_r": 0.20,
                    "probability": 0.40,
                    "fill_probability": 0.10,
                    "source_completeness": 0.50,
                    "source_completeness_status": "partial",
                    "pretrade_cost_packet_status": "PASSED",
                }
            ],
        },
        {
            "enabled": True,
            "live_activation_allowed": False,
            "apply_to_execution": False,
            "package_opposite_side_close_reverse_enabled": True,
            "package_opposite_side_close_reverse_min_scheduler_score": 0.0,
            "package_opposite_side_close_reverse_min_expected_net_r": 0.80,
            "package_opposite_side_close_reverse_min_probability": 0.75,
            "package_opposite_side_close_reverse_min_fill_probability": 0.25,
            "package_opposite_side_close_reverse_min_source_completeness": 0.95,
            "min_trade_score": 0.0,
        },
    )

    option = next(
        row
        for row in result["all_options_preserved"]
        if row.get("candidate_id") == "weak-close-reverse"
    )
    authority = option["score_components"]["package_opposite_side_close_reverse_authority"]
    assert authority["applies"] is True
    assert authority["allowed"] is False
    assert set(authority["failures"]) >= {
        "expected_net_r",
        "probability",
        "fill_probability",
        "source_completeness",
    }
    assert option["runtime_eligible"] is False
    assert "opposite_side_requires_close_reduce_reverse_no_hedge" in option["vetoes"]


def test_package_positive_open_reduced_risk_candidate_reaches_scheduler(monkeypatch) -> None:
    captured = {}

    def fake_allocate(window, config, *, raw_config=None):
        captured["window"] = window
        captured["config"] = config
        return {
            "selected_candidate_id": "candidate-a",
            "selected_candidate_ids": ["candidate-a"],
            "option_trace": [],
        }

    monkeypatch.setattr(timewarp, "allocate_decision_window", fake_allocate)
    candidate = {
        "candidate_id": "candidate-a",
        "symbol": "XAUUSD",
        "side": "LONG",
        "risk_reward_ratio": 2.0,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "candidate_expected_net_r": 0.86,
        "probability": 0.76,
        "candidate_probability": 0.76,
        "fill_probability": 0.81,
        "candidate_fill_probability": 0.81,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "packets.candidate_ev_r-minus-packets.broker_calibrated_expected_cost_r",
            "probability": "packets.candidate_probability",
            "fill_probability": "predecision_limit_fillability.fill_probability",
            "source_completeness": "fixture.predecision.source_completeness",
        },
        "candidate_decision_quality_alias_status": "exact_materialized",
        "candidate_decision_quality_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        "source_window_complete": True,
    }
    decision_time = "2025-06-11T08:15:00+00:00"
    candidate.update(
        {
            "decision_time_utc": decision_time,
            "confidence": 0.7,
            "candidate_confidence": 0.7,
            "scheduler_confidence": 0.7,
            "cost_r": 0.05,
            "expected_cost_r": 0.05,
        }
    )
    candidate.update(timewarp.ultimate_package_member_axis_parity_fields(candidate))
    _add_strict_limit_fillability(candidate, 0.81)
    selector_packet = _selector_packet(
        "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk",
        action="open-reduced-risk",
    )
    selector_packet["component_scores"][
        "ultimate_candidate_package_open_reduced_risk_authority"
    ] = {
        "applies": True,
        "allowed": True,
        "authority_family": "router_refusal_softening",
    }
    _attach_signed_open_reduced_authority(
        candidate,
        selector_packet,
        reason=(
            "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk"
        ),
        decision_time=decision_time,
        authority_family="router_refusal_softening",
        bind_selected_policy_calibration_hash=True,
    )
    packets = {
        f"candidate-a@@{decision_time}": {
            "selector_packet": selector_packet,
            "probability_packet": {
                "theses": [
                    {
                        "action": "long",
                            "probability": 0.76,
                            "EV": 0.91,
                        "confidence": 0.7,
                    }
                ]
            },
            "lifecycle_packet": {"action": "new_position"},
            "selector_event": {
                "predecision_limit_fillability": {"fill_probability": 0.81}
            },
            "pretrade_broker_net_cost_packet": _cost_packet(),
            "cost_r": 0.05,
            "broker_calibrated_expected_cost_r": 0.05,
            "expected_net_r": 0.86,
        }
    }

    timewarp.materialize_scheduler_window(
        asof_utc=decision_time,
        candidates=[candidate],
        v4_packets=packets,
        config={
            "gtos_vnext_runtime": {
                "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk_allowed": True,
            }
        },
    )

    scheduler_candidates = captured["window"]["candidates"]
    assert len(scheduler_candidates) == 1
    row = scheduler_candidates[0]
    assert row["candidate_id"] == "candidate-a"
    assert row["selector_action"] == "open-reduced-risk"
    assert row["selector_reason"] == (
        "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk"
    )
    assert row["expected_net_r"] == 0.86
    assert row["candidate_expected_net_r"] == 0.86
    assert row["scheduler_materialization_override_reason"] == (
        "explicit_open_reduced_risk_entry_authority"
    )
    assert row["pretrade_cost_packet_status"] == "PASSED"
    assert candidate["scheduler_materialization_override_reason"] == (
        "explicit_open_reduced_risk_entry_authority"
    )
    assert candidate["package_open_reduced_authority_allowed"] is True
    assert (
        candidate["ultimate_package_open_reduced_authority_allowed"]
        is True
    )
    assert (
        candidate["ultimate_candidate_package_open_reduced_risk_authority"][
            "authority_family"
        ]
        == "router_refusal_softening"
    )
    assert row["package_open_reduced_authority_allowed"] is True
    assert row["package_open_reduced_authority_family"] == "router_refusal_softening"
    assert row["candidate_decision_quality_alias_status"] == "exact_materialized"
    assert row["candidate_decision_quality_field_sources"]["expected_net_r"] == (
        "packets.candidate_ev_r-minus-packets.broker_calibrated_expected_cost_r"
    )
    assert row["candidate_decision_quality_source_boundary"] == (
        "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
    )
    assert row["package_new_entry_authority_valid"] is True
    validation = scheduler.reduced_package_new_entry_authority_validation(
        row,
        selector_action=row["selector_action"],
        selector_reason=row["selector_reason"],
        action_intent=row["action_intent"],
    )
    signed_payload = row["ultimate_candidate_package_open_reduced_risk_authority"][
        "package_new_entry_authority_payload"
    ]
    projected_payload = scheduler.package_new_entry_authority_payload(
        row,
        selector_action=row["selector_action"],
        selector_reason=row["selector_reason"],
        action_intent=row["action_intent"],
        authority=row["ultimate_candidate_package_open_reduced_risk_authority"],
    )
    payload_diff = {
        key: (signed_payload.get(key), projected_payload.get(key))
        for key in signed_payload.keys() | projected_payload.keys()
        if signed_payload.get(key) != projected_payload.get(key)
    }
    assert validation["valid"] is True, (validation["failures"], payload_diff)


def test_package_router_reject_without_signed_positive_authority_uses_source_bound_reason(
    monkeypatch,
) -> None:
    captured = {}

    def fake_allocate(window, config, *, raw_config=None):
        captured["window"] = window
        return {
            "selected_candidate_id": "candidate-router-reject",
            "selected_candidate_ids": ["candidate-router-reject"],
            "option_trace": [],
        }

    monkeypatch.setattr(timewarp, "allocate_decision_window", fake_allocate)
    decision_time = "2025-06-11T08:15:00+00:00"
    fillability_source_time = "2025-06-11T08:00:00+00:00"
    fillability_source_boundary = (
        "closed_m15_predecision_asof_no_postdecision_path"
    )
    reason = "admission_quality_dynamic_router_refused_candidate_use"
    candidate = {
        "candidate_id": "candidate-router-reject",
        "decision_time_utc": decision_time,
        "symbol": "XAUUSD",
        "side": "LONG",
        "risk_reward_ratio": 2.0,
        "source_bound_package_candidate_use_allowed": True,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "package_replay_candidate_use_allowed": True,
        "ultimate_package_effective_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_admission_count": 1,
        "ultimate_package_effective_matched_count": 2,
        "ultimate_package_effective_source_bound_signal_r": 12.5,
        "candidate_expected_net_r": 1.12,
        "probability": 0.91,
        "fill_probability": 0.92,
        "predecision_limit_fillability_probability": 0.92,
        "execution_fill_probability": 0.92,
        "execution_fill_probability_source": (
            "predecision_limit_fillability.fill_probability"
        ),
        "execution_fill_probability_authority_class": (
            "predecision_passive_limit_fillability_authority"
        ),
        "execution_fill_probability_source_time_utc": fillability_source_time,
        "execution_fill_probability_source_boundary": fillability_source_boundary,
        "predecision_limit_fillability_source_time_utc": fillability_source_time,
        "predecision_limit_fillability_source_boundary": fillability_source_boundary,
        "candidate_decision_quality": {
            "execution_fill_probability_source_time_utc": fillability_source_time,
            "execution_fill_probability_source_boundary": (
                fillability_source_boundary
            ),
        },
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "fixture.predecision.expected_net_r",
            "probability": "fixture.predecision.probability",
            "fill_probability": "predecision_limit_fillability.fill_probability",
            "predecision_limit_fillability_probability": (
                "predecision_limit_fillability_probability"
            ),
            "execution_fill_probability": (
                "predecision_limit_fillability.fill_probability"
            ),
            "execution_fill_probability_source_time_utc": (
                "fixture.predecision.execution_fill_probability_source_time_utc"
            ),
            "execution_fill_probability_source_boundary": (
                "fixture.predecision.execution_fill_probability_source_boundary"
            ),
            "source_completeness": "fixture.predecision.source_completeness",
        },
        "candidate_decision_quality_alias_status": "exact_materialized",
        "candidate_decision_quality_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        "selected_policy_for_expected_net_r": "momentum_exhaustion",
        "selected_policy_expected_net_calibration_status": (
            "calibrated"
        ),
        "selected_policy_expected_net_calibrated": True,
        "selected_policy_expected_net_calibration_source": (
            "selected_policy_replay_calibration_packet"
        ),
        "selected_policy_expected_net_calibration_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        "lifecycle_action": "new_position",
    }
    selector_packet = _selector_packet(reason, action="reject")
    packets = {
        f"candidate-router-reject@@{decision_time}": {
            "selector_packet": selector_packet,
            "probability_packet": {
                "theses": [{"action": "long", "probability": 0.91, "EV": 1.19}]
            },
            "lifecycle_packet": {"action": "new_position"},
            "selector_event": {
                "predecision_limit_fillability": {},
                "predecision_limit_fillability_probability": 0.92,
                "execution_fill_probability_source_time_utc": (
                    fillability_source_time
                ),
                "execution_fill_probability_source_boundary": (
                    fillability_source_boundary
                ),
            },
            "pretrade_broker_net_cost_packet": _cost_packet(),
            "expected_net_r": 1.12,
            "candidate_expected_net_r": 1.12,
            "candidate_probability": 0.91,
            "candidate_fill_probability": 0.92,
            "source_completeness": 1.0,
        }
    }

    timewarp.materialize_scheduler_window(
        asof_utc=decision_time,
        candidates=[candidate],
        v4_packets=packets,
        config={
            "gtos_vnext_runtime": {
                "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk_allowed": True,
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_router_refusal_package_new_entry_authority_enabled": True,
            }
        },
    )

    scheduler_candidates = captured["window"]["candidates"]
    assert len(scheduler_candidates) == 1
    row = scheduler_candidates[0]
    assert row["selector_action"] == "open-reduced-risk"
    assert row["raw_selector_action"] == "reject"
    assert row["effective_selector_action"] == "open-reduced-risk"
    assert row["materialized_selector_action"] == "open-reduced-risk"
    assert row["scheduler_materialization_effective_selector_action"] == (
        "open-reduced-risk"
    )
    assert row["selector_action_semantics"]
    assert row["selector_reason"] == (
        "source_bound_router_refusal_open_reduced_materialized_for_replay"
    )
    assert row["raw_selector_reason"] == reason
    assert row["effective_selector_reason"] == (
        "source_bound_router_refusal_open_reduced_materialized_for_replay"
    )
    assert row["scheduler_materialization_original_selector_action"] == "reject"
    assert row["scheduler_materialization_original_selector_reason"] == reason
    assert row["scheduler_materialization_selector_reason_normalized_from"] == reason
    assert row["scheduler_materialization_selector_reject_open_reduced_applied"] is True
    assert row["package_open_reduced_authority_allowed"] is True
    assert row["package_open_reduced_authority_family"] == "router_refusal_softening"
    assert row["package_new_entry_authority_valid"] is True
    assert row["ultimate_candidate_package_open_reduced_risk_authority"][
        "original_selector_reason"
    ] == reason
    assert row["ultimate_candidate_package_open_reduced_risk_authority"][
        "explicit_positive_predecision_router_refusal_authority_present"
    ] is False
    assert scheduler.reduced_package_new_entry_authority_validation(
        row,
        selector_action=row["selector_action"],
        selector_reason=row["selector_reason"],
        action_intent=row["action_intent"],
    )["valid"] is True
    assert candidate["scheduler_materialization_selector_reject_open_reduced_applied"] is True
    assert candidate.get("scheduler_materialization_skip_reason") is None


def test_v221_selector_admission_exact_axis_and_atomic_fillability_reach_scheduler(
    monkeypatch,
) -> None:
    captured = {}

    def fake_allocate(window, config, *, raw_config=None):
        captured["window"] = window
        return {
            "selected_candidate_id": "v221-exact-axis-candidate",
            "selected_candidate_ids": ["v221-exact-axis-candidate"],
            "option_trace": [],
        }

    monkeypatch.setattr(timewarp, "allocate_decision_window", fake_allocate)
    monkeypatch.setattr(
        timewarp,
        "ultimate_package_member_axis_rows",
        lambda: (
            {
                "stable_member_axis_id": "member_axis:v221-exact-axis",
                "symbol": "NAS100",
                "side": "SHORT",
                "package_role": "scheduler_lifecycle_core",
                "combined_source_bound_signal_r": 12.5,
            },
        ),
    )
    decision_time = "2026-05-13T01:30:00+00:00"
    reason = "admission_quality_dynamic_router_refused_candidate_use"
    candidate = _ensure_fixture_quality_aliases(
        {
            "candidate_id": "v221-exact-axis-candidate",
            "decision_time_utc": decision_time,
            "symbol": "NAS100",
            "side": "SHORT",
            "framework": "broader_origin",
            "origin_family": "liquidity_sweep_reclaim",
            "candidate_expected_net_r": 0.82,
            "probability": 0.78,
            "confidence": 0.70,
            "fill_probability": 0.88,
            "source_completeness": 1.0,
            "source_completeness_status": "complete",
            "package_source_bound_admission_diagnostic": False,
            "source_bound_package_candidate_use_allowed": False,
            "ultimate_package_source_bound_candidate_use_allowed": False,
            "package_new_entry_authority_valid": False,
            "package_new_entry_authority_status": (
                "invalid_or_missing_signed_new_entry_authority"
            ),
            "package_new_entry_authority_payload": {},
            "package_new_entry_authority_failures": ["authority_payload_missing"],
            "lifecycle_action": "new_position",
        }
    )
    _add_strict_limit_fillability(candidate, 0.92)
    selector_packet = _selector_packet(reason, action="reject")
    package = selector_packet["component_scores"]["ultimate_candidate_package"]
    package.pop("admission_member_axis_match_count", None)
    package.pop("matched_member_axis_count", None)
    package.pop("matched_member_axis_ids", None)
    package["package_replay_executable_candidate_use_allowed"] = True
    package["package_replay_executable_candidate_use_allowed_reason"] = (
        "broker_cost_and_source_authority_executable"
    )
    selector_packet["component_scores"][
        "ultimate_candidate_package_open_reduced_risk_authority"
    ] = {
        "applies": True,
        "allowed": True,
        "authority_family": "router_refusal_softening",
        "selector_reason": reason,
        "reduced_risk_reasons": [reason],
        "ultimate_package_replay_admission_enabled": True,
        "ultimate_package_apply_to_execution": True,
        "ultimate_package_source_bound_replay_authority_allowed": True,
        "source_bound_router_refusal_authority_allowed": True,
        "positive_predecision_package_edge": True,
        "broker_cost_passed_for_package_router": True,
        "quality_contract": {
            "valid": True,
            "source_boundary": (
                "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
            ),
        },
        "source_boundary": (
            "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
        ),
    }
    packets = {
        f"v221-exact-axis-candidate@@{decision_time}": {
            "selector_packet": selector_packet,
            "probability_packet": {
                "theses": [
                    {"action": "short", "probability": 0.78, "EV": 0.87}
                ]
            },
            "lifecycle_packet": {"action": "new_position"},
            "selector_event": {
                "predecision_limit_fillability": dict(
                    candidate["predecision_limit_fillability"]
                )
            },
            "pretrade_broker_net_cost_packet": _cost_packet(),
            "expected_net_r": 0.82,
            "candidate_expected_net_r": 0.82,
            "candidate_probability": 0.78,
            "candidate_fill_probability": 0.88,
            "source_completeness": 1.0,
        }
    }

    timewarp.materialize_scheduler_window(
        asof_utc=decision_time,
        candidates=[candidate],
        v4_packets=packets,
        config={
            "gtos_vnext_runtime": {
                "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk_allowed": True,
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_router_refusal_package_new_entry_authority_enabled": True,
            }
        },
    )

    assert len(captured["window"]["candidates"]) == 1, {
        "skip_reason": candidate.get("scheduler_materialization_skip_reason"),
        "selector_action": candidate.get("scheduler_materialization_selector_action"),
        "selector_reason": candidate.get("scheduler_materialization_selector_reason"),
        "source_bound": candidate.get("source_bound_package_candidate_use_allowed"),
        "authority_status": candidate.get("package_new_entry_authority_status"),
        "authority_failures": candidate.get("package_new_entry_authority_failures"),
        "materialization_failures": candidate.get(
            "scheduler_materialization_selector_reject_open_reduced_failures"
        ),
    }
    row = captured["window"]["candidates"][0]
    assert row["selector_action"] == "open-reduced-risk"
    assert row["source_bound_package_candidate_use_allowed"] is True
    assert row["ultimate_package_matched_member_axis_ids"] == [
        "member_axis:v221-exact-axis"
    ]
    assert row["execution_fill_probability"] == 0.92
    assert row["execution_fillability_atomic_failure"] is None
    assert row["package_new_entry_authority_valid"] is True
    assert row["ultimate_candidate_package_open_reduced_risk_authority"][
        "package_new_entry_authority_payload"
    ]["execution_fill_probability"] == 0.92


def test_package_router_reject_with_signed_positive_authority_materializes(
    monkeypatch,
) -> None:
    captured = {}

    def fake_allocate(window, config, *, raw_config=None):
        captured["window"] = window
        return {
            "selected_candidate_id": "candidate-router-reject-signed",
            "selected_candidate_ids": ["candidate-router-reject-signed"],
            "option_trace": [],
        }

    monkeypatch.setattr(timewarp, "allocate_decision_window", fake_allocate)
    decision_time = "2025-06-11T08:15:00+00:00"
    member_axis_id = "fixture-member-axis:candidate-router-reject-signed"
    monkeypatch.setattr(
        timewarp,
        "ultimate_package_member_axis_rows",
        lambda: (
            {
                "stable_member_axis_id": member_axis_id,
                "symbol": "XAUUSD",
                "side": "LONG",
                "package_role": "scheduler_lifecycle_core",
                "combined_source_bound_signal_r": 12.5,
            },
        ),
    )
    raw_reason = "admission_quality_dynamic_router_refused_candidate_use"
    positive_reason = (
        "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk"
    )
    candidate = {
        "candidate_id": "candidate-router-reject-signed",
        "symbol": "XAUUSD",
        "side": "LONG",
        "risk_reward_ratio": 2.0,
        "source_bound_package_candidate_use_allowed": True,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "package_replay_candidate_use_allowed": True,
        "ultimate_package_effective_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_admission_count": 1,
        "ultimate_package_effective_matched_count": 2,
        "ultimate_package_effective_source_bound_signal_r": 12.5,
        "candidate_expected_net_r": 1.12,
        "probability": 0.91,
        "fill_probability": 0.92,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "fixture.predecision.expected_net_r",
            "probability": "fixture.predecision.probability",
            "fill_probability": "fixture.predecision.fill_probability",
            "source_completeness": "fixture.predecision.source_completeness",
        },
        "candidate_decision_quality_alias_status": "exact_materialized",
        "candidate_decision_quality_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        "selected_policy_for_expected_net_r": "momentum_exhaustion",
        "selected_policy_expected_net_calibration_status": (
            "calibrated"
        ),
        "selected_policy_expected_net_calibrated": True,
        "selected_policy_expected_net_calibration_source": (
            "selected_policy_replay_calibration_packet"
        ),
        "selected_policy_expected_net_calibration_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        "lifecycle_action": "new_position",
    }
    selector_packet = _selector_packet(raw_reason, action="reject")
    signed_authority = _attach_signed_open_reduced_authority(
        candidate,
        selector_packet,
        reason=positive_reason,
        decision_time=decision_time,
        authority_family="router_refusal_softening",
    )
    packets = {
        f"candidate-router-reject-signed@@{decision_time}": {
            "selector_packet": selector_packet,
            "decision_time_utc": decision_time,
            "probability_packet": {
                "theses": [{"action": "long", "probability": 0.91, "EV": 1.19}]
            },
            "lifecycle_packet": {"action": "new_position"},
            "selector_event": {
                "predecision_limit_fillability": {"fill_probability": 0.92}
            },
            "pretrade_broker_net_cost_packet": _cost_packet(),
            "expected_net_r": 1.12,
            "candidate_expected_net_r": 1.12,
            "candidate_probability": 0.91,
            "candidate_fill_probability": 0.92,
            "source_completeness": 1.0,
        }
    }

    timewarp.materialize_scheduler_window(
        asof_utc=decision_time,
        candidates=[candidate],
        v4_packets=packets,
        config={
            "gtos_vnext_runtime": {
                "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk_allowed": True,
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_router_refusal_package_new_entry_authority_enabled": True,
            }
        },
    )

    scheduler_candidates = captured["window"]["candidates"]
    assert len(scheduler_candidates) == 1
    row = scheduler_candidates[0]
    assert row["selector_action"] == "open-reduced-risk"
    assert row["selector_reason"] == positive_reason
    assert row["scheduler_materialization_original_selector_action"] == "reject"
    assert row["scheduler_materialization_original_selector_reason"] == raw_reason
    assert row["scheduler_materialization_selector_reason_normalized_from"] == raw_reason
    assert row["scheduler_materialization_selector_reject_open_reduced_applied"] is True
    assert row["package_open_reduced_authority_allowed"] is True
    assert row["package_open_reduced_authority_family"] == "router_refusal_softening"
    assert row["package_new_entry_authority_valid"] is True
    assert row["package_new_entry_authority_hash_sha256"] == (
        row["expected_package_new_entry_authority_hash_sha256"]
    )
    assert row["ultimate_candidate_package_open_reduced_risk_authority"][
        "package_new_entry_authority_hash_sha256"
    ] == row["package_new_entry_authority_hash_sha256"]
    assert candidate["scheduler_materialization_selector_reject_open_reduced_applied"] is True
    assert candidate.get("scheduler_materialization_skip_reason") is None


def test_package_reject_open_reduced_requires_existing_signed_authority(
    monkeypatch,
) -> None:
    captured = {}

    def fake_allocate(window, config, *, raw_config=None):
        captured["window"] = window
        return {
            "selected_candidate_id": "candidate-signed-reject-fill-floor",
            "selected_candidate_ids": ["candidate-signed-reject-fill-floor"],
            "option_trace": [],
        }

    monkeypatch.setattr(timewarp, "allocate_decision_window", fake_allocate)
    decision_time = "2025-06-11T08:15:00+00:00"
    reason = "ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay"
    member_axis_id = "fixture-member-axis:candidate-signed-reject-fill-floor"
    monkeypatch.setattr(
        timewarp,
        "ultimate_package_member_axis_rows",
        lambda: (
            {
                "stable_member_axis_id": member_axis_id,
                "symbol": "XAUUSD",
                "side": "LONG",
                "package_role": "scheduler_lifecycle_core",
                "combined_source_bound_signal_r": 12.5,
            },
        ),
    )
    candidate = {
        "candidate_id": "candidate-signed-reject-fill-floor",
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": (
            f"candidate-signed-reject-fill-floor@@{decision_time}"
        ),
        "source_bound_replay_candidate_instance_key": (
            f"candidate-signed-reject-fill-floor@@{decision_time}"
        ),
        "candidate_instance_identity_status": "materialized",
        "symbol": "XAUUSD",
        "side": "LONG",
        "risk_reward_ratio": 2.0,
        "source_bound_package_candidate_use_allowed": True,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "package_replay_candidate_use_allowed": True,
        "ultimate_package_effective_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_admission_count": 1,
        "ultimate_package_effective_matched_count": 2,
        "ultimate_package_effective_source_bound_signal_r": 12.5,
        "expected_net_r": 0.84,
        "candidate_expected_net_r": 0.84,
        "probability": 0.80,
        "fill_probability": 0.62,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "fixture.predecision.expected_net_r",
            "probability": "fixture.predecision.probability",
            "fill_probability": "fixture.predecision.fill_probability",
            "source_completeness": "fixture.predecision.source_completeness",
        },
        "candidate_decision_quality_alias_status": "exact_materialized",
        "candidate_decision_quality_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        "selected_policy_for_expected_net_r": "momentum_exhaustion",
        "selected_policy_expected_net_calibration_status": (
            "calibrated"
        ),
        "selected_policy_expected_net_calibrated": True,
        "selected_policy_expected_net_calibration_source": (
            "selected_policy_replay_calibration_packet"
        ),
        "selected_policy_expected_net_calibration_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "candidate_cost_r_fallback_is_authority": False,
        "package_replay_order_executable_candidate_use_allowed": True,
        "package_replay_order_executable_candidate_use_allowed_reason": (
            "raw_selector_reject_open_reduced_order_executable_promotion_contract_passed"
        ),
        "package_replay_order_executable_authority_source": (
            "selector_reject_open_reduced_materialization_detail"
        ),
        "lifecycle_action": "new_position",
    }
    selector_packet = _selector_packet(reason, action="reject")
    signed_authority = _attach_signed_open_reduced_authority(
        candidate,
        selector_packet,
        reason=reason,
        decision_time=decision_time,
        action_intent="new_position",
        authority_family="fill_floor_softening",
        authority_overrides={
            "source_bound_router_refusal_materialization_floors": {
                "expected_net_r": 0.55,
                "probability": 0.70,
                "fill_probability": 0.55,
                "source_completeness": 0.95,
            }
        },
    )
    packets = {
        f"candidate-signed-reject-fill-floor@@{decision_time}": {
            "selector_packet": selector_packet,
            "decision_time_utc": decision_time,
            "probability_packet": {
                "theses": [{"action": "long", "probability": 0.80, "EV": 0.91}]
            },
            "lifecycle_packet": {"action": "new_position"},
            "selector_event": {
                "predecision_limit_fillability": {"fill_probability": 0.62}
            },
            "pretrade_broker_net_cost_packet": _cost_packet(),
            "expected_net_r": 0.84,
            "candidate_expected_net_r": 0.84,
            "candidate_probability": 0.80,
            "candidate_fill_probability": 0.62,
            "source_completeness": 1.0,
        }
    }

    timewarp.materialize_scheduler_window(
        asof_utc=decision_time,
        candidates=[candidate],
        v4_packets=packets,
        config={
            "gtos_vnext_runtime": {
                "ultimate_candidate_package_soften_selector_fill_floor_enabled": True,
            }
        },
    )

    scheduler_candidates = captured["window"]["candidates"]
    assert len(scheduler_candidates) == 1
    row = scheduler_candidates[0]
    assert row["selector_action"] == "open-reduced-risk"
    assert row["scheduler_materialization_original_selector_action"] == "reject"
    assert row["scheduler_materialization_selector_reject_open_reduced_applied"] is True
    assert row["package_new_entry_authority_valid"] is True
    assert row["package_new_entry_authority_hash_sha256"] == (
        row["expected_package_new_entry_authority_hash_sha256"]
    )
    assert row["ultimate_candidate_package_open_reduced_risk_authority"][
        "package_new_entry_authority_hash_sha256"
    ] == row["package_new_entry_authority_hash_sha256"]
    assert candidate["package_new_entry_authority_valid"] is False
    assert "authority_provisional_marker_present" in candidate[
        "package_new_entry_authority_failures"
    ]
    assert candidate["ultimate_candidate_package_open_reduced_risk_authority"][
        "package_new_entry_authority_provisional_until_scheduler_row_finalized"
    ] is True
    assert candidate.get("scheduler_materialization_skip_reason") is None


def test_package_positive_router_reject_cost_refused_stays_non_executable(
    monkeypatch,
) -> None:
    captured = {}

    def fake_allocate(window, config, *, raw_config=None):
        captured["window"] = window
        return {"selected_candidate_id": None, "selected_candidate_ids": [], "option_trace": []}

    monkeypatch.setattr(timewarp, "allocate_decision_window", fake_allocate)
    decision_time = "2025-06-11T08:15:00+00:00"
    candidate = {
        "candidate_id": "candidate-router-cost-refused",
        "symbol": "XAUUSD",
        "side": "LONG",
        "risk_reward_ratio": 2.0,
        "source_bound_package_candidate_use_allowed": True,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "package_replay_candidate_use_allowed": True,
        "ultimate_package_effective_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_admission_count": 1,
        "ultimate_package_effective_matched_count": 2,
        "ultimate_package_effective_source_bound_signal_r": 12.5,
        "candidate_expected_net_r": 0.84,
        "probability": 0.80,
        "fill_probability": 0.62,
        "source_completeness": 1.0,
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "fixture.predecision.expected_net_r",
            "probability": "fixture.predecision.probability",
            "fill_probability": "fixture.predecision.fill_probability",
            "source_completeness": "fixture.predecision.source_completeness",
        },
        "candidate_decision_quality_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        "lifecycle_action": "new_position",
    }
    refused_cost = _cost_packet("REFUSED")
    refused_cost["refusal_reasons"] = ["total_cost_r_exceeds_max_cost_r"]
    packets = {
        f"candidate-router-cost-refused@@{decision_time}": {
            "selector_packet": _selector_packet(
                "admission_quality_dynamic_router_refused_candidate_use",
                action="reject",
            ),
            "probability_packet": {
                "theses": [{"action": "long", "probability": 0.80, "EV": 0.91}]
            },
            "lifecycle_packet": {"action": "new_position"},
            "selector_event": {
                "predecision_limit_fillability": {"fill_probability": 0.62}
            },
            "pretrade_broker_net_cost_packet": refused_cost,
            "expected_net_r": 0.84,
            "candidate_probability": 0.80,
            "candidate_fill_probability": 0.62,
            "source_completeness": 1.0,
        }
    }

    timewarp.materialize_scheduler_window(
        asof_utc=decision_time,
        candidates=[candidate],
        v4_packets=packets,
        config={
            "gtos_vnext_runtime": {
                "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk_allowed": True,
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_router_refusal_package_new_entry_authority_enabled": True,
            }
        },
    )

    assert captured["window"]["candidates"] == []
    assert candidate["scheduler_materialization_selector_reject_open_reduced_applied"] is False
    assert candidate["scheduler_materialization_skip_reason"] == (
        "selector_not_risk_bearing_cost_failed"
    )


def test_reduce_risk_fill_floor_soft_authority_reaches_scheduler(monkeypatch) -> None:
    captured = {}

    def fake_allocate(window, config, *, raw_config=None):
        captured["window"] = window
        captured["config"] = config
        return {
            "selected_candidate_id": "candidate-soft-fill-floor",
            "selected_candidate_ids": ["candidate-soft-fill-floor"],
            "option_trace": [],
        }

    monkeypatch.setattr(timewarp, "allocate_decision_window", fake_allocate)
    decision_time = "2025-06-11T08:15:00+00:00"
    reason = "ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay"
    open_reduced_authority = {
        "applies": False,
        "allowed": False,
        "authority_family": None,
        "selector_reason": reason,
        "reduced_risk_reasons": [
            reason,
            "ultimate_candidate_package_dynamic_router_refusal_softened_reduce_risk",
            "ultimate_candidate_package_fill_floor_bypass_reduce_risk_only",
            "ultimate_candidate_package_soft_admission:calibrated_admission_fill_probability_below_generalized_floor",
        ],
        "ultimate_package_soft_admission_override_allowed": True,
        "source_bound_candidate_use_allowed_now": True,
        "broker_cost_passed_for_package_router": True,
        "positive_predecision_package_edge": True,
        "current_config_allowed": True,
    }
    candidate = {
        "candidate_id": "candidate-soft-fill-floor",
        "symbol": "US30_cash",
        "side": "LONG",
        "risk_reward_ratio": 2.0,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "ultimate_package_admission_candidate_use_allowed": True,
        "ultimate_package_effective_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_admission_count": 1,
        "ultimate_package_effective_matched_count": 2,
        "candidate_expected_net_r": 1.27,
        "probability": 0.94,
        "fill_probability": 0.23,
        "source_completeness": 1.0,
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "fixture.predecision.expected_net_r",
            "probability": "fixture.predecision.probability",
            "fill_probability": "fixture.predecision.fill_probability",
            "source_completeness": "fixture.predecision.source_completeness",
        },
        "candidate_decision_quality_alias_status": "exact_materialized",
        "candidate_decision_quality_source_boundary": (
            "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
        ),
        "source_window_complete": True,
        "lifecycle_action": "new_position",
        "ultimate_candidate_package_open_reduced_risk_authority": (
            open_reduced_authority
        ),
    }
    selector_packet = _selector_packet(reason, action="reduce-risk")
    selector_packet["component_scores"][
        "ultimate_candidate_package_open_reduced_risk_authority"
    ] = open_reduced_authority
    packets = {
        f"candidate-soft-fill-floor@@{decision_time}": {
            "selector_packet": selector_packet,
            "probability_packet": {
                "theses": [{"action": "long", "probability": 0.94, "EV": 1.34}]
            },
            "lifecycle_packet": {"action": "new_position"},
            "selector_event": {
                "predecision_limit_fillability": {"fill_probability": 0.23}
            },
            "pretrade_broker_net_cost_packet": _cost_packet(),
            "cost_r": 0.07,
            "broker_calibrated_expected_cost_r": 0.07,
            "expected_net_r": 1.27,
            "candidate_probability": 0.94,
            "candidate_fill_probability": 0.23,
            "source_completeness": 1.0,
        }
    }

    timewarp.materialize_scheduler_window(
        asof_utc=decision_time,
        candidates=[candidate],
        v4_packets=packets,
        config={
            "gtos_vnext_runtime": {
                "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk_allowed": False,
                "ultimate_candidate_package_soften_selector_fill_floor_enabled": True,
            }
        },
    )

    scheduler_candidates = captured["window"]["candidates"]
    assert len(scheduler_candidates) == 1
    row = scheduler_candidates[0]
    assert row["selector_action"] == "open-reduced-risk"
    assert row["scheduler_materialization_original_selector_action"] == "reduce-risk"
    assert row["scheduler_materialization_action_intent"] == "new_position"
    assert row["scheduler_materialization_override_reason"] == (
        "explicit_open_reduced_risk_entry_authority"
    )
    assert row["package_open_reduced_authority_allowed"] is True
    assert row["package_open_reduced_authority_family"] == "fill_floor_softening"
    assert row["replay_candidate_use_allowed_now"] is True
    assert candidate["selector_action"] == "open-reduced-risk"
    assert candidate["replay_candidate_use_allowed_now"] is True
    assert (
        row["ultimate_candidate_package_open_reduced_risk_authority"][
            "authority_source"
        ]
        == "derived_from_soft_open_reduced_package_authority"
    )
    assert candidate.get("scheduler_materialization_skip_reason") is None


def test_reduce_risk_router_soft_authority_remains_blocked_when_config_disabled(
    monkeypatch,
) -> None:
    captured = {}

    def fake_allocate(window, config, *, raw_config=None):
        captured["window"] = window
        return {"selected_candidate_id": None, "selected_candidate_ids": [], "option_trace": []}

    monkeypatch.setattr(timewarp, "allocate_decision_window", fake_allocate)
    decision_time = "2025-06-11T08:15:00+00:00"
    reason = "ultimate_candidate_package_dynamic_router_refusal_softened_reduce_risk"
    open_reduced_authority = {
        "applies": False,
        "allowed": False,
        "authority_family": None,
        "selector_reason": reason,
        "reduced_risk_reasons": [reason],
        "ultimate_package_soft_admission_override_allowed": True,
        "source_bound_candidate_use_allowed_now": True,
        "broker_cost_passed_for_package_router": True,
        "positive_predecision_package_edge": True,
        "current_config_allowed": True,
    }
    candidate = {
        "candidate_id": "candidate-router-disabled",
        "symbol": "AUDJPY",
        "side": "LONG",
        "candidate_expected_net_r": 1.05,
        "probability": 0.86,
        "fill_probability": 0.92,
        "source_completeness": 1.0,
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "fixture.predecision.expected_net_r",
            "probability": "fixture.predecision.probability",
            "fill_probability": "fixture.predecision.fill_probability",
            "source_completeness": "fixture.predecision.source_completeness",
        },
        "candidate_decision_quality_alias_status": "exact_materialized",
        "candidate_decision_quality_source_boundary": (
            "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
        ),
        "lifecycle_action": "new_position",
        "ultimate_candidate_package_open_reduced_risk_authority": (
            open_reduced_authority
        ),
    }
    selector_packet = _selector_packet(reason, action="reduce-risk")
    selector_packet["component_scores"][
        "ultimate_candidate_package_open_reduced_risk_authority"
    ] = open_reduced_authority
    packets = {
        f"candidate-router-disabled@@{decision_time}": {
            "selector_packet": selector_packet,
            "lifecycle_packet": {"action": "new_position"},
            "selector_event": {
                "predecision_limit_fillability": {"fill_probability": 0.92}
            },
            "pretrade_broker_net_cost_packet": _cost_packet(),
            "expected_net_r": 1.05,
            "candidate_probability": 0.86,
            "candidate_fill_probability": 0.92,
            "source_completeness": 1.0,
        }
    }

    timewarp.materialize_scheduler_window(
        asof_utc=decision_time,
        candidates=[candidate],
        v4_packets=packets,
        config={
            "gtos_vnext_runtime": {
                "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk_allowed": False,
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_router_refusal_package_new_entry_authority_enabled": False,
            }
        },
    )

    assert captured["window"]["candidates"] == []
    assert candidate["scheduler_materialization_skip_reason"] == (
        "selector_reduce_risk_not_new_entry_authority"
    )


def test_reduce_risk_numeric_open_reduced_authority_materializes_as_open_reduced(
    monkeypatch,
) -> None:
    captured = {}

    def fake_allocate(window, config, *, raw_config=None):
        captured["window"] = window
        return {"selected_candidate_id": None, "selected_candidate_ids": [], "option_trace": []}

    monkeypatch.setattr(timewarp, "allocate_decision_window", fake_allocate)
    decision_time = "2025-06-11T08:15:00+00:00"
    reason = "numeric_confluence_structured_disagreement"
    open_reduced_authority = {
        "applies": True,
        "allowed": True,
        "authority_family": "numeric_disagreement_softening",
        "selector_reason": reason,
        "reduced_risk_reasons": [
            reason,
            "ultimate_candidate_package_numeric_disagreement_open_reduced_risk",
        ],
        "ultimate_package_soft_admission_override_allowed": True,
        "source_bound_candidate_use_allowed_now": True,
        "broker_cost_passed_for_package_router": True,
        "positive_predecision_package_edge": True,
        "current_config_allowed": True,
    }
    candidate = {
        "candidate_id": "candidate-numeric-reduce-risk",
        "symbol": "NZDUSD",
        "side": "SHORT",
        "risk_reward_ratio": 2.0,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "ultimate_package_admission_candidate_use_allowed": True,
        "ultimate_package_effective_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_admission_count": 1,
        "ultimate_package_effective_matched_count": 2,
        "candidate_expected_net_r": 0.77,
        "probability": 0.77,
        "fill_probability": 0.92,
        "source_completeness": 1.0,
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "fixture.predecision.expected_net_r",
            "probability": "fixture.predecision.probability",
            "fill_probability": "fixture.predecision.fill_probability",
            "source_completeness": "fixture.predecision.source_completeness",
        },
        "candidate_decision_quality_alias_status": "exact_materialized",
        "candidate_decision_quality_source_boundary": (
            "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
        ),
        "lifecycle_action": "new_position",
        "ultimate_candidate_package_open_reduced_risk_authority": (
            open_reduced_authority
        ),
    }
    selector_packet = _selector_packet(reason, action="reduce-risk")
    selector_packet["component_scores"][
        "ultimate_candidate_package_open_reduced_risk_authority"
    ] = open_reduced_authority
    packets = {
        f"candidate-numeric-reduce-risk@@{decision_time}": {
            "selector_packet": selector_packet,
            "lifecycle_packet": {"action": "new_position"},
            "selector_event": {
                "predecision_limit_fillability": {"fill_probability": 0.92}
            },
            "pretrade_broker_net_cost_packet": _cost_packet(),
            "expected_net_r": 0.77,
            "candidate_probability": 0.77,
            "candidate_fill_probability": 0.92,
            "source_completeness": 1.0,
        }
    }

    timewarp.materialize_scheduler_window(
        asof_utc=decision_time,
        candidates=[candidate],
        v4_packets=packets,
        config={
            "gtos_vnext_runtime": {
                "ultimate_candidate_package_numeric_disagreement_open_reduced_risk_enabled": True,
            }
        },
    )

    scheduler_candidates = captured["window"]["candidates"]
    assert len(scheduler_candidates) == 1
    row = scheduler_candidates[0]
    assert row["selector_action"] == "open-reduced-risk"
    assert row["scheduler_materialization_original_selector_action"] == "reduce-risk"
    assert row["scheduler_materialization_selector_action_normalization_reason"] == (
        "selector_reduce_risk_normalized_to_open_reduced_risk"
    )
    assert row["scheduler_materialization_selector_action_normalization_family"] == (
        "numeric_disagreement_softening"
    )
    assert row["scheduler_materialization_override_reason"] == (
        "explicit_open_reduced_risk_entry_authority"
    )
    assert candidate.get("scheduler_materialization_skip_reason") is None


def test_reduce_risk_numeric_open_reduced_disabled_stays_rankable_as_reduce_risk(
    monkeypatch,
) -> None:
    captured = {}

    def fake_allocate(window, config, *, raw_config=None):
        captured["window"] = window
        return {"selected_candidate_id": None, "selected_candidate_ids": [], "option_trace": []}

    monkeypatch.setattr(timewarp, "allocate_decision_window", fake_allocate)
    decision_time = "2025-06-11T08:15:00+00:00"
    reason = "numeric_confluence_structured_disagreement"
    member_axis_id = "fixture-member-axis:candidate-numeric-reduce-risk-disabled"
    monkeypatch.setattr(
        timewarp,
        "ultimate_package_member_axis_rows",
        lambda: (
            {
                "stable_member_axis_id": member_axis_id,
                "symbol": "NZDUSD",
                "side": "SHORT",
                "package_role": "scheduler_lifecycle_core",
                "combined_source_bound_signal_r": 11.0,
            },
        ),
    )
    open_reduced_authority = {
        "applies": False,
        "allowed": False,
        "authority_family": None,
        "selector_reason": reason,
        "reduced_risk_reasons": [
            reason,
            "ultimate_candidate_package_selector_fill_floor_softening_broker_cost_passed",
            "ultimate_candidate_package_selector_fill_floor_softening_positive_predecision_edge",
        ],
        "ultimate_package_soft_admission_override_allowed": True,
        "source_bound_candidate_use_allowed_now": True,
        "broker_cost_passed_for_package_router": True,
        "positive_predecision_package_edge": True,
        "current_config_allowed": True,
    }
    candidate = {
        "candidate_id": "candidate-numeric-reduce-risk-disabled",
        "decision_time_utc": decision_time,
        "symbol": "NZDUSD",
        "side": "SHORT",
        "risk_reward_ratio": 2.0,
        "selector_action": "reduce-risk",
        "selector_reason": reason,
        "action_intent": "new_position",
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "ultimate_package_admission_candidate_use_allowed": True,
        "ultimate_package_effective_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_admission_count": 1,
        "ultimate_package_effective_matched_count": 2,
        "candidate_expected_net_r": 0.77,
        "probability": 0.77,
        "fill_probability": 0.92,
        "source_completeness": 1.0,
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "fixture.predecision.expected_net_r",
            "probability": "fixture.predecision.probability",
            "fill_probability": "fixture.predecision.fill_probability",
            "source_completeness": "fixture.predecision.source_completeness",
        },
        "candidate_decision_quality_alias_status": "exact_materialized",
        "candidate_decision_quality_source_boundary": (
            "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
        ),
        "lifecycle_action": "new_position",
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "candidate_cost_r_fallback_is_authority": False,
        "ultimate_candidate_package_reduce_risk_authority": {
            "applies": True,
            "allowed": True,
            "authority_family": "numeric_disagreement_softening",
            "current_config_allowed": True,
            "source_boundary": (
                "predecision_package_reduce_risk_new_order_authority_no_outcome_fields"
            ),
        },
    }
    _add_strict_limit_fillability(candidate, 0.92)
    _sign_package_new_entry_authority(candidate)
    selector_packet = _selector_packet(reason, action="reduce-risk")
    selector_packet["component_scores"][
        "ultimate_candidate_package_open_reduced_risk_authority"
    ] = open_reduced_authority
    selector_packet["component_scores"][
        "ultimate_candidate_package_reduce_risk_authority"
    ] = candidate["ultimate_candidate_package_reduce_risk_authority"]
    selector_packet["component_scores"][
        "selector_reduced_risk_new_position_signed_authority"
    ] = candidate["ultimate_candidate_package_reduce_risk_authority"]
    packets = {
        f"candidate-numeric-reduce-risk-disabled@@{decision_time}": {
            "selector_packet": selector_packet,
            "lifecycle_packet": {"action": "new_position"},
            "selector_event": {
                "predecision_limit_fillability": {"fill_probability": 0.92}
            },
            "pretrade_broker_net_cost_packet": _cost_packet(),
            "expected_net_r": 0.77,
            "candidate_probability": 0.77,
            "candidate_fill_probability": 0.92,
            "source_completeness": 1.0,
        }
    }

    timewarp.materialize_scheduler_window(
        asof_utc=decision_time,
        candidates=[candidate],
        v4_packets=packets,
        config={
            "gtos_vnext_runtime": {
                "ultimate_candidate_package_numeric_disagreement_open_reduced_risk_enabled": False,
            }
        },
    )

    scheduler_candidates = captured["window"]["candidates"]
    assert len(scheduler_candidates) == 1
    row = scheduler_candidates[0]
    assert row["candidate_id"] == "candidate-numeric-reduce-risk-disabled"
    assert row["raw_selector_action"] == "reduce-risk"
    assert row["effective_selector_action"] == "reduce-risk"
    assert row["materialized_selector_action"] == "reduce-risk"
    assert row["selector_action_semantics"] == (
        "selector_action_is_materialized_runtime_action;"
        "raw_selector_action_preserves_original_selector_intent"
    )
    assert row["scheduler_materialization_override_reason"] == (
        "package_positive_reduce_risk_rankable_after_broker_cost_pass"
    )
    assert row["ultimate_package_scheduler_consumed_status"] == (
        "eligible_for_scheduler_consumption"
    )
    assert row["package_replay_executable_candidate_use_allowed"] is True
    assert row["package_reduce_risk_authority_allowed"] is True
    assert candidate["package_open_reduced_authority_allowed"] is False
    assert candidate["ultimate_package_open_reduced_authority_allowed"] is False
    assert candidate["ultimate_candidate_package_open_reduced_risk_authority"][
        "config_block_reason"
    ] == "numeric_disagreement_open_reduced_risk_disabled_by_config"
    assert "scheduler_materialization_skip_reason" not in candidate


def test_signed_open_reduced_authority_is_not_vetoed_by_legacy_reduce_risk_floor() -> None:
    decision_time = "2026-05-13T00:15:00+00:00"
    reason = "numeric_confluence_structured_disagreement"
    authority = {
        "applies": True,
        "allowed": True,
        "authority_family": "numeric_disagreement_softening",
        "selector_reason": reason,
        "source_boundary": (
            "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
        ),
        "ultimate_package_soft_admission_override_allowed": True,
        "source_bound_candidate_use_allowed_now": True,
        "broker_cost_passed_for_package_router": True,
        "positive_predecision_package_edge": True,
        "current_config_allowed": True,
    }
    candidate = {
        "candidate_id": "candidate-signed-open-reduced-low-floor",
        "decision_time_utc": decision_time,
        "symbol": "NZDUSD",
        "side": "SHORT",
        "route_session": "london_broad",
        "session": "london_broad",
        "session_bucket": "london_broad",
        "kill_zone": "london_broad",
        "selector_action": "open-reduced-risk",
        "selector_reason": reason,
        "action_intent": "new_position",
        "requested_risk_pct": 0.25,
        "selected_cell_risk_pct": 0.25,
        "expected_net_r": 0.623397451,
        "candidate_expected_net_r": 0.623397451,
        "probability": 0.716843496,
        "candidate_probability": 0.716843496,
        "fill_probability": 0.92,
        "candidate_fill_probability": 0.92,
        "confidence": 0.55,
        "candidate_confidence": 0.55,
        "source_completeness": 1.0,
        "source_completeness_status": "complete",
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "fixture.predecision.expected_net_r",
            "probability": "fixture.predecision.probability",
            "fill_probability": "fixture.predecision.fill_probability",
            "source_completeness": "fixture.predecision.source_completeness",
        },
        "candidate_decision_quality_alias_status": "exact_materialized",
        "candidate_decision_quality_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        "selected_policy_for_expected_net_r": "partial_be_runner",
        "expected_net_r_selected_policy": "partial_be_runner",
        "selected_policy_expected_net_calibration_status": "calibrated",
        "selected_policy_expected_net_calibrated": True,
        "selected_policy_expected_net_calibration_source": (
            "selected_policy_replay_calibration_packet"
        ),
        "selected_policy_expected_net_calibration_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        "source_bound_package_candidate_use_allowed": True,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_source_bound_candidate_use_allowed": True,
        "ultimate_package_admission_candidate_use_allowed": True,
        "ultimate_package_effective_admission_count": 1,
        "ultimate_package_effective_matched_count": 2,
        "ultimate_package_matched_sleeve_count": 2,
        "ultimate_package_admission_sleeve_match_count": 1,
        "package_replay_executable_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed_reason": (
            "broker_cost_selector_and_scheduler_action_executable"
        ),
        "replay_candidate_use_allowed_now": True,
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "candidate_cost_r_fallback_is_authority": False,
        "cost_r": 0.05,
        "expected_cost_r": 0.05,
        "ultimate_candidate_package_open_reduced_risk_authority": authority,
        "package_open_reduced_authority_allowed": True,
        "package_open_reduced_authority_family": "numeric_disagreement_softening",
    }
    _add_strict_limit_fillability(candidate)
    _sign_package_new_entry_authority(candidate)

    result = scheduler.allocate_decision_window(
        {
            "decision_window_id": f"timewarp:{decision_time}",
            "candidate_set_id": f"timewarp_candidate_set:{decision_time}",
            "asof_utc": decision_time,
            "candidates": [candidate],
            "open_positions": [],
            "pending_orders": [],
        },
        {
            "gtos_vnext_runtime": {
                "scheduler_v4_best_trade_allocator_min_trade_score": 0.35,
                "scheduler_v4_best_trade_allocator_zero_trade_score": 0.20,
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_authority_enabled": True,
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_expected_net_r": 0.70,
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_probability": 0.70,
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_fill_probability": 0.45,
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_source_completeness": 0.95,
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_open_reduced_expected_net_policy_calibration_required": True,
                "ultimate_candidate_package_numeric_disagreement_open_reduced_risk_enabled": True,
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_numeric_disagreement_package_new_entry_authority_enabled": True,
                "scheduler_v4_best_trade_allocator_dynamic_budget_quality_gate_enabled": False,
            },
        },
    )

    option = next(
        row
        for row in result["all_options_preserved"]
        if row.get("candidate_id") == candidate["candidate_id"]
    )
    replay_authority = option["score_components"][
        "selector_reduce_risk_package_replay_executable_authority"
    ]
    fill_floor_authority = option["score_components"][
        "selector_reduce_risk_package_fill_floor_authority"
    ]
    assert option["selector_action"] == "open-reduced-risk"
    assert option["runtime_eligible"] is True
    assert option["package_new_entry_authority_valid"] is True
    assert replay_authority["signed_open_reduced_new_entry_authority_allowed"] is True
    assert fill_floor_authority["allowed"] is False
    assert list(fill_floor_authority["failures"]) == ["expected_net_r"]
    assert not any(
        str(veto).startswith("selector_reduce_risk_new_entry_not_trade_authority")
        for veto in option["vetoes"]
    )
    assert option["reason"] != (
        "selector_reduce_risk_new_entry_not_trade_authority:"
        "numeric_confluence_structured_disagreement"
    )


def test_router_refusal_open_reduced_requires_selected_policy_calibration() -> None:
    decision_time = "2026-05-13T08:15:00+00:00"
    reason = "ultimate_candidate_package_dynamic_router_refusal_softened_reduce_risk"
    authority = {
        "applies": True,
        "allowed": True,
        "authority_family": "router_refusal_softening",
        "selector_reason": reason,
        "source_boundary": (
            "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
        ),
        "ultimate_package_soft_admission_override_allowed": True,
        "source_bound_candidate_use_allowed_now": True,
        "broker_cost_passed_for_package_router": True,
        "positive_predecision_package_edge": True,
        "current_config_allowed": True,
    }
    candidate = {
        "candidate_id": "candidate-router-refusal-uncalibrated-policy",
        "decision_time_utc": decision_time,
        "symbol": "XAUUSD",
        "side": "LONG",
        "route_session": "london",
        "session": "london",
        "session_bucket": "london",
        "kill_zone": "london",
        "selector_action": "open-reduced-risk",
        "selector_reason": reason,
        "action_intent": "new_position",
        "requested_risk_pct": 0.25,
        "selected_cell_risk_pct": 0.25,
        "expected_net_r": 1.05,
        "candidate_expected_net_r": 1.05,
        "probability": 0.88,
        "candidate_probability": 0.88,
        "fill_probability": 0.92,
        "candidate_fill_probability": 0.92,
        "confidence": 0.60,
        "candidate_confidence": 0.60,
        "source_completeness": 1.0,
        "source_completeness_status": "complete",
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "packets.candidate_expected_net_r",
            "probability": "packets.candidate_probability",
            "fill_probability": "candidate.fill_probability",
            "source_completeness": "candidate.source_completeness",
        },
        "candidate_decision_quality_alias_status": "materialized",
        "candidate_decision_quality_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        "selected_policy_for_expected_net_r": "momentum_exhaustion",
        "expected_net_r_selected_policy": "momentum_exhaustion",
        "selected_policy_expected_net_calibration_status": (
            "selected_policy_expected_net_calibration_missing"
        ),
        "selected_policy_expected_net_calibrated": False,
        "selected_policy_expected_net_calibration_required": True,
        "selected_policy_expected_net_calibration_source": (
            "packets.candidate_expected_net_r"
        ),
        "selected_policy_expected_net_calibration_source_boundary": (
            "selected_policy_expected_net_uncalibrated_bridge_proxy_predecision_quality"
        ),
        "source_bound_package_candidate_use_allowed": True,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_source_bound_candidate_use_allowed": True,
        "ultimate_package_admission_candidate_use_allowed": True,
        "ultimate_package_effective_admission_count": 1,
        "ultimate_package_effective_matched_count": 2,
        "ultimate_package_matched_sleeve_count": 2,
        "ultimate_package_admission_sleeve_match_count": 1,
        "package_replay_executable_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed_reason": (
            "broker_cost_selector_and_scheduler_action_executable"
        ),
        "replay_candidate_use_allowed_now": True,
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "candidate_cost_r_fallback_is_authority": False,
        "cost_r": 0.05,
        "expected_cost_r": 0.05,
        "ultimate_candidate_package_open_reduced_risk_authority": authority,
        "package_open_reduced_authority_allowed": True,
        "package_open_reduced_authority_family": "router_refusal_softening",
    }
    _sign_package_new_entry_authority(candidate)
    signed_authority = candidate[
        "ultimate_candidate_package_open_reduced_risk_authority"
    ]

    result = scheduler.allocate_decision_window(
        {
            "decision_window_id": f"timewarp:{decision_time}",
            "candidate_set_id": f"timewarp_candidate_set:{decision_time}",
            "asof_utc": decision_time,
            "candidates": [candidate],
            "open_positions": [],
            "pending_orders": [],
        },
        {
            "gtos_vnext_runtime": {
                "scheduler_v4_best_trade_allocator_min_trade_score": 0.35,
                "scheduler_v4_best_trade_allocator_zero_trade_score": 0.20,
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_authority_enabled": True,
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_expected_net_r": 0.70,
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_probability": 0.70,
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_fill_probability": 0.45,
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_source_completeness": 0.95,
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_open_reduced_expected_net_policy_calibration_required": True,
                "scheduler_v4_best_trade_allocator_selected_policy_expected_net_calibration_required_for_new_risk": True,
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_router_refusal_package_new_entry_authority_enabled": True,
                "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk_allowed": True,
                "scheduler_v4_best_trade_allocator_dynamic_budget_quality_gate_enabled": True,
            },
        },
    )

    option = next(
        row
        for row in result["all_options_preserved"]
        if row.get("candidate_id") == candidate["candidate_id"]
    )
    signed_detail = option["score_components"][
        "selector_reduced_risk_new_position_signed_authority"
    ]
    replay_authority = option["score_components"][
        "selector_reduce_risk_package_replay_executable_authority"
    ]
    assert signed_authority["package_new_entry_authority_valid"] is False
    assert "selected_policy_expected_net_bridge_proxy_not_executable" in (
        signed_authority["package_new_entry_authority_failures"]
    )
    assert option["runtime_eligible"] is False
    assert signed_detail["valid"] is False
    assert any(
        failure in signed_detail["failures"]
        for failure in (
            "selected_policy_expected_net_bridge_proxy_not_executable",
            "selected_policy_expected_net_calibration_missing",
        )
    )
    assert replay_authority["signed_open_reduced_new_entry_authority_allowed"] is False
    assert (
        replay_authority["selected_policy_expected_net_calibration"]["calibrated"]
        is False
    )


def test_owner_approved_selected_policy_replaces_stale_nested_bridge_proxy() -> None:
    stale_nested = {
        "selected_policy_for_expected_net_r": "momentum_exhaustion",
        "selected_policy_expected_net_calibration_status": (
            "selected_policy_expected_net_bridge_proxy_diagnostic_only"
        ),
        "selected_policy_expected_net_calibrated": False,
        "selected_policy_expected_net_calibration_required": True,
        "selected_policy_expected_net_calibration_source": (
            "packets.candidate_expected_net_r"
        ),
        "selected_policy_expected_net_calibration_source_boundary": (
            "selected_policy_expected_net_uncalibrated_bridge_proxy_predecision_quality"
        ),
    }
    owner_approved_fields = {
        "candidate_decision_quality": stale_nested,
        "selected_policy_for_expected_net_r": "momentum_exhaustion",
        "selected_policy_expected_net_calibration_status": (
            "owner_approved_reconstructed_replay_selected_policy_expected_net_calibrated"
        ),
        "selected_policy_expected_net_calibrated": True,
        "selected_policy_expected_net_calibration_required": True,
        "selected_policy_expected_net_calibration_source": (
            "owner_approved_reconstructed_proxy_package_expected_net_r"
        ),
        "selected_policy_expected_net_calibration_source_boundary": (
            "owner_approved_reconstructed_replay_predecision_selected_policy_expected_net_"
            "no_outcome_fields_local_replay_final_closed_no_broker_order_mutation"
        ),
        "selected_policy_expected_net_assumption_hash": "owner-approved-fixture-hash",
    }

    timewarp_envelope = timewarp.candidate_decision_quality_envelope(
        owner_approved_fields
    )
    scheduler_envelope = scheduler._candidate_decision_quality_envelope(
        owner_approved_fields
    )

    for envelope in (timewarp_envelope, scheduler_envelope):
        assert envelope["selected_policy_expected_net_calibrated"] is True
        assert envelope["selected_policy_expected_net_calibration_status"] == (
            "owner_approved_reconstructed_replay_selected_policy_expected_net_calibrated"
        )
        assert envelope["selected_policy_expected_net_calibration_source"] == (
            "owner_approved_reconstructed_proxy_package_expected_net_r"
        )
        assert (
            envelope[
                "selected_policy_expected_net_nested_replaced_by_owner_approved_calibration"
            ]
            is True
        )


def test_materialized_scheduler_window_refreshes_stale_nested_selected_policy(
    monkeypatch,
) -> None:
    captured = {}

    def fake_allocate(window, config, *, raw_config=None):
        captured["window"] = window
        return {"selected_candidate_id": None, "selected_candidate_ids": [], "option_trace": []}

    monkeypatch.setattr(timewarp, "allocate_decision_window", fake_allocate)
    decision_time = "2026-05-13T00:15:00+00:00"
    candidate_id = "candidate-owner-approved-refresh"
    reason = "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk"
    stale_nested = {
        "selected_policy_for_expected_net_r": "momentum_exhaustion",
        "selected_policy_expected_net_calibration_status": (
            "selected_policy_expected_net_bridge_proxy_diagnostic_only"
        ),
        "selected_policy_expected_net_calibrated": False,
        "selected_policy_expected_net_calibration_required": True,
        "selected_policy_expected_net_calibration_source": (
            "packets.candidate_expected_net_r"
        ),
        "selected_policy_expected_net_calibration_source_boundary": (
            "selected_policy_expected_net_uncalibrated_bridge_proxy_predecision_quality"
        ),
    }
    owner_boundary = (
        "owner_approved_reconstructed_replay_predecision_selected_policy_expected_net_"
        "no_outcome_fields_local_replay_final_closed_no_broker_order_mutation"
    )
    candidate = {
        "candidate_id": candidate_id,
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "source_bound_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "candidate_instance_identity_status": "materialized",
        "symbol": "AUDUSD",
        "side": "LONG",
        "risk_reward_ratio": 2.0,
        "source_bound_package_candidate_use_allowed": True,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_admission_count": 1,
        "ultimate_package_effective_matched_count": 1,
        "ultimate_package_effective_source_bound_signal_r": 12.5,
        "expected_net_r": 0.88,
        "candidate_expected_net_r": 0.88,
        "probability": 0.81,
        "candidate_probability": 0.81,
        "fill_probability": 0.93,
        "candidate_fill_probability": 0.93,
        "source_completeness": 1.0,
        "source_completeness_status": "complete",
        "candidate_decision_quality": stale_nested,
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "packets.candidate_expected_net_r",
            "probability": "packets.candidate_probability",
            "fill_probability": "selector_event.entry_quality_fill_probability",
            "source_completeness": "candidate.source_completeness",
        },
        "candidate_decision_quality_alias_status": "materialized",
        "candidate_decision_quality_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        "selected_policy_for_expected_net_r": "momentum_exhaustion",
        "selected_policy_expected_net_calibration_status": (
            "owner_approved_reconstructed_replay_selected_policy_expected_net_calibrated"
        ),
        "selected_policy_expected_net_calibrated": True,
        "selected_policy_expected_net_calibration_required": True,
        "selected_policy_expected_net_calibration_source": (
            "owner_approved_reconstructed_proxy_package_expected_net_r"
        ),
        "selected_policy_expected_net_calibration_source_boundary": owner_boundary,
        "selected_policy_expected_net_calibration_boundary": owner_boundary,
        "selected_policy_expected_net_assumption_hash": "owner-approved-fixture-hash",
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "candidate_cost_r_fallback_is_authority": False,
        "lifecycle_action": "new_position",
    }
    packets = {
        f"{candidate_id}@@{decision_time}": {
            "selector_packet": _open_reduced_selector_packet(reason),
            "probability_packet": {
                "theses": [{"action": "long", "probability": 0.81, "EV": 0.98}]
            },
            "lifecycle_packet": {"action": "new_position"},
            "selector_event": {
                "predecision_limit_fillability": {"fill_probability": 0.93}
            },
            "pretrade_broker_net_cost_packet": _cost_packet(),
            "candidate_expected_net_r": 0.88,
            "candidate_probability": 0.81,
            "candidate_fill_probability": 0.93,
            "source_completeness": 1.0,
        }
    }

    timewarp.materialize_scheduler_window(
        asof_utc=decision_time,
        candidates=[candidate],
        v4_packets=packets,
        config={
            "gtos_vnext_runtime": {
                "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk_allowed": True,
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_router_refusal_package_new_entry_authority_enabled": True,
            }
        },
    )

    row = captured["window"]["candidates"][0]
    quality = row["candidate_decision_quality"]
    assert quality["selected_policy_expected_net_calibrated"] is True
    assert quality["selected_policy_expected_net_calibration_status"] == "calibrated"
    assert quality["selected_policy_expected_net_calibration_source"] == (
        "owner_approved_reconstructed_proxy_package_expected_net_r"
    )
    assert row["selected_policy_expected_net_calibrated"] is True


def test_signed_reduce_risk_package_authority_requires_resolved_fill_floor() -> None:
    decision_time = "2026-05-13T00:30:00+00:00"
    reason = "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk"
    authority = {
        "applies": True,
        "allowed": True,
        "authority_family": "router_refusal_softening",
        "selector_reason": reason,
        "source_boundary": (
            "predecision_package_reduce_risk_new_entry_authority_no_outcome_fields"
        ),
        "source_bound_candidate_use_allowed_now": True,
        "broker_cost_passed_for_package_router": True,
        "current_config_allowed": True,
    }
    candidate = {
        "candidate_id": "candidate-signed-reduce-risk-explicit-authority",
        "decision_time_utc": decision_time,
        "symbol": "NZDUSD",
        "side": "SHORT",
        "selector_action": "reduce-risk",
        "selector_reason": reason,
        "action_intent": "new_position",
        "requested_risk_pct": 1.0,
        "selected_cell_risk_pct": 1.0,
        "expected_net_r": 0.92,
        "candidate_expected_net_r": 0.92,
        "probability": 0.82,
        "candidate_probability": 0.82,
        "fill_probability": 0.20,
        "candidate_fill_probability": 0.20,
        "confidence": 0.60,
        "candidate_confidence": 0.60,
        "source_completeness": 1.0,
        "source_completeness_status": "complete",
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "fixture.predecision.expected_net_r",
            "probability": "fixture.predecision.probability",
            "fill_probability": "fixture.predecision.fill_probability",
            "source_completeness": "fixture.predecision.source_completeness",
        },
        "candidate_decision_quality_alias_status": "exact_materialized",
        "candidate_decision_quality_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        "source_bound_package_candidate_use_allowed": True,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_source_bound_candidate_use_allowed": True,
        "ultimate_package_admission_candidate_use_allowed": True,
        "ultimate_package_effective_admission_count": 1,
        "ultimate_package_effective_matched_count": 2,
        "ultimate_package_matched_sleeve_count": 2,
        "ultimate_package_admission_sleeve_match_count": 1,
        "package_replay_executable_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed_reason": (
            "broker_cost_selector_and_scheduler_action_executable"
        ),
        "replay_candidate_use_allowed_now": True,
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "candidate_cost_r_fallback_is_authority": False,
        "cost_r": 0.05,
        "expected_cost_r": 0.05,
        "ultimate_candidate_package_reduce_risk_authority": authority,
        "package_reduce_risk_authority_allowed": True,
        "package_reduce_risk_authority_family": "router_refusal_softening",
    }
    _add_strict_limit_fillability(candidate)
    _sign_package_new_entry_authority(candidate)

    result = scheduler.allocate_decision_window(
        {
            "decision_window_id": f"timewarp:{decision_time}",
            "candidate_set_id": f"timewarp_candidate_set:{decision_time}",
            "asof_utc": decision_time,
            "candidates": [candidate],
            "open_positions": [],
            "pending_orders": [],
        },
        {
            "gtos_vnext_runtime": {
                "scheduler_v4_best_trade_allocator_min_trade_score": 0.35,
                "scheduler_v4_best_trade_allocator_zero_trade_score": 0.20,
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_authority_enabled": True,
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_expected_net_r": 0.70,
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_probability": 0.70,
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_fill_probability": 0.25,
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_source_completeness": 0.65,
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_router_refusal_package_new_entry_authority_enabled": True,
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_new_entry_risk_cap_enabled": True,
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_new_entry_max_risk_pct": 0.10,
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_release_risk_cap_enabled": True,
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_release_max_risk_pct": 0.25,
                "scheduler_v4_best_trade_allocator_dynamic_budget_quality_gate_enabled": True,
                "scheduler_v4_best_trade_allocator_dynamic_budget_min_fill_probability": 0.80,
            },
        },
    )

    option = next(
        row
        for row in result["all_options_preserved"]
        if row.get("candidate_id") == candidate["candidate_id"]
    )
    replay_authority = option["score_components"][
        "selector_reduce_risk_package_replay_executable_authority"
    ]
    fill_floor_authority = option["score_components"][
        "selector_reduce_risk_package_fill_floor_authority"
    ]
    reduce_risk_authority = option["score_components"][
        "selector_reduce_risk_new_entry_authority"
    ]
    assert option["runtime_eligible"] is False
    assert option["package_new_entry_authority_valid"] is True
    authority_sources = option[
        "package_new_entry_authority_candidate_decision_quality_field_sources"
    ]
    for required_key in (
        "expected_net_r",
        "probability",
        "fill_probability",
        "source_completeness",
    ):
        assert authority_sources[required_key] == candidate[
            "candidate_decision_quality_field_sources"
        ][required_key]
    assert option[
        "package_new_entry_authority_candidate_decision_quality_provenance_failures"
    ] == []
    assert replay_authority["allowed"] is False
    assert replay_authority["failures"] == [
        "package_fill_floor_quality_not_met:"
        "fill_probability_below_execution_authority_floor"
    ]
    assert fill_floor_authority["allowed"] is False
    assert (
        "fill_probability_below_execution_authority_floor"
        in fill_floor_authority["failures"]
    )
    assert reduce_risk_authority.get("risk_cap_release_reason") is None
    assert any(
        str(veto).startswith("selector_reduce_risk_new_entry_not_order_authority")
        for veto in option["vetoes"]
    )


def test_signed_open_reduced_fill_floor_authority_does_not_imply_off_session_authority() -> None:
    decision_time = "2026-05-15T07:00:00+00:00"
    reason = "ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay"
    authority = {
        "applies": True,
        "allowed": True,
        "authority_family": "fill_floor_softening",
        "selector_reason": reason,
        "source_boundary": (
            "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
        ),
        "ultimate_package_soft_admission_override_allowed": True,
        "source_bound_candidate_use_allowed_now": True,
        "broker_cost_passed_for_package_router": True,
        "positive_predecision_package_edge": True,
        "current_config_allowed": True,
    }
    candidate = {
        "candidate_id": "candidate-signed-open-reduced-off-session",
        "decision_time_utc": decision_time,
        "symbol": "BTCUSD",
        "side": "LONG",
        "route_session": "off_configured_session",
        "session": "off_configured_session",
        "session_bucket": "off_configured_session",
        "kill_zone": "off_configured_session",
        "selector_action": "open-reduced-risk",
        "selector_reason": reason,
        "action_intent": "same_direction_scale_in",
        "requested_risk_pct": 0.25,
        "selected_cell_risk_pct": 0.25,
        "expected_net_r": 1.18,
        "candidate_expected_net_r": 1.18,
        "probability": 0.927,
        "candidate_probability": 0.927,
        "fill_probability": 0.42,
        "candidate_fill_probability": 0.42,
        "confidence": 0.55,
        "candidate_confidence": 0.55,
        "source_completeness": 1.0,
        "source_completeness_status": "complete",
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "fixture.predecision.expected_net_r",
            "probability": "fixture.predecision.probability",
            "fill_probability": "fixture.predecision.fill_probability",
            "source_completeness": "fixture.predecision.source_completeness",
        },
        "candidate_decision_quality_alias_status": "exact_materialized",
        "candidate_decision_quality_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        "source_bound_package_candidate_use_allowed": True,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_source_bound_candidate_use_allowed": True,
        "ultimate_package_admission_candidate_use_allowed": True,
        "ultimate_package_effective_admission_count": 1,
        "ultimate_package_effective_matched_count": 2,
        "ultimate_package_matched_sleeve_count": 2,
        "ultimate_package_admission_sleeve_match_count": 1,
        "package_replay_executable_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed_reason": (
            "broker_cost_selector_and_scheduler_action_executable"
        ),
        "replay_candidate_use_allowed_now": True,
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "candidate_cost_r_fallback_is_authority": False,
        "cost_r": 0.05,
        "expected_cost_r": 0.05,
        "ultimate_candidate_package_open_reduced_risk_authority": authority,
        "package_open_reduced_authority_allowed": True,
        "package_open_reduced_authority_family": "fill_floor_softening",
    }
    _add_strict_limit_fillability(candidate)
    _sign_package_new_entry_authority(
        candidate,
        action_intent="same_direction_scale_in",
    )

    result = scheduler.allocate_decision_window(
        {
            "decision_window_id": f"timewarp:{decision_time}",
            "candidate_set_id": f"timewarp_candidate_set:{decision_time}",
            "asof_utc": decision_time,
            "candidates": [candidate],
            "open_positions": [],
            "pending_orders": [],
        },
        {
            "gtos_vnext_runtime": {
                "scheduler_v4_best_trade_allocator_min_trade_score": 0.35,
                "scheduler_v4_best_trade_allocator_zero_trade_score": 0.20,
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_authority_enabled": True,
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_expected_net_r": 0.70,
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_probability": 0.70,
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_fill_probability": 0.25,
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_source_completeness": 0.95,
                "ultimate_candidate_package_fill_floor_open_reduced_risk_enabled": True,
                "scheduler_v4_best_trade_allocator_dynamic_budget_quality_gate_enabled": False,
            },
        },
    )

    option = next(
        row
        for row in result["all_options_preserved"]
        if row.get("candidate_id") == candidate["candidate_id"]
    )
    replay_authority = option["score_components"][
        "selector_reduce_risk_package_replay_executable_authority"
    ]
    fill_floor_authority = option["score_components"][
        "selector_reduce_risk_package_fill_floor_authority"
    ]
    reduced_authority = option["score_components"][
        "selector_reduce_risk_new_entry_authority"
    ]
    expected_failure = "off_configured_session_requires_explicit_off_session_authority"
    assert option["package_new_entry_authority_valid"] is True
    assert option["runtime_eligible"] is False
    assert replay_authority["signed_open_reduced_new_entry_authority_allowed"] is False
    assert replay_authority["off_configured_session_authority_missing"] is True
    assert fill_floor_authority["off_configured_session_authority_missing"] is True
    assert expected_failure in fill_floor_authority["failures"]
    assert reduced_authority["off_configured_session_authority"][
        "authority_missing"
    ] is True
    assert any(expected_failure in veto for veto in option["vetoes"])
    assert (
        "package_lifecycle_root_authority_not_allowed:"
        "same_direction_scale_in_authority_not_allowed"
        in option["vetoes"]
    )


def test_scheduler_materialization_prefers_execution_session_over_route_session(monkeypatch) -> None:
    captured = {}

    def fake_allocate(window, config, *, raw_config=None):
        captured["window"] = window
        captured["config"] = config
        return {
            "selected_candidate_id": "candidate-session-namespace",
            "selected_candidate_ids": ["candidate-session-namespace"],
            "option_trace": [],
        }

    monkeypatch.setattr(timewarp, "allocate_decision_window", fake_allocate)
    decision_time = "2026-05-13T04:15:00+00:00"
    reason = "ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay"
    selector_packet = _selector_packet(reason, action="open-reduced-risk")
    selector_packet["component_scores"][
        "ultimate_candidate_package_open_reduced_risk_authority"
    ] = {
        "applies": True,
        "allowed": True,
        "authority_family": "fill_floor_softening",
        "source_boundary": (
            "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
        ),
        "ultimate_package_soft_admission_override_allowed": True,
        "source_bound_candidate_use_allowed_now": True,
        "broker_cost_passed_for_package_router": True,
        "positive_predecision_package_edge": True,
        "current_config_allowed": True,
    }
    candidate = {
        "candidate_id": "candidate-session-namespace",
        "symbol": "XAUUSD",
        "side": "LONG",
        "risk_reward_ratio": 2.0,
        "route_session": "off_configured_session",
        "session": "off_configured_session",
        "session_bucket": "moonshot_h04_05",
        "kill_zone": "moonshot_h04_05",
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_admission_count": 1,
        "ultimate_package_effective_matched_count": 2,
        "candidate_expected_net_r": 0.91,
        "probability": 0.78,
        "candidate_probability": 0.78,
        "confidence": 0.78,
        "candidate_confidence": 0.78,
        "fill_probability": 0.82,
        "candidate_fill_probability": 0.82,
        "source_completeness": 1.0,
        "source_completeness_status": "complete",
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "fixture.predecision.expected_net_r",
            "probability": "fixture.predecision.probability",
            "fill_probability": "fixture.predecision.fill_probability",
            "source_completeness": "fixture.predecision.source_completeness",
        },
        "candidate_decision_quality_alias_status": "exact_materialized",
        "candidate_decision_quality_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        "source_window_complete": True,
    }
    _add_strict_limit_fillability(candidate, 0.86)
    _add_strict_limit_fillability(candidate, 0.82)
    _attach_signed_open_reduced_authority(
        candidate,
        selector_packet,
        reason=reason,
        decision_time=decision_time,
        authority_family="fill_floor_softening",
    )
    packets = {
        f"candidate-session-namespace@@{decision_time}": {
            "selector_packet": selector_packet,
            "probability_packet": {
                "theses": [
                    {
                        "action": "long",
                        "probability": 0.78,
                        "EV": 0.96,
                        "confidence": 0.78,
                    }
                ]
            },
            "lifecycle_packet": {"action": "new_position"},
            "selector_event": {
                "predecision_limit_fillability": {"fill_probability": 0.82}
            },
            "pretrade_broker_net_cost_packet": _cost_packet(),
            "cost_r": 0.05,
            "broker_calibrated_expected_cost_r": 0.05,
            "expected_net_r": 0.91,
        }
    }

    timewarp.materialize_scheduler_window(
        asof_utc=decision_time,
        candidates=[candidate],
        v4_packets=packets,
        config={
            "gtos_vnext_runtime": {
                "ultimate_candidate_package_soften_selector_fill_floor_enabled": True,
            }
        },
    )

    row = captured["window"]["candidates"][0]
    assert row["route_session"] == "off_configured_session"
    assert row["session"] == "moonshot_h04_05"
    assert row["session_bucket"] == "moonshot_h04_05"
    assert row["kill_zone"] == "moonshot_h04_05"
    assert row["authority_session"] == "moonshot_h04_05"
    assert row["authority_session_source"] == "kill_zone"
    assert "moonshot_h04_05" in row["authority_session_tokens"]


def test_open_reduced_risk_without_explicit_package_authority_is_blocked(
    monkeypatch,
) -> None:
    captured = {}

    def fake_allocate(window, config, *, raw_config=None):
        captured["window"] = window
        captured["config"] = config
        return {
            "selected_candidate_id": None,
            "selected_candidate_ids": [],
            "option_trace": [],
        }

    monkeypatch.setattr(timewarp, "allocate_decision_window", fake_allocate)
    candidate = {
        "candidate_id": "candidate-off-session",
        "symbol": "XAUUSD",
        "side": "SHORT",
        "risk_reward_ratio": 2.0,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "candidate_expected_net_r": 0.91,
        "probability": 0.78,
        "confidence": 0.82,
        "candidate_confidence": 0.82,
        "scheduler_confidence": 0.82,
        "fill_probability": 0.32,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "fixture.predecision.expected_net_r",
            "probability": "fixture.predecision.probability",
            "confidence": "fixture",
            "fill_probability": "fixture.predecision.fill_probability",
            "source_completeness": "fixture.predecision.source_completeness",
        },
        "candidate_decision_quality_alias_status": "exact_materialized",
        "candidate_decision_quality_source_boundary": "predecision_fixture",
        "source_window_complete": True,
    }
    decision_time = "2025-06-11T17:30:00+00:00"
    packets = {
        f"candidate-off-session@@{decision_time}": {
            "selector_packet": _selector_packet(
                "ultimate_candidate_package_positive_predecision_off_session_open_reduced_risk",
                action="open-reduced-risk",
            ),
            "probability_packet": {
                "theses": [
                    {
                        "action": "short",
                        "probability": 0.78,
                        "EV": 1.02,
                        "confidence": 0.7,
                    }
                ]
            },
            "lifecycle_packet": {"action": "new_position"},
            "selector_event": {
                "predecision_limit_fillability": {"fill_probability": 0.84}
            },
            "pretrade_broker_net_cost_packet": _cost_packet(),
            "cost_r": 0.05,
            "broker_calibrated_expected_cost_r": 0.05,
            "expected_net_r": 0.91,
        }
    }

    timewarp.materialize_scheduler_window(
        asof_utc=decision_time,
        candidates=[candidate],
        v4_packets=packets,
        config={"gtos_vnext_runtime": {}},
    )

    assert captured["window"]["candidates"] == []
    assert candidate["scheduler_materialization_skip_reason"] == (
        "selector_open_reduced_risk_authority_missing"
    )
    assert candidate["scheduler_materialization_selector_action"] == "open-reduced-risk"


def test_scheduler_materialization_marks_missing_fillability_and_source_as_degraded(
    monkeypatch,
) -> None:
    captured = {}

    def fake_allocate(window, config, *, raw_config=None):
        captured["window"] = window
        return {"selected_candidate_id": None, "selected_candidate_ids": [], "option_trace": []}

    monkeypatch.setattr(timewarp, "allocate_decision_window", fake_allocate)
    candidate = {
        "candidate_id": "candidate-missing-roots",
        "symbol": "XAUUSD",
        "side": "LONG",
        "risk_reward_ratio": 2.0,
        "ultimate_package_source_bound_candidate_use_allowed": True,
    }
    packets = {
        "candidate-missing-roots": {
            "selector_packet": _open_reduced_selector_packet(
                "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk",
            ),
            "probability_packet": {
                "theses": [{"action": "long", "probability": 0.72, "EV": 0.78}]
            },
            "lifecycle_packet": {"action": "new_position"},
            "pretrade_broker_net_cost_packet": _cost_packet(),
        }
    }

    timewarp.materialize_scheduler_window(
        asof_utc="2025-06-11T08:15:00+00:00",
        candidates=[candidate],
        v4_packets=packets,
        config={"gtos_vnext_runtime": {}},
    )

    row = captured["window"]["candidates"][0]
    assert row["fill_probability_missing_degraded_default_applied"] is True
    assert row["fill_probability_status"] == "missing_degraded_heuristic_default"
    assert row["source_completeness_missing_degraded_default_applied"] is True
    assert row["source_completeness_status"] == "source_completeness_missing"
    assert row["source_completeness"] == 0.25


def test_scheduler_materialization_uses_candidate_fill_probability_alias(
    monkeypatch,
) -> None:
    captured = {}

    def fake_allocate(window, config, *, raw_config=None):
        captured["window"] = window
        return {"selected_candidate_id": None, "selected_candidate_ids": [], "option_trace": []}

    monkeypatch.setattr(timewarp, "allocate_decision_window", fake_allocate)
    candidate = {
        "candidate_id": "candidate-fill-alias",
        "symbol": "XAUUSD",
        "side": "LONG",
        "risk_reward_ratio": 2.0,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "candidate_fill_probability": 0.88,
        "source_completeness": 1.0,
    }
    packets = {
        "candidate-fill-alias": {
            "selector_packet": _open_reduced_selector_packet(
                "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk",
            ),
            "probability_packet": {
                "theses": [{"action": "long", "probability": 0.72, "EV": 0.78}]
            },
            "lifecycle_packet": {"action": "new_position"},
            "pretrade_broker_net_cost_packet": _cost_packet(),
        }
    }

    timewarp.materialize_scheduler_window(
        asof_utc="2025-06-11T08:15:00+00:00",
        candidates=[candidate],
        v4_packets=packets,
        config={"gtos_vnext_runtime": {}},
    )

    row = captured["window"]["candidates"][0]
    assert row["fill_probability"] == 0.88
    assert row["candidate_fill_probability"] == 0.88
    assert row.get("fill_probability_missing_degraded_default_applied") is not True
    assert row["fill_probability_status"] == "source_bound_input_present"


def test_scheduler_materialization_preserves_limit_fillability_separate_from_entry_quality(
    monkeypatch,
) -> None:
    captured = {}

    def fake_allocate(window, config, *, raw_config=None):
        captured["window"] = window
        return {"selected_candidate_id": None, "selected_candidate_ids": [], "option_trace": []}

    monkeypatch.setattr(timewarp, "allocate_decision_window", fake_allocate)
    monkeypatch.setattr(
        timewarp,
        "ultimate_package_member_axis_rows",
        lambda: (
            {
                "stable_member_axis_id": "member_axis:candidate-split-fill",
                "symbol": "XAUUSD",
                "side": "LONG",
                "package_role": "scheduler_lifecycle_core",
                "combined_source_bound_signal_r": 14.0,
            },
        ),
    )
    candidate = _ensure_fixture_quality_aliases(
        {
            "candidate_id": "candidate-split-fill",
            "decision_time_utc": "2025-06-11T08:15:00+00:00",
            "symbol": "XAUUSD",
            "side": "LONG",
            "risk_reward_ratio": 2.0,
            "ultimate_package_source_bound_candidate_use_allowed": True,
            "candidate_expected_net_r": 0.73,
            "probability": 0.72,
            "confidence": 0.70,
            "candidate_fill_probability": 0.24,
            "fill_probability": 0.24,
            "source_completeness": 1.0,
        }
    )
    packets = {
        "candidate-split-fill@@2025-06-11T08:15:00+00:00": {
                "selector_packet": _open_reduced_selector_packet(
                    "ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay",
                    authority_family="fill_floor_softening",
                ),
            "selector_event": {
                "entry_quality_fill_probability": 0.24,
                "decision_time_utc": "2025-06-11T08:15:00+00:00",
                "predecision_limit_fillability": {
                    "fill_probability": 0.92,
                    "source": "predecision_limit_fillability",
                    "source_time_utc": "2025-06-11T08:00:00+00:00",
                    "source_boundary": (
                        "asof_candidate_fields_only_no_postdecision_path"
                    ),
                    "uses_outcome_fields": False,
                },
            },
            "probability_packet": {
                "theses": [{"action": "long", "probability": 0.72, "EV": 0.78}]
            },
            "lifecycle_packet": {"action": "new_position"},
            "pretrade_broker_net_cost_packet": _cost_packet(),
        }
    }

    timewarp.materialize_scheduler_window(
        asof_utc="2025-06-11T08:15:00+00:00",
        candidates=[candidate],
        v4_packets=packets,
        config={
            "gtos_vnext_runtime": {
                "ultimate_candidate_package_soften_selector_fill_floor_enabled": True,
            }
        },
    )

    row = captured["window"]["candidates"][0]
    assert row["fill_probability"] == 0.24
    assert row["candidate_fill_probability"] == 0.24
    assert row["entry_quality_fill_probability"] == 0.24
    assert row["limit_fillability_probability"] == 0.92
    assert row["predecision_limit_fillability_probability"] == 0.92
    assert row["execution_fill_probability"] == 0.92
    assert row["execution_fill_probability_source"] == "predecision_limit_fillability"
    assert row["execution_fill_probability_source_time_utc"] == (
        "2025-06-11T08:00:00+00:00"
    )
    assert row["execution_fill_probability_source_boundary"] == (
        "asof_candidate_fields_only_no_postdecision_path"
    )
    assert row["execution_fill_probability_authority_class"] == (
        "predecision_passive_limit_fillability_authority"
    )
    assert row["execution_fillability_atomic_failure"] is None


def test_scheduler_materialization_uses_broker_packet_cost_when_aliases_absent(
    monkeypatch,
) -> None:
    captured = {}

    def fake_allocate(window, config, *, raw_config=None):
        captured["window"] = window
        return {"selected_candidate_id": None, "selected_candidate_ids": [], "option_trace": []}

    monkeypatch.setattr(timewarp, "allocate_decision_window", fake_allocate)
    cost_packet = _cost_packet()
    cost_packet["total_cost_r"] = 0.40
    candidate = {
        "candidate_id": "candidate-broker-cost",
        "symbol": "XAUUSD",
        "side": "LONG",
        "risk_reward_ratio": 2.0,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "source_window_complete": True,
    }
    packets = {
        "candidate-broker-cost": {
            "selector_packet": _open_reduced_selector_packet(
                "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk",
            ),
            "probability_packet": {
                "theses": [{"action": "long", "probability": 0.72, "EV": 0.78}]
            },
            "lifecycle_packet": {"action": "new_position"},
            "selector_event": {
                "predecision_limit_fillability": {"fill_probability": 0.81}
            },
            "pretrade_broker_net_cost_packet": cost_packet,
        }
    }

    timewarp.materialize_scheduler_window(
        asof_utc="2025-06-11T08:15:00+00:00",
        candidates=[candidate],
        v4_packets=packets,
        config={"gtos_vnext_runtime": {}},
    )

    row = captured["window"]["candidates"][0]
    assert row["expected_cost_r"] == 0.40
    assert row["broker_calibrated_expected_cost_r"] == 0.40
    assert row["candidate_expected_net_r"] == 0.38


def test_scheduler_materialization_rejects_unknown_action_intent(monkeypatch) -> None:
    captured = {}

    def fake_allocate(window, config, *, raw_config=None):
        captured["window"] = window
        return {"selected_candidate_id": None, "selected_candidate_ids": [], "option_trace": []}

    monkeypatch.setattr(timewarp, "allocate_decision_window", fake_allocate)
    candidate = {
        "candidate_id": "candidate-unknown-action",
        "symbol": "XAUUSD",
        "side": "LONG",
        "risk_reward_ratio": 2.0,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "candidate_expected_net_r": 0.67,
        "source_window_complete": True,
    }
    packets = {
        "candidate-unknown-action": {
            "selector_packet": _selector_packet(
                "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk",
                action="open-reduced-risk",
            ),
            "probability_packet": {
                "theses": [{"action": "long", "probability": 0.72, "EV": 0.78}]
            },
            "lifecycle_packet": {"action": "unknown_closeish"},
            "selector_event": {
                "predecision_limit_fillability": {"fill_probability": 0.81}
            },
            "pretrade_broker_net_cost_packet": _cost_packet(),
        }
    }

    timewarp.materialize_scheduler_window(
        asof_utc="2025-06-11T08:15:00+00:00",
        candidates=[candidate],
        v4_packets=packets,
        config={"gtos_vnext_runtime": {}},
    )

    assert captured["window"]["candidates"] == []
    assert candidate["scheduler_materialization_skip_reason"] == (
        "invalid_scheduler_action_intent"
    )
    assert candidate["scheduler_materialization_action_intent"] == (
        "invalid_action_intent:unknown_closeish"
    )


def test_duplicate_lifecycle_action_is_terminal_no_new_order_not_invalid(
    monkeypatch,
) -> None:
    captured = {}

    def fake_allocate(window, config, *, raw_config=None):
        captured["window"] = window
        return {"selected_candidate_id": None, "selected_candidate_ids": []}

    monkeypatch.setattr(timewarp, "allocate_decision_window", fake_allocate)
    candidate = {
        "candidate_id": "candidate-duplicate-terminal",
        "symbol": "XAUUSD",
        "side": "LONG",
        "risk_reward_ratio": 2.0,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "candidate_expected_net_r": 0.67,
        "source_window_complete": True,
    }
    packets = {
        "candidate-duplicate-terminal": {
            "selector_packet": _selector_packet(
                "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk",
                action="open-reduced-risk",
            ),
            "probability_packet": {
                "theses": [{"action": "long", "probability": 0.72, "EV": 0.78}]
            },
            "lifecycle_packet": {"action": "no_trade_duplicate"},
            "selector_event": {
                "predecision_limit_fillability": {"fill_probability": 0.81}
            },
            "pretrade_broker_net_cost_packet": _cost_packet(),
        }
    }

    timewarp.materialize_scheduler_window(
        asof_utc="2025-06-11T08:15:00+00:00",
        candidates=[candidate],
        v4_packets=packets,
        open_positions=[
            {
                "trade_id": "open:xau-long",
                "symbol": "XAUUSD",
                "side": "LONG",
                "risk_pct": 0.25,
            }
        ],
        config={"gtos_vnext_runtime": {}},
    )

    assert captured["window"]["candidates"] == []
    assert candidate["scheduler_materialization_skip_reason"] == (
        "scheduler_terminal_no_new_order_duplicate_lifecycle_action"
    )
    assert candidate["scheduler_materialization_action_intent"] == "no_trade_duplicate"
    assert (
        candidate["scheduler_materialization_terminal_no_new_order_action"]
        == "no_trade_duplicate"
    )
    assert candidate["same_symbol_replay_exposure_context"]["same_side_open_ids"] == [
        "open:xau-long"
    ]
    assert candidate["same_symbol_lifecycle_exposure_risk_pct"] == 0.25


def test_same_side_pending_duplicate_package_row_reaches_replace_pending_scheduler(
    monkeypatch,
) -> None:
    captured = {}

    def fake_allocate(window, config, *, raw_config=None):
        captured["window"] = window
        return {
            "selected_candidate_id": "candidate-duplicate-pending-replace",
            "selected_candidate_ids": ["candidate-duplicate-pending-replace"],
            "option_trace": [],
        }

    monkeypatch.setattr(timewarp, "allocate_decision_window", fake_allocate)
    decision_time = "2025-06-11T08:15:00+00:00"
    reason = "source_bound_router_refusal_open_reduced_materialized_for_replay"
    selector_packet = _selector_packet(reason, action="open-reduced-risk")
    candidate = {
        "candidate_id": "candidate-duplicate-pending-replace",
        "symbol": "XAUUSD",
        "side": "LONG",
        "risk_reward_ratio": 2.0,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "candidate_expected_net_r": 0.91,
        "probability": 0.80,
        "candidate_probability": 0.80,
        "fill_probability": 0.82,
        "candidate_fill_probability": 0.82,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "source_window_complete": True,
    }
    _add_strict_limit_fillability(candidate, 0.82)
    _attach_signed_open_reduced_authority(
        candidate,
        selector_packet,
        reason=reason,
        decision_time=decision_time,
        action_intent="replace_pending",
        authority_family="router_refusal_softening",
    )
    packets = {
        f"candidate-duplicate-pending-replace@@{decision_time}": {
            "selector_packet": selector_packet,
            "probability_packet": {
                "theses": [
                    {
                        "action": "long",
                        "probability": 0.80,
                        "EV": 0.96,
                    }
                ]
            },
            "lifecycle_packet": {"action": "no_trade_duplicate"},
            "selector_event": {
                "predecision_limit_fillability": {"fill_probability": 0.82}
            },
            "pretrade_broker_net_cost_packet": _cost_packet(),
            "expected_net_r": 0.91,
            "fill_probability": 0.82,
            "candidate_fill_probability": 0.82,
        }
    }

    timewarp.materialize_scheduler_window(
        asof_utc=decision_time,
        candidates=[candidate],
        v4_packets=packets,
        pending_orders=[
            {
                "order_id": "pending:xau-long",
                "symbol": "XAUUSD",
                "side": "LONG",
                "risk_pct": 0.25,
                "reserved_risk_pct": 0.25,
                "expected_net_r": 0.20,
                "fill_probability": 0.70,
                "pending_limit_fillability_probability": 0.70,
                "pending_fill_probability_authority_class": (
                    "passive_limit_fillability"
                ),
                "source_completeness": 1.0,
            }
        ],
        config={"gtos_vnext_runtime": {}},
    )

    scheduler_candidates = captured["window"]["candidates"]
    assert len(scheduler_candidates) == 1
    row = scheduler_candidates[0]
    assert row["candidate_id"] == "candidate-duplicate-pending-replace"
    assert row["action_intent"] == "replace_pending"
    assert row["same_symbol_lifecycle_action"] == "replace_pending"
    assert (
        row[
            "scheduler_materialization_duplicate_no_trade_pending_replacement_replay_override_applied"
        ]
        is True
    )
    assert row["scheduler_materialization_original_action_intent"] == (
        "no_trade_duplicate"
    )
    assert row["scheduler_materialization_original_lifecycle_action"] == (
        "no_trade_duplicate"
    )
    assert "scheduler_materialization_terminal_no_new_order_action" not in row
    assert row["same_symbol_replay_exposure_context"]["same_side_pending_ids"] == [
        "pending:xau-long"
    ]
    assert row["same_symbol_lifecycle_exposure_risk_pct"] == 0.25


def test_package_effective_signal_is_materialized_before_selector_reject_skip(
    monkeypatch,
) -> None:
    captured = {}

    def fake_allocate(window, config, *, raw_config=None):
        captured["window"] = window
        return {
            "selected_candidate_id": None,
            "selected_candidate_ids": [],
            "option_trace": [],
        }

    monkeypatch.setattr(timewarp, "allocate_decision_window", fake_allocate)
    selector_packet = _selector_packet(
        "admission_quality_off_configured_session_entry_blocked",
        action="reject",
    )
    selector_packet["component_scores"]["ultimate_candidate_package"][
        "admission_sleeve_match_count"
    ] = 1
    candidate = {
        "candidate_id": "candidate-offsession-package-reject",
        "symbol": "XAUUSD",
        "side": "LONG",
        "risk_reward_ratio": 2.0,
        "source_window_complete": True,
    }
    packets = {
        "candidate-offsession-package-reject": {
            "selector_packet": selector_packet,
            "probability_packet": {
                "theses": [{"action": "long", "probability": 0.80, "EV": 0.95}]
            },
            "lifecycle_packet": {"action": "new_position"},
            "selector_event": {
                "predecision_limit_fillability": {"fill_probability": 0.82}
            },
            "pretrade_broker_net_cost_packet": _cost_packet(),
            "expected_net_r": 0.90,
        }
    }

    timewarp.materialize_scheduler_window(
        asof_utc="2025-06-11T08:15:00+00:00",
        candidates=[candidate],
        v4_packets=packets,
        config={"gtos_vnext_runtime": {}},
    )

    assert captured["window"]["candidates"] == []
    assert candidate["scheduler_materialization_skip_reason"] == (
        "selector_not_risk_bearing_off_configured_session_block"
    )
    assert candidate["ultimate_package_effective_evidence_source"] in {
        "sleeve_admission_source_bound_use_allowed",
        "member_axis_admission_source_bound_use_allowed",
    }
    assert candidate["ultimate_package_scheduler_consumed_status"] == (
        "diagnostic_not_scheduler_consumed"
    )
    assert candidate["ultimate_package_effective_source_bound_candidate_use_allowed"] is True


def test_source_required_fail_closed_package_replay_override_reaches_scheduler(
    monkeypatch,
) -> None:
    captured = {}

    def fake_allocate(window, config, *, raw_config=None):
        captured["window"] = window
        captured["config"] = config
        return {
            "selected_candidate_id": "candidate-source-required",
            "selected_candidate_ids": ["candidate-source-required"],
            "option_trace": [],
        }

    monkeypatch.setattr(timewarp, "allocate_decision_window", fake_allocate)
    decision_time = "2025-06-11T08:15:00+00:00"
    selector_packet = _selector_packet(
        "ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay",
        action="open-reduced-risk",
    )
    selector_packet["component_scores"]["ultimate_candidate_package"][
        "admission_sleeve_match_count"
    ] = 1
    candidate = {
        "candidate_id": "candidate-source-required",
        "symbol": "XAUUSD",
        "side": "LONG",
        "risk_reward_ratio": 2.0,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "candidate_expected_net_r": 0.91,
        "probability": 0.78,
        "candidate_probability": 0.78,
        "fill_probability": 0.32,
        "candidate_fill_probability": 0.32,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "source_window_complete": True,
    }
    _attach_signed_open_reduced_authority(
        candidate,
        selector_packet,
        reason="ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay",
        decision_time=decision_time,
        action_intent="same_direction_scale_in",
    )
    _add_strict_limit_fillability(candidate, 0.32)
    packets = {
        f"candidate-source-required@@{decision_time}": {
            "selector_packet": selector_packet,
            "probability_packet": {
                "theses": [
                    {
                        "action": "long",
                        "probability": 0.78,
                        "EV": 0.96,
                        "confidence": 0.7,
                    }
                ]
            },
            "lifecycle_packet": {"action": "source_required_fail_closed"},
            "selector_event": {
                "predecision_limit_fillability": {"fill_probability": 0.32}
            },
            "pretrade_broker_net_cost_packet": _cost_packet(),
            "cost_r": 0.05,
            "broker_calibrated_expected_cost_r": 0.05,
            "expected_net_r": 0.91,
            "fill_probability": 0.32,
            "candidate_fill_probability": 0.32,
        }
    }

    timewarp.materialize_scheduler_window(
        asof_utc=decision_time,
        candidates=[candidate],
        v4_packets=packets,
        open_positions=[
            {
                "symbol": "XAUUSD",
                "side": "LONG",
                "risk_pct": 0.05,
            }
        ],
        config={
            "gtos_vnext_runtime": {
                "scheduler_v4_best_trade_allocator_source_required_fail_closed_package_replay_override_enabled": True,
                "scheduler_v4_best_trade_allocator_source_required_fail_closed_package_replay_override_min_expected_net_r": 0.80,
                "scheduler_v4_best_trade_allocator_source_required_fail_closed_package_replay_override_min_probability": 0.75,
                "scheduler_v4_best_trade_allocator_source_required_fail_closed_package_replay_override_min_fill_probability": 0.25,
                "scheduler_v4_best_trade_allocator_source_required_fail_closed_package_replay_override_min_source_completeness": 0.95,
                "scheduler_v4_best_trade_allocator_source_required_package_duplicate_scale_in_enabled": True,
            }
        },
    )

    scheduler_candidates = captured["window"]["candidates"]
    assert len(scheduler_candidates) == 1
    row = scheduler_candidates[0]
    assert row["candidate_id"] == "candidate-source-required"
    assert row["action_intent"] == "same_direction_scale_in"
    assert row["scheduler_materialization_original_action_intent"] == (
        "invalid_action_intent:source_required_fail_closed"
    )
    assert (
        row[
            "scheduler_materialization_source_required_fail_closed_override_applied"
        ]
        is True
    )
    assert (
        row[
            "scheduler_materialization_source_required_fail_closed_same_side_open_position"
        ]
        is True
    )
    assert (
        row[
            "scheduler_materialization_source_required_fail_closed_lifecycle_context_present"
        ]
        is True
    )
    assert (
        row[
            "scheduler_materialization_source_required_fail_closed_lifecycle_context_source"
        ]
        == "open_position"
    )
    assert row["scheduler_materialization_override_reason"] == (
        "source_required_fail_closed_package_source_reconciled_for_replay"
    )
    assert row["package_replay_executable_candidate_use_allowed"] is True
    assert row["package_replay_executable_candidate_use_allowed_reason"] == (
        "broker_cost_and_scheduler_action_executable"
    )
    assert row["replay_candidate_use_allowed_now"] is True
    assert row["replay_candidate_use_allowed_now_reason"] == (
        "source_required_fail_closed_package_replay_override_applied"
    )
    assert row["ultimate_package_scheduler_consumed_status"] == (
        "eligible_for_scheduler_consumption"
    )


def test_source_required_fail_closed_package_replay_override_requires_same_side_open_position(
    monkeypatch,
) -> None:
    captured = {}

    def fake_allocate(window, config, *, raw_config=None):
        captured["window"] = window
        return {
            "selected_candidate_id": None,
            "selected_candidate_ids": [],
            "option_trace": [],
        }

    monkeypatch.setattr(timewarp, "allocate_decision_window", fake_allocate)
    decision_time = "2025-06-11T08:15:00+00:00"
    selector_packet = _selector_packet(
        "ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay",
        action="open-reduced-risk",
    )
    selector_packet["component_scores"]["ultimate_candidate_package"][
        "admission_sleeve_match_count"
    ] = 1
    candidate = {
        "candidate_id": "candidate-source-required-no-context",
        "symbol": "XAUUSD",
        "side": "LONG",
        "risk_reward_ratio": 2.0,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "candidate_expected_net_r": 0.91,
        "probability": 0.78,
        "candidate_probability": 0.78,
        "fill_probability": 0.32,
        "candidate_fill_probability": 0.32,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "source_window_complete": True,
    }
    packets = {
        "candidate-source-required-no-context": {
            "selector_packet": selector_packet,
            "probability_packet": {
                "theses": [{"action": "long", "probability": 0.78, "EV": 0.96}]
            },
            "lifecycle_packet": {"action": "source_required_fail_closed"},
            "selector_event": {
                "predecision_limit_fillability": {"fill_probability": 0.32}
            },
            "pretrade_broker_net_cost_packet": _cost_packet(),
            "expected_net_r": 0.91,
            "fill_probability": 0.32,
            "candidate_fill_probability": 0.32,
        }
    }

    timewarp.materialize_scheduler_window(
        asof_utc="2025-06-11T08:15:00+00:00",
        candidates=[candidate],
        v4_packets=packets,
        config={
            "gtos_vnext_runtime": {
                "scheduler_v4_best_trade_allocator_source_required_fail_closed_package_replay_override_enabled": True,
                "scheduler_v4_best_trade_allocator_source_required_package_duplicate_scale_in_enabled": True,
            }
        },
    )

    assert captured["window"]["candidates"] == []
    assert candidate["scheduler_materialization_skip_reason"] == (
        "source_required_fail_closed_package_replay_override_failed:"
        "same_symbol_lifecycle_action_context_missing"
    )
    assert (
        candidate[
            "scheduler_materialization_source_required_fail_closed_override_applied"
        ]
        is False
    )
    assert (
        candidate[
            "scheduler_materialization_source_required_fail_closed_same_side_open_position"
        ]
        is False
    )
    assert (
        candidate[
            "scheduler_materialization_source_required_fail_closed_lifecycle_context_present"
        ]
        is False
    )


def test_source_required_fail_closed_source_bound_router_authority_signs_new_position_without_old_router_floor(
    monkeypatch,
) -> None:
    captured = {}

    def fake_allocate(window, config, *, raw_config=None):
        captured["window"] = window
        return {
            "selected_candidate_id": "candidate-source-required-router",
            "selected_candidate_ids": ["candidate-source-required-router"],
            "option_trace": [],
        }

    monkeypatch.setattr(timewarp, "allocate_decision_window", fake_allocate)
    decision_time = "2025-06-11T08:15:00+00:00"
    selector_reason = "source_bound_router_refusal_open_reduced_materialized_for_replay"
    selector_packet = _open_reduced_selector_packet(
        selector_reason,
        authority_family="router_refusal_softening",
    )
    selector_packet["component_scores"]["candidate_decision_inputs"] = {
        "expected_net_r": 0.62,
        "candidate_expected_net_r": 0.62,
        "probability": 0.72,
        "candidate_probability": 0.72,
        "fill_probability": 0.86,
        "candidate_fill_probability": 0.86,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "fixture.predecision.expected_net_r",
            "probability": "fixture.predecision.probability",
            "fill_probability": "fixture.predecision.fill_probability",
            "source_completeness": "fixture.predecision.source_completeness",
        },
        "candidate_decision_quality_source_boundary": "predecision_fixture",
        "candidate_decision_quality_alias_status": "exact_materialized",
        "selected_policy_for_expected_net_r": "momentum_exhaustion",
        "selected_policy_expected_net_calibration_status": "calibrated",
        "selected_policy_expected_net_calibrated": True,
        "selected_policy_expected_net_calibration_source": (
            "selected_policy_replay_calibration_packet"
        ),
        "selected_policy_expected_net_calibration_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
    }
    candidate = {
        "candidate_id": "candidate-source-required-router",
        "symbol": "XAUUSD",
        "side": "LONG",
        "risk_reward_ratio": 2.0,
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": (
            f"candidate-source-required-router@@{decision_time}"
        ),
        "source_bound_replay_candidate_instance_key": (
            f"candidate-source-required-router@@{decision_time}"
        ),
        "candidate_instance_identity_status": "materialized",
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "source_bound_package_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed": True,
        "candidate_expected_net_r": 0.62,
        "probability": 0.72,
        "candidate_probability": 0.72,
        "fill_probability": 0.86,
        "candidate_fill_probability": 0.86,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "fixture.predecision.expected_net_r",
            "probability": "fixture.predecision.probability",
            "fill_probability": "fixture.predecision.fill_probability",
            "source_completeness": "fixture.predecision.source_completeness",
        },
        "candidate_decision_quality_source_boundary": "predecision_fixture",
        "candidate_decision_quality_alias_status": "exact_materialized",
        "selected_policy_for_expected_net_r": "momentum_exhaustion",
        "selected_policy_expected_net_calibration_status": "calibrated",
        "selected_policy_expected_net_calibrated": True,
        "selected_policy_expected_net_calibration_source": (
            "selected_policy_replay_calibration_packet"
        ),
        "selected_policy_expected_net_calibration_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        "source_window_complete": True,
    }
    candidate.update(timewarp.ultimate_package_member_axis_parity_fields(candidate))
    source_required_config = {
        "gtos_vnext_runtime": {
            "scheduler_v4_best_trade_allocator_source_required_fail_closed_package_replay_override_enabled": True,
            "scheduler_v4_best_trade_allocator_source_required_fail_closed_package_replay_override_allow_new_position_without_same_side_context_enabled": True,
            "scheduler_v4_best_trade_allocator_source_required_fail_closed_package_replay_override_min_expected_net_r": 0.55,
            "scheduler_v4_best_trade_allocator_source_required_fail_closed_package_replay_override_min_probability": 0.70,
            "scheduler_v4_best_trade_allocator_source_required_fail_closed_package_replay_override_min_fill_probability": 0.80,
            "scheduler_v4_best_trade_allocator_source_required_fail_closed_package_replay_override_min_source_completeness": 0.95,
            "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk_allowed": True,
            "ultimate_candidate_package_source_bound_router_refusal_open_reduced_materialization_enabled": True,
        }
    }
    _attach_signed_open_reduced_authority(
        candidate,
        selector_packet,
        reason=selector_reason,
        decision_time=decision_time,
        authority_family="router_refusal_softening",
        authority_overrides={
            "authority_source": (
                "derived_from_source_bound_router_refusal_package_authority"
            ),
            "source_bound_router_refusal_materialization_floors": {
                "expected_net_r": 0.55,
                "probability": 0.70,
                "fill_probability": 0.80,
                "source_completeness": 0.95,
            },
        },
        config=source_required_config,
    )
    packets = {
        f"candidate-source-required-router@@{decision_time}": {
            "selector_packet": selector_packet,
            "probability_packet": {
                "theses": [{"action": "long", "probability": 0.72, "EV": 0.67}]
            },
            "lifecycle_packet": {"action": "source_required_fail_closed"},
            "selector_event": {
                "predecision_limit_fillability": {"fill_probability": 0.86}
            },
            "pretrade_broker_net_cost_packet": _cost_packet(),
            "expected_net_r": 0.62,
            "fill_probability": 0.86,
            "candidate_fill_probability": 0.86,
        }
    }

    timewarp.materialize_scheduler_window(
        asof_utc=decision_time,
        candidates=[candidate],
        v4_packets=packets,
        config=source_required_config,
    )

    scheduler_candidates = captured["window"]["candidates"]
    assert len(scheduler_candidates) == 1
    row = scheduler_candidates[0]
    assert row["candidate_id"] == "candidate-source-required-router"
    assert row["action_intent"] == "new_position"
    assert (
        row["scheduler_materialization_source_required_fail_closed_override_applied"]
        is True
    )
    assert row["scheduler_materialization_override_reason"] == (
        "source_required_fail_closed_package_new_position_source_gap_reconciled_for_replay"
    )
    assert row["package_new_entry_authority_valid"] is True, row[
        "package_new_entry_authority_failures"
    ]
    assert (
        row["package_new_entry_authority_target_action_intent"]
        == "new_position"
    )
    assert row["package_new_entry_authority_selector_reason"] == selector_reason
    assert row["package_open_reduced_authority_family"] == "router_refusal_softening"
    assert row["package_replay_executable_candidate_use_allowed"] is True
    assert row["replay_candidate_use_allowed_now"] is True


def test_source_required_fail_closed_derives_reduce_risk_authority_in_own_namespace(
    monkeypatch,
) -> None:
    captured = {}

    def fake_allocate(window, config, *, raw_config=None):
        captured["window"] = window
        return {
            "selected_candidate_id": "candidate-source-required-reduce",
            "selected_candidate_ids": ["candidate-source-required-reduce"],
            "option_trace": [],
        }

    monkeypatch.setattr(timewarp, "allocate_decision_window", fake_allocate)
    decision_time = "2025-06-11T08:30:00+00:00"
    selector_reason = "source_bound_router_refusal_open_reduced_materialized_for_replay"
    selector_packet = _selector_packet(selector_reason, action="reduce-risk")
    selector_packet["component_scores"]["ultimate_candidate_package"][
        "admission_sleeve_match_count"
    ] = 1
    candidate = {
        "candidate_id": "candidate-source-required-reduce",
        "symbol": "XAUUSD",
        "side": "LONG",
        "risk_reward_ratio": 2.0,
        "decision_time_utc": decision_time,
        "source_bound_package_candidate_use_allowed": True,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed_reason": (
            "source_bound_package_candidate_executable"
        ),
        "expected_net_r": 0.91,
        "candidate_expected_net_r": 0.91,
        "probability": 0.78,
        "candidate_probability": 0.78,
        "fill_probability": 0.86,
        "candidate_fill_probability": 0.86,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "source_window_complete": True,
        "selector_action": "reduce-risk",
        "selector_reason": selector_reason,
        "selected_policy_for_expected_net_r": "momentum_exhaustion",
        "selected_policy_expected_net_calibration_status": "calibrated",
        "selected_policy_expected_net_calibrated": True,
        "selected_policy_expected_net_calibration_required": True,
        "selected_policy_expected_net_calibration_source": (
            "selected_policy_replay_calibration_packet"
        ),
        "selected_policy_expected_net_calibration_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
    }
    _ensure_fixture_quality_aliases(candidate)
    _ensure_exact_package_member_axis_identity(candidate)
    _add_strict_limit_fillability(candidate, 0.86)
    selector_packet["component_scores"]["candidate_decision_inputs"] = dict(
        candidate
    )
    packets = {
        f"candidate-source-required-reduce@@{decision_time}": {
            "selector_packet": selector_packet,
            "probability_packet": {
                "theses": [
                    {
                        "action": "long",
                        "probability": 0.78,
                        "EV": 0.96,
                        "confidence": 0.7,
                    }
                ]
            },
            "lifecycle_packet": {"action": "source_required_fail_closed"},
            "selector_event": {
                "predecision_limit_fillability": {"fill_probability": 0.86}
            },
            "pretrade_broker_net_cost_packet": _cost_packet(),
            "expected_net_r": 0.91,
            "fill_probability": 0.86,
            "candidate_fill_probability": 0.86,
        }
    }
    config = {
        "gtos_vnext_runtime": {
            "scheduler_v4_best_trade_allocator_source_required_fail_closed_package_replay_override_enabled": True,
            "scheduler_v4_best_trade_allocator_source_required_fail_closed_package_replay_override_allow_new_position_without_same_side_context_enabled": True,
            "scheduler_v4_best_trade_allocator_source_required_fail_closed_package_replay_override_min_expected_net_r": 0.80,
            "scheduler_v4_best_trade_allocator_source_required_fail_closed_package_replay_override_min_probability": 0.75,
            "scheduler_v4_best_trade_allocator_source_required_fail_closed_package_replay_override_min_fill_probability": 0.25,
            "scheduler_v4_best_trade_allocator_source_required_fail_closed_package_replay_override_min_source_completeness": 0.95,
            "scheduler_v4_best_trade_allocator_selector_reduce_risk_router_refusal_package_new_entry_authority_enabled": True,
        }
    }

    timewarp.materialize_scheduler_window(
        asof_utc=decision_time,
        candidates=[candidate],
        v4_packets=packets,
        config=config,
    )

    scheduler_candidates = captured["window"]["candidates"]
    assert len(scheduler_candidates) == 1, "\n".join(
        f"{key}={value!r}"
        for key, value in sorted(candidate.items())
        if key.startswith("scheduler_materialization_")
        or key.startswith("package_new_entry_authority_")
        or key.startswith("package_reduce_risk_")
    )
    row = scheduler_candidates[0]
    assert row["action_intent"] == "new_position"
    assert row[
        "scheduler_materialization_source_required_fail_closed_override_applied"
    ] is True
    assert row["package_new_entry_authority_valid"] is True, row.get(
        "package_new_entry_authority_failures"
    )
    assert row["package_new_entry_authority_selector_action"] == "reduce-risk"
    assert row["package_new_entry_authority_authority_field"] == (
        "ultimate_candidate_package_reduce_risk_authority"
    )
    assert row["package_reduce_risk_authority_allowed"] is True
    assert row["ultimate_package_reduce_risk_authority_allowed"] is True
    assert isinstance(
        row["ultimate_candidate_package_reduce_risk_authority"],
        dict,
    )
    assert not row.get("ultimate_candidate_package_open_reduced_risk_authority")


def test_scheduler_signing_uses_selector_owned_source_bound_materialization_floors() -> None:
    contract = timewarp.selector_admission_materialization_floor_contract(
        {
            "component_scores": {
                "ultimate_candidate_package_router_refusal_release": {
                    "source_bound_materialization_quality_allowed": True,
                    "source_bound_materialization_min_expected_net_r": 0.55,
                    "source_bound_materialization_min_probability": 0.70,
                    "source_bound_materialization_min_fill_probability": 0.80,
                    "source_bound_materialization_min_source_completeness": 0.95,
                }
            }
        },
        {
            "selector_reduce_risk_package_fill_floor_min_expected_net_r": 0.90,
            "selector_reduce_risk_package_fill_floor_min_probability": 0.90,
            "selector_reduce_risk_package_fill_floor_min_fill_probability": 0.90,
            "selector_reduce_risk_package_fill_floor_min_source_completeness": 1.0,
        },
    )

    assert contract == {
        "floors": {
            "expected_net_r": 0.55,
            "probability": 0.70,
            "fill_probability": 0.80,
            "source_completeness": 0.95,
        },
        "source": "selector_v4.source_bound_router_refusal_materialization",
        "selector_owned": True,
    }


def test_source_required_fail_closed_package_replay_override_accepts_same_side_pending_context(
    monkeypatch,
) -> None:
    captured = {}

    def fake_allocate(window, config, *, raw_config=None):
        captured["window"] = window
        return {
            "selected_candidate_id": "candidate-source-required-pending-context",
            "selected_candidate_ids": ["candidate-source-required-pending-context"],
            "option_trace": [],
        }

    monkeypatch.setattr(timewarp, "allocate_decision_window", fake_allocate)
    decision_time = "2025-06-11T08:15:00+00:00"
    selector_packet = _selector_packet(
        "ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay",
        action="open-reduced-risk",
    )
    selector_packet["component_scores"]["ultimate_candidate_package"][
        "admission_sleeve_match_count"
    ] = 1
    candidate = {
        "candidate_id": "candidate-source-required-pending-context",
        "symbol": "XAUUSD",
        "side": "LONG",
        "risk_reward_ratio": 2.0,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "candidate_expected_net_r": 0.91,
        "probability": 0.78,
        "confidence": 0.82,
        "candidate_confidence": 0.82,
        "scheduler_confidence": 0.82,
        "fill_probability": 0.32,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "fixture.predecision.expected_net_r",
            "probability": "fixture.predecision.probability",
            "confidence": "fixture",
            "fill_probability": "fixture.predecision.fill_probability",
            "source_completeness": "fixture.predecision.source_completeness",
        },
        "candidate_decision_quality_alias_status": "exact_materialized",
        "candidate_decision_quality_source_boundary": "predecision_fixture",
        "source_window_complete": True,
    }
    _attach_signed_open_reduced_authority(
        candidate,
        selector_packet,
        reason="ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay",
        decision_time=decision_time,
        action_intent="same_direction_scale_in",
    )
    packets = {
        f"candidate-source-required-pending-context@@{decision_time}": {
            "selector_packet": selector_packet,
            "probability_packet": {
                "theses": [{"action": "long", "probability": 0.78, "EV": 0.96}]
            },
            "lifecycle_packet": {"action": "source_required_fail_closed"},
            "selector_event": {
                "predecision_limit_fillability": {"fill_probability": 0.32}
            },
            "pretrade_broker_net_cost_packet": _cost_packet(),
            "expected_net_r": 0.91,
        }
    }

    timewarp.materialize_scheduler_window(
        asof_utc=decision_time,
        candidates=[candidate],
        v4_packets=packets,
        pending_orders=[
            {
                "symbol": "XAUUSD",
                "side": "LONG",
                "reserved_risk_pct": 0.05,
                "order_status": "pending_accepted",
            }
        ],
        config={
            "gtos_vnext_runtime": {
                "scheduler_v4_best_trade_allocator_source_required_fail_closed_package_replay_override_enabled": True,
                "scheduler_v4_best_trade_allocator_source_required_package_duplicate_scale_in_enabled": True,
            }
        },
    )

    row = captured["window"]["candidates"][0]
    assert row["candidate_id"] == "candidate-source-required-pending-context"
    assert row["action_intent"] == "replace_pending"
    assert row["same_symbol_lifecycle_action"] == "replace_pending"
    assert (
        row[
            "scheduler_materialization_source_required_fail_closed_override_applied"
        ]
        is True
    )
    assert (
        row[
            "scheduler_materialization_source_required_fail_closed_same_side_open_position"
        ]
        is False
    )
    assert (
        row[
            "scheduler_materialization_source_required_fail_closed_lifecycle_context_present"
        ]
        is True
    )
    assert (
        row[
            "scheduler_materialization_source_required_fail_closed_lifecycle_context_source"
        ]
        == "pending_order"
    )
    assert (
        row["scheduler_materialization_source_required_fail_closed_lifecycle_context"]
        == "same_side_pending_replace_pending_context"
    )
    assert row["package_replay_executable_candidate_use_allowed"] is True
    assert row["package_replay_executable_candidate_use_allowed_reason"] == (
        "broker_cost_and_scheduler_action_executable"
    )
    assert row["replay_candidate_use_allowed_now"] is True


def test_source_required_fail_closed_package_replay_override_accepts_opposite_open_context(
    monkeypatch,
) -> None:
    captured = {}

    def fake_allocate(window, config, *, raw_config=None):
        captured["window"] = window
        return {
            "selected_candidate_id": "candidate-source-required-close-reverse",
            "selected_candidate_ids": ["candidate-source-required-close-reverse"],
            "option_trace": [],
        }

    monkeypatch.setattr(timewarp, "allocate_decision_window", fake_allocate)
    decision_time = "2025-06-11T08:15:00+00:00"
    selector_packet = _selector_packet(
        "ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay",
        action="open-reduced-risk",
    )
    selector_packet["component_scores"]["ultimate_candidate_package"][
        "admission_sleeve_match_count"
    ] = 1
    candidate = {
        "candidate_id": "candidate-source-required-close-reverse",
        "symbol": "XAUUSD",
        "side": "LONG",
        "risk_reward_ratio": 2.0,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "candidate_expected_net_r": 0.91,
        "probability": 0.78,
        "fill_probability": 0.32,
        "source_completeness": 1.0,
        "source_window_complete": True,
    }
    _add_strict_limit_fillability(candidate, 0.32)
    _attach_signed_open_reduced_authority(
        candidate,
        selector_packet,
        reason="ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay",
        decision_time=decision_time,
        action_intent="close_and_reverse",
    )
    packets = {
        f"candidate-source-required-close-reverse@@{decision_time}": {
            "selector_packet": selector_packet,
            "probability_packet": {
                "theses": [{"action": "long", "probability": 0.78, "EV": 0.96}]
            },
            "lifecycle_packet": {"action": "source_required_fail_closed"},
            "selector_event": {
                "predecision_limit_fillability": {"fill_probability": 0.32}
            },
            "pretrade_broker_net_cost_packet": _cost_packet(),
            "expected_net_r": 0.91,
        }
    }

    timewarp.materialize_scheduler_window(
        asof_utc=decision_time,
        candidates=[candidate],
        v4_packets=packets,
        open_positions=[
            {
                "symbol": "XAUUSD",
                "side": "SHORT",
                "risk_pct": 0.05,
            }
        ],
        config={
            "gtos_vnext_runtime": {
                "scheduler_v4_best_trade_allocator_source_required_fail_closed_package_replay_override_enabled": True,
                "scheduler_v4_best_trade_allocator_package_opposite_side_close_reverse_enabled": True,
            }
        },
    )

    row = captured["window"]["candidates"][0]
    assert row["candidate_id"] == "candidate-source-required-close-reverse"
    assert row["action_intent"] == "close_and_reverse"
    assert row["same_symbol_lifecycle_action"] == "close_and_reverse"
    assert row["scheduler_materialization_override_reason"] == (
        "source_required_fail_closed_package_close_reverse_reconciled_for_replay"
    )
    assert (
        row["scheduler_materialization_source_required_fail_closed_lifecycle_context"]
        == "opposite_open_close_and_reverse_context"
    )
    assert (
        row[
            "scheduler_materialization_source_required_fail_closed_lifecycle_context_source"
        ]
        == "same_symbol_replay_exposure_context"
    )


def test_source_required_fail_closed_package_replay_override_accepts_opposite_pending_context(
    monkeypatch,
) -> None:
    captured = {}

    def fake_allocate(window, config, *, raw_config=None):
        captured["window"] = window
        return {
            "selected_candidate_id": "candidate-source-required-replace-pending",
            "selected_candidate_ids": ["candidate-source-required-replace-pending"],
            "option_trace": [],
        }

    monkeypatch.setattr(timewarp, "allocate_decision_window", fake_allocate)
    decision_time = "2025-06-11T08:15:00+00:00"
    selector_packet = _selector_packet(
        "ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay",
        action="open-reduced-risk",
    )
    selector_packet["component_scores"]["ultimate_candidate_package"][
        "admission_sleeve_match_count"
    ] = 1
    candidate = {
        "candidate_id": "candidate-source-required-replace-pending",
        "symbol": "XAUUSD",
        "side": "LONG",
        "risk_reward_ratio": 2.0,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "candidate_expected_net_r": 0.91,
        "probability": 0.78,
        "fill_probability": 0.32,
        "source_completeness": 1.0,
        "source_window_complete": True,
    }
    _attach_signed_open_reduced_authority(
        candidate,
        selector_packet,
        reason="ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay",
        decision_time=decision_time,
        action_intent="replace_pending",
    )
    _add_strict_limit_fillability(candidate, 0.32)
    packets = {
        f"candidate-source-required-replace-pending@@{decision_time}": {
            "selector_packet": selector_packet,
            "probability_packet": {
                "theses": [{"action": "long", "probability": 0.78, "EV": 0.96}]
            },
            "lifecycle_packet": {"action": "source_required_fail_closed"},
            "selector_event": {
                "predecision_limit_fillability": {"fill_probability": 0.32}
            },
            "pretrade_broker_net_cost_packet": _cost_packet(),
            "expected_net_r": 0.91,
        }
    }

    timewarp.materialize_scheduler_window(
        asof_utc=decision_time,
        candidates=[candidate],
        v4_packets=packets,
        pending_orders=[
            {
                "symbol": "XAUUSD",
                "side": "SHORT",
                "reserved_risk_pct": 0.05,
                "order_status": "pending_accepted",
            }
        ],
        config={
            "gtos_vnext_runtime": {
                "scheduler_v4_best_trade_allocator_source_required_fail_closed_package_replay_override_enabled": True,
                "scheduler_v4_best_trade_allocator_package_opposite_side_close_reverse_enabled": True,
            }
        },
    )

    row = captured["window"]["candidates"][0]
    assert row["candidate_id"] == "candidate-source-required-replace-pending"
    assert row["action_intent"] == "replace_pending"
    assert row["same_symbol_lifecycle_action"] == "replace_pending"
    assert row["scheduler_materialization_override_reason"] == (
        "source_required_fail_closed_package_replace_pending_reconciled_for_replay"
    )
    assert (
        row["scheduler_materialization_source_required_fail_closed_lifecycle_context"]
        == "opposite_pending_replace_context"
    )
    assert (
        row[
            "scheduler_materialization_source_required_fail_closed_lifecycle_context_source"
        ]
        == "same_symbol_replay_exposure_context"
    )


def test_replay_lifecycle_resolver_derives_same_direction_scale_in(monkeypatch) -> None:
    captured = {}

    def fake_allocate(window, config, *, raw_config=None):
        captured["window"] = window
        return {
            "selected_candidate_id": "candidate-scale-resolver",
            "selected_candidate_ids": ["candidate-scale-resolver"],
            "option_trace": [],
        }

    monkeypatch.setattr(timewarp, "allocate_decision_window", fake_allocate)
    decision_time = "2025-06-11T08:15:00+00:00"
    selector_packet = _selector_packet("broker_net_probability_confluence_pass", action="trade")
    selector_packet["component_scores"]["ultimate_candidate_package"][
        "admission_sleeve_match_count"
    ] = 1
    candidate = {
        "candidate_id": "candidate-scale-resolver",
        "symbol": "XAUUSD",
        "side": "LONG",
        "risk_reward_ratio": 2.0,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "candidate_expected_net_r": 0.91,
        "probability": 0.79,
        "candidate_probability": 0.79,
        "fill_probability": 0.32,
        "candidate_fill_probability": 0.32,
        "source_window_complete": True,
    }
    _add_strict_limit_fillability(candidate, 0.32)
    _attach_signed_open_reduced_authority(
        candidate,
        selector_packet,
        reason="broker_net_probability_confluence_pass",
        decision_time=decision_time,
        action_intent="same_direction_scale_in",
    )
    packets = {
        f"candidate-scale-resolver@@{decision_time}": {
            "selector_packet": selector_packet,
            "probability_packet": {
                "theses": [{"action": "long", "probability": 0.79, "EV": 0.96}]
            },
            "lifecycle_packet": {"action": "new_position"},
            "selector_event": {
                "predecision_limit_fillability": {"fill_probability": 0.32}
            },
            "pretrade_broker_net_cost_packet": _cost_packet(),
            "expected_net_r": 0.91,
        }
    }

    timewarp.materialize_scheduler_window(
        asof_utc=decision_time,
        candidates=[candidate],
        v4_packets=packets,
        open_positions=[
            {
                "position_id": "open-long",
                "symbol": "XAUUSD",
                "side": "LONG",
                "risk_pct": 0.15,
            }
        ],
        config={
            "gtos_vnext_runtime": {
                "scheduler_v4_best_trade_allocator_replay_lifecycle_action_resolver_enabled": True,
                "scheduler_v4_best_trade_allocator_source_required_package_duplicate_scale_in_enabled": True,
                "scheduler_v4_best_trade_allocator_source_required_package_duplicate_scale_in_min_fill_probability": 0.12,
            }
        },
    )

    row = captured["window"]["candidates"][0]
    assert row["action_intent"] == "same_direction_scale_in"
    assert row["same_symbol_lifecycle_action"] == "same_direction_scale_in"
    assert row["scheduler_materialization_replay_lifecycle_action_resolver_applied"] is True
    assert row["scheduler_materialization_replay_lifecycle_action_resolver_reason"] == (
        "replay_lifecycle_action_resolver_same_direction_scale_in"
    )
    assert row["same_symbol_lifecycle_exposure_risk_pct"] == 0.15
    assert row["same_symbol_replay_exposure_context"]["same_side_open_count"] == 1


def test_replay_lifecycle_resolver_router_scale_in_cannot_bypass_signed_floors(
    monkeypatch,
) -> None:
    captured = {}

    def fake_allocate(window, config, *, raw_config=None):
        captured["window"] = window
        return {
            "selected_candidate_id": "candidate-router-scale-resolver",
            "selected_candidate_ids": ["candidate-router-scale-resolver"],
            "option_trace": [],
        }

    monkeypatch.setattr(timewarp, "allocate_decision_window", fake_allocate)
    decision_time = "2025-06-11T08:15:00+00:00"
    legacy_reason = "admission_quality_dynamic_router_refused_candidate_use"
    canonical_reason = (
        "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk"
    )
    selector_packet = _selector_packet(legacy_reason, action="open-reduced-risk")
    selector_packet["component_scores"][
        "ultimate_candidate_package_open_reduced_risk_authority"
    ] = {
        "applies": False,
        "allowed": False,
        "selector_reason": legacy_reason,
        "source_boundary": (
            "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
        ),
    }
    candidate = {
        "candidate_id": "candidate-router-scale-resolver",
        "symbol": "XAUUSD",
        "side": "LONG",
        "risk_reward_ratio": 2.0,
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": (
            f"candidate-router-scale-resolver@@{decision_time}"
        ),
        "source_bound_replay_candidate_instance_key": (
            f"candidate-router-scale-resolver@@{decision_time}"
        ),
        "candidate_instance_identity_status": "materialized",
        "source_bound_package_candidate_use_allowed": True,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_source_bound_candidate_use_allowed": True,
        "ultimate_package_admission_candidate_use_allowed": True,
        "ultimate_package_effective_admission_count": 1,
        "ultimate_package_effective_matched_count": 1,
        "ultimate_package_scheduler_consumed_status": (
            "eligible_for_scheduler_consumption"
        ),
        "candidate_expected_net_r": 0.96,
        "expected_net_r": 0.96,
        "probability": 0.79,
        "candidate_probability": 0.79,
        "fill_probability": 0.32,
        "candidate_fill_probability": 0.32,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "fixture.predecision.expected_net_r",
            "probability": "fixture.predecision.probability",
            "fill_probability": "fixture.predecision.fill_probability",
            "source_completeness": "fixture.predecision.source_completeness",
        },
        "candidate_decision_quality_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        "candidate_decision_quality_alias_status": "exact_materialized",
        "selected_policy_for_expected_net_r": "momentum_exhaustion",
        "selected_policy_expected_net_calibration_status": (
            "calibrated"
        ),
        "selected_policy_expected_net_calibrated": True,
        "selected_policy_expected_net_calibration_source": (
            "selected_policy_replay_calibration_packet"
        ),
        "selected_policy_expected_net_calibration_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "candidate_cost_r_fallback_is_authority": False,
    }
    _add_strict_limit_fillability(candidate, 0.18)
    packets = {
        f"candidate-router-scale-resolver@@{decision_time}": {
            "selector_packet": selector_packet,
            "probability_packet": {
                "theses": [{"action": "long", "probability": 0.79, "EV": 1.01}]
            },
            "lifecycle_packet": {"action": "new_position"},
            "selector_event": {
                "predecision_limit_fillability": {"fill_probability": 0.32}
            },
            "pretrade_broker_net_cost_packet": _cost_packet(),
            "expected_net_r": 0.96,
            "candidate_expected_net_r": 0.96,
            "candidate_probability": 0.79,
        }
    }

    timewarp.materialize_scheduler_window(
        asof_utc=decision_time,
        candidates=[candidate],
        v4_packets=packets,
        open_positions=[
            {
                "position_id": "open-long",
                "symbol": "XAUUSD",
                "side": "LONG",
                "risk_pct": 0.15,
            }
        ],
        config={
            "gtos_vnext_runtime": {
                "scheduler_v4_best_trade_allocator_replay_lifecycle_action_resolver_enabled": True,
                "scheduler_v4_best_trade_allocator_source_required_package_duplicate_scale_in_enabled": True,
                "scheduler_v4_best_trade_allocator_source_required_package_duplicate_scale_in_min_fill_probability": 0.12,
                "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk_allowed": True,
            }
        },
    )

    assert captured["window"]["candidates"] == []
    assert (
        candidate["scheduler_materialization_replay_lifecycle_action_resolver_applied"]
        is False
    )
    assert any(
        "router_refusal_same_direction_scale_in_floor_override_forbidden"
        in str(failure)
        for failure in candidate[
            "scheduler_materialization_replay_lifecycle_action_resolver_failures"
        ]
    )
    assert candidate["scheduler_materialization_skip_reason"].startswith(
        "package_lifecycle_action_resolution_required:"
    )
    assert candidate["scheduler_materialization_action_intent"] == (
        "same_direction_scale_in"
    )


def test_replay_lifecycle_resolver_derives_source_bound_fill_floor_scale_in_authority(
    monkeypatch,
) -> None:
    captured = {}

    def fake_allocate(window, config, *, raw_config=None):
        captured["window"] = window
        return {
            "selected_candidate_id": "candidate-fill-floor-scale-resolver",
            "selected_candidate_ids": ["candidate-fill-floor-scale-resolver"],
            "option_trace": [],
        }

    monkeypatch.setattr(timewarp, "allocate_decision_window", fake_allocate)
    decision_time = "2025-06-11T08:15:00+00:00"
    legacy_reason = "calibrated_admission_fill_probability_below_generalized_floor"
    materialized_reason = "source_bound_fill_floor_package_materialized_for_replay"
    selector_packet = _selector_packet(legacy_reason, action="reject")
    selector_packet["component_scores"][
        "ultimate_candidate_package_open_reduced_risk_authority"
    ] = {
        "applies": False,
        "allowed": False,
        "selector_reason": legacy_reason,
        "source_boundary": (
            "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
        ),
    }
    candidate = {
        "candidate_id": "candidate-fill-floor-scale-resolver",
        "symbol": "XAUUSD",
        "side": "LONG",
        "risk_reward_ratio": 2.0,
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": (
            f"candidate-fill-floor-scale-resolver@@{decision_time}"
        ),
        "source_bound_replay_candidate_instance_key": (
            f"candidate-fill-floor-scale-resolver@@{decision_time}"
        ),
        "candidate_instance_identity_status": "materialized",
        "source_bound_package_candidate_use_allowed": True,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_source_bound_candidate_use_allowed": True,
        "ultimate_package_admission_candidate_use_allowed": True,
        "ultimate_package_admission_sleeve_match_count": 1,
        "ultimate_package_matched_sleeve_count": 1,
        "ultimate_package_effective_admission_count": 1,
        "ultimate_package_effective_matched_count": 1,
        "ultimate_package_effective_source_bound_signal_r": 120.0,
        "ultimate_package_combined_source_bound_signal_r_sum": 120.0,
        "ultimate_package_scheduler_consumed_status": (
            "eligible_for_scheduler_consumption"
        ),
        "candidate_expected_net_r": 0.82,
        "expected_net_r": 0.82,
        "probability": 0.76,
        "candidate_probability": 0.76,
        "fill_probability": 0.18,
        "candidate_fill_probability": 0.18,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "fixture.predecision.expected_net_r",
            "probability": "fixture.predecision.probability",
            "fill_probability": "fixture.predecision.fill_probability",
            "source_completeness": "fixture.predecision.source_completeness",
        },
        "candidate_decision_quality_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        "candidate_decision_quality_alias_status": "exact_materialized",
        "selected_policy_for_expected_net_r": "momentum_exhaustion",
        "selected_policy_expected_net_calibration_status": "calibrated",
        "selected_policy_expected_net_calibrated": True,
        "selected_policy_expected_net_calibration_source": (
            "selected_policy_replay_calibration_packet"
        ),
        "selected_policy_expected_net_calibration_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "candidate_cost_r_fallback_is_authority": False,
    }
    _add_strict_limit_fillability(candidate, 0.18)
    packets = {
        f"candidate-fill-floor-scale-resolver@@{decision_time}": {
            "selector_packet": selector_packet,
            "probability_packet": {
                "theses": [{"action": "long", "probability": 0.76, "EV": 0.87}]
            },
            "lifecycle_packet": {"action": "new_position"},
            "selector_event": {
                "predecision_limit_fillability": {"fill_probability": 0.18}
            },
            "pretrade_broker_net_cost_packet": _cost_packet(),
            "expected_net_r": 0.82,
            "candidate_expected_net_r": 0.82,
            "candidate_probability": 0.76,
        }
    }

    timewarp.materialize_scheduler_window(
        asof_utc=decision_time,
        candidates=[candidate],
        v4_packets=packets,
        open_positions=[
            {
                "position_id": "open-long",
                "symbol": "XAUUSD",
                "side": "LONG",
                "risk_pct": 0.15,
            }
        ],
        config={
            "gtos_vnext_runtime": {
                "scheduler_v4_best_trade_allocator_replay_lifecycle_action_resolver_enabled": True,
                "scheduler_v4_best_trade_allocator_source_required_package_duplicate_scale_in_enabled": True,
                "scheduler_v4_best_trade_allocator_source_required_package_duplicate_scale_in_min_expected_net_r": 0.75,
                "scheduler_v4_best_trade_allocator_source_required_package_duplicate_scale_in_min_probability": 0.75,
                "scheduler_v4_best_trade_allocator_source_required_package_duplicate_scale_in_min_fill_probability": 0.12,
                "scheduler_v4_best_trade_allocator_source_required_package_duplicate_scale_in_min_source_completeness": 0.95,
                "scheduler_v4_best_trade_allocator_source_bound_fill_floor_replay_materialization_enabled": True,
                "scheduler_v4_best_trade_allocator_source_bound_fill_floor_replay_materialization_min_expected_net_r": 0.70,
                "scheduler_v4_best_trade_allocator_source_bound_fill_floor_replay_materialization_min_probability": 0.70,
                "scheduler_v4_best_trade_allocator_source_bound_fill_floor_replay_materialization_min_fill_probability": 0.05,
                "scheduler_v4_best_trade_allocator_source_bound_fill_floor_replay_materialization_min_source_completeness": 0.95,
            }
        },
    )

    row = captured["window"]["candidates"][0]
    assert row["action_intent"] == "same_direction_scale_in"
    assert row["same_symbol_lifecycle_action"] == "same_direction_scale_in"
    assert row["scheduler_materialization_replay_lifecycle_action_resolver_applied"] is True
    assert row["scheduler_materialization_replay_lifecycle_action_resolver_reason"] == (
        "replay_lifecycle_action_resolver_same_direction_scale_in"
    )
    assert row["selector_reason"] == materialized_reason
    assert row["scheduler_materialization_selector_reason"] == materialized_reason
    assert row["scheduler_materialization_selector_reason_normalized_from"] == legacy_reason
    assert row["package_open_reduced_authority_allowed"] is True
    assert row["package_open_reduced_authority_family"] == (
        "source_bound_fill_floor_replay_materialization"
    )
    assert (
        row["package_new_entry_authority_target_action_intent"]
        == "same_direction_scale_in"
    )
    assert row["package_new_entry_authority_valid"] is True
    assert (
        row["ultimate_candidate_package_open_reduced_risk_authority"]["selector_reason"]
        == materialized_reason
    )


def test_replay_lifecycle_resolver_derives_close_and_reverse(monkeypatch) -> None:
    captured = {}

    def fake_allocate(window, config, *, raw_config=None):
        captured["window"] = window
        return {
            "selected_candidate_id": "candidate-reverse-resolver",
            "selected_candidate_ids": ["candidate-reverse-resolver"],
            "option_trace": [],
        }

    monkeypatch.setattr(timewarp, "allocate_decision_window", fake_allocate)
    decision_time = "2025-06-11T08:15:00+00:00"
    selector_packet = _selector_packet("broker_net_probability_confluence_pass", action="trade")
    selector_packet["component_scores"]["ultimate_candidate_package"][
        "admission_sleeve_match_count"
    ] = 1
    candidate = {
        "candidate_id": "candidate-reverse-resolver",
        "symbol": "XAUUSD",
        "side": "LONG",
        "risk_reward_ratio": 2.0,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "candidate_expected_net_r": 0.91,
        "probability": 0.79,
        "candidate_probability": 0.79,
        "fill_probability": 0.32,
        "candidate_fill_probability": 0.32,
        "source_window_complete": True,
    }
    _add_strict_limit_fillability(candidate, 0.32)
    _attach_signed_open_reduced_authority(
        candidate,
        selector_packet,
        reason="broker_net_probability_confluence_pass",
        decision_time=decision_time,
        action_intent="close_and_reverse",
    )
    packets = {
        f"candidate-reverse-resolver@@{decision_time}": {
            "selector_packet": selector_packet,
            "probability_packet": {
                "theses": [{"action": "long", "probability": 0.79, "EV": 0.96}]
            },
            "lifecycle_packet": {"action": "new_position"},
            "selector_event": {
                "predecision_limit_fillability": {"fill_probability": 0.32}
            },
            "pretrade_broker_net_cost_packet": _cost_packet(),
            "expected_net_r": 0.91,
        }
    }

    timewarp.materialize_scheduler_window(
        asof_utc=decision_time,
        candidates=[candidate],
        v4_packets=packets,
        open_positions=[
            {
                "position_id": "open-short",
                "symbol": "XAUUSD",
                "side": "SHORT",
                "risk_pct": 0.22,
            }
        ],
        config={
            "gtos_vnext_runtime": {
                "scheduler_v4_best_trade_allocator_replay_lifecycle_action_resolver_enabled": True,
                "scheduler_v4_best_trade_allocator_package_opposite_side_close_reverse_enabled": True,
            }
        },
    )

    row = captured["window"]["candidates"][0]
    assert row["action_intent"] == "close_and_reverse"
    assert row["same_symbol_lifecycle_action"] == "close_and_reverse"
    assert row["scheduler_materialization_replay_lifecycle_action_resolver_applied"] is True
    assert row["scheduler_materialization_replay_lifecycle_action_resolver_reason"] == (
        "replay_lifecycle_action_resolver_close_and_reverse"
    )
    assert row["same_symbol_lifecycle_exposure_risk_pct"] == 0.22
    assert row["same_symbol_replay_exposure_context"]["opposite_open_count"] == 1


def test_replay_lifecycle_resolver_blocks_unresolved_refused_cost_new_position(
    monkeypatch,
) -> None:
    captured = {}

    def fake_allocate(window, config, *, raw_config=None):
        captured["window"] = window
        return {
            "selected_candidate_id": None,
            "selected_candidate_ids": [],
            "option_trace": [],
        }

    monkeypatch.setattr(timewarp, "allocate_decision_window", fake_allocate)
    selector_packet = _selector_packet("broker_net_probability_confluence_pass", action="trade")
    selector_packet["component_scores"]["ultimate_candidate_package"][
        "admission_sleeve_match_count"
    ] = 1
    candidate = {
        "candidate_id": "candidate-scale-cost-refused",
        "symbol": "XAUUSD",
        "side": "LONG",
        "risk_reward_ratio": 2.0,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "candidate_expected_net_r": 0.91,
        "source_window_complete": True,
    }
    packets = {
        "candidate-scale-cost-refused": {
            "selector_packet": selector_packet,
            "probability_packet": {
                "theses": [{"action": "long", "probability": 0.79, "EV": 0.96}]
            },
            "lifecycle_packet": {"action": "new_position"},
            "selector_event": {
                "predecision_limit_fillability": {"fill_probability": 0.32}
            },
            "pretrade_broker_net_cost_packet": _cost_packet("REFUSED"),
            "expected_net_r": 0.91,
        }
    }

    timewarp.materialize_scheduler_window(
        asof_utc="2025-06-11T08:15:00+00:00",
        candidates=[candidate],
        v4_packets=packets,
        open_positions=[
            {
                "position_id": "open-long",
                "symbol": "XAUUSD",
                "side": "LONG",
                "risk_pct": 0.15,
            }
        ],
        config={
            "gtos_vnext_runtime": {
                "scheduler_v4_best_trade_allocator_replay_lifecycle_action_resolver_enabled": True,
                "scheduler_v4_best_trade_allocator_source_required_package_duplicate_scale_in_enabled": True,
                "scheduler_v4_best_trade_allocator_source_required_package_duplicate_scale_in_min_fill_probability": 0.12,
            }
        },
    )

    assert captured["window"]["candidates"] == []
    assert candidate["scheduler_materialization_skip_reason"] == (
        "package_lifecycle_action_resolution_required:broker_cost_packet_refused:unspecified"
    )
    assert (
        candidate["scheduler_materialization_lifecycle_action_resolution_required"]
        is True
    )
    assert (
        candidate["scheduler_materialization_replay_lifecycle_action_resolver_applied"]
        is False
    )
    assert any(
        "broker_cost_packet_refused" in str(failure)
        for failure in candidate[
            "scheduler_materialization_replay_lifecycle_action_resolver_failures"
        ]
    )


def test_source_required_fail_closed_package_replay_override_allows_no_context_new_position_when_enabled(
    monkeypatch,
) -> None:
    captured = {}

    def fake_allocate(window, config, *, raw_config=None):
        captured["window"] = window
        return {
            "selected_candidate_id": "candidate-source-required-no-context",
            "selected_candidate_ids": ["candidate-source-required-no-context"],
            "option_trace": [],
        }

    monkeypatch.setattr(timewarp, "allocate_decision_window", fake_allocate)
    decision_time = "2025-06-11T08:15:00+00:00"
    selector_packet = _selector_packet(
        "ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay",
        action="open-reduced-risk",
    )
    selector_packet["component_scores"]["ultimate_candidate_package"][
        "admission_sleeve_match_count"
    ] = 1
    candidate = {
        "candidate_id": "candidate-source-required-no-context",
        "symbol": "XAUUSD",
        "side": "LONG",
        "risk_reward_ratio": 2.0,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "candidate_expected_net_r": 0.91,
        "probability": 0.78,
        "confidence": 0.82,
        "candidate_confidence": 0.82,
        "scheduler_confidence": 0.82,
        "fill_probability": 0.32,
        "source_completeness": 1.0,
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "fixture.predecision.expected_net_r",
            "probability": "fixture.predecision.probability",
            "confidence": "fixture",
            "fill_probability": "fixture.predecision.fill_probability",
            "source_completeness": "fixture.predecision.source_completeness",
        },
        "candidate_decision_quality_alias_status": "exact_materialized",
        "candidate_decision_quality_source_boundary": "predecision_fixture",
        "source_window_complete": True,
    }
    _attach_signed_open_reduced_authority(
        candidate,
        selector_packet,
        reason="ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay",
        decision_time=decision_time,
        action_intent="new_position",
    )
    packets = {
        f"candidate-source-required-no-context@@{decision_time}": {
            "selector_packet": selector_packet,
            "probability_packet": {
                "theses": [{"action": "long", "probability": 0.78, "EV": 0.96}]
            },
            "lifecycle_packet": {"action": "source_required_fail_closed"},
            "selector_event": {
                "predecision_limit_fillability": {"fill_probability": 0.32}
            },
            "pretrade_broker_net_cost_packet": _cost_packet(),
            "expected_net_r": 0.91,
        }
    }

    timewarp.materialize_scheduler_window(
        asof_utc=decision_time,
        candidates=[candidate],
        v4_packets=packets,
        config={
            "gtos_vnext_runtime": {
                "scheduler_v4_best_trade_allocator_source_required_fail_closed_package_replay_override_enabled": True,
                "scheduler_v4_best_trade_allocator_source_required_fail_closed_package_replay_override_allow_new_position_without_same_side_context_enabled": True,
            }
        },
    )

    scheduler_candidates = captured["window"]["candidates"]
    assert len(scheduler_candidates) == 1
    row = scheduler_candidates[0]
    assert row["candidate_id"] == "candidate-source-required-no-context"
    assert row["action_intent"] == "new_position"
    assert (
        row[
            "scheduler_materialization_source_required_fail_closed_override_applied"
        ]
        is True
    )
    assert (
        row[
            "scheduler_materialization_source_required_fail_closed_same_side_open_position"
        ]
        is False
    )
    assert (
        row[
            "scheduler_materialization_source_required_fail_closed_allow_new_position_without_same_side_context"
        ]
        is True
    )
    assert row[
        "scheduler_materialization_source_required_fail_closed_lifecycle_context"
    ] == "new_position_without_same_symbol_exposure_context"
    assert row["scheduler_materialization_override_reason"] == (
        "source_required_fail_closed_package_new_position_source_gap_reconciled_for_replay"
    )
    assert row["package_replay_executable_candidate_use_allowed"] is True
    assert row["package_replay_executable_candidate_use_allowed_reason"] == (
        "broker_cost_and_scheduler_action_executable"
    )
    assert row["replay_candidate_use_allowed_now"] is True
    assert row["replay_candidate_use_allowed_now_reason"] == (
        "source_required_fail_closed_package_replay_override_applied"
    )


def test_order_materialization_authority_recomputes_source_required_override() -> None:
    selector_packet = _selector_packet(
        "ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay",
        action="open-reduced-risk",
    )
    selector_packet["component_scores"]["ultimate_candidate_package"][
        "admission_sleeve_match_count"
    ] = 1
    candidate = {
        "candidate_id": "candidate-source-required-stale-exec-flag",
        "symbol": "XAUUSD",
        "side": "LONG",
        "decision_time_utc": "2025-06-11T08:15:00+00:00",
        "selector_action": "open-reduced-risk",
        "selector_reason": (
            "ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay"
        ),
        "lifecycle_action": "source_required_fail_closed",
        "same_symbol_lifecycle_action": "source_required_fail_closed",
        "scheduler_materialization_action_intent": "new_position",
        "scheduler_materialization_source_required_fail_closed_override_applied": True,
        "scheduler_materialization_override_reason": (
            "source_required_fail_closed_package_source_reconciled_for_replay"
        ),
        "source_required_fail_closed_replay_override_applied": True,
        "broker_lifecycle_truth_satisfied": True,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_source_bound_candidate_use_allowed": True,
        "ultimate_package_admission_candidate_use_allowed": True,
        "ultimate_package_effective_admission_count": 1,
        "ultimate_package_effective_matched_count": 1,
        "ultimate_package_scheduler_consumed_status": (
            "eligible_for_scheduler_consumption"
        ),
        "expected_net_r": 0.91,
        "candidate_expected_net_r": 0.91,
        "probability": 0.78,
        "confidence": 0.82,
        "candidate_confidence": 0.82,
        "scheduler_confidence": 0.82,
        "fill_probability": 0.32,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "fixture.predecision.expected_net_r",
            "probability": "fixture.predecision.probability",
            "confidence": "fixture",
            "fill_probability": "fixture.predecision.fill_probability",
            "source_completeness": "fixture.predecision.source_completeness",
        },
        "candidate_decision_quality_alias_status": "exact_materialized",
        "candidate_decision_quality_source_boundary": "predecision_fixture",
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "candidate_cost_r_fallback_is_authority": False,
        "package_replay_executable_candidate_use_allowed": False,
        "package_replay_executable_candidate_use_allowed_reason": (
            "scheduler_materialization_source_required_fail_closed_without_override"
        ),
    }
    instance_key = (
        f"{candidate['candidate_id']}@@{candidate['decision_time_utc']}"
    )
    candidate.update(
        {
            "candidate_id_source": "candidate_id",
            "canonical_replay_candidate_instance_key": instance_key,
            "source_bound_replay_candidate_instance_key": instance_key,
            "candidate_instance_identity_status": "materialized",
        }
    )
    _add_strict_limit_fillability(candidate)
    open_reduced_authority = _attach_signed_open_reduced_authority(
        candidate,
        selector_packet,
        reason=(
            "ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay"
        ),
        decision_time=candidate["decision_time_utc"],
        action_intent="new_position",
        authority_family="fill_floor_softening",
    )
    packets = {
        "selector_packet": selector_packet,
        "pretrade_broker_net_cost_packet": _cost_packet(),
    }

    assert (
        timewarp.replay_order_materialization_authority_block_reason(
            candidate=candidate,
            packets=packets,
        )
        is None
    )

    refused_packets = {
        "selector_packet": selector_packet,
        "pretrade_broker_net_cost_packet": _cost_packet("REFUSED"),
    }
    refused_reason = timewarp.replay_order_materialization_authority_block_reason(
        candidate={
            **candidate,
            "pretrade_cost_packet_status": "REFUSED",
        },
        packets=refused_packets,
    )
    assert refused_reason is not None
    assert "broker_cost_packet_refused" in refused_reason


def test_order_materialization_blocks_stale_source_required_override_without_signed_authority() -> None:
    selector_packet = _selector_packet(
        "ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay",
        action="open-reduced-risk",
    )
    candidate = {
        "candidate_id": "candidate-stale-source-required-override",
        "symbol": "XAUUSD",
        "side": "LONG",
        "decision_time_utc": "2025-06-11T08:15:00+00:00",
        "selector_action": "open-reduced-risk",
        "selector_reason": (
            "ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay"
        ),
        "scheduler_materialization_action_intent": "new_position",
        "scheduler_materialization_source_required_fail_closed_override_applied": True,
        "scheduler_materialization_source_required_fail_closed_override_failures": [],
        "scheduler_materialization_override_reason": (
            "source_required_fail_closed_package_new_position_source_gap_reconciled_for_replay"
        ),
        "source_required_fail_closed_replay_override_applied": True,
        "broker_lifecycle_truth_satisfied": True,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_source_bound_candidate_use_allowed": True,
        "ultimate_package_admission_candidate_use_allowed": True,
        "ultimate_package_effective_admission_count": 1,
        "ultimate_package_effective_matched_count": 1,
        "expected_net_r": 0.91,
        "candidate_expected_net_r": 0.91,
        "probability": 0.78,
        "fill_probability": 0.32,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "fixture.predecision.expected_net_r",
            "probability": "fixture.predecision.probability",
            "fill_probability": "fixture.predecision.fill_probability",
            "source_completeness": "fixture.predecision.source_completeness",
        },
        "candidate_decision_quality_alias_status": "exact_materialized",
        "candidate_decision_quality_source_boundary": "predecision_fixture",
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "candidate_cost_r_fallback_is_authority": False,
        "package_replay_executable_candidate_use_allowed": False,
        "package_replay_executable_candidate_use_allowed_reason": (
            "scheduler_materialization_source_required_fail_closed_without_override"
        ),
    }

    reason = timewarp.replay_order_materialization_authority_block_reason(
        candidate=candidate,
        packets={
            "selector_packet": selector_packet,
            "pretrade_broker_net_cost_packet": _cost_packet(),
        },
    )

    assert reason is not None
    assert reason.startswith(
        "signed_package_new_entry_authority_required_for_source_required_fail_closed_override"
    )


def test_order_materialization_blocks_stale_selector_hold_override_without_signed_authority() -> None:
    selector_packet = _selector_packet(
        "ultimate_candidate_package_source_required_hold",
        action="source-required",
    )
    candidate = {
        "candidate_id": "candidate-stale-selector-hold-override",
        "symbol": "EURUSD",
        "side": "SHORT",
        "decision_time_utc": "2025-06-11T08:15:00+00:00",
        "selector_action": "source-required",
        "selector_reason": "ultimate_candidate_package_source_required_hold",
        "scheduler_materialization_action_intent": "new_position",
        "scheduler_materialization_source_required_selector_hold_override_applied": True,
        "scheduler_materialization_source_required_selector_hold_override_failures": [],
        "scheduler_materialization_override_reason": (
            "source_required_selector_hold_package_source_reconciled_for_replay"
        ),
        "source_required_selector_hold_replay_override_applied": True,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_source_bound_candidate_use_allowed": True,
        "ultimate_package_admission_candidate_use_allowed": True,
        "ultimate_package_effective_admission_count": 1,
        "ultimate_package_effective_matched_count": 1,
        "expected_net_r": 0.70,
        "candidate_expected_net_r": 0.70,
        "probability": 0.74,
        "fill_probability": 0.92,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "fixture.predecision.expected_net_r",
            "probability": "fixture.predecision.probability",
            "fill_probability": "fixture.predecision.fill_probability",
            "source_completeness": "fixture.predecision.source_completeness",
        },
        "candidate_decision_quality_alias_status": "exact_materialized",
        "candidate_decision_quality_source_boundary": "predecision_fixture",
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "candidate_cost_r_fallback_is_authority": False,
        "package_replay_executable_candidate_use_allowed": False,
        "package_replay_executable_candidate_use_allowed_reason": (
            "source_required_selector_hold_without_override"
        ),
    }

    reason = timewarp.replay_order_materialization_authority_block_reason(
        candidate=candidate,
        packets={
            "selector_packet": selector_packet,
            "pretrade_broker_net_cost_packet": _cost_packet(),
        },
    )

    assert reason is not None
    assert reason.startswith(
        "signed_package_new_entry_authority_required_for_source_required_selector_hold_override"
    )


def test_order_materialization_blocks_stale_lifecycle_resolver_without_signed_authority() -> None:
    selector_packet = _selector_packet("broker_net_probability_confluence_pass", action="trade")
    candidate = {
        "candidate_id": "candidate-stale-lifecycle-resolver",
        "symbol": "XAUUSD",
        "side": "LONG",
        "decision_time_utc": "2025-06-11T08:15:00+00:00",
        "selector_action": "trade",
        "selector_reason": "broker_net_probability_confluence_pass",
        "scheduler_materialization_action_intent": "same_direction_scale_in",
        "scheduler_materialization_replay_lifecycle_action_resolver_applied": True,
        "scheduler_materialization_replay_lifecycle_action_resolver_failures": [],
        "scheduler_materialization_replay_lifecycle_action_resolver_resolved_action_intent": (
            "same_direction_scale_in"
        ),
        "scheduler_materialization_override_reason": (
            "replay_lifecycle_action_resolver_same_direction_scale_in"
        ),
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_source_bound_candidate_use_allowed": True,
        "ultimate_package_admission_candidate_use_allowed": True,
        "ultimate_package_effective_admission_count": 1,
        "ultimate_package_effective_matched_count": 1,
        "expected_net_r": 0.91,
        "candidate_expected_net_r": 0.91,
        "probability": 0.79,
        "fill_probability": 0.32,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "fixture.predecision.expected_net_r",
            "probability": "fixture.predecision.probability",
            "fill_probability": "fixture.predecision.fill_probability",
            "source_completeness": "fixture.predecision.source_completeness",
        },
        "candidate_decision_quality_alias_status": "exact_materialized",
        "candidate_decision_quality_source_boundary": "predecision_fixture",
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "candidate_cost_r_fallback_is_authority": False,
        "package_replay_executable_candidate_use_allowed": False,
        "package_replay_executable_candidate_use_allowed_reason": (
            "package_lifecycle_action_resolution_required"
        ),
    }

    reason = timewarp.replay_order_materialization_authority_block_reason(
        candidate=candidate,
        packets={
            "selector_packet": selector_packet,
            "pretrade_broker_net_cost_packet": _cost_packet(),
        },
    )

    assert reason is not None
    assert reason.startswith(
        "signed_package_new_entry_authority_required_for_replay_lifecycle_action_resolution"
    )


def test_order_materialization_allows_source_required_reduce_risk_scale_in_override_after_lifecycle_reconcile() -> None:
    selector_packet = _selector_packet(
        "numeric_confluence_structured_disagreement",
        action="reduce-risk",
    )
    selector_packet["component_scores"]["ultimate_candidate_package"][
        "admission_sleeve_match_count"
    ] = 1
    candidate = {
        "candidate_id": "candidate-source-required-reduce-risk-scale-in",
        "symbol": "XAUUSD",
        "side": "LONG",
        "decision_time_utc": "2025-06-11T08:15:00+00:00",
        "selector_action": "reduce-risk",
        "selector_reason": "numeric_confluence_structured_disagreement",
        "scheduler_materialization_action_intent": "same_direction_scale_in",
        "lifecycle_action": "same_direction_scale_in",
        "same_symbol_lifecycle_action": "same_direction_scale_in",
        "scheduler_materialization_source_required_fail_closed_override_applied": True,
        "scheduler_materialization_source_required_fail_closed_override_failures": [],
        "scheduler_materialization_override_reason": (
            "package_same_direction_scale_in_lifecycle_reconciled_for_replay"
        ),
        "source_required_lifecycle_origin": True,
        "source_required_lifecycle_origin_reason": "source_required_fail_closed",
        "source_required_fail_closed_replay_override_applied": True,
        "broker_lifecycle_truth_satisfied": True,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_source_bound_candidate_use_allowed": True,
        "ultimate_package_admission_candidate_use_allowed": True,
        "ultimate_package_effective_admission_count": 1,
        "ultimate_package_effective_matched_count": 1,
        "ultimate_package_scheduler_consumed_status": (
            "eligible_for_scheduler_consumption"
        ),
        "expected_net_r": 0.91,
        "candidate_expected_net_r": 0.91,
        "probability": 0.78,
        "confidence": 0.82,
        "candidate_confidence": 0.82,
        "scheduler_confidence": 0.82,
        "fill_probability": 0.92,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "fixture.predecision.expected_net_r",
            "probability": "fixture.predecision.probability",
            "confidence": "fixture",
            "fill_probability": "fixture.predecision.fill_probability",
            "source_completeness": "fixture.predecision.source_completeness",
        },
        "candidate_decision_quality_alias_status": "exact_materialized",
        "candidate_decision_quality_source_boundary": "predecision_fixture",
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "package_replay_executable_candidate_use_allowed": False,
        "package_replay_executable_candidate_use_allowed_reason": (
            "ultimate_package_effective_source_bound_not_allowed"
        ),
    }
    instance_key = (
        f"{candidate['candidate_id']}@@{candidate['decision_time_utc']}"
    )
    candidate.update(
        {
            "candidate_id_source": "candidate_id",
            "canonical_replay_candidate_instance_key": instance_key,
            "source_bound_replay_candidate_instance_key": instance_key,
            "candidate_instance_identity_status": "materialized",
        }
    )
    candidate["ultimate_candidate_package_reduce_risk_authority"] = {
        "applies": True,
        "allowed": True,
        "authority_family": "numeric_disagreement_softening",
        "current_config_allowed": True,
        "source_boundary": (
            "predecision_package_reduce_risk_new_order_authority_no_outcome_fields"
        ),
    }
    _add_strict_limit_fillability(candidate)
    _sign_package_new_entry_authority(
        candidate,
        action_intent="same_direction_scale_in",
    )
    reduce_risk_authority = candidate[
        "ultimate_candidate_package_reduce_risk_authority"
    ]
    selector_packet["component_scores"][
        "ultimate_candidate_package_reduce_risk_authority"
    ] = reduce_risk_authority
    packets = {
        "selector_packet": selector_packet,
        "pretrade_broker_net_cost_packet": _cost_packet(),
    }

    assert (
        timewarp.replay_order_materialization_authority_block_reason(
            candidate=candidate,
            packets=packets,
            config={
                "gtos_vnext_runtime": {
                    "ultimate_candidate_package_numeric_disagreement_open_reduced_risk_enabled": True,
                    "scheduler_v4_best_trade_allocator_selector_reduce_risk_numeric_disagreement_package_new_entry_authority_enabled": True,
                }
            },
        )
        is None
    )


def test_order_materialization_rejects_open_reduced_alias_without_authority_mapping() -> None:
    selector_packet = _selector_packet(
        "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk",
        action="open-reduced-risk",
    )
    candidate = {
        "candidate_id": "candidate-open-reduced-alias-only",
        "symbol": "XAUUSD",
        "side": "LONG",
        "decision_time_utc": "2025-06-11T08:15:00+00:00",
        "selector_action": "open-reduced-risk",
        "selector_reason": (
            "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk"
        ),
        "scheduler_materialization_action_intent": "new_position",
        "lifecycle_action": "new_position",
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_source_bound_candidate_use_allowed": True,
        "ultimate_package_admission_candidate_use_allowed": True,
        "ultimate_package_effective_admission_count": 1,
        "ultimate_package_effective_matched_count": 1,
        "ultimate_package_scheduler_consumed_status": (
            "eligible_for_scheduler_consumption"
        ),
        "expected_net_r": 0.91,
        "candidate_expected_net_r": 0.91,
        "probability": 0.78,
        "fill_probability": 0.32,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "package_replay_executable_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed_reason": (
            "broker_cost_and_scheduler_action_executable"
        ),
        "package_open_reduced_authority_allowed": True,
    }
    packets = {
        "selector_packet": selector_packet,
        "pretrade_broker_net_cost_packet": _cost_packet(),
    }

    reason = timewarp.replay_order_materialization_authority_block_reason(
        candidate=candidate,
        packets=packets,
        config={
            "gtos_vnext_runtime": {
                "ultimate_candidate_package_broker_net_gradient_open_reduced_risk_enabled": True
            }
        },
    )

    assert reason == "selector_open_reduced_risk_authority_missing"


def test_order_materialization_allows_broker_net_gradient_open_reduced_authority() -> None:
    selector_packet = _open_reduced_selector_packet(
        "broker_net_admission_ev_below_full_trade_floor",
        authority_family="broker_net_admission_gradient",
    )
    selector_packet["component_scores"][
        "ultimate_candidate_package_open_reduced_risk_authority"
    ]["current_config_allowed"] = True
    candidate = _sign_package_new_entry_authority({
        "candidate_id": "candidate-open-reduced-broker-net-gradient",
        "symbol": "XAUUSD",
        "side": "LONG",
        "decision_time_utc": "2025-06-11T08:15:00+00:00",
        "selector_action": "open-reduced-risk",
        "selector_reason": "broker_net_admission_ev_below_full_trade_floor",
        "scheduler_materialization_action_intent": "new_position",
        "lifecycle_action": "new_position",
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_source_bound_candidate_use_allowed": True,
        "ultimate_package_admission_candidate_use_allowed": True,
        "ultimate_package_effective_admission_count": 1,
        "ultimate_package_effective_matched_count": 1,
        "ultimate_package_scheduler_consumed_status": (
            "eligible_for_scheduler_consumption"
        ),
        "expected_net_r": 0.08,
        "candidate_expected_net_r": 0.08,
        "probability": 0.72,
        "fill_probability": 0.82,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "fixture.predecision.expected_net_r",
            "probability": "fixture.predecision.probability",
            "fill_probability": "fixture.predecision.fill_probability",
            "source_completeness": "fixture.predecision.source_completeness",
        },
        "candidate_decision_quality_alias_status": "exact_materialized",
        "candidate_decision_quality_source_boundary": (
            "predecision_fixture_quality_fields_no_outcome"
        ),
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "package_replay_executable_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed_reason": (
            "broker_cost_and_scheduler_action_executable"
        ),
        "ultimate_candidate_package_open_reduced_risk_authority": (
            selector_packet["component_scores"][
                "ultimate_candidate_package_open_reduced_risk_authority"
            ]
        ),
    }, config={
        "ultimate_candidate_package_broker_net_gradient_open_reduced_risk_enabled": True
    })
    packets = {
        "selector_packet": selector_packet,
        "pretrade_broker_net_cost_packet": _cost_packet(),
    }

    reason = timewarp.replay_order_materialization_authority_block_reason(
        candidate=candidate,
        packets=packets,
        config={
            "gtos_vnext_runtime": {
                "ultimate_candidate_package_broker_net_gradient_open_reduced_risk_enabled": True
            }
        },
    )

    assert reason is None


def test_order_materialization_blocks_uncalibrated_selected_policy_signed_authority() -> None:
    selector_packet = _open_reduced_selector_packet(
        "broker_net_admission_ev_below_full_trade_floor",
        authority_family="broker_net_admission_gradient",
    )
    candidate = _sign_package_new_entry_authority({
        "candidate_id": "candidate-open-reduced-uncalibrated-selected-policy",
        "symbol": "XAUUSD",
        "side": "LONG",
        "decision_time_utc": "2025-06-11T08:15:00+00:00",
        "selector_action": "open-reduced-risk",
        "selector_reason": "broker_net_admission_ev_below_full_trade_floor",
        "scheduler_materialization_action_intent": "new_position",
        "lifecycle_action": "new_position",
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_source_bound_candidate_use_allowed": True,
        "ultimate_package_admission_candidate_use_allowed": True,
        "ultimate_package_effective_admission_count": 1,
        "ultimate_package_effective_matched_count": 1,
        "ultimate_package_scheduler_consumed_status": (
            "eligible_for_scheduler_consumption"
        ),
        "expected_net_r": 0.88,
        "candidate_expected_net_r": 0.88,
        "probability": 0.72,
        "fill_probability": 0.82,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "fixture.predecision.expected_net_r",
            "probability": "fixture.predecision.probability",
            "fill_probability": "fixture.predecision.fill_probability",
            "source_completeness": "fixture.predecision.source_completeness",
        },
        "candidate_decision_quality_alias_status": "exact_materialized",
        "candidate_decision_quality_source_boundary": (
            "predecision_fixture_quality_fields_no_outcome"
        ),
        "selected_policy_for_expected_net_r": "momentum_exhaustion",
        "selected_policy_expected_net_calibration_status": (
            "selected_policy_expected_net_calibration_missing"
        ),
        "selected_policy_expected_net_calibrated": False,
        "selected_policy_expected_net_calibration_required": True,
        "selected_policy_expected_net_calibration_source": (
            "fixture.predecision.expected_net_r"
        ),
        "selected_policy_expected_net_calibration_source_boundary": (
            "predecision_fixture_quality_fields_no_outcome"
        ),
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "package_replay_executable_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed_reason": (
            "broker_cost_and_scheduler_action_executable"
        ),
        "ultimate_candidate_package_open_reduced_risk_authority": (
            selector_packet["component_scores"][
                "ultimate_candidate_package_open_reduced_risk_authority"
            ]
        ),
    })
    packets = {
        "selector_packet": selector_packet,
        "pretrade_broker_net_cost_packet": _cost_packet(),
    }

    signed_validation = timewarp.signed_reduced_package_new_entry_authority_validation(
        candidate=candidate,
        packets=packets,
        selector_action="open-reduced-risk",
        selector_reason="broker_net_admission_ev_below_full_trade_floor",
        action_intent="new_position",
        components={},
    )
    reason = timewarp.replay_order_materialization_authority_block_reason(
        candidate=candidate,
        packets=packets,
    )

    assert signed_validation["valid"] is False
    assert "selected_policy_expected_net_calibration_missing" in set(
        signed_validation["failures"]
    )
    assert reason == (
        "selected_policy_expected_net_calibration_missing"
        "_order_materialization_block"
    )


def test_order_materialization_uses_package_source_floor_for_open_reduced_authority() -> None:
    reason_text = "ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay"
    selector_packet = _open_reduced_selector_packet(
        reason_text,
        authority_family="fill_floor_softening",
    )
    authority = selector_packet["component_scores"][
        "ultimate_candidate_package_open_reduced_risk_authority"
    ]
    candidate = {
        "candidate_id": "candidate-open-reduced-package-source-floor",
        "symbol": "XAUUSD",
        "side": "LONG",
        "decision_time_utc": "2025-06-11T08:15:00+00:00",
        "selector_action": "open-reduced-risk",
        "selector_reason": reason_text,
        "scheduler_materialization_action_intent": "new_position",
        "lifecycle_action": "new_position",
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_source_bound_candidate_use_allowed": True,
        "ultimate_package_admission_candidate_use_allowed": True,
        "ultimate_package_effective_admission_count": 1,
        "ultimate_package_effective_matched_count": 1,
        "ultimate_package_scheduler_consumed_status": (
            "eligible_for_scheduler_consumption"
        ),
        "expected_net_r": 0.91,
        "candidate_expected_net_r": 0.91,
        "probability": 0.78,
        "fill_probability": 0.32,
        "source_completeness": 0.70,
        "source_completeness_status": "source_completeness_present",
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "fixture.predecision.expected_net_r",
            "probability": "fixture.predecision.probability",
            "fill_probability": "fixture.predecision.fill_probability",
            "source_completeness": "fixture.predecision.source_completeness",
        },
        "candidate_decision_quality_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        "candidate_decision_quality_alias_status": "exact_materialized",
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "package_replay_executable_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed_reason": (
            "broker_cost_and_scheduler_action_executable"
        ),
    }
    candidate["ultimate_candidate_package_open_reduced_risk_authority"] = authority
    _add_strict_limit_fillability(candidate)
    _sign_package_new_entry_authority(candidate)
    signed_authority = candidate[
        "ultimate_candidate_package_open_reduced_risk_authority"
    ]
    selector_packet["component_scores"][
        "ultimate_candidate_package_open_reduced_risk_authority"
    ] = signed_authority
    packets = {
        "selector_packet": selector_packet,
        "pretrade_broker_net_cost_packet": _cost_packet(),
    }
    config = {
        "gtos_vnext_runtime": {
            "ultimate_candidate_package_soften_selector_fill_floor_enabled": True,
            "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_source_completeness": 0.65,
        }
    }

    assert (
        timewarp.replay_order_materialization_authority_block_reason(
            candidate=candidate,
            packets=packets,
            config=config,
        )
        is None
    )

    below_floor_candidate = dict(candidate)
    below_floor_candidate["source_completeness"] = 0.64
    below_floor_candidate[
        "ultimate_candidate_package_open_reduced_risk_authority"
    ] = authority
    _sign_package_new_entry_authority(below_floor_candidate)
    below_floor_authority = below_floor_candidate[
        "ultimate_candidate_package_open_reduced_risk_authority"
    ]
    below_floor_packets = {
        **packets,
        "selector_packet": {
            **selector_packet,
            "component_scores": {
                **selector_packet["component_scores"],
                "ultimate_candidate_package_open_reduced_risk_authority": (
                    below_floor_authority
                ),
            },
        },
    }
    below_floor_reason = timewarp.replay_order_materialization_authority_block_reason(
        candidate=below_floor_candidate,
        packets=below_floor_packets,
        config=config,
    )
    assert below_floor_reason == (
        "selector_open_reduced_risk_source_completeness_below_floor:"
        "0.640<floor:0.650"
    )


def test_order_materialization_blocks_disabled_broker_net_gradient_authority() -> None:
    selector_packet = _open_reduced_selector_packet(
        "broker_net_admission_ev_below_full_trade_floor",
        authority_family="broker_net_admission_gradient",
    )
    candidate = {
        "candidate_id": "candidate-open-reduced-broker-net-gradient-disabled",
        "symbol": "XAUUSD",
        "side": "LONG",
        "decision_time_utc": "2025-06-11T08:15:00+00:00",
        "selector_action": "open-reduced-risk",
        "selector_reason": "broker_net_admission_ev_below_full_trade_floor",
        "scheduler_materialization_action_intent": "new_position",
        "lifecycle_action": "new_position",
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_source_bound_candidate_use_allowed": True,
        "ultimate_package_admission_candidate_use_allowed": True,
        "ultimate_package_effective_admission_count": 1,
        "ultimate_package_effective_matched_count": 1,
        "ultimate_package_scheduler_consumed_status": (
            "eligible_for_scheduler_consumption"
        ),
        "expected_net_r": 0.08,
        "candidate_expected_net_r": 0.08,
        "probability": 0.72,
        "fill_probability": 0.82,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "package_replay_executable_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed_reason": (
            "broker_cost_and_scheduler_action_executable"
        ),
        "ultimate_candidate_package_open_reduced_risk_authority": (
            selector_packet["component_scores"][
                "ultimate_candidate_package_open_reduced_risk_authority"
            ]
        ),
    }
    packets = {
        "selector_packet": selector_packet,
        "pretrade_broker_net_cost_packet": _cost_packet(),
    }

    reason = timewarp.replay_order_materialization_authority_block_reason(
        candidate=candidate,
        packets=packets,
    )
    assert reason == "broker_net_gradient_open_reduced_risk_disabled_by_config"

    reason = timewarp.replay_order_materialization_authority_block_reason(
        candidate=candidate,
        packets=packets,
        config={
            "gtos_vnext_runtime": {
                "ultimate_candidate_package_broker_net_gradient_open_reduced_risk_enabled": False
            }
        },
    )

    assert reason == "broker_net_gradient_open_reduced_risk_disabled_by_config"


def test_order_materialization_blocks_stale_router_refusal_open_reduced_authority() -> None:
    selector_packet = _open_reduced_selector_packet(
        "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk",
        authority_family="router_refusal_softening",
    )
    candidate = {
        "candidate_id": "candidate-open-reduced-stale-router",
        "symbol": "XAUUSD",
        "side": "LONG",
        "decision_time_utc": "2025-06-11T08:15:00+00:00",
        "selector_action": "open-reduced-risk",
        "selector_reason": (
            "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk"
        ),
        "scheduler_materialization_action_intent": "new_position",
        "lifecycle_action": "new_position",
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_source_bound_candidate_use_allowed": True,
        "ultimate_package_admission_candidate_use_allowed": True,
        "ultimate_package_effective_admission_count": 1,
        "ultimate_package_effective_matched_count": 1,
        "ultimate_package_scheduler_consumed_status": (
            "eligible_for_scheduler_consumption"
        ),
        "expected_net_r": 0.91,
        "candidate_expected_net_r": 0.91,
        "probability": 0.78,
        "fill_probability": 0.92,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "package_replay_executable_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed_reason": (
            "broker_cost_and_scheduler_action_executable"
        ),
        "ultimate_candidate_package_open_reduced_risk_authority": (
            selector_packet["component_scores"][
                "ultimate_candidate_package_open_reduced_risk_authority"
            ]
        ),
    }
    packets = {
        "selector_packet": selector_packet,
        "pretrade_broker_net_cost_packet": _cost_packet(),
    }

    reason = timewarp.replay_order_materialization_authority_block_reason(
        candidate=candidate,
        packets=packets,
        config={
            "gtos_vnext_runtime": {
                "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk_allowed": False
            }
        },
    )

    assert reason == "router_refusal_open_reduced_risk_disabled_by_config"


def test_live_duplicate_candidate_hold_detects_pending_and_open_exposure() -> None:
    account = timewarp.AccountState()
    account.pending_orders = {
        "order-1": {
            "simulated_order_id": "order-1",
            "candidate_id": "candidate-dup",
            "symbol": "XAUUSD",
            "side": "SHORT",
            "decision_time_utc": "2025-06-11T08:15:00+00:00",
            "order_status": "pending_accepted",
            "created_time_utc": "2025-06-11T08:15:00+00:00",
            "expiry_utc": "2025-06-11T10:15:00+00:00",
        }
    }

    pending = timewarp.live_duplicate_candidate_hold_detail(
        account=account,
        candidate={
            "candidate_id": "candidate-dup",
            "symbol": "XAUUSD",
            "side": "SHORT",
            "decision_time_utc": "2025-06-11T08:15:00+00:00",
        },
    )

    assert pending["applies"] is True
    assert pending["reason"] == "same_candidate_pending_order_already_live"
    assert pending["candidate_instance_identity_scope"] == (
        "candidate_id_and_decision_time"
    )
    assert pending["existing_simulated_order_id"] == "order-1"

    different_instance = timewarp.live_duplicate_candidate_hold_detail(
        account=account,
        candidate={
            "candidate_id": "candidate-dup",
            "symbol": "XAUUSD",
            "side": "SHORT",
            "decision_time_utc": "2025-06-11T08:30:00+00:00",
        },
    )

    assert different_instance["applies"] is False

    account.pending_orders = {}
    account.open_positions = {
        "trade-1": {
            "simulated_order_id": "order-2",
            "simulated_trade_id": "trade-1",
            "candidate_id": "candidate-dup",
            "symbol": "XAUUSD",
            "side": "SHORT",
            "decision_time_utc": "2025-06-11T08:45:00+00:00",
            "order_status": "filled",
        }
    }
    open_position = timewarp.live_duplicate_candidate_hold_detail(
        account=account,
        candidate={
            "candidate_id": "candidate-dup",
            "symbol": "XAUUSD",
            "side": "SHORT",
            "decision_time_utc": "2025-06-11T08:45:00+00:00",
        },
    )

    assert open_position["applies"] is True
    assert open_position["reason"] == "same_candidate_open_position_already_live"
    assert open_position["existing_simulated_trade_id"] == "trade-1"

    different_open_instance = timewarp.live_duplicate_candidate_hold_detail(
        account=account,
        candidate={
            "candidate_id": "candidate-dup",
            "symbol": "XAUUSD",
            "side": "SHORT",
            "decision_time_utc": "2025-06-11T09:00:00+00:00",
        },
    )

    assert different_open_instance["applies"] is False

    clear = timewarp.live_duplicate_candidate_hold_detail(
        account=account,
        candidate={
            "candidate_id": "candidate-other",
            "symbol": "XAUUSD",
            "side": "SHORT",
        },
    )

    assert clear["applies"] is False


def test_live_duplicate_candidate_hold_blocks_same_geometry_scale_in_without_independent_authority() -> None:
    account = timewarp.AccountState()
    account.pending_orders = {
        "order-prior": {
            "simulated_order_id": "order-prior",
            "candidate_id": "candidate-prior",
            "symbol": "XAUUSD",
            "side": "SHORT",
            "session": "moonshot_h23_00",
            "decision_time_utc": "2026-05-15T00:15:00+00:00",
            "created_time_utc": "2026-05-15T00:15:00+00:00",
            "entry_price": 4651.91,
            "stop_loss": 4654.735236544301,
            "take_profit_1": 4646.259526911397,
            "order_execution_path": "limit_first_probe",
            "policy_target_r": 2.0,
            "risk_pct": 0.1,
            "order_status": "pending_accepted",
        }
    }

    hold = timewarp.live_duplicate_candidate_hold_detail(
        account=account,
        candidate={
            "candidate_id": "candidate-next",
            "symbol": "XAUUSD",
            "side": "SHORT",
            "session": "moonshot_h23_00",
            "decision_time_utc": "2026-05-15T00:30:00+00:00",
            "scheduler_materialization_action_intent": "same_direction_scale_in",
            "entry_price": 4651.91,
            "stop_loss": 4654.735236544301,
            "take_profit_1": 4646.259526911397,
        },
    )

    assert hold["applies"] is True
    assert hold["reason"] == "same_geometry_scale_in_requires_independent_authority"
    assert hold["duplicate_live_state"] == "pending_order"
    assert hold["existing_simulated_order_id"] == "order-prior"
    assert hold["same_geometry_scale_in_active_match_count"] == 1
    assert hold["uses_outcome_fields"] is False


def test_live_duplicate_candidate_hold_allows_same_geometry_scale_in_with_independent_authority() -> None:
    account = timewarp.AccountState()
    account.pending_orders = {
        "order-prior": {
            "simulated_order_id": "order-prior",
            "candidate_id": "candidate-prior",
            "symbol": "XAUUSD",
            "side": "SHORT",
            "session": "moonshot_h23_00",
            "decision_time_utc": "2026-05-15T00:15:00+00:00",
            "entry_price": 4651.91,
            "stop_loss": 4654.735236544301,
            "take_profit_1": 4646.259526911397,
            "risk_pct": 0.1,
            "order_status": "pending_accepted",
        }
    }

    hold = timewarp.live_duplicate_candidate_hold_detail(
        account=account,
        candidate={
            "candidate_id": "candidate-next",
            "symbol": "XAUUSD",
            "side": "SHORT",
            "session": "moonshot_h23_00",
            "decision_time_utc": "2026-05-15T00:30:00+00:00",
            "scheduler_materialization_action_intent": "same_direction_scale_in",
            "entry_price": 4651.91,
            "stop_loss": 4654.735236544301,
            "take_profit_1": 4646.259526911397,
            "source_required_package_duplicate_scale_in_same_geometry_independence_authority": {
                "allowed": True,
                "source_boundary": (
                    "predecision_candidate_geometry_and_simulated_account_state_no_outcome_fields"
                ),
            },
        },
    )

    assert hold["applies"] is False
    assert (
        hold["reason"]
        == "same_geometry_scale_in_independent_authority_present"
    )


def test_source_required_fail_closed_package_replay_override_keeps_cost_refusal_blocked(
    monkeypatch,
) -> None:
    captured = {}

    def fake_allocate(window, config, *, raw_config=None):
        captured["window"] = window
        return {
            "selected_candidate_id": None,
            "selected_candidate_ids": [],
            "option_trace": [],
        }

    monkeypatch.setattr(timewarp, "allocate_decision_window", fake_allocate)
    selector_packet = _selector_packet(
        "ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay",
        action="open-reduced-risk",
    )
    selector_packet["component_scores"]["ultimate_candidate_package"][
        "admission_sleeve_match_count"
    ] = 1
    candidate = {
        "candidate_id": "candidate-source-required-cost-refused",
        "symbol": "XAUUSD",
        "side": "LONG",
        "risk_reward_ratio": 2.0,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "candidate_expected_net_r": 0.91,
        "source_window_complete": True,
    }
    packets = {
        "candidate-source-required-cost-refused": {
            "selector_packet": selector_packet,
            "probability_packet": {
                "theses": [{"action": "long", "probability": 0.78, "EV": 0.96}]
            },
            "lifecycle_packet": {"action": "source_required_fail_closed"},
            "selector_event": {
                "predecision_limit_fillability": {"fill_probability": 0.32}
            },
            "pretrade_broker_net_cost_packet": _cost_packet("REFUSED"),
            "expected_net_r": 0.91,
        }
    }

    timewarp.materialize_scheduler_window(
        asof_utc="2025-06-11T08:15:00+00:00",
        candidates=[candidate],
        v4_packets=packets,
        config={
            "gtos_vnext_runtime": {
                "scheduler_v4_best_trade_allocator_source_required_fail_closed_package_replay_override_enabled": True,
            }
        },
    )

    assert captured["window"]["candidates"] == []
    assert candidate["scheduler_materialization_skip_reason"].startswith(
        "source_required_fail_closed_package_replay_override_failed:"
    )
    assert (
        candidate[
            "scheduler_materialization_source_required_fail_closed_override_applied"
        ]
        is False
    )
    assert any(
        str(reason).startswith("broker_cost_packet_refused")
        for reason in candidate[
            "scheduler_materialization_source_required_fail_closed_override_failures"
        ]
    )


def test_source_required_fail_closed_package_replay_override_failure_is_not_invalid_action(
    monkeypatch,
) -> None:
    captured = {}

    def fake_allocate(window, config, *, raw_config=None):
        captured["window"] = window
        return {
            "selected_candidate_id": None,
            "selected_candidate_ids": [],
            "option_trace": [],
        }

    monkeypatch.setattr(timewarp, "allocate_decision_window", fake_allocate)
    selector_packet = _selector_packet(
        "ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay",
        action="open-reduced-risk",
    )
    selector_packet["component_scores"]["ultimate_candidate_package"][
        "admission_sleeve_match_count"
    ] = 1
    decision_time = "2025-06-11T08:15:00+00:00"
    candidate = {
        "candidate_id": "candidate-source-required-low-fill",
        "decision_time_utc": decision_time,
        "symbol": "XAUUSD",
        "side": "LONG",
        "risk_reward_ratio": 2.0,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "candidate_expected_net_r": 0.91,
        "source_window_complete": True,
    }
    _add_strict_limit_fillability(candidate, 0.12)
    packets = {
        f"candidate-source-required-low-fill@@{decision_time}": {
            "selector_packet": selector_packet,
            "probability_packet": {
                "theses": [{"action": "long", "probability": 0.78, "EV": 0.96}]
            },
            "lifecycle_packet": {"action": "source_required_fail_closed"},
            "selector_event": {
                "predecision_limit_fillability": {"fill_probability": 0.12}
            },
            "pretrade_broker_net_cost_packet": _cost_packet(),
            "expected_net_r": 0.91,
        }
    }

    timewarp.materialize_scheduler_window(
        asof_utc=decision_time,
        candidates=[candidate],
        v4_packets=packets,
        config={
            "gtos_vnext_runtime": {
                "scheduler_v4_best_trade_allocator_source_required_fail_closed_package_replay_override_enabled": True,
                "scheduler_v4_best_trade_allocator_source_required_fail_closed_package_replay_override_min_fill_probability": 0.25,
            }
        },
    )

    assert captured["window"]["candidates"] == []
    assert candidate["scheduler_materialization_original_action_intent"] == (
        "invalid_action_intent:source_required_fail_closed"
    )
    assert candidate["scheduler_materialization_action_intent"] == (
        "source_required_fail_closed_hold_not_executable_without_source"
    )
    assert candidate["scheduler_materialization_skip_reason"] == (
        "source_required_fail_closed_package_replay_override_failed:"
        "same_symbol_lifecycle_action_context_missing|fill_probability_below_floor"
    )
    assert (
        candidate[
            "scheduler_materialization_source_required_fail_closed_override_applied"
        ]
        is False
    )


def test_source_required_selector_hold_package_replay_override_reaches_scheduler(
    monkeypatch,
) -> None:
    captured = {}

    def fake_allocate(window, config, *, raw_config=None):
        captured["window"] = window
        return {
            "selected_candidate_id": "candidate-source-required-selector-hold",
            "selected_candidate_ids": ["candidate-source-required-selector-hold"],
            "option_trace": [],
        }

    monkeypatch.setattr(timewarp, "allocate_decision_window", fake_allocate)
    decision_time = "2025-06-11T08:15:00+00:00"
    selector_packet = _selector_packet(
        "ultimate_candidate_package_source_required_hold",
        action="source-required",
    )
    selector_packet["component_scores"]["ultimate_candidate_package"][
        "admission_sleeve_match_count"
    ] = 1
    candidate = {
        "candidate_id": "candidate-source-required-selector-hold",
        "symbol": "EURUSD",
        "side": "SHORT",
        "risk_reward_ratio": 2.0,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "candidate_expected_net_r": 0.70,
        "probability": 0.74,
        "candidate_probability": 0.74,
        "fill_probability": 0.92,
        "candidate_fill_probability": 0.92,
        "source_window_complete": True,
    }
    _add_strict_limit_fillability(candidate, 0.92)
    _attach_signed_open_reduced_authority(
        candidate,
        selector_packet,
        reason="ultimate_candidate_package_source_required_hold",
        decision_time=decision_time,
        action_intent="new_position",
    )
    packets = {
        f"candidate-source-required-selector-hold@@{decision_time}": {
            "selector_packet": selector_packet,
            "probability_packet": {
                "theses": [
                    {
                        "action": "short",
                        "probability": 0.74,
                        "EV": 0.76,
                        "confidence": 0.7,
                    }
                ]
            },
            "lifecycle_packet": {"action": "new_position"},
            "selector_event": {
                "predecision_limit_fillability": {"fill_probability": 0.92}
            },
            "pretrade_broker_net_cost_packet": _cost_packet(),
            "cost_r": 0.05,
            "broker_calibrated_expected_cost_r": 0.05,
            "expected_net_r": 0.70,
        }
    }

    timewarp.materialize_scheduler_window(
        asof_utc=decision_time,
        candidates=[candidate],
        v4_packets=packets,
        config={
            "gtos_vnext_runtime": {
                "scheduler_v4_best_trade_allocator_source_required_selector_hold_package_replay_override_enabled": True,
                "scheduler_v4_best_trade_allocator_source_required_selector_hold_package_replay_override_min_expected_net_r": 0.60,
                "scheduler_v4_best_trade_allocator_source_required_selector_hold_package_replay_override_min_probability": 0.72,
                "scheduler_v4_best_trade_allocator_source_required_selector_hold_package_replay_override_min_fill_probability": 0.90,
                "scheduler_v4_best_trade_allocator_source_required_selector_hold_package_replay_override_min_source_completeness": 0.95,
            }
        },
    )

    scheduler_candidates = captured["window"]["candidates"]
    assert len(scheduler_candidates) == 1
    row = scheduler_candidates[0]
    assert row["candidate_id"] == "candidate-source-required-selector-hold"
    assert row["selector_action"] == "source-required"
    assert row["action_intent"] == "new_position"
    assert (
        row[
            "scheduler_materialization_source_required_selector_hold_override_applied"
        ]
        is True
    )
    assert row["scheduler_materialization_override_reason"] == (
        "source_required_selector_hold_package_source_reconciled_for_replay"
    )
    assert row["replay_candidate_use_allowed_now"] is True
    assert row["replay_candidate_use_allowed_now_reason"] == (
        "source_required_selector_hold_package_replay_override_applied"
    )


def test_scheduler_missed_attribution_carries_source_required_and_veto_diagnostics() -> None:
    candidate = {
        "candidate_id": "candidate-source-required-missed",
        "scheduler_materialization_status": "scheduler_option_materialized",
        "scheduler_materialization_source_required_selector_hold_override_enabled": True,
        "scheduler_materialization_source_required_selector_hold_override_applied": False,
        "scheduler_materialization_source_required_selector_hold_override_failures": [
            "fill_probability_below_source_required_floor"
        ],
        "scheduler_materialization_source_required_fail_closed_override_enabled": True,
        "scheduler_materialization_source_required_fail_closed_override_applied": False,
        "scheduler_materialization_source_required_fail_closed_override_failures": [
            "same_side_lifecycle_scale_in_context_missing"
        ],
        "scheduler_materialization_source_required_fail_closed_same_side_open_position": False,
        "scheduler_materialization_source_required_fail_closed_lifecycle_context_present": False,
        "scheduler_materialization_source_required_fail_closed_lifecycle_context_source": None,
        "scheduler_materialization_source_required_fail_closed_allow_new_position_without_same_side_context": False,
        "scheduler_materialization_source_required_fail_closed_lifecycle_context": (
            "same_side_scale_in_context_missing"
        ),
        "scheduler_materialization_lifecycle_action_resolution_required": True,
        "scheduler_materialization_replay_lifecycle_action_resolver_enabled": True,
        "scheduler_materialization_replay_lifecycle_action_resolver_applied": False,
        "scheduler_materialization_replay_lifecycle_action_resolver_reason": (
            "broker_cost_packet_refused:unspecified"
        ),
        "scheduler_materialization_replay_lifecycle_action_resolver_failures": [
            "package_not_executable_source_bound_admission",
            "broker_cost_packet_refused:unspecified",
        ],
        "same_symbol_replay_exposure_context": {
            "same_side_open_count": 1,
            "same_side_open_ids": ["open-long"],
        },
        "same_symbol_lifecycle_exposure_risk_pct": 0.15,
        "pretrade_cost_packet_status": "REFUSED",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "cost_authority": "broker_calibrated_replay_cost",
        "candidate_cost_r_fallback_is_authority": False,
    }
    scheduler_option = {
        "decision_status": "candidate_vetoed",
        "runtime_eligible": False,
        "vetoes": [
            "selector_reduce_risk_new_entry_quality_floor_not_met:fill_probability"
        ],
        "score_components": {
            "candidate_decision_inputs": {
                "ev_r": 1.0,
                "cost_total_r": 0.05,
                "probability": 0.74,
                "fill_probability": 0.42,
                "source_completeness": 1.0,
            },
            "selector_reduce_risk_new_entry_authority": {
                "quality_failures": ["fill_probability"],
            },
            "selector_reduce_risk_package_fill_floor_authority": {
                "enabled": True,
                "allowed": False,
                "failures": ["fill_probability"],
            },
            "dynamic_budget_quality_gate": {
                "enabled": True,
                "quality_failures": ["fill_probability_below_dynamic_allocator_floor"],
            },
        },
    }

    fields = timewarp.scheduler_missed_opportunity_attribution_fields(
        candidate=candidate,
        scheduler_option=scheduler_option,
        selected_id_set={"other-candidate"},
        original_selected_ids=[],
    )

    assert fields["scheduler_selection_disposition"] == (
        "candidate_generated_not_scheduler_selected"
    )
    assert fields["candidate_generated_not_scheduler_selected"] is True
    assert fields[
        "scheduler_materialization_source_required_selector_hold_override_enabled"
    ] is True
    assert fields[
        "scheduler_materialization_source_required_selector_hold_override_applied"
    ] is False
    assert fields["scheduler_option_candidate_specific_diagnostic_status"] == (
        "materialized"
    )
    assert fields["scheduler_option_runtime_eligible"] is False
    assert fields["scheduler_option_package_fill_floor_authority_allowed"] is False
    assert fields["scheduler_option_package_fill_floor_authority_failures"] == [
        "fill_probability"
    ]
    assert (
        fields[
            "scheduler_materialization_source_required_fail_closed_override_applied"
        ]
        is False
    )
    assert (
        fields[
            "scheduler_materialization_source_required_fail_closed_lifecycle_context_present"
        ]
        is False
    )
    assert (
        fields[
            "scheduler_materialization_source_required_fail_closed_lifecycle_context"
        ]
        == "same_side_scale_in_context_missing"
    )
    assert (
        fields[
            "scheduler_materialization_source_required_fail_closed_allow_new_position_without_same_side_context"
        ]
        is False
    )
    assert fields["scheduler_option_dynamic_budget_quality_failures"] == [
        "fill_probability_below_dynamic_allocator_floor"
    ]
    assert (
        fields["scheduler_materialization_lifecycle_action_resolution_required"]
        is True
    )
    assert (
        fields["scheduler_materialization_replay_lifecycle_action_resolver_applied"]
        is False
    )
    assert fields[
        "scheduler_materialization_replay_lifecycle_action_resolver_failures"
    ] == [
        "package_not_executable_source_bound_admission",
        "broker_cost_packet_refused:unspecified",
    ]
    assert fields["same_symbol_replay_exposure_context"]["same_side_open_ids"] == [
        "open-long"
    ]
    assert fields["same_symbol_lifecycle_exposure_risk_pct"] == 0.15
    assert fields["missed_cost_disposition"] == (
        "scoreable_missed_cost_refused_non_executable_diagnostic"
    )
    assert fields["missed_opportunity_counterfactual_scoreable"] is True
    assert fields["missed_opportunity_headline_r_scoreable"] is False
    assert fields["missed_opportunity_non_executable_diagnostic_scoreable"] is True
    assert fields["missed_pretrade_cost_packet_status"] == "REFUSED"


def test_scheduler_option_trace_reports_unresolved_fill_floor_failures_not_raw() -> None:
    candidate = {
        "candidate_id": "route-resolved-passive-limit-fill-floor",
        "decision_time_utc": "2026-06-03T10:00:00+00:00",
        "symbol": "XAUUSD",
        "side": "LONG",
        "pretrade_cost_packet_status": "PASSED",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "cost_authority": "broker_calibrated_replay_cost",
    }
    scheduler_option = {
        "decision_status": "candidate_admitted_selector_open_reduced_risk_capped",
        "runtime_eligible": True,
        "vetoes": [],
        "score_components": {
            "candidate_decision_inputs": {
                "decision_time_utc": "2026-06-03T10:00:00+00:00",
                "ev_r": 1.0,
                "cost_total_r": 0.05,
                "probability": 0.82,
                "fill_probability": 0.30,
                "source_completeness": 1.0,
            },
            "selector_reduce_risk_package_fill_floor_authority": {
                "enabled": True,
                "allowed": True,
                "failures": ["execution_fill_probability"],
                "raw_failures": ["execution_fill_probability"],
                "resolved_failures": ["execution_fill_probability"],
                "unresolved_failures": [],
                "authority_failures": [],
            },
        },
    }

    fields = timewarp.scheduler_missed_opportunity_attribution_fields(
        candidate=candidate,
        scheduler_option=scheduler_option,
        selected_id_set=set(),
        original_selected_ids=[],
    )

    assert fields["scheduler_option_package_fill_floor_authority_allowed"] is True
    assert fields["scheduler_option_package_fill_floor_authority_failures"] == []
    assert fields["scheduler_option_package_fill_floor_authority_raw_failures"] == [
        "execution_fill_probability"
    ]
    assert fields["scheduler_option_package_fill_floor_authority_resolved_failures"] == [
        "execution_fill_probability"
    ]
    assert fields[
        "scheduler_option_package_fill_floor_authority_unresolved_failures"
    ] == []


def test_source_required_selector_hold_package_replay_override_keeps_cost_refusal_blocked(
    monkeypatch,
) -> None:
    captured = {}

    def fake_allocate(window, config, *, raw_config=None):
        captured["window"] = window
        return {
            "selected_candidate_id": None,
            "selected_candidate_ids": [],
            "option_trace": [],
        }

    monkeypatch.setattr(timewarp, "allocate_decision_window", fake_allocate)
    selector_packet = _selector_packet(
        "ultimate_candidate_package_source_required_hold",
        action="source-required",
    )
    selector_packet["component_scores"]["ultimate_candidate_package"][
        "admission_sleeve_match_count"
    ] = 1
    candidate = {
        "candidate_id": "candidate-source-required-selector-hold-cost-refused",
        "symbol": "EURUSD",
        "side": "SHORT",
        "risk_reward_ratio": 2.0,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "candidate_expected_net_r": 0.70,
        "source_window_complete": True,
    }
    packets = {
        "candidate-source-required-selector-hold-cost-refused": {
            "selector_packet": selector_packet,
            "probability_packet": {
                "theses": [{"action": "short", "probability": 0.74, "EV": 0.76}]
            },
            "lifecycle_packet": {"action": "new_position"},
            "selector_event": {
                "predecision_limit_fillability": {"fill_probability": 0.92}
            },
            "pretrade_broker_net_cost_packet": {
                **_cost_packet("REFUSED"),
                "refusal_reasons": [
                    "total_cost_r_exceeds_limit:0.220000>0.150000",
                ],
            },
            "expected_net_r": 0.70,
        }
    }

    timewarp.materialize_scheduler_window(
        asof_utc="2025-06-11T08:15:00+00:00",
        candidates=[candidate],
        v4_packets=packets,
        config={
            "gtos_vnext_runtime": {
                "scheduler_v4_best_trade_allocator_source_required_selector_hold_package_replay_override_enabled": True,
            }
        },
    )

    assert captured["window"]["candidates"] == []
    assert candidate["scheduler_materialization_skip_reason"] == (
        "selector_not_risk_bearing_cost_failed"
    )
    assert candidate["scheduler_materialization_cost_block_reason"].startswith(
        "broker_cost_packet_refused"
    )
    assert (
        candidate[
            "scheduler_materialization_source_required_selector_hold_override_applied"
        ]
        is False
    )
    assert any(
        str(reason).startswith("broker_cost_packet_refused")
        for reason in candidate[
            "scheduler_materialization_source_required_selector_hold_override_failures"
        ]
    )


def test_package_positive_reduce_risk_new_entry_reaches_scheduler_after_cost_pass(monkeypatch) -> None:
    captured = {}

    def fake_allocate(window, config, *, raw_config=None):
        captured["window"] = window
        captured["config"] = config
        return {"selected_candidate_id": "candidate-a", "selected_candidate_ids": ["candidate-a"], "option_trace": []}

    monkeypatch.setattr(timewarp, "allocate_decision_window", fake_allocate)
    candidate = {
        "candidate_id": "candidate-a",
        "symbol": "XAUUSD",
        "side": "LONG",
        "risk_reward_ratio": 2.0,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "candidate_expected_net_r": 0.67,
        "source_window_complete": True,
    }
    decision_time = "2025-06-11T08:15:00+00:00"
    packets = {
        f"candidate-a@@{decision_time}": {
            "selector_packet": _selector_packet(
                "calibrated_admission_fill_probability_below_generalized_floor"
            ),
            "probability_packet": {
                "theses": [
                    {
                        "action": "long",
                        "probability": 0.72,
                        "EV": 0.78,
                        "confidence": 0.7,
                    }
                ]
            },
            "lifecycle_packet": {"action": "new_position"},
            "selector_event": {
                "predecision_limit_fillability": {"fill_probability": 0.81}
            },
            "pretrade_broker_net_cost_packet": _cost_packet(),
            "cost_r": 0.05,
            "broker_calibrated_expected_cost_r": 0.05,
            "expected_net_r": 0.67,
        }
    }

    timewarp.materialize_scheduler_window(
        asof_utc=decision_time,
        candidates=[candidate],
        v4_packets=packets,
        config={"gtos_vnext_runtime": {}},
    )

    assert captured["window"]["candidates"] == []
    assert candidate["scheduler_materialization_skip_reason"] == (
        "selector_reduce_risk_open_reduced_not_executable:"
        "open_reduced_authority_not_allowed"
    )
    assert candidate["scheduler_materialization_selector_action"] == "reduce-risk"
    assert candidate["scheduler_materialization_action_intent"] == "new_position"


def test_package_dynamic_router_reduce_risk_new_entry_requires_explicit_authority(
    monkeypatch,
) -> None:
    captured = {}

    def fake_allocate(window, config, *, raw_config=None):
        captured["window"] = window
        captured["config"] = config
        return {
            "selected_candidate_id": "candidate-router",
            "selected_candidate_ids": ["candidate-router"],
            "option_trace": [],
        }

    monkeypatch.setattr(timewarp, "allocate_decision_window", fake_allocate)
    candidate = {
        "candidate_id": "candidate-router",
        "symbol": "XAUUSD",
        "side": "SHORT",
        "risk_reward_ratio": 2.0,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "candidate_expected_net_r": 0.82,
        "candidate_probability": 0.76,
        "candidate_fill_probability": 0.92,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "source_window_complete": True,
    }
    decision_time = "2025-06-11T08:15:00+00:00"
    packets = {
        f"candidate-router@@{decision_time}": {
            "selector_packet": _selector_packet(
                "ultimate_candidate_package_dynamic_router_refusal_softened_reduce_risk"
            ),
            "probability_packet": {
                "theses": [
                    {
                        "action": "short",
                        "probability": 0.76,
                        "EV": 0.87,
                        "confidence": 0.7,
                    }
                ]
            },
            "lifecycle_packet": {"action": "new_position"},
            "selector_event": {
                "predecision_limit_fillability": {"fill_probability": 0.92}
            },
            "pretrade_broker_net_cost_packet": _cost_packet(),
            "cost_r": 0.05,
            "broker_calibrated_expected_cost_r": 0.05,
            "expected_net_r": 0.82,
        }
    }

    timewarp.materialize_scheduler_window(
        asof_utc=decision_time,
        candidates=[candidate],
        v4_packets=packets,
        config={"gtos_vnext_runtime": {}},
    )

    assert captured["window"]["candidates"] == []
    assert candidate["scheduler_materialization_skip_reason"] == (
        "selector_reduce_risk_not_new_entry_authority"
    )
    assert candidate["scheduler_materialization_selector_action"] == "reduce-risk"
    assert candidate["scheduler_materialization_action_intent"] == "new_position"


def test_package_dynamic_router_reduce_risk_with_unsigned_authority_remains_blocked(
    monkeypatch,
) -> None:
    captured = {}

    def fake_allocate(window, config, *, raw_config=None):
        captured["window"] = window
        captured["config"] = config
        return {
            "selected_candidate_id": "candidate-router-authorized",
            "selected_candidate_ids": ["candidate-router-authorized"],
            "option_trace": [],
        }

    monkeypatch.setattr(timewarp, "allocate_decision_window", fake_allocate)
    candidate = {
        "candidate_id": "candidate-router-authorized",
        "symbol": "XAUUSD",
        "side": "SHORT",
        "risk_reward_ratio": 2.0,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "candidate_expected_net_r": 0.82,
        "candidate_probability": 0.76,
        "candidate_confidence": 0.70,
        "candidate_fill_probability": 0.92,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "source_window_complete": True,
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "candidate_expected_net_r",
            "probability": "candidate_probability",
            "confidence": "candidate_confidence",
            "fill_probability": "candidate_fill_probability",
            "source_completeness": "source_completeness",
        },
        "candidate_decision_quality_source_boundary": (
            "predecision_fixture_quality_fields_no_outcome"
        ),
    }
    decision_time = "2025-06-11T08:15:00+00:00"
    selector_packet = _selector_packet(
        "ultimate_candidate_package_dynamic_router_refusal_softened_reduce_risk"
    )
    selector_packet["component_scores"][
        "ultimate_candidate_package_reduce_risk_authority"
    ] = {
        "applies": True,
        "allowed": True,
        "authority_family": "router_refusal_softening",
    }
    packets = {
        f"candidate-router-authorized@@{decision_time}": {
            "selector_packet": selector_packet,
            "probability_packet": {
                "theses": [
                    {
                        "action": "short",
                        "probability": 0.76,
                        "EV": 0.87,
                        "confidence": 0.70,
                    }
                ]
            },
            "lifecycle_packet": {"action": "new_position"},
            "selector_event": {
                "predecision_limit_fillability": {"fill_probability": 0.92}
            },
            "pretrade_broker_net_cost_packet": _cost_packet(),
            "cost_r": 0.05,
            "broker_calibrated_expected_cost_r": 0.05,
            "expected_net_r": 0.82,
            "probability": 0.76,
            "confidence": 0.70,
            "fill_probability": 0.92,
            "source_completeness": 1.0,
        }
    }

    timewarp.materialize_scheduler_window(
        asof_utc=decision_time,
        candidates=[candidate],
        v4_packets=packets,
        config={"gtos_vnext_runtime": {}},
    )

    assert captured["window"]["candidates"] == []
    assert candidate["scheduler_materialization_skip_reason"] == (
        "selector_reduce_risk_not_new_entry_authority"
    )
    assert candidate["scheduler_materialization_selector_action"] == "reduce-risk"
    assert candidate["scheduler_materialization_action_intent"] == "new_position"


def test_owner_approved_xau_family_root_can_sign_without_claiming_exact_member_axis(
    monkeypatch,
) -> None:
    decision_time = "2025-10-27T08:30:00+00:00"
    candidate_id = "broadorigin_owner_xau_family_root"
    instance_key = f"{candidate_id}@@{decision_time}"
    sleeve_id = (
        "fpsc_scheduler_lifecycle_merge_sleeve__broader_origin__"
        "displacement_continuation__short"
    )
    row_sha = "3dbe5a25b5ca98140881dd204b5189d0c032ba565c6ea9690ee3715fc7b99005"
    candidate = _ensure_fixture_quality_aliases(
        {
            "candidate_id": candidate_id,
            "decision_time_utc": decision_time,
            "symbol": "XAUUSD",
            "side": "SHORT",
            "origin_family": "displacement_continuation",
            "candidate_expected_net_r": 0.77,
            "candidate_probability": 0.74,
            "candidate_fill_probability": 0.92,
            "source_completeness": 1.0,
            "source_completeness_status": "source_completeness_present",
        }
    )
    _add_strict_limit_fillability(candidate, 0.92)
    selector_packet = {
        "action": "trade",
        "reason": "broker_net_probability_confluence_lifecycle_admission_passed",
        "component_scores": {
            "ultimate_candidate_package": {
                "matched_sleeves": [
                    {
                        "sleeve_id": sleeve_id,
                        "row_hash_sha256": row_sha,
                        "framework": "broader_origin",
                        "origin_family": "displacement_continuation",
                        "side": "SHORT",
                        "package_role": "scheduler_lifecycle_core",
                        "combined_source_bound_signal_r": 36423.104143333,
                    }
                ],
                "matched_sleeve_count": 1,
                "admission_sleeve_match_count": 1,
                "non_admission_sleeve_match_count": 0,
                "source_bound_package_candidate_use_allowed": True,
                "decision_status": "shadow_sleeve_matches_found",
                "role_disposition": "scheduler_lifecycle_core",
            }
        },
    }
    candidate.update(timewarp.scheduler_package_parity_fields(selector_packet))
    candidate.update(
        timewarp.executable_identity_fields(
            candidate,
            decision_time_utc=decision_time,
        )
    )
    assert candidate["canonical_replay_candidate_instance_key"] == instance_key
    assert candidate["source_bound_replay_candidate_instance_key"] == instance_key
    candidate.update(
        timewarp.ultimate_package_owner_approved_family_root_admission_fields(
            candidate,
            {
                "gtos_vnext_runtime": {
                    "ultimate_candidate_package_owner_approved_family_root_admission": {
                        "policy_id": "owner_xau_displacement_short_family_root_v1",
                        "symbol": "XAUUSD",
                        "side": "SHORT",
                        "origin_family": "displacement_continuation",
                        "required_sleeve_id": sleeve_id,
                        "required_registry_row_sha256": row_sha,
                        "required_package_role": "scheduler_lifecycle_core",
                        "research_only": True,
                        "live_broker_authority": False,
                        "uses_outcome_fields": False,
                    }
                }
            },
        )
    )
    packets = {
        "selector_packet": selector_packet,
        "pretrade_broker_net_cost_packet": _cost_packet(),
        "expected_net_r": 0.77,
        "probability": 0.74,
        "fill_probability": 0.92,
        "source_completeness": 1.0,
        "predecision_limit_fillability": candidate["predecision_limit_fillability"],
    }
    monkeypatch.setattr(timewarp, "ultimate_package_member_axis_rows", lambda: ())

    seed = timewarp.package_effective_signal_seed(
        candidate=candidate,
        packets=packets,
    )
    detail = timewarp.exact_member_axis_provisional_new_entry_authority_detail(
        selector_packet,
        seed,
        packets,
        decision_time_utc=decision_time,
    )

    assert seed["ultimate_package_admission_member_axis_match_count"] == 0
    assert seed["ultimate_package_source_bound_candidate_use_allowed"] is True, (
        timewarp._owner_approved_family_root_admission_detail(seed)
    )
    assert seed["package_source_bound_authority_status"] == (
        "owner_approved_research_family_root_identity_materialized"
    )
    assert detail["authority_lineage_kind"] == "owner_approved_family_root"
    assert detail["provisional_signing_allowed"] is True
    assert detail["failures"] == ()

    root_only_surface = {
        key: candidate[key]
        for key in (
            "candidate_id",
            "decision_time_utc",
            "canonical_replay_candidate_instance_key",
            "source_bound_replay_candidate_instance_key",
            "candidate_instance_identity_status",
            "symbol",
            "side",
            "origin_family",
            "ultimate_package_matched_sleeve_authorities",
            "ultimate_package_admission_sleeve_match_count",
            "ultimate_package_combined_source_bound_signal_r_sum",
            "ultimate_package_owner_approved_family_root_admission_allowed",
            "ultimate_package_owner_approved_family_root_admission_payload",
            "ultimate_package_owner_approved_family_root_admission_hash_sha256",
        )
    }
    assert timewarp.package_source_bound_or_admission_alias_allowed(
        root_only_surface
    )
    stale_false_reason = (
        "explicit_package_replay_executable_rejected:"
        "source_bound_package_candidate_use_not_allowed"
    )
    assert timewarp.explicit_package_false_reason_can_be_rederived(
        stale_false_reason,
        root_only_surface,
    )
    assert timewarp.explicit_package_false_reason_can_be_rederived_for_order_release(
        stale_false_reason,
        root_only_surface,
    )
    assert timewarp.explicit_package_false_reason_can_be_rederived(
        "package_replay_executable_candidate_use_not_allowed:" + stale_false_reason,
        root_only_surface,
    )

    tampered_root = dict(root_only_surface)
    tampered_root[
        "ultimate_package_owner_approved_family_root_admission_hash_sha256"
    ] = "0" * 64
    assert not timewarp.package_source_bound_or_admission_alias_allowed(tampered_root)
    assert not timewarp.explicit_package_false_reason_can_be_rederived(
        stale_false_reason,
        tampered_root,
    )
    assert not timewarp.explicit_package_false_reason_can_be_rederived(
        "explicit_package_replay_executable_rejected:daily_loss_lockout",
        root_only_surface,
    )


def test_owner_approved_family_root_refuses_when_registry_sleeve_hash_is_not_matched() -> None:
    decision_time = "2025-10-27T08:30:00+00:00"
    candidate_id = "broadorigin_owner_xau_bad_root"
    instance_key = f"{candidate_id}@@{decision_time}"
    candidate = {
        "candidate_id": candidate_id,
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": instance_key,
        "source_bound_replay_candidate_instance_key": instance_key,
        "candidate_instance_identity_status": "materialized",
        "symbol": "XAUUSD",
        "side": "SHORT",
        "origin_family": "displacement_continuation",
        "ultimate_package_admission_sleeve_match_count": 1,
        "ultimate_package_combined_source_bound_signal_r_sum": 12.0,
        "ultimate_package_matched_sleeve_authorities": [],
    }
    fields = timewarp.ultimate_package_owner_approved_family_root_admission_fields(
        candidate,
        {
            "gtos_vnext_runtime": {
                "ultimate_candidate_package_owner_approved_family_root_admission": {
                    "policy_id": "owner_xau_displacement_short_family_root_v1",
                    "symbol": "XAUUSD",
                    "side": "SHORT",
                    "origin_family": "displacement_continuation",
                    "required_sleeve_id": "missing-sleeve",
                    "required_registry_row_sha256": "a" * 64,
                    "required_package_role": "scheduler_lifecycle_core",
                    "research_only": True,
                    "live_broker_authority": False,
                    "uses_outcome_fields": False,
                }
            }
        },
    )

    assert fields[
        "ultimate_package_owner_approved_family_root_admission_allowed"
    ] is False
    assert "owner_approved_family_root_required_sleeve_not_matched" in fields[
        "ultimate_package_owner_approved_family_root_admission_failures"
    ]


@pytest.mark.parametrize(
    ("expected_net_r", "expected_materialized"),
    ((0.82, True), (0.646438955, False)),
)
def test_exact_member_axis_reduce_risk_provisional_authority_is_signed_before_scheduler(
    monkeypatch,
    expected_net_r: float,
    expected_materialized: bool,
) -> None:
    captured = {}

    def fake_allocate(window, config, *, raw_config=None):
        captured["window"] = window
        captured["config"] = config
        return {
            "selected_candidate_id": "candidate-router-exact-member",
            "selected_candidate_ids": ["candidate-router-exact-member"],
            "option_trace": [],
        }

    monkeypatch.setattr(timewarp, "allocate_decision_window", fake_allocate)
    decision_time = "2025-06-11T08:15:00+00:00"
    candidate_id = "candidate-router-exact-member"
    member_axis_id = f"member_axis:{candidate_id}"
    monkeypatch.setattr(
        timewarp,
        "ultimate_package_member_axis_rows",
        lambda: (
            {
                "stable_member_axis_id": member_axis_id,
                "symbol": "XAUUSD",
                "side": "SHORT",
                "package_role": "scheduler_lifecycle_core",
                "combined_source_bound_signal_r": 12.5,
            },
        ),
    )
    instance_key = f"{candidate_id}@@{decision_time}"
    candidate = {
        "candidate_id": candidate_id,
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": instance_key,
        "source_bound_replay_candidate_instance_key": instance_key,
        "candidate_instance_identity_status": "materialized",
        "symbol": "XAUUSD",
        "side": "SHORT",
        "risk_reward_ratio": 2.0,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "source_bound_package_candidate_use_allowed": True,
        "candidate_expected_net_r": expected_net_r,
        "candidate_probability": 0.76,
        "candidate_confidence": 0.70,
        "candidate_fill_probability": 0.92,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "source_window_complete": True,
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "candidate_expected_net_r",
            "probability": "candidate_probability",
            "confidence": "candidate_confidence",
            "fill_probability": "candidate_fill_probability",
            "source_completeness": "source_completeness",
        },
        "candidate_decision_quality_alias_status": "exact_materialized",
        "candidate_decision_quality_source_boundary": (
            "predecision_fixture_quality_fields_no_outcome"
        ),
    }
    _add_strict_limit_fillability(candidate, 0.037322039)
    selector_reason = (
        "ultimate_candidate_package_dynamic_router_refusal_softened_reduce_risk"
    )
    selector_packet = _selector_packet(selector_reason)
    selector_packet["component_scores"][
        "ultimate_candidate_package_reduce_risk_authority"
    ] = {
        "applies": True,
        "allowed": True,
        "authority_family": "router_refusal_softening",
        "selector_reason": selector_reason,
        "source_bound_candidate_use_allowed_now": True,
        "broker_cost_passed_for_package_router": True,
        "positive_predecision_package_edge": True,
        "source_boundary": (
            "predecision_package_reduce_risk_new_order_authority_no_outcome_fields"
        ),
    }
    packets = {
        instance_key: {
            "selector_packet": selector_packet,
            "probability_packet": {
                "theses": [
                    {
                        "action": "short",
                        "probability": 0.76,
                        "EV": 0.87,
                        "confidence": 0.70,
                    }
                ]
            },
            "lifecycle_packet": {"action": "new_position"},
            "pretrade_broker_net_cost_packet": _cost_packet(),
            "expected_net_r": expected_net_r,
            "probability": 0.76,
            "confidence": 0.70,
            "fill_probability": 0.92,
            "source_completeness": 1.0,
            "predecision_limit_fillability": candidate[
                "predecision_limit_fillability"
            ],
        }
    }

    timewarp.materialize_scheduler_window(
        asof_utc=decision_time,
        candidates=[candidate],
        v4_packets=packets,
        config={
            "gtos_vnext_runtime": {
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_"
                "router_refusal_package_new_entry_authority_enabled": True,
            }
        },
    )

    assert len(captured["window"]["candidates"]) == int(expected_materialized), {
        "skip_reason": candidate.get("scheduler_materialization_skip_reason"),
        "identity_allowed": candidate.get(
            "scheduler_materialization_exact_member_axis_authority_finalization_allowed"
        ),
        "signed_claim": candidate.get(
            "scheduler_materialization_existing_package_new_entry_signed_claim"
        ),
        "authority_valid": (
            candidate.get("ultimate_candidate_package_reduce_risk_authority")
            or {}
        ).get("package_new_entry_authority_valid"),
        "authority_status": (
            candidate.get("ultimate_candidate_package_reduce_risk_authority")
            or {}
        ).get("package_new_entry_authority_status"),
        "authority_failures": (
            candidate.get("ultimate_candidate_package_reduce_risk_authority")
            or {}
        ).get("package_new_entry_authority_failures"),
    }
    authority = candidate["ultimate_candidate_package_reduce_risk_authority"]
    assert authority["package_new_entry_authority_valid"] is expected_materialized
    if not expected_materialized:
        assert candidate["scheduler_materialization_skip_reason"] == (
            "package_positive_reduce_risk_signed_authority_invalid"
        )
        assert "router_refusal_expected_net_r_below_floor" in authority[
            "package_new_entry_authority_failures"
        ]
        assert candidate.get(
            "scheduler_materialization_provisional_authority_finalized"
        ) is not True
        return
    assert authority["authority_family"] == "router_refusal_softening"
    assert authority["selector_reason"] == selector_reason
    assert authority["package_new_entry_authority_payload"][
        "execution_fill_probability"
    ] == 0.037322039
    assert candidate[
        "scheduler_materialization_exact_member_axis_provisional_authority_allowed"
    ] is True
    assert candidate["scheduler_materialization_provisional_authority_finalized"] is True
    assert candidate[
        "scheduler_materialization_provisional_authority_finalized_field"
    ] == "ultimate_candidate_package_reduce_risk_authority"


def test_exact_member_axis_open_reduced_provisional_authority_is_signed_before_scheduler(
    monkeypatch,
) -> None:
    captured = {}

    def fake_allocate(window, config, *, raw_config=None):
        captured["window"] = window
        captured["config"] = config
        return {
            "selected_candidate_id": "candidate-open-exact-member",
            "selected_candidate_ids": ["candidate-open-exact-member"],
            "option_trace": [],
        }

    monkeypatch.setattr(timewarp, "allocate_decision_window", fake_allocate)
    decision_time = "2025-06-11T08:15:00+00:00"
    candidate_id = "candidate-open-exact-member"
    member_axis_id = f"member_axis:{candidate_id}"
    monkeypatch.setattr(
        timewarp,
        "ultimate_package_member_axis_rows",
        lambda: (
            {
                "stable_member_axis_id": member_axis_id,
                "symbol": "US30_cash",
                "side": "LONG",
                "package_role": "scheduler_lifecycle_core",
                "combined_source_bound_signal_r": 18.0,
            },
        ),
    )
    instance_key = f"{candidate_id}@@{decision_time}"
    reason = "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk"
    candidate = {
        "candidate_id": candidate_id,
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": instance_key,
        "source_bound_replay_candidate_instance_key": instance_key,
        "candidate_instance_identity_status": "materialized",
        "symbol": "US30_cash",
        "side": "LONG",
        "risk_reward_ratio": 2.0,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "source_bound_package_candidate_use_allowed": True,
        "candidate_expected_net_r": 0.91,
        "candidate_probability": 0.79,
        "candidate_confidence": 0.74,
        "candidate_fill_probability": 0.92,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "source_window_complete": True,
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "candidate_expected_net_r",
            "probability": "candidate_probability",
            "confidence": "candidate_confidence",
            "fill_probability": "candidate_fill_probability",
            "source_completeness": "source_completeness",
        },
        "candidate_decision_quality_alias_status": "exact_materialized",
        "candidate_decision_quality_source_boundary": (
            "predecision_fixture_quality_fields_no_outcome"
        ),
    }
    _add_strict_limit_fillability(candidate, 0.92)
    selector_packet = _selector_packet(reason, action="open-reduced-risk")
    selector_packet["component_scores"][
        "ultimate_candidate_package_open_reduced_risk_authority"
    ] = {
        "applies": True,
        "allowed": True,
        "authority_family": "router_refusal_softening",
        "selector_reason": reason,
        "router_refusal_min_expected_net_r": 0.70,
        "router_refusal_min_probability": 0.70,
        "router_refusal_min_fill_probability": 0.80,
        "router_refusal_min_source_completeness": 0.95,
    }
    packets = {
        instance_key: {
            "selector_packet": selector_packet,
            "probability_packet": {
                "theses": [
                    {
                        "action": "long",
                        "probability": 0.79,
                        "EV": 0.96,
                        "confidence": 0.74,
                    }
                ]
            },
            "lifecycle_packet": {"action": "new_position"},
            "pretrade_broker_net_cost_packet": _cost_packet(),
            "expected_net_r": 0.91,
            "probability": 0.79,
            "confidence": 0.74,
            "fill_probability": 0.92,
            "source_completeness": 1.0,
            "predecision_limit_fillability": candidate[
                "predecision_limit_fillability"
            ],
        }
    }

    timewarp.materialize_scheduler_window(
        asof_utc=decision_time,
        candidates=[candidate],
        v4_packets=packets,
        config={
            "gtos_vnext_runtime": {
                "ultimate_candidate_package_positive_predecision_router_"
                "refusal_open_reduced_risk_allowed": True,
            }
        },
    )

    assert len(captured["window"]["candidates"]) == 1, {
        "skip_reason": candidate.get("scheduler_materialization_skip_reason"),
        "identity_allowed": candidate.get(
            "scheduler_materialization_exact_member_axis_authority_finalization_allowed"
        ),
        "signed_claim": candidate.get(
            "scheduler_materialization_existing_package_new_entry_signed_claim"
        ),
        "authority_valid": (
            candidate.get("ultimate_candidate_package_open_reduced_risk_authority")
            or {}
        ).get("package_new_entry_authority_valid"),
        "authority_nested_status": (
            candidate.get("ultimate_candidate_package_open_reduced_risk_authority")
            or {}
        ).get("package_new_entry_authority_status"),
        "authority_nested_failures": (
            candidate.get("ultimate_candidate_package_open_reduced_risk_authority")
            or {}
        ).get("package_new_entry_authority_failures"),
        "authority_status": candidate.get("package_new_entry_authority_status"),
        "authority_failures": candidate.get("package_new_entry_authority_failures"),
    }
    authority = candidate[
        "ultimate_candidate_package_open_reduced_risk_authority"
    ]
    assert authority["package_new_entry_authority_valid"] is True
    assert authority["authority_family"] == "router_refusal_softening"
    assert candidate["scheduler_materialization_provisional_authority_finalized"] is True
    assert candidate[
        "scheduler_materialization_provisional_authority_finalized_field"
    ] == "ultimate_candidate_package_open_reduced_risk_authority"


def test_exact_member_axis_provisional_authority_requires_atomic_fillability() -> None:
    decision_time = "2025-06-11T08:15:00+00:00"
    candidate_id = "candidate-exact-member-missing-atomic-fill"
    instance_key = f"{candidate_id}@@{decision_time}"
    candidate = _ensure_fixture_quality_aliases(
        {
            "candidate_id": candidate_id,
            "decision_time_utc": decision_time,
            "canonical_replay_candidate_instance_key": instance_key,
            "source_bound_replay_candidate_instance_key": instance_key,
            "candidate_instance_identity_status": "materialized",
            "symbol": "US30_cash",
            "side": "LONG",
            "candidate_expected_net_r": 0.91,
            "probability": 0.79,
            "confidence": 0.74,
            "candidate_fill_probability": 0.92,
            "fill_probability": 0.92,
            "source_completeness": 1.0,
            "source_completeness_status": "source_completeness_present",
        }
    )
    _add_exact_member_axis_execution_evidence(candidate)
    selector_packet = _selector_packet(
        "numeric_confluence_structured_disagreement"
    )
    selector_packet["component_scores"][
        "ultimate_candidate_package_reduce_risk_authority"
    ] = {
        "applies": True,
        "allowed": True,
        "authority_family": "numeric_disagreement_softening",
    }
    packets = {
        "selector_packet": selector_packet,
        "pretrade_broker_net_cost_packet": _cost_packet(),
        "expected_net_r": 0.91,
        "probability": 0.79,
        "source_completeness": 1.0,
    }

    detail = timewarp.exact_member_axis_provisional_new_entry_authority_detail(
        selector_packet,
        candidate,
        packets,
        decision_time_utc=decision_time,
    )

    assert detail["provisional_signing_allowed"] is False
    assert detail["atomic_execution_fillability_available"] is False
    assert "exact_member_axis_atomic_execution_fillability_missing" in detail[
        "failures"
    ]
    assert timewarp.selector_reduce_risk_package_new_entry_override_allowed(
        selector_packet,
        "new_position",
        candidate=candidate,
        packets=packets,
        runtime={
            "scheduler_v4_best_trade_allocator_selector_reduce_risk_"
            "numeric_disagreement_package_new_entry_authority_enabled": True,
        },
        provisional_authority_detail=detail,
    ) is False


def test_exact_member_axis_provisional_authority_does_not_restamp_tampered_claim() -> None:
    decision_time = "2025-06-11T08:15:00+00:00"
    candidate_id = "candidate-exact-member-tampered-claim"
    instance_key = f"{candidate_id}@@{decision_time}"
    selector_reason = "numeric_confluence_structured_disagreement"
    candidate = _ensure_fixture_quality_aliases(
        {
            "candidate_id": candidate_id,
            "candidate_id_source": "candidate_id",
            "decision_time_utc": decision_time,
            "canonical_replay_candidate_instance_key": instance_key,
            "source_bound_replay_candidate_instance_key": instance_key,
            "candidate_instance_identity_status": "materialized",
            "symbol": "US30_cash",
            "side": "LONG",
            "selector_action": "reduce-risk",
            "selector_reason": selector_reason,
            "action_intent": "new_position",
            "candidate_expected_net_r": 0.91,
            "probability": 0.79,
            "confidence": 0.74,
            "candidate_fill_probability": 0.92,
            "fill_probability": 0.92,
            "source_completeness": 1.0,
            "source_completeness_status": "source_completeness_present",
            "pretrade_cost_packet_status": "PASSED",
            "cost_authority": "broker_calibrated_replay_cost",
            "cost_source_gap_status": "source_bound_cost_authority_present",
            "candidate_cost_r_fallback_is_authority": False,
            "package_replay_order_executable_candidate_use_allowed": True,
            "package_replay_order_executable_candidate_use_allowed_reason": (
                "fixture_exact_member_axis_predecision_authorized"
            ),
            "package_replay_order_executable_authority_source": (
                "fixture_exact_member_axis_predecision_materialization"
            ),
        }
    )
    _add_exact_member_axis_execution_evidence(candidate)
    _add_strict_limit_fillability(candidate, 0.92)
    authority = scheduler.stamp_package_new_entry_authority(
        candidate,
        selector_action="reduce-risk",
        selector_reason=selector_reason,
        authority={
            "applies": True,
            "allowed": True,
            "authority_family": "numeric_disagreement_softening",
            "selector_reason": selector_reason,
            "source_boundary": (
                "predecision_exact_member_axis_materialization_no_outcome_fields"
            ),
        },
        action_intent="new_position",
        config={},
    )
    assert authority["package_new_entry_authority_valid"] is True
    tampered_authority = dict(authority)
    tampered_payload = dict(authority["package_new_entry_authority_payload"])
    tampered_payload["expected_net_r"] = 99.0
    tampered_authority["package_new_entry_authority_payload"] = tampered_payload
    candidate["ultimate_candidate_package_reduce_risk_authority"] = (
        tampered_authority
    )
    selector_packet = _selector_packet(selector_reason)
    selector_packet["component_scores"][
        "ultimate_candidate_package_reduce_risk_authority"
    ] = tampered_authority
    packets = {
        "selector_packet": selector_packet,
        "pretrade_broker_net_cost_packet": _cost_packet(),
        "predecision_limit_fillability": candidate[
            "predecision_limit_fillability"
        ],
        "execution_fill_probability": candidate["execution_fill_probability"],
        "execution_fill_probability_source": candidate[
            "execution_fill_probability_source"
        ],
        "execution_fill_probability_source_time_utc": candidate[
            "execution_fill_probability_source_time_utc"
        ],
        "execution_fill_probability_source_boundary": candidate[
            "execution_fill_probability_source_boundary"
        ],
    }

    detail = timewarp.exact_member_axis_provisional_new_entry_authority_detail(
        selector_packet,
        candidate,
        packets,
        decision_time_utc=decision_time,
    )

    assert detail["existing_signed_claim"] is True
    assert detail["signed_same_instance_valid"] is False
    assert detail["provisional_signing_allowed"] is False
    assert "existing_signed_authority_invalid_not_restampable" in detail[
        "failures"
    ]


def test_member_axis_package_positive_reduce_risk_missing_sizing_reaches_scheduler() -> None:
    selector = _selector_packet(
        "calibrated_admission_fill_probability_below_generalized_floor"
    )
    selector["final_risk_pct"] = 0.0
    candidate = {
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "ultimate_package_matched_member_axis_count": 2,
        "ultimate_package_admission_member_axis_match_count": 1,
        "ultimate_package_matched_member_axis_ids": [
            "member-axis-primary",
            "member-axis-secondary",
        ],
        "ultimate_package_member_axis_source_bound_signal_r_sum": 12.5,
        "candidate_expected_net_r": 0.67,
        "probability": 0.72,
        "fill_probability": 0.81,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "candidate_cost_r_fallback_is_authority": False,
    }
    packets = {
        "pretrade_broker_net_cost_packet": _cost_packet("PASSED"),
        "expected_net_r": 0.67,
    }

    effective = timewarp.ultimate_package_effective_signal_fields(candidate)
    reason = timewarp.selector_reduce_risk_new_entry_block_reason(
        selector,
        "new_position",
        candidate=candidate,
        packets=packets,
    )

    assert effective["ultimate_package_effective_evidence_source"] == (
        "member_axis_admission_source_bound_use_allowed"
    )
    assert effective["ultimate_package_scheduler_consumed_status"] == (
        "eligible_for_scheduler_consumption"
    )
    assert reason == "selector_reduce_risk_missing_positive_sizing"


def test_effective_package_quality_without_source_bound_admission_is_diagnostic() -> None:
    candidate = {
        "ultimate_package_matched_member_axis_count": 1,
        "ultimate_package_admission_member_axis_match_count": 1,
        "ultimate_package_matched_member_axis_ids": ["member-axis-diagnostic"],
        "ultimate_package_member_axis_source_bound_signal_r_sum": 8.0,
        "candidate_expected_net_r": 0.81,
        "probability": 0.76,
        "fill_probability": 0.91,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "candidate_cost_r_fallback_is_authority": False,
        "package_replay_executable_candidate_use_allowed": False,
        "package_replay_executable_candidate_use_allowed_reason": (
            "source_bound_package_replay_not_allowed"
        ),
    }

    effective = timewarp.ultimate_package_effective_signal_fields(candidate)

    assert effective["ultimate_package_derived_executable_quality_authority"] is True
    assert (
        effective["ultimate_package_effective_source_bound_candidate_use_allowed"]
        is False
    )
    assert effective["ultimate_package_effective_executable_authority_allowed"] is False
    assert effective["ultimate_package_scheduler_consumed_status"] == (
        "diagnostic_not_scheduler_consumed"
    )


def test_nonpackage_reduce_risk_new_entry_does_not_reach_scheduler(monkeypatch) -> None:
    captured = {}

    def fake_allocate(window, config, *, raw_config=None):
        captured["window"] = window
        captured["config"] = config
        return {
            "selected_candidate_id": None,
            "selected_candidate_ids": [],
            "option_trace": [],
        }

    monkeypatch.setattr(timewarp, "allocate_decision_window", fake_allocate)
    selector_packet = _selector_packet(
        "calibrated_admission_fill_probability_below_generalized_floor"
    )
    selector_packet["component_scores"]["ultimate_candidate_package"][
        "source_bound_package_candidate_use_allowed"
    ] = False
    candidate = {
        "candidate_id": "candidate-nonpackage",
        "symbol": "XAUUSD",
        "side": "LONG",
        "risk_reward_ratio": 2.0,
        "ultimate_package_source_bound_candidate_use_allowed": False,
        "candidate_expected_net_r": 0.67,
        "source_window_complete": True,
    }
    packets = {
        "candidate-nonpackage": {
            "selector_packet": selector_packet,
            "probability_packet": {
                "theses": [
                    {
                        "action": "long",
                        "probability": 0.72,
                        "EV": 0.78,
                        "confidence": 0.7,
                    }
                ]
            },
            "lifecycle_packet": {"action": "new_position"},
            "selector_event": {
                "predecision_limit_fillability": {"fill_probability": 0.81}
            },
            "pretrade_broker_net_cost_packet": _cost_packet(),
            "cost_r": 0.05,
            "broker_calibrated_expected_cost_r": 0.05,
            "expected_net_r": 0.67,
        }
    }

    timewarp.materialize_scheduler_window(
        asof_utc="2025-06-11T08:15:00+00:00",
        candidates=[candidate],
        v4_packets=packets,
        config={"gtos_vnext_runtime": {}},
    )

    assert captured["window"]["candidates"] == []
    assert candidate["scheduler_materialization_skip_reason"] == (
        "selector_reduce_risk_open_reduced_not_executable:open_reduced_authority_not_allowed"
    )
    assert candidate["scheduler_materialization_selector_action"] == "reduce-risk"


def test_package_positive_reduce_risk_keeps_refused_cost_blocked() -> None:
    selector = _selector_packet("numeric_confluence_structured_disagreement")
    candidate = {
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "candidate_expected_net_r": 0.67,
    }
    packets = {
        "pretrade_broker_net_cost_packet": _cost_packet("REFUSED"),
        "expected_net_r": 0.67,
    }

    reason = timewarp.selector_reduce_risk_new_entry_block_reason(
        selector,
        "new_position",
        candidate=candidate,
        packets=packets,
    )

    assert reason == (
        "selector_reduce_risk_new_entry_blocked:"
        "numeric_confluence_structured_disagreement"
    )


def test_package_positive_numeric_disagreement_reduce_risk_reaches_scheduler_with_cost_passed() -> None:
    reason_text = "numeric_confluence_structured_disagreement"
    selector = _selector_packet(reason_text)
    selector["component_scores"][
        "ultimate_candidate_package_open_reduced_risk_authority"
    ] = {
        "applies": True,
        "allowed": False,
        "authority_family": None,
        "source_bound_candidate_use_allowed_now": True,
        "broker_cost_passed_for_package_router": True,
        "positive_predecision_package_edge": True,
        "ultimate_package_soft_admission_override_allowed": True,
        "reduced_risk_reasons": [
            "numeric_confluence_structured_disagreement",
            "ultimate_candidate_package_dynamic_router_refusal_softened_reduce_risk",
            "ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay",
        ],
        "source_boundary": (
            "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
        ),
    }
    candidate = {
        "candidate_id": "candidate-numeric-reduce-risk-strict",
        "decision_time_utc": "2026-05-15T07:45:00+00:00",
        "selector_action": "reduce-risk",
        "selector_reason": reason_text,
        "action_intent": "new_position",
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "ultimate_package_matched_member_axis_count": 2,
        "ultimate_package_admission_member_axis_match_count": 1,
        "candidate_expected_net_r": 1.10,
        "confidence": 0.82,
        "candidate_confidence": 0.82,
        "probability": 0.72,
        "fill_probability": 0.81,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "candidate_expected_net_r",
            "probability": "probability",
            "confidence": "candidate_confidence",
            "fill_probability": "fill_probability",
            "source_completeness": "source_completeness",
        },
        "candidate_decision_quality_source_boundary": (
            "predecision_fixture_quality_fields_no_outcome"
        ),
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "candidate_cost_r_fallback_is_authority": False,
        "ultimate_candidate_package_reduce_risk_authority": {
            "applies": True,
            "allowed": True,
            "authority_family": "numeric_disagreement_softening",
            "current_config_allowed": True,
            "source_boundary": (
                "predecision_package_reduce_risk_new_order_authority_no_outcome_fields"
            ),
        },
    }
    _add_strict_limit_fillability(candidate, 0.81)
    _sign_package_new_entry_authority(candidate)
    selector["component_scores"][
        "ultimate_candidate_package_reduce_risk_authority"
    ] = candidate["ultimate_candidate_package_reduce_risk_authority"]
    selector["component_scores"][
        "selector_reduced_risk_new_position_signed_authority"
    ] = candidate["ultimate_candidate_package_reduce_risk_authority"]
    packets = {
        "pretrade_broker_net_cost_packet": _cost_packet("PASSED"),
        "expected_net_r": 1.10,
        "probability": 0.72,
        "confidence": 0.82,
        "fill_probability": 0.81,
        "source_completeness": 1.0,
    }

    reason = timewarp.selector_reduce_risk_new_entry_block_reason(
        selector,
        "new_position",
        candidate=candidate,
        packets=packets,
    )

    assert reason is None


def test_package_positive_reduce_risk_requires_explicit_authority_for_new_entry() -> None:
    reason_text = (
        "ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay"
    )
    selector = _selector_packet(reason_text)
    selector["component_scores"][
        "ultimate_candidate_package_reduce_risk_authority"
    ] = {
        "applies": True,
        "allowed": True,
        "authority_family": "fill_floor_softening",
        "source_boundary": (
            "predecision_package_reduce_risk_new_order_authority_no_outcome_fields"
        ),
    }
    candidate = {
        "candidate_id": "candidate-fill-floor-reduce-risk-strict",
        "decision_time_utc": "2026-05-15T07:45:00+00:00",
        "selector_action": "reduce-risk",
        "selector_reason": reason_text,
        "action_intent": "new_position",
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "ultimate_package_matched_member_axis_count": 2,
        "ultimate_package_admission_member_axis_match_count": 1,
        "candidate_expected_net_r": 1.10,
        "probability": 0.72,
        "fill_probability": 0.81,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "candidate_cost_r_fallback_is_authority": False,
    }
    candidate["ultimate_candidate_package_reduce_risk_authority"] = dict(
        selector["component_scores"][
            "ultimate_candidate_package_reduce_risk_authority"
        ]
    )
    _add_strict_limit_fillability(candidate, 0.81)
    _sign_package_new_entry_authority(candidate)
    selector["component_scores"][
        "ultimate_candidate_package_reduce_risk_authority"
    ] = candidate["ultimate_candidate_package_reduce_risk_authority"]
    selector["component_scores"][
        "selector_reduced_risk_new_position_signed_authority"
    ] = candidate["ultimate_candidate_package_reduce_risk_authority"]
    packets = {
        "selector_packet": selector,
        "pretrade_broker_net_cost_packet": _cost_packet("PASSED"),
        "expected_net_r": 1.10,
        "probability": 0.72,
        "fill_probability": 0.81,
        "source_completeness": 1.0,
    }

    reason = timewarp.selector_reduce_risk_new_entry_block_reason(
        selector,
        "new_position",
        candidate=candidate,
        packets=packets,
    )

    assert reason is None


def test_selector_not_risk_bearing_cost_missing_is_not_threshold_failure() -> None:
    reason = timewarp.selector_not_risk_bearing_materialization_skip_reason(
        selector_action="source-required",
        selector_reason="source_hold",
        packets={"pretrade_broker_net_cost_packet": {"status": "REFUSED"}},
        candidate={},
    )

    assert reason == "selector_not_risk_bearing_cost_missing"


def test_package_replay_executable_numeric_reduce_risk_below_floor_is_ranked_then_vetoed() -> None:
    candidate = {
        "candidate_id": "candidate-numeric-replay-executable",
        "symbol": "XAGUSD",
        "side": "LONG",
        "risk_reward_ratio": 2.0,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "ultimate_package_matched_member_axis_count": 2,
        "ultimate_package_admission_member_axis_match_count": 1,
        "ultimate_package_member_axis_source_bound_signal_r_sum": 12.5,
        "candidate_expected_net_r": 0.60,
        "source_window_complete": True,
    }
    packets = {
        "candidate-numeric-replay-executable": {
            "selector_packet": _selector_packet(
                "numeric_confluence_structured_disagreement"
            ),
            "probability_packet": {
                "theses": [
                    {
                        "action": "long",
                        "probability": 0.69,
                        "EV": 0.65,
                        "confidence": 0.7,
                    }
                ]
            },
            "lifecycle_packet": {"action": "new_position"},
            "selector_event": {
                "predecision_limit_fillability": {"fill_probability": 0.92}
            },
            "pretrade_broker_net_cost_packet": _cost_packet("PASSED"),
            "cost_r": 0.05,
            "broker_calibrated_expected_cost_r": 0.05,
            "expected_net_r": 0.60,
        }
    }

    packet = timewarp.materialize_scheduler_window(
        asof_utc="2025-06-11T08:15:00+00:00",
        candidates=[candidate],
        v4_packets=packets,
        config={
            "gtos_vnext_runtime": {
                "scheduler_v4_best_trade_allocator_min_trade_score": 0.0,
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_new_entry_penalty_enabled": True,
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_new_entry_quality_gate_enabled": True,
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_new_entry_risk_cap_enabled": True,
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_new_entry_max_risk_pct": 0.10,
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_authority_enabled": True,
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_expected_net_r": 0.70,
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_probability": 0.70,
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_fill_probability": 0.20,
                "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_source_completeness": 0.95,
            }
        },
    )

    assert candidate["scheduler_materialization_skip_reason"] == (
        "selector_reduce_risk_open_reduced_not_executable:open_reduced_authority_not_allowed"
    )
    assert all(
        row.get("candidate_id") != "candidate-numeric-replay-executable"
        for row in packet["all_options_preserved"]
    )


def test_scheduler_authority_bypass_keys_override_stale_legacy_fill_floor_aliases() -> None:
    config = scheduler.SchedulerV4Config.from_mapping(
        {
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_bypass_enabled": True,
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_bypass_selector_trade_only": True,
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_bypass_min_expected_net_r": 0.70,
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_bypass_min_probability": 0.70,
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_bypass_min_fill_probability": 0.20,
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_bypass_min_source_completeness": 0.95,
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_bypass_min_scheduler_score": 2.50,
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_authority_bypass_enabled": True,
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_authority_bypass_selector_trade_only": False,
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_authority_bypass_min_expected_net_r": 0.80,
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_authority_bypass_min_probability": 0.75,
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_authority_bypass_min_fill_probability": 0.25,
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_authority_bypass_min_source_completeness": 0.65,
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_authority_bypass_min_scheduler_score": 0.0,
        }
    )

    assert config.dynamic_budget_package_fill_floor_bypass_enabled is True
    assert config.dynamic_budget_package_fill_floor_bypass_selector_trade_only is False
    assert config.dynamic_budget_package_fill_floor_bypass_min_expected_net_r == 0.80
    assert config.dynamic_budget_package_fill_floor_bypass_min_probability == 0.75
    assert config.dynamic_budget_package_fill_floor_bypass_min_fill_probability == 0.25
    assert config.dynamic_budget_package_fill_floor_bypass_min_source_completeness == 0.65
    assert config.dynamic_budget_package_fill_floor_bypass_min_scheduler_score == 0.0


def test_package_replay_executable_numeric_reduce_risk_quality_pass_reaches_runtime() -> None:
    result = scheduler.allocate_decision_window(
        {
            "decision_window_id": "window:package-numeric-reduce-risk-runtime",
            "candidate_set_id": "candidate-set:package-numeric-reduce-risk-runtime",
            "asof_utc": "2026-05-15T07:45:00+00:00",
            "candidates": [
                _sign_package_new_entry_authority({
                    "candidate_id": "candidate-numeric-quality-pass",
                    "symbol": "XAUUSD",
                    "side": "SHORT",
                    "risk_reward_ratio": 2.0,
                    "dynamic_geometry_policy": "partial_be_runner",
                    "expected_net_r_selected_policy": "partial_be_runner",
                    "selected_policy_expected_net_calibration_status": (
                        "calibrated"
                    ),
                    "selected_policy_expected_net_calibration_source": (
                        "selected_policy_replay_calibration_packet"
                    ),
                    "action_intent": "new_position",
                    "selected_cell_risk_pct": 1.0,
                    "expected_net_r": 0.94,
                    "candidate_expected_net_r": 0.94,
                    "candidate_ev_r": 0.98,
                    "probability": 0.81,
                    "confidence": 0.82,
                    "candidate_confidence": 0.82,
                    "scheduler_confidence": 0.82,
                    "fill_probability": 0.40,
                    "source_completeness": 1.0,
                    "source_completeness_status": "complete",
                    "candidate_decision_quality_alias_status": "exact_materialized",
                    "candidate_decision_quality_field_sources": {
                        "expected_net_r": "candidate_expected_net_r",
                        "probability": "candidate_probability",
                        "confidence": "candidate_confidence",
                        "fill_probability": "candidate_fill_probability",
                        "source_completeness": "source_completeness",
                    },
                    "candidate_decision_quality_source_boundary": (
                        "predecision_fixture_quality_fields_no_outcome"
                    ),
                    "selector_action": "open-reduced-risk",
                    "selector_reason": (
                        "ultimate_candidate_package_numeric_disagreement_open_reduced_risk"
                    ),
                    "ultimate_candidate_package_open_reduced_risk_authority": {
                        "applies": True,
                        "allowed": True,
                        "authority_family": "numeric_disagreement_softening",
                    },
                    "ultimate_package_source_bound_candidate_use_allowed": True,
                    "ultimate_package_effective_source_bound_candidate_use_allowed": True,
                    "ultimate_package_matched_sleeve_count": 1.0,
                    "ultimate_package_admission_sleeve_match_count": 1.0,
                    "ultimate_package_effective_matched_count": 1.0,
                    "ultimate_package_effective_admission_count": 1.0,
                    "ultimate_package_effective_source_bound_signal_r": 46571.8,
                    "ultimate_package_role_disposition": "admission_candidate",
                    "package_replay_executable_candidate_use_allowed": True,
                    "package_replay_executable_candidate_use_allowed_reason": "broker_cost_and_scheduler_action_executable",
                    "pretrade_cost_packet_status": "PASSED",
                    "cost_authority": "broker_calibrated_replay_cost",
                    "cost_source_gap_status": "source_bound_cost_authority_present",
                    "candidate_cost_r_fallback_is_authority": False,
                    "cost_r": 0.03,
                })
            ],
        },
        {
            "enabled": True,
            "live_activation_allowed": False,
            "apply_to_execution": False,
            "min_trade_score": 0.0,
            "zero_trade_score": 0.2,
            "dynamic_budget_quality_gate_enabled": True,
            "dynamic_budget_min_expected_net_r": 0.20,
            "dynamic_budget_min_probability": 0.58,
            "dynamic_budget_min_fill_probability": 0.80,
            "dynamic_budget_min_source_completeness": 0.65,
            "selector_reduce_risk_new_entry_penalty_enabled": True,
            "selector_reduce_risk_new_entry_quality_gate_enabled": True,
            "selector_reduce_risk_new_entry_risk_cap_enabled": True,
            "selector_reduce_risk_new_entry_max_risk_pct": 0.10,
            "selector_reduce_risk_numeric_disagreement_package_new_entry_authority_enabled": True,
            "ultimate_candidate_package_numeric_disagreement_open_reduced_risk_enabled": True,
            "selector_reduce_risk_package_fill_floor_authority_enabled": True,
            "selector_reduce_risk_package_fill_floor_min_expected_net_r": 0.70,
            "selector_reduce_risk_package_fill_floor_min_probability": 0.70,
            "selector_reduce_risk_package_fill_floor_min_fill_probability": 0.25,
            "selector_reduce_risk_package_fill_floor_min_source_completeness": 0.65,
            "selector_reduce_risk_package_fill_floor_release_risk_cap_enabled": True,
            "selector_reduce_risk_package_fill_floor_release_max_risk_pct": 0.25,
            "dynamic_budget_package_fill_floor_authority_bypass_enabled": True,
            "dynamic_budget_package_fill_floor_authority_bypass_selector_trade_only": False,
            "dynamic_budget_package_fill_floor_authority_bypass_min_expected_net_r": 0.80,
            "dynamic_budget_package_fill_floor_authority_bypass_min_probability": 0.75,
            "dynamic_budget_package_fill_floor_authority_bypass_min_fill_probability": 0.25,
            "dynamic_budget_package_fill_floor_authority_bypass_min_source_completeness": 0.65,
            "dynamic_budget_package_fill_floor_authority_bypass_min_scheduler_score": 0.0,
        },
    )

    option = next(
        row
        for row in result["all_options_preserved"]
        if row.get("candidate_id") == "candidate-numeric-quality-pass"
    )
    assert option["runtime_eligible"] is True
    assert (
        option["decision_status"]
        == "candidate_admitted_selector_open_reduced_risk_package_cap_released_bounded"
    )
    assert option["approved_risk_pct"] == 0.25
    assert option["vetoes"] == []
    package_authority = option["score_components"][
        "selector_reduce_risk_package_fill_floor_authority"
    ]
    assert package_authority["applies"] is True
    assert package_authority["allowed"] is True
    assert package_authority["package_open_reduced_authority_applies"] is True
    assert package_authority["package_open_reduced_authority_allowed"] is True
    replay_authority = option["score_components"][
        "selector_reduce_risk_package_replay_executable_authority"
    ]
    assert replay_authority["applies"] is True
    assert replay_authority["allowed"] is True


def test_package_reduce_risk_release_at_cap_gets_explicit_package_status() -> None:
    result = scheduler.allocate_decision_window(
        {
            "decision_window_id": "window:package-numeric-reduce-risk-at-release-cap",
            "candidate_set_id": "candidate-set:package-numeric-reduce-risk-at-release-cap",
            "asof_utc": "2026-05-15T07:45:00+00:00",
            "candidates": [
                _sign_package_new_entry_authority({
                    "candidate_id": "candidate-numeric-quality-pass-at-release-cap",
                    "symbol": "XAUUSD",
                    "side": "SHORT",
                    "risk_reward_ratio": 2.0,
                    "dynamic_geometry_policy": "partial_be_runner",
                    "expected_net_r_selected_policy": "partial_be_runner",
                    "selected_policy_expected_net_calibration_status": "calibrated",
                    "selected_policy_expected_net_calibrated": True,
                    "selected_policy_expected_net_calibration_source": (
                        "selected_policy_replay_calibration_packet"
                    ),
                    "selected_policy_expected_net_calibration_source_boundary": (
                        "predecision_fixture_quality_fields_no_outcome"
                    ),
                    "action_intent": "new_position",
                    "selected_cell_risk_pct": 0.25,
                    "expected_net_r": 0.94,
                    "candidate_expected_net_r": 0.94,
                    "candidate_ev_r": 0.98,
                    "probability": 0.81,
                    "confidence": 0.82,
                    "candidate_confidence": 0.82,
                    "scheduler_confidence": 0.82,
                    "fill_probability": 0.40,
                    "source_completeness": 1.0,
                    "source_completeness_status": "complete",
                    "candidate_decision_quality_alias_status": "exact_materialized",
                    "candidate_decision_quality_field_sources": {
                        "expected_net_r": "candidate_expected_net_r",
                        "probability": "candidate_probability",
                        "confidence": "candidate_confidence",
                        "fill_probability": "candidate_fill_probability",
                        "source_completeness": "source_completeness",
                    },
                    "candidate_decision_quality_source_boundary": (
                        "predecision_fixture_quality_fields_no_outcome"
                    ),
                    "selector_action": "open-reduced-risk",
                    "selector_reason": (
                        "ultimate_candidate_package_numeric_disagreement_open_reduced_risk"
                    ),
                    "ultimate_candidate_package_open_reduced_risk_authority": {
                        "applies": True,
                        "allowed": True,
                        "authority_family": "numeric_disagreement_softening",
                    },
                    "ultimate_package_source_bound_candidate_use_allowed": True,
                    "ultimate_package_effective_source_bound_candidate_use_allowed": True,
                    "ultimate_package_matched_sleeve_count": 1.0,
                    "ultimate_package_admission_sleeve_match_count": 1.0,
                    "ultimate_package_effective_matched_count": 1.0,
                    "ultimate_package_effective_admission_count": 1.0,
                    "ultimate_package_effective_source_bound_signal_r": 46571.8,
                    "ultimate_package_role_disposition": "admission_candidate",
                    "package_replay_executable_candidate_use_allowed": True,
                    "package_replay_executable_candidate_use_allowed_reason": "broker_cost_and_scheduler_action_executable",
                    "pretrade_cost_packet_status": "PASSED",
                    "cost_authority": "broker_calibrated_replay_cost",
                    "cost_source_gap_status": "source_bound_cost_authority_present",
                    "candidate_cost_r_fallback_is_authority": False,
                    "cost_r": 0.03,
                })
            ],
        },
        {
            "enabled": True,
            "live_activation_allowed": False,
            "apply_to_execution": False,
            "min_trade_score": 0.0,
            "zero_trade_score": 0.2,
            "dynamic_budget_quality_gate_enabled": True,
            "dynamic_budget_min_expected_net_r": 0.20,
            "dynamic_budget_min_probability": 0.58,
            "dynamic_budget_min_fill_probability": 0.80,
            "dynamic_budget_min_source_completeness": 0.65,
            "selector_reduce_risk_new_entry_penalty_enabled": True,
            "selector_reduce_risk_new_entry_quality_gate_enabled": True,
            "selector_reduce_risk_new_entry_risk_cap_enabled": True,
            "selector_reduce_risk_new_entry_max_risk_pct": 0.10,
            "selector_reduce_risk_numeric_disagreement_package_new_entry_authority_enabled": True,
            "ultimate_candidate_package_numeric_disagreement_open_reduced_risk_enabled": True,
            "selector_reduce_risk_package_fill_floor_authority_enabled": True,
            "selector_reduce_risk_package_fill_floor_min_expected_net_r": 0.70,
            "selector_reduce_risk_package_fill_floor_min_probability": 0.70,
            "selector_reduce_risk_package_fill_floor_min_fill_probability": 0.25,
            "selector_reduce_risk_package_fill_floor_min_source_completeness": 0.65,
            "selector_reduce_risk_package_fill_floor_release_risk_cap_enabled": True,
            "selector_reduce_risk_package_fill_floor_release_max_risk_pct": 0.25,
            "dynamic_budget_package_fill_floor_authority_bypass_enabled": True,
            "dynamic_budget_package_fill_floor_authority_bypass_selector_trade_only": False,
            "dynamic_budget_package_fill_floor_authority_bypass_min_expected_net_r": 0.80,
            "dynamic_budget_package_fill_floor_authority_bypass_min_probability": 0.75,
            "dynamic_budget_package_fill_floor_authority_bypass_min_fill_probability": 0.25,
            "dynamic_budget_package_fill_floor_authority_bypass_min_source_completeness": 0.65,
            "dynamic_budget_package_fill_floor_authority_bypass_min_scheduler_score": 0.0,
        },
    )

    option = next(
        row
        for row in result["all_options_preserved"]
        if row.get("candidate_id") == "candidate-numeric-quality-pass-at-release-cap"
    )
    assert option["runtime_eligible"] is True
    assert (
        option["decision_status"]
        == "candidate_admitted_selector_open_reduced_risk_package_cap_released_bounded"
    )
    assert option["approved_risk_pct"] == 0.25
    assert option["vetoes"] == []
    selected_option = next(
        row
        for row in result["decision"]["selected_options"]
        if row.get("candidate_id") == "candidate-numeric-quality-pass-at-release-cap"
    )
    assert selected_option["approved_risk_pct"] == option["approved_risk_pct"]
    assert selected_option["decision_status"] == option["decision_status"]
    assert selected_option["reason"] == option["reason"]
    assert selected_option["package_replay_executable_candidate_use_allowed"] is True
    assert option["package_replay_executable_candidate_use_allowed"] is True
    assert selected_option["pretrade_cost_packet_status"] == "PASSED"
    assert option["pretrade_cost_packet_status"] == "PASSED"
    authority = option["score_components"]["selector_reduce_risk_new_entry_authority"]
    assert authority.get("risk_cap_released_for_package_fill_floor") is True
    assert authority.get("risk_cap_release_max_risk_pct") == 0.25
    package_authority = option["score_components"][
        "selector_reduce_risk_package_fill_floor_authority"
    ]
    assert package_authority["applies"] is True
    assert package_authority["allowed"] is True
    assert option["candidate_decision_quality_alias_status"] == "exact_materialized"
    assert (
        option["candidate_decision_quality_field_sources"]["expected_net_r"]
        == "candidate_expected_net_r"
    )


def test_package_reduce_risk_quality_pass_below_cap_gets_explicit_package_status() -> None:
    result = scheduler.allocate_decision_window(
        {
            "decision_window_id": "window:package-numeric-reduce-risk-below-cap",
            "candidate_set_id": "candidate-set:package-numeric-reduce-risk-below-cap",
            "asof_utc": "2026-05-15T07:45:00+00:00",
            "candidates": [
                _sign_package_new_entry_authority({
                    "candidate_id": "candidate-numeric-quality-pass-below-cap",
                    "symbol": "XAUUSD",
                    "side": "SHORT",
                    "risk_reward_ratio": 2.0,
                    "dynamic_geometry_policy": "partial_be_runner",
                    "expected_net_r_selected_policy": "partial_be_runner",
                    "selected_policy_expected_net_calibration_status": "calibrated",
                    "selected_policy_expected_net_calibrated": True,
                    "selected_policy_expected_net_calibration_source": (
                        "selected_policy_replay_calibration_packet"
                    ),
                    "selected_policy_expected_net_calibration_source_boundary": (
                        "predecision_fixture_quality_fields_no_outcome"
                    ),
                    "action_intent": "new_position",
                    "selected_cell_risk_pct": 0.10,
                    "expected_net_r": 0.94,
                    "candidate_expected_net_r": 0.94,
                    "candidate_ev_r": 0.98,
                    "probability": 0.81,
                    "confidence": 0.82,
                    "candidate_confidence": 0.82,
                    "scheduler_confidence": 0.82,
                    "fill_probability": 0.40,
                    "source_completeness": 1.0,
                    "source_completeness_status": "complete",
                    "candidate_decision_quality_alias_status": "exact_materialized",
                    "candidate_decision_quality_field_sources": {
                        "expected_net_r": "candidate_expected_net_r",
                        "probability": "candidate_probability",
                        "confidence": "candidate_confidence",
                        "fill_probability": "candidate_fill_probability",
                        "source_completeness": "source_completeness",
                    },
                    "candidate_decision_quality_source_boundary": (
                        "predecision_fixture_quality_fields_no_outcome"
                    ),
                    "selector_action": "open-reduced-risk",
                    "selector_reason": (
                        "ultimate_candidate_package_numeric_disagreement_open_reduced_risk"
                    ),
                    "ultimate_candidate_package_open_reduced_risk_authority": {
                        "applies": True,
                        "allowed": True,
                        "authority_family": "numeric_disagreement_softening",
                    },
                    "ultimate_package_source_bound_candidate_use_allowed": True,
                    "ultimate_package_effective_source_bound_candidate_use_allowed": True,
                    "ultimate_package_matched_sleeve_count": 1.0,
                    "ultimate_package_admission_sleeve_match_count": 1.0,
                    "ultimate_package_effective_matched_count": 1.0,
                    "ultimate_package_effective_admission_count": 1.0,
                    "ultimate_package_effective_source_bound_signal_r": 46571.8,
                    "ultimate_package_role_disposition": "admission_candidate",
                    "package_replay_executable_candidate_use_allowed": True,
                    "package_replay_executable_candidate_use_allowed_reason": "broker_cost_and_scheduler_action_executable",
                    "pretrade_cost_packet_status": "PASSED",
                    "cost_authority": "broker_calibrated_replay_cost",
                    "cost_source_gap_status": "source_bound_cost_authority_present",
                    "candidate_cost_r_fallback_is_authority": False,
                    "cost_r": 0.03,
                })
            ],
        },
        {
            "enabled": True,
            "live_activation_allowed": False,
            "apply_to_execution": False,
            "min_trade_score": 0.0,
            "zero_trade_score": 0.2,
            "dynamic_budget_quality_gate_enabled": True,
            "dynamic_budget_min_expected_net_r": 0.20,
            "dynamic_budget_min_probability": 0.58,
            "dynamic_budget_min_fill_probability": 0.80,
            "dynamic_budget_min_source_completeness": 0.65,
            "selector_reduce_risk_new_entry_penalty_enabled": True,
            "selector_reduce_risk_new_entry_quality_gate_enabled": True,
            "selector_reduce_risk_new_entry_risk_cap_enabled": True,
            "selector_reduce_risk_new_entry_max_risk_pct": 0.10,
            "selector_reduce_risk_numeric_disagreement_package_new_entry_authority_enabled": True,
            "ultimate_candidate_package_numeric_disagreement_open_reduced_risk_enabled": True,
            "selector_reduce_risk_package_fill_floor_authority_enabled": True,
            "selector_reduce_risk_package_fill_floor_min_expected_net_r": 0.70,
            "selector_reduce_risk_package_fill_floor_min_probability": 0.70,
            "selector_reduce_risk_package_fill_floor_min_fill_probability": 0.25,
            "selector_reduce_risk_package_fill_floor_min_source_completeness": 0.65,
            "selector_reduce_risk_package_fill_floor_release_risk_cap_enabled": True,
            "selector_reduce_risk_package_fill_floor_release_max_risk_pct": 0.25,
            "dynamic_budget_package_fill_floor_authority_bypass_enabled": True,
            "dynamic_budget_package_fill_floor_authority_bypass_selector_trade_only": False,
            "dynamic_budget_package_fill_floor_authority_bypass_min_expected_net_r": 0.80,
            "dynamic_budget_package_fill_floor_authority_bypass_min_probability": 0.75,
            "dynamic_budget_package_fill_floor_authority_bypass_min_fill_probability": 0.25,
            "dynamic_budget_package_fill_floor_authority_bypass_min_source_completeness": 0.65,
            "dynamic_budget_package_fill_floor_authority_bypass_min_scheduler_score": 0.0,
        },
    )

    option = next(
        row
        for row in result["all_options_preserved"]
        if row.get("candidate_id") == "candidate-numeric-quality-pass-below-cap"
    )
    assert option["runtime_eligible"] is True
    assert (
        option["decision_status"]
        == "candidate_admitted_selector_open_reduced_risk_package_authority"
    )
    assert option["approved_risk_pct"] == 0.10
    assert option["vetoes"] == []
    assert (
        option["score_components"]["selector_reduce_risk_new_entry_authority"].get(
            "package_authority_without_cap_release"
        )
        is True
    )
    package_authority = option["score_components"][
        "selector_reduce_risk_package_fill_floor_authority"
    ]
    assert package_authority["applies"] is True
    assert package_authority["allowed"] is True
    assert package_authority["package_open_reduced_authority_applies"] is True
    assert package_authority["package_open_reduced_authority_allowed"] is True
