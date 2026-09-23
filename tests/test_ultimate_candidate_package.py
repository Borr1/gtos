from __future__ import annotations

import json
from pathlib import Path

import pytest

import src.components.ultimate_candidate_package as package_module
from src.components.ultimate_candidate_package import (
    PROMOTE_DEFAULT_OFF_TYPE,
    SCHEDULER_LIFECYCLE_MERGE_TYPE,
    build_ultimate_candidate_execution_policy_shadow,
    build_ultimate_candidate_package_surface,
    evaluate_ultimate_candidate_package_replay_authority,
    evaluate_ultimate_candidate_selector_shadow,
    load_ultimate_candidate_package_registry,
    load_sleeve_rows,
    schedule_ultimate_candidate_package_shadow,
)
from src.components.live_decision_packet_v4 import (
    build_live_decision_packet_v4,
    validate_live_decision_packet_v4,
)


ACCEPTANCE_ROUTE = Path(
    "research/operations/"
    "final_moonshot_ultimate_system_final_package_acceptance_compression_2026_06_19"
)
SLEEVE_PATH = ACCEPTANCE_ROUTE / "FINAL_PACKAGE_SLEEVE_CANDIDATE_LEDGER.jsonl"
MEMBER_PATH = ACCEPTANCE_ROUTE / "FINAL_PACKAGE_SLEEVE_MEMBER_LEDGER.jsonl"
ROUTE_REGISTRY_PATH = Path(
    "research/operations/"
    "final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/"
    "ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl"
)


def _surface():
    return build_ultimate_candidate_package_surface(
        load_sleeve_rows(SLEEVE_PATH),
        member_rows=load_sleeve_rows(MEMBER_PATH),
        generated_utc="2026-06-20T09:45:00Z",
        source_sleeve_path=str(SLEEVE_PATH),
        source_member_path=str(MEMBER_PATH),
    )


def _quality_fields() -> dict:
    return {
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
        "candidate_decision_quality_alias_mismatches": [],
        "source_boundary": "source_bound_asof_timewarp_decision_input",
    }


def test_builds_default_off_shadow_package_from_82_compressed_sleeves() -> None:
    package = _surface()
    surface = package["surface"]
    verification = package["verification"]

    assert surface["compressed_sleeve_rows"] == 82
    assert surface["compressed_member_rows"] == 1101
    assert surface["scheduler_lifecycle_merge_sleeves"] == 20
    assert surface["promote_default_off_signal_sleeves"] == 3
    assert surface["sleeve_type_counts"][SCHEDULER_LIFECYCLE_MERGE_TYPE] == 20
    assert surface["sleeve_type_counts"][PROMOTE_DEFAULT_OFF_TYPE] == 3
    assert surface["selector_shadow_ledger_rows"] == 82
    assert surface["scheduler_shadow_ledger_rows"] == 20
    assert surface["selector_surface_ready"] is True
    assert surface["scheduler_surface_ready"] is True
    assert surface["default_off"] is True
    assert surface["shadow_only"] is True
    assert surface["final_package_selected"] is False
    assert surface["runtime_effect_now"] is False
    assert surface["live_execution_activation_allowed"] is False
    assert verification["ok"] is True


def test_selector_shadow_matches_core_and_promote_sleeves_without_execution() -> None:
    package = _surface()
    packet = evaluate_ultimate_candidate_selector_shadow(
        {
            "candidate_id": "candidate:nas-vol-long",
            "symbol": "NAS100",
            "side": "LONG",
            "framework": "origin_volatility_compression_expansion",
            "origin_family": "volatility_compression_expansion",
            "decision_time_utc": "2026-05-05T06:15:00Z",
            "broker_real_net_r": 99.0,
        },
        package["sleeve_registry_rows"],
        {
            "ultimate_candidate_package_enabled": True,
            "ultimate_candidate_package_apply_to_execution": True,
            "ultimate_candidate_package_live_activation_allowed": True,
            "ultimate_candidate_package_final_package_selected": True,
        },
        generated_utc="2026-06-20T09:45:00Z",
    )

    assert packet["decision_status"] == "shadow_sleeve_matches_found"
    assert packet["matched_sleeve_count"] >= 2
    assert packet["matched_scheduler_lifecycle_merge_sleeves"] >= 1
    assert packet["matched_promote_default_off_sleeves"] == 1
    assert all(
        row.get("row_hash_sha256")
        for row in packet["matched_sleeves"]
    )
    assert packet["ignored_forbidden_fields"] == ["broker_real_net_r"]
    assert packet["action"] == "shadow_no_execution"
    assert packet["candidate_use_allowed_now"] is False
    assert packet["runtime_effect_now"] is False
    assert packet["order_calls"] is False
    assert packet["live_execution_activation_allowed"] is False


def test_selector_shadow_treats_broader_origin_scheduler_sleeves_as_framework_wildcards() -> None:
    package = _surface()
    packet = evaluate_ultimate_candidate_selector_shadow(
        {
            "candidate_id": "candidate:xau-liquidity-short",
            "symbol": "XAUUSD",
            "side": "SHORT",
            "framework": "origin_liquidity_sweep_reclaim",
            "origin_family": "liquidity_sweep_reclaim",
            "decision_time_utc": "2026-05-05T12:15:00Z",
        },
        package["sleeve_registry_rows"],
        {"ultimate_candidate_package_enabled": True},
        generated_utc="2026-06-20T09:45:00Z",
    )

    assert packet["decision_status"] == "shadow_sleeve_matches_found"
    assert packet["matched_scheduler_lifecycle_merge_sleeves"] >= 1


def test_registry_loader_resolves_repo_relative_path_from_route_cwd(monkeypatch, tmp_path) -> None:
    nested_cwd = tmp_path / "route" / "nested"
    nested_cwd.mkdir(parents=True)
    monkeypatch.chdir(nested_cwd)

    rows = load_ultimate_candidate_package_registry(str(SLEEVE_PATH))

    assert len(rows) == 82
    assert sum(1 for row in rows if row["sleeve_type"] == SCHEDULER_LIFECYCLE_MERGE_TYPE) == 20
    assert sum(1 for row in rows if row["sleeve_type"] == PROMOTE_DEFAULT_OFF_TYPE) == 3


def test_registry_campaign_lease_reads_once_and_fails_on_source_mutation(
    tmp_path: Path,
) -> None:
    registry_path = tmp_path / "registry.jsonl"
    registry_path.write_bytes(ROUTE_REGISTRY_PATH.read_bytes())

    with package_module.ultimate_candidate_package_registry_campaign_lease(
        replay_lfs_pointer_fallback=True,
    ) as lease:
        first = load_ultimate_candidate_package_registry(registry_path)
        second = load_ultimate_candidate_package_registry(registry_path)
        third = load_ultimate_candidate_package_registry(registry_path)

        assert first == second == third
        assert lease.miss_count == 1
        assert lease.hit_count == 2

    with pytest.raises(
        package_module.UltimateCandidatePackageRegistryChanged,
        match="registry_source_changed_during_campaign",
    ):
        with package_module.ultimate_candidate_package_registry_campaign_lease(
            replay_lfs_pointer_fallback=True,
        ):
            load_ultimate_candidate_package_registry(registry_path)
            registry_path.write_bytes(registry_path.read_bytes() + b"\n")


def test_git_lfs_pointer_fallback_is_replay_lease_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pointer = tmp_path / "registry-pointer.jsonl"
    pointer.write_text(
        "version https://git-lfs.github.com/spec/v1\n"
        "oid sha256:" + "a" * 64 + "\n"
        "size 123\n",
        encoding="ascii",
    )
    monkeypatch.setattr(
        package_module,
        "DEFAULT_COMPRESSED_SLEEVE_SOURCE_PATH",
        SLEEVE_PATH,
    )

    with pytest.raises(json.JSONDecodeError):
        load_ultimate_candidate_package_registry(pointer)

    with package_module.ultimate_candidate_package_registry_campaign_lease(
        replay_lfs_pointer_fallback=True,
    ):
        rows = load_ultimate_candidate_package_registry(pointer)

    assert len(rows) == 82


