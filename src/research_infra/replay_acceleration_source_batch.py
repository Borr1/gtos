"""Outcome-blind tracer bullet for immutable replay source-byte batches.

Only the raw source-byte stage is admissible here.  Normalization and every
stateful replay stage remain outside this cache boundary until a separate,
enforced read-set proof admits them prospectively.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import hmac
import io
import json
import os
import secrets
import stat
import subprocess
import sys
import time
import weakref
from contextlib import contextmanager
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterator, Mapping


SOURCE_BYTES_STAGE = "replay.source_bytes.v1"
CONDITIONAL_OR_ARM_LOCAL_STAGES = (
    "replay.normalization",
    "replay.snapshot_mso",
    "replay.raw_candidate_generation",
    "replay.candidate_evaluation",
    "replay.scheduler_materialization",
    "replay.downstream_policy",
)
FACTORIAL_ARMS = frozenset(("S0R0", "S1R0", "S0R1", "S1R1"))
MANIFEST_SCHEMA = "gtos.replay_acceleration.immutable_source_batch.v1"
CONFIG_PROJECTION_SCHEMA = "gtos.replay_acceleration.config_projection.v1"
_MANIFEST_FIELDS = frozenset(
    (
        "schema",
        "stage",
        "implementation_root",
        "source_identity_root",
        "source_path_root",
        "partition_root",
        "partition_symbol",
        "config_projection_root",
        "config_projection_keys",
        "payload_root",
        "byte_count",
        "record_count",
    )
)
_BINDING_FIELDS = frozenset(
    (
        "stage",
        "implementation_root",
        "source_identity_root",
        "source_path_root",
        "partition_root",
        "partition_symbol",
        "config_projection_root",
        "config_projection_keys",
    )
)
_ARM_STATE_PREFIXES = (
    "arm.",
    "account.",
    "broker.",
    "event_queue.",
    "pending.",
    "open_positions.",
    "closed_positions.",
    "accepted_risk.",
    "order_sequence.",
)
_CACHE_ROOT_CREATE_RETRIES = 8


def _canonical_bytes(value: Any) -> bytes:
    material: str | None = None
    try:
        material = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError):
        pass
    if material is None:
        value = None
        raise ConfigReadRejected("config_projection_not_canonical")
    return material.encode("utf-8")


def _root(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _bytes_root(value: bytes | memoryview) -> str:
    return hashlib.sha256(value).hexdigest()


def _valid_root(value: Any) -> bool:
    return type(value) is str and len(value) == 64 and all(
        character in "009abcdef" for character in value
    )


def _record_count(payload: bytes | memoryview) -> int:
    source_bytes = bytes(payload)
    handle: io.TextIOWrapper | None = None
    malformed = False
    framed_records = 0
    try:
        with io.TextIOWrapper(
            io.BytesIO(source_bytes),
            encoding="utf-8",
            newline="",
        ) as handle:
            framed_records = sum(
                1 for row in csv.reader(handle, strict=True) if row
            )
    except (csv.Error, UnicodeError):
        malformed = True
    if malformed:
        handle = None
        payload = b""
        source_bytes = b""
        raise SourceBatchRejected("malformed_csv_framing")
    return max(0, framed_records - 1)


def _source_path_root(path: Path) -> str:
    return _root({"source_path": os.path.abspath(os.fspath(path))})


def _empty_config_projection_root() -> str:
    return _root(
        {
            "schema": CONFIG_PROJECTION_SCHEMA,
            "keys": [],
            "values": [],
        }
    )


_REDACTED_PARTITION_ROOT = _root({"partition": "redacted"})


class ConfigReadRejected(RuntimeError):
    """A config consumer attempted a read outside its sealed projection."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class SourceBatchRejected(RuntimeError):
    """Fail-closed source-batch rejection with a redacted structural surface."""

    def __init__(
        self,
        code: str,
        *,
        stage: str = SOURCE_BYTES_STAGE,
        partition_root: str | None = None,
    ) -> None:
        del stage
        self.code = code
        self.stage = SOURCE_BYTES_STAGE
        self.partition_root = (
            partition_root if _valid_root(partition_root) else _REDACTED_PARTITION_ROOT
        )
        super().__init__(code)

    def structural_output(self) -> dict[str, Any]:
        return {
            "equality": False,
            "roots": {},
            "counts": {"failures": 1},
            "failure": {
                "code": self.code,
                "stage": self.stage,
                "partition_root": self.partition_root,
            },
        }


@dataclass(frozen=True)
class ConfigProjection:
    keys: tuple[str, ...]
    root: str


class ConfigReadGuard:
    """Expose only declared config keys and seal the exact observed read set."""

    def __init__(
        self,
        config: Mapping[str, Any],
        *,
        known_keys: set[str] | frozenset[str],
        projection_keys: set[str] | frozenset[str],
    ) -> None:
        self._config = dict(config)
        self._known_keys = frozenset(str(key) for key in known_keys)
        self._projection_keys = frozenset(str(key) for key in projection_keys)
        self._observed_reads: set[str] = set()

    def __getitem__(self, key: str) -> Any:
        key = str(key)
        if key.startswith(_ARM_STATE_PREFIXES):
            raise ConfigReadRejected("arm_state_read_forbidden")
        if key not in self._known_keys or key not in self._config:
            raise ConfigReadRejected("unknown_config_read")
        if key not in self._projection_keys:
            raise ConfigReadRejected("out_of_projection_config_read")
        self._observed_reads.add(key)
        return self._config[key]

    def get(self, key: str, default: Any = None) -> Any:
        del default
        return self[key]

    def seal_projection(self) -> ConfigProjection:
        if self._observed_reads != set(self._projection_keys):
            raise ConfigReadRejected("config_read_set_mismatch")
        keys = tuple(sorted(self._projection_keys))
        values = [[key, self._config[key]] for key in keys]
        return ConfigProjection(
            keys=keys,
            root=_root(
                {
                    "schema": CONFIG_PROJECTION_SCHEMA,
                    "keys": list(keys),
                    "values": values,
                }
            ),
        )


_SOURCE_CONSUMER_COMPONENTS = (
    (
        "timewarp_csv_source_consumer",
        Path(__file__).with_name("v4_timewarp_simulated_live_research_loop.py"),
        (
            "iso",
            "parse_row_time",
            "compact_source_records_field",
            "normalize_row",
            "load_csv_rows",
        ),
        ("CSV_TIME_KEYS",),
    ),
    (
        "shared_utc_parser",
        Path(__file__).with_name("wave4r_replay_microstructure.py"),
        ("parse_utc",),
        (),
    ),
)


