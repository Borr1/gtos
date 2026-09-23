from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest


MODULE_PATH = Path(__file__).with_name(
    "build_b7_5_selection_sizing_decision_contract.py"
)
SPEC = importlib.util.spec_from_file_location(
    "build_b7_5_selection_sizing_decision_contract", MODULE_PATH
)
assert SPEC is not None and SPEC.loader is not None
builder = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = builder
SPEC.loader.exec_module(builder)

HARNESS_ROUTE = builder.ROOT / builder.EXECUTION_ROUTE
sys.path.insert(0, str(builder.ROOT))
sys.path.insert(0, str(HARNESS_ROUTE))
import run_broad_live_as_if_replay_harness as harness  # noqa: E402
from src.research_infra.v4_timewarp_simulated_live_research_loop import (  # noqa: E402
    b7_5_selection_sizing_factorial_runtime_binding,
)


def _protocol() -> dict:
    protocol, _ = builder.read_and_validate_protocol()
    return protocol


def test_sealed_protocol_validates_and_arm_mutation_fails_closed() -> None:
    protocol = _protocol()
    mutated = copy.deepcopy(protocol)
    mutated["arms"][0]["selection"] = "S1"

    with pytest.raises(
        builder.ContractValidationError, match="four_arm_declaration_mismatch"
    ):
        builder.validate_protocol(
            mutated,
            protocol_file_sha256=builder.EXPECTED_PROTOCOL_SHA256,
        )

    mutated_economics = copy.deepcopy(protocol)
    mutated_economics["matched_risk"]["pending_to_open_transfer_once"] = 1
    with pytest.raises(
        builder.ContractValidationError,
        match="protocol_economics_mismatch:matched_risk.pending_to_open_transfer_once",
    ):
        builder.sealed_protocol_economics(mutated_economics)


