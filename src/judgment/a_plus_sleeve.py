"""A+ sleeve on gate flow — first-class sleeve, not a side catalog.

Owner vision lock (SYMBOL_STATE_V0): A+ setups for every instrument become
sleeves. Those sleeves sit on the **same** Challenge information flow
(assemble typed state → fluid / admit / selector observe → compose size
observe). They are not a parallel catalog and they do not place.

SHADOW / observe first. Never place / remint / flatten. Never silent APPLY.
CA labels may enrich any sleeve. Missing primitives stay unassembled.
"""

from __future__ import annotations

from typing import Any, Mapping

from .bars import normalize_symbol
from .family import family_class_for
from .symbol_class import asset_class_for

SCHEMA = "gtos.judgment.sleeve.v0"
GATE_FLOW_NAME = "a_plus_sleeve_on_gate_flow"
A_PLUS_PREFIXES = ("aplus_", "a_plus_")

# Same pipe live Challenge already uses. Not a second inventory.
GATE_PIPE = (
    "assemble_symbol_state_v0",
    "observe_fluid_inventory",  # fluid
    "observe UB-AUTH-010 / FLUID-ADM-*",  # admit
    "observe_sel_v4_002",  # selector, research-only
    "compose_shadow",  # size observe
)

GATE_CONSUMERS = ("fluid", "admit", "selector", "size_observe")

# Per-symbol A+ library. Each row IS a sleeve tag. Stubs: no generator, no fire.
A_PLUS_LIBRARY_V0: dict[str, tuple[dict[str, Any], ...]] = {
    "XAUUSD": (
        {"tag": "aplus_xau_london_htf_align", "setup_kind": "london_htf_align", "session": "london"},
        {"tag": "aplus_xau_ny_continuation", "setup_kind": "ny_continuation", "session": "ny"},
    ),
    "EURUSD": (
        {"tag": "aplus_eurusd_london_session_reclaim", "setup_kind": "london_session_reclaim", "session": "london"},
    ),
    "USDJPY": (
        {"tag": "aplus_usdjpy_tokyo_ny_usd_leg", "setup_kind": "tokyo_ny_usd_leg", "session": "tokyo_ny"},
    ),
    "GBPJPY": (
        {"tag": "aplus_gbpjpy_london_cross", "setup_kind": "london_cross", "session": "london"},
    ),
    "US30": (
        {"tag": "aplus_us30_ny_open", "setup_kind": "ny_open", "session": "ny", "house_us30_off": True},
    ),
    "GBPUSD": (
        {"tag": "aplus_gbpusd_london_session_reclaim", "setup_kind": "london_session_reclaim", "session": "london"},
    ),
}


def is_a_plus_tag(sleeve: str | None) -> bool:
    sl = (sleeve or "").strip().lower()
    return any(sl.startswith(p) for p in A_PLUS_PREFIXES)


def library_for(symbol: str | None) -> list[dict[str, Any]]:
    """Named A+ sleeves for this primary. Empty list is honest, not a catalog miss."""
    return [dict(row) for row in A_PLUS_LIBRARY_V0.get(normalize_symbol(symbol), ())]


def lookup_a_plus(symbol: str | None, sleeve: str | None) -> dict[str, Any] | None:
    tag = (sleeve or "").strip().lower()
    if not tag:
        return None
    for row in library_for(symbol):
        if str(row.get("tag") or "").lower() == tag:
            return dict(row)
    if is_a_plus_tag(tag):
        return {"tag": tag, "setup_kind": "unassembled", "session": None, "source": "prefix_only"}
    return None


def gate_flow_block(*, a_plus: bool, observe_only: bool) -> dict[str, Any]:
    return {
        "name": GATE_FLOW_NAME,
        "side_catalog": False,
        "pipe": list(GATE_PIPE),
        "consumers": list(GATE_CONSUMERS),
        "same_as_live_challenge": True,
        "a_plus": a_plus,
        "observe_only": observe_only,
        "never_place": True,
        "never_silent_apply": True,
        "never_remint": True,
        "never_flatten": True,
    }