def test_selector_shadow_matches_origin_and_session_namespace_aliases() -> None:
    registry = [
        {
            "sleeve_id": "core:alias-test",
            "sleeve_type": SCHEDULER_LIFECYCLE_MERGE_TYPE,
            "package_role": "scheduler_lifecycle_core",
            "framework": "broader_origin",
            "origin_family": "current_liquidity_sweep_reclaim",
            "side": "LONG",
            "symbols": ["AUDJPY"],
            "session_buckets": ["moonshot_h08_09"],
            "selector_shadow_priority_score": 1.0,
            "combined_source_bound_signal_r": 1.5,
            "scheduler_action_class_counts": {"enter": 1},
        }
    ]

    packet = evaluate_ultimate_candidate_selector_shadow(
        {
            "candidate_id": "candidate:alias-test",
            "symbol": "AUDJPY",
            "side": "LONG",
            "framework": "origin_liquidity_sweep_reclaim",
            "origin_family": "liquidity_sweep_reclaim",
            "decision_time_utc": "2026-05-05T08:15:00+00:00",
        },
        registry,
        {"ultimate_candidate_package_enabled": True},
        generated_utc="2026-06-20T09:45:00Z",
    )

    assert packet["decision_status"] == "shadow_sleeve_matches_found"
    assert packet["matched_scheduler_lifecycle_merge_sleeves"] == 1
    assert packet["admission_sleeve_match_count"] == 1


def test_selector_shadow_splits_entry_quality_from_execution_fill_probability() -> None:
    registry = [
        {
            "sleeve_id": "core:fill-split",
            "sleeve_type": SCHEDULER_LIFECYCLE_MERGE_TYPE,
            "package_role": "scheduler_lifecycle_core",
            "framework": "origin_liquidity_sweep_reclaim",
            "origin_family": "liquidity_sweep_reclaim",
            "side": "SHORT",
            "symbols": ["XAUUSD"],
            "session_buckets": ["london_broad"],
            "selector_shadow_priority_score": 2.0,
            "combined_source_bound_signal_r": 8.0,
            "scheduler_action_class_counts": {"enter": 1},
        }
    ]
    packet = evaluate_ultimate_candidate_selector_shadow(
        {
            "candidate_id": "candidate:fill-split",
            "symbol": "XAUUSD",
            "side": "SHORT",
            "framework": "origin_liquidity_sweep_reclaim",
            "origin_family": "liquidity_sweep_reclaim",
            "decision_time_utc": "2026-05-13T08:15:00+00:00",
            "session_bucket": "london_broad",
            "expected_net_r": 1.21,
            "probability": 0.88,
            "fill_probability": 0.93,
            "candidate_fill_probability": 0.93,
            "execution_fill_probability": 0.15,
            "execution_fill_probability_source": (
                "predecision_limit_fillability.fill_probability"
            ),
            "execution_fill_probability_source_time_utc": (
                "2026-05-13T08:00:00+00:00"
            ),
            "execution_fill_probability_source_boundary": (
                "closed_m15_predecision_asof_no_postdecision_path"
            ),
            "execution_fill_probability_authority_class": (
                "predecision_passive_limit_fillability_authority"
            ),
            "predecision_limit_fillability_probability": 0.15,
            "limit_fillability_probability": 0.15,
            "predecision_limit_fillability": {
                "available": True,
                "fill_probability": 0.15,
                "current_price_source_time_utc": (
                    "2026-05-13T08:00:00+00:00"
                ),
                "current_price_source_boundary": (
                    "closed_m15_predecision_asof_no_postdecision_path"
                ),
            },
            "source_completeness": 1.0,
            **_quality_fields(),
        },
        registry,
        {
            "ultimate_candidate_package_enabled": True,
            "ultimate_candidate_package_replay_admission_enabled": True,
            "ultimate_candidate_package_apply_to_execution": True,
        },
        generated_utc="2026-06-20T09:45:00Z",
    )

    assert packet["decision_status"] == "shadow_sleeve_matches_found"
    assert packet["candidate_fill_probability"] == 0.93
    assert packet["fill_probability"] == 0.93
    assert packet["entry_quality_fill_probability"] == 0.93
    assert packet["execution_fill_probability"] == 0.15
    assert packet["execution_fill_probability_source"] == (
        "predecision_limit_fillability.fill_probability"
    )
    assert packet["execution_fill_probability_source_time_utc"] == (
        "2026-05-13T08:00:00+00:00"
    )
    assert packet["execution_fill_probability_source_boundary"] == (
        "closed_m15_predecision_asof_no_postdecision_path"
    )
    assert packet["execution_fillability_atomic_status"] == "complete"


def test_selector_shadow_does_not_promote_value_only_execution_fillability() -> None:
    registry = [
        {
            "sleeve_id": "core:fill-value-only",
            "sleeve_type": SCHEDULER_LIFECYCLE_MERGE_TYPE,
            "package_role": "scheduler_lifecycle_core",
            "framework": "origin_liquidity_sweep_reclaim",
            "origin_family": "liquidity_sweep_reclaim",
            "side": "SHORT",
            "symbols": ["XAUUSD"],
            "session_buckets": ["london_broad"],
            "selector_shadow_priority_score": 2.0,
            "combined_source_bound_signal_r": 8.0,
            "scheduler_action_class_counts": {"enter": 1},
        }
    ]
    packet = evaluate_ultimate_candidate_selector_shadow(
        {
            "candidate_id": "candidate:fill-value-only",
            "symbol": "XAUUSD",
            "side": "SHORT",
            "framework": "origin_liquidity_sweep_reclaim",
            "origin_family": "liquidity_sweep_reclaim",
            "decision_time_utc": "2026-05-13T08:15:00+00:00",
            "session_bucket": "london_broad",
            "expected_net_r": 1.21,
            "probability": 0.88,
            "fill_probability": 0.93,
            "execution_fill_probability": 0.15,
            "source_completeness": 1.0,
            **_quality_fields(),
        },
        registry,
        {
            "ultimate_candidate_package_enabled": True,
            "ultimate_candidate_package_replay_admission_enabled": True,
            "ultimate_candidate_package_apply_to_execution": True,
        },
        generated_utc="2026-06-20T09:45:00Z",
    )

    assert packet["fill_probability"] == 0.93
    assert packet["execution_fill_probability"] is None
    assert packet["execution_fillability_atomic_status"] == (
        "incomplete_not_executable"
    )
    assert packet["execution_fillability_atomic_failure"] == (
        "execution_fillability_incomplete_value_only_not_propagated"
    )


def test_selector_shadow_requires_non_wildcard_sleeve_alias_fields() -> None:
    registry = [
        {
            "sleeve_id": "promote:exact-vol",
            "sleeve_type": PROMOTE_DEFAULT_OFF_TYPE,
            "package_role": "promote_default_off_signal",
            "framework": "origin_volatility_compression_expansion",
            "origin_family": "volatility_compression_expansion",
            "side": "LONG",
            "symbols": ["NAS100"],
            "session_buckets": ["h06_07"],
            "selector_shadow_priority_score": 5.0,
            "combined_source_bound_signal_r": 10.0,
            "scheduler_action_class_counts": {"enter": 1},
        }
    ]

    packet = evaluate_ultimate_candidate_selector_shadow(
        {
            "candidate_id": "candidate:missing-framework",
            "symbol": "NAS100",
            "side": "LONG",
            "origin_family": "volatility_compression_expansion",
            "decision_time_utc": "2026-05-05T06:15:00+00:00",
        },
        registry,
        {
            "ultimate_candidate_package_enabled": True,
            "ultimate_candidate_package_replay_admission_enabled": True,
        },
        generated_utc="2026-06-20T09:45:00Z",
    )

    assert packet["matched_sleeve_count"] == 0
    assert packet["admission_sleeve_match_count"] == 0
    assert packet["source_bound_package_candidate_use_allowed"] is False


def test_scheduler_shadow_ranks_candidates_but_selects_no_live_action() -> None:
    package = _surface()
    packet = schedule_ultimate_candidate_package_shadow(
        [
            {
                "candidate_id": "candidate:nas-vol-long",
                "symbol": "NAS100",
                "side": "LONG",
                "origin_family": "volatility_compression_expansion",
                "decision_time_utc": "2026-05-05T06:15:00Z",
                "candidate_ev_r": 1.1,
                "broker_pretrade_cost_r": 0.08,
                "candidate_probability": 0.77,
                "fill_probability": 0.66,
                "source_completeness": 0.95,
            },
            {
                "candidate_id": "candidate:unmatched",
                "symbol": "UNKNOWN",
                "side": "LONG",
                "origin_family": "unknown",
            },
        ],
        package["sleeve_registry_rows"],
        {"ultimate_candidate_package_enabled": True},
        decision_window_id="window:test",
        generated_utc="2026-06-20T09:45:00Z",
    )

    assert packet["decision_status"] == "shadow_scheduler_ranked_candidates"
    assert packet["candidate_rows"] == 2
    assert packet["shadow_selected_candidate_id"] == "candidate:nas-vol-long"
    assert packet["shadow_selected_expected_net_r"] == 1.02
    assert packet["shadow_selected_broker_pretrade_cost_r"] == 0.08
    assert packet["shadow_selected_fill_probability"] == 0.66
    assert packet["shadow_selected_source_completeness"] == 0.95
    assert packet["selected_candidate_id"] is None


