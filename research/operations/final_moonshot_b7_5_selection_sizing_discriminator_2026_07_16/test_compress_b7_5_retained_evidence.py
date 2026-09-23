from __future__ import annotations

import hashlib
import json
import os
import stat
import sys
from pathlib import Path

import pytest

import compress_b7_5_retained_evidence as subject


pytestmark = pytest.mark.skipif(sys.platform != "darwin", reason="macOS-only APFS proof")


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _verify_self_hash(manifest: dict) -> None:
    expected = manifest.pop("self_hash_sha256")
    try:
        actual = hashlib.sha256(subject._canonical_json_bytes(manifest)).hexdigest()
    finally:
        manifest["self_hash_sha256"] = expected
    assert actual == expected


def test_dry_run_hashes_without_mutation(tmp_path: Path) -> None:
    source = tmp_path / "retained.jsonl"
    source.write_bytes((b'{"same":"repetitive evidence row"}\n' * 20_000))
    before = source.stat()

    manifest = subject.compress_paths(
        paths=[source],
        repo_root=tmp_path,
        allowed_root=tmp_path,
        script_path=Path(subject.__file__),
        manifest_path=None,
        apply=False,
        min_savings_bytes=1,
    )

    after = source.stat()
    assert manifest["status"] == "DRY_RUN_NO_MUTATION"
    assert manifest["mutation_applied"] is False
    assert manifest["entries"][0]["sha256"] == _hash(source)
    assert manifest["entries"][0]["status"] == "PLANNED"
    assert before.st_ino == after.st_ino
    assert not (getattr(after, "st_flags", 0) & subject.UF_COMPRESSED)
    _verify_self_hash(manifest)


def test_apply_preserves_bytes_and_writes_verified_manifest(tmp_path: Path) -> None:
    source = tmp_path / "retained.jsonl"
    source.write_bytes((b'{"same":"repetitive evidence row"}\n' * 100_000))
    os.chmod(source, 0o640)
    before_bytes = source.read_bytes()
    before_hash = _hash(source)
    before = source.stat()
    manifest_path = tmp_path / "compression_manifest.json"

    manifest = subject.compress_paths(
        paths=[source],
        repo_root=tmp_path,
        allowed_root=tmp_path,
        script_path=Path(subject.__file__),
        manifest_path=manifest_path,
        apply=True,
        min_savings_bytes=1,
    )

    written = json.loads(manifest_path.read_text(encoding="utf-8"))
    after = source.stat()
    assert manifest == written
    assert source.read_bytes() == before_bytes
    assert _hash(source) == before_hash
    assert stat.S_IMODE(after.st_mode) == stat.S_IMODE(before.st_mode)
    assert after.st_mtime_ns == before.st_mtime_ns
    assert getattr(after, "st_flags", 0) & subject.UF_COMPRESSED
    assert manifest["status"] == subject.TERMINAL_PASS
    assert manifest["mutation_applied"] is True
    assert manifest["entries"][0]["status"] == "COMPRESSED_VERIFIED"
    assert manifest["entries"][0]["sha256"] == before_hash
    assert manifest["entries"][0]["post_sha256"] == before_hash
    assert manifest["totals"]["physical_bytes_reclaimed"] > 0
    _verify_self_hash(manifest)


def test_refuses_symlink_duplicate_escape_and_manifest_overwrite(tmp_path: Path) -> None:
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    source = allowed / "source.jsonl"
    source.write_text('{"row":1}\n', encoding="utf-8")
    link = allowed / "link.jsonl"
    link.symlink_to(source)
    outside = tmp_path / "outside.jsonl"
    outside.write_text('{"row":2}\n', encoding="utf-8")
    manifest = allowed / "manifest.json"
    manifest.write_text("{}\n", encoding="utf-8")

    common = {
        "repo_root": tmp_path,
        "allowed_root": allowed,
        "script_path": Path(subject.__file__),
        "manifest_path": None,
        "apply": False,
        "min_savings_bytes": 1,
    }
    with pytest.raises(subject.CompressionRefusal, match="symlink"):
        subject.compress_paths(paths=[link], **common)
    with pytest.raises(subject.CompressionRefusal, match="duplicate"):
        subject.compress_paths(paths=[source, source], **common)
    with pytest.raises(subject.CompressionRefusal, match="escapes"):
        subject.compress_paths(paths=[outside], **common)
    with pytest.raises(subject.CompressionRefusal, match="overwrite manifest"):
        subject.compress_paths(
            paths=[source],
            **{**common, "manifest_path": manifest, "apply": True},
        )


def test_final_verification_failure_restores_original_inode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "retained.jsonl"
    source.write_bytes((b'{"same":"rollback proof row"}\n' * 100_000))
    before_bytes = source.read_bytes()
    before_hash = _hash(source)
    before = source.stat()
    manifest_path = tmp_path / "rollback_manifest.json"
    real_snapshot = subject._snapshot

    def fail_final_metadata(path: Path) -> dict:
        snapshot = real_snapshot(path)
        if path == source and snapshot["uf_compressed"]:
            snapshot["mode"] ^= 0o001
        return snapshot

    monkeypatch.setattr(subject, "_snapshot", fail_final_metadata)

    with pytest.raises(subject.CompressionRefusal, match="metadata mismatch"):
        subject.compress_paths(
            paths=[source],
            repo_root=tmp_path,
            allowed_root=tmp_path,
            script_path=Path(subject.__file__),
            manifest_path=manifest_path,
            apply=True,
            min_savings_bytes=1,
        )

    after = source.stat()
    written = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert source.read_bytes() == before_bytes
    assert _hash(source) == before_hash
    assert after.st_ino == before.st_ino
    assert not (getattr(after, "st_flags", 0) & subject.UF_COMPRESSED)
    assert written["status"] == "FAILED_SAFE_COMPRESSION_INCOMPLETE"
    assert written["entries"][0]["rollback_status"] == "ORIGINAL_BACKUP_RESTORED"
    assert not list(tmp_path.glob(".*gtos-hfs-original-backup"))
    assert not list(tmp_path.glob(".*gtos-hfs-compressed-candidate*"))
    _verify_self_hash(written)


def test_refuses_above_proven_ditto_ceiling_before_hashing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "too-large.jsonl"
    with source.open("wb") as handle:
        handle.truncate(subject.MAX_DITTO_HFS_COMPRESSION_SOURCE_BYTES + 1)

    def forbidden_hash(_path: Path) -> str:
        raise AssertionError("oversized source must be refused before hashing")

    monkeypatch.setattr(subject, "_sha256_file", forbidden_hash)
    with pytest.raises(
        subject.CompressionRefusal,
        match="source_exceeds_proven_ditto_hfs_compression_ceiling",
    ):
        subject.compress_paths(
            paths=[source],
            repo_root=tmp_path,
            allowed_root=tmp_path,
            script_path=Path(subject.__file__),
            manifest_path=None,
            apply=False,
            min_savings_bytes=1,
        )
