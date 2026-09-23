#!/usr/bin/env python3
"""Owner-approved bounded semantic acceptance for replay-acceleration Task 2.

This verifier deliberately does not reuse the old opaque-byte acceptance bit.
It compares every persisted semantic row in order, permits only the finite
runtime-clock closure declared below, validates the locally available hash
preimages, and fails closed on every unknown difference.
"""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import os
from collections import Counter
from collections.abc import Iterable, Iterator, Mapping, Sequence
from datetime import date, datetime, timedelta
from itertools import zip_longest
from pathlib import Path
from typing import Any

from src.research_infra.replay_canonical_bytes import (
    canonical_bytes as _sealing_canonical_bytes,
)


ROOT = Path(__file__).resolve().parents[2]
PREFIX = (
    "BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_01_SELECTION_SIZING_"
    "S0R0_SOURCE_REPAIRED_R3_CAP_R2"
)
LEGACY_ROOT = ROOT / (
    ".hermes/evidence/task2/latest-golden-20260721-r2/successor-namespace"
)
LEGACY_MANIFEST = ROOT / (
    ".hermes/evidence/task2/latest-golden-20260721-r3/"
    "PARTIAL_GOLDEN_MANIFEST.json"
)
LEGACY_SUCCESSOR_AUTHORITY = ROOT / (
    ".hermes/evidence/task2/latest-golden-20260721-r2/"
    "PARTIAL_GOLDEN_SUCCESSOR_AUTHORITY.json"
)
ACCELERATED_JAN1_7_ROOT = ROOT / (
    "research/operations/"
    "final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/"
    "attempt_5_typed_sparse/ATTEMPT5_S0R0_JAN1_7_PARITY_20260721T234805Z"
)
PHYSICAL_OVERRIDE_RECEIPT = ROOT / (
    ".hermes/receipts/task2/physical-reference-bounded-salvage-"
    "20260722T064314Z/OWNER_ROUTE_OVERRIDE_RECEIPT.json"
)
STRONG_SOURCE_REBIND_AUTHORITY = ROOT / (
    ".hermes/receipts/task2/source-bundle-consumer-rebind-20260722-r7-strong/"
    "SOURCE_BUNDLE_CONSUMER_REBIND_AUTHORITY.json"
)
EXPECTED_STRONG_SOURCE_REBIND_FILE_SHA256 = (
    "b8d81926f9f44f459675c5998ef0b64938f2ed818ab67fe6875944c38c9b220c"
)
EXPECTED_STRONG_SOURCE_REBIND_ROOT_SHA256 = (
    "582ddde81f752c20f8b70643c515b3e8f147bd9db3470fde9f7d5a749f091df3"
)
EXPECTED_SOURCE_PLAN_DIGEST = (
    "85663876fababc9b69c1bd7041c2bd043b286b456c2e635b2a6fc2289192d4e5"
)
EXPECTED_ARM_FINGERPRINT = (
    "2ece240b5fc9434a7ec20919e95cdf549bcd46f1c0311f130458fd4804c6d447"
)
EXPECTED_ECONOMIC_CONTRACT_DIGEST = (
    "7682e9d8d4448b57a9fe461f273d98df03145da8bad198b3b4aee49d5966b62d"
)
EXPECTED_RUNTIME_PRODUCER_SHA256 = (
    "675ab42233272d22e451b623669d5a2cf4e0683b9c67981e1432f64c0cadbebb"
)
EXPECTED_PROP_HEADROOM_PRODUCER_SHA256 = (
    "045eeec3e00cb5e9cd676b670672dd525b8b1b9d4c46b71162fd27c7965ffee0"
)
SCHEMA = "gtos.replay_acceleration.task2_semantic_acceptance.v1"
SEMANTIC_REPORT_ACCEPTANCE_AUTHORIZED = False
ALLOWLIST_SCHEMA = "gtos.replay_acceleration.semantic_volatility_allowlist.v1"
RUNTIME_SENTINEL = "<ALLOWLISTED_NONCAUSAL_RUNTIME_VALUE>"
HASH_SENTINEL = "<PROVEN_TRANSITIVE_RUNTIME_HASH>"
EXACT_ROLES = frozenset({"source", "decision", "bucket", "candidate"})
ROLE_SUFFIXES = {
    "source": "SOURCE_UNIVERSE_LEDGER.jsonl",
    "decision": "DECISION_LEDGER.jsonl",
    "scorecard": "SCORECARD_LEDGER.jsonl",
    "order": "ORDER_LEDGER.jsonl",
    "trade": "TRADE_LEDGER.jsonl",
    "oracle": "ORDERED_PATH_ORACLE_LEDGER.jsonl",
    "missed": "MISSED_OPPORTUNITY_LEDGER.jsonl",
    "bucket": "BUCKET_LEDGER.jsonl",
}
ARCHIVE_ROLES = frozenset({"decision", "scorecard", "missed"})
ACCOUNT_STATE_FIELDS = frozenset(
    {
        "balance",
        "equity",
        "peak_equity",
        "max_drawdown_pct",
        "daily_start_balance",
        "accepted_risk_orders_by_day",
        "accepted_risk_pct_by_day",
        "accepted_risk_orders_by_day_session",
        "accepted_risk_pct_by_day_session",
        "accepted_risk_orders_by_day_decision_time",
        "accepted_risk_pct_by_day_decision_time",
        "accepted_risk_orders_by_day_decision_cluster_side",
        "accepted_risk_pct_by_day_decision_cluster_side",
        "pending_orders",
        "open_positions",
        "closed_trades",
        "event_queue",
        "event_sequence",
    }
)
RESERVATION_ACCOUNT_FIELDS = (
    "accepted_risk_orders_by_day",
    "accepted_risk_pct_by_day",
    "accepted_risk_orders_by_day_session",
    "accepted_risk_pct_by_day_session",
    "accepted_risk_orders_by_day_decision_time",
    "accepted_risk_pct_by_day_decision_time",
    "accepted_risk_orders_by_day_decision_cluster_side",
    "accepted_risk_pct_by_day_decision_cluster_side",
    "pending_orders",
    "open_positions",
)

# Every top-level summary field is assigned one explicit policy.  This is an
# exhaustive schema registry, not a positive comparison whitelist: an unknown
# field fails closed even when both sides contain the same value.
_SUMMARY_EXACT_FIELDS = frozenset(
    {
        "schema",
        "status",
        "output_prefix",
        "profiles_requested",
        "b7_5_selection_sizing_factorial_arm_binding",
        "broker_mutation_enabled",
        "live_broker_authority",
        "final_selection_claim",
        "evidence_class",
        "package_new_entry_authority_payload_contract",
        "package_new_entry_authority_payload_required_for_signed_executable_rows",
        "ultimate_package_runtime_input_contract",
        "candidate_index_ledger_omitted",
        "candidate_ledger_omitted",
        "decision_ledger_compacted",
        "missed_ledger_compacted",
        "packet_sidecar_ledger_omitted",
        "partial_summary_semantics",
        "scorecard_ledger_compacted",
        "source_authority_chunk_invariance_required",
        "source_universe_rows_indexed_so_far",
    }
)
_SUMMARY_SCOPE_FIELDS = frozenset(
    {
        "candidate_relational_materialization",
        "candidate_rows_materialized_so_far",
        "compact_projection_counts_so_far",
        "comparison_rows",
        "last_completed_chunk_id",
        "last_completed_end_day",
        "last_completed_profile",
        "last_completed_split",
        "last_completed_start_day",
        "ledger_write_row_counts_so_far",
        "progress_rows",
        "source_authority_chunk_invariance_contract",
        "source_authority_preflight_checkpoints",
        "split_profile_stats",
    }
)
_SUMMARY_RUNTIME_FIELDS = frozenset(
    {
        "automatic_gc_disabled_during_replay_chunks",
        "automatic_gc_reenabled_between_chunks",
        "caller_automatic_gc_state_restored_after_harness",
        "capacity_safe_chunk_execution_contract",
        "capacity_safe_chunk_execution_required",
        "explicit_gc_collection_after_result_release",
        "gc_between_chunks",
        "generated_at_utc",
        "ledger_file_bytes_flushed_before_partial_summary",
        "route_id",
    }
)
_SUMMARY_AUTHORITY_FIELDS = frozenset(
    {
        "attempt5_execution_identity",
        "b7_5_contract_binding",
        "real_s0r0_parity_gate",
        "runtime_evidence_contract",
        "shared_execution_contract",
        "source_acceleration_authority",
        "streaming_capacity_checks",
        "streaming_proof_archive",
        "streaming_proof_archive_shards",
        "task2_semantic_checkpoint",
    }
)
SUMMARY_FIELD_POLICIES = {
    **{field: "exact_semantic" for field in _SUMMARY_EXACT_FIELDS},
    **{field: "scope_aggregate" for field in _SUMMARY_SCOPE_FIELDS},
    **{field: "noncausal_runtime_envelope" for field in _SUMMARY_RUNTIME_FIELDS},
    **{field: "independently_validated_authority" for field in _SUMMARY_AUTHORITY_FIELDS},
}

_SHARED_CONTRACT_FIELDS = frozenset(
    {
        "active_replay_symbol_universe",
        "broker_live_final_authority",
        "code_authority",
        "config_file_hashes",
        "effective_profile_config_hash_semantics",
        "effective_profile_config_hashes",
        "execution_options",
        "missing_code_paths",
        "schema",
        "shared_execution_contract_digest_sha256",
        "status",
        "ultimate_package_runtime_input_contract",
        "valid",
        "window_identity_excluded_from_shared_digest",
    }
)
_SHARED_CONFIG_SEMANTICS_FIELDS = frozenset(
    {
        "excluded_runtime_fields",
        "projection",
        "raw_artifact_sha256_retained_in_runtime_and_ledgers",
    }
)
_LEGACY_CONFIG_RUNTIME_FIELDS = frozenset(
    {
        "broad_live_as_if_replay_owner_approved_reconstructed_proxy_"
        "selected_policy_expected_net_source_artifact_sha256",
    }
)
_CURRENT_CONFIG_RUNTIME_FIELDS = frozenset(
    {
        *_LEGACY_CONFIG_RUNTIME_FIELDS,
        "broad_live_as_if_replay_owner_approved_reconstructed_proxy_"
        "selected_policy_expected_net_source_path",
        "ultimate_candidate_package_registry_path",
    }
)
_BASE_EXECUTION_OPTION_FIELDS = frozenset(
    {
        "b7_5_selection_sizing_factorial_arm",
        "candidate_ledger_packet_max_bytes",
        "chunk_size",
        "compact_decision_ledger",
        "compact_missed_ledger",
        "compact_scorecard_ledger",
        "compact_scorecard_symbol_risk_config",
        "gc_between_chunks",
        "max_candidates_per_symbol_window",
        "omit_candidate_index_ledger",
        "omit_candidate_ledger",
        "omit_packet_sidecar_ledger",
        "profiles",
        "scorecard_ledger_packet_max_bytes",
        "scorecard_probe_row_limit",
        "skip_tick_source",
        "smoke_subset",
        "use_native_h1",
    }
)
_ACCELERATION_EXECUTION_OPTION_FIELDS = frozenset(
    {
        "max_streaming_proof_archive_bytes",
        "parity_gate_after_day",
        "parity_gate_requires_independent_receipt",
        "source_acceleration",
        "streaming_proof_archive_enabled",
        "streaming_proof_archive_hot_roles",
        "task2_semantic_checkpoint_after_day",
    }
)
_ALLOWED_EXECUTION_OPTION_KEYSETS = frozenset(
    {
        _BASE_EXECUTION_OPTION_FIELDS,
        _BASE_EXECUTION_OPTION_FIELDS
        | (_ACCELERATION_EXECUTION_OPTION_FIELDS - {"task2_semantic_checkpoint_after_day"}),
        _BASE_EXECUTION_OPTION_FIELDS | _ACCELERATION_EXECUTION_OPTION_FIELDS,
    }
)
_B7_CONTRACT_BINDING_FIELDS = frozenset(
    {
        "actual_shared_execution_contract_digest_sha256",
        "actual_source_plan_digests_sha256",
        "expected_shared_execution_contract_digest_sha256",
        "expected_source_plan_digest_sha256",
        "required",
        "selection_sizing_factorial_arm_binding",
        "status",
        "valid",
    }
)
_EXPECTED_SHARED_CAUSAL_ROOT_SHA256 = (
    "b635a446f79a8289dfa4ead09f5dc063e9f0a5af18efe83187386900b55f66bb"
)
_EXPECTED_B7_CAUSAL_ROOT_SHA256 = (
    "e21ed646c36cfae57e687cad8cf5fb13e74334716d6ddab6eaec873c7b57fec4"
)
_EXPECTED_ARM_BINDING_ROOT_SHA256 = (
    "7fa79e7133d7cbb7f68d7d2815f9441914e453a3e383e368117ef603ee08b709"
)
_ALLOWED_CODE_AUTHORITY_ROOTS = frozenset(
    {
        "e8d23b8e7be30f76326a93c6d7ff4fd1bda8dc75a4c367c0b495077ffdca8d09",
        "004c7ce9030532e57f6d7a3617a005ada6d1b2d2174d83fcad453b8c0c9ef005",
        "1309e8c5d3cd07d82279e7eeb54bd1ea35520ea7bb6a99caa85b38d03a763cd5",
    }
)
_ALLOWED_EFFECTIVE_CONFIG_HASH_ROOTS = frozenset(
    {
        "baa26134b0ffe4f3f9905b1567d92d267d56ab871092fc5eef7c8d211d51ee39",
        "e05fcb2a81758feac152e00d5f3fccc3ddfb19c6cf05535ecc0e30ed3c602c51",
    }
)
_ALLOWED_ACCELERATION_OPTION_ROOTS = frozenset(
    {
        "44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a",
        "b9acee874195297de8685e81d2773c6d6731845f81f20cd0362254fb3c0722c3",
        "b6ff4276b893c82908f5b09161908898671fa4b5cda842771d7ce12ec24b8d5e",
    }
)
_NULL_ROOT_SHA256 = (
    "74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b"
)
_ALLOWED_SUMMARY_PROOF_OBJECT_ROOTS = {
    "attempt5_execution_identity": frozenset(
        {_NULL_ROOT_SHA256, "27592c6993358693961893378b980b577908b17044c56f587c5dc1d3a7b6049c"}
    ),
    "real_s0r0_parity_gate": frozenset({_NULL_ROOT_SHA256}),
    "runtime_evidence_contract": frozenset(
        {_NULL_ROOT_SHA256, "127f105bcd978ed48288e73fd4bc56588c46e42fd9976ce9e5e40d575c031092"}
    ),
    "source_acceleration_authority": frozenset(
        {
            _NULL_ROOT_SHA256,
            "fd81e7c40f0db8be7199cce423d5cd33c861860716f370a32b740995da81236f",
            "3d139c326b31ac29a353240ab9916513918ea1f2ec2a1f8eb43efd533502980d",
        }
    ),
    "streaming_capacity_checks": frozenset(
        {
            _NULL_ROOT_SHA256,
            "cdf8de094f3ef706d087136abd1e470258f84daa9ab0c148fb3248bfcc07710b",
            "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
        }
    ),
    "streaming_proof_archive": frozenset(
        {_NULL_ROOT_SHA256, "60131cd8859198cd4fb7708f4e6152efece7f9757ee7832a3238dde48b759949"}
    ),
    "streaming_proof_archive_shards": frozenset(
        {_NULL_ROOT_SHA256, "b8de9308f1f7218eb07880a7b51cc785402af801547731eac5150bfc6880bbd3"}
    ),
    "task2_semantic_checkpoint": frozenset(
        {_NULL_ROOT_SHA256, "cfbe198818e2a7d18870bb30073dd840518a6a3a67914cbe75c5afb8231859e0"}
    ),
}

