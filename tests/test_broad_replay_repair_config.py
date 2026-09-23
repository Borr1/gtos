from __future__ import annotations

import copy
import gc
import importlib.util
import json
import sys
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from src.components.poi_execution_lifecycle import (
    build_causal_poi_lifecycle_envelope,
)
from src.components.poi_state_contract import finalize_poi_state
from src.research import moonshot_scheduler_v4_best_trade_allocator as scheduler
from src.research.moonshot_scheduler_v4_best_trade_allocator import (
    stamp_package_new_entry_authority,
)
from src.research.reduced_risk_action_reason_contract import (
    OPEN_REDUCED_SELECTOR_REASONS,
    REDUCED_RISK_SIGNED_NEW_ENTRY_ACTION_INTENTS,
    SCHEDULER_ACTION_INTENT_ALIASES,
    SELECTOR_OPEN_REDUCED_RISK_ALLOWED_ACTION_INTENTS,
    SELECTOR_REDUCE_RISK_ALLOWED_ACTION_INTENTS,
    normalize_selector_action_for_reason,
)
from src.research.source_required_lifecycle_authority import (
    source_required_replay_override_applied,
    source_required_replay_override_kind,
)
from src.research_infra import v4_timewarp_simulated_live_research_loop as timewarp


ROOT = Path(__file__).resolve().parents[1]
HARNESS_PATH = (
    ROOT
    / "src/research_infra/replay_acceleration_attempt5_typed_sparse_runner.py"
)
BRIDGE_PATH = (
    ROOT
    / "research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20"
    / "run_selected_package_replay_bridge.py"
)
FLOW_ANALYZER_PATH = (
    ROOT
    / "research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20"
    / "analyze_broad_live_as_if_replay_flow.py"
)
COMPARATOR_PATH = (
    ROOT
    / "research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20"
    / "compare_broad_live_as_if_replay_runs.py"
)
COMPACT_POI_REPAIR_PATH = (
    ROOT
    / "research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20"
    / "repair_compact_candidate_index_poi_state.py"
)


def load_broad_replay_harness():
    spec = importlib.util.spec_from_file_location(
        "replay_acceleration_attempt5_typed_sparse_runner_test", HARNESS_PATH
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_broad_replay_comparator():
    spec = importlib.util.spec_from_file_location(
        "compare_broad_live_as_if_replay_runs", COMPARATOR_PATH
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_compact_poi_repair():
    spec = importlib.util.spec_from_file_location(
        "repair_compact_candidate_index_poi_state", COMPACT_POI_REPAIR_PATH
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _valid_compact_poi_atom(
    *,
    poi_id: str = "poi-compact-proof",
    decision_time: str = "2026-05-14T01:15:00+00:00",
) -> tuple[dict, dict]:
    state = finalize_poi_state(
        {
            "poi_id": poi_id,
            "poi_type": "fair_value_gap",
            "poi_timeframe": "M15",
            "poi_direction": "bullish",
            "poi_zone_low": 100.0,
            "poi_zone_high": 101.0,
            "poi_source_candle_times": [
                "2026-05-14T00:15:00+00:00",
                "2026-05-14T00:30:00+00:00",
                "2026-05-14T00:45:00+00:00",
            ],
            "poi_created_at_utc": "2026-05-14T01:00:00+00:00",
            "poi_state_asof_utc": decision_time,
            "poi_age_hours": 0.25,
            "poi_touch_count": 0,
            "poi_first_touch_time_utc": "",
            "poi_last_touch_time_utc": "",
            "poi_mitigation_status": "untouched",
            "poi_filled": False,
            "poi_invalidated": False,
            "poi_invalidation_time_utc": "",
            "poi_invalidation_reason": "",
        }
    )
    lifecycle = build_causal_poi_lifecycle_envelope(
        poi_state=state,
        decision_time_utc=decision_time,
        fillability={
            "fill_probability": 0.60,
            "current_price": 102.0,
            "entry_price": 100.5,
            "stop_loss": 99.0,
            "atr14": 1.0,
            "distance_to_limit_price": 1.5,
            "distance_to_limit_atr": 1.5,
            "distance_to_limit_risk": 1.0,
            "limit_marketable_at_decision": False,
            "current_price_source_time_utc": "2026-05-14T01:00:00+00:00",
            "current_price_source_boundary": (
                "closed_m15_predecision_asof_no_postdecision_path"
            ),
        },
        distance_to_zone_price=1.0,
        distance_to_zone_atr=1.0,
        distance_to_midpoint_price=1.5,
        distance_to_midpoint_atr=1.5,
        scheduler_readiness_floor=0.35,
        scheduler_readiness_policy_source="unit_test",
        scheduler_readiness_policy_hash_sha256="b" * 64,
    )
    assert state["poi_state_contract_status"] == "valid_predecision_poi_state"
    assert lifecycle["contract_status"] == "valid_predecision_poi_lifecycle"
    return state, lifecycle


def _current_summary_complete_authority_row(
    *,
    candidate_id: str = "current-summary-authority",
    decision_time: str = "2026-05-13T08:00:00+00:00",
) -> dict:
    instance_key = f"{candidate_id}@@{decision_time}"
    member_axis_id = "member_axis:current-summary-authority"
    payload = {
        "payload_schema": scheduler.PACKAGE_NEW_ENTRY_AUTHORITY_PAYLOAD_SCHEMA,
        "payload_contract": (
            scheduler.PACKAGE_NEW_ENTRY_AUTHORITY_IMMUTABLE_PAYLOAD_CONTRACT
        ),
        "scope": "selector_reduced_risk_to_scheduler_new_position",
        "target_action_intent": "new_position",
        "uses_outcome_fields": False,
        "candidate_id": candidate_id,
        "candidate_id_source": "candidate_id",
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": instance_key,
        "source_bound_replay_candidate_instance_key": instance_key,
        "candidate_instance_identity_status": "materialized",
        "matched_member_axis_ids": [member_axis_id],
        "selector_action": "open-reduced-risk",
        "selector_reason": "current_summary_unit_test",
        "authority_applies": True,
        "authority_allowed": True,
        "authority_family": "current_summary_unit_test",
        "authority_source": "current_summary_unit_test_predecision_authority",
        "source_boundary": (
            "predecision_current_summary_unit_test_no_outcome_fields"
        ),
        "source_bound_package_candidate_use_allowed": True,
        "source_completeness_status": "complete",
        "expected_net_r": 0.75,
        "expected_net_r_semantics": (
            scheduler.LEGACY_UNTYPED_EXPECTED_VALUE
        ),
        "expected_net_r_semantics_source": (
            scheduler.LEGACY_UNTYPED_EXPECTED_VALUE_SOURCE
        ),
        "probability": 0.70,
        "fill_probability": 0.80,
        "source_completeness": 1.0,
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "unit_test.predecision.expected_net_r",
            "probability": "unit_test.predecision.probability",
            "fill_probability": "unit_test.predecision.fill_probability",
            "source_completeness": "unit_test.predecision.source_completeness",
        },
        "candidate_decision_quality_source_boundary": (
            "predecision_current_summary_quality_no_outcome_fields"
        ),
        "candidate_decision_quality_alias_status": "exact_materialized",
        "candidate_decision_quality_alias_mismatches": [],
        "candidate_decision_quality_provenance_failures": [],
        "pretrade_cost_packet_status": "PASSED",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "cost_authority": "broker_calibrated_replay_cost",
        "candidate_cost_r_fallback_is_authority": False,
        "execution_fill_probability": 0.80,
        "execution_fill_probability_source": "predecision_limit_fillability",
        "execution_fill_probability_source_time_utc": (
            "2026-05-13T07:45:00+00:00"
        ),
        "execution_fill_probability_source_boundary": (
            "asof_candidate_fields_only_no_postdecision_path"
        ),
        "execution_fill_probability_authority_class": (
            scheduler.PACKAGE_NEW_ENTRY_AUTHORITY_EXECUTION_FILLABILITY_CLASS
        ),
        "entry_quality_fill_probability": 0.80,
        "limit_fillability_probability": 0.80,
        "predecision_limit_fillability_probability": 0.80,
        "selected_policy_for_expected_net_r": "not_required_no_selected_policy",
        "selected_policy_expected_net_calibration_status": (
            "not_required_no_selected_policy"
        ),
        "selected_policy_expected_net_calibrated": False,
        "selected_policy_expected_net_calibration_required": False,
        "selected_policy_expected_net_calibration_source": "",
        "selected_policy_expected_net_calibration_source_boundary": "",
        "selected_policy_expected_net_calibration_hash": "",
        "package_replay_order_executable_candidate_use_allowed": True,
        "package_replay_order_executable_candidate_use_allowed_reason": (
            "current_summary_unit_test_signed_authority"
        ),
        "package_replay_order_executable_authority_source": (
            "current_summary_unit_test_predecision_authority"
        ),
    }
    digest = scheduler.package_new_entry_authority_payload_hash_sha256(payload)
    authority_field = "ultimate_candidate_package_open_reduced_risk_authority"
    authority = {
        "package_new_entry_authority_required": True,
        "package_new_entry_authority_valid": True,
        "package_new_entry_authority_status": (
            scheduler.PACKAGE_NEW_ENTRY_AUTHORITY_VALID_STATUS
        ),
        "package_new_entry_authority_failures": [],
        "package_new_entry_authority_hash_sha256": digest,
        "expected_package_new_entry_authority_hash_sha256": digest,
        "package_new_entry_authority_payload": payload,
        "package_new_entry_authority_authority_field": authority_field,
    }
    for payload_field, value in payload.items():
        projection_field = (
            "package_new_entry_authority_payload_schema"
            if payload_field == "payload_schema"
            else "package_new_entry_authority_payload_contract"
            if payload_field == "payload_contract"
            else f"package_new_entry_authority_{payload_field}"
        )
        authority[projection_field] = copy.deepcopy(value)
    authority["package_new_entry_authority_candidate_decision_quality"] = {
        field: copy.deepcopy(payload[field])
        for field in (
            "expected_net_r",
            "probability",
            "fill_probability",
            "source_completeness",
            "candidate_decision_quality_field_sources",
            "candidate_decision_quality_source_boundary",
            "candidate_decision_quality_alias_status",
            "candidate_decision_quality_alias_mismatches",
            "candidate_decision_quality_provenance_failures",
        )
    }
    return {
        "candidate_id": candidate_id,
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": instance_key,
        "source_bound_replay_candidate_instance_key": instance_key,
        "candidate_instance_identity_status": "materialized",
        "ultimate_package_matched_member_axis_ids": [member_axis_id],
        "selected_package_matched_member_axis_ids": [member_axis_id],
        "selector_action": "open-reduced-risk",
        "selector_reason": "current_summary_unit_test",
        "scheduler_materialization_selector_action": "open-reduced-risk",
        "scheduler_materialization_action_intent": "new_position",
        "package_replay_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed": True,
        "package_replay_order_executable_candidate_use_allowed": True,
        "approved_risk_pct": 0.25,
        **authority,
    }


def _current_summary_terminal_zero_trade_with_namespaced_authorities(
    *authorities: tuple[str, dict],
) -> dict:
    row = _current_summary_diagnostic_candidate_row()
    row.update(
        {
            "selected_action_class": "zero_trade",
            "effective_action_intent": "new_position",
            "effective_risk_decision": "reject",
            "executable_finalized": False,
            "risk_finalizer_executable_finalized": False,
            "package_replay_order_executable_transfer_status": "final_blocked",
            "approved_risk_pct": None,
            "scheduler_approved_risk_pct": None,
            "selected_scheduler_approved_risk_pct": None,
            "risk_decision_approved_risk_pct": None,
            "package_new_entry_authority_required": None,
            "package_new_entry_authority_valid": None,
            "package_new_entry_authority_status": None,
            "package_new_entry_authority_payload": None,
            "package_new_entry_authority_hash_sha256": None,
            "expected_package_new_entry_authority_hash_sha256": None,
        }
    )
    for prefix, authority in authorities:
        for field, value in authority.items():
            if field.startswith("package_new_entry_authority_") or field == (
                "expected_package_new_entry_authority_hash_sha256"
            ):
                row[f"{prefix}{field}"] = copy.deepcopy(value)
    return row


CURRENT_SUMMARY_EXECUTABLE_AUTHORITY_ALIASES = (
    "ledger_namespace_synthesized_executable_candidate_use_allowed",
    "package_replay_candidate_use_allowed",
    "package_replay_executable_candidate_use_allowed",
    "package_replay_order_executable_candidate_use_allowed",
    "replay_candidate_use_allowed_now",
    "ultimate_package_effective_executable_authority_allowed",
    "executable_finalized",
    "missed_row_executable_finalized",
)


def _current_summary_diagnostic_candidate_row(
    *,
    legacy_hash_only: bool = False,
) -> dict:
    row = {
        "candidate_id": "current-summary-diagnostic-candidate",
        "decision_time_utc": "2026-05-13T08:00:00+00:00",
        "selector_action": "open-reduced-risk",
        "scheduler_materialization_action_intent": "new_position",
        "package_replay_executable_candidate_use_allowed_reason": (
            "candidate_ledger_diagnostic_only"
        ),
        "package_replay_order_executable_candidate_use_allowed_reason": (
            "candidate_ledger_diagnostic_only"
        ),
        "replay_candidate_use_allowed_now_reason": (
            "candidate_ledger_diagnostic_only"
        ),
        "approved_risk_pct": 0.25,
        "scheduler_approved_risk_pct": 0.25,
        "selected_scheduler_approved_risk_pct": 0.25,
        "risk_decision_approved_risk_pct": 0.25,
        **{
            alias: False
            for alias in CURRENT_SUMMARY_EXECUTABLE_AUTHORITY_ALIASES
        },
    }
    if legacy_hash_only:
        legacy_digest = "a" * 64
        row.update(
            {
                "package_new_entry_authority_required": False,
                "package_new_entry_authority_valid": False,
                "package_new_entry_authority_status": (
                    "legacy_hash_only_authority_diagnostic_only"
                ),
                "package_new_entry_authority_failures": [],
                "package_new_entry_authority_hash_sha256": legacy_digest,
                "expected_package_new_entry_authority_hash_sha256": legacy_digest,
            }
        )
    return row


def test_missed_cost_passed_scope_splits_hold_and_reduced_package_roles() -> None:
    harness = load_broad_replay_harness()
    row = {
        "missed_cost_executable_opportunity_scoreable": True,
        "missed_opportunity_execution_bound_cost_passed": True,
        "executable_finalized": True,
        "package_replay_executable_candidate_use_allowed": True,
        "package_replay_order_executable_candidate_use_allowed": True,
        "replay_candidate_use_allowed_now": True,
        "order_status": "expired_unfilled",
        "ultimate_package_role_disposition": "avoid_feature_only_veto",
    }

    assert harness.missed_opportunity_execution_bound_cost_passed_scope(row) is False

    reduced_role = {
        **row,
        "ultimate_package_role_disposition": "admission_with_avoid_feature_risk_control",
    }
    assert (
        harness.missed_opportunity_execution_bound_cost_passed_scope(reduced_role)
        is True
    )

    executable_role = {**row, "ultimate_package_role_disposition": "admission_candidate"}
    assert (
        harness.missed_opportunity_execution_bound_cost_passed_scope(executable_role)
        is True
    )

    explicit_block = {**executable_role, "role_disposition_executable": False}
    assert (
        harness.missed_opportunity_execution_bound_cost_passed_scope(explicit_block)
        is False
    )


def load_selected_package_replay_bridge():
    spec = importlib.util.spec_from_file_location(
        "run_selected_package_replay_bridge", BRIDGE_PATH
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_selected_bridge_fast_path_caches_validate_source_identity() -> None:
    bridge = load_selected_package_replay_bridge()
    original_symbol_config = bridge.timewarp_loop.replay_symbol_config
    original_get_candles = bridge.timewarp_loop.HistoricalMT5Adapter.get_candles

    def closure_values(function):
        return {
            name: cell.cell_contents
            for name, cell in zip(
                function.__code__.co_freevars,
                function.__closure__ or (),
            )
        }

    try:
        bridge.install_source_bound_csv_replay_fast_paths(
            disable_m15_tick_repair=False,
            suppress_pipeline_writes=False,
            cache_symbol_config=True,
            cache_candle_index=True,
        )

        cached_symbol_config = bridge.timewarp_loop.replay_symbol_config
        symbol_config_cache = closure_values(cached_symbol_config)[
            "symbol_config_cache"
        ]
        stale_config = {"source_marker": "stale"}
        current_config = {"source_marker": "current"}
        stale_output = cached_symbol_config(stale_config, "XAUUSD")
        symbol_config_cache[(id(current_config), "XAUUSD")] = (
            stale_config,
            stale_output,
        )

        current_output = cached_symbol_config(current_config, "XAUUSD")

        assert current_output["source_marker"] == "current"
        assert symbol_config_cache[(id(current_config), "XAUUSD")][0] is current_config

        fast_get_candles = bridge.timewarp_loop.HistoricalMT5Adapter.get_candles
        indexed_rows = closure_values(fast_get_candles)["_indexed_rows"]
        candle_index_cache = closure_values(indexed_rows)["candle_index_cache"]
        stale_rows = (
            {
                "time_utc": "2026-06-01T00:00:00+00:00",
                "source_marker": "stale",
            },
        )
        current_rows = (
            {
                "time_utc": "2026-06-02T00:00:00+00:00",
                "source_marker": "current",
            },
        )
        stale_time = bridge.timewarp_loop.parse_utc(
            "2026-06-01T00:00:00+00:00"
        )
        asof = bridge.timewarp_loop.parse_utc("2026-06-02T00:30:00+00:00")
        assert stale_time is not None
        assert asof is not None
        candle_index_cache[(id(current_rows), "M15")] = (
            stale_rows,
            stale_rows,
            (stale_time,),
        )

        selected = indexed_rows(
            current_rows,
            timeframe="M15",
            asof=asof,
            limit=10,
        )

        assert [row["source_marker"] for row in selected] == ["current"]
        assert candle_index_cache[(id(current_rows), "M15")][0] is current_rows
    finally:
        bridge.timewarp_loop.replay_symbol_config = original_symbol_config
        bridge.timewarp_loop.HistoricalMT5Adapter.get_candles = original_get_candles


def test_selected_bridge_execution_fillability_prefers_signed_payload_projection() -> None:
    bridge = load_selected_package_replay_bridge()
    row = _current_summary_complete_authority_row()
    row.update(
        {
            "execution_fill_probability": 0.12,
            "execution_fill_probability_source": "stale.mutable.direct_alias",
            "predecision_limit_fillability_probability": 0.12,
            "limit_fillability_probability": 0.12,
        }
    )

    assert bridge.execution_fillability_authority(row) == (
        0.80,
        "predecision_limit_fillability",
    )


def test_selected_bridge_execution_fillability_consumer_rejects_invalid_signed_payload_before_stale_alias() -> None:
    bridge = load_selected_package_replay_bridge()
    row = _current_summary_complete_authority_row()
    tampered_payload = copy.deepcopy(row["package_new_entry_authority_payload"])
    tampered_payload["execution_fill_probability"] = 0.44
    row["package_new_entry_authority_payload"] = tampered_payload
    row.update(
        {
            "execution_fill_probability": 0.93,
            "execution_fill_probability_source": (
                "fixture.current.predecision_limit_fillability_probability"
            ),
            "predecision_limit_fillability_probability": 0.93,
            "limit_fillability_probability": 0.93,
        }
    )

    assert bridge.trusted_signed_package_new_entry_authority_surface(row) is False
    assert bridge.execution_fillability_authority(row) == (
        None,
        timewarp.INVALID_SIGNED_EXECUTION_FILLABILITY_SOURCE,
    )


def test_selected_bridge_execution_payload_prefers_explicit_valid_nested_authority() -> None:
    bridge = load_selected_package_replay_bridge()
    candidate_id = "bridge-explicit-nested-authority"
    decision_time = "2026-05-13T08:15:00+00:00"
    base = {
        "candidate_id": candidate_id,
        "candidate_id_source": "candidate_id",
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "source_bound_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "candidate_instance_identity_status": "materialized",
        "ultimate_package_matched_member_axis_ids": [
            "member_axis:bridge-explicit-nested-authority"
        ],
        "selected_package_matched_member_axis_ids": [
            "member_axis:bridge-explicit-nested-authority"
        ],
        "selector_action": "open-reduced-risk",
        "selector_reason": "bridge_explicit_nested_authority",
        "scheduler_materialization_action_intent": "new_position",
        "source_bound_package_candidate_use_allowed": True,
        "package_replay_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed": True,
        "package_replay_order_executable_candidate_use_allowed": True,
        "expected_net_r": 0.80,
        "probability": 0.75,
        "confidence": 0.75,
        "fill_probability": 0.96,
        "source_completeness": 1.0,
    }
    stale = _complete_test_authority_surface(
        copy.deepcopy(base),
        selector_action="open-reduced-risk",
        selector_reason=base["selector_reason"],
        action_intent="new_position",
        authority={
            "authority_family": "bridge_explicit_nested_authority",
            "authority_source": "stale_root_predecision_authority",
        },
    )
    selected_base = copy.deepcopy(base)
    selected_base["fill_probability"] = 0.88
    selected_base["candidate_fill_probability"] = 0.88
    selected_base["execution_fill_probability"] = 0.88
    selected_base["limit_fillability_probability"] = 0.88
    selected_base["predecision_limit_fillability_probability"] = 0.88
    selected = _complete_test_authority_surface(
        selected_base,
        selector_action="open-reduced-risk",
        selector_reason=base["selector_reason"],
        action_intent="new_position",
        authority={
            "authority_family": "bridge_explicit_nested_authority",
            "authority_source": "selected_nested_predecision_authority",
        },
    )
    authority_field = "ultimate_candidate_package_open_reduced_risk_authority"
    row = {**base, **stale, authority_field: selected}
    row["package_new_entry_authority_authority_field"] = authority_field

    payload = bridge._signed_execution_payload_from_surface(row)

    assert payload["execution_fill_probability"] == 0.88
    assert payload["authority_source"] == (
        "selected_nested_predecision_authority"
    )


def test_selected_bridge_does_not_stamp_equal_decision_time_as_predecision_source() -> None:
    bridge = load_selected_package_replay_bridge()
    decision_time = "2026-05-13T08:15:00+00:00"
    row = {
        "decision_time_utc": decision_time,
        "candle_close_utc": decision_time,
        "predecision_limit_fillability": {
            "available": True,
            "fill_probability": 0.80,
            "current_price": 1.25,
            "source_boundary": (
                "closed_m15_predecision_asof_no_postdecision_path"
            ),
        },
    }

    bridge.normalize_bridge_predecision_fillability_source_time(row)

    assert row["predecision_limit_fillability_source_time_status"] == (
        "source_time_not_before_decision_non_executable"
    )
    assert row["diagnostic_unsafe_predecision_fillability_source_time_utc"] == (
        decision_time
    )
    assert "predecision_current_price_source_time_utc" not in row


def test_selected_bridge_fillability_producer_restamps_current_predecision_limit() -> None:
    bridge = load_selected_package_replay_bridge()
    selector_reason = (
        "source_bound_router_refusal_open_reduced_materialized_for_replay"
    )
    candidate_id = "candidate-producer-fillability-restamp"
    decision_time = "2026-05-15T10:15:00+00:00"
    row = {
        "candidate_id": candidate_id,
        "candidate_id_source": "candidate_id",
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": (
            f"{candidate_id}@@{decision_time}"
        ),
        "source_bound_replay_candidate_instance_key": (
            f"{candidate_id}@@{decision_time}"
        ),
        "candidate_instance_identity_status": "materialized",
        "selector_action": "open-reduced-risk",
        "selector_reason": selector_reason,
        "scheduler_materialization_action_intent": "new_position",
        "expected_net_r": 0.91,
        "probability": 0.78,
        "fill_probability": 0.62,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "fixture.predecision.expected_net_r",
            "probability": "fixture.predecision.probability",
            "fill_probability": "fixture.entry_quality.fill_probability",
            "source_completeness": "fixture.predecision.source_completeness",
        },
        "candidate_decision_quality_source_boundary": (
            "predecision_fixture_quality_no_outcome_fields"
        ),
        "candidate_decision_quality_alias_status": "exact_materialized",
        "candidate_decision_quality_alias_mismatches": [],
        "candidate_decision_quality_provenance_failures": [],
        "ultimate_candidate_package_open_reduced_risk_authority": {
            "applies": True,
            "allowed": True,
            "authority_family": "router_refusal_softening",
            "authority_source": "fixture_predecision_authority",
            "selector_reason": selector_reason,
            "source_boundary": (
                "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
            ),
            "source_bound_candidate_use_allowed_now": True,
            "broker_cost_passed_for_package_router": True,
            "positive_predecision_package_edge": True,
        },
    }
    _prepare_complete_test_authority_row(
        row,
        action_intent="new_position",
        matched_member_axis_id="member_axis:producer-fillability-restamp",
    )
    for field in (
        "execution_fill_probability",
        "execution_fill_probability_source",
        "limit_fillability_probability",
    ):
        row.pop(field, None)
    row["predecision_limit_fillability_probability"] = 0.87
    stale_hash = "f" * 64
    row.update(
        {
            "package_new_entry_authority_required": True,
            "package_new_entry_authority_valid": False,
            "package_new_entry_authority_status": (
                "invalid_or_missing_signed_new_entry_authority"
            ),
            "package_new_entry_authority_failures": [
                "stale_fixture_signature_missing_payload"
            ],
            "package_new_entry_authority_hash_sha256": stale_hash,
            "expected_package_new_entry_authority_hash_sha256": stale_hash,
            "package_new_entry_authority_execution_fill_probability": 0.11,
            "package_new_entry_authority_execution_fill_probability_source": (
                "stale.package.predecision_limit_fillability_probability"
            ),
            "package_new_entry_authority_predecision_limit_fillability_probability": (
                0.11
            ),
        }
    )

    assert bridge.execution_fillability_authority(row) == (
        None,
        timewarp.INVALID_SIGNED_EXECUTION_FILLABILITY_SOURCE,
    )
    assert bridge.bridge_predecision_execution_fillability_for_stamp(row) == (
        0.87,
        "predecision_limit_fillability_probability",
    )

    materialized = bridge._bridge_materialize_signed_reduced_authority(
        row,
        selector_action=row["selector_action"],
        selector_reason=row["selector_reason"],
        action_intent="new_position",
    )

    assert materialized["package_new_entry_authority_bridge_materialized"] is True
    assert materialized["package_new_entry_authority_valid"] is True
    assert materialized["package_new_entry_authority_hash_sha256"] != stale_hash
    assert bridge.trusted_signed_package_new_entry_authority_surface(materialized)
    payload = materialized["package_new_entry_authority_payload"]
    assert payload["execution_fill_probability"] == 0.87
    assert payload["execution_fill_probability_source"] == (
        "predecision_limit_fillability_probability"
    )
    assert payload["execution_fill_probability_source_time_utc"] == row[
        "execution_fill_probability_source_time_utc"
    ]
    assert payload["execution_fill_probability_source_boundary"] == row[
        "execution_fill_probability_source_boundary"
    ]


def test_selected_bridge_fillability_producer_ignores_stale_signed_aliases_and_unsourced_generic_fill() -> None:
    bridge = load_selected_package_replay_bridge()
    row = {
        "decision_time_utc": "2026-05-15T10:15:00+00:00",
        "fill_probability": 0.73,
        "execution_fill_probability_source_boundary": (
            "predecision_fixture_execution_fillability_no_outcome_fields"
        ),
        "execution_fill_probability_source_time_utc": (
            "2026-05-15T10:14:00+00:00"
        ),
        "candidate_decision_quality_field_sources": {
            "fill_probability": "fixture.entry_quality.fill_probability"
        },
        "package_new_entry_authority_execution_fill_probability": 0.99,
        "package_new_entry_authority_execution_fill_probability_source": (
            "stale.package.predecision_limit_fillability_probability"
        ),
        "package_new_entry_authority_predecision_limit_fillability_probability": (
            0.98
        ),
        "package_new_entry_authority_limit_fillability_probability": 0.97,
    }

    assert bridge.bridge_predecision_execution_fillability_for_stamp(row) == (
        None,
        bridge.EXECUTION_FILLABILITY_MISSING_SOURCE,
    )

    explicitly_sourced = copy.deepcopy(row)
    explicitly_sourced["candidate_decision_quality_field_sources"] = {
        "fill_probability": (
            "fixture.predecision_limit_fillability.fill_probability"
        )
    }
    assert bridge.bridge_predecision_execution_fillability_for_stamp(
        explicitly_sourced
    ) == (None, bridge.EXECUTION_FILLABILITY_MISSING_SOURCE)

    explicit_limit = copy.deepcopy(explicitly_sourced)
    explicit_limit["predecision_limit_fillability_probability"] = 0.73
    assert bridge.bridge_predecision_execution_fillability_for_stamp(
        explicit_limit
    ) == (0.73, "predecision_limit_fillability_probability")


def test_selected_bridge_ordinary_trade_unsigned_package_fill_alias_is_not_executable() -> None:
    bridge = load_selected_package_replay_bridge()
    row = {
        "selector_action": "trade",
        "scheduler_materialization_action_intent": "new_position",
        "ultimate_package_effective_admission_count": 1,
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "candidate_cost_r_fallback_is_authority": False,
        "expected_net_r": 0.80,
        "probability": 0.75,
        "fill_probability": 0.90,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "package_new_entry_authority_execution_fill_probability": 0.90,
        "package_new_entry_authority_execution_fill_probability_source": (
            "predecision_limit_fillability"
        ),
    }

    assert bridge.execution_fillability_authority(row) == (
        None,
        bridge.EXECUTION_FILLABILITY_MISSING_SOURCE,
    )
    assert bridge.executable_package_use_detail(
        row,
        source_bound_allowed=True,
    ) == (False, bridge.EXECUTION_FILLABILITY_MISSING_SOURCE)


def test_selected_bridge_generic_model_fill_is_not_execution_authority() -> None:
    bridge = load_selected_package_replay_bridge()
    row = {
        "decision_time_utc": "2026-05-15T10:15:00+00:00",
        "fill_probability": 0.94,
        "execution_fill_probability": 0.94,
        "execution_fill_probability_source": (
            "model.predecision_generic_fill_probability"
        ),
        "execution_fill_probability_source_boundary": (
            "predecision_model_quality_no_outcome_fields"
        ),
        "execution_fill_probability_source_time_utc": (
            "2026-05-15T10:14:00+00:00"
        ),
        "candidate_decision_quality_field_sources": {
            "fill_probability": "model.predecision_generic_fill_probability"
        },
    }

    assert bridge.bridge_predecision_execution_fillability_for_stamp(row) == (
        None,
        bridge.EXECUTION_FILLABILITY_MISSING_SOURCE,
    )
    assert bridge.execution_fillability_authority(row) == (
        None,
        bridge.EXECUTION_FILLABILITY_MISSING_SOURCE,
    )


@pytest.mark.parametrize(
    ("nested_override", "row_override"),
    (
        ({"available": False}, {}),
        (
            {
                "source_boundary": (
                    "postdecision_order_fillability_outcome_path"
                )
            },
            {},
        ),
        (
            {"source_time_utc": "2026-05-15T10:15:00+00:00"},
            {},
        ),
    ),
)
def test_selected_bridge_fillability_producer_rejects_unavailable_postdecision_or_same_time_nested(
    nested_override: dict,
    row_override: dict,
) -> None:
    bridge = load_selected_package_replay_bridge()
    nested = {
        "available": True,
        "fill_probability": 0.87,
        "fill_probability_source": (
            "fixture.predecision_limit_fillability.fill_probability"
        ),
        "source_boundary": (
            "predecision_fixture_limit_fillability_no_outcome_fields"
        ),
        "source_time_utc": "2026-05-15T10:14:00+00:00",
        **nested_override,
    }
    row = {
        "decision_time_utc": "2026-05-15T10:15:00+00:00",
        "predecision_limit_fillability": nested,
        **row_override,
    }

    assert bridge.bridge_predecision_execution_fillability_for_stamp(row) == (
        None,
        bridge.EXECUTION_FILLABILITY_MISSING_SOURCE,
    )


def test_selected_bridge_signed_execution_fill_overwrites_stale_flat_and_nested_projection() -> None:
    bridge = load_selected_package_replay_bridge()
    row = _current_summary_complete_authority_row()
    row.update(
        {
            "execution_fill_probability": 0.12,
            "execution_fill_probability_source": "stale.mutable.direct_alias",
            "predecision_limit_fillability_probability": 0.12,
            "limit_fillability_probability": 0.12,
            "predecision_limit_fillability": {
                "available": True,
                "fill_probability": 0.12,
                "fill_probability_source": "stale.mutable.nested_alias",
            },
        }
    )

    hydrated = bridge.hydrate_candidate_quality_aliases(row)

    assert hydrated["execution_fill_probability"] == 0.80
    assert hydrated["predecision_limit_fillability_probability"] == 0.80
    assert hydrated["limit_fillability_probability"] == 0.80
    assert hydrated["execution_fill_probability_source"] == (
        "predecision_limit_fillability"
    )
    assert hydrated["execution_fill_probability_authority_class"] == (
        bridge.PACKAGE_NEW_ENTRY_AUTHORITY_EXECUTION_FILLABILITY_CLASS
    )
    nested = hydrated["predecision_limit_fillability"]
    assert nested["fill_probability"] == 0.80
    assert nested["limit_fillability_probability"] == 0.80
    assert nested["fill_probability_source"] == "predecision_limit_fillability"
    assert nested["source"] == "predecision_limit_fillability"
    assert nested["authority_class"] == (
        bridge.PACKAGE_NEW_ENTRY_AUTHORITY_EXECUTION_FILLABILITY_CLASS
    )


def test_selected_bridge_lightweight_trust_cannot_bypass_full_validation() -> None:
    bridge = load_selected_package_replay_bridge()
    row = _signed_bridge_router_refusal_row(
        "source_bound_router_refusal_open_reduced_materialized_for_replay",
        matched_member_axis_id="member_axis:full-validation-mismatch",
    )
    row.update(
        {
            "entry_price": 2400.0,
            "stop_loss": 2390.0,
            "take_profit_1": 2420.0,
        }
    )
    nested_authority = dict(
        row["ultimate_candidate_package_open_reduced_risk_authority"]
    )
    nested_authority["current_config_allowed"] = False
    row["ultimate_candidate_package_open_reduced_risk_authority"] = nested_authority

    assert bridge.trusted_signed_package_new_entry_authority_surface(row) is True
    validation = bridge.bridge_reduced_package_new_entry_authority_validation(
        row,
        selector_action=row["selector_action"],
        selector_reason=row["selector_reason"],
        action_intent="new_position",
    )
    assert validation["valid"] is False
    assert "authority_current_config_blocked" in validation["failures"]
    block_reason = bridge.signed_reduced_package_bridge_authority_block_reason(
        row,
        selector_action=row["selector_action"],
        selector_reason=row["selector_reason"],
        action_intent="new_position",
    )
    assert block_reason is not None
    assert "authority_current_config_blocked" in block_reason
    authority_fields = bridge.package_authority_bridge_fields(
        row,
        source_bound_allowed=True,
    )
    assert authority_fields[
        "package_replay_order_executable_candidate_use_allowed"
    ] is False
    assert authority_fields["package_new_entry_authority_valid"] is False


def test_selected_bridge_preserves_entry_and_execution_fill_values_and_provenance() -> None:
    bridge = load_selected_package_replay_bridge()
    candidate_id = "candidate-entry-execution-fill-split"
    decision_time = "2026-05-15T10:15:00+00:00"
    row = {
        "candidate_id": candidate_id,
        "candidate_id_source": "candidate_id",
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": (
            f"{candidate_id}@@{decision_time}"
        ),
        "source_bound_replay_candidate_instance_key": (
            f"{candidate_id}@@{decision_time}"
        ),
        "candidate_instance_identity_status": "materialized",
        "selector_action": "open-reduced-risk",
        "selector_reason": "off_session_softening",
        "scheduler_materialization_action_intent": "new_position",
        "expected_net_r": 0.91,
        "probability": 0.78,
        "fill_probability": 0.42,
        "candidate_fill_probability": 0.42,
        "execution_fill_probability": 0.87,
        "execution_fill_probability_source": (
            "fixture.predecision_limit_fillability.fill_probability"
        ),
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "fixture.predecision.expected_net_r",
            "probability": "fixture.predecision.probability",
            "fill_probability": "fixture.entry_model.fill_probability",
            "source_completeness": "fixture.predecision.source_completeness",
        },
        "candidate_decision_quality_source_boundary": (
            "predecision_fixture_quality_no_outcome_fields"
        ),
        "candidate_decision_quality_alias_status": "exact_materialized",
        "candidate_decision_quality_alias_mismatches": [],
        "candidate_decision_quality_provenance_failures": [],
        "entry_price": 193.10,
        "stop_loss": 192.70,
        "take_profit_1": 193.90,
        "ultimate_candidate_package_open_reduced_risk_authority": {
            "applies": True,
            "allowed": True,
            "authority_family": "off_session_softening",
            "authority_source": "fixture_predecision_authority",
            "source_boundary": (
                "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
            ),
        },
    }
    signed = _complete_test_authority_surface(
        row,
        selector_action=row["selector_action"],
        selector_reason=row["selector_reason"],
        action_intent="new_position",
        authority=row["ultimate_candidate_package_open_reduced_risk_authority"],
        matched_member_axis_id="member_axis:entry-execution-fill-split",
    )
    row.update(signed)
    row["ultimate_candidate_package_open_reduced_risk_authority"] = dict(signed)

    fields = bridge.selected_package_bridge_quality_fields(
        row,
        matched_stable_member_axis_ids=["member_axis:entry-execution-fill-split"],
    )

    assert fields["fill_probability"] == 0.42
    assert fields["candidate_fill_probability"] == 0.42
    assert fields["entry_quality_fill_probability"] == 0.42
    assert fields["execution_fill_probability"] == 0.87
    assert fields["limit_fillability_probability"] == 0.87
    assert fields["predecision_limit_fillability_probability"] == 0.87
    sources = fields["candidate_decision_quality_field_sources"]
    assert sources["fill_probability"] == "fixture.entry_model.fill_probability"
    assert sources["execution_fill_probability"] == (
        "fixture.predecision_limit_fillability.fill_probability"
    )
    quality = fields["candidate_decision_quality"]
    assert quality["fill_probability"] == 0.42
    assert quality["entry_quality_fill_probability"] == 0.42
    assert quality["execution_fill_probability"] == 0.87


def load_broad_replay_flow_analyzer():
    spec = importlib.util.spec_from_file_location(
        "analyze_broad_live_as_if_replay_flow", FLOW_ANALYZER_PATH
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


SOURCE_BOUND_TEST_MATERIALIZATION_FLOORS = {
    "expected_net_r": 0.55,
    "probability": 0.70,
    "fill_probability": 0.55,
    "source_completeness": 0.95,
}


def _prepare_complete_test_authority_row(
    row: dict,
    *,
    action_intent: str,
    matched_member_axis_id: str | None = None,
) -> None:
    """Populate every immutable atom required by the production signer."""

    candidate_id = str(row.get("candidate_id") or "").strip()
    decision_time = str(row.get("decision_time_utc") or "").strip()
    assert candidate_id and decision_time
    parsed_decision_time = timewarp.parse_utc(decision_time)
    assert parsed_decision_time is not None
    execution_fill_source_time = (
        parsed_decision_time - timedelta(minutes=1)
    ).isoformat()
    instance_key = f"{candidate_id}@@{decision_time}"
    row.setdefault("candidate_id_source", "candidate_id")
    row.setdefault("canonical_replay_candidate_instance_key", instance_key)
    row.setdefault("source_bound_replay_candidate_instance_key", instance_key)
    row.setdefault("candidate_instance_identity_status", "materialized")

    if matched_member_axis_id is None:
        existing_axis_ids = row.get("ultimate_package_matched_member_axis_ids")
        if isinstance(existing_axis_ids, (list, tuple)) and existing_axis_ids:
            matched_member_axis_id = str(existing_axis_ids[0])
        else:
            safe_candidate_id = "".join(
                character
                if character.isalnum() or character in {"-", "_", ".", ":"}
                else "_"
                for character in candidate_id
            )
            matched_member_axis_id = (
                f"member_axis:test:{safe_candidate_id}:{action_intent}"
            )
    row["ultimate_package_matched_member_axis_ids"] = [matched_member_axis_id]
    row.setdefault("ultimate_package_matched_member_axis_count", 1)
    row.setdefault("ultimate_package_admission_member_axis_match_count", 1)
    row.setdefault("source_bound_package_candidate_use_allowed", True)
    row.setdefault("ultimate_package_source_bound_candidate_use_allowed", True)
    row.setdefault("package_replay_source_bound_candidate_use_allowed", True)
    row.setdefault(
        "source_bound_router_refusal_materialization_floors",
        dict(SOURCE_BOUND_TEST_MATERIALIZATION_FLOORS),
    )

    row.setdefault("expected_net_r", 0.91)
    row.setdefault("probability", 0.78)
    row.setdefault("fill_probability", 0.82)
    row.setdefault("source_completeness", 1.0)
    row.setdefault("source_completeness_status", "source_completeness_present")
    execution_fill_probability = next(
        (
            row.get(field)
            for field in (
                "execution_fill_probability",
                "predecision_limit_fillability_probability",
                "limit_fillability_probability",
                "fill_probability",
            )
            if row.get(field) not in (None, "")
        ),
        0.82,
    )
    execution_fill_source = str(
        row.get("execution_fill_probability_source")
        or "unit_test.predecision_limit_fillability_probability"
    )
    row.setdefault("execution_fill_probability", execution_fill_probability)
    row.setdefault(
        "predecision_limit_fillability_probability",
        execution_fill_probability,
    )
    row.setdefault("limit_fillability_probability", execution_fill_probability)
    row.setdefault("execution_fill_probability_source", execution_fill_source)
    row.setdefault(
        "execution_fill_probability_source_boundary",
        "predecision_unit_test_execution_fillability_no_outcome_fields",
    )
    row.setdefault(
        "execution_fill_probability_source_time_utc",
        execution_fill_source_time,
    )
    row.setdefault(
        "predecision_limit_fillability_source_boundary",
        "predecision_unit_test_execution_fillability_no_outcome_fields",
    )
    row.setdefault(
        "predecision_limit_fillability_source_time_utc",
        execution_fill_source_time,
    )

    field_sources = row.get("candidate_decision_quality_field_sources")
    field_sources = dict(field_sources) if isinstance(field_sources, dict) else {}
    field_sources.setdefault(
        "expected_net_r", "unit_test.predecision.expected_net_r"
    )
    field_sources.setdefault("probability", "unit_test.predecision.probability")
    field_sources.setdefault("fill_probability", execution_fill_source)
    field_sources.setdefault("execution_fill_probability", execution_fill_source)
    field_sources.setdefault("limit_fillability_probability", execution_fill_source)
    field_sources.setdefault(
        "predecision_limit_fillability_probability",
        execution_fill_source,
    )
    field_sources.setdefault(
        "source_completeness", "unit_test.predecision.source_completeness"
    )
    row["candidate_decision_quality_field_sources"] = field_sources
    row.setdefault(
        "candidate_decision_quality_source_boundary",
        "predecision_unit_test_quality_no_outcome_fields",
    )
    row.setdefault("candidate_decision_quality_alias_status", "exact_materialized")
    row.setdefault("candidate_decision_quality_alias_mismatches", [])
    row.setdefault("candidate_decision_quality_provenance_failures", [])

    row.setdefault("pretrade_cost_packet_status", "PASSED")
    row.setdefault("cost_authority", "broker_calibrated_replay_cost")
    row.setdefault("cost_source_gap_status", "source_bound_cost_authority_present")
    row.setdefault("candidate_cost_r_fallback_is_authority", False)
    row.setdefault("package_replay_order_executable_candidate_use_allowed", True)
    row.setdefault(
        "package_replay_order_executable_candidate_use_allowed_reason",
        "broker_cost_selector_and_scheduler_action_executable",
    )
    row.setdefault(
        "package_replay_order_executable_authority_source",
        "selected_package_bridge_package_authority_bridge_fields",
    )


def _complete_test_authority_surface(
    row: dict,
    *,
    selector_action: str,
    selector_reason: str,
    action_intent: str,
    authority: dict,
    matched_member_axis_id: str | None = None,
) -> dict:
    """Return a genuinely valid scheduler signature for a complete test row."""

    _prepare_complete_test_authority_row(
        row,
        action_intent=action_intent,
        matched_member_axis_id=matched_member_axis_id,
    )
    signable_authority = dict(authority)
    signable_authority.setdefault("applies", True)
    signable_authority.setdefault("allowed", True)
    signable_authority.setdefault("authority_source", "unit_test_predecision_authority")
    signable_authority.setdefault(
        "source_boundary",
        "predecision_unit_test_authority_no_outcome_fields",
    )
    surface = stamp_package_new_entry_authority(
        row,
        selector_action=selector_action,
        selector_reason=selector_reason,
        action_intent=action_intent,
        authority=signable_authority,
    )
    assert surface["package_new_entry_authority_valid"] is True, surface[
        "package_new_entry_authority_failures"
    ]
    return surface


def _resign_test_authority(
    row: dict,
    *,
    expect_valid: bool,
) -> dict:
    """Re-sign current inputs without allowing an older payload to win precedence."""

    selector_action = str(row["selector_action"])
    selector_reason = str(row["selector_reason"])
    action_intent = str(row["scheduler_materialization_action_intent"])
    authority_field = (
        "ultimate_candidate_package_open_reduced_risk_authority"
        if selector_action == "open-reduced-risk"
        else "ultimate_candidate_package_reduce_risk_authority"
    )
    current_authority = row.get(authority_field)
    current_authority = (
        current_authority if isinstance(current_authority, dict) else {}
    )
    unsigned_authority = {
        key: copy.deepcopy(value)
        for key, value in current_authority.items()
        if not key.startswith("package_new_entry_authority_")
        and key != "expected_package_new_entry_authority_hash_sha256"
        and key not in (
            scheduler.PACKAGE_NEW_ENTRY_AUTHORITY_ORDER_EXECUTABLE_TRIPLET
        )
    }
    for key in tuple(row):
        if key.startswith("package_new_entry_authority_") or key == (
            "expected_package_new_entry_authority_hash_sha256"
        ):
            row.pop(key)
    row[authority_field] = unsigned_authority
    signed_authority = stamp_package_new_entry_authority(
        row,
        selector_action=selector_action,
        selector_reason=selector_reason,
        action_intent=action_intent,
        authority=unsigned_authority,
    )
    row.update(signed_authority)
    row[authority_field] = dict(signed_authority)
    assert signed_authority["package_new_entry_authority_valid"] is expect_valid
    return signed_authority


def _signed_bridge_router_refusal_row(
    selector_reason: str,
    *,
    authority_family: str = "router_refusal_softening",
    matched_member_axis_id: str | None = None,
) -> dict:
    candidate_id = f"candidate-{selector_reason}"
    decision_time = "2026-05-15T10:15:00+00:00"
    row = {
        "candidate_id": candidate_id,
        "candidate_id_source": "candidate_id",
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "source_bound_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "candidate_instance_identity_status": "materialized",
        "selector_action": "open-reduced-risk",
        "selector_reason": selector_reason,
        "scheduler_materialization_action_intent": "new_position",
        "expected_net_r": 0.91,
        "candidate_expected_net_r": 0.91,
        "probability": 0.78,
        "candidate_probability": 0.78,
        "fill_probability": 0.82,
        "candidate_fill_probability": 0.82,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "unit_test.predecision.expected_net_r",
            "probability": "unit_test.predecision.probability",
            "fill_probability": (
                "unit_test.predecision_limit_fillability_probability"
            ),
            "source_completeness": "unit_test.predecision.source_completeness",
        },
        "candidate_decision_quality_source_boundary": (
            "predecision_unit_test_quality_no_outcome_fields"
        ),
        "candidate_decision_quality_alias_status": "exact_materialized",
        "candidate_decision_quality_alias_mismatches": [],
        "candidate_decision_quality_provenance_failures": [],
        "candidate_decision_quality_optional_provenance_warnings": [],
        "ultimate_candidate_package_open_reduced_risk_authority": {
            "applies": True,
            "allowed": True,
            "authority_family": authority_family,
            "authority_source": "unit_test_predecision_authority",
            "selector_reason": selector_reason,
            "source_boundary": (
                "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
            ),
            "source_bound_candidate_use_allowed_now": True,
            "broker_cost_passed_for_package_router": True,
            "positive_predecision_package_edge": True,
        },
    }
    signed_authority = _complete_test_authority_surface(
        row,
        selector_action=row["selector_action"],
        selector_reason=row["selector_reason"],
        authority=row["ultimate_candidate_package_open_reduced_risk_authority"],
        action_intent="new_position",
        matched_member_axis_id=matched_member_axis_id,
    )
    row.update(signed_authority)
    row["ultimate_candidate_package_open_reduced_risk_authority"] = dict(
        signed_authority
    )
    return row


def _signed_compact_missed_source(
    *,
    candidate_id: str,
    selector_reason: str,
) -> dict:
    decision_time = "2026-05-13T08:00:00+00:00"
    instance_key = f"{candidate_id}@@{decision_time}"
    row = {
        "candidate_id": candidate_id,
        "candidate_id_source": "candidate_id",
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": instance_key,
        "source_bound_replay_candidate_instance_key": instance_key,
        "candidate_instance_identity_status": "materialized",
        "symbol": "XAUUSD",
        "side": "LONG",
        "selector_action": "open-reduced-risk",
        "effective_selector_action": "open-reduced-risk",
        "selector_reason": selector_reason,
        "scheduler_materialization_action_intent": "new_position",
        "expected_net_r": 1.1,
        "probability": 0.85,
        "fill_probability": 0.8,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "unit_test.predecision.expected_net_r",
            "probability": "unit_test.predecision.probability",
            "fill_probability": "unit_test.predecision.fill_probability",
            "source_completeness": "unit_test.predecision.source_completeness",
        },
        "candidate_decision_quality_source_boundary": (
            "predecision_unit_test_quality_no_outcome_fields"
        ),
        "candidate_decision_quality_alias_status": "exact_materialized",
        "candidate_decision_quality_alias_mismatches": [],
        "candidate_decision_quality_provenance_failures": [],
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "candidate_cost_r_fallback_is_authority": False,
        "source_bound_package_candidate_use_allowed": True,
        "package_replay_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed_reason": (
            "signed_compact_missed_fixture_executable"
        ),
        "package_replay_order_executable_candidate_use_allowed": True,
        "package_replay_order_executable_candidate_use_allowed_reason": (
            "signed_compact_missed_fixture_order_executable"
        ),
        "package_replay_order_executable_authority_source": (
            "signed_compact_missed_fixture_predecision_authority"
        ),
        "replay_candidate_use_allowed_now": True,
        "ultimate_package_effective_executable_authority_allowed": True,
        "missed_package_replay_order_executable_candidate_use_allowed": True,
        "order_status": "not_sent_missed_opportunity",
    }
    authority = _complete_test_authority_surface(
        row,
        selector_action="open-reduced-risk",
        selector_reason=selector_reason,
        action_intent="new_position",
        authority={
            "applies": True,
            "allowed": True,
            "authority_family": "compact_missed_unit_test",
            "authority_source": "signed_compact_missed_fixture_predecision_authority",
            "source_boundary": (
                "predecision_compact_missed_authority_no_outcome_fields"
            ),
        },
    )
    row.update(authority)
    row["ultimate_candidate_package_open_reduced_risk_authority"] = dict(authority)
    row["scheduler_candidate_decision_inputs"] = {
        "expected_net_r": row["expected_net_r"],
        "probability": row["probability"],
        "fill_probability": row["fill_probability"],
        "source_completeness": row["source_completeness"],
        **authority,
        "ultimate_candidate_package_open_reduced_risk_authority": dict(authority),
    }
    return row


def test_selected_bridge_explicit_non_router_family_ignores_stale_router_reason() -> None:
    bridge = load_selected_package_replay_bridge()
    row = _signed_bridge_router_refusal_row(
        "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk",
        authority_family="fill_floor_softening",
    )
    row["expected_net_r"] = 0.01
    row["candidate_expected_net_r"] = 0.01
    row["probability"] = 0.01
    row["candidate_probability"] = 0.01
    row["fill_probability"] = 0.01
    row["candidate_fill_probability"] = 0.01
    row.update(_execution_fillability_fields(0.01))
    row["ultimate_candidate_package_open_reduced_risk_authority"][
        "authority_family"
    ] = "fill_floor_softening"
    _resign_test_authority(
        row,
        expect_valid=True,
    )

    assert bridge._router_refusal_open_reduced_authority_applies(row) is False
    assert bridge.trusted_signed_package_new_entry_authority_surface(row) is True
    assert (
        bridge.signed_reduced_package_bridge_authority_block_reason(
            row,
            selector_action=row["selector_action"],
            selector_reason=row["selector_reason"],
            action_intent="new_position",
        )
        is None
    )


def test_selected_bridge_source_bound_router_refusal_uses_materialization_floors() -> None:
    bridge = load_selected_package_replay_bridge()
    row = _signed_bridge_router_refusal_row(
        "source_bound_router_refusal_open_reduced_materialized_for_replay"
    )

    assert bridge.trusted_signed_package_new_entry_authority_surface(row) is True
    assert (
        bridge.signed_reduced_package_bridge_authority_block_reason(
            row,
            selector_action=row["selector_action"],
            selector_reason=row["selector_reason"],
            action_intent="new_position",
        )
        is None
    )


def test_selected_bridge_positive_predecision_router_refusal_stays_strict() -> None:
    bridge = load_selected_package_replay_bridge()
    row = _signed_bridge_router_refusal_row(
        "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk"
    )

    assert bridge.trusted_signed_package_new_entry_authority_surface(row) is True
    row["expected_net_r"] = 0.80
    row["candidate_expected_net_r"] = 0.80
    signed_authority = _resign_test_authority(row, expect_valid=False)

    assert "router_refusal_expected_net_r_below_floor" in signed_authority[
        "package_new_entry_authority_failures"
    ]
    assert bridge.trusted_signed_package_new_entry_authority_surface(row) is False
    block_reason = bridge.signed_reduced_package_bridge_authority_block_reason(
        row,
        selector_action=row["selector_action"],
        selector_reason=row["selector_reason"],
        action_intent="new_position",
    )
    assert block_reason is not None
    assert "router_refusal_expected_net_r_below_floor" in block_reason


def _agent_config_runtime() -> dict:
    with (ROOT / "config/agent_config.yaml").open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    runtime = config.get("gtos_vnext_runtime")
    assert isinstance(runtime, dict)
    return runtime


def test_reduced_risk_action_intent_contract_is_shared_across_replay_surfaces() -> None:
    bridge = load_selected_package_replay_bridge()

    assert bridge.SELECTOR_REDUCE_RISK_ALLOWED_ACTION_INTENTS == (
        SELECTOR_REDUCE_RISK_ALLOWED_ACTION_INTENTS
    )
    assert timewarp.SELECTOR_REDUCE_RISK_ALLOWED_ACTION_INTENTS == (
        SELECTOR_REDUCE_RISK_ALLOWED_ACTION_INTENTS
    )
    assert bridge.SELECTOR_OPEN_REDUCED_RISK_ALLOWED_ACTION_INTENTS == (
        SELECTOR_OPEN_REDUCED_RISK_ALLOWED_ACTION_INTENTS
    )
    assert timewarp.SELECTOR_OPEN_REDUCED_RISK_ALLOWED_ACTION_INTENTS == (
        SELECTOR_OPEN_REDUCED_RISK_ALLOWED_ACTION_INTENTS
    )
    assert bridge.SIGNED_REDUCED_PACKAGE_NEW_ENTRY_ACTIONS == (
        REDUCED_RISK_SIGNED_NEW_ENTRY_ACTION_INTENTS
    )
    assert timewarp.SIGNED_REDUCED_PACKAGE_NEW_ENTRY_ACTIONS == (
        REDUCED_RISK_SIGNED_NEW_ENTRY_ACTION_INTENTS
    )
    assert scheduler.REDUCED_RISK_SIGNED_NEW_ENTRY_ACTIONS == (
        REDUCED_RISK_SIGNED_NEW_ENTRY_ACTION_INTENTS
    )
    assert "close_and_reverse" in SELECTOR_OPEN_REDUCED_RISK_ALLOWED_ACTION_INTENTS
    assert "close_and_reverse" in REDUCED_RISK_SIGNED_NEW_ENTRY_ACTION_INTENTS
    assert "replace_pending" in REDUCED_RISK_SIGNED_NEW_ENTRY_ACTION_INTENTS
    assert bridge.SCHEDULER_ACTION_INTENT_ALIASES == SCHEDULER_ACTION_INTENT_ALIASES
    assert timewarp.SCHEDULER_ACTION_INTENT_ALIASES == SCHEDULER_ACTION_INTENT_ALIASES
    assert scheduler.ACTION_INTENT_ALIASES == SCHEDULER_ACTION_INTENT_ALIASES
    assert scheduler.OPEN_REDUCED_SELECTOR_REASONS == OPEN_REDUCED_SELECTOR_REASONS
    assert timewarp.SELECTOR_OPEN_REDUCED_RISK_REASON_ALIASES == (
        OPEN_REDUCED_SELECTOR_REASONS
    )
    reason = "ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay"
    assert scheduler._normalize_selector_action_for_reason("reduce-risk", reason) == (
        "reduce-risk"
    )
    assert timewarp.normalize_selector_action_for_reason("reduce-risk", reason) == (
        "reduce-risk"
    )
    assert normalize_selector_action_for_reason("reduce-risk", reason) == (
        "reduce-risk"
    )
    dynamic_router_reason = "ultimate_candidate_package_dynamic_router_refusal_softened_reduce_risk"
    assert normalize_selector_action_for_reason(
        "reduce-risk",
        dynamic_router_reason,
        "new_position",
    ) == "reduce-risk"
    assert normalize_selector_action_for_reason(
        "reduce-risk",
        dynamic_router_reason,
        "reduce_existing",
    ) == "reduce-risk"
    assert normalize_selector_action_for_reason(
        None,
        "source_bound_fill_floor_package_materialized_for_replay",
        "new_position",
    ) == "open-reduced-risk"
    assert normalize_selector_action_for_reason(
        None,
        "selected_package_bridge_open_reduced_materialized_for_replay",
        "new_position",
    ) == "open-reduced-risk"
    assert normalize_selector_action_for_reason(
        None,
        "broker_net_admission_ev_below_full_trade_floor",
        "new_position",
    ) == ""
    assert normalize_selector_action_for_reason(
        "reduce-risk",
        "broker_net_admission_ev_below_full_trade_floor",
        "new_position",
    ) == "reduce-risk"


def test_broad_source_resolver_m1_below_floor_preserves_predecision_symbol_day(
    tmp_path: Path,
    monkeypatch,
) -> None:
    harness = load_broad_replay_harness()
    data_root = tmp_path / "data"
    m1_dir = data_root / "bridge_ftmo_m1_202605"
    m1_dir.mkdir(parents=True)
    (m1_dir / "XAUUSD_M1.csv").write_text(
        "time,open,high,low,close,volume\n"
        "2026-05-13T00:00:00+00:00,1,2,1,1.5,10\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(harness, "data_roots", lambda: (data_root,))
    m15_rows = (
        {
            "time_utc": "2026-05-13T00:00:00+00:00",
            "time": "2026-05-13T00:00:00+00:00",
            "symbol": "XAUUSD",
            "open": 1.0,
            "high": 2.0,
            "low": 1.0,
            "close": 1.5,
            "volume": 10.0,
        },
    )
    m15 = harness.ResolvedSource(
        spec=harness.SourceSpec(
            symbol="XAUUSD",
            mapped_symbol="XAUUSD",
            timeframe="M15",
            path=tmp_path / "m15.csv",
            source_family="test_m15",
            source_broker="FTMO",
            source_role="unit_test",
        ),
        rows=m15_rows,
        rows_by_day={"2026-05-13": m15_rows},
        sha256="m15",
        day_counts={"2026-05-13": 1},
        selected_status="selected_source_meets_floor",
        min_required_rows_per_day=1,
    )
    resolver = harness.BroadSourceResolver()

    result = resolver.resolve_m1_for_days(
        symbol="XAUUSD",
        days=("2026-05-13",),
        m15_source=m15,
    )

    assert result is not None
    assert result.spec.diagnostic_fallback_only is False
    assert result.selected_status == (
        "selected_m1_all_session_days_diagnostic_path_proxy_required"
    )
    assert result.source_gaps == ()
    assert result.day_source_authority["2026-05-13"][
        "diagnostic_fallback_only"
    ] is True
    statuses = [row.get("status") for row in resolver.source_rows]
    assert "selected_day_source_below_session_scaled_floor" in statuses
    assert (
        "m1_requested_symbol_days_below_session_scaled_floor" in statuses
    )


def test_broad_source_resolver_m1_accepts_broker_shortened_session_floor(
    tmp_path: Path,
    monkeypatch,
) -> None:
    harness = load_broad_replay_harness()
    data_root = tmp_path / "data"
    m1_dir = data_root / "bridge_ftmo_m1_202604"
    m1_dir.mkdir(parents=True)
    rows = [
        f"2026-04-03T00:{minute:02d}:00+00:00,1,2,1,1.5,10\n"
        for minute in range(12)
    ]
    (m1_dir / "JP225_M1.csv").write_text(
        "time,open,high,low,close,volume\n" + "".join(rows),
        encoding="utf-8",
    )
    monkeypatch.setattr(harness, "data_roots", lambda: (data_root,))
    m15_rows = (
        {
            "time_utc": "2026-04-03T00:00:00+00:00",
            "time": "2026-04-03T00:00:00+00:00",
            "symbol": "JP225",
            "open": 1.0,
            "high": 2.0,
            "low": 1.0,
            "close": 1.5,
            "volume": 10.0,
        },
    )
    m15 = harness.ResolvedSource(
        spec=harness.SourceSpec(
            symbol="JP225",
            mapped_symbol="JP225",
            timeframe="M15",
            path=tmp_path / "m15.csv",
            source_family="test_m15",
            source_broker="FTMO",
            source_role="unit_test",
        ),
        rows=m15_rows,
        rows_by_day={"2026-04-03": m15_rows},
        sha256="m15",
        day_counts={"2026-04-03": 1},
        selected_status="selected_source_meets_floor",
        min_required_rows_per_day=1,
    )

    result = harness.BroadSourceResolver().resolve_m1_for_days(
        symbol="JP225",
        days=("2026-04-03",),
        m15_source=m15,
    )

    authority = result.day_source_authority["2026-04-03"]
    assert authority["status"] == (
        "selected_day_source_meets_session_scaled_floor"
    )
    assert authority["effective_min_rows"] == 12
    assert authority["diagnostic_fallback_only"] is False
    assert result.spec.diagnostic_fallback_only is False
    assert result.source_gaps == ()


def test_broad_source_resolver_m1_gap_is_scoped_to_one_symbol_day(
    tmp_path: Path,
    monkeypatch,
) -> None:
    harness = load_broad_replay_harness()
    data_root = tmp_path / "data"
    m1_dir = data_root / "bridge_ftmo_m1_202604"
    m1_dir.mkdir(parents=True)
    valid_rows = [
        f"2026-04-02T00:{minute:02d}:00+00:00,1,2,1,1.5,10\n"
        for minute in range(12)
    ]
    gap_row = "2026-04-03T00:00:00+00:00,1,2,1,1.5,10\n"
    (m1_dir / "JP225_M1.csv").write_text(
        "time,open,high,low,close,volume\n"
        + "".join(valid_rows)
        + gap_row,
        encoding="utf-8",
    )
    monkeypatch.setattr(harness, "data_roots", lambda: (data_root,))
    m15_rows = tuple(
        {
            "time_utc": f"{day}T00:00:00+00:00",
            "time": f"{day}T00:00:00+00:00",
            "symbol": "JP225",
            "open": 1.0,
            "high": 2.0,
            "low": 1.0,
            "close": 1.5,
            "volume": 10.0,
        }
        for day in ("2026-04-02", "2026-04-03")
    )
    m15 = harness.ResolvedSource(
        spec=harness.SourceSpec(
            symbol="JP225",
            mapped_symbol="JP225",
            timeframe="M15",
            path=tmp_path / "m15.csv",
            source_family="test_m15",
            source_broker="FTMO",
            source_role="unit_test",
        ),
        rows=m15_rows,
        rows_by_day={
            "2026-04-02": (m15_rows[0],),
            "2026-04-03": (m15_rows[1],),
        },
        sha256="m15",
        day_counts={"2026-04-02": 1, "2026-04-03": 1},
        selected_status="selected_source_meets_floor",
        min_required_rows_per_day=1,
    )

    result = harness.BroadSourceResolver().resolve_m1_for_days(
        symbol="JP225",
        days=("2026-04-02", "2026-04-03"),
        m15_source=m15,
    )

    assert result.selected_status == (
        "selected_composite_m1_days_with_symbol_day_scoped_gaps"
    )
    assert result.spec.diagnostic_fallback_only is False
    assert result.day_source_authority["2026-04-02"][
        "diagnostic_fallback_only"
    ] is False
    assert result.day_source_authority["2026-04-03"][
        "diagnostic_fallback_only"
    ] is True


def test_selected_package_bridge_m1_gap_does_not_demote_valid_sibling_day(
    tmp_path: Path,
) -> None:
    bridge = load_selected_package_replay_bridge()
    source_path = tmp_path / "JP225_M1.csv"
    rows = [
        f"2026-04-02T00:{minute:02d}:00+00:00,1,2,1,1.5,10\n"
        for minute in range(12)
    ]
    source_path.write_text(
        "time,open,high,low,close,volume\n" + "".join(rows),
        encoding="utf-8",
    )
    source_sha = bridge.file_sha256(source_path)
    m15_rows = tuple(
        {
            "time_utc": f"{day}T00:00:00+00:00",
            "time": f"{day}T00:00:00+00:00",
            "symbol": "JP225",
            "open": 1.0,
            "high": 2.0,
            "low": 1.0,
            "close": 1.5,
            "volume": 10.0,
        }
        for day in ("2026-04-02", "2026-04-03")
    )
    m15 = bridge.ResolvedSource(
        spec=bridge.SourceSpec(
            symbol="JP225",
            mapped_symbol="JP225",
            timeframe="M15",
            path=tmp_path / "JP225_M15.csv",
            source_family="fixture",
            source_broker="FTMO",
            source_role="unit_test",
        ),
        rows=m15_rows,
        rows_by_day={
            "2026-04-02": (m15_rows[0],),
            "2026-04-03": (m15_rows[1],),
        },
        sha256="m15",
        day_counts={"2026-04-02": 1, "2026-04-03": 1},
        selected_status="selected_source_meets_floor",
        min_required_rows_per_day=1,
    )
    selection = {
        "symbol": "JP225",
        "mapped_symbol": "JP225",
        "timeframe": "M1",
        "selected": True,
        "selected_source_path": str(source_path),
        "selected_manifest_path": str(tmp_path / "manifest.json"),
        "selected_manifest_rows": 12,
        "required_window_start": "2026-04-02T00:00:00+00:00",
        "required_window_end_exclusive": "2026-04-03T00:00:00+00:00",
    }

    source, hydration, _labels = bridge.resolved_m1_source(
        symbol="JP225",
        replay_days=("2026-04-02", "2026-04-03"),
        day_rows={("JP225", "2026-04-02"): selection},
        m15_source=m15,
        selected_files={
            str(source_path): {
                "manifest_sha256": source_sha,
                "source_broker": "FTMO",
                "source_role": "unit_test",
            }
        },
        cache={},
    )

    assert source is not None
    assert source.spec.diagnostic_fallback_only is False
    assert source.source_gaps == ()
    assert source.day_source_authority["2026-04-02"][
        "diagnostic_fallback_only"
    ] is False
    assert source.day_source_authority["2026-04-02"][
        "path_replay_allowed"
    ] is True
    assert source.day_source_authority["2026-04-03"][
        "diagnostic_fallback_only"
    ] is True
    assert source.day_source_authority["2026-04-03"][
        "path_replay_allowed"
    ] is False
    assert {row["trading_day"] for row in hydration} == {
        "2026-04-02",
        "2026-04-03",
    }


def test_source_authority_v2_binds_full_window_and_exact_chunk_m1_subset(
    tmp_path: Path,
) -> None:
    harness = load_broad_replay_harness()
    symbol = "XAUUSD"
    days = ("2026-04-01", "2026-04-02")

    def source(timeframe: str, *, authorities=None):
        rows = tuple(
            {
                "time_utc": f"{day}T00:00:00+00:00",
                "time": f"{day}T00:00:00+00:00",
                "symbol": symbol,
                "open": 1.0,
                "high": 2.0,
                "low": 1.0,
                "close": 1.5,
            }
            for day in (
                tuple(authorities) if authorities is not None else days
            )
        )
        return harness.ResolvedSource(
            spec=harness.SourceSpec(
                symbol=symbol,
                mapped_symbol=symbol,
                timeframe=timeframe,
                path=tmp_path / f"{symbol}_{timeframe}.csv",
                source_family="fixture",
                source_broker="FTMO",
                source_role="unit_test",
            ),
            rows=rows,
            rows_by_day={str(row["time_utc"])[:10]: (row,) for row in rows},
            sha256=harness.stable_sha256({"timeframe": timeframe}),
            day_counts={str(row["time_utc"])[:10]: 1 for row in rows},
            selected_status="selected_source_meets_floor",
            min_required_rows_per_day=1,
            day_source_authority=(
                {
                    day: harness.m1_symbol_day_source_authority(
                        symbol=symbol,
                        trading_day=day,
                        m1_row_count=12,
                        m15_row_count=1,
                    )
                    for day in authorities
                }
                if authorities is not None
                else {}
            ),
        )

    static = {
        timeframe: source(timeframe)
        for timeframe in harness.STATIC_SOURCE_AUTHORITY_TIMEFRAMES
    }
    full_sources = {symbol: {**static, "M1": source("M1", authorities=days)}}
    chunk_sources = {
        symbol: {**static, "M1": source("M1", authorities=(days[0],))}
    }
    full = harness.static_source_authority_plan(
        sources=full_sources,
        source_authority_days=days,
        requested_symbols=(symbol,),
    )
    chunk = harness.static_source_authority_plan(
        sources=chunk_sources,
        source_authority_days=(days[0],),
        requested_symbols=(symbol,),
    )

    checkpoint = harness.source_authority_chunk_checkpoint(
        profile=harness.PROFILE_REPAIRED,
        split="development",
        execution_days=(days[0],),
        source_plan=chunk,
        canonical_plan=full,
    )

    assert full["valid"] is True
    assert chunk["valid"] is True
    assert full["m1_symbol_day_authority_row_count"] == 2
    assert chunk["m1_symbol_day_authority_row_count"] == 1
    assert full["plan_digest_sha256"] != chunk["plan_digest_sha256"]
    assert checkpoint["canonical_source_plan_digest_sha256"] == full[
        "plan_digest_sha256"
    ]
    assert checkpoint["source_plan_digest_sha256"] == full[
        "plan_digest_sha256"
    ]
    assert checkpoint["source_plan_matches_canonical"] is True
    assert checkpoint["static_sources_match_canonical"] is True
    assert checkpoint["tick_component_sources_match_canonical"] is True
    assert checkpoint["m1_execution_day_authority_matches_canonical"] is True

    mutated = copy.deepcopy(chunk)
    mutated["m1_symbol_day_authority_rows"][0][
        "source_day_authority_hash_sha256"
    ] = "f" * 64
    drift = harness.source_authority_chunk_checkpoint(
        profile=harness.PROFILE_REPAIRED,
        split="development",
        execution_days=(days[0],),
        source_plan=mutated,
        canonical_plan=full,
    )
    assert drift["source_plan_matches_canonical"] is False
    assert drift["m1_execution_day_authority_matches_canonical"] is False


def test_broad_source_resolver_uses_family_priority_across_data_roots(
    tmp_path: Path,
    monkeypatch,
) -> None:
    harness = load_broad_replay_harness()
    active_root = tmp_path / "active"
    integration_root = tmp_path / "integration"
    low = active_root / "low_priority"
    high = integration_root / "high_priority"
    low.mkdir(parents=True)
    high.mkdir(parents=True)
    row = "time,open,high,low,close,volume\n2026-06-01T00:00:00+00:00,1,2,1,1.5,10\n"
    (low / "XAUUSD_D1.csv").write_text(row, encoding="utf-8")
    (high / "XAUUSD_D1.csv").write_text(row, encoding="utf-8")
    monkeypatch.setattr(
        harness,
        "data_roots",
        lambda: (active_root, integration_root),
    )

    result = harness.BroadSourceResolver().resolve_file_source(
        symbol="XAUUSD",
        timeframe="D1",
        root_order=("high_priority", "low_priority"),
        min_total_rows=1,
        requested_days=("2026-06-01",),
    )

    assert result is not None
    assert result.spec.source_family == "high_priority"
    assert result.spec.path == high / "XAUUSD_D1.csv"


def test_broad_source_resolver_m1_uses_consistent_supplemental_gap_fill(
    tmp_path: Path,
    monkeypatch,
) -> None:
    harness = load_broad_replay_harness()
    data_root = tmp_path / "data"
    monthly = data_root / "bridge_ftmo_m1_202606"
    supplemental = data_root / "supplemental_m1"
    monthly.mkdir(parents=True)
    supplemental.mkdir(parents=True)
    header = "time,open,high,low,close,volume\n"
    day_one = "2026-06-01T00:00:00+00:00,1,2,1,1.5,10\n"
    day_two = "2026-06-02T00:00:00+00:00,2,3,2,2.5,10\n"
    (monthly / "XAUUSD_M1.csv").write_text(header + day_one, encoding="utf-8")
    (supplemental / "XAUUSD_M1.csv").write_text(
        header + day_one + day_two,
        encoding="utf-8",
    )
    monkeypatch.setattr(harness, "data_roots", lambda: (data_root,))
    monkeypatch.setattr(harness, "M1_MIN_ROWS_PER_DAY", 1)
    monkeypatch.setattr(
        harness,
        "M1_SUPPLEMENTAL_ROOT_ORDER_BY_MONTH",
        {"202606": ("supplemental_m1",)},
    )
    m15_rows = tuple(
        {
            "time_utc": f"{day}T00:00:00+00:00",
            "time": f"{day}T00:00:00+00:00",
            "symbol": "XAUUSD",
            "open": 1.0,
            "high": 2.0,
            "low": 1.0,
            "close": 1.5,
            "volume": 10.0,
        }
        for day in ("2026-06-01", "2026-06-02")
    )
    m15 = harness.ResolvedSource(
        spec=harness.SourceSpec(
            symbol="XAUUSD",
            mapped_symbol="XAUUSD",
            timeframe="M15",
            path=tmp_path / "m15.csv",
            source_family="test_m15",
            source_broker="FTMO",
            source_role="unit_test",
        ),
        rows=m15_rows,
        rows_by_day={
            "2026-06-01": (m15_rows[0],),
            "2026-06-02": (m15_rows[1],),
        },
        sha256="m15",
        day_counts={"2026-06-01": 1, "2026-06-02": 1},
        selected_status="selected_source_meets_floor",
        min_required_rows_per_day=1,
    )

    resolver = harness.BroadSourceResolver()
    result = resolver.resolve_m1_for_days(
        symbol="XAUUSD",
        days=("2026-06-01", "2026-06-02"),
        m15_source=m15,
    )

    assert result is not None
    assert result.source_gaps == ()
    assert result.component_source_labels[0]["source_family"] == "bridge_ftmo_m1_202606"
    assert result.component_source_labels[1]["source_family"] == "supplemental_m1"
    assert any(
        row.get("status") == "m1_source_overlap_consistent"
        for row in resolver.source_rows
    )


def test_broad_source_resolver_m1_fails_closed_on_overlap_conflict(
    tmp_path: Path,
    monkeypatch,
) -> None:
    harness = load_broad_replay_harness()
    data_root = tmp_path / "data"
    monthly = data_root / "bridge_ftmo_m1_202606"
    supplemental = data_root / "supplemental_m1"
    monthly.mkdir(parents=True)
    supplemental.mkdir(parents=True)
    header = "time,open,high,low,close,volume\n"
    (monthly / "XAUUSD_M1.csv").write_text(
        header + "2026-06-01T00:00:00+00:00,1,2,1,1.5,10\n",
        encoding="utf-8",
    )
    (supplemental / "XAUUSD_M1.csv").write_text(
        header + "2026-06-01T00:00:00+00:00,1,2,1,1.7,10\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(harness, "data_roots", lambda: (data_root,))
    monkeypatch.setattr(
        harness,
        "M1_SUPPLEMENTAL_ROOT_ORDER_BY_MONTH",
        {"202606": ("supplemental_m1",)},
    )
    m15_rows = (
        {
            "time_utc": "2026-06-01T00:00:00+00:00",
            "time": "2026-06-01T00:00:00+00:00",
            "symbol": "XAUUSD",
            "open": 1.0,
            "high": 2.0,
            "low": 1.0,
            "close": 1.5,
            "volume": 10.0,
        },
    )
    m15 = harness.ResolvedSource(
        spec=harness.SourceSpec(
            symbol="XAUUSD",
            mapped_symbol="XAUUSD",
            timeframe="M15",
            path=tmp_path / "m15.csv",
            source_family="test_m15",
            source_broker="FTMO",
            source_role="unit_test",
        ),
        rows=m15_rows,
        rows_by_day={"2026-06-01": m15_rows},
        sha256="m15",
        day_counts={"2026-06-01": 1},
        selected_status="selected_source_meets_floor",
        min_required_rows_per_day=1,
    )

    with pytest.raises(ValueError, match="m1_source_overlap_conflict"):
        harness.BroadSourceResolver().resolve_m1_for_days(
            symbol="XAUUSD",
            days=("2026-06-01",),
            m15_source=m15,
        )


def test_broad_source_resolver_derived_h1_returns_day_mapping(tmp_path: Path) -> None:
    harness = load_broad_replay_harness()
    m15_rows = tuple(
        {
            "time_utc": f"2026-05-13T00:{minute:02d}:00+00:00",
            "time": f"2026-05-13T00:{minute:02d}:00+00:00",
            "symbol": "GER40",
            "open": 100.0 + minute,
            "high": 101.0 + minute,
            "low": 99.0 + minute,
            "close": 100.5 + minute,
            "volume": 10.0,
        }
        for minute in (0, 15, 30, 45)
    )
    m15 = harness.ResolvedSource(
        spec=harness.SourceSpec(
            symbol="GER40",
            mapped_symbol="GER40",
            timeframe="M15",
            path=tmp_path / "GER40_M15.csv",
            source_family="unit_test_m15",
            source_broker="FTMO",
            source_role="unit_test",
        ),
        rows=m15_rows,
        rows_by_day={"2026-05-13": m15_rows},
        sha256="unit-test-m15",
        day_counts={"2026-05-13": 4},
        selected_status="selected_source_meets_floor",
        min_required_rows_per_day=1,
    )

    result = harness.BroadSourceResolver().resolve_h1(
        "GER40",
        m15,
        requested_days=("2026-05-13",),
    )

    assert result.day_counts == {"2026-05-13": 1}
    assert list(result.rows_by_day) == ["2026-05-13"]
    assert len(result.rows_by_day["2026-05-13"]) == 1
    assert result.rows_by_day["2026-05-13"][0]["source_records"] == 4


def test_broad_source_resolver_bounded_d1_slice_preserves_live_lookback(
    tmp_path: Path,
    monkeypatch,
) -> None:
    harness = load_broad_replay_harness()
    data_root = tmp_path / "data"
    d1_dir = data_root / "deep_universe_h4d1_2014_2026"
    d1_dir.mkdir(parents=True)
    d1_path = d1_dir / "XAUUSD_D1.csv"

    rows = ["time,open,high,low,close,volume\n"]
    current = date(2026, 3, 20)
    end = date(2026, 5, 15)
    price = 100.0
    while current <= end:
        if current.weekday() < 5:
            rows.append(
                f"{current.isoformat()}T00:00:00+00:00,{price},{price + 1},{price - 1},{price + 0.5},100\n"
            )
            price += 1.0
        current += timedelta(days=1)
    d1_path.write_text("".join(rows), encoding="utf-8")
    monkeypatch.setattr(harness, "data_roots", lambda: (data_root,))

    resolver = harness.BroadSourceResolver()
    selected, grouped, _sha256, metadata = resolver.load_file_replay_lookback_window(
        d1_path,
        symbol="XAUUSD",
        timeframe="D1",
        days=("2026-05-13",),
        min_total_rows=harness.HTF_MIN_TOTAL_ROWS["D1"],
    )

    predecision_rows = [
        row
        for row in selected
        if str(row.get("time_utc") or row.get("time") or "") < "2026-05-13"
    ]
    assert len(predecision_rows) >= harness.DEFAULT_LOOKBACKS["D1"]
    assert metadata["bounded_replay_required_live_lookback_rows"] == harness.DEFAULT_LOOKBACKS["D1"]
    assert metadata["bounded_replay_prewindow_selected_rows"] >= harness.DEFAULT_LOOKBACKS["D1"]
    assert metadata["bounded_replay_source_selection_mode"] == (
        "count_preserving_predecision_lookback_slice"
    )
    assert grouped["2026-05-13"]


def test_summary_accumulator_reports_generated_candidates_when_candidate_ledger_omitted() -> None:
    harness = load_broad_replay_harness()
    accumulator = harness.SummaryAccumulator()

    accumulator.add_result(
        profile="repaired_package_conversion_v3",
        split="holdout",
        days=("2026-05-13",),
        result={
            "ledgers": {
                "asof": [
                    {
                        "symbol": "XAUUSD",
                        "raw_data_status": "live_equivalent_raw_data_built_and_mso_computed",
                        "candidate_count": 7,
                    },
                    {
                        "symbol": "USDJPY",
                        "raw_data_status": "source_required_insufficient_live_timeframes",
                        "candidate_count": 0,
                        "source_required_exception_type": "DataIncompleteError",
                    },
                ],
                "candidate": [],
                "scorecard": [],
                "order": [],
                "trade": [],
                "oracle": [],
                "missed": [],
            }
        },
    )

    row = accumulator.serializable_stats()[0]
    assert row["candidate_rows"] == 0
    assert row["candidate_rows_generated_from_decisions"] == 7
    assert row["candidate_generation_by_symbol"] == {"XAUUSD": 7}
    assert row["candidate_generating_decision_rows_by_symbol"] == {"XAUUSD": 1}
    assert row["raw_data_status_by_symbol"]["USDJPY"] == {
        "source_required_insufficient_live_timeframes": 1
    }
    assert row["source_required_exception_by_symbol"]["USDJPY"] == {
        "DataIncompleteError": 1
    }


def test_zero_candidate_run_status_not_materialized_proof(
    tmp_path: Path,
    monkeypatch,
) -> None:
    harness = load_broad_replay_harness()
    monkeypatch.setattr(harness, "ROUTE", tmp_path)
    monkeypatch.setattr(harness, "GTOS_24_SYMBOL_SURFACE", ("XAUUSD",))
    monkeypatch.setattr(
        harness,
        "build_config",
        lambda profile, *, factorial_arm_binding=None: {},
    )
    runtime_contract = {
        "schema": harness.ULTIMATE_PACKAGE_RUNTIME_INPUT_CONTRACT_SCHEMA,
        "status": "unit_test_runtime_inputs_valid",
        "valid": True,
        "inputs": {},
    }
    monkeypatch.setattr(
        harness,
        "ultimate_package_runtime_input_contract",
        lambda: runtime_contract,
    )
    monkeypatch.setattr(
        harness,
        "require_ultimate_package_runtime_inputs",
        lambda *, contract: dict(contract),
    )
    monkeypatch.setattr(harness, "summarize_campaign", lambda result, phase: {})
    campaign_gc_states: list[bool] = []
    ledger_flush_gc_states: list[bool] = []
    cache_release_days: list[tuple[str, ...]] = []
    source_authority_calls: list[tuple[str, ...]] = []
    explicit_gc_states: list[bool] = []

    class FakeResolver:
        def __init__(self, **_kwargs):
            self.source_rows = []

        def build_sources_for_days(
            self,
            days,
            *,
            symbols=None,
            source_authority_days=None,
        ):
            del symbols
            source_authority_calls.append(tuple(source_authority_days or ()))
            self.source_rows.append(
                {
                    "row_type": "source_selection",
                    "symbol": "XAUUSD",
                    "timeframe": "M15",
                    "status": "unit_test_source",
                }
            )
            return {"XAUUSD": {}}

        def drain_source_rows(self):
            rows = list(self.source_rows)
            self.source_rows.clear()
            return rows

        def release_completed_chunk_caches(
            self,
            days,
            *,
            source_authority_days=(),
        ):
            day_key = tuple(days)
            cache_release_days.append(day_key)
            return {
                "requested_days": list(day_key),
                "execution_chunk_days": list(day_key),
                "source_authority_days": list(source_authority_days),
                "before": {"file": 0, "day_file": 1, "htf": 1, "tick": 1},
                "after": {"file": 0, "day_file": 0, "htf": 0, "tick": 1},
                "released_day_file_entries": 1,
                "released_day_file_rows": 1,
                "released_htf_entries": 1,
                "released_htf_rows": 1,
                "persistent_tick_source_entries": 1,
                "persistent_full_file_entries": 0,
                "replay_source_cache_before": {
                    "closed_bar_index": 1,
                    "row_time_index": 1,
                    "predecision_tick_query": 1,
                },
                "replay_source_cache_after": {
                    "closed_bar_index": 0,
                    "row_time_index": 0,
                    "predecision_tick_query": 0,
                },
                "completed_replay_source_cache_entries_remaining": 0,
                "completed_replay_source_caches_released": True,
                "completed_chunk_day_scoped_entries_remaining": 0,
                "completed_source_authority_scoped_entries_remaining": 0,
            }

    def fake_run_campaign(**kwargs):
        campaign_gc_states.append(gc.isenabled())
        return {
            "selected_order_sequence": kwargs["starting_order_sequence"] + 1,
            "broker": kwargs["broker"],
            "ledgers": {
                "asof": [],
                "candidate": [],
                "scorecard": [],
                "order": [],
                "trade": [],
                "oracle": [],
                "missed": [],
                "daily": [],
                "rollup": [],
                "packet_sidecar": [],
            },
        }

    monkeypatch.setattr(harness, "BroadSourceResolver", FakeResolver)
    def fake_static_source_authority_plan(
        *,
        sources,
        source_authority_days,
        requested_symbols,
    ):
        del sources
        scope = harness.source_authority_scope(source_authority_days)
        m1_authority_rows = [
            {
                "symbol": "XAUUSD",
                "trading_day": day,
                "source_day_authority_hash_sha256": harness.stable_sha256(
                    {"symbol": "XAUUSD", "trading_day": day}
                ),
            }
            for day in scope["days"]
        ]
        return {
            "schema": (
                "gtos.final_moonshot.broad_replay."
                "source_authority_plan.v2"
            ),
            "status": "valid_static_source_authority_plan",
            "valid": True,
            "source_authority_scope": scope,
            "requested_symbols": list(requested_symbols),
            "requested_symbol_count": len(tuple(requested_symbols)),
            "resolved_symbol_count": 1,
            "missing_symbols": [],
            "incomplete_sources": [],
            "source_row_count": 1,
            "static_source_digest_sha256": "a" * 64,
            "m1_day_plan_digest_sha256": harness.stable_sha256(
                m1_authority_rows
            ),
            "tick_window_plan_digest_sha256": "b" * 64,
            "tick_component_source_digest_sha256": "c" * 64,
            "plan_digest_sha256": harness.stable_sha256(
                {
                    "scope": scope,
                    "m1": m1_authority_rows,
                }
            ),
            "m1_symbol_day_authority_rows": m1_authority_rows,
            "source_rows": [],
        }

    monkeypatch.setattr(
        harness,
        "static_source_authority_plan",
        fake_static_source_authority_plan,
    )
    monkeypatch.setattr(harness, "run_campaign", fake_run_campaign)
    append_jsonl = harness.append_jsonl

    def record_ledger_flush_gc_state(path, rows):
        if str(path).endswith("_DECISION_LEDGER.jsonl"):
            ledger_flush_gc_states.append(gc.isenabled())
        return append_jsonl(path, rows)

    monkeypatch.setattr(harness, "append_jsonl", record_ledger_flush_gc_state)
    monkeypatch.setattr(
        harness.gc,
        "collect",
        lambda: explicit_gc_states.append(gc.isenabled()) or 7,
    )
    args = SimpleNamespace(
        output_prefix="UNIT_ZERO_CANDIDATE",
        use_native_h1=False,
        verbose=False,
        start="2026-05-13",
        end="2026-05-14",
        max_days=None,
        chunk_size=1,
        profiles=(harness.PROFILE_RAW,),
        omit_candidate_ledger=True,
        omit_packet_sidecar_ledger=True,
        candidate_ledger_packet_max_bytes=0,
        scorecard_ledger_packet_max_bytes=0,
        compact_scorecard_symbol_risk_config=False,
        scorecard_probe_row_limit=0,
        max_candidates_per_symbol_window=0,
        smoke_subset=False,
        gc_between_chunks=True,
    )

    summary = harness.run_replay_engine(args)

    assert campaign_gc_states == [False, False]
    assert ledger_flush_gc_states == [False, False]
    assert cache_release_days == [
        ("2026-05-13", "2026-05-14"),
        ("2026-05-13",),
        ("2026-05-14",),
    ]
    assert source_authority_calls == [
        ("2026-05-13", "2026-05-14"),
        ("2026-05-13", "2026-05-14"),
        ("2026-05-13", "2026-05-14"),
    ]
    assert explicit_gc_states == [True, False, False]
    assert gc.isenabled() is True
    assert summary["status"] == (
        "broad_live_as_if_replay_zero_candidates_no_terminal_execution_broker_live_closed"
    )
    assert summary["candidate_rows"] == 0
    assert summary["source_universe_rows"] == 6
    capacity = summary["capacity_safe_chunk_execution_contract"]
    assert summary["capacity_safe_chunk_execution_required"] is True
    assert capacity["valid"] is True
    assert capacity["status"] == "complete_capacity_safe_chunk_execution"
    assert capacity["planned_chunk_count"] == 2
    assert capacity["completed_chunk_count"] == 2
    assert capacity["cleanup_checkpoint_count"] == 2
    assert capacity["same_simulated_broker_reused_across_chunks"] is True
    assert capacity["same_account_state_reused_across_chunks"] is True
    assert capacity["selected_order_sequence_monotonic_across_chunks"] is True
    assert capacity["completed_chunk_day_scoped_source_caches_released"] is True
    assert capacity["explicit_gc_after_result_release_enabled"] is True
    assert capacity["automatic_gc_reenabled_between_chunks"] is False
    assert capacity["completed_source_authority_scoped_caches_released"] is True
    assert capacity["completed_replay_source_caches_released"] is True
    assert [
        (row["starting_order_sequence"], row["ending_order_sequence"])
        for row in capacity["checkpoints"]
    ] == [(0, 1), (1, 2)]
    source_authority = summary[
        "source_authority_chunk_invariance_contract"
    ]
    assert summary["source_authority_chunk_invariance_required"] is True
    assert source_authority["valid"] is True
    assert source_authority["status"] == (
        "complete_source_authority_chunk_invariance"
    )
    assert source_authority["canonical_plan_count"] == 1
    assert source_authority["checkpoint_count"] == 2
    assert source_authority["all_chunk_source_plans_match_canonical"] is True
    assert len(summary["source_authority_preflight_checkpoints"]) == 1
    assert (
        summary["source_authority_preflight_checkpoints"][0]["cleanup_valid"]
        is True
    )
    assert summary["schema"] == harness.BROAD_REPLAY_CURRENT_SUMMARY_SCHEMA
    assert summary["package_new_entry_authority_payload_contract"] == (
        scheduler.PACKAGE_NEW_ENTRY_AUTHORITY_IMMUTABLE_PAYLOAD_CONTRACT
    )
    assert (
        summary[
            "package_new_entry_authority_payload_required_for_signed_executable_rows"
        ]
        is True
    )
    assert summary["live_broker_authority"] is False
    assert summary["broker_mutation_enabled"] is False
    assert summary["final_selection_claim"] is False
    source_path = tmp_path / "UNIT_ZERO_CANDIDATE_SOURCE_UNIVERSE_LEDGER.jsonl"
    assert source_path.exists()
    assert source_path.read_text(encoding="utf-8").count("\n") == 6


def test_source_resolver_releases_only_completed_chunk_day_scoped_caches() -> None:
    harness = load_broad_replay_harness()
    timewarp.clear_replay_source_caches()
    resolver = harness.BroadSourceResolver(skip_tick_source=True)
    completed_days = ("2026-06-01",)
    authority_days = ("2026-06-01", "2026-06-02")
    retained_days = ("2026-06-03",)
    completed_file = Path("completed.csv")
    retained_file = Path("retained.csv")
    resolver._day_file_cache[(str(completed_file), completed_days)] = (
        ({"time": "2026-06-01T00:00:00+00:00"},),
        {},
        "completed-sha",
    )
    resolver._day_file_cache[(str(completed_file), "M15", completed_days)] = (
        ({"time": "2026-06-01T00:15:00+00:00"},),
        {},
        "completed-window-sha",
        {},
    )
    resolver._day_file_cache[(str(completed_file), "M15", authority_days)] = (
        ({"time": "2026-06-01T00:15:00+00:00"},),
        {},
        "authority-window-sha",
        {},
    )
    resolver._day_file_cache[(str(retained_file), retained_days)] = (
        ({"time": "2026-06-02T00:00:00+00:00"},),
        {},
        "retained-sha",
    )
    resolver._htf_cache[("XAUUSD", "M15", completed_days)] = SimpleNamespace(
        rows=({"time": "2026-06-01T00:00:00+00:00"},)
    )
    resolver._htf_cache[("XAUUSD", "H4", authority_days)] = SimpleNamespace(
        rows=({"time": "2026-06-01T00:00:00+00:00"},)
    )
    resolver._htf_cache[("XAUUSD", "M15", retained_days)] = SimpleNamespace(
        rows=({"time": "2026-06-02T00:00:00+00:00"},)
    )
    resolver._tick_cache[("XAUUSD", completed_days)] = None
    cached_rows = (
        {"time_utc": "2026-06-01T00:00:00+00:00", "close": 1.0},
    )
    asof = timewarp.parse_utc("2026-06-01T00:30:00+00:00")
    after = timewarp.parse_utc("2026-05-31T23:59:00+00:00")
    assert asof is not None
    assert after is not None
    timewarp.closed_bar_rows_until(
        cached_rows,
        timeframe="M15",
        asof=asof,
    )
    timewarp.rows_after_until_indexed(
        cached_rows,
        after=after,
        until=asof,
    )
    timewarp._PREDECISION_TICK_QUERY_CACHE[(1, "unit", 60.0)] = (
        object(),
        None,
        {},
    )

    release = resolver.release_completed_chunk_caches(
        completed_days,
        source_authority_days=authority_days,
    )

    assert release["released_day_file_entries"] == 3
    assert release["released_day_file_rows"] == 3
    assert release["released_htf_entries"] == 2
    assert release["released_htf_rows"] == 2
    assert release["completed_chunk_day_scoped_entries_remaining"] == 0
    assert release["completed_source_authority_scoped_entries_remaining"] == 0
    assert release["replay_source_cache_before"] == {
        "closed_bar_index": 1,
        "row_time_index": 1,
        "predecision_tick_query": 1,
    }
    assert release["replay_source_cache_after"] == {
        "closed_bar_index": 0,
        "row_time_index": 0,
        "predecision_tick_query": 0,
    }
    assert release["completed_replay_source_cache_entries_remaining"] == 0
    assert release["completed_replay_source_caches_released"] is True
    assert release["after"] == {"file": 0, "day_file": 1, "htf": 1, "tick": 1}
    assert (str(retained_file), retained_days) in resolver._day_file_cache
    assert ("XAUUSD", "M15", retained_days) in resolver._htf_cache
    assert timewarp.replay_source_cache_counts() == {
        "closed_bar_index": 0,
        "row_time_index": 0,
        "predecision_tick_query": 0,
    }


def test_source_resolver_separates_static_authority_from_execution_days(
    monkeypatch,
) -> None:
    harness = load_broad_replay_harness()
    resolver = harness.BroadSourceResolver()
    authority_days = (
        "2026-06-01",
        "2026-06-02",
        "2026-06-03",
        "2026-06-04",
        "2026-06-05",
    )
    static_calls: list[tuple[str, tuple[str, ...]]] = []
    m1_calls: list[tuple[str, tuple[str, ...], object]] = []
    tick_calls: list[tuple[str, tuple[str, ...]]] = []
    m15_source = object()
    tick_source = object()
    static_sources = {
        "D1": object(),
        "H4": object(),
        "H1": object(),
        "M15": m15_source,
    }

    def fake_static(symbol, *, requested_days=()):
        static_calls.append((symbol, tuple(requested_days)))
        return dict(static_sources)

    def fake_m1(*, symbol, days, m15_source):
        m1_calls.append((symbol, tuple(days), m15_source))
        return object()

    def fake_tick(symbol, *, source_authority_days=()):
        tick_calls.append((symbol, tuple(source_authority_days)))
        return tick_source

    monkeypatch.setattr(resolver, "resolve_static_sources", fake_static)
    monkeypatch.setattr(resolver, "resolve_m1_for_days", fake_m1)
    monkeypatch.setattr(resolver, "resolve_tick", fake_tick)

    sources = resolver.build_sources_for_days(
        ("2026-06-02",),
        symbols=("XAUUSD",),
        source_authority_days=authority_days,
    )

    assert static_calls == [("XAUUSD", authority_days)]
    assert m1_calls == [("XAUUSD", ("2026-06-02",), m15_source)]
    assert tick_calls == [("XAUUSD", authority_days)]
    assert sources["XAUUSD"]["M15"] is m15_source
    assert sources["XAUUSD"]["TICK"] is tick_source

    with pytest.raises(
        ValueError,
        match="execution_chunk_outside_source_authority_scope",
    ):
        resolver.build_sources_for_days(
            ("2026-06-06",),
            symbols=("XAUUSD",),
            source_authority_days=authority_days,
        )


def test_tick_resolver_merges_roots_by_authority_window_and_exact_sha(
    tmp_path: Path,
    monkeypatch,
) -> None:
    harness = load_broad_replay_harness()
    active_root = tmp_path / "active"
    integration_root = tmp_path / "integration"
    monkeypatch.setattr(harness, "ROOT", active_root)
    monkeypatch.setattr(harness, "MAIN_REPO_ROOT", integration_root)

    def tick_spec(
        path: Path,
        *,
        start: str,
        end: str,
        sha: str,
        rows: int = 10,
    ) -> timewarp.SourceSpec:
        return timewarp.SourceSpec(
            symbol="UKOIL_cash",
            mapped_symbol="UKOIL.cash",
            timeframe="TICK",
            path=path,
            source_family="ftmo_mt5_research_export",
            source_broker="FTMO",
            source_role="owner_authorized_path_override",
            start_utc=start,
            end_utc=end,
            row_count=rows,
            sha256=sha,
            manifest_path=str(path.parent / "manifest.json"),
            source_truth_scope=timewarp.SOURCE_TRUTH_SCOPE,
            not_redacted_account_native=True,
            broker_lifecycle_truth_satisfied=False,
            ordered_tick_truth_satisfied=True,
        )

    def resolved(specs: tuple[timewarp.SourceSpec, ...]) -> timewarp.ResolvedSource:
        first = specs[0]
        return timewarp.ResolvedSource(
            spec=first,
            rows=(),
            rows_by_day=SimpleNamespace(specs=specs),
            sha256=str(first.sha256),
            day_counts={},
            selected_status="selected_priority_tick_sources_lazy_window_load",
            min_required_rows_per_day=1,
        )

    may_spec = tick_spec(
        active_root / "bridge_ftmo_ticks_v122i" / "UKOIL_cash.jsonl",
        start="2026-05-13T00:00:00+00:00",
        end="2026-05-17T23:59:59+00:00",
        sha="1" * 64,
    )
    june_path = (
        active_root
        / "bridge_ftmo_ticks_v127_b7_3_20260601_20260605_full_plus_expiry"
        / "ticks/UKOIL_cash/v127_b7_3_nonhostile5d_ticks.jsonl"
    )
    june_spec = tick_spec(
        june_path,
        start="2026-06-01T03:05:00.017000+00:00",
        end="2026-06-05T23:49:57.216000+00:00",
        sha="2" * 64,
        rows=282_386,
    )
    april_specs = tuple(
        tick_spec(
            integration_root
            / "timewarp_ftmo_selected_order_ticks_UKOIL_cash_20260607"
            / f"ticks/UKOIL_cash/sel_{index:03d}_ticks.jsonl",
            start=f"2026-04-{day:02d}T04:00:00+00:00",
            end=f"2026-04-{day:02d}T06:00:00+00:00",
            sha=f"{index + 2:x}" * 64,
        )
        for index, day in enumerate((21, 22, 23, 24, 29, 30), start=1)
    )
    mirrored_june = tick_spec(
        integration_root / "mirror/v127_b7_3_nonhostile5d_ticks.jsonl",
        start=june_spec.start_utc or "",
        end=june_spec.end_utc or "",
        sha=str(june_spec.sha256),
        rows=int(june_spec.row_count or 0),
    )
    by_root = {
        active_root: resolved((may_spec, june_spec)),
        integration_root: resolved((*april_specs, mirrored_june)),
    }
    calls: list[Path] = []

    def fake_resolve(symbol, *, repo_root):
        assert symbol == "UKOIL_cash"
        root = Path(repo_root)
        calls.append(root)
        return by_root[root], (f"{root}:outside_window_missing",)

    monkeypatch.setattr(harness, "resolve_ftmo_tick_source", fake_resolve)
    resolver = harness.BroadSourceResolver()
    june_days = tuple(f"2026-06-{day:02d}" for day in range(1, 6))
    april_days = tuple(f"2026-04-{day:02d}" for day in range(21, 31))

    june = resolver.resolve_tick(
        "UKOIL_cash",
        source_authority_days=june_days,
    )
    assert june is not None
    assert [spec.path for spec in june.rows_by_day.specs] == [june_path]
    assert june.spec.row_count == 282_386
    assert june.source_gaps == ()
    assert resolver.resolve_tick(
        "UKOIL_cash",
        source_authority_days=reversed(june_days),
    ) is june

    april = resolver.resolve_tick(
        "UKOIL_cash",
        source_authority_days=april_days,
    )
    assert april is not None
    assert [spec.path for spec in april.rows_by_day.specs] == [
        spec.path for spec in april_specs
    ]
    assert len(april.component_source_labels) == 6
    assert calls == [
        active_root,
        integration_root,
        active_root,
        integration_root,
    ]
    assert set(resolver._tick_cache) == {
        ("UKOIL_cash", june_days),
        ("UKOIL_cash", april_days),
    }

    july_days = ("2026-07-01",)
    assert resolver.resolve_tick(
        "UKOIL_cash",
        source_authority_days=july_days,
    ) is None
    gaps = [
        row
        for row in resolver.drain_source_rows()
        if row.get("row_type") == "tick_symbol_source_gap"
    ]
    assert gaps[-1]["status"] == (
        "no_ftmo_tick_source_overlaps_requested_authority_window"
    )
    assert gaps[-1]["requested_replay_days"] == ["2026-07-01"]
    assert gaps[-1]["live_broker_authority"] is False
    assert gaps[-1]["broker_mutation_enabled"] is False


def test_tick_resolver_fails_closed_on_cross_source_quote_conflict(
    tmp_path: Path,
    monkeypatch,
) -> None:
    harness = load_broad_replay_harness()
    active_root = tmp_path / "active"
    integration_root = tmp_path / "integration"
    active_root.mkdir()
    integration_root.mkdir()
    monkeypatch.setattr(harness, "ROOT", active_root)
    monkeypatch.setattr(harness, "MAIN_REPO_ROOT", integration_root)
    timestamp = "2026-06-04T11:30:00+00:00"
    active_path = active_root / "active_ticks.jsonl"
    integration_path = integration_root / "integration_ticks.jsonl"
    active_path.write_text(
        json.dumps({"time_utc": timestamp, "bid": 98.3, "ask": 98.4}) + "\n",
        encoding="utf-8",
    )
    integration_path.write_text(
        json.dumps({"time_utc": timestamp, "bid": 98.2, "ask": 98.4}) + "\n",
        encoding="utf-8",
    )

    def resolved(path: Path) -> timewarp.ResolvedSource:
        spec = timewarp.SourceSpec(
            symbol="UKOIL_cash",
            mapped_symbol="UKOIL.cash",
            timeframe="TICK",
            path=path,
            source_family="ftmo_mt5_research_export",
            source_broker="FTMO",
            source_role="owner_authorized_path_override",
            start_utc="2026-06-04T11:29:00+00:00",
            end_utc="2026-06-04T11:31:00+00:00",
            row_count=1,
            sha256=timewarp.file_sha256(path),
            source_truth_scope=timewarp.SOURCE_TRUTH_SCOPE,
            not_redacted_account_native=True,
            broker_lifecycle_truth_satisfied=False,
            ordered_tick_truth_satisfied=True,
        )
        return timewarp.ResolvedSource(
            spec=spec,
            rows=(),
            rows_by_day=SimpleNamespace(specs=(spec,)),
            sha256=str(spec.sha256),
            day_counts={},
            selected_status="selected_priority_tick_sources_lazy_window_load",
            min_required_rows_per_day=1,
        )

    by_root = {
        active_root: resolved(active_path),
        integration_root: resolved(integration_path),
    }
    monkeypatch.setattr(
        harness,
        "resolve_ftmo_tick_source",
        lambda symbol, *, repo_root: (by_root[Path(repo_root)], ()),
    )
    resolver = harness.BroadSourceResolver()
    tick = resolver.resolve_tick(
        "UKOIL_cash",
        source_authority_days=("2026-06-04",),
    )
    assert tick is not None
    after = timewarp.parse_utc("2026-06-04T11:29:00+00:00")
    until = timewarp.parse_utc("2026-06-04T11:31:00+00:00")
    assert after is not None
    assert until is not None
    with pytest.raises(
        RuntimeError,
        match="conflicting_overlapping_tick_observations:UKOIL_cash",
    ):
        tick.rows_by_day.query(after=after, until=until)


def test_source_ledger_deduplication_preserves_distinct_authority_scopes() -> None:
    harness = load_broad_replay_harness()
    resolver = harness.BroadSourceResolver(skip_tick_source=True)
    base = {
        "row_type": "source_selection",
        "symbol": "XAUUSD",
        "timeframe": "M15",
        "source_path": "/tmp/XAUUSD_M15.csv",
    }

    resolver.emit_source_row({**base, "source_authority_scope_id": "scope-a"})
    resolver.emit_source_row({**base, "source_authority_scope_id": "scope-a"})
    resolver.emit_source_row({**base, "source_authority_scope_id": "scope-b"})

    rows = resolver.drain_source_rows()
    assert [row["source_authority_scope_id"] for row in rows] == [
        "scope-a",
        "scope-b",
    ]


def test_failed_summary_from_partial_is_explicit_non_final_tombstone(
    tmp_path: Path,
    monkeypatch,
) -> None:
    harness = load_broad_replay_harness()
    monkeypatch.setattr(harness, "ROUTE", tmp_path)
    prefix = "UNIT_FAILED_PARTIAL"
    outputs = harness.output_paths(prefix)
    outputs["partial_summary"].write_text(
        json.dumps(
            {
                "output_prefix": prefix,
                "profiles_requested": [harness.PROFILE_REPAIRED],
                "ledger_write_row_counts_so_far": {
                    "source": 4,
                    "candidate": 12,
                    "scorecard": 3,
                    "order": 0,
                    "trade": 0,
                    "oracle": 0,
                    "missed": 12,
                    "bucket": 2,
                    "packet_sidecar": 15,
                },
            }
        ),
        encoding="utf-8",
    )

    failure = ValueError("current_summary_v2_unit_failure")
    summary = harness.failed_summary_from_partial(
        prefix,
        failure_stage="final_current_summary_v2_certification",
        failure=failure,
    )

    assert summary["status"] == "failed_partial_not_final_proof"
    assert summary["failed_run"] is True
    assert summary["interrupted_run"] is False
    assert summary["failure_type"] == "ValueError"
    assert summary["failure_message"] == "current_summary_v2_unit_failure"
    assert summary["source_universe_rows"] == 4
    assert summary["candidate_rows"] == 12
    assert summary["candidate_rows_written"] == 12
    assert summary["scorecard_rows"] == 3
    assert summary["order_rows"] == 0
    assert summary["trade_rows"] == 0
    assert summary["oracle_rows"] == 0
    assert summary["missed_opportunity_rows"] == 12
    assert summary["bucket_rows"] == 2
    assert summary["packet_sidecar_rows"] == 15
    assert summary["comparison_ledger_rows"] == 0
    assert summary["terminal_execution_materialized"] is False
    assert summary["terminal_execution_materialization_status"] == (
        "partial_candidate_replay_no_terminal_execution_materialized"
    )
    assert summary["live_broker_authority"] is False
    assert summary["broker_mutation_enabled"] is False
    assert summary["final_selection_claim"] is False
    assert json.loads(outputs["summary"].read_text(encoding="utf-8")) == summary


def test_finalize_existing_completed_run_requires_exact_flushed_checkpoint(
    tmp_path: Path,
    monkeypatch,
) -> None:
    harness = load_broad_replay_harness()
    monkeypatch.setattr(harness, "ROUTE", tmp_path)
    prefix = "UNIT_RECOVER_COMPLETED"
    outputs = harness.output_paths(prefix)
    ledger_keys = (
        "source",
        "decision",
        "candidate",
        "scorecard",
        "order",
        "trade",
        "oracle",
        "missed",
        "bucket",
        "packet_sidecar",
    )
    for key in ledger_keys:
        outputs[key].write_text("", encoding="utf-8")
    outputs["partial_summary"].write_text(
        json.dumps(
            {
                "schema": (
                    "gtos.final_moonshot.broad_live_as_if_replay_harness."
                    "partial_summary.v1"
                ),
                "status": "partial_in_progress_not_final_proof",
                "output_prefix": prefix,
                "profiles_requested": [harness.PROFILE_RAW],
                "progress_rows": [
                    {
                        "profile": harness.PROFILE_RAW,
                        "split": "holdout",
                        "start_day": "2026-05-13",
                        "end_day": "2026-05-13",
                    }
                ],
                "ledger_write_row_counts_so_far": {
                    key: 0 for key in ledger_keys
                },
                "ledger_file_bytes_flushed_before_partial_summary": {
                    key: 0 for key in ledger_keys
                },
                "split_profile_stats": [],
                "comparison_rows": [],
                "candidate_ledger_omitted": False,
                "candidate_index_ledger_omitted": False,
                "missed_ledger_compacted": True,
                "packet_sidecar_ledger_omitted": False,
                "live_broker_authority": False,
                "broker_mutation_enabled": False,
                "final_selection_claim": False,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    outputs["summary"].write_text(
        json.dumps(
            {
                "status": "failed_partial_not_final_proof",
                "failure_stage": "final_current_summary_v2_certification",
                "failure_message": "unit_historical_contract_failure",
            }
        ),
        encoding="utf-8",
    )
    args = SimpleNamespace(
        output_prefix=prefix,
        profiles=(harness.PROFILE_RAW,),
        start="2026-05-13",
        end="2026-05-13",
        max_days=None,
        smoke_subset=False,
        symbols=None,
        gc_between_chunks=False,
    )

    summary = harness.finalize_existing_completed_run(args)

    assert summary["schema"] == harness.BROAD_REPLAY_CURRENT_SUMMARY_SCHEMA
    assert summary["status"] == (
        "broad_live_as_if_replay_zero_candidates_no_terminal_execution_"
        "broker_live_closed"
    )
    assert summary["recovered_completed_run"] is True
    assert summary["selected_day_count"] == 1
    assert summary["live_broker_authority"] is False
    assert summary["final_selection_claim"] is False
    assert Path(summary["recovery_source_summary_backup_path"]).exists()
    assert summary["completed_run_flushed_ledger_integrity"]["valid"] is True
    assert outputs["comparison"].exists()
    assert json.loads(outputs["summary"].read_text(encoding="utf-8")) == summary


def test_finalize_existing_completed_run_recovers_summaryless_external_interruption(
    tmp_path: Path,
    monkeypatch,
) -> None:
    harness = load_broad_replay_harness()
    monkeypatch.setattr(harness, "ROUTE", tmp_path)
    prefix = "UNIT_RECOVER_SUMMARYLESS_COMPLETED"
    outputs = harness.output_paths(prefix)
    ledger_keys = (
        "source",
        "decision",
        "candidate",
        "candidate_index",
        "scorecard",
        "order",
        "trade",
        "oracle",
        "missed",
        "bucket",
        "packet_sidecar",
    )
    for key in ledger_keys:
        outputs[key].write_text("", encoding="utf-8")
    outputs["partial_summary"].write_text(
        json.dumps(
            {
                "schema": (
                    "gtos.final_moonshot.broad_live_as_if_replay_harness."
                    "partial_summary.v1"
                ),
                "status": "partial_in_progress_not_final_proof",
                "partial_summary_semantics": (
                    "salvage_checkpoint_with_completed_capacity_cleanup_only_"
                    "final_summary_required_for_completed_run"
                ),
                "output_prefix": prefix,
                "profiles_requested": [harness.PROFILE_RAW],
                "progress_rows": [
                    {
                        "profile": harness.PROFILE_RAW,
                        "split": "holdout",
                        "start_day": "2026-05-13",
                        "end_day": "2026-05-13",
                    }
                ],
                "ledger_write_row_counts_so_far": {
                    key: 0 for key in ledger_keys
                },
                "ledger_file_bytes_flushed_before_partial_summary": {
                    key: 0 for key in ledger_keys
                },
                "capacity_safe_chunk_execution_required": True,
                "capacity_safe_chunk_execution_contract": {
                    "valid": True,
                    "status": "complete_capacity_safe_chunk_execution",
                    "planned_chunk_count": 1,
                    "completed_chunk_count": 1,
                },
                "source_authority_chunk_invariance_required": True,
                "source_authority_chunk_invariance_contract": {
                    "valid": True,
                    "status": "complete_source_authority_chunk_invariance",
                    "planned_chunk_count": 1,
                    "completed_chunk_count": 1,
                    "current_chunk_pending": False,
                },
                "split_profile_stats": [],
                "comparison_rows": [],
                "candidate_ledger_omitted": False,
                "candidate_index_ledger_omitted": False,
                "missed_ledger_compacted": True,
                "packet_sidecar_ledger_omitted": False,
                "live_broker_authority": False,
                "broker_mutation_enabled": False,
                "final_selection_claim": False,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    args = SimpleNamespace(
        output_prefix=prefix,
        profiles=(harness.PROFILE_RAW,),
        start="2026-05-13",
        end="2026-05-13",
        max_days=None,
        smoke_subset=False,
        symbols=None,
        skip_tick_source=False,
        max_candidates_per_symbol_window=0,
        gc_between_chunks=False,
    )

    summary = harness.finalize_existing_completed_run(args)

    assert summary["schema"] == harness.BROAD_REPLAY_CURRENT_SUMMARY_SCHEMA
    assert summary["recovered_completed_run"] is True
    assert summary["recovery_source_status"] == (
        "summary_missing_after_external_interruption"
    )
    assert summary["recovery_source_summary_present"] is False
    assert summary["recovery_source_summary_backup_path"] is None
    assert summary["completed_run_flushed_ledger_integrity"]["valid"] is True
    assert outputs["comparison"].exists()
    assert outputs["comparison"].stat().st_size == 0


def test_completed_summary_can_be_reconciled_from_fully_flushed_checkpoint(
    tmp_path: Path,
    monkeypatch,
) -> None:
    harness = load_broad_replay_harness()
    monkeypatch.setattr(harness, "ROUTE", tmp_path)
    prefix = "UNIT_COMPLETED_SUMMARY_RECONCILIATION"
    outputs = harness.output_paths(prefix)
    completed_summary = {
        "status": "broad_live_as_if_replay_materialized_broker_live_closed",
        "split_profile_stats": [],
    }
    outputs["summary"].write_text(
        json.dumps(completed_summary, sort_keys=True), encoding="utf-8"
    )
    partial = {
        "status": "partial_in_progress_not_final_proof",
        "partial_summary_semantics": (
            "salvage_checkpoint_with_completed_capacity_cleanup_only_"
            "final_summary_required_for_completed_run"
        ),
        "output_prefix": prefix,
        "progress_rows": [{}],
        "capacity_safe_chunk_execution_contract": {
            "valid": True,
            "status": "complete_capacity_safe_chunk_execution",
            "planned_chunk_count": 1,
            "completed_chunk_count": 1,
        },
        "source_authority_chunk_invariance_contract": {
            "valid": True,
            "status": "complete_source_authority_chunk_invariance",
            "planned_chunk_count": 1,
            "completed_chunk_count": 1,
            "current_chunk_pending": False,
        },
    }

    recovery, backup = harness.existing_completed_run_recovery_source(
        outputs, partial
    )

    assert recovery == completed_summary
    assert backup == tmp_path / (
        f"{prefix}_PRE_PHYSICAL_SUMMARY_PARITY_RECONCILIATION_SUMMARY.json"
    )


def test_completed_run_flushed_ledger_integrity_rejects_row_count_mismatch(
    tmp_path: Path,
    monkeypatch,
) -> None:
    harness = load_broad_replay_harness()
    monkeypatch.setattr(harness, "ROUTE", tmp_path)
    outputs = harness.output_paths("UNIT_FLUSHED_INTEGRITY")
    row_bytes = b'{"row_type":"source_selection"}\n'
    outputs["source"].write_bytes(row_bytes)

    contract = harness.completed_run_flushed_ledger_integrity_contract(
        outputs,
        {
            "ledger_write_row_counts_so_far": {"source": 2},
            "ledger_file_bytes_flushed_before_partial_summary": {
                "source": len(row_bytes)
            },
        },
    )

    assert contract["valid"] is False
    assert contract["status"] == "flushed_ledger_integrity_failed"
    assert any(
        failure.startswith("source:integrity_mismatch")
        for failure in contract["failures"]
    )


def test_flow_analyzer_can_stream_local_jsonl_without_duplicate_cache(
    tmp_path: Path,
    monkeypatch,
) -> None:
    flow = load_broad_replay_flow_analyzer()
    source = tmp_path / "large.jsonl"
    source.write_text('{"row":1}\n', encoding="utf-8")
    cache = tmp_path / "cache"
    monkeypatch.setattr(flow, "JSONL_LOCAL_CACHE_ENABLED", False)
    monkeypatch.setattr(flow, "JSONL_LOCAL_CACHE_DIR", cache)

    assert flow.local_cached_jsonl_path(source) == source
    assert not cache.exists()


def test_current_summary_v2_certifies_complete_single_immutable_envelope() -> None:
    harness = load_broad_replay_harness()
    row = _current_summary_complete_authority_row()

    contract = harness.current_summary_v2_contract_for_rows(
        [("scorecard:1", row)]
    )

    payload = row["package_new_entry_authority_payload"]
    digest = scheduler.package_new_entry_authority_payload_hash_sha256(payload)
    assert row["package_new_entry_authority_hash_sha256"] == digest
    assert row["expected_package_new_entry_authority_hash_sha256"] == digest
    assert contract == {
        "schema": harness.BROAD_REPLAY_CURRENT_SUMMARY_SCHEMA,
        "package_new_entry_authority_payload_contract": (
            scheduler.PACKAGE_NEW_ENTRY_AUTHORITY_IMMUTABLE_PAYLOAD_CONTRACT
        ),
        "package_new_entry_authority_payload_required_for_signed_executable_rows": True,
    }


def test_current_summary_v2_rejects_incomplete_hash_only_and_mixed_authority(
    tmp_path: Path,
) -> None:
    harness = load_broad_replay_harness()

    incomplete = _current_summary_complete_authority_row()
    incomplete_payload = incomplete["package_new_entry_authority_payload"]
    incomplete_payload.pop("authority_source")
    incomplete_digest = scheduler.package_new_entry_authority_payload_hash_sha256(
        incomplete_payload
    )
    incomplete["package_new_entry_authority_hash_sha256"] = incomplete_digest
    incomplete["expected_package_new_entry_authority_hash_sha256"] = (
        incomplete_digest
    )

    hash_only = _current_summary_complete_authority_row()
    hash_only.pop("package_new_entry_authority_payload")

    mixed = _current_summary_complete_authority_row()
    authority_field = mixed["package_new_entry_authority_authority_field"]
    mixed_surface = {
        key: copy.deepcopy(value)
        for key, value in mixed.items()
        if key.startswith("package_new_entry_authority_")
    }
    mixed_payload = mixed_surface["package_new_entry_authority_payload"]
    mixed_payload["expected_net_r"] = 0.55
    mixed_surface["package_new_entry_authority_expected_net_r"] = 0.55
    mixed_digest = scheduler.package_new_entry_authority_payload_hash_sha256(
        mixed_payload
    )
    mixed_surface["package_new_entry_authority_hash_sha256"] = mixed_digest
    mixed_surface["expected_package_new_entry_authority_hash_sha256"] = mixed_digest
    mixed[authority_field] = mixed_surface

    cases = (
        ("incomplete", incomplete, "payload_atom_missing:source:authority_source"),
        ("hash_only", hash_only, "package_new_entry_authority_payload_missing"),
        ("mixed", mixed, "conflicting_current_authority_envelopes"),
    )
    for case, row, expected_reason in cases:
        scorecard_path = tmp_path / f"{case}_SCORECARD_LEDGER.jsonl"
        scorecard_path.write_text(
            json.dumps(row, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        with pytest.raises(ValueError) as exc_info:
            harness.current_summary_v2_contract_for_outputs(
                {"scorecard": scorecard_path}
            )
        message = str(exc_info.value)
        assert "current_summary_v2_authority_certification_failed" in message
        assert expected_reason in message


def test_current_summary_v2_accepts_non_executable_diagnostic_candidate_risk_metadata() -> None:
    harness = load_broad_replay_harness()
    row = _current_summary_diagnostic_candidate_row()

    contract = harness.current_summary_v2_contract_for_rows(
        [("candidate:1", row)]
    )

    assert all(
        row[alias] is False
        for alias in CURRENT_SUMMARY_EXECUTABLE_AUTHORITY_ALIASES
    )
    assert "package_new_entry_authority_payload" not in row
    assert "package_new_entry_authority_hash_sha256" not in row
    assert "simulated_order_id" not in row
    assert "simulated_trade_id" not in row
    assert contract["schema"] == harness.BROAD_REPLAY_CURRENT_SUMMARY_SCHEMA


def test_scheduler_authority_projection_does_not_invent_missing_payload_failure_for_nonrequired_state() -> None:
    harness = load_broad_replay_harness()
    row = {
        "selector_action": "trade",
        "scheduler_materialization_selector_action": "trade",
        "package_new_entry_authority_required": False,
        "package_new_entry_authority_valid": False,
        "package_new_entry_authority_status": (
            "not_required_for_selector_action_or_action_intent"
        ),
        "package_new_entry_authority_failures": [],
    }

    harness.promote_scheduler_authority_and_selector(row)

    assert row["package_new_entry_authority_required"] is False
    assert row["package_new_entry_authority_valid"] is False
    assert row["package_new_entry_authority_status"] == (
        "not_required_for_selector_action_or_action_intent"
    )
    assert row.get("package_new_entry_authority_projection_failures", []) == []


@pytest.mark.parametrize(
    ("claim_field", "claim_value"),
    (
        ("package_new_entry_authority_payload", {"diagnostic": True}),
        ("package_new_entry_authority_hash_sha256", "a" * 64),
        ("expected_package_new_entry_authority_hash_sha256", "a" * 64),
    ),
)
def test_current_summary_v2_rejects_nonrequired_immutable_authority_claim(
    claim_field: str,
    claim_value: object,
) -> None:
    harness = load_broad_replay_harness()
    row = _current_summary_diagnostic_candidate_row()
    row.update(
        {
            "package_new_entry_authority_required": False,
            "package_new_entry_authority_valid": False,
            "package_new_entry_authority_status": (
                "not_required_for_selector_action_or_action_intent"
            ),
            claim_field: claim_value,
        }
    )

    with pytest.raises(ValueError) as exc_info:
        harness.current_summary_v2_contract_for_rows([("candidate:1", row)])

    message = str(exc_info.value)
    assert "current_summary_v2_nonrequired_authority_payload_claim" in message
    assert claim_field in message


def test_current_summary_v2_rejects_legacy_nonrequired_hash_diagnostic() -> None:
    harness = load_broad_replay_harness()
    row = _current_summary_diagnostic_candidate_row(legacy_hash_only=True)

    with pytest.raises(ValueError) as exc_info:
        harness.current_summary_v2_contract_for_rows([("candidate:1", row)])

    assert "current_summary_v2_nonrequired_authority_payload_claim" in str(
        exc_info.value
    )


def test_current_summary_v2_uses_admission_action_before_risk_expression() -> None:
    harness = load_broad_replay_harness()
    row = _current_summary_diagnostic_candidate_row()
    row.update(
        {
            "selector_action": "trade",
            "raw_selector_action": "trade",
            "materialized_selector_action": "trade",
            "effective_selector_action_before_risk_expression": "trade",
            "effective_selector_action": "reduce-risk",
            "risk_decision": "reduce-risk",
            "package_new_entry_authority_required": False,
            "package_new_entry_authority_valid": False,
            "package_new_entry_authority_status": (
                "not_required_for_selector_action_or_action_intent"
            ),
            "package_new_entry_authority_failures": [],
            "package_replay_candidate_use_allowed": True,
            "package_replay_executable_candidate_use_allowed": True,
            "package_replay_order_executable_candidate_use_allowed": True,
            "replay_candidate_use_allowed_now": True,
            "ultimate_package_effective_executable_authority_allowed": True,
            "risk_finalizer_executable_finalized": True,
            "package_replay_order_executable_transfer_status": "trade_bound",
            "simulated_trade_id": "trade-admission-before-risk-expression",
        }
    )

    contract = harness.current_summary_v2_contract_for_rows(
        [("trade:1", row)]
    )

    assert contract["schema"] == harness.BROAD_REPLAY_CURRENT_SUMMARY_SCHEMA


def test_current_summary_v2_keeps_proxy_terminal_r_separate_from_final_live_claim() -> None:
    harness = load_broad_replay_harness()
    row = _current_summary_diagnostic_candidate_row()
    row.update(
        {
            "selector_action": "trade",
            "raw_selector_action": "trade",
            "scheduler_materialization_selector_action": "trade",
            "effective_selector_action": "reduce-risk",
            "risk_decision": "reduce-risk",
            "package_new_entry_authority_required": False,
            "package_new_entry_authority_valid": False,
            "package_new_entry_authority_status": (
                "not_required_for_selector_action_or_action_intent"
            ),
            "package_new_entry_authority_failures": [],
            "package_replay_candidate_use_allowed": True,
            "package_replay_executable_candidate_use_allowed": True,
            "package_replay_order_executable_candidate_use_allowed": True,
            "replay_candidate_use_allowed_now": True,
            "ultimate_package_effective_executable_authority_allowed": True,
            "risk_finalizer_executable_finalized": True,
            "package_replay_order_executable_transfer_status": "trade_bound",
            "simulated_trade_id": "proxy-terminal-r-local-replay",
            "terminal_r_authority_status": (
                "terminal_r_source_gap_not_final_live_proof"
            ),
            "terminal_r_path_authority": (
                "terminal_r_source_gap_not_final_live_proof"
            ),
            "headline_result_authority_status": "not_headline_final_r_authority",
            "terminal_r_ordered_tick_final_live_authority": False,
            "ordered_tick_final_r_authority": False,
            "headline_result_authority": False,
            "final_r_authority": False,
            "live_broker_authority": False,
            "broker_mutation_enabled": False,
            "final_selection_claim": False,
        }
    )

    contract = harness.current_summary_v2_contract_for_rows([("trade:1", row)])
    assert contract["schema"] == harness.BROAD_REPLAY_CURRENT_SUMMARY_SCHEMA

    row["final_selection_claim"] = True
    with pytest.raises(ValueError) as exc_info:
        harness.current_summary_v2_contract_for_rows([("trade:1", row)])
    assert "current_summary_v2_terminal_r_final_live_claim" in str(exc_info.value)


def test_current_summary_v2_accepts_blocked_status_without_executable_claim() -> None:
    harness = load_broad_replay_harness()
    row = _current_summary_diagnostic_candidate_row()
    row["package_replay_order_executable_transfer_status"] = "final_blocked"

    contract = harness.current_summary_v2_contract_for_rows(
        [("candidate:1", row)]
    )

    assert contract["schema"] == harness.BROAD_REPLAY_CURRENT_SUMMARY_SCHEMA


def test_current_summary_v2_accepts_final_blocked_candidate_with_signed_proposal() -> None:
    harness = load_broad_replay_harness()
    row = _current_summary_complete_authority_row()
    row["package_replay_order_executable_transfer_status"] = "final_blocked"
    row["package_replay_order_executable_final_blocker_reason"] = (
        "off_configured_session_requires_explicit_off_session_authority"
    )
    row["package_replay_order_executable_final_blocker_source"] = (
        "scheduler_package_fill_floor_authority"
    )
    row["scheduler_candidate_decision_inputs"] = {
        "package_replay_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed": True,
        "package_replay_order_executable_candidate_use_allowed": True,
        "package_replay_order_executable_candidate_use_allowed_reason": (
            "unit_test_signed_pre_finalization_order_proposal"
        ),
        "package_replay_order_executable_authority_source": (
            "unit_test_scheduler_candidate_decision_inputs"
        ),
    }

    normalized = timewarp.normalize_package_new_entry_authority_ledger_row(row)
    contract = harness.current_summary_v2_contract_for_rows(
        [("candidate:1", normalized)]
    )

    assert normalized["package_new_entry_authority_valid"] is True
    assert all(
        normalized[alias] is False
        for alias in CURRENT_SUMMARY_EXECUTABLE_AUTHORITY_ALIASES
    )
    assert normalized[
        "package_replay_order_executable_candidate_use_allowed_pre_finalization"
    ] is True
    assert all(
        normalized["scheduler_candidate_decision_inputs"][alias] is False
        for alias in CURRENT_SUMMARY_EXECUTABLE_AUTHORITY_ALIASES
        if alias in normalized["scheduler_candidate_decision_inputs"]
    )
    assert normalized["scheduler_candidate_decision_inputs"][
        "package_replay_order_executable_candidate_use_allowed_pre_finalization"
    ] is True
    assert contract["schema"] == harness.BROAD_REPLAY_CURRENT_SUMMARY_SCHEMA


def test_current_summary_v2_accepts_terminal_zero_trade_with_distinct_namespaced_proposals() -> None:
    harness = load_broad_replay_harness()
    scorecard_authority = _current_summary_complete_authority_row(
        candidate_id="scorecard-proposal"
    )
    finalizer_authority = _current_summary_complete_authority_row(
        candidate_id="finalizer-proposal"
    )
    row = _current_summary_terminal_zero_trade_with_namespaced_authorities(
        ("scorecard_reported_", scorecard_authority),
        ("finalizer_primary_probe_", finalizer_authority),
    )

    contract = harness.current_summary_v2_contract_for_rows(
        [("scorecard:134", row)]
    )

    assert contract["schema"] == harness.BROAD_REPLAY_CURRENT_SUMMARY_SCHEMA


def test_current_summary_v2_rejects_tampered_namespaced_signed_proposal() -> None:
    harness = load_broad_replay_harness()
    authority = _current_summary_complete_authority_row(
        candidate_id="tampered-scorecard-proposal"
    )
    row = _current_summary_terminal_zero_trade_with_namespaced_authorities(
        ("scorecard_reported_", authority),
    )
    row[
        "scorecard_reported_package_new_entry_authority_payload"
    ]["expected_net_r"] = 9.0

    with pytest.raises(ValueError) as exc_info:
        harness.current_summary_v2_contract_for_rows([("scorecard:1", row)])

    message = str(exc_info.value)
    assert "current_summary_v2_namespaced_authority_certification_failed" in message
    assert "package_new_entry_authority_payload_hash_mismatch" in message


def test_current_summary_v2_rejects_same_instance_namespaced_hash_conflict() -> None:
    harness = load_broad_replay_harness()
    first = _current_summary_complete_authority_row(
        candidate_id="same-instance-proposal"
    )
    second = copy.deepcopy(first)
    second_payload = second["package_new_entry_authority_payload"]
    second_payload["expected_net_r"] = 0.9
    second["package_new_entry_authority_expected_net_r"] = 0.9
    second_digest = scheduler.package_new_entry_authority_payload_hash_sha256(
        second_payload
    )
    second["package_new_entry_authority_hash_sha256"] = second_digest
    second["expected_package_new_entry_authority_hash_sha256"] = second_digest
    row = _current_summary_terminal_zero_trade_with_namespaced_authorities(
        ("scorecard_reported_", first),
        ("risk_finalizer_best_package_probe_", second),
    )

    with pytest.raises(ValueError) as exc_info:
        harness.current_summary_v2_contract_for_rows([("scorecard:1", row)])

    assert (
        "conflicting_flat_namespace_authority_envelopes_same_candidate_instance"
        in str(exc_info.value)
    )


def test_current_summary_v2_namespaced_proposal_does_not_cover_terminal_executable_claim() -> None:
    harness = load_broad_replay_harness()
    authority = _current_summary_complete_authority_row(
        candidate_id="diagnostic-proposal-only"
    )
    row = _current_summary_terminal_zero_trade_with_namespaced_authorities(
        ("risk_finalizer_best_package_probe_", authority),
    )
    row["package_replay_order_executable_candidate_use_allowed"] = True

    with pytest.raises(ValueError) as exc_info:
        harness.current_summary_v2_contract_for_rows([("scorecard:1", row)])

    message = str(exc_info.value)
    assert "current_summary_v2_blocked_executable_claim" in message


def test_current_summary_v2_rejects_blocked_status_with_executable_claim() -> None:
    harness = load_broad_replay_harness()
    row = _current_summary_complete_authority_row()
    row["package_replay_order_executable_transfer_status"] = "final_blocked"

    with pytest.raises(ValueError) as exc_info:
        harness.current_summary_v2_contract_for_rows([("scorecard:1", row)])

    message = str(exc_info.value)
    assert "current_summary_v2_blocked_executable_claim" in message
    assert "blocked_status_executable_claim" in message


@pytest.mark.parametrize(
    "executable_alias",
    CURRENT_SUMMARY_EXECUTABLE_AUTHORITY_ALIASES,
)
def test_current_summary_v2_rejects_diagnostic_candidate_when_any_executable_alias_is_true(
    executable_alias: str,
) -> None:
    harness = load_broad_replay_harness()
    row = _current_summary_diagnostic_candidate_row()
    row[executable_alias] = True

    with pytest.raises(ValueError) as exc_info:
        harness.current_summary_v2_contract_for_rows([("candidate:1", row)])

    message = str(exc_info.value)
    assert "current_summary_v2_authority_certification_failed" in message
    assert "authority_envelope_missing" in message


@pytest.mark.parametrize(
    ("identity_field", "identity"),
    (
        ("simulated_order_id", "order-current-summary-diagnostic"),
        ("simulated_trade_id", "trade-current-summary-diagnostic"),
    ),
)
def test_current_summary_v2_rejects_diagnostic_candidate_with_order_or_trade_identity(
    identity_field: str,
    identity: str,
) -> None:
    harness = load_broad_replay_harness()
    row = _current_summary_diagnostic_candidate_row()
    row[identity_field] = identity

    with pytest.raises(ValueError) as exc_info:
        harness.current_summary_v2_contract_for_rows([("candidate:1", row)])

    message = str(exc_info.value)
    assert "current_summary_v2_authority_certification_failed" in message
    assert "authority_envelope_missing" in message


def test_current_summary_v2_rejects_provisional_marker_on_diagnostic_candidate() -> None:
    harness = load_broad_replay_harness()
    verifier = harness._current_summary_verifier_module()
    marker = verifier.PACKAGE_NEW_ENTRY_AUTHORITY_PROVISIONAL_MARKER
    row = _current_summary_diagnostic_candidate_row()
    row[marker] = False

    with pytest.raises(ValueError) as exc_info:
        harness.current_summary_v2_contract_for_rows([("candidate:1", row)])

    message = str(exc_info.value)
    assert "current_summary_v2_provisional_authority_marker_leak" in message
    assert f"root.{marker}" in message


@pytest.mark.parametrize(
    ("ledger_name", "identity_fields"),
    (
        ("scorecard", {}),
        (
            "order",
            {
                "simulated_order_id": "order-current-summary-strict",
                "order_status": "pending_accepted",
            },
        ),
        (
            "trade",
            {"simulated_trade_id": "trade-current-summary-strict"},
        ),
    ),
)
def test_current_summary_v2_keeps_downstream_signed_envelope_strict(
    ledger_name: str,
    identity_fields: dict,
) -> None:
    harness = load_broad_replay_harness()
    signed = _current_summary_complete_authority_row()
    signed.update(identity_fields)

    harness.current_summary_v2_contract_for_rows(
        [(f"{ledger_name}:1", signed)]
    )

    hash_only = copy.deepcopy(signed)
    hash_only.pop("package_new_entry_authority_payload")
    with pytest.raises(ValueError) as exc_info:
        harness.current_summary_v2_contract_for_rows(
            [(f"{ledger_name}:1", hash_only)]
        )

    message = str(exc_info.value)
    assert "current_summary_v2_authority_certification_failed" in message
    assert "package_new_entry_authority_payload_missing" in message


def assert_package_rank_boost_replay_authority_enabled(runtime: dict) -> None:
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_ultimate_package_rank_boost_enabled"
        ]
        is True
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_ultimate_package_rank_score_weight"
        ]
        == 0.65
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_ultimate_package_rank_source_r_weight"
        ]
        == 0.35
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_ultimate_package_rank_admission_weight"
        ]
        == 0.20
    )
    assert (
        runtime["scheduler_v4_best_trade_allocator_ultimate_package_rank_max_boost"]
        == 2.50
    )
    assert (
        "enabled_for_local_replay_authority"
        in runtime[
            "scheduler_v4_best_trade_allocator_ultimate_package_rank_boost_status"
        ]
    )


def assert_package_rank_boost_diagnostic_only(runtime: dict) -> None:
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_ultimate_package_rank_boost_enabled"
        ]
        is False
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_ultimate_package_rank_score_weight"
        ]
        == 0.0
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_ultimate_package_rank_source_r_weight"
        ]
        == 0.0
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_ultimate_package_rank_admission_weight"
        ]
        == 0.0
    )
    assert (
        runtime["scheduler_v4_best_trade_allocator_ultimate_package_rank_max_boost"]
        == 0.0
    )
    assert (
        "disabled_until_final_package_selected_false"
        in runtime[
            "scheduler_v4_best_trade_allocator_ultimate_package_rank_boost_demotion_reason"
        ]
    )


def _package_exec_aliases() -> dict:
    return {
        "decision_time_utc": "2026-05-05T08:15:00+00:00",
        "source_bound_package_candidate_use_allowed": True,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "ultimate_package_admission_candidate_use_allowed": True,
        "ultimate_package_effective_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_admission_count": 1,
        "package_replay_source_bound_candidate_use_allowed": True,
        "package_replay_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed_reason": (
            "broker_cost_selector_and_scheduler_action_executable"
        ),
        "replay_candidate_use_allowed_now": True,
        "replay_candidate_use_allowed_now_reason": (
            "broker_cost_selector_and_scheduler_action_executable"
        ),
        "selected_package_candidate_use_allowed_status": (
            "broker_cost_selector_and_scheduler_action_executable"
        ),
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "candidate_cost_r_fallback_is_authority": False,
        "expected_net_r": 0.91,
        "candidate_expected_net_r": 0.91,
        "probability": 0.75,
        "candidate_probability": 0.75,
        "fill_probability": 0.82,
        "candidate_fill_probability": 0.82,
        "predecision_limit_fillability_probability": 0.82,
        "limit_fillability_probability": 0.82,
        "execution_fill_probability": 0.82,
        "execution_fill_probability_source": (
            "unit_test.predecision_limit_fillability_probability"
        ),
        "execution_fill_probability_source_time_utc": (
            "2025-01-01T00:00:00+00:00"
        ),
        "execution_fill_probability_source_boundary": (
            "asof_candidate_fields_only_no_postdecision_path"
        ),
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "unit_test.predecision.expected_net_r",
            "probability": "unit_test.predecision.probability",
            "fill_probability": "unit_test.predecision_limit_fillability.fill_probability",
            "source_completeness": "unit_test.predecision.source_completeness",
        },
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
    }


def _execution_fillability_fields(fill_probability: float) -> dict:
    return {
        "predecision_limit_fillability_probability": fill_probability,
        "limit_fillability_probability": fill_probability,
        "execution_fill_probability": fill_probability,
        "execution_fill_probability_source": (
            "unit_test.predecision_limit_fillability_probability"
        ),
        "execution_fill_probability_source_time_utc": (
            "2025-01-01T00:00:00+00:00"
        ),
        "execution_fill_probability_source_boundary": (
            "asof_candidate_fields_only_no_postdecision_path"
        ),
    }


def test_selected_bridge_soft_scheduler_transfer_skip_produces_order_exec_authority() -> None:
    bridge = load_selected_package_replay_bridge()
    candidate = _signed_bridge_router_refusal_row(
        "source_bound_router_refusal_open_reduced_materialized_for_replay",
        matched_member_axis_id="member_axis:soft-transfer",
    )
    candidate.update(
        {
            "symbol": "XAUUSD",
            "side": "LONG",
            "framework": "fw",
            "origin_family": "origin",
            "session_bucket": "london",
            "source_bound_package_candidate_use_allowed": True,
            "package_replay_source_bound_candidate_use_allowed": True,
            "pretrade_cost_packet_status": "PASSED",
            "cost_authority": "broker_calibrated_replay_cost",
            "cost_source_gap_status": "source_bound_cost_authority_present",
            "source_gap_cost_fallback_blocked": False,
            "candidate_cost_r_fallback_is_authority": False,
            "entry_price": 2400.0,
            "stop_loss": 2390.0,
            "take_profit_1": 2420.0,
            "risk_reward_ratio": 2.0,
            "scheduler_materialization_skip_reason": (
                "candidate_generated_not_scheduler_selected"
            ),
            "package_replay_order_executable_final_blocker_class": (
                "scheduler_selection"
            ),
            "scheduler_terminal_vs_soft_guard": {
                "schema_version": "scheduler_reallocation_terminal_vs_soft_guard_v1",
                "soft_guard_vetoes": ["not_scheduler_selected"],
                "terminal_vetoes": [],
                "pool_eligible": True,
                "pool_status": "eligible",
            },
            "reallocation_soft_guard_vetoes": ["not_scheduler_selected"],
            "reallocation_soft_guard_pool_eligible": True,
            "reallocation_soft_guard_pool_status": "eligible",
            "terminal_vetoes": [],
        }
    )
    member = {
        "source_axis_row_index": 7,
        "stable_member_axis_id": "member_axis:soft-transfer",
        "sleeve_id": "sleeve-soft-transfer",
        "framework": "fw",
        "origin_family": "origin",
        "symbol": "XAUUSD",
        "side": "LONG",
        "session_bucket": "london",
        "sleeve_type": "scheduler_lifecycle_core",
    }

    fields = bridge.selected_package_bridge_quality_fields(
        candidate,
        matched_stable_member_axis_ids=["member_axis:soft-transfer"],
        matched_members=[member],
    )

    assert fields["package_replay_executable_candidate_use_allowed"] is True
    assert fields["package_replay_order_executable_candidate_use_allowed"] is True
    assert fields["package_replay_order_executable_candidate_use_allowed_reason"] == (
        "broker_cost_selector_and_scheduler_action_executable"
    )
    assert fields["package_replay_order_executable_authority_source"] == (
        "selected_package_bridge_package_authority_bridge_fields"
    )

    ambiguous_soft_string = dict(candidate)
    for key in (
        "scheduler_terminal_vs_soft_guard",
        "reallocation_soft_guard_vetoes",
        "reallocation_soft_guard_pool_eligible",
        "reallocation_soft_guard_pool_status",
        "terminal_vetoes",
        "package_replay_order_executable_final_blocker_class",
    ):
        ambiguous_soft_string.pop(key, None)
    ambiguous_fields = bridge.selected_package_bridge_quality_fields(
        ambiguous_soft_string,
        matched_stable_member_axis_ids=["member_axis:soft-transfer"],
        matched_members=[member],
    )
    assert ambiguous_fields["package_replay_executable_candidate_use_allowed"] is False
    assert ambiguous_fields["package_replay_order_executable_candidate_use_allowed"] is False
    assert ambiguous_fields["package_replay_order_executable_candidate_use_allowed_reason"] == (
        "scheduler_materialization_skipped:candidate_generated_not_scheduler_selected"
    )

    explicit_order_exec_false = {
        **candidate,
        "package_replay_order_executable_candidate_use_allowed": False,
    }
    _resign_test_authority(explicit_order_exec_false, expect_valid=True)
    blocked_fields = bridge.selected_package_bridge_quality_fields(
        explicit_order_exec_false,
        matched_stable_member_axis_ids=["member_axis:soft-transfer"],
        matched_members=[member],
    )
    assert blocked_fields["package_replay_executable_candidate_use_allowed"] is False
    assert blocked_fields["package_replay_order_executable_candidate_use_allowed"] is False
    assert blocked_fields["package_replay_order_executable_candidate_use_allowed_reason"] == (
        "scheduler_materialization_skipped:candidate_generated_not_scheduler_selected"
    )

    cost_refused = {
        **candidate,
        "pretrade_cost_packet_status": "REFUSED",
        "pretrade_cost_refusal_reasons": ["spread_r_exceeds_selected_cell_limit"],
    }
    _resign_test_authority(cost_refused, expect_valid=False)
    refused_fields = bridge.selected_package_bridge_quality_fields(
        cost_refused,
        matched_stable_member_axis_ids=["member_axis:soft-transfer"],
        matched_members=[member],
    )
    assert refused_fields["package_replay_executable_candidate_use_allowed"] is False
    assert refused_fields["package_replay_order_executable_candidate_use_allowed"] is False
    assert refused_fields[
        "package_replay_order_executable_candidate_use_allowed_reason"
    ] == "signed_package_new_entry_authority_invalid:broker_cost_packet_not_passed"


def _v220_hard_clean_capped_bridge_row() -> dict:
    row = _signed_bridge_router_refusal_row(
        "source_bound_router_refusal_open_reduced_materialized_for_replay",
        matched_member_axis_id="member_axis:v220-hard-clean-capped",
    )
    row.update(
        {
            "source_bound_package_candidate_use_allowed": True,
            "ultimate_package_source_bound_candidate_use_allowed": True,
            "package_replay_source_bound_candidate_use_allowed": True,
            "ultimate_package_admission_member_axis_match_count": 1,
            "package_replay_order_executable_candidate_use_allowed": True,
            "package_replay_order_executable_final_blocker_class": (
                "selector_materialization"
            ),
            "pretrade_cost_packet_status": "PASSED",
            "cost_authority": "broker_calibrated_replay_cost",
            "cost_source_gap_status": "source_bound_cost_authority_present",
            "candidate_cost_r_fallback_is_authority": False,
            "source_gap_cost_fallback_blocked": False,
            "predecision_stop_hazard_guard_status": "capped",
            "predecision_stop_hazard_guard_action": "cap",
            "predecision_stop_hazard_guard_risk_cap_applied": True,
            "package_risk_expression_full_risk_allowed": False,
            "package_risk_expression_full_risk_applied": False,
            "broker_order_lifecycle_truth_satisfied": True,
            "same_symbol_lifecycle_permitted": True,
            "terminal_vetoes": [],
            "scheduler_materialization_skip_reason": (
                "reallocation_quality_score_below_floor"
            ),
            "entry_price": 2400.0,
            "stop_loss": 2390.0,
            "take_profit_1": 2420.0,
            "replacement_reallocation_quality": {
                "soft_risk_cap_transfer_eligible": True,
                "eligible_for_reallocation_promotion": True,
                "raw_hard_gate_failures": [],
                "hard_gate_failures": [],
                "reallocation_quality_min_promotion_score": 0.0,
                "risk_cap_adjusted_expected_transfer_score": 0.20,
                "legacy_mixed_reallocation_quality_score": -1.05,
                "legacy_mixed_reallocation_quality_score_authority": False,
                "risk_cap_transfer_factor": 0.10,
                "stop_hazard_status": "capped",
                "soft_guard_reallocation_allowed": True,
                "reallocation_quality_score_policy": (
                    "risk_cap_adjusted_expected_transfer_for_capped_candidate;"
                    "legacy_absolute_guard_penalty_is_diagnostic_only"
                ),
                "source_boundary": (
                    "predecision_expected_transfer_plus_pending_replacement_"
                    "quality_no_outcome_fields"
                ),
                "uses_outcome_fields": False,
            },
        }
    )
    return row


def test_selected_bridge_v220_hard_clean_capped_skip_remains_reduced_risk_executable() -> None:
    bridge = load_selected_package_replay_bridge()
    row = _v220_hard_clean_capped_bridge_row()

    assert bridge.v220_hard_clean_capped_reduced_risk_contract_allowed(row) is True
    assert (
        bridge.scheduler_materialization_skip_is_soft_transfer(
            row,
            row["scheduler_materialization_skip_reason"],
        )
        is True
    )
    assert bridge.executable_package_use_detail(
        row,
        source_bound_allowed=True,
    ) == (True, "broker_cost_selector_and_scheduler_action_executable")
    fields = bridge.selected_package_bridge_quality_fields(
        row,
        matched_stable_member_axis_ids=["member_axis:v220-hard-clean-capped"],
    )
    assert fields["package_replay_executable_candidate_use_allowed"] is True
    assert fields["package_replay_order_executable_candidate_use_allowed"] is True


def test_selected_bridge_v220_hard_clean_capped_skip_rejects_contract_leaks() -> None:
    bridge = load_selected_package_replay_bridge()
    denied: list[tuple[str, dict]] = []

    generic_negative = _v220_hard_clean_capped_bridge_row()
    generic_negative["replacement_reallocation_quality"][
        "soft_risk_cap_transfer_eligible"
    ] = False
    denied.append(("generic_negative", generic_negative))

    hard_failure = _v220_hard_clean_capped_bridge_row()
    hard_failure["replacement_reallocation_quality"]["raw_hard_gate_failures"] = [
        "unit_risk_geometry_hard_failure"
    ]
    denied.append(("unit_risk_geometry", hard_failure))

    nonpositive_transfer = _v220_hard_clean_capped_bridge_row()
    nonpositive_transfer["replacement_reallocation_quality"][
        "risk_cap_adjusted_expected_transfer_score"
    ] = 0.0
    denied.append(("nonpositive_transfer", nonpositive_transfer))

    signed_failure = _v220_hard_clean_capped_bridge_row()
    signed_failure["package_new_entry_authority_valid"] = False
    denied.append(("signed_authority", signed_failure))

    cost_failure = _v220_hard_clean_capped_bridge_row()
    cost_failure["pretrade_cost_packet_status"] = "REFUSED"
    denied.append(("broker_cost", cost_failure))

    source_failure = _v220_hard_clean_capped_bridge_row()
    source_failure["source_completeness"] = 0.80
    denied.append(("source_completeness", source_failure))

    lifecycle_failure = _v220_hard_clean_capped_bridge_row()
    lifecycle_failure["broker_order_lifecycle_truth_satisfied"] = False
    denied.append(("lifecycle", lifecycle_failure))

    cap_escape = _v220_hard_clean_capped_bridge_row()
    cap_escape["predecision_stop_hazard_guard_risk_cap_applied"] = False
    denied.append(("cap_inactive", cap_escape))

    full_risk_escape = _v220_hard_clean_capped_bridge_row()
    full_risk_escape["package_risk_expression_full_risk_allowed"] = True
    denied.append(("full_risk_escape", full_risk_escape))

    for label, row in denied:
        assert (
            bridge.v220_hard_clean_capped_reduced_risk_contract_allowed(row) is False
        ), label
        assert (
            bridge.scheduler_materialization_skip_is_soft_transfer(
                row,
                row["scheduler_materialization_skip_reason"],
            )
            is False
        ), label


def test_selected_package_bridge_filters_non_executable_order_trade_rows() -> None:
    bridge = load_selected_package_replay_bridge()

    rows = [
        {
            "candidate_id": "blocked",
            "decision_time_utc": "2026-05-05T07:15:00+00:00",
            "package_replay_executable_candidate_use_allowed": False,
            "package_replay_executable_candidate_use_allowed_reason": (
                "ultimate_package_effective_source_bound_not_allowed"
            ),
            "replay_candidate_use_allowed_now": True,
        },
        {
            "candidate_id": "allowed",
            "decision_time_utc": "2026-05-05T07:30:00+00:00",
            "package_replay_executable_candidate_use_allowed": True,
            "package_replay_executable_candidate_use_allowed_reason": (
                "broker_cost_selector_and_scheduler_action_executable"
            ),
            "selector_action": "trade",
            "scheduler_materialization_action_intent": "new_position",
        },
        {
            "candidate_id": "source-required-lifecycle-gap",
            "decision_time_utc": "2026-05-05T07:45:00+00:00",
            "package_replay_executable_candidate_use_allowed": True,
            "package_replay_executable_candidate_use_allowed_reason": (
                "broker_cost_selector_and_scheduler_action_executable"
            ),
            "source_required_lifecycle_origin": True,
            "broker_order_lifecycle_truth_satisfied": False,
            "selector_action": "trade",
            "scheduler_materialization_action_intent": "same_direction_scale_in",
        },
    ]

    kept, dropped = bridge.filter_executable_order_trade_rows(rows, row_type="order")

    assert [row["candidate_id"] for row in kept] == ["allowed"]
    assert [row["candidate_id"] for row in dropped] == [
        "blocked",
        "source-required-lifecycle-gap",
    ]
    assert dropped[0]["replay_candidate_use_allowed_now"] is False
    assert dropped[0]["order_materialization_authority_blocked"] is True
    assert dropped[1]["order_filtered_from_executable_ledger_reason"] == (
        "source_required_lifecycle_origin_without_broker_order_lifecycle_truth"
    )


def test_selected_package_bridge_terminal_blocked_and_non_sent_statuses_fail_closed() -> None:
    bridge = load_selected_package_replay_bridge()
    base = {
        "candidate_id": "terminal-status-candidate",
        "decision_time_utc": "2026-05-05T08:00:00+00:00",
        "ultimate_package_effective_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_admission_count": 1,
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "candidate_cost_r_fallback_is_authority": False,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "expected_net_r": 0.8,
        "probability": 0.8,
        "fill_probability": 0.8,
        "execution_fill_probability": 0.8,
        "execution_fill_probability_source": "unit_test_predecision_fillability",
        "selector_action": "trade",
        "scheduler_materialization_action_intent": "new_position",
        "entry_price": 1.1000,
        "stop_loss": 1.0950,
        "take_profit_1": 1.1100,
        "package_replay_executable_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed_reason": (
            "broker_cost_selector_and_scheduler_action_executable"
        ),
    }
    statuses = (
        "risk_rejected",
        "execution_manager_blocked",
        "guarded_market_fallback_contract_unmet",
        "source_required_lifecycle_gap_diagnostic_only",
        "not_sent_missed_opportunity",
        "not_sent_marketable_limit_structure_preservation_contract_unmet",
    )

    for status in statuses:
        row = {**base, "order_status": status}
        allowed, reason = bridge.executable_package_use_detail(
            row,
            source_bound_allowed=True,
        )
        assert allowed is False, status
        assert reason == f"terminal_non_executable_status:order_status:{status}", status
        fields = bridge.package_authority_bridge_fields(
            row,
            source_bound_allowed=True,
        )
        assert fields["package_replay_order_executable_candidate_use_allowed"] is False
        assert fields["package_replay_order_executable_candidate_use_allowed_reason"] == (
            reason
        )

    rows = [
        {
            **base,
            "candidate_id": f"terminal-{index}",
            "order_status": status,
        }
        for index, status in enumerate(statuses)
    ]
    kept, dropped = bridge.filter_executable_order_trade_rows(rows, row_type="order")

    assert kept == []
    assert len(dropped) == len(statuses)
    assert all(row["order_materialization_authority_blocked"] is True for row in dropped)
    assert all(row["order_filtered_from_executable_ledger"] is True for row in dropped)


def test_package_replay_missing_scheduler_action_requires_explicit_intent() -> None:
    candidate = {
        "candidate_id": "package-row",
        "selector_action": "trade",
        "package_replay_executable_candidate_use_allowed": True,
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "candidate_cost_r_fallback_is_authority": False,
    }

    assert (
        timewarp.package_or_replay_row_requires_explicit_action_intent(candidate, {})
        is True
    )
    assert (
        timewarp.replay_order_materialization_authority_block_reason(
            candidate=candidate,
            packets={},
            config={"gtos_vnext_runtime": {}},
        )
        == "missing_explicit_scheduler_action_intent_for_package_replay_authority"
    )


def test_compact_candidate_index_backfills_selected_cell_risk_from_risk_packet() -> None:
    harness = load_broad_replay_harness()

    rows = harness.compact_candidate_index_rows(
        [
            {
                "candidate_id": "candidate-risk-packet",
                "decision_time_utc": "2026-05-13T08:00:00+00:00",
                "symbol": "XAUUSD",
                "side": "LONG",
                "selector_action": "open-reduced-risk",
                "risk_authority_pre_scheduler": {
                    "schema_version": "risk_authority_pre_scheduler_v1",
                    "risk_per_trade_pct": 0.25,
                    "approved_risk_pct": 0.10,
                    "packet_hash_sha256": "risk-packet-hash",
                },
            }
        ]
    )

    assert rows[0]["risk_per_trade_pct"] == 0.25
    assert rows[0]["selected_cell_risk_pct"] == 0.25


def _write_runtime_package_input(
    path: Path,
    *,
    schema: str,
    identity_field: str,
    identities: list[str | None],
) -> None:
    rows = [
        {
            "schema": schema,
            **({identity_field: identity} if identity is not None else {}),
        }
        for identity in identities
    ]
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_ultimate_package_runtime_input_contract_accepts_complete_inputs(
    tmp_path: Path,
) -> None:
    harness = load_broad_replay_harness()
    registry = tmp_path / "registry.jsonl"
    member_axis = tmp_path / "member-axis.jsonl"
    _write_runtime_package_input(
        registry,
        schema=harness.ULTIMATE_PACKAGE_REGISTRY_SCHEMA,
        identity_field="sleeve_id",
        identities=["sleeve-a", "sleeve-b"],
    )
    _write_runtime_package_input(
        member_axis,
        schema=harness.ULTIMATE_PACKAGE_MEMBER_AXIS_SCHEMA,
        identity_field="stable_member_axis_id",
        identities=["axis-a", "axis-b", "axis-c"],
    )

    contract = harness.ultimate_package_runtime_input_contract(
        registry_path=registry,
        member_axis_path=member_axis,
        expected_registry_rows=2,
        expected_member_axis_rows=3,
    )

    assert contract["valid"] is True
    assert contract["failure_reasons"] == []
    assert contract["inputs"]["sleeve_registry"]["unique_identity_count"] == 2
    assert contract["inputs"]["member_axis"]["unique_identity_count"] == 3
    assert len(contract["inputs"]["member_axis"]["sha256"]) == 64
    assert harness.require_ultimate_package_runtime_inputs(contract=contract) == contract


def test_ultimate_package_runtime_input_contract_rejects_missing_member_axis(
    tmp_path: Path,
) -> None:
    harness = load_broad_replay_harness()
    registry = tmp_path / "registry.jsonl"
    member_axis = tmp_path / "missing-member-axis.jsonl"
    _write_runtime_package_input(
        registry,
        schema=harness.ULTIMATE_PACKAGE_REGISTRY_SCHEMA,
        identity_field="sleeve_id",
        identities=["sleeve-a"],
    )

    contract = harness.ultimate_package_runtime_input_contract(
        registry_path=registry,
        member_axis_path=member_axis,
        expected_registry_rows=1,
        expected_member_axis_rows=1,
    )

    assert contract["valid"] is False
    assert "member_axis:file_missing" in contract["failure_reasons"]
    with pytest.raises(ValueError, match="member_axis:file_missing"):
        harness.require_ultimate_package_runtime_inputs(contract=contract)


def test_ultimate_package_runtime_input_contract_rejects_empty_member_axis(
    tmp_path: Path,
) -> None:
    harness = load_broad_replay_harness()
    registry = tmp_path / "registry.jsonl"
    member_axis = tmp_path / "empty-member-axis.jsonl"
    _write_runtime_package_input(
        registry,
        schema=harness.ULTIMATE_PACKAGE_REGISTRY_SCHEMA,
        identity_field="sleeve_id",
        identities=["sleeve-a"],
    )
    member_axis.write_text("", encoding="utf-8")

    contract = harness.ultimate_package_runtime_input_contract(
        registry_path=registry,
        member_axis_path=member_axis,
        expected_registry_rows=1,
        expected_member_axis_rows=1,
    )

    assert contract["valid"] is False
    assert "member_axis:file_empty" in contract["failure_reasons"]


def test_ultimate_package_runtime_input_contract_rejects_schema_and_identity_corruption(
    tmp_path: Path,
) -> None:
    harness = load_broad_replay_harness()
    registry = tmp_path / "registry.jsonl"
    member_axis = tmp_path / "member-axis.jsonl"
    _write_runtime_package_input(
        registry,
        schema=harness.ULTIMATE_PACKAGE_REGISTRY_SCHEMA,
        identity_field="sleeve_id",
        identities=["sleeve-a"],
    )
    _write_runtime_package_input(
        member_axis,
        schema="wrong.member.axis.schema",
        identity_field="stable_member_axis_id",
        identities=["axis-a", "axis-a", None],
    )

    contract = harness.ultimate_package_runtime_input_contract(
        registry_path=registry,
        member_axis_path=member_axis,
        expected_registry_rows=1,
        expected_member_axis_rows=3,
    )
    member = contract["inputs"]["member_axis"]

    assert contract["valid"] is False
    assert member["schema_mismatch_rows"] == 3
    assert member["duplicate_identity_rows"] == 1
    assert member["missing_identity_rows"] == 1


def test_ultimate_package_runtime_input_contract_accepts_hydrated_route_inputs() -> None:
    harness = load_broad_replay_harness()
    harness.configure_runtime_evidence_root(Path("/Users/borr/GTOSActive/repo"))

    contract = harness.ultimate_package_runtime_input_contract()

    assert contract["valid"] is True
    assert contract["inputs"]["sleeve_registry"]["row_count"] == 82
    assert contract["inputs"]["member_axis"]["row_count"] == 1101


def test_broad_replay_fails_before_source_resolution_on_invalid_runtime_inputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = load_broad_replay_harness()
    prefix = "RUNTIME_INPUT_FAIL_CLOSED_TEST"
    monkeypatch.setattr(harness, "ROUTE", tmp_path)
    outputs = harness.output_paths(prefix)
    outputs["candidate"].write_text("stale\n", encoding="utf-8")
    contract = {
        "schema": harness.ULTIMATE_PACKAGE_RUNTIME_INPUT_CONTRACT_SCHEMA,
        "status": "runtime_authority_inputs_invalid_fail_closed",
        "valid": False,
        "failure_reasons": ["member_axis:file_missing"],
        "inputs": {},
    }
    monkeypatch.setattr(
        harness,
        "ultimate_package_runtime_input_contract",
        lambda: contract,
    )

    args = SimpleNamespace(
        output_prefix=prefix,
        skip_tick_source=False,
        symbols=None,
        compact_missed_ledger=True,
        compact_decision_ledger=True,
        compact_scorecard_ledger=True,
        omit_candidate_ledger=True,
        omit_candidate_index_ledger=True,
        omit_packet_sidecar_ledger=True,
        profiles=[harness.PROFILE_REPAIRED],
        chunk_size=1,
        max_candidates_per_symbol_window=0,
        smoke_subset=False,
        use_native_h1=False,
        candidate_ledger_packet_max_bytes=1024,
        scorecard_ledger_packet_max_bytes=4096,
        compact_scorecard_symbol_risk_config=True,
        scorecard_probe_row_limit=12,
        gc_between_chunks=True,
    )
    with pytest.raises(
        ValueError,
        match="ultimate_package_runtime_input_contract_failed:member_axis:file_missing",
    ):
        harness._run_typed_sparse_attempt5(args)

    assert not outputs["candidate"].exists()
    partial = json.loads(outputs["partial_summary"].read_text(encoding="utf-8"))
    assert partial["status"] == "runtime_input_preflight_not_final_proof"
    assert partial["ultimate_package_runtime_input_contract"] == contract


def test_compact_decision_projection_omits_only_exact_nested_fvg_alias() -> None:
    harness = load_broad_replay_harness()
    partition = {
        "schema": "gtos.current_fvg_poi_generation_partition.v1",
        "rows": [
            {"poi_id": f"poi-{index}", "disposition": "emitted"}
            for index in range(80)
        ],
    }
    source = {
        "decision_time_utc": "2026-06-03T08:00:00+00:00",
        "current_fvg_poi_generation": partition,
        "candidate_generation_audit": {
            "producer_generation_audit": {
                "status": "candidate_generation_complete",
                "current_fvg_poi_generation": partition,
            }
        },
    }

    [compact] = harness.compact_asof_decision_rows([source])

    producer = compact["candidate_generation_audit"]["producer_generation_audit"]
    assert compact["current_fvg_poi_generation"] == partition
    assert "current_fvg_poi_generation" not in producer
    assert producer["current_fvg_poi_generation_projection_ref"] == (
        "top_level.current_fvg_poi_generation"
    )
    assert compact["current_fvg_poi_generation_projection_sha256"] == (
        harness.stable_sha256(partition)
    )
    assert len(json.dumps(compact, sort_keys=True)) < (
        len(json.dumps(source, sort_keys=True)) * 0.60
    )


def test_compact_decision_projection_preserves_distinct_nested_partition() -> None:
    harness = load_broad_replay_harness()
    source = {
        "current_fvg_poi_generation": {"rows": [{"poi_id": "top"}]},
        "candidate_generation_audit": {
            "producer_generation_audit": {
                "current_fvg_poi_generation": {
                    "rows": [{"poi_id": "distinct"}]
                }
            }
        },
    }

    [compact] = harness.compact_asof_decision_rows([source])

    assert compact["candidate_generation_audit"]["producer_generation_audit"][
        "current_fvg_poi_generation"
    ] == {"rows": [{"poi_id": "distinct"}]}
    assert compact["current_fvg_poi_generation_projection_status"] == (
        "distinct_nested_partition_preserved_not_compacted"
    )


def test_compact_decision_projection_marks_canonical_no_alias_row() -> None:
    harness = load_broad_replay_harness()
    partition = {"rows": [{"poi_id": "canonical-only"}]}

    [compact] = harness.compact_asof_decision_rows(
        [{"current_fvg_poi_generation": partition}]
    )

    assert compact["current_fvg_poi_generation"] == partition
    assert compact["current_fvg_poi_generation_projection_status"] == (
        "canonical_top_level_preserved_no_nested_alias"
    )
    assert compact["current_fvg_poi_generation_projection_sha256"] == (
        harness.stable_sha256(partition)
    )


def test_compact_scorecard_projection_preserves_canonical_trace_and_finalizer() -> None:
    harness = load_broad_replay_harness()
    trace = [
        {
            "candidate_id": f"candidate-{index}",
            "scheduler_rank": index + 1,
            "score": 100.0 - index,
            "selected": index == 0,
            "evidence": "x" * 200,
        }
        for index in range(120)
    ]
    finalizer = {
        "probe_rows": [
            {
                "candidate_id": "candidate-0",
                "selected": True,
                "final_approved_risk_pct": 1.0,
            }
        ]
    }
    source = {
        "scheduler_option_trace": trace,
        "pre_risk_finalizer_scheduler_option_trace": trace,
        "post_risk_finalizer_scheduler_option_trace": trace,
        "risk_admitted_scheduler_finalizer": finalizer,
    }

    [compact] = harness.compact_scorecard_rows([source])

    assert compact["scheduler_option_trace"] == trace
    assert compact["risk_admitted_scheduler_finalizer"] == finalizer
    assert "pre_risk_finalizer_scheduler_option_trace" not in compact
    assert "post_risk_finalizer_scheduler_option_trace" not in compact
    assert compact["scheduler_option_trace_projection_sha256"] == (
        harness.stable_sha256(trace)
    )
    assert len(json.dumps(compact, sort_keys=True)) < (
        len(json.dumps(source, sort_keys=True)) * 0.55
    )


def test_compact_scorecard_projection_preserves_distinct_trace_alias() -> None:
    harness = load_broad_replay_harness()
    source = {
        "scheduler_option_trace": [{"candidate_id": "canonical"}],
        "pre_risk_finalizer_scheduler_option_trace": [
            {"candidate_id": "distinct"}
        ],
        "post_risk_finalizer_scheduler_option_trace": [
            {"candidate_id": "canonical"}
        ],
    }

    [compact] = harness.compact_scorecard_rows([source])

    assert compact["pre_risk_finalizer_scheduler_option_trace"] == [
        {"candidate_id": "distinct"}
    ]
    assert "post_risk_finalizer_scheduler_option_trace" not in compact
    assert compact["scheduler_option_trace_omitted_duplicate_aliases"] == [
        "post_risk_finalizer_scheduler_option_trace"
    ]


def test_compact_scorecard_projection_marks_canonical_no_alias_row() -> None:
    harness = load_broad_replay_harness()
    trace = [{"candidate_id": "canonical-only"}]

    [compact] = harness.compact_scorecard_rows(
        [{"scheduler_option_trace": trace}]
    )

    assert compact["scheduler_option_trace"] == trace
    assert compact["scheduler_option_trace_projection_status"] == (
        "canonical_trace_preserved_no_aliases_present"
    )
    assert compact["scheduler_option_trace_omitted_duplicate_aliases"] == []
    assert compact["scheduler_option_trace_projection_sha256"] == (
        harness.stable_sha256(trace)
    )


def test_candidate_relational_materialization_requires_disjoint_terminal_paths() -> None:
    harness = load_broad_replay_harness()

    def row(candidate_id: str, **fields: object) -> dict[str, object]:
        return {
            "candidate_id": candidate_id,
            "canonical_replay_candidate_instance_key": (
                f"{candidate_id}@@2026-06-03T08:00:00+00:00"
            ),
            **fields,
        }

    exact = harness.candidate_relational_materialization_audit(
        candidate_rows=[row("missed"), row("filled"), row("unfilled")],
        missed_rows=[row("missed", terminal_outcome="not_filled_no_trade")],
        order_rows=[
            row("filled", order_status="pending_accepted", simulated_order_id="o1"),
            row(
                "filled",
                order_status="filled",
                simulated_order_id="o1",
                is_terminal_order_event=True,
            ),
            row("unfilled", order_status="pending_accepted", simulated_order_id="o2"),
            row(
                "unfilled",
                order_status="expired_unfilled",
                simulated_order_id="o2",
                is_terminal_order_event=True,
            ),
        ],
        trade_rows=[
            row(
                "filled",
                simulated_order_id="o1",
                simulated_trade_id="t1",
                terminal_outcome="target_reached_before_stop",
            )
        ],
        exit_rows=[
            row(
                "filled",
                simulated_order_id="o1",
                simulated_trade_id="t1",
                terminal_outcome="target_reached_before_stop",
                close_reason="target_reached_before_stop",
            ),
            row(
                "unfilled",
                simulated_order_id="o2",
                simulated_trade_id="t2",
                terminal_outcome="not_filled",
                close_reason="not_filled_no_trade",
            ),
        ],
        account_rows=[
            {
                "event": "simulated_trade_closed",
                "simulated_order_id": "o1",
                "simulated_trade_id": "t1",
            },
            {"event": "simulated_order_expired_unfilled", "simulated_order_id": "o2"},
        ],
    )

    assert exact["exact"] is True
    assert exact["candidate_rows"] == 3
    assert exact["terminal_disposition_counts"] == {
        "missed": 1,
        "trade": 1,
        "terminal_unfilled": 1,
    }
    assert exact["order_trade_overlap"] == 1
    assert exact["graph"] == "research_timewarp"
    assert exact["production_parity"] is False
    assert exact["full_flow_economics_complete"] is False


def test_candidate_relational_materialization_rejects_pending_only_and_zero() -> None:
    harness = load_broad_replay_harness()
    candidate = {
        "candidate_id": "pending",
        "canonical_replay_candidate_instance_key": "pending@@2026-06-03T08:00:00+00:00",
    }
    pending_only = harness.candidate_relational_materialization_audit(
        candidate_rows=[candidate],
        missed_rows=[],
        order_rows=[
            {**candidate, "order_status": "pending_accepted", "simulated_order_id": "o1"}
        ],
        trade_rows=[],
        exit_rows=[],
        account_rows=[],
    )
    empty = harness.candidate_relational_materialization_audit(
        candidate_rows=[],
        missed_rows=[],
        order_rows=[],
        trade_rows=[],
        exit_rows=[],
        account_rows=[],
    )

    assert pending_only["exact"] is False
    assert pending_only["failure_counts"] == {
        "candidate_terminal_order_or_identity_count_not_one": 1
    }
    assert empty["exact"] is False
    assert empty["failure_counts"] == {"candidate_population_empty": 1}


def test_candidate_relational_materialization_rejects_missing_and_orphan_joins() -> None:
    harness = load_broad_replay_harness()
    key = "filled@@2026-06-03T08:00:00+00:00"
    candidate = {"candidate_id": "filled", "canonical_replay_candidate_instance_key": key}
    audit = harness.candidate_relational_materialization_audit(
        candidate_rows=[candidate],
        missed_rows=[],
        order_rows=[
            {
                **candidate,
                "order_status": "filled",
                "simulated_order_id": "o1",
                "is_terminal_order_event": True,
            }
        ],
        trade_rows=[
            {
                **candidate,
                "simulated_order_id": "o1",
                "simulated_trade_id": "t1",
                "terminal_outcome": "stop_reached_before_target",
            },
            {
                "candidate_id": "orphan",
                "canonical_replay_candidate_instance_key": "orphan@@time",
                "simulated_order_id": "orphan-order",
                "simulated_trade_id": "orphan-trade",
                "terminal_outcome": "stop_reached_before_target",
            },
        ],
        exit_rows=[],
        account_rows=[{"event": "simulated_trade_closed"}],
    )

    assert audit["exact"] is False
    assert audit["failure_counts"]["filled_trade_exit_account_counts_invalid"] == 1
    assert audit["failure_counts"]["orphan_trade_candidate_instance"] == 1
    assert audit["failure_counts"]["closed_account_execution_identity_missing"] == 1


def test_candidate_relational_materialization_rejects_terminal_overlap_and_duplicate() -> None:
    harness = load_broad_replay_harness()
    candidate = {
        "candidate_id": "unfilled",
        "canonical_replay_candidate_instance_key": "unfilled@@2026-06-03T08:00:00+00:00",
    }
    terminal_order = {
        **candidate,
        "order_status": "expired_unfilled",
        "simulated_order_id": "o1",
        "is_terminal_order_event": True,
    }
    audit = harness.candidate_relational_materialization_audit(
        candidate_rows=[candidate],
        missed_rows=[{**candidate, "terminal_outcome": "not_filled_no_trade"}],
        order_rows=[terminal_order, dict(terminal_order)],
        trade_rows=[],
        exit_rows=[
            {
                **candidate,
                "simulated_order_id": "o1",
                "terminal_outcome": "not_filled",
                "close_reason": "not_filled_no_trade",
            }
        ],
        account_rows=[],
    )

    assert audit["exact"] is False
    assert audit["failure_counts"]["missed_terminal_overlaps_selected_flow"] == 1
    assert audit["failure_counts"]["duplicate_order_event_joins"] == 1


def test_materialized_candidate_rows_from_stats_survives_ledger_omission() -> None:
    harness = load_broad_replay_harness()

    assert harness.materialized_candidate_rows_from_stats(
        [
            {"profile": "repaired", "split": "development", "candidate_rows": 7},
            {"profile": "repaired", "split": "holdout", "candidate_rows": 11},
        ]
    ) == 18


def test_selected_bridge_status_join_falls_back_to_canonical_scorecard_trace() -> None:
    bridge = load_selected_package_replay_bridge()
    row = {
        "selected_candidate_id": "selected",
        "scheduler_option_trace": [
            {
                "candidate_id": "selected",
                "stable_decision_window_id": "XAUUSD:LONG:2026-06-03T08:00:00Z",
            },
            {
                "candidate_id": "alternative",
                "stable_decision_window_id": "XAUUSD:LONG:2026-06-03T08:00:00Z",
            },
        ],
    }

    assert bridge._candidate_ids_for_status_join(row) == [
        "selected",
        "alternative",
    ]
    assert bridge._status_join_windows(row) == [
        "XAUUSD:LONG:2026-06-03T08:00:00Z"
    ]


def test_compact_candidate_index_rows_materialize_canonical_instance_identity() -> None:
    harness = load_broad_replay_harness()

    rows = harness.compact_candidate_index_rows(
        [
            {
                "candidate_id": "candidate-identity",
                "decision_time_utc": "2026-04-21T08:00:00+00:00",
                "symbol": "XAUUSD",
                "side": "LONG",
                "selector_action": "trade",
                "entry_price": 2300.0,
                "stop_loss": 2290.0,
                "take_profit_1": 2320.0,
                "dynamic_geometry_policy": "momentum_exhaustion",
                "dynamic_execution_policy_id": "vnext_exec_momentum_1r_pullback_04r_cap_2r",
                "expected_net_r": 1.15,
                "selected_policy_expected_net_r": 1.15,
                "selected_policy_for_expected_net_r": "momentum_exhaustion",
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
                "probability": 0.91,
                "fill_probability": 0.92,
                "source_completeness": 1.0,
                "candidate_decision_quality_source_boundary": (
                    "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
                ),
                "source_boundary": (
                    "predecision_package_quality_and_broker_cost_no_outcome_fields"
                ),
                "same_symbol_replay_exposure_context": {
                    "symbol": "XAUUSD",
                    "side": "LONG",
                    "same_side_pending_count": 1,
                    "same_side_pending_ids": ["pending-1"],
                    "same_side_pending_risk_pct": 0.1,
                    "opposite_pending_count": 0,
                    "opposite_pending_ids": [],
                    "opposite_pending_risk_pct": 0.0,
                },
                "replacement_reallocation_quality": {
                    "score": 0.42,
                    "eligible_for_reallocation_promotion": True,
                    "hard_gate_failures": [],
                    "source_boundary": "scheduler_replacement_predecision_quality",
                    "uses_outcome_fields": False,
                },
                "selected_scheduler_options_by_candidate_instance_key": {
                    "candidate-identity@@2026-04-21T08:00:00+00:00": {
                        "candidate_id": "candidate-identity",
                        "decision_time_utc": "2026-04-21T08:00:00+00:00",
                    }
                },
                "selected_scheduler_options_by_candidate_id_lookup_status": (
                    "legacy_candidate_id_map_for_diagnostics_only"
                ),
                "scheduler_quality_backfill_status": (
                    "scheduler_option_missing_for_candidate"
                ),
                "ultimate_candidate_package_open_reduced_risk_authority": {
                    "allowed": True,
                    "authority_family": "package_open_reduced_unit_test",
                },
                "package_open_reduced_authority_allowed": True,
                "package_open_reduced_authority_family": "package_open_reduced_unit_test",
                "pretrade_cost_packet_status": "PASSED",
                "cost_source_gap_status": "source_bound_cost_authority_present",
                "cost_authority": "broker_calibrated_replay_cost",
                "ultimate_package_source_bound_candidate_use_allowed": True,
                "ultimate_package_effective_source_bound_candidate_use_allowed": True,
                "ultimate_package_effective_admission_count": 1.0,
                "replay_candidate_use_allowed_now": True,
                "risk_authority_pre_scheduler": {
                    "schema_version": "runtime_risk_authority_packet_v1",
                    "packet_hash_sha256": "hash-risk",
                    "risk_config_source": "fixture",
                    "risk_per_trade_pct": 0.25,
                    "selected_cell_risk_pct": 0.25,
                },
            }
        ]
    )

    assert len(rows) == 1
    row = rows[0]
    instance_key = "candidate-identity@@2026-04-21T08:00:00+00:00"
    assert row["canonical_replay_candidate_instance_key"] == instance_key
    assert row["risk_finalizer_probe_instance_key"] == instance_key
    assert row["source_bound_replay_candidate_instance_key"] == instance_key
    assert row["candidate_instance_identity_status"] == "materialized"
    assert row["risk_authority"] == "runtime_risk_authority_packet_v1"
    assert row["risk_authority_status"] == "pre_scheduler_risk_authority_materialized"
    assert row["risk_authority_packet_hash_sha256"] == "hash-risk"
    assert row["source_boundary"] == (
        "predecision_package_quality_and_broker_cost_no_outcome_fields"
    )
    assert row["same_symbol_replay_exposure_context"]["same_side_pending_count"] == 1
    assert row["same_symbol_replay_exposure_context_status"] == "source_observed"
    assert row["canonical_replay_context_projection_status"] == "materialized"
    assert row["canonical_replay_context_envelope"]["symbol"] == "XAUUSD"
    assert row["replacement_reallocation_quality_score"] == 0.42
    assert row["replacement_reallocation_quality_eligible"] is True
    assert row["replacement_reallocation_quality_uses_outcome_fields"] is False
    assert (
        row["selected_scheduler_options_by_candidate_instance_key"][
            "candidate-identity@@2026-04-21T08:00:00+00:00"
        ]["candidate_id"]
        == "candidate-identity"
    )
    assert (
        row["selected_scheduler_options_by_candidate_id_lookup_status"]
        == "legacy_candidate_id_map_for_diagnostics_only"
    )
    quality = row["candidate_decision_quality"]
    assert quality["expected_net_r"] == 1.15
    assert quality["candidate_expected_net_r"] == 1.15
    assert quality["probability"] == 0.91
    assert quality["candidate_probability"] == 0.91
    assert quality["fill_probability"] == 0.92
    assert quality["candidate_fill_probability"] == 0.92
    assert quality["source_completeness"] == 1.0
    assert quality["candidate_decision_quality_source_boundary"] == (
        "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
    )
    assert row["candidate_scheduler_quality_parity_status"] == (
        "not_applicable_scheduler_option_missing"
    )
    assert row["candidate_scheduler_quality_parity_mismatches"] == []
    assert row["package_open_reduced_authority_allowed"] is True
    assert (
        row["ultimate_candidate_package_open_reduced_risk_authority"]["allowed"]
        is True
    )
    assert row["candidate_packet_sidecar_payload_omitted"] is True
    assert row["candidate_index_lossless_candidate_payload"] is False
    assert row["entry_price"] == 2300.0
    assert row["stop_loss"] == 2290.0
    assert row["take_profit_1"] == 2320.0
    assert row["dynamic_geometry_policy"] == "momentum_exhaustion"
    assert row["dynamic_execution_policy_id"] == (
        "vnext_exec_momentum_1r_pullback_04r_cap_2r"
    )
    assert row["selected_policy_expected_net_r"] == 1.15
    assert row["selected_policy_for_expected_net_r"] == "momentum_exhaustion"
    assert (
        row["selected_policy_expected_net_calibration_status"]
        == "selected_policy_expected_net_calibration_missing"
    )
    assert row["selected_policy_expected_net_calibrated"] is False
    assert row["selected_policy_expected_net_calibration_required"] is True
    assert row["selected_policy_expected_net_calibration_source"] == (
        "packets.candidate_expected_net_r"
    )
    assert row["selected_policy_expected_net_calibration_source_boundary"] == (
        "selected_policy_expected_net_uncalibrated_bridge_proxy_predecision_quality"
    )
    assert row["source_bound_package_candidate_use_allowed"] is False
    assert row["package_source_bound_admission_diagnostic"] is False
    assert row["package_replay_candidate_use_allowed"] is False
    assert row["package_replay_executable_candidate_use_allowed"] is False
    assert (
        row["ledger_namespace_executable_authority_source"]
        == "explicit_package_replay_executable_or_replay_candidate_use_allowed_now"
    )


def _zero_trade_scorecard_quality_row() -> dict:
    sources = {
        "confidence": "scheduler_default_missing_confidence_0_55",
        "expected_net_r": "packets.candidate_expected_net_r",
        "fill_probability": (
            "ultimate_candidate_package.entry_quality_fill_probability"
        ),
        "probability": "packets.candidate_probability",
        "source_completeness": "candidate.source_completeness",
    }
    return {
        "selected_action_class": "zero_trade",
        "pre_risk_finalizer_candidate_decision_quality_field_sources": None,
        "pre_risk_finalizer_expected_net_r": 1.300472515,
        "pre_risk_finalizer_probability": 0.958768888,
        "pre_risk_finalizer_source_completeness": 1.0,
        "scorecard_reported_expected_net_r": 1.300472515,
        "scorecard_reported_probability": 0.958768888,
        "scorecard_reported_source_completeness": 1.0,
        "finalizer_primary_probe_expected_net_r": 1.300472515,
        "finalizer_primary_probe_probability": 0.958768888,
        "finalizer_primary_probe_source_completeness": 1.0,
        "scorecard_reported_candidate_decision_quality_field_sources": dict(
            sources
        ),
        "finalizer_primary_probe_candidate_decision_quality_field_sources": dict(
            sources
        ),
    }


def test_zero_trade_scorecard_backfills_matching_pre_risk_quality_sources() -> None:
    harness = load_broad_replay_harness()
    row = _zero_trade_scorecard_quality_row()

    harness.normalize_replay_quality_fields(row, row_type="scheduler_scorecard")

    assert row[
        "pre_risk_finalizer_candidate_decision_quality_field_sources"
    ] == {
        "expected_net_r": "packets.candidate_expected_net_r",
        "probability": "packets.candidate_probability",
        "source_completeness": "candidate.source_completeness",
    }


def test_zero_trade_scorecard_quality_source_backfill_fails_closed_on_value_mismatch() -> None:
    harness = load_broad_replay_harness()
    row = _zero_trade_scorecard_quality_row()
    row["finalizer_primary_probe_probability"] = 0.91

    harness.normalize_replay_quality_fields(row, row_type="scheduler_scorecard")

    assert row[
        "pre_risk_finalizer_candidate_decision_quality_field_sources"
    ] is None


def test_zero_trade_scorecard_quality_source_backfill_fails_closed_on_source_mismatch() -> None:
    harness = load_broad_replay_harness()
    row = _zero_trade_scorecard_quality_row()
    row[
        "finalizer_primary_probe_candidate_decision_quality_field_sources"
    ]["probability"] = "different.probability.source"

    harness.normalize_replay_quality_fields(row, row_type="scheduler_scorecard")

    assert row[
        "pre_risk_finalizer_candidate_decision_quality_field_sources"
    ] is None


def test_zero_trade_scorecard_quality_source_backfill_is_idempotent() -> None:
    harness = load_broad_replay_harness()
    row = _zero_trade_scorecard_quality_row()

    harness.normalize_replay_quality_fields(row, row_type="scheduler_scorecard")
    normalized_once = copy.deepcopy(row)
    harness.normalize_replay_quality_fields(row, row_type="scheduler_scorecard")

    assert row == normalized_once

    existing_sources = {
        "expected_net_r": "existing.expected_net_r",
        "probability": "existing.probability",
        "source_completeness": "existing.source_completeness",
        "additional_existing_source": "existing.extra",
    }
    row = _zero_trade_scorecard_quality_row()
    row[
        "pre_risk_finalizer_candidate_decision_quality_field_sources"
    ] = dict(existing_sources)
    harness.normalize_replay_quality_fields(row, row_type="scheduler_scorecard")

    assert row[
        "pre_risk_finalizer_candidate_decision_quality_field_sources"
    ] == existing_sources


def test_zero_trade_scorecard_quality_source_backfill_rejects_synthetic_probe_value() -> None:
    harness = load_broad_replay_harness()
    row = _zero_trade_scorecard_quality_row()
    del row["finalizer_primary_probe_probability"]

    harness.normalize_replay_quality_fields(row, row_type="scheduler_scorecard")

    assert row["finalizer_primary_probe_probability"] == pytest.approx(
        row["pre_risk_finalizer_probability"]
    )
    assert row["finalizer_primary_probe_probability_quality_fill_source"] == (
        "pre_risk_finalizer_probability"
    )
    assert row[
        "pre_risk_finalizer_candidate_decision_quality_field_sources"
    ] is None


def test_scorecard_annotation_backfills_sources_after_late_donor_materialization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = load_broad_replay_harness()
    row = _zero_trade_scorecard_quality_row()
    reported_sources = row.pop(
        "scorecard_reported_candidate_decision_quality_field_sources"
    )
    probe_sources = row.pop(
        "finalizer_primary_probe_candidate_decision_quality_field_sources"
    )

    def materialize_late_donors(output_row: dict) -> None:
        output_row[
            "scorecard_reported_candidate_decision_quality_field_sources"
        ] = copy.deepcopy(reported_sources)
        output_row[
            "finalizer_primary_probe_candidate_decision_quality_field_sources"
        ] = copy.deepcopy(probe_sources)

    monkeypatch.setattr(
        harness,
        "normalize_package_new_entry_authority_ledger_row",
        materialize_late_donors,
    )

    output = harness.annotate_rows(
        [row],
        profile=harness.PROFILE_REPAIRED,
        split="holdout",
        chunk_id="repaired:holdout:2026-06-04:2026-06-04",
        row_type="scheduler_scorecard",
    )[0]

    assert output[
        "pre_risk_finalizer_candidate_decision_quality_field_sources"
    ] == {
        "expected_net_r": "packets.candidate_expected_net_r",
        "probability": "packets.candidate_probability",
        "source_completeness": "candidate.source_completeness",
    }


def test_compact_candidate_index_flattens_scheduler_authority_and_effective_selector_action() -> None:
    harness = load_broad_replay_harness()
    decision_time = "2026-05-13T08:00:00+00:00"
    candidate_id = "candidate-signed-authority"
    materialized_reason = (
        "ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay"
    )
    candidate = {
        "candidate_id": candidate_id,
        "candidate_id_source": "candidate_id",
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": (
            f"{candidate_id}@@{decision_time}"
        ),
        "source_bound_replay_candidate_instance_key": (
            f"{candidate_id}@@{decision_time}"
        ),
        "candidate_instance_identity_status": "materialized",
        "symbol": "XAUUSD",
        "side": "LONG",
        "selector_action": "reject",
        "selector_reason": "router_refusal",
        "scheduler_materialization_selector_action": "open-reduced-risk",
        "scheduler_materialization_selector_reason": materialized_reason,
        "scheduler_materialization_action_intent": "new_position",
        "expected_net_r": 1.2,
        "probability": 0.9,
        "fill_probability": 0.91,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "unit_test.predecision.expected_net_r",
            "probability": "unit_test.predecision.probability",
            "fill_probability": "unit_test.predecision.fill_probability",
            "source_completeness": "unit_test.predecision.source_completeness",
        },
        "candidate_decision_quality_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        "candidate_decision_quality_alias_status": "exact_materialized",
        "candidate_decision_quality_alias_mismatches": [],
        "candidate_decision_quality_provenance_failures": [],
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "candidate_cost_r_fallback_is_authority": False,
        "source_bound_package_candidate_use_allowed": True,
        "package_replay_order_executable_candidate_use_allowed": True,
        "package_replay_order_executable_candidate_use_allowed_reason": (
            "package_candidate_and_signed_new_entry_authority_executable"
        ),
        "package_replay_order_executable_authority_source": (
            "package_replay_executable_and_signed_new_entry_authority"
        ),
    }
    authority_surface = _complete_test_authority_surface(
        candidate,
        selector_action="open-reduced-risk",
        selector_reason=materialized_reason,
        action_intent="new_position",
        authority={
            "applies": True,
            "allowed": True,
            "authority_family": "source_required_lifecycle_repair",
            "authority_source": "unit_test_scheduler_inputs",
            "source_boundary": (
                "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
            ),
        },
    )
    authority_payload = authority_surface["package_new_entry_authority_payload"]
    authority_hash = authority_surface["package_new_entry_authority_hash_sha256"]
    candidate["scheduler_candidate_decision_inputs"] = {
        "expected_net_r": 1.2,
        "probability": 0.9,
        "fill_probability": 0.91,
        "source_completeness": 1.0,
        **authority_surface,
        "predecision_stop_hazard_guard_status": "capped",
        "predecision_stop_hazard_guard_reason": (
            "predecision_stop_hazard_guard_risk_capped"
        ),
        "predecision_stop_hazard_guard_action": "cap",
        "predecision_stop_hazard_guard_risk_cap_applied": False,
        "predecision_stop_hazard_guard_risk_cap_pct": 0.10,
        "predecision_stop_hazard_guard_unit_risk_atr": 0.75,
        "predecision_stop_hazard_guard_distance_to_limit_risk": 0.45,
        "predecision_stop_hazard_guard_limit_fill_probability": 0.78,
        "predecision_stop_hazard_guard_source_boundary": (
            "predecision_limit_fillability_geometry_no_outcome_path"
        ),
        "predecision_stop_hazard_guard_outcome_fields_used": False,
    }

    rows = harness.compact_candidate_index_rows([candidate])

    row = rows[0]
    assert row["selector_action_origin"] == "reject"
    assert row["selector_reason_origin"] == "router_refusal"
    assert row["selector_action"] == "reject"
    assert row["effective_selector_action"] == "open-reduced-risk"
    assert row["effective_selector_reason"] == (
        "ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay"
    )
    assert row["package_new_entry_authority_required"] is True
    assert row["package_new_entry_authority_valid"] is True
    assert row["package_new_entry_authority_hash_sha256"] == authority_hash
    assert row["package_new_entry_authority_payload"] == authority_payload
    assert row["package_new_entry_authority_payload_contract"] == (
        scheduler.PACKAGE_NEW_ENTRY_AUTHORITY_IMMUTABLE_PAYLOAD_CONTRACT
    )
    assert (
        row["package_new_entry_authority_flattened_from_scheduler_inputs"]
        == "scheduler_candidate_decision_inputs"
    )
    assert row["predecision_stop_hazard_guard_status"] == "capped"
    assert row["predecision_stop_hazard_guard_risk_cap_applied"] is True
    assert row["predecision_stop_hazard_guard_risk_cap_pct"] == 0.10
    assert (
        row["predecision_stop_hazard_guard_source_boundary"]
        == "predecision_limit_fillability_geometry_no_outcome_path"
    )
    assert row["predecision_stop_hazard_guard_outcome_fields_used"] is False


def test_compact_candidate_index_preserves_exact_poi_atom() -> None:
    harness = load_broad_replay_harness()
    decision_time = "2026-05-14T01:15:00+00:00"
    poi_state, lifecycle = _valid_compact_poi_atom(decision_time=decision_time)

    row = harness.compact_candidate_index_rows(
        [
            {
                "candidate_id": "poi-compact-candidate",
                "decision_time_utc": decision_time,
                "symbol": "GER40",
                "side": "LONG",
                "origin_family": "current_fvg_fill",
                "poi_state_required": True,
                "poi_id": poi_state["poi_id"],
                "poi_state": poi_state,
                "poi_state_hash_sha256": poi_state["poi_state_hash_sha256"],
                "causal_poi_lifecycle": lifecycle,
                "causal_poi_lifecycle_hash_sha256": lifecycle[
                    "lifecycle_hash_sha256"
                ],
            }
        ]
    )[0]

    assert row["poi_state_required"] is True
    assert row["poi_id"] == "poi-compact-proof"
    assert row["poi_state"] == poi_state
    assert row["poi_state_hash_sha256"] == poi_state["poi_state_hash_sha256"]
    assert row["poi_state_transfer_status"] == timewarp.POI_STATE_TRANSFER_STATUS
    assert row["causal_poi_lifecycle_required"] is True
    assert row["causal_poi_lifecycle"] == lifecycle
    assert row["causal_poi_lifecycle_hash_sha256"] == lifecycle[
        "lifecycle_hash_sha256"
    ]


def test_compact_candidate_index_poi_rehydration_is_exact_and_identity_neutral(
    tmp_path: Path,
) -> None:
    repair = load_compact_poi_repair()
    decision_time = "2026-05-14T01:15:00+00:00"
    instance_key = f"poi-compact-candidate@@{decision_time}"
    poi_state, lifecycle = _valid_compact_poi_atom(decision_time=decision_time)
    candidate_path = tmp_path / "candidate.jsonl"
    missed_path = tmp_path / "missed.jsonl"
    order_path = tmp_path / "order.jsonl"
    candidate_path.write_text(
        json.dumps(
            {
                "candidate_id": "poi-compact-candidate",
                "canonical_replay_candidate_instance_key": instance_key,
                "decision_time_utc": decision_time,
                "origin_family": "current_fvg_fill",
                "symbol": "GER40",
                "side": "LONG",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    missed_path.write_text(
        json.dumps(
            {
                "candidate_id": "poi-compact-candidate",
                "canonical_replay_candidate_instance_key": instance_key,
                "decision_time_utc": decision_time,
                "origin_family": "current_fvg_fill",
                "poi_state_required": True,
                "poi_id": poi_state["poi_id"],
                "poi_state": poi_state,
                "poi_state_hash_sha256": poi_state["poi_state_hash_sha256"],
                "causal_poi_lifecycle": lifecycle,
                "causal_poi_lifecycle_hash_sha256": lifecycle[
                    "lifecycle_hash_sha256"
                ],
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    order_path.write_text("", encoding="utf-8")

    result = repair.rehydrate_candidate_index(
        candidate_index_path=candidate_path,
        missed_path=missed_path,
        order_path=order_path,
        apply=True,
    )
    row = json.loads(candidate_path.read_text(encoding="utf-8"))

    assert result["counts"]["candidate_rows"] == 1
    assert result["counts"]["poi_required_candidate_rows"] == 1
    assert result["counts"]["poi_state_missing_before_rows"] == 1
    assert result["counts"]["poi_terminal_projection_bound_rows"] == 1
    assert result["counts"]["candidate_rows_changed"] == 1
    assert result["candidate_identity_sequence_sha256_before"] == result[
        "candidate_identity_sequence_sha256_after"
    ]
    assert row["canonical_replay_candidate_instance_key"] == instance_key
    assert row["poi_state"] == poi_state
    assert row["causal_poi_lifecycle"] == lifecycle
    assert row["poi_state_required"] is True
    assert row["causal_poi_lifecycle_required"] is True


def test_compact_candidate_index_poi_rehydration_fails_closed_on_lineage_conflict(
    tmp_path: Path,
) -> None:
    repair = load_compact_poi_repair()
    decision_time = "2026-05-14T01:15:00+00:00"
    instance_key = f"poi-compact-candidate@@{decision_time}"
    candidate_state, candidate_lifecycle = _valid_compact_poi_atom(
        poi_id="poi-candidate-lineage",
        decision_time=decision_time,
    )
    terminal_state, terminal_lifecycle = _valid_compact_poi_atom(
        poi_id="poi-terminal-lineage",
        decision_time=decision_time,
    )
    candidate_path = tmp_path / "candidate.jsonl"
    missed_path = tmp_path / "missed.jsonl"
    order_path = tmp_path / "order.jsonl"
    candidate_row = {
        "candidate_id": "poi-compact-candidate",
        "canonical_replay_candidate_instance_key": instance_key,
        "decision_time_utc": decision_time,
        "origin_family": "current_fvg_fill",
        "poi_state_required": True,
        "poi_id": candidate_state["poi_id"],
        "poi_state": candidate_state,
        "poi_state_hash_sha256": candidate_state["poi_state_hash_sha256"],
        "causal_poi_lifecycle": candidate_lifecycle,
        "causal_poi_lifecycle_hash_sha256": candidate_lifecycle[
            "lifecycle_hash_sha256"
        ],
    }
    terminal_row = {
        "candidate_id": "poi-compact-candidate",
        "canonical_replay_candidate_instance_key": instance_key,
        "decision_time_utc": decision_time,
        "origin_family": "current_fvg_fill",
        "poi_state_required": True,
        "poi_id": terminal_state["poi_id"],
        "poi_state": terminal_state,
        "poi_state_hash_sha256": terminal_state["poi_state_hash_sha256"],
        "causal_poi_lifecycle": terminal_lifecycle,
        "causal_poi_lifecycle_hash_sha256": terminal_lifecycle[
            "lifecycle_hash_sha256"
        ],
    }
    candidate_path.write_text(
        json.dumps(candidate_row, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    missed_path.write_text(
        json.dumps(terminal_row, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    order_path.write_text("", encoding="utf-8")
    before = candidate_path.read_bytes()

    with pytest.raises(ValueError, match="candidate_terminal_poi_lineage_conflict"):
        repair.rehydrate_candidate_index(
            candidate_index_path=candidate_path,
            missed_path=missed_path,
            order_path=order_path,
            apply=True,
        )

    assert candidate_path.read_bytes() == before


def test_compact_missed_opportunity_rows_keep_scoreable_execution_evidence() -> None:
    harness = load_broad_replay_harness()

    rows = harness.compact_missed_opportunity_rows(
        [
            {
                "candidate_id": "missed-candidate",
                "decision_time_utc": "2026-05-13T08:00:00+00:00",
                "symbol": "XAUUSD",
                "side": "LONG",
                "selector_action": "open-reduced-risk",
                "selector_reason": (
                    "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk"
                ),
                "scheduler_score": 4.2,
                "scheduler_rank": 2,
                "scheduler_option_runtime_eligible": False,
                "scheduler_option_primary_runtime_ineligible_reason": (
                    "opening_window_scheduler_score_below_quality_floor"
                ),
                "risk_finalizer_reason": (
                    "opening_window_scheduler_score_below_quality_floor"
                ),
                "risk_finalizer_scheduler_option_package_fill_floor_authority_allowed": False,
                "risk_finalizer_scheduler_option_package_fill_floor_authority_failures": [
                    "expected_net_r"
                ],
                "risk_finalizer_scheduler_option_package_fill_floor_authority_raw_failures": [
                    "expected_net_r"
                ],
                "risk_finalizer_scheduler_option_package_fill_floor_authority_resolved_failures": [],
                "risk_finalizer_scheduler_option_package_fill_floor_authority_unresolved_failures": [
                    "expected_net_r"
                ],
                "passive_limit_queue_route_available": True,
                "passive_limit_queue_route_enabled": True,
                "passive_limit_fallback_envelope_required": True,
                "passive_limit_fallback_envelope_applies": True,
                "passive_limit_fallback_envelope_status": "blocked",
                "passive_limit_fallback_envelope_reason": (
                    "passive_limit_fallback_envelope_degraded_transfer_score_below_floor"
                ),
                "passive_limit_fallback_envelope_reasons": [
                    "passive_limit_fallback_envelope_distance_to_limit_risk_above_thesis_geometry_ceiling",
                    "passive_limit_fallback_envelope_degraded_transfer_score_below_floor",
                ],
                "passive_limit_fallback_envelope_degraded_to_passive_queue": False,
                "passive_limit_fallback_envelope_degraded_rank_penalty": 0,
                "passive_limit_fallback_envelope_degraded_transfer_score": 0.3875,
                "passive_limit_fallback_envelope_min_degraded_transfer_score": 0.40,
                "passive_limit_fallback_envelope_used_only_predecision_fields": True,
                "passive_limit_fallback_envelope_distance_to_limit_risk": 2.0,
                "passive_limit_fallback_envelope_distance_to_limit_atr": 0.9,
                "passive_limit_fallback_envelope_limit_fill_probability": 0.50,
                "passive_limit_fallback_envelope_expected_net_r": 1.0,
                "passive_limit_fallback_envelope_expected_net_r_after_guarded_fallback_cost": 0.95,
                "passive_limit_fallback_envelope_source_completeness": 1.0,
                "passive_limit_fallback_envelope_candidate_probability": 0.775,
                "passive_limit_fallback_envelope_blocked": True,
                "passive_limit_fallback_envelope_block_reason": (
                    "passive_limit_fallback_envelope_degraded_transfer_score_below_floor"
                ),
                "expected_net_r": 1.21,
                "candidate_expected_net_r": 1.21,
                "selected_policy_for_expected_net_r": "momentum_exhaustion",
                "selected_policy_expected_net_calibration_status": (
                    "selected_policy_expected_net_bridge_proxy_diagnostic_only"
                ),
                "selected_policy_expected_net_calibration_source": (
                    "packets.candidate_expected_net_r"
                ),
                "selected_policy_expected_net_calibration_source_boundary": (
                    "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
                ),
                "probability": 0.93,
                "fill_probability": 0.91,
                "source_completeness": 1.0,
                "pretrade_cost_packet_status": "PASSED",
                "missed_pretrade_cost_packet_status": "PASSED",
                "cost_authority": "broker_calibrated_replay_cost",
                "cost_source_gap_status": "source_bound_cost_authority_present",
                "candidate_cost_r_fallback_is_authority": False,
                "order_status": "not_sent_missed_opportunity",
                "missed_opportunity_accounting_scope": (
                    "executable_cost_passed_opportunity_diagnostic"
                ),
                "missed_cost_disposition": "cost_authority_not_primary_miss_reason",
                "missed_cost_executable_opportunity_scoreable": True,
                "opportunity_net_proxy_r": 1.05,
                "opportunity_gross_r": 1.12,
                "package_replay_executable_candidate_use_allowed": True,
                "package_replay_executable_candidate_use_allowed_reason": (
                    "broker_cost_and_scheduler_action_executable"
                ),
                "source_boundary": (
                    "predecision_package_quality_and_broker_cost_no_outcome_fields"
                ),
                "same_symbol_replay_exposure_context": {
                    "symbol": "XAUUSD",
                    "side": "LONG",
                    "same_side_pending_count": 0,
                    "same_side_pending_ids": [],
                    "same_side_pending_risk_pct": 0.0,
                    "opposite_pending_count": 1,
                    "opposite_pending_ids": ["opp-pending"],
                    "opposite_pending_risk_pct": 0.2,
                },
                "replacement_reallocation_quality": {
                    "score": 0.57,
                    "eligible_for_reallocation_promotion": False,
                    "hard_gate_failures": ["quality_floor"],
                    "source_boundary": "scheduler_replacement_predecision_quality",
                    "uses_outcome_fields": False,
                },
                "selected_scheduler_replacement_reallocation_quality_score": 0.57,
                "selected_scheduler_options_by_candidate_instance_key": {
                    "missed-candidate@@2026-05-13T08:00:00+00:00": {
                        "candidate_id": "missed-candidate",
                        "decision_time_utc": "2026-05-13T08:00:00+00:00",
                    }
                },
                "candidate_decision_quality": {"large": "payload"},
                "scheduler_candidate_decision_inputs": {
                    "large": "payload",
                    "package_replay_order_executable_candidate_use_allowed": True,
                    "package_replay_order_executable_candidate_use_allowed_reason": (
                        "package_candidate_and_signed_new_entry_authority_executable"
                    ),
                    "package_replay_order_executable_authority_source": (
                        "package_replay_executable_and_signed_new_entry_authority"
                    ),
                },
                "risk_authority": {
                    "large": "payload",
                    "schema_version": "runtime_risk_authority_packet_v1",
                    "packet_hash_sha256": "risk-hash",
                    "risk_config_source": "unit_fixture",
                    "risk_per_trade_pct": 0.25,
                    "selected_cell_risk_pct": 0.25,
                    "approved_risk_pct": 0.10,
                },
                "ultimate_candidate_package_open_reduced_risk_authority": {
                    "large": "payload"
                },
            }
        ]
    )

    assert len(rows) == 1
    row = rows[0]
    instance_key = "missed-candidate@@2026-05-13T08:00:00+00:00"
    assert row["canonical_replay_candidate_instance_key"] == instance_key
    assert row["same_symbol_replay_exposure_context"]["opposite_pending_count"] == 1
    assert row["same_symbol_replay_exposure_context_status"] == "source_observed"
    assert row["canonical_replay_context_projection_status"] == "materialized"
    assert row["replacement_reallocation_quality_score"] == 0.57
    assert row["replacement_reallocation_quality_eligible"] is False
    assert row["replacement_reallocation_quality_hard_gate_failures"] == [
        "quality_floor"
    ]
    assert row["selected_scheduler_replacement_reallocation_quality_score"] == 0.57
    assert (
        row["selected_scheduler_options_by_candidate_instance_key"][instance_key][
            "candidate_id"
        ]
        == "missed-candidate"
    )
    assert row["missed_opportunity_compact_schema"] == (
        "compact_broad_replay_missed_opportunity_v1"
    )
    assert row["missed_opportunity_payload_omitted"] is True
    assert row["missed_opportunity_lossless_payload"] is False
    assert row["candidate_decision_quality_payload_omitted"] is True
    assert row["scheduler_candidate_decision_inputs_payload_omitted"] is True
    assert row["risk_authority_payload_omitted"] is True
    assert (
        row["ultimate_candidate_package_open_reduced_risk_authority_payload_omitted"]
        is True
    )
    assert row["selected_policy_for_expected_net_r"] == "momentum_exhaustion"
    assert row["selected_policy_expected_net_calibration_status"] == (
        "selected_policy_expected_net_bridge_proxy_diagnostic_only"
    )
    assert row["pretrade_cost_packet_status"] == "PASSED"
    assert row["missed_cost_executable_opportunity_scoreable"] is True
    assert row["opportunity_net_proxy_r"] == 1.05
    assert row["risk_finalizer_reason"] == (
        "opening_window_scheduler_score_below_quality_floor"
    )
    assert (
        row[
            "risk_finalizer_scheduler_option_package_fill_floor_authority_allowed"
        ]
        is False
    )
    assert row[
        "risk_finalizer_scheduler_option_package_fill_floor_authority_failures"
    ] == ["expected_net_r"]
    assert row[
        "risk_finalizer_scheduler_option_package_fill_floor_authority_raw_failures"
    ] == ["expected_net_r"]
    assert row[
        "risk_finalizer_scheduler_option_package_fill_floor_authority_resolved_failures"
    ] == []
    assert row[
        "risk_finalizer_scheduler_option_package_fill_floor_authority_unresolved_failures"
    ] == ["expected_net_r"]
    assert row["passive_limit_queue_route_available"] is True
    assert row["passive_limit_fallback_envelope_status"] == "blocked"
    assert row["passive_limit_fallback_envelope_degraded_to_passive_queue"] is False
    assert row["passive_limit_fallback_envelope_degraded_transfer_score"] == 0.3875
    assert row["passive_limit_fallback_envelope_min_degraded_transfer_score"] == 0.40
    assert row["passive_limit_fallback_envelope_limit_fill_probability"] == 0.50
    assert row["passive_limit_fallback_envelope_used_only_predecision_fields"] is True
    assert row["passive_limit_fallback_envelope_block_reason"] == (
        "passive_limit_fallback_envelope_degraded_transfer_score_below_floor"
    )
    assert row["package_replay_executable_candidate_use_allowed"] is False
    assert row["package_replay_order_executable_candidate_use_allowed"] is False
    assert row["package_replay_order_executable_candidate_use_allowed_reason"] == (
        "compact_missed_complete_immutable_authority_envelope_missing"
    )
    assert row["package_replay_order_executable_authority_source"] == (
        "compact_missed_atomic_authority_fail_closed"
    )
    assert row["missed_opportunity_authority_envelope_status"] == "fail_closed"
    assert row["missed_opportunity_authority_envelope_failure_reason"] == (
        "compact_missed_complete_immutable_authority_envelope_missing"
    )
    assert row["missed_opportunity_signed_authority_payload_preserved"] is False
    assert "package_new_entry_authority_payload" not in row
    assert row["risk_authority"] == "runtime_risk_authority_packet_v1"
    assert row["risk_authority_packet_hash_sha256"] == "risk-hash"
    assert row["risk_config_source"] == "unit_fixture"
    assert row["selected_cell_risk_pct"] == 0.25
    assert row["scheduler_approved_risk_pct"] == 0.10
    assert row["admission_risk_class"] == "open-reduced-risk"
    assert row["final_approved_risk_pct"] == 0.10
    assert row["sizing_haircut_applied"] is True
    assert row["sizing_haircut_factor"] == 0.4
    assert row["ledger_namespace_executable_authority_source"] == (
        "compact_missed_atomic_authority_fail_closed"
    )


def test_compact_missed_opportunity_rows_preserve_exact_poi_atom() -> None:
    harness = load_broad_replay_harness()
    poi_state = {
        "poi_id": "poi-compact-proof",
        "poi_state_hash_sha256": "a" * 64,
        "poi_state_source_boundary": (
            "closed_market_state_candles_asof_decision_no_postdecision_path"
        ),
        "poi_state_asof_utc": "2026-05-14T01:15:00+00:00",
    }

    row = harness.compact_missed_opportunity_rows(
        [
            {
                "candidate_id": "poi-compact-candidate",
                "decision_time_utc": "2026-05-14T01:15:00+00:00",
                "symbol": "GER40",
                "side": "SHORT",
                "poi_state_required": True,
                "poi_id": poi_state["poi_id"],
                "poi_state": poi_state,
                "poi_state_hash_sha256": poi_state["poi_state_hash_sha256"],
            }
        ]
    )[0]

    assert row["poi_state_required"] is True
    assert row["poi_id"] == "poi-compact-proof"
    assert row["poi_state"] == poi_state
    assert row["poi_state_hash_sha256"] == "a" * 64
    assert row["poi_state_transfer_status"] == timewarp.POI_STATE_TRANSFER_STATUS


def test_compact_missed_opportunity_preserves_one_atomic_nested_and_flat_authority() -> None:
    harness = load_broad_replay_harness()
    source = _signed_compact_missed_source(
        candidate_id="compact-missed-atomic",
        selector_reason="compact_missed_atomic_authority_fixture",
    )

    row = harness.compact_missed_opportunity_rows([source])[0]
    authority_field = row["package_new_entry_authority_authority_field"]
    nested = row[authority_field]

    assert row["missed_opportunity_authority_envelope_status"] == "atomic_complete"
    assert row["missed_opportunity_signed_authority_payload_preserved"] is True
    assert row[f"{authority_field}_payload_omitted"] is False
    assert row["package_replay_executable_candidate_use_allowed"] is True
    assert row["package_replay_order_executable_candidate_use_allowed"] is True
    assert row["replay_candidate_use_allowed_now"] is True
    assert timewarp.package_new_entry_authority_immutable_payload_failures(row) == []
    assert timewarp.package_new_entry_authority_immutable_payload_failures(nested) == []
    for field in harness.PACKAGE_NEW_ENTRY_AUTHORITY_ATOMIC_FLAT_FIELDS:
        if field in row or field in nested:
            assert row.get(field) == nested.get(field), field

    serialized = json.dumps(row, sort_keys=True, default=str)
    round_tripped = json.loads(serialized)
    expected_digest = row["missed_opportunity_authority_envelope_digest_sha256"]
    assert row["missed_opportunity_authority_envelope_round_trip_verified"] is True
    assert row[
        "missed_opportunity_authority_envelope_round_trip_digest_sha256"
    ] == expected_digest
    assert (
        harness.compact_missed_authority_envelope_digest_sha256(round_tripped)
        == expected_digest
    )


def test_compact_missed_opportunity_rejects_mixed_complete_authority_envelopes() -> None:
    harness = load_broad_replay_harness()
    source = _signed_compact_missed_source(
        candidate_id="compact-missed-mixed",
        selector_reason="compact_missed_outer_authority",
    )
    conflicting = _signed_compact_missed_source(
        candidate_id="compact-missed-mixed",
        selector_reason="compact_missed_conflicting_scheduler_authority",
    )
    source["scheduler_candidate_decision_inputs"] = conflicting[
        "scheduler_candidate_decision_inputs"
    ]

    row = harness.compact_missed_opportunity_rows([source])[0]

    assert row["missed_opportunity_authority_envelope_status"] == "fail_closed"
    assert row["missed_opportunity_authority_envelope_failure_reason"] == (
        "compact_missed_conflicting_complete_authority_envelopes"
    )
    assert row["missed_opportunity_signed_authority_payload_preserved"] is False
    assert row[
        "missed_opportunity_authority_envelope_mixed_reconstruction_allowed"
    ] is False
    assert row["package_replay_candidate_use_allowed"] is False
    assert row["package_replay_executable_candidate_use_allowed"] is False
    assert row["package_replay_order_executable_candidate_use_allowed"] is False
    assert row["replay_candidate_use_allowed_now"] is False
    assert "package_new_entry_authority_payload" not in row
    assert "ultimate_candidate_package_open_reduced_risk_authority" not in row


def test_compact_missed_opportunity_promotes_finalizer_ladder_risk_scalars() -> None:
    harness = load_broad_replay_harness()

    rows = harness.compact_missed_opportunity_rows(
        [
            {
                "candidate_id": "ladder-risk-candidate",
                "decision_time_utc": "2026-05-13T08:00:00+00:00",
                "symbol": "BTCUSD",
                "side": "LONG",
                "order_status": "not_sent_missed_opportunity",
                "effective_selector_action": "open-reduced-risk",
                "risk_authority": {
                    "schema_version": "runtime_risk_authority_packet_v1",
                    "packet_hash_sha256": "risk-hash",
                },
                "finalizer_primary_probe_risk_expression_ladder": {
                    "schema_version": "package_risk_expression_ladder_v1",
                    "requested_risk_pct": 0.25,
                    "approved_risk_pct": 0.10,
                    "ladder_tier": "reduced",
                    "tier_causes": ["execution_fillability_below_full_risk_floor"],
                },
            }
        ]
    )

    assert len(rows) == 1
    row = rows[0]
    assert row["selected_cell_risk_pct"] == 0.25
    assert row["scheduler_approved_risk_pct"] == 0.10
    assert row["final_approved_risk_pct"] == 0.10
    assert row["sizing_haircut_applied"] is True
    assert row["sizing_haircut_factor"] == 0.4
    assert row["sizing_haircut_reason"] == (
        "approved_risk_pct_below_selected_cell_risk_pct"
    )


def test_compact_missed_opportunity_preserves_scalar_risk_authority() -> None:
    harness = load_broad_replay_harness()

    [row] = harness.compact_missed_opportunity_rows(
        [
            {
                "candidate_id": "scalar-risk-authority-candidate",
                "decision_time_utc": "2026-05-13T08:00:00+00:00",
                "symbol": "XAUUSD",
                "side": "LONG",
                "order_status": "not_sent_missed_opportunity",
                "risk_authority": "pre_scheduler_risk_authority_materialized",
                "risk_authority_packet_hash_sha256": "risk-hash",
            }
        ]
    )

    assert row["risk_authority"] == (
        "pre_scheduler_risk_authority_materialized"
    )
    assert row["risk_authority_flattened_from"] == "risk_authority_scalar"
    assert "risk_authority_payload_omitted" not in row


def test_result_ledgers_promote_effective_selector_action_without_cost_backfill() -> None:
    harness = load_broad_replay_harness()
    base_row = {
        "candidate_id": "candidate-signed-authority",
        "candidate_id_source": "candidate_id",
        "decision_time_utc": "2026-05-13T08:00:00+00:00",
        "canonical_replay_candidate_instance_key": (
            "candidate-signed-authority@@2026-05-13T08:00:00+00:00"
        ),
        "source_bound_replay_candidate_instance_key": (
            "candidate-signed-authority@@2026-05-13T08:00:00+00:00"
        ),
        "candidate_instance_identity_status": "materialized",
        "trading_day": "2026-05-13",
        "symbol": "XAUUSD",
        "side": "LONG",
        "selector_action": "reject",
        "selector_reason": "router_refusal",
        "scheduler_materialization_selector_action": "open-reduced-risk",
        "scheduler_materialization_selector_reason": (
            "ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay"
        ),
        "scheduler_materialization_action_intent": "new_position",
        "source_bound_package_candidate_use_allowed": True,
        "cost_authority": "broker_calibrated_replay_cost",
        "execution_cost_authority": "broker_pretrade_cost_only",
        "package_replay_order_executable_candidate_use_allowed": True,
        "package_replay_order_executable_candidate_use_allowed_reason": (
            "package_candidate_and_signed_new_entry_authority_executable"
        ),
        "package_replay_order_executable_authority_source": (
            "package_replay_executable_and_signed_new_entry_authority"
        ),
        "risk_authority": {
            "schema_version": "runtime_risk_authority_packet_v1",
            "packet_hash_sha256": "risk-hash",
            "risk_config_source": "unit_fixture",
            "risk_per_trade_pct": 0.25,
            "selected_cell_risk_pct": 0.25,
            "approved_risk_pct": 0.25,
        },
    }
    authority = _complete_test_authority_surface(
        base_row,
        selector_action="open-reduced-risk",
        selector_reason=(
            "ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay"
        ),
        action_intent="new_position",
        authority={
            "applies": True,
            "allowed": True,
            "authority_family": "result_ledger_unit_test",
            "authority_source": "scheduler_candidate_decision_inputs",
            "source_boundary": (
                "predecision_result_ledger_unit_test_no_outcome_fields"
            ),
        },
    )
    base_row["scheduler_candidate_decision_inputs"] = {
        **authority,
        "ultimate_candidate_package_open_reduced_risk_authority": dict(authority),
    }
    authority_hash = authority["package_new_entry_authority_hash_sha256"]

    for row_type in ("simulated_order", "simulated_trade", "missed_opportunity"):
        result_row = dict(base_row)
        result_row["simulated_order_id"] = f"order-{row_type}"
        result_row["order_status"] = (
            "filled" if row_type == "simulated_trade" else "pending_accepted"
        )
        if row_type == "simulated_trade":
            result_row["simulated_trade_id"] = "trade-simulated-trade"
            result_row["fill_status"] = "filled_ordered_tick_entry_touch"
        row = harness.annotate_rows(
            [result_row],
            profile=harness.PROFILE_REPAIRED,
            split="development",
            chunk_id="unit",
            row_type=row_type,
        )[0]

        assert row["selector_action_origin"] == "reject"
        assert row["selector_reason_origin"] == "router_refusal"
        assert row["selector_action"] == "reject"
        assert row["effective_selector_action"] == "open-reduced-risk"
        assert row["effective_selector_reason"] == (
            "ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay"
        )
        assert row["package_new_entry_authority_hash_sha256"] == authority_hash
        assert row["package_replay_order_executable_candidate_use_allowed"] is True
        assert row["package_replay_order_executable_candidate_use_allowed_reason"] == (
            "package_candidate_and_signed_new_entry_authority_executable"
        )
        assert row["package_replay_order_executable_authority_source"] == (
            "package_replay_executable_and_signed_new_entry_authority"
        )
        assert row["risk_authority"]["schema_version"] == (
            "runtime_risk_authority_packet_v1"
        )
        assert row["admission_risk_class"] == "open-reduced-risk"
        assert row["sizing_haircut_applied"] is False
        assert row["cost_authority"] == "broker_calibrated_replay_cost"
        assert row["execution_cost_authority"] == "broker_pretrade_cost_only"
        assert "broker_pretrade_cost_executable" not in row


def test_missed_opportunity_selector_truth_does_not_promote_executable_authority() -> None:
    harness = load_broad_replay_harness()

    row = harness.annotate_rows(
        [
            {
                "candidate_id": "candidate-missed",
                "decision_time_utc": "2026-05-13T08:00:00+00:00",
                "trading_day": "2026-05-13",
                "symbol": "XAUUSD",
                "side": "LONG",
                "selector_action": "reject",
                "selector_reason": "router_refusal",
                "scheduler_materialization_selector_action": "open-reduced-risk",
                "scheduler_materialization_selector_reason": (
                    "ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay"
                ),
                "package_replay_executable_candidate_use_allowed": False,
                "replay_candidate_use_allowed_now": False,
            }
        ],
        profile=harness.PROFILE_REPAIRED,
        split="development",
        chunk_id="unit",
        row_type="missed_opportunity",
    )[0]

    assert row["selector_action"] == "reject"
    assert row["effective_selector_action"] == "open-reduced-risk"
    assert row["package_replay_executable_candidate_use_allowed"] is False
    assert row["replay_candidate_use_allowed_now"] is False


def test_source_required_lifecycle_resolver_alias_counts_as_replay_override() -> None:
    row = {
        "source_required_lifecycle_resolver_replay_override_applied": True,
        "scheduler_materialization_override_reason": (
            "replay_lifecycle_action_resolver_same_direction_scale_in"
        ),
    }

    assert source_required_replay_override_applied(row) is True
    assert source_required_replay_override_kind(row) == "replay_lifecycle_action_resolver"


def test_repaired_profile_routes_marketable_package_entries_only_in_no_broker_replay() -> None:
    harness = load_broad_replay_harness()
    config = harness.build_config(harness.PROFILE_REPAIRED)
    runtime = config["gtos_vnext_runtime"]
    replay = config["broad_live_as_if_replay_harness"]

    assert runtime["scheduler_v4_best_trade_allocator_package_marketable_entry_guard_enabled"]
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_replay_route_allowed"
        ]
        is True
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_replay_route_min_scheduler_score"
        ]
        == 3.0
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_immediate_marketable_opening_quality_floor_release_enabled"
        ]
        is True
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_immediate_marketable_limit_min_scheduler_score"
        ]
        == 1.0
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_replay_route_min_fill_probability"
        ]
        == 0.80
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_router_refusal_immediate_marketable_limit_replay_authority_enabled"
        ]
        is True
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_router_refusal_derived_immediate_marketable_limit_replay_authority_enabled"
        ]
        is True
    )
    assert replay["live_broker_authority"] is False
    assert replay["broker_mutation_enabled"] is False
    assert replay["final_selection_claim"] is False
    assert runtime["ultimate_candidate_package_live_activation_allowed"] is False
    assert runtime["ultimate_candidate_package_final_package_selected"] is False
    assert_package_rank_boost_replay_authority_enabled(runtime)
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_ultimate_package_rank_boost_source_boundary"
        ]
        == "predecision_package_membership_selector_shadow_source_r_and_broker_cost_"
        "authority_no_outcome_fields_no_live_broker_authority"
    )
    assert "package rank boost" in runtime[
        "scheduler_v4_best_trade_allocator_ultimate_package_rank_boost_repair_reason"
    ]
    assert (
        runtime[
            "ultimate_candidate_package_positive_predecision_router_refusal_full_trade_allowed"
        ]
        is True
    )
    assert (
        runtime[
            "ultimate_candidate_package_numeric_disagreement_open_reduced_risk_enabled"
        ]
        is False
    )
    assert "default-off" in runtime[
        "ultimate_candidate_package_numeric_disagreement_open_reduced_risk_demotion_reason"
    ]
    assert (
        runtime["ultimate_candidate_package_soften_selector_fill_floor_enabled"]
        is False
    )
    assert "V114C_B3" in runtime[
        "ultimate_candidate_package_soften_selector_fill_floor_repair_reason"
    ]
    assert (
        runtime[
            "ultimate_candidate_package_soften_selector_fill_floor_requires_broker_cost_pass"
        ]
        is True
    )
    assert (
        runtime[
            "ultimate_candidate_package_soften_selector_fill_floor_requires_positive_predecision_edge"
        ]
        is True
    )
    assert runtime["selector_v4_package_session_token_authority_enabled"] is True
    assert (
        runtime[
            "ultimate_candidate_package_positive_predecision_off_session_softening_enabled"
        ]
        is False
    )
    assert (
        runtime[
            "ultimate_candidate_package_positive_predecision_off_session_min_expected_net_r"
        ]
        == 0.80
    )
    assert (
        runtime[
            "ultimate_candidate_package_positive_predecision_off_session_min_probability"
        ]
        == 0.75
    )
    assert (
        runtime[
            "ultimate_candidate_package_positive_predecision_off_session_min_fill_probability"
        ]
        == 0.70
    )
    assert runtime["selector_v4_dynamic_router_refusal_action"] == "reject"
    assert runtime["broad_live_as_if_replay_pretrade_swap_cost_time_stop_bars"] == 32
    assert runtime["selected_cell_swap_cost_time_stop_bars"] == 32
    assert runtime["ultimate_candidate_package_soften_dynamic_router_refusal_enabled"] is True
    assert (
        runtime[
            "ultimate_candidate_package_soften_dynamic_router_refusal_requires_broker_cost_pass"
        ]
        is True
    )
    allowed_router_refusal_families = runtime[
        "ultimate_candidate_package_dynamic_router_refusal_softening_allowed_origin_families"
    ]
    scheduler_allowed_router_refusal_families = runtime[
        "scheduler_v4_best_trade_allocator_package_soft_authority_router_refusal_allowed_origin_families"
    ]
    assert "session_open_range_break" in allowed_router_refusal_families
    assert "session_open_range_break" in scheduler_allowed_router_refusal_families
    assert set(allowed_router_refusal_families) == set(
        scheduler_allowed_router_refusal_families
    )
    assert runtime["selector_v4_calibrated_admission_floor_failure_action"] == "reject"
    assert runtime["selector_v4_admission_quality_exact_block_rules_mode"] == "diagnostic"
    assert (
        runtime[
            "ultimate_candidate_package_broker_net_gradient_open_reduced_risk_enabled"
        ]
        is False
    )
    assert "default-off" in runtime[
        "ultimate_candidate_package_broker_net_gradient_open_reduced_risk_demotion_reason"
    ]
    assert "exact-block rows" in runtime[
        "selector_v4_admission_quality_exact_block_rules_mode_source"
    ]
    assert runtime["selector_v4_repaired_profile_soft_fail_status"] == (
        "dynamic_router_refusal_softens_to_reduced_risk_for_package_admitted_broker_cost_passed_rows"
    )
    assert runtime["profit_harvest_mfe_capture_v4_enabled"] is True
    assert runtime["profit_harvest_mfe_capture_v4_composition_mode"] == (
        "selected_policy_only"
    )
    assert runtime[
        "profit_harvest_mfe_capture_v4_selected_policy_only_policy_names"
    ] == ["momentum_exhaustion"]
    assert runtime["ultimate_candidate_package_registry_path"].endswith(
        "ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl"
    )
    assert runtime["selector_v4_dynamic_router_refusal_action"] == "reject"
    assert runtime["ultimate_candidate_package_soften_dynamic_router_refusal_enabled"] is True
    assert (
        runtime[
            "ultimate_candidate_package_soften_dynamic_router_refusal_requires_broker_cost_pass"
        ]
        is True
    )
    assert runtime["selector_v4_package_session_token_authority_enabled"] is True
    assert runtime["selector_v4_admission_quality_exact_block_rules_mode"] == "diagnostic"
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_risk_admitted_finalizer_allow_reallocation"
        ]
        is True
    )
    assert runtime["selected_cell_swap_cost_time_stop_bars"] == 32
    assert runtime["profit_harvest_mfe_capture_v4_min_mfe_r"] == 0.50
    assert runtime["profit_harvest_mfe_capture_v4_stop_activation_mfe_r"] == 0.50
    assert runtime["profit_harvest_mfe_capture_v4_target_activation_fraction"] == 0.75
    assert runtime["profit_harvest_mfe_capture_v4_trail_gap_r"] == 0.35
    assert runtime["profit_harvest_mfe_capture_v4_allow_m1_proxy_final_r_authority"] is True
    assert (
        runtime["profit_harvest_mfe_capture_v4_m1_proxy_final_r_authority_source"]
        == "owner_approved_reconstructed_proxy_replay_authority_m1_ordered_path_not_live"
    )
    assert runtime["profit_harvest_mfe_capture_v4_min_hold_minutes_before_stop_raise"] == 0
    assert runtime["replay_order_fillability_policy_v1_min_candidate_probability"] == 0.58
    assert (
        runtime[
            "replay_order_fillability_policy_v1_min_candidate_expected_net_r_after_fallback"
        ]
        == 0.40
    )
    assert (
        runtime["replay_order_fillability_policy_v1_min_fill_probability"]
        == 0.60
    )
    assert (
        runtime[
            "replay_order_fillability_policy_v1_min_order_fillability_probability_for_fallback"
        ]
        == 0.35
    )
    assert (
        runtime[
            "replay_order_fillability_policy_v1_package_min_order_fillability_probability_for_fallback"
        ]
        == 0.35
    )
    assert (
        runtime[
            "replay_order_fillability_policy_v1_max_limit_fill_probability_for_fallback"
        ]
        == 0.85
    )
    assert (
        runtime[
            "replay_order_fillability_policy_v1_allow_high_fill_probability_after_unfilled_probe"
        ]
        is False
    )
    assert (
        runtime[
            "replay_order_fillability_policy_v1_defer_predecision_distance_block_to_fallback_path"
        ]
        is True
    )
    assert (
        runtime[
            "replay_order_fillability_policy_v1_passive_limit_too_close_guard_enabled"
        ]
        is True
    )
    assert (
        runtime[
            "replay_order_fillability_policy_v1_passive_limit_min_distance_to_limit_risk"
        ]
        == 1.25
    )
    assert (
        runtime[
            "replay_order_fillability_policy_v1_passive_limit_min_distance_to_limit_atr"
        ]
        == 0.50
    )
    assert (
        runtime[
            "replay_order_fillability_policy_v1_passive_limit_max_fill_probability"
        ]
        == 0.64
    )
    assert (
        runtime[
            "replay_order_fillability_policy_v1_allow_open_reduced_risk_guarded_market_fallback"
        ]
        is True
    )
    assert (
        runtime[
            "replay_order_fillability_policy_v1_allow_off_configured_session_guarded_market_fallback"
        ]
        is False
    )
    assert "V111_19d_comparator" in runtime[
        "replay_order_fillability_policy_v1_repaired_profile_guarded_market_fallback_route_reason"
    ]
    assert runtime["replay_order_fillability_policy_v1_max_adverse_entry_drift_r"] == 0.75
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_risk_admitted_finalizer_allow_reallocation"
        ]
        is True
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_risk_admitted_finalizer_allow_zero_trade_conversion"
        ]
        is True
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_adaptive_replay_memory_guard_allow_session_origin_side_axis"
        ]
        is False
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_adaptive_replay_memory_guard_allow_origin_side_axis"
        ]
        is False
    )
    assert "session_origin_side" in runtime[
        "scheduler_v4_best_trade_allocator_adaptive_replay_memory_guard_axis_scope_reason"
    ]
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_authority_enabled"
        ]
        is True
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_package_lifecycle_scale_in_allow_no_new_position_comparator_authority"
        ]
        is True
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_package_lifecycle_scale_in_no_comparator_min_expected_net_r"
        ]
        == 1.0
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_package_lifecycle_scale_in_no_comparator_min_fill_probability"
        ]
        == 0.25
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_package_lifecycle_scale_in_allocation_comparator_enabled"
        ]
        is True
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_package_lifecycle_scale_in_allocation_transfer_ratio_floor"
        ]
        == 0.90
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_source_bound_router_refusal_replay_materialization_min_expected_net_r"
        ]
        == 0.55
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_source_bound_router_refusal_replay_materialization_min_probability"
        ]
        == 0.70
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_source_bound_router_refusal_replay_materialization_min_fill_probability"
        ]
        == 0.55
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_source_bound_router_refusal_replay_materialization_min_source_completeness"
        ]
        == 0.95
    )
    assert (
        runtime[
            "ultimate_candidate_package_source_bound_router_refusal_open_reduced_materialization_enabled"
        ]
        is True
    )
    assert (
        runtime[
            "ultimate_candidate_package_source_bound_router_refusal_materialization_min_expected_net_r"
        ]
        == 0.55
    )
    assert (
        runtime[
            "ultimate_candidate_package_source_bound_router_refusal_materialization_min_probability"
        ]
        == 0.70
    )
    assert (
        runtime[
            "ultimate_candidate_package_source_bound_router_refusal_materialization_min_fill_probability"
        ]
        == 0.55
    )
    assert "broker_cost_passed_source_complete_positive_router_refusal" in runtime[
        "ultimate_candidate_package_source_bound_router_refusal_materialization_reason"
    ]
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_bypass_enabled"
        ]
        is True
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_bypass_selector_trade_only"
        ]
        is False
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_authority_bypass_enabled"
        ]
        is True
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_authority_bypass_selector_trade_only"
        ]
        is False
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_authority_bypass_min_scheduler_score"
        ]
        == 0.0
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_authority_bypass_min_expected_net_r"
        ]
        == 0.75
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_authority_bypass_min_fill_probability"
        ]
        == 0.45
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_authority_bypass_min_source_completeness"
        ]
        == 0.65
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_authority_bypass_namespace_status"
        ]
        == "authoritative_namespace_only_legacy_dynamic_budget_package_fill_floor_bypass_removed"
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_execution_drag_penalty_enabled"
        ]
        is True
    )
    assert runtime["replay_order_fillability_policy_v1_enabled"] is True
    assert (
        runtime[
            "replay_order_fillability_policy_v1_require_package_execution_policy"
        ]
        is True
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_immediate_marketable_limit_allowed"
        ]
        is True
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_immediate_marketable_limit_max_expected_cost_r"
        ]
        == 0.10
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_immediate_marketable_limit_tick_floor_cost_ceiling_enabled"
        ]
        is True
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_immediate_marketable_limit_tick_floor_cost_ceiling_multiplier"
        ]
        == 1.25
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_immediate_marketable_opening_quality_floor_release_enabled"
        ]
        is True
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_immediate_marketable_limit_min_scheduler_score"
        ]
        == 1.0
    )
    assert config["broad_live_as_if_replay_harness"]["live_broker_authority"] is False
    assert config["broad_live_as_if_replay_harness"]["broker_mutation_enabled"] is False
    assert config["broad_live_as_if_replay_harness"]["final_selection_claim"] is False
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_order_cap_release_enabled"
        ]
        is True
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_daily_order_cap_release_enabled"
        ]
        is True
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_decision_time_order_cap_release_enabled"
        ]
        is True
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_opening_quality_floor_release_enabled"
        ]
        is False
    )
    assert "package-qualified" in runtime[
        "scheduler_v4_best_trade_allocator_dynamic_budget_package_order_cap_release_reason"
    ]
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_package_opposite_side_close_reverse_enabled"
        ]
        is True
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_package_opposite_side_close_reverse_lifecycle_reconcile_enabled"
        ]
        is True
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_package_opposite_side_close_reverse_router_refusal_lifecycle_reconcile_enabled"
        ]
        is True
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_package_opposite_side_close_reverse_router_refusal_lifecycle_reconcile_min_expected_net_r"
        ]
        == 0.55
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_release_risk_cap_enabled"
        ]
        is True
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_release_max_risk_pct"
        ]
        == 0.25
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_authority_bypass_enabled"
        ]
        is True
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_authority_bypass_min_fill_probability"
        ]
        == 0.45
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_source_required_fail_closed_package_replay_override_enabled"
        ]
        is True
    )
    assert "replay-only package authority" in runtime[
        "scheduler_v4_best_trade_allocator_source_required_fail_closed_package_replay_override_reason"
    ]
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_source_required_fail_closed_package_replay_override_min_expected_net_r"
        ]
        == 0.75
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_source_required_fail_closed_package_replay_override_min_probability"
        ]
        == 0.75
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_source_required_fail_closed_package_replay_override_min_fill_probability"
        ]
        == 0.12
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_source_required_fail_closed_package_replay_override_allow_new_position_without_same_side_context_enabled"
        ]
        is False
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_source_required_selector_hold_package_replay_override_enabled"
        ]
        is False
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_source_required_selector_hold_package_replay_override_min_expected_net_r"
        ]
        == 0.60
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_source_required_selector_hold_package_replay_override_min_probability"
        ]
        == 0.72
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_source_required_selector_hold_package_replay_override_min_fill_probability"
        ]
        == 0.90
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_source_required_package_duplicate_scale_in_enabled"
        ]
        is True
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_source_required_package_duplicate_scale_in_min_expected_net_r"
        ]
        == 0.75
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_source_required_package_duplicate_scale_in_min_fill_probability"
        ]
        == 0.12
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_source_required_package_risk_lifecycle_reconcile_enabled"
        ]
        is True
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_source_required_package_risk_lifecycle_reconcile_min_scheduler_score"
        ]
        == 2.50
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_source_required_package_risk_lifecycle_reconcile_min_expected_net_r"
        ]
        == 0.75
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_source_required_package_risk_lifecycle_reconcile_min_fill_probability"
        ]
        == 0.12
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_package_same_direction_scale_in_lifecycle_reconcile_enabled"
        ]
        is True
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_package_same_direction_scale_in_lifecycle_reconcile_min_expected_net_r"
        ]
        == 0.75
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_package_same_direction_scale_in_lifecycle_reconcile_min_fill_probability"
        ]
        == 0.12
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_allow_window_headroom_reduced_new_entries"
        ]
        is True
    )
    assert "sized to the remaining" in runtime[
        "scheduler_v4_best_trade_allocator_window_headroom_reduced_new_entry_policy_reason"
    ]
    assert runtime["selected_cell_pretrade_max_spread_r"] == 0.35
    assert runtime["selected_cell_pretrade_max_total_cost_r"] == 0.45
    owner_root = runtime[
        "ultimate_candidate_package_owner_approved_family_root_admission"
    ]
    assert owner_root == {
            "policy_id": "owner_xau_displacement_short_family_root_v1",
            "symbol": "XAUUSD",
            "side": "SHORT",
            "origin_family": "displacement_continuation",
            "required_sleeve_id": (
                "fpsc_scheduler_lifecycle_merge_sleeve__broader_origin__"
                "displacement_continuation__short"
            ),
            "required_registry_row_sha256": (
                "3dbe5a25b5ca98140881dd204b5189d0c032ba565c6ea9690ee3715fc7b99005"
            ),
            "required_package_role": "scheduler_lifecycle_core",
            "research_only": True,
            "live_broker_authority": False,
            "uses_outcome_fields": False,
        }
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_package_cooldown_release_allow_same_symbol_daily_loss_lockout"
        ]
        is False
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_package_cooldown_release_allow_same_symbol_daily_loss_lockout_for_package_quality"
        ]
        is False
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_package_cooldown_release_allow_same_symbol_daily_loss_lockout_for_fill_floor_authority"
        ]
        is True
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_package_cooldown_release_allow_same_symbol_daily_loss_lockout_for_router_refusal_authority"
        ]
        is True
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_package_cooldown_release_allow_same_symbol_daily_loss_lockout_for_signed_executable_package_authority"
        ]
        is True
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_package_cooldown_release_fill_floor_authority_min_fill_probability"
        ]
        == 0.45
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_opening_risk_cap_release_enabled"
        ]
        is True
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_opening_risk_cap_release_max_risk_pct"
        ]
        == 0.25
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_immediate_marketable_limit_allowed"
        ]
        is True
    )
    assert (
        runtime.get(
            "replay_order_fillability_policy_v1_allow_open_reduced_risk_guarded_market_fallback",
            False,
        )
        is True
    )
    assert (
        runtime[
            "replay_order_fillability_policy_v1_defer_predecision_distance_block_to_fallback_path"
        ]
        is True
    )
    assert (
        runtime[
            "replay_order_fillability_policy_v1_allow_off_configured_session_guarded_market_fallback"
        ]
        is False
    )
    assert runtime["replay_order_fillability_policy_v1_max_adverse_entry_drift_r"] == 0.75
    assert "0.25R rescue calibration" in runtime[
        "profit_harvest_mfe_capture_v4_repair_reason"
    ]


def test_repaired_profile_forwards_window_headroom_policy_to_scheduler() -> None:
    harness = load_broad_replay_harness()
    config = harness.build_config(harness.PROFILE_REPAIRED)
    scheduler = timewarp.scheduler_config(config)

    assert scheduler["allow_window_headroom_reduced_new_entries"] is True
    assert scheduler["selector_reduce_risk_package_fill_floor_authority_enabled"] is True
    assert scheduler["dynamic_budget_package_fill_floor_bypass_enabled"] is True
    assert scheduler["dynamic_budget_package_fill_floor_bypass_selector_trade_only"] is False
    assert scheduler["dynamic_budget_package_fill_floor_authority_bypass_enabled"] is True
    assert (
        scheduler["dynamic_budget_package_fill_floor_authority_bypass_min_scheduler_score"]
        == 0.0
    )
    assert (
        scheduler["dynamic_budget_package_fill_floor_authority_bypass_min_source_completeness"]
        == 0.65
    )
    assert (
        scheduler["dynamic_budget_package_fill_floor_authority_bypass_min_fill_probability"]
        == 0.45
    )
    assert (
        scheduler["dynamic_budget_package_fill_floor_bypass_min_execution_fill_probability"]
        == 0.35
    )
    assert scheduler["source_required_fail_closed_package_replay_override_enabled"] is True
    assert scheduler["source_required_selector_hold_package_replay_override_enabled"] is False
    assert scheduler["source_required_package_duplicate_scale_in_enabled"] is True
    assert scheduler["package_opposite_side_close_reverse_enabled"] is True
    assert (
        scheduler[
            "package_opposite_side_close_reverse_router_refusal_lifecycle_reconcile_enabled"
        ]
        is True
    )
    assert (
        scheduler[
            "package_opposite_side_close_reverse_router_refusal_lifecycle_reconcile_min_probability"
        ]
        == 0.70
    )
    assert scheduler["package_opposite_side_pending_collision_min_edge_delta"] == 0.0
    assert scheduler["package_marketable_entry_guard_immediate_marketable_limit_allowed"] is True
    assert (
        scheduler[
            "package_marketable_entry_guard_router_refusal_immediate_marketable_limit_replay_authority_enabled"
        ]
        is True
    )
    assert (
        scheduler[
            "package_marketable_entry_guard_router_refusal_derived_immediate_marketable_limit_replay_authority_enabled"
        ]
        is True
    )
    assert (
        scheduler[
            "package_marketable_entry_guard_immediate_marketable_limit_min_scheduler_score"
        ]
        == 1.0
    )
    assert (
        scheduler[
            "package_marketable_entry_guard_immediate_marketable_limit_max_expected_cost_r"
        ]
        == 0.10
    )
    assert (
        scheduler[
            "package_marketable_entry_guard_immediate_marketable_limit_tick_floor_cost_ceiling_enabled"
        ]
        is True
    )
    assert (
        scheduler[
            "package_marketable_entry_guard_immediate_marketable_limit_tick_floor_cost_ceiling_multiplier"
        ]
        == 1.25
    )
    assert scheduler["package_marketable_entry_guard_replay_route_min_scheduler_score"] == 3.0
    assert (
        scheduler[
            "dynamic_budget_package_immediate_marketable_opening_quality_floor_release_enabled"
        ]
        is True
    )
    assert scheduler["replay_order_fillability_policy_v1_enabled"] is True
    assert (
        scheduler[
            "replay_order_fillability_policy_v1_allow_open_reduced_risk_guarded_market_fallback"
        ]
        is True
    )
    assert (
        scheduler[
            "replay_order_fillability_policy_v1_allow_passive_limit_queue_for_package_replay"
        ]
        is True
    )
    assert (
        scheduler[
            "replay_order_fillability_policy_v1_require_passive_limit_fallback_envelope"
        ]
        is True
    )
    assert (
        scheduler[
            "replay_order_fillability_policy_v1_passive_limit_queue_min_fill_probability"
        ]
        == 0.20
    )
    assert (
        scheduler[
            "selector_reduce_risk_package_fill_floor_execution_drag_min_fill_probability"
        ]
        == 0.80
    )
    assert scheduler["execution_fill_shortfall_score_penalty_weight"] == 2.50
    assert (
        scheduler[
            "replay_order_fillability_policy_v1_passive_limit_fallback_envelope_min_degraded_transfer_score"
        ]
        == 0.40
    )
    assert (
        scheduler[
            "replay_order_fillability_policy_v1_require_package_execution_policy"
        ]
        is True
    )
    assert scheduler["replay_order_fillability_policy_v1_max_adverse_entry_drift_r"] == 0.75
    assert scheduler["predecision_passive_limit_too_close_guard_enabled"] is True
    assert scheduler["predecision_passive_limit_too_close_guard_action"] == "block"
    assert scheduler["predecision_passive_limit_too_close_require_all_thresholds"] is True
    assert (
        scheduler["predecision_passive_limit_too_close_min_distance_to_limit_risk"]
        == 1.25
    )
    assert (
        scheduler["predecision_passive_limit_too_close_min_distance_to_limit_atr"]
        == 0.50
    )
    assert (
        scheduler["predecision_passive_limit_too_close_max_limit_fill_probability"]
        == 0.64
    )
    assert (
        scheduler["predecision_passive_limit_too_close_missing_fields_action"]
        == "no_block"
    )
    assert scheduler["predecision_stop_hazard_guard_enabled"] is True
    assert scheduler["predecision_stop_hazard_guard_action"] == "cap"
    assert scheduler["predecision_stop_hazard_require_all_thresholds"] is True
    assert scheduler["predecision_stop_hazard_min_unit_risk_atr"] == 0.35
    assert scheduler["predecision_stop_hazard_max_distance_to_limit_risk"] == 1.00
    assert scheduler["predecision_stop_hazard_min_limit_fill_probability"] == 0.50
    assert scheduler["predecision_stop_hazard_min_target_r"] == 1.50
    assert scheduler["predecision_stop_hazard_pressure_enabled"] is True
    assert scheduler["predecision_stop_hazard_pressure_min_score"] == 0.75
    assert scheduler["predecision_stop_hazard_pressure_distance_weight"] == 0.40
    assert scheduler["predecision_stop_hazard_pressure_fill_weight"] == 0.35
    assert scheduler["predecision_stop_hazard_pressure_target_weight"] == 0.25
    assert scheduler["predecision_stop_hazard_pressure_requires_base_fragility"] is True
    assert scheduler["predecision_stop_hazard_risk_cap_pct"] == 0.10
    assert scheduler["predecision_stop_hazard_score_penalty"] == 1.25
    assert scheduler["predecision_stop_hazard_missing_fields_action"] == "no_block"
    assert (
        scheduler[
            "replay_order_fillability_policy_v1_min_candidate_expected_net_r_after_fallback"
        ]
        == 0.40
    )
    assert scheduler["source_required_package_risk_lifecycle_reconcile_enabled"] is True
    assert (
        scheduler["package_same_direction_scale_in_lifecycle_reconcile_enabled"]
        is True
    )
    assert (
        scheduler["selector_reduce_risk_package_fill_floor_release_risk_cap_enabled"]
        is True
    )
    assert scheduler["selector_reduce_risk_package_fill_floor_release_max_risk_pct"] == 0.25
    assert (
        scheduler["source_required_fail_closed_package_replay_override_min_fill_probability"]
        == 0.12
    )
    assert scheduler["source_required_package_duplicate_scale_in_min_fill_probability"] == 0.12
    assert (
        scheduler["source_required_selector_hold_package_replay_override_min_fill_probability"]
        == 0.90
    )
    assert (
        scheduler["source_required_package_risk_lifecycle_reconcile_min_fill_probability"]
        == 0.12
    )
    assert (
        scheduler["package_same_direction_scale_in_lifecycle_reconcile_min_fill_probability"]
        == 0.12
    )
    assert scheduler["selector_reduce_risk_numeric_disagreement_min_expected_net_r"] == 1.0
    assert scheduler["selector_reduce_risk_numeric_disagreement_min_probability"] == 0.85
    assert (
        scheduler["selector_reduce_risk_cross_asset_lead_lag_soft_authority_enabled"]
        is False
    )
    assert (
        scheduler[
            "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk_allowed"
        ]
        is True
    )
    assert (
        scheduler["ultimate_candidate_package_numeric_disagreement_open_reduced_risk_enabled"]
        is False
    )
    assert scheduler["ultimate_candidate_package_soften_selector_fill_floor_enabled"] is False
    assert (
        scheduler["ultimate_candidate_package_broker_net_gradient_open_reduced_risk_enabled"]
        is False
    )
    assert scheduler["ultimate_candidate_package_strong_fill_floor_bypass_enabled"] is True
    assert (
        scheduler["ultimate_candidate_package_positive_predecision_off_session_softening_enabled"]
        is False
    )
    assert scheduler["package_soft_authority_displacement_quality_gate_enabled"] is True
    assert scheduler["package_soft_authority_displacement_require_primary_comparator"] is True
    assert (
        scheduler[
            "package_soft_authority_displacement_allow_no_primary_comparator_authority"
        ]
        is True
    )
    assert scheduler["package_soft_authority_displacement_min_edge_delta"] == 0.05
    assert (
        scheduler[
            "package_soft_authority_displacement_no_primary_min_edge_score"
        ]
        == 0.0
    )
    assert (
        scheduler[
            "package_replay_executable_authority_overrides_router_refusal_floors"
        ]
        is True
    )
    assert scheduler["same_window_executable_comparator_hard_dominance_enabled"] is True
    assert scheduler["same_window_executable_comparator_hard_dominance_min_delta"] == (
        0.000000001
    )


def test_scheduler_blocks_cross_asset_derived_router_refusal_without_explicit_authority() -> None:
    selector_reason = "source_bound_router_refusal_open_reduced_materialized_for_replay"
    result = scheduler.allocate_decision_window(
        {
            "decision_window_id": "cross-asset-derived-router-refusal",
            "candidate_set_id": "unit",
            "asof_utc": "2026-05-15T13:30:00+00:00",
            "candidates": [
                {
                    "candidate_id": "cross-asset-derived",
                    "symbol": "USDJPY",
                    "side": "LONG",
                    "decision_time_utc": "2026-05-15T13:30:00+00:00",
                    "action_intent": "new_position",
                    "requested_risk_pct": 0.1,
                    "selected_cell_risk_pct": 0.1,
                    "selector_action": "open-reduced-risk",
                    "selector_reason": selector_reason,
                    "origin_family": "cross_asset_lead_lag",
                    "candidate_origin_family": "origin_cross_asset_lead_lag",
                    "framework": "origin_cross_asset_lead_lag",
                    "expected_net_r": 1.18,
                    "probability": 0.93,
                    "fill_probability": 0.92,
                    "source_completeness": 1.0,
                    "pretrade_cost_packet_status": "PASSED",
                    "cost_authority": "broker_calibrated_replay_cost",
                    "cost_source_gap_status": "source_bound_cost_authority_present",
                    "candidate_cost_r_fallback_is_authority": False,
                    "expected_cost_r": 0.05,
                    "source_bound_package_candidate_use_allowed": True,
                    "ultimate_package_effective_source_bound_candidate_use_allowed": True,
                    "ultimate_package_effective_admission_count": 1,
                    "ultimate_package_effective_matched_count": 1,
                    "ultimate_package_admission_candidate_use_allowed": True,
                    "package_replay_candidate_use_allowed": True,
                    "package_replay_executable_candidate_use_allowed": True,
                    "package_open_reduced_authority_allowed": True,
                    "package_open_reduced_authority_family": "router_refusal_softening",
                    "package_new_entry_authority_required": True,
                    "package_new_entry_authority_valid": True,
                    "package_new_entry_authority_failures": [],
                    "ultimate_candidate_package_open_reduced_risk_authority": {
                        "allowed": True,
                        "applies": True,
                        "authority_family": "router_refusal_softening",
                        "authority_source": (
                            "derived_from_source_bound_router_refusal_package_authority"
                        ),
                        "current_config_allowed": True,
                        "explicit_positive_predecision_router_refusal_authority_present": False,
                        "source_boundary": (
                            "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
                        ),
                    },
                }
            ],
        },
        {
            "enabled": True,
            "apply_to_execution": True,
            "selector_reduce_risk_cross_asset_lead_lag_soft_authority_enabled": True,
            "package_soft_authority_displacement_quality_gate_enabled": False,
        },
    )

    option = next(
        opt
        for opt in result["all_options_preserved"]
        if opt.get("candidate_id") == "cross-asset-derived"
    )
    assert option["runtime_eligible"] is False
    assert any(
        "cross_asset_lead_lag_requires_explicit_predecision_authority" in veto
        for veto in option["vetoes"]
    )
    diagnostic = option["score_components"]["selector_reduce_risk_new_entry_authority"][
        "cross_asset_lead_lag_soft_authority"
    ]
    assert diagnostic["enabled"] is True
    assert diagnostic["explicit_predecision_authority_present"] is False
    assert diagnostic["block_reason"] == (
        "cross_asset_lead_lag_requires_explicit_predecision_authority"
    )


def test_broad_profiles_split_raw_diagnostic_from_executable_marketable_guard() -> None:
    harness = load_broad_replay_harness()

    raw_config = harness.build_config(harness.PROFILE_RAW)
    raw_runtime = raw_config["gtos_vnext_runtime"]
    raw_harness = raw_config["broad_live_as_if_replay_harness"]
    assert raw_harness["package_execution_result_scope"] == "raw_baseline_diagnostic_only"
    assert raw_harness["raw_baseline_diagnostic_only"] is True
    assert raw_harness["marketable_guard_profile"] is False
    assert raw_runtime["broad_live_as_if_replay_package_execution_result_scope"] == (
        "raw_baseline_diagnostic_only"
    )
    assert raw_runtime["replay_order_fillability_policy_v1_enabled"] is False
    assert (
        raw_runtime[
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_enabled"
        ]
        is False
    )
    assert (
        raw_runtime[
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_replay_route_allowed"
        ]
        is False
    )
    assert (
        raw_runtime[
            "broad_live_as_if_replay_owner_approved_reconstructed_proxy_selected_policy_expected_net_enabled"
        ]
        is False
    )
    assert (
        raw_runtime[
            "scheduler_v4_best_trade_allocator_selected_package_bridge_replay_materialization_enabled"
        ]
        is False
    )
    assert raw_runtime["selected_package_bridge_replay_materialization_enabled"] is False
    assert (
        raw_runtime[
            "selected_package_bridge_replay_materialization_live_broker_authority"
        ]
        is False
    )
    assert (
        raw_runtime["selected_package_bridge_replay_materialization_source_boundary"]
        == "closed_for_raw_guarded_comparator_profiles"
    )

    for profile, expected_scope in (
        (harness.PROFILE_GUARDED, "guarded_executable_package_replay"),
        (harness.PROFILE_REPAIRED, "repaired_executable_package_replay"),
    ):
        config = harness.build_config(profile)
        runtime = config["gtos_vnext_runtime"]
        route = config["broad_live_as_if_replay_harness"]
        assert route["package_execution_result_scope"] == expected_scope
        assert route["raw_baseline_diagnostic_only"] is False
        assert route["marketable_guard_profile"] is True
        assert runtime["broad_live_as_if_replay_package_execution_result_scope"] == (
            expected_scope
        )
        assert runtime["replay_order_fillability_policy_v1_enabled"] is True
        assert (
            runtime[
                "broad_live_as_if_replay_owner_approved_reconstructed_proxy_selected_policy_expected_net_enabled"
            ]
            is True
        )
        assert runtime[
            "broad_live_as_if_replay_owner_approved_reconstructed_proxy_selected_policy_expected_net_source_path"
        ].endswith("RECONSTRUCTED_PROXY_PACKAGE_SELECTION_SUMMARY.json")
        expected_bridge_enabled = profile == harness.PROFILE_REPAIRED
        assert (
            runtime[
                "scheduler_v4_best_trade_allocator_selected_package_bridge_replay_materialization_enabled"
            ]
            is expected_bridge_enabled
        )
        assert (
            runtime["selected_package_bridge_replay_materialization_enabled"]
            is expected_bridge_enabled
        )
        assert (
            runtime[
                "selected_package_bridge_replay_materialization_live_broker_authority"
            ]
            is False
        )
        if expected_bridge_enabled:
            assert (
                runtime[
                    "selected_package_bridge_replay_materialization_source_boundary"
                ]
                == (
                    "local_repaired_replay_only_strict_signed_predecision_bridge_"
                    "broker_live_final_closed_no_order_mutation"
                )
            )
            bridge_status = runtime["selected_package_bridge_replay_materialization_status"]
            assert "strict_bridge_contract" in bridge_status
            assert "broker/live/final false" in bridge_status
        else:
            assert (
                runtime[
                    "selected_package_bridge_replay_materialization_source_boundary"
                ]
                == "closed_for_raw_guarded_comparator_profiles"
            )
        source_hash = runtime[
            "broad_live_as_if_replay_owner_approved_reconstructed_proxy_selected_policy_expected_net_source_sha256"
        ]
        assert source_hash is None or len(source_hash) == 64
        assert source_hash == runtime[
            "broad_live_as_if_replay_owner_approved_reconstructed_proxy_selected_policy_expected_net_source_semantic_sha256"
        ]
        assert len(
            runtime[
                "broad_live_as_if_replay_owner_approved_reconstructed_proxy_selected_policy_expected_net_source_artifact_sha256"
            ]
        ) == 64
        assert runtime[
            "broad_live_as_if_replay_owner_approved_reconstructed_proxy_selected_policy_expected_net_source_contract_valid"
        ] is True
        assert runtime[
            "broad_live_as_if_replay_owner_approved_reconstructed_proxy_selected_policy_expected_net_source_contract_failure_reasons"
        ] == []
        assert (
            runtime[
                "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_enabled"
            ]
            is True
        )
        assert (
            runtime[
                "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_replay_route_allowed"
            ]
            is True
        )
        assert (
            runtime[
                "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_immediate_marketable_limit_allowed"
            ]
            is True
        )
        expected_no_comparator_scale_in = profile == harness.PROFILE_REPAIRED
        assert (
            runtime[
                "scheduler_v4_best_trade_allocator_package_lifecycle_scale_in_allow_no_new_position_comparator_authority"
            ]
            is expected_no_comparator_scale_in
        )
        assert (
            runtime[
                "scheduler_v4_best_trade_allocator_package_lifecycle_scale_in_allocation_comparator_enabled"
            ]
            is True
        )
        assert (
            runtime[
                "scheduler_v4_best_trade_allocator_package_lifecycle_scale_in_allocation_transfer_ratio_floor"
            ]
            == 0.90
        )
        if profile == harness.PROFILE_REPAIRED:
            assert (
                runtime[
                    "scheduler_v4_best_trade_allocator_package_lifecycle_scale_in_no_comparator_min_expected_net_r"
                ]
                == 1.0
            )
            assert (
                runtime[
                    "scheduler_v4_best_trade_allocator_package_lifecycle_scale_in_no_comparator_min_fill_probability"
                ]
                == 0.25
            )
            assert (
                runtime[
                    "replay_order_fillability_policy_v1_min_drift_adjusted_candidate_expected_net_r_after_fallback"
                ]
                == 0.50
            )
        assert (
            runtime[
                "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_immediate_marketable_limit_entry_quality_enabled"
            ]
            is True
        )
        assert (
            runtime[
                "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_immediate_marketable_limit_min_open_range_break_extension_atr"
            ]
            == 0.02
        )


def test_proxy_selection_source_contract_ignores_only_generated_metadata(
    tmp_path: Path,
) -> None:
    bridge = load_selected_package_replay_bridge()
    path = tmp_path / "selection-summary.json"
    payload = {
        "schema": bridge.RECONSTRUCTED_PROXY_PACKAGE_SELECTION_SUMMARY_SCHEMA,
        "generated_utc": "first",
        "packet_hash_sha256": "a" * 64,
        "status": "proxy_package_selected_for_local_replay_evaluation_final_live_closed",
        "proxy_package_selected_for_replay_evaluation": True,
        "owner_approved_proxy_package_selection": True,
        "local_replay_proxy_package_selection_allowed": True,
        "local_replay_proxy_package_selection_passed": True,
        "selected_package_scope": "full_82_sleeve_proxy_approved_replay_package",
        "live_trading_enabled": False,
        "broker_operation": False,
        "final_package_selected": False,
        "order_calls": 0,
        "nested": {
            "generated_utc": "nested-first",
            "economic_expected_net_r": 1.25,
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    first = bridge.reconstructed_proxy_package_selection_source_contract(path)

    payload["generated_utc"] = "timestamp-only-second-build"
    payload["packet_hash_sha256"] = "b" * 64
    payload["nested"]["generated_utc"] = "nested-second"
    path.write_text(json.dumps(payload), encoding="utf-8")
    timestamp_only = bridge.reconstructed_proxy_package_selection_source_contract(path)

    assert first["valid"] is True
    assert timestamp_only["valid"] is True
    assert first["source_artifact_sha256"] != timestamp_only["source_artifact_sha256"]
    assert first["source_semantic_sha256"] == timestamp_only["source_semantic_sha256"]

    payload["nested"]["economic_expected_net_r"] = 0.25
    path.write_text(json.dumps(payload), encoding="utf-8")
    economic_change = bridge.reconstructed_proxy_package_selection_source_contract(path)
    assert economic_change["valid"] is True
    assert (
        economic_change["source_semantic_sha256"]
        != timestamp_only["source_semantic_sha256"]
    )


def test_shared_execution_digest_excludes_raw_calibration_artifact_hash(
    monkeypatch,
) -> None:
    harness = load_broad_replay_harness()
    state = {
        "semantic": "a" * 64,
        "artifact": "b" * 64,
    }

    def source_contract(_path):
        return {
            "valid": True,
            "status": "semantic_calibration_source_bound",
            "source_path": (
                "research/operations/final_moonshot_ultimate_system_denominator_to_"
                "deployment_execution_2026_06_20/"
                "RECONSTRUCTED_PROXY_PACKAGE_SELECTION_SUMMARY.json"
            ),
            "source_semantic_sha256": state["semantic"],
            "source_artifact_sha256": state["artifact"],
            "semantic_digest_boundary": "canonical_semantic_projection",
            "semantic_digest_excluded_keys": [
                "generated_utc",
                "packet_hash_sha256",
            ],
            "source_summary_schema": "selection.summary.v1",
            "source_summary_status": "local_replay_selected",
            "failure_reasons": [],
        }

    monkeypatch.setattr(
        harness,
        "reconstructed_proxy_package_selection_source_contract",
        source_contract,
    )

    def shared_contract():
        return harness.broad_replay_shared_execution_contract(
            profiles=(harness.PROFILE_REPAIRED,),
            active_symbols=("XAUUSD",),
            execution_options={"unit_test": True},
            runtime_input_contract={"valid": True},
        )

    first = shared_contract()
    state["artifact"] = "c" * 64
    timestamp_only = shared_contract()
    assert (
        first["effective_profile_config_hashes"]
        == timestamp_only["effective_profile_config_hashes"]
    )
    assert (
        first["shared_execution_contract_digest_sha256"]
        == timestamp_only["shared_execution_contract_digest_sha256"]
    )

    state["semantic"] = "d" * 64
    economic_change = shared_contract()
    assert (
        economic_change["effective_profile_config_hashes"]
        != timestamp_only["effective_profile_config_hashes"]
    )
    assert (
        economic_change["shared_execution_contract_digest_sha256"]
        != timestamp_only["shared_execution_contract_digest_sha256"]
    )


def test_risk_finalizer_conversion_and_reallocation_are_repaired_profile_only() -> None:
    harness = load_broad_replay_harness()

    for profile in (harness.PROFILE_RAW, harness.PROFILE_GUARDED):
        runtime = harness.build_config(profile)["gtos_vnext_runtime"]
        assert (
            runtime[
                "scheduler_v4_best_trade_allocator_risk_admitted_finalizer_allow_zero_trade_conversion"
            ]
            is False
        )
        assert (
            runtime[
                "scheduler_v4_best_trade_allocator_risk_admitted_finalizer_allow_reallocation"
            ]
            is False
        )
        assert (
            runtime.get(
                "ultimate_candidate_package_source_bound_router_refusal_open_reduced_materialization_enabled",
                False,
            )
            is False
        )
        assert (
            runtime.get(
                "replay_order_fillability_policy_v1_allow_open_reduced_risk_guarded_market_fallback",
                False,
            )
            is False
        )
        assert (
            runtime[
                "replay_order_fillability_policy_v1_allow_off_configured_session_guarded_market_fallback"
            ]
            is False
        )
        assert (
            runtime[
                "replay_order_fillability_policy_v1_passive_limit_too_close_guard_enabled"
            ]
            is False
        )
        assert (
            runtime[
                "scheduler_v4_best_trade_allocator_predecision_passive_limit_too_close_guard_enabled"
            ]
            is False
        )
        assert (
            runtime[
                "scheduler_v4_best_trade_allocator_predecision_stop_hazard_guard_enabled"
            ]
            is False
        )

    repaired_runtime = harness.build_config(harness.PROFILE_REPAIRED)[
        "gtos_vnext_runtime"
    ]
    assert (
        repaired_runtime[
            "scheduler_v4_best_trade_allocator_risk_admitted_finalizer_allow_zero_trade_conversion"
        ]
        is True
    )
    assert (
        repaired_runtime[
            "scheduler_v4_best_trade_allocator_risk_admitted_finalizer_allow_reallocation"
        ]
        is True
    )
    assert (
        repaired_runtime[
            "replay_order_fillability_policy_v1_allow_open_reduced_risk_guarded_market_fallback"
        ]
        is True
    )
    assert (
        repaired_runtime[
            "replay_order_fillability_policy_v1_allow_off_configured_session_guarded_market_fallback"
        ]
        is False
    )
    assert (
        repaired_runtime[
            "replay_order_fillability_policy_v1_passive_limit_too_close_guard_enabled"
        ]
        is True
    )
    assert (
        repaired_runtime[
            "replay_order_fillability_policy_v1_passive_limit_too_close_require_all_thresholds"
        ]
        is True
    )
    assert (
        repaired_runtime[
            "replay_order_fillability_policy_v1_passive_limit_too_close_missing_fields_action"
        ]
        == "no_block"
    )
    assert (
        repaired_runtime[
            "replay_order_fillability_policy_v1_passive_limit_min_distance_to_limit_risk"
        ]
        == 1.25
    )
    assert (
        repaired_runtime[
            "replay_order_fillability_policy_v1_passive_limit_min_distance_to_limit_atr"
        ]
        == 0.50
    )
    assert (
        repaired_runtime[
            "replay_order_fillability_policy_v1_passive_limit_max_fill_probability"
        ]
        == 0.64
    )
    assert (
        repaired_runtime[
            "scheduler_v4_best_trade_allocator_predecision_passive_limit_too_close_guard_enabled"
        ]
        is True
    )
    assert (
        repaired_runtime[
            "scheduler_v4_best_trade_allocator_predecision_passive_limit_too_close_guard_action"
        ]
        == "block"
    )
    assert (
        repaired_runtime[
            "scheduler_v4_best_trade_allocator_predecision_passive_limit_too_close_require_all_thresholds"
        ]
        is True
    )
    assert (
        repaired_runtime[
            "scheduler_v4_best_trade_allocator_predecision_passive_limit_too_close_min_distance_to_limit_risk"
        ]
        == 1.25
    )
    assert (
        repaired_runtime[
            "scheduler_v4_best_trade_allocator_predecision_passive_limit_too_close_min_distance_to_limit_atr"
        ]
        == 0.50
    )
    assert (
        repaired_runtime[
            "scheduler_v4_best_trade_allocator_predecision_passive_limit_too_close_max_limit_fill_probability"
        ]
        == 0.64
    )
    assert (
        repaired_runtime[
            "scheduler_v4_best_trade_allocator_predecision_passive_limit_too_close_missing_fields_action"
        ]
        == "no_block"
    )
    assert (
        repaired_runtime[
            "scheduler_v4_best_trade_allocator_predecision_stop_hazard_guard_enabled"
        ]
        is True
    )
    assert (
        repaired_runtime[
            "scheduler_v4_best_trade_allocator_predecision_stop_hazard_guard_action"
        ]
        == "cap"
    )
    assert (
        repaired_runtime[
            "scheduler_v4_best_trade_allocator_predecision_stop_hazard_require_all_thresholds"
        ]
        is True
    )
    assert (
        repaired_runtime[
            "scheduler_v4_best_trade_allocator_predecision_stop_hazard_min_unit_risk_atr"
        ]
        == 0.35
    )
    assert (
        repaired_runtime[
            "scheduler_v4_best_trade_allocator_predecision_stop_hazard_max_distance_to_limit_risk"
        ]
        == 1.00
    )
    assert (
        repaired_runtime[
            "scheduler_v4_best_trade_allocator_predecision_stop_hazard_min_limit_fill_probability"
        ]
        == 0.50
    )
    assert (
        repaired_runtime[
            "scheduler_v4_best_trade_allocator_predecision_stop_hazard_min_target_r"
        ]
        == 1.50
    )
    assert (
        repaired_runtime[
            "scheduler_v4_best_trade_allocator_predecision_stop_hazard_pressure_enabled"
        ]
        is True
    )
    assert (
        repaired_runtime[
            "scheduler_v4_best_trade_allocator_predecision_stop_hazard_pressure_min_score"
        ]
        == 0.75
    )
    assert (
        repaired_runtime[
            "scheduler_v4_best_trade_allocator_predecision_stop_hazard_risk_cap_pct"
        ]
        == 0.10
    )
    assert (
        repaired_runtime[
            "scheduler_v4_best_trade_allocator_predecision_stop_hazard_missing_fields_action"
        ]
        == "no_block"
    )


def test_selected_package_bridge_uses_live_like_profit_harvest_thresholds() -> None:
    bridge = load_selected_package_replay_bridge()

    config = bridge.apply_ultimate_replay_loss_bucket_policy({"gtos_vnext_runtime": {}})
    runtime = config["gtos_vnext_runtime"]
    overlay = config["ultimate_replay_loss_bucket_policy"]["profit_harvest_overlay"]

    assert runtime["profit_harvest_mfe_capture_v4_enabled"] is True
    assert runtime["profit_harvest_mfe_capture_v4_min_mfe_r"] == 0.50
    assert runtime["profit_harvest_mfe_capture_v4_stop_activation_mfe_r"] == 0.50
    assert runtime["profit_harvest_mfe_capture_v4_target_activation_fraction"] == 0.75
    assert runtime["profit_harvest_mfe_capture_v4_trail_gap_r"] == 0.35
    assert runtime["profit_harvest_mfe_capture_v4_allow_m1_proxy_final_r_authority"] is True
    assert (
        runtime["profit_harvest_mfe_capture_v4_m1_proxy_final_r_authority_source"]
        == "owner_approved_reconstructed_proxy_replay_authority_m1_ordered_path_not_live"
    )
    assert runtime["profit_harvest_mfe_capture_v4_min_hold_minutes_before_stop_raise"] == 0
    assert runtime["ultimate_candidate_package_live_activation_allowed"] is False
    assert runtime["ultimate_candidate_package_final_package_selected"] is False
    assert_package_rank_boost_replay_authority_enabled(runtime)
    assert overlay["enabled"] is True
    assert overlay["repair_status"] == (
        "sub1r_protective_floor_replay_authority_enabled_no_broker_mutation_target_touch_source_gap_safe"
    )
    assert overlay["min_hold_minutes_before_stop_raise"] == 0


def test_profit_harvest_mechanism_params_match_replay_bridge_and_live_config() -> None:
    harness = load_broad_replay_harness()
    bridge = load_selected_package_replay_bridge()

    broad_runtime = harness.build_config(harness.PROFILE_REPAIRED)[
        "gtos_vnext_runtime"
    ]
    bridge_runtime = bridge.apply_ultimate_replay_loss_bucket_policy(
        {"gtos_vnext_runtime": {}}
    )["gtos_vnext_runtime"]
    live_runtime = _agent_config_runtime()

    mechanism_keys = (
        "profit_harvest_mfe_capture_v4_enabled",
        "profit_harvest_mfe_capture_v4_require_vnext_dynamic_policy",
        "profit_harvest_mfe_capture_v4_min_mfe_r",
        "profit_harvest_mfe_capture_v4_stop_activation_mfe_r",
        "profit_harvest_mfe_capture_v4_target_activation_fraction",
        "profit_harvest_mfe_capture_v4_trail_gap_r",
        "profit_harvest_mfe_capture_v4_protect_floor_r",
        "profit_harvest_mfe_capture_v4_cost_aware_protect_floor_enabled",
        "profit_harvest_mfe_capture_v4_cost_aware_margin_r",
        "profit_harvest_mfe_capture_v4_close_on_giveback_r",
        "profit_harvest_mfe_capture_v4_min_hold_minutes_before_stop_raise",
        "profit_harvest_mfe_capture_v4_armed_stale_close_enabled",
        "profit_harvest_mfe_capture_v4_armed_stale_minutes",
        "profit_harvest_mfe_capture_v4_armed_stale_min_mfe_r",
        "profit_harvest_mfe_capture_v4_armed_stale_close_below_r",
        "profit_harvest_mfe_capture_v4_stale_minutes",
        "profit_harvest_mfe_capture_v4_stale_min_mfe_r",
        "profit_harvest_mfe_capture_v4_stale_close_below_r",
    )
    for key in mechanism_keys:
        assert broad_runtime[key] == bridge_runtime[key] == live_runtime[key]

    assert broad_runtime["profit_harvest_mfe_capture_v4_stop_activation_mfe_r"] == 0.50
    assert (
        broad_runtime[
            "profit_harvest_mfe_capture_v4_min_hold_minutes_before_stop_raise"
        ]
        == 0
    )
    assert (
        "profit_harvest_mfe_capture_v4_allow_m1_proxy_final_r_authority"
        not in live_runtime
    )
    assert (
        broad_runtime["profit_harvest_mfe_capture_v4_allow_m1_proxy_final_r_authority"]
        is True
    )
    assert (
        bridge_runtime["profit_harvest_mfe_capture_v4_allow_m1_proxy_final_r_authority"]
        is True
    )


def test_selected_package_bridge_forwards_source_required_replay_policy_to_scheduler() -> None:
    bridge = load_selected_package_replay_bridge()

    config = bridge.apply_ultimate_replay_loss_bucket_policy({"gtos_vnext_runtime": {}})
    runtime = config["gtos_vnext_runtime"]
    scheduler = timewarp.scheduler_config(config)

    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_source_required_fail_closed_package_replay_override_enabled"
        ]
        is True
    )
    assert scheduler["source_required_fail_closed_package_replay_override_enabled"] is True
    assert (
        scheduler[
            "source_required_fail_closed_package_replay_override_min_fill_probability"
        ]
        == 0.12
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_package_cooldown_release_allow_same_symbol_daily_loss_lockout_for_fill_floor_authority"
        ]
        is True
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_package_cooldown_release_allow_same_symbol_daily_loss_lockout_for_router_refusal_authority"
        ]
        is True
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_package_cooldown_release_allow_same_symbol_daily_loss_lockout_for_signed_executable_package_authority"
        ]
        is True
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_package_cooldown_release_allow_same_symbol_daily_loss_lockout_for_package_quality"
        ]
        is False
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_package_cooldown_release_fill_floor_authority_min_fill_probability"
        ]
        == 0.25
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_opening_risk_cap_release_enabled"
        ]
        is True
    )
    assert (
        scheduler["dynamic_budget_package_opening_risk_cap_release_enabled"] is True
    )
    assert scheduler["dynamic_budget_package_opening_risk_cap_release_max_risk_pct"] == 0.25
    assert (
        scheduler[
            "source_required_fail_closed_package_replay_override_allow_new_position_without_same_side_context_enabled"
        ]
        is False
    )
    assert scheduler["source_required_selector_hold_package_replay_override_enabled"] is False
    assert scheduler["source_required_package_duplicate_scale_in_enabled"] is True
    assert scheduler["source_required_package_duplicate_scale_in_min_fill_probability"] == 0.12
    assert scheduler["source_required_package_risk_lifecycle_reconcile_enabled"] is True
    assert (
        scheduler["source_required_package_risk_lifecycle_reconcile_min_fill_probability"]
        == 0.12
    )
    assert runtime["ultimate_candidate_package_soften_selector_fill_floor_enabled"] is False
    assert "V114C_B3" in runtime[
        "ultimate_candidate_package_soften_selector_fill_floor_repair_reason"
    ]
    assert scheduler["ultimate_candidate_package_soften_selector_fill_floor_enabled"] is False
    assert (
        runtime[
            "ultimate_candidate_package_broker_net_gradient_open_reduced_risk_enabled"
        ]
        is False
    )
    assert "default-off" in runtime[
        "ultimate_candidate_package_broker_net_gradient_open_reduced_risk_demotion_reason"
    ]
    assert (
        scheduler["ultimate_candidate_package_broker_net_gradient_open_reduced_risk_enabled"]
        is False
    )
    assert runtime["ultimate_candidate_package_live_activation_allowed"] is False
    assert runtime["ultimate_candidate_package_final_package_selected"] is False
    assert_package_rank_boost_replay_authority_enabled(runtime)


def test_selected_package_bridge_hydrates_broker_cost_profile() -> None:
    bridge = load_selected_package_replay_bridge()

    config = bridge.build_replay_config()
    profile = config["selected_package_bridge_broker_cost_profile"]
    runtime = config["gtos_vnext_runtime"]

    assert profile["broker_symbol_spec_source"] == "config/profiles/operator_profile.yaml"
    assert profile["instrument_count"] > 0
    assert config["runtime"]["broker_account_namespace"] == "operator_profile"
    assert config.get("broker") or config.get("broker_profile") or config.get("profile_name")
    assert "XAUUSD" in config.get("instruments", {})
    assert runtime["ultimate_candidate_package_live_activation_allowed"] is False
    assert runtime["ultimate_candidate_package_final_package_selected"] is False
    assert_package_rank_boost_replay_authority_enabled(runtime)


def test_selected_package_bridge_preserves_executable_geometry_fields() -> None:
    bridge = load_selected_package_replay_bridge()

    candidate = {
        "candidate_id": "geometry-candidate",
        "symbol": "XAUUSD",
        "side": "LONG",
        "decision_time_utc": "2026-05-05T07:15:00+00:00",
        "timeframe": "M15",
        "source_hash": "source-hash-fixture",
        "source_path": "route/source-bound-fixture.jsonl",
        "entry_price": 3300.25,
        "entry_reference": "source_bound_limit_entry",
        "stop_loss": 3296.25,
        "stop_or_invalidation": 3296.25,
        "take_profit_1": 3308.25,
        "target_reference": "source_bound_target",
        "risk_reward_ratio": 2.0,
        "trade_parameters": {"entry_price": 3300.25, "stop_loss": 3296.25},
        "geometry_contract": {"status": "source_bound_geometry_present"},
        "dynamic_geometry_policy": "limit_first_probe",
        "dynamic_execution_policy_id": "selected_package_bridge_geometry_fixture",
        "expected_net_r": 0.9,
        "probability": 0.8,
        "fill_probability": 0.7,
        "source_completeness": 1.0,
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "same_symbol_replay_exposure_context": {
            "symbol": "XAUUSD",
            "side": "LONG",
            "same_side_pending_count": 1,
            "same_side_pending_ids": ["pending-context"],
            "same_side_pending_order_ids": ["pending-context"],
            "same_side_pending_risk_pct": 0.25,
            "opposite_pending_count": 0,
            "opposite_pending_ids": [],
            "opposite_pending_order_ids": [],
            "opposite_pending_risk_pct": 0.0,
        },
        "same_symbol_lifecycle_exposure_risk_pct": 0.25,
        "replacement_reallocation_quality": {
            "enabled": True,
            "eligible_for_reallocation_promotion": True,
            "score": 0.64,
            "selected_release_pending_id": "pending-context",
            "source_boundary": (
                "predecision_expected_transfer_plus_pending_"
                "replacement_quality_no_outcome_fields"
            ),
            "uses_outcome_fields": False,
        },
        "replacement_reallocation_quality_score": 0.64,
        "scheduler_materialization_action_intent": "new_position",
        "scheduler_materialization_selector_action": "open-reduced-risk",
        "scheduler_materialization_selector_reason": "package_fixture",
        "source_bound_package_candidate_use_allowed": True,
    }

    fields = bridge.selected_package_bridge_quality_fields(candidate)
    compact = bridge.compact_candidate_rows([candidate], [])[0]
    instance_key = "geometry-candidate@@2026-05-05T07:15:00+00:00"

    assert fields["upstream_package_source_bound_candidate_use_allowed"] is True
    assert fields["canonical_replay_candidate_instance_key"] == instance_key
    assert fields["risk_finalizer_probe_instance_key"] == instance_key
    assert fields["source_bound_replay_candidate_instance_key"] == instance_key
    assert fields["candidate_instance_identity_status"] == "materialized"
    assert (
        fields["candidate_decision_quality_source_boundary"]
        == "selected_package_bridge_predecision_quality_alias_repair"
    )
    assert fields["source_boundary"] == "source_bound_asof_timewarp_decision_input"
    assert fields["selected_policy_for_expected_net_r"] == "limit_first_probe"
    assert fields["selected_policy_expected_net_r"] == 0.9
    assert fields["selected_policy_probability"] == 0.8
    assert fields["selected_policy_source_completeness"] == 1.0
    assert (
        fields["selected_policy_quality_alias_status"]
        == "selected_policy_proxy_quality_materialized"
    )
    expected_calibration_status = (
        bridge.timewarp_loop
        .OWNER_APPROVED_RECONSTRUCTED_PROXY_SELECTED_POLICY_EXPECTED_NET_STATUS
    )
    assert (
        fields["selected_policy_expected_net_calibration_status"]
        == expected_calibration_status
    )
    assert fields["selected_policy_expected_net_calibrated"] is True
    assert compact["canonical_replay_candidate_instance_key"] == instance_key
    assert compact["risk_finalizer_probe_instance_key"] == instance_key
    assert compact["source_bound_replay_candidate_instance_key"] == instance_key
    assert compact["candidate_instance_identity_status"] == "materialized"
    for row in (fields, compact):
        assert row["timeframe"] == "M15"
        assert row["source_hash"] == "source-hash-fixture"
        assert row["source_path"] == "route/source-bound-fixture.jsonl"
        assert row["same_symbol_replay_exposure_context"]["same_side_pending_ids"] == [
            "pending-context"
        ]
        assert row["same_symbol_replay_exposure_context_status"] == "source_observed"
        assert row["same_symbol_lifecycle_exposure_risk_pct"] == 0.25
        assert row["canonical_replay_context_envelope"]["timeframe"] == "M15"
        assert (
            row["canonical_replay_context_projection_status"]
            == "materialized"
        )
        assert row["replacement_reallocation_quality_score"] == 0.64
        assert row["replacement_reallocation_quality_uses_outcome_fields"] is False
    assert (
        compact["candidate_decision_quality_source_boundary"]
        == "selected_package_bridge_predecision_quality_alias_repair"
    )
    assert compact["source_boundary"] == "source_bound_asof_timewarp_decision_input"
    assert compact["selected_policy_for_expected_net_r"] == "limit_first_probe"
    assert compact["selected_policy_expected_net_r"] == 0.9
    assert compact["selected_policy_probability"] == 0.8
    assert compact["selected_policy_source_completeness"] == 1.0
    assert (
        compact["selected_policy_quality_alias_status"]
        == "selected_policy_proxy_quality_materialized"
    )
    assert (
        compact["selected_policy_expected_net_calibration_status"]
        == expected_calibration_status
    )
    assert compact["selected_policy_expected_net_calibrated"] is True
    assert fields["selected_package_member_axis_authority_bound"] is False
    assert fields["package_source_bound_admission_diagnostic"] is True
    assert fields["source_bound_package_candidate_use_allowed"] is True
    assert fields["ultimate_package_matched_member_axis_count"] == 0
    assert fields["package_replay_candidate_use_allowed"] is False
    assert (
        fields["package_replay_executable_candidate_use_allowed_reason"]
        == "ultimate_package_effective_admission_count_zero"
    )
    for row in (fields, compact):
        assert row["package_authority_has_order_geometry"] is True
        assert row["package_authority_order_geometry_status"] == "order_geometry_present"
        assert row["package_authority_executable_candidate_status"].startswith(
            "package_authority_candidate_not_executable:"
            "signed_package_new_entry_authority_invalid:"
        )
    for key in bridge.EXECUTABLE_GEOMETRY_FIELDS:
        if key in candidate:
            if key in {"trade_parameters", "target_reference"}:
                continue
            assert fields[key] == candidate[key]
            assert compact[key] == candidate[key]
    for row in (fields, compact):
        params = row["trade_parameters"]
        assert params["entry_price"] == 3300.25
        assert params["stop_loss"] == 3296.25
        assert params["take_profit_1"] == 3308.25
        assert params["target_reference"] == 3308.25
        assert params["risk_reward_ratio"] == 2.0
        assert row["target_reference"] == 3308.25
        assert row["canonical_geometry_status"] == "canonicalized"
        assert row["scheduler_materialization_action_intent"] == "new_position"
        assert row["scheduler_materialization_selector_action"] == "open-reduced-risk"
        assert row["scheduler_materialization_selector_reason"] == "package_fixture"


def test_selected_package_bridge_compact_candidate_backfills_stop_hazard_projection() -> None:
    bridge = load_selected_package_replay_bridge()

    candidate = {
        "candidate_id": "stop-hazard-candidate",
        "symbol": "XAUUSD",
        "side": "LONG",
        "decision_time_utc": "2026-05-05T07:15:00+00:00",
        "source_bound_package_candidate_use_allowed": True,
        "expected_net_r": 0.9,
        "probability": 0.8,
        "fill_probability": 0.7,
        "source_completeness": 1.0,
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "scheduler_candidate_decision_inputs": {
            "predecision_stop_hazard_guard_status": "capped",
            "predecision_stop_hazard_guard_reason": (
                "predecision_stop_hazard_guard_risk_capped"
            ),
            "predecision_stop_hazard_guard_action": "cap",
            "predecision_stop_hazard_guard_risk_cap_applied": False,
            "predecision_stop_hazard_guard_risk_cap_pct": 0.10,
            "predecision_stop_hazard_guard_unit_risk_atr": 0.75,
            "predecision_stop_hazard_guard_distance_to_limit_risk": 0.45,
            "predecision_stop_hazard_guard_limit_fill_probability": 0.78,
            "predecision_stop_hazard_guard_source_boundary": (
                "predecision_limit_fillability_geometry_no_outcome_path"
            ),
            "predecision_stop_hazard_guard_outcome_fields_used": False,
        },
    }

    compact = bridge.compact_candidate_rows([candidate], [])[0]

    assert compact["predecision_stop_hazard_guard_status"] == "capped"
    assert compact["predecision_stop_hazard_guard_action"] == "cap"
    assert compact["predecision_stop_hazard_guard_risk_cap_applied"] is True
    assert compact["predecision_stop_hazard_guard_risk_cap_pct"] == 0.10
    assert compact["predecision_stop_hazard_guard_outcome_fields_used"] is False


def test_selected_package_bridge_marks_dynamic_policy_expected_net_bridge_proxy_diagnostic() -> None:
    bridge = load_selected_package_replay_bridge()

    row = {
        "selected_policy_for_expected_net_r": "unspecified_expected_net_r_policy",
        "selected_policy_expected_net_calibration_status": "not_required_no_selected_policy",
        "dynamic_geometry_policy": "momentum_exhaustion",
        "dynamic_execution_policy_id": "vnext_exec_momentum_1r_pullback_04r_cap_2r",
        "expected_net_r": 1.18,
        "probability": 0.93,
        "source_completeness": 1.0,
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "packets.candidate_expected_net_r",
            "probability": "packets.candidate_probability",
            "source_completeness": "candidate.source_completeness",
        },
        "candidate_decision_quality_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
    }

    fields = bridge.selected_policy_expected_net_calibration_fields(row)

    assert bridge.selected_policy_from_bridge_row(row) == "momentum_exhaustion"
    assert fields["selected_policy_for_expected_net_r"] == "momentum_exhaustion"
    assert fields["selected_policy_expected_net_calibration_required"] is True
    assert fields["selected_policy_expected_net_calibrated"] is False
    assert (
        fields["selected_policy_expected_net_calibration_status"]
        == "selected_policy_expected_net_bridge_proxy_diagnostic_only"
    )
    assert fields["selected_policy_expected_net_calibration_source_boundary"] == (
        "selected_policy_expected_net_uncalibrated_bridge_proxy_predecision_quality"
    )
    assert fields["selected_policy_expected_net_assumption_hash"] is None


def test_selected_package_bridge_demotes_stale_calibrated_bridge_proxy_source() -> None:
    bridge = load_selected_package_replay_bridge()

    row = {
        "selected_policy_for_expected_net_r": "momentum_exhaustion",
        "selected_policy_expected_net_calibration_status": "calibrated",
        "selected_policy_expected_net_calibrated": True,
        "selected_policy_expected_net_calibration_source": (
            "packets.candidate_expected_net_r"
        ),
        "selected_policy_expected_net_calibration_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        "expected_net_r": 1.18,
        "probability": 0.93,
        "source_completeness": 1.0,
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "packets.candidate_expected_net_r",
            "probability": "packets.candidate_probability",
            "source_completeness": "candidate.source_completeness",
        },
        "candidate_decision_quality_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
    }

    fields = bridge.selected_policy_expected_net_calibration_fields(row)

    assert fields["selected_policy_expected_net_calibration_required"] is True
    assert fields["selected_policy_expected_net_calibrated"] is False
    assert fields["selected_policy_expected_net_calibration_status"] == (
        "selected_policy_expected_net_bridge_proxy_diagnostic_only"
    )
    assert fields["selected_policy_expected_net_calibration_source_boundary"] == (
        "selected_policy_expected_net_uncalibrated_bridge_proxy_predecision_quality"
    )
    assert fields["selected_policy_expected_net_assumption_hash"] is None


def test_selected_package_bridge_owner_approved_reconstructed_proxy_calibrates_package_row() -> None:
    bridge = load_selected_package_replay_bridge()

    row = {
        "candidate_id": "pkg-owner-approved-1",
        "decision_time_utc": "2026-05-13T09:00:00+00:00",
        "ultimate_package_effective_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_admission_count": 1,
        "dynamic_geometry_policy": "momentum_exhaustion",
        "expected_net_r": 1.18,
        "candidate_expected_net_r": 1.18,
        "probability": 0.93,
        "source_completeness": 1.0,
        "selected_policy_expected_net_calibration_status": (
            "selected_policy_expected_net_bridge_proxy_diagnostic_only"
        ),
        "selected_policy_expected_net_calibrated": False,
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "packets.candidate_expected_net_r",
            "probability": "packets.candidate_probability",
            "source_completeness": "candidate.source_completeness",
        },
        "candidate_decision_quality_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
    }

    hydrated = bridge.hydrate_candidate_quality_aliases(row)

    assert hydrated[
        bridge.timewarp_loop.OWNER_APPROVED_RECONSTRUCTED_PROXY_SELECTED_POLICY_EXPECTED_NET_FLAG
    ] is True
    assert hydrated["selected_policy_for_expected_net_r"] == "momentum_exhaustion"
    assert hydrated["selected_policy_expected_net_r"] == 1.18
    assert hydrated["selected_policy_expected_net_calibrated"] is True
    assert hydrated["selected_policy_expected_net_calibration_status"] == (
        bridge.timewarp_loop.OWNER_APPROVED_RECONSTRUCTED_PROXY_SELECTED_POLICY_EXPECTED_NET_STATUS
    )
    assert hydrated["selected_policy_expected_net_calibration_source"] == (
        bridge.timewarp_loop.OWNER_APPROVED_RECONSTRUCTED_PROXY_SELECTED_POLICY_EXPECTED_NET_SOURCE
    )
    assert hydrated["selected_policy_expected_net_assumption_hash"]
    assert hydrated["selected_policy_expected_net_replay_authority_class"] == (
        "owner_approved_reconstructed_proxy_local_replay_not_live_or_final"
    )


def test_selected_package_bridge_keeps_non_package_bridge_proxy_diagnostic() -> None:
    bridge = load_selected_package_replay_bridge()

    row = {
        "candidate_id": "non-package-bridge-proxy",
        "dynamic_geometry_policy": "momentum_exhaustion",
        "expected_net_r": 1.18,
        "candidate_expected_net_r": 1.18,
        "probability": 0.93,
        "source_completeness": 1.0,
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "packets.candidate_expected_net_r",
            "probability": "packets.candidate_probability",
            "source_completeness": "candidate.source_completeness",
        },
        "candidate_decision_quality_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
    }

    hydrated = bridge.hydrate_candidate_quality_aliases(row)

    assert (
        bridge.timewarp_loop.OWNER_APPROVED_RECONSTRUCTED_PROXY_SELECTED_POLICY_EXPECTED_NET_FLAG
        not in hydrated
    )
    assert hydrated["selected_policy_expected_net_calibrated"] is False
    assert hydrated["selected_policy_expected_net_calibration_status"] == (
        "selected_policy_expected_net_bridge_proxy_diagnostic_only"
    )
    assert hydrated.get("selected_policy_expected_net_assumption_hash") is None


def test_selected_package_bridge_keeps_dynamic_policy_uncalibrated_without_expected_net_source() -> None:
    bridge = load_selected_package_replay_bridge()

    row = {
        "selected_policy_for_expected_net_r": "unspecified_expected_net_r_policy",
        "selected_policy_expected_net_calibration_status": "not_required_no_selected_policy",
        "dynamic_geometry_policy": "momentum_exhaustion",
        "expected_net_r": 1.18,
        "probability": 0.93,
        "source_completeness": 1.0,
        "candidate_decision_quality_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
    }

    fields = bridge.selected_policy_expected_net_calibration_fields(row)

    assert fields["selected_policy_for_expected_net_r"] == "momentum_exhaustion"
    assert fields["selected_policy_expected_net_calibration_required"] is True
    assert fields["selected_policy_expected_net_calibrated"] is False
    assert fields["selected_policy_expected_net_calibration_status"] == (
        "selected_policy_expected_net_calibration_missing"
    )
    assert fields["selected_policy_expected_net_calibration_source_boundary"] == (
        "selected_policy_expected_net_uncalibrated_bridge_proxy_predecision_quality"
    )


def test_selected_package_bridge_rejects_existing_outcome_backed_selected_policy_calibration() -> None:
    bridge = load_selected_package_replay_bridge()

    row = {
        "selected_policy_for_expected_net_r": "momentum_exhaustion",
        "selected_policy_expected_net_calibration_status": "calibrated",
        "selected_policy_expected_net_calibrated": True,
        "selected_policy_expected_net_calibration_source": (
            "postdecision_outcome.final_r"
        ),
        "selected_policy_expected_net_calibration_source_boundary": (
            "broker_live_outcome_boundary"
        ),
        "expected_net_r": 1.18,
        "probability": 0.93,
        "source_completeness": 1.0,
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "postdecision_outcome.final_r",
        },
        "candidate_decision_quality_source_boundary": (
            "broker_live_outcome_boundary"
        ),
    }

    fields = bridge.selected_policy_expected_net_calibration_fields(row)

    assert fields["selected_policy_expected_net_calibration_required"] is True
    assert fields["selected_policy_expected_net_calibrated"] is False
    assert fields["selected_policy_expected_net_calibration_status"] == (
        "selected_policy_expected_net_calibration_missing"
    )
    assert fields["selected_policy_expected_net_calibration_source_boundary"] == (
        "selected_policy_expected_net_uncalibrated_bridge_proxy_predecision_quality"
    )


def test_selected_package_bridge_accepts_source_required_fail_closed_replay_override() -> None:
    bridge = load_selected_package_replay_bridge()

    base = {
        "ultimate_package_effective_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_admission_count": 1,
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "candidate_cost_r_fallback_is_authority": False,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "expected_net_r": 0.85,
        "probability": 0.80,
        "fill_probability": 0.12,
        **_execution_fillability_fields(0.12),
        "scheduler_materialization_action_intent": "new_position",
        "selector_action": "open-reduced-risk",
    }

    cases = (
        (
            "",
            {
                "scheduler_materialization_source_required_fail_closed_override_applied": True,
            },
            "source_required_override_reason_missing_or_invalid",
        ),
        (
            "source_required_fail_closed_package_close_reverse_reconciled_for_replay",
            {
                "scheduler_materialization_source_required_fail_closed_override_applied": True,
                "scheduler_materialization_action_intent": "replace_pending",
            },
            "source_required_override_reason_action_mismatch",
        ),
        (
            "source_required_fail_closed_package_close_reverse_reconciled_for_replay",
            {
                "scheduler_materialization_replay_lifecycle_action_resolver_applied": True,
                "scheduler_materialization_action_intent": "close_and_reverse",
            },
            "source_required_override_reason_kind_mismatch",
        ),
        (
            "replay_lifecycle_action_resolver_replace_pending",
            {
                "scheduler_materialization_replay_lifecycle_action_resolver_applied": True,
                "scheduler_materialization_action_intent": "close_and_reverse",
            },
            "source_required_override_reason_action_mismatch",
        ),
    )
    for override_reason, override_fields, expected_reason in cases:
        row = {
            **base,
            **override_fields,
            "scheduler_materialization_override_reason": override_reason,
        }
        allowed, reason = bridge.executable_package_use_detail(
            row,
            source_bound_allowed=True,
        )

        assert allowed is False
        assert expected_reason in reason

    signed_new_position = _signed_bridge_router_refusal_row(
        "source_bound_router_refusal_open_reduced_materialized_for_replay",
        matched_member_axis_id="member_axis:source-required-new-position",
    )
    signed_new_position.update(
        {
            "scheduler_materialization_action_intent": "new_position",
            "scheduler_materialization_source_required_fail_closed_override_applied": True,
            "scheduler_materialization_override_reason": (
                "source_required_fail_closed_package_new_position_source_gap_"
                "reconciled_for_replay"
            ),
            "scheduler_materialization_source_required_fail_closed_override_failures": [],
        }
    )

    assert bridge.executable_package_use_detail(
        signed_new_position,
        source_bound_allowed=True,
    ) == (True, "broker_cost_selector_and_scheduler_action_executable")


def test_selected_package_bridge_source_required_close_reverse_requires_bound_release() -> None:
    bridge = load_selected_package_replay_bridge()
    row = _signed_bridge_router_refusal_row(
        "source_bound_router_refusal_open_reduced_materialized_for_replay",
        matched_member_axis_id="member_axis:source-required-close-reverse",
    )
    release_ids = ["bridge-opposite-open-position"]
    release_binding = {
        "schema_version": "package_close_reverse_release_binding_v1",
        "candidate_id": row["candidate_id"],
        "decision_time_utc": row["decision_time_utc"],
        "canonical_replay_candidate_instance_key": row[
            "canonical_replay_candidate_instance_key"
        ],
        "source_bound_replay_candidate_instance_key": row[
            "source_bound_replay_candidate_instance_key"
        ],
        "candidate_instance_identity_status": row[
            "candidate_instance_identity_status"
        ],
        "effective_action_intent": "close_and_reverse",
        "opposite_open_position_ids": release_ids,
        "same_symbol_close_reverse_release_risk_pct": 0.25,
    }
    row.update(
        {
            "scheduler_materialization_action_intent": "close_and_reverse",
            "scheduler_materialization_source_required_fail_closed_override_applied": True,
            "scheduler_materialization_override_reason": (
                "source_required_fail_closed_package_close_reverse_reconciled_"
                "for_replay"
            ),
            "scheduler_materialization_source_required_fail_closed_override_failures": [],
            "package_opposite_side_close_reverse_authority": {
                "applies": True,
                "allowed": True,
                "failures": [],
                "effective_action_intent": "close_and_reverse",
                "same_symbol_close_reverse_release_risk_pct": 0.25,
                "opposite_open_position_ids": release_ids,
                "opposite_open_position_count": 1,
                "release_binding_payload": release_binding,
                "release_binding_hash_sha256": bridge.stable_sha256(
                    release_binding
                ),
            },
        }
    )
    _resign_test_authority(row, expect_valid=True)

    assert bridge.executable_package_use_detail(
        row,
        source_bound_allowed=True,
    ) == (True, "broker_cost_selector_and_scheduler_action_executable")

    tampered = copy.deepcopy(row)
    tampered["package_opposite_side_close_reverse_authority"][
        "release_binding_payload"
    ]["opposite_open_position_ids"] = ["different-open-position"]
    assert bridge.executable_package_use_detail(
        tampered,
        source_bound_allowed=True,
    ) == (False, "close_reverse_release_binding_invalid")


def test_selected_package_bridge_source_required_override_preserves_zero_quality_values() -> None:
    bridge = load_selected_package_replay_bridge()

    row = {
        "ultimate_package_effective_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_admission_count": 1,
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "candidate_cost_r_fallback_is_authority": False,
        "source_completeness": 0.0,
        "candidate_source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "expected_net_r": 0.85,
        "probability": 0.80,
        "fill_probability": 0.12,
        **_execution_fillability_fields(0.12),
        "scheduler_materialization_action_intent": "same_direction_scale_in",
        "scheduler_materialization_source_required_fail_closed_override_applied": True,
        "scheduler_materialization_override_reason": (
            "source_required_fail_closed_package_source_reconciled_for_replay"
        ),
        "selector_action": "open-reduced-risk",
    }

    assert bridge.executable_package_use_detail(
        row,
        source_bound_allowed=True,
    ) == (
        False,
        "source_required_replay_override_invalid:"
        "source_required_quality_field_below_floor:source_completeness",
    )


def test_selected_package_bridge_open_reduced_allows_replace_pending_action_intent() -> None:
    bridge = load_selected_package_replay_bridge()

    row = {
        "candidate_id": "bridge-replace-pending-signed",
        "candidate_id_source": "candidate_id",
        "decision_time_utc": "2026-05-15T10:15:00+00:00",
        "canonical_replay_candidate_instance_key": (
            "bridge-replace-pending-signed@@2026-05-15T10:15:00+00:00"
        ),
        "source_bound_replay_candidate_instance_key": (
            "bridge-replace-pending-signed@@2026-05-15T10:15:00+00:00"
        ),
        "candidate_instance_identity_status": "materialized",
        "ultimate_package_effective_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_admission_count": 1,
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "candidate_cost_r_fallback_is_authority": False,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "expected_net_r": 0.80,
        "probability": 0.75,
        "fill_probability": 0.25,
        **_execution_fillability_fields(0.25),
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "bridge_fixture.predecision.expected_net_r",
            "probability": "bridge_fixture.predecision.probability",
            "fill_probability": "bridge_fixture.predecision.fill_probability",
            "source_completeness": (
                "bridge_fixture.predecision.source_completeness"
            ),
        },
        "candidate_decision_quality_source_boundary": (
            "predecision_bridge_fixture_quality_no_outcome_fields"
        ),
        "candidate_decision_quality_alias_status": "exact_materialized",
        "source_bound_package_candidate_use_allowed": True,
        "package_replay_order_executable_candidate_use_allowed": True,
        "package_replay_order_executable_candidate_use_allowed_reason": (
            "bridge_fixture_signed_replace_pending"
        ),
        "package_replay_order_executable_authority_source": (
            "bridge_fixture_predecision_authority"
        ),
        "entry_price": 1.1000,
        "stop_loss": 1.0950,
        "take_profit_1": 1.1100,
        "scheduler_materialization_action_intent": "replace_pending",
        "same_symbol_replay_exposure_context": {
            "same_side_pending_ids": ["bridge-pending-old"],
            "same_side_pending_order_ids": ["bridge-pending-old"],
            "opposite_pending_ids": [],
            "opposite_pending_order_ids": [],
        },
        "selector_action": "open-reduced-risk",
        "selector_reason": (
            "selected_package_bridge_open_reduced_materialized_for_replay"
        ),
        "ultimate_candidate_package_open_reduced_risk_authority": {
            "applies": True,
            "allowed": True,
            "authority_family": "unit_test_authority",
            "authority_source": "bridge_fixture_predecision_authority",
            "source_boundary": (
                "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
            ),
        },
    }
    replacement_binding = {
        "schema_version": "package_pending_replacement_release_binding_v1",
        "candidate_id": row["candidate_id"],
        "decision_time_utc": row["decision_time_utc"],
        "canonical_replay_candidate_instance_key": row[
            "canonical_replay_candidate_instance_key"
        ],
        "source_bound_replay_candidate_instance_key": row[
            "source_bound_replay_candidate_instance_key"
        ],
        "candidate_instance_identity_status": row[
            "candidate_instance_identity_status"
        ],
        "effective_action_intent": "replace_pending",
        "selected_release_pending_id": "bridge-pending-old",
        "selected_release_reason": "bridge_fixture_replace_pending",
        "same_side_pending_ids": ["bridge-pending-old"],
        "same_side_pending_order_ids": ["bridge-pending-old"],
        "opposite_pending_ids": [],
        "opposite_pending_order_ids": [],
    }
    row["replacement_reallocation_quality"] = {
        "selected_release_pending_id": "bridge-pending-old",
        "replacement_release_binding_payload": replacement_binding,
        "replacement_release_binding_hash_sha256": bridge.stable_sha256(
            replacement_binding
        ),
    }
    signed_authority = _complete_test_authority_surface(
        row,
        selector_action="open-reduced-risk",
        selector_reason="selected_package_bridge_open_reduced_materialized_for_replay",
        authority=row["ultimate_candidate_package_open_reduced_risk_authority"],
        action_intent="replace_pending",
    )
    row.update(signed_authority)
    row["ultimate_candidate_package_open_reduced_risk_authority"] = signed_authority

    assert bridge.executable_package_use_detail(
        row,
        source_bound_allowed=True,
    ) == (True, "broker_cost_selector_and_scheduler_action_executable")
    fields = bridge.package_authority_bridge_fields(row, source_bound_allowed=True)
    assert fields["package_authority_executable_candidate_status"] == (
        "package_authority_candidate_executable"
    )
    assert fields["package_new_entry_authority_required"] is True
    assert fields["package_new_entry_authority_valid"] is True

    tampered = dict(row)
    tampered_payload = dict(row["package_new_entry_authority_payload"])
    tampered_payload["target_action_intent"] = "new_position"
    tampered["package_new_entry_authority_payload"] = tampered_payload
    tampered_nested = dict(signed_authority)
    tampered_nested["package_new_entry_authority_payload"] = tampered_payload
    tampered["ultimate_candidate_package_open_reduced_risk_authority"] = (
        tampered_nested
    )

    tampered_allowed, tampered_reason = bridge.executable_package_use_detail(
        tampered,
        source_bound_allowed=True,
    )
    tampered_fields = bridge.package_authority_bridge_fields(
        tampered,
        source_bound_allowed=True,
    )
    assert tampered_allowed is False
    assert tampered_reason.startswith(
        "selector_reduced_package_new_entry_signed_authority_invalid:"
    )
    assert tampered_fields[
        "package_replay_order_executable_candidate_use_allowed"
    ] is False

    tampered_release = copy.deepcopy(row)
    tampered_release["replacement_reallocation_quality"][
        "replacement_release_binding_payload"
    ]["selected_release_pending_id"] = "different-pending-id"
    assert bridge.executable_package_use_detail(
        tampered_release,
        source_bound_allowed=True,
    ) == (False, "replace_pending_release_binding_invalid")


def test_selected_package_bridge_unsigned_replace_pending_is_non_executable() -> None:
    bridge = load_selected_package_replay_bridge()
    row = {
        "ultimate_package_effective_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_admission_count": 1,
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "candidate_cost_r_fallback_is_authority": False,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "expected_net_r": 0.80,
        "probability": 0.75,
        "fill_probability": 0.25,
        **_execution_fillability_fields(0.25),
        "entry_price": 1.1000,
        "stop_loss": 1.0950,
        "take_profit_1": 1.1100,
        "scheduler_materialization_action_intent": "replace_pending",
        "selector_action": "open-reduced-risk",
        "ultimate_candidate_package_open_reduced_risk_authority": {
            "allowed": True,
            "authority_family": "router_refusal_softening",
            "source_boundary": (
                "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
            ),
        },
    }

    executable_allowed, executable_reason = bridge.executable_package_use_detail(
        row,
        source_bound_allowed=True,
    )
    fields = bridge.package_authority_bridge_fields(row, source_bound_allowed=True)

    assert executable_allowed is False
    assert executable_reason.startswith(
        "selector_reduced_package_new_entry_signed_authority_invalid:"
    )
    assert fields["package_new_entry_authority_required"] is True
    assert fields["package_new_entry_authority_valid"] is False
    assert fields["package_replay_order_executable_candidate_use_allowed"] is False
    assert fields["package_authority_executable_candidate_status"].startswith(
        "package_authority_candidate_not_executable:"
        "signed_package_new_entry_authority_invalid:"
    )


def test_selected_package_bridge_quality_fields_carry_package_packet_hashes() -> None:
    bridge = load_selected_package_replay_bridge()

    fields = bridge.selected_package_bridge_quality_fields(
        {
            "candidate_id": "candidate-packet-hash",
            "symbol": "XAUUSD",
            "side": "LONG",
            "decision_time_utc": "2026-05-05T07:15:00+00:00",
            "expected_net_r": 0.7,
            "probability": 0.8,
            "fill_probability": 0.75,
            "source_completeness": 1.0,
            "source_completeness_status": "source_completeness_present",
            "ultimate_candidate_package_packet_hash_sha256": "packet-hash",
            "ultimate_candidate_package_packet_shape_hash_sha256": "shape-hash",
        },
        matched_stable_member_axis_ids=("member_axis:fixture",),
    )

    assert fields["ultimate_candidate_package_packet_hash_sha256"] == "packet-hash"
    assert fields["ultimate_candidate_package_packet_shape_hash_sha256"] == "shape-hash"

    nested_fields = bridge.selected_package_bridge_quality_fields(
        {
            "candidate_id": "candidate-nested-packet",
            "symbol": "XAUUSD",
            "side": "LONG",
            "decision_time_utc": "2026-05-05T07:15:00+00:00",
            "expected_net_r": 0.7,
            "probability": 0.8,
            "fill_probability": 0.75,
            "source_completeness": 1.0,
            "source_completeness_status": "source_completeness_present",
            "ultimate_candidate_package_packet": {
                "packet_hash_sha256": "nested-packet-hash",
                "payload_shape_hash_sha256": "nested-shape-hash",
            },
        },
        matched_stable_member_axis_ids=("member_axis:fixture",),
    )

    assert nested_fields["ultimate_candidate_package_packet_hash_sha256"] == (
        "nested-packet-hash"
    )
    assert nested_fields["ultimate_candidate_package_packet_shape_hash_sha256"] == (
        "nested-shape-hash"
    )


def test_selected_package_bridge_materialized_packet_includes_context_envelope_and_instance_projection() -> None:
    bridge = load_selected_package_replay_bridge()
    instance_key = "candidate-context@@2026-05-05T07:15:00+00:00"

    packet = bridge._bridge_materialized_package_packet_contract(
        {
            "candidate_id": "candidate-context",
            "decision_time_utc": "2026-05-05T07:15:00+00:00",
            "canonical_replay_candidate_instance_key": instance_key,
            "risk_finalizer_probe_instance_key": instance_key,
            "source_bound_replay_candidate_instance_key": instance_key,
            "candidate_instance_identity_status": "materialized",
            "symbol": "XAUUSD",
            "side": "LONG",
            "timeframe": "M15",
            "session_bucket": "ny",
            "same_symbol_replay_exposure_context": {
                "symbol": "XAUUSD",
                "side": "LONG",
                "same_side_pending_ids": ["pending-context"],
                "same_side_pending_order_ids": ["pending-context"],
            },
            "canonical_replay_context_projection_status": "materialized",
            "canonical_replay_context_source_boundary": (
                "predecision_package_quality_and_broker_cost_no_outcome_fields"
            ),
            "source_hash": "source-hash-fixture",
            "source_path": "route/source-bound-fixture.jsonl",
            "replacement_reallocation_quality_score": 0.64,
            "replacement_reallocation_quality_uses_outcome_fields": False,
            "selector_action": "open-reduced-risk",
            "scheduler_materialization_action_intent": "new_position",
        },
        source_bound_allowed=True,
    )

    assert packet["canonical_replay_candidate_instance_key"] == instance_key
    assert packet["risk_finalizer_probe_instance_key"] == instance_key
    assert packet["candidate_instance_identity_status"] == "materialized"
    assert packet["timeframe"] == "M15"
    assert packet["session_bucket"] == "ny"
    context = packet["canonical_replay_context"]
    assert context["timeframe"] == "M15"
    assert context["source_hash"] == "source-hash-fixture"
    assert context["source_path"] == "route/source-bound-fixture.jsonl"
    assert context["same_symbol_replay_exposure_context"]["same_side_pending_ids"] == [
        "pending-context"
    ]
    assert context["replacement_reallocation_quality_score"] == 0.64
    assert context["replacement_reallocation_quality_uses_outcome_fields"] is False


def test_selected_package_bridge_executable_gate_requires_quality_floors() -> None:
    bridge = load_selected_package_replay_bridge()

    base = {
        "decision_time_utc": "2025-01-01T00:15:00+00:00",
        "ultimate_package_effective_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_admission_count": 1,
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "candidate_cost_r_fallback_is_authority": False,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "expected_net_r": 0.80,
        "probability": 0.75,
        "fill_probability": 0.25,
        **_execution_fillability_fields(0.25),
        "scheduler_materialization_action_intent": "new_position",
        "selector_action": "trade",
    }

    assert bridge.executable_package_use_detail(
        base,
        source_bound_allowed=True,
    ) == (True, "broker_cost_selector_and_scheduler_action_executable")

    low_net = {**base, "expected_net_r": 0.39}
    assert bridge.executable_package_use_detail(
        low_net,
        source_bound_allowed=True,
    ) == (False, "expected_net_r_below_floor:0.390")

    low_probability = {**base, "probability": 0.57}
    assert bridge.executable_package_use_detail(
        low_probability,
        source_bound_allowed=True,
    ) == (False, "probability_below_floor:0.570")

    low_fill = {
        **base,
        "fill_probability": 0.24,
        **_execution_fillability_fields(0.24),
    }
    assert bridge.executable_package_use_detail(
        low_fill,
        source_bound_allowed=True,
    ) == (
        False,
        "execution_fillability_below_floor:0.240:"
        "unit_test.predecision_limit_fillability_probability",
    )

    reduced_risk_low_fill_allowed = {
        **base,
        "candidate_id": "bridge-open-reduced-low-fill",
        "symbol": "GBPJPY",
        "side": "LONG",
        "decision_time_utc": "2026-06-01T17:15:00+00:00",
        "expected_net_r": 0.70,
        "probability": 0.70,
        "fill_probability": 0.20,
        "selector_action": "open-reduced-risk",
        "selector_reason": "fixture_explicit_open_reduced_risk",
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "fixture.predecision.expected_net_r",
            "probability": "fixture.predecision.probability",
            "fill_probability": "fixture.predecision_limit_fillability.fill_probability",
            "source_completeness": "fixture.predecision.source_completeness",
        },
        "candidate_decision_quality_alias_status": "exact_materialized",
        "candidate_decision_quality_source_boundary": (
            "predecision_fixture_quality_fields_no_outcome"
        ),
        "package_open_reduced_authority_allowed": True,
        "source_bound_package_candidate_use_allowed": True,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "package_replay_order_executable_candidate_use_allowed": True,
        "package_replay_order_executable_candidate_use_allowed_reason": (
            "fixture_signed_open_reduced_order_executable"
        ),
        "package_replay_order_executable_authority_source": (
            "fixture_signed_open_reduced_predecision_authority"
        ),
        "ultimate_candidate_package_open_reduced_risk_authority": {
            "allowed": True,
            "authority_family": "fixture_explicit_open_reduced_risk",
            "current_config_allowed": True,
            "source_boundary": (
                "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
            ),
        },
    }
    instance_key = (
        f"{reduced_risk_low_fill_allowed['candidate_id']}@@"
        f"{reduced_risk_low_fill_allowed['decision_time_utc']}"
    )
    reduced_risk_low_fill_allowed.update(
        {
            "candidate_id_source": "candidate_id",
            "canonical_replay_candidate_instance_key": instance_key,
            "source_bound_replay_candidate_instance_key": instance_key,
            "candidate_instance_identity_status": "materialized",
        }
    )
    signed_low_fill_authority = _complete_test_authority_surface(
        reduced_risk_low_fill_allowed,
        selector_action="open-reduced-risk",
        selector_reason="fixture_explicit_open_reduced_risk",
        authority=reduced_risk_low_fill_allowed[
            "ultimate_candidate_package_open_reduced_risk_authority"
        ],
        action_intent="new_position",
    )
    reduced_risk_low_fill_allowed.update(signed_low_fill_authority)
    reduced_risk_low_fill_allowed[
        "ultimate_candidate_package_open_reduced_risk_authority"
    ] = dict(signed_low_fill_authority)
    assert bridge.executable_package_use_detail(
        reduced_risk_low_fill_allowed,
        source_bound_allowed=True,
    ) == (True, "broker_cost_selector_and_scheduler_action_executable")


def test_selected_package_bridge_quality_fields_preserve_open_reduced_authority() -> None:
    bridge = load_selected_package_replay_bridge()

    candidate = {
        "candidate_id": "candidate-open-reduced-denominator",
        "candidate_id_source": "candidate_id",
        "symbol": "GBPJPY",
        "side": "LONG",
        "decision_time_utc": "2026-06-01T17:15:00+00:00",
        "canonical_replay_candidate_instance_key": (
            "candidate-open-reduced-denominator@@2026-06-01T17:15:00+00:00"
        ),
        "source_bound_replay_candidate_instance_key": (
            "candidate-open-reduced-denominator@@2026-06-01T17:15:00+00:00"
        ),
        "candidate_instance_identity_status": "materialized",
        "ultimate_package_matched_member_axis_ids": [
            "member_axis:test:candidate-open-reduced-denominator:new_position"
        ],
        "selected_package_matched_member_axis_ids": [
            "member_axis:test:candidate-open-reduced-denominator:new_position"
        ],
        "entry_price": 193.10,
        "stop_loss": 192.70,
        "take_profit_1": 193.90,
        "expected_net_r": 0.72,
        "probability": 0.72,
        "fill_probability": 0.26,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "candidate_cost_r_fallback_is_authority": False,
        "selector_action": "open-reduced-risk",
        "selector_reason": "off_session_softening",
        "scheduler_materialization_action_intent": "new_position",
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "fixture.predecision.expected_net_r",
            "probability": "fixture.predecision.probability",
            "fill_probability": "fixture.predecision_limit_fillability.fill_probability",
            "source_completeness": "fixture.predecision.source_completeness",
        },
        "candidate_decision_quality_alias_status": "exact_materialized",
        "candidate_decision_quality_source_boundary": (
            "predecision_fixture_quality_fields_no_outcome"
        ),
        "source_bound_package_candidate_use_allowed": True,
        "ultimate_package_effective_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_admission_count": 1,
        "ultimate_candidate_package_open_reduced_risk_authority": {
            "allowed": True,
            "authority_family": "off_session_softening",
            "current_config_allowed": True,
            "source_boundary": (
                "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
            ),
        },
        "package_open_reduced_authority_allowed": True,
        "package_open_reduced_authority_family": "off_session_softening",
        "package_open_reduced_authority_current_config_allowed": True,
        "package_open_reduced_authority_source_boundary": (
            "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
        ),
        "package_replay_executable_candidate_use_allowed": True,
        "package_replay_order_executable_candidate_use_allowed": True,
        "package_replay_order_executable_candidate_use_allowed_reason": (
            "off_session_softening_signed_order_executable"
        ),
        "package_replay_order_executable_authority_source": (
            "off_session_softening_predecision_authority"
        ),
        "package_new_entry_authority_required": True,
        "package_new_entry_authority_valid": True,
        "package_new_entry_authority_status": (
            "valid_signed_predecision_new_entry_authority"
        ),
        "package_new_entry_authority_failures": [],
        "package_new_entry_authority_hash_sha256": "",
        "expected_package_new_entry_authority_hash_sha256": "",
        "package_new_entry_authority_payload_schema": (
            "ultimate_candidate_package.new_entry_authority.v1"
        ),
        "package_new_entry_authority_scope": (
            "selector_reduced_risk_to_scheduler_new_position"
        ),
        "package_new_entry_authority_target_action_intent": "new_position",
        "package_new_entry_authority_authority_field": (
            "ultimate_candidate_package_open_reduced_risk_authority"
        ),
        "package_new_entry_authority_authority_family": "off_session_softening",
        "package_new_entry_authority_source_boundary": (
            "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
        ),
        "package_new_entry_authority_uses_outcome_fields": False,
        "package_new_entry_authority_selector_action": "open-reduced-risk",
        "package_new_entry_authority_selector_reason": "off_session_softening",
    }
    signed_authority = _complete_test_authority_surface(
        candidate,
        selector_action="open-reduced-risk",
        selector_reason="off_session_softening",
        authority=candidate["ultimate_candidate_package_open_reduced_risk_authority"],
        action_intent="new_position",
    )
    candidate.update(signed_authority)
    candidate["ultimate_candidate_package_open_reduced_risk_authority"] = (
        dict(signed_authority)
    )

    fields = bridge.selected_package_bridge_quality_fields(candidate)

    assert fields["package_open_reduced_authority_allowed"] is True
    assert fields["package_open_reduced_authority_family"] == "off_session_softening"
    assert fields["package_open_reduced_authority_current_config_allowed"] is True
    assert fields["package_open_reduced_authority_source_boundary"] == (
        "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
    )
    assert (
        fields["ultimate_candidate_package_open_reduced_risk_authority"]["allowed"]
        is True
    )
    assert bridge.open_reduced_bridge_authority_allowed(fields) is True
    assert bridge.executable_package_use_detail(
        fields,
        source_bound_allowed=fields["source_bound_package_candidate_use_allowed"],
    ) == (True, "broker_cost_selector_and_scheduler_action_executable")


def test_selected_package_bridge_rejects_weak_signed_router_refusal_authority() -> None:
    bridge = load_selected_package_replay_bridge()
    instance_key = "candidate-weak-router-refusal@@2026-05-13T08:15:00+00:00"
    row = {
        "candidate_id": "candidate-weak-router-refusal",
        "candidate_id_source": "candidate_id",
        "symbol": "GBPJPY",
        "side": "LONG",
        "decision_time_utc": "2026-05-13T08:15:00+00:00",
        "canonical_replay_candidate_instance_key": instance_key,
        "source_bound_replay_candidate_instance_key": instance_key,
        "candidate_instance_identity_status": "materialized",
        "selector_action": "open-reduced-risk",
        "selector_reason": (
            "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk"
        ),
        "scheduler_materialization_action_intent": "new_position",
        "expected_net_r": 0.91,
        "probability": 0.78,
        "fill_probability": 0.92,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "candidate_cost_r_fallback_is_authority": False,
        "source_bound_package_candidate_use_allowed": True,
        "ultimate_package_effective_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_admission_count": 1,
        "package_replay_executable_candidate_use_allowed": True,
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "fixture.predecision.expected_net_r",
            "probability": "fixture.predecision.probability",
            "fill_probability": "fixture.predecision_limit_fillability.fill_probability",
            "source_completeness": "fixture.predecision.source_completeness",
        },
        "candidate_decision_quality_alias_status": "exact_materialized",
        "candidate_decision_quality_source_boundary": (
            "predecision_fixture_quality_fields_no_outcome"
        ),
        "ultimate_candidate_package_open_reduced_risk_authority": {
            "allowed": True,
            "authority_family": "router_refusal_softening",
            "current_config_allowed": True,
            "source_boundary": (
                "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
            ),
        },
        "package_open_reduced_authority_allowed": True,
        "package_open_reduced_authority_family": "router_refusal_softening",
        "package_open_reduced_authority_current_config_allowed": True,
        "package_open_reduced_authority_source_boundary": (
            "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
        ),
    }
    signed_authority = _complete_test_authority_surface(
        row,
        selector_action=row["selector_action"],
        selector_reason=row["selector_reason"],
        authority=row["ultimate_candidate_package_open_reduced_risk_authority"],
        action_intent="new_position",
    )
    row.update(signed_authority)
    row["ultimate_candidate_package_open_reduced_risk_authority"] = dict(
        signed_authority
    )
    row["expected_net_r"] = 0.84
    signed_authority = _resign_test_authority(row, expect_valid=True)

    assert bridge._candidate_quality_floor_requirements(row) == {
        "expected_net_r": 0.85,
        "probability": 0.75,
        "fill_probability": 0.60,
    }
    assert bridge.trusted_signed_package_new_entry_authority_surface(row) is False
    block_reason = bridge.signed_reduced_package_bridge_authority_block_reason(
        row,
        selector_action=row["selector_action"],
        selector_reason=row["selector_reason"],
        action_intent="new_position",
    )
    assert block_reason is not None
    assert "router_refusal_expected_net_r_below_floor" in block_reason

    row["expected_net_r"] = 0.91
    row["probability"] = 0.78
    row["fill_probability"] = 0.62
    row.update(_execution_fillability_fields(0.62))
    _resign_test_authority(row, expect_valid=True)

    assert bridge.trusted_signed_package_new_entry_authority_surface(row) is True
    assert bridge.signed_reduced_package_bridge_authority_block_reason(
        row,
        selector_action=row["selector_action"],
        selector_reason=row["selector_reason"],
        action_intent="new_position",
    ) is None


def test_selected_package_bridge_restamps_stale_signed_authority_for_resolved_scale_in() -> None:
    bridge = load_selected_package_replay_bridge()
    instance_key = "candidate-stale-scale-in@@2026-05-14T09:15:00+00:00"
    selector_reason = "source_bound_router_refusal_open_reduced_materialized_for_replay"
    row = {
        "candidate_id": "candidate-stale-scale-in",
        "candidate_id_source": "candidate_id",
        "symbol": "XAUUSD",
        "side": "LONG",
        "decision_time_utc": "2026-05-14T09:15:00+00:00",
        "canonical_replay_candidate_instance_key": instance_key,
        "source_bound_replay_candidate_instance_key": instance_key,
        "candidate_instance_identity_status": "materialized",
        "selector_action": "open-reduced-risk",
        "selector_reason": selector_reason,
        "scheduler_materialization_action_intent": "same_direction_scale_in",
        "lifecycle_action": "same_direction_scale_in",
        "expected_net_r": 1.18,
        "candidate_expected_net_r": 1.18,
        "probability": 0.83,
        "candidate_probability": 0.83,
        "fill_probability": 0.95,
        "candidate_fill_probability": 0.95,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "source_bound_router_refusal_materialization_floors": {
            "expected_net_r": 0.55,
            "probability": 0.70,
            "fill_probability": 0.55,
            "source_completeness": 0.95,
        },
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "candidate_cost_r_fallback_is_authority": False,
        "source_bound_package_candidate_use_allowed": True,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_admission_count": 1,
        "ultimate_package_matched_member_axis_count": 1,
        "ultimate_package_admission_member_axis_match_count": 1,
        "ultimate_package_matched_member_axis_ids": [
            "member_axis:XAUUSD:LONG:resolved_scale_in_fixture"
        ],
        "package_replay_executable_candidate_use_allowed": True,
        "package_replay_order_executable_candidate_use_allowed": True,
        "package_replay_order_executable_candidate_use_allowed_reason": (
            "resolved_scale_in_signed_order_executable"
        ),
        "package_replay_order_executable_authority_source": (
            "resolved_scale_in_predecision_authority"
        ),
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "fixture.predecision.expected_net_r",
            "probability": "fixture.predecision.probability",
            "fill_probability": "fixture.predecision_limit_fillability.fill_probability",
            "source_completeness": "fixture.predecision.source_completeness",
        },
        "candidate_decision_quality_alias_status": "exact_materialized",
        "candidate_decision_quality_source_boundary": (
            "predecision_fixture_quality_fields_no_outcome"
        ),
        "ultimate_candidate_package_open_reduced_risk_authority": {
            "allowed": True,
            "authority_family": "router_refusal_softening",
            "current_config_allowed": True,
            "selector_reason": selector_reason,
            "source_boundary": (
                "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
            ),
            "ultimate_package_soft_admission_override_allowed": True,
            "source_bound_candidate_use_allowed_now": True,
            "broker_cost_passed_for_package_router": True,
        },
        "package_open_reduced_authority_allowed": True,
        "package_open_reduced_authority_family": "router_refusal_softening",
    }
    stale_signed_authority = _complete_test_authority_surface(
        row,
        selector_action=row["selector_action"],
        selector_reason=row["selector_reason"],
        authority=row["ultimate_candidate_package_open_reduced_risk_authority"],
        action_intent="new_position",
    )
    row.update(stale_signed_authority)
    row["ultimate_candidate_package_open_reduced_risk_authority"] = (
        dict(stale_signed_authority)
    )
    stale_hash = row["package_new_entry_authority_hash_sha256"]

    assert (
        row["package_new_entry_authority_target_action_intent"] == "new_position"
    )
    assert (
        bridge.trusted_signed_package_new_entry_authority_surface(
            row,
            action_intent="same_direction_scale_in",
        )
        is False
    )

    materialized = bridge._bridge_materialize_signed_reduced_authority(
        row,
        selector_action=row["selector_action"],
        selector_reason=row["selector_reason"],
        action_intent="same_direction_scale_in",
    )

    assert materialized["package_new_entry_authority_target_action_intent"] == (
        "same_direction_scale_in"
    )
    assert materialized["package_new_entry_authority_hash_sha256"] != stale_hash
    assert materialized["package_new_entry_authority_bridge_materialized"] is True
    assert materialized["package_new_entry_authority_bridge_stale_target_action_intent"] == (
        "new_position"
    )
    assert (
        bridge.trusted_signed_package_new_entry_authority_surface(
            materialized,
            action_intent="same_direction_scale_in",
        )
        is True
    )
    assert bridge.signed_reduced_package_bridge_authority_block_reason(
        materialized,
        selector_action=materialized["selector_action"],
        selector_reason=materialized["selector_reason"],
        action_intent="same_direction_scale_in",
    ) is None


def test_selected_package_bridge_trusted_signed_surface_rejects_bridge_proxy_expected_net() -> None:
    bridge = load_selected_package_replay_bridge()
    instance_key = "candidate-stale-bridge-proxy@@2026-05-13T08:15:00+00:00"
    row = {
        "candidate_id": "candidate-stale-bridge-proxy",
        "symbol": "XAUUSD",
        "side": "LONG",
        "decision_time_utc": "2026-05-13T08:15:00+00:00",
        "canonical_replay_candidate_instance_key": instance_key,
        "source_bound_replay_candidate_instance_key": instance_key,
        "candidate_instance_identity_status": "materialized",
        "selector_action": "open-reduced-risk",
        "selector_reason": (
            "ultimate_candidate_package_numeric_disagreement_open_reduced_risk"
        ),
        "scheduler_materialization_action_intent": "new_position",
        "expected_net_r": 1.18,
        "candidate_expected_net_r": 1.18,
        "probability": 0.83,
        "candidate_probability": 0.83,
        "fill_probability": 0.76,
        "candidate_fill_probability": 0.76,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "candidate_cost_r_fallback_is_authority": False,
        "source_bound_package_candidate_use_allowed": True,
        "ultimate_package_effective_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_admission_count": 1,
        "package_replay_executable_candidate_use_allowed": True,
        "selected_policy_for_expected_net_r": "partial_be_runner",
        "expected_net_r_selected_policy": "partial_be_runner",
        "selected_policy_expected_net_calibration_status": "calibrated",
        "selected_policy_expected_net_calibrated": True,
        "selected_policy_expected_net_calibration_required": True,
        "selected_policy_expected_net_calibration_source": (
            "selected_policy_replay_calibration_packet"
        ),
        "selected_policy_expected_net_calibration_source_boundary": (
            "predecision_fixture_quality_fields_no_outcome"
        ),
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "fixture.predecision.expected_net_r",
            "probability": "fixture.predecision.probability",
            "fill_probability": "fixture.predecision_limit_fillability.fill_probability",
            "source_completeness": "fixture.predecision.source_completeness",
        },
        "candidate_decision_quality_alias_status": "exact_materialized",
        "candidate_decision_quality_source_boundary": (
            "predecision_fixture_quality_fields_no_outcome"
        ),
        "ultimate_candidate_package_open_reduced_risk_authority": {
            "allowed": True,
            "applies": True,
            "authority_family": "numeric_disagreement_softening",
            "current_config_allowed": True,
            "source_boundary": (
                "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
            ),
        },
        "package_open_reduced_authority_allowed": True,
        "package_open_reduced_authority_family": "numeric_disagreement_softening",
        "package_open_reduced_authority_current_config_allowed": True,
        "package_open_reduced_authority_source_boundary": (
            "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
        ),
    }
    signed_authority = _complete_test_authority_surface(
        row,
        selector_action=row["selector_action"],
        selector_reason=row["selector_reason"],
        authority=row["ultimate_candidate_package_open_reduced_risk_authority"],
        action_intent="new_position",
    )
    row.update(signed_authority)
    row["ultimate_candidate_package_open_reduced_risk_authority"] = dict(
        signed_authority
    )

    row["selected_policy_expected_net_calibration_source"] = (
        "packets.candidate_expected_net_r"
    )
    row[
        "package_new_entry_authority_selected_policy_expected_net_calibration_source"
    ] = "packets.candidate_expected_net_r"

    assert bridge.trusted_signed_package_new_entry_authority_surface(row) is False
    block_reason = bridge.signed_reduced_package_bridge_authority_block_reason(
        row,
        selector_action=row["selector_action"],
        selector_reason=row["selector_reason"],
        action_intent="new_position",
    )
    assert block_reason is not None
    assert "selected_policy_expected_net_bridge_proxy_not_executable" in block_reason

    row["scheduler_materialization_action_intent"] = "new_position"
    row["scheduler_materialization_source_required_fail_closed_override_applied"] = True
    row["scheduler_materialization_override_reason"] = (
        "source_required_fail_closed_package_new_position_source_gap_"
        "reconciled_for_replay"
    )
    allowed, reason = bridge.executable_package_use_detail(
        row,
        source_bound_allowed=True,
    )
    assert allowed is False
    assert "selected_policy_expected_net_bridge_proxy_not_executable" in reason


def test_selected_package_bridge_rejects_router_refusal_below_source_floor() -> None:
    bridge = load_selected_package_replay_bridge()
    instance_key = "candidate-router-refusal-source-gap@@2026-05-13T08:15:00+00:00"
    row = {
        "candidate_id": "candidate-router-refusal-source-gap",
        "symbol": "GBPJPY",
        "side": "LONG",
        "decision_time_utc": "2026-05-13T08:15:00+00:00",
        "canonical_replay_candidate_instance_key": instance_key,
        "source_bound_replay_candidate_instance_key": instance_key,
        "candidate_instance_identity_status": "materialized",
        "selector_action": "open-reduced-risk",
        "selector_reason": (
            "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk"
        ),
        "scheduler_materialization_action_intent": "new_position",
        "expected_net_r": 1.12,
        "probability": 0.91,
        "fill_probability": 0.92,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "candidate_cost_r_fallback_is_authority": False,
        "source_bound_package_candidate_use_allowed": True,
        "ultimate_package_effective_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_admission_count": 1,
        "package_replay_executable_candidate_use_allowed": True,
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "fixture.predecision.expected_net_r",
            "probability": "fixture.predecision.probability",
            "fill_probability": "fixture.predecision_limit_fillability.fill_probability",
            "source_completeness": "fixture.predecision.source_completeness",
        },
        "candidate_decision_quality_alias_status": "exact_materialized",
        "candidate_decision_quality_source_boundary": (
            "predecision_fixture_quality_fields_no_outcome"
        ),
        "ultimate_candidate_package_open_reduced_risk_authority": {
            "allowed": True,
            "authority_family": "router_refusal_softening",
            "current_config_allowed": True,
            "source_boundary": (
                "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
            ),
        },
        "package_open_reduced_authority_allowed": True,
        "package_open_reduced_authority_family": "router_refusal_softening",
        "package_open_reduced_authority_current_config_allowed": True,
        "package_open_reduced_authority_source_boundary": (
            "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
        ),
    }
    signed_authority = _complete_test_authority_surface(
        row,
        selector_action=row["selector_action"],
        selector_reason=row["selector_reason"],
        authority=row["ultimate_candidate_package_open_reduced_risk_authority"],
        action_intent="new_position",
    )
    row.update(signed_authority)
    row["ultimate_candidate_package_open_reduced_risk_authority"] = dict(
        signed_authority
    )
    row["source_completeness"] = 0.94
    _resign_test_authority(row, expect_valid=True)

    assert bridge.trusted_signed_package_new_entry_authority_surface(row) is False
    assert bridge.executable_package_use_detail(
        row,
        source_bound_allowed=True,
    ) == (False, "source_completeness_below_floor:0.940")


def test_selected_package_bridge_requires_cost_and_source_authority_for_execution() -> None:
    bridge = load_selected_package_replay_bridge()

    missing_cost_allowed, missing_cost_reason = bridge.executable_package_use_detail(
        {
            "ultimate_package_effective_source_bound_candidate_use_allowed": True,
            "ultimate_package_effective_admission_count": 1,
            "source_completeness": 1.0,
            "source_completeness_status": "source_completeness_present",
            "scheduler_materialization_action_intent": "new_position",
            "selector_action": "trade",
        },
        source_bound_allowed=True,
    )
    degraded_source_allowed, degraded_source_reason = (
        bridge.executable_package_use_detail(
            {
                "ultimate_package_effective_source_bound_candidate_use_allowed": True,
                "ultimate_package_effective_admission_count": 1,
                "pretrade_cost_packet_status": "PASSED",
                "cost_authority": "broker_calibrated_replay_cost",
                "cost_source_gap_status": "source_bound_cost_authority_present",
                "candidate_cost_r_fallback_is_authority": False,
                "source_completeness": 0.25,
                "source_completeness_status": (
                    "source_completeness_missing_degraded_default"
                ),
                "scheduler_materialization_action_intent": "new_position",
                "selector_action": "trade",
            },
            source_bound_allowed=True,
        )
    )

    assert missing_cost_allowed is False
    assert missing_cost_reason == "broker_cost_packet_status_missing"
    assert degraded_source_allowed is False
    assert degraded_source_reason == "source_completeness_below_floor:0.250"


def test_selected_package_bridge_refused_cost_stays_source_bound_non_executable() -> None:
    bridge = load_selected_package_replay_bridge()
    reason = "spread_r_exceeds_selected_cell_limit"
    candidate = {
        "candidate_id": "refused-cost-source-bound",
        "symbol": "XAUUSD",
        "side": "LONG",
        "decision_time_utc": "2026-05-05T07:15:00+00:00",
        "source_bound_package_candidate_use_allowed": True,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "ultimate_package_admission_candidate_use_allowed": True,
        "ultimate_package_effective_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_admission_count": 1,
        "expected_net_r": 0.92,
        "probability": 0.78,
        "fill_probability": 0.81,
        **_execution_fillability_fields(0.81),
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "pretrade_cost_packet_status": "REFUSED",
        "pretrade_cost_refusal_reasons": [reason],
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "scheduler_materialization_action_intent": "new_position",
        "selector_action": "trade",
    }

    assert bridge.executable_package_use_detail(
        candidate,
        source_bound_allowed=True,
    ) == (False, f"broker_cost_packet_refused:{reason}")

    fields = bridge.selected_package_bridge_quality_fields(candidate)
    compact = bridge.compact_candidate_rows([candidate], [])[0]

    assert (
        fields["ultimate_package_effective_source_bound_candidate_diagnostic_present"]
        is True
    )
    for row in (fields, compact):
        assert row["source_bound_package_candidate_use_allowed"] is True
        assert row["package_replay_source_bound_candidate_use_allowed"] is True
        assert row["package_source_bound_admission_diagnostic"] is True
        assert (
            row["ultimate_package_effective_source_bound_candidate_use_allowed"]
            is False
        )
        assert row["ultimate_package_effective_executable_authority_allowed"] is False
        assert row["expected_net_r"] == 0.92
        assert row["probability"] == 0.78
        assert row["fill_probability"] == 0.81
        assert row["pretrade_cost_packet_status"] == "REFUSED"
        assert row["pretrade_cost_refusal_reasons"] == [reason]
        assert row["package_replay_candidate_use_allowed"] is False
        assert row["package_replay_executable_candidate_use_allowed"] is False
        assert row["replay_candidate_use_allowed_now"] is False
        assert (
            row["package_replay_executable_candidate_use_allowed_reason"]
            == f"broker_cost_packet_refused:{reason}"
        )


def test_broad_replay_headline_excludes_source_required_lifecycle_gap_trades() -> None:
    harness = load_broad_replay_harness()
    ordinary_trade = {
        "candidate_id": "ordinary",
        "trading_day": "2026-05-13",
        "symbol": "XAUUSD",
        "side": "LONG",
        "net_proxy_r": 1.0,
        "gross_r": 1.1,
        "final_r": 1.1,
        "expected_cost_r": 0.1,
        "total_execution_cost_r": 0.1,
        "pnl_cash": 100.0,
        "risk_cash": 100.0,
        "risk_pct": 1.0,
        "same_symbol_lifecycle_action": "new_position",
        "broker_order_lifecycle_truth_satisfied": False,
    }
    source_required_trade = {
        "candidate_id": "source_required",
        "trading_day": "2026-05-13",
        "symbol": "XAUUSD",
        "side": "LONG",
        "net_proxy_r": 2.0,
        "gross_r": 2.1,
        "final_r": 2.1,
        "expected_cost_r": 0.1,
        "total_execution_cost_r": 0.1,
        "pnl_cash": 200.0,
        "risk_cash": 100.0,
        "risk_pct": 1.0,
        "same_symbol_lifecycle_action": "source_required_fail_closed",
        "execution_manager_live_promotion_blocker_reasons": [
            "same_symbol_lifecycle_v4_not_permitted:source_required_fail_closed"
        ],
        "scheduler_materialization_source_required_fail_closed_override_applied": True,
        "broker_order_lifecycle_truth_satisfied": False,
    }
    signed_source_required_trade = {
        "candidate_id": "signed_source_required",
        "simulated_trade_id": "signed-source-required-trade",
        "candidate_id_source": "candidate_id",
        "decision_time_utc": "2026-05-13T08:00:00+00:00",
        "canonical_replay_candidate_instance_key": (
            "signed_source_required@@2026-05-13T08:00:00+00:00"
        ),
        "source_bound_replay_candidate_instance_key": (
            "signed_source_required@@2026-05-13T08:00:00+00:00"
        ),
        "candidate_instance_identity_status": "materialized",
        "trading_day": "2026-05-13",
        "symbol": "XAUUSD",
        "side": "LONG",
        "net_proxy_r": 3.0,
        "gross_r": 3.1,
        "final_r": 3.1,
        "expected_cost_r": 0.1,
        "total_execution_cost_r": 0.1,
        "pnl_cash": 300.0,
        "risk_cash": 100.0,
        "risk_pct": 1.0,
        "selector_action": "open-reduced-risk",
        "selector_reason": "signed_source_required_lifecycle_replay",
        "scheduler_materialization_action_intent": "same_direction_scale_in",
        "expected_net_r": 0.8,
        "probability": 0.8,
        "fill_probability": 0.8,
        **_execution_fillability_fields(0.8),
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
            "predecision_fixture_quality_no_outcome_fields"
        ),
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "candidate_cost_r_fallback_is_authority": False,
        "source_bound_package_candidate_use_allowed": True,
        "source_required_lifecycle_origin": True,
        "source_required_lifecycle_origin_reason": "source_required_fail_closed",
        "source_required_fail_closed_replay_override_applied": True,
        "scheduler_materialization_source_required_fail_closed_override_applied": True,
        "scheduler_materialization_override_reason": (
            "source_required_fail_closed_package_source_reconciled_for_replay"
        ),
        "broker_order_lifecycle_truth_satisfied": False,
        "same_symbol_lifecycle_action": "same_direction_scale_in",
        "lifecycle_action": "same_direction_scale_in",
        "risk_lifecycle_action": "same_direction_scale_in",
        "risk_lifecycle_action_reconciled_from_scheduler": True,
        "execution_manager_same_symbol_lifecycle_permission_reconcile_applied": True,
        "scheduler_materialization_source_required_fail_closed_lifecycle_context_present": True,
        "scheduler_materialization_source_required_fail_closed_lifecycle_context_source": "pending_order",
        "package_replay_executable_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed_reason": "broker_cost_and_scheduler_action_executable",
        "package_replay_order_executable_candidate_use_allowed": True,
        "package_replay_order_executable_candidate_use_allowed_reason": (
            "signed_source_required_lifecycle_order_executable"
        ),
        "package_replay_order_executable_authority_source": (
            "signed_source_required_lifecycle_predecision_authority"
        ),
        "broker_pretrade_cost_executable": True,
        "source_gap_cost_fallback_blocked": False,
        "ultimate_candidate_package_open_reduced_risk_authority": {
            "applies": True,
            "allowed": True,
            "authority_family": "source_required_lifecycle_repair",
            "authority_source": (
                "signed_source_required_lifecycle_predecision_authority"
            ),
            "source_boundary": (
                "predecision_source_required_lifecycle_no_outcome_fields"
            ),
        },
    }
    signed_source_required_authority = _complete_test_authority_surface(
        signed_source_required_trade,
        selector_action="open-reduced-risk",
        selector_reason="signed_source_required_lifecycle_replay",
        action_intent="same_direction_scale_in",
        authority=signed_source_required_trade[
            "ultimate_candidate_package_open_reduced_risk_authority"
        ],
    )
    signed_source_required_trade.update(signed_source_required_authority)
    signed_source_required_trade[
        "ultimate_candidate_package_open_reduced_risk_authority"
    ] = dict(signed_source_required_authority)
    invalid_reason_source_required_trade = {
        **signed_source_required_trade,
        "candidate_id": "invalid_reason_source_required",
        "scheduler_materialization_override_reason": "bogus_source_required_reason",
    }
    profit_harvest_m1_diagnostic_trade = {
        "candidate_id": "profit_harvest_m1_diagnostic",
        "trading_day": "2026-05-13",
        "symbol": "XAUUSD",
        "side": "LONG",
        "net_proxy_r": 5.0,
        "gross_r": 5.1,
        "final_r": 5.1,
        "expected_cost_r": 0.1,
        "total_execution_cost_r": 0.1,
        "pnl_cash": 500.0,
        "risk_cash": 100.0,
        "risk_pct": 1.0,
        "profit_harvest_mfe_capture_replay_exit_final_r_authority": False,
        "profit_harvest_mfe_capture_replay_exit_final_r_authority_status": (
            "m1_ordered_path_proxy_final_r_diagnostic_not_authority"
        ),
    }

    annotated = harness.annotate_rows(
        [
            ordinary_trade,
            source_required_trade,
            signed_source_required_trade,
            invalid_reason_source_required_trade,
            profit_harvest_m1_diagnostic_trade,
        ],
        profile=harness.PROFILE_REPAIRED,
        split="holdout",
        chunk_id="test",
        row_type="simulated_trade",
    )

    assert annotated[0]["headline_result_eligible"] is True
    assert annotated[1]["headline_result_eligible"] is False
    assert annotated[1]["result_scope"] == (
        "diagnostic_source_required_lifecycle_gap_not_headline"
    )
    assert annotated[2]["headline_result_eligible"] is True
    assert annotated[2]["strict_full_package_parity_result_eligible"] is False
    assert annotated[2]["source_required_lifecycle_replay_headline_authorized"] is True
    assert annotated[2]["result_scope"] == (
        "headline_replay_signed_source_required_lifecycle_result"
    )
    assert annotated[3]["headline_result_eligible"] is False
    assert annotated[3]["source_required_lifecycle_replay_headline_authorized"] is False
    assert annotated[3]["result_scope"] == (
        "diagnostic_source_required_lifecycle_gap_not_headline"
    )
    assert annotated[4]["headline_result_eligible"] is False
    assert annotated[4]["strict_full_package_parity_result_eligible"] is False
    assert annotated[4]["result_scope"] == (
        "diagnostic_profit_harvest_m1_proxy_not_headline"
    )
    explicit_diagnostic_overlay_with_base_terminal = {
        **profit_harvest_m1_diagnostic_trade,
        "candidate_id": "profit_harvest_m1_diagnostic_with_base_terminal",
        "close_reason": "target_reached_before_stop",
        "terminal_outcome": "target_reached_before_stop",
        "profit_harvest_mfe_capture_replay_exit_diagnostic_only": True,
        "profit_harvest_mfe_capture_replay_bound": False,
    }
    annotated_overlay = harness.annotate_rows(
        [explicit_diagnostic_overlay_with_base_terminal],
        profile=harness.PROFILE_REPAIRED,
        split="holdout",
        chunk_id="test",
        row_type="simulated_trade",
    )[0]
    assert annotated_overlay["headline_result_eligible"] is True
    assert annotated_overlay["strict_full_package_parity_result_eligible"] is True
    assert (
        annotated_overlay[
            "profit_harvest_m1_proxy_diagnostic_overlay_base_headline_allowed"
        ]
        is True
    )
    assert annotated_overlay["profit_harvest_m1_proxy_replay_headline_eligible"] is True
    assert annotated_overlay["result_scope"] == "headline_replay_result"

    accumulator = harness.SummaryAccumulator()
    accumulator.add_result(
        profile=harness.PROFILE_REPAIRED,
        split="holdout",
        days=("2026-05-13",),
        result={
            "ledgers": {
                "asof": [],
                "scorecard": [],
                "candidate": [],
                "order": [],
                "event": [],
                "oracle": [],
                "missed": [],
                "trade": [
                    ordinary_trade,
                    source_required_trade,
                    signed_source_required_trade,
                    profit_harvest_m1_diagnostic_trade,
                ],
            }
        },
    )
    stat = accumulator.serializable_stats()[0]

    assert stat["trade_rows"] == 4
    assert stat["filled_trade_count"] == 2
    assert stat["all_executed_net_r"] == 4.0
    assert stat["net_r"] == 4.0
    assert stat["headline_net_r"] == 4.0
    assert stat["headline_filled_trade_count"] == 2
    assert stat["strict_full_package_filled_trade_count"] == 1
    assert stat["strict_full_package_net_r"] == 1.0
    assert stat["diagnostic_only_trade_rows"] == 2
    assert stat["diagnostic_only_net_r"] == 7.0
    assert stat["source_required_lifecycle_gap_trade_rows"] == 1
    assert stat["source_required_lifecycle_gap_net_r"] == 2.0
    assert stat["stress"]["trade_count"] == 2
    assert stat["monte_carlo"]["trade_count"] == 2
    assert stat["headline_result_exclusion_reason_counts"] == {
        "headline_result_eligible": 2,
        "source_required_fail_closed_lifecycle_source_gap_diagnostic_only": 1,
        "profit_harvest_m1_proxy_final_r_diagnostic_not_headline_authority": 1,
    }


def test_bucket_rows_use_headline_authority_and_preserve_all_trade_totals() -> None:
    harness = load_broad_replay_harness()

    headline_trade = {
        "trading_day": "2026-05-13",
        "symbol": "XAUUSD",
        "session": "ny",
        "framework": "fvg_fill",
        "dynamic_geometry_policy": "momentum_exhaustion",
        "risk_decision_reason": "selector_open_reduced_risk_origin_preserved",
        "net_proxy_r": 1.9,
        "gross_r": 2.0,
        "final_r": 2.0,
        "expected_cost_r": 0.1,
        "pnl_cash": 190.0,
        "risk_cash": 100.0,
        "risk_pct": 1.0,
    }
    diagnostic_trade = {
        **headline_trade,
        "net_proxy_r": 0.4,
        "gross_r": 0.5,
        "final_r": 0.5,
        "expected_cost_r": 0.1,
        "pnl_cash": 40.0,
        "profit_harvest_mfe_capture_replay_exit_final_r_authority_status": (
            "m1_ordered_path_proxy_final_r_diagnostic_not_authority"
        ),
    }
    bucket = {
        "trading_day": "2026-05-13",
        "symbol": "XAUUSD",
        "session": "ny",
        "framework": "fvg_fill",
        "policy": "momentum_exhaustion",
        "risk_reason": "selector_open_reduced_risk_origin_preserved",
        "filled_trade_count": 2,
        "winner_count": 2,
        "loser_count": 0,
        "net_proxy_r": 2.3,
        "total_r": 2.3,
        "gross_r": 2.5,
        "expected_cost_r": 0.2,
        "cash_pnl": 230.0,
        "risk_cash": 200.0,
        "risk_cash_sum": 200.0,
        "risk_pct_sum": 2.0,
    }

    repaired = harness.headline_authority_bucket_rows(
        [bucket],
        [headline_trade, diagnostic_trade],
    )[0]

    assert repaired["bucket_result_authority"] == (
        "headline_result_eligible_trade_rows_with_all_trade_diagnostic_fields"
    )
    assert repaired["all_trade_net_proxy_r"] == 2.3
    assert repaired["all_trade_filled_trade_count"] == 2
    assert repaired["filled_trade_count"] == 1
    assert repaired["winner_count"] == 1
    assert repaired["net_proxy_r"] == 1.9
    assert repaired["total_r"] == 1.9
    assert repaired["gross_r"] == 2.0
    assert repaired["expected_cost_r"] == 0.1
    assert repaired["cash_pnl"] == 190.0
    assert repaired["risk_cash"] == 100.0
    assert repaired["diagnostic_only_trade_count"] == 1
    assert repaired["diagnostic_only_net_proxy_r"] == 0.4


def test_flow_diagnostic_trade_metrics_separate_headline_from_diagnostic() -> None:
    flow = load_broad_replay_flow_analyzer()

    metric = flow.Metric()
    metric.add_trade(
        {
            "net_proxy_r": 1.9,
            "gross_r": 2.0,
            "final_r": 2.0,
            "expected_cost_r": 0.1,
            "pnl_cash": 190.0,
            "risk_cash": 100.0,
            "risk_pct": 1.0,
            "headline_result_eligible": True,
            "headline_result_exclusion_reason": "headline_result_eligible",
        }
    )
    metric.add_trade(
        {
            "net_proxy_r": 0.4,
            "gross_r": 0.5,
            "final_r": 0.5,
            "expected_cost_r": 0.1,
            "pnl_cash": 40.0,
            "risk_cash": 100.0,
            "risk_pct": 1.0,
            "headline_result_eligible": False,
            "headline_result_exclusion_reason": (
                "profit_harvest_m1_proxy_final_r_diagnostic_not_headline_authority"
            ),
            "result_scope": "diagnostic_profit_harvest_m1_proxy_not_headline",
        }
    )

    payload = metric.as_dict()
    assert payload["rows"] == 2
    assert payload["all_trade_rows"] == 2
    assert payload["all_trade_net_r"] == 2.3
    assert payload["all_trade_win_count"] == 2
    assert payload["all_trade_loss_count"] == 0
    assert payload["all_trade_flat_count"] == 0
    assert payload["diagnostic_only_trade_rows"] == 1
    assert payload["diagnostic_only_net_r"] == 0.4
    assert payload["diagnostic_only_win_count"] == 1
    assert payload["diagnostic_only_loss_count"] == 0
    assert payload["diagnostic_only_flat_count"] == 0
    assert payload["filled_count"] == 1
    assert payload["scoreable_rows"] == 1
    assert payload["net_r"] == 1.9
    assert payload["cash_pnl"] == 190.0
    assert payload["counters"]["headline_result_exclusion_reason"] == {
        "headline_result_eligible": 1,
        "profit_harvest_m1_proxy_final_r_diagnostic_not_headline_authority": 1,
    }


def test_flow_evidence_boundary_preserves_mixed_tick_and_m1_sources() -> None:
    flow = load_broad_replay_flow_analyzer()

    boundary = flow.trade_r_evidence_boundary(
        [
            {
                "symbol": "XAUUSD",
                "net_proxy_r": 1.1,
                "path_source": "tick",
                "path_source_timeframe": "TICK",
                "ordered_tick_truth_satisfied": True,
                "entry_fill_authority_source_boundary": (
                    "post_asof_ordered_tick_entry_path"
                ),
                "fill_realism_source_boundary": "post_asof_ordered_tick_path",
                "terminal_r_scoreability_status": (
                    "ordered_tick_terminal_r_scoreable"
                ),
            },
            {
                "symbol": "EURUSD",
                "net_proxy_r": 0.8,
                "path_source": "tick",
                "path_source_timeframe": "TICK",
                "ordered_tick_truth_satisfied": True,
                "entry_fill_authority_source_boundary": (
                    "predecision_marketable_limit_at_decision"
                ),
                "fill_realism_source_boundary": (
                    "predecision_market_price_source_time_at_or_before_decision"
                ),
                "terminal_r_scoreability_status": (
                    "ordered_tick_terminal_r_scoreable"
                ),
            },
            {
                "symbol": "US30_cash",
                "net_proxy_r": 1.9,
                "path_source": "m1",
                "path_source_timeframe": "M1",
                "ordered_tick_truth_satisfied": False,
                "entry_fill_authority_source_boundary": (
                    "predecision_marketable_limit_at_decision"
                ),
                "fill_realism_source_boundary": (
                    "predecision_market_price_source_time_at_or_before_decision"
                ),
                "terminal_r_scoreability_status": (
                    "ordered_m1_proxy_terminal_r_scoreable"
                ),
            },
            {
                "symbol": "UKOIL_cash",
                "net_proxy_r": None,
                "path_source": "m1",
                "path_source_timeframe": "M1",
                "ordered_tick_truth_satisfied": False,
                "entry_fill_authority_source_boundary": (
                    "predecision_marketable_limit_at_decision"
                ),
                "fill_realism_source_boundary": (
                    "predecision_market_price_source_time_at_or_before_decision"
                ),
                "terminal_r_scoreability_status": (
                    "entry_fill_executable_terminal_r_ordered_tick_sequence_required"
                ),
            },
        ]
    )

    assert boundary["executed_trade_r_source"] == (
        "mixed_simulated_ordered_path_sources"
    )
    assert boundary["executed_trade_r_source_mix_status"] == "mixed_sources"
    assert boundary["executed_trade_r_source_row_count"] == 4
    assert boundary["executed_trade_r_source_counts"] == {
        "simulated_ordered_m1_path_proxy": 2,
        "simulated_ordered_tick_path": 2,
    }
    assert boundary["scoreable_trade_r_source_counts"] == {
        "simulated_ordered_m1_path_proxy": 1,
        "simulated_ordered_tick_path": 2,
    }
    assert boundary["unscoreable_trade_r_source_counts"] == {
        "simulated_ordered_m1_path_proxy": 1,
    }
    assert boundary["executed_trade_r_source_by_symbol"]["XAUUSD"] == {
        "simulated_ordered_tick_path": 1
    }
    assert boundary["executed_trade_r_source_by_symbol"]["US30_cash"] == {
        "simulated_ordered_m1_path_proxy": 1
    }
    assert boundary["path_source_counts"] == {"m1": 2, "tick": 2}
    assert boundary["path_source_timeframe_counts"] == {"M1": 2, "TICK": 2}
    assert "all broad replay R" not in boundary["missing_or_reconstructed_r"]


def test_terminal_unscoreable_entry_fill_is_physical_missing_r_not_flat_or_headline() -> None:
    harness = load_broad_replay_harness()
    flow = load_broad_replay_flow_analyzer()
    terminal_status = (
        "entry_fill_executable_terminal_r_ordered_tick_sequence_required"
    )
    trade = {
        "candidate_id": "terminal-unscoreable",
        "trading_day": "2026-05-13",
        "symbol": "XAUUSD",
        "side": "LONG",
        "entry_fill_executable": True,
        "terminal_r_scoreable": False,
        "terminal_r_scoreability_status": terminal_status,
        "result_scoreable": False,
        "trade_state": "closed_terminal_r_unscoreable",
        "accepted_risk_budget_consumed_by_fill": True,
        "accepted_risk_reservation_released": False,
        "accepted_risk_reservation_transition": (
            "pending_order_to_filled_position"
        ),
        "final_r": None,
        "gross_r": None,
        "net_proxy_r": None,
        "net_r": None,
        "pnl_cash": None,
        "expected_cost_r": 0.101557995608,
        "total_execution_cost_r": 0.101558,
        "risk_cash": 100.0,
        "risk_pct": 0.1,
        "risk_decision": "trade",
        "risk_expression_ladder_tier": "full",
        "risk_expression_ladder": {
            "ladder_tier": "full",
            "risk_decision": "trade",
        },
    }
    scoreable_trade = {
        "candidate_id": "terminal-scoreable-diagnostic",
        "trading_day": "2026-05-13",
        "symbol": "XAUUSD",
        "side": "LONG",
        "entry_fill_executable": True,
        "terminal_r_scoreable": True,
        "terminal_r_scoreability_status": "ordered_m1_proxy_terminal_r_scoreable",
        "headline_result_authority": False,
        "headline_result_authority_status": (
            "m1_proxy_replay_not_headline_authority_ordered_tick_required"
        ),
        "result_scoreable": True,
        "trade_state": "closed",
        "accepted_risk_budget_consumed_by_fill": True,
        "accepted_risk_reservation_released": False,
        "accepted_risk_reservation_transition": (
            "pending_order_to_filled_position"
        ),
        "final_r": -1.0,
        "gross_r": -1.0,
        "expected_cost_r": 0.104387949348,
        "total_execution_cost_r": 0.10438795,
        "net_proxy_r": -1.1,
        "net_r": -1.1,
        "pnl_cash": -165.0,
        "risk_cash": 150.0,
        "risk_pct": 0.15,
        "risk_decision": "open-reduced-risk",
        "risk_expression_ladder_tier": "reduced",
        "risk_expression_ladder": {
            "ladder_tier": "reduced",
            "risk_decision": "open-reduced-risk",
        },
    }

    exclusion = harness.headline_result_exclusion_reason(trade)
    assert exclusion == f"terminal_r_unscoreable:{terminal_status}"
    annotated_scoreable_trade, annotated_unscoreable_trade = harness.annotate_rows(
        [scoreable_trade, trade],
        profile=harness.PROFILE_REPAIRED,
        split="holdout",
        chunk_id="terminal-lifecycle-test",
        row_type="simulated_trade",
    )
    assert annotated_scoreable_trade["result_scope"] == (
        "diagnostic_terminal_result_not_headline_authority"
    )
    assert annotated_scoreable_trade["package_execution_result_scope"] == (
        "repaired_executable_package_replay"
    )
    assert annotated_unscoreable_trade["result_scope"] == (
        "executed_entry_terminal_r_unscoreable"
    )
    assert annotated_unscoreable_trade["package_execution_result_scope"] == (
        "entry_fill_executable_terminal_r_unscoreable"
    )
    assert annotated_scoreable_trade["risk_expression_ladder_tier"] == "reduced"
    assert annotated_unscoreable_trade["risk_expression_ladder_tier"] == "reduced"

    accumulator = harness.SummaryAccumulator()
    accumulator.add_result(
        profile=harness.PROFILE_REPAIRED,
        split="holdout",
        days=("2026-05-13",),
        result={
            "ledgers": {
                "asof": [],
                "scorecard": [],
                "candidate": [],
                "order": [],
                "event": [],
                "oracle": [],
                "missed": [],
                "trade": [scoreable_trade, trade],
            }
        },
    )
    stat = accumulator.serializable_stats()[0]
    assert stat["trade_rows"] == 2
    assert stat["physical_scoreable_trade_rows"] == 1
    assert stat["physical_unscoreable_trade_rows"] == 1
    assert stat["entry_fill_executable_terminal_r_unscoreable_trade_rows"] == 1
    assert stat["physical_win_count"] == 0
    assert stat["physical_loss_count"] == 1
    assert stat["physical_flat_count"] == 0
    assert stat["physical_gross_r"] == -1.0
    assert stat["physical_final_r"] == -1.0
    assert stat["physical_expected_cost_r"] == 0.20594594
    assert stat["physical_total_execution_cost_r"] == 0.20594595
    assert stat["physical_scoreable_expected_cost_r"] == 0.10438795
    assert stat["physical_unscoreable_expected_cost_r"] == 0.101558
    assert stat["physical_scoreable_total_execution_cost_r"] == 0.10438795
    assert stat["physical_unscoreable_total_execution_cost_r"] == 0.101558
    assert stat["physical_net_r"] == -1.1
    assert stat["physical_cash_pnl"] == -165.0
    assert stat["physical_risk_cash"] == 250.0
    assert stat["physical_risk_pct"] == 0.25
    assert stat["physical_risk_ladder_tier_counts"] == {"reduced": 2}
    assert stat["physical_full_risk_trade_rows"] == 0
    assert stat["physical_reduced_risk_trade_rows"] == 2
    assert stat["physical_win_rate"] == 0.0
    assert stat["filled_trade_count"] == 0
    assert stat["win_count"] == 0
    assert stat["loss_count"] == 0
    assert stat["flat_count"] == 0
    assert stat["diagnostic_only_trade_rows"] == 2
    assert stat["diagnostic_only_missing_r_rows"] == 1
    assert stat["diagnostic_only_net_r"] == -1.1
    assert stat["stress"]["trade_count"] == 0
    assert stat["monte_carlo"]["trade_count"] == 0
    assert stat["physical_stress"]["trade_count"] == 1
    assert stat["physical_monte_carlo"]["trade_count"] == 1

    metric = flow.Metric()
    metric.add_trade({**trade, "headline_result_eligible": False})
    payload = metric.as_dict()
    assert payload["all_trade_rows"] == 1
    assert payload["all_trade_scoreable_rows"] == 0
    assert payload["all_trade_missing_r_rows"] == 1
    assert payload["entry_fill_executable_rows"] == 1
    assert payload["terminal_r_unscoreable_rows"] == 1
    assert payload["all_trade_win_count"] == 0
    assert payload["all_trade_loss_count"] == 0
    assert payload["all_trade_flat_count"] == 0
    assert payload["diagnostic_only_trade_rows"] == 1
    assert payload["diagnostic_only_missing_r_rows"] == 1


def test_completed_run_physical_summary_reconciles_from_serialized_trade_truth(
    tmp_path: Path,
) -> None:
    harness = load_broad_replay_harness()
    trade_path = tmp_path / "TRADE_LEDGER.jsonl"
    rows = harness.annotate_rows(
        [
            {
                "candidate_id": "signed-full",
                "trading_day": "2026-04-10",
                "risk_expression_ladder_tier": "full",
                "risk_expression_ladder": {"ladder_tier": "full"},
                "risk_decision": "trade",
                "final_r": 1.0,
                "gross_r": 1.0,
                "net_proxy_r": 0.9,
                "expected_cost_r": 0.1,
                "total_execution_cost_r": 0.1,
                "pnl_cash": 90.0,
                "risk_cash": 100.0,
                "risk_pct": 0.5,
            },
            {
                "candidate_id": "terminal-unscoreable",
                "trading_day": "2026-04-10",
                "risk_expression_ladder_tier": "reduced",
                "risk_expression_ladder": {"ladder_tier": "reduced"},
                "risk_decision": "open-reduced-risk",
                "entry_fill_executable": True,
                "terminal_r_scoreable": False,
                "final_r": None,
                "gross_r": None,
                "net_proxy_r": None,
                "expected_cost_r": 0.2,
                "total_execution_cost_r": 0.2,
                "pnl_cash": None,
                "risk_cash": 50.0,
                "risk_pct": 0.1,
            },
        ],
        profile=harness.PROFILE_REPAIRED,
        split="holdout",
        chunk_id="reconcile:holdout:2026-04-10:2026-04-10",
        row_type="simulated_trade",
    )
    trade_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    stale = [
        {
            "profile": harness.PROFILE_REPAIRED,
            "split": "holdout",
            "trade_rows": 2,
            "physical_risk_ladder_tier_counts": {"reduced": 2},
        }
    ]

    reconciled = harness.reconcile_physical_summary_stats_from_trade_ledger(
        stale, trade_path
    )[0]

    assert reconciled["physical_risk_ladder_tier_counts"] == {"reduced": 2}
    assert reconciled["physical_scoreable_trade_rows"] == 1
    assert reconciled["physical_unscoreable_trade_rows"] == 1
    assert reconciled["physical_scoreable_expected_cost_r"] == 0.1
    assert reconciled["physical_unscoreable_expected_cost_r"] == 0.2
    assert reconciled["physical_expected_cost_r"] == 0.3
    assert reconciled["physical_net_r"] == 0.9

def test_flow_diagnostic_missed_metrics_preserve_authority_boundary() -> None:
    flow = load_broad_replay_flow_analyzer()

    metric = flow.Metric()
    metric.add_missed(
        {
            "net_proxy_r": 1.25,
            "opportunity_net_proxy_r": 9.0,
            "missed_opportunity_r_scoreability_status": "headline_r_scoreable",
            "missed_opportunity_headline_r_scoreable": True,
            "missed_opportunity_accounting_scope": "execution_bound_headline",
        }
    )
    metric.add_missed(
        {
            "net_proxy_r": None,
            "opportunity_net_proxy_r": -0.75,
            "missed_opportunity_r_scoreability_status": (
                "diagnostic_opportunity_r_scoreable"
            ),
            "missed_opportunity_non_executable_diagnostic_scoreable": True,
            "missed_opportunity_accounting_scope": "non_executable_cost_diagnostic",
        }
    )
    metric.add_missed(
        {
            "net_proxy_r": None,
            "opportunity_net_proxy_r": 12.0,
            "missed_opportunity_r_scoreability_status": (
                "path_auditable_r_unscoreable"
            ),
            "missed_opportunity_accounting_scope": (
                "non_executable_cost_passed_without_execution_bound_diagnostic"
            ),
        }
    )

    payload = metric.as_dict()
    assert payload["rows"] == 3
    assert payload["missed_scoreable_count"] == 2
    assert payload["missed_unscoreable_count"] == 1
    assert payload["missed_net_r"] == 0.5
    assert payload["missed_positive_net_r"] == 1.25
    assert payload["missed_negative_net_r"] == -0.75
    assert payload["missed_flat_count"] == 0
    assert payload["missed_executable_scoreable_count"] == 1
    assert payload["missed_executable_net_r"] == 1.25
    assert payload["missed_executable_positive_count"] == 1
    assert payload["missed_executable_negative_count"] == 0
    assert payload["missed_diagnostic_scoreable_count"] == 1
    assert payload["missed_diagnostic_net_r"] == -0.75
    assert payload["missed_diagnostic_positive_count"] == 0
    assert payload["missed_diagnostic_negative_count"] == 1
    assert payload["counters"]["missed_opportunity_r_scoreability_status"] == {
        "headline_r_scoreable": 1,
        "diagnostic_opportunity_r_scoreable": 1,
        "path_auditable_r_unscoreable": 1,
    }


def test_comparator_uses_flow_authority_for_physical_and_missed_metrics(
    tmp_path: Path,
) -> None:
    comparator = load_broad_replay_comparator()
    prefix = "BROAD_UNIT_FLOW_AUTHORITY"
    (tmp_path / f"{prefix}_SUMMARY.json").write_text(
        json.dumps(
            {
                "status": "broad_live_as_if_replay_materialized_broker_live_closed",
                "date_start": "2026-06-01",
                "date_end": "2026-06-01",
                "candidate_rows": 10,
                "scorecard_rows": 2,
                "trade_rows": 2,
                "missed_opportunity_rows": 8,
                "split_profile_stats": [
                    {
                        "profile": "repaired_package_conversion_v3",
                        "split": "holdout",
                        "trade_rows": 2,
                        "filled_trade_count": 1,
                        "headline_trade_rows": 1,
                        "headline_win_count": 1,
                        "headline_loss_count": 0,
                        "headline_flat_count": 0,
                        "headline_net_r": 1.0,
                        "headline_gross_r": 1.1,
                        "headline_final_r": 1.1,
                        "net_r": 1.0,
                        "gross_r": 1.1,
                        "final_r": 1.1,
                        "cash_pnl": 100.0,
                        "risk_cash": 100.0,
                        "risk_pct": 0.1,
                        "diagnostic_only_trade_rows": 1,
                        "diagnostic_only_net_r": -0.25,
                        "missed_opportunity_rows": 8,
                        "missed_counterfactual_scoreable_rows": 3,
                        "missed_executable_counterfactual_scoreable_rows": 0,
                        "missed_diagnostic_counterfactual_scoreable_rows": 3,
                        "missed_diagnostic_opportunity_net_r": -0.5,
                    }
                ],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    key = "profile_split|repaired_package_conversion_v3|holdout|all"
    (tmp_path / f"{prefix}_FLOW_DIAGNOSTIC_SUMMARY.json").write_text(
        json.dumps(
            {
                "trade_overall": {
                    key: {
                        "profile": "repaired_package_conversion_v3",
                        "split_or_segment": "holdout",
                        "all_trade_rows": 2,
                        "all_trade_win_count": 1,
                        "all_trade_loss_count": 1,
                        "all_trade_flat_count": 0,
                        "all_trade_net_r": 0.75,
                        "all_trade_gross_r": 0.85,
                        "all_trade_final_r": 0.85,
                        "all_trade_cash_pnl": 75.0,
                        "all_trade_risk_cash": 200.0,
                        "all_trade_risk_pct": 0.2,
                        "diagnostic_only_trade_rows": 1,
                        "diagnostic_only_win_count": 0,
                        "diagnostic_only_loss_count": 1,
                        "diagnostic_only_flat_count": 0,
                        "diagnostic_only_net_r": -0.25,
                        "cash_pnl": 100.0,
                    }
                },
                "missed_opportunity_overall": {
                    key: {
                        "profile": "repaired_package_conversion_v3",
                        "split_or_segment": "holdout",
                        "missed_scoreable_count": 3,
                        "missed_unscoreable_count": 5,
                        "missed_net_r": -0.5,
                        "missed_positive_net_r": 1.0,
                        "missed_negative_net_r": -1.5,
                        "missed_executable_scoreable_count": 0,
                        "missed_executable_net_r": 0.0,
                        "missed_executable_positive_count": 0,
                        "missed_executable_negative_count": 0,
                        "missed_diagnostic_scoreable_count": 3,
                        "missed_diagnostic_net_r": -0.5,
                        "missed_diagnostic_positive_count": 1,
                        "missed_diagnostic_positive_net_r": 1.0,
                        "missed_diagnostic_negative_count": 2,
                        "missed_diagnostic_negative_net_r": -1.5,
                    }
                },
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    metrics = comparator.run_metrics(prefix, root=tmp_path)

    assert metrics["headline_trades"] == 1
    assert metrics["headline_net_r"] == 1.0
    assert metrics["physical_trades"] == 2
    assert metrics["physical_net_r"] == 0.75
    assert metrics["physical_wins"] == 1
    assert metrics["physical_losses"] == 1
    assert metrics["diagnostic_trades"] == 1
    assert metrics["diagnostic_net_r"] == -0.25
    assert metrics["missed_scoreable"] == 3
    assert metrics["missed_unscoreable"] == 5
    assert metrics["missed_total_scoreable_net_r"] == -0.5
    assert metrics["missed_executable_scoreable"] == 0
    assert metrics["missed_diagnostic_scoreable"] == 3
    assert metrics["missed_diagnostic_positive_rows"] == 1
    assert metrics["missed_diagnostic_negative_rows"] == 2


def test_strict_full_package_counts_package_authorized_reduced_actions() -> None:
    harness = load_broad_replay_harness()

    generic_terminal_reason = (
        "terminal_result_not_headline_authority:"
        "m1_proxy_replay_not_headline_authority_ordered_tick_required"
    )
    assert harness.headline_result_exclusion_reason(
        {
            "headline_result_authority": False,
            "headline_result_authority_status": (
                "m1_proxy_replay_not_headline_authority_ordered_tick_required"
            ),
            "m1_proxy_replay_authority": True,
        }
    ) == generic_terminal_reason
    assert harness.strict_full_package_parity_result_exclusion_reason(
        {
            "headline_result_authority": False,
            "headline_result_authority_status": (
                "m1_proxy_replay_not_headline_authority_ordered_tick_required"
            ),
            "m1_proxy_replay_authority": True,
        }
    ) == generic_terminal_reason

    assert harness.headline_result_exclusion_reason(
        {
            "profit_harvest_mfe_capture_replay_exit_final_r_authority_status": (
                "m1_ordered_path_proxy_final_r_authority_not_live"
            )
        }
    ) == "profit_harvest_m1_proxy_final_r_diagnostic_not_headline_authority"
    assert harness.strict_full_package_parity_result_exclusion_reason(
        {
            "profit_harvest_mfe_capture_replay_exit_final_r_authority_status": (
                "m1_ordered_path_proxy_final_r_authority_not_live"
            )
        }
    ) == "profit_harvest_m1_proxy_final_r_diagnostic_not_headline_authority"
    assert harness.profit_harvest_m1_proxy_replay_scope(
        {
            "profit_harvest_mfe_capture_replay_exit_final_r_authority_status": (
                "m1_ordered_path_proxy_final_r_authority_not_live"
            )
        }
    ) == "m1_proxy_diagnostic_overlay_not_terminal_r_authority"
    assert harness.headline_result_exclusion_reason(
        {
            "profit_harvest_mfe_capture_replay_exit_final_r_authority_status": (
                "m1_ordered_path_proxy_final_r_diagnostic_not_authority"
            )
        }
    ) == "profit_harvest_m1_proxy_final_r_diagnostic_not_headline_authority"
    assert harness.strict_full_package_parity_result_exclusion_reason(
        {
            "profit_harvest_mfe_capture_replay_exit_final_r_authority_status": (
                "m1_ordered_path_proxy_final_r_diagnostic_not_authority"
            )
        }
    ) == "profit_harvest_m1_proxy_final_r_diagnostic_not_headline_authority"
    assert harness.profit_harvest_m1_proxy_replay_scope(
        {
            "profit_harvest_mfe_capture_replay_exit_final_r_authority_status": (
                "m1_ordered_path_proxy_final_r_diagnostic_not_authority"
            )
        }
    ) == "m1_proxy_diagnostic_overlay_not_terminal_r_authority"
    assert harness.headline_result_exclusion_reason(
        {
            "final_r": 2.0,
            "close_reason": "target_reached_before_stop",
            "profit_harvest_mfe_capture_replay_exit_diagnostic_only": True,
            "profit_harvest_mfe_capture_replay_bound": False,
            "profit_harvest_mfe_capture_replay_exit_final_r_authority_status": (
                "m1_ordered_path_proxy_final_r_diagnostic_not_authority"
            ),
        }
    ) is None
    assert harness.strict_full_package_parity_result_exclusion_reason(
        {
            "final_r": 2.0,
            "close_reason": "target_reached_before_stop",
            "profit_harvest_mfe_capture_replay_exit_diagnostic_only": True,
            "profit_harvest_mfe_capture_replay_bound": False,
            "profit_harvest_mfe_capture_replay_exit_final_r_authority_status": (
                "m1_ordered_path_proxy_final_r_diagnostic_not_authority"
            ),
        }
    ) is None

    assert harness.strict_full_package_parity_result_exclusion_reason(
        {
            "selector_action": "reduce-risk",
            "package_open_reduced_authority_allowed": True,
            "ultimate_candidate_package_open_reduced_risk_authority": {
                "allowed": True,
                "authority_family": "fill_floor_softening",
                "current_config_allowed": True,
            },
        }
    ) == "selector_reduced_replay_repair_only_not_strict_full_package_parity"

    assert harness.strict_full_package_parity_result_exclusion_reason(
        {
            "selector_action": "reduce-risk",
            "package_open_reduced_authority_allowed": True,
            "strict_full_package_reduced_action_authority_allowed": True,
            "ultimate_candidate_package_open_reduced_risk_authority": {
                "allowed": True,
                "authority_family": "fill_floor_softening",
                "current_config_allowed": True,
            },
        }
    ) is None

    assert harness.strict_full_package_parity_result_exclusion_reason(
        {
            "selector_action": "reduce-risk",
            "package_open_reduced_authority_allowed": True,
            "package_open_reduced_authority_family": "router_refusal_softening",
            "package_new_entry_authority_valid": True,
            "package_new_entry_authority_status": (
                "signed_reduced_package_new_entry_authority_valid"
            ),
            "package_new_entry_authority_hash_sha256": "wrong-surface",
            "package_new_entry_authority_source_boundary": (
                "predecision_package_reduce_risk_new_order_authority_no_outcome_fields"
            ),
            "package_new_entry_authority_uses_outcome_fields": False,
            "package_new_entry_authority_candidate_decision_quality_alias_status": (
                "materialized"
            ),
            "ultimate_candidate_package_open_reduced_risk_authority": {
                "allowed": True,
                "current_config_allowed": True,
                "authority_family": "router_refusal_softening",
            },
        }
    ) == "selector_reduced_replay_repair_only_not_strict_full_package_parity"

    signed_reduce_risk_authority = {
        "selector_action": "reduce-risk",
        "package_reduce_risk_authority_allowed": True,
        "ultimate_package_reduce_risk_authority_allowed": True,
        "package_reduce_risk_authority_family": "broker_net_admission_gradient",
        "package_new_entry_authority_valid": True,
        "package_new_entry_authority_status": (
            "signed_reduced_package_new_entry_authority_valid"
        ),
        "package_new_entry_authority_hash_sha256": "reduce123",
        "package_new_entry_authority_source_boundary": (
            "predecision_package_reduce_risk_new_order_authority_no_outcome_fields"
        ),
        "package_new_entry_authority_uses_outcome_fields": False,
        "package_new_entry_authority_candidate_decision_quality_alias_status": (
            "materialized"
        ),
        "ultimate_candidate_package_reduce_risk_authority": {
            "allowed": True,
            "current_config_allowed": True,
            "authority_family": "broker_net_admission_gradient",
            "source_boundary": (
                "predecision_package_reduce_risk_new_order_authority_no_outcome_fields"
            ),
        },
    }
    assert harness.strict_full_package_reduced_action_authority_allowed(
        signed_reduce_risk_authority
    ) is True
    assert harness.strict_full_package_parity_result_exclusion_reason(
        signed_reduce_risk_authority
    ) is None

    signed_predecision_authority = {
        "selector_action": "open-reduced-risk",
        "package_open_reduced_authority_allowed": True,
        "package_open_reduced_authority_family": "router_refusal_softening",
        "package_new_entry_authority_valid": True,
        "package_new_entry_authority_status": (
            "signed_reduced_package_new_entry_authority_valid"
        ),
        "package_new_entry_authority_hash_sha256": "abc123",
        "package_new_entry_authority_source_boundary": (
            "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
        ),
        "package_new_entry_authority_uses_outcome_fields": False,
        "package_new_entry_authority_candidate_decision_quality_alias_status": (
            "materialized"
        ),
        "ultimate_candidate_package_open_reduced_risk_authority": {
            "allowed": True,
            "current_config_allowed": True,
            "authority_family": "router_refusal_softening",
        },
    }
    assert harness.strict_full_package_reduced_action_authority_allowed(
        signed_predecision_authority
    ) is True
    assert harness.strict_full_package_parity_result_exclusion_reason(
        signed_predecision_authority
    ) is None

    assert harness.strict_full_package_parity_result_exclusion_reason(
        {"selector_action": "reduce-risk"}
    ) == "selector_reduced_replay_repair_only_not_strict_full_package_parity"

    assert harness.strict_full_package_parity_result_exclusion_reason(
        {
            "selector_action": "reduce-risk",
            "ultimate_candidate_package_open_reduced_risk_authority": {
                "applies": True,
                "allowed": False,
                "authority_family": "router_refusal_softening",
            },
        }
    ) == "selector_reduced_replay_repair_only_not_strict_full_package_parity"


def test_broad_summary_counts_selector_reasons_and_source_required_fields() -> None:
    harness = load_broad_replay_harness()
    accumulator = harness.SummaryAccumulator()

    accumulator.add_result(
        profile=harness.PROFILE_RAW,
        split="development",
        days=("2026-05-13",),
        result={
            "ledgers": {
                "asof": [],
                "scorecard": [],
                "candidate": [
                    {
                        "candidate_id": "source-required-candidate",
                        "selector_action": "source-required",
                        "selector_reason": "market_state_source_required",
                        "source_required_fields": ["market_state", "cost"],
                    },
                    {
                        "candidate_id": "source-required-candidate-2",
                        "selector_action": "source-required",
                        "selector_decision_reason": "lifecycle_source_required",
                        "source_required_fields": "lifecycle,source_completeness",
                    },
                    {
                        "candidate_id": "trade-candidate",
                        "selector_action": "trade",
                        "selector_reason": "broker_net_probability_passed",
                    },
                ],
                "order": [],
                "event": [],
                "oracle": [],
                "missed": [],
                "trade": [],
            }
        },
    )

    stat = accumulator.serializable_stats()[0]

    assert stat["selector_action_counts"] == {"source-required": 2, "trade": 1}
    assert stat["selector_reason_counts"] == {
        "broker_net_probability_passed": 1,
        "lifecycle_source_required": 1,
        "market_state_source_required": 1,
    }
    assert stat["selector_source_required_reason_counts"] == {
        "lifecycle_source_required": 1,
        "market_state_source_required": 1,
    }
    assert stat["selector_source_required_field_counts"] == {
        "cost": 1,
        "lifecycle": 1,
        "market_state": 1,
        "source_completeness": 1,
    }


def test_broad_summary_splits_executable_and_diagnostic_missed_opportunity() -> None:
    harness = load_broad_replay_harness()
    accumulator = harness.SummaryAccumulator()

    accumulator.add_result(
        profile=harness.PROFILE_RAW,
        split="development",
        days=("2026-05-13",),
        result={
            "ledgers": {
                "asof": [],
                "scorecard": [],
                "candidate": [],
                "order": [],
                "event": [],
                "oracle": [],
                "trade": [],
                "missed": [
                    {
                        "candidate_id": "cost-passed-missed",
                        "order_status": "not_sent_missed_opportunity",
                        "executable_finalized": False,
                        "missed_row_executable_finalized": False,
                        "missed_opportunity_accounting_scope": (
                            "non_executable_cost_passed_without_execution_bound_diagnostic"
                        ),
                        "missed_cost_executable_headline_eligible": False,
                        "missed_cost_executable_opportunity_scoreable": False,
                        "missed_cost_broker_authority_passed": True,
                        "missed_opportunity_execution_bound_cost_passed": False,
                        "missed_opportunity_headline_execution_bound_eligible": False,
                        "missed_opportunity_headline_r_scoreable": False,
                        "missed_opportunity_counterfactual_scoreable": True,
                        "missed_opportunity_r_scoreability_status": (
                            "diagnostic_opportunity_r_scoreable"
                        ),
                        "missed_cost_disposition": "cost_authority_not_primary_miss_reason",
                        "missed_non_executable_diagnostic_reason": (
                            "cost_passed_broker_authority_without_execution_bound_order_path"
                        ),
                        "net_proxy_r": None,
                        "opportunity_net_proxy_r": 1.5,
                    },
                    {
                        "candidate_id": "refused-cost-diagnostic",
                        "missed_opportunity_accounting_scope": (
                            "non_executable_cost_diagnostic"
                        ),
                        "pretrade_cost_packet_status": "REFUSED",
                        "pretrade_cost_refusal_reasons": [
                            "spread_r_exceeds_selected_cell_limit"
                        ],
                        "package_replay_source_bound_candidate_use_allowed": True,
                        "package_replay_candidate_use_allowed": False,
                        "package_replay_executable_candidate_use_allowed": False,
                        "package_replay_executable_candidate_use_allowed_reason": (
                            "broker_cost_packet_refused:"
                            "spread_r_exceeds_selected_cell_limit"
                        ),
                        "missed_cost_executable_headline_eligible": False,
                        "missed_cost_disposition": (
                            "non_scoreable_cost_refused_non_executable_diagnostic"
                        ),
                        "missed_non_executable_diagnostic_reason": (
                            "non_scoreable_cost_refused_non_executable_diagnostic"
                        ),
                        "missed_opportunity_counterfactual_scoreable": True,
                        "missed_opportunity_r_scoreability_status": (
                            "diagnostic_opportunity_r_scoreable"
                        ),
                        "net_proxy_r": None,
                        "opportunity_net_proxy_r": 8.0,
                    },
                ],
            }
        },
    )

    stat = accumulator.serializable_stats()[0]

    assert stat["missed_opportunity_rows"] == 2
    assert stat["missed_total_scoreable_net_r"] == 0.0
    assert stat["missed_positive_net_r"] == 0.0
    assert stat["missed_counterfactual_scoreable_rows"] == 2
    assert stat["missed_counterfactual_positive_rows"] == 0
    assert stat["missed_diagnostic_counterfactual_positive_rows"] == 2
    assert stat["missed_diagnostic_counterfactual_negative_rows"] == 0
    assert stat["missed_diagnostic_counterfactual_flat_rows"] == 0
    assert stat["missed_diagnostic_positive_net_r"] == 9.5
    assert stat["missed_diagnostic_negative_net_r"] == 0.0
    assert stat["missed_headline_scoreable_rows"] == 0
    assert stat["missed_headline_total_net_r"] == 0.0
    assert stat["headline_net_r"] == 0.0
    assert stat["missed_executable_cost_passed_rows"] == 0
    assert stat["missed_executable_cost_passed_total_net_r"] == 0.0
    assert stat["missed_opportunity_diagnostic_rows"] == 2
    assert stat["missed_opportunity_diagnostic_total_net_r"] == 9.5
    assert stat["missed_non_executable_diagnostic_rows"] == 2
    assert stat["missed_non_executable_diagnostic_total_net_r"] == 9.5
    assert stat["missed_opportunity_accounting_scope_counts"] == {
        "non_executable_cost_passed_without_execution_bound_diagnostic": 1,
        "non_executable_cost_diagnostic": 1,
    }
    assert stat["missed_cost_disposition_counts"] == {
        "cost_authority_not_primary_miss_reason": 1,
        "non_scoreable_cost_refused_non_executable_diagnostic": 1,
    }
    assert stat["missed_non_executable_diagnostic_reason_counts"] == {
        "cost_passed_broker_authority_without_execution_bound_order_path": 1,
        "non_scoreable_cost_refused_non_executable_diagnostic": 1,
    }


def test_broad_summary_counts_selected_contract_unmet_without_promoting_missed_r() -> None:
    harness = load_broad_replay_harness()
    accumulator = harness.SummaryAccumulator()

    accumulator.add_result(
        profile=harness.PROFILE_REPAIRED,
        split="holdout",
        days=("2026-05-13",),
        result={
            "ledgers": {
                "asof": [],
                "scorecard": [],
                "candidate": [],
                "order": [
                    {
                        "simulated_order_id": "order-contract-unmet",
                        "candidate_id": "candidate-contract-unmet",
                        "decision_time_utc": "2026-05-13T15:30:00+00:00",
                        "canonical_replay_candidate_instance_key": (
                            "candidate-contract-unmet@@2026-05-13T15:30:00+00:00"
                        ),
                        "order_status": "guarded_market_fallback_contract_unmet",
                        "fill_status": (
                            "not_sent_marketable_limit_structure_preservation_contract_unmet"
                        ),
                        "package_marketable_guarded_fallback_contract_unmet": True,
                        "package_marketable_guarded_fallback_contract_unmet_reason": (
                            "marketable_limit_structure_preservation_contract_unmet"
                        ),
                        "expected_net_r": 1.25,
                        "risk_decision": "open-reduced-risk",
                    }
                ],
                "event": [],
                "oracle": [],
                "missed": [],
                "trade": [],
            }
        },
    )

    stat = accumulator.serializable_stats()[0]

    assert stat["terminal_order_rows"] == 1
    assert stat["order_rows"] == 1
    assert stat["filled_trade_count"] == 0
    assert stat["order_status_counts"] == {
        "guarded_market_fallback_contract_unmet": 1
    }
    assert stat["guarded_market_fallback_contract_unmet_count"] == 1
    assert stat["selected_contract_unmet_rows"] == 1
    assert stat["selected_contract_unmet_expected_net_r"] == 1.25
    assert stat["selected_contract_unmet_reason_counts"] == {
        "marketable_limit_structure_preservation_contract_unmet": 1
    }
    assert stat["selected_contract_unmet_instance_keys"] == [
        "candidate-contract-unmet@@2026-05-13T15:30:00+00:00"
    ]
    assert stat["missed_executable_cost_passed_rows"] == 0
    assert stat["missed_executable_cost_passed_total_net_r"] == 0.0


def test_selected_package_bridge_allows_unique_stable_window_member_axis_alias() -> None:
    bridge = load_selected_package_replay_bridge()
    candidate = {
        "candidate_id": "broadorigin_alias",
        "symbol": "XAUUSD",
        "side": "LONG",
        "decision_time_utc": "2026-05-05T07:15:00+00:00",
        "framework": "fw",
        "origin_family": "origin",
        "session_bucket": "london",
        "source_bound_package_candidate_use_allowed": True,
        "expected_net_r": 0.8,
        "probability": 0.8,
        "fill_probability": 0.8,
        **_execution_fillability_fields(0.8),
        "source_completeness": 1.0,
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "scheduler_materialization_action_intent": "new_position",
        "entry_price": 3300.0,
        "stop_loss": 3290.0,
        "take_profit_1": 3320.0,
        "risk_reward_ratio": 2.0,
    }
    member = {
        "source_axis_row_index": 42,
        "sleeve_id": "sleeve",
        "framework": "fw",
        "origin_family": "origin",
        "symbol": "XAUUSD",
        "side": "LONG",
        "session_bucket": "london",
        "sleeve_type": "scheduler_lifecycle_core",
    }
    label = {
        "label_id": "label:1",
        "candidate_id": "XAUUSD_2026-05-05T07:15:00+00:00",
        "symbol": "XAUUSD",
        "side": "LONG",
        "decision_time_utc": "2026-05-05T07:15:00+00:00",
    }

    bridge_rows, label_rows, summary = bridge.build_denominator_bridge(
        candidates=[candidate],
        members=[member],
        labels=[label],
        decision_time_source="lifecycle-labels",
    )

    assert summary["exact_denominator_join_rows"] == 0
    assert summary["selected_package_denominator_use_allowed_rows"] == 1
    assert label_rows[0]["canonical_candidate_alias_status"] == (
        "stable_window_member_axis_unique_alias"
    )
    assert label_rows[0]["selected_package_denominator_use_allowed"] is True
    assert bridge_rows[0]["selected_package_denominator_use_allowed"] is True
    assert bridge_rows[0]["selected_package_member_axis_authority_bound"] is True
    assert bridge_rows[0]["source_bound_package_candidate_use_allowed"] is True
    assert bridge_rows[0]["scheduler_materialization_action_intent"] == "new_position"
    assert label_rows[0]["scheduler_materialization_action_intent"] == "new_position"
    expected_instance_key = f"{candidate['candidate_id']}@@{candidate['decision_time_utc']}"
    expected_bridge_join_key = (
        f"{candidate['candidate_id']}@@"
        f"{bridge.decision_window_id('XAUUSD', 'LONG', candidate['decision_time_utc'])}"
    )
    assert bridge_rows[0]["candidate_id"] == candidate["candidate_id"]
    assert bridge_rows[0]["replay_candidate_id"] == candidate["candidate_id"]
    assert bridge_rows[0]["canonical_replay_candidate_instance_key"] == expected_instance_key
    assert bridge_rows[0]["selected_package_bridge_join_status"] == (
        "exact_candidate_window_join"
    )
    assert bridge_rows[0]["selected_package_bridge_join_key"] == expected_bridge_join_key
    assert label_rows[0]["candidate_id"] == candidate["candidate_id"]
    assert label_rows[0]["replay_candidate_id"] == candidate["candidate_id"]
    assert label_rows[0]["canonical_replay_candidate_instance_key"] == expected_instance_key
    assert label_rows[0]["selected_package_bridge_join_status"] == (
        "exact_candidate_window_join"
    )
    assert label_rows[0]["selected_package_bridge_join_key"] == expected_bridge_join_key


def test_selected_package_bridge_allows_unique_executable_package_axis_alias_in_collided_window() -> None:
    bridge = load_selected_package_replay_bridge()
    base_candidate = {
        "symbol": "XAUUSD",
        "side": "SHORT",
        "decision_time_utc": "2026-05-05T08:15:00+00:00",
        "framework": "fw",
        "origin_family": "origin",
        "session_bucket": "london",
        "source_bound_package_candidate_use_allowed": True,
        "expected_net_r": 0.9,
        "probability": 0.82,
        "fill_probability": 0.78,
        **_execution_fillability_fields(0.78),
        "source_completeness": 1.0,
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "scheduler_materialization_action_intent": "new_position",
        "entry_price": 3300.0,
        "stop_loss": 3310.0,
        "take_profit_1": 3280.0,
        "risk_reward_ratio": 2.0,
    }
    executable = {
        **base_candidate,
        "candidate_id": "broadorigin_axis_executable",
        "pretrade_cost_packet_status": "PASSED",
    }
    refused = {
        **base_candidate,
        "candidate_id": "broadorigin_axis_refused",
        "pretrade_cost_packet_status": "REFUSED",
        "pretrade_cost_refusal_reasons": ["spread_r_exceeds_selected_cell_limit"],
    }
    member = {
        "source_axis_row_index": 42,
        "stable_member_axis_id": "member_axis:axis-collided",
        "sleeve_id": "sleeve",
        "framework": "fw",
        "origin_family": "origin",
        "symbol": "XAUUSD",
        "side": "SHORT",
        "session_bucket": "london",
        "sleeve_type": "scheduler_lifecycle_core",
    }
    labels = [
        {
            "label_id": "label:1",
            "candidate_id": "XAUUSD_2026-05-05T08:15:00+00:00:a",
            "symbol": "XAUUSD",
            "side": "SHORT",
            "decision_time_utc": "2026-05-05T08:15:00+00:00",
        },
        {
            "label_id": "label:2",
            "candidate_id": "XAUUSD_2026-05-05T08:15:00+00:00:b",
            "symbol": "XAUUSD",
            "side": "SHORT",
            "decision_time_utc": "2026-05-05T08:15:00+00:00",
        },
    ]

    bridge_rows, label_rows, summary = bridge.build_denominator_bridge(
        candidates=[executable, refused],
        members=[member],
        labels=labels,
        decision_time_source="lifecycle-labels",
    )

    allowed_rows = [
        row for row in label_rows if row["selected_package_denominator_use_allowed"]
    ]
    refused_rows = [
        row for row in label_rows if row["replay_candidate_id"] == refused["candidate_id"]
    ]

    assert summary["exact_denominator_join_rows"] == 0
    assert summary["stable_window_member_axis_unique_alias_rows"] == 0
    assert summary["package_axis_window_unique_executable_alias_rows"] == 2
    assert summary["selected_package_denominator_use_allowed_rows"] == 1
    assert summary["selected_package_denominator_use_allowed_label_join_rows"] == 2
    assert {row["replay_candidate_id"] for row in allowed_rows} == {
        executable["candidate_id"]
    }
    assert {row["candidate_id"] for row in allowed_rows} == {executable["candidate_id"]}
    assert {
        row["canonical_replay_candidate_instance_key"] for row in allowed_rows
    } == {f"{executable['candidate_id']}@@{executable['decision_time_utc']}"}
    assert {
        row["selected_package_bridge_join_status"] for row in allowed_rows
    } == {"exact_candidate_window_join"}
    assert [
        row["candidate_id"]
        for row in bridge_rows
        if row["selected_package_denominator_use_allowed"]
    ] == [executable["candidate_id"]]
    assert all(
        row["canonical_replay_candidate_instance_key"]
        == f"{row['candidate_id']}@@{row['decision_time_utc']}"
        for row in bridge_rows
    )
    assert all(
        row["canonical_candidate_alias_status"]
        == "package_axis_window_unique_executable_alias"
        for row in allowed_rows
    )
    assert all(
        row["canonical_package_axis_alias_id"] == "member_axis:axis-collided"
        for row in allowed_rows
    )
    assert all(
        row["package_axis_window_replay_candidate_count"] == 2
        and row["package_axis_window_executable_candidate_count"] == 1
        and row["package_axis_window_label_count"] == 2
        for row in allowed_rows
    )
    assert all(not row["selected_package_denominator_use_allowed"] for row in refused_rows)
    assert [
        row["selected_package_denominator_use_allowed"]
        for row in bridge_rows
        if row["replay_candidate_id"] == executable["candidate_id"]
    ] == [True]
    assert [
        row["selected_package_denominator_use_allowed"]
        for row in bridge_rows
        if row["replay_candidate_id"] == refused["candidate_id"]
    ] == [False]


def test_selected_package_bridge_member_axis_match_does_not_create_candidate_authority() -> None:
    bridge = load_selected_package_replay_bridge()
    candidate = {
        "candidate_id": "broadorigin_diagnostic_only",
        "symbol": "XAUUSD",
        "side": "LONG",
        "decision_time_utc": "2026-05-05T07:15:00+00:00",
        "framework": "fw",
        "origin_family": "origin",
        "session_bucket": "london",
        "source_bound_package_candidate_use_allowed": False,
        "ultimate_package_source_bound_candidate_use_allowed": False,
        "package_replay_source_bound_candidate_use_allowed": False,
        "package_replay_executable_candidate_use_allowed": False,
        "package_replay_executable_candidate_use_allowed_reason": (
            "candidate_canonical_not_source_bound"
        ),
        "expected_net_r": 0.8,
        "probability": 0.8,
        "fill_probability": 0.8,
        "source_completeness": 1.0,
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "scheduler_materialization_action_intent": "new_position",
        "entry_price": 3300.0,
        "stop_loss": 3290.0,
        "take_profit_1": 3320.0,
        "risk_reward_ratio": 2.0,
    }
    member = {
        "source_axis_row_index": 43,
        "sleeve_id": "sleeve",
        "framework": "fw",
        "origin_family": "origin",
        "symbol": "XAUUSD",
        "side": "LONG",
        "session_bucket": "london",
        "sleeve_type": "scheduler_lifecycle_core",
    }
    label = {
        "label_id": "label:diagnostic",
        "candidate_id": "XAUUSD_2026-05-05T07:15:00+00:00",
        "symbol": "XAUUSD",
        "side": "LONG",
        "decision_time_utc": "2026-05-05T07:15:00+00:00",
    }

    bridge_rows, label_rows, summary = bridge.build_denominator_bridge(
        candidates=[candidate],
        members=[member],
        labels=[label],
        decision_time_source="lifecycle-labels",
    )
    compact_rows = bridge.compact_candidate_rows(
        candidates=[candidate],
        bridge_rows=bridge_rows,
    )

    assert summary["selected_package_denominator_use_allowed_rows"] == 0
    assert label_rows[0]["selected_package_denominator_use_allowed"] is False
    assert bridge_rows[0]["selected_package_member_axis_authority_bound"] is True
    assert bridge_rows[0]["selected_package_bridge_source_bound_candidate_use_allowed"] is True
    assert bridge_rows[0]["source_bound_package_candidate_use_allowed"] is False
    assert bridge_rows[0]["package_replay_executable_candidate_use_allowed"] is False
    assert compact_rows[0]["selected_package_bridge_source_bound_candidate_use_allowed"] is True
    assert compact_rows[0]["source_bound_package_candidate_use_allowed"] is False
    assert compact_rows[0]["package_replay_executable_candidate_use_allowed"] is False
    assert compact_rows[0]["package_replay_executable_candidate_use_allowed_reason"] == (
        "candidate_canonical_not_source_bound"
    )


def test_selected_package_bridge_hydration_keeps_effective_member_axis_alias_diagnostic() -> None:
    bridge = load_selected_package_replay_bridge()
    hydrated = bridge.hydrate_candidate_quality_aliases(
        {
            "candidate_id": "member-axis-diagnostic-hydration",
            "decision_time_utc": "2026-05-05T07:15:00+00:00",
            "symbol": "XAUUSD",
            "side": "LONG",
            "source_bound_package_candidate_use_allowed": False,
            "ultimate_package_source_bound_candidate_use_allowed": False,
            "package_replay_source_bound_candidate_use_allowed": False,
            "ultimate_package_effective_source_bound_candidate_use_allowed": True,
            "ultimate_package_matched_member_axis_count": 1,
            "package_replay_executable_candidate_use_allowed": False,
            "package_replay_executable_candidate_use_allowed_reason": (
                "candidate_canonical_not_source_bound"
            ),
            "expected_net_r": 0.8,
            "probability": 0.8,
            "fill_probability": 0.8,
            "source_completeness": 1.0,
            "source_completeness_status": "complete",
            "pretrade_cost_packet_status": "PASSED",
            "cost_authority": "broker_calibrated_replay_cost",
            "cost_source_gap_status": "source_bound_cost_authority_present",
        }
    )

    assert hydrated["source_bound_package_candidate_use_allowed"] is False
    assert hydrated["ultimate_package_source_bound_candidate_use_allowed"] is False
    assert hydrated["package_replay_source_bound_candidate_use_allowed"] is False
    assert hydrated["package_replay_executable_candidate_use_allowed"] is False


def test_selected_package_bridge_member_axis_requires_exact_signed_instance_to_repair_false() -> None:
    bridge = load_selected_package_replay_bridge()
    member_axis_id = "member_axis:exact-signed-repair"
    candidate = _signed_bridge_router_refusal_row(
        "source_bound_router_refusal_open_reduced_materialized_for_replay",
        matched_member_axis_id=member_axis_id,
    )
    candidate.update(
        {
            "symbol": "XAUUSD",
            "side": "LONG",
            "framework": "fw",
            "origin_family": "origin",
            "session_bucket": "london",
            "source_bound_package_candidate_use_allowed": False,
            "ultimate_package_source_bound_candidate_use_allowed": False,
            "package_replay_source_bound_candidate_use_allowed": False,
            "pretrade_cost_packet_status": "PASSED",
            "cost_authority": "broker_calibrated_replay_cost",
            "cost_source_gap_status": "source_bound_cost_authority_present",
            "candidate_cost_r_fallback_is_authority": False,
            "entry_price": 2400.0,
            "stop_loss": 2390.0,
            "take_profit_1": 2420.0,
        }
    )
    signed_fields = bridge.selected_package_bridge_quality_fields(
        candidate,
        matched_stable_member_axis_ids=[member_axis_id],
    )

    assert signed_fields[
        "selected_package_bridge_source_bound_candidate_use_allowed"
    ] is True
    assert signed_fields["source_bound_package_candidate_use_allowed"] is True

    mismatched = dict(candidate)
    mismatched[
        "package_new_entry_authority_source_bound_replay_candidate_instance_key"
    ] = "different-candidate@@2026-05-15T10:15:00+00:00"
    mismatched_fields = bridge.selected_package_bridge_quality_fields(
        mismatched,
        matched_stable_member_axis_ids=[member_axis_id],
    )

    assert mismatched_fields[
        "selected_package_bridge_source_bound_candidate_use_allowed"
    ] is True
    assert mismatched_fields["source_bound_package_candidate_use_allowed"] is False
    assert mismatched_fields["package_replay_executable_candidate_use_allowed"] is False


def test_selected_package_bridge_compact_candidate_fails_closed_on_exact_window_miss() -> None:
    bridge = load_selected_package_replay_bridge()
    bridge_window = bridge.decision_window_id(
        "XAUUSD",
        "LONG",
        "2026-05-05T08:15:00+00:00",
    )

    compact_rows = bridge.compact_candidate_rows(
        candidates=[
            {
                "candidate_id": "candidate:reused",
                "symbol": "XAUUSD",
                "side": "LONG",
                "decision_time_utc": "2026-05-05T08:30:00+00:00",
                "ultimate_package_matched_member_axis_ids": [],
                "source_bound_package_candidate_use_allowed": False,
                "ultimate_package_source_bound_candidate_use_allowed": False,
                "package_replay_candidate_use_allowed": False,
            }
        ],
        bridge_rows=[
            {
                "replay_candidate_id": "candidate:reused",
                "stable_decision_window_id": bridge_window,
                "matched_stable_member_axis_ids": ["member-axis:wrong-window"],
                "selected_package_denominator_use_allowed": True,
            }
        ],
    )

    compact = compact_rows[0]
    assert compact["selected_package_bridge_join_status"] == (
        "selected_package_bridge_exact_missing"
    )
    assert compact["selected_package_bridge_join_key"] is None
    assert compact["matched_stable_member_axis_ids"] == []
    assert compact["selected_package_replay_row"] is False


def test_selected_package_bridge_compact_candidate_fails_closed_without_candidate_window() -> None:
    bridge = load_selected_package_replay_bridge()
    bridge_window = bridge.decision_window_id(
        "XAUUSD",
        "LONG",
        "2026-05-05T08:15:00+00:00",
    )

    compact_rows = bridge.compact_candidate_rows(
        candidates=[
            {
                "candidate_id": "candidate:reused",
                "symbol": "XAUUSD",
                "side": "LONG",
                "ultimate_package_matched_member_axis_ids": [],
                "source_bound_package_candidate_use_allowed": False,
                "ultimate_package_source_bound_candidate_use_allowed": False,
                "package_replay_candidate_use_allowed": False,
            }
        ],
        bridge_rows=[
            {
                "replay_candidate_id": "candidate:reused",
                "stable_decision_window_id": bridge_window,
                "matched_stable_member_axis_ids": ["member-axis:wrong-window"],
                "selected_package_denominator_use_allowed": True,
            }
        ],
    )

    compact = compact_rows[0]
    assert compact["selected_package_bridge_join_status"] == (
        "selected_package_bridge_window_missing"
    )
    assert compact["selected_package_bridge_join_key"] is None
    assert compact["matched_stable_member_axis_ids"] == []
    assert compact["selected_package_denominator_use_allowed"] is False
    assert compact["selected_package_replay_row"] is False


def test_selected_package_bridge_order_trade_rows_join_candidate_status() -> None:
    bridge = load_selected_package_replay_bridge()
    window = "decision_window:unit:candidate_joined"
    status = {
        "candidate_id": "candidate:joined",
        "stable_decision_window_id": window,
        "source_bound_package_candidate_use_allowed": False,
        "ultimate_package_source_bound_candidate_use_allowed": False,
        "package_replay_executable_candidate_use_allowed": False,
        "package_replay_executable_candidate_use_allowed_reason": (
            "broker_cost_packet_refused:spread_r_exceeds_selected_cell_limit"
        ),
        "selected_package_candidate_use_allowed_status": (
            "broker_cost_packet_refused:spread_r_exceeds_selected_cell_limit"
        ),
        "replay_candidate_use_allowed_now": False,
        "replay_candidate_use_allowed_now_reason": (
            "broker_cost_packet_refused:spread_r_exceeds_selected_cell_limit"
        ),
        "candidate_expected_net_r": 1.25,
        "expected_net_r": 1.25,
        "pretrade_cost_packet_status": "REFUSED",
        "pretrade_cost_refusal_reasons": [
            "spread_r_exceeds_selected_cell_limit"
        ],
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "selector_action": "reject",
        "selector_reason": (
            "broker_net_pretrade_cost_packet_refused:"
            "spread_r_exceeds_selected_cell_limit"
        ),
    }

    decorated = bridge.decorate_rows(
        [
            {
                **_package_exec_aliases(),
                "candidate_id": "candidate:joined",
                "stable_decision_window_id": window,
                "candidate_expected_net_r": 1.20,
                "expected_net_r": 1.20,
                "package_replay_executable_candidate_use_allowed": True,
                "package_replay_executable_candidate_use_allowed_reason": (
                    "broker_cost_selector_and_scheduler_action_executable"
                ),
                "replay_candidate_use_allowed_now": True,
                "replay_candidate_use_allowed_now_reason": (
                    "broker_cost_selector_and_scheduler_action_executable"
                ),
                "selected_package_candidate_use_allowed_status": (
                    "broker_cost_selector_and_scheduler_action_executable"
                ),
                "selector_action": "trade",
                "selector_reason": "broker_net_probability_confluence_lifecycle_admission_passed",
                "pretrade_cost_packet_status": "PASSED",
                "pretrade_cost_refusal_reasons": [],
            }
        ],
        row_type="trade",
        candidate_status_by_id=bridge.build_candidate_status_lookup([status]),
    )[0]

    assert decorated["selected_package_candidate_status_joined"] is True
    assert decorated["package_replay_executable_candidate_use_allowed"] is True
    assert decorated["selected_package_status_package_replay_executable_candidate_use_allowed"] is False
    assert "selected_package_non_executable_order_trade_diagnostic" not in decorated
    assert decorated["candidate_expected_net_r"] == 1.25
    assert decorated["expected_net_r"] == 1.25
    assert decorated["trade_reported_candidate_expected_net_r"] == 1.20
    assert decorated["trade_reported_expected_net_r"] == 1.20
    assert decorated["pretrade_cost_packet_status"] == "PASSED"
    assert decorated["selected_package_status_pretrade_cost_packet_status"] == "REFUSED"
    assert decorated["pretrade_cost_refusal_reasons"] == []
    assert decorated["selected_package_status_pretrade_cost_refusal_reasons"] == [
        "spread_r_exceeds_selected_cell_limit"
    ]
    assert decorated["selector_action"] == "trade"
    assert decorated["selected_package_status_selector_action"] == "reject"
    assert decorated["replay_candidate_use_allowed_now"] is True
    assert decorated["selected_package_status_replay_candidate_use_allowed_now"] is False
    assert decorated["selected_package_candidate_use_allowed_status"] == (
        "broker_cost_selector_and_scheduler_action_executable"
    )
    assert decorated["selected_package_status_selected_package_candidate_use_allowed_status"] == (
        "broker_cost_packet_refused:spread_r_exceeds_selected_cell_limit"
    )
    assert (
        decorated["selected_package_candidate_status_join_execution_authority_conflict"]
        is True
    )
    assert {
        conflict["field"]
        for conflict in decorated["selected_package_candidate_status_join_conflicts"]
    } >= {
        "package_replay_executable_candidate_use_allowed",
        "replay_candidate_use_allowed_now",
        "selected_package_candidate_use_allowed_status",
        "pretrade_cost_packet_status",
        "pretrade_cost_refusal_reasons",
        "selector_action",
    }


def test_selected_package_bridge_oracle_rows_preserve_authority_conflicts() -> None:
    bridge = load_selected_package_replay_bridge()
    window = "decision_window:unit:oracle_candidate_joined"
    status = {
        "candidate_id": "candidate:oracle-joined",
        "stable_decision_window_id": window,
        "selector_action": "replace_pending",
        "package_new_entry_authority_selector_action": "replace_pending",
        "package_replay_executable_candidate_use_allowed": False,
        "package_replay_executable_candidate_use_allowed_reason": (
            "candidate_status_non_executable_fixture"
        ),
    }

    decorated = bridge.decorate_rows(
        [
            {
                **_package_exec_aliases(),
                "candidate_id": "candidate:oracle-joined",
                "stable_decision_window_id": window,
                "selector_action": "new_position",
                "package_new_entry_authority_selector_action": "new_position",
                "package_replay_executable_candidate_use_allowed": True,
            }
        ],
        row_type="oracle",
        candidate_status_by_id=bridge.build_candidate_status_lookup([status]),
    )[0]

    assert decorated["selector_action"] == "new_position"
    assert decorated["oracle_reported_selector_action"] == "new_position"
    assert decorated["selected_package_status_selector_action"] == "replace_pending"
    assert (
        decorated["package_new_entry_authority_selector_action"]
        == "new_position"
    )
    assert (
        decorated[
            "selected_package_status_package_new_entry_authority_selector_action"
        ]
        == "replace_pending"
    )
    assert (
        decorated["selected_package_candidate_status_join_execution_authority_conflict"]
        is True
    )


def test_selected_package_bridge_clears_stale_stop_hazard_cap_truth() -> None:
    bridge = load_selected_package_replay_bridge()
    row = {
        "predecision_stop_hazard_guard_status": "pass",
        "predecision_stop_hazard_guard_action": "block",
        "predecision_stop_hazard_guard_risk_cap_pct": 0.10,
        "predecision_stop_hazard_guard_risk_cap_applied": True,
    }

    bridge._normalize_stop_hazard_cap_truth(row)

    assert row["predecision_stop_hazard_guard_risk_cap_applied"] is False


def test_selected_package_bridge_treats_stale_source_bound_status_as_provenance() -> None:
    bridge = load_selected_package_replay_bridge()
    window = "decision_window:unit:candidate_stale_source_status"
    status = {
        "candidate_id": "candidate:stale-source-status",
        "stable_decision_window_id": window,
        "source_bound_package_candidate_use_allowed": True,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "package_replay_source_bound_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed": False,
        "package_replay_executable_candidate_use_allowed_reason": (
            "ultimate_package_effective_source_bound_not_allowed"
        ),
        "replay_candidate_use_allowed_now": False,
        "replay_candidate_use_allowed_now_reason": (
            "ultimate_package_effective_source_bound_not_allowed"
        ),
        "selected_package_candidate_use_allowed_status": (
            "ultimate_package_effective_source_bound_not_allowed"
        ),
        "pretrade_cost_packet_status": "PASSED",
        "cost_source_gap_status": "source_bound_cost_authority_present",
    }

    decorated = bridge.decorate_rows(
        [
            {
                **_package_exec_aliases(),
                "candidate_id": "candidate:stale-source-status",
                "stable_decision_window_id": window,
                "selector_action": "trade",
                "selector_reason": (
                    "broker_net_probability_confluence_lifecycle_admission_passed"
                ),
                "scheduler_materialization_action_intent": "new_position",
                "entry_price": 2400.0,
                "stop_loss": 2395.0,
                "take_profit_1": 2410.0,
            }
        ],
        row_type="trade",
        candidate_status_by_id=bridge.build_candidate_status_lookup([status]),
    )[0]

    assert decorated["selected_package_candidate_status_joined"] is True
    assert decorated["package_replay_executable_candidate_use_allowed"] is True
    assert decorated["replay_candidate_use_allowed_now"] is True
    assert (
        "selected_package_candidate_status_join_execution_authority_conflict"
        not in decorated
    )
    assert "selected_package_non_executable_order_trade_diagnostic" not in decorated
    provenance_fields = {
        item["field"]
        for item in decorated[
            "selected_package_candidate_status_join_provenance_differences"
        ]
    }
    assert {
        "package_replay_executable_candidate_use_allowed",
        "package_replay_executable_candidate_use_allowed_reason",
        "replay_candidate_use_allowed_now",
        "replay_candidate_use_allowed_now_reason",
        "selected_package_candidate_use_allowed_status",
    }.issubset(provenance_fields)


def test_selected_package_bridge_canonical_status_join_preserves_sleeve_admission() -> None:
    bridge = load_selected_package_replay_bridge()
    decision_time = "2026-05-05T04:00:00+00:00"
    candidate = {
        "candidate_id": "candidate:canonical-sleeve",
        "symbol": "XAUUSD",
        "side": "SHORT",
        "decision_time_utc": decision_time,
        "entry_price": 3300.0,
        "stop_loss": 3305.0,
        "take_profit_1": 3290.0,
        "expected_net_r": 1.12,
        "candidate_expected_net_r": 1.12,
        "probability": 0.81,
        "candidate_probability": 0.81,
        "fill_probability": 0.76,
        "candidate_fill_probability": 0.76,
        **_execution_fillability_fields(0.76),
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "candidate_cost_r_fallback_is_authority": False,
        "selector_action": "trade",
        "scheduler_materialization_action_intent": "new_position",
        "package_replay_source_bound_candidate_use_allowed": True,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "ultimate_package_admission_sleeve_match_count": 1,
        "ultimate_package_matched_sleeve_count": 1,
        "ultimate_package_combined_source_bound_signal_r_sum": 44.0,
        "ultimate_package_max_combined_source_bound_signal_r": 44.0,
    }
    stable_window = bridge.decision_window_id("XAUUSD", "SHORT", decision_time)

    fields = bridge.selected_package_bridge_quality_fields(
        candidate,
        matched_stable_member_axis_ids=["member-axis:canonical-sleeve"],
    )

    assert fields["selected_package_bridge_admission_candidate_use_allowed"] is True
    assert fields["ultimate_package_admission_candidate_use_allowed"] is True
    assert fields["ultimate_package_effective_admission_count"] == 1

    compact_rows = bridge.compact_candidate_rows(
        [candidate],
        [
            {
                "replay_candidate_id": "candidate:canonical-sleeve",
                "stable_decision_window_id": stable_window,
                "matched_stable_member_axis_ids": ["member-axis:canonical-sleeve"],
                "selected_package_replay_row": True,
                "selected_package_denominator_use_allowed": True,
            }
        ],
    )
    status = compact_rows[0]
    canonical_key = status["canonical_replay_candidate_instance_key"]
    status_lookup = bridge.build_candidate_status_lookup(compact_rows)

    assert canonical_key == f"candidate:canonical-sleeve@@{decision_time}"
    assert canonical_key in status_lookup

    decorated = bridge.decorate_rows(
        [
            {
                **_package_exec_aliases(),
                "candidate_id": "candidate:canonical-sleeve",
                "symbol": "XAUUSD",
                "side": "SHORT",
                "decision_time_utc": decision_time,
                "stable_decision_window_id": stable_window,
                "selector_action": "trade",
                "scheduler_materialization_action_intent": "new_position",
            }
        ],
        row_type="trade",
        candidate_status_by_id=status_lookup,
    )[0]

    assert decorated["selected_package_candidate_status_joined"] is True
    assert decorated["selected_package_candidate_status_lookup_key"] == canonical_key
    assert decorated["selected_package_candidate_status_join_key"] == canonical_key
    assert decorated["ultimate_package_admission_candidate_use_allowed"] is True
    assert (
        "selected_package_candidate_status_join_execution_authority_conflict"
        not in decorated
    )
    assert decorated["broker_mutation"] is False


def test_selected_package_bridge_status_join_canonicalizes_equivalent_execution_reasons() -> None:
    bridge = load_selected_package_replay_bridge()
    window = "decision_window:unit:candidate_joined"
    status = {
        **_package_exec_aliases(),
        "candidate_id": "candidate:joined",
        "stable_decision_window_id": window,
        "package_replay_executable_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed_reason": (
            "broker_cost_selector_and_scheduler_action_executable"
        ),
        "replay_candidate_use_allowed_now": True,
        "replay_candidate_use_allowed_now_reason": (
            "broker_cost_selector_and_scheduler_action_executable"
        ),
        "selected_package_candidate_use_allowed_status": (
            "broker_cost_selector_and_scheduler_action_executable"
        ),
        "pretrade_cost_packet_status": "PASSED",
        "pretrade_cost_refusal_reasons": [],
        "execution_cost_authority": "broker_pretrade_cost_only",
        "selector_action": "trade",
        "selector_reason": "broker_net_probability_confluence_lifecycle_admission_passed",
        "matched_sleeve_ids": ["sleeve:b", "sleeve:a"],
        "ultimate_package_matched_sleeve_ids": ["sleeve:b", "sleeve:a"],
    }

    decorated = bridge.decorate_rows(
        [
            {
                **_package_exec_aliases(),
                "candidate_id": "candidate:joined",
                "stable_decision_window_id": window,
                "package_replay_executable_candidate_use_allowed": True,
                "package_replay_executable_candidate_use_allowed_reason": (
                    "broker_cost_and_scheduler_action_executable"
                ),
                "replay_candidate_use_allowed_now": True,
                "replay_candidate_use_allowed_now_reason": (
                    "risk_bearing_selector_and_broker_cost_passed"
                ),
                "selected_package_candidate_use_allowed_status": (
                    "risk_bearing_selector_and_broker_cost_passed"
                ),
                "pretrade_cost_packet_status": "PASSED",
                "pretrade_cost_refusal_reasons": [],
                "execution_cost_authority": (
                    "broker_pretrade_plus_guarded_market_fallback_surcharge"
                ),
                "selector_action": "trade",
                "selector_reason": "broker_net_probability_confluence_lifecycle_admission_passed",
                "matched_sleeve_ids": ["sleeve:a", "sleeve:b"],
                "ultimate_package_matched_sleeve_ids": ["sleeve:a", "sleeve:b"],
            }
        ],
        row_type="trade",
        candidate_status_by_id=bridge.build_candidate_status_lookup([status]),
    )[0]

    assert decorated["selected_package_candidate_status_joined"] is True
    assert "selected_package_candidate_status_join_execution_authority_conflict" not in decorated
    assert decorated["package_replay_executable_candidate_use_allowed_reason"] == (
        "broker_cost_and_scheduler_action_executable"
    )
    assert decorated[
        "selected_package_status_package_replay_executable_candidate_use_allowed_reason"
    ] == "broker_cost_selector_and_scheduler_action_executable"
    assert decorated[
        "selected_package_status_package_replay_executable_candidate_use_allowed_reason_canonical_equivalent"
    ] is True
    assert decorated["replay_candidate_use_allowed_now_reason"] == (
        "risk_bearing_selector_and_broker_cost_passed"
    )
    assert decorated[
        "selected_package_status_replay_candidate_use_allowed_now_reason_canonical_equivalent"
    ] is True
    assert decorated["matched_sleeve_ids"] == ["sleeve:a", "sleeve:b"]
    assert decorated["selected_package_status_matched_sleeve_ids"] == [
        "sleeve:b",
        "sleeve:a",
    ]
    assert decorated["selected_package_status_matched_sleeve_ids_canonical_equivalent"] is True
    assert decorated["execution_cost_authority"] == (
        "broker_pretrade_plus_guarded_market_fallback_surcharge"
    )
    assert decorated[
        "selected_package_status_execution_cost_authority_canonical_equivalent"
    ] is True


def test_selected_package_bridge_status_join_unions_execution_attribution_lists() -> None:
    bridge = load_selected_package_replay_bridge()
    window = "decision_window:unit:candidate_joined"
    status = {
        "candidate_id": "candidate:joined",
        "stable_decision_window_id": window,
        "package_replay_executable_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed_reason": (
            "broker_cost_selector_and_scheduler_action_executable"
        ),
        "replay_candidate_use_allowed_now": True,
        "replay_candidate_use_allowed_now_reason": (
            "broker_cost_selector_and_scheduler_action_executable"
        ),
        "selected_package_candidate_use_allowed_status": (
            "broker_cost_selector_and_scheduler_action_executable"
        ),
        "pretrade_cost_packet_status": "PASSED",
        "pretrade_cost_refusal_reasons": [],
        "execution_cost_authority": "broker_pretrade_cost_only",
        "selector_action": "trade",
        "selector_reason": "broker_net_probability_confluence_lifecycle_admission_passed",
        "matched_sleeve_ids": ["sleeve:core"],
        "ultimate_package_matched_sleeve_ids": ["sleeve:core"],
    }

    decorated = bridge.decorate_rows(
        [
            {
                "candidate_id": "candidate:joined",
                "stable_decision_window_id": window,
                "package_replay_executable_candidate_use_allowed": True,
                "package_replay_executable_candidate_use_allowed_reason": (
                    "broker_cost_and_scheduler_action_executable"
                ),
                "replay_candidate_use_allowed_now": True,
                "replay_candidate_use_allowed_now_reason": (
                    "risk_bearing_selector_and_broker_cost_passed"
                ),
                "selected_package_candidate_use_allowed_status": (
                    "risk_bearing_selector_and_broker_cost_passed"
                ),
                "pretrade_cost_packet_status": "PASSED",
                "pretrade_cost_refusal_reasons": [],
                "execution_cost_authority": (
                    "broker_pretrade_plus_guarded_market_fallback_surcharge"
                ),
                "selector_action": "trade",
                "selector_reason": "broker_net_probability_confluence_lifecycle_admission_passed",
                "matched_sleeve_ids": ["sleeve:core", "sleeve:avoid"],
                "ultimate_package_matched_sleeve_ids": ["sleeve:core", "sleeve:avoid"],
            }
        ],
        row_type="trade",
        candidate_status_by_id=bridge.build_candidate_status_lookup([status]),
    )[0]

    assert decorated["selected_package_candidate_status_joined"] is True
    assert "selected_package_candidate_status_join_execution_authority_conflict" not in decorated
    assert decorated["matched_sleeve_ids"] == ["sleeve:avoid", "sleeve:core"]
    assert decorated["ultimate_package_matched_sleeve_ids"] == [
        "sleeve:avoid",
        "sleeve:core",
    ]
    assert decorated["selected_package_status_matched_sleeve_ids"] == ["sleeve:core"]
    assert decorated["trade_reported_matched_sleeve_ids"] == [
        "sleeve:core",
        "sleeve:avoid",
    ]
    assert decorated["selected_package_status_matched_sleeve_ids_union_merged"] is True


def test_selected_package_bridge_status_lookup_does_not_alias_status_selected_candidate_id() -> None:
    bridge = load_selected_package_replay_bridge()
    window = bridge.decision_window_id(
        "US30_cash",
        "LONG",
        "2026-05-05T05:30:00+00:00",
    )
    winner = {
        **_package_exec_aliases(),
        "candidate_id": "candidate:winner",
        "selected_candidate_id": "candidate:winner",
        "symbol": "US30_cash",
        "side": "LONG",
        "decision_time_utc": "2026-05-05T05:30:00+00:00",
        "stable_decision_window_id": window,
        "package_replay_executable_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed_reason": (
            "broker_cost_selector_and_scheduler_action_executable"
        ),
        "replay_candidate_use_allowed_now": True,
        "replay_candidate_use_allowed_now_reason": (
            "broker_cost_selector_and_scheduler_action_executable"
        ),
        "ultimate_package_role_disposition": "admission_candidate",
        "ultimate_package_matched_sleeve_ids": ["sleeve:winner"],
        "ultimate_package_matched_sleeve_count": 1,
        "ultimate_package_admission_sleeve_match_count": 1,
        "selected_package_candidate_use_allowed_status": (
            "broker_cost_selector_and_scheduler_action_executable"
        ),
        "pretrade_cost_packet_status": "PASSED",
        "selector_action": "trade",
        "selector_reason": "broker_net_probability_confluence_lifecycle_admission_passed",
        "expected_net_r": 0.91,
        "candidate_expected_net_r": 0.91,
    }
    refused_sibling = {
        "candidate_id": "candidate:refused-sibling",
        "selected_candidate_id": "candidate:winner",
        "symbol": "US30_cash",
        "side": "LONG",
        "decision_time_utc": "2026-05-05T05:30:00+00:00",
        "stable_decision_window_id": window,
        "package_replay_executable_candidate_use_allowed": False,
        "package_replay_executable_candidate_use_allowed_reason": (
            "broker_cost_packet_refused:spread_r_exceeds_selected_cell_limit"
        ),
        "selected_package_candidate_use_allowed_status": (
            "broker_cost_packet_refused:spread_r_exceeds_selected_cell_limit"
        ),
        "pretrade_cost_packet_status": "REFUSED",
        "selector_action": "reject",
        "selector_reason": (
            "broker_net_pretrade_cost_packet_refused:"
            "spread_r_exceeds_selected_cell_limit"
        ),
        "expected_net_r": 0.72,
        "candidate_expected_net_r": 0.72,
    }
    status_lookup = bridge.build_candidate_status_lookup([winner, refused_sibling])

    decorated = bridge.decorate_rows(
        [
            {
                **_package_exec_aliases(),
                "candidate_id": "candidate:winner",
                "selected_candidate_id": "candidate:winner",
                "symbol": "US30_cash",
                "side": "LONG",
                "decision_time_utc": "2026-05-05T05:30:00+00:00",
                "stable_decision_window_id": window,
                "pretrade_cost_packet_status": "PASSED",
                "package_replay_executable_candidate_use_allowed": True,
            }
        ],
        row_type="trade",
        candidate_status_by_id=status_lookup,
    )[0]

    assert decorated["selected_package_candidate_status_joined"] is True
    assert decorated["selected_package_candidate_status_join_key"] == (
        "candidate:winner@@2026-05-05T05:30:00+00:00"
    )
    assert decorated["selected_package_candidate_status_join_candidate_id"] == (
        "candidate:winner"
    )
    assert decorated["pretrade_cost_packet_status"] == "PASSED"
    assert decorated["selector_action"] == "trade"
    assert decorated["package_replay_executable_candidate_use_allowed"] is True
    assert decorated["replay_candidate_use_allowed_now"] is True
    assert decorated["role_disposition"] == "admission_candidate"
    assert decorated["matched_sleeve_count"] == 1
    assert decorated["admission_sleeve_match_count"] == 1
    assert "selected_package_non_executable_order_trade_diagnostic" not in decorated


def test_selected_package_bridge_candidate_status_join_uses_decision_instance() -> None:
    bridge = load_selected_package_replay_bridge()
    window_0815 = bridge.decision_window_id(
        "XAUUSD",
        "LONG",
        "2026-05-05T08:15:00+00:00",
    )
    window_0830 = bridge.decision_window_id(
        "XAUUSD",
        "LONG",
        "2026-05-05T08:30:00+00:00",
    )
    compact_status_rows = [
        {
            "candidate_id": "candidate:reused",
            "symbol": "XAUUSD",
            "side": "LONG",
            "decision_time_utc": "2026-05-05T08:15:00+00:00",
            "stable_decision_window_id": window_0815,
            "package_replay_candidate_use_allowed": False,
            "package_replay_executable_candidate_use_allowed": False,
            "package_replay_executable_candidate_use_allowed_reason": (
                "scheduler_materialization_skipped:selector_reduce_risk_not_new_entry_authority"
            ),
            "selected_package_candidate_use_allowed_status": (
                "scheduler_materialization_skipped:selector_reduce_risk_not_new_entry_authority"
            ),
            "scheduler_materialization_skip_reason": (
                "selector_reduce_risk_not_new_entry_authority"
            ),
        },
        {
            "candidate_id": "candidate:reused",
            "symbol": "XAUUSD",
            "side": "LONG",
            "decision_time_utc": "2026-05-05T08:30:00+00:00",
            "stable_decision_window_id": window_0830,
            "package_replay_candidate_use_allowed": True,
            "package_replay_executable_candidate_use_allowed": True,
            "package_replay_executable_candidate_use_allowed_reason": (
                "broker_cost_selector_and_scheduler_action_executable"
            ),
            "replay_candidate_use_allowed_now": True,
            "replay_candidate_use_allowed_now_reason": (
                "broker_cost_selector_and_scheduler_action_executable"
            ),
            "package_replay_authority_enabled": True,
            "source_bound_package_candidate_use_allowed_reason": (
                "replay_admission_enabled_matched_admission_sleeve"
            ),
            "package_replay_authority_evidence_class": (
                "local_replay_authority_not_live_broker_authority"
            ),
            "package_replay_result_use_status": (
                "local_replay_scorecard_not_broker_real_result"
            ),
            "package_replay_score": 0.84,
            "package_replay_source_bound_candidate_use_allowed": True,
            "ultimate_package_admission_candidate_use_allowed": True,
            "ultimate_package_role_disposition": "admission_candidate",
            "ultimate_package_matched_sleeve_count": 1,
            "ultimate_package_admission_sleeve_match_count": 1,
            "ultimate_package_non_admission_sleeve_match_count": 0,
            "selected_package_candidate_use_allowed_status": (
                "broker_cost_selector_and_scheduler_action_executable"
            ),
        },
    ]
    status_lookup = bridge.build_candidate_status_lookup(compact_status_rows)

    decorated = bridge.decorate_rows(
        [
            {
                "candidate_id": "candidate:reused",
                "symbol": "XAUUSD",
                "side": "LONG",
                "decision_time_utc": "2026-05-05T08:15:00+00:00",
                "package_replay_candidate_use_allowed": True,
                "package_replay_executable_candidate_use_allowed": True,
                "package_replay_executable_candidate_use_allowed_reason": (
                    "stale_raw_pre_scheduler_materialization"
                ),
            },
            {
                "candidate_id": "candidate:reused",
                "symbol": "XAUUSD",
                "side": "LONG",
                "decision_time_utc": "2026-05-05T08:30:00+00:00",
                "package_replay_candidate_use_allowed": False,
                "package_replay_executable_candidate_use_allowed": False,
                "package_replay_executable_candidate_use_allowed_reason": (
                    "stale_raw_other_instance"
                ),
            },
        ],
        row_type="candidate",
        candidate_status_by_id=status_lookup,
    )

    first, second = decorated
    assert first["selected_package_candidate_status_joined"] is True
    assert first["selected_package_candidate_status_join_key"] == (
        "candidate:reused@@2026-05-05T08:15:00+00:00"
    )
    assert first["package_replay_candidate_use_allowed"] is False
    assert first["package_replay_executable_candidate_use_allowed"] is False
    assert first["package_replay_executable_candidate_use_allowed_reason"] == (
        "scheduler_materialization_skipped:selector_reduce_risk_not_new_entry_authority"
    )
    assert first["scheduler_materialization_skip_reason"] == (
        "selector_reduce_risk_not_new_entry_authority"
    )

    assert second["selected_package_candidate_status_joined"] is True
    assert second["selected_package_candidate_status_join_key"] == (
        "candidate:reused@@2026-05-05T08:30:00+00:00"
    )
    assert second["package_replay_candidate_use_allowed"] is True
    assert second["package_replay_executable_candidate_use_allowed"] is True
    assert second["package_replay_executable_candidate_use_allowed_reason"] == (
        "broker_cost_selector_and_scheduler_action_executable"
    )


def test_selected_package_bridge_candidate_status_join_fails_closed_on_duplicate_exact_key() -> None:
    bridge = load_selected_package_replay_bridge()
    window = bridge.decision_window_id(
        "XAUUSD",
        "LONG",
        "2026-05-05T08:15:00+00:00",
    )
    compact_status_rows = [
        {
            "candidate_id": "candidate:duplicate",
            "symbol": "XAUUSD",
            "side": "LONG",
            "decision_time_utc": "2026-05-05T08:15:00+00:00",
            "stable_decision_window_id": window,
            "package_replay_executable_candidate_use_allowed": True,
            "package_replay_executable_candidate_use_allowed_reason": (
                "broker_cost_selector_and_scheduler_action_executable"
            ),
            "pretrade_cost_packet_status": "PASSED",
        },
        {
            "candidate_id": "candidate:duplicate",
            "symbol": "XAUUSD",
            "side": "LONG",
            "decision_time_utc": "2026-05-05T08:15:00+00:00",
            "stable_decision_window_id": window,
            "package_replay_executable_candidate_use_allowed": False,
            "package_replay_executable_candidate_use_allowed_reason": (
                "broker_cost_packet_refused:spread_r_exceeds_selected_cell_limit"
            ),
            "pretrade_cost_packet_status": "REFUSED",
        },
    ]
    status_lookup = bridge.build_candidate_status_lookup(compact_status_rows)

    decorated = bridge.decorate_rows(
        [
            {
                **_package_exec_aliases(),
                "candidate_id": "candidate:duplicate",
                "symbol": "XAUUSD",
                "side": "LONG",
                "decision_time_utc": "2026-05-05T08:15:00+00:00",
                "stable_decision_window_id": window,
                "pretrade_cost_packet_status": "PASSED",
                "package_replay_executable_candidate_use_allowed": True,
            }
        ],
        row_type="trade",
        candidate_status_by_id=status_lookup,
    )[0]

    assert decorated["selected_package_candidate_status_joined"] is False
    assert decorated["selected_package_candidate_status_join_status"] == (
        "selected_package_candidate_status_join_duplicate_ambiguous"
    )
    assert decorated["selected_package_candidate_status_join_duplicate_keys"] == [
        "candidate:duplicate@@2026-05-05T08:15:00+00:00",
        f"candidate:duplicate@@{window}",
    ]
    assert decorated["pretrade_cost_packet_status"] == "PASSED"
    assert decorated["package_replay_executable_candidate_use_allowed"] is True


def test_selected_package_bridge_candidate_status_join_fails_closed_on_exact_miss() -> None:
    bridge = load_selected_package_replay_bridge()
    window_0815 = bridge.decision_window_id(
        "XAUUSD",
        "LONG",
        "2026-05-05T08:15:00+00:00",
    )
    compact_status_rows = [
        {
            "candidate_id": "candidate:reused",
            "symbol": "XAUUSD",
            "side": "LONG",
            "decision_time_utc": "2026-05-05T08:15:00+00:00",
            "stable_decision_window_id": window_0815,
            "package_replay_candidate_use_allowed": True,
            "package_replay_executable_candidate_use_allowed": True,
            "package_replay_executable_candidate_use_allowed_reason": (
                "broker_cost_selector_and_scheduler_action_executable"
            ),
            "replay_candidate_use_allowed_now": True,
        }
    ]
    status_lookup = bridge.build_candidate_status_lookup(compact_status_rows)

    decorated = bridge.decorate_rows(
        [
            {
                "candidate_id": "candidate:reused",
                "symbol": "XAUUSD",
                "side": "LONG",
                "decision_time_utc": "2026-05-05T08:30:00+00:00",
                "package_replay_candidate_use_allowed": False,
                "package_replay_executable_candidate_use_allowed": False,
                "package_replay_executable_candidate_use_allowed_reason": (
                    "raw_row_without_exact_status"
                ),
            }
        ],
        row_type="trade",
        candidate_status_by_id=status_lookup,
    )[0]

    assert decorated["selected_package_candidate_status_joined"] is False
    assert decorated["selected_package_candidate_status_join_status"] == (
        "selected_package_candidate_status_join_exact_missing"
    )
    assert decorated["selected_package_candidate_status_join_required_windows"] == [
        bridge.decision_window_id("XAUUSD", "LONG", "2026-05-05T08:30:00+00:00")
    ]
    assert decorated["package_replay_executable_candidate_use_allowed"] is False
    assert decorated["package_replay_executable_candidate_use_allowed_reason"] == (
        "raw_row_without_exact_status"
    )


def test_selected_package_bridge_scorecard_no_selection_gets_window_candidate_diagnostic() -> None:
    bridge = load_selected_package_replay_bridge()
    decision_time = "2026-05-05T08:15:00+00:00"
    stable_window = bridge.decision_window_id("XAUUSD", "LONG", decision_time)
    compact_rows = [
        {
            "candidate_id": "candidate:window-best",
            "symbol": "XAUUSD",
            "side": "LONG",
            "decision_time_utc": decision_time,
            "stable_decision_window_id": stable_window,
            "expected_net_r": 1.25,
            "probability": 0.91,
            "fill_probability": 0.42,
            "source_completeness": 1.0,
            "package_replay_candidate_use_allowed": True,
            "package_replay_executable_candidate_use_allowed": True,
            "package_replay_executable_candidate_use_allowed_reason": (
                "broker_cost_selector_and_scheduler_action_executable"
            ),
            "ultimate_package_matched_sleeve_ids": ["sleeve:fvg-fill"],
            "ultimate_package_matched_member_axis_ids": ["axis:fvg-fill-long"],
            "packet_sidecar_id": "packet-sidecar-1",
            "packet_sidecar_hash_sha256": "packet-sidecar-hash",
            "ultimate_candidate_package_packet_hash_sha256": "package-packet-hash",
            "ultimate_candidate_package_packet_shape_hash_sha256": (
                "package-packet-shape-hash"
            ),
        },
        {
            "candidate_id": "candidate:window-weaker",
            "symbol": "XAUUSD",
            "side": "LONG",
            "decision_time_utc": decision_time,
            "stable_decision_window_id": stable_window,
            "expected_net_r": 0.40,
            "probability": 0.70,
            "fill_probability": 0.30,
            "source_completeness": 1.0,
            "package_replay_candidate_use_allowed": True,
            "package_replay_executable_candidate_use_allowed": True,
            "package_replay_executable_candidate_use_allowed_reason": (
                "broker_cost_selector_and_scheduler_action_executable"
            ),
        },
    ]

    decorated = bridge.decorate_rows(
        [
            {
                "stable_decision_window_id": stable_window,
                "symbol": "XAUUSD",
                "side": "LONG",
                "decision_time_utc": decision_time,
                "selected_action_class": "zero_trade",
            }
        ],
        row_type="scorecard",
        candidate_status_by_id=bridge.build_candidate_status_lookup(compact_rows),
        candidate_status_by_window=bridge.build_candidate_status_window_lookup(
            compact_rows
        ),
    )[0]

    assert decorated["selected_package_candidate_status_joined"] is False
    assert decorated["selected_package_candidate_status_join_status"] == (
        "selected_package_candidate_status_join_exact_missing_with_window_diagnostic"
    )
    assert decorated["selected_package_window_candidate_status_joined"] is True
    assert decorated["selected_package_window_candidate_count"] == 2
    assert decorated["selected_package_window_best_candidate_id"] == (
        "candidate:window-best"
    )
    assert decorated["selected_package_window_best_expected_net_r"] == 1.25
    assert decorated["selected_package_window_best_probability"] == 0.91
    assert decorated["selected_package_window_best_fill_probability"] == 0.42
    assert decorated["selected_package_window_best_matched_sleeve_ids"] == [
        "sleeve:fvg-fill"
    ]
    assert (
        decorated["selected_package_window_best_ultimate_candidate_package_packet_hash_sha256"]
        == "package-packet-hash"
    )
    assert "selected_candidate_id" not in decorated


def test_selected_package_bridge_candidate_status_join_fails_closed_without_window() -> None:
    bridge = load_selected_package_replay_bridge()
    window_0815 = bridge.decision_window_id(
        "XAUUSD",
        "LONG",
        "2026-05-05T08:15:00+00:00",
    )
    status_lookup = bridge.build_candidate_status_lookup(
        [
            {
                "candidate_id": "candidate:reused",
                "symbol": "XAUUSD",
                "side": "LONG",
                "decision_time_utc": "2026-05-05T08:15:00+00:00",
                "stable_decision_window_id": window_0815,
                "package_replay_candidate_use_allowed": True,
                "package_replay_executable_candidate_use_allowed": True,
                "package_replay_executable_candidate_use_allowed_reason": (
                    "broker_cost_selector_and_scheduler_action_executable"
                ),
                "replay_candidate_use_allowed_now": True,
            }
        ]
    )

    decorated = bridge.decorate_rows(
        [
            {
                "candidate_id": "candidate:reused",
                "package_replay_candidate_use_allowed": False,
                "package_replay_executable_candidate_use_allowed": False,
                "package_replay_executable_candidate_use_allowed_reason": (
                    "raw_row_without_decision_window"
                ),
            }
        ],
        row_type="trade",
        candidate_status_by_id=status_lookup,
    )[0]

    assert decorated["selected_package_candidate_status_joined"] is False
    assert decorated["selected_package_candidate_status_join_status"] == (
        "selected_package_candidate_status_join_window_missing"
    )
    assert decorated["package_replay_executable_candidate_use_allowed"] is False
    assert decorated["package_replay_executable_candidate_use_allowed_reason"] == (
        "raw_row_without_decision_window"
    )


def test_selected_package_bridge_scorecard_join_uses_selected_scheduler_option_context() -> None:
    bridge = load_selected_package_replay_bridge()
    window = bridge.decision_window_id(
        "USOIL_cash",
        "LONG",
        "2026-05-05T00:15:00+00:00",
    )
    compact_status_rows = [
        {
            "candidate_id": "candidate:scorecard",
            "symbol": "USOIL_cash",
            "side": "LONG",
            "decision_time_utc": "2026-05-05T00:15:00+00:00",
            "stable_decision_window_id": "decision_window:USOIL_cash:LONG:2026-05-05T00:15:00+00:00",
            "package_replay_executable_candidate_use_allowed": True,
            "package_replay_executable_candidate_use_allowed_reason": (
                "broker_cost_selector_and_scheduler_action_executable"
            ),
            "replay_candidate_use_allowed_now": True,
            "replay_candidate_use_allowed_now_reason": (
                "broker_cost_selector_and_scheduler_action_executable"
            ),
            "package_replay_authority_enabled": True,
            "source_bound_package_candidate_use_allowed_reason": (
                "replay_admission_enabled_matched_admission_sleeve"
            ),
            "package_replay_authority_evidence_class": (
                "local_replay_authority_not_live_broker_authority"
            ),
            "package_replay_result_use_status": (
                "local_replay_scorecard_not_broker_real_result"
            ),
            "package_replay_score": 0.84,
            "package_replay_source_bound_candidate_use_allowed": True,
            "ultimate_package_admission_candidate_use_allowed": True,
            "ultimate_package_role_disposition": "admission_candidate",
            "ultimate_package_matched_sleeve_count": 1,
            "ultimate_package_admission_sleeve_match_count": 1,
            "ultimate_package_non_admission_sleeve_match_count": 0,
            "selected_package_candidate_use_allowed_status": (
                "broker_cost_selector_and_scheduler_action_executable"
            ),
            "candidate_expected_net_r": 1.27,
            "expected_net_r": 1.27,
            "probability": 0.93,
            "candidate_probability": 0.93,
            "fill_probability": 0.69,
            "candidate_fill_probability": 0.69,
            "source_completeness": 1.0,
            "source_completeness_status": "source_completeness_present",
            "ultimate_package_role_disposition": "admission_candidate",
            "ultimate_package_matched_sleeve_ids": ["sleeve:scorecard"],
            "ultimate_package_matched_sleeve_count": 1,
            "ultimate_package_admission_sleeve_match_count": 1,
            "ultimate_package_matched_member_axis_ids": ["member_axis:scorecard"],
            "ultimate_package_matched_member_axis_count": 1,
            "ultimate_package_admission_member_axis_match_count": 1,
            "ultimate_package_matched_member_axis_role_counts": {
                "scheduler_lifecycle_core": 1
            },
        }
    ]
    status_lookup = bridge.build_candidate_status_lookup(compact_status_rows)

    decorated = bridge.decorate_rows(
        [
            {
                "selected_candidate_id": "candidate:scorecard",
                "selected_scheduler_primary_candidate_id": "candidate:scorecard",
                "decision_time_utc": "2026-05-05T00:15:00+00:00",
                "stable_decision_window_id": "scheduler_window:2026-05-05T00:15:00+00:00",
                "selected_scheduler_option_trace": [
                    {
                        "candidate_id": "candidate:scorecard",
                        "symbol": "USOIL_cash",
                        "side": "LONG",
                        "decision_time_utc": "2026-05-05T00:15:00+00:00",
                        "expected_net_r": 1.20,
                        "probability": 0.90,
                    }
                ],
                "expected_net_r": 1.20,
                "candidate_expected_net_r": 1.20,
                "source_completeness_status": "complete",
            }
        ],
        row_type="scorecard",
        candidate_status_by_id=status_lookup,
    )[0]

    assert decorated["selected_package_candidate_status_joined"] is True
    assert decorated["selected_package_candidate_status_join_key"] == (
        "candidate:scorecard@@2026-05-05T00:15:00+00:00"
    )
    assert decorated["scheduler_stable_decision_window_id"] == (
        "scheduler_window:2026-05-05T00:15:00+00:00"
    )
    assert decorated["stable_decision_window_id"] == window
    assert decorated["selected_package_candidate_status_join_candidate_id"] == (
        "candidate:scorecard"
    )
    assert decorated["package_replay_executable_candidate_use_allowed"] is True
    assert decorated["selected_package_candidate_use_allowed_status"] == (
        "broker_cost_selector_and_scheduler_action_executable"
    )
    assert decorated["expected_net_r"] == 1.27
    assert decorated["scorecard_reported_expected_net_r"] == 1.20
    assert decorated["probability"] == 0.93
    assert decorated["candidate_probability"] == 0.93
    assert decorated["fill_probability"] == 0.69
    assert decorated["candidate_fill_probability"] == 0.69
    assert decorated["source_completeness_status"] == "source_completeness_present"
    assert decorated["ultimate_package_role_disposition"] == "admission_candidate"
    assert decorated["role_disposition"] == "admission_candidate"
    assert decorated["ultimate_package_matched_sleeve_ids"] == ["sleeve:scorecard"]
    assert decorated["ultimate_package_matched_sleeve_count"] == 1
    assert decorated["matched_sleeve_count"] == 1
    assert decorated["ultimate_package_admission_sleeve_match_count"] == 1
    assert decorated["admission_sleeve_match_count"] == 1
    assert decorated["ultimate_package_matched_member_axis_role_counts"] == {
        "scheduler_lifecycle_core": 1
    }


def test_selected_package_bridge_scorecard_without_final_selection_keeps_status_join_diagnostic() -> None:
    bridge = load_selected_package_replay_bridge()
    compact_status_rows = [
        {
            "candidate_id": "candidate:rejected",
            "symbol": "XAUUSD",
            "side": "SHORT",
            "decision_time_utc": "2026-05-05T04:30:00+00:00",
            "stable_decision_window_id": bridge.decision_window_id(
                "XAUUSD",
                "SHORT",
                "2026-05-05T04:30:00+00:00",
            ),
            "package_replay_candidate_use_allowed": True,
            "package_replay_executable_candidate_use_allowed": True,
            "package_replay_executable_candidate_use_allowed_reason": (
                "broker_cost_selector_and_scheduler_action_executable"
            ),
            "replay_candidate_use_allowed_now": True,
            "replay_candidate_use_allowed_now_reason": (
                "broker_cost_selector_and_scheduler_action_executable"
            ),
            "canonical_replay_candidate_instance_key": (
                "candidate:rejected@@2026-05-05T04:30:00+00:00"
            ),
            "risk_finalizer_probe_instance_key": (
                "candidate:rejected@@2026-05-05T04:30:00+00:00"
            ),
            "source_bound_replay_candidate_instance_key": (
                "candidate:rejected@@2026-05-05T04:30:00+00:00"
            ),
            "candidate_instance_identity_status": "materialized",
            "candidate_expected_net_r": 1.19,
            "expected_net_r": 1.19,
            "probability": 0.91,
            "candidate_probability": 0.91,
            "source_completeness": 1.0,
            "source_completeness_status": "source_completeness_present",
        }
    ]
    status_lookup = bridge.build_candidate_status_lookup(compact_status_rows)

    decorated = bridge.decorate_rows(
        [
            {
                "selected_candidate_id": None,
                "selected_candidate_ids": [],
                "selected_action_class": "zero_trade",
                "decision_time_utc": "2026-05-05T04:30:00+00:00",
                "stable_decision_window_id": (
                    "scheduler_window:2026-05-05T04:30:00+00:00"
                ),
                "post_risk_finalizer_scheduler_option_trace": [
                    {
                        "candidate_id": "candidate:rejected",
                        "symbol": "XAUUSD",
                        "side": "SHORT",
                        "decision_time_utc": "2026-05-05T04:30:00+00:00",
                        "stable_decision_window_id": bridge.decision_window_id(
                            "XAUUSD",
                            "SHORT",
                            "2026-05-05T04:30:00+00:00",
                        ),
                    }
                ],
                "package_replay_candidate_use_allowed": True,
                "canonical_replay_candidate_instance_key": (
                    "stale@@2026-05-05T04:30:00+00:00"
                ),
                "candidate_instance_identity_status": "materialized",
            }
        ],
        row_type="scorecard",
        candidate_status_by_id=status_lookup,
    )[0]

    assert decorated["selected_package_candidate_status_joined"] is True
    assert decorated["selected_package_status_package_replay_candidate_use_allowed"] is True
    assert (
        decorated[
            "selected_package_status_package_replay_executable_candidate_use_allowed"
        ]
        is True
    )
    assert decorated["package_replay_candidate_use_allowed"] is None
    assert decorated["package_replay_executable_candidate_use_allowed"] is None
    assert decorated["replay_candidate_use_allowed_now"] is None
    assert decorated["canonical_replay_candidate_instance_key"] is None
    assert decorated["risk_finalizer_probe_instance_key"] is None
    assert decorated["source_bound_replay_candidate_instance_key"] is None
    assert decorated["candidate_instance_identity_status"] is None
    assert decorated["scorecard_no_final_selection_candidate_authority_scrubbed"] is True
    assert decorated["expected_net_r"] == 1.19
    assert decorated["probability"] == 0.91


def test_selected_package_bridge_order_trade_backfills_selected_scheduler_aliases() -> None:
    bridge = load_selected_package_replay_bridge()
    compact_status_rows = [
        {
            "candidate_id": "candidate:order",
            "symbol": "GER40",
            "side": "SHORT",
            "decision_time_utc": "2026-05-05T10:15:00+00:00",
            "stable_decision_window_id": bridge.decision_window_id(
                "GER40",
                "SHORT",
                "2026-05-05T10:15:00+00:00",
            ),
            "package_replay_executable_candidate_use_allowed": True,
            "package_replay_executable_candidate_use_allowed_reason": (
                "broker_cost_selector_and_scheduler_action_executable"
            ),
            "replay_candidate_use_allowed_now": True,
            "replay_candidate_use_allowed_now_reason": (
                "broker_cost_selector_and_scheduler_action_executable"
            ),
            "package_replay_authority_enabled": True,
            "source_bound_package_candidate_use_allowed_reason": (
                "replay_admission_enabled_matched_admission_sleeve"
            ),
            "package_replay_authority_evidence_class": (
                "local_replay_authority_not_live_broker_authority"
            ),
            "package_replay_result_use_status": (
                "local_replay_scorecard_not_broker_real_result"
            ),
            "package_replay_score": 0.84,
            "package_replay_source_bound_candidate_use_allowed": True,
            "ultimate_package_admission_candidate_use_allowed": True,
            "ultimate_package_role_disposition": "admission_candidate",
            "ultimate_package_matched_sleeve_count": 1,
            "ultimate_package_admission_sleeve_match_count": 1,
            "ultimate_package_non_admission_sleeve_match_count": 0,
            "selected_package_candidate_use_allowed_status": (
                "broker_cost_selector_and_scheduler_action_executable"
            ),
            "ultimate_package_matched_member_axis_role_counts": {
                "scheduler_lifecycle_core": 1
            },
            "ultimate_package_matched_sleeve_ids": ["sleeve:order"],
            "target_reference": 15500.0,
            "risk_reward_ratio": 1.85,
            "canonical_geometry_status": "canonicalized",
            "canonical_geometry_source": "selected_package_unit_fixture",
            "broker_pretrade_cost_r": 0.045,
            "broker_calibrated_expected_cost_r": 0.045,
        }
    ]
    status_lookup = bridge.build_candidate_status_lookup(compact_status_rows)

    decorated = bridge.decorate_rows(
        [
            {
                "candidate_id": "candidate:order",
                "selected_candidate_id": "candidate:order",
                "decision_time_utc": "2026-05-05T10:15:00+00:00",
                "symbol": "GER40",
                "side": "SHORT",
                "scheduler_rank": 3,
                "scheduler_score": 2.45,
                "scheduler_option_status": "candidate_ranked",
                "scheduler_option_reason": "candidate_ranked_against_window",
                "scheduler_action_class": "new_position",
                "scheduler_expected_net_r": 0.88,
                "scheduler_probability": 0.81,
                "scheduler_fill_probability": 0.72,
                "scheduler_source_completeness": 1.0,
                "scheduler_candidate_decision_inputs": {
                    "expected_net_r": 0.88,
                    "probability": 0.81,
                    "requested_risk_pct": 1.0,
                    "approved_risk_pct": 0.5,
                    "risk_delta_pct": -0.5,
                    "broker_pretrade_cost_r": 0.045,
                    "broker_calibrated_expected_cost_r": 0.045,
                },
                "selector_action": "trade",
                "selector_reason": "unit",
                "pretrade_cost_packet_status": "PASSED",
                "cost_authority": "broker_calibrated_replay_cost",
                "source_bound_signal_r": 123.0,
                "package_replay_candidate_use_allowed": True,
            }
        ],
        row_type="order",
        candidate_status_by_id=status_lookup,
    )[0]

    assert decorated["selected_package_candidate_status_joined"] is True
    assert decorated["selected_scheduler_primary_candidate_id"] == "candidate:order"
    assert decorated["selected_scheduler_input_status"] == (
        "order_trade_scheduler_alias_backfill"
    )
    assert decorated["selected_scheduler_rank"] == 3
    assert decorated["selected_scheduler_score"] == 2.45
    assert decorated["selected_scheduler_expected_net_r"] == 0.88
    assert decorated["selected_scheduler_probability"] == 0.81
    assert decorated["selected_scheduler_fill_probability"] == 0.72
    assert decorated["selected_scheduler_requested_risk_pct"] == 1.0
    assert decorated["selected_scheduler_approved_risk_pct"] == 0.5
    assert decorated["selected_scheduler_risk_delta_pct"] == -0.5
    assert decorated["selected_scheduler_broker_pretrade_cost_r"] == 0.045
    assert decorated["selected_scheduler_broker_calibrated_expected_cost_r"] == 0.045
    assert decorated["selected_scheduler_selector_action"] == "trade"
    assert decorated["selected_scheduler_cost_authority"] == "broker_calibrated_replay_cost"
    assert (
        decorated["selected_scheduler_package_replay_source_bound_candidate_use_allowed"]
        is True
    )
    assert decorated["selected_scheduler_package_replay_candidate_use_allowed"] is True
    assert decorated["selected_scheduler_package_replay_authority_enabled"] is True
    assert decorated[
        "selected_scheduler_source_bound_package_candidate_use_allowed_reason"
    ] == "replay_admission_enabled_matched_admission_sleeve"
    assert decorated["selected_scheduler_package_replay_authority_evidence_class"] == (
        "local_replay_authority_not_live_broker_authority"
    )
    assert decorated["selected_scheduler_package_replay_result_use_status"] == (
        "local_replay_scorecard_not_broker_real_result"
    )
    assert decorated["selected_scheduler_package_replay_score"] == 0.84
    assert (
        decorated["selected_scheduler_package_replay_executable_candidate_use_allowed"]
        is True
    )
    assert decorated[
        "selected_scheduler_package_replay_executable_candidate_use_allowed_reason"
    ] == "broker_cost_selector_and_scheduler_action_executable"
    assert decorated["selected_scheduler_replay_candidate_use_allowed_now"] is True
    assert decorated["selected_scheduler_replay_candidate_use_allowed_now_reason"] == (
        "broker_cost_selector_and_scheduler_action_executable"
    )
    assert decorated[
        "selected_scheduler_selected_package_candidate_use_allowed_status"
    ] == "broker_cost_selector_and_scheduler_action_executable"
    assert (
        decorated["selected_scheduler_ultimate_package_admission_candidate_use_allowed"]
        is True
    )
    assert decorated["selected_scheduler_decision_inputs"]["expected_net_r"] == 0.88
    assert decorated["target_reference"] == 15500.0
    assert decorated["risk_reward_ratio"] == 1.85
    assert decorated["canonical_geometry_status"] == "canonicalized"
    assert decorated["canonical_geometry_source"] == "selected_package_unit_fixture"
    assert decorated["ultimate_package_matched_sleeve_ids"] == ["sleeve:order"]
    assert decorated["role_disposition"] == "admission_candidate"
    assert decorated["matched_sleeve_count"] == 1
    assert decorated["admission_sleeve_match_count"] == 1
    assert decorated["non_admission_sleeve_match_count"] == 0
    assert decorated["ultimate_package_matched_member_axis_role_counts"] == {
        "scheduler_lifecycle_core": 1
    }


def test_selected_package_bridge_trade_rows_preserve_selected_scheduler_package_provenance() -> None:
    bridge = load_selected_package_replay_bridge()
    window = bridge.decision_window_id(
        "XAUUSD",
        "LONG",
        "2026-05-05T08:30:00+00:00",
    )
    status_lookup = bridge.build_candidate_status_lookup(
        [
            {
                "candidate_id": "candidate:filled-trade",
                "symbol": "XAUUSD",
                "side": "LONG",
                "decision_time_utc": "2026-05-05T08:30:00+00:00",
                "framework": "origin_fvg_fill",
                "current_framework": "fvg_fill",
                "origin_family": "fvg_fill",
                "candidate_origin_family": "origin_fvg_fill",
                "route_family": "scheduler_lifecycle_merge",
                "route_session": "off_configured_session",
                "session": "moonshot_h08_09",
                "session_bucket": "moonshot_h08_09",
                "setup_family": "source_bound_router_refusal",
                "dynamic_geometry_policy": "momentum_exhaustion",
                "stable_decision_window_id": window,
                "package_replay_source_bound_candidate_use_allowed": True,
                "package_replay_candidate_use_allowed": True,
                "package_replay_executable_candidate_use_allowed": True,
                "package_replay_executable_candidate_use_allowed_reason": (
                    "broker_cost_selector_and_scheduler_action_executable"
                ),
                "replay_candidate_use_allowed_now": True,
                "replay_candidate_use_allowed_now_reason": (
                    "broker_cost_selector_and_scheduler_action_executable"
                ),
                "package_replay_authority_enabled": True,
                "source_bound_package_candidate_use_allowed_reason": (
                    "replay_admission_enabled_matched_admission_sleeve"
                ),
                "package_replay_authority_evidence_class": (
                    "local_replay_authority_not_live_broker_authority"
                ),
                "package_replay_result_use_status": (
                    "local_replay_scorecard_not_broker_real_result"
                ),
                "package_replay_score": 0.84,
                "selected_package_candidate_use_allowed_status": (
                    "broker_cost_selector_and_scheduler_action_executable"
                ),
                "ultimate_package_admission_candidate_use_allowed": True,
            }
        ]
    )

    decorated = bridge.decorate_rows(
        [
            {
                "candidate_id": "candidate:filled-trade",
                "symbol": "XAUUSD",
                "side": "LONG",
                "decision_time_utc": "2026-05-05T08:30:00+00:00",
                "stable_decision_window_id": window,
                "fill_status": "filled_from_ordered_m1_path",
                "net_proxy_r": 1.2,
            }
        ],
        row_type="trade",
        candidate_status_by_id=status_lookup,
    )[0]

    assert decorated["selected_package_candidate_status_joined"] is True
    assert (
        decorated[
            "selected_scheduler_package_replay_source_bound_candidate_use_allowed"
        ]
        is True
    )
    assert decorated["selected_scheduler_package_replay_candidate_use_allowed"] is True
    assert decorated["selected_scheduler_package_replay_authority_enabled"] is True
    assert decorated["selected_scheduler_package_replay_authority_evidence_class"] == (
        "local_replay_authority_not_live_broker_authority"
    )
    assert decorated["selected_scheduler_package_replay_result_use_status"] == (
        "local_replay_scorecard_not_broker_real_result"
    )
    assert decorated["selected_scheduler_package_replay_score"] == 0.84
    assert (
        decorated["selected_scheduler_package_replay_executable_candidate_use_allowed"]
        is True
    )
    assert decorated[
        "selected_scheduler_package_replay_executable_candidate_use_allowed_reason"
    ] == "broker_cost_selector_and_scheduler_action_executable"
    assert decorated["selected_scheduler_replay_candidate_use_allowed_now"] is True
    assert decorated["selected_scheduler_replay_candidate_use_allowed_now_reason"] == (
        "broker_cost_selector_and_scheduler_action_executable"
    )
    assert (
        decorated["selected_scheduler_selected_package_candidate_use_allowed_status"]
        == "broker_cost_selector_and_scheduler_action_executable"
    )
    assert (
        decorated["selected_scheduler_ultimate_package_admission_candidate_use_allowed"]
        is True
    )
    for key, expected in {
        "framework": "origin_fvg_fill",
        "current_framework": "fvg_fill",
        "origin_family": "fvg_fill",
        "candidate_origin_family": "origin_fvg_fill",
        "route_family": "scheduler_lifecycle_merge",
        "route_session": "off_configured_session",
        "session": "moonshot_h08_09",
        "session_bucket": "moonshot_h08_09",
        "setup_family": "source_bound_router_refusal",
        "dynamic_geometry_policy": "momentum_exhaustion",
    }.items():
        assert decorated[key] == expected
        assert decorated[f"selected_scheduler_{key}"] == expected


def test_selected_package_bridge_compact_preserves_candidate_carried_package_evidence() -> None:
    bridge = load_selected_package_replay_bridge()
    rows = bridge.compact_candidate_rows(
        [
            {
                "candidate_id": "candidate:carried-package",
                "symbol": "USOIL_cash",
                "side": "LONG",
                "decision_time_utc": "2026-05-05T00:15:00+00:00",
                "framework": "origin_fvg_fill",
                "current_framework": "fvg_fill",
                "origin_family": "fvg_fill",
                "candidate_origin_family": "origin_fvg_fill",
                "route_family": "scheduler_lifecycle_merge",
                "route_session": "off_configured_session",
                "session": "moonshot_h00_01",
                "session_bucket": "moonshot_h00_01",
                "setup_family": "source_bound_router_refusal",
                "dynamic_geometry_policy": "momentum_exhaustion",
                "source_bound_package_candidate_use_allowed": True,
                "source_bound_package_candidate_use_allowed_reason": (
                    "replay_admission_enabled_matched_admission_sleeve"
                ),
                "ultimate_package_source_bound_candidate_use_allowed": True,
                "package_replay_source_bound_candidate_use_allowed": True,
                "package_replay_candidate_use_allowed": True,
                "package_replay_authority_enabled": True,
                "package_replay_authority_evidence_class": (
                    "local_replay_authority_not_live_broker_authority"
                ),
                "package_replay_result_use_status": (
                    "local_replay_scorecard_not_broker_real_result"
                ),
                "package_replay_score": 0.84,
                "ultimate_package_decision_status": "shadow_sleeve_matches_found",
                "ultimate_package_role_disposition": "admission_candidate",
                "ultimate_package_matched_sleeve_ids": "sleeve:carried",
                "ultimate_package_matched_sleeve_count": 1,
                "ultimate_package_admission_sleeve_match_count": 1,
                "ultimate_package_selector_shadow_score": 0.71,
                "ultimate_package_combined_source_bound_signal_r_sum": 123.45,
                "ultimate_package_max_combined_source_bound_signal_r": 123.45,
                "ultimate_package_scheduler_parity_evidence_class": (
                    "source_bound_package_replay_parity_scheduler_input"
                ),
                "ultimate_package_matched_member_axis_ids": ["member_axis:carried"],
                "ultimate_package_matched_member_axis_count": 1,
                "ultimate_package_admission_member_axis_match_count": 1,
                "ultimate_package_matched_member_axis_role_counts": {
                    "scheduler_lifecycle_core": 1
                },
                "ultimate_package_member_axis_source_bound_signal_r_sum": 12.0,
                "ultimate_package_member_axis_max_source_bound_signal_r": 12.0,
                "ultimate_package_member_axis_evidence_class": (
                    "candidate_carried_source_member_axis_overlap_fallback"
                ),
                "risk_finalizer_signed_soft_transfer_displacement_allowed": True,
                "risk_finalizer_signed_soft_transfer_displacement_source_boundary": (
                    "predecision_signed_package_soft_transfer_quality_cost_source_order_no_outcome_fields"
                ),
                "risk_finalizer_signed_soft_transfer_displacement_uses_outcome_fields": False,
                "finalizer_admission_rank_reason": (
                    "risk_admitted_signed_soft_transfer_displacement_rank"
                ),
            }
        ],
        [],
    )

    assert len(rows) == 1
    row = rows[0]
    assert row["ultimate_package_role_disposition"] == "admission_candidate"
    assert row["role_disposition"] == "admission_candidate"
    assert row["package_replay_authority_enabled"] is True
    assert row["source_bound_package_candidate_use_allowed_reason"] == (
        "replay_admission_enabled_matched_admission_sleeve"
    )
    assert row["package_replay_authority_evidence_class"] == (
        "local_replay_authority_not_live_broker_authority"
    )
    assert row["package_replay_result_use_status"] == (
        "local_replay_scorecard_not_broker_real_result"
    )
    assert row["package_replay_score"] == 0.84
    assert row["package_replay_source_bound_candidate_use_allowed"] is True
    for key, expected in {
        "framework": "origin_fvg_fill",
        "current_framework": "fvg_fill",
        "origin_family": "fvg_fill",
        "candidate_origin_family": "origin_fvg_fill",
        "route_family": "scheduler_lifecycle_merge",
        "route_session": "off_configured_session",
        "session": "moonshot_h00_01",
        "session_bucket": "moonshot_h00_01",
        "setup_family": "source_bound_router_refusal",
        "dynamic_geometry_policy": "momentum_exhaustion",
    }.items():
        assert row[key] == expected
    assert row["ultimate_package_matched_sleeve_ids"] == ["sleeve:carried"]
    assert row["matched_sleeve_ids"] == ["sleeve:carried"]
    assert row["ultimate_package_matched_sleeve_count"] == 1
    assert row["matched_sleeve_count"] == 1
    assert row["ultimate_package_admission_sleeve_match_count"] == 1
    assert row["admission_sleeve_match_count"] == 1
    assert row["non_admission_sleeve_match_count"] == 0
    assert row["ultimate_package_selector_shadow_score"] == 0.71
    assert row["ultimate_package_matched_member_axis_ids"] == ["member_axis:carried"]
    assert row["ultimate_package_matched_member_axis_count"] == 1
    assert row["ultimate_package_admission_member_axis_match_count"] == 1
    assert row["ultimate_package_matched_member_axis_role_counts"] == {
        "scheduler_lifecycle_core": 1
    }
    assert row["ultimate_package_member_axis_evidence_class"] == (
        "candidate_carried_source_member_axis_overlap_fallback"
    )
    assert row["risk_finalizer_signed_soft_transfer_displacement_allowed"] is True
    assert row["risk_finalizer_signed_soft_transfer_displacement_source_boundary"] == (
        "predecision_signed_package_soft_transfer_quality_cost_source_order_no_outcome_fields"
    )
    assert row["risk_finalizer_signed_soft_transfer_displacement_uses_outcome_fields"] is False
    assert row["finalizer_admission_rank_reason"] == (
        "risk_admitted_signed_soft_transfer_displacement_rank"
    )


def test_selected_package_bridge_accepts_package_replay_source_bound_alias() -> None:
    bridge = load_selected_package_replay_bridge()

    fields = bridge.selected_package_bridge_quality_fields(
        {
            "candidate_id": "candidate:package-source-bound",
            "symbol": "XAUUSD",
            "side": "LONG",
            "decision_time_utc": "2026-05-05T00:15:00+00:00",
            "entry_price": 3300.0,
            "stop_loss": 3295.0,
            "take_profit_1": 3310.0,
            "expected_net_r": 1.1,
            "probability": 0.82,
            "fill_probability": 0.61,
            **_execution_fillability_fields(0.61),
            "source_completeness": 1.0,
            "source_completeness_status": "source_completeness_present",
            "pretrade_cost_packet_status": "PASSED",
            "cost_authority": "broker_calibrated_replay_cost",
            "cost_source_gap_status": "source_bound_cost_authority_present",
            "candidate_cost_r_fallback_is_authority": False,
            "selector_action": "trade",
            "scheduler_materialization_action_intent": "new_position",
            "package_replay_source_bound_candidate_use_allowed": True,
            "ultimate_package_effective_source_bound_candidate_use_allowed": True,
            "ultimate_package_admission_sleeve_match_count": 1,
            "ultimate_package_matched_sleeve_count": 1,
            "ultimate_package_combined_source_bound_signal_r_sum": 42.0,
            "ultimate_package_max_combined_source_bound_signal_r": 42.0,
        }
    )

    assert fields["source_bound_package_candidate_use_allowed"] is True
    assert fields["ultimate_package_source_bound_candidate_use_allowed"] is True
    assert fields["package_replay_source_bound_candidate_use_allowed"] is True
    assert fields["package_replay_candidate_use_allowed"] is True
    assert fields["package_replay_executable_candidate_use_allowed"] is True
    assert fields["package_replay_executable_candidate_use_allowed_reason"] == (
        "broker_cost_selector_and_scheduler_action_executable"
    )
    assert fields["package_authority_has_order_geometry"] is True
    assert fields["package_authority_executable_candidate_status"] == (
        "package_authority_candidate_executable"
    )


def test_selected_package_bridge_preserves_source_bound_membership_when_non_executable() -> None:
    bridge = load_selected_package_replay_bridge()

    fields = bridge.selected_package_bridge_quality_fields(
        {
            "candidate_id": "candidate:package-source-bound-non-executable",
            "symbol": "XAUUSD",
            "side": "LONG",
            "decision_time_utc": "2026-05-05T00:15:00+00:00",
            "entry_price": 3300.0,
            "stop_loss": 3295.0,
            "take_profit_1": 3310.0,
            "expected_net_r": 1.1,
            "probability": 0.82,
            "fill_probability": 0.61,
            "source_completeness": 1.0,
            "source_completeness_status": "source_completeness_present",
            "pretrade_cost_packet_status": "PASSED",
            "cost_authority": "broker_calibrated_replay_cost",
            "cost_source_gap_status": "source_bound_cost_authority_present",
            "candidate_cost_r_fallback_is_authority": False,
            "selector_action": "reject",
            "selector_reason": "no_shadow_sleeve_match",
            "scheduler_materialization_action_intent": "new_position",
            "package_replay_source_bound_candidate_use_allowed": True,
            "ultimate_package_effective_source_bound_candidate_use_allowed": True,
            "ultimate_package_admission_sleeve_match_count": 1,
            "ultimate_package_matched_sleeve_count": 1,
            "ultimate_package_combined_source_bound_signal_r_sum": 42.0,
            "ultimate_package_max_combined_source_bound_signal_r": 42.0,
        }
    )

    assert fields["source_bound_package_candidate_use_allowed"] is True
    assert fields["ultimate_package_source_bound_candidate_use_allowed"] is True
    assert fields["ultimate_package_effective_source_bound_candidate_use_allowed"] is True
    assert fields["ultimate_package_effective_source_bound_signal_r"] == 0.0
    assert fields["ultimate_package_combined_source_bound_signal_r_sum"] == 0.0
    assert fields["ultimate_package_max_combined_source_bound_signal_r"] == 0.0
    assert fields["diagnostic_ultimate_package_effective_source_bound_signal_r"] == 42.0
    assert fields["diagnostic_ultimate_package_combined_source_bound_signal_r_sum"] == 42.0
    assert fields["diagnostic_ultimate_package_max_combined_source_bound_signal_r"] == 42.0
    assert fields["missed_opportunity_ultimate_package_effective_source_bound_signal_r"] == 42.0
    assert fields["package_replay_executable_candidate_use_allowed"] is False
    assert fields["ultimate_package_effective_source_bound_non_executable"] is True
    assert fields["ultimate_package_effective_executable_authority_allowed"] is False
    assert fields["ultimate_package_effective_source_bound_non_executable_reason"] == (
        "selector_not_risk_bearing_no_shadow_sleeve_match"
    )


def test_selected_package_bridge_builds_execution_disposition_rows() -> None:
    bridge = load_selected_package_replay_bridge()

    compact_rows = [
        {
            "candidate_id": "candidate-skip",
            "decision_time_utc": "2026-05-05T00:15:00+00:00",
            "symbol": "XAUUSD",
            "side": "LONG",
            "canonical_replay_candidate_instance_key": (
                "candidate-skip@@2026-05-05T00:15:00+00:00"
            ),
            "timeframe": "M15",
            "same_symbol_replay_exposure_context": {
                "symbol": "XAUUSD",
                "side": "LONG",
                "same_side_pending_ids": ["pending-skip"],
                "same_side_pending_order_ids": ["pending-skip"],
            },
            "canonical_replay_context_projection_status": "materialized",
            "replacement_reallocation_quality_score": 0.61,
            "selected_package_replay_row": True,
            "package_replay_executable_candidate_use_allowed": False,
            "scheduler_materialization_skip_reason": (
                "selector_reduce_risk_not_new_entry_authority"
            ),
            "source_bound_package_candidate_use_allowed": True,
            "ultimate_package_effective_source_bound_candidate_use_allowed": True,
            "ultimate_package_effective_executable_authority_allowed": True,
            "ultimate_package_effective_source_bound_signal_r": 7.0,
        },
        {
            "candidate_id": "candidate-delay",
            "decision_time_utc": "2026-05-05T00:30:00+00:00",
            "symbol": "XAUUSD",
            "side": "LONG",
            "canonical_replay_candidate_instance_key": (
                "candidate-delay@@2026-05-05T00:30:00+00:00"
            ),
            "selected_package_replay_row": True,
            "package_replay_executable_candidate_use_allowed": True,
            "order_policy_action": "limit_first_delay_queue",
        },
        {
            "candidate_id": "candidate-unfilled",
            "decision_time_utc": "2026-05-05T00:45:00+00:00",
            "symbol": "XAUUSD",
            "side": "LONG",
            "canonical_replay_candidate_instance_key": (
                "candidate-unfilled@@2026-05-05T00:45:00+00:00"
            ),
            "selected_package_replay_row": True,
            "package_replay_executable_candidate_use_allowed": True,
        },
        {
            "candidate_id": "candidate-not-selected",
            "decision_time_utc": "2026-05-05T00:50:00+00:00",
            "symbol": "XAUUSD",
            "side": "LONG",
            "canonical_replay_candidate_instance_key": (
                "candidate-not-selected@@2026-05-05T00:50:00+00:00"
            ),
            "selected_package_replay_row": True,
            "package_replay_executable_candidate_use_allowed": True,
            "selected_candidate_ids": [],
        },
        {
            "candidate_id": "candidate-final-missing",
            "decision_time_utc": "2026-05-05T00:55:00+00:00",
            "symbol": "XAUUSD",
            "side": "LONG",
            "canonical_replay_candidate_instance_key": (
                "candidate-final-missing@@2026-05-05T00:55:00+00:00"
            ),
            "selected_package_replay_row": True,
            "package_replay_executable_candidate_use_allowed": True,
            "scheduler_final_selected": True,
        },
        {
            "candidate_id": "candidate-filtered-blocked",
            "decision_time_utc": "2026-05-05T00:56:00+00:00",
            "symbol": "XAUUSD",
            "side": "LONG",
            "canonical_replay_candidate_instance_key": (
                "candidate-filtered-blocked@@2026-05-05T00:56:00+00:00"
            ),
            "selected_package_replay_row": True,
            "package_replay_executable_candidate_use_allowed": True,
            "scheduler_final_selected": True,
        },
        {
            "candidate_id": "candidate-filled-no-trade",
            "decision_time_utc": "2026-05-05T00:56:15+00:00",
            "symbol": "XAUUSD",
            "side": "LONG",
            "canonical_replay_candidate_instance_key": (
                "candidate-filled-no-trade@@2026-05-05T00:56:15+00:00"
            ),
            "selected_package_replay_row": True,
            "package_replay_executable_candidate_use_allowed": True,
            "scheduler_final_selected": True,
        },
        {
            "candidate_id": "candidate-filtered-filled",
            "decision_time_utc": "2026-05-05T00:56:30+00:00",
            "symbol": "XAUUSD",
            "side": "LONG",
            "canonical_replay_candidate_instance_key": (
                "candidate-filtered-filled@@2026-05-05T00:56:30+00:00"
            ),
            "selected_package_replay_row": True,
            "package_replay_executable_candidate_use_allowed": True,
            "scheduler_final_selected": True,
        },
        {
            "candidate_id": "candidate-pre-finalizer",
            "decision_time_utc": "2026-05-05T00:57:00+00:00",
            "symbol": "XAUUSD",
            "side": "LONG",
            "canonical_replay_candidate_instance_key": (
                "candidate-pre-finalizer@@2026-05-05T00:57:00+00:00"
            ),
            "selected_package_replay_row": True,
            "package_replay_executable_candidate_use_allowed": True,
            "scheduler_pre_finalizer_selected": True,
            "selected_candidate_ids": [],
        },
        {
            "candidate_id": "candidate-oracle-diagnostic",
            "decision_time_utc": "2026-05-05T01:00:00+00:00",
            "symbol": "XAUUSD",
            "side": "LONG",
            "canonical_replay_candidate_instance_key": (
                "candidate-oracle-diagnostic@@2026-05-05T01:00:00+00:00"
            ),
            "selected_package_replay_row": True,
            "package_replay_executable_candidate_use_allowed": False,
            "package_replay_executable_candidate_use_allowed_reason": (
                "ultimate_package_effective_source_bound_not_allowed"
            ),
        },
        {
            "candidate_id": "candidate-invalid-trade",
            "decision_time_utc": "2026-05-05T01:15:00+00:00",
            "symbol": "XAUUSD",
            "side": "LONG",
            "canonical_replay_candidate_instance_key": (
                "candidate-invalid-trade@@2026-05-05T01:15:00+00:00"
            ),
            "selected_package_replay_row": True,
            "package_replay_executable_candidate_use_allowed": False,
            "package_replay_executable_candidate_use_allowed_reason": (
                "ultimate_package_effective_source_bound_not_allowed"
            ),
        },
    ]
    order_rows = [
        {
            "candidate_id": "candidate-unfilled",
            "canonical_replay_candidate_instance_key": (
                "candidate-unfilled@@2026-05-05T00:45:00+00:00"
            ),
            "order_status": "expired_unfilled",
        },
        {
            "candidate_id": "candidate-filled-no-trade",
            "canonical_replay_candidate_instance_key": (
                "candidate-filled-no-trade@@2026-05-05T00:56:15+00:00"
            ),
            "order_status": "filled",
        }
    ]
    oracle_rows = [
        {
            "candidate_id": "candidate-unfilled",
            "canonical_replay_candidate_instance_key": (
                "candidate-unfilled@@2026-05-05T00:45:00+00:00"
            ),
            "fill_status": "not_filled_expired_unfilled",
        },
        {
            "candidate_id": "candidate-filled-no-trade",
            "canonical_replay_candidate_instance_key": (
                "candidate-filled-no-trade@@2026-05-05T00:56:15+00:00"
            ),
            "fill_status": "filled_from_ordered_m1_path",
        },
        {
            "candidate_id": "candidate-oracle-diagnostic",
            "canonical_replay_candidate_instance_key": (
                "candidate-oracle-diagnostic@@2026-05-05T01:00:00+00:00"
            ),
            "fill_status": "filled_from_ordered_m1_path",
        }
    ]
    trade_rows = [
        {
            "candidate_id": "candidate-invalid-trade",
            "canonical_replay_candidate_instance_key": (
                "candidate-invalid-trade@@2026-05-05T01:15:00+00:00"
            ),
            "simulated_trade_id": "trade-invalid",
        }
    ]
    filtered_non_executable_order_rows = [
        {
            "candidate_id": "candidate-filtered-blocked",
            "canonical_replay_candidate_instance_key": (
                "candidate-filtered-blocked@@2026-05-05T00:56:00+00:00"
            ),
            "order_status": "risk_rejected",
            "selected_package_non_executable_order_trade_reason": (
                "source_required_fail_closed_lifecycle_source_gap_diagnostic_only"
            ),
        },
        {
            "candidate_id": "candidate-filtered-filled",
            "canonical_replay_candidate_instance_key": (
                "candidate-filtered-filled@@2026-05-05T00:56:30+00:00"
            ),
            "order_status": "filled",
            "selected_package_non_executable_order_trade_reason": (
                "ultimate_package_effective_source_bound_not_allowed"
            ),
        },
    ]
    filtered_non_executable_trade_rows = [
        {
            "candidate_id": "candidate-filtered-filled",
            "canonical_replay_candidate_instance_key": (
                "candidate-filtered-filled@@2026-05-05T00:56:30+00:00"
            ),
            "simulated_trade_id": "filtered-trade",
            "fill_status": "filled",
            "selected_package_non_executable_order_trade_reason": (
                "ultimate_package_effective_source_bound_not_allowed"
            ),
        }
    ]

    rows = bridge.build_selected_package_execution_disposition_rows(
        compact_rows=compact_rows,
        order_rows=order_rows,
        oracle_rows=oracle_rows,
        trade_rows=trade_rows,
        filtered_non_executable_order_rows=filtered_non_executable_order_rows,
        filtered_non_executable_trade_rows=filtered_non_executable_trade_rows,
    )
    by_id = {row["candidate_id"]: row for row in rows}

    assert by_id["candidate-skip"]["execution_disposition"] == (
        "non_executable_scheduler_skip"
    )
    assert by_id["candidate-skip"]["timeframe"] == "M15"
    assert by_id["candidate-skip"]["same_symbol_replay_exposure_context"][
        "same_side_pending_ids"
    ] == ["pending-skip"]
    assert (
        by_id["candidate-skip"]["canonical_replay_context_projection_status"]
        == "materialized"
    )
    assert by_id["candidate-skip"]["replacement_reallocation_quality_score"] == 0.61
    assert (
        by_id["candidate-skip"]["ultimate_package_effective_source_bound_signal_r"]
        == 0.0
    )
    assert (
        by_id["candidate-skip"][
            "diagnostic_ultimate_package_effective_source_bound_signal_r"
        ]
        == 7.0
    )
    assert (
        by_id["candidate-skip"]["ultimate_package_effective_source_bound_non_executable"]
        is True
    )
    assert (
        by_id["candidate-skip"]["ultimate_package_effective_executable_authority_allowed"]
        is False
    )
    assert by_id["candidate-delay"]["execution_disposition"] == (
        "deferred_limit_first_delay_queue_not_ordered"
    )
    assert by_id["candidate-unfilled"]["execution_disposition"] == (
        "ordered_unfilled_no_trade"
    )
    assert by_id["candidate-filled-no-trade"]["execution_disposition"] == (
        "filled_order_or_oracle_without_trade_row"
    )
    assert by_id["candidate-not-selected"]["execution_disposition"] == (
        "executable_package_candidate_not_scheduler_selected"
    )
    assert by_id["candidate-final-missing"]["execution_disposition"] == (
        "executable_scheduler_final_selected_missing_order_binding"
    )
    assert by_id["candidate-filtered-blocked"]["execution_disposition"] == (
        "filtered_non_executable_terminal_blocked_no_trade"
    )
    assert by_id["candidate-filtered-filled"]["execution_disposition"] == (
        "filtered_non_executable_terminal_filled_diagnostic"
    )
    assert by_id["candidate-pre-finalizer"]["execution_disposition"] == (
        "executable_pre_finalizer_selected_not_risk_final_selected"
    )
    assert by_id["candidate-oracle-diagnostic"]["execution_disposition"] == (
        "non_executable_path_oracle_diagnostic"
    )
    assert by_id["candidate-invalid-trade"]["execution_disposition"] == (
        "invalid_non_executable_bound_execution"
    )
    summary = bridge.summarize_selected_package_execution_dispositions(rows)
    assert summary["selected_package_execution_disposition_rows"] == 11
    assert (
        summary["selected_package_execution_disposition_ordered_unfilled_rows"] == 1
    )
    assert (
        summary[
            "selected_package_execution_disposition_filtered_terminal_blocked_rows"
        ]
        == 1
    )
    assert (
        summary[
            "selected_package_execution_disposition_filtered_terminal_filled_diagnostic_rows"
        ]
        == 1
    )
    assert (
        summary[
            "selected_package_execution_disposition_not_scheduler_selected_rows"
        ]
        == 2
    )
    assert (
        summary[
            "selected_package_execution_disposition_missing_order_binding_rows"
        ]
        == 1
    )
    assert summary["selected_package_execution_disposition_non_executable_rows"] == 5
    assert summary["selected_package_execution_disposition_invalid_rows"] == 3


def test_selected_package_bridge_backfills_order_trade_path_provenance_from_oracle() -> None:
    bridge = load_selected_package_replay_bridge()

    oracle_rows = [
        {
            "candidate_id": "candidate-path",
            "decision_time_utc": "2026-05-05T00:45:00+00:00",
            "canonical_replay_candidate_instance_key": (
                "candidate-path@@2026-05-05T00:45:00+00:00"
            ),
            "simulated_order_id": "order-path",
            "simulated_trade_id": "trade-path",
            "source": "m1",
            "path_index_timeframe": "M1",
            "path_index_source_path": "/tmp/XAUUSD_M1.csv",
            "path_index_source_sha256": "fixture-sha",
            "path_row_count": 17,
            "ordered_tick_truth_satisfied": False,
            "postdecision_path_proxy": True,
            "postdecision_path_proxy_reason": "m1_path_proxy_no_ordered_tick_export",
            "terminal_r_path_authority": "proxy_replay_not_final_live_proof",
        }
    ]

    order_rows = bridge.backfill_order_trade_path_provenance_from_oracles(
        [
            {
                "candidate_id": "candidate-path",
                "decision_time_utc": "2026-05-05T00:45:00+00:00",
                "canonical_replay_candidate_instance_key": (
                    "candidate-path@@2026-05-05T00:45:00+00:00"
                ),
                "simulated_order_id": "order-path",
                "order_status": "filled",
            }
        ],
        oracle_rows,
        row_type="order",
    )
    trade_rows = bridge.backfill_order_trade_path_provenance_from_oracles(
        [
            {
                "candidate_id": "candidate-path",
                "decision_time_utc": "2026-05-05T00:45:00+00:00",
                "canonical_replay_candidate_instance_key": (
                    "candidate-path@@2026-05-05T00:45:00+00:00"
                ),
                "simulated_trade_id": "trade-path",
            }
        ],
        oracle_rows,
        row_type="trade",
    )

    for row, expected_type in ((order_rows[0], "order"), (trade_rows[0], "trade")):
        assert row["path_source"] == "m1"
        assert row["path_index_timeframe"] == "M1"
        assert row["path_index_source_sha256"] == "fixture-sha"
        assert row["path_row_count"] == 17
        assert row["ordered_tick_truth_satisfied"] is False
        assert row["postdecision_path_proxy"] is True
        assert row["terminal_r_path_authority"] == "proxy_replay_not_final_live_proof"
        assert row["path_provenance_backfilled_from_oracle"] is True
        assert row["path_provenance_backfill_row_type"] == expected_type
        assert "path_source" in row["path_provenance_backfilled_fields"]


def test_selected_package_bridge_scorecard_scrubs_no_selected_authority() -> None:
    bridge = load_selected_package_replay_bridge()

    rows = bridge.decorate_rows(
        [
            {
                "selected_candidate_ids": [],
                "package_replay_executable_candidate_use_allowed": True,
                "canonical_replay_candidate_instance_key": (
                    "candidate@@2026-05-05T00:15:00+00:00"
                ),
                "candidate_instance_identity_status": "materialized",
            }
        ],
        row_type="scorecard",
    )

    row = rows[0]
    assert row["source_boundary"] == (
        "predecision_scheduler_window_no_selected_candidate_no_outcome_fields"
    )
    assert row["candidate_decision_quality_source_boundary"] == (
        "predecision_scheduler_window_no_selected_candidate_no_outcome_fields"
    )
    assert row["package_replay_executable_candidate_use_allowed"] is None
    assert row["canonical_replay_candidate_instance_key"] is None
    assert row["candidate_instance_identity_status"] is None
    assert row["scorecard_reported_package_replay_executable_candidate_use_allowed"] is True
    assert row["scorecard_no_final_selection_candidate_authority_scrubbed"] is True


def test_selected_package_bridge_order_trade_flattens_joined_package_contract() -> None:
    bridge = load_selected_package_replay_bridge()
    instance_key = "candidate-package@@2026-05-05T00:15:00+00:00"
    candidate_status = {
        "candidate_id": "candidate-package",
        "decision_time_utc": "2026-05-05T00:15:00+00:00",
        "canonical_replay_candidate_instance_key": instance_key,
        "timeframe": "M15",
        "same_symbol_replay_exposure_context": {
            "symbol": "XAUUSD",
            "side": "LONG",
            "same_side_pending_ids": ["pending-package"],
            "same_side_pending_order_ids": ["pending-package"],
        },
        "canonical_replay_context_projection_status": "materialized",
        "replacement_reallocation_quality_score": 0.71,
        "source_bound_package_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed": True,
        "ultimate_candidate_package_packet_hash_sha256": "packet-hash",
        "ultimate_candidate_package_packet_shape_hash_sha256": "shape-hash",
        "package_new_entry_authority_valid": True,
        "package_new_entry_authority_hash_sha256": "authority-hash",
        "package_new_entry_authority_target_action_intent": "new_position",
        "entry_price": 100.0,
        "stop_loss": 99.0,
        "take_profit_1": 102.0,
        "target_reference": 102.0,
        "risk_reward_ratio": 2.0,
    }

    rows = bridge.decorate_rows(
        [
            {
                "candidate_id": "candidate-package",
                "decision_time_utc": "2026-05-05T00:15:00+00:00",
                "canonical_replay_candidate_instance_key": instance_key,
                "order_status": "filled",
                "entry_price": 100.0,
                "stop_loss": 99.0,
                "take_profit_1": 102.0,
                "target_reference": 102.0,
                "risk_reward_ratio": 2.0,
            }
        ],
        row_type="order",
        candidate_status_by_id={instance_key: candidate_status},
    )

    row = rows[0]
    assert row["selected_package_candidate_status_joined"] is True
    assert row["ultimate_candidate_package_packet_hash_sha256"] == "packet-hash"
    assert row["ultimate_candidate_package_packet_shape_hash_sha256"] == "shape-hash"
    assert row["package_new_entry_authority_valid"] is True
    assert row["package_new_entry_authority_hash_sha256"] == "authority-hash"
    assert row["timeframe"] == "M15"
    assert row["same_symbol_replay_exposure_context"]["same_side_pending_ids"] == [
        "pending-package"
    ]
    assert row["canonical_replay_context_projection_status"] == "materialized"
    assert row["replacement_reallocation_quality_score"] == 0.71


def test_profit_harvest_blocker_uses_exact_candidate_time_trade_instance() -> None:
    bridge = load_selected_package_replay_bridge()

    rows = bridge.build_profit_harvest_authority_blocker_rows(
        oracles=[
            {
                "candidate_id": "candidate:reused",
                "symbol": "XAUUSD",
                "side": "LONG",
                "decision_time_utc": "2026-05-06T09:15:00+00:00",
                "expected_cost_r": 0.10,
                "profit_harvest_mfe_capture_replay_exit_final_r_authority": False,
                "profit_harvest_mfe_capture_replay_exit_diagnostic": {
                    "diagnostic_policy_gross_r": 1.50,
                    "diagnostic_policy_close_reason": "target_touch",
                },
            }
        ],
        trades=[
            {
                "candidate_id": "candidate:reused",
                "symbol": "XAUUSD",
                "side": "LONG",
                "decision_time_utc": "2026-05-06T09:15:00+00:00",
                "net_proxy_r": 0.75,
                "gross_r": 0.85,
                "expected_cost_r": 0.10,
                "exit_time_utc": "2026-05-06T10:00:00+00:00",
            },
            {
                "candidate_id": "candidate:reused",
                "symbol": "XAUUSD",
                "side": "SHORT",
                "decision_time_utc": "2026-05-06T08:45:00+00:00",
                "net_proxy_r": -1.25,
                "gross_r": -1.15,
                "expected_cost_r": 0.10,
                "exit_time_utc": "2026-05-06T09:30:00+00:00",
            },
        ],
    )

    assert len(rows) == 1
    row = rows[0]
    assert row["profit_harvest_trade_join_status"] == "exact_candidate_time_trade_join"
    assert row["profit_harvest_trade_join_key"] == (
        "candidate:reused@@2026-05-06T09:15:00+00:00"
    )
    assert row["profit_harvest_trade_join_candidate_id_trade_count"] == 2
    assert row["actual_net_r"] == 0.75
    assert row["side"] == "LONG"
    assert row["profit_harvest_authority_blocker_status"] == (
        "profit_harvest_diagnostic_needs_ordered_tick"
    )


def test_profit_harvest_blocker_marks_m1_proxy_ordered_tick_requirement() -> None:
    bridge = load_selected_package_replay_bridge()

    rows = bridge.build_profit_harvest_authority_blocker_rows(
        oracles=[
            {
                "candidate_id": "candidate:m1-proxy",
                "symbol": "XAUUSD",
                "side": "LONG",
                "decision_time_utc": "2026-05-06T09:15:00+00:00",
                "expected_cost_r": 0.10,
                "profit_harvest_mfe_capture_replay_exit_final_r_authority": False,
                "profit_harvest_mfe_capture_replay_exit_final_r_authority_status": (
                    "m1_ordered_path_proxy_replay_not_terminal_final_r_authority"
                ),
                "profit_harvest_mfe_capture_replay_exit_m1_proxy_replay_authority": True,
                "profit_harvest_mfe_capture_replay_exit_diagnostic": {
                    "status": "diagnostic",
                    "m1_proxy_replay_authority": True,
                    "m1_proxy_policy_gross_r": 1.50,
                    "diagnostic_policy_close_reason": "proxy_trailing_stop",
                },
            }
        ],
        trades=[
            {
                "candidate_id": "candidate:m1-proxy",
                "symbol": "XAUUSD",
                "side": "LONG",
                "decision_time_utc": "2026-05-06T09:15:00+00:00",
                "net_proxy_r": -0.20,
                "gross_r": -0.10,
                "expected_cost_r": 0.10,
            }
        ],
    )

    assert len(rows) == 1
    row = rows[0]
    assert row["profit_harvest_trade_join_status"] == "exact_candidate_time_trade_join"
    assert row["m1_proxy_replay_authority"] is True
    assert row["ordered_tick_final_r_authority"] is False
    assert row["headline_result_authority"] is False
    assert row["legacy_final_r_authority"] is False
    assert row["m1_proxy_policy_gross_r"] == 1.5
    assert row["m1_proxy_policy_net_r"] == 1.4
    assert row["blocker_type"] == "m1_proxy_ordered_tick_proof_required"
    assert row["ordered_tick_proof_required"] is True
    assert row["ordered_tick_proof_required_reason"] == (
        "m1_proxy_replay_authority_not_terminal_headline_final_r"
    )


def test_profit_harvest_blocker_fails_closed_when_timed_trade_instance_missing() -> None:
    bridge = load_selected_package_replay_bridge()

    rows = bridge.build_profit_harvest_authority_blocker_rows(
        oracles=[
            {
                "candidate_id": "candidate:timed-miss",
                "symbol": "GBPJPY",
                "side": "SHORT",
                "decision_time_utc": "2026-05-06T09:15:00+00:00",
                "expected_cost_r": 0.12,
                "profit_harvest_mfe_capture_replay_exit_final_r_authority": False,
                "profit_harvest_mfe_capture_replay_exit_diagnostic": {
                    "diagnostic_policy_gross_r": 1.40,
                    "diagnostic_policy_close_reason": "target_touch",
                },
            }
        ],
        trades=[
            {
                "candidate_id": "candidate:timed-miss",
                "symbol": "GBPJPY",
                "side": "SHORT",
                "decision_time_utc": "2026-05-06T08:45:00+00:00",
                "net_proxy_r": -1.0,
                "gross_r": -0.88,
                "expected_cost_r": 0.12,
            }
        ],
    )

    assert len(rows) == 1
    row = rows[0]
    assert row["profit_harvest_trade_join_status"] == (
        "profit_harvest_trade_join_exact_missing"
    )
    assert row["profit_harvest_trade_join_key"] == (
        "candidate:timed-miss@@2026-05-06T09:15:00+00:00"
    )
    assert row["profit_harvest_trade_join_candidate_id_trade_count"] == 1
    assert row["actual_net_r"] is None
    assert row["profit_harvest_authority_blocker_status"] == (
        "profit_harvest_diagnostic_needs_ordered_tick"
    )


def test_profit_harvest_blocker_does_not_use_candidate_id_when_decision_time_missing() -> None:
    bridge = load_selected_package_replay_bridge()

    rows = bridge.build_profit_harvest_authority_blocker_rows(
        oracles=[
            {
                "candidate_id": "candidate:no-time",
                "symbol": "XAUUSD",
                "side": "LONG",
                "expected_cost_r": 0.10,
                "profit_harvest_mfe_capture_replay_exit_final_r_authority": False,
                "profit_harvest_mfe_capture_replay_exit_diagnostic": {
                    "diagnostic_policy_gross_r": 1.25,
                    "diagnostic_policy_close_reason": "target_touch",
                },
            }
        ],
        trades=[
            {
                "candidate_id": "candidate:no-time",
                "symbol": "XAUUSD",
                "side": "LONG",
                "decision_time_utc": "2026-05-06T09:15:00+00:00",
                "net_proxy_r": 0.80,
                "gross_r": 0.90,
                "expected_cost_r": 0.10,
            }
        ],
    )

    assert len(rows) == 1
    row = rows[0]
    assert row["profit_harvest_trade_join_status"] == (
        "profit_harvest_trade_join_decision_time_missing_no_trade_join"
    )
    assert row["profit_harvest_trade_join_key"] is None
    assert row["profit_harvest_trade_join_candidate_id_trade_count"] == 1
    assert row["actual_net_r"] is None
