#!/usr/bin/env python3
"""Final exact end-to-end validation for the accepted replay accelerator.

Task 9 measures the real Jan 1-2 S0R0 replay route.  Cache classes are derived
from authenticated disk state, every timing trial independently re-proves Task
8 semantic parity, and persisted receipts remain outcome-blind.
"""

from __future__ import annotations

import argparse
import errno
import hashlib
import json
import math
import os
import signal
import stat
import statistics
import subprocess
import sys
import time
import uuid
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from src.research_infra import replay_acceleration_integrated_source as integrated
from src.research_infra import replay_acceleration_progressive_benchmark as benchmark
from src.research_infra import replay_acceleration_slice as slice_metrics
from src.research_infra import replay_acceleration_task7_isolated_runner as task7
from src.research_infra import replay_acceleration_task8_profile_runner as task8


ROOT = Path(__file__).resolve().parents[2]
MODULE_NAME = "src.research_infra.replay_acceleration_task9_final_validation"
TASK8_ACCEPTED_NAMESPACE = ROOT / (
    "research/operations/"
    "final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/"
    "attempt_5_typed_sparse/"
    "TASK8_REVIEW_REPAIRED_R5_JAN1_2_20260723T103000Z"
)
TASK8_ACCEPTED_PROFILE = TASK8_ACCEPTED_NAMESPACE / task8.PROFILE_RECEIPT_NAME
TASK8_ACCEPTED_TYPED_CACHE = TASK8_ACCEPTED_NAMESPACE / "typed-cache"
TASK8_ACCEPTED_PREWARM = (
    TASK8_ACCEPTED_NAMESPACE / "ATTEMPT5_TICK_SPARSE_CACHE_PREWARM_RECEIPT.json"
)

TASK9_LAUNCH_NONCE_ENV = "GTOS_TASK9_LAUNCH_NONCE"
COLD_PROCESS_STATE = "sealed_cache_cold_process"
WARM_FILESYSTEM_STATE = "warm_filesystem"
CACHE_AUTHORITY_SCHEMA = "gtos.replay_acceleration.task9.typed_cache_authority.v2"
CACHE_AUTHORITY_STATUS = "TASK9_DERIVED_COLD_TYPED_CACHE_SEALED"
PRIMING_REQUEST_SCHEMA = "gtos.replay_acceleration.task9.priming_request.v2"
PRIMING_RECEIPT_SCHEMA = "gtos.replay_acceleration.task9.priming_receipt.v2"
PRIMING_STATUS = "TASK9_CACHE_INPUTS_PRIMED"
TRIAL_REQUEST_SCHEMA = "gtos.replay_acceleration.task9.trial_request.v2"
TRIAL_RECEIPT_SCHEMA = "gtos.replay_acceleration.task9.trial_receipt.v2"
TRIAL_STATUS = "TASK9_EXACT_TRIAL_PARITY_GREEN"
TRIAL_SEAL_SCHEMA = "gtos.replay_acceleration.task9.trial_seal.v2"
OBSERVATION_SCHEMA = "gtos.replay_acceleration.task9.parent_observation.v1"
PRELIMINARY_SCHEMA = "gtos.replay_acceleration.task9.preliminary_validation.v1"
PRELIMINARY_STATUS = "TASK9_FINAL_VALIDATION_COMPLETE_REVIEW_PENDING"
REVIEW_REBIND_SCHEMA = "gtos.replay_acceleration.task9.review_rebind.v1"
REVIEW_REBIND_STATUS = "TASK9_COMPLETED_TRIALS_CONTENT_BOUND_REVIEW_PENDING"
FINAL_VALIDATION_SCHEMA = "gtos.replay_acceleration.task9.final_validation.v2"
FINAL_VALIDATION_STATUS = "TASK9_FINAL_VALIDATION_NAMESPACE_SEALED_REVIEW_PENDING"

LEGACY_CACHE_AUTHORITY_SCHEMA = (
    "gtos.replay_acceleration.task9.typed_cache_authority.v1"
)
LEGACY_PRIMING_REQUEST_SCHEMA = "gtos.replay_acceleration.task9.priming_request.v1"
LEGACY_PRIMING_RECEIPT_SCHEMA = "gtos.replay_acceleration.task9.priming_receipt.v1"
LEGACY_TRIAL_REQUEST_SCHEMA = "gtos.replay_acceleration.task9.trial_request.v1"
LEGACY_TRIAL_RECEIPT_SCHEMA = "gtos.replay_acceleration.task9.trial_receipt.v1"
LEGACY_TRIAL_SEAL_SCHEMA = "gtos.replay_acceleration.task9.trial_seal.v1"

TRIAL_RECEIPT_NAME = "TASK9_EXACT_TRIAL_RECEIPT.json"
TRIAL_SEAL_NAME = "TASK9_EXACT_TRIAL.SEALED.json"
PRELIMINARY_RECEIPT_NAME = "TASK9_FINAL_VALIDATION_PRELIMINARY.json"
REVIEW_REBIND_RECEIPT_NAME = "TASK9_FINAL_VALIDATION_REVIEW_REBIND.json"
FINAL_VALIDATION_RECEIPT_SUFFIX = ".TASK9_FINAL_VALIDATION.SEALED.json"
TRIAL_ENVELOPE_PATHS = frozenset({TRIAL_RECEIPT_NAME, TRIAL_SEAL_NAME})
TRIAL_TIMEOUT_SECONDS = 3600.0
PRIMING_TIMEOUT_SECONDS = 1800.0
TASK9_REQUIRED_STAGE_ENTRIES = frozenset(
    {
        "startup",
        "source_slicing",
        "generation",
        "evaluation",
        "scheduler_risk",
        "path_oracle",
        "broker_mutation",
        "proof_emission",
        "archive_seal",
        "verification",
    }
)
TASK9_REQUIRED_CALL_COUNTERS = frozenset(
    {
        "scheduler_config",
        "decision_times_for_day",
        "calendar_no_session_breadth_guard",
        "prepared_candidates_read",
        "evaluate_candidate",
        "schedule_window",
        "path_source_and_oracle",
        "process_events_until_window",
        "simulate_order",
        "process_events_until_day_end",
        "build_rollup_rows",
        "sort_event_ledgers",
    }
)

STANDARDIZED_WORKLOAD_COUNTS = {
    "one_month": {"dense_days": 21, "no_event_days": 1},
    "two_months": {"dense_days": 42, "no_event_days": 2},
    "six_months": {"dense_days": 126, "no_event_days": 6},
}
FORBIDDEN_RECEIPT_FIELDS = benchmark.FORBIDDEN_FULL_REPLAY_RETURN_FIELDS


