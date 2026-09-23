"""Single-materialisation columnar source layer.

Why this exists
---------------
The typed source cache is *already* columnar on disk: `rows.bin` is a header plus
a packed array of ``<qddddd`` records — an int64 microsecond timestamp and five
float64s, **48 bytes per row** (`replay_acceleration_integrated_source.py:45`).

The current loader throws that away. `TypedNormalizedPartitionCache._load_entry`
(`:432-450`) unpacks each record into a **Python dict** via `_row_from_values`
(`:144-157`), appends it to a list, and returns `tuple(rows)`. Measured on this
machine (Python 3.14.4, `tracemalloc`, 200k synthetic M1 bars) that costs
**474.3 bytes/row** — a 9.9x inflation over the bytes it was read from.

It is then duplicated. `rows_by_day`
(`v4_timewarp_simulated_live_research_loop.py:4851-4862`) and `select_days`
(`replay_acceleration_integrated_source.py:1082-1105`) both call ``dict(row)``,
so the ``grouped`` half of every ``(rows, grouped, sha)`` triple is an
*independent second copy*, not a view. And `load_or_build_partition` keeps no
in-memory memo, so each of the engine's three loader entry points
(`replay_acceleration_attempt5_typed_sparse_runner.py:8384-8482`) re-reads
`rows.bin` and builds a fresh set of dicts, retained under its own cache key.

This module materialises each partition **once**, as numpy columns, and serves
every read as a zero-copy view over those columns.

Identity
--------
Row identity is guaranteed *by construction*, not by re-implementation: the row
view decodes through the same `_row_from_values` / `_decode_timestamp` helpers
the sealed loader uses, and `ColumnarPartition.load` re-verifies the manifest
identity, the payload SHA-256, the framing, **and** the canonical `rows_root`
digest — the same four checks as `_load_entry`, in the same order, streaming so
that verification costs O(1) memory rather than O(rows).

Contract position
-----------------
This file is **new and unbound**. It is in neither the R1 nor the R2 decision
contract, and it is not reachable from `code_authority_paths`. It imports from
bound modules but modifies none of them, so the sealed path stays byte-identical
and the H1 membership check stays at its expected `drifted=1`.
"""

from __future__ import annotations

import hashlib
import json
import threading
from collections.abc import Iterable, Iterator, Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np

from src.research_infra.replay_acceleration_integrated_source import (
    _HEADER,
    _MAGIC,
    _ROW,
    IntegratedSourceRejected,
    TYPED_MANIFEST_SCHEMA,
    _canonical_bytes,
    _decode_timestamp,
    _manifest_root,
    _root,
)

__all__ = [
    "ColumnarPartition",
    "ColumnarPartitionStore",
    "ColumnarRow",
    "ColumnarRowSequence",
    "ROW_KEYS",
    "iso_for_micros",
]

# The exact key set and order `_row_from_values` builds. Order is cosmetic —
# every digest downstream canonicalises with ``sort_keys=True``
# (`replay_acceleration_integrated_source.py:76-86`) — but matching it keeps
# ``dict(row)`` byte-comparable with the sealed representation under repr too.
ROW_KEYS = ("time", "time_utc", "symbol", "open", "high", "low", "close", "volume")

_MANIFEST_FIELDS = frozenset(
    {
        "schema",
        "identity",
        "identity_root_sha256",
        "row_count",
        "payload_byte_count",
        "payload_sha256",
        "rows_root_sha256",
        "manifest_root_sha256",
    }
)

_MICROS_PER_DAY = 86_400_000_000

# ---------------------------------------------------------------------------
# Timestamp decoding
# ---------------------------------------------------------------------------
# `_decode_timestamp` is not cheap (timedelta construction + ISO formatting) and
# the same instant recurs across all 24 symbols at the same timeframe, so a
# shared memo pays for itself several times over. It is *bounded*: an unbounded
# memo over 3.5M distinct instants would reintroduce ~280 MB of exactly the
# string overhead this module exists to remove.
_ISO_MEMO_LIMIT = 200_000
_ISO_MEMO: dict[int, str] = {}


def iso_for_micros(micros: int) -> str:
    """Decode epoch microseconds exactly as the sealed loader does."""
    cached = _ISO_MEMO.get(micros)
    if cached is not None:
        return cached
    decoded = _decode_timestamp(micros)
    if len(_ISO_MEMO) < _ISO_MEMO_LIMIT:
        _ISO_MEMO[micros] = decoded
    return decoded


# ---------------------------------------------------------------------------
# Row view
# ---------------------------------------------------------------------------


