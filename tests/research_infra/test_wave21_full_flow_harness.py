from __future__ import annotations

import copy
import gzip
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.research_infra import wave21_full_flow_harness as harness
from src.research_infra import wave21_full_flow_verifier as verifier
from src.research_infra.wave21_full_flow_verifier import VerificationError, verify


def test_completed_bar_chronology_has_zero_future_tolerance() -> None:
    decision_time = datetime(2025, 10, 27, 8, 0, tzinfo=timezone.utc)
    exact = {
        "M15": [{"time_utc": "2025-10-27T07:45:00+00:00"}]
    }
    one_microsecond_future = {
        "M15": [{"time_utc": "2025-10-27T07:45:00.000001+00:00"}]
    }

    assert harness.completed_bar_chronology_violations(
        exact, decision_time_utc=decision_time
    ) == []
    violations = harness.completed_bar_chronology_violations(
        one_microsecond_future, decision_time_utc=decision_time
    )
    assert len(violations) == 1
    assert violations[0]["scheduled_close_utc"] == (
        "2025-10-27T08:00:00.000001+00:00"
    )

    explicit_future = {
        "M15": [
            {
                "time_utc": "2025-10-27T07:45:00+00:00",
                "scheduled_close_utc": "2025-10-27T08:00:00.000001+00:00",
            }
        ]
    }
    explicit_violations = harness.completed_bar_chronology_violations(
        explicit_future, decision_time_utc=decision_time
    )
    assert explicit_violations[0]["scheduled_close_authority"] == (
        "row_carried_close_diagnostic_unverified"
    )
    with pytest.raises(
        harness.FullFlowHarnessError,
        match="truth_completed_bar_prefilter_dependency_not_integrated",
    ):
        harness.completed_bar_chronology_violations(
            exact,
            decision_time_utc=decision_time,
            require_explicit_scheduled_close=True,
        )


def test_truth_generator_wrapper_refuses_before_call_without_loader_prefilter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called = 0

    def forbidden_original(_self: object, **_kwargs: object) -> list[object]:
        nonlocal called
        called += 1
        return []

    monkeypatch.setattr(
        harness.V4DecisionCycleCore,
        "generate_candidates",
        forbidden_original,
    )
    core = SimpleNamespace(
        _candidate_generator=(
            harness.broader_origin_generators.generate_live_broader_origin_candidates
        )
    )
    with harness._trace_real_generator_calls(
        source_authority_fields_by_symbol={}, truth_mode=True
    ):
        with pytest.raises(
            harness.FullFlowHarnessError,
            match="truth_completed_bar_prefilter_dependency_not_integrated",
        ):
            harness.V4DecisionCycleCore.generate_candidates(
                core,
                symbol="EURUSD",
                raw_data={"candles": {"M15": []}},
                now_utc=datetime(2025, 10, 27, 8, 0, tzinfo=timezone.utc),
            )
    assert called == 0


def test_hashing_rejects_unsupported_objects_and_naive_datetimes() -> None:
    class Unsupported:
        pass

    with pytest.raises(harness.FullFlowHarnessError, match="unsupported_json_object"):
        harness.stable_sha256({"value": Unsupported()})
    with pytest.raises(harness.FullFlowHarnessError, match="naive_datetime_forbidden"):
        harness.stable_sha256({"value": datetime(2025, 10, 27, 8, 0)})
    with pytest.raises(harness.FullFlowHarnessError, match="naive_timestamp_forbidden"):
        harness.completed_bar_chronology_violations(
            {"M15": [{"time_utc": "2025-10-27T07:45:00"}]},
            decision_time_utc=datetime(
                2025, 10, 27, 8, 0, tzinfo=timezone.utc
            ),
        )


def test_truth_config_is_exact_default_off_flag_and_explicit_dimensions() -> None:
    baseline = {"gtos_vnext_runtime": {}}
    with pytest.raises(
        harness.FullFlowHarnessError, match="truth_mode_must_be_exact_boolean"
    ):
        harness._safety_bound_config(baseline, truth_mode=1)  # type: ignore[arg-type]
    engineering = harness._safety_bound_config(baseline, truth_mode=False)
    truth = harness._safety_bound_config(baseline, truth_mode=True)

    assert (
        engineering["gtos_vnext_runtime"][harness.WAVE21_FULL_FLOW_TRUTH_MODE_KEY]
        is False
    )
    assert (
        truth["gtos_vnext_runtime"][harness.WAVE21_FULL_FLOW_TRUTH_MODE_KEY]
        is True
    )
    assert truth["broad_live_as_if_replay_harness"][
        "completed_bar_only_chronology"
    ] is True
    assert truth["broad_live_as_if_replay_harness"]["arm_dimensions"] == {
        "continuous_session_treatment": "baseline_unchanged",
        "adr006_breaker_buffer_treatment": "baseline_unchanged",
        "forming_bar_treatment": "corrected_completed_bar_only",
    }
    assert baseline == {"gtos_vnext_runtime": {}}


def test_truth_verifier_requires_exact_24_then_independent_source_reopen() -> None:
    config = harness._safety_bound_config({}, truth_mode=True)

    def manifest(symbols: tuple[str, ...]) -> tuple[dict[str, object], dict[str, object]]:
        source_body = {"sources": [{"symbol": symbol} for symbol in symbols]}
        code_path = Path(harness.__file__).resolve()
        code_body = {
            "modules": [
                {
                    "module": harness.__name__,
                    "path": str(code_path),
                    "sha256": harness.file_sha256(code_path),
                    "byte_count": code_path.stat().st_size,
                }
            ]
        }
        inputs = {
            "campaign": {
                "max_candidates_per_symbol_window": 0,
                "run_smoke_subset": False,
            },
            "effective_config_payload": config,
            "config_root_sha256": harness.stable_sha256(config),
            "source_manifest": {
                **source_body,
                "source_root_sha256": harness.stable_sha256(source_body),
            },
            "source_authority": {
                "result_use_scope": "SOURCE_ESTATE_PREFLIGHT_ONLY",
                "loader_owned_source_receipts_attached": False,
            },
            "code_manifest": {
                **code_body,
                "code_root_sha256": harness.stable_sha256(code_body),
            },
            "prepared_day_pack": None,
            "truth_mode": True,
        }
        fingerprint = {
            "input_manifest_root_sha256": harness.stable_sha256(inputs)
        }
        return inputs, fingerprint

    exact_inputs, exact_fingerprint = manifest(
        harness.timewarp.GTOS_24_SYMBOL_SURFACE
    )
    with pytest.raises(
        VerificationError,
        match=(
            "truth_source_authority_independent_reopen_validator_"
            "dependency_not_integrated"
        ),
    ):
        verifier._verify_input_manifest(
            input_manifest=exact_inputs, fingerprint=exact_fingerprint
        )

    overbroad_inputs, overbroad_fingerprint = manifest(
        (*harness.timewarp.GTOS_24_SYMBOL_SURFACE, "UNREGISTERED_SYMBOL")
    )
    with pytest.raises(
        VerificationError, match="truth_source_denominator_not_exact_24"
    ):
        verifier._verify_input_manifest(
            input_manifest=overbroad_inputs, fingerprint=overbroad_fingerprint
        )


