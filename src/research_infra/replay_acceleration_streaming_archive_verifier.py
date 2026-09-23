"""Independent verifier for reconstructable zstd replay-proof shards."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
from collections.abc import Callable, Iterator, Mapping
from datetime import date, timedelta
from pathlib import Path
from typing import Any


SHARD_SCHEMA = "gtos.replay_acceleration.streaming_proof_shard.v1"
CAMPAIGN_SCHEMA = "gtos.replay_acceleration.streaming_proof_campaign.v1"
RECEIPT_SCHEMA = "gtos.replay_acceleration.streaming_proof_verification.v1"
CHECKPOINT_AUTHORITY_SCHEMA = (
    "gtos.replay_acceleration.streaming_checkpoint_authority.v1"
)
CHECKPOINT_PREIMAGE_SCHEMA = (
    "gtos.replay_acceleration.streaming_checkpoint_preimage.v1"
)
CHECKPOINT_CHAIN_GENESIS_SCHEMA = (
    "gtos.replay_acceleration.streaming_checkpoint_chain_genesis.v1"
)
CHECKPOINT_CHAIN_LINK_SCHEMA = (
    "gtos.replay_acceleration.streaming_checkpoint_chain_link.v1"
)
SHARED_EXECUTION_CONTRACT_SCHEMA = (
    "gtos.final_moonshot.broad_replay.shared_execution_contract.v1"
)
CHECKPOINT_AUTHORITY_KEYS = frozenset(
    {
        "schema",
        "output_prefix",
        "run_identity_root_sha256",
        "source_plan_digest_sha256",
        "arm_fingerprint_sha256",
        "shared_execution_contract_sha256",
        "accelerated_code_config_authority_root_sha256",
    }
)
CHECKPOINT_PREIMAGE_KEYS = frozenset(
    {
        "schema",
        "segment_id",
        "segment_index",
        "start_day",
        "end_day",
        "completed_day",
        "output_prefix",
        "checkpoint_authority",
        "pre_archive_partial_summary",
        "hot_surfaces",
        "prior_checkpoint_chain_root_sha256",
        "checkpoint_root_sha256",
    }
)
CHECKPOINT_SNAPSHOT_KEYS = frozenset(
    {"source_name", "snapshot_path", "bytes", "sha256"}
)
CHECKPOINT_HOT_SURFACE_KEYS = frozenset(
    {"role", "name", "bytes", "rows", "sha256"}
)
CHECKPOINT_CHAIN_ENTRY_KEYS = frozenset(
    {
        "segment_id",
        "segment_index",
        "checkpoint_preimage_path",
        "checkpoint_preimage_sha256",
        "checkpoint_root_sha256",
        "prior_checkpoint_chain_root_sha256",
        "checkpoint_chain_root_sha256",
    }
)
SHARD_MANIFEST_KEYS = frozenset(
    {
        "schema",
        "segment_id",
        "segment_index",
        "start_day",
        "end_day",
        "output_prefix",
        "surfaces",
        "checkpoint_preimage_path",
        "checkpoint_preimage_sha256",
        "checkpoint_root_sha256",
        "prior_checkpoint_chain_root_sha256",
        "checkpoint_chain_root_sha256",
        "compression",
        "exact_concatenation_reconstruction",
        "economic_values_exposed",
        "manifest_root_sha256",
    }
)
CAMPAIGN_MANIFEST_KEYS = frozenset(
    {
        "schema",
        "output_prefix",
        "hot_roles",
        "checkpoint_authority",
        "checkpoint_chain_genesis_root_sha256",
        "checkpoint_chain",
        "checkpoint_chain_set_root_sha256",
        "terminal_checkpoint_chain_root_sha256",
        "shards",
        "cumulative_surfaces",
        "hot_tombstones",
        "exact_concatenation_reconstruction",
        "writer_retains_economic_values",
        "live_broker_authority",
        "campaign_manifest_root_sha256",
    }
)
ROW_TYPES_BY_ROLE = {
    "decision": "asof_decision",
    "scorecard": "scheduler_scorecard",
    "missed": "missed_opportunity",
}
ROW_PROVENANCE_SCHEMA = "broad_live_as_if_replay_row_provenance_v1"
ROLES = ("decision", "scorecard", "missed")
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def root(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def self_root(value: Mapping[str, Any], field: str) -> str:
    projection = dict(value)
    projection.pop(field, None)
    return root(projection)


def _is_sha256(value: Any) -> bool:
    text = str(value or "")
    return len(text) == 64 and all(
        character in "009abcdef" for character in text
    )


def _lexical_path(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def _validate_partition_row(
    raw: bytes,
    *,
    role: str,
    start_day: date,
    end_day: date,
) -> None:
    try:
        row = json.loads(raw)
        trading_day = date.fromisoformat(row["trading_day"])
    except (KeyError, TypeError, ValueError, UnicodeError, json.JSONDecodeError):
        raise ValueError("archive_row_partition_mismatch") from None
    profile = row.get("profile")
    split = row.get("split")
    start_text = start_day.isoformat()
    end_text = end_day.isoformat()
    expected_chunk_id = f"{profile}:{split}:{start_text}:{end_text}"
    expected_day_count = (end_day - start_day).days + 1
    if (
        type(row) is not dict
        or role not in ROW_TYPES_BY_ROLE
        or row.get("row_type") != ROW_TYPES_BY_ROLE[role]
        or type(profile) is not str
        or not profile
        or row.get("broad_replay_profile") != profile
        or type(split) is not str
        or not split
        or row.get("chunk_id") != expected_chunk_id
        or row.get("chunk_start_day") != start_text
        or row.get("chunk_end_day") != end_text
        or type(row.get("chunk_day_count")) is not int
        or row.get("chunk_day_count") != expected_day_count
        or row.get("row_provenance_schema") != ROW_PROVENANCE_SCHEMA
        or not start_day <= trading_day <= end_day
    ):
        raise ValueError("archive_row_partition_mismatch")


def _path_has_symlink_component(path: Path) -> bool:
    lexical = _lexical_path(path)
    current = Path(lexical.anchor)
    for component in lexical.parts[1:]:
        current /= component
        if current.is_symlink():
            return True
    return False


def _open_regular_nofollow(path: Path, *, code: str) -> int:
    lexical = _lexical_path(path)
    if _path_has_symlink_component(lexical):
        raise ValueError("archive_symlink_component_forbidden")
    directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    parent_descriptor = -1
    try:
        parent_descriptor = os.open(lexical.anchor, directory_flags)
        for component in lexical.parts[1:-1]:
            next_descriptor = os.open(
                component,
                directory_flags | nofollow,
                dir_fd=parent_descriptor,
            )
            os.close(parent_descriptor)
            parent_descriptor = next_descriptor
        descriptor = os.open(
            lexical.name,
            os.O_RDONLY | nofollow,
            dir_fd=parent_descriptor,
        )
    except OSError:
        raise ValueError(code) from None
    finally:
        if parent_descriptor >= 0:
            os.close(parent_descriptor)
    opened = os.fstat(descriptor)
    if not stat.S_ISREG(opened.st_mode):
        os.close(descriptor)
        raise ValueError(code)
    if opened.st_nlink != 1:
        os.close(descriptor)
        raise ValueError("archive_hardlink_forbidden")
    return descriptor


class BoundRegularFile:
    def __init__(self, path: Path, *, code: str) -> None:
        self.path = _lexical_path(path)
        self.code = str(code)
        self.descriptor = _open_regular_nofollow(self.path, code=self.code)
        self._opened = os.fstat(self.descriptor)

    @property
    def identity(self) -> tuple[int, int]:
        return self._opened.st_dev, self._opened.st_ino

    def _assert_descriptor_unchanged(self) -> None:
        observed = os.fstat(self.descriptor)
        if (
            observed.st_dev != self._opened.st_dev
            or observed.st_ino != self._opened.st_ino
            or observed.st_size != self._opened.st_size
            or observed.st_mtime_ns != self._opened.st_mtime_ns
        ):
            raise ValueError("archive_evidence_changed_during_read")

    def assert_path_unchanged(self) -> None:
        if _path_has_symlink_component(self.path):
            raise ValueError("archive_evidence_path_changed")
        try:
            descriptor = _open_regular_nofollow(
                self.path,
                code="archive_evidence_path_changed",
            )
        except ValueError:
            raise ValueError("archive_evidence_path_changed") from None
        try:
            observed = os.fstat(descriptor)
            if (observed.st_dev, observed.st_ino) != self.identity:
                raise ValueError("archive_evidence_path_changed")
        finally:
            os.close(descriptor)
        self._assert_descriptor_unchanged()

    def chunks(self) -> Iterator[bytes]:
        offset = 0
        while True:
            chunk = os.pread(self.descriptor, 1024 * 1024, offset)
            if not chunk:
                break
            offset += len(chunk)
            yield chunk
        self._assert_descriptor_unchanged()

    def read_bytes(self) -> bytes:
        return b"".join(self.chunks())

    def close(self) -> None:
        if self.descriptor >= 0:
            os.close(self.descriptor)
            self.descriptor = -1


class BoundEvidence:
    def __init__(self, *, archive_root: Path) -> None:
        self.archive_root = _lexical_path(archive_root)
        self._files: dict[Path, BoundRegularFile] = {}
        self._identities: dict[tuple[int, int], Path] = {}

    def __enter__(self) -> BoundEvidence:
        return self

    def __exit__(self, *_unused: object) -> None:
        for bound in reversed(tuple(self._files.values())):
            bound.close()

    def bind(self, path: Path, *, code: str) -> BoundRegularFile:
        lexical = _lexical_path(path)
        try:
            lexical.relative_to(self.archive_root)
        except ValueError:
            raise ValueError("archive_path_outside_root") from None
        bound = self._files.get(lexical)
        if bound is not None:
            return bound
        bound = BoundRegularFile(lexical, code=code)
        previous_path = self._identities.get(bound.identity)
        if previous_path is not None and previous_path != lexical:
            bound.close()
            raise ValueError("archive_inode_alias_forbidden")
        self._files[lexical] = bound
        self._identities[bound.identity] = lexical
        return bound

    def assert_paths_unchanged(self) -> None:
        for bound in self._files.values():
            bound.assert_path_unchanged()


def _load_canonical(bound: BoundRegularFile) -> dict[str, Any]:
    raw = bound.read_bytes()
    try:
        value = json.loads(raw)
    except (UnicodeError, json.JSONDecodeError):
        raise ValueError("archive_artifact_not_canonical") from None
    if type(value) is not dict or raw != canonical_bytes(value) + b"\n":
        raise ValueError("archive_artifact_not_canonical")
    return value


def _file_contract(bound: BoundRegularFile) -> dict[str, Any]:
    digest = hashlib.sha256()
    size = 0
    for chunk in bound.chunks():
        digest.update(chunk)
        size += len(chunk)
    return {"bytes": size, "sha256": digest.hexdigest()}


def _campaign_path(path: Path) -> tuple[Path, Path]:
    lexical = _lexical_path(path)
    if lexical.name != "CAMPAIGN_ARCHIVE_MANIFEST.json":
        raise ValueError("archive_campaign_topology_invalid")
    return lexical, lexical.parent


def _manifest_topology(path: Path) -> tuple[Path, Path, Path]:
    lexical = _lexical_path(path)
    segment_dir = lexical.parent
    shards_dir = segment_dir.parent
    archive_root = shards_dir.parent
    if lexical.name != "SHARD_MANIFEST.json" or shards_dir.name != "shards":
        raise ValueError("archive_shard_topology_invalid")
    return lexical, segment_dir, archive_root


def _validate_manifest(
    manifest: Mapping[str, Any],
    *,
    manifest_path: Path,
    segment_dir: Path,
) -> None:
    try:
        segment_index = int(manifest["segment_index"])
        start_day = date.fromisoformat(str(manifest["start_day"]))
        end_day = date.fromisoformat(str(manifest["end_day"]))
    except (KeyError, TypeError, ValueError):
        raise ValueError("archive_shard_manifest_invalid") from None
    expected_segment_id = (
        f"{segment_index:03d}_{start_day.isoformat()}_{end_day.isoformat()}"
    )
    surfaces = manifest.get("surfaces")
    checkpoint_preimage_path = Path(
        str(manifest.get("checkpoint_preimage_path") or "")
    )
    if (
        type(manifest) is not dict
        or set(manifest) != SHARD_MANIFEST_KEYS
        or manifest.get("schema") != SHARD_SCHEMA
        or manifest.get("manifest_root_sha256")
        != self_root(manifest, "manifest_root_sha256")
        or start_day > end_day
        or segment_index < 1
        or manifest.get("segment_id") != expected_segment_id
        or segment_dir.name != expected_segment_id
        or not str(manifest.get("output_prefix") or "")
        or not checkpoint_preimage_path.is_absolute()
        or _lexical_path(checkpoint_preimage_path)
        != segment_dir / "CHECKPOINT_PREIMAGE.json"
        or not _is_sha256(manifest.get("checkpoint_preimage_sha256"))
        or not _is_sha256(manifest.get("checkpoint_root_sha256"))
        or not _is_sha256(
            manifest.get("prior_checkpoint_chain_root_sha256")
        )
        or not _is_sha256(manifest.get("checkpoint_chain_root_sha256"))
        or type(manifest.get("exact_concatenation_reconstruction")) is not bool
        or manifest.get("exact_concatenation_reconstruction") is not True
        or type(manifest.get("economic_values_exposed")) is not bool
        or manifest.get("economic_values_exposed") is not False
        or not isinstance(surfaces, list)
        or [item.get("role") for item in surfaces] != list(ROLES)
    ):
        raise ValueError("archive_shard_manifest_invalid")
    for item in surfaces:
        role = str(item.get("role") or "")
        expected_path = segment_dir / f"{role}.jsonl.zst"
        supplied_path = Path(str(item.get("compressed_path") or ""))
        if (
            not supplied_path.is_absolute()
            or _lexical_path(supplied_path) != expected_path
            or type(item.get("raw_bytes")) is not int
            or type(item.get("raw_rows")) is not int
            or type(item.get("compressed_bytes")) is not int
            or item.get("raw_bytes", -1) < 0
            or item.get("raw_rows", -1) < 0
            or item.get("compressed_bytes", -1) < 0
            or not _is_sha256(item.get("raw_sha256"))
            or not _is_sha256(item.get("compressed_sha256"))
            or not str(item.get("raw_name") or "")
        ):
            raise ValueError("archive_surface_topology_invalid")
    if manifest_path != segment_dir / "SHARD_MANIFEST.json":
        raise ValueError("archive_shard_topology_invalid")


def _validate_checkpoint_authority(
    value: Any,
    *,
    output_prefix: str,
) -> dict[str, Any]:
    hash_fields = (
        "run_identity_root_sha256",
        "source_plan_digest_sha256",
        "arm_fingerprint_sha256",
        "shared_execution_contract_sha256",
        "accelerated_code_config_authority_root_sha256",
    )
    if (
        type(value) is not dict
        or set(value) != CHECKPOINT_AUTHORITY_KEYS
        or value.get("schema") != CHECKPOINT_AUTHORITY_SCHEMA
        or value.get("output_prefix") != output_prefix
        or any(
            type(value.get(field)) is not str
            or not _is_sha256(value.get(field))
            for field in hash_fields
        )
    ):
        raise ValueError("archive_checkpoint_authority_invalid")
    return dict(value)


def _checkpoint_authority_from_snapshot(
    snapshot_file: BoundRegularFile,
    *,
    manifest: Mapping[str, Any],
) -> dict[str, Any]:
    try:
        partial = json.loads(snapshot_file.read_bytes())
    except (UnicodeError, json.JSONDecodeError):
        raise ValueError("archive_checkpoint_snapshot_invalid") from None
    if type(partial) is not dict:
        raise ValueError("archive_checkpoint_snapshot_invalid")
    identity = partial.get("attempt5_execution_identity")
    shared = partial.get("shared_execution_contract")
    binding = partial.get("b7_5_contract_binding")
    arm = partial.get("b7_5_selection_sizing_factorial_arm_binding")
    if (
        type(identity) is not dict
        or type(shared) is not dict
        or type(binding) is not dict
        or type(arm) is not dict
        or partial.get("output_prefix") != manifest.get("output_prefix")
        or partial.get("last_completed_end_day") != manifest.get("end_day")
    ):
        raise ValueError("archive_checkpoint_snapshot_authority_invalid")

    run_identity_root_sha256 = identity.get("identity_root_sha256")
    if (
        type(run_identity_root_sha256) is not str
        or not _is_sha256(run_identity_root_sha256)
        or run_identity_root_sha256
        != self_root(identity, "identity_root_sha256")
    ):
        raise ValueError("archive_checkpoint_run_identity_invalid")

    shared_digest = shared.get("shared_execution_contract_digest_sha256")
    shared_payload = dict(shared)
    shared_payload.pop("valid", None)
    shared_payload.pop("status", None)
    shared_payload.pop("shared_execution_contract_digest_sha256", None)
    code_authority = shared.get("code_authority")
    config_file_hashes = shared.get("config_file_hashes")
    if (
        shared.get("schema") != SHARED_EXECUTION_CONTRACT_SCHEMA
        or shared.get("valid") is not True
        or shared.get("status") != "shared_execution_contract_bound"
        or type(shared_digest) is not str
        or shared_digest != root(shared_payload)
        or type(code_authority) is not list
        or type(config_file_hashes) is not dict
    ):
        raise ValueError("archive_checkpoint_shared_execution_invalid")
    if any(
        type(item) is not dict
        or set(item) != {"path", "sha256"}
        or type(item.get("path")) is not str
        or not item.get("path")
        or type(item.get("sha256")) is not str
        or not _is_sha256(item.get("sha256"))
        for item in code_authority
    ) or any(
        type(path) is not str
        or not path
        or type(digest) is not str
        or not _is_sha256(digest)
        for path, digest in config_file_hashes.items()
    ):
        raise ValueError("archive_checkpoint_code_config_authority_invalid")

    source_plan_digests = binding.get("actual_source_plan_digests_sha256")
    arm_fingerprint_sha256 = arm.get("arm_fingerprint_sha256")
    if (
        type(source_plan_digests) is not list
        or len(source_plan_digests) != 1
        or type(source_plan_digests[0]) is not str
        or not _is_sha256(source_plan_digests[0])
        or type(arm_fingerprint_sha256) is not str
        or not _is_sha256(arm_fingerprint_sha256)
        or binding.get("selection_sizing_factorial_arm_binding") != arm
        or binding.get("actual_shared_execution_contract_digest_sha256")
        != shared_digest
    ):
        raise ValueError("archive_checkpoint_replay_authority_invalid")

    return {
        "schema": CHECKPOINT_AUTHORITY_SCHEMA,
        "output_prefix": manifest["output_prefix"],
        "run_identity_root_sha256": run_identity_root_sha256,
        "source_plan_digest_sha256": source_plan_digests[0],
        "arm_fingerprint_sha256": arm_fingerprint_sha256,
        "shared_execution_contract_sha256": shared_digest,
        "accelerated_code_config_authority_root_sha256": root(
            {
                "code_authority": code_authority,
                "config_file_hashes": config_file_hashes,
            }
        ),
    }


def _verify_checkpoint(
    *,
    evidence: BoundEvidence,
    manifest: Mapping[str, Any],
    segment_dir: Path,
    expected_authority: Mapping[str, Any] | None = None,
    expected_prior_checkpoint_chain_root_sha256: str | None = None,
) -> dict[str, Any]:
    checkpoint_preimage_path = segment_dir / "CHECKPOINT_PREIMAGE.json"
    checkpoint_preimage_file = evidence.bind(
        checkpoint_preimage_path,
        code="archive_checkpoint_preimage_invalid",
    )
    checkpoint_preimage_contract = _file_contract(checkpoint_preimage_file)
    if checkpoint_preimage_contract["sha256"] != manifest.get(
        "checkpoint_preimage_sha256"
    ):
        raise ValueError("archive_checkpoint_preimage_identity_mismatch")
    checkpoint_preimage = _load_canonical(checkpoint_preimage_file)
    if set(checkpoint_preimage) != CHECKPOINT_PREIMAGE_KEYS:
        raise ValueError("archive_checkpoint_preimage_invalid")

    authority = _validate_checkpoint_authority(
        checkpoint_preimage.get("checkpoint_authority"),
        output_prefix=str(manifest["output_prefix"]),
    )
    if expected_authority is not None and authority != dict(expected_authority):
        raise ValueError("archive_checkpoint_authority_drift")

    snapshot = checkpoint_preimage.get("pre_archive_partial_summary")
    if type(snapshot) is not dict or set(snapshot) != CHECKPOINT_SNAPSHOT_KEYS:
        raise ValueError("archive_checkpoint_snapshot_invalid")
    source_name = snapshot.get("source_name")
    snapshot_path = Path(str(snapshot.get("snapshot_path") or ""))
    if (
        type(source_name) is not str
        or not source_name
        or Path(source_name).name != source_name
        or not snapshot_path.is_absolute()
        or _lexical_path(snapshot_path)
        != segment_dir / "PRE_ARCHIVE_PARTIAL_SUMMARY.json"
        or type(snapshot.get("bytes")) is not int
        or snapshot.get("bytes", -1) < 0
        or type(snapshot.get("sha256")) is not str
        or not _is_sha256(snapshot.get("sha256"))
    ):
        raise ValueError("archive_checkpoint_snapshot_invalid")
    snapshot_file = evidence.bind(
        snapshot_path,
        code="archive_checkpoint_snapshot_invalid",
    )
    if _file_contract(snapshot_file) != {
        "bytes": snapshot["bytes"],
        "sha256": snapshot["sha256"],
    }:
        raise ValueError("archive_checkpoint_snapshot_identity_mismatch")
    snapshot_authority = _checkpoint_authority_from_snapshot(
        snapshot_file,
        manifest=manifest,
    )
    if authority != snapshot_authority:
        raise ValueError("archive_checkpoint_snapshot_authority_mismatch")

    hot_surfaces = checkpoint_preimage.get("hot_surfaces")
    if (
        type(hot_surfaces) is not list
        or [item.get("role") for item in hot_surfaces] != list(ROLES)
    ):
        raise ValueError("archive_checkpoint_hot_surfaces_invalid")
    expected_hot_surfaces = [
        {
            "role": item["role"],
            "name": item["raw_name"],
            "bytes": item["raw_bytes"],
            "rows": item["raw_rows"],
            "sha256": item["raw_sha256"],
        }
        for item in manifest["surfaces"]
    ]
    if any(
        type(item) is not dict
        or set(item) != CHECKPOINT_HOT_SURFACE_KEYS
        or type(item.get("name")) is not str
        or not item.get("name")
        or Path(str(item["name"])).name != item["name"]
        or type(item.get("bytes")) is not int
        or type(item.get("rows")) is not int
        or item.get("bytes", -1) < 0
        or item.get("rows", -1) < 0
        or type(item.get("sha256")) is not str
        or not _is_sha256(item.get("sha256"))
        for item in hot_surfaces
    ) or hot_surfaces != expected_hot_surfaces:
        raise ValueError("archive_checkpoint_hot_surfaces_mismatch")

    checkpoint_root_sha256 = checkpoint_preimage.get(
        "checkpoint_root_sha256"
    )
    prior_checkpoint_chain_root_sha256 = checkpoint_preimage.get(
        "prior_checkpoint_chain_root_sha256"
    )
    if (
        checkpoint_preimage.get("schema") != CHECKPOINT_PREIMAGE_SCHEMA
        or checkpoint_preimage.get("segment_id") != manifest.get("segment_id")
        or checkpoint_preimage.get("segment_index")
        != manifest.get("segment_index")
        or checkpoint_preimage.get("start_day") != manifest.get("start_day")
        or checkpoint_preimage.get("end_day") != manifest.get("end_day")
        or checkpoint_preimage.get("completed_day") != manifest.get("end_day")
        or checkpoint_preimage.get("output_prefix")
        != manifest.get("output_prefix")
        or not _is_sha256(checkpoint_root_sha256)
        or checkpoint_root_sha256
        != self_root(checkpoint_preimage, "checkpoint_root_sha256")
        or checkpoint_root_sha256 != manifest.get("checkpoint_root_sha256")
        or not _is_sha256(prior_checkpoint_chain_root_sha256)
        or prior_checkpoint_chain_root_sha256
        != manifest.get("prior_checkpoint_chain_root_sha256")
        or (
            expected_prior_checkpoint_chain_root_sha256 is not None
            and prior_checkpoint_chain_root_sha256
            != expected_prior_checkpoint_chain_root_sha256
        )
    ):
        raise ValueError("archive_checkpoint_preimage_mismatch")

    checkpoint_chain_core = {
        "schema": CHECKPOINT_CHAIN_LINK_SCHEMA,
        "segment_id": manifest["segment_id"],
        "segment_index": manifest["segment_index"],
        "checkpoint_preimage_sha256": checkpoint_preimage_contract["sha256"],
        "checkpoint_root_sha256": checkpoint_root_sha256,
        "prior_checkpoint_chain_root_sha256": (
            prior_checkpoint_chain_root_sha256
        ),
    }
    checkpoint_chain_root_sha256 = root(checkpoint_chain_core)
    if checkpoint_chain_root_sha256 != manifest.get(
        "checkpoint_chain_root_sha256"
    ):
        raise ValueError("archive_checkpoint_chain_link_mismatch")
    checkpoint_entry = {
        "segment_id": manifest["segment_id"],
        "segment_index": manifest["segment_index"],
        "checkpoint_preimage_path": str(checkpoint_preimage_path),
        "checkpoint_preimage_sha256": checkpoint_preimage_contract["sha256"],
        "checkpoint_root_sha256": checkpoint_root_sha256,
        "prior_checkpoint_chain_root_sha256": (
            prior_checkpoint_chain_root_sha256
        ),
        "checkpoint_chain_root_sha256": checkpoint_chain_root_sha256,
    }
    return {
        "authority": authority,
        "entry": checkpoint_entry,
        "pre_archive_partial_summary": {
            "segment_id": manifest["segment_id"],
            "segment_index": manifest["segment_index"],
            "completed_day": manifest["end_day"],
            **snapshot,
            "checkpoint_root_sha256": checkpoint_root_sha256,
            "checkpoint_chain_root_sha256": checkpoint_chain_root_sha256,
        },
    }


def _decompressed_lines(
    bound: BoundRegularFile,
) -> Iterator[bytes]:
    try:
        os.lseek(bound.descriptor, 0, os.SEEK_SET)
        process = subprocess.Popen(
            ["zstd", "-q", "-d", "-c"],
            stdin=bound.descriptor,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError:
        raise ValueError("archive_decompression_failed") from None
    assert process.stdout is not None
    for raw in process.stdout:
        yield raw
    _stdout, stderr = process.communicate()
    if process.returncode != 0:
        del stderr
        raise ValueError("archive_decompression_failed")
    bound._assert_descriptor_unchanged()


def _receipt_for_verified(
    manifest: Mapping[str, Any],
    verified: list[dict[str, Any]],
    checkpoint: Mapping[str, Any],
) -> dict[str, Any]:
    checkpoint_entry = checkpoint["entry"]
    receipt_core = {
        "schema": RECEIPT_SCHEMA,
        "valid": True,
        "manifest_root_sha256": manifest["manifest_root_sha256"],
        "segment_id": manifest["segment_id"],
        "checkpoint_preimage_sha256": checkpoint_entry[
            "checkpoint_preimage_sha256"
        ],
        "checkpoint_root_sha256": checkpoint_entry["checkpoint_root_sha256"],
        "prior_checkpoint_chain_root_sha256": checkpoint_entry[
            "prior_checkpoint_chain_root_sha256"
        ],
        "checkpoint_chain_root_sha256": checkpoint_entry[
            "checkpoint_chain_root_sha256"
        ],
        "surface_count": len(verified),
        "surface_set_root_sha256": root(verified),
        "persisted_bytes_consumed": True,
        "writer_imported": False,
        "runner_imported": False,
        "economic_values_exposed": False,
    }
    return {**receipt_core, "receipt_root_sha256": root(receipt_core)}


def verify_shard(manifest_path: Path) -> dict[str, Any]:
    lexical_manifest, segment_dir, archive_root = _manifest_topology(
        manifest_path
    )
    with BoundEvidence(archive_root=archive_root) as evidence:
        manifest_file = evidence.bind(
            lexical_manifest,
            code="archive_shard_manifest_invalid",
        )
        manifest = _load_canonical(manifest_file)
        _validate_manifest(
            manifest,
            manifest_path=lexical_manifest,
            segment_dir=segment_dir,
        )
        checkpoint = _verify_checkpoint(
            evidence=evidence,
            manifest=manifest,
            segment_dir=segment_dir,
        )
        start_day = date.fromisoformat(manifest["start_day"])
        end_day = date.fromisoformat(manifest["end_day"])
        verified = []
        for item in manifest["surfaces"]:
            compressed = evidence.bind(
                Path(str(item["compressed_path"])),
                code="archive_compressed_identity_mismatch",
            )
            compressed_contract = _file_contract(compressed)
            if compressed_contract != {
                "bytes": item["compressed_bytes"],
                "sha256": item["compressed_sha256"],
            }:
                raise ValueError("archive_compressed_identity_mismatch")
            digest = hashlib.sha256()
            size = 0
            rows = 0
            final = b""
            for raw in _decompressed_lines(compressed):
                _validate_partition_row(
                    raw,
                    role=str(item["role"]),
                    start_day=start_day,
                    end_day=end_day,
                )
                digest.update(raw)
                size += len(raw)
                rows += raw.count(b"\n")
                final = raw[-1:]
            if size and final != b"\n":
                raise ValueError("archive_decompressed_framing_mismatch")
            raw_contract = {
                "bytes": size,
                "rows": rows,
                "sha256": digest.hexdigest(),
            }
            if raw_contract != {
                "bytes": item["raw_bytes"],
                "rows": item["raw_rows"],
                "sha256": item["raw_sha256"],
            }:
                raise ValueError("archive_reconstructed_identity_mismatch")
            verified.append(
                {
                    "role": item["role"],
                    **raw_contract,
                    "compressed_sha256": compressed_contract["sha256"],
                }
            )
        evidence.assert_paths_unchanged()
        return _receipt_for_verified(manifest, verified, checkpoint)


def _walk_campaign(
    campaign_manifest_path: Path,
    *,
    line_roles: frozenset[str],
) -> Iterator[tuple[str, bytes]]:
    campaign_path, archive_root = _campaign_path(campaign_manifest_path)
    with BoundEvidence(archive_root=archive_root) as evidence:
        campaign_file = evidence.bind(
            campaign_path,
            code="archive_campaign_manifest_invalid",
        )
        campaign_raw = campaign_file.read_bytes()
        try:
            campaign = json.loads(campaign_raw)
        except (UnicodeError, json.JSONDecodeError):
            raise ValueError("archive_artifact_not_canonical") from None
        if (
            type(campaign) is not dict
            or set(campaign) != CAMPAIGN_MANIFEST_KEYS
            or campaign_raw != canonical_bytes(campaign) + b"\n"
            or campaign.get("schema") != CAMPAIGN_SCHEMA
            or campaign.get("campaign_manifest_root_sha256")
            != self_root(campaign, "campaign_manifest_root_sha256")
            or type(campaign.get("exact_concatenation_reconstruction"))
            is not bool
            or campaign.get("exact_concatenation_reconstruction") is not True
            or type(campaign.get("writer_retains_economic_values")) is not bool
            or campaign.get("writer_retains_economic_values") is not False
            or type(campaign.get("live_broker_authority")) is not bool
            or campaign.get("live_broker_authority") is not False
        ):
            raise ValueError("archive_campaign_manifest_invalid")
        shards = campaign.get("shards")
        output_prefix = str(campaign.get("output_prefix") or "")
        hot_tombstones = campaign.get("hot_tombstones")
        if (
            not isinstance(shards, list)
            or not shards
            or not output_prefix
            or campaign.get("hot_roles") != list(ROLES)
            or not isinstance(hot_tombstones, list)
            or [item.get("role") for item in hot_tombstones] != list(ROLES)
            or any(
                set(item) != {"role", "name", "bytes", "rows", "sha256"}
                or not str(item.get("name") or "")
                or item.get("bytes") != 0
                or item.get("rows") != 0
                or item.get("sha256") != EMPTY_SHA256
                for item in hot_tombstones
            )
        ):
            raise ValueError("archive_campaign_shards_invalid")
        hot_tombstones_by_role = {
            str(item["role"]): item for item in hot_tombstones
        }
        checkpoint_authority = _validate_checkpoint_authority(
            campaign.get("checkpoint_authority"),
            output_prefix=output_prefix,
        )
        checkpoint_chain_genesis_root_sha256 = root(
            {
                "schema": CHECKPOINT_CHAIN_GENESIS_SCHEMA,
                "checkpoint_authority": checkpoint_authority,
            }
        )
        checkpoint_chain = campaign.get("checkpoint_chain")
        if (
            campaign.get("checkpoint_chain_genesis_root_sha256")
            != checkpoint_chain_genesis_root_sha256
            or type(checkpoint_chain) is not list
            or len(checkpoint_chain) != len(shards)
            or any(
                type(item) is not dict
                or set(item) != CHECKPOINT_CHAIN_ENTRY_KEYS
                for item in checkpoint_chain
            )
            or campaign.get("checkpoint_chain_set_root_sha256")
            != root(checkpoint_chain)
            or not _is_sha256(
                campaign.get("terminal_checkpoint_chain_root_sha256")
            )
        ):
            raise ValueError("archive_campaign_checkpoint_chain_invalid")

        shard_data: list[dict[str, Any]] = []
        previous_end: date | None = None
        prior_checkpoint_chain_root_sha256 = (
            checkpoint_chain_genesis_root_sha256
        )
        for expected_index, shard in enumerate(shards, start=1):
            if not isinstance(shard, Mapping):
                raise ValueError("archive_campaign_shards_invalid")
            try:
                start_day = date.fromisoformat(str(shard.get("start_day")))
                end_day = date.fromisoformat(str(shard.get("end_day")))
            except ValueError:
                raise ValueError(
                    "archive_campaign_entry_manifest_metadata_mismatch"
                ) from None
            expected_segment_id = (
                f"{expected_index:03d}_{start_day.isoformat()}_"
                f"{end_day.isoformat()}"
            )
            segment_dir = archive_root / "shards" / expected_segment_id
            manifest_path = segment_dir / "SHARD_MANIFEST.json"
            receipt_path = segment_dir / "VERIFY_RECEIPT.json"
            supplied_manifest_path = Path(
                str(shard.get("manifest_path") or "")
            )
            supplied_receipt_path = Path(
                str(shard.get("receipt_path") or "")
            )
            if (
                not supplied_manifest_path.is_absolute()
                or not supplied_receipt_path.is_absolute()
                or _lexical_path(supplied_manifest_path) != manifest_path
                or _lexical_path(supplied_receipt_path) != receipt_path
                or start_day > end_day
            ):
                raise ValueError("archive_campaign_entry_topology_mismatch")
            if shard.get("segment_id") != expected_segment_id:
                raise ValueError(
                    "archive_campaign_entry_manifest_metadata_mismatch"
                )
            if previous_end is not None:
                if start_day <= previous_end:
                    raise ValueError("archive_campaign_order_invalid")
                if start_day != previous_end + timedelta(days=1):
                    raise ValueError("archive_campaign_calendar_gap")
            previous_end = end_day
            manifest_file = evidence.bind(
                manifest_path,
                code="archive_shard_manifest_invalid",
            )
            receipt_file = evidence.bind(
                receipt_path,
                code="archive_shard_receipt_mismatch",
            )
            manifest = _load_canonical(manifest_file)
            stored_receipt = _load_canonical(receipt_file)
            _validate_manifest(
                manifest,
                manifest_path=manifest_path,
                segment_dir=segment_dir,
            )
            checkpoint = _verify_checkpoint(
                evidence=evidence,
                manifest=manifest,
                segment_dir=segment_dir,
                expected_authority=checkpoint_authority,
                expected_prior_checkpoint_chain_root_sha256=(
                    prior_checkpoint_chain_root_sha256
                ),
            )
            checkpoint_entry = checkpoint["entry"]
            if (
                checkpoint_entry != checkpoint_chain[expected_index - 1]
                or any(
                    shard.get(key) != checkpoint_entry[key]
                    for key in CHECKPOINT_CHAIN_ENTRY_KEYS
                )
                or manifest.get("segment_id") != shard.get("segment_id")
                or manifest.get("segment_index") != expected_index
                or manifest.get("start_day") != shard.get("start_day")
                or manifest.get("end_day") != shard.get("end_day")
                or manifest.get("output_prefix") != output_prefix
                or manifest.get("manifest_root_sha256")
                != shard.get("manifest_root_sha256")
                or stored_receipt.get("receipt_root_sha256")
                != shard.get("receipt_root_sha256")
                or stored_receipt.get("receipt_root_sha256")
                != self_root(stored_receipt, "receipt_root_sha256")
            ):
                raise ValueError(
                    "archive_campaign_entry_manifest_metadata_mismatch"
                )
            prior_checkpoint_chain_root_sha256 = checkpoint_entry[
                "checkpoint_chain_root_sha256"
            ]
            compressed_files: dict[str, BoundRegularFile] = {}
            surfaces: dict[str, Mapping[str, Any]] = {}
            for item in manifest["surfaces"]:
                role = str(item["role"])
                if item.get("raw_name") != hot_tombstones_by_role[role]["name"]:
                    raise ValueError("archive_campaign_hot_tombstone_mismatch")
                compressed_files[role] = evidence.bind(
                    Path(str(item["compressed_path"])),
                    code="archive_compressed_identity_mismatch",
                )
                surfaces[role] = item
            shard_data.append(
                {
                    "start_day": start_day,
                    "end_day": end_day,
                    "manifest": manifest,
                    "stored_receipt": stored_receipt,
                    "checkpoint": checkpoint,
                    "compressed_files": compressed_files,
                    "surfaces": surfaces,
                }
            )

        if campaign.get("terminal_checkpoint_chain_root_sha256") != (
            prior_checkpoint_chain_root_sha256
        ):
            raise ValueError("archive_campaign_checkpoint_chain_invalid")

        cumulative_hashes = {role: hashlib.sha256() for role in ROLES}
        cumulative_bytes = {role: 0 for role in ROLES}
        cumulative_rows = {role: 0 for role in ROLES}
        verified_by_shard: list[dict[str, dict[str, Any]]] = [
            {} for _item in shard_data
        ]
        role_chains: dict[str, list[str]] = {role: [] for role in ROLES}
        total_raw_bytes = 0
        total_compressed_bytes = 0
        for role in ROLES:
            for shard_index, data in enumerate(shard_data):
                item = data["surfaces"][role]
                compressed = data["compressed_files"][role]
                compressed_contract = _file_contract(compressed)
                if compressed_contract != {
                    "bytes": item["compressed_bytes"],
                    "sha256": item["compressed_sha256"],
                }:
                    raise ValueError("archive_compressed_identity_mismatch")
                raw_digest = hashlib.sha256()
                raw_bytes = 0
                raw_rows = 0
                final = b""
                for raw in _decompressed_lines(compressed):
                    _validate_partition_row(
                        raw,
                        role=role,
                        start_day=data["start_day"],
                        end_day=data["end_day"],
                    )
                    raw_digest.update(raw)
                    cumulative_hashes[role].update(raw)
                    raw_bytes += len(raw)
                    raw_rows += raw.count(b"\n")
                    final = raw[-1:]
                    if role in line_roles:
                        yield role, raw
                if raw_bytes and final != b"\n":
                    raise ValueError("archive_decompressed_framing_mismatch")
                raw_contract = {
                    "bytes": raw_bytes,
                    "rows": raw_rows,
                    "sha256": raw_digest.hexdigest(),
                }
                if raw_contract != {
                    "bytes": item["raw_bytes"],
                    "rows": item["raw_rows"],
                    "sha256": item["raw_sha256"],
                }:
                    raise ValueError("archive_reconstructed_identity_mismatch")
                verified_by_shard[shard_index][role] = {
                    "role": role,
                    **raw_contract,
                    "compressed_sha256": compressed_contract["sha256"],
                }
                role_chains[role].append(str(item["raw_sha256"]))
                cumulative_bytes[role] += raw_bytes
                cumulative_rows[role] += raw_rows
                total_raw_bytes += raw_bytes
                total_compressed_bytes += compressed_contract["bytes"]

        verified_roots = []
        verified_role_partitions: list[dict[str, Any]] = []
        row_offsets = {role: 0 for role in ROLES}
        for shard_index, data in enumerate(shard_data):
            manifest = data["manifest"]
            verified = [verified_by_shard[shard_index][role] for role in ROLES]
            receipt = _receipt_for_verified(
                manifest,
                verified,
                data["checkpoint"],
            )
            if receipt != data["stored_receipt"]:
                raise ValueError("archive_shard_receipt_mismatch")
            verified_roots.append(receipt["receipt_root_sha256"])
            for role in ROLES:
                raw_contract = verified_by_shard[shard_index][role]
                row_start_offset = row_offsets[role]
                row_offsets[role] += int(raw_contract["rows"])
                verified_role_partitions.append(
                    {
                        "role": role,
                        "segment_id": str(manifest["segment_id"]),
                        "start_day": data["start_day"].isoformat(),
                        "end_day": data["end_day"].isoformat(),
                        "row_start_offset": row_start_offset,
                        "row_end_offset_exclusive": row_offsets[role],
                        "rows": raw_contract["rows"],
                        "sha256": raw_contract["sha256"],
                    }
                )
        cumulative_surfaces = [
            {
                "role": role,
                "bytes": cumulative_bytes[role],
                "rows": cumulative_rows[role],
                "sha256": cumulative_hashes[role].hexdigest(),
            }
            for role in ROLES
        ]
        if campaign.get("cumulative_surfaces") != cumulative_surfaces:
            raise ValueError("archive_campaign_cumulative_surface_mismatch")
        evidence.assert_paths_unchanged()
        report_core = {
            "schema": "gtos.replay_acceleration.streaming_proof_campaign_verification.v1",
            "valid": True,
            "campaign_manifest_path": str(campaign_path),
            "campaign_manifest_sha256": hashlib.sha256(
                campaign_raw
            ).hexdigest(),
            "campaign_manifest_root_sha256": campaign[
                "campaign_manifest_root_sha256"
            ],
            "checkpoint_authority": checkpoint_authority,
            "checkpoint_chain_genesis_root_sha256": (
                checkpoint_chain_genesis_root_sha256
            ),
            "checkpoint_chain": checkpoint_chain,
            "checkpoint_chain_set_root_sha256": campaign[
                "checkpoint_chain_set_root_sha256"
            ],
            "terminal_checkpoint_chain_root_sha256": campaign[
                "terminal_checkpoint_chain_root_sha256"
            ],
            "terminal_pre_archive_partial_summary": shard_data[-1][
                "checkpoint"
            ]["pre_archive_partial_summary"],
            "shard_count": len(shards),
            "verified_shard_receipt_set_root_sha256": root(verified_roots),
            "role_reconstruction_chain_roots_sha256": {
                role: root(values)
                for role, values in sorted(role_chains.items())
            },
            "cumulative_surfaces": cumulative_surfaces,
            "hot_tombstones": hot_tombstones,
            "hot_tombstone_set_root_sha256": root(hot_tombstones),
            "verified_role_partitions": verified_role_partitions,
            "verified_role_partitions_root_sha256": root(
                verified_role_partitions
            ),
            "total_raw_bytes": total_raw_bytes,
            "total_compressed_bytes": total_compressed_bytes,
            "writer_imported": False,
            "runner_imported": False,
            "economic_values_exposed": False,
        }
        return {**report_core, "verification_root_sha256": root(report_core)}


def _consume_campaign(
    walker: Iterator[tuple[str, bytes]],
    *,
    consumer: Callable[[str, bytes], None] | None,
) -> dict[str, Any]:
    while True:
        try:
            role, raw = next(walker)
        except StopIteration as completed:
            report = completed.value
            if not isinstance(report, dict):
                raise ValueError("archive_campaign_verification_incomplete")
            return report
        if consumer is not None:
            consumer(role, raw)


def verify_campaign(campaign_manifest_path: Path) -> dict[str, Any]:
    return _consume_campaign(
        _walk_campaign(campaign_manifest_path, line_roles=frozenset()),
        consumer=None,
    )


def verify_campaign_with_role_line_consumer(
    campaign_manifest_path: Path,
    *,
    roles: tuple[str, ...],
    consumer: Callable[[str, bytes], None],
) -> dict[str, Any]:
    requested_roles = tuple(str(role) for role in roles)
    if (
        not requested_roles
        or len(set(requested_roles)) != len(requested_roles)
        or any(role not in ROLES for role in requested_roles)
    ):
        raise ValueError("archive_campaign_role_invalid")
    return _consume_campaign(
        _walk_campaign(
            campaign_manifest_path,
            line_roles=frozenset(requested_roles),
        ),
        consumer=consumer,
    )


def iter_campaign_roles_lines(
    campaign_manifest_path: Path,
    roles: tuple[str, ...],
) -> Iterator[tuple[str, bytes]]:
    requested_roles = tuple(str(role) for role in roles)
    if (
        not requested_roles
        or len(set(requested_roles)) != len(requested_roles)
        or any(role not in ROLES for role in requested_roles)
    ):
        raise ValueError("archive_campaign_role_invalid")
    yield from _walk_campaign(
        campaign_manifest_path,
        line_roles=frozenset(requested_roles),
    )


def iter_campaign_role_lines(
    campaign_manifest_path: Path,
    role: str,
) -> Iterator[bytes]:
    requested_role = str(role)
    for observed_role, raw in iter_campaign_roles_lines(
        campaign_manifest_path,
        (requested_role,),
    ):
        if observed_role == requested_role:
            yield raw


def atomic_write(path: Path, value: Mapping[str, Any]) -> None:
    path = _lexical_path(path)
    if _path_has_symlink_component(path):
        raise ValueError("archive_symlink_component_forbidden")
    if path.exists() or path.is_symlink():
        raise ValueError("archive_verification_output_must_be_new")
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    descriptor = os.open(
        temporary,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
        0o600,
    )
    try:
        payload = canonical_bytes(value) + b"\n"
        offset = 0
        while offset < len(payload):
            written = os.write(descriptor, payload[offset:])
            if written <= 0:
                raise ValueError("archive_verification_output_write_failed")
            offset += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    shard = subparsers.add_parser("verify-shard")
    shard.add_argument("--manifest", type=Path, required=True)
    shard.add_argument("--output", type=Path, required=True)
    campaign = subparsers.add_parser("verify-campaign")
    campaign.add_argument("--manifest", type=Path, required=True)
    campaign.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = (
        verify_shard(args.manifest)
        if args.command == "verify-shard"
        else verify_campaign(args.manifest)
    )
    atomic_write(args.output, report)
    print(
        canonical_bytes(
            {
                "valid": True,
                "verification_root_sha256": report.get(
                    "verification_root_sha256"
                )
                or report.get("receipt_root_sha256"),
                "economic_values_exposed": False,
            }
        ).decode("ascii")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
