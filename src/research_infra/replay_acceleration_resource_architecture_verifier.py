"""Independent verifier for the resource and retention result."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping


SCHEMA = "gtos.replay_acceleration.resource_architecture_result.v1"
GIB = 1024**3
WARNING = 34 * GIB
HARD_FLOOR = 28 * GIB
QUOTA = GIB


class VerificationError(RuntimeError):
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
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise VerificationError(code)


def verify_resource_result(result_path: Path) -> dict[str, Any]:
    raw = result_path.read_bytes()
    _require(raw.endswith(b"\n"), "result_newline_missing")
    try:
        result = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VerificationError("result_json_invalid") from exc
    _require(result.get("schema") == SCHEMA, "result_schema_mismatch")
    _require(result.get("status") == "ACCEPTED", "result_status_invalid")
    _require(result.get("gate") == "RESOURCE_STORAGE_ARCHITECTURE_ACCEPTED", "result_gate_mismatch")
    recorded = result.get("result_root_sha256")
    payload = dict(result)
    payload.pop("result_root_sha256", None)
    _require(recorded == _root(payload), "result_root_mismatch")
    disk = result.get("disk") or {}
    _require(disk.get("warning_bytes") == WARNING, "disk_warning_mismatch")
    _require(disk.get("hard_floor_bytes") == HARD_FLOOR, "disk_floor_mismatch")
    _require(disk.get("available_bytes", 0) >= WARNING, "recorded_disk_below_warning")
    live = os.statvfs(Path.cwd())
    _require(live.f_bavail * live.f_frsize >= HARD_FLOOR, "live_disk_below_hard_floor")
    retention = result.get("retention") or {}
    slices = retention.get("bounded_slices") or []
    _require(bool(slices), "bounded_slice_inventory_missing")
    for row in slices:
        _require(row.get("allocated_bytes", QUOTA) < QUOTA, "bounded_slice_quota_invalid")
        _require(Path(str(row.get("path") or "")).exists(), "bounded_slice_path_missing")
    _require(retention.get("files_deleted") == 0, "retention_deleted_files")
    _require(retention.get("bytes_reclaimed") == 0, "retention_reclaimed_bytes")
    _require(retention.get("unique_proof_evidence_preserved") is True, "proof_preservation_invalid")
    _require(retention.get("broad_lfs_hydration_performed") is False, "broad_lfs_hydration_invalid")
    _require(retention.get("lfs_prune_performed") is False, "lfs_prune_invalid")
    hash_probe = result.get("hash_probe") or {}
    files = hash_probe.get("files") or []
    _require(len(files) == hash_probe.get("file_count"), "hash_inventory_count_mismatch")
    for row in files:
        path = Path(str(row.get("path") or ""))
        _require(path.is_file(), "hash_inventory_file_missing")
        _require(path.stat().st_size == row.get("logical_bytes"), "hash_inventory_size_mismatch")
        _require(_file_hash(path) == row.get("sha256"), "hash_inventory_digest_mismatch")
    _require(_root(files) == hash_probe.get("inventory_root_sha256"), "hash_inventory_root_mismatch")
    compression = result.get("compression_probe") or {}
    _require(
        compression.get("scope") == "typed_structural_shards_in_memory_only"
        and compression.get("persistent_compressed_artifact_created") is False
        and 0 < compression.get("compressed_bytes", 0) < compression.get("input_bytes", 0),
        "compression_probe_invalid",
    )
    probes = result.get("verification_probes") or []
    _require(len(probes) == 4, "verification_probe_count_mismatch")
    _require(all(row.get("status") == "VERIFIED" for row in probes), "verification_probe_invalid")
    legacy = result.get("legacy_process") or {}
    _require(legacy.get("pid") == 34389, "legacy_pid_mismatch")
    _require(legacy.get("modified_or_signaled") is False, "legacy_process_mutation_flag_invalid")
    code = result.get("code_identity") or {}
    for path_key, hash_key in (
        ("writer_path", "writer_sha256"),
        ("independent_verifier_path", "independent_verifier_sha256"),
    ):
        path = Path(str(code.get(path_key) or ""))
        _require(path.is_file(), "code_file_missing")
        _require(_file_hash(path) == code.get(hash_key), "code_hash_mismatch")
    execution = result.get("execution") or {}
    _require(execution.get("policy_callbacks_invoked") is False, "policy_callback_flag_invalid")
    _require(execution.get("successor_arm_execution_launched") is False, "successor_launch_flag_invalid")
    return {
        "status": "VERIFIED",
        "result_root_sha256": recorded,
        "persisted_bytes_sha256": hashlib.sha256(raw).hexdigest(),
        "bounded_slice_count": len(slices),
    }


def _atomic_receipt(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_bytes(_canonical(payload) + b"\n")
    os.replace(temporary, path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("result", type=Path)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args(argv)
    receipt = verify_resource_result(args.result)
    if args.receipt:
        _atomic_receipt(args.receipt, receipt)
    print(_canonical(receipt).decode("ascii"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
