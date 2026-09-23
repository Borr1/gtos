"""Bounded, lossless replay proof spooling outside canonical Python ledgers.

The sink is deliberately replay-only.  It accepts canonical producer rows,
serializes them with the same JSON contract used by the legacy JSONL writer,
compresses bounded groups of rows as authenticated blocks, and reconstructs
rows in their original role-local order after the economic reducer finishes.

Only append-only roles should be routed through :class:`ReplayCompactLedger`.
Mutable candidate/scorecard/order lifecycle rows stay on the legacy list path
until a future typed patch-event contract proves their exact semantics.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
import copy
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import struct
from typing import Any

from compression import zstd


COMPACT_EVENT_SCHEMA = "gtos.replay_acceleration.compact_event_sink.v3"
ROW_FRAME_COMPACT_EVENT_SCHEMA = "gtos.replay_acceleration.compact_event_sink.v2"
LEGACY_COMPACT_EVENT_SCHEMA = "gtos.replay_acceleration.compact_event_sink.v1"
COMPACT_EVENT_MANIFEST = "COMPACT_EVENT_MANIFEST.json"
COMPACT_EVENT_ROLES: tuple[str, ...] = (
    "candidate",
    "decision",
    "scorecard",
    "order",
    "trade",
    "oracle",
    "missed",
)

_ROW_FRAME_HEADER = struct.Struct(">QQQ32s")
_BLOCK_HEADER = struct.Struct(">QQQQ32s")
_ROW_LENGTH = struct.Struct(">Q")
_DEFAULT_MAX_SHARD_BYTES = 128 * 1024 * 1024
_HARD_MAX_SHARD_BYTES = 128 * 1024 * 1024
_DEFAULT_MAX_RAW_EVENT_BYTES = 128 * 1024 * 1024
_HARD_MAX_RAW_EVENT_BYTES = 128 * 1024 * 1024
_DEFAULT_TARGET_RAW_BLOCK_BYTES = 4 * 1024 * 1024
_HARD_TARGET_RAW_BLOCK_BYTES = 128 * 1024 * 1024
_MIN_BLOCK_SHARD_BYTES = _BLOCK_HEADER.size + 32
_MIN_ROW_FRAME_SHARD_BYTES = _ROW_FRAME_HEADER.size + 32
_MANIFEST_ROOT_FIELDS: tuple[str, ...] = (
    "schema",
    "format",
    "compression",
    "max_shard_bytes",
    "max_raw_event_bytes",
    "target_raw_block_bytes",
    "roles",
    "row_counts",
    "raw_byte_counts",
    "raw_stream_sha256",
    "role_shards",
    "resident_canonical_row_count",
    "relational_identity_audit",
)
_ROW_FRAME_MANIFEST_ROOT_FIELDS = tuple(
    field for field in _MANIFEST_ROOT_FIELDS if field != "target_raw_block_bytes"
)
_LEGACY_MANIFEST_ROOT_FIELDS = tuple(
    field
    for field in _ROW_FRAME_MANIFEST_ROOT_FIELDS
    if field != "max_raw_event_bytes"
)


class CompactEventSinkError(ValueError):
    """Fail-closed compact-event contract error."""


def _stable_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
        default=str,
    ).encode("utf-8")


def _legacy_jsonl_bytes(row: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(
            row,
            sort_keys=True,
            default=str,
        )
        + "\n"
    ).encode("utf-8")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_candidate_instance_key(row: Mapping[str, Any]) -> str:
    return str(row.get("canonical_replay_candidate_instance_key") or "").strip()


def _diagnostic_fallback_candidate_instance_key(row: Mapping[str, Any]) -> str:
    for field in (
        "source_bound_replay_candidate_instance_key",
        "risk_finalizer_probe_instance_key",
    ):
        value = str(row.get(field) or "").strip()
        if value:
            return value
    candidate_id = str(
        row.get("candidate_id") or row.get("selected_candidate_id") or ""
    ).strip()
    decision_time = str(
        row.get("decision_time_utc")
        or row.get("candidate_instance_time_utc")
        or ""
    ).strip()
    return f"{candidate_id}@@{decision_time}" if candidate_id and decision_time else ""


@dataclass
class _OpenShard:
    role: str
    index: int
    path: Path
    handle: Any
    sha256: Any = field(default_factory=hashlib.sha256)
    bytes_written: int = 0
    raw_bytes: int = 0
    row_count: int = 0
    block_count: int = 0
    first_ordinal: int | None = None
    last_ordinal: int | None = None

    def write_block(
        self,
        *,
        first_ordinal: int,
        row_count: int,
        rows_raw_bytes: int,
        body: bytes,
        compressed: bytes,
    ) -> None:
        raw_sha256 = hashlib.sha256(body).digest()
        frame = _BLOCK_HEADER.pack(
            first_ordinal,
            row_count,
            len(compressed),
            len(body),
            raw_sha256,
        ) + compressed
        self.handle.write(frame)
        self.sha256.update(frame)
        self.bytes_written += len(frame)
        self.raw_bytes += rows_raw_bytes
        self.row_count += row_count
        self.block_count += 1
        self.first_ordinal = (
            first_ordinal if self.first_ordinal is None else self.first_ordinal
        )
        self.last_ordinal = first_ordinal + row_count - 1

    def close(self, *, root: Path) -> dict[str, Any]:
        self.handle.flush()
        self.handle.close()
        return {
            "path": self.path.relative_to(root).as_posix(),
            "role": self.role,
            "shard_index": self.index,
            "rows": self.row_count,
            "blocks": self.block_count,
            "bytes": self.bytes_written,
            "raw_bytes": self.raw_bytes,
            "sha256": self.sha256.hexdigest(),
            "first_ordinal": self.first_ordinal,
            "last_ordinal": self.last_ordinal,
        }


@dataclass
class _PendingBlock:
    rows: list[tuple[int, bytes]] = field(default_factory=list)
    body_bytes: int = 0

    def append(self, *, ordinal: int, raw: bytes) -> None:
        self.rows.append((ordinal, raw))
        self.body_bytes += _ROW_LENGTH.size + len(raw)


class ReplayCompactEventSink:
    """Write bounded compressed role shards and reconstruct exact JSON rows."""

    def __init__(
        self,
        *,
        root: Path,
        max_shard_bytes: int = _DEFAULT_MAX_SHARD_BYTES,
        max_raw_event_bytes: int = _DEFAULT_MAX_RAW_EVENT_BYTES,
        target_raw_block_bytes: int = _DEFAULT_TARGET_RAW_BLOCK_BYTES,
        compression_level: int = 1,
        defer_seal_to_caller: bool = False,
        row_projectors: Mapping[
            str,
            Callable[[Mapping[str, Any]], Mapping[str, Any]],
        ]
        | None = None,
        retained_row_projectors: Mapping[
            str,
            Callable[[Mapping[str, Any]], Mapping[str, Any]],
        ]
        | None = None,
    ) -> None:
        self.root = Path(root)
        self._schema = COMPACT_EVENT_SCHEMA
        self.max_shard_bytes = int(max_shard_bytes)
        self.max_raw_event_bytes = int(max_raw_event_bytes)
        self.target_raw_block_bytes = int(target_raw_block_bytes)
        self.compression_level = int(compression_level)
        self.defer_seal_to_caller = bool(defer_seal_to_caller)
        self._row_projectors = dict(row_projectors or {})
        self._retained_row_projectors = dict(retained_row_projectors or {})
        if any(
            role not in COMPACT_EVENT_ROLES or not callable(projector)
            for role, projector in self._row_projectors.items()
        ):
            raise CompactEventSinkError("row_projector_invalid")
        if any(
            role not in COMPACT_EVENT_ROLES or not callable(projector)
            for role, projector in self._retained_row_projectors.items()
        ):
            raise CompactEventSinkError("retained_row_projector_invalid")
        if self.max_shard_bytes < _MIN_BLOCK_SHARD_BYTES:
            raise CompactEventSinkError("max_shard_bytes_too_small")
        if self.max_shard_bytes > _HARD_MAX_SHARD_BYTES:
            raise CompactEventSinkError("max_shard_bytes_exceeds_hard_cap")
        if self.max_raw_event_bytes < 1:
            raise CompactEventSinkError("max_raw_event_bytes_too_small")
        if self.max_raw_event_bytes > _HARD_MAX_RAW_EVENT_BYTES:
            raise CompactEventSinkError("max_raw_event_bytes_exceeds_hard_cap")
        if self.target_raw_block_bytes < 1:
            raise CompactEventSinkError("target_raw_block_bytes_too_small")
        if self.target_raw_block_bytes > _HARD_TARGET_RAW_BLOCK_BYTES:
            raise CompactEventSinkError("target_raw_block_bytes_exceeds_hard_cap")
        if self.root.exists() or self.root.is_symlink():
            raise CompactEventSinkError("root_must_be_new")
        self.root.mkdir(parents=True, exist_ok=False)
        self._open: dict[str, _OpenShard] = {}
        self._pending: dict[str, _PendingBlock] = {}
        self._shards: dict[str, list[dict[str, Any]]] = {
            role: [] for role in COMPACT_EVENT_ROLES
        }
        self._row_counts: Counter[str] = Counter()
        self._raw_byte_counts: Counter[str] = Counter()
        self._raw_stream_hashers = {
            role: hashlib.sha256() for role in COMPACT_EVENT_ROLES
        }
        self._observed_row_counts: Counter[str] = Counter()
        self._observed_missing_keys: Counter[str] = Counter()
        self._observed_keys: dict[str, set[str]] = {
            role: set() for role in ("candidate", "missed", "order", "trade")
        }
        self._observed_fallback_keys: dict[str, set[str]] = {
            role: set() for role in ("candidate", "missed", "order", "trade")
        }
        self._sealed = False
        self._aborted = False
        self._reopened = False
        self._authority: dict[str, Any] | None = None

    @classmethod
    def open_sealed(
        cls,
        *,
        root: Path,
        expected_authority_root_sha256: str,
    ) -> "ReplayCompactEventSink":
        """Reopen an immutable sink only through its externally bound root."""

        root = Path(root)
        manifest_path = root / COMPACT_EVENT_MANIFEST
        if root.is_symlink() or manifest_path.is_symlink() or not manifest_path.is_file():
            raise CompactEventSinkError("sealed_manifest_missing_or_symlink")
        try:
            authority = json.loads(manifest_path.read_bytes())
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CompactEventSinkError("sealed_manifest_invalid") from exc
        if not isinstance(authority, dict):
            raise CompactEventSinkError("sealed_manifest_invalid")
        schema = authority.get("schema")
        root_fields = (
            _MANIFEST_ROOT_FIELDS
            if schema == COMPACT_EVENT_SCHEMA
            else _ROW_FRAME_MANIFEST_ROOT_FIELDS
            if schema == ROW_FRAME_COMPACT_EVENT_SCHEMA
            else _LEGACY_MANIFEST_ROOT_FIELDS
            if schema == LEGACY_COMPACT_EVENT_SCHEMA
            else ()
        )
        allowed_fields = {
            *root_fields,
            "status",
            "authority_root_sha256",
        }
        if set(authority) != allowed_fields:
            raise CompactEventSinkError("sealed_manifest_schema_fields_invalid")
        deterministic = {field: authority[field] for field in root_fields}
        recomputed_root = hashlib.sha256(_stable_json_bytes(deterministic)).hexdigest()
        if (
            authority.get("status") != "sealed"
            or authority.get("roles") != list(COMPACT_EVENT_ROLES)
            or authority.get("authority_root_sha256") != recomputed_root
            or expected_authority_root_sha256 != recomputed_root
        ):
            raise CompactEventSinkError("sealed_manifest_authority_root_mismatch")
        max_shard_bytes = int(authority.get("max_shard_bytes") or 0)
        minimum_shard_bytes = (
            _MIN_BLOCK_SHARD_BYTES
            if schema == COMPACT_EVENT_SCHEMA
            else _MIN_ROW_FRAME_SHARD_BYTES
        )
        if not (minimum_shard_bytes <= max_shard_bytes <= _HARD_MAX_SHARD_BYTES):
            raise CompactEventSinkError("sealed_manifest_shard_bound_invalid")

        sink = cls.__new__(cls)
        sink.root = root
        sink._schema = schema
        sink.max_shard_bytes = max_shard_bytes
        sink.max_raw_event_bytes = int(
            authority.get("max_raw_event_bytes")
            if schema in {COMPACT_EVENT_SCHEMA, ROW_FRAME_COMPACT_EVENT_SCHEMA}
            else _HARD_MAX_RAW_EVENT_BYTES
        )
        if not (1 <= sink.max_raw_event_bytes <= _HARD_MAX_RAW_EVENT_BYTES):
            raise CompactEventSinkError("sealed_manifest_raw_event_bound_invalid")
        sink.target_raw_block_bytes = int(
            authority.get("target_raw_block_bytes")
            if schema == COMPACT_EVENT_SCHEMA
            else _DEFAULT_TARGET_RAW_BLOCK_BYTES
        )
        if not (
            1
            <= sink.target_raw_block_bytes
            <= _HARD_TARGET_RAW_BLOCK_BYTES
        ):
            raise CompactEventSinkError("sealed_manifest_raw_block_bound_invalid")
        compression = authority.get("compression")
        compression = compression if isinstance(compression, Mapping) else {}
        sink.compression_level = int(compression.get("level") or 0)
        sink.defer_seal_to_caller = False
        sink._row_projectors = {}
        sink._retained_row_projectors = {}
        sink._open = {}
        sink._pending = {}
        sink._shards = copy.deepcopy(authority["role_shards"])
        sink._row_counts = Counter(
            {
                role: int(authority["row_counts"].get(role) or 0)
                for role in COMPACT_EVENT_ROLES
            }
        )
        sink._raw_byte_counts = Counter(
            {
                role: int(authority["raw_byte_counts"].get(role) or 0)
                for role in COMPACT_EVENT_ROLES
            }
        )
        sink._raw_stream_hashers = {}
        sink._observed_row_counts = Counter()
        sink._observed_missing_keys = Counter()
        sink._observed_keys = {
            role: set() for role in ("candidate", "missed", "order", "trade")
        }
        sink._observed_fallback_keys = {
            role: set() for role in ("candidate", "missed", "order", "trade")
        }
        sink._sealed = True
        sink._aborted = False
        sink._reopened = True
        sink._authority = {
            **authority,
            "manifest_path": manifest_path.relative_to(root).as_posix(),
            "manifest_sha256": _sha256_file(manifest_path),
        }
        return sink

    @property
    def sealed(self) -> bool:
        return self._sealed

    def _require_role(self, role: str) -> str:
        normalized = str(role or "").strip()
        if normalized not in COMPACT_EVENT_ROLES:
            raise CompactEventSinkError(f"unknown_role:{normalized}")
        return normalized

    def retained_row_projector(
        self,
        role: str,
    ) -> Callable[[Mapping[str, Any]], Mapping[str, Any]] | None:
        """Return an in-memory retention projector, never a proof projector."""

        return self._retained_row_projectors.get(self._require_role(role))

    def _new_shard(self, role: str) -> _OpenShard:
        index = len(self._shards[role])
        path = self.root / f"{role}-{index:05d}.zstf"
        if path.exists() or path.is_symlink():
            raise CompactEventSinkError("shard_path_must_be_new")
        shard = _OpenShard(
            role=role,
            index=index,
            path=path,
            handle=path.open("xb"),
        )
        self._open[role] = shard
        return shard

    def _close_role_shard(self, role: str) -> None:
        shard = self._open.pop(role, None)
        if shard is None:
            return
        metadata = shard.close(root=self.root)
        if metadata["bytes"] > self.max_shard_bytes:
            raise CompactEventSinkError("bounded_shard_contract_violated")
        self._shards[role].append(metadata)

    @staticmethod
    def _block_body(rows: Sequence[tuple[int, bytes]]) -> bytes:
        return b"".join(
            _ROW_LENGTH.pack(len(raw)) + raw for _ordinal, raw in rows
        )

    def _write_block_rows(
        self,
        role: str,
        rows: Sequence[tuple[int, bytes]],
    ) -> None:
        if not rows:
            return
        first_ordinal = rows[0][0]
        if any(
            ordinal != first_ordinal + offset
            for offset, (ordinal, _raw) in enumerate(rows)
        ):
            raise CompactEventSinkError("pending_block_ordinal_gap")
        body = self._block_body(rows)
        compressed = zstd.compress(body, level=self.compression_level)
        frame_bytes = _BLOCK_HEADER.size + len(compressed)
        if frame_bytes > self.max_shard_bytes:
            if len(rows) == 1:
                raise CompactEventSinkError(
                    f"event_exceeds_max_shard_bytes:{role}:{frame_bytes}"
                )
            midpoint = len(rows) // 2
            self._write_block_rows(role, rows[:midpoint])
            self._write_block_rows(role, rows[midpoint:])
            return
        shard = self._open.get(role)
        if shard is None:
            shard = self._new_shard(role)
        elif shard.bytes_written + frame_bytes > self.max_shard_bytes:
            self._close_role_shard(role)
            shard = self._new_shard(role)
        shard.write_block(
            first_ordinal=first_ordinal,
            row_count=len(rows),
            rows_raw_bytes=sum(len(raw) for _ordinal, raw in rows),
            body=body,
            compressed=compressed,
        )

    def _flush_role_block(self, role: str) -> None:
        pending = self._pending.get(role)
        if pending is None or not pending.rows:
            return
        self._write_block_rows(role, pending.rows)
        self._pending.pop(role, None)

    def observe(self, role: str, row: Mapping[str, Any]) -> None:
        role = self._require_role(role)
        if self._sealed:
            raise CompactEventSinkError("already_sealed")
        if not isinstance(row, Mapping):
            raise CompactEventSinkError("row_must_be_mapping")
        if role not in self._observed_keys:
            return
        self._observed_row_counts[role] += 1
        key = _canonical_candidate_instance_key(row)
        if key:
            self._observed_keys[role].add(key)
        else:
            self._observed_missing_keys[role] += 1
            fallback = _diagnostic_fallback_candidate_instance_key(row)
            if fallback:
                self._observed_fallback_keys[role].add(fallback)

    def _append_canonical_row(
        self,
        role: str,
        row: Mapping[str, Any],
        *,
        ordinal: int,
    ) -> None:
        raw = _legacy_jsonl_bytes(row)
        if len(raw) > self.max_raw_event_bytes:
            raise CompactEventSinkError(
                f"raw_event_exceeds_max_bytes:{role}:{len(raw)}"
            )
        encoded_row_bytes = _ROW_LENGTH.size + len(raw)
        pending = self._pending.get(role)
        if (
            pending is not None
            and pending.rows
            and pending.body_bytes + encoded_row_bytes
            > self.target_raw_block_bytes
        ):
            self._flush_role_block(role)
            pending = None
        if pending is None:
            pending = _PendingBlock()
            self._pending[role] = pending
        pending.append(ordinal=ordinal, raw=raw)
        self._raw_byte_counts[role] += len(raw)
        self._raw_stream_hashers[role].update(raw)

    def append(self, role: str, row: Mapping[str, Any]) -> None:
        role = self._require_role(role)
        if self._aborted:
            raise CompactEventSinkError("sink_aborted")
        if self._sealed:
            raise CompactEventSinkError("already_sealed")
        if not isinstance(row, Mapping):
            raise CompactEventSinkError("row_must_be_mapping")
        original_key = _canonical_candidate_instance_key(row)
        original_fallback_key = _diagnostic_fallback_candidate_instance_key(
            row
        )
        projected_row = row
        projector = self._row_projectors.get(role)
        if projector is not None:
            projected_row = projector(row)
            if not isinstance(projected_row, Mapping):
                raise CompactEventSinkError(
                    f"row_projector_result_not_mapping:{role}"
                )
            projected_key = _canonical_candidate_instance_key(projected_row)
            if original_key != projected_key:
                raise CompactEventSinkError(
                    f"row_projector_candidate_identity_changed:{role}"
                )
            if (
                not original_key
                and original_fallback_key
                != _diagnostic_fallback_candidate_instance_key(projected_row)
            ):
                raise CompactEventSinkError(
                    f"row_projector_fallback_identity_changed:{role}"
                )
        ordinal = int(self._row_counts[role])
        self._append_canonical_row(role, projected_row, ordinal=ordinal)
        self._row_counts[role] += 1
        self.observe(role, projected_row)

    def ledger(self, role: str) -> "ReplayCompactLedger":
        return ReplayCompactLedger(sink=self, role=self._require_role(role))

    def seal(self) -> dict[str, Any]:
        if self._aborted:
            raise CompactEventSinkError("sink_aborted")
        if self._sealed:
            if self._authority is None:
                raise CompactEventSinkError("sealed_authority_missing")
            return copy.deepcopy(self._authority)
        for role in COMPACT_EVENT_ROLES:
            self._flush_role_block(role)
            self._close_role_shard(role)
        deterministic = {
            "schema": COMPACT_EVENT_SCHEMA,
            "format": "authenticated_role_ordinal_zstd_blocks",
            "compression": {
                "algorithm": "zstd",
                "level": self.compression_level,
                "block_header": ">QQQQ32s",
                "row_length_encoding": ">Q",
            },
            "max_shard_bytes": self.max_shard_bytes,
            "max_raw_event_bytes": self.max_raw_event_bytes,
            "target_raw_block_bytes": self.target_raw_block_bytes,
            "roles": list(COMPACT_EVENT_ROLES),
            "row_counts": {
                role: int(self._row_counts[role]) for role in COMPACT_EVENT_ROLES
            },
            "raw_byte_counts": {
                role: int(self._raw_byte_counts[role])
                for role in COMPACT_EVENT_ROLES
            },
            "raw_stream_sha256": {
                role: self._raw_stream_hashers[role].hexdigest()
                for role in COMPACT_EVENT_ROLES
            },
            "role_shards": copy.deepcopy(self._shards),
            "resident_canonical_row_count": 0,
            "relational_identity_audit": self.relational_identity_audit(),
        }
        authority_root = hashlib.sha256(_stable_json_bytes(deterministic)).hexdigest()
        authority = {
            **deterministic,
            "status": "sealed",
            "authority_root_sha256": authority_root,
        }
        manifest_path = self.root / COMPACT_EVENT_MANIFEST
        with manifest_path.open("x", encoding="utf-8") as handle:
            json.dump(authority, handle, indent=2, sort_keys=True)
            handle.write("\n")
        authority["manifest_path"] = manifest_path.relative_to(self.root).as_posix()
        authority["manifest_sha256"] = _sha256_file(manifest_path)
        self._authority = authority
        self._sealed = True
        return copy.deepcopy(authority)

    def abort(self) -> None:
        """Close any open shard handles after an upstream replay failure."""

        if self._sealed:
            return
        self._aborted = True
        self._pending.clear()
        for shard in tuple(self._open.values()):
            try:
                shard.handle.flush()
            except Exception:
                pass
            try:
                shard.handle.close()
            except Exception:
                pass
        self._open.clear()

    def _validate_shard(self, metadata: Mapping[str, Any]) -> Path:
        relative = str(metadata.get("path") or "")
        if not relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise CompactEventSinkError("shard_relative_path_invalid")
        path = self.root / relative
        if path.is_symlink() or not path.is_file():
            raise CompactEventSinkError("shard_missing_or_symlink")
        expected_bytes = int(metadata.get("bytes") or -1)
        if path.stat().st_size != expected_bytes:
            raise CompactEventSinkError("shard_byte_count_mismatch")
        expected_sha = str(metadata.get("sha256") or "")
        if _sha256_file(path) != expected_sha:
            raise CompactEventSinkError("shard_sha256_mismatch")
        return path

    def iter_rows(self, role: str) -> Iterator[dict[str, Any]]:
        role = self._require_role(role)
        if not self._sealed or self._authority is None:
            raise CompactEventSinkError("sink_not_sealed")
        schema = self._authority.get("schema")
        expected_ordinal = 0
        stream_hasher = hashlib.sha256()
        total_raw_bytes = 0
        for metadata in self._authority["role_shards"][role]:
            path = self._validate_shard(metadata)
            with path.open("rb") as handle:
                shard_rows = 0
                shard_blocks = 0
                while True:
                    header_size = (
                        _BLOCK_HEADER.size
                        if schema == COMPACT_EVENT_SCHEMA
                        else _ROW_FRAME_HEADER.size
                    )
                    header = handle.read(header_size)
                    if not header:
                        break
                    if len(header) != header_size:
                        raise CompactEventSinkError("truncated_frame_header")
                    if schema == COMPACT_EVENT_SCHEMA:
                        (
                            first_ordinal,
                            block_row_count,
                            compressed_len,
                            raw_len,
                            raw_sha,
                        ) = _BLOCK_HEADER.unpack(header)
                        if first_ordinal != expected_ordinal:
                            raise CompactEventSinkError("role_ordinal_mismatch")
                        max_raw_block_bytes = max(
                            self.target_raw_block_bytes,
                            self.max_raw_event_bytes + _ROW_LENGTH.size,
                        )
                        if (
                            block_row_count < 1
                            or raw_len < block_row_count * (_ROW_LENGTH.size + 1)
                            or raw_len > max_raw_block_bytes
                        ):
                            raise CompactEventSinkError("raw_block_length_invalid")
                    else:
                        (
                            first_ordinal,
                            compressed_len,
                            raw_len,
                            raw_sha,
                        ) = _ROW_FRAME_HEADER.unpack(header)
                        block_row_count = 1
                        if first_ordinal != expected_ordinal:
                            raise CompactEventSinkError("role_ordinal_mismatch")
                        if raw_len < 1 or raw_len > self.max_raw_event_bytes:
                            raise CompactEventSinkError("raw_frame_length_invalid")
                    if (
                        compressed_len < 1
                        or compressed_len > self.max_shard_bytes - header_size
                    ):
                        raise CompactEventSinkError("compressed_frame_length_invalid")
                    compressed = handle.read(compressed_len)
                    if len(compressed) != compressed_len:
                        raise CompactEventSinkError("truncated_compressed_frame")
                    try:
                        decompressor = zstd.ZstdDecompressor()
                        block_body = decompressor.decompress(
                            compressed,
                            max_length=raw_len + 1,
                        )
                    except (EOFError, zstd.ZstdError) as exc:
                        raise CompactEventSinkError("zstd_frame_invalid") from exc
                    if (
                        len(block_body) != raw_len
                        or not decompressor.eof
                        or decompressor.unused_data
                    ):
                        raise CompactEventSinkError("raw_frame_byte_count_mismatch")
                    if hashlib.sha256(block_body).digest() != raw_sha:
                        raise CompactEventSinkError("raw_frame_sha256_mismatch")
                    if schema == COMPACT_EVENT_SCHEMA:
                        offset = 0
                        raw_rows: list[bytes] = []
                        for _index in range(block_row_count):
                            if offset + _ROW_LENGTH.size > len(block_body):
                                raise CompactEventSinkError(
                                    "truncated_block_row_length"
                                )
                            (row_length,) = _ROW_LENGTH.unpack_from(
                                block_body,
                                offset,
                            )
                            offset += _ROW_LENGTH.size
                            if (
                                row_length < 1
                                or row_length > self.max_raw_event_bytes
                                or offset + row_length > len(block_body)
                            ):
                                raise CompactEventSinkError(
                                    "block_row_length_invalid"
                                )
                            raw_rows.append(
                                block_body[offset : offset + row_length]
                            )
                            offset += row_length
                        if offset != len(block_body):
                            raise CompactEventSinkError(
                                "block_trailing_bytes_invalid"
                            )
                    else:
                        raw_rows = [block_body]
                    for raw in raw_rows:
                        if not raw.endswith(b"\n") or raw.count(b"\n") != 1:
                            raise CompactEventSinkError(
                                "canonical_row_framing_invalid"
                            )
                        try:
                            row = json.loads(raw)
                        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                            raise CompactEventSinkError(
                                "canonical_row_json_invalid"
                            ) from exc
                        if not isinstance(row, dict):
                            raise CompactEventSinkError(
                                "reconstructed_row_not_mapping"
                            )
                        stream_hasher.update(raw)
                        total_raw_bytes += len(raw)
                        expected_ordinal += 1
                        shard_rows += 1
                        yield row
                    shard_blocks += 1
                if shard_rows != int(metadata.get("rows") or 0):
                    raise CompactEventSinkError("shard_row_count_mismatch")
                if schema == COMPACT_EVENT_SCHEMA and shard_blocks != int(
                    metadata.get("blocks") or 0
                ):
                    raise CompactEventSinkError("shard_block_count_mismatch")
        if expected_ordinal != int(self._authority["row_counts"][role]):
            raise CompactEventSinkError("role_row_count_mismatch")
        if total_raw_bytes != int(self._authority["raw_byte_counts"][role]):
            raise CompactEventSinkError("role_raw_byte_count_mismatch")
        if stream_hasher.hexdigest() != self._authority["raw_stream_sha256"][role]:
            raise CompactEventSinkError("role_raw_stream_sha256_mismatch")

    def row_count(self, role: str) -> int:
        role = self._require_role(role)
        return int(self._row_counts[role])

    def relational_identity_audit(self) -> dict[str, Any]:
        if self._reopened and self._authority is not None:
            audit = self._authority.get("relational_identity_audit")
            if isinstance(audit, Mapping):
                return copy.deepcopy(dict(audit))
        candidate_keys = self._observed_keys["candidate"]
        observed_downstream_keys = (
            self._observed_keys["missed"]
            | self._observed_keys["order"]
            | self._observed_keys["trade"]
        )
        candidate_rows = int(self._observed_row_counts["candidate"])
        candidate_missing = int(self._observed_missing_keys["candidate"])
        candidate_duplicates = candidate_rows - len(candidate_keys) - candidate_missing
        candidate_minus_downstream = sorted(
            candidate_keys - observed_downstream_keys
        )
        downstream_minus_candidate = sorted(
            observed_downstream_keys - candidate_keys
        )
        missing = {
            role: int(self._observed_missing_keys[role])
            for role in ("candidate", "missed", "order", "trade")
        }
        fallback_only = {
            role: len(self._observed_fallback_keys[role])
            for role in ("candidate", "missed", "order", "trade")
        }
        identity_coverage_exact = not any(
            (
                sum(missing.values()),
                candidate_duplicates,
                len(candidate_minus_downstream),
                len(downstream_minus_candidate),
            )
        )
        return {
            "schema": (
                "gtos.final_moonshot.broad_replay."
                "candidate_relational_identity_coverage.v2"
            ),
            "status": (
                "incomplete_identity_coverage_only_requires_exit_account_"
                "terminal_reconciliation"
            ),
            "exact": False,
            "identity_coverage_exact": identity_coverage_exact,
            "terminal_reconciliation_complete": False,
            "graph": "research_timewarp",
            "production_parity": False,
            "candidate_rows": candidate_rows,
            "candidate_unique_instance_keys": len(candidate_keys),
            "candidate_duplicate_instance_rows": candidate_duplicates,
            "missed_rows": int(self._observed_row_counts["missed"]),
            "order_rows": int(self._observed_row_counts["order"]),
            "trade_rows": int(self._observed_row_counts["trade"]),
            "observed_downstream_union_unique_instance_keys": len(
                observed_downstream_keys
            ),
            "missing_instance_key_counts": missing,
            "fallback_only_instance_key_counts": fallback_only,
            "candidate_minus_observed_downstream_union_count": len(
                candidate_minus_downstream
            ),
            "observed_downstream_union_minus_candidate_count": len(
                downstream_minus_candidate
            ),
            "candidate_minus_observed_downstream_union_sample": (
                candidate_minus_downstream[:8]
            ),
            "observed_downstream_union_minus_candidate_sample": (
                downstream_minus_candidate[:8]
            ),
            "missed_order_overlap": len(
                self._observed_keys["missed"] & self._observed_keys["order"]
            ),
            "missed_trade_overlap": len(
                self._observed_keys["missed"] & self._observed_keys["trade"]
            ),
            "order_trade_overlap": len(
                self._observed_keys["order"] & self._observed_keys["trade"]
            ),
        }

    def relational_identity_sets(self) -> dict[str, set[str]]:
        """Return bounded identity indexes, never canonical proof rows."""

        return {
            role: set(keys)
            for role, keys in self._observed_keys.items()
        }


class ReplayCompactLedger(Sequence[dict[str, Any]]):
    """Read-only-after-seal sequence facade for one compact sink role."""

    def __init__(self, *, sink: ReplayCompactEventSink, role: str) -> None:
        self.sink = sink
        self.role = role
        self._materialization_transform: Callable[[dict[str, Any]], None] | None = None

    def append(self, row: Mapping[str, Any]) -> None:
        self.sink.append(self.role, row)

    def extend(self, rows: Iterable[Mapping[str, Any]]) -> None:
        for row in rows:
            self.append(row)

    def set_materialization_transform(
        self,
        transform: Callable[[dict[str, Any]], None],
    ) -> None:
        self._materialization_transform = transform

    def __len__(self) -> int:
        return self.sink.row_count(self.role)

    def __iter__(self) -> Iterator[dict[str, Any]]:
        for row in self.sink.iter_rows(self.role):
            if self._materialization_transform is not None:
                self._materialization_transform(row)
            yield row

    def __getitem__(self, index: int | slice) -> Any:
        raise CompactEventSinkError("random_access_not_supported")


class ReplayObservedLedger(list[dict[str, Any]]):
    """Legacy mutable list that reports immutable relational identities."""

    def __init__(self, *, sink: ReplayCompactEventSink, role: str) -> None:
        super().__init__()
        self.sink = sink
        self.role = sink._require_role(role)
        self._retained_row_projector = sink.retained_row_projector(self.role)
        self._projected_prefix = 0

    def append(self, row: dict[str, Any]) -> None:
        self.sink.observe(self.role, row)
        super().append(row)

    def extend(self, rows: Iterable[dict[str, Any]]) -> None:
        for row in rows:
            self.append(row)

    def project_completed_prefix(self, stop: int | None = None) -> int:
        """Release completed full rows while preserving stable list indexes."""

        if self._retained_row_projector is None:
            return 0
        bounded_stop = len(self) if stop is None else min(int(stop), len(self))
        if bounded_stop < self._projected_prefix:
            raise CompactEventSinkError("retained_projection_prefix_reversed")
        projected_count = 0
        for index in range(self._projected_prefix, bounded_stop):
            original = list.__getitem__(self, index)
            projected = self._retained_row_projector(original)
            if not isinstance(projected, Mapping):
                raise CompactEventSinkError("retained_row_projection_invalid")
            retained = copy.deepcopy(dict(projected))
            original_key = _canonical_candidate_instance_key(original)
            retained_key = _canonical_candidate_instance_key(retained)
            if original_key != retained_key:
                raise CompactEventSinkError(
                    "retained_row_projection_candidate_identity_changed"
                )
            list.__setitem__(self, index, retained)
            projected_count += 1
        self._projected_prefix = bounded_stop
        return projected_count
