"""Typed immutable source cache used by the real broad S0R0 replay harness.

This module stops at normalized market-data rows.  It does not cache candidates,
policy decisions, broker state, or any result/economic surface.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import struct
import threading
import time
import uuid
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, ContextManager, Iterable, Mapping, Sequence, TextIO

from src.research_infra import v4_timewarp_simulated_live_research_loop as legacy
from src.research_infra.replay_acceleration_source_batch import (
    SOURCE_BYTES_STAGE,
    CacheAdmissionRegistry,
    ImmutableSourceBatchCache,
    SourceBatchBinding,
    implementation_root as accepted_source_implementation_root,
)
from src.research_infra.replay_acceleration_immutable_evidence import (
    ImmutableEvidenceError,
    lexical_path,
    read_regular_nofollow,
)


TYPED_CACHE_SCHEMA = "gtos.replay_acceleration.integrated_typed_source_cache.v1"
TYPED_MANIFEST_SCHEMA = "gtos.replay_acceleration.integrated_typed_partition.v1"
TYPED_ROW_SCHEMA = "gtos.replay_acceleration.ohlcv_time_f64.v1"
_MAGIC = b"GTOSNR01"
_HEADER = struct.Struct("<8sQ")
_ROW = struct.Struct("<qddddd")
_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
_ROOT_FIELDS = (
    "source_bundle_root_sha256",
    "config_projection_root_sha256",
    "source_payload_root_sha256",
    "source_path_root_sha256",
    "normalizer_code_root_sha256",
)
_MANIFEST_FIELDS = frozenset(
    {
        "schema",
        "identity",
        "identity_root_sha256",
        "payload_sha256",
        "payload_byte_count",
        "row_count",
        "rows_root_sha256",
        "manifest_root_sha256",
    }
)


class IntegratedSourceRejected(RuntimeError):
    """Stable fail-closed error for the integrated source-only cache."""

    def __init__(self, code: str) -> None:
        self.code = str(code)
        super().__init__(self.code)


def _canonical_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError):
        raise IntegratedSourceRejected("typed_noncanonical_value") from None


def _root(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _valid_root(value: Any) -> bool:
    return type(value) is str and len(value) == 64 and all(
        character in "009abcdef" for character in value
    )


def _source_path_root(path: Path) -> str:
    return _root({"source_path": os.path.abspath(os.fspath(path))})


def _normalizer_code_root() -> str:
    return _root(
        {
            "integrated_source_module_sha256": _file_sha256(Path(__file__)),
            "legacy_normalizer_module_sha256": _file_sha256(Path(legacy.__file__)),
            "typed_row_schema": TYPED_ROW_SCHEMA,
        }
    )


def _manifest_root(manifest: Mapping[str, Any]) -> str:
    projection = dict(manifest)
    projection.pop("manifest_root_sha256", None)
    return _root(projection)


def _timestamp_microseconds(row: Mapping[str, Any]) -> int:
    timestamp = legacy.parse_row_time(row)
    if timestamp is None:
        raise IntegratedSourceRejected("typed_row_time_invalid")
    timestamp = timestamp.astimezone(timezone.utc)
    delta = timestamp - _EPOCH
    return (
        delta.days * 86_400_000_000
        + delta.seconds * 1_000_000
        + delta.microseconds
    )


def _decode_timestamp(value: int) -> str:
    return legacy.iso(_EPOCH + timedelta(microseconds=int(value)))


def _row_from_values(
    *, symbol: str, micros: int, values: Sequence[float]
) -> dict[str, Any]:
    timestamp = _decode_timestamp(micros)
    return {
        "time": timestamp,
        "time_utc": timestamp,
        "symbol": symbol,
        "open": float(values[0]),
        "high": float(values[1]),
        "low": float(values[2]),
        "close": float(values[3]),
        "volume": float(values[4]),
    }


def _update_rows_digest(digest: "hashlib._Hash", row: Mapping[str, Any]) -> None:
    digest.update(_canonical_bytes(dict(row)))
    digest.update(b"\n")


@dataclass(frozen=True)
class TypedPartitionResult:
    rows: tuple[dict[str, Any], ...]
    cache_hit: bool
    partition_root_sha256: str
    cache_entry_dir: Path


class TypedNormalizedPartitionCache:
    """Content-addressed fixed-width cache for normalized source partitions."""

    def __init__(
        self,
        root: Path,
        *,
        source_bundle_root: str,
        config_projection_root: str,
    ) -> None:
        if not _valid_root(source_bundle_root) or not _valid_root(
            config_projection_root
        ):
            raise IntegratedSourceRejected("typed_cache_authority_root_invalid")
        self.root = Path(root)
        self.source_bundle_root = source_bundle_root
        self.config_projection_root = config_projection_root
        self.normalizer_code_root = _normalizer_code_root()
        self.root.mkdir(parents=True, exist_ok=True)
        self._metrics_lock = threading.Lock()
        self._metrics: dict[str, int | float] = {
            "cold_partition_count": 0,
            "warm_partition_count": 0,
            "normalized_row_count": 0,
            "bytes_read": 0,
            "bytes_written": 0,
            "normalization_seconds": 0.0,
            "serialization_seconds": 0.0,
            "verification_seconds": 0.0,
            "hashing_seconds": 0.0,
        }

    def metrics(self) -> dict[str, int | float]:
        with self._metrics_lock:
            return dict(self._metrics)

    def _add_metrics(self, **values: int | float) -> None:
        with self._metrics_lock:
            for key, value in values.items():
                self._metrics[key] = self._metrics.get(key, 0) + value

    def _identity(
        self,
        *,
        source_path: Path,
        symbol: str,
        physical_timeframe: str,
        source_payload_root: str,
        expected_normalized_root: str | None,
        expected_normalized_row_count: int | None,
    ) -> dict[str, Any]:
        if not _valid_root(source_payload_root):
            raise IntegratedSourceRejected("typed_source_payload_root_invalid")
        symbol_value = str(symbol).strip()
        timeframe_value = str(physical_timeframe).strip().upper()
        if not symbol_value or timeframe_value not in {"D1", "H4", "H1", "M15", "M1"}:
            raise IntegratedSourceRejected("typed_partition_identity_invalid")
        return {
            "schema": TYPED_CACHE_SCHEMA,
            "typed_row_schema": TYPED_ROW_SCHEMA,
            "source_bundle_root_sha256": self.source_bundle_root,
            "config_projection_root_sha256": self.config_projection_root,
            "source_payload_root_sha256": source_payload_root,
            "source_path_root_sha256": _source_path_root(source_path),
            "normalizer_code_root_sha256": self.normalizer_code_root,
            "symbol": symbol_value,
            "physical_timeframe": timeframe_value,
            "accepted_normalized_root_sha256": expected_normalized_root,
            "accepted_normalized_row_count": expected_normalized_row_count,
        }

    def load_or_build_partition(
        self,
        *,
        source_path: Path,
        symbol: str,
        physical_timeframe: str,
        source_payload_root: str,
        open_text: Callable[[], ContextManager[TextIO]],
        source_byte_count: int = 0,
        expected_normalized_root: str | None = None,
        expected_normalized_row_count: int | None = None,
    ) -> TypedPartitionResult:
        identity = self._identity(
            source_path=source_path,
            symbol=symbol,
            physical_timeframe=physical_timeframe,
            source_payload_root=source_payload_root,
            expected_normalized_root=expected_normalized_root,
            expected_normalized_row_count=expected_normalized_row_count,
        )
        identity_root = _root(identity)
        entry = self.root / identity_root
        if entry.exists():
            rows = self._load_entry(entry, expected_identity=identity)
            self._add_metrics(
                warm_partition_count=1,
                normalized_row_count=len(rows),
            )
            return TypedPartitionResult(rows, True, identity_root, entry)

        started = time.perf_counter()
        temporary = self.root / f".{identity_root}.{uuid.uuid4().hex}.tmp"
        try:
            temporary.mkdir(mode=0o700)
            payload_path = temporary / "rows.bin"
            row_count = 0
            rows_digest = hashlib.sha256(
                b"gtos.replay_acceleration.canonical_rows.v1\n"
            )
            normalization_seconds = 0.0
            serialization_seconds = 0.0
            with payload_path.open("w+b") as payload_handle:
                payload_handle.write(_HEADER.pack(_MAGIC, 0))
                with open_text() as source_handle:
                    reader = csv.DictReader(source_handle)
                    if tuple(reader.fieldnames or ()) != (
                        "time",
                        "open",
                        "high",
                        "low",
                        "close",
                        "volume",
                    ):
                        raise IntegratedSourceRejected("typed_source_schema_mismatch")
                    for raw in reader:
                        normalize_started = time.perf_counter()
                        row = legacy.normalize_row(raw, symbol=str(symbol))
                        normalization_seconds += time.perf_counter() - normalize_started
                        if row is None:
                            continue
                        if set(row) != {
                            "time",
                            "time_utc",
                            "symbol",
                            "open",
                            "high",
                            "low",
                            "close",
                            "volume",
                        }:
                            raise IntegratedSourceRejected(
                                "typed_normalized_row_schema_mismatch"
                            )
                        serialize_started = time.perf_counter()
                        payload_handle.write(
                            _ROW.pack(
                                _timestamp_microseconds(row),
                                float(row["open"]),
                                float(row["high"]),
                                float(row["low"]),
                                float(row["close"]),
                                float(row["volume"]),
                            )
                        )
                        _update_rows_digest(rows_digest, row)
                        serialization_seconds += time.perf_counter() - serialize_started
                        row_count += 1
                payload_handle.seek(0)
                payload_handle.write(_HEADER.pack(_MAGIC, row_count))
                payload_handle.flush()
                os.fsync(payload_handle.fileno())

            hashing_started = time.perf_counter()
            payload_sha256 = _file_sha256(payload_path)
            hashing_seconds = time.perf_counter() - hashing_started
            payload_bytes = payload_path.stat().st_size
            if (
                expected_normalized_row_count is not None
                and row_count != int(expected_normalized_row_count)
            ):
                raise IntegratedSourceRejected("typed_normalized_row_count_mismatch")
            if (
                expected_normalized_root is not None
                and rows_digest.hexdigest() != expected_normalized_root
            ):
                raise IntegratedSourceRejected("typed_normalized_root_mismatch")
            manifest: dict[str, Any] = {
                "schema": TYPED_MANIFEST_SCHEMA,
                "identity": identity,
                "identity_root_sha256": identity_root,
                "payload_sha256": payload_sha256,
                "payload_byte_count": payload_bytes,
                "row_count": row_count,
                "rows_root_sha256": rows_digest.hexdigest(),
            }
            manifest["manifest_root_sha256"] = _manifest_root(manifest)
            manifest_bytes = _canonical_bytes(manifest) + b"\n"
            (temporary / "manifest.json").write_bytes(manifest_bytes)
            (temporary / "SEALED").write_bytes(
                manifest["manifest_root_sha256"].encode("ascii") + b"\n"
            )
            try:
                temporary.rename(entry)
            except FileExistsError:
                shutil.rmtree(temporary)
            rows = self._load_entry(entry, expected_identity=identity)
            self._add_metrics(
                cold_partition_count=1,
                normalized_row_count=len(rows),
                bytes_read=int(source_byte_count),
                bytes_written=payload_bytes + len(manifest_bytes) + 65,
                normalization_seconds=normalization_seconds,
                serialization_seconds=serialization_seconds,
                hashing_seconds=hashing_seconds,
            )
            del started
            return TypedPartitionResult(rows, False, identity_root, entry)
        except Exception:
            if temporary.exists():
                shutil.rmtree(temporary)
            raise

    def _load_entry(
        self, entry: Path, *, expected_identity: Mapping[str, Any]
    ) -> tuple[dict[str, Any], ...]:
        started = time.perf_counter()
        manifest_path = entry / "manifest.json"
        payload_path = entry / "rows.bin"
        seal_path = entry / "SEALED"
        try:
            manifest_raw = manifest_path.read_bytes()
            manifest = json.loads(manifest_raw)
            seal = seal_path.read_bytes()
        except (OSError, UnicodeError, json.JSONDecodeError):
            raise IntegratedSourceRejected("typed_manifest_invalid") from None
        if (
            type(manifest) is not dict
            or set(manifest) != _MANIFEST_FIELDS
            or manifest.get("schema") != TYPED_MANIFEST_SCHEMA
            or manifest_raw != _canonical_bytes(manifest) + b"\n"
            or manifest.get("manifest_root_sha256") != _manifest_root(manifest)
            or seal
            != str(manifest.get("manifest_root_sha256") or "").encode("ascii") + b"\n"
        ):
            raise IntegratedSourceRejected("typed_manifest_identity_mismatch")
        if (
            manifest.get("identity") != dict(expected_identity)
            or manifest.get("identity_root_sha256") != _root(expected_identity)
        ):
            raise IntegratedSourceRejected("typed_cache_identity_mismatch")
        try:
            payload = payload_path.read_bytes()
        except OSError:
            raise IntegratedSourceRejected("typed_payload_missing") from None
        if (
            manifest.get("payload_byte_count") != len(payload)
            or manifest.get("payload_sha256")
            != hashlib.sha256(payload).hexdigest()
            or len(payload) < _HEADER.size
        ):
            raise IntegratedSourceRejected("typed_payload_identity_mismatch")
        magic, row_count = _HEADER.unpack_from(payload, 0)
        if (
            magic != _MAGIC
            or row_count != manifest.get("row_count")
            or len(payload) != _HEADER.size + row_count * _ROW.size
        ):
            raise IntegratedSourceRejected("typed_payload_framing_mismatch")
        rows: list[dict[str, Any]] = []
        rows_digest = hashlib.sha256(
            b"gtos.replay_acceleration.canonical_rows.v1\n"
        )
        symbol = str(expected_identity["symbol"])
        offset = _HEADER.size
        for _index in range(row_count):
            micros, *values = _ROW.unpack_from(payload, offset)
            offset += _ROW.size
            row = _row_from_values(symbol=symbol, micros=micros, values=values)
            _update_rows_digest(rows_digest, row)
            rows.append(row)
        if manifest.get("rows_root_sha256") != rows_digest.hexdigest():
            raise IntegratedSourceRejected("typed_rows_root_mismatch")
        self._add_metrics(
            verification_seconds=time.perf_counter() - started,
            bytes_read=len(payload) + len(manifest_raw) + len(seal),
        )
        return tuple(rows)


@dataclass(frozen=True)
class _AcceptedPartition:
    source_path: Path
    symbol: str
    physical_timeframe: str
    source_payload_root: str
    source_byte_count: int
    normalized_root: str
    normalized_row_count: int
    partition_identity: Mapping[str, Any]
    binding: SourceBatchBinding
    batch_root: str


@dataclass(frozen=True)
class AcceptedSourceCandidate:
    """Logical source identity committed by the accepted source bundle."""

    source_path: Path
    symbol: str
    mapped_symbol: str
    physical_timeframe: str
    source_family: str


def _accepted_source_candidates(
    bundle: "_AcceptedSourceBundle",
    *,
    symbol: str,
    physical_timeframe: str,
    source_family_order: Iterable[str],
) -> tuple[AcceptedSourceCandidate, ...]:
    """Project the exact logical source order committed by an accepted bundle."""

    symbol_value = str(symbol)
    timeframe_value = str(physical_timeframe).upper()
    family_order = tuple(str(value) for value in source_family_order)
    family_rank = {family: index for index, family in enumerate(family_order)}
    candidates: list[AcceptedSourceCandidate] = []
    for partition in bundle.partitions.values():
        if (
            partition.symbol != symbol_value
            or partition.physical_timeframe.upper() != timeframe_value
        ):
            continue
        source_path = partition.source_path
        source_family = source_path.parent.name
        suffix = f"_{timeframe_value}.csv"
        if not source_path.name.endswith(suffix):
            raise IntegratedSourceRejected(
                "accepted_source_filename_identity_invalid"
            )
        mapped_symbol = source_path.name[: -len(suffix)]
        candidates.append(
            AcceptedSourceCandidate(
                source_path=source_path,
                symbol=symbol_value,
                mapped_symbol=mapped_symbol,
                physical_timeframe=timeframe_value,
                source_family=source_family,
            )
        )
    if not candidates:
        raise IntegratedSourceRejected("accepted_source_partition_missing")
    return tuple(
        sorted(
            candidates,
            key=lambda value: (
                family_rank.get(value.source_family, len(family_rank)),
                str(value.source_path),
            ),
        )
    )


def _rows_root(rows: Iterable[Mapping[str, Any]]) -> str:
    digest = hashlib.sha256(b"gtos.replay_acceleration.canonical_rows.v1\n")
    for row in rows:
        digest.update(_canonical_bytes(dict(row)))
        digest.update(b"\n")
    return digest.hexdigest()


class _AcceptedSourceBundle:
    """Exact index over the independently accepted immutable source bundle."""

    def __init__(
        self,
        *,
        source_bundle_dir: Path,
        selection_path: Path,
        expected_bundle_root: str,
        expected_source_plan_digest: str,
    ) -> None:
        started = time.perf_counter()
        self.source_bundle_dir = lexical_path(Path(source_bundle_dir))
        self.selection_path = lexical_path(Path(selection_path))
        try:
            bundle_raw, _bundle_identity = read_regular_nofollow(
                self.source_bundle_dir / "bundle.json",
                code="accepted_source_bundle_invalid",
            )
            selection_raw, _selection_identity = read_regular_nofollow(
                self.selection_path,
                code="accepted_source_bundle_invalid",
            )
            bundle = json.loads(bundle_raw)
            selection = json.loads(selection_raw)
            seal, _seal_identity = read_regular_nofollow(
                self.source_bundle_dir / "SEALED",
                code="accepted_source_bundle_invalid",
            )
        except (
            ImmutableEvidenceError,
            OSError,
            UnicodeError,
            json.JSONDecodeError,
        ):
            raise IntegratedSourceRejected("accepted_source_bundle_invalid") from None
        if type(bundle) is not dict or type(selection) is not dict:
            raise IntegratedSourceRejected("accepted_source_bundle_invalid")
        bundle_projection = dict(bundle)
        bundle_root = bundle_projection.pop("bundle_root_sha256", None)
        selection_projection = dict(selection)
        selection_root = selection_projection.pop("selection_root_sha256", None)
        if (
            bundle_raw != _canonical_bytes(bundle) + b"\n"
            or selection_raw != _canonical_bytes(selection) + b"\n"
            or bundle.get("schema")
            != "gtos.replay_acceleration.persisted_source_bundle.v1"
            or selection.get("schema")
            != "gtos.replay_acceleration.slice_selection.v1"
            or bundle_root != _root(bundle_projection)
            or selection_root != _root(selection_projection)
            or seal != str(bundle_root or "").encode("ascii") + b"\n"
        ):
            raise IntegratedSourceRejected("accepted_source_bundle_invalid")
        if bundle_root != expected_bundle_root:
            raise IntegratedSourceRejected("accepted_source_bundle_root_mismatch")
        if (
            not _valid_root(expected_source_plan_digest)
            or selection.get("expected_source_plan_digest_sha256")
            != expected_source_plan_digest
            or bundle.get("expected_source_plan_digest_sha256")
            != expected_source_plan_digest
            or bundle.get("selection_root_sha256") != selection_root
            or bundle.get("status") != "SEALED_SOURCE_EQUIVALENCE_BUNDLE"
            or bundle.get("policy_execution_entered") is not False
            or selection.get("policy_execution_entered") is not False
        ):
            raise IntegratedSourceRejected("accepted_source_bundle_authority_mismatch")
        current_source_implementation_root = accepted_source_implementation_root()
        if (
            bundle.get("accepted_cache_implementation_root")
            != current_source_implementation_root
        ):
            raise IntegratedSourceRejected(
                "accepted_source_implementation_identity_stale"
            )
        selection_records = selection.get("physical_partitions")
        bundle_records = bundle.get("physical_partitions")
        if not isinstance(selection_records, list) or not isinstance(bundle_records, list):
            raise IntegratedSourceRejected("accepted_source_partition_index_invalid")
        selection_by_id = {
            str(record.get("partition_id")): record
            for record in selection_records
            if isinstance(record, Mapping)
        }
        bundle_by_id = {
            str(record.get("partition_id")): record
            for record in bundle_records
            if isinstance(record, Mapping)
        }
        if (
            len(selection_by_id) != len(selection_records)
            or len(bundle_by_id) != len(bundle_records)
            or set(selection_by_id) != set(bundle_by_id)
            or len(selection_by_id) != 96
        ):
            raise IntegratedSourceRejected("accepted_source_partition_index_invalid")

        registry = CacheAdmissionRegistry()
        registry.admit(
            stage=SOURCE_BYTES_STAGE,
            implementation_identity_root=accepted_source_implementation_root(),
            config_projection_keys=(),
        )
        self.cache = ImmutableSourceBatchCache(
            self.source_bundle_dir / "cache", registry=registry
        )
        partitions: dict[str, _AcceptedPartition] = {}
        projection_roots: set[str] = set()
        for partition_id in sorted(selection_by_id):
            selected = selection_by_id[partition_id]
            persisted = bundle_by_id[partition_id]
            try:
                binding = SourceBatchBinding.from_dict(persisted["binding"])
                source_path = Path(str(selected["source_path"])).resolve()
                symbol = str(selected["symbol"])
                physical_timeframe = str(selected["physical_timeframe"])
                payload_root = str(selected["source_file_sha256"])
                source_byte_count = int(selected["byte_count"])
                normalized_root = str(persisted["normalized_root_sha256"])
                normalized_row_count = int(persisted["normalized_record_count"])
                partition_identity = selected["partition_identity"]
                batch_root = str(persisted["batch_root"])
            except (KeyError, TypeError, ValueError):
                raise IntegratedSourceRejected(
                    "accepted_source_partition_identity_invalid"
                ) from None
            if (
                persisted.get("payload_root") != payload_root
                or persisted.get("symbol") != symbol
                or persisted.get("physical_timeframe") != physical_timeframe
                or binding.partition_symbol != symbol
                or binding.source_path_root != _source_path_root(source_path)
                or selected.get("source_path_root") != binding.source_path_root
                or selected.get("source_path_root") != _source_path_root(source_path)
                or selected.get("source_plan_digest_sha256")
                not in (None, expected_source_plan_digest)
                or not isinstance(partition_identity, Mapping)
            ):
                raise IntegratedSourceRejected(
                    "accepted_source_partition_identity_invalid"
                )
            if binding.implementation_root != current_source_implementation_root:
                raise IntegratedSourceRejected(
                    "accepted_source_implementation_identity_stale"
                )
            projection_roots.add(binding.config_projection_root)
            partitions[str(source_path)] = _AcceptedPartition(
                source_path=source_path,
                symbol=symbol,
                physical_timeframe=physical_timeframe,
                source_payload_root=payload_root,
                source_byte_count=source_byte_count,
                normalized_root=normalized_root,
                normalized_row_count=normalized_row_count,
                partition_identity=dict(partition_identity),
                binding=binding,
                batch_root=batch_root,
            )
        if len(partitions) != 96 or len(projection_roots) != 1:
            raise IntegratedSourceRejected("accepted_source_partition_index_invalid")
        self.partitions = partitions
        self.bundle_root = str(bundle_root)
        self.selection_root = str(selection_root)
        self.source_plan_digest = expected_source_plan_digest
        self.config_projection_root = next(iter(projection_roots))
        self.validation_seconds = time.perf_counter() - started

    def partition(self, source_path: Path, *, symbol: str) -> _AcceptedPartition:
        resolved = str(Path(source_path).resolve())
        partition = self.partitions.get(resolved)
        if partition is None:
            raise IntegratedSourceRejected("source_path_not_in_accepted_bundle")
        if partition.symbol != str(symbol):
            raise IntegratedSourceRejected("accepted_source_symbol_mismatch")
        return partition

    def open_text(
        self, partition: _AcceptedPartition
    ) -> ContextManager[TextIO]:
        lease = self.cache.acquire_lease(
            partition.batch_root,
            expected_binding=partition.binding,
        )
        return lease._open_text(
            source_path=partition.source_path,
            symbol=partition.symbol,
            partition_identity=partition.partition_identity,
        )


class AcceptedPhysicalSourceReference:
    """Legacy CSV-normalization oracle over an accepted immutable source bundle.

    This adapter deliberately has no typed cache.  It shares only the sealed
    source selection and raw source bytes with the accelerated route, then
    exercises the original ``load_csv_rows`` decoder/normalizer independently.
    """

    def __init__(self, *, accepted_bundle: _AcceptedSourceBundle) -> None:
        self._bundle = accepted_bundle
        self._metrics: dict[str, int] = {
            "physical_parse_count": 0,
            "physical_normalized_row_count": 0,
            "physical_source_bytes_read": 0,
        }

    @classmethod
    def from_accepted_bundle(
        cls,
        *,
        source_bundle_dir: Path,
        selection_path: Path,
        expected_bundle_root: str,
        expected_source_plan_digest: str,
    ) -> "AcceptedPhysicalSourceReference":
        return cls(
            accepted_bundle=_AcceptedSourceBundle(
                source_bundle_dir=source_bundle_dir,
                selection_path=selection_path,
                expected_bundle_root=expected_bundle_root,
                expected_source_plan_digest=expected_source_plan_digest,
            )
        )

    def authority(self) -> dict[str, Any]:
        return {
            "schema": (
                "gtos.replay_acceleration.accepted_physical_source_reference.v1"
            ),
            "source_bundle_root_sha256": self._bundle.bundle_root,
            "selection_root_sha256": self._bundle.selection_root,
            "source_plan_digest_sha256": self._bundle.source_plan_digest,
            "config_projection_root_sha256": (
                self._bundle.config_projection_root
            ),
            "partition_count": len(self._bundle.partitions),
            "symbol_count": len(
                {
                    partition.symbol
                    for partition in self._bundle.partitions.values()
                }
            ),
            "loader": "legacy_csv_dict_reader_and_normalize_row",
            "typed_cache_enabled": False,
            "sparse_bar_cache_enabled": False,
            "candidate_cache_enabled": False,
            "policy_state_cache_enabled": False,
            "policy_execution_entered": False,
            "metrics": dict(self._metrics),
        }

    def accepted_source_candidates(
        self,
        *,
        symbol: str,
        physical_timeframe: str,
        source_family_order: Iterable[str],
    ) -> tuple[AcceptedSourceCandidate, ...]:
        return _accepted_source_candidates(
            self._bundle,
            symbol=symbol,
            physical_timeframe=physical_timeframe,
            source_family_order=source_family_order,
        )

    def _load_rows(
        self,
        path: Path,
        *,
        symbol: str,
    ) -> tuple[tuple[dict[str, Any], ...], _AcceptedPartition]:
        partition = self._bundle.partition(path, symbol=symbol)
        lease = self._bundle.cache.acquire_lease(
            partition.batch_root,
            expected_binding=partition.binding,
        )
        rows = legacy.load_csv_rows(
            path,
            symbol=symbol,
            source_batch_lease=lease,
            source_partition=partition.partition_identity,
        )
        if (
            len(rows) != partition.normalized_row_count
            or _rows_root(rows) != partition.normalized_root
        ):
            raise IntegratedSourceRejected(
                "accepted_physical_normalization_mismatch"
            )
        self._metrics["physical_parse_count"] += 1
        self._metrics["physical_normalized_row_count"] += len(rows)
        self._metrics["physical_source_bytes_read"] += (
            partition.source_byte_count
        )
        return rows, partition

    def load_file(
        self,
        path: Path,
        *,
        symbol: str,
    ) -> tuple[
        tuple[dict[str, Any], ...],
        dict[str, tuple[dict[str, Any], ...]],
        str,
    ]:
        rows, partition = self._load_rows(path, symbol=symbol)
        return rows, legacy.rows_by_day(rows), partition.source_payload_root

    def load_file_days(
        self,
        path: Path,
        *,
        symbol: str,
        days: Iterable[str],
    ) -> tuple[
        tuple[dict[str, Any], ...],
        dict[str, tuple[dict[str, Any], ...]],
        str,
    ]:
        rows, partition = self._load_rows(path, symbol=symbol)
        selected, grouped = select_days(rows, days=days)
        return selected, grouped, partition.source_payload_root

    def load_file_replay_lookback_window(
        self,
        path: Path,
        *,
        symbol: str,
        timeframe: str,
        days: Iterable[str],
        min_total_rows: int,
    ) -> tuple[
        tuple[dict[str, Any], ...],
        dict[str, tuple[dict[str, Any], ...]],
        str,
        dict[str, Any],
    ]:
        all_rows, _partition = self._load_rows(path, symbol=symbol)
        rows, grouped, metadata = select_replay_lookback_window(
            all_rows,
            timeframe=timeframe,
            days=days,
            min_total_rows=min_total_rows,
        )
        metadata["bounded_replay_source_path"] = str(path)
        valid_times = [legacy.parse_row_time(row) for row in rows]
        valid_times = [value for value in valid_times if value is not None]
        bounds = (
            (legacy.iso(min(valid_times)), legacy.iso(max(valid_times)))
            if valid_times
            else (None, None)
        )
        sha256 = legacy.stable_sha256(
            {**metadata, "first_last": bounds, "rows": rows}
        )
        return rows, grouped, sha256, metadata


class RealReplaySourceAccelerator:
    """Source/normalization adapter for the actual broad replay resolver."""

    def __init__(
        self,
        *,
        accepted_bundle: _AcceptedSourceBundle,
        typed_cache_root: Path,
    ) -> None:
        self._bundle = accepted_bundle
        self._cache = TypedNormalizedPartitionCache(
            typed_cache_root,
            source_bundle_root=accepted_bundle.bundle_root,
            config_projection_root=accepted_bundle.config_projection_root,
        )
        self._prewarm: dict[str, Any] = {
            "requested": False,
            "worker_count": 0,
            "barrier_complete": False,
            "seconds": 0.0,
        }

    @classmethod
    def from_accepted_bundle(
        cls,
        *,
        source_bundle_dir: Path,
        selection_path: Path,
        typed_cache_root: Path,
        expected_bundle_root: str,
        expected_source_plan_digest: str,
    ) -> "RealReplaySourceAccelerator":
        return cls(
            accepted_bundle=_AcceptedSourceBundle(
                source_bundle_dir=source_bundle_dir,
                selection_path=selection_path,
                expected_bundle_root=expected_bundle_root,
                expected_source_plan_digest=expected_source_plan_digest,
            ),
            typed_cache_root=typed_cache_root,
        )

    def authority(self) -> dict[str, Any]:
        return {
            "schema": "gtos.replay_acceleration.real_source_authority.v1",
            "source_bundle_root_sha256": self._bundle.bundle_root,
            "selection_root_sha256": self._bundle.selection_root,
            "source_plan_digest_sha256": self._bundle.source_plan_digest,
            "config_projection_root_sha256": self._bundle.config_projection_root,
            "normalizer_code_root_sha256": self._cache.normalizer_code_root,
            "partition_count": len(self._bundle.partitions),
            "symbol_count": len(
                {partition.symbol for partition in self._bundle.partitions.values()}
            ),
            "policy_execution_entered": False,
            "candidate_cache_enabled": False,
            "policy_state_cache_enabled": False,
            "cross_symbol_prewarm_barrier": dict(self._prewarm),
            "bundle_validation_seconds": self._bundle.validation_seconds,
            "typed_cache_metrics": self._cache.metrics(),
        }

    def accepted_source_candidates(
        self,
        *,
        symbol: str,
        physical_timeframe: str,
        source_family_order: Iterable[str],
    ) -> tuple[AcceptedSourceCandidate, ...]:
        """Return bundle-bound logical paths without touching those filesystem paths."""

        return _accepted_source_candidates(
            self._bundle,
            symbol=symbol,
            physical_timeframe=physical_timeframe,
            source_family_order=source_family_order,
        )

    def _load_partition(self, partition: _AcceptedPartition) -> TypedPartitionResult:
        return self._cache.load_or_build_partition(
            source_path=partition.source_path,
            symbol=partition.symbol,
            physical_timeframe=partition.physical_timeframe,
            source_payload_root=partition.source_payload_root,
            open_text=lambda: self._bundle.open_text(partition),
            source_byte_count=partition.source_byte_count,
            expected_normalized_root=partition.normalized_root,
            expected_normalized_row_count=partition.normalized_row_count,
        )

    def prewarm_all(self, *, workers: int) -> dict[str, Any]:
        worker_count = int(workers)
        if worker_count < 1 or worker_count > 8:
            raise IntegratedSourceRejected("typed_prewarm_worker_count_invalid")
        started = time.perf_counter()
        partitions = sorted(
            self._bundle.partitions.values(),
            key=lambda value: (value.symbol, value.physical_timeframe),
        )
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            roots = list(
                executor.map(
                    lambda partition: self._load_partition(
                        partition
                    ).partition_root_sha256,
                    partitions,
                )
            )
        self._prewarm = {
            "requested": True,
            "worker_count": worker_count,
            "partition_count": len(partitions),
            "partition_set_root_sha256": _root(roots),
            "barrier_complete": len(roots) == len(partitions),
            "seconds": time.perf_counter() - started,
        }
        if self._prewarm["barrier_complete"] is not True:
            raise IntegratedSourceRejected("typed_prewarm_barrier_incomplete")
        return dict(self._prewarm)

    def load_file(
        self,
        path: Path,
        *,
        symbol: str,
    ) -> tuple[
        tuple[dict[str, Any], ...],
        dict[str, tuple[dict[str, Any], ...]],
        str,
    ]:
        partition = self._bundle.partition(path, symbol=symbol)
        result = self._load_partition(partition)
        return result.rows, legacy.rows_by_day(result.rows), partition.source_payload_root

    def load_file_days(
        self,
        path: Path,
        *,
        symbol: str,
        days: Iterable[str],
    ) -> tuple[
        tuple[dict[str, Any], ...],
        dict[str, tuple[dict[str, Any], ...]],
        str,
    ]:
        partition = self._bundle.partition(path, symbol=symbol)
        result = self._load_partition(partition)
        rows, grouped = select_days(result.rows, days=days)
        return rows, grouped, partition.source_payload_root

    def load_file_replay_lookback_window(
        self,
        path: Path,
        *,
        symbol: str,
        timeframe: str,
        days: Iterable[str],
        min_total_rows: int,
    ) -> tuple[
        tuple[dict[str, Any], ...],
        dict[str, tuple[dict[str, Any], ...]],
        str,
        dict[str, Any],
    ]:
        partition = self._bundle.partition(path, symbol=symbol)
        result = self._load_partition(partition)
        rows, grouped, metadata = select_replay_lookback_window(
            result.rows,
            timeframe=timeframe,
            days=days,
            min_total_rows=min_total_rows,
        )
        metadata["bounded_replay_source_path"] = str(path)
        valid_times = [legacy.parse_row_time(row) for row in rows]
        valid_times = [value for value in valid_times if value is not None]
        bounds = (
            (legacy.iso(min(valid_times)), legacy.iso(max(valid_times)))
            if valid_times
            else (None, None)
        )
        sha256 = legacy.stable_sha256(
            {**metadata, "first_last": bounds, "rows": rows}
        )
        return rows, grouped, sha256, metadata


def select_days(
    rows: Iterable[Mapping[str, Any]], *, days: Iterable[str]
) -> tuple[tuple[dict[str, Any], ...], dict[str, tuple[dict[str, Any], ...]]]:
    day_key = tuple(sorted(set(str(day) for day in days)))
    grouped: dict[str, list[dict[str, Any]]] = {day: [] for day in day_key}
    for source_row in rows:
        row = dict(source_row)
        timestamp = legacy.parse_row_time(row)
        if timestamp is None:
            continue
        day = timestamp.astimezone(timezone.utc).date().isoformat()
        if day in grouped:
            grouped[day].append(row)
    sorted_grouped = {
        day: tuple(
            sorted(
                values,
                key=lambda item: str(item.get("time_utc") or item.get("time") or ""),
            )
        )
        for day, values in grouped.items()
    }
    selected = tuple(row for day in day_key for row in sorted_grouped.get(day, ()))
    return selected, sorted_grouped


def select_replay_lookback_window(
    rows: Iterable[Mapping[str, Any]],
    *,
    timeframe: str,
    days: Iterable[str],
    min_total_rows: int,
) -> tuple[
    tuple[dict[str, Any], ...],
    dict[str, tuple[dict[str, Any], ...]],
    dict[str, Any],
]:
    day_key = tuple(sorted(set(str(day) for day in days)))
    if not day_key:
        return (), {}, {
            "source_hash_scope": "missing_or_unbounded_source_file",
            "bounded_replay_lookback_start_day": None,
            "bounded_replay_lookback_end_day": None,
            "bounded_replay_row_count": 0,
        }
    timeframe_value = str(timeframe).upper()
    minutes_per_row = {"D1": 24 * 60, "H4": 4 * 60, "H1": 60, "M15": 15}.get(
        timeframe_value, 15
    )
    required_rows = max(
        int(min_total_rows),
        int(legacy.DEFAULT_LOOKBACKS.get(timeframe_value, min_total_rows) or 0),
    )
    lookback_days = max(
        1,
        (max(required_rows, 1) * minutes_per_row + 24 * 60 - 1) // (24 * 60),
    )
    first_day = date.fromisoformat(day_key[0])
    last_day = date.fromisoformat(day_key[-1])
    start_day = first_day - timedelta(days=lookback_days + 2)
    end_day = last_day + timedelta(days=3)
    pre_window_rows: deque[dict[str, Any]] = deque(
        maxlen=max(required_rows + 2, int(min_total_rows) + 2)
    )
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    selected_rows: list[dict[str, Any]] = []
    for source_row in rows:
        row = dict(source_row)
        timestamp = legacy.parse_row_time(row)
        if timestamp is None:
            continue
        row_day = timestamp.astimezone(timezone.utc).date()
        if row_day < first_day:
            pre_window_rows.append(row)
            continue
        if row_day > end_day:
            break
        selected_rows.append(row)
        grouped[row_day.isoformat()].append(row)
    selected_rows = list(pre_window_rows) + selected_rows
    for row in pre_window_rows:
        timestamp = legacy.parse_row_time(row)
        if timestamp is not None:
            grouped[timestamp.astimezone(timezone.utc).date().isoformat()].append(row)
    sorted_grouped = {
        day: tuple(
            sorted(
                values,
                key=lambda item: str(item.get("time_utc") or item.get("time") or ""),
            )
        )
        for day, values in grouped.items()
    }
    rows_tuple = tuple(
        sorted(
            selected_rows,
            key=lambda item: str(item.get("time_utc") or item.get("time") or ""),
        )
    )
    metadata = {
        "source_hash_scope": "bounded_replay_lookback_slice_not_full_historical_file_hash",
        "bounded_replay_lookback_start_day": start_day.isoformat(),
        "bounded_replay_lookback_end_day": end_day.isoformat(),
        "bounded_replay_requested_days": list(day_key),
        "bounded_replay_min_total_rows": int(min_total_rows),
        "bounded_replay_required_live_lookback_rows": required_rows,
        "bounded_replay_prewindow_selected_rows": len(pre_window_rows),
        "bounded_replay_source_selection_mode": "count_preserving_predecision_lookback_slice",
        "bounded_replay_row_count": len(rows_tuple),
    }
    return rows_tuple, sorted_grouped, metadata


__all__ = [
    "AcceptedPhysicalSourceReference",
    "IntegratedSourceRejected",
    "RealReplaySourceAccelerator",
    "TypedNormalizedPartitionCache",
    "TypedPartitionResult",
    "select_days",
    "select_replay_lookback_window",
]