def enrich_ca_labels(world: Mapping[str, Any] | None) -> dict[str, Any]:
    """CA / world labels may enrich ANY sleeve. Never invent DXY or yields."""
    packed = dict(world or {})
    source = packed.get("source") or "unassembled"
    labels = packed.get("labels") or packed.get("ca_labels") or packed.get("cross_asset")
    if not isinstance(labels, dict):
        labels = {}
    return {
        "source": source if source != "unassembled" or labels else "unassembled",
        "labels": dict(labels),
        "dxy": packed.get("dxy"),
        "rates": packed.get("rates"),
        "never_invent_dxy": True,
        "never_invent_tips": True,
        "never_invent_yield": True,
        "enriches_any_sleeve": True,
    }


def attach_sleeve_object(
    *,
    symbol: str,
    sleeve: str,
    family_class: str | None = None,
    origin_organism: str = "f5_challenge",
    world: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """First-class sleeve on the Challenge gate pipe. Not a catalog card."""
    sym = normalize_symbol(symbol)
    tag = (sleeve or "").strip() or "unknown"
    family = family_class or family_class_for(tag, symbol=sym, origin=origin_organism)
    hit = lookup_a_plus(sym, tag)
    a_plus = bool(hit) or is_a_plus_tag(tag)
    observe_only = a_plus or sym != "XAUUSD"
    return {
        "schema": SCHEMA,
        "tag": tag,
        "symbol": sym,
        "asset_class": asset_class_for(sym),
        "family_class": family,
        "origin_organism": origin_organism,
        "a_plus": a_plus,
        "setup_kind": (hit or {}).get("setup_kind"),
        "session": (hit or {}).get("session"),
        "library": "per_symbol_a_plus" if a_plus else "challenge_live",
        "library_row": hit if a_plus else None,
        "side_catalog": False,
        "gate_flow": GATE_FLOW_NAME,
        "observe_only": observe_only,
        "ca_labels": enrich_ca_labels(world),
        "never_place": True,
        "never_silent_apply": True,
        "never_remint": True,
        "never_flatten": True,
    }


def observe_a_plus_on_gate_flow(
    state: Mapping[str, Any] | None,
    *,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run the live Challenge observe pipe. SHADOW only. Never place."""
    from .a1_log import observe_fluid_inventory, observe_sel_v4_002
    from .compose import compose_shadow

    packed = dict(state or {})
    sleeve = (packed.get("sleeve") or {}) if isinstance(packed.get("sleeve"), dict) else {}
    extra_row = {"gate_flow": GATE_FLOW_NAME, "a_plus_sleeve_on_gate_flow": True, **(extra or {})}
    fluid = observe_fluid_inventory(packed, extra=extra_row)
    selector = observe_sel_v4_002({"symbol": (packed.get("identity") or {}).get("symbol"), **extra_row})
    composed = compose_shadow(packed, extra=extra_row)
    apply_row = bool(composed.get("apply_this_row")) and not (
        sleeve.get("a_plus") or sleeve.get("never_silent_apply")
    )
    return {
        "schema": "gtos.judgment.gate_flow_observe.v0",
        "gate_flow": GATE_FLOW_NAME,
        "side_catalog": False,
        "consumers": list(GATE_CONSUMERS),
        "fluid": {k: fluid.get(k) for k in ("gate_id", "skipped", "logged", "n_fluid")},
        "selector": {k: selector.get(k) for k in ("gate_id", "skipped", "logged")},
        "compose": {
            "disposition": composed.get("disposition"),
            "apply_this_row": composed.get("apply_this_row"),
            "named_apply_symbol": composed.get("named_apply_symbol"),
            "combined_live_tilt": composed.get("combined_live_tilt"),
        },
        "apply_this_row": apply_row,
        "never_place": True,
        "never_silent_apply": True,
        "never_remint": True,
        "never_flatten": True,
    }
