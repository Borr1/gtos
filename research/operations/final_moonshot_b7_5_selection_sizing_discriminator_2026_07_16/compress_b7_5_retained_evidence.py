#!/usr/bin/env python3
"""Reclaim APFS space without changing retained replay evidence bytes.

This utility is intentionally fail closed.  It copies each explicitly named
regular file through ``ditto --hfsCompression``, proves byte and metadata
equality, and only then atomically replaces the original path.  A self-hashed
JSON manifest records every pre/post observation.

Dry-run is the default.  ``--apply`` is required for filesystem mutation.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import stat
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence


SCHEMA = "gtos.b7_5.retained_evidence_apfs_compression.v1"
TERMINAL_PASS = "PASS_EVIDENCE_BYTES_PRESERVED_STORAGE_RECLAIMED"
UF_COMPRESSED = getattr(stat, "UF_COMPRESSED", 0x00000020)
COMPRESSION_XATTRS = frozenset({"com.apple.decmpfs"})
HASH_CHUNK_BYTES = 8 * 1024 * 1024
# Empirically proven on this host: ditto exits zero but omits UF_COMPRESSED
# above this exact logical-size boundary.  Refuse before copying or hashing a
# source that cannot satisfy the transparent-compression contract.
MAX_DITTO_HFS_COMPRESSION_SOURCE_BYTES = 512 * 1024 * 1024


class CompressionRefusal(RuntimeError):
    """Raised when a safety invariant prevents compression."""


def _canonical_json_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb", buffering=0) as handle:
        return _sha256_handle(handle)


def _sha256_handle(handle: Any) -> str:
    digest = hashlib.sha256()
    handle.seek(0)
    while chunk := handle.read(HASH_CHUNK_BYTES):
        digest.update(chunk)
    return digest.hexdigest()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _physical_bytes(file_stat: os.stat_result) -> int:
    return int(getattr(file_stat, "st_blocks", 0)) * 512


def _xattr_digests(path: Path) -> dict[str, str]:
    if not hasattr(os, "listxattr"):
        listed = subprocess.run(
            ["/usr/bin/xattr", str(path)],
            check=False,
            capture_output=True,
        )
        if listed.returncode != 0:
            raise CompressionRefusal(
                f"cannot list xattrs for {path}: "
                f"{listed.stderr.decode('utf-8', errors='replace').strip()}"
            )
        result: dict[str, str] = {}
        for encoded_name in listed.stdout.splitlines():
            name = encoded_name.decode("utf-8")
            extracted = subprocess.run(
                ["/usr/bin/xattr", "-px", name, str(path)],
                check=False,
                capture_output=True,
            )
            if extracted.returncode != 0:
                raise CompressionRefusal(
                    f"cannot read xattr {name!r} for {path}: "
                    f"{extracted.stderr.decode('utf-8', errors='replace').strip()}"
                )
            try:
                value = bytes.fromhex(extracted.stdout.decode("ascii"))
            except (UnicodeDecodeError, ValueError) as exc:
                raise CompressionRefusal(
                    f"cannot decode xattr {name!r} for {path}"
                ) from exc
            result[name] = _sha256_bytes(value)
        return result
    try:
        names = os.listxattr(path, follow_symlinks=False)
    except OSError as exc:
        raise CompressionRefusal(f"cannot list xattrs for {path}: {exc}") from exc
    result: dict[str, str] = {}
    for name in sorted(names):
        try:
            value = os.getxattr(path, name, follow_symlinks=False)
        except OSError as exc:
            raise CompressionRefusal(
                f"cannot read xattr {name!r} for {path}: {exc}"
            ) from exc
        result[name] = _sha256_bytes(value)
    return result


def _snapshot(path: Path) -> dict[str, Any]:
    file_stat = path.lstat()
    return {
        "device": int(file_stat.st_dev),
        "inode": int(file_stat.st_ino),
        "mode": stat.S_IMODE(file_stat.st_mode),
        "uid": int(file_stat.st_uid),
        "gid": int(file_stat.st_gid),
        "link_count": int(file_stat.st_nlink),
        "logical_bytes": int(file_stat.st_size),
        "physical_bytes": _physical_bytes(file_stat),
        "mtime_ns": int(file_stat.st_mtime_ns),
        "flags": int(getattr(file_stat, "st_flags", 0)),
        "uf_compressed": bool(int(getattr(file_stat, "st_flags", 0)) & UF_COMPRESSED),
        "xattr_sha256": _xattr_digests(path),
    }


def _stable_identity(snapshot: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        snapshot["device"],
        snapshot["inode"],
        snapshot["mode"],
        snapshot["uid"],
        snapshot["gid"],
        snapshot["link_count"],
        snapshot["logical_bytes"],
        snapshot["mtime_ns"],
        snapshot["flags"],
        tuple(sorted(snapshot["xattr_sha256"].items())),
    )


def _assert_source_safe(path: Path, allowed_root: Path) -> None:
    if path.is_symlink():
        raise CompressionRefusal(f"symlink inputs are forbidden: {path}")
    try:
        path.relative_to(allowed_root)
    except ValueError as exc:
        raise CompressionRefusal(
            f"input escapes allowed root {allowed_root}: {path}"
        ) from exc
    if not path.exists():
        raise CompressionRefusal(f"input does not exist: {path}")
    if not path.is_file():
        raise CompressionRefusal(f"input is not a regular file: {path}")
    file_stat = path.lstat()
    if not stat.S_ISREG(file_stat.st_mode):
        raise CompressionRefusal(f"input is not a regular file: {path}")
    if file_stat.st_nlink != 1:
        raise CompressionRefusal(
            f"hard-linked input is forbidden (nlink={file_stat.st_nlink}): {path}"
        )


def _source_plan(path: Path, allowed_root: Path) -> dict[str, Any]:
    _assert_source_safe(path, allowed_root)
    before_hash_snapshot = _snapshot(path)
    if before_hash_snapshot["logical_bytes"] > MAX_DITTO_HFS_COMPRESSION_SOURCE_BYTES:
        raise CompressionRefusal(
            "source_exceeds_proven_ditto_hfs_compression_ceiling:"
            f"{path}:{before_hash_snapshot['logical_bytes']}>"
            f"{MAX_DITTO_HFS_COMPRESSION_SOURCE_BYTES}"
        )
    digest = _sha256_file(path)
    after_hash_snapshot = _snapshot(path)
    if _stable_identity(before_hash_snapshot) != _stable_identity(after_hash_snapshot):
        raise CompressionRefusal(f"input changed while hashing: {path}")
    return {
        "path": str(path),
        "sha256": digest,
        "pre": after_hash_snapshot,
        "status": "PLANNED",
    }


def _assert_preserved_metadata(
    source: Mapping[str, Any],
    copied: Mapping[str, Any],
    path: Path,
) -> None:
    for field in ("mode", "uid", "gid", "logical_bytes", "mtime_ns"):
        if copied[field] != source[field]:
            raise CompressionRefusal(
                f"metadata mismatch for {path}: {field} "
                f"{source[field]!r} != {copied[field]!r}"
            )
    source_xattrs = {
        name: digest
        for name, digest in source["xattr_sha256"].items()
        if name not in COMPRESSION_XATTRS
    }
    copied_xattrs = {
        name: digest
        for name, digest in copied["xattr_sha256"].items()
        if name not in COMPRESSION_XATTRS
    }
    if copied_xattrs != source_xattrs:
        raise CompressionRefusal(f"non-compression xattr mismatch for {path}")
    source_flags = int(source["flags"]) & ~UF_COMPRESSED
    copied_flags = int(copied["flags"]) & ~UF_COMPRESSED
    if copied_flags != source_flags:
        raise CompressionRefusal(
            f"non-compression file flags mismatch for {path}: "
            f"{source_flags} != {copied_flags}"
        )


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


def _manifest_payload(manifest: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in manifest.items() if key != "self_hash_sha256"}


def _seal_manifest(manifest: dict[str, Any]) -> None:
    manifest["self_hash_sha256"] = _sha256_bytes(
        _canonical_json_bytes(_manifest_payload(manifest))
    )


def _write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    _seal_manifest(manifest)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(manifest, handle, indent=2, sort_keys=True, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        _fsync_directory(path.parent)
    finally:
        if temporary.exists():
            temporary.unlink()


def _git_head(repo_root: Path) -> str | None:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return None
    return completed.stdout.strip() or None


def _new_manifest(
    *,
    repo_root: Path,
    allowed_root: Path,
    script_path: Path,
    entries: Sequence[dict[str, Any]],
    apply: bool,
) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "generated_at_utc": _utc_now(),
        "status": "IN_PROGRESS" if apply else "DRY_RUN_NO_MUTATION",
        "mutation_applied": False,
        "repo_root": str(repo_root),
        "repo_head": _git_head(repo_root),
        "allowed_root": str(allowed_root),
        "script_path": str(script_path),
        "script_sha256": _sha256_file(script_path),
        "tool_contract": {
            "copy_command": [
                "/usr/bin/ditto",
                "--hfsCompression",
                "--noclone",
                "--nocache",
                "<source>",
                "<same-directory-temporary>",
            ],
            "atomic_replace_only_after_temp_sha256_equality": True,
            "logical_bytes_must_match": True,
            "source_sha256_must_match_temp_and_final": True,
            "source_noncompression_metadata_must_match": True,
            "uf_compressed_flag_required": True,
            "positive_physical_savings_required": True,
            "maximum_source_logical_bytes": (
                MAX_DITTO_HFS_COMPRESSION_SOURCE_BYTES
            ),
            "broker_runtime_change_status": False,
            "live_activation_status": False,
            "march_outcome_access_status": False,
        },
        "entries": list(entries),
        "totals": {
            "file_count": len(entries),
            "logical_bytes": sum(entry["pre"]["logical_bytes"] for entry in entries),
            "physical_bytes_pre": sum(entry["pre"]["physical_bytes"] for entry in entries),
            "physical_bytes_post": None,
            "physical_bytes_reclaimed": None,
        },
        "failure": None,
    }


def _compress_one(
    entry: dict[str, Any],
    *,
    allowed_root: Path,
    min_savings_bytes: int,
    checkpoint: Callable[[], None],
) -> None:
    source = Path(entry["path"])
    _assert_source_safe(source, allowed_root)
    current = _snapshot(source)
    if _stable_identity(current) != _stable_identity(entry["pre"]):
        raise CompressionRefusal(f"input changed after plan seal: {source}")

    if current["uf_compressed"]:
        current_digest = _sha256_file(source)
        if current_digest != entry["sha256"]:
            raise CompressionRefusal(f"already-compressed input hash changed: {source}")
        entry["post"] = current
        entry["post_sha256"] = current_digest
        entry["physical_bytes_reclaimed"] = 0
        entry["status"] = "ALREADY_COMPRESSED_VERIFIED"
        return

    suffix = source.suffix or ".evidence"
    temporary = source.with_name(
        f".{source.name}.gtos-hfs-compressed-candidate{suffix}"
    )
    backup = source.with_name(f".{source.name}.gtos-hfs-original-backup")
    for recovery_path in (temporary, backup):
        if recovery_path.exists() or recovery_path.is_symlink():
            raise CompressionRefusal(
                f"interrupted-compression recovery path already exists: {recovery_path}"
            )
    entry["recovery_contract"] = {
        "compressed_candidate_path": str(temporary),
        "original_backup_path": str(backup),
        "original_backup_retained_until_final_verification": True,
        "source_rehashed_under_exclusive_advisory_lock_before_replace": True,
        "namespace_quiescence_required": True,
    }
    entry["status"] = "COPYING_COMPRESSED_CANDIDATE"
    checkpoint()
    backup_created = False
    try:
        completed = subprocess.run(
            [
                "/usr/bin/ditto",
                "--hfsCompression",
                "--noclone",
                "--nocache",
                str(source),
                str(temporary),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            raise CompressionRefusal(
                f"ditto failed for {source} with exit {completed.returncode}: "
                f"{completed.stderr.strip()}"
            )
        if not temporary.is_file() or temporary.is_symlink():
            raise CompressionRefusal(f"ditto did not produce a regular file: {temporary}")

        copied = _snapshot(temporary)
        copied_digest = _sha256_file(temporary)
        copied_after_hash = _snapshot(temporary)
        if _stable_identity(copied) != _stable_identity(copied_after_hash):
            raise CompressionRefusal(f"compressed copy changed while hashing: {temporary}")
        if copied_digest != entry["sha256"]:
            raise CompressionRefusal(f"compressed-copy hash mismatch for {source}")
        _assert_preserved_metadata(entry["pre"], copied_after_hash, source)
        if not copied_after_hash["uf_compressed"]:
            raise CompressionRefusal(f"UF_COMPRESSED was not set for {source}")
        reclaimed = entry["pre"]["physical_bytes"] - copied_after_hash["physical_bytes"]
        if reclaimed < min_savings_bytes:
            raise CompressionRefusal(
                f"physical savings below required minimum for {source}: "
                f"{reclaimed} < {min_savings_bytes}"
            )

        _fsync_file(temporary)
        entry["compressed_copy_pre_replace"] = copied_after_hash
        entry["status"] = "COMPRESSED_CANDIDATE_VERIFIED_RECHECKING_SOURCE"
        checkpoint()

        with source.open("rb", buffering=0) as locked_source:
            try:
                fcntl.flock(locked_source.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                raise CompressionRefusal(
                    f"cannot acquire exclusive source lock for {source}: {exc}"
                ) from exc
            locked_before = os.fstat(locked_source.fileno())
            locked_digest = _sha256_handle(locked_source)
            locked_after = os.fstat(locked_source.fileno())
            path_immediately_before_replace = _snapshot(source)
            if (
                locked_before.st_dev != locked_after.st_dev
                or locked_before.st_ino != locked_after.st_ino
                or locked_before.st_size != locked_after.st_size
                or locked_before.st_mtime_ns != locked_after.st_mtime_ns
            ):
                raise CompressionRefusal(f"source changed during locked rehash: {source}")
            if (
                locked_after.st_dev != path_immediately_before_replace["device"]
                or locked_after.st_ino != path_immediately_before_replace["inode"]
            ):
                raise CompressionRefusal(
                    f"source path identity changed before replace: {source}"
                )
            if _stable_identity(path_immediately_before_replace) != _stable_identity(
                entry["pre"]
            ):
                raise CompressionRefusal(
                    f"source metadata changed before replace: {source}"
                )
            if locked_digest != entry["sha256"]:
                raise CompressionRefusal(f"source hash changed before replace: {source}")

            entry["source_immediately_before_replace"] = (
                path_immediately_before_replace
            )
            entry["source_sha256_immediately_before_replace"] = locked_digest
            entry["status"] = "SOURCE_REVERIFIED_ORIGINAL_BACKUP_PENDING"
            checkpoint()

            os.replace(source, backup)
            backup_created = True
            _fsync_directory(source.parent)
            backup_snapshot = _snapshot(backup)
            if _stable_identity(backup_snapshot) != _stable_identity(entry["pre"]):
                raise CompressionRefusal(
                    f"original backup identity mismatch after rename: {backup}"
                )
            entry["original_backup"] = backup_snapshot
            entry["status"] = "ORIGINAL_BACKUP_RETAINED_REPLACING_SOURCE"
            checkpoint()

            os.replace(temporary, source)
            _fsync_directory(source.parent)

        final = _snapshot(source)
        final_digest = _sha256_file(source)
        final_after_hash = _snapshot(source)
        if _stable_identity(final) != _stable_identity(final_after_hash):
            raise CompressionRefusal(f"final file changed while hashing: {source}")
        if final_digest != entry["sha256"]:
            raise CompressionRefusal(f"final hash mismatch after replace: {source}")
        _assert_preserved_metadata(entry["pre"], final_after_hash, source)
        if not final_after_hash["uf_compressed"]:
            raise CompressionRefusal(f"final UF_COMPRESSED flag absent: {source}")

        entry["post"] = final_after_hash
        entry["post_sha256"] = final_digest
        entry["physical_bytes_reclaimed"] = (
            entry["pre"]["physical_bytes"] - final_after_hash["physical_bytes"]
        )
        entry["status"] = "COMPRESSED_VERIFIED_ORIGINAL_BACKUP_PENDING_DELETE"
        checkpoint()

        with backup.open("rb", buffering=0) as locked_backup:
            try:
                fcntl.flock(locked_backup.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                raise CompressionRefusal(
                    f"cannot lock original backup before deletion for {source}: {exc}"
                ) from exc
            backup_before_delete = _snapshot(backup)
            backup_digest_before_delete = _sha256_handle(locked_backup)
            locked_backup_after = os.fstat(locked_backup.fileno())
            backup_after_hash = _snapshot(backup)
            if (
                locked_backup_after.st_dev != backup_after_hash["device"]
                or locked_backup_after.st_ino != backup_after_hash["inode"]
                or _stable_identity(backup_before_delete)
                != _stable_identity(backup_after_hash)
                or _stable_identity(backup_after_hash)
                != _stable_identity(entry["pre"])
            ):
                raise CompressionRefusal(
                    f"original backup changed before deletion: {backup}"
                )
            if backup_digest_before_delete != entry["sha256"]:
                raise CompressionRefusal(
                    f"original backup hash changed before deletion: {backup}"
                )
            entry["original_backup_immediately_before_delete"] = backup_after_hash
            entry["original_backup_sha256_immediately_before_delete"] = (
                backup_digest_before_delete
            )
            backup.unlink()
            backup_created = False
        _fsync_directory(source.parent)
        entry["original_backup_deleted_after_final_verification"] = True
        entry["status"] = "COMPRESSED_VERIFIED"
    finally:
        if backup_created and backup.exists():
            try:
                os.replace(backup, source)
                backup_created = False
                _fsync_directory(source.parent)
                entry["rollback_status"] = "ORIGINAL_BACKUP_RESTORED"
            except OSError as rollback_exc:
                entry["rollback_status"] = (
                    "ORIGINAL_BACKUP_RETAINED_MANUAL_RECOVERY_REQUIRED"
                )
                entry["rollback_error"] = f"{type(rollback_exc).__name__}: {rollback_exc}"
        if temporary.exists():
            temporary.unlink()


def compress_paths(
    *,
    paths: Iterable[Path],
    repo_root: Path,
    allowed_root: Path,
    script_path: Path,
    manifest_path: Path | None,
    apply: bool,
    min_savings_bytes: int,
) -> dict[str, Any]:
    if sys.platform != "darwin":
        raise CompressionRefusal("APFS/HFS transparent compression requires macOS")
    repo_root = repo_root.resolve(strict=True)
    allowed_root = allowed_root.resolve(strict=True)
    lexical_paths = [Path(os.path.abspath(path)) for path in paths]
    for lexical_path in lexical_paths:
        if lexical_path.is_symlink():
            raise CompressionRefusal(f"symlink inputs are forbidden: {lexical_path}")
    resolved_paths = [path.resolve(strict=False) for path in lexical_paths]
    if not resolved_paths:
        raise CompressionRefusal("at least one --path is required")
    if len(set(resolved_paths)) != len(resolved_paths):
        raise CompressionRefusal("duplicate input paths are forbidden")
    if min_savings_bytes < 1:
        raise CompressionRefusal("--min-savings-bytes must be positive")
    if apply and manifest_path is None:
        raise CompressionRefusal("--manifest is required with --apply")
    if manifest_path is not None and manifest_path.exists():
        raise CompressionRefusal(f"refusing to overwrite manifest: {manifest_path}")

    entries = [_source_plan(path, allowed_root) for path in resolved_paths]
    manifest = _new_manifest(
        repo_root=repo_root,
        allowed_root=allowed_root,
        script_path=script_path,
        entries=entries,
        apply=apply,
    )
    _seal_manifest(manifest)
    if not apply:
        return manifest

    assert manifest_path is not None
    manifest_path = manifest_path.resolve(strict=False)
    _write_manifest(manifest_path, manifest)
    try:
        for entry in manifest["entries"]:
            _compress_one(
                entry,
                allowed_root=allowed_root,
                min_savings_bytes=min_savings_bytes,
                checkpoint=lambda: _write_manifest(manifest_path, manifest),
            )
            manifest["mutation_applied"] = any(
                candidate["status"] == "COMPRESSED_VERIFIED"
                for candidate in manifest["entries"]
            )
            _write_manifest(manifest_path, manifest)

        physical_post = sum(entry["post"]["physical_bytes"] for entry in manifest["entries"])
        manifest["totals"]["physical_bytes_post"] = physical_post
        manifest["totals"]["physical_bytes_reclaimed"] = (
            manifest["totals"]["physical_bytes_pre"] - physical_post
        )
        manifest["status"] = TERMINAL_PASS
        manifest["completed_at_utc"] = _utc_now()
        _write_manifest(manifest_path, manifest)
        return manifest
    except BaseException as exc:
        manifest["status"] = "FAILED_SAFE_COMPRESSION_INCOMPLETE"
        manifest["failure"] = f"{type(exc).__name__}: {exc}"
        manifest["completed_at_utc"] = _utc_now()
        _write_manifest(manifest_path, manifest)
        raise


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", action="append", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--allowed-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--min-savings-bytes", type=int, default=1)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        manifest = compress_paths(
            paths=args.path,
            repo_root=args.repo_root,
            allowed_root=args.allowed_root,
            script_path=Path(__file__).resolve(),
            manifest_path=args.manifest,
            apply=args.apply,
            min_savings_bytes=args.min_savings_bytes,
        )
    except (CompressionRefusal, OSError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
