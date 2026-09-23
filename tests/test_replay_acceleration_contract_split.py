from __future__ import annotations

import copy
import hashlib
import json

import pytest

from src.research_infra.replay_acceleration_contract_split import (
    ContractSplitError,
    split_shared_execution_contract,
)


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _shared_contract() -> dict[str, object]:
    payload: dict[str, object] = {
        "schema": "gtos.final_moonshot.broad_replay.shared_execution_contract.v1",
        "code_authority": [{"path": "runner.py", "sha256": "a" * 64}],
        "missing_code_paths": [],
        "effective_profile_config_hashes": {"profile": "b" * 64},
        "exact_profile_config_roots_sha256": {"profile": "f" * 64},
        "exact_risk_profile_bindings": {
            "profile": {"path": "config/profiles/ftmo.yaml", "sha256": "9" * 64}
        },
        "effective_profile_config_hash_semantics": {
            "projection": "semantic",
            "excluded_runtime_fields": [],
            "raw_artifact_sha256_retained_in_runtime_and_ledgers": True,
        },
        "config_file_hashes": {"config.yaml": "c" * 64},
        "ultimate_package_runtime_input_contract": {"valid": True},
        "active_replay_symbol_universe": ["XAUUSD"],
        "execution_options": {
            "profiles": ["profile"],
            "chunk_size": 1,
            "max_candidates_per_symbol_window": 0,
            "smoke_subset": False,
            "skip_tick_source": False,
            "use_native_h1": False,
            "omit_candidate_ledger": True,
            "omit_candidate_index_ledger": True,
            "omit_packet_sidecar_ledger": True,
            "compact_missed_ledger": True,
            "compact_decision_ledger": True,
            "compact_scorecard_ledger": True,
            "candidate_ledger_packet_max_bytes": 1024,
            "scorecard_ledger_packet_max_bytes": 4096,
            "compact_scorecard_symbol_risk_config": True,
            "scorecard_probe_row_limit": 12,
            "gc_between_chunks": True,
            "b7_5_selection_sizing_factorial_arm": {
                "arm_id": "S0R0",
                "arm_fingerprint_sha256": "d" * 64,
            },
        },
        "window_identity_excluded_from_shared_digest": True,
        "broker_live_final_authority": {
            "live_broker_authority": False,
            "broker_mutation_enabled": False,
            "final_selection_claim": False,
        },
    }
    return {
        **payload,
        "valid": True,
        "status": "shared_execution_contract_bound",
        "shared_execution_contract_digest_sha256": _digest(
            {
                key: value
                for key, value in payload.items()
                if key
                not in {
                    "exact_profile_config_roots_sha256",
                    "exact_risk_profile_bindings",
                }
            }
        ),
    }


def _reroot_shared(value: dict[str, object]) -> None:
    projection = {
        key: item
        for key, item in value.items()
        if key
        not in {
            "valid",
            "status",
            "shared_execution_contract_digest_sha256",
            "exact_profile_config_roots_sha256",
            "exact_risk_profile_bindings",
        }
    }
    value["shared_execution_contract_digest_sha256"] = _digest(projection)


def test_proof_and_accelerator_drift_does_not_relabel_economic_semantics() -> None:
    legacy = _shared_contract()
    accelerated = copy.deepcopy(legacy)
    accelerated["code_authority"] = [
        {"path": "runner.py", "sha256": "e" * 64},
        {"path": "fixed_verifier.py", "sha256": "f" * 64},
    ]
    accelerated["execution_options"].update(
        {
            "parity_gate_after_day": "2026-01-07",
            "parity_gate_requires_independent_receipt": True,
            "streaming_proof_archive_enabled": True,
            "streaming_proof_archive_hot_roles": [
                "decision",
                "scorecard",
                "missed",
            ],
            "max_streaming_proof_archive_bytes": 1024,
            "compact_event_sink_enabled": True,
            "compact_event_sink_roles": ["decision", "missed"],
            "compact_event_sink_max_shard_bytes": 128 * 1024 * 1024,
            "source_acceleration": {
                "source_bundle_root_sha256": "1" * 64,
                "policy_execution_entered": False,
            },
        }
    )
    _reroot_shared(accelerated)

    legacy_split = split_shared_execution_contract(legacy)
    accelerated_split = split_shared_execution_contract(accelerated)

    assert (
        legacy_split["economic_execution_contract_digest_sha256"]
        == accelerated_split["economic_execution_contract_digest_sha256"]
    )
    assert (
        legacy_split["accelerator_implementation_authority_root_sha256"]
        != accelerated_split[
            "accelerator_implementation_authority_root_sha256"
        ]
    )