def _assignment_target_names(target: ast.AST) -> set[str]:
    if isinstance(target, ast.Name):
        return {target.id}
    if isinstance(target, (ast.Tuple, ast.List)):
        names: set[str] = set()
        for item in target.elts:
            names.update(_assignment_target_names(item))
        return names
    return set()


def _top_level_bound_names(node: ast.AST) -> set[str]:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return {node.name}
    if isinstance(node, ast.Import):
        return {
            alias.asname or alias.name.split(".", 1)[0]
            for alias in node.names
        }
    if isinstance(node, ast.ImportFrom):
        return {
            alias.asname or alias.name
            for alias in node.names
            if alias.name != "*"
        }
    if isinstance(node, ast.Assign):
        names: set[str] = set()
        for target in node.targets:
            names.update(_assignment_target_names(target))
        return names
    if isinstance(node, ast.AnnAssign):
        return _assignment_target_names(node.target)
    if isinstance(node, ast.AugAssign):
        return _assignment_target_names(node.target)
    return set()


def _source_consumer_dependency_projection(
    module: ast.Module,
    *,
    seed_names: tuple[str, ...],
) -> list[list[Any]]:
    """Bind each selected symbol plus its transitive module-level dependencies."""

    bindings: dict[str, list[tuple[int, ast.AST]]] = {}
    bound_names_by_index: dict[int, tuple[str, ...]] = {}
    for index, node in enumerate(module.body):
        names = tuple(sorted(_top_level_bound_names(node)))
        if not names:
            continue
        bound_names_by_index[index] = names
        for name in names:
            bindings.setdefault(name, []).append((index, node))

    if set(seed_names) - set(bindings):
        raise SourceBatchRejected("source_consumer_identity_unavailable")

    pending = list(seed_names)
    visited_names: set[str] = set()
    selected_nodes: dict[int, ast.AST] = {}
    while pending:
        name = pending.pop()
        if name in visited_names:
            continue
        visited_names.add(name)
        for index, node in bindings.get(name, ()):
            if index in selected_nodes:
                continue
            selected_nodes[index] = node
            for nested in ast.walk(node):
                if (
                    isinstance(nested, ast.Name)
                    and isinstance(nested.ctx, ast.Load)
                    and nested.id in bindings
                    and nested.id not in visited_names
                ):
                    pending.append(nested.id)

    return [
        [
            index,
            list(bound_names_by_index[index]),
            ast.dump(selected_nodes[index], include_attributes=False),
        ]
        for index in sorted(selected_nodes)
    ]


@lru_cache(maxsize=1)
def _source_consumer_component_root() -> str:
    """Bind the finite CSV source reader, not the entire economic replay engine."""

    components: list[dict[str, Any]] = []
    for role, path, function_names, constant_names in _SOURCE_CONSUMER_COMPONENTS:
        try:
            module = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError, UnicodeError):
            raise SourceBatchRejected(
                "source_consumer_identity_unavailable"
            ) from None
        seed_names = tuple((*function_names, *constant_names))
        components.append(
            {
                "role": role,
                "seed_names": list(seed_names),
                "dependency_bindings": _source_consumer_dependency_projection(
                    module,
                    seed_names=seed_names,
                ),
            }
        )
    return _root(
        {
            "schema": "gtos.replay_acceleration.csv_source_consumer_identity.v2",
            "components": components,
        }
    )


@lru_cache(maxsize=1)
def implementation_root() -> str:
    digest = hashlib.sha256()
    with Path(__file__).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    component_roots = [
        ["immutable_source_batch", digest.hexdigest()],
        ["csv_source_consumer", _source_consumer_component_root()],
    ]
    return _root(
        {
            "components": component_roots,
            "python_implementation": sys.implementation.name,
            "python_version": list(sys.version_info[:3]),
        }
    )


