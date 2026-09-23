"""SKETCH only — writer consume of place_action. Never calls broker.

Default-off until GTOS_JEV_PLACE_FLUID_APPLY=1 AND prove receipt AND scoped symbol.
Jev dark / missing choice → DELAY.
Envelope wall → STAND.
"""

from __future__ import annotations

from typing import Any

JUDGMENT_LABELS = frozenset({"PLACE", "STAND", "DELAY", "place", "stand", "delay"})


def consume_place_choice(
    choice: str | None,
    *,
    apply_flag: bool,
    envelope_hit: str | None,
    jev_ok: bool,
    symbol_in_scope: bool,
    prove_ok: bool,
) -> str:
    if envelope_hit:
        return "STAND"
    if not jev_ok or not choice:
        return "DELAY"
    label = str(choice).strip().upper()
    if label == "STAND":
        return "STAND"
    if label == "DELAY":
        return "DELAY"
    if label == "PLACE" and apply_flag and symbol_in_scope and prove_ok:
        return "PLACE_AUTHORIZED"
    return "DELAY"


def is_judgment_place_label(action: str) -> bool:
    return str(action or "").strip().upper() in {"PLACE", "STAND", "DELAY"}
