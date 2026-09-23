"""Chair G1–G8 ENFORCE surface for S14 admit/size *labels*.

This module never places. It only constrains shadow labels so S14 cannot
weaken hard-offs (INDEX / xa_huge / orb_crypto / bleed / mx_us30 / US30)
or boost KEEP (G7 ALLOW_NO_BOOST).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .challenge import CHALLENGE_HARD_OFF_FAMILIES, CHALLENGE_KEEP_FAMILIES

CHAIR_ENFORCE_PATH = (
    Path(__file__).resolve().parents[2] / "judgment" / "astra" / "chair_enforce_g1_g8.json"
)

#: INDEX family + US30 symbol. Do not weaken.
INDEX_SLEEVE_MARKERS = ("idxrev",)
INDEX_SYMBOL_PREFIXES = ("US30",)
HARD_OFF_MARKERS = tuple(CHALLENGE_HARD_OFF_FAMILIES) + ("orb_",)
KEEP_MARKERS = tuple(CHALLENGE_KEEP_FAMILIES) + ("dsp_spring", "vss_fxcross")

G6_CUT_SESSIONS = frozenset({"London", "NY", "London_NY_overlap", "Asia", "london", "ny", "asia"})
G6_LEAVE_ALONE = frozenset({"Asia_London_pre", "Off_hours", "asia_london_pre", "off_hours"})

FLUID_STAMPS_OBSERVE = (
    "FLUID-ADM-002",
    "FLUID-ADM-007",
    "FLUID-PLC-001",
    "f5_xau_flow_alignment_size_tilt",
    "FLUID-SIZ-008",
)


def load_chair_enforce(path: Path | None = None) -> dict[str, Any]:
    target = path if path is not None else CHAIR_ENFORCE_PATH
    if not target.is_file():
        return {
            "schema": "gtos.chair.enforce.v1",
            "login": 0,
            "decisions": {},
            "note": "chair_enforce_file_missing_fail_closed_hard_offs_still_hold",
        }
    return json.loads(target.read_text(encoding="utf-8"))


def _contains_marker(name: str, markers: tuple[str, ...]) -> bool:
    raw = str(name or "").strip().lower()
    if not raw:
        return False
    for marker in markers:
        m = marker.lower()
        if raw == m or raw.startswith(m) or f"_{m}" in raw or raw.startswith(f"{m}_"):
            return True
    return False


def is_hard_off_sleeve(sleeve: str | None) -> bool:
    return _contains_marker(sleeve or "", HARD_OFF_MARKERS)


def is_index_hard_off(*, sleeve: str | None, symbol: str | None) -> bool:
    if _contains_marker(sleeve or "", INDEX_SLEEVE_MARKERS):
        return True
    sym = str(symbol or "").strip().upper()
    return any(sym == p or sym.startswith(p) for p in INDEX_SYMBOL_PREFIXES)


def is_keep_family(sleeve: str | None) -> bool:
    raw = str(sleeve or "").strip().lower()
    if not raw:
        return False
    if raw in CHALLENGE_KEEP_FAMILIES:
        return True
    return _contains_marker(raw, KEEP_MARKERS)


def hard_off_reason(*, sleeve: str | None, symbol: str | None) -> str | None:
    if is_index_hard_off(sleeve=sleeve, symbol=symbol):
        return "chair_g_index_hard_off"
    if is_hard_off_sleeve(sleeve):
        if _contains_marker(sleeve or "", ("xa_huge",)):
            return "chair_xa_huge_hard_off"
        if _contains_marker(sleeve or "", ("orb_crypto", "orb_")):
            return "chair_orb_crypto_hard_off"
        if _contains_marker(sleeve or "", ("bleed",)):
            return "chair_bleed_hard_off"
        if _contains_marker(sleeve or "", ("mx_us30",)):
            return "chair_mx_us30_hard_off"
        return "chair_hard_off_family"
    return None


@dataclass(frozen=True)
class ChairEnforceStamp:
    """Constraints applied to an S14 label. Never a broker send."""

    hard_off: bool
    hard_off_reason: str | None
    keep_family: bool
    keep_no_boost: bool
    g4_size_ceiling: float | None
    g6_size_ceiling: float | None
    g7_size_ceiling: float
    g8_block_reentry: bool
    size_ceiling: float
    decisions: dict[str, str]
    notes: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "hard_off": self.hard_off,
            "hard_off_reason": self.hard_off_reason,
            "keep_family": self.keep_family,
            "keep_no_boost": self.keep_no_boost,
            "g4_size_ceiling": self.g4_size_ceiling,
            "g6_size_ceiling": self.g6_size_ceiling,
            "g7_size_ceiling": self.g7_size_ceiling,
            "g8_block_reentry": self.g8_block_reentry,
            "size_ceiling": self.size_ceiling,
            "decisions": dict(self.decisions),
            "notes": list(self.notes),
            "fluid_stamps_observe": list(FLUID_STAMPS_OBSERVE),
        }


def stamp_chair_enforce(
    *,
    sleeve: str | None,
    symbol: str | None,
    session_named: str | None = None,
    occupancy: Mapping[str, Any] | None = None,
    chair_doc: Mapping[str, Any] | None = None,
    g4_applies: bool = False,
) -> ChairEnforceStamp:
    doc = dict(chair_doc) if chair_doc is not None else load_chair_enforce()
    raw_decisions = doc.get("decisions") if isinstance(doc.get("decisions"), Mapping) else {}
    decisions = {
        key: str((raw_decisions.get(key) or {}).get("status") or "")
        for key in ("G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8")
    }
    notes = [
        "g1_g3_confirm_enforce_not_weakened",
        "g5_confirm_shadow_stay_shadow",
        "broker_effect_always_false",
    ]
    reason = hard_off_reason(sleeve=sleeve, symbol=symbol)
    keep = is_keep_family(sleeve)
    if keep:
        notes.append("g7_keep_allow_no_boost")

    g4_ceiling = None
    if g4_applies and not keep:
        g4_ceiling = 0.5
        notes.append("g4_allow_with_cut_ceiling_0_5")

    g6_ceiling = None
    sess = str(session_named or "").strip()
    if sess and sess not in G6_LEAVE_ALONE and sess.lower() not in {s.lower() for s in G6_LEAVE_ALONE}:
        if sess in G6_CUT_SESSIONS or sess.lower() in {s.lower() for s in G6_CUT_SESSIONS}:
            if not keep:
                g6_ceiling = 0.75
                notes.append("g6_session_cut_0_75")
            else:
                notes.append("g6_exempt_keep_surface")
    elif sess:
        notes.append("g6_leave_alone_session")

    occ = occupancy if isinstance(occupancy, Mapping) else {}
    g8_block = False
    if occ.get("already_placed_today") is True:
        g8_block = True
        notes.append("g8_block_reentry_same_sleeve_already_placed_today")
    minutes = occ.get("minutes_since_flat")
    new_named = occ.get("new_named_fire") is True
    try:
        mins = float(minutes) if minutes is not None else None
    except (TypeError, ValueError):
        mins = None
    if mins is not None and mins < 15 and not new_named:
        if occ.get("same_sleeve_reentry") is True or occ.get("already_placed_today") is True:
            g8_block = True
            notes.append("g8_block_reentry_within_15m")
    if new_named and mins is not None and mins >= 15:
        notes.append("g8_allow_after_15m_new_named_fire_only")

    ceiling = 1.0  # G7 ALLOW_NO_BOOST — never boost
    if g6_ceiling is not None:
        ceiling = min(ceiling, g6_ceiling)
    if g4_ceiling is not None:
        ceiling = min(ceiling, g4_ceiling)

    return ChairEnforceStamp(
        hard_off=reason is not None,
        hard_off_reason=reason,
        keep_family=keep,
        keep_no_boost=True,
        g4_size_ceiling=g4_ceiling,
        g6_size_ceiling=g6_ceiling,
        g7_size_ceiling=1.0,
        g8_block_reentry=g8_block,
        size_ceiling=ceiling,
        decisions=decisions,
        notes=tuple(notes),
    )