@dataclass(frozen=True)
class SourceBatchBinding:
    stage: str
    implementation_root: str
    source_identity_root: str
    source_path_root: str
    partition_root: str
    partition_symbol: str
    config_projection_root: str
    config_projection_keys: tuple[str, ...]

    @classmethod
    def create(
        cls,
        *,
        stage: str,
        source_identity: Any,
        source_path: Path,
        partition_identity: Any,
        config_projection: ConfigProjection,
    ) -> "SourceBatchBinding":
        current_implementation_root = implementation_root()
        if (
            not isinstance(config_projection, ConfigProjection)
            or not _valid_root(config_projection.root)
            or tuple(config_projection.keys)
            != tuple(sorted(set(config_projection.keys)))
        ):
            raise SourceBatchRejected("config_projection_malformed", stage=stage)
        if (
            not isinstance(partition_identity, Mapping)
            or type(partition_identity.get("symbol")) is not str
            or not partition_identity["symbol"]
        ):
            raise SourceBatchRejected("partition_identity_malformed", stage=stage)
        return cls(
            stage=str(stage),
            implementation_root=current_implementation_root,
            source_identity_root=_root({"source_identity": source_identity}),
            source_path_root=_source_path_root(source_path),
            partition_root=_root({"partition_identity": partition_identity}),
            partition_symbol=partition_identity["symbol"],
            config_projection_root=config_projection.root,
            config_projection_keys=tuple(config_projection.keys),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "implementation_root": self.implementation_root,
            "source_identity_root": self.source_identity_root,
            "source_path_root": self.source_path_root,
            "partition_root": self.partition_root,
            "partition_symbol": self.partition_symbol,
            "config_projection_root": self.config_projection_root,
            "config_projection_keys": list(self.config_projection_keys),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "SourceBatchBinding":
        stage = SOURCE_BYTES_STAGE
        partition_root: str | None = None
        try:
            if not isinstance(value, Mapping) or set(value) != _BINDING_FIELDS:
                raise ValueError("binding_fields")
            identity_fields = (
                "stage",
                "implementation_root",
                "source_identity_root",
                "source_path_root",
                "partition_root",
                "partition_symbol",
                "config_projection_root",
            )
            if not all(type(value[field]) is str for field in identity_fields):
                raise ValueError("binding_identity_types")
            stage = value["stage"]
            implementation = value["implementation_root"]
            source_identity = value["source_identity_root"]
            source_path = value["source_path_root"]
            partition = value["partition_root"]
            partition_symbol = value["partition_symbol"]
            projection = value["config_projection_root"]
            raw_keys = value["config_projection_keys"]
            if not isinstance(raw_keys, list) or not all(
                isinstance(key, str) for key in raw_keys
            ):
                raise ValueError("binding_projection_keys")
            keys = tuple(raw_keys)
            if (
                stage != SOURCE_BYTES_STAGE
                or not all(
                    _valid_root(root)
                    for root in (
                        implementation,
                        source_identity,
                        source_path,
                        partition,
                        projection,
                    )
                )
                or not partition_symbol
                or keys != tuple(sorted(set(keys)))
                or keys
                or projection != _empty_config_projection_root()
            ):
                raise ValueError("binding_identity")
            partition_root = partition
            return cls(
                stage=stage,
                implementation_root=implementation,
                source_identity_root=source_identity,
                source_path_root=source_path,
                partition_root=partition,
                partition_symbol=partition_symbol,
                config_projection_root=projection,
                config_projection_keys=keys,
            )
        except (KeyError, TypeError, ValueError):
            pass
        raise SourceBatchRejected(
            "binding_malformed",
            stage=stage if stage == SOURCE_BYTES_STAGE else SOURCE_BYTES_STAGE,
            partition_root=(
                partition_root
                if partition_root is not None and _valid_root(partition_root)
                else None
            ),
        )


class CacheAdmissionRegistry:
    """Exact-match admission registry; an empty registry denies everything."""

    def __init__(self) -> None:
        self._admitted: set[tuple[str, str, tuple[str, ...]]] = set()

    def admit(
        self,
        *,
        stage: str,
        implementation_identity_root: str,
        config_projection_keys: tuple[str, ...] | list[str],
    ) -> None:
        if stage != SOURCE_BYTES_STAGE:
            raise SourceBatchRejected(
                "stage_not_admissible_in_source_slice",
                stage=stage,
            )
        if config_projection_keys:
            raise SourceBatchRejected(
                "source_bytes_config_projection_must_be_empty",
                stage=stage,
            )
        if implementation_identity_root != implementation_root():
            raise SourceBatchRejected(
                "implementation_identity_stale",
                stage=stage,
            )
        self._admitted.add(
            (
                stage,
                implementation_identity_root,
                tuple(sorted(config_projection_keys)),
            )
        )

    def allows(self, binding: SourceBatchBinding) -> bool:
        if (
            binding.config_projection_keys
            or binding.config_projection_root != _empty_config_projection_root()
        ):
            return False
        return (
            binding.stage,
            binding.implementation_root,
            tuple(sorted(binding.config_projection_keys)),
        ) in self._admitted


@dataclass(frozen=True)
class SealedSourceBatch:
    batch_root: str
    payload_root: str
    byte_count: int
    record_count: int
    cache_hit: bool


class VerifiedSourceBatchLease:
    """Opaque cache-issued capability for one verified immutable source batch."""

    __slots__ = ("__weakref__",)

    def __new__(cls, *args: Any, **kwargs: Any) -> "VerifiedSourceBatchLease":
        del cls, args, kwargs
        raise TypeError("verified_source_batch_lease_must_be_cache_issued")

    def __copy__(self) -> "VerifiedSourceBatchLease":
        raise TypeError("verified_source_batch_lease_cannot_be_copied")

    def __deepcopy__(self, memo: Any) -> "VerifiedSourceBatchLease":
        del memo
        raise TypeError("verified_source_batch_lease_cannot_be_copied")

    def __reduce_ex__(self, protocol: int) -> Any:
        del protocol
        raise TypeError("verified_source_batch_lease_cannot_be_reconstructed")

    def __reduce__(self) -> Any:
        raise TypeError("verified_source_batch_lease_cannot_be_reconstructed")

    @contextmanager
    def _open_text(
        self,
        *,
        source_path: Path,
        symbol: str,
        partition_identity: Mapping[str, Any] | None,
        _lease_resolver: Any,
    ) -> Iterator[io.TextIOWrapper]:
        record = _lease_resolver(self)
        binding = record.binding
        if implementation_root() != binding.implementation_root:
            raise SourceBatchRejected(
                "implementation_identity_stale",
                partition_root=binding.partition_root,
            )
        if _source_path_root(source_path) != binding.source_path_root:
            raise SourceBatchRejected(
                "source_path_identity_mismatch",
                partition_root=binding.partition_root,
            )
        if symbol != binding.partition_symbol:
            raise SourceBatchRejected(
                "partition_symbol_mismatch",
                partition_root=binding.partition_root,
            )
        partition_root: str | None = None
        try:
            partition_root = _root({"partition_identity": partition_identity})
        except ConfigReadRejected:
            pass
        if partition_root is None:
            partition_identity = None
            raise SourceBatchRejected(
                "partition_identity_mismatch",
                partition_root=binding.partition_root,
            )
        if partition_root != binding.partition_root:
            raise SourceBatchRejected(
                "partition_identity_mismatch",
                partition_root=binding.partition_root,
            )
        cache = _admitted_source_cache(record.cache_root)
        _manifest, payload = cache._read_verified_snapshot(
            record.batch_root,
            expected_binding=binding,
        )
        handle = io.TextIOWrapper(
            io.BytesIO(payload),
            encoding="utf-8",
            newline="",
        )
        try:
            yield handle
        finally:
            handle.close()


@dataclass(frozen=True)
class _VerifiedSourceBatchLeaseRecord:
    batch_root: str
    binding: SourceBatchBinding
    cache_root: Path
    integrity_root: str


def _build_verified_source_batch_lease_authority():
    authority_key = secrets.token_bytes(32)
    issued: weakref.WeakKeyDictionary[
        VerifiedSourceBatchLease,
        _VerifiedSourceBatchLeaseRecord,
    ] = weakref.WeakKeyDictionary()

    def integrity_root(
        *,
        batch_root: str,
        binding: SourceBatchBinding,
        cache_root: Path,
    ) -> str:
        material = _canonical_bytes(
            {
                "batch_root": batch_root,
                "binding": binding.as_dict(),
                "cache_root": os.path.abspath(os.fspath(cache_root)),
            }
        )
        return hmac.new(authority_key, material, hashlib.sha256).hexdigest()

    def issue(
        *,
        batch_root: str,
        binding: SourceBatchBinding,
        cache_root: Path,
    ) -> VerifiedSourceBatchLease:
        lease = object.__new__(VerifiedSourceBatchLease)
        normalized_root = Path(cache_root)
        issued[lease] = _VerifiedSourceBatchLeaseRecord(
            batch_root=batch_root,
            binding=binding,
            cache_root=normalized_root,
            integrity_root=integrity_root(
                batch_root=batch_root,
                binding=binding,
                cache_root=normalized_root,
            ),
        )
        return lease

    def resolve(
        lease: VerifiedSourceBatchLease,
    ) -> _VerifiedSourceBatchLeaseRecord:
        record = issued.get(lease)
        if record is None or not hmac.compare_digest(
            record.integrity_root,
            integrity_root(
                batch_root=record.batch_root,
                binding=record.binding,
                cache_root=record.cache_root,
            ),
        ):
            raise SourceBatchRejected("source_batch_lease_not_issued")
        return record

    return issue, resolve


(
    _issue_verified_source_batch_lease,
    _resolve_verified_source_batch_lease,
) = _build_verified_source_batch_lease_authority()
del _build_verified_source_batch_lease_authority


def _bind_verified_source_batch_lease_resolver(resolve):
    method = VerifiedSourceBatchLease._open_text

    def bound_open_text(
        self,
        *,
        source_path: Path,
        symbol: str,
        partition_identity: Mapping[str, Any] | None,
    ):
        return method(
            self,
            source_path=source_path,
            symbol=symbol,
            partition_identity=partition_identity,
            _lease_resolver=resolve,
        )

    bound_open_text.__name__ = method.__name__
    bound_open_text.__qualname__ = method.__qualname__
    bound_open_text.__doc__ = method.__doc__
    return bound_open_text


VerifiedSourceBatchLease._open_text = (  # type: ignore[method-assign]
    _bind_verified_source_batch_lease_resolver(
        _resolve_verified_source_batch_lease
    )
)
del _resolve_verified_source_batch_lease
del _bind_verified_source_batch_lease_resolver


def _bind_verified_source_batch_lease_issuer(issue):
    def decorate(method):
        def bound_acquire_lease(
            self,
            batch_root: str,
            *,
            expected_binding: SourceBatchBinding,
        ) -> VerifiedSourceBatchLease:
            return method(
                self,
                batch_root,
                expected_binding=expected_binding,
                _lease_issuer=issue,
            )

        bound_acquire_lease.__name__ = method.__name__
        bound_acquire_lease.__qualname__ = method.__qualname__
        bound_acquire_lease.__doc__ = method.__doc__
        return bound_acquire_lease

    return decorate


class ImmutableSourceBatchCache:
    """Seal and verify immutable, content-addressed source byte batches."""

    def __init__(self, root: Path, *, registry: CacheAdmissionRegistry | None = None) -> None:
        self.root = Path(root)
        self.registry = registry or CacheAdmissionRegistry()

    def batch_path(self, batch_root: str) -> Path:
        if not _valid_root(batch_root):
            raise SourceBatchRejected("invalid_batch_root")
        return self.root / batch_root

    def payload_path(self, batch_root: str) -> Path:
        return self.batch_path(batch_root) / "payload.bin"

    def seal_source_file(
        self,
        source_path: Path,
        *,
        binding: SourceBatchBinding,
    ) -> SealedSourceBatch:
        if _source_path_root(source_path) != binding.source_path_root:
            raise SourceBatchRejected(
                "source_path_identity_mismatch",
                partition_root=binding.partition_root,
            )
        absolute_source = Path(os.path.abspath(os.fspath(source_path)))
        components = absolute_source.parts[1:]
        if not components:
            raise SourceBatchRejected(
                "source_file_not_regular",
                partition_root=binding.partition_root,
            )
        current = os.open(os.sep, self._directory_open_flags())
        source_descriptor: int | None = None
        try:
            for component in components[:-1]:
                child: int | None = None
                try:
                    child = os.open(
                        component,
                        self._directory_open_flags(),
                        dir_fd=current,
                    )
                except OSError:
                    pass
                if child is None:
                    mode = self._entry_mode(current, component)
                    code = (
                        "source_path_symlink_forbidden"
                        if mode is not None and stat.S_ISLNK(mode)
                        else "source_path_not_directory"
                        if mode is not None
                        else "source_path_missing"
                    )
                    raise SourceBatchRejected(
                        code,
                        partition_root=binding.partition_root,
                    )
                os.close(current)
                current = child
            source_name = components[-1]
            try:
                source_descriptor = os.open(
                    source_name,
                    os.O_RDONLY
                    | getattr(os, "O_NOFOLLOW", 0)
                    | getattr(os, "O_NONBLOCK", 0),
                    dir_fd=current,
                )
            except OSError:
                pass
            if source_descriptor is None:
                mode = self._entry_mode(current, source_name)
                code = (
                    "source_path_symlink_forbidden"
                    if mode is not None and stat.S_ISLNK(mode)
                    else "source_file_not_regular"
                    if mode is not None
                    else "source_path_missing"
                )
                raise SourceBatchRejected(
                    code,
                    partition_root=binding.partition_root,
                )
            before = os.fstat(source_descriptor)
            if not stat.S_ISREG(before.st_mode):
                raise SourceBatchRejected(
                    "source_file_not_regular",
                    partition_root=binding.partition_root,
                )
            payload = self._read_descriptor(source_descriptor)
            after = os.fstat(source_descriptor)
            identity_before = (
                before.st_dev,
                before.st_ino,
                before.st_size,
                before.st_mtime_ns,
                before.st_ctime_ns,
            )
            identity_after = (
                after.st_dev,
                after.st_ino,
                after.st_size,
                after.st_mtime_ns,
                after.st_ctime_ns,
            )
            if identity_after != identity_before or len(payload) != after.st_size:
                raise SourceBatchRejected(
                    "source_file_changed_during_read",
                    partition_root=binding.partition_root,
                )
        finally:
            if source_descriptor is not None:
                os.close(source_descriptor)
            os.close(current)
        return self.seal(payload, binding=binding)

    @_bind_verified_source_batch_lease_issuer(
        _issue_verified_source_batch_lease
    )
    def acquire_lease(
        self,
        batch_root: str,
        *,
        expected_binding: SourceBatchBinding,
        _lease_issuer: Any,
    ) -> VerifiedSourceBatchLease:
        self._read_verified_snapshot(
            batch_root,
            expected_binding=expected_binding,
        )
        return _lease_issuer(
            batch_root=batch_root,
            binding=expected_binding,
            cache_root=self.root,
        )

    @staticmethod
    def _directory_open_flags() -> int:
        return (
            os.O_RDONLY
            | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_NOFOLLOW", 0)
        )

    @staticmethod
    def _entry_mode(parent_descriptor: int, name: str) -> int | None:
        try:
            return os.stat(
                name,
                dir_fd=parent_descriptor,
                follow_symlinks=False,
            ).st_mode
        except OSError:
            return None

    def _open_cache_root_component_at(
        self,
        parent_descriptor: int,
        component: str,
        *,
        expected_binding: SourceBatchBinding,
        create: bool,
    ) -> int:
        failure_code: str | None = None
        for _attempt in range(_CACHE_ROOT_CREATE_RETRIES):
            child: int | None = None
            missing = False
            open_failed = False
            try:
                child = os.open(
                    component,
                    self._directory_open_flags(),
                    dir_fd=parent_descriptor,
                )
            except FileNotFoundError:
                missing = True
            except OSError:
                open_failed = True
            if child is not None:
                return child
            if open_failed:
                mode = self._entry_mode(parent_descriptor, component)
                failure_code = (
                    "cache_root_symlink_forbidden"
                    if mode is not None and stat.S_ISLNK(mode)
                    else "cache_root_not_directory"
                    if mode is not None
                    else "cache_root_unreadable"
                )
                break
            if not missing:
                failure_code = "cache_root_unreadable"
                break
            if not create:
                failure_code = "cache_root_missing"
                break

            created = False
            competing_entry = False
            create_failed = False
            try:
                os.mkdir(component, 0o755, dir_fd=parent_descriptor)
                created = True
            except FileExistsError:
                competing_entry = True
            except OSError:
                create_failed = True
            if create_failed:
                mode = self._entry_mode(parent_descriptor, component)
                failure_code = (
                    "cache_root_symlink_forbidden"
                    if mode is not None and stat.S_ISLNK(mode)
                    else "cache_root_not_directory"
                    if mode is not None
                    else "cache_root_create_failed"
                )
                break
            if competing_entry:
                continue
            if created:
                sync_failed = False
                try:
                    os.fsync(parent_descriptor)
                except OSError:
                    sync_failed = True
                if sync_failed:
                    failure_code = "cache_root_parent_sync_failed"
                    break
                continue

        if failure_code is None:
            failure_code = "cache_root_create_race_exhausted"
        raise SourceBatchRejected(
            failure_code,
            partition_root=expected_binding.partition_root,
        )

    @contextmanager
    def _held_cache_root(
        self,
        *,
        expected_binding: SourceBatchBinding,
        create: bool,
    ) -> Iterator[int]:
        absolute_root = Path(os.path.abspath(os.fspath(self.root)))
        components = absolute_root.parts[1:]
        if not components:
            raise SourceBatchRejected(
                "cache_root_not_directory",
                partition_root=expected_binding.partition_root,
            )
        current = os.open(os.sep, self._directory_open_flags())
        try:
            for component in components:
                child = self._open_cache_root_component_at(
                    current,
                    component,
                    expected_binding=expected_binding,
                    create=create,
                )
                os.close(current)
                current = child
            if not stat.S_ISDIR(os.fstat(current).st_mode):
                raise SourceBatchRejected(
                    "cache_root_not_directory",
                    partition_root=expected_binding.partition_root,
                )
            yield current
        finally:
            os.close(current)

    def _open_batch_directory_at(
        self,
        root_descriptor: int,
        batch_root: str,
        *,
        expected_binding: SourceBatchBinding,
        missing_ok: bool = False,
    ) -> int | None:
        if not _valid_root(batch_root):
            raise SourceBatchRejected(
                "invalid_batch_root",
                partition_root=expected_binding.partition_root,
            )
        descriptor: int | None = None
        missing = False
        open_failed = False
        try:
            descriptor = os.open(
                batch_root,
                self._directory_open_flags(),
                dir_fd=root_descriptor,
            )
        except FileNotFoundError:
            missing = True
        except OSError:
            open_failed = True
        if missing:
            if missing_ok:
                return None
            raise SourceBatchRejected(
                "batch_directory_missing",
                partition_root=expected_binding.partition_root,
            )
        if open_failed or descriptor is None:
            mode = self._entry_mode(root_descriptor, batch_root)
            code = (
                "batch_directory_symlink_forbidden"
                if mode is not None and stat.S_ISLNK(mode)
                else "batch_path_not_directory"
                if mode is not None
                else "batch_directory_missing"
            )
            raise SourceBatchRejected(
                code,
                partition_root=expected_binding.partition_root,
            )
        mode = os.fstat(descriptor).st_mode
        if mode & 0o222:
            os.close(descriptor)
            raise SourceBatchRejected(
                "sealed_permissions_mutable",
                partition_root=expected_binding.partition_root,
            )
        entries: set[str] | None = None
        try:
            entries = set(os.listdir(descriptor))
        except OSError:
            pass
        if entries is None:
            os.close(descriptor)
            raise SourceBatchRejected(
                "batch_directory_unreadable",
                partition_root=expected_binding.partition_root,
            )
        if entries != {"manifest.json", "payload.bin"}:
            os.close(descriptor)
            raise SourceBatchRejected(
                "batch_directory_schema_mismatch",
                partition_root=expected_binding.partition_root,
            )
        return descriptor

    @staticmethod
    def _open_sealed_file_at(
        batch_descriptor: int,
        name: str,
        *,
        expected_binding: SourceBatchBinding,
    ) -> int:
        stat_failed = False
        try:
            expected_stat = os.stat(
                name,
                dir_fd=batch_descriptor,
                follow_symlinks=False,
            )
        except OSError:
            stat_failed = True
        if stat_failed:
            raise SourceBatchRejected(
                "sealed_file_unreadable",
                partition_root=expected_binding.partition_root,
            )

        descriptor: int | None = None
        open_failed = False
        try:
            descriptor = os.open(
                name,
                os.O_RDONLY
                | getattr(os, "O_NOFOLLOW", 0)
                | getattr(os, "O_NONBLOCK", 0),
                dir_fd=batch_descriptor,
            )
            file_stat = os.fstat(descriptor)
        except OSError:
            open_failed = True
        if open_failed or descriptor is None:
            if descriptor is not None:
                os.close(descriptor)
            raise SourceBatchRejected(
                "sealed_file_unreadable",
                partition_root=expected_binding.partition_root,
            )
        if (file_stat.st_dev, file_stat.st_ino) != (
            expected_stat.st_dev,
            expected_stat.st_ino,
        ):
            os.close(descriptor)
            raise SourceBatchRejected(
                "sealed_file_identity_changed",
                partition_root=expected_binding.partition_root,
            )
        if not stat.S_ISREG(file_stat.st_mode):
            os.close(descriptor)
            raise SourceBatchRejected(
                "sealed_file_not_regular",
                partition_root=expected_binding.partition_root,
            )
        if file_stat.st_mode & 0o222:
            os.close(descriptor)
            raise SourceBatchRejected(
                "sealed_permissions_mutable",
                partition_root=expected_binding.partition_root,
            )
        return descriptor

    @staticmethod
    def _read_descriptor(descriptor: int) -> bytes:
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                return b"".join(chunks)
            chunks.append(chunk)

    @staticmethod
    def _write_descriptor(descriptor: int, value: bytes) -> None:
        view = memoryview(value)
        offset = 0
        while offset < len(view):
            written = os.write(descriptor, view[offset:])
            if written <= 0:
                raise OSError("sealed_file_write_failed")
            offset += written

    def _write_sealed_file_at(
        self,
        batch_descriptor: int,
        name: str,
        value: bytes,
    ) -> None:
        descriptor = os.open(
            name,
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_NOFOLLOW", 0),
            0o600,
            dir_fd=batch_descriptor,
        )
        try:
            self._write_descriptor(descriptor, value)
            os.fsync(descriptor)
            os.fchmod(descriptor, 0o444)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

    @staticmethod
    def _cleanup_temporary_batch(
        root_descriptor: int,
        temporary_name: str,
        temporary_descriptor: int | None,
    ) -> None:
        descriptor = temporary_descriptor
        if descriptor is None:
            try:
                descriptor = os.open(
                    temporary_name,
                    ImmutableSourceBatchCache._directory_open_flags(),
                    dir_fd=root_descriptor,
                )
            except OSError:
                return
        try:
            os.fchmod(descriptor, 0o700)
            for name in os.listdir(descriptor):
                os.unlink(name, dir_fd=descriptor)
        finally:
            os.close(descriptor)
        try:
            os.rmdir(temporary_name, dir_fd=root_descriptor)
        except FileNotFoundError:
            pass

    def seal(
        self,
        payload: bytes,
        *,
        binding: SourceBatchBinding,
    ) -> SealedSourceBatch:
        if type(payload) is not bytes:
            raise SourceBatchRejected(
                "mutable_payload_rejected",
                stage=binding.stage,
                partition_root=binding.partition_root,
            )
        if not self.registry.allows(binding):
            raise SourceBatchRejected(
                "cache_stage_not_admitted",
                stage=binding.stage,
                partition_root=binding.partition_root,
            )
        payload_root = _bytes_root(payload)
        manifest = {
            "schema": MANIFEST_SCHEMA,
            **binding.as_dict(),
            "payload_root": payload_root,
            "byte_count": len(payload),
            "record_count": _record_count(payload),
        }
        manifest_bytes = _canonical_bytes(manifest) + b"\n"
        batch_root = _bytes_root(manifest_bytes)
        with self._held_cache_root(
            expected_binding=binding,
            create=True,
        ) as root_descriptor:
            try:
                verified, _snapshot = self._read_verified_batch_at(
                    root_descriptor,
                    batch_root,
                    expected_binding=binding,
                )
            except SourceBatchRejected as exc:
                if exc.code != "batch_directory_missing":
                    raise
            else:
                return SealedSourceBatch(
                    batch_root=batch_root,
                    payload_root=str(verified["payload_root"]),
                    byte_count=int(verified["byte_count"]),
                    record_count=int(verified["record_count"]),
                    cache_hit=True,
                )

            temporary_name: str | None = None
            temporary_descriptor: int | None = None
            try:
                for _attempt in range(32):
                    candidate = f".source-batch-{secrets.token_hex(12)}"
                    try:
                        os.mkdir(candidate, 0o700, dir_fd=root_descriptor)
                    except FileExistsError:
                        continue
                    temporary_name = candidate
                    break
                if temporary_name is None:
                    raise SourceBatchRejected(
                        "temporary_batch_name_exhausted",
                        partition_root=binding.partition_root,
                    )
                temporary_descriptor = os.open(
                    temporary_name,
                    self._directory_open_flags(),
                    dir_fd=root_descriptor,
                )
                self._write_sealed_file_at(
                    temporary_descriptor,
                    "payload.bin",
                    payload,
                )
                self._write_sealed_file_at(
                    temporary_descriptor,
                    "manifest.json",
                    manifest_bytes,
                )
                os.fchmod(temporary_descriptor, 0o555)
                os.fsync(temporary_descriptor)
                try:
                    os.rename(
                        temporary_name,
                        batch_root,
                        src_dir_fd=root_descriptor,
                        dst_dir_fd=root_descriptor,
                    )
                except OSError:
                    self._cleanup_temporary_batch(
                        root_descriptor,
                        temporary_name,
                        temporary_descriptor,
                    )
                    temporary_name = None
                    temporary_descriptor = None
                    verified, _snapshot = self._read_verified_batch_at(
                        root_descriptor,
                        batch_root,
                        expected_binding=binding,
                    )
                    return SealedSourceBatch(
                        batch_root=batch_root,
                        payload_root=str(verified["payload_root"]),
                        byte_count=int(verified["byte_count"]),
                        record_count=int(verified["record_count"]),
                        cache_hit=True,
                    )
                os.close(temporary_descriptor)
                temporary_descriptor = None
                temporary_name = None
                os.fsync(root_descriptor)
                self._read_verified_batch_at(
                    root_descriptor,
                    batch_root,
                    expected_binding=binding,
                )
            finally:
                if temporary_name is not None:
                    self._cleanup_temporary_batch(
                        root_descriptor,
                        temporary_name,
                        temporary_descriptor,
                    )
            return SealedSourceBatch(
                batch_root=batch_root,
                payload_root=payload_root,
                byte_count=len(payload),
                record_count=_record_count(payload),
                cache_hit=False,
            )

    def _verify_batch(
        self,
        batch_root: str,
        *,
        expected_binding: SourceBatchBinding,
    ) -> dict[str, Any]:
        manifest, _snapshot = self._read_verified_snapshot(
            batch_root,
            expected_binding=expected_binding,
        )
        return manifest

    def _require_current_read_admission(
        self,
        expected_binding: SourceBatchBinding,
    ) -> None:
        if expected_binding.implementation_root != implementation_root():
            raise SourceBatchRejected(
                "implementation_identity_stale",
                partition_root=expected_binding.partition_root,
            )
        if not self.registry.allows(expected_binding):
            raise SourceBatchRejected(
                "cache_stage_not_admitted",
                partition_root=expected_binding.partition_root,
            )

    def _read_verified_batch_at(
        self,
        root_descriptor: int,
        batch_root: str,
        *,
        expected_binding: SourceBatchBinding,
    ) -> tuple[dict[str, Any], bytes]:
        self._require_current_read_admission(expected_binding)
        batch_descriptor = self._open_batch_directory_at(
            root_descriptor,
            batch_root,
            expected_binding=expected_binding,
        )
        if batch_descriptor is None:
            raise SourceBatchRejected(
                "batch_directory_missing",
                partition_root=expected_binding.partition_root,
            )
        try:
            manifest_descriptor = self._open_sealed_file_at(
                batch_descriptor,
                "manifest.json",
                expected_binding=expected_binding,
            )
            try:
                manifest_bytes = self._read_descriptor(manifest_descriptor)
            finally:
                os.close(manifest_descriptor)
            payload_descriptor = self._open_sealed_file_at(
                batch_descriptor,
                "payload.bin",
                expected_binding=expected_binding,
            )
            try:
                payload_snapshot = self._read_descriptor(payload_descriptor)
            finally:
                os.close(payload_descriptor)
        finally:
            os.close(batch_descriptor)
        manifest: Any = None
        manifest_parse_failed = False
        try:
            manifest = json.loads(manifest_bytes)
        except (ValueError, TypeError):
            manifest_parse_failed = True
        if manifest_parse_failed:
            manifest = None
            manifest_bytes = b""
            raise SourceBatchRejected(
                "manifest_unreadable",
                partition_root=expected_binding.partition_root,
            )
        if not isinstance(manifest, dict):
            raise SourceBatchRejected(
                "manifest_schema_mismatch",
                partition_root=expected_binding.partition_root,
            )
        if set(manifest) != _MANIFEST_FIELDS:
            raise SourceBatchRejected(
                "manifest_schema_mismatch",
                partition_root=expected_binding.partition_root,
            )
        if manifest.get("schema") != MANIFEST_SCHEMA or _bytes_root(manifest_bytes) != batch_root:
            raise SourceBatchRejected(
                "manifest_identity_mismatch",
                partition_root=expected_binding.partition_root,
            )
        canonical_manifest_bytes: bytes | None = None
        try:
            canonical_manifest_bytes = _canonical_bytes(manifest) + b"\n"
        except ConfigReadRejected:
            pass
        if canonical_manifest_bytes is None:
            manifest = None
            manifest_bytes = b""
            raise SourceBatchRejected(
                "manifest_not_canonical",
                partition_root=expected_binding.partition_root,
            )
        if manifest_bytes != canonical_manifest_bytes:
            raise SourceBatchRejected(
                "manifest_not_canonical",
                partition_root=expected_binding.partition_root,
            )
        raw_projection_keys = manifest.get("config_projection_keys")
        if (
            type(raw_projection_keys) is not list
            or raw_projection_keys
            or manifest.get("config_projection_root")
            != _empty_config_projection_root()
            or type(manifest.get("byte_count")) is not int
            or int(manifest["byte_count"]) < 0
            or type(manifest.get("record_count")) is not int
            or int(manifest["record_count"]) < 0
        ):
            raise SourceBatchRejected(
                "manifest_schema_mismatch",
                partition_root=expected_binding.partition_root,
            )
        identity_fields = (
            ("stage", "stage_identity_mismatch"),
            ("implementation_root", "implementation_identity_mismatch"),
            ("source_identity_root", "source_identity_mismatch"),
            ("source_path_root", "source_path_identity_mismatch"),
            ("partition_root", "partition_identity_mismatch"),
            ("partition_symbol", "partition_symbol_mismatch"),
            ("config_projection_root", "config_projection_mismatch"),
        )
        expected = expected_binding.as_dict()
        for field, code in identity_fields:
            if manifest.get(field) != expected[field]:
                raise SourceBatchRejected(
                    code,
                    partition_root=expected_binding.partition_root,
                )
        if tuple(manifest.get("config_projection_keys") or ()) != tuple(
            expected_binding.config_projection_keys
        ):
            raise SourceBatchRejected(
                "config_projection_mismatch",
                partition_root=expected_binding.partition_root,
            )
        if (
            _bytes_root(payload_snapshot) != manifest.get("payload_root")
            or len(payload_snapshot) != manifest.get("byte_count")
        ):
            raise SourceBatchRejected(
                "post_seal_payload_mutation",
                partition_root=expected_binding.partition_root,
            )
        actual_record_count = _record_count(payload_snapshot)
        if (
            type(manifest.get("record_count")) is not int
            or manifest.get("record_count") != actual_record_count
        ):
            raise SourceBatchRejected(
                "manifest_record_count_mismatch",
                partition_root=expected_binding.partition_root,
            )
        return manifest, payload_snapshot

    def _read_verified_snapshot(
        self,
        batch_root: str,
        *,
        expected_binding: SourceBatchBinding,
    ) -> tuple[dict[str, Any], bytes]:
        self._require_current_read_admission(expected_binding)
        with self._held_cache_root(
            expected_binding=expected_binding,
            create=False,
        ) as root_descriptor:
            return self._read_verified_batch_at(
                root_descriptor,
                batch_root,
                expected_binding=expected_binding,
            )


del _issue_verified_source_batch_lease
del _bind_verified_source_batch_lease_issuer


def _admitted_source_cache(cache_root: Path) -> ImmutableSourceBatchCache:
    registry = CacheAdmissionRegistry()
    registry.admit(
        stage=SOURCE_BYTES_STAGE,
        implementation_identity_root=implementation_root(),
        config_projection_keys=(),
    )
    return ImmutableSourceBatchCache(cache_root, registry=registry)


def _structural_process_receipt(
    *,
    manifest: Mapping[str, Any],
    batch_root: str,
    arm_id: str,
) -> dict[str, Any]:
    if arm_id not in FACTORIAL_ARMS:
        raise SourceBatchRejected(
            "arm_execution_order_invalid",
            partition_root=str(manifest.get("partition_root") or ""),
        )
    roots = {
        "batch": batch_root,
        "payload": manifest["payload_root"],
        "implementation": manifest["implementation_root"],
        "source_identity": manifest["source_identity_root"],
        "source_path": manifest["source_path_root"],
        "config_projection": manifest["config_projection_root"],
        "partition": manifest["partition_root"],
    }
    counts = {
        "bytes": manifest["byte_count"],
        "records": manifest["record_count"],
    }
    return {
        "arm": {
            "id": arm_id,
            "attestation_root": _root(
                {
                    "schema": "gtos.replay_acceleration.arm_source_receipt.v1",
                    "arm": arm_id,
                    "roots": roots,
                    "counts": counts,
                }
            ),
        },
        "roots": roots,
        "counts": counts,
    }


def _fresh_process_receipt(
    *,
    cache_root: Path,
    batch_root: str,
    expected_binding: SourceBatchBinding,
    arm_id: str,
) -> dict[str, Any]:
    cache = _admitted_source_cache(cache_root)
    manifest, source_bytes = cache._read_verified_snapshot(
        batch_root,
        expected_binding=expected_binding,
    )
    if type(source_bytes) is not bytes:
        raise SourceBatchRejected(
            "fresh_process_payload_not_read_only",
            partition_root=expected_binding.partition_root,
        )
    return _structural_process_receipt(
        manifest=manifest,
        batch_root=batch_root,
        arm_id=arm_id,
    )


def consume_in_fresh_processes(
    *,
    cache_root: Path,
    batch_root: str,
    expected_binding: SourceBatchBinding,
    arm_execution_order: tuple[str, ...] | list[str],
) -> dict[str, Any]:
    order = tuple(str(arm) for arm in arm_execution_order)
    if len(order) != len(FACTORIAL_ARMS) or set(order) != FACTORIAL_ARMS:
        raise SourceBatchRejected(
            "complete_arm_set_required",
            stage=expected_binding.stage,
            partition_root=expected_binding.partition_root,
        )
    cache = _admitted_source_cache(Path(cache_root))
    parent_manifest, _source_bytes = cache._read_verified_snapshot(
        batch_root,
        expected_binding=expected_binding,
    )
    receipts: dict[str, dict[str, Any]] = {}
    binding_json = json.dumps(expected_binding.as_dict(), separators=(",", ":"))
    for arm_id in order:
        expected_receipt = _structural_process_receipt(
            manifest=parent_manifest,
            batch_root=batch_root,
            arm_id=arm_id,
        )
        completed: subprocess.CompletedProcess[str] | None = None
        try:
            completed = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    "_consume",
                    str(cache_root),
                    batch_root,
                    binding_json,
                    arm_id,
                ],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired):
            pass
        if completed is None:
            raise SourceBatchRejected(
                "fresh_process_consumption_failed",
                stage=expected_binding.stage,
                partition_root=expected_binding.partition_root,
            )
        if completed.returncode != 0:
            completed = None
            raise SourceBatchRejected(
                "fresh_process_consumption_failed",
                stage=expected_binding.stage,
                partition_root=expected_binding.partition_root,
            )
        receipt: Any = None
        parse_failed = False
        try:
            receipt = json.loads(completed.stdout)
        except (json.JSONDecodeError, TypeError):
            parse_failed = True
        if parse_failed:
            completed = None
            receipt = None
            raise SourceBatchRejected(
                "fresh_process_consumption_failed",
                stage=expected_binding.stage,
                partition_root=expected_binding.partition_root,
            )
        if type(receipt) is not dict or receipt != expected_receipt:
            completed = None
            receipt = None
            raise SourceBatchRejected(
                "fresh_process_consumption_failed",
                partition_root=expected_binding.partition_root,
            )
        completed = None
        receipts[arm_id] = receipt
    first_receipt = receipts[sorted(receipts)[0]]
    roots = dict(first_receipt["roots"])
    roots["arm_attestations"] = {
        arm_id: receipts[arm_id]["arm"]["attestation_root"]
        for arm_id in sorted(receipts)
    }
    return {
        "equality": True,
        "roots": roots,
        "counts": {
            **first_receipt["counts"],
            "processes": len(receipts),
        },
        "failures": [],
    }