class Task9Rejected(RuntimeError):
    """The final acceleration validation failed closed."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_bytes(canonical_bytes(dict(payload)) + b"\n")
    os.replace(temporary, path)


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(
        character in "009abcdef" for character in value
    )


def _load_rooted_json(
    path: Path,
    *,
    root_field: str,
    code: str,
    expected_file_sha256: str | None = None,
    require_canonical_bytes: bool = True,
) -> dict[str, Any]:
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise Task9Rejected(f"{code}_missing")
    raw = path.read_bytes()
    if expected_file_sha256 is not None and (
        not _is_sha256(expected_file_sha256)
        or hashlib.sha256(raw).hexdigest() != expected_file_sha256
    ):
        raise Task9Rejected(f"{code}_file_hash_invalid")
    try:
        payload = json.loads(raw)
    except (UnicodeError, json.JSONDecodeError):
        raise Task9Rejected(f"{code}_json_invalid") from None
    if not isinstance(payload, dict) or (
        require_canonical_bytes and raw != canonical_bytes(payload) + b"\n"
    ):
        raise Task9Rejected(f"{code}_canonical_bytes_invalid")
    projection = dict(payload)
    observed = projection.pop(root_field, None)
    if not _is_sha256(observed) or observed != stable_sha256(projection):
        raise Task9Rejected(f"{code}_root_invalid")
    return payload


def inventory_tree(
    root: Path,
    *,
    excluded_relative_paths: Iterable[str] = (),
) -> dict[str, Any]:
    """Hash one immutable tree without following or tolerating symlinks."""

    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise Task9Rejected("task9_inventory_root_invalid")
    excluded = frozenset(str(value) for value in excluded_relative_paths)
    if any(
        not value
        or value.startswith("/")
        or Path(value).as_posix() != value
        or ".." in Path(value).parts
        for value in excluded
    ):
        raise Task9Rejected("task9_inventory_exclusion_invalid")
    rows: list[dict[str, Any]] = []
    allocated = 0
    for base, directories, filenames in os.walk(root, followlinks=False):
        base_path = Path(base)
        for directory in list(directories):
            child = base_path / directory
            if child.is_symlink():
                raise Task9Rejected("task9_inventory_symlink_forbidden")
        for filename in filenames:
            path = base_path / filename
            relative = path.relative_to(root).as_posix()
            if relative in excluded:
                continue
            if path.is_symlink():
                raise Task9Rejected("task9_inventory_symlink_forbidden")
            info = path.stat(follow_symlinks=False)
            if not stat.S_ISREG(info.st_mode):
                raise Task9Rejected("task9_inventory_nonregular_file")
            rows.append(
                {
                    "path": relative,
                    "bytes": int(info.st_size),
                    "sha256": file_sha256(path),
                }
            )
            allocated += int(getattr(info, "st_blocks", 0) * 512)
    rows.sort(key=lambda row: row["path"])
    if not rows:
        raise Task9Rejected("task9_inventory_empty")
    return {
        "root": str(root.resolve()),
        "file_count": len(rows),
        "logical_bytes": sum(int(row["bytes"]) for row in rows),
        "allocated_bytes": allocated,
        "inventory_root_sha256": stable_sha256(rows),
        "files": rows,
    }


def validate_inventory_binding(
    root: Path,
    declared: Mapping[str, Any],
    *,
    excluded_relative_paths: Iterable[str] = (),
) -> dict[str, Any]:
    files = declared.get("files")
    if not isinstance(files, list) or stable_sha256(files) != declared.get(
        "inventory_root_sha256"
    ):
        raise Task9Rejected("task9_evidence_inventory_declaration_invalid")
    try:
        current = inventory_tree(
            root,
            excluded_relative_paths=excluded_relative_paths,
        )
    except Task9Rejected as exc:
        if str(exc) == "task9_inventory_empty":
            raise Task9Rejected("task9_evidence_inventory_drift") from None
        raise
    if current != dict(declared):
        raise Task9Rejected("task9_evidence_inventory_drift")
    return current


def _compact_inventory(inventory: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: inventory[key]
        for key in (
            "root",
            "file_count",
            "logical_bytes",
            "allocated_bytes",
            "inventory_root_sha256",
        )
    }


def _inventory_set(inventory: Mapping[str, Any]) -> set[tuple[str, int, str]]:
    return {
        (str(row["path"]), int(row["bytes"]), str(row["sha256"]))
        for row in inventory["files"]
    }


def _contained_path(path: Path, root: Path, *, code: str) -> Path:
    try:
        resolved = Path(path).resolve(strict=True)
        resolved.relative_to(Path(root).resolve(strict=True))
    except (OSError, ValueError):
        raise Task9Rejected(code) from None
    return resolved


def _subtree_inventory(
    parent_inventory: Mapping[str, Any],
    *,
    relative_root: str,
    root_path: Path,
) -> dict[str, Any]:
    prefix = relative_root.rstrip("/") + "/"
    rows = []
    for raw in parent_inventory.get("files", ()):
        if not isinstance(raw, Mapping):
            raise Task9Rejected("task9_parent_inventory_invalid")
        path = str(raw.get("path") or "")
        if path.startswith(prefix):
            rows.append(
                {
                    "path": path[len(prefix) :],
                    "bytes": int(raw["bytes"]),
                    "sha256": str(raw["sha256"]),
                }
            )
    rows.sort(key=lambda row: row["path"])
    if not rows:
        raise Task9Rejected("task9_subtree_inventory_empty")
    allocated = 0
    root_path = Path(root_path)
    for row in rows:
        path = root_path / row["path"]
        info = path.stat(follow_symlinks=False)
        allocated += int(getattr(info, "st_blocks", 0) * 512)
    return {
        "root": str(root_path.resolve()),
        "file_count": len(rows),
        "logical_bytes": sum(int(row["bytes"]) for row in rows),
        "allocated_bytes": allocated,
        "inventory_root_sha256": stable_sha256(rows),
        "files": rows,
    }


def _make_read_only(root: Path) -> None:
    root = Path(root)
    for base, directories, filenames in os.walk(root, topdown=False):
        base_path = Path(base)
        for filename in filenames:
            os.chmod(base_path / filename, 0o444)
        for directory in directories:
            os.chmod(base_path / directory, 0o555)
    os.chmod(root, 0o555)


def _assert_tree_read_only(
    root: Path,
    *,
    code: str = "task9_cache_authority_not_read_only",
) -> None:
    for base, directories, filenames in os.walk(root, followlinks=False):
        base_path = Path(base)
        for name in [*directories, *filenames]:
            if (base_path / name).stat(follow_symlinks=False).st_mode & 0o222:
                raise Task9Rejected(code)
    if Path(root).stat(follow_symlinks=False).st_mode & 0o222:
        raise Task9Rejected(code)


def _task8_tick_prewarm_authority(
    *,
    receipt_path: Path = TASK8_ACCEPTED_PREWARM,
    cache_root: Path | None = None,
) -> tuple[dict[str, Any], list[Path]]:
    receipt_path = Path(receipt_path)
    if receipt_path.is_symlink() or not receipt_path.is_file():
        raise Task9Rejected("task9_task8_tick_prewarm_invalid")
    try:
        receipt_path = receipt_path.resolve(strict=True)
    except OSError:
        raise Task9Rejected("task9_task8_tick_prewarm_invalid") from None
    try:
        receipt = json.loads(receipt_path.read_bytes())
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise Task9Rejected("task9_task8_tick_prewarm_invalid") from None
    if not isinstance(receipt, dict):
        raise Task9Rejected("task9_task8_tick_prewarm_invalid")
    try:
        task8.replay.sparse_tick_source_attestations(receipt)
    except (OSError, RuntimeError, TypeError, ValueError):
        raise Task9Rejected("task9_task8_tick_prewarm_invalid") from None
    entries = receipt.get("entries")
    if not isinstance(entries, list) or len(entries) != 4:
        raise Task9Rejected("task9_task8_tick_prewarm_invalid")
    declared_cache_root = Path(str(receipt.get("cache_root") or ""))
    expected_cache_root = Path(
        cache_root or task8.replay.ATTEMPT5_TICK_SPARSE_CACHE_ROOT
    )
    try:
        if expected_cache_root.is_symlink() or declared_cache_root.is_symlink():
            raise Task9Rejected("task9_task8_tick_cache_root_mismatch")
        resolved_cache_root = expected_cache_root.resolve(strict=True)
        if declared_cache_root.resolve(strict=True) != resolved_cache_root:
            raise Task9Rejected("task9_task8_tick_cache_root_mismatch")
    except OSError:
        raise Task9Rejected("task9_task8_tick_cache_root_mismatch") from None
    paths: list[Path] = []
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise Task9Rejected("task9_task8_tick_prewarm_invalid")
        identity = entry.get("identity_root_sha256")
        if not _is_sha256(identity):
            raise Task9Rejected("task9_task8_tick_identity_invalid")
        candidate = resolved_cache_root / str(identity)
        try:
            resolved = candidate.resolve(strict=True)
        except OSError:
            raise Task9Rejected("task9_task8_tick_identity_missing") from None
        if (
            resolved.parent != resolved_cache_root
            or candidate.is_symlink()
            or not resolved.is_dir()
        ):
            raise Task9Rejected("task9_task8_tick_identity_escape")
        paths.append(resolved)
    if len(paths) != 4 or len({str(path) for path in paths}) != 4:
        raise Task9Rejected("task9_task8_tick_prewarm_invalid")
    projection = dict(receipt)
    projection.pop("prewarm_root_sha256", None)
    projection.pop("non_authoritative_filesystem_storage_receipt", None)
    authority = {
        "path": str(receipt_path.resolve()),
        "file_sha256": file_sha256(receipt_path),
        "prewarm_root_sha256": receipt.get("prewarm_root_sha256"),
        "cache_root": str(resolved_cache_root),
        "entry_identity_roots": sorted(
            str(entry["identity_root_sha256"]) for entry in entries
        ),
    }
    if (
        not _is_sha256(authority["prewarm_root_sha256"])
        or authority["prewarm_root_sha256"] != stable_sha256(projection)
    ):
        raise Task9Rejected("task9_task8_tick_prewarm_root_invalid")
    return authority, paths


def _tick_input_paths() -> list[Path]:
    return _task8_tick_prewarm_authority()[1]


def _cache_input_inventory(typed_cache_root: Path) -> dict[str, Any]:
    args = task8.task8_args(ROOT / ".task9-inventory-unused")
    named_paths = {
        "typed_normalized_cache": Path(typed_cache_root),
        "accepted_source_bundle": Path(args.source_acceleration_bundle_dir),
        "prepared_day_packs": task7.TASK6_CORRECTED_PACK_ROOT,
        **{
            f"sparse_tick_entry_{index}": path
            for index, path in enumerate(_tick_input_paths(), start=1)
        },
    }
    rows = []
    for name, path in sorted(named_paths.items()):
        inventory = inventory_tree(path)
        rows.append({"name": name, **_compact_inventory(inventory)})
    return {
        "inputs": rows,
        "input_count": len(rows),
        "logical_bytes": sum(int(row["logical_bytes"]) for row in rows),
        "inventory_root_sha256": stable_sha256(rows),
    }


def _finite_nonnegative(value: Any) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(float(value))
        and float(value) >= 0.0
    )


def _forbidden_paths(value: Any, path: tuple[str, ...] = ()) -> list[str]:
    found: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = (*path, str(key))
            if key in FORBIDDEN_RECEIPT_FIELDS:
                found.append(".".join(child_path))
            found.extend(_forbidden_paths(child, child_path))
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            found.extend(_forbidden_paths(child, (*path, str(index))))
    return found


def assert_outcome_blind(value: Mapping[str, Any]) -> None:
    if _forbidden_paths(value):
        raise Task9Rejected("task9_economic_field_exposed")


def build_typed_cache_authority(output_root: Path) -> Path:
    """Construct the complete current R5 typed cache from an absent directory."""

    output_root = Path(output_root)
    authority_dir = output_root / "cache-authority"
    typed_cache_root = authority_dir / "typed-cache"
    manifest_path = authority_dir / "TASK9_TYPED_CACHE_AUTHORITY.json"
    if authority_dir.exists() or authority_dir.is_symlink():
        raise Task9Rejected("task9_cache_authority_output_must_be_new")
    authority_dir.mkdir(parents=True)
    args = task8.task8_args(output_root / ".cache-build-unused")
    before_resource = slice_metrics._resource_snapshot()
    swap_before = slice_metrics._swap_used_bytes()
    started = time.perf_counter()
    accelerator = integrated.RealReplaySourceAccelerator.from_accepted_bundle(
        source_bundle_dir=Path(args.source_acceleration_bundle_dir),
        selection_path=Path(args.source_acceleration_selection),
        typed_cache_root=typed_cache_root,
        expected_bundle_root=str(args.expected_source_bundle_root_sha256),
        expected_source_plan_digest=str(args.expected_source_plan_digest_sha256),
    )
    binding_seconds = time.perf_counter() - started
    prewarm_started = time.perf_counter()
    prewarm = accelerator.prewarm_all(workers=int(args.source_prewarm_workers))
    prewarm_seconds = time.perf_counter() - prewarm_started
    authority = accelerator.authority()
    typed_metrics = authority.get("typed_cache_metrics")
    if (
        not isinstance(typed_metrics, Mapping)
        or int(typed_metrics.get("cold_partition_count") or 0) != 96
        or int(typed_metrics.get("warm_partition_count") or 0) != 0
        or int(typed_metrics.get("bytes_written") or 0) <= 0
        or prewarm.get("barrier_complete") is not True
        or int(prewarm.get("partition_count") or 0) != 96
    ):
        raise Task9Rejected("task9_derived_cold_cache_construction_invalid")
    inventory_started = time.perf_counter()
    inventory = inventory_tree(typed_cache_root)
    accepted_inventory = inventory_tree(TASK8_ACCEPTED_TYPED_CACHE)
    if not _inventory_set(inventory).issubset(_inventory_set(accepted_inventory)):
        raise Task9Rejected("task9_cache_not_subset_of_task8_exact_cache")
    input_inventory = _cache_input_inventory(typed_cache_root)
    tick_prewarm_authority, _ = _task8_tick_prewarm_authority()
    inventory_seconds = time.perf_counter() - inventory_started
    _make_read_only(typed_cache_root)
    _assert_tree_read_only(typed_cache_root)
    elapsed = time.perf_counter() - started
    after_resource = slice_metrics._resource_snapshot()
    swap_after = slice_metrics._swap_used_bytes()
    accepted_profile = _load_rooted_json(
        TASK8_ACCEPTED_PROFILE,
        root_field="receipt_root_sha256",
        code="task9_task8_profile",
        require_canonical_bytes=False,
    )
    core = {
        "schema": CACHE_AUTHORITY_SCHEMA,
        "status": CACHE_AUTHORITY_STATUS,
        "typed_cache": _compact_inventory(inventory),
        "input_inventory": input_inventory,
        "task8_tick_prewarm_authority": tick_prewarm_authority,
        "derived_cold_construction": {
            "wall_seconds": elapsed,
            "source_binding_seconds": binding_seconds,
            "prewarm_seconds": prewarm_seconds,
            "inventory_and_authentication_seconds": inventory_seconds,
            "typed_cache_metrics": dict(typed_metrics),
            "prewarm": dict(prewarm),
            "resource": slice_metrics._resource_delta(
                before_resource,
                after_resource,
                wall_seconds=elapsed,
            ),
            "swap_used_start_bytes": swap_before,
            "swap_used_end_bytes": swap_after,
            "swap_used_delta_bytes": (
                None
                if swap_before is None or swap_after is None
                else int(swap_after) - int(swap_before)
            ),
        },
        "accepted_task8_predecessor": {
            "profile_path": str(TASK8_ACCEPTED_PROFILE),
            "profile_file_sha256": file_sha256(TASK8_ACCEPTED_PROFILE),
            "profile_receipt_root_sha256": accepted_profile["receipt_root_sha256"],
            "complete_cache_path": str(TASK8_ACCEPTED_TYPED_CACHE),
            "complete_cache_inventory_root_sha256": accepted_inventory[
                "inventory_root_sha256"
            ],
            "new_cache_is_exact_current_entry_subset": True,
        },
        "source_contract": {
            "source_bundle_root_sha256": authority["source_bundle_root_sha256"],
            "selection_root_sha256": authority["selection_root_sha256"],
            "source_plan_digest_sha256": authority["source_plan_digest_sha256"],
            "config_projection_root_sha256": authority[
                "config_projection_root_sha256"
            ],
            "normalizer_code_root_sha256": authority[
                "normalizer_code_root_sha256"
            ],
        },
        "read_only_filesystem_mode": True,
        "policy_execution_entered": False,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
        "real_order_transmission_possible": False,
        "economic_values_exposed": False,
        "acceptance_authorized": False,
    }
    assert_outcome_blind(core)
    receipt = {**core, "authority_root_sha256": stable_sha256(core)}
    atomic_write_json(manifest_path, receipt)
    return manifest_path


def verify_cache_authority(
    manifest_path: Path,
    *,
    expected_file_sha256: str | None = None,
) -> dict[str, Any]:
    manifest_path = Path(manifest_path)
    payload = _load_rooted_json(
        manifest_path,
        root_field="authority_root_sha256",
        code="task9_cache_authority",
        expected_file_sha256=expected_file_sha256,
    )
    if (
        payload.get("schema") != CACHE_AUTHORITY_SCHEMA
        or payload.get("status") != CACHE_AUTHORITY_STATUS
        or payload.get("read_only_filesystem_mode") is not True
        or payload.get("broker_live_authority") is not False
        or payload.get("broker_mutation_enabled") is not False
        or payload.get("real_order_transmission_possible") is not False
        or payload.get("economic_values_exposed") is not False
        or payload.get("acceptance_authorized") is not False
    ):
        raise Task9Rejected("task9_cache_authority_scope_invalid")
    assert_outcome_blind(payload)
    manifest_path = manifest_path.resolve(strict=True)
    if manifest_path.name != "TASK9_TYPED_CACHE_AUTHORITY.json":
        raise Task9Rejected("task9_cache_authority_path_invalid")
    declared = payload.get("typed_cache")
    if not isinstance(declared, Mapping):
        raise Task9Rejected("task9_cache_authority_inventory_invalid")
    declared_root = Path(str(declared.get("root") or ""))
    expected_root = manifest_path.parent / "typed-cache"
    try:
        if (
            declared_root.is_symlink()
            or expected_root.is_symlink()
            or declared_root.resolve(strict=True) != expected_root.resolve(strict=True)
        ):
            raise Task9Rejected("task9_cache_authority_typed_cache_escape")
    except OSError:
        raise Task9Rejected("task9_cache_authority_typed_cache_escape") from None
    current = inventory_tree(expected_root)
    for field in (
        "file_count",
        "logical_bytes",
        "allocated_bytes",
        "inventory_root_sha256",
    ):
        if current[field] != declared.get(field):
            raise Task9Rejected("task9_cache_authority_inventory_drift")
    _assert_tree_read_only(Path(current["root"]))
    current_inputs = _cache_input_inventory(Path(current["root"]))
    declared_inputs = payload.get("input_inventory")
    if current_inputs != declared_inputs:
        raise Task9Rejected("task9_cache_input_inventory_drift")
    current_tick_prewarm, _ = _task8_tick_prewarm_authority()
    if current_tick_prewarm != payload.get("task8_tick_prewarm_authority"):
        raise Task9Rejected("task9_task8_tick_prewarm_authority_drift")
    return {**payload, "verified_current_inventory": _compact_inventory(current)}


def _current_launch_nonce_sha256() -> str:
    raw = os.environ.get(TASK9_LAUNCH_NONCE_ENV)
    if not raw:
        raise Task9Rejected("task9_launch_nonce_missing")
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _validate_expected_ancestor(expected_pid: int) -> None:
    if isinstance(expected_pid, bool) or int(expected_pid) <= 0:
        raise Task9Rejected("task9_expected_parent_pid_invalid")
    current = os.getpid()
    for _ in range(4):
        parent = os.getppid() if current == os.getpid() else _parent_pid(current)
        if parent == int(expected_pid):
            return
        if parent <= 1 or parent == current:
            break
        current = parent
    raise Task9Rejected("task9_expected_parent_not_ancestor")


def _parent_pid(pid: int) -> int:
    try:
        import psutil

        return int(psutil.Process(pid).ppid())
    except Exception:
        return -1


def _load_request(path: Path, *, schema: str) -> dict[str, Any]:
    payload = _load_rooted_json(
        path,
        root_field="request_root_sha256",
        code="task9_request",
    )
    if payload.get("schema") != schema:
        raise Task9Rejected("task9_request_schema_invalid")
    if payload.get("launch_nonce_sha256") != _current_launch_nonce_sha256():
        raise Task9Rejected("task9_request_launch_nonce_mismatch")
    _validate_expected_ancestor(int(payload.get("expected_orchestrator_pid") or 0))
    return payload


def derive_cache_state(
    *,
    priming_receipt_path: Path | None,
    priming_receipt_file_sha256: str | None,
    expected_cache_inventory_root_sha256: str,
    expected_cache_authority_path: Path,
    expected_cache_authority_file_sha256: str,
    expected_cache_authority_root_sha256: str,
    expected_complete_input_inventory_root_sha256: str,
    expected_validation_output_root: Path,
    current_launch_nonce_sha256: str,
) -> dict[str, Any]:
    try:
        validation_output_root = Path(expected_validation_output_root).resolve(
            strict=True
        )
    except OSError:
        raise Task9Rejected("task9_validation_output_root_invalid") from None
    expected_authority_resolved = _contained_path(
        Path(expected_cache_authority_path),
        validation_output_root / "cache-authority",
        code="task9_cache_authority_path_escape",
    )
    if expected_authority_resolved.name != "TASK9_TYPED_CACHE_AUTHORITY.json":
        raise Task9Rejected("task9_cache_authority_path_invalid")
    expected_authority_path = str(expected_authority_resolved)
    if not all(
        _is_sha256(value)
        for value in (
            expected_cache_inventory_root_sha256,
            expected_cache_authority_file_sha256,
            expected_cache_authority_root_sha256,
            expected_complete_input_inventory_root_sha256,
            current_launch_nonce_sha256,
        )
    ):
        raise Task9Rejected("task9_cache_state_hash_invalid")
    base = {
        "cache_authority_root_sha256": expected_cache_authority_root_sha256,
        "cache_authority_file_sha256": expected_cache_authority_file_sha256,
        "complete_input_inventory_root_sha256": (
            expected_complete_input_inventory_root_sha256
        ),
        "trial_launch_nonce_sha256": current_launch_nonce_sha256,
        "validation_output_root": str(validation_output_root),
    }
    if priming_receipt_path is None:
        if priming_receipt_file_sha256 is not None:
            raise Task9Rejected("task9_priming_receipt_evidence_incomplete")
        return {
            "cache_state": COLD_PROCESS_STATE,
            **base,
            "priming_request_path": None,
            "priming_request_file_sha256": None,
            "priming_request_root_sha256": None,
            "priming_receipt_path": None,
            "priming_receipt_file_sha256": None,
            "priming_receipt_root_sha256": None,
            "process_cold": True,
            "warm_filesystem_expected": False,
            "os_page_cache_controlled": False,
        }
    if not _is_sha256(priming_receipt_file_sha256):
        raise Task9Rejected("task9_priming_receipt_evidence_incomplete")
    priming = _load_rooted_json(
        Path(priming_receipt_path),
        root_field="receipt_root_sha256",
        code="task9_priming_receipt",
        expected_file_sha256=priming_receipt_file_sha256,
    )
    process = priming.get("measurement_process")
    request_binding = priming.get("request")
    authority_binding = priming.get("cache_authority")
    if not isinstance(request_binding, Mapping):
        raise Task9Rejected("task9_priming_request_binding_invalid")
    prime_request_path = Path(str(request_binding.get("path") or ""))
    prime_request_path = _contained_path(
        prime_request_path,
        validation_output_root / "requests",
        code="task9_priming_request_path_escape",
    )
    priming_receipt_resolved = _contained_path(
        Path(priming_receipt_path),
        validation_output_root / "requests",
        code="task9_priming_receipt_path_escape",
    )
    prime_request = _load_rooted_json(
        prime_request_path,
        root_field="request_root_sha256",
        code="task9_priming_request",
        expected_file_sha256=str(request_binding.get("file_sha256") or ""),
    )
    expected_request_binding = {
        "path": str(prime_request_path.resolve()),
        "file_sha256": file_sha256(prime_request_path),
        "request_root_sha256": prime_request["request_root_sha256"],
    }
    expected_authority_binding = {
        "path": expected_authority_path,
        "file_sha256": expected_cache_authority_file_sha256,
        "authority_root_sha256": expected_cache_authority_root_sha256,
    }
    expected_priming_receipt_path = prime_request_path.with_name(
        prime_request_path.stem + ".receipt.json"
    )
    if (
        priming.get("schema") != PRIMING_RECEIPT_SCHEMA
        or priming.get("status") != PRIMING_STATUS
        or priming.get("cache_inventory_root_sha256")
        != expected_cache_inventory_root_sha256
        or priming.get("complete_input_inventory_root_sha256")
        != expected_complete_input_inventory_root_sha256
        or request_binding != expected_request_binding
        or authority_binding != expected_authority_binding
        or not isinstance(process, Mapping)
        or not _is_sha256(process.get("launch_nonce_sha256"))
        or process.get("launch_nonce_sha256") == current_launch_nonce_sha256
        or prime_request.get("schema") != PRIMING_REQUEST_SCHEMA
        or prime_request.get("validation_output_root")
        != str(validation_output_root)
        or prime_request.get("launch_nonce_sha256")
        != process.get("launch_nonce_sha256")
        or prime_request.get("cache_authority_path") != expected_authority_path
        or prime_request.get("cache_authority_file_sha256")
        != expected_cache_authority_file_sha256
        or prime_request.get("cache_authority_root_sha256")
        != expected_cache_authority_root_sha256
        or prime_request.get("complete_input_inventory_root_sha256")
        != expected_complete_input_inventory_root_sha256
        or prime_request.get("receipt_path")
        != str(priming_receipt_resolved)
        or priming_receipt_resolved != expected_priming_receipt_path
        or not prime_request_path.name.endswith(".prime.request.json")
        or priming.get("sequential_read_and_hash_complete") is not True
        or priming.get("os_page_cache_controlled") is not False
        or priming.get("broker_live_authority") is not False
        or priming.get("broker_mutation_enabled") is not False
        or priming.get("real_order_transmission_possible") is not False
        or priming.get("economic_values_exposed") is not False
        or priming.get("acceptance_authorized") is not False
    ):
        raise Task9Rejected("task9_priming_receipt_scope_invalid")
    return {
        "cache_state": WARM_FILESYSTEM_STATE,
        **base,
        "priming_request_path": str(prime_request_path.resolve()),
        "priming_request_file_sha256": file_sha256(prime_request_path),
        "priming_request_root_sha256": prime_request["request_root_sha256"],
        "priming_receipt_path": str(priming_receipt_resolved),
        "priming_receipt_file_sha256": str(priming_receipt_file_sha256),
        "priming_receipt_root_sha256": priming["receipt_root_sha256"],
        "priming_process_launch_nonce_sha256": process["launch_nonce_sha256"],
        "process_cold": True,
        "warm_filesystem_expected": True,
        "os_page_cache_controlled": False,
    }


def semantic_trial_projection(parity: Mapping[str, Any]) -> dict[str, Any]:
    semantic_parity = parity.get("semantic_parity")
    days = parity.get("days")
    if (
        not isinstance(semantic_parity, Mapping)
        or not isinstance(days, Mapping)
        or parity.get("meaningful_difference_count") != 0
        or parity.get("unknown_difference_count") != 0
        or semantic_parity.get("meaningful_difference_count") != 0
        or semantic_parity.get("unknown_difference_count") != 0
    ):
        raise Task9Rejected("task9_semantic_parity_invalid")
    exact_days: dict[str, Any] = {}
    for day in (task8.DAY1, task8.DAY2):
        day_payload = days.get(day)
        roles = day_payload.get("roles") if isinstance(day_payload, Mapping) else None
        if not isinstance(roles, Mapping):
            raise Task9Rejected("task9_semantic_day_projection_invalid")
        try:
            exact_days[day] = {
                role: dict(roles[role])
                for role in sorted(task8.TASK8_SEMANTIC_EXACT_ROLES)
            }
        except (KeyError, TypeError, ValueError):
            raise Task9Rejected("task9_semantic_day_projection_invalid") from None
    order = semantic_parity.get("order_semantic_comparison")
    preimages = semantic_parity.get("selected_order_preimage_comparison")
    clock = semantic_parity.get("runtime_clock_closure_contract")
    accelerated_preimages = (
        preimages.get("accelerated_preimage_validation")
        if isinstance(preimages, Mapping)
        else None
    )
    if (
        not isinstance(order, Mapping)
        or not isinstance(preimages, Mapping)
        or not isinstance(accelerated_preimages, Mapping)
        or not isinstance(clock, Mapping)
        or not _is_sha256(order.get("ordered_semantic_projection_root_sha256"))
        or not _is_sha256(preimages.get("projection_root_sha256"))
        or not _is_sha256(preimages.get("selected_identity_root_sha256"))
        or not _is_sha256(
            accelerated_preimages.get("persisted_order_indexes_root_sha256")
        )
        or clock.get("contract_root_sha256")
        != task8.task8_runtime_clock_closure_contract()["contract_root_sha256"]
    ):
        raise Task9Rejected("task9_semantic_finite_projection_invalid")
    return {
        "days": exact_days,
        "order": {
            "row_count": int(order.get("row_count") or 0),
            "ordered_semantic_projection_root_sha256": order[
                "ordered_semantic_projection_root_sha256"
            ],
        },
        "selected_order_preimages": {
            "row_count": int(preimages.get("row_count") or 0),
            "projection_root_sha256": preimages["projection_root_sha256"],
            "selected_identity_root_sha256": preimages[
                "selected_identity_root_sha256"
            ],
            "persisted_order_indexes_root_sha256": accelerated_preimages[
                "persisted_order_indexes_root_sha256"
            ],
        },
        "runtime_clock_closure_contract_root_sha256": clock[
            "contract_root_sha256"
        ],
        "tick_sparse_cache_raw_source_full_hash_count": int(
            parity.get("tick_sparse_cache_raw_source_full_hash_count") or 0
        ),
        "tick_sparse_cache_sealed_reuse_count": int(
            parity.get("tick_sparse_cache_sealed_reuse_count") or 0
        ),
    }


def _semantic_diagnostic_root(root: Path) -> Path:
    root = Path(root)
    return root.with_name(root.name + ".semantic-diagnostic")


def _semantic_reference_binding() -> dict[str, Any]:
    reference_root = Path(task7.TASK6_REFERENCE_EXECUTION_ROOT)
    main = inventory_tree(reference_root)
    diagnostic = inventory_tree(_semantic_diagnostic_root(reference_root))
    core = {
        "reference_root": str(reference_root.resolve()),
        "main_namespace": main,
        "semantic_diagnostic_namespace": diagnostic,
    }
    return {**core, "binding_root_sha256": stable_sha256(core)}


def _authenticated_trial_tick_prewarm(trial_root: Path) -> dict[str, Any]:
    path = Path(trial_root) / "ATTEMPT5_TICK_SPARSE_CACHE_PREWARM_RECEIPT.json"
    if path.is_symlink() or not path.is_file():
        raise Task9Rejected("task9_trial_tick_prewarm_missing")
    try:
        payload = json.loads(path.read_bytes())
        task8.replay.sparse_tick_source_attestations(payload)
    except (OSError, UnicodeError, json.JSONDecodeError, RuntimeError, TypeError):
        raise Task9Rejected("task9_trial_tick_prewarm_invalid") from None
    if (
        not isinstance(payload, Mapping)
        or int(payload.get("raw_source_full_hash_count") or 0) != 0
        or int(payload.get("sealed_cache_reuse_count") or 0) != 4
    ):
        raise Task9Rejected("task9_trial_tick_prewarm_invalid")
    return {
        "path": str(path.resolve()),
        "file_sha256": file_sha256(path),
        "prewarm_root_sha256": payload["prewarm_root_sha256"],
        "raw_source_full_hash_count": 0,
        "sealed_cache_reuse_count": 4,
    }


def rederive_semantic_projection_from_ledgers(
    trial_root: Path,
    *,
    reference_projection: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Recompute the Task 8 projection from persisted raw ledgers."""

    trial_root = Path(trial_root)
    try:
        output_projection = {
            day: task8._day_projection(trial_root, day)
            for day in (task8.DAY1, task8.DAY2)
        }
        reference = (
            dict(reference_projection)
            if reference_projection is not None
            else {
                day: task8._day_projection(
                    task7.TASK6_REFERENCE_EXECUTION_ROOT,
                    day,
                )
                for day in (task8.DAY1, task8.DAY2)
            }
        )
        parity = task8._task8_semantic_parity(
            namespace=trial_root,
            output_projection=output_projection,
            reference_projection=reference,
        )
        tick = _authenticated_trial_tick_prewarm(trial_root)
        wrapper = {
            "days": {
                day: {
                    "projection_root_sha256": stable_sha256(
                        output_projection[day]
                    ),
                    "roles": output_projection[day],
                }
                for day in (task8.DAY1, task8.DAY2)
            },
            "semantic_parity": parity,
            "meaningful_difference_count": 0,
            "unknown_difference_count": 0,
            "tick_sparse_cache_raw_source_full_hash_count": tick[
                "raw_source_full_hash_count"
            ],
            "tick_sparse_cache_sealed_reuse_count": tick[
                "sealed_cache_reuse_count"
            ],
        }
        projection = semantic_trial_projection(wrapper)
    except (
        task7.Task7Rejected,
        task8.Task8ProfileRejected,
        task8.task3_acceptance.Task3ExactCacheRejected,
        task8.task3_acceptance.semantic.SemanticAcceptanceError,
        OSError,
        TypeError,
        ValueError,
    ) as exc:
        raise Task9Rejected(f"task9_semantic_ledger_rederivation_failed:{exc}") from None
    validate_semantic_projection(projection)
    return {
        "semantic_projection": projection,
        "semantic_projection_root_sha256": stable_sha256(projection),
        "trial_tick_prewarm": tick,
        "derivation": "task8_exact_roles_order_and_preimages_from_bound_ledgers",
    }