def test_scheduler_shadow_does_not_select_non_rankable_diagnostics() -> None:
    registry = [
        {
            "sleeve_id": "source-required:vol-long",
            "sleeve_type": SCHEDULER_LIFECYCLE_MERGE_TYPE,
            "package_role": "source_required_hold",
            "framework": "broader_origin",
            "origin_family": "volatility_compression_expansion",
            "side": "LONG",
            "symbols": ["NAS100"],
            "session_buckets": ["ALL"],
            "selector_shadow_priority_score": 10.0,
            "combined_source_bound_signal_r": 1000.0,
            "scheduler_action_class_counts": {"enter": 99},
        }
    ]

    packet = schedule_ultimate_candidate_package_shadow(
        [
            {
                "candidate_id": "candidate:source-required-diagnostic",
                "symbol": "NAS100",
                "side": "LONG",
                "origin_family": "volatility_compression_expansion",
                "decision_time_utc": "2026-05-05T06:15:00Z",
                "candidate_ev_r": 2.0,
                "candidate_probability": 0.95,
                "fill_probability": 0.95,
                "source_completeness": 1.0,
            }
        ],
        registry,
        {"ultimate_candidate_package_enabled": True},
        decision_window_id="window:source-required-diagnostic",
        generated_utc="2026-06-20T09:45:00Z",
    )

    assert packet["decision_status"] == "shadow_scheduler_no_candidates"
    assert packet["shadow_selected_candidate_id"] is None
    assert packet["selector_packets"] == []
    assert packet["scheduler_action_class_counts"] == {}
    assert packet["execution_policy_shadow"]["shadow_selected_candidate_id"] is None


def test_scheduler_shadow_ranks_admitted_candidates_by_source_and_probability() -> None:
    registry = [
        {
            "sleeve_id": "core:vol-long",
            "sleeve_type": SCHEDULER_LIFECYCLE_MERGE_TYPE,
            "package_role": "scheduler_lifecycle_core",
            "framework": "broader_origin",
            "origin_family": "volatility_compression_expansion",
            "side": "LONG",
            "symbols": ["NAS100"],
            "session_buckets": ["ALL"],
            "selector_shadow_priority_score": 1.0,
            "combined_source_bound_signal_r": 10.0,
            "scheduler_action_class_counts": {"enter": 1},
        }
    ]

    packet = schedule_ultimate_candidate_package_shadow(
        [
            {
                "candidate_id": "candidate:lower-source",
                "symbol": "NAS100",
                "side": "LONG",
                "origin_family": "volatility_compression_expansion",
                "decision_time_utc": "2026-05-05T06:15:00Z",
                "candidate_ev_r": 2.0,
                "candidate_probability": 0.55,
                "fill_probability": 0.80,
                "source_completeness": 0.40,
            },
            {
                "candidate_id": "candidate:higher-source",
                "symbol": "NAS100",
                "side": "LONG",
                "origin_family": "volatility_compression_expansion",
                "decision_time_utc": "2026-05-05T06:15:00Z",
                "candidate_ev_r": 1.0,
                "candidate_probability": 0.80,
                "fill_probability": 0.70,
                "source_completeness": 0.95,
            },
        ],
        registry,
        {"ultimate_candidate_package_enabled": True},
        decision_window_id="window:source-rank",
        generated_utc="2026-06-20T09:45:00Z",
    )

    assert packet["shadow_selected_candidate_id"] == "candidate:higher-source"
    assert packet["shadow_selected_source_completeness"] == 0.95
    assert packet["action"] == "shadow_no_trade_no_execution"
    assert packet["approved_risk_pct"] == 0.0
    assert packet["order_calls"] == 0
    assert packet["runtime_effect_now"] is False
    assert packet["live_execution_activation_allowed"] is False
    assert packet["broker_account_order_history_deal_position_mutation_allowed"] is False
    assert packet["scheduler_action_class_counts"]
    policy = packet["execution_policy_shadow"]
    assert policy["policy_status"] == "shadow_execution_policy_ready_not_selectable"
    assert policy["selected_order_type_architecture"] is None
    assert policy["execution_order_type_policy_selectable"] is False
    assert policy["missed_fill_opportunity_cost_allowed"] is False
    assert policy["order_calls"] == 0
    assert policy["runtime_effect_now"] is False
    assert policy["live_execution_activation_allowed"] is False
    assert "order_type" in policy["required_fillability_source_fields"]
    assert "close_side_all_in_cost" in policy["required_cost_source_fields"]


def test_selector_shadow_replay_admission_does_not_require_execution_activation() -> None:
    package = _surface()
    packet = evaluate_ultimate_candidate_selector_shadow(
        {
            "candidate_id": "candidate:nas-vol-long",
            "symbol": "NAS100",
            "side": "LONG",
            "origin_family": "volatility_compression_expansion",
            "decision_time_utc": "2026-05-05T06:15:00Z",
        },
        package["sleeve_registry_rows"],
        {
            "ultimate_candidate_package_enabled": True,
            "ultimate_candidate_package_shadow_enabled": True,
            "ultimate_candidate_package_replay_admission_enabled": True,
            "ultimate_candidate_package_apply_to_execution": False,
            "ultimate_candidate_package_live_activation_allowed": False,
            "ultimate_candidate_package_final_package_selected": False,
        },
        generated_utc="2026-06-20T09:45:00Z",
    )

    assert packet["shadow_enabled"] is True
    assert packet["replay_admission_enabled"] is True
    assert packet["apply_to_execution"] is False
    assert packet["source_bound_package_candidate_use_allowed"] is True
    assert packet["source_bound_package_candidate_use_allowed_reason"] == (
        "replay_admission_enabled_matched_admission_sleeve"
    )
    assert packet["candidate_use_allowed_now"] is False
    assert packet["live_execution_activation_allowed"] is False
    assert packet["final_package_selected_by_config"] is False
    assert packet["runtime_effect_now"] is False
    assert packet["order_calls"] == 0


def test_execution_policy_shadow_maps_scheduler_controls_without_execution() -> None:
    policy = build_ultimate_candidate_execution_policy_shadow(
        decision_window_id="window:test",
        shadow_selected_candidate_id="candidate:test",
        scheduler_action_class_counts={"delay": 7, "replace": 2},
        would_scheduler_action="shadow_queue_or_delay",
        dominant_scheduler_control="delay",
        config={
            "ultimate_candidate_package_enabled": True,
            "ultimate_candidate_package_apply_to_execution": True,
            "ultimate_candidate_package_live_activation_allowed": True,
            "ultimate_candidate_package_final_package_selected": True,
        },
        generated_utc="2026-06-20T09:45:00Z",
    )

    assert policy["would_order_entry_policy"] == "shadow_limit_first_delay_queue"
    assert policy["would_primary_order_type"] == "limit"
    assert policy["would_guarded_market_fallback"] == "guarded_market_after_fillability_cost_proof"
    assert policy["selected_order_type_architecture"] is None
    assert policy["execution_order_type_policy_selectable"] is False
    assert policy["approved_risk_pct"] == 0.0
    assert policy["order_calls"] == 0
    assert policy["runtime_effect_now"] is False
    assert policy["live_execution_activation_allowed"] is False
    assert policy["broker_account_order_history_deal_position_mutation_allowed"] is False


