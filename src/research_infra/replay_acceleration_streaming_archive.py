"""Verified streaming archive for amplified real-replay proof ledgers."""

from __future__ import annotations

import hashlib
import json
import math
import os
import resource
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Callable, Mapping


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
RECLAIM_RECOVERY_SCHEMA = (
    "gtos.replay_acceleration.streaming_reclaim_recovery.v1"
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
ROLES = ("decision", "scorecard", "missed")
ARCHIVE_COMPRESSION_CONTROL_RESERVE_BYTES = 64 * 1024 * 1024
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
EMPTY_RAW_CONTRACT = {
    "raw_bytes": 0,
    "raw_rows": 0,
    "raw_sha256": EMPTY_SHA256,
}
VERIFIER_PATH = Path(__file__).with_name(
    "replay_acceleration_streaming_archive_verifier.py"
)


class ArchiveRejected(RuntimeError):
    def __init__(self, code: str) -> None:
        self.code = str(code)
        super().__init__(self.code)


def canonical_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError):
        raise ArchiveRejected("archive_noncanonical_value") from None


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


def _snapshot_regular_file(source: Path, target: Path) -> dict[str, Any]:
    source = Path(source)
    target = Path(target)
    if source.is_symlink() or target.exists() or target.is_symlink():
        raise ArchiveRejected("archive_checkpoint_snapshot_invalid")
    try:
        source_descriptor = os.open(
            source,
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
        )
        target_descriptor = os.open(
            target,
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_NOFOLLOW", 0),
            0o600,
        )
    except OSError:
        try:
            os.close(source_descriptor)
        except (NameError, OSError):
            pass
        raise ArchiveRejected("archive_checkpoint_snapshot_invalid") from None
    digest = hashlib.sha256()
    size = 0
    try:
        while True:
            chunk = os.read(source_descriptor, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            size += len(chunk)
            offset = 0
            while offset < len(chunk):
                written = os.write(target_descriptor, chunk[offset:])
                if written <= 0:
                    raise ArchiveRejected(
                        "archive_checkpoint_snapshot_write_failed"
                    )
                offset += written
        os.fsync(target_descriptor)
    finally:
        os.close(source_descriptor)
        os.close(target_descriptor)
    return {"bytes": size, "sha256": digest.hexdigest()}


def atomic_write(path: Path, value: Mapping[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    descriptor: int | None = None
    try:
        descriptor = os.open(
            temporary,
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_NOFOLLOW", 0),
            0o600,
        )
        payload = canonical_bytes(value) + b"\n"
        offset = 0
        while offset < len(payload):
            written = os.write(descriptor, payload[offset:])
            if written <= 0:
                raise ArchiveRejected("archive_atomic_write_failed")
            offset += written
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = None
        os.replace(temporary, path)
    finally:
        if descriptor is not None:
            os.close(descriptor)
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(
        Path(path),
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0),
    )
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def load_canonical(path: Path) -> dict[str, Any]:
    raw = Path(path).read_bytes()
    value = json.loads(raw)
    if type(value) is not dict or raw != canonical_bytes(value) + b"\n":
        raise ArchiveRejected("archive_artifact_invalid")
    return value


def stream_contract(path: Path) -> dict[str, Any]:
    digest = hashlib.sha256()
    rows = 0
    size = 0
    final = b""
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
            rows += chunk.count(b"\n")
            size += len(chunk)
            final = chunk[-1:]
    if size and final != b"\n":
        raise ArchiveRejected("archive_raw_framing_invalid")
    return {"raw_bytes": size, "raw_rows": rows, "raw_sha256": digest.hexdigest()}


def descriptor_stream_contract(descriptor: int) -> dict[str, Any]:
    digest = hashlib.sha256()
    rows = 0
    size = 0
    final = b""
    offset = 0
    while True:
        chunk = os.pread(descriptor, 1024 * 1024, offset)
        if not chunk:
            break
        digest.update(chunk)
        rows += chunk.count(b"\n")
        size += len(chunk)
        offset += len(chunk)
        final = chunk[-1:]
    if size and final != b"\n":
        raise ArchiveRejected("archive_raw_framing_invalid")
    return {"raw_bytes": size, "raw_rows": rows, "raw_sha256": digest.hexdigest()}


def file_contract(path: Path) -> dict[str, Any]:
    digest = hashlib.sha256()
    size = 0
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
    return {"compressed_bytes": size, "compressed_sha256": digest.hexdigest()}


def planned_zstd_contract(zstd: str, path: Path) -> dict[str, Any]:
    """Measure deterministic zstd output without retaining or writing it."""

    process: subprocess.Popen[bytes] | None = None
    stdout = None
    try:
        process = subprocess.Popen(
            [zstd, "-q", "-1", "-T1", "-c", str(path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        stdout = process.stdout
        if stdout is None:
            raise OSError("compression planner stdout unavailable")
        digest = hashlib.sha256()
        size = 0
        for chunk in iter(lambda: stdout.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
        if process.wait() != 0:
            raise ArchiveRejected("archive_compression_plan_failed")
        return {
            "compressed_bytes": size,
            "compressed_sha256": digest.hexdigest(),
        }
    except ArchiveRejected:
        raise
    except Exception:
        if process is not None and process.returncode is None:
            try:
                process.kill()
            finally:
                process.wait()
        raise ArchiveRejected("archive_compression_plan_failed") from None
    finally:
        if stdout is not None:
            stdout.close()


def tree_bytes(path: Path) -> int:
    return sum(item.stat().st_size for item in Path(path).rglob("*") if item.is_file())


class StreamingProofArchive:
    def __init__(
        self,
        *,
        root: Path,
        output_prefix: str,
        hot_outputs: Mapping[str, Path],
        max_archive_bytes: int,
        hard_floor_free_bytes: int,
        warning_floor_free_bytes: int = 34 * 1024 * 1024 * 1024,
    ) -> None:
        if set(hot_outputs) != set(ROLES):
            raise ArchiveRejected("archive_hot_surface_inventory_invalid")
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.output_prefix = str(output_prefix)
        self.hot_outputs = {role: Path(hot_outputs[role]) for role in ROLES}
        self.max_archive_bytes = int(max_archive_bytes)
        self.hard_floor_free_bytes = int(hard_floor_free_bytes)
        self.warning_floor_free_bytes = int(warning_floor_free_bytes)
        self.campaign_manifest_path = self.root / "CAMPAIGN_ARCHIVE_MANIFEST.json"
        self._shards: list[dict[str, Any]] = []
        self._cumulative_hashes = {role: hashlib.sha256() for role in ROLES}
        self._cumulative_bytes = {role: 0 for role in ROLES}
        self._cumulative_rows = {role: 0 for role in ROLES}
        self._checkpoint_authority: dict[str, Any] | None = None
        self._checkpoint_chain_genesis_root_sha256: str | None = None
        self._checkpoint_chain_root_sha256: str | None = None
        self._metrics: dict[str, int | float] = {
            "compression_seconds": 0.0,
            "verification_seconds": 0.0,
            "hashing_seconds": 0.0,
            "raw_bytes_archived": 0,
            "compressed_bytes_retained": 0,
            "raw_bytes_reclaimed": 0,
            "shard_count": 0,
            "child_user_cpu_seconds": 0.0,
            "child_system_cpu_seconds": 0.0,
        }
        if self.campaign_manifest_path.exists():
            raise ArchiveRejected("archive_root_not_new")
        zstd = shutil.which("zstd")
        if not zstd:
            raise ArchiveRejected("archive_zstd_unavailable")
        self.zstd = zstd
        self.zstd_version = subprocess.check_output(
            [self.zstd, "--version"], text=True
        ).strip()

    def metrics(self) -> dict[str, int | float]:
        return dict(self._metrics)

    def authority(self) -> dict[str, Any]:
        campaign = (
            load_canonical(self.campaign_manifest_path)
            if self.campaign_manifest_path.is_file()
            else None
        )
        return {
            "schema": "gtos.replay_acceleration.streaming_proof_authority.v1",
            "campaign_manifest_path": str(self.campaign_manifest_path),
            "campaign_manifest_root_sha256": (
                campaign.get("campaign_manifest_root_sha256") if campaign else None
            ),
            "shard_count": len(self._shards),
            "hot_roles": list(ROLES),
            "checkpoint_authority": (
                dict(self._checkpoint_authority)
                if self._checkpoint_authority is not None
                else None
            ),
            "terminal_checkpoint_chain_root_sha256": (
                self._checkpoint_chain_root_sha256
            ),
            "exact_reconstruction": True,
            "verified_before_reclaim": True,
            "metrics": self.metrics(),
        }

    def day_capacity_contract(
        self,
        *,
        min_transient_headroom_bytes: int,
    ) -> dict[str, Any]:
        free_bytes = shutil.disk_usage(self.root).free
        required_free_bytes = (
            self.warning_floor_free_bytes
            + int(min_transient_headroom_bytes)
        )
        return {
            "schema": "gtos.replay_acceleration.streaming_day_capacity.v1",
            "free_bytes": free_bytes,
            "warning_floor_free_bytes": self.warning_floor_free_bytes,
            "min_transient_headroom_bytes": int(
                min_transient_headroom_bytes
            ),
            "required_free_bytes": required_free_bytes,
            "valid": free_bytes >= required_free_bytes,
        }

    def require_day_capacity(
        self,
        *,
        min_transient_headroom_bytes: int,
        settle_timeout_seconds: float = 0,
        settle_poll_seconds: float = 5,
        on_advisory_miss: Callable[[], Any] | None = None,
    ) -> dict[str, Any]:
        settle_timeout = float(settle_timeout_seconds)
        settle_poll = float(settle_poll_seconds)
        if (
            not math.isfinite(settle_timeout)
            or not math.isfinite(settle_poll)
            or settle_timeout < 0
            or settle_poll <= 0
        ):
            raise ArchiveRejected("archive_day_capacity_settle_invalid")

        def sample() -> dict[str, Any]:
            contract = self.day_capacity_contract(
                min_transient_headroom_bytes=min_transient_headroom_bytes
            )
            if contract["free_bytes"] < self.hard_floor_free_bytes:
                raise ArchiveRejected("archive_day_capacity_hard_floor")
            return contract

        contract = sample()
        if contract["valid"] is True:
            return contract
        if settle_timeout == 0:
            raise ArchiveRejected("archive_day_capacity_warning")
        if on_advisory_miss is not None:
            on_advisory_miss()

        remaining_seconds = settle_timeout
        while remaining_seconds > 0:
            sleep_seconds = min(settle_poll, remaining_seconds)
            time.sleep(sleep_seconds)
            remaining_seconds -= sleep_seconds
            contract = sample()
            if contract["valid"] is True:
                return contract
        raise ArchiveRejected("archive_day_capacity_warning")

    def _require_planned_compression_capacity(
        self,
        *,
        planned_compressed_bytes: int,
        partial_snapshot_bytes: int,
        settle_timeout_seconds: float,
        settle_poll_seconds: float,
        on_advisory_miss: Callable[[], Any] | None,
    ) -> None:
        """Wait without publishing until the measured archive growth is safe."""

        settle_timeout = float(settle_timeout_seconds)
        settle_poll = float(settle_poll_seconds)
        if (
            not math.isfinite(settle_timeout)
            or not math.isfinite(settle_poll)
            or settle_timeout < 0
            or settle_poll <= 0
        ):
            raise ArchiveRejected("archive_compression_settle_invalid")
        required_free_bytes = (
            self.hard_floor_free_bytes
            + int(planned_compressed_bytes)
            + int(partial_snapshot_bytes)
            + ARCHIVE_COMPRESSION_CONTROL_RESERVE_BYTES
        )

        def sufficient() -> bool:
            return shutil.disk_usage(self.root).free >= required_free_bytes

        if sufficient():
            return
        if settle_timeout == 0:
            raise ArchiveRejected("archive_compression_would_threaten_hard_floor")
        if on_advisory_miss is not None:
            on_advisory_miss()
        remaining_seconds = settle_timeout
        while remaining_seconds > 0:
            sleep_seconds = min(settle_poll, remaining_seconds)
            time.sleep(sleep_seconds)
            remaining_seconds -= sleep_seconds
            if sufficient():
                return
        raise ArchiveRejected("archive_compression_would_threaten_hard_floor")

    def _require_remaining_compression_capacity(
        self,
        planned_remaining_bytes: int,
    ) -> None:
        required_free_bytes = (
            self.hard_floor_free_bytes
            + int(planned_remaining_bytes)
            + ARCHIVE_COMPRESSION_CONTROL_RESERVE_BYTES
        )
        if shutil.disk_usage(self.root).free < required_free_bytes:
            raise ArchiveRejected("archive_compression_would_threaten_hard_floor")

    def _cumulative_surfaces(self) -> list[dict[str, Any]]:
        return [
            {
                "role": role,
                "bytes": self._cumulative_bytes[role],
                "rows": self._cumulative_rows[role],
                "sha256": self._cumulative_hashes[role].hexdigest(),
            }
            for role in ROLES
        ]

    def gate_surface_contracts(self) -> dict[str, dict[str, Any]]:
        if not self.campaign_manifest_path.is_file() or not self._shards:
            raise ArchiveRejected("archive_campaign_manifest_missing")
        campaign = load_canonical(self.campaign_manifest_path)
        return {
            row["role"]: {
                **row,
                "name": self.hot_outputs[row["role"]].name,
                "storage": "verified_zstd_campaign",
                "archive_campaign_manifest_path": str(
                    self.campaign_manifest_path
                ),
                "archive_campaign_manifest_root_sha256": campaign[
                    "campaign_manifest_root_sha256"
                ],
            }
            for row in self._cumulative_surfaces()
        }

    def independent_verify_campaign(self, output_path: Path) -> dict[str, Any]:
        if not self.campaign_manifest_path.is_file():
            raise ArchiveRejected("archive_campaign_manifest_missing")
        output_path = Path(output_path)
        if output_path.exists() or output_path.is_symlink():
            raise ArchiveRejected("archive_campaign_receipt_must_be_new")
        subprocess.run(
            [
                sys.executable,
                str(VERIFIER_PATH),
                "verify-campaign",
                "--manifest",
                str(self.campaign_manifest_path),
                "--output",
                str(output_path),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            check=True,
        )
        report = load_canonical(output_path)
        if report.get("valid") is not True:
            raise ArchiveRejected("archive_campaign_verification_failed")
        return report

    def _validated_checkpoint_authority(
        self,
        value: Mapping[str, Any],
    ) -> dict[str, Any]:
        authority = dict(value)
        hash_fields = (
            "run_identity_root_sha256",
            "source_plan_digest_sha256",
            "arm_fingerprint_sha256",
            "shared_execution_contract_sha256",
            "accelerated_code_config_authority_root_sha256",
        )
        if (
            set(authority) != CHECKPOINT_AUTHORITY_KEYS
            or authority.get("schema") != CHECKPOINT_AUTHORITY_SCHEMA
            or authority.get("output_prefix") != self.output_prefix
            or any(not _is_sha256(authority.get(field)) for field in hash_fields)
        ):
            raise ArchiveRejected("archive_checkpoint_authority_invalid")
        if (
            self._checkpoint_authority is not None
            and authority != self._checkpoint_authority
        ):
            raise ArchiveRejected("archive_checkpoint_authority_drift")
        return authority

    def _checkpoint_chain_entries(self) -> list[dict[str, Any]]:
        return [
            {
                key: shard[key]
                for key in (
                    "segment_id",
                    "segment_index",
                    "checkpoint_preimage_path",
                    "checkpoint_preimage_sha256",
                    "checkpoint_root_sha256",
                    "prior_checkpoint_chain_root_sha256",
                    "checkpoint_chain_root_sha256",
                )
            }
            for shard in self._shards
        ]

    def _hot_tombstones(self) -> list[dict[str, Any]]:
        return [
            {
                "role": role,
                "name": self.hot_outputs[role].name,
                "bytes": 0,
                "rows": 0,
                "sha256": EMPTY_SHA256,
            }
            for role in ROLES
        ]

    @staticmethod
    def _regular_identity(value: os.stat_result) -> dict[str, int]:
        if not stat.S_ISREG(value.st_mode) or value.st_nlink != 1:
            raise ArchiveRejected("archive_raw_binding_invalid")
        return {
            "device": int(value.st_dev),
            "inode": int(value.st_ino),
            "mode": int(value.st_mode),
            "links": int(value.st_nlink),
        }

    def _validate_bound_hot_surfaces(
        self,
        descriptors: Mapping[str, int],
        identities: Mapping[str, Mapping[str, int]],
        expected_contracts: Mapping[str, Mapping[str, Any]],
    ) -> None:
        for role in ROLES:
            try:
                opened = self._regular_identity(os.fstat(descriptors[role]))
                path_state = self._regular_identity(
                    os.stat(self.hot_outputs[role], follow_symlinks=False)
                )
            except (OSError, ArchiveRejected):
                raise ArchiveRejected("archive_raw_binding_changed") from None
            if opened != identities[role] or path_state != identities[role]:
                raise ArchiveRejected("archive_raw_binding_changed")
            if descriptor_stream_contract(descriptors[role]) != dict(
                expected_contracts[role]
            ):
                raise ArchiveRejected("archive_raw_binding_changed")

    def _bind_hot_surfaces(
        self,
        raw_contracts: Mapping[str, Mapping[str, Any]],
    ) -> tuple[dict[str, int], dict[str, dict[str, int]]]:
        descriptors: dict[str, int] = {}
        identities: dict[str, dict[str, int]] = {}
        try:
            for role in ROLES:
                path = self.hot_outputs[role]
                if path.is_symlink():
                    raise ArchiveRejected("archive_raw_binding_invalid")
                descriptor = os.open(
                    path,
                    os.O_RDWR | getattr(os, "O_NOFOLLOW", 0),
                )
                descriptors[role] = descriptor
                opened = self._regular_identity(os.fstat(descriptor))
                path_state = self._regular_identity(
                    os.stat(path, follow_symlinks=False)
                )
                if opened != path_state:
                    raise ArchiveRejected("archive_raw_binding_invalid")
                if descriptor_stream_contract(descriptor) != dict(
                    raw_contracts[role]
                ):
                    raise ArchiveRejected("archive_raw_binding_invalid")
                identities[role] = opened
            self._validate_bound_hot_surfaces(
                descriptors,
                identities,
                raw_contracts,
            )
            return descriptors, identities
        except OSError:
            error = ArchiveRejected("archive_raw_binding_invalid")
        except ArchiveRejected as exc:
            error = exc
        for descriptor in descriptors.values():
            try:
                os.close(descriptor)
            except OSError:
                pass
        raise error

    @staticmethod
    def _close_bound_hot_surfaces(descriptors: Mapping[str, int]) -> None:
        for descriptor in descriptors.values():
            try:
                os.close(descriptor)
            except OSError:
                pass

    def _restore_descriptor_from_verified_surface(
        self,
        *,
        descriptor: int,
        compressed_path: Path,
        expected_contract: Mapping[str, Any],
    ) -> None:
        observed = descriptor_stream_contract(descriptor)
        if observed == dict(expected_contract):
            return
        if observed != EMPTY_RAW_CONTRACT:
            raise ArchiveRejected("archive_tombstone_rollback_failed")
        process: subprocess.Popen[bytes] | None = None
        stdout = None
        try:
            os.ftruncate(descriptor, 0)
            os.lseek(descriptor, 0, os.SEEK_SET)
            process = subprocess.Popen(
                [self.zstd, "-q", "-d", "-c", str(compressed_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
            stdout = process.stdout
            if stdout is None:
                raise OSError("archive recovery stdout unavailable")
            while True:
                chunk = stdout.read(1024 * 1024)
                if not chunk:
                    break
                offset = 0
                while offset < len(chunk):
                    written = os.write(descriptor, chunk[offset:])
                    if written <= 0:
                        raise OSError("archive recovery write failed")
                    offset += written
            if process.wait() != 0:
                raise OSError("archive recovery decompression failed")
            os.fsync(descriptor)
            if descriptor_stream_contract(descriptor) != dict(expected_contract):
                raise OSError("archive recovery contract mismatch")
        except Exception:
            if process is not None and process.returncode is None:
                try:
                    process.kill()
                finally:
                    process.wait()
            raise ArchiveRejected("archive_tombstone_rollback_failed") from None
        finally:
            if stdout is not None:
                stdout.close()

    def _restore_bound_hot_surfaces(
        self,
        *,
        descriptors: Mapping[str, int],
        identities: Mapping[str, Mapping[str, int]],
        raw_contracts: Mapping[str, Mapping[str, Any]],
        surfaces: list[Mapping[str, Any]],
    ) -> None:
        by_role = {str(surface["role"]): surface for surface in surfaces}
        for role in ROLES:
            try:
                opened = self._regular_identity(os.fstat(descriptors[role]))
                path_state = self._regular_identity(
                    os.stat(self.hot_outputs[role], follow_symlinks=False)
                )
            except (OSError, ArchiveRejected):
                raise ArchiveRejected("archive_tombstone_rollback_failed") from None
            if opened != identities[role] or path_state != identities[role]:
                raise ArchiveRejected("archive_tombstone_rollback_failed")
        for role in ROLES:
            self._restore_descriptor_from_verified_surface(
                descriptor=descriptors[role],
                compressed_path=Path(by_role[role]["compressed_path"]),
                expected_contract=raw_contracts[role],
            )
        self._validate_bound_hot_surfaces(
            descriptors,
            identities,
            raw_contracts,
        )

    def _write_recovery_journal(
        self,
        *,
        path: Path,
        state: str,
        segment_id: str,
        identities: Mapping[str, Mapping[str, int]],
        raw_contracts: Mapping[str, Mapping[str, Any]],
        surfaces: list[Mapping[str, Any]],
        manifest_root_sha256: str,
        receipt_root_sha256: str,
    ) -> None:
        compressed_by_role = {
            str(surface["role"]): surface for surface in surfaces
        }
        core = {
            "schema": RECLAIM_RECOVERY_SCHEMA,
            "state": state,
            "acceptance_authorized": False,
            "segment_id": segment_id,
            "campaign_manifest_path": str(self.campaign_manifest_path),
            "manifest_root_sha256": manifest_root_sha256,
            "receipt_root_sha256": receipt_root_sha256,
            "hot_surfaces": [
                {
                    "role": role,
                    "path": str(self.hot_outputs[role]),
                    **dict(identities[role]),
                    **dict(raw_contracts[role]),
                    "compressed_path": str(
                        compressed_by_role[role]["compressed_path"]
                    ),
                    "compressed_bytes": int(
                        compressed_by_role[role]["compressed_bytes"]
                    ),
                    "compressed_sha256": str(
                        compressed_by_role[role]["compressed_sha256"]
                    ),
                }
                for role in ROLES
            ],
        }
        atomic_write(path, {**core, "journal_root_sha256": root(core)})
        _fsync_directory(path.parent)

    def _write_campaign_manifest(self) -> None:
        if (
            self._checkpoint_authority is None
            or self._checkpoint_chain_genesis_root_sha256 is None
            or self._checkpoint_chain_root_sha256 is None
        ):
            raise ArchiveRejected("archive_checkpoint_chain_incomplete")
        checkpoint_chain = self._checkpoint_chain_entries()
        core = {
            "schema": CAMPAIGN_SCHEMA,
            "output_prefix": self.output_prefix,
            "hot_roles": list(ROLES),
            "checkpoint_authority": dict(self._checkpoint_authority),
            "checkpoint_chain_genesis_root_sha256": (
                self._checkpoint_chain_genesis_root_sha256
            ),
            "checkpoint_chain": checkpoint_chain,
            "checkpoint_chain_set_root_sha256": root(checkpoint_chain),
            "terminal_checkpoint_chain_root_sha256": (
                self._checkpoint_chain_root_sha256
            ),
            "shards": list(self._shards),
            "cumulative_surfaces": self._cumulative_surfaces(),
            "hot_tombstones": self._hot_tombstones(),
            "exact_concatenation_reconstruction": True,
            "writer_retains_economic_values": False,
            "live_broker_authority": False,
        }
        atomic_write(
            self.campaign_manifest_path,
            {**core, "campaign_manifest_root_sha256": root(core)},
        )

    def seal_and_reclaim(
        self,
        *,
        start_day: str,
        end_day: str,
        pre_archive_partial_summary_path: Path | None = None,
        checkpoint_authority: Mapping[str, Any] | None = None,
        current_summary_contract_root_sha256: str | None = None,
        settle_timeout_seconds: float = 0,
        settle_poll_seconds: float = 5,
        on_advisory_miss: Callable[[], Any] | None = None,
    ) -> dict[str, Any]:
        build_state: dict[str, Any] = {}
        try:
            return self._seal_and_reclaim_impl(
                start_day=start_day,
                end_day=end_day,
                pre_archive_partial_summary_path=(
                    pre_archive_partial_summary_path
                ),
                checkpoint_authority=checkpoint_authority,
                current_summary_contract_root_sha256=(
                    current_summary_contract_root_sha256
                ),
                settle_timeout_seconds=settle_timeout_seconds,
                settle_poll_seconds=settle_poll_seconds,
                on_advisory_miss=on_advisory_miss,
                build_state=build_state,
            )
        except BaseException:
            staging_dir = build_state.get("staging_dir")
            if staging_dir is not None:
                shutil.rmtree(Path(staging_dir), ignore_errors=True)
            segment_dir_value = build_state.get("segment_dir")
            if segment_dir_value is not None:
                segment_dir = Path(segment_dir_value)
                safe_to_remove = (
                    not self.campaign_manifest_path.exists()
                    and not bool(build_state.get("reclaim_started"))
                )
                journal_path = segment_dir / "RECLAIM_RECOVERY_JOURNAL.json"
                if journal_path.is_file():
                    try:
                        journal = load_canonical(journal_path)
                    except Exception:
                        journal = {}
                    safe_to_remove = safe_to_remove or (
                        journal.get("schema") == RECLAIM_RECOVERY_SCHEMA
                        and journal.get("state")
                        == "restored_non_acceptance"
                        and journal.get("acceptance_authorized") is False
                    )
                if safe_to_remove:
                    shutil.rmtree(segment_dir, ignore_errors=True)
            raise

    def _seal_and_reclaim_impl(
        self,
        *,
        start_day: str,
        end_day: str,
        pre_archive_partial_summary_path: Path | None,
        checkpoint_authority: Mapping[str, Any] | None,
        current_summary_contract_root_sha256: str | None,
        settle_timeout_seconds: float,
        settle_poll_seconds: float,
        on_advisory_miss: Callable[[], Any] | None,
        build_state: dict[str, Any],
    ) -> dict[str, Any]:
        if (
            current_summary_contract_root_sha256 is not None
            or pre_archive_partial_summary_path is None
            or checkpoint_authority is None
        ):
            raise ArchiveRejected("archive_checkpoint_preimage_required")
        authority = self._validated_checkpoint_authority(checkpoint_authority)
        genesis_core = {
            "schema": CHECKPOINT_CHAIN_GENESIS_SCHEMA,
            "checkpoint_authority": authority,
        }
        checkpoint_chain_genesis_root = root(genesis_core)
        if (
            self._checkpoint_chain_genesis_root_sha256 is not None
            and checkpoint_chain_genesis_root
            != self._checkpoint_chain_genesis_root_sha256
        ):
            raise ArchiveRejected("archive_checkpoint_chain_genesis_drift")
        prior_checkpoint_chain_root = (
            self._checkpoint_chain_root_sha256
            or checkpoint_chain_genesis_root
        )
        segment_index = len(self._shards) + 1
        segment_id = f"{segment_index:03d}_{start_day}_{end_day}"
        segment_dir = self.root / "shards" / segment_id
        if segment_dir.exists():
            raise ArchiveRejected("archive_segment_already_exists")
        raw_contracts = {
            role: stream_contract(self.hot_outputs[role]) for role in ROLES
        }
        planned_compressed_contracts = {
            role: planned_zstd_contract(self.zstd, self.hot_outputs[role])
            for role in ROLES
        }
        partial_source_path = Path(pre_archive_partial_summary_path)
        if partial_source_path.is_symlink() or not partial_source_path.is_file():
            raise ArchiveRejected("archive_checkpoint_snapshot_invalid")
        partial_snapshot_bytes = partial_source_path.stat().st_size
        planned_compressed_total = sum(
            int(value["compressed_bytes"])
            for value in planned_compressed_contracts.values()
        )
        self._require_planned_compression_capacity(
            planned_compressed_bytes=planned_compressed_total,
            partial_snapshot_bytes=partial_snapshot_bytes,
            settle_timeout_seconds=settle_timeout_seconds,
            settle_poll_seconds=settle_poll_seconds,
            on_advisory_miss=on_advisory_miss,
        )
        shards_root = self.root / "shards"
        shards_root.mkdir(parents=True, exist_ok=True)
        staging_dir = Path(
            tempfile.mkdtemp(
                prefix=f".{segment_id}.staging-",
                dir=shards_root,
            )
        )
        build_state["segment_dir"] = str(segment_dir)
        build_state["staging_dir"] = str(staging_dir)
        partial_snapshot_path = segment_dir / "PRE_ARCHIVE_PARTIAL_SUMMARY.json"
        partial_snapshot_staging_path = (
            staging_dir / partial_snapshot_path.name
        )
        partial_snapshot_contract = _snapshot_regular_file(
            partial_source_path,
            partial_snapshot_staging_path,
        )
        if partial_snapshot_contract["bytes"] != partial_snapshot_bytes:
            raise ArchiveRejected("archive_checkpoint_snapshot_changed")
        checkpoint_preimage_core = {
            "schema": CHECKPOINT_PREIMAGE_SCHEMA,
            "segment_id": segment_id,
            "segment_index": segment_index,
            "start_day": start_day,
            "end_day": end_day,
            "completed_day": end_day,
            "output_prefix": self.output_prefix,
            "checkpoint_authority": authority,
            "pre_archive_partial_summary": {
                "source_name": Path(pre_archive_partial_summary_path).name,
                "snapshot_path": str(partial_snapshot_path),
                **partial_snapshot_contract,
            },
            "hot_surfaces": [
                {
                    "role": role,
                    "name": self.hot_outputs[role].name,
                    "bytes": raw_contracts[role]["raw_bytes"],
                    "rows": raw_contracts[role]["raw_rows"],
                    "sha256": raw_contracts[role]["raw_sha256"],
                }
                for role in ROLES
            ],
            "prior_checkpoint_chain_root_sha256": (
                prior_checkpoint_chain_root
            ),
        }
        checkpoint_preimage = {
            **checkpoint_preimage_core,
            "checkpoint_root_sha256": root(checkpoint_preimage_core),
        }
        checkpoint_preimage_path = segment_dir / "CHECKPOINT_PREIMAGE.json"
        checkpoint_preimage_staging_path = (
            staging_dir / checkpoint_preimage_path.name
        )
        atomic_write(checkpoint_preimage_staging_path, checkpoint_preimage)
        checkpoint_preimage_sha256 = hashlib.sha256(
            checkpoint_preimage_staging_path.read_bytes()
        ).hexdigest()
        checkpoint_chain_core = {
            "schema": CHECKPOINT_CHAIN_LINK_SCHEMA,
            "segment_id": segment_id,
            "segment_index": segment_index,
            "checkpoint_preimage_sha256": checkpoint_preimage_sha256,
            "checkpoint_root_sha256": checkpoint_preimage[
                "checkpoint_root_sha256"
            ],
            "prior_checkpoint_chain_root_sha256": (
                prior_checkpoint_chain_root
            ),
        }
        checkpoint_chain_root = root(checkpoint_chain_core)
        next_hashes = {
            role: self._cumulative_hashes[role].copy() for role in ROLES
        }
        for role in ROLES:
            with self.hot_outputs[role].open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    next_hashes[role].update(chunk)
        raw_total = sum(value["raw_bytes"] for value in raw_contracts.values())
        surfaces = []
        compression_started = time.perf_counter()
        child_before = resource.getrusage(resource.RUSAGE_CHILDREN)
        planned_remaining_bytes = planned_compressed_total
        for role in ROLES:
            raw_path = self.hot_outputs[role]
            self._require_remaining_compression_capacity(
                planned_remaining_bytes,
            )
            if stream_contract(raw_path) != raw_contracts[role]:
                raise ArchiveRejected("archive_raw_changed_before_compression")
            compressed_path = segment_dir / f"{role}.jsonl.zst"
            staged_compressed_path = staging_dir / compressed_path.name
            temporary = staged_compressed_path.with_suffix(
                staged_compressed_path.suffix + ".tmp"
            )
            try:
                with temporary.open("xb") as target:
                    try:
                        result = subprocess.run(
                            [
                                self.zstd,
                                "-q",
                                "-1",
                                "-T1",
                                "-c",
                                str(raw_path),
                            ],
                            stdout=target,
                            stderr=subprocess.DEVNULL,
                            check=False,
                        )
                    except OSError:
                        raise ArchiveRejected(
                            "archive_compression_failed"
                        ) from None
                    target.flush()
                    os.fsync(target.fileno())
                if result.returncode != 0:
                    raise ArchiveRejected("archive_compression_failed")
                temporary.replace(staged_compressed_path)
            finally:
                try:
                    temporary.unlink()
                except FileNotFoundError:
                    pass
            compressed_contract = file_contract(staged_compressed_path)
            if compressed_contract != planned_compressed_contracts[role]:
                raise ArchiveRejected("archive_compression_plan_mismatch")
            surfaces.append(
                {
                    "role": role,
                    "raw_name": raw_path.name,
                    "compressed_path": str(compressed_path),
                    **raw_contracts[role],
                    **compressed_contract,
                }
            )
            planned_remaining_bytes -= int(
                planned_compressed_contracts[role]["compressed_bytes"]
            )
        child_after = resource.getrusage(resource.RUSAGE_CHILDREN)
        compression_seconds = time.perf_counter() - compression_started
        manifest_core = {
            "schema": SHARD_SCHEMA,
            "segment_id": segment_id,
            "segment_index": segment_index,
            "start_day": start_day,
            "end_day": end_day,
            "output_prefix": self.output_prefix,
            "surfaces": surfaces,
            "checkpoint_preimage_path": str(checkpoint_preimage_path),
            "checkpoint_preimage_sha256": checkpoint_preimage_sha256,
            "checkpoint_root_sha256": checkpoint_preimage[
                "checkpoint_root_sha256"
            ],
            "prior_checkpoint_chain_root_sha256": (
                prior_checkpoint_chain_root
            ),
            "checkpoint_chain_root_sha256": checkpoint_chain_root,
            "compression": {
                "codec": "zstd",
                "level": 1,
                "threads": 1,
                "version": self.zstd_version,
            },
            "exact_concatenation_reconstruction": True,
            "economic_values_exposed": False,
        }
        manifest = {
            **manifest_core,
            "manifest_root_sha256": root(manifest_core),
        }
        manifest_path = segment_dir / "SHARD_MANIFEST.json"
        receipt_path = segment_dir / "VERIFY_RECEIPT.json"
        atomic_write(staging_dir / manifest_path.name, manifest)
        staging_dir.rename(segment_dir)
        build_state["staging_dir"] = None
        _fsync_directory(shards_root)
        verification_started = time.perf_counter()
        verification_result = subprocess.run(
            [
                sys.executable,
                str(VERIFIER_PATH),
                "verify-shard",
                "--manifest",
                str(manifest_path),
                "--output",
                str(receipt_path),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if verification_result.returncode != 0:
            raise ArchiveRejected("archive_independent_verifier_failed")
        verification_seconds = time.perf_counter() - verification_started
        receipt = load_canonical(receipt_path)
        if (
            receipt.get("schema") != RECEIPT_SCHEMA
            or receipt.get("valid") is not True
            or receipt.get("manifest_root_sha256")
            != manifest["manifest_root_sha256"]
            or receipt.get("receipt_root_sha256")
            != self_root(receipt, "receipt_root_sha256")
        ):
            raise ArchiveRejected("archive_independent_receipt_invalid")
        archive_bytes = tree_bytes(self.root)
        if archive_bytes > self.max_archive_bytes:
            raise ArchiveRejected("archive_quota_exceeded")
        shard_entry = {
            "segment_id": segment_id,
            "segment_index": segment_index,
            "start_day": start_day,
            "end_day": end_day,
            "checkpoint_preimage_path": str(checkpoint_preimage_path),
            "checkpoint_preimage_sha256": checkpoint_preimage_sha256,
            "checkpoint_root_sha256": checkpoint_preimage[
                "checkpoint_root_sha256"
            ],
            "prior_checkpoint_chain_root_sha256": (
                prior_checkpoint_chain_root
            ),
            "checkpoint_chain_root_sha256": checkpoint_chain_root,
            "manifest_path": str(manifest_path),
            "manifest_root_sha256": manifest["manifest_root_sha256"],
            "receipt_path": str(receipt_path),
            "receipt_root_sha256": receipt["receipt_root_sha256"],
        }
        descriptors, identities = self._bind_hot_surfaces(raw_contracts)
        recovery_journal_path = (
            segment_dir / "RECLAIM_RECOVERY_JOURNAL.json"
        )
        self._write_recovery_journal(
            path=recovery_journal_path,
            state="prepared_non_acceptance",
            segment_id=segment_id,
            identities=identities,
            raw_contracts=raw_contracts,
            surfaces=surfaces,
            manifest_root_sha256=manifest["manifest_root_sha256"],
            receipt_root_sha256=receipt["receipt_root_sha256"],
        )
        self._validate_bound_hot_surfaces(
            descriptors,
            identities,
            raw_contracts,
        )
        build_state["reclaim_started"] = True
        tombstones_complete = False
        state_mutated = False
        prior_state = {
            "cumulative_hashes": self._cumulative_hashes,
            "cumulative_bytes": dict(self._cumulative_bytes),
            "cumulative_rows": dict(self._cumulative_rows),
            "checkpoint_authority": self._checkpoint_authority,
            "checkpoint_chain_genesis_root_sha256": (
                self._checkpoint_chain_genesis_root_sha256
            ),
            "checkpoint_chain_root_sha256": self._checkpoint_chain_root_sha256,
            "shards": list(self._shards),
        }
        try:
            for role in ROLES:
                descriptor = descriptors[role]
                os.ftruncate(descriptor, 0)
                os.fsync(descriptor)
                if descriptor_stream_contract(descriptor) != EMPTY_RAW_CONTRACT:
                    raise ArchiveRejected(
                        "archive_tombstone_verification_failed"
                    )
            self._validate_bound_hot_surfaces(
                descriptors,
                identities,
                {role: EMPTY_RAW_CONTRACT for role in ROLES},
            )
            tombstones_complete = True
            self._write_recovery_journal(
                path=recovery_journal_path,
                state="tombstoned_pending_campaign",
                segment_id=segment_id,
                identities=identities,
                raw_contracts=raw_contracts,
                surfaces=surfaces,
                manifest_root_sha256=manifest["manifest_root_sha256"],
                receipt_root_sha256=receipt["receipt_root_sha256"],
            )
            hot_tombstones = self._hot_tombstones()
            reclaim_core = {
                "schema": (
                    "gtos.replay_acceleration.streaming_proof_reclaim.v1"
                ),
                "segment_id": segment_id,
                "manifest_root_sha256": manifest["manifest_root_sha256"],
                "receipt_root_sha256": receipt["receipt_root_sha256"],
                "checkpoint_root_sha256": checkpoint_preimage[
                    "checkpoint_root_sha256"
                ],
                "checkpoint_chain_root_sha256": checkpoint_chain_root,
                "raw_bytes_reclaimed": raw_total,
                "hot_tombstones": hot_tombstones,
                "hot_tombstone_set_root_sha256": root(hot_tombstones),
                "verified_before_reclaim": True,
                "tombstones_fsynced_and_verified": True,
                "reconstructable": True,
            }
            atomic_write(
                segment_dir / "RECLAIM_RECEIPT.json",
                {
                    **reclaim_core,
                    "reclaim_root_sha256": root(reclaim_core),
                },
            )
            _fsync_directory(segment_dir)
            if tree_bytes(self.root) > self.max_archive_bytes:
                raise ArchiveRejected("archive_quota_exceeded")

            self._cumulative_hashes = next_hashes
            for role in ROLES:
                self._cumulative_bytes[role] += int(
                    raw_contracts[role]["raw_bytes"]
                )
                self._cumulative_rows[role] += int(
                    raw_contracts[role]["raw_rows"]
                )
            self._checkpoint_authority = authority
            self._checkpoint_chain_genesis_root_sha256 = (
                checkpoint_chain_genesis_root
            )
            self._checkpoint_chain_root_sha256 = checkpoint_chain_root
            self._shards.append(shard_entry)
            state_mutated = True
            self._write_campaign_manifest()
        except BaseException as exc:
            if not self.campaign_manifest_path.exists():
                try:
                    self._restore_bound_hot_surfaces(
                        descriptors=descriptors,
                        identities=identities,
                        raw_contracts=raw_contracts,
                        surfaces=surfaces,
                    )
                    if state_mutated:
                        self._cumulative_hashes = prior_state[
                            "cumulative_hashes"
                        ]
                        self._cumulative_bytes = prior_state[
                            "cumulative_bytes"
                        ]
                        self._cumulative_rows = prior_state[
                            "cumulative_rows"
                        ]
                        self._checkpoint_authority = prior_state[
                            "checkpoint_authority"
                        ]
                        self._checkpoint_chain_genesis_root_sha256 = (
                            prior_state[
                                "checkpoint_chain_genesis_root_sha256"
                            ]
                        )
                        self._checkpoint_chain_root_sha256 = prior_state[
                            "checkpoint_chain_root_sha256"
                        ]
                        self._shards = prior_state["shards"]
                    self._write_recovery_journal(
                        path=recovery_journal_path,
                        state="restored_non_acceptance",
                        segment_id=segment_id,
                        identities=identities,
                        raw_contracts=raw_contracts,
                        surfaces=surfaces,
                        manifest_root_sha256=manifest[
                            "manifest_root_sha256"
                        ],
                        receipt_root_sha256=receipt[
                            "receipt_root_sha256"
                        ],
                    )
                except BaseException:
                    raise ArchiveRejected(
                        "archive_tombstone_rollback_failed"
                    ) from None
            if isinstance(exc, ArchiveRejected):
                raise
            if not tombstones_complete:
                raise ArchiveRejected(
                    "archive_tombstone_write_failed"
                ) from None
            raise ArchiveRejected("archive_reclaim_publication_failed") from None
        finally:
            self._close_bound_hot_surfaces(descriptors)
        compressed_total = sum(item["compressed_bytes"] for item in surfaces)
        self._metrics["compression_seconds"] += compression_seconds
        self._metrics["verification_seconds"] += verification_seconds
        self._metrics["raw_bytes_archived"] += raw_total
        self._metrics["compressed_bytes_retained"] += compressed_total
        self._metrics["raw_bytes_reclaimed"] += raw_total
        self._metrics["shard_count"] += 1
        self._metrics["child_user_cpu_seconds"] += (
            child_after.ru_utime - child_before.ru_utime
        )
        self._metrics["child_system_cpu_seconds"] += (
            child_after.ru_stime - child_before.ru_stime
        )
        return {
            **manifest,
            "manifest_path": str(manifest_path),
            "receipt_path": str(receipt_path),
            "receipt_root_sha256": receipt["receipt_root_sha256"],
            "verified_before_reclaim": True,
            "raw_derivatives_reclaimed": True,
            "archive_bytes_after": tree_bytes(self.root),
        }


__all__ = ["ArchiveRejected", "StreamingProofArchive"]