def _nonnegative_integer(value: Any) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and value >= 0
    )


def validate_semantic_projection(projection: Mapping[str, Any]) -> dict[str, Any]:
    expected_top = {
        "days",
        "order",
        "selected_order_preimages",
        "runtime_clock_closure_contract_root_sha256",
        "tick_sparse_cache_raw_source_full_hash_count",
        "tick_sparse_cache_sealed_reuse_count",
    }
    if not isinstance(projection, Mapping) or set(projection) != expected_top:
        raise Task9Rejected("task9_semantic_projection_structure_invalid")
    days = projection.get("days")
    expected_roles = set(task8.TASK8_SEMANTIC_EXACT_ROLES)
    if not isinstance(days, Mapping) or set(days) != {task8.DAY1, task8.DAY2}:
        raise Task9Rejected("task9_semantic_projection_structure_invalid")
    for day in (task8.DAY1, task8.DAY2):
        roles = days.get(day)
        if not isinstance(roles, Mapping) or set(roles) != expected_roles:
            raise Task9Rejected("task9_semantic_projection_structure_invalid")
        for role in sorted(expected_roles):
            row = roles.get(role)
            if (
                not isinstance(row, Mapping)
                or set(row) != {"row_count", "ordered_bytes_sha256"}
                or not _nonnegative_integer(row.get("row_count"))
                or not _is_sha256(row.get("ordered_bytes_sha256"))
            ):
                raise Task9Rejected("task9_semantic_projection_structure_invalid")
    order = projection.get("order")
    if (
        not isinstance(order, Mapping)
        or set(order)
        != {"row_count", "ordered_semantic_projection_root_sha256"}
        or not _nonnegative_integer(order.get("row_count"))
        or not _is_sha256(order.get("ordered_semantic_projection_root_sha256"))
    ):
        raise Task9Rejected("task9_semantic_projection_structure_invalid")
    preimages = projection.get("selected_order_preimages")
    if (
        not isinstance(preimages, Mapping)
        or set(preimages)
        != {
            "row_count",
            "projection_root_sha256",
            "selected_identity_root_sha256",
            "persisted_order_indexes_root_sha256",
        }
        or not _nonnegative_integer(preimages.get("row_count"))
        or not all(
            _is_sha256(preimages.get(field))
            for field in (
                "projection_root_sha256",
                "selected_identity_root_sha256",
                "persisted_order_indexes_root_sha256",
            )
        )
    ):
        raise Task9Rejected("task9_semantic_projection_structure_invalid")
    if (
        projection.get("runtime_clock_closure_contract_root_sha256")
        != task8.task8_runtime_clock_closure_contract()["contract_root_sha256"]
        or projection.get("tick_sparse_cache_raw_source_full_hash_count") != 0
        or projection.get("tick_sparse_cache_sealed_reuse_count") != 4
    ):
        raise Task9Rejected("task9_semantic_projection_structure_invalid")
    return dict(projection)


def validate_cache_state_evidence(
    *,
    declared_cache_state: Any,
    evidence: Any,
    measurement_process: Any,
) -> dict[str, Any]:
    if not isinstance(evidence, Mapping) or not isinstance(
        measurement_process, Mapping
    ):
        raise Task9Rejected("task9_cache_state_evidence_invalid")
    state = evidence.get("cache_state")
    if state != declared_cache_state:
        raise Task9Rejected("task9_cache_state_relabelled")
    if state not in {COLD_PROCESS_STATE, WARM_FILESYSTEM_STATE}:
        raise Task9Rejected("task9_cache_state_evidence_invalid")
    for field in (
        "cache_authority_root_sha256",
        "cache_authority_file_sha256",
        "complete_input_inventory_root_sha256",
        "trial_launch_nonce_sha256",
    ):
        if not _is_sha256(evidence.get(field)):
            raise Task9Rejected("task9_cache_state_evidence_invalid")
    if (
        not isinstance(evidence.get("validation_output_root"), str)
        or not Path(str(evidence["validation_output_root"])).is_absolute()
    ):
        raise Task9Rejected("task9_cache_state_evidence_invalid")
    if (
        measurement_process.get("launch_nonce_sha256")
        != evidence.get("trial_launch_nonce_sha256")
        or evidence.get("process_cold") is not True
        or evidence.get("os_page_cache_controlled") is not False
    ):
        raise Task9Rejected("task9_cache_state_evidence_invalid")
    prime_fields = (
        "priming_request_path",
        "priming_request_file_sha256",
        "priming_request_root_sha256",
        "priming_receipt_path",
        "priming_receipt_file_sha256",
        "priming_receipt_root_sha256",
    )
    if state == COLD_PROCESS_STATE:
        if (
            any(evidence.get(field) is not None for field in prime_fields)
            or evidence.get("warm_filesystem_expected") is not False
            or evidence.get("priming_process_launch_nonce_sha256") is not None
        ):
            raise Task9Rejected("task9_cache_state_evidence_invalid")
    else:
        if (
            evidence.get("warm_filesystem_expected") is not True
            or not all(
                isinstance(evidence.get(field), str)
                and bool(evidence.get(field))
                and Path(str(evidence.get(field))).is_absolute()
                for field in ("priming_request_path", "priming_receipt_path")
            )
            or not all(
                _is_sha256(evidence.get(field))
                for field in (
                    "priming_request_file_sha256",
                    "priming_request_root_sha256",
                    "priming_receipt_file_sha256",
                    "priming_receipt_root_sha256",
                    "priming_process_launch_nonce_sha256",
                )
            )
            or evidence.get("priming_process_launch_nonce_sha256")
            == evidence.get("trial_launch_nonce_sha256")
        ):
            raise Task9Rejected("task9_cache_state_evidence_invalid")
    return dict(evidence)


def _validate_inventory_declaration(inventory: Any) -> dict[str, Any]:
    if not isinstance(inventory, Mapping):
        raise Task9Rejected("task9_evidence_inventory_declaration_invalid")
    files = inventory.get("files")
    if not isinstance(files, list) or not files:
        raise Task9Rejected("task9_evidence_inventory_declaration_invalid")
    paths: list[str] = []
    for row in files:
        if not isinstance(row, Mapping):
            raise Task9Rejected("task9_evidence_inventory_declaration_invalid")
        path = row.get("path")
        if (
            not isinstance(path, str)
            or not path
            or path.startswith("/")
            or ".." in Path(path).parts
            or not _nonnegative_integer(row.get("bytes"))
            or not _is_sha256(row.get("sha256"))
        ):
            raise Task9Rejected("task9_evidence_inventory_declaration_invalid")
        paths.append(path)
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        raise Task9Rejected("task9_evidence_inventory_declaration_invalid")
    if (
        not isinstance(inventory.get("root"), str)
        or not Path(str(inventory["root"])).is_absolute()
        or inventory.get("file_count") != len(files)
        or inventory.get("logical_bytes")
        != sum(int(row["bytes"]) for row in files)
        or not _nonnegative_integer(inventory.get("allocated_bytes"))
        or inventory.get("inventory_root_sha256") != stable_sha256(files)
    ):
        raise Task9Rejected("task9_evidence_inventory_declaration_invalid")
    return dict(inventory)


def validate_stage_profile(profile: Any) -> dict[str, Any]:
    if (
        not isinstance(profile, Mapping)
        or profile.get("schema") != benchmark.STAGE_PROFILE_SCHEMA
        or profile.get("enabled") is not True
        or profile.get("clock") != "perf_counter_ns"
    ):
        raise Task9Rejected("task9_stage_profile_scope_invalid")
    expected_order = list(benchmark.REPLAY_STAGE_ORDER)
    if profile.get("stage_order") != expected_order:
        raise Task9Rejected("task9_stage_profile_order_invalid")
    stages = profile.get("stages")
    if (
        not isinstance(stages, list)
        or [row.get("name") if isinstance(row, Mapping) else None for row in stages]
        != expected_order
    ):
        raise Task9Rejected("task9_stage_profile_order_invalid")
    numeric_fields = {
        "entered_count",
        "wall_ns",
        "self_wall_ns",
        "cpu_user_ns",
        "cpu_system_ns",
        "peak_rss_bytes",
        "block_input_operations",
        "block_output_operations",
        "output_rows",
        "output_bytes",
    }
    for row in stages:
        if (
            not isinstance(row, Mapping)
            or set(row) != {"name", *numeric_fields}
            or any(not _nonnegative_integer(row.get(field)) for field in numeric_fields)
            or int(row["self_wall_ns"]) > int(row["wall_ns"])
        ):
            raise Task9Rejected("task9_stage_profile_value_invalid")
        if row["name"] in TASK9_REQUIRED_STAGE_ENTRIES and int(
            row["entered_count"]
        ) <= 0:
            raise Task9Rejected("task9_stage_profile_required_stage_missing")
    call_counters = profile.get("call_counters")
    if (
        not isinstance(call_counters, Mapping)
        or any(
            not isinstance(name, str)
            or not name
            or not _nonnegative_integer(value)
            for name, value in call_counters.items()
        )
        or not TASK9_REQUIRED_CALL_COUNTERS.issubset(call_counters)
        or any(int(call_counters[name]) <= 0 for name in TASK9_REQUIRED_CALL_COUNTERS)
    ):
        raise Task9Rejected("task9_stage_profile_counter_invalid")
    output_counters = profile.get("output_counters")
    if not isinstance(output_counters, Mapping):
        raise Task9Rejected("task9_stage_profile_counter_invalid")
    for name, value in output_counters.items():
        if (
            not isinstance(name, str)
            or not name
            or not isinstance(value, Mapping)
            or set(value) != {"rows", "bytes"}
            or not _nonnegative_integer(value.get("rows"))
            or not _nonnegative_integer(value.get("bytes"))
        ):
            raise Task9Rejected("task9_stage_profile_counter_invalid")
    bounds = profile.get("resource_bounds")
    resource_fields = {
        "cpu_user_ns",
        "cpu_system_ns",
        "peak_rss_bytes",
        "block_input_operations",
        "block_output_operations",
    }
    if not isinstance(bounds, Mapping) or set(bounds) != {"first", "last"}:
        raise Task9Rejected("task9_stage_profile_resource_invalid")
    for name in ("first", "last"):
        row = bounds.get(name)
        if (
            not isinstance(row, Mapping)
            or set(row) != resource_fields
            or any(not _nonnegative_integer(row.get(field)) for field in resource_fields)
        ):
            raise Task9Rejected("task9_stage_profile_resource_invalid")
    for field in (
        "cpu_user_ns",
        "cpu_system_ns",
        "peak_rss_bytes",
        "block_input_operations",
        "block_output_operations",
    ):
        if int(bounds["last"][field]) < int(bounds["first"][field]):
            raise Task9Rejected("task9_stage_profile_resource_invalid")
    return dict(profile)


def validate_trial_receipt(receipt: Mapping[str, Any]) -> dict[str, Any]:
    if (
        receipt.get("schema") != TRIAL_RECEIPT_SCHEMA
        or receipt.get("status") != TRIAL_STATUS
        or receipt.get("derived_cache_state")
        not in {COLD_PROCESS_STATE, WARM_FILESYSTEM_STATE}
        or receipt.get("broker_live_authority") is not False
        or receipt.get("broker_mutation_enabled") is not False
        or receipt.get("real_order_transmission_possible") is not False
        or receipt.get("economic_values_exposed") is not False
        or receipt.get("acceptance_authorized") is not False
    ):
        raise Task9Rejected("task9_trial_scope_invalid")
    semantic_projection = receipt.get("semantic_projection")
    if not isinstance(semantic_projection, Mapping):
        raise Task9Rejected("task9_semantic_projection_structure_invalid")
    validate_semantic_projection(semantic_projection)
    if receipt.get("semantic_projection_root_sha256") != stable_sha256(
        semantic_projection
    ):
        raise Task9Rejected("task9_semantic_projection_root_invalid")
    validate_cache_state_evidence(
        declared_cache_state=receipt.get("derived_cache_state"),
        evidence=receipt.get("cache_state_evidence"),
        measurement_process=receipt.get("measurement_process"),
    )
    validate_stage_profile(receipt.get("stage_profile"))
    _validate_inventory_declaration(receipt.get("evidence_inventory"))
    _validate_inventory_declaration(receipt.get("semantic_diagnostic_inventory"))
    semantic_derivation = receipt.get("semantic_projection_derivation")
    if (
        not isinstance(semantic_derivation, Mapping)
        or semantic_derivation.get("derivation")
        != "task8_exact_roles_order_and_preimages_from_bound_ledgers"
        or semantic_derivation.get("semantic_projection_root_sha256")
        != receipt.get("semantic_projection_root_sha256")
        or not isinstance(semantic_derivation.get("trial_tick_prewarm"), Mapping)
    ):
        raise Task9Rejected("task9_semantic_projection_derivation_invalid")
    inventory_policy = receipt.get("evidence_inventory_policy")
    if (
        not isinstance(inventory_policy, Mapping)
        or inventory_policy.get("excluded_envelope_paths")
        != sorted(TRIAL_ENVELOPE_PATHS)
        or inventory_policy.get("excluded_paths_are_non_parity_envelope_only")
        is not True
        or inventory_policy.get("all_replay_evidence_files_included") is not True
    ):
        raise Task9Rejected("task9_evidence_inventory_policy_invalid")
    cache = receipt.get("cache")
    parity = receipt.get("parity")
    measurement = receipt.get("measurement")
    output_tree = receipt.get("output_tree")
    if not all(
        isinstance(value, Mapping)
        for value in (cache, parity, measurement, output_tree)
    ):
        raise Task9Rejected("task9_trial_payload_invalid")
    if int(cache.get("cold_partition_count") or 0) != 0:
        raise Task9Rejected("task9_trial_cache_rebuilt")
    if int(cache.get("bytes_written") or 0) != 0:
        raise Task9Rejected("task9_trial_cache_written")
    inventory_root = cache.get("inventory_root_sha256")
    if (
        not _is_sha256(inventory_root)
        or cache.get("pre_inventory_root_sha256") != inventory_root
        or cache.get("post_inventory_root_sha256") != inventory_root
    ):
        raise Task9Rejected("task9_trial_cache_drift")
    if (
        parity.get("meaningful_difference_count") != 0
        or parity.get("unknown_difference_count") != 0
        or int(parity.get("tick_sparse_cache_raw_source_full_hash_count") or 0) != 0
        or int(parity.get("tick_sparse_cache_sealed_reuse_count") or 0) != 4
    ):
        raise Task9Rejected("task9_trial_parity_invalid")
    for field in (
        "child_wall_seconds",
        "cpu_user_seconds",
        "cpu_system_seconds",
        "peak_rss_bytes",
        "no_event_total_seconds",
        "dense_total_seconds",
        "fixed_campaign_overhead_seconds",
        "engine_wall_seconds",
        "engine_cpu_seconds",
        "parity_verification_seconds",
        "bytes_read",
        "bytes_written",
        "swap_used_delta_bytes",
    ):
        if not _finite_nonnegative(measurement.get(field)):
            raise Task9Rejected("task9_trial_measurement_invalid")
    reconciled = (
        float(measurement["no_event_total_seconds"])
        + float(measurement["dense_total_seconds"])
        + float(measurement["fixed_campaign_overhead_seconds"])
    )
    if abs(reconciled - float(measurement["child_wall_seconds"])) > max(
        0.1, 0.005 * float(measurement["child_wall_seconds"])
    ):
        raise Task9Rejected("task9_trial_timing_reconciliation_invalid")
    if (
        float(measurement["engine_wall_seconds"])
        + float(measurement["parity_verification_seconds"])
        > float(measurement["child_wall_seconds"])
        + max(0.1, 0.005 * float(measurement["child_wall_seconds"]))
    ):
        raise Task9Rejected("task9_trial_engine_timing_reconciliation_invalid")
    verification_stage = next(
        row
        for row in receipt["stage_profile"]["stages"]
        if row["name"] == "verification"
    )
    verification_seconds = float(verification_stage["wall_ns"]) / 1_000_000_000.0
    if abs(
        verification_seconds - float(measurement["parity_verification_seconds"])
    ) > max(0.1, 0.02 * float(measurement["parity_verification_seconds"])):
        raise Task9Rejected("task9_trial_verification_stage_timing_mismatch")
    for field in ("logical_bytes", "allocated_bytes", "file_count"):
        if not _finite_nonnegative(output_tree.get(field)):
            raise Task9Rejected("task9_trial_output_inventory_invalid")
    assert_outcome_blind(receipt)
    return dict(receipt)