def test_replay_authority_selects_candidates_and_order_policy_without_live_authority() -> None:
    package = _surface()
    result = evaluate_ultimate_candidate_package_replay_authority(
        [
            {
                "candidate_id": "candidate:nas-vol-long",
                "symbol": "NAS100",
                "side": "LONG",
                "origin_family": "volatility_compression_expansion",
                "decision_time_utc": "2026-05-05T06:15:00Z",
                "candidate_ev_r": 1.2,
                "candidate_expected_net_r": 1.08,
                "candidate_probability": 0.78,
                "expected_cost_r": 0.12,
                "fill_probability": 0.82,
                "source_completeness": 0.97,
                "source_completeness_status": "complete",
                **_quality_fields(),
                "cost_authority": "broker_calibrated_replay_cost",
                "pretrade_cost_packet_status": "PASSED",
                "cost_source_gap_status": "source_bound_cost_authority_present",
                "risk_pct": 1.0,
                "entry_price": 18000.0,
                "entry_reference": 18000.0,
                "stop_loss": 17950.0,
                "take_profit_1": 18100.0,
                "target_reference": 18100.0,
                "risk_reward_ratio": 2.0,
                "trade_parameters": {
                    "entry_price": 18000.0,
                    "stop_loss": 17950.0,
                    "take_profit_1": 18100.0,
                },
                "canonical_geometry_status": "canonicalized",
                "canonical_geometry_source": "unit_fixture",
                "matched_stable_member_axis_ids": [
                    "member_axis:route-compact-source",
                ],
                "ultimate_package_matched_member_axis_ids": [
                    "member_axis:explicit-package-axis",
                ],
                "matched_source_axis_row_indexes": [101, 202],
                "source_bound_fields": {
                    "ultimate_package_matched_member_axis_count": 2,
                    "ultimate_package_role_disposition": "admission_candidate",
                },
                "actual_r": 99.0,
            },
            {
                "candidate_id": "candidate:unmatched",
                "symbol": "UNKNOWN",
                "side": "LONG",
                "origin_family": "unknown",
                "decision_time_utc": "2026-05-05T06:15:00Z",
                "candidate_ev_r": 0.1,
                "candidate_probability": 0.51,
                "expected_cost_r": 0.12,
                "risk_pct": 1.0,
            },
        ],
        package["sleeve_registry_rows"],
        scorecard_rows=[
            {
                "decision_time_utc": "2026-05-05T06:15:00Z",
                "selected_action_class": "zero_trade",
                "selected_candidate_id": None,
            }
        ],
        order_rows=[
            {
                "candidate_id": "candidate:nas-vol-long",
                "decision_time_utc": "2026-05-05T06:15:00Z",
                "counterfactual_final_r": 0.8,
                "counterfactual_fill_status": "filled_from_ordered_m1_path",
            }
        ],
        source_namespace="fixture_replay",
        generated_utc="2026-06-20T09:45:00Z",
    )

    summary = result["summary"]
    assert summary["package_replay_authority_enabled"] is True
    assert summary["candidate_rows"] == 2
    assert summary["decision_window_rows"] == 1
    assert summary["selected_candidate_rows"] == 1
    assert summary["source_bound_candidate_use_allowed_rows"] == 1
    assert summary["executable_candidate_use_allowed_rows"] == 1
    assert summary["executable_candidate_use_allowed_reason_counts"][
        "broker_cost_source_and_replay_order_path_exact_candidate_time_join_executable"
    ] == 1
    selected = [
        row for row in result["candidate_rows"] if row["selected_by_package_replay"]
    ][0]
    assert selected["candidate_id"] == "candidate:nas-vol-long"
    assert selected["package_replay_candidate_use_allowed"] is True
    assert selected["package_replay_source_bound_candidate_use_allowed"] is True
    assert selected["package_replay_executable_candidate_use_allowed"] is True
    assert selected["replay_candidate_use_allowed_now"] is True
    assert selected["package_replay_executable_candidate_use_allowed_reason"] == (
        "broker_cost_source_and_replay_order_path_exact_candidate_time_join_executable"
    )
    assert selected["selected_candidate_id"] == "candidate:nas-vol-long"
    assert selected["expected_net_r"] == 1.08
    assert selected["candidate_expected_net_r"] == 1.08
    assert selected["broker_calibrated_expected_cost_r"] == 0.12
    assert selected["broker_pretrade_cost_r"] == 0.12
    assert set(selected["matched_stable_member_axis_ids"]) == {
        "member_axis:explicit-package-axis",
        "member_axis:route-compact-source",
    }
    assert set(selected["ultimate_package_matched_member_axis_ids"]) == {
        "member_axis:explicit-package-axis",
        "member_axis:route-compact-source",
    }
    assert set(selected["selected_package_matched_member_axis_ids"]) == {
        "member_axis:explicit-package-axis",
        "member_axis:route-compact-source",
    }
    assert selected["matched_source_axis_row_indexes"] == ["101", "202"]
    assert selected["source_bound_fields"][
        "ultimate_package_matched_member_axis_count"
    ] == 2
    assert selected["fill_probability"] == 0.82
    assert selected["model_limit_fill_probability_prior"] == 0.82
    assert selected["fill_probability_authority_class"] == (
        "predecision_model_prior_not_fill_execution_authority"
    )
    assert selected["fill_probability_source_bound_input_present"] is True
    assert selected["source_completeness"] == 0.97
    assert selected["source_completeness_status"] == "complete"
    assert selected["candidate_decision_quality_field_sources"] == {
        "expected_net_r": "fixture.predecision.expected_net_r",
        "probability": "fixture.predecision.probability",
        "fill_probability": "fixture.predecision.fill_probability",
        "source_completeness": "fixture.predecision.source_completeness",
    }
    assert selected["candidate_decision_quality_source_boundary"] == (
        "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
    )
    assert selected["candidate_decision_quality_alias_status"] == "exact_materialized"
    assert selected["candidate_decision_quality_alias_mismatches"] == []
    assert selected["candidate_decision_quality_provenance_failures"] == []
    assert selected["source_boundary"] == "source_bound_asof_timewarp_decision_input"
    assert selected["cost_authority"] == "broker_calibrated_replay_cost"
    assert selected["pretrade_cost_packet_status"] == "PASSED"
    assert selected["cost_source_gap_status"] == "source_bound_cost_authority_present"
    assert selected["entry_price"] == 18000.0
    assert selected["stop_loss"] == 17950.0
    assert selected["take_profit_1"] == 18100.0
    assert selected["target_reference"] == 18100.0
    assert selected["risk_reward_ratio"] == 2.0
    assert selected["canonical_geometry_status"] == "canonicalized"
    assert selected["canonical_geometry_source"] == "unit_fixture"
    assert selected["matched_sleeve_ids"]
    assert selected["ultimate_package_matched_sleeve_ids"] == selected["matched_sleeve_ids"]
    assert "actual_r" in selected["ignored_forbidden_fields"]
    assert "actual_r" not in selected
    assert selected["execution_order_type_policy_selectable"] is True
    assert selected["missed_fill_opportunity_cost_allowed"] is True
    assert selected["local_replay_effect_now"] is True
    assert selected["runtime_effect_now"] is False
    assert selected["live_execution_activation_allowed"] is False
    assert selected["final_package_selection_allowed"] is False
    assert selected["broker_account_order_history_deal_position_mutation_allowed"] is False
    assert selected["order_calls"] == 0
    scorecard = result["scorecard_rows"][0]
    assert scorecard["package_selected_candidate_id"] == "candidate:nas-vol-long"
    assert scorecard["baseline_selected_action_class"] == "zero_trade"
    assert scorecard["missed_fill_opportunity_cost_r"] == 0.8
    assert scorecard["candidate_expected_net_r"] == 1.08
    assert scorecard["probability"] == 0.78
    assert scorecard["fill_probability"] == 0.82
    assert scorecard["source_completeness"] == 0.97
    assert scorecard["source_completeness_status"] == "complete"
    assert scorecard["candidate_decision_quality_field_sources"] == (
        selected["candidate_decision_quality_field_sources"]
    )
    assert scorecard["candidate_decision_quality_source_boundary"] == (
        selected["candidate_decision_quality_source_boundary"]
    )
    assert scorecard["candidate_decision_quality_alias_status"] == "exact_materialized"
    assert scorecard["candidate_decision_quality_provenance_failures"] == []
    assert scorecard["source_boundary"] == "source_bound_asof_timewarp_decision_input"
    assert scorecard["cost_authority"] == "broker_calibrated_replay_cost"
    assert scorecard["pretrade_cost_packet_status"] == "PASSED"
    assert scorecard["matched_sleeve_count"] == selected["matched_sleeve_count"]
    assert scorecard["role_disposition"] == selected["role_disposition"]
    policy = result["order_policy_rows"][0]
    assert policy["execution_order_type_policy_selectable"] is True
    assert policy["candidate_expected_net_r"] == 1.08
    assert policy["probability"] == 0.78
    assert policy["fill_probability"] == 0.82
    assert policy["source_completeness"] == 0.97
    assert policy["source_completeness_status"] == "complete"
    assert policy["candidate_decision_quality_field_sources"] == (
        selected["candidate_decision_quality_field_sources"]
    )
    assert policy["candidate_decision_quality_source_boundary"] == (
        selected["candidate_decision_quality_source_boundary"]
    )
    assert policy["candidate_decision_quality_alias_status"] == "exact_materialized"
    assert policy["candidate_decision_quality_provenance_failures"] == []
    assert policy["source_boundary"] == "source_bound_asof_timewarp_decision_input"
    assert policy["cost_authority"] == "broker_calibrated_replay_cost"
    assert policy["pretrade_cost_packet_status"] == "PASSED"
    assert policy["matched_sleeve_count"] == selected["matched_sleeve_count"]
    assert policy["role_disposition"] == selected["role_disposition"]


