"""Observation-only convergence advisory for ultimate_book runtime-learning packets.

The advisory converts the large V3/V4/CP281 research reservoirs into packet
metadata that can be joined and replayed later. It never admits, sizes, places,
manages, closes, or mutates broker/account/order/deal/position state.
"""

from __future__ import annotations

from typing import Any, Mapping

from .runtime_learning_packet import stable_hash


SCHEMA_VERSION = "ultimate_convergence_advisory_v1"
CHECKPOINT_ROUTE = "research/operations/final_moonshot_ultimate_system_convergence_2026_06_19"
CHECKPOINT_COMMIT = "319590c1ebd6c859e75c4a236e2f4535a7fae5ef"

DEFAULT_CONFIG: dict[str, Any] = {
    "ultimate_convergence_advisory_enabled": False,
    "ultimate_convergence_advisory_log_enabled": False,
    "ultimate_convergence_advisory_apply_to_execution": False,
    "ultimate_convergence_advisory_checkpoint_path": CHECKPOINT_ROUTE,
    "ultimate_convergence_advisory_schema": SCHEMA_VERSION,
}

RESERVOIR_SUMMARIES: dict[str, dict[str, Any]] = {
    "selector_v3_source_bound_proxy": {
        "evidence_class": "source_bound_proxy_R_research_materialization",
        "rows": 289917,
        "total_r": 286137.784349529,
        "expectancy_r": 0.986964491,
        "exact_r_rows": 0,
        "runtime_use": "expert_signal_reservoir_not_direct_live_authority",
    },
    "scheduler_v3_source_bound_proxy": {
        "evidence_class": "source_bound_proxy_R_research_materialization",
        "rows": 289909,
        "total_r": 286137.835936219,
        "expectancy_r": 0.986991904,
        "exact_broker_real_rows": 8,
        "exact_broker_real_total_r": 0.393586,
        "runtime_use": "priority_disagreement_shadow_allocator_feature",
    },
    "wave4r_exit_path_comparators": {
        "evidence_class": "frozen_replay_proxy_R_path_exit_comparator",
        "processed_rows": 214536,
        "v4_total_proxy_r": 3188.390455784,
        "be_after_trigger_total_replay_r": 83555.679218977,
        "fixed_1_5r_total_replay_r": 80776.051948961,
        "promoted_router_total_replay_r": 56872.791504935,
        "runtime_use": "exit_path_opportunity_cost_feature",
    },
    "cp281_ready_runtime_mapping": {
        "evidence_class": "default_off_research_to_runtime_rule_mapping_and_simulated_R",
        "rule_mapping_rows": 461,
        "follow_rule_rows": 173,
        "avoid_filter_rows": 288,
        "rule_replay_result_table_rows": 841,
        "runtime_candidate_use_permitted_rows": 0,
        "runtime_use": "follow_avoid_expert_family_for_shadow_replay",
    },
}


def _cfg_bool(cfg: Mapping[str, Any], key: str) -> bool:
    return bool(cfg.get(key, DEFAULT_CONFIG[key]))


