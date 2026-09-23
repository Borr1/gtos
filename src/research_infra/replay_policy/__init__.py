"""``replay_policy`` — the Phase-2 policy-plural decision core.

One core, N policy modules behind one ``Policy`` interface
(`FULL_VISION_PLAN.md:201-204`).  The structural amendment exists because of F1:
with policy-plural, "replay measures the thing that trades" is true by
construction for any OD-1 outcome, and E1 cannot reopen.

Modules
-------
``core``        the ``Policy`` protocol, its data contract, and ``DecisionCore``
``sleeve_book`` ``SleeveBookPolicy`` — the live ``ultimate_book`` W7 book
``inert``       ``InertPolicy`` — a second implementation, so the core is
                demonstrably not shaped around one policy

Nothing here reaches a broker.  ``sleeve_book`` imports the live decision path
(``src.components.ultimate_book.bridge``), which is pure by contract:
"performs NO broker/account/order work" (``bridge.py:295-296``).
"""
from __future__ import annotations

from .core import (
    AccountDayState,
    DecisionCore,
    Policy,
    PolicyAllocation,
    PolicyCandidate,
    PolicyDecision,
    PolicyError,
    PolicyUnit,
)
from .inert import InertPolicy
from .sleeve_book import SleeveBookPolicy

__all__ = [
    "AccountDayState",
    "DecisionCore",
    "InertPolicy",
    "Policy",
    "PolicyAllocation",
    "PolicyCandidate",
    "PolicyDecision",
    "PolicyError",
    "PolicyUnit",
    "SleeveBookPolicy",
]