def test_replay_authority_upgrades_complete_materialized_quality_alias_status() -> None:
    package = _surface()
    quality_fields = {
        **_quality_fields(),
        "candidate_decision_quality_alias_status": "materialized",
        "candidate_decision_quality_provenance_failures": [
            "candidate_decision_quality_alias_status:materialized"
        ],
    }
    result = evaluate_ultimate_candidate_package_replay_authority(
        [
            {
                "candidate_id": "candidate:materialized-quality",
                "symbol": "NAS100",
                "side": "LONG",
                "origin_family": "volatility_compression_expansion",
                "decision_time_utc": "2026-05-05T06:15:00Z",
                "candidate_ev_r": 1.2,
                "candidate_expected_net_r": 1.08,
                "candidate_probability": 0.78,
                "expected_cost_r": 0.12,
                "fill_probability": 0.82,
                "source_completeness": 0.97,
                "source_completeness_status": "complete",
                **quality_fields,
                "cost_authority": "broker_calibrated_replay_cost",
                "pretrade_cost_packet_status": "PASSED",
                "cost_source_gap_status": "source_bound_cost_authority_present",
                "risk_pct": 1.0,
            }
        ],
        package["sleeve_registry_rows"],
        scorecard_rows=[{"decision_time_utc": "2026-05-05T06:15:00Z"}],
        order_rows=[
            {
                "candidate_id": "candidate:materialized-quality",
                "decision_time_utc": "2026-05-05T06:15:00Z",
                "counterfactual_final_r": 0.8,
                "counterfactual_fill_status": "filled_from_ordered_m1_path",
            }
        ],
        source_namespace="fixture_replay",
        generated_utc="2026-06-20T09:45:00Z",
    )

    assert result["summary"]["selected_candidate_rows"] == 1
    selected = result["candidate_rows"][0]
    assert selected["package_replay_executable_candidate_use_allowed"] is True
    assert selected["candidate_decision_quality_alias_status"] == (
        "exact_materialized_from_complete_predecision_quality_sources"
    )
    assert selected["candidate_decision_quality_provenance_failures"] == []
    scorecard = result["scorecard_rows"][0]
    assert scorecard["package_selected_candidate_id"] == "candidate:materialized-quality"
    assert scorecard["candidate_decision_quality_alias_status"] == (
        "exact_materialized_from_complete_predecision_quality_sources"
    )


def test_replay_authority_matches_candidate_origin_family_alias() -> None:
    package = _surface()
    result = evaluate_ultimate_candidate_package_replay_authority(
        [
            {
                "candidate_id": "candidate:nas-origin-alias",
                "symbol": "NAS100",
                "side": "LONG",
                "candidate_origin_family": "volatility_compression_expansion",
                "framework": "volatility_compression_expansion",
                "decision_time_utc": "2026-05-05T06:15:00Z",
                "candidate_ev_r": 1.4,
                "candidate_expected_net_r": 1.36,
                "candidate_probability": 0.78,
                "fill_probability": 0.70,
                "source_completeness": 0.96,
                "source_completeness_status": "source_completeness_present",
                **_quality_fields(),
                "expected_cost_r": 0.04,
                "risk_pct": 0.25,
            }
        ],
        package["sleeve_registry_rows"],
        generated_utc="2026-06-20T10:00:00Z",
    )

    row = result["candidate_rows"][0]
    assert row["matched_sleeve_count"] > 0
    assert row["admission_sleeve_match_count"] > 0
    assert row["package_replay_candidate_use_allowed"] is True
    assert row["source_bound_package_candidate_use_allowed"] is True
    assert row["package_replay_executable_candidate_use_allowed"] is False
    assert row["replay_candidate_use_allowed_now"] is False
    assert row["package_replay_executable_candidate_use_allowed_reason"] == (
        "broker_cost_packet_status_missing"
    )
    assert result["summary"]["source_bound_candidate_use_allowed_rows"] == 1
    assert result["summary"]["executable_candidate_use_allowed_rows"] == 0


def test_replay_authority_missing_source_completeness_stays_scoreable_not_executable() -> None:
    promote_registry = [
        {
            "sleeve_id": "promote:source-gap",
            "sleeve_type": PROMOTE_DEFAULT_OFF_TYPE,
            "package_role": "promote_default_off_signal",
            "framework": "origin_liquidity_sweep_reclaim",
            "origin_family": "liquidity_sweep_reclaim",
            "side": "LONG",
            "symbols": ["AUDJPY"],
            "session_buckets": ["h08_09"],
            "selector_shadow_priority_score": 1.0,
            "combined_source_bound_signal_r": 1.5,
            "scheduler_action_class_counts": {},
        }
    ]
    result = evaluate_ultimate_candidate_package_replay_authority(
        [
            {
                "candidate_id": "candidate:source-gap",
                "symbol": "AUDJPY",
                "side": "LONG",
                "framework": "origin_liquidity_sweep_reclaim",
                "origin_family": "liquidity_sweep_reclaim",
                "decision_time_utc": "2026-05-05T08:15:00Z",
                "candidate_ev_r": 0.4,
                "candidate_expected_net_r": 0.32,
                "candidate_probability": 0.62,
                "expected_cost_r": 0.08,
                "fill_probability": 0.70,
                **_quality_fields(),
                "pretrade_cost_packet_status": "PASSED",
                "cost_authority": "broker_calibrated_replay_cost",
                "cost_source_gap_status": "source_bound_cost_authority_present",
                "risk_pct": 1.0,
            }
        ],
        promote_registry,
        scorecard_rows=[{"decision_time_utc": "2026-05-05T08:15:00Z"}],
        order_rows=[
            {
                "candidate_id": "candidate:source-gap",
                "decision_time_utc": "2026-05-05T08:15:00Z",
                "order_status": "filled",
                "final_r": 0.4,
            }
        ],
        source_namespace="fixture_replay",
        generated_utc="2026-06-20T09:45:00Z",
    )

    candidate = result["candidate_rows"][0]
    assert candidate["package_replay_candidate_use_allowed"] is True
    assert candidate["source_bound_package_candidate_use_allowed"] is True
    assert candidate["source_completeness"] == 0.25
    assert candidate["source_completeness_status"] == (
        "source_completeness_missing_degraded_default"
    )
    assert candidate["package_replay_executable_candidate_use_allowed"] is False
    assert candidate["replay_candidate_use_allowed_now"] is False
    assert candidate["package_replay_executable_candidate_use_allowed_reason"] == (
        "source_completeness_below_floor:0.250000"
    )
    assert candidate["selected_by_package_replay"] is False
    assert result["summary"]["source_bound_candidate_use_allowed_rows"] == 1
    assert result["summary"]["executable_candidate_use_allowed_rows"] == 0
    assert result["scorecard_rows"][0]["package_selected_candidate_id"] is None