def _clean_mapping(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _clean_mapping(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean_mapping(item) for item in value]
    return value


def _first_sleeve(unit: Mapping[str, Any] | None, outcome: Mapping[str, Any] | None) -> str | None:
    if outcome and outcome.get("sleeve"):
        return str(outcome.get("sleeve"))
    if unit:
        members = unit.get("sleeve_members")
        if isinstance(members, list) and members:
            return str(members[0])
        if unit.get("sleeve"):
            return str(unit.get("sleeve"))
    return None


def _join_keys(
    *,
    namespace: str | None,
    event_type: str,
    unit: Mapping[str, Any] | None,
    outcome: Mapping[str, Any] | None,
) -> dict[str, Any]:
    outcome = outcome or {}
    unit = unit or {}
    return {
        "namespace": namespace,
        "event_type": event_type,
        "sleeve": _first_sleeve(unit, outcome),
        "symbol": outcome.get("symbol") or unit.get("symbol"),
        "direction": outcome.get("direction") or unit.get("direction"),
        "decision_bar_iso": outcome.get("decision_bar_iso"),
        "decision_day": outcome.get("decision_day"),
        "candidate_id": outcome.get("candidate_id") or unit.get("candidate_id"),
        "cluster": outcome.get("cluster") or unit.get("cluster"),
        "placement_status": outcome.get("placement_status"),
        "skip_reason": outcome.get("skip_reason") or outcome.get("reason"),
    }


def build_convergence_advisory(
    *,
    config: Mapping[str, Any],
    namespace: str | None,
    event_type: str,
    bridge: Mapping[str, Any] | None = None,
    unit: Mapping[str, Any] | None = None,
    outcome: Mapping[str, Any] | None = None,
    candidate_match_inputs: Mapping[str, Any] | None = None,
    candidate_matches: list[Mapping[str, Any]] | None = None,
) -> dict[str, Any] | None:
    """Build a packet-local advisory record when enabled.

    `ultimate_convergence_advisory_apply_to_execution` is intentionally ignored
    for runtime effect: this surface is observation-only until a later replay
    gate promotes a separate execution change.
    """
    if not _cfg_bool(config, "ultimate_convergence_advisory_enabled"):
        return None
    if not _cfg_bool(config, "ultimate_convergence_advisory_log_enabled"):
        return None

    bridge = dict(bridge or {})
    join_keys = _join_keys(namespace=namespace, event_type=event_type, unit=unit, outcome=outcome)
    apply_requested = _cfg_bool(config, "ultimate_convergence_advisory_apply_to_execution")
    candidate_matches_clean = [_clean_mapping(dict(row)) for row in (candidate_matches or [])]
    candidate_match_inputs_clean = _clean_mapping(dict(candidate_match_inputs or {}))
    material = {
        "schema_version": str(config.get("ultimate_convergence_advisory_schema", SCHEMA_VERSION) or SCHEMA_VERSION),
        "checkpoint_route": str(config.get("ultimate_convergence_advisory_checkpoint_path", CHECKPOINT_ROUTE) or CHECKPOINT_ROUTE),
        "checkpoint_commit": CHECKPOINT_COMMIT,
        "enabled": True,
        "log_enabled": True,
        "apply_to_execution_requested": apply_requested,
        "direct_execution_authority": False,
        "broker_runtime_change_status": False,
        "advisory_status": (
            "apply_requested_but_forced_shadow_until_replay_gate"
            if apply_requested
            else "shadow_observation_only"
        ),
        "runtime_effect_boundary": "observation_only_no_broker_account_order_deal_position_mutation",
        "join_keys": join_keys,
        "bridge_context": {
            "runtime_effect_now": bool(bridge.get("runtime_effect_now", False)),
            "profile": bridge.get("profile"),
            "candidate_book_profile": bridge.get("candidate_book_profile"),
            "market_expansion_policy": bridge.get("market_expansion_policy"),
            "include_candidate_book": bool(bridge.get("include_candidate_book", False)),
            "include_market_expansion_book": bool(bridge.get("include_market_expansion_book", False)),
            "broad_selector_apply_to_execution": bool(bridge.get("broad_selector_apply_to_execution", False)),
        },
        "reservoirs": RESERVOIR_SUMMARIES,
        "match_status": (
            "candidate_level_matches_attached_observation_only"
            if candidate_matches_clean
            else "reservoir_summary_attached_pending_candidate_level_expert_match"
        ),
        "next_replay_requirement": "join advisory packets to replay candidates and measure lift before any execution effect",
    }
    if candidate_match_inputs_clean or candidate_matches_clean:
        material["candidate_level"] = {
            "match_inputs": candidate_match_inputs_clean,
            "candidate_matches": candidate_matches_clean,
            "direct_execution_authority": False,
            "broker_runtime_change_status": False,
        }
    material["advisory_hash_sha256"] = stable_hash(material, prefix="ultimate_convergence_advisory")
    return material


__all__ = [
    "CHECKPOINT_COMMIT",
    "CHECKPOINT_ROUTE",
    "DEFAULT_CONFIG",
    "RESERVOIR_SUMMARIES",
    "SCHEMA_VERSION",
    "build_convergence_advisory",
]
