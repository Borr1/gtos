"""Immutable normalized-partition cache over an accepted source bundle.

The writer binds every normalized logical partition to exact source, config,
schema, and code identities.  It never enters candidate or policy execution.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from src.research_infra import v4_timewarp_simulated_live_research_loop as legacy
from src.research_infra.replay_acceleration_slice import (
    HARD_FLOOR_FREE_BYTES,
    MAX_SCRATCH_BYTES,
    WARNING_FREE_BYTES,
    SliceRejected,
    _StageMeasurements,
    _aggregate_h1,
    _atomic_write,
    _load_canonical_json,
    _resource_delta,
    _resource_snapshot,
    _rows_root,
    _swap_used_bytes,
    _tree_usage,
    _verify_self_root,
    _with_self_root,
    _write_canonical_json,
    canonical_json_bytes,
    file_sha256,
    sha256_bytes,
    verify_selection_receipt,
)


NORMALIZED_BUNDLE_SCHEMA = "gtos.replay_acceleration.normalized_bundle.v1"
NORMALIZED_MANIFEST_SCHEMA = "gtos.replay_acceleration.normalized_manifest.v1"
NORMALIZED_RUN_SCHEMA = "gtos.replay_acceleration.normalized_run.v1"
NORMALIZED_CASE_SCHEMA = "gtos.replay_acceleration.normalized_failure_case.v1"
NORMALIZED_INJECTION_SCHEMA = "gtos.replay_acceleration.normalized_injections.v1"
NORMALIZED_VERIFIER_ENVELOPE_SCHEMA = (
    "gtos.replay_acceleration.normalized_verifier_envelope.v1"
)
NORMALIZED_RESULT_SCHEMA = "gtos.replay_acceleration.normalized_result.v1"
NORMALIZED_ROW_SCHEMA = "gtos.replay_acceleration.normalized_rows_jsonl.v1"
SOURCE_BUNDLE_SCHEMA = "gtos.replay_acceleration.persisted_source_bundle.v1"
SOURCE_STAGE_LABEL = "bounded_all_symbol_normalization_stage_not_whole_replay"
EMPTY_CONFIG_ROOT = sha256_bytes(canonical_json_bytes({}))
VERIFIER_PATH = Path(__file__).with_name(
    "replay_acceleration_normalized_verifier.py"
)
SOURCE_VERIFIER_PATH = Path(__file__).with_name(
    "replay_acceleration_slice_verifier.py"
)
LOGICAL_ORDER = {"D1": 0, "H4": 1, "H1": 2, "M15": 3, "M1": 4}
MANIFEST_FIELDS = {
    "schema",
    "identity",
    "identity_root_sha256",
    "payload_root_sha256",
    "payload_byte_count",
    "row_count",
    "normalized_rows_root_sha256",
    "manifest_root_sha256",
}


class NormalizedRejected(SliceRejected):
    """Stable fail-closed normalized-cache rejection."""


def _payload_bytes(rows: Iterable[Mapping[str, Any]]) -> bytes:
    try:
        return b"".join(canonical_json_bytes(dict(row)) + b"\n" for row in rows)
    except SliceRejected as exc:
        raise NormalizedRejected("normalized_payload_noncanonical") from exc


def _normalized_rows_root(payload: bytes) -> str:
    return sha256_bytes(b"gtos.replay_acceleration.normalized_rows.v1\n" + payload)


def _load_payload(path: Path) -> tuple[tuple[dict[str, Any], ...], bytes]:
    try:
        raw = Path(path).read_bytes()
    except OSError:
        raise NormalizedRejected("normalized_payload_missing") from None
    if raw and not raw.endswith(b"\n"):
        raise NormalizedRejected("normalized_payload_not_canonical")
    rows: list[dict[str, Any]] = []
    for line in raw.splitlines(keepends=True):
        if line == b"\n" or not line.endswith(b"\n"):
            raise NormalizedRejected("normalized_payload_not_canonical")
        try:
            value = json.loads(line)
        except (UnicodeError, json.JSONDecodeError):
            raise NormalizedRejected("normalized_payload_not_canonical") from None
        if type(value) is not dict or line != canonical_json_bytes(value) + b"\n":
            raise NormalizedRejected("normalized_payload_not_canonical")
        rows.append(value)
    return tuple(rows), raw


def _load_source_bundle(
    *, source_bundle_dir: Path, selection_path: Path
) -> tuple[dict[str, Any], dict[str, Any], str]:
    selection = verify_selection_receipt(selection_path)
    source = _load_canonical_json(
        Path(source_bundle_dir) / "bundle.json", code="normalized_source_bundle_invalid"
    )
    if source.get("schema") != SOURCE_BUNDLE_SCHEMA:
        raise NormalizedRejected("normalized_source_bundle_invalid")
    source_root = _verify_self_root(
        source, "bundle_root_sha256", code="normalized_source_bundle_invalid"
    )
    try:
        marker = (Path(source_bundle_dir) / "SEALED").read_bytes()
    except OSError:
        raise NormalizedRejected("normalized_source_bundle_unsealed") from None
    if marker != source_root.encode("ascii") + b"\n":
        raise NormalizedRejected("normalized_source_bundle_unsealed")
    if source.get("selection_root_sha256") != selection.get(
        "selection_root_sha256"
    ):
        raise NormalizedRejected("normalized_source_identity_mismatch")
    return selection, source, source_root


def _code_identity() -> dict[str, Any]:
    writer_root = file_sha256(Path(__file__))
    legacy_root = file_sha256(Path(legacy.__file__))
    verifier_root = file_sha256(VERIFIER_PATH)
    core = {
        "writer_file_sha256": writer_root,
        "legacy_normalizer_file_sha256": legacy_root,
        "independent_verifier_file_sha256": verifier_root,
        "normalized_row_schema": NORMALIZED_ROW_SCHEMA,
    }
    return {
        **core,
        "normalization_code_identity_root_sha256": sha256_bytes(
            canonical_json_bytes(core)
        ),
    }


def _cache_identity(
    *, source_root: str, selection_root: str, code_identity: Mapping[str, Any]
) -> str:
    return sha256_bytes(
        canonical_json_bytes(
            {
                "source_bundle_root_sha256": source_root,
                "selection_root_sha256": selection_root,
                "legacy_normalizer_file_sha256": code_identity[
                    "legacy_normalizer_file_sha256"
                ],
                "writer_file_sha256": code_identity["writer_file_sha256"],
                "normalized_row_schema": NORMALIZED_ROW_SCHEMA,
                "config_projection_root_sha256": EMPTY_CONFIG_ROOT,
            }
        )
    )


def _identity(
    *,
    logical: Mapping[str, Any],
    physical: Mapping[str, Any],
    source_root: str,
    selection_root: str,
    code_identity: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema": "gtos.replay_acceleration.normalized_identity.v1",
        "source_bundle_root_sha256": source_root,
        "selection_root_sha256": selection_root,
        "partition_id": f"{logical['symbol']}:{logical['timeframe']}",
        "symbol": logical["symbol"],
        "timeframe": logical["timeframe"],
        "physical_partition_id": logical["physical_partition_id"],
        "transform": logical["transform"],
        "source_payload_root_sha256": physical["payload_root"],
        "source_logical_rows_root_sha256": logical["normalized_root_sha256"],
        "source_logical_row_count": logical["normalized_record_count"],
        "config_projection_keys": [],
        "config_projection_root_sha256": EMPTY_CONFIG_ROOT,
        "normalized_row_schema": NORMALIZED_ROW_SCHEMA,
        "legacy_normalizer_file_sha256": code_identity[
            "legacy_normalizer_file_sha256"
        ],
        "writer_file_sha256": code_identity["writer_file_sha256"],
    }


def _manifest(
    *, identity: Mapping[str, Any], payload: bytes, row_count: int
) -> dict[str, Any]:
    core = {
        "schema": NORMALIZED_MANIFEST_SCHEMA,
        "identity": dict(identity),
        "identity_root_sha256": sha256_bytes(canonical_json_bytes(identity)),
        "payload_root_sha256": sha256_bytes(payload),
        "payload_byte_count": len(payload),
        "row_count": int(row_count),
        "normalized_rows_root_sha256": _normalized_rows_root(payload),
    }
    return _with_self_root(core, "manifest_root_sha256")


def _validate_manifest(
    *, manifest: Mapping[str, Any], identity: Mapping[str, Any], payload: bytes
) -> None:
    if (
        set(manifest) != MANIFEST_FIELDS
        or manifest.get("schema") != NORMALIZED_MANIFEST_SCHEMA
    ):
        raise NormalizedRejected("normalized_manifest_schema_mismatch")
    _verify_self_root(
        manifest,
        "manifest_root_sha256",
        code="normalized_manifest_identity_mismatch",
    )
    if manifest.get("identity") != identity:
        raise NormalizedRejected("normalized_cache_identity_mismatch")
    if manifest.get("identity_root_sha256") != sha256_bytes(
        canonical_json_bytes(identity)
    ):
        raise NormalizedRejected("normalized_cache_identity_mismatch")
    rows, raw = _load_payload_bytes(payload)
    if (
        manifest.get("payload_root_sha256") != sha256_bytes(raw)
        or manifest.get("payload_byte_count") != len(raw)
        or manifest.get("row_count") != len(rows)
        or manifest.get("normalized_rows_root_sha256")
        != _normalized_rows_root(raw)
    ):
        raise NormalizedRejected("normalized_payload_identity_mismatch")


def _load_payload_bytes(
    payload: bytes,
) -> tuple[tuple[dict[str, Any], ...], bytes]:
    if payload and not payload.endswith(b"\n"):
        raise NormalizedRejected("normalized_payload_not_canonical")
    rows: list[dict[str, Any]] = []
    for line in payload.splitlines(keepends=True):
        if not line.endswith(b"\n"):
            raise NormalizedRejected("normalized_payload_not_canonical")
        try:
            value = json.loads(line)
        except (UnicodeError, json.JSONDecodeError):
            raise NormalizedRejected("normalized_payload_not_canonical") from None
        if type(value) is not dict or line != canonical_json_bytes(value) + b"\n":
            raise NormalizedRejected("normalized_payload_not_canonical")
        rows.append(value)
    return tuple(rows), payload


def _source_verification(
    *, source_bundle_dir: Path, selection_path: Path
) -> tuple[dict[str, Any], list[str]]:
    command = [
        sys.executable,
        str(SOURCE_VERIFIER_PATH.resolve()),
        "verify",
        "--bundle-dir",
        str(Path(source_bundle_dir).resolve()),
        "--selection",
        str(Path(selection_path).resolve()),
    ]
    completed = subprocess.run(
        command,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=600,
    )
    try:
        receipt = json.loads(completed.stdout)
    except json.JSONDecodeError:
        raise NormalizedRejected("normalized_source_verification_failed") from None
    if completed.returncode != 0 or receipt.get("status") != "VERIFIED":
        raise NormalizedRejected("normalized_source_verification_failed")
    return receipt, command


def _logical_rows(
    *,
    source_bundle_dir: Path,
    logical: Mapping[str, Any],
    physical: Mapping[str, Any],
) -> tuple[dict[str, Any], ...]:
    path = Path(source_bundle_dir) / str(physical["legacy_path"])
    rows = legacy.load_csv_rows(path, symbol=str(logical["symbol"]))
    if logical.get("transform") == "derived_h1_from_m15":
        rows = _aggregate_h1(rows, symbol=str(logical["symbol"]))
    elif logical.get("transform") != "direct_csv_normalization":
        raise NormalizedRejected("normalized_transform_invalid")
    if _rows_root(rows) != logical.get("normalized_root_sha256"):
        raise NormalizedRejected("normalized_legacy_source_root_mismatch")
    if len(rows) != logical.get("normalized_record_count"):
        raise NormalizedRejected("normalized_legacy_source_count_mismatch")
    return rows


def _capacity(
    *, workspace: Path, baseline_free: int, baseline_allocated: int
) -> dict[str, int]:
    usage = _tree_usage(workspace)
    growth = max(0, usage["allocated_bytes"] - baseline_allocated)
    free = shutil.disk_usage(workspace).free
    if growth > MAX_SCRATCH_BYTES:
        raise NormalizedRejected("normalized_scratch_quota_exceeded")
    if free < HARD_FLOOR_FREE_BYTES:
        raise NormalizedRejected("normalized_disk_hard_floor_reached")
    if baseline_free - free > MAX_SCRATCH_BYTES:
        raise NormalizedRejected("normalized_workspace_growth_quota_exceeded")
    return {"free_bytes": int(free), "allocated_growth_bytes": int(growth)}


def materialize_normalized_bundle(
    *,
    source_bundle_dir: Path,
    selection_path: Path,
    workspace: Path,
    run_label: str,
    expected_mode: str,
    command_argv: Sequence[str] | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    resource_started = _resource_snapshot()
    if expected_mode not in {"cold", "warm"}:
        raise NormalizedRejected("normalized_mode_invalid")
    selection, source, source_root = _load_source_bundle(
        source_bundle_dir=Path(source_bundle_dir),
        selection_path=Path(selection_path),
    )
    root = Path(workspace)
    root.mkdir(parents=True, exist_ok=True)
    bundle_dir = root / "bundle"
    seal_exists = (bundle_dir / "SEALED").exists()
    if expected_mode == "cold" and seal_exists:
        raise NormalizedRejected("normalized_cold_workspace_not_empty")
    if expected_mode == "warm" and not seal_exists:
        raise NormalizedRejected("normalized_warm_bundle_missing")
    baseline_free = shutil.disk_usage(root).free
    baseline_usage = _tree_usage(root)
    source_bytes = sum(
        int(row.get("byte_count") or 0)
        for row in source.get("physical_partitions") or ()
    )
    projected = source_bytes * 6 + 64 * 1024 * 1024
    if projected > MAX_SCRATCH_BYTES:
        raise NormalizedRejected("normalized_projected_scratch_quota_exceeded")
    if baseline_free - projected < HARD_FLOOR_FREE_BYTES:
        raise NormalizedRejected("normalized_projected_disk_floor_threat")
    swap_before = _swap_used_bytes()
    measurements = _StageMeasurements(root)
    with measurements.stage("source_bundle_independent_revalidation"):
        source_verification, source_verification_command = _source_verification(
            source_bundle_dir=Path(source_bundle_dir),
            selection_path=Path(selection_path),
        )
    if source_verification.get("bundle_root_sha256") != source_root:
        raise NormalizedRejected("normalized_source_verification_mismatch")
    code_identity = _code_identity()
    selection_root = str(selection["selection_root_sha256"])
    global_cache_identity = _cache_identity(
        source_root=source_root,
        selection_root=selection_root,
        code_identity=code_identity,
    )
    physical_by_id = {
        str(row["partition_id"]): row for row in source["physical_partitions"]
    }
    logical_plan = sorted(
        source["logical_partitions"],
        key=lambda row: (
            str(row["symbol"]),
            LOGICAL_ORDER.get(str(row["timeframe"]), 99),
        ),
    )
    entries: list[dict[str, Any]] = []
    hits = 0
    misses = 0
    total_rows = 0
    total_payload_bytes = 0
    for index, logical in enumerate(logical_plan):
        physical = physical_by_id.get(str(logical["physical_partition_id"]))
        if physical is None:
            raise NormalizedRejected("normalized_physical_partition_missing")
        identity = _identity(
            logical=logical,
            physical=physical,
            source_root=source_root,
            selection_root=selection_root,
            code_identity=code_identity,
        )
        identity_root = sha256_bytes(canonical_json_bytes(identity))
        relative_root = Path("cache") / identity_root
        payload_path = bundle_dir / relative_root / "rows.jsonl"
        manifest_path = bundle_dir / relative_root / "manifest.json"
        exists = payload_path.exists() or manifest_path.exists()
        if expected_mode == "cold":
            if exists:
                raise NormalizedRejected("normalized_cold_cache_not_empty")
            with measurements.stage("legacy_normalize_and_serialize"):
                rows = _logical_rows(
                    source_bundle_dir=Path(source_bundle_dir),
                    logical=logical,
                    physical=physical,
                )
                payload = _payload_bytes(rows)
                manifest = _manifest(
                    identity=identity, payload=payload, row_count=len(rows)
                )
            with measurements.stage("normalized_payload_persist"):
                _atomic_write(payload_path, payload, mode=0o444)
                _write_canonical_json(manifest_path, manifest, mode=0o444)
            misses += 1
        else:
            if not payload_path.exists() or not manifest_path.exists():
                raise NormalizedRejected("normalized_warm_cache_missing")
            with measurements.stage("normalized_cache_revalidation"):
                manifest = _load_canonical_json(
                    manifest_path, code="normalized_manifest_not_canonical"
                )
                payload = payload_path.read_bytes()
                _validate_manifest(
                    manifest=manifest, identity=identity, payload=payload
                )
                rows, _raw = _load_payload_bytes(payload)
            hits += 1
        entry = {
            "index": index,
            "partition_id": identity["partition_id"],
            "symbol": identity["symbol"],
            "timeframe": identity["timeframe"],
            "physical_partition_id": identity["physical_partition_id"],
            "transform": identity["transform"],
            "identity": identity,
            "identity_root_sha256": identity_root,
            "source_logical_rows_root_sha256": identity[
                "source_logical_rows_root_sha256"
            ],
            "source_selected_day_row_count": logical[
                "selected_day_record_count"
            ],
            "payload_path": str(relative_root / "rows.jsonl"),
            "manifest_path": str(relative_root / "manifest.json"),
            "payload_root_sha256": manifest["payload_root_sha256"],
            "payload_byte_count": manifest["payload_byte_count"],
            "row_count": manifest["row_count"],
            "normalized_rows_root_sha256": manifest[
                "normalized_rows_root_sha256"
            ],
            "manifest_root_sha256": manifest["manifest_root_sha256"],
        }
        entries.append(entry)
        total_rows += int(entry["row_count"])
        total_payload_bytes += int(entry["payload_byte_count"])
        _capacity(
            workspace=root,
            baseline_free=baseline_free,
            baseline_allocated=baseline_usage["allocated_bytes"],
        )

    symbols = sorted({str(row["symbol"]) for row in entries})
    barrier = {
        "sealed": True,
        "policy_execution_entered": False,
        "symbol_count": len(symbols),
        "symbols": symbols,
        "logical_partition_count": len(entries),
    }
    bundle_core = {
        "schema": NORMALIZED_BUNDLE_SCHEMA,
        "status": "SEALED_NORMALIZED_EQUIVALENCE_BUNDLE",
        "source_bundle_root_sha256": source_root,
        "selection_root_sha256": selection_root,
        "selected_day": selection["selected_day"],
        "normalized_row_schema": NORMALIZED_ROW_SCHEMA,
        "legacy_normalizer_file_sha256": code_identity[
            "legacy_normalizer_file_sha256"
        ],
        "writer_file_sha256": code_identity["writer_file_sha256"],
        "independent_verifier_file_sha256": code_identity[
            "independent_verifier_file_sha256"
        ],
        "normalization_code_identity_root_sha256": code_identity[
            "normalization_code_identity_root_sha256"
        ],
        "config_projection_keys": [],
        "config_projection_root_sha256": EMPTY_CONFIG_ROOT,
        "cache_identity_root_sha256": global_cache_identity,
        "logical_partitions": entries,
        "cross_symbol_barrier": barrier,
        "policy_execution_entered": False,
    }
    normalized_bundle = _with_self_root(
        bundle_core, "normalized_bundle_root_sha256"
    )
    with measurements.stage("normalized_bundle_serialization_and_seal"):
        bundle_path = bundle_dir / "bundle.json"
        if bundle_path.exists():
            existing = _load_canonical_json(
                bundle_path, code="normalized_bundle_invalid"
            )
            if existing != normalized_bundle:
                raise NormalizedRejected("normalized_warm_bundle_determinism_mismatch")
        else:
            if expected_mode != "cold":
                raise NormalizedRejected("normalized_warm_bundle_missing")
            _write_canonical_json(bundle_path, normalized_bundle, mode=0o444)
            _atomic_write(
                bundle_dir / "SEALED",
                normalized_bundle["normalized_bundle_root_sha256"].encode()
                + b"\n",
                mode=0o444,
            )
    capacity = _capacity(
        workspace=root,
        baseline_free=baseline_free,
        baseline_allocated=baseline_usage["allocated_bytes"],
    )
    measurement_result = measurements.result()
    measurement_result["label"] = SOURCE_STAGE_LABEL
    measurement_result["end_to_end"] = _resource_delta(
        resource_started,
        _resource_snapshot(),
        wall_seconds=time.perf_counter() - started,
    )
    swap_after = _swap_used_bytes()
    run_core = {
        "schema": NORMALIZED_RUN_SCHEMA,
        "status": "NORMALIZED_STAGE_EQUIVALENT",
        "run_label": str(run_label),
        "expected_mode": expected_mode,
        "command": list(command_argv or ("python_api:materialize_normalized_bundle",)),
        "workspace": str(root.resolve()),
        "source_bundle_dir": str(Path(source_bundle_dir).resolve()),
        "source_bundle_root_sha256": source_root,
        "selection_root_sha256": selection_root,
        "normalized_bundle_root_sha256": normalized_bundle[
            "normalized_bundle_root_sha256"
        ],
        "code_identity": code_identity,
        "cache_hits": {"hits": hits, "misses": misses},
        "counts": {
            "symbols": len(symbols),
            "logical_partitions": len(entries),
            "normalized_rows": total_rows,
            "normalized_payload_bytes": total_payload_bytes,
        },
        "cross_symbol_barrier": barrier,
        "source_independent_verification": source_verification,
        "source_verification_command": source_verification_command,
        "measurements": measurement_result,
        "disk": {
            "warning_free_bytes": WARNING_FREE_BYTES,
            "hard_floor_free_bytes": HARD_FLOOR_FREE_BYTES,
            "free_before_bytes": int(baseline_free),
            "free_after_bytes": capacity["free_bytes"],
        },
        "scratch": {
            "quota_bytes": MAX_SCRATCH_BYTES,
            "allocated_growth_bytes": capacity["allocated_growth_bytes"],
            "peak_observed": measurement_result["peak_scratch"],
        },
        "swap": {
            "available": swap_before is not None and swap_after is not None,
            "used_before_bytes": swap_before,
            "used_after_bytes": swap_after,
            "delta_bytes": (
                swap_after - swap_before
                if swap_before is not None and swap_after is not None
                else None
            ),
        },
        "source_stage_only": False,
        "normalization_stage_only": True,
        "whole_replay_claim": False,
        "policy_execution_entered": False,
    }
    run = _with_self_root(run_core, "run_root_sha256")
    _write_canonical_json(root / "runs" / f"{run_label}.json", run)
    return run


def _reroot_bundle(value: Mapping[str, Any]) -> dict[str, Any]:
    return _with_self_root(value, "normalized_bundle_root_sha256")


def build_normalized_failure_case(
    *, normalized_bundle_dir: Path, cases_root: Path, case_name: str
) -> Path:
    base = Path(normalized_bundle_dir).resolve()
    bundle = _load_canonical_json(base / "bundle.json", code="normalized_bundle_invalid")
    case_dir = Path(cases_root) / case_name
    if case_dir.exists():
        raise NormalizedRejected("normalized_failure_case_already_exists")
    case_dir.mkdir(parents=True)
    target = min(
        bundle["logical_partitions"],
        key=lambda row: (int(row["payload_byte_count"]), str(row["partition_id"])),
    )
    overrides: dict[str, dict[str, str]] = {}
    bundle_override: str | None = None
    marker_root = str(bundle["normalized_bundle_root_sha256"])
    if case_name in {"bit_flip", "truncation", "append"}:
        payload = (base / target["payload_path"]).read_bytes()
        if not payload:
            raise NormalizedRejected("normalized_failure_target_empty")
        if case_name == "bit_flip":
            changed = bytearray(payload)
            start = payload.find(b'"close":')
            index = next(
                (
                    position
                    for position in range(max(0, start), len(changed))
                    if changed[position] in b"009"
                ),
                -1,
            )
            if index < 0:
                raise NormalizedRejected("normalized_failure_target_invalid")
            changed[index] = ord("8") if changed[index] != ord("8") else ord("7")
            payload = bytes(changed)
        elif case_name == "truncation":
            payload = payload[:-1]
        else:
            first_line = payload.splitlines(keepends=True)[0]
            payload = payload + first_line
        path = case_dir / "payload.override.jsonl"
        _atomic_write(path, payload)
        overrides[target["partition_id"]] = {"payload_path": path.name}
    elif case_name in {
        "manifest_mismatch",
        "schema_mismatch",
        "source_mismatch",
        "config_mismatch",
        "code_mismatch",
    }:
        manifest = _load_canonical_json(
            base / target["manifest_path"], code="normalized_manifest_invalid"
        )
        if case_name == "manifest_mismatch":
            manifest["undeclared"] = True
        elif case_name == "schema_mismatch":
            manifest["schema"] = "wrong.schema"
            manifest = _with_self_root(manifest, "manifest_root_sha256")
        else:
            identity = dict(manifest["identity"])
            if case_name == "source_mismatch":
                identity["source_bundle_root_sha256"] = "0" * 64
            elif case_name == "config_mismatch":
                identity["config_projection_root_sha256"] = "0" * 64
            else:
                identity["legacy_normalizer_file_sha256"] = "0" * 64
            manifest["identity"] = identity
            manifest["identity_root_sha256"] = sha256_bytes(
                canonical_json_bytes(identity)
            )
            manifest = _with_self_root(manifest, "manifest_root_sha256")
        path = case_dir / "manifest.override.json"
        _write_canonical_json(path, manifest)
        overrides[target["partition_id"]] = {"manifest_path": path.name}
    elif case_name == "partition_reorder":
        changed = dict(bundle)
        entries = [dict(row) for row in bundle["logical_partitions"]]
        entries[0], entries[1] = entries[1], entries[0]
        changed["logical_partitions"] = entries
        changed = _reroot_bundle(changed)
        path = case_dir / "bundle.override.json"
        _write_canonical_json(path, changed)
        bundle_override = path.name
        marker_root = changed["normalized_bundle_root_sha256"]
    elif case_name == "stale_cache":
        changed = dict(bundle)
        changed["cache_identity_root_sha256"] = "0" * 64
        changed = _reroot_bundle(changed)
        path = case_dir / "bundle.override.json"
        _write_canonical_json(path, changed)
        bundle_override = path.name
        marker_root = changed["normalized_bundle_root_sha256"]
    elif case_name == "cross_symbol_barrier":
        changed = dict(bundle)
        barrier = dict(changed["cross_symbol_barrier"])
        barrier["sealed"] = False
        changed["cross_symbol_barrier"] = barrier
        changed = _reroot_bundle(changed)
        path = case_dir / "bundle.override.json"
        _write_canonical_json(path, changed)
        bundle_override = path.name
        marker_root = changed["normalized_bundle_root_sha256"]
    elif case_name in {"interruption_before_seal", "interruption_after_seal"}:
        pass
    else:
        raise NormalizedRejected("normalized_failure_case_unknown")
    case = {
        "schema": NORMALIZED_CASE_SCHEMA,
        "case_name": case_name,
        "base_normalized_bundle_dir": str(base),
        "bundle_manifest_override": bundle_override,
        "partition_overrides": overrides,
    }
    _write_canonical_json(case_dir / "case.json", case)
    if case_name != "interruption_before_seal":
        _atomic_write(
            case_dir / "SEALED", marker_root.encode() + b"\n", mode=0o444
        )
    return case_dir


def _invoke_verifier(command: list[str]) -> tuple[int, dict[str, Any]]:
    completed = subprocess.run(
        command,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=900,
    )
    try:
        receipt = json.loads(completed.stdout)
    except json.JSONDecodeError:
        raise NormalizedRejected("normalized_verifier_output_invalid") from None
    if type(receipt) is not dict:
        raise NormalizedRejected("normalized_verifier_output_invalid")
    return completed.returncode, receipt


def run_independent_normalized_verifier(
    *,
    normalized_bundle_dir: Path,
    source_bundle_dir: Path,
    selection_path: Path,
    output_path: Path,
    command_argv: Sequence[str] | None = None,
) -> dict[str, Any]:
    measurements = _StageMeasurements(Path(normalized_bundle_dir).parent)
    raw_output = Path(output_path).with_suffix(".verifier.json")
    command = [
        sys.executable,
        str(VERIFIER_PATH.resolve()),
        "verify",
        "--normalized-bundle-dir",
        str(Path(normalized_bundle_dir).resolve()),
        "--source-bundle-dir",
        str(Path(source_bundle_dir).resolve()),
        "--selection",
        str(Path(selection_path).resolve()),
        "--output",
        str(raw_output.resolve()),
    ]
    with measurements.stage("independent_normalized_verification"):
        returncode, receipt = _invoke_verifier(command)
    if returncode != 0 or receipt.get("status") != "VERIFIED":
        raise NormalizedRejected("independent_normalized_verification_failed")
    core = {
        "schema": NORMALIZED_VERIFIER_ENVELOPE_SCHEMA,
        "status": "VERIFIED",
        "command": command,
        "orchestrator_command": list(
            command_argv or ("python_api:run_independent_normalized_verifier",)
        ),
        "receipt": receipt,
        "receipt_file_sha256": file_sha256(raw_output),
        "measurements": measurements.result(),
    }
    envelope = _with_self_root(core, "envelope_root_sha256")
    _write_canonical_json(Path(output_path), envelope)
    return envelope


def run_normalized_failure_injections(
    *,
    normalized_bundle_dir: Path,
    source_bundle_dir: Path,
    selection_path: Path,
    cases_root: Path,
    output_path: Path,
    command_argv: Sequence[str] | None = None,
) -> dict[str, Any]:
    rejection_cases = (
        "bit_flip",
        "truncation",
        "append",
        "partition_reorder",
        "manifest_mismatch",
        "schema_mismatch",
        "source_mismatch",
        "config_mismatch",
        "code_mismatch",
        "stale_cache",
        "cross_symbol_barrier",
        "interruption_before_seal",
    )
    rows: list[dict[str, Any]] = []
    commands: list[list[str]] = []
    for case_name in (*rejection_cases, "interruption_after_seal"):
        case_dir = build_normalized_failure_case(
            normalized_bundle_dir=normalized_bundle_dir,
            cases_root=cases_root,
            case_name=case_name,
        )
        command = [
            sys.executable,
            str(VERIFIER_PATH.resolve()),
            "verify-case",
            "--case-dir",
            str(case_dir.resolve()),
            "--source-bundle-dir",
            str(Path(source_bundle_dir).resolve()),
            "--selection",
            str(Path(selection_path).resolve()),
        ]
        commands.append(command)
        returncode, receipt = _invoke_verifier(command)
        if case_name in rejection_cases:
            passed = returncode != 0 and receipt.get("status") == "REJECTED"
        else:
            passed = returncode == 0 and receipt.get("status") == "VERIFIED"
            commands.append(command)
            repeat_code, repeat = _invoke_verifier(command)
            passed = bool(
                passed
                and repeat_code == 0
                and repeat.get("normalized_bundle_root_sha256")
                == receipt.get("normalized_bundle_root_sha256")
            )
        if not passed:
            raise NormalizedRejected(
                f"normalized_failure_injection_failed:{case_name}"
            )
        rows.append(
            {
                "case": case_name,
                "verdict": "PASS",
                "observed_status": receipt.get("status"),
                "observed_code": receipt.get("code"),
                "fresh_process": True,
            }
        )
    scratch_usage = _tree_usage(Path(cases_root))
    if scratch_usage["allocated_bytes"] > MAX_SCRATCH_BYTES:
        raise NormalizedRejected("normalized_failure_scratch_quota_exceeded")
    if shutil.disk_usage(Path(cases_root)).free < HARD_FLOOR_FREE_BYTES:
        raise NormalizedRejected("normalized_disk_hard_floor_reached")
    core = {
        "schema": NORMALIZED_INJECTION_SCHEMA,
        "status": "ALL_REQUIRED_CASES_PASS",
        "command": list(
            command_argv or ("python_api:run_normalized_failure_injections",)
        ),
        "verifier_commands": commands,
        "cases": rows,
        "case_count": len(rows),
        "scratch_usage": scratch_usage,
        "policy_execution_entered": False,
    }
    receipt = _with_self_root(core, "injection_root_sha256")
    _write_canonical_json(Path(output_path), receipt)
    return receipt


def _load_run(path: Path) -> dict[str, Any]:
    run = _load_canonical_json(path, code="normalized_run_invalid")
    if run.get("schema") != NORMALIZED_RUN_SCHEMA:
        raise NormalizedRejected("normalized_run_invalid")
    _verify_self_root(run, "run_root_sha256", code="normalized_run_invalid")
    return run


def finalize_normalized_result(
    *,
    cold_run_path: Path,
    cold_repeat_run_path: Path,
    warm_run_path: Path,
    warm_repeat_run_path: Path,
    verifier_paths: Sequence[Path],
    injection_path: Path,
    output_path: Path,
    command_argv: Sequence[str] | None = None,
) -> dict[str, Any]:
    runs = [
        _load_run(path)
        for path in (
            cold_run_path,
            cold_repeat_run_path,
            warm_run_path,
            warm_repeat_run_path,
        )
    ]
    roots = {run["normalized_bundle_root_sha256"] for run in runs}
    if len(roots) != 1:
        raise NormalizedRejected("normalized_run_determinism_mismatch")
    logical_count = int(runs[0]["counts"]["logical_partitions"])
    if any(
        run["cache_hits"] != {"hits": 0, "misses": logical_count}
        for run in runs[:2]
    ):
        raise NormalizedRejected("normalized_cold_cache_classification_mismatch")
    if any(
        run["cache_hits"] != {"hits": logical_count, "misses": 0}
        for run in runs[2:]
    ):
        raise NormalizedRejected("normalized_warm_cache_classification_mismatch")
    if any(
        run.get("policy_execution_entered") is not False
        or run.get("source_independent_verification", {}).get("status") != "VERIFIED"
        for run in runs
    ):
        raise NormalizedRejected("normalized_run_boundary_mismatch")
    envelopes = [
        _load_canonical_json(path, code="normalized_verifier_envelope_invalid")
        for path in verifier_paths
    ]
    for envelope in envelopes:
        if envelope.get("schema") != NORMALIZED_VERIFIER_ENVELOPE_SCHEMA:
            raise NormalizedRejected("normalized_verifier_envelope_invalid")
        _verify_self_root(
            envelope,
            "envelope_root_sha256",
            code="normalized_verifier_envelope_invalid",
        )
        if (
            envelope.get("status") != "VERIFIED"
            or envelope.get("receipt", {}).get("status") != "VERIFIED"
            or envelope.get("receipt", {}).get(
                "normalized_bundle_root_sha256"
            )
            not in roots
        ):
            raise NormalizedRejected("normalized_verifier_envelope_invalid")
    injections = _load_canonical_json(
        injection_path, code="normalized_injection_receipt_invalid"
    )
    if injections.get("schema") != NORMALIZED_INJECTION_SCHEMA:
        raise NormalizedRejected("normalized_injection_receipt_invalid")
    _verify_self_root(
        injections,
        "injection_root_sha256",
        code="normalized_injection_receipt_invalid",
    )
    if injections.get("status") != "ALL_REQUIRED_CASES_PASS":
        raise NormalizedRejected("normalized_injection_receipt_invalid")
    stage_wall = [
        round(
            sum(
                float(row.get("wall_seconds") or 0.0)
                for row in run["measurements"]["stages"].values()
            ),
            9,
        )
        for run in runs
    ]
    end_to_end_wall = [
        float(run["measurements"]["end_to_end"]["wall_seconds"])
        for run in runs
    ]
    workspaces = {
        str(run["workspace"]): _tree_usage(Path(run["workspace"])) for run in runs
    }
    failure_scratch = injections.get("scratch_usage")
    if type(failure_scratch) is not dict:
        raise NormalizedRejected("normalized_injection_receipt_invalid")
    combined = sum(row["allocated_bytes"] for row in workspaces.values()) + int(
        failure_scratch.get("allocated_bytes") or 0
    )
    if combined > MAX_SCRATCH_BYTES:
        raise NormalizedRejected("normalized_combined_scratch_quota_exceeded")
    commands = {
        "materialization": [run["command"] for run in runs],
        "source_verification_processes": [
            run["source_verification_command"] for run in runs
        ],
        "independent_verifier_orchestration": [
            envelope["orchestrator_command"] for envelope in envelopes
        ],
        "independent_verifier_processes": [
            envelope["command"] for envelope in envelopes
        ],
        "failure_injection_orchestration": injections["command"],
        "failure_verifier_processes": injections["verifier_commands"],
        "finalization": list(
            command_argv or ("python_api:finalize_normalized_result",)
        ),
    }
    core = {
        "schema": NORMALIZED_RESULT_SCHEMA,
        "status": "ACCEPTED",
        "gate": "NORMALIZATION_EQUIVALENCE_ACCEPTED",
        "source_bundle_root_sha256": runs[0]["source_bundle_root_sha256"],
        "selection_root_sha256": runs[0]["selection_root_sha256"],
        "normalized_bundle_root_sha256": next(iter(roots)),
        "code_identity": runs[0]["code_identity"],
        "counts": runs[0]["counts"],
        "cross_symbol_barrier": runs[0]["cross_symbol_barrier"],
        "determinism": {
            "fresh_process_runs": 4,
            "cold_runs": 2,
            "warm_runs": 2,
            "bundle_roots_identical": True,
            "cold_cache_misses_per_run": logical_count,
            "warm_cache_hits_per_run": logical_count,
        },
        "measurements": {
            "label": SOURCE_STAGE_LABEL,
            "stage_attributed_wall_seconds_by_run": stage_wall,
            "end_to_end_wall_seconds_by_run": end_to_end_wall,
            "cold_to_first_warm_ratio": (
                round(end_to_end_wall[0] / end_to_end_wall[2], 6)
                if end_to_end_wall[2]
                else None
            ),
            "whole_replay_claim": False,
        },
        "resource_measurements": [run["measurements"] for run in runs],
        "disk": [run["disk"] for run in runs],
        "swap": [run["swap"] for run in runs],
        "combined_retained_scratch": {
            "quota_bytes": MAX_SCRATCH_BYTES,
            "allocated_bytes": combined,
            "workspaces": workspaces,
            "failure_cases": failure_scratch,
        },
        "independent_verification": [
            envelope["receipt"] for envelope in envelopes
        ],
        "failure_injections": injections["cases"],
        "exact_command_receipts": commands,
        "outcome_blind_structural_only": True,
        "policy_execution_entered": False,
        "successor_replay_launched": False,
        "whole_replay_claim": False,
    }
    result = _with_self_root(core, "result_root_sha256")
    forbidden = (
        "pnl",
        "win_rate",
        "win_count",
        "loss_count",
        "r_total",
        "treatment_economics",
        "march_",
        "economic_outcome",
    )
    serialized = canonical_json_bytes(result).lower()
    if any(token.encode() in serialized for token in forbidden):
        raise NormalizedRejected("normalized_result_content_policy_failed")
    _write_canonical_json(Path(output_path), result)
    return result


def _executed_command(argv: Sequence[str]) -> list[str]:
    original = getattr(sys, "orig_argv", None)
    if type(original) is list and original:
        return [str(item) for item in original]
    return [sys.executable, str(Path(__file__).resolve()), *map(str, argv)]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    materialize = subparsers.add_parser("materialize")
    materialize.add_argument("--source-bundle-dir", type=Path, required=True)
    materialize.add_argument("--selection", type=Path, required=True)
    materialize.add_argument("--workspace", type=Path, required=True)
    materialize.add_argument("--run-label", required=True)
    materialize.add_argument("--mode", choices=("cold", "warm"), required=True)
    verify = subparsers.add_parser("verify-independent")
    verify.add_argument("--normalized-bundle-dir", type=Path, required=True)
    verify.add_argument("--source-bundle-dir", type=Path, required=True)
    verify.add_argument("--selection", type=Path, required=True)
    verify.add_argument("--output", type=Path, required=True)
    inject = subparsers.add_parser("inject")
    inject.add_argument("--normalized-bundle-dir", type=Path, required=True)
    inject.add_argument("--source-bundle-dir", type=Path, required=True)
    inject.add_argument("--selection", type=Path, required=True)
    inject.add_argument("--cases-root", type=Path, required=True)
    inject.add_argument("--output", type=Path, required=True)
    finalize = subparsers.add_parser("finalize")
    finalize.add_argument("--cold-run", type=Path, required=True)
    finalize.add_argument("--cold-repeat-run", type=Path, required=True)
    finalize.add_argument("--warm-run", type=Path, required=True)
    finalize.add_argument("--warm-repeat-run", type=Path, required=True)
    finalize.add_argument("--verifier", type=Path, action="append", required=True)
    finalize.add_argument("--injections", type=Path, required=True)
    finalize.add_argument("--output", type=Path, required=True)
    return parser


def _main(argv: list[str]) -> int:
    args = _parser().parse_args(argv)
    try:
        command = _executed_command(argv)
        if args.command == "materialize":
            result = materialize_normalized_bundle(
                source_bundle_dir=args.source_bundle_dir,
                selection_path=args.selection,
                workspace=args.workspace,
                run_label=args.run_label,
                expected_mode=args.mode,
                command_argv=command,
            )
        elif args.command == "verify-independent":
            result = run_independent_normalized_verifier(
                normalized_bundle_dir=args.normalized_bundle_dir,
                source_bundle_dir=args.source_bundle_dir,
                selection_path=args.selection,
                output_path=args.output,
                command_argv=command,
            )
        elif args.command == "inject":
            result = run_normalized_failure_injections(
                normalized_bundle_dir=args.normalized_bundle_dir,
                source_bundle_dir=args.source_bundle_dir,
                selection_path=args.selection,
                cases_root=args.cases_root,
                output_path=args.output,
                command_argv=command,
            )
        else:
            result = finalize_normalized_result(
                cold_run_path=args.cold_run,
                cold_repeat_run_path=args.cold_repeat_run,
                warm_run_path=args.warm_run,
                warm_repeat_run_path=args.warm_repeat_run,
                verifier_paths=args.verifier,
                injection_path=args.injections,
                output_path=args.output,
                command_argv=command,
            )
    except (NormalizedRejected, SliceRejected) as exc:
        code = getattr(exc, "code", str(exc))
        print(json.dumps({"status": "REJECTED", "code": code}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
