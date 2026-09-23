"""Module_ATR winner affinity tags as a research overlay.

These tags exist on leftover-ship F5 as J2b ALL36-GEOMETRY sleeves
(``NOT ARMED``, forward_only). They are **not** spliced into
``config/live_armed_set.json`` and they are **not** W7 ``armed_sleeves()``.

Jev never ``order_send``. Place stays on the Challenge writer only.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .challenge import CHALLENGE_LOGIN

AUTHORITY = Path(__file__).resolve().parents[2] / "judgment" / "astra" / "research_armed_tags.json"

MODULE_ATR_WINNER_TAGS = (
    "dsp_three_fresh_lower_lows",
    "dsp_spring_close_on_20low_through_the_box",
)

LIVE_ARMED_SET_PATH = Path(__file__).resolve().parents[2] / "config" / "live_armed_set.json"


def load_research_armed_tags(*, path: Path | str | None = None) -> dict[str, Any]:
    """Load the Chair-named research overlay. Missing file ⇒ empty tags."""

    authority = Path(path) if path is not None else AUTHORITY
    if not authority.is_file():
        return {
            "schema": "gtos.judgment.research_armed_tags.v1",
            "source": "module_atr_winners",
            "tags": [],
            "live_armed_set_mutated": False,
            "place": "writer_only",
            "missing_authority": True,
        }
    doc = json.loads(authority.read_text(encoding="utf-8"))
    tags = tuple(
        str(t).strip()
        for t in (doc.get("tags") or MODULE_ATR_WINNER_TAGS)
        if str(t).strip()
    )
    return {
        "schema": str(doc.get("schema") or "gtos.judgment.research_armed_tags.v1"),
        "source": str(doc.get("source") or "module_atr_winners"),
        "module": str(doc.get("module") or "Module_ATR"),
        "tags": list(tags),
        "surface": list(doc.get("surface") or []),
        "status": str(doc.get("status") or "research_overlay_only"),
        "live_armed_set_mutated": False,
        "place": "writer_only",
        "never_order_send": True,
        "login": CHALLENGE_LOGIN,
        "path": str(authority),
        "hard_off_keep_research": False,
        "missing_authority": False,
    }


def research_armed_tag_names(*, path: Path | str | None = None) -> tuple[str, ...]:
    doc = load_research_armed_tags(path=path)
    return tuple(doc.get("tags") or ())


def live_armed_set_contains(tag: str) -> bool:
    """True only if the W7 declaration already names ``tag``. Read-only."""

    if not LIVE_ARMED_SET_PATH.is_file():
        return False
    doc = json.loads(LIVE_ARMED_SET_PATH.read_text(encoding="utf-8"))
    accounts = doc.get("accounts") or {}
    for block in accounts.values():
        armed = block.get("armed_sleeves") or []
        if tag in armed:
            return True
    return False


def attach_research_overlay(
    gold_state: Mapping[str, Any] | None,
    *,
    tags: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Copy STATE with research overlay on identity. Does not mutate live_armed_set."""

    src = dict(gold_state or {})
    ident = dict(src.get("identity") or {})
    overlay = load_research_armed_tags()
    named = tags if tags is not None else tuple(overlay.get("tags") or ())
    ident["research_armed_tags"] = list(named)
    ident["research_overlay"] = {
        "source": overlay.get("source") or "module_atr_winners",
        "module": overlay.get("module") or "Module_ATR",
        "live_armed_set_mutated": False,
        "place": "writer_only",
        "never_order_send": True,
        "hard_off_keep_research": False,
        "affinity_rule": "instrument_x_sleeve_not_global",
    }
    src["identity"] = ident
    src["research_armed_tags"] = list(named)
    return src
