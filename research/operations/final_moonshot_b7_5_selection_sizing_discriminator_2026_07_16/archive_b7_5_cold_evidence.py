#!/usr/bin/env python3
"""Transactionally demote immutable B7.5 JSONL ledgers to cold zstd shards.

Dry-run is the default.  ``--apply`` requires a new operation manifest path.
The apply path is fail closed:

* every source is exclusively advisory-locked, semantically validated, and
  hashed before work;
* shards contain whole JSONL lines and are at most 256 MiB uncompressed;
* each shard and the exact logical concatenation are independently verified by
  byte identity after that one full JSON-object validation;
* every source is re-hashed under its lock immediately before rename;
* an owned directory guard occupies each removed raw pathname until archive
  verification and backup disposition finish, blocking path-based recreation;
* originals are renamed to backups and retained until all final archives and
  manifests have passed a second verification;
* any pre-verification failure restores all original raw paths.

The resulting layout is consumed by :mod:`b7_5_cold_evidence` without full
materialization.
"""

from __future__ import annotations

import argparse
import copy
from contextlib import contextmanager
import fcntl
import hashlib
import io
import json
import os
import shutil
import stat
import subprocess
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, BinaryIO, Iterable, Iterator, Mapping, Sequence

from b7_5_cold_evidence import (
    ARCHIVE_PASS_STATUS,
    ARCHIVE_SCHEMA,
    DEFAULT_SHARD_MAX_BYTES,
    MANIFEST_FILENAME,
    ColdConcatReader,
    ColdEvidenceError,
    canonical_json_bytes,
    cold_archive_dir,
    scan_jsonl_binary_stream,
    seal_manifest,
    sha256_file,
    verify_archive_structure,
    verify_manifest_self_hash,
)


OPERATION_SCHEMA = "gtos.b7_5.cold_jsonl_demotion_operation.v1"
OPERATION_PASS = "PASS_COLD_DEMOTION_LOGICAL_BYTES_PRESERVED"
MIN_SHARD_BYTES = 4 * 1024
DEFAULT_MIN_FREE_RESERVE_BYTES = 8 * 1024 * 1024 * 1024
HASH_CHUNK_BYTES = 16 * 1024 * 1024
SOURCE_LINE_BUFFER_BYTES = 1024 * 1024
BYTE_IDENTITY_KEYS = ("logical_bytes", "sha256")
SEMANTIC_IDENTITY_KEYS = (
    "physical_line_count",
    "json_object_row_count",
    "blank_line_count",
    "ends_with_lf",
)
LOGICAL_IDENTITY_KEYS = BYTE_IDENTITY_KEYS + SEMANTIC_IDENTITY_KEYS


class DemotionRefusal(ColdEvidenceError):
    """Raised when a cold-demotion safety invariant is not satisfied."""