def test_replay_authority_promote_sleeves_can_admit_without_live_authority() -> None:
    promote_registry = [
        {
            "sleeve_id": "promote:test",
            "sleeve_type": PROMOTE_DEFAULT_OFF_TYPE,
            "package_role": "promote_default_off_signal",
            "framework": "origin_liquidity_sweep_reclaim",
            "origin_family": "liquidity_sweep_reclaim",
            "side": "LONG",
            "symbols": ["AUDJPY"],
            "session_buckets": ["h08_09"],
            "selector_shadow_priority_score": 1.0,
            "combined_source_bound_signal_r": 1.5,
            "scheduler_action_class_counts": {},
        }
    ]
    result = evaluate_ultimate_candidate_package_replay_authority(
        [
            {
                "candidate_id": "candidate:promote",
                "symbol": "AUDJPY",
                "side": "LONG",
                "framework": "origin_liquidity_sweep_reclaim",
                "origin_family": "liquidity_sweep_reclaim",
                "decision_time_utc": "2026-05-05T08:15:00Z",
                "candidate_ev_r": 0.4,
                "candidate_expected_net_r": 0.32,
                "candidate_probability": 0.62,
                "expected_cost_r": 0.08,
                "fill_probability": 0.70,
                "source_completeness": 0.98,
                "source_completeness_status": "source_completeness_present",
                **_quality_fields(),
                "cost_authority": "broker_calibrated_replay_cost",
                "pretrade_cost_packet_status": "PASSED",
                "cost_source_gap_status": "source_bound_cost_authority_present",
                "risk_pct": 1.0,
            }
        ],
        promote_registry,
        scorecard_rows=[{"decision_time_utc": "2026-05-05T08:15:00Z"}],
        order_rows=[
            {
                "candidate_id": "candidate:promote",
                "decision_time_utc": "2026-05-05T08:15:00Z",
                "order_status": "filled",
                "final_r": 0.4,
            }
        ],
        source_namespace="fixture_replay",
        generated_utc="2026-06-20T09:45:00Z",
    )

    candidate = result["candidate_rows"][0]
    assert candidate["matched_promote_default_off_sleeves"] == 1
    assert candidate["admission_sleeve_match_count"] == 1
    assert candidate["package_replay_candidate_use_allowed"] is True
    assert candidate["package_replay_executable_candidate_use_allowed"] is True
    assert candidate["replay_action"] == "replay_admit_limit_first"
    assert candidate["selected_by_package_replay"] is True
    assert candidate["runtime_effect_now"] is False
    assert candidate["live_execution_activation_allowed"] is False
    policy = result["order_policy_rows"][0]
    assert policy["selected_order_type_architecture"] == (
        "limit_first_with_guarded_market_fallback"
    )
    assert policy["execution_order_type_policy_selectable"] is True
    assert policy["order_calls"] == 0


def test_replay_authority_fill_probability_prior_is_not_execution_authority() -> None:
    promote_registry = [
        {
            "sleeve_id": "promote:fill-prior",
            "sleeve_type": PROMOTE_DEFAULT_OFF_TYPE,
            "package_role": "promote_default_off_signal",
            "framework": "origin_liquidity_sweep_reclaim",
            "origin_family": "liquidity_sweep_reclaim",
            "side": "LONG",
            "symbols": ["AUDJPY"],
            "session_buckets": ["h08_09"],
            "selector_shadow_priority_score": 1.0,
            "combined_source_bound_signal_r": 1.5,
            "scheduler_action_class_counts": {},
        }
    ]
    result = evaluate_ultimate_candidate_package_replay_authority(
        [
            {
                "candidate_id": "candidate:fill-prior",
                "symbol": "AUDJPY",
                "side": "LONG",
                "framework": "origin_liquidity_sweep_reclaim",
                "origin_family": "liquidity_sweep_reclaim",
                "decision_time_utc": "2026-05-05T08:15:00Z",
                "candidate_ev_r": 0.6,
                "candidate_expected_net_r": 0.52,
                "candidate_probability": 0.72,
                "expected_cost_r": 0.08,
                "source_completeness": 0.98,
                "source_completeness_status": "source_completeness_present",
                **_quality_fields(),
                "cost_authority": "broker_calibrated_replay_cost",
                "pretrade_cost_packet_status": "PASSED",
                "cost_source_gap_status": "source_bound_cost_authority_present",
                "risk_pct": 1.0,
            }
        ],
        promote_registry,
        scorecard_rows=[{"decision_time_utc": "2026-05-05T08:15:00Z"}],
        order_rows=[
            {
                "candidate_id": "candidate:fill-prior",
                "decision_time_utc": "2026-05-05T08:15:00Z",
                "order_status": "filled",
                "final_r": 0.2,
            }
        ],
        source_namespace="fixture_replay",
        generated_utc="2026-06-20T09:45:00Z",
    )

    candidate = result["candidate_rows"][0]
    assert candidate["package_replay_executable_candidate_use_allowed"] is False
    assert candidate["replay_candidate_use_allowed_now"] is False
    assert candidate["fill_probability"] == 0.0
    assert candidate["model_limit_fill_probability_prior"] == 0.0
    assert candidate["fill_probability_source_bound_input_present"] is False
    assert candidate["fill_probability_authority_class"] == (
        "predecision_model_prior_not_fill_execution_authority"
    )
    assert candidate["package_replay_executable_candidate_use_allowed_reason"] == (
        "fill_probability_missing"
    )


def test_replay_authority_missing_explicit_quality_stays_scoreable_not_executable() -> None:
    promote_registry = [
        {
            "sleeve_id": "promote:quality-gap",
            "sleeve_type": PROMOTE_DEFAULT_OFF_TYPE,
            "package_role": "promote_default_off_signal",
            "framework": "origin_liquidity_sweep_reclaim",
            "origin_family": "liquidity_sweep_reclaim",
            "side": "LONG",
            "symbols": ["AUDJPY"],
            "session_buckets": ["h08_09"],
            "selector_shadow_priority_score": 1.0,
            "combined_source_bound_signal_r": 1.5,
            "scheduler_action_class_counts": {},
        }
    ]
    result = evaluate_ultimate_candidate_package_replay_authority(
        [
            {
                "candidate_id": "candidate:quality-gap",
                "symbol": "AUDJPY",
                "side": "LONG",
                "framework": "origin_liquidity_sweep_reclaim",
                "origin_family": "liquidity_sweep_reclaim",
                "decision_time_utc": "2026-05-05T08:15:00Z",
                "candidate_ev_r": 0.4,
                "expected_cost_r": 0.08,
                "source_completeness": 0.98,
                "source_completeness_status": "source_completeness_present",
                "cost_authority": "broker_calibrated_replay_cost",
                "pretrade_cost_packet_status": "PASSED",
                "cost_source_gap_status": "source_bound_cost_authority_present",
                "risk_pct": 1.0,
            }
        ],
        promote_registry,
        scorecard_rows=[{"decision_time_utc": "2026-05-05T08:15:00Z"}],
        source_namespace="fixture_replay",
        generated_utc="2026-06-20T09:45:00Z",
    )

    candidate = result["candidate_rows"][0]
    assert candidate["package_replay_candidate_use_allowed"] is True
    assert candidate["source_bound_package_candidate_use_allowed"] is True
    assert candidate["package_replay_executable_candidate_use_allowed"] is False
    assert candidate["replay_candidate_use_allowed_now"] is False
    assert candidate["package_replay_executable_candidate_use_allowed_reason"] == (
        "candidate_decision_quality_provenance_missing:"
        "expected_net_r_source_missing,probability_source_missing,"
        "fill_probability_source_missing,source_completeness_source_missing,"
        "candidate_decision_quality_source_boundary_missing,"
        "candidate_decision_quality_alias_status:missing"
    )
    assert candidate["selected_by_package_replay"] is False
    assert result["summary"]["source_bound_candidate_use_allowed_rows"] == 1
    assert result["summary"]["executable_candidate_use_allowed_rows"] == 0


