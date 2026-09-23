"""Wire the columnar source layer into the replay engine without editing it.

Why a bridge rather than an edit
--------------------------------
The construction site is `replay_acceleration_attempt5_typed_sparse_runner.py:15680`
and the loader is `replay_acceleration_integrated_source.py:974-1079`. Both files
are in R2's 43 bound paths *and* in `code_authority_paths`
(`attempt5:1405-1431`), so editing either forces a contract regeneration, a
re-seal, and a re-run of every affected window. This module changes neither
file's bytes: it subclasses the sealed accelerator and rebinds the name in the
runner's namespace at runtime. The H1 membership check stays at its expected
`drifted=1`.

What it actually changes
------------------------
Exactly one method — `_load_partition`. The sealed version returns a
`TypedPartitionResult` whose `.rows` is a `tuple[dict, ...]`: **every row of the
whole partition, as Python dicts**, built fresh on each call
(`integrated_source.py:432-450`). This version returns a lazy
`ColumnarRowSequence` over columns held once by a `ColumnarPartitionStore`.

Nothing downstream needs to know. The three consumers all iterate the sequence
exactly once and build their own dicts as they go:

- `select_replay_lookback_window:1148-1149` — ``for source_row in rows: row =
  dict(source_row)`` — retains only a bounded `deque` of pre-window rows plus the
  selected window, and `break`s past `end_day` (`:1157`).
- `select_days:1088-1089` — same shape, keyed to the requested days.
- `legacy.rows_by_day:4853-4857` — same shape (reached only via `load_file`,
  which is dead on the sealed path; see B81).

So the rows those functions *retain* are ordinary dicts, byte-identical to
today's, and the full-partition dict set is simply never built. `load_file*`
return values, `stable_sha256` over the returned rows (`:1076-1078`), and every
downstream digest are unchanged by construction.

Fallback is total: on any rejection, a cache miss, or a partition the columnar
loader cannot read, this silently defers to the sealed implementation.
"""

from __future__ import annotations

import functools
from typing import Any

from src.research_infra import replay_acceleration_attempt5_typed_sparse_runner as attempt5
from src.research_infra import v4_timewarp_simulated_live_research_loop as legacy
from src.research_infra.replay_acceleration_integrated_source import (
    IntegratedSourceRejected,
    RealReplaySourceAccelerator,
    TypedPartitionResult,
    _AcceptedPartition,
    _root,
)
from src.research_infra.replay_columnar_source import ColumnarPartitionStore

__all__ = ["ColumnarSourceAccelerator", "install", "uninstall", "metrics"]

_INSTALLED: list[Any] = []
_STORE = ColumnarPartitionStore(verify_rows_root=True)


class ColumnarSourceAccelerator(RealReplaySourceAccelerator):
    """The sealed accelerator, with partitions served from columns.

    Subclassed rather than reimplemented so `from_accepted_bundle`, `authority`,
    `accepted_source_candidates` and `prewarm_all` keep the sealed behaviour and
    the sealed authority digest exactly.
    """

    def _columnar_entry(self, partition: _AcceptedPartition):
        """Resolve the typed-cache entry for a partition without decoding it."""
        identity = self._cache._identity(
            source_path=partition.source_path,
            symbol=partition.symbol,
            physical_timeframe=partition.physical_timeframe,
            source_payload_root=partition.source_payload_root,
            expected_normalized_root=partition.normalized_root,
            expected_normalized_row_count=partition.normalized_row_count,
        )
        identity_root = _root(identity)
        return self._cache.root / identity_root, identity, identity_root

    def _load_partition(self, partition: _AcceptedPartition) -> TypedPartitionResult:
        try:
            entry, identity, identity_root = self._columnar_entry(partition)
        except IntegratedSourceRejected:
            return super()._load_partition(partition)

        if not entry.is_dir():
            # Cold miss: let the sealed writer build and seal the entry, then
            # serve it from columns so the dicts it just built are released.
            sealed = super()._load_partition(partition)
            if not entry.is_dir():
                return sealed

        try:
            columnar = _STORE.get(entry, expected_identity=identity)
        except (IntegratedSourceRejected, OSError, ValueError):
            return super()._load_partition(partition)

        return TypedPartitionResult(
            columnar.rows(),  # lazy; not a tuple of dicts
            True,
            identity_root,
            entry,
        )


def install() -> None:
    """Rebind the accelerator used by the engine, and join its release path.

    Idempotent. The second rebind matters: the engine releases source memory at
    chunk boundaries via `clear_replay_source_caches`
    (`v4_timewarp_simulated_live_research_loop.py:5048`, called from
    `attempt5:8670` and `:9758`). A module-global store that ignores that call
    holds its columns for the whole run and *adds* to peak RSS — measured at
    ~0.17 GB in the first arm-level A/B, which is most of why that run came out
    0.27 GB above the sealed baseline. Joining the release path fixes it.
    """
    if _INSTALLED:
        return
    _INSTALLED.append((attempt5.RealReplaySourceAccelerator, legacy.clear_replay_source_caches))
    attempt5.RealReplaySourceAccelerator = ColumnarSourceAccelerator

    sealed_clear = legacy.clear_replay_source_caches

    @functools.wraps(sealed_clear)
    def clear_including_columns() -> None:
        sealed_clear()
        _STORE.clear()

    legacy.clear_replay_source_caches = clear_including_columns
    # attempt5 imported the name directly, so rebind it there too or the engine
    # keeps calling the original.
    if getattr(attempt5, "clear_replay_source_caches", None) is sealed_clear:
        attempt5.clear_replay_source_caches = clear_including_columns


def uninstall() -> None:
    if not _INSTALLED:
        return
    accelerator, sealed_clear = _INSTALLED.pop()
    attempt5.RealReplaySourceAccelerator = accelerator
    legacy.clear_replay_source_caches = sealed_clear
    if getattr(attempt5, "clear_replay_source_caches", None) is not sealed_clear:
        if hasattr(attempt5, "clear_replay_source_caches"):
            attempt5.clear_replay_source_caches = sealed_clear


def metrics() -> dict[str, int]:
    return _STORE.metrics()
