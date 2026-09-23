"""Separate replay economics from accelerator and proof implementation bytes."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping


SHARED_SCHEMA = "gtos.final_moonshot.broad_replay.shared_execution_contract.v1"
ECONOMIC_SCHEMA = (
    "gtos.replay_acceleration.economic_execution_contract.v1"
)
IMPLEMENTATION_SCHEMA = (
    "gtos.replay_acceleration.accelerator_implementation_authority.v1"
)
CONFIG_LOCATION_NORMALIZATION_SCHEMA = (
    "gtos.replay_acceleration.effective_config_location_normalization.v1"
)
CONFIG_LOCATION_ONLY_RUNTIME_FIELDS = (
    "broad_live_as_if_replay_owner_approved_reconstructed_proxy_"
    "selected_policy_expected_net_source_artifact_sha256",
    "broad_live_as_if_replay_owner_approved_reconstructed_proxy_"
    "selected_policy_expected_net_source_path",
    "ultimate_candidate_package_registry_path",
)
REPAIRED_PROFILE = "repaired_package_conversion_v3"
REPAIRED_PROFILE_LOCATION_EQUIVALENT_HASHES = frozenset(
    {
        # Accepted predecessor projection: identical execution config with the
        # replay-route-relative evidence locations retained.
        "f22c2e02f110844043c201e9dbb47a803de1f4f22c328164d48e1e123609d100",
        # Canonical projection after removing only the three location/audit
        # fields above.  Unknown config hashes remain economic differences.
        "5d9c3fae4c965bbb4be7c8dbbec1e9ce79b71aee73dc44f487250022e398c195",
    }
)
REPAIRED_PROFILE_NORMALIZED_CONFIG_SHA256 = (
    "5d9c3fae4c965bbb4be7c8dbbec1e9ce79b71aee73dc44f487250022e398c195"
)
SHARED_PAYLOAD_KEYS = frozenset(
    {
        "schema",
        "code_authority",
        "missing_code_paths",
        "effective_profile_config_hashes",
        "effective_profile_config_hash_semantics",
        "config_file_hashes",
        "ultimate_package_runtime_input_contract",
        "active_replay_symbol_universe",
        "execution_options",
        "window_identity_excluded_from_shared_digest",
        "broker_live_final_authority",
    }
)
SHARED_KEYS = frozenset(
    {
        *SHARED_PAYLOAD_KEYS,
        "exact_profile_config_roots_sha256",
        "exact_risk_profile_bindings",
        "valid",
        "status",
        "shared_execution_contract_digest_sha256",
    }
)
ECONOMIC_OPTION_KEYS = frozenset(
    {
        "profiles",
        "chunk_size",
        "max_candidates_per_symbol_window",
        "smoke_subset",
        "skip_tick_source",
        "use_native_h1",
        "b7_5_selection_sizing_factorial_arm",
    }
)
PROOF_OPTION_KEYS = frozenset(
    {
        "omit_candidate_ledger",
        "omit_candidate_index_ledger",
        "omit_packet_sidecar_ledger",
        "compact_missed_ledger",
        "compact_decision_ledger",
        "compact_scorecard_ledger",
        "compact_event_sink_enabled",
        "compact_event_sink_roles",
        "compact_event_sink_max_shard_bytes",
        "candidate_ledger_packet_max_bytes",
        "scorecard_ledger_packet_max_bytes",
        "compact_scorecard_symbol_risk_config",
        "scorecard_probe_row_limit",
        "gc_between_chunks",
        "parity_gate_after_day",
        "parity_gate_requires_independent_receipt",
        "streaming_proof_archive_enabled",
        "streaming_proof_archive_hot_roles",
        "max_streaming_proof_archive_bytes",
        "source_acceleration",
        "task2_semantic_checkpoint_after_day",
    }
)
KNOWN_OPTION_KEYS = ECONOMIC_OPTION_KEYS | PROOF_OPTION_KEYS


class ContractSplitError(RuntimeError):
    pass


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise ContractSplitError(code)


def _digest(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _is_sha256(value: Any) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(character in "009abcdef" for character in value)
    )


def _normalized_effective_config_contract(
    shared: Mapping[str, Any],
) -> tuple[dict[str, str], dict[str, Any], dict[str, Any]]:
    raw_hashes = shared.get("effective_profile_config_hashes")
    semantics = shared.get("effective_profile_config_hash_semantics")
    _require(
        type(raw_hashes) is dict
        and bool(raw_hashes)
        and all(
            type(profile) is str and _is_sha256(config_hash)
            for profile, config_hash in raw_hashes.items()
        )
        and type(semantics) is dict,
        "effective_profile_config_contract_invalid",
    )
    normalized: dict[str, str] = {}
    rows: list[dict[str, Any]] = []
    for profile in sorted(raw_hashes):
        raw_hash = str(raw_hashes[profile])
        exact_location_alias = (
            profile == REPAIRED_PROFILE
            and raw_hash in REPAIRED_PROFILE_LOCATION_EQUIVALENT_HASHES
        )
        economic_hash = (
            REPAIRED_PROFILE_NORMALIZED_CONFIG_SHA256
            if exact_location_alias
            else raw_hash
        )
        normalized[profile] = economic_hash
        rows.append(
            {
                "profile": profile,
                "raw_effective_config_sha256": raw_hash,
                "economic_effective_config_sha256": economic_hash,
                "exact_location_normalization_allowlist_match": (
                    exact_location_alias
                ),
            }
        )
    all_profiles_location_bound = all(
        row["exact_location_normalization_allowlist_match"] for row in rows
    )
    economic_semantics = (
        {
            "projection": (
                "execution_semantic_config_excludes_exact_noncausal_"
                "runtime_locations"
            ),
            "excluded_runtime_fields": list(
                CONFIG_LOCATION_ONLY_RUNTIME_FIELDS
            ),
            "raw_artifact_sha256_retained_in_runtime_and_ledgers": True,
        }
        if all_profiles_location_bound
        else dict(semantics)
    )
    evidence_core = {
        "schema": CONFIG_LOCATION_NORMALIZATION_SCHEMA,
        "allowed_runtime_fields": list(CONFIG_LOCATION_ONLY_RUNTIME_FIELDS),
        "profiles": rows,
        "all_profiles_exactly_classified": all_profiles_location_bound,
        "unknown_hashes_normalized": False,
    }
    evidence = {
        **evidence_core,
        "normalization_root_sha256": _digest(evidence_core),
    }
    return normalized, economic_semantics, evidence


def split_shared_execution_contract(
    shared: Mapping[str, Any],
) -> dict[str, Any]:
    """Return independently rooted economic and implementation authorities.

    Proof/materialization switches and code hashes are deliberately excluded
    from the economic digest. Unknown switches fail closed instead of being
    silently classified as non-causal.
    """

    _require(type(shared) is dict, "shared_execution_contract_invalid")
    _require(set(shared) == SHARED_KEYS, "shared_execution_contract_invalid")
    _require(
        shared.get("schema") == SHARED_SCHEMA
        and shared.get("valid") is True
        and shared.get("status") == "shared_execution_contract_bound"
        and shared.get("window_identity_excluded_from_shared_digest") is True,
        "shared_execution_contract_invalid",
    )
    shared_projection = {
        key: shared[key] for key in SHARED_PAYLOAD_KEYS
    }
    _require(
        shared.get("shared_execution_contract_digest_sha256")
        == _digest(shared_projection),
        "shared_execution_contract_digest_mismatch",
    )
    options = shared.get("execution_options")
    _require(type(options) is dict, "execution_options_invalid")
    unknown = sorted(set(options) - KNOWN_OPTION_KEYS)
    _require(not unknown, "unknown_execution_options")
    missing_economic = sorted(ECONOMIC_OPTION_KEYS - set(options))
    _require(not missing_economic, "economic_execution_options_missing")
    economic_options = {
        key: options[key] for key in sorted(ECONOMIC_OPTION_KEYS)
    }
    proof_options = {
        key: options[key]
        for key in sorted(PROOF_OPTION_KEYS)
        if key in options
    }
    broker_authority = shared.get("broker_live_final_authority")
    _require(
        broker_authority
        == {
            "live_broker_authority": False,
            "broker_mutation_enabled": False,
            "final_selection_claim": False,
        },
        "broker_authority_open",
    )
    (
        normalized_effective_config_hashes,
        economic_config_semantics,
        config_normalization_evidence,
    ) = _normalized_effective_config_contract(shared)
    _require(
        type(shared.get("code_authority")) is list
        and bool(shared["code_authority"])
        and shared.get("missing_code_paths") == []
        and type(shared.get("active_replay_symbol_universe")) is list
        and bool(shared["active_replay_symbol_universe"]),
        "shared_execution_contract_invalid",
    )
    exact_profile_config_roots = shared.get(
        "exact_profile_config_roots_sha256"
    )
    _require(
        type(exact_profile_config_roots) is dict
        and set(exact_profile_config_roots)
        == set(shared["effective_profile_config_hashes"])
        and all(
            type(profile) is str and _is_sha256(config_root)
            for profile, config_root in exact_profile_config_roots.items()
        ),
        "exact_profile_config_roots_invalid",
    )
    exact_risk_profile_bindings = shared.get("exact_risk_profile_bindings")
    _require(
        type(exact_risk_profile_bindings) is dict
        and set(exact_risk_profile_bindings)
        == set(shared["effective_profile_config_hashes"])
        and all(
            type(profile) is str
            and type(binding) is dict
            and set(binding) == {"path", "sha256"}
            and type(binding.get("path")) is str
            and bool(binding.get("path"))
            and _is_sha256(binding.get("sha256"))
            for profile, binding in exact_risk_profile_bindings.items()
        ),
        "exact_risk_profile_bindings_invalid",
    )
    economic_payload = {
        "schema": ECONOMIC_SCHEMA,
        "effective_profile_config_hashes": normalized_effective_config_hashes,
        "effective_profile_config_hash_semantics": economic_config_semantics,
        "config_file_hashes": shared["config_file_hashes"],
        "ultimate_package_runtime_input_contract": shared[
            "ultimate_package_runtime_input_contract"
        ],
        "active_replay_symbol_universe": shared[
            "active_replay_symbol_universe"
        ],
        "economic_execution_options": economic_options,
        "window_identity_excluded_from_economic_digest": True,
        "broker_live_final_authority": broker_authority,
    }
    economic_digest = _digest(economic_payload)
    implementation_payload = {
        "schema": IMPLEMENTATION_SCHEMA,
        "shared_execution_contract_digest_sha256": shared[
            "shared_execution_contract_digest_sha256"
        ],
        "economic_execution_contract_digest_sha256": economic_digest,
        "code_authority": shared["code_authority"],
        "missing_code_paths": shared["missing_code_paths"],
        "proof_execution_options": proof_options,
        "raw_effective_profile_config_hashes": shared[
            "effective_profile_config_hashes"
        ],
        "exact_profile_config_roots_sha256": exact_profile_config_roots,
        "exact_risk_profile_bindings": exact_risk_profile_bindings,
        "effective_profile_config_location_normalization": (
            config_normalization_evidence
        ),
        "broker_live_final_authority": broker_authority,
    }
    implementation_root = _digest(implementation_payload)
    _require(
        _is_sha256(economic_digest) and _is_sha256(implementation_root),
        "contract_split_root_invalid",
    )
    return {
        "economic_execution_contract": economic_payload,
        "economic_execution_contract_digest_sha256": economic_digest,
        "accelerator_implementation_authority": implementation_payload,
        "accelerator_implementation_authority_root_sha256": (
            implementation_root
        ),
        "effective_profile_config_location_normalization": (
            config_normalization_evidence
        ),
    }
