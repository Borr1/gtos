"""Owner/Chair gate for never_place / remint / flatten.

Chair ENFORCE 2026-09-21: Owner unlock + GTOS_JEV_PLACE_APPLY enough.
Prove receipt optional audit — does not re-cage Owner unlock.
Dig Land D drafts only — never broker-sends.
"""
from __future__ import annotations
import os
from pathlib import Path
from typing import Mapping, Protocol

PLACE_APPLY_ALIASES = (
    "GTOS_JEV_PLACE_APPLY",
    "GTOS_JEV_PLACE_CHOICE_APPLY",
    "GTOS_JEV_PLACE_FLUID_APPLY",
)
_TRUTHY = frozenset({"1", "true", "yes", "on"})
LEGAL_WIRE_CLASSES = frozenset({"A1", "A2", "A3", "W_named"})

class _ReceiptLike(Protocol):
    proven: bool
    wire_class: str

def _env_on(name: str, environ: Mapping[str, str] | None = None) -> bool:
    env = environ if environ is not None else os.environ
    return str(env.get(name, "")).strip().lower() in _TRUTHY

def place_apply_enabled(*, environ: Mapping[str, str] | None = None) -> bool:
    env = environ if environ is not None else os.environ
    return any(_env_on(name, env) for name in PLACE_APPLY_ALIASES)

def owner_unlock_acknowledged() -> bool:
    # VPS: env flag OR Chair unlock already applied via PLACE_APPLY
    return place_apply_enabled() or _env_on("GTOS_JEV_OWNER_PLACE_UNLOCK")

def receipt_legal(receipt: _ReceiptLike | None) -> bool:
    if receipt is None:
        return False
    if not bool(getattr(receipt, "proven", False)):
        return False
    return str(getattr(receipt, "wire_class", "") or "") in LEGAL_WIRE_CLASSES

def never_place_effective(
    *,
    environ: Mapping[str, str] | None = None,
    receipt: _ReceiptLike | None = None,
) -> bool:
    """True (block) unless Owner unlock + Chair APPLY. Receipt optional."""
    if not place_apply_enabled(environ=environ) and not owner_unlock_acknowledged():
        return True
    if not place_apply_enabled(environ=environ):
        return True
    _ = receipt
    return False

def never_remint_effective(*, environ=None, receipt=None) -> bool:
    return never_place_effective(environ=environ, receipt=receipt)

def never_flatten_effective(*, environ=None, receipt=None) -> bool:
    return never_place_effective(environ=environ, receipt=receipt)
