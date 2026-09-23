#!/usr/bin/env python3
"""Verify Task 3 campaign-cache parity and measured end-to-end improvement.

This verifier compares the authenticated pre-cache Task 2 Jan 1-2 execution
with one cache-enabled execution of the identical workload.  It does not
reopen Task 2's historical-golden authority.  Every causal/economic ledger,
candidate row, and state checkpoint remains exact; only explicitly named
runtime-clock-derived proof hashes may normalize after both preimages are
independently recomputed.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from src.research_infra import (
    replay_acceleration_task2_semantic_acceptance as semantic,
)
from src.research_infra.replay_acceleration_contract_split import (
    ContractSplitError,
    split_shared_execution_contract,
)
from src.research_infra.replay_acceleration_source_rebind_successor import (
    SourceRebindRejected,
    validate_independent_verifier_envelope,
)


SCHEMA = "gtos.replay_acceleration.task3_campaign_exact_cache_acceptance.v1"
STATUS = "TASK3_CAMPAIGN_EXACT_CACHE_SEMANTIC_AND_PERFORMANCE_VERIFIED"
END_DAY = "2026-01-02"
HASH_SENTINEL = "<TASK3_RUNTIME_DERIVED_HASH>"
TIME_SENTINEL = "<TASK3_NONCAUSAL_RUNTIME_CLOCK>"

_ORDER_PREIMAGE_HASH_PATHS = frozenset(
    {
        ("final_producer_order_row_sha256",),
        ("owner", "payload_root_sha256"),
        ("persisted_order_row_sha256",),
        ("pre_normalization_producer_order_row_sha256",),
        ("producer_order_row_sha256",),
        ("semantic_execution_manager_packet_sha256",),
        ("semantic_order_preimage_id",),
        ("sidecar_payload_sha256",),
    }
)
_PAYLOAD_WALL_CLOCK_PATHS = frozenset(
    {
        ("execution_manager_packet", "generated_at_utc"),
        (
            "execution_manager_packet",
            "broker_order_lifecycle_capture_v4",
            "generated_at_utc",
        ),
    }
)
_PAYLOAD_DIRECT_HASH_PATHS = frozenset(
    {
        (
            "broker_order_lifecycle_capture_v4_packet",
            "packet_hash_sha256",
        ),
        (
            "broker_order_lifecycle_capture_v4_packet",
            "pre_order_capture_contract",
            "execution_manager_packet_hash",
        ),
    }
)
_EXPOSURE_HASH_TAILS = frozenset(
    {
        ("broker_order_lifecycle_capture_v4_packet", "packet_hash_sha256"),
        (
            "broker_order_lifecycle_capture_v4_packet",
            "pre_order_capture_contract",
            "execution_manager_packet_hash",
        ),
    }
)
_CACHE_KEYS = frozenset(
    {
        "schema",
        "status",
        "config_root_sha256",
        "risk_profile_path",
        "risk_profile_sha256",
        "expected_risk_profile_sha256",
        "risk_profile_payload_root_sha256",
        "miss_counts",
        "cached_symbol_counts",
        "live_broker_authority",
        "broker_mutation_enabled",
    }
)
_SOURCE_AUTHORITY_FIELDS = frozenset(
    {
        "bundle_validation_seconds",
        "candidate_cache_enabled",
        "config_projection_root_sha256",
        "cross_symbol_prewarm_barrier",
        "normalizer_code_root_sha256",
        "partition_count",
        "policy_execution_entered",
        "policy_state_cache_enabled",
        "schema",
        "selection_root_sha256",
        "source_bundle_consumer_rebind_authority",
        "source_bundle_root_sha256",
        "source_plan_digest_sha256",
        "symbol_count",
        "typed_cache_metrics",
    }
)
_SHARED_SOURCE_FIELDS = frozenset(
    {
        "candidate_cache_enabled",
        "config_projection_root_sha256",
        "normalizer_code_root_sha256",
        "partition_count",
        "policy_execution_entered",
        "policy_state_cache_enabled",
        "prewarm_worker_count",
        "schema",
        "selection_root_sha256",
        "source_bundle_consumer_rebind_authority",
        "source_bundle_root_sha256",
        "source_plan_digest_sha256",
        "symbol_count",
    }
)
_SOURCE_BARRIER_FIELDS = frozenset(
    {
        "barrier_complete",
        "partition_count",
        "partition_set_root_sha256",
        "requested",
        "seconds",
        "worker_count",
    }
)
_SOURCE_METRIC_FIELDS = frozenset(
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
_BOUND_REBIND_FIELDS = frozenset(
    {
        "authority",
        "authority_file_sha256",
        "authority_path",
        "authority_root_sha256",
        "binding_root_sha256",
        "broker_live_authority",
        "continuation_authorized",
        "economic_values_exposed",
        "policy_execution_entered",
        "schema",
        "source_plan_digest_sha256",
        "verified_successor_bundle",
        "verified_successor_selection",
    }
)
_SOURCE_REBIND_AUTHORITY_FIELDS = frozenset(
    {
        "authority_root_sha256",
        "broker_live_authority",
        "bundle_transformation",
        "continuation_authorized",
        "economic_values_exposed",
        "fresh_cold_runs",
        "independent_verifiers",
        "policy_execution_entered",
        "predecessor_bundle",
        "predecessor_selection",
        "reason",
        "schema",
        "selection_transformation",
        "status",
        "successor_bundle",
        "successor_selection",
    }
)
_INDEPENDENT_VERIFIER_ROW_FIELDS = frozenset(
    {
        "envelope_root_sha256",
        "logical_recomputed_root_sha256",
        "path",
        "physical_recomputed_root_sha256",
        "receipt_file_sha256",
        "sha256",
    }
)
_EXPECTED_CACHE_ROWS = (
    {
        "day": "2026-01-01",
        "miss_counts": {"scheduler_config": 1},
        "cached_symbol_counts": {
            "risk_pct": 0,
            "risk_limits": 0,
            "replay_symbol_config": 0,
            "broker_symbol_config": 0,
        },
    },
    {
        "day": "2026-01-02",
        "miss_counts": {
            "broker_symbol_config": 24,
            "replay_symbol_config": 24,
            "risk_limits": 25,
            "risk_pct": 25,
            "scheduler_config": 1,
            "typed_scheduler_config": 1,
        },
        "cached_symbol_counts": {
            "risk_pct": 25,
            "risk_limits": 25,
            "replay_symbol_config": 24,
            "broker_symbol_config": 24,
        },
    },
)
_SPARSE_PREWARM_KEYS = frozenset(
    {
        "broker_live_authority",
        "cache_precondition_measurement",
        "cache_root",
        "cache_schema",
        "economic_values_exposed",
        "entries",
        "entry_count",
        "non_authoritative_filesystem_storage_receipt",
        "partition_count",
        "prewarm_root_sha256",
        "raw_source_full_hash_count",
        "retained_row_count",
        "schema",
        "sealed_cache_reuse_count",
        "status",
        "window_end_utc",
        "window_start_utc",
        "worker_count",
    }
)
_SPARSE_PREWARM_ENTRY_KEYS = frozenset(
    {
        "identity_root_sha256",
        "manifest_root_sha256",
        "partition_count",
        "raw_source_full_hash_performed",
        "retained_row_count",
        "sealed_cache_reused",
        "source_path",
        "source_sha256",
        "source_validation",
        "symbol",
    }
)
_SPARSE_SOURCE_VALIDATION_KEYS = frozenset(
    {
        "manifest_sha256",
        "path",
        "raw_source_full_hash_performed",
        "sha_validation_status",
        "source_stat_identity",
        "status",
    }
)
_SPARSE_STORAGE_KEYS = frozenset(
    {
        "authoritative",
        "entries",
        "included_in_prewarm_root_sha256",
        "schema",
        "status",
    }
)
_SPARSE_STORAGE_ENTRY_KEYS = frozenset(
    {"partitions", "source_path", "source_sha256", "symbol"}
)
_SPARSE_SOURCE_STAT_KEYS = frozenset(
    {"device", "inode", "byte_count", "mtime_ns", "ctime_ns"}
)
_SPARSE_IDENTITY_KEYS = frozenset(
    {
        "builder_implementation_root_sha256",
        "builder_path",
        "declared_source_row_count",
        "row_semantics",
        "schema",
        "source_path",
        "source_sha256",
        "source_stat_identity",
        "symbol",
        "window_end_utc",
        "window_start_utc",
    }
)
_SPARSE_MANIFEST_KEYS = frozenset(
    {
        "broker_live_authority",
        "economic_values_exposed",
        "identity",
        "identity_root_sha256",
        "manifest_root_sha256",
        "partition_count",
        "partitions",
        "retained_row_count",
        "schema",
        "source_rows_scanned_through_window_end",
        "source_validation",
        "status",
    }
)
_SPARSE_MANIFEST_SOURCE_VALIDATION_KEYS = frozenset(
    {"source_sha256", "source_stat_identity", "status"}
)
_SPARSE_PARTITION_KEYS = frozenset(
    {"bytes", "day", "path", "rows", "sha256"}
)
_SPARSE_ROW_SEMANTICS = (
    "original_json_payload_with_legacy_time_time_utc_symbol_normalization"
)


class Task3ExactCacheRejected(RuntimeError):
    """The Task 3 implementation or evidence failed closed."""


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise Task3ExactCacheRejected(code)


def _require_exact_mapping_keys(
    value: Any,
    expected: frozenset[str],
    code: str,
) -> Mapping[str, Any]:
    _require(isinstance(value, Mapping) and set(value) == expected, code)
    return value


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(Path(path).read_bytes())
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise Task3ExactCacheRejected("task3_json_invalid") from None
    _require(type(payload) is dict, "task3_json_invalid")
    return payload


def _rows(path: Path) -> list[dict[str, Any]]:
    try:
        rows = list(semantic.iter_jsonl(path))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        raise Task3ExactCacheRejected("task3_jsonl_invalid") from None
    _require(all(type(row) is dict for row in rows), "task3_jsonl_invalid")
    return rows


def _is_exposure_hash_path(path: tuple[str, ...]) -> bool:
    prefix = (
        "execution_manager_packet",
        "scheduler_v4",
        "packet",
        "exposure_snapshot",
        "open_positions",
    )
    if (
        len(path) <= len(prefix) + 2
        or path[: len(prefix)] != prefix
        or not path[len(prefix)].isdigit()
    ):
        return False
    remainder = path[len(prefix) + 1 :]
    return remainder[0] == "metadata" and remainder[1:] in _EXPOSURE_HASH_TAILS


def _payload_difference_class(path: tuple[str, ...]) -> str | None:
    if path in _PAYLOAD_WALL_CLOCK_PATHS:
        return "wall_clock_timestamp"
    if path in _PAYLOAD_DIRECT_HASH_PATHS or _is_exposure_hash_path(path):
        return "derived_hash"
    return None


def project_order_preimage_payload_pair(
    reference: Mapping[str, Any],
    accelerated: Mapping[str, Any],
    *,
    reference_hashes_by_exposure: Mapping[str, tuple[str, str]],
    accelerated_hashes_by_exposure: Mapping[str, tuple[str, str]],
) -> tuple[dict[str, Any], Counter[str]]:
    """Normalize only the finite Task 3 runtime-clock proof closure."""

    left = copy.deepcopy(dict(reference))
    right = copy.deepcopy(dict(accelerated))
    observed: Counter[str] = Counter()
    for path in semantic._difference_paths(reference, accelerated):
        value_class = _payload_difference_class(path)
        if value_class is None:
            raise Task3ExactCacheRejected(
                "task3_order_preimage_semantic_mismatch:" + "/".join(path)
            )
        left_value = semantic._path_value(reference, path)
        right_value = semantic._path_value(accelerated, path)
        if value_class == "wall_clock_timestamp":
            _require(
                semantic._is_utc_timestamp(left_value)
                and semantic._is_utc_timestamp(right_value),
                "task3_order_preimage_runtime_clock_invalid",
            )
            replacement = TIME_SENTINEL
        else:
            _require(
                semantic._is_sha256(left_value)
                and semantic._is_sha256(right_value),
                "task3_order_preimage_hash_invalid",
            )
            if _is_exposure_hash_path(path):
                execution_hash = path[-1] == "execution_manager_packet_hash"
                position_path = path[: path.index("metadata")]
                reference_position = semantic._path_value(
                    reference, position_path
                )
                accelerated_position = semantic._path_value(
                    accelerated, position_path
                )
                _require(
                    isinstance(reference_position, Mapping)
                    and isinstance(accelerated_position, Mapping)
                    and reference_position.get("exposure_id")
                    == accelerated_position.get("exposure_id")
                    and type(reference_position.get("exposure_id")) is str,
                    "task3_exposure_identity_invalid",
                )
                exposure_id = str(reference_position["exposure_id"])
                reference_pair = reference_hashes_by_exposure.get(exposure_id)
                accelerated_pair = accelerated_hashes_by_exposure.get(exposure_id)
                pair_index = 1 if execution_hash else 0
                _require(
                    reference_pair is not None
                    and accelerated_pair is not None
                    and left_value == reference_pair[pair_index]
                    and right_value == accelerated_pair[pair_index],
                    "task3_exposure_hash_alias_unbound",
                )
            replacement = HASH_SENTINEL
        semantic._set_path(left, path, replacement)
        semantic._set_path(right, path, replacement)
        observed["/".join(path)] += 1
    _require(
        semantic.canonical_bytes(left) == semantic.canonical_bytes(right),
        "task3_order_preimage_projection_mismatch",
    )
    return left, observed


def _selected_identity_keys(root: Path) -> set[str]:
    keys = {
        semantic._identity_key(row, label="task3:selected_order")
        for row in semantic._role_rows(root, "order")
    }
    _require(bool(keys), "task3_selected_identity_empty")
    return keys


def _lifecycle_hashes_by_exposure(
    root: Path,
) -> dict[str, tuple[str, str]]:
    order_hashes: dict[str, tuple[str, str]] = {}
    for row in semantic._role_rows(root, "order"):
        order_id = row.get("simulated_order_id")
        packet = row.get("broker_order_lifecycle_capture_v4_packet")
        _require(isinstance(packet, Mapping), "task3_lifecycle_packet_missing")
        packet_hash = packet.get("packet_hash_sha256")
        pre_order = packet.get("pre_order_capture_contract")
        execution_hash = (
            pre_order.get("execution_manager_packet_hash")
            if isinstance(pre_order, Mapping)
            else None
        )
        _require(
            semantic._is_sha256(packet_hash)
            and semantic._is_sha256(execution_hash),
            "task3_lifecycle_hash_invalid",
        )
        _require(type(order_id) is str and bool(order_id), "task3_order_id_invalid")
        pair = (str(packet_hash), str(execution_hash))
        previous = order_hashes.setdefault(order_id, pair)
        _require(previous == pair, "task3_order_lifecycle_alias_conflict")
    by_exposure = dict(order_hashes)
    for row in semantic._role_rows(root, "trade"):
        trade_id = row.get("simulated_trade_id")
        order_id = row.get("simulated_order_id")
        _require(
            type(trade_id) is str
            and bool(trade_id)
            and type(order_id) is str
            and order_id in order_hashes,
            "task3_trade_order_lineage_invalid",
        )
        pair = order_hashes[order_id]
        previous = by_exposure.setdefault(trade_id, pair)
        _require(previous == pair, "task3_trade_lifecycle_alias_conflict")
    return by_exposure


def compare_order_preimages(
    reference_root: Path,
    accelerated_root: Path,
) -> dict[str, Any]:
    reference_keys = _selected_identity_keys(reference_root)
    accelerated_keys = _selected_identity_keys(accelerated_root)
    _require(reference_keys == accelerated_keys, "task3_selected_identity_mismatch")
    reference_validation = semantic._validate_selected_order_preimages(
        reference_root,
        end_day=END_DAY,
        exact_scope=True,
        required=True,
        required_candidate_keys=reference_keys,
    )
    accelerated_validation = semantic._validate_selected_order_preimages(
        accelerated_root,
        end_day=END_DAY,
        exact_scope=True,
        required=True,
        required_candidate_keys=accelerated_keys,
    )
    reference_rows = _rows(
        semantic._semantic_paths(reference_root)["order_preimage"]
    )
    accelerated_rows = _rows(
        semantic._semantic_paths(accelerated_root)["order_preimage"]
    )
    _require(
        len(reference_rows) == len(accelerated_rows) == len(reference_keys),
        "task3_order_preimage_row_count_mismatch",
    )
    reference_hashes_by_exposure = _lifecycle_hashes_by_exposure(reference_root)
    accelerated_hashes_by_exposure = _lifecycle_hashes_by_exposure(
        accelerated_root
    )
    _require(
        set(reference_hashes_by_exposure)
        == set(accelerated_hashes_by_exposure),
        "task3_exposure_lineage_set_mismatch",
    )
    observed: Counter[str] = Counter()
    projected_rows: list[dict[str, Any]] = []
    for index, (reference_row, accelerated_row) in enumerate(
        zip(reference_rows, accelerated_rows)
    ):
        reference_payload = json.loads(
            str(reference_row["sidecar_payload_canonical_json"])
        )
        accelerated_payload = json.loads(
            str(accelerated_row["sidecar_payload_canonical_json"])
        )
        projected_payload, payload_observed = project_order_preimage_payload_pair(
            reference_payload,
            accelerated_payload,
            reference_hashes_by_exposure=reference_hashes_by_exposure,
            accelerated_hashes_by_exposure=accelerated_hashes_by_exposure,
        )
        observed.update(payload_observed)
        left = copy.deepcopy(reference_row)
        right = copy.deepcopy(accelerated_row)
        left["sidecar_payload_canonical_json"] = projected_payload
        right["sidecar_payload_canonical_json"] = projected_payload
        for path in semantic._difference_paths(left, right):
            _require(
                path in _ORDER_PREIMAGE_HASH_PATHS,
                "task3_order_preimage_row_mismatch:" + "/".join(path),
            )
            left_value = semantic._path_value(left, path)
            right_value = semantic._path_value(right, path)
            _require(
                semantic._is_sha256(left_value)
                and semantic._is_sha256(right_value),
                "task3_order_preimage_row_hash_invalid",
            )
            semantic._set_path(left, path, HASH_SENTINEL)
            semantic._set_path(right, path, HASH_SENTINEL)
            observed["/".join(path)] += 1
        _require(
            semantic.canonical_bytes(left) == semantic.canonical_bytes(right),
            f"task3_order_preimage_row_projection_mismatch:{index}",
        )
        projected_rows.append(left)
    return {
        "status": "TASK3_ORDER_PREIMAGES_SEMANTICALLY_EQUIVALENT",
        "row_count": len(projected_rows),
        "selected_identity_root_sha256": reference_validation[
            "selected_identity_root_sha256"
        ],
        "reference_preimage_validation": reference_validation,
        "accelerated_preimage_validation": accelerated_validation,
        "observed_allowlisted_paths": dict(sorted(observed.items())),
        "projection_root_sha256": semantic.canonical_sha256(projected_rows),
        "meaningful_difference_count": 0,
        "unknown_difference_count": 0,
    }


def validate_cache_audits(summary: Mapping[str, Any]) -> dict[str, Any]:
    progress = summary.get("progress_rows")
    _require(
        isinstance(progress, list) and len(progress) == len(_EXPECTED_CACHE_ROWS),
        "task3_cache_progress_invalid",
    )
    config_roots: set[str] = set()
    risk_roots: set[str] = set()
    risk_payload_roots: set[str] = set()
    rows: list[dict[str, Any]] = []
    for row, expected in zip(progress, _EXPECTED_CACHE_ROWS):
        _require(isinstance(row, Mapping), "task3_cache_progress_invalid")
        audit = row.get("campaign_exact_cache")
        _require(
            isinstance(audit, Mapping)
            and set(audit) == _CACHE_KEYS
            and row.get("start_day") == expected["day"]
            and row.get("end_day") == expected["day"]
            and audit.get("schema")
            == "gtos.replay_acceleration.campaign_exact_cache.v1"
            and audit.get("status") == "exact_cache_boundary_valid"
            and audit.get("live_broker_authority") is False
            and audit.get("broker_mutation_enabled") is False
            and semantic._is_sha256(audit.get("config_root_sha256"))
            and semantic._is_sha256(audit.get("risk_profile_sha256"))
            and semantic._is_sha256(
                audit.get("expected_risk_profile_sha256")
            )
            and audit.get("expected_risk_profile_sha256")
            == audit.get("risk_profile_sha256")
            and semantic._is_sha256(
                audit.get("risk_profile_payload_root_sha256")
            )
            and audit.get("miss_counts") == expected["miss_counts"]
            and audit.get("cached_symbol_counts")
            == expected["cached_symbol_counts"],
            "task3_cache_audit_invalid",
        )
        config_roots.add(str(audit["config_root_sha256"]))
        risk_roots.add(str(audit["risk_profile_sha256"]))
        risk_payload_roots.add(str(audit["risk_profile_payload_root_sha256"]))
        rows.append(copy.deepcopy(dict(audit)))
    _require(
        len(config_roots) == len(risk_roots) == len(risk_payload_roots) == 1,
        "task3_cache_binding_changed_between_days",
    )
    return {
        "status": "TASK3_CAMPAIGN_CACHE_BOUNDED_AND_EXACT",
        "day_count": len(rows),
        "config_root_sha256": next(iter(config_roots)),
        "risk_profile_sha256": next(iter(risk_roots)),
        "expected_risk_profile_sha256": next(iter(risk_roots)),
        "risk_profile_payload_root_sha256": next(iter(risk_payload_roots)),
        "daily_audits": rows,
        "audit_root_sha256": semantic.canonical_sha256(rows),
    }


def _validate_bound_source_successor(
    source: Mapping[str, Any],
) -> dict[str, Any]:
    bound = source.get("source_bundle_consumer_rebind_authority")
    bound = _require_exact_mapping_keys(
        bound,
        _BOUND_REBIND_FIELDS,
        "task3_source_rebind_binding_invalid",
    )
    bound_projection = copy.deepcopy(dict(bound))
    bound_root = bound_projection.pop("binding_root_sha256", None)
    _require(
        semantic._is_sha256(bound_root)
        and semantic.canonical_sha256(bound_projection) == bound_root
        and bound.get("schema")
        == "gtos.replay_acceleration.bound_source_bundle_consumer_rebind_authority.v1"
        and bound.get("broker_live_authority") is False
        and bound.get("continuation_authorized") is False
        and bound.get("economic_values_exposed") is False
        and bound.get("policy_execution_entered") is False,
        "task3_source_rebind_binding_invalid",
    )
    authority_path = Path(str(bound.get("authority_path") or ""))
    _require(
        authority_path.is_absolute()
        and authority_path.is_file()
        and not authority_path.is_symlink()
        and semantic.file_sha256(authority_path)
        == bound.get("authority_file_sha256"),
        "task3_source_rebind_authority_file_invalid",
    )
    authority = _load_json(authority_path)
    _require_exact_mapping_keys(
        authority,
        _SOURCE_REBIND_AUTHORITY_FIELDS,
        "task3_source_rebind_authority_invalid",
    )
    _require(
        semantic.canonical_bytes(authority)
        == semantic.canonical_bytes(bound.get("authority")),
        "task3_source_rebind_authority_embedding_mismatch",
    )
    authority_projection = copy.deepcopy(authority)
    authority_root = authority_projection.pop("authority_root_sha256", None)
    transformation = authority.get("bundle_transformation")
    selection = authority.get("selection_transformation")
    _require(
        semantic._is_sha256(authority_root)
        and authority_root == bound.get("authority_root_sha256")
        and semantic.canonical_sha256(authority_projection) == authority_root
        and authority.get("status")
        == "ACCEPTED_SOURCE_BYTES_IDENTICAL_IMPLEMENTATION_SUCCESSOR"
        and authority.get("broker_live_authority") is False
        and authority.get("continuation_authorized") is False
        and authority.get("economic_values_exposed") is False
        and authority.get("policy_execution_entered") is False
        and isinstance(transformation, Mapping)
        and transformation.get("cross_symbol_barrier_exact") is True
        and transformation.get("normalized_rows_exact") is True
        and transformation.get("selected_day_rows_exact") is True
        and transformation.get("source_payloads_exact") is True
        and transformation.get("source_plan_exact") is True
        and transformation.get("unexpected_difference_count") == 0
        and isinstance(selection, Mapping)
        and selection.get("source_semantics_exact") is True
        and selection.get("unexpected_difference_count") == 0
        and selection.get("source_plan_digest_sha256")
        == source.get("source_plan_digest_sha256")
        == bound.get("source_plan_digest_sha256"),
        "task3_source_rebind_authority_invalid",
    )
    verified_bundle = bound.get("verified_successor_bundle")
    verified_selection = bound.get("verified_successor_selection")
    successor_bundle = authority.get("successor_bundle")
    successor_selection = authority.get("successor_selection")
    _require(
        isinstance(verified_bundle, Mapping)
        and isinstance(verified_selection, Mapping)
        and isinstance(successor_bundle, Mapping)
        and isinstance(successor_selection, Mapping)
        and verified_bundle.get("bundle_root_sha256")
        == successor_bundle.get("bundle_root_sha256")
        == source.get("source_bundle_root_sha256")
        and verified_bundle.get("file_sha256")
        == successor_bundle.get("sha256")
        and verified_bundle.get("implementation_root_sha256")
        == successor_bundle.get("implementation_root_sha256")
        and verified_selection.get("selection_root_sha256")
        == successor_selection.get("selection_root_sha256")
        == source.get("selection_root_sha256")
        and verified_selection.get("file_sha256")
        == successor_selection.get("sha256"),
        "task3_source_rebind_successor_mismatch",
    )
    bundle_path = Path(str(verified_bundle.get("path") or ""))
    selection_path = Path(str(verified_selection.get("path") or ""))
    _require(
        bundle_path.is_absolute()
        and bundle_path.is_file()
        and not bundle_path.is_symlink()
        and selection_path.is_absolute()
        and selection_path.is_file()
        and not selection_path.is_symlink()
        and semantic.file_sha256(bundle_path)
        == verified_bundle.get("file_sha256")
        and semantic.file_sha256(selection_path)
        == verified_selection.get("file_sha256"),
        "task3_source_rebind_successor_file_invalid",
    )
    bundle = _load_json(bundle_path)
    selection_payload = _load_json(selection_path)
    bundle_projection = copy.deepcopy(bundle)
    selection_projection = copy.deepcopy(selection_payload)
    bundle_root = bundle_projection.pop("bundle_root_sha256", None)
    selection_root = selection_projection.pop("selection_root_sha256", None)
    _require(
        bundle_root == verified_bundle.get("bundle_root_sha256")
        and semantic.canonical_sha256(bundle_projection) == bundle_root
        and selection_root == verified_selection.get("selection_root_sha256")
        and semantic.canonical_sha256(selection_projection) == selection_root,
        "task3_source_rebind_successor_root_invalid",
    )
    independent = authority.get("independent_verifiers")
    _require(
        isinstance(independent, list) and len(independent) == 1,
        "task3_source_rebind_independent_verifier_invalid",
    )
    verifier_row = independent[0]
    verifier_row = _require_exact_mapping_keys(
        verifier_row,
        _INDEPENDENT_VERIFIER_ROW_FIELDS,
        "task3_source_rebind_independent_verifier_invalid",
    )
    verifier_path = Path(str(verifier_row.get("path") or ""))
    _require(
        verifier_path.is_absolute()
        and verifier_path.is_file()
        and not verifier_path.is_symlink()
        and semantic.file_sha256(verifier_path) == verifier_row.get("sha256"),
        "task3_source_rebind_independent_verifier_invalid",
    )
    verifier = _load_json(verifier_path)
    try:
        strict_verifier = validate_independent_verifier_envelope(
            verifier,
            envelope_path=verifier_path,
        )
    except SourceRebindRejected as exc:
        raise Task3ExactCacheRejected(
            f"task3_source_rebind_independent_verifier_invalid:{exc}"
        ) from None
    verifier_receipt = strict_verifier["receipt"]
    roots = verifier_receipt.get("roots")
    _require(
        strict_verifier.get("envelope_root_sha256")
        == verifier_row.get("envelope_root_sha256")
        and strict_verifier.get("receipt_file_sha256")
        == verifier_row.get("receipt_file_sha256")
        and verifier_receipt.get("bundle_root_sha256") == bundle_root
        and verifier_receipt.get("selection_root_sha256") == selection_root
        and isinstance(roots, Mapping)
        and roots.get("physical_recomputed")
        == verifier_row.get("physical_recomputed_root_sha256")
        and roots.get("logical_recomputed")
        == verifier_row.get("logical_recomputed_root_sha256"),
        "task3_source_rebind_independent_verifier_invalid",
    )
    return {
        "status": "TASK3_SOURCE_SUCCESSOR_INDEPENDENTLY_BOUND",
        "authority_file_sha256": bound["authority_file_sha256"],
        "authority_root_sha256": authority_root,
        "binding_root_sha256": bound_root,
        "bundle_root_sha256": bundle_root,
        "selection_root_sha256": selection_root,
        "independent_verifier_file_sha256": verifier_row["sha256"],
    }


def _runtime_number(value: Any) -> bool:
    return (
        type(value) in {int, float}
        and not isinstance(value, bool)
        and value >= 0
    )


def _project_source_authority_pair(
    reference: Mapping[str, Any],
    accelerated: Mapping[str, Any],
    *,
    reference_shared: Mapping[str, Any],
    accelerated_shared: Mapping[str, Any],
) -> dict[str, Any]:
    for source in (reference, accelerated):
        _require_exact_mapping_keys(
            source,
            _SOURCE_AUTHORITY_FIELDS,
            "task3_source_authority_schema_invalid",
        )
        barrier = _require_exact_mapping_keys(
            source.get("cross_symbol_prewarm_barrier"),
            _SOURCE_BARRIER_FIELDS,
            "task3_source_barrier_schema_invalid",
        )
        metrics = _require_exact_mapping_keys(
            source.get("typed_cache_metrics"),
            _SOURCE_METRIC_FIELDS,
            "task3_source_metrics_schema_invalid",
        )
        _require(
            source.get("schema")
            == "gtos.replay_acceleration.real_source_authority.v1"
            and source.get("candidate_cache_enabled") is False
            and source.get("policy_execution_entered") is False
            and source.get("policy_state_cache_enabled") is False
            and source.get("partition_count") == 96
            and source.get("symbol_count") == 24
            and semantic._is_sha256(source.get("config_projection_root_sha256"))
            and semantic._is_sha256(source.get("normalizer_code_root_sha256"))
            and semantic._is_sha256(source.get("selection_root_sha256"))
            and semantic._is_sha256(source.get("source_bundle_root_sha256"))
            and semantic._is_sha256(source.get("source_plan_digest_sha256"))
            and _runtime_number(source.get("bundle_validation_seconds"))
            and barrier.get("barrier_complete") is True
            and barrier.get("requested") is True
            and barrier.get("partition_count") == 96
            and barrier.get("worker_count") == 4
            and semantic._is_sha256(barrier.get("partition_set_root_sha256"))
            and _runtime_number(barrier.get("seconds"))
            and all(
                _runtime_number(metrics.get(field))
                for field in _SOURCE_METRIC_FIELDS
            ),
            "task3_source_authority_invalid",
        )
    for shared, source in (
        (reference_shared, reference),
        (accelerated_shared, accelerated),
    ):
        _require_exact_mapping_keys(
            shared,
            _SHARED_SOURCE_FIELDS,
            "task3_shared_source_schema_invalid",
        )
        _require(
            all(
                semantic.canonical_bytes(shared.get(field))
                == semantic.canonical_bytes(source.get(field))
                for field in _SHARED_SOURCE_FIELDS - {"prewarm_worker_count"}
            )
            and shared.get("prewarm_worker_count")
            == source["cross_symbol_prewarm_barrier"]["worker_count"],
            "task3_shared_source_authority_mismatch",
        )
    reference_successor = _validate_bound_source_successor(reference)
    accelerated_successor = _validate_bound_source_successor(accelerated)
    left = copy.deepcopy(dict(reference))
    right = copy.deepcopy(dict(accelerated))
    for projected in (left, right):
        projected["bundle_validation_seconds"] = TIME_SENTINEL
        projected["normalizer_code_root_sha256"] = HASH_SENTINEL
        projected["selection_root_sha256"] = HASH_SENTINEL
        projected["source_bundle_root_sha256"] = HASH_SENTINEL
        projected["source_bundle_consumer_rebind_authority"] = HASH_SENTINEL
        projected["cross_symbol_prewarm_barrier"][
            "partition_set_root_sha256"
        ] = HASH_SENTINEL
        projected["cross_symbol_prewarm_barrier"]["seconds"] = TIME_SENTINEL
        for field in (
            "hashing_seconds",
            "normalization_seconds",
            "serialization_seconds",
            "verification_seconds",
        ):
            projected["typed_cache_metrics"][field] = TIME_SENTINEL
    _require(
        semantic.canonical_bytes(left) == semantic.canonical_bytes(right),
        "task3_source_authority_semantic_mismatch",
    )
    shared_left = copy.deepcopy(dict(reference_shared))
    shared_right = copy.deepcopy(dict(accelerated_shared))
    for projected in (shared_left, shared_right):
        projected["normalizer_code_root_sha256"] = HASH_SENTINEL
        projected["selection_root_sha256"] = HASH_SENTINEL
        projected["source_bundle_root_sha256"] = HASH_SENTINEL
        projected["source_bundle_consumer_rebind_authority"] = HASH_SENTINEL
    _require(
        semantic.canonical_bytes(shared_left)
        == semantic.canonical_bytes(shared_right),
        "task3_shared_source_semantic_mismatch",
    )
    return {
        "status": "TASK3_SOURCE_AUTHORITY_SCHEMA_EXACT",
        "reference_successor": reference_successor,
        "accelerated_successor": accelerated_successor,
        "normalized_paths": [
            "bundle_validation_seconds",
            "normalizer_code_root_sha256",
            "selection_root_sha256",
            "source_bundle_root_sha256",
            "source_bundle_consumer_rebind_authority",
            "cross_symbol_prewarm_barrier/partition_set_root_sha256",
            "cross_symbol_prewarm_barrier/seconds",
            "typed_cache_metrics/hashing_seconds",
            "typed_cache_metrics/normalization_seconds",
            "typed_cache_metrics/serialization_seconds",
            "typed_cache_metrics/verification_seconds",
        ],
    }


def _validate_task3_summary_authority(
    reference: Mapping[str, Any],
    accelerated: Mapping[str, Any],
    *,
    cache: Mapping[str, Any],
) -> dict[str, Any]:
    reference_shared = reference.get("shared_execution_contract")
    accelerated_shared = accelerated.get("shared_execution_contract")
    _require(
        isinstance(reference_shared, Mapping)
        and isinstance(accelerated_shared, Mapping),
        "task3_shared_contract_missing",
    )
    try:
        split = split_shared_execution_contract(dict(accelerated_shared))
    except ContractSplitError as exc:
        raise Task3ExactCacheRejected(
            f"task3_shared_contract_invalid:{exc}"
        ) from None
    exact_roots = accelerated_shared.get("exact_profile_config_roots_sha256")
    _require(
        exact_roots
        == {"repaired_package_conversion_v3": cache["config_root_sha256"]},
        "task3_exact_config_root_not_cache_bound",
    )
    exact_risk_bindings = accelerated_shared.get(
        "exact_risk_profile_bindings"
    )
    _require(
        exact_risk_bindings
        == {
            "repaired_package_conversion_v3": {
                "path": "config/profiles/ftmo.yaml",
                "sha256": cache["risk_profile_sha256"],
            }
        }
        and cache["risk_profile_sha256"]
        == cache["expected_risk_profile_sha256"],
        "task3_risk_profile_not_contract_bound",
    )
    reference_binding = reference.get("b7_5_contract_binding")
    accelerated_binding = accelerated.get("b7_5_contract_binding")
    _require(
        isinstance(reference_binding, Mapping)
        and isinstance(accelerated_binding, Mapping),
        "task3_b7_binding_invalid",
    )
    for binding, shared in (
        (reference_binding, reference_shared),
        (accelerated_binding, accelerated_shared),
    ):
        _require(
            binding.get("valid") is True
            and binding.get("required") is True
            and binding.get("actual_shared_execution_contract_digest_sha256")
            == binding.get("expected_shared_execution_contract_digest_sha256")
            == shared.get("shared_execution_contract_digest_sha256"),
            "task3_b7_binding_invalid",
        )
    reference_binding_projection = copy.deepcopy(dict(reference_binding))
    accelerated_binding_projection = copy.deepcopy(dict(accelerated_binding))
    for projection in (
        reference_binding_projection,
        accelerated_binding_projection,
    ):
        projection.pop("actual_shared_execution_contract_digest_sha256")
        projection.pop("expected_shared_execution_contract_digest_sha256")
    _require(
        semantic.canonical_bytes(reference_binding_projection)
        == semantic.canonical_bytes(accelerated_binding_projection),
        "task3_b7_binding_semantic_mismatch",
    )
    reference_source = reference.get("source_acceleration_authority")
    accelerated_source = accelerated.get("source_acceleration_authority")
    _require(
        isinstance(reference_source, Mapping)
        and isinstance(accelerated_source, Mapping),
        "task3_source_authority_missing",
    )
    reference_shared_source = reference_shared.get("execution_options", {}).get(
        "source_acceleration"
    )
    accelerated_shared_source = accelerated_shared.get(
        "execution_options", {}
    ).get("source_acceleration")
    _require(
        isinstance(reference_shared_source, Mapping)
        and isinstance(accelerated_shared_source, Mapping),
        "task3_shared_source_authority_missing",
    )
    source_successor = _project_source_authority_pair(
        reference_source,
        accelerated_source,
        reference_shared=reference_shared_source,
        accelerated_shared=accelerated_shared_source,
    )
    return {
        "status": "TASK3_IMPLEMENTATION_AUTHORITY_VALID",
        "shared_execution_contract_digest_sha256": accelerated_shared[
            "shared_execution_contract_digest_sha256"
        ],
        "economic_execution_contract_digest_sha256": split[
            "economic_execution_contract_digest_sha256"
        ],
        "accelerator_implementation_authority_root_sha256": split[
            "accelerator_implementation_authority_root_sha256"
        ],
        "exact_profile_config_roots_sha256": dict(exact_roots),
        "exact_risk_profile_bindings": copy.deepcopy(exact_risk_bindings),
        "source_successor": source_successor,
    }


def compare_summary_with_cache_provenance(
    reference: Mapping[str, Any],
    accelerated: Mapping[str, Any],
    *,
    cache_validator: Callable[[Mapping[str, Any]], dict[str, Any]] = (
        validate_cache_audits
    ),
    reference_cache_validator: (
        Callable[[Mapping[str, Any]], dict[str, Any]] | None
    ) = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    cache = cache_validator(accelerated)
    if reference_cache_validator is not None:
        reference_cache_validator(reference)
    authority = _validate_task3_summary_authority(
        reference,
        accelerated,
        cache=cache,
    )
    reference_copy = copy.deepcopy(dict(reference))
    accelerated_copy = copy.deepcopy(dict(accelerated))
    for row in reference_copy.get("progress_rows") or []:
        if reference_cache_validator is None:
            _require(
                "campaign_exact_cache" not in row,
                "task3_reference_cache_metadata_unexpected",
            )
        else:
            row.pop("campaign_exact_cache", None)
    for row in accelerated_copy.get("progress_rows") or []:
        row.pop("campaign_exact_cache", None)
    classified_paths: list[dict[str, str]] = []
    for field, rationale in (
        ("generated_at_utc", "noncausal_wall_clock_generation_time"),
        ("route_id", "replay_output_namespace_identity"),
        ("b7_5_contract_binding", "validated_implementation_digest_successor"),
        ("shared_execution_contract", "validated_accelerator_implementation_successor"),
        ("source_acceleration_authority", "validated_byte_exact_source_successor_and_runtime_metrics"),
    ):
        if semantic.canonical_bytes(reference_copy.get(field)) != semantic.canonical_bytes(
            accelerated_copy.get(field)
        ):
            classified_paths.append({"path": field, "rationale": rationale})
        if field in {
            "b7_5_contract_binding",
            "shared_execution_contract",
            "source_acceleration_authority",
        }:
            # Both complete objects were already checked by the stricter
            # successor-aware authority validator above.  Replace them with
            # the semantic comparator's null authority sentinel so a newly
            # accepted accelerator can itself serve as the next task's
            # reference without extending historical fixed-root registries.
            reference_copy[field] = None
            accelerated_copy[field] = None
        else:
            accelerated_copy[field] = copy.deepcopy(reference_copy.get(field))
    reference_capacity = reference_copy.get(
        "capacity_safe_chunk_execution_contract"
    )
    accelerated_capacity = accelerated_copy.get(
        "capacity_safe_chunk_execution_contract"
    )
    _require(
        isinstance(reference_capacity, Mapping)
        and isinstance(accelerated_capacity, Mapping),
        "task3_capacity_contract_invalid",
    )
    reference_checkpoints = reference_capacity.get("checkpoints")
    accelerated_checkpoints = accelerated_capacity.get("checkpoints")
    _require(
        isinstance(reference_checkpoints, list)
        and isinstance(accelerated_checkpoints, list)
        and len(reference_checkpoints) == len(accelerated_checkpoints),
        "task3_capacity_contract_invalid",
    )
    for index, (left, right) in enumerate(
        zip(reference_checkpoints, accelerated_checkpoints)
    ):
        _require(
            isinstance(left, Mapping) and isinstance(right, Mapping),
            "task3_capacity_contract_invalid",
        )
        if left.get("gc_collected_objects") != right.get("gc_collected_objects"):
            _require(
                type(left.get("gc_collected_objects")) is int
                and left.get("gc_collected_objects") >= 0
                and type(right.get("gc_collected_objects")) is int
                and right.get("gc_collected_objects") >= 0,
                "task3_gc_measurement_invalid",
            )
            accelerated_checkpoints[index]["gc_collected_objects"] = left[
                "gc_collected_objects"
            ]
            classified_paths.append(
                {
                    "path": (
                        "capacity_safe_chunk_execution_contract/checkpoints/"
                        f"{index}/gc_collected_objects"
                    ),
                    "rationale": "host_runtime_gc_measurement",
                }
            )
    try:
        comparison = semantic.compare_summary_semantics(
            reference_copy,
            accelerated_copy,
            end_day=END_DAY,
        )
    except semantic.SemanticAcceptanceError as exc:
        raise Task3ExactCacheRejected(
            f"task3_summary_semantic_mismatch:{exc}"
        ) from None
    return {
        **comparison,
        "task3_classified_noncausal_or_implementation_paths": classified_paths,
    }, cache, authority


def _exact_semantic_file(
    reference_path: Path,
    accelerated_path: Path,
    *,
    role: str,
) -> dict[str, Any]:
    reference_sha = semantic.file_sha256(reference_path)
    accelerated_sha = semantic.file_sha256(accelerated_path)
    _require(reference_sha == accelerated_sha, f"task3_{role}_file_mismatch")
    rows = _rows(reference_path)
    return {
        "role": role,
        "status": "BYTE_EXACT",
        "row_count": len(rows),
        "sha256": reference_sha,
        "bytes": reference_path.stat().st_size,
    }


def _measurement(receipt: Mapping[str, Any]) -> float:
    measurement = receipt.get("measurement")
    value = (
        measurement.get("wall_seconds")
        if isinstance(measurement, Mapping)
        else None
    )
    _require(
        type(value) in {int, float} and not isinstance(value, bool) and value > 0,
        "task3_wall_measurement_invalid",
    )
    return float(value)


def _sparse_builder_implementation_root(builder_path: Path) -> str:
    try:
        source = Path(builder_path).read_bytes()
        begin_marker = b"# BEGIN GTOS_SPARSE_TICK_CACHE_IMPLEMENTATION\n"
        end_marker = b"# " + b"END GTOS_SPARSE_TICK_CACHE_IMPLEMENTATION\n"
        begin = source.index(begin_marker) + len(begin_marker)
        end = source.index(end_marker, begin)
    except (OSError, ValueError):
        raise Task3ExactCacheRejected(
            "task3_warm_sparse_cache_builder_invalid"
        ) from None
    return hashlib.sha256(source[begin:end]).hexdigest()


def _hash_and_count_sparse_partition(path: Path) -> tuple[str, int, int]:
    digest = hashlib.sha256()
    byte_count = 0
    row_count = 0
    try:
        with Path(path).open("rb") as handle:
            for line in handle:
                _require(
                    bool(line.strip()) and line.endswith(b"\n"),
                    "task3_warm_sparse_cache_partition_framing_invalid",
                )
                digest.update(line)
                byte_count += len(line)
                row_count += 1
    except OSError:
        raise Task3ExactCacheRejected(
            "task3_warm_sparse_cache_partition_unreadable"
        ) from None
    return digest.hexdigest(), byte_count, row_count


def _validate_sealed_sparse_cache_entry(
    *,
    cache_root: Path,
    receipt_entry: Mapping[str, Any],
    window_start_utc: str,
    window_end_utc: str,
) -> dict[str, Any]:
    identity_root = str(receipt_entry.get("identity_root_sha256") or "")
    entry_root = cache_root / identity_root
    _require(
        semantic._is_sha256(identity_root)
        and entry_root.parent == cache_root
        and entry_root.is_dir()
        and not entry_root.is_symlink(),
        "task3_warm_sparse_cache_entry_invalid",
    )
    manifest_path = entry_root / "manifest.json"
    seal_path = entry_root / "SEALED"
    partition_root = entry_root / "partitions"
    _require(
        manifest_path.is_file()
        and not manifest_path.is_symlink()
        and seal_path.is_file()
        and not seal_path.is_symlink()
        and partition_root.is_dir()
        and not partition_root.is_symlink(),
        "task3_warm_sparse_cache_seal_invalid",
    )
    manifest = _require_exact_mapping_keys(
        _load_json(manifest_path),
        _SPARSE_MANIFEST_KEYS,
        "task3_warm_sparse_cache_manifest_invalid",
    )
    identity = _require_exact_mapping_keys(
        manifest.get("identity"),
        _SPARSE_IDENTITY_KEYS,
        "task3_warm_sparse_cache_identity_invalid",
    )
    source_stat = _require_exact_mapping_keys(
        identity.get("source_stat_identity"),
        _SPARSE_SOURCE_STAT_KEYS,
        "task3_warm_sparse_cache_identity_invalid",
    )
    manifest_source_validation = _require_exact_mapping_keys(
        manifest.get("source_validation"),
        _SPARSE_MANIFEST_SOURCE_VALIDATION_KEYS,
        "task3_warm_sparse_cache_source_attestation_invalid",
    )
    _require_exact_mapping_keys(
        manifest_source_validation.get("source_stat_identity"),
        _SPARSE_SOURCE_STAT_KEYS,
        "task3_warm_sparse_cache_source_attestation_invalid",
    )
    expected_builder_path = Path(__file__).with_name(
        "replay_acceleration_attempt5_typed_sparse_runner.py"
    ).resolve()
    declared_builder_path = Path(str(identity.get("builder_path") or ""))
    identity_projection = dict(identity)
    computed_identity_root = semantic.canonical_sha256(identity_projection)
    manifest_projection = dict(manifest)
    expected_manifest_root = str(
        manifest_projection.pop("manifest_root_sha256", "")
    )
    try:
        sealed_root = seal_path.read_text(encoding="ascii").strip()
    except (OSError, UnicodeError):
        raise Task3ExactCacheRejected(
            "task3_warm_sparse_cache_seal_invalid"
        ) from None
    _require(
        manifest.get("schema")
        == "gtos.replay_acceleration.sparse_tick_window_cache.v1"
        and manifest.get("status")
        == "SEALED_IMMUTABLE_SPARSE_TICK_WINDOW"
        and manifest.get("economic_values_exposed") is False
        and manifest.get("broker_live_authority") is False
        and identity.get("schema")
        == "gtos.replay_acceleration.sparse_tick_window_cache.v1"
        and identity.get("source_path")
        == str(Path(str(receipt_entry.get("source_path") or "")).resolve())
        and identity.get("source_sha256")
        == receipt_entry.get("source_sha256")
        and identity.get("source_stat_identity")
        == receipt_entry.get("source_validation", {}).get(
            "source_stat_identity"
        )
        and identity.get("symbol") == receipt_entry.get("symbol")
        and identity.get("window_start_utc") == window_start_utc
        and identity.get("window_end_utc") == window_end_utc
        and type(identity.get("declared_source_row_count")) is int
        and identity.get("declared_source_row_count") > 0
        and identity.get("row_semantics") == _SPARSE_ROW_SEMANTICS
        and declared_builder_path == expected_builder_path
        and not expected_builder_path.is_symlink()
        and identity.get("builder_implementation_root_sha256")
        == _sparse_builder_implementation_root(expected_builder_path)
        and computed_identity_root == identity_root
        and manifest.get("identity_root_sha256") == identity_root
        and semantic._is_sha256(expected_manifest_root)
        and semantic.canonical_sha256(manifest_projection)
        == expected_manifest_root
        and receipt_entry.get("manifest_root_sha256")
        == expected_manifest_root
        and sealed_root == expected_manifest_root
        and manifest_source_validation.get("status")
        == "FULL_SOURCE_SHA256_VALIDATED_AT_BUILD"
        and manifest_source_validation.get("source_sha256")
        == receipt_entry.get("source_sha256")
        and manifest_source_validation.get("source_stat_identity")
        == source_stat,
        "task3_warm_sparse_cache_commitment_invalid",
    )
    partitions = manifest.get("partitions")
    _require(
        isinstance(partitions, list)
        and type(manifest.get("partition_count")) is int
        and manifest.get("partition_count") > 0
        and len(partitions) == manifest.get("partition_count")
        and manifest.get("partition_count")
        == receipt_entry.get("partition_count")
        and type(manifest.get("retained_row_count")) is int
        and manifest.get("retained_row_count") > 0
        and manifest.get("retained_row_count")
        == receipt_entry.get("retained_row_count")
        and type(manifest.get("source_rows_scanned_through_window_end"))
        is int
        and manifest.get("source_rows_scanned_through_window_end")
        >= manifest.get("retained_row_count"),
        "task3_warm_sparse_cache_partition_inventory_invalid",
    )
    try:
        window_start = datetime.fromisoformat(window_start_utc)
        window_end = datetime.fromisoformat(window_end_utc)
    except ValueError:
        raise Task3ExactCacheRejected(
            "task3_warm_sparse_cache_window_invalid"
        ) from None
    observed_days: list[str] = []
    observed_rows = 0
    observed_bytes = 0
    for raw_partition in partitions:
        partition = _require_exact_mapping_keys(
            raw_partition,
            _SPARSE_PARTITION_KEYS,
            "task3_warm_sparse_cache_partition_manifest_invalid",
        )
        day = str(partition.get("day") or "")
        relative_path = Path(str(partition.get("path") or ""))
        unresolved_path = entry_root / relative_path
        resolved_path = unresolved_path.resolve()
        try:
            resolved_path.relative_to(entry_root.resolve())
            partition_day = datetime.fromisoformat(day)
        except (ValueError, OSError):
            raise Task3ExactCacheRejected(
                "task3_warm_sparse_cache_partition_path_invalid"
            ) from None
        _require(
            relative_path == Path("partitions") / f"{day}.jsonl"
            and unresolved_path.is_file()
            and not unresolved_path.is_symlink()
            and window_start.date() <= partition_day.date() <= window_end.date()
            and type(partition.get("bytes")) is int
            and partition.get("bytes") > 0
            and type(partition.get("rows")) is int
            and partition.get("rows") > 0
            and semantic._is_sha256(partition.get("sha256")),
            "task3_warm_sparse_cache_partition_path_invalid",
        )
        actual_sha, actual_bytes, actual_rows = _hash_and_count_sparse_partition(
            resolved_path
        )
        _require(
            actual_sha == partition.get("sha256")
            and actual_bytes == partition.get("bytes")
            and actual_rows == partition.get("rows"),
            "task3_warm_sparse_cache_partition_commitment_invalid",
        )
        observed_days.append(day)
        observed_rows += actual_rows
        observed_bytes += actual_bytes
    _require(
        observed_days == sorted(set(observed_days))
        and observed_rows == manifest.get("retained_row_count"),
        "task3_warm_sparse_cache_partition_aggregate_invalid",
    )
    return {
        "identity_root_sha256": identity_root,
        "manifest_root_sha256": expected_manifest_root,
        "partition_count": len(partitions),
        "retained_row_count": observed_rows,
        "partition_bytes": observed_bytes,
    }


def validate_sealed_tick_cache_prewarm(
    accelerated_root: Path,
) -> dict[str, Any]:
    path = (
        Path(accelerated_root)
        / "ATTEMPT5_TICK_SPARSE_CACHE_PREWARM_RECEIPT.json"
    )
    payload = _require_exact_mapping_keys(
        _load_json(path),
        _SPARSE_PREWARM_KEYS,
        "task3_warm_sparse_prewarm_invalid",
    )
    storage = _require_exact_mapping_keys(
        payload.get("non_authoritative_filesystem_storage_receipt"),
        _SPARSE_STORAGE_KEYS,
        "task3_warm_sparse_prewarm_invalid",
    )
    core = copy.deepcopy(dict(payload))
    expected_root = core.pop("prewarm_root_sha256", None)
    core.pop("non_authoritative_filesystem_storage_receipt", None)
    entries = payload.get("entries")
    storage_entries = storage.get("entries")
    cache_root = Path(str(payload.get("cache_root") or ""))
    _require(
        payload.get("schema")
        == "gtos.replay_acceleration.sparse_tick_cache_prewarm.v1"
        and payload.get("status")
        == "SEALED_SPARSE_TICK_CACHE_PREWARM_COMPLETE"
        and payload.get("cache_schema")
        == "gtos.replay_acceleration.sparse_tick_window_cache.v1"
        and payload.get("cache_precondition_measurement")
        == (
            "entry_identity_binds_exact_source_stat_declared_sha_builder_and_window;"
            "reuse_recomputes_manifest_and_partition_hashes"
        )
        and cache_root.is_absolute()
        and payload.get("window_start_utc")
        == "2025-12-31T00:00:00+00:00"
        and payload.get("window_end_utc") == "2026-01-04T00:00:00+00:00"
        and payload.get("worker_count") == 4
        and payload.get("entry_count") == 4
        and payload.get("partition_count") == 8
        and type(payload.get("retained_row_count")) is int
        and payload.get("retained_row_count") > 0
        and payload.get("raw_source_full_hash_count") == 0
        and payload.get("sealed_cache_reuse_count") == 4
        and payload.get("economic_values_exposed") is False
        and payload.get("broker_live_authority") is False
        and semantic._is_sha256(expected_root)
        and semantic.canonical_sha256(core) == expected_root
        and isinstance(entries, list)
        and len(entries) == 4
        and storage.get("schema")
        == "gtos.replay_acceleration.sparse_tick_filesystem_storage.v1"
        and storage.get("status")
        == "NON_AUTHORITATIVE_FILESYSTEM_STORAGE_TELEMETRY"
        and storage.get("authoritative") is False
        and storage.get("included_in_prewarm_root_sha256") is False
        and isinstance(storage_entries, list)
        and len(storage_entries) == 4,
        "task3_warm_sparse_prewarm_invalid",
    )
    _require(
        cache_root == cache_root.resolve()
        and cache_root.is_dir()
        and not cache_root.is_symlink(),
        "task3_warm_sparse_cache_root_invalid",
    )
    expected_symbols = {"EURUSD", "USDJPY", "XAGUSD", "XAUUSD"}
    observed_symbols: set[str] = set()
    observed_storage: set[tuple[str, str, str]] = set()
    partition_count = 0
    retained_row_count = 0
    partition_bytes = 0
    for raw_entry in entries:
        entry = _require_exact_mapping_keys(
            raw_entry,
            _SPARSE_PREWARM_ENTRY_KEYS,
            "task3_warm_sparse_prewarm_invalid",
        )
        validation = _require_exact_mapping_keys(
            entry.get("source_validation"),
            _SPARSE_SOURCE_VALIDATION_KEYS,
            "task3_warm_sparse_prewarm_invalid",
        )
        source_stat = _require_exact_mapping_keys(
            validation.get("source_stat_identity"),
            _SPARSE_SOURCE_STAT_KEYS,
            "task3_warm_sparse_prewarm_invalid",
        )
        symbol = str(entry.get("symbol") or "")
        source_path = Path(str(entry.get("source_path") or ""))
        try:
            stat_result = source_path.stat()
            current_stat = {
                "device": stat_result.st_dev,
                "inode": stat_result.st_ino,
                "byte_count": stat_result.st_size,
                "mtime_ns": stat_result.st_mtime_ns,
                "ctime_ns": stat_result.st_ctime_ns,
            }
        except OSError:
            current_stat = {}
        _require(
            symbol in expected_symbols
            and symbol not in observed_symbols
            and source_path.is_absolute()
            and source_path.is_file()
            and not source_path.is_symlink()
            and semantic._is_sha256(entry.get("source_sha256"))
            and semantic._is_sha256(entry.get("identity_root_sha256"))
            and semantic._is_sha256(entry.get("manifest_root_sha256"))
            and validation.get("path") == str(source_path)
            and validation.get("manifest_sha256")
            == entry.get("source_sha256")
            and validation.get("sha_validation_status")
            == "sealed_full_hash_attestation_reused"
            and validation.get("status")
            == (
                "SEALED_CACHE_REUSED_AFTER_EXACT_SOURCE_STAT_AND_"
                "PARTITION_VALIDATION"
            )
            and validation.get("raw_source_full_hash_performed") is False
            and entry.get("raw_source_full_hash_performed") is False
            and entry.get("sealed_cache_reused") is True
            and source_stat == current_stat
            and type(entry.get("partition_count")) is int
            and entry.get("partition_count") > 0
            and type(entry.get("retained_row_count")) is int
            and entry.get("retained_row_count") > 0,
            "task3_warm_sparse_prewarm_invalid",
        )
        observed_symbols.add(symbol)
        verified_entry = _validate_sealed_sparse_cache_entry(
            cache_root=cache_root,
            receipt_entry=entry,
            window_start_utc=str(payload["window_start_utc"]),
            window_end_utc=str(payload["window_end_utc"]),
        )
        partition_count += int(verified_entry["partition_count"])
        retained_row_count += int(verified_entry["retained_row_count"])
        partition_bytes += int(verified_entry["partition_bytes"])
        observed_storage.add(
            (symbol, str(source_path), str(entry["source_sha256"]))
        )
    storage_projection: set[tuple[str, str, str]] = set()
    for raw_entry in storage_entries:
        entry = _require_exact_mapping_keys(
            raw_entry,
            _SPARSE_STORAGE_ENTRY_KEYS,
            "task3_warm_sparse_prewarm_invalid",
        )
        _require(
            entry.get("partitions") == [],
            "task3_warm_sparse_prewarm_invalid",
        )
        storage_projection.add(
            (
                str(entry.get("symbol") or ""),
                str(entry.get("source_path") or ""),
                str(entry.get("source_sha256") or ""),
            )
        )
    _require(
        observed_symbols == expected_symbols
        and partition_count == payload.get("partition_count")
        and retained_row_count == payload.get("retained_row_count")
        and storage_projection == observed_storage,
        "task3_warm_sparse_prewarm_invalid",
    )
    return {
        "status": "TASK3_WARM_SPARSE_CACHE_PRECONDITION_VERIFIED",
        "path": str(path.resolve()),
        "file_sha256": semantic.file_sha256(path),
        "prewarm_root_sha256": expected_root,
        "entry_count": 4,
        "partition_count": partition_count,
        "retained_row_count": retained_row_count,
        "partition_bytes": partition_bytes,
        "raw_source_full_hash_count": 0,
        "sealed_cache_reuse_count": 4,
        "symbols": sorted(observed_symbols),
    }


def run_acceptance(
    reference_root: Path,
    accelerated_root: Path,
    *,
    cache_validator: Callable[[Mapping[str, Any]], dict[str, Any]] = (
        validate_cache_audits
    ),
    reference_cache_validator: (
        Callable[[Mapping[str, Any]], dict[str, Any]] | None
    ) = None,
    receipt_schema: str = SCHEMA,
    receipt_status: str = STATUS,
    task_name: str = "Replay-Acceleration Task 3",
) -> dict[str, Any]:
    reference_root = Path(os.path.abspath(reference_root))
    accelerated_root = Path(os.path.abspath(accelerated_root))
    _require(reference_root != accelerated_root, "task3_roots_not_distinct")
    reference_identity = semantic._fresh_execution_identity(reference_root)
    accelerated_identity = semantic._fresh_execution_identity(accelerated_root)
    reference_manifest = semantic.validate_semantic_source_manifest(
        reference_root
    )
    accelerated_manifest = semantic.validate_semantic_source_manifest(
        accelerated_root
    )
    reference_receipt = _load_json(
        reference_root / "TASK2_SEMANTIC_SLICE_EXECUTION_RECEIPT.json"
    )
    accelerated_receipt = _load_json(
        accelerated_root / "TASK2_SEMANTIC_SLICE_EXECUTION_RECEIPT.json"
    )
    sealed_raw_tick_cache = validate_sealed_tick_cache_prewarm(
        accelerated_root
    )
    for field in (
        "source_plan_digest_sha256",
        "arm_fingerprint_sha256",
        "economic_execution_contract_digest_sha256",
        "runtime_input_contract_root_sha256",
    ):
        _require(
            reference_receipt.get(field) == accelerated_receipt.get(field),
            f"task3_execution_contract_mismatch:{field}",
        )
    _require(
        reference_receipt.get("broker_live_authority") is False
        and accelerated_receipt.get("broker_live_authority") is False
        and reference_receipt.get("broker_mutation_enabled") is False
        and accelerated_receipt.get("broker_mutation_enabled") is False,
        "task3_broker_authority_open",
    )

    role_proof = {
        "broker_order_lifecycle_capture_v4_packet/pre_order_capture_contract/"
        "execution_manager_packet_hash": "PREIMAGE"
    }
    role_comparisons = []
    for role in semantic.ROLE_SUFFIXES:
        try:
            role_comparisons.append(
                semantic.compare_role_rows(
                    role,
                    semantic._role_rows(reference_root, role),
                    semantic._role_rows(accelerated_root, role),
                    derived_hash_proofs=role_proof,
                )
            )
        except semantic.SemanticAcceptanceError as exc:
            raise Task3ExactCacheRejected(
                f"task3_role_semantic_mismatch:{role}:{exc}"
            ) from None

    reference_summary = _load_json(
        reference_root / f"{semantic.PREFIX}_PARTIAL_SUMMARY.json"
    )
    accelerated_summary = _load_json(
        accelerated_root / f"{semantic.PREFIX}_PARTIAL_SUMMARY.json"
    )
    (
        summary_comparison,
        cache_audit,
        implementation_authority,
    ) = compare_summary_with_cache_provenance(
        reference_summary,
        accelerated_summary,
        cache_validator=cache_validator,
        reference_cache_validator=reference_cache_validator,
    )
    preimages = compare_order_preimages(reference_root, accelerated_root)
    exact_semantic_files = [
        _exact_semantic_file(
            semantic._semantic_paths(reference_root)[role],
            semantic._semantic_paths(accelerated_root)[role],
            role=role,
        )
        for role in ("candidate", "state")
    ]

    reference_wall = _measurement(reference_receipt)
    accelerated_wall = _measurement(accelerated_receipt)
    saved = reference_wall - accelerated_wall
    _require(saved > 0, "task3_end_to_end_speedup_not_measured")
    speedup = reference_wall / accelerated_wall
    improvement_pct = saved / reference_wall * 100.0
    core = {
        "schema": receipt_schema,
        "status": receipt_status,
        "task": task_name,
        "acceptance_authorized": False,
        "reference_execution": reference_identity,
        "accelerated_execution": accelerated_identity,
        "semantic_source_manifests": {
            "reference": reference_manifest,
            "accelerated": accelerated_manifest,
        },
        "execution_contract": {
            field: reference_receipt[field]
            for field in (
                "source_plan_digest_sha256",
                "arm_fingerprint_sha256",
                "economic_execution_contract_digest_sha256",
                "runtime_input_contract_root_sha256",
            )
        },
        "performance": {
            "scope": "contiguous_jan1_no_event_plus_jan2_candidate_rich",
            "reference_wall_seconds": reference_wall,
            "accelerated_wall_seconds": accelerated_wall,
            "wall_seconds_saved": saved,
            "improvement_pct": improvement_pct,
            "speedup_ratio": speedup,
            "end_to_end_improvement_measured": True,
        },
        "sealed_raw_tick_cache_precondition": sealed_raw_tick_cache,
        "campaign_exact_cache": cache_audit,
        "accelerator_implementation_authority": implementation_authority,
        "role_comparisons": role_comparisons,
        "order_preimage_comparison": preimages,
        "exact_semantic_files": exact_semantic_files,
        "summary_semantics": summary_comparison,
        "meaningful_difference_count": 0,
        "unknown_difference_count": 0,
        "causal_or_economic_field_normalized": False,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
        "economic_values_exposed": False,
    }
    return {**core, "receipt_root_sha256": semantic.canonical_sha256(core)}


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path = Path(os.path.abspath(path))
    if path.exists() or path.is_symlink():
        raise Task3ExactCacheRejected("task3_output_must_be_new")
    path.parent.mkdir(parents=True, exist_ok=True)
    semantic.atomic_write_json(path, payload)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-root", type=Path, required=True)
    parser.add_argument("--accelerated-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    receipt = run_acceptance(args.reference_root, args.accelerated_root)
    atomic_write_json(args.output, receipt)
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