def _summary(values: Iterable[float | int]) -> dict[str, float]:
    numbers = [float(value) for value in values]
    if not numbers or any(not math.isfinite(value) or value < 0 for value in numbers):
        raise Task9Rejected("task9_summary_values_invalid")
    return {
        "median": statistics.median(numbers),
        "worst": max(numbers),
    }


def _metric_value(trial: Mapping[str, Any], field: str) -> float:
    measurement = trial["measurement"]
    value = measurement.get(field)
    if value is None and field in {"bytes_read", "bytes_written"}:
        return 0.0
    if not _finite_nonnegative(value):
        raise Task9Rejected("task9_trial_metric_invalid")
    return float(value)


def aggregate_trials(trials: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    validated = [validate_trial_receipt(trial) for trial in trials]
    counts = Counter(str(trial["derived_cache_state"]) for trial in validated)
    if counts != Counter({COLD_PROCESS_STATE: 2, WARM_FILESYSTEM_STATE: 3}):
        raise Task9Rejected("task9_trial_class_counts_invalid")
    if len({str(trial.get("trial_id")) for trial in validated}) != 5:
        raise Task9Rejected("task9_trial_identity_invalid")
    if len({trial["semantic_projection_root_sha256"] for trial in validated}) != 1:
        raise Task9Rejected("task9_cross_trial_semantic_root_mismatch")
    if len({trial["cache"]["inventory_root_sha256"] for trial in validated}) != 1:
        raise Task9Rejected("task9_cross_trial_cache_root_mismatch")
    classes: dict[str, Any] = {}
    metric_fields = (
        "wall_seconds",
        "cpu_seconds",
        "peak_rss_bytes",
        "bytes_read",
        "bytes_written",
        "swap_used_delta_bytes",
        "no_event_total_seconds",
        "dense_total_seconds",
        "fixed_campaign_overhead_seconds",
    )
    for cache_state in (COLD_PROCESS_STATE, WARM_FILESYSTEM_STATE):
        members = [
            trial for trial in validated if trial["derived_cache_state"] == cache_state
        ]
        rows: dict[str, Any] = {}
        for field in metric_fields:
            values: list[float] = []
            for trial in members:
                measurement = trial["measurement"]
                if field == "wall_seconds":
                    value = measurement.get(
                        "parent_observed_wall_seconds",
                        measurement["child_wall_seconds"],
                    )
                elif field == "cpu_seconds":
                    value = float(measurement["cpu_user_seconds"]) + float(
                        measurement["cpu_system_seconds"]
                    )
                elif field == "swap_used_delta_bytes":
                    value = max(0.0, float(measurement.get(field) or 0.0))
                else:
                    value = measurement.get(field)
                if not _finite_nonnegative(value):
                    raise Task9Rejected("task9_trial_metric_invalid")
                values.append(float(value))
            rows[field] = _summary(values)
        for field in ("logical_bytes", "allocated_bytes", "file_count"):
            rows[f"output_{field}"] = _summary(
                float(trial["output_tree"][field]) for trial in members
            )
        classes[cache_state] = rows

    projections: dict[str, Any] = {}
    for horizon, workload in STANDARDIZED_WORKLOAD_COUNTS.items():
        horizon_payload: dict[str, Any] = {
            "workload_counts": dict(workload),
            "scenario": (
                "standardized_equal_cost_linear_s0r0_extrapolation_not_"
                "an_upper_bound_or_future_density_prediction"
            ),
        }
        for cache_state, label in (
            (COLD_PROCESS_STATE, "cold"),
            (WARM_FILESYSTEM_STATE, "warm"),
        ):
            per_trial = []
            for trial in validated:
                if trial["derived_cache_state"] != cache_state:
                    continue
                measurement = trial["measurement"]
                wall = float(
                    measurement.get(
                        "parent_observed_wall_seconds",
                        measurement["child_wall_seconds"],
                    )
                )
                no_event = float(measurement["no_event_total_seconds"])
                dense = float(measurement["dense_total_seconds"])
                observed_two_day_residual = max(0.0, wall - no_event - dense)
                residual_per_observed_day = observed_two_day_residual / 2.0
                one_arm = (
                    (int(workload["no_event_days"]) + int(workload["dense_days"]))
                    * residual_per_observed_day
                    + int(workload["no_event_days"]) * no_event
                    + int(workload["dense_days"]) * dense
                )
                per_trial.append(one_arm)
            one_arm_summary = _summary(per_trial)
            horizon_payload[label] = {
                "one_arm_seconds": one_arm_summary,
                "four_arm_serial_seconds": {
                    key: value * 4.0 for key, value in one_arm_summary.items()
                },
            }
        projections[horizon] = horizon_payload
    return {
        "trial_counts": {
            COLD_PROCESS_STATE: counts[COLD_PROCESS_STATE],
            WARM_FILESYSTEM_STATE: counts[WARM_FILESYSTEM_STATE],
        },
        "semantic_projection_root_sha256": validated[0][
            "semantic_projection_root_sha256"
        ],
        "cache_inventory_root_sha256": validated[0]["cache"][
            "inventory_root_sha256"
        ],
        "classes": classes,
        "workload_counts_origin": (
            "standardized_22_scheduled_days_per_month_with_one_no_event_"
            "closure_day_and_all_other_days_dense_for_capacity_planning"
        ),
        "projections": projections,
        "four_arm_projection_kind": (
            "standardized_equal_cost_serial_4x_s0r0_extrapolation"
        ),
        "projection_limitations": (
            "measured_s0r0_two_day_residual_scaled_linearly_per_observed_day;"
            "all_four_arms_assumed_equal_cost;not_a_bound_or_speedup_claim"
        ),
        "shared_preparation_speedup_claimed": False,
        "parallel_four_arm_speedup_claimed": False,
    }


def _request_payload(
    *,
    schema: str,
    launch_nonce: str,
    expected_orchestrator_pid: int,
    values: Mapping[str, Any],
) -> dict[str, Any]:
    core = {
        "schema": schema,
        **dict(values),
        "launch_nonce_sha256": hashlib.sha256(
            launch_nonce.encode("utf-8")
        ).hexdigest(),
        "expected_orchestrator_pid": int(expected_orchestrator_pid),
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
        "real_order_transmission_possible": False,
        "economic_values_exposed": False,
        "acceptance_authorized": False,
    }
    assert_outcome_blind(core)
    return {**core, "request_root_sha256": stable_sha256(core)}


def make_priming_request(
    *,
    path: Path,
    cache_authority_path: Path,
    launch_nonce: str,
) -> Path:
    path = Path(path)
    try:
        requests_root = path.parent.resolve(strict=True)
        validation_output_root = requests_root.parent.resolve(strict=True)
    except OSError:
        raise Task9Rejected("task9_priming_request_namespace_invalid") from None
    if (
        requests_root.name != "requests"
        or not path.name.endswith(".prime.request.json")
    ):
        raise Task9Rejected("task9_priming_request_namespace_invalid")
    authority_path = _contained_path(
        cache_authority_path,
        validation_output_root / "cache-authority",
        code="task9_cache_authority_path_escape",
    )
    if authority_path.name != "TASK9_TYPED_CACHE_AUTHORITY.json":
        raise Task9Rejected("task9_cache_authority_path_invalid")
    authority = _load_rooted_json(
        authority_path,
        root_field="authority_root_sha256",
        code="task9_cache_authority",
    )
    payload = _request_payload(
        schema=PRIMING_REQUEST_SCHEMA,
        launch_nonce=launch_nonce,
        expected_orchestrator_pid=os.getpid(),
        values={
            "validation_output_root": str(validation_output_root),
            "cache_authority_path": str(authority_path),
            "cache_authority_file_sha256": file_sha256(authority_path),
            "cache_authority_root_sha256": authority["authority_root_sha256"],
            "complete_input_inventory_root_sha256": authority["input_inventory"][
                "inventory_root_sha256"
            ],
            "receipt_path": str(
                path.with_name(path.stem + ".receipt.json").resolve()
            ),
        },
    )
    atomic_write_json(path, payload)
    return Path(path)


def execute_priming_request(request_path: Path) -> Path:
    request = _load_request(request_path, schema=PRIMING_REQUEST_SCHEMA)
    request_path = Path(request_path).resolve(strict=True)
    validation_output_root = request_path.parent.parent.resolve(strict=True)
    if (
        request_path.parent.name != "requests"
        or request.get("validation_output_root") != str(validation_output_root)
        or not request_path.name.endswith(".prime.request.json")
    ):
        raise Task9Rejected("task9_priming_request_namespace_invalid")
    authority_path = _contained_path(
        Path(str(request.get("cache_authority_path") or "")),
        validation_output_root / "cache-authority",
        code="task9_cache_authority_path_escape",
    )
    if authority_path.name != "TASK9_TYPED_CACHE_AUTHORITY.json":
        raise Task9Rejected("task9_cache_authority_path_invalid")
    receipt_path = Path(str(request.get("receipt_path") or ""))
    receipt_parent = receipt_path.parent
    try:
        resolved_receipt_parent = receipt_parent.resolve(strict=True)
    except OSError:
        raise Task9Rejected("task9_priming_receipt_path_escape") from None
    if resolved_receipt_parent != (validation_output_root / "requests"):
        raise Task9Rejected("task9_priming_receipt_path_escape")
    receipt_path = receipt_parent / receipt_path.name
    if receipt_path.name != request_path.name.replace(".json", ".receipt.json"):
        raise Task9Rejected("task9_priming_receipt_identity_invalid")
    if receipt_path.exists() or receipt_path.is_symlink():
        raise Task9Rejected("task9_priming_receipt_must_be_new")
    started = time.perf_counter()
    authority = verify_cache_authority(
        authority_path,
        expected_file_sha256=str(request["cache_authority_file_sha256"]),
    )
    if (
        request.get("cache_authority_root_sha256")
        != authority["authority_root_sha256"]
        or request.get("complete_input_inventory_root_sha256")
        != authority["input_inventory"]["inventory_root_sha256"]
    ):
        raise Task9Rejected("task9_priming_request_authority_binding_invalid")
    elapsed = time.perf_counter() - started
    input_inventory = authority["input_inventory"]
    core = {
        "schema": PRIMING_RECEIPT_SCHEMA,
        "status": PRIMING_STATUS,
        "cache_inventory_root_sha256": authority["typed_cache"][
            "inventory_root_sha256"
        ],
        "complete_input_inventory_root_sha256": input_inventory[
            "inventory_root_sha256"
        ],
        "request": {
            "path": str(Path(request_path).resolve()),
            "file_sha256": file_sha256(request_path),
            "request_root_sha256": request["request_root_sha256"],
        },
        "cache_authority": {
            "path": str(Path(request["cache_authority_path"]).resolve()),
            "file_sha256": request["cache_authority_file_sha256"],
            "authority_root_sha256": authority["authority_root_sha256"],
        },
        "measurement_process": {
            "pid": os.getpid(),
            "parent_pid": os.getppid(),
            "launch_nonce_sha256": _current_launch_nonce_sha256(),
        },
        "primed_logical_bytes": int(input_inventory["logical_bytes"]),
        "priming_wall_seconds": elapsed,
        "sequential_read_and_hash_complete": True,
        "os_page_cache_controlled": False,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
        "real_order_transmission_possible": False,
        "economic_values_exposed": False,
        "acceptance_authorized": False,
    }
    assert_outcome_blind(core)
    receipt = {**core, "receipt_root_sha256": stable_sha256(core)}
    atomic_write_json(receipt_path, receipt)
    return receipt_path


def make_trial_request(
    *,
    path: Path,
    trial_id: str,
    output_dir: Path,
    cache_authority_path: Path,
    launch_nonce: str,
    priming_receipt_path: Path | None,
) -> Path:
    path = Path(path)
    output_dir = Path(output_dir)
    if not trial_id or output_dir.exists() or output_dir.is_symlink():
        raise Task9Rejected("task9_trial_request_output_invalid")
    try:
        requests_root = path.parent.resolve(strict=True)
        validation_output_root = requests_root.parent.resolve(strict=True)
        trials_root = output_dir.parent.resolve(strict=True)
    except OSError:
        raise Task9Rejected("task9_trial_request_namespace_invalid") from None
    if (
        requests_root.name != "requests"
        or path.name != f"{trial_id}.trial.request.json"
        or trials_root != (validation_output_root / "trials").resolve(strict=True)
        or output_dir.name != trial_id
    ):
        raise Task9Rejected("task9_trial_request_namespace_invalid")
    authority_path = _contained_path(
        cache_authority_path,
        validation_output_root / "cache-authority",
        code="task9_cache_authority_path_escape",
    )
    if authority_path.name != "TASK9_TYPED_CACHE_AUTHORITY.json":
        raise Task9Rejected("task9_cache_authority_path_invalid")
    contained_priming_receipt: Path | None = None
    if priming_receipt_path is not None:
        contained_priming_receipt = _contained_path(
            priming_receipt_path,
            requests_root,
            code="task9_priming_receipt_path_escape",
        )
    authority = _load_rooted_json(
        authority_path,
        root_field="authority_root_sha256",
        code="task9_cache_authority",
    )
    payload = _request_payload(
        schema=TRIAL_REQUEST_SCHEMA,
        launch_nonce=launch_nonce,
        expected_orchestrator_pid=os.getpid(),
        values={
            "validation_output_root": str(validation_output_root),
            "trial_id": trial_id,
            "output_dir": str(output_dir.resolve()),
            "cache_authority_path": str(authority_path),
            "cache_authority_file_sha256": file_sha256(authority_path),
            "cache_authority_root_sha256": authority["authority_root_sha256"],
            "complete_input_inventory_root_sha256": authority["input_inventory"][
                "inventory_root_sha256"
            ],
            "priming_receipt_path": (
                str(contained_priming_receipt)
                if contained_priming_receipt is not None
                else None
            ),
            "priming_receipt_file_sha256": (
                file_sha256(contained_priming_receipt)
                if contained_priming_receipt is not None
                else None
            ),
        },
    )
    atomic_write_json(path, payload)
    return Path(path)


def _process_create_time() -> float | None:
    try:
        import psutil

        return float(psutil.Process(os.getpid()).create_time())
    except Exception:
        return None


def _source_cache_metrics(partial: Mapping[str, Any]) -> dict[str, Any]:
    authority = partial.get("source_acceleration_authority")
    metrics = authority.get("typed_cache_metrics") if isinstance(authority, Mapping) else None
    if not isinstance(metrics, Mapping):
        raise Task9Rejected("task9_trial_typed_cache_metrics_missing")
    return dict(metrics)


def execute_trial_request(request_path: Path) -> Path:
    child_started = time.perf_counter()
    before_resource = slice_metrics._resource_snapshot()
    swap_before = slice_metrics._swap_used_bytes()
    request = _load_request(request_path, schema=TRIAL_REQUEST_SCHEMA)
    request_path = Path(request_path).resolve(strict=True)
    validation_output_root = request_path.parent.parent.resolve(strict=True)
    trial_id = str(request.get("trial_id") or "")
    if (
        request_path.parent.name != "requests"
        or request.get("validation_output_root") != str(validation_output_root)
        or request_path.name != f"{trial_id}.trial.request.json"
    ):
        raise Task9Rejected("task9_trial_request_namespace_invalid")
    authority_path = _contained_path(
        Path(str(request.get("cache_authority_path") or "")),
        validation_output_root / "cache-authority",
        code="task9_cache_authority_path_escape",
    )
    if authority_path.name != "TASK9_TYPED_CACHE_AUTHORITY.json":
        raise Task9Rejected("task9_cache_authority_path_invalid")
    output_dir = Path(str(request.get("output_dir") or ""))
    if (
        output_dir.parent.resolve(strict=True)
        != (validation_output_root / "trials").resolve(strict=True)
        or output_dir.name != trial_id
    ):
        raise Task9Rejected("task9_trial_output_path_escape")
    if output_dir.exists() or output_dir.is_symlink():
        raise Task9Rejected("task9_trial_output_must_be_new")
    cache_auth_started = time.perf_counter()
    authority = verify_cache_authority(
        authority_path,
        expected_file_sha256=str(request["cache_authority_file_sha256"]),
    )
    if (
        request.get("cache_authority_root_sha256")
        != authority["authority_root_sha256"]
        or request.get("complete_input_inventory_root_sha256")
        != authority["input_inventory"]["inventory_root_sha256"]
    ):
        raise Task9Rejected("task9_trial_request_authority_binding_invalid")
    cache_auth_seconds = time.perf_counter() - cache_auth_started
    typed_cache = authority["typed_cache"]
    cache_state = derive_cache_state(
        priming_receipt_path=(
            Path(request["priming_receipt_path"])
            if request.get("priming_receipt_path") is not None
            else None
        ),
        priming_receipt_file_sha256=request.get("priming_receipt_file_sha256"),
        expected_cache_inventory_root_sha256=str(
            typed_cache["inventory_root_sha256"]
        ),
        expected_cache_authority_path=Path(request["cache_authority_path"]),
        expected_cache_authority_file_sha256=str(
            request["cache_authority_file_sha256"]
        ),
        expected_cache_authority_root_sha256=str(
            request["cache_authority_root_sha256"]
        ),
        expected_complete_input_inventory_root_sha256=str(
            request["complete_input_inventory_root_sha256"]
        ),
        expected_validation_output_root=validation_output_root,
        current_launch_nonce_sha256=_current_launch_nonce_sha256(),
    )
    pre_cache = inventory_tree(Path(typed_cache["root"]))
    profiler = benchmark.ReplayStageProfiler(enabled=True)
    execution = task8.run_task8_exact_execution(
        output_dir,
        typed_cache_authority_root=Path(typed_cache["root"]),
        stage_profiler=profiler,
    )
    partial = execution["partial"]
    parity = execution["parity"]
    semantic_projection = semantic_trial_projection(parity)
    semantic_root = stable_sha256(semantic_projection)
    rederived_semantic = rederive_semantic_projection_from_ledgers(output_dir)
    if (
        rederived_semantic["semantic_projection"] != semantic_projection
        or rederived_semantic["semantic_projection_root_sha256"] != semantic_root
    ):
        raise Task9Rejected("task9_semantic_projection_raw_ledger_mismatch")
    post_cache = inventory_tree(Path(typed_cache["root"]))
    metrics = _source_cache_metrics(partial)
    if int(metrics.get("cold_partition_count") or 0) != 0:
        raise Task9Rejected("task9_trial_cache_rebuilt")
    if int(metrics.get("bytes_written") or 0) != 0:
        raise Task9Rejected("task9_trial_cache_written")
    if (
        pre_cache["inventory_root_sha256"]
        != post_cache["inventory_root_sha256"]
        or post_cache["inventory_root_sha256"]
        != typed_cache["inventory_root_sha256"]
    ):
        raise Task9Rejected("task9_trial_cache_drift")
    progress = partial.get("progress_rows")
    if not isinstance(progress, list) or len(progress) != 2:
        raise Task9Rejected("task9_trial_progress_invalid")
    try:
        no_event_economic = float(progress[0]["economic_hot_path_seconds"])
        no_event_proof = float(progress[0]["proof_finalization_seconds"])
        dense_economic = float(progress[1]["economic_hot_path_seconds"])
        dense_proof = float(progress[1]["proof_finalization_seconds"])
    except (KeyError, TypeError, ValueError):
        raise Task9Rejected("task9_trial_progress_timing_invalid") from None
    if not all(
        _finite_nonnegative(value)
        for value in (
            no_event_economic,
            no_event_proof,
            dense_economic,
            dense_proof,
        )
    ):
        raise Task9Rejected("task9_trial_progress_timing_invalid")
    output_inventory_started = time.perf_counter()
    evidence_inventory = inventory_tree(output_dir)
    semantic_diagnostic_inventory = inventory_tree(
        _semantic_diagnostic_root(output_dir)
    )
    output_tree = _compact_inventory(evidence_inventory)
    output_inventory_seconds = time.perf_counter() - output_inventory_started
    child_wall = time.perf_counter() - child_started
    after_resource = slice_metrics._resource_snapshot()
    resource_delta = slice_metrics._resource_delta(
        before_resource,
        after_resource,
        wall_seconds=child_wall,
    )
    swap_after = slice_metrics._swap_used_bytes()
    no_event_total = no_event_economic + no_event_proof
    dense_total = dense_economic + dense_proof
    fixed_overhead = child_wall - no_event_total - dense_total
    if fixed_overhead < -0.05:
        raise Task9Rejected("task9_trial_timing_reconciliation_negative")
    fixed_overhead = max(0.0, fixed_overhead)
    runtime_contract = execution["runtime_contract"]
    shared_contract = execution["shared_contract"]
    core = {
        "schema": TRIAL_RECEIPT_SCHEMA,
        "status": TRIAL_STATUS,
        "trial_id": str(request["trial_id"]),
        "derived_cache_state": cache_state["cache_state"],
        "cache_state_evidence": cache_state,
        "request": {
            "path": str(Path(request_path).resolve()),
            "file_sha256": file_sha256(request_path),
            "request_root_sha256": request["request_root_sha256"],
        },
        "measurement_process": {
            "pid": os.getpid(),
            "parent_pid": os.getppid(),
            "process_create_time": _process_create_time(),
            "launch_nonce_sha256": _current_launch_nonce_sha256(),
        },
        "execution_contract": {
            "arm_id": "S0R0",
            "arm_fingerprint_sha256": task8.semantic.EXPECTED_ARM_FINGERPRINT,
            "source_plan_digest_sha256": task8.semantic.EXPECTED_SOURCE_PLAN_DIGEST,
            "shared_execution_contract_digest_sha256": shared_contract.get(
                "shared_execution_contract_digest_sha256"
            ),
            "runtime_input_contract_root_sha256": runtime_contract.get(
                "contract_root_sha256"
            ),
            "prepared_pack_roots": {
                ":".join(key): value for key, value in task8.TASK8_PACK_ROOTS.items()
            },
        },
        "semantic_projection": semantic_projection,
        "semantic_projection_root_sha256": semantic_root,
        "semantic_projection_derivation": rederived_semantic,
        "parity": {
            "meaningful_difference_count": parity[
                "meaningful_difference_count"
            ],
            "unknown_difference_count": parity["unknown_difference_count"],
            "tick_sparse_cache_raw_source_full_hash_count": parity[
                "tick_sparse_cache_raw_source_full_hash_count"
            ],
            "tick_sparse_cache_sealed_reuse_count": parity[
                "tick_sparse_cache_sealed_reuse_count"
            ],
        },
        "cache": {
            "inventory_root_sha256": typed_cache["inventory_root_sha256"],
            "pre_inventory_root_sha256": pre_cache[
                "inventory_root_sha256"
            ],
            "post_inventory_root_sha256": post_cache[
                "inventory_root_sha256"
            ],
            "file_count": int(post_cache["file_count"]),
            "logical_bytes": int(post_cache["logical_bytes"]),
            "cold_partition_count": int(metrics.get("cold_partition_count") or 0),
            "warm_partition_count": int(metrics.get("warm_partition_count") or 0),
            "logical_bytes_read": int(metrics.get("bytes_read") or 0),
            "bytes_written": int(metrics.get("bytes_written") or 0),
        },
        "measurement": {
            **resource_delta,
            "child_wall_seconds": child_wall,
            "cache_authentication_seconds": cache_auth_seconds,
            "engine_wall_seconds": float(execution["engine_wall_seconds"]),
            "engine_cpu_seconds": float(execution["engine_cpu_seconds"]),
            "parity_verification_seconds": float(
                execution["parity_verification_seconds"]
            ),
            "output_inventory_seconds": output_inventory_seconds,
            "no_event_economic_hot_path_seconds": no_event_economic,
            "no_event_proof_finalization_seconds": no_event_proof,
            "no_event_total_seconds": no_event_total,
            "dense_economic_hot_path_seconds": dense_economic,
            "dense_proof_finalization_seconds": dense_proof,
            "dense_total_seconds": dense_total,
            "fixed_campaign_overhead_seconds": fixed_overhead,
            "swap_used_start_bytes": swap_before,
            "swap_used_end_bytes": swap_after,
            "swap_used_delta_bytes": (
                0
                if swap_before is None or swap_after is None
                else max(0, int(swap_after) - int(swap_before))
            ),
            "swap_counter_scope": "machine_wide_not_child_attributable",
        },
        "stage_profile": profiler.to_payload(),
        "evidence_inventory": evidence_inventory,
        "semantic_diagnostic_inventory": semantic_diagnostic_inventory,
        "evidence_inventory_policy": {
            "excluded_envelope_paths": sorted(TRIAL_ENVELOPE_PATHS),
            "excluded_paths_are_non_parity_envelope_only": True,
            "all_replay_evidence_files_included": True,
        },
        "output_tree": output_tree,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
        "real_order_transmission_possible": False,
        "economic_values_exposed": False,
        "acceptance_authorized": False,
    }
    assert_outcome_blind(core)
    validate_trial_receipt(core)
    receipt = {**core, "receipt_root_sha256": stable_sha256(core)}
    receipt_path = output_dir / TRIAL_RECEIPT_NAME
    atomic_write_json(receipt_path, receipt)
    seal_core = {
        "schema": TRIAL_SEAL_SCHEMA,
        "status": "TASK9_EXACT_TRIAL_SEALED_AFTER_PARITY",
        "trial_id": str(request["trial_id"]),
        "receipt_path": str(receipt_path.resolve()),
        "receipt_file_sha256": file_sha256(receipt_path),
        "receipt_root_sha256": receipt["receipt_root_sha256"],
        "semantic_projection_root_sha256": semantic_root,
        "evidence_inventory_root_sha256": evidence_inventory[
            "inventory_root_sha256"
        ],
        "semantic_diagnostic_inventory_root_sha256": (
            semantic_diagnostic_inventory["inventory_root_sha256"]
        ),
        "request_root_sha256": request["request_root_sha256"],
        "cache_authority_root_sha256": authority["authority_root_sha256"],
        "broker_live_authority": False,
        "economic_values_exposed": False,
        "acceptance_authorized": False,
    }
    seal = {**seal_core, "seal_root_sha256": stable_sha256(seal_core)}
    atomic_write_json(output_dir / TRIAL_SEAL_NAME, seal)
    _make_read_only(output_dir)
    _make_read_only(_semantic_diagnostic_root(output_dir))
    _assert_tree_read_only(
        output_dir,
        code="task9_trial_namespace_not_read_only",
    )
    _assert_tree_read_only(
        _semantic_diagnostic_root(output_dir),
        code="task9_trial_semantic_namespace_not_read_only",
    )
    validate_inventory_binding(
        output_dir,
        evidence_inventory,
        excluded_relative_paths=TRIAL_ENVELOPE_PATHS,
    )
    validate_inventory_binding(
        _semantic_diagnostic_root(output_dir),
        semantic_diagnostic_inventory,
    )
    return receipt_path


def load_sealed_trial(receipt_path: Path) -> dict[str, Any]:
    receipt_path = Path(receipt_path)
    receipt = _load_rooted_json(
        receipt_path,
        root_field="receipt_root_sha256",
        code="task9_trial_receipt",
    )
    validate_trial_receipt(receipt)
    evidence_inventory = receipt["evidence_inventory"]
    if evidence_inventory.get("root") != str(receipt_path.parent.resolve()):
        raise Task9Rejected("task9_trial_evidence_root_invalid")
    validate_inventory_binding(
        receipt_path.parent,
        evidence_inventory,
        excluded_relative_paths=TRIAL_ENVELOPE_PATHS,
    )
    semantic_inventory = receipt["semantic_diagnostic_inventory"]
    semantic_root_path = _semantic_diagnostic_root(receipt_path.parent)
    if semantic_inventory.get("root") != str(semantic_root_path.resolve()):
        raise Task9Rejected("task9_trial_semantic_evidence_root_invalid")
    validate_inventory_binding(semantic_root_path, semantic_inventory)
    _assert_tree_read_only(
        receipt_path.parent,
        code="task9_trial_namespace_not_read_only",
    )
    _assert_tree_read_only(
        semantic_root_path,
        code="task9_trial_semantic_namespace_not_read_only",
    )
    rederived_semantic = rederive_semantic_projection_from_ledgers(
        receipt_path.parent
    )
    if (
        rederived_semantic != receipt.get("semantic_projection_derivation")
        or rederived_semantic["semantic_projection"]
        != receipt.get("semantic_projection")
    ):
        raise Task9Rejected("task9_semantic_projection_raw_ledger_mismatch")
    request_binding = receipt.get("request")
    if not isinstance(request_binding, Mapping):
        raise Task9Rejected("task9_trial_request_binding_invalid")
    request_path = Path(str(request_binding.get("path") or ""))
    request_path = request_path.resolve(strict=True)
    validation_output_root = request_path.parent.parent.resolve(strict=True)
    trial_id = str(receipt.get("trial_id") or "")
    if (
        request_path.parent.name != "requests"
        or request_path.name != f"{trial_id}.trial.request.json"
        or receipt_path.parent != validation_output_root / "trials" / trial_id
    ):
        raise Task9Rejected("task9_trial_request_namespace_invalid")
    request = _load_rooted_json(
        request_path,
        root_field="request_root_sha256",
        code="task9_trial_request",
        expected_file_sha256=str(request_binding.get("file_sha256") or ""),
    )
    if (
        request.get("schema") != TRIAL_REQUEST_SCHEMA
        or request.get("validation_output_root") != str(validation_output_root)
        or request_binding.get("path") != str(request_path.resolve())
        or request_binding.get("request_root_sha256")
        != request.get("request_root_sha256")
        or request.get("trial_id") != receipt.get("trial_id")
        or request.get("output_dir") != str(receipt_path.parent.resolve())
    ):
        raise Task9Rejected("task9_trial_request_binding_invalid")
    authority_path = _contained_path(
        Path(str(request.get("cache_authority_path") or "")),
        validation_output_root / "cache-authority",
        code="task9_cache_authority_path_escape",
    )
    if authority_path.name != "TASK9_TYPED_CACHE_AUTHORITY.json":
        raise Task9Rejected("task9_cache_authority_path_invalid")
    authority = verify_cache_authority(
        authority_path,
        expected_file_sha256=str(request.get("cache_authority_file_sha256") or ""),
    )
    if (
        request.get("cache_authority_root_sha256")
        != authority["authority_root_sha256"]
        or request.get("complete_input_inventory_root_sha256")
        != authority["input_inventory"]["inventory_root_sha256"]
    ):
        raise Task9Rejected("task9_trial_request_authority_binding_invalid")
    derived = derive_cache_state(
        priming_receipt_path=(
            Path(request["priming_receipt_path"])
            if request.get("priming_receipt_path") is not None
            else None
        ),
        priming_receipt_file_sha256=request.get("priming_receipt_file_sha256"),
        expected_cache_inventory_root_sha256=authority["typed_cache"][
            "inventory_root_sha256"
        ],
        expected_cache_authority_path=Path(request["cache_authority_path"]),
        expected_cache_authority_file_sha256=request[
            "cache_authority_file_sha256"
        ],
        expected_cache_authority_root_sha256=request[
            "cache_authority_root_sha256"
        ],
        expected_complete_input_inventory_root_sha256=request[
            "complete_input_inventory_root_sha256"
        ],
        expected_validation_output_root=validation_output_root,
        current_launch_nonce_sha256=receipt["measurement_process"][
            "launch_nonce_sha256"
        ],
    )
    if derived != receipt.get("cache_state_evidence"):
        raise Task9Rejected("task9_cache_state_evidence_drift")
    seal_path = receipt_path.with_name(TRIAL_SEAL_NAME)
    seal = _load_rooted_json(
        seal_path,
        root_field="seal_root_sha256",
        code="task9_trial_seal",
    )
    if (
        seal.get("schema") != TRIAL_SEAL_SCHEMA
        or seal.get("status") != "TASK9_EXACT_TRIAL_SEALED_AFTER_PARITY"
        or seal.get("receipt_path") != str(Path(receipt_path).resolve())
        or seal.get("receipt_file_sha256") != file_sha256(receipt_path)
        or seal.get("receipt_root_sha256") != receipt["receipt_root_sha256"]
        or seal.get("semantic_projection_root_sha256")
        != receipt["semantic_projection_root_sha256"]
        or seal.get("evidence_inventory_root_sha256")
        != receipt["evidence_inventory"]["inventory_root_sha256"]
        or seal.get("semantic_diagnostic_inventory_root_sha256")
        != receipt["semantic_diagnostic_inventory"]["inventory_root_sha256"]
        or seal.get("request_root_sha256") != request["request_root_sha256"]
        or seal.get("cache_authority_root_sha256")
        != authority["authority_root_sha256"]
    ):
        raise Task9Rejected("task9_trial_seal_binding_invalid")
    return receipt


def parse_macos_time_lp(path: Path) -> dict[str, Any]:
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise Task9Rejected("task9_independent_time_evidence_missing")
    labels = {
        "real": ("real_seconds", float),
        "user": ("user_seconds", float),
        "sys": ("system_seconds", float),
        "maximum resident set size": (
            "maximum_resident_set_size_bytes",
            int,
        ),
        "block input operations": ("block_input_operations", int),
        "block output operations": ("block_output_operations", int),
    }
    parsed: dict[str, Any] = {}
    try:
        lines = path.read_text(encoding="ascii").splitlines()
    except (OSError, UnicodeError):
        raise Task9Rejected("task9_independent_time_evidence_invalid") from None
    for raw_line in lines:
        line = raw_line.strip()
        for label, (field, converter) in labels.items():
            if label in {"real", "user", "sys"}:
                parts = line.split()
                if len(parts) != 2 or parts[0] != label:
                    continue
                raw_value = parts[1]
            elif line.endswith(label):
                raw_value = line[: -len(label)].strip()
            else:
                continue
            try:
                value = converter(raw_value)
            except (TypeError, ValueError):
                raise Task9Rejected("task9_independent_time_evidence_invalid") from None
            if not _finite_nonnegative(value) or field in parsed:
                raise Task9Rejected("task9_independent_time_evidence_invalid")
            parsed[field] = value
            break
    if set(parsed) != {field for field, _ in labels.values()}:
        raise Task9Rejected("task9_independent_time_evidence_invalid")
    return parsed


def validate_independent_time_metrics(
    metrics: Mapping[str, Any],
    trial: Mapping[str, Any],
    observation: Mapping[str, Any],
) -> dict[str, Any]:
    required = {
        "real_seconds",
        "user_seconds",
        "system_seconds",
        "maximum_resident_set_size_bytes",
        "block_input_operations",
        "block_output_operations",
    }
    if set(metrics) != required or any(
        not _finite_nonnegative(metrics.get(field)) for field in required
    ):
        raise Task9Rejected("task9_independent_time_evidence_invalid")
    measurement = trial.get("measurement")
    if not isinstance(measurement, Mapping):
        raise Task9Rejected("task9_independent_time_evidence_invalid")
    parent_wall = float(observation.get("parent_observed_wall_seconds") or -1.0)
    raw_wall = float(metrics["real_seconds"])
    if not _finite_nonnegative(parent_wall) or abs(raw_wall - parent_wall) > max(
        2.0, 0.02 * parent_wall
    ):
        raise Task9Rejected("task9_independent_time_wall_mismatch")
    for raw_field, measurement_field in (
        ("user_seconds", "cpu_user_seconds"),
        ("system_seconds", "cpu_system_seconds"),
    ):
        observed = float(measurement.get(measurement_field) or -1.0)
        raw = float(metrics[raw_field])
        if not _finite_nonnegative(observed) or abs(raw - observed) > max(
            2.0, 0.02 * max(raw, observed)
        ):
            raise Task9Rejected("task9_independent_time_cpu_mismatch")
    child_peak = float(measurement.get("peak_rss_bytes") or -1.0)
    raw_peak = float(metrics["maximum_resident_set_size_bytes"])
    if not _finite_nonnegative(child_peak) or abs(raw_peak - child_peak) > max(
        4096.0, 0.02 * max(raw_peak, child_peak)
    ):
        raise Task9Rejected("task9_independent_time_rss_mismatch")
    profile = trial.get("stage_profile")
    bounds = profile.get("resource_bounds") if isinstance(profile, Mapping) else None
    if not isinstance(bounds, Mapping):
        raise Task9Rejected("task9_independent_time_io_mismatch")
    for raw_field, child_field, profile_field in (
        (
            "block_input_operations",
            "block_input_operations",
            "block_input_operations",
        ),
        (
            "block_output_operations",
            "block_output_operations",
            "block_output_operations",
        ),
    ):
        raw_value = float(metrics[raw_field])
        child_value = measurement.get(child_field)
        if not _finite_nonnegative(child_value) or abs(
            raw_value - float(child_value)
        ) > max(1.0, 0.05 * max(raw_value, float(child_value))):
            raise Task9Rejected("task9_independent_time_io_mismatch")
        first = bounds.get("first")
        last = bounds.get("last")
        if not isinstance(first, Mapping) or not isinstance(last, Mapping):
            raise Task9Rejected("task9_independent_time_io_mismatch")
        profile_delta = int(last.get(profile_field) or 0) - int(
            first.get(profile_field) or 0
        )
        if profile_delta < 0 or profile_delta > max(
            raw_value, float(child_value)
        ) + 1.0:
            raise Task9Rejected("task9_independent_time_io_mismatch")
    return dict(metrics)


def _process_group_exists(process_group_id: int) -> bool:
    try:
        os.killpg(int(process_group_id), 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError as exc:
        if exc.errno == errno.ESRCH:
            return False
        raise


def _wait_process_group_exit(process_group_id: int, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while _process_group_exists(process_group_id):
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.05)
    return True


def _terminate_process_group(process: subprocess.Popen[bytes]) -> None:
    process_group_id = int(process.pid)
    if process_group_id <= 1 or process_group_id == os.getpgrp():
        raise Task9Rejected("task9_process_group_identity_invalid")
    if not _process_group_exists(process_group_id):
        try:
            process.wait(timeout=0.0)
        except (subprocess.TimeoutExpired, ChildProcessError):
            pass
        return
    try:
        os.killpg(process_group_id, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=5.0)
    except (subprocess.TimeoutExpired, ChildProcessError):
        pass
    if _wait_process_group_exit(process_group_id, 5.0):
        return
    try:
        os.killpg(process_group_id, signal.SIGKILL)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=5.0)
    except (subprocess.TimeoutExpired, ChildProcessError):
        pass
    if not _wait_process_group_exit(process_group_id, 5.0):
        raise Task9Rejected("task9_process_group_cleanup_failed")


def _assert_process_group_reaped(
    process: subprocess.Popen[bytes],
    *,
    code: str,
) -> None:
    if _process_group_exists(int(process.pid)):
        _terminate_process_group(process)
        raise Task9Rejected(code)


def _stdout_receipt_path(path: Path) -> Path:
    try:
        lines = [line for line in Path(path).read_bytes().splitlines() if line.strip()]
        payload = json.loads(lines[-1] if lines else b"")
        receipt = Path(str(payload.get("receipt") or ""))
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise Task9Rejected("task9_worker_stdout_invalid") from None
    if receipt.is_symlink() or not receipt.is_file():
        raise Task9Rejected("task9_worker_receipt_missing")
    return receipt


def _run_priming_subprocess(
    *,
    request_path: Path,
    launch_nonce: str,
    log_root: Path,
    label: str,
) -> Path:
    stdout_path = Path(log_root) / f"{label}.prime.stdout.log"
    stderr_path = Path(log_root) / f"{label}.prime.stderr.log"
    env = dict(os.environ)
    env[TASK9_LAUNCH_NONCE_ENV] = launch_nonce
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                MODULE_NAME,
                "prime",
                "--request",
                str(request_path),
            ],
            cwd=ROOT,
            env=env,
            stdout=stdout,
            stderr=stderr,
            start_new_session=True,
        )
        try:
            returncode = process.wait(timeout=PRIMING_TIMEOUT_SECONDS)
            _assert_process_group_reaped(
                process,
                code="task9_priming_process_group_not_clean",
            )
        except subprocess.TimeoutExpired:
            _terminate_process_group(process)
            raise Task9Rejected("task9_priming_process_timeout") from None
        except BaseException:
            _terminate_process_group(process)
            raise
    if returncode != 0:
        detail = stderr_path.read_text(encoding="utf-8", errors="replace")[-4000:]
        raise Task9Rejected(
            f"task9_priming_process_failed:{returncode}:{detail}"
        )
    receipt_path = _stdout_receipt_path(stdout_path)
    _load_rooted_json(
        receipt_path,
        root_field="receipt_root_sha256",
        code="task9_priming_receipt",
    )
    return receipt_path


