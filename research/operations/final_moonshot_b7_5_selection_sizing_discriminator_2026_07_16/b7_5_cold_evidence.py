#!/usr/bin/env python3
"""Fail-closed logical reader for raw or chunked-zstd B7.5 JSONL evidence.

The cold layout is deliberately adjacent to the raw logical path::

    <ledger>.jsonl.cold/
      manifest.json
      part-000000.jsonl.zst
      part-000001.jsonl.zst

Exactly one representation may exist.  A raw file wins only when no cold
directory exists; simultaneous raw and cold representations are an error.
Cold reads are transparent, streaming, and seekable.  Seeking replays at most
one line-safe shard from its beginning, so no full-ledger materialization is
required.  A completed shard must reach decompressor EOF at exactly its
declared uncompressed byte count; concatenated or appended frames fail closed.
"""

from __future__ import annotations

import bisect
import copy
import hashlib
import io
import json
import os
import re
import shutil
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO, Iterator, Mapping, Sequence, TextIO


ARCHIVE_SCHEMA = "gtos.b7_5.cold_jsonl_archive.v1"
ARCHIVE_PASS_STATUS = "PASS_COLD_ARCHIVE_LOGICAL_BYTES_VERIFIED"
MANIFEST_FILENAME = "manifest.json"
COLD_SUFFIX = ".cold"
SHARD_NAME_RE = re.compile(r"^part-(?P<index>\d{6})\.jsonl\.zst$")
DEFAULT_SHARD_MAX_BYTES = 256 * 1024 * 1024
HASH_CHUNK_BYTES = 16 * 1024 * 1024


class ColdEvidenceError(RuntimeError):
    """Raised when a raw/cold evidence invariant is not satisfied."""


