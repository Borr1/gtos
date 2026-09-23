"""Training-lane compact-sink fork: retain snapshot dicts until day-end.

The frozen replay sink is a disk-backed proof spool. It serializes every
decision and missed row on append, then the attempt-5 runner seals the spool and
immediately iterates it, which decompresses and decodes every row before writing
the day's JSONL ledgers. That is the right contract for a bounded sealed replay,
but CB measured the serialize/decode round trip at 14.9% of wall and the train
lane has enough RAM to retain one day of rows.

This fork changes only the storage medium:

* ``append`` still applies the frozen row projectors, increments the same counts,
  and observes the same relational identities;
* ``_append_canonical_row`` takes a deep snapshot, preserving the frozen sink's
  append-time semantics if the producer mutates a row later;
* ``seal`` marks a lane-only, non-authorizing in-memory authority; and
* ``iter_rows`` yields a fresh deep copy, matching the isolation supplied by a
  JSON decode. The attempt-5 day-end writer then performs the row's one and only
  serialization into its final JSONL ledger.

The frozen module is imported, never edited. This resident authority cannot be
reopened and declares no proof hash: it is a training-lane transport, with
trade/order/missed-pool identity as its acceptance gate.
"""

from __future__ import annotations

from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from src.research_infra import replay_compact_event_sink as frozen
from src.research_infra.fast_engine import accel


RESIDENT_EVENT_SINK_SCHEMA = "gtos.train_engine.resident_event_sink.v1"
ATTEMPT5_MODULE = (
    "src.research_infra.replay_acceleration_attempt5_typed_sparse_runner"
)

_STATS: Counter[str] = Counter()


def reset_stats() -> None:
    _STATS.clear()


def report() -> dict[str, Any]:
    return {
        "sinks_created": int(_STATS["sinks_created"]),
        "rows_snapshotted": int(_STATS["rows_snapshotted"]),
        "rows_iterated": int(_STATS["rows_iterated"]),
        "seals": int(_STATS["seals"]),
        "aborts": int(_STATS["aborts"]),
        "peak_resident_rows_per_sink": int(_STATS["peak_resident_rows_per_sink"]),
        "json_serializations_inside_sink": 0,
        "json_decodes_inside_sink": 0,
    }


class TrainResidentEventSink(frozen.ReplayCompactEventSink):
    """One-day resident snapshot store with the frozen sink's public facade."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._resident_rows: dict[str, list[tuple[int, dict[str, Any]]]] = {
            role: [] for role in frozen.COMPACT_EVENT_ROLES
        }
        self._resident_count = 0
        _STATS["sinks_created"] += 1

    @classmethod
    def open_sealed(
        cls,
        *,
        root: Path,
        expected_authority_root_sha256: str,
    ) -> "TrainResidentEventSink":
        del root, expected_authority_root_sha256
        raise frozen.CompactEventSinkError("resident_sink_not_reopenable")

    def _append_canonical_row(
        self,
        role: str,
        row: Mapping[str, Any],
        *,
        ordinal: int,
    ) -> None:
        # The disk sink's json.dumps freezes the row at append time. A shallow
        # copy would not: nested producer payloads are mutable, so deepcopy is
        # the identity-preserving equivalent of that serialization boundary.
        snapshot = copy.deepcopy(dict(row))
        self._resident_rows[role].append((ordinal, snapshot))
        self._resident_count += 1
        _STATS["rows_snapshotted"] += 1
        _STATS["peak_resident_rows_per_sink"] = max(
            _STATS["peak_resident_rows_per_sink"], self._resident_count
        )

    def seal(self) -> dict[str, Any]:
        if self._aborted:
            raise frozen.CompactEventSinkError("sink_aborted")
        if self._sealed:
            if self._authority is None:
                raise frozen.CompactEventSinkError("sealed_authority_missing")
            return copy.deepcopy(self._authority)

        row_counts = {
            role: int(self._row_counts[role]) for role in frozen.COMPACT_EVENT_ROLES
        }
        resident_counts = {
            role: len(self._resident_rows[role])
            for role in frozen.COMPACT_EVENT_ROLES
        }
        if row_counts != resident_counts:
            raise frozen.CompactEventSinkError("resident_row_count_mismatch")
        deterministic = {
            "schema": RESIDENT_EVENT_SINK_SCHEMA,
            "format": "append_time_deep_snapshot_dicts",
            "status": "sealed_training_transport",
            "roles": list(frozen.COMPACT_EVENT_ROLES),
            "row_counts": row_counts,
            "resident_canonical_row_count": self._resident_count,
            "json_serializations_inside_sink": 0,
            "json_decodes_inside_sink": 0,
            "reopenable": False,
            "acceptance_authority": False,
            "relational_identity_audit": self.relational_identity_audit(),
        }
        authority_root = hashlib.sha256(
            json.dumps(
                deterministic,
                sort_keys=True,
                separators=(",", ":"),
                default=str,
            ).encode("utf-8")
        ).hexdigest()
        self._authority = {
            **deterministic,
            "authority_root_sha256": authority_root,
            "root_materialization": "empty_directory_only",
        }
        self._sealed = True
        _STATS["seals"] += 1
        return copy.deepcopy(self._authority)

    def iter_rows(self, role: str):
        role = self._require_role(role)
        if not self._sealed or self._authority is None:
            raise frozen.CompactEventSinkError("sink_not_sealed")
        expected = 0
        for ordinal, row in self._resident_rows[role]:
            if ordinal != expected:
                raise frozen.CompactEventSinkError("role_ordinal_mismatch")
            expected += 1
            _STATS["rows_iterated"] += 1
            yield copy.deepcopy(row)
        if expected != int(self._authority["row_counts"][role]):
            raise frozen.CompactEventSinkError("role_row_count_mismatch")

    def abort(self) -> None:
        if not self._sealed:
            for rows in self._resident_rows.values():
                rows.clear()
            self._resident_count = 0
            _STATS["aborts"] += 1
        super().abort()


def make_patch() -> accel.Patch:
    saved: dict[str, Any] = {}

    def apply() -> None:
        module = accel._module(ATTEMPT5_MODULE)
        if module is None or not hasattr(module, "ReplayCompactEventSink"):
            return
        saved[ATTEMPT5_MODULE] = module.ReplayCompactEventSink
        module.ReplayCompactEventSink = TrainResidentEventSink

    def revert() -> None:
        for module_name, value in saved.items():
            module = accel._module(module_name)
            if module is not None:
                module.ReplayCompactEventSink = value
        saved.clear()

    return accel.Patch(
        patch_id="train_resident_event_sink",
        summary=(
            "retain append-time deep-snapshot dicts for one day and serialize "
            "only in the attempt-5 day-end JSONL writer"
        ),
        identity_argument=(
            "Deepcopy establishes the same append-time snapshot as frozen "
            "json.dumps, and every iteration yields a fresh deepcopy like "
            "json.loads. Row order/count, row projection and relational identity "
            "use the inherited frozen paths. The resident authority is explicitly "
            "non-reopenable and non-authorizing; outcome identity is the gate."
        ),
        apply=apply,
        revert=revert,
        default_on=True,
        sealed_compatible=False,
    )


__all__ = [
    "RESIDENT_EVENT_SINK_SCHEMA",
    "TrainResidentEventSink",
    "make_patch",
    "report",
    "reset_stats",
]