def _run_trial_subprocess(
    *,
    request_path: Path,
    launch_nonce: str,
    output_root: Path,
    trial_id: str,
) -> tuple[Path, Path]:
    try:
        import psutil
    except ImportError as exc:
        raise Task9Rejected("task9_psutil_required") from exc
    logs = Path(output_root) / "logs"
    observations = Path(output_root) / "observations"
    logs.mkdir(parents=True, exist_ok=True)
    observations.mkdir(parents=True, exist_ok=True)
    stdout_path = logs / f"{trial_id}.stdout.log"
    stderr_path = logs / f"{trial_id}.stderr.log"
    raw_time_path = logs / f"{trial_id}.time-lp.txt"
    env = dict(os.environ)
    env[TASK9_LAUNCH_NONCE_ENV] = launch_nonce
    command = [
        "/usr/bin/time",
        "-lp",
        "-o",
        str(raw_time_path),
        sys.executable,
        "-m",
        MODULE_NAME,
        "trial",
        "--request",
        str(request_path),
    ]
    virtual_start = psutil.virtual_memory()
    swap_start = psutil.swap_memory()
    peak_tree_rss = 0
    min_available = int(virtual_start.available)
    peak_swap_used = int(swap_start.used)
    sample_count = 0
    parent_started = time.perf_counter()
    deadline = time.monotonic() + TRIAL_TIMEOUT_SECONDS
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            env=env,
            stdout=stdout,
            stderr=stderr,
            start_new_session=True,
        )
        try:
            while process.poll() is None:
                if time.monotonic() >= deadline:
                    raise Task9Rejected(f"task9_trial_process_timeout:{trial_id}")
                sample_count += 1
                tree_rss = 0
                try:
                    leader = psutil.Process(process.pid)
                    tree_rss += int(leader.memory_info().rss)
                    for child in leader.children(recursive=True):
                        tree_rss += int(child.memory_info().rss)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                virtual = psutil.virtual_memory()
                swap = psutil.swap_memory()
                peak_tree_rss = max(peak_tree_rss, tree_rss)
                min_available = min(min_available, int(virtual.available))
                peak_swap_used = max(peak_swap_used, int(swap.used))
                time.sleep(0.2)
            returncode = process.wait()
            _assert_process_group_reaped(
                process,
                code="task9_trial_process_group_not_clean",
            )
        except BaseException:
            _terminate_process_group(process)
            raise
    parent_wall = time.perf_counter() - parent_started
    if returncode != 0:
        detail = stderr_path.read_text(encoding="utf-8", errors="replace")[-4000:]
        raise Task9Rejected(f"task9_trial_process_failed:{trial_id}:{returncode}:{detail}")
    receipt_path = _stdout_receipt_path(stdout_path)
    receipt = load_sealed_trial(receipt_path)
    swap_end = psutil.swap_memory()
    output_dir = Path(str(receipt_path.parent))
    final_output_tree = slice_metrics._tree_usage(output_dir)
    if not raw_time_path.is_file():
        raise Task9Rejected("task9_independent_time_evidence_missing")
    raw_time_metrics = parse_macos_time_lp(raw_time_path)
    observation_core = {
        "schema": OBSERVATION_SCHEMA,
        "status": "TASK9_PARENT_OBSERVED_TRIAL_COMPLETE",
        "trial_id": trial_id,
        "request_path": str(Path(request_path).resolve()),
        "request_file_sha256": file_sha256(request_path),
        "trial_receipt_path": str(receipt_path.resolve()),
        "trial_receipt_file_sha256": file_sha256(receipt_path),
        "trial_receipt_root_sha256": receipt["receipt_root_sha256"],
        "parent_observed_wall_seconds": parent_wall,
        "parent_peak_child_tree_rss_bytes": peak_tree_rss,
        "resource_sample_count": sample_count,
        "host_available_memory_start_bytes": int(virtual_start.available),
        "minimum_host_available_memory_bytes": min_available,
        "swap_used_start_bytes": int(swap_start.used),
        "swap_used_peak_bytes": peak_swap_used,
        "swap_used_end_bytes": int(swap_end.used),
        "swap_out_start_bytes": int(swap_start.sout),
        "swap_out_end_bytes": int(swap_end.sout),
        "swap_out_growth_bytes": max(0, int(swap_end.sout) - int(swap_start.sout)),
        "swap_counter_scope": "machine_wide_not_child_attributable",
        "output_tree": final_output_tree,
        "raw_time_evidence": {
            "path": str(raw_time_path.resolve()),
            "bytes": raw_time_path.stat().st_size,
            "sha256": file_sha256(raw_time_path),
            "format": "macos_usr_bin_time_lp",
            "parsed_metrics": raw_time_metrics,
        },
        "stdout": {
            "path": str(stdout_path.resolve()),
            "bytes": stdout_path.stat().st_size,
            "sha256": file_sha256(stdout_path),
        },
        "stderr": {
            "path": str(stderr_path.resolve()),
            "bytes": stderr_path.stat().st_size,
            "sha256": file_sha256(stderr_path),
        },
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
        "real_order_transmission_possible": False,
        "economic_values_exposed": False,
        "acceptance_authorized": False,
    }
    validate_independent_time_metrics(raw_time_metrics, receipt, observation_core)
    assert_outcome_blind(observation_core)
    observation = {
        **observation_core,
        "observation_root_sha256": stable_sha256(observation_core),
    }
    observation_path = observations / f"{trial_id}.json"
    atomic_write_json(observation_path, observation)
    return receipt_path, observation_path