class ColumnarRow(Mapping):
    """A zero-copy view of one row of a `ColumnarPartition`.

    Equal to — and canonically indistinguishable from — the dict
    `_row_from_values` builds for the same record. Holds two slots instead of a
    dict, and decodes floats and the timestamp only when they are read.
    """

    __slots__ = ("_partition", "_index")

    def __init__(self, partition: "ColumnarPartition", index: int) -> None:
        self._partition = partition
        self._index = index

    def __getitem__(self, key: str) -> Any:
        partition = self._partition
        index = self._index
        if key == "symbol":
            return partition.symbol
        if key in ("time", "time_utc"):
            return iso_for_micros(int(partition.micros[index]))
        column = partition.columns.get(key)
        if column is None:
            raise KeyError(key)
        # float() is exact: both sides are IEEE-754 binary64, and json.dumps
        # rejects np.float64 outright, so this conversion is required for the
        # canonical digest to be byte-identical.
        return float(column[index])

    def __iter__(self) -> Iterator[str]:
        return iter(ROW_KEYS)

    def __len__(self) -> int:
        return len(ROW_KEYS)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, ColumnarRow):
            return (
                other._partition is self._partition and other._index == self._index
            ) or dict(self) == dict(other)
        if isinstance(other, Mapping):
            return dict(self) == dict(other)
        return NotImplemented

    def __ne__(self, other: Any) -> bool:
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result

    def __hash__(self) -> int:  # dicts are unhashable; match that.
        raise TypeError("unhashable type: 'ColumnarRow'")

    def __repr__(self) -> str:
        return repr(dict(self))

    def as_dict(self) -> dict[str, Any]:
        """Materialise this row as the plain dict the sealed loader returns."""
        return {key: self[key] for key in ROW_KEYS}


# ---------------------------------------------------------------------------
# Row sequence
# ---------------------------------------------------------------------------


class ColumnarRowSequence(Sequence):
    """A lazy, contiguous window over a partition's columns.

    Substitutes for the ``tuple[dict, ...]`` the sealed loader returns. The
    engine's consumption of that tuple is iteration and ``len()``
    (`replay_acceleration_attempt5_typed_sparse_runner.py`, ~30 call sites), both
    of which are O(1) memory here. Slicing returns another view, never a copy.
    """

    __slots__ = ("_partition", "_start", "_stop")

    def __init__(self, partition: "ColumnarPartition", start: int, stop: int) -> None:
        self._partition = partition
        self._start = start
        self._stop = stop

    def __len__(self) -> int:
        return self._stop - self._start

    def __getitem__(self, index: Any) -> Any:
        if isinstance(index, slice):
            start, stop, step = index.indices(len(self))
            if step != 1:
                return tuple(
                    ColumnarRow(self._partition, self._start + position)
                    for position in range(start, stop, step)
                )
            return ColumnarRowSequence(
                self._partition, self._start + start, self._start + max(start, stop)
            )
        length = self._stop - self._start
        position = int(index)
        if position < 0:
            position += length
        if position < 0 or position >= length:
            raise IndexError("row index out of range")
        return ColumnarRow(self._partition, self._start + position)

    def __iter__(self) -> Iterator[ColumnarRow]:
        partition = self._partition
        for position in range(self._start, self._stop):
            yield ColumnarRow(partition, position)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, (ColumnarRowSequence, tuple, list)):
            if len(self) != len(other):
                return False
            return all(left == right for left, right in zip(self, other))
        return NotImplemented

    def __ne__(self, other: Any) -> bool:
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result

    def __repr__(self) -> str:
        return f"ColumnarRowSequence(rows={len(self)})"

    def as_tuple(self) -> tuple[dict[str, Any], ...]:
        """Materialise to the sealed representation. For tests and comparison."""
        return tuple(row.as_dict() for row in self)


_EMPTY_MICROS = np.empty(0, dtype="<i8")
_EMPTY_VALUES = np.empty(0, dtype="<f8")


# ---------------------------------------------------------------------------
# Partition
# ---------------------------------------------------------------------------


