"""DRAFT ONLY — not imported by live writer / VPS.

Admission helpers claimed in JEV_SCOPED_SELECT_APPLY_LAND_20260921.md
are MISSING from every sleeve_select.py on box. This is the sketch.

Fail-closed: if Jev dark and scoped APPLY off → None (no fire-rate change).
If Jev dark and scoped APPLY on → hist default STAND of the drop sleeve, logged.

place=false · global GTOS_JEV_SLEEVE_SELECT_APPLY stays 0
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence


XAU_STAND_REASON = "jev_sleeve_select_xau_conflict_stand_three_fresh"
GBPJPY_STAND_REASON = "jev_sleeve_select_gbpjpy_conflict_stand"


def _tags(alive_tags: Sequence[str]) -> list[str]:
    return [str(t) for t in alive_tags]


def should_stand_three_fresh_xau_conflict(
    symbol: str,
    alive_tags: Sequence[str],
    state: Mapping[str, Any] | None = None,
    *,
    jev_choice: str | None = None,
    scoped_apply_on: bool = False,
    jev_dark: bool = False,
) -> dict[str, Any] | None:
    """Return stand instruction or None. Never places."""
    sym = str(symbol or "").upper()
    if sym not in ("XAUUSD", "XAU"):
        return None
    tags = _tags(alive_tags)
    tf = [t for t in tags if "three_fresh" in t.lower()]
    sp = [t for t in tags if "spring" in t.lower()]
    if not (tf and sp):
        return None
    if jev_dark and not scoped_apply_on:
        return {
            "stand": None,
            "reason": "jev_dark_fail_closed_no_apply",
            "apply": False,
            "place": False,
            "fail_closed": True,
        }
    pick = jev_choice
    if pick is None and scoped_apply_on:
        pick = "KEEP_B"  # hist default: spring
    if pick == "STAND":
        return {
            "stand": tf + sp,
            "keep": [],
            "reason": XAU_STAND_REASON + "_both",
            "apply": scoped_apply_on,
            "place": False,
        }
    if pick == "KEEP_A":
        return {
            "stand": sp,
            "keep": tf[:1],
            "reason": "jev_choice_keep_three_fresh",
            "apply": scoped_apply_on,
            "place": False,
        }
    # KEEP_B or hist fallback
    return {
        "stand": tf,
        "keep": sp[:1],
        "reason": XAU_STAND_REASON,
        "apply": scoped_apply_on,
        "place": False,
        "hist_fallback": jev_choice is None,
    }


def should_stand_gbpjpy_conflict(
    symbol: str,
    alive_tags: Sequence[str],
    state: Mapping[str, Any] | None = None,
    *,
    jev_choice: str | None = None,
    scoped_apply_on: bool = False,
    jev_dark: bool = False,
) -> dict[str, Any] | None:
    """Opp-side: stand sub_mid. Same SHORT: stand vss. Unresolved: stand both."""
    if str(symbol or "").upper() != "GBPJPY":
        return None
    state = state or {}
    tags = _tags(alive_tags)
    vss = [t for t in tags if "vss" in t.lower()]
    sub = [
        t
        for t in tags
        if "sub_mid" in t.lower() and "eurusd" not in t.lower() and "package" not in t.lower()
    ]
    if not (vss and sub):
        return None
    if jev_dark and not scoped_apply_on:
        return {
            "stand": None,
            "reason": "jev_dark_fail_closed_no_apply",
            "apply": False,
            "place": False,
            "fail_closed": True,
        }
    sides = state.get("sleeve_sides") or {}
    vs = sides.get(vss[0].lower()) or sides.get("vss")
    ss = sides.get(sub[0].lower()) or sides.get("sub_mid")
    if vs is None or ss is None:
        if jev_choice in ("KEEP_A", "KEEP_B", "STAND"):
            pass
        else:
            return {
                "stand": vss + sub,
                "keep": [],
                "reason": GBPJPY_STAND_REASON + "_sides_unresolved",
                "apply": scoped_apply_on,
                "place": False,
            }
    if jev_choice == "STAND" or (vs is not None and ss is not None and int(vs) > 0 and int(ss) > 0):
        return {
            "stand": vss + sub,
            "keep": [],
            "reason": GBPJPY_STAND_REASON + "_residual_or_choice_stand",
            "apply": scoped_apply_on,
            "place": False,
        }
    if jev_choice == "KEEP_A" or (vs is not None and ss is not None and int(vs) > 0 and int(ss) < 0):
        return {
            "stand": sub,
            "keep": vss[:1],
            "reason": GBPJPY_STAND_REASON + "_opp_prefer_vss_LONG",
            "apply": scoped_apply_on,
            "place": False,
        }
    if jev_choice == "KEEP_B" or (vs is not None and ss is not None and int(vs) < 0 and int(ss) < 0):
        return {
            "stand": vss,
            "keep": sub[:1],
            "reason": GBPJPY_STAND_REASON + "_same_SHORT_prefer_sub_mid",
            "apply": scoped_apply_on,
            "place": False,
        }
    return {
        "stand": vss + sub,
        "keep": [],
        "reason": GBPJPY_STAND_REASON + "_unresolved",
        "apply": scoped_apply_on,
        "place": False,
    }