def test_economic_option_drift_changes_the_economic_contract() -> None:
    reference = _shared_contract()
    changed = copy.deepcopy(reference)
    changed["execution_options"]["max_candidates_per_symbol_window"] = 1
    _reroot_shared(changed)

    assert split_shared_execution_contract(reference)[
        "economic_execution_contract_digest_sha256"
    ] != split_shared_execution_contract(changed)[
        "economic_execution_contract_digest_sha256"
    ]


def test_exact_config_root_is_provenance_not_economic_semantics() -> None:
    reference = _shared_contract()
    changed = copy.deepcopy(reference)
    changed["exact_profile_config_roots_sha256"] = {"profile": "9" * 64}

    reference_split = split_shared_execution_contract(reference)
    changed_split = split_shared_execution_contract(changed)

    assert (
        reference["shared_execution_contract_digest_sha256"]
        == changed["shared_execution_contract_digest_sha256"]
    )
    assert (
        reference_split["economic_execution_contract_digest_sha256"]
        == changed_split["economic_execution_contract_digest_sha256"]
    )
    assert (
        reference_split["accelerator_implementation_authority_root_sha256"]
        != changed_split["accelerator_implementation_authority_root_sha256"]
    )


def test_exact_risk_profile_binding_is_fail_closed_implementation_authority() -> None:
    reference = _shared_contract()
    changed = copy.deepcopy(reference)
    changed["exact_risk_profile_bindings"]["profile"]["sha256"] = "8" * 64

    reference_split = split_shared_execution_contract(reference)
    changed_split = split_shared_execution_contract(changed)

    assert (
        reference_split["economic_execution_contract_digest_sha256"]
        == changed_split["economic_execution_contract_digest_sha256"]
    )
    assert (
        reference_split["accelerator_implementation_authority_root_sha256"]
        != changed_split["accelerator_implementation_authority_root_sha256"]
    )


def test_unknown_execution_option_fails_closed() -> None:
    shared = _shared_contract()
    shared["execution_options"]["future_option"] = True
    _reroot_shared(shared)

    with pytest.raises(ContractSplitError, match="unknown_execution_options"):
        split_shared_execution_contract(shared)


def test_exact_runtime_location_config_alias_is_noncausal_and_unknown_hash_is_not() -> None:
    predecessor = _shared_contract()
    predecessor["effective_profile_config_hashes"] = {
        "repaired_package_conversion_v3": (
            "f22c2e02f110844043c201e9dbb47a803de1f4f22c328164d48e1e123609d100"
        )
    }
    predecessor["exact_profile_config_roots_sha256"] = {
        "repaired_package_conversion_v3": "f" * 64
    }
    predecessor["exact_risk_profile_bindings"] = {
        "repaired_package_conversion_v3": {
            "path": "config/profiles/ftmo.yaml",
            "sha256": "9" * 64,
        }
    }
    predecessor["execution_options"]["profiles"] = [
        "repaired_package_conversion_v3"
    ]
    _reroot_shared(predecessor)
    relocated = copy.deepcopy(predecessor)
    relocated["effective_profile_config_hashes"] = {
        "repaired_package_conversion_v3": (
            "5d9c3fae4c965bbb4be7c8dbbec1e9ce79b71aee73dc44f487250022e398c195"
        )
    }
    relocated["effective_profile_config_hash_semantics"] = {
        "projection": (
            "execution_semantic_config_excludes_diagnostic_provenance"
        ),
        "excluded_runtime_fields": [
            "broad_live_as_if_replay_owner_approved_reconstructed_proxy_"
            "selected_policy_expected_net_source_artifact_sha256",
            "broad_live_as_if_replay_owner_approved_reconstructed_proxy_"
            "selected_policy_expected_net_source_path",
            "ultimate_candidate_package_registry_path",
        ],
        "raw_artifact_sha256_retained_in_runtime_and_ledgers": True,
    }
    _reroot_shared(relocated)

    predecessor_split = split_shared_execution_contract(predecessor)
    relocated_split = split_shared_execution_contract(relocated)

    assert predecessor_split[
        "economic_execution_contract_digest_sha256"
    ] == relocated_split["economic_execution_contract_digest_sha256"]
    assert predecessor_split[
        "accelerator_implementation_authority_root_sha256"
    ] != relocated_split["accelerator_implementation_authority_root_sha256"]
    assert predecessor_split[
        "effective_profile_config_location_normalization"
    ]["all_profiles_exactly_classified"] is True
    unknown = copy.deepcopy(relocated)
    unknown["effective_profile_config_hashes"][
        "repaired_package_conversion_v3"
    ] = "e" * 64
    _reroot_shared(unknown)
    assert split_shared_execution_contract(unknown)[
        "economic_execution_contract_digest_sha256"
    ] != relocated_split["economic_execution_contract_digest_sha256"]