class ColumnarPartition:
    """One symbol/timeframe partition, held once as numpy columns.

    Storage is exactly the 48 bytes/row the file occupies on disk: one int64
    timestamp column and five float64 value columns, all views into a single
    decoded buffer.
    """

    __slots__ = (
        "symbol",
        "physical_timeframe",
        "micros",
        "columns",
        "row_count",
        "identity_root_sha256",
        "rows_root_sha256",
        "cache_entry_dir",
        "_day_labels",
        "_day_starts",
    )

    def __init__(
        self,
        *,
        symbol: str,
        physical_timeframe: str,
        micros: np.ndarray,
        columns: dict[str, np.ndarray],
        identity_root_sha256: str,
        rows_root_sha256: str,
        cache_entry_dir: Path,
    ) -> None:
        self.symbol = symbol
        self.physical_timeframe = physical_timeframe
        self.micros = micros
        self.columns = columns
        self.row_count = int(micros.shape[0])
        self.identity_root_sha256 = identity_root_sha256
        self.rows_root_sha256 = rows_root_sha256
        self.cache_entry_dir = cache_entry_dir
        self._day_labels: tuple[str, ...] | None = None
        self._day_starts: np.ndarray | None = None

    # -- construction -------------------------------------------------------

    @classmethod
    def load(
        cls,
        entry: Path,
        *,
        expected_identity: Mapping[str, Any] | None = None,
        verify_rows_root: bool = True,
    ) -> "ColumnarPartition":
        """Load a typed-cache entry into columns, with the sealed loader's checks.

        Mirrors `TypedNormalizedPartitionCache._load_entry`
        (`replay_acceleration_integrated_source.py:386-450`) check for check.
        `verify_rows_root` streams one transient row at a time, so the digest is
        re-derived at O(1) memory rather than O(rows).
        """
        entry = Path(entry)
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
        identity = manifest.get("identity")
        if type(identity) is not dict:
            raise IntegratedSourceRejected("typed_manifest_identity_mismatch")
        if expected_identity is not None and (
            identity != dict(expected_identity)
            or manifest.get("identity_root_sha256") != _root(expected_identity)
        ):
            raise IntegratedSourceRejected("typed_cache_identity_mismatch")
        if manifest.get("identity_root_sha256") != _root(identity):
            raise IntegratedSourceRejected("typed_cache_identity_mismatch")

        try:
            payload = payload_path.read_bytes()
        except OSError:
            raise IntegratedSourceRejected("typed_payload_missing") from None
        if (
            manifest.get("payload_byte_count") != len(payload)
            or manifest.get("payload_sha256") != hashlib.sha256(payload).hexdigest()
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

        symbol = str(identity["symbol"])
        record = np.dtype(
            [
                ("time", "<i8"),
                ("open", "<f8"),
                ("high", "<f8"),
                ("low", "<f8"),
                ("close", "<f8"),
                ("volume", "<f8"),
            ]
        )
        if record.itemsize != _ROW.size:
            raise IntegratedSourceRejected("typed_payload_framing_mismatch")
        if row_count:
            view = np.frombuffer(
                payload, dtype=record, offset=_HEADER.size, count=row_count
            )
            # One contiguous copy per column, then `payload` is released. This
            # is the single materialisation the module is named for.
            micros = np.ascontiguousarray(view["time"])
            columns = {
                name: np.ascontiguousarray(view[name])
                for name in ("open", "high", "low", "close", "volume")
            }
            del view
        else:
            micros = _EMPTY_MICROS
            columns = {
                name: _EMPTY_VALUES
                for name in ("open", "high", "low", "close", "volume")
            }
        del payload

        partition = cls(
            symbol=symbol,
            physical_timeframe=str(identity.get("physical_timeframe") or ""),
            micros=micros,
            columns=columns,
            identity_root_sha256=str(manifest["identity_root_sha256"]),
            rows_root_sha256=str(manifest["rows_root_sha256"]),
            cache_entry_dir=entry,
        )
        if verify_rows_root and partition.canonical_rows_root() != manifest.get(
            "rows_root_sha256"
        ):
            raise IntegratedSourceRejected("typed_rows_root_mismatch")
        return partition

    # -- verification -------------------------------------------------------

    def canonical_rows_root(self) -> str:
        """Re-derive the sealed `rows_root_sha256` from the columns.

        Streams: one transient dict is built and discarded per row, so peak
        memory is flat regardless of row count.
        """
        digest = hashlib.sha256(b"gtos.replay_acceleration.canonical_rows.v1\n")
        symbol = self.symbol
        micros = self.micros
        opens = self.columns["open"]
        highs = self.columns["high"]
        lows = self.columns["low"]
        closes = self.columns["close"]
        volumes = self.columns["volume"]
        for index in range(self.row_count):
            timestamp = iso_for_micros(int(micros[index]))
            digest.update(
                _canonical_bytes(
                    {
                        "time": timestamp,
                        "time_utc": timestamp,
                        "symbol": symbol,
                        "open": float(opens[index]),
                        "high": float(highs[index]),
                        "low": float(lows[index]),
                        "close": float(closes[index]),
                        "volume": float(volumes[index]),
                    }
                )
            )
            digest.update(b"\n")
        return digest.hexdigest()

    def nbytes(self) -> int:
        """Bytes actually held by the columns."""
        return int(
            self.micros.nbytes + sum(column.nbytes for column in self.columns.values())
        )

    # -- access -------------------------------------------------------------

    def rows(self) -> ColumnarRowSequence:
        return ColumnarRowSequence(self, 0, self.row_count)

    def _build_day_index(self) -> None:
        """Index contiguous UTC-day runs.

        Timestamps are strictly increasing within a typed-cache partition
        (verified against sealed January data: 192/192 partitions), so a day is
        a contiguous run and its bounds fall out of one `searchsorted`.
        """
        if self._day_labels is not None:
            return
        if self.row_count == 0:
            self._day_labels = ()
            self._day_starts = np.zeros(1, dtype="<i8")
            return
        day_ordinals = self.micros // _MICROS_PER_DAY
        if not bool(np.all(np.diff(day_ordinals) >= 0)):
            raise IntegratedSourceRejected("typed_partition_days_not_monotonic")
        boundaries = np.flatnonzero(np.diff(day_ordinals)) + 1
        starts = np.concatenate(
            (np.zeros(1, dtype=boundaries.dtype), boundaries)
        ).astype("<i8")
        labels = tuple(
            iso_for_micros(int(self.micros[int(start)]))[:10] for start in starts
        )
        self._day_labels = labels
        self._day_starts = np.concatenate(
            (starts, np.array([self.row_count], dtype="<i8"))
        )

    def day_labels(self) -> tuple[str, ...]:
        self._build_day_index()
        assert self._day_labels is not None
        return self._day_labels

    def rows_for_day(self, day: str) -> ColumnarRowSequence:
        """The rows of one UTC day, as a view. Empty view if the day is absent."""
        self._build_day_index()
        assert self._day_labels is not None and self._day_starts is not None
        try:
            position = self._day_labels.index(day)
        except ValueError:
            return ColumnarRowSequence(self, 0, 0)
        return ColumnarRowSequence(
            self,
            int(self._day_starts[position]),
            int(self._day_starts[position + 1]),
        )

    def rows_by_day(self) -> dict[str, ColumnarRowSequence]:
        """Every day present, as views.

        The columnar analogue of
        `v4_timewarp_simulated_live_research_loop.rows_by_day:4851`, which copies
        every row with ``dict(row)``. This copies nothing.
        """
        self._build_day_index()
        assert self._day_labels is not None and self._day_starts is not None
        return {
            label: ColumnarRowSequence(
                self, int(self._day_starts[index]), int(self._day_starts[index + 1])
            )
            for index, label in enumerate(self._day_labels)
        }

    def select_days(
        self, days: Iterable[str]
    ) -> tuple[tuple[ColumnarRowSequence, ...], dict[str, ColumnarRowSequence]]:
        """Views for the requested days, in sorted-day order.

        Matches `select_days` (`replay_acceleration_integrated_source.py:1082`):
        every requested day appears in the mapping, empty if absent, and the
        selection is concatenated in sorted-day order.
        """
        day_key = tuple(sorted({str(day) for day in days}))
        grouped = {day: self.rows_for_day(day) for day in day_key}
        selected = tuple(grouped[day] for day in day_key if len(grouped[day]))
        return selected, grouped


# ---------------------------------------------------------------------------
# Store
# ---------------------------------------------------------------------------


class ColumnarPartitionStore:
    """Process-wide memo: one `ColumnarPartition` per typed-cache identity.

    This is the half of the fix that removes *duplication*. The sealed loader
    keeps no partition-level memo, so each of the engine's three loader entry
    points re-reads `rows.bin` and builds an independent set of dicts under its
    own cache key. Here every caller that resolves to the same identity root
    gets the same object.
    """

    def __init__(self, *, verify_rows_root: bool = True) -> None:
        self._partitions: dict[str, ColumnarPartition] = {}
        self._lock = threading.Lock()
        self._verify_rows_root = verify_rows_root
        self._metrics: dict[str, int] = {
            "partition_load_count": 0,
            "partition_hit_count": 0,
            "row_count": 0,
            "column_bytes": 0,
        }

    def get(
        self,
        entry: Path,
        *,
        expected_identity: Mapping[str, Any] | None = None,
    ) -> ColumnarPartition:
        entry = Path(entry)
        key = entry.name
        with self._lock:
            cached = self._partitions.get(key)
            if cached is not None:
                self._metrics["partition_hit_count"] += 1
                return cached
        # Load outside the lock: decoding is the slow part and partitions are
        # independent. A concurrent duplicate load is wasteful but not wrong,
        # and the second one is discarded below.
        partition = ColumnarPartition.load(
            entry,
            expected_identity=expected_identity,
            verify_rows_root=self._verify_rows_root,
        )
        with self._lock:
            existing = self._partitions.get(key)
            if existing is not None:
                self._metrics["partition_hit_count"] += 1
                return existing
            self._partitions[key] = partition
            self._metrics["partition_load_count"] += 1
            self._metrics["row_count"] += partition.row_count
            self._metrics["column_bytes"] += partition.nbytes()
            return partition

    def metrics(self) -> dict[str, int]:
        with self._lock:
            return dict(self._metrics)

    def __len__(self) -> int:
        with self._lock:
            return len(self._partitions)

    def clear(self) -> None:
        with self._lock:
            self._partitions.clear()
            for key in self._metrics:
                self._metrics[key] = 0