def test_source_hash_domains_are_not_conflated() -> None:
    sources, _fixture = harness.build_deterministic_smoke_sources()
    source = sources["XAUUSD"]["M15"]
    sources["XAUUSD"]["M15"] = harness.replace(
        source,
        sha256="a" * 64,
        spec=harness.replace(source.spec, sha256="b" * 64),
    )

    manifest = harness.source_manifest(sources)
    row = next(
        item
        for item in manifest["sources"]
        if item["symbol"] == "XAUUSD" and item["timeframe"] == "M15"
    )
    assert row["resolved_source_identity_sha256"] == "a" * 64
    assert row["source_spec_declared_sha256"] == "b" * 64
    assert row["canonical_normalized_rows_root_sha256"] not in {"a" * 64, "b" * 64}
    assert row["hash_domains_distinct"] is True


def test_source_merge_is_timestamp_primary_and_conflicts_fail_closed() -> None:
    row = {
        "time_utc": "2025-10-27T07:45:00+00:00",
        "symbol": "EURUSD",
        "open": 1.1,
        "high": 1.2,
        "low": 1.0,
        "close": 1.15,
        "volume": 10.0,
    }
    first = harness._resolved_fixture_source(
        symbol="EURUSD", timeframe="M15", rows=[row]
    )
    second = harness._resolved_fixture_source(
        symbol="EURUSD", timeframe="M15", rows=[row]
    )

    merged = harness._merge_sources(
        first, second, source_family="test_exact_merge"
    )

    assert len(merged.rows) == 1
    receipt = merged.component_source_labels[-1]["merge_multiplicity_receipt"]
    assert receipt["input_occurrence_count"] == 2
    assert receipt["unique_timestamp_count"] == 1
    assert receipt["exact_duplicate_occurrence_count"] == 1
    conflicting = harness._resolved_fixture_source(
        symbol="EURUSD", timeframe="M15", rows=[{**row, "close": 1.16}]
    )
    with pytest.raises(
        harness.FullFlowHarnessError,
        match="source_merge_conflicting_same_timestamp",
    ):
        harness._merge_sources(
            first, conflicting, source_family="test_conflicting_merge"
        )


def test_source_merge_never_overwrites_day_authority() -> None:
    first = harness._resolved_fixture_source(
        symbol="EURUSD",
        timeframe="M15",
        rows=[{"time_utc": "2025-10-27T07:45:00+00:00"}],
        day_source_authority={"2025-10-27": {"source": "first"}},
    )
    second = harness._resolved_fixture_source(
        symbol="EURUSD",
        timeframe="M15",
        rows=[{"time_utc": "2025-10-28T07:45:00+00:00"}],
        day_source_authority={"2025-10-27": {"source": "second"}},
    )

    with pytest.raises(
        harness.FullFlowHarnessError,
        match="source_merge_day_authority_conflict",
    ):
        harness._merge_sources(
            first, second, source_family="test_day_authority_conflict"
        )


def test_candidate_retention_preserves_comparison_semantics() -> None:
    candidate = {
        "candidate_id": "c1",
        "symbol": "EURUSD",
        "side": "BUY",
        "decision_time_utc": "2025-10-27T07:15:00+00:00",
        "canonical_replay_candidate_instance_key": "c1@@2025-10-27T07:15:00+00:00",
        "candidate_instance_identity_status": "materialized",
        "entry_price": 1.1,
        "stop_loss": 1.09,
        "take_profit_1": 1.12,
        "geometry_contract": {"entry_price": 1.1, "stop_loss": 1.09},
        "selector_packet": {"action": "OPEN", "reason": "admit"},
        "large_unused_packet": {"rows": [{"x": index} for index in range(20)]},
    }
    retained = harness._harness_candidate_retention_row(candidate)
    full_projection = harness._comparison_projection(
        stage="candidate", ordinal=0, row=candidate
    )
    retained_projection = harness._comparison_projection(
        stage="candidate", ordinal=0, row=retained
    )

    assert "large_unused_packet" not in retained
    assert full_projection == retained_projection
    assert retained["geometry_contract_hash_sha256"] == harness.stable_sha256(
        candidate["geometry_contract"]
    )


def _truth_stage_packet(
    *,
    stage_id: str,
    stage_ordinal: int,
    payload: dict[str, object],
    predecessor: dict[str, object] | None,
    fixed_point_pass: int = 0,
    terminal_disposition: str | None = None,
) -> dict[str, object]:
    stage_payload = {
        "wave21_truth_stage_payload_schema": (
            "gtos.wave21.truth_stage_payload.v1"
        ),
        "wave21_truth_stage_id": stage_id,
        "wave21_truth_stage_status": (
            "EVALUABLE_NONTRADE"
            if terminal_disposition == "TERMINAL_EVALUABLE_NONTRADE"
            else "NOT_EVALUABLE"
            if terminal_disposition == "TERMINAL_NOT_EVALUABLE"
            else "MATERIALIZED"
        ),
        "wave21_truth_stage_failures": (
            ["fixture_terminal"]
            if terminal_disposition == "TERMINAL_NOT_EVALUABLE"
            else []
        ),
        **payload,
    }
    predecessor_receipt = (
        predecessor[harness.WAVE21_TRUTH_STAGE_RECEIPT_FIELD]
        if predecessor is not None
        else None
    )
    identity_root = harness.stable_sha256(
        {
            "schema": harness.WAVE21_TRUTH_IDENTITY_ROOT_SCHEMA,
            "stage_id": stage_id,
            "fixed_point_pass": fixed_point_pass,
            "predecessor_identity_root_sha256": (
                predecessor[harness.WAVE21_TRUTH_IDENTITY_ROOT_FIELD]
                if predecessor is not None
                else None
            ),
            "stage_payload_sha256": harness.stable_sha256(stage_payload),
        }
    )
    packet = {
        **stage_payload,
        harness.WAVE21_TRUTH_IDENTITY_ROOT_FIELD: identity_root,
    }
    receipt = {
        "schema": harness.WAVE21_TRUTH_STAGE_RECEIPT_SCHEMA,
        "stage_id": stage_id,
        "stage_ordinal": stage_ordinal,
        "fixed_point_pass": fixed_point_pass,
        "predecessor_stage_id": (
            predecessor_receipt["stage_id"] if predecessor_receipt else None
        ),
        "predecessor_stage_receipt_sha256": (
            predecessor_receipt["receipt_sha256"] if predecessor_receipt else None
        ),
        "identity_root_sha256": identity_root,
        "payload_sha256": harness.stable_sha256(packet),
        "disposition": terminal_disposition or "MATERIALIZED",
    }
    receipt["receipt_sha256"] = harness.stable_sha256(receipt)
    packet[harness.WAVE21_TRUTH_STAGE_RECEIPT_FIELD] = receipt
    return packet