def measure_tiny_fixture_cold_warm(
    *,
    cache: ImmutableSourceBatchCache,
    payload: bytes,
    binding: SourceBatchBinding,
) -> dict[str, Any]:
    cold_start = time.perf_counter()
    cold = cache.seal(payload, binding=binding)
    _cold_manifest, cold_source_bytes = cache._read_verified_snapshot(
        cold.batch_root,
        expected_binding=binding,
    )
    _bytes_root(cold_source_bytes)
    cold_seconds = time.perf_counter() - cold_start

    warm_start = time.perf_counter()
    warm = cache.seal(payload, binding=binding)
    _warm_manifest, warm_source_bytes = cache._read_verified_snapshot(
        warm.batch_root,
        expected_binding=binding,
    )
    _bytes_root(warm_source_bytes)
    warm_seconds = time.perf_counter() - warm_start
    return {
        "label": "tiny_fixture_microbenchmark_not_replay_speed_claim",
        "cache_hits": {"cold": cold.cache_hit, "warm": warm.cache_hit},
        "roots": {"batch": warm.batch_root, "payload": warm.payload_root},
        "counts": {"bytes": warm.byte_count, "records": warm.record_count},
        "timings_seconds": {
            "cold": round(cold_seconds, 9),
            "warm": round(warm_seconds, 9),
        },
    }


def _main(argv: list[str]) -> int:
    if len(argv) != 5 or argv[0] != "_consume":
        rejected = SourceBatchRejected("binding_malformed")
        print(json.dumps(rejected.structural_output(), sort_keys=True))
        return 2
    try:
        raw_binding = json.loads(argv[3])
        if not isinstance(raw_binding, Mapping):
            raise SourceBatchRejected("binding_malformed")
        receipt = _fresh_process_receipt(
            cache_root=Path(argv[1]),
            batch_root=argv[2],
            expected_binding=SourceBatchBinding.from_dict(raw_binding),
            arm_id=argv[4],
        )
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        rejected = SourceBatchRejected("binding_malformed")
        print(json.dumps(rejected.structural_output(), sort_keys=True))
        return 2
    except SourceBatchRejected as exc:
        print(json.dumps(exc.structural_output(), sort_keys=True))
        return 2
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
