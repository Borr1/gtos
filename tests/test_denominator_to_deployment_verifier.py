from __future__ import annotations

import importlib.util
import copy
import hashlib
import json
from types import SimpleNamespace
from pathlib import Path

import pytest

from src.components.poi_execution_lifecycle import (
    build_causal_poi_lifecycle_envelope,
)
from src.components.poi_state_contract import finalize_poi_state, stable_poi_id
from src.research.moonshot_scheduler_v4_best_trade_allocator import (
    PACKAGE_NEW_ENTRY_AUTHORITY_IMMUTABLE_PAYLOAD_CONTRACT,
    PACKAGE_NEW_ENTRY_AUTHORITY_PAYLOAD_SCHEMA,
    package_new_entry_authority_payload_hash_sha256,
)


ROOT = Path(__file__).resolve().parents[1]
VERIFIER_PATH = (
    ROOT
    / "research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20"
    / "verify_denominator_to_deployment_execution.py"
)
AUDIT_PATH = (
    ROOT
    / "research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20"
    / "audit_provenance_and_flags_v114.py"
)
BUILDER_PATH = (
    ROOT
    / "research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20"
    / "build_denominator_to_deployment_execution.py"
)
PARITY_BUILDER_PATH = (
    ROOT
    / "research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20"
    / "build_source_bound_execution_parity.py"
)
BRIDGE_PATH = (
    ROOT
    / "research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20"
    / "run_selected_package_replay_bridge.py"
)
EXPECTED_EFFECTIVE_ORDER_EXECUTABLE_DEMOTION_FIELDS = (
    "package_replay_candidate_use_allowed",
    "package_replay_executable_candidate_use_allowed",
    "package_replay_order_executable_candidate_use_allowed",
    "replay_candidate_use_allowed_now",
    "ultimate_package_effective_executable_authority_allowed",
    "finalizer_primary_probe_executable_finalized",
    "risk_finalizer_executable_finalized",
    "executable_finalized",
    "missed_row_executable_finalized",
    "selected_scheduler_package_replay_executable_candidate_use_allowed",
    "selected_scheduler_package_replay_order_executable_candidate_use_allowed",
    "scheduler_option_package_replay_executable_candidate_use_allowed",
    "scheduler_option_package_replay_order_executable_candidate_use_allowed",
    "risk_finalizer_package_replay_executable_candidate_use_allowed",
    "risk_finalizer_package_replay_order_executable_candidate_use_allowed",
    "finalizer_primary_probe_package_replay_executable_candidate_use_allowed",
    "scorecard_reported_package_replay_order_executable_candidate_use_allowed",
    "finalizer_primary_probe_package_replay_order_executable_candidate_use_allowed",
    "risk_finalizer_best_package_probe_package_replay_order_executable_candidate_use_allowed",
)


def load_verifier():
    spec = importlib.util.spec_from_file_location(
        "verify_denominator_to_deployment_execution", VERIFIER_PATH
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_audit():
    spec = importlib.util.spec_from_file_location(
        "audit_provenance_and_flags_v114", AUDIT_PATH
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_builder():
    spec = importlib.util.spec_from_file_location(
        "build_denominator_to_deployment_execution", BUILDER_PATH
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_parity_builder():
    spec = importlib.util.spec_from_file_location(
        "build_source_bound_execution_parity", PARITY_BUILDER_PATH
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_bridge():
    spec = importlib.util.spec_from_file_location(
        "run_selected_package_replay_bridge", BRIDGE_PATH
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _verifier_unit_poi_state() -> dict:
    source_times = [
        "2026-05-14T00:00:00+00:00",
        "2026-05-14T00:15:00+00:00",
        "2026-05-14T00:30:00+00:00",
    ]
    return finalize_poi_state(
        {
            "poi_id": stable_poi_id(
                symbol="US30_CASH",
                timeframe="M15",
                poi_type="fair_value_gap",
                direction="bullish",
                source_candle_times=source_times,
                zone_low=42000.0,
                zone_high=42010.0,
            ),
            "poi_type": "fair_value_gap",
            "poi_timeframe": "M15",
            "poi_direction": "bullish",
            "poi_zone_low": 42000.0,
            "poi_zone_high": 42010.0,
            "poi_source_candle_times": source_times,
            "poi_created_at_utc": "2026-05-14T00:45:00+00:00",
            "poi_state_asof_utc": "2026-05-14T01:00:00+00:00",
            "poi_age_hours": 0.25,
            "poi_touch_count": 0,
            "poi_first_touch_time_utc": "",
            "poi_last_touch_time_utc": "",
            "poi_mitigation_status": "untouched",
            "poi_filled": False,
            "poi_invalidated": False,
            "poi_invalidation_time_utc": "",
            "poi_invalidation_reason": "",
            "poi_state_uses_outcome_fields": False,
        }
    )


def _verifier_poi_scan_fixture() -> dict[str, list[dict]]:
    state = _verifier_unit_poi_state()
    candidate_id = "current-fvg-logical-candidate"
    decision_time = "2026-05-14T01:00:00+00:00"
    instance_key = f"{candidate_id}@@{decision_time}"
    lifecycle = build_causal_poi_lifecycle_envelope(
        poi_state=state,
        decision_time_utc=decision_time,
        fillability={
            "fill_probability": 0.80,
            "current_price_source_time_utc": "2026-05-14T00:45:00+00:00",
            "source_boundary": "closed_m15_predecision_asof_no_postdecision_path",
        },
        distance_to_zone_price=0.0,
        distance_to_zone_atr=0.0,
        distance_to_midpoint_price=0.0,
        distance_to_midpoint_atr=0.0,
        scheduler_readiness_floor=0.45,
        scheduler_readiness_policy_source="test_floor",
        scheduler_readiness_policy_hash_sha256="a" * 64,
    )
    payload = {
        "payload_schema": PACKAGE_NEW_ENTRY_AUTHORITY_PAYLOAD_SCHEMA,
        "payload_contract": PACKAGE_NEW_ENTRY_AUTHORITY_IMMUTABLE_PAYLOAD_CONTRACT,
        "candidate_id": candidate_id,
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": instance_key,
        "poi_state_required": True,
        "poi_state": state,
        "poi_id": state["poi_id"],
        "poi_state_hash_sha256": state["poi_state_hash_sha256"],
        "causal_poi_lifecycle_required": True,
        "causal_poi_lifecycle": lifecycle,
        "causal_poi_lifecycle_hash_sha256": lifecycle[
            "lifecycle_hash_sha256"
        ],
        "poi_scheduler_rankable_now": True,
        "poi_execution_allowed_by_lifecycle": True,
    }
    stage_row = {
        "candidate_id": candidate_id,
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": instance_key,
        "origin_family": "current_fvg_fill",
        "current_framework": "fvg_fill",
        "poi_state_required": True,
        "poi_state": state,
        "poi_id": state["poi_id"],
        "poi_state_hash_sha256": state["poi_state_hash_sha256"],
        "causal_poi_lifecycle_required": True,
        "causal_poi_lifecycle": lifecycle,
        "causal_poi_lifecycle_hash_sha256": lifecycle[
            "lifecycle_hash_sha256"
        ],
        "poi_scheduler_rankable_now": True,
        "poi_execution_allowed_by_lifecycle": True,
        "package_new_entry_authority_payload": payload,
    }
    partition = {
        "schema": "gtos.current_fvg_poi_generation_partition.v1",
        "source_boundary": state["poi_state_source_boundary"],
        "uses_outcome_fields": False,
        "source_poi_instance_count": 1,
        "considered_poi_count": 1,
        "emitted_poi_count": 1,
        "denied_poi_count": 0,
        "partition_reconciled": True,
        "disposition_counts": {"emitted_executable": 1},
        "rows": [
            {
                "source_poi_index": 0,
                "poi_id": state["poi_id"],
                "poi_state_hash_sha256": state["poi_state_hash_sha256"],
                "candidate_id": candidate_id,
                "decision_time_utc": decision_time,
                "disposition": "emitted_executable",
                "reason": "fvg_poi_state_valid_and_within_proximity",
                "causal_poi_lifecycle": lifecycle,
                "causal_poi_lifecycle_hash_sha256": lifecycle[
                    "lifecycle_hash_sha256"
                ],
                "poi_scheduler_rankable_now": True,
                "uses_outcome_fields": False,
            }
        ],
    }
    return {
        "source_universe": [{"row_type": "source_scope"}],
        "decision": [
            {
                "decision_time_utc": decision_time,
                "candidate_generation_audit": {
                    "producer_generation_audit": {
                        "status": "candidate_generation_complete"
                    }
                },
                "current_fvg_poi_generation": partition,
            }
        ],
        "candidate": [dict(stage_row)],
        "scorecard": [dict(stage_row)],
        "order": [dict(stage_row)],
        "trade": [dict(stage_row)],
        "missed": [dict(stage_row)],
    }


def test_broad_poi_state_contract_path_map_includes_decision_generation_ledger() -> None:
    verifier = load_verifier()
    paths = _verifier_poi_scan_fixture()
    candidate_path = [{"candidate_id": "candidate-index-row"}]

    mapped = verifier.broad_poi_state_contract_paths(
        paths,
        candidate_path=candidate_path,
    )

    assert tuple(mapped) == (
        "source_universe",
        "decision",
        "candidate",
        "scorecard",
        "order",
        "trade",
        "missed",
    )
    assert mapped["decision"] is paths["decision"]
    assert mapped["candidate"] is candidate_path


def test_order_executable_verifier_accepts_shared_canonical_blocker_families() -> None:
    verifier = load_verifier()

    assert {
        "source_or_signature_authority",
        "poi_lifecycle_terminal",
        "session_authority",
        "execution_fillability",
        "risk_safety",
        "order_lifecycle",
    }.issubset(verifier.ORDER_EXECUTABLE_TRANSFER_ALLOWED_BLOCKERS)


def test_broad_poi_state_contract_accepts_exact_causal_lineage() -> None:
    verifier = load_verifier()

    scan = verifier.scan_broad_poi_state_contract(_verifier_poi_scan_fixture())

    assert scan["bad_counts"] == {}
    assert scan["poi_identity_counts"] == {
        "unique_poi_ids": 1,
        "unique_logical_candidate_ids": 1,
        "unique_candidate_instances": 1,
    }
    assert scan["row_counts"]["poi_generation_considered_rows"] == 1
    assert scan["row_counts"]["candidate_causal_poi_lifecycle_rows"] == 1
    assert scan["row_counts"]["missed_causal_poi_lifecycle_rows"] == 1


def test_broad_poi_state_contract_counts_compact_projection_rows() -> None:
    verifier = load_verifier()
    paths = _verifier_poi_scan_fixture()
    decision = paths["decision"][0]
    partition = decision["current_fvg_poi_generation"]
    decision.update(
        {
            "compact_decision_projection_schema": (
                "gtos.final_moonshot.broad_replay.compact_decision_projection.v1"
            ),
            "current_fvg_poi_generation_projection_status": (
                "canonical_top_level_preserved_no_nested_alias"
            ),
            "current_fvg_poi_generation_projection_sha256": (
                verifier.stable_projection_sha256(partition)
            ),
        }
    )
    scorecard = paths["scorecard"][0]
    trace = [{"candidate_id": scorecard["candidate_id"]}]
    scorecard.update(
        {
            "compact_scorecard_projection_schema": (
                "gtos.final_moonshot.broad_replay.compact_scorecard_projection.v1"
            ),
            "scheduler_option_trace_projection_status": (
                "canonical_trace_preserved_no_aliases_present"
            ),
            "scheduler_option_trace_omitted_duplicate_aliases": [],
            "scheduler_option_trace": trace,
            "scheduler_option_trace_projection_sha256": (
                verifier.stable_projection_sha256(trace)
            ),
        }
    )

    scan = verifier.scan_broad_poi_state_contract(paths)

    assert scan["bad_counts"] == {}
    assert scan["row_counts"]["decision_compact_projection_eligible_rows"] == 1
    assert scan["row_counts"]["decision_compact_projection_rows"] == 1
    assert scan["row_counts"]["scorecard_compact_projection_eligible_rows"] == 1
    assert scan["row_counts"]["scorecard_compact_projection_rows"] == 1


def test_broad_poi_state_contract_joins_outer_instance_and_preserves_source_time() -> None:
    verifier = load_verifier()
    paths = _verifier_poi_scan_fixture()
    disposition = paths["decision"][0]["current_fvg_poi_generation"]["rows"][0]
    disposition["candidate_generation_source_time_utc"] = (
        "2026-05-14T00:45:00+00:00"
    )
    disposition["candidate_instance_time_utc"] = (
        paths["decision"][0]["decision_time_utc"]
    )
    disposition["canonical_replay_candidate_instance_key"] = (
        f"{disposition['candidate_id']}@@{paths['decision'][0]['decision_time_utc']}"
    )

    scan = verifier.scan_broad_poi_state_contract(paths)

    assert scan["bad_counts"] == {}
    assert scan["row_counts"]["poi_generation_explicit_source_time_rows"] == 1


def test_broad_poi_state_contract_rejects_future_generation_source_time() -> None:
    verifier = load_verifier()
    paths = _verifier_poi_scan_fixture()
    disposition = paths["decision"][0]["current_fvg_poi_generation"]["rows"][0]
    disposition["candidate_generation_source_time_utc"] = (
        "2026-05-14T01:15:00+00:00"
    )
    disposition["candidate_instance_time_utc"] = (
        paths["decision"][0]["decision_time_utc"]
    )

    scan = verifier.scan_broad_poi_state_contract(paths)

    assert scan["bad_counts"][
        "decision:candidate_generation_source_time_after_replay_decision"
    ] == 1


def test_broad_poi_state_contract_rejects_independent_source_index_drift() -> None:
    verifier = load_verifier()
    paths = _verifier_poi_scan_fixture()
    partition = paths["decision"][0]["current_fvg_poi_generation"]
    partition["source_poi_instance_count"] = 2
    partition["rows"][0]["source_poi_index"] = 3

    scan = verifier.scan_broad_poi_state_contract(paths)

    assert scan["bad_counts"][
        "decision:source_poi_instance_count_mismatch"
    ] == 1
    assert scan["bad_counts"]["decision:source_poi_index_coverage_mismatch"] == 1


def test_broad_poi_state_contract_requires_dormant_candidate_missed_accounting() -> None:
    verifier = load_verifier()
    paths = _verifier_poi_scan_fixture()
    state = paths["candidate"][0]["poi_state"]
    decision_time = paths["candidate"][0]["decision_time_utc"]
    dormant_lifecycle = build_causal_poi_lifecycle_envelope(
        poi_state=state,
        decision_time_utc=decision_time,
        fillability={
            "fill_probability": 0.10,
            "current_price_source_time_utc": "2026-05-14T00:45:00+00:00",
            "source_boundary": "closed_m15_predecision_asof_no_postdecision_path",
        },
        distance_to_zone_price=10.0,
        distance_to_zone_atr=10.0,
        distance_to_midpoint_price=10.0,
        distance_to_midpoint_atr=10.0,
        scheduler_readiness_floor=0.45,
        scheduler_readiness_policy_source="test_floor",
        scheduler_readiness_policy_hash_sha256="a" * 64,
    )

    def apply_dormant_lifecycle(row: dict) -> None:
        row["causal_poi_lifecycle"] = dormant_lifecycle
        row["causal_poi_lifecycle_hash_sha256"] = dormant_lifecycle[
            "lifecycle_hash_sha256"
        ]
        row["poi_scheduler_rankable_now"] = False
        row["poi_execution_allowed_by_lifecycle"] = False
        payload = row["package_new_entry_authority_payload"]
        payload["causal_poi_lifecycle"] = dormant_lifecycle
        payload["causal_poi_lifecycle_hash_sha256"] = dormant_lifecycle[
            "lifecycle_hash_sha256"
        ]
        payload["poi_scheduler_rankable_now"] = False
        payload["poi_execution_allowed_by_lifecycle"] = False

    apply_dormant_lifecycle(paths["candidate"][0])
    apply_dormant_lifecycle(paths["scorecard"][0])
    disposition = paths["decision"][0]["current_fvg_poi_generation"]["rows"][0]
    disposition.update(
        {
            "disposition": "emitted_diagnostic_not_scheduler_ready",
            "reason": "execution_fillability_below_poi_scheduler_readiness_floor",
            "causal_poi_lifecycle": dormant_lifecycle,
            "causal_poi_lifecycle_hash_sha256": dormant_lifecycle[
                "lifecycle_hash_sha256"
            ],
            "poi_scheduler_rankable_now": False,
        }
    )
    paths["decision"][0]["current_fvg_poi_generation"]["disposition_counts"] = {
        "emitted_diagnostic_not_scheduler_ready": 1
    }
    for stage in ("order", "trade", "missed"):
        placeholder_id = f"non-poi-{stage}"
        paths[stage] = [
            {
                "candidate_id": placeholder_id,
                "decision_time_utc": decision_time,
                "canonical_replay_candidate_instance_key": (
                    f"{placeholder_id}@@{decision_time}"
                ),
                "origin_family": "current_ob_retest",
                "framework": "ob_retest",
            }
        ]

    scan = verifier.scan_broad_poi_state_contract(paths)

    assert scan["bad_counts"][
        "cross_stage:nonrankable_poi_candidate_missing_missed_disposition"
    ] == 1


def test_broad_poi_state_contract_rejects_generic_dormant_missed_blocker() -> None:
    verifier = load_verifier()
    paths = _verifier_poi_scan_fixture()
    missed = paths["missed"][0]
    dormant_lifecycle = build_causal_poi_lifecycle_envelope(
        poi_state=missed["poi_state"],
        decision_time_utc=missed["decision_time_utc"],
        fillability={
            "fill_probability": 0.10,
            "current_price_source_time_utc": "2026-05-14T00:45:00+00:00",
            "source_boundary": "closed_m15_predecision_asof_no_postdecision_path",
        },
        distance_to_zone_price=10.0,
        distance_to_zone_atr=10.0,
        distance_to_midpoint_price=10.0,
        distance_to_midpoint_atr=10.0,
        scheduler_readiness_floor=0.45,
        scheduler_readiness_policy_source="test_floor",
        scheduler_readiness_policy_hash_sha256="a" * 64,
    )
    missed["causal_poi_lifecycle"] = dormant_lifecycle
    missed["causal_poi_lifecycle_hash_sha256"] = dormant_lifecycle[
        "lifecycle_hash_sha256"
    ]
    missed["poi_scheduler_rankable_now"] = False
    payload = missed["package_new_entry_authority_payload"]
    payload["causal_poi_lifecycle"] = dormant_lifecycle
    payload["causal_poi_lifecycle_hash_sha256"] = dormant_lifecycle[
        "lifecycle_hash_sha256"
    ]
    payload["poi_scheduler_rankable_now"] = False
    missed["package_replay_order_executable_final_blocker_reason"] = (
        "package_executable_authority_required_not_met"
    )
    missed["package_replay_order_executable_final_blocker_source"] = (
        "package_replay_order_executable_candidate_use_allowed"
    )
    missed["package_replay_order_executable_blocker_resolution"] = {
        "primary_reason": "package_executable_authority_required_not_met",
        "primary_source": (
            "reason_surface[0].package_replay_order_executable_candidate_use_allowed_reason"
        ),
        "all_observed_reasons": [
            "package_executable_authority_required_not_met"
        ],
    }

    scan = verifier.scan_broad_poi_state_contract(paths)

    assert scan["bad_counts"][
        "missed:nonrankable_poi_lifecycle_blocker_not_observed"
    ] == 1
    assert scan["bad_counts"][
        "missed:nonrankable_poi_lower_precedence_primary_blocker"
    ] == 1


def test_broad_poi_state_contract_accepts_specific_dormant_missed_blocker() -> None:
    verifier = load_verifier()
    paths = _verifier_poi_scan_fixture()
    missed = paths["missed"][0]
    dormant_lifecycle = build_causal_poi_lifecycle_envelope(
        poi_state=missed["poi_state"],
        decision_time_utc=missed["decision_time_utc"],
        fillability={
            "fill_probability": 0.10,
            "current_price_source_time_utc": "2026-05-14T00:45:00+00:00",
            "source_boundary": "closed_m15_predecision_asof_no_postdecision_path",
        },
        distance_to_zone_price=10.0,
        distance_to_zone_atr=10.0,
        distance_to_midpoint_price=10.0,
        distance_to_midpoint_atr=10.0,
        scheduler_readiness_floor=0.45,
        scheduler_readiness_policy_source="test_floor",
        scheduler_readiness_policy_hash_sha256="a" * 64,
    )
    lifecycle_reason = dormant_lifecycle["primary_reason"]
    lifecycle_source = "reason_surface[0].causal_poi_lifecycle.primary_reason"
    missed["causal_poi_lifecycle"] = dormant_lifecycle
    missed["causal_poi_lifecycle_hash_sha256"] = dormant_lifecycle[
        "lifecycle_hash_sha256"
    ]
    missed["poi_scheduler_rankable_now"] = False
    payload = missed["package_new_entry_authority_payload"]
    payload["causal_poi_lifecycle"] = dormant_lifecycle
    payload["causal_poi_lifecycle_hash_sha256"] = dormant_lifecycle[
        "lifecycle_hash_sha256"
    ]
    payload["poi_scheduler_rankable_now"] = False
    missed["package_replay_order_executable_final_blocker_reason"] = lifecycle_reason
    missed["package_replay_order_executable_final_blocker_source"] = lifecycle_source
    missed["package_replay_order_executable_blocker_resolution"] = {
        "primary_reason": lifecycle_reason,
        "primary_source": lifecycle_source,
        "all_observed_reasons": [
            lifecycle_reason,
            "package_executable_authority_required_not_met",
        ],
    }

    scan = verifier.scan_broad_poi_state_contract(paths)

    assert "missed:nonrankable_poi_lifecycle_blocker_not_observed" not in scan[
        "bad_counts"
    ]
    assert "missed:nonrankable_poi_lower_precedence_primary_blocker" not in scan[
        "bad_counts"
    ]
    assert "missed:nonrankable_poi_lifecycle_primary_source_mismatch" not in scan[
        "bad_counts"
    ]


def test_broad_poi_state_contract_rejects_partition_and_hash_swap() -> None:
    verifier = load_verifier()
    paths = _verifier_poi_scan_fixture()
    paths["decision"][0]["current_fvg_poi_generation"][
        "considered_poi_count"
    ] = 2
    swapped = dict(paths["scorecard"][0]["poi_state"])
    swapped["poi_state_hash_sha256"] = "0" * 64
    paths["scorecard"][0]["poi_state"] = swapped
    order_identity = {
        key: paths["order"][0][key]
        for key in (
            "candidate_id",
            "decision_time_utc",
            "canonical_replay_candidate_instance_key",
        )
    }
    paths["order"][0] = order_identity

    scan = verifier.scan_broad_poi_state_contract(paths)

    assert scan["bad_counts"]["decision:considered_count_mismatch"] == 1
    assert scan["bad_counts"]["decision:partition_not_reconciled"] == 1
    assert scan["bad_counts"][
        "scorecard:poi_state_contract:poi_state_hash_mismatch"
    ] == 1
    assert scan["bad_counts"]["scorecard:poi_state_atomic_conflict"] >= 1
    assert scan["bad_counts"]["cross_stage:cross_stage_poi_lineage_mismatch"] == 1
    assert scan["bad_counts"][
        "cross_stage:required_poi_state_missing_from_bound_stage"
    ] == 1


def test_broad_poi_state_contract_rejects_vacuous_generation_coverage() -> None:
    verifier = load_verifier()
    paths = _verifier_poi_scan_fixture()
    paths["decision"] = [{"decision_time_utc": "2026-05-14T01:00:00+00:00"}]

    scan = verifier.scan_broad_poi_state_contract(paths)

    assert scan["bad_counts"][
        "decision:generation_partition_coverage_zero_for_poi_candidates"
    ] == 1
    assert scan["bad_counts"][
        "cross_stage:poi_candidate_missing_emitted_generation_disposition"
    ] == 1


def test_broad_poi_state_contract_ignores_non_poi_signed_payload() -> None:
    verifier = load_verifier()
    candidate_id = "current-ob-candidate"
    decision_time = "2026-05-14T01:00:00+00:00"
    instance_key = f"{candidate_id}@@{decision_time}"
    payload = {
        "payload_schema": PACKAGE_NEW_ENTRY_AUTHORITY_PAYLOAD_SCHEMA,
        "payload_contract": PACKAGE_NEW_ENTRY_AUTHORITY_IMMUTABLE_PAYLOAD_CONTRACT,
        "candidate_id": candidate_id,
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": instance_key,
        "poi_state_required": False,
    }
    stage_row = {
        "candidate_id": candidate_id,
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": instance_key,
        "origin_family": "current_ob_retest",
        "framework": "ob_retest",
        "package_new_entry_authority_payload": payload,
    }
    paths = {
        "source_universe": [{"row_type": "source_scope"}],
        "decision": [{"decision_time_utc": decision_time}],
        "candidate": [dict(stage_row)],
        "scorecard": [dict(stage_row)],
        "order": [dict(stage_row)],
        "trade": [dict(stage_row)],
        "missed": [dict(stage_row)],
    }

    scan = verifier.scan_broad_poi_state_contract(paths)

    assert scan["bad_counts"] == {}
    assert scan["row_counts"]["candidate_non_poi_rows"] == 1


def test_broad_poi_scorecard_contract_isolates_selected_probe_candidate_identity() -> None:
    verifier = load_verifier()
    paths = _verifier_poi_scan_fixture()
    scorecard = paths["scorecard"][0]
    primary_probe = copy.deepcopy(scorecard)
    primary_probe["selected"] = True
    primary_probe["risk_finalizer_probe_instance_key"] = scorecard[
        "canonical_replay_candidate_instance_key"
    ]
    secondary_probe = copy.deepcopy(primary_probe)
    secondary_probe["candidate_id"] = "secondary-selected-candidate"
    secondary_probe["canonical_replay_candidate_instance_key"] = (
        "secondary-selected-candidate@@" + scorecard["decision_time_utc"]
    )
    secondary_probe["risk_finalizer_probe_instance_key"] = secondary_probe[
        "canonical_replay_candidate_instance_key"
    ]
    secondary_state = dict(secondary_probe["poi_state"])
    secondary_state["poi_id"] = "poi-secondary"
    secondary_state["poi_state_hash_sha256"] = "f" * 64
    secondary_probe["poi_state"] = secondary_state
    secondary_probe["package_new_entry_authority_poi_state"] = secondary_state
    scorecard["risk_admitted_scheduler_finalizer"] = {
        "probe_rows": [primary_probe, secondary_probe]
    }

    contract = verifier._broad_poi_row_contract(scorecard)

    assert contract["conflicts"] == []
    assert all(
        "probe_rows[1]" not in source for source in contract["state_sources"]
    )


def test_broad_poi_contract_does_not_promote_explicit_nonrequired_stale_alias() -> None:
    verifier = load_verifier()
    row = {
        "candidate_id": "non-poi-candidate",
        "decision_time_utc": "2026-06-16T15:45:00+00:00",
        "origin_family": "current_ob_retest",
        "framework": "ob_retest",
        "package_new_entry_authority_required": False,
        "package_new_entry_authority_poi_state_required": False,
        "package_new_entry_authority_poi_id": "stale-poi-alias",
    }

    contract = verifier._broad_poi_row_contract(row)

    assert contract["required"] is False
    assert contract["state"] == {}


def test_route_artifact_dataless_placeholder_detection() -> None:
    verifier = load_verifier()

    assert verifier.route_artifact_is_dataless_placeholder(
        SimpleNamespace(st_size=2_000_000, st_blocks=0)
    )
    assert not verifier.route_artifact_is_dataless_placeholder(
        SimpleNamespace(st_size=0, st_blocks=0)
    )
    assert not verifier.route_artifact_is_dataless_placeholder(
        SimpleNamespace(st_size=10, st_blocks=0)
    )
    assert not verifier.route_artifact_is_dataless_placeholder(
        SimpleNamespace(st_size=10, st_blocks=1)
    )


def test_materialize_file_provider_artifact_fails_fast_for_dataless(
    tmp_path: Path,
    monkeypatch,
) -> None:
    verifier = load_verifier()
    artifact = tmp_path / "proof.jsonl"
    artifact.write_text("{}", encoding="utf-8")

    class DatalessPath:
        def __init__(self, path: Path) -> None:
            self._path = path

        def __str__(self) -> str:
            return str(self._path)

        def stat(self):
            return SimpleNamespace(st_size=10, st_blocks=0)

    monkeypatch.setattr(verifier, "FILE_PROVIDER_MATERIALIZE_TIMEOUT_RETRIES", 1)
    monkeypatch.setattr(verifier, "FILE_PROVIDER_DATALESS_MIN_BYTES", 1)
    monkeypatch.setattr(verifier.Path, "exists", lambda self: False)

    try:
        verifier.materialize_file_provider_artifact(DatalessPath(artifact), force=True)
    except verifier.RouteArtifactMaterializationError as exc:
        assert "artifact remains dataless" in str(exc)
    else:
        raise AssertionError("expected dataless proof artifact to fail fast")


def test_default_confidence_provenance_allows_visible_warning_flag() -> None:
    verifier = load_verifier()

    issues = verifier.default_confidence_provenance_issues(
        {
            "candidate_decision_quality_field_sources": {
                "confidence": "scheduler_default_missing_confidence_0_55",
            },
            "candidate_decision_quality_optional_provenance_warnings": [
                "confidence_source_inferred:scheduler_default_missing_confidence_0_55",
                "confidence_missing_degraded_default_applied",
            ],
            "confidence_missing_degraded_default_applied": True,
        }
    )

    assert issues == []


def test_default_confidence_provenance_flags_hidden_nested_default() -> None:
    verifier = load_verifier()

    issues = verifier.default_confidence_provenance_issues(
        {
            "candidate_decision_quality_field_sources": {
                "confidence": "candidate.candidate_confidence",
            },
            "scheduler_candidate_decision_inputs": {
                "candidate_decision_quality_field_sources": {
                    "confidence": "scheduler_default_missing_confidence_0_55",
                }
            },
        }
    )

    assert "default_confidence_hidden_by_top_level_source" in issues
    assert "default_confidence_source_without_warning" in issues
    assert "default_confidence_source_without_degraded_default_flag" in issues


def test_default_confidence_provenance_flags_stale_semantic_alias_mismatch() -> None:
    verifier = load_verifier()

    issues = verifier.default_confidence_provenance_issues(
        {
            "confidence": 0.55,
            "candidate_confidence": 0.55,
            "confidence_missing_degraded_default_applied": True,
            "candidate_decision_quality_alias_status": "mismatch",
            "candidate_decision_quality_alias_mismatches": [
                "field_sources:confidence:row.candidate_decision_quality_vs_canonical",
            ],
            "candidate_decision_quality_field_sources": {
                "confidence": "candidate.candidate_confidence",
            },
            "candidate_decision_quality_optional_provenance_warnings": [
                "confidence_source_inferred:scheduler_default_missing_confidence_0_55",
                "confidence_missing_degraded_default_applied",
            ],
            "candidate_decision_quality": {
                "confidence": 0.55,
                "candidate_confidence": 0.55,
                "confidence_missing_degraded_default_applied": True,
                "candidate_decision_quality_field_sources": {
                    "confidence": "scheduler_default_missing_confidence_0_55",
                },
            },
        }
    )

    assert "stale_default_confidence_source_mismatch" in issues
    assert "default_confidence_hidden_by_top_level_source" not in issues


def test_default_confidence_provenance_requires_genuine_source_conflict_to_fail_closed() -> None:
    verifier = load_verifier()

    issues = verifier.default_confidence_provenance_issues(
        {
            "confidence": 0.55,
            "candidate_confidence": 0.55,
            "confidence_missing_degraded_default_applied": True,
            "candidate_decision_quality_alias_status": "exact_materialized",
            "candidate_decision_quality_alias_mismatches": [],
            "candidate_decision_quality_field_sources": {
                "confidence": "model.calibrated_confidence_v2",
            },
            "candidate_decision_quality_optional_provenance_warnings": [
                "confidence_source_inferred:scheduler_default_missing_confidence_0_55",
                "confidence_missing_degraded_default_applied",
            ],
            "candidate_decision_quality": {
                "confidence": 0.55,
                "candidate_decision_quality_field_sources": {
                    "confidence": "scheduler_default_missing_confidence_0_55",
                },
            },
        }
    )

    assert "genuine_confidence_source_conflict_not_fail_closed" in issues
    assert "default_confidence_hidden_by_top_level_source" in issues


def test_dynamic_execution_fillability_floor_flags_stale_veto() -> None:
    verifier = load_verifier()
    row = {
        "candidate_id": "stale-dynamic-fill-veto",
        "decision_time_utc": "2026-05-14T08:15:00+00:00",
        "dynamic_budget_min_fill_probability": 0.80,
        "vetoes": [
            "scheduler_dynamic_budget_quality_floor_not_met:"
            "fill_probability_below_dynamic_allocator_floor"
        ],
        "predecision_limit_fillability": {
            "available": True,
            "fill_probability": 0.92,
            "current_price_source_time_utc": "2026-05-14T08:00:00+00:00",
            "source_boundary": "closed_m15_predecision_asof_no_postdecision_path",
        },
    }

    assert verifier.dynamic_execution_fillability_floor_issues(row) == [
        "stale_dynamic_fill_floor_veto_above_canonical_execution_floor"
    ]


def test_dynamic_execution_fillability_floor_keeps_honest_low_fill_veto() -> None:
    verifier = load_verifier()
    row = {
        "candidate_id": "honest-dynamic-fill-veto",
        "decision_time_utc": "2026-05-14T08:15:00+00:00",
        "dynamic_budget_min_fill_probability": 0.80,
        "vetoes": [
            "scheduler_dynamic_budget_quality_floor_not_met:"
            "fill_probability_below_dynamic_allocator_floor"
        ],
        "predecision_limit_fillability": {
            "available": True,
            "fill_probability": 0.24,
            "current_price_source_time_utc": "2026-05-14T08:00:00+00:00",
            "source_boundary": "closed_m15_predecision_asof_no_postdecision_path",
        },
    }

    assert verifier.dynamic_execution_fillability_floor_issues(row) == []


def test_confidence_source_omission_flags_present_confidence_without_source() -> None:
    verifier = load_verifier()

    issues = verifier.confidence_source_omission_issues(
        {
            "candidate_id": "missed-hidden-default",
            "confidence": 0.55,
            "candidate_confidence": 0.55,
        }
    )

    assert issues == ["confidence_present_without_confidence_source"]


def test_scorecard_scan_flags_top_level_default_confidence_without_warning() -> None:
    verifier = load_verifier()

    scan = verifier.scan_replay_bridge_quality_parity(
        compact_candidate_groups={},
        scorecard_groups={
            "fixture": [
                {
                    "candidate_id": "scorecard-default-confidence",
                    "selected_candidate_ids": ["scorecard-default-confidence"],
                    "candidate_instance_identity_status": "materialized",
                    "source_boundary": "predecision_limit_fillability_geometry_no_outcome_path",
                    "candidate_decision_quality_source_boundary": (
                        "predecision_limit_fillability_geometry_no_outcome_path"
                    ),
                    "confidence": 0.55,
                    "candidate_confidence": 0.55,
                    "candidate_decision_quality_field_sources": {
                        "confidence": "scheduler_default_missing_confidence_0_55",
                    },
                }
            ]
        },
    )

    assert (
        scan["scorecard_provenance_bad_counts"][
            "fixture.scorecard:candidate_decision_quality:"
            "default_confidence_source_without_warning"
        ]
        == 1
    )
    assert (
        scan["scorecard_provenance_bad_counts"][
            "fixture.scorecard:candidate_decision_quality:"
            "default_confidence_source_without_degraded_default_flag"
        ]
        == 1
    )


def _exact_window_contract_fixture() -> tuple[dict, dict, dict]:
    prefix = (
        "BROAD_LIVE_AS_IF_REPLAY_SELECTED_POLICY_AUTHORITY_AND_STOP_HAZARD_"
        "RISK_CAP_REPAIR_V95_20260513_REPAIRED_ONLY_COMPACT_SMOKE"
    )
    broad_summary = {
        "output_prefix": prefix,
        "date_start": "2026-05-13",
        "date_end": "2026-05-13",
        "selected_day_count": 1,
        "coverage_status": "bounded_replay_materialization_not_full_available_universe",
        "full_available_configured_day_count": 901,
        "split_profile_stats": [
            {
                "profile": "repaired_package_conversion_v3",
                "headline_net_r": 4.144574,
                "headline_gross_r": 4.94074213,
                "headline_final_r": 4.94074213,
                "cash_pnl": 1048.35585088,
                "headline_trade_rows": 10,
            }
        ],
    }
    stream_scan = {
        "exact_window_profile_metrics": {
            "repaired_package_conversion_v3": {
                "package_axis_rows_in_parity_scope": 1101,
                "package_axes_available_inside_replay_window": 1101,
                "source_bound_r_nonzero_package_axes_inside_replay_window": 30,
                "source_bound_r_positive_package_axes_inside_replay_window": 22,
                "package_axes_in_global_diagnostic_surface": 1094,
                "candidate_generated_axes_inside_replay_window": 853,
                "scorecard_present_axes_inside_replay_window": 13,
                "order_present_axes_inside_replay_window": 13,
                "scorecard_or_order_present_axes_inside_replay_window": 13,
                "filled_trade_axes_inside_replay_window": 7,
                "scorecard_selected_count_inside_replay_window": 21,
                "order_present_count_inside_replay_window": 21,
                "trade_count_inside_replay_window": 10,
                "source_bound_r_available_inside_replay_window": 56984.445501245,
                "package_source_bound_r_available_inside_replay_window": 56984.445501245,
                "non_additive_executable_gated_source_bound_signal_r_inside_replay_window": 56984.445501245,
                "non_additive_executable_gated_package_source_bound_signal_r_inside_replay_window": 56984.445501245,
                "diagnostic_global_source_bound_r_sum_not_denominator": 1249248.03066685,
                "diagnostic_global_package_source_bound_r_sum_not_denominator": 1249248.03066685,
                "axis_attributed_actual_executable_r_inside_replay_window": 1.89411632,
            }
        }
    }
    parity_summary = {
        "candidate_instance_parity_projection": {
            "profile_stage_presence_counts": {
                "repaired_package_conversion_v3": {
                    "candidate": 100,
                    "scorecard": 30,
                    "scheduler_selected": 19,
                    "order": 19,
                    "trade": 10,
                    "missed": 90,
                }
            }
        },
        "profile_metrics": {
            "repaired_package_conversion_v3": {
                "unique_actual_r_sum": 4.144574,
                "unique_gross_r_sum": 4.94074213,
                "unique_final_r_sum": 4.94074213,
                "unique_cash_pnl_sum": 1048.35585088,
            }
        },
        "exact_replay_window_transfer": {
            "schema": (
                "gtos.final_moonshot.denominator_to_deployment."
                "exact_replay_window_transfer.v1"
            ),
            "broad_replay_prefix": prefix,
            "date_start": "2026-05-13",
            "date_end": "2026-05-13",
            "selected_day_count": 1,
            "coverage_status": "bounded_replay_materialization_not_full_available_universe",
            "full_available_configured_day_count": 901,
            "denominator_scope": (
                "selected_replay_window_axis_presence_with_non_additive_"
                "source_member_signal_diagnostics"
            ),
            "source_bound_r_additive_allowed": False,
            "package_source_bound_r_additive_allowed": False,
            "executable_r_to_source_bound_r_percentage_allowed": False,
            "source_bound_r_denominator_field": None,
            "package_source_bound_r_denominator_field": None,
            "source_bound_signal_evidence_class": (
                "source_member_axis_overlap_not_additive_exact_execution_r"
            ),
            "legacy_compatibility_non_additive_signal_fields": [
                "source_bound_r_available_inside_replay_window",
                "package_source_bound_r_available_inside_replay_window",
            ],
            "canonical_non_additive_signal_fields": [
                "non_additive_executable_gated_source_bound_signal_r_inside_replay_window",
                "non_additive_executable_gated_package_source_bound_signal_r_inside_replay_window",
            ],
            "diagnostic_reservoir_fields_not_denominator": [
                "diagnostic_source_bound_r",
                "diagnostic_package_source_bound_r",
            ],
            "full_reservoir_transfer_claim_allowed": False,
            "interpretation": (
                "This smoke proves or disproves the local repair; it does not prove "
                "total reservoir conversion."
            ),
            "profiles": {
                "repaired_package_conversion_v3": {
                    "package_axis_rows_in_parity_scope": 1101,
                    "package_axes_available_inside_replay_window": 1101,
                    "source_bound_r_nonzero_package_axes_inside_replay_window": 30,
                    "source_bound_r_positive_package_axes_inside_replay_window": 22,
                    "package_axes_in_global_diagnostic_surface": 1094,
                    "candidate_generated_axes_inside_replay_window": 853,
                    "scorecard_present_axes_inside_replay_window": 13,
                    "order_present_axes_inside_replay_window": 13,
                    "scorecard_or_order_present_axes_inside_replay_window": 13,
                    "filled_trade_axes_inside_replay_window": 7,
                    "axis_attributed_scorecard_selected_count_inside_replay_window": 21,
                    "axis_attributed_order_present_count_inside_replay_window": 21,
                    "axis_attributed_trade_count_inside_replay_window": 10,
                    "scorecard_selected_count_inside_replay_window": 19,
                    "order_present_count_inside_replay_window": 19,
                    "trade_count_inside_replay_window": 10,
                    "candidate_instance_count_authority": (
                        "candidate_instance_parity_projection_exact_unique"
                    ),
                    "candidate_instance_rows_inside_replay_window": 100,
                    "scorecard_present_candidate_instance_rows_inside_replay_window": 30,
                    "scheduler_selected_candidate_instance_rows_inside_replay_window": 19,
                    "order_present_candidate_instance_rows_inside_replay_window": 19,
                    "filled_candidate_instance_rows_inside_replay_window": 10,
                    "missed_candidate_instance_rows_inside_replay_window": 90,
                    "source_bound_r_available_inside_replay_window": 56984.445501245,
                    "package_source_bound_r_available_inside_replay_window": 56984.445501245,
                    "non_additive_executable_gated_source_bound_signal_r_inside_replay_window": 56984.445501245,
                    "non_additive_executable_gated_package_source_bound_signal_r_inside_replay_window": 56984.445501245,
                    "diagnostic_global_source_bound_r_sum_not_denominator": 1249248.03066685,
                    "diagnostic_global_package_source_bound_r_sum_not_denominator": 1249248.03066685,
                    "axis_attributed_actual_executable_r_inside_replay_window": 1.89411632,
                    "actual_executable_r_inside_replay_window": 4.144574,
                    "gross_executable_r_inside_replay_window": 4.94074213,
                    "final_executable_r_inside_replay_window": 4.94074213,
                    "cash_pnl_inside_replay_window": 1048.35585088,
                    "headline_replay_net_r_inside_replay_window": 4.144574,
                    "headline_replay_gross_r_inside_replay_window": 4.94074213,
                    "headline_replay_final_r_inside_replay_window": 4.94074213,
                    "headline_replay_cash_pnl_inside_replay_window": 1048.35585088,
                    "headline_replay_trade_rows_inside_replay_window": 10,
                    "headline_vs_unique_actual_r_delta": 0.0,
                    "headline_vs_axis_attributed_actual_r_delta": 2.25045768,
                    "unique_actual_vs_axis_attributed_actual_r_delta": 2.25045768,
                    "r_metric_reconciliation_status": (
                        "headline_unique_axis_r_surfaces_differ_explicit"
                    ),
                    "diagnostic_global_r_is_denominator": False,
                    "source_bound_r_additive_allowed": False,
                    "package_source_bound_r_additive_allowed": False,
                    "executable_r_to_source_bound_r_percentage_allowed": False,
                    "source_bound_signal_evidence_class": (
                        "source_member_axis_overlap_not_additive_exact_execution_r"
                    ),
                    "actual_executable_r_pct_of_window_source_bound_r": None,
                    "actual_executable_r_pct_disposition": (
                        "forbidden_non_additive_source_member_axis_overlap_signal"
                    ),
                }
            },
        },
    }
    return parity_summary, broad_summary, stream_scan


def test_exact_replay_window_transfer_contract_accepts_bounded_smoke() -> None:
    verifier = load_verifier()
    parity_summary, broad_summary, stream_scan = _exact_window_contract_fixture()

    issues = verifier.validate_exact_replay_window_transfer_contract(
        source_bound_parity_summary=parity_summary,
        broad_live_as_if_summary=broad_summary,
        source_bound_parity_stream_scan=stream_scan,
    )

    assert issues == []


def test_exact_replay_window_transfer_separates_physical_and_headline_trade_counts() -> None:
    verifier = load_verifier()
    parity_summary, broad_summary, stream_scan = _exact_window_contract_fixture()
    profile = "repaired_package_conversion_v3"
    broad_stats = broad_summary["split_profile_stats"][0]
    broad_stats["trade_rows"] = 12
    broad_stats["headline_trade_rows"] = 10
    broad_stats["all_executed_trade_rows"] = 10
    projection = parity_summary["candidate_instance_parity_projection"][
        "profile_stage_presence_counts"
    ][profile]
    projection["trade"] = 12
    exact = parity_summary["exact_replay_window_transfer"]["profiles"][profile]
    exact["trade_count_inside_replay_window"] = 12
    exact["filled_candidate_instance_rows_inside_replay_window"] = 12
    exact["headline_replay_trade_rows_inside_replay_window"] = 10

    issues = verifier.validate_exact_replay_window_transfer_contract(
        source_bound_parity_summary=parity_summary,
        broad_live_as_if_summary=broad_summary,
        source_bound_parity_stream_scan=stream_scan,
    )

    assert issues == []


def test_exact_replay_window_transfer_contract_rejects_full_reservoir_misuse() -> None:
    verifier = load_verifier()
    parity_summary, broad_summary, stream_scan = _exact_window_contract_fixture()
    transfer = parity_summary["exact_replay_window_transfer"]
    transfer["full_reservoir_transfer_claim_allowed"] = True
    transfer["source_bound_r_denominator_field"] = "diagnostic_source_bound_r"
    transfer["profiles"]["repaired_package_conversion_v3"][
        "diagnostic_global_r_is_denominator"
    ] = True

    issues = verifier.validate_exact_replay_window_transfer_contract(
        source_bound_parity_summary=parity_summary,
        broad_live_as_if_summary=broad_summary,
        source_bound_parity_stream_scan=stream_scan,
    )

    assert "source_bound_parity_bounded_smoke_full_reservoir_claim_allowed" in issues
    assert "source_bound_parity_exact_window_source_denominator_mismatch" in issues
    assert (
        "source_bound_parity_exact_window_diagnostic_r_marked_denominator:"
        "repaired_package_conversion_v3"
    ) in issues


def test_exact_replay_window_transfer_rejects_non_additive_percentage() -> None:
    verifier = load_verifier()
    parity_summary, broad_summary, stream_scan = _exact_window_contract_fixture()
    metrics = parity_summary["exact_replay_window_transfer"]["profiles"][
        "repaired_package_conversion_v3"
    ]
    metrics["actual_executable_r_pct_of_window_source_bound_r"] = 0.01

    issues = verifier.validate_exact_replay_window_transfer_contract(
        source_bound_parity_summary=parity_summary,
        broad_live_as_if_summary=broad_summary,
        source_bound_parity_stream_scan=stream_scan,
    )

    assert (
        "source_bound_parity_exact_window_non_additive_semantics_invalid:"
        "repaired_package_conversion_v3"
    ) in issues


def test_exact_replay_window_transfer_contract_requires_r_reconciliation() -> None:
    verifier = load_verifier()
    parity_summary, broad_summary, stream_scan = _exact_window_contract_fixture()
    metrics = parity_summary["exact_replay_window_transfer"]["profiles"][
        "repaired_package_conversion_v3"
    ]
    metrics.pop("r_metric_reconciliation_status")
    metrics["headline_vs_unique_actual_r_delta"] = 99.0

    issues = verifier.validate_exact_replay_window_transfer_contract(
        source_bound_parity_summary=parity_summary,
        broad_live_as_if_summary=broad_summary,
        source_bound_parity_stream_scan=stream_scan,
    )

    assert (
        "source_bound_parity_exact_window_r_reconciliation_status_missing:"
        "repaired_package_conversion_v3:missing"
    ) in issues
    assert (
        "source_bound_parity_exact_window_headline_unique_delta_mismatch:"
        "repaired_package_conversion_v3"
    ) in issues


def test_exact_replay_window_transfer_contract_rejects_false_reconciliation_status() -> None:
    verifier = load_verifier()
    parity_summary, broad_summary, stream_scan = _exact_window_contract_fixture()
    metrics = parity_summary["exact_replay_window_transfer"]["profiles"][
        "repaired_package_conversion_v3"
    ]
    metrics["r_metric_reconciliation_status"] = "headline_unique_axis_r_aligned"

    issues = verifier.validate_exact_replay_window_transfer_contract(
        source_bound_parity_summary=parity_summary,
        broad_live_as_if_summary=broad_summary,
        source_bound_parity_stream_scan=stream_scan,
    )

    assert (
        "source_bound_parity_exact_window_r_reconciliation_status_mismatch:"
        "repaired_package_conversion_v3:expected="
        "headline_unique_axis_r_surfaces_differ_explicit:actual="
        "headline_unique_axis_r_aligned"
    ) in issues


def test_exact_replay_window_transfer_contract_rejects_broad_headline_drift() -> None:
    verifier = load_verifier()
    parity_summary, broad_summary, stream_scan = _exact_window_contract_fixture()
    broad_summary["split_profile_stats"][0]["headline_net_r"] = -99.0
    broad_summary["output_prefix"] = "OTHER_PREFIX"

    issues = verifier.validate_exact_replay_window_transfer_contract(
        source_bound_parity_summary=parity_summary,
        broad_live_as_if_summary=broad_summary,
        source_bound_parity_stream_scan=stream_scan,
    )

    assert (
        "source_bound_parity_exact_window_broad_headline_mismatch:"
        "repaired_package_conversion_v3:"
        "headline_replay_net_r_inside_replay_window:expected=-99.0:actual=4.144574"
    ) in issues
    assert any(
        issue.startswith(
            "source_bound_parity_exact_window_broad_replay_prefix_mismatch:"
        )
        for issue in issues
    )


def test_package_new_entry_scope_target_scan_flags_nonmatching_intent_scope(tmp_path: Path) -> None:
    verifier = load_verifier()
    ledger = tmp_path / "scope_target.jsonl"
    rows = [
        {
            "candidate_id": "good-scale-in",
            "package_new_entry_authority_scope": (
                "selector_reduced_risk_to_scheduler_same_direction_scale_in"
            ),
            "package_new_entry_authority_target_action_intent": "same_direction_scale_in",
        },
        {
            "candidate_id": "bad-replace",
            "package_new_entry_authority_scope": (
                "selector_reduced_risk_to_scheduler_new_position"
            ),
            "package_new_entry_authority_target_action_intent": "replace_pending",
        },
    ]
    ledger.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )

    scan = verifier.scan_package_new_entry_scope_target_parity({"fixture": ledger})

    assert scan["bad_counts"] == {"fixture:scope_target_mismatch:replace_pending": 1}
    assert scan["sample_bad"][0]["candidate_id"] == "bad-replace"
    assert (
        scan["sample_bad"][0]["expected_scope"]
        == "selector_reduced_risk_to_scheduler_replace_pending"
    )


def test_verifier_package_replay_authority_scope_ignores_plain_diagnostic_false() -> None:
    verifier = load_verifier()

    assert (
        verifier.package_replay_authority_scope_present(
            {
                "candidate_id": "ordinary-row",
                "package_replay_executable_candidate_use_allowed": False,
                "package_replay_executable_candidate_use_allowed_reason": (
                    "candidate_decision_quality_provenance_missing:expected_net_r"
                ),
            }
        )
        is False
    )
    assert (
        verifier.package_replay_authority_scope_present(
            {
                "candidate_id": "package-row",
                "source_bound_package_candidate_use_allowed": True,
                "package_replay_executable_candidate_use_allowed": False,
            }
        )
        is True
    )
    assert (
        verifier.package_replay_authority_scope_present(
            {
                "candidate_id": "admission-row",
                "ultimate_package_effective_admission_count": 1,
            }
        )
        is True
    )


def test_behavior_row_compact_quality_alias_status_upgrades_materialized() -> None:
    builder = load_builder()

    row = builder.compact_replay_candidate_fields_for_behavior_row(
        source_candidate={
            "candidate_expected_net_r": 1.1,
            "candidate_probability": 0.7,
            "candidate_fill_probability": 0.8,
            "source_completeness": 1.0,
            "candidate_decision_quality_field_sources": {
                "expected_net_r": "fixture.expected_net_r",
                "probability": "fixture.probability",
                "fill_probability": "fixture.fill_probability",
                "source_completeness": "fixture.source_completeness",
            },
            "candidate_decision_quality_source_boundary": (
                "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
            ),
            "candidate_decision_quality_alias_status": "materialized",
            "candidate_decision_quality_provenance_failures": [
                "candidate_decision_quality_alias_status:materialized"
            ],
        },
        order_policy_row={},
    )

    assert row["candidate_decision_quality_alias_status"] == (
        "exact_materialized_from_complete_predecision_quality_sources"
    )
    assert row["candidate_decision_quality_provenance_failures"] == []


def test_signed_package_new_entry_authority_required_only_for_new_entry_intents() -> None:
    verifier = load_verifier()

    assert verifier.signed_package_new_entry_authority_required(
        {
            "selector_action": "open-reduced-risk",
            "selector_reason": (
                "ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay"
            ),
            "scheduler_materialization_action_intent": "new_position",
        }
    ) == (True, "new_position")
    assert verifier.signed_package_new_entry_authority_required(
        {
            "selector_action": "open-reduced-risk",
            "selector_reason": (
                "ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay"
            ),
            "scheduler_materialization_action_intent": (
                "source_required_fail_closed_hold_not_executable_without_source"
            ),
        }
    ) == (
        False,
        "source_required_fail_closed_hold_not_executable_without_source",
    )
    assert verifier.signed_package_new_entry_authority_required(
        {
            "selector_action": "open-reduced-risk",
            "selector_reason": "replay_lifecycle_action_resolver_replace_pending",
            "scheduler_materialization_action_intent": "replace_pending",
        }
    ) == (True, "replace_pending")
    assert verifier.signed_package_new_entry_authority_required(
        {
            "selector_action": "open-reduced-risk",
            "selector_reason": "replay_lifecycle_action_resolver_close_and_reverse",
            "scheduler_materialization_action_intent": "close_and_reverse",
        }
    ) == (True, "close_and_reverse")


def test_nonrequired_authority_cannot_carry_immutable_claim_on_same_surface() -> None:
    verifier = load_verifier()
    row = {
        "package_new_entry_authority_required": False,
        "package_new_entry_authority_valid": False,
        "package_new_entry_authority_status": (
            "not_required_for_selector_action_or_action_intent"
        ),
        "package_new_entry_authority_payload": {"diagnostic": True},
        "package_new_entry_authority_hash_sha256": "a" * 64,
        "expected_package_new_entry_authority_hash_sha256": "a" * 64,
    }

    assert verifier.nonrequired_package_new_entry_authority_immutable_claim_reasons(
        row
    ) == [
        "nonrequired_package_new_entry_authority_immutable_claim:"
        "root:package_new_entry_authority_payload",
        "nonrequired_package_new_entry_authority_immutable_claim:"
        "root:package_new_entry_authority_hash_sha256",
        "nonrequired_package_new_entry_authority_immutable_claim:"
        "root:expected_package_new_entry_authority_hash_sha256",
    ]


def test_nonrequired_authority_check_does_not_merge_distinct_required_surface() -> None:
    verifier = load_verifier()
    row = {
        "package_new_entry_authority_required": False,
        "package_new_entry_authority_valid": False,
        "package_new_entry_authority_status": (
            "not_required_for_selector_action_or_action_intent"
        ),
        "scheduler_candidate_decision_inputs": {
            "ultimate_candidate_package_open_reduced_risk_authority": {
                "package_new_entry_authority_required": True,
                "package_new_entry_authority_valid": True,
                "package_new_entry_authority_status": (
                    "valid_signed_predecision_new_entry_authority"
                ),
                "package_new_entry_authority_payload": {"signed": True},
                "package_new_entry_authority_hash_sha256": "b" * 64,
                "expected_package_new_entry_authority_hash_sha256": "b" * 64,
            }
        },
    }

    assert (
        verifier.nonrequired_package_new_entry_authority_immutable_claim_reasons(row)
        == []
    )


def test_nonrequired_authority_rejects_stale_projection_failure() -> None:
    verifier = load_verifier()
    row = {
        "package_new_entry_authority_required": False,
        "package_new_entry_authority_valid": False,
        "package_new_entry_authority_status": (
            "not_required_for_selector_action_or_action_intent"
        ),
        "package_new_entry_authority_failures": [],
        "package_new_entry_authority_projection_failures": [
            "authority_payload_missing"
        ],
    }

    assert verifier.nonrequired_package_new_entry_authority_immutable_claim_reasons(
        row
    ) == [
        "nonrequired_package_new_entry_authority_projection_failure:"
        "root:package_new_entry_authority_projection_failures"
    ]


def test_runtime_reduced_risk_trade_admission_does_not_require_package_signature(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    row = {
        "candidate_id": "plain-trade-runtime-risk-cap",
        "selector_action": "trade",
        "raw_selector_action": "trade",
        "materialized_selector_action": "trade",
        "effective_selector_action_before_risk_expression": "trade",
        "effective_selector_action": "reduce-risk",
        "effective_risk_decision": "reduce-risk",
        "risk_decision": "reduce-risk",
        "risk_decision_family": "runtime_reduced_risk_entry",
        "risk_sizing_class": "runtime_reduced_risk_entry",
        "admission_risk_class_origin": "trade",
        "scheduler_materialization_action_intent": "new_position",
        "package_new_entry_authority_required": False,
        "package_new_entry_authority_valid": False,
        "package_new_entry_authority_status": (
            "not_required_for_selector_action_or_action_intent"
        ),
        "package_new_entry_authority_failures": [],
        "package_new_entry_authority_projection_failures": [],
        "package_replay_executable_candidate_use_allowed": True,
        "package_replay_order_executable_candidate_use_allowed": True,
        "package_replay_order_executable_transfer_status": "order_bound",
        "package_replay_order_executable_bound_order_id": "order-runtime-cap",
        "simulated_order_id": "order-runtime-cap",
        "order_status": "pending_accepted",
        "package_marketable_entry_guard_status": (
            "routed_to_immediate_marketable_limit_replay_order_policy"
        ),
        "order_execution_path": "immediate_marketable_limit_at_decision",
        "ultimate_package_matched_member_axis_count": 1,
        "ultimate_package_matched_member_axis_ids": [
            "member_axis:runtime-trade-cap"
        ],
        "risk_expression_ladder": {
            "raw_selector_action": "trade",
            "effective_selector_action": "trade",
            "risk_decision": "reduce-risk",
            "risk_decision_family": "runtime_reduced_risk_entry",
            "risk_sizing_class": "runtime_reduced_risk_entry",
            "source_boundary": (
                "predecision_scheduler_runtime_risk_authority_no_outcome_fields"
            ),
        },
        "replacement_reallocation_quality": {
            "soft_risk_cap_transfer_eligible": False,
            "stop_hazard_status": "capped",
            "legacy_mixed_reallocation_quality_score": -1.25,
            "reallocation_quality_min_promotion_score": 0.0,
        },
    }

    assert verifier.runtime_reduced_risk_trade_admission_contract_reasons(row) == []
    assert verifier.v220_hard_clean_capped_reduced_risk_contract_applies(row) is False
    assert verifier.finalized_executable_member_axis_identity_reasons(row) == []

    path = tmp_path / "runtime-reduced-trade-admission.jsonl"
    write_jsonl(path, [row])
    scan = verifier.scan_broad_order_executable_transfer_contract({"order": path})
    assert scan["bad_counts"] == {}

    reduced_admission = {**row, "raw_selector_action": "reduce-risk"}
    assert (
        "trade_admission_raw_selector_action_not_trade"
        in verifier.runtime_reduced_risk_trade_admission_contract_reasons(
            reduced_admission
        )
    )
    assert (
        verifier.v220_hard_clean_capped_reduced_risk_contract_applies(
            reduced_admission
        )
        is True
    )


def test_preserved_prefinal_runtime_trade_admission_does_not_require_package_signature(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    candidate_id = "plain-trade-runtime-cap-finally-blocked"
    decision_time = "2026-01-23T07:45:00+00:00"
    row = {
        "candidate_id": candidate_id,
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "source_bound_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "selector_action": "trade",
        "raw_selector_action": "trade",
        "materialized_selector_action": "trade",
        "effective_selector_action_before_risk_expression": "trade",
        "effective_selector_action": "reduce-risk",
        "effective_risk_decision": "reduce-risk",
        "risk_decision": "reduce-risk",
        "risk_decision_family": "runtime_reduced_risk_entry",
        "risk_sizing_class": "runtime_reduced_risk_entry",
        "admission_risk_class_origin": "trade",
        "scheduler_materialization_action_intent": "new_position",
        "package_new_entry_authority_required": False,
        "package_new_entry_authority_valid": False,
        "package_new_entry_authority_status": (
            "not_required_for_selector_action_or_action_intent"
        ),
        "package_new_entry_authority_failures": [],
        "package_new_entry_authority_projection_failures": [],
        "package_replay_executable_candidate_use_allowed": False,
        "package_replay_executable_candidate_use_allowed_pre_finalization": True,
        "package_replay_order_executable_candidate_use_allowed": False,
        "package_replay_order_executable_candidate_use_allowed_pre_finalization": True,
        "package_replay_order_executable_transfer_status": "final_blocked",
        "package_replay_order_executable_final_blocker_class": "fill_realism",
        "package_replay_order_executable_final_blocker_reason": (
            "ordered_tick_required_for_adverse_before_profit_sequence_not_satisfied"
        ),
        "ultimate_package_matched_member_axis_count": 1,
        "ultimate_package_matched_member_axis_ids": [
            "member_axis:runtime-trade-cap-final-blocked"
        ],
        "risk_expression_ladder": {
            "raw_selector_action": "trade",
            "effective_selector_action": "trade",
            "risk_decision": "reduce-risk",
            "risk_decision_family": "runtime_reduced_risk_entry",
            "risk_sizing_class": "runtime_reduced_risk_entry",
            "source_boundary": (
                "predecision_scheduler_runtime_risk_authority_no_outcome_fields"
            ),
        },
    }

    assert verifier.runtime_reduced_risk_trade_admission_contract_reasons(row) == [
        "trade_admission_package_replay_executable_candidate_use_allowed_not_true",
        "trade_admission_package_replay_order_executable_candidate_use_allowed_not_true",
    ]
    assert verifier.runtime_reduced_risk_trade_admission_contract_reasons(
        row,
        executable_authority_stage="pre_finalization",
    ) == []
    assert verifier.preserved_order_executable_proposal_contract_reasons(row) == []
    assert verifier.finalized_executable_member_axis_identity_reasons(
        row,
        executable_authority_stage="pre_finalization",
    ) == []

    path = tmp_path / "prefinal-runtime-trade-finally-blocked.jsonl"
    write_jsonl(path, [row])
    scan = verifier.scan_broad_order_executable_transfer_contract({"order": path})
    assert scan["bad_counts"] == {}


def test_selector_fill_floor_softening_requires_signed_predecision_package_authority_before_execution(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    order_path = tmp_path / "ORDER_LEDGER.jsonl"
    decision_time = "2026-05-13T08:30:00+00:00"
    base = {
        "candidate_id": "softened-fill-floor",
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": (
            f"softened-fill-floor@@{decision_time}"
        ),
        "source_bound_replay_candidate_instance_key": (
            f"softened-fill-floor@@{decision_time}"
        ),
        "selector_action": "open-reduced-risk",
        "selector_action_origin": "reject",
        "effective_selector_action": "open-reduced-risk",
        "selector_reason": (
            "ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay"
        ),
        "effective_selector_reason": (
            "ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay"
        ),
        "scheduler_materialization_selector_action": "open-reduced-risk",
        "scheduler_materialization_action_intent": "new_position",
        "package_open_reduced_authority_allowed": True,
        "package_open_reduced_authority_family": "fill_floor_softening",
        "package_open_reduced_authority_current_config_allowed": True,
        "open_reduced_authority_source_boundary": (
            "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
        ),
        "ultimate_candidate_package_open_reduced_risk_authority": {
            "allowed": True,
            "authority_family": "fill_floor_softening",
            "current_config_allowed": True,
            "source_boundary": (
                "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
            ),
        },
        "package_replay_executable_candidate_use_allowed": True,
        "package_replay_order_executable_candidate_use_allowed": True,
        "package_replay_order_executable_transfer_status": "order_bound",
        "package_replay_order_executable_bound_order_id": "order-softened",
        "pretrade_cost_packet_status": "PASSED",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "cost_authority": "broker_calibrated_replay_cost",
        "approved_risk_pct": 0.25,
        "simulated_order_id": "order-softened",
        "order_status": "pending_accepted",
    }
    signed = {
        **base,
        "candidate_id": "softened-fill-floor-signed",
        "canonical_replay_candidate_instance_key": (
            f"softened-fill-floor-signed@@{decision_time}"
        ),
        "source_bound_replay_candidate_instance_key": (
            f"softened-fill-floor-signed@@{decision_time}"
        ),
        "simulated_order_id": "order-softened-signed",
        "package_replay_order_executable_bound_order_id": "order-softened-signed",
        **signed_package_new_entry_fields(
            candidate_id="softened-fill-floor-signed",
            decision_time_utc=decision_time,
            action_intent="new_position",
            selector_action="open-reduced-risk",
        ),
    }
    mismatched = {
        **base,
        "candidate_id": "softened-fill-floor-mismatch",
        "canonical_replay_candidate_instance_key": (
            f"softened-fill-floor-mismatch@@{decision_time}"
        ),
        "source_bound_replay_candidate_instance_key": (
            f"softened-fill-floor-mismatch@@{decision_time}"
        ),
        "simulated_order_id": "order-softened-mismatch",
        "package_replay_order_executable_bound_order_id": "order-softened-mismatch",
        **signed_package_new_entry_fields(
            candidate_id="softened-fill-floor-mismatch",
            decision_time_utc=decision_time,
            action_intent="new_position",
            selector_action="open-reduced-risk",
        ),
        "expected_package_new_entry_authority_hash_sha256": "different-hash",
    }
    write_jsonl(order_path, [base, signed, mismatched])

    scan = verifier.scan_broad_emitted_scheduler_status_authority({"order": order_path})

    assert scan["bad_counts"][
        "order:selector_open_reduced_risk_signed_authority_invalid"
    ] == 3
    assert scan["bad_counts"].get("order:selector_open_reduced_risk_authority_missing", 0) == 0
    assert {
        sample["candidate_id"]
        for sample in scan["sample_bad"]
        if "selector_open_reduced_risk_signed_authority_invalid"
        in sample["reasons"]
    } == {
        "softened-fill-floor",
        "softened-fill-floor-signed",
        "softened-fill-floor-mismatch",
    }


def signed_package_new_entry_fields(
    *,
    candidate_id: str,
    decision_time_utc: str,
    action_intent: str = "new_position",
    selector_action: str = "reduce-risk",
    matched_member_axis_ids: tuple[str, ...] = ("member_axis:fixture",),
) -> dict:
    instance_key = f"{candidate_id}@@{decision_time_utc}"
    authority_field = (
        "ultimate_candidate_package_open_reduced_risk_authority"
        if selector_action == "open-reduced-risk"
        else "ultimate_candidate_package_reduce_risk_authority"
    )
    source_boundary = (
        "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
        if selector_action == "open-reduced-risk"
        else "predecision_package_reduce_risk_new_order_authority_no_outcome_fields"
    )
    scope = {
        "new_position": "selector_reduced_risk_to_scheduler_new_position",
        "same_direction_scale_in": (
            "selector_reduced_risk_to_scheduler_same_direction_scale_in"
        ),
        "replace_pending": "selector_reduced_risk_to_scheduler_replace_pending",
        "close_and_reverse": "selector_reduced_risk_to_scheduler_close_and_reverse",
    }.get(action_intent, f"selector_reduced_risk_to_scheduler_{action_intent}")
    quality_source_boundary = (
        "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
    )
    quality_field_sources = {
        "expected_net_r": "candidate_decision_inputs.expected_net_r",
        "probability": "candidate_decision_inputs.probability",
        "fill_probability": "candidate_decision_inputs.fill_probability",
        "source_completeness": "candidate_decision_inputs.source_completeness",
    }
    payload = {
        "payload_schema": PACKAGE_NEW_ENTRY_AUTHORITY_PAYLOAD_SCHEMA,
        "payload_contract": (
            PACKAGE_NEW_ENTRY_AUTHORITY_IMMUTABLE_PAYLOAD_CONTRACT
        ),
        "scope": scope,
        "target_action_intent": action_intent,
        "uses_outcome_fields": False,
        "candidate_id": candidate_id,
        "candidate_id_source": "candidate_id",
        "decision_time_utc": decision_time_utc,
        "canonical_replay_candidate_instance_key": instance_key,
        "source_bound_replay_candidate_instance_key": instance_key,
        "candidate_instance_identity_status": "materialized",
        "matched_member_axis_ids": list(matched_member_axis_ids),
        "selector_action": selector_action,
        "selector_reason": "unit_test_authority",
        "authority_applies": True,
        "authority_allowed": True,
        "authority_family": "unit_test_authority",
        "authority_source": "unit_test_predecision_authority",
        "source_boundary": source_boundary,
        "source_bound_package_candidate_use_allowed": True,
        "package_replay_order_executable_candidate_use_allowed": True,
        "package_replay_order_executable_candidate_use_allowed_reason": (
            "unit_test_signed_authority"
        ),
        "package_replay_order_executable_authority_source": (
            "unit_test_predecision_authority"
        ),
        "pretrade_cost_packet_status": "PASSED",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "cost_authority": "broker_calibrated_replay_cost",
        "candidate_cost_r_fallback_is_authority": False,
        "expected_net_r": 0.75,
        "probability": 0.7,
        "fill_probability": 0.8,
        "execution_fill_probability": 0.8,
        "execution_fill_probability_source": "predecision_limit_fillability",
        "execution_fill_probability_source_time_utc": (
            "2025-01-01T00:00:00+00:00"
        ),
        "execution_fill_probability_source_boundary": (
            "asof_candidate_fields_only_no_postdecision_path"
        ),
        "execution_fill_probability_authority_class": (
            "signed_predecision_execution_fillability_authority"
        ),
        "entry_quality_fill_probability": 0.8,
        "limit_fillability_probability": 0.8,
        "predecision_limit_fillability_probability": 0.8,
        "source_completeness": 1.0,
        "source_completeness_status": "complete",
        "candidate_decision_quality_field_sources": quality_field_sources,
        "candidate_decision_quality_source_boundary": quality_source_boundary,
        "candidate_decision_quality_alias_status": "exact_materialized",
        "candidate_decision_quality_alias_mismatches": [],
        "candidate_decision_quality_degraded_default_flags": {},
        "candidate_decision_quality_provenance_failures": [],
        "selected_policy_for_expected_net_r": "not_required_no_selected_policy",
        "selected_policy_expected_net_calibration_status": (
            "not_required_no_selected_policy"
        ),
        "selected_policy_expected_net_calibrated": False,
        "selected_policy_expected_net_calibration_required": False,
        "selected_policy_expected_net_calibration_source": "",
        "selected_policy_expected_net_calibration_source_boundary": "",
        "selected_policy_expected_net_calibration_hash": "",
    }
    authority_hash = package_new_entry_authority_payload_hash_sha256(payload)
    fields = {
        "package_new_entry_authority_required": True,
        "package_new_entry_authority_valid": True,
        "package_new_entry_authority_status": (
            "valid_signed_predecision_new_entry_authority"
        ),
        "package_new_entry_authority_failures": [],
        "package_new_entry_authority_hash_sha256": authority_hash,
        "expected_package_new_entry_authority_hash_sha256": authority_hash,
        "package_new_entry_authority_payload_schema": (
            PACKAGE_NEW_ENTRY_AUTHORITY_PAYLOAD_SCHEMA
        ),
        "package_new_entry_authority_payload_contract": (
            PACKAGE_NEW_ENTRY_AUTHORITY_IMMUTABLE_PAYLOAD_CONTRACT
        ),
        "package_new_entry_authority_payload": payload,
        "package_new_entry_authority_scope": scope,
        "package_new_entry_authority_target_action_intent": action_intent,
        "package_new_entry_authority_authority_field": authority_field,
        "package_new_entry_authority_authority_family": "unit_test_authority",
        "package_new_entry_authority_source_boundary": source_boundary,
        "package_new_entry_authority_uses_outcome_fields": False,
        "package_new_entry_authority_candidate_id": candidate_id,
        "package_new_entry_authority_decision_time_utc": decision_time_utc,
        "package_new_entry_authority_canonical_replay_candidate_instance_key": (
            instance_key
        ),
        "package_new_entry_authority_source_bound_replay_candidate_instance_key": (
            instance_key
        ),
        "package_new_entry_authority_candidate_instance_identity_status": (
            "materialized"
        ),
        "package_new_entry_authority_selector_action": selector_action,
        "package_new_entry_authority_selector_reason": "unit_test_authority",
        "package_new_entry_authority_candidate_decision_quality": {
            "expected_net_r": 0.75,
            "probability": 0.7,
            "fill_probability": 0.8,
            "source_completeness": 1.0,
            "source_boundary": (
                "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
            ),
            "candidate_decision_quality_source_boundary": (
                "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
            ),
        },
        "package_new_entry_authority_candidate_decision_quality_field_sources": {
            **quality_field_sources,
        },
        "package_new_entry_authority_candidate_decision_quality_source_boundary": (
            quality_source_boundary
        ),
        "package_new_entry_authority_candidate_decision_quality_alias_status": (
            "exact_materialized"
        ),
        "package_new_entry_authority_candidate_decision_quality_alias_mismatches": [],
        "package_new_entry_authority_candidate_decision_quality_provenance_failures": [],
    }
    for payload_key, payload_value in payload.items():
        fields.setdefault(
            f"package_new_entry_authority_{payload_key}",
            payload_value,
        )
    return fields


def resign_signed_package_new_entry_fields(
    fields: dict,
    **payload_updates,
) -> dict:
    resigned = json.loads(json.dumps(fields))
    payload = resigned["package_new_entry_authority_payload"]
    payload.update(payload_updates)
    for payload_key, payload_value in payload_updates.items():
        projected_field = f"package_new_entry_authority_{payload_key}"
        if projected_field in resigned:
            resigned[projected_field] = payload_value
    digest = package_new_entry_authority_payload_hash_sha256(payload)
    resigned["package_new_entry_authority_hash_sha256"] = digest
    resigned["expected_package_new_entry_authority_hash_sha256"] = digest
    return resigned


def test_summary_v2_uses_full_verifier_path_and_v1_is_historical_only() -> None:
    verifier = load_verifier()

    assert (
        verifier.broad_summary_requires_immutable_package_new_entry_authority_payload(
            {}
        )
        is False
    )
    assert (
        verifier.broad_summary_package_new_entry_authority_payload_contract_issues(
            {}
        )
        == []
    )
    current_summary = {
        "schema": verifier.BROAD_REPLAY_IMMUTABLE_AUTHORITY_SUMMARY_SCHEMA,
        "package_new_entry_authority_payload_contract": (
            PACKAGE_NEW_ENTRY_AUTHORITY_IMMUTABLE_PAYLOAD_CONTRACT
        ),
        "package_new_entry_authority_payload_required_for_signed_executable_rows": True,
    }
    assert (
        verifier.broad_summary_requires_immutable_package_new_entry_authority_payload(
            current_summary
        )
        is True
    )
    assert (
        verifier.broad_summary_package_new_entry_authority_payload_contract_issues(
            current_summary
        )
        == []
    )
    assert verifier.broad_summary_requires_immutable_package_new_entry_authority_payload(
        {"schema": verifier.BROAD_REPLAY_IMMUTABLE_AUTHORITY_SUMMARY_SCHEMA}
    ) is True
    assert verifier.broad_summary_package_new_entry_authority_payload_contract_issues(
        {"schema": verifier.BROAD_REPLAY_IMMUTABLE_AUTHORITY_SUMMARY_SCHEMA}
    ) == [
        "broad_summary_package_new_entry_authority_payload_contract_invalid",
        "broad_summary_package_new_entry_authority_payload_requirement_not_true",
    ]
    assert verifier.broad_summary_full_verifier_schema_issues(current_summary) == []
    assert (
        verifier.broad_summary_verifier_mode(current_summary)
        == "current_summary_v2_full_verifier"
    )
    historical_summary = {
        "schema": verifier.BROAD_REPLAY_HISTORICAL_SUMMARY_SCHEMA,
    }
    assert verifier.broad_summary_full_verifier_schema_issues(
        historical_summary
    ) == ["package_parity_repair_summary_v1_historical_only"]
    assert (
        verifier.broad_summary_verifier_mode(historical_summary)
        == "historical_summary_v1_diagnostic_only"
    )
    assert verifier.broad_summary_package_new_entry_authority_payload_contract_issues(
        {
            "schema": verifier.BROAD_REPLAY_IMMUTABLE_AUTHORITY_SUMMARY_SCHEMA,
            "package_new_entry_authority_payload_contract": "unknown_contract",
            "package_new_entry_authority_payload_required_for_signed_executable_rows": False,
        }
    ) == [
        "broad_summary_package_new_entry_authority_payload_contract_invalid",
        "broad_summary_package_new_entry_authority_payload_requirement_not_true",
    ]


def test_signed_authority_payload_recomputes_hash_and_binds_same_instance() -> None:
    verifier = load_verifier()
    decision_time = "2026-05-13T08:30:00+00:00"
    candidate_id = "immutable-authority-candidate"
    row = {
        "candidate_id": candidate_id,
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "source_bound_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "selector_action": "open-reduced-risk",
        "scheduler_materialization_action_intent": "new_position",
        **signed_package_new_entry_fields(
            candidate_id=candidate_id,
            decision_time_utc=decision_time,
            selector_action="open-reduced-risk",
        ),
    }
    assert verifier.signed_package_new_entry_authority_reasons(
        row,
        action_intent="new_position",
        require_immutable_payload=True,
    ) == []

    tampered = dict(row)
    tampered_payload = dict(row["package_new_entry_authority_payload"])
    tampered_payload["candidate_id"] = "borrowed-candidate"
    tampered["package_new_entry_authority_payload"] = tampered_payload
    reasons = verifier.signed_package_new_entry_authority_reasons(
        tampered,
        action_intent="new_position",
        require_immutable_payload=True,
    )
    assert "package_new_entry_authority_payload_hash_mismatch" in reasons
    assert (
        "package_new_entry_authority_payload_candidate_id_projection_mismatch"
        in reasons
    )
    assert "package_new_entry_authority_payload_candidate_id_mismatch" in reasons


def test_flat_namespaced_signed_authorities_validate_independently() -> None:
    verifier = load_verifier()
    row: dict = {}
    expected_candidates = {
        "scorecard_reported": "scorecard-flat-authority",
        "finalizer_primary_probe": "finalizer-flat-authority",
    }
    for namespace, candidate_id in expected_candidates.items():
        decision_time = "2026-05-13T08:30:00+00:00"
        fields = signed_package_new_entry_fields(
            candidate_id=candidate_id,
            decision_time_utc=decision_time,
        )
        row.update(
            {
                f"{namespace}_{field}": value
                for field, value in fields.items()
            }
        )

    records = verifier.package_new_entry_authority_flat_namespace_contract_records(
        row
    )

    assert {record["source"] for record in records} == {
        "flat_namespace:scorecard_reported",
        "flat_namespace:finalizer_primary_probe",
    }
    assert all(record["claim_bearing"] is True for record in records)
    assert all(record["valid"] is True for record in records)
    assert {
        record["surface"]["package_new_entry_authority_candidate_id"]
        for record in records
    } == set(expected_candidates.values())


def test_flat_namespaced_signed_authority_rejects_payload_tamper() -> None:
    verifier = load_verifier()
    fields = signed_package_new_entry_fields(
        candidate_id="tampered-flat-authority",
        decision_time_utc="2026-05-13T08:30:00+00:00",
    )
    row = {f"scorecard_reported_{field}": value for field, value in fields.items()}
    row[
        "scorecard_reported_package_new_entry_authority_payload"
    ]["expected_net_r"] = 9.0

    records = verifier.package_new_entry_authority_flat_namespace_contract_records(
        row
    )

    assert len(records) == 1
    assert records[0]["valid"] is False
    assert "package_new_entry_authority_payload_hash_mismatch" in records[0][
        "reasons"
    ]


def test_flat_namespaced_authority_repairs_only_hash_bound_empty_projections() -> None:
    verifier = load_verifier()
    fields = signed_package_new_entry_fields(
        candidate_id="legacy-empty-projection-authority",
        decision_time_utc="2026-05-13T08:30:00+00:00",
    )
    fields["package_new_entry_authority_payload"][
        "source_bound_router_refusal_materialization_floors"
    ] = {}
    digest = package_new_entry_authority_payload_hash_sha256(
        fields["package_new_entry_authority_payload"]
    )
    fields["package_new_entry_authority_hash_sha256"] = digest
    fields["expected_package_new_entry_authority_hash_sha256"] = digest
    omitted_fields = (
        "package_new_entry_authority_candidate_decision_quality_alias_mismatches",
        "package_new_entry_authority_candidate_decision_quality_provenance_failures",
        "package_new_entry_authority_source_bound_router_refusal_materialization_floors",
    )
    for field in omitted_fields:
        fields.pop(field, None)
    row = {f"scorecard_reported_{field}": value for field, value in fields.items()}

    records = verifier.package_new_entry_authority_flat_namespace_contract_records(
        row
    )

    assert len(records) == 1
    assert records[0]["valid"] is True
    assert set(records[0]["hash_bound_empty_projection_repairs"]) >= set(
        omitted_fields
    )


def test_flat_namespaced_authorities_reject_distinct_hashes_for_same_instance() -> None:
    verifier = load_verifier()
    fields = signed_package_new_entry_fields(
        candidate_id="same-instance-flat-authority",
        decision_time_utc="2026-05-13T08:30:00+00:00",
    )
    revised_fields = resign_signed_package_new_entry_fields(
        fields,
        expected_net_r=0.9,
    )
    row = {
        **{f"scorecard_reported_{field}": value for field, value in fields.items()},
        **{
            f"risk_finalizer_best_package_probe_{field}": value
            for field, value in revised_fields.items()
        },
    }

    records = verifier.package_new_entry_authority_flat_namespace_contract_records(
        row
    )

    assert len(records) == 2
    assert all(record["valid"] is False for record in records)
    assert all(
        any(
            reason.startswith(
                "conflicting_flat_namespace_authority_envelopes_same_candidate_instance:"
            )
            for reason in record["reasons"]
        )
        for record in records
    )


def test_flat_namespaced_authority_keeps_scorecard_decision_time_binding() -> None:
    verifier = load_verifier()
    fields = signed_package_new_entry_fields(
        candidate_id="decision-time-flat-authority",
        decision_time_utc="2026-05-13T08:45:00+00:00",
    )
    row = {
        "decision_time_utc": "2026-05-13T08:30:00+00:00",
        **{f"scorecard_reported_{field}": value for field, value in fields.items()},
    }

    records = verifier.package_new_entry_authority_flat_namespace_contract_records(
        row
    )

    assert len(records) == 1
    assert records[0]["valid"] is False
    assert "package_new_entry_authority_payload_decision_time_utc_mismatch" in (
        records[0]["reasons"]
    )


def test_emitted_scheduler_scan_accepts_terminal_zero_trade_namespaced_proof(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    decision_time = "2026-05-13T08:30:00+00:00"
    fields = signed_package_new_entry_fields(
        candidate_id="route-scan-flat-authority",
        decision_time_utc=decision_time,
    )
    row = {
        "decision_time_utc": decision_time,
        "selected_action_class": "zero_trade",
        "effective_action_intent": "new_position",
        "selector_action": "reduce-risk",
        "effective_risk_decision": "reject",
        "executable_finalized": False,
        "risk_finalizer_executable_finalized": False,
        "package_replay_executable_candidate_use_allowed": False,
        "package_replay_order_executable_candidate_use_allowed": False,
        **{f"scorecard_reported_{field}": value for field, value in fields.items()},
    }
    path = tmp_path / "scorecard.jsonl"
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")

    scan = verifier.scan_broad_emitted_scheduler_status_authority(
        {"scorecard": path},
        require_immutable_payload=True,
    )

    assert scan["bad_counts"] == {}
    assert scan["row_counts"]["scorecard_namespaced_authority_claim_rows"] == 1
    assert scan["row_counts"]["scorecard_namespaced_authority_valid_rows"] == 1
    assert scan["row_counts"][
        "scorecard_selector_reduce_risk_diagnostic_non_executable_rows"
    ] == 1


def test_current_authority_payload_rejects_deletion_of_every_required_atom() -> None:
    verifier = load_verifier()
    candidate_id = "atom-complete-authority"
    decision_time = "2026-05-13T08:30:00+00:00"
    base = {
        "candidate_id": candidate_id,
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "source_bound_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "selector_action": "open-reduced-risk",
        "scheduler_materialization_action_intent": "new_position",
        **signed_package_new_entry_fields(
            candidate_id=candidate_id,
            decision_time_utc=decision_time,
            selector_action="open-reduced-risk",
        ),
    }

    for atom_class, atom_fields in (
        verifier.PACKAGE_NEW_ENTRY_AUTHORITY_REQUIRED_PAYLOAD_ATOMS.items()
    ):
        for atom_field in atom_fields:
            row = json.loads(json.dumps(base))
            payload = row["package_new_entry_authority_payload"]
            del payload[atom_field]
            digest = package_new_entry_authority_payload_hash_sha256(payload)
            row["package_new_entry_authority_hash_sha256"] = digest
            row["expected_package_new_entry_authority_hash_sha256"] = digest

            reasons = verifier.signed_package_new_entry_authority_reasons(
                row,
                action_intent="new_position",
            )

            expected = (
                "package_new_entry_authority_payload_atom_missing:"
                f"{atom_class}:{atom_field}"
            )
            assert any(
                reason == expected or reason.endswith(f":{expected}")
                for reason in reasons
            ), (
                atom_class,
                atom_field,
                reasons,
            )


@pytest.mark.parametrize(
    ("source_time", "expected_reason"),
    (
        (
            None,
            "package_new_entry_authority_payload_fill_source_time_invalid",
        ),
        (
            "2026-05-13T08:30:00+00:00",
            "package_new_entry_authority_payload_fill_source_time_not_before_decision",
        ),
        (
            "2026-05-13T08:30:01+00:00",
            "package_new_entry_authority_payload_fill_source_time_not_before_decision",
        ),
    ),
    ids=("missing", "equal", "future"),
)
def test_current_authority_payload_rejects_non_strict_fillability_source_time(
    source_time: str | None,
    expected_reason: str,
) -> None:
    verifier = load_verifier()
    candidate_id = "authority-fillability-time-equality"
    decision_time = "2026-05-13T08:30:00+00:00"
    row = {
        "candidate_id": candidate_id,
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "source_bound_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "selector_action": "open-reduced-risk",
        "scheduler_materialization_action_intent": "new_position",
        **signed_package_new_entry_fields(
            candidate_id=candidate_id,
            decision_time_utc=decision_time,
            selector_action="open-reduced-risk",
        ),
    }
    payload = dict(row["package_new_entry_authority_payload"])
    if source_time is None:
        payload.pop("execution_fill_probability_source_time_utc")
    else:
        payload["execution_fill_probability_source_time_utc"] = source_time
    digest = package_new_entry_authority_payload_hash_sha256(payload)
    row["package_new_entry_authority_payload"] = payload
    row["package_new_entry_authority_hash_sha256"] = digest
    row["expected_package_new_entry_authority_hash_sha256"] = digest
    projected = "package_new_entry_authority_execution_fill_probability_source_time_utc"
    if source_time is None:
        row.pop(projected)
    else:
        row[projected] = source_time

    reasons = verifier.signed_package_new_entry_authority_reasons(
        row,
        action_intent="new_position",
    )

    assert expected_reason in reasons


@pytest.mark.parametrize(
    "authority_class",
    (None, "heuristic_execution_fillability"),
    ids=("missing", "unsafe"),
)
def test_current_authority_payload_requires_signed_fillability_authority_class(
    authority_class: str | None,
) -> None:
    verifier = load_verifier()
    candidate_id = "authority-fillability-class"
    decision_time = "2026-05-13T08:30:00+00:00"
    row = {
        "candidate_id": candidate_id,
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "source_bound_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "selector_action": "open-reduced-risk",
        "scheduler_materialization_action_intent": "new_position",
        **signed_package_new_entry_fields(
            candidate_id=candidate_id,
            decision_time_utc=decision_time,
            selector_action="open-reduced-risk",
        ),
    }
    payload = dict(row["package_new_entry_authority_payload"])
    projected = (
        "package_new_entry_authority_"
        "execution_fill_probability_authority_class"
    )
    if authority_class is None:
        payload.pop("execution_fill_probability_authority_class")
        row.pop(projected)
    else:
        payload["execution_fill_probability_authority_class"] = authority_class
        row[projected] = authority_class
    digest = package_new_entry_authority_payload_hash_sha256(payload)
    row["package_new_entry_authority_payload"] = payload
    row["package_new_entry_authority_hash_sha256"] = digest
    row["expected_package_new_entry_authority_hash_sha256"] = digest

    reasons = verifier.signed_package_new_entry_authority_reasons(
        row,
        action_intent="new_position",
    )

    assert (
        "package_new_entry_authority_payload_fill_authority_class_invalid"
        in reasons
    )


@pytest.mark.parametrize(
    "source_boundary",
    (
        "predecision_future_no_outcome_fields",
        "predecision_inferred_no_outcome_fields",
        "predecision_fallback_no_outcome_fields",
        "predecision_generic_no_outcome_fields",
        "predecision_model_no_outcome_fields",
        "predecision_unknown_no_outcome_fields",
        "predecision_postdecision_no_outcome_fields",
        "predecision_outcome_fields",
    ),
    ids=(
        "future",
        "inferred",
        "fallback",
        "generic",
        "model",
        "unknown",
        "postdecision",
        "outcome",
    ),
)
def test_current_authority_payload_rejects_unsafe_fillability_boundary_markers(
    source_boundary: str,
) -> None:
    verifier = load_verifier()
    candidate_id = "authority-fillability-boundary"
    decision_time = "2026-05-13T08:30:00+00:00"
    row = {
        "candidate_id": candidate_id,
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "source_bound_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "selector_action": "open-reduced-risk",
        "scheduler_materialization_action_intent": "new_position",
        **signed_package_new_entry_fields(
            candidate_id=candidate_id,
            decision_time_utc=decision_time,
            selector_action="open-reduced-risk",
        ),
    }
    row = resign_signed_package_new_entry_fields(
        row,
        execution_fill_probability_source_boundary=source_boundary,
    )

    reasons = verifier.signed_package_new_entry_authority_reasons(
        row,
        action_intent="new_position",
    )

    assert (
        "package_new_entry_authority_payload."
        "execution_fill_probability_source_boundary_unsafe"
        in reasons
    )


def test_current_authority_payload_rejects_missing_fillability_boundary() -> None:
    verifier = load_verifier()
    candidate_id = "authority-fillability-boundary-missing"
    decision_time = "2026-05-13T08:30:00+00:00"
    row = {
        "candidate_id": candidate_id,
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "source_bound_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "selector_action": "open-reduced-risk",
        "scheduler_materialization_action_intent": "new_position",
        **signed_package_new_entry_fields(
            candidate_id=candidate_id,
            decision_time_utc=decision_time,
            selector_action="open-reduced-risk",
        ),
    }
    payload = dict(row["package_new_entry_authority_payload"])
    payload.pop("execution_fill_probability_source_boundary")
    digest = package_new_entry_authority_payload_hash_sha256(payload)
    row["package_new_entry_authority_payload"] = payload
    row["package_new_entry_authority_hash_sha256"] = digest
    row["expected_package_new_entry_authority_hash_sha256"] = digest
    row.pop("package_new_entry_authority_execution_fill_probability_source_boundary")

    reasons = verifier.signed_package_new_entry_authority_reasons(
        row,
        action_intent="new_position",
    )

    assert (
        "package_new_entry_authority_payload."
        "execution_fill_probability_source_boundary_missing"
        in reasons
    )


@pytest.mark.parametrize(
    "member_axis_ids",
    (
        (),
        ("unknown",),
        ("member_axis:duplicate", "member_axis:duplicate"),
        ("member_axis:z", "member_axis:a"),
        ("1",),
    ),
    ids=("empty", "sentinel", "duplicate", "unsorted", "numeric"),
)
def test_current_authority_payload_requires_canonical_nonempty_member_axis_ids(
    member_axis_ids: tuple[str, ...],
) -> None:
    verifier = load_verifier()
    candidate_id = "authority-member-axis-canonicality"
    decision_time = "2026-05-13T08:30:00+00:00"
    row = {
        "candidate_id": candidate_id,
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "source_bound_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "selector_action": "open-reduced-risk",
        "scheduler_materialization_action_intent": "new_position",
        **signed_package_new_entry_fields(
            candidate_id=candidate_id,
            decision_time_utc=decision_time,
            selector_action="open-reduced-risk",
            matched_member_axis_ids=member_axis_ids,
        ),
    }

    reasons = verifier.signed_package_new_entry_authority_reasons(
        row,
        action_intent="new_position",
    )

    assert (
        "package_new_entry_authority_payload_"
        "matched_member_axis_ids_not_canonical_nonempty"
        in reasons
    )


def test_current_authority_envelope_never_merges_root_and_nested_surfaces() -> None:
    verifier = load_verifier()
    decision_time = "2026-05-13T08:30:00+00:00"
    candidate_id = "root-envelope-candidate"
    row = {
        "candidate_id": candidate_id,
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "source_bound_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "selector_action": "open-reduced-risk",
        "scheduler_materialization_action_intent": "new_position",
        **signed_package_new_entry_fields(
            candidate_id=candidate_id,
            decision_time_utc=decision_time,
            selector_action="open-reduced-risk",
        ),
    }
    row.pop("package_new_entry_authority_authority_field")
    nested_candidate = "nested-envelope-candidate"
    row["ultimate_candidate_package_open_reduced_risk_authority"] = (
        signed_package_new_entry_fields(
            candidate_id=nested_candidate,
            decision_time_utc=decision_time,
            selector_action="open-reduced-risk",
        )
    )

    selection = verifier.package_new_entry_authority_envelope_selection(
        row,
        action_intent="new_position",
    )

    assert selection["valid"] is False
    assert selection["status"] == "conflicting_current_authority_envelopes"
    assert selection["reasons"] == ["mixed_current_authority_envelope_payloads"]

    split = json.loads(json.dumps(row))
    split.pop("ultimate_candidate_package_open_reduced_risk_authority")
    moved_projection = split.pop("package_new_entry_authority_cost_authority")
    split["ultimate_candidate_package_open_reduced_risk_authority"] = {
        "package_new_entry_authority_cost_authority": moved_projection,
    }
    split_selection = verifier.package_new_entry_authority_envelope_selection(
        split,
        action_intent="new_position",
    )
    assert split_selection["valid"] is False
    assert any(
        "cost_authority" in reason and "projection" in reason
        for reason in split_selection["reasons"]
    )


def test_current_authority_envelope_prefers_explicit_valid_nested_surface() -> None:
    verifier = load_verifier()
    candidate_id = "explicit-nested-authority"
    decision_time = "2026-05-13T08:30:00+00:00"
    selected_field = "ultimate_candidate_package_reduce_risk_authority"
    selected = resign_signed_package_new_entry_fields(
        signed_package_new_entry_fields(
            candidate_id=candidate_id,
            decision_time_utc=decision_time,
            selector_action="reduce-risk",
        ),
        authority_family="selected_current_authority",
    )
    stale_root = resign_signed_package_new_entry_fields(
        signed_package_new_entry_fields(
            candidate_id=candidate_id,
            decision_time_utc=decision_time,
            selector_action="reduce-risk",
        ),
        authority_family="stale_root_authority",
    )
    stale_root["package_new_entry_authority_payload"]["expected_net_r"] = -9.0
    stale_other = resign_signed_package_new_entry_fields(
        signed_package_new_entry_fields(
            candidate_id=candidate_id,
            decision_time_utc=decision_time,
            selector_action="open-reduced-risk",
        ),
        authority_family="stale_other_authority",
    )
    stale_other["package_new_entry_authority_payload"]["probability"] = -1.0
    row = {
        "candidate_id": candidate_id,
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "source_bound_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "selector_action": "reduce-risk",
        "scheduler_materialization_action_intent": "new_position",
        **stale_root,
        "package_new_entry_authority_authority_field": selected_field,
        selected_field: selected,
        "ultimate_candidate_package_open_reduced_risk_authority": stale_other,
    }

    selection = verifier.package_new_entry_authority_envelope_selection(
        row,
        action_intent="new_position",
    )

    assert selection["valid"] is True
    assert selection["source"] == selected_field
    assert selection["selection_basis"] == "explicit_nested_authority_field"
    assert selection["digest"] == selected[
        "package_new_entry_authority_hash_sha256"
    ]


def test_current_authority_envelope_explicit_invalid_surface_fails_closed() -> None:
    verifier = load_verifier()
    candidate_id = "explicit-invalid-authority"
    decision_time = "2026-05-13T08:30:00+00:00"
    selected_field = "ultimate_candidate_package_reduce_risk_authority"
    valid_fallback = signed_package_new_entry_fields(
        candidate_id=candidate_id,
        decision_time_utc=decision_time,
        selector_action="reduce-risk",
    )
    invalid_selected = json.loads(json.dumps(valid_fallback))
    invalid_selected["package_new_entry_authority_payload"]["expected_net_r"] = -7.0
    row = {
        "candidate_id": candidate_id,
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "source_bound_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "selector_action": "reduce-risk",
        "scheduler_materialization_action_intent": "new_position",
        **valid_fallback,
        selected_field: invalid_selected,
    }

    selection = verifier.package_new_entry_authority_envelope_selection(
        row,
        action_intent="new_position",
    )

    assert selection["valid"] is False
    assert selection["status"] == "explicitly_designated_authority_envelope_invalid"
    assert selection["designated_source"] == selected_field
    assert any("payload_hash_mismatch" in reason for reason in selection["reasons"])

    for malformed_surface in ({}, "not-an-authority-envelope"):
        malformed_row = {**row, selected_field: malformed_surface}
        malformed_selection = (
            verifier.package_new_entry_authority_envelope_selection(
                malformed_row,
                action_intent="new_position",
            )
        )
        assert malformed_selection["valid"] is False
        assert malformed_selection["status"] == (
            "explicitly_designated_authority_envelope_invalid"
        )


def test_current_authority_envelope_rejects_unselected_distinct_valid_hash() -> None:
    verifier = load_verifier()
    candidate_id = "explicit-multi-hash-authority"
    decision_time = "2026-05-13T08:30:00+00:00"
    selected_field = "ultimate_candidate_package_reduce_risk_authority"
    selected = resign_signed_package_new_entry_fields(
        signed_package_new_entry_fields(
            candidate_id=candidate_id,
            decision_time_utc=decision_time,
            selector_action="reduce-risk",
        ),
        authority_family="selected_hash",
    )
    unselected = resign_signed_package_new_entry_fields(
        signed_package_new_entry_fields(
            candidate_id=candidate_id,
            decision_time_utc=decision_time,
            selector_action="open-reduced-risk",
        ),
        authority_family="unselected_distinct_hash",
    )
    row = {
        "candidate_id": candidate_id,
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "source_bound_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "selector_action": "reduce-risk",
        "scheduler_materialization_action_intent": "new_position",
        "package_new_entry_authority_authority_field": selected_field,
        selected_field: selected,
        "ultimate_candidate_package_open_reduced_risk_authority": unselected,
    }

    selection = verifier.package_new_entry_authority_envelope_selection(
        row,
        action_intent="new_position",
    )

    assert selection["valid"] is False
    assert selection["status"] == "conflicting_current_authority_envelopes"
    assert selection["reasons"] == [
        "multiple_distinct_current_authority_envelopes"
    ]


def test_signed_authority_payload_legacy_compatibility_is_not_new_run_authority() -> None:
    verifier = load_verifier()
    decision_time = "2026-05-13T08:30:00+00:00"
    candidate_id = "legacy-authority-candidate"
    row = {
        "candidate_id": candidate_id,
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "source_bound_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "selector_action": "open-reduced-risk",
        "scheduler_materialization_action_intent": "new_position",
        **signed_package_new_entry_fields(
            candidate_id=candidate_id,
            decision_time_utc=decision_time,
            selector_action="open-reduced-risk",
        ),
    }
    row.pop("package_new_entry_authority_payload")
    row.pop("package_new_entry_authority_payload_contract")

    reasons = verifier.signed_package_new_entry_authority_reasons(
        row,
        action_intent="new_position",
    )
    assert any(
        reason == "package_new_entry_authority_payload_missing"
        or reason.endswith(":package_new_entry_authority_payload_missing")
        for reason in reasons
    )
    assert verifier.package_new_entry_authority_envelope_selection(
        row,
        action_intent="new_position",
    )["status"] == "legacy_or_hash_only_authority_diagnostic_only"


def test_replace_pending_signed_authority_cannot_escape_immutable_payload_scan(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    decision_time = "2026-05-13T08:30:00+00:00"
    candidate_id = "replace-pending-legacy-authority"
    row = {
        "candidate_id": candidate_id,
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "source_bound_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "selector_action": "open-reduced-risk",
        "scheduler_materialization_selector_action": "open-reduced-risk",
        "scheduler_materialization_action_intent": "replace_pending",
        "ultimate_candidate_package_open_reduced_risk_authority": {
            "allowed": True,
            "authority_family": "unit_test_authority",
        },
        "package_replay_executable_candidate_use_allowed": True,
        "package_replay_order_executable_candidate_use_allowed": True,
        "approved_risk_pct": 0.25,
        "simulated_order_id": "replace-pending-order",
        "order_status": "pending_accepted",
        **signed_package_new_entry_fields(
            candidate_id=candidate_id,
            decision_time_utc=decision_time,
            action_intent="replace_pending",
            selector_action="open-reduced-risk",
        ),
    }
    row.pop("package_new_entry_authority_payload")
    row.pop("package_new_entry_authority_payload_contract")
    order_path = tmp_path / "ORDER_LEDGER.jsonl"
    write_jsonl(order_path, [row])

    scan = verifier.scan_broad_emitted_scheduler_status_authority(
        {"order": order_path},
        require_immutable_payload=True,
    )

    assert scan["bad_counts"][
        "order:selector_open_reduced_risk_signed_authority_invalid"
    ] == 1
    assert any(
        "package_new_entry_authority_payload_missing" in reason
        for reason in scan["sample_bad"][0]["reasons"]
    )


def v220_hard_clean_capped_verifier_row() -> dict:
    candidate_id = "candidate-v220-hard-clean-capped"
    decision_time = "2026-05-13T08:00:00+00:00"
    instance_key = f"{candidate_id}@@{decision_time}"
    boundary = (
        "predecision_signed_package_soft_transfer_quality_cost_source_order_no_outcome_fields"
    )
    return {
        "candidate_id": candidate_id,
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": instance_key,
        "risk_finalizer_probe_instance_key": instance_key,
        "source_bound_replay_candidate_instance_key": instance_key,
        "candidate_instance_identity_status": "materialized",
        "selector_action": "open-reduced-risk",
        "selector_reason": "unit_test_authority",
        "scheduler_materialization_action_intent": "new_position",
        "scheduler_materialization_skip_reason": (
            "reallocation_quality_score_below_floor"
        ),
        "package_replay_order_executable_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed": True,
        "package_replay_order_executable_final_blocker_class": (
            "selector_materialization"
        ),
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "candidate_cost_r_fallback_is_authority": False,
        "source_gap_cost_fallback_blocked": False,
        "source_completeness": 1.0,
        "source_completeness_status": "complete",
        "predecision_stop_hazard_guard_status": "capped",
        "predecision_stop_hazard_guard_action": "cap",
        "predecision_stop_hazard_guard_risk_cap_applied": True,
        "package_risk_expression_full_risk_allowed": False,
        "package_risk_expression_full_risk_applied": False,
        "broker_order_lifecycle_truth_satisfied": False,
        "same_symbol_lifecycle_permitted": True,
        "terminal_vetoes": [],
        "risk_finalizer_signed_soft_transfer_displacement_allowed": True,
        "risk_finalizer_signed_soft_transfer_displacement_source_boundary": boundary,
        "risk_finalizer_signed_soft_transfer_displacement_uses_outcome_fields": False,
        "finalizer_admission_rank_reason": (
            "risk_admitted_signed_soft_transfer_displacement_rank"
        ),
        "selected_policy_executable_quality_reallocation_score": -1.05,
        "selected_policy_executable_quality_min_reallocation_quality_score": 0.0,
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
                "predecision_expected_transfer_plus_pending_replacement_quality_"
                "no_outcome_fields"
            ),
            "uses_outcome_fields": False,
        },
        **signed_package_new_entry_fields(
            candidate_id=candidate_id,
            decision_time_utc=decision_time,
            selector_action="open-reduced-risk",
        ),
    }


def test_scorecard_signed_authority_accepts_scheduler_identity_over_selected_candidate(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    scorecard_path = tmp_path / "SCORECARD_LEDGER.jsonl"
    decision_time = "2026-05-14T07:30:00+00:00"
    signed_id = "scheduler-signed-candidate"
    fallback_selected_id = "finalizer-fallback-candidate"
    row = {
        "selected_candidate_id": fallback_selected_id,
        "selected_scheduler_primary_candidate_id": signed_id,
        "canonical_replay_candidate_instance_key": f"{signed_id}@@{decision_time}",
        "selected_scheduler_canonical_replay_candidate_instance_key": (
            f"{signed_id}@@{decision_time}"
        ),
        "source_bound_replay_candidate_instance_key": f"{signed_id}@@{decision_time}",
        "decision_time_utc": decision_time,
        "selector_action": "open-reduced-risk",
        "scheduler_materialization_action_intent": "new_position",
        "package_replay_order_executable_transfer_status": "final_blocked",
        "package_replay_order_executable_final_blocker_class": "fill_realism",
        "package_replay_order_executable_final_blocker_reason": (
            "selector_open_reduced_risk_origin_preserved_after_runtime_risk_reduction"
        ),
        **signed_package_new_entry_fields(
            candidate_id=signed_id,
            decision_time_utc=decision_time,
            selector_action="open-reduced-risk",
        ),
    }
    write_jsonl(scorecard_path, [row])

    scan = verifier.scan_broad_emitted_scheduler_status_authority(
        {"scorecard": scorecard_path}
    )

    assert scan["bad_counts"] == {}


def test_scorecard_signed_authority_uses_effective_action_intent(tmp_path: Path) -> None:
    verifier = load_verifier()
    scorecard_path = tmp_path / "SCORECARD_LEDGER.jsonl"
    decision_time = "2026-05-13T15:30:00+00:00"
    candidate_id = "close-reverse-signed-probe"
    row = {
        "candidate_id": None,
        "selected_candidate_id": None,
        "canonical_replay_candidate_instance_key": None,
        "decision_time_utc": decision_time,
        "selector_action": "open-reduced-risk",
        "effective_selector_action": "open-reduced-risk",
        "effective_action_intent": "close_and_reverse",
        "package_replay_order_executable_transfer_status": "final_blocked",
        "package_replay_order_executable_final_blocker_class": "risk_finalizer",
        "package_replay_order_executable_final_blocker_reason": (
            "pre_order_materialization_preflight_blocked"
        ),
        "executable_finalized": False,
        **signed_package_new_entry_fields(
            candidate_id=candidate_id,
            decision_time_utc=decision_time,
            action_intent="close_and_reverse",
            selector_action="open-reduced-risk",
        ),
    }
    write_jsonl(scorecard_path, [row])

    scan = verifier.scan_broad_emitted_scheduler_status_authority(
        {"scorecard": scorecard_path}
    )

    assert scan["bad_counts"] == {}


def test_scorecard_final_blocked_signed_probe_identity_is_projection_not_row_identity(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    scorecard_path = tmp_path / "SCORECARD_LEDGER.jsonl"
    decision_time = "2026-05-14T13:45:00+00:00"
    reduce_id = "reduce-risk-signed-probe"
    open_id = "open-reduced-signed-probe"
    base = {
        "selected_candidate_id": None,
        "selected_candidate_ids": [],
        "decision_time_utc": decision_time,
        "package_replay_order_executable_transfer_status": "final_blocked",
        "package_replay_order_executable_final_blocker_class": "daily_lockout",
        "package_replay_order_executable_final_blocker_reason": (
            "same_symbol_daily_loss_lockout_after_closed_trade"
        ),
    }
    reduce_row = {
        **base,
        "selector_action": "reduce-risk",
        "scorecard_reported_candidate_id": "different-window-probe",
        "scorecard_reported_canonical_replay_candidate_instance_key": (
            f"different-window-probe@@{decision_time}"
        ),
        **signed_package_new_entry_fields(
            candidate_id=reduce_id,
            decision_time_utc=decision_time,
            selector_action="reduce-risk",
        ),
    }
    open_row = {
        **base,
        "selector_action": "open-reduced-risk",
        **signed_package_new_entry_fields(
            candidate_id=open_id,
            decision_time_utc=decision_time,
            selector_action="open-reduced-risk",
        ),
    }
    write_jsonl(scorecard_path, [reduce_row, open_row])

    scan = verifier.scan_broad_emitted_scheduler_status_authority(
        {"scorecard": scorecard_path}
    )

    assert scan["bad_counts"] == {}


def test_compact_order_terminal_resolution_scan_flags_pending_and_fallback_leaks() -> None:
    verifier = load_verifier()

    scan = verifier.scan_compact_order_terminal_resolution_and_fallback_provenance(
        [
            {
                "simulated_order_id": "order-ok",
                "order_status": "pending_accepted",
                "is_terminal_order_event": False,
                "terminal_resolution_required": True,
            },
            {
                "simulated_order_id": "order-ok",
                "order_status": "filled",
                "is_terminal_order_event": True,
                "terminal_resolution_order_id": "order-ok",
                "terminal_resolution_status": "resolved_filled",
            },
            {
                "simulated_order_id": "order-missing-terminal",
                "order_status": "pending_accepted",
            },
            {
                "simulated_order_id": "order-duplicate-terminal",
                "order_status": "pending_accepted",
            },
            {
                "simulated_order_id": "order-duplicate-terminal",
                "order_status": "expired_unfilled",
            },
            {
                "simulated_order_id": "order-duplicate-terminal",
                "order_status": "filled",
            },
            {
                "simulated_order_id": "order-terminal-field-bad",
                "order_status": "filled",
                "is_terminal_order_event": False,
                "terminal_resolution_order_id": "different-order",
                "terminal_resolution_status": "pending_terminal_resolution_required",
            },
            {
                "simulated_order_id": "order-adverse-bad",
                "order_status": "expired_unfilled",
                "guarded_market_fallback_reason": (
                    "fallback_entry_adverse_drift_above_thesis_geometry_ceiling"
                ),
                "fallback_decision_used_elapsed_market_path": False,
            },
            {
                "simulated_order_id": "order-fallback-predecision-bad",
                "order_status": "expired_unfilled",
                "guarded_market_fallback_reason": (
                    "fallback_entry_adverse_drift_above_thesis_geometry_ceiling"
                ),
                "fallback_decision_used_elapsed_market_path": True,
                "guarded_market_fallback_used_only_predecision_fields": True,
            },
        ]
    )

    assert scan["bad_counts"]["pending_without_terminal_resolution"] == 1
    assert scan["bad_counts"]["pending_multiple_terminal_resolution"] == 1
    assert scan["bad_counts"]["duplicate_terminal_order_id"] == 1
    assert scan["bad_counts"]["terminal_field_mismatch"] == 3
    assert scan["bad_counts"]["adverse_drift_missing_elapsed_path_flag"] == 1
    assert scan["bad_counts"]["fallback_elapsed_path_claimed_predecision_only"] == 1


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def write_completed_broad_quality_family(module, route: Path, prefix: str) -> None:
    tag = module.broad_quality_artifact_tag(prefix)
    summary = {
        "status": "broad_live_as_if_replay_materialized_broker_live_closed",
        "candidate_rows": 1,
        "order_rows": 1,
        "oracle_rows": 1,
        "trade_rows": 1,
        "live_broker_authority": False,
        "broker_mutation_enabled": False,
        "final_selection_claim": False,
    }
    if hasattr(module, "broad_quality_artifact_paths"):
        artifact_paths = list(module.broad_quality_artifact_paths(prefix, tag).items())
    else:
        artifact_paths = [
            ("summary", route / f"{prefix}_SUMMARY.json"),
            ("candidate", route / f"{prefix}_CANDIDATE_LEDGER.jsonl"),
            ("packet_sidecar", route / f"{prefix}_PACKET_SIDECAR_LEDGER.jsonl"),
        ]
    for name, path in artifact_paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        if name == "summary":
            path.write_text(json.dumps(summary), encoding="utf-8")
        elif path.suffix == ".json":
            path.write_text("{}", encoding="utf-8")
        else:
            path.write_text(json.dumps({"candidate_id": prefix}) + "\n", encoding="utf-8")
    if hasattr(module, "broad_quality_required_manifest_files"):
        for filename in module.broad_quality_required_manifest_files(prefix, tag):
            path = route / filename
            if path.exists():
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.suffix == ".json":
                path.write_text("{}", encoding="utf-8")
            elif path.suffix == ".md":
                path.write_text("placeholder\n", encoding="utf-8")
            else:
                path.write_text(json.dumps({"candidate_id": prefix}) + "\n", encoding="utf-8")


def test_denominator_builder_compact_candidate_normalizes_geometry_and_skip_authority() -> None:
    builder = load_builder()

    row = builder.compact_replay_candidate_row(
        {
            "candidate_id": "compact-geometry-fixture",
            "symbol": "XAUUSD",
            "side": "LONG",
            "decision_time_utc": "2026-05-05T00:15:00+00:00",
            "entry_price": 100.0,
            "stop_loss": 99.0,
            "take_profit_1": 102.0,
            "trade_parameters": {
                "entry_price": 100.0,
                "stop_loss": 99.0,
                "take_profit_1": 102.0,
                "target_reference": 102.0,
                "risk_reward_ratio": 2.0,
            },
            "package_replay_executable_candidate_use_allowed": True,
            "replay_candidate_use_allowed_now": True,
            "scheduler_materialization_skip_reason": "fixture_skip",
        },
        bridge_row=None,
        source_namespace="fixture",
    )

    assert row["target_reference"] == 102.0
    assert row["risk_reward_ratio"] == 2.0
    assert row["canonical_geometry_status"] == "canonicalized"
    assert row["package_replay_candidate_use_allowed"] is False
    assert row["package_replay_executable_candidate_use_allowed"] is False
    assert row["replay_candidate_use_allowed_now"] is False
    assert (
        row["package_replay_executable_candidate_use_allowed_reason"]
        == "scheduler_materialization_skipped:fixture_skip"
    )


def test_denominator_builder_compact_candidate_demotes_hash_only_package_authority() -> None:
    builder = load_builder()

    row = builder.compact_replay_candidate_row(
        {
            "candidate_id": "compact-package-contract-fixture",
            "symbol": "XAUUSD",
            "side": "LONG",
            "decision_time_utc": "2026-05-05T00:15:00+00:00",
            "entry_price": 100.0,
            "stop_loss": 99.0,
            "take_profit_1": 102.0,
            "trade_parameters": {
                "entry_price": 100.0,
                "stop_loss": 99.0,
                "take_profit_1": 102.0,
                "target_reference": 102.0,
                "risk_reward_ratio": 2.0,
            },
            "selected_package_replay_row": True,
            "ultimate_candidate_package_packet_hash_sha256": "packet-hash",
            "ultimate_candidate_package_packet_shape_hash_sha256": "shape-hash",
            "package_new_entry_authority_valid": True,
            "package_new_entry_authority_hash_sha256": "authority-hash",
            "package_new_entry_authority_target_action_intent": "new_position",
            "package_new_entry_authority_candidate_decision_quality": {
                "expected_net_r": 0.75,
                "probability": 0.7,
                "fill_probability": 0.8,
                "source_completeness": 1.0,
                "source_boundary": (
                    "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
                ),
                "candidate_decision_quality_source_boundary": (
                    "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
                ),
            },
            "package_new_entry_authority_candidate_decision_quality_field_sources": {
                "expected_net_r": "candidate_decision_inputs.expected_net_r",
                "probability": "candidate_decision_inputs.probability",
                "fill_probability": "candidate_decision_inputs.fill_probability",
                "source_completeness": (
                    "candidate_decision_inputs.source_completeness"
                ),
            },
            "package_new_entry_authority_candidate_decision_quality_source_boundary": (
                "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
            ),
            "package_new_entry_authority_candidate_decision_quality_alias_status": (
                "exact_materialized"
            ),
            "package_new_entry_authority_candidate_decision_quality_alias_mismatches": [],
            "package_new_entry_authority_candidate_decision_quality_provenance_failures": [],
        },
        bridge_row=None,
        source_namespace="fixture",
    )

    assert row["compact_candidate_schema_version"] == 9
    assert row["ultimate_candidate_package_packet_hash_sha256"] == "packet-hash"
    assert row["ultimate_candidate_package_packet_shape_hash_sha256"] == "shape-hash"
    assert row["package_new_entry_authority_valid"] is False
    assert row["package_new_entry_authority_status"] == (
        "legacy_or_invalid_authority_diagnostic_only"
    )
    assert row["diagnostic_package_new_entry_authority_hash_sha256"] == (
        "authority-hash"
    )
    assert row["package_replay_candidate_use_allowed"] is False
    assert row["package_replay_executable_candidate_use_allowed"] is False
    assert row["replay_candidate_use_allowed_now"] is False


def test_denominator_builder_schema_v9_reuse_revalidates_complete_envelope(
    tmp_path: Path,
) -> None:
    builder = load_builder()
    candidate_id = "schema-v9-authority"
    decision_time = "2026-05-05T00:15:00+00:00"
    candidate = {
        "candidate_id": candidate_id,
        "symbol": "XAUUSD",
        "side": "LONG",
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "source_bound_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "candidate_instance_identity_status": "materialized",
        "entry_price": 100.0,
        "stop_loss": 99.0,
        "take_profit_1": 102.0,
        "trade_parameters": {
            "entry_price": 100.0,
            "stop_loss": 99.0,
            "take_profit_1": 102.0,
            "target_reference": 102.0,
            "risk_reward_ratio": 2.0,
        },
        "selector_action": "open-reduced-risk",
        "scheduler_materialization_action_intent": "new_position",
        **signed_package_new_entry_fields(
            candidate_id=candidate_id,
            decision_time_utc=decision_time,
            selector_action="open-reduced-risk",
        ),
    }
    good = builder.compact_replay_candidate_row(
        candidate,
        bridge_row=None,
        source_namespace="fresh",
    )
    assert good["package_new_entry_authority_envelope_validation_status"] == (
        "single_current_schema_immutable_envelope"
    )
    stale = json.loads(json.dumps(good))
    stale["source_namespace"] = "stale-reused"
    del stale["package_new_entry_authority_payload"]["cost_authority"]
    digest = package_new_entry_authority_payload_hash_sha256(
        stale["package_new_entry_authority_payload"]
    )
    stale["package_new_entry_authority_hash_sha256"] = digest
    stale["expected_package_new_entry_authority_hash_sha256"] = digest

    candidate_path = tmp_path / "candidate.jsonl"
    denominator_path = tmp_path / "denominator.jsonl"
    compact_path = tmp_path / "compact.jsonl"
    write_jsonl(candidate_path, [candidate])
    write_jsonl(denominator_path, [])
    write_jsonl(compact_path, [stale])

    rows = builder.compact_replay_candidate_rows_if_needed(
        candidate_path=candidate_path,
        denominator_bridge_path=denominator_path,
        compact_path=compact_path,
        source_namespace="fresh",
    )

    assert len(rows) == 1
    assert rows[0]["source_namespace"] == "fresh"
    assert rows[0]["package_new_entry_authority_payload"]["cost_authority"] == (
        "broker_calibrated_replay_cost"
    )
    assert rows[0]["package_new_entry_authority_valid"] is True


def test_denominator_builder_rejects_stale_compact_rows_beyond_sample_window(
    tmp_path: Path,
) -> None:
    builder = load_builder()
    candidate_path = tmp_path / "candidate.jsonl"
    denominator_path = tmp_path / "denominator.jsonl"
    compact_path = tmp_path / "compact.jsonl"
    candidate = {
        "candidate_id": "deep-stale-fixture",
        "symbol": "XAUUSD",
        "side": "LONG",
        "decision_time_utc": "2026-05-05T00:15:00+00:00",
        "entry_price": 100.0,
        "stop_loss": 99.0,
        "take_profit_1": 102.0,
        "trade_parameters": {
            "entry_price": 100.0,
            "stop_loss": 99.0,
            "take_profit_1": 102.0,
            "target_reference": 102.0,
            "risk_reward_ratio": 2.0,
        },
        "package_replay_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed": True,
        "replay_candidate_use_allowed_now": True,
        "scheduler_materialization_skip_reason": "fixture_skip",
    }
    write_jsonl(candidate_path, [candidate])
    write_jsonl(denominator_path, [])
    good_stale_row = {
        **builder.compact_replay_candidate_row(
            {**candidate, "scheduler_materialization_skip_reason": None},
            bridge_row=None,
            source_namespace="fixture",
        ),
        "pretrade_broker_net_cost_packet": {"status": "PASSED"},
    }
    bad_deep_row = {
        **good_stale_row,
        "candidate_id": "bad-deep-row",
        "target_reference": None,
        "risk_reward_ratio": None,
        "canonical_geometry_status": None,
        "package_replay_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed": False,
        "scheduler_materialization_skip_reason": "fixture_skip",
    }
    write_jsonl(compact_path, [good_stale_row] * 25 + [bad_deep_row])

    rows = builder.compact_replay_candidate_rows_if_needed(
        candidate_path=candidate_path,
        denominator_bridge_path=denominator_path,
        compact_path=compact_path,
        source_namespace="fixture",
    )

    assert len(rows) == 1
    assert rows[0]["target_reference"] == 102.0
    assert rows[0]["package_replay_candidate_use_allowed"] is False
    assert rows[0]["package_replay_executable_candidate_use_allowed"] is False


def test_builder_all_symbol_artifact_guard_omits_derived_compact_candidate(
    tmp_path: Path,
    monkeypatch,
) -> None:
    builder = load_builder()
    summary_path = tmp_path / "PHASE2_M15_GRID_ALL_SYMBOL_REPLAY_BRIDGE_SUMMARY.json"
    ledger_paths = {
        key: tmp_path / path.name
        for key, path in builder.PHASE2_M15_GRID_ALL_SYMBOL_LEDGER_PATHS.items()
    }
    monkeypatch.setattr(builder, "PHASE2_M15_GRID_ALL_SYMBOL_SUMMARY_PATH", summary_path)
    monkeypatch.setattr(builder, "PHASE2_M15_GRID_ALL_SYMBOL_LEDGER_PATHS", ledger_paths)
    summary_path.write_text(
        json.dumps({"status": "completed", "compact_candidate_rows": 43170}),
        encoding="utf-8",
    )
    for key in builder.PHASE2_M15_GRID_ALL_SYMBOL_REQUIRED_INPUT_KEYS:
        ledger_paths[key].write_text(json.dumps({"key": key}) + "\n", encoding="utf-8")

    assert builder.phase2_m15_grid_all_symbol_missing_artifacts(
        require_compact=False
    ) == []
    assert builder.phase2_m15_grid_all_symbol_missing_artifacts(
        require_compact=True
    ) == [ledger_paths["compact_candidate"].name]
    assert builder.phase2_m15_grid_all_symbol_manifest_files() == [
        summary_path.name,
        *[
            ledger_paths[key].name
            for key in builder.PHASE2_M15_GRID_ALL_SYMBOL_REQUIRED_INPUT_KEYS
        ],
    ]
    assert ledger_paths["compact_candidate"].name not in (
        builder.phase2_m15_grid_all_symbol_manifest_files()
    )
    assert (
        ledger_paths["profit_harvest_authority_blocker"].name
        in builder.phase2_m15_grid_all_symbol_manifest_files()
    )
    omitted = builder.phase2_m15_grid_all_symbol_compact_candidate_omission(
        {"compact_candidate_rows": 43170}
    )
    assert omitted["file"] == ledger_paths["compact_candidate"].name
    assert omitted["row_count_authority"] == 43170
    assert omitted["source_candidate_ledger"] == ledger_paths["candidate"].name


def test_builder_all_symbol_artifact_guard_allows_zero_row_terminal_ledgers(
    tmp_path: Path,
    monkeypatch,
) -> None:
    builder = load_builder()
    summary_path = tmp_path / "PHASE2_M15_GRID_ALL_SYMBOL_REPLAY_BRIDGE_SUMMARY.json"
    ledger_paths = {
        key: tmp_path / path.name
        for key, path in builder.PHASE2_M15_GRID_ALL_SYMBOL_LEDGER_PATHS.items()
    }
    monkeypatch.setattr(builder, "PHASE2_M15_GRID_ALL_SYMBOL_SUMMARY_PATH", summary_path)
    monkeypatch.setattr(builder, "PHASE2_M15_GRID_ALL_SYMBOL_LEDGER_PATHS", ledger_paths)
    summary_path.write_text(
        json.dumps(
            {
                "status": "completed",
                "filtered_non_executable_order_rows": 0,
                "filtered_non_executable_trade_rows": 0,
                "oracle_rows": 0,
                "order_rows": 0,
                "profit_harvest_authority_blocker_rows": 0,
                "trade_rows": 0,
            }
        ),
        encoding="utf-8",
    )
    zero_row_keys = {
        "filtered_non_executable_order",
        "filtered_non_executable_trade",
        "oracle",
        "order",
        "profit_harvest_authority_blocker",
        "trade",
    }
    for key in builder.PHASE2_M15_GRID_ALL_SYMBOL_REQUIRED_INPUT_KEYS:
        if key not in zero_row_keys:
            ledger_paths[key].write_text(json.dumps({"key": key}) + "\n", encoding="utf-8")

    assert builder.phase2_m15_grid_all_symbol_missing_artifacts(
        require_compact=False
    ) == []


def test_builder_expansion_artifact_guard_accepts_summary_backed_zero_row_omissions(
    tmp_path: Path,
    monkeypatch,
) -> None:
    builder = load_builder()
    summary_path = tmp_path / "PHASE2_M15_GRID_EXPANSION_REPLAY_BRIDGE_SUMMARY.json"
    ledger_paths = {
        key: tmp_path / path.name
        for key, path in builder.PHASE2_M15_GRID_EXPANSION_LEDGER_PATHS.items()
    }
    monkeypatch.setattr(builder, "PHASE2_M15_GRID_EXPANSION_SUMMARY_PATH", summary_path)
    monkeypatch.setattr(builder, "PHASE2_M15_GRID_EXPANSION_LEDGER_PATHS", ledger_paths)
    summary_path.write_text(
        json.dumps(
            {
                "status": "completed_candidate_replay_no_terminal_execution",
                "filtered_non_executable_order_rows": 0,
                "filtered_non_executable_trade_rows": 0,
                "packet_sidecar_rows": 3,
            }
        ),
        encoding="utf-8",
    )
    for key, path in ledger_paths.items():
        if key in {
            "candidate",
            "filtered_non_executable_order",
            "filtered_non_executable_trade",
            "packet_sidecar",
        }:
            continue
        path.write_text(json.dumps({"key": key}) + "\n", encoding="utf-8")
    ledger_paths["compact_candidate"].write_text(
        json.dumps({"candidate_id": "candidate-1"}) + "\n",
        encoding="utf-8",
    )

    rows, summary, _source_rows = builder.build_phase2_m15_grid_expansion_analysis_rows(
        baseline_bridge_label_join_rows=[],
    )

    assert summary["phase2_m15_grid_expansion_replay_completed"] is True
    assert summary["phase2_m15_grid_candidate_rows"] == 1
    assert rows[0]["status"] != "m15_grid_expansion_replay_missing"


def test_route_manifest_requires_selected_pending_and_phase2_profit_harvest_blockers() -> None:
    verifier = load_verifier()

    required = {
        "REPLAY_EXTENSION_SELECTED_PACKAGE_REPLAY_BRIDGE_PROFIT_HARVEST_AUTHORITY_BLOCKER_LEDGER.jsonl",
        "REPLAY_EXTENSION_PENDING_CREATED_REPLAY_BRIDGE_PROFIT_HARVEST_AUTHORITY_BLOCKER_LEDGER.jsonl",
        "PHASE2_M15_GRID_EXPANSION_REPLAY_BRIDGE_PROFIT_HARVEST_AUTHORITY_BLOCKER_LEDGER.jsonl",
    }
    source = Path(verifier.__file__).read_text(encoding="utf-8")

    for filename in required:
        assert filename in source


def test_builder_selected_package_replay_split_keeps_selection_closed() -> None:
    builder = load_builder()

    split = builder.selected_package_replay_materialization_split_fields(
        replay_completed=True,
        candidate_rows_materialized=307,
        selected_candidate_rows=178,
        denominator_use_allowed_rows=0,
        final_package_selection_allowed=False,
    )

    assert split["selected_package_replay_materialized"] is True
    assert split["selected_package_replay_denominator_selectable"] is False
    assert split["selected_package_replay_final_selectable"] is False
    assert split["selected_package_replay_final_selection_allowed"] is False
    assert split["selected_package_replay_live_selectable"] is False
    assert split["selected_package_replay_materialization_split_status"] == (
        "replay_materialized_denominator_and_final_selection_closed"
    )


def test_verifier_all_symbol_manifest_allows_omitted_compact_candidate(
    tmp_path: Path,
    monkeypatch,
) -> None:
    verifier = load_verifier()
    monkeypatch.setattr(verifier, "ROUTE", tmp_path)
    candidate = "PHASE2_M15_GRID_ALL_SYMBOL_REPLAY_BRIDGE_CANDIDATE_LEDGER.jsonl"
    compact = (
        "PHASE2_M15_GRID_ALL_SYMBOL_REPLAY_BRIDGE_COMPACT_CANDIDATE_LEDGER.jsonl"
    )
    scorecard = "PHASE2_M15_GRID_ALL_SYMBOL_REPLAY_BRIDGE_SCORECARD_LEDGER.jsonl"
    summary = "PHASE2_M15_GRID_ALL_SYMBOL_REPLAY_BRIDGE_SUMMARY.json"
    assert candidate in verifier.PHASE2_M15_GRID_ALL_SYMBOL_REQUIRED_FILES
    assert compact not in verifier.PHASE2_M15_GRID_ALL_SYMBOL_REQUIRED_FILES
    assert compact in verifier.PHASE2_M15_GRID_ALL_SYMBOL_OMITTABLE_LARGE_FILES
    (tmp_path / scorecard).write_text("", encoding="utf-8")
    manifest = {
        "files": [summary],
        "omitted_large_artifacts": [
            {
                "file": compact,
                "row_count_authority": 43170,
                "reason": "summary_row_count_authority",
                "summary_row_count_authority": (
                    "PHASE2_M15_GRID_ALL_SYMBOL_REPLAY_BRIDGE_SUMMARY.json:"
                    "compact_candidate_rows"
                ),
            },
        ],
    }

    omitted = verifier.manifest_omitted_large_artifact_files(manifest)
    required = verifier.phase2_m15_grid_all_symbol_manifest_required_files(
        manifest
    )

    assert omitted == {compact}
    assert required == verifier.PHASE2_M15_GRID_ALL_SYMBOL_REQUIRED_FILES


def test_verifier_manifest_listed_all_symbol_file_presence_is_early_structured(
    tmp_path: Path,
    monkeypatch,
) -> None:
    verifier = load_verifier()
    monkeypatch.setattr(verifier, "ROUTE", tmp_path)
    summary_name = "PHASE2_M15_GRID_ALL_SYMBOL_REPLAY_BRIDGE_SUMMARY.json"
    candidate_name = "PHASE2_M15_GRID_ALL_SYMBOL_REPLAY_BRIDGE_CANDIDATE_LEDGER.jsonl"
    (tmp_path / summary_name).write_text("", encoding="utf-8")

    issues = verifier.manifest_listed_file_presence_issues(
        {"files": [summary_name, candidate_name]},
        filename_prefix="PHASE2_M15_GRID_ALL_SYMBOL_REPLAY_BRIDGE",
    )

    assert issues == [
        f"manifest_listed_file_missing:{candidate_name}",
        f"manifest_listed_summary_empty:{summary_name}",
    ]


def test_verifier_allows_empty_no_terminal_execution_manifest_ledgers(
    tmp_path: Path,
    monkeypatch,
) -> None:
    verifier = load_verifier()
    monkeypatch.setattr(verifier, "ROUTE", tmp_path)
    prefix = "PHASE2_M15_GRID_ALL_SYMBOL_REPLAY_BRIDGE"
    summary_name = f"{prefix}_SUMMARY.json"
    empty_ledgers = [
        f"{prefix}_FILTERED_NON_EXECUTABLE_ORDER_LEDGER.jsonl",
        f"{prefix}_ORDERED_PATH_ORACLE_LEDGER.jsonl",
        f"{prefix}_ORDER_LEDGER.jsonl",
        f"{prefix}_PROFIT_HARVEST_AUTHORITY_BLOCKER_LEDGER.jsonl",
        f"{prefix}_TRADE_LEDGER.jsonl",
    ]
    (tmp_path / summary_name).write_text(
        json.dumps(
            {
                "filtered_non_executable_order_rows": 0,
                "oracle_rows": 0,
                "order_rows": 0,
                "profit_harvest_authority_blocker_rows": 0,
                "trade_rows": 0,
            }
        ),
        encoding="utf-8",
    )
    for ledger in empty_ledgers:
        (tmp_path / ledger).write_text("", encoding="utf-8")

    issues = verifier.manifest_listed_file_presence_issues(
        {"files": [summary_name, *empty_ledgers]},
        filename_prefix=prefix,
    )

    assert issues == []


def test_broad_quality_complete_manifest_pin_detects_newer_completed_prefix(
    tmp_path: Path, monkeypatch
) -> None:
    verifier = load_verifier()
    monkeypatch.setattr(verifier, "ROUTE", tmp_path)
    monkeypatch.delenv("GTOS_BROAD_QUALITY_PARITY_PREFIX", raising=False)
    manifest_prefix = "BROAD_LIVE_AS_IF_REPLAY_A_MANIFEST_REPAIR_SMOKE"
    competing_prefix = "BROAD_LIVE_AS_IF_REPLAY_Z_NEWER_SORT_REPAIR_SMOKE"
    write_completed_broad_quality_family(verifier, tmp_path, manifest_prefix)
    write_completed_broad_quality_family(verifier, tmp_path, competing_prefix)
    (tmp_path / f"{competing_prefix}_SUMMARY.json").touch()

    issues: list[str] = []
    selected_prefix, selected_tag, _ = verifier.select_broad_quality_parity_artifacts(
        issues,
        {"broad_quality_parity_prefix": manifest_prefix},
    )

    assert issues == [
        "broad_quality_manifest_pinned_prefix_stale_newer_completed_prefix_available:"
        f"{manifest_prefix}->['{competing_prefix}']"
    ]
    assert selected_prefix == competing_prefix
    assert selected_tag == "Z_NEWER_SORT_REPAIR_SMOKE"

    monkeypatch.setenv("GTOS_BROAD_QUALITY_PARITY_PREFIX", manifest_prefix)
    issues = []
    selected_prefix, selected_tag, _ = verifier.select_broad_quality_parity_artifacts(
        issues,
        {"broad_quality_parity_prefix": competing_prefix},
    )
    assert issues == []
    assert selected_prefix == manifest_prefix
    assert selected_tag == "A_MANIFEST_REPAIR_SMOKE"


def test_broad_quality_auto_selection_skips_missing_parity_manifest_pin(
    tmp_path: Path, monkeypatch
) -> None:
    verifier = load_verifier()
    monkeypatch.setattr(verifier, "ROUTE", tmp_path)
    monkeypatch.delenv("GTOS_BROAD_QUALITY_PARITY_PREFIX", raising=False)
    stale_complete_prefix = "BROAD_LIVE_AS_IF_REPLAY_A_PARITY_COMPLETE_SMOKE"
    newer_missing_prefix = "BROAD_LIVE_AS_IF_REPLAY_Z_MISSING_PARITY_SMOKE"
    write_completed_broad_quality_family(verifier, tmp_path, stale_complete_prefix)
    write_completed_broad_quality_family(verifier, tmp_path, newer_missing_prefix)
    missing_paths = verifier.broad_quality_artifact_paths(
        newer_missing_prefix,
        verifier.broad_quality_artifact_tag(newer_missing_prefix),
    )
    for name in verifier.BROAD_QUALITY_REQUIRED_PARITY_ARTIFACT_NAMES:
        missing_paths[name].unlink()

    issues: list[str] = []
    selected_prefix, selected_tag, _ = verifier.select_broad_quality_parity_artifacts(
        issues,
        {"broad_quality_parity_prefix": newer_missing_prefix},
    )

    assert selected_prefix == stale_complete_prefix
    assert selected_tag == "A_PARITY_COMPLETE_SMOKE"
    assert issues == [
        "broad_quality_manifest_pinned_prefix_incomplete_parity_skipped:"
        f"{newer_missing_prefix}:"
        "[\"broad_quality_parity_selected_prefix_missing_parity_artifacts:"
        f"{newer_missing_prefix}:"
        "['big_r', 'parity_summary', 'parity_ledger', 'candidate_projection', "
        "'leakage_bucket', 'repair_plan']\"]"
    ]


def test_broad_quality_selection_prefers_current_root_map_without_exhaustive_sweep(
    tmp_path: Path,
    monkeypatch,
) -> None:
    verifier = load_verifier()
    monkeypatch.setattr(verifier, "ROOT", tmp_path)
    monkeypatch.setattr(verifier, "ROUTE", tmp_path)
    monkeypatch.delenv("GTOS_BROAD_QUALITY_PARITY_PREFIX", raising=False)
    monkeypatch.delenv("GTOS_BROAD_QUALITY_EXHAUSTIVE_PREFIX_SCAN", raising=False)
    current_prefix = "BROAD_LIVE_AS_IF_REPLAY_A_CURRENT_ROOT_SMOKE"
    newer_prefix = "BROAD_LIVE_AS_IF_REPLAY_Z_NEWER_HISTORICAL_SMOKE"
    write_completed_broad_quality_family(verifier, tmp_path, current_prefix)
    write_completed_broad_quality_family(verifier, tmp_path, newer_prefix)
    (tmp_path / f"{newer_prefix}_SUMMARY.json").touch()
    root_map = tmp_path / ".context/context_os/CURRENT_ROOT_CAUSE_MAP.json"
    root_map.parent.mkdir(parents=True, exist_ok=True)
    root_map.write_text(
        json.dumps(
            {
                "latest_completed_replay_prefix": current_prefix,
                "latest_completed_targeted_replay": {"prefix": current_prefix},
            }
        ),
        encoding="utf-8",
    )

    issues: list[str] = []
    selected_prefix, selected_tag, _ = verifier.select_broad_quality_parity_artifacts(
        issues,
        {},
    )

    assert selected_prefix == current_prefix
    assert selected_tag == "A_CURRENT_ROOT_SMOKE"
    assert issues == []

    monkeypatch.setenv("GTOS_BROAD_QUALITY_EXHAUSTIVE_PREFIX_SCAN", "1")
    issues = []
    selected_prefix, selected_tag, _ = verifier.select_broad_quality_parity_artifacts(
        issues,
        {},
    )
    assert selected_prefix == newer_prefix
    assert selected_tag == "Z_NEWER_HISTORICAL_SMOKE"


def test_broad_quality_selection_uses_recent_complete_prefix_when_current_root_incomplete(
    tmp_path: Path,
    monkeypatch,
) -> None:
    verifier = load_verifier()
    monkeypatch.setattr(verifier, "ROOT", tmp_path)
    monkeypatch.setattr(verifier, "ROUTE", tmp_path)
    monkeypatch.delenv("GTOS_BROAD_QUALITY_PARITY_PREFIX", raising=False)
    monkeypatch.delenv("GTOS_BROAD_QUALITY_EXHAUSTIVE_PREFIX_SCAN", raising=False)
    current_prefix = "BROAD_LIVE_AS_IF_REPLAY_A_INCOMPLETE_ROOT_SMOKE"
    newer_prefix = "BROAD_LIVE_AS_IF_REPLAY_Z_NEWER_COMPLETE_SMOKE"
    write_completed_broad_quality_family(verifier, tmp_path, current_prefix)
    write_completed_broad_quality_family(verifier, tmp_path, newer_prefix)
    verifier.broad_quality_artifact_paths(
        current_prefix,
        verifier.broad_quality_artifact_tag(current_prefix),
    )["candidate"].unlink()
    (tmp_path / f"{newer_prefix}_SUMMARY.json").touch()
    root_map = tmp_path / ".context/context_os/CURRENT_ROOT_CAUSE_MAP.json"
    root_map.parent.mkdir(parents=True, exist_ok=True)
    root_map.write_text(
        json.dumps({"latest_completed_replay": {"prefix": current_prefix}}),
        encoding="utf-8",
    )

    issues: list[str] = []
    selected_prefix, selected_tag, _ = verifier.select_broad_quality_parity_artifacts(
        issues,
        {},
    )

    assert selected_prefix == newer_prefix
    assert selected_tag == "Z_NEWER_COMPLETE_SMOKE"
    assert not any("FIELD_PARITY_RESTORED" in issue for issue in issues)


def test_broad_quality_summary_completed_rejects_zero_candidate_materialized_status() -> None:
    verifier = load_verifier()

    assert (
        verifier.broad_quality_summary_completed(
            {
                "status": "broad_live_as_if_replay_materialized_broker_live_closed",
                "candidate_rows": 0,
                "order_rows": 0,
                "oracle_rows": 0,
                "trade_rows": 0,
                "live_broker_authority": False,
                "broker_mutation_enabled": False,
                "final_selection_claim": False,
            }
        )
        is False
    )
    assert (
        verifier.broad_quality_summary_completed(
            {
                "status": "broad_live_as_if_replay_materialized_broker_live_closed",
                "candidate_rows": 1,
                "order_rows": 1,
                "oracle_rows": 1,
                "trade_rows": 1,
                "live_broker_authority": False,
                "broker_mutation_enabled": False,
                "final_selection_claim": False,
            }
        )
        is True
    )


def test_broad_emitted_scheduler_status_authority_scan_flags_ranked_package_leak(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    order_path = tmp_path / "ORDER_LEDGER.jsonl"
    trade_path = tmp_path / "TRADE_LEDGER.jsonl"
    scorecard_path = tmp_path / "SCORECARD_LEDGER.jsonl"
    missed_path = tmp_path / "MISSED_OPPORTUNITY_LEDGER.jsonl"
    leak = {
        "candidate_id": "ranked-package-leak",
        "canonical_replay_candidate_instance_key": (
            "ranked-package-leak@@2026-05-13T00:15:00+00:00"
        ),
        "symbol": "XAUUSD",
        "side": "LONG",
        "order_status": "filled",
        "scheduler_option_status": "candidate_ranked",
        "scheduler_option_package_fill_floor_authority_allowed": True,
        "package_replay_executable_candidate_use_allowed": True,
        "pretrade_cost_packet_status": "PASSED",
        "approved_risk_pct": 0.25,
    }
    safe = {
        **leak,
        "candidate_id": "explicit-package-status",
        "scheduler_option_status": (
            "candidate_admitted_selector_reduce_risk_package_cap_released_bounded"
        ),
    }
    non_trade_bypass = {
        **safe,
        "candidate_id": "non-trade-bypass-leak",
        "scheduler_option_dynamic_budget_package_fill_floor_bypass_allowed": True,
        "scheduler_materialization_selector_action": "reduce-risk",
    }
    trade_bypass = {
        **safe,
        "candidate_id": "trade-bypass-ok",
        "scheduler_option_dynamic_budget_package_fill_floor_bypass_allowed": True,
        "scheduler_materialization_selector_action": "trade",
    }
    reduce_risk_order_leak = {
        **safe,
        "candidate_id": "reduce-risk-new-order-leak",
        "scheduler_materialization_selector_action": "reduce-risk",
        "scheduler_materialization_action_intent": "new_position",
    }
    reduce_risk_signed_order = {
        **safe,
        "candidate_id": "reduce-risk-signed-new-order-ok",
        "decision_time_utc": "2026-05-13T00:15:00+00:00",
        "canonical_replay_candidate_instance_key": (
            "reduce-risk-signed-new-order-ok@@2026-05-13T00:15:00+00:00"
        ),
        "source_bound_replay_candidate_instance_key": (
            "reduce-risk-signed-new-order-ok@@2026-05-13T00:15:00+00:00"
        ),
        "scheduler_materialization_selector_action": "reduce-risk",
        "scheduler_materialization_action_intent": "new_position",
        **signed_package_new_entry_fields(
            candidate_id="reduce-risk-signed-new-order-ok",
            decision_time_utc="2026-05-13T00:15:00+00:00",
            action_intent="new_position",
            selector_action="reduce-risk",
        ),
    }
    reduce_risk_alias_order_leak = {
        **safe,
        "candidate_id": "reduce-risk-alias-new-order-leak",
        "scheduler_materialization_selector_action": "reduce_risk",
        "scheduler_materialization_action_intent": "new_position",
    }
    reduce_risk_trade_leak = {
        **safe,
        "candidate_id": "reduce-risk-scale-trade-leak",
        "scheduler_materialization_selector_action": "reduce-risk",
        "scheduler_materialization_action_intent": "same_direction_scale_in",
    }
    open_reduced_alias_only_leak = {
        **safe,
        "candidate_id": "open-reduced-alias-only-leak",
        "scheduler_materialization_selector_action": "open-reduced-risk",
        "scheduler_materialization_action_intent": "new_position",
        "package_open_reduced_authority_allowed": True,
        "ultimate_candidate_package_open_reduced_risk_authority": {
            "allowed": True,
        },
    }
    missing_exact_safe = {
        **safe,
        "candidate_id": "missing-exact-diagnostic-safe",
        "scheduler_option_status": "not_scheduler_materialized",
        "risk_finalizer_reason": (
            "risk_finalizer_synthesized_all_candidate_probe_diagnostic_only_missing_exact_scheduler_option"
        ),
        "package_replay_executable_candidate_use_allowed": False,
        "package_replay_order_executable_candidate_use_allowed": False,
        "package_replay_order_executable_transfer_status": "not_order_executable",
        "approved_risk_pct": 0.0,
        "order_status": "not_sent_missed_opportunity",
        "simulated_order_id": "",
    }
    missing_exact_order_leak = {
        **missing_exact_safe,
        "candidate_id": "missing-exact-order-bound-leak",
        "package_replay_order_executable_candidate_use_allowed": True,
        "package_replay_order_executable_transfer_status": "order_bound",
        "package_replay_order_executable_bound_order_id": "order-missing-exact",
        "approved_risk_pct": 0.25,
        "order_status": "pending_accepted",
        "simulated_order_id": "order-missing-exact",
    }
    missing_exact_scorecard_leak = {
        **missing_exact_safe,
        "candidate_id": "missing-exact-scorecard-executable-leak",
        "package_replay_order_executable_candidate_use_allowed": True,
        "package_replay_order_executable_transfer_status": "order_bound",
        "approved_risk_pct": 0.25,
    }
    missed_dynamic_nonexec = {
        "candidate_id": "missed-dynamic-bypass-diagnostic",
        "scheduler_option_dynamic_budget_package_fill_floor_bypass_allowed": True,
        "scheduler_materialization_selector_action": "reduce-risk",
        "scheduler_materialization_action_intent": "new_position",
        "package_replay_executable_candidate_use_allowed": True,
        "package_replay_order_executable_candidate_use_allowed": False,
        "package_replay_order_executable_transfer_status": "not_order_executable",
        "approved_risk_pct": 0.0,
        "order_status": "not_sent_missed_opportunity",
        "simulated_order_id": "",
        "decision_time_utc": "2026-05-13T00:15:00+00:00",
        "canonical_replay_candidate_instance_key": (
            "missed-dynamic-bypass-diagnostic@@2026-05-13T00:15:00+00:00"
        ),
        "source_bound_replay_candidate_instance_key": (
            "missed-dynamic-bypass-diagnostic@@2026-05-13T00:15:00+00:00"
        ),
        **signed_package_new_entry_fields(
            candidate_id="missed-dynamic-bypass-diagnostic",
            decision_time_utc="2026-05-13T00:15:00+00:00",
            action_intent="new_position",
            selector_action="reduce-risk",
        ),
    }
    soft_reallocation_pool_safe = {
        **safe,
        "candidate_id": "soft-reallocation-pool-safe",
        "reallocation_soft_guard_pool_eligible": True,
        "reallocation_soft_guard_pool_status": "eligible",
        "reallocation_soft_guard_vetoes": ["predecision_stop_hazard_guard"],
        "terminal_vetoes": [],
    }
    soft_reallocation_pool_missing_label = {
        **safe,
        "candidate_id": "soft-reallocation-pool-missing-label",
        "reallocation_soft_guard_pool_eligible": True,
        "reallocation_soft_guard_pool_status": "eligible",
        "reallocation_soft_guard_vetoes": [],
        "terminal_vetoes": [],
    }
    soft_reallocation_pool_terminal_leak = {
        **safe,
        "candidate_id": "soft-reallocation-pool-terminal-leak",
        "reallocation_soft_guard_pool_eligible": True,
        "reallocation_soft_guard_pool_status": "eligible",
        "reallocation_soft_guard_vetoes": ["predecision_stop_hazard_guard"],
        "terminal_vetoes": ["broker_cost_status_REFUSED"],
    }
    terminal_veto_executable_leak = {
        **safe,
        "candidate_id": "terminal-veto-executable-leak",
        "reallocation_soft_guard_pool_eligible": False,
        "terminal_vetoes": ["cost_source_gap"],
    }
    unresolved_fill_floor_order_leak = {
        **safe,
        "candidate_id": "unresolved-fill-floor-order-leak",
        "scheduler_option_package_fill_floor_authority_allowed": False,
        "scheduler_option_package_fill_floor_authority_unresolved_failures": [
            "fill_probability_below_execution_authority_floor"
        ],
    }
    unresolved_fill_floor_trade_leak = {
        **safe,
        "candidate_id": "unresolved-fill-floor-trade-leak",
        "scheduler_option_package_fill_floor_authority_allowed": False,
        "risk_finalizer_scheduler_option_package_fill_floor_authority_unresolved_failures": [
            "fill_probability_below_execution_authority_floor"
        ],
    }
    unresolved_fill_floor_scorecard_diagnostic = {
        **safe,
        "candidate_id": "unresolved-fill-floor-scorecard-diagnostic",
        "scheduler_option_package_fill_floor_authority_allowed": False,
        "scheduler_option_package_fill_floor_authority_unresolved_failures": [
            "fill_probability_below_execution_authority_floor"
        ],
    }
    unresolved_fill_floor_missed_diagnostic = {
        **missing_exact_safe,
        "candidate_id": "unresolved-fill-floor-missed-diagnostic",
        "scheduler_option_package_fill_floor_authority_allowed": False,
        "scheduler_option_package_fill_floor_authority_unresolved_failures": [
            "fill_probability_below_execution_authority_floor"
        ],
    }
    missed_terminal_namespace_leak = {
        **missing_exact_safe,
        "candidate_id": "missed-terminal-namespace-leak",
        "ledger_namespace_synthesized_executable_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed": False,
        "package_replay_order_executable_candidate_use_allowed": False,
        "approved_risk_pct": 0.0,
        "terminal_vetoes": ["cost_source_gap"],
    }
    write_jsonl(
        order_path,
        [
            leak,
            safe,
            non_trade_bypass,
            trade_bypass,
            reduce_risk_order_leak,
            reduce_risk_signed_order,
            reduce_risk_alias_order_leak,
            open_reduced_alias_only_leak,
            missing_exact_order_leak,
            soft_reallocation_pool_safe,
            soft_reallocation_pool_missing_label,
            soft_reallocation_pool_terminal_leak,
            terminal_veto_executable_leak,
            unresolved_fill_floor_order_leak,
        ],
    )
    write_jsonl(trade_path, [safe, reduce_risk_trade_leak, unresolved_fill_floor_trade_leak])
    write_jsonl(
        scorecard_path,
        [missing_exact_scorecard_leak, unresolved_fill_floor_scorecard_diagnostic],
    )
    write_jsonl(
        missed_path,
        [
            missing_exact_safe,
            missed_dynamic_nonexec,
            unresolved_fill_floor_missed_diagnostic,
            missed_terminal_namespace_leak,
        ],
    )

    scan = verifier.scan_broad_emitted_scheduler_status_authority(
        {
            "scorecard": scorecard_path,
            "order": order_path,
            "trade": trade_path,
            "missed": missed_path,
        }
    )

    assert scan["bad_counts"] == {
        "order:dynamic_fill_floor_bypass_non_trade_selector_action": 1,
        "order:emitted_ranked_package_authority_leak": 1,
        "order:missing_exact_scheduler_option_probe_executable": 1,
        "order:selector_open_reduced_risk_authority_missing": 1,
        "order:selector_reduce_risk_not_new_order_authority": 3,
        "order:terminal_veto_executable_claim": 2,
        "order:terminal_veto_in_soft_reallocation_pool": 1,
        "order:terminal_vs_soft_guard_pool_missing_soft_vetoes": 1,
        "order:unresolved_fill_floor_executable_claim": 1,
        "missed:terminal_veto_executable_claim": 1,
        "scorecard:missing_exact_scheduler_option_probe_executable": 1,
        "trade:selector_reduce_risk_not_new_order_authority": 1,
        "trade:unresolved_fill_floor_executable_claim": 1,
    }
    assert (
        scan["row_counts"]["missed_dynamic_fill_floor_bypass_non_trade_diagnostic_rows"]
        == 1
    )
    sample_candidate_ids = {
        row.get("candidate_id") for row in scan["sample_bad"]
    }
    assert "ranked-package-leak" in sample_candidate_ids
    assert "missing-exact-scorecard-executable-leak" in sample_candidate_ids


def test_broad_stop_hazard_cap_execution_authority_scan_flags_cap_escape(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    order_path = tmp_path / "ORDER_LEDGER.jsonl"
    trade_path = tmp_path / "TRADE_LEDGER.jsonl"
    safe_capped = {
        "candidate_id": "safe-capped-fill",
        "simulated_order_id": "order-safe",
        "simulated_trade_id": "trade-safe",
        "symbol": "XAUUSD",
        "side": "LONG",
        "order_status": "filled",
        "fill_status": "filled_from_ordered_m1_path",
        "predecision_stop_hazard_guard_status": "capped",
        "predecision_stop_hazard_guard_action": "cap",
        "predecision_stop_hazard_guard_risk_cap_applied": True,
        "predecision_stop_hazard_guard_risk_cap_pct": 0.10,
        "risk_pct": 0.10,
    }
    passed_configured_cap = {
        **safe_capped,
        "candidate_id": "passed-configured-cap-not-applied",
        "simulated_order_id": "order-passed-configured-cap",
        "simulated_trade_id": "trade-passed-configured-cap",
        "predecision_stop_hazard_guard_status": "passed",
        "predecision_stop_hazard_guard_action": "cap",
        "predecision_stop_hazard_guard_configured_action": "cap",
        "predecision_stop_hazard_guard_effective_action": "no_block",
        "predecision_stop_hazard_guard_effective_cap": False,
        "predecision_stop_hazard_guard_risk_cap_applied": False,
        "risk_pct": 0.50,
    }
    leaking_order = {
        **safe_capped,
        "candidate_id": "order-cap-escape",
        "simulated_order_id": "order-leak",
        "simulated_trade_id": "trade-leak",
        "risk_pct": 0.25,
    }
    leaking_trade = {
        **safe_capped,
        "candidate_id": "trade-cap-escape",
        "simulated_order_id": "order-trade-leak",
        "simulated_trade_id": "trade-cap-escape",
        "risk_pct": 0.35,
    }
    pending_diagnostic = {
        **leaking_order,
        "candidate_id": "not-execution-bound-diagnostic",
        "simulated_order_id": "",
        "simulated_trade_id": "",
        "order_status": "not_sent_missed_opportunity",
        "fill_status": "",
    }
    write_jsonl(
        order_path,
        [safe_capped, passed_configured_cap, leaking_order, pending_diagnostic],
    )
    write_jsonl(trade_path, [safe_capped, passed_configured_cap, leaking_trade])

    scan = verifier.scan_broad_stop_hazard_cap_execution_authority(
        {"order": order_path, "trade": trade_path}
    )

    assert scan["bad_counts"] == {
        "order:executed_risk_pct_exceeds_stop_hazard_cap": 1,
        "order:stop_hazard_cap_execution_authority_leak": 1,
        "trade:executed_risk_pct_exceeds_stop_hazard_cap": 1,
        "trade:stop_hazard_cap_execution_authority_leak": 1,
    }
    sample_candidate_ids = {row.get("candidate_id") for row in scan["sample_bad"]}
    assert sample_candidate_ids == {"order-cap-escape", "trade-cap-escape"}


def test_broad_stop_hazard_cap_requires_base_fragility_when_causal_mode_enabled(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    order_path = tmp_path / "ORDER_LEDGER.jsonl"
    trade_path = tmp_path / "TRADE_LEDGER.jsonl"
    causal_base = {
        "simulated_order_id": "order-causal",
        "simulated_trade_id": "trade-causal",
        "order_status": "filled",
        "fill_status": "filled_from_ordered_m1_path",
        "predecision_stop_hazard_guard_status": "capped",
        "predecision_stop_hazard_guard_action": "cap",
        "predecision_stop_hazard_guard_risk_cap_applied": True,
        "predecision_stop_hazard_guard_risk_cap_pct": 0.10,
        "predecision_stop_hazard_guard_pressure_requires_base_fragility": True,
        "predecision_stop_hazard_guard_pressure_triggered": True,
        "predecision_stop_hazard_guard_min_unit_risk_atr": 0.35,
        "risk_pct": 0.10,
    }
    causal_valid = {
        **causal_base,
        "candidate_id": "causal-base-fragile",
        "predecision_stop_hazard_guard_unit_risk_atr": 0.20,
    }
    causal_invalid = {
        **causal_base,
        "candidate_id": "causal-not-base-fragile",
        "simulated_order_id": "order-causal-invalid",
        "simulated_trade_id": "trade-causal-invalid",
        "predecision_stop_hazard_guard_unit_risk_atr": 0.80,
    }
    legacy_pressure_only = {
        **causal_invalid,
        "candidate_id": "legacy-pressure-only",
        "simulated_order_id": "order-legacy",
        "simulated_trade_id": "trade-legacy",
        "predecision_stop_hazard_guard_pressure_requires_base_fragility": False,
    }
    write_jsonl(order_path, [causal_valid, causal_invalid, legacy_pressure_only])
    write_jsonl(trade_path, [])

    scan = verifier.scan_broad_stop_hazard_cap_execution_authority(
        {"order": order_path, "trade": trade_path}
    )

    assert scan["row_counts"]["order_cap_requires_base_fragility_rows"] == 2
    assert scan["row_counts"]["order_base_fragile_cap_rows"] == 1
    assert scan["row_counts"]["order_legacy_pressure_only_cap_policy_rows"] == 1
    assert scan["bad_counts"] == {
        "order:causal_stop_hazard_cap_without_base_fragility": 1,
        "order:causal_stop_hazard_pressure_triggered_without_base_fragility": 1,
        "order:stop_hazard_cap_execution_authority_leak": 1,
    }
    assert scan["sample_bad"][0]["candidate_id"] == "causal-not-base-fragile"


def test_broad_physical_trade_summary_parity_binds_cost_risk_and_scoreability(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    trade_path = tmp_path / "TRADE_LEDGER.jsonl"
    write_jsonl(
        trade_path,
        [
            {
                "profile": "repaired_package_conversion_v3",
                "split": "holdout",
                "risk_expression_ladder_tier": "full",
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
                "profile": "repaired_package_conversion_v3",
                "split": "holdout",
                "risk_expression_ladder_tier": "reduced",
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
    )
    summary = {
        "physical_trade_summary_serialized_ledger_parity_contract": {
            "schema": verifier.PHYSICAL_TRADE_SUMMARY_PARITY_SCHEMA,
            "canonical_result_ledger_normalization_before_summary": True,
            "scoreable_unscoreable_cost_partition_required": True,
            "serialized_trade_ledger_is_physical_summary_authority": True,
        },
        "split_profile_stats": [
            {
                "profile": "repaired_package_conversion_v3",
                "split": "holdout",
                "trade_rows": 2,
                "physical_scoreable_trade_rows": 1,
                "physical_unscoreable_trade_rows": 1,
                "physical_win_count": 1,
                "physical_loss_count": 0,
                "physical_flat_count": 0,
                "physical_gross_r": 1.0,
                "physical_final_r": 1.0,
                "physical_expected_cost_r": 0.3,
                "physical_total_execution_cost_r": 0.3,
                "physical_scoreable_expected_cost_r": 0.1,
                "physical_unscoreable_expected_cost_r": 0.2,
                "physical_scoreable_total_execution_cost_r": 0.1,
                "physical_unscoreable_total_execution_cost_r": 0.2,
                "physical_net_r": 0.9,
                "physical_cash_pnl": 90.0,
                "physical_risk_cash": 150.0,
                "physical_risk_pct": 0.6,
                "physical_risk_ladder_tier_counts": {"full": 1, "reduced": 1},
                "physical_stress": {"trade_count": 1},
                "physical_monte_carlo": {"trade_count": 1},
            }
        ],
    }

    passed = verifier.scan_broad_physical_trade_summary_parity(summary, trade_path)
    assert passed["status"] == "passed"
    assert passed["bad_counts"] == {}

    summary["split_profile_stats"][0]["physical_risk_ladder_tier_counts"] = {
        "reduced": 2
    }
    summary["split_profile_stats"][0]["physical_scoreable_expected_cost_r"] = 0.2
    failed = verifier.scan_broad_physical_trade_summary_parity(summary, trade_path)
    assert failed["status"] == "failed"
    assert failed["bad_counts"]["summary_trade_risk_tier_counts_mismatch"] == 1
    assert failed["bad_counts"]["summary_trade_float_mismatch:physical_scoreable_expected_cost_r"] == 1
    assert failed["bad_counts"]["summary_physical_expected_cost_partition_mismatch"] == 1


def test_broad_executable_risk_fillability_atomicity_scan_flags_truth_leaks(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    order_path = tmp_path / "ORDER_LEDGER.jsonl"
    trade_path = tmp_path / "TRADE_LEDGER.jsonl"
    decision_time = "2026-05-14T14:15:00+00:00"
    source_time = "2026-05-14T14:00:00+00:00"
    boundary = "closed_m15_predecision_asof_no_postdecision_path"

    def risk_atom(candidate_id: str, risk_pct: float) -> dict:
        atom = {
            "schema_version": verifier.CANONICAL_EXECUTABLE_FINAL_RISK_ATOM_SCHEMA,
            "final_risk_pct": risk_pct,
            "risk_decision": "trade",
            "risk_decision_reason": "unit_test_atomic_authority",
            "authority_source": "unit_test_final_risk_atom",
            "candidate_id": candidate_id,
            "decision_time_utc": decision_time,
            "selected_cell_risk_pct": 0.25,
            "scheduler_approved_risk_pct": risk_pct,
            "dynamic_daily_drawdown_budget_approved_risk_pct": risk_pct,
            "precanonical_provenance": {
                "final_approved_risk_pct": risk_pct,
                "runtime_final_risk_pct": 0.0,
                "approved_risk_pct": 0.25,
            },
            "upstream_atom_hash_sha256": None,
            "uses_outcome_fields": False,
            "live_broker_authority": False,
            "broker_mutation_enabled": False,
        }
        material = json.dumps(
            atom,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        atom["atom_hash_sha256"] = hashlib.sha256(
            material.encode("utf-8")
        ).hexdigest()
        return atom

    def valid_row(candidate_id: str) -> dict:
        atom = risk_atom(candidate_id, 0.5)
        return {
            "candidate_id": candidate_id,
            "decision_time_utc": decision_time,
            "simulated_order_id": f"order-{candidate_id}",
            "simulated_trade_id": f"trade-{candidate_id}",
            "symbol": "US30_cash",
            "side": "LONG",
            "order_status": "filled",
            "fill_status": "filled_from_ordered_m1_path",
            "risk_pct": 0.5,
            "final_approved_risk_pct": 0.5,
            "runtime_final_risk_pct": 0.5,
            "approved_risk_pct": 0.5,
            "risk_cash": 500.0,
            "balance_before": 100000.0,
            "canonical_executable_final_risk_atom": atom,
            "risk_authority": {
                "risk_decision": "trade",
                "final_approved_risk_pct": 0.5,
                "runtime_final_risk_pct": 0.5,
                "approved_risk_pct": 0.5,
                "balance_before": 100000.0,
                "equity_before": 100000.0,
                "risk_cash": 500.0,
                "order_risk_cash": 500.0,
                "canonical_executable_final_risk_atom": atom,
            },
            "execution_fill_probability": 0.92,
            "execution_fill_probability_source": (
                "predecision_limit_fillability.fill_probability"
            ),
            "execution_fill_probability_source_time_utc": source_time,
            "execution_fill_probability_source_boundary": boundary,
            "execution_fill_probability_authority_class": (
                "signed_predecision_execution_fillability_authority"
            ),
            "execution_fillability_atomic_status": "complete_executable",
            "predecision_limit_fillability": {
                "fill_probability": 0.92,
                "current_price_source_time_utc": source_time,
                "source_boundary": boundary,
            },
        }

    safe_order = valid_row("safe-order")
    stale_outer_risk = valid_row("stale-outer-risk")
    stale_outer_risk.update(
        {
            "risk_pct": 0.0,
            "final_approved_risk_pct": 0.0,
            "runtime_final_risk_pct": 0.0,
            "approved_risk_pct": 0.0,
            "risk_cash": 0.0,
        }
    )
    safe_trade = valid_row("safe-trade")
    safe_trade["balance_before"] = 100500.0
    fillability_gap = valid_row("fillability-gap")
    for key in (
        "execution_fill_probability",
        "execution_fill_probability_source",
        "execution_fill_probability_source_time_utc",
        "execution_fill_probability_source_boundary",
        "execution_fill_probability_authority_class",
    ):
        fillability_gap.pop(key)
    fillability_gap["execution_fillability_atomic_status"] = (
        "incomplete_not_executable"
    )
    fillability_gap["execution_fillability_atomic_failure"] = (
        "execution_fillability_incomplete_value_only_not_propagated"
    )

    write_jsonl(order_path, [safe_order, stale_outer_risk])
    write_jsonl(trade_path, [safe_trade, fillability_gap])

    scan = verifier.scan_broad_executable_risk_and_fillability_atomicity(
        {"order": order_path, "trade": trade_path}
    )

    assert scan["row_counts"]["order_atomic_rows_valid"] == 1
    assert scan["row_counts"]["trade_atomic_rows_valid"] == 1
    assert scan["bad_counts"][
        "order:executable_risk_fillability_atomicity_leak"
    ] == 1
    assert scan["bad_counts"]["order:outer_risk_pct_mismatch"] == 1
    assert scan["bad_counts"][
        "order:risk_cash_not_bound_to_final_risk_pct"
    ] == 1
    assert scan["bad_counts"][
        "trade:executable_risk_fillability_atomicity_leak"
    ] == 1
    assert scan["bad_counts"][
        "trade:execution_fill_probability_missing_or_invalid"
    ] == 1
    assert scan["bad_counts"][
        "trade:execution_fillability_atomic_failure_present"
    ] == 1
    sample_ids = {row["candidate_id"] for row in scan["sample_bad"]}
    assert sample_ids == {"stale-outer-risk", "fillability-gap"}


def test_broad_executable_atomicity_rejects_over_budget_risk_and_permission_gaps(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    order_path = tmp_path / "ORDER_LEDGER.jsonl"
    decision_time = "2026-05-14T08:15:00+00:00"
    source_time = "2026-05-14T08:00:00+00:00"
    boundary = "closed_m15_predecision_asof_no_postdecision_path"
    atom = {
        "schema_version": verifier.CANONICAL_EXECUTABLE_FINAL_RISK_ATOM_SCHEMA,
        "final_risk_pct": 0.5,
        "risk_decision": "trade",
        "risk_decision_reason": "risk_authority_bound_and_headroom_available",
        "authority_source": "unit_test_finalizer",
        "candidate_id": "over-budget-risk",
        "decision_time_utc": decision_time,
        "selected_cell_risk_pct": 0.25,
        "scheduler_approved_risk_pct": 0.5,
        "dynamic_daily_drawdown_budget_approved_risk_pct": 0.25,
        "precanonical_provenance": {},
        "upstream_atom_hash_sha256": None,
        "uses_outcome_fields": False,
        "live_broker_authority": False,
        "broker_mutation_enabled": False,
    }
    material = json.dumps(atom, sort_keys=True, separators=(",", ":"), default=str)
    atom["atom_hash_sha256"] = hashlib.sha256(material.encode("utf-8")).hexdigest()
    row = {
        "candidate_id": "over-budget-risk",
        "decision_time_utc": decision_time,
        "simulated_order_id": "order-over-budget-risk",
        "symbol": "XAUUSD",
        "side": "LONG",
        "order_status": "pending_accepted",
        "fill_status": "filled_from_ordered_tick_path",
        "risk_pct": 0.5,
        "final_approved_risk_pct": 0.5,
        "runtime_final_risk_pct": 0.5,
        "approved_risk_pct": 0.5,
        "risk_cash": 500.0,
        "balance_before": 100000.0,
        "dynamic_daily_drawdown_budget_approved_risk_pct": 0.25,
        "canonical_executable_final_risk_atom": atom,
        "package_replay_executable_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed_reason": (
            "signed_candidate_permission"
        ),
        "package_replay_order_executable_candidate_use_allowed": True,
        "package_replay_order_executable_candidate_use_allowed_reason": (
            "signed_order_permission"
        ),
        "replay_candidate_use_allowed_now": True,
        "risk_authority": {
            "risk_decision": "trade",
            "final_approved_risk_pct": 0.5,
            "runtime_final_risk_pct": 0.5,
            "approved_risk_pct": 0.5,
            "dynamic_daily_drawdown_budget_enabled": True,
            "dynamic_daily_drawdown_budget_approved_risk_pct": 0.25,
            "balance_before": 100000.0,
            "risk_cash": 500.0,
            "order_risk_cash": 500.0,
            "canonical_executable_final_risk_atom": atom,
        },
        "execution_fill_probability": 0.92,
        "execution_fill_probability_source": (
            "predecision_limit_fillability.fill_probability"
        ),
        "execution_fill_probability_source_time_utc": source_time,
        "execution_fill_probability_source_boundary": boundary,
        "execution_fill_probability_authority_class": (
            "signed_predecision_execution_fillability_authority"
        ),
        "execution_fillability_atomic_status": "complete_executable",
        "predecision_limit_fillability": {
            "fill_probability": 0.92,
            "current_price_source_time_utc": source_time,
            "source_boundary": boundary,
        },
    }
    write_jsonl(order_path, [row])

    scan = verifier.scan_broad_executable_risk_and_fillability_atomicity(
        {"order": order_path}
    )

    assert scan["bad_counts"]["order:final_risk_exceeds_dynamic_budget_approval"] == 1
    assert scan["bad_counts"][
        "order:package_replay_executable_candidate_use_allowed_true_source_missing"
    ] == 1
    assert scan["bad_counts"][
        "order:package_replay_order_executable_candidate_use_allowed_true_source_missing"
    ] == 1
    assert scan["bad_counts"][
        "order:replay_candidate_use_allowed_now_true_reason_missing"
    ] == 1


def test_broad_selected_policy_replay_authority_scan_flags_unimplemented_and_unflattened(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    order_path = tmp_path / "ORDER_LEDGER.jsonl"
    trade_path = tmp_path / "TRADE_LEDGER.jsonl"
    write_jsonl(
        order_path,
        [
            {
                "candidate_id": "filled-order-status-policy-unimplemented",
                "simulated_order_id": "order-1",
                "symbol": "XAUUSD",
                "dynamic_geometry_policy": "momentum_exhaustion",
                "order_status": "filled",
                "selected_execution_policy_replay_exit": {
                    "replay_status": "unimplemented",
                    "final_r_authority_status": (
                        "selected_policy_replay_unimplemented:momentum_exhaustion"
                    ),
                },
                "selected_execution_policy_replay_bound": False,
            }
        ],
    )
    write_jsonl(
        trade_path,
        [
            {
                "candidate_id": "filled-momentum-unimplemented",
                "simulated_trade_id": "trade-1",
                "symbol": "XAUUSD",
                "dynamic_geometry_policy": "momentum_exhaustion",
                "fill_status": "filled_from_ordered_m1_path",
                "selected_execution_policy_replay_exit": {
                    "replay_status": "unimplemented",
                    "final_r_authority_status": (
                        "selected_policy_replay_unimplemented:momentum_exhaustion"
                    ),
                },
                "selected_execution_policy_replay_bound": False,
            },
            {
                "candidate_id": "filled-momentum-unflattened",
                "simulated_trade_id": "trade-2",
                "symbol": "XAUUSD",
                "dynamic_geometry_policy": "momentum_exhaustion",
                "fill_status": "filled_from_ordered_m1_path",
                "selected_execution_policy_replay_exit": {
                    "replay_status": "replayed",
                    "final_r_authority": True,
                    "final_r_authority_status": (
                        "selected_policy_ordered_path_replay_authority"
                    ),
                },
                "selected_execution_policy_replay_status": "replayed",
                "selected_execution_policy_replay_bound": True,
            },
            {
                "candidate_id": "filled-momentum-null-replay",
                "simulated_trade_id": "trade-3",
                "symbol": "XAUUSD",
                "dynamic_geometry_policy": "momentum_exhaustion",
                "fill_status": "filled_from_ordered_m1_path",
                "selected_execution_policy_replay_exit": None,
                "selected_execution_policy_replay_bound": False,
            },
            {
                "candidate_id": "filled-momentum-alias-unimplemented",
                "simulated_trade_id": "trade-4",
                "symbol": "XAUUSD",
                "gtos_vnext_dynamic_policy_selected": "momentum_exhaustion",
                "fill_status": "filled_from_ordered_m1_path",
                "selected_execution_policy": {
                    "replay": {
                        "replay_status": "unimplemented",
                        "final_r_authority_status": (
                            "selected_policy_replay_unimplemented:momentum_exhaustion"
                        ),
                    }
                },
                "selected_execution_policy_replay_bound": False,
            },
            {
                "candidate_id": "filled-profit-harvest-unordered",
                "simulated_trade_id": "trade-5",
                "symbol": "XAGUSD",
                "selected_policy": "momentum_exhaustion",
                "fill_status": "filled_from_ordered_m1_path",
                "selected_execution_policy_replay_exit": {
                    "replay_status": "replayed",
                    "final_r_authority_status": (
                        "selected_policy_ordered_path_replay_authority"
                    ),
                },
                "selected_execution_policy_replay_status": "replayed",
                "selected_execution_policy_replay_final_r_authority_status": (
                    "selected_policy_ordered_path_replay_authority"
                ),
                "selected_execution_policy_replay_bound": True,
                "profit_harvest_mfe_capture_replay_bound": True,
                "profit_harvest_mfe_capture_replay_exit_final_r_authority": True,
                "ordered_tick_truth_satisfied": False,
                "fill_bar_observation_allowed": False,
            },
            {
                "candidate_id": "filled-profit-harvest-m1-proxy",
                "simulated_trade_id": "trade-6",
                "symbol": "XAGUSD",
                "selected_policy": "momentum_exhaustion",
                "fill_status": "filled_from_ordered_m1_path",
                "selected_execution_policy_replay_exit": {
                    "replay_status": "replayed",
                    "final_r_authority_status": (
                        "selected_policy_ordered_path_replay_authority"
                    ),
                },
                "selected_execution_policy_replay_status": "replayed",
                "selected_execution_policy_replay_final_r_authority_status": (
                    "selected_policy_ordered_path_replay_authority"
                ),
                "selected_execution_policy_replay_bound": True,
                "profit_harvest_mfe_capture_replay_bound": True,
                "profit_harvest_mfe_capture_replay_exit_final_r_authority": True,
                "profit_harvest_mfe_capture_replay_exit_final_r_authority_status": (
                    "m1_ordered_path_proxy_final_r_authority_not_live"
                ),
                "profit_harvest_mfe_capture_replay_exit": {
                    "source_boundary": (
                        "m1_ordered_path_profit_harvest_proxy_replay_"
                        "not_broker_live_authority"
                    )
                },
                "ordered_tick_truth_satisfied": False,
                "fill_bar_observation_allowed": False,
            },
        ],
    )

    scan = verifier.scan_broad_selected_policy_replay_authority(
        {"order": order_path, "trade": trade_path}
    )

    assert scan["bad_counts"]["trade:selected_policy_replay_unimplemented"] == 2
    assert scan["bad_counts"]["order:selected_policy_replay_unimplemented"] == 1
    assert (
        scan["bad_counts"][
            "order:selected_policy_replay_authority_status_not_flattened"
        ]
        == 1
    )
    assert (
        scan["bad_counts"][
            "trade:selected_policy_replay_authority_status_not_flattened"
        ]
        == 4
    )
    assert scan["bad_counts"]["trade:selected_policy_replay_exit_missing"] == 2
    assert scan["bad_counts"]["trade:selected_policy_replay_bound_false"] == 2
    assert scan["bad_counts"]["trade:selected_policy_replay_status_missing"] == 1
    assert (
        scan["bad_counts"][
            "trade:profit_harvest_replay_bound_without_ordered_tick_truth"
        ]
        == 2
    )
    assert (
        scan["bad_counts"][
            "trade:profit_harvest_final_r_authority_without_ordered_tick_truth"
        ]
        == 2
    )
    assert (
        scan["bad_counts"]["trade:m1_proxy_profit_harvest_bound_as_terminal_authority"]
        == 1
    )
    assert (
        scan["bad_counts"][
            "trade:m1_proxy_profit_harvest_legacy_final_r_authority_true"
        ]
        == 1
    )


def test_broad_selected_policy_replay_authority_accepts_m1_diagnostic_replay(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    order_path = tmp_path / "ORDER_LEDGER.jsonl"
    trade_path = tmp_path / "TRADE_LEDGER.jsonl"
    diagnostic_row = {
        "candidate_id": "m1-diagnostic-replay",
        "simulated_order_id": "order-1",
        "simulated_trade_id": "trade-1",
        "symbol": "XAGUSD",
        "side": "LONG",
        "selected_policy": "momentum_exhaustion",
        "fill_status": "filled_from_ordered_m1_path",
        "order_status": "filled",
        "path_source": "m1",
        "ordered_tick_truth_satisfied": False,
        "selected_execution_policy_replay_exit": {
            "replay_status": "replayed",
            "final_r_authority": False,
            "final_r_authority_status": (
                "selected_policy_replay_not_authoritative:"
                "path_source_not_ordered_tick_truth:m1"
            ),
            "source_boundary": (
                "postdecision_selected_policy_replay_diagnostic_"
                "no_ordered_tick_terminal_r_authority"
            ),
        },
        "selected_execution_policy_replay_status": "replayed",
        "selected_execution_policy_replay_bound": False,
        "selected_execution_policy_replay_final_r_authority_status": (
            "selected_policy_replay_not_authoritative:"
            "path_source_not_ordered_tick_truth:m1"
        ),
        "selected_execution_policy_replay_source_boundary": (
            "postdecision_selected_policy_replay_diagnostic_"
            "no_ordered_tick_terminal_r_authority"
        ),
    }
    write_jsonl(order_path, [diagnostic_row])
    write_jsonl(trade_path, [diagnostic_row])

    scan = verifier.scan_broad_selected_policy_replay_authority(
        {"order": order_path, "trade": trade_path}
    )

    assert scan["bad_counts"] == {}


def test_broad_selected_policy_replay_requires_tick_oracle_authority_atom(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    trade_path = tmp_path / "TRADE_LEDGER.jsonl"
    authority = {
        "source": "tick",
        "source_path": "fixture_tick.csv",
        "source_sha256": "a" * 64,
        "source_timeframe": "TICK",
        "ordered_tick_truth_satisfied": True,
        "query_after_utc": "2026-05-14T08:15:00+00:00",
        "query_until_utc": "2026-05-14T09:15:00+00:00",
        "query_row_count": 20,
        "source_boundary": "ordered_postdecision_tick_path_truth",
    }
    material = json.dumps(
        authority,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    authority_hash = hashlib.sha256(material.encode("utf-8")).hexdigest()
    valid = {
        "candidate_id": "ordered-tick-valid",
        "simulated_trade_id": "trade-ordered-tick-valid",
        "symbol": "GER40",
        "side": "SHORT",
        "selected_policy": "momentum_exhaustion",
        "fill_status": "filled_from_ordered_tick_path",
        "order_status": "filled",
        "path_source": "tick",
        "ordered_tick_truth_satisfied": True,
        "ordered_tick_truth_source_satisfied": True,
        "ordered_tick_truth_oracle_satisfied": True,
        "ordered_tick_truth_authority": authority,
        "ordered_tick_truth_authority_hash_sha256": authority_hash,
        "selected_execution_policy_replay_exit": {
            "replay_status": "replayed",
            "final_r_authority": True,
            "final_r_authority_status": (
                "selected_policy_ordered_tick_replay_authority"
            ),
        },
        "selected_execution_policy_replay_status": "replayed",
        "selected_execution_policy_replay_bound": True,
        "selected_execution_policy_replay_final_r_authority_status": (
            "selected_policy_ordered_tick_replay_authority"
        ),
    }
    invalid = {
        **valid,
        "candidate_id": "ordered-tick-oracle-missing",
        "simulated_trade_id": "trade-ordered-tick-oracle-missing",
        "ordered_tick_truth_satisfied": False,
        "ordered_tick_truth_oracle_satisfied": False,
        "ordered_tick_truth_authority": None,
        "ordered_tick_truth_authority_hash_sha256": None,
    }
    write_jsonl(trade_path, [valid, invalid])

    scan = verifier.scan_broad_selected_policy_replay_authority(
        {"trade": trade_path}
    )

    assert scan["row_counts"]["trade_ordered_tick_source_truth_rows"] == 2
    assert scan["bad_counts"][
        "trade:ordered_tick_source_truth_not_bound_to_oracle_authority"
    ] == 1
    assert scan["bad_counts"]["trade:ordered_tick_truth_authority_missing"] == 1


def test_broad_selected_policy_replay_authority_accepts_ordered_profit_harvest(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    order_path = tmp_path / "ORDER_LEDGER.jsonl"
    trade_path = tmp_path / "TRADE_LEDGER.jsonl"
    write_jsonl(order_path, [])
    write_jsonl(
        trade_path,
        [
            {
                "candidate_id": "ordered-profit-harvest",
                "simulated_trade_id": "trade-ordered-profit-harvest",
                "symbol": "XAGUSD",
                "selected_policy": "momentum_exhaustion",
                "fill_status": "filled_from_ordered_tick_path",
                "path_source": "tick",
                "ordered_tick_truth_satisfied": True,
                "fill_bar_observation_allowed": True,
                "selected_execution_policy_replay_exit": {
                    "replay_status": "replayed",
                    "final_r_authority": True,
                    "final_r_authority_status": (
                        "selected_policy_ordered_tick_replay_authority"
                    ),
                    "ordered_tick_truth_satisfied_for_selected_policy_replay": True,
                },
                "selected_execution_policy_replay_status": "replayed",
                "selected_execution_policy_replay_bound": True,
                "selected_execution_policy_replay_final_r_authority_status": (
                    "selected_policy_ordered_tick_replay_authority"
                ),
                "selected_execution_policy_fill_bar_observation_allowed": True,
                "selected_execution_policy_ordered_tick_truth_satisfied": True,
                "profit_harvest_mfe_capture_replay_bound": True,
                "profit_harvest_mfe_capture_replay_exit_final_r_authority": True,
                "profit_harvest_mfe_capture_replay_exit_ordered_tick_final_r_authority": True,
                "profit_harvest_mfe_capture_replay_exit_m1_proxy_replay_authority": False,
            }
        ],
    )

    scan = verifier.scan_broad_selected_policy_replay_authority(
        {"order": order_path, "trade": trade_path}
    )

    assert scan["bad_counts"] == {}


def test_broad_selected_policy_replay_authority_still_flags_raw_replayed_unbound(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    order_path = tmp_path / "ORDER_LEDGER.jsonl"
    trade_path = tmp_path / "TRADE_LEDGER.jsonl"
    unsafe_row = {
        "candidate_id": "unsafe-raw-replay",
        "simulated_trade_id": "trade-1",
        "symbol": "XAGUSD",
        "selected_policy": "momentum_exhaustion",
        "fill_status": "filled_from_ordered_m1_path",
        "path_source": "m1",
        "ordered_tick_truth_satisfied": False,
        "selected_execution_policy_replay_exit": {
            "replay_status": "replayed",
            "final_r_authority": False,
            "final_r_authority_status": "selected_policy_ordered_path_replay_authority",
        },
        "selected_execution_policy_replay_status": "replayed",
        "selected_execution_policy_replay_bound": False,
        "selected_execution_policy_replay_final_r_authority_status": (
            "selected_policy_ordered_path_replay_authority"
        ),
    }
    write_jsonl(order_path, [])
    write_jsonl(trade_path, [unsafe_row])

    scan = verifier.scan_broad_selected_policy_replay_authority(
        {"order": order_path, "trade": trade_path}
    )

    assert scan["bad_counts"]["trade:selected_policy_replayed_but_bound_false"] == 1
    assert scan["bad_counts"]["trade:selected_policy_replay_authority_leak"] == 1


def test_broad_selected_policy_replay_authority_flags_quality_gate_leaks(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    order_path = tmp_path / "ORDER_LEDGER.jsonl"
    trade_path = tmp_path / "TRADE_LEDGER.jsonl"
    blocked_gate_order = {
        "candidate_id": "blocked-quality-gate-order",
        "simulated_order_id": "order-blocked-quality",
        "symbol": "XAUUSD",
        "selected_policy": "momentum_exhaustion",
        "order_status": "filled",
        "selected_execution_policy_replay_exit": {
            "replay_status": "not_authoritative_predecision_quality_gate",
            "final_r_authority": False,
            "final_r_authority_status": (
                "selected_policy_replay_not_authoritative:"
                "selected_policy_executable_quality_gate_failed"
            ),
            "selected_policy_executable_quality_gate_status": "blocked",
            "selected_policy_executable_quality_gate_source_boundary": (
                "predecision_selected_policy_executable_quality_gate_no_outcome_fields"
            ),
            "selected_policy_executable_quality_gate_uses_outcome_fields": False,
        },
        "selected_execution_policy_replay_status": (
            "not_authoritative_predecision_quality_gate"
        ),
        "selected_execution_policy_replay_bound": False,
        "selected_execution_policy_replay_final_r_authority_status": (
            "selected_policy_replay_not_authoritative:"
            "selected_policy_executable_quality_gate_failed"
        ),
        "selected_policy_executable_quality_gate_status": "blocked",
        "selected_policy_executable_quality_gate_source_boundary": (
            "predecision_selected_policy_executable_quality_gate_no_outcome_fields"
        ),
        "selected_policy_executable_quality_gate_uses_outcome_fields": False,
    }
    outcome_gate_trade = {
        "candidate_id": "outcome-quality-gate-trade",
        "simulated_trade_id": "trade-outcome-quality",
        "symbol": "XAUUSD",
        "selected_policy": "momentum_exhaustion",
        "fill_status": "filled_from_ordered_tick_path",
        "ordered_tick_truth_satisfied": True,
        "selected_execution_policy_replay_exit": {
            "replay_status": "replayed",
            "final_r_authority": True,
            "final_r_authority_status": (
                "selected_policy_ordered_tick_replay_authority"
            ),
            "selected_policy_executable_quality_gate_status": "passed",
            "selected_policy_executable_quality_gate_source_boundary": (
                "predecision_selected_policy_executable_quality_gate_no_outcome_fields"
            ),
            "selected_policy_executable_quality_gate_uses_outcome_fields": True,
        },
        "selected_execution_policy_replay_status": "replayed",
        "selected_execution_policy_replay_bound": True,
        "selected_execution_policy_replay_final_r_authority_status": (
            "selected_policy_ordered_tick_replay_authority"
        ),
        "selected_policy_executable_quality_gate_status": "passed",
        "selected_policy_executable_quality_gate_source_boundary": (
            "predecision_selected_policy_executable_quality_gate_no_outcome_fields"
        ),
        "selected_policy_executable_quality_gate_uses_outcome_fields": True,
    }
    bad_boundary_trade = {
        **outcome_gate_trade,
        "candidate_id": "bad-boundary-quality-gate-trade",
        "simulated_trade_id": "trade-bad-boundary-quality",
        "selected_policy_executable_quality_gate_uses_outcome_fields": False,
        "selected_policy_executable_quality_gate_source_boundary": (
            "postdecision_result_fields"
        ),
        "selected_execution_policy_replay_exit": {
            **outcome_gate_trade["selected_execution_policy_replay_exit"],
            "selected_policy_executable_quality_gate_uses_outcome_fields": False,
            "selected_policy_executable_quality_gate_source_boundary": (
                "postdecision_result_fields"
            ),
        },
    }
    write_jsonl(order_path, [blocked_gate_order])
    write_jsonl(trade_path, [outcome_gate_trade, bad_boundary_trade])

    scan = verifier.scan_broad_selected_policy_replay_authority(
        {"order": order_path, "trade": trade_path}
    )

    assert (
        scan["bad_counts"][
            "order:selected_policy_executable_quality_gate_blocked_reached_execution"
        ]
        == 1
    )
    assert (
        scan["bad_counts"][
            "trade:selected_policy_executable_quality_gate_used_outcome_fields"
        ]
        == 1
    )
    assert (
        scan["bad_counts"][
            "trade:selected_policy_executable_quality_gate_source_boundary_bad"
        ]
        == 1
    )
    assert scan["bad_counts"]["order:selected_policy_replay_authority_leak"] == 1
    assert scan["bad_counts"]["trade:selected_policy_replay_authority_leak"] == 2


def test_m1_proxy_final_r_authority_split_requires_blocker_and_no_legacy_authority() -> None:
    verifier = load_verifier()

    bad_row = {
        "candidate_id": "m1-proxy-bad",
        "decision_time_utc": "2026-05-06T09:15:00+00:00",
        "profit_harvest_mfe_capture_replay_exit_m1_proxy_replay_authority": True,
        "profit_harvest_mfe_capture_replay_exit_final_r_authority": True,
        "profit_harvest_mfe_capture_replay_bound": True,
        "headline_result_authority": True,
        "final_r_authority": True,
    }
    clean_row = {
        "candidate_id": "m1-proxy-clean",
        "decision_time_utc": "2026-05-06T09:30:00+00:00",
        "profit_harvest_mfe_capture_replay_exit_m1_proxy_replay_authority": True,
        "profit_harvest_mfe_capture_replay_exit_final_r_authority": False,
        "profit_harvest_mfe_capture_replay_exit_ordered_tick_final_r_authority": False,
        "profit_harvest_mfe_capture_replay_exit_headline_result_authority": False,
        "profit_harvest_mfe_capture_replay_bound": False,
        "headline_result_authority": False,
        "final_r_authority": False,
    }
    blocker = {
        "candidate_id": "m1-proxy-clean",
        "decision_time_utc": "2026-05-06T09:30:00+00:00",
        "ordered_tick_proof_required": True,
        "m1_proxy_replay_authority": True,
    }

    scan = verifier.scan_m1_proxy_final_r_authority_split(
        {
            "bridge": {
                "oracle": [bad_row, clean_row],
                "order": [],
                "trade": [],
                "blocker": [blocker],
            }
        }
    )

    assert scan["row_counts"]["bridge:oracle_m1_proxy_rows"] == 2
    assert scan["bad_counts"]["bridge:oracle:m1_proxy_authority_split_bad"] == 1
    assert scan["bad_counts"]["bridge:oracle:m1_proxy_legacy_final_r_authority_true"] == 1
    assert (
        scan["bad_counts"][
            "bridge:oracle:m1_proxy_profit_harvest_legacy_final_r_authority_true"
        ]
        == 1
    )
    assert scan["bad_counts"]["bridge:oracle:m1_proxy_headline_result_authority_true"] == 1
    assert scan["bad_counts"]["bridge:oracle:m1_proxy_profit_harvest_bound_true"] == 1
    assert scan["bad_counts"]["bridge:oracle:m1_proxy_ordered_tick_blocker_missing"] == 1


def test_bridge_hydrate_candidate_preserves_predecision_fillability_source_time() -> None:
    bridge = load_bridge()
    verifier = load_verifier()

    row = bridge.hydrate_candidate_quality_aliases(
        {
            "candidate_id": "bridge-source-time",
            "symbol": "XAGUSD",
            "side": "LONG",
            "decision_time_utc": "2026-05-05T07:15:00+00:00",
            "entry_price": 32.1,
            "stop_loss": 31.9,
            "take_profit_1": 32.7,
            "predecision_limit_fillability": {
                "schema_version": "predecision_limit_fillability_signal_v1",
                "available": True,
                "current_price": 32.0,
                "source_boundary": "asof_candidate_fields_only_no_postdecision_path",
                "current_price_source_time_utc": "2026-05-05T07:14:00+00:00",
                "fill_probability": 0.92,
            },
        }
    )

    fillability = row["predecision_limit_fillability"]
    assert (
        fillability["current_price_source_time_utc"]
        == "2026-05-05T07:14:00+00:00"
    )
    assert row["predecision_current_price_source_time_utc"] == (
        "2026-05-05T07:14:00+00:00"
    )
    assert row["current_price_source_boundary"] == (
        "asof_candidate_fields_only_no_postdecision_path"
    )
    assert row["predecision_current_price"] == 32.0
    assert row.get("fill_probability") is None
    assert row.get("candidate_fill_probability") is None
    assert row.get("limit_fillability_probability") is None
    assert row.get("predecision_limit_fillability_probability") is None
    assert bridge.execution_fillability_authority(row) == (
        0.92,
        "predecision_limit_fillability.fill_probability",
    )
    assert verifier.current_price_authority_leak_reasons(row) == []


def test_broad_order_trade_path_provenance_scan_accepts_tick_and_labeled_proxy(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    order_path = tmp_path / "ORDER_LEDGER.jsonl"
    trade_path = tmp_path / "TRADE_LEDGER.jsonl"
    write_jsonl(
        order_path,
        [
            {
                "candidate_id": "filled-tick-order",
                "simulated_order_id": "order-tick",
                "symbol": "XAUUSD",
                "order_status": "filled",
                "path_source": "tick",
                "path_index_timeframe": "TICK",
                "path_index_source_path": "/tmp/XAUUSD_ticks.jsonl",
                "path_index_source_sha256": "tick-sha",
                "ordered_tick_truth_satisfied": True,
            },
            {
                "candidate_id": "filled-missing-path-order",
                "simulated_order_id": "order-missing",
                "symbol": "XAUUSD",
                "order_status": "filled",
            },
            {
                "candidate_id": "pending-missing-path-order",
                "simulated_order_id": "order-pending",
                "symbol": "XAUUSD",
                "order_status": "accepted_pending",
            },
        ],
    )
    write_jsonl(
        trade_path,
        [
            {
                "candidate_id": "filled-m1-proxy-trade",
                "simulated_trade_id": "trade-m1",
                "symbol": "XAUUSD",
                "fill_status": "filled_from_ordered_m1_path",
                "path_source": "m1",
                "path_index_timeframe": "M1",
                "path_index_source_path": "/tmp/XAUUSD_M1.csv",
                "path_index_source_sha256": "m1-sha",
                "ordered_tick_truth_satisfied": False,
                "postdecision_path_proxy": True,
                "terminal_r_path_authority": "proxy_replay_not_final_live_proof",
            },
            {
                "candidate_id": "filled-false-tick-claim",
                "simulated_trade_id": "trade-false-tick",
                "symbol": "XAUUSD",
                "fill_status": "filled_from_ordered_m1_path",
                "path_source": "m1",
                "path_index_timeframe": "M1",
                "path_index_source_path": "/tmp/XAUUSD_M1.csv",
                "path_index_source_sha256": "m1-sha",
                "ordered_tick_truth_satisfied": True,
            },
        ],
    )

    scan = verifier.scan_broad_order_trade_path_provenance(
        {"order": order_path, "trade": trade_path}
    )

    assert scan["row_counts"]["order_terminal_rows"] == 2
    assert scan["row_counts"]["trade_terminal_rows"] == 2
    assert scan["bad_counts"]["order:path_provenance_bad"] == 1
    assert scan["bad_counts"]["order:path_source_missing"] == 1
    assert scan["bad_counts"]["order:ordered_tick_truth_satisfied_missing"] == 1
    assert scan["bad_counts"]["trade:path_provenance_bad"] == 1
    assert scan["bad_counts"]["trade:ordered_tick_truth_true_non_tick_path_source"] == 1
    assert scan["bad_counts"]["trade:ordered_tick_truth_true_non_tick_timeframe"] == 1


def test_broad_full_risk_counterfactual_authority_scan_flags_bad_authority_and_arithmetic(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    order_path = tmp_path / "ORDER_LEDGER.jsonl"
    trade_path = tmp_path / "TRADE_LEDGER.jsonl"
    expected_authority = (
        "replay_diagnostic_same_path_scaled_to_risk_reduction_basis_no_broker_authority"
    )
    write_jsonl(order_path, [])
    write_jsonl(
        trade_path,
        [
            {
                "candidate_id": "candidate-good-full-risk",
                "simulated_trade_id": "trade-good",
                "symbol": "XAUUSD",
                "full_risk_counterfactual_applicable": True,
                "full_risk_counterfactual_authority": expected_authority,
                "full_risk_counterfactual_live_broker_authority": False,
                "full_risk_counterfactual_final_selection_claim": False,
                "full_risk_counterfactual_risk_reduction_factor": 0.5,
                "risk_cash": 100.0,
                "net_proxy_r": 1.25,
                "full_risk_counterfactual_risk_cash": 200.0,
                "full_risk_counterfactual_pnl_cash": 250.0,
                "full_risk_counterfactual_pnl_cash_delta": 125.0,
                "full_risk_counterfactual_net_proxy_r": 1.25,
            },
            {
                "candidate_id": "candidate-bad-full-risk",
                "simulated_trade_id": "trade-bad",
                "symbol": "XAUUSD",
                "full_risk_counterfactual_applicable": True,
                "full_risk_counterfactual_authority": "broker_authority_overclaim",
                "full_risk_counterfactual_live_broker_authority": True,
                "full_risk_counterfactual_final_selection_claim": True,
                "full_risk_counterfactual_risk_reduction_factor": 0.5,
                "risk_cash": 100.0,
                "net_proxy_r": 1.25,
                "full_risk_counterfactual_risk_cash": 190.0,
                "full_risk_counterfactual_pnl_cash": 200.0,
                "full_risk_counterfactual_pnl_cash_delta": 50.0,
                "full_risk_counterfactual_net_proxy_r": 1.0,
            },
        ],
    )

    scan = verifier.scan_broad_full_risk_counterfactual_authority(
        {"order": order_path, "trade": trade_path}
    )

    assert scan["row_counts"]["trade_applicable_rows"] == 2
    assert scan["bad_counts"]["trade:full_risk_counterfactual_authority_bad"] == 1
    assert scan["bad_counts"]["trade:full_risk_counterfactual_authority_invalid"] == 1
    assert (
        scan["bad_counts"][
            "trade:full_risk_counterfactual_live_broker_authority_not_false"
        ]
        == 1
    )
    assert (
        scan["bad_counts"][
            "trade:full_risk_counterfactual_final_selection_claim_not_false"
        ]
        == 1
    )
    assert (
        scan["bad_counts"]["trade:full_risk_counterfactual_risk_cash_arithmetic_bad"]
        == 1
    )
    assert (
        scan["bad_counts"]["trade:full_risk_counterfactual_pnl_cash_arithmetic_bad"]
        == 1
    )
    assert (
        scan["bad_counts"][
            "trade:full_risk_counterfactual_pnl_cash_delta_arithmetic_bad"
        ]
        == 1
    )
    assert scan["bad_counts"]["trade:full_risk_counterfactual_net_proxy_r_mismatch"] == 1
    assert scan["sample_bad"][0]["candidate_id"] == "candidate-bad-full-risk"


def test_full_risk_row_missing_signing_condition_fatal(tmp_path: Path) -> None:
    verifier = load_verifier()
    order_path = tmp_path / "ORDER_LEDGER.jsonl"
    trade_path = tmp_path / "TRADE_LEDGER.jsonl"
    missed_path = tmp_path / "MISSED_OPPORTUNITY_LEDGER.jsonl"
    write_jsonl(order_path, [])
    write_jsonl(missed_path, [])
    write_jsonl(
        trade_path,
        [
            {
                "candidate_id": "candidate-full-risk-good",
                "simulated_trade_id": "trade-full-risk-good",
                "package_execution_result_scope": "repaired_executable_package_replay",
                "risk_expression_ladder_tier": "full",
                "risk_expression_ladder": {
                    "signed_authority_valid": True,
                    "broker_cost_passed": True,
                    "source_complete": True,
                    "fill_floor_resolved_or_empty": True,
                    "full_risk_allowed": True,
                    "full_risk_applied": True,
                    "scheduler_top_rank_status": "final_selected_top_rank",
                },
            },
            {
                "candidate_id": "candidate-full-risk-bad",
                "simulated_trade_id": "trade-full-risk-bad",
                "package_execution_result_scope": "repaired_executable_package_replay",
                "risk_expression_ladder_tier": "full",
                "risk_expression_ladder": {
                    "signed_authority_valid": False,
                    "broker_cost_passed": True,
                    "source_complete": True,
                    "fill_floor_resolved_or_empty": True,
                    "full_risk_allowed": True,
                    "full_risk_applied": True,
                    "scheduler_top_rank_status": "final_selected_top_rank",
                },
            },
            {
                "candidate_id": "candidate-full-risk-namespace-bad",
                "simulated_trade_id": "trade-full-risk-namespace-bad",
                "package_execution_result_scope": "repaired_executable_package_replay",
                "risk_expression_ladder_tier": "full",
                "effective_selector_action": "open-reduced-risk",
                "risk_expression_effective_action": "trade",
                "risk_expression_ladder": {
                    "signed_authority_valid": True,
                    "broker_cost_passed": True,
                    "source_complete": True,
                    "fill_floor_resolved_or_empty": True,
                    "full_risk_allowed": True,
                    "full_risk_applied": True,
                    "scheduler_top_rank_status": "final_selected_top_rank",
                },
            },
        ],
    )

    scan = verifier.scan_broad_risk_expression_ladder_authority(
        {"order": order_path, "trade": trade_path, "missed": missed_path}
    )

    assert scan["row_counts"]["trade_full_risk_ladder_rows"] == 3
    assert (
        scan["bad_counts"]["trade:full_risk_ladder_signing_condition_bad"]
        == 2
    )
    assert (
        scan["bad_counts"][
            "trade:full_risk_ladder_signing_condition_false:signed_authority_valid"
        ]
        == 1
    )
    assert (
        scan["bad_counts"][
            "trade:full_risk_namespace_action_not_trade:effective_selector_action:open-reduced-risk"
        ]
        == 1
    )
    assert scan["sample_bad"][0]["candidate_id"] == "candidate-full-risk-bad"


def test_reduced_ladder_with_repaired_priority_rejects_stale_priority_cause(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    order_path = tmp_path / "ORDER_LEDGER.jsonl"
    trade_path = tmp_path / "TRADE_LEDGER.jsonl"
    missed_path = tmp_path / "MISSED_OPPORTUNITY_LEDGER.jsonl"
    write_jsonl(order_path, [])
    write_jsonl(missed_path, [])
    write_jsonl(
        trade_path,
        [
            {
                "candidate_id": "candidate-reduced-stale-priority",
                "simulated_trade_id": "trade-reduced-stale-priority",
                "package_execution_result_scope": "repaired_executable_package_replay",
                "risk_expression_ladder_tier": "reduced",
                "risk_expression_ladder_tier_causes": [
                    "selector_reduced_risk_origin",
                    "scheduler_priority_reduced_tier",
                ],
                "risk_expression_ladder": {
                    "ladder_tier": "reduced",
                    "scheduler_priority_tier": 0,
                    "scheduler_priority_reason": (
                        "selector_reduced_new_entry_no_primary_trade_competitor"
                    ),
                    "tier_causes": [
                        "selector_reduced_risk_origin",
                        "scheduler_priority_reduced_tier",
                    ],
                },
            }
        ],
    )

    scan = verifier.scan_broad_risk_expression_ladder_authority(
        {"order": order_path, "trade": trade_path, "missed": missed_path}
    )

    assert (
        scan["bad_counts"][
            "trade:reduced_ladder_stale_scheduler_priority_cause"
        ]
        == 1
    )
    assert scan["sample_bad"][0]["candidate_id"] == (
        "candidate-reduced-stale-priority"
    )


def test_reduced_signed_executable_ladder_requires_risk_and_fill_floor_proof(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    order_path = tmp_path / "ORDER_LEDGER.jsonl"
    trade_path = tmp_path / "TRADE_LEDGER.jsonl"
    missed_path = tmp_path / "MISSED_OPPORTUNITY_LEDGER.jsonl"
    write_jsonl(missed_path, [])
    write_jsonl(
        order_path,
        [
            {
                "candidate_id": "candidate-reduced-good",
                "simulated_order_id": "order-reduced-good",
                "package_execution_result_scope": "repaired_executable_package_replay",
                "package_replay_order_executable_candidate_use_allowed": True,
                "package_risk_expression_signed_authority_valid": True,
                "risk_expression_ladder_tier": "reduced",
                "risk_expression_ladder_tier_causes": [
                    "execution_fillability_below_full_risk_floor",
                ],
                "package_risk_expression_full_risk_failures": [
                    "execution_fillability_below_full_risk_floor",
                ],
                "package_risk_expression_execution_fill_probability": 0.61,
                "package_risk_expression_execution_fill_probability_full_risk_floor": 0.80,
                "risk_pct_basis": 0.50,
                "runtime_final_risk_pct": 0.25,
                "risk_pct_provenance": {
                    "source": "build_runtime_risk_authority",
                },
            },
            {
                "candidate_id": "candidate-reduced-missing-proof",
                "simulated_order_id": "order-reduced-missing-proof",
                "package_execution_result_scope": "repaired_executable_package_replay",
                "package_replay_order_executable_candidate_use_allowed": True,
                "package_risk_expression_signed_authority_valid": True,
                "risk_expression_ladder_tier": "reduced",
                "risk_expression_ladder_tier_causes": [
                    "execution_fillability_below_full_risk_floor",
                ],
                "package_risk_expression_full_risk_failures": [
                    "execution_fillability_below_full_risk_floor",
                ],
                "runtime_final_risk_pct": 0.25,
            },
        ],
    )
    write_jsonl(trade_path, [])

    scan = verifier.scan_broad_risk_expression_ladder_authority(
        {"order": order_path, "trade": trade_path, "missed": missed_path}
    )

    assert scan["tier_counts"]["order:reduced"] == 2
    assert scan["bad_counts"]["order:reduced_ladder_authority_bad"] == 1
    assert scan["bad_counts"]["order:reduced_ladder_risk_pct_basis_missing"] == 1
    assert scan["bad_counts"]["order:reduced_ladder_risk_pct_provenance_missing"] == 1
    assert scan["bad_counts"]["order:reduced_ladder_fillability_value_missing"] == 1
    assert scan["bad_counts"]["order:reduced_ladder_fillability_floor_missing"] == 1
    assert scan["sample_bad"][0]["candidate_id"] == (
        "candidate-reduced-missing-proof"
    )


def test_missed_opportunity_semantics_scan_rejects_generic_counterfactual_pnl(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    missed_path = tmp_path / "MISSED_OPPORTUNITY_LEDGER.jsonl"
    write_jsonl(
        missed_path,
        [
            {
                "candidate_id": "missed-bad",
                "miss_reason": "selected_candidate_risk_rejected_counterfactual",
                "ordered_path_status": "selected_candidate_blocked_counterfactual_scored",
                "policy_gross_r": 1.25,
                "gross_r": 1.25,
                "net_proxy_r": 1.10,
                "profit_harvest_mfe_capture_replay_exit": {"final_r": 1.25},
                "profit_harvest_mfe_capture_replay_bound": True,
            },
            {
                "candidate_id": "missed-good",
                "miss_reason": "selected_candidate_risk_rejected_counterfactual",
                "ordered_path_status": "selected_candidate_blocked_counterfactual_scored",
                "policy_gross_r": 1.25,
                "counterfactual_gross_r": 1.25,
                "counterfactual_net_proxy_r": 1.10,
                "opportunity_gross_r": 1.25,
                "opportunity_net_proxy_r": 1.10,
                "gross_r": None,
                "net_proxy_r": None,
                "profit_harvest_mfe_capture_replay_exit": None,
                "profit_harvest_mfe_capture_replay_bound": False,
            },
            {
                "candidate_id": "missed-not-sent-headline-leak",
                "miss_reason": "candidate_generated_not_scheduler_selected",
                "ordered_path_status": "scored_for_nonselected_candidate",
                "order_status": "not_sent_missed_opportunity",
                "executable_finalized": False,
                "missed_row_executable_finalized": False,
                "opportunity_gross_r": 1.50,
                "opportunity_net_proxy_r": 1.35,
                "gross_r": None,
                "net_proxy_r": 1.35,
                "missed_opportunity_headline_r_scoreable": True,
                "missed_opportunity_r_scoreability_status": "headline_r_scoreable",
            },
        ],
    )

    scan = verifier.scan_broad_missed_opportunity_semantics(missed_path)

    assert scan["row_counts"]["missed_rows"] == 3
    assert scan["row_counts"]["unexecuted_missed_rows"] == 3
    assert (
        scan["bad_counts"][
            "missed:counterfactual_missed_generic_pnl_present:gross_r"
        ]
        == 1
    )
    assert (
        scan["bad_counts"][
            "missed:counterfactual_missed_generic_pnl_present:net_proxy_r"
        ]
        == 1
    )
    assert (
        scan["bad_counts"][
            "missed:counterfactual_missed_generic_profit_harvest_exit_present"
        ]
        == 1
    )
    assert (
        scan["bad_counts"][
            "missed:counterfactual_missed_generic_profit_harvest_bound_true"
        ]
        == 1
    )
    assert (
        scan["bad_counts"][
            "missed:unexecuted_missed_generic_pnl_present:net_proxy_r"
        ]
        == 2
    )
    assert (
        scan["bad_counts"]["missed:unexecuted_missed_headline_r_scoreable_true"]
        == 1
    )
    assert (
        scan["bad_counts"][
            "missed:unexecuted_missed_scoreability_status_headline_r_scoreable"
        ]
        == 1
    )
    assert scan["sample_bad"][0]["candidate_id"] == "missed-bad"


def test_verification_scan_shape_issues_fail_closed_on_missing_required_key() -> None:
    verifier = load_verifier()

    issues = verifier.verification_scan_shape_issues(
        {
            "missing_scan": (None, ("paths", "bad_counts")),
            "not_mapping_scan": ([], ("paths", "bad_counts")),
            "missing_key_scan": ({"paths": {}}, ("paths", "bad_counts")),
        }
    )

    assert "verification_scan_missing:missing_scan" in issues
    assert "verification_scan_not_mapping:not_mapping_scan" in issues
    assert "verification_scan_key_missing:missing_key_scan:bad_counts" in issues


def test_broad_quality_selected_prefix_rejects_zero_byte_required_execution_ledgers(
    tmp_path: Path, monkeypatch
) -> None:
    verifier = load_verifier()
    monkeypatch.setattr(verifier, "ROUTE", tmp_path)
    prefix = "BROAD_LIVE_AS_IF_REPLAY_ZERO_BYTE_REQUIRED_SMOKE"
    write_completed_broad_quality_family(verifier, tmp_path, prefix)
    paths = verifier.broad_quality_artifact_paths(
        prefix,
        verifier.broad_quality_artifact_tag(prefix),
    )
    for name in ("decision", "order", "trade"):
        paths[name].write_text("", encoding="utf-8")

    monkeypatch.setenv("GTOS_BROAD_QUALITY_PARITY_PREFIX", prefix)
    issues: list[str] = []
    selected_prefix, selected_tag, _ = verifier.select_broad_quality_parity_artifacts(
        issues,
        {"broad_quality_parity_prefix": prefix},
    )

    assert selected_prefix == prefix
    assert selected_tag == "ZERO_BYTE_REQUIRED_SMOKE"
    assert any(
        issue.startswith(
            "broad_quality_parity_selected_prefix_zero_byte_required_ledgers:"
        )
        and "decision" in issue
        and "order" in issue
        and "trade" in issue
        for issue in issues
    )


def test_broad_quality_selected_prefix_rejects_zero_byte_required_aux_execution_ledgers(
    tmp_path: Path, monkeypatch
) -> None:
    verifier = load_verifier()
    monkeypatch.setattr(verifier, "ROUTE", tmp_path)
    prefix = "BROAD_LIVE_AS_IF_REPLAY_ZERO_BYTE_AUX_REQUIRED_SMOKE"
    write_completed_broad_quality_family(verifier, tmp_path, prefix)
    paths = verifier.broad_quality_artifact_paths(
        prefix,
        verifier.broad_quality_artifact_tag(prefix),
    )
    summary = json.loads(paths["summary"].read_text(encoding="utf-8"))
    summary["comparison_ledger_rows"] = 1
    paths["summary"].write_text(json.dumps(summary, sort_keys=True), encoding="utf-8")
    for name in ("source_universe", "bucket", "comparison"):
        paths[name].write_text("", encoding="utf-8")

    monkeypatch.setenv("GTOS_BROAD_QUALITY_PARITY_PREFIX", prefix)
    issues: list[str] = []
    selected_prefix, selected_tag, _ = verifier.select_broad_quality_parity_artifacts(
        issues,
        {"broad_quality_parity_prefix": prefix},
    )

    assert selected_prefix == prefix
    assert selected_tag == "ZERO_BYTE_AUX_REQUIRED_SMOKE"
    assert any(
        issue.startswith(
            "broad_quality_parity_selected_prefix_zero_byte_required_ledgers:"
        )
        and "source_universe" in issue
        and "bucket" in issue
        and "comparison" in issue
        for issue in issues
    )


def test_broad_quality_selected_prefix_rejects_summary_physical_row_count_mismatch(
    tmp_path: Path, monkeypatch
) -> None:
    verifier = load_verifier()
    monkeypatch.setattr(verifier, "ROUTE", tmp_path)
    prefix = "BROAD_LIVE_AS_IF_REPLAY_ROW_COUNT_MISMATCH_SMOKE"
    write_completed_broad_quality_family(verifier, tmp_path, prefix)
    paths = verifier.broad_quality_artifact_paths(
        prefix,
        verifier.broad_quality_artifact_tag(prefix),
    )
    summary = json.loads(paths["summary"].read_text(encoding="utf-8"))
    summary["ledger_write_row_counts"] = {"decision": 2}
    paths["summary"].write_text(json.dumps(summary), encoding="utf-8")
    paths["decision"].write_text(json.dumps({"row_type": "asof_decision"}) + "\n")

    monkeypatch.setenv("GTOS_BROAD_QUALITY_PARITY_PREFIX", prefix)
    issues: list[str] = []
    selected_prefix, selected_tag, _ = verifier.select_broad_quality_parity_artifacts(
        issues,
        {"broad_quality_parity_prefix": prefix},
    )

    assert selected_prefix == prefix
    assert selected_tag == "ROW_COUNT_MISMATCH_SMOKE"
    assert any(
        issue.startswith(
            "broad_quality_parity_selected_prefix_row_count_mismatch:"
        )
        and "'decision': {'summary': 2, 'physical': 1}" in issue
        for issue in issues
    )


def test_broad_quality_selected_prefix_allows_zero_byte_omitted_identity_ledgers(
    tmp_path: Path, monkeypatch
) -> None:
    verifier = load_verifier()
    monkeypatch.setattr(verifier, "ROUTE", tmp_path)
    prefix = "BROAD_LIVE_AS_IF_REPLAY_OMITTED_IDENTITY_LEDGER_SMOKE"
    write_completed_broad_quality_family(verifier, tmp_path, prefix)
    paths = verifier.broad_quality_artifact_paths(
        prefix,
        verifier.broad_quality_artifact_tag(prefix),
    )
    summary = json.loads(paths["summary"].read_text(encoding="utf-8"))
    summary["candidate_ledger_omitted"] = True
    summary["packet_sidecar_ledger_omitted"] = True
    paths["summary"].write_text(json.dumps(summary), encoding="utf-8")
    paths["candidate"].write_text("", encoding="utf-8")
    paths["packet_sidecar"].write_text("", encoding="utf-8")
    paths["candidate_index"].write_text(
        json.dumps({"candidate_id": prefix}) + "\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("GTOS_BROAD_QUALITY_PARITY_PREFIX", prefix)
    issues: list[str] = []
    selected_prefix, selected_tag, _ = verifier.select_broad_quality_parity_artifacts(
        issues,
        {"broad_quality_parity_prefix": prefix},
    )

    assert selected_prefix == prefix
    assert selected_tag == "OMITTED_IDENTITY_LEDGER_SMOKE"
    assert issues == []


def test_builder_uses_newest_completed_broad_quality_prefix_before_stale_pin(
    tmp_path: Path, monkeypatch
) -> None:
    builder = load_builder()
    monkeypatch.setattr(builder, "ROUTE", tmp_path)
    monkeypatch.delenv("GTOS_BROAD_QUALITY_PARITY_PREFIX", raising=False)
    pinned_prefix = "BROAD_LIVE_AS_IF_REPLAY_MEMBER_AXIS_COST_GAP_SMOKE"
    competing_prefix = "BROAD_LIVE_AS_IF_REPLAY_Z_COMPETING_REPAIR_SMOKE"
    write_completed_broad_quality_family(builder, tmp_path, pinned_prefix)
    write_completed_broad_quality_family(builder, tmp_path, competing_prefix)
    (tmp_path / "VERIFICATION_RESULT.json").write_text(
        json.dumps({"broad_live_as_if_quality_parity_prefix": pinned_prefix}),
        encoding="utf-8",
    )

    selected_prefix, selected_tag = builder.select_current_broad_quality_prefix()

    assert selected_prefix == competing_prefix
    assert selected_tag == "Z_COMPETING_REPAIR_SMOKE"

    monkeypatch.setenv("GTOS_BROAD_QUALITY_PARITY_PREFIX", pinned_prefix)
    selected_prefix, selected_tag = builder.select_current_broad_quality_prefix()
    assert selected_prefix == pinned_prefix
    assert selected_tag == "MEMBER_AXIS_COST_GAP_SMOKE"


def test_builder_prefers_current_root_map_without_exhaustive_sweep(
    tmp_path: Path, monkeypatch
) -> None:
    builder = load_builder()
    monkeypatch.setattr(builder, "ROOT", tmp_path)
    monkeypatch.setattr(builder, "ROUTE", tmp_path)
    monkeypatch.delenv("GTOS_BROAD_QUALITY_PARITY_PREFIX", raising=False)
    monkeypatch.delenv("GTOS_BROAD_QUALITY_EXHAUSTIVE_PREFIX_SCAN", raising=False)
    current_prefix = "BROAD_LIVE_AS_IF_REPLAY_A_CURRENT_ROOT_SMOKE"
    newer_prefix = "BROAD_LIVE_AS_IF_REPLAY_Z_NEWER_HISTORICAL_SMOKE"
    write_completed_broad_quality_family(builder, tmp_path, current_prefix)
    write_completed_broad_quality_family(builder, tmp_path, newer_prefix)
    (tmp_path / "OUTPUT_MANIFEST.json").write_text(
        json.dumps({"broad_quality_parity_prefix": newer_prefix}),
        encoding="utf-8",
    )
    (tmp_path / f"{newer_prefix}_SUMMARY.json").touch()
    root_map = tmp_path / ".context/context_os/CURRENT_ROOT_CAUSE_MAP.json"
    root_map.parent.mkdir(parents=True, exist_ok=True)
    root_map.write_text(
        json.dumps({"latest_completed_replay": {"prefix": current_prefix}}),
        encoding="utf-8",
    )

    selected_prefix, selected_tag = builder.select_current_broad_quality_prefix()

    assert selected_prefix == current_prefix
    assert selected_tag == "A_CURRENT_ROOT_SMOKE"

    monkeypatch.setenv("GTOS_BROAD_QUALITY_EXHAUSTIVE_PREFIX_SCAN", "1")
    selected_prefix, selected_tag = builder.select_current_broad_quality_prefix()
    assert selected_prefix == newer_prefix
    assert selected_tag == "Z_NEWER_HISTORICAL_SMOKE"


def test_builder_uses_recent_complete_prefix_when_current_root_incomplete(
    tmp_path: Path, monkeypatch
) -> None:
    builder = load_builder()
    monkeypatch.setattr(builder, "ROOT", tmp_path)
    monkeypatch.setattr(builder, "ROUTE", tmp_path)
    monkeypatch.delenv("GTOS_BROAD_QUALITY_PARITY_PREFIX", raising=False)
    monkeypatch.delenv("GTOS_BROAD_QUALITY_EXHAUSTIVE_PREFIX_SCAN", raising=False)
    current_prefix = "BROAD_LIVE_AS_IF_REPLAY_A_INCOMPLETE_ROOT_SMOKE"
    newer_prefix = "BROAD_LIVE_AS_IF_REPLAY_Z_NEWER_COMPLETE_SMOKE"
    write_completed_broad_quality_family(builder, tmp_path, current_prefix)
    write_completed_broad_quality_family(builder, tmp_path, newer_prefix)
    (tmp_path / f"{current_prefix}_CANDIDATE_LEDGER.jsonl").unlink()
    (tmp_path / f"{newer_prefix}_SUMMARY.json").touch()
    root_map = tmp_path / ".context/context_os/CURRENT_ROOT_CAUSE_MAP.json"
    root_map.parent.mkdir(parents=True, exist_ok=True)
    root_map.write_text(
        json.dumps({"latest_completed_replay": {"prefix": current_prefix}}),
        encoding="utf-8",
    )

    selected_prefix, selected_tag = builder.select_current_broad_quality_prefix()

    assert selected_prefix == newer_prefix
    assert selected_tag == "Z_NEWER_COMPLETE_SMOKE"


def test_builder_manifest_includes_resolved_tag_vs_behavior_summary(
    tmp_path: Path, monkeypatch
) -> None:
    builder = load_builder()
    monkeypatch.setattr(builder, "ROUTE", tmp_path)
    prefix = "BROAD_LIVE_AS_IF_REPLAY_V231_CURRENT"
    tag = "V231_CURRENT"
    comparison_name = (
        "V231_CURRENT_VS_V230_BASELINE_deadbeef_BEHAVIOR_COMPARISON_SUMMARY.json"
    )
    (tmp_path / f"{prefix}_SUMMARY.json").write_text("{}", encoding="utf-8")
    (tmp_path / comparison_name).write_text("{}", encoding="utf-8")

    required = builder.broad_quality_required_manifest_files(prefix, tag)

    assert comparison_name in required
    assert (
        "CANDIDATE_INSTANCE_PARITY_PROJECTION_V231_CURRENT_LEDGER.jsonl"
        in required
    )


def test_builder_manifest_requires_flow_bucket_when_flow_summary_exists(
    tmp_path: Path, monkeypatch
) -> None:
    builder = load_builder()
    prefix = "BROAD_LIVE_AS_IF_REPLAY_V231_FLOW_PAIR"
    tag = "V231_FLOW_PAIR"
    monkeypatch.setattr(builder, "ROUTE", tmp_path)
    (tmp_path / f"{prefix}_SUMMARY.json").write_text("{}", encoding="utf-8")
    (tmp_path / f"{prefix}_FLOW_DIAGNOSTIC_SUMMARY.json").write_text(
        "{}",
        encoding="utf-8",
    )

    required = builder.broad_quality_required_manifest_files(prefix, tag)

    assert f"{prefix}_FLOW_DIAGNOSTIC_SUMMARY.json" in required
    assert f"{prefix}_FLOW_BUCKET_LEDGER.jsonl" in required


def test_builder_and_verifier_manifest_include_poi_rehydration_result(
    tmp_path: Path, monkeypatch
) -> None:
    builder = load_builder()
    verifier = load_verifier()
    prefix = "BROAD_LIVE_AS_IF_REPLAY_V249_CURRENT"
    tag = "V249_CURRENT"
    result_name = f"{prefix}_CANDIDATE_INDEX_POI_REHYDRATION_RESULT.json"
    monkeypatch.setattr(builder, "ROUTE", tmp_path)
    monkeypatch.setattr(verifier, "ROUTE", tmp_path)
    (tmp_path / f"{prefix}_SUMMARY.json").write_text("{}", encoding="utf-8")
    (tmp_path / result_name).write_text("{}", encoding="utf-8")

    assert result_name in builder.broad_quality_required_manifest_files(prefix, tag)
    assert result_name in verifier.broad_quality_required_files(prefix, tag)


def test_builder_and_verifier_manifest_include_terminal_cost_alias_repair(
    tmp_path: Path, monkeypatch
) -> None:
    builder = load_builder()
    verifier = load_verifier()
    prefix = "BROAD_LIVE_AS_IF_REPLAY_V258_CURRENT"
    tag = "V258_CURRENT"
    result_name = f"{prefix}_TERMINAL_CANDIDATE_COST_ALIAS_REPAIR_SUMMARY.json"
    monkeypatch.setattr(builder, "ROUTE", tmp_path)
    monkeypatch.setattr(verifier, "ROUTE", tmp_path)
    (tmp_path / f"{prefix}_SUMMARY.json").write_text("{}", encoding="utf-8")
    (tmp_path / result_name).write_text("{}", encoding="utf-8")

    assert result_name in builder.broad_quality_required_manifest_files(prefix, tag)
    assert result_name in verifier.broad_quality_required_files(prefix, tag)


def test_builder_and_verifier_resolve_bounded_behavior_artifacts_by_prefix(
    tmp_path: Path, monkeypatch
) -> None:
    builder = load_builder()
    verifier = load_verifier()
    prefix = (
        "BROAD_LIVE_AS_IF_REPLAY_V249_B7_2_HOSTILE_5D_"
        "FULL_UNBOUNDED_REPLAY_PREFIX"
    )
    tag = "V249_B7_2_HOSTILE_5D_FULL_UNBOUNDED_REPLAY_PREFIX"
    comparison_name = (
        "V249_B7_2_HOSTILE_5D_BOUNDED_deadbeef_"
        "BEHAVIOR_COMPARISON_SUMMARY.json"
    )
    dossier_name = "V249_B7_2_HOSTILE_5D_BOUNDED_deadbeef_BEHAVIOR_DOSSIER.md"
    monkeypatch.setattr(builder, "ROUTE", tmp_path)
    monkeypatch.setattr(verifier, "ROUTE", tmp_path)
    (tmp_path / f"{prefix}_SUMMARY.json").write_text("{}", encoding="utf-8")
    (tmp_path / dossier_name).write_text("# Dossier\n", encoding="utf-8")
    (tmp_path / comparison_name).write_text(
        json.dumps(
            {
                "repair_prefix": prefix,
                "artifacts": {"behavior_dossier": str(tmp_path / dossier_name)},
            }
        ),
        encoding="utf-8",
    )

    builder_required = set(
        builder.broad_quality_required_manifest_files(prefix, tag)
    )
    verifier_required = verifier.broad_quality_required_files(prefix, tag)
    assert {comparison_name, dossier_name} <= builder_required
    assert {comparison_name, dossier_name} <= verifier_required


def test_builder_and_verifier_resolve_same_window_candidate_prefix_and_inputs(
    tmp_path: Path, monkeypatch
) -> None:
    builder = load_builder()
    verifier = load_verifier()
    prefix = (
        "BROAD_LIVE_AS_IF_REPLAY_V258_B7_4_FULL_UNBOUNDED_REPLAY_PREFIX"
    )
    tag = "V258_B7_4_FULL_UNBOUNDED_REPLAY_PREFIX"
    comparison_name = (
        "V258_B7_4_BOUNDED_deadbeef_BEHAVIOR_COMPARISON_SUMMARY.json"
    )
    dossier_name = "V258_B7_4_BOUNDED_deadbeef_BEHAVIOR_DOSSIER.md"
    baseline_inputs = {
        "baseline_summary": "BASE_SUMMARY.json",
        "baseline_trade_ledger": "BASE_TRADE_LEDGER.jsonl",
        "baseline_parity_summary": "BASE_PARITY_SUMMARY.json",
    }
    monkeypatch.setattr(builder, "ROUTE", tmp_path)
    monkeypatch.setattr(verifier, "ROUTE", tmp_path)
    (tmp_path / f"{prefix}_SUMMARY.json").write_text("{}", encoding="utf-8")
    (tmp_path / dossier_name).write_text("# Dossier\n", encoding="utf-8")
    for filename in baseline_inputs.values():
        (tmp_path / filename).write_text("{}\n", encoding="utf-8")
    (tmp_path / comparison_name).write_text(
        json.dumps(
            {
                "candidate_prefix": prefix,
                "artifacts": {
                    "behavior_dossier": str(tmp_path / dossier_name),
                    **{
                        key: str(tmp_path / filename)
                        for key, filename in baseline_inputs.items()
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    assert builder.broad_quality_behavior_summary_path(prefix).name == comparison_name
    assert verifier.broad_quality_behavior_summary_path(prefix).name == comparison_name
    expected = {comparison_name, dossier_name, *baseline_inputs.values()}
    assert expected <= set(builder.broad_quality_required_manifest_files(prefix, tag))
    assert expected <= verifier.broad_quality_required_files(prefix, tag)


def test_b7_4_behavior_comparison_requires_identity_and_named_winner_blockers() -> None:
    verifier = load_verifier()
    prefix = "BROAD_LIVE_AS_IF_REPLAY_V258_B7_4_CURRENT"
    summary = {
        "schema": (
            "gtos.final_moonshot.broad_live_as_if_replay."
            "same_window_comparison.v1"
        ),
        "candidate_prefix": prefix,
        "trade_identity_comparison_status": "computed",
        "trade_key_counts": {"common": 14, "removed": 2},
        "trade_identity_comparison_authority": {
            role: {
                "status": "present",
                "comparable": True,
                "expected_rows_inside_summary_window": count,
                "observed_rows_inside_summary_window": count,
                "byte_count": count * 100,
                "sha256": char * 64,
            }
            for role, count, char in (
                ("baseline", 95, "a"),
                ("candidate", 42, "b"),
            )
        },
        "baseline": {"scorecard_rows": 1056},
        "candidate": {"scorecard_rows": 1440},
        "removed_trade_current_projection_rows": [
            {
                "baseline_net_r": 1.5,
                "current_blocker_stage": "scheduler_allocation",
                "current_blocker_reason": "scheduler_not_selected",
            },
            {
                "baseline_net_r": -1.0,
                "current_blocker_stage": "selector_admission",
                "current_blocker_reason": "broker_cost_refused",
            },
        ],
    }

    assert verifier.b7_4_behavior_comparison_issues(summary, prefix=prefix) == []

    summary["trade_key_counts"]["common"] = 0
    summary["removed_trade_current_projection_rows"][0][
        "current_blocker_reason"
    ] = ""
    assert verifier.b7_4_behavior_comparison_issues(summary, prefix=prefix) == [
        "b7_4_common_trade_overlap_not_positive",
        "b7_4_removed_winner_blocker_reason_missing",
    ]


def test_builder_manifest_follows_producer_bound_parity_artifacts(
    tmp_path: Path, monkeypatch
) -> None:
    builder = load_builder()
    monkeypatch.setattr(builder, "ROUTE", tmp_path)
    prefix = "BROAD_LIVE_AS_IF_REPLAY_V245_LONG_REPLAY_TAG"
    tag = "V245_LONG_REPLAY_TAG"
    short_tag = "V245_BOUND_PROOF"
    parity_summary = tmp_path / (
        f"SOURCE_BOUND_TO_EXECUTED_PARITY_{short_tag}_SUMMARY.json"
    )
    artifacts = {
        "big_r_provenance_breakdown": str(
            tmp_path / f"BIG_R_PROVENANCE_BREAKDOWN_{short_tag}.json"
        ),
        "source_bound_to_executed_parity_ledger": str(
            tmp_path / f"SOURCE_BOUND_TO_EXECUTED_PARITY_{short_tag}_LEDGER.jsonl"
        ),
        "candidate_instance_parity_projection_ledger": str(
            tmp_path
            / f"CANDIDATE_INSTANCE_PARITY_PROJECTION_{short_tag}_LEDGER.jsonl"
        ),
        "execution_leakage_bucket_ledger": str(
            tmp_path / f"EXECUTION_LEAKAGE_BUCKET_{short_tag}_LEDGER.jsonl"
        ),
        "execution_leakage_repair_plan": str(
            tmp_path / f"EXECUTION_LEAKAGE_REPAIR_PLAN_{short_tag}.json"
        ),
    }
    parity_summary.write_text(
        json.dumps(
            {
                "broad_replay_prefix": prefix,
                "artifacts": artifacts,
            }
        ),
        encoding="utf-8",
    )

    required = builder.broad_quality_required_manifest_files(prefix, tag)

    assert parity_summary.name in required
    assert (
        f"CANDIDATE_INSTANCE_PARITY_PROJECTION_{short_tag}_LEDGER.jsonl"
        in required
    )
    assert not any(
        f"CANDIDATE_INSTANCE_PARITY_PROJECTION_{tag}" in filename
        for filename in required
    )


def test_broad_trade_cost_scan_requires_net_arithmetic_and_scope(tmp_path: Path) -> None:
    verifier = load_verifier()
    order_path = tmp_path / "orders.jsonl"
    trade_path = tmp_path / "trades.jsonl"
    base = {
        "candidate_id": "candidate-1",
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "candidate_cost_r_fallback_is_authority": False,
        "fill_realism_class": "passive_queue_confirmed",
    }
    write_jsonl(
        order_path,
        [
            {**base, "order_status": "accepted"},
            {
                **base,
                "candidate_id": "candidate-proxy-cost",
                "order_status": "accepted",
                "cost_authority": "timewarp_candidate_cost_proxy",
            },
            {
                **{
                    key: value
                    for key, value in base.items()
                    if key != "cost_authority"
                },
                "candidate_id": "candidate-missing-cost-authority",
                "order_status": "accepted",
            },
            {
                **base,
                "candidate_id": "candidate-diagnostic-cost",
                "order_status": "accepted",
                "package_execution_result_scope": "diagnostic_counterfactual_only",
                "cost_authority": "timewarp_candidate_cost_proxy",
                "pretrade_cost_packet_status": "REFUSED",
                "fill_realism_class": "first_touch_optimistic",
            },
            {
                **{
                    key: value
                    for key, value in base.items()
                    if key != "fill_realism_class"
                },
                "candidate_id": "candidate-pending-awaiting-terminal-fill",
                "simulated_order_id": "order-pending-awaiting-terminal-fill",
                "order_status": "pending_accepted",
                "is_terminal_order_event": False,
                "entry_fill_executable": False,
                "fill_status": None,
            },
            {
                **base,
                "candidate_id": "candidate-pending-forbidden-fill-realism",
                "simulated_order_id": "order-pending-forbidden-fill-realism",
                "order_status": "pending_accepted",
                "is_terminal_order_event": False,
                "entry_fill_executable": False,
                "fill_status": None,
                "fill_realism_class": "first_touch_optimistic",
            },
            {
                **base,
                "candidate_id": "candidate-pending-authority-leak",
                "simulated_order_id": "order-pending-authority-leak",
                "order_status": "pending_accepted",
                "is_terminal_order_event": False,
                "entry_fill_executable": False,
                "fill_status": None,
                "same_bar_ambiguity": True,
                "final_r_authority": True,
            },
            {
                **{
                    key: value
                    for key, value in base.items()
                    if key != "fill_realism_class"
                },
                "candidate_id": "candidate-missing-fill-realism",
                "order_status": "accepted",
            },
            {
                **base,
                "candidate_id": "candidate-unknown-fill-realism",
                "order_status": "accepted",
                "fill_realism_class": "unknown",
            },
            {
                **base,
                "candidate_id": "candidate-first-touch-fill-realism",
                "order_status": "accepted",
                "fill_realism_class": "first_touch_optimistic",
            },
            {
                **base,
                "candidate_id": "candidate-legacy-m1-fill-realism",
                "order_status": "accepted",
                "fill_realism_class": "legacy_m1_first_touch_no_queue_realism",
            },
            {
                **base,
                "candidate_id": "candidate-same-bar-final-authority",
                "order_status": "accepted",
                "same_bar_ambiguity": True,
                "final_r_authority": True,
            },
            {
                **base,
                "candidate_id": "candidate-guarded-fallback-final-authority",
                "order_status": "accepted",
                "fill_realism_class": "guarded_market_fallback_elapsed_path",
                "headline_result_authority": True,
            },
            {
                **base,
                "candidate_id": "candidate-ordered-tick-gap-fill-realism",
                "order_status": "accepted",
                "fill_realism_class": "passive_queue_confirmed",
                "source_gaps": [
                    "ordered_tick_required_for_adverse_before_profit_sequence"
                ],
            },
            {
                **base,
                "candidate_id": "candidate-source-gap-cost-order",
                "simulated_order_id": "order-source-gap-cost",
                "order_status": "pending_accepted",
                "cost_source_gap_status": "mt5_tick_spread_floor_missing",
                "source_gap_cost_fallback_blocked": True,
            },
        ],
    )
    write_jsonl(
        trade_path,
        [
            {
                **base,
                "candidate_id": "candidate-terminal-r-unscoreable",
                "simulated_trade_id": "trade-terminal-r-unscoreable",
                "entry_fill_executable": True,
                "terminal_r_scoreable": False,
                "final_r": None,
                "expected_cost_r": 0.10,
                "net_proxy_r": None,
                "net_cost_scope": (
                    "broker_pretrade_plus_optional_fallback_surcharge_not_close_side_all_in"
                ),
                "close_side_all_in_cost_status": "not_joined_in_replay_net_proxy_r",
            },
            {
                **base,
                "candidate_id": "candidate-scoreable-missing-arithmetic",
                "simulated_trade_id": "trade-scoreable-missing-arithmetic",
                "entry_fill_executable": True,
                "terminal_r_scoreable": True,
                "final_r": None,
                "expected_cost_r": 0.10,
                "net_proxy_r": None,
                "net_cost_scope": (
                    "broker_pretrade_plus_optional_fallback_surcharge_not_close_side_all_in"
                ),
                "close_side_all_in_cost_status": "not_joined_in_replay_net_proxy_r",
            },
            {
                **base,
                "candidate_id": "candidate-terminal-r-unscoreable-missing-cost",
                "simulated_trade_id": "trade-terminal-r-unscoreable-missing-cost",
                "entry_fill_executable": True,
                "terminal_r_scoreable": False,
                "final_r": None,
                "expected_cost_r": None,
                "net_proxy_r": None,
                "net_cost_scope": (
                    "broker_pretrade_plus_optional_fallback_surcharge_not_close_side_all_in"
                ),
                "close_side_all_in_cost_status": "not_joined_in_replay_net_proxy_r",
            },
            {
                **base,
                "candidate_id": "candidate-terminal-r-unscoreable-stale-final-r",
                "simulated_trade_id": "trade-terminal-r-unscoreable-stale-final-r",
                "entry_fill_executable": True,
                "terminal_r_scoreable": False,
                "final_r": 1.25,
                "expected_cost_r": 0.10,
                "net_proxy_r": None,
                "net_cost_scope": (
                    "broker_pretrade_plus_optional_fallback_surcharge_not_close_side_all_in"
                ),
                "close_side_all_in_cost_status": "not_joined_in_replay_net_proxy_r",
            },
            {
                **base,
                "simulated_trade_id": "trade-good",
                "final_r": 1.25,
                "expected_cost_r": 0.10,
                "net_proxy_r": 1.15,
                "net_cost_scope": (
                    "broker_pretrade_plus_optional_fallback_surcharge_not_close_side_all_in"
                ),
                "close_side_all_in_cost_status": "not_joined_in_replay_net_proxy_r",
            },
            {
                **base,
                "simulated_trade_id": "trade-m15-proxy",
                "candidate_id": "candidate-m15-proxy-fill-realism",
                "fill_realism_class": "m15_proxy",
                "final_r": 1.25,
                "expected_cost_r": 0.10,
                "net_proxy_r": 1.15,
                "net_cost_scope": (
                    "broker_pretrade_plus_optional_fallback_surcharge_not_close_side_all_in"
                ),
                "close_side_all_in_cost_status": "not_joined_in_replay_net_proxy_r",
            },
            {
                **base,
                "simulated_trade_id": "trade-ordered-tick-gap",
                "candidate_id": "candidate-ordered-tick-gap-fill-realism",
                "fill_realism_class": "passive_queue_confirmed",
                "source_gaps": [
                    "ordered_tick_required_for_adverse_before_profit_sequence"
                ],
                "final_r": 1.25,
                "expected_cost_r": 0.10,
                "net_proxy_r": 1.15,
                "net_cost_scope": (
                    "broker_pretrade_plus_optional_fallback_surcharge_not_close_side_all_in"
                ),
                "close_side_all_in_cost_status": "not_joined_in_replay_net_proxy_r",
            },
            {
                **base,
                "simulated_trade_id": "trade-bad",
                "final_r": 1.25,
                "expected_cost_r": 0.10,
                "net_proxy_r": 1.20,
                "net_cost_scope": "close_side_all_in",
                "close_side_all_in_cost_status": "close_side_all_in_cost_joined",
                "close_side_all_in_cost_joined": False,
            },
            {
                **base,
                "candidate_id": "candidate-source-gap-cost-trade",
                "simulated_trade_id": "trade-source-gap-cost",
                "cost_source_gap_status": "mt5_tick_spread_floor_missing",
                "source_gap_cost_fallback_blocked": True,
                "final_r": 1.25,
                "expected_cost_r": 0.10,
                "net_proxy_r": 1.15,
                "net_cost_scope": (
                    "broker_pretrade_plus_optional_fallback_surcharge_not_close_side_all_in"
                ),
                "close_side_all_in_cost_status": "not_joined_in_replay_net_proxy_r",
            },
        ],
    )

    scan = verifier.scan_broad_order_trade_cost_authority(
        {"order": order_path, "trade": trade_path}
    )

    bad = scan["bad_counts"]
    assert bad["trade:net_proxy_r_not_final_r_minus_expected_cost_r"] == 1
    assert bad["trade:net_proxy_arithmetic_missing_fields"] == 3
    assert bad["trade:net_cost_scope:close_side_all_in"] == 1
    assert bad["trade:close_side_all_in_cost_join_overclaimed"] == 1
    assert bad["order:executable_fill_realism_class_missing"] == 1
    assert bad["order:executable_fill_realism_class_unknown"] == 1
    assert bad["order:first_touch_optimistic_fill_marked_executable"] == 2
    assert bad["order:legacy_m1_first_touch_no_queue_realism_fill_marked_executable"] == 1
    assert bad["order:same_bar_ambiguity_claims_final_or_headline_authority"] == 2
    assert (
        bad[
            "order:guarded_market_fallback_elapsed_path_claims_final_or_live_authority"
        ]
        == 1
    )
    assert bad["order:ordered_tick_required_source_gap_marked_executable"] == 1
    assert bad["trade:m15_proxy_fill_marked_executable"] == 1
    assert bad["trade:ordered_tick_required_source_gap_marked_executable"] == 1
    assert bad["order:cost_refused_or_source_gap_materialized"] == 1
    assert bad["trade:cost_refused_or_source_gap_materialized"] == 1
    assert bad["order:materialized_cost_source_gap:mt5_tick_spread_floor_missing"] == 1
    assert bad["trade:materialized_cost_source_gap:mt5_tick_spread_floor_missing"] == 1
    assert bad["order:cost_authority:timewarp_candidate_cost_proxy"] == 1
    assert bad["order:cost_authority:missing"] == 1
    assert scan["row_counts"]["order_diagnostic_or_non_executable_rows"] == 1
    assert (
        scan["row_counts"][
            "order_pending_intent_awaiting_terminal_fill_realism_rows"
        ]
        == 1
    )
    assert (
        scan["row_counts"][
            "trade_entry_fill_terminal_r_unscoreable_arithmetic_not_applicable_rows"
        ]
        == 1
    )


def test_guarded_fallback_damage_scan_blocks_limit_winner_to_fallback_loser(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    trade_path = tmp_path / "trades.jsonl"
    write_jsonl(
        trade_path,
        [
            {
                "candidate_id": "candidate-damaged",
                "simulated_trade_id": "trade-damaged",
                "symbol": "UKOIL_cash",
                "side": "LONG",
                "guarded_market_fallback_applied": True,
                "limit_first_terminal_outcome": "target_reached_before_stop",
                "close_reason": "stop_reached_before_target",
                "net_proxy_r": -1.0,
                "fallback_vs_limit_full_horizon_delta_r": -3.0,
            },
            {
                "candidate_id": "candidate-ok",
                "simulated_trade_id": "trade-ok",
                "guarded_market_fallback_applied": True,
                "limit_first_terminal_outcome": "not_filled",
                "close_reason": "target_reached_before_stop",
            },
        ],
    )

    scan = verifier.scan_broad_guarded_fallback_damage(trade_path)

    assert scan["row_counts"]["guarded_market_fallback_applied_rows"] == 2
    assert scan["bad_counts"]["fallback_winner_to_loser"] == 1
    assert scan["sample_bad"][0]["candidate_id"] == "candidate-damaged"


def test_guarded_fallback_damage_scan_blocks_routed_filled_rows_without_fallback(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    order_path = tmp_path / "orders.jsonl"
    trade_path = tmp_path / "trades.jsonl"
    write_jsonl(
        order_path,
        [
            {
                "candidate_id": "candidate-order-leak",
                "simulated_order_id": "order-leak",
                "risk_finalizer_package_marketable_entry_guard_status": (
                    "routed_to_replay_order_policy"
                ),
                "order_status": "filled",
                "guarded_market_fallback_applied": False,
            },
            {
                "candidate_id": "candidate-order-ok",
                "simulated_order_id": "order-ok",
                "risk_finalizer_package_marketable_entry_guard_status": (
                    "routed_to_replay_order_policy"
                ),
                "order_status": "filled",
                "guarded_market_fallback_applied": True,
                "fallback_fill_price_source": "m1_side_conservative_close",
                "limit_requested_entry_price": 100.0,
                "limit_requested_stop_loss": 99.5,
                "limit_requested_take_profit_1": 101.0,
                "fallback_stop_loss": 99.5,
                "fallback_take_profit_1": 101.0,
                "fallback_entry_adverse_drift_r": 0.04,
                "max_adverse_entry_drift_r": 0.10,
            },
            {
                "candidate_id": "candidate-off-configured-fallback-leak",
                "simulated_order_id": "order-off-configured-fallback-leak",
                "risk_finalizer_package_marketable_entry_guard_status": (
                    "routed_to_replay_order_policy"
                ),
                "order_status": "filled",
                "guarded_market_fallback_applied": True,
                "guarded_market_fallback_off_configured_session": True,
                "route_session": "off_configured_session",
                "off_configured_session_guarded_market_fallback_allowed": False,
                "fallback_fill_price_source": "m1_side_conservative_close",
                "limit_requested_entry_price": 100.0,
                "limit_requested_stop_loss": 99.5,
                "limit_requested_take_profit_1": 101.0,
                "fallback_stop_loss": 99.5,
                "fallback_take_profit_1": 101.0,
                "fallback_entry_adverse_drift_r": 0.04,
                "max_adverse_entry_drift_r": 0.10,
            },
            {
                "candidate_id": "candidate-off-configured-fallback-allowed",
                "simulated_order_id": "order-off-configured-fallback-allowed",
                "risk_finalizer_package_marketable_entry_guard_status": (
                    "routed_to_replay_order_policy"
                ),
                "order_status": "filled",
                "guarded_market_fallback_applied": True,
                "guarded_market_fallback_off_configured_session": True,
                "route_session": "off_configured_session",
                "off_configured_session_guarded_market_fallback_allowed": True,
                "fallback_fill_price_source": "m1_side_conservative_close",
                "limit_requested_entry_price": 100.0,
                "limit_requested_stop_loss": 99.5,
                "limit_requested_take_profit_1": 101.0,
                "fallback_stop_loss": 99.5,
                "fallback_take_profit_1": 101.0,
                "fallback_entry_adverse_drift_r": 0.04,
                "max_adverse_entry_drift_r": 0.10,
            },
            {
                "candidate_id": "candidate-configured-fallback-ok",
                "simulated_order_id": "order-configured-fallback-ok",
                "risk_finalizer_package_marketable_entry_guard_status": (
                    "routed_to_replay_order_policy"
                ),
                "order_status": "filled",
                "guarded_market_fallback_applied": True,
                "guarded_market_fallback_off_configured_session": False,
                "route_session": "london",
                "off_configured_session_guarded_market_fallback_allowed": False,
                "fallback_fill_price_source": "m1_side_conservative_close",
                "limit_requested_entry_price": 100.0,
                "limit_requested_stop_loss": 99.5,
                "limit_requested_take_profit_1": 101.0,
                "fallback_stop_loss": 99.5,
                "fallback_take_profit_1": 101.0,
                "fallback_entry_adverse_drift_r": 0.04,
                "max_adverse_entry_drift_r": 0.10,
            },
            {
                "candidate_id": "candidate-order-disabled-guard-leak",
                "simulated_order_id": "order-disabled-guard-leak",
                "risk_finalizer_package_marketable_entry_guard_status": "disabled",
                "limit_marketable_at_decision": True,
                "package_replay_executable_candidate_use_allowed": True,
                "package_execution_result_scope": "guarded_executable_package_replay",
                "order_status": "filled",
                "guarded_market_fallback_applied": False,
            },
            {
                "candidate_id": "candidate-passive-envelope-block-leak",
                "simulated_order_id": "order-passive-envelope-block-leak",
                "order_status": "expired_unfilled",
                "open_reduced_passive_limit_queue_route_available": True,
                "passive_limit_fallback_envelope_required": True,
                "passive_limit_fallback_envelope_status": "blocked",
                "passive_limit_fallback_envelope_reason": (
                    "passive_limit_fallback_envelope_distance_to_limit_risk_above_thesis_geometry_ceiling"
                ),
                "guarded_market_fallback_applied": False,
            },
            {
                "candidate_id": "candidate-passive-envelope-ok",
                "simulated_order_id": "order-passive-envelope-ok",
                "order_status": "expired_unfilled",
                "open_reduced_passive_limit_queue_route_available": True,
                "passive_limit_fallback_envelope_required": True,
                "passive_limit_fallback_envelope_status": "passed",
                "guarded_market_fallback_applied": False,
            },
            {
                "candidate_id": "candidate-passive-envelope-degraded-ok",
                "simulated_order_id": "order-passive-envelope-degraded-ok",
                "order_status": "expired_unfilled",
                "open_reduced_passive_limit_queue_route_available": True,
                "passive_limit_fallback_envelope_required": True,
                "passive_limit_fallback_envelope_status": (
                    "degraded_to_passive_limit_queue"
                ),
                "passive_limit_fallback_envelope_degraded_to_passive_queue": True,
                "passive_limit_fallback_envelope_passive_queue_release_reason": (
                    "passive_limit_queue_remains_executable_when_guarded_fallback_envelope_is_unusable"
                ),
                "passive_limit_fallback_envelope_reasons": [
                    "passive_limit_fallback_envelope_limit_fill_probability_above_fallback_wait_ceiling"
                ],
                "passive_limit_fallback_envelope_used_only_predecision_fields": True,
                "passive_limit_fallback_envelope_source_boundary": (
                    "predecision_limit_fillability_cost_policy_no_elapsed_path_no_broker_authority"
                ),
                "passive_limit_fallback_envelope_degraded_transfer_score": 0.44,
                "passive_limit_fallback_envelope_min_degraded_transfer_score": 0.40,
                "passive_limit_fallback_envelope_distance_to_limit_risk": 2.0,
                "passive_limit_fallback_envelope_limit_fill_probability": 0.40,
                "passive_limit_fallback_envelope_expected_net_r": 1.25,
                "passive_limit_fallback_envelope_expected_net_r_after_guarded_fallback_cost": 1.20,
                "passive_limit_fallback_envelope_min_expected_net_r_after_guarded_fallback_cost": 0.40,
                "passive_limit_fallback_envelope_source_completeness": 1.0,
                "passive_limit_fallback_envelope_candidate_probability": 0.88,
                "pretrade_cost_packet_status": "PASSED",
                "broker_pretrade_cost_executable": True,
                "guarded_market_fallback_applied": False,
            },
            {
                "candidate_id": "candidate-order-raw-diagnostic",
                "simulated_order_id": "order-raw-diagnostic",
                "risk_finalizer_package_marketable_entry_guard_status": "disabled",
                "limit_marketable_at_decision": True,
                "package_replay_executable_candidate_use_allowed": True,
                "broad_replay_profile": "raw_package_live_as_if",
                "package_execution_result_scope": "raw_baseline_diagnostic_only",
                "order_status": "filled",
                "guarded_market_fallback_applied": False,
            },
        ],
    )
    write_jsonl(
        trade_path,
        [
            {
                "candidate_id": "candidate-trade-leak",
                "simulated_trade_id": "trade-leak",
                "package_marketable_entry_guard_status": (
                    "routed_to_replay_order_policy"
                ),
                "limit_first_fill_status": "filled_from_ordered_m1_path",
                "guarded_market_fallback_applied": False,
            },
            {
                "candidate_id": "candidate-trade-nonrouted",
                "simulated_trade_id": "trade-nonrouted",
                "package_marketable_entry_guard_status": "clear",
                "limit_first_fill_status": "filled_from_ordered_m1_path",
                "guarded_market_fallback_applied": False,
            },
            {
                "candidate_id": "candidate-trade-disabled-guard-leak",
                "simulated_trade_id": "trade-disabled-guard-leak",
                "package_marketable_entry_guard_status": "disabled",
                "limit_marketable_at_decision": True,
                "ultimate_package_effective_admission_count": 1.0,
                "package_execution_result_scope": "repaired_executable_package_replay",
                "limit_first_fill_status": "filled_from_ordered_m1_path",
                "guarded_market_fallback_applied": False,
            },
            {
                "candidate_id": "candidate-trade-raw-diagnostic",
                "simulated_trade_id": "trade-raw-diagnostic",
                "package_marketable_entry_guard_status": "disabled",
                "limit_marketable_at_decision": True,
                "ultimate_package_effective_admission_count": 1.0,
                "broad_replay_profile": "raw_package_live_as_if",
                "package_execution_result_scope": "raw_baseline_diagnostic_only",
                "limit_first_fill_status": "filled_from_ordered_m1_path",
                "guarded_market_fallback_applied": False,
            },
        ],
    )

    scan = verifier.scan_broad_guarded_fallback_damage(
        {"order": order_path, "trade": trade_path}
    )

    bad = scan["bad_counts"]
    assert bad["order:routed_filled_without_guarded_market_fallback"] == 1
    assert bad["trade:routed_filled_without_guarded_market_fallback"] == 1
    assert (
        bad["order:off_configured_guarded_market_fallback_applied_while_disabled"]
        == 1
    )
    assert bad["order:marketable_limit_filled_with_disabled_package_guard"] == 1
    assert bad["trade:marketable_limit_filled_with_disabled_package_guard"] == 1
    assert (
        bad["order:passive_limit_queue_expired_without_passed_fallback_envelope"]
        == 1
    )
    assert (
        bad["order:passive_limit_order_materialized_after_fallback_envelope_block"]
        == 1
    )
    assert scan["row_counts"]["order_routed_to_replay_order_policy_rows"] == 5
    assert scan["row_counts"]["trade_routed_to_replay_order_policy_rows"] == 1
    assert (
        scan["row_counts"][
            "order_passive_limit_fallback_envelope_required_rows"
        ]
        == 3
    )
    assert (
        scan["row_counts"]["order_passive_limit_fallback_envelope_passed_rows"]
        == 1
    )
    assert (
        scan["row_counts"][
            "order_passive_limit_fallback_envelope_degraded_release_valid_rows"
        ]
        == 1
    )
    assert (
        scan["row_counts"][
            "order_raw_diagnostic_disabled_guard_market_limit_filled_rows"
        ]
        == 1
    )
    assert (
        scan["row_counts"][
            "trade_raw_diagnostic_disabled_guard_market_limit_filled_rows"
        ]
        == 1
    )
    # The sample is intentionally bounded; bad_counts above prove the trade-ledger
    # leak classes even when order-ledger samples fill the debug budget first.
    assert {row["candidate_id"] for row in scan["sample_bad"]} >= {
        "candidate-order-leak",
        "candidate-off-configured-fallback-leak",
        "candidate-order-disabled-guard-leak",
        "candidate-passive-envelope-block-leak",
    }


def test_broad_guarded_fallback_damage_scan_blocks_bad_degraded_passive_queue_release(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    order_path = tmp_path / "orders.jsonl"
    base = {
        "order_status": "expired_unfilled",
        "open_reduced_passive_limit_queue_route_available": True,
        "passive_limit_fallback_envelope_required": True,
        "passive_limit_fallback_envelope_status": "degraded_to_passive_limit_queue",
        "passive_limit_fallback_envelope_degraded_to_passive_queue": True,
        "passive_limit_fallback_envelope_passive_queue_release_reason": (
            "passive_limit_queue_remains_executable_when_guarded_fallback_envelope_is_unusable"
        ),
        "passive_limit_fallback_envelope_reasons": [
            "passive_limit_fallback_envelope_limit_fill_probability_above_fallback_wait_ceiling"
        ],
        "passive_limit_fallback_envelope_used_only_predecision_fields": True,
        "passive_limit_fallback_envelope_source_boundary": (
            "predecision_limit_fillability_cost_policy_no_elapsed_path_no_broker_authority"
        ),
        "passive_limit_fallback_envelope_degraded_transfer_score": 0.44,
        "passive_limit_fallback_envelope_min_degraded_transfer_score": 0.40,
        "passive_limit_fallback_envelope_distance_to_limit_risk": 2.0,
        "passive_limit_fallback_envelope_limit_fill_probability": 0.40,
        "passive_limit_fallback_envelope_expected_net_r": 1.25,
        "passive_limit_fallback_envelope_expected_net_r_after_guarded_fallback_cost": 1.20,
        "passive_limit_fallback_envelope_min_expected_net_r_after_guarded_fallback_cost": 0.40,
        "passive_limit_fallback_envelope_source_completeness": 1.0,
        "passive_limit_fallback_envelope_candidate_probability": 0.88,
        "pretrade_cost_packet_status": "PASSED",
        "broker_pretrade_cost_executable": True,
    }
    write_jsonl(
        order_path,
        [
            {
                **base,
                "candidate_id": "candidate-degraded-postdecision",
                "simulated_order_id": "order-degraded-postdecision",
                "passive_limit_fallback_envelope_source_boundary": (
                    "postdecision_elapsed_path"
                ),
            },
            {
                **base,
                "candidate_id": "candidate-degraded-quality-failure",
                "simulated_order_id": "order-degraded-quality-failure",
                "passive_limit_fallback_envelope_reasons": [
                    "passive_limit_fallback_envelope_probability_below_floor"
                ],
            },
            {
                **base,
                "candidate_id": "candidate-degraded-distance-breach",
                "simulated_order_id": "order-degraded-distance-breach",
                "passive_limit_fallback_envelope_reasons": [
                    "passive_limit_fallback_envelope_distance_to_limit_risk_above_thesis_geometry_ceiling"
                ],
            },
            {
                **base,
                "candidate_id": "candidate-degraded-cost-refused",
                "simulated_order_id": "order-degraded-cost-refused",
                "pretrade_cost_packet_status": "REFUSED",
                "broker_cost_packet_refused": True,
            },
            {
                **base,
                "candidate_id": "candidate-degraded-missing-score",
                "simulated_order_id": "order-degraded-missing-score",
                "passive_limit_fallback_envelope_degraded_transfer_score": None,
            },
            {
                **base,
                "candidate_id": "candidate-degraded-route-not-consumed",
                "simulated_order_id": "order-degraded-route-not-consumed",
                "open_reduced_passive_limit_queue_route_available": False,
            },
        ],
    )

    scan = verifier.scan_broad_guarded_fallback_damage({"order": order_path})

    bad = scan["bad_counts"]
    assert bad["order:passive_limit_degraded_release_non_predecision_boundary"] == 1
    assert (
        bad["order:passive_limit_degraded_release_contains_quality_failure_reason"]
        == 2
    )
    assert bad["order:passive_limit_degraded_release_with_broker_cost_refused"] == 1
    assert (
        bad["order:passive_limit_degraded_release_missing_numeric_thresholds"]
        == 1
    )
    assert (
        bad["order:passive_limit_degraded_release_not_consumed_by_order_route"]
        == 1
    )
    assert (
        bad["order:passive_limit_queue_expired_without_valid_fallback_envelope"]
        == 5
    )


def test_broad_guarded_fallback_accepts_declined_fallback_with_live_passive_queue(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    order_path = tmp_path / "orders.jsonl"
    write_jsonl(
        order_path,
        [
            {
                "candidate_id": "candidate-passive-fallback-declined",
                "simulated_order_id": "order-passive-fallback-declined",
                "order_status": "expired_unfilled",
                "open_reduced_passive_limit_queue_route_available": True,
                "passive_limit_fallback_envelope_required": True,
                "passive_limit_fallback_envelope_status": "blocked",
                "passive_limit_fallback_envelope_fallback_unclamped_time_utc": (
                    "2026-05-14T08:45:00+00:00"
                ),
                "passive_limit_fallback_envelope_latest_usable_time_utc": (
                    "2026-05-14T09:14:59+00:00"
                ),
                "passive_limit_fallback_envelope_fallback_window_exhausted_by_expiry": (
                    False
                ),
                "passive_limit_fallback_envelope_expiry_utc": (
                    "2026-05-14T09:15:00+00:00"
                ),
                "open_reduced_soft_authority_passive_limit_contract_status": (
                    "passed"
                ),
                "open_reduced_soft_authority_passive_limit_contract_reason": (
                    "fallback_declined_keep_passive_limit"
                ),
                "open_reduced_soft_authority_passive_limit_contract_source": (
                    "passive_limit_queue_replay_order_policy"
                ),
                "open_reduced_soft_authority_passive_limit_queue_route_available": (
                    True
                ),
            }
        ],
    )

    scan = verifier.scan_broad_guarded_fallback_damage({"order": order_path})

    assert scan["row_counts"][
        "order_fallback_declined_keep_passive_limit_valid_rows"
    ] == 1
    assert not any(
        "passive_limit" in key for key in scan["bad_counts"]
    ), scan["bad_counts"]


def test_guarded_fallback_damage_scan_requires_high_fill_counterfactual(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    order_path = tmp_path / "orders.jsonl"
    write_jsonl(
        order_path,
        [
            {
                "candidate_id": "candidate-high-fill-missing",
                "simulated_order_id": "order-high-fill-missing",
                "order_status": "expired_unfilled",
                "guarded_market_fallback_configured": True,
                "guarded_market_fallback_applied": False,
                "guarded_market_fallback_reasons": [
                    "limit_fill_probability_above_fallback_wait_ceiling"
                ],
                "limit_first_fill_status": "not_filled_in_post_asof_m1_path",
            },
            {
                "candidate_id": "candidate-high-fill-scored",
                "simulated_order_id": "order-high-fill-scored",
                "order_status": "expired_unfilled",
                "guarded_market_fallback_configured": True,
                "guarded_market_fallback_applied": False,
                "guarded_market_fallback_reasons": [
                    "limit_fill_probability_above_fallback_wait_ceiling"
                ],
                "limit_first_fill_status": "not_filled_in_post_asof_m1_path",
                "high_fill_unfilled_probe_counterfactual_status": "scored",
                "high_fill_unfilled_probe_counterfactual_net_r": -0.42,
            },
        ],
    )

    scan = verifier.scan_broad_guarded_fallback_damage({"order": order_path})

    assert (
        scan["row_counts"][
            "order_high_fill_unfilled_probe_counterfactual_required_rows"
        ]
        == 2
    )
    assert (
        scan["row_counts"][
            "order_high_fill_unfilled_probe_counterfactual_scored_rows"
        ]
        == 1
    )
    assert (
        scan["bad_counts"][
            "order:high_fill_unfilled_probe_counterfactual_missing"
        ]
        == 1
    )
    assert scan["sample_bad"][0]["candidate_id"] == "candidate-high-fill-missing"


def test_selected_package_executed_authority_scan_fails_join_conflict() -> None:
    verifier = load_verifier()
    good_authority = {
        "candidate_id": "candidate-good",
        "order_status": "filled",
        "decision_time_utc": "2026-05-13T08:00:00+00:00",
        "candidate_instance_identity_status": "materialized",
        "canonical_replay_candidate_instance_key": (
            "candidate-good@@2026-05-13T08:00:00+00:00"
        ),
        "risk_finalizer_probe_instance_key": (
            "candidate-good@@2026-05-13T08:00:00+00:00"
        ),
        "source_bound_replay_candidate_instance_key": (
            "candidate-good@@2026-05-13T08:00:00+00:00"
        ),
        "candidate_decision_quality_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        "source_boundary": "source_bound_asof_timewarp_decision_input",
        "pretrade_cost_packet_status": "PASSED",
        "pretrade_cost_refusal_reasons": [],
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "source_gap_cost_fallback_blocked": False,
        "candidate_cost_r_fallback_is_authority": False,
        "fill_realism_class": "passive_queue_confirmed",
        "package_replay_executable_candidate_use_allowed": True,
        "package_replay_order_executable_candidate_use_allowed": True,
        "package_replay_order_executable_candidate_use_allowed_reason": (
            "fixture_order_executable_true"
        ),
        "package_replay_order_executable_authority_source": (
            "fixture_package_replay_order_executable_authority"
        ),
        "selected_scheduler_package_replay_executable_candidate_use_allowed": True,
        "selected_package_candidate_status_join_status": "exact_candidate_window_join",
        "selected_package_candidate_status_join_key": (
            "candidate-good@@2026-05-13T08:00:00+00:00"
        ),
        "role_disposition": "source_bound_candidate",
        "matched_sleeve_ids": ["sleeve-fixture"],
        "matched_sleeve_count": 1,
        "admission_sleeve_match_count": 1,
        "selector_action": "trade",
        "scheduler_materialization_action_intent": "new_position",
    }
    signed_open_reduced_new_entry_authority = {
        "package_new_entry_authority_required": True,
        "package_new_entry_authority_valid": True,
        "package_new_entry_authority_status": (
            "valid_signed_predecision_new_entry_authority"
        ),
        "package_new_entry_authority_failures": [],
        "package_new_entry_authority_hash_sha256": "fixture-signed-authority-hash",
        "expected_package_new_entry_authority_hash_sha256": (
            "fixture-signed-authority-hash"
        ),
        "package_new_entry_authority_payload_schema": (
            "ultimate_candidate_package.new_entry_authority.v2"
        ),
        "package_new_entry_authority_scope": (
            "selector_reduced_risk_to_scheduler_new_position"
        ),
        "package_new_entry_authority_target_action_intent": "new_position",
        "package_new_entry_authority_authority_field": (
            "ultimate_candidate_package_open_reduced_risk_authority"
        ),
        "package_new_entry_authority_authority_family": "unit_test_authority",
        "package_new_entry_authority_source_boundary": (
            "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
        ),
        "package_new_entry_authority_uses_outcome_fields": False,
        "package_new_entry_authority_selector_action": "open-reduced-risk",
        "package_new_entry_authority_selector_reason": "unit_test_authority",
        "package_new_entry_authority_candidate_decision_quality": {
            "expected_net_r": 0.75,
            "probability": 0.7,
            "fill_probability": 0.8,
            "source_completeness": 1.0,
            "source_boundary": (
                "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
            ),
            "candidate_decision_quality_source_boundary": (
                "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
            ),
        },
        "package_new_entry_authority_candidate_decision_quality_field_sources": {
            "expected_net_r": "candidate_decision_inputs.expected_net_r",
            "probability": "candidate_decision_inputs.probability",
            "fill_probability": "candidate_decision_inputs.fill_probability",
            "source_completeness": "candidate_decision_inputs.source_completeness",
        },
        "package_new_entry_authority_candidate_decision_quality_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        "package_new_entry_authority_candidate_decision_quality_alias_status": (
            "exact_materialized"
        ),
        "package_new_entry_authority_candidate_decision_quality_alias_mismatches": [],
        "package_new_entry_authority_candidate_decision_quality_provenance_failures": [],
    }
    def signed_identity(candidate_id: str) -> dict:
        instance_key = f"{candidate_id}@@2026-05-13T08:00:00+00:00"
        return {
            "package_new_entry_authority_candidate_id": candidate_id,
            "package_new_entry_authority_decision_time_utc": (
                "2026-05-13T08:00:00+00:00"
            ),
            "package_new_entry_authority_canonical_replay_candidate_instance_key": (
                instance_key
            ),
            "package_new_entry_authority_source_bound_replay_candidate_instance_key": (
                instance_key
            ),
            "package_new_entry_authority_candidate_instance_identity_status": (
                "materialized"
            ),
        }

    scan = verifier.scan_selected_package_executed_order_trade_authority(
        {
            "fixture": (
                [
                    good_authority,
                    {
                        **good_authority,
                        "source_boundary": None,
                        "candidate_id": "candidate-missing-source-boundary",
                        "canonical_replay_candidate_instance_key": (
                            "candidate-missing-source-boundary@@2026-05-13T08:00:00+00:00"
                        ),
                        "risk_finalizer_probe_instance_key": (
                            "candidate-missing-source-boundary@@2026-05-13T08:00:00+00:00"
                        ),
                        "source_bound_replay_candidate_instance_key": (
                            "candidate-missing-source-boundary@@2026-05-13T08:00:00+00:00"
                        ),
                        "selected_package_candidate_status_join_key": (
                            "candidate-missing-source-boundary@@2026-05-13T08:00:00+00:00"
                        ),
                        "simulated_order_id": "order-missing-source-boundary",
                    },
                    {
                        **good_authority,
                        "candidate_id": "candidate-conflict",
                        "canonical_replay_candidate_instance_key": (
                            "candidate-conflict@@2026-05-13T08:00:00+00:00"
                        ),
                        "risk_finalizer_probe_instance_key": (
                            "candidate-conflict@@2026-05-13T08:00:00+00:00"
                        ),
                        "source_bound_replay_candidate_instance_key": (
                            "candidate-conflict@@2026-05-13T08:00:00+00:00"
                        ),
                        "selected_package_candidate_status_join_key": (
                            "candidate-conflict@@2026-05-13T08:00:00+00:00"
                        ),
                        "simulated_order_id": "order-conflict",
                        "selected_package_candidate_status_join_execution_authority_conflict": True,
                    },
                    {
                        **good_authority,
                        "candidate_id": "candidate-duplicate",
                        "canonical_replay_candidate_instance_key": (
                            "candidate-duplicate@@2026-05-13T08:00:00+00:00"
                        ),
                        "risk_finalizer_probe_instance_key": (
                            "candidate-duplicate@@2026-05-13T08:00:00+00:00"
                        ),
                        "source_bound_replay_candidate_instance_key": (
                            "candidate-duplicate@@2026-05-13T08:00:00+00:00"
                        ),
                        "selected_package_candidate_status_join_key": (
                            "candidate-duplicate@@2026-05-13T08:00:00+00:00"
                        ),
                        "simulated_order_id": "order-duplicate",
                        "selected_package_candidate_status_join_status": (
                            "selected_package_candidate_status_join_duplicate_ambiguous"
                        ),
                    },
                    {
                        **good_authority,
                        "candidate_id": "candidate-reduce-risk-new-order",
                        "canonical_replay_candidate_instance_key": (
                            "candidate-reduce-risk-new-order@@2026-05-13T08:00:00+00:00"
                        ),
                        "risk_finalizer_probe_instance_key": (
                            "candidate-reduce-risk-new-order@@2026-05-13T08:00:00+00:00"
                        ),
                        "source_bound_replay_candidate_instance_key": (
                            "candidate-reduce-risk-new-order@@2026-05-13T08:00:00+00:00"
                        ),
                        "selected_package_candidate_status_join_key": (
                            "candidate-reduce-risk-new-order@@2026-05-13T08:00:00+00:00"
                        ),
                        "simulated_order_id": "order-reduce-risk-new-order",
                        "selector_action": "reduce-risk",
                        "scheduler_materialization_action_intent": "new_position",
                    },
                    {
                        "candidate_id": "candidate-hold-emitted-order",
                        "simulated_order_id": "order-hold-emitted",
                        "order_status": "pending",
                        "selector_action": "hold",
                        "scheduler_materialization_action_intent": "new_position",
                    },
                    {
                        **good_authority,
                        **signed_open_reduced_new_entry_authority,
                        **signed_identity("candidate-open-reduced-good"),
                        "candidate_id": "candidate-open-reduced-good",
                        "canonical_replay_candidate_instance_key": (
                            "candidate-open-reduced-good@@2026-05-13T08:00:00+00:00"
                        ),
                        "risk_finalizer_probe_instance_key": (
                            "candidate-open-reduced-good@@2026-05-13T08:00:00+00:00"
                        ),
                        "source_bound_replay_candidate_instance_key": (
                            "candidate-open-reduced-good@@2026-05-13T08:00:00+00:00"
                        ),
                        "selected_package_candidate_status_join_key": (
                            "candidate-open-reduced-good@@2026-05-13T08:00:00+00:00"
                        ),
                        "simulated_order_id": "order-open-reduced-good",
                        "selector_action": "open-reduced-risk",
                        "package_open_reduced_authority_allowed": True,
                        "package_open_reduced_authority_family": "unit_test_authority",
                        "ultimate_candidate_package_open_reduced_risk_authority": {
                            "allowed": True,
                            "authority_family": "unit_test_authority",
                            "source_boundary": (
                                "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
                            ),
                        },
                    },
                    {
                        **good_authority,
                        **signed_open_reduced_new_entry_authority,
                        **signed_identity("candidate-order-exec-false"),
                        "candidate_id": "candidate-order-exec-false",
                        "canonical_replay_candidate_instance_key": (
                            "candidate-order-exec-false@@2026-05-13T08:00:00+00:00"
                        ),
                        "risk_finalizer_probe_instance_key": (
                            "candidate-order-exec-false@@2026-05-13T08:00:00+00:00"
                        ),
                        "source_bound_replay_candidate_instance_key": (
                            "candidate-order-exec-false@@2026-05-13T08:00:00+00:00"
                        ),
                        "selected_package_candidate_status_join_key": (
                            "candidate-order-exec-false@@2026-05-13T08:00:00+00:00"
                        ),
                        "simulated_order_id": "order-order-exec-false",
                        "selector_action": "open-reduced-risk",
                        "package_open_reduced_authority_allowed": True,
                        "package_open_reduced_authority_family": "unit_test_authority",
                        "ultimate_candidate_package_open_reduced_risk_authority": {
                            "allowed": True,
                            "authority_family": "unit_test_authority",
                            "source_boundary": (
                                "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
                            ),
                        },
                        "package_replay_executable_candidate_use_allowed": True,
                        "package_replay_order_executable_candidate_use_allowed": False,
                        "package_replay_order_executable_candidate_use_allowed_reason": (
                            "fixture_order_executable_false"
                        ),
                        "package_replay_order_executable_authority_source": None,
                    },
                    {
                        **good_authority,
                        **signed_open_reduced_new_entry_authority,
                        **signed_identity("candidate-order-exec-false-reason-missing"),
                        "candidate_id": "candidate-order-exec-false-reason-missing",
                        "canonical_replay_candidate_instance_key": (
                            "candidate-order-exec-false-reason-missing@@2026-05-13T08:00:00+00:00"
                        ),
                        "risk_finalizer_probe_instance_key": (
                            "candidate-order-exec-false-reason-missing@@2026-05-13T08:00:00+00:00"
                        ),
                        "source_bound_replay_candidate_instance_key": (
                            "candidate-order-exec-false-reason-missing@@2026-05-13T08:00:00+00:00"
                        ),
                        "selected_package_candidate_status_join_key": (
                            "candidate-order-exec-false-reason-missing@@2026-05-13T08:00:00+00:00"
                        ),
                        "simulated_order_id": "order-order-exec-false-reason-missing",
                        "selector_action": "open-reduced-risk",
                        "package_open_reduced_authority_allowed": True,
                        "package_open_reduced_authority_family": "unit_test_authority",
                        "ultimate_candidate_package_open_reduced_risk_authority": {
                            "allowed": True,
                            "authority_family": "unit_test_authority",
                            "source_boundary": (
                                "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
                            ),
                        },
                        "package_replay_executable_candidate_use_allowed": True,
                        "package_replay_order_executable_candidate_use_allowed": False,
                        "package_replay_order_executable_candidate_use_allowed_reason": None,
                        "package_replay_order_executable_authority_source": None,
                    },
                    {
                        **good_authority,
                        **signed_open_reduced_new_entry_authority,
                        **signed_identity("candidate-order-exec-missing"),
                        "candidate_id": "candidate-order-exec-missing",
                        "canonical_replay_candidate_instance_key": (
                            "candidate-order-exec-missing@@2026-05-13T08:00:00+00:00"
                        ),
                        "risk_finalizer_probe_instance_key": (
                            "candidate-order-exec-missing@@2026-05-13T08:00:00+00:00"
                        ),
                        "source_bound_replay_candidate_instance_key": (
                            "candidate-order-exec-missing@@2026-05-13T08:00:00+00:00"
                        ),
                        "selected_package_candidate_status_join_key": (
                            "candidate-order-exec-missing@@2026-05-13T08:00:00+00:00"
                        ),
                        "simulated_order_id": "order-order-exec-missing",
                        "selector_action": "open-reduced-risk",
                        "package_open_reduced_authority_allowed": True,
                        "package_open_reduced_authority_family": "unit_test_authority",
                        "ultimate_candidate_package_open_reduced_risk_authority": {
                            "allowed": True,
                            "authority_family": "unit_test_authority",
                            "source_boundary": (
                                "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
                            ),
                        },
                        "package_replay_executable_candidate_use_allowed": True,
                        "package_replay_order_executable_candidate_use_allowed": None,
                        "package_replay_order_executable_candidate_use_allowed_reason": None,
                    },
                    {
                        **good_authority,
                        **signed_open_reduced_new_entry_authority,
                        **signed_identity("candidate-open-reduced-good"),
                        "candidate_id": "candidate-open-reduced-stale-signed-identity",
                        "canonical_replay_candidate_instance_key": (
                            "candidate-open-reduced-stale-signed-identity@@2026-05-13T08:00:00+00:00"
                        ),
                        "risk_finalizer_probe_instance_key": (
                            "candidate-open-reduced-stale-signed-identity@@2026-05-13T08:00:00+00:00"
                        ),
                        "source_bound_replay_candidate_instance_key": (
                            "candidate-open-reduced-stale-signed-identity@@2026-05-13T08:00:00+00:00"
                        ),
                        "selected_package_candidate_status_join_key": (
                            "candidate-open-reduced-stale-signed-identity@@2026-05-13T08:00:00+00:00"
                        ),
                        "simulated_order_id": "order-open-reduced-stale-signed-identity",
                        "selector_action": "open-reduced-risk",
                        "package_open_reduced_authority_allowed": True,
                        "package_open_reduced_authority_family": "unit_test_authority",
                        "ultimate_candidate_package_open_reduced_risk_authority": {
                            "allowed": True,
                            "authority_family": "unit_test_authority",
                            "source_boundary": (
                                "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
                            ),
                        },
                    },
                    {
                        **good_authority,
                        "candidate_id": "candidate-open-reduced-router-disabled",
                        "canonical_replay_candidate_instance_key": (
                            "candidate-open-reduced-router-disabled@@2026-05-13T08:00:00+00:00"
                        ),
                        "risk_finalizer_probe_instance_key": (
                            "candidate-open-reduced-router-disabled@@2026-05-13T08:00:00+00:00"
                        ),
                        "source_bound_replay_candidate_instance_key": (
                            "candidate-open-reduced-router-disabled@@2026-05-13T08:00:00+00:00"
                        ),
                        "selected_package_candidate_status_join_key": (
                            "candidate-open-reduced-router-disabled@@2026-05-13T08:00:00+00:00"
                        ),
                        "simulated_order_id": "order-open-reduced-router-disabled",
                        "selector_action": "open-reduced-risk",
                        "package_open_reduced_authority_allowed": True,
                        "package_open_reduced_authority_family": "router_refusal_softening",
                        "package_open_reduced_authority_current_config_allowed": False,
                        "package_open_reduced_authority_config_block_reason": (
                            "router_refusal_open_reduced_risk_disabled_by_config"
                        ),
                        "ultimate_candidate_package_open_reduced_risk_authority": {
                            "allowed": True,
                            "authority_family": "router_refusal_softening",
                            "current_config_allowed": False,
                            "config_block_reason": (
                                "router_refusal_open_reduced_risk_disabled_by_config"
                            ),
                            "source_boundary": (
                                "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
                            ),
                        },
                    },
                    {
                        **good_authority,
                        "candidate_id": "candidate-open-reduced-invalid-boundary",
                        "canonical_replay_candidate_instance_key": (
                            "candidate-open-reduced-invalid-boundary@@2026-05-13T08:00:00+00:00"
                        ),
                        "risk_finalizer_probe_instance_key": (
                            "candidate-open-reduced-invalid-boundary@@2026-05-13T08:00:00+00:00"
                        ),
                        "source_bound_replay_candidate_instance_key": (
                            "candidate-open-reduced-invalid-boundary@@2026-05-13T08:00:00+00:00"
                        ),
                        "selected_package_candidate_status_join_key": (
                            "candidate-open-reduced-invalid-boundary@@2026-05-13T08:00:00+00:00"
                        ),
                        "simulated_order_id": "order-open-reduced-invalid-boundary",
                        "selector_action": "open-reduced-risk",
                        "package_open_reduced_authority_allowed": True,
                        "package_open_reduced_authority_family": "unit_test_authority",
                        "ultimate_candidate_package_open_reduced_risk_authority": {
                            "allowed": True,
                            "authority_family": "unit_test_authority",
                        },
                    },
                    {
                        **good_authority,
                        "candidate_id": "candidate-missing-join-key",
                        "canonical_replay_candidate_instance_key": (
                            "candidate-missing-join-key@@2026-05-13T08:00:00+00:00"
                        ),
                        "risk_finalizer_probe_instance_key": (
                            "candidate-missing-join-key@@2026-05-13T08:00:00+00:00"
                        ),
                        "source_bound_replay_candidate_instance_key": (
                            "candidate-missing-join-key@@2026-05-13T08:00:00+00:00"
                        ),
                        "selected_package_candidate_status_join_key": None,
                        "simulated_order_id": "order-missing-join-key",
                    },
                    {
                        **good_authority,
                        "candidate_id": "candidate-mismatched-join-key",
                        "canonical_replay_candidate_instance_key": (
                            "candidate-mismatched-join-key@@2026-05-13T08:00:00+00:00"
                        ),
                        "risk_finalizer_probe_instance_key": (
                            "candidate-mismatched-join-key@@2026-05-13T08:00:00+00:00"
                        ),
                        "source_bound_replay_candidate_instance_key": (
                            "candidate-mismatched-join-key@@2026-05-13T08:00:00+00:00"
                        ),
                        "selected_package_candidate_status_join_key": (
                            "candidate-other@@2026-05-13T08:00:00+00:00"
                        ),
                        "simulated_order_id": "order-mismatched-join-key",
                    },
                ],
                [
                    {
                        **good_authority,
                        "candidate_id": "candidate-open-reduced-missing-authority",
                        "canonical_replay_candidate_instance_key": (
                            "candidate-open-reduced-missing-authority@@2026-05-13T08:00:00+00:00"
                        ),
                        "risk_finalizer_probe_instance_key": (
                            "candidate-open-reduced-missing-authority@@2026-05-13T08:00:00+00:00"
                        ),
                        "source_bound_replay_candidate_instance_key": (
                            "candidate-open-reduced-missing-authority@@2026-05-13T08:00:00+00:00"
                        ),
                        "selected_package_candidate_status_join_key": (
                            "candidate-open-reduced-missing-authority@@2026-05-13T08:00:00+00:00"
                        ),
                        "simulated_trade_id": "trade-open-reduced-missing-authority",
                        "selector_action": "open-reduced-risk",
                    },
                    {
                        **good_authority,
                        "candidate_id": "candidate-selected-policy-missing-nested",
                        "canonical_replay_candidate_instance_key": (
                            "candidate-selected-policy-missing-nested@@2026-05-13T08:00:00+00:00"
                        ),
                        "risk_finalizer_probe_instance_key": (
                            "candidate-selected-policy-missing-nested@@2026-05-13T08:00:00+00:00"
                        ),
                        "source_bound_replay_candidate_instance_key": (
                            "candidate-selected-policy-missing-nested@@2026-05-13T08:00:00+00:00"
                        ),
                        "selected_package_candidate_status_join_key": (
                            "candidate-selected-policy-missing-nested@@2026-05-13T08:00:00+00:00"
                        ),
                        "simulated_trade_id": "trade-selected-policy-missing-nested",
                        "selected_policy_for_expected_net_r": "momentum_exhaustion",
                        "selected_policy_expected_net_r": 0.75,
                        "selected_policy_probability": 0.7,
                    },
                    {
                        **good_authority,
                        **signed_open_reduced_new_entry_authority,
                        **signed_identity("candidate-trade-order-exec-false"),
                        "candidate_id": "candidate-trade-order-exec-false",
                        "canonical_replay_candidate_instance_key": (
                            "candidate-trade-order-exec-false@@2026-05-13T08:00:00+00:00"
                        ),
                        "risk_finalizer_probe_instance_key": (
                            "candidate-trade-order-exec-false@@2026-05-13T08:00:00+00:00"
                        ),
                        "source_bound_replay_candidate_instance_key": (
                            "candidate-trade-order-exec-false@@2026-05-13T08:00:00+00:00"
                        ),
                        "selected_package_candidate_status_join_key": (
                            "candidate-trade-order-exec-false@@2026-05-13T08:00:00+00:00"
                        ),
                        "simulated_trade_id": "trade-order-exec-false",
                        "selector_action": "open-reduced-risk",
                        "package_open_reduced_authority_allowed": True,
                        "package_open_reduced_authority_family": "unit_test_authority",
                        "ultimate_candidate_package_open_reduced_risk_authority": {
                            "allowed": True,
                            "authority_family": "unit_test_authority",
                            "source_boundary": (
                                "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
                            ),
                        },
                        "package_replay_executable_candidate_use_allowed": True,
                        "package_replay_order_executable_candidate_use_allowed": False,
                        "package_replay_order_executable_candidate_use_allowed_reason": (
                            "fixture_order_executable_false"
                        ),
                        "package_replay_order_executable_authority_source": None,
                    },
                    {
                        **good_authority,
                        **signed_open_reduced_new_entry_authority,
                        **signed_identity("candidate-trade-order-exec-false-reason-missing"),
                        "candidate_id": "candidate-trade-order-exec-false-reason-missing",
                        "canonical_replay_candidate_instance_key": (
                            "candidate-trade-order-exec-false-reason-missing@@2026-05-13T08:00:00+00:00"
                        ),
                        "risk_finalizer_probe_instance_key": (
                            "candidate-trade-order-exec-false-reason-missing@@2026-05-13T08:00:00+00:00"
                        ),
                        "source_bound_replay_candidate_instance_key": (
                            "candidate-trade-order-exec-false-reason-missing@@2026-05-13T08:00:00+00:00"
                        ),
                        "selected_package_candidate_status_join_key": (
                            "candidate-trade-order-exec-false-reason-missing@@2026-05-13T08:00:00+00:00"
                        ),
                        "simulated_trade_id": "trade-order-exec-false-reason-missing",
                        "selector_action": "open-reduced-risk",
                        "package_open_reduced_authority_allowed": True,
                        "package_open_reduced_authority_family": "unit_test_authority",
                        "ultimate_candidate_package_open_reduced_risk_authority": {
                            "allowed": True,
                            "authority_family": "unit_test_authority",
                            "source_boundary": (
                                "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
                            ),
                        },
                        "package_replay_executable_candidate_use_allowed": True,
                        "package_replay_order_executable_candidate_use_allowed": False,
                        "package_replay_order_executable_candidate_use_allowed_reason": None,
                        "package_replay_order_executable_authority_source": None,
                    },
                    {
                        **good_authority,
                        **signed_open_reduced_new_entry_authority,
                        **signed_identity("candidate-trade-order-exec-missing"),
                        "candidate_id": "candidate-trade-order-exec-missing",
                        "canonical_replay_candidate_instance_key": (
                            "candidate-trade-order-exec-missing@@2026-05-13T08:00:00+00:00"
                        ),
                        "risk_finalizer_probe_instance_key": (
                            "candidate-trade-order-exec-missing@@2026-05-13T08:00:00+00:00"
                        ),
                        "source_bound_replay_candidate_instance_key": (
                            "candidate-trade-order-exec-missing@@2026-05-13T08:00:00+00:00"
                        ),
                        "selected_package_candidate_status_join_key": (
                            "candidate-trade-order-exec-missing@@2026-05-13T08:00:00+00:00"
                        ),
                        "simulated_trade_id": "trade-order-exec-missing",
                        "selector_action": "open-reduced-risk",
                        "package_open_reduced_authority_allowed": True,
                        "package_open_reduced_authority_family": "unit_test_authority",
                        "ultimate_candidate_package_open_reduced_risk_authority": {
                            "allowed": True,
                            "authority_family": "unit_test_authority",
                            "source_boundary": (
                                "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
                            ),
                        },
                        "package_replay_executable_candidate_use_allowed": True,
                        "package_replay_order_executable_candidate_use_allowed": None,
                        "package_replay_order_executable_candidate_use_allowed_reason": None,
                    },
                ],
            )
        }
    )

    assert scan["row_counts"]["fixture.order_filled_rows"] == 14
    assert scan["row_counts"]["fixture.trade_filled_rows"] == 5
    assert scan["bad_counts"]["fixture.order:emitted_order_authority_leak"] == 9
    assert scan["bad_counts"]["fixture.order:executed_authority_leak"] == 13
    assert scan["bad_counts"]["fixture.trade:executed_authority_leak"] == 5
    assert scan["bad_counts"]["fixture.trade:candidate_decision_quality"] == 1
    assert scan["bad_counts"]["fixture.order:source_boundary_missing"] == 1
    assert (
        scan["bad_counts"][
            "fixture.order:selected_package_candidate_status_join_execution_authority_conflict"
        ]
        == 1
    )
    assert (
        scan["bad_counts"][
            "fixture.order:selected_package_candidate_status_join_status:"
            "selected_package_candidate_status_join_duplicate_ambiguous"
        ]
        == 1
    )
    assert (
        scan["bad_counts"]["fixture.order:selector_reduce_risk_not_new_order_authority"]
        == 2
    )
    assert (
        scan["bad_counts"]["fixture.order:selector_open_reduced_risk_authority_missing"]
        == 4
    )
    assert (
        scan["bad_counts"][
            "fixture.order:router_refusal_open_reduced_risk_disabled_by_config"
        ]
        == 1
    )
    assert (
        scan["bad_counts"][
            "fixture.order:open_reduced_authority_source_boundary_missing"
        ]
        == 1
    )
    assert (
        scan["bad_counts"][
            "fixture.order:selected_package_candidate_status_join_key_missing"
        ]
        == 1
    )
    assert (
        scan["bad_counts"][
            "fixture.order:selected_package_candidate_status_join_key_mismatch"
        ]
        == 1
    )
    assert (
        scan["bad_counts"][
            "fixture.order:package_replay_order_executable_candidate_use_allowed_false"
        ]
        == 2
    )
    assert (
        scan["bad_counts"][
            "fixture.order:"
            "package_replay_order_executable_candidate_use_allowed_false_reason_missing"
        ]
        == 1
    )
    assert (
        scan["bad_counts"][
            "fixture.order:package_replay_order_executable_authority_source_missing"
        ]
        == 2
    )
    assert (
        scan["bad_counts"][
            "fixture.trade:package_replay_order_executable_candidate_use_allowed_false"
        ]
        == 2
    )
    assert (
        scan["bad_counts"][
            "fixture.trade:"
            "package_replay_order_executable_candidate_use_allowed_false_reason_missing"
        ]
        == 1
    )
    assert (
        scan["bad_counts"][
            "fixture.trade:package_replay_order_executable_authority_source_missing"
        ]
        == 2
    )
    assert (
        scan["bad_counts"][
            "fixture.order:package_replay_order_executable_candidate_use_allowed_missing"
        ]
        == 1
    )
    assert (
        scan["bad_counts"][
            "fixture.order:"
            "selected_scheduler_package_replay_order_executable_candidate_use_allowed_missing"
        ]
        == 1
    )
    assert (
        scan["bad_counts"][
            "fixture.trade:package_replay_order_executable_candidate_use_allowed_missing"
        ]
        == 1
    )
    assert (
        scan["bad_counts"][
            "fixture.trade:"
            "selected_scheduler_package_replay_order_executable_candidate_use_allowed_missing"
        ]
        == 1
    )
    assert (
        scan["bad_counts"][
            "fixture.order:package_new_entry_authority_envelope_missing"
        ]
        == 2
    )
    assert (
        scan["bad_counts"][
            "fixture.order:"
            "ultimate_candidate_package_open_reduced_risk_authority:"
            "package_new_entry_authority_required_missing_or_false"
        ]
        == 10
    )
    assert (
        scan["bad_counts"][
            "fixture.order:"
            "ultimate_candidate_package_open_reduced_risk_authority:"
            "package_new_entry_authority_payload_missing"
        ]
        == 10
    )
    assert (
        scan["bad_counts"]["fixture.order:selector_action_not_new_order_authority:hold"]
        == 1
    )
    assert (
        scan["bad_counts"][
            "fixture.trade:selector_open_reduced_risk_authority_missing"
        ]
        == 1
    )
    sample_ids = {row["candidate_id"] for row in scan["sample_bad"]}
    assert "candidate-missing-source-boundary" in sample_ids
    assert "candidate-conflict" in sample_ids


def test_broad_order_executable_transfer_contract_requires_bound_or_final_blocker(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    path = tmp_path / "transfer.jsonl"
    rows = [
        {
            "candidate_id": "bound-order",
            "package_replay_order_executable_candidate_use_allowed": True,
            "package_replay_order_executable_transfer_status": "order_bound",
            "package_replay_order_executable_bound_order_id": "order-1",
            "simulated_order_id": "order-1",
            "order_status": "pending_accepted",
        },
        {
            "candidate_id": "blocked-market",
            "package_replay_order_executable_candidate_use_allowed": True,
            "package_replay_order_executable_transfer_status": "final_blocked",
            "package_replay_order_executable_final_blocker_class": (
                "marketable_guard"
            ),
            "package_replay_order_executable_final_blocker_reason": (
                "package_marketable_limit_entry_guard_blocked"
            ),
        },
        {
            "candidate_id": "terminal-deferred-ok",
            "package_replay_order_executable_candidate_use_allowed": True,
            "package_replay_order_executable_transfer_status": (
                "terminal_lifecycle_deferred_source_gap"
            ),
            "package_replay_order_executable_final_blocker_class": (
                "lifecycle_authority"
            ),
            "package_replay_order_executable_final_blocker_reason": (
                "source_gap_terminal_lifecycle_close_r_missing"
            ),
            "package_replay_order_executable_bound_order_id": "order-deferred",
            "package_replay_order_executable_bound_trade_id": None,
            "package_replay_terminal_binding_status": (
                "terminal_lifecycle_deferred_source_gap"
            ),
            "package_replay_terminal_bound_trade_id": None,
            "package_replay_terminal_deferred_trade_id": "trade-deferred",
            "simulated_order_id": "order-deferred",
            "simulated_trade_id": "trade-deferred",
            "order_status": "terminal_lifecycle_position_state_mutation_deferred",
            "fill_status": "not_filled_terminal_lifecycle_close_r_missing_deferred",
        },
        {
            "candidate_id": "terminal-deferred-legacy-bound-bad",
            "package_replay_order_executable_candidate_use_allowed": True,
            "package_replay_order_executable_transfer_status": "order_bound",
            "package_replay_order_executable_bound_order_id": "order-legacy",
            "package_replay_order_executable_bound_trade_id": "trade-legacy",
            "simulated_order_id": "order-legacy",
            "simulated_trade_id": "trade-legacy",
            "order_status": "terminal_lifecycle_position_state_mutation_deferred",
            "fill_status": "not_filled_terminal_lifecycle_close_r_missing_deferred",
            "terminal_lifecycle_mutation_deferred": True,
        },
        {
            "candidate_id": "bad-unbound",
            "package_replay_order_executable_candidate_use_allowed": True,
            "package_replay_order_executable_transfer_status": (
                "unbound_without_final_blocker"
            ),
        },
        {
            "candidate_id": "bad-order-missing-status",
            "scorecard_reported_package_replay_order_executable_candidate_use_allowed": True,
            "scorecard_reported_package_replay_order_executable_candidate_use_allowed_reason": (
                "broker_cost_selector_scheduler_order_executable"
            ),
            "scorecard_reported_package_replay_order_executable_authority_source": (
                "scorecard_reported_package_new_entry_authority"
            ),
        },
        {
            "candidate_id": "bad-blocker",
            "package_replay_order_executable_candidate_use_allowed": True,
            "package_replay_order_executable_transfer_status": "final_blocked",
            "package_replay_order_executable_final_blocker_class": "unknown",
            "package_replay_order_executable_final_blocker_reason": (
                "unknown_blocker"
            ),
        },
        {
            "candidate_id": "bad-generic-missed-authority-reason",
            "package_replay_order_executable_candidate_use_allowed": False,
            "missed_package_replay_order_executable_candidate_use_allowed": None,
            "missed_package_replay_order_executable_candidate_use_allowed_reason": (
                "package_replay_order_executable_authority_missing"
            ),
            "package_replay_order_executable_transfer_status": "not_order_executable",
            "package_replay_order_executable_final_blocker_class": (
                "selector_materialization"
            ),
            "package_replay_order_executable_final_blocker_reason": (
                "package_replay_order_executable_authority_missing"
            ),
        },
        {
            "candidate_id": "good-concrete-missed-authority-reason",
            "package_replay_order_executable_candidate_use_allowed": False,
            "missed_package_replay_order_executable_candidate_use_allowed": False,
            "missed_package_replay_order_executable_candidate_use_allowed_reason": (
                "selector_reduce_risk_not_new_entry_authority"
            ),
            "package_replay_order_executable_transfer_status": "not_order_executable",
            "package_replay_order_executable_final_blocker_class": (
                "selector_materialization"
            ),
            "package_replay_order_executable_final_blocker_reason": (
                "selector_reduce_risk_not_new_entry_authority"
            ),
        },
        {
            "candidate_id": "good-legacy-fill-realism-class-only",
            "package_replay_order_executable_candidate_use_allowed": False,
            "missed_package_replay_order_executable_candidate_use_allowed": None,
            "missed_package_replay_order_executable_candidate_use_allowed_reason": (
                "package_replay_order_executable_authority_missing"
            ),
            "package_replay_order_executable_transfer_status": "not_order_executable",
            "missed_package_replay_order_executable_final_blocker_class": (
                "fill_realism"
            ),
            "package_replay_order_executable_final_blocker_class": "fill_realism",
            "package_replay_order_executable_final_blocker_reason": (
                "package_replay_order_executable_authority_missing"
            ),
        },
    ]
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))

    scan = verifier.scan_broad_order_executable_transfer_contract({"missed": path})

    assert scan["row_counts"]["missed_order_executable_true_rows"] == 3
    assert scan["row_counts"]["missed_order_executable_false_rows"] == 7
    assert scan["transfer_status_counts"]["missed:order_bound"] == 2
    assert scan["transfer_status_counts"]["missed:final_blocked"] == 2
    assert (
        scan["transfer_status_counts"][
            "missed:terminal_lifecycle_deferred_source_gap"
        ]
        == 1
    )
    assert scan["transfer_status_counts"]["missed:missing"] == 1
    assert scan["blocker_counts"]["missed:marketable_guard"] == 1
    assert scan["blocker_counts"]["missed:lifecycle_authority"] == 1
    assert (
        scan["bad_counts"]["missed:order_executable_transfer_contract_bad"] == 6
    )
    assert (
        scan["bad_counts"][
            "missed:order_executable_true_without_bound_or_final_blocker"
        ]
        == 2
    )
    assert (
        scan["bad_counts"]["missed:terminal_deferred_marked_executable_bound"]
        == 1
    )
    assert scan["bad_counts"]["missed:terminal_deferred_has_bound_trade_id"] == 1
    assert scan["bad_counts"]["missed:blocked_status_executable_claim"] == 5
    assert (
        scan["bad_counts"][
            "missed:effective_demotion_executable_alias_still_true:"
            "package_replay_order_executable_candidate_use_allowed"
        ]
        == 4
    )
    assert (
        scan["bad_counts"][
            "missed:blocked_status_executable_claim:"
            "package_replay_order_executable_transfer_status:final_blocked"
        ]
        == 2
    )
    assert (
        scan["bad_counts"][
            "missed:blocked_status_executable_claim:"
            "order_status:terminal_lifecycle_position_state_mutation_deferred"
        ]
        == 2
    )
    assert (
        scan["bad_counts"][
            "missed:blocked_status_executable_claim:"
            "fill_status:not_filled_terminal_lifecycle_close_r_missing_deferred"
        ]
        == 2
    )
    assert (
        scan["bad_counts"][
            "missed:generic_order_executable_missing_reason_with_explicit_authority"
        ]
        == 1
    )
    assert (
        scan["row_counts"][
            "missed_generic_order_executable_reason_with_legacy_concrete_class"
        ]
        == 1
    )


def test_broad_order_executable_transfer_scan_flags_unresolved_package_fill_floor_execution(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    order_path = tmp_path / "ORDER_LEDGER.jsonl"
    trade_path = tmp_path / "TRADE_LEDGER.jsonl"
    missed_path = tmp_path / "MISSED_OPPORTUNITY_LEDGER.jsonl"
    unresolved = ["fill_probability_below_execution_authority_floor"]
    order_leak = {
        "candidate_id": "unresolved-fill-floor-order-bound",
        "package_replay_order_executable_candidate_use_allowed": True,
        "package_replay_order_executable_transfer_status": "order_bound",
        "package_replay_order_executable_bound_order_id": "order-unresolved",
        "simulated_order_id": "order-unresolved",
        "order_status": "pending_accepted",
        "scheduler_option_package_fill_floor_authority_unresolved_failures": unresolved,
    }
    trade_leak = {
        "candidate_id": "unresolved-fill-floor-trade-bound",
        "package_replay_order_executable_candidate_use_allowed": True,
        "package_replay_order_executable_transfer_status": "trade_bound",
        "package_replay_order_executable_bound_trade_id": "trade-unresolved",
        "simulated_trade_id": "trade-unresolved",
        "risk_finalizer_scheduler_option_package_fill_floor_authority_unresolved_failures": unresolved,
    }
    missed_diagnostic = {
        "candidate_id": "unresolved-fill-floor-missed-diagnostic",
        "package_replay_order_executable_candidate_use_allowed": False,
        "package_replay_order_executable_transfer_status": "not_order_executable",
        "approved_risk_pct": 0.0,
        "order_status": "not_sent_missed_opportunity",
        "scheduler_option_package_fill_floor_authority_unresolved_failures": unresolved,
    }
    write_jsonl(order_path, [order_leak])
    write_jsonl(trade_path, [trade_leak])
    write_jsonl(missed_path, [missed_diagnostic])

    scan = verifier.scan_broad_order_executable_transfer_contract(
        {"order": order_path, "trade": trade_path, "missed": missed_path}
    )

    assert scan["bad_counts"]["order:order_executable_transfer_contract_bad"] == 1
    assert (
        scan["bad_counts"][
            "order:package_fill_floor_unresolved_executable_authority"
        ]
        == 1
    )
    assert scan["bad_counts"]["trade:order_executable_transfer_contract_bad"] == 1
    assert (
        scan["bad_counts"][
            "trade:package_fill_floor_unresolved_executable_authority"
        ]
        == 1
    )
    assert scan["row_counts"]["missed_order_executable_false_rows"] == 1
    assert not any(key.startswith("missed:") for key in scan["bad_counts"])


@pytest.mark.parametrize(
    "executable_alias",
    EXPECTED_EFFECTIVE_ORDER_EXECUTABLE_DEMOTION_FIELDS,
)
def test_order_transfer_effective_demotion_scans_every_executable_alias(
    tmp_path: Path,
    executable_alias: str,
) -> None:
    verifier = load_verifier()
    assert tuple(verifier.EFFECTIVE_ORDER_EXECUTABLE_DEMOTION_FIELDS) == (
        EXPECTED_EFFECTIVE_ORDER_EXECUTABLE_DEMOTION_FIELDS
    )
    path = tmp_path / f"demotion-{executable_alias}.jsonl"
    row = {
        "candidate_id": f"demotion-{executable_alias}",
        "package_replay_order_executable_candidate_use_allowed": False,
        "package_replay_order_executable_transfer_status": "final_blocked",
        "package_replay_order_executable_final_blocker_class": "package_authority",
        "package_replay_order_executable_final_blocker_reason": (
            "final_current_package_authority_demotion"
        ),
        executable_alias: True,
    }
    write_jsonl(path, [row])

    scan = verifier.scan_broad_order_executable_transfer_contract({"missed": path})

    assert scan["bad_counts"][
        "missed:effective_demotion_executable_alias_still_true:"
        f"{executable_alias}"
    ] == 1


def test_order_transfer_scan_proves_demoted_signed_proposal_blockers(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    path = tmp_path / "DEMOTED_SIGNED_PROPOSALS.jsonl"
    failure = "fill_probability_below_execution_authority_floor"
    candidate_id = "signed-proposal-finally-blocked"
    decision_time = "2026-05-13T08:30:00+00:00"
    signed_proposal = {
        "candidate_id": candidate_id,
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "source_bound_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "selector_action": "reduce-risk",
        "scheduler_materialization_action_intent": "new_position",
        **signed_package_new_entry_fields(
            candidate_id=candidate_id,
            decision_time_utc=decision_time,
            selector_action="reduce-risk",
        ),
        "package_replay_order_executable_candidate_use_allowed": False,
        "package_replay_order_executable_candidate_use_allowed_pre_finalization": True,
        "package_replay_order_executable_transfer_status": "not_order_executable",
        "package_replay_order_executable_final_blocker_class": "package_authority",
        "package_replay_order_executable_final_blocker_reason": (
            f"package_fill_floor_unresolved_executable_authority:{failure}"
        ),
        "scheduler_option_package_fill_floor_authority_unresolved_failures": [
            failure
        ],
    }
    missing_blocker = {
        "candidate_id": "prefinal-proposal-missing-blocker",
        "package_replay_order_executable_candidate_use_allowed": False,
        "package_replay_order_executable_candidate_use_allowed_pre_finalization": True,
        "package_replay_order_executable_transfer_status": "final_blocked",
    }
    mismatched_fill_floor = {
        "candidate_id": "prefinal-proposal-wrong-fill-floor-blocker",
        "package_replay_order_executable_candidate_use_allowed": False,
        "package_replay_order_executable_candidate_use_allowed_pre_finalization": True,
        "package_replay_order_executable_transfer_status": "not_order_executable",
        "package_replay_order_executable_final_blocker_class": "fill_realism",
        "package_replay_order_executable_final_blocker_reason": "queue_depth_missing",
        "scheduler_option_package_fill_floor_authority_unresolved_failures": [
            failure
        ],
    }
    bound_with_unresolved = {
        "candidate_id": "prefinal-proposal-bound-with-unresolved-fill-floor",
        "package_replay_order_executable_candidate_use_allowed": False,
        "package_replay_order_executable_candidate_use_allowed_pre_finalization": True,
        "package_replay_order_executable_transfer_status": "order_bound",
        "package_replay_order_executable_bound_order_id": "order-unresolved",
        "scheduler_option_package_fill_floor_authority_unresolved_failures": [
            failure
        ],
    }
    write_jsonl(
        path,
        [
            signed_proposal,
            missing_blocker,
            mismatched_fill_floor,
            bound_with_unresolved,
        ],
    )

    scan = verifier.scan_broad_order_executable_transfer_contract({"missed": path})

    assert scan["row_counts"]["missed_order_executable_false_rows"] == 4
    assert scan["row_counts"]["missed_preserved_order_executable_proposal_rows"] == 4
    assert scan["bad_counts"]["missed:order_executable_transfer_contract_bad"] == 3
    assert scan["bad_counts"]["missed:final_blocker_class_missing_or_unapproved"] == 1
    assert scan["bad_counts"]["missed:final_blocker_reason_missing"] == 1
    assert scan["bad_counts"][
        "missed:package_fill_floor_unresolved_blocker_class_mismatch"
    ] == 1
    assert scan["bad_counts"][
        "missed:package_fill_floor_unresolved_blocker_reason_mismatch"
    ] == 1
    assert scan["bad_counts"][
        "missed:package_fill_floor_unresolved_executable_authority"
    ] == 1
    assert scan["bad_counts"][
        "missed:preserved_proposal:preserved_proposal_exact_final_status_missing"
    ] == 1
    assert scan["bad_counts"][
        "missed:preserved_proposal:preserved_proposal_has_bound_order_or_trade_id"
    ] == 1
    assert candidate_id not in {
        sample.get("candidate_id") for sample in scan["sample_bad"]
    }


def test_signed_payload_projection_is_immutable_not_current_without_explicit_marker() -> None:
    verifier = load_verifier()
    candidate_id = "signed-payload-without-explicit-proposal"
    decision_time = "2026-05-13T08:30:00+00:00"
    row = {
        "candidate_id": candidate_id,
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "source_bound_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "selector_action": "reduce-risk",
        "scheduler_materialization_action_intent": "new_position",
        **signed_package_new_entry_fields(
            candidate_id=candidate_id,
            decision_time_utc=decision_time,
            selector_action="reduce-risk",
        ),
        "package_replay_order_executable_candidate_use_allowed": False,
        "package_replay_order_executable_transfer_status": "not_order_executable",
        "package_replay_order_executable_final_blocker_class": "package_authority",
        "package_replay_order_executable_final_blocker_reason": "final_demotion",
        "scheduler_candidate_decision_inputs": {
            "package_replay_order_executable_candidate_use_allowed": False,
            "package_new_entry_authority_package_replay_order_executable_candidate_use_allowed": True,
        },
    }

    assert verifier.row_preserved_order_executable_proposal_allowed(row) is False
    assert verifier.effective_order_executable_demotion_reasons(row) == []
    assert verifier.blocked_status_executable_claim_reasons(row) == []


@pytest.mark.parametrize(
    ("case", "expected_reason"),
    (
        ("valid", None),
        ("missing_payload", "close_and_reverse_release_binding_payload_missing"),
        ("bad_hash", "close_and_reverse_release_binding_hash_invalid"),
        ("identity", "close_and_reverse_release_binding_identity_mismatch"),
        ("action", "close_and_reverse_release_binding_action_mismatch"),
        ("risk", "close_and_reverse_release_binding_risk_invalid"),
        (
            "opposite_open_ids",
            "close_and_reverse_release_binding_opposite_open_ids_invalid",
        ),
    ),
)
def test_final_executable_close_and_reverse_requires_release_binding(
    case: str,
    expected_reason: str | None,
) -> None:
    verifier = load_verifier()
    candidate_id = "close-reverse-release-binding"
    decision_time = "2026-05-13T08:30:00+00:00"
    instance_key = f"{candidate_id}@@{decision_time}"
    payload = {
        "schema_version": "package_close_reverse_release_binding_v1",
        "candidate_id": candidate_id,
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": instance_key,
        "source_bound_replay_candidate_instance_key": instance_key,
        "candidate_instance_identity_status": "materialized",
        "effective_action_intent": "close_and_reverse",
        "opposite_open_position_ids": ["position:opposite-open"],
        "same_symbol_close_reverse_release_risk_pct": 0.5,
    }
    authority = {
        "applies": True,
        "allowed": True,
        "failures": [],
        "effective_action_intent": "close_and_reverse",
        "opposite_open_position_count": 1,
        "opposite_open_position_ids": ["position:opposite-open"],
        "same_symbol_close_reverse_release_risk_pct": 0.5,
        "release_binding_payload": payload,
        "release_binding_hash_sha256": (
            package_new_entry_authority_payload_hash_sha256(payload)
        ),
    }
    row = {
        "candidate_id": candidate_id,
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": instance_key,
        "source_bound_replay_candidate_instance_key": instance_key,
        "candidate_instance_identity_status": "materialized",
        "scheduler_materialization_action_intent": "close_and_reverse",
        "package_opposite_side_close_reverse_authority": authority,
    }
    if case == "missing_payload":
        authority.pop("release_binding_payload")
    elif case == "bad_hash":
        authority["release_binding_hash_sha256"] = "0" * 64
    elif case == "identity":
        payload["candidate_id"] = "other-candidate"
    elif case == "action":
        payload["effective_action_intent"] = "replace_pending"
    elif case == "risk":
        payload["same_symbol_close_reverse_release_risk_pct"] = 0.0
    elif case == "opposite_open_ids":
        payload["opposite_open_position_ids"] = ["position:other"]
    if case not in {"valid", "missing_payload", "bad_hash"}:
        authority["release_binding_hash_sha256"] = (
            package_new_entry_authority_payload_hash_sha256(payload)
        )

    reasons = verifier.lifecycle_release_binding_reasons(row)

    if expected_reason is None:
        assert reasons == []
    else:
        assert expected_reason in reasons


@pytest.mark.parametrize(
    ("case", "expected_reason"),
    (
        ("valid", None),
        ("missing_payload", "replace_pending_release_binding_payload_missing"),
        ("bad_hash", "replace_pending_release_binding_hash_invalid"),
        ("identity", "replace_pending_release_binding_identity_mismatch"),
        ("action", "replace_pending_release_binding_action_mismatch"),
        (
            "selected_mismatch",
            "replace_pending_release_binding_selected_pending_id_mismatch",
        ),
        (
            "noncanonical_pending_set",
            "replace_pending_release_binding_pending_id_set_invalid",
        ),
    ),
)
def test_final_executable_replace_pending_requires_release_binding(
    case: str,
    expected_reason: str | None,
) -> None:
    verifier = load_verifier()
    candidate_id = "replace-pending-release-binding"
    decision_time = "2026-05-13T08:30:00+00:00"
    instance_key = f"{candidate_id}@@{decision_time}"
    payload = {
        "schema_version": "package_pending_replacement_release_binding_v1",
        "candidate_id": candidate_id,
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": instance_key,
        "source_bound_replay_candidate_instance_key": instance_key,
        "candidate_instance_identity_status": "materialized",
        "effective_action_intent": "replace_pending",
        "selected_release_pending_id": "pending:selected",
        "selected_release_reason": "lower_quality_same_side_pending",
        "same_side_pending_ids": ["pending:selected"],
        "same_side_pending_order_ids": [],
        "opposite_pending_ids": [],
        "opposite_pending_order_ids": [],
    }
    replacement = {
        "selected_release_pending_id": "pending:selected",
        "replacement_release_binding_payload": payload,
        "replacement_release_binding_hash_sha256": (
            package_new_entry_authority_payload_hash_sha256(payload)
        ),
    }
    row = {
        "candidate_id": candidate_id,
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": instance_key,
        "source_bound_replay_candidate_instance_key": instance_key,
        "candidate_instance_identity_status": "materialized",
        "scheduler_materialization_action_intent": "replace_pending",
        "replacement_reallocation_selected_release_pending_id": "pending:selected",
        "replacement_reallocation_quality": replacement,
    }
    if case == "missing_payload":
        replacement.pop("replacement_release_binding_payload")
    elif case == "bad_hash":
        replacement["replacement_release_binding_hash_sha256"] = "0" * 64
    elif case == "identity":
        payload["candidate_id"] = "other-candidate"
    elif case == "action":
        payload["effective_action_intent"] = "close_and_reverse"
    elif case == "selected_mismatch":
        payload["selected_release_pending_id"] = "pending:other"
        payload["same_side_pending_ids"].append("pending:other")
    elif case == "noncanonical_pending_set":
        payload["same_side_pending_ids"] = [
            "pending:selected",
            "pending:selected",
        ]
    if case not in {"valid", "missing_payload", "bad_hash"}:
        replacement["replacement_release_binding_hash_sha256"] = (
            package_new_entry_authority_payload_hash_sha256(payload)
        )

    reasons = verifier.lifecycle_release_binding_reasons(row)

    if expected_reason is None:
        assert reasons == []
    else:
        assert expected_reason in reasons


def test_order_transfer_scan_enforces_final_executable_release_binding(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    candidate_id = "bound-close-reverse-without-release-binding"
    decision_time = "2026-05-13T08:30:00+00:00"
    path = tmp_path / "bound-close-reverse.jsonl"
    write_jsonl(
        path,
        [
            {
                "candidate_id": candidate_id,
                "decision_time_utc": decision_time,
                "canonical_replay_candidate_instance_key": (
                    f"{candidate_id}@@{decision_time}"
                ),
                "source_bound_replay_candidate_instance_key": (
                    f"{candidate_id}@@{decision_time}"
                ),
                "candidate_instance_identity_status": "materialized",
                "scheduler_materialization_action_intent": "close_and_reverse",
                "package_replay_order_executable_candidate_use_allowed": True,
                "package_replay_order_executable_transfer_status": "order_bound",
                "package_replay_order_executable_bound_order_id": "order-close-reverse",
                "simulated_order_id": "order-close-reverse",
                "order_status": "pending_accepted",
            }
        ],
    )

    scan = verifier.scan_broad_order_executable_transfer_contract({"order": path})

    assert scan["bad_counts"][
        "order:lifecycle_release_binding:"
        "close_and_reverse_release_binding_payload_missing"
    ] == 1


def test_broad_order_executable_transfer_scan_blocks_diagnostic_selector_materialization_execution(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    order_path = tmp_path / "ORDER_LEDGER.jsonl"
    trade_path = tmp_path / "TRADE_LEDGER.jsonl"
    missed_path = tmp_path / "MISSED_OPPORTUNITY_LEDGER.jsonl"
    order_leak = {
        "candidate_id": "diagnostic-selector-materialization-order",
        "package_replay_order_executable_candidate_use_allowed": True,
        "package_replay_order_executable_transfer_status": "order_bound",
        "package_replay_order_executable_bound_order_id": "order-diagnostic",
        "simulated_order_id": "order-diagnostic",
        "order_status": "pending_accepted",
        "selector_materialization_policy_comparator_status": (
            "diagnostic_current_policy_blocked"
        ),
    }
    trade_leak = {
        "candidate_id": "diagnostic-selector-materialization-trade",
        "package_replay_order_executable_candidate_use_allowed": True,
        "package_replay_order_executable_transfer_status": "trade_bound",
        "package_replay_order_executable_bound_trade_id": "trade-diagnostic",
        "simulated_trade_id": "trade-diagnostic",
        "selector_materialization_policy_comparator": {
            "status": "eligible_for_explicit_targeted_comparator",
        },
    }
    missed_diagnostic = {
        "candidate_id": "diagnostic-selector-materialization-missed",
        "package_replay_order_executable_candidate_use_allowed": False,
        "package_replay_order_executable_transfer_status": "not_order_executable",
        "order_status": "not_sent_missed_opportunity",
        "selector_materialization_policy_comparator_status": (
            "diagnostic_current_policy_blocked"
        ),
    }
    write_jsonl(order_path, [order_leak])
    write_jsonl(trade_path, [trade_leak])
    write_jsonl(missed_path, [missed_diagnostic])

    scan = verifier.scan_broad_order_executable_transfer_contract(
        {"order": order_path, "trade": trade_path, "missed": missed_path}
    )

    assert (
        scan["bad_counts"][
            "order:diagnostic_selector_materialization_policy_materialized"
        ]
        == 1
    )
    assert (
        scan["bad_counts"][
            "trade:diagnostic_selector_materialization_policy_materialized"
        ]
        == 1
    )
    assert not any(key.startswith("missed:") for key in scan["bad_counts"])


def test_broad_order_executable_transfer_scan_fails_bad_signed_soft_transfer_proof(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    path = tmp_path / "SIGNED_SOFT_TRANSFER_LEDGER.jsonl"
    boundary = (
        "predecision_signed_package_soft_transfer_quality_cost_source_order_no_outcome_fields"
    )
    base = {
        "candidate_id": "signed-soft-transfer-bad",
        "package_replay_order_executable_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed": True,
        "package_replay_order_executable_transfer_status": "order_bound",
        "package_replay_order_executable_bound_order_id": "order-signed-soft",
        "simulated_order_id": "order-signed-soft",
        "order_status": "pending_accepted",
        "risk_finalizer_signed_soft_transfer_displacement_allowed": True,
        "risk_finalizer_signed_soft_transfer_displacement_source_boundary": boundary,
        "risk_finalizer_signed_soft_transfer_displacement_uses_outcome_fields": True,
        "finalizer_admission_rank_reason": (
            "risk_admitted_signed_soft_transfer_displacement_rank"
        ),
        "pretrade_cost_packet_status": "PASSED",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "cost_authority": "broker_calibrated_replay_cost",
        "candidate_cost_r_fallback_is_authority": False,
        "source_completeness": 1.0,
        "source_completeness_status": "complete",
        "selected_policy_executable_quality_reallocation_score": -1.15,
        "selected_policy_executable_quality_min_reallocation_quality_score": 0.0,
    }
    write_jsonl(
        path,
        [
            {**base, "candidate_id": f"{ledger}-signed-soft-transfer-bad"}
            for ledger in ("order", "trade", "missed", "scorecard")
        ],
    )

    scan = verifier.scan_broad_order_executable_transfer_contract(
        {
            "order": path,
            "trade": path,
            "missed": path,
            "scorecard": path,
        }
    )

    for ledger in ("order", "trade", "missed", "scorecard"):
        assert (
            scan["bad_counts"][
                f"{ledger}:signed_soft_transfer:"
                "signed_soft_transfer_displacement_uses_outcome_fields_not_false"
            ]
            == 4
        )
        assert (
            scan["bad_counts"][
                f"{ledger}:signed_soft_transfer:"
                "signed_soft_transfer_selected_policy_reallocation_quality_score_below_floor"
            ]
            == 4
        )
        assert scan["bad_counts"][f"{ledger}:order_executable_transfer_contract_bad"] == 4


def test_order_executable_transfer_allowed_uses_shared_aliases() -> None:
    verifier = load_verifier()

    assert (
        verifier.row_order_executable_transfer_allowed(
            {
                "selected_scheduler_package_replay_order_executable_candidate_use_allowed": True
            }
        )
        is True
    )
    assert (
        verifier.row_order_executable_transfer_allowed(
            {
                "scheduler_option_package_replay_order_executable_candidate_use_allowed": False
            }
        )
        is False
    )
    assert (
        verifier.row_order_executable_transfer_allowed(
            {
                "candidate_decision_inputs": {
                    "risk_finalizer_best_package_probe_package_replay_order_executable_candidate_use_allowed": True
                }
            }
        )
        is True
    )


def test_package_parity_summary_scope_rejects_capped_or_narrowed_proof() -> None:
    verifier = load_verifier()

    assert (
        verifier.package_parity_repair_summary_breadth_issues(
            {
                "max_candidates_per_symbol_window": 0,
                "candidate_generation_authority": "uncapped_full_authority",
                "symbol_universe_mode": "full_24_symbol_surface",
                "requested_symbols": [f"SYM{i:02d}" for i in range(24)],
            }
        )
        == []
    )
    issues = verifier.package_parity_repair_summary_breadth_issues(
        {
            "max_candidates_per_symbol_window": 5,
            "candidate_generation_authority": "capped_subset",
            "symbol_universe_mode": "targeted_symbol_subset",
            "requested_symbols": ["XAUUSD"],
        }
    )
    assert "package_parity_repair_summary_max_candidates_per_symbol_window_mismatch" in issues
    assert "package_parity_repair_summary_candidate_generation_authority_mismatch" in issues
    assert (
        "package_parity_repair_summary_symbol_universe_mode_not_full_24_symbol_surface"
        in issues
    )
    assert (
        "package_parity_repair_summary_symbol_scope_narrowed_without_bounded_smoke"
        in issues
    )
    bounded = verifier.package_parity_repair_summary_breadth_issues(
        {
            "max_candidates_per_symbol_window": 0,
            "candidate_generation_authority": "uncapped_full_authority",
            "symbol_universe_mode": "targeted_symbol_subset",
            "requested_symbols": ["XAUUSD"],
            "bounded_smoke": True,
        }
    )
    assert bounded == []


def test_selected_package_replay_bridge_scope_requires_explicit_bounded_smoke() -> None:
    verifier = load_verifier()

    assert verifier.selected_package_replay_bridge_scope_issues(
        {
            "symbol_scope": "full-package",
            "requested_symbol_scope": "full-package",
            "bounded_smoke": False,
        }
    ) == []
    assert verifier.selected_package_replay_bridge_scope_issues(
        {
            "symbol_scope": "lifecycle-labels",
            "bounded_smoke": True,
        }
    ) == []
    assert (
        "selected_package_replay_bridge_bounded_scope_missing_bounded_smoke"
        in verifier.selected_package_replay_bridge_scope_issues(
            {
                "symbol_scope": "lifecycle-labels",
            }
        )
    )
    assert (
        "selected_package_replay_bridge_full_package_marked_bounded_smoke"
        in verifier.selected_package_replay_bridge_scope_issues(
            {
                "symbol_scope": "full-package",
                "requested_symbol_scope": "full-package",
                "bounded_smoke": True,
            }
        )
    )


def test_selected_package_bridge_lifecycle_context_contract_scan() -> None:
    verifier = load_verifier()

    axis_row = {
        "source_axis_row_index": 7,
        "source_axis_lifecycle_label_context_rows": 2,
        "source_axis_lifecycle_label_context_id_count": 2,
        "source_axis_lifecycle_label_context_ids": [
            "fillability_label:1",
            "fillability_label:2",
        ],
        "source_axis_lifecycle_decision_window_id_samples": [
            "decision_window:XAUUSD:LONG:2026-05-05T07:15:00+00:00"
        ],
        "source_axis_lifecycle_missing_decision_label_count": 0,
        "source_axis_lifecycle_pending_created_proxy_only_label_count": 0,
        "source_axis_lifecycle_exact_decision_time_recovered_label_count": 0,
        "source_axis_lifecycle_context_attribution_scope": (
            "bridge_exact_denominator_join"
        ),
        "source_axis_lifecycle_source_window_recoverability_status": (
            "source_decision_window_present"
        ),
        "source_axis_lifecycle_bridge_window_mismatch_status": (
            "bridge_window_overlap"
        ),
        "source_axis_lifecycle_bridge_window_transfer_status": "bridge_window_overlap",
        "source_materialization_transfer_status": "bridge_window_overlap",
        "source_axis_lifecycle_bridge_decision_window_overlap_count": 1,
        "source_axis_lifecycle_bridge_decision_window_overlap_samples": [
            "decision_window:XAUUSD:LONG:2026-05-05T07:15:00+00:00"
        ],
        "source_axis_lifecycle_pending_state_group_samples": ["pending_created"],
        "source_axis_lifecycle_fillability_label_family_samples": [
            "filled_internal_lifecycle"
        ],
        "source_axis_lifecycle_fill_no_fill_label_samples": [
            "internal_filled_broker_ticket_known"
        ],
        "exact_denominator_join_rows": 1,
        "selected_package_replay_bridge_source_counts": {
            "ultimate_replay_authority_candidate_axis_materialization": 1
        },
        "selected_package_replay_bridge_materialization_binding_statuses": [
            "explicit_and_heuristic_member_axis_binding"
        ],
    }
    bridge_row = {
        "candidate_id": "candidate-1",
        "selected_package_denominator_use_reason": (
            "stable_window_lifecycle_context_present_"
            "candidate_id_namespace_mismatch_or_collision"
        ),
        "selected_package_denominator_use_allowed": False,
    }

    scan = verifier.scan_selected_package_bridge_lifecycle_context_contract(
        namespace_rows=[axis_row],
        member_rows=[axis_row],
        bridge_denominator_rows=[bridge_row],
        bridge_label_join_rows=[bridge_row],
    )

    assert scan["bad_counts"] == {}
    assert scan["namespace_lifecycle_context_axis_rows"] == 1
    assert scan["member_lifecycle_context_axis_rows"] == 1
    assert scan["bridge_denominator_use_reason_counts"][
        "stable_window_lifecycle_context_present_"
        "candidate_id_namespace_mismatch_or_collision"
    ] == 2

    stale_scan = verifier.scan_selected_package_bridge_lifecycle_context_contract(
        namespace_rows=[{"source_axis_row_index": 8, "context_lifecycle_label_rows": 3}],
        member_rows=[axis_row],
        bridge_denominator_rows=[{}],
        bridge_label_join_rows=[bridge_row],
    )
    assert stale_scan["bad_counts"][
        "namespace_legacy_context_rows_without_axis_context_ids"
    ] == 1
    assert stale_scan["bad_counts"][
        "denominator_bridge_denominator_use_reason_missing"
    ] == 1
    missing_transfer_scan = verifier.scan_selected_package_bridge_lifecycle_context_contract(
        namespace_rows=[
            {
                **axis_row,
                "source_axis_lifecycle_bridge_window_transfer_status": "",
                "source_materialization_transfer_status": "",
                "source_axis_lifecycle_bridge_decision_window_overlap_count": 0,
                "source_axis_lifecycle_bridge_decision_window_overlap_samples": [],
            }
        ],
        member_rows=[axis_row],
        bridge_denominator_rows=[bridge_row],
        bridge_label_join_rows=[bridge_row],
    )
    assert missing_transfer_scan["bad_counts"][
        "namespace_lifecycle_bridge_window_transfer_status_missing"
    ] == 1
    overlap_without_exact_scope_scan = (
        verifier.scan_selected_package_bridge_lifecycle_context_contract(
            namespace_rows=[
                {
                    **axis_row,
                    "source_axis_lifecycle_context_attribution_scope": (
                        "symbol_side_pair_broadcast_only"
                    ),
                    "exact_denominator_join_rows": 0,
                }
            ],
            member_rows=[axis_row],
            bridge_denominator_rows=[bridge_row],
            bridge_label_join_rows=[bridge_row],
        )
    )
    assert overlap_without_exact_scope_scan["bad_counts"][
        "namespace_lifecycle_bridge_overlap_status_without_exact_axis_authority"
    ] == 1
    unknown_scope_scan = (
        verifier.scan_selected_package_bridge_lifecycle_context_contract(
            namespace_rows=[
                {
                    **axis_row,
                    "source_axis_lifecycle_context_attribution_scope": (
                        "mystery_scope"
                    ),
                }
            ],
            member_rows=[axis_row],
            bridge_denominator_rows=[bridge_row],
            bridge_label_join_rows=[bridge_row],
        )
    )
    assert unknown_scope_scan["bad_counts"][
        "namespace_lifecycle_context_attribution_scope_unknown"
    ] == 1
    inconsistent_transfer_scan = verifier.scan_selected_package_bridge_lifecycle_context_contract(
        namespace_rows=[
            {
                **axis_row,
                "source_axis_lifecycle_bridge_window_transfer_status": "source_window_missing",
                "source_materialization_transfer_status": "source_window_missing",
            }
        ],
        member_rows=[axis_row],
        bridge_denominator_rows=[bridge_row],
        bridge_label_join_rows=[bridge_row],
    )
    assert inconsistent_transfer_scan["bad_counts"][
        "namespace_lifecycle_bridge_source_window_missing_has_source_samples"
    ] == 1
    proxy_without_count_scan = verifier.scan_selected_package_bridge_lifecycle_context_contract(
        namespace_rows=[
            {
                **axis_row,
                "source_axis_lifecycle_decision_window_id_samples": [],
                "source_axis_lifecycle_bridge_window_transfer_status": (
                    "source_window_missing_pending_created_proxy_only"
                ),
                "source_materialization_transfer_status": (
                    "source_window_missing_pending_created_proxy_only"
                ),
                "source_axis_lifecycle_bridge_decision_window_overlap_count": 0,
                "source_axis_lifecycle_bridge_decision_window_overlap_samples": [],
                "source_axis_lifecycle_source_window_recoverability_status": (
                    "pending_created_proxy_only_not_exact_decision_time"
                ),
                "source_axis_lifecycle_bridge_window_mismatch_status": (
                    "source_window_missing"
                ),
                "source_axis_lifecycle_pending_created_proxy_only_label_count": 0,
            }
        ],
        member_rows=[axis_row],
        bridge_denominator_rows=[bridge_row],
        bridge_label_join_rows=[bridge_row],
    )
    assert proxy_without_count_scan["bad_counts"][
        "namespace_lifecycle_source_window_pending_created_proxy_status_without_proxy_count"
    ] == 1
    missing_binding_scan = verifier.scan_selected_package_bridge_lifecycle_context_contract(
        namespace_rows=[
            {
                **axis_row,
                "selected_package_replay_bridge_materialization_binding_statuses": [],
            }
        ],
        member_rows=[axis_row],
        bridge_denominator_rows=[bridge_row],
        bridge_label_join_rows=[bridge_row],
    )
    assert missing_binding_scan["bad_counts"][
        "namespace_selected_package_materialization_binding_status_missing"
    ] == 1


def test_bridge_stop_hazard_normalizer_does_not_invent_partial_projection() -> None:
    bridge = load_bridge()

    row = {}
    bridge._normalize_stop_hazard_cap_truth(row)
    assert row == {}

    passed = {
        "predecision_stop_hazard_guard_status": "passed",
        "predecision_stop_hazard_guard_action": "cap",
    }
    bridge._normalize_stop_hazard_cap_truth(passed)
    assert passed["predecision_stop_hazard_guard_risk_cap_applied"] is False

    capped = {
        "predecision_stop_hazard_guard_status": "capped",
        "predecision_stop_hazard_guard_reason": (
            "predecision_stop_hazard_guard_risk_capped"
        ),
        "predecision_stop_hazard_guard_action": "cap",
        "predecision_stop_hazard_guard_risk_cap_pct": 0.1,
    }
    bridge._normalize_stop_hazard_cap_truth(capped)
    assert capped["predecision_stop_hazard_guard_risk_cap_applied"] is True


def test_marketable_route_binding_blocks_non_immediate_order_bound_rows(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    path = tmp_path / "transfer-immediate-marketable.jsonl"
    rows = [
        {
            "candidate_id": "immediate-route-bound-ok",
            "package_marketable_entry_guard_status": (
                "routed_to_immediate_marketable_limit_replay_order_policy"
            ),
            "limit_marketable_at_decision": True,
            "order_execution_path": "immediate_marketable_limit_at_decision",
            "package_replay_order_executable_candidate_use_allowed": True,
            "package_replay_order_executable_transfer_status": "order_bound",
            "package_replay_order_executable_bound_order_id": "order-ok",
            "simulated_order_id": "order-ok",
            "order_status": "filled",
        },
        {
            "candidate_id": "immediate-route-bound-leak",
            "package_marketable_entry_guard_status": (
                "routed_to_immediate_marketable_limit_replay_order_policy"
            ),
            "limit_marketable_at_decision": True,
            "order_execution_path": "limit_first_probe",
            "package_replay_order_executable_candidate_use_allowed": True,
            "package_replay_order_executable_transfer_status": "order_bound",
            "package_replay_order_executable_bound_order_id": "order-leak",
            "simulated_order_id": "order-leak",
            "order_status": "filled",
        },
        {
            "candidate_id": "immediate-route-final-blocked-ok",
            "package_marketable_entry_guard_status": (
                "routed_to_immediate_marketable_limit_replay_order_policy"
            ),
            "limit_marketable_at_decision": True,
            "order_execution_path": "limit_first_probe",
            "package_replay_order_executable_candidate_use_allowed": True,
            "package_replay_order_executable_transfer_status": "final_blocked",
            "package_replay_order_executable_final_blocker_class": "marketable_guard",
            "package_replay_order_executable_final_blocker_reason": (
                "package_marketable_limit_entry_guard_blocked"
            ),
        },
        {
            "candidate_id": "immediate-route-final-blocked-leak",
            "package_marketable_entry_guard_status": (
                "routed_to_immediate_marketable_limit_replay_order_policy"
            ),
            "limit_marketable_at_decision": True,
            "order_execution_path": "limit_first_probe",
            "package_replay_order_executable_candidate_use_allowed": True,
            "package_replay_order_executable_transfer_status": "final_blocked",
            "package_replay_order_executable_final_blocker_class": "headroom",
            "package_replay_order_executable_final_blocker_reason": (
                "risk_authority_headroom_unavailable"
            ),
        },
        {
            "candidate_id": "immediate-route-final-blocked-fill-realism-ok",
            "package_marketable_entry_guard_status": (
                "routed_to_immediate_marketable_limit_replay_order_policy"
            ),
            "limit_marketable_at_decision": True,
            "order_execution_path": "immediate_marketable_limit_at_decision",
            "package_replay_order_executable_candidate_use_allowed": True,
            "package_replay_order_executable_transfer_status": "final_blocked",
            "package_replay_order_executable_final_blocker_class": "fill_realism",
            "package_replay_order_executable_final_blocker_reason": (
                "ordered_tick_required_for_adverse_before_profit_sequence_not_satisfied"
            ),
            "package_replay_order_executable_final_blocker_source": (
                "fill_realism_authority"
            ),
        },
        {
            "candidate_id": "immediate-route-final-blocked-selector-ok",
            "package_marketable_entry_guard_status": (
                "routed_to_immediate_marketable_limit_replay_order_policy"
            ),
            "limit_marketable_at_decision": True,
            "package_replay_order_executable_candidate_use_allowed": True,
            "package_replay_order_executable_transfer_status": "final_blocked",
            "package_replay_order_executable_final_blocker_class": (
                "selector_materialization"
            ),
            "package_replay_order_executable_final_blocker_reason": (
                "selector_open_reduced_risk_origin_preserved_after_runtime_risk_reduction"
            ),
            "package_replay_order_executable_final_blocker_source": (
                "package_order_executable_final_blocker_fields"
            ),
        },
        {
            "candidate_id": "immediate-route-contract-unmet",
            "package_marketable_entry_guard_status": (
                "routed_to_immediate_marketable_limit_replay_order_policy"
            ),
            "package_marketable_immediate_route_contract_unmet": True,
            "package_marketable_guarded_fallback_contract_unmet_reason": (
                "package_marketable_immediate_route_contract_unmet:"
                "off_configured_session_immediate_marketable_limit_disabled"
            ),
            "package_replay_order_executable_candidate_use_allowed": True,
            "package_replay_order_executable_transfer_status": "final_blocked",
            "package_replay_order_executable_final_blocker_class": "marketable_guard",
            "package_replay_order_executable_final_blocker_reason": (
                "package_marketable_immediate_route_contract_unmet:"
                "off_configured_session_immediate_marketable_limit_disabled"
            ),
            "order_status": "guarded_market_fallback_contract_unmet",
        },
    ]
    write_jsonl(path, rows)

    scan = verifier.scan_broad_order_executable_transfer_contract({"order": path})

    assert scan["bad_counts"]["order:order_executable_transfer_contract_bad"] == 6
    assert scan["bad_counts"]["order:blocked_status_executable_claim"] == 5
    assert (
        scan["bad_counts"][
            "order:blocked_status_executable_claim:"
            "package_replay_order_executable_transfer_status:final_blocked"
        ]
        == 5
    )
    assert (
        scan["bad_counts"].get("order:immediate_marketable_route_contract_unmet", 0)
        == 0
    )
    assert (
        scan["bad_counts"][
            "order:immediate_marketable_route_bound_with_non_immediate_path"
        ]
        == 1
    )
    assert (
        scan["bad_counts"].get(
            "order:immediate_marketable_route_final_blocker_missing", 0
        )
        == 1
    )


def test_order_transfer_scan_treats_not_order_executable_status_as_false(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    path = tmp_path / "scorecard-not-order-executable.jsonl"
    write_jsonl(
        path,
        [
            {
                "candidate_id": "scorecard-package-blocked",
                "package_replay_order_executable_candidate_use_allowed": False,
                "package_replay_order_executable_transfer_status": (
                    "not_order_executable"
                ),
                "package_replay_order_executable_final_blocker_class": (
                    "package_authority"
                ),
                "package_replay_order_executable_final_blocker_reason": (
                    "package_fill_floor_unresolved_executable_authority:"
                    "off_configured_session_requires_explicit_off_session_authority"
                ),
            }
        ],
    )

    scan = verifier.scan_broad_order_executable_transfer_contract({"scorecard": path})

    assert scan["row_counts"]["scorecard_order_executable_false_rows"] == 1
    assert scan["bad_counts"] == {}


def test_order_transfer_scan_flags_unsigned_router_refusal_executable_alias(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    path = tmp_path / "unsigned-router-refusal-order.jsonl"
    valid_hash = "a" * 64
    rows = [
        {
            "candidate_id": "unsigned-router-refusal",
            "selector_reason": (
                "source_bound_router_refusal_open_reduced_materialized_for_replay"
            ),
            "package_replay_order_executable_candidate_use_allowed": True,
            "replay_candidate_use_allowed_now": True,
            "package_new_entry_authority_status": (
                "valid_signed_predecision_new_entry_authority"
            ),
            "package_new_entry_authority_valid": False,
            "package_new_entry_authority_signed": False,
            "package_replay_order_executable_transfer_status": "final_blocked",
            "package_replay_order_executable_final_blocker_class": (
                "selector_materialization"
            ),
            "package_replay_order_executable_final_blocker_reason": (
                "selector_open_reduced_risk_origin_preserved_after_runtime_risk_reduction"
            ),
        },
        {
            "candidate_id": "signed-router-refusal",
            "selector_reason": (
                "source_bound_router_refusal_open_reduced_materialized_for_replay"
            ),
            "package_replay_order_executable_candidate_use_allowed": True,
            "replay_candidate_use_allowed_now": True,
            "package_new_entry_authority_status": (
                "valid_signed_predecision_new_entry_authority"
            ),
            "package_new_entry_authority_valid": True,
            "package_new_entry_authority_signed": True,
            "package_new_entry_authority_hash_sha256": valid_hash,
            "expected_package_new_entry_authority_hash_sha256": valid_hash,
            "package_new_entry_authority_source_bound_replay_candidate_instance_key": (
                "signed-router-refusal@@2026-06-01T09:00:00+00:00"
            ),
            "package_replay_order_executable_transfer_status": "final_blocked",
            "package_replay_order_executable_final_blocker_class": (
                "selector_materialization"
            ),
            "package_replay_order_executable_final_blocker_reason": (
                "selector_open_reduced_risk_origin_preserved_after_runtime_risk_reduction"
            ),
        },
    ]
    write_jsonl(path, rows)

    scan = verifier.scan_broad_order_executable_transfer_contract({"missed": path})

    assert (
        scan["bad_counts"]["missed:unsigned_router_refusal_executable_authority"]
        == 2
    )


def test_missed_counterfactual_fill_is_not_real_materialization(tmp_path: Path) -> None:
    verifier = load_verifier()
    path = tmp_path / "missed-counterfactual-fill.jsonl"
    rows = [
        {
            "candidate_id": "missed-counterfactual",
            "order_status": "not_sent_missed_opportunity",
            "fill_status": "filled_from_ordered_m1_path",
            "fill_status_scope": "counterfactual_missed_opportunity",
            "counterfactual_fill_status": "filled_from_ordered_m1_path",
            "order_execution_path": "counterfactual_not_selected_policy_plan",
            "package_replay_executable_candidate_use_allowed": False,
            "package_replay_executable_candidate_use_allowed_reason": (
                "pretrade_cost_packet_status_REFUSED"
            ),
            "package_replay_order_executable_candidate_use_allowed": False,
            "package_replay_order_executable_transfer_status": "final_blocked",
        }
    ]
    write_jsonl(path, rows)

    scan = verifier.scan_broad_order_executable_transfer_contract({"missed": path})

    assert scan["bad_counts"] == {}


def test_broad_order_executable_transfer_contract_accepts_expanded_blockers(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    path = tmp_path / "transfer-expanded-blockers.jsonl"
    rows = [
        {
            "candidate_id": f"blocked-{blocker}",
            "package_replay_order_executable_candidate_use_allowed": False,
            "package_replay_order_executable_transfer_status": "final_blocked",
            "package_replay_order_executable_final_blocker_class": blocker,
            "package_replay_order_executable_final_blocker_reason": reason,
        }
        for blocker, reason in [
            ("selector_materialization", "selector_not_risk_bearing_cost_failed"),
            ("scheduler_selection", "scheduler_vetoed_candidate"),
            (
                "stop_hazard_materialization",
                "stop_hazard_materialization_requires_reallocation_dominance",
            ),
            (
                "cost_authority",
                "broker_cost_packet_refused:total_cost_r_exceeds_limit",
            ),
            (
                "package_authority",
                "raw_selector_reject_open_reduced_order_executable_promotion_contract_failed",
            ),
            (
                "lifecycle_authority",
                "package_lifecycle_root_authority_not_allowed:"
                "pending_replacement_causal_quality_gate_failed",
            ),
        ]
    ]
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))

    scan = verifier.scan_broad_order_executable_transfer_contract({"missed": path})

    assert scan["bad_counts"] == {}
    assert scan["transfer_status_counts"]["missed:final_blocked"] == len(rows)
    for row in rows:
        blocker = row["package_replay_order_executable_final_blocker_class"]
        assert scan["blocker_counts"][f"missed:{blocker}"] == 1


def test_order_transfer_scan_blocks_suppressed_pressure_materialization_escape(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    path = tmp_path / "transfer-stop-pressure.jsonl"
    rows = [
        {
            "candidate_id": "bad-suppressed-pressure-final-blocked",
            "package_replay_order_executable_candidate_use_allowed": False,
            "package_replay_order_executable_transfer_status": "final_blocked",
            "package_replay_order_executable_final_blocker_class": (
                "stop_hazard_materialization"
            ),
            "package_replay_order_executable_final_blocker_reason": (
                "stop_hazard_materialization_requires_reallocation_dominance"
            ),
            "package_replay_order_executable_final_blocker_source": (
                "stop_hazard_materialization_authority"
            ),
            "package_marketable_entry_guard_status": (
                "routed_to_immediate_marketable_limit_replay_order_policy"
            ),
            "stop_hazard_materialization_stop_pressure": True,
            "stop_hazard_materialization_pressure_score_materialized": True,
            "stop_hazard_materialization_pressure_suppressed_reason": (
                "stop_hazard_pressure_requires_base_fragility"
            ),
            "stop_hazard_materialization_requires_reallocation_dominance": True,
            "stop_hazard_materialization_reallocation_dominance_allowed": False,
            "stop_hazard_materialization_blocked": True,
        },
        {
            "candidate_id": "good-suppressed-pressure-bound",
            "package_replay_order_executable_candidate_use_allowed": True,
            "package_replay_order_executable_transfer_status": "order_bound",
            "package_replay_order_executable_bound_order_id": "order-bad",
            "simulated_order_id": "order-bad",
            "order_status": "pending_accepted",
            "order_execution_path": "immediate_marketable_limit_at_decision",
            "package_marketable_entry_guard_status": (
                "routed_to_immediate_marketable_limit_replay_order_policy"
            ),
            "stop_hazard_materialization_stop_pressure": False,
            "stop_hazard_materialization_pressure_score_materialized": True,
            "stop_hazard_materialization_pressure_suppressed_reason": (
                "stop_hazard_pressure_requires_base_fragility"
            ),
            "stop_hazard_materialization_requires_reallocation_dominance": False,
            "stop_hazard_materialization_reallocation_dominance_allowed": True,
            "stop_hazard_materialization_blocked": False,
        },
    ]
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))

    scan = verifier.scan_broad_order_executable_transfer_contract({"order": path})

    assert scan["blocker_counts"]["order:stop_hazard_materialization"] == 1
    assert scan["transfer_status_counts"]["order:final_blocked"] == 1
    assert scan["transfer_status_counts"]["order:order_bound"] == 1
    assert scan["bad_counts"]["order:order_executable_transfer_contract_bad"] == 1
    assert (
        scan["bad_counts"][
            "order:base_fragility_suppressed_pressure_materialization_block"
        ]
        == 1
    )


def test_same_side_pending_duplicate_lifecycle_authority_scan_flags_filled_scale_in(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    order_path = tmp_path / "ORDER_LEDGER.jsonl"
    trade_path = tmp_path / "TRADE_LEDGER.jsonl"
    missed_path = tmp_path / "MISSED_OPPORTUNITY_LEDGER.jsonl"
    write_jsonl(
        order_path,
        [
            {
                "candidate_id": "good-replace",
                "simulated_order_id": "order-good",
                "symbol": "BTCUSD",
                "side": "LONG",
                "order_status": "filled",
                "same_side_pending_order_ids": ["old-pending"],
                "same_symbol_lifecycle_action": "replace_pending",
                "pending_replacement_applied": True,
                "pending_replacement_cancel_commit_status": (
                    "admitted_pending_cancel_commit"
                ),
            },
            {
                "candidate_id": "good-scale-in",
                "simulated_order_id": "order-scale-in-good",
                "symbol": "BTCUSD",
                "side": "LONG",
                "order_status": "filled",
                "canonical_replay_context_envelope": {
                    "same_symbol_replay_exposure_context": {
                        "same_side_pending_order_ids": ["old-pending-2"],
                        "same_side_pending_risk_pct": 0.25,
                    }
                },
                "same_symbol_lifecycle_action": "same_direction_scale_in",
                "scheduler_package_lifecycle_scale_in_opportunity_cost_allowed": True,
                "package_lifecycle_root_authority": {
                    "release_kind": "same_symbol_scale_in",
                    "signed_authority_valid": True,
                },
            },
            {
                "candidate_id": "bad-scale-in",
                "simulated_order_id": "order-bad",
                "symbol": "BTCUSD",
                "side": "LONG",
                "order_status": "filled",
                "same_side_pending_order_ids": ["old-pending-4"],
                "same_symbol_lifecycle_action": "same_direction_scale_in",
            },
        ],
    )
    write_jsonl(
        trade_path,
        [
            {
                "candidate_id": "bad-trade-scale-in",
                "simulated_order_id": "order-trade-bad",
                "simulated_trade_id": "trade-bad",
                "symbol": "BTCUSD",
                "side": "LONG",
                "fill_status": "filled_from_ordered_m1_path",
                "same_side_pending_count": 1,
                "same_symbol_lifecycle_action": "same_direction_scale_in",
            }
        ],
    )
    write_jsonl(
        missed_path,
        [
            {
                "candidate_id": "missed-counterfactual-replace",
                "symbol": "BTCUSD",
                "side": "LONG",
                "order_status": "not_sent_missed_opportunity",
                "fill_status": "filled_from_ordered_m1_path",
                "counterfactual_order_fill_status": "filled_from_ordered_m1_path",
                "same_side_pending_order_ids": ["old-pending-3"],
                "same_symbol_lifecycle_action": "replace_pending",
            }
        ],
    )

    scan = verifier.scan_same_side_pending_duplicate_lifecycle_authority(
        {"order": order_path, "trade": trade_path, "missed": missed_path}
    )

    assert (
        scan["row_counts"]["order_filled_same_side_pending_replace_ok_rows"] == 1
    )
    assert (
        scan["row_counts"]["order_filled_same_side_pending_scale_in_ok_rows"] == 1
    )
    assert (
        scan["bad_counts"][
            "order:same_side_pending_duplicate_filled_without_lifecycle_authority"
        ]
        == 1
    )
    assert (
        scan["bad_counts"][
            "trade:same_side_pending_duplicate_filled_without_lifecycle_authority"
        ]
        == 1
    )
    assert scan["row_counts"].get("missed_filled_rows", 0) == 0
    assert not any(key.startswith("missed:") for key in scan["bad_counts"])
    assert {
        row["candidate_id"]
        for row in scan["sample_bad"]
    } == {"bad-scale-in", "bad-trade-scale-in"}


def test_broad_selector_materialization_and_r_identity_scan_flags_drift(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    path = tmp_path / "trade.jsonl"
    rows = [
        {
            "candidate_id": "good-materialized",
            "selector_action_origin": "reject",
            "effective_selector_action": "open-reduced-risk",
            "scheduler_materialization_original_selector_action": "reject",
            "gross_r": 1.25,
            "expected_cost_r": 0.25,
            "net_proxy_r": 1.0,
            "r_identity_check": 0.0,
        },
        {
            "candidate_id": "bad-materialized",
            "selector_action_origin": "reject",
            "effective_selector_action": "trade",
        },
        {
            "candidate_id": "bad-r-identity",
            "selector_action_origin": "trade",
            "effective_selector_action": "trade",
            "gross_r": 1.25,
            "expected_cost_r": 0.25,
            "net_proxy_r": 0.50,
        },
    ]
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))

    scan = verifier.scan_broad_selector_materialization_and_r_identity(
        {"trade": path}
    )

    assert scan["row_counts"]["trade_selector_pair_rows"] == 3
    assert scan["row_counts"]["trade_selector_materialized_rows"] == 2
    assert (
        scan["bad_counts"][
            "trade:selector_materialized_without_original_selector_action"
        ]
        == 1
    )
    assert scan["bad_counts"]["trade:r_identity_computed_nonzero"] == 1


def test_selected_package_executed_authority_scan_requires_fill_realism_class() -> None:
    verifier = load_verifier()
    base = {
        "candidate_id": "candidate-fill-realism-good",
        "order_status": "filled",
        "decision_time_utc": "2026-05-13T08:00:00+00:00",
        "candidate_instance_identity_status": "materialized",
        "canonical_replay_candidate_instance_key": (
            "candidate-fill-realism-good@@2026-05-13T08:00:00+00:00"
        ),
        "risk_finalizer_probe_instance_key": (
            "candidate-fill-realism-good@@2026-05-13T08:00:00+00:00"
        ),
        "source_bound_replay_candidate_instance_key": (
            "candidate-fill-realism-good@@2026-05-13T08:00:00+00:00"
        ),
        "candidate_decision_quality_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        "source_boundary": "source_bound_asof_timewarp_decision_input",
        "pretrade_cost_packet_status": "PASSED",
        "pretrade_cost_refusal_reasons": [],
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "source_gap_cost_fallback_blocked": False,
        "candidate_cost_r_fallback_is_authority": False,
        "fill_realism_class": "passive_queue_confirmed",
        "package_replay_executable_candidate_use_allowed": True,
        "selected_scheduler_package_replay_executable_candidate_use_allowed": True,
        "selected_package_candidate_status_join_status": "exact_candidate_window_join",
        "selected_package_candidate_status_join_key": (
            "candidate-fill-realism-good@@2026-05-13T08:00:00+00:00"
        ),
        "role_disposition": "source_bound_candidate",
        "matched_sleeve_ids": ["sleeve-fixture"],
        "matched_sleeve_count": 1,
        "admission_sleeve_match_count": 1,
        "selector_action": "trade",
        "scheduler_materialization_action_intent": "new_position",
        "fill_realism_class": "passive_queue_confirmed",
    }

    scan = verifier.scan_selected_package_executed_order_trade_authority(
        {
            "fixture": (
                [],
                [
                    base,
                    {
                        **{
                            key: value
                            for key, value in base.items()
                            if key != "fill_realism_class"
                        },
                        "candidate_id": "candidate-fill-realism-missing",
                        "selected_package_candidate_status_join_key": (
                            "candidate-fill-realism-missing@@2026-05-13T08:00:00+00:00"
                        ),
                    },
                    {
                        **base,
                        "candidate_id": "candidate-fill-realism-first-touch",
                        "selected_package_candidate_status_join_key": (
                            "candidate-fill-realism-first-touch@@2026-05-13T08:00:00+00:00"
                        ),
                        "fill_realism_class": "first_touch_optimistic",
                    },
                    {
                        **base,
                        "candidate_id": "candidate-fill-realism-diagnostic",
                        "package_execution_result_scope": "diagnostic_counterfactual_only",
                        "fill_realism_class": "first_touch_optimistic",
                    },
                ],
                [
                    {
                        **base,
                        "candidate_id": "candidate-fill-realism-m15",
                        "simulated_trade_id": "trade-fill-realism-m15",
                        "selected_package_candidate_status_join_key": (
                            "candidate-fill-realism-m15@@2026-05-13T08:00:00+00:00"
                        ),
                        "fill_realism_class": "m15_proxy",
                    }
                ],
            )
        }
    )

    bad = scan["bad_counts"]
    assert bad["fixture.order:executable_fill_realism_class_missing"] == 1
    assert bad["fixture.order:first_touch_optimistic_fill_marked_executable"] == 1
    assert bad["fixture.trade:m15_proxy_fill_marked_executable"] == 1
    assert "fixture.order:diagnostic_counterfactual_only" not in bad


def test_selected_package_executed_authority_scan_flags_unresolved_package_fill_floor_order_trade() -> None:
    verifier = load_verifier()
    order_key = "candidate-unresolved-order@@2026-05-13T08:00:00+00:00"
    trade_key = "candidate-unresolved-trade@@2026-05-13T08:15:00+00:00"
    base = {
        "candidate_instance_identity_status": "materialized",
        "candidate_decision_quality_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        "source_boundary": "source_bound_asof_timewarp_decision_input",
        "pretrade_cost_packet_status": "PASSED",
        "pretrade_cost_refusal_reasons": [],
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "source_gap_cost_fallback_blocked": False,
        "candidate_cost_r_fallback_is_authority": False,
        "fill_realism_class": "passive_queue_confirmed",
        "package_replay_executable_candidate_use_allowed": True,
        "package_replay_order_executable_candidate_use_allowed": True,
        "selected_scheduler_package_replay_executable_candidate_use_allowed": True,
        "selected_scheduler_package_replay_order_executable_candidate_use_allowed": True,
        "selected_package_candidate_status_join_status": "exact_candidate_window_join",
        "role_disposition": "source_bound_candidate",
        "matched_sleeve_ids": ["sleeve-fixture"],
        "matched_sleeve_count": 1,
        "admission_sleeve_match_count": 1,
        "selector_action": "trade",
        "effective_selector_action": "trade",
        "scheduler_materialization_action_intent": "new_position",
    }
    order_row = {
        **base,
        "candidate_id": "candidate-unresolved-order",
        "decision_time_utc": "2026-05-13T08:00:00+00:00",
        "canonical_replay_candidate_instance_key": order_key,
        "risk_finalizer_probe_instance_key": order_key,
        "source_bound_replay_candidate_instance_key": order_key,
        "selected_package_candidate_status_join_key": order_key,
        "simulated_order_id": "order-unresolved-fill-floor",
        "order_status": "pending_accepted",
        "scheduler_option_package_fill_floor_authority_unresolved_failures": [
            "fill_probability_below_execution_authority_floor"
        ],
    }
    trade_row = {
        **base,
        "candidate_id": "candidate-unresolved-trade",
        "decision_time_utc": "2026-05-13T08:15:00+00:00",
        "canonical_replay_candidate_instance_key": trade_key,
        "risk_finalizer_probe_instance_key": trade_key,
        "source_bound_replay_candidate_instance_key": trade_key,
        "selected_package_candidate_status_join_key": trade_key,
        "simulated_trade_id": "trade-unresolved-fill-floor",
        "order_status": "filled",
        "risk_finalizer_scheduler_option_package_fill_floor_authority_unresolved_failures": [
            "fill_probability_below_execution_authority_floor"
        ],
    }

    scan = verifier.scan_selected_package_executed_order_trade_authority(
        {"fixture": ([], [order_row], [trade_row])}
    )

    bad = scan["bad_counts"]
    assert bad["fixture.order:emitted_order_authority_leak"] == 1
    assert (
        bad["fixture.order:package_fill_floor_unresolved_executable_authority"]
        == 1
    )
    assert bad["fixture.trade:executed_authority_leak"] == 1
    assert (
        bad["fixture.trade:package_fill_floor_unresolved_executable_authority"]
        == 1
    )


def test_selected_package_executed_authority_scan_accepts_oracle_order_trade_action_parity() -> None:
    verifier = load_verifier()
    instance_key = "candidate-parity@@2026-05-13T08:00:00+00:00"
    base = {
        "candidate_id": "candidate-parity",
        "canonical_replay_candidate_instance_key": instance_key,
        "decision_time_utc": "2026-05-13T08:00:00+00:00",
        "selector_action": "open-reduced-risk",
        "effective_selector_action": "open-reduced-risk",
        "materialized_package_new_entry_authority_selector_action": (
            "open-reduced-risk"
        ),
        "scheduler_materialization_action_intent": "new_position",
        "package_new_entry_authority_target_action_intent": "new_position",
        "package_new_entry_authority_selector_action": "open-reduced-risk",
        "package_new_entry_authority_hash_sha256": "hash-parity",
        "order_status": "pending",
    }

    scan = verifier.scan_selected_package_executed_order_trade_authority(
        {
            "fixture": {
                "oracle": [{**base, "simulated_order_id": "oracle-parity"}],
                "order": [{**base, "simulated_order_id": "order-parity"}],
                "trade": [],
            }
        }
    )

    assert (
        scan["bad_counts"].get(
            "fixture:oracle_order_trade_action_contract_mismatch", 0
        )
        == 0
    )


def test_selected_package_executed_authority_scan_fails_oracle_action_mismatch() -> None:
    verifier = load_verifier()
    instance_key = "candidate-mismatch@@2026-05-13T08:00:00+00:00"
    base = {
        "candidate_id": "candidate-mismatch",
        "canonical_replay_candidate_instance_key": instance_key,
        "decision_time_utc": "2026-05-13T08:00:00+00:00",
        "selector_action": "open-reduced-risk",
        "effective_selector_action": "open-reduced-risk",
        "materialized_package_new_entry_authority_selector_action": (
            "open-reduced-risk"
        ),
        "scheduler_materialization_action_intent": "new_position",
        "package_new_entry_authority_target_action_intent": "new_position",
        "package_new_entry_authority_selector_action": "open-reduced-risk",
        "package_new_entry_authority_hash_sha256": "hash-mismatch",
        "order_status": "pending",
    }

    scan = verifier.scan_selected_package_executed_order_trade_authority(
        {
            "fixture": {
                "oracle": [
                    {
                        **base,
                        "simulated_order_id": "oracle-mismatch",
                        "package_new_entry_authority_target_action_intent": (
                            "close_and_reverse"
                        ),
                    }
                ],
                "order": [{**base, "simulated_order_id": "order-mismatch"}],
                "trade": [],
            }
        }
    )

    assert (
        scan["bad_counts"][
            "fixture:oracle_order_trade_action_contract_mismatch"
        ]
        == 1
    )
    assert (
        scan["bad_counts"][
            "fixture:oracle_order_trade_action_contract_mismatch:"
            "package_new_entry_authority_target_action_intent"
        ]
        == 1
    )


def test_selected_package_executed_authority_scan_fails_oracle_join_conflict() -> None:
    verifier = load_verifier()

    scan = verifier.scan_selected_package_executed_order_trade_authority(
        {
            "fixture": {
                "oracle": [
                    {
                        "candidate_id": "candidate-oracle-conflict",
                        "canonical_replay_candidate_instance_key": (
                            "candidate-oracle-conflict@@2026-05-13T08:00:00+00:00"
                        ),
                        "decision_time_utc": "2026-05-13T08:00:00+00:00",
                        "selector_action": "open-reduced-risk",
                        "scheduler_materialization_action_intent": "new_position",
                        "order_status": "pending",
                        "selected_package_candidate_status_join_execution_authority_conflict": True,
                    }
                ],
                "order": [],
                "trade": [],
            }
        }
    )

    assert (
        scan["bad_counts"][
            "fixture.oracle:selected_package_candidate_status_join_execution_"
            "authority_conflict"
        ]
        == 1
    )


def test_selected_package_executed_authority_scan_fails_package_displacement_quality_rejected() -> None:
    verifier = load_verifier()
    base = {
        "candidate_id": "candidate-displacement-rejected",
        "order_status": "filled",
        "candidate_instance_identity_status": "materialized",
        "canonical_replay_candidate_instance_key": (
            "candidate-displacement-rejected@@2026-05-13T08:00:00+00:00"
        ),
        "risk_finalizer_probe_instance_key": (
            "candidate-displacement-rejected@@2026-05-13T08:00:00+00:00"
        ),
        "source_bound_replay_candidate_instance_key": (
            "candidate-displacement-rejected@@2026-05-13T08:00:00+00:00"
        ),
        "candidate_decision_quality_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        "source_boundary": "source_bound_asof_timewarp_decision_input",
        "pretrade_cost_packet_status": "PASSED",
        "pretrade_cost_refusal_reasons": [],
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "source_gap_cost_fallback_blocked": False,
        "candidate_cost_r_fallback_is_authority": False,
        "fill_realism_class": "passive_queue_confirmed",
        "package_replay_executable_candidate_use_allowed": True,
        "selected_scheduler_package_replay_executable_candidate_use_allowed": True,
        "selected_package_candidate_status_join_status": "exact_candidate_window_join",
        "selected_package_candidate_status_join_key": (
            "candidate-displacement-rejected@@2026-05-13T08:00:00+00:00"
        ),
        "role_disposition": "source_bound_candidate",
        "matched_sleeve_ids": ["sleeve-fixture"],
        "matched_sleeve_count": 1,
        "admission_sleeve_match_count": 1,
        "selector_action": "trade",
        "scheduler_materialization_action_intent": "new_position",
        "scheduler_candidate_decision_inputs": {
            "package_displacement_quality": {
                "applies": True,
                "enabled": True,
                "allowed": False,
                "reason": "package_soft_authority_edge_below_primary",
                "uses_outcome_fields": False,
            }
        },
    }

    scan = verifier.scan_selected_package_executed_order_trade_authority(
        {"fixture": ([base], [{**base, "simulated_trade_id": "trade-displacement"}])}
    )

    bad = scan["bad_counts"]
    assert (
        bad[
            "fixture.order:package_soft_authority_displacement_quality_failed"
        ]
        == 2
    )
    assert (
        bad[
            "fixture.trade:package_soft_authority_displacement_quality_failed"
        ]
        == 1
    )


def test_selected_package_executed_authority_scan_fails_signed_soft_transfer_bad_boundary() -> None:
    verifier = load_verifier()
    boundary = (
        "predecision_signed_package_soft_transfer_quality_cost_source_order_no_outcome_fields"
    )
    base = {
        "candidate_id": "candidate-signed-soft-transfer",
        "order_status": "filled",
        "candidate_instance_identity_status": "materialized",
        "canonical_replay_candidate_instance_key": (
            "candidate-signed-soft-transfer@@2026-05-13T08:00:00+00:00"
        ),
        "risk_finalizer_probe_instance_key": (
            "candidate-signed-soft-transfer@@2026-05-13T08:00:00+00:00"
        ),
        "source_bound_replay_candidate_instance_key": (
            "candidate-signed-soft-transfer@@2026-05-13T08:00:00+00:00"
        ),
        "candidate_decision_quality_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        "source_boundary": "source_bound_asof_timewarp_decision_input",
        "selector_action": "trade",
        "scheduler_materialization_action_intent": "new_position",
        "pretrade_cost_packet_status": "PASSED",
        "pretrade_cost_refusal_reasons": [],
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "cost_authority": "broker_calibrated_replay_cost",
        "source_gap_cost_fallback_blocked": False,
        "candidate_cost_r_fallback_is_authority": False,
        "source_completeness": 1.0,
        "source_completeness_status": "complete",
        "fill_realism_class": "passive_queue_confirmed",
        "package_replay_executable_candidate_use_allowed": True,
        "package_replay_order_executable_candidate_use_allowed": True,
        "selected_scheduler_package_replay_executable_candidate_use_allowed": True,
        "selected_package_candidate_status_join_status": "exact_candidate_window_join",
        "selected_package_candidate_status_join_key": (
            "candidate-signed-soft-transfer@@2026-05-13T08:00:00+00:00"
        ),
        "role_disposition": "source_bound_candidate",
        "matched_sleeve_ids": ["sleeve-fixture"],
        "matched_sleeve_count": 1,
        "admission_sleeve_match_count": 1,
        "risk_finalizer_signed_soft_transfer_displacement_allowed": True,
        "risk_finalizer_signed_soft_transfer_displacement_source_boundary": (
            "postdecision_bad_boundary"
        ),
        "risk_finalizer_signed_soft_transfer_displacement_uses_outcome_fields": False,
        "selected_policy_executable_quality_gate_signed_soft_transfer_displacement_override_applied": True,
        "selected_policy_executable_quality_gate_signed_soft_transfer_displacement_source_boundary": boundary,
        "selected_policy_executable_quality_gate_signed_soft_transfer_displacement_uses_outcome_fields": False,
        "finalizer_admission_rank_reason": (
            "risk_admitted_signed_soft_transfer_displacement_rank"
        ),
    }

    scan = verifier.scan_selected_package_executed_order_trade_authority(
        {"fixture": ([base], [{**base, "simulated_trade_id": "trade-signed-soft"}])}
    )

    bad = scan["bad_counts"]
    assert (
        bad[
            "fixture.order:signed_soft_transfer:"
            "signed_soft_transfer_displacement_source_boundary_invalid"
        ]
        == 2
    )
    assert (
        bad[
            "fixture.trade:signed_soft_transfer:"
            "signed_soft_transfer_displacement_source_boundary_invalid"
        ]
        == 1
    )


def test_signed_soft_transfer_displacement_reliance_reasons_cover_causal_contract() -> None:
    verifier = load_verifier()
    boundary = (
        "predecision_signed_package_soft_transfer_quality_cost_source_order_no_outcome_fields"
    )
    valid = {
        "risk_finalizer_signed_soft_transfer_displacement_allowed": True,
        "risk_finalizer_signed_soft_transfer_displacement_source_boundary": boundary,
        "risk_finalizer_signed_soft_transfer_displacement_uses_outcome_fields": False,
        "finalizer_admission_rank_reason": (
            "risk_admitted_signed_soft_transfer_displacement_rank"
        ),
        "pretrade_cost_packet_status": "PASSED",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "cost_authority": "broker_calibrated_replay_cost",
        "candidate_cost_r_fallback_is_authority": False,
        "package_replay_order_executable_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed": True,
        "source_completeness": 1.0,
        "source_completeness_status": "complete",
        "selected_policy_executable_quality_reallocation_score": 0.25,
        "selected_policy_executable_quality_min_reallocation_quality_score": 0.0,
    }

    assert verifier.signed_soft_transfer_displacement_reliance_reasons(valid) == []

    bad = {
        **valid,
        "risk_finalizer_signed_soft_transfer_displacement_allowed": False,
        "risk_finalizer_signed_soft_transfer_displacement_source_boundary": "bad",
        "risk_finalizer_signed_soft_transfer_displacement_uses_outcome_fields": True,
        "pretrade_cost_packet_status": "REFUSED",
        "cost_source_gap_status": "source_gap_unresolved",
        "cost_authority": "candidate_cost_r_diagnostic_proxy",
        "candidate_cost_r_fallback_is_authority": True,
        "package_replay_order_executable_candidate_use_allowed": False,
        "package_replay_executable_candidate_use_allowed": False,
        "source_completeness": 0.2,
        "source_completeness_status": "incomplete",
        "selected_policy_executable_quality_reallocation_score": -1.15,
        "selected_policy_executable_quality_min_reallocation_quality_score": 0.0,
    }
    reasons = verifier.signed_soft_transfer_displacement_reliance_reasons(bad)

    for expected in (
        "signed_soft_transfer_displacement_allowed_not_true",
        "signed_soft_transfer_displacement_source_boundary_invalid",
        "signed_soft_transfer_displacement_uses_outcome_fields_not_false",
        "signed_soft_transfer_cost_status:REFUSED",
        "signed_soft_transfer_cost_source_gap_status:source_gap_unresolved",
        "signed_soft_transfer_cost_authority:candidate_cost_r_diagnostic_proxy",
        "signed_soft_transfer_candidate_cost_fallback_is_authority",
        "signed_soft_transfer_order_executable_not_true",
        "signed_soft_transfer_package_executable_not_true",
        "signed_soft_transfer_source_completeness_incomplete",
        "signed_soft_transfer_selected_policy_reallocation_quality_score_below_floor",
    ):
        assert expected in reasons


def test_v220_hard_clean_capped_contract_allows_below_floor_reduced_risk() -> None:
    verifier = load_verifier()
    row = v220_hard_clean_capped_verifier_row()

    assert verifier.v220_hard_clean_capped_reduced_risk_contract_applies(row) is True
    assert verifier.v220_hard_clean_capped_reduced_risk_contract_reasons(row) == []
    assert verifier.signed_soft_transfer_displacement_reliance_reasons(row) == []
    assert (
        verifier.scheduler_materialization_skip_is_soft_transfer(
            row,
            row["scheduler_materialization_skip_reason"],
        )
        is True
    )


def test_v220_hard_clean_capped_contract_rejects_each_authority_escape() -> None:
    verifier = load_verifier()
    denied: list[tuple[str, dict, str]] = []

    generic_negative = v220_hard_clean_capped_verifier_row()
    generic_negative["replacement_reallocation_quality"][
        "soft_risk_cap_transfer_eligible"
    ] = False
    denied.append(
        ("generic_negative", generic_negative, "hard_clean_capped_marker_not_true")
    )

    hard_failure = v220_hard_clean_capped_verifier_row()
    hard_failure["replacement_reallocation_quality"]["raw_hard_gate_failures"] = [
        "unit_risk_geometry_hard_failure"
    ]
    denied.append(
        (
            "unit_risk_geometry",
            hard_failure,
            "hard_clean_capped_raw_hard_failures_present",
        )
    )

    transfer_failure = v220_hard_clean_capped_verifier_row()
    transfer_failure["replacement_reallocation_quality"][
        "risk_cap_adjusted_expected_transfer_score"
    ] = 0.0
    denied.append(
        (
            "risk_adjusted_transfer",
            transfer_failure,
            "hard_clean_capped_risk_adjusted_transfer_not_positive",
        )
    )

    signed_failure = v220_hard_clean_capped_verifier_row()
    signed_failure["package_new_entry_authority_valid"] = False
    denied.append(
        (
            "signed_authority",
            signed_failure,
            "hard_clean_capped_signed_authority:package_new_entry_authority_invalid:valid_signed_predecision_new_entry_authority",
        )
    )

    cost_failure = v220_hard_clean_capped_verifier_row()
    cost_failure["pretrade_cost_packet_status"] = "REFUSED"
    denied.append(
        ("broker_cost", cost_failure, "hard_clean_capped_cost_status:REFUSED")
    )

    source_failure = v220_hard_clean_capped_verifier_row()
    source_failure["source_completeness"] = 0.80
    denied.append(
        (
            "source_completeness",
            source_failure,
            "hard_clean_capped_source_completeness_below_floor",
        )
    )

    lifecycle_failure = v220_hard_clean_capped_verifier_row()
    lifecycle_failure["same_symbol_lifecycle_permitted"] = False
    denied.append(
        (
            "lifecycle",
            lifecycle_failure,
            "hard_clean_capped_same_symbol_lifecycle_permitted_false",
        )
    )

    cap_escape = v220_hard_clean_capped_verifier_row()
    cap_escape["predecision_stop_hazard_guard_risk_cap_applied"] = False
    denied.append(
        ("cap_escape", cap_escape, "hard_clean_capped_risk_cap_not_active")
    )

    full_risk_escape = v220_hard_clean_capped_verifier_row()
    full_risk_escape["package_risk_expression_full_risk_allowed"] = True
    denied.append(
        (
            "full_risk_escape",
            full_risk_escape,
            "hard_clean_capped_package_risk_expression_full_risk_allowed_not_false",
        )
    )

    for label, row, expected_reason in denied:
        reasons = verifier.v220_hard_clean_capped_reduced_risk_contract_reasons(row)
        assert expected_reason in reasons, label
        assert (
            verifier.scheduler_materialization_skip_is_soft_transfer(
                row,
                row["scheduler_materialization_skip_reason"],
            )
            is False
        ), label


def test_order_transfer_scan_consumes_v220_hard_clean_capped_contract(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    valid_path = tmp_path / "V220_VALID_ORDER.jsonl"
    invalid_path = tmp_path / "V220_INVALID_ORDER.jsonl"
    valid = {
        **v220_hard_clean_capped_verifier_row(),
        "package_replay_order_executable_transfer_status": "order_bound",
        "package_replay_order_executable_bound_order_id": "order-v220-valid",
        "simulated_order_id": "order-v220-valid",
        "order_status": "pending_accepted",
    }
    invalid = {
        **v220_hard_clean_capped_verifier_row(),
        "package_replay_order_executable_transfer_status": "order_bound",
        "package_replay_order_executable_bound_order_id": "order-v220-invalid",
        "simulated_order_id": "order-v220-invalid",
        "order_status": "pending_accepted",
    }
    invalid["replacement_reallocation_quality"] = {
        **invalid["replacement_reallocation_quality"],
        "raw_hard_gate_failures": ["unit_risk_geometry_hard_failure"],
    }
    write_jsonl(valid_path, [valid])
    write_jsonl(invalid_path, [invalid])

    valid_scan = verifier.scan_broad_order_executable_transfer_contract(
        {"order": valid_path}
    )
    invalid_scan = verifier.scan_broad_order_executable_transfer_contract(
        {"order": invalid_path}
    )

    assert not any(
        "hard_clean_capped_transfer" in key
        for key in valid_scan["bad_counts"]
    )
    assert invalid_scan["bad_counts"][
        "order:hard_clean_capped_transfer:"
        "hard_clean_capped_raw_hard_failures_present"
    ] == 1


def test_v220_contract_accepts_valid_signed_proposal_with_terminal_blocker() -> None:
    verifier = load_verifier()
    row = v220_hard_clean_capped_verifier_row()
    row.update(
        {
            "package_replay_order_executable_candidate_use_allowed": False,
            "package_replay_executable_candidate_use_allowed": False,
            "package_replay_order_executable_candidate_use_allowed_pre_finalization": (
                True
            ),
            "package_replay_order_executable_transfer_status": (
                "not_order_executable"
            ),
            "package_replay_order_executable_final_blocker_class": (
                "marketable_guard"
            ),
            "package_replay_order_executable_final_blocker_reason": (
                "package_marketable_limit_entry_guard_blocked"
            ),
        }
    )

    hard_reasons = verifier.v220_hard_clean_capped_reduced_risk_contract_reasons(
        row
    )
    signed_soft_reasons = (
        verifier.signed_soft_transfer_displacement_reliance_reasons(row)
    )

    assert "hard_clean_capped_order_route_not_executable" not in hard_reasons
    assert "hard_clean_capped_package_route_not_executable" not in hard_reasons
    assert "hard_clean_capped_final_blocker_not_soft_selection" not in hard_reasons
    assert "signed_soft_transfer_order_executable_not_true" not in (
        signed_soft_reasons
    )
    assert "signed_soft_transfer_package_executable_not_true" not in (
        signed_soft_reasons
    )


def test_finalized_authority_scan_rejects_provisional_marker_in_every_ledger(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    marker = verifier.PACKAGE_NEW_ENTRY_AUTHORITY_PROVISIONAL_MARKER
    rows = {
        "scorecard": {marker: True},
        "order": {
            "ultimate_candidate_package_open_reduced_risk_authority": {
                marker: True,
            }
        },
        "trade": {
            "scheduler_candidate_decision_inputs": [
                {"package_new_entry_authority": {marker: False}}
            ]
        },
        "missed": {
            "package_replay_order_executable_candidate_use_allowed": False,
            "historical_authority": {marker: False},
        },
    }
    paths: dict[str, Path] = {}
    for ledger, row in rows.items():
        paths[ledger] = tmp_path / f"{ledger}.jsonl"
        write_jsonl(paths[ledger], [row])

    scan = verifier.scan_broad_order_executable_transfer_contract(paths)

    for ledger in rows:
        assert scan["bad_counts"][
            f"{ledger}:provisional_package_new_entry_authority_marker_leak"
        ] == 1


def test_candidate_quality_scan_requires_exact_atomic_proof_for_finalized_authority(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    candidate_path = tmp_path / "prefix_CANDIDATE_LEDGER.jsonl"
    write_jsonl(
        candidate_path,
        [
            {
                "candidate_id": "provisional-good",
                "ultimate_package_source_bound_candidate_use_allowed": True,
                "scheduler_materialization_provisional_authority_finalized": True,
                "scheduler_materialization_provisional_authority_finalized_field": (
                    "ultimate_candidate_package_reduce_risk_authority"
                ),
                "ultimate_package_member_axis_evidence_class": (
                    "source_member_axis_overlap_not_additive_exact_execution_r"
                ),
                "ultimate_package_member_axis_match_status": (
                    "exact_current_source_member_axis_match"
                ),
                "scheduler_materialization_exact_member_axis_authority_finalization_allowed": (
                    True
                ),
                "scheduler_materialization_exact_member_axis_atomic_fillability_available": (
                    True
                ),
                "scheduler_materialization_exact_member_axis_execution_fill_probability": (
                    0.037322039
                ),
                "package_new_entry_authority_valid": True,
            },
            {
                "candidate_id": "provisional-bad",
                "ultimate_package_source_bound_candidate_use_allowed": True,
                "scheduler_materialization_provisional_authority_finalized": True,
                "ultimate_package_member_axis_evidence_class": (
                    "unmatched_candidate_carried_member_axis_diagnostic_only"
                ),
                "ultimate_package_member_axis_match_status": (
                    "no_actual_member_axis_match"
                ),
                "scheduler_materialization_exact_member_axis_authority_finalization_allowed": (
                    False
                ),
                "scheduler_materialization_exact_member_axis_atomic_fillability_available": (
                    False
                ),
                "scheduler_materialization_exact_member_axis_execution_fill_probability": (
                    None
                ),
                "package_new_entry_authority_valid": False,
                "ultimate_candidate_package_reduce_risk_authority": {
                    verifier.PACKAGE_NEW_ENTRY_AUTHORITY_PROVISIONAL_MARKER: True,
                },
            },
        ],
    )

    scan = verifier.scan_broad_candidate_quality_parity(candidate_path)
    bad = scan["candidate_index_bad_counts"]

    assert scan["provisional_authority_finalized_rows"] == 2
    assert bad[
        "provisional_authority_finalized_without_exact_member_axis_evidence"
    ] == 1
    assert bad[
        "provisional_authority_finalized_without_finalization_contract"
    ] == 1
    assert bad[
        "provisional_authority_finalized_without_atomic_fillability"
    ] == 1
    assert bad[
        "provisional_authority_finalized_without_positive_execution_fillability"
    ] == 1
    assert bad[
        "provisional_authority_finalized_without_valid_signed_authority"
    ] == 1
    assert bad[
        "provisional_authority_finalized_with_provisional_marker_leak"
    ] == 1


def test_finalized_executable_member_axis_rejects_root_only_and_mismatch(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    candidate_id = "finalized-member-axis"
    decision_time = "2026-05-13T08:30:00+00:00"
    order_base = {
        "candidate_id": candidate_id,
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "source_bound_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "candidate_instance_identity_status": "materialized",
        "selector_action": "reduce-risk",
        "scheduler_materialization_action_intent": "new_position",
        "package_replay_order_executable_candidate_use_allowed": True,
        "package_replay_order_executable_transfer_status": "order_bound",
        "package_replay_order_executable_bound_order_id": "order-member-axis",
        "simulated_order_id": "order-member-axis",
        "order_status": "pending_accepted",
        "ultimate_package_matched_member_axis_count": 1,
    }
    signed = {
        **order_base,
        **signed_package_new_entry_fields(
            candidate_id=candidate_id,
            decision_time_utc=decision_time,
            selector_action="reduce-risk",
            matched_member_axis_ids=("member_axis:fixture",),
        ),
        "ultimate_package_matched_member_axis_ids": ["member_axis:fixture"],
    }
    paths = {
        "signed": tmp_path / "signed.jsonl",
        "root_only": tmp_path / "root_only.jsonl",
        "root_mismatch": tmp_path / "root_mismatch.jsonl",
        "count_mismatch": tmp_path / "count_mismatch.jsonl",
    }
    write_jsonl(paths["signed"], [signed])
    write_jsonl(
        paths["root_only"],
        [
            {
                **order_base,
                "ultimate_package_matched_member_axis_ids": ["member_axis:fixture"],
            }
        ],
    )
    write_jsonl(
        paths["root_mismatch"],
        [
            {
                **signed,
                "ultimate_package_matched_member_axis_ids": [
                    "member_axis:wrong-root"
                ],
            }
        ],
    )
    write_jsonl(
        paths["count_mismatch"],
        [
            {
                **signed,
                "ultimate_package_matched_member_axis_count": 2,
            }
        ],
    )

    scans = {
        label: verifier.scan_broad_order_executable_transfer_contract(
            {"order": path}
        )
        for label, path in paths.items()
    }
    missing_payload_reason = (
        "order:finalized_executable_member_axis_identity:"
        "selected_immutable_authority_payload_missing_or_invalid_for_member_axis_identity"
    )

    assert not any(
        key.startswith("order:finalized_executable_member_axis_identity:")
        for key in scans["signed"]["bad_counts"]
    )
    assert scans["root_only"]["bad_counts"][missing_payload_reason] == 1
    assert scans["root_mismatch"]["bad_counts"][
        "order:finalized_executable_member_axis_identity:"
        "member_axis_id_aliases_mismatch_selected_signed_authority_payload"
    ] == 1
    assert scans["count_mismatch"]["bad_counts"][
        "order:finalized_executable_member_axis_identity:"
        "member_axis_count_exceeds_exact_stable_member_axis_id_count"
    ] == 1


def test_finalized_member_axis_identity_uses_only_root_and_selected_signed_payload() -> None:
    verifier = load_verifier()
    borrowed = {
        "ultimate_package_matched_member_axis_count": 1,
        "unrelated_diagnostic": {
            "matched_member_axis_ids": ["member_axis:diagnostic-only"],
        },
    }

    assert verifier.finalized_executable_member_axis_identity_reasons(borrowed) == [
        "selected_immutable_authority_payload_missing_or_invalid_for_member_axis_identity"
    ]

    candidate_id = "selected-signed-axis-payload"
    decision_time = "2026-05-13T08:30:00+00:00"
    selected_field = "ultimate_candidate_package_reduce_risk_authority"
    selected = resign_signed_package_new_entry_fields(
        signed_package_new_entry_fields(
            candidate_id=candidate_id,
            decision_time_utc=decision_time,
            selector_action="reduce-risk",
        ),
        matched_member_axis_ids=["member_axis:selected-signed"],
    )
    selected_row = {
        "candidate_id": candidate_id,
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "source_bound_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "selector_action": "reduce-risk",
        "scheduler_materialization_action_intent": "new_position",
        "ultimate_package_matched_member_axis_count": 1,
        "package_new_entry_authority_authority_field": selected_field,
        selected_field: selected,
        "unrelated_diagnostic": {
            "matched_member_axis_ids": ["member_axis:diagnostic-only"],
        },
    }

    assert verifier.finalized_executable_member_axis_identity_reasons(selected_row) == []

    mismatched_root = {
        **selected_row,
        "ultimate_package_matched_member_axis_ids": ["member_axis:wrong-root"],
    }
    assert (
        "member_axis_id_aliases_mismatch_selected_signed_authority_payload"
        in verifier.finalized_executable_member_axis_identity_reasons(mismatched_root)
    )


def test_order_transfer_scan_catches_every_blocked_status_with_executable_claim(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    rows = []
    for index, status in enumerate(
        sorted(verifier.ORDER_EXECUTABLE_TRANSFER_BLOCKED_STATUSES)
    ):
        rows.append(
            {
                "candidate_id": f"blocked-status-{index}",
                "package_replay_order_executable_transfer_status": status,
                "package_replay_order_executable_candidate_use_allowed": True,
                "package_replay_executable_candidate_use_allowed": True,
            }
        )
    order_path = tmp_path / "BLOCKED_STATUS_ORDER.jsonl"
    write_jsonl(order_path, rows)

    scan = verifier.scan_broad_order_executable_transfer_contract(
        {"order": order_path}
    )

    assert scan["bad_counts"]["order:blocked_status_executable_claim"] == len(rows)
    for status in verifier.ORDER_EXECUTABLE_TRANSFER_BLOCKED_STATUSES:
        key = (
            "order:blocked_status_executable_claim:"
            "package_replay_order_executable_transfer_status:"
            f"{status}"
        )
        assert scan["bad_counts"][key] == 1


def test_blocked_auxiliary_status_cannot_coexist_with_executable_permission() -> None:
    verifier = load_verifier()

    for status_field in verifier.ORDER_EXECUTABLE_BLOCKED_STATUS_FIELDS:
        if status_field == "package_replay_order_executable_transfer_status":
            continue
        row = {
            status_field: "diagnostic_only_blocked",
            "package_replay_order_executable_candidate_use_allowed": True,
        }
        reasons = verifier.blocked_status_executable_claim_reasons(row)
        assert reasons == [
            f"blocked_status_executable_claim:{status_field}:diagnostic_only_blocked",
            "blocked_status_executable_alias_claim:"
            f"{status_field}:diagnostic_only_blocked:"
            "package_replay_order_executable_candidate_use_allowed:True",
        ]


def test_terminally_blocked_order_attempt_id_is_not_an_executable_binding_claim() -> None:
    verifier = load_verifier()
    row = {
        "simulated_order_id": "attempt-terminally-blocked",
        "package_replay_order_executable_transfer_status": "not_order_executable",
        "package_replay_terminal_binding_status": "terminal_final_blocked",
        "package_replay_candidate_use_allowed": False,
        "package_replay_executable_candidate_use_allowed": False,
        "package_replay_order_executable_candidate_use_allowed": False,
        "replay_candidate_use_allowed_now": False,
        "ultimate_package_effective_executable_authority_allowed": False,
        "finalizer_primary_probe_executable_finalized": False,
        "risk_finalizer_executable_finalized": False,
        "executable_finalized": False,
    }

    assert verifier.blocked_status_executable_claim_reasons(row) == []

    row["risk_finalizer_executable_finalized"] = True
    reasons = verifier.blocked_status_executable_claim_reasons(row)
    assert (
        "blocked_status_executable_alias_claim:"
        "package_replay_order_executable_transfer_status:not_order_executable:"
        "risk_finalizer_executable_finalized:True"
    ) in reasons
    assert (
        "blocked_status_executable_alias_claim:"
        "package_replay_terminal_binding_status:terminal_final_blocked:"
        "risk_finalizer_executable_finalized:True"
    ) in reasons


def test_positive_reduced_risk_is_not_a_terminal_execution_blocker() -> None:
    verifier = load_verifier()
    row = {
        "package_replay_order_executable_transfer_status": (
            "unbound_without_final_blocker"
        ),
        "package_replay_order_executable_final_blocker_reason": (
            "approved_risk_pct_below_selected_cell_risk_pct"
        ),
        "selected_cell_risk_pct": 1.0,
        "scheduler_approved_risk_pct": 0.1,
    }

    assert verifier.blocked_status_executable_claim_reasons(row) == [
        "positive_reduced_risk_misclassified_as_terminal_blocker:"
        "package_replay_order_executable_final_blocker_reason:"
        "scheduler_approved_risk_pct:0.1"
    ]

    row["scheduler_approved_risk_pct"] = 0.0
    assert verifier.blocked_status_executable_claim_reasons(row) == []


def test_terminal_r_non_final_proof_is_not_an_execution_block() -> None:
    verifier = load_verifier()
    row = {
        "terminal_r_authority_status": (
            "terminal_r_source_gap_not_final_live_proof"
        ),
        "terminal_r_path_authority": (
            "terminal_r_source_gap_not_final_live_proof"
        ),
        "headline_result_authority_status": "not_headline_final_r_authority",
        "package_replay_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed": True,
        "package_replay_order_executable_candidate_use_allowed": True,
        "replay_candidate_use_allowed_now": True,
        "terminal_r_ordered_tick_final_live_authority": False,
        "ordered_tick_final_r_authority": False,
        "headline_result_authority": False,
        "final_r_authority": False,
        "live_broker_authority": False,
        "broker_mutation_enabled": False,
        "final_selection_claim": False,
    }

    assert verifier.blocked_status_executable_claim_reasons(row) == []
    assert verifier.terminal_r_final_live_claim_reasons(row) == []

    row["final_r_authority"] = True
    assert verifier.terminal_r_final_live_claim_reasons(row) == [
        "terminal_r_non_final_evidence_claims_final_live_authority:"
        "final_r_authority:"
        "headline_result_authority_status=not_headline_final_r_authority,"
        "terminal_r_authority_status=terminal_r_source_gap_not_final_live_proof,"
        "terminal_r_path_authority=terminal_r_source_gap_not_final_live_proof"
    ]


def test_final_blocked_unqualified_nested_scheduler_claim_remains_fatal() -> None:
    verifier = load_verifier()
    row = {
        "package_replay_order_executable_transfer_status": "final_blocked",
        "package_replay_candidate_use_allowed": False,
        "package_replay_executable_candidate_use_allowed": False,
        "package_replay_order_executable_candidate_use_allowed": False,
        "scheduler_candidate_decision_inputs": {
            "package_replay_candidate_use_allowed": True,
            "package_replay_executable_candidate_use_allowed": True,
            "package_replay_order_executable_candidate_use_allowed": True,
        },
    }

    reasons = verifier.blocked_status_executable_claim_reasons(row)

    assert reasons == [
        "blocked_status_executable_claim:"
        "package_replay_order_executable_transfer_status:final_blocked",
        "blocked_status_executable_alias_claim:"
        "package_replay_order_executable_transfer_status:final_blocked:"
        "scheduler_candidate_decision_inputs.package_replay_candidate_use_allowed:True",
        "blocked_status_executable_alias_claim:"
        "package_replay_order_executable_transfer_status:final_blocked:"
        "scheduler_candidate_decision_inputs.package_replay_executable_candidate_use_allowed:True",
        "blocked_status_executable_alias_claim:"
        "package_replay_order_executable_transfer_status:final_blocked:"
        "scheduler_candidate_decision_inputs.package_replay_order_executable_candidate_use_allowed:True",
    ]


def test_selected_package_executed_authority_scan_flags_limit_fillability_quality_alias() -> None:
    verifier = load_verifier()
    base = {
        "candidate_id": "candidate-limit-fill-alias",
        "order_status": "filled",
        "candidate_instance_identity_status": "materialized",
        "canonical_replay_candidate_instance_key": (
            "candidate-limit-fill-alias@@2026-05-13T08:00:00+00:00"
        ),
        "risk_finalizer_probe_instance_key": (
            "candidate-limit-fill-alias@@2026-05-13T08:00:00+00:00"
        ),
        "source_bound_replay_candidate_instance_key": (
            "candidate-limit-fill-alias@@2026-05-13T08:00:00+00:00"
        ),
        "candidate_decision_quality": {
            "expected_net_r": 0.75,
            "probability": 0.7,
            "fill_probability": 0.92,
            "source_completeness": 1.0,
        },
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "candidate_decision_inputs.expected_net_r",
            "probability": "candidate_decision_inputs.probability",
            "fill_probability": "predecision_limit_fillability.fill_probability",
            "source_completeness": "candidate_decision_inputs.source_completeness",
        },
        "candidate_decision_quality_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        "candidate_decision_quality_alias_status": "materialized",
        "expected_net_r": 0.75,
        "probability": 0.7,
        "fill_probability": 0.92,
        "source_completeness": 1.0,
        "source_boundary": "source_bound_asof_timewarp_decision_input",
        "pretrade_cost_packet_status": "PASSED",
        "pretrade_cost_refusal_reasons": [],
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "source_gap_cost_fallback_blocked": False,
        "candidate_cost_r_fallback_is_authority": False,
        "package_replay_executable_candidate_use_allowed": True,
        "selected_scheduler_package_replay_executable_candidate_use_allowed": True,
        "selected_package_candidate_status_join_status": "exact_candidate_window_join",
        "selected_package_candidate_status_join_key": (
            "candidate-limit-fill-alias@@2026-05-13T08:00:00+00:00"
        ),
        "role_disposition": "source_bound_candidate",
        "matched_sleeve_ids": ["sleeve-fixture"],
        "matched_sleeve_count": 1,
        "admission_sleeve_match_count": 1,
        "selector_action": "trade",
        "scheduler_materialization_action_intent": "new_position",
    }

    scan = verifier.scan_selected_package_executed_order_trade_authority(
        {"fixture": ([base], [{**base, "simulated_trade_id": "trade-limit-fill-alias"}])}
    )

    bad = scan["bad_counts"]
    assert (
        bad[
            "fixture.order:"
            "candidate_decision_quality_field_sources.fill_probability_limit_fillability_alias"
        ]
        == 2
    )
    assert (
        bad[
            "fixture.trade:"
            "candidate_decision_quality_field_sources.fill_probability_limit_fillability_alias"
        ]
        == 1
    )


def test_selected_package_executed_authority_scan_flags_raw_reject_promotion_without_contract() -> None:
    verifier = load_verifier()
    base = {
        "candidate_id": "candidate-raw-reject-promotion",
        "order_status": "filled",
        "decision_time_utc": "2026-05-13T08:00:00+00:00",
        "candidate_instance_identity_status": "materialized",
        "canonical_replay_candidate_instance_key": (
            "candidate-raw-reject-promotion@@2026-05-13T08:00:00+00:00"
        ),
        "risk_finalizer_probe_instance_key": (
            "candidate-raw-reject-promotion@@2026-05-13T08:00:00+00:00"
        ),
        "source_bound_replay_candidate_instance_key": (
            "candidate-raw-reject-promotion@@2026-05-13T08:00:00+00:00"
        ),
        "candidate_decision_quality_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        "source_boundary": "source_bound_asof_timewarp_decision_input",
        "pretrade_cost_packet_status": "PASSED",
        "pretrade_cost_refusal_reasons": [],
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "source_gap_cost_fallback_blocked": False,
        "candidate_cost_r_fallback_is_authority": False,
        "fill_realism_class": "passive_queue_confirmed",
        "package_replay_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed": True,
        "package_replay_order_executable_candidate_use_allowed": True,
        "package_replay_order_executable_candidate_use_allowed_reason": (
            "package_candidate_and_signed_new_entry_authority_executable"
        ),
        "package_replay_order_executable_authority_source": (
            "package_replay_executable_and_signed_new_entry_authority"
        ),
        "selected_scheduler_package_replay_executable_candidate_use_allowed": True,
        "selected_package_candidate_status_join_status": "exact_candidate_window_join",
        "selected_package_candidate_status_join_key": (
            "candidate-raw-reject-promotion@@2026-05-13T08:00:00+00:00"
        ),
        "role_disposition": "source_bound_candidate",
        "matched_sleeve_ids": ["sleeve-fixture"],
        "matched_sleeve_count": 1,
        "admission_sleeve_match_count": 1,
        "source_bound_package_candidate_use_allowed": True,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "package_replay_source_bound_candidate_use_allowed": True,
        "selector_action_origin": "reject",
        "scheduler_materialization_original_selector_action": "reject",
        "selector_action": "reject",
        "effective_selector_action": "open-reduced-risk",
        "materialized_package_new_entry_authority_selector_action": (
            "open-reduced-risk"
        ),
        "scheduler_materialization_action_intent": "new_position",
        "package_new_entry_authority_hash_sha256": "signed-fixture-hash",
        "package_new_entry_authority_valid": True,
        "raw_selector_reject_open_reduced_order_executable_promotion_allowed": False,
        "raw_selector_reject_open_reduced_order_executable_promotion_failures": [
            "predecision_limit_fillability_probability_below_floor"
        ],
        "raw_selector_reject_open_reduced_promotion_min_limit_fillability": 0.50,
        "raw_selector_reject_open_reduced_promotion_limit_fillability_probability": 0.42,
    }

    scan = verifier.scan_selected_package_executed_order_trade_authority(
        {"fixture": ([base], [{**base, "simulated_trade_id": "trade-raw-reject-promotion"}])}
    )

    bad = scan["bad_counts"]
    assert (
        bad[
            "fixture.order:"
            "raw_selector_reject_promoted_executable_without_promotion_contract"
        ]
        == 2
    )
    assert (
        bad[
            "fixture.trade:"
            "raw_selector_reject_promoted_executable_without_promotion_contract"
        ]
        == 1
    )
    assert (
        bad[
            "fixture.order:"
            "raw_selector_reject_promotion_limit_fillability_below_floor"
        ]
        == 2
    )


def test_selected_package_execution_disposition_scan_contracts() -> None:
    verifier = load_verifier()
    compact_rows = [
        {
            "candidate_id": "candidate-skip",
            "decision_time_utc": "2026-05-13T08:00:00+00:00",
            "canonical_replay_candidate_instance_key": (
                "candidate-skip@@2026-05-13T08:00:00+00:00"
            ),
            "selected_package_replay_row": True,
            "package_replay_executable_candidate_use_allowed": False,
        },
        {
            "candidate_id": "candidate-unfilled",
            "decision_time_utc": "2026-05-13T08:15:00+00:00",
            "canonical_replay_candidate_instance_key": (
                "candidate-unfilled@@2026-05-13T08:15:00+00:00"
            ),
            "selected_package_replay_row": True,
            "package_replay_executable_candidate_use_allowed": True,
            "scheduler_final_selected": True,
        },
        {
            "candidate_id": "candidate-not-selected",
            "decision_time_utc": "2026-05-13T08:30:00+00:00",
            "canonical_replay_candidate_instance_key": (
                "candidate-not-selected@@2026-05-13T08:30:00+00:00"
            ),
            "selected_package_replay_row": True,
            "package_replay_executable_candidate_use_allowed": True,
            "selected_candidate_ids": [],
        },
        {
            "candidate_id": "candidate-soft-transfer",
            "decision_time_utc": "2026-05-13T08:40:00+00:00",
            "canonical_replay_candidate_instance_key": (
                "candidate-soft-transfer@@2026-05-13T08:40:00+00:00"
            ),
            "selected_package_replay_row": True,
            "package_replay_executable_candidate_use_allowed": True,
            "scheduler_materialization_skip_reason": (
                "candidate_generated_not_scheduler_selected"
            ),
            "scheduler_terminal_vs_soft_guard": {
                "soft_guard_vetoes": ["not_scheduler_selected"],
                "terminal_vetoes": [],
                "pool_eligible": True,
                "pool_status": "eligible",
            },
            "reallocation_soft_guard_vetoes": ["not_scheduler_selected"],
            "reallocation_soft_guard_pool_eligible": True,
            "reallocation_soft_guard_pool_status": "eligible",
            "terminal_vetoes": [],
            "selected_candidate_ids": [],
        },
        {
            "candidate_id": "candidate-filtered-terminal",
            "decision_time_utc": "2026-05-13T08:45:00+00:00",
            "canonical_replay_candidate_instance_key": (
                "candidate-filtered-terminal@@2026-05-13T08:45:00+00:00"
            ),
            "selected_package_replay_row": True,
            "package_replay_executable_candidate_use_allowed": True,
            "scheduler_final_selected": True,
        },
    ]
    disposition_rows = [
        {
            "candidate_id": "candidate-skip",
            "canonical_replay_candidate_instance_key": (
                "candidate-skip@@2026-05-13T08:00:00+00:00"
            ),
            "execution_disposition": "non_executable_scheduler_skip",
            "execution_disposition_reason": (
                "selector_reduce_risk_not_new_entry_authority"
            ),
            "bound_order_rows": 0,
            "bound_oracle_rows": 0,
            "bound_trade_rows": 0,
        },
        {
            "candidate_id": "candidate-unfilled",
            "canonical_replay_candidate_instance_key": (
                "candidate-unfilled@@2026-05-13T08:15:00+00:00"
            ),
            "execution_disposition": "ordered_unfilled_no_trade",
            "execution_disposition_reason": (
                "order_and_oracle_present_without_filled_trade"
            ),
            "bound_order_rows": 1,
            "bound_oracle_rows": 1,
            "bound_trade_rows": 0,
        },
        {
            "candidate_id": "candidate-not-selected",
            "canonical_replay_candidate_instance_key": (
                "candidate-not-selected@@2026-05-13T08:30:00+00:00"
            ),
            "execution_disposition": (
                "executable_package_candidate_not_scheduler_selected"
            ),
            "execution_disposition_reason": (
                "package_executable_candidate_not_scheduler_final_selected"
            ),
            "bound_order_rows": 0,
            "bound_oracle_rows": 0,
            "bound_trade_rows": 0,
        },
        {
            "candidate_id": "candidate-filtered-terminal",
            "canonical_replay_candidate_instance_key": (
                "candidate-filtered-terminal@@2026-05-13T08:45:00+00:00"
            ),
            "execution_disposition": (
                "filtered_non_executable_terminal_blocked_no_trade"
            ),
            "execution_disposition_reason": (
                "source_required_fail_closed_lifecycle_source_gap_diagnostic_only"
            ),
            "bound_order_rows": 0,
            "bound_oracle_rows": 1,
            "bound_trade_rows": 0,
            "bound_filtered_non_executable_order_rows": 1,
            "bound_filtered_non_executable_trade_rows": 0,
        },
        {
            "candidate_id": "candidate-soft-transfer",
            "canonical_replay_candidate_instance_key": (
                "candidate-soft-transfer@@2026-05-13T08:40:00+00:00"
            ),
            "execution_disposition": (
                "executable_package_candidate_not_scheduler_selected"
            ),
            "execution_disposition_reason": (
                "package_executable_candidate_not_scheduler_final_selected"
            ),
            "package_replay_executable_candidate_use_allowed": True,
            "scheduler_materialization_skip_reason": (
                "candidate_generated_not_scheduler_selected"
            ),
            "scheduler_terminal_vs_soft_guard": {
                "soft_guard_vetoes": ["not_scheduler_selected"],
                "terminal_vetoes": [],
                "pool_eligible": True,
                "pool_status": "eligible",
            },
            "reallocation_soft_guard_vetoes": ["not_scheduler_selected"],
            "reallocation_soft_guard_pool_eligible": True,
            "reallocation_soft_guard_pool_status": "eligible",
            "terminal_vetoes": [],
            "bound_order_rows": 0,
            "bound_oracle_rows": 0,
            "bound_trade_rows": 0,
        },
    ]

    scan = verifier.scan_selected_package_execution_dispositions(
        compact_rows=compact_rows,
        disposition_rows=disposition_rows,
    )

    assert scan["bad_counts"] == {}
    assert scan["row_counts"]["selected_compact_rows"] == 5
    assert scan["row_counts"]["disposition:ordered_unfilled_no_trade"] == 1
    assert (
        scan["row_counts"][
            "disposition:filtered_non_executable_terminal_blocked_no_trade"
        ]
        == 1
    )
    assert (
        scan["row_counts"][
            "disposition:executable_package_candidate_not_scheduler_selected"
        ]
        == 2
    )


def test_selected_package_execution_disposition_scan_fails_missing_and_invalid() -> None:
    verifier = load_verifier()
    compact_rows = [
        {
            "candidate_id": "candidate-missing",
            "decision_time_utc": "2026-05-13T08:00:00+00:00",
            "canonical_replay_candidate_instance_key": (
                "candidate-missing@@2026-05-13T08:00:00+00:00"
            ),
            "selected_package_replay_row": True,
            "package_replay_executable_candidate_use_allowed": True,
        },
        {
            "candidate_id": "candidate-invalid",
            "decision_time_utc": "2026-05-13T08:15:00+00:00",
            "canonical_replay_candidate_instance_key": (
                "candidate-invalid@@2026-05-13T08:15:00+00:00"
            ),
            "selected_package_replay_row": True,
            "package_replay_executable_candidate_use_allowed": True,
        },
        {
            "candidate_id": "candidate-final-missing",
            "decision_time_utc": "2026-05-13T08:30:00+00:00",
            "canonical_replay_candidate_instance_key": (
                "candidate-final-missing@@2026-05-13T08:30:00+00:00"
            ),
            "selected_package_replay_row": True,
            "package_replay_executable_candidate_use_allowed": True,
            "scheduler_final_selected": True,
        },
        {
            "candidate_id": "candidate-filled-no-trade",
            "decision_time_utc": "2026-05-13T08:45:00+00:00",
            "canonical_replay_candidate_instance_key": (
                "candidate-filled-no-trade@@2026-05-13T08:45:00+00:00"
            ),
            "selected_package_replay_row": True,
            "package_replay_executable_candidate_use_allowed": True,
            "scheduler_final_selected": True,
        },
        {
            "candidate_id": "candidate-soft-transfer-bad-label",
            "decision_time_utc": "2026-05-13T09:00:00+00:00",
            "canonical_replay_candidate_instance_key": (
                "candidate-soft-transfer-bad-label@@2026-05-13T09:00:00+00:00"
            ),
            "selected_package_replay_row": True,
            "package_replay_executable_candidate_use_allowed": True,
            "scheduler_materialization_skip_reason": (
                "candidate_generated_not_scheduler_selected"
            ),
            "scheduler_terminal_vs_soft_guard": {
                "soft_guard_vetoes": ["not_scheduler_selected"],
                "terminal_vetoes": [],
                "pool_eligible": True,
                "pool_status": "eligible",
            },
            "reallocation_soft_guard_vetoes": ["not_scheduler_selected"],
            "reallocation_soft_guard_pool_eligible": True,
            "reallocation_soft_guard_pool_status": "eligible",
            "terminal_vetoes": [],
            "selected_candidate_ids": [],
        },
    ]
    disposition_rows = [
        {
            "candidate_id": "candidate-invalid",
            "canonical_replay_candidate_instance_key": (
                "candidate-invalid@@2026-05-13T08:15:00+00:00"
            ),
            "execution_disposition": "ordered_unfilled_no_trade",
            "execution_disposition_reason": (
                "order_and_oracle_present_without_filled_trade"
            ),
            "bound_order_rows": 1,
            "bound_oracle_rows": 1,
            "bound_trade_rows": 1,
            "bound_filled_order_rows": 1,
            "bound_filled_oracle_rows": 1,
        },
        {
            "candidate_id": "candidate-final-missing",
            "canonical_replay_candidate_instance_key": (
                "candidate-final-missing@@2026-05-13T08:30:00+00:00"
            ),
            "execution_disposition": (
                "executable_scheduler_final_selected_missing_order_binding"
            ),
            "execution_disposition_reason": (
                "scheduler_final_selected_candidate_has_no_order_or_oracle_trade_binding"
            ),
            "bound_order_rows": 0,
            "bound_oracle_rows": 0,
            "bound_trade_rows": 0,
        },
        {
            "candidate_id": "candidate-filled-no-trade",
            "canonical_replay_candidate_instance_key": (
                "candidate-filled-no-trade@@2026-05-13T08:45:00+00:00"
            ),
            "execution_disposition": "filled_order_or_oracle_without_trade_row",
            "execution_disposition_reason": (
                "filled_order_or_oracle_present_without_filled_trade"
            ),
            "bound_order_rows": 1,
            "bound_oracle_rows": 1,
            "bound_trade_rows": 0,
            "bound_filled_order_rows": 1,
            "bound_filled_oracle_rows": 1,
        },
        {
            "candidate_id": "candidate-soft-transfer-bad-label",
            "canonical_replay_candidate_instance_key": (
                "candidate-soft-transfer-bad-label@@2026-05-13T09:00:00+00:00"
            ),
            "execution_disposition": "non_executable_scheduler_skip",
            "execution_disposition_reason": (
                "candidate_generated_not_scheduler_selected"
            ),
            "package_replay_executable_candidate_use_allowed": True,
            "scheduler_materialization_skip_reason": (
                "candidate_generated_not_scheduler_selected"
            ),
            "scheduler_terminal_vs_soft_guard": {
                "soft_guard_vetoes": ["not_scheduler_selected"],
                "terminal_vetoes": [],
                "pool_eligible": True,
                "pool_status": "eligible",
            },
            "reallocation_soft_guard_vetoes": ["not_scheduler_selected"],
            "reallocation_soft_guard_pool_eligible": True,
            "reallocation_soft_guard_pool_status": "eligible",
            "terminal_vetoes": [],
            "bound_order_rows": 0,
            "bound_oracle_rows": 0,
            "bound_trade_rows": 0,
        },
    ]

    scan = verifier.scan_selected_package_execution_dispositions(
        compact_rows=compact_rows,
        disposition_rows=disposition_rows,
    )

    assert scan["bad_counts"][
        "selected_compact_missing_execution_disposition"
    ] == 1
    assert scan["bad_counts"]["ordered_unfilled_disposition_has_trade_row"] == 1
    assert (
        scan["bad_counts"][
            "ordered_unfilled_disposition_has_filled_order_or_oracle"
        ]
        == 1
    )
    assert scan["bad_counts"]["filled_order_or_oracle_without_trade_row"] == 1
    assert (
        scan["bad_counts"][
            "executable_scheduler_final_selected_missing_order_binding"
        ]
        == 1
    )
    assert (
        scan["bad_counts"][
            "soft_transfer_executable_row_labeled_non_executable_scheduler_skip"
        ]
        == 1
    )


def test_selected_package_execution_disposition_scan_blocks_cost_refused_execution() -> None:
    verifier = load_verifier()
    compact_rows = [
        {
            "candidate_id": "candidate-refused-cost",
            "decision_time_utc": "2026-05-13T08:00:00+00:00",
            "canonical_replay_candidate_instance_key": (
                "candidate-refused-cost@@2026-05-13T08:00:00+00:00"
            ),
            "selected_package_replay_row": True,
            "package_replay_executable_candidate_use_allowed": True,
            "scheduler_final_selected": True,
            "pretrade_cost_packet_status": "REFUSED",
            "cost_source_gap_status": "source_bound_cost_authority_present",
            "cost_authority": "broker_calibrated_replay_cost",
            "pretrade_cost_refusal_reasons": [
                "symbol_specific_untradeable_cost_floor"
            ],
        }
    ]
    disposition_rows = [
        {
            "candidate_id": "candidate-refused-cost",
            "canonical_replay_candidate_instance_key": (
                "candidate-refused-cost@@2026-05-13T08:00:00+00:00"
            ),
            "execution_disposition": "bound_filled_trade",
            "execution_disposition_reason": "fixture_bad_execution",
            "bound_order_rows": 1,
            "bound_filled_order_rows": 1,
            "bound_oracle_rows": 1,
            "bound_filled_oracle_rows": 1,
            "bound_trade_rows": 1,
        }
    ]

    scan = verifier.scan_selected_package_execution_dispositions(
        compact_rows=compact_rows,
        disposition_rows=disposition_rows,
    )

    bad = scan["bad_counts"]
    assert bad["broker_cost_refused_or_source_gap_compact_marked_executable"] == 1
    assert bad["broker_cost_refused_or_source_gap_compact_scheduler_selected"] == 1
    assert bad["broker_cost_refused_or_source_gap_compact_bound_to_execution"] == 1
    assert (
        scan["row_counts"][
            "selected_compact_cost_non_executable:broker_cost_status_REFUSED"
        ]
        == 1
    )


def test_selected_package_execution_disposition_scan_blocks_cost_source_gap_execution() -> None:
    verifier = load_verifier()
    compact_rows = [
        {
            "candidate_id": "candidate-source-gap-cost",
            "decision_time_utc": "2026-05-13T08:00:00+00:00",
            "canonical_replay_candidate_instance_key": (
                "candidate-source-gap-cost@@2026-05-13T08:00:00+00:00"
            ),
            "selected_package_replay_row": True,
            "package_replay_executable_candidate_use_allowed": True,
            "scheduler_final_selected": True,
            "pretrade_cost_packet_status": "PASSED",
            "cost_source_gap_status": "mt5_tick_spread_floor_missing",
            "cost_authority": "broker_calibrated_replay_cost",
            "execution_disposition_reason": (
                "cost_source_gap:mt5_tick_spread_floor_missing"
            ),
        }
    ]
    disposition_rows = [
        {
            "candidate_id": "candidate-source-gap-cost",
            "canonical_replay_candidate_instance_key": (
                "candidate-source-gap-cost@@2026-05-13T08:00:00+00:00"
            ),
            "execution_disposition": "bound_filled_trade",
            "execution_disposition_reason": "fixture_bad_execution",
            "bound_order_rows": 1,
            "bound_filled_order_rows": 1,
            "bound_oracle_rows": 1,
            "bound_filled_oracle_rows": 1,
            "bound_trade_rows": 1,
        }
    ]

    scan = verifier.scan_selected_package_execution_dispositions(
        compact_rows=compact_rows,
        disposition_rows=disposition_rows,
    )

    bad = scan["bad_counts"]
    assert bad["broker_cost_refused_or_source_gap_compact_marked_executable"] == 1
    assert bad["broker_cost_refused_or_source_gap_compact_scheduler_selected"] == 1
    assert bad["broker_cost_refused_or_source_gap_compact_bound_to_execution"] == 1
    assert (
        scan["row_counts"][
            "selected_compact_cost_non_executable:"
            "cost_source_gap:mt5_tick_spread_floor_missing"
        ]
        == 1
    )


def test_execution_manager_lifecycle_replay_scan_requires_truth_for_demoted_source_required(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    order_path = tmp_path / "orders.jsonl"
    trade_path = tmp_path / "trades.jsonl"
    stale_reason = "same_symbol_lifecycle_v4_not_permitted:source_required_fail_closed"
    write_jsonl(
        order_path,
        [
            {
                "candidate_id": "candidate-stale",
                "simulated_order_id": "order-stale",
                "execution_manager_source_required_package_risk_lifecycle_reconcile_applied": True,
                "execution_manager_replay_admission_status": (
                    "execution_manager_replay_block_applied"
                ),
                "execution_manager_replay_blocking_reasons": [stale_reason],
            },
            {
                "candidate_id": "candidate-demoted",
                "simulated_order_id": "order-demoted",
                "order_status": "pending_accepted",
                "execution_manager_source_required_package_risk_lifecycle_reconcile_applied": True,
                "execution_manager_replay_admission_status": (
                    "execution_manager_live_promotion_blockers_recorded_replay_allowed"
                ),
                "execution_manager_replay_blocking_reasons": [],
                "execution_manager_replay_demoted_live_promotion_blocker_reasons": [
                    stale_reason
                ],
                "execution_manager_live_promotion_blocker_reasons": [stale_reason],
            },
        ],
    )
    write_jsonl(trade_path, [])

    scan = verifier.scan_execution_manager_lifecycle_replay_parity(
        {"order": order_path, "trade": trade_path}
    )

    assert scan["bad_counts"][
        "order:source_required_lifecycle_demoted_without_broker_truth"
    ] == 1
    assert scan["bad_counts"][
        "order:source_required_lifecycle_gap_has_executable_order_without_broker_truth"
    ] == 1
    assert scan["row_counts"]["order_source_required_reconciled_rows"] == 2
    assert scan["row_counts"]["order_source_required_replay_blocked_rows"] == 1
    assert scan["row_counts"]["order_source_required_replay_demoted_rows"] == 1
    assert scan["sample_bad"][0]["candidate_id"] == "candidate-demoted"


def test_execution_manager_lifecycle_replay_scan_accepts_truth_bound_demoted_live_blocker(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    order_path = tmp_path / "orders.jsonl"
    trade_path = tmp_path / "trades.jsonl"
    stale_reason = "same_symbol_lifecycle_v4_not_permitted:source_required_fail_closed"
    write_jsonl(
        order_path,
        [
            {
                "candidate_id": "candidate-demoted",
                "simulated_order_id": "order-demoted",
                "order_status": "pending_accepted",
                "source_required_broker_lifecycle_truth_satisfied": True,
                "execution_manager_source_required_package_risk_lifecycle_reconcile_applied": True,
                "execution_manager_replay_admission_status": (
                    "execution_manager_live_promotion_blockers_recorded_replay_allowed"
                ),
                "execution_manager_replay_blocking_reasons": [],
                "execution_manager_replay_demoted_live_promotion_blocker_reasons": [
                    stale_reason
                ],
                "execution_manager_live_promotion_blocker_reasons": [stale_reason],
            }
        ],
    )
    write_jsonl(
        trade_path,
        [
            {
                "candidate_id": "candidate-trade-demoted",
                "simulated_trade_id": "trade-demoted",
                "source_required_broker_lifecycle_truth_satisfied": True,
                "execution_manager_source_required_package_risk_lifecycle_reconcile_applied": True,
                "execution_manager_replay_admission_status": (
                    "execution_manager_live_promotion_blockers_recorded_replay_allowed"
                ),
                "execution_manager_replay_blocking_reasons": [],
                "execution_manager_replay_demoted_live_promotion_blocker_reasons": [
                    stale_reason
                ],
                "execution_manager_live_promotion_blocker_reasons": [stale_reason],
            }
        ],
    )

    scan = verifier.scan_execution_manager_lifecycle_replay_parity(
        {"order": order_path, "trade": trade_path}
    )

    assert scan["bad_counts"] == {}
    assert scan["row_counts"]["order_source_required_replay_demoted_rows"] == 1
    assert scan["row_counts"]["trade_source_required_replay_demoted_rows"] == 1


def test_package_lifecycle_root_flat_truth_scan_rejects_non_applicable_flat_denial(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    order_path = tmp_path / "orders.jsonl"
    missed_path = tmp_path / "missed.jsonl"
    write_jsonl(
        order_path,
        [
            {
                "candidate_id": "candidate-new-position",
                "symbol": "XAUUSD",
                "side": "LONG",
                "package_lifecycle_root_authority": {
                    "applies": False,
                    "allowed": False,
                    "failures": [],
                    "root_action": "new_position",
                },
                "package_lifecycle_root_authority_allowed": False,
            }
        ],
    )
    write_jsonl(
        missed_path,
        [
            {
                "candidate_id": "candidate-missed-new-position",
                "symbol": "XAUUSD",
                "side": "LONG",
                "package_lifecycle_root_authority": {
                    "applies": False,
                    "allowed": False,
                    "failures": [],
                    "root_action": "new_position",
                },
                "package_lifecycle_root_authority_allowed": False,
            }
        ],
    )

    scan = verifier.scan_package_lifecycle_root_flat_truth(
        {"order": order_path, "missed": missed_path}
    )

    assert scan["bad_counts"][
        "order:non_applicable_lifecycle_root_flattened_as_denied"
    ] == 1
    assert scan["bad_counts"][
        "missed:non_applicable_lifecycle_root_flattened_as_denied"
    ] == 1
    assert scan["row_counts"]["order_not_applicable_root_rows"] == 1
    assert scan["row_counts"]["missed_not_applicable_root_rows"] == 1
    assert scan["sample_bad"][0]["candidate_id"] == "candidate-new-position"


def test_package_lifecycle_root_flat_truth_scan_accepts_applicable_denial(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    order_path = tmp_path / "orders.jsonl"
    write_jsonl(
        order_path,
        [
            {
                "candidate_id": "candidate-scale-in-blocked",
                "symbol": "XAUUSD",
                "side": "LONG",
                "package_lifecycle_root_authority": {
                    "applies": True,
                    "allowed": False,
                    "failures": ["same_direction_scale_in_authority_not_allowed"],
                    "root_action": "same_direction_scale_in",
                },
                "package_lifecycle_root_authority_allowed": False,
            }
        ],
    )

    scan = verifier.scan_package_lifecycle_root_flat_truth({"order": order_path})

    assert scan["bad_counts"] == {}
    assert scan["row_counts"].get("order_not_applicable_root_rows", 0) == 0


def test_candidate_context_envelope_scan_requires_package_context_mapping(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    scorecard_path = tmp_path / "scorecard.jsonl"
    write_jsonl(
        scorecard_path,
        [
            {
                "candidate_id": "candidate-with-context",
                "canonical_replay_candidate_instance_key": (
                    "candidate-with-context@@2026-05-13T08:00:00+00:00"
                ),
                "selected_package_replay_row": True,
                "package_replay_executable_candidate_use_allowed": True,
                "same_symbol_replay_exposure_context": {
                    "same_side_pending_ids": [],
                    "opposite_pending_ids": [],
                    "source_boundary": (
                        "predecision_same_symbol_replay_exposure_context"
                    ),
                },
            },
            {
                "candidate_id": "candidate-missing-context",
                "canonical_replay_candidate_instance_key": (
                    "candidate-missing-context@@2026-05-13T08:15:00+00:00"
                ),
                "selected_package_replay_row": True,
                "package_replay_executable_candidate_use_allowed": True,
            },
        ],
    )

    scan = verifier.scan_candidate_context_envelope_presence(
        {"scorecard": scorecard_path}
    )

    assert scan["row_counts"]["scorecard_context_required_rows"] == 2
    assert scan["bad_counts"][
        "scorecard:same_symbol_replay_exposure_context_missing"
    ] == 1
    assert scan["sample_bad"][0]["candidate_id"] == "candidate-missing-context"


def test_candidate_context_scan_ignores_zero_trade_false_flag_scorecard(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    scorecard_path = tmp_path / "scorecard.jsonl"
    write_jsonl(
        scorecard_path,
        [
            {
                "candidate_set_id": "timewarp_candidate_set:zero-trade",
                "selected_candidate_id": None,
                "selected_candidate_ids": [],
                "package_replay_candidate_use_allowed": False,
                "package_replay_executable_candidate_use_allowed": False,
                "package_replay_order_executable_candidate_use_allowed": False,
            },
            {
                "selected_candidate_id": "selected-missing-context",
                "selected_candidate_ids": ["selected-missing-context"],
                "package_replay_candidate_use_allowed": False,
                "package_replay_executable_candidate_use_allowed": False,
                "package_replay_order_executable_candidate_use_allowed": False,
            },
        ],
    )

    scan = verifier.scan_candidate_context_envelope_presence(
        {"scorecard": scorecard_path}
    )

    assert scan["row_counts"]["scorecard_rows"] == 2
    assert scan["row_counts"]["scorecard_context_required_rows"] == 1
    assert scan["bad_counts"] == {
        "scorecard:same_symbol_replay_exposure_context_missing": 1
    }
    assert scan["sample_bad"][0]["candidate_id"] == "selected-missing-context"


def test_adaptive_broad_axis_disabled_scan_rejects_exact_disabled_axes(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    missed_path = tmp_path / "missed.jsonl"
    write_jsonl(
        missed_path,
        [
            {
                "candidate_id": "candidate-disabled-origin-side",
                "adaptive_replay_memory_guard_matched_axis_id": (
                    "origin_side:fixture"
                ),
                "adaptive_replay_memory_guard_allow_origin_side_axis": False,
            },
            {
                "candidate_id": "candidate-disabled-session-origin-side",
                "adaptive_replay_memory_guard_matched_axis_id": (
                    "session_origin_side:fixture"
                ),
                "adaptive_replay_memory_guard_allow_session_origin_side_axis": False,
            },
            {
                "candidate_id": "candidate-symbol-origin-side-ok",
                "adaptive_replay_memory_guard_matched_axis_id": (
                    "symbol_origin_side:fixture"
                ),
                "adaptive_replay_memory_guard_allow_origin_side_axis": False,
            },
        ],
    )

    scan = verifier.scan_adaptive_broad_axis_disabled({"missed": missed_path})

    assert scan["row_counts"]["missed_adaptive_axis_rows"] == 3
    assert scan["bad_counts"]["missed:origin_side_axis_disabled"] == 1
    assert scan["bad_counts"]["missed:session_origin_side_axis_disabled"] == 1
    assert len(scan["sample_bad"]) == 2


def test_broad_candidate_quality_scan_requires_field_sources_and_alias_status(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    candidate_path = tmp_path / "candidates.jsonl"
    write_jsonl(
        candidate_path,
        [
            {
                "candidate_id": "candidate-good",
                "decision_time_utc": "2026-04-21T08:00:00+00:00",
                "symbol": "XAUUSD",
                "canonical_replay_candidate_instance_key": (
                    "candidate-good@@2026-04-21T08:00:00+00:00"
                ),
                "risk_finalizer_probe_instance_key": (
                    "candidate-good@@2026-04-21T08:00:00+00:00"
                ),
                "source_bound_replay_candidate_instance_key": (
                    "candidate-good@@2026-04-21T08:00:00+00:00"
                ),
                "candidate_instance_identity_status": "materialized",
                "risk_authority": "runtime_risk_authority_packet_v1",
                "risk_authority_status": "pre_scheduler_risk_authority_materialized",
                "risk_authority_packet_hash_sha256": "hash-good",
                "risk_config_source": "fixture",
                "risk_per_trade_pct": 0.25,
                "scheduler_approved_risk_pct": 0.25,
                "ultimate_package_source_bound_candidate_use_allowed": True,
                "probability": 0.7,
                "candidate_probability": 0.7,
                "confidence": 0.64,
                "ev_r": 0.8,
                "candidate_ev_r": 0.8,
                "expected_cost_r": 0.05,
                "cost_r": 0.05,
                "expected_net_r": 0.75,
                "candidate_expected_net_r": 0.75,
                "fill_probability": 0.8,
                "source_completeness": 1.0,
                "source_completeness_status": "complete",
                "candidate_decision_quality_alias_status": "materialized",
                "candidate_decision_quality_source_boundary": (
                    "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
                ),
                "candidate_decision_quality_field_sources": {
                    "probability": "candidate_probability",
                    "expected_net_r": "candidate_expected_net_r",
                    "fill_probability": "fill_probability",
                    "source_completeness": "source_completeness",
                },
            },
            {
                "candidate_id": "candidate-selected-policy-missing-nested",
                "decision_time_utc": "2026-04-21T08:00:00+00:00",
                "symbol": "XAUUSD",
                "canonical_replay_candidate_instance_key": (
                    "candidate-selected-policy-missing-nested@@2026-04-21T08:00:00+00:00"
                ),
                "risk_finalizer_probe_instance_key": (
                    "candidate-selected-policy-missing-nested@@2026-04-21T08:00:00+00:00"
                ),
                "source_bound_replay_candidate_instance_key": (
                    "candidate-selected-policy-missing-nested@@2026-04-21T08:00:00+00:00"
                ),
                "candidate_instance_identity_status": "materialized",
                "risk_authority": "runtime_risk_authority_packet_v1",
                "risk_authority_status": "pre_scheduler_risk_authority_materialized",
                "risk_authority_packet_hash_sha256": "hash-selected-policy-missing-nested",
                "risk_config_source": "fixture",
                "risk_per_trade_pct": 0.25,
                "selected_cell_risk_pct": 0.25,
                "scheduler_approved_risk_pct": 0.25,
                "ultimate_package_source_bound_candidate_use_allowed": True,
                "probability": 0.7,
                "candidate_probability": 0.7,
                "ev_r": 0.8,
                "candidate_ev_r": 0.8,
                "expected_cost_r": 0.05,
                "cost_r": 0.05,
                "expected_net_r": 0.75,
                "candidate_expected_net_r": 0.75,
                "fill_probability": 0.8,
                "source_completeness": 1.0,
                "source_completeness_status": "complete",
                "candidate_decision_quality_alias_status": "materialized",
                "candidate_decision_quality_source_boundary": (
                    "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
                ),
                "source_boundary": (
                    "predecision_package_quality_and_broker_cost_no_outcome_fields"
                ),
                "candidate_decision_quality_field_sources": {
                    "probability": "candidate_probability",
                    "expected_net_r": "candidate_expected_net_r",
                    "fill_probability": "fill_probability",
                    "source_completeness": "source_completeness",
                },
                "selected_policy_for_expected_net_r": "momentum_exhaustion",
                "selected_policy_expected_net_r": 0.75,
                "selected_policy_probability": 0.7,
                "selected_policy_source_completeness": 1.0,
                "selected_policy_expected_net_calibration_status": (
                    "selected_policy_proxy_quality_partial"
                ),
                "selected_policy_expected_net_calibration_source": "unit_fixture",
                "selected_policy_expected_net_calibration_source_boundary": (
                    "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
                ),
            },
            {
                "candidate_id": "candidate-selected-policy-incomplete-nested",
                "decision_time_utc": "2026-04-21T08:00:00+00:00",
                "symbol": "XAUUSD",
                "canonical_replay_candidate_instance_key": (
                    "candidate-selected-policy-incomplete-nested@@2026-04-21T08:00:00+00:00"
                ),
                "risk_finalizer_probe_instance_key": (
                    "candidate-selected-policy-incomplete-nested@@2026-04-21T08:00:00+00:00"
                ),
                "source_bound_replay_candidate_instance_key": (
                    "candidate-selected-policy-incomplete-nested@@2026-04-21T08:00:00+00:00"
                ),
                "candidate_instance_identity_status": "materialized",
                "risk_authority": "runtime_risk_authority_packet_v1",
                "risk_authority_status": "pre_scheduler_risk_authority_materialized",
                "risk_authority_packet_hash_sha256": "hash-selected-policy-incomplete-nested",
                "risk_config_source": "fixture",
                "risk_per_trade_pct": 0.25,
                "selected_cell_risk_pct": 0.25,
                "scheduler_approved_risk_pct": 0.25,
                "ultimate_package_source_bound_candidate_use_allowed": True,
                "probability": 0.7,
                "candidate_probability": 0.7,
                "ev_r": 0.8,
                "candidate_ev_r": 0.8,
                "expected_cost_r": 0.05,
                "cost_r": 0.05,
                "expected_net_r": 0.75,
                "candidate_expected_net_r": 0.75,
                "fill_probability": 0.8,
                "source_completeness": 1.0,
                "source_completeness_status": "complete",
                "candidate_decision_quality_alias_status": "materialized",
                "candidate_decision_quality_source_boundary": (
                    "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
                ),
                "source_boundary": (
                    "predecision_package_quality_and_broker_cost_no_outcome_fields"
                ),
                "candidate_decision_quality_field_sources": {
                    "probability": "candidate_probability",
                    "expected_net_r": "candidate_expected_net_r",
                    "fill_probability": "fill_probability",
                    "source_completeness": "source_completeness",
                },
                "selected_policy_for_expected_net_r": "momentum_exhaustion",
                "selected_policy_probability": 0.7,
                "candidate_decision_quality": {
                    "selected_policy_for_expected_net_r": "momentum_exhaustion",
                },
            },
            {
                "candidate_id": "candidate-bad",
                "decision_time_utc": "2026-04-21T08:00:00+00:00",
                "symbol": "XAUUSD",
                "ultimate_package_source_bound_candidate_use_allowed": True,
                "probability": 0.7,
                "candidate_probability": 0.7,
                "ev_r": 0.8,
                "candidate_ev_r": 0.8,
                "expected_cost_r": 0.05,
                "cost_r": 0.05,
                "expected_net_r": 0.75,
                "candidate_expected_net_r": 0.75,
                "fill_probability": 0.8,
                "source_completeness": 1.0,
                "source_completeness_status": "complete",
                "candidate_decision_quality_alias_status": "missing",
                "candidate_decision_quality_field_sources": {
                    "probability": "candidate_probability",
                    "fill_probability": "fill_probability",
                },
            },
            {
                "candidate_id": "candidate-not-selected-scheduler-missing",
                "decision_time_utc": "2026-04-21T08:00:00+00:00",
                "symbol": "XAUUSD",
                "canonical_replay_candidate_instance_key": (
                    "candidate-not-selected-scheduler-missing@@2026-04-21T08:00:00+00:00"
                ),
                "risk_finalizer_probe_instance_key": (
                    "candidate-not-selected-scheduler-missing@@2026-04-21T08:00:00+00:00"
                ),
                "source_bound_replay_candidate_instance_key": (
                    "candidate-not-selected-scheduler-missing@@2026-04-21T08:00:00+00:00"
                ),
                "candidate_instance_identity_status": "materialized",
                "risk_authority": "runtime_risk_authority_packet_v1",
                "risk_authority_status": "pre_scheduler_risk_authority_materialized",
                "risk_authority_packet_hash_sha256": "hash-not-selected",
                "risk_config_source": "fixture",
                "risk_per_trade_pct": 0.25,
                "selected_cell_risk_pct": 0.25,
                "scheduler_approved_risk_pct": 0.25,
                "ultimate_package_source_bound_candidate_use_allowed": True,
                "scheduler_quality_backfill_status": (
                    "scheduler_option_missing_for_candidate"
                ),
                "scheduler_materialization_action_intent": "new_position",
                "candidate_scheduler_quality_parity_status": (
                    "not_applicable_scheduler_option_missing"
                ),
                "candidate_scheduler_quality_parity_mismatches": [],
                "probability": 0.7,
                "candidate_probability": 0.7,
                "ev_r": 0.8,
                "candidate_ev_r": 0.8,
                "expected_cost_r": 0.05,
                "cost_r": 0.05,
                "expected_net_r": 0.75,
                "candidate_expected_net_r": 0.75,
                "fill_probability": 0.8,
                "source_completeness": 1.0,
                "source_completeness_status": "complete",
                "candidate_decision_quality_alias_status": "materialized",
                "candidate_decision_quality_source_boundary": (
                    "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
                ),
                "source_boundary": (
                    "predecision_package_quality_and_broker_cost_no_outcome_fields"
                ),
                "candidate_decision_quality_field_sources": {
                    "probability": "candidate_probability",
                    "expected_net_r": "candidate_expected_net_r",
                    "fill_probability": "fill_probability",
                    "source_completeness": "source_completeness",
                },
            },
            {
                "candidate_id": "candidate-selected-lost-scheduler-quality",
                "decision_time_utc": "2026-04-21T08:00:00+00:00",
                "symbol": "XAUUSD",
                "canonical_replay_candidate_instance_key": (
                    "candidate-selected-lost-scheduler-quality@@2026-04-21T08:00:00+00:00"
                ),
                "risk_finalizer_probe_instance_key": (
                    "candidate-selected-lost-scheduler-quality@@2026-04-21T08:00:00+00:00"
                ),
                "source_bound_replay_candidate_instance_key": (
                    "candidate-selected-lost-scheduler-quality@@2026-04-21T08:00:00+00:00"
                ),
                "candidate_instance_identity_status": "materialized",
                "risk_authority": "runtime_risk_authority_packet_v1",
                "risk_authority_status": "pre_scheduler_risk_authority_materialized",
                "risk_authority_packet_hash_sha256": "hash-selected",
                "risk_config_source": "fixture",
                "risk_per_trade_pct": 0.25,
                "selected_cell_risk_pct": 0.25,
                "scheduler_approved_risk_pct": 0.25,
                "ultimate_package_source_bound_candidate_use_allowed": True,
                "selected_candidate_id": (
                    "candidate-selected-lost-scheduler-quality"
                ),
                "scheduler_option_status": "candidate_selected",
                "probability": 0.7,
                "candidate_probability": 0.7,
                "ev_r": 0.8,
                "candidate_ev_r": 0.8,
                "expected_cost_r": 0.05,
                "cost_r": 0.05,
                "expected_net_r": 0.75,
                "candidate_expected_net_r": 0.75,
                "fill_probability": 0.8,
                "source_completeness": 1.0,
                "source_completeness_status": "complete",
                "candidate_decision_quality_alias_status": "materialized",
                "candidate_decision_quality_source_boundary": (
                    "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
                ),
                "candidate_decision_quality_field_sources": {
                    "probability": "candidate_probability",
                    "expected_net_r": "candidate_expected_net_r",
                    "fill_probability": "fill_probability",
                    "source_completeness": "source_completeness",
                },
            },
        ],
    )

    scan = verifier.scan_broad_candidate_quality_parity(candidate_path)

    missing = scan["missing_counts"]
    assert missing["candidate_decision_quality_field_sources.expected_net_r"] == 1
    assert missing["candidate_decision_quality_field_sources.source_completeness"] == 1
    assert missing["candidate_decision_quality_field_sources.confidence"] == 1
    assert missing["candidate_confidence"] == 1
    assert missing["candidate_decision_quality_alias_status"] == 1
    assert missing["candidate_decision_quality_source_boundary"] == 1
    assert missing["candidate_decision_quality"] == 1
    assert missing["candidate_decision_quality.selected_policy_probability"] == 1
    assert missing["canonical_replay_candidate_instance_key"] == 1
    assert missing["risk_authority"] == 1
    scheduler_missing = scan["scheduler_missing_counts"]
    assert scan["materialized_scheduler_backfill_rows"] == 1
    assert scheduler_missing["scheduler_quality_backfill_status"] == 1
    assert scheduler_missing["scheduler_candidate_decision_inputs"] == 1
    assert scheduler_missing["scheduler_expected_net_r"] == 1
    assert scan["scheduler_parity_mismatch_counts"] == {}


def test_broad_candidate_quality_scan_requires_compact_candidate_index_contract(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    candidate_index_path = tmp_path / "prefix_CANDIDATE_INDEX_LEDGER.jsonl"
    write_jsonl(
        candidate_index_path,
        [
            {
                "row_type": "candidate_index",
                "candidate_index_schema": "compact_broad_replay_candidate_index_v1",
                "candidate_packet_sidecar_payload_omitted": True,
                "candidate_index_lossless_candidate_payload": False,
                "candidate_id": "candidate-good",
                "decision_time_utc": "2026-04-21T08:00:00+00:00",
                "canonical_replay_candidate_instance_key": (
                    "candidate-good@@2026-04-21T08:00:00+00:00"
                ),
                "risk_finalizer_probe_instance_key": (
                    "candidate-good@@2026-04-21T08:00:00+00:00"
                ),
                "source_bound_replay_candidate_instance_key": (
                    "candidate-good@@2026-04-21T08:00:00+00:00"
                ),
                "candidate_instance_identity_status": "materialized",
                "risk_authority": "runtime_risk_authority_packet_v1",
                "risk_authority_status": "pre_scheduler_risk_authority_materialized",
                "risk_authority_packet_hash_sha256": "hash-good",
                "risk_config_source": "fixture",
                "risk_per_trade_pct": 0.25,
                "selected_cell_risk_pct": 0.25,
                "scheduler_approved_risk_pct": 0.25,
                "ultimate_package_source_bound_candidate_use_allowed": True,
                "probability": 0.7,
                "candidate_probability": 0.7,
                "ev_r": 0.8,
                "candidate_ev_r": 0.8,
                "expected_cost_r": 0.05,
                "cost_r": 0.05,
                "expected_net_r": 0.75,
                "candidate_expected_net_r": 0.75,
                "fill_probability": 0.8,
                "source_completeness": 1.0,
                "source_completeness_status": "complete",
                "candidate_decision_quality_alias_status": "materialized",
                "candidate_decision_quality_source_boundary": (
                    "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
                ),
                "candidate_decision_quality_field_sources": {
                    "probability": "candidate_probability",
                    "expected_net_r": "candidate_expected_net_r",
                    "fill_probability": "fill_probability",
                    "source_completeness": "source_completeness",
                },
                "scheduler_quality_backfill_status": "materialized",
                "scheduler_candidate_decision_inputs": {
                    "expected_net_r": 0.75,
                    "probability": 0.7,
                    "fill_probability": 0.8,
                    "source_completeness": 1.0,
                },
                "scheduler_expected_net_r": 0.75,
                "scheduler_probability": 0.7,
                "scheduler_fill_probability": 0.8,
                "scheduler_source_completeness": 1.0,
                "candidate_scheduler_quality_parity_status": "pass",
                "predecision_stop_hazard_guard_status": "capped",
                "predecision_stop_hazard_guard_reason": (
                    "predecision_stop_hazard_guard_risk_capped"
                ),
                "predecision_stop_hazard_guard_action": "cap",
                "predecision_stop_hazard_guard_risk_cap_applied": True,
                "predecision_stop_hazard_guard_risk_cap_pct": 0.10,
                "predecision_stop_hazard_guard_unit_risk_atr": 0.75,
                "predecision_stop_hazard_guard_distance_to_limit_risk": 0.45,
                "predecision_stop_hazard_guard_limit_fill_probability": 0.78,
                "predecision_stop_hazard_guard_source_boundary": (
                    "predecision_limit_fillability_geometry_no_outcome_path"
                ),
                "predecision_stop_hazard_guard_outcome_fields_used": False,
            },
            {
                "row_type": "candidate",
                "candidate_index_schema": "old_helper_schema",
                "candidate_packet_sidecar_payload_omitted": False,
                "candidate_index_lossless_candidate_payload": True,
            },
        ],
    )

    scan = verifier.scan_broad_candidate_quality_parity(candidate_index_path)

    bad = scan["candidate_index_bad_counts"]
    assert scan["missing_counts"].get("selected_cell_risk_pct", 0) == 0
    assert bad["row_type_mismatch"] == 1
    assert bad["candidate_index_schema_mismatch"] == 1
    assert bad["candidate_packet_sidecar_payload_omitted_mismatch"] == 1
    assert bad["candidate_index_lossless_candidate_payload_mismatch"] == 1
    assert scan["stop_hazard_projection_rows"] == 1
    assert all(
        not str(key).startswith("predecision_stop_hazard_guard")
        for key in bad
    )


def test_broad_candidate_quality_scan_stop_hazard_cap_requires_actual_capped_status(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    candidate_index_path = tmp_path / "prefix_CANDIDATE_INDEX_LEDGER.jsonl"
    write_jsonl(
        candidate_index_path,
        [
            {
                "row_type": "candidate_index",
                "candidate_index_schema": "compact_broad_replay_candidate_index_v1",
                "candidate_packet_sidecar_payload_omitted": True,
                "candidate_index_lossless_candidate_payload": False,
                "candidate_id": "candidate-passed-cap-action",
                "decision_time_utc": "2026-04-21T08:00:00+00:00",
                "ultimate_package_source_bound_candidate_use_allowed": True,
                "predecision_stop_hazard_guard_status": "passed",
                "predecision_stop_hazard_guard_reason": (
                    "predecision_stop_hazard_guard_passed"
                ),
                "predecision_stop_hazard_guard_action": "cap",
                "predecision_stop_hazard_guard_source_boundary": (
                    "predecision_limit_fillability_geometry_no_outcome_path"
                ),
                "predecision_stop_hazard_guard_outcome_fields_used": False,
            },
            {
                "row_type": "candidate_index",
                "candidate_index_schema": "compact_broad_replay_candidate_index_v1",
                "candidate_packet_sidecar_payload_omitted": True,
                "candidate_index_lossless_candidate_payload": False,
                "candidate_id": "candidate-malformed-capped",
                "decision_time_utc": "2026-04-21T08:15:00+00:00",
                "ultimate_package_source_bound_candidate_use_allowed": True,
                "predecision_stop_hazard_guard_status": "capped",
                "predecision_stop_hazard_guard_reason": (
                    "predecision_stop_hazard_guard_risk_capped"
                ),
                "predecision_stop_hazard_guard_action": "cap",
                "predecision_stop_hazard_guard_source_boundary": (
                    "predecision_limit_fillability_geometry_no_outcome_path"
                ),
                "predecision_stop_hazard_guard_outcome_fields_used": True,
                "predecision_stop_hazard_guard_risk_cap_applied": False,
            },
        ],
    )

    scan = verifier.scan_broad_candidate_quality_parity(candidate_index_path)

    bad = scan["candidate_index_bad_counts"]
    assert scan["stop_hazard_projection_rows"] == 2
    assert bad["predecision_stop_hazard_guard_capped_without_risk_cap"] == 1
    assert bad[
        "predecision_stop_hazard_guard_outcome_fields_used_not_false"
    ] == 1
    assert bad[
        "predecision_stop_hazard_guard_missing:"
        "predecision_stop_hazard_guard_risk_cap_pct"
    ] == 1
    assert bad[
        "predecision_stop_hazard_guard_missing:"
        "predecision_stop_hazard_guard_unit_risk_atr"
    ] == 1


def test_broad_candidate_quality_scan_timeout_fails_closed(
    tmp_path: Path, monkeypatch
) -> None:
    verifier = load_verifier()
    candidate_index_path = tmp_path / "prefix_CANDIDATE_INDEX_LEDGER.jsonl"
    candidate_index_path.write_text("{}\n", encoding="utf-8")

    def raise_timeout(_path):
        raise TimeoutError("fixture timeout")
        yield ""  # pragma: no cover

    monkeypatch.setattr(verifier, "iter_text_lines_with_retries", raise_timeout)

    scan = verifier.scan_broad_candidate_quality_parity(candidate_index_path)

    assert scan["exists"] is True
    assert scan["candidate_index_bad_counts"][
        "candidate_quality_parity_ledger_unreadable"
    ] == 1


def test_binary_stream_timeout_attempts_materialization_and_reports_path(
    monkeypatch,
) -> None:
    verifier = load_verifier()
    materialize_calls: list[tuple[str, bool]] = []

    class TimeoutHandle:
        def __enter__(self):
            return self

        def __exit__(self, _exc_type, _exc, _tb):
            return False

        def read(self, _chunk_size):
            raise TimeoutError("fixture read timeout")

    class TimeoutPath:
        def __str__(self):
            return "route/blocked.jsonl"

        def open(self, mode):
            assert mode == "rb"
            return TimeoutHandle()

    def materialize(path, *, force=False):
        materialize_calls.append((str(path), force))
        return force

    monkeypatch.setattr(verifier, "materialize_file_provider_artifact", materialize)
    monkeypatch.setattr(verifier.time, "sleep", lambda _seconds: None)

    try:
        list(
            verifier.iter_binary_text_lines_with_retries(
                TimeoutPath(),
                max_timeout_retries=120,
            )
        )
    except TimeoutError as exc:
        message = str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected path-qualified timeout")

    assert "route/blocked.jsonl" in message
    assert "materialization_attempted=True" in message
    assert materialize_calls == [
        ("route/blocked.jsonl", False),
        ("route/blocked.jsonl", True),
        ("route/blocked.jsonl", True),
    ]


def test_file_provider_materializer_retries_initial_timeout(monkeypatch) -> None:
    verifier = load_verifier()
    verifier._FILE_PROVIDER_MATERIALIZED_PATHS.clear()
    read_calls: list[int] = []

    class DatalessStat:
        st_size = 1024
        st_blocks = 0

    class HydrateHandle:
        def __enter__(self):
            return self

        def __exit__(self, _exc_type, _exc, _tb):
            return False

        def read(self, byte_count):
            read_calls.append(byte_count)
            if len(read_calls) == 1:
                raise TimeoutError("fixture initial hydrate timeout")
            return b"x"

    class DatalessPath:
        def __str__(self):
            return "route/dataless-scorecard.jsonl"

        def stat(self):
            return DatalessStat()

        def open(self, mode):
            assert mode == "rb"
            return HydrateHandle()

    monkeypatch.setattr(verifier, "FILE_PROVIDER_MATERIALIZE_TIMEOUT_RETRIES", 3)
    monkeypatch.setattr(verifier, "FILE_PROVIDER_MATERIALIZE_RETRY_SLEEP_SECONDS", 0)
    monkeypatch.setattr(verifier.time, "sleep", lambda _seconds: None)

    assert verifier.materialize_file_provider_artifact(DatalessPath()) is True
    assert read_calls == [1, 1]
    assert verifier.materialize_file_provider_artifact(DatalessPath()) is False


def test_jsonl_row_count_uses_inprocess_binary_counter(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    ledger = tmp_path / "ledger.jsonl"
    ledger.write_bytes(b'{"a":1}\n\n  \n{"b":2}\n{"c":3}')

    assert verifier.jsonl_row_count(ledger) == 3
    assert verifier.count_nonblank_binary_lines_with_retries(ledger, chunk_size=5) == 3


def test_binary_line_reader_terminates_at_file_size_eof(tmp_path: Path) -> None:
    verifier = load_verifier()
    ledger = tmp_path / "ledger.jsonl"
    ledger.write_bytes(b'{"a":1}\n{"b":2}')

    assert list(verifier.iter_binary_text_lines_with_retries(ledger, chunk_size=5)) == [
        '{"a":1}\n',
        '{"b":2}',
    ]


def test_builder_jsonl_line_reader_terminates_at_file_size_eof(tmp_path: Path) -> None:
    builder = load_builder()
    ledger = tmp_path / "builder-ledger.jsonl"
    ledger.write_bytes(b'{"a":1}\n{"b":2}')

    assert list(builder.iter_jsonl_text_lines(ledger)) == [
        '{"a":1}\n',
        '{"b":2}',
    ]
    assert list(builder.iter_jsonl(ledger)) == [{"a": 1}, {"b": 2}]


def test_read_text_timeout_reports_path(monkeypatch) -> None:
    verifier = load_verifier()
    materialize_calls: list[tuple[str, bool]] = []

    def materialize(path, *, force=False):
        materialize_calls.append((str(path), force))
        return force

    def timeout_read_text(self, *args, **kwargs):
        raise TimeoutError("fixture read timeout")

    monkeypatch.setattr(verifier, "materialize_file_provider_artifact", materialize)
    monkeypatch.setattr(verifier.Path, "read_text", timeout_read_text)
    monkeypatch.setattr(verifier.time, "sleep", lambda _seconds: None)

    try:
        verifier.read_text_with_retries(Path("route/blocked-summary.json"))
    except TimeoutError as exc:
        message = str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected path-qualified timeout")

    assert "route/blocked-summary.json" in message
    assert "materialization_attempted=True" in message
    assert materialize_calls == [
        ("route/blocked-summary.json", False),
        ("route/blocked-summary.json", True),
        ("route/blocked-summary.json", True),
        ("route/blocked-summary.json", True),
    ]


def test_jsonl_row_stream_unknown_length_is_explicit(tmp_path: Path) -> None:
    verifier = load_verifier()
    ledger = tmp_path / "large.jsonl"
    ledger.write_text(json.dumps({"row": 1}) + "\n", encoding="utf-8")
    stream = verifier.JsonlRowStream(ledger)

    assert list(stream) == [{"row": 1}]
    try:
        len(stream)
    except TypeError as exc:
        assert "length is unknown" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("unknown stream length should not trigger a file scan")

    assert len(verifier.JsonlRowStream(ledger, row_count=1)) == 1


def test_phase2_all_symbol_order_trade_rows_are_streamed_from_summary_counts() -> None:
    verifier = load_verifier()
    source = Path(verifier.__file__).read_text(encoding="utf-8")

    order_block_start = source.index("phase2_m15_grid_all_symbol_order_row_count")
    order_block = source[order_block_start: source.index("phase2_m15_grid_all_symbol_oracle_rows")]

    assert "stream_jsonl_rows_if_readable" in order_block
    assert "phase2_m15_grid_all_symbol_summary.get(\"order_rows\")" in order_block
    assert "phase2_m15_grid_all_symbol_summary.get(\"trade_rows\")" in order_block
    assert "read_jsonl_if_readable" not in order_block
    assert "len(" not in order_block


def test_verifier_route_reads_use_retry_wrapper_for_materialized_text() -> None:
    verifier = load_verifier()
    source = Path(verifier.__file__).read_text(encoding="utf-8")

    assert source.count(".read_text(encoding=\"utf-8\")") == 1
    assert "return path.read_text(encoding=\"utf-8\")" in source
    assert (
        "read_text_with_retries(\n"
        "            ROUTE / \"ULTIMATE_CANDIDATE_PACKAGE_REPLAY_BEHAVIOR_DOSSIER.md\""
        in source
    )
    assert (
        "read_text_with_retries(ROOT / DENOMINATOR_FORWARD_CAPTURE_PROFILE_PATH)"
        in source
    )
    assert "read_text_with_retries(ROOT / \"config/agent_config.yaml\")" in source


def test_executable_reason_aliases_are_canonicalized_before_leak_scan() -> None:
    verifier = load_verifier()
    base = {
        "package_replay_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed": True,
        "source_bound_package_candidate_use_allowed": True,
        "candidate_decision_quality_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        "source_boundary": "source_bound_asof_timewarp_decision_input",
        "pretrade_cost_packet_status": "PASSED",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "source_gap_cost_fallback_blocked": False,
        "candidate_cost_r_fallback_is_authority": False,
        "scheduler_materialization_action_intent": "new_position",
        "selector_action": "trade",
        "package_authority_has_order_geometry": True,
        "package_authority_order_geometry_status": "canonicalized",
    }

    for reason in (
        "broker_cost_selector_scheduler_executable",
        "broker_cost_selector_and_scheduler_action_executable",
    ):
        assert (
            "executable_reason_missing_or_not_authoritative"
            not in verifier.replay_executable_authority_leak_reasons(
                {
                    **base,
                    "package_replay_executable_candidate_use_allowed_reason": reason,
                }
            )
        )


def test_replay_executable_authority_requires_source_boundaries() -> None:
    verifier = load_verifier()
    row = {
        "package_replay_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed": True,
        "source_bound_package_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed_reason": (
            "broker_cost_selector_and_scheduler_action_executable"
        ),
        "pretrade_cost_packet_status": "PASSED",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "scheduler_materialization_action_intent": "new_position",
        "selector_action": "trade",
        "package_authority_has_order_geometry": True,
        "package_authority_order_geometry_status": "canonicalized",
    }

    reasons = verifier.replay_executable_authority_leak_reasons(row)

    assert "candidate_decision_quality_source_boundary_missing" in reasons
    assert "source_boundary_missing" in reasons


def test_replay_executable_authority_requires_predecision_current_price_boundary() -> None:
    verifier = load_verifier()
    row = {
        "package_replay_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed": True,
        "source_bound_package_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed_reason": (
            "broker_cost_selector_and_scheduler_action_executable"
        ),
        "candidate_decision_quality_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        "source_boundary": "source_bound_asof_timewarp_decision_input",
        "current_price": 100.0,
        "decision_time_utc": "2026-05-14T07:45:00+00:00",
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "source_gap_cost_fallback_blocked": False,
        "candidate_cost_r_fallback_is_authority": False,
        "scheduler_materialization_action_intent": "new_position",
        "selector_action": "trade",
        "package_authority_has_order_geometry": True,
        "package_authority_order_geometry_status": "canonicalized",
    }

    reasons = verifier.replay_executable_authority_leak_reasons(row)

    assert (
        "claim_bearing_current_price_without_predecision_current_price_source_boundary"
        in reasons
    )


def test_replay_executable_authority_rejects_postdecision_current_price_boundary() -> None:
    verifier = load_verifier()
    row = {
        "package_replay_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed": True,
        "source_bound_package_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed_reason": (
            "broker_cost_selector_and_scheduler_action_executable"
        ),
        "candidate_decision_quality_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        "source_boundary": "source_bound_asof_timewarp_decision_input",
        "current_price": 100.0,
        "predecision_current_price_source_boundary": (
            "postdecision_ordered_path_replay_label_not_broker_ticket_truth"
        ),
        "decision_time_utc": "2026-05-14T07:45:00+00:00",
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "source_gap_cost_fallback_blocked": False,
        "candidate_cost_r_fallback_is_authority": False,
        "scheduler_materialization_action_intent": "new_position",
        "selector_action": "trade",
        "package_authority_has_order_geometry": True,
        "package_authority_order_geometry_status": "canonicalized",
    }

    reasons = verifier.replay_executable_authority_leak_reasons(row)

    assert (
        "predecision_current_price_source_boundary_non_predecision_or_live_boundary"
        in reasons
    )


def test_replay_executable_authority_requires_predecision_current_price_source_time() -> None:
    verifier = load_verifier()
    row = {
        "package_replay_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed": True,
        "source_bound_package_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed_reason": (
            "broker_cost_selector_and_scheduler_action_executable"
        ),
        "candidate_decision_quality_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        "source_boundary": "source_bound_asof_timewarp_decision_input",
        "current_price": 100.0,
        "predecision_current_price_source_boundary": (
            "closed_m15_predecision_asof_no_postdecision_path"
        ),
        "decision_time_utc": "2026-05-14T07:45:00+00:00",
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "source_gap_cost_fallback_blocked": False,
        "candidate_cost_r_fallback_is_authority": False,
        "scheduler_materialization_action_intent": "new_position",
        "selector_action": "trade",
        "package_authority_has_order_geometry": True,
        "package_authority_order_geometry_status": "canonicalized",
    }

    reasons = verifier.replay_executable_authority_leak_reasons(row)

    assert (
        "claim_bearing_current_price_without_predecision_current_price_source_time"
        in reasons
    )


def test_current_price_authority_rejects_source_time_equal_to_decision_time() -> None:
    verifier = load_verifier()
    decision_time = "2026-05-14T07:45:00+00:00"
    row = {
        "package_replay_executable_candidate_use_allowed": True,
        "current_price": 100.0,
        "predecision_current_price_source_boundary": (
            "closed_m15_predecision_asof_no_postdecision_path"
        ),
        "predecision_current_price_source_time_utc": decision_time,
        "decision_time_utc": decision_time,
    }

    assert verifier.current_price_authority_leak_reasons(row) == [
        "predecision_current_price_source_time_not_before_decision_time"
    ]


def test_replay_executable_authority_requires_immediate_fill_source_time_field() -> None:
    verifier = load_verifier()
    row = {
        "package_replay_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed": True,
        "source_bound_package_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed_reason": (
            "broker_cost_selector_and_scheduler_action_executable"
        ),
        "candidate_decision_quality_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        "source_boundary": "source_bound_asof_timewarp_decision_input",
        "limit_immediate_marketable_fill_at_decision_applied": True,
        "limit_immediate_marketable_fill_current_price": 100.0,
        "limit_immediate_marketable_fill_source_boundary": (
            "closed_m15_predecision_asof_no_postdecision_path"
        ),
        "predecision_current_price_source_time_utc": "2026-05-14T07:30:00+00:00",
        "decision_time_utc": "2026-05-14T07:45:00+00:00",
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "source_gap_cost_fallback_blocked": False,
        "candidate_cost_r_fallback_is_authority": False,
        "scheduler_materialization_action_intent": "new_position",
        "selector_action": "trade",
        "package_authority_has_order_geometry": True,
        "package_authority_order_geometry_status": "canonicalized",
    }

    reasons = verifier.replay_executable_authority_leak_reasons(row)

    assert (
        "limit_immediate_marketable_fill_current_price_without_source_time"
        in reasons
    )


def test_replay_executable_authority_rejects_positive_r_on_non_executable_rows() -> None:
    verifier = load_verifier()
    row = {
        "package_replay_candidate_use_allowed": False,
        "package_replay_executable_candidate_use_allowed": False,
        "replay_candidate_use_allowed_now": False,
        "source_bound_package_candidate_use_allowed": True,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_source_bound_non_executable": True,
        "ultimate_package_effective_source_bound_non_executable_reason": (
            "selector_not_risk_bearing_no_shadow_sleeve_match"
        ),
        "ultimate_package_effective_source_bound_signal_r": 12.5,
    }

    reasons = verifier.replay_executable_authority_leak_reasons(row)

    assert (
        "non_executable_positive_source_bound_r_leak:"
        "ultimate_package_effective_source_bound_signal_r"
    ) in reasons


def test_replay_executable_authority_treats_generic_replay_admission_as_non_executable() -> None:
    verifier = load_verifier()
    row = {
        "package_replay_candidate_use_allowed": True,
        "replay_candidate_use_allowed_now": True,
        "package_replay_executable_candidate_use_allowed": False,
        "source_bound_package_candidate_use_allowed": True,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_source_bound_non_executable": True,
        "ultimate_package_effective_source_bound_non_executable_reason": (
            "generic_replay_admission_without_executable_authority"
        ),
        "ultimate_package_effective_source_bound_signal_r": 12.5,
        "package_replay_executable_candidate_use_allowed_reason": (
            "diagnostic_replay_admission_not_executable"
        ),
    }

    reasons = verifier.replay_executable_authority_leak_reasons(row)

    assert (
        "non_executable_positive_source_bound_r_leak:"
        "ultimate_package_effective_source_bound_signal_r"
    ) in reasons
    assert "executable_without_source_bound_membership" not in reasons


def test_replay_executable_authority_requires_source_required_reconcile_proof() -> None:
    verifier = load_verifier()
    row = {
        "package_replay_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed": True,
        "source_bound_package_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed_reason": (
            "broker_cost_selector_and_scheduler_action_executable"
        ),
        "candidate_decision_quality_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        "source_boundary": "source_bound_asof_timewarp_decision_input",
        "pretrade_cost_packet_status": "PASSED",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "source_gap_cost_fallback_blocked": False,
        "candidate_cost_r_fallback_is_authority": False,
        "scheduler_materialization_action_intent": "source_required_fail_closed",
        "scheduler_materialization_original_action_intent": (
            "invalid_action_intent:source_required_fail_closed"
        ),
        "scheduler_materialization_override_reason": (
            "source_required_fail_closed_package_source_reconciled_for_replay"
        ),
        "selector_action": "source_required",
        "package_authority_has_order_geometry": True,
        "package_authority_order_geometry_status": "canonicalized",
        "source_completeness": 1.0,
        "candidate_expected_net_r": 0.8,
        "candidate_probability": 0.75,
        "candidate_fill_probability": 0.2,
    }

    reasons = verifier.replay_executable_authority_leak_reasons(row)

    assert "source_required_replay_reconcile_not_applied" in reasons
    assert "selector_action_not_risk_bearing" not in reasons


def test_replay_executable_authority_accepts_source_required_lifecycle_reasons() -> None:
    verifier = load_verifier()
    base = {
        "package_replay_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed": True,
        "source_bound_package_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed_reason": (
            "broker_cost_selector_and_scheduler_action_executable"
        ),
        "candidate_decision_quality_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        "source_boundary": "source_bound_asof_timewarp_decision_input",
        "pretrade_cost_packet_status": "PASSED",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "source_gap_cost_fallback_blocked": False,
        "candidate_cost_r_fallback_is_authority": False,
        "scheduler_materialization_action_intent": "source_required_fail_closed",
        "scheduler_materialization_original_action_intent": (
            "invalid_action_intent:source_required_fail_closed"
        ),
        "scheduler_materialization_source_required_fail_closed_override_applied": True,
        "selector_action": "open-reduced-risk",
        "package_authority_has_order_geometry": True,
        "package_authority_order_geometry_status": "canonicalized",
        "source_completeness": 1.0,
        "candidate_expected_net_r": 0.8,
        "candidate_probability": 0.75,
        "candidate_fill_probability": 0.2,
    }

    cases = (
        (
            "source_required_fail_closed_package_source_reconciled_for_replay",
            {
                "scheduler_materialization_source_required_fail_closed_override_applied": True,
            },
        ),
        (
            "source_required_fail_closed_package_new_position_source_gap_reconciled_for_replay",
            {
                "scheduler_materialization_source_required_fail_closed_override_applied": True,
            },
        ),
        (
            "source_required_fail_closed_package_close_reverse_reconciled_for_replay",
            {
                "scheduler_materialization_source_required_fail_closed_override_applied": True,
            },
        ),
        (
            "source_required_fail_closed_package_replace_pending_reconciled_for_replay",
            {
                "scheduler_materialization_source_required_fail_closed_override_applied": True,
            },
        ),
        (
            "replay_lifecycle_action_resolver_close_and_reverse",
            {
                "scheduler_materialization_source_required_fail_closed_override_applied": False,
                "scheduler_materialization_replay_lifecycle_action_resolver_applied": True,
            },
        ),
        (
            "replay_lifecycle_action_resolver_replace_pending",
            {
                "scheduler_materialization_source_required_fail_closed_override_applied": False,
                "scheduler_materialization_replay_lifecycle_action_resolver_applied": True,
            },
        ),
    )
    for override_reason, override_fields in cases:
        row = {
            **base,
            **override_fields,
            "scheduler_materialization_override_reason": override_reason,
        }
        if override_fields.get(
            "scheduler_materialization_replay_lifecycle_action_resolver_applied"
        ):
            row["scheduler_materialization_action_intent"] = "close_and_reverse"
            row["scheduler_materialization_original_action_intent"] = "new_position"
        reasons = verifier.replay_executable_authority_leak_reasons(row)

        assert "source_required_override_reason_missing_or_invalid" not in reasons
        assert "source_required_replay_reconcile_not_applied" not in reasons


def test_executable_row_with_raw_reject_effective_trade_flagged() -> None:
    verifier = load_verifier()
    row = {
        "candidate_id": "candidate-raw-reject-effective-trade",
        "source_bound_package_candidate_use_allowed": True,
        "package_replay_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed_reason": (
            "broker_cost_selector_and_scheduler_action_executable"
        ),
        "candidate_decision_quality_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        "source_boundary": "source_bound_asof_timewarp_decision_input",
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "scheduler_materialization_action_intent": "new_position",
        "selector_action_origin": "reject",
        "selector_action": "reject",
        "effective_selector_action": "trade",
    }

    reasons = verifier.replay_executable_authority_leak_reasons(row)

    assert (
        "raw_blocking_selector_action_promoted_without_signed_materialization"
        in reasons
    )

    signed_reasons = verifier.replay_executable_authority_leak_reasons(
        {
            **row,
            "package_new_entry_authority_hash_sha256": "signed-materialization",
        }
    )
    assert (
        "raw_blocking_selector_action_promoted_without_signed_materialization"
        not in signed_reasons
    )


def test_off_session_order_execution_requires_exact_enabled_authority_family() -> None:
    verifier = load_verifier()
    row = {
        "candidate_id": "off-session-generic-authority",
        "package_replay_executable_candidate_use_allowed": True,
        "package_replay_order_executable_candidate_use_allowed": True,
        "selector_materialization_off_session_applies": True,
        "package_new_entry_authority_authority_family": (
            "explicit_package_executable_replay_materialization"
        ),
        "package_open_reduced_authority_current_config_allowed": True,
    }

    generic_reasons = verifier.replay_executable_authority_leak_reasons(row)
    assert (
        "off_session_order_executable_without_off_session_authority_family"
        in generic_reasons
    )

    exact_row = {
        **row,
        "package_new_entry_authority_authority_family": "off_session_softening",
    }
    exact_reasons = verifier.replay_executable_authority_leak_reasons(exact_row)
    assert (
        "off_session_order_executable_without_off_session_authority_family"
        not in exact_reasons
    )
    assert (
        "off_session_order_executable_without_current_config_authority"
        not in exact_reasons
    )

    disabled_reasons = verifier.replay_executable_authority_leak_reasons(
        {
            **exact_row,
            "package_open_reduced_authority_current_config_allowed": False,
        }
    )
    assert (
        "off_session_order_executable_without_current_config_authority"
        in disabled_reasons
    )


def test_reallocation_terminal_dispositions_form_exact_partition() -> None:
    verifier = load_verifier()
    finalizer = {
        "reallocation_candidate_probe_count": 4,
        "reallocation_selected_probe_count": 1,
        "reallocation_quality_blocked_probe_count": 1,
        "reallocation_policy_blocked_probe_count": 1,
        "reallocation_unadmitted_probe_count": 1,
        "reallocation_terminal_disposition_counts": {
            "selected": 1,
            "quality_blocked": 1,
            "guard_blocked": 0,
            "cost_blocked": 0,
            "lifecycle_blocked": 0,
            "policy_blocked": 1,
            "unadmitted": 1,
        },
        "reallocation_terminal_probe_row_count": 4,
        "reallocation_terminal_probe_rows": [
            {
                "canonical_replay_candidate_instance_key": (
                    f"candidate-{disposition}@@2026-05-14T08:0{index}:00+00:00"
                ),
                "reallocation_terminal_disposition": disposition,
                "reallocation_terminal_disposition_source_boundary": (
                    "risk_finalizer_terminal_selection_no_outcome_fields"
                ),
            }
            for index, disposition in enumerate(
                ("selected", "quality_blocked", "policy_blocked", "unadmitted")
            )
        ],
        "reallocation_terminal_disposition_reconciled": True,
    }
    row = {
        "candidate_id": "reallocation-partition",
        "risk_admitted_scheduler_finalizer": finalizer,
    }

    assert verifier.reallocation_terminal_disposition_reconciliation_reasons(row) == []

    bad_row = {
        **row,
        "risk_admitted_scheduler_finalizer": {
            **finalizer,
            "reallocation_unadmitted_probe_count": 0,
            "reallocation_terminal_disposition_counts": {
                **finalizer["reallocation_terminal_disposition_counts"],
                "unadmitted": 0,
            },
            "reallocation_terminal_disposition_reconciled": False,
        },
    }
    reasons = verifier.reallocation_terminal_disposition_reconciliation_reasons(
        bad_row
    )
    assert any(
        reason.startswith("reallocation_terminal_disposition_count_mismatch:")
        for reason in reasons
    )
    assert "reallocation_terminal_disposition_reconciled_not_true" in reasons

    scan = verifier.scan_replay_bridge_quality_parity(
        {},
        {"scorecard_fixture": [bad_row]},
    )
    assert scan["reallocation_terminal_disposition_bad_counts"][
        "scorecard_fixture.scorecard:reallocation_terminal_disposition_reconciled_not_true"
    ] == 1


def test_reallocation_verifier_rejects_vacuous_causal_gate_with_candidates() -> None:
    verifier = load_verifier()
    row = {
        "risk_admitted_scheduler_finalizer": {
            "causal_quality_gate_enabled": True,
            "causal_quality_gate_applied_probe_count": 0,
            "reallocation_candidate_probe_count": 1,
            "zero_trade_conversion_candidate_probe_count": 0,
            "reallocation_selected_probe_count": 0,
            "reallocation_quality_blocked_probe_count": 1,
            "reallocation_policy_blocked_probe_count": 0,
            "reallocation_unadmitted_probe_count": 0,
            "reallocation_terminal_disposition_counts": {
                "selected": 0,
                "quality_blocked": 1,
                "guard_blocked": 0,
                "cost_blocked": 0,
                "lifecycle_blocked": 0,
                "policy_blocked": 0,
                "unadmitted": 0,
            },
            "reallocation_terminal_probe_row_count": 1,
            "reallocation_terminal_probe_rows": [
                {
                    "canonical_replay_candidate_instance_key": (
                        "candidate-quality@@2026-05-14T08:00:00+00:00"
                    ),
                    "reallocation_terminal_disposition": "quality_blocked",
                    "reallocation_terminal_disposition_source_boundary": (
                        "risk_finalizer_terminal_selection_no_outcome_fields"
                    ),
                }
            ],
            "reallocation_terminal_disposition_reconciled": True,
        }
    }

    reasons = verifier.reallocation_terminal_disposition_reconciliation_reasons(row)

    assert (
        "causal_quality_gate_zero_applied_with_candidate_probes:candidates=1"
        in reasons
    )


def test_scheduler_bound_option_partition_reconciles_exactly() -> None:
    verifier = load_verifier()
    instance_keys = [
        f"scheduler-bound-{index}@@2026-05-14T08:{index:02d}:00+00:00"
        for index in range(11)
    ]
    counts = {
        "selected": 1,
        "quality_blocked": 2,
        "policy_blocked": 1,
        "authority_blocked": 3,
        "scheduler_ineligible": 4,
        "diagnostic_unadmitted": 0,
    }
    row = {
        "all_options_preserved_count": 11,
        "risk_admitted_scheduler_finalizer": {
            "scheduler_bound_option_probe_count": 11,
            "scheduler_bound_terminal_disposition_identity_schema_version": (
                "risk_finalizer_scheduler_bound_terminal_identity_partition_v1"
            ),
            "scheduler_bound_input_option_count": 11,
            "scheduler_bound_input_unique_instance_count": 11,
            "scheduler_bound_input_instance_keys": instance_keys,
            "scheduler_bound_input_missing_instance_key_count": 0,
            "scheduler_bound_input_duplicate_instance_keys": [],
            "scheduler_bound_partition_instance_keys": instance_keys,
            "scheduler_bound_partition_missing_instance_key_count": 0,
            "scheduler_bound_partition_duplicate_instance_keys": [],
            "scheduler_bound_missing_partition_instance_keys": [],
            "scheduler_bound_unexpected_partition_instance_keys": [],
            "scheduler_bound_terminal_disposition_identity_reconciled": True,
            "scheduler_bound_terminal_disposition_counts": counts,
            "scheduler_bound_terminal_disposition_reconciled": True,
            "reallocation_candidate_probe_count": 0,
        },
    }

    assert verifier.reallocation_terminal_disposition_reconciliation_reasons(row) == []

    zero_trade_cardinality = {
        **row,
        "all_options_preserved_count": 12,
    }
    assert (
        verifier.reallocation_terminal_disposition_reconciliation_reasons(
            zero_trade_cardinality
        )
        == []
    )
    mismatch = {
        **row,
        "risk_admitted_scheduler_finalizer": {
            **row["risk_admitted_scheduler_finalizer"],
            "scheduler_bound_input_option_count": 12,
            "finalizer_synthesized_all_candidate_option_count": 1,
        },
    }
    reasons = verifier.reallocation_terminal_disposition_reconciliation_reasons(
        mismatch
    )
    assert "scheduler_bound_option_probe_count_mismatch:expected=12:actual=11" in reasons
    assert (
        "scheduler_bound_input_includes_synthesized_diagnostic_options:count=1"
        in reasons
    )


def test_scheduler_bound_zero_trade_option_is_not_a_bound_probe() -> None:
    verifier = load_verifier()
    row = {
        "all_options_preserved_count": 1,
        "risk_admitted_scheduler_finalizer": {
            "scheduler_bound_option_probe_count": 0,
            "scheduler_bound_terminal_disposition_identity_schema_version": (
                "risk_finalizer_scheduler_bound_terminal_identity_partition_v1"
            ),
            "scheduler_bound_input_option_count": 0,
            "scheduler_bound_input_unique_instance_count": 0,
            "scheduler_bound_input_instance_keys": [],
            "scheduler_bound_input_missing_instance_key_count": 0,
            "scheduler_bound_input_duplicate_instance_keys": [],
            "scheduler_bound_partition_instance_keys": [],
            "scheduler_bound_partition_missing_instance_key_count": 0,
            "scheduler_bound_partition_duplicate_instance_keys": [],
            "scheduler_bound_missing_partition_instance_keys": [],
            "scheduler_bound_unexpected_partition_instance_keys": [],
            "scheduler_bound_terminal_disposition_identity_reconciled": True,
            "scheduler_bound_terminal_disposition_counts": {
                "selected": 0,
                "quality_blocked": 0,
                "policy_blocked": 0,
                "authority_blocked": 0,
                "scheduler_ineligible": 0,
                "diagnostic_unadmitted": 0,
            },
            "scheduler_bound_terminal_disposition_reconciled": True,
            "reallocation_candidate_probe_count": 0,
        },
    }

    assert verifier.reallocation_terminal_disposition_reconciliation_reasons(row) == []


def test_scheduler_bound_identity_partition_rejects_duplicate_for_missing_option() -> None:
    verifier = load_verifier()
    duplicate_key = "duplicate@@2026-05-14T08:00:00+00:00"
    row = {
        "risk_admitted_scheduler_finalizer": {
            "scheduler_bound_option_probe_count": 2,
            "scheduler_bound_terminal_disposition_identity_schema_version": (
                "risk_finalizer_scheduler_bound_terminal_identity_partition_v1"
            ),
            "scheduler_bound_input_option_count": 2,
            "scheduler_bound_input_unique_instance_count": 1,
            "scheduler_bound_input_instance_keys": [duplicate_key],
            "scheduler_bound_input_missing_instance_key_count": 0,
            "scheduler_bound_input_duplicate_instance_keys": [duplicate_key],
            "scheduler_bound_partition_instance_keys": [duplicate_key],
            "scheduler_bound_partition_missing_instance_key_count": 0,
            "scheduler_bound_partition_duplicate_instance_keys": [duplicate_key],
            "scheduler_bound_missing_partition_instance_keys": [],
            "scheduler_bound_unexpected_partition_instance_keys": [],
            "scheduler_bound_terminal_disposition_identity_reconciled": True,
            "scheduler_bound_terminal_disposition_counts": {
                "selected": 0,
                "quality_blocked": 2,
                "policy_blocked": 0,
                "authority_blocked": 0,
                "scheduler_ineligible": 0,
                "diagnostic_unadmitted": 0,
            },
            "scheduler_bound_terminal_disposition_reconciled": True,
            "reallocation_candidate_probe_count": 0,
        },
    }

    reasons = verifier.reallocation_terminal_disposition_reconciliation_reasons(row)

    assert "scheduler_bound_input_identity_count_mismatch" in reasons
    assert "scheduler_bound_partition_identity_count_mismatch" in reasons
    assert "scheduler_bound_input_duplicate_instance_keys_not_empty" in reasons
    assert "scheduler_bound_partition_duplicate_instance_keys_not_empty" in reasons


def test_signed_order_stale_selector_alias_partition_reconciles_exactly() -> None:
    verifier = load_verifier()
    scheduler_instance_keys = [
        f"scheduler-bound-{index}@@2026-05-14T08:{index:02d}:00+00:00"
        for index in range(11)
    ]
    alias_candidate_keys = scheduler_instance_keys[:5]
    alias_probe_keys = alias_candidate_keys[:3]
    alias_terminal_keys = alias_candidate_keys[3:]
    finalizer = {
        "scheduler_bound_option_probe_count": 11,
        "scheduler_bound_terminal_disposition_identity_schema_version": (
            "risk_finalizer_scheduler_bound_terminal_identity_partition_v1"
        ),
        "scheduler_bound_input_option_count": 11,
        "scheduler_bound_input_unique_instance_count": 11,
        "scheduler_bound_input_instance_keys": scheduler_instance_keys,
        "scheduler_bound_input_missing_instance_key_count": 0,
        "scheduler_bound_input_duplicate_instance_keys": [],
        "scheduler_bound_partition_instance_keys": scheduler_instance_keys,
        "scheduler_bound_partition_missing_instance_key_count": 0,
        "scheduler_bound_partition_duplicate_instance_keys": [],
        "scheduler_bound_missing_partition_instance_keys": [],
        "scheduler_bound_unexpected_partition_instance_keys": [],
        "scheduler_bound_terminal_disposition_identity_reconciled": True,
        "scheduler_bound_terminal_disposition_counts": {
            "selected": 1,
            "quality_blocked": 7,
            "policy_blocked": 1,
            "authority_blocked": 1,
            "scheduler_ineligible": 1,
            "diagnostic_unadmitted": 0,
        },
        "scheduler_bound_terminal_disposition_reconciled": True,
        "signed_order_stale_selector_alias_partition_schema_version": (
            "signed_order_stale_selector_alias_identity_partition_v1"
        ),
        "signed_order_stale_selector_alias_candidate_count": 5,
        "signed_order_stale_selector_alias_candidate_instance_keys": (
            alias_candidate_keys
        ),
        "signed_order_stale_selector_alias_probe_eligible_count": 3,
        "signed_order_stale_selector_alias_probe_eligible_instance_keys": (
            alias_probe_keys
        ),
        "signed_order_stale_selector_alias_probe_count": 3,
        "signed_order_stale_selector_alias_probe_instance_keys": alias_probe_keys,
        "signed_order_stale_selector_alias_probe_not_applied_count": 0,
        "signed_order_stale_selector_alias_terminal_count": 2,
        "signed_order_stale_selector_alias_terminal_instance_keys": (
            alias_terminal_keys
        ),
        "signed_order_stale_selector_alias_quality_blocked_probe_count": 2,
        "signed_order_stale_selector_alias_quality_blocked_instance_keys": (
            alias_probe_keys[:2]
        ),
        "signed_order_stale_selector_alias_selected_probe_count": 0,
        "signed_order_stale_selector_alias_selected_instance_keys": [],
        "signed_order_stale_selector_alias_other_terminal_probe_count": 1,
        "signed_order_stale_selector_alias_other_terminal_instance_keys": (
            alias_probe_keys[2:]
        ),
        "signed_order_stale_selector_alias_missing_instance_key_count": 0,
        "signed_order_stale_selector_alias_duplicate_instance_keys": [],
        "signed_order_stale_selector_alias_partition_reconciled": True,
        "reallocation_candidate_probe_count": 0,
    }
    row = {
        "all_options_preserved_count": 11,
        "risk_admitted_scheduler_finalizer": finalizer,
    }

    assert verifier.reallocation_terminal_disposition_reconciliation_reasons(row) == []

    bad_row = {
        **row,
        "risk_admitted_scheduler_finalizer": {
            **finalizer,
            "signed_order_stale_selector_alias_terminal_count": 1,
            "signed_order_stale_selector_alias_partition_reconciled": False,
        },
    }
    reasons = verifier.reallocation_terminal_disposition_reconciliation_reasons(
        bad_row
    )
    assert "signed_order_stale_selector_alias_candidate_partition_mismatch" in reasons
    assert (
        "signed_order_stale_selector_alias_partition_reconciled_not_true"
        in reasons
    )


def test_verifier_rejects_selected_policy_quality_block_masked_by_later_risk() -> None:
    verifier = load_verifier()
    probe = {
        "candidate_id": "masked-selected-policy-quality",
        "scheduler_soft_veto_finalizer_probe_applied": True,
        "scheduler_soft_veto_signed_order_stale_selector_alias_probe_allowed": True,
        "scheduler_soft_veto_signed_order_stale_selector_disposition_contract_valid": True,
        "selected_policy_executable_quality_gate_status": "blocked",
        "selected_policy_executable_quality_gate_failures": [
            "selected_policy_execution_fill_probability",
        ],
        "risk_decision": "reject",
        "risk_decision_reason": "risk_headroom_zero",
        "status": "risk_headroom_zero",
        "policy_selection_block_reason": None,
        "selected": False,
    }
    row = {
        "risk_admitted_scheduler_finalizer": {
            "probe_rows": [probe],
        },
    }

    reasons = verifier.reallocation_terminal_disposition_reconciliation_reasons(row)

    assert (
        "signed_order_stale_selector_alias_selected_policy_quality_block_masked"
        in reasons
    )

    repaired = {
        **row,
        "risk_admitted_scheduler_finalizer": {
            "probe_rows": [
                {
                    **probe,
                    "status": "selected_policy_executable_quality_gate_failed",
                    "policy_selection_block_reason": (
                        "selected_policy_executable_quality_gate_failed:"
                        "selected_policy_execution_fill_probability"
                    ),
                }
            ]
        },
    }
    assert (
        "signed_order_stale_selector_alias_selected_policy_quality_block_masked"
        not in verifier.reallocation_terminal_disposition_reconciliation_reasons(
            repaired
        )
    )


def scheduler_score_override_authority_row(**overrides: object) -> dict:
    candidate_id = "candidate-score-override"
    decision_time = "2026-05-14T08:00:00+00:00"
    instance_key = f"{candidate_id}@@{decision_time}"
    row = {
        "candidate_id": candidate_id,
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": instance_key,
        "source_bound_replay_candidate_instance_key": instance_key,
        "candidate_instance_identity_status": "materialized",
        "selector_action": "open-reduced-risk",
        "selector_reason": "candidate_admitted_selector_open_reduced_risk_package",
        "scheduler_materialization_action_intent": "new_position",
        "source_bound_package_candidate_use_allowed": True,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "package_replay_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed": True,
        "package_replay_order_executable_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed_reason": (
            "broker_cost_selector_and_scheduler_action_executable"
        ),
        "candidate_decision_quality_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        "source_boundary": "source_bound_asof_timewarp_decision_input",
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "source_gap_cost_fallback_blocked": False,
        "candidate_cost_r_fallback_is_authority": False,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "pre_order_materialization_preflight_allowed": True,
        "final_approved_risk_pct": 0.25,
        "package_authority_has_order_geometry": True,
        "package_authority_order_geometry_status": "canonicalized",
        "causal_finalizer_zero_trade_conversion_candidate": True,
        "risk_finalizer_scheduler_quality_score_before_override": -0.01,
        "risk_finalizer_scheduler_quality_score_after_override": 0.52,
        "risk_admitted_scheduler_reallocation_score": 0.52,
        "risk_finalizer_scheduler_quality_score_source": (
            "zero_trade_soft_veto_risk_admitted_scheduler_reallocation_score"
        ),
        "risk_finalizer_scheduler_score_floor_override_applied": True,
        "risk_finalizer_scheduler_score_floor_override_allowed": True,
        "risk_finalizer_scheduler_score_floor_override_reason": (
            "strict_zero_trade_soft_veto_signed_cost_source_preflight_score_handoff"
        ),
        "risk_finalizer_scheduler_score_floor_override_failures": [],
        "risk_finalizer_scheduler_score_floor_override_source_boundary": (
            "strict_predecision_signed_package_broker_cost_source_preflight_no_outcome_fields"
        ),
        "risk_finalizer_scheduler_score_floor_override_uses_outcome_fields": False,
        **signed_package_new_entry_fields(
            candidate_id=candidate_id,
            decision_time_utc=decision_time,
            selector_action="open-reduced-risk",
        ),
    }
    row.update(overrides)
    return row


def test_scheduler_score_override_authority_rejects_cost_and_signed_leaks() -> None:
    verifier = load_verifier()
    clean = scheduler_score_override_authority_row()

    assert verifier.scheduler_score_override_authority_leak_reasons(clean) == []

    cases = (
        (
            {"pretrade_cost_packet_status": "REFUSED"},
            "scheduler_score_override_pretrade_cost_not_passed",
        ),
        (
            {"cost_source_gap_status": "source_gap_pending_capture"},
            "scheduler_score_override_cost_source_gap_not_source_bound",
        ),
        (
            {"source_gap_cost_fallback_blocked": True},
            "scheduler_score_override_source_gap_cost_fallback_blocked",
        ),
        (
            {"candidate_cost_r_fallback_is_authority": True},
            "scheduler_score_override_candidate_cost_r_fallback_authority",
        ),
        (
            {
                "package_new_entry_authority_valid": False,
                "package_new_entry_authority_status": (
                    "invalid_or_missing_signed_new_entry_authority"
                ),
                "package_new_entry_authority_failures": ["unit_test_invalid"],
            },
            "scheduler_score_override_signed_authority:"
            "package_new_entry_authority_invalid:"
            "invalid_or_missing_signed_new_entry_authority",
        ),
    )
    for overrides, expected_reason in cases:
        reasons = verifier.scheduler_score_override_authority_leak_reasons(
            scheduler_score_override_authority_row(**overrides)
        )
        assert expected_reason in reasons


def test_scorecard_scan_flags_nested_scheduler_score_override_authority_leak() -> None:
    verifier = load_verifier()
    bad_probe = scheduler_score_override_authority_row(
        pretrade_cost_packet_status="REFUSED"
    )

    scan = verifier.scan_replay_bridge_quality_parity(
        {},
        {
            "scorecard_fixture": [
                {
                    "candidate_id": "scorecard-row",
                    "selected_candidate_ids": ["scorecard-row"],
                    "candidate_instance_identity_status": "materialized",
                    "candidate_decision_quality_source_boundary": (
                        "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
                    ),
                    "source_boundary": "source_bound_asof_timewarp_decision_input",
                    "risk_admitted_scheduler_finalizer": {
                        "probe_rows": [bad_probe],
                    },
                }
            ]
        },
    )

    assert (
        scan["scorecard_provenance_bad_counts"][
            "scorecard_fixture.scorecard_probe:"
            "scheduler_score_override_authority:"
            "scheduler_score_override_pretrade_cost_not_passed"
        ]
        == 1
    )


def test_replay_bridge_quality_scan_flags_unsigned_router_refusal_executable_alias() -> None:
    verifier = load_verifier()
    row = {
        "candidate_id": "unsigned-router-refusal-candidate",
        "selected_package_replay_row": True,
        "source_bound_package_candidate_use_allowed": True,
        "package_replay_source_bound_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed": True,
        "replay_candidate_use_allowed_now": True,
        "selector_action": "open-reduced-risk",
        "selector_reason": (
            "source_bound_router_refusal_open_reduced_materialized_for_replay"
        ),
        "package_new_entry_authority_status": (
            "valid_signed_predecision_new_entry_authority"
        ),
        "package_new_entry_authority_valid": False,
        "package_new_entry_authority_signed": False,
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "source_boundary": "source_bound_asof_timewarp_decision_input",
        "candidate_decision_quality_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        "scheduler_materialization_action_intent": "new_position",
    }

    scan = verifier.scan_replay_bridge_quality_parity(
        {},
        {},
        candidate_groups={"selected_package_replay_bridge": [row]},
    )

    executable_leaks = scan["executable_authority_leak_counts"]
    assert any(
        key.startswith(
            "selected_package_replay_bridge."
            "unsigned_router_refusal_executable_authority:"
        )
        for key in executable_leaks
    )


def test_verifier_rejects_mutable_projection_drift_after_valid_signed_order_admission() -> None:
    verifier = load_verifier()
    row = {
        "candidate_id": "signed-projection-drift",
        "selected_package_replay_row": True,
        "finalizer_primary_probe_package_new_entry_authority_valid": True,
        "finalizer_primary_probe_package_replay_order_executable_candidate_use_allowed": True,
        "finalizer_primary_probe_package_replay_executable_candidate_use_allowed": False,
        "finalizer_primary_probe_package_replay_executable_candidate_use_allowed_reason": (
            "signed_order_executable_authority_required:"
            "current_signed_authority_projection_mismatch:"
            "selected_policy_expected_net_calibration_required"
        ),
    }

    expected = (
        "valid_signed_order_authority_mutable_projection_drift:"
        "selected_policy_expected_net_calibration_required"
    )
    assert verifier.signed_authority_execution_projection_drift_reasons(row) == [
        expected
    ]

    scan = verifier.scan_replay_bridge_quality_parity(
        {},
        {},
        candidate_groups={"candidate_fixture": [row]},
    )
    assert scan["executable_authority_leak_counts"][
        f"candidate_fixture.{expected}"
    ] == 1


def test_verifier_rejects_signed_immediate_route_stranded_by_session_projection() -> None:
    verifier = load_verifier()
    probe = {
        "package_new_entry_authority_valid": True,
        "package_marketable_entry_guard_route_allowed": True,
        "package_marketable_entry_guard_immediate_marketable_limit_route_allowed": True,
        "package_marketable_entry_guard_replay_route": {
            "allowed": True,
            "route_allowed": True,
            "immediate_marketable_limit_route_allowed": True,
            "route_session": "moonshot_h17_18",
            "concrete_execution_session_for_immediate_marketable_limit": True,
        },
        "pre_order_materialization_immediate_marketable_fill_reason": (
            "off_configured_session_immediate_marketable_limit_disabled"
        ),
    }
    row = {
        "candidate_id": "signed-route-session-drift",
        "risk_admitted_scheduler_finalizer": {"probe_rows": [probe]},
    }
    expected = (
        "signed_immediate_marketable_route_concrete_session_projection_drift"
    )

    assert verifier.signed_marketable_route_session_projection_drift_reasons(row) == [
        expected
    ]
    assert expected in verifier.replay_executable_authority_leak_reasons(row)

    probe.update(
        {
            "pre_order_materialization_immediate_marketable_concrete_execution_session_authority": True,
            "pre_order_materialization_immediate_marketable_signed_authority_valid": True,
            "pre_order_materialization_immediate_marketable_route_authority_allowed": False,
        }
    )
    route_expected = (
        "signed_immediate_marketable_exact_route_overridden_by_auxiliary_false"
    )
    assert verifier.signed_marketable_route_session_projection_drift_reasons(row) == []
    assert verifier.signed_marketable_route_authority_precedence_drift_reasons(row) == [
        route_expected
    ]
    assert route_expected in verifier.replay_executable_authority_leak_reasons(row)

    probe["pre_order_materialization_immediate_marketable_fill_reason"] = (
        "source_safe_predecision_limit_marketable_at_decision"
    )
    assert verifier.signed_marketable_route_session_projection_drift_reasons(row) == []


def test_unsigned_router_refusal_diagnostic_candidate_use_is_not_executable_alias() -> None:
    verifier = load_verifier()
    row = {
        "candidate_id": "unsigned-router-refusal-diagnostic-candidate",
        "selected_package_replay_row": True,
        "source_bound_package_candidate_use_allowed": True,
        "package_replay_source_bound_candidate_use_allowed": True,
        "package_replay_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed": False,
        "replay_candidate_use_allowed_now": False,
        "selector_action": "reject",
        "selector_reason": (
            "source_bound_router_refusal_open_reduced_materialized_for_replay"
        ),
        "package_new_entry_authority_status": (
            "invalid_or_missing_signed_new_entry_authority"
        ),
        "package_new_entry_authority_valid": False,
        "package_new_entry_authority_signed": False,
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "source_boundary": "source_bound_asof_timewarp_decision_input",
        "candidate_decision_quality_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        "scheduler_materialization_action_intent": "new_position",
    }

    assert verifier.unsigned_router_refusal_executable_authority_leak_reasons(row) == []


def test_replay_bridge_quality_scan_requires_compact_and_scorecard_aliases() -> None:
    verifier = load_verifier()
    geometry = {
        "entry_price": 100.0,
        "stop_loss": 99.0,
        "take_profit_1": 102.0,
        "target_reference": 102.0,
        "risk_reward_ratio": 2.0,
        "trade_parameters": {
            "entry_price": 100.0,
            "stop_loss": 99.0,
            "take_profit_1": 102.0,
            "target_reference": 102.0,
            "risk_reward_ratio": 2.0,
        },
        "canonical_geometry_status": "canonicalized",
    }
    source_boundary_fields = {
        "candidate_decision_quality_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        "source_boundary": "source_bound_asof_timewarp_decision_input",
    }
    scan = verifier.scan_replay_bridge_quality_parity(
        {
            "selected_package_replay_bridge": [
                {
                    **geometry,
                    **source_boundary_fields,
                    "candidate_id": "candidate-good",
                    "selected_package_replay_row": True,
                    "expected_net_r": 0.75,
                    "candidate_expected_net_r": 0.75,
                    "fill_probability": 0.8,
                    "source_completeness": 1.0,
                    "source_completeness_status": "complete",
                    "source_bound_package_candidate_use_allowed": True,
                    "ultimate_package_source_bound_candidate_use_allowed": True,
                    "package_replay_source_bound_candidate_use_allowed": True,
                    "package_replay_candidate_use_allowed": False,
                    "package_replay_executable_candidate_use_allowed": False,
                    "package_replay_executable_candidate_use_allowed_reason": (
                        "broker_cost_packet_refused"
                    ),
                    "selected_package_candidate_use_allowed_status": (
                        "source_bound_package_axis_match_replay_candidate_use_allowed"
                    ),
                    "probability": 0.72,
                    "candidate_probability": 0.72,
                    "candidate_fill_probability": 0.8,
                    "ultimate_package_effective_matched_count": 2,
                    "ultimate_package_effective_admission_count": 1,
                    "ultimate_package_effective_source_bound_signal_r": 12.5,
                    "ultimate_package_effective_source_bound_candidate_use_allowed": True,
                    "ultimate_package_executable_admission_status": (
                        "executable_source_bound_package_admission"
                    ),
                    "ultimate_package_scheduler_consumed_status": (
                        "eligible_for_scheduler_consumption"
                    ),
                    "broker_pretrade_cost_r": 0.05,
                    "broker_calibrated_expected_cost_r": 0.05,
                    "pretrade_cost_packet_status": "REFUSED",
                    "cost_source_gap_status": "source_bound_cost_authority_present",
                    "scheduler_materialization_action_intent": "new_position",
                    "selector_action": "open-reduced-risk",
                    "effective_selector_action": "open-reduced-risk",
                    "selector_reason": "fixture",
                },
                {
                    **geometry,
                    **source_boundary_fields,
                    "candidate_id": "candidate-executable-leak",
                    "selected_package_replay_row": True,
                    "expected_net_r": 0.75,
                    "candidate_expected_net_r": 0.75,
                    "fill_probability": 0.8,
                    "source_completeness": 1.0,
                    "source_completeness_status": "complete",
                    "source_bound_package_candidate_use_allowed": True,
                    "ultimate_package_source_bound_candidate_use_allowed": True,
                    "package_replay_source_bound_candidate_use_allowed": True,
                    "package_replay_candidate_use_allowed": True,
                    "package_replay_executable_candidate_use_allowed": True,
                    "package_replay_executable_candidate_use_allowed_reason": (
                        "broker_cost_selector_and_scheduler_action_executable"
                    ),
                    "selected_package_candidate_use_allowed_status": (
                        "source_bound_package_axis_match_replay_candidate_use_allowed"
                    ),
                    "probability": 0.72,
                    "candidate_probability": 0.72,
                    "candidate_fill_probability": 0.8,
                    "ultimate_package_effective_matched_count": 2,
                    "ultimate_package_effective_admission_count": 1,
                    "ultimate_package_effective_source_bound_signal_r": 12.5,
                    "ultimate_package_effective_source_bound_candidate_use_allowed": True,
                    "ultimate_package_executable_admission_status": (
                        "executable_source_bound_package_admission"
                    ),
                    "ultimate_package_scheduler_consumed_status": (
                        "eligible_for_scheduler_consumption"
                    ),
                    "broker_pretrade_cost_r": 0.05,
                    "broker_calibrated_expected_cost_r": 0.05,
                    "pretrade_cost_packet_status": "REFUSED",
                    "cost_source_gap_status": "source_bound_cost_authority_present",
                    "scheduler_materialization_action_intent": "new_position",
                    "selector_action": "open-reduced-risk",
                    "effective_selector_action": "open-reduced-risk",
                    "selector_reason": "fixture",
                },
                {
                    **geometry,
                    **source_boundary_fields,
                    "candidate_id": "candidate-selected-policy-missing-nested",
                    "selected_package_replay_row": True,
                    "expected_net_r": 0.75,
                    "candidate_expected_net_r": 0.75,
                    "fill_probability": 0.8,
                    "source_completeness": 1.0,
                    "source_completeness_status": "complete",
                    "source_bound_package_candidate_use_allowed": True,
                    "ultimate_package_source_bound_candidate_use_allowed": True,
                    "package_replay_source_bound_candidate_use_allowed": True,
                    "package_replay_candidate_use_allowed": False,
                    "package_replay_executable_candidate_use_allowed": False,
                    "package_replay_executable_candidate_use_allowed_reason": (
                        "broker_cost_packet_refused"
                    ),
                    "selected_package_candidate_use_allowed_status": (
                        "source_bound_package_axis_match_replay_candidate_use_allowed"
                    ),
                    "probability": 0.72,
                    "candidate_probability": 0.72,
                    "candidate_fill_probability": 0.8,
                    "ultimate_candidate_package_packet_hash_sha256": "packet-hash",
                    "ultimate_candidate_package_packet_shape_hash_sha256": "shape-hash",
                    "ultimate_package_effective_matched_count": 2,
                    "ultimate_package_effective_admission_count": 1,
                    "ultimate_package_effective_source_bound_signal_r": 12.5,
                    "ultimate_package_effective_source_bound_candidate_use_allowed": True,
                    "ultimate_package_executable_admission_status": (
                        "executable_source_bound_package_admission"
                    ),
                    "ultimate_package_scheduler_consumed_status": (
                        "eligible_for_scheduler_consumption"
                    ),
                    "broker_pretrade_cost_r": 0.05,
                    "broker_calibrated_expected_cost_r": 0.05,
                    "pretrade_cost_packet_status": "REFUSED",
                    "cost_source_gap_status": "source_bound_cost_authority_present",
                    "scheduler_materialization_action_intent": "new_position",
                    "selector_action": "trade",
                    "effective_selector_action": "trade",
                    "selector_reason": "fixture",
                    "selected_policy_for_expected_net_r": "momentum_exhaustion",
                    "selected_policy_expected_net_r": 0.75,
                    "selected_policy_probability": 0.72,
                    "selected_policy_source_completeness": 1.0,
                },
                {
                    "candidate_id": "candidate-bad",
                    "selected_package_replay_row": True,
                    "source_completeness": 1.0,
                },
            ],
        },
        {
            "selected_package_replay_bridge": [
                {
                    "scheduler_packet": {
                        "all_options_preserved": [
                            {
                                "candidate_id": "candidate-option-bad",
                                "source_completeness": 1.0,
                            },
                            {
                                "candidate_id": "candidate-option-pending-wait",
                                "source_type": "pending_order",
                                "action_class": "wait",
                            },
                            {
                                "candidate_id": "candidate-option-good",
                                "scheduler_candidate_decision_inputs": {
                                    "expected_net_r": 0.8,
                                    "candidate_expected_net_r": 0.8,
                                    "probability": 0.72,
                                    "fill_probability": 0.64,
                                    "source_completeness": 1.0,
                                    "broker_pretrade_cost_r": 0.04,
                                    "broker_calibrated_expected_cost_r": 0.04,
                                    "selector_action": "open-reduced-risk",
                                    "selector_reason": "fixture",
                                },
                            },
                        ]
                    }
                }
            ],
            "scorecard_fixture": [
                {
                    "selected_candidate_id": None,
                    "selected_candidate_ids": [],
                    "source_boundary": None,
                    "candidate_decision_quality_source_boundary": None,
                    "canonical_replay_candidate_instance_key": (
                        "bad-no-selected@@2026-05-13T08:00:00+00:00"
                    ),
                    "risk_finalizer_probe_instance_key": (
                        "bad-no-selected@@2026-05-13T08:00:00+00:00"
                    ),
                    "source_bound_replay_candidate_instance_key": (
                        "bad-no-selected@@2026-05-13T08:00:00+00:00"
                    ),
                    "candidate_instance_identity_status": "materialized",
                    "risk_admitted_scheduler_finalizer": {
                        "probe_rows": [
                            {
                                "candidate_id": "probe-missing-boundary",
                                "status": "risk_authority_admitted",
                                "source_boundary": None,
                                "candidate_decision_quality_source_boundary": None,
                            }
                        ]
                    },
                },
                {
                    "selected_candidate_id": None,
                    "selected_candidate_ids": [],
                    "source_boundary": "broker_live_outcome_boundary",
                    "candidate_decision_quality_source_boundary": (
                        "postdecision_trade_result_boundary"
                    ),
                    "final_r": 1.25,
                    "package_replay_executable_candidate_use_allowed": True,
                    "risk_admitted_scheduler_finalizer": {
                        "probe_rows": [
                            {
                                "candidate_id": "probe-skipped-with-outcome",
                                "status": "candidate_instance_identity_missing",
                                "final_r": -1.0,
                            }
                        ]
                    },
                }
            ],
        },
        {
            "selected_package_replay_bridge": [
                {
                    **geometry,
                    **source_boundary_fields,
                    "replay_candidate_id": "candidate-denom-good",
                    "member_axis_match_count": 1,
                    "selected_package_denominator_use_allowed": True,
                    "selected_package_bridge_join_status": "exact_candidate_window_join",
                    "selected_package_bridge_join_key": (
                        "candidate-denom-good@@2026-05-13T08:00:00+00:00"
                    ),
                    "canonical_replay_candidate_instance_key": (
                        "candidate-denom-good@@2026-05-13T08:00:00+00:00"
                    ),
                    "expected_net_r": 0.75,
                    "candidate_expected_net_r": 0.75,
                    "probability": 0.7,
                    "candidate_probability": 0.7,
                    "fill_probability": 0.8,
                    "candidate_fill_probability": 0.8,
                    "source_completeness": 1.0,
                    "source_completeness_status": "complete",
                    "source_bound_package_candidate_use_allowed": True,
                    "ultimate_package_source_bound_candidate_use_allowed": True,
                    "package_replay_source_bound_candidate_use_allowed": True,
                    "package_replay_candidate_use_allowed": False,
                    "package_replay_executable_candidate_use_allowed": False,
                    "package_replay_executable_candidate_use_allowed_reason": (
                        "broker_cost_packet_refused"
                    ),
                    "selected_package_candidate_use_allowed_status": (
                        "source_bound_package_axis_match_replay_candidate_use_allowed"
                    ),
                    "ultimate_package_effective_matched_count": 2,
                    "ultimate_package_effective_admission_count": 1,
                    "ultimate_package_effective_source_bound_signal_r": 12.5,
                    "ultimate_package_effective_source_bound_candidate_use_allowed": True,
                    "ultimate_package_executable_admission_status": (
                        "executable_source_bound_package_admission"
                    ),
                    "ultimate_package_scheduler_consumed_status": (
                        "eligible_for_scheduler_consumption"
                    ),
                    "selector_action": "open-reduced-risk",
                    "selector_reason": "fixture",
                },
                {
                    "replay_candidate_id": "candidate-denom-bad",
                    "selected_package_denominator_use_allowed": True,
                    "source_bound_package_candidate_use_allowed": True,
                    "member_axis_match_count": "malformed-numeric-count",
                    "matched_stable_member_axis_ids": ["member_axis:fixture"],
                    "source_completeness": 1.0,
                },
                {
                    **geometry,
                    **source_boundary_fields,
                    "replay_candidate_id": "candidate-denom-mismatch",
                    "selected_package_denominator_use_allowed": True,
                    "member_axis_match_count": 1,
                    "selected_package_bridge_join_status": "exact_candidate_window_join",
                    "selected_package_bridge_join_key": (
                        "candidate-denom-mismatch@@window:legacy"
                    ),
                    "canonical_replay_candidate_instance_key": (
                        "candidate-denom-mismatch@@2026-05-13T08:45:00+00:00"
                    ),
                    "expected_net_r": 0.75,
                    "candidate_expected_net_r": 0.75,
                    "probability": 0.7,
                    "candidate_probability": 0.7,
                    "fill_probability": 0.8,
                    "candidate_fill_probability": 0.8,
                    "source_completeness": 1.0,
                    "source_completeness_status": "complete",
                    "source_bound_package_candidate_use_allowed": True,
                    "ultimate_package_source_bound_candidate_use_allowed": True,
                    "package_replay_source_bound_candidate_use_allowed": True,
                    "package_replay_candidate_use_allowed": False,
                    "package_replay_executable_candidate_use_allowed": False,
                    "selected_package_candidate_use_allowed_status": (
                        "source_bound_package_axis_match_replay_candidate_use_allowed"
                    ),
                    "ultimate_package_effective_matched_count": 2,
                    "ultimate_package_effective_admission_count": 1,
                    "ultimate_package_effective_source_bound_signal_r": 12.5,
                    "ultimate_package_effective_source_bound_candidate_use_allowed": True,
                    "ultimate_package_executable_admission_status": (
                        "executable_source_bound_package_admission"
                    ),
                    "ultimate_package_scheduler_consumed_status": (
                        "eligible_for_scheduler_consumption"
                    ),
                    "selector_action": "open-reduced-risk",
                    "selector_reason": "fixture",
                },
            ],
            "phase2_m15_grid_all_symbol_label_join": [
                {
                    **geometry,
                    **source_boundary_fields,
                    "replay_candidate_id": "candidate-all-symbol-label-loss",
                    "selected_package_denominator_use_allowed": True,
                    "member_axis_match_count": 1,
                    "source_bound_package_candidate_use_allowed": True,
                }
            ],
        },
        candidate_groups={
            "selected_package_replay_bridge": [
                {
                    **geometry,
                    **source_boundary_fields,
                    "candidate_id": "candidate-raw-stale-executable",
                    "selected_package_replay_row": True,
                    "expected_net_r": 0.75,
                    "candidate_expected_net_r": 0.75,
                    "fill_probability": 0.8,
                    "source_completeness": 1.0,
                    "source_completeness_status": "complete",
                    "source_bound_package_candidate_use_allowed": True,
                    "ultimate_package_source_bound_candidate_use_allowed": True,
                    "package_replay_source_bound_candidate_use_allowed": True,
                    "package_replay_candidate_use_allowed": True,
                    "package_replay_executable_candidate_use_allowed": True,
                    "package_replay_executable_candidate_use_allowed_reason": (
                        "broker_cost_selector_and_scheduler_action_executable"
                    ),
                    "selected_package_candidate_use_allowed_status": (
                        "broker_cost_selector_and_scheduler_action_executable"
                    ),
                    "pretrade_cost_packet_status": "PASSED",
                    "cost_source_gap_status": "source_bound_cost_authority_present",
                    "scheduler_materialization_action_intent": "new_position",
                    "scheduler_materialization_skip_reason": (
                        "selector_reduce_risk_not_new_entry_authority"
                    ),
                    "selector_action": "reduce-risk",
                    "selector_reason": "numeric_confluence_structured_disagreement",
                }
            ]
        },
    )

    compact_missing = scan["compact_missing_counts"]
    denominator_missing = scan["denominator_missing_counts"]
    option_missing = scan["scorecard_option_missing_counts"]
    executable_leaks = scan["executable_authority_leak_counts"]
    bridge_join_bad = scan["selected_package_bridge_join_bad_counts"]
    scorecard_bad = scan["scorecard_provenance_bad_counts"]
    assert compact_missing["selected_package_replay_bridge.expected_net_r"] == 1
    assert compact_missing["selected_package_replay_bridge.selector_action"] == 1
    assert compact_missing["selected_package_replay_bridge.effective_selector_action"] == 1
    assert (
        compact_missing[
            "selected_package_replay_bridge.candidate_decision_quality_source_boundary"
        ]
        == 1
    )
    assert compact_missing["selected_package_replay_bridge.candidate_decision_quality"] == 1
    assert compact_missing["selected_package_replay_bridge.source_boundary"] == 1
    assert (
        denominator_missing[
            "selected_package_replay_bridge.ultimate_package_effective_admission_count"
        ]
        == 1
    )
    assert (
        denominator_missing[
            "selected_package_replay_bridge.selected_package_candidate_use_allowed_status"
        ]
        == 1
    )
    assert (
        denominator_missing[
            "selected_package_replay_bridge.candidate_decision_quality_source_boundary"
        ]
        == 1
    )
    assert denominator_missing["selected_package_replay_bridge.source_boundary"] == 1
    assert (
        denominator_missing["phase2_m15_grid_all_symbol_label_join.expected_net_r"]
        == 1
    )
    assert (
        denominator_missing["phase2_m15_grid_all_symbol_label_join.selector_action"]
        == 1
    )
    assert (
        scan["selected_package_bridge_join_status_counts"]["exact_candidate_window_join"]
        == 2
    )
    assert (
        bridge_join_bad[
            "selected_package_replay_bridge.selected_package_bridge_join_status:missing"
        ]
        == 1
    )
    assert (
        bridge_join_bad[
            "selected_package_replay_bridge.selected_package_bridge_join_key_missing"
        ]
        == 1
    )
    assert (
        bridge_join_bad[
            "selected_package_replay_bridge.canonical_replay_candidate_instance_key_missing"
        ]
        == 1
    )
    assert (
        bridge_join_bad[
            "selected_package_replay_bridge.selected_package_bridge_join_key_not_canonical_instance_key"
        ]
        == 1
    )
    assert (
        bridge_join_bad[
            "phase2_m15_grid_all_symbol_label_join.selected_package_bridge_join_status:missing"
        ]
        == 1
    )
    assert (
        bridge_join_bad[
            "phase2_m15_grid_all_symbol_label_join.selected_package_bridge_join_key_missing"
        ]
        == 1
    )
    assert (
        bridge_join_bad[
            "phase2_m15_grid_all_symbol_label_join.canonical_replay_candidate_instance_key_missing"
        ]
        == 1
    )
    assert (
        denominator_missing.get(
            "phase2_m15_grid_all_symbol_label_join.candidate_decision_quality_source_boundary"
        , 0)
        == 0
    )
    assert (
        executable_leaks[
            "selected_package_replay_bridge.pretrade_cost_packet_status_not_passed"
        ]
        == 1
    )
    assert (
        executable_leaks[
            "selected_package_replay_bridge.scheduler_materialization_skip_reason_present"
        ]
        == 1
    )
    assert option_missing["selected_package_replay_bridge.expected_net_r"] == 1
    assert option_missing["selected_package_replay_bridge.selector_reason"] == 1
    assert scorecard_bad["scorecard_fixture.scorecard:source_boundary_missing"] == 1
    assert (
        scorecard_bad[
            "scorecard_fixture.scorecard:"
            "source_boundary_non_predecision_or_live_boundary"
        ]
        == 1
    )
    assert (
        scorecard_bad[
            "scorecard_fixture.scorecard:"
            "candidate_decision_quality_source_boundary_missing"
        ]
        == 1
    )
    assert (
        scorecard_bad[
            "scorecard_fixture.scorecard:"
            "candidate_decision_quality_source_boundary_non_predecision_or_live_boundary"
        ]
        == 1
    )
    assert (
        scorecard_bad[
            "scorecard_fixture.scorecard:"
            "no_selected_scorecard_outcome_field_present:final_r"
        ]
        == 1
    )
    assert (
        scorecard_bad[
            "scorecard_fixture.scorecard:"
            "no_selected_scorecard_executable_authority_present:"
            "package_replay_executable_candidate_use_allowed"
        ]
        == 1
    )
    assert (
        scorecard_bad[
            "scorecard_fixture.scorecard:"
            "no_selected_scorecard_top_level_canonical_replay_candidate_instance_key_present"
        ]
        == 1
    )
    assert (
        scorecard_bad[
            "scorecard_fixture.scorecard:"
            "no_selected_scorecard_top_level_risk_finalizer_probe_instance_key_present"
        ]
        == 1
    )
    assert (
        scorecard_bad[
            "scorecard_fixture.scorecard:"
            "no_selected_scorecard_top_level_candidate_identity_materialized"
        ]
        == 1
    )
    assert (
        scorecard_bad[
            "scorecard_fixture.scorecard_probe:probe_source_boundary_missing"
        ]
        == 1
    )
    assert (
        scorecard_bad[
            "scorecard_fixture.scorecard_probe:"
            "probe_candidate_decision_quality_source_boundary_missing"
        ]
        == 1
    )
    assert (
        scorecard_bad[
            "scorecard_fixture.scorecard_probe:probe_outcome_field_present:final_r"
        ]
        == 1
    )
    assert scan["candidate_scheduler_options"] == 2
    assert scan["pending_lifecycle_scheduler_options"] == 1


def test_scorecard_scheduler_options_reads_selected_scheduler_option_trace_lists() -> None:
    verifier = load_verifier()

    options = verifier.scorecard_scheduler_options(
        {
            "selected_scheduler_option_trace": [
                {"candidate_id": "selected-a"},
                {"candidate_id": "selected-b"},
            ],
            "pre_risk_finalizer_scheduler_option_trace": [
                {"candidate_id": "pre-finalizer"}
            ],
            "post_risk_finalizer_scheduler_option_trace": [
                {"candidate_id": "post-finalizer"}
            ],
        }
    )

    assert [option["candidate_id"] for option in options] == [
        "selected-a",
        "selected-b",
        "pre-finalizer",
        "post-finalizer",
    ]


def test_compact_scorecard_projection_contract_preserves_canonical_trace() -> None:
    verifier = load_verifier()
    trace = [
        {"candidate_id": "candidate-a", "scheduler_rank": 1, "selected": True}
    ]
    row = {
        "compact_scorecard_projection_schema": (
            "gtos.final_moonshot.broad_replay.compact_scorecard_projection.v1"
        ),
        "scheduler_option_trace_projection_status": (
            "canonical_trace_preserved_exact_duplicate_aliases_omitted"
        ),
        "scheduler_option_trace_omitted_duplicate_aliases": [
            "pre_risk_finalizer_scheduler_option_trace",
            "post_risk_finalizer_scheduler_option_trace",
        ],
        "scheduler_option_trace": trace,
        "scheduler_option_trace_projection_sha256": (
            verifier.stable_projection_sha256(trace)
        ),
    }

    assert verifier.compact_scorecard_projection_reasons(row) == []
    row["scheduler_option_trace_projection_sha256"] = "bad"
    assert verifier.compact_scorecard_projection_reasons(row) == [
        "compact_scorecard_canonical_trace_hash_mismatch"
    ]


def test_compact_scorecard_projection_contract_preserves_distinct_alias() -> None:
    verifier = load_verifier()
    canonical = [{"candidate_id": "canonical"}]
    distinct = [{"candidate_id": "distinct"}]
    row = {
        "compact_scorecard_projection_schema": (
            "gtos.final_moonshot.broad_replay.compact_scorecard_projection.v1"
        ),
        "scheduler_option_trace_projection_status": (
            "canonical_trace_preserved_exact_duplicate_aliases_omitted"
        ),
        "scheduler_option_trace_omitted_duplicate_aliases": [
            "post_risk_finalizer_scheduler_option_trace"
        ],
        "scheduler_option_trace": canonical,
        "pre_risk_finalizer_scheduler_option_trace": distinct,
        "scheduler_option_trace_projection_sha256": (
            verifier.stable_projection_sha256(canonical)
        ),
    }

    assert verifier.compact_scorecard_projection_reasons(row) == []
    row["pre_risk_finalizer_scheduler_option_trace"] = canonical
    assert verifier.compact_scorecard_projection_reasons(row) == [
        "compact_scorecard_duplicate_alias_not_omitted:"
        "pre_risk_finalizer_scheduler_option_trace"
    ]


def test_compact_decision_projection_contract_rejects_reintroduced_alias() -> None:
    verifier = load_verifier()
    partition = {
        "schema": "gtos.current_fvg_poi_generation_partition.v1",
        "rows": [{"poi_id": "poi-a"}],
    }
    row = {
        "compact_decision_projection_schema": (
            "gtos.final_moonshot.broad_replay.compact_decision_projection.v1"
        ),
        "current_fvg_poi_generation_projection_status": (
            "canonical_top_level_preserved_exact_nested_alias_omitted"
        ),
        "current_fvg_poi_generation_projection_sha256": (
            verifier.stable_projection_sha256(partition)
        ),
        "current_fvg_poi_generation": partition,
        "candidate_generation_audit": {
            "producer_generation_audit": {
                "current_fvg_poi_generation_projection_ref": (
                    "top_level.current_fvg_poi_generation"
                )
            }
        },
    }

    assert verifier.compact_decision_projection_reasons(row) == []
    row["candidate_generation_audit"]["producer_generation_audit"][
        "current_fvg_poi_generation"
    ] = partition
    assert verifier.compact_decision_projection_reasons(row) == [
        "compact_decision_nested_duplicate_still_present"
    ]


def _valid_runtime_input_contract_summary() -> dict:
    def runtime_input(
        name: str,
        identity_field: str,
        expected_schema: str,
        rows: int,
    ) -> dict:
        return {
            "input_name": name,
            "path": f"/route/{name}.jsonl",
            "identity_field": identity_field,
            "expected_schema": expected_schema,
            "expected_row_count": rows,
            "row_count": rows,
            "unique_identity_count": rows,
            "bytes": rows * 100,
            "sha256": "a" * 64,
            "missing_identity_rows": 0,
            "duplicate_identity_rows": 0,
            "schema_mismatch_rows": 0,
            "invalid_json_rows": 0,
            "non_mapping_rows": 0,
            "issues": [],
            "valid": True,
            "status": "runtime_input_valid",
        }

    return {
        "schema": "gtos.final_moonshot.broad_live_as_if_replay_harness.summary.v2",
        "candidate_ledger_omitted": True,
        "candidate_index_ledger_omitted": True,
        "decision_ledger_compacted": True,
        "scorecard_ledger_compacted": True,
        "ultimate_package_runtime_input_contract": {
            "schema": (
                "gtos.final_moonshot.broad_replay."
                "ultimate_package_runtime_inputs.v1"
            ),
            "status": "complete_runtime_authority_inputs_bound",
            "valid": True,
            "expected_sleeve_count": 82,
            "expected_member_axis_count": 1101,
            "full_82_sleeve_surface_required": True,
            "member_axis_execution_authority_required": True,
            "invalid_input_runtime_effect": "fail_before_run_campaign",
            "failure_reasons": [],
            "inputs": {
                "sleeve_registry": runtime_input(
                    "sleeve_registry",
                    "sleeve_id",
                    (
                        "gtos.final_moonshot.ultimate_candidate_package."
                        "sleeve_registry.v1"
                    ),
                    82,
                ),
                "member_axis": runtime_input(
                    "member_axis",
                    "stable_member_axis_id",
                    (
                        "gtos.final_moonshot.denominator_to_deployment."
                        "sleeve_member_exact_join.v1"
                    ),
                    1101,
                ),
            },
        },
    }


def test_broad_summary_runtime_input_contract_accepts_complete_package_surface() -> None:
    verifier = load_verifier()
    summary = _valid_runtime_input_contract_summary()

    assert verifier.broad_summary_requires_ultimate_package_runtime_input_contract(
        summary
    ) is True
    assert verifier.broad_summary_ultimate_package_runtime_input_contract_issues(
        summary
    ) == []


def test_broad_summary_runtime_input_contract_rejects_missing_or_invalid_axis() -> None:
    verifier = load_verifier()
    summary = _valid_runtime_input_contract_summary()
    summary.pop("ultimate_package_runtime_input_contract")

    assert verifier.broad_summary_ultimate_package_runtime_input_contract_issues(
        summary
    ) == ["broad_summary_ultimate_package_runtime_input_contract_missing"]

    summary = _valid_runtime_input_contract_summary()
    member = summary["ultimate_package_runtime_input_contract"]["inputs"][
        "member_axis"
    ]
    member["valid"] = False
    member["status"] = "runtime_input_invalid"
    member["row_count"] = 0
    member["unique_identity_count"] = 0
    member["issues"] = ["file_missing"]
    issues = verifier.broad_summary_ultimate_package_runtime_input_contract_issues(
        summary
    )

    assert "broad_summary_ultimate_package_member_axis_contract_not_valid" in issues
    assert "broad_summary_ultimate_package_member_axis_row_count_invalid" in issues
    assert "broad_summary_ultimate_package_member_axis_issues_present" in issues


def test_broad_summary_runtime_input_contract_does_not_rewrite_historical_modes() -> None:
    verifier = load_verifier()
    summary = _valid_runtime_input_contract_summary()
    summary["candidate_index_ledger_omitted"] = False
    summary.pop("ultimate_package_runtime_input_contract")

    assert verifier.broad_summary_ultimate_package_runtime_input_contract_issues(
        summary
    ) == []


def _valid_capacity_safe_chunk_summary() -> dict:
    checkpoints = []
    for index, day in enumerate(("2026-06-01", "2026-06-02")):
        checkpoints.append(
            {
                "chunk_id": f"repaired:holdout:{day}:{day}",
                "profile": "repaired_package_conversion_v3",
                "split": "holdout",
                "start_day": day,
                "end_day": day,
                "day_count": 1,
                "cleanup_status": "completed",
                "broker_object_continuity": True,
                "account_object_continuity": True,
                "starting_order_sequence": index,
                "ending_order_sequence": index + 1,
                "selected_order_sequence_monotonic": True,
                "source_cache_release": {
                    "completed_chunk_day_scoped_entries_remaining": 0,
                    "completed_source_authority_scoped_entries_remaining": 0,
                    "completed_replay_source_cache_entries_remaining": 0,
                    "completed_replay_source_caches_released": True,
                    "replay_source_cache_after": {
                        "closed_bar_index": 0,
                        "row_time_index": 0,
                        "predecision_tick_query": 0,
                    },
                },
                "explicit_gc_requested": True,
                "explicit_gc_completed": True,
                "gc_collected_objects": 7,
                "automatic_gc_enabled_before_explicit_collection": False,
                "automatic_gc_enabled_after_explicit_collection": False,
            }
        )
    return {
        "capacity_safe_chunk_execution_required": True,
        "capacity_safe_chunk_execution_contract": {
            "schema": (
                "gtos.final_moonshot.broad_replay."
                "capacity_safe_chunk_execution.v2"
            ),
            "status": "complete_capacity_safe_chunk_execution",
            "valid": True,
            "configured_chunk_size": 1,
            "planned_chunk_count": 2,
            "completed_chunk_count": 2,
            "cleanup_checkpoint_count": 2,
            "current_chunk_cleanup_pending": False,
            "same_simulated_broker_reused_across_chunks": True,
            "same_account_state_reused_across_chunks": True,
            "selected_order_sequence_monotonic_across_chunks": True,
            "completed_chunk_day_scoped_source_caches_released": True,
            "completed_source_authority_scoped_caches_released": True,
            "completed_replay_source_caches_released": True,
            "explicit_gc_after_result_release_enabled": True,
            "explicit_gc_requirement_satisfied": True,
            "automatic_gc_disabled_during_replay_chunks": True,
            "automatic_gc_reenabled_between_chunks": False,
            "caller_automatic_gc_state_restored_after_harness": True,
            "cleanup_complete_for_all_completed_chunks": True,
            "checkpoints": checkpoints,
        },
    }


def test_broad_summary_capacity_safe_chunk_contract_accepts_complete_continuity() -> None:
    verifier = load_verifier()

    assert verifier.broad_summary_capacity_safe_chunk_execution_issues(
        _valid_capacity_safe_chunk_summary()
    ) == []


def test_broad_summary_capacity_safe_chunk_contract_rejects_runtime_leaks() -> None:
    verifier = load_verifier()
    summary = _valid_capacity_safe_chunk_summary()
    contract = summary["capacity_safe_chunk_execution_contract"]
    contract["valid"] = False
    contract["explicit_gc_after_result_release_enabled"] = False
    contract["checkpoints"][1]["starting_order_sequence"] = 0
    contract["checkpoints"][1]["source_cache_release"][
        "completed_chunk_day_scoped_entries_remaining"
    ] = 1
    contract["checkpoints"][1]["source_cache_release"][
        "completed_source_authority_scoped_entries_remaining"
    ] = 1
    contract["checkpoints"][1]["source_cache_release"][
        "completed_replay_source_cache_entries_remaining"
    ] = 1
    contract["checkpoints"][1]["source_cache_release"][
        "completed_replay_source_caches_released"
    ] = False
    contract["checkpoints"][1]["source_cache_release"][
        "replay_source_cache_after"
    ]["closed_bar_index"] = 1
    contract["completed_replay_source_caches_released"] = False

    issues = verifier.broad_summary_capacity_safe_chunk_execution_issues(summary)

    assert "broad_summary_capacity_safe_chunk_execution_not_valid" in issues
    assert "broad_summary_capacity_safe_chunk_explicit_gc_not_enabled" in issues
    assert (
        "broad_summary_capacity_safe_chunk_order_sequence_discontinuous:1" in issues
    )
    assert (
        "broad_summary_capacity_safe_chunk_source_cache_release_invalid:1" in issues
    )
    assert (
        "broad_summary_capacity_safe_chunk_source_authority_cache_release_invalid:1"
        in issues
    )
    assert (
        "broad_summary_capacity_safe_chunk_completed_replay_source_caches_released_not_true"
        in issues
    )
    assert (
        "broad_summary_capacity_safe_chunk_replay_source_cache_release_invalid:1"
        in issues
    )
    assert (
        "broad_summary_capacity_safe_chunk_replay_source_cache_entries_remaining:1"
        in issues
    )
    assert (
        "broad_summary_capacity_safe_chunk_replay_source_cache_counts_nonzero:1"
        in issues
    )


def test_broad_summary_capacity_safe_chunk_contract_is_opt_in_for_history() -> None:
    verifier = load_verifier()

    assert verifier.broad_summary_capacity_safe_chunk_execution_issues({}) == []


def _valid_source_authority_chunk_invariance_summary() -> dict:
    scope_days = ["2026-06-01", "2026-06-02"]
    digest = "a" * 64
    scope = {
        "mode": "full_selected_split_window_independent_of_execution_chunk",
        "scope_id": "b" * 64,
        "days": scope_days,
        "start_day": scope_days[0],
        "end_day": scope_days[-1],
        "day_count": 2,
    }
    checkpoints = []
    for day in scope_days:
        checkpoints.append(
            {
                "profile": "repaired_package_conversion_v3",
                "split": "holdout",
                "execution_days": [day],
                "source_authority_scope_mode": scope["mode"],
                "source_authority_scope_id": scope["scope_id"],
                "source_authority_days": scope_days,
                "execution_days_subset_of_source_authority": True,
                "source_plan_valid": True,
                "source_plan_digest_sha256": digest,
                "canonical_source_plan_digest_sha256": digest,
                "source_plan_matches_canonical": True,
            }
        )
    return {
        "source_authority_chunk_invariance_required": True,
        "source_authority_chunk_invariance_contract": {
            "schema": (
                "gtos.final_moonshot.broad_replay."
                "source_authority_chunk_invariance.v1"
            ),
            "status": "complete_source_authority_chunk_invariance",
            "valid": True,
            "source_authority_scope_mode": scope["mode"],
            "planned_chunk_count": 2,
            "completed_chunk_count": 2,
            "checkpoint_count": 2,
            "canonical_plan_count": 1,
            "current_chunk_pending": False,
            "all_execution_days_inside_authority_scope": True,
            "all_source_plans_valid": True,
            "all_chunk_source_plans_match_canonical": True,
            "canonical_plans": {
                f"holdout:{scope['scope_id']}": {
                    "valid": True,
                    "source_authority_scope": scope,
                    "plan_digest_sha256": digest,
                }
            },
            "checkpoints": checkpoints,
        },
    }


def test_broad_summary_source_authority_chunk_invariance_accepts_frozen_plan() -> None:
    verifier = load_verifier()

    assert verifier.broad_summary_source_authority_chunk_invariance_issues(
        _valid_source_authority_chunk_invariance_summary()
    ) == []


def test_broad_summary_source_authority_chunk_invariance_rejects_drift() -> None:
    verifier = load_verifier()
    summary = _valid_source_authority_chunk_invariance_summary()
    contract = summary["source_authority_chunk_invariance_contract"]
    contract["valid"] = False
    contract["all_chunk_source_plans_match_canonical"] = False
    contract["checkpoints"][1]["source_plan_matches_canonical"] = False
    contract["checkpoints"][1]["source_plan_digest_sha256"] = "c" * 64

    issues = verifier.broad_summary_source_authority_chunk_invariance_issues(
        summary
    )

    assert "broad_summary_source_authority_chunk_invariance_not_valid" in issues
    assert (
        "broad_summary_source_authority_all_chunk_source_plans_match_canonical_not_true"
        in issues
    )
    assert (
        "broad_summary_source_authority_source_plan_matches_canonical_invalid:1"
        in issues
    )
    assert "broad_summary_source_authority_checkpoint_digest_invalid:1" in issues


def test_broad_summary_source_authority_chunk_invariance_is_opt_in() -> None:
    verifier = load_verifier()

    assert verifier.broad_summary_source_authority_chunk_invariance_issues({}) == []


def _valid_source_authority_v2_summary(verifier) -> dict:
    symbol = "XAUUSD"
    days = ["2026-04-01", "2026-04-02"]
    scope = {
        "mode": "full_selected_split_window_independent_of_execution_chunk",
        "scope_id": "1" * 64,
        "days": days,
        "start_day": days[0],
        "end_day": days[-1],
        "day_count": 2,
    }
    static_rows = [
        {
            "symbol": symbol,
            "timeframe": timeframe,
            "sha256": str(index) * 64,
        }
        for index, timeframe in enumerate(("D1", "H4", "H1", "M15"), 1)
    ]
    m1_rows = [
        {
            "symbol": symbol,
            "trading_day": day,
            "source_day_authority_id": f"source_day:{index:024d}",
            "source_day_authority_hash_sha256": str(index + 4) * 64,
            "diagnostic_fallback_only": False,
        }
        for index, day in enumerate(days, 1)
    ]
    tick_rows = [
        {
            "symbol": symbol,
            "status": "none",
            "integrity_valid": True,
            "components": [],
        }
    ]
    static_digest = verifier.stable_projection_sha256(static_rows)
    m1_digest = verifier.stable_projection_sha256(m1_rows)
    tick_digest = verifier.stable_projection_sha256(tick_rows)
    tick_component_digest = verifier.stable_projection_sha256(
        [{"symbol": symbol, "components": []}]
    )
    plan_payload = {
        "source_authority_scope": scope,
        "requested_symbols": [symbol],
        "missing_symbols": [],
        "incomplete_sources": [],
        "static_source_digest_sha256": static_digest,
        "m1_day_plan_digest_sha256": m1_digest,
        "tick_window_plan_digest_sha256": tick_digest,
        "tick_component_source_digest_sha256": tick_component_digest,
    }
    plan_digest = verifier.stable_projection_sha256(plan_payload)
    plan = {
        "schema": (
            "gtos.final_moonshot.broad_replay.source_authority_plan.v2"
        ),
        "valid": True,
        "source_authority_scope": scope,
        "requested_symbols": [symbol],
        "requested_symbol_count": 1,
        "resolved_symbol_count": 1,
        "missing_symbols": [],
        "incomplete_sources": [],
        "expected_static_source_row_count": 4,
        "static_source_row_count": 4,
        "expected_m1_symbol_day_authority_row_count": 2,
        "m1_symbol_day_authority_row_count": 2,
        "m1_symbol_day_authority_unique_id_count": 2,
        "m1_unresolved_symbol_day_count": 0,
        "tick_window_authority_row_count": 1,
        "tick_window_integrity_failure_symbols": [],
        "static_source_digest_sha256": static_digest,
        "m1_day_plan_digest_sha256": m1_digest,
        "tick_window_plan_digest_sha256": tick_digest,
        "tick_component_source_digest_sha256": tick_component_digest,
        "plan_digest_sha256": plan_digest,
        "static_source_rows": static_rows,
        "m1_symbol_day_authority_rows": m1_rows,
        "tick_window_authority_rows": tick_rows,
    }
    checkpoints = []
    for index, day in enumerate(days):
        subset_digest = verifier.stable_projection_sha256(
            [((symbol, day), m1_rows[index]["source_day_authority_hash_sha256"])]
        )
        checkpoints.append(
            {
                "profile": "repaired_package_conversion_v3",
                "split": "development",
                "execution_days": [day],
                "source_authority_scope_mode": scope["mode"],
                "source_authority_scope_id": scope["scope_id"],
                "source_authority_days": days,
                "execution_days_subset_of_source_authority": True,
                "source_plan_valid": True,
                "source_plan_digest_sha256": str(index + 7) * 64,
                "canonical_source_plan_digest_sha256": plan_digest,
                "source_plan_matches_canonical": True,
                "static_sources_match_canonical": True,
                "tick_component_sources_match_canonical": True,
                "m1_execution_day_authority_matches_canonical": True,
                "expected_m1_execution_day_authority_digest_sha256": (
                    subset_digest
                ),
                "actual_m1_execution_day_authority_digest_sha256": subset_digest,
                "expected_m1_execution_day_authority_row_count": 1,
                "actual_m1_execution_day_authority_row_count": 1,
            }
        )
    plan_key = f"development:{scope['scope_id']}"
    return {
        "source_authority_chunk_invariance_required": True,
        "source_authority_preflight_checkpoints": [
            {
                "source_plan_key": plan_key,
                "canonical_source_plan_valid": True,
                "cleanup_valid": True,
                "canonical_source_plan_digest_sha256": plan_digest,
            }
        ],
        "source_authority_chunk_invariance_contract": {
            "schema": (
                "gtos.final_moonshot.broad_replay."
                "source_authority_chunk_invariance.v2"
            ),
            "status": "complete_source_authority_chunk_invariance",
            "valid": True,
            "source_authority_scope_mode": scope["mode"],
            "planned_chunk_count": 2,
            "completed_chunk_count": 2,
            "checkpoint_count": 2,
            "canonical_plan_count": 1,
            "current_chunk_pending": False,
            "all_execution_days_inside_authority_scope": True,
            "all_source_plans_valid": True,
            "all_chunk_source_plans_match_canonical": True,
            "canonical_plans": {plan_key: plan},
            "checkpoints": checkpoints,
        },
    }


def test_broad_summary_source_authority_v2_accepts_exact_symbol_day_contract() -> None:
    verifier = load_verifier()
    summary = _valid_source_authority_v2_summary(verifier)

    assert verifier.broad_summary_source_authority_chunk_invariance_issues(
        summary
    ) == []


def test_broad_summary_source_authority_v2_rejects_foreign_day_and_subset_drift() -> None:
    verifier = load_verifier()
    summary = _valid_source_authority_v2_summary(verifier)
    contract = summary["source_authority_chunk_invariance_contract"]
    plan = next(iter(contract["canonical_plans"].values()))
    plan["m1_symbol_day_authority_rows"][0]["trading_day"] = "2026-03-31"
    contract["checkpoints"][1][
        "actual_m1_execution_day_authority_digest_sha256"
    ] = "f" * 64

    issues = verifier.broad_summary_source_authority_chunk_invariance_issues(
        summary
    )

    assert any(
        issue.startswith(
            "broad_summary_source_authority_plan_m1_symbol_day_join_invalid:"
        )
        for issue in issues
    )
    assert (
        "broad_summary_source_authority_checkpoint_m1_subset_invalid:1"
        in issues
    )


def test_b7_5_real_extended_history_contract_is_verified_and_identity_bound() -> None:
    verifier = load_verifier()
    contract_path = (
        ROOT
        / "research/operations/"
        "final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20"
        / "B7_5_EXTENDED_HISTORY_SOURCE_WINDOW_CONTRACT.json"
    )
    contract = json.loads(contract_path.read_text(encoding="utf-8"))

    assert verifier.b7_5_extended_history_source_window_contract_issues(
        contract
    ) == []

    semantic_mutation = copy.deepcopy(contract)
    semantic_mutation["shared_execution_contract"][
        "effective_profile_config_hash_semantics"
    ]["raw_artifact_sha256_retained_in_runtime_and_ledgers"] = False
    shared_payload = dict(semantic_mutation["shared_execution_contract"])
    for field in (
        "valid",
        "status",
        "shared_execution_contract_digest_sha256",
    ):
        shared_payload.pop(field, None)
    semantic_mutation["shared_execution_contract"][
        "shared_execution_contract_digest_sha256"
    ] = verifier.stable_projection_sha256(shared_payload)
    contract_payload = dict(semantic_mutation)
    contract_payload.pop("contract_digest_sha256", None)
    semantic_mutation["contract_digest_sha256"] = (
        verifier.stable_projection_sha256(contract_payload)
    )
    semantic_issues = verifier.b7_5_extended_history_source_window_contract_issues(
        semantic_mutation
    )
    assert "b7_5_effective_profile_config_hash_semantics_invalid" in semantic_issues

    partition_mutation = copy.deepcopy(contract)
    partition_mutation["execution_contract_authority_partition"][
        "behavioral_execution_contract_digest_sha256"
    ] = "0" * 64
    partition_payload = dict(partition_mutation)
    partition_payload.pop("contract_digest_sha256", None)
    partition_mutation["contract_digest_sha256"] = (
        verifier.stable_projection_sha256(partition_payload)
    )
    partition_issues = (
        verifier.b7_5_extended_history_source_window_contract_issues(
            partition_mutation
        )
    )
    assert "b7_5_execution_contract_authority_partition_invalid" in (
        partition_issues
    )

    contract["windows"][0]["selector_axis_dispositions"][0][
        "stable_member_axis_id"
    ] = "member_axis:mutated"
    issues = verifier.b7_5_extended_history_source_window_contract_issues(
        contract
    )

    assert "b7_5_source_window_contract_digest_mismatch" in issues
    assert "b7_5_selector_disposition_invalid:b7_5_2026_01" in issues


def test_broad_summary_relational_candidate_contract_requires_exact_union() -> None:
    verifier = load_verifier()
    summary = {
        "candidate_ledger_omitted": True,
        "candidate_index_ledger_omitted": True,
        "candidate_rows": 3,
        "candidate_rows_written": 0,
        "candidate_index_rows_written": 0,
        "candidate_rows_serialized_in_dedicated_candidate_ledger": 0,
        "candidate_relational_materialization": {
            "schema": (
                "gtos.final_moonshot.broad_replay."
                "candidate_relational_materialization.v1"
            ),
            "enabled": True,
            "exact": True,
            "status": "exact_candidate_equals_missed_order_trade_union",
            "candidate_rows": 3,
            "candidate_unique_profile_scoped_instance_keys": 3,
            "candidate_duplicate_profile_scoped_instance_rows": 0,
            "terminal_union_unique_profile_scoped_instance_keys": 3,
            "candidate_minus_terminal_union_count": 0,
            "terminal_union_minus_candidate_count": 0,
            "missing_instance_key_counts": {
                "candidate": 0,
                "missed": 0,
                "order": 0,
                "trade": 0,
            },
        },
        "artifacts": {"candidate": None, "candidate_index": None},
    }

    assert verifier.broad_summary_candidate_relational_materialization_issues(
        summary
    ) == []
    summary["candidate_relational_materialization"][
        "terminal_union_unique_profile_scoped_instance_keys"
    ] = 2
    assert verifier.broad_summary_candidate_relational_materialization_issues(
        summary
    ) == ["broad_summary_candidate_relational_terminal_union_mismatch"]


def test_relational_candidate_surface_replaces_missing_candidate_index(
    tmp_path: Path,
    monkeypatch,
) -> None:
    verifier = load_verifier()
    builder = load_builder()
    monkeypatch.setattr(verifier, "ROUTE", tmp_path)
    monkeypatch.setattr(builder, "ROUTE", tmp_path)
    prefix = "BROAD_LIVE_AS_IF_REPLAY_V258_RELATIONAL_FIXTURE"
    tag = "V258_RELATIONAL_FIXTURE"
    summary = {
        "status": "broad_live_as_if_replay_materialized_broker_live_closed",
        "candidate_ledger_omitted": True,
        "candidate_index_ledger_omitted": True,
        "candidate_rows": 3,
        "candidate_rows_written": 0,
        "candidate_index_rows_written": 0,
        "candidate_rows_serialized_in_dedicated_candidate_ledger": 0,
        "order_rows": 1,
        "oracle_rows": 1,
        "trade_rows": 1,
        "live_broker_authority": False,
        "broker_mutation_enabled": False,
        "final_selection_claim": False,
        "candidate_relational_materialization": {
            "schema": (
                "gtos.final_moonshot.broad_replay."
                "candidate_relational_materialization.v1"
            ),
            "enabled": True,
            "exact": True,
            "status": "exact_candidate_equals_missed_order_trade_union",
            "candidate_rows": 3,
            "candidate_unique_profile_scoped_instance_keys": 3,
            "candidate_duplicate_profile_scoped_instance_rows": 0,
            "terminal_union_unique_profile_scoped_instance_keys": 3,
            "candidate_minus_terminal_union_count": 0,
            "terminal_union_minus_candidate_count": 0,
            "missing_instance_key_counts": {
                "candidate": 0,
                "missed": 0,
                "order": 0,
                "trade": 0,
            },
        },
        "artifacts": {"candidate": None, "candidate_index": None},
    }
    summary_path = tmp_path / f"{prefix}_SUMMARY.json"
    summary_path.write_text(json.dumps(summary), encoding="utf-8")
    required = set(builder.broad_quality_required_manifest_files(prefix, tag))
    required.update(verifier.broad_quality_required_files(prefix, tag))
    for filename in required:
        path = tmp_path / filename
        if path == summary_path:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == ".json":
            path.write_text("{}", encoding="utf-8")
        elif path.suffix == ".md":
            path.write_text("fixture\n", encoding="utf-8")
        else:
            path.write_text("{}\n", encoding="utf-8")

    assert not any("CANDIDATE_INDEX_LEDGER" in name for name in required)
    assert verifier.broad_quality_candidate_index_parity_health(
        prefix, summary
    ) == (True, 0)
    assert builder.broad_quality_candidate_index_parity_health(
        prefix, summary
    ) == (True, 0)
    assert verifier.broad_quality_prefix_complete_for_selection(prefix) is True
    assert builder.broad_quality_prefix_complete_for_selection(prefix) is True


def test_candidate_quality_scan_accepts_lossless_terminal_cost_and_risk_aliases(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    candidate_path = tmp_path / "relational-candidate.jsonl"
    decision_time = "2026-06-01T08:00:00+00:00"
    instance_key = f"candidate-alias@@{decision_time}"
    row = {
        "candidate_id": "candidate-alias",
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": instance_key,
        "risk_finalizer_probe_instance_key": instance_key,
        "source_bound_replay_candidate_instance_key": instance_key,
        "candidate_instance_identity_status": "materialized",
        "risk_authority": {
            "risk_authority_status": (
                "risk_finalizer_approved_sizing_bound_to_runtime_risk_authority"
            )
        },
        "risk_authority_packet_hash_sha256": "a" * 64,
        "risk_config_source": "fixture",
        "risk_per_trade_pct": 0.25,
        "selected_cell_risk_pct": 0.25,
        "scheduler_approved_risk_pct": 0.25,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "probability": 0.7,
        "candidate_probability": 0.7,
        "ev_r": 0.8,
        "candidate_ev_r": 0.8,
        "expected_cost_r": 0.05,
        "expected_net_r": 0.75,
        "candidate_expected_net_r": 0.75,
        "fill_probability": 0.8,
        "source_completeness": 1.0,
        "source_completeness_status": "complete",
        "candidate_decision_quality_alias_status": "materialized",
        "candidate_decision_quality_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        "source_boundary": (
            "predecision_package_quality_and_broker_cost_no_outcome_fields"
        ),
        "candidate_decision_quality_field_sources": {
            "probability": "candidate_probability",
            "expected_net_r": "candidate_expected_net_r",
            "fill_probability": "fill_probability",
            "source_completeness": "source_completeness",
        },
    }
    write_jsonl(candidate_path, [row])

    scan = verifier.scan_broad_candidate_quality_parity(candidate_path)

    assert scan["missing_counts"].get("cost_r", 0) == 0
    assert scan["missing_counts"].get("risk_authority_status", 0) == 0
    assert scan["candidate_index_bad_counts"].get(
        "expected_cost_r_cost_r_alias_mismatch", 0
    ) == 0
    assert scan["candidate_index_bad_counts"].get(
        "risk_authority_status_alias_mismatch", 0
    ) == 0


def test_provenance_required_numeric_source_fails_closed_instead_of_zero(
    tmp_path: Path,
) -> None:
    parity_builder = load_parity_builder()
    primary_path = tmp_path / "primary.json"
    fallback_path = tmp_path / "fallback.json"

    value, source_path = parity_builder.required_numeric_source_value(
        "candidate_level_source_bound_r_sum",
        ({}, primary_path),
        ({"candidate_level_source_bound_r_sum": 285719.394083202}, fallback_path),
    )

    assert value == 285719.394083202
    assert source_path == fallback_path
    with pytest.raises(
        ValueError,
        match="required_provenance_component_missing:candidate_level_source_bound_r_sum",
    ):
        parity_builder.required_numeric_source_value(
            "candidate_level_source_bound_r_sum",
            ({}, primary_path),
            ({}, fallback_path),
        )


def test_broad_summary_compact_projection_contract_requires_every_row() -> None:
    verifier = load_verifier()
    summary = {
        "decision_ledger_compacted": True,
        "scorecard_ledger_compacted": True,
        "broad_replay_compact_ledgers": {
            "decision_projection_schema": (
                "gtos.final_moonshot.broad_replay.compact_decision_projection.v1"
            ),
            "scorecard_projection_schema": (
                "gtos.final_moonshot.broad_replay.compact_scorecard_projection.v1"
            ),
            "compact_projection_counts": {
                "decision_input_rows": 2,
                "decision_rows": 2,
                "decision_projection_eligible_rows": 1,
                "scorecard_input_rows": 1,
                "scorecard_rows": 1,
                "scorecard_projection_eligible_rows": 1,
            },
        },
    }
    scan = {
        "row_counts": {
            "decision_rows": 2,
            "decision_compact_projection_eligible_rows": 1,
            "decision_compact_projection_rows": 1,
            "scorecard_rows": 1,
            "scorecard_compact_projection_eligible_rows": 1,
            "scorecard_compact_projection_rows": 1,
        }
    }

    assert verifier.broad_summary_compact_projection_issues(summary, scan) == []
    scan["row_counts"]["decision_compact_projection_rows"] = 0
    assert verifier.broad_summary_compact_projection_issues(summary, scan) == [
        "broad_summary_compact_decision_projection_incomplete"
    ]


def test_exact_relational_candidate_source_deduplicates_terminal_events(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    missed = tmp_path / "missed.jsonl"
    order = tmp_path / "order.jsonl"
    trade = tmp_path / "trade.jsonl"
    candidate = {
        "profile": "repaired_package_conversion_v3",
        "candidate_id": "candidate-a",
        "decision_time_utc": "2026-06-01T08:00:00+00:00",
        "canonical_replay_candidate_instance_key": (
            "candidate-a@@2026-06-01T08:00:00+00:00"
        ),
    }
    missed.write_text(json.dumps(candidate) + "\n", encoding="utf-8")
    order.write_text(
        json.dumps(candidate) + "\n" + json.dumps(candidate) + "\n",
        encoding="utf-8",
    )
    trade.write_text("", encoding="utf-8")
    source = verifier.ExactRelationalCandidateSource((missed, order, trade))

    assert [row["candidate_id"] for row in source] == ["candidate-a"]
    scan = verifier.scan_broad_candidate_quality_parity(source)
    assert scan["exists"] is True
    assert scan["row_count"] == 1
    assert scan["missing_counts"] == {}


def test_replay_bridge_quality_scan_fails_selected_package_displacement_quality_rejected() -> None:
    verifier = load_verifier()
    selected_option = {
        "candidate_id": "selected-displacement-bad",
        "source_type": "candidate",
        "package_replay_executable_candidate_use_allowed": True,
        "expected_net_r": 0.8,
        "candidate_expected_net_r": 0.8,
        "probability": 0.75,
        "confidence": 0.8,
        "fill_probability": 0.8,
        "source_completeness": 1.0,
        "broker_pretrade_cost_r": 0.02,
        "broker_calibrated_expected_cost_r": 0.02,
        "selector_action": "open-reduced-risk",
        "selector_reason": "package_softened",
        "scheduler_candidate_decision_inputs": {
            "package_displacement_quality": {
                "applies": True,
                "enabled": True,
                "allowed": False,
                "reason": "package_soft_authority_edge_below_primary",
                "uses_outcome_fields": False,
            }
        },
    }
    rejected_alternative = {
        **selected_option,
        "candidate_id": "rejected-alternative",
        "scheduler_candidate_decision_inputs": {
            "package_displacement_quality": {
                "applies": True,
                "enabled": True,
                "allowed": False,
                "reason": "rejected_alternative_expected_not_fatal",
                "uses_outcome_fields": False,
            }
        },
    }

    scan = verifier.scan_replay_bridge_quality_parity(
        {},
        {
            "scorecard_fixture": [
                {
                    "selected_candidate_id": "selected-displacement-bad",
                    "selected_scheduler_option_trace": [selected_option],
                    "scheduler_option_trace": [rejected_alternative],
                }
            ]
        },
    )

    bad = scan["package_displacement_quality_bad_counts"]
    assert (
        bad[
            "scorecard_fixture.scorecard:"
            "package_soft_authority_displacement_quality_failed"
        ]
        == 1
    )


def test_displacement_threshold_truth_rejects_v230_comparator_delta_as_no_primary_floor() -> None:
    verifier = load_verifier()
    reasons = verifier.package_displacement_threshold_truth_reasons(
        {
            "scheduler_candidate_decision_inputs": {
                "package_displacement_quality": {
                    "applies": True,
                    "enabled": True,
                    "allowed": False,
                    "reason": "no_primary_comparator_package_edge_below_zero_floor",
                    "candidate_edge_score": 0.046955565,
                    "best_primary_edge_score": None,
                    "edge_delta": 0.046955565,
                    "min_edge_delta": 0.05,
                    "signed_new_entry_authority_effective_valid_for_displacement": True,
                    "broker_cost_executable": True,
                    "router_refusal_origin_family_allowed": True,
                    "no_primary_comparator_override_allowed": True,
                }
            }
        }
    )

    assert "no_primary_comparator_threshold_mode_missing_or_invalid" in reasons
    assert "no_primary_comparator_absolute_edge_floor_missing" in reasons
    assert "no_primary_comparator_edge_delta_present" in reasons
    assert "no_primary_comparator_legacy_comparator_delta_floor_reason" in reasons
    assert "no_primary_comparator_eligible_positive_edge_rejected" in reasons


def test_replay_bridge_scan_surfaces_no_primary_threshold_truth_on_candidate_rows() -> None:
    verifier = load_verifier()
    scan = verifier.scan_replay_bridge_quality_parity(
        {},
        {},
        candidate_groups={
            "candidate_fixture": [
                {
                    "candidate_id": "v230-no-primary-threshold-drift",
                    "source_bound_package_candidate_use_allowed": True,
                    "scheduler_candidate_decision_inputs": {
                        "package_displacement_quality": {
                            "applies": True,
                            "enabled": True,
                            "allowed": False,
                            "reason": (
                                "no_primary_comparator_package_edge_below_zero_floor"
                            ),
                            "candidate_edge_score": 0.046955565,
                            "best_primary_edge_score": None,
                            "edge_delta": 0.046955565,
                            "min_edge_delta": 0.05,
                            "signed_new_entry_authority_effective_valid_for_displacement": True,
                            "broker_cost_executable": True,
                            "router_refusal_origin_family_allowed": True,
                            "no_primary_comparator_override_allowed": True,
                        }
                    },
                }
            ]
        },
    )

    bad = scan["package_displacement_quality_bad_counts"]
    assert bad[
        "candidate_fixture.candidate:"
        "no_primary_comparator_eligible_positive_edge_rejected"
    ] == 1


def test_displacement_threshold_truth_accepts_positive_signed_no_primary_absolute_floor() -> None:
    verifier = load_verifier()
    reasons = verifier.package_displacement_threshold_truth_reasons(
        {
            "scheduler_candidate_decision_inputs": {
                "package_displacement_quality": {
                    "applies": True,
                    "enabled": True,
                    "allowed": True,
                    "reason": (
                        "no_primary_comparator_available_explicit_override_signed_"
                        "package_edge_floor_allowed"
                    ),
                    "candidate_edge_score": 0.046955565,
                    "primary_comparator_present": False,
                    "best_primary_edge_score": None,
                    "edge_delta": None,
                    "min_edge_delta": 0.05,
                    "min_edge_delta_applies": False,
                    "no_primary_min_edge_score": 0.0,
                    "no_primary_min_edge_score_applies": True,
                    "threshold_mode": "no_primary_absolute_expected_transfer_score",
                    "threshold_value": 0.0,
                    "signed_new_entry_authority_effective_valid_for_displacement": True,
                    "broker_cost_executable": True,
                    "router_refusal_origin_family_allowed": True,
                    "no_primary_comparator_override_allowed": True,
                }
            }
        }
    )

    assert reasons == []


def test_displacement_threshold_truth_rejects_allowed_below_absolute_floor() -> None:
    verifier = load_verifier()
    reasons = verifier.package_displacement_threshold_truth_reasons(
        {
            "package_displacement_quality": {
                "applies": True,
                "enabled": True,
                "allowed": True,
                "candidate_edge_score": 0.04,
                "primary_comparator_present": False,
                "best_primary_edge_score": None,
                "edge_delta": None,
                "min_edge_delta_applies": False,
                "no_primary_min_edge_score": 0.05,
                "no_primary_min_edge_score_applies": True,
                "threshold_mode": "no_primary_absolute_expected_transfer_score",
                "signed_new_entry_authority_effective_valid_for_displacement": True,
                "broker_cost_executable": True,
                "router_refusal_origin_family_allowed": True,
                "no_primary_comparator_override_allowed": True,
            }
        }
    )

    assert reasons == ["no_primary_comparator_allowed_below_absolute_edge_floor"]


def test_broad_displacement_contract_preserves_same_instance_across_ledgers(
    tmp_path,
) -> None:
    verifier = load_verifier()
    diagnostic = {
        "applies": True,
        "enabled": True,
        "allowed": True,
        "reason": (
            "no_primary_comparator_available_explicit_override_signed_package_"
            "edge_floor_allowed"
        ),
        "authority_family": "router_refusal_softening",
        "candidate_edge_score": 0.046955565,
        "primary_comparator_present": False,
        "best_primary_candidate_id": None,
        "best_primary_edge_score": None,
        "edge_delta": None,
        "min_edge_delta": 0.05,
        "min_edge_delta_applies": False,
        "no_primary_min_edge_score": 0.0,
        "no_primary_min_edge_score_applies": True,
        "threshold_mode": "no_primary_absolute_expected_transfer_score",
        "threshold_value": 0.0,
        "candidate_edge_positive": True,
        "signed_new_entry_authority_valid": True,
        "signed_new_entry_authority_effective_valid_for_displacement": True,
        "broker_cost_executable": True,
        "candidate_origin_family": "fvg_fill",
        "candidate_origin_family_candidates": ["fvg_fill"],
        "router_refusal_origin_family_gate_enabled": True,
        "router_refusal_allowed_origin_families": ["fvg_fill"],
        "router_refusal_origin_family_allowed": True,
        "no_primary_comparator_override_allowed": True,
        "no_primary_comparator_policy_allowed": True,
        "primary_comparator_required": True,
        "hard_veto": False,
        "rank_limited_by_primary": False,
        "source_boundary": (
            "predecision_scheduler_displacement_quality_no_outcome_fields"
        ),
        "uses_outcome_fields": False,
    }
    instance_key = "candidate-contract@@2026-05-14T07:00:00+00:00"
    option = {
        "candidate_id": "candidate-contract",
        "canonical_replay_candidate_instance_key": instance_key,
        "scheduler_candidate_decision_inputs": {
            "package_displacement_quality": diagnostic,
        },
    }
    rows = {
        "candidate": {
            **option,
            "profile": "repaired_package_conversion_v3",
        },
        "missed": {
            **option,
            "profile": "repaired_package_conversion_v3",
        },
        "scorecard": {
            "profile": "repaired_package_conversion_v3",
            "scheduler_option_trace": [option],
        },
    }
    paths = {}
    for surface, row in rows.items():
        path = tmp_path / f"{surface}.jsonl"
        path.write_text(json.dumps(row) + "\n", encoding="utf-8")
        paths[surface] = path

    scan = verifier.scan_broad_package_displacement_quality_contract(paths)

    assert scan["bad_counts"] == {}
    assert scan["row_counts"]["candidate_unique_diagnostic_instances"] == 1
    assert scan["row_counts"]["scorecard_unique_diagnostic_instances"] == 1
    assert scan["row_counts"]["missed_unique_diagnostic_instances"] == 1


def test_broad_displacement_contract_requires_symmetric_missed_coverage(
    tmp_path,
) -> None:
    verifier = load_verifier()
    diagnostic = {
        "applies": True,
        "enabled": True,
        "allowed": True,
        "reason": "no_primary_comparator_not_required_signed_package_edge_floor_allowed",
        "authority_family": "numeric_disagreement_softening",
        "candidate_edge_score": 0.04,
        "primary_comparator_present": False,
        "best_primary_edge_score": None,
        "edge_delta": None,
        "min_edge_delta_applies": False,
        "no_primary_min_edge_score": 0.0,
        "no_primary_min_edge_score_applies": True,
        "threshold_mode": "no_primary_absolute_expected_transfer_score",
        "threshold_value": 0.0,
        "candidate_edge_positive": True,
        "signed_new_entry_authority_valid": True,
        "signed_new_entry_authority_effective_valid_for_displacement": True,
        "broker_cost_executable": True,
        "router_refusal_origin_family_gate_enabled": False,
        "router_refusal_origin_family_allowed": True,
        "no_primary_comparator_override_allowed": True,
        "no_primary_comparator_policy_allowed": True,
        "primary_comparator_required": False,
        "hard_veto": False,
        "rank_limited_by_primary": False,
        "source_boundary": (
            "predecision_scheduler_displacement_quality_no_outcome_fields"
        ),
        "uses_outcome_fields": False,
    }
    instance_key = "missing-missed@@2026-05-14T08:00:00+00:00"
    option = {
        "candidate_id": "missing-missed",
        "canonical_replay_candidate_instance_key": instance_key,
        "profile": "repaired_package_conversion_v3",
        "scheduler_candidate_decision_inputs": {
            "package_displacement_quality": diagnostic,
        },
    }
    paths = {}
    for surface, row in {
        "candidate": option,
        "scorecard": {
            "profile": "repaired_package_conversion_v3",
            "scheduler_option_trace": [option],
        },
        "missed": None,
    }.items():
        path = tmp_path / f"{surface}.jsonl"
        path.write_text("" if row is None else json.dumps(row) + "\n", encoding="utf-8")
        paths[surface] = path

    scan = verifier.scan_broad_package_displacement_quality_contract(paths)

    assert scan["bad_counts"]["missed:zero_displacement_contract_coverage"] == 1
    assert scan["bad_counts"][
        "cross_surface:candidate_scorecard_instance_missing_missed"
    ] == 1


@pytest.mark.parametrize("terminal_surface", ["order", "trade"])
def test_broad_displacement_contract_accepts_execution_terminal_coverage(
    tmp_path,
    terminal_surface,
) -> None:
    verifier = load_verifier()
    diagnostic = {
        "applies": True,
        "enabled": True,
        "allowed": True,
        "reason": "signed_package_edge_floor_allowed",
        "authority_family": "numeric_disagreement_softening",
        "candidate_edge_score": 0.04,
        "primary_comparator_present": False,
        "edge_delta": None,
        "min_edge_delta_applies": False,
        "no_primary_min_edge_score": 0.0,
        "no_primary_min_edge_score_applies": True,
        "threshold_mode": "no_primary_absolute_expected_transfer_score",
        "threshold_value": 0.0,
        "candidate_edge_positive": True,
        "signed_new_entry_authority_valid": True,
        "signed_new_entry_authority_effective_valid_for_displacement": True,
        "broker_cost_executable": True,
        "router_refusal_origin_family_gate_enabled": False,
        "router_refusal_origin_family_allowed": True,
        "no_primary_comparator_override_allowed": True,
        "no_primary_comparator_policy_allowed": True,
        "primary_comparator_required": False,
        "hard_veto": False,
        "rank_limited_by_primary": False,
        "source_boundary": "predecision_scheduler_displacement_quality_no_outcome_fields",
        "uses_outcome_fields": False,
    }
    instance_key = "filled-terminal@@2026-05-14T08:00:00+00:00"
    option = {
        "candidate_id": "filled-terminal",
        "canonical_replay_candidate_instance_key": instance_key,
        "profile": "repaired_package_conversion_v3",
        "scheduler_candidate_decision_inputs": {
            "package_displacement_quality": diagnostic,
        },
    }
    rows = {
        "candidate": option,
        "scorecard": {
            "profile": "repaired_package_conversion_v3",
            "scheduler_option_trace": [option],
        },
        "missed": None,
        terminal_surface: option,
    }
    paths = {}
    for surface, row in rows.items():
        path = tmp_path / f"{surface}.jsonl"
        path.write_text(
            "" if row is None else json.dumps(row) + "\n",
            encoding="utf-8",
        )
        paths[surface] = path

    scan = verifier.scan_broad_package_displacement_quality_contract(paths)

    assert scan["bad_counts"] == {}
    assert scan["row_counts"][f"{terminal_surface}_unique_diagnostic_instances"] == 1


def test_passive_limit_queue_contract_accepts_penetration_or_repeated_touch(
    tmp_path,
) -> None:
    verifier = load_verifier()
    rows = [
        {
            "candidate_id": "one-touch-diagnostic",
            "entry_price": 100.0,
            "passive_limit_queue_realism_required": True,
            "passive_limit_queue_touch_count": 1,
            "passive_limit_queue_realism_min_touch_count": 2,
            "passive_limit_queue_max_penetration_r": 0.0,
            "passive_limit_queue_realism_min_penetration_r": 0.02,
            "passive_limit_queue_max_penetration_price": 100.0,
            "passive_limit_queue_realism_passed": False,
            "fill_realism_executable": False,
            "fill_realism_reason": "not_filled_fill_realism_diagnostic_only",
        },
        {
            "candidate_id": "penetration-pass",
            "entry_price": 100.0,
            "passive_limit_queue_realism_required": True,
            "passive_limit_queue_touch_count": 1,
            "passive_limit_queue_realism_min_touch_count": 2,
            "passive_limit_queue_max_penetration_r": 0.03,
            "passive_limit_queue_realism_min_penetration_r": 0.02,
            "passive_limit_queue_max_penetration_price": 99.7,
            "passive_limit_queue_realism_passed": True,
            "fill_realism_executable": True,
            "fill_realism_reason": (
                "passive_limit_queue_realism_confirmed_by_penetration_or_repeated_touch"
            ),
        },
        {
            "candidate_id": "repeated-touch-pass",
            "entry_price": 100.0,
            "passive_limit_queue_realism_required": True,
            "passive_limit_queue_touch_count": 2,
            "passive_limit_queue_realism_min_touch_count": 2,
            "passive_limit_queue_max_penetration_r": 0.0,
            "passive_limit_queue_realism_min_penetration_r": 0.02,
            "passive_limit_queue_max_penetration_price": 100.0,
            "passive_limit_queue_realism_passed": True,
            "fill_realism_executable": True,
            "fill_realism_reason": (
                "passive_limit_queue_realism_confirmed_by_penetration_or_repeated_touch"
            ),
        },
        {
            "candidate_id": "queue-pass-terminal-ordered-tick-source-gap",
            "entry_price": 100.0,
            "passive_limit_queue_realism_required": True,
            "passive_limit_queue_touch_count": 1,
            "passive_limit_queue_realism_min_touch_count": 2,
            "passive_limit_queue_max_penetration_r": 0.03,
            "passive_limit_queue_realism_min_penetration_r": 0.02,
            "passive_limit_queue_max_penetration_price": 99.7,
            "passive_limit_queue_realism_passed": True,
            "fill_realism_executable": False,
            "fill_realism_class": "ordered_tick_required_source_gap",
            "fill_realism_reason": (
                "ordered_tick_required_for_adverse_before_profit_sequence_not_satisfied"
            ),
        },
    ]
    path = tmp_path / "missed.jsonl"
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )

    scan = verifier.scan_broad_passive_limit_queue_realism_contract(
        {"missed": path}
    )

    assert scan["bad_counts"] == {}
    assert scan["row_counts"]["missed_queue_required_rows"] == 4


def test_passive_limit_queue_contract_rejects_single_touch_without_penetration(
    tmp_path,
) -> None:
    verifier = load_verifier()
    path = tmp_path / "missed.jsonl"
    path.write_text(
        json.dumps(
            {
                "candidate_id": "invalid-one-touch-pass",
                "entry_price": 100.0,
                "passive_limit_queue_realism_required": True,
                "passive_limit_queue_touch_count": 1,
                "passive_limit_queue_realism_min_touch_count": 2,
                "passive_limit_queue_max_penetration_r": 0.0,
                "passive_limit_queue_realism_min_penetration_r": 0.02,
                "passive_limit_queue_max_penetration_price": 100.0,
                "passive_limit_queue_realism_passed": True,
                "fill_realism_executable": True,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    scan = verifier.scan_broad_passive_limit_queue_realism_contract(
        {"missed": path}
    )

    assert scan["bad_counts"][
        "missed:single_touch_without_penetration_marked_executable"
    ] == 1
    assert any(
        key.startswith("missed:queue_pass_truth_mismatch:")
        for key in scan["bad_counts"]
    )


def test_broad_quality_behavior_summary_resolves_versioned_comparison_name(
    tmp_path,
    monkeypatch,
) -> None:
    verifier = load_verifier()
    monkeypatch.setattr(verifier, "ROUTE", tmp_path)
    prefix = "BROAD_LIVE_AS_IF_REPLAY_V231_SIGNED_FINALIZER"
    comparison = (
        tmp_path
        / "V231_SIGNED_FINALIZER_VS_V230_TERMINAL_b29d4736_BEHAVIOR_COMPARISON_SUMMARY.json"
    )
    comparison.write_text("{}\n", encoding="utf-8")

    assert verifier.broad_quality_behavior_summary_path(prefix) == comparison


def test_broad_quality_behavior_contract_normalizes_same_window_schema() -> None:
    verifier = load_verifier()
    contract = verifier.normalize_broad_quality_behavior_summary(
        {
            "schema": (
                "gtos.final_moonshot.broad_live_as_if_replay."
                "same_window_comparison.v1"
            ),
            "baseline_prefix": "BASE",
            "candidate_prefix": "REPAIR",
            "candidate": {
                "live_broker_authority": False,
                "broker_mutation_enabled": False,
                "final_selection_claim": False,
                "candidate_rows": 714,
                "decision_rows": 2208,
                "scorecard_rows": 92,
                "order_event_rows": 2,
                "trades": 1,
                "missed_rows": 713,
            },
        }
    )

    assert contract == {
        "schema": (
            "gtos.final_moonshot.broad_live_as_if_replay."
            "same_window_comparison.v1"
        ),
        "schema_supported": True,
        "candidate_payload_valid": True,
        "baseline_prefix": "BASE",
        "candidate_prefix": "REPAIR",
        "live_broker_authority": False,
        "broker_mutation_enabled": False,
        "final_selection_claim": False,
        "row_counts": {
            "candidate": 714,
            "decision": 2208,
            "scorecard": 92,
            "order": 2,
            "trade": 1,
            "missed": 713,
        },
    }


def test_broad_flow_behavior_counts_keep_relational_candidate_authority() -> None:
    verifier = load_verifier()

    counts = verifier.merged_broad_flow_behavior_row_counts(
        {
            "row_counts": {
                "candidate": 104_434,
                "decision": 42_816,
                "scorecard": 1_440,
                "order": 43,
                "trade": 42,
                "missed": 104_391,
            },
            "ledger_row_counts": {
                "decision": 42_816,
                "scorecard": 1_440,
                "order": 108,
                "trade": 42,
                "missed": 104_391,
            },
        },
        fallback={},
    )

    assert counts == {
        "candidate": 104_434,
        "decision": 42_816,
        "scorecard": 1_440,
        "order": 108,
        "trade": 42,
        "missed": 104_391,
    }


def test_broad_quality_behavior_contract_preserves_legacy_schema() -> None:
    verifier = load_verifier()
    contract = verifier.normalize_broad_quality_behavior_summary(
        {
            "schema": (
                "gtos.final_moonshot.broad_live_as_if_replay.prefix_comparison.v1"
            ),
            "baseline_prefix": "BASE",
            "repair_prefix": "REPAIR",
            "live_broker_authority": False,
            "broker_mutation_enabled": False,
            "final_selection_claim": False,
            "repair_row_counts": {
                "candidate": 7,
                "decision": 11,
                "scorecard": 5,
                "order": 4,
                "trade": 2,
                "missed": 6,
            },
        }
    )

    assert contract["schema_supported"] is True
    assert contract["candidate_payload_valid"] is True
    assert contract["candidate_prefix"] == "REPAIR"
    assert contract["row_counts"] == {
        "candidate": 7,
        "decision": 11,
        "scorecard": 5,
        "order": 4,
        "trade": 2,
        "missed": 6,
    }


def test_broad_quality_behavior_contract_accepts_prefix_comparison_v2() -> None:
    verifier = load_verifier()
    contract = verifier.normalize_broad_quality_behavior_summary(
        {
            "schema": (
                "gtos.final_moonshot.broad_live_as_if_replay.prefix_comparison.v2"
            ),
            "baseline_prefix": "BASE",
            "repair_prefix": "REPAIR",
            "live_broker_authority": False,
            "broker_mutation_enabled": False,
            "final_selection_claim": False,
            "repair_row_counts": {
                "candidate": 25006,
                "decision": 11424,
                "scorecard": 288,
                "order": 45,
                "trade": 20,
                "missed": 24984,
            },
        }
    )

    assert contract["schema_supported"] is True
    assert contract["candidate_payload_valid"] is True
    assert contract["candidate_prefix"] == "REPAIR"
    assert contract["live_broker_authority"] is False
    assert contract["broker_mutation_enabled"] is False
    assert contract["final_selection_claim"] is False
    assert contract["row_counts"] == {
        "candidate": 25006,
        "decision": 11424,
        "scorecard": 288,
        "order": 45,
        "trade": 20,
        "missed": 24984,
    }


def test_broad_displacement_contract_rejects_repaired_origin_gate_drift(
    tmp_path,
) -> None:
    verifier = load_verifier()
    instance_key = "candidate-origin-drift@@2026-05-14T07:00:00+00:00"
    diagnostic = {
        "applies": True,
        "enabled": True,
        "allowed": True,
        "reason": (
            "no_primary_comparator_available_explicit_override_signed_package_"
            "edge_floor_allowed"
        ),
        "authority_family": "router_refusal_softening",
        "candidate_edge_score": 0.04,
        "edge_delta": None,
        "no_primary_min_edge_score": 0.0,
        "threshold_mode": "no_primary_absolute_expected_transfer_score",
        "signed_new_entry_authority_effective_valid_for_displacement": True,
        "broker_cost_executable": True,
        "router_refusal_origin_family_gate_enabled": False,
        "router_refusal_origin_family_allowed": True,
        "no_primary_comparator_override_allowed": True,
        "source_boundary": (
            "predecision_scheduler_displacement_quality_no_outcome_fields"
        ),
        "uses_outcome_fields": False,
    }
    option = {
        "candidate_id": "candidate-origin-drift",
        "canonical_replay_candidate_instance_key": instance_key,
        "profile": "repaired_package_conversion_v3",
        "scheduler_candidate_decision_inputs": {
            "package_displacement_quality": diagnostic,
        },
    }
    paths = {}
    for surface, row in {
        "candidate": option,
        "missed": option,
        "scorecard": {
            "profile": "repaired_package_conversion_v3",
            "scheduler_option_trace": [option],
        },
    }.items():
        path = tmp_path / f"{surface}.jsonl"
        path.write_text(json.dumps(row) + "\n", encoding="utf-8")
        paths[surface] = path

    scan = verifier.scan_broad_package_displacement_quality_contract(paths)

    assert scan["bad_counts"][
        "candidate:repaired_router_refusal_origin_gate_disabled"
    ] == 1


def test_replay_bridge_quality_scan_fails_signed_soft_transfer_outcome_usage() -> None:
    verifier = load_verifier()
    boundary = (
        "predecision_signed_package_soft_transfer_quality_cost_source_order_no_outcome_fields"
    )
    probe = {
        "candidate_id": "selected-signed-soft-transfer",
        "status": "selected",
        "source_boundary": "source_bound_asof_timewarp_decision_input",
        "candidate_decision_quality_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        "risk_finalizer_signed_soft_transfer_displacement_allowed": True,
        "risk_finalizer_signed_soft_transfer_displacement_source_boundary": boundary,
        "risk_finalizer_signed_soft_transfer_displacement_uses_outcome_fields": True,
        "pretrade_cost_packet_status": "PASSED",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "cost_authority": "broker_calibrated_replay_cost",
        "candidate_cost_r_fallback_is_authority": False,
        "package_replay_executable_candidate_use_allowed": True,
        "package_replay_order_executable_candidate_use_allowed": True,
        "source_completeness": 1.0,
        "source_completeness_status": "complete",
        "finalizer_admission_rank_reason": (
            "risk_admitted_signed_soft_transfer_displacement_rank"
        ),
    }

    scan = verifier.scan_replay_bridge_quality_parity(
        {},
        {
            "scorecard_fixture": [
                {
                    "selected_candidate_id": "selected-signed-soft-transfer",
                    "selected_candidate_ids": ["selected-signed-soft-transfer"],
                    "candidate_instance_identity_status": "materialized",
                    "risk_admitted_scheduler_finalizer": {"probe_rows": [probe]},
                }
            ]
        },
    )

    bad = scan["scorecard_provenance_bad_counts"]
    assert (
        bad[
            "scorecard_fixture.scorecard_probe:signed_soft_transfer:"
            "signed_soft_transfer_displacement_uses_outcome_fields_not_false"
        ]
        == 1
    )


def test_phase2_instance_completion_authority_requires_instance_sums() -> None:
    verifier = load_verifier()
    rows = [
        {
            "replay_candidate_id": "reused-candidate",
            "replay_instance_join_key": "reused-candidate@@2026-05-05T08:00:00+00:00",
            "target_value": {"counterfactual_final_r": 1.0},
        },
        {
            "replay_candidate_id": "reused-candidate",
            "replay_instance_join_key": "reused-candidate@@2026-05-05T08:15:00+00:00",
            "target_value": {"counterfactual_final_r": -0.25},
        },
    ]
    summary = {
        "phase2_proxy_target_unique_instance_final_r_sum": 0.75,
        "phase2_proxy_target_unique_instance_final_r_sum_authority": (
            "replay_instance_join_key_authority"
        ),
        "phase2_proxy_target_instance_rows": 2,
        "phase2_proxy_target_repeated_candidate_id_count": 1,
        "phase2_collapsed_unique_instance_proxy_final_r_sum": 0.75,
        "phase2_collapsed_unique_instance_proxy_final_r_sum_authority": (
            "replay_instance_join_key_authority"
        ),
        "phase2_collapsed_unique_replay_instance_count": 2,
        "phase2_collapsed_repeated_candidate_id_count": 1,
    }

    assert (
        verifier.phase2_instance_completion_authority_issues(
            summary=summary,
            completion_phase2_counts=dict(summary),
            phase2_proxy_target_label_rows=rows,
        )
        == []
    )

    bad_completion = {
        **summary,
        "phase2_proxy_target_unique_instance_final_r_sum": 1.0,
        "phase2_proxy_target_unique_instance_final_r_sum_authority": (
            "diagnostic_only_candidate_id_collapse"
        ),
        "phase2_proxy_target_instance_rows": 1,
        "phase2_proxy_target_repeated_candidate_id_count": 0,
        "phase2_collapsed_unique_instance_proxy_final_r_sum": 1.0,
        "phase2_collapsed_unique_instance_proxy_final_r_sum_authority": (
            "diagnostic_only_candidate_id_collapse"
        ),
        "phase2_collapsed_unique_replay_instance_count": 1,
        "phase2_collapsed_repeated_candidate_id_count": 0,
    }

    issues = verifier.phase2_instance_completion_authority_issues(
        summary=summary,
        completion_phase2_counts=bad_completion,
        phase2_proxy_target_label_rows=rows,
    )

    assert "completion_phase2_proxy_target_unique_instance_final_r_sum_mismatch" in issues
    assert (
        "completion_phase2_proxy_target_unique_instance_final_r_sum_authority_missing"
        in issues
    )
    assert "completion_phase2_proxy_target_instance_rows_mismatch" in issues
    assert "completion_phase2_proxy_target_repeated_candidate_id_count_mismatch" in issues
    assert (
        "completion_phase2_collapsed_unique_instance_proxy_final_r_sum_mismatch"
        in issues
    )
    assert (
        "completion_phase2_collapsed_unique_instance_proxy_final_r_sum_authority_missing"
        in issues
    )
    assert "completion_phase2_collapsed_unique_replay_instance_count_mismatch" in issues
    assert "completion_phase2_collapsed_repeated_candidate_id_count_mismatch" in issues


def test_verifier_result_exposes_phase2_instance_authority_root_keys() -> None:
    verifier = load_verifier()
    summary = {
        "phase2_proxy_target_unique_instance_final_r_sum": 0.75,
        "phase2_proxy_target_unique_instance_final_r_sum_authority": (
            "replay_instance_join_key_authority"
        ),
        "phase2_proxy_target_instance_rows": 2,
        "phase2_proxy_target_repeated_candidate_id_count": 1,
        "phase2_collapsed_unique_instance_proxy_final_r_sum": 0.75,
        "phase2_collapsed_unique_instance_proxy_final_r_sum_authority": (
            "replay_instance_join_key_authority"
        ),
        "phase2_collapsed_unique_replay_instance_count": 2,
        "phase2_collapsed_repeated_candidate_id_count": 1,
        "phase2_proxy_target_unique_candidate_final_r_sum": 99.0,
    }

    fields = verifier.phase2_instance_authority_result_fields(summary)

    assert set(fields) == set(verifier.PHASE2_INSTANCE_AUTHORITY_ROOT_KEYS)
    assert (
        fields["phase2_proxy_target_unique_instance_final_r_sum_authority"]
        == "replay_instance_join_key_authority"
    )
    assert fields["phase2_proxy_target_unique_instance_final_r_sum"] == 0.75
    assert "phase2_proxy_target_unique_candidate_final_r_sum" not in fields


def test_phase2_proxy_target_allowed_truth_scopes_include_source_bound_candidate_signal() -> None:
    verifier = load_verifier()

    assert verifier.PHASE2_PROXY_TARGET_ALLOWED_SOURCE_TRUTH_SCOPES == {
        "ordered_price_path_only_not_broker_order_lifecycle_truth",
        "source_bound_replay_candidate_signal_not_order_or_lifecycle_truth",
    }
    assert "proxy_target_contract_source_gap_not_materialized" in (
        verifier.PHASE2_UNMATERIALIZED_LABEL_VALUE_STATUSES
    )


def _write_broad_prefix_artifacts(verifier, tmp_path: Path, prefix: str) -> dict[str, Path]:
    verifier.ROOT = tmp_path
    verifier.ROUTE = tmp_path / "route"
    verifier.ROUTE.mkdir(parents=True, exist_ok=True)
    summary = {
        "status": "broad_live_as_if_replay_materialized_broker_live_closed",
        "live_broker_authority": False,
        "broker_mutation_enabled": False,
        "final_selection_claim": False,
        "candidate_ledger_omitted": True,
        "packet_sidecar_ledger_omitted": True,
        "comparison_ledger_rows": 0,
        "source_universe_rows": 1,
        "decision_rows": 1,
        "candidate_index_rows": 1,
        "candidate_index_rows_written": 1,
        "scorecard_rows": 1,
        "order_rows": 1,
        "oracle_rows": 1,
        "trade_rows": 1,
        "missed_opportunity_rows": 1,
        "bucket_rows": 1,
    }
    paths = verifier.broad_quality_artifact_paths(
        prefix,
        verifier.broad_quality_artifact_tag(prefix),
    )
    paths["summary"].write_text(json.dumps(summary), encoding="utf-8")
    paths["flow_summary"].write_text("{}", encoding="utf-8")
    for name in (
        "source_universe",
        "decision",
        "candidate_index",
        "scorecard",
        "order",
        "oracle",
        "trade",
        "missed",
        "bucket",
        "parity_ledger",
        "candidate_projection",
        "leakage_bucket",
    ):
        paths[name].write_text("{}\n", encoding="utf-8")
    for name in ("big_r", "parity_summary", "repair_plan"):
        paths[name].write_text("{}", encoding="utf-8")
    return paths


def test_broad_quality_artifact_paths_follow_producer_declared_paths(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    verifier.ROOT = tmp_path
    verifier.ROUTE = tmp_path / "route"
    verifier.ROUTE.mkdir(parents=True)
    prefix = "BROAD_LIVE_AS_IF_REPLAY_PRODUCER_BOUND"
    tag = verifier.broad_quality_artifact_tag(prefix)
    inferred = verifier.broad_quality_artifact_paths(prefix, tag)
    declared_candidate = verifier.ROUTE / "migrated_candidate_rows.jsonl"
    inferred["summary"].write_text(
        json.dumps(
            {
                "artifacts": {
                    "candidate": declared_candidate.name,
                }
            }
        ),
        encoding="utf-8",
    )
    declared_projection = verifier.ROUTE / "migrated_projection_rows.jsonl"
    inferred["parity_summary"].write_text(
        json.dumps(
            {
                "artifacts": {
                    "candidate_instance_parity_projection_ledger": (
                        declared_projection.name
                    )
                }
            }
        ),
        encoding="utf-8",
    )

    paths = verifier.broad_quality_artifact_paths(prefix, tag)
    assert paths["candidate"] == declared_candidate
    assert paths["candidate_projection"] == declared_projection


def test_broad_quality_artifact_paths_resolve_parity_summary_by_producer_prefix(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    verifier.ROOT = tmp_path
    verifier.ROUTE = tmp_path / "route"
    verifier.ROUTE.mkdir(parents=True)
    prefix = "BROAD_LIVE_AS_IF_REPLAY_V245_LONG_REPLAY_TAG"
    tag = verifier.broad_quality_artifact_tag(prefix)
    short_summary = (
        verifier.ROUTE
        / "SOURCE_BOUND_TO_EXECUTED_PARITY_V245_BOUND_PROOF_SUMMARY.json"
    )
    declared_projection = verifier.ROUTE / "v245_bound_projection.jsonl"
    short_summary.write_text(
        json.dumps(
            {
                "broad_replay_prefix": prefix,
                "artifacts": {
                    "candidate_instance_parity_projection_ledger": (
                        declared_projection.name
                    )
                },
            }
        ),
        encoding="utf-8",
    )

    paths = verifier.broad_quality_artifact_paths(prefix, tag)

    assert paths["parity_summary"] == short_summary
    assert paths["candidate_projection"] == declared_projection


def test_candidate_instance_projection_scan_reconciles_exact_funnel(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    path = tmp_path / "projection.jsonl"
    schema = (
        "gtos.final_moonshot.denominator_to_deployment."
        "candidate_instance_parity_projection.v1"
    )
    write_jsonl(
        path,
        [
            {
                "schema": schema,
                "row_type": "candidate_instance_parity_projection",
                "candidate_instance_parity_key": "candidate-a@@2026-05-13T10:00:00Z",
                "candidate_id": "candidate-a",
                "candidate_present": True,
                "scorecard_present": True,
                "scheduler_selected": True,
                "order_present": True,
                "trade_present": True,
                "missed_present": False,
            },
            {
                "schema": schema,
                "row_type": "candidate_instance_parity_projection",
                "candidate_instance_parity_key": "candidate-a@@2026-05-13T10:15:00Z",
                "candidate_id": "candidate-a",
                "candidate_present": True,
                "scorecard_present": True,
                "scheduler_selected": False,
                "order_present": False,
                "trade_present": False,
                "missed_present": True,
            },
        ],
    )

    scan = verifier.scan_candidate_instance_parity_projection(path)
    assert scan["bad_counts"] == {}
    assert scan["row_count"] == 2
    assert scan["unique_candidate_instance_parity_key_count"] == 2
    assert scan["duplicate_candidate_instance_parity_key_count"] == 0
    assert scan["stage_presence_counts"] == {
        "candidate": 2,
        "missed": 1,
        "order": 1,
        "scheduler_selected": 1,
        "scorecard": 2,
        "trade": 1,
    }
    assert scan["profile_stage_presence_counts"] == {
        "unknown": {
            "candidate": 2,
            "missed": 1,
            "order": 1,
            "scheduler_selected": 1,
            "scorecard": 2,
            "trade": 1,
        }
    }
    assert scan["package_candidate_identity_match_status_counts"] == {
        "missing": 2
    }


def _write_current_prefix_fixture(verifier, tmp_path: Path, prefix: str) -> dict[str, Path]:
    paths = _write_broad_prefix_artifacts(verifier, tmp_path, prefix)
    context_dir = tmp_path / ".context/context_os"
    context_dir.mkdir(parents=True, exist_ok=True)
    (context_dir / "CURRENT_ROOT_CAUSE_MAP.json").write_text(
        json.dumps({"latest_completed_replay": {"prefix": prefix}}),
        encoding="utf-8",
    )
    return paths


def _write_fable_matrix_fixture(
    tmp_path: Path,
    prefix: str,
    *,
    parity_built: bool = False,
) -> Path:
    version = f"V{prefix.split('_V', 1)[1].split('_', 1)[0]}"
    path = (
        tmp_path
        / ".context/context_os/fable_ultimate_plan/FABLE_EXECUTION_MATRIX_20260710.md"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    parity_section = ""
    if parity_built:
        parity_section = (
            f"\n## {version} Parity Completion Update\n\n"
            f"{version} source-bound-to-executed parity and leakage artifacts "
            "materialized.\n"
        )
    path.write_text(
        "# Fable Execution Matrix\n\n"
        "## Latest Completed Replay\n\n"
        f"Prefix:\n`{prefix}`\n"
        f"{parity_section}",
        encoding="utf-8",
    )
    return path


def test_current_root_prefix_binding_rejects_stale_broad_quality_selection(tmp_path) -> None:
    verifier = load_verifier()
    _write_current_prefix_fixture(verifier, tmp_path, "CURRENT_PREFIX")

    issues = verifier.broad_quality_current_root_prefix_binding_issues(
        "OLDER_SELECTED_PREFIX",
        {},
    )

    assert (
        "broad_quality_current_root_prefix_mismatch:"
        "expected=CURRENT_PREFIX;selected=OLDER_SELECTED_PREFIX"
        in issues
    )
    assert (
        verifier.broad_quality_current_root_prefix_binding_issues(
            "CURRENT_PREFIX",
            {},
        )
        == []
    )


def test_current_prefix_contract_prefers_newer_fable_replay_over_stale_pins(
    tmp_path: Path,
    monkeypatch,
) -> None:
    verifier = load_verifier()
    old_prefix = "BROAD_LIVE_AS_IF_REPLAY_V218_TARGETED"
    current_prefix = "BROAD_LIVE_AS_IF_REPLAY_V219_HOSTILE_FULLGRID"
    _write_broad_prefix_artifacts(verifier, tmp_path, old_prefix)
    _write_broad_prefix_artifacts(verifier, tmp_path, current_prefix)
    matrix_path = _write_fable_matrix_fixture(tmp_path, current_prefix)
    context_dir = tmp_path / ".context/context_os"
    (context_dir / "CURRENT_ROOT_CAUSE_MAP.json").write_text(
        json.dumps(
            {
                "latest_completed_replay": {"prefix": old_prefix},
                "fable_execution_matrix": str(matrix_path.relative_to(tmp_path)),
            }
        ),
        encoding="utf-8",
    )
    (context_dir / "CONTINUATION_CURSOR.json").write_text(
        json.dumps({"latest_completed_replay_prefix": old_prefix}),
        encoding="utf-8",
    )
    stale_manifest = {"broad_quality_parity_prefix": old_prefix}
    selection_issues: list[str] = []

    selected_prefix, _tag, _paths = verifier.select_broad_quality_parity_artifacts(
        selection_issues,
        stale_manifest,
    )
    assert selected_prefix == current_prefix
    assert any(
        issue.startswith(
            "broad_quality_manifest_pinned_prefix_stale_newer_completed_prefix_available:"
        )
        for issue in selection_issues
    )

    monkeypatch.setenv("GTOS_BROAD_QUALITY_PARITY_PREFIX", old_prefix)

    assert verifier.current_root_cause_map_broad_quality_prefix(stale_manifest) == current_prefix
    assert verifier.current_root_cause_map_broad_quality_prefixes()[0] == current_prefix
    assert verifier.broad_quality_current_root_prefix_binding_issues(
        current_prefix,
        stale_manifest,
    ) == []
    issues = verifier.broad_quality_current_root_prefix_binding_issues(
        old_prefix,
        stale_manifest,
    )
    assert (
        "broad_quality_current_root_prefix_mismatch:"
        f"expected={current_prefix};selected={old_prefix}"
        in issues
    )


def test_current_prefix_contract_orders_revision_prefix_after_older_base_version(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    old_prefix = "BROAD_LIVE_AS_IF_REPLAY_V219_HOSTILE_FULLGRID"
    stale_revision_prefix = "BROAD_LIVE_AS_IF_REPLAY_V220R15_TERMINAL_RECONCILIATION"
    current_prefix = "BROAD_LIVE_AS_IF_REPLAY_V220R16_CANONICAL_TERMINAL_INDEX"
    for prefix in (old_prefix, stale_revision_prefix, current_prefix):
        _write_broad_prefix_artifacts(verifier, tmp_path, prefix)
    matrix_path = _write_fable_matrix_fixture(tmp_path, current_prefix)
    context_dir = tmp_path / ".context/context_os"
    (context_dir / "CURRENT_ROOT_CAUSE_MAP.json").write_text(
        json.dumps(
            {
                "latest_completed_replay": {"prefix": old_prefix},
                "fable_execution_matrix": str(matrix_path.relative_to(tmp_path)),
            }
        ),
        encoding="utf-8",
    )
    (context_dir / "CONTINUATION_CURSOR.json").write_text(
        json.dumps({"latest_completed_replay_prefix": stale_revision_prefix}),
        encoding="utf-8",
    )

    assert verifier.broad_replay_prefix_version(current_prefix) == 220
    assert verifier.broad_replay_prefix_sort_key(old_prefix) == (219, 0)
    assert verifier.broad_replay_prefix_sort_key(stale_revision_prefix) == (220, 15)
    assert verifier.broad_replay_prefix_sort_key(current_prefix) == (220, 16)
    assert verifier.current_control_broad_quality_prefix({}) == current_prefix


def test_current_prefix_contract_uses_latest_complete_replay_when_newer_is_compact_retained(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    complete_prefix = "BROAD_LIVE_AS_IF_REPLAY_V250_COMPLETE_QUALITY"
    retained_prefix = "BROAD_LIVE_AS_IF_REPLAY_V257_COMPACT_RETAINED"
    _write_broad_prefix_artifacts(verifier, tmp_path, complete_prefix)
    retained_paths = _write_broad_prefix_artifacts(
        verifier,
        tmp_path,
        retained_prefix,
    )
    retained_paths["decision"].unlink()
    retained_paths["scorecard"].unlink()
    retained_paths["missed"].unlink()
    matrix_path = _write_fable_matrix_fixture(tmp_path, retained_prefix)
    context_dir = tmp_path / ".context/context_os"
    (context_dir / "CURRENT_ROOT_CAUSE_MAP.json").write_text(
        json.dumps(
            {
                "latest_completed_replay_prefix": complete_prefix,
                "fable_execution_matrix": str(matrix_path.relative_to(tmp_path)),
            }
        ),
        encoding="utf-8",
    )
    (context_dir / "CONTINUATION_CURSOR.json").write_text(
        json.dumps({"latest_completed_replay_prefix": retained_prefix}),
        encoding="utf-8",
    )

    assert verifier.current_control_broad_quality_prefix({}) == complete_prefix


def test_current_prefix_contract_requires_flow_and_built_parity_artifacts(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    prefix = "BROAD_LIVE_AS_IF_REPLAY_V219_HOSTILE_FULLGRID"
    paths = _write_current_prefix_fixture(verifier, tmp_path, prefix)
    matrix_path = _write_fable_matrix_fixture(tmp_path, prefix, parity_built=True)
    root_map_path = tmp_path / ".context/context_os/CURRENT_ROOT_CAUSE_MAP.json"
    root_map_path.write_text(
        json.dumps(
            {
                "latest_completed_replay": {"prefix": prefix},
                "fable_execution_matrix": str(matrix_path.relative_to(tmp_path)),
            }
        ),
        encoding="utf-8",
    )
    paths["flow_summary"].unlink()
    paths["parity_ledger"].unlink()

    state = verifier.fable_execution_matrix_current_prefix_state(
        verifier.current_root_cause_map_payload()
    )
    assert state["latest_completed_replay_prefix"] == prefix
    assert state["parity_built_versions"] == [219]
    issues = verifier.broad_quality_current_root_prefix_binding_issues(prefix, {})
    missing_issue = next(
        issue
        for issue in issues
        if issue.startswith(
            "broad_quality_current_root_prefix_missing_or_empty_artifacts:"
        )
    )
    assert "flow_summary" in missing_issue
    assert "parity_ledger" in missing_issue


def _canonical_quality_fixture() -> dict:
    sources = {
        "expected_net_r": "packets.candidate_expected_net_r",
        "probability": "packets.candidate_probability",
        "source_completeness": "candidate.source_completeness",
    }
    return {
        "candidate_id": "candidate-selected",
        "selected_candidate_id": "candidate-selected",
        "expected_net_r": 0.8,
        "candidate_expected_net_r": 0.8,
        "probability": 0.7,
        "candidate_probability": 0.7,
        "source_completeness": 1.0,
        "candidate_decision_quality_field_sources": dict(sources),
        "candidate_decision_quality": {
            "expected_net_r": 0.8,
            "candidate_expected_net_r": 0.8,
            "probability": 0.7,
            "candidate_probability": 0.7,
            "source_completeness": 1.0,
            "field_sources": dict(sources),
        },
    }


def test_selected_quality_contract_requires_one_canonical_source_and_matching_aliases() -> None:
    verifier = load_verifier()
    valid = _canonical_quality_fixture()

    assert verifier.selected_quality_source_contract_reasons(valid) == []

    multiple_source = json.loads(json.dumps(valid))
    multiple_source["candidate_decision_quality_field_sources"]["expected_net_r"] = [
        "source-a",
        "source-b",
    ]
    reasons = verifier.selected_quality_source_contract_reasons(multiple_source)
    assert "canonical_quality_source_not_single_scalar:expected_net_r" in reasons

    stale_alias = json.loads(json.dumps(valid))
    stale_alias["candidate_probability"] = 0.2
    reasons = verifier.selected_quality_source_contract_reasons(stale_alias)
    assert "canonical_quality_compatibility_alias_mismatch:candidate_probability" in reasons


def test_zero_trade_scorecard_quality_must_remain_explicitly_reported_or_probe_scoped() -> None:
    verifier = load_verifier()
    sources = {
        "expected_net_r": "packets.candidate_expected_net_r",
        "probability": "packets.candidate_probability",
        "source_completeness": "candidate.source_completeness",
    }
    zero_trade = {
        "candidate_id": "window-reported-probe",
        "selected_candidate_id": None,
        "selected_candidate_ids": [],
        "candidate_decision_quality": {
            "selected_policy_for_expected_net_r": "momentum_exhaustion"
        },
        "scorecard_reported_expected_net_r": 0.8,
        "scorecard_reported_probability": 0.7,
        "scorecard_reported_source_completeness": 1.0,
        "scorecard_reported_candidate_decision_quality_field_sources": dict(sources),
        "scorecard_reported_candidate_decision_quality": {
            "expected_net_r": 0.8,
            "probability": 0.7,
            "source_completeness": 1.0,
            "field_sources": dict(sources),
        },
    }

    assert (
        verifier.zero_trade_scorecard_quality_source_contract_reasons(zero_trade)
        == []
    )

    stale = dict(zero_trade)
    stale["expected_net_r"] = 0.1
    reasons = verifier.zero_trade_scorecard_quality_source_contract_reasons(stale)
    assert (
        "zero_trade_scorecard_stale_top_level_quality_alias:expected_net_r"
        in reasons
    )

    stale_nested = json.loads(json.dumps(zero_trade))
    stale_nested["candidate_decision_quality"]["expected_net_r"] = 0.1
    reasons = verifier.zero_trade_scorecard_quality_source_contract_reasons(
        stale_nested
    )
    assert (
        "zero_trade_scorecard_stale_top_level_quality_alias:"
        "candidate_decision_quality.expected_net_r"
        in reasons
    )


def test_broad_selected_quality_scan_checks_scorecard_order_and_trade_rows(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    selected_scorecard = _canonical_quality_fixture()
    selected_order = _canonical_quality_fixture()
    selected_trade = _canonical_quality_fixture()
    selected_trade["candidate_decision_quality_field_sources"] = {
        "expected_net_r": "packets.candidate_expected_net_r",
        "probability": "packets.candidate_probability",
    }
    zero_trade = {
        "candidate_id": "window-reported-probe",
        "selected_candidate_id": None,
        "selected_candidate_ids": [],
        "scorecard_reported_expected_net_r": 0.8,
        "scorecard_reported_probability": 0.7,
        "scorecard_reported_source_completeness": 1.0,
        "scorecard_reported_candidate_decision_quality_field_sources": {
            "expected_net_r": "packets.candidate_expected_net_r",
            "probability": "packets.candidate_probability",
            "source_completeness": "candidate.source_completeness",
        },
    }
    paths = {
        "scorecard": tmp_path / "scorecard.jsonl",
        "order": tmp_path / "order.jsonl",
        "trade": tmp_path / "trade.jsonl",
    }
    paths["scorecard"].write_text(
        "\n".join(json.dumps(row) for row in (zero_trade, selected_scorecard)) + "\n",
        encoding="utf-8",
    )
    paths["order"].write_text(json.dumps(selected_order) + "\n", encoding="utf-8")
    paths["trade"].write_text(json.dumps(selected_trade) + "\n", encoding="utf-8")

    scan = verifier.scan_broad_selected_quality_source_contract(paths)

    assert scan["row_counts"] == {
        "order_rows": 1,
        "scorecard_rows": 2,
        "selected_order_rows": 1,
        "selected_scorecard_rows": 1,
        "selected_trade_rows": 1,
        "trade_rows": 1,
        "zero_trade_scorecard_rows": 1,
    }
    assert scan["bad_counts"] == {
        "trade:canonical_quality_source_missing:source_completeness": 1
    }


def test_snapshot_count_pins_are_opt_in(tmp_path) -> None:
    verifier = load_verifier()
    built_in = {"rows": 10}
    pin_path = tmp_path / "pin.json"
    pin_path.write_text(json.dumps({"expected_counts": {"rows": 11}}), encoding="utf-8")

    assert verifier.snapshot_expected_count_pins(built_in, argv=[]) == {}
    assert verifier.snapshot_expected_count_pins(built_in, argv=["--pin-snapshot", str(pin_path)]) == {
        "rows": 11
    }
    assert verifier.snapshot_expected_count_pins(built_in, argv=["--pin-snapshot=builtin"]) == {
        "rows": 10
    }


def test_broker_cost_refusal_histogram_counts_list_reasons_by_family(tmp_path) -> None:
    audit = load_audit()
    audit.ROUTE_DIR = tmp_path
    prefix = "COST_PREFIX"
    candidate_path = tmp_path / f"{prefix}_CANDIDATE_INDEX_LEDGER.jsonl"
    candidate_path.write_text(
        json.dumps(
            {
                "candidate_id": "cand-1",
                "decision_time_utc": "2026-05-15T08:00:00+00:00",
                "symbol": "XAUUSD",
                "session": "london",
                "pretrade_cost_packet_status": "REFUSED",
                "pretrade_cost_refusal_reasons": [
                    "total_cost_r_exceeds_limit:0.37",
                    "missing_side_aware_swap_cost_r_conversion:swap_mode",
                ],
                "broker_cost_spread_floor_source": "measured_mt5_tick_spread_floor",
                "cost_quality_source": "broker_calibrated",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = audit.broker_cost_refusal_histogram(prefix)

    assert result["refused_rows"] == 1
    assert result["refused_reason_instances"] == 2
    families = {row["refusal_reason_family"] for row in result["histogram"]}
    assert families == {
        "total_cost_r_exceeds_limit",
        "missing_side_aware_swap_cost_r_conversion",
    }
    assert {row["spread_floor_source_status"] for row in result["histogram"]} == {
        "present_spread_floor_source"
    }
    assert {row["cost_quality_source"] for row in result["histogram"]} == {
        "broker_calibrated"
    }


def _identity_row(candidate_id: str, decision_time: str, **updates) -> dict:
    key = f"{candidate_id}@@{decision_time}"
    row = {
        "candidate_id": candidate_id,
        "decision_time_utc": decision_time,
        "candidate_instance_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": key,
        "risk_finalizer_probe_instance_key": key,
        "source_bound_replay_candidate_instance_key": key,
        "candidate_instance_identity_status": "materialized",
    }
    row.update(updates)
    return row


def test_cross_ledger_candidate_instance_identity_keeps_reused_ids_exact() -> None:
    verifier = load_verifier()
    candidate_id = "reused-candidate"
    first_time = "2026-05-13T00:15:00+00:00"
    selected_time = "2026-05-13T00:30:00+00:00"
    selected_key = f"{candidate_id}@@{selected_time}"
    scan = verifier.scan_cross_ledger_candidate_instance_identity(
        {
            "candidate": [
                _identity_row(candidate_id, first_time),
                _identity_row(candidate_id, selected_time),
            ],
            "scorecard": [
                {
                    "selected_candidate_instance_keys": [selected_key],
                    "risk_admitted_final_selected_candidate_instance_keys": [
                        selected_key
                    ],
                    "risk_admitted_scheduler_finalizer": {
                        "probe_rows": [
                            _identity_row(candidate_id, selected_time, selected=True)
                        ]
                    },
                }
            ],
            "order": [_identity_row(candidate_id, selected_time)],
            "trade": [_identity_row(candidate_id, selected_time)],
            "missed": [_identity_row(candidate_id, first_time)],
            "disposition": [
                _identity_row(
                    candidate_id,
                    selected_time,
                    bound_order_rows=1,
                    bound_trade_rows=1,
                )
            ],
        }
    )

    assert scan["bad_counts"] == {}
    assert scan["candidate_instance_count"] == 2
    assert scan["selected_instance_count"] == 1


def test_cross_ledger_candidate_identity_accepts_selected_instance_without_probe() -> None:
    verifier = load_verifier()
    candidate_id = "selected-without-finalizer-probe"
    decision_time = "2026-05-13T11:00:00+00:00"
    selected_key = f"{candidate_id}@@{decision_time}"

    scan = verifier.scan_cross_ledger_candidate_instance_identity(
        {
            "candidate": [_identity_row(candidate_id, decision_time)],
            "scorecard": [
                {
                    "selected_candidate_instance_keys": [selected_key],
                    "risk_admitted_final_selected_candidate_instance_keys": [
                        selected_key
                    ],
                }
            ],
            "order": [
                _identity_row(
                    candidate_id,
                    decision_time,
                    order_status="pending_accepted",
                ),
                _identity_row(
                    candidate_id,
                    decision_time,
                    order_status="cancelled_replaced_by_scheduler_v4",
                ),
            ],
            "trade": [],
            "missed": [],
            "disposition": [],
        }
    )

    assert scan["bad_counts"] == {}
    assert scan["selected_instance_count"] == 1
    assert scan["probed_instance_count"] == 0


@pytest.mark.parametrize(
    ("ledger", "expected_reason"),
    (
        ("probe", "probe:canonical_replay_candidate_instance_key_tuple_mismatch"),
        ("order", "order:canonical_replay_candidate_instance_key_tuple_mismatch"),
        ("trade", "trade:canonical_replay_candidate_instance_key_tuple_mismatch"),
        ("missed", "missed:canonical_replay_candidate_instance_key_tuple_mismatch"),
        (
            "disposition",
            "disposition:canonical_replay_candidate_instance_key_tuple_mismatch",
        ),
    ),
)
def test_cross_ledger_candidate_instance_identity_rejects_time_swaps(
    ledger: str,
    expected_reason: str,
) -> None:
    verifier = load_verifier()
    candidate_id = "reused-candidate"
    first_time = "2026-05-13T00:15:00+00:00"
    second_time = "2026-05-13T00:30:00+00:00"
    stale_key = f"{candidate_id}@@{first_time}"
    mutated = _identity_row(candidate_id, second_time)
    mutated["canonical_replay_candidate_instance_key"] = stale_key
    groups = {
        "candidate": [
            _identity_row(candidate_id, first_time),
            _identity_row(candidate_id, second_time),
        ],
        "scorecard": [],
        "order": [],
        "trade": [],
        "missed": [],
        "disposition": [],
    }
    if ledger == "probe":
        groups["scorecard"] = [
            {"risk_admitted_scheduler_finalizer": {"probe_rows": [mutated]}}
        ]
    else:
        groups[ledger] = [mutated]

    scan = verifier.scan_cross_ledger_candidate_instance_identity(groups)

    assert scan["bad_counts"][expected_reason] == 1


def test_signed_authority_verifier_rejects_spoofed_predecision_fill_source() -> None:
    verifier = load_verifier()
    fields = signed_package_new_entry_fields(
        candidate_id="unsafe-fill-source",
        decision_time_utc="2026-05-13T00:15:00+00:00",
    )
    fields = resign_signed_package_new_entry_fields(
        fields,
        execution_fill_probability_source=(
            "post_trade_predecision_limit_fillability"
        ),
    )

    reasons = verifier.signed_package_new_entry_authority_reasons(
        {
            **fields,
            "candidate_id": "unsafe-fill-source",
            "decision_time_utc": "2026-05-13T00:15:00+00:00",
            "canonical_replay_candidate_instance_key": (
                "unsafe-fill-source@@2026-05-13T00:15:00+00:00"
            ),
            "source_bound_replay_candidate_instance_key": (
                "unsafe-fill-source@@2026-05-13T00:15:00+00:00"
            ),
            "candidate_instance_identity_status": "materialized",
            "selector_action": "reduce-risk",
            "selector_reason": "unit_test_authority",
            "scheduler_materialization_action_intent": "new_position",
        },
        action_intent="new_position",
        require_immutable_payload=True,
    )

    assert "package_new_entry_authority_payload_fill_source_unsafe" in reasons


def test_order_transfer_scan_separates_attempt_identity_from_executable_binding(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    order_path = tmp_path / "terminal-order.jsonl"
    missed_path = tmp_path / "counterfactual-missed.jsonl"
    write_jsonl(
        order_path,
        [
            {
                "candidate_id": "terminal-order-attempt",
                "simulated_order_id": "attempt-order-id",
                "package_replay_order_executable_candidate_use_allowed": False,
                "package_replay_order_executable_transfer_status": "final_blocked",
                "package_replay_order_executable_final_blocker_class": (
                    "marketable_guard"
                ),
                "package_replay_order_executable_final_blocker_reason": (
                    "package_marketable_limit_entry_guard_blocked"
                ),
                "package_replay_order_executable_final_blocker_source": (
                    "package_order_executable_final_blocker_fields"
                ),
                "order_status": "guarded_market_fallback_contract_unmet",
                "fill_status": "not_sent_guarded_market_fallback_contract_unmet",
            }
        ],
    )
    write_jsonl(
        missed_path,
        [
            {
                "candidate_id": "counterfactual-immediate-route",
                "package_replay_order_executable_candidate_use_allowed": False,
                "package_replay_order_executable_transfer_status": "final_blocked",
                "package_replay_order_executable_final_blocker_class": (
                    "scheduler_selection"
                ),
                "package_replay_order_executable_final_blocker_reason": (
                    "scheduler_option_status_not_executable:candidate_vetoed"
                ),
                "package_replay_order_executable_final_blocker_source": (
                    "reason_surface[0].risk_decision_reason"
                ),
                "package_marketable_entry_guard_status": (
                    "routed_to_immediate_marketable_limit_replay_order_policy"
                ),
                "order_execution_path": "counterfactual_not_selected_policy_plan",
                "order_status": "not_sent_missed_opportunity",
            }
        ],
    )

    scan = verifier.scan_broad_order_executable_transfer_contract(
        {"order": order_path, "missed": missed_path}
    )

    assert scan["bad_counts"].get(
        "order:blocked_row_has_bound_order_or_trade_id", 0
    ) == 0
    assert scan["bad_counts"].get(
        "missed:immediate_marketable_route_final_blocker_missing", 0
    ) == 0


def test_entry_fill_terminal_r_lifecycle_contract_partitions_fill_and_expiry(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    order_path = tmp_path / "orders.jsonl"
    trade_path = tmp_path / "trades.jsonl"
    terminal_status = (
        "entry_fill_executable_terminal_r_ordered_tick_sequence_required"
    )
    write_jsonl(
        order_path,
        [
            {
                "simulated_order_id": "filled-order",
                "candidate_id": "filled-candidate",
                "order_intent_materialized": True,
                "order_status": "pending_accepted",
                "is_terminal_order_event": False,
            },
            {
                "simulated_order_id": "filled-order",
                "candidate_id": "filled-candidate",
                "order_intent_materialized": True,
                "order_status": "filled",
                "is_terminal_order_event": True,
                "entry_fill_executable": True,
                "terminal_r_scoreable": False,
                "terminal_r_scoreability_status": terminal_status,
                "accepted_risk_budget_consumed_by_fill": True,
                "accepted_risk_reservation_released": False,
                "accepted_risk_reservation_transition": (
                    "pending_order_to_filled_position"
                ),
                "final_r": None,
                "gross_r": None,
                "net_proxy_r": None,
                "pnl_cash": None,
            },
            {
                "simulated_order_id": "expired-order",
                "candidate_id": "expired-candidate",
                "order_intent_materialized": True,
                "order_status": "pending_accepted",
                "is_terminal_order_event": False,
            },
            {
                "simulated_order_id": "expired-order",
                "candidate_id": "expired-candidate",
                "order_intent_materialized": True,
                "order_status": "expired_unfilled",
                "is_terminal_order_event": True,
                "entry_fill_executable": False,
                "terminal_r_scoreable": False,
                "accepted_risk_budget_consumed_by_fill": False,
                "accepted_risk_reservation_released": True,
            },
        ],
    )
    write_jsonl(
        trade_path,
        [
            {
                "simulated_order_id": "filled-order",
                "simulated_trade_id": "filled-trade",
                "candidate_id": "filled-candidate",
                "entry_fill_executable": True,
                "terminal_r_scoreable": False,
                "terminal_r_scoreability_status": terminal_status,
                "trade_state": "closed_terminal_r_unscoreable",
                "result_scoreable": False,
                "result_scope": "executed_entry_terminal_r_unscoreable",
                "package_execution_result_scope": (
                    "entry_fill_executable_terminal_r_unscoreable"
                ),
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
            }
        ],
    )

    scan = verifier.scan_broad_entry_fill_terminal_r_lifecycle_contract(
        {"order": order_path, "trade": trade_path}
    )

    assert scan["bad_counts"] == {}
    assert scan["row_counts"]["unique_materialized_order_intents"] == 2
    assert scan["row_counts"]["terminal_filled_order_intents"] == 1
    assert scan["row_counts"]["terminal_unfilled_order_intents"] == 1
    assert scan["row_counts"]["order_terminal_r_unscoreable_rows"] == 1
    assert scan["row_counts"]["order_terminal_r_not_applicable_no_entry_rows"] == 1
    assert scan["row_counts"]["trade_terminal_r_unscoreable_rows"] == 1


def test_entry_fill_terminal_r_lifecycle_contract_rejects_unscoreable_r_claim(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    trade_path = tmp_path / "bad-trades.jsonl"
    write_jsonl(
        trade_path,
        [
            {
                "simulated_order_id": "bad-order",
                "simulated_trade_id": "bad-trade",
                "candidate_id": "bad-candidate",
                "entry_fill_executable": True,
                "terminal_r_scoreable": False,
                "trade_state": "closed_terminal_r_unscoreable",
                "result_scoreable": False,
                "accepted_risk_budget_consumed_by_fill": True,
                "accepted_risk_reservation_released": False,
                "raw_gross_r": 1.0,
            }
        ],
    )

    scan = verifier.scan_broad_entry_fill_terminal_r_lifecycle_contract(
        {"trade": trade_path}
    )

    assert scan["bad_counts"][
        "trade:terminal_r_unscoreable_carries_raw_gross_r"
    ] == 1


def test_entry_fill_terminal_r_lifecycle_contract_requires_factorial_close_release(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    trade_path = tmp_path / "factorial-trades.jsonl"
    write_jsonl(
        trade_path,
        [
            {
                "simulated_order_id": "factorial-order",
                "simulated_trade_id": "factorial-trade",
                "candidate_id": "factorial-candidate",
                "entry_fill_executable": True,
                "terminal_r_scoreable": True,
                "result_scoreable": True,
                "trade_state": "closed",
                "accepted_risk_budget_consumed_by_fill": True,
                "accepted_risk_reservation_released": True,
                "accepted_risk_reservation_transition": (
                    "pending_order_to_filled_position"
                ),
                "accepted_risk_close_release_once_status": (
                    "released_exactly_once_at_terminal_close"
                ),
                "accepted_risk_reservation_release": {
                    "released_risk_pct": 0.625,
                    "day_accepted_risk_pct_before_release": 0.625,
                    "day_accepted_risk_pct_after_release": 0.0,
                },
                "b7_5_selection_sizing_factorial_arm_id": "S1R1",
                "b7_5_selection_sizing_factorial_expiry_or_close_release_once": True,
                "final_r": 1.0,
                "gross_r": 1.0,
                "net_proxy_r": 0.9,
                "net_r": 0.9,
                "pnl_cash": 90.0,
            }
        ],
    )

    scan = verifier.scan_broad_entry_fill_terminal_r_lifecycle_contract(
        {"trade": trade_path}
    )

    assert scan["bad_counts"] == {}
    assert scan["row_counts"][
        "trade_factorial_close_release_required_rows"
    ] == 1


def test_factorial_risk_lifecycle_summary_scan_requires_valid_terminal_zero_audit() -> None:
    verifier = load_verifier()
    matched_risk = {
        "daily_accepted_risk_pct_cap": 4.0,
        "peak_open_plus_pending_risk_pct_cap": 4.0,
        "cluster_risk_pct_cap": 1.5,
        "opening_window_risk_pct_cap": 1.0,
        "pending_to_open_transfer_once": True,
        "expiry_or_close_release_once": True,
        "same_ex_ante_rules_all_arms": True,
        "ex_post_rescaling_forbidden": True,
    }
    summary = {
        "b7_5_selection_sizing_factorial_arm_binding": {
            "arm_id": "S1R1",
            "valid": True,
            "matched_risk": matched_risk,
        },
        "b7_5_selection_sizing_factorial_risk_lifecycle": {
            "status": "factorial_risk_lifecycle_contract_valid",
            "required": True,
            "valid": True,
            "arm_id": "S1R1",
            "matched_risk": matched_risk,
            "accepted_order_count": 2,
            "close_or_expiry_event_count": 2,
            "close_or_expiry_release_count": 2,
            "peak_daily_accepted_risk_pct": 0.625,
            "peak_open_plus_pending_risk_pct": 0.625,
            "peak_opening_window_risk_pct": 0.625,
            "peak_cluster_risk_pct": {"usd_fx": 0.625},
            "terminal_daily_accepted_risk_pct": 0.0,
            "terminal_pending_risk_pct": 0.0,
            "terminal_open_risk_pct": 0.0,
            "failure_count": 0,
            "failures": [],
            "uses_outcome_fields_for_selection_or_sizing": False,
            "broker_mutation_enabled": False,
            "live_broker_authority": False,
        },
    }

    scan = verifier.scan_broad_factorial_risk_lifecycle_summary(summary)

    assert scan["required"] is True
    assert scan["status"] == "factorial_risk_lifecycle_summary_valid"
    assert scan["bad_counts"] == {}

    missing = dict(summary)
    missing.pop("b7_5_selection_sizing_factorial_risk_lifecycle")
    missing_scan = verifier.scan_broad_factorial_risk_lifecycle_summary(missing)
    assert missing_scan["bad_counts"][
        "factorial_risk_lifecycle_summary_audit_missing"
    ] == 1

    invalid = json.loads(json.dumps(summary))
    invalid_audit = invalid["b7_5_selection_sizing_factorial_risk_lifecycle"]
    invalid_audit["valid"] = False
    invalid_audit["terminal_open_risk_pct"] = 0.625
    invalid_audit["peak_daily_accepted_risk_pct"] = 99.0
    invalid_scan = verifier.scan_broad_factorial_risk_lifecycle_summary(invalid)
    assert invalid_scan["bad_counts"][
        "factorial_risk_lifecycle_summary_audit_not_valid"
    ] == 1
    assert invalid_scan["bad_counts"][
        "factorial_risk_lifecycle_summary_terminal_risk_not_zero"
    ] == 1
    assert invalid_scan["bad_counts"][
        "factorial_risk_lifecycle_summary_peak_cap_breached"
    ] == 1

    nan_invalid = json.loads(json.dumps(summary))
    nan_binding = nan_invalid["b7_5_selection_sizing_factorial_arm_binding"]
    nan_audit = nan_invalid[
        "b7_5_selection_sizing_factorial_risk_lifecycle"
    ]
    nan_audit["peak_opening_window_risk_pct"] = float("nan")
    nan_binding["matched_risk"]["cluster_risk_pct_cap"] = float("nan")
    nan_audit["matched_risk"]["cluster_risk_pct_cap"] = float("nan")
    nan_scan = verifier.scan_broad_factorial_risk_lifecycle_summary(nan_invalid)
    assert nan_scan["bad_counts"][
        "factorial_risk_lifecycle_summary_peak_missing_or_invalid"
    ] == 1
    assert nan_scan["bad_counts"][
        "factorial_risk_lifecycle_summary_cluster_cap_missing_or_invalid"
    ] == 1


def test_entry_fill_lifecycle_cross_stage_ignores_scheduler_mutation_order_row(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    order_path = tmp_path / "scheduler-mutation-orders.jsonl"
    trade_path = tmp_path / "scheduler-mutation-trades.jsonl"
    order_id = "factorial-scheduler-order"
    common = {
        "simulated_order_id": order_id,
        "candidate_id": "factorial-scheduler-candidate",
        "order_intent_materialized": True,
    }
    write_jsonl(
        order_path,
        [
            {
                **common,
                "order_event_stage": "accepted_pending",
                "is_terminal_order_event": False,
                "entry_fill_executable": False,
                "terminal_r_scoreable": False,
            },
            {
                **common,
                "order_event_stage": "terminal_filled",
                "is_terminal_order_event": True,
                "order_status": "filled",
                "entry_fill_executable": True,
                "terminal_r_scoreable": True,
                "accepted_risk_budget_consumed_by_fill": True,
                "accepted_risk_reservation_released": False,
                "accepted_risk_reservation_transition": (
                    "pending_order_to_filled_position"
                ),
            },
            {
                **common,
                "order_event_stage": (
                    "terminal_lifecycle_open_position_state_mutation"
                ),
                "is_terminal_order_event": False,
                "entry_fill_executable": True,
                "terminal_r_scoreable": True,
                "accepted_risk_budget_consumed_by_fill": True,
                "accepted_risk_reservation_released": True,
            },
        ],
    )
    write_jsonl(
        trade_path,
        [
            {
                **common,
                "simulated_trade_id": "factorial-scheduler-trade",
                "entry_fill_executable": True,
                "terminal_r_scoreable": True,
                "result_scoreable": True,
                "trade_state": "closed",
                "accepted_risk_budget_consumed_by_fill": True,
                "accepted_risk_reservation_released": True,
                "accepted_risk_reservation_transition": (
                    "pending_order_to_filled_position"
                ),
                "accepted_risk_close_release_once_status": (
                    "released_exactly_once_at_terminal_close"
                ),
                "accepted_risk_reservation_release": {
                    "released_risk_pct": 0.625,
                },
                "b7_5_selection_sizing_factorial_arm_id": "S1R1",
                "b7_5_selection_sizing_factorial_expiry_or_close_release_once": True,
                "final_r": 1.0,
                "gross_r": 1.0,
                "net_proxy_r": 0.9,
                "net_r": 0.9,
                "pnl_cash": 562.5,
            }
        ],
    )

    scan = verifier.scan_broad_entry_fill_terminal_r_lifecycle_contract(
        {"order": order_path, "trade": trade_path}
    )

    assert scan["bad_counts"] == {}
    assert scan["row_counts"]["unique_materialized_order_intents"] == 1


def test_entry_fill_lifecycle_scopes_shared_order_ids_by_profile(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    order_path = tmp_path / "scoped-orders.jsonl"
    trade_path = tmp_path / "scoped-trades.jsonl"
    order_rows = []
    trade_rows = []
    for profile in ("profile-a", "profile-b"):
        common = {
            "profile": profile,
            "campaign": f"campaign-{profile}",
            "simulated_order_id": "shared-order-id",
            "candidate_id": f"candidate-{profile}",
            "order_intent_materialized": True,
        }
        order_rows.extend(
            (
                {
                    **common,
                    "order_event_stage": "accepted_pending",
                    "is_terminal_order_event": False,
                    "entry_fill_executable": False,
                    "terminal_r_scoreable": False,
                },
                {
                    **common,
                    "order_event_stage": "terminal_filled",
                    "is_terminal_order_event": True,
                    "order_status": "filled",
                    "entry_fill_executable": True,
                    "terminal_r_scoreable": True,
                    "accepted_risk_budget_consumed_by_fill": True,
                    "accepted_risk_reservation_released": False,
                    "accepted_risk_reservation_transition": (
                        "pending_order_to_filled_position"
                    ),
                },
            )
        )
        trade_rows.append(
            {
                **common,
                "simulated_trade_id": f"trade-{profile}",
                "entry_fill_executable": True,
                "terminal_r_scoreable": True,
                "result_scoreable": True,
                "trade_state": "closed",
                "accepted_risk_budget_consumed_by_fill": True,
                "accepted_risk_reservation_released": True,
                "accepted_risk_reservation_transition": (
                    "pending_order_to_filled_position"
                ),
                "accepted_risk_close_release_once_status": (
                    "released_exactly_once_at_terminal_close"
                ),
                "accepted_risk_reservation_release": {
                    "released_risk_pct": 0.625,
                },
                "b7_5_selection_sizing_factorial_arm_id": "S1R1",
                "b7_5_selection_sizing_factorial_expiry_or_close_release_once": True,
            }
        )
    write_jsonl(order_path, order_rows)
    write_jsonl(trade_path, trade_rows)

    scan = verifier.scan_broad_entry_fill_terminal_r_lifecycle_contract(
        {"order": order_path, "trade": trade_path}
    )

    assert scan["bad_counts"] == {}
    assert scan["row_counts"]["unique_materialized_order_intents"] == 2


def test_entry_fill_terminal_r_lifecycle_contract_rejects_scoreable_trade_risk_drift(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    trade_path = tmp_path / "scoreable-risk-drift-trades.jsonl"
    write_jsonl(
        trade_path,
        [
            {
                "simulated_order_id": "scoreable-order",
                "simulated_trade_id": "scoreable-trade",
                "candidate_id": "scoreable-candidate",
                "entry_fill_executable": True,
                "terminal_r_scoreable": True,
                "result_scoreable": True,
                "trade_state": "closed",
                "accepted_risk_budget_consumed_by_fill": False,
                "accepted_risk_reservation_released": True,
                "accepted_risk_reservation_transition": "pending_order_released",
                "final_r": 1.0,
                "gross_r": 1.0,
                "net_proxy_r": 0.9,
                "net_r": 0.9,
                "pnl_cash": 90.0,
            }
        ],
    )

    scan = verifier.scan_broad_entry_fill_terminal_r_lifecycle_contract(
        {"trade": trade_path}
    )

    assert scan["bad_counts"][
        "trade:entry_fill_trade_missing_risk_consumption"
    ] == 1
    assert scan["bad_counts"][
        "trade:entry_fill_trade_releases_daily_accepted_risk"
    ] == 1
    assert scan["bad_counts"][
        "trade:entry_fill_trade_missing_fill_risk_transition"
    ] == 1


def test_hard_clean_capped_contract_is_not_required_after_terminal_block() -> None:
    verifier = load_verifier()
    row = v220_hard_clean_capped_verifier_row()
    row["replacement_reallocation_quality"][
        "soft_risk_cap_transfer_eligible"
    ] = False
    row.update(
        {
            "package_replay_order_executable_transfer_status": "final_blocked",
            "package_replay_order_executable_final_blocker_class": (
                "session_authority"
            ),
            "package_replay_order_executable_final_blocker_reason": (
                "off_configured_session_requires_explicit_off_session_authority"
            ),
        }
    )

    assert verifier.v220_hard_clean_capped_reduced_risk_contract_reasons(row) == []