def test_source_authority_amendment_chain_is_exact_and_source_only() -> None:
    amendment_r1, amendment_r1_sha256 = builder.read_and_validate_amendment_r1()
    amendment_r2, amendment_r2_sha256 = builder.read_and_validate_amendment_r2()
    amendment_r3, amendment_r3_sha256 = builder.read_and_validate_amendment_r3()

    assert amendment_r1_sha256 == builder.EXPECTED_AMENDMENT_R1_SHA256
    assert amendment_r2_sha256 == builder.EXPECTED_AMENDMENT_R2_SHA256
    assert amendment_r3_sha256 == builder.EXPECTED_AMENDMENT_R3_SHA256
    assert builder.verify_amendment_self_hash(amendment_r1)
    assert builder.verify_amendment_self_hash(amendment_r2)
    assert builder.verify_amendment_self_hash(amendment_r3)
    assert amendment_r1["self_hash"]["sha256"] == (
        builder.EXPECTED_AMENDMENT_R1_SELF_HASH_SHA256
    )
    assert amendment_r2["self_hash"]["sha256"] == (
        builder.EXPECTED_AMENDMENT_R2_SELF_HASH_SHA256
    )
    assert amendment_r3["self_hash"]["sha256"] == (
        builder.EXPECTED_AMENDMENT_R3_SELF_HASH_SHA256
    )
    assert amendment_r1["base_protocol_binding"] == {
        "path": builder.PROTOCOL_RELATIVE_PATH,
        "file_sha256": builder.EXPECTED_PROTOCOL_SHA256,
        "immutable": True,
        "mutation_forbidden": True,
    }
    assert amendment_r1["source_plan_transition"][
        "protocol_source_plan_digest_sha256"
    ] == builder.EXPECTED_ENGINEERING_JUNE_04_PROTOCOL_SOURCE_PLAN_SHA256
    assert amendment_r1["source_plan_transition"][
        "conditional_repaired_source_plan_digest_sha256"
    ] == builder.EXPECTED_ENGINEERING_JUNE_04_R1_CONDITIONAL_SOURCE_PLAN_SHA256
    assert amendment_r1["owner_authorized_source"] == builder.EXPECTED_UKOIL_SOURCE
    assert amendment_r1["immutable_factorial_closure"][
        "amendment_is_arm_varying_treatment"
    ] is False
    assert amendment_r1["outcome_boundary"]["march_outcome_read"] is False

    assert amendment_r2["superseded_r1_binding"]["file_sha256"] == (
        builder.EXPECTED_AMENDMENT_R1_SHA256
    )
    assert amendment_r2["superseded_r1_binding"]["self_hash_sha256"] == (
        builder.EXPECTED_AMENDMENT_R1_SELF_HASH_SHA256
    )
    actual = amendment_r2["correction_evidence"]["actual_repaired"]
    assert actual["source_plan_digest_sha256"] == (
        builder.EXPECTED_ENGINEERING_JUNE_04_ACTUAL_REPAIRED_SOURCE_PLAN_SHA256
    )
    assert actual["static_component_digest_sha256"] == (
        builder.EXPECTED_STATIC_COMPONENT_SHA256
    )
    assert actual["m1_component_digest_sha256"] == (
        builder.EXPECTED_M1_COMPONENT_SHA256
    )
    assert actual["tick_component_digest_sha256"] == (
        builder.EXPECTED_ACTUAL_REPAIRED_TICK_COMPONENT_SHA256
    )
    assert actual["tick_window_plan_digest_sha256"] == (
        builder.EXPECTED_ACTUAL_REPAIRED_TICK_WINDOW_PLAN_SHA256
    )
    assert actual["ukoil_cash_window_digest_sha256"] == (
        builder.EXPECTED_REPAIRED_UKOIL_WINDOW_SHA256
    )
    assert actual["covered_symbol_count"] == 24
    assert actual["covered_component_count"] == 24
    assert actual["exactly_one_v127_component_per_symbol"] is True
    assert actual["bad_row_count"] == 0
    assert amendment_r2["immutable_factorial_closure"][
        "amendment_is_arm_varying_treatment"
    ] is False
    assert amendment_r2["outcome_boundary"]["march_outcome_read"] is False
    assert all(
        amendment_r2["authority_boundary"][field] is False
        for field in (
            "broker_mutation_enabled",
            "broker_authority",
            "live_authority",
            "canary_authority",
            "final_authority",
        )
    )

    assert amendment_r3["prior_chain_binding"]["protocol"]["file_sha256"] == (
        builder.EXPECTED_PROTOCOL_SHA256
    )
    assert amendment_r3["prior_chain_binding"]["r1"]["file_sha256"] == (
        builder.EXPECTED_AMENDMENT_R1_SHA256
    )
    assert amendment_r3["prior_chain_binding"]["r2"]["file_sha256"] == (
        builder.EXPECTED_AMENDMENT_R2_SHA256
    )
    assert amendment_r3["prior_chain_binding"]["r2"][
        "remains_active_for_window_id"
    ] == "engineering_june_04"
    r3_transition = amendment_r3["active_source_plan_transition"]
    assert r3_transition[
        "protocol_and_sealed_contract_source_plan_digest_sha256"
    ] == builder.EXPECTED_DEVELOPMENT_JANUARY_PROTOCOL_SOURCE_PLAN_SHA256
    assert r3_transition[
        "current_reproduced_source_plan_digest_sha256"
    ] == builder.EXPECTED_DEVELOPMENT_JANUARY_R3_SOURCE_PLAN_SHA256
    assert amendment_r3["component_transition"]["static_component_unchanged"] is True
    assert amendment_r3["component_transition"]["m1_component_unchanged"] is True
    assert amendment_r3["component_transition"][
        "only_tick_component_tick_window_and_composite_plan_changed"
    ] is True
    assert amendment_r3["reproduction_audit"]["resolver_run_count"] == 2
    assert amendment_r3["reproduction_audit"]["resolver_runs_identical"] is True
    assert amendment_r3["reproduction_audit"]["march_window_replay_count"] == 0
    assert amendment_r3["reproduction_audit"][
        "march_outcome_artifact_read_count"
    ] == 0
    assert amendment_r3["reproduction_audit"]["march_outcome_read"] is False
    assert amendment_r3["reproduction_audit"][
        "selected_january_authority_file_integrity_hashes_may_traverse_"
        "multi_month_raw_source_containers"
    ] is True
    assert len(amendment_r3["tick_authority_row_transition"]) == 24
    assert all(
        row["digest_changed"]
        for row in amendment_r3["tick_authority_row_transition"]
    )

    tampered = copy.deepcopy(amendment_r2)
    tampered["active_source_plan_transition"][
        "actual_repaired_source_plan_digest_sha256"
    ] = "f" * 64
    assert not builder.verify_amendment_self_hash(tampered)
    with pytest.raises(
        builder.ContractValidationError, match="amendment_r2_self_hash_mismatch"
    ):
        builder.validate_amendment_r2(
            tampered,
            amendment_file_sha256=builder.EXPECTED_AMENDMENT_R2_SHA256,
            protocol_file_sha256=builder.EXPECTED_PROTOCOL_SHA256,
        )

    tampered_r3 = copy.deepcopy(amendment_r3)
    tampered_r3["active_source_plan_transition"][
        "current_reproduced_source_plan_digest_sha256"
    ] = "f" * 64
    assert not builder.verify_amendment_self_hash(tampered_r3)
    with pytest.raises(
        builder.ContractValidationError, match="amendment_r3_self_hash_mismatch"
    ):
        builder.validate_amendment_r3(
            tampered_r3,
            amendment_file_sha256=builder.EXPECTED_AMENDMENT_R3_SHA256,
            protocol_file_sha256=builder.EXPECTED_PROTOCOL_SHA256,
            amendment_r1_file_sha256=builder.EXPECTED_AMENDMENT_R1_SHA256,
            amendment_r2_file_sha256=builder.EXPECTED_AMENDMENT_R2_SHA256,
        )