_LOCAL_PREIMAGE_DERIVED_PATTERNS = frozenset(
    {
        "broker_order_lifecycle_capture_v4_packet/packet_hash_sha256",
        "risk_authority/packet_hash_sha256",
        "risk_authority/prop_firm_headroom/prop_firm_headroom_v4_evaluation/snapshot/snapshot_hash_sha256",
        "risk_authority/prop_firm_headroom/simulated_headroom/snapshot_hash_sha256",
    }
)
_CAMPAIGN_DERIVED_HASH_PROOF_CLASSES = {
    "candidate_packet_sidecar_hash_sha256": "HISTORICAL_HASH_ONLY_NONCAUSAL",
    "packet_sidecar_hash_sha256": "HISTORICAL_HASH_ONLY_NONCAUSAL",
    "risk_authority/order_recomputed_risk_authority_provenance/packet_hash_sha256": "TRANSITIVE_RUNTIME_ONLY_DERIVED_HASH",
    "risk_authority/risk_finalizer_probe_packet_hash_sha256": "TRANSITIVE_RUNTIME_ONLY_DERIVED_HASH",
    "risk_admitted_scheduler_finalizer/probe_rows/*/risk_authority_packet_hash_sha256": "TRANSITIVE_RUNTIME_ONLY_DERIVED_HASH",
    "risk_admitted_scheduler_finalizer/selected_probe_rows/*/risk_authority_packet_hash_sha256": "TRANSITIVE_RUNTIME_ONLY_DERIVED_HASH",
    "risk_admitted_scheduler_finalizer/payload_hash_sha256": "HISTORICAL_HASH_ONLY_NONCAUSAL",
    "finalizer_primary_probe_risk_authority_packet_hash_sha256": "TRANSITIVE_RUNTIME_ONLY_DERIVED_HASH",
    "oracle:risk_authority_packet_hash_sha256": "IDENTITY_ALIAS",
}


class SemanticAcceptanceError(ValueError):
    """The bounded semantic contract did not hold."""


def canonical_bytes(value: Any) -> bytes:
    """R-P1, landed 2026-07-26 under the R2 verification-split contract.

    This encoder used ``allow_nan=True``, with a comment claiming the tagged
    Infinity/NaN identity was intentional. It is not survivable: acceptance is
    decided on BYTES, so ``b"NaN" == b"NaN"`` made two runs that both produced
    an undefined economic value compare EQUAL and this comparator report zero
    differences. All 28 sealing encoders use ``allow_nan=False``.

    The fix landed in ``replay_semantic_parity`` in July and could not land here:
    this file was SHA-bound in the R1 decision contract. OD-2's split moved it to
    ``input_bindings.verification_tooling``, which the enforcement loop does not
    read, so the hole closes now. Routed through the shared encoder so a failure
    names the offending path instead of raising a bare ValueError.
    """

    return _sealing_canonical_bytes(value)


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def producer_sha256(value: Any) -> str:
    material = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _is_sha256(value: Any) -> bool:
    return bool(
        type(value) is str
        and len(value) == 64
        and all(character in "009abcdef" for character in value)
    )


def _is_utc_timestamp(value: Any) -> bool:
    if type(value) is not str or value != value.strip() or "T" not in value:
        return False
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() == timedelta(0)


def _allow(
    role: str,
    path: tuple[str, ...],
    *,
    value_class: str,
    rationale: str,
    proof: str,
) -> dict[str, Any]:
    return {
        "role": role,
        "path": list(path),
        "value_class": value_class,
        "rationale": rationale,
        "proof": proof,
        "may_hide_semantic_or_economic_value": False,
    }


_CLOCK_RATIONALE = (
    "wall-clock capture metadata replaced by the deterministic replay decision clock; "
    "the causal decision timestamp remains separately exact"
)
_LOCAL_HASH_RATIONALE = (
    "hash changes only because its validated local preimage contains an allowlisted "
    "runtime-clock field"
)
_PRODUCER_HASH_RATIONALE = (
    "producer-derived hash-only alias changes transitively with the runtime-clock "
    "packet; every persisted semantic and economic leaf outside this exact hash path "
    "is compared without normalization"
)


def _risk_entries(role: str) -> list[dict[str, Any]]:
    base = ("risk_authority", "prop_firm_headroom")
    entries = [
        _allow(
            role,
            (*base, "simulated_headroom", "captured_at_utc"),
            value_class="wall_clock_timestamp",
            rationale=_CLOCK_RATIONALE,
            proof="valid_utc_and_separate_causal_decision_time_exact",
        ),
        _allow(
            role,
            (*base, "prop_firm_headroom_v4_evaluation", "captured_at_utc"),
            value_class="wall_clock_timestamp",
            rationale=_CLOCK_RATIONALE,
            proof="valid_utc_and_separate_causal_decision_time_exact",
        ),
        _allow(
            role,
            (
                *base,
                "prop_firm_headroom_v4_evaluation",
                "snapshot",
                "captured_at_utc",
            ),
            value_class="wall_clock_timestamp",
            rationale=_CLOCK_RATIONALE,
            proof="valid_utc_and_separate_causal_decision_time_exact",
        ),
        _allow(
            role,
            (*base, "simulated_headroom", "snapshot_hash_sha256"),
            value_class="derived_hash",
            rationale=_LOCAL_HASH_RATIONALE,
            proof="snapshot_hash_recomputed_from_complete_persisted_snapshot",
        ),
        _allow(
            role,
            (
                *base,
                "prop_firm_headroom_v4_evaluation",
                "snapshot",
                "snapshot_hash_sha256",
            ),
            value_class="derived_hash",
            rationale=_LOCAL_HASH_RATIONALE,
            proof="snapshot_hash_recomputed_from_complete_persisted_snapshot",
        ),
        _allow(
            role,
            ("risk_authority", "packet_hash_sha256"),
            value_class="derived_hash",
            rationale=_LOCAL_HASH_RATIONALE,
            proof="risk_packet_hash_recomputed_from_complete_persisted_packet",
        ),
        _allow(
            role,
            ("risk_authority_packet_hash_sha256",),
            value_class="derived_hash",
            rationale=_LOCAL_HASH_RATIONALE,
            proof="exact_alias_of_validated_nested_risk_packet_hash",
        ),
        _allow(
            role,
            (
                "risk_authority",
                "order_recomputed_risk_authority_provenance",
                "packet_hash_sha256",
            ),
            value_class="derived_hash",
            rationale=_PRODUCER_HASH_RATIONALE,
            proof="explicit_pre_finalizer_producer_hash_alias_and_full_row_projection",
        ),
        _allow(
            role,
            ("risk_authority", "risk_finalizer_probe_packet_hash_sha256"),
            value_class="derived_hash",
            rationale=_PRODUCER_HASH_RATIONALE,
            proof="cross_ledger_scorecard_probe_hash_alias_and_full_row_projection",
        ),
    ]
    return entries


VOLATILITY_ALLOWLIST: tuple[dict[str, Any], ...] = tuple(
    [
        _allow(
            "order",
            ("broker_order_lifecycle_capture_v4_packet", "generated_at_utc"),
            value_class="wall_clock_timestamp",
            rationale=_CLOCK_RATIONALE,
            proof="valid_utc_and_separate_causal_decision_time_exact",
        ),
        _allow(
            "order",
            (
                "broker_order_lifecycle_capture_v4_packet",
                "packet_hash_sha256",
            ),
            value_class="derived_hash",
            rationale=_LOCAL_HASH_RATIONALE,
            proof="lifecycle_hash_recomputed_from_complete_persisted_packet",
        ),
        _allow(
            "order",
            (
                "broker_order_lifecycle_capture_v4_packet",
                "pre_order_capture_contract",
                "execution_manager_packet_hash",
            ),
            value_class="derived_hash",
            rationale=_PRODUCER_HASH_RATIONALE,
            proof="execution_preimage_producer_closure_and_full_row_projection",
        ),
        _allow(
            "order",
            ("candidate_packet_sidecar_hash_sha256",),
            value_class="derived_hash",
            rationale=_PRODUCER_HASH_RATIONALE,
            proof="candidate_hash_alias_consistency_and_full_row_projection",
        ),
        _allow(
            "order",
            ("packet_sidecar_hash_sha256",),
            value_class="derived_hash",
            rationale=_PRODUCER_HASH_RATIONALE,
            proof="candidate_hash_alias_consistency_and_full_row_projection",
        ),
        *_risk_entries("order"),
        _allow(
            "trade",
            ("broker_order_lifecycle_capture_v4_packet", "generated_at_utc"),
            value_class="wall_clock_timestamp",
            rationale=_CLOCK_RATIONALE,
            proof="valid_utc_and_separate_causal_decision_time_exact",
        ),
        _allow(
            "trade",
            (
                "broker_order_lifecycle_capture_v4_packet",
                "packet_hash_sha256",
            ),
            value_class="derived_hash",
            rationale=_LOCAL_HASH_RATIONALE,
            proof="lifecycle_hash_recomputed_from_complete_persisted_packet",
        ),
        _allow(
            "trade",
            (
                "broker_order_lifecycle_capture_v4_packet",
                "pre_order_capture_contract",
                "execution_manager_packet_hash",
            ),
            value_class="derived_hash",
            rationale=_PRODUCER_HASH_RATIONALE,
            proof="execution_preimage_producer_closure_and_full_row_projection",
        ),
        _allow(
            "trade",
            ("candidate_packet_sidecar_hash_sha256",),
            value_class="derived_hash",
            rationale=_PRODUCER_HASH_RATIONALE,
            proof="candidate_hash_alias_consistency_and_full_row_projection",
        ),
        _allow(
            "trade",
            ("packet_sidecar_hash_sha256",),
            value_class="derived_hash",
            rationale=_PRODUCER_HASH_RATIONALE,
            proof="candidate_hash_alias_consistency_and_full_row_projection",
        ),
        *_risk_entries("trade"),
        _allow(
            "oracle",
            ("packet_sidecar_hash_sha256",),
            value_class="derived_hash",
            rationale=_PRODUCER_HASH_RATIONALE,
            proof="candidate_hash_alias_consistency_and_full_row_projection",
        ),
        _allow(
            "oracle",
            ("risk_authority_packet_hash_sha256",),
            value_class="derived_hash",
            rationale=_PRODUCER_HASH_RATIONALE,
            proof="order_identity_risk_hash_alias_and_full_row_projection",
        ),
        _allow(
            "missed",
            ("packet_sidecar_hash_sha256",),
            value_class="derived_hash",
            rationale=_PRODUCER_HASH_RATIONALE,
            proof="candidate_identity_hash_alias_and_full_row_projection",
        ),
        _allow(
            "missed",
            ("risk_authority_packet_hash_sha256",),
            value_class="derived_hash",
            rationale=_PRODUCER_HASH_RATIONALE,
            proof="finalizer_or_pre_scheduler_hash_alias_and_full_row_projection",
        ),
        _allow(
            "scorecard",
            (
                "risk_admitted_scheduler_finalizer",
                "probe_rows",
                "*",
                "risk_authority_packet_hash_sha256",
            ),
            value_class="derived_hash",
            rationale=_PRODUCER_HASH_RATIONALE,
            proof="bounded_finalizer_probe_hash_alias_and_full_probe_projection",
        ),
        _allow(
            "scorecard",
            (
                "risk_admitted_scheduler_finalizer",
                "selected_probe_rows",
                "*",
                "risk_authority_packet_hash_sha256",
            ),
            value_class="derived_hash",
            rationale=_PRODUCER_HASH_RATIONALE,
            proof="bounded_selected_probe_hash_alias_and_full_probe_projection",
        ),
        _allow(
            "scorecard",
            ("risk_admitted_scheduler_finalizer", "payload_hash_sha256"),
            value_class="derived_hash",
            rationale=_PRODUCER_HASH_RATIONALE,
            proof="compacted_finalizer_payload_hash_and_full_compact_projection",
        ),
        _allow(
            "scorecard",
            ("finalizer_primary_probe_risk_authority_packet_hash_sha256",),
            value_class="derived_hash",
            rationale=_PRODUCER_HASH_RATIONALE,
            proof="exact_alias_of_primary_finalizer_probe_hash",
        ),
        _allow(
            "state_checkpoint",
            ("state_projection", "account_root_sha256"),
            value_class="derived_hash",
            rationale=(
                "the opaque account root transitively includes closed-trade runtime "
                "hash aliases; every AccountState semantic field is independently "
                "bound by exact progress economics, reservation, broker, event, "
                "order, trade, and sequence witnesses"
            ),
            proof="complete_account_state_field_coverage_and_temporal_isolation",
        ),
        _allow(
            "state_checkpoint",
            ("state_root_sha256",),
            value_class="derived_hash",
            rationale=(
                "the state root is locally recomputed from the complete state "
                "projection and differs only through the separately proven "
                "account-root closure"
            ),
            proof="state_root_recomputed_and_only_account_root_projection_differs",
        ),
    ]
)


ALLOWLIST_RECEIPT = {
    "schema": ALLOWLIST_SCHEMA,
    "normalization_mechanism": "exact_role_and_json_path_registry_only",
    "broad_recursive_key_deletion": False,
    "result_specific_exceptions": False,
    "entries": list(VOLATILITY_ALLOWLIST),
}
ALLOWLIST_RECEIPT["allowlist_root_sha256"] = canonical_sha256(ALLOWLIST_RECEIPT)


def _entry_for_path(role: str, path: tuple[str, ...]) -> Mapping[str, Any] | None:
    for entry in VOLATILITY_ALLOWLIST:
        if entry["role"] != role or len(entry["path"]) != len(path):
            continue
        if all(
            expected == "*" or expected == observed
            for expected, observed in zip(entry["path"], path)
        ):
            return entry
    return None


def _difference_paths(
    reference: Any,
    accelerated: Any,
    *,
    path: tuple[str, ...] = (),
) -> list[tuple[str, ...]]:
    if isinstance(reference, Mapping) and isinstance(accelerated, Mapping):
        result: list[tuple[str, ...]] = []
        for key in sorted(set(reference) | set(accelerated), key=str):
            if key not in reference or key not in accelerated:
                result.append((*path, str(key)))
            else:
                result.extend(
                    _difference_paths(
                        reference[key],
                        accelerated[key],
                        path=(*path, str(key)),
                    )
                )
        return result
    if isinstance(reference, list) and isinstance(accelerated, list):
        if len(reference) != len(accelerated):
            return [path]
        result = []
        for index, (left, right) in enumerate(zip(reference, accelerated)):
            result.extend(
                _difference_paths(left, right, path=(*path, str(index)))
            )
        return result
    return [] if canonical_bytes(reference) == canonical_bytes(accelerated) else [path]


def _path_value(value: Any, path: tuple[str, ...]) -> Any:
    current = value
    for key in path:
        if isinstance(current, Mapping):
            current = current[key]
        elif isinstance(current, list):
            current = current[int(key)]
        else:
            raise SemanticAcceptanceError("semantic_allowlist_path_invalid")
    return current


def _set_path(value: Any, path: tuple[str, ...], replacement: Any) -> None:
    current = value
    for key in path[:-1]:
        current = current[int(key)] if isinstance(current, list) else current[key]
    final = path[-1]
    if isinstance(current, list):
        current[int(final)] = replacement
    else:
        current[final] = replacement


def _validate_snapshot(snapshot: Any, *, role: str, row_index: int) -> None:
    if not isinstance(snapshot, Mapping):
        raise SemanticAcceptanceError(f"snapshot_missing:{role}:{row_index}")
    declared = snapshot.get("snapshot_hash_sha256")
    material = dict(snapshot)
    material.pop("snapshot_hash_sha256", None)
    if not _is_sha256(declared) or declared != producer_sha256(material):
        raise SemanticAcceptanceError(f"snapshot_hash_invalid:{role}:{row_index}")


def _validate_lifecycle(packet: Any, *, role: str, row_index: int) -> None:
    if packet is None:
        return
    if not isinstance(packet, Mapping):
        raise SemanticAcceptanceError(f"lifecycle_packet_invalid:{role}:{row_index}")
    if packet.get("schema_version") != "broker_order_lifecycle_capture_v4_packet_v1":
        raise SemanticAcceptanceError(f"lifecycle_packet_invalid:{role}:{row_index}")
    generated = packet.get("generated_at_utc")
    declared = packet.get("packet_hash_sha256")
    material = {
        key: value
        for key, value in packet.items()
        if key not in {"generated_at_utc", "packet_hash_sha256"}
    }
    if (
        not _is_utc_timestamp(generated)
        or not _is_sha256(declared)
        or declared != producer_sha256(material)
    ):
        raise SemanticAcceptanceError(f"lifecycle_hash_invalid:{role}:{row_index}")