def _complete_post_lifecycle_cost_packet() -> dict[str, object]:
    quote_geometry = {
        "source_sha256": "9" * 64,
        "trade_id": "trade:1",
        "gross_basis": "fill_anchored_quote_geometry",
        "gross_includes_spread": True,
    }
    lifecycle = {
        "entry_utc": "2025-10-27T08:15:00+00:00",
        "exit_utc": "2025-10-27T09:15:00+00:00",
        "symbol": "EURUSD",
        "account": "FTMO",
        "side": "BUY",
        "elapsed_holding_hours": 1.0,
        "holding_source_status": "actual_simulated_entry_exit_elapsed",
        "source_status": "actual_simulated_lifecycle",
        "provenance": "wave21_source_bound_fixture_lifecycle",
        "entry_price": 1.1,
        "exit_price": 1.11,
        "sl_distance_price": 0.01,
        "quote_geometry": quote_geometry,
    }
    lifecycle_integrity = dict(lifecycle)
    lifecycle["record_sha256"] = hashlib.sha256(
        json.dumps(
            lifecycle_integrity, sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()
    manifest_sha = "7" * 64
    broker_sha = "8" * 64
    components = {
        "spread_r": {
            "value": 0.01,
            "coverage": "MEASURED",
            "provenance": "ordered_quote_fixture",
            "source_role": (
                "observed_quote_spread_attributed_in_fill_anchored_gross"
            ),
            "accounting": (
                "included_in_fill_anchored_gross_no_additional_deduction"
            ),
            "attributed_physical_spread_r": 0.01,
        },
        "expected_slippage_r": {
            "value": 0.02,
            "coverage": "MODELLED",
            "provenance": "source_bound_slippage_fixture",
            "source_role": (
                "source_bound_expected_slippage_not_broker_realized"
            ),
            "cost_inputs_manifest_sha256": manifest_sha,
        },
        "swap_cost_r": {
            "value": 0.0,
            "coverage": "MEASURED",
            "provenance": "actual_elapsed_swap_fixture",
            "source_role": "actual_elapsed_broker_rollover_component",
            "broker_true_costs_artifact_sha256": broker_sha,
        },
        "commission_r": {
            "value": 0.03,
            "coverage": "MEASURED",
            "provenance": "broker_schedule_fixture",
            "source_role": "broker_schedule_component",
            "broker_true_costs_artifact_sha256": broker_sha,
        },
    }
    return {
        "schema": harness.POST_LIFECYCLE_COMPONENT_COST_SCHEMA,
        "cost_role": "post_lifecycle_component_cost",
        "result_use_scope": (
            "SIMULATED_POST_LIFECYCLE_COST_NOT_BROKER_REALIZED"
        ),
        "broker_realized_status": (
            "NOT_EVALUABLE_NO_BROKER_DEAL_COMPONENTS"
        ),
        "trade_id": "trade:1",
        "predecessor": {
            "cost_role": "pretrade_expected_cost",
            "packet_ref": "pretrade:1",
            "components_reused": [],
        },
        "lifecycle": lifecycle,
        "component_sum_order": list(harness.COST_COMPONENT_FIELDS),
        "cost_input_authority": {
            "root_kind": "git_versioned_manifest_bytes",
            "manifest_path": "config/broker_truth/COST_INPUTS_MANIFEST.json",
            "manifest_sha256": manifest_sha,
            "broker_true_costs_artifact_sha256": broker_sha,
        },
        "status": "COMPLETE",
        "components": components,
        "total_cost_r": 0.06,
        "coverage": "MODELLED",
        "total_provenance": "four_component_fixture",
        "failures": [],
    }


def _selected_truth_stage_rows() -> tuple[dict[str, object], list[dict[str, object]]]:
    fingerprint = "b" * 64
    verdict = "c" * 64
    candidate = {
        "candidate_id": "candidate:source-bound",
        "symbol": "EURUSD",
        "side": "BUY",
        "decision_time_utc": "2025-10-27T08:00:00+00:00",
        "canonical_replay_candidate_instance_key": "candidate:source-bound@@2025-10-27T08:00:00+00:00",
        "candidate_instance_identity_status": "materialized",
        "candidate_instance_identity_collision": False,
        harness.WAVE21_TRUTH_CANDIDATE_ORDINAL_FIELD: 0,
        "candidate_identity_contract_status": (
            "valid_emission_v2_candidate_decision_v1_exec_not_final"
        ),
        "candidate_decision_fingerprint_sha256": fingerprint,
        "candidate_decision_fingerprint_status": "materialized",
        "candidate_decision_fingerprint_atoms": {
            "entry_reference_price": 1.1,
            "candidate_class": "NEW_EXPOSURE_CANDIDATE",
        },
        "selector_v4_verdict_hash_sha256": verdict,
        "selector_v4_verdict_predecessor_candidate_decision_fingerprint_sha256": fingerprint,
    }
    source_slot_key = "2025-10-27T08:00:00+00:00@@EURUSD"
    option_atoms = {
        "candidate_occurrence_ordinal": 0,
        "candidate_decision_fingerprint_sha256": fingerprint,
        "selector_v4_verdict_hash_sha256": verdict,
        "scheduler_candidate_option_identity_key": "option:0",
        "scheduler_candidate_option_disposition": "RISK_BEARING_EVALUATED",
        "scheduler_candidate_option_selected": True,
        "scheduler_selected_rank": 0,
        "scheduler_rank_tie_state_sha256": "d" * 64,
    }
    selected_atoms = {
        "candidate_occurrence_ordinal": 0,
        "research_continuous_risk_sizing_proxy_id": "sizing:fixture",
        "research_continuous_risk_sizing_proxy_hash_sha256": "e" * 64,
        "approved_risk_pct": 0.5,
        "final_order_semantics_sha256": "f" * 64,
        "pretrade_expected_cost_sha256": "1" * 64,
        "order_fillability_sha256": "2" * 64,
    }
    fixed_atoms = {
        "scheduler_window_packet_sha256": "3" * 64,
        "candidate_option_atoms": [option_atoms],
        "selected_order_dependent_atoms": [selected_atoms],
    }
    fixed_key = harness.stable_sha256(
        {
            "schema": "gtos.wave21.order_policy_window_fixed_point.v1",
            **fixed_atoms,
        }
    )
    committed_identity = {
        "candidate_decision_fingerprint_sha256": fingerprint,
        "selector_v4_verdict_hash_sha256": verdict,
        "scheduler_candidate_option_identity_key": "option:0",
        "research_continuous_risk_sizing_proxy_id": "sizing:fixture",
        "research_continuous_risk_sizing_proxy_hash_sha256": "e" * 64,
        "final_order_semantics_sha256": "f" * 64,
        "order_policy_fixed_point_key_sha256": fixed_key,
    }
    stages: list[tuple[str, int, dict[str, object]]] = [
        ("source_lineage", 0, {"emission_lineage_hash_sha256": "4" * 64}),
        (
            "candidate_decision_fingerprint",
            0,
            {
                "candidate_decision_fingerprint_sha256": fingerprint,
                "candidate_decision_fingerprint_atoms": candidate[
                    "candidate_decision_fingerprint_atoms"
                ],
            },
        ),
    ]
    for fixed_pass, stable in ((0, False), (1, True)):
        stages.extend(
            [
                (
                    "selector_verdict",
                    fixed_pass,
                    {
                        "candidate_decision_fingerprint_sha256": fingerprint,
                        "selector_v4_verdict_hash_sha256": verdict,
                        "selector_v4_verdict_predecessor_candidate_decision_fingerprint_sha256": fingerprint,
                    },
                ),
                ("scheduler_option", fixed_pass, dict(option_atoms)),
                (
                    "continuous_risk_sizing",
                    fixed_pass,
                    {
                        "research_continuous_risk_sizing_proxy_id": (
                            "sizing:fixture"
                        ),
                        "research_continuous_risk_sizing_proxy_hash_sha256": (
                            "e" * 64
                        ),
                        "approved_risk_pct": 0.5,
                    },
                ),
                (
                    "final_order",
                    fixed_pass,
                    {"final_order_semantics_sha256": "f" * 64},
                ),
                (
                    "pretrade_expected_cost",
                    fixed_pass,
                    {"pretrade_expected_cost_sha256": "1" * 64},
                ),
                (
                    "order_fillability",
                    fixed_pass,
                    {"order_fillability_sha256": "2" * 64},
                ),
                (
                    "fixed_point_convergence",
                    fixed_pass,
                    {
                        "order_policy_fixed_point_pass": fixed_pass,
                        "order_policy_fixed_point_key_sha256": fixed_key,
                        "order_policy_fixed_point_atoms": fixed_atoms,
                        "order_policy_fixed_point_adjacent_stable": stable,
                    },
                ),
            ]
        )
    stages.extend(
        (stage_id, 1, {})
        for stage_id in (
            "executable_instance",
            "fill",
            "exit",
            "post_lifecycle_component_cost",
            "accounting",
        )
    )
    packets: list[dict[str, object]] = []
    for stage_ordinal, (stage_id, fixed_pass, payload) in enumerate(stages):
        payload = dict(payload)
        if stage_id == "executable_instance":
            payload.update(
                {
                    **committed_identity,
                    "executable_instance_hash_sha256": "6" * 64,
                }
            )
        elif stage_id in {"fill", "exit"}:
            payload.update(
                {
                    **committed_identity,
                    "executable_instance_hash_sha256": "6" * 64,
                }
            )
        elif stage_id == "post_lifecycle_component_cost":
            nested_cost = _complete_post_lifecycle_cost_packet()
            cost_assessment = (
                harness._post_lifecycle_component_cost_assessment(nested_cost)
            )
            payload.update(
                {
                    **committed_identity,
                    "executable_instance_hash_sha256": "6" * 64,
                    "status": "MATERIALIZED",
                    "failures": [],
                    "post_lifecycle_component_cost_stage_schema": (
                        harness.POST_LIFECYCLE_COST_STAGE_SCHEMA
                    ),
                    "post_lifecycle_component_cost": nested_cost,
                    "post_lifecycle_component_cost_sha256": (
                        harness.stable_sha256(nested_cost)
                    ),
                    "post_lifecycle_component_cost_assessment": (
                        cost_assessment
                    ),
                }
            )
        elif stage_id == "accounting":
            nested_cost = _complete_post_lifecycle_cost_packet()
            accounting_atoms = {
                **committed_identity,
                "executable_instance_hash_sha256": "6" * 64,
                "post_lifecycle_component_cost_sha256": (
                    harness.stable_sha256(nested_cost)
                ),
                "gross_result_r": 1.0,
                "gross_result_provenance": "exit_stage_fixture",
                "gross_result_source_stage_receipt_sha256": packets[-2][
                    harness.WAVE21_TRUTH_STAGE_RECEIPT_FIELD
                ]["receipt_sha256"],
                "post_lifecycle_total_cost_r": 0.06,
                "net_result_r": 0.94,
                "post_lifecycle_cost_coverage": "MODELLED",
                "broker_realized_status": (
                    "NOT_EVALUABLE_NO_BROKER_DEAL_COMPONENTS"
                ),
                "result_use_scope": (
                    "SIMULATED_POST_LIFECYCLE_ECONOMICS_NOT_BROKER_REALIZED"
                ),
            }
            payload.update(
                {
                    "status": "MATERIALIZED",
                    "failures": [],
                    **accounting_atoms,
                    "post_lifecycle_accounting_schema": (
                        harness.POST_LIFECYCLE_ACCOUNTING_SCHEMA
                    ),
                    "post_lifecycle_accounting_atoms": accounting_atoms,
                    "post_lifecycle_accounting_packet_sha256": (
                        harness.stable_sha256(
                            {
                                "schema": (
                                    harness.POST_LIFECYCLE_ACCOUNTING_SCHEMA
                                ),
                                "atoms": accounting_atoms,
                            }
                        )
                    ),
                }
            )
        packet = _truth_stage_packet(
            stage_id=stage_id,
            stage_ordinal=stage_ordinal,
            payload=payload,
            predecessor=packets[-1] if packets else None,
            fixed_point_pass=fixed_pass,
        )
        packets.append(packet)
    rows = []
    for occurrence_ordinal, packet in enumerate(packets):
        atoms = {
            harness.WAVE21_TRUTH_CHAIN_ORDINAL_FIELD: occurrence_ordinal,
            harness.WAVE21_TRUTH_CHAIN_KIND_FIELD: "candidate",
            harness.WAVE21_TRUTH_SOURCE_SLOT_KEY_FIELD: source_slot_key,
            harness.WAVE21_TRUTH_CANDIDATE_ORDINAL_FIELD: 0,
        }
        rows.append(
            {
                "wave21_truth_chain_occurrence_schema": (
                    harness.WAVE21_TRUTH_CHAIN_OCCURRENCE_SCHEMA
                ),
                harness.WAVE21_TRUTH_CHAIN_ORDINAL_FIELD: occurrence_ordinal,
                harness.WAVE21_TRUTH_CHAIN_KEY_FIELD: (
                    "wave21chain:"
                    + harness.stable_sha256(
                        {
                            "schema": harness.WAVE21_TRUTH_CHAIN_OCCURRENCE_SCHEMA,
                            **atoms,
                        }
                    )
                ),
                harness.WAVE21_TRUTH_CHAIN_KIND_FIELD: "candidate",
                harness.WAVE21_TRUTH_SOURCE_SLOT_KEY_FIELD: source_slot_key,
                harness.WAVE21_TRUTH_CHAIN_ATOMS_FIELD: atoms,
                harness.WAVE21_TRUTH_CANDIDATE_ORDINAL_FIELD: 0,
                harness.WAVE21_TRUTH_STAGE_PACKET_FIELD: packet,
            }
        )
    return candidate, rows


def test_occurrence_stage_dag_requires_full_predecessor_hashed_path() -> None:
    candidate, rows = _selected_truth_stage_rows()
    ledgers = {
        "asof": [{"candidate_generation_emitted_count": 1}],
        "candidate": [candidate],
        harness.WAVE21_TRUTH_STAGE_LEDGER: rows,
    }

    audit = harness._occurrence_stage_dag_audit(
        {"ledgers": ledgers}, ledgers=ledgers
    )

    assert audit["status"] == "PASS"
    assert audit["candidate_occurrence_count"] == 1
    assert audit["complete_accounted_chain_count"] == 1

    deleted = {**ledgers, harness.WAVE21_TRUTH_STAGE_LEDGER: rows[:5] + rows[6:]}
    stopped = harness._occurrence_stage_dag_audit(
        {"ledgers": deleted}, ledgers=deleted
    )
    assert stopped["status"] == "FAIL"
    assert any(
        row["reason"] in {
            "truth_stage_occurrence_ordinal_not_contiguous",
            "truth_stage_ordinal_not_contiguous",
        }
        for row in stopped["failures"]
    )


def test_missing_post_lifecycle_component_stays_in_denominator_and_blocks_headline() -> None:
    _candidate, rows = _selected_truth_stage_rows()
    broken = copy.deepcopy(rows)
    for row in broken:
        packet = row[harness.WAVE21_TRUTH_STAGE_PACKET_FIELD]
        receipt = packet[harness.WAVE21_TRUTH_STAGE_RECEIPT_FIELD]
        if receipt["stage_id"] != "post_lifecycle_component_cost":
            continue
        del packet["post_lifecycle_component_cost"]["components"]["commission_r"]
        break
    else:  # pragma: no cover - fixture contract assertion
        raise AssertionError("post_lifecycle_component_cost fixture missing")

    projection = harness._economic_projection(
        {"ledgers": {harness.WAVE21_TRUTH_STAGE_LEDGER: broken}},
        result_scope="deterministic_smoke",
        denominator_symbols=("EURUSD",),
    )

    costs = projection["post_lifecycle_component_cost_projection"]
    assert costs["denominator_chain_count"] == 1
    assert costs["complete_chain_count"] == 0
    assert costs["not_evaluable_chain_count"] == 1
    assert costs["component_field_counts"] == {
        "spread_r": 0,
        "expected_slippage_r": 0,
        "swap_cost_r": 0,
        "commission_r": 0,
    }
    assert projection["economics_complete_for_all_materialized_lifecycles"] is False
    assert projection["aggregate_economic_headline_status"] == (
        "NOT_EVALUABLE_POST_LIFECYCLE_COMPONENT_OR_ACCOUNTING_GAPS"
    )


def test_all24_denominator_requires_exact_symbol_equality() -> None:
    empty = {"ledgers": {harness.WAVE21_TRUTH_STAGE_LEDGER: []}}
    exact = harness._economic_projection(
        empty,
        result_scope="source_bound_truth",
        denominator_symbols=harness.timewarp.GTOS_24_SYMBOL_SURFACE,
    )
    overbroad = harness._economic_projection(
        empty,
        result_scope="source_bound_truth",
        denominator_symbols=(
            *harness.timewarp.GTOS_24_SYMBOL_SURFACE,
            "UNREGISTERED_SYMBOL",
        ),
    )

    assert exact["all_24_output"]["denominator_is_exact_gtos_24"] is True
    assert overbroad["all_24_output"]["denominator_is_exact_gtos_24"] is False


def test_compact_comparison_reopens_exact_spool_not_retained_view(
    tmp_path: Path,
) -> None:
    candidate = {
        "candidate_id": "c1",
        "canonical_replay_candidate_instance_key": "c1@@t1",
        "source_authority_packet": {"manifest_sha256": "a" * 64},
    }
    sink = harness.ReplayCompactEventSink(root=tmp_path / "sink")
    sink.append("candidate", candidate)
    authority = sink.seal()
    result = {
        "ledgers": {
            "candidate": [
                {
                    "candidate_id": "c1",
                    "canonical_replay_candidate_instance_key": "c1@@t1",
                }
            ]
        },
        "compact_event_sink_authority": authority,
    }

    exact = harness._exact_comparison_ledgers(result, sink)

    assert list(exact["candidate"]) == [candidate]


def _complete_cost_row(**extra: object) -> dict[str, object]:
    return {
        "candidate_id": "c1",
        "symbol": "EURUSD",
        "side": "BUY",
        "decision_time_utc": "2025-10-27T07:15:00+00:00",
        "canonical_replay_candidate_instance_key": "c1@@2025-10-27T07:15:00+00:00",
        "candidate_instance_identity_status": "materialized",
        "spread_r": 0.01,
        "expected_slippage_r": 0.02,
        "swap_cost_r": 0.0,
        "commission_r": 0.03,
        "spread_r_source": "ordered_bid_ask_fixture",
        "expected_slippage_r_source": "source_bound_fixture",
        "swap_cost_r_source": "broker_spec_fixture",
        "commission_r_source": "broker_spec_fixture",
        "pretrade_cost_packet_status": "OK",
        "cost_authority": "source_bound_test",
        "broker_pretrade_cost_source": "four_components",
        "cost_quote_source": "historical_tick_bid_ask",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "candidate_cost_r_fallback_is_authority": False,
        "source_gap_cost_fallback_blocked": False,
        **extra,
    }


def test_independent_verifier_recomputes_serialized_economics(tmp_path: Path) -> None:
    chain_candidate, truth_stage_rows = _selected_truth_stage_rows()
    candidate = _complete_cost_row(
        **chain_candidate,
        origin_family="current_fvg_fill",
        entry_price=1.1,
        stop_loss=1.09,
        take_profit_1=1.12,
        risk_reward_ratio=2.0,
    )
    trade = _complete_cost_row(
        simulated_trade_id="t1",
        gross_r=1.0,
        expected_cost_r=0.06,
        net_proxy_r=0.94,
        net_r=0.94,
        pnl_cash=94.0,
        risk_cash=100.0,
        risk_pct=0.01,
    )
    result = {
        "ledgers": {
            "asof": [
                {
                    "symbol": "EURUSD",
                    "trading_day": "2025-10-27",
                    "decision_time_utc": "2025-10-27T08:00:00+00:00",
                    "raw_data_status": "live_equivalent_raw_data_built_and_mso_computed",
                    "candidate_generation_raw_count": 1,
                    "candidate_generation_emitted_count": 1,
                    "candidate_generation_truncated_count": 0,
                }
            ],
            "candidate": [candidate],
            "trade": [trade],
            harness.WAVE21_TRUTH_STAGE_LEDGER: truth_stage_rows,
        }
    }
    stage_path = tmp_path / "stage.jsonl.gz"
    _rows, stages = harness._project_ledgers_bounded(
        result["ledgers"], collect_rows=False, stage_ledger_path=stage_path
    )
    source_body = {"sources": [{"symbol": "EURUSD"}]}
    effective_config = harness._safety_bound_config({}, truth_mode=False)
    code_path = Path(harness.__file__).resolve()
    code_body = {
        "modules": [
            {
                "module": harness.__name__,
                "path": str(code_path),
                "sha256": harness.file_sha256(code_path),
                "byte_count": code_path.stat().st_size,
            }
        ]
    }
    input_manifest = {
        "campaign": {
            "days": ["2025-10-27"],
            "max_candidates_per_symbol_window": 0,
            "run_smoke_subset": False,
        },
        "effective_config_payload": effective_config,
        "config_root_sha256": harness.stable_sha256(effective_config),
        "source_manifest": {
            **source_body,
            "source_root_sha256": harness.stable_sha256(source_body),
        },
        "code_manifest": {
            **code_body,
            "code_root_sha256": harness.stable_sha256(code_body),
        },
        "prepared_day_pack": None,
        "truth_mode": False,
    }
    fingerprint = harness.build_comparator_fingerprint(
        result,
        stage_summaries=stages,
        input_manifest=input_manifest,
        generation_trace={
            "raw_generation_executed": True,
            "generator_call_count": 1,
            "raw_generated_candidate_count": 1,
            "prepared_candidate_payload_consumed": False,
            "candidate_population_truncated": False,
            "generation_audit_transport_workaround_applied": False,
            "generator_future_or_forming_bar_violation_count": 0,
        },
        result_scope="deterministic_smoke",
    )
    stage_dag = harness._occurrence_stage_dag_audit(
        result, ledgers=result["ledgers"]
    )
    coverage = [
        {
            "symbol": "EURUSD",
            "origin_family": family,
            "side": side,
            "candidate_count": int(
                family == "current_fvg_fill" and side == "BUY"
            ),
        }
        for family in harness.broader_origin_generators.PRODUCTION_ORIGIN_FAMILIES
        + tuple(
            harness.broader_origin_generators.CURRENT_FRAMEWORK_ORIGIN_FAMILY.values()
        )
        for side in ("BUY", "SELL")
    ]
    conservation_body = {
        "schema": harness.CONSERVATION_SCHEMA,
        "expected_decision_slot_count": 1,
        "observed_asof_row_count": 1,
        "silent_continue_or_missing_slot_count": 0,
        "duplicate_decision_slot_count": 0,
        "decision_windows_by_day": {"2025-10-27": 1},
        "expected_slots_by_day": {"2025-10-27": 1},
        "market_calendar_rows": [
            {
                "trading_day": "2025-10-27",
                "weekday": "Monday",
                "decision_window_count": 1,
                "status": "decision_bars_present",
            }
        ],
        "generator_eligible_slot_count": 1,
        "generator_refusal_or_source_disposition_counts": {
            "live_equivalent_raw_data_built_and_mso_computed": 1
        },
        "generator_call_count": 1,
        "raw_generated_candidate_count": 1,
        "emitted_candidate_count": 1,
        "candidate_ledger_row_count": 1,
        "truncated_candidate_count": 0,
        "coverage_cells": coverage,
        "coverage_cell_count": len(coverage),
        "violations": [],
        "status": "PASS",
    }
    conservation = {
        **conservation_body,
        "conservation_root_sha256": harness.stable_sha256(conservation_body),
    }
    fingerprint["occurrence_stage_dag_audit"] = stage_dag
    fingerprint["decision_conservation"] = conservation
    fingerprint_body = dict(fingerprint)
    fingerprint_body.pop("fingerprint_root_sha256")
    fingerprint["fingerprint_root_sha256"] = harness.stable_sha256(
        fingerprint_body
    )
    fingerprint_path = tmp_path / "fingerprint.json"
    harness._atomic_write_json(fingerprint_path, fingerprint)
    receipt_body = {
        "schema": harness.RECEIPT_SCHEMA,
        **harness.GRAPH_BOUNDARY,
        "status": "RAW_GENERATION_ENGINEERING_SMOKE_EXECUTED",
        "raw_generation_executed": True,
        "prepared_candidate_payload_consumed": False,
        "candidate_population_truncated": False,
        "truth_mode_hard_failures": [],
        "truth_mode": False,
        "engineering_only": True,
        "result_bearing_truth_run": False,
        "result_scope": "deterministic_smoke",
        "full_flow_stage_coverage_complete": True,
        "mandatory_stage_zero_counts": [],
        "broker_true_economics_claimed": False,
        "broker_boundary": {
            "broker_adapter": "SimulatedBroker",
            "broker_mutation_enabled": False,
            "order_send_attempts": 0,
        },
        "occurrence_stage_dag_audit": stage_dag,
        "decision_conservation": conservation,
        "generation_trace": {
            "raw_generation_executed": True,
            "generator_call_count": 1,
            "raw_generated_candidate_count": 1,
            "prepared_candidate_payload_consumed": False,
            "candidate_population_truncated": False,
            "generation_audit_transport_workaround_applied": False,
            "generator_future_or_forming_bar_violation_count": 0,
        },
        "inputs": input_manifest,
        "comparator_fingerprint": fingerprint,
    }
    receipt = {
        **receipt_body,
        "receipt_root_sha256": harness.stable_sha256(receipt_body),
    }
    receipt_path = tmp_path / "receipt.json"
    harness._atomic_write_json(receipt_path, receipt)

    verified = verify(
        stage_ledger=stage_path,
        fingerprint_path=fingerprint_path,
        receipt_path=receipt_path,
    )

    assert verified["status"] == "PASS"
    assert verified["producer_summary_imported"] is False
    economics = verified["recomputed_economics"]
    assert economics["legacy_candidate_or_trade_expected_cost_consumed"] is False
    assert economics["post_lifecycle_component_cost_projection"][
        "complete_chain_count"
    ] == 1
    assert economics["post_lifecycle_component_cost_projection"][
        "component_field_sums"
    ] == {
        "spread_r": 0.01,
        "expected_slippage_r": 0.02,
        "swap_cost_r": 0.0,
        "commission_r": 0.03,
    }
    assert economics["post_lifecycle_accounting_projection"]["field_sums"] == {
        "gross_result_r": 1.0,
        "post_lifecycle_total_cost_r": 0.06,
        "net_result_r": 0.94,
    }

    forged_body = dict(receipt_body)
    forged_body["status"] = (
        "RAW_GENERATION_RESEARCH_TIMEWARP_FULL_FLOW_EXECUTED"
    )
    forged = {
        **forged_body,
        "receipt_root_sha256": harness.stable_sha256(forged_body),
    }
    forged_path = tmp_path / "forged_full_flow_receipt.json"
    harness._atomic_write_json(forged_path, forged)
    with pytest.raises(
        VerificationError, match="obsolete_unscoped_full_flow_status_forbidden"
    ):
        verify(
            stage_ledger=stage_path,
            fingerprint_path=fingerprint_path,
            receipt_path=forged_path,
        )


def test_source_authority_preflight_has_complete_bar_and_explicit_tick_gap() -> None:
    if not harness.DEFAULT_LANE_HOLD_ROOT.is_dir() or not harness.DEFAULT_P1_PACKET_ROOT.is_dir():
        pytest.skip("machine-local held source estates are unavailable")

    authority = harness.verify_real_source_estates(verify_payload_bytes=False)

    assert authority["status"] == "PASS"
    assert authority["all_24_bar_surface_complete"] is True
    assert authority["registered_bar_denominator_exact_gtos_24"] is True
    assert authority["loader_owned_source_receipts_attached"] is False
    assert authority["result_bearing_chronology_coverage_complete"] is False
    assert authority["ordered_bid_ask_tick_covered_symbols"] == [
        "EURUSD",
        "USDJPY",
        "XAGUSD",
        "XAUUSD",
    ]
    assert len(authority["ordered_bid_ask_tick_missing_symbols"]) == 20
    assert authority["forbidden_semantic_payloads_loaded"] is False
    assert authority["lane_registry"]["march_manifest_opened"] is False


def test_two_day_real_source_loader_uses_no_prepared_decisions() -> None:
    if not harness.DEFAULT_LANE_HOLD_ROOT.is_dir() or not harness.DEFAULT_P1_PACKET_ROOT.is_dir():
        pytest.skip("machine-local held source estates are unavailable")
    authority = harness.verify_real_source_estates(verify_payload_bytes=False)

    sources, projection = harness.load_real_source_bound_inputs(
        days=("2025-10-27", "2025-10-28"), source_authority=authority
    )

    assert set(sources) == set(harness.timewarp.GTOS_24_SYMBOL_SURFACE)
    assert all(set(source_map) >= {"D1", "H4", "H1", "M15", "M1"} for source_map in sources.values())
    assert set(symbol for symbol, source_map in sources.items() if "TICK" in source_map) == set(
        harness.TICK_COVERED_SYMBOLS
    )
    assert projection["prepared_day_pack"] is None
    assert projection["stored_candidates_or_outcomes_loaded"] is False
    assert projection["future_rows_consumed"] == 0
    assert all(row["mismatch_count"] == 0 for row in projection["m15_cross_checks"])


# ---------------------------------------------------------------------------
# Occurrence-union DAG (candidate occurrence -> exactly one disjoint terminal
# disposition: missed | trade | terminal_unfilled).  This is the graph the raw
# comparator actually emits; the truth-chain model above remains verified for
# runs that emit truth-stage rows.  Added at wave-21 integration when the
# independent verifier was repaired from the stale flattened-chain-only model.
# ---------------------------------------------------------------------------


def _occurrence_row(key: str, **extra: object) -> dict[str, object]:
    return {"canonical_replay_candidate_instance_key": key, **extra}


def _union_ledgers(
    *,
    candidates: list[dict[str, object]],
    missed: list[dict[str, object]] | None = None,
    orders: list[dict[str, object]] | None = None,
    trades: list[dict[str, object]] | None = None,
    truth_rows: list[dict[str, object]] | None = None,
) -> dict[str, list[dict[str, object]]]:
    return {
        "asof": [],
        "candidate": candidates,
        "missed": missed or [],
        "order": orders or [],
        "trade": trades or [],
        harness.WAVE21_TRUTH_STAGE_LEDGER: truth_rows or [],
    }


def _run_union_audit(ledgers: dict[str, list[dict[str, object]]]) -> dict[str, object]:
    return harness._occurrence_stage_dag_audit({"ledgers": ledgers}, ledgers=ledgers)


def _verifier_union_audit(
    ledgers: dict[str, list[dict[str, object]]]
) -> dict[str, object]:
    from src.research_infra.wave21_full_flow_verifier import (
        _OccurrenceStageDagVerifier,
    )

    dag = _OccurrenceStageDagVerifier()
    for row in ledgers["asof"]:
        dag.observe_asof(row, {})
    for row in ledgers["candidate"]:
        dag.observe_candidate(row, {})
    for row in ledgers["missed"]:
        dag.observe_missed(row, {})
    for row in ledgers["order"]:
        dag.observe_order(row, {})
    for row in ledgers["trade"]:
        dag.observe_trade(row, {})
    for row in ledgers[harness.WAVE21_TRUTH_STAGE_LEDGER]:
        dag.observe_truth_stage(row, {})
    return dag.finish()


def test_occurrence_union_dag_passes_on_disjoint_terminals_and_mirrors() -> None:
    ledgers = _union_ledgers(
        candidates=[
            _occurrence_row("cand:missed@@t0"),
            _occurrence_row("cand:trade@@t1"),
            _occurrence_row("cand:unfilled@@t2"),
        ],
        missed=[_occurrence_row("cand:missed@@t0", miss_reason="scheduler_vetoed_candidate")],
        orders=[
            _occurrence_row("cand:trade@@t1", order_status="pending_accepted"),
            _occurrence_row("cand:trade@@t1", order_status="filled"),
            _occurrence_row("cand:unfilled@@t2", order_status="pending_accepted"),
        ],
        trades=[_occurrence_row("cand:trade@@t1", net_r=0.5)],
    )
    audit = _run_union_audit(ledgers)
    assert audit["status"] == "PASS", audit["failures"]
    assert audit["dag_model"] == "candidate_occurrence_disjoint_terminal_v1"
    assert audit["occurrence_disposition_counts"] == {
        "missed": 1,
        "trade": 1,
        "terminal_unfilled": 1,
        "truth_chain_covered": 0,
    }
    assert audit["occurrence_disposition_conservation_exact"] is True
    assert audit["truth_chain_model_active"] is False
    verifier_audit = _verifier_union_audit(ledgers)
    assert harness.stable_sha256(audit) == harness.stable_sha256(verifier_audit)


@pytest.mark.parametrize(
    "mutate,expected_failure",
    [
        (
            lambda ledgers: ledgers["missed"].clear(),
            "candidate_occurrence_without_terminal_disposition",
        ),
        (
            lambda ledgers: ledgers["missed"].append(
                _occurrence_row("cand:trade@@t1")
            ),
            "occurrence_both_missed_and_ordered",
        ),
        (
            lambda ledgers: ledgers["trade"].append(
                _occurrence_row("cand:missed@@t0")
            ),
            "trade_without_order",
        ),
        (
            lambda ledgers: ledgers["trade"].clear(),
            "filled_order_without_trade",
        ),
        (
            lambda ledgers: ledgers["missed"].append(
                _occurrence_row("cand:never-emitted@@t9")
            ),
            "missed_row_without_candidate_occurrence",
        ),
        (
            lambda ledgers: ledgers["candidate"].append(
                _occurrence_row("cand:missed@@t0")
            ),
            "candidate_occurrence_instance_key_duplicate",
        ),
    ],
)
def test_occurrence_union_dag_fails_closed_on_violations(
    mutate, expected_failure: str
) -> None:
    ledgers = _union_ledgers(
        candidates=[
            _occurrence_row("cand:missed@@t0"),
            _occurrence_row("cand:trade@@t1"),
        ],
        missed=[_occurrence_row("cand:missed@@t0")],
        orders=[
            _occurrence_row("cand:trade@@t1", order_status="pending_accepted"),
            _occurrence_row("cand:trade@@t1", order_status="filled"),
        ],
        trades=[_occurrence_row("cand:trade@@t1", net_r=0.5)],
    )
    mutate(ledgers)

    def _all_reasons(audit: dict[str, object]) -> set[str]:
        reasons: set[str] = set()
        for failure in audit["failures"]:
            reasons.add(failure["reason"])
            nested = failure.get("failures")
            if isinstance(nested, list):
                reasons.update(str(item) for item in nested)
        return reasons

    audit = _run_union_audit(ledgers)
    assert audit["status"] == "FAIL"
    assert expected_failure in _all_reasons(audit), _all_reasons(audit)
    verifier_audit = _verifier_union_audit(ledgers)
    assert expected_failure in _all_reasons(verifier_audit), _all_reasons(
        verifier_audit
    )


def test_truth_chain_model_requires_candidate_ordinals_when_chains_exist() -> None:
    chain_candidate, truth_rows = _selected_truth_stage_rows()
    union_candidate = _occurrence_row("cand:union-only@@t7")
    ledgers = _union_ledgers(
        candidates=[chain_candidate, union_candidate],
        missed=[_occurrence_row("cand:union-only@@t7")],
        truth_rows=truth_rows,
    )
    audit = _run_union_audit(ledgers)
    assert audit["truth_chain_model_active"] is True
    reasons = {failure["reason"] for failure in audit["failures"]}
    assert "candidate_occurrence_ordinal_missing_under_truth_chain_model" in reasons


def test_config_loader_neutralizes_a_cached_integration_bound_runner(monkeypatch) -> None:
    """Monolithic suites import the typed-sparse runner long before this
    harness runs, and that cached module binds the integration repository's H1
    fallback roots -- the exact contamination `load_repaired_replay_config`
    refuses. Refusing a cache is not neutralizing it: the loader must import a
    fresh, target-bound copy for its own use and restore the cached module's
    identity for the rest of the session."""

    import importlib
    import sys as _sys

    runner_name = (
        "src.research_infra.replay_acceleration_attempt5_typed_sparse_runner"
    )
    poisoned = importlib.import_module(runner_name)
    if Path(poisoned.MAIN_REPO_ROOT).resolve() == harness.active_target_root():
        # Force the poisoned shape even when this worktree IS the fallback root.
        monkeypatch.setattr(
            poisoned, "MAIN_REPO_ROOT", "/nonexistent/integration/repo"
        )
    config = harness.load_repaired_replay_config()
    assert isinstance(config, dict) and config
    assert _sys.modules[runner_name] is poisoned