def test_arm_fingerprint_varies_only_with_declared_factor_deltas() -> None:
    protocol = _protocol()
    common_digest = "a" * 64
    reference = builder.arm_fingerprint(
        protocol,
        protocol["arms"][0],
        common_execution_input_digest_sha256=common_digest,
    )
    role_only_change = dict(protocol["arms"][0], role="not_part_of_fingerprint")
    role_changed = builder.arm_fingerprint(
        protocol,
        role_only_change,
        common_execution_input_digest_sha256=common_digest,
    )
    selection_change = builder.arm_fingerprint(
        protocol,
        protocol["arms"][1],
        common_execution_input_digest_sha256=common_digest,
    )

    assert reference["arm_fingerprint_sha256"] == role_changed["arm_fingerprint_sha256"]
    assert reference["arm_fingerprint_sha256"] != selection_change["arm_fingerprint_sha256"]
    assert set(reference["arm_fingerprint_projection"]) == {
        "common_execution_input_digest_sha256",
        "declared_factor_deltas",
        "protocol_economics",
    }
    assert reference["arm_fingerprint_projection"]["protocol_economics"] == (
        builder.EXPECTED_PROTOCOL_ECONOMICS
    )


def test_contract_is_deterministic_self_hashed_and_replay_free() -> None:
    first = builder.build_contract_payload()
    second = builder.build_contract_payload()

    assert first == second
    assert builder.verify_contract_self_hash(first)
    assert first["outcome_ledger_read_count"] == 0
    assert first["outcome_artifact_read_count"] == 0
    assert first["march_outcome_read"] is False
    assert first["schema"] == "gtos.b7_5.selection_sizing_decision_contract.v2"
    assert first["protocol_binding"]["path"] == builder.PROTOCOL_RELATIVE_PATH
    assert first["protocol_binding"]["file_sha256"] == (
        builder.EXPECTED_PROTOCOL_SHA256
    )
    amendment_binding = first["source_authority_repair_amendment_binding"]
    assert amendment_binding["active_amendment"] == "R3"
    assert amendment_binding["active_amendments_by_window"] == {
        "engineering_june_04": "R2",
        "development_january": "R3",
    }
    r1_binding = amendment_binding["r1_historical_failed_conditional"]
    r2_binding = amendment_binding["r2_active_digest_correction"]
    r3_binding = amendment_binding["r3_active_january_correction"]
    assert r1_binding["path"] == builder.AMENDMENT_R1_RELATIVE_PATH
    assert r1_binding["file_sha256"] == builder.EXPECTED_AMENDMENT_R1_SHA256
    assert r1_binding["self_hash_sha256"] == (
        builder.EXPECTED_AMENDMENT_R1_SELF_HASH_SHA256
    )
    assert r1_binding["source_plan_transition"][
        "conditional_repaired_source_plan_digest_sha256"
    ] == builder.EXPECTED_ENGINEERING_JUNE_04_R1_CONDITIONAL_SOURCE_PLAN_SHA256
    assert r2_binding["path"] == builder.AMENDMENT_R2_RELATIVE_PATH
    assert r2_binding["file_sha256"] == builder.EXPECTED_AMENDMENT_R2_SHA256
    assert r2_binding["self_hash_sha256"] == (
        builder.EXPECTED_AMENDMENT_R2_SELF_HASH_SHA256
    )
    assert r2_binding["superseded_r1_binding"]["file_sha256"] == (
        builder.EXPECTED_AMENDMENT_R1_SHA256
    )
    assert r2_binding["active_source_plan_transition"][
        "actual_repaired_source_plan_digest_sha256"
    ] == (
        builder.EXPECTED_ENGINEERING_JUNE_04_ACTUAL_REPAIRED_SOURCE_PLAN_SHA256
    )
    assert r3_binding["path"] == builder.AMENDMENT_R3_RELATIVE_PATH
    assert r3_binding["file_sha256"] == builder.EXPECTED_AMENDMENT_R3_SHA256
    assert r3_binding["self_hash_sha256"] == (
        builder.EXPECTED_AMENDMENT_R3_SELF_HASH_SHA256
    )
    assert r3_binding["prior_chain_binding"]["r2"]["file_sha256"] == (
        builder.EXPECTED_AMENDMENT_R2_SHA256
    )
    assert r3_binding["active_source_plan_transition"][
        "current_reproduced_source_plan_digest_sha256"
    ] == builder.EXPECTED_DEVELOPMENT_JANUARY_R3_SOURCE_PLAN_SHA256
    assert r3_binding["reproduction_audit"]["resolver_run_count"] == 2
    assert r3_binding["reproduction_audit"]["march_outcome_read"] is False
    assert amendment_binding["common_across_all_arms"] is True
    assert amendment_binding["amendment_is_arm_varying_treatment"] is False
    assert amendment_binding["source_file_read_by_builder"] is False
    assert amendment_binding["outcome_artifact_read_by_builder"] is False
    assert first["factorial_contract"][
        "source_authority_repair_amendment_is_arm_varying_treatment"
    ] is False
    assert first["protocol_economics"] == builder.EXPECTED_PROTOCOL_ECONOMICS
    assert first["protocol_economics_digest_sha256"] == builder.canonical_sha256(
        builder.EXPECTED_PROTOCOL_ECONOMICS
    )
    assert all(
        row["source_plan_artifact_read_by_builder"] is False
        and row["outcome_artifact_read_by_builder"] is False
        for row in first["window_source_plan_bindings"]
    )
    common_inputs = first["input_bindings"]["common_behavior_inputs"]
    amendment_inputs = {
        row["input_id"]: row
        for row in common_inputs
        if row["input_id"].startswith("sealed_source_authority_repair_amendment_")
    }
    assert amendment_inputs[
        "sealed_source_authority_repair_amendment_r1"
    ]["path"] == builder.AMENDMENT_R1_RELATIVE_PATH
    assert amendment_inputs[
        "sealed_source_authority_repair_amendment_r1"
    ]["sha256"] == builder.EXPECTED_AMENDMENT_R1_SHA256
    assert amendment_inputs[
        "sealed_source_authority_repair_amendment_r2"
    ]["path"] == builder.AMENDMENT_R2_RELATIVE_PATH
    assert amendment_inputs[
        "sealed_source_authority_repair_amendment_r2"
    ]["sha256"] == builder.EXPECTED_AMENDMENT_R2_SHA256
    assert amendment_inputs[
        "sealed_source_authority_repair_amendment_r3"
    ]["path"] == builder.AMENDMENT_R3_RELATIVE_PATH
    assert amendment_inputs[
        "sealed_source_authority_repair_amendment_r3"
    ]["sha256"] == builder.EXPECTED_AMENDMENT_R3_SHA256

    windows = {
        row["window_id"]: row for row in first["window_source_plan_bindings"]
    }
    june = windows["engineering_june_04"]
    assert june["protocol_source_plan_digest_sha256"] == (
        builder.EXPECTED_ENGINEERING_JUNE_04_PROTOCOL_SOURCE_PLAN_SHA256
    )
    assert june["source_plan_digest_sha256"] == (
        builder.EXPECTED_ENGINEERING_JUNE_04_ACTUAL_REPAIRED_SOURCE_PLAN_SHA256
    )
    assert june["source_plan_metadata_origin"] == (
        "sealed_source_authority_repair_amendment_r2"
    )
    assert june[
        "r2_actual_digest_reproduced_by_fail_before_replay_"
        "real_root_source_preflight"
    ] is True
    assert june["r1_failed_conditional_source_plan_digest_sha256"] == (
        builder.EXPECTED_ENGINEERING_JUNE_04_R1_CONDITIONAL_SOURCE_PLAN_SHA256
    )
    assert june["old_r1_and_r2_source_plan_arms_may_not_mix"] is True

    january = windows["development_january"]
    assert january["protocol_source_plan_digest_sha256"] == (
        builder.EXPECTED_DEVELOPMENT_JANUARY_PROTOCOL_SOURCE_PLAN_SHA256
    )
    assert january["source_plan_digest_sha256"] == (
        builder.EXPECTED_DEVELOPMENT_JANUARY_R3_SOURCE_PLAN_SHA256
    )
    assert january["source_plan_metadata_origin"] == (
        "sealed_source_authority_repair_amendment_r3"
    )
    assert january[
        "r3_current_digest_reproduced_by_two_replay_free_current_resolver_passes"
    ] is True
    assert january["old_and_r3_source_plan_arms_may_not_mix"] is True
    assert january["engineering_june_04_r2_binding_unchanged"] is True

    protocol_windows = {row["id"]: row for row in _protocol()["windows"]}
    for window_id, window in windows.items():
        if window_id in {"engineering_june_04", "development_january"}:
            continue
        assert window["source_plan_digest_sha256"] == protocol_windows[window_id][
            "source_plan_digest_sha256"
        ]
        assert window["source_plan_metadata_origin"] == (
            "sealed_experiment_protocol"
        )
    march = windows["untouched_treatment_challenge_march"]
    assert march["source_plan_digest_sha256"] is None
    assert march["outcome_read_gate"] == (
        "development_disposition_and_treatment_frozen"
    )
    assert len(
        {
            arm["arm_fingerprint_sha256"]
            for arm in first["factorial_contract"]["arms"]
        }
    ) == 4
    assert all(
        set(arm["arm_fingerprint_projection"])
        == {
            "common_execution_input_digest_sha256",
            "declared_factor_deltas",
            "protocol_economics",
        }
        for arm in first["factorial_contract"]["arms"]
    )

    tampered = copy.deepcopy(first)
    tampered["matched_risk"]["daily_accepted_risk_pct_cap"] = 99.0
    assert not builder.verify_contract_self_hash(tampered)


