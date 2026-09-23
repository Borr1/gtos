"""ALIVE_MENU — rebuild Choice criteria from this-cycle inventory.

Stale menus (prior-cycle option maps after inventory change) are refused.
Escape hatches are always present. Cap is 255 options (TypeSafe high-cardinality).
"""

from __future__ import annotations

import hashlib
import uuid
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field

from .inventory import (
    ESCAPE_HATCHES,
    MAX_CHOICE_OPTIONS,
    LiveInventory,
)

ESCAPE_CRITERIA = {
    "HOLD": {
        "what": "Stay in current book state; no new fire and no APPLY.",
        "not_for": "A new enrolled fire the printer is already willing to send.",
        "examples": ("cluster forming", "spine empty", "chair sit dark"),
    },
    "ABSTAIN": {
        "what": "Not enough state or confidence to speak; book unchanged.",
        "not_for": "A house-law refuse (that is BLOCKED / writer).",
        "examples": ("missing slate_id", "Jev down", "Noul near 0.5"),
    },
    "ESCALATE_CHAIR": {
        "what": "Draft a Chair-visible card; Chair still writes the inbox.",
        "not_for": "Auto VETO, place, remint, or flatten.",
        "examples": ("MED band on sleeve_admit", "state_sufficient low"),
    },
    "BLOCKED": {
        "what": "Writer / house law already refuses; Jev answers are log-only.",
        "not_for": "Intelligence KEEP on a non-enrolled sleeve.",
        "examples": ("US30", "hard-off family", "two-stop exhausted"),
    },
}



def menu_hash(option_ids: Sequence[str]) -> str:
    """Permutation-invariant sha256 of the option id set (sorted)."""
    canonical = "|".join(sorted(str(x) for x in option_ids))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def option_order_hash(option_ids: Sequence[str]) -> str:
    """Permutation-sensitive sha256 of option ids in presented order."""
    presented = "|".join(str(x) for x in option_ids)
    return hashlib.sha256(presented.encode("utf-8")).hexdigest()


class StaleMenuError(ValueError):
    """Prior-cycle option map reused after inventory changed."""


@dataclass(frozen=True)
class Criterion:
    """Structured Choice option (what / not_for / examples)."""

    id: str
    what: str
    not_for: str
    examples: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class AliveMenu:
    """One cycle's Choice criteria. Always newly built; never a cached enum."""

    cycle_id: str
    inventory_fingerprint: str
    criteria: tuple[Criterion, ...]
    rebuilt: bool
    prior_fingerprint: str | None
    inventory_changed: bool
    notes: tuple[str, ...] = field(default_factory=tuple)

    @property
    def option_ids(self) -> tuple[str, ...]:
        return tuple(c.id for c in self.criteria)

    def as_dict(self) -> dict[str, object]:
        ids = list(self.option_ids)
        return {
            "cycle_id": self.cycle_id,
            "inventory_fingerprint": self.inventory_fingerprint,
            "criteria": [c.as_dict() for c in self.criteria],
            "rebuilt": self.rebuilt,
            "prior_fingerprint": self.prior_fingerprint,
            "inventory_changed": self.inventory_changed,
            "notes": list(self.notes),
            "option_ids": ids,
            "menu_hash": menu_hash(ids),
            "option_order_hash": option_order_hash(ids),
        }


def _sleeve_criterion(name: str) -> Criterion:
    return Criterion(
        id=f"sleeve:{name}",
        what=f"Consider live sleeve {name} that exists on this tick's inventory.",
        not_for="A hard-off / US30 / yesterday tag that is not in this inventory.",
        examples=(name,),
    )


def _worker_criterion(name: str) -> Criterion:
    return Criterion(
        id=f"worker:{name}",
        what=f"Address live worker {name} that is up this cycle.",
        not_for="A stopped launcher row or a quarantined verification worker.",
        examples=(name,),
    )


def _handler_criterion(name: str) -> Criterion:
    return Criterion(
        id=f"handler:{name}",
        what=f"Run supported non-broker handler {name}.",
        not_for="place / remint / flatten / order_send / token mint.",
        examples=(name,),
    )


def _escape_criterion(name: str) -> Criterion:
    spec = ESCAPE_CRITERIA[name]
    return Criterion(
        id=name,
        what=spec["what"],
        not_for=spec["not_for"],
        examples=tuple(spec["examples"]),
    )


def rebuild_choice_criteria(
    inventory: LiveInventory,
    *,
    prior_menu: AliveMenu | None = None,
    extra_ops: tuple[str, ...] = (),
) -> AliveMenu:
    """Always rebuild. Refuse reuse when the inventory fingerprint moved."""

    notes: list[str] = ["alive_menu_rebuilt"]
    prior_fp = prior_menu.inventory_fingerprint if prior_menu is not None else None
    changed = bool(prior_fp and prior_fp != inventory.fingerprint)
    if prior_menu is not None and changed:
        notes.append("inventory_changed_prior_menu_discarded")
    elif prior_menu is not None:
        notes.append("inventory_unchanged_menu_still_rebuilt")

    criteria: list[Criterion] = [_escape_criterion(name) for name in ESCAPE_HATCHES]
    for name in inventory.sleeves:
        criteria.append(_sleeve_criterion(name))
    for name in inventory.workers:
        criteria.append(_worker_criterion(name))
    for name in inventory.handlers:
        criteria.append(_handler_criterion(name))
    for raw in extra_ops:
        op = str(raw or "").strip()
        if not op or op in {c.id for c in criteria}:
            continue
        if op in ESCAPE_HATCHES:
            continue
        criteria.append(
            Criterion(
                id=op,
                what=f"Supported extra op {op} present this cycle.",
                not_for="Broker / place / remint / flatten.",
                examples=(op,),
            )
        )

    if len(criteria) > MAX_CHOICE_OPTIONS:
        notes.append("capped_at_255")
        # Keep escapes, then the first inventory rows (already prefer-filtered).
        head = [c for c in criteria if c.id in ESCAPE_HATCHES]
        rest = [c for c in criteria if c.id not in ESCAPE_HATCHES]
        budget = MAX_CHOICE_OPTIONS - len(head)
        criteria = head + rest[:budget]

    return AliveMenu(
        cycle_id=uuid.uuid4().hex,
        inventory_fingerprint=inventory.fingerprint,
        criteria=tuple(criteria),
        rebuilt=True,
        prior_fingerprint=prior_fp,
        inventory_changed=changed,
        notes=tuple(notes),
    )


def assert_menu_fresh(menu: AliveMenu, inventory: LiveInventory) -> None:
    """Call before the next Jev / compose step if a menu was held across a tick."""

    if menu.inventory_fingerprint != inventory.fingerprint:
        raise StaleMenuError(
            "ALIVE_MENU: prior-cycle option map does not match current inventory "
            f"({menu.inventory_fingerprint[:12]}… != {inventory.fingerprint[:12]}…)"
        )
    missing = [name for name in ESCAPE_HATCHES if name not in menu.option_ids]
    if missing:
        raise StaleMenuError(f"ALIVE_MENU missing escape hatches: {missing}")
    if len(menu.criteria) > MAX_CHOICE_OPTIONS:
        raise StaleMenuError("ALIVE_MENU exceeds 255 options")