def test_replay_authority_order_results_join_by_candidate_decision_time() -> None:
    promote_registry = [
        {
            "sleeve_id": "promote:exact-order-join",
            "sleeve_type": PROMOTE_DEFAULT_OFF_TYPE,
            "package_role": "promote_default_off_signal",
            "framework": "origin_liquidity_sweep_reclaim",
            "origin_family": "liquidity_sweep_reclaim",
            "side": "LONG",
            "symbols": ["AUDJPY"],
            "session_buckets": ["h08_09"],
            "selector_shadow_priority_score": 1.0,
            "combined_source_bound_signal_r": 1.5,
            "scheduler_action_class_counts": {},
        }
    ]
    candidates = [
        {
            "candidate_id": "candidate:reused",
            "symbol": "AUDJPY",
            "side": "LONG",
            "framework": "origin_liquidity_sweep_reclaim",
            "origin_family": "liquidity_sweep_reclaim",
            "decision_time_utc": "2026-05-05T08:15:00Z",
            "candidate_ev_r": 1.2,
            "candidate_expected_net_r": 1.12,
            "candidate_probability": 0.82,
            "expected_cost_r": 0.08,
            "fill_probability": 0.70,
            "source_completeness": 0.98,
            "source_completeness_status": "source_completeness_present",
            **_quality_fields(),
            "cost_authority": "broker_calibrated_replay_cost",
            "pretrade_cost_packet_status": "PASSED",
            "cost_source_gap_status": "source_bound_cost_authority_present",
            "risk_pct": 1.0,
        },
        {
            "candidate_id": "candidate:reused",
            "symbol": "AUDJPY",
            "side": "LONG",
            "framework": "origin_liquidity_sweep_reclaim",
            "origin_family": "liquidity_sweep_reclaim",
            "decision_time_utc": "2026-05-05T08:30:00Z",
            "candidate_ev_r": 1.3,
            "candidate_expected_net_r": 1.22,
            "candidate_probability": 0.84,
            "expected_cost_r": 0.08,
            "fill_probability": 0.70,
            "source_completeness": 0.98,
            "source_completeness_status": "source_completeness_present",
            **_quality_fields(),
            "cost_authority": "broker_calibrated_replay_cost",
            "pretrade_cost_packet_status": "PASSED",
            "cost_source_gap_status": "source_bound_cost_authority_present",
            "risk_pct": 1.0,
        },
    ]

    result = evaluate_ultimate_candidate_package_replay_authority(
        candidates,
        promote_registry,
        scorecard_rows=[
            {
                "decision_time_utc": "2026-05-05T08:15:00Z",
                "selected_action_class": "zero_trade",
            },
            {
                "decision_time_utc": "2026-05-05T08:30:00Z",
                "selected_action_class": "zero_trade",
            },
        ],
        order_rows=[
            {
                "candidate_id": "candidate:reused",
                "decision_time_utc": "2026-05-05T08:15:00Z",
                "final_r": -1.0,
                "order_status": "filled",
            },
            {
                "candidate_id": "candidate:reused",
                "decision_time_utc": "2026-05-05T08:30:00Z",
                "final_r": 2.0,
                "order_status": "filled",
            },
        ],
        source_namespace="fixture_replay",
        generated_utc="2026-06-20T09:45:00Z",
    )

    candidate_by_time = {
        row["decision_time_utc"]: row for row in result["candidate_rows"]
    }
    assert candidate_by_time["2026-05-05T08:15:00Z"]["replay_order_result_r"] == -1.0
    assert candidate_by_time["2026-05-05T08:15:00Z"][
        "replay_order_result_join_status"
    ] == "exact_candidate_time_join"
    assert candidate_by_time["2026-05-05T08:30:00Z"]["replay_order_result_r"] == 2.0
    assert candidate_by_time["2026-05-05T08:30:00Z"][
        "replay_order_result_join_key"
    ] == "candidate:reused@@2026-05-05T08:30:00Z"

    scorecard_by_time = {
        row["decision_time_utc"]: row for row in result["scorecard_rows"]
    }
    assert scorecard_by_time["2026-05-05T08:15:00Z"][
        "package_replay_result_r"
    ] == -1.0
    assert scorecard_by_time["2026-05-05T08:30:00Z"][
        "package_replay_result_r"
    ] == 2.0
    assert scorecard_by_time["2026-05-05T08:30:00Z"][
        "package_replay_order_result_join_status"
    ] == "exact_candidate_time_join"


def test_replay_authority_does_not_count_expected_value_as_terminal_result() -> None:
    promote_registry = [
        {
            "sleeve_id": "promote:result-authority",
            "sleeve_type": PROMOTE_DEFAULT_OFF_TYPE,
            "package_role": "promote_default_off_signal",
            "framework": "origin_liquidity_sweep_reclaim",
            "origin_family": "liquidity_sweep_reclaim",
            "side": "LONG",
            "symbols": ["AUDJPY"],
            "session_buckets": ["h08_09"],
            "selector_shadow_priority_score": 1.0,
            "combined_source_bound_signal_r": 1.5,
            "scheduler_action_class_counts": {},
        }
    ]
    candidate = {
        "candidate_id": "candidate:ev-only",
        "symbol": "AUDJPY",
        "side": "LONG",
        "framework": "origin_liquidity_sweep_reclaim",
        "origin_family": "liquidity_sweep_reclaim",
        "decision_time_utc": "2026-05-05T08:15:00Z",
        "candidate_ev_r": 1.2,
        "candidate_expected_net_r": 1.12,
        "candidate_probability": 0.82,
        "expected_cost_r": 0.08,
        "fill_probability": 0.70,
        "source_completeness": 0.98,
        "source_completeness_status": "source_completeness_present",
        **_quality_fields(),
        "cost_authority": "broker_calibrated_replay_cost",
        "pretrade_cost_packet_status": "PASSED",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "risk_pct": 1.0,
    }

    result = evaluate_ultimate_candidate_package_replay_authority(
        [candidate],
        promote_registry,
        scorecard_rows=[
            {
                "decision_time_utc": "2026-05-05T08:15:00Z",
                "selected_action_class": "zero_trade",
            }
        ],
        order_rows=[
            {
                "candidate_id": "candidate:ev-only",
                "decision_time_utc": "2026-05-05T08:15:00Z",
                "expectancy_r": 1.2,
                "ev_r": 1.2,
                "order_status": "filled",
            }
        ],
        source_namespace="fixture_replay",
        generated_utc="2026-06-20T09:45:00Z",
    )

    candidate_row = result["candidate_rows"][0]
    scorecard_row = result["scorecard_rows"][0]
    assert candidate_row["replay_order_result_r"] is None
    assert candidate_row["replay_order_expected_r_diagnostic"] == 1.2
    assert candidate_row["replay_order_result_authority_status"] == (
        "expected_value_diagnostic_only_not_terminal_result"
    )
    assert scorecard_row["package_replay_result_r"] is None
    assert scorecard_row["package_expected_r_diagnostic"] == 1.2
    assert scorecard_row["package_replay_result_authority_status"] == (
        "expected_value_diagnostic_only_not_terminal_result"
    )
    assert result["summary"]["scorecards_with_package_result_r"] == 0


def test_replay_authority_terminal_result_overrides_expected_value_diagnostic() -> None:
    promote_registry = [
        {
            "sleeve_id": "promote:terminal-result",
            "sleeve_type": PROMOTE_DEFAULT_OFF_TYPE,
            "package_role": "promote_default_off_signal",
            "framework": "origin_liquidity_sweep_reclaim",
            "origin_family": "liquidity_sweep_reclaim",
            "side": "LONG",
            "symbols": ["AUDJPY"],
            "session_buckets": ["h08_09"],
            "selector_shadow_priority_score": 1.0,
            "combined_source_bound_signal_r": 1.5,
            "scheduler_action_class_counts": {},
        }
    ]
    candidate = {
        "candidate_id": "candidate:terminal",
        "symbol": "AUDJPY",
        "side": "LONG",
        "framework": "origin_liquidity_sweep_reclaim",
        "origin_family": "liquidity_sweep_reclaim",
        "decision_time_utc": "2026-05-05T08:15:00Z",
        "candidate_ev_r": 1.2,
        "candidate_expected_net_r": 1.12,
        "candidate_probability": 0.82,
        "expected_cost_r": 0.08,
        "fill_probability": 0.70,
        "source_completeness": 0.98,
        "source_completeness_status": "source_completeness_present",
        **_quality_fields(),
        "cost_authority": "broker_calibrated_replay_cost",
        "pretrade_cost_packet_status": "PASSED",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "risk_pct": 1.0,
    }

    result = evaluate_ultimate_candidate_package_replay_authority(
        [candidate],
        promote_registry,
        scorecard_rows=[
            {
                "decision_time_utc": "2026-05-05T08:15:00Z",
                "selected_action_class": "zero_trade",
            }
        ],
        order_rows=[
            {
                "candidate_id": "candidate:terminal",
                "decision_time_utc": "2026-05-05T08:15:00Z",
                "counterfactual_final_r": -0.4,
                "expectancy_r": 1.2,
                "ev_r": 1.2,
                "order_status": "filled",
            }
        ],
        source_namespace="fixture_replay",
        generated_utc="2026-06-20T09:45:00Z",
    )

    candidate_row = result["candidate_rows"][0]
    scorecard_row = result["scorecard_rows"][0]
    assert candidate_row["replay_order_result_r"] == -0.4
    assert candidate_row["replay_order_expected_r_diagnostic"] == 1.2
    assert candidate_row["replay_order_result_authority_status"] == (
        "terminal_replay_result:counterfactual_final_r"
    )
    assert scorecard_row["package_replay_result_r"] == -0.4
    assert scorecard_row["package_expected_r_diagnostic"] == 1.2
    assert scorecard_row["package_replay_result_authority_status"] == (
        "terminal_replay_result:counterfactual_final_r"
    )
    assert result["summary"]["scorecards_with_package_result_r"] == 1