@dataclass
class SourceState:
    path: Path
    handle: BinaryIO
    initial_fstat: os.stat_result
    plan: dict[str, Any]
    archive_dir: Path
    staging_dir: Path
    backup_path: Path
    entry: dict[str, Any]
    source_renamed: bool = False
    archive_promoted: bool = False
    backup_deleted: bool = False
    path_guard_created: bool = False
    path_guard_identity: tuple[int, int] | None = None


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _fsync_file(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    seal_manifest(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        _fsync_directory(path.parent)
    finally:
        if temporary.exists():
            temporary.unlink()


def _git_head(repo_root: Path) -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def _source_identity(observed: os.stat_result) -> tuple[int, int, int, int, int]:
    return (
        int(observed.st_dev),
        int(observed.st_ino),
        int(observed.st_size),
        int(observed.st_mtime_ns),
        int(observed.st_nlink),
    )


def _source_metadata(observed: os.stat_result) -> dict[str, Any]:
    return {
        "device": int(observed.st_dev),
        "inode": int(observed.st_ino),
        "mode": stat.S_IMODE(observed.st_mode),
        "uid": int(observed.st_uid),
        "gid": int(observed.st_gid),
        "link_count": int(observed.st_nlink),
        "mtime_ns": int(observed.st_mtime_ns),
        "logical_bytes": int(observed.st_size),
        "physical_bytes": int(getattr(observed, "st_blocks", 0)) * 512,
    }


def _assert_source_path(path: Path, allowed_root: Path) -> os.stat_result:
    lexical = Path(os.path.abspath(path))
    if lexical.is_symlink():
        raise DemotionRefusal(f"source_symlink_forbidden:{lexical}")
    try:
        lexical.relative_to(allowed_root)
    except ValueError as exc:
        raise DemotionRefusal(
            f"source_escapes_allowed_root:{lexical}:root={allowed_root}"
        ) from exc
    try:
        resolved_parent = lexical.parent.resolve(strict=True)
        resolved_parent.relative_to(allowed_root)
    except (OSError, ValueError) as exc:
        raise DemotionRefusal(
            f"source_parent_escapes_allowed_root:{lexical}:root={allowed_root}"
        ) from exc
    try:
        observed = lexical.stat()
    except OSError as exc:
        raise DemotionRefusal(f"source_unavailable:{lexical}:{exc}") from exc
    if not stat.S_ISREG(observed.st_mode):
        raise DemotionRefusal(f"source_not_regular_file:{lexical}")
    if observed.st_nlink != 1:
        raise DemotionRefusal(
            f"source_hardlink_forbidden:{lexical}:nlink={observed.st_nlink}"
        )
    if observed.st_size <= 0:
        raise DemotionRefusal(f"source_empty_forbidden:{lexical}")
    return observed


def _lock_source(path: Path, allowed_root: Path) -> tuple[BinaryIO, os.stat_result]:
    path_stat = _assert_source_path(path, allowed_root)
    handle = path.open("rb", buffering=0)
    try:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise DemotionRefusal(f"source_exclusive_lock_unavailable:{path}:{exc}") from exc
        descriptor_stat = os.fstat(handle.fileno())
        if _source_identity(descriptor_stat) != _source_identity(path_stat):
            raise DemotionRefusal(f"source_identity_changed_while_locking:{path}")
        return handle, descriptor_stat
    except BaseException:
        handle.close()
        raise


@contextmanager
def _buffered_locked_line_reader(
    handle: BinaryIO,
) -> Iterator[io.BufferedReader]:
    """Temporarily buffer line reads without surrendering the locked raw fd."""

    handle.seek(0)
    reader = io.BufferedReader(handle, buffer_size=SOURCE_LINE_BUFFER_BYTES)
    try:
        yield reader
    finally:
        # BufferedReader.close() would close the raw descriptor and release its
        # flock.  Detach instead, discard any read-ahead, and make every later
        # raw identity pass start from the descriptor's canonical offset.
        detached = reader.detach()
        if detached is not handle:
            raise DemotionRefusal("buffered_source_detach_identity_mismatch")
        handle.seek(0)


def _byte_identity(values: Mapping[str, Any]) -> dict[str, Any]:
    return {key: values[key] for key in BYTE_IDENTITY_KEYS}


def _logical_identity(values: Mapping[str, Any]) -> dict[str, Any]:
    return {key: values[key] for key in LOGICAL_IDENTITY_KEYS}


def _semantic_identity(values: Mapping[str, Any]) -> dict[str, Any]:
    return {key: values[key] for key in SEMANTIC_IDENTITY_KEYS}


def _scan_binary_identity_stream(handle: BinaryIO) -> dict[str, Any]:
    """Hash a binary stream without invoking line or JSON parsing machinery."""

    digest = hashlib.sha256()
    logical_bytes = 0
    while True:
        chunk = handle.read(HASH_CHUNK_BYTES)
        if not chunk:
            break
        digest.update(chunk)
        logical_bytes += len(chunk)
    return {
        "logical_bytes": logical_bytes,
        "sha256": digest.hexdigest(),
    }


def _scan_locked_source_semantic(handle: BinaryIO) -> dict[str, Any]:
    with _buffered_locked_line_reader(handle) as reader:
        return scan_jsonl_binary_stream(reader, parse_json=True)


def _scan_locked_source_identity(handle: BinaryIO) -> dict[str, Any]:
    handle.seek(0)
    result = _scan_binary_identity_stream(handle)
    handle.seek(0)
    return result


def _zstd_identity(zstd_path: Path) -> dict[str, Any]:
    result = subprocess.run(
        [str(zstd_path), "--version"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise DemotionRefusal(
            f"zstd_version_probe_failed:{zstd_path}:{result.stderr.strip()}"
        )
    return {
        "path": str(zstd_path),
        "sha256": sha256_file(zstd_path),
        "version": result.stdout.strip(),
    }


def _resolve_zstd(value: Path | None) -> Path:
    candidate = str(value) if value is not None else shutil.which("zstd")
    if not candidate:
        raise DemotionRefusal("zstd_binary_not_found")
    path = Path(candidate).resolve(strict=True)
    if path.is_symlink() or not path.is_file():
        raise DemotionRefusal(f"zstd_binary_invalid:{path}")
    return path


def _compress_raw_shard(
    raw_path: Path,
    compressed_path: Path,
    *,
    zstd_path: Path,
    level: int,
) -> None:
    if compressed_path.exists() or compressed_path.is_symlink():
        raise DemotionRefusal(f"compressed_shard_destination_exists:{compressed_path}")
    result = subprocess.run(
        [
            str(zstd_path),
            "-q",
            "--threads=1",
            f"-{level}",
            "--check",
            str(raw_path),
            "-o",
            str(compressed_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise DemotionRefusal(
            f"zstd_compression_failed:{raw_path}:exit={result.returncode}:"
            f"stderr={result.stderr.strip()}"
        )
    _fsync_file(compressed_path)


def _scan_compressed_shard(
    compressed_path: Path,
    *,
    zstd_path: Path,
) -> dict[str, Any]:
    process = subprocess.Popen(
        [str(zstd_path), "-q", "-d", "-c", str(compressed_path)],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if process.stdout is None or process.stderr is None:
        process.kill()
        process.wait()
        raise DemotionRefusal("zstd_decompression_pipe_unavailable")
    try:
        observed = _scan_binary_identity_stream(process.stdout)
        process.stdout.close()
        error = process.stderr.read()
        returncode = process.wait()
    finally:
        process.stderr.close()
        if process.poll() is None:
            process.kill()
            process.wait()
    if returncode != 0:
        raise DemotionRefusal(
            f"zstd_decompression_failed:{compressed_path}:exit={returncode}:"
            f"stderr={error.decode('utf-8', errors='replace').strip()}"
        )
    return observed


def _assert_disk_reserve(
    path: Path,
    *,
    shard_max_bytes: int,
    minimum_free_reserve_bytes: int,
) -> dict[str, int]:
    usage = shutil.disk_usage(path)
    worst_case_working_bytes = 2 * shard_max_bytes
    required = minimum_free_reserve_bytes + worst_case_working_bytes
    if usage.free < required:
        raise DemotionRefusal(
            f"cold_demotion_disk_reserve_insufficient:{path}:"
            f"free={usage.free}:required={required}:"
            f"reserve={minimum_free_reserve_bytes}:working={worst_case_working_bytes}"
        )
    return {
        "free_bytes_observed": int(usage.free),
        "minimum_free_reserve_bytes": minimum_free_reserve_bytes,
        "worst_case_per_shard_working_bytes": worst_case_working_bytes,
        "required_free_bytes": required,
    }


def _build_archive_from_reader(
    state: SourceState,
    source_handle: BinaryIO,
    *,
    zstd_path: Path,
    zstd_identity: Mapping[str, Any],
    level: int,
    shard_max_bytes: int,
    minimum_free_reserve_bytes: int,
) -> dict[str, Any]:
    source = state.path
    staging = state.staging_dir
    if staging.exists() or staging.is_symlink():
        raise DemotionRefusal(f"cold_staging_path_exists:{staging}")
    staging.mkdir(mode=0o755)
    _fsync_directory(staging.parent)

    source_digest = hashlib.sha256()
    source_bytes = 0
    source_lines = 0
    source_rows = 0
    source_blanks = 0
    source_ends_lf = False
    logical_offset = 0
    pending_line: bytes | None = None
    shards: list[dict[str, Any]] = []

    while True:
        disk_reserve = _assert_disk_reserve(
            staging,
            shard_max_bytes=shard_max_bytes,
            minimum_free_reserve_bytes=minimum_free_reserve_bytes,
        )
        index = len(shards)
        raw_path = staging / f".part-{index:06d}.jsonl.raw.tmp"
        compressed_path = staging / f"part-{index:06d}.jsonl.zst"
        shard_digest = hashlib.sha256()
        shard_bytes = 0
        shard_lines = 0
        shard_rows = 0
        shard_blanks = 0
        shard_ends_lf = False
        first_line = source_lines + 1

        with raw_path.open("xb") as raw_handle:
            while True:
                line = pending_line
                if line is None:
                    line = source_handle.readline(shard_max_bytes + 1)
                pending_line = None
                if not line:
                    break
                if len(line) > shard_max_bytes:
                    raise DemotionRefusal(
                        f"source_line_exceeds_shard_limit:{source}:"
                        f"line={source_lines + 1}:bytes>{shard_max_bytes}"
                    )
                if shard_bytes and shard_bytes + len(line) > shard_max_bytes:
                    pending_line = line
                    break
                # The initial locked pass has already validated every nonblank
                # line as a JSON object.  From here onward the transaction uses
                # exact bytes, hashes, row/blank counts, and newline state to
                # prove identity without repeatedly decoding multi-GiB JSON.
                is_row = bool(line.strip())
                raw_handle.write(line)
                shard_digest.update(line)
                source_digest.update(line)
                shard_bytes += len(line)
                source_bytes += len(line)
                shard_lines += 1
                source_lines += 1
                shard_rows += int(is_row)
                source_rows += int(is_row)
                shard_blanks += int(not is_row)
                source_blanks += int(not is_row)
                shard_ends_lf = line.endswith(b"\n")
                source_ends_lf = shard_ends_lf
            raw_handle.flush()
            os.fsync(raw_handle.fileno())

        if shard_bytes == 0:
            raw_path.unlink()
            break
        if pending_line is not None and not shard_ends_lf:
            raise DemotionRefusal(f"line_safe_shard_boundary_without_lf:{source}:{index}")

        _compress_raw_shard(
            raw_path,
            compressed_path,
            zstd_path=zstd_path,
            level=level,
        )
        compressed_stat = compressed_path.stat()
        observed = _scan_compressed_shard(
            compressed_path,
            zstd_path=zstd_path,
        )
        expected_observed = {
            "logical_bytes": shard_bytes,
            "sha256": shard_digest.hexdigest(),
        }
        if observed != expected_observed:
            raise DemotionRefusal(
                f"compressed_shard_logical_mismatch:{source}:{index}:"
                f"expected={expected_observed}:actual={observed}"
            )
        raw_path.unlink()
        shard = {
            "index": index,
            "name": compressed_path.name,
            "logical_start_offset": logical_offset,
            "logical_end_offset_exclusive": logical_offset + shard_bytes,
            "uncompressed_bytes": shard_bytes,
            "uncompressed_sha256": shard_digest.hexdigest(),
            "compressed_bytes": int(compressed_stat.st_size),
            "compressed_sha256": sha256_file(compressed_path),
            "first_physical_line_number": first_line,
            "last_physical_line_number": source_lines,
            "physical_line_count": shard_lines,
            "json_object_row_count": shard_rows,
            "blank_line_count": shard_blanks,
            "ends_with_lf": shard_ends_lf,
            "disk_reserve_before_shard": disk_reserve,
        }
        shards.append(shard)
        logical_offset += shard_bytes

    built = {
        "logical_bytes": source_bytes,
        "sha256": source_digest.hexdigest(),
        "physical_line_count": source_lines,
        "json_object_row_count": source_rows,
        "blank_line_count": source_blanks,
        "ends_with_lf": source_ends_lf,
    }
    for key, expected in state.plan.items():
        if key in built and built[key] != expected:
            raise DemotionRefusal(
                f"source_changed_between_plan_and_archive:{source}:{key}:"
                f"expected={expected}:actual={built[key]}"
            )

    manifest = {
        "schema": ARCHIVE_SCHEMA,
        "status": ARCHIVE_PASS_STATUS,
        "generated_at_utc": _utc_now(),
        "logical_source": {
            "name": source.name,
            **built,
            "source_metadata_before_demotion": _source_metadata(state.initial_fstat),
        },
        "archive_layout": {
            "manifest_filename": MANIFEST_FILENAME,
            "codec": "zstd",
            "line_safe": True,
            "concatenation_order": "ascending_shard_index",
            "shard_uncompressed_max_bytes": shard_max_bytes,
            "shard_count": len(shards),
            "compression_level": level,
            "frame_checksum": True,
            "zstd_threads": 1,
            "zstd_binary": copy.deepcopy(dict(zstd_identity)),
            "compression_command": [
                "<zstd>",
                "-q",
                "--threads=1",
                f"-{level}",
                "--check",
                "<raw_line_safe_shard>",
                "-o",
                "<compressed_shard>",
            ],
        },
        "shards": shards,
        "verification": {
            "initial_source_full_json_object_validation_required": True,
            "post_validation_reverification_by_exact_byte_identity_required": True,
            "post_validation_identity_reverification_uses_bounded_binary_chunks": True,
            "line_row_blank_and_terminal_lf_metadata_inherited_after_exact_byte_identity": True,
            "each_compressed_shard_reopened_and_fully_decompressed": True,
            "each_uncompressed_shard_sha256_matched": True,
            "each_compressed_shard_sha256_recorded": True,
            "each_shard_decompressor_eof_exact": True,
            "exact_concatenated_sha256_required": True,
            "exact_concatenated_bytes_rows_and_newline_required": True,
            "source_rehashed_under_exclusive_lock_before_demotion": True,
            "original_backup_retained_until_final_archive_reverification": True,
        },
        "safety_boundary": {
            "broker_runtime_change_status": False,
            "live_activation_status": False,
            "march_outcome_access_status": False,
        },
    }
    _write_json_atomic(staging / MANIFEST_FILENAME, manifest)
    verified = verify_archive_structure(
        staging / MANIFEST_FILENAME,
        expected_logical_path=source,
        require_canonical_location=False,
        verify_compressed_hashes=True,
    )
    with io.BufferedReader(
        ColdConcatReader(verified, zstd_path=zstd_path),
        buffer_size=1024 * 1024,
    ) as logical_handle:
        concatenated_identity = _scan_binary_identity_stream(logical_handle)
    if concatenated_identity != _byte_identity(built):
        raise DemotionRefusal(
            f"staged_archive_concatenation_mismatch:{source}:"
            f"expected={_byte_identity(built)}:actual={concatenated_identity}"
        )
    state.entry["staged_archive"] = {
        "manifest_path": str(staging / MANIFEST_FILENAME),
        "manifest_file_sha256": sha256_file(staging / MANIFEST_FILENAME),
        "manifest_self_hash_sha256": verify_manifest_self_hash(manifest),
        "shard_count": len(shards),
        "compressed_bytes": sum(shard["compressed_bytes"] for shard in shards),
        "identity_reverification": concatenated_identity,
        "logical_reverification": _logical_identity(built),
        "semantic_metadata_inherited_from_initial_locked_scan": _semantic_identity(
            state.plan
        ),
    }
    state.entry["status"] = "STAGED_ARCHIVE_FULLY_VERIFIED"
    return manifest


def _build_archive(
    state: SourceState,
    *,
    zstd_path: Path,
    zstd_identity: Mapping[str, Any],
    level: int,
    shard_max_bytes: int,
    minimum_free_reserve_bytes: int,
) -> dict[str, Any]:
    with _buffered_locked_line_reader(state.handle) as source_handle:
        return _build_archive_from_reader(
            state,
            source_handle,
            zstd_path=zstd_path,
            zstd_identity=zstd_identity,
            level=level,
            shard_max_bytes=shard_max_bytes,
            minimum_free_reserve_bytes=minimum_free_reserve_bytes,
        )


def _verify_locked_source_unchanged(state: SourceState) -> dict[str, Any]:
    before = os.fstat(state.handle.fileno())
    path_stat = state.path.stat()
    if _source_identity(before) != _source_identity(path_stat):
        raise DemotionRefusal(f"source_path_identity_changed_before_demotion:{state.path}")
    observed = _scan_locked_source_identity(state.handle)
    after = os.fstat(state.handle.fileno())
    if _source_identity(before) != _source_identity(after):
        raise DemotionRefusal(f"source_mutated_during_locked_rehash:{state.path}")
    expected = _byte_identity(state.plan)
    if observed != expected:
        raise DemotionRefusal(
            f"source_locked_rehash_mismatch:{state.path}:"
            f"expected={expected}:actual={observed}"
        )
    return observed


def _assert_backup_is_locked_original(state: SourceState) -> os.stat_result:
    if state.backup_path.is_symlink():
        raise DemotionRefusal(f"original_backup_symlink_forbidden:{state.backup_path}")
    try:
        path_stat = state.backup_path.stat()
    except OSError as exc:
        raise DemotionRefusal(
            f"original_backup_unavailable:{state.backup_path}:{exc}"
        ) from exc
    descriptor_stat = os.fstat(state.handle.fileno())
    if (
        _source_identity(path_stat) != _source_identity(descriptor_stat)
        or _source_identity(path_stat) != _source_identity(state.initial_fstat)
    ):
        raise DemotionRefusal(
            f"original_backup_identity_mismatch:{state.backup_path}"
        )
    return path_stat


def _create_canonical_path_guard(state: SourceState) -> None:
    """Occupy the removed raw pathname so path-based producers fail closed."""

    if state.path.exists() or state.path.is_symlink():
        raise DemotionRefusal(
            f"canonical_raw_path_reappeared_before_guard:{state.path}"
        )
    try:
        state.path.mkdir(mode=0o700)
    except OSError as exc:
        raise DemotionRefusal(
            f"canonical_raw_path_guard_create_failed:{state.path}:{exc}"
        ) from exc
    observed = state.path.lstat()
    if state.path.is_symlink() or not stat.S_ISDIR(observed.st_mode):
        raise DemotionRefusal(f"canonical_raw_path_guard_invalid:{state.path}")
    state.path_guard_created = True
    state.path_guard_identity = (int(observed.st_dev), int(observed.st_ino))
    state.entry["canonical_raw_path_guard"] = {
        "path": str(state.path),
        "device": int(observed.st_dev),
        "inode": int(observed.st_ino),
        "mode": stat.S_IMODE(observed.st_mode),
        "status": "HELD_THROUGH_ARCHIVE_COMMIT_AND_BACKUP_DISPOSITION",
    }
    _fsync_directory(state.path.parent)


def _assert_canonical_path_guard(state: SourceState) -> os.stat_result:
    if not state.path_guard_created or state.path_guard_identity is None:
        raise DemotionRefusal(f"canonical_raw_path_guard_not_owned:{state.path}")
    if state.path.is_symlink():
        raise DemotionRefusal(f"canonical_raw_path_guard_replaced:{state.path}")
    try:
        observed = state.path.lstat()
    except OSError as exc:
        raise DemotionRefusal(
            f"canonical_raw_path_guard_missing:{state.path}:{exc}"
        ) from exc
    identity = (int(observed.st_dev), int(observed.st_ino))
    if not stat.S_ISDIR(observed.st_mode) or identity != state.path_guard_identity:
        raise DemotionRefusal(f"canonical_raw_path_guard_replaced:{state.path}")
    return observed


def _remove_canonical_path_guard(state: SourceState) -> None:
    _assert_canonical_path_guard(state)
    try:
        state.path.rmdir()
    except OSError as exc:
        raise DemotionRefusal(
            f"canonical_raw_path_guard_remove_failed:{state.path}:{exc}"
        ) from exc
    state.path_guard_created = False
    state.path_guard_identity = None
    _fsync_directory(state.path.parent)
    if state.path.exists() or state.path.is_symlink():
        raise DemotionRefusal(
            f"canonical_raw_path_reappeared_after_guard_removal:{state.path}"
        )
    guard = state.entry.get("canonical_raw_path_guard")
    if isinstance(guard, dict):
        guard["status"] = "REMOVED_AFTER_VERIFIED_COLD_COMMIT"


def _assert_canonical_raw_path_absent(state: SourceState) -> None:
    if state.path.exists() or state.path.is_symlink():
        raise DemotionRefusal(
            f"canonical_raw_path_reappeared_during_cold_commit:{state.path}"
        )


def _verify_final_archive(
    state: SourceState,
    *,
    zstd_path: Path,
) -> dict[str, Any]:
    _assert_canonical_path_guard(state)
    verified = verify_archive_structure(
        state.archive_dir / MANIFEST_FILENAME,
        expected_logical_path=state.path,
        require_canonical_location=True,
        verify_compressed_hashes=True,
    )
    with io.BufferedReader(
        ColdConcatReader(verified, zstd_path=zstd_path),
        buffer_size=1024 * 1024,
    ) as logical_handle:
        observed = _scan_binary_identity_stream(logical_handle)
    expected = _byte_identity(state.plan)
    if observed != expected:
        raise DemotionRefusal(
            f"final_archive_concatenation_mismatch:{state.path}:"
            f"expected={expected}:actual={observed}"
        )
    _assert_canonical_path_guard(state)
    return {
        "manifest_path": str(verified.manifest_path),
        "manifest_file_sha256": verified.manifest_file_sha256,
        "manifest_self_hash_sha256": verified.manifest_self_hash_sha256,
        "identity_reverification": observed,
        "logical_reverification": _logical_identity(state.plan),
        "semantic_metadata_inherited_from_initial_locked_scan": _semantic_identity(
            state.plan
        ),
    }


def _operation_manifest(
    *,
    repo_root: Path,
    allowed_root: Path,
    apply: bool,
    operation_id: str,
    entries: Sequence[dict[str, Any]],
    zstd_identity: Mapping[str, Any],
    shard_max_bytes: int,
    minimum_free_reserve_bytes: int,
) -> dict[str, Any]:
    payload = {
        "schema": OPERATION_SCHEMA,
        "generated_at_utc": _utc_now(),
        "operation_id": operation_id,
        "status": "IN_PROGRESS" if apply else "DRY_RUN_NO_MUTATION",
        "mutation_applied": False,
        "repo_root": str(repo_root),
        "repo_head": _git_head(repo_root),
        "allowed_root": str(allowed_root),
        "tool": {
            "path": str(Path(__file__).resolve()),
            "sha256": sha256_file(Path(__file__).resolve()),
            "reader_path": str(
                Path(__file__).resolve().with_name("b7_5_cold_evidence.py")
            ),
            "reader_sha256": sha256_file(
                Path(__file__).resolve().with_name("b7_5_cold_evidence.py")
            ),
            "zstd": copy.deepcopy(dict(zstd_identity)),
        },
        "contract": {
            "initial_full_source_json_object_validation_required": True,
            "later_full_reverification_reuses_semantic_validation_via_exact_byte_identity": True,
            "later_identity_reverification_uses_bounded_binary_chunks": True,
            "line_row_blank_and_terminal_lf_metadata_inherited_after_exact_byte_identity": True,
            "line_safe_shards": True,
            "shard_uncompressed_max_bytes": shard_max_bytes,
            "minimum_free_reserve_bytes": minimum_free_reserve_bytes,
            "exact_concatenated_sha256_bytes_rows_newline_required": True,
            "per_shard_compressed_and_uncompressed_hashes_required": True,
            "per_shard_decompressor_eof_exact_required": True,
            "source_exclusive_lock_and_pre_rename_rehash_required": True,
            "canonical_raw_path_guard_until_cold_commit_required": True,
            "original_backup_until_final_reverification_required": True,
            "raw_and_cold_simultaneous_representation_forbidden": True,
            "broker_runtime_change_status": False,
            "live_activation_status": False,
            "march_outcome_access_status": False,
        },
        "entries": list(entries),
        "failure": None,
    }
    seal_manifest(payload)
    return payload


def _checkpoint(path: Path | None, operation: dict[str, Any], *, apply: bool) -> None:
    if apply:
        assert path is not None
        _write_json_atomic(path, operation)
    else:
        seal_manifest(operation)


def _bounded_cleanup_staging(state: SourceState) -> None:
    staging = state.staging_dir
    if not staging.exists():
        return
    if staging.is_symlink() or not staging.is_dir():
        raise DemotionRefusal(f"staging_cleanup_target_invalid:{staging}")
    expected_prefix = f".{state.path.name}.cold-staging-"
    if staging.parent != state.path.parent or not staging.name.startswith(expected_prefix):
        raise DemotionRefusal(f"staging_cleanup_target_out_of_contract:{staging}")
    shutil.rmtree(staging)
    _fsync_directory(staging.parent)


def _rollback(states: Sequence[SourceState]) -> tuple[bool, list[str]]:
    failures: list[str] = []
    for state in reversed(states):
        try:
            unexpected_paths: list[str] = []
            archive_exists = state.archive_dir.exists() or state.archive_dir.is_symlink()
            staging_exists = state.staging_dir.exists() or state.staging_dir.is_symlink()
            if archive_exists and state.archive_promoted and not staging_exists:
                if state.archive_dir.is_symlink() or not state.archive_dir.is_dir():
                    unexpected_paths.append(str(state.archive_dir))
                else:
                    os.replace(state.archive_dir, state.staging_dir)
                    state.archive_promoted = False
                    _fsync_directory(state.path.parent)
            elif archive_exists:
                # Never remove a canonical path that this operation cannot
                # unambiguously identify as its own promoted staging tree.
                unexpected_paths.append(str(state.archive_dir))

            backup_exists = state.backup_path.exists() or state.backup_path.is_symlink()
            if backup_exists:
                _assert_backup_is_locked_original(state)
                if state.path_guard_created:
                    _remove_canonical_path_guard(state)
                if state.path.exists() or state.path.is_symlink():
                    raise DemotionRefusal(f"rollback_raw_path_occupied:{state.path}")
                os.replace(state.backup_path, state.path)
                state.source_renamed = False
                _fsync_directory(state.path.parent)
            if not state.path.is_file() or state.path.is_symlink():
                raise DemotionRefusal(f"rollback_original_not_restored:{state.path}")
            path_stat = state.path.stat()
            if _source_identity(path_stat) != _source_identity(state.initial_fstat):
                raise DemotionRefusal(f"rollback_original_identity_mismatch:{state.path}")
            observed = _scan_locked_source_identity(state.handle)
            expected = _byte_identity(state.plan)
            if observed != expected:
                raise DemotionRefusal(f"rollback_original_logical_mismatch:{state.path}")
            _bounded_cleanup_staging(state)
            if unexpected_paths:
                raise DemotionRefusal(
                    f"rollback_unowned_paths_preserved:{unexpected_paths}"
                )
            state.entry["rollback_status"] = "ORIGINAL_RAW_PATH_RESTORED_VERIFIED"
        except BaseException as exc:
            failures.append(f"{state.path}:{type(exc).__name__}:{exc}")
            state.entry["rollback_status"] = "MANUAL_RECOVERY_REQUIRED"
            state.entry["rollback_failure"] = failures[-1]
    return not failures, failures


def demote_jsonl_paths(
    *,
    paths: Iterable[Path],
    repo_root: Path,
    allowed_root: Path,
    operation_manifest_path: Path | None,
    apply: bool,
    zstd_path: Path | None = None,
    compression_level: int = 6,
    shard_max_bytes: int = DEFAULT_SHARD_MAX_BYTES,
    minimum_free_reserve_bytes: int = DEFAULT_MIN_FREE_RESERVE_BYTES,
) -> dict[str, Any]:
    repo_root = repo_root.resolve(strict=True)
    allowed_root = allowed_root.resolve(strict=True)
    lexical_paths = [Path(os.path.abspath(path)) for path in paths]
    if not lexical_paths:
        raise DemotionRefusal("at_least_one_path_required")
    if len(set(lexical_paths)) != len(lexical_paths):
        raise DemotionRefusal("duplicate_source_paths_forbidden")
    if not MIN_SHARD_BYTES <= shard_max_bytes <= DEFAULT_SHARD_MAX_BYTES:
        raise DemotionRefusal(
            f"shard_max_bytes_out_of_range:{shard_max_bytes}:"
            f"required={MIN_SHARD_BYTES}..{DEFAULT_SHARD_MAX_BYTES}"
        )
    if not 1 <= compression_level <= 19:
        raise DemotionRefusal(f"compression_level_out_of_range:{compression_level}")
    if minimum_free_reserve_bytes < 0:
        raise DemotionRefusal("minimum_free_reserve_bytes_negative")
    if apply and operation_manifest_path is None:
        raise DemotionRefusal("operation_manifest_required_with_apply")
    if operation_manifest_path is not None and (
        operation_manifest_path.exists() or operation_manifest_path.is_symlink()
    ):
        raise DemotionRefusal(
            f"refusing_to_overwrite_operation_manifest:{operation_manifest_path}"
        )

    zstd = _resolve_zstd(zstd_path)
    zstd_info = _zstd_identity(zstd)
    operation_id = uuid.uuid4().hex
    states: list[SourceState] = []
    entries: list[dict[str, Any]] = []
    operation: dict[str, Any] | None = None
    rollback_permitted = True
    try:
        for source in sorted(lexical_paths):
            handle, source_stat = _lock_source(source, allowed_root)
            try:
                plan = _scan_locked_source_semantic(handle)
                if plan["logical_bytes"] != source_stat.st_size:
                    raise DemotionRefusal(f"source_scan_size_mismatch:{source}")
                archive_dir = cold_archive_dir(source)
                staging_dir = source.with_name(
                    f".{source.name}.cold-staging-{operation_id}"
                )
                backup_path = source.with_name(
                    f".{source.name}.cold-original-backup-{operation_id}"
                )
                for candidate in (archive_dir, staging_dir, backup_path):
                    if candidate.exists() or candidate.is_symlink():
                        raise DemotionRefusal(f"demotion_destination_exists:{candidate}")
                entry = {
                    "path": str(source),
                    "archive_dir": str(archive_dir),
                    "staging_dir": str(staging_dir),
                    "backup_path": str(backup_path),
                    "source_metadata": _source_metadata(source_stat),
                    "logical_plan": plan,
                    "status": "PLANNED_SOURCE_EXCLUSIVE_LOCK_HELD",
                    "recovery_contract": {
                        "initial_full_source_json_object_validation_completed": True,
                        "later_full_reverification_by_exact_byte_identity": True,
                        "later_identity_reverification_uses_bounded_binary_chunks": True,
                        "line_row_blank_and_terminal_lf_metadata_inherited_after_exact_byte_identity": True,
                        "source_exclusive_advisory_lock_held_through_commit": True,
                        "source_rehash_immediately_before_rename": True,
                        "canonical_raw_path_guard_held_until_cold_commit": True,
                        "original_backup_retained_until_all_final_archives_verified": True,
                        "all_or_nothing_pre_backup_delete_rollback": True,
                    },
                }
                entries.append(entry)
                states.append(
                    SourceState(
                        path=source,
                        handle=handle,
                        initial_fstat=source_stat,
                        plan=plan,
                        archive_dir=archive_dir,
                        staging_dir=staging_dir,
                        backup_path=backup_path,
                        entry=entry,
                    )
                )
            except BaseException:
                handle.close()
                raise

        operation = _operation_manifest(
            repo_root=repo_root,
            allowed_root=allowed_root,
            apply=apply,
            operation_id=operation_id,
            entries=entries,
            zstd_identity=zstd_info,
            shard_max_bytes=shard_max_bytes,
            minimum_free_reserve_bytes=minimum_free_reserve_bytes,
        )
        _checkpoint(operation_manifest_path, operation, apply=apply)
        if not apply:
            return operation

        for state in states:
            _build_archive(
                state,
                zstd_path=zstd,
                zstd_identity=zstd_info,
                level=compression_level,
                shard_max_bytes=shard_max_bytes,
                minimum_free_reserve_bytes=minimum_free_reserve_bytes,
            )
            _checkpoint(operation_manifest_path, operation, apply=True)

        for state in states:
            # Keep the locked byte-identity rehash adjacent to this source's rename.
            # A prior all-sources rehash plus an operation-manifest checkpoint
            # left a real mutation window despite the advisory inode locks.
            locked_identity = _verify_locked_source_unchanged(state)
            state.entry["source_locked_identity_reverification_before_rename"] = (
                locked_identity
            )
            state.entry["source_locked_rehash_before_rename"] = _logical_identity(
                state.plan
            )
            state.entry[
                "source_locked_semantic_metadata_inherited_from_initial_scan"
            ] = _semantic_identity(state.plan)
            state.entry["status"] = "SOURCE_REHASHED_IMMEDIATE_RENAME_PENDING"
            os.replace(state.path, state.backup_path)
            state.source_renamed = True
            _assert_backup_is_locked_original(state)
            _create_canonical_path_guard(state)
            state.entry["status"] = "ORIGINAL_BACKUP_RETAINED_PATH_GUARD_HELD"
            _fsync_directory(state.path.parent)
        operation["mutation_applied"] = True
        _checkpoint(operation_manifest_path, operation, apply=True)

        for state in states:
            _assert_canonical_path_guard(state)
            state.archive_promoted = True
            os.replace(state.staging_dir, state.archive_dir)
            state.entry["status"] = "FINAL_ARCHIVE_PROMOTED_BACKUP_RETAINED"
            _fsync_directory(state.path.parent)
        _checkpoint(operation_manifest_path, operation, apply=True)

        for state in states:
            _assert_canonical_path_guard(state)
            state.entry["final_archive"] = _verify_final_archive(
                state, zstd_path=zstd
            )
            _assert_backup_is_locked_original(state)
            backup_observed = _scan_locked_source_identity(state.handle)
            expected = _byte_identity(state.plan)
            if backup_observed != expected:
                raise DemotionRefusal(f"original_backup_logical_mismatch:{state.path}")
            state.entry["original_backup_identity_reverification"] = backup_observed
            state.entry["original_backup_reverification"] = _logical_identity(
                state.plan
            )
            state.entry[
                "original_backup_semantic_metadata_inherited_from_initial_scan"
            ] = _semantic_identity(state.plan)
            _assert_canonical_path_guard(state)
            state.entry["status"] = (
                "FINAL_ARCHIVE_AND_ORIGINAL_BACKUP_VERIFIED_PATH_GUARD_HELD"
            )
        _checkpoint(operation_manifest_path, operation, apply=True)

        # From this point onward every canonical archive and every retained
        # original backup has passed a full logical re-read.  Once backup
        # deletion starts, rollback is no longer all-or-nothing; a later
        # bookkeeping failure must preserve the verified canonical archives.
        rollback_permitted = False
        retained_backups: list[str] = []
        for state in states:
            try:
                _assert_canonical_path_guard(state)
                _assert_backup_is_locked_original(state)
                state.backup_path.unlink()
                state.backup_deleted = True
                _fsync_directory(state.path.parent)
                state.entry["original_backup_deleted_after_final_reverification"] = True
                state.entry["status"] = "COLD_DEMOTION_VERIFIED_PATH_GUARD_HELD"
            except OSError as exc:
                retained_backups.append(str(state.backup_path))
                state.entry["original_backup_deleted_after_final_reverification"] = False
                state.entry["backup_delete_failure"] = f"{type(exc).__name__}:{exc}"
                state.entry["status"] = (
                    "COLD_DEMOTION_VERIFIED_BACKUP_RETAINED_PATH_GUARD_HELD"
                )

        for state in states:
            _assert_canonical_path_guard(state)
            _remove_canonical_path_guard(state)
            _assert_canonical_raw_path_absent(state)
            state.entry["status"] = (
                "COLD_DEMOTION_VERIFIED"
                if state.backup_deleted
                else "COLD_DEMOTION_VERIFIED_BACKUP_RETAINED"
            )

        operation["status"] = (
            OPERATION_PASS
            if not retained_backups
            else "PASS_COLD_DEMOTION_VERIFIED_BACKUPS_RETAINED"
        )
        operation["retained_backups"] = retained_backups
        operation["completed_at_utc"] = _utc_now()
        operation["totals"] = {
            "file_count": len(states),
            "logical_bytes": sum(state.plan["logical_bytes"] for state in states),
            "compressed_shard_bytes": sum(
                state.entry["staged_archive"]["compressed_bytes"] for state in states
            ),
            "json_object_row_count": sum(
                state.plan["json_object_row_count"] for state in states
            ),
        }
        _checkpoint(operation_manifest_path, operation, apply=True)
        # Close the final check/write race as far as a pathname-only protocol
        # can: a producer that recreates the raw name during the final manifest
        # write converts the operation to an explicit post-commit failure,
        # never a false PASS.  The path guard above protects the entire long
        # archive verification and backup-disposition interval.
        for state in states:
            _assert_canonical_raw_path_absent(state)
        return operation
    except BaseException as exc:
        if operation is None:
            raise
        operation["failure"] = f"{type(exc).__name__}:{exc}"
        if rollback_permitted:
            rollback_ok, rollback_failures = _rollback(states)
            operation["status"] = (
                "FAILED_SAFE_ORIGINAL_RAW_PATHS_RESTORED"
                if rollback_ok
                else "FAILED_MANUAL_RECOVERY_REQUIRED"
            )
            operation["rollback_failures"] = rollback_failures
        else:
            operation["status"] = (
                "FAILED_RECORDING_AFTER_VERIFIED_COLD_COMMIT_ARCHIVES_PRESERVED"
            )
            operation["rollback_failures"] = []
            operation["post_commit_archive_preservation"] = True
        operation["completed_at_utc"] = _utc_now()
        try:
            _checkpoint(operation_manifest_path, operation, apply=apply)
        except BaseException as checkpoint_exc:
            operation["failure_checkpoint"] = (
                f"{type(checkpoint_exc).__name__}:{checkpoint_exc}"
            )
        raise
    finally:
        for state in states:
            try:
                fcntl.flock(state.handle.fileno(), fcntl.LOCK_UN)
            except OSError:
                pass
            state.handle.close()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", action="append", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--allowed-root", type=Path, required=True)
    parser.add_argument("--operation-manifest", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--zstd", type=Path)
    parser.add_argument("--compression-level", type=int, default=6)
    parser.add_argument(
        "--shard-max-bytes", type=int, default=DEFAULT_SHARD_MAX_BYTES
    )
    parser.add_argument(
        "--minimum-free-reserve-bytes",
        type=int,
        default=DEFAULT_MIN_FREE_RESERVE_BYTES,
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = demote_jsonl_paths(
            paths=args.path,
            repo_root=args.repo_root,
            allowed_root=args.allowed_root,
            operation_manifest_path=args.operation_manifest,
            apply=args.apply,
            zstd_path=args.zstd,
            compression_level=args.compression_level,
            shard_max_bytes=args.shard_max_bytes,
            minimum_free_reserve_bytes=args.minimum_free_reserve_bytes,
        )
    except (DemotionRefusal, ColdEvidenceError, OSError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
