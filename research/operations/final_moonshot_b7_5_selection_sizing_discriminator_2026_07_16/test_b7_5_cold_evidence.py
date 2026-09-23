from __future__ import annotations

import fcntl
import hashlib
import io
import json
import os
import shutil
from pathlib import Path

import pytest

import archive_b7_5_cold_evidence as archiver
from b7_5_cold_evidence import (
    ARCHIVE_PASS_STATUS,
    ColdEvidenceError,
    RawOrColdResolver,
    cold_archive_dir,
    verify_archive_structure,
    verify_manifest_self_hash,
)


ZSTD = shutil.which("zstd")
pytestmark = pytest.mark.skipif(ZSTD is None, reason="zstd is required")


def _jsonl(row_count: int = 700, payload_bytes: int = 96) -> bytes:
    return b"".join(
        json.dumps(
            {"row": index, "payload": "x" * payload_bytes},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
        for index in range(row_count)
    )


def _apply(
    source: Path,
    operation_manifest: Path,
    *,
    shard_max_bytes: int = 16 * 1024,
) -> dict[str, object]:
    return archiver.demote_jsonl_paths(
        paths=[source],
        repo_root=source.parent,
        allowed_root=source.parent,
        operation_manifest_path=operation_manifest,
        apply=True,
        zstd_path=Path(ZSTD),
        compression_level=3,
        shard_max_bytes=shard_max_bytes,
        minimum_free_reserve_bytes=0,
    )


def test_dry_run_is_self_hashed_and_does_not_mutate_source(tmp_path: Path) -> None:
    source = tmp_path / "ledger.jsonl"
    original = _jsonl(row_count=40)
    source.write_bytes(original)
    before = source.stat()

    result = archiver.demote_jsonl_paths(
        paths=[source],
        repo_root=tmp_path,
        allowed_root=tmp_path,
        operation_manifest_path=None,
        apply=False,
        zstd_path=Path(ZSTD),
        shard_max_bytes=16 * 1024,
        minimum_free_reserve_bytes=0,
    )

    after = source.stat()
    assert result["status"] == "DRY_RUN_NO_MUTATION"
    assert result["mutation_applied"] is False
    assert verify_manifest_self_hash(result) == result["self_hash"]["sha256"]
    assert source.read_bytes() == original
    assert (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) == (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
    )
    assert not cold_archive_dir(source).exists()
    assert not list(tmp_path.glob(f".{source.name}.cold-*"))


def test_invalid_json_fails_initial_semantic_scan_before_any_mutation(
    tmp_path: Path,
) -> None:
    source = tmp_path / "ledger.jsonl"
    original = b'{"valid":true}\n{"invalid":\n'
    source.write_bytes(original)
    operation_path = tmp_path / "operation.json"

    with pytest.raises(ColdEvidenceError, match="cold_logical_invalid_jsonl"):
        _apply(source, operation_path)

    assert source.read_bytes() == original
    assert not operation_path.exists()
    assert not cold_archive_dir(source).exists()
    assert not list(tmp_path.glob(f".{source.name}.cold-*"))


def test_non_object_json_fails_initial_semantic_scan_before_any_mutation(
    tmp_path: Path,
) -> None:
    source = tmp_path / "ledger.jsonl"
    original = b'{"valid":true}\n42\n'
    source.write_bytes(original)
    operation_path = tmp_path / "operation.json"

    with pytest.raises(ColdEvidenceError, match="cold_logical_jsonl_row_not_object"):
        _apply(source, operation_path)

    assert source.read_bytes() == original
    assert not operation_path.exists()
    assert not cold_archive_dir(source).exists()
    assert not list(tmp_path.glob(f".{source.name}.cold-*"))


def test_binary_identity_scan_uses_bounded_reads_without_line_iteration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    chunk_bytes = 7
    payload = b"009abcdefghijklmnopqrstuvwxyz"

    class ChunkOnlyStream(io.BytesIO):
        def __init__(self, content: bytes) -> None:
            super().__init__(content)
            self.read_sizes: list[int] = []

        def __iter__(self) -> object:
            raise AssertionError("identity scan must not iterate lines")

        def readline(self, *args: object, **kwargs: object) -> bytes:
            raise AssertionError("identity scan must not call readline")

        def read(self, size: int = -1) -> bytes:
            assert 0 < size <= chunk_bytes
            self.read_sizes.append(size)
            return super().read(size)

    monkeypatch.setattr(archiver, "HASH_CHUNK_BYTES", chunk_bytes)
    stream = ChunkOnlyStream(payload)

    observed = archiver._scan_binary_identity_stream(stream)

    assert observed == {
        "logical_bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }
    assert len(stream.read_sizes) > 2
    assert set(stream.read_sizes) == {chunk_bytes}


def test_bounded_locked_line_reader_batches_raw_reads_and_rewinds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    buffer_bytes = 128
    payload = _jsonl(row_count=80, payload_bytes=12)

    class CountingRaw(io.RawIOBase):
        def __init__(self, content: bytes) -> None:
            super().__init__()
            self.stream = io.BytesIO(content)
            self.readinto_sizes: list[int] = []

        def readable(self) -> bool:
            return True

        def seekable(self) -> bool:
            return True

        def readinto(self, buffer: object) -> int:
            self.readinto_sizes.append(len(buffer))
            return self.stream.readinto(buffer)

        def seek(self, offset: int, whence: int = os.SEEK_SET) -> int:
            return self.stream.seek(offset, whence)

        def tell(self) -> int:
            return self.stream.tell()

    monkeypatch.setattr(archiver, "SOURCE_LINE_BUFFER_BYTES", buffer_bytes)
    raw = CountingRaw(payload)

    with archiver._buffered_locked_line_reader(raw) as reader:
        assert isinstance(reader, io.BufferedReader)
        assert reader.raw is raw
        semantic = archiver.scan_jsonl_binary_stream(reader, parse_json=True)

    maximum_reads = (len(payload) + buffer_bytes - 1) // buffer_bytes + 1
    assert semantic == {
        "logical_bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "physical_line_count": 80,
        "json_object_row_count": 80,
        "blank_line_count": 0,
        "ends_with_lf": True,
    }
    assert 1 < len(raw.readinto_sizes) <= maximum_reads
    assert len(raw.readinto_sizes) * 8 < len(payload)
    assert set(raw.readinto_sizes) == {buffer_bytes}
    assert raw.tell() == 0
    assert not raw.closed

    raw.readinto_sizes.clear()
    observed_lines: list[bytes] = []
    with archiver._buffered_locked_line_reader(raw) as reader:
        while True:
            line = reader.readline(4097)
            if not line:
                break
            observed_lines.append(line)

    assert b"".join(observed_lines) == payload
    assert 1 < len(raw.readinto_sizes) <= maximum_reads
    assert len(raw.readinto_sizes) * 8 < len(payload)
    assert set(raw.readinto_sizes) == {buffer_bytes}
    assert raw.tell() == 0
    assert not raw.closed


def test_buffered_line_reader_failure_preserves_lock_and_raw_inode_lifetime(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "ledger.jsonl"
    original = _jsonl(row_count=80, payload_bytes=32)
    source.write_bytes(original)
    monkeypatch.setattr(archiver, "SOURCE_LINE_BUFFER_BYTES", 1024)
    handle, initial_stat = archiver._lock_source(source, tmp_path.resolve())
    backup = source.with_name("ledger.jsonl.test-backup")

    try:
        with pytest.raises(RuntimeError, match="injected_buffered_read_failure"):
            with archiver._buffered_locked_line_reader(handle) as reader:
                first_line = reader.readline()
                assert first_line == original.splitlines(keepends=True)[0]
                assert reader.raw is handle
                assert handle.tell() > reader.tell()
                raise RuntimeError("injected_buffered_read_failure")

        assert not handle.closed
        assert handle.tell() == 0
        assert archiver._source_identity(os.fstat(handle.fileno())) == (
            archiver._source_identity(initial_stat)
        )

        with source.open("rb", buffering=0) as contender:
            with pytest.raises(BlockingIOError):
                fcntl.flock(contender.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

        os.replace(source, backup)
        assert not source.exists()
        assert archiver._source_identity(os.fstat(handle.fileno())) == (
            archiver._source_identity(backup.stat())
        )
        assert archiver._scan_locked_source_identity(handle) == {
            "logical_bytes": len(original),
            "sha256": hashlib.sha256(original).hexdigest(),
        }
        os.replace(backup, source)
        assert archiver._source_identity(source.stat()) == (
            archiver._source_identity(initial_stat)
        )
    finally:
        if backup.exists() and not source.exists():
            os.replace(backup, source)
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


def test_buffered_failure_discards_read_ahead_before_identity_rehash(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "ledger.jsonl"
    original = _jsonl(row_count=80, payload_bytes=32)
    changed = original.replace(b'"row":0', b'"row":9', 1)
    assert len(changed) == len(original)
    source.write_bytes(original)
    plan = archiver.scan_jsonl_binary_stream(io.BytesIO(original), parse_json=True)
    monkeypatch.setattr(archiver, "SOURCE_LINE_BUFFER_BYTES", len(original) * 2)
    handle, initial_stat = archiver._lock_source(source, tmp_path.resolve())

    try:
        with pytest.raises(RuntimeError, match="injected_after_read_ahead"):
            with archiver._buffered_locked_line_reader(handle) as reader:
                assert reader.readline() == original.splitlines(keepends=True)[0]
                assert handle.tell() == len(original)
                assert reader.tell() < handle.tell()
                with source.open("r+b", buffering=0) as writer:
                    writer.seek(0)
                    writer.write(changed)
                    writer.flush()
                    os.fsync(writer.fileno())
                raise RuntimeError("injected_after_read_ahead")

        assert handle.tell() == 0
        state = archiver.SourceState(
            path=source,
            handle=handle,
            initial_fstat=initial_stat,
            plan=plan,
            archive_dir=cold_archive_dir(source),
            staging_dir=tmp_path / ".ledger.jsonl.cold-staging-test",
            backup_path=tmp_path / ".ledger.jsonl.cold-original-backup-test",
            entry={},
        )
        with pytest.raises(
            archiver.DemotionRefusal,
            match="source_locked_rehash_mismatch:.*sha256",
        ):
            archiver._verify_locked_source_unchanged(state)
    finally:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


def test_apply_semantically_parses_each_source_once_then_uses_identity_scans(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = tmp_path / "first.jsonl"
    second = tmp_path / "second.jsonl"
    first.write_bytes(_jsonl(row_count=140))
    second.write_bytes(_jsonl(row_count=160))
    operation_path = tmp_path / "operation.json"
    original_scan = archiver.scan_jsonl_binary_stream
    parse_modes: list[bool] = []

    def recording_scan(handle: object, *, parse_json: bool = True) -> dict[str, object]:
        parse_modes.append(parse_json)
        return original_scan(handle, parse_json=parse_json)

    monkeypatch.setattr(archiver, "scan_jsonl_binary_stream", recording_scan)
    result = archiver.demote_jsonl_paths(
        paths=[second, first],
        repo_root=tmp_path,
        allowed_root=tmp_path,
        operation_manifest_path=operation_path,
        apply=True,
        zstd_path=Path(ZSTD),
        compression_level=3,
        shard_max_bytes=16 * 1024,
        minimum_free_reserve_bytes=0,
    )

    assert result["status"] == archiver.OPERATION_PASS
    assert parse_modes == [True, True]
    assert not first.exists()
    assert not second.exists()
    assert result["contract"][
        "initial_full_source_json_object_validation_required"
    ] is True
    assert result["contract"][
        "later_full_reverification_reuses_semantic_validation_via_exact_byte_identity"
    ] is True
    assert result["contract"][
        "later_identity_reverification_uses_bounded_binary_chunks"
    ] is True
    assert result["contract"][
        "line_row_blank_and_terminal_lf_metadata_inherited_after_exact_byte_identity"
    ] is True

    for source in (first, second):
        manifest = json.loads(
            (cold_archive_dir(source) / "manifest.json").read_text(encoding="utf-8")
        )
        assert manifest["verification"][
            "initial_source_full_json_object_validation_required"
        ] is True
        assert manifest["verification"][
            "post_validation_reverification_by_exact_byte_identity_required"
        ] is True
        assert manifest["verification"][
            "post_validation_identity_reverification_uses_bounded_binary_chunks"
        ] is True
        assert manifest["verification"][
            "line_row_blank_and_terminal_lf_metadata_inherited_after_exact_byte_identity"
        ] is True

    for entry in result["entries"]:
        plan = entry["logical_plan"]
        expected_identity = {
            "logical_bytes": plan["logical_bytes"],
            "sha256": plan["sha256"],
        }
        expected_semantics = {
            key: plan[key] for key in archiver.SEMANTIC_IDENTITY_KEYS
        }
        assert entry["staged_archive"]["identity_reverification"] == expected_identity
        assert entry["final_archive"]["identity_reverification"] == expected_identity
        assert entry["source_locked_identity_reverification_before_rename"] == (
            expected_identity
        )
        assert entry["original_backup_identity_reverification"] == expected_identity
        assert entry["staged_archive"][
            "semantic_metadata_inherited_from_initial_locked_scan"
        ] == expected_semantics
        assert entry["final_archive"][
            "semantic_metadata_inherited_from_initial_locked_scan"
        ] == expected_semantics


def test_equal_size_post_validation_drift_is_rejected_by_sha(
    tmp_path: Path,
) -> None:
    source = tmp_path / "ledger.jsonl"
    valid = b'{"a":1}\n'
    equal_size_invalid = b"notjson\n"
    assert len(equal_size_invalid) == len(valid)
    source.write_bytes(valid)
    plan = archiver.scan_jsonl_binary_stream(io.BytesIO(valid), parse_json=True)
    entry: dict[str, object] = {}
    state = archiver.SourceState(
        path=source,
        handle=io.BytesIO(equal_size_invalid),
        initial_fstat=source.stat(),
        plan=plan,
        archive_dir=cold_archive_dir(source),
        staging_dir=tmp_path / ".ledger.jsonl.cold-staging-test",
        backup_path=tmp_path / ".ledger.jsonl.cold-original-backup-test",
        entry=entry,
    )
    zstd_path = Path(ZSTD).resolve(strict=True)

    with pytest.raises(
        archiver.DemotionRefusal,
        match="source_changed_between_plan_and_archive:.*:sha256:",
    ):
        archiver._build_archive(
            state,
            zstd_path=zstd_path,
            zstd_identity=archiver._zstd_identity(zstd_path),
            level=3,
            shard_max_bytes=4096,
            minimum_free_reserve_bytes=0,
        )

    assert source.read_bytes() == valid
    assert not cold_archive_dir(source).exists()


def test_locked_pre_rename_identity_rehash_rejects_same_size_drift_by_sha(
    tmp_path: Path,
) -> None:
    source = tmp_path / "ledger.jsonl"
    original = b'{"a":1}\n'
    changed = b'{"b":2}\n'
    assert len(changed) == len(original)
    source.write_bytes(original)
    plan = archiver.scan_jsonl_binary_stream(io.BytesIO(original), parse_json=True)
    source.write_bytes(changed)

    with source.open("rb", buffering=0) as handle:
        state = archiver.SourceState(
            path=source,
            handle=handle,
            initial_fstat=source.stat(),
            plan=plan,
            archive_dir=cold_archive_dir(source),
            staging_dir=tmp_path / ".ledger.jsonl.cold-staging-test",
            backup_path=tmp_path / ".ledger.jsonl.cold-original-backup-test",
            entry={},
        )
        with pytest.raises(
            archiver.DemotionRefusal,
            match="source_locked_rehash_mismatch:.*sha256",
        ):
            archiver._verify_locked_source_unchanged(state)


def test_blank_lines_and_missing_terminal_lf_preserve_exact_identity(
    tmp_path: Path,
) -> None:
    source = tmp_path / "ledger.jsonl"
    original = b'{"a":1}\n\n \n{"b":2}'
    source.write_bytes(original)

    result = _apply(source, tmp_path / "operation.json")

    assert result["status"] == archiver.OPERATION_PASS
    manifest = json.loads(
        (cold_archive_dir(source) / "manifest.json").read_text(encoding="utf-8")
    )
    logical = manifest["logical_source"]
    assert logical["logical_bytes"] == len(original)
    assert logical["sha256"] == hashlib.sha256(original).hexdigest()
    assert logical["physical_line_count"] == 4
    assert logical["json_object_row_count"] == 2
    assert logical["blank_line_count"] == 2
    assert logical["ends_with_lf"] is False
    resolver = RawOrColdResolver(zstd_path=Path(ZSTD))
    with resolver.open_binary(source) as handle:
        assert handle.read() == original


def test_apply_round_trip_seek_lines_and_manifest_proofs(tmp_path: Path) -> None:
    source = tmp_path / "ledger.jsonl"
    original = _jsonl()
    original_sha = hashlib.sha256(original).hexdigest()
    source.write_bytes(original)
    operation_path = tmp_path / "operation.json"

    result = _apply(source, operation_path)

    archive_dir = cold_archive_dir(source)
    manifest_path = archive_dir / "manifest.json"
    assert result["status"] == archiver.OPERATION_PASS
    assert result["mutation_applied"] is True
    assert not source.exists()
    assert archive_dir.is_dir()
    assert operation_path.is_file()
    assert not list(tmp_path.glob(f".{source.name}.cold-*"))

    operation = json.loads(operation_path.read_text(encoding="utf-8"))
    assert verify_manifest_self_hash(operation) == operation["self_hash"]["sha256"]
    verified = verify_archive_structure(
        manifest_path,
        expected_logical_path=source,
        verify_compressed_hashes=True,
    )
    manifest = verified.manifest
    assert manifest["status"] == ARCHIVE_PASS_STATUS
    assert manifest["logical_source"]["logical_bytes"] == len(original)
    assert manifest["logical_source"]["sha256"] == original_sha
    assert len(manifest["shards"]) > 1
    assert all(
        shard["uncompressed_bytes"] <= 16 * 1024
        for shard in manifest["shards"]
    )
    assert sum(shard["uncompressed_bytes"] for shard in manifest["shards"]) == len(
        original
    )

    resolver = RawOrColdResolver(zstd_path=Path(ZSTD))
    assert resolver.exists(source)
    assert resolver.mode(source) == "cold"
    with resolver.open_binary(source) as handle:
        assert handle.seekable()
        assert handle.tell() == 0
        assert handle.read() == original
        assert handle.tell() == len(original)
        for offset in (
            0,
            1,
            len(original) // 2,
            int(manifest["shards"][0]["logical_end_offset_exclusive"]),
            len(original) - 37,
            len(original),
        ):
            assert handle.seek(offset, os.SEEK_SET) == offset
            assert handle.tell() == offset
            assert handle.read(31) == original[offset : offset + 31]
        assert handle.seek(-20, os.SEEK_END) == len(original) - 20
        assert handle.read() == original[-20:]

    assert b"".join(resolver.iter_binary_lines(source)) == original
    with resolver.open_text(source) as text_handle:
        assert text_handle.readline() == original.splitlines(keepends=True)[0].decode()
    metadata = resolver.logical_metadata(source, verify_full=True)
    assert metadata["storage_mode"] == "cold_zstd_shards"
    assert metadata["logical_bytes"] == len(original)
    assert metadata["sha256"] == original_sha
    assert metadata["json_object_row_count"] == 700
    assert metadata["full_logical_reverification"] is True


def test_raw_resolver_and_raw_cold_ambiguity_refuse(tmp_path: Path) -> None:
    source = tmp_path / "ledger.jsonl"
    original = _jsonl(row_count=30)
    source.write_bytes(original)
    resolver = RawOrColdResolver(zstd_path=Path(ZSTD))

    assert resolver.mode(source) == "raw"
    with resolver.open_binary(source) as handle:
        assert handle.seekable()
        assert handle.read() == original

    _apply(source, tmp_path / "operation.json")
    source.write_bytes(original)
    with pytest.raises(ColdEvidenceError, match="raw_and_cold_evidence_ambiguous"):
        resolver.mode(source)
    with pytest.raises(ColdEvidenceError, match="raw_and_cold_evidence_ambiguous"):
        resolver.exists(source)
    with pytest.raises(ColdEvidenceError, match="raw_and_cold_evidence_ambiguous"):
        resolver.open_binary(source)


def test_compressed_shard_tamper_is_detected_before_read(tmp_path: Path) -> None:
    source = tmp_path / "ledger.jsonl"
    source.write_bytes(_jsonl(row_count=100))
    _apply(source, tmp_path / "operation.json")
    archive_dir = cold_archive_dir(source)
    shard = sorted(archive_dir.glob("part-*.jsonl.zst"))[0]
    data = bytearray(shard.read_bytes())
    data[len(data) // 2] ^= 0x01
    shard.write_bytes(data)

    resolver = RawOrColdResolver(zstd_path=Path(ZSTD))
    with pytest.raises(ColdEvidenceError, match="compressed_hash_mismatch"):
        resolver.open_binary(source)


def test_same_length_recompressed_shard_tamper_hits_uncompressed_hash_guard(
    tmp_path: Path,
) -> None:
    source = tmp_path / "ledger.jsonl"
    source.write_bytes(_jsonl(row_count=100))
    _apply(source, tmp_path / "operation.json")
    archive_dir = cold_archive_dir(source)
    manifest_path = archive_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    shard_record = manifest["shards"][0]
    shard_path = archive_dir / shard_record["name"]
    raw_path = tmp_path / "tampered-shard.jsonl"
    decompressed = archiver.subprocess.run(
        [str(ZSTD), "-q", "-d", "-c", str(shard_path)],
        check=True,
        capture_output=True,
    ).stdout
    tampered = bytearray(decompressed)
    tampered[0] ^= 0x01
    assert len(tampered) == shard_record["uncompressed_bytes"]
    raw_path.write_bytes(tampered)
    recompressed = archiver.subprocess.run(
        [
            str(ZSTD),
            "-q",
            "--threads=1",
            "-3",
            "--check",
            "-f",
            str(raw_path),
            "-o",
            str(shard_path),
        ],
        check=False,
        capture_output=True,
    )
    assert recompressed.returncode == 0, recompressed.stderr
    shard_record["compressed_bytes"] = shard_path.stat().st_size
    shard_record["compressed_sha256"] = archiver.sha256_file(shard_path)
    archiver.seal_manifest(manifest)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    # The stored-byte manifest is coherent, but the declared uncompressed
    # content hash remains the original and must reject this equal-size swap.
    verify_archive_structure(
        manifest_path,
        expected_logical_path=source,
        verify_compressed_hashes=True,
    )
    resolver = RawOrColdResolver(zstd_path=Path(ZSTD))
    with pytest.raises(ColdEvidenceError, match="uncompressed_hash_mismatch"):
        with resolver.open_binary(source) as handle:
            handle.read()


def test_appended_valid_zstd_frame_is_rejected_at_declared_logical_eof(
    tmp_path: Path,
) -> None:
    source = tmp_path / "ledger.jsonl"
    source.write_bytes(_jsonl(row_count=100))
    _apply(source, tmp_path / "operation.json")
    archive_dir = cold_archive_dir(source)
    manifest_path = archive_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    shard_record = manifest["shards"][0]
    shard_path = archive_dir / shard_record["name"]
    extra_raw = tmp_path / "extra-frame.jsonl"
    extra_frame = tmp_path / "extra-frame.jsonl.zst"
    extra_raw.write_bytes(b'{"appended_valid_frame":true}\n')
    result = archiver.subprocess.run(
        [
            str(ZSTD),
            "-q",
            "--threads=1",
            "-3",
            "--check",
            str(extra_raw),
            "-o",
            str(extra_frame),
        ],
        check=False,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    with shard_path.open("ab") as handle:
        handle.write(extra_frame.read_bytes())
    shard_record["compressed_bytes"] = shard_path.stat().st_size
    shard_record["compressed_sha256"] = archiver.sha256_file(shard_path)
    archiver.seal_manifest(manifest)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    # Stored-byte structure and its resealed manifest are internally coherent;
    # only an exact logical EOF check can expose the appended valid frame.
    verify_archive_structure(
        manifest_path,
        expected_logical_path=source,
        verify_compressed_hashes=True,
    )
    resolver = RawOrColdResolver(zstd_path=Path(ZSTD))
    with pytest.raises(ColdEvidenceError, match="uncompressed_overflow"):
        with resolver.open_binary(source) as handle:
            handle.read()
    with pytest.raises(ColdEvidenceError, match="uncompressed_overflow"):
        resolver.logical_metadata(source, verify_full=True)


def test_manifest_tamper_and_extra_archive_entry_are_detected(tmp_path: Path) -> None:
    source = tmp_path / "ledger.jsonl"
    source.write_bytes(_jsonl(row_count=100))
    _apply(source, tmp_path / "operation.json")
    archive_dir = cold_archive_dir(source)
    manifest_path = archive_dir / "manifest.json"
    original_manifest = manifest_path.read_bytes()

    manifest = json.loads(original_manifest)
    manifest["logical_source"]["logical_bytes"] += 1
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ColdEvidenceError, match="self_hash_invalid"):
        verify_archive_structure(manifest_path, expected_logical_path=source)

    manifest_path.write_bytes(original_manifest)
    (archive_dir / "unexpected.tmp").write_bytes(b"unexpected")
    with pytest.raises(ColdEvidenceError, match="directory_entries_invalid"):
        verify_archive_structure(manifest_path, expected_logical_path=source)


def test_final_archive_failure_rolls_back_exact_original(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "ledger.jsonl"
    original = _jsonl(row_count=200)
    source.write_bytes(original)
    before = source.stat()
    operation_path = tmp_path / "operation.json"

    def fail_final(*args: object, **kwargs: object) -> dict[str, object]:
        raise archiver.DemotionRefusal("injected_final_archive_failure")

    monkeypatch.setattr(archiver, "_verify_final_archive", fail_final)
    with pytest.raises(archiver.DemotionRefusal, match="injected_final_archive_failure"):
        _apply(source, operation_path)

    after = source.stat()
    assert source.read_bytes() == original
    assert (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) == (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
    )
    assert not cold_archive_dir(source).exists()
    assert not list(tmp_path.glob(f".{source.name}.cold-*"))
    operation = json.loads(operation_path.read_text(encoding="utf-8"))
    assert operation["status"] == "FAILED_SAFE_ORIGINAL_RAW_PATHS_RESTORED"
    assert operation["entries"][0]["rollback_status"] == (
        "ORIGINAL_RAW_PATH_RESTORED_VERIFIED"
    )
    verify_manifest_self_hash(operation)


def test_oversized_line_fails_before_source_mutation_and_cleans_staging(
    tmp_path: Path,
) -> None:
    source = tmp_path / "ledger.jsonl"
    original = json.dumps({"payload": "x" * 5000}).encode() + b"\n"
    source.write_bytes(original)
    operation_path = tmp_path / "operation.json"

    with pytest.raises(archiver.DemotionRefusal, match="source_line_exceeds_shard_limit"):
        _apply(source, operation_path, shard_max_bytes=4096)

    assert source.read_bytes() == original
    assert not cold_archive_dir(source).exists()
    assert not list(tmp_path.glob(f".{source.name}.cold-*"))
    operation = json.loads(operation_path.read_text(encoding="utf-8"))
    assert operation["status"] == "FAILED_SAFE_ORIGINAL_RAW_PATHS_RESTORED"
    verify_manifest_self_hash(operation)


def test_multi_source_final_failure_rolls_back_every_original(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first = tmp_path / "first.jsonl"
    second = tmp_path / "second.jsonl"
    originals = {first: _jsonl(row_count=90), second: _jsonl(row_count=110)}
    for path, content in originals.items():
        path.write_bytes(content)
    operation_path = tmp_path / "operation.json"
    original_verify = archiver._verify_final_archive
    call_count = 0

    def fail_second(*args: object, **kwargs: object) -> dict[str, object]:
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            raise archiver.DemotionRefusal("injected_second_archive_failure")
        return original_verify(*args, **kwargs)

    monkeypatch.setattr(archiver, "_verify_final_archive", fail_second)
    with pytest.raises(archiver.DemotionRefusal, match="injected_second_archive_failure"):
        archiver.demote_jsonl_paths(
            paths=[second, first],
            repo_root=tmp_path,
            allowed_root=tmp_path,
            operation_manifest_path=operation_path,
            apply=True,
            zstd_path=Path(ZSTD),
            compression_level=3,
            shard_max_bytes=16 * 1024,
            minimum_free_reserve_bytes=0,
        )

    for path, content in originals.items():
        assert path.read_bytes() == content
        assert not cold_archive_dir(path).exists()
        assert not list(tmp_path.glob(f".{path.name}.cold-*"))
    operation = json.loads(operation_path.read_text(encoding="utf-8"))
    assert operation["status"] == "FAILED_SAFE_ORIGINAL_RAW_PATHS_RESTORED"
    assert all(
        entry["rollback_status"] == "ORIGINAL_RAW_PATH_RESTORED_VERIFIED"
        for entry in operation["entries"]
    )


def test_canonical_raw_path_guard_blocks_path_based_recreation_until_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "ledger.jsonl"
    original = _jsonl(row_count=120)
    source.write_bytes(original)
    operation_path = tmp_path / "operation.json"
    original_verify = archiver._verify_final_archive
    attempts = 0

    def attempt_recreation(*args: object, **kwargs: object) -> dict[str, object]:
        nonlocal attempts
        state = args[0]
        attempts += 1
        assert state.path.is_dir()
        with pytest.raises(IsADirectoryError):
            state.path.write_bytes(b'{"producer_recreated":true}\n')
        return original_verify(*args, **kwargs)

    monkeypatch.setattr(archiver, "_verify_final_archive", attempt_recreation)
    result = _apply(source, operation_path)

    assert attempts == 1
    assert result["status"] == archiver.OPERATION_PASS
    assert not source.exists()
    assert cold_archive_dir(source).is_dir()
    assert not list(tmp_path.glob(f".{source.name}.cold-*"))
    recorded = json.loads(operation_path.read_text(encoding="utf-8"))
    guard = recorded["entries"][0]["canonical_raw_path_guard"]
    assert guard["status"] == "REMOVED_AFTER_VERIFIED_COLD_COMMIT"


def test_raw_path_reappearance_after_guard_removal_never_returns_pass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "ledger.jsonl"
    original = _jsonl(row_count=120)
    source.write_bytes(original)
    operation_path = tmp_path / "operation.json"
    original_remove = archiver._remove_canonical_path_guard

    def remove_then_recreate(state: archiver.SourceState) -> None:
        original_remove(state)
        state.path.write_bytes(b'{"producer_recreated":true}\n')

    monkeypatch.setattr(
        archiver,
        "_remove_canonical_path_guard",
        remove_then_recreate,
    )
    with pytest.raises(
        archiver.DemotionRefusal,
        match="canonical_raw_path_reappeared_during_cold_commit",
    ):
        _apply(source, operation_path)

    recorded = json.loads(operation_path.read_text(encoding="utf-8"))
    assert recorded["status"] == (
        "FAILED_RECORDING_AFTER_VERIFIED_COLD_COMMIT_ARCHIVES_PRESERVED"
    )
    assert recorded["status"] != archiver.OPERATION_PASS
    assert recorded["post_commit_archive_preservation"] is True
    assert source.is_file()
    assert cold_archive_dir(source).is_dir()
    assert recorded["entries"][0]["final_archive"]["logical_reverification"][
        "sha256"
    ] == hashlib.sha256(original).hexdigest()


def test_post_commit_manifest_failure_preserves_verified_cold_archive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "ledger.jsonl"
    original = _jsonl(row_count=150)
    source.write_bytes(original)
    operation_path = tmp_path / "operation.json"
    original_checkpoint = archiver._checkpoint

    def fail_pass_checkpoint(
        path: Path | None, operation: dict[str, object], *, apply: bool
    ) -> None:
        if operation.get("status") in {
            archiver.OPERATION_PASS,
            "PASS_COLD_DEMOTION_VERIFIED_BACKUPS_RETAINED",
        }:
            raise OSError("injected_post_commit_manifest_failure")
        original_checkpoint(path, operation, apply=apply)

    monkeypatch.setattr(archiver, "_checkpoint", fail_pass_checkpoint)
    with pytest.raises(OSError, match="injected_post_commit_manifest_failure"):
        _apply(source, operation_path)

    assert not source.exists()
    assert cold_archive_dir(source).is_dir()
    assert not list(tmp_path.glob(f".{source.name}.cold-*"))
    resolver = RawOrColdResolver(zstd_path=Path(ZSTD))
    with resolver.open_binary(source) as handle:
        assert handle.read() == original
    recorded_failure = json.loads(operation_path.read_text(encoding="utf-8"))
    assert recorded_failure["status"] == (
        "FAILED_RECORDING_AFTER_VERIFIED_COLD_COMMIT_ARCHIVES_PRESERVED"
    )
    assert recorded_failure["post_commit_archive_preservation"] is True
    assert recorded_failure["entries"][0]["status"] == "COLD_DEMOTION_VERIFIED"
    verify_manifest_self_hash(recorded_failure)


def test_source_through_symlinked_parent_is_outside_allowed_root(tmp_path: Path) -> None:
    allowed = tmp_path / "allowed"
    outside = tmp_path / "outside"
    allowed.mkdir()
    outside.mkdir()
    source = outside / "ledger.jsonl"
    source.write_bytes(_jsonl(row_count=2))
    (allowed / "escape").symlink_to(outside, target_is_directory=True)

    with pytest.raises(archiver.DemotionRefusal, match="parent_escapes_allowed_root"):
        archiver.demote_jsonl_paths(
            paths=[allowed / "escape" / source.name],
            repo_root=tmp_path,
            allowed_root=allowed,
            operation_manifest_path=None,
            apply=False,
            zstd_path=Path(ZSTD),
            shard_max_bytes=4096,
            minimum_free_reserve_bytes=0,
        )
    assert source.is_file()
    assert not cold_archive_dir(source).exists()