def _load_observation(
    path: Path,
    *,
    trial: Mapping[str, Any] | None = None,
    allow_legacy_missing_parsed_metrics: bool = False,
) -> dict[str, Any]:
    path = Path(path)
    payload = _load_rooted_json(
        path,
        root_field="observation_root_sha256",
        code="task9_parent_observation",
    )
    if (
        payload.get("schema") != OBSERVATION_SCHEMA
        or payload.get("status") != "TASK9_PARENT_OBSERVED_TRIAL_COMPLETE"
        or payload.get("broker_live_authority") is not False
        or payload.get("broker_mutation_enabled") is not False
        or payload.get("real_order_transmission_possible") is not False
        or payload.get("economic_values_exposed") is not False
        or payload.get("acceptance_authorized") is not False
    ):
        raise Task9Rejected("task9_parent_observation_scope_invalid")
    assert_outcome_blind(payload)
    if trial is not None:
        path = path.resolve(strict=True)
        trial_id = str(trial.get("trial_id") or "")
        if (
            path.parent.name != "observations"
            or path.name != f"{trial_id}.json"
        ):
            raise Task9Rejected("task9_observation_namespace_invalid")
        output_root = path.parent.parent.resolve(strict=True)
        logs_root = output_root / "logs"
        raw_time = payload.get("raw_time_evidence")
        if (
            payload.get("trial_id") != trial_id
            or payload.get("trial_receipt_root_sha256")
            != trial.get("receipt_root_sha256")
            or not isinstance(raw_time, Mapping)
        ):
            raise Task9Rejected("task9_trial_observation_binding_invalid")
        expected_logs = {
            "raw_time_evidence": f"{trial_id}.time-lp.txt",
            "stdout": f"{trial_id}.stdout.log",
            "stderr": f"{trial_id}.stderr.log",
        }
        resolved_logs: dict[str, Path] = {}
        for field, expected_name in expected_logs.items():
            binding = payload.get(field)
            if not isinstance(binding, Mapping):
                raise Task9Rejected("task9_observation_log_binding_invalid")
            resolved = _contained_path(
                Path(str(binding.get("path") or "")),
                logs_root,
                code="task9_observation_log_path_escape",
            )
            if (
                resolved.name != expected_name
                or binding.get("bytes") != resolved.stat().st_size
                or binding.get("sha256") != file_sha256(resolved)
            ):
                raise Task9Rejected("task9_observation_log_binding_invalid")
            resolved_logs[field] = resolved
        raw_path = resolved_logs["raw_time_evidence"]
        if (
            raw_time.get("format") != "macos_usr_bin_time_lp"
        ):
            raise Task9Rejected("task9_independent_time_evidence_binding_invalid")
        parsed = parse_macos_time_lp(raw_path)
        declared_parsed = raw_time.get("parsed_metrics")
        if (
            declared_parsed != parsed
            and not (
                allow_legacy_missing_parsed_metrics
                and declared_parsed is None
            )
        ):
            raise Task9Rejected("task9_independent_time_evidence_binding_invalid")
        receipt_path = output_root / "trials" / trial_id / TRIAL_RECEIPT_NAME
        request_path = output_root / "requests" / f"{trial_id}.trial.request.json"
        if (
            payload.get("trial_receipt_path") != str(receipt_path.resolve(strict=True))
            or payload.get("trial_receipt_file_sha256")
            != file_sha256(receipt_path)
            or payload.get("request_path") != str(request_path.resolve(strict=True))
            or payload.get("request_file_sha256") != file_sha256(request_path)
        ):
            raise Task9Rejected("task9_trial_observation_binding_invalid")
        validate_independent_time_metrics(parsed, trial, payload)
    return payload


def _merge_parent_observation(
    trial: Mapping[str, Any], observation: Mapping[str, Any]
) -> dict[str, Any]:
    if (
        observation.get("trial_id") != trial.get("trial_id")
        or observation.get("trial_receipt_root_sha256")
        != trial.get("receipt_root_sha256")
    ):
        raise Task9Rejected("task9_trial_observation_binding_invalid")
    merged = json.loads(json.dumps(trial))
    measurement = merged["measurement"]
    measurement["parent_observed_wall_seconds"] = float(
        observation["parent_observed_wall_seconds"]
    )
    measurement["peak_rss_bytes"] = max(
        int(measurement["peak_rss_bytes"]),
        int(observation["parent_peak_child_tree_rss_bytes"]),
    )
    measurement["swap_used_delta_bytes"] = max(
        int(measurement.get("swap_used_delta_bytes") or 0),
        max(
            0,
            int(observation["swap_used_peak_bytes"])
            - int(observation["swap_used_start_bytes"]),
        ),
    )
    merged["output_tree"] = dict(observation["output_tree"])
    return merged


