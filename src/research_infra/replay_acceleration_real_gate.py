"""Structural pause gate for the actual accelerated S0R0 replay process."""

from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import shutil
import stat
import time
from pathlib import Path
from typing import Any, Mapping

from src.research_infra.replay_acceleration_contract_split import (
    ContractSplitError,
    split_shared_execution_contract,
)
from src.research_infra.replay_acceleration_fixed_verifier_authority import (
    FixedVerifierAuthorityError,
    assert_fixed_verifier_code_identity,
    validate_fixed_verifier_code_authority,
)
from src.research_infra.replay_acceleration_immutable_evidence import (
    ImmutableEvidenceError,
    immutable_write_bytes,
    read_regular_nofollow,
)
from src.research_infra.replay_acceleration_partial_golden_successor_authority import (
    SuccessorAuthorityError,
    verify_successor_authority,
)


GATE_REQUEST_SCHEMA = "gtos.replay_acceleration.real_s0r0_gate_request.v1"
GATE_REQUEST_SCHEMA_V2 = "gtos.replay_acceleration.real_s0r0_gate_request.v2"
PARITY_RECEIPT_SCHEMA = "gtos.replay_acceleration.real_s0r0_parity_receipt.v1"
PARITY_REPORT_SCHEMA = "gtos.replay_acceleration.real_s0r0_parity_report.v1"
PARITY_RECEIPT_SCHEMA_V2 = (
    "gtos.replay_acceleration.real_s0r0_parity_receipt.v2"
)
PARITY_REPORT_SCHEMA_V2 = (
    "gtos.replay_acceleration.real_s0r0_parity_report.v2"
)
ARCHIVE_TRANSFORMATION_SCHEMA = (
    "gtos.replay_acceleration.partial_summary_archive_transformation.v1"
)
ARCHIVE_TRANSFORMATION_ALLOWED_TOP_LEVEL_KEYS = (
    "generated_at_utc",
    "streaming_proof_archive",
    "streaming_proof_archive_shards",
    "streaming_capacity_checks",
)
ACCELERATION_ENVELOPE_TRANSFORMATION_SCHEMA = (
    "gtos.replay_acceleration.partial_summary_acceleration_envelope.v2"
)
ACCELERATION_ENVELOPE_ALLOWED_TOP_LEVEL_KEYS = (
    "generated_at_utc",
    "shared_execution_contract",
    "b7_5_contract_binding",
    "runtime_evidence_contract",
    "source_acceleration_authority",
    "attempt5_execution_identity",
    "real_s0r0_parity_gate",
    "route_id",
)
ACCELERATION_ENVELOPE_ALLOWED_NESTED_CHANGES = (
    "capacity_safe_chunk_execution_contract.checkpoints[*].gc_collected_objects",
    "ledger_file_bytes_flushed_before_partial_summary.decision",
    "ledger_file_bytes_flushed_before_partial_summary.scorecard",
    "ledger_file_bytes_flushed_before_partial_summary.missed",
)
ATTEMPT5_EXECUTION_IDENTITY_KEYS = frozenset(
    {
        "schema",
        "status",
        "output_namespace",
        "output_prefix",
        "start_day",
        "parity_day",
        "contract_end_day",
        "arm_id",
        "expected_shared_execution_contract_sha256",
        "expected_source_plan_digest_sha256",
        "expected_arm_fingerprint_sha256",
        "expected_source_bundle_root_sha256",
        "expected_tick_source_manifest_sha256",
        "prospective_golden_authority",
        "runner_path",
        "runner_sha256",
        "source_bundle_consumer_rebind_authority",
        "source_prewarm_workers",
        "tick_diagnostic_manifest_bindings",
        "tick_source_manifest",
        "tick_sparse_cache",
        "policy_execution_entered",
        "legacy_replay_route_invoked",
        "other_arms_launched",
        "broker_live_authority",
        "broker_mutation_enabled",
        "economic_values_exposed",
        "identity_root_sha256",
    }
)
RUNTIME_EVIDENCE_CONTRACT_KEYS = frozenset(
    {
        "schema",
        "root",
        "integration_repo_root",
        "data_roots",
        "inputs",
        "legacy_evidence_mutation_enabled",
        "read_only_existing_evidence",
        "contract_root_sha256",
    }
)
RUNTIME_EVIDENCE_INPUT_NAMES = frozenset(
    {
        "accepted_member_ledger",
        "fillability_labels",
        "member_axis",
        "pending_source_coverage",
        "reconstructed_selection",
        "sleeve_registry",
        "source_materializer",
    }
)
RUNTIME_EVIDENCE_REQUIRED_INPUT_NAMES = frozenset(
    {
        "accepted_member_ledger",
        "fillability_labels",
        "member_axis",
        "reconstructed_selection",
        "sleeve_registry",
    }
)
SHARED_SOURCE_ACCELERATION_KEYS = frozenset(
    {
        "schema",
        "source_bundle_root_sha256",
        "selection_root_sha256",
        "source_plan_digest_sha256",
        "config_projection_root_sha256",
        "normalizer_code_root_sha256",
        "partition_count",
        "symbol_count",
        "policy_execution_entered",
        "candidate_cache_enabled",
        "policy_state_cache_enabled",
        "source_bundle_consumer_rebind_authority",
        "prewarm_worker_count",
    }
)
SOURCE_ACCELERATION_AUTHORITY_KEYS = frozenset(
    {
        *SHARED_SOURCE_ACCELERATION_KEYS,
        "cross_symbol_prewarm_barrier",
        "bundle_validation_seconds",
        "typed_cache_metrics",
    }
) - {"prewarm_worker_count"}
SOURCE_PREWARM_BARRIER_KEYS = frozenset(
    {
        "requested",
        "worker_count",
        "barrier_complete",
        "seconds",
        "partition_count",
        "partition_set_root_sha256",
    }
)
SOURCE_TYPED_CACHE_METRIC_KEYS = frozenset(
    {
        "bytes_read",
        "bytes_written",
        "cold_partition_count",
        "hashing_seconds",
        "normalization_seconds",
        "normalized_row_count",
        "serialization_seconds",
        "verification_seconds",
        "warm_partition_count",
    }
)
SOURCE_REBIND_KEYS = frozenset(
    {
        "schema",
        "authority",
        "authority_path",
        "authority_file_sha256",
        "authority_root_sha256",
        "source_plan_digest_sha256",
        "verified_successor_bundle",
        "verified_successor_selection",
        "policy_execution_entered",
        "continuation_authorized",
        "broker_live_authority",
        "economic_values_exposed",
        "binding_root_sha256",
    }
)
ATTEMPT5_RUNNER_RELATIVE_PATH = (
    "src/research_infra/replay_acceleration_attempt5_typed_sparse_runner.py"
)
TICK_EXPORT_MANIFEST_KEYS = frozenset(
    {
        "account",
        "chunk_minutes",
        "created_at_utc",
        "errors",
        "files",
        "label",
        "manifest_path",
        "mt5_client_kind",
        "output_dir",
        "read_only",
        "schema_version",
        "source_provenance",
        "symbols",
        "terminal",
        "windows",
    }
)
FIXED_VERIFIER_MODULE = (
    "src.research_infra.replay_acceleration_real_parity_verifier"
)
PROSPECTIVE_GOLDEN_AUTHORITY_KEYS = frozenset(
    {
        "golden_manifest_path",
        "golden_manifest_file_sha256",
        "golden_manifest_self_root_sha256",
        "golden_root_sha256",
        "opaque_result_surface_root_sha256",
        "golden_amendment_path",
        "golden_amendment_file_sha256",
        "golden_amendment_self_root_sha256",
        "fixed_verifier_module",
        "fixed_verifier_path",
        "fixed_verifier_file_sha256",
    }
)
PROSPECTIVE_GOLDEN_AUTHORITY_V2_KEYS = PROSPECTIVE_GOLDEN_AUTHORITY_KEYS | {
    "successor_authority_path",
    "successor_authority_file_sha256",
    "successor_authority_root_sha256",
    "successor_authority_verification_root_sha256",
    "economic_execution_contract_digest_sha256",
    "fixed_verifier_code_authority",
    "fixed_verifier_code_authority_root_sha256",
}
GATE_REQUEST_KEYS = frozenset(
    {
        "schema",
        "output_prefix",
        "accelerated_namespace_path",
        "prospective_golden_authority",
        "scope",
        "source_plan_digest_sha256",
        "shared_execution_contract_sha256",
        "arm_fingerprint_sha256",
        "persisted_result_surfaces",
        "partial_summary",
        "partial_summary_archive_transformation",
        "policy_execution_entered",
        "actual_run_campaign_path",
        "synthetic_reducer_harness",
        "candidate_cache_enabled",
        "policy_state_cache_enabled",
        "other_arms_launched",
        "live_broker_authority",
        "broker_mutation_enabled",
        "economic_values_exposed",
        "gate_request_root_sha256",
    }
)
GATE_REQUEST_V2_KEYS = GATE_REQUEST_KEYS | {
    "economic_execution_contract_sha256",
    "accelerator_implementation_authority_root_sha256",
    "partial_summary_acceleration_envelope_transformation",
}
EMPTY_SURFACE_CONTRACT = {
    "bytes": 0,
    "rows": 0,
    "sha256": hashlib.sha256(b"").hexdigest(),
}
RESULT_ROLES = (
    "source",
    "decision",
    "scorecard",
    "order",
    "trade",
    "oracle",
    "missed",
    "bucket",
)
CATEGORY_NAMES = frozenset(
    {
        "candidate_identity_union",
        "ordering_decisions_scorecards",
        "misses",
        "lifecycle_replacement",
        "account_broker_terminal",
        "costs_reservations",
    }
)
RECEIPT_KEYS = frozenset(
    {
        "schema",
        "status",
        "parity_accepted",
        "gate_request_root_sha256",
        "parity_report_root_sha256",
        "golden_manifest_sha256",
        "golden_manifest_self_root_sha256",
        "golden_root_sha256",
        "golden_amendment_sha256",
        "golden_amendment_self_root_sha256",
        "fixed_verifier_file_sha256",
        "partial_golden_verification_root_sha256",
        "persisted_result_surface_root_sha256",
        "partial_summary_semantic_root_sha256",
        "partial_summary_archive_transformation_root_sha256",
        "output_prefix",
        "completed_through_day",
        "accelerated_s0r0_research_route_authorized",
        "same_state_continuation_through_2026_01_31_authorized",
        "other_arms_launched",
        "broker_live_authority",
        "economic_values_exposed",
        "receipt_root_sha256",
    }
)
RECEIPT_V2_KEYS = RECEIPT_KEYS | {
    "partial_summary_acceleration_envelope_transformation_root_sha256",
    "successor_authority_root_sha256",
    "successor_authority_verification_root_sha256",
    "economic_execution_contract_digest_sha256",
    "accelerated_shared_execution_contract_digest_sha256",
    "accelerator_implementation_authority_root_sha256",
    "fixed_verifier_code_authority_root_sha256",
}
REPORT_KEYS = frozenset(
    {
        "schema",
        "valid",
        "gate",
        "output_prefix",
        "scope",
        "contract_identity",
        "all_persisted_ledger_bytes_equal",
        "persisted_result_surface_root_sha256",
        "persisted_result_surfaces",
        "archive_campaign_verifications",
        "archive_campaign_verification_set_root_sha256",
        "partial_summary_semantic_root_sha256",
        "partial_summary_archive_transformation_root_sha256",
        "semantic_category_equality",
        "semantic_category_roots",
        "candidate_identity_union_root_sha256",
        "candidate_identity_union_count",
        "candidate_identity_missing_count",
        "golden_manifest_sha256",
        "golden_manifest_self_root_sha256",
        "golden_root_sha256",
        "golden_amendment_sha256",
        "golden_amendment_self_root_sha256",
        "fixed_verifier_file_sha256",
        "partial_golden_verification_root_sha256",
        "gate_request_root_sha256",
        "economic_values_exposed",
        "independent_writer_imported",
        "independent_runner_imported",
        "other_arms_launched",
        "broker_live_authority",
        "report_root_sha256",
    }
)
REPORT_V2_KEYS = REPORT_KEYS | {
    "partial_summary_acceleration_envelope_transformation_root_sha256",
    "successor_authority_root_sha256",
    "successor_authority_verification_root_sha256",
    "economic_execution_contract_digest_sha256",
    "accelerated_shared_execution_contract_digest_sha256",
    "accelerator_implementation_authority_root_sha256",
    "fixed_verifier_code_authority_root_sha256",
}