def test_builder_opens_no_tick_source_outcome_or_replay_artifact(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    accessed: list[str] = []
    original_repo_file = builder._repo_file

    def tracking_repo_file(root: Path, relative_path: str) -> Path:
        accessed.append(relative_path)
        return original_repo_file(root, relative_path)

    monkeypatch.setattr(builder, "_repo_file", tracking_repo_file)
    payload = builder.build_contract_payload()

    expected_paths = {
        ".context/00_core/GTOS_ULTRA_GOAL.md",
        *(spec.relative_path for spec in builder.COMMON_INPUT_SPECS),
        *(spec.relative_path for spec in builder.PACKAGE_INPUT_SPECS),
    }
    assert set(accessed) == expected_paths
    assert builder.EXPECTED_UKOIL_SOURCE["path"] not in accessed
    assert payload["run_campaign_call_count"] == 0
    assert payload["outcome_ledger_read_count"] == 0
    assert payload["outcome_artifact_read_count"] == 0
    assert payload["march_outcome_read"] is False


def test_undeclared_or_outcome_ledger_inputs_are_rejected() -> None:
    with pytest.raises(
        builder.ContractValidationError, match="undeclared_ledger_input_forbidden"
    ):
        builder._validate_input_specs(
            (
                builder.InputSpec(
                    "forbidden_march_scorecard",
                    "package_authority",
                    "research/forbidden/MARCH_SCORECARD_LEDGER.jsonl",
                ),
            )
        )


def test_partial_treatment_arguments_fail_closed_before_file_access() -> None:
    with pytest.raises(
        ValueError, match="selection_sizing_factorial_binding_arguments_incomplete"
    ):
        harness.selection_sizing_factorial_binding_from_args(
            SimpleNamespace(
                decision_contract=None,
                arm_id=None,
                expected_arm_fingerprint_sha256="not-a-digest",
            )
        )

    with pytest.raises(
        ValueError, match="selection_sizing_factorial_expected_fingerprint_invalid"
    ):
        harness.selection_sizing_factorial_binding_from_args(
            SimpleNamespace(
                decision_contract="not-opened.json",
                arm_id="S0R0",
                expected_arm_fingerprint_sha256="not-a-digest",
            )
        )

    with pytest.raises(
        ValueError,
        match="selection_sizing_factorial_partial_ledger_binding_invalid",
    ):
        harness.selection_sizing_factorial_ledger_fields({"arm_id": "S0R0"})


def test_harness_binds_exact_economics_without_global_risk_mutation() -> None:
    payload = builder.build_contract_payload()
    arm = next(
        row
        for row in payload["factorial_contract"]["arms"]
        if row["arm_id"] == "S0R0"
    )
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            prefix=".b7_5_contract_test_",
            suffix=".json",
            dir=builder.ROUTE,
            delete=False,
        ) as handle:
            json.dump(payload, handle, sort_keys=True)
            temporary_path = Path(handle.name)
        binding = harness.selection_sizing_factorial_binding_from_args(
            SimpleNamespace(
                decision_contract=str(temporary_path.relative_to(builder.ROOT)),
                arm_id="S0R0",
                expected_arm_fingerprint_sha256=arm[
                    "arm_fingerprint_sha256"
                ],
            )
        )
        assert binding is not None
        assert binding["protocol_economics"] == (
            harness.B7_5_SELECTION_SIZING_PROTOCOL_ECONOMICS
        )
        assert binding["binding_payload_sha256"] == harness.stable_sha256(
            binding["binding_payload"]
        )

        default_config = harness.build_config(harness.PROFILE_REPAIRED)
        prefix = harness.B7_5_SELECTION_SIZING_FACTORIAL_RUNTIME_PREFIX
        assert not any(
            str(key).startswith(prefix)
            for key in default_config["gtos_vnext_runtime"]
        )
        default_binding = b7_5_selection_sizing_factorial_runtime_binding(
            default_config
        )
        assert default_binding["requested"] is False
        assert default_binding["enabled"] is False
        assert default_binding["valid"] is True
        bound_config = harness.build_config(
            harness.PROFILE_REPAIRED,
            factorial_arm_binding=binding,
        )
        assert bound_config["risk"] == default_config["risk"]
        assert bound_config.get("timewarp_replay_symbol_risk_pct") == (
            default_config.get("timewarp_replay_symbol_risk_pct")
        )

        runtime = bound_config["gtos_vnext_runtime"]
        assert runtime[f"{prefix}binding_payload_sha256"] == binding[
            "binding_payload_sha256"
        ]
        assert runtime[f"{prefix}fixed_account_risk_unit_cash"] == 100.0
        assert runtime[f"{prefix}fixed_denominator_portfolio_r_cash"] == 100.0
        assert runtime[f"{prefix}pending_to_open_transfer_once"] is True
        assert runtime[f"{prefix}expiry_or_close_release_once"] is True
        assert runtime[f"{prefix}ex_post_rescaling_forbidden"] is True
        core_binding = b7_5_selection_sizing_factorial_runtime_binding(
            bound_config,
            fail_on_invalid=True,
        )
        assert core_binding["binding_payload_sha256"] == binding[
            "binding_payload_sha256"
        ]
        assert core_binding["matched_risk"] == binding["matched_risk"]

        ledger_fields = harness.selection_sizing_factorial_ledger_fields(binding)
        assert harness.selection_sizing_factorial_ledger_fields(None) == {}
        assert ledger_fields[
            "b7_5_selection_sizing_factorial_binding_payload_sha256"
        ] == binding["binding_payload_sha256"]
        assert ledger_fields[
            "b7_5_selection_sizing_factorial_fixed_account_risk_unit_cash"
        ] == 100.0
        assert ledger_fields[
            "b7_5_selection_sizing_factorial_ex_post_rescaling_forbidden"
        ] is True
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
