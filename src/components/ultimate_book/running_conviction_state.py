"""Leak-free RUNNING per-day conviction count for the Kelly-lite tilt (default-OFF).

The validated W7 MC sizes the Kelly-lite day-level conviction tilt off the FULL-DAY count of distinct
firing sleeves (KB7_growth_kelly_sizing.py) — a count that, live, is only knowable with LOOKAHEAD (when
an early-cycle trade is sized, later-cycle sleeves are still in the future). The live book therefore
counts per-EVALUATION-CYCLE, which UNDER-sizes vs the validated dial and makes the same signal size
differently on the two accounts.

This store recovers the validated convention WITHOUT lookahead: it persists the set of distinct
sleeves whose placement has been accepted SO FAR TODAY (per intent.decision_day, the UTC bar date =
the admission grouping key). A current candidate is included provisionally while it is sized, but it
is not committed until the downstream cost, permission, idempotency and broker placement path accepts
it. A refused candidate therefore cannot size up a later candidate. That running count is
a leak-free SUBSET of the full-day union, so the resulting Kelly bin is <= the validated full-day bin
for every unit (proven bounded-above by the validated MC envelope; it CANNOT breach more than the
validated 0% daily). It only ever sizes UP toward the validated nominal — never above it.

State file (per namespace): pipeline_state/ultimate_book/<namespace>/firing_sleeves.json
  {"days": {"YYYY-MM-DD": ["idxrev", "metals_core", ...]}}

No order path. Best-effort + atomic (tmp + os.replace); NEVER raises into the decision path — a read/
write error yields an empty count, and the sizer falls back to the per-cycle count (== current live
behavior), so the running-count can never block trading nor mis-size on a storage fault.
"""
from __future__ import annotations

import json
import os
import uuid
from typing import Any, Mapping

_HOP: dict[tuple, dict[str, float | None]] = {}


def _finite(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _keep_days(day_names: list[str]) -> float | None:
    key = tuple(sorted(str(day) for day in day_names))
    if key in _HOP:
        return _HOP[key].get("keep_days")
    payload = {"days": list(key), "n_days": len(key)}
    number = None
    try:
        from src.judgment.nineteen import score as ask

        number = _finite(
            ask(
                payload,
                question_id="keep_days",
                instructions=(
                    "The score you return is how many recent decision days this conviction file still keeps. "
                    "An empty score does not drop a day. Do not send."
                ),
                anchors=[("decision days named on this state", float(len(key)))],
            )
        )
    except Exception:
        number = None
    _HOP[key] = {"keep_days": number}
    return number


class RunningConvictionLedger:
    def __init__(self, repo_root: str, namespace: str = "ftmo_primary"):
        self._dir = os.path.join(repo_root, "pipeline_state", "ultimate_book", namespace)
        os.makedirs(self._dir, exist_ok=True)
        self._path = os.path.join(self._dir, "firing_sleeves.json")

    def _read(self) -> dict:
        try:
            with open(self._path, encoding="utf-8") as fh:
                obj = json.load(fh)
            return obj if isinstance(obj, dict) else {}
        except (OSError, ValueError):
            return {}

    def _write(self, obj: dict) -> None:
        try:
            # UNIQUE temp per write (pid+uuid): in the documented restart-race window two same-namespace
            # workers must NOT do concurrent truncating writes to ONE shared `*.tmp` -> interleaved bytes
            # produce corrupt JSON that os.replace then publishes. Each writer's own tmp + atomic rename
            # keeps every published file well-formed (a wrong firing count would mis-tilt the Kelly-lite n).
            tmp = f"{self._path}.{os.getpid()}.{uuid.uuid4().hex}.tmp"
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(obj, fh)
            os.replace(tmp, self._path)
        except OSError:
            pass

    def update_and_count(self, firing_by_day: Mapping[str, "set[str]"]) -> dict[str, int]:
        """Commit accepted sleeves to the persisted per-day sets (idempotent across re-ticks), prune
        to the most recent days, and return {decision_day: distinct-accepted-sleeve-count-so-far}.

        NEVER raises. On any fault returns {} (the caller then falls back to the per-cycle count)."""
        try:
            store = self._read()
            days = store.get("days")
            if not isinstance(days, dict):
                days = {}
            # union this cycle's fired sleeves into each day's running set
            for day, sleeves in (firing_by_day or {}).items():
                cur = set(days.get(day) or [])
                cur.update(s for s in (sleeves or set()) if s)
                days[day] = sorted(cur)
            keep = _keep_days(list(days.keys()))
            if keep is not None and keep > 0 and len(days) > int(keep):
                for stale in sorted(days.keys())[:-int(keep)]:
                    days.pop(stale, None)
            self._write({"days": days})
            return {day: len(set(days.get(day) or [])) for day in (firing_by_day or {})}
        except Exception:
            return {}

    def count_with_provisional(self, firing_by_day: Mapping[str, "set[str]"]) -> dict[str, int]:
        """Return committed sleeves union the current provisional candidates WITHOUT writing.

        Admission needs the current sleeve in its own Kelly breadth, but a refusal downstream must
        not enter durable conviction state. This preview/commit split is the boundary: callers use
        this method before placement and :meth:`update_and_count` only after placement is accepted.

        NEVER raises. On any fault returns {} so the caller retains the existing per-cycle fallback.
        """
        try:
            store = self._read()
            days = store.get("days")
            if not isinstance(days, dict):
                days = {}
            return {
                day: len(set(days.get(day) or []).union(
                    sleeve for sleeve in (sleeves or set()) if sleeve
                ))
                for day, sleeves in (firing_by_day or {}).items()
            }
        except Exception:
            return {}