def _validate_runtime_hash_preimages(
    role: str,
    row: Mapping[str, Any],
    *,
    row_index: int,
) -> None:
    if role not in {"order", "trade"}:
        return
    _validate_lifecycle(
        row.get("broker_order_lifecycle_capture_v4_packet"),
        role=role,
        row_index=row_index,
    )
    risk = row.get("risk_authority")
    if not isinstance(risk, Mapping):
        return
    headroom = risk.get("prop_firm_headroom")
    if isinstance(headroom, Mapping):
        simulated = headroom.get("simulated_headroom")
        evaluation = headroom.get("prop_firm_headroom_v4_evaluation")
        evaluation_snapshot = (
            evaluation.get("snapshot") if isinstance(evaluation, Mapping) else None
        )
        _validate_snapshot(simulated, role=role, row_index=row_index)
        _validate_snapshot(evaluation_snapshot, role=role, row_index=row_index)
        if canonical_bytes(simulated) != canonical_bytes(evaluation_snapshot):
            raise SemanticAcceptanceError(
                f"headroom_snapshot_alias_mismatch:{role}:{row_index}"
            )
    declared = risk.get("packet_hash_sha256")
    material = copy.deepcopy(dict(risk))
    material["packet_hash_sha256"] = ""
    if not _is_sha256(declared) or declared != producer_sha256(material):
        raise SemanticAcceptanceError(f"risk_packet_hash_invalid:{role}:{row_index}")
    alias = row.get("risk_authority_packet_hash_sha256")
    if alias is not None and alias != declared:
        raise SemanticAcceptanceError(f"risk_packet_alias_invalid:{role}:{row_index}")
    candidate_hash = row.get("candidate_packet_sidecar_hash_sha256")
    packet_hash = row.get("packet_sidecar_hash_sha256")
    if candidate_hash is not None and packet_hash is not None and candidate_hash != packet_hash:
        raise SemanticAcceptanceError(f"candidate_packet_alias_invalid:{role}:{row_index}")


class _ArrayRoot:
    def __init__(self) -> None:
        self._digest = hashlib.sha256()
        self._digest.update(b"[")
        self.count = 0

    def update(self, row: Mapping[str, Any]) -> None:
        if self.count:
            self._digest.update(b",")
        self._digest.update(canonical_bytes(row))
        self.count += 1

    def hexdigest(self) -> str:
        digest = self._digest.copy()
        digest.update(b"]")
        return digest.hexdigest()