def canonical_json_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb", buffering=0) as handle:
        for chunk in iter(lambda: handle.read(HASH_CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()


def manifest_payload(manifest: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in manifest.items() if key != "self_hash"}


def seal_manifest(manifest: dict[str, Any]) -> None:
    manifest["self_hash"] = {
        "algorithm": "sha256",
        "canonicalization": (
            "utf8_json_sort_keys_compact_separators_excluding_self_hash"
        ),
        "sha256": sha256_bytes(canonical_json_bytes(manifest_payload(manifest))),
    }


def verify_manifest_self_hash(manifest: Mapping[str, Any]) -> str:
    self_hash = manifest.get("self_hash")
    if not isinstance(self_hash, Mapping):
        raise ColdEvidenceError("cold_manifest_self_hash_missing")
    expected = self_hash.get("sha256")
    actual = sha256_bytes(canonical_json_bytes(manifest_payload(manifest)))
    if not isinstance(expected, str) or expected != actual:
        raise ColdEvidenceError(
            f"cold_manifest_self_hash_invalid:expected={expected}:actual={actual}"
        )
    return actual


def cold_archive_dir(path: Path) -> Path:
    return path.with_name(path.name + COLD_SUFFIX)


def cold_manifest_path(path: Path) -> Path:
    return cold_archive_dir(path) / MANIFEST_FILENAME


def _regular_nonsymlink(path: Path, *, label: str) -> os.stat_result:
    if path.is_symlink():
        raise ColdEvidenceError(f"{label}_symlink_forbidden:{path}")
    try:
        observed = path.stat()
    except OSError as exc:
        raise ColdEvidenceError(f"{label}_unavailable:{path}:{exc}") from exc
    if not stat.S_ISREG(observed.st_mode):
        raise ColdEvidenceError(f"{label}_not_regular_file:{path}")
    return observed


def _load_json_object(path: Path) -> dict[str, Any]:
    _regular_nonsymlink(path, label="cold_manifest")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ColdEvidenceError(f"cold_manifest_invalid_json:{path}:{exc}") from exc
    if not isinstance(payload, dict):
        raise ColdEvidenceError(f"cold_manifest_not_object:{path}")
    return payload


def _integer(value: Any, *, label: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ColdEvidenceError(f"{label}_invalid:{value!r}")
    parsed = value
    if parsed < minimum:
        raise ColdEvidenceError(f"{label}_invalid:{value!r}")
    return parsed


def _hex_sha256(value: Any, *, label: str) -> str:
    if not isinstance(value, str):
        raise ColdEvidenceError(f"{label}_invalid:{value!r}")
    text = value.lower()
    if len(text) != 64 or any(char not in "009abcdef" for char in text):
        raise ColdEvidenceError(f"{label}_invalid:{value!r}")
    return text


@dataclass(frozen=True)
class VerifiedArchive:
    logical_path: Path
    archive_dir: Path
    manifest_path: Path
    manifest: Mapping[str, Any]
    manifest_file_sha256: str
    manifest_self_hash_sha256: str
    shard_paths: tuple[Path, ...]

    @property
    def logical_bytes(self) -> int:
        return int(self.manifest["logical_source"]["logical_bytes"])

    @property
    def logical_sha256(self) -> str:
        return str(self.manifest["logical_source"]["sha256"])


def verify_archive_structure(
    manifest_path: Path,
    *,
    expected_logical_path: Path,
    require_canonical_location: bool = True,
    verify_compressed_hashes: bool = True,
) -> VerifiedArchive:
    """Validate a cold manifest and every stored shard without inflating data."""

    manifest_path = Path(os.path.abspath(manifest_path))
    expected_logical_path = Path(os.path.abspath(expected_logical_path))
    archive_dir = manifest_path.parent
    if require_canonical_location:
        expected_manifest = cold_manifest_path(expected_logical_path)
        if manifest_path != expected_manifest:
            raise ColdEvidenceError(
                "cold_manifest_noncanonical_location:"
                f"expected={expected_manifest}:actual={manifest_path}"
            )
    if archive_dir.is_symlink():
        raise ColdEvidenceError(f"cold_archive_dir_symlink_forbidden:{archive_dir}")
    if not archive_dir.is_dir():
        raise ColdEvidenceError(f"cold_archive_dir_missing:{archive_dir}")

    manifest = _load_json_object(manifest_path)
    manifest_self_hash = verify_manifest_self_hash(manifest)
    if manifest.get("schema") != ARCHIVE_SCHEMA:
        raise ColdEvidenceError(f"cold_manifest_schema_invalid:{manifest.get('schema')}")
    if manifest.get("status") != ARCHIVE_PASS_STATUS:
        raise ColdEvidenceError(f"cold_manifest_status_invalid:{manifest.get('status')}")

    logical = manifest.get("logical_source")
    layout = manifest.get("archive_layout")
    shards = manifest.get("shards")
    boundary = manifest.get("safety_boundary")
    if not isinstance(logical, Mapping):
        raise ColdEvidenceError("cold_manifest_logical_source_missing")
    if not isinstance(layout, Mapping):
        raise ColdEvidenceError("cold_manifest_archive_layout_missing")
    if not isinstance(shards, list) or not shards:
        raise ColdEvidenceError("cold_manifest_shards_missing")
    if not isinstance(boundary, Mapping):
        raise ColdEvidenceError("cold_manifest_safety_boundary_missing")

    if logical.get("name") != expected_logical_path.name:
        raise ColdEvidenceError(
            "cold_manifest_logical_name_mismatch:"
            f"expected={expected_logical_path.name}:actual={logical.get('name')}"
        )
    logical_bytes = _integer(
        logical.get("logical_bytes"), label="cold_logical_bytes", minimum=1
    )
    logical_rows = _integer(
        logical.get("json_object_row_count"),
        label="cold_logical_json_object_rows",
        minimum=0,
    )
    logical_lines = _integer(
        logical.get("physical_line_count"),
        label="cold_logical_physical_lines",
        minimum=1,
    )
    logical_blanks = _integer(
        logical.get("blank_line_count"),
        label="cold_logical_blank_lines",
        minimum=0,
    )
    _hex_sha256(logical.get("sha256"), label="cold_logical_sha256")
    if not isinstance(logical.get("ends_with_lf"), bool):
        raise ColdEvidenceError("cold_logical_ends_with_lf_invalid")
    if logical_rows + logical_blanks != logical_lines:
        raise ColdEvidenceError("cold_manifest_logical_line_accounting_invalid")

    shard_max = _integer(
        layout.get("shard_uncompressed_max_bytes"),
        label="cold_shard_max_bytes",
        minimum=1,
    )
    if shard_max > DEFAULT_SHARD_MAX_BYTES:
        raise ColdEvidenceError(
            f"cold_shard_max_exceeds_contract:{shard_max}>{DEFAULT_SHARD_MAX_BYTES}"
        )
    if layout.get("manifest_filename") != MANIFEST_FILENAME:
        raise ColdEvidenceError("cold_archive_manifest_filename_invalid")
    if layout.get("codec") != "zstd" or layout.get("line_safe") is not True:
        raise ColdEvidenceError("cold_archive_codec_or_line_safety_invalid")
    if layout.get("concatenation_order") != "ascending_shard_index":
        raise ColdEvidenceError("cold_archive_concatenation_order_invalid")
    if _integer(layout.get("shard_count"), label="cold_shard_count", minimum=1) != len(shards):
        raise ColdEvidenceError("cold_archive_shard_count_mismatch")
    verification = manifest.get("verification")
    if not isinstance(verification, Mapping):
        raise ColdEvidenceError("cold_manifest_verification_missing")
    for key in (
        "each_compressed_shard_reopened_and_fully_decompressed",
        "each_uncompressed_shard_sha256_matched",
        "each_compressed_shard_sha256_recorded",
        "each_shard_decompressor_eof_exact",
        "exact_concatenated_sha256_required",
        "exact_concatenated_bytes_rows_and_newline_required",
        "source_rehashed_under_exclusive_lock_before_demotion",
        "original_backup_retained_until_final_archive_reverification",
    ):
        if verification.get(key) is not True:
            raise ColdEvidenceError(f"cold_archive_verification_contract_invalid:{key}")
    for key in (
        "broker_runtime_change_status",
        "live_activation_status",
        "march_outcome_access_status",
    ):
        if boundary.get(key) is not False:
            raise ColdEvidenceError(f"cold_archive_safety_boundary_invalid:{key}")

    shard_paths: list[Path] = []
    next_offset = 0
    next_line = 1
    row_sum = 0
    blank_sum = 0
    line_sum = 0
    compressed_names: set[str] = set()
    for expected_index, shard in enumerate(shards):
        if not isinstance(shard, Mapping):
            raise ColdEvidenceError(f"cold_shard_not_object:{expected_index}")
        index = _integer(shard.get("index"), label="cold_shard_index", minimum=0)
        if index != expected_index:
            raise ColdEvidenceError(
                f"cold_shard_index_noncontiguous:{index}!={expected_index}"
            )
        name = str(shard.get("name") or "")
        match = SHARD_NAME_RE.fullmatch(name)
        if match is None or int(match.group("index")) != index or name in compressed_names:
            raise ColdEvidenceError(f"cold_shard_name_invalid:{name}")
        compressed_names.add(name)
        shard_path = archive_dir / name
        try:
            shard_path.relative_to(archive_dir)
        except ValueError as exc:
            raise ColdEvidenceError(f"cold_shard_path_escape:{shard_path}") from exc
        observed = _regular_nonsymlink(shard_path, label="cold_shard")
        compressed_bytes = _integer(
            shard.get("compressed_bytes"),
            label=f"cold_shard_compressed_bytes:{index}",
            minimum=1,
        )
        if observed.st_size != compressed_bytes:
            raise ColdEvidenceError(
                f"cold_shard_compressed_size_mismatch:{index}:"
                f"{observed.st_size}!={compressed_bytes}"
            )
        compressed_sha = _hex_sha256(
            shard.get("compressed_sha256"),
            label=f"cold_shard_compressed_sha256:{index}",
        )
        if verify_compressed_hashes:
            actual_compressed_sha = sha256_file(shard_path)
            if actual_compressed_sha != compressed_sha:
                raise ColdEvidenceError(
                    f"cold_shard_compressed_hash_mismatch:{index}:"
                    f"{actual_compressed_sha}!={compressed_sha}"
                )

        start = _integer(
            shard.get("logical_start_offset"),
            label=f"cold_shard_start:{index}",
            minimum=0,
        )
        end = _integer(
            shard.get("logical_end_offset_exclusive"),
            label=f"cold_shard_end:{index}",
            minimum=1,
        )
        uncompressed_bytes = _integer(
            shard.get("uncompressed_bytes"),
            label=f"cold_shard_uncompressed_bytes:{index}",
            minimum=1,
        )
        _hex_sha256(
            shard.get("uncompressed_sha256"),
            label=f"cold_shard_uncompressed_sha256:{index}",
        )
        if start != next_offset or end - start != uncompressed_bytes:
            raise ColdEvidenceError(f"cold_shard_offset_accounting_invalid:{index}")
        if uncompressed_bytes > shard_max:
            raise ColdEvidenceError(f"cold_shard_uncompressed_limit_exceeded:{index}")

        first_line = _integer(
            shard.get("first_physical_line_number"),
            label=f"cold_shard_first_line:{index}",
            minimum=1,
        )
        last_line = _integer(
            shard.get("last_physical_line_number"),
            label=f"cold_shard_last_line:{index}",
            minimum=1,
        )
        physical_lines = _integer(
            shard.get("physical_line_count"),
            label=f"cold_shard_physical_lines:{index}",
            minimum=1,
        )
        rows = _integer(
            shard.get("json_object_row_count"),
            label=f"cold_shard_rows:{index}",
            minimum=0,
        )
        blanks = _integer(
            shard.get("blank_line_count"),
            label=f"cold_shard_blanks:{index}",
            minimum=0,
        )
        if not isinstance(shard.get("ends_with_lf"), bool):
            raise ColdEvidenceError(f"cold_shard_ends_with_lf_invalid:{index}")
        if (
            first_line != next_line
            or last_line - first_line + 1 != physical_lines
            or rows + blanks != physical_lines
        ):
            raise ColdEvidenceError(f"cold_shard_line_accounting_invalid:{index}")
        if index < len(shards) - 1 and shard.get("ends_with_lf") is not True:
            raise ColdEvidenceError(f"cold_nonfinal_shard_without_lf:{index}")

        shard_paths.append(shard_path)
        next_offset = end
        next_line = last_line + 1
        row_sum += rows
        blank_sum += blanks
        line_sum += physical_lines

    if (
        next_offset != logical_bytes
        or row_sum != logical_rows
        or blank_sum != logical_blanks
        or line_sum != logical_lines
        or bool(shards[-1].get("ends_with_lf"))
        != bool(logical.get("ends_with_lf"))
    ):
        raise ColdEvidenceError("cold_archive_concatenated_accounting_invalid")

    expected_entries = {MANIFEST_FILENAME, *compressed_names}
    try:
        actual_entries = {entry.name for entry in archive_dir.iterdir()}
    except OSError as exc:
        raise ColdEvidenceError(
            f"cold_archive_directory_unreadable:{archive_dir}:{exc}"
        ) from exc
    if actual_entries != expected_entries:
        raise ColdEvidenceError(
            "cold_archive_directory_entries_invalid:"
            f"expected={sorted(expected_entries)}:actual={sorted(actual_entries)}"
        )

    return VerifiedArchive(
        logical_path=expected_logical_path,
        archive_dir=archive_dir,
        manifest_path=manifest_path,
        manifest=manifest,
        manifest_file_sha256=sha256_file(manifest_path),
        manifest_self_hash_sha256=manifest_self_hash,
        shard_paths=tuple(shard_paths),
    )


def _find_zstd(explicit: Path | None = None) -> Path:
    candidate = str(explicit) if explicit is not None else shutil.which("zstd")
    if not candidate:
        raise ColdEvidenceError("zstd_binary_not_found")
    path = Path(candidate).resolve(strict=True)
    _regular_nonsymlink(path, label="zstd_binary")
    return path


class ColdConcatReader(io.RawIOBase):
    """Binary logical view over ordered independent zstd shards."""

    def __init__(self, archive: VerifiedArchive, *, zstd_path: Path | None = None):
        super().__init__()
        self._archive = archive
        self._zstd = _find_zstd(zstd_path)
        self._shards: Sequence[Mapping[str, Any]] = archive.manifest["shards"]
        self._ends = [int(shard["logical_end_offset_exclusive"]) for shard in self._shards]
        self._position = 0
        self._process: subprocess.Popen[bytes] | None = None
        self._process_shard = -1
        self._shard_consumed = 0
        self._shard_digest: hashlib._Hash | None = None

    def readable(self) -> bool:
        return True

    def writable(self) -> bool:
        return False

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        self._checkClosed()
        return self._position

    def _stop_process(self, *, completed: bool) -> None:
        process = self._process
        if process is None:
            return
        stdout = process.stdout
        stderr = process.stderr
        try:
            if stdout is not None:
                stdout.close()
            if completed:
                error = stderr.read() if stderr is not None else b""
                returncode = process.wait()
                if returncode != 0:
                    raise ColdEvidenceError(
                        f"zstd_decompression_failed:shard={self._process_shard}:"
                        f"exit={returncode}:stderr={error.decode('utf-8', errors='replace').strip()}"
                    )
                expected = str(
                    self._shards[self._process_shard]["uncompressed_sha256"]
                )
                actual = self._shard_digest.hexdigest() if self._shard_digest else ""
                if actual != expected:
                    raise ColdEvidenceError(
                        f"cold_shard_uncompressed_hash_mismatch:{self._process_shard}:"
                        f"{actual}!={expected}"
                    )
            else:
                if process.poll() is None:
                    process.terminate()
                process.wait()
        finally:
            if stderr is not None:
                stderr.close()
            self._process = None
            self._process_shard = -1
            self._shard_consumed = 0
            self._shard_digest = None

    def _open_shard(self, index: int, *, skip: int = 0) -> None:
        self._stop_process(completed=False)
        if not 0 <= index < len(self._shards):
            raise ColdEvidenceError(f"cold_shard_index_out_of_range:{index}")
        shard = self._shards[index]
        shard_size = int(shard["uncompressed_bytes"])
        if not 0 <= skip <= shard_size:
            raise ColdEvidenceError(f"cold_shard_seek_out_of_range:{index}:{skip}")
        process = subprocess.Popen(
            [str(self._zstd), "-q", "-d", "-c", str(self._archive.shard_paths[index])],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if process.stdout is None or process.stderr is None:
            process.kill()
            process.wait()
            raise ColdEvidenceError("zstd_decompression_pipe_unavailable")
        self._process = process
        self._process_shard = index
        self._shard_consumed = 0
        self._shard_digest = hashlib.sha256()
        while self._shard_consumed < skip:
            needed = min(HASH_CHUNK_BYTES, skip - self._shard_consumed)
            chunk = process.stdout.read(needed)
            if not chunk:
                self._stop_process(completed=False)
                raise ColdEvidenceError(f"cold_shard_truncated_during_seek:{index}")
            self._shard_digest.update(chunk)
            self._shard_consumed += len(chunk)

    def _current_shard_index(self) -> int:
        if self._position >= self._archive.logical_bytes:
            return len(self._shards)
        return bisect.bisect_right(self._ends, self._position)

    def _ensure_process(self) -> None:
        index = self._current_shard_index()
        if index >= len(self._shards):
            self._stop_process(completed=False)
            return
        shard_start = int(self._shards[index]["logical_start_offset"])
        desired = self._position - shard_start
        if self._process_shard != index or self._shard_consumed != desired:
            self._open_shard(index, skip=desired)

    def _finish_shard_exactly(self) -> None:
        """Require decompressor EOF immediately after the declared shard bytes."""

        process = self._process
        index = self._process_shard
        if process is None or process.stdout is None or not 0 <= index < len(self._shards):
            raise ColdEvidenceError("cold_shard_finish_without_active_process")
        expected_bytes = int(self._shards[index]["uncompressed_bytes"])
        if self._shard_consumed != expected_bytes:
            raise ColdEvidenceError(
                f"cold_shard_finish_size_mismatch:{index}:"
                f"{self._shard_consumed}!={expected_bytes}"
            )
        # Zstd transparently concatenates frames.  Reading only the manifest's
        # declared prefix would therefore accept an appended valid frame unless
        # EOF is proved explicitly.  A one-byte probe is enough and blocks only
        # until the quiet decompressor either produces overflow or exits.
        overflow = process.stdout.read(1)
        if overflow:
            self._stop_process(completed=False)
            raise ColdEvidenceError(
                f"cold_shard_uncompressed_overflow:{index}:"
                f"declared_bytes={expected_bytes}"
            )
        self._stop_process(completed=True)

    def readinto(self, buffer: Any) -> int:
        data = self.read(len(buffer))
        count = len(data)
        buffer[:count] = data
        return count

    def read(self, size: int = -1) -> bytes:
        self._checkClosed()
        remaining_total = self._archive.logical_bytes - self._position
        if remaining_total <= 0 or size == 0:
            return b""
        target = remaining_total if size is None or size < 0 else min(size, remaining_total)
        result = bytearray()
        while len(result) < target:
            self._ensure_process()
            if self._process is None or self._process.stdout is None:
                break
            shard = self._shards[self._process_shard]
            shard_remaining = int(shard["uncompressed_bytes"]) - self._shard_consumed
            wanted = min(target - len(result), shard_remaining)
            chunk = self._process.stdout.read(wanted)
            if not chunk:
                self._stop_process(completed=False)
                raise ColdEvidenceError(
                    f"cold_shard_truncated:{self._process_shard}:"
                    f"remaining={shard_remaining}"
                )
            assert self._shard_digest is not None
            self._shard_digest.update(chunk)
            self._shard_consumed += len(chunk)
            self._position += len(chunk)
            result.extend(chunk)
            if self._shard_consumed == int(shard["uncompressed_bytes"]):
                self._finish_shard_exactly()
        return bytes(result)

    def seek(self, offset: int, whence: int = os.SEEK_SET) -> int:
        self._checkClosed()
        if whence == os.SEEK_SET:
            target = offset
        elif whence == os.SEEK_CUR:
            target = self._position + offset
        elif whence == os.SEEK_END:
            target = self._archive.logical_bytes + offset
        else:
            raise ValueError(f"unsupported whence: {whence}")
        if not 0 <= target <= self._archive.logical_bytes:
            raise ValueError(f"seek outside logical evidence: {target}")
        if target != self._position:
            self._stop_process(completed=False)
            self._position = target
        return self._position

    def close(self) -> None:
        if not self.closed:
            self._stop_process(completed=False)
        super().close()


def scan_jsonl_binary_stream(handle: BinaryIO, *, parse_json: bool = True) -> dict[str, Any]:
    digest = hashlib.sha256()
    byte_count = 0
    physical_lines = 0
    rows = 0
    blanks = 0
    ends_with_lf = False
    for physical_lines, line in enumerate(handle, start=1):
        digest.update(line)
        byte_count += len(line)
        ends_with_lf = line.endswith(b"\n")
        if not line.strip():
            blanks += 1
            continue
        rows += 1
        if parse_json:
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ColdEvidenceError(
                    f"cold_logical_invalid_jsonl:line={physical_lines}:{exc}"
                ) from exc
            if not isinstance(payload, dict):
                raise ColdEvidenceError(
                    f"cold_logical_jsonl_row_not_object:line={physical_lines}"
                )
    return {
        "logical_bytes": byte_count,
        "sha256": digest.hexdigest(),
        "physical_line_count": physical_lines,
        "json_object_row_count": rows,
        "blank_line_count": blanks,
        "ends_with_lf": ends_with_lf,
    }


class RawOrColdResolver:
    """Resolve one logical JSONL path to exactly one verified representation."""

    def __init__(self, *, zstd_path: Path | None = None):
        self.zstd_path = _find_zstd(zstd_path)

    def mode(self, path: Path) -> str:
        path = Path(os.path.abspath(path))
        raw_exists = path.exists() or path.is_symlink()
        archive = cold_archive_dir(path)
        cold_exists = archive.exists() or archive.is_symlink()
        if raw_exists and cold_exists:
            raise ColdEvidenceError(f"raw_and_cold_evidence_ambiguous:{path}")
        if raw_exists:
            _regular_nonsymlink(path, label="raw_evidence")
            return "raw"
        if cold_exists:
            if archive.is_symlink() or not archive.is_dir():
                raise ColdEvidenceError(f"cold_archive_dir_invalid:{archive}")
            return "cold"
        raise ColdEvidenceError(f"logical_evidence_missing:{path}")

    def exists(self, path: Path) -> bool:
        try:
            self.mode(path)
        except ColdEvidenceError as exc:
            if str(exc).startswith("logical_evidence_missing:"):
                return False
            raise
        return True

    def archive(
        self,
        path: Path,
        *,
        verify_compressed_hashes: bool = True,
    ) -> VerifiedArchive:
        if self.mode(path) != "cold":
            raise ColdEvidenceError(f"logical_evidence_not_cold:{path}")
        return verify_archive_structure(
            cold_manifest_path(Path(os.path.abspath(path))),
            expected_logical_path=Path(os.path.abspath(path)),
            require_canonical_location=True,
            verify_compressed_hashes=verify_compressed_hashes,
        )

    def open_binary(self, path: Path) -> BinaryIO:
        path = Path(os.path.abspath(path))
        mode = self.mode(path)
        if mode == "raw":
            return path.open("rb")
        archive = self.archive(path)
        return io.BufferedReader(
            ColdConcatReader(archive, zstd_path=self.zstd_path),
            buffer_size=1024 * 1024,
        )

    def open_text(
        self,
        path: Path,
        *,
        encoding: str = "utf-8",
        errors: str = "strict",
    ) -> TextIO:
        return io.TextIOWrapper(
            self.open_binary(path),
            encoding=encoding,
            errors=errors,
            newline=None,
        )

    def iter_binary_lines(self, path: Path) -> Iterator[bytes]:
        with self.open_binary(path) as handle:
            yield from handle

    def logical_metadata(
        self,
        path: Path,
        *,
        verify_full: bool = False,
        parse_json: bool = True,
    ) -> dict[str, Any]:
        path = Path(os.path.abspath(path))
        mode = self.mode(path)
        if mode == "raw":
            before = path.stat()
            with path.open("rb") as handle:
                observed = scan_jsonl_binary_stream(handle, parse_json=parse_json)
            after = path.stat()
            if (
                before.st_dev,
                before.st_ino,
                before.st_size,
                before.st_mtime_ns,
            ) != (
                after.st_dev,
                after.st_ino,
                after.st_size,
                after.st_mtime_ns,
            ):
                raise ColdEvidenceError(f"raw_evidence_mutated_while_scanning:{path}")
            return {
                **observed,
                "path": str(path),
                "storage_mode": "raw",
                "storage_identity": [
                    int(after.st_dev),
                    int(after.st_ino),
                    int(after.st_size),
                    int(after.st_mtime_ns),
                ],
            }

        archive = self.archive(path, verify_compressed_hashes=True)
        logical = dict(archive.manifest["logical_source"])
        result = {
            **logical,
            "path": str(path),
            "storage_mode": "cold_zstd_shards",
            "manifest_path": str(archive.manifest_path),
            "manifest_file_sha256": archive.manifest_file_sha256,
            "manifest_self_hash_sha256": archive.manifest_self_hash_sha256,
            "storage_identity": [
                archive.manifest_self_hash_sha256,
                *[str(shard["compressed_sha256"]) for shard in archive.manifest["shards"]],
            ],
        }
        if verify_full:
            with self.open_binary(path) as handle:
                observed = scan_jsonl_binary_stream(handle, parse_json=parse_json)
            expected = {
                key: logical[key]
                for key in (
                    "logical_bytes",
                    "sha256",
                    "physical_line_count",
                    "json_object_row_count",
                    "blank_line_count",
                    "ends_with_lf",
                )
            }
            if observed != expected:
                raise ColdEvidenceError(
                    f"cold_logical_concatenation_mismatch:{path}:"
                    f"expected={expected}:actual={observed}"
                )
            result["full_logical_reverification"] = True
        return result


def open_raw_or_cold_binary(
    path: Path,
    *,
    zstd_path: Path | None = None,
) -> BinaryIO:
    return RawOrColdResolver(zstd_path=zstd_path).open_binary(path)


def open_raw_or_cold_text(
    path: Path,
    *,
    zstd_path: Path | None = None,
    encoding: str = "utf-8",
    errors: str = "strict",
) -> TextIO:
    return RawOrColdResolver(zstd_path=zstd_path).open_text(
        path,
        encoding=encoding,
        errors=errors,
    )


__all__ = [
    "ARCHIVE_PASS_STATUS",
    "ARCHIVE_SCHEMA",
    "COLD_SUFFIX",
    "ColdConcatReader",
    "ColdEvidenceError",
    "DEFAULT_SHARD_MAX_BYTES",
    "MANIFEST_FILENAME",
    "RawOrColdResolver",
    "VerifiedArchive",
    "canonical_json_bytes",
    "cold_archive_dir",
    "cold_manifest_path",
    "manifest_payload",
    "open_raw_or_cold_binary",
    "open_raw_or_cold_text",
    "scan_jsonl_binary_stream",
    "seal_manifest",
    "sha256_file",
    "verify_archive_structure",
    "verify_manifest_self_hash",
]
