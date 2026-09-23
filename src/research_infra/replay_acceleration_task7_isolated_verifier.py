#!/usr/bin/env python3
"""Independent verification of the production-real Task 7 acceptance receipt."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.research_infra.replay_prepared_day_pack import PreparedDayPackReader


ROOT = Path(__file__).resolve().parents[2]
ARMS = ("S0R0", "S1R0", "S0R1", "S1R1")
DAY = "2026-01-01"
PACK_SHA256 = "b83649706b47e625c965a1060252162535b2f95db4c5048eddc082369a2f300a"
TASK6_FILE_SHA256 = "fbe9f7de9854e213f57ee19e37c1513302222394f9e80ae73ee1df16c6346819"
TASK6_ROOT_SHA256 = "3137c0bb8e5f9dede3ae8cbc9ef5d3d1da7abd698b975f59fe8fc66fdfb892a3"
EXPECTED_ARM_FINGERPRINT = "2ece240b5fc9434a7ec20919e95cdf549bcd46f1c0311f130458fd4804c6d447"
EXPECTED_SOURCE_PLAN_DIGEST = "85663876fababc9b69c1bd7041c2bd043b286b456c2e635b2a6fc2289192d4e5"
EXPECTED_SHARED_EXECUTION_DIGEST = "d40353d4833f32929e83da7dc07369467c8a8dc1ef2499ef0f24255785b5ccdc"
EXPECTED_RUNTIME_INPUT_ROOT = "68e5f6832f97b79da326ceff75d428aa723aca839a48708348ad3a8c7a1bfbd7"
EXPECTED_SOURCE_AUTHORITY_SHA256 = "4a2703d70c80727ef9f7924cd5b2590004ce9cd958eadaf361224c2e508fff26"
EXPECTED_SOURCE_AUTHORITY_ROOT = "bd8a699e786ee0350f6ae36c40270d1db6f1ee2bae66c45984d134f06d54155a"
EXPECTED_SOURCE_BUNDLE_SHA256 = "a875636c9ec783bd06bf052b3ca9c082b8275b48156eb03eaf70de2c9494763c"
EXPECTED_SOURCE_BUNDLE_ROOT = "1283fdbff6a22715b1974ccd687396439228969353d58a2d405ad6a073cb6557"
EXPECTED_SOURCE_IMPLEMENTATION_ROOT = "4cafcaef4492e6e619941d4955ccf6dde601a2ef4c10c8fe853be43e5292555d"
EXPECTED_SOURCE_SELECTION_SHA256 = "0eb4828655cf2a1c8693c16b864271bd9c7561fb5ecd39387e386f1f8c36473a"
EXPECTED_SOURCE_SELECTION_ROOT = "1a3a57413a3b8b42d31542198954e1e72bb9ab28fbb0e8b9cf24773400dea80a"
EXPECTED_TICK_WINDOW_START = "2025-12-31T00:00:00+00:00"
EXPECTED_TICK_WINDOW_END = "2026-01-04T00:00:00+00:00"
CRITICAL_HOST_AVAILABLE_BYTES = 128 * 1024 * 1024
ACCEPTANCE_SCHEMA = "gtos.replay_acceleration.task7.acceptance.v1"
WORKER_SCHEMA = "gtos.replay_acceleration.task7.worker_receipt.v1"
ROLE_NAMES = (
    "decision",
    "scorecard",
    "order",
    "trade",
    "oracle",
    "missed",
    "bucket",
    "semantic_candidate",
    "semantic_state",
    "semantic_order_preimage",
)
ROLE_SUFFIXES = {
    "decision": "_DECISION_LEDGER.jsonl",
    "scorecard": "_SCORECARD_LEDGER.jsonl",
    "order": "_ORDER_LEDGER.jsonl",
    "trade": "_TRADE_LEDGER.jsonl",
    "oracle": "_ORDERED_PATH_ORACLE_LEDGER.jsonl",
    "missed": "_MISSED_OPPORTUNITY_LEDGER.jsonl",
    "bucket": "_BUCKET_LEDGER.jsonl",
    "semantic_candidate": "_SEMANTIC_CANDIDATE_LEDGER.jsonl",
    "semantic_state": "_SEMANTIC_STATE_CHECKPOINT_LEDGER.jsonl",
    "semantic_order_preimage": "_SEMANTIC_ORDER_PREIMAGE_LEDGER.jsonl",
}


class Task7VerificationError(RuntimeError):
    pass


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _root(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise Task7VerificationError(code)


def _rooted_json(path: Path, root_field: str, code: str) -> dict[str, Any]:
    path = Path(path)
    _require(path.is_file() and not path.is_symlink(), f"{code}_missing")
    raw = path.read_bytes()
    _require(raw.endswith(b"\n"), f"{code}_newline_missing")
    try:
        payload = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Task7VerificationError(f"{code}_json_invalid") from exc
    _require(isinstance(payload, dict), f"{code}_not_mapping")
    projection = dict(payload)
    recorded = projection.pop(root_field, None)
    _require(recorded == _root(projection), f"{code}_root_mismatch")
    return payload


def _absolute(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def _has_symlink_component(path: Path) -> bool:
    current = _absolute(path)
    while True:
        if current.is_symlink():
            return True
        parent = current.parent
        if parent == current:
            return False
        current = parent


def _regular_path(path: Path, code: str) -> Path:
    absolute = _absolute(path)
    _require(
        absolute.is_file() and not _has_symlink_component(absolute),
        f"{code}_invalid",
    )
    return absolute


def _directory_path(path: Path, code: str) -> Path:
    absolute = _absolute(path)
    _require(
        absolute.is_dir() and not _has_symlink_component(absolute),
        f"{code}_invalid",
    )
    return absolute


def _require_under(path: Path, parent: Path, code: str) -> Path:
    absolute = _absolute(path)
    root = _absolute(parent)
    try:
        absolute.relative_to(root)
    except ValueError:
        raise Task7VerificationError(code) from None
    return absolute


def _json_mapping(path: Path, code: str) -> dict[str, Any]:
    path = _regular_path(path, code)
    try:
        payload = json.loads(path.read_bytes())
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Task7VerificationError(f"{code}_json_invalid") from exc
    _require(isinstance(payload, dict), f"{code}_not_mapping")
    return payload


def _tree_inventory(root: Path) -> dict[str, Any]:
    root = _directory_path(root, "worker_private_cache")
    entries: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        _require(not path.is_symlink(), "worker_private_cache_symlink_forbidden")
        if not path.is_file():
            continue
        entries.append(
            {
                "path": path.relative_to(root).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": _file_hash(path),
            }
        )
    return {
        "file_count": len(entries),
        "bytes": sum(int(row["bytes"]) for row in entries),
        "inventory_root_sha256": _root(entries),
        "entries": entries,
    }


def _source_stat_identity(path: Path) -> dict[str, int]:
    path = _regular_path(path, "tick_source")
    stat = path.stat()
    return {
        "byte_count": int(stat.st_size),
        "ctime_ns": int(stat.st_ctime_ns),
        "device": int(stat.st_dev),
        "inode": int(stat.st_ino),
        "mtime_ns": int(stat.st_mtime_ns),
    }


def _scan_day(path: Path, *, allow_bucket_aggregate_rows: bool = False) -> dict[str, Any]:
    path = Path(path)
    _require(path.is_file() and not path.is_symlink(), "worker_role_file_missing")
    digest = hashlib.sha256()
    total_rows = 0
    day_rows = 0
    day_bytes = 0
    with path.open("rb") as handle:
        for raw in handle:
            total_rows += 1
            _require(raw.endswith(b"\n"), "worker_role_framing_invalid")
            row = json.loads(raw)
            _require(isinstance(row, dict), "worker_role_row_invalid")
            if "trading_day" not in row:
                _require(
                    allow_bucket_aggregate_rows
                    and row.get("row_type") == "bucket"
                    and row.get("profile")
                    and row.get("split"),
                    "worker_role_day_missing",
                )
                continue
            if row["trading_day"] == DAY:
                digest.update(raw)
                day_rows += 1
                day_bytes += len(raw)
    return {
        "file_sha256": _file_hash(path),
        "file_bytes": path.stat().st_size,
        "total_rows": total_rows,
        "day_rows": day_rows,
        "day_bytes": day_bytes,
        "ordered_day_bytes_sha256": digest.hexdigest(),
    }


def _verify_decision_rows(path: Path) -> None:
    day_rows = 0
    with _regular_path(path, "worker_decision_role").open("rb") as handle:
        for raw in handle:
            row = json.loads(raw)
            if row.get("trading_day") != DAY:
                continue
            day_rows += 1
            _require(
                row.get("b7_5_selection_sizing_factorial_arm_id") == "S0R0"
                and row.get("b7_5_selection_sizing_factorial_arm_fingerprint_sha256")
                == EXPECTED_ARM_FINGERPRINT
                and row.get("b7_5_selection_sizing_factorial_selection_factor") == "S0"
                and row.get("b7_5_selection_sizing_factorial_sizing_factor") == "R0"
                and row.get("b7_5_selection_sizing_factorial_uses_outcome_fields")
                is False
                and row.get("b7_5_selection_sizing_factorial_broker_mutation_enabled")
                is False
                and row.get("b7_5_selection_sizing_factorial_live_broker_authority")
                is False
                and row.get("broker_mutation_enabled") is False
                and row.get("live_broker_authority") is False,
                "worker_decision_arm_or_broker_binding_invalid",
            )
    _require(day_rows == 2304, "worker_decision_row_count_invalid")


def _reference_projection(root: Path) -> dict[str, Any]:
    root = _directory_path(root, "task6_reference_execution")
    projection: dict[str, Any] = {}
    for role in ROLE_NAMES:
        search_root = (
            Path(f"{root}.semantic-diagnostic")
            if role.startswith("semantic_")
            else root
        )
        search_root = _directory_path(search_root, f"task6_reference_{role}_root")
        paths = sorted(search_root.glob(f"*{ROLE_SUFFIXES[role]}"))
        _require(len(paths) == 1, f"task6_reference_role_missing:{role}")
        observed = _scan_day(
            paths[0], allow_bucket_aggregate_rows=(role == "bucket")
        )
        projection[role] = {
            "row_count": observed["day_rows"],
            "ordered_bytes_sha256": observed["ordered_day_bytes_sha256"],
        }
    return projection


def _verify_source_rebind(bound: Mapping[str, Any]) -> dict[str, Any]:
    _require(
        bound.get("schema")
        == "gtos.replay_acceleration.bound_source_bundle_consumer_rebind_authority.v1",
        "source_rebind_binding_schema_invalid",
    )
    binding_projection = dict(bound)
    binding_root = binding_projection.pop("binding_root_sha256", None)
    _require(binding_root == _root(binding_projection), "source_rebind_binding_root_invalid")
    authority_path = _regular_path(
        Path(str(bound.get("authority_path") or "")), "source_rebind_authority"
    )
    _require(
        _file_hash(authority_path) == EXPECTED_SOURCE_AUTHORITY_SHA256
        and bound.get("authority_file_sha256") == EXPECTED_SOURCE_AUTHORITY_SHA256,
        "source_rebind_authority_hash_invalid",
    )
    authority = _rooted_json(
        authority_path, "authority_root_sha256", "source_rebind_authority"
    )
    _require(
        authority.get("authority_root_sha256") == EXPECTED_SOURCE_AUTHORITY_ROOT
        and bound.get("authority_root_sha256") == EXPECTED_SOURCE_AUTHORITY_ROOT
        and bound.get("authority") == authority
        and authority.get("status")
        == "ACCEPTED_SOURCE_BYTES_IDENTICAL_IMPLEMENTATION_SUCCESSOR"
        and authority.get("broker_live_authority") is False
        and authority.get("policy_execution_entered") is False
        and authority.get("economic_values_exposed") is False
        and authority.get("selection_transformation", {}).get(
            "source_plan_digest_sha256"
        )
        == EXPECTED_SOURCE_PLAN_DIGEST,
        "source_rebind_authority_scope_invalid",
    )
    bundle_binding = bound.get("verified_successor_bundle")
    selection_binding = bound.get("verified_successor_selection")
    _require(
        isinstance(bundle_binding, Mapping)
        and isinstance(selection_binding, Mapping),
        "source_rebind_successor_binding_invalid",
    )
    bundle_path = _regular_path(
        Path(str(bundle_binding.get("path") or "")), "source_rebind_bundle"
    )
    bundle = _json_mapping(bundle_path, "source_rebind_bundle")
    bundle_projection = dict(bundle)
    bundle_root = bundle_projection.pop("bundle_root_sha256", None)
    _require(
        _file_hash(bundle_path) == EXPECTED_SOURCE_BUNDLE_SHA256
        and bundle_binding.get("file_sha256") == EXPECTED_SOURCE_BUNDLE_SHA256
        and bundle_root == EXPECTED_SOURCE_BUNDLE_ROOT
        and bundle_root == _root(bundle_projection)
        and bundle_binding.get("bundle_root_sha256") == bundle_root
        and bundle.get("accepted_cache_implementation_root")
        == EXPECTED_SOURCE_IMPLEMENTATION_ROOT
        and bundle_binding.get("implementation_root_sha256")
        == EXPECTED_SOURCE_IMPLEMENTATION_ROOT
        and bundle.get("expected_source_plan_digest_sha256")
        == EXPECTED_SOURCE_PLAN_DIGEST,
        "source_rebind_bundle_invalid",
    )
    seal_path = _regular_path(bundle_path.parent / "SEALED", "source_rebind_seal")
    _require(
        seal_path.read_bytes() == f"{bundle_root}\n".encode("ascii"),
        "source_rebind_seal_invalid",
    )
    selection_path = _regular_path(
        Path(str(selection_binding.get("path") or "")), "source_rebind_selection"
    )
    selection = _json_mapping(selection_path, "source_rebind_selection")
    selection_projection = dict(selection)
    selection_root = selection_projection.pop("selection_root_sha256", None)
    _require(
        _file_hash(selection_path) == EXPECTED_SOURCE_SELECTION_SHA256
        and selection_binding.get("file_sha256") == EXPECTED_SOURCE_SELECTION_SHA256
        and selection_root == EXPECTED_SOURCE_SELECTION_ROOT
        and selection_root == _root(selection_projection)
        and selection_binding.get("selection_root_sha256") == selection_root
        and selection.get("expected_source_plan_digest_sha256")
        == EXPECTED_SOURCE_PLAN_DIGEST
        and bundle.get("selection_root_sha256") == selection_root
        and bound.get("source_plan_digest_sha256") == EXPECTED_SOURCE_PLAN_DIGEST
        and bound.get("broker_live_authority") is False
        and bound.get("policy_execution_entered") is False,
        "source_rebind_selection_invalid",
    )
    return {
        "authority_root_sha256": EXPECTED_SOURCE_AUTHORITY_ROOT,
        "bundle_root_sha256": EXPECTED_SOURCE_BUNDLE_ROOT,
        "selection_root_sha256": EXPECTED_SOURCE_SELECTION_ROOT,
    }


def _verify_tick_cache(
    worker: Mapping[str, Any],
    *,
    verified_content: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    bypass = worker.get("authenticated_prepared_pack_tick_cache_superset_reuse")
    _require(isinstance(bypass, Mapping), "worker_tick_cache_binding_missing")
    namespace = _directory_path(Path(str(worker.get("namespace") or "")), "worker_namespace")
    receipt_path = _require_under(
        _regular_path(
            Path(str(bypass.get("prewarm_receipt") or "")),
            "worker_tick_cache_prewarm_receipt",
        ),
        namespace,
        "worker_tick_cache_prewarm_outside_namespace",
    )
    receipt_hash = _file_hash(receipt_path)
    _require(
        receipt_hash == bypass.get("prewarm_receipt_sha256"),
        "worker_tick_cache_prewarm_hash_invalid",
    )
    receipt = _json_mapping(receipt_path, "worker_tick_cache_prewarm_receipt")
    projection = dict(receipt)
    recorded_root = projection.pop("prewarm_root_sha256", None)
    projection.pop("non_authoritative_filesystem_storage_receipt", None)
    entries = projection.get("entries")
    _require(
        recorded_root == _root(projection)
        and receipt.get("schema")
        == "gtos.replay_acceleration.sparse_tick_cache_prewarm.v1"
        and receipt.get("status") == "SEALED_SPARSE_TICK_CACHE_PREWARM_COMPLETE"
        and receipt.get("window_start_utc") == EXPECTED_TICK_WINDOW_START
        and receipt.get("window_end_utc") == EXPECTED_TICK_WINDOW_END
        and receipt.get("broker_live_authority") is False
        and receipt.get("economic_values_exposed") is False
        and isinstance(entries, list)
        and len(entries) == 4
        and receipt.get("entry_count") == 4
        and receipt.get("raw_source_full_hash_count") == 0
        and receipt.get("sealed_cache_reuse_count") == 4
        and bypass.get("enabled") is True
        and bypass.get("tick_authority_still_bound") is True
        and bypass.get("window_end_after_day") == "2026-01-02"
        and bypass.get("raw_source_full_hash_count") == 0
        and bypass.get("sealed_cache_reuse_count") == 4,
        "worker_tick_cache_prewarm_scope_invalid",
    )
    cache_root = _directory_path(
        Path(str(bypass.get("tick_sparse_cache_root") or "")), "tick_cache_root"
    )
    _require(
        _absolute(Path(str(receipt.get("cache_root") or ""))) == cache_root,
        "worker_tick_cache_root_mismatch",
    )
    content_key = (str(cache_root), receipt_hash)
    if content_key not in verified_content:
        partition_count = 0
        retained_rows = 0
        manifest_roots: dict[str, str] = {}
        for entry in entries:
            _require(isinstance(entry, Mapping), "tick_cache_entry_invalid")
            identity_root = str(entry.get("identity_root_sha256") or "")
            entry_root = _directory_path(
                _require_under(
                    cache_root / identity_root,
                    cache_root,
                    "tick_cache_entry_outside_root",
                ),
                "tick_cache_entry_root",
            )
            manifest_path = _regular_path(
                entry_root / "manifest.json", "tick_cache_manifest"
            )
            manifest = _json_mapping(manifest_path, "tick_cache_manifest")
            manifest_projection = dict(manifest)
            manifest_root = manifest_projection.pop("manifest_root_sha256", None)
            _require(
                manifest_root == _root(manifest_projection)
                and manifest_root == entry.get("manifest_root_sha256")
                and manifest.get("identity_root_sha256") == identity_root
                and manifest.get("identity") is not None
                and _root(manifest["identity"]) == identity_root
                and manifest.get("partition_count") == entry.get("partition_count")
                and manifest.get("retained_row_count") == entry.get("retained_row_count")
                and manifest.get("broker_live_authority") is False
                and manifest.get("economic_values_exposed") is False,
                "tick_cache_manifest_binding_invalid",
            )
            _require(
                (entry_root / "SEALED").read_bytes()
                == f"{manifest_root}\n".encode("ascii"),
                "tick_cache_manifest_seal_invalid",
            )
            source_path = Path(str(entry.get("source_path") or ""))
            source_validation = entry.get("source_validation")
            _require(
                isinstance(source_validation, Mapping)
                and _source_stat_identity(source_path)
                == source_validation.get("source_stat_identity")
                == manifest.get("identity", {}).get("source_stat_identity")
                and entry.get("source_sha256")
                == source_validation.get("manifest_sha256")
                == manifest.get("identity", {}).get("source_sha256")
                and source_validation.get("raw_source_full_hash_performed") is False
                and source_validation.get("sha_validation_status")
                == "sealed_full_hash_attestation_reused",
                "tick_cache_source_attestation_invalid",
            )
            partitions = manifest.get("partitions")
            _require(isinstance(partitions, list), "tick_cache_partitions_invalid")
            for partition in partitions:
                _require(isinstance(partition, Mapping), "tick_cache_partition_invalid")
                partition_path = _require_under(
                    _regular_path(
                        entry_root / str(partition.get("path") or ""),
                        "tick_cache_partition",
                    ),
                    entry_root,
                    "tick_cache_partition_outside_entry",
                )
                _require(
                    partition_path.stat().st_size == partition.get("bytes")
                    and _file_hash(partition_path) == partition.get("sha256")
                    and sum(1 for _ in partition_path.open("rb"))
                    == partition.get("rows"),
                    "tick_cache_partition_binding_invalid",
                )
            partition_count += int(entry.get("partition_count") or 0)
            retained_rows += int(entry.get("retained_row_count") or 0)
            manifest_roots[str(entry.get("symbol") or "")] = str(manifest_root)
        _require(
            partition_count == receipt.get("partition_count")
            and retained_rows == receipt.get("retained_row_count"),
            "tick_cache_prewarm_totals_invalid",
        )
        verified_content[content_key] = {
            "prewarm_root_sha256": recorded_root,
            "manifest_roots": manifest_roots,
            "partition_count": partition_count,
        }
    return verified_content[content_key]


def _role_projection(worker: Mapping[str, Any]) -> dict[str, Any]:
    recorded_roles = worker.get("semantic_roles")
    _require(isinstance(recorded_roles, Mapping), "worker_roles_missing")
    projection: dict[str, Any] = {}
    for role in ROLE_NAMES:
        recorded = recorded_roles.get(role)
        _require(isinstance(recorded, Mapping), "worker_role_receipt_missing")
        observed = _scan_day(
            Path(str(recorded.get("path") or "")),
            allow_bucket_aggregate_rows=(role == "bucket"),
        )
        for field in (
            "file_sha256",
            "file_bytes",
            "total_rows",
            "day_rows",
            "day_bytes",
            "ordered_day_bytes_sha256",
        ):
            _require(
                recorded.get(field) == observed[field],
                f"worker_role_receipt_mismatch:{role}:{field}",
            )
        projection[role] = {
            "row_count": observed["day_rows"],
            "ordered_bytes_sha256": observed["ordered_day_bytes_sha256"],
        }
    _require(
        projection == worker.get("semantic_projection"),
        "worker_semantic_projection_mismatch",
    )
    _require(
        _root(projection) == worker.get("semantic_projection_root_sha256"),
        "worker_semantic_projection_root_mismatch",
    )
    _verify_decision_rows(Path(str(recorded_roles["decision"]["path"])))
    return projection


def _verify_worker_artifacts(
    worker: Mapping[str, Any],
    *,
    worker_path: Path,
    expected_logical_arm: str,
    expected_worker_kind: str,
    pack_root: Path,
    verified_tick_content: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    _require(
        worker.get("schema") == WORKER_SCHEMA
        and worker.get("status") == "TASK7_ISOLATED_BASELINE_REDUCER_COMPLETE"
        and worker.get("logical_arm_id") == expected_logical_arm
        and worker.get("worker_kind") == expected_worker_kind
        and worker.get("executed_baseline_arm_id") == "S0R0"
        and worker.get("factorial_policy_execution") is False
        and worker.get("live_broker_authority") is False
        and worker.get("broker_mutation_enabled") is False
        and worker.get("real_order_transmission_possible") is False,
        "worker_scope_or_live_boundary_invalid",
    )
    namespace = _directory_path(Path(str(worker.get("namespace") or "")), "worker_namespace")
    _require_under(
        _regular_path(worker_path, "worker_receipt"),
        namespace,
        "worker_receipt_outside_namespace",
    )
    private = worker.get("private_namespaces")
    _require(isinstance(private, Mapping), "worker_private_namespaces_missing")
    output_path = _absolute(Path(str(private.get("output") or "")))
    cache_path = _directory_path(
        Path(str(private.get("typed_source_cache") or "")), "worker_private_cache"
    )
    compact_path = _absolute(Path(str(private.get("compact_event_sink") or "")))
    _require(
        output_path == namespace
        and _require_under(cache_path, namespace, "worker_cache_outside_namespace")
        == cache_path
        and _require_under(compact_path, namespace, "worker_compact_outside_namespace")
        == compact_path,
        "worker_private_namespace_binding_invalid",
    )
    request = worker.get("request")
    _require(isinstance(request, Mapping), "worker_request_binding_missing")
    request_path = _regular_path(
        Path(str(request.get("path") or "")), "worker_request"
    )
    task_root = namespace.parent.parent
    _require_under(
        request_path,
        task_root / "requests",
        "worker_request_outside_task_requests",
    )
    request_raw = request_path.read_bytes()
    request_payload = json.loads(request_raw)
    request_projection = dict(request_payload)
    request_root = request_projection.pop("request_root_sha256", None)
    _require(
        hashlib.sha256(request_raw).hexdigest() == request.get("file_sha256")
        and request_root == _root(request_projection)
        and request_root == request.get("request_root_sha256")
        and request_payload.get("schema")
        == "gtos.replay_acceleration.task7.worker_spec.v1"
        and request_payload.get("logical_arm_id") == expected_logical_arm
        and request_payload.get("worker_kind") == expected_worker_kind
        and request_payload.get("executed_baseline_arm_id") == "S0R0"
        and _absolute(Path(str(request_payload.get("output_dir") or "")))
        == namespace
        and _absolute(Path(str(request_payload.get("prepared_day_pack_root") or "")))
        == pack_root.parent.parent
        and request_payload.get("expected_prepared_day_pack_root_sha256")
        == PACK_SHA256
        and request_payload.get("task6_acceptance_receipt_sha256")
        == TASK6_FILE_SHA256,
        "worker_request_binding_invalid",
    )
    execution = worker.get("execution_contract")
    _require(
        isinstance(execution, Mapping)
        and execution.get("arm_id") == "S0R0"
        and execution.get("arm_fingerprint_sha256") == EXPECTED_ARM_FINGERPRINT
        and execution.get("source_plan_digest_sha256")
        == EXPECTED_SOURCE_PLAN_DIGEST
        and execution.get("shared_execution_contract_digest_sha256")
        == EXPECTED_SHARED_EXECUTION_DIGEST
        and execution.get("runtime_input_contract_root_sha256")
        == EXPECTED_RUNTIME_INPUT_ROOT,
        "worker_execution_contract_invalid",
    )
    broker = worker.get("broker_boundary")
    _require(
        isinstance(broker, Mapping)
        and broker.get("broker_adapter") == "SimulatedBroker"
        and broker.get("order_send_attempts") == 0
        and broker.get("broker_mutation_enabled") is False
        and broker.get("broker_account_order_history_deal_position_mutation")
        is False,
        "worker_broker_boundary_invalid",
    )
    partial_binding = worker.get("partial_summary")
    _require(isinstance(partial_binding, Mapping), "worker_partial_summary_missing")
    partial_path = _require_under(
        _regular_path(
            Path(str(partial_binding.get("path") or "")), "worker_partial_summary"
        ),
        namespace,
        "worker_partial_summary_outside_namespace",
    )
    _require(
        _file_hash(partial_path) == partial_binding.get("file_sha256")
        and partial_path.stat().st_size == partial_binding.get("bytes"),
        "worker_partial_summary_hash_invalid",
    )
    partial = _json_mapping(partial_path, "worker_partial_summary")
    progress = partial.get("progress_rows")
    _require(
        partial.get("status") == "partial_in_progress_not_final_proof"
        and partial.get("live_broker_authority") is False
        and partial.get("broker_mutation_enabled") is False
        and partial.get("final_selection_claim") is False
        and isinstance(progress, list)
        and len(progress) == 1,
        "worker_partial_summary_scope_invalid",
    )
    progress_row = progress[0]
    progress_broker = progress_row.get("broker_boundary")
    _require(
        progress_row.get("live_broker_authority") is False
        and progress_row.get("broker_mutation_enabled") is False
        and progress_row.get("selected_order_sequence") == 0
        and progress_broker == broker
        and progress_row.get("campaign_exact_cache", {}).get(
            "live_broker_authority"
        )
        is False
        and progress_row.get("campaign_exact_cache", {}).get(
            "broker_mutation_enabled"
        )
        is False,
        "worker_partial_progress_broker_boundary_invalid",
    )
    arm_binding = partial.get("b7_5_selection_sizing_factorial_arm_binding")
    contract_binding = partial.get("b7_5_contract_binding")
    shared = partial.get("shared_execution_contract")
    _require(
        isinstance(arm_binding, Mapping)
        and arm_binding.get("arm_id") == "S0R0"
        and arm_binding.get("arm_fingerprint_sha256") == EXPECTED_ARM_FINGERPRINT
        and arm_binding.get("broker_mutation_enabled") is False
        and arm_binding.get("live_broker_authority") is False
        and isinstance(contract_binding, Mapping)
        and contract_binding.get("actual_shared_execution_contract_digest_sha256")
        == EXPECTED_SHARED_EXECUTION_DIGEST
        and contract_binding.get("expected_shared_execution_contract_digest_sha256")
        == EXPECTED_SHARED_EXECUTION_DIGEST
        and contract_binding.get("expected_source_plan_digest_sha256")
        == EXPECTED_SOURCE_PLAN_DIGEST
        and isinstance(shared, Mapping)
        and shared.get("shared_execution_contract_digest_sha256")
        == EXPECTED_SHARED_EXECUTION_DIGEST
        and shared.get("broker_live_final_authority", {}).get(
            "live_broker_authority"
        )
        is False
        and shared.get("broker_live_final_authority", {}).get(
            "broker_mutation_enabled"
        )
        is False
        and partial.get("ultimate_package_runtime_input_contract", {}).get(
            "live_broker_authority"
        )
        is False
        and partial.get("ultimate_package_runtime_input_contract", {}).get(
            "broker_mutation_enabled"
        )
        is False,
        "worker_partial_execution_contract_invalid",
    )
    source = partial.get("source_acceleration_authority")
    _require(
        isinstance(source, Mapping)
        and source.get("source_plan_digest_sha256")
        == EXPECTED_SOURCE_PLAN_DIGEST
        and source.get("source_bundle_root_sha256") == EXPECTED_SOURCE_BUNDLE_ROOT
        and source.get("selection_root_sha256") == EXPECTED_SOURCE_SELECTION_ROOT
        and source.get("policy_execution_entered") is False,
        "worker_partial_source_authority_invalid",
    )
    source_rebind = source.get("source_bundle_consumer_rebind_authority")
    _require(isinstance(source_rebind, Mapping), "worker_source_rebind_missing")
    source_roots = _verify_source_rebind(source_rebind)
    shared_source_rebind = (
        shared.get("execution_options", {})
        .get("source_acceleration", {})
        .get("source_bundle_consumer_rebind_authority")
    )
    _require(
        shared_source_rebind == source_rebind,
        "worker_shared_source_rebind_mismatch",
    )
    tick_roots = _verify_tick_cache(
        worker, verified_content=verified_tick_content
    )
    seed = worker.get("private_typed_cache_seed")
    _require(isinstance(seed, Mapping), "worker_private_cache_seed_missing")
    inventory = _tree_inventory(cache_path)
    seed_source = _directory_path(
        Path(str(seed.get("source") or "")), "worker_private_cache_seed_source"
    )
    source_inventory = _tree_inventory(seed_source)
    destination_rows = {
        str(row["path"]): row for row in inventory["entries"]
    }
    source_rows = {
        str(row["path"]): row for row in source_inventory["entries"]
    }
    _require(
        _absolute(Path(str(seed.get("destination") or ""))) == cache_path
        and seed.get("private_copy_not_shared_mutable_cache") is True
        and seed.get("file_count") == source_inventory["file_count"]
        and seed.get("bytes") == source_inventory["bytes"]
        and seed.get("inventory_root_sha256")
        == source_inventory["inventory_root_sha256"]
        and inventory["file_count"] >= source_inventory["file_count"]
        and inventory["bytes"] >= source_inventory["bytes"]
        and all(destination_rows.get(path) == row for path, row in source_rows.items()),
        "worker_private_cache_inventory_invalid",
    )
    return {
        "namespace": str(namespace),
        "typed_cache": str(cache_path),
        "request_root_sha256": request_root,
        "source_roots": source_roots,
        "tick_roots": tick_roots,
        "private_cache_inventory_root_sha256": inventory[
            "inventory_root_sha256"
        ],
        "private_cache_seed_inventory_root_sha256": source_inventory[
            "inventory_root_sha256"
        ],
    }


def _verify_timeline(
    worker: Mapping[str, Any],
    *,
    decision_times: Sequence[str],
) -> str:
    state_receipt = worker["semantic_roles"]["semantic_state"]
    state_path = Path(str(state_receipt["path"]))
    rows = [
        json.loads(raw)
        for raw in state_path.read_bytes().splitlines()
        if raw and json.loads(raw).get("trading_day") == DAY
    ]
    _require(
        [row.get("boundary") for row in rows] == ["pre_day", "post_day"],
        "worker_state_boundaries_invalid",
    )
    broker = worker.get("broker_boundary")
    _require(isinstance(broker, Mapping), "worker_broker_boundary_missing")
    for row in rows:
        account = row.get("account_preimage")
        state = row.get("state_projection")
        _require(isinstance(account, Mapping), "worker_account_preimage_invalid")
        _require(isinstance(state, Mapping), "worker_state_projection_invalid")
        reservations = {
            key: account.get(key)
            for key in (
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
        }
        expected_state = {
            "schema": "gtos.replay_acceleration.pre_day_state.v1",
            "account_root_sha256": _root(account),
            "broker_root_sha256": _root(broker),
            "event_queue_root_sha256": _root(account.get("event_queue", [])),
            "reservation_root_sha256": _root(reservations),
            "selected_order_sequence": 0,
        }
        _require(dict(state) == expected_state, "worker_state_projection_invalid")
        _require(row.get("state_root_sha256") == _root(expected_state), "worker_state_root_invalid")
    expected_post = copy.deepcopy(rows[0]["account_preimage"])
    expected_post["daily_start_balance"].setdefault(DAY, expected_post["balance"])
    _require(
        expected_post == rows[1]["account_preimage"],
        "worker_no_event_transition_invalid",
    )
    _require(
        not rows[1]["account_preimage"]["event_queue"]
        and not rows[1]["account_preimage"]["pending_orders"]
        and not rows[1]["account_preimage"]["open_positions"]
        and not rows[1]["account_preimage"]["closed_trades"]
        and rows[1]["account_preimage"]["event_sequence"] == 0,
        "worker_no_event_state_not_empty",
    )
    timeline = [
        {
            "decision_time_utc": timestamp,
            "state_root_sha256": rows[1]["state_root_sha256"],
        }
        for timestamp in decision_times
    ]
    timeline_receipt = worker.get("no_event_state_timeline")
    _require(isinstance(timeline_receipt, Mapping), "worker_timeline_missing")
    _require(
        timeline_receipt.get("timestamp_count") == len(timeline)
        and timeline_receipt.get("timeline_root_sha256") == _root(timeline)
        and timeline_receipt.get("scope")
        in {
            "no_event_day_exact_window_state_timeline",
            "no_event_day_derived_invariant_timeline",
        },
        "worker_timeline_root_mismatch",
    )
    if timeline_receipt.get("scope") == "no_event_day_derived_invariant_timeline":
        _require(
            timeline_receipt.get("observed_state_checkpoint_count") == 2
            and timeline_receipt.get("per_window_state_observed") is False,
            "worker_derived_timeline_scope_invalid",
        )
    return _root(timeline)


def verify_task7_acceptance(path: Path) -> dict[str, Any]:
    acceptance = _rooted_json(path, "receipt_root_sha256", "task7_acceptance")
    _require(acceptance.get("schema") == ACCEPTANCE_SCHEMA, "acceptance_schema_invalid")
    _require(
        acceptance.get("status") == "TASK7_ISOLATED_CHRONOLOGICAL_REDUCERS_ACCEPTED"
        and acceptance.get("task_gate_authorized") is True
        and acceptance.get("acceptance_authorized") is False,
        "acceptance_status_invalid",
    )
    _require(
        acceptance.get("semantic_or_economic_difference_count") == 0
        and acceptance.get("unknown_difference_count") == 0,
        "acceptance_difference_count_invalid",
    )
    task6 = acceptance.get("task6_acceptance")
    _require(isinstance(task6, Mapping), "task6_binding_missing")
    task6_path = Path(str(task6.get("path") or ""))
    _require(_file_hash(task6_path) == TASK6_FILE_SHA256, "task6_file_hash_mismatch")
    task6_payload = _rooted_json(task6_path, "receipt_root_sha256", "task6_acceptance")
    _require(
        task6_payload.get("receipt_root_sha256") == TASK6_ROOT_SHA256,
        "task6_root_mismatch",
    )
    pack = acceptance.get("prepared_day_pack")
    _require(isinstance(pack, Mapping), "pack_binding_missing")
    pack_path = Path(str(pack.get("path") or ""))
    reader = PreparedDayPackReader(pack_path, expected_pack_root_sha256=PACK_SHA256)
    inventory = reader.manifest.get("window_inventory")
    _require(isinstance(inventory, list) and len(inventory) == 96, "pack_inventory_invalid")
    decision_times: list[str] = []
    for ordinal, row in enumerate(inventory):
        record = reader.next_window(
            trading_day=DAY,
            decision_time_utc=str(row["decision_time_utc"]),
            window_ordinal=ordinal,
        )
        _require(
            record.get("calendar_no_session_breadth_guard", {}).get("active") is True,
            "pack_no_event_guard_invalid",
        )
        _require(
            all(symbol.get("status") == "source_skipped" for symbol in record["symbols"]),
            "pack_no_event_symbol_status_invalid",
        )
        decision_times.append(str(record["decision_time_utc"]))
    reader.finish()
    _require(
        pack.get("decision_time_root_sha256") == _root(decision_times),
        "pack_decision_time_root_mismatch",
    )
    reference_root = Path(str(acceptance.get("reference_execution_root") or ""))
    task6_reference_projection = _reference_projection(reference_root)
    verified_tick_content: dict[tuple[str, str], dict[str, Any]] = {}

    baseline_binding = acceptance.get("baseline")
    _require(isinstance(baseline_binding, Mapping), "baseline_binding_missing")
    baseline_path = Path(str(baseline_binding.get("path") or ""))
    _require(
        _file_hash(baseline_path) == baseline_binding.get("file_sha256"),
        "baseline_file_hash_mismatch",
    )
    baseline = _rooted_json(
        baseline_path, "worker_receipt_root_sha256", "baseline_worker"
    )
    baseline_artifacts = _verify_worker_artifacts(
        baseline,
        worker_path=baseline_path,
        expected_logical_arm="S0R0",
        expected_worker_kind="baseline",
        pack_root=pack_path,
        verified_tick_content=verified_tick_content,
    )
    baseline_projection = _role_projection(baseline)
    baseline_timeline = _verify_timeline(baseline, decision_times=decision_times)
    _require(
        baseline.get("schema") == WORKER_SCHEMA
        and baseline.get("executed_baseline_arm_id") == "S0R0"
        and baseline.get("factorial_policy_execution") is False,
        "baseline_worker_scope_invalid",
    )
    expected_task6_parity = {
        "status": "EXACT_ORDERED_JAN1_ROLE_PARITY",
        "role_count": len(ROLE_NAMES),
        "projection_root_sha256": _root(task6_reference_projection),
        "roles": task6_reference_projection,
    }
    _require(
        task6_reference_projection == baseline_projection
        and baseline_binding.get("task6_jan1_exact_parity")
        == expected_task6_parity,
        "baseline_task6_reference_parity_invalid",
    )

    logical_bindings = acceptance.get("logical_arms")
    _require(isinstance(logical_bindings, Mapping), "logical_bindings_missing")
    _require(set(logical_bindings) == set(ARMS), "logical_arm_set_invalid")
    pids = {int(baseline["worker_pid"])}
    namespaces = {str(baseline["namespace"])}
    caches = {str(baseline["private_namespaces"]["typed_source_cache"])}
    request_roots = {str(baseline_artifacts["request_root_sha256"])}
    canonical: dict[str, Any] = {}
    for arm in ARMS:
        binding = logical_bindings[arm]
        _require(isinstance(binding, Mapping), "logical_binding_invalid")
        worker_path = Path(str(binding.get("path") or ""))
        _require(
            _file_hash(worker_path) == binding.get("file_sha256"),
            "logical_worker_file_hash_mismatch",
        )
        worker = _rooted_json(
            worker_path, "worker_receipt_root_sha256", "logical_worker"
        )
        worker_artifacts = _verify_worker_artifacts(
            worker,
            worker_path=worker_path,
            expected_logical_arm=arm,
            expected_worker_kind="logical_arm",
            pack_root=pack_path,
            verified_tick_content=verified_tick_content,
        )
        _require(
            worker.get("schema") == WORKER_SCHEMA
            and worker.get("logical_arm_id") == arm
            and worker.get("executed_baseline_arm_id") == "S0R0"
            and worker.get("factorial_policy_execution") is False,
            "logical_worker_scope_invalid",
        )
        projection = _role_projection(worker)
        timeline = _verify_timeline(worker, decision_times=decision_times)
        _require(projection == baseline_projection, "logical_worker_semantic_mismatch")
        _require(timeline == baseline_timeline, "logical_worker_timeline_mismatch")
        pids.add(int(worker["worker_pid"]))
        namespaces.add(str(worker["namespace"]))
        caches.add(str(worker["private_namespaces"]["typed_source_cache"]))
        request_roots.add(str(worker_artifacts["request_root_sha256"]))
        canonical[arm] = {
            "executed_baseline_arm_id": "S0R0",
            "semantic_projection_root_sha256": _root(projection),
            "timeline_root_sha256": timeline,
        }
    _require(len(pids) == 5, "worker_pid_isolation_invalid")
    _require(len(namespaces) == 5, "worker_namespace_isolation_invalid")
    _require(len(caches) == 5, "worker_cache_isolation_invalid")
    _require(len(request_roots) == 5, "worker_request_isolation_invalid")
    aggregate = acceptance.get("canonical_aggregate")
    _require(isinstance(aggregate, Mapping), "aggregate_missing")
    aggregate_root = _root(canonical)
    legacy_order_claim = aggregate.get("order_independent") is True
    corrected_order_claim = (
        aggregate.get("canonical_mapping_serialization_order_independent") is True
        and aggregate.get("execution_order_independence_claimed") is False
    )
    _require(
        aggregate.get("root_sha256") == aggregate_root
        and aggregate.get("reverse_materialization_root_sha256") == aggregate_root
        and aggregate.get("launch_order") == list(reversed(ARMS))
        and aggregate.get("canonical_order") == list(ARMS)
        and (legacy_order_claim or corrected_order_claim),
        "aggregate_root_invalid",
    )
    for resource_scope in ("baseline", "four_logical_arms"):
        resources = acceptance.get("resources", {}).get(resource_scope)
        _require(isinstance(resources, Mapping), "resource_receipt_missing")
        expected_workers = 1 if resource_scope == "baseline" else 2
        swap_start = int(resources.get("swap_out_start_bytes") or 0)
        swap_end = int(resources.get("swap_out_end_bytes") or 0)
        swap_growth = max(0, swap_end - swap_start)
        _require(
            int(resources.get("sample_count") or 0) > 0
            and int(resources.get("configured_max_workers") or 0)
            == expected_workers
            and 1 <= int(resources.get("peak_active_workers") or 0)
            <= expected_workers
            and int(resources.get("peak_aggregate_child_tree_rss_bytes") or 0)
            <= int(resources.get("max_aggregate_rss_bytes") or -1)
            and int(resources.get("minimum_host_available_memory_bytes") or 0)
            >= CRITICAL_HOST_AVAILABLE_BYTES
            and int(resources.get("swap_used_peak_bytes") or 0)
            >= int(resources.get("swap_used_start_bytes") or 0)
            and int(resources.get("swap_used_peak_bytes") or 0)
            >= int(resources.get("swap_used_end_bytes") or 0)
            and swap_growth == int(resources.get("raw_swap_out_growth_bytes") or 0)
            and swap_growth
            <= int(resources.get("material_swap_growth_budget_bytes") or -1)
            and resources.get("material_swap_growth_detected") is False
            and resources.get("memory_pressure_failure") is False
            and resources.get("swap_counter_scope")
            == "machine_wide_not_child_attributable",
            "resource_gate_invalid",
        )
    _require(
        acceptance.get("live_broker_authority") is False
        and acceptance.get("broker_mutation_enabled") is False
        and acceptance.get("real_order_transmission_possible") is False,
        "acceptance_live_boundary_invalid",
    )
    core = {
        "schema": "gtos.replay_acceleration.task7.independent_verification.v1",
        "status": "TASK7_INDEPENDENT_VERIFICATION_PASS_REVIEW_REPAIRED",
        "receipt_root_sha256": acceptance["receipt_root_sha256"],
        "baseline_semantic_projection_root_sha256": _root(baseline_projection),
        "task6_reference_projection_root_sha256": _root(
            task6_reference_projection
        ),
        "derived_no_event_invariant_timeline_root_sha256": baseline_timeline,
        "observed_state_checkpoint_count_per_worker": 2,
        "per_window_state_observation_claimed": False,
        "canonical_mapping_serialization_independence": True,
        "execution_order_independence_claimed": False,
        "legacy_order_claim_narrowed": legacy_order_claim,
        "logical_arm_count": 4,
        "worker_process_count": 5,
        "worker_request_count": 5,
        "private_typed_cache_count": 5,
        "authenticated_sparse_tick_manifest_count": 4,
        "semantic_or_economic_difference_count": 0,
        "unknown_difference_count": 0,
        "live_broker_authority": False,
        "broker_mutation_enabled": False,
        "real_order_transmission_possible": False,
        "acceptance_authorized": False,
    }
    return {**core, "verification_root_sha256": _root(core)}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("acceptance", type=Path)
    parser.add_argument("--receipt", type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    result = verify_task7_acceptance(args.acceptance)
    rendered = _canonical(result) + b"\n"
    if args.receipt is not None:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.receipt.with_name(f".{args.receipt.name}.tmp-{os.getpid()}")
        temporary.write_bytes(rendered)
        os.replace(temporary, args.receipt)
    print(rendered.decode("ascii").rstrip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