def compare_role_rows(
    role: str,
    reference_rows: Iterable[Mapping[str, Any]],
    accelerated_rows: Iterable[Mapping[str, Any]],
    *,
    derived_hash_proofs: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Compare one ordered role stream with the exact volatility allowlist."""

    role = str(role)
    if role not in {*ROLE_SUFFIXES, "candidate"}:
        raise SemanticAcceptanceError(f"semantic_role_invalid:{role}")
    sentinel = object()
    projected = _ArrayRoot()
    raw_reference = _ArrayRoot()
    raw_accelerated = _ArrayRoot()
    observed: Counter[str] = Counter()
    observed_proof_classes: Counter[str] = Counter()
    mismatched_rows = 0
    excluded_count = 0
    for index, pair in enumerate(
        zip_longest(reference_rows, accelerated_rows, fillvalue=sentinel)
    ):
        reference, accelerated = pair
        if reference is sentinel or accelerated is sentinel:
            raise SemanticAcceptanceError(f"semantic_row_count_mismatch:{role}")
        if not isinstance(reference, Mapping) or not isinstance(accelerated, Mapping):
            raise SemanticAcceptanceError(f"semantic_row_not_mapping:{role}:{index}")
        _validate_runtime_hash_preimages(role, reference, row_index=index)
        _validate_runtime_hash_preimages(role, accelerated, row_index=index)
        raw_reference.update(reference)
        raw_accelerated.update(accelerated)
        differences = _difference_paths(reference, accelerated)
        if differences:
            mismatched_rows += 1
        if role in EXACT_ROLES and differences:
            raise SemanticAcceptanceError(f"semantic_row_mismatch:{role}:{index}")
        left = copy.deepcopy(dict(reference))
        right = copy.deepcopy(dict(accelerated))
        for path in differences:
            entry = _entry_for_path(role, path)
            if entry is None:
                raise SemanticAcceptanceError(
                    f"semantic_row_mismatch:{role}:{index}:{'/'.join(path)}"
                )
            left_value = _path_value(reference, path)
            right_value = _path_value(accelerated, path)
            if entry["value_class"] == "wall_clock_timestamp":
                if not _is_utc_timestamp(left_value) or not _is_utc_timestamp(
                    right_value
                ):
                    raise SemanticAcceptanceError(
                        f"volatile_timestamp_invalid:{role}:{index}"
                    )
                replacement = RUNTIME_SENTINEL
            else:
                if not _is_sha256(left_value) or not _is_sha256(right_value):
                    raise SemanticAcceptanceError(
                        f"derived_hash_invalid:{role}:{index}"
                    )
                pattern = "/".join(entry["path"])
                proof_class: Any = None
                if pattern in _LOCAL_PREIMAGE_DERIVED_PATTERNS:
                    proof_class = "PREIMAGE"
                elif (
                    pattern == "risk_authority_packet_hash_sha256"
                    and role in {"order", "trade"}
                    and isinstance(reference.get("risk_authority"), Mapping)
                    and isinstance(accelerated.get("risk_authority"), Mapping)
                ):
                    proof_class = "PREIMAGE"
                else:
                    proof_class = (derived_hash_proofs or {}).get(
                        f"{role}:{pattern}",
                        (derived_hash_proofs or {}).get(pattern),
                    )
                    if isinstance(proof_class, Mapping):
                        reference_identity = _identity_key(
                            reference,
                            label=f"{role}:reference:{index}",
                        )
                        accelerated_identity = _identity_key(
                            accelerated,
                            label=f"{role}:accelerated:{index}",
                        )
                        if reference_identity != accelerated_identity:
                            raise SemanticAcceptanceError(
                                f"derived_hash_identity_mismatch:{role}:{index}:{pattern}"
                            )
                        proof_class = proof_class.get(reference_identity)
                if proof_class not in {
                    "PREIMAGE",
                    "IDENTITY_ALIAS",
                    "HISTORICAL_HASH_ONLY_NONCAUSAL",
                    "TRANSITIVE_RUNTIME_ONLY_DERIVED_HASH",
                }:
                    raise SemanticAcceptanceError(
                        f"derived_hash_closure_unproven:{role}:{index}:{pattern}"
                    )
                observed_proof_classes[proof_class] += 1
                replacement = HASH_SENTINEL
            _set_path(left, path, replacement)
            _set_path(right, path, replacement)
            pattern = "/".join(entry["path"])
            observed[pattern] += 1
            excluded_count += 1
        if canonical_bytes(left) != canonical_bytes(right):
            raise SemanticAcceptanceError(f"semantic_projection_mismatch:{role}:{index}")
        projected.update(left)
    return {
        "role": role,
        "status": "SEMANTICALLY_EQUIVALENT",
        "row_count": projected.count,
        "ordered_semantic_projection_root_sha256": projected.hexdigest(),
        "reference_raw_root_sha256": raw_reference.hexdigest(),
        "accelerated_raw_root_sha256": raw_accelerated.hexdigest(),
        "raw_rows_with_volatile_differences": mismatched_rows,
        "excluded_volatile_difference_count": excluded_count,
        "observed_allowlisted_paths": dict(sorted(observed.items())),
        "observed_derived_hash_proof_classes": dict(
            sorted(observed_proof_classes.items())
        ),
        "meaningful_difference_count": 0,
        "unknown_difference_count": 0,
        "economic_values_exposed": False,
    }


def _identity_key(row: Mapping[str, Any], *, label: str) -> str:
    key = str(
        row.get("canonical_replay_candidate_instance_key")
        or row.get("risk_finalizer_probe_instance_key")
        or ""
    ).strip()
    candidate_id = str(row.get("candidate_id") or "").strip()
    decision_time = str(
        row.get("decision_time_utc")
        or row.get("candidate_instance_time_utc")
        or ""
    ).strip()
    if "@@" in key:
        key_candidate, key_time = key.rsplit("@@", 1)
        if not decision_time:
            decision_time = key_time
        if key_candidate != candidate_id or key_time != decision_time:
            raise SemanticAcceptanceError(
                f"hash_closure_identity_alias_mismatch:{label}"
            )
    if not key or not candidate_id or not decision_time:
        raise SemanticAcceptanceError(f"hash_closure_identity_invalid:{label}")
    return key


def _add_hash_owner(
    target: dict[str, str],
    *,
    key: str,
    value: Any,
    label: str,
) -> None:
    if not _is_sha256(value):
        raise SemanticAcceptanceError(f"hash_closure_value_invalid:{label}:{key}")
    previous = target.get(key)
    if previous is not None and previous != value:
        raise SemanticAcceptanceError(f"hash_closure_alias_conflict:{label}:{key}")
    target[key] = str(value)


def _scoped_role_rows(
    root: Path,
    role: str,
    *,
    end_day: str,
    exact_scope: bool,
) -> Iterable[Mapping[str, Any]]:
    rows = _role_rows(root, role)
    if exact_scope:
        return exact_scope_rows(
            rows,
            role=role,
            start_day="2026-01-01",
            end_day=end_day,
        )
    return rows_through(rows, end_day=end_day)


def _require_exact_selected_preimage_identities(
    observed: set[str],
    required: set[str],
) -> None:
    if observed != required or not required:
        raise SemanticAcceptanceError(
            "semantic_order_preimage_identity_partition_invalid"
        )


def _validate_selected_order_preimages(
    root: Path,
    *,
    end_day: str,
    exact_scope: bool,
    required: bool,
    required_candidate_keys: set[str],
) -> dict[str, Any]:
    path = _semantic_paths(root)["order_preimage"]
    if not path.is_file():
        if required:
            raise SemanticAcceptanceError("semantic_order_preimage_missing")
        return {
            "status": "HISTORICAL_PREIMAGE_UNAVAILABLE",
            "row_count": 0,
            "historical_selected_identity_count": len(required_candidate_keys),
            "historical_selected_identity_root_sha256": canonical_sha256(
                sorted(required_candidate_keys)
            ),
        }
    records = list(
        exact_scope_rows(
            iter_jsonl(path),
            role="semantic_order_preimage",
            start_day="2026-01-01",
            end_day=end_day,
        )
        if exact_scope
        else rows_through(iter_jsonl(path), end_day=end_day)
    )
    order_rows = list(
        _scoped_role_rows(
            root, "order", end_day=end_day, exact_scope=exact_scope
        )
    )
    indexes: set[int] = set()
    identities: set[str] = set()
    for record in records:
        sidecar_id = str(record.get("execution_packet_sidecar_id") or "").strip()
        canonical = record.get("sidecar_payload_canonical_json")
        owner = record.get("owner")
        index = record.get("persisted_order_stream_index")
        if (
            not sidecar_id
            or type(canonical) is not str
            or not isinstance(owner, Mapping)
            or type(index) is not int
            or index < 0
            or index >= len(order_rows)
            or index in indexes
        ):
            raise SemanticAcceptanceError("semantic_order_preimage_binding_invalid")
        try:
            payload = json.loads(canonical)
        except json.JSONDecodeError:
            raise SemanticAcceptanceError(
                "semantic_order_preimage_binding_invalid"
            ) from None
        if (
            not isinstance(payload, Mapping)
            or canonical_sha256(payload) != record.get("sidecar_payload_sha256")
            or producer_sha256(order_rows[index])
            != record.get("persisted_order_row_sha256")
        ):
            raise SemanticAcceptanceError("semantic_order_preimage_binding_invalid")
        execution = payload.get("execution_manager_packet")
        lifecycle = payload.get("broker_order_lifecycle_capture_v4_packet")
        persisted = order_rows[index]
        nested = (
            execution.get("broker_order_lifecycle_capture_v4")
            if isinstance(execution, Mapping)
            else None
        )
        nested_material = dict(nested) if isinstance(nested, Mapping) else {}
        nested_declared = nested_material.pop("packet_hash_sha256", None)
        nested_material.pop("generated_at_utc", None)
        lifecycle_material = dict(lifecycle) if isinstance(lifecycle, Mapping) else {}
        lifecycle_declared = lifecycle_material.pop("packet_hash_sha256", None)
        lifecycle_material.pop("generated_at_utc", None)
        pre_order = (
            lifecycle.get("pre_order_capture_contract")
            if isinstance(lifecycle, Mapping)
            else None
        )
        expected_owner = {
            key: persisted.get(key)
            for key in (
                "campaign",
                "profile",
                "decision_window_id",
                "canonical_replay_candidate_instance_key",
                "candidate_id",
                "simulated_order_id",
                "decision_time_utc",
            )
        }
        candidate_key = expected_owner[
            "canonical_replay_candidate_instance_key"
        ]
        if (
            set(payload)
            != {
                "execution_manager_packet",
                "broker_order_lifecycle_capture_v4_packet",
            }
            or not isinstance(execution, Mapping)
            or not isinstance(lifecycle, Mapping)
            or not isinstance(nested, Mapping)
            or execution.get("schema_version") != "execution_manager_v4_packet_v1"
            or execution.get("component") != "execution_manager_v4"
            or not _is_utc_timestamp(execution.get("generated_at_utc"))
            or nested.get("schema_version")
            != "broker_order_lifecycle_capture_v4_packet_v1"
            or nested.get("component") != "broker_order_lifecycle_capture_v4"
            or not _is_utc_timestamp(nested.get("generated_at_utc"))
            or nested_declared != producer_sha256(nested_material)
            or lifecycle_declared != producer_sha256(lifecycle_material)
            or canonical_bytes(lifecycle)
            != canonical_bytes(
                persisted.get("broker_order_lifecycle_capture_v4_packet")
            )
            or not isinstance(pre_order, Mapping)
            or pre_order.get("execution_manager_packet_hash")
            != producer_sha256(
                {
                    key: value
                    for key, value in execution.items()
                    if key not in {"generated_at_utc", "packet_hash_sha256"}
                }
            )
            or record.get("semantic_execution_manager_packet_sha256")
            != canonical_sha256(execution)
            or owner.get("payload_root_sha256")
            != record.get("sidecar_payload_sha256")
            or any(owner.get(key) != value for key, value in expected_owner.items())
            or persisted.get("execution_packet_sidecar_id") != sidecar_id
            or type(candidate_key) is not str
            or not candidate_key
            or candidate_key in identities
        ):
            raise SemanticAcceptanceError("semantic_order_preimage_binding_invalid")
        indexes.add(index)
        identities.add(candidate_key)
    if required or records:
        _require_exact_selected_preimage_identities(
            identities,
            required_candidate_keys,
        )
    return {
        "status": "COMPLETE_SELECTED_ORDER_PREIMAGES_RECOMPUTED",
        "row_count": len(records),
        "selected_identity_count": len(identities),
        "selected_identity_root_sha256": canonical_sha256(sorted(identities)),
        "persisted_order_indexes_root_sha256": canonical_sha256(sorted(indexes)),
        "payload_roots_sha256": canonical_sha256(
            sorted(record["sidecar_payload_sha256"] for record in records)
        ),
    }


def _historical_hash_noncausal_contract() -> dict[str, Any]:
    producer_path = ROOT / "src/research_infra/v4_timewarp_simulated_live_research_loop.py"
    headroom_path = ROOT / "src/components/prop_firm_headroom_v4.py"
    source = producer_path.read_text(encoding="utf-8")
    headroom_source = headroom_path.read_text(encoding="utf-8")
    if (
        file_sha256(producer_path) != EXPECTED_RUNTIME_PRODUCER_SHA256
        or file_sha256(headroom_path) != EXPECTED_PROP_HEADROOM_PRODUCER_SHA256
        or "packet_sidecar_omitted_compact_broad_replay_hash_only" not in source
        or '"payload_hash_sha256": stable_sha256(payload)' not in source
        or "compact_payload(\n                            packets," not in source
        or "captured_at_utc = (\n            str(decision_time_for_option)" not in source
        or "packet[\"packet_hash_sha256\"] = stable_sha256(packet)" not in source
        or 'reason="snapshot_not_broker_real"' not in headroom_source
    ):
        raise SemanticAcceptanceError("historical_hash_producer_contract_changed")
    tree = ast.parse(source, filename=str(producer_path))
    parent: dict[ast.AST, ast.AST] = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parent[child] = node
    consumer_counts = {
        "packet_sidecar_hash_sha256": 0,
        "payload_hash_sha256": 0,
        "risk_authority_packet_hash_sha256": 0,
    }
    occurrence_counts = Counter()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or node.value not in consumer_counts:
            continue
        field = str(node.value)
        occurrence_counts[field] += 1
        current: ast.AST | None = node
        while current is not None:
            owner = parent.get(current)
            if isinstance(owner, ast.Compare):
                consumer_counts[field] += 1
                break
            if isinstance(owner, (ast.If, ast.While, ast.IfExp)) and getattr(
                owner, "test", None
            ) is current:
                consumer_counts[field] += 1
                break
            current = owner
    if consumer_counts["packet_sidecar_hash_sha256"] != 0:
        raise SemanticAcceptanceError("candidate_packet_hash_has_decision_consumer")
    if consumer_counts["risk_authority_packet_hash_sha256"] != 0:
        raise SemanticAcceptanceError("flattened_risk_hash_has_decision_consumer")
    # Other payload_hash fields are authoritative signed-payload controls.  The
    # historical exception is only the compact finalizer producer named above,
    # so its exact source marker is bound separately instead of treating the
    # generic key as globally noncausal.
    return {
        "status": "HISTORICAL_HASH_ONLY_NONCAUSAL_PRODUCER_BOUND",
        "producer_path": str(producer_path.relative_to(ROOT)),
        "producer_sha256": file_sha256(producer_path),
        "prop_headroom_producer_path": str(headroom_path.relative_to(ROOT)),
        "prop_headroom_producer_sha256": file_sha256(headroom_path),
        "simulated_capture_clock_source": "causal_decision_time",
        "broker_real_freshness_or_authority_consumed": False,
        "candidate_packet_hash_decision_consumer_count": 0,
        "flattened_risk_hash_decision_consumer_count": 0,
        "candidate_packet_hash_ast_occurrence_count": occurrence_counts[
            "packet_sidecar_hash_sha256"
        ],
        "candidate_packet_preimage_persistence_status": (
            "historical_compact_stack_omitted_hash_only"
        ),
        "finalizer_payload_preimage_persistence_status": (
            "historical_full_payload_truncated_after_hash"
        ),
    }


def _collect_hash_alias_state(
    root: Path,
    *,
    end_day: str,
    exact_scope: bool,
    require_preimages: bool,
) -> dict[str, Any]:
    packet: dict[str, dict[str, str]] = {
        role: {} for role in ("missed", "order", "trade", "oracle")
    }
    risk: dict[str, dict[str, str]] = {
        role: {} for role in ("missed", "order", "trade", "oracle")
    }
    probe: dict[str, str] = {}
    probe_projection_roots: dict[str, str] = {}
    selected_probe: dict[str, str] = {}
    primary_probe: dict[str, str] = {}
    order_probe: dict[str, str] = {}
    missed_meta: dict[str, dict[str, Any]] = {}
    evaluated_missed_keys: set[str] = set()
    probe_caps_by_window: dict[str, dict[str, int]] = {}
    finalizer_payload_hash_count = 0
    scorecard_count = 0
    for role in packet:
        for row in _scoped_role_rows(
            root, role, end_day=end_day, exact_scope=exact_scope
        ):
            key = _identity_key(row, label=role)
            packet_hash = row.get(
                "candidate_packet_sidecar_hash_sha256",
                row.get("packet_sidecar_hash_sha256"),
            )
            if packet_hash is None:
                packet_hash = row.get("packet_sidecar_hash_sha256")
            _add_hash_owner(
                packet[role], key=key, value=packet_hash, label=f"{role}:packet"
            )
            risk_hash = row.get("risk_authority_packet_hash_sha256")
            if risk_hash is not None:
                _add_hash_owner(
                    risk[role], key=key, value=risk_hash, label=f"{role}:risk"
                )
            if role == "missed":
                semantic_row = copy.deepcopy(dict(row))
                for volatile_hash_field in (
                    "packet_sidecar_hash_sha256",
                    "risk_authority_packet_hash_sha256",
                ):
                    if volatile_hash_field in semantic_row:
                        semantic_row[volatile_hash_field] = HASH_SENTINEL
                missed_meta[key] = {
                    "trading_day": row.get("trading_day"),
                    "decision_window_id": row.get("decision_window_id"),
                    "risk_finalizer_rank": row.get("risk_finalizer_rank"),
                    "risk_authority": row.get("risk_authority"),
                    "risk_authority_status": row.get("risk_authority_status"),
                    "row_projection_root_sha256": canonical_sha256(semantic_row),
                }
                if row.get("risk_decision") != "risk_probe_materialized":
                    evaluated_missed_keys.add(key)
            if role == "order":
                nested = row.get("risk_authority")
                nested = nested if isinstance(nested, Mapping) else {}
                probe_hash = nested.get("risk_finalizer_probe_packet_hash_sha256")
                if probe_hash is not None:
                    _add_hash_owner(
                        order_probe,
                        key=key,
                        value=probe_hash,
                        label="order:probe",
                    )
    for row in _scoped_role_rows(
        root, "scorecard", end_day=end_day, exact_scope=exact_scope
    ):
        scorecard_count += 1
        finalizer = row.get("risk_admitted_scheduler_finalizer")
        if not isinstance(finalizer, Mapping):
            continue
        decision_window_id = row.get("decision_window_id")
        preserved_count = finalizer.get("probe_rows_preserved_count")
        total_count = finalizer.get("probe_rows_total_count")
        if (
            type(decision_window_id) is str
            and type(preserved_count) is int
            and type(total_count) is int
        ):
            cap = {
                "preserved_count": preserved_count,
                "total_count": total_count,
            }
            previous_cap = probe_caps_by_window.get(decision_window_id)
            if previous_cap is not None and previous_cap != cap:
                raise SemanticAcceptanceError(
                    f"finalizer_probe_cap_conflict:{decision_window_id}"
                )
            probe_caps_by_window[decision_window_id] = cap
        payload_hash = finalizer.get("payload_hash_sha256")
        if payload_hash is not None:
            if (
                not _is_sha256(payload_hash)
                or finalizer.get("payload_compacted_for_broad_replay") is not True
                or type(finalizer.get("probe_rows_preserved_count")) is not int
                or type(finalizer.get("probe_rows_total_count")) is not int
                or finalizer.get("probe_rows_preserved_count", -1) < 0
                or finalizer.get("probe_rows_total_count", -1)
                < finalizer.get("probe_rows_preserved_count", 0)
            ):
                raise SemanticAcceptanceError("finalizer_compact_hash_closure_invalid")
            finalizer_payload_hash_count += 1
        for field, target in (
            ("probe_rows", probe),
            ("selected_probe_rows", selected_probe),
        ):
            rows = finalizer.get(field) or []
            if not isinstance(rows, list):
                raise SemanticAcceptanceError("finalizer_probe_inventory_invalid")
            local: set[str] = set()
            for probe_row in rows:
                if not isinstance(probe_row, Mapping):
                    raise SemanticAcceptanceError("finalizer_probe_inventory_invalid")
                key = _identity_key(probe_row, label=f"scorecard:{field}")
                if key in local:
                    raise SemanticAcceptanceError(
                        f"finalizer_probe_identity_duplicate:{field}:{key}"
                    )
                local.add(key)
                _add_hash_owner(
                    target,
                    key=key,
                    value=probe_row.get("risk_authority_packet_hash_sha256"),
                    label=f"scorecard:{field}",
                )
                if field == "probe_rows":
                    probe_projection = copy.deepcopy(dict(probe_row))
                    probe_projection["risk_authority_packet_hash_sha256"] = (
                        HASH_SENTINEL
                    )
                    projection_root = canonical_sha256(probe_projection)
                    previous_projection = probe_projection_roots.get(key)
                    if (
                        previous_projection is not None
                        and previous_projection != projection_root
                    ):
                        raise SemanticAcceptanceError(
                            f"finalizer_probe_projection_conflict:{key}"
                        )
                    probe_projection_roots[key] = projection_root
        primary_hash = row.get(
            "finalizer_primary_probe_risk_authority_packet_hash_sha256"
        )
        if primary_hash is not None:
            key = _identity_key(
                {
                    "canonical_replay_candidate_instance_key": row.get(
                        "finalizer_primary_probe_canonical_replay_candidate_instance_key"
                    ),
                    "candidate_id": row.get("finalizer_primary_probe_candidate_id"),
                    "decision_time_utc": row.get(
                        "finalizer_primary_probe_decision_time_utc"
                    ),
                },
                label="scorecard:primary_probe",
            )
            _add_hash_owner(
                primary_probe,
                key=key,
                value=primary_hash,
                label="scorecard:primary_probe",
            )
    for key, value in selected_probe.items():
        if probe.get(key) != value:
            raise SemanticAcceptanceError(
                f"selected_probe_hash_alias_mismatch:{key}"
            )
    for key, value in primary_probe.items():
        terminal_value = risk["missed"].get(key) or risk["order"].get(key)
        if probe.get(key) != value and terminal_value != value:
            raise SemanticAcceptanceError(f"primary_probe_hash_alias_mismatch:{key}")
    for key, value in order_probe.items():
        if probe.get(key) != value:
            raise SemanticAcceptanceError(f"order_probe_hash_alias_mismatch:{key}")
    selected_keys = set(packet["order"])
    if (
        set(packet["trade"]) != selected_keys
        or set(packet["oracle"]) != selected_keys
        or selected_keys & set(packet["missed"])
    ):
        raise SemanticAcceptanceError("candidate_terminal_partition_invalid")
    for key in selected_keys:
        if not (
            packet["order"][key]
            == packet["trade"][key]
            == packet["oracle"][key]
        ):
            raise SemanticAcceptanceError(f"candidate_packet_alias_mismatch:{key}")
        if not (
            risk["order"].get(key)
            == risk["trade"].get(key)
            == risk["oracle"].get(key)
        ):
            raise SemanticAcceptanceError(f"selected_risk_alias_mismatch:{key}")
    preimages = _validate_selected_order_preimages(
        root,
        end_day=end_day,
        exact_scope=exact_scope,
        required=require_preimages,
        required_candidate_keys=selected_keys,
    )
    return {
        "packet": packet,
        "risk": risk,
        "probe": probe,
        "probe_projection_roots": probe_projection_roots,
        "selected_probe": selected_probe,
        "primary_probe": primary_probe,
        "order_probe": order_probe,
        "missed_meta": missed_meta,
        "evaluated_missed_keys": evaluated_missed_keys,
        "probe_caps_by_window": probe_caps_by_window,
        "candidate_terminal_identity_count": len(packet["missed"]) + len(selected_keys),
        "missed_identity_count": len(packet["missed"]),
        "selected_identity_count": len(selected_keys),
        "scorecard_count": scorecard_count,
        "finalizer_payload_hash_count": finalizer_payload_hash_count,
        "selected_order_preimages": preimages,
    }


def validate_campaign_hash_closure(
    reference_root: Path,
    accelerated_root: Path,
    *,
    end_day: str,
    accelerated_exact_scope: bool,
    reference_preimages_required: bool,
) -> dict[str, Any]:
    historical = _historical_hash_noncausal_contract()
    reference = _collect_hash_alias_state(
        reference_root,
        end_day=end_day,
        exact_scope=False,
        require_preimages=reference_preimages_required,
    )
    accelerated = _collect_hash_alias_state(
        accelerated_root,
        end_day=end_day,
        exact_scope=accelerated_exact_scope,
        require_preimages=True,
    )
    for side, state in (("reference", reference), ("accelerated", accelerated)):
        if state["candidate_terminal_identity_count"] <= 0:
            raise SemanticAcceptanceError(
                f"candidate_terminal_partition_empty:{side}"
            )
    if (
        reference["candidate_terminal_identity_count"]
        != accelerated["candidate_terminal_identity_count"]
        or reference["missed_identity_count"] != accelerated["missed_identity_count"]
        or reference["selected_identity_count"]
        != accelerated["selected_identity_count"]
    ):
        raise SemanticAcceptanceError("candidate_terminal_partition_count_mismatch")
    for role in reference["packet"]:
        if set(reference["packet"][role]) != set(accelerated["packet"][role]):
            raise SemanticAcceptanceError(
                f"candidate_terminal_identity_set_mismatch:{role}"
            )
    if set(reference["probe"]) != set(accelerated["probe"]):
        raise SemanticAcceptanceError("finalizer_probe_identity_set_mismatch")
    changed_missed_risk = {
        key
        for key, value in reference["risk"]["missed"].items()
        if accelerated["risk"]["missed"].get(key) != value
    }
    if (
        changed_missed_risk != reference["evaluated_missed_keys"]
        or changed_missed_risk != accelerated["evaluated_missed_keys"]
    ):
        raise SemanticAcceptanceError("missed_risk_evaluated_partition_mismatch")
    changed_missed_risk_aliases: set[str] = set()
    changed_missed_risk_cohort: set[str] = set()
    for key in changed_missed_risk:
        reference_meta = reference["missed_meta"].get(key)
        accelerated_meta = accelerated["missed_meta"].get(key)
        if not isinstance(reference_meta, Mapping) or reference_meta != accelerated_meta:
            raise SemanticAcceptanceError(
                f"missed_risk_row_projection_mismatch:{key}"
            )
        if (
            reference["probe"].get(key)
            == reference["risk"]["missed"].get(key)
            and accelerated["probe"].get(key)
            == accelerated["risk"]["missed"].get(key)
        ):
            if (
                reference["probe_projection_roots"].get(key)
                != accelerated["probe_projection_roots"].get(key)
            ):
                raise SemanticAcceptanceError(
                    f"missed_risk_probe_projection_mismatch:{key}"
                )
            changed_missed_risk_aliases.add(key)
            continue
        if key in reference["probe"] or key in accelerated["probe"]:
            raise SemanticAcceptanceError(f"missed_risk_probe_alias_mismatch:{key}")
        if (
            reference_meta.get("risk_authority")
            != "timewarp_v4_runtime_risk_authority_v1"
            or reference_meta.get("risk_authority_status")
            != "pre_scheduler_risk_authority_materialized"
        ):
            raise SemanticAcceptanceError(
                f"missed_risk_omitted_probe_semantics_mismatch:{key}"
            )
        decision_window_id = reference_meta.get("decision_window_id")
        rank = reference_meta.get("risk_finalizer_rank")
        reference_cap = reference["probe_caps_by_window"].get(decision_window_id)
        accelerated_cap = accelerated["probe_caps_by_window"].get(
            decision_window_id
        )
        if (
            type(decision_window_id) is not str
            or type(rank) is not int
            or not isinstance(reference_cap, Mapping)
            or reference_cap != accelerated_cap
            or type(reference_cap.get("preserved_count")) is not int
            or type(reference_cap.get("total_count")) is not int
            or rank <= reference_cap["preserved_count"]
            or rank > reference_cap["total_count"]
        ):
            raise SemanticAcceptanceError(
                f"missed_risk_probe_omission_not_deterministic:{key}"
            )
        changed_missed_risk_cohort.add(key)
    alias_days = {
        reference["missed_meta"][key]["trading_day"]
        for key in changed_missed_risk_aliases
    }
    if any(
        reference["missed_meta"][key]["trading_day"] not in alias_days
        for key in changed_missed_risk_cohort
    ):
        raise SemanticAcceptanceError("missed_risk_runtime_cohort_witness_missing")
    proof_classes = dict(_CAMPAIGN_DERIVED_HASH_PROOF_CLASSES)
    selected_preimage_identities = set(reference["packet"]["order"])
    proof_classes[
        "broker_order_lifecycle_capture_v4_packet/"
        "pre_order_capture_contract/execution_manager_packet_hash"
    ] = {
        key: "PREIMAGE" for key in selected_preimage_identities
    }
    proof_classes["missed:risk_authority_packet_hash_sha256"] = {
        key: "TRANSITIVE_RUNTIME_ONLY_DERIVED_HASH"
        for key in changed_missed_risk
    }
    evaluated_identity_root = canonical_sha256(sorted(changed_missed_risk))
    normalized_missed_rows_root = canonical_sha256(
        [
            [key, reference["missed_meta"][key]["row_projection_root_sha256"]]
            for key in sorted(changed_missed_risk)
        ]
    )
    covered_probe_identity_root = canonical_sha256(
        sorted(changed_missed_risk_aliases)
    )
    normalized_probe_rows_root = canonical_sha256(
        [
            [key, reference["probe_projection_roots"][key]]
            for key in sorted(changed_missed_risk_aliases)
        ]
    )
    return {
        "status": "ALL_DERIVED_HASH_FAMILIES_CLASSIFIED_AND_VALIDATED",
        "proof_classes": proof_classes,
        "historical_hash_only_noncausal_contract": historical,
        "reference": {
            key: value
            for key, value in reference.items()
            if key
            not in {
                "packet",
                "risk",
                "probe",
                "probe_projection_roots",
                "selected_probe",
                "primary_probe",
                "order_probe",
                "missed_meta",
                "evaluated_missed_keys",
                "probe_caps_by_window",
            }
        },
        "accelerated": {
            key: value
            for key, value in accelerated.items()
            if key
            not in {
                "packet",
                "risk",
                "probe",
                "probe_projection_roots",
                "selected_probe",
                "primary_probe",
                "order_probe",
                "missed_meta",
                "evaluated_missed_keys",
                "probe_caps_by_window",
            }
        },
        "changed_missed_risk_identity_count": len(changed_missed_risk),
        "changed_missed_risk_probe_alias_count": len(
            changed_missed_risk_aliases
        ),
        "changed_missed_risk_deterministically_omitted_probe_count": len(
            changed_missed_risk_cohort
        ),
        "evaluated_probe_identity_root_sha256": evaluated_identity_root,
        "normalized_missed_rows_root_sha256": normalized_missed_rows_root,
        "covered_probe_identity_root_sha256": covered_probe_identity_root,
        "normalized_probe_rows_root_sha256": normalized_probe_rows_root,
        "deterministically_omitted_probe_identities": sorted(
            changed_missed_risk_cohort
        ),
        "closure_root_sha256": canonical_sha256(
            {
                "proof_classes": proof_classes,
                "historical": historical,
                "reference_terminal_count": reference[
                    "candidate_terminal_identity_count"
                ],
                "accelerated_terminal_count": accelerated[
                    "candidate_terminal_identity_count"
                ],
                "changed_missed_risk_identity_count": len(changed_missed_risk),
                "changed_missed_risk_probe_alias_count": len(
                    changed_missed_risk_aliases
                ),
                "changed_missed_risk_deterministically_omitted_probe_count": len(
                    changed_missed_risk_cohort
                ),
                "evaluated_probe_identity_root_sha256": evaluated_identity_root,
                "normalized_missed_rows_root_sha256": normalized_missed_rows_root,
                "covered_probe_identity_root_sha256": covered_probe_identity_root,
                "normalized_probe_rows_root_sha256": normalized_probe_rows_root,
            }
        ),
    }


def _progress_through(value: Any, end_day: str) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        raise SemanticAcceptanceError("summary_progress_invalid")
    result = []
    for row in value:
        if not isinstance(row, Mapping) or type(row.get("end_day")) is not str:
            raise SemanticAcceptanceError("summary_progress_invalid")
        if row["end_day"] <= end_day:
            result.append(row)
    return result


def _exact_progress_rows(
    value: Any,
    *,
    start_day: str,
    end_day: str,
) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        raise SemanticAcceptanceError("summary_progress_invalid")
    rows: list[Mapping[str, Any]] = []
    for index, row in enumerate(value):
        if not isinstance(row, Mapping):
            raise SemanticAcceptanceError("summary_progress_invalid")
        row_start = row.get("start_day")
        row_end = row.get("end_day")
        if (
            type(row_start) is not str
            or type(row_end) is not str
            or row_start != row_end
            or row_start < start_day
            or row_end > end_day
        ):
            raise SemanticAcceptanceError(
                f"summary_progress_outside_exact_scope:{index}"
            )
        rows.append(row)
    expected = [
        (date.fromisoformat(start_day) + timedelta(days=offset)).isoformat()
        for offset in range((date.fromisoformat(end_day) - date.fromisoformat(start_day)).days + 1)
    ]
    if [row.get("end_day") for row in rows] != expected:
        raise SemanticAcceptanceError("summary_progress_exact_scope_incomplete")
    return rows


def _leaf_paths(value: Any, *, path: tuple[str, ...]) -> list[tuple[str, ...]]:
    if isinstance(value, Mapping):
        if not value:
            return [path]
        result: list[tuple[str, ...]] = []
        for key in sorted(value, key=str):
            result.extend(_leaf_paths(value[key], path=(*path, str(key))))
        return result
    if isinstance(value, list):
        if not value:
            return [path]
        result = []
        for index, item in enumerate(value):
            result.extend(_leaf_paths(item, path=(*path, str(index))))
        return result
    return [path]


def _expanded_difference_paths(
    reference: Any,
    accelerated: Any,
    *,
    path: tuple[str, ...] = (),
) -> list[tuple[str, ...]]:
    if isinstance(reference, Mapping) and isinstance(accelerated, Mapping):
        result: list[tuple[str, ...]] = []
        for key in sorted(set(reference) | set(accelerated), key=str):
            next_path = (*path, str(key))
            if key not in reference:
                result.extend(_leaf_paths(accelerated[key], path=next_path))
            elif key not in accelerated:
                result.extend(_leaf_paths(reference[key], path=next_path))
            else:
                result.extend(
                    _expanded_difference_paths(
                        reference[key], accelerated[key], path=next_path
                    )
                )
        return result
    if isinstance(reference, list) and isinstance(accelerated, list):
        result = []
        for index in range(max(len(reference), len(accelerated))):
            next_path = (*path, str(index))
            if index >= len(reference):
                result.extend(_leaf_paths(accelerated[index], path=next_path))
            elif index >= len(accelerated):
                result.extend(_leaf_paths(reference[index], path=next_path))
            else:
                result.extend(
                    _expanded_difference_paths(
                        reference[index], accelerated[index], path=next_path
                    )
                )
        return result
    if isinstance(reference, (Mapping, list)):
        return _leaf_paths(reference, path=path)
    if isinstance(accelerated, (Mapping, list)):
        return _leaf_paths(accelerated, path=path)
    return [] if canonical_bytes(reference) == canonical_bytes(accelerated) else [path]


def _validate_shared_contract(
    shared: Any,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    if shared is None:
        return None, {
            "shared_contract_root_sha256": _NULL_ROOT_SHA256,
            "shared_causal_projection_root_sha256": _NULL_ROOT_SHA256,
        }
    if not isinstance(shared, Mapping) or set(shared) != _SHARED_CONTRACT_FIELDS:
        raise SemanticAcceptanceError("summary_shared_contract_schema_invalid")
    broker = shared.get("broker_live_final_authority")
    code_authority = shared.get("code_authority")
    config_semantics = shared.get("effective_profile_config_hash_semantics")
    config_hashes = shared.get("effective_profile_config_hashes")
    options = shared.get("execution_options")
    if (
        shared.get("valid") is not True
        or not _is_sha256(shared.get("shared_execution_contract_digest_sha256"))
        or not isinstance(broker, Mapping)
        or broker.get("broker_mutation_enabled") is not False
        or broker.get("live_broker_authority") is not False
        or broker.get("final_selection_claim") is not False
        or not isinstance(code_authority, list)
        or not code_authority
        or any(
            not isinstance(row, Mapping)
            or set(row) != {"path", "sha256"}
            or type(row.get("path")) is not str
            or not row.get("path")
            or not _is_sha256(row.get("sha256"))
            for row in code_authority
        )
        or len({row["path"] for row in code_authority}) != len(code_authority)
        or canonical_sha256(code_authority) not in _ALLOWED_CODE_AUTHORITY_ROOTS
        or not isinstance(config_semantics, Mapping)
        or set(config_semantics) != _SHARED_CONFIG_SEMANTICS_FIELDS
        or config_semantics.get("projection")
        != "execution_semantic_config_excludes_diagnostic_provenance"
        or config_semantics.get("raw_artifact_sha256_retained_in_runtime_and_ledgers")
        is not True
        or not isinstance(config_semantics.get("excluded_runtime_fields"), list)
        or len(config_semantics["excluded_runtime_fields"])
        != len(set(config_semantics["excluded_runtime_fields"]))
        or frozenset(config_semantics["excluded_runtime_fields"])
        not in {_LEGACY_CONFIG_RUNTIME_FIELDS, _CURRENT_CONFIG_RUNTIME_FIELDS}
        or not isinstance(config_hashes, Mapping)
        or set(config_hashes) != {"repaired_package_conversion_v3"}
        or not _is_sha256(config_hashes.get("repaired_package_conversion_v3"))
        or canonical_sha256(config_hashes) not in _ALLOWED_EFFECTIVE_CONFIG_HASH_ROOTS
        or not isinstance(options, Mapping)
        or frozenset(options) not in _ALLOWED_EXECUTION_OPTION_KEYSETS
    ):
        raise SemanticAcceptanceError("summary_shared_contract_schema_invalid")
    acceleration_options = {
        key: options[key]
        for key in sorted(_ACCELERATION_EXECUTION_OPTION_FIELDS)
        if key in options
    }
    if canonical_sha256(acceleration_options) not in _ALLOWED_ACCELERATION_OPTION_ROOTS:
        raise SemanticAcceptanceError("summary_shared_contract_acceleration_options_invalid")

    causal = copy.deepcopy(dict(shared))
    causal.pop("code_authority")
    causal.pop("effective_profile_config_hashes")
    causal.pop("shared_execution_contract_digest_sha256")
    causal["effective_profile_config_hash_semantics"].pop(
        "excluded_runtime_fields"
    )
    for key in _ACCELERATION_EXECUTION_OPTION_FIELDS:
        causal["execution_options"].pop(key, None)
    causal_root = canonical_sha256(causal)
    return causal, {
        "shared_contract_root_sha256": canonical_sha256(shared),
        "shared_causal_projection_root_sha256": causal_root,
        "code_authority_root_sha256": canonical_sha256(code_authority),
        "effective_config_hash_root_sha256": canonical_sha256(config_hashes),
        "acceleration_option_root_sha256": canonical_sha256(acceleration_options),
    }


def _validate_summary_proof_object(field: str, value: Any) -> str:
    root = canonical_sha256(value)
    if root not in _ALLOWED_SUMMARY_PROOF_OBJECT_ROOTS[field]:
        raise SemanticAcceptanceError(f"summary_{field}_root_invalid")
    if field == "attempt5_execution_identity" and value is not None:
        if (
            not isinstance(value, Mapping)
            or value.get("arm_id") != "S0R0"
            or value.get("expected_arm_fingerprint_sha256")
            != EXPECTED_ARM_FINGERPRINT
            or value.get("expected_source_plan_digest_sha256")
            != EXPECTED_SOURCE_PLAN_DIGEST
            or value.get("broker_live_authority") is not False
            or value.get("broker_mutation_enabled") is not False
            or value.get("policy_execution_entered") is not False
            or value.get("other_arms_launched") is not False
        ):
            raise SemanticAcceptanceError("summary_attempt5_execution_identity_invalid")
    elif field == "runtime_evidence_contract" and value is not None:
        if (
            not isinstance(value, Mapping)
            or not _is_sha256(value.get("contract_root_sha256"))
            or value.get("legacy_evidence_mutation_enabled") is not False
            or value.get("read_only_existing_evidence") is not True
        ):
            raise SemanticAcceptanceError("summary_runtime_authority_invalid")
    elif field == "source_acceleration_authority" and value is not None:
        if (
            not isinstance(value, Mapping)
            or value.get("source_plan_digest_sha256")
            != EXPECTED_SOURCE_PLAN_DIGEST
            or value.get("symbol_count") != 24
            or value.get("policy_execution_entered") is not False
            or value.get("candidate_cache_enabled") is not False
        ):
            raise SemanticAcceptanceError("summary_source_authority_invalid")
    elif field == "task2_semantic_checkpoint" and value is not None:
        projection = dict(value) if isinstance(value, Mapping) else {}
        declared = projection.pop("checkpoint_root_sha256", None)
        if (
            not isinstance(value, Mapping)
            or value.get("start_day") != "2026-01-01"
            or value.get("end_day") != "2026-01-02"
            or value.get("completed_day_count") != 2
            or value.get("canonical_source_plan_digest_sha256")
            != EXPECTED_SOURCE_PLAN_DIGEST
            or value.get("acceptance_authorized") is not False
            or value.get("broker_live_authority") is not False
            or value.get("broker_mutation_enabled") is not False
            or declared != canonical_sha256(projection)
        ):
            raise SemanticAcceptanceError("summary_task2_checkpoint_invalid")
    return root


def _validate_summary_authority(
    summary: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    arm = summary.get("b7_5_selection_sizing_factorial_arm_binding")
    if arm is not None:
        if (
            not isinstance(arm, Mapping)
            or arm.get("arm_id") != "S0R0"
            or arm.get("arm_fingerprint_sha256") != EXPECTED_ARM_FINGERPRINT
            or arm.get("broker_mutation_enabled") is not False
            or arm.get("live_broker_authority") is not False
            or arm.get("uses_outcome_fields") is not False
            or arm.get("valid") is not True
            or (
                summary.get("shared_execution_contract") is not None
                and canonical_sha256(arm) != _EXPECTED_ARM_BINDING_ROOT_SHA256
            )
        ):
            raise SemanticAcceptanceError("summary_arm_authority_invalid")
    binding = summary.get("b7_5_contract_binding")
    binding_causal: dict[str, Any] | None = None
    if binding is not None:
        if (
            not isinstance(binding, Mapping)
            or set(binding) != _B7_CONTRACT_BINDING_FIELDS
            or binding.get("required") is not True
            or binding.get("valid") is not True
            or binding.get("expected_source_plan_digest_sha256")
            != EXPECTED_SOURCE_PLAN_DIGEST
            or binding.get("actual_source_plan_digests_sha256")
            != [EXPECTED_SOURCE_PLAN_DIGEST]
            or canonical_bytes(binding.get("selection_sizing_factorial_arm_binding"))
            != canonical_bytes(arm)
            or binding.get("actual_shared_execution_contract_digest_sha256")
            != binding.get("expected_shared_execution_contract_digest_sha256")
        ):
            raise SemanticAcceptanceError("summary_contract_authority_invalid")
        binding_causal = copy.deepcopy(dict(binding))
        binding_causal.pop("actual_shared_execution_contract_digest_sha256")
        binding_causal.pop("expected_shared_execution_contract_digest_sha256")

    shared_causal, shared_validation = _validate_shared_contract(
        summary.get("shared_execution_contract")
    )
    proof_roots = {
        field: _validate_summary_proof_object(field, summary.get(field))
        for field in sorted(
            _SUMMARY_AUTHORITY_FIELDS
            - {"b7_5_contract_binding", "shared_execution_contract"}
        )
    }
    validation = {
        "arm_root_sha256": canonical_sha256(arm),
        "binding_root_sha256": canonical_sha256(binding),
        "binding_causal_projection_root_sha256": canonical_sha256(
            binding_causal
        ),
        **shared_validation,
        "proof_object_roots_sha256": proof_roots,
    }
    causal = {
        "b7_5_contract_binding": binding_causal,
        "shared_execution_contract": shared_causal,
    }
    return validation, causal


def _authority_difference_rationale(path: tuple[str, ...]) -> dict[str, str]:
    field = path[0]
    remainder = path[1:]
    if field == "b7_5_contract_binding" and remainder and remainder[0] in {
        "actual_shared_execution_contract_digest_sha256",
        "expected_shared_execution_contract_digest_sha256",
    }:
        return {
            "rationale": "derived_digest_of_schema_exhaustive_shared_contract",
            "proof": "causal_binding_projection_exact_and_expected_root_bound",
        }
    if field == "shared_execution_contract" and remainder:
        if remainder[0] == "code_authority":
            return {
                "rationale": "code_provenance_only",
                "proof": "exact_item_schema_and_authenticated_whole_object_root",
            }
        if remainder[0] == "effective_profile_config_hashes":
            return {
                "rationale": "hash_derived_from_explicit_diagnostic_provenance_exclusions",
                "proof": "causal_shared_contract_projection_exact_and_config_hash_root_bound",
            }
        if remainder[:2] == (
            "effective_profile_config_hash_semantics",
            "excluded_runtime_fields",
        ):
            return {
                "rationale": "explicit_noncausal_config_provenance_field_registry",
                "proof": "finite_exact_allowed_field_sets_and_causal_projection_exact",
            }
        if remainder[0] == "shared_execution_contract_digest_sha256":
            return {
                "rationale": "derived_digest_of_complete_contract_including_noncausal_provenance",
                "proof": "causal_shared_contract_projection_exact_and_expected_root_bound",
            }
        if (
            len(remainder) >= 2
            and remainder[0] == "execution_options"
            and remainder[1] in _ACCELERATION_EXECUTION_OPTION_FIELDS
        ):
            return {
                "rationale": "replay_only_acceleration_or_proof_transport_option",
                "proof": "finite_option_keyset_authenticated_option_root_and_exact_economic_ledgers",
            }
        raise SemanticAcceptanceError(
            "summary_authority_unallowlisted_difference:" + "/".join(path)
        )
    proof_rationales = {
        "attempt5_execution_identity": "replay_only_execution_and_proof_identity",
        "real_s0r0_parity_gate": "replay_only_independent_parity_proof_transport",
        "runtime_evidence_contract": "read_only_input_provenance_envelope",
        "source_acceleration_authority": "source_equivalent_replay_only_acceleration_provenance",
        "streaming_capacity_checks": "host_capacity_measurement_envelope",
        "streaming_proof_archive": "lossless_proof_transport_envelope",
        "streaming_proof_archive_shards": "lossless_proof_transport_shard_inventory",
        "task2_semantic_checkpoint": "bounded_non_authorizing_checkpoint_envelope",
    }
    if field in proof_rationales:
        return {
            "rationale": proof_rationales[field],
            "proof": "authenticated_whole_object_root_plus_exact_causal_role_and_state_comparison",
        }
    raise SemanticAcceptanceError(
        "summary_authority_unallowlisted_difference:" + "/".join(path)
    )


def compare_summary_semantics(
    reference: Mapping[str, Any],
    accelerated: Mapping[str, Any],
    *,
    end_day: str | None = None,
) -> dict[str, Any]:
    observed = set(reference) | set(accelerated)
    unknown = sorted(observed - set(SUMMARY_FIELD_POLICIES))
    if unknown:
        raise SemanticAcceptanceError("summary_field_unknown:" + ",".join(unknown))
    left = {field: reference.get(field) for field in sorted(_SUMMARY_EXACT_FIELDS)}
    right = {field: accelerated.get(field) for field in sorted(_SUMMARY_EXACT_FIELDS)}
    if end_day is None:
        for field in sorted(_SUMMARY_SCOPE_FIELDS - {"progress_rows"}):
            left[field] = reference.get(field)
            right[field] = accelerated.get(field)
        left["progress_rows"] = reference.get("progress_rows")
        right["progress_rows"] = accelerated.get("progress_rows")
    else:
        left["progress_rows"] = _progress_through(reference.get("progress_rows"), end_day)
        right["progress_rows"] = _exact_progress_rows(
            accelerated.get("progress_rows"),
            start_day="2026-01-01",
            end_day=end_day,
        )
    progress_count = len(left.get("progress_rows") or [])
    if canonical_bytes(left) != canonical_bytes(right):
        differences = _difference_paths(left, right)
        raise SemanticAcceptanceError(
            "summary_semantic_mismatch:" + ",".join("/".join(path) for path in differences[:8])
        )
    reference_authority, reference_authority_causal = (
        _validate_summary_authority(reference)
    )
    accelerated_authority, accelerated_authority_causal = (
        _validate_summary_authority(accelerated)
    )
    if canonical_bytes(reference_authority_causal) != canonical_bytes(
        accelerated_authority_causal
    ):
        differences = _difference_paths(
            reference_authority_causal, accelerated_authority_causal
        )
        raise SemanticAcceptanceError(
            "summary_authority_semantic_mismatch:"
            + ",".join("/".join(path) for path in differences[:8])
        )
    binding_causal = reference_authority_causal.get("b7_5_contract_binding")
    shared_causal = reference_authority_causal.get("shared_execution_contract")
    if (
        binding_causal is not None
        and canonical_sha256(binding_causal) != _EXPECTED_B7_CAUSAL_ROOT_SHA256
    ):
        raise SemanticAcceptanceError("summary_contract_semantic_root_invalid")
    if (
        shared_causal is not None
        and canonical_sha256(shared_causal) != _EXPECTED_SHARED_CAUSAL_ROOT_SHA256
    ):
        raise SemanticAcceptanceError("summary_shared_contract_semantic_root_invalid")
    reference_authority_values = {
        field: reference.get(field) for field in sorted(_SUMMARY_AUTHORITY_FIELDS)
    }
    accelerated_authority_values = {
        field: accelerated.get(field) for field in sorted(_SUMMARY_AUTHORITY_FIELDS)
    }
    authority_difference_paths = _expanded_difference_paths(
        reference_authority_values, accelerated_authority_values
    )
    classified_authority_differences = []
    for path in authority_difference_paths:
        classification = _authority_difference_rationale(path)
        classified_authority_differences.append(
            {
                "path": list(path),
                "json_pointer": "/" + "/".join(path),
                **classification,
            }
        )
    return {
        "status": "SEMANTICALLY_EQUIVALENT",
        "projection_root_sha256": canonical_sha256(left),
        "authority_causal_projection_root_sha256": canonical_sha256(
            reference_authority_causal
        ),
        "progress_row_count": progress_count,
        "complete_top_level_field_count": len(observed),
        "field_policies": {
            field: SUMMARY_FIELD_POLICIES[field] for field in sorted(observed)
        },
        "reference_authority_validation": reference_authority,
        "accelerated_authority_validation": accelerated_authority,
        "noncausal_authority_difference_count": len(
            classified_authority_differences
        ),
        "noncausal_authority_differences": classified_authority_differences,
        "economic_values_exposed": False,
    }


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open("rb") as handle:
        for index, raw in enumerate(handle):
            if not raw.endswith(b"\n"):
                raise SemanticAcceptanceError(f"jsonl_framing_invalid:{path.name}:{index}")
            try:
                row = json.loads(raw)
            except (UnicodeDecodeError, json.JSONDecodeError):
                raise SemanticAcceptanceError(
                    f"jsonl_row_invalid:{path.name}:{index}"
                ) from None
            if not isinstance(row, dict):
                raise SemanticAcceptanceError(f"jsonl_row_invalid:{path.name}:{index}")
            yield row


def _require_regular_no_symlink_components(path: Path, *, label: str) -> None:
    absolute = Path(path).absolute()
    try:
        relative = absolute.relative_to(ROOT)
    except ValueError:
        raise SemanticAcceptanceError(
            f"semantic_source_file_invalid:{label}"
        ) from None
    current = ROOT
    for component in relative.parts:
        current = current / component
        if current.is_symlink():
            raise SemanticAcceptanceError(
                f"semantic_source_file_invalid:{label}"
            )
    if not absolute.is_file():
        raise SemanticAcceptanceError(f"semantic_source_file_invalid:{label}")


def _row_day(row: Mapping[str, Any]) -> str:
    value = row.get("trading_day")
    if type(value) is str and len(value) == 10:
        try:
            if date.fromisoformat(value).isoformat() == value:
                return value
        except ValueError:
            pass
    for field in ("decision_time_utc", "decision_time", "asof_utc"):
        value = row.get(field)
        if type(value) is str and len(value) >= 10:
            try:
                if date.fromisoformat(value[:10]).isoformat() == value[:10]:
                    return value[:10]
            except ValueError:
                pass
    chunk_start = row.get("chunk_start_day")
    chunk_end = row.get("chunk_end_day")
    if (
        type(chunk_start) is str
        and type(chunk_end) is str
        and chunk_start == chunk_end
        and len(chunk_end) == 10
    ):
        try:
            if date.fromisoformat(chunk_end).isoformat() == chunk_end:
                return chunk_end
        except ValueError:
            pass
    raise SemanticAcceptanceError("semantic_row_day_invalid")


def rows_through(
    rows: Iterable[Mapping[str, Any]],
    *,
    end_day: str | None,
) -> Iterator[Mapping[str, Any]]:
    if end_day is None:
        yield from rows
        return
    for row in rows:
        if _row_day(row) <= end_day:
            yield row


def exact_scope_rows(
    rows: Iterable[Mapping[str, Any]],
    *,
    role: str,
    start_day: str,
    end_day: str,
) -> Iterator[Mapping[str, Any]]:
    """Consume the complete fresh stream and reject every out-of-scope row."""

    for index, row in enumerate(rows):
        day = _row_day(row)
        if day < start_day or day > end_day:
            raise SemanticAcceptanceError(
                f"semantic_row_outside_exact_scope:{role}:{index}:{day}"
            )
        yield row


def _role_path(root: Path, role: str) -> Path:
    return root / f"{PREFIX}_{ROLE_SUFFIXES[role]}"


def _archive_role_rows(root: Path, role: str) -> Iterator[dict[str, Any]]:
    from src.research_infra.replay_acceleration_streaming_archive_verifier import (
        iter_campaign_role_lines,
    )

    manifest = root / "streaming-proof-archive/CAMPAIGN_ARCHIVE_MANIFEST.json"
    for raw in iter_campaign_role_lines(manifest, role):
        try:
            row = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise SemanticAcceptanceError(f"archive_row_invalid:{role}") from None
        if not isinstance(row, dict):
            raise SemanticAcceptanceError(f"archive_row_invalid:{role}")
        yield row


def _role_rows(root: Path, role: str) -> Iterator[dict[str, Any]]:
    path = _role_path(root, role)
    if role in ARCHIVE_ROLES and path.is_file() and path.stat().st_size == 0:
        yield from _archive_role_rows(root, role)
    else:
        yield from iter_jsonl(path)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_bytes())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise SemanticAcceptanceError(f"json_invalid:{path.name}") from None
    if not isinstance(value, dict):
        raise SemanticAcceptanceError(f"json_invalid:{path.name}")
    return value


def _semantic_paths(root: Path) -> dict[str, Path]:
    semantic = root.with_name(root.name + ".semantic-diagnostic")
    return {
        "root": semantic,
        "candidate": semantic / f"{PREFIX}_SEMANTIC_CANDIDATE_LEDGER.jsonl",
        "state": semantic / f"{PREFIX}_SEMANTIC_STATE_CHECKPOINT_LEDGER.jsonl",
        "order_preimage": semantic
        / f"{PREFIX}_SEMANTIC_ORDER_PREIMAGE_LEDGER.jsonl",
        "manifest": semantic / f"{PREFIX}_SEMANTIC_SOURCE_MANIFEST.json",
    }


def validate_semantic_source_manifest(root: Path) -> dict[str, Any]:
    paths = _semantic_paths(root)
    _require_regular_no_symlink_components(paths["manifest"], label="manifest")
    manifest = _load_json(paths["manifest"])
    projection = dict(manifest)
    declared = projection.pop("source_manifest_root_sha256", None)
    schema = manifest.get("schema")
    if manifest.get("acceptance_authorized") is not False or declared != canonical_sha256(
        projection
    ):
        raise SemanticAcceptanceError("semantic_source_manifest_invalid")
    files = manifest.get("files")
    if not isinstance(files, Mapping):
        raise SemanticAcceptanceError("semantic_source_manifest_invalid")
    if schema == "gtos.replay_acceleration.task2_direct_semantic_source_manifest.v1":
        expected_paths = {
            **{role: _role_path(root, role) for role in ROLE_SUFFIXES},
            "semantic_candidate": paths["candidate"],
            "semantic_state_checkpoint": paths["state"],
            "semantic_order_preimage": paths["order_preimage"],
            "partial_summary": root / f"{PREFIX}_PARTIAL_SUMMARY.json",
        }
        if (
            set(files) != set(expected_paths)
            or manifest.get("transport") != "bounded_direct_hot_files"
            or manifest.get("streaming_proof_archive_used") is not False
            or manifest.get("direct_hot_file_count") != len(expected_paths)
            or manifest.get("causal_or_economic_field_excluded") is not False
            or manifest.get("broker_live_authority") is not False
            or manifest.get("broker_mutation_enabled") is not False
            or Path(str(manifest.get("namespace"))).resolve() != root.resolve()
        ):
            raise SemanticAcceptanceError("semantic_source_manifest_invalid")
        scope = manifest.get("scope")
        contract = manifest.get("execution_contract")
        if (
            not isinstance(scope, Mapping)
            or scope
            != {
                "start_day": "2026-01-01",
                "end_day": "2026-01-02",
                "day_count": 2,
                "profile": "repaired_package_conversion_v3",
                "arm_id": "S0R0",
                "chunk_size": 1,
            }
            or not isinstance(contract, Mapping)
            or not _is_sha256(contract.get("runtime_input_contract_root_sha256"))
            or not _is_sha256(
                contract.get("shared_execution_contract_digest_sha256")
            )
            or contract.get("economic_execution_contract_digest_sha256")
            != EXPECTED_ECONOMIC_CONTRACT_DIGEST
        ):
            raise SemanticAcceptanceError("semantic_source_manifest_invalid")
        for role, expected in expected_paths.items():
            record = files.get(role)
            expected_keys = {"path", "format", "bytes", "sha256"}
            if role != "partial_summary":
                expected_keys.add("rows")
            if (
                not isinstance(record, Mapping)
                or set(record) != expected_keys
                or type(record.get("path")) is not str
            ):
                raise SemanticAcceptanceError(f"semantic_source_file_invalid:{role}")
            recorded_path = Path(record["path"])
            _require_regular_no_symlink_components(recorded_path, label=role)
            _require_regular_no_symlink_components(expected, label=role)
            if (
                Path(os.path.abspath(recorded_path))
                != Path(os.path.abspath(expected))
                or record.get("bytes") != expected.stat().st_size
                or record.get("sha256") != file_sha256(expected)
            ):
                raise SemanticAcceptanceError(f"semantic_source_file_invalid:{role}")
            if role == "partial_summary":
                if record.get("format") != "json":
                    raise SemanticAcceptanceError(
                        "semantic_source_file_invalid:partial_summary"
                    )
                _load_json(expected)
                continue
            row_count = 0
            with expected.open("rb") as handle:
                for raw in handle:
                    if not raw.endswith(b"\n"):
                        raise SemanticAcceptanceError(
                            f"semantic_source_file_invalid:{role}"
                        )
                    try:
                        row = json.loads(raw)
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        raise SemanticAcceptanceError(
                            f"semantic_source_file_invalid:{role}"
                        ) from None
                    if not isinstance(row, Mapping):
                        raise SemanticAcceptanceError(
                            f"semantic_source_file_invalid:{role}"
                        )
                    row_count += 1
            if record.get("format") != "jsonl" or record.get("rows") != row_count:
                raise SemanticAcceptanceError(f"semantic_source_file_invalid:{role}")
        source = manifest.get("source_identity")
        if (
            not isinstance(source, Mapping)
            or set(source)
            != {
                "arm_fingerprint_sha256",
                "arm_id",
                "profile",
                "source_bundle_dir",
                "source_plan_digest_sha256",
                "source_rebind_authority_sha256",
                "source_selection_sha256",
            }
            or source.get("source_plan_digest_sha256")
            != EXPECTED_SOURCE_PLAN_DIGEST
            or source.get("arm_fingerprint_sha256") != EXPECTED_ARM_FINGERPRINT
            or source.get("arm_id") != "S0R0"
            or source.get("profile") != "repaired_package_conversion_v3"
            or not _is_sha256(source.get("source_selection_sha256"))
            or not _is_sha256(source.get("source_rebind_authority_sha256"))
        ):
            raise SemanticAcceptanceError("semantic_source_identity_invalid")
        return {
            "schema": schema,
            "source_manifest_root_sha256": declared,
            "candidate_sha256": files["semantic_candidate"]["sha256"],
            "state_checkpoint_sha256": files["semantic_state_checkpoint"][
                "sha256"
            ],
            "direct_hot_file_count": len(files),
            "direct_hot_files_root_sha256": canonical_sha256(files),
            "runtime_input_contract_root_sha256": contract[
                "runtime_input_contract_root_sha256"
            ],
            "shared_execution_contract_digest_sha256": contract[
                "shared_execution_contract_digest_sha256"
            ],
            "economic_execution_contract_digest_sha256": contract[
                "economic_execution_contract_digest_sha256"
            ],
        }
    if schema != "gtos.replay_acceleration.semantic_source_manifest.v1":
        raise SemanticAcceptanceError("semantic_source_manifest_invalid")
    expected_paths = {
        "candidate": paths["candidate"],
        "state_checkpoint": paths["state"],
        "order_preimage": paths["order_preimage"],
        "order": _role_path(root, "order"),
        "trade": _role_path(root, "trade"),
        "oracle": _role_path(root, "oracle"),
    }
    if set(files) != set(expected_paths):
        raise SemanticAcceptanceError("semantic_source_manifest_invalid")
    for role, expected in expected_paths.items():
        record = files.get(role)
        if (
            not isinstance(record, Mapping)
            or set(record) != {"path", "bytes", "sha256", "row_count"}
            or type(record.get("path")) is not str
        ):
            raise SemanticAcceptanceError(f"semantic_source_file_invalid:{role}")
        recorded_path = Path(record["path"])
        _require_regular_no_symlink_components(recorded_path, label=role)
        _require_regular_no_symlink_components(expected, label=role)
        if (
            Path(os.path.abspath(recorded_path)) != Path(os.path.abspath(expected))
            or record.get("sha256") != file_sha256(expected)
            or record.get("bytes") != expected.stat().st_size
        ):
            raise SemanticAcceptanceError(f"semantic_source_file_invalid:{role}")
        row_count = sum(1 for _row in iter_jsonl(expected))
        if record.get("row_count") != row_count:
            raise SemanticAcceptanceError(f"semantic_source_file_invalid:{role}")
    source = manifest.get("source_identity")
    if (
        not isinstance(source, Mapping)
        or set(source)
        != {
            "accelerated_code_config_authority_root_sha256",
            "arm_fingerprint_sha256",
            "arm_id",
            "campaign_id",
            "output_prefix",
            "profile",
            "run_identity_root_sha256",
            "shared_execution_contract_sha256",
            "source_plan_digest_sha256",
        }
        or source.get("source_plan_digest_sha256") != EXPECTED_SOURCE_PLAN_DIGEST
        or source.get("arm_fingerprint_sha256") != EXPECTED_ARM_FINGERPRINT
        or source.get("arm_id") != "S0R0"
    ):
        raise SemanticAcceptanceError("semantic_source_identity_invalid")
    return {
        "schema": schema,
        "source_manifest_root_sha256": declared,
        "candidate_sha256": files["candidate"]["sha256"],
        "state_checkpoint_sha256": files["state_checkpoint"]["sha256"],
        "authenticated_file_roles": sorted(files),
        "authenticated_files_root_sha256": canonical_sha256(files),
    }


def validate_state_checkpoints(
    rows: Iterable[Mapping[str, Any]],
    *,
    expected_days: Sequence[str],
    require_account_preimage: bool = False,
) -> dict[str, Any]:
    material = list(rows)
    if len(material) != 2 * len(expected_days):
        raise SemanticAcceptanceError("state_checkpoint_count_invalid")
    prior_post: Mapping[str, Any] | None = None
    projected = _ArrayRoot()
    for day_index, day in enumerate(expected_days):
        pre = material[day_index * 2]
        post = material[day_index * 2 + 1]
        for boundary, row in (("pre_day", pre), ("post_day", post)):
            state = row.get("state_projection")
            if (
                row.get("schema")
                != "gtos.replay_acceleration.semantic_state_checkpoint.v1"
                or row.get("trading_day") != day
                or row.get("boundary") != boundary
                or not isinstance(state, Mapping)
                or any(
                    not _is_sha256(state.get(field))
                    for field in (
                        "account_root_sha256",
                        "broker_root_sha256",
                        "event_queue_root_sha256",
                        "reservation_root_sha256",
                    )
                )
                or type(state.get("selected_order_sequence")) is not int
                or state.get("selected_order_sequence", -1) < 0
                or row.get("state_root_sha256") != canonical_sha256(state)
            ):
                raise SemanticAcceptanceError("state_checkpoint_invalid")
            account_preimage = row.get("account_preimage")
            if require_account_preimage:
                if (
                    not isinstance(account_preimage, Mapping)
                    or set(account_preimage) != ACCOUNT_STATE_FIELDS
                    or producer_sha256(account_preimage)
                    != state.get("account_root_sha256")
                    or producer_sha256(account_preimage.get("event_queue"))
                    != state.get("event_queue_root_sha256")
                    or producer_sha256(
                        {
                            field: account_preimage.get(field)
                            for field in RESERVATION_ACCOUNT_FIELDS
                        }
                    )
                    != state.get("reservation_root_sha256")
                ):
                    raise SemanticAcceptanceError(
                        "account_preimage_accelerated_root_mismatch"
                    )
            elif account_preimage is not None:
                raise SemanticAcceptanceError(
                    "reference_account_preimage_unexpected"
                )
            projection_row = dict(row)
            projection_row.pop("account_preimage", None)
            projected.update(projection_row)
        if prior_post is not None and canonical_bytes(prior_post) != canonical_bytes(
            pre.get("state_projection")
        ):
            raise SemanticAcceptanceError("cross_day_state_continuity_mismatch")
        prior_post = post.get("state_projection")
    return {
        "status": "STATE_CONTINUITY_VERIFIED",
        "day_count": len(expected_days),
        "checkpoint_row_count": len(material),
        "ordered_checkpoint_root_sha256": projected.hexdigest(),
        "terminal_state_root_sha256": material[-1]["state_root_sha256"],
        "economic_values_exposed": False,
    }


def _trade_identity(row: Mapping[str, Any]) -> str:
    identity = str(row.get("simulated_trade_id") or "").strip()
    if not identity:
        raise SemanticAcceptanceError("account_closed_trade_identity_missing")
    return identity


def _unique_trade_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    side: str,
) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        identity = _trade_identity(row)
        previous = result.get(identity)
        if previous is not None and canonical_bytes(previous) != canonical_bytes(row):
            raise SemanticAcceptanceError(
                f"account_trade_identity_duplicate:{side}:{identity}"
            )
        result[identity] = row
    return result


def _account_semantic_pair(
    *,
    reference_account_root: str,
    accelerated_account_preimage: Mapping[str, Any],
    reference_trades: Mapping[str, Mapping[str, Any]],
    accelerated_trades: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """Reconstruct the historical account preimage from proven trade closure."""

    accelerated = copy.deepcopy(dict(accelerated_account_preimage))
    reference = copy.deepcopy(accelerated)
    closed = accelerated.get("closed_trades")
    reference_closed = reference.get("closed_trades")
    if not isinstance(closed, list) or not isinstance(reference_closed, list):
        raise SemanticAcceptanceError("account_closed_trade_preimage_invalid")
    for index, closed_trade in enumerate(closed):
        if not isinstance(closed_trade, Mapping):
            raise SemanticAcceptanceError("account_closed_trade_preimage_invalid")
        identity = _trade_identity(closed_trade)
        reference_trade = reference_trades.get(identity)
        accelerated_trade = accelerated_trades.get(identity)
        if not isinstance(reference_trade, Mapping) or not isinstance(
            accelerated_trade, Mapping
        ):
            raise SemanticAcceptanceError(
                f"account_closed_trade_ledger_owner_missing:{identity}"
            )
        for path in _difference_paths(reference_trade, accelerated_trade):
            entry = _entry_for_path("trade", path)
            if entry is None:
                raise SemanticAcceptanceError(
                    "account_closed_trade_unproven_difference:"
                    + identity
                    + ":"
                    + "/".join(path)
                )
            try:
                closed_value = _path_value(closed_trade, path)
                accelerated_value = _path_value(accelerated_trade, path)
            except (KeyError, IndexError, ValueError, TypeError):
                continue
            if canonical_bytes(closed_value) != canonical_bytes(accelerated_value):
                raise SemanticAcceptanceError(
                    f"account_closed_trade_fresh_owner_mismatch:{identity}"
                )
            _set_path(
                reference_closed[index],
                path,
                copy.deepcopy(_path_value(reference_trade, path)),
            )
    if producer_sha256(reference) != reference_account_root:
        raise SemanticAcceptanceError("account_preimage_reference_root_mismatch")

    normalized_reference = copy.deepcopy(reference)
    normalized_accelerated = copy.deepcopy(accelerated)
    normalized_count = 0
    for path in _difference_paths(reference, accelerated):
        if len(path) < 3 or path[0] != "closed_trades":
            raise SemanticAcceptanceError(
                "account_preimage_semantic_mismatch:" + "/".join(path)
            )
        trade_path = path[2:]
        entry = _entry_for_path("trade", trade_path)
        if entry is None:
            raise SemanticAcceptanceError(
                "account_preimage_semantic_mismatch:" + "/".join(path)
            )
        left_value = _path_value(reference, path)
        right_value = _path_value(accelerated, path)
        if entry.get("value_class") == "wall_clock_timestamp":
            if not _is_utc_timestamp(left_value) or not _is_utc_timestamp(right_value):
                raise SemanticAcceptanceError("account_preimage_timestamp_invalid")
            replacement = RUNTIME_SENTINEL
        else:
            if not _is_sha256(left_value) or not _is_sha256(right_value):
                raise SemanticAcceptanceError("account_preimage_hash_invalid")
            replacement = HASH_SENTINEL
        _set_path(normalized_reference, path, replacement)
        _set_path(normalized_accelerated, path, replacement)
        normalized_count += 1
    if canonical_bytes(normalized_reference) != canonical_bytes(
        normalized_accelerated
    ):
        raise SemanticAcceptanceError("account_preimage_projection_mismatch")
    return normalized_reference, normalized_accelerated, normalized_count


def compare_state_checkpoint_semantics(
    reference_rows: Sequence[Mapping[str, Any]],
    accelerated_rows: Sequence[Mapping[str, Any]],
    *,
    reference_progress_rows: Sequence[Mapping[str, Any]],
    accelerated_progress_rows: Sequence[Mapping[str, Any]],
    reference_order_rows: Iterable[Mapping[str, Any]],
    accelerated_order_rows: Iterable[Mapping[str, Any]],
    reference_trade_rows: Iterable[Mapping[str, Any]],
    accelerated_trade_rows: Iterable[Mapping[str, Any]],
    derived_hash_proofs: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Prove the one observed opaque account-hash closure without hiding state."""

    days = ("2026-01-01", "2026-01-02")
    reference_state = validate_state_checkpoints(reference_rows, expected_days=days)
    accelerated_state = validate_state_checkpoints(
        accelerated_rows,
        expected_days=days,
        require_account_preimage=True,
    )
    if (
        len(reference_progress_rows) != len(days)
        or any(
            row.get("start_day") != day or row.get("end_day") != day
            for row, day in zip(reference_progress_rows, days)
        )
        or any(
            row.get("start_day") != day or row.get("end_day") != day
            for row, day in zip(accelerated_progress_rows, days)
        )
    ):
        raise SemanticAcceptanceError("account_progress_witness_scope_invalid")
    if canonical_bytes(reference_progress_rows) != canonical_bytes(
        accelerated_progress_rows
    ):
        raise SemanticAcceptanceError("account_progress_witness_mismatch")
    reference_order_material = list(reference_order_rows)
    accelerated_order_material = list(accelerated_order_rows)
    reference_trade_material = list(reference_trade_rows)
    accelerated_trade_material = list(accelerated_trade_rows)
    order_witness = compare_role_rows(
        "order",
        reference_order_material,
        accelerated_order_material,
        derived_hash_proofs=derived_hash_proofs,
    )
    trade_witness = compare_role_rows(
        "trade",
        reference_trade_material,
        accelerated_trade_material,
        derived_hash_proofs=derived_hash_proofs,
    )
    if (
        trade_witness["row_count"] <= 0
        or trade_witness["excluded_volatile_difference_count"] <= 0
    ):
        raise SemanticAcceptanceError("account_hash_closure_trade_witness_missing")
    projected = _ArrayRoot()
    observed: Counter[str] = Counter()
    reference_trade_index = _unique_trade_rows(
        reference_trade_material, side="reference"
    )
    accelerated_trade_index = _unique_trade_rows(
        accelerated_trade_material, side="accelerated"
    )
    exact_checkpoint_count = 0
    account_hash_closure_checkpoint_count = 0
    normalized_account_leaf_count = 0
    for reference, accelerated in zip(reference_rows, accelerated_rows, strict=True):
        account_preimage = accelerated.get("account_preimage")
        if not isinstance(account_preimage, Mapping):
            raise SemanticAcceptanceError("account_preimage_missing")
        normalized_reference, normalized_accelerated, normalized_count = (
            _account_semantic_pair(
                reference_account_root=str(
                    reference.get("state_projection", {}).get(
                        "account_root_sha256"
                    )
                ),
                accelerated_account_preimage=account_preimage,
                reference_trades=reference_trade_index,
                accelerated_trades=accelerated_trade_index,
            )
        )
        normalized_account_leaf_count += normalized_count
        left = copy.deepcopy(dict(reference))
        right = copy.deepcopy(dict(accelerated))
        right.pop("account_preimage", None)
        semantic_account_root = producer_sha256(normalized_reference)
        if semantic_account_root != producer_sha256(normalized_accelerated):
            raise SemanticAcceptanceError("account_preimage_projection_mismatch")
        raw_account_equal = (
            _path_value(left, ("state_projection", "account_root_sha256"))
            == _path_value(right, ("state_projection", "account_root_sha256"))
        )
        for target in (left, right):
            target["state_projection"]["account_root_sha256"] = (
                semantic_account_root
            )
            target["state_root_sha256"] = canonical_sha256(
                target["state_projection"]
            )
        if canonical_bytes(left) != canonical_bytes(right):
            raise SemanticAcceptanceError("state_checkpoint_semantic_mismatch")
        if raw_account_equal:
            exact_checkpoint_count += 1
        else:
            account_hash_closure_checkpoint_count += 1
            observed["state_projection/account_root_sha256"] += 1
            observed["state_root_sha256"] += 1
        projected.update(left)
    if account_hash_closure_checkpoint_count <= 0:
        raise SemanticAcceptanceError("state_checkpoint_hash_closure_not_observed")
    progress_root = canonical_sha256(list(reference_progress_rows))
    coverage = {
        "balance_equity_peak_drawdown_and_daily_start": (
            "exact_ordered_chunk_progress_economics"
        ),
        "accepted_risk_maps_pending_and_open": (
            "exact_reservation_root_each_checkpoint"
        ),
        "closed_trades": "ordered_trade_semantic_projection",
        "event_queue": "exact_event_queue_root_each_checkpoint",
        "event_sequence": (
            "ordered_order_trade_lifecycle_and_selected_order_sequence"
        ),
        "broker_state": "exact_broker_root_each_checkpoint",
    }
    witness_core = {
        "progress_rows_root_sha256": progress_root,
        "order_projection_root_sha256": order_witness[
            "ordered_semantic_projection_root_sha256"
        ],
        "trade_projection_root_sha256": trade_witness[
            "ordered_semantic_projection_root_sha256"
        ],
        "account_state_field_coverage": coverage,
        "reference_terminal_state_root_sha256": reference_state[
            "terminal_state_root_sha256"
        ],
        "accelerated_terminal_state_root_sha256": accelerated_state[
            "terminal_state_root_sha256"
        ],
    }
    return {
        "status": "SEMANTIC_ACCOUNT_STATE_EQUIVALENT",
        "ordered_state_projection_root_sha256": projected.hexdigest(),
        "exact_checkpoint_count": exact_checkpoint_count,
        "account_hash_closure_checkpoint_count": account_hash_closure_checkpoint_count,
        "excluded_derived_hash_difference_count": sum(observed.values()),
        "observed_allowlisted_paths": dict(sorted(observed.items())),
        "reference_state": reference_state,
        "accelerated_state": accelerated_state,
        "order_witness": order_witness,
        "trade_witness": trade_witness,
        "account_state_field_coverage": coverage,
        "account_state_field_count": len(ACCOUNT_STATE_FIELDS),
        "account_state_fields": sorted(ACCOUNT_STATE_FIELDS),
        "normalized_closed_trade_runtime_leaf_count": normalized_account_leaf_count,
        "account_semantic_witness_root_sha256": canonical_sha256(witness_core),
        "meaningful_difference_count": 0,
        "unknown_difference_count": 0,
        "economic_values_exposed": False,
    }


def _compare_candidates_and_state(
    existing_root: Path,
    fresh_root: Path,
    *,
    existing_summary: Mapping[str, Any],
    fresh_summary: Mapping[str, Any],
    derived_hash_proofs: Mapping[str, Any],
) -> dict[str, Any]:
    existing = _semantic_paths(existing_root)
    fresh = _semantic_paths(fresh_root)
    days = ("2026-01-01", "2026-01-02")
    candidate = compare_role_rows(
        "candidate",
        rows_through(iter_jsonl(existing["candidate"]), end_day=days[-1]),
        exact_scope_rows(
            iter_jsonl(fresh["candidate"]),
            role="candidate",
            start_day=days[0],
            end_day=days[-1],
        ),
    )
    existing_state_rows = list(
        rows_through(iter_jsonl(existing["state"]), end_day=days[-1])
    )
    fresh_state_rows = list(iter_jsonl(fresh["state"]))
    existing_progress = _progress_through(
        existing_summary.get("progress_rows"), days[-1]
    )
    fresh_progress = _exact_progress_rows(
        fresh_summary.get("progress_rows"),
        start_day=days[0],
        end_day=days[-1],
    )
    state = compare_state_checkpoint_semantics(
        existing_state_rows,
        fresh_state_rows,
        reference_progress_rows=existing_progress,
        accelerated_progress_rows=fresh_progress,
        reference_order_rows=rows_through(
            _role_rows(existing_root, "order"), end_day=days[-1]
        ),
        accelerated_order_rows=rows_through(
            exact_scope_rows(
                _role_rows(fresh_root, "order"),
                role="order",
                start_day=days[0],
                end_day=days[-1],
            ),
            end_day=days[-1],
        ),
        reference_trade_rows=rows_through(
            _role_rows(existing_root, "trade"), end_day=days[-1]
        ),
        accelerated_trade_rows=rows_through(
            exact_scope_rows(
                _role_rows(fresh_root, "trade"),
                role="trade",
                start_day=days[0],
                end_day=days[-1],
            ),
            end_day=days[-1],
        ),
        derived_hash_proofs=derived_hash_proofs,
    )
    return {
        "candidate_identity_order": candidate,
        "state_continuity_and_account_semantics": state,
    }


def _physical_disposition() -> dict[str, Any]:
    receipt = _load_json(PHYSICAL_OVERRIDE_RECEIPT)
    route = receipt.get("route_decision")
    interruption = receipt.get("interruption")
    physical_child = (
        interruption.get("physical_child")
        if isinstance(interruption, Mapping)
        else None
    )
    waiting_codex = (
        interruption.get("waiting_codex_cli")
        if isinstance(interruption, Mapping)
        else None
    )
    if (
        receipt.get("status") != "OWNER_APPROVED_ROUTE_OVERRIDE_PRESERVED_AND_STOPPED"
        or not isinstance(route, Mapping)
        or route.get("jan2_post_cleanup_checkpoint_sealed") is not False
        or route.get("automatic_relaunch_permitted") is not False
        or not isinstance(physical_child, Mapping)
        or physical_child.get("alive_after") is not False
        or not isinstance(waiting_codex, Mapping)
        or waiting_codex.get("alive_after") is not False
    ):
        raise SemanticAcceptanceError("physical_override_disposition_invalid")
    return {
        "status": "JAN1_CHECKPOINT_PLUS_LEGACY_DENSE_DAY_COST_LOWER_BOUND_ONLY",
        "jan2_post_cleanup_checkpoint_sealed": False,
        "physical_semantic_comparator_used": False,
        "automatic_relaunch_permitted": False,
        "override_receipt_sha256": file_sha256(PHYSICAL_OVERRIDE_RECEIPT),
    }


def _strong_source_rebind_authentication() -> dict[str, Any]:
    authority = _load_json(STRONG_SOURCE_REBIND_AUTHORITY)
    projection = dict(authority)
    declared = projection.pop("authority_root_sha256", None)
    transform = authority.get("bundle_transformation")
    successor_bundle = authority.get("successor_bundle")
    successor_selection = authority.get("successor_selection")
    verifiers = authority.get("independent_verifiers")
    if (
        file_sha256(STRONG_SOURCE_REBIND_AUTHORITY)
        != EXPECTED_STRONG_SOURCE_REBIND_FILE_SHA256
        or declared != canonical_sha256(projection)
        or declared != EXPECTED_STRONG_SOURCE_REBIND_ROOT_SHA256
        or authority.get("status")
        != "ACCEPTED_SOURCE_BYTES_IDENTICAL_IMPLEMENTATION_SUCCESSOR"
        or authority.get("continuation_authorized") is not False
        or authority.get("policy_execution_entered") is not False
        or authority.get("economic_values_exposed") is not False
        or authority.get("broker_live_authority") is not False
        or not isinstance(transform, Mapping)
        or transform.get("source_plan_exact") is not True
        or transform.get("source_payloads_exact") is not True
        or transform.get("normalized_rows_exact") is not True
        or transform.get("selected_day_rows_exact") is not True
        or transform.get("cross_symbol_barrier_exact") is not True
        or transform.get("physical_partition_count") != 96
        or transform.get("unexpected_difference_count") != 0
        or not isinstance(successor_bundle, Mapping)
        or successor_bundle.get("bundle_root_sha256")
        != "56841c1789246c4f5164921f07b5922b77c4fc06d407584f8e33c61731c6b5e7"
        or not isinstance(successor_selection, Mapping)
        or successor_selection.get("selection_root_sha256")
        != "c6c08af93039c1a779526225f21be882aff3d1dbafd910f9817efa79f5c71476"
        or not isinstance(verifiers, list)
        or len(verifiers) != 1
        or not isinstance(verifiers[0], Mapping)
        or verifiers[0].get("physical_recomputed_root_sha256")
        != "1accee925488b129d1294fc8813a3cf495613b8461c7649fee44c3f34da2052c"
        or verifiers[0].get("logical_recomputed_root_sha256")
        != "ab8440912822469267a96c1cb3237a308fd42e0c47e55b735b88da5a8df540d8"
    ):
        raise SemanticAcceptanceError("strong_source_rebind_authentication_invalid")
    return {
        "file_sha256": EXPECTED_STRONG_SOURCE_REBIND_FILE_SHA256,
        "authority_root_sha256": declared,
        "transformation_root_sha256": transform.get(
            "transformation_root_sha256"
        ),
        "successor_bundle_root_sha256": successor_bundle.get(
            "bundle_root_sha256"
        ),
        "successor_selection_root_sha256": successor_selection.get(
            "selection_root_sha256"
        ),
        "independent_physical_recomputed_root_sha256": verifiers[0].get(
            "physical_recomputed_root_sha256"
        ),
        "independent_logical_recomputed_root_sha256": verifiers[0].get(
            "logical_recomputed_root_sha256"
        ),
    }


def _authenticate_legacy_and_archives(
    fresh_semantic: Mapping[str, Any],
) -> dict[str, Any]:
    from src.research_infra.replay_acceleration_partial_golden_successor_authority import (
        verify_successor_authority,
    )
    from src.research_infra.replay_acceleration_partial_golden_verifier import (
        verify_partial_golden_manifest,
    )
    from src.research_infra.replay_acceleration_streaming_archive_verifier import (
        verify_campaign,
    )

    legacy_manifest = verify_partial_golden_manifest(
        LEGACY_MANIFEST,
        git_root=ROOT,
    )
    successor = verify_successor_authority(LEGACY_SUCCESSOR_AUTHORITY)
    existing_archive = verify_campaign(
        ACCELERATED_JAN1_7_ROOT
        / "streaming-proof-archive/CAMPAIGN_ARCHIVE_MANIFEST.json"
    )
    return {
        "legacy_manifest_verification_root_sha256": legacy_manifest.get(
            "verification_root_sha256"
        ),
        "legacy_successor_verification_root_sha256": successor.get(
            "verification_root_sha256"
        ),
        "existing_archive_verification_root_sha256": existing_archive.get(
            "verification_root_sha256"
        ),
        "fresh_direct_semantic_source_manifest_root_sha256": (
            fresh_semantic.get("source_manifest_root_sha256")
        ),
        "fresh_direct_hot_files_root_sha256": fresh_semantic.get(
            "direct_hot_files_root_sha256"
        ),
        "fresh_streaming_archive_claimed": False,
        "strong_source_rebind_authentication": (
            _strong_source_rebind_authentication()
        ),
    }


def _fresh_execution_identity(fresh_root: Path) -> dict[str, Any]:
    receipt = _load_json(fresh_root / "TASK2_SEMANTIC_SLICE_EXECUTION_RECEIPT.json")
    receipt_projection = dict(receipt)
    declared_receipt_root = receipt_projection.pop("receipt_root_sha256", None)
    scope = receipt.get("scope")
    semantic_manifest = receipt.get("semantic_source_manifest")
    checkpoint = receipt.get("task2_semantic_checkpoint_authority")
    checkpoint_projection = dict(checkpoint) if isinstance(checkpoint, Mapping) else {}
    declared_checkpoint_root = checkpoint_projection.pop(
        "checkpoint_root_sha256", None
    )
    if (
        declared_receipt_root != canonical_sha256(receipt_projection)
        or receipt.get("status") != "TASK2_ACCELERATED_JAN1_2_COMPLETE"
        or not isinstance(scope, Mapping)
        or scope.get("start_day") != "2026-01-01"
        or scope.get("end_day") != "2026-01-02"
        or scope.get("day_count") != 2
        or scope.get("arm_id") != "S0R0"
        or receipt.get("source_plan_digest_sha256") != EXPECTED_SOURCE_PLAN_DIGEST
        or receipt.get("arm_fingerprint_sha256") != EXPECTED_ARM_FINGERPRINT
        or receipt.get("economic_execution_contract_digest_sha256")
        != EXPECTED_ECONOMIC_CONTRACT_DIGEST
        or receipt.get("broker_live_authority") is not False
        or receipt.get("broker_mutation_enabled") is not False
        or receipt.get("proof_transport") != "bounded_direct_hot_files"
        or receipt.get("streaming_proof_archive_used") is not False
        or not isinstance(checkpoint, Mapping)
        or checkpoint.get("status")
        != "JAN1_2_POST_CLEANUP_CHECKPOINT_COMPLETE"
        or checkpoint.get("start_day") != "2026-01-01"
        or checkpoint.get("end_day") != "2026-01-02"
        or checkpoint.get("completed_day_count") != 2
        or checkpoint.get("canonical_source_authority_start_day")
        != "2026-01-01"
        or checkpoint.get("canonical_source_authority_end_day")
        != "2026-01-31"
        or checkpoint.get("canonical_source_plan_digest_sha256")
        != EXPECTED_SOURCE_PLAN_DIGEST
        or checkpoint.get("acceptance_authorized") is not False
        or checkpoint.get("broker_live_authority") is not False
        or checkpoint.get("broker_mutation_enabled") is not False
        or declared_checkpoint_root != canonical_sha256(checkpoint_projection)
        or not isinstance(semantic_manifest, Mapping)
        or Path(str(semantic_manifest.get("path"))).resolve()
        != _semantic_paths(fresh_root)["manifest"].resolve()
        or semantic_manifest.get("sha256")
        != file_sha256(_semantic_paths(fresh_root)["manifest"])
    ):
        raise SemanticAcceptanceError("fresh_semantic_slice_identity_invalid")
    return {
        "receipt_sha256": file_sha256(
            fresh_root / "TASK2_SEMANTIC_SLICE_EXECUTION_RECEIPT.json"
        ),
        "receipt_root_sha256": receipt.get("receipt_root_sha256"),
        "shared_execution_contract_digest_sha256": receipt.get(
            "shared_execution_contract_digest_sha256"
        ),
    }


def run_acceptance(fresh_root: Path) -> dict[str, Any]:
    fresh_root = Path(os.path.abspath(fresh_root))
    physical = _physical_disposition()
    fresh_identity = _fresh_execution_identity(fresh_root)
    existing_semantic = validate_semantic_source_manifest(ACCELERATED_JAN1_7_ROOT)
    fresh_semantic = validate_semantic_source_manifest(fresh_root)
    if (
        fresh_semantic.get("shared_execution_contract_digest_sha256")
        != fresh_identity.get("shared_execution_contract_digest_sha256")
        or fresh_semantic.get("economic_execution_contract_digest_sha256")
        != EXPECTED_ECONOMIC_CONTRACT_DIGEST
    ):
        raise SemanticAcceptanceError("fresh_semantic_contract_binding_invalid")
    authentication = _authenticate_legacy_and_archives(fresh_semantic)
    full_hash_closure = validate_campaign_hash_closure(
        LEGACY_ROOT,
        ACCELERATED_JAN1_7_ROOT,
        end_day="2026-01-07",
        accelerated_exact_scope=False,
        reference_preimages_required=False,
    )
    fresh_hash_closure = validate_campaign_hash_closure(
        LEGACY_ROOT,
        fresh_root,
        end_day="2026-01-02",
        accelerated_exact_scope=True,
        reference_preimages_required=False,
    )

    full_roles = []
    fresh_roles = []
    for role in ROLE_SUFFIXES:
        full_roles.append(
            compare_role_rows(
                role,
                _role_rows(LEGACY_ROOT, role),
                _role_rows(ACCELERATED_JAN1_7_ROOT, role),
                derived_hash_proofs=full_hash_closure["proof_classes"],
            )
        )
        fresh_roles.append(
            compare_role_rows(
                role,
                (
                    _role_rows(LEGACY_ROOT, role)
                    if role == "source"
                    else rows_through(
                        _role_rows(LEGACY_ROOT, role),
                        end_day="2026-01-02",
                    )
                ),
                (
                    _role_rows(fresh_root, role)
                    if role == "source"
                    else exact_scope_rows(
                        _role_rows(fresh_root, role),
                        role=role,
                        start_day="2026-01-01",
                        end_day="2026-01-02",
                    )
                ),
                derived_hash_proofs=fresh_hash_closure["proof_classes"],
            )
        )

    legacy_summary = _load_json(_role_path(LEGACY_ROOT, "source").with_name(
        f"{PREFIX}_PARTIAL_SUMMARY.json"
    ))
    existing_summary = _load_json(
        ACCELERATED_JAN1_7_ROOT / f"{PREFIX}_PARTIAL_SUMMARY.json"
    )
    fresh_summary = _load_json(fresh_root / f"{PREFIX}_PARTIAL_SUMMARY.json")
    summaries = {
        "jan1_7": compare_summary_semantics(legacy_summary, existing_summary),
        "jan1_2": compare_summary_semantics(
            legacy_summary,
            fresh_summary,
            end_day="2026-01-02",
        ),
    }
    candidate_state = _compare_candidates_and_state(
        ACCELERATED_JAN1_7_ROOT,
        fresh_root,
        existing_summary=existing_summary,
        fresh_summary=fresh_summary,
        derived_hash_proofs=fresh_hash_closure["proof_classes"],
    )
    core = {
        "schema": SCHEMA,
        "status": "TASK2_OWNER_APPROVED_SEMANTIC_EQUIVALENCE_VERIFIED",
        "task": "Replay-Acceleration Task 2",
        # This report is evidence for a separately adjudicated Task 2 closure
        # gate. Semantic normalization must never authorize continuation.
        "acceptance_authorized": SEMANTIC_REPORT_ACCEPTANCE_AUTHORIZED,
        "acceptance_authority": (
            "explicit_owner_route_correction_from_full_opaque_byte_parity_to_"
            "bounded_semantic_equivalence"
        ),
        "withdrawn_gates": {
            "fresh_full_jan1_7_physical_reference_required": False,
            "two_full_physical_references_required": False,
            "volatile_runtime_provenance_raw_byte_equality_required": False,
            "generated_wall_clock_timestamp_or_solely_derived_hash_equality_required": False,
            "withdrawn_gates_claimed_passed": False,
        },
        "physical_reference_disposition": physical,
        "scope": {
            "existing_accelerated_comparison": "2026-01-01_through_2026-01-07",
            "fresh_corrected_accelerated_comparison": "2026-01-01_through_2026-01-02",
            "arm_id": "S0R0",
            "source_plan_digest_sha256": EXPECTED_SOURCE_PLAN_DIGEST,
            "arm_fingerprint_sha256": EXPECTED_ARM_FINGERPRINT,
            "economic_execution_contract_digest_sha256": (
                EXPECTED_ECONOMIC_CONTRACT_DIGEST
            ),
        },
        "allowlist": ALLOWLIST_RECEIPT,
        "derived_hash_closure": {
            "existing_accelerated_jan1_7": full_hash_closure,
            "fresh_corrected_accelerated_jan1_2": fresh_hash_closure,
        },
        "authentication": authentication,
        "semantic_source_manifests": {
            "existing_accelerated": existing_semantic,
            "fresh_corrected_accelerated": fresh_semantic,
        },
        "fresh_execution_identity": fresh_identity,
        "semantic_acceptance_verifier_sha256": file_sha256(
            Path(__file__).resolve()
        ),
        "jan1_7_role_comparisons": full_roles,
        "fresh_jan1_2_role_comparisons": fresh_roles,
        "summary_semantics": summaries,
        "candidate_and_state_continuity": candidate_state,
        "meaningful_difference_count": 0,
        "unknown_difference_count": 0,
        "causal_or_economic_field_normalized": False,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
        "economic_values_exposed": False,
    }
    return {**core, "receipt_root_sha256": canonical_sha256(core)}


def atomic_write_json(path: Path, value: Mapping[str, Any]) -> None:
    path = Path(os.path.abspath(path))
    if path.exists() or path.is_symlink():
        raise SemanticAcceptanceError("semantic_acceptance_output_must_be_new")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("xb") as handle:
        handle.write(canonical_bytes(value) + b"\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fresh-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    receipt = run_acceptance(args.fresh_root)
    atomic_write_json(args.output, receipt)
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