class GateRejected(RuntimeError):
    def __init__(self, code: str) -> None:
        self.code = str(code)
        super().__init__(self.code)


def canonical_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError):
        raise GateRejected("gate_noncanonical_value") from None


def root(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def is_sha256(value: Any) -> bool:
    text = str(value or "")
    return len(text) == 64 and all(character in "009abcdef" for character in text)


def _self_root(value: Mapping[str, Any], field: str) -> str:
    projection = dict(value)
    projection.pop(field, None)
    return root(projection)


def _partial_golden_self_root(value: Mapping[str, Any], field: str) -> str:
    projection = dict(value)
    projection.pop(field, None)
    payload = (
        json.dumps(
            projection,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )
    return hashlib.sha256(payload).hexdigest()


def _read_regular_file_nofollow(path: Path, *, code: str) -> bytes:
    try:
        raw, _identity = read_regular_nofollow(path, code=code)
        return raw
    except ImmutableEvidenceError:
        raise GateRejected(code) from None


def _load_bound_json(path: Path, *, code: str) -> tuple[dict[str, Any], bytes]:
    raw = _read_regular_file_nofollow(path, code=code)
    try:
        value = json.loads(raw)
    except (UnicodeError, json.JSONDecodeError):
        raise GateRejected(code) from None
    if type(value) is not dict:
        raise GateRejected(code)
    return value, raw


def _validated_prospective_golden_authority(
    authority: Mapping[str, Any],
) -> dict[str, Any]:
    is_successor = (
        type(authority) is dict
        and set(authority) == PROSPECTIVE_GOLDEN_AUTHORITY_V2_KEYS
    )
    if (
        type(authority) is not dict
        or set(authority)
        not in {
            PROSPECTIVE_GOLDEN_AUTHORITY_KEYS,
            PROSPECTIVE_GOLDEN_AUTHORITY_V2_KEYS,
        }
        or authority.get("fixed_verifier_module") != FIXED_VERIFIER_MODULE
    ):
        raise GateRejected("prospective_golden_authority_invalid")
    hash_fields = (
        "golden_manifest_file_sha256",
        "golden_manifest_self_root_sha256",
        "golden_root_sha256",
        "opaque_result_surface_root_sha256",
        "golden_amendment_file_sha256",
        "golden_amendment_self_root_sha256",
        "fixed_verifier_file_sha256",
        *(
            (
                "successor_authority_file_sha256",
                "successor_authority_root_sha256",
                "successor_authority_verification_root_sha256",
                "economic_execution_contract_digest_sha256",
                "fixed_verifier_code_authority_root_sha256",
            )
            if is_successor
            else ()
        ),
    )
    if any(not is_sha256(authority.get(field)) for field in hash_fields):
        raise GateRejected("prospective_golden_authority_invalid")
    path_fields = (
        "golden_manifest_path",
        "golden_amendment_path",
        "fixed_verifier_path",
        *(("successor_authority_path",) if is_successor else ()),
    )
    if any(
        type(authority.get(field)) is not str
        or not Path(str(authority[field])).is_absolute()
        for field in path_fields
    ):
        raise GateRejected("prospective_golden_authority_invalid")
    manifest_path = Path(str(authority["golden_manifest_path"]))
    amendment_path = Path(str(authority["golden_amendment_path"]))
    verifier_path = Path(str(authority["fixed_verifier_path"]))
    successor_authority_path = (
        Path(str(authority["successor_authority_path"]))
        if is_successor
        else None
    )
    expected_verifier_path = Path(__file__).with_name(
        "replay_acceleration_real_parity_verifier.py"
    ).resolve()
    if (
        manifest_path.resolve() == amendment_path.resolve()
        or manifest_path.resolve() == verifier_path.resolve()
        or amendment_path.resolve() == verifier_path.resolve()
        or verifier_path.resolve() != expected_verifier_path
        or (
            successor_authority_path is not None
            and successor_authority_path.resolve()
            in {
                manifest_path.resolve(),
                amendment_path.resolve(),
                verifier_path.resolve(),
            }
        )
    ):
        raise GateRejected("prospective_golden_authority_invalid")
    manifest, manifest_raw = _load_bound_json(
        manifest_path,
        code="prospective_golden_manifest_invalid",
    )
    amendment, amendment_raw = _load_bound_json(
        amendment_path,
        code="prospective_golden_amendment_invalid",
    )
    verifier_raw = _read_regular_file_nofollow(
        verifier_path,
        code="fixed_parity_verifier_invalid",
    )
    partial_golden = amendment.get("partial_golden")
    if (
        hashlib.sha256(manifest_raw).hexdigest()
        != authority["golden_manifest_file_sha256"]
        or manifest.get("manifest_self_root_sha256")
        != authority["golden_manifest_self_root_sha256"]
        or manifest.get("manifest_self_root_sha256")
        != _partial_golden_self_root(manifest, "manifest_self_root_sha256")
        or manifest.get("golden_root_sha256")
        != authority["golden_root_sha256"]
        or manifest.get("opaque_result_surface_root_sha256")
        != authority["opaque_result_surface_root_sha256"]
        or hashlib.sha256(amendment_raw).hexdigest()
        != authority["golden_amendment_file_sha256"]
        or amendment.get("amendment_self_root_sha256")
        != authority["golden_amendment_self_root_sha256"]
        or amendment.get("amendment_self_root_sha256")
        != _partial_golden_self_root(
            amendment,
            "amendment_self_root_sha256",
        )
        or not isinstance(partial_golden, Mapping)
        or partial_golden.get("manifest_self_root_sha256")
        != authority["golden_manifest_self_root_sha256"]
        or partial_golden.get("golden_root_sha256")
        != authority["golden_root_sha256"]
        or hashlib.sha256(verifier_raw).hexdigest()
        != authority["fixed_verifier_file_sha256"]
    ):
        raise GateRejected("prospective_golden_authority_mismatch")
    if is_successor:
        try:
            successor_verification = verify_successor_authority(
                successor_authority_path
            )
            validate_fixed_verifier_code_authority(
                authority["fixed_verifier_code_authority"],
                module_directory=Path(__file__).parent,
            )
        except (
            SuccessorAuthorityError,
            FixedVerifierAuthorityError,
            TypeError,
        ):
            raise GateRejected("prospective_golden_authority_mismatch") from None
        manifest_successor = manifest.get("successor_authority")
        contract_identity = manifest.get("contract_identity")
        if (
            manifest.get("schema")
            != "gtos.replay_acceleration.partial_golden_manifest.v2"
            or amendment.get("schema")
            != "gtos.replay_acceleration.partial_golden_amendment.v2"
            or not isinstance(manifest_successor, Mapping)
            or not isinstance(contract_identity, Mapping)
            or successor_verification.get("authority_file_sha256")
            != authority["successor_authority_file_sha256"]
            or successor_verification.get("authority_root_sha256")
            != authority["successor_authority_root_sha256"]
            or successor_verification.get("verification_root_sha256")
            != authority["successor_authority_verification_root_sha256"]
            or manifest_successor.get("file_sha256")
            != authority["successor_authority_file_sha256"]
            or manifest_successor.get("authority_root_sha256")
            != authority["successor_authority_root_sha256"]
            or manifest_successor.get("verification_root_sha256")
            != authority["successor_authority_verification_root_sha256"]
            or partial_golden.get("successor_authority_root_sha256")
            != authority["successor_authority_root_sha256"]
            or contract_identity.get(
                "economic_execution_contract_digest_sha256"
            )
            != authority["economic_execution_contract_digest_sha256"]
            or authority["fixed_verifier_code_authority"].get(
                "authority_root_sha256"
            )
            != authority["fixed_verifier_code_authority_root_sha256"]
        ):
            raise GateRejected("prospective_golden_authority_mismatch")
    return dict(authority)


def validate_prospective_golden_authority(
    authority: Mapping[str, Any],
) -> dict[str, Any]:
    return _validated_prospective_golden_authority(authority)


def file_contract(path: Path, *, expected_rows: int | None) -> dict[str, Any]:
    digest = hashlib.sha256()
    rows = 0
    final_byte = b""
    try:
        with Path(path).open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
                rows += chunk.count(b"\n")
                final_byte = chunk[-1:]
    except OSError:
        raise GateRejected("gate_surface_missing") from None
    size = Path(path).stat().st_size
    if size and final_byte != b"\n":
        raise GateRejected("gate_surface_framing_invalid")
    if expected_rows is not None and rows != int(expected_rows):
        raise GateRejected("gate_surface_row_count_mismatch")
    return {"bytes": size, "rows": rows, "sha256": digest.hexdigest()}


def _summary_projection(value: Mapping[str, Any]) -> dict[str, Any]:
    return {
        str(key): item
        for key, item in value.items()
        if str(key) not in ARCHIVE_TRANSFORMATION_ALLOWED_TOP_LEVEL_KEYS
    }


def _partial_summary_archive_transformation(
    *,
    archived: Mapping[str, Mapping[str, Any]],
    post_archive_snapshot_path: Path,
) -> dict[str, Any] | None:
    if not archived:
        return None
    campaign_paths = {
        Path(
            os.path.abspath(
                os.fspath(record.get("archive_campaign_manifest_path") or "")
            )
        )
        for record in archived.values()
    }
    if len(campaign_paths) != 1:
        raise GateRejected("gate_archive_transformation_campaign_invalid")
    campaign_path = next(iter(campaign_paths))
    campaign, _campaign_raw = _load_bound_json(
        campaign_path,
        code="gate_archive_transformation_campaign_invalid",
    )
    expected_campaign_roots = {
        str(record.get("archive_campaign_manifest_root_sha256") or "")
        for record in archived.values()
    }
    shards = campaign.get("shards")
    if (
        campaign.get("schema")
        != "gtos.replay_acceleration.streaming_proof_campaign.v1"
        or campaign.get("campaign_manifest_root_sha256")
        != _self_root(campaign, "campaign_manifest_root_sha256")
        or expected_campaign_roots
        != {str(campaign.get("campaign_manifest_root_sha256") or "")}
        or type(shards) is not list
        or not shards
        or type(shards[-1]) is not dict
        or campaign.get("terminal_checkpoint_chain_root_sha256")
        != shards[-1].get("checkpoint_chain_root_sha256")
    ):
        raise GateRejected("gate_archive_transformation_campaign_invalid")
    terminal_shard = shards[-1]
    checkpoint_preimage_path = Path(
        str(terminal_shard.get("checkpoint_preimage_path") or "")
    )
    if not checkpoint_preimage_path.is_absolute():
        raise GateRejected("gate_archive_transformation_preimage_invalid")
    checkpoint_preimage, checkpoint_preimage_raw = _load_bound_json(
        checkpoint_preimage_path,
        code="gate_archive_transformation_preimage_invalid",
    )
    snapshot = checkpoint_preimage.get("pre_archive_partial_summary")
    if (
        hashlib.sha256(checkpoint_preimage_raw).hexdigest()
        != terminal_shard.get("checkpoint_preimage_sha256")
        or checkpoint_preimage.get("checkpoint_root_sha256")
        != terminal_shard.get("checkpoint_root_sha256")
        or checkpoint_preimage.get("checkpoint_root_sha256")
        != _self_root(checkpoint_preimage, "checkpoint_root_sha256")
        or type(snapshot) is not dict
    ):
        raise GateRejected("gate_archive_transformation_preimage_invalid")
    pre_archive_snapshot_path = Path(str(snapshot.get("snapshot_path") or ""))
    if not pre_archive_snapshot_path.is_absolute():
        raise GateRejected("gate_archive_transformation_snapshot_invalid")
    pre_archive_raw = _read_regular_file_nofollow(
        pre_archive_snapshot_path,
        code="gate_archive_transformation_snapshot_invalid",
    )
    post_archive_raw = _read_regular_file_nofollow(
        post_archive_snapshot_path,
        code="gate_archive_transformation_snapshot_invalid",
    )
    try:
        pre_archive_partial = json.loads(pre_archive_raw)
        post_archive_partial = json.loads(post_archive_raw)
    except (UnicodeError, json.JSONDecodeError):
        raise GateRejected("gate_archive_transformation_snapshot_invalid") from None
    if (
        type(pre_archive_partial) is not dict
        or type(post_archive_partial) is not dict
        or snapshot.get("bytes") != len(pre_archive_raw)
        or snapshot.get("sha256")
        != hashlib.sha256(pre_archive_raw).hexdigest()
    ):
        raise GateRejected("gate_archive_transformation_snapshot_invalid")
    stable_projection_root_sha256 = root(
        _summary_projection(pre_archive_partial)
    )
    if stable_projection_root_sha256 != root(
        _summary_projection(post_archive_partial)
    ):
        raise GateRejected("gate_archive_transformation_semantic_mismatch")
    transformation_core = {
        "schema": ARCHIVE_TRANSFORMATION_SCHEMA,
        "campaign_manifest_path": str(campaign_path),
        "campaign_manifest_root_sha256": campaign[
            "campaign_manifest_root_sha256"
        ],
        "terminal_checkpoint_chain_root_sha256": campaign[
            "terminal_checkpoint_chain_root_sha256"
        ],
        "pre_archive_partial_summary": {
            "path": str(pre_archive_snapshot_path),
            "bytes": len(pre_archive_raw),
            "sha256": hashlib.sha256(pre_archive_raw).hexdigest(),
            "checkpoint_root_sha256": checkpoint_preimage[
                "checkpoint_root_sha256"
            ],
        },
        "post_archive_partial_summary": {
            "path": str(post_archive_snapshot_path),
            "bytes": len(post_archive_raw),
            "sha256": hashlib.sha256(post_archive_raw).hexdigest(),
        },
        "allowed_top_level_changes": list(
            ARCHIVE_TRANSFORMATION_ALLOWED_TOP_LEVEL_KEYS
        ),
        "stable_projection_root_sha256": stable_projection_root_sha256,
    }
    return {
        **transformation_core,
        "transformation_root_sha256": root(transformation_core),
    }


def _golden_partial_from_authority(
    authority: Mapping[str, Any],
) -> tuple[dict[str, Any], Path, bytes]:
    manifest, _manifest_raw = _load_bound_json(
        Path(str(authority["golden_manifest_path"])),
        code="prospective_golden_manifest_invalid",
    )
    namespace = Path(str((manifest.get("namespace") or {}).get("path") or ""))
    partial_name = str(
        (manifest.get("partial_summary") or {}).get("name") or ""
    )
    partial_path = namespace / partial_name
    partial, partial_raw = _load_bound_json(
        partial_path,
        code="prospective_golden_partial_summary_invalid",
    )
    if hashlib.sha256(partial_raw).hexdigest() != (
        manifest.get("partial_summary") or {}
    ).get("sha256"):
        raise GateRejected("prospective_golden_partial_summary_invalid")
    return partial, partial_path, partial_raw


def no_replay_contract_preflight(
    *,
    prospective_golden_authority: Mapping[str, Any],
    current_shared_execution_contract: Mapping[str, Any],
    source_bundle_consumer_rebind_authority: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Fail before replay when economic equivalence is impossible."""

    authority = _validated_prospective_golden_authority(
        prospective_golden_authority
    )
    if set(authority) != PROSPECTIVE_GOLDEN_AUTHORITY_V2_KEYS:
        raise GateRejected("successor_golden_authority_required")
    golden_partial, _golden_path, golden_raw = _golden_partial_from_authority(
        authority
    )
    try:
        golden_split = split_shared_execution_contract(
            golden_partial["shared_execution_contract"]
        )
        current_split = split_shared_execution_contract(
            current_shared_execution_contract
        )
    except (KeyError, ContractSplitError):
        raise GateRejected("economic_execution_contract_invalid") from None
    expected_economic = authority[
        "economic_execution_contract_digest_sha256"
    ]
    if (
        golden_split["economic_execution_contract_digest_sha256"]
        != expected_economic
        or current_split["economic_execution_contract_digest_sha256"]
        != expected_economic
    ):
        raise GateRejected("economic_execution_contract_mismatch")
    bound_source_rebind = None
    if source_bundle_consumer_rebind_authority is not None:
        if type(source_bundle_consumer_rebind_authority) is not dict:
            raise GateRejected("source_consumer_rebind_authority_mismatch")
        bound_source_rebind = copy.deepcopy(
            dict(source_bundle_consumer_rebind_authority)
        )
        rebind_projection = dict(bound_source_rebind)
        rebind_root = rebind_projection.pop("binding_root_sha256", None)
        current_rebind = (
            (current_shared_execution_contract.get("execution_options") or {})
            .get("source_acceleration", {})
            .get("source_bundle_consumer_rebind_authority")
        )
        if (
            bound_source_rebind.get("schema")
            != (
                "gtos.replay_acceleration."
                "bound_source_bundle_consumer_rebind_authority.v1"
            )
            or rebind_root != root(rebind_projection)
            or bound_source_rebind.get("policy_execution_entered") is not False
            or bound_source_rebind.get("continuation_authorized") is not False
            or bound_source_rebind.get("broker_live_authority") is not False
            or bound_source_rebind.get("economic_values_exposed") is not False
            or current_rebind != bound_source_rebind
        ):
            raise GateRejected("source_consumer_rebind_authority_mismatch")
    core = {
        "schema": "gtos.replay_acceleration.no_replay_contract_preflight.v1",
        "gate": "LATEST_GOLDEN_ECONOMIC_CONTRACT_PREFLIGHT_ACCEPTED",
        "golden_manifest_file_sha256": authority[
            "golden_manifest_file_sha256"
        ],
        "successor_authority_root_sha256": authority[
            "successor_authority_root_sha256"
        ],
        "golden_partial_summary_sha256": hashlib.sha256(golden_raw).hexdigest(),
        "legacy_shared_execution_contract_digest_sha256": golden_partial[
            "shared_execution_contract"
        ]["shared_execution_contract_digest_sha256"],
        "current_shared_execution_contract_digest_sha256": (
            current_shared_execution_contract[
                "shared_execution_contract_digest_sha256"
            ]
        ),
        "economic_execution_contract_digest_sha256": expected_economic,
        "golden_effective_config_location_normalization_root_sha256": (
            golden_split[
                "effective_profile_config_location_normalization"
            ]["normalization_root_sha256"]
        ),
        "current_effective_config_location_normalization_root_sha256": (
            current_split[
                "effective_profile_config_location_normalization"
            ]["normalization_root_sha256"]
        ),
        "normalized_effective_profile_config_hashes_root_sha256": root(
            current_split["economic_execution_contract"][
                "effective_profile_config_hashes"
            ]
        ),
        "accelerator_implementation_authority_root_sha256": current_split[
            "accelerator_implementation_authority_root_sha256"
        ],
        "allowed_partial_summary_envelope_keys": list(
            ACCELERATION_ENVELOPE_ALLOWED_TOP_LEVEL_KEYS
        ),
        **(
            {
                "source_bundle_consumer_rebind_authority": (
                    bound_source_rebind
                )
            }
            if bound_source_rebind is not None
            else {}
        ),
        "policy_execution_entered": False,
        "economic_values_exposed": False,
        "continuation_authorized": False,
        "broker_live_authority": False,
    }
    return {**core, "preflight_root_sha256": root(core)}


def _binding_without_implementation_digest(
    value: Any,
) -> dict[str, Any]:
    if type(value) is not dict:
        raise GateRejected("acceleration_envelope_binding_invalid")
    projection = dict(value)
    projection.pop("actual_shared_execution_contract_digest_sha256", None)
    projection.pop("expected_shared_execution_contract_digest_sha256", None)
    return projection


def _is_absolute_lexical_path(value: Any) -> bool:
    if type(value) is not str or not value:
        return False
    path = Path(value)
    return path.is_absolute() and str(Path(os.path.abspath(value))) == value


def _is_nonnegative_number(value: Any) -> bool:
    return (
        type(value) in {int, float}
        and math.isfinite(float(value))
        and float(value) >= 0.0
    )


def _validate_bound_source_rebind(
    value: Any,
    *,
    source_plan_digest_sha256: str,
    source_bundle_root_sha256: str,
    selection_root_sha256: str,
) -> None:
    if type(value) is not dict or set(value) != SOURCE_REBIND_KEYS:
        raise GateRejected("acceleration_envelope_source_rebind_invalid")
    core = dict(value)
    binding_root = core.pop("binding_root_sha256", None)
    authority = value.get("authority")
    bundle = value.get("verified_successor_bundle")
    selection = value.get("verified_successor_selection")
    if (
        value.get("schema")
        != (
            "gtos.replay_acceleration."
            "bound_source_bundle_consumer_rebind_authority.v1"
        )
        or binding_root != root(core)
        or not is_sha256(value.get("authority_root_sha256"))
        or not is_sha256(value.get("authority_file_sha256"))
        or not _is_absolute_lexical_path(value.get("authority_path"))
        or value.get("source_plan_digest_sha256")
        != source_plan_digest_sha256
        or value.get("policy_execution_entered") is not False
        or value.get("continuation_authorized") is not False
        or value.get("broker_live_authority") is not False
        or value.get("economic_values_exposed") is not False
        or type(authority) is not dict
        or authority.get("authority_root_sha256")
        != value.get("authority_root_sha256")
        or authority.get("policy_execution_entered") is not False
        or authority.get("continuation_authorized") is not False
        or authority.get("broker_live_authority") is not False
        or authority.get("economic_values_exposed") is not False
        or type(bundle) is not dict
        or set(bundle)
        != {
            "path",
            "file_sha256",
            "bundle_root_sha256",
            "implementation_root_sha256",
        }
        or not _is_absolute_lexical_path(bundle.get("path"))
        or not is_sha256(bundle.get("file_sha256"))
        or not is_sha256(bundle.get("implementation_root_sha256"))
        or bundle.get("bundle_root_sha256")
        != source_bundle_root_sha256
        or type(selection) is not dict
        or set(selection)
        != {"path", "file_sha256", "selection_root_sha256"}
        or not _is_absolute_lexical_path(selection.get("path"))
        or not is_sha256(selection.get("file_sha256"))
        or selection.get("selection_root_sha256") != selection_root_sha256
    ):
        raise GateRejected("acceleration_envelope_source_rebind_invalid")


def _validate_runtime_evidence_contract(value: Any) -> None:
    if type(value) is not dict or set(value) != RUNTIME_EVIDENCE_CONTRACT_KEYS:
        raise GateRejected("acceleration_envelope_runtime_evidence_invalid")
    core = dict(value)
    contract_root = core.pop("contract_root_sha256", None)
    inputs = value.get("inputs")
    data_roots = value.get("data_roots")
    if (
        value.get("schema")
        != "gtos.replay_acceleration.runtime_evidence_root.v1"
        or contract_root != root(core)
        or not _is_absolute_lexical_path(value.get("root"))
        or value.get("integration_repo_root") != value.get("root")
        or type(data_roots) is not list
        or not data_roots
        or len(set(data_roots)) != len(data_roots)
        or any(not _is_absolute_lexical_path(path) for path in data_roots)
        or type(inputs) is not dict
        or set(inputs) != RUNTIME_EVIDENCE_INPUT_NAMES
        or value.get("legacy_evidence_mutation_enabled") is not False
        or value.get("read_only_existing_evidence") is not True
    ):
        raise GateRejected("acceleration_envelope_runtime_evidence_invalid")
    for name in sorted(RUNTIME_EVIDENCE_INPUT_NAMES):
        record = inputs[name]
        required = name in RUNTIME_EVIDENCE_REQUIRED_INPUT_NAMES
        expected_keys = (
            {
                "path",
                "present",
                "required_by_actual_replay_path",
                "bytes",
                "sha256",
            }
            if required
            else {"path", "present", "required_by_actual_replay_path"}
        )
        if (
            type(record) is not dict
            or set(record) != expected_keys
            or not _is_absolute_lexical_path(record.get("path"))
            or record.get("present") is not required
            or record.get("required_by_actual_replay_path") is not required
            or (
                required
                and (
                    type(record.get("bytes")) is not int
                    or record.get("bytes", 0) <= 0
                    or not is_sha256(record.get("sha256"))
                )
            )
        ):
            raise GateRejected(
                "acceleration_envelope_runtime_evidence_invalid"
            )


def _validate_source_acceleration_authority(
    value: Any,
    *,
    shared_execution_contract: Any,
    source_plan_digest_sha256: str,
) -> dict[str, Any]:
    execution_options = (
        shared_execution_contract.get("execution_options")
        if type(shared_execution_contract) is dict
        else None
    )
    shared = (
        execution_options.get("source_acceleration")
        if type(execution_options) is dict
        else None
    )
    if (
        type(shared) is not dict
        or set(shared) != SHARED_SOURCE_ACCELERATION_KEYS
        or type(value) is not dict
        or set(value) != SOURCE_ACCELERATION_AUTHORITY_KEYS
    ):
        raise GateRejected("acceleration_envelope_source_authority_invalid")
    stable_keys = SHARED_SOURCE_ACCELERATION_KEYS - {"prewarm_worker_count"}
    if any(value.get(key) != shared.get(key) for key in stable_keys):
        raise GateRejected("acceleration_envelope_source_authority_invalid")
    rebind = shared.get("source_bundle_consumer_rebind_authority")
    if (
        shared.get("schema")
        != "gtos.replay_acceleration.real_source_authority.v1"
        or shared.get("source_plan_digest_sha256")
        != source_plan_digest_sha256
        or any(
            not is_sha256(shared.get(key))
            for key in (
                "source_bundle_root_sha256",
                "selection_root_sha256",
                "source_plan_digest_sha256",
                "config_projection_root_sha256",
                "normalizer_code_root_sha256",
            )
        )
        or type(shared.get("partition_count")) is not int
        or shared.get("partition_count", 0) <= 0
        or type(shared.get("symbol_count")) is not int
        or shared.get("symbol_count", 0) <= 0
        or type(shared.get("prewarm_worker_count")) is not int
        or shared.get("prewarm_worker_count", 0) <= 0
        or shared.get("policy_execution_entered") is not False
        or shared.get("candidate_cache_enabled") is not False
        or shared.get("policy_state_cache_enabled") is not False
    ):
        raise GateRejected("acceleration_envelope_source_authority_invalid")
    _validate_bound_source_rebind(
        rebind,
        source_plan_digest_sha256=source_plan_digest_sha256,
        source_bundle_root_sha256=str(shared["source_bundle_root_sha256"]),
        selection_root_sha256=str(shared["selection_root_sha256"]),
    )
    barrier = value.get("cross_symbol_prewarm_barrier")
    metrics = value.get("typed_cache_metrics")
    if (
        type(barrier) is not dict
        or set(barrier) != SOURCE_PREWARM_BARRIER_KEYS
        or barrier.get("requested") is not True
        or barrier.get("barrier_complete") is not True
        or barrier.get("worker_count") != shared.get("prewarm_worker_count")
        or barrier.get("partition_count") != shared.get("partition_count")
        or not is_sha256(barrier.get("partition_set_root_sha256"))
        or not _is_nonnegative_number(barrier.get("seconds"))
        or not _is_nonnegative_number(value.get("bundle_validation_seconds"))
        or type(metrics) is not dict
        or set(metrics) != SOURCE_TYPED_CACHE_METRIC_KEYS
    ):
        raise GateRejected("acceleration_envelope_source_authority_invalid")
    for key in (
        "bytes_read",
        "bytes_written",
        "cold_partition_count",
        "normalized_row_count",
        "warm_partition_count",
    ):
        if type(metrics.get(key)) is not int or metrics.get(key, -1) < 0:
            raise GateRejected(
                "acceleration_envelope_source_authority_invalid"
            )
    for key in (
        "hashing_seconds",
        "normalization_seconds",
        "serialization_seconds",
        "verification_seconds",
    ):
        if not _is_nonnegative_number(metrics.get(key)):
            raise GateRejected(
                "acceleration_envelope_source_authority_invalid"
            )
    return shared


def _validate_tick_export_manifest_bytes(
    raw: bytes,
    *,
    expected_sha256: str,
    required_window_start_utc: str | None = None,
    required_window_end_utc: str | None = None,
    require_no_errors: bool = False,
) -> None:
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise GateRejected("acceleration_envelope_tick_manifest_invalid")
    try:
        manifest = json.loads(raw)
    except (UnicodeError, json.JSONDecodeError):
        raise GateRejected(
            "acceleration_envelope_tick_manifest_invalid"
        ) from None
    windows = manifest.get("windows") if type(manifest) is dict else None
    symbols = manifest.get("symbols") if type(manifest) is dict else None
    if (
        type(manifest) is not dict
        or set(manifest) != TICK_EXPORT_MANIFEST_KEYS
        or manifest.get("schema_version") != "mt5_research_tick_export_v1"
        or manifest.get("read_only") is not True
        or type(manifest.get("errors")) is not list
        or (require_no_errors and manifest.get("errors") != [])
        or any(
            type(row) is not dict
            or set(row) != {"error", "file_symbol", "mt5_symbol", "window"}
            or any(not str(row.get(key) or "") for key in row)
            for row in manifest.get("errors", [])
        )
        or type(manifest.get("account")) is not dict
        or type(manifest.get("terminal")) is not dict
        or type(manifest.get("source_provenance")) is not dict
        or type(manifest.get("files")) is not dict
        or not manifest.get("files")
        or not _is_nonnegative_number(manifest.get("chunk_minutes"))
        or float(manifest.get("chunk_minutes", 0.0)) <= 0.0
        or any(
            type(manifest.get(key)) is not str or not manifest.get(key)
            for key in (
                "created_at_utc",
                "label",
                "manifest_path",
                "mt5_client_kind",
                "output_dir",
            )
        )
        or type(symbols) is not list
        or not symbols
        or any(
            type(row) is not dict
            or set(row) != {"file_symbol", "mt5_symbol"}
            or not str(row.get("file_symbol") or "")
            or not str(row.get("mt5_symbol") or "")
            for row in symbols
        )
        or type(windows) is not list
        or not windows
        or any(
            type(row) is not dict
            or set(row) != {"start", "end", "label"}
            or type(row.get("start")) is not str
            or type(row.get("end")) is not str
            or type(row.get("label")) is not str
            or not row.get("label")
            or row.get("start", "") >= row.get("end", "")
            for row in windows
        )
    ):
        raise GateRejected("acceleration_envelope_tick_manifest_invalid")
    if (
        required_window_start_utc is not None
        and required_window_end_utc is not None
        and not any(
            row["start"] <= required_window_start_utc
            and row["end"] >= required_window_end_utc
            for row in windows
        )
    ):
        raise GateRejected("acceleration_envelope_tick_manifest_invalid")


def _validate_attempt5_execution_identity(
    identity: Any,
    *,
    partial: Mapping[str, Any],
    partial_path: Path,
    shared_source_authority: Mapping[str, Any],
    expected_output_prefix: str,
    expected_shared_execution_contract_sha256: str,
    expected_source_plan_digest_sha256: str,
    expected_arm_fingerprint_sha256: str,
    expected_prospective_golden_authority: Mapping[str, Any],
) -> None:
    if type(identity) is not dict or set(identity) != ATTEMPT5_EXECUTION_IDENTITY_KEYS:
        raise GateRejected("acceleration_envelope_identity_invalid")
    identity_core = dict(identity)
    identity_root = identity_core.pop("identity_root_sha256", None)
    if identity_root != root(identity_core):
        raise GateRejected("acceleration_envelope_identity_invalid")
    runner_path = identity.get("runner_path")
    shared_execution_contract = partial.get("shared_execution_contract")
    code_authority = (
        shared_execution_contract.get("code_authority")
        if type(shared_execution_contract) is dict
        else None
    )
    canonical_runner_path = Path(__file__).with_name(
        "replay_acceleration_attempt5_typed_sparse_runner.py"
    ).resolve()
    runner_sha256 = identity.get("runner_sha256")
    runner_rows = [
        row
        for row in (code_authority if type(code_authority) is list else ())
        if type(row) is dict
        and set(row) == {"path", "sha256"}
        and row.get("path") == ATTEMPT5_RUNNER_RELATIVE_PATH
        and row.get("sha256") == runner_sha256
    ]
    if (
        runner_path != str(canonical_runner_path)
        or not is_sha256(runner_sha256)
        or len(runner_rows) != 1
        or hashlib.sha256(
            _read_regular_file_nofollow(
                canonical_runner_path,
                code="acceleration_envelope_runner_invalid",
            )
        ).hexdigest()
        != runner_sha256
    ):
        raise GateRejected("acceleration_envelope_runner_invalid")
    tick_cache = identity.get("tick_sparse_cache")
    diagnostics = identity.get("tick_diagnostic_manifest_bindings")
    rebind = identity.get("source_bundle_consumer_rebind_authority")
    if (
        identity.get("schema")
        != "gtos.replay_acceleration.attempt5_typed_sparse_identity.v1"
        or identity.get("status")
        != "ATTEMPT5_TYPED_SPARSE_S0R0_JAN1_7_BOUND"
        or identity.get("arm_id") != "S0R0"
        or identity.get("start_day") != "2026-01-01"
        or identity.get("parity_day") != "2026-01-07"
        or identity.get("contract_end_day") != "2026-01-31"
        or identity.get("output_namespace") != str(partial_path.parent)
        or identity.get("output_prefix") != expected_output_prefix
        or partial.get("output_prefix") != expected_output_prefix
        or partial.get("route_id") != partial_path.parent.name
        or identity.get("prospective_golden_authority")
        != expected_prospective_golden_authority
        or identity.get("expected_shared_execution_contract_sha256")
        != expected_shared_execution_contract_sha256
        or identity.get("expected_source_plan_digest_sha256")
        != expected_source_plan_digest_sha256
        or identity.get("expected_arm_fingerprint_sha256")
        != expected_arm_fingerprint_sha256
        or identity.get("expected_source_bundle_root_sha256")
        != shared_source_authority.get("source_bundle_root_sha256")
        or not is_sha256(identity.get("expected_tick_source_manifest_sha256"))
        or identity.get("source_prewarm_workers")
        != shared_source_authority.get("prewarm_worker_count")
        or rebind
        != shared_source_authority.get(
            "source_bundle_consumer_rebind_authority"
        )
        or not _is_absolute_lexical_path(identity.get("tick_source_manifest"))
        or type(diagnostics) is not list
        or not diagnostics
        or len(
            {
                row.get("path")
                for row in diagnostics
                if type(row) is dict
            }
        )
        != len(diagnostics)
        or any(
            type(row) is not dict
            or set(row) != {"path", "sha256"}
            or not _is_absolute_lexical_path(row.get("path"))
            or not is_sha256(row.get("sha256"))
            for row in diagnostics
        )
        or type(tick_cache) is not dict
        or set(tick_cache)
        != {
            "schema",
            "root",
            "window_start_utc",
            "window_end_utc",
            "source_plan_or_replay_semantics_changed",
        }
        or tick_cache.get("schema")
        != "gtos.replay_acceleration.sparse_tick_window_cache.v1"
        or not _is_absolute_lexical_path(tick_cache.get("root"))
        or tick_cache.get("window_start_utc")
        != "2025-12-31T00:00:00+00:00"
        or tick_cache.get("window_end_utc")
        != "2026-01-09T00:00:00+00:00"
        or tick_cache.get("source_plan_or_replay_semantics_changed") is not False
        or identity.get("policy_execution_entered") is not False
        or identity.get("legacy_replay_route_invoked") is not False
        or identity.get("other_arms_launched") is not False
        or identity.get("broker_live_authority") is not False
        or identity.get("broker_mutation_enabled") is not False
        or identity.get("economic_values_exposed") is not False
    ):
        raise GateRejected("acceleration_envelope_identity_invalid")
    tick_manifest_path = Path(str(identity["tick_source_manifest"]))
    _validate_tick_export_manifest_bytes(
        _read_regular_file_nofollow(
            tick_manifest_path,
            code="acceleration_envelope_tick_manifest_invalid",
        ),
        expected_sha256=str(identity["expected_tick_source_manifest_sha256"]),
        required_window_start_utc=str(tick_cache["window_start_utc"]),
        required_window_end_utc=str(tick_cache["window_end_utc"]),
        require_no_errors=True,
    )
    for row in diagnostics:
        _validate_tick_export_manifest_bytes(
            _read_regular_file_nofollow(
                Path(str(row["path"])),
                code="acceleration_envelope_tick_manifest_invalid",
            ),
            expected_sha256=str(row["sha256"]),
        )


def _acceleration_stable_projection(
    value: Mapping[str, Any],
    *,
    partial_path: Path,
    expected_output_prefix: str | None,
    expected_prospective_golden_authority: Mapping[str, Any] | None,
    expected_shared_execution_contract_sha256: str | None,
    expected_source_plan_digest_sha256: str | None,
    expected_arm_fingerprint_sha256: str | None,
    archived_result_surface_roles: frozenset[str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    projection = copy.deepcopy(dict(value))
    runtime_fields: dict[str, Any] = {}

    is_accelerated = expected_shared_execution_contract_sha256 is not None
    identity = projection.get("attempt5_execution_identity")
    if not is_accelerated:
        if (
            identity is not None
            or projection.get("runtime_evidence_contract") is not None
            or projection.get("source_acceleration_authority") is not None
        ):
            raise GateRejected("acceleration_envelope_golden_authority_invalid")
    else:
        if (
            expected_output_prefix is None
            or expected_prospective_golden_authority is None
            or expected_source_plan_digest_sha256 is None
            or expected_arm_fingerprint_sha256 is None
            or "real_s0r0_parity_gate" not in projection
            or projection["real_s0r0_parity_gate"] is not None
        ):
            raise GateRejected("acceleration_envelope_prior_parity_gate_invalid")
        _validate_runtime_evidence_contract(
            projection.get("runtime_evidence_contract")
        )
        shared_source_authority = _validate_source_acceleration_authority(
            projection.get("source_acceleration_authority"),
            shared_execution_contract=projection.get(
                "shared_execution_contract"
            ),
            source_plan_digest_sha256=expected_source_plan_digest_sha256,
        )
        _validate_attempt5_execution_identity(
            identity,
            partial=projection,
            partial_path=partial_path,
            shared_source_authority=shared_source_authority,
            expected_output_prefix=expected_output_prefix,
            expected_shared_execution_contract_sha256=(
                expected_shared_execution_contract_sha256
            ),
            expected_source_plan_digest_sha256=(
                expected_source_plan_digest_sha256
            ),
            expected_arm_fingerprint_sha256=expected_arm_fingerprint_sha256,
            expected_prospective_golden_authority=(
                expected_prospective_golden_authority
            ),
        )

    capacity = projection.get("capacity_safe_chunk_execution_contract")
    if capacity is not None:
        if type(capacity) is not dict or type(capacity.get("checkpoints")) is not list:
            raise GateRejected("acceleration_envelope_gc_counter_invalid")
        gc_counters: list[dict[str, int]] = []
        for index, checkpoint in enumerate(capacity["checkpoints"]):
            if type(checkpoint) is not dict:
                raise GateRejected("acceleration_envelope_gc_counter_invalid")
            if "gc_collected_objects" not in checkpoint:
                continue
            observed = checkpoint["gc_collected_objects"]
            if type(observed) is not int or observed < 0:
                raise GateRejected("acceleration_envelope_gc_counter_invalid")
            gc_counters.append({"checkpoint_index": index, "value": observed})
            checkpoint["gc_collected_objects"] = 0
        runtime_fields[
            ACCELERATION_ENVELOPE_ALLOWED_NESTED_CHANGES[0]
        ] = gc_counters

    ledger_bytes = projection.get(
        "ledger_file_bytes_flushed_before_partial_summary"
    )
    if ledger_bytes is not None:
        if type(ledger_bytes) is not dict:
            raise GateRejected("acceleration_envelope_archive_bytes_invalid")
        for index, role in enumerate(("decision", "scorecard", "missed"), 1):
            if role not in ledger_bytes or role not in archived_result_surface_roles:
                continue
            observed = ledger_bytes[role]
            if type(observed) is not int or observed < 0:
                raise GateRejected("acceleration_envelope_archive_bytes_invalid")
            runtime_fields[
                ACCELERATION_ENVELOPE_ALLOWED_NESTED_CHANGES[index]
            ] = observed
            ledger_bytes[role] = 0

    ignored = {
        *ACCELERATION_ENVELOPE_ALLOWED_TOP_LEVEL_KEYS,
        *ARCHIVE_TRANSFORMATION_ALLOWED_TOP_LEVEL_KEYS,
    }
    return (
        {
            str(key): item
            for key, item in projection.items()
            if str(key) not in ignored
        },
        runtime_fields,
    )


def _partial_summary_acceleration_envelope_transformation(
    *,
    authority: Mapping[str, Any],
    accelerated_partial_path: Path,
    output_prefix: str,
    shared_execution_contract_sha256: str,
    economic_execution_contract_sha256: str,
    accelerator_implementation_authority_root_sha256: str,
    source_plan_digest_sha256: str,
    arm_fingerprint_sha256: str,
    archived_result_surface_roles: frozenset[str],
) -> dict[str, Any]:
    golden_partial, golden_path, golden_raw = _golden_partial_from_authority(
        authority
    )
    accelerated, accelerated_raw = _load_bound_json(
        accelerated_partial_path,
        code="accelerated_partial_summary_invalid",
    )
    try:
        golden_split = split_shared_execution_contract(
            golden_partial["shared_execution_contract"]
        )
        accelerated_split = split_shared_execution_contract(
            accelerated["shared_execution_contract"]
        )
    except (KeyError, ContractSplitError):
        raise GateRejected("acceleration_envelope_contract_invalid") from None
    if (
        golden_split["economic_execution_contract_digest_sha256"]
        != economic_execution_contract_sha256
        or accelerated_split["economic_execution_contract_digest_sha256"]
        != economic_execution_contract_sha256
        or accelerated["shared_execution_contract"].get(
            "shared_execution_contract_digest_sha256"
        )
        != shared_execution_contract_sha256
        or accelerated_split[
            "accelerator_implementation_authority_root_sha256"
        ]
        != accelerator_implementation_authority_root_sha256
        or _binding_without_implementation_digest(
            golden_partial.get("b7_5_contract_binding")
        )
        != _binding_without_implementation_digest(
            accelerated.get("b7_5_contract_binding")
        )
    ):
        raise GateRejected("acceleration_envelope_contract_mismatch")
    golden_projection, golden_runtime_fields = _acceleration_stable_projection(
        golden_partial,
        partial_path=golden_path,
        expected_output_prefix=None,
        expected_prospective_golden_authority=None,
        expected_shared_execution_contract_sha256=None,
        expected_source_plan_digest_sha256=None,
        expected_arm_fingerprint_sha256=None,
        archived_result_surface_roles=archived_result_surface_roles,
    )
    accelerated_projection, accelerated_runtime_fields = (
        _acceleration_stable_projection(
            accelerated,
            partial_path=accelerated_partial_path,
            expected_output_prefix=output_prefix,
            expected_prospective_golden_authority=authority,
            expected_shared_execution_contract_sha256=(
                shared_execution_contract_sha256
            ),
            expected_source_plan_digest_sha256=source_plan_digest_sha256,
            expected_arm_fingerprint_sha256=arm_fingerprint_sha256,
            archived_result_surface_roles=archived_result_surface_roles,
        )
    )
    stable_root = root(golden_projection)
    if stable_root != root(accelerated_projection):
        raise GateRejected("acceleration_envelope_semantic_mismatch")
    core = {
        "schema": ACCELERATION_ENVELOPE_TRANSFORMATION_SCHEMA,
        "golden_partial_summary": {
            "path": str(golden_path),
            "bytes": len(golden_raw),
            "sha256": hashlib.sha256(golden_raw).hexdigest(),
        },
        "accelerated_partial_summary": {
            "path": str(accelerated_partial_path),
            "bytes": len(accelerated_raw),
            "sha256": hashlib.sha256(accelerated_raw).hexdigest(),
        },
        "allowed_top_level_changes": list(
            ACCELERATION_ENVELOPE_ALLOWED_TOP_LEVEL_KEYS
        ),
        "allowed_nested_changes": list(
            ACCELERATION_ENVELOPE_ALLOWED_NESTED_CHANGES
        ),
        "golden_nested_runtime_fields_root_sha256": root(
            golden_runtime_fields
        ),
        "accelerated_nested_runtime_fields_root_sha256": root(
            accelerated_runtime_fields
        ),
        "stable_projection_root_sha256": stable_root,
        "legacy_shared_execution_contract_digest_sha256": golden_partial[
            "shared_execution_contract"
        ]["shared_execution_contract_digest_sha256"],
        "accelerated_shared_execution_contract_digest_sha256": (
            shared_execution_contract_sha256
        ),
        "economic_execution_contract_digest_sha256": (
            economic_execution_contract_sha256
        ),
        "accelerator_implementation_authority_root_sha256": (
            accelerator_implementation_authority_root_sha256
        ),
        "golden_envelope_root_sha256": root(
            {
                key: golden_partial.get(key)
                for key in ACCELERATION_ENVELOPE_ALLOWED_TOP_LEVEL_KEYS
            }
        ),
        "accelerated_envelope_root_sha256": root(
            {
                key: accelerated.get(key)
                for key in ACCELERATION_ENVELOPE_ALLOWED_TOP_LEVEL_KEYS
            }
        ),
        "economic_values_exposed": False,
    }
    return {**core, "transformation_root_sha256": root(core)}


def build_gate_request(
    *,
    output_prefix: str,
    outputs: Mapping[str, Path],
    ledger_row_counts: Mapping[str, int],
    completed_through_day: str,
    source_plan_digest_sha256: str,
    shared_execution_contract_sha256: str,
    arm_id: str,
    arm_fingerprint_sha256: str,
    prospective_golden_authority: Mapping[str, Any],
    economic_execution_contract_sha256: str | None = None,
    accelerator_implementation_authority_root_sha256: str | None = None,
    partial_summary_snapshot: Path | None = None,
    archived_result_surfaces: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    if arm_id != "S0R0" or completed_through_day != "2026-01-07":
        raise GateRejected("gate_scope_not_authorized")
    authority = _validated_prospective_golden_authority(
        prospective_golden_authority
    )
    is_successor = set(authority) == PROSPECTIVE_GOLDEN_AUTHORITY_V2_KEYS
    if is_successor != bool(
        economic_execution_contract_sha256
        and accelerator_implementation_authority_root_sha256
    ):
        raise GateRejected("gate_contract_split_authority_incomplete")
    try:
        output_paths = [
            Path(os.path.abspath(os.fspath(outputs[role])))
            for role in RESULT_ROLES
        ]
        output_paths.append(
            Path(os.path.abspath(os.fspath(outputs["partial_summary"])))
        )
    except KeyError:
        raise GateRejected("gate_surface_inventory_invalid") from None
    output_namespaces = {path.parent for path in output_paths}
    if len(output_namespaces) != 1:
        raise GateRejected("gate_output_namespace_mismatch")
    accelerated_namespace = next(iter(output_namespaces))
    surfaces: list[dict[str, Any]] = []
    archived = dict(archived_result_surfaces or {})
    if not set(archived).issubset({"decision", "scorecard", "missed"}):
        raise GateRejected("gate_archived_surface_inventory_invalid")
    for role in RESULT_ROLES:
        path = Path(outputs[role])
        if role in archived:
            record = dict(archived[role])
            expected = int(ledger_row_counts[role])
            try:
                archived_rows = int(record["rows"])
                archived_bytes = int(record["bytes"])
            except (KeyError, TypeError, ValueError):
                raise GateRejected("gate_archived_surface_invalid") from None
            if (
                record.get("role") != role
                or record.get("name") != path.name
                or record.get("storage") != "verified_zstd_campaign"
                or archived_rows != expected
                or archived_bytes < 0
                or len(str(record.get("sha256") or "")) != 64
                or not Path(
                    str(record.get("archive_campaign_manifest_path") or "")
                ).is_file()
                or len(
                    str(
                        record.get(
                            "archive_campaign_manifest_root_sha256"
                        )
                        or ""
                    )
                )
                != 64
            ):
                raise GateRejected("gate_archived_surface_invalid")
            hot_tombstone = file_contract(path, expected_rows=None)
            if hot_tombstone != EMPTY_SURFACE_CONTRACT:
                raise GateRejected("archived_hot_surface_not_empty")
            record["hot_tombstone"] = hot_tombstone
            surfaces.append(record)
            continue
        surfaces.append(
            {
                "role": role,
                "name": path.name,
                **file_contract(path, expected_rows=int(ledger_row_counts[role])),
            }
        )
    partial_path = Path(outputs["partial_summary"])
    partial_contract_path = partial_path
    if partial_summary_snapshot is not None:
        partial_contract_path = Path(partial_summary_snapshot)
        if partial_contract_path.exists() or partial_contract_path.is_symlink():
            raise GateRejected("gate_partial_snapshot_already_exists")
        partial_contract_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = partial_contract_path.with_name(
            f".{partial_contract_path.name}.{os.getpid()}.tmp"
        )
        try:
            with partial_path.open("rb") as source, temporary.open("xb") as target:
                shutil.copyfileobj(source, target, length=1024 * 1024)
                target.flush()
                os.fsync(target.fileno())
            os.replace(temporary, partial_contract_path)
        except OSError:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
            raise GateRejected("gate_partial_snapshot_write_failed") from None
    partial = file_contract(partial_contract_path, expected_rows=None)
    partial["name"] = partial_path.name
    partial["snapshot_path"] = str(partial_contract_path)
    archive_transformation = _partial_summary_archive_transformation(
        archived=archived,
        post_archive_snapshot_path=partial_contract_path,
    )
    acceleration_envelope_transformation = (
        _partial_summary_acceleration_envelope_transformation(
            authority=authority,
            accelerated_partial_path=partial_contract_path,
            output_prefix=str(output_prefix),
            shared_execution_contract_sha256=(
                shared_execution_contract_sha256
            ),
            economic_execution_contract_sha256=str(
                economic_execution_contract_sha256
            ),
            accelerator_implementation_authority_root_sha256=str(
                accelerator_implementation_authority_root_sha256
            ),
            source_plan_digest_sha256=source_plan_digest_sha256,
            arm_fingerprint_sha256=arm_fingerprint_sha256,
            archived_result_surface_roles=frozenset(archived),
        )
        if is_successor
        else None
    )
    request_core = {
        "schema": GATE_REQUEST_SCHEMA_V2 if is_successor else GATE_REQUEST_SCHEMA,
        "output_prefix": str(output_prefix),
        "accelerated_namespace_path": str(accelerated_namespace),
        "prospective_golden_authority": authority,
        "scope": {
            "start_day": "2026-01-01",
            "completed_through_day": completed_through_day,
            "day_count": 7,
            "arm_id": arm_id,
        },
        "source_plan_digest_sha256": source_plan_digest_sha256,
        "shared_execution_contract_sha256": shared_execution_contract_sha256,
        "arm_fingerprint_sha256": arm_fingerprint_sha256,
        "persisted_result_surfaces": surfaces,
        "partial_summary": partial,
        "partial_summary_archive_transformation": archive_transformation,
        **(
            {
                "economic_execution_contract_sha256": (
                    economic_execution_contract_sha256
                ),
                "accelerator_implementation_authority_root_sha256": (
                    accelerator_implementation_authority_root_sha256
                ),
                "partial_summary_acceleration_envelope_transformation": (
                    acceleration_envelope_transformation
                ),
            }
            if is_successor
            else {}
        ),
        "policy_execution_entered": True,
        "actual_run_campaign_path": True,
        "synthetic_reducer_harness": False,
        "candidate_cache_enabled": False,
        "policy_state_cache_enabled": False,
        "other_arms_launched": False,
        "live_broker_authority": False,
        "broker_mutation_enabled": False,
        "economic_values_exposed": False,
    }
    return {**request_core, "gate_request_root_sha256": root(request_core)}


def atomic_write_json(path: Path, value: Mapping[str, Any]) -> None:
    try:
        immutable_write_bytes(
            path,
            canonical_bytes(value) + b"\n",
            code="gate_request_write_failed",
        )
    except ImmutableEvidenceError:
        raise GateRejected("gate_request_write_failed") from None


def validate_parity_receipt(
    receipt: Mapping[str, Any],
    *,
    gate_request: Mapping[str, Any],
    parity_report: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    is_successor = gate_request.get("schema") == GATE_REQUEST_SCHEMA_V2
    if not isinstance(receipt, Mapping):
        raise GateRejected("parity_receipt_invalid")
    if receipt.get("receipt_root_sha256") != _self_root(
        receipt, "receipt_root_sha256"
    ):
        raise GateRejected("parity_receipt_self_root_mismatch")
    if (
        receipt.get("schema")
        != (PARITY_RECEIPT_SCHEMA_V2 if is_successor else PARITY_RECEIPT_SCHEMA)
        or receipt.get("status") != "EXACT_FULL_RESULT_PARITY_ACCEPTED"
        or receipt.get("parity_accepted") is not True
        or receipt.get("other_arms_launched") is not False
        or receipt.get("broker_live_authority") is not False
        or receipt.get("output_prefix") != gate_request.get("output_prefix")
        or receipt.get("completed_through_day") != "2026-01-07"
    ):
        raise GateRejected("parity_receipt_invalid")
    if receipt.get("gate_request_root_sha256") != gate_request.get(
        "gate_request_root_sha256"
    ):
        raise GateRejected("parity_receipt_request_mismatch")
    if parity_report is None:
        raise GateRejected("parity_report_required")
    if not isinstance(parity_report, Mapping):
        raise GateRejected("parity_report_invalid")
    report = dict(parity_report)
    request = dict(gate_request)
    request_projection = dict(request)
    request_root = request_projection.pop("gate_request_root_sha256", None)
    request_scope = request.get("scope")
    request_archive_transformation = request.get(
        "partial_summary_archive_transformation"
    )
    is_successor = request.get("schema") == GATE_REQUEST_SCHEMA_V2
    request_acceleration_transformation = request.get(
        "partial_summary_acceleration_envelope_transformation"
    )
    if request_archive_transformation is None:
        expected_archive_transformation_root = root(None)
    elif (
        isinstance(request_archive_transformation, Mapping)
        and is_sha256(
            request_archive_transformation.get("transformation_root_sha256")
        )
        and request_archive_transformation.get("transformation_root_sha256")
        == _self_root(
            request_archive_transformation,
            "transformation_root_sha256",
        )
    ):
        expected_archive_transformation_root = str(
            request_archive_transformation["transformation_root_sha256"]
        )
    else:
        raise GateRejected("parity_gate_request_invalid")
    if is_successor:
        if (
            not isinstance(request_acceleration_transformation, Mapping)
            or request_acceleration_transformation.get(
                "transformation_root_sha256"
            )
            != _self_root(
                request_acceleration_transformation,
                "transformation_root_sha256",
            )
        ):
            raise GateRejected("parity_gate_request_invalid")
        expected_acceleration_transformation_root = str(
            request_acceleration_transformation[
                "transformation_root_sha256"
            ]
        )
    else:
        expected_acceleration_transformation_root = root(None)
    try:
        bound_authority = _validated_prospective_golden_authority(
            request.get("prospective_golden_authority")
        )
    except GateRejected:
        raise GateRejected("parity_gate_request_invalid") from None
    accelerated_namespace_value = request.get("accelerated_namespace_path")
    if (
        set(request)
        != (GATE_REQUEST_V2_KEYS if is_successor else GATE_REQUEST_KEYS)
        or request.get("schema")
        not in {GATE_REQUEST_SCHEMA, GATE_REQUEST_SCHEMA_V2}
        or request_root != root(request_projection)
        or type(accelerated_namespace_value) is not str
        or not Path(str(accelerated_namespace_value)).is_absolute()
        or not Path(str(accelerated_namespace_value)).is_dir()
        or not isinstance(request_scope, Mapping)
        or request_scope
        != {
            "start_day": "2026-01-01",
            "completed_through_day": "2026-01-07",
            "day_count": 7,
            "arm_id": "S0R0",
        }
        or request.get("policy_execution_entered") is not True
        or request.get("actual_run_campaign_path") is not True
        or request.get("synthetic_reducer_harness") is not False
        or request.get("candidate_cache_enabled") is not False
        or request.get("policy_state_cache_enabled") is not False
        or request.get("other_arms_launched") is not False
        or request.get("live_broker_authority") is not False
        or request.get("broker_mutation_enabled") is not False
        or request.get("economic_values_exposed") is not False
        or not is_sha256(request.get("source_plan_digest_sha256"))
        or not is_sha256(request.get("shared_execution_contract_sha256"))
        or not is_sha256(request.get("arm_fingerprint_sha256"))
        or (
            is_successor
            and (
                not is_sha256(
                    request.get("economic_execution_contract_sha256")
                )
                or not is_sha256(
                    request.get(
                        "accelerator_implementation_authority_root_sha256"
                    )
                )
            )
        )
    ):
        raise GateRejected("parity_gate_request_invalid")
    if set(receipt) != (RECEIPT_V2_KEYS if is_successor else RECEIPT_KEYS):
        raise GateRejected("parity_receipt_invalid")
    if (
        set(report) != (REPORT_V2_KEYS if is_successor else REPORT_KEYS)
        or report.get("report_root_sha256") != _self_root(
            report, "report_root_sha256"
        )
        or report.get("schema")
        != (PARITY_REPORT_SCHEMA_V2 if is_successor else PARITY_REPORT_SCHEMA)
        or report.get("valid") is not True
        or report.get("gate") != "EXACT_FULL_RESULT_PARITY_ACCEPTED"
        or report.get("output_prefix") != request.get("output_prefix")
        or report.get("scope") != request_scope
        or report.get("gate_request_root_sha256") != request_root
        or report.get("all_persisted_ledger_bytes_equal") is not True
        or report.get("economic_values_exposed") is not False
        or report.get("independent_writer_imported") is not False
        or report.get("independent_runner_imported") is not False
        or report.get("other_arms_launched") is not False
        or report.get("broker_live_authority") is not False
    ):
        raise GateRejected("parity_report_invalid")

    contract_identity = report.get("contract_identity")
    if (
        not isinstance(contract_identity, Mapping)
        or set(contract_identity)
        != {
            "arm_id",
            "arm_fingerprint_sha256",
            "selection_factor",
            "sizing_factor",
            "selection_mode",
            "sizing_mode",
            "shared_execution_contract_digest_sha256",
            "source_plan_digest_sha256",
            *(("economic_execution_contract_digest_sha256",) if is_successor else ()),
        }
        or contract_identity.get("arm_id") != "S0R0"
        or contract_identity.get("selection_factor") != "S0"
        or contract_identity.get("sizing_factor") != "R0"
        or contract_identity.get("selection_mode")
        != "neutral_hash_hard_eligible"
        or contract_identity.get("sizing_mode") != "fixed_equal_account_risk"
        or contract_identity.get("arm_fingerprint_sha256")
        != request.get("arm_fingerprint_sha256")
        or (
            not is_successor
            and contract_identity.get(
                "shared_execution_contract_digest_sha256"
            )
            != request.get("shared_execution_contract_sha256")
        )
        or (
            is_successor
            and contract_identity.get(
                "economic_execution_contract_digest_sha256"
            )
            != request.get("economic_execution_contract_sha256")
        )
        or contract_identity.get("source_plan_digest_sha256")
        != request.get("source_plan_digest_sha256")
    ):
        raise GateRejected("parity_report_contract_identity_mismatch")

    surfaces = report.get("persisted_result_surfaces")
    if (
        not isinstance(surfaces, list)
        or [row.get("role") for row in surfaces if isinstance(row, Mapping)]
        != list(RESULT_ROLES)
        or any(
            not isinstance(row, Mapping)
            or set(row) != {"role", "bytes", "rows", "sha256"}
            or type(row.get("bytes")) is not int
            or type(row.get("rows")) is not int
            or row.get("bytes", -1) < 0
            or row.get("rows", -1) < 0
            or not is_sha256(row.get("sha256"))
            for row in surfaces
        )
        or report.get("persisted_result_surface_root_sha256") != root(surfaces)
    ):
        raise GateRejected("parity_report_surface_contract_invalid")
    request_surfaces = request.get("persisted_result_surfaces")
    if not isinstance(request_surfaces, list):
        raise GateRejected("parity_gate_request_invalid")
    request_has_archived_surfaces = any(
        isinstance(row, Mapping)
        and row.get("storage") == "verified_zstd_campaign"
        for row in request_surfaces
    )
    if request_has_archived_surfaces != isinstance(
        request_archive_transformation,
        Mapping,
    ):
        raise GateRejected("parity_gate_request_invalid")
    try:
        request_surface_projection = [
            {
                "role": row["role"],
                "bytes": row["bytes"],
                "rows": row["rows"],
                "sha256": row["sha256"],
            }
            for row in request_surfaces
        ]
    except (KeyError, TypeError):
        raise GateRejected("parity_gate_request_invalid") from None
    if request_surface_projection != surfaces:
        raise GateRejected("parity_report_surface_request_mismatch")

    archives = report.get("archive_campaign_verifications")
    if (
        not isinstance(archives, list)
        or any(
            not isinstance(row, Mapping)
            or set(row)
            != {
                "campaign_manifest_path",
                "campaign_manifest_sha256",
                "campaign_manifest_root_sha256",
                "verification_root_sha256",
                "verified_role_partitions_root_sha256",
            }
            or not str(row.get("campaign_manifest_path") or "")
            or any(
                not is_sha256(row.get(field))
                for field in (
                    "campaign_manifest_sha256",
                    "campaign_manifest_root_sha256",
                    "verification_root_sha256",
                    "verified_role_partitions_root_sha256",
                )
            )
            for row in archives
        )
        or report.get("archive_campaign_verification_set_root_sha256")
        != root(archives)
    ):
        raise GateRejected("parity_report_archive_contract_invalid")

    category_equality = report.get("semantic_category_equality")
    category_roots = report.get("semantic_category_roots")
    if (
        not isinstance(category_equality, Mapping)
        or set(category_equality) != CATEGORY_NAMES
        or any(value is not True for value in category_equality.values())
        or not isinstance(category_roots, Mapping)
        or set(category_roots) != CATEGORY_NAMES
        or any(
            not isinstance(value, Mapping)
            or set(value) != {"match_count", "root_sha256"}
            or type(value.get("match_count")) is not int
            or value.get("match_count", 0) < 1
            or not is_sha256(value.get("root_sha256"))
            for value in category_roots.values()
        )
    ):
        raise GateRejected("parity_report_semantic_contract_invalid")

    report_root_fields = (
        "persisted_result_surface_root_sha256",
        "partial_summary_semantic_root_sha256",
        "partial_summary_archive_transformation_root_sha256",
        "candidate_identity_union_root_sha256",
        "golden_manifest_sha256",
        "golden_manifest_self_root_sha256",
        "golden_root_sha256",
        "golden_amendment_sha256",
        "golden_amendment_self_root_sha256",
        "fixed_verifier_file_sha256",
        "partial_golden_verification_root_sha256",
        "gate_request_root_sha256",
        "archive_campaign_verification_set_root_sha256",
        "report_root_sha256",
    )
    receipt_root_fields = (
        "gate_request_root_sha256",
        "parity_report_root_sha256",
        "golden_manifest_sha256",
        "golden_manifest_self_root_sha256",
        "golden_root_sha256",
        "golden_amendment_sha256",
        "golden_amendment_self_root_sha256",
        "fixed_verifier_file_sha256",
        "partial_golden_verification_root_sha256",
        "persisted_result_surface_root_sha256",
        "partial_summary_semantic_root_sha256",
        "partial_summary_archive_transformation_root_sha256",
        "receipt_root_sha256",
        *(
            (
                "partial_summary_acceleration_envelope_transformation_root_sha256",
                "successor_authority_root_sha256",
                "successor_authority_verification_root_sha256",
                "economic_execution_contract_digest_sha256",
                "accelerated_shared_execution_contract_digest_sha256",
                "accelerator_implementation_authority_root_sha256",
                "fixed_verifier_code_authority_root_sha256",
            )
            if is_successor
            else ()
        ),
    )
    if (
        any(not is_sha256(report.get(field)) for field in report_root_fields)
        or any(not is_sha256(receipt.get(field)) for field in receipt_root_fields)
        or type(report.get("candidate_identity_union_count")) is not int
        or report.get("candidate_identity_union_count", -1) < 0
        or type(report.get("candidate_identity_missing_count")) is not int
        or report.get("candidate_identity_missing_count") != 0
        or receipt.get("parity_report_root_sha256")
        != report.get("report_root_sha256")
        or receipt.get("golden_manifest_sha256")
        != report.get("golden_manifest_sha256")
        or receipt.get("golden_manifest_self_root_sha256")
        != report.get("golden_manifest_self_root_sha256")
        or receipt.get("golden_root_sha256")
        != report.get("golden_root_sha256")
        or receipt.get("golden_amendment_sha256")
        != report.get("golden_amendment_sha256")
        or receipt.get("golden_amendment_self_root_sha256")
        != report.get("golden_amendment_self_root_sha256")
        or receipt.get("fixed_verifier_file_sha256")
        != report.get("fixed_verifier_file_sha256")
        or report.get("golden_manifest_sha256")
        != bound_authority["golden_manifest_file_sha256"]
        or report.get("golden_manifest_self_root_sha256")
        != bound_authority["golden_manifest_self_root_sha256"]
        or report.get("golden_root_sha256")
        != bound_authority["golden_root_sha256"]
        or report.get("golden_amendment_sha256")
        != bound_authority["golden_amendment_file_sha256"]
        or report.get("golden_amendment_self_root_sha256")
        != bound_authority["golden_amendment_self_root_sha256"]
        or report.get("fixed_verifier_file_sha256")
        != bound_authority["fixed_verifier_file_sha256"]
        or receipt.get("partial_golden_verification_root_sha256")
        != report.get("partial_golden_verification_root_sha256")
        or receipt.get("persisted_result_surface_root_sha256")
        != report.get("persisted_result_surface_root_sha256")
        or receipt.get("partial_summary_semantic_root_sha256")
        != report.get("partial_summary_semantic_root_sha256")
        or report.get(
            "partial_summary_archive_transformation_root_sha256"
        )
        != expected_archive_transformation_root
        or receipt.get(
            "partial_summary_archive_transformation_root_sha256"
        )
        != report.get(
            "partial_summary_archive_transformation_root_sha256"
        )
        or receipt.get("accelerated_s0r0_research_route_authorized") is not True
        or receipt.get(
            "same_state_continuation_through_2026_01_31_authorized"
        )
        is not True
        or receipt.get("economic_values_exposed") is not False
        or (
            is_successor
            and (
                report.get(
                    "partial_summary_acceleration_envelope_transformation_root_sha256"
                )
                != expected_acceleration_transformation_root
                or receipt.get(
                    "partial_summary_acceleration_envelope_transformation_root_sha256"
                )
                != expected_acceleration_transformation_root
                or report.get("successor_authority_root_sha256")
                != bound_authority["successor_authority_root_sha256"]
                or receipt.get("successor_authority_root_sha256")
                != report.get("successor_authority_root_sha256")
                or report.get(
                    "successor_authority_verification_root_sha256"
                )
                != bound_authority[
                    "successor_authority_verification_root_sha256"
                ]
                or receipt.get(
                    "successor_authority_verification_root_sha256"
                )
                != report.get(
                    "successor_authority_verification_root_sha256"
                )
                or report.get("economic_execution_contract_digest_sha256")
                != request.get("economic_execution_contract_sha256")
                or receipt.get("economic_execution_contract_digest_sha256")
                != report.get("economic_execution_contract_digest_sha256")
                or report.get(
                    "accelerated_shared_execution_contract_digest_sha256"
                )
                != request.get("shared_execution_contract_sha256")
                or receipt.get(
                    "accelerated_shared_execution_contract_digest_sha256"
                )
                != report.get(
                    "accelerated_shared_execution_contract_digest_sha256"
                )
                or report.get(
                    "accelerator_implementation_authority_root_sha256"
                )
                != request.get(
                    "accelerator_implementation_authority_root_sha256"
                )
                or receipt.get(
                    "accelerator_implementation_authority_root_sha256"
                )
                != report.get(
                    "accelerator_implementation_authority_root_sha256"
                )
                or report.get("fixed_verifier_code_authority_root_sha256")
                != bound_authority[
                    "fixed_verifier_code_authority_root_sha256"
                ]
                or receipt.get("fixed_verifier_code_authority_root_sha256")
                != report.get("fixed_verifier_code_authority_root_sha256")
            )
        )
    ):
        raise GateRejected("parity_receipt_report_mismatch")
    code_identities = None
    try:
        if is_successor:
            code_identities = validate_fixed_verifier_code_authority(
                bound_authority["fixed_verifier_code_authority"],
                module_directory=Path(__file__).parent,
            )
        from src.research_infra import (
            replay_acceleration_real_parity_verifier as fixed_verifier,
        )

        recomputed_report, recomputed_receipt = fixed_verifier.verify_real_parity(
            golden_manifest_path=Path(
                str(bound_authority["golden_manifest_path"])
            ),
            accelerated_namespace=Path(str(accelerated_namespace_value)),
            gate_request=request,
        )
        if code_identities is not None:
            assert_fixed_verifier_code_identity(code_identities)
            validate_fixed_verifier_code_authority(
                bound_authority["fixed_verifier_code_authority"],
                module_directory=Path(__file__).parent,
            )
    except Exception:
        raise GateRejected("parity_verifier_recompute_failed") from None
    if (
        canonical_bytes(recomputed_report) != canonical_bytes(report)
        or canonical_bytes(recomputed_receipt) != canonical_bytes(receipt)
    ):
        raise GateRejected("parity_verifier_recompute_mismatch")
    return dict(receipt)


def wait_for_parity_receipt(
    *,
    receipt_path: Path,
    report_path: Path,
    gate_request: Mapping[str, Any],
    timeout_seconds: int,
    poll_seconds: float = 1.0,
) -> dict[str, Any]:
    deadline = time.monotonic() + int(timeout_seconds)
    receipt_path = Path(receipt_path)
    report_path = Path(report_path)
    while time.monotonic() < deadline:
        if receipt_path.is_symlink() or report_path.is_symlink():
            raise GateRejected("parity_evidence_symlink_forbidden")
        if receipt_path.is_file() and report_path.is_file():
            receipt_raw = _read_regular_file_nofollow(
                receipt_path,
                code="parity_evidence_invalid",
            )
            report_raw = _read_regular_file_nofollow(
                report_path,
                code="parity_evidence_invalid",
            )
            try:
                receipt = json.loads(receipt_raw)
                report = json.loads(report_raw)
            except (UnicodeError, json.JSONDecodeError):
                raise GateRejected("parity_evidence_invalid") from None
            if receipt_raw != canonical_bytes(receipt) + b"\n":
                raise GateRejected("parity_receipt_not_canonical")
            if report_raw != canonical_bytes(report) + b"\n":
                raise GateRejected("parity_report_not_canonical")
            return validate_parity_receipt(
                receipt,
                gate_request=gate_request,
                parity_report=report,
            )
        time.sleep(max(0.05, float(poll_seconds)))
    raise GateRejected("parity_receipt_timeout")


__all__ = [
    "GateRejected",
    "atomic_write_json",
    "build_gate_request",
    "validate_parity_receipt",
    "validate_prospective_golden_authority",
    "wait_for_parity_receipt",
]
