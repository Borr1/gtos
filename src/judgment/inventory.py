"""Live sleeve / worker inventory for ALIVE_MENU.

Choice criteria are rebuilt from what exists *this cycle*, not from a frozen
enum left over from last deploy. Hard-off families are recorded as blocked
context and are not offered as fire options.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable, Sequence

from .challenge import (
    CHALLENGE_HARD_OFF_FAMILIES,
    CHALLENGE_KEEP_FAMILIES,
    CHALLENGE_WORKER_ID,
)
from .research_armed import research_armed_tag_names

#: Non-broker handlers the sidecar itself can perform.
DEFAULT_HANDLERS = (
    "shadow_log",
    "label_draft",
    "escalate_chair",
    "review_flag",
)

ESCAPE_HATCHES = ("HOLD", "ABSTAIN", "ESCALATE_CHAIR", "BLOCKED")
MAX_CHOICE_OPTIONS = 255
# 4 escape hatches always reserved.
MAX_INVENTORY_OPTIONS = MAX_CHOICE_OPTIONS - len(ESCAPE_HATCHES)


@dataclass(frozen=True)
class LiveInventory:
    """What sleeves / workers / handlers exist on this tick."""

    sleeves: tuple[str, ...]
    workers: tuple[str, ...]
    handlers: tuple[str, ...]
    blocked_sleeves: tuple[str, ...]
    fingerprint: str
    collected_at_utc: str
    source: str
    notes: tuple[str, ...] = field(default_factory=tuple)
    research_armed_tags: tuple[str, ...] = field(default_factory=tuple)

    def option_names(self) -> tuple[str, ...]:
        return tuple(
            [f"sleeve:{n}" for n in self.sleeves]
            + [f"research_sleeve:{n}" for n in self.research_armed_tags]
            + [f"worker:{n}" for n in self.workers]
            + [f"handler:{n}" for n in self.handlers]
        )


def inventory_fingerprint(
    sleeves: Sequence[str],
    workers: Sequence[str],
    handlers: Sequence[str],
    blocked: Sequence[str] = (),
) -> str:
    payload = {
        "sleeves": list(sleeves),
        "workers": list(workers),
        "handlers": list(handlers),
        "blocked": list(blocked),
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _uniq(items: Iterable[str]) -> tuple[str, ...]:
    seen: list[str] = []
    bag: set[str] = set()
    for raw in items:
        name = str(raw or "").strip()
        if not name or name in bag:
            continue
        bag.add(name)
        seen.append(name)
    return tuple(seen)


def _w7_armed_sleeves() -> tuple[str, ...]:
    """Declared live W7 armed set — what exists on this tree right now."""

    from src.safety.armed_set import armed_sleeves

    return tuple(sorted(armed_sleeves()))


def _launcher_workers() -> tuple[str, ...]:
    from src.safety.armed_set import launcher_arming

    return tuple(sorted(launcher_arming().keys()))


def collect_live_inventory(
    *,
    sleeves: Sequence[str] | None = None,
    workers: Sequence[str] | None = None,
    handlers: Sequence[str] | None = None,
    include_w7_armed: bool = True,
    include_challenge_keep: bool = True,
    include_launcher_workers: bool = True,
    include_research_armed: bool = True,
) -> LiveInventory:
    """Build this-cycle inventory.

    Injected lists win (tests / leftover-ship F5 tags). Otherwise the live
    W7 armed set + launcher workers + Challenge keep-family nouns are unioned
    so the menu is never yesterday's gate list.

    Module_ATR winner tags land on ``research_armed_tags`` only — they are
    never written into ``live_armed_set.json`` and they are not fire sleeves.
    """

    notes: list[str] = []
    sleeve_acc: list[str] = []
    if sleeves is not None:
        sleeve_acc.extend(sleeves)
        notes.append("sleeves_injected")
    else:
        if include_challenge_keep:
            sleeve_acc.extend(CHALLENGE_KEEP_FAMILIES)
            notes.append("challenge_keep_families")
        if include_w7_armed:
            try:
                sleeve_acc.extend(_w7_armed_sleeves())
                notes.append("w7_armed_set")
            except Exception as exc:  # pragma: no cover - defensive
                notes.append(f"w7_armed_unavailable:{type(exc).__name__}")

    blocked = set(CHALLENGE_HARD_OFF_FAMILIES)
    live_sleeves = _uniq(s for s in sleeve_acc if s not in blocked)
    # Prefer keep / armed names if the union exceeds the Choice cap.
    if len(live_sleeves) > MAX_INVENTORY_OPTIONS:
        notes.append("score_then_choice_truncated")
        live_sleeves = live_sleeves[:MAX_INVENTORY_OPTIONS]

    worker_acc: list[str] = [CHALLENGE_WORKER_ID]
    if workers is not None:
        worker_acc.extend(workers)
        notes.append("workers_injected")
    elif include_launcher_workers:
        try:
            worker_acc.extend(_launcher_workers())
            notes.append("launcher_workers")
        except Exception as exc:  # pragma: no cover - defensive
            notes.append(f"launcher_workers_unavailable:{type(exc).__name__}")

    live_workers = _uniq(worker_acc)
    live_handlers = _uniq(handlers if handlers is not None else DEFAULT_HANDLERS)
    research_tags: tuple[str, ...] = ()
    if include_research_armed:
        try:
            research_tags = research_armed_tag_names()
            notes.append("research_armed_tags")
        except Exception as exc:  # pragma: no cover - defensive
            notes.append(f"research_armed_unavailable:{type(exc).__name__}")
    # Research overlay is never a live fire sleeve and never a live_armed_set splice.
    live_sleeves = _uniq(s for s in live_sleeves if s not in set(research_tags))
    blocked_tuple = tuple(sorted(blocked))
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    fp = inventory_fingerprint(live_sleeves, live_workers, live_handlers, blocked_tuple)
    return LiveInventory(
        sleeves=live_sleeves,
        workers=live_workers,
        handlers=live_handlers,
        blocked_sleeves=blocked_tuple,
        fingerprint=fp,
        collected_at_utc=now,
        source="live_cycle",
        notes=tuple(notes),
        research_armed_tags=research_tags,
    )