def test_replay_authority_non_admission_sleeves_do_not_admit_candidates() -> None:
    avoid_registry = [
        {
            "sleeve_id": "avoid:test",
            "sleeve_type": "avoid_failure_feature_sleeve",
            "package_role": "avoid_failure_feature",
            "framework": "origin_liquidity_sweep_reclaim",
            "origin_family": "liquidity_sweep_reclaim",
            "side": "LONG",
            "symbols": ["AUDJPY"],
            "session_buckets": ["h08_09"],
            "selector_shadow_priority_score": 1.0,
            "combined_source_bound_signal_r": 1.5,
            "scheduler_action_class_counts": {},
        }
    ]
    result = evaluate_ultimate_candidate_package_replay_authority(
        [
            {
                "candidate_id": "candidate:avoid-only",
                "symbol": "AUDJPY",
                "side": "LONG",
                "framework": "origin_liquidity_sweep_reclaim",
                "origin_family": "liquidity_sweep_reclaim",
                "decision_time_utc": "2026-05-05T08:15:00Z",
                "candidate_ev_r": 1.4,
                "candidate_probability": 0.82,
                "expected_cost_r": 0.08,
                "risk_pct": 1.0,
            }
        ],
        avoid_registry,
        scorecard_rows=[{"decision_time_utc": "2026-05-05T08:15:00Z"}],
        source_namespace="fixture_replay",
        generated_utc="2026-06-20T09:45:00Z",
    )

    candidate = result["candidate_rows"][0]
    assert candidate["matched_sleeve_count"] == 1
    assert candidate["admission_sleeve_match_count"] == 0
    assert candidate["avoid_failure_feature_match_count"] == 1
    assert candidate["role_disposition"] == "avoid_feature_only_veto"
    assert candidate["package_replay_candidate_use_allowed"] is False
    assert candidate["replay_action"] == "replay_skip_avoid_feature_only"
    assert candidate["selected_by_package_replay"] is False
    assert candidate["selected_candidate_id"] is None
    scorecard = result["scorecard_rows"][0]
    assert scorecard["package_selected_candidate_id"] is None
    assert scorecard["package_selected_action"] == "replay_skip_avoid_feature_only"
    policy = result["order_policy_rows"][0]
    assert policy["candidate_id"] is None
    assert policy["selected_order_type_architecture"] == "skip"
    assert policy["approved_risk_pct"] == 0.0
    assert policy["order_calls"] == 0
    assert policy["limit_first_vs_guarded_market_comparison_allowed"] is True
    assert policy["runtime_effect_now"] is False
    assert policy["live_execution_activation_allowed"] is False
    assert policy["broker_account_order_history_deal_position_mutation_allowed"] is False


def test_live_decision_packet_captures_ultimate_package_shadow_surface() -> None:
    package = _surface()
    candidate = {
        "candidate_id": "candidate:nas-vol-long",
        "symbol": "NAS100",
        "side": "LONG",
        "framework": "origin_volatility_compression_expansion",
        "origin_family": "volatility_compression_expansion",
        "decision_time_utc": "2026-05-05T06:15:00Z",
    }
    selector_packet = evaluate_ultimate_candidate_selector_shadow(
        candidate,
        package["sleeve_registry_rows"],
        {
            "ultimate_candidate_package_enabled": True,
            "ultimate_candidate_package_shadow_enabled": True,
        },
        generated_utc="2026-06-20T09:45:00Z",
    )
    scheduler_packet = schedule_ultimate_candidate_package_shadow(
        [candidate],
        package["sleeve_registry_rows"],
        {
            "ultimate_candidate_package_enabled": True,
            "ultimate_candidate_package_shadow_enabled": True,
        },
        decision_window_id="window:test",
        generated_utc="2026-06-20T09:45:00Z",
    )
    packet = build_live_decision_packet_v4(
        record={
            "decision_pipeline": {
                "selector_v4": {
                    "component_scores": {
                        "ultimate_candidate_package": selector_packet,
                    },
                },
                "scheduler_v4_best_trade_allocator": {
                    "decision_window_id": "window:test",
                    "candidate_set_id": "candidate-set:test",
                    "input_counts": {"candidate_rows": 1},
                    "zero_trade_value": 0.0,
                    "decision": {
                        "selected_action_class": "new_position",
                        "selected_candidate_id": candidate["candidate_id"],
                    },
                    "ultimate_candidate_package_shadow": scheduler_packet,
                },
            }
        },
        legacy_packet={
            "candidate_identity": {
                "candidate_id": candidate["candidate_id"],
                "broker_symbol": "NAS100",
            },
            "source_m15": {
                "candle_close_utc": "2026-05-05T06:15:00Z",
                "timeframe": "M15",
            },
            "source_completeness": {"source_window_complete": True},
            "order_readiness": {"order_path": "replay"},
        },
        candidate=candidate,
        raw_data={
            "symbol": "NAS100",
            "source_hash": "fixture-source-hash",
            "candle_close_utc": "2026-05-05T06:15:00Z",
        },
        runtime_config={
            "ultimate_candidate_package_enabled": True,
            "ultimate_candidate_package_shadow_enabled": True,
            "ultimate_candidate_package_apply_to_execution": False,
            "ultimate_candidate_package_live_activation_allowed": False,
            "ultimate_candidate_package_final_package_selected": False,
            "ultimate_candidate_package_registry_path": str(SLEEVE_PATH),
        },
    )

    group = packet["field_groups"]["ultimate_candidate_package_selector_scheduler_surface"]
    assert group["group_source_status"] == "captured_present"
    assert group["matched_sleeve_count"] >= 2
    assert group["matched_scheduler_lifecycle_merge_sleeves"] >= 1
    assert group["matched_promote_default_off_sleeves"] == 1
    assert group["shadow_selected_candidate_id"] == candidate["candidate_id"]
    assert group["selected_candidate_id"] is None
    assert group["execution_policy_status"] == "shadow_execution_policy_ready_not_selectable"
    assert group["would_order_entry_policy"]
    assert group["selected_order_type_architecture"] is None
    assert group["execution_order_type_policy_selectable"] is False
    assert group["missed_fill_opportunity_cost_allowed"] is False
    assert "order_type" in group["required_fillability_source_fields"]
    assert "close_side_all_in_cost" in group["required_cost_source_fields"]
    assert group["execution_policy_packet"]["action"] == "shadow_no_order_type_selection_no_execution"
    assert group["approved_risk_pct"] == 0.0
    assert group["runtime_effect_now"] is False
    assert group["candidate_use_allowed_now"] is False
    assert group["final_package_selection_allowed"] is False
    assert group["live_execution_activation_allowed"] is False
    assert group["broker_account_order_history_deal_position_mutation_allowed"] is False
    assert group["order_calls"] == 0
    assert group["gate_violations"] == []
    assert packet["semantic_ownership"]["ultimate_candidate_package"][
        "owner_lane"
    ] == "ultimate_candidate_package_shadow_selector_scheduler_surface"
    assert validate_live_decision_packet_v4(packet) == []


def test_live_decision_packet_validation_rejects_open_ultimate_package_gates() -> None:
    packet = build_live_decision_packet_v4(
        record={"decision_pipeline": {}},
        legacy_packet={
            "candidate_identity": {
                "candidate_id": "candidate:test",
                "broker_symbol": "NAS100",
            },
            "source_m15": {
                "candle_close_utc": "2026-05-05T06:15:00Z",
                "timeframe": "M15",
            },
            "source_completeness": {"source_window_complete": True},
            "order_readiness": {"order_path": "replay"},
        },
        candidate={"candidate_id": "candidate:test", "symbol": "NAS100"},
        raw_data={
            "symbol": "NAS100",
            "source_hash": "fixture-source-hash",
            "candle_close_utc": "2026-05-05T06:15:00Z",
        },
        runtime_config={},
    )
    packet["field_groups"]["ultimate_candidate_package_selector_scheduler_surface"][
        "selected_candidate_id"
    ] = "candidate:test"
    packet["field_groups"]["ultimate_candidate_package_selector_scheduler_surface"][
        "approved_risk_pct"
    ] = 1.0
    packet["field_groups"]["ultimate_candidate_package_selector_scheduler_surface"][
        "selected_order_type_architecture"
    ] = "limit_first"
    packet["field_groups"]["ultimate_candidate_package_selector_scheduler_surface"][
        "execution_order_type_policy_selectable"
    ] = True

    issues = validate_live_decision_packet_v4(packet)

    assert any(
        issue["code"] == "ultimate_candidate_package_selected_candidate_not_closed"
        for issue in issues
    )
    assert any(
        issue["code"] == "ultimate_candidate_package_approved_risk_not_zero"
        for issue in issues
    )
    assert any(
        issue["code"] == "ultimate_candidate_package_order_type_selection_not_closed"
        for issue in issues
    )
    assert any(
        issue["code"] == "ultimate_candidate_package_execution_policy_selectable_not_false"
        for issue in issues
    )