def _task9_targets(trials: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    warm_trials = [
        trial
        for trial in trials
        if trial.get("derived_cache_state") == WARM_FILESYSTEM_STATE
    ]
    if len(warm_trials) != 3:
        raise Task9Rejected("task9_warm_target_trial_count_invalid")
    allocated_rows = []
    for trial in warm_trials:
        measurement = trial["measurement"]
        no_event = float(measurement["no_event_total_seconds"])
        dense = float(measurement["dense_total_seconds"])
        parent_wall = float(
            measurement.get(
                "parent_observed_wall_seconds",
                measurement["child_wall_seconds"],
            )
        )
        residual = max(0.0, parent_wall - no_event - dense)
        allocated_rows.append(
            {
                "trial_id": trial["trial_id"],
                "parent_wall_seconds": parent_wall,
                "two_day_fixed_and_verification_residual_seconds": residual,
                "equal_per_observed_day_allocation_seconds": residual / 2.0,
                "no_event_allocated_envelope_seconds": no_event + residual / 2.0,
                "dense_allocated_envelope_seconds": dense + residual / 2.0,
            }
        )
    no_event_total_worst = max(
        row["no_event_allocated_envelope_seconds"] for row in allocated_rows
    )
    dense_total_worst = max(
        row["dense_allocated_envelope_seconds"] for row in allocated_rows
    )
    direct_no_event_worst = max(
        float(trial["measurement"]["no_event_total_seconds"])
        for trial in warm_trials
    )
    direct_dense_worst = max(
        float(trial["measurement"]["dense_total_seconds"])
        for trial in warm_trials
    )
    no_event_economic_worst = max(
        float(trial["measurement"]["no_event_economic_hot_path_seconds"])
        for trial in warm_trials
    )
    dense_economic_worst = max(
        float(trial["measurement"]["dense_economic_hot_path_seconds"])
        for trial in warm_trials
    )
    return {
        "controlling_cache_state": WARM_FILESYSTEM_STATE,
        "controlling_metric": (
            "standardized_per_day_envelope_with_equal_allocation_of_measured_"
            "two_day_fixed_and_verification_residual"
        ),
        "isolated_one_day_parent_wall_trials_available": False,
        "allocation_rows": allocated_rows,
        "no_event_total_target_seconds": 5.0,
        "no_event_total_worst_observed_seconds": no_event_total_worst,
        "no_event_total_target_met": no_event_total_worst <= 5.0,
        "dense_total_target_seconds": 180.0,
        "dense_total_worst_observed_seconds": dense_total_worst,
        "dense_total_target_met": dense_total_worst <= 180.0,
        "diagnostic_economic_hot_path": {
            "no_event_worst_seconds": no_event_economic_worst,
            "dense_worst_seconds": dense_economic_worst,
            "acceptance_metric": False,
        },
        "diagnostic_direct_day_total_including_proof_finalization": {
            "no_event_worst_seconds": direct_no_event_worst,
            "dense_worst_seconds": direct_dense_worst,
            "acceptance_metric": False,
        },
        "dense_target_disposition_if_missed": (
            "owner_adjusted_continuation_correctness_and_architecture_"
            "preserved_target_not_claimed_passed"
        ),
    }


def _verify_legacy_cache_authority_for_rebind(
    manifest_path: Path,
) -> dict[str, Any]:
    manifest_path = Path(manifest_path)
    payload = _load_rooted_json(
        manifest_path,
        root_field="authority_root_sha256",
        code="task9_legacy_cache_authority",
    )
    if (
        payload.get("schema") != LEGACY_CACHE_AUTHORITY_SCHEMA
        or payload.get("status") != CACHE_AUTHORITY_STATUS
        or payload.get("read_only_filesystem_mode") is not True
        or payload.get("broker_live_authority") is not False
        or payload.get("broker_mutation_enabled") is not False
        or payload.get("real_order_transmission_possible") is not False
        or payload.get("economic_values_exposed") is not False
        or payload.get("acceptance_authorized") is not False
    ):
        raise Task9Rejected("task9_legacy_cache_authority_scope_invalid")
    assert_outcome_blind(payload)
    manifest_path = manifest_path.resolve(strict=True)
    if manifest_path.name != "TASK9_TYPED_CACHE_AUTHORITY.json":
        raise Task9Rejected("task9_legacy_cache_authority_path_invalid")
    declared = payload.get("typed_cache")
    if not isinstance(declared, Mapping):
        raise Task9Rejected("task9_legacy_cache_authority_inventory_invalid")
    declared_root = Path(str(declared.get("root") or ""))
    expected_root = manifest_path.parent / "typed-cache"
    try:
        if (
            declared_root.is_symlink()
            or expected_root.is_symlink()
            or declared_root.resolve(strict=True) != expected_root.resolve(strict=True)
        ):
            raise Task9Rejected(
                "task9_legacy_cache_authority_typed_cache_escape"
            )
    except OSError:
        raise Task9Rejected(
            "task9_legacy_cache_authority_typed_cache_escape"
        ) from None
    current = inventory_tree(expected_root)
    for field in (
        "file_count",
        "logical_bytes",
        "allocated_bytes",
        "inventory_root_sha256",
    ):
        if current[field] != declared.get(field):
            raise Task9Rejected("task9_legacy_cache_authority_inventory_drift")
    _assert_tree_read_only(Path(current["root"]))
    current_inputs = _cache_input_inventory(Path(current["root"]))
    if current_inputs != payload.get("input_inventory"):
        raise Task9Rejected("task9_legacy_cache_input_inventory_drift")
    tick_authority, _ = _task8_tick_prewarm_authority()
    return {
        **payload,
        "verified_current_inventory": _compact_inventory(current),
        "task8_tick_prewarm_authority": tick_authority,
    }


def _legacy_cache_state_evidence(
    *,
    trial_id: str,
    trial_request: Mapping[str, Any],
    trial_receipt: Mapping[str, Any],
    authority_path: Path,
    authority: Mapping[str, Any],
    output_root: Path,
) -> dict[str, Any]:
    trial_nonce = trial_request.get("launch_nonce_sha256")
    process = trial_receipt.get("measurement_process")
    if (
        not _is_sha256(trial_nonce)
        or not isinstance(process, Mapping)
        or process.get("launch_nonce_sha256") != trial_nonce
    ):
        raise Task9Rejected("task9_legacy_trial_nonce_binding_invalid")
    base = {
        "cache_authority_root_sha256": authority["authority_root_sha256"],
        "cache_authority_file_sha256": file_sha256(authority_path),
        "complete_input_inventory_root_sha256": authority["input_inventory"][
            "inventory_root_sha256"
        ],
        "trial_launch_nonce_sha256": trial_nonce,
        "validation_output_root": str(Path(output_root).resolve()),
    }
    prime_receipt_path_raw = trial_request.get("priming_receipt_path")
    prime_receipt_hash = trial_request.get("priming_receipt_file_sha256")
    if prime_receipt_path_raw is None:
        if prime_receipt_hash is not None:
            raise Task9Rejected("task9_legacy_priming_evidence_incomplete")
        return {
            "cache_state": COLD_PROCESS_STATE,
            **base,
            "priming_request_path": None,
            "priming_request_file_sha256": None,
            "priming_request_root_sha256": None,
            "priming_receipt_path": None,
            "priming_receipt_file_sha256": None,
            "priming_receipt_root_sha256": None,
            "process_cold": True,
            "warm_filesystem_expected": False,
            "os_page_cache_controlled": False,
        }
    if not _is_sha256(prime_receipt_hash):
        raise Task9Rejected("task9_legacy_priming_evidence_incomplete")
    requests_root = Path(output_root) / "requests"
    prime_receipt_path = _contained_path(
        Path(str(prime_receipt_path_raw)),
        requests_root,
        code="task9_legacy_priming_receipt_escape",
    )
    if prime_receipt_path.name != f"{trial_id}.prime.request.receipt.json":
        raise Task9Rejected("task9_legacy_priming_receipt_identity_invalid")
    prime_receipt = _load_rooted_json(
        prime_receipt_path,
        root_field="receipt_root_sha256",
        code="task9_legacy_priming_receipt",
        expected_file_sha256=str(prime_receipt_hash),
    )
    prime_request_path = requests_root / f"{trial_id}.prime.request.json"
    prime_request = _load_rooted_json(
        prime_request_path,
        root_field="request_root_sha256",
        code="task9_legacy_priming_request",
    )
    prime_process = prime_receipt.get("measurement_process")
    expected_authority_path = str(Path(authority_path).resolve())
    if (
        prime_request.get("schema") != LEGACY_PRIMING_REQUEST_SCHEMA
        or prime_receipt.get("schema") != LEGACY_PRIMING_RECEIPT_SCHEMA
        or prime_receipt.get("status") != PRIMING_STATUS
        or not isinstance(prime_process, Mapping)
        or prime_process.get("launch_nonce_sha256")
        != prime_request.get("launch_nonce_sha256")
        or prime_process.get("launch_nonce_sha256") == trial_nonce
        or prime_request.get("receipt_path") != str(prime_receipt_path.resolve())
        or prime_request.get("cache_authority_path") != expected_authority_path
        or prime_request.get("cache_authority_file_sha256")
        != file_sha256(authority_path)
        or prime_receipt.get("cache_inventory_root_sha256")
        != authority["typed_cache"]["inventory_root_sha256"]
        or prime_receipt.get("complete_input_inventory_root_sha256")
        != authority["input_inventory"]["inventory_root_sha256"]
        or prime_receipt.get("sequential_read_and_hash_complete") is not True
        or prime_receipt.get("os_page_cache_controlled") is not False
        or prime_receipt.get("broker_live_authority") is not False
        or prime_receipt.get("broker_mutation_enabled") is not False
        or prime_receipt.get("real_order_transmission_possible") is not False
        or prime_receipt.get("economic_values_exposed") is not False
        or prime_receipt.get("acceptance_authorized") is not False
    ):
        raise Task9Rejected("task9_legacy_priming_binding_invalid")
    return {
        "cache_state": WARM_FILESYSTEM_STATE,
        **base,
        "priming_request_path": str(prime_request_path.resolve()),
        "priming_request_file_sha256": file_sha256(prime_request_path),
        "priming_request_root_sha256": prime_request["request_root_sha256"],
        "priming_receipt_path": str(prime_receipt_path.resolve()),
        "priming_receipt_file_sha256": file_sha256(prime_receipt_path),
        "priming_receipt_root_sha256": prime_receipt["receipt_root_sha256"],
        "priming_process_launch_nonce_sha256": prime_process[
            "launch_nonce_sha256"
        ],
        "process_cold": True,
        "warm_filesystem_expected": True,
        "os_page_cache_controlled": False,
    }


def _rebind_legacy_trial(
    *,
    trial_id: str,
    output_root: Path,
    parent_inventory: Mapping[str, Any],
    authority_path: Path,
    authority: Mapping[str, Any],
    reference_projection: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    trial_root = Path(output_root) / "trials" / trial_id
    receipt_path = trial_root / TRIAL_RECEIPT_NAME
    receipt = _load_rooted_json(
        receipt_path,
        root_field="receipt_root_sha256",
        code="task9_legacy_trial_receipt",
    )
    if (
        receipt.get("schema") != LEGACY_TRIAL_RECEIPT_SCHEMA
        or receipt.get("status") != TRIAL_STATUS
        or receipt.get("trial_id") != trial_id
        or receipt.get("broker_live_authority") is not False
        or receipt.get("economic_values_exposed") is not False
        or receipt.get("acceptance_authorized") is not False
    ):
        raise Task9Rejected("task9_legacy_trial_scope_invalid")
    request_binding = receipt.get("request")
    if not isinstance(request_binding, Mapping):
        raise Task9Rejected("task9_legacy_trial_request_binding_invalid")
    request_path = _contained_path(
        Path(str(request_binding.get("path") or "")),
        Path(output_root) / "requests",
        code="task9_legacy_trial_request_escape",
    )
    request = _load_rooted_json(
        request_path,
        root_field="request_root_sha256",
        code="task9_legacy_trial_request",
        expected_file_sha256=str(request_binding.get("file_sha256") or ""),
    )
    if (
        request.get("schema") != LEGACY_TRIAL_REQUEST_SCHEMA
        or request.get("trial_id") != trial_id
        or request.get("output_dir") != str(trial_root.resolve())
        or request_binding.get("request_root_sha256")
        != request.get("request_root_sha256")
        or request.get("cache_authority_path") != str(authority_path.resolve())
        or request.get("cache_authority_file_sha256") != file_sha256(authority_path)
    ):
        raise Task9Rejected("task9_legacy_trial_request_binding_invalid")
    cache_state_evidence = _legacy_cache_state_evidence(
        trial_id=trial_id,
        trial_request=request,
        trial_receipt=receipt,
        authority_path=authority_path,
        authority=authority,
        output_root=output_root,
    )
    if receipt.get("derived_cache_state") != cache_state_evidence["cache_state"]:
        raise Task9Rejected("task9_cache_state_relabelled")
    trial_inventory = _subtree_inventory(
        parent_inventory,
        relative_root=f"trials/{trial_id}",
        root_path=trial_root,
    )
    semantic_root_path = _semantic_diagnostic_root(trial_root)
    semantic_inventory = _subtree_inventory(
        parent_inventory,
        relative_root=f"trials/{trial_id}.semantic-diagnostic",
        root_path=semantic_root_path,
    )
    rederived_semantic = rederive_semantic_projection_from_ledgers(
        trial_root,
        reference_projection=reference_projection,
    )
    if (
        rederived_semantic["semantic_projection"]
        != receipt.get("semantic_projection")
        or rederived_semantic["semantic_projection_root_sha256"]
        != receipt.get("semantic_projection_root_sha256")
    ):
        raise Task9Rejected("task9_semantic_projection_raw_ledger_mismatch")
    upgraded = {
        **receipt,
        "schema": TRIAL_RECEIPT_SCHEMA,
        "cache_state_evidence": cache_state_evidence,
        "evidence_inventory": trial_inventory,
        "semantic_diagnostic_inventory": semantic_inventory,
        "semantic_projection_derivation": rederived_semantic,
        "evidence_inventory_policy": {
            "excluded_envelope_paths": sorted(TRIAL_ENVELOPE_PATHS),
            "excluded_paths_are_non_parity_envelope_only": True,
            "all_replay_evidence_files_included": True,
        },
    }
    validate_trial_receipt(upgraded)
    seal_path = trial_root / TRIAL_SEAL_NAME
    seal = _load_rooted_json(
        seal_path,
        root_field="seal_root_sha256",
        code="task9_legacy_trial_seal",
    )
    if (
        seal.get("schema") != LEGACY_TRIAL_SEAL_SCHEMA
        or seal.get("status") != "TASK9_EXACT_TRIAL_SEALED_AFTER_PARITY"
        or seal.get("trial_id") != trial_id
        or seal.get("receipt_path") != str(receipt_path.resolve())
        or seal.get("receipt_file_sha256") != file_sha256(receipt_path)
        or seal.get("receipt_root_sha256") != receipt["receipt_root_sha256"]
    ):
        raise Task9Rejected("task9_legacy_trial_seal_binding_invalid")
    observation_path = Path(output_root) / "observations" / f"{trial_id}.json"
    observation = _load_observation(
        observation_path,
        trial=upgraded,
        allow_legacy_missing_parsed_metrics=True,
    )
    raw_time = observation.get("raw_time_evidence")
    if not isinstance(raw_time, Mapping):
        raise Task9Rejected("task9_legacy_trial_observation_binding_invalid")
    raw_time_path = _contained_path(
        Path(str(raw_time.get("path") or "")),
        Path(output_root) / "logs",
        code="task9_legacy_time_evidence_escape",
    )
    if (
        raw_time.get("bytes") != raw_time_path.stat().st_size
        or raw_time.get("sha256") != file_sha256(raw_time_path)
        or raw_time.get("format") != "macos_usr_bin_time_lp"
    ):
        raise Task9Rejected("task9_legacy_time_evidence_binding_invalid")
    parsed_time = parse_macos_time_lp(raw_time_path)
    validate_independent_time_metrics(parsed_time, upgraded, observation)
    merged = _merge_parent_observation(upgraded, observation)
    binding = {
        "trial_id": trial_id,
        "derived_cache_state": upgraded["derived_cache_state"],
        "legacy_receipt": {
            "path": str(receipt_path.resolve()),
            "file_sha256": file_sha256(receipt_path),
            "receipt_root_sha256": receipt["receipt_root_sha256"],
        },
        "legacy_seal": {
            "path": str(seal_path.resolve()),
            "file_sha256": file_sha256(seal_path),
            "seal_root_sha256": seal["seal_root_sha256"],
        },
        "trial_request": {
            "path": str(request_path.resolve()),
            "file_sha256": file_sha256(request_path),
            "request_root_sha256": request["request_root_sha256"],
        },
        "cache_state_evidence": cache_state_evidence,
        "semantic_projection_root_sha256": upgraded[
            "semantic_projection_root_sha256"
        ],
        "stage_profile_root_sha256": stable_sha256(upgraded["stage_profile"]),
        "complete_trial_namespace_inventory": trial_inventory,
        "complete_semantic_diagnostic_inventory": semantic_inventory,
        "parent_observation": {
            "path": str(observation_path.resolve()),
            "file_sha256": file_sha256(observation_path),
            "observation_root_sha256": observation["observation_root_sha256"],
        },
        "independent_time_metrics": parsed_time,
    }
    return merged, binding


def _recompute_legacy_task9_rebind(
    output_root: Path,
    *,
    parent_inventory: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    output_root = Path(output_root).resolve(strict=True)
    inventory = (
        dict(parent_inventory)
        if parent_inventory is not None
        else inventory_tree(output_root)
    )
    if inventory.get("root") != str(output_root):
        raise Task9Rejected("task9_rebind_namespace_inventory_root_invalid")
    preliminary_path = output_root / PRELIMINARY_RECEIPT_NAME
    preliminary = _load_rooted_json(
        preliminary_path,
        root_field="receipt_root_sha256",
        code="task9_legacy_preliminary",
    )
    validate_preliminary_scope(preliminary)
    cache_binding = preliminary.get("derived_cold_cache_authority")
    if not isinstance(cache_binding, Mapping):
        raise Task9Rejected("task9_legacy_cache_binding_invalid")
    authority_path = _contained_path(
        Path(str(cache_binding.get("path") or "")),
        output_root,
        code="task9_legacy_cache_authority_escape",
    )
    authority = _verify_legacy_cache_authority_for_rebind(authority_path)
    if (
        cache_binding.get("file_sha256") != file_sha256(authority_path)
        or cache_binding.get("authority_root_sha256")
        != authority["authority_root_sha256"]
        or cache_binding.get("typed_cache_inventory_root_sha256")
        != authority["typed_cache"]["inventory_root_sha256"]
        or cache_binding.get("construction")
        != authority["derived_cold_construction"]
    ):
        raise Task9Rejected("task9_legacy_cache_binding_invalid")
    preliminary_trials = preliminary.get("trials")
    if not isinstance(preliminary_trials, list):
        raise Task9Rejected("task9_legacy_trial_bindings_invalid")
    expected_ids = ["C1", "C2", "W1", "W2", "W3"]
    if [row.get("trial_id") for row in preliminary_trials] != expected_ids:
        raise Task9Rejected("task9_legacy_trial_bindings_invalid")
    merged_trials: list[dict[str, Any]] = []
    trial_bindings: list[dict[str, Any]] = []
    reference_projection = {
        day: task8._day_projection(task7.TASK6_REFERENCE_EXECUTION_ROOT, day)
        for day in (task8.DAY1, task8.DAY2)
    }
    semantic_reference = _semantic_reference_binding()
    for trial_id, preliminary_binding in zip(
        expected_ids, preliminary_trials, strict=True
    ):
        merged, binding = _rebind_legacy_trial(
            trial_id=trial_id,
            output_root=output_root,
            parent_inventory=inventory,
            authority_path=authority_path,
            authority=authority,
            reference_projection=reference_projection,
        )
        if (
            preliminary_binding.get("derived_cache_state")
            != binding["derived_cache_state"]
            or preliminary_binding.get("receipt_file_sha256")
            != binding["legacy_receipt"]["file_sha256"]
            or preliminary_binding.get("receipt_root_sha256")
            != binding["legacy_receipt"]["receipt_root_sha256"]
            or preliminary_binding.get("semantic_projection_root_sha256")
            != binding["semantic_projection_root_sha256"]
            or preliminary_binding.get("observation_file_sha256")
            != binding["parent_observation"]["file_sha256"]
            or preliminary_binding.get("observation_root_sha256")
            != binding["parent_observation"]["observation_root_sha256"]
        ):
            raise Task9Rejected("task9_legacy_preliminary_trial_binding_invalid")
        merged_trials.append(merged)
        trial_bindings.append(binding)
    aggregate = aggregate_trials(merged_trials)
    return {
        "complete_namespace_inventory": inventory,
        "legacy_preliminary": {
            "path": str(preliminary_path.resolve()),
            "file_sha256": file_sha256(preliminary_path),
            "receipt_root_sha256": preliminary["receipt_root_sha256"],
        },
        "cache_authority": {
            "path": str(authority_path.resolve()),
            "file_sha256": file_sha256(authority_path),
            "authority_root_sha256": authority["authority_root_sha256"],
            "typed_cache_inventory_root_sha256": authority["typed_cache"][
                "inventory_root_sha256"
            ],
            "complete_input_inventory_root_sha256": authority[
                "input_inventory"
            ]["inventory_root_sha256"],
            "task8_tick_prewarm_authority": authority[
                "task8_tick_prewarm_authority"
            ],
        },
        "semantic_reference": semantic_reference,
        "trials": trial_bindings,
        "aggregate": aggregate,
        "targets": _task9_targets(merged_trials),
    }


def rebind_completed_task9_validation(
    output_root: Path,
    receipt_path: Path,
) -> Path:
    output_root = Path(output_root).resolve(strict=True)
    receipt_path = Path(receipt_path)
    if receipt_path.exists() or receipt_path.is_symlink():
        raise Task9Rejected("task9_review_rebind_receipt_must_be_new")
    initial_inventory = inventory_tree(output_root)
    recomputed = _recompute_legacy_task9_rebind(
        output_root,
        parent_inventory=initial_inventory,
    )
    _make_read_only(output_root)
    _assert_tree_read_only(
        output_root,
        code="task9_review_rebind_namespace_not_read_only",
    )
    final_inventory = inventory_tree(output_root)
    if final_inventory != initial_inventory:
        raise Task9Rejected("task9_review_rebind_namespace_changed_during_read")
    core = {
        "schema": REVIEW_REBIND_SCHEMA,
        "status": REVIEW_REBIND_STATUS,
        "controlling_task": "Replay-Acceleration Task 9",
        "source_namespace": str(output_root),
        **recomputed,
        "binding_policy": {
            "content_inventory_exclusions": [],
            "symlinks_allowed": False,
            "namespace_read_only": True,
            "legacy_v1_receipts_preserved_unmodified": True,
            "fresh_replay_required_for_envelope_repair": False,
        },
        "review_repairs": {
            "semantic_projection_recomputed": True,
            "cache_class_rederived_from_request_and_prime_evidence": True,
            "stage_profile_validated": True,
            "independent_time_evidence_parsed_and_reconciled": True,
            "complete_namespace_content_bound": True,
            "projection_kind": (
                "standardized_equal_cost_linear_s0r0_extrapolation_not_a_bound"
            ),
        },
        "implementation": {
            "path": str(Path(__file__).resolve()),
            "file_sha256": file_sha256(Path(__file__)),
        },
        "exact_semantic_parity_all_trials": True,
        "cache_rebuild_or_write_count": 0,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
        "real_order_transmission_possible": False,
        "economic_values_exposed": False,
        "review_required": True,
        "acceptance_authorized": False,
    }
    assert_outcome_blind(core)
    receipt = {**core, "receipt_root_sha256": stable_sha256(core)}
    atomic_write_json(receipt_path, receipt)
    verify_task9_review_rebind(receipt_path)
    return receipt_path


def verify_task9_review_rebind(receipt_path: Path) -> dict[str, Any]:
    payload = _load_rooted_json(
        receipt_path,
        root_field="receipt_root_sha256",
        code="task9_review_rebind",
    )
    if (
        payload.get("schema") != REVIEW_REBIND_SCHEMA
        or payload.get("status") != REVIEW_REBIND_STATUS
        or payload.get("broker_live_authority") is not False
        or payload.get("broker_mutation_enabled") is not False
        or payload.get("real_order_transmission_possible") is not False
        or payload.get("economic_values_exposed") is not False
        or payload.get("acceptance_authorized") is not False
    ):
        raise Task9Rejected("task9_review_rebind_scope_invalid")
    output_root = Path(str(payload.get("source_namespace") or ""))
    current_inventory = inventory_tree(output_root)
    if current_inventory != payload.get("complete_namespace_inventory"):
        raise Task9Rejected("task9_review_rebind_namespace_inventory_drift")
    _assert_tree_read_only(
        output_root,
        code="task9_review_rebind_namespace_not_read_only",
    )
    recomputed = _recompute_legacy_task9_rebind(
        output_root,
        parent_inventory=current_inventory,
    )
    for field in (
        "complete_namespace_inventory",
        "legacy_preliminary",
        "cache_authority",
        "semantic_reference",
        "trials",
        "aggregate",
        "targets",
    ):
        if recomputed[field] != payload.get(field):
            raise Task9Rejected(f"task9_review_rebind_{field}_drift")
    implementation = payload.get("implementation")
    if (
        not isinstance(implementation, Mapping)
        or implementation.get("path") != str(Path(__file__).resolve())
        or implementation.get("file_sha256") != file_sha256(Path(__file__))
    ):
        raise Task9Rejected("task9_review_rebind_implementation_drift")
    assert_outcome_blind(payload)
    return payload


def validate_preliminary_scope(preliminary: Mapping[str, Any]) -> dict[str, Any]:
    assert_outcome_blind(preliminary)
    expected_scope = {
        "start_day": task8.DAY1,
        "end_day": task8.DAY2,
        "no_event_day": task8.DAY1,
        "dense_day": task8.DAY2,
        "arm_id": "S0R0",
    }
    if (
        preliminary.get("schema") != PRELIMINARY_SCHEMA
        or preliminary.get("status") != PRELIMINARY_STATUS
        or preliminary.get("controlling_task")
        != "Replay-Acceleration Task 9"
        or preliminary.get("scope") != expected_scope
        or preliminary.get("exact_semantic_parity_all_trials") is not True
        or not _nonnegative_integer(
            preliminary.get("cache_rebuild_or_write_count")
        )
        or preliminary.get("cache_rebuild_or_write_count") != 0
        or preliminary.get("broker_live_authority") is not False
        or preliminary.get("broker_mutation_enabled") is not False
        or preliminary.get("real_order_transmission_possible") is not False
        or preliminary.get("economic_values_exposed") is not False
        or preliminary.get("review_required") is not True
        or preliminary.get("acceptance_authorized") is not False
    ):
        raise Task9Rejected("task9_preliminary_scope_invalid")
    bindings = preliminary.get("trials")
    expected = [
        ("C1", COLD_PROCESS_STATE),
        ("C2", COLD_PROCESS_STATE),
        ("W1", WARM_FILESYSTEM_STATE),
        ("W2", WARM_FILESYSTEM_STATE),
        ("W3", WARM_FILESYSTEM_STATE),
    ]
    if (
        not isinstance(bindings, list)
        or len(bindings) != len(expected)
        or any(not isinstance(row, Mapping) for row in bindings)
        or [
            (row.get("trial_id"), row.get("derived_cache_state"))
            for row in bindings
        ]
        != expected
    ):
        raise Task9Rejected("task9_preliminary_trial_class_invalid")
    return dict(preliminary)


def _verify_v2_preliminary(
    output_root: Path,
    preliminary: Mapping[str, Any],
) -> dict[str, Any]:
    validate_preliminary_scope(preliminary)
    bindings = preliminary.get("trials")
    if not isinstance(bindings, list):
        raise Task9Rejected("task9_v2_preliminary_trial_bindings_invalid")
    cache_binding = preliminary.get("derived_cold_cache_authority")
    if not isinstance(cache_binding, Mapping):
        raise Task9Rejected("task9_v2_cache_binding_invalid")
    authority_path = _contained_path(
        Path(str(cache_binding.get("path") or "")),
        Path(output_root) / "cache-authority",
        code="task9_v2_cache_authority_escape",
    )
    if authority_path.name != "TASK9_TYPED_CACHE_AUTHORITY.json":
        raise Task9Rejected("task9_v2_cache_binding_invalid")
    authority = verify_cache_authority(
        authority_path,
        expected_file_sha256=str(cache_binding.get("file_sha256") or ""),
    )
    if (
        cache_binding.get("authority_root_sha256")
        != authority["authority_root_sha256"]
        or cache_binding.get("typed_cache_inventory_root_sha256")
        != authority["typed_cache"]["inventory_root_sha256"]
        or cache_binding.get("construction")
        != authority["derived_cold_construction"]
    ):
        raise Task9Rejected("task9_v2_cache_binding_invalid")
    merged_trials: list[dict[str, Any]] = []
    for binding in bindings:
        trial_id = str(binding["trial_id"])
        receipt_path = _contained_path(
            Path(str(binding.get("receipt_path") or "")),
            Path(output_root) / "trials" / trial_id,
            code="task9_v2_trial_receipt_escape",
        )
        if receipt_path.name != TRIAL_RECEIPT_NAME:
            raise Task9Rejected("task9_v2_trial_receipt_identity_invalid")
        trial = load_sealed_trial(receipt_path)
        observation_path = _contained_path(
            Path(str(binding.get("observation_path") or "")),
            Path(output_root) / "observations",
            code="task9_v2_observation_escape",
        )
        if observation_path.name != f"{trial_id}.json":
            raise Task9Rejected("task9_v2_observation_identity_invalid")
        observation = _load_observation(observation_path, trial=trial)
        cache_evidence = trial["cache_state_evidence"]
        if (
            binding.get("derived_cache_state")
            != trial["derived_cache_state"]
            or cache_evidence["cache_authority_root_sha256"]
            != authority["authority_root_sha256"]
            or cache_evidence["cache_authority_file_sha256"]
            != file_sha256(authority_path)
            or cache_evidence["complete_input_inventory_root_sha256"]
            != authority["input_inventory"]["inventory_root_sha256"]
            or trial["cache"]["inventory_root_sha256"]
            != authority["typed_cache"]["inventory_root_sha256"]
            or binding.get("receipt_file_sha256") != file_sha256(receipt_path)
            or binding.get("receipt_root_sha256")
            != trial["receipt_root_sha256"]
            or binding.get("semantic_projection_root_sha256")
            != trial["semantic_projection_root_sha256"]
            or binding.get("stage_profile_root_sha256")
            != stable_sha256(trial["stage_profile"])
            or binding.get("observation_file_sha256")
            != file_sha256(observation_path)
            or binding.get("observation_root_sha256")
            != observation["observation_root_sha256"]
        ):
            raise Task9Rejected("task9_v2_preliminary_trial_binding_invalid")
        merged_trials.append(_merge_parent_observation(trial, observation))
    aggregate = aggregate_trials(merged_trials)
    targets = _task9_targets(merged_trials)
    if (
        aggregate != preliminary.get("aggregate")
        or targets != preliminary.get("targets")
        or aggregate.get("cache_inventory_root_sha256")
        != authority["typed_cache"]["inventory_root_sha256"]
    ):
        raise Task9Rejected("task9_v2_preliminary_aggregate_drift")
    return {"aggregate": aggregate, "targets": targets}


def finalize_task9_v2_namespace(
    output_root: Path,
    preliminary_path: Path,
) -> Path:
    output_root = Path(output_root).resolve(strict=True)
    preliminary_path = _contained_path(
        preliminary_path,
        output_root,
        code="task9_v2_preliminary_path_escape",
    )
    if preliminary_path.name != PRELIMINARY_RECEIPT_NAME:
        raise Task9Rejected("task9_v2_preliminary_identity_invalid")
    final_path = output_root.with_name(
        output_root.name + FINAL_VALIDATION_RECEIPT_SUFFIX
    )
    if final_path.exists() or final_path.is_symlink():
        raise Task9Rejected("task9_v2_final_receipt_must_be_new")
    preliminary = _load_rooted_json(
        preliminary_path,
        root_field="receipt_root_sha256",
        code="task9_v2_preliminary",
    )
    verified = _verify_v2_preliminary(output_root, preliminary)
    namespace_inventory = inventory_tree(output_root)
    semantic_reference = _semantic_reference_binding()
    _make_read_only(output_root)
    _assert_tree_read_only(
        output_root,
        code="task9_v2_namespace_not_read_only",
    )
    if inventory_tree(output_root) != namespace_inventory:
        raise Task9Rejected("task9_v2_namespace_changed_during_seal")
    core = {
        "schema": FINAL_VALIDATION_SCHEMA,
        "status": FINAL_VALIDATION_STATUS,
        "controlling_task": "Replay-Acceleration Task 9",
        "source_namespace": str(output_root),
        "complete_namespace_inventory": namespace_inventory,
        "content_inventory_exclusions": [],
        "namespace_read_only": True,
        "preliminary": {
            "path": str(preliminary_path),
            "file_sha256": file_sha256(preliminary_path),
            "receipt_root_sha256": preliminary["receipt_root_sha256"],
        },
        "semantic_reference": semantic_reference,
        "aggregate": verified["aggregate"],
        "targets": verified["targets"],
        "implementation": {
            "path": str(Path(__file__).resolve()),
            "file_sha256": file_sha256(Path(__file__)),
        },
        "exact_semantic_parity_all_trials": True,
        "cache_rebuild_or_write_count": 0,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
        "real_order_transmission_possible": False,
        "economic_values_exposed": False,
        "review_required": True,
        "acceptance_authorized": False,
    }
    assert_outcome_blind(core)
    receipt = {**core, "receipt_root_sha256": stable_sha256(core)}
    atomic_write_json(final_path, receipt)
    verify_task9_v2_final_receipt(final_path)
    return final_path


def verify_task9_v2_final_receipt(receipt_path: Path) -> dict[str, Any]:
    receipt_path = Path(receipt_path).resolve(strict=True)
    payload = _load_rooted_json(
        receipt_path,
        root_field="receipt_root_sha256",
        code="task9_v2_final",
    )
    if (
        payload.get("schema") != FINAL_VALIDATION_SCHEMA
        or payload.get("status") != FINAL_VALIDATION_STATUS
        or payload.get("content_inventory_exclusions") != []
        or payload.get("namespace_read_only") is not True
        or payload.get("broker_live_authority") is not False
        or payload.get("broker_mutation_enabled") is not False
        or payload.get("real_order_transmission_possible") is not False
        or payload.get("economic_values_exposed") is not False
        or payload.get("acceptance_authorized") is not False
    ):
        raise Task9Rejected("task9_v2_final_scope_invalid")
    output_root = Path(str(payload.get("source_namespace") or "")).resolve(
        strict=True
    )
    expected_receipt_path = output_root.with_name(
        output_root.name + FINAL_VALIDATION_RECEIPT_SUFFIX
    )
    if receipt_path != expected_receipt_path:
        raise Task9Rejected("task9_v2_final_receipt_identity_invalid")
    current_inventory = inventory_tree(output_root)
    if current_inventory != payload.get("complete_namespace_inventory"):
        raise Task9Rejected("task9_v2_final_namespace_inventory_drift")
    _assert_tree_read_only(
        output_root,
        code="task9_v2_namespace_not_read_only",
    )
    preliminary_binding = payload.get("preliminary")
    if not isinstance(preliminary_binding, Mapping):
        raise Task9Rejected("task9_v2_final_preliminary_binding_invalid")
    preliminary_path = _contained_path(
        Path(str(preliminary_binding.get("path") or "")),
        output_root,
        code="task9_v2_preliminary_path_escape",
    )
    preliminary = _load_rooted_json(
        preliminary_path,
        root_field="receipt_root_sha256",
        code="task9_v2_preliminary",
        expected_file_sha256=str(preliminary_binding.get("file_sha256") or ""),
    )
    if preliminary_binding.get("receipt_root_sha256") != preliminary.get(
        "receipt_root_sha256"
    ):
        raise Task9Rejected("task9_v2_final_preliminary_binding_invalid")
    verified = _verify_v2_preliminary(output_root, preliminary)
    if (
        verified["aggregate"] != payload.get("aggregate")
        or verified["targets"] != payload.get("targets")
        or _semantic_reference_binding() != payload.get("semantic_reference")
    ):
        raise Task9Rejected("task9_v2_final_recomputation_drift")
    implementation = payload.get("implementation")
    if (
        not isinstance(implementation, Mapping)
        or implementation.get("path") != str(Path(__file__).resolve())
        or implementation.get("file_sha256") != file_sha256(Path(__file__))
    ):
        raise Task9Rejected("task9_v2_final_implementation_drift")
    assert_outcome_blind(payload)
    return payload


def run_task9_final_validation(output_root: Path) -> Path:
    output_root = Path(output_root)
    if output_root.exists() or output_root.is_symlink():
        raise Task9Rejected("task9_output_root_must_be_new")
    final_receipt_path = output_root.with_name(
        output_root.name + FINAL_VALIDATION_RECEIPT_SUFFIX
    )
    if final_receipt_path.exists() or final_receipt_path.is_symlink():
        raise Task9Rejected("task9_v2_final_receipt_must_be_new")
    output_root.mkdir(parents=True)
    (output_root / "requests").mkdir()
    (output_root / "logs").mkdir()
    (output_root / "trials").mkdir()
    cache_authority_path = build_typed_cache_authority(output_root)
    cache_authority = verify_cache_authority(cache_authority_path)
    trial_paths: list[Path] = []
    observation_paths: list[Path] = []
    trial_specs = (
        ("C1", COLD_PROCESS_STATE),
        ("C2", COLD_PROCESS_STATE),
        ("W1", WARM_FILESYSTEM_STATE),
        ("W2", WARM_FILESYSTEM_STATE),
        ("W3", WARM_FILESYSTEM_STATE),
    )
    for trial_id, expected_state in trial_specs:
        priming_receipt_path = None
        if expected_state == WARM_FILESYSTEM_STATE:
            prime_nonce = uuid.uuid4().hex
            prime_request = make_priming_request(
                path=output_root / "requests" / f"{trial_id}.prime.request.json",
                cache_authority_path=cache_authority_path,
                launch_nonce=prime_nonce,
            )
            priming_receipt_path = _run_priming_subprocess(
                request_path=prime_request,
                launch_nonce=prime_nonce,
                log_root=output_root / "logs",
                label=trial_id,
            )
        trial_nonce = uuid.uuid4().hex
        request_path = make_trial_request(
            path=output_root / "requests" / f"{trial_id}.trial.request.json",
            trial_id=trial_id,
            output_dir=output_root / "trials" / trial_id,
            cache_authority_path=cache_authority_path,
            launch_nonce=trial_nonce,
            priming_receipt_path=priming_receipt_path,
        )
        receipt_path, observation_path = _run_trial_subprocess(
            request_path=request_path,
            launch_nonce=trial_nonce,
            output_root=output_root,
            trial_id=trial_id,
        )
        trial = load_sealed_trial(receipt_path)
        if trial["derived_cache_state"] != expected_state:
            raise Task9Rejected("task9_trial_derived_cache_state_mismatch")
        trial_paths.append(receipt_path)
        observation_paths.append(observation_path)
    merged_trials = []
    for receipt_path, observation_path in zip(
        trial_paths, observation_paths, strict=True
    ):
        trial = load_sealed_trial(receipt_path)
        observation = _load_observation(observation_path, trial=trial)
        merged_trials.append(_merge_parent_observation(trial, observation))
    aggregate = aggregate_trials(merged_trials)
    trial_bindings = []
    for receipt_path, observation_path, trial in zip(
        trial_paths, observation_paths, merged_trials, strict=True
    ):
        observation = _load_observation(observation_path, trial=trial)
        trial_bindings.append(
            {
                "trial_id": trial["trial_id"],
                "derived_cache_state": trial["derived_cache_state"],
                "receipt_path": str(receipt_path.resolve()),
                "receipt_file_sha256": file_sha256(receipt_path),
                "receipt_root_sha256": trial["receipt_root_sha256"],
                "semantic_projection_root_sha256": trial[
                    "semantic_projection_root_sha256"
                ],
                "stage_profile_root_sha256": stable_sha256(
                    trial["stage_profile"]
                ),
                "observation_path": str(observation_path.resolve()),
                "observation_file_sha256": file_sha256(observation_path),
                "observation_root_sha256": observation[
                    "observation_root_sha256"
                ],
            }
        )
    output_tree = slice_metrics._tree_usage(output_root)
    core = {
        "schema": PRELIMINARY_SCHEMA,
        "status": PRELIMINARY_STATUS,
        "controlling_task": "Replay-Acceleration Task 9",
        "scope": {
            "start_day": task8.DAY1,
            "end_day": task8.DAY2,
            "no_event_day": task8.DAY1,
            "dense_day": task8.DAY2,
            "arm_id": "S0R0",
        },
        "derived_cold_cache_authority": {
            "path": str(cache_authority_path.resolve()),
            "file_sha256": file_sha256(cache_authority_path),
            "authority_root_sha256": cache_authority[
                "authority_root_sha256"
            ],
            "typed_cache_inventory_root_sha256": cache_authority[
                "typed_cache"
            ]["inventory_root_sha256"],
            "construction": cache_authority["derived_cold_construction"],
        },
        "trials": trial_bindings,
        "aggregate": aggregate,
        "targets": _task9_targets(merged_trials),
        "output_tree_before_preliminary_receipt": output_tree,
        "exact_semantic_parity_all_trials": True,
        "cache_rebuild_or_write_count": 0,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
        "real_order_transmission_possible": False,
        "economic_values_exposed": False,
        "review_required": True,
        "acceptance_authorized": False,
    }
    assert_outcome_blind(core)
    receipt = {**core, "receipt_root_sha256": stable_sha256(core)}
    receipt_path = output_root / PRELIMINARY_RECEIPT_NAME
    atomic_write_json(receipt_path, receipt)
    return finalize_task9_v2_namespace(output_root, receipt_path)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build-cache")
    build.add_argument("--output-root", type=Path, required=True)
    prime = subparsers.add_parser("prime")
    prime.add_argument("--request", type=Path, required=True)
    trial = subparsers.add_parser("trial")
    trial.add_argument("--request", type=Path, required=True)
    orchestrate = subparsers.add_parser("orchestrate")
    orchestrate.add_argument("--output-root", type=Path, required=True)
    rebind = subparsers.add_parser("rebind-completed")
    rebind.add_argument("--output-root", type=Path, required=True)
    rebind.add_argument("--receipt", type=Path, required=True)
    verify_rebind = subparsers.add_parser("verify-rebind")
    verify_rebind.add_argument("--receipt", type=Path, required=True)
    verify_final = subparsers.add_parser("verify-final")
    verify_final.add_argument("--receipt", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "build-cache":
        receipt_path = build_typed_cache_authority(args.output_root)
    elif args.command == "prime":
        receipt_path = execute_priming_request(args.request)
    elif args.command == "trial":
        receipt_path = execute_trial_request(args.request)
    elif args.command == "rebind-completed":
        receipt_path = rebind_completed_task9_validation(
            args.output_root,
            args.receipt,
        )
    elif args.command == "verify-rebind":
        verify_task9_review_rebind(args.receipt)
        receipt_path = args.receipt
    elif args.command == "verify-final":
        verify_task9_v2_final_receipt(args.receipt)
        receipt_path = args.receipt
    else:
        receipt_path = run_task9_final_validation(args.output_root)
    print(
        json.dumps(
            {
                "status": "complete",
                "receipt": str(Path(receipt_path).resolve()),
                "receipt_file_sha256": file_sha256(receipt_path),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
