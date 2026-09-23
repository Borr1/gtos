"""Named CA size wire — Score size_tilt. Hist-proved Challenge 0.

``ca_cross_asset_size_tilt`` consumes the seven CA labels
(OCC / LIQ / EVT / USD / CORR / RSK / IDX). Conservative veto-class clamp
``[0.70, 1.00]``: cannot add size, cannot zero a fire, cannot refuse.

Chair APPLY flag: ``GTOS_JEV_CA_SIZE_APPLY=1``. Default-off helper keeps
live=1.0. When the flag is on (and process_lock APPLY is open for the
row), live follows the shadow product. Compose still multiplies
flow × cost × ca on its own path.

This module does not place, remint, or flatten (size_tilt only — not an
eternal never_place law). Empty news spine is not "no HIGH" and is not
an invented HIGH. Do not invent NEWS_PROTOCOL.
"""

from __future__ import annotations

import os
from typing import Any, Mapping

from .cross_asset import local_cross_asset_answers
from .process_lock import (
    CA_TILT_MAX,
    CA_TILT_MIN,
    WIRE_CA_SIZE,
    leave_orig_ticket,
    wire_apply_open,
)

WIRE_ID = WIRE_CA_SIZE
CA_SIZE_SCHEMA = "gtos.judgment.ca_size.v1"
APPLY_ENV = "GTOS_JEV_CA_SIZE_APPLY"

# Seven CA labels this named fire consumes. CA-* label APPLY stays false.
CONSUMED_LABELS = (
    "CA-OCC-001",
    "CA-LIQ-001",
    "CA-EVT-001",
    "CA-USD-001",
    "CA-CORR-001",
    "CA-RSK-001",
    "CA-IDX-001",
)

# Conservative defaults. Missing / unassembled / mixed / no_clear → 1.0.
# No component is a boost. Chair later may widen the clamp; this pack does not.
OCC_CROWDED_TILT = 0.85
LIQ_THIN_TILT = 0.80
EVT_HIGH_TILT = 0.70
USD_ADVERSE_TILT = 0.85
CORR_WITH_USD_TILT = 0.85
RSK_ON_TILT = 0.90
IDX_WITH_US30_TILT = 0.92


def _f(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _side_sign(side: Any) -> int:
    raw = str(side or "").lower()
    if raw in {"long", "buy"}:
        return 1
    if raw in {"short", "sell"}:
        return -1
    return 0


def _clamp(value: float) -> float:
    return round(min(CA_TILT_MAX, max(CA_TILT_MIN, float(value))), 4)


def ca_size_apply_env() -> bool:
    """Chair land flag. Unset/0 → helper live stays 1.0."""
    return os.environ.get(APPLY_ENV, "").strip().lower() in {"1", "true", "yes", "on"}


def ca_size_apply_open(*, ticket: Any = None, house_block: bool = False) -> bool:
    """Size-tilt APPLY for this row. Never place. Leave-orig and house_block stay 1.0."""
    if house_block:
        return False
    if leave_orig_ticket(ticket):
        return False
    if not ca_size_apply_env():
        return False
    return wire_apply_open(WIRE_CA_SIZE, ticket=ticket)


def _component(name: str, raw: Any, tilt: float, *, assembled: bool, source: str) -> dict[str, Any]:
    return {
        "name": name,
        "input": raw,
        "tilt": 1.0 if not assembled else round(float(tilt), 4),
        "assembled": bool(assembled),
        "source": source,
    }


def ca_size_components(
    world: Mapping[str, Any] | None,
    *,
    side: Any = None,
    answers: Mapping[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    """Per-label component tilts. Unassembled stays 1.0 — never a guessed 0.0."""
    packed = dict(world or {})
    local = dict(answers or local_cross_asset_answers(packed))
    occ = local.get("occupancy_world") or {}
    liq = local.get("session_liquidity") or {}
    corr = local.get("gold_usd_comove") or {}
    rsk = local.get("risk_on_funding") or {}
    idx = local.get("gold_index_comove") or {}
    ev = packed.get("event_join") or {}
    usd_named = (packed.get("usd_proxy") or {}).get("named")

    occ_score = _f(occ.get("score"))
    occ_ok = bool(occ.get("decidable")) and occ_score is not None
    occ_tilt = OCC_CROWDED_TILT if occ_ok and occ_score >= 2.0 else 1.0

    liq_score = _f(liq.get("score"))
    liq_ok = bool(liq.get("decidable")) and liq_score is not None
    liq_tilt = LIQ_THIN_TILT if liq_ok and liq_score <= 0.0 else 1.0

    spine_empty = bool(ev.get("spine_empty"))
    ev_ok = (not spine_empty) and ev.get("source") == "news_spine"
    high = bool(
        ev.get("usd_high_in_window")
        or ev.get("gbp_high_in_window")
        or ev.get("jpy_high_in_window")
        or ev.get("eur_high_in_window")
    )
    ev_tilt = EVT_HIGH_TILT if ev_ok and high else 1.0

    usd_ok = usd_named not in {None, "unassembled"}
    sign = _side_sign(side)
    usd_tilt = 1.0
    if usd_ok and sign != 0:
        if usd_named == "usd_up" and sign > 0:
            usd_tilt = USD_ADVERSE_TILT
        elif usd_named == "usd_down" and sign < 0:
            usd_tilt = USD_ADVERSE_TILT

    corr_choice = corr.get("choice")
    corr_ok = bool(corr.get("decidable")) and corr_choice not in {None, "no_clear"}
    corr_tilt = CORR_WITH_USD_TILT if corr_ok and corr_choice == "with_usd" else 1.0

    rsk_choice = rsk.get("choice")
    rsk_ok = bool(rsk.get("decidable")) and rsk_choice not in {None}
    rsk_tilt = RSK_ON_TILT if rsk_ok and rsk_choice == "risk_on" else 1.0

    idx_choice = idx.get("choice")
    idx_ok = bool(idx.get("decidable")) and idx_choice not in {None, "no_clear"}
    idx_tilt = IDX_WITH_US30_TILT if idx_ok and idx_choice == "with_us30" else 1.0

    return {
        "occupancy_world": _component("occupancy_world", occ_score, occ_tilt, assembled=occ_ok, source="world.occupancy_book"),
        "session_liquidity": _component("session_liquidity", liq_score, liq_tilt, assembled=liq_ok, source="world.session_liquidity"),
        "event_join": _component(
            "event_join",
            None if spine_empty else high,
            ev_tilt,
            assembled=ev_ok,
            source="world.event_join" if ev_ok else "news_spine_empty",
        ),
        "usd_proxy": _component("usd_proxy", usd_named if usd_ok else None, usd_tilt, assembled=usd_ok, source="world.usd_proxy"),
        "gold_usd_comove": _component(
            "gold_usd_comove",
            corr_choice if corr.get("decidable") else None,
            corr_tilt,
            assembled=corr_ok,
            source="world.gold_vs_usd",
        ),
        "risk_on_funding": _component(
            "risk_on_funding",
            rsk_choice if rsk.get("decidable") else None,
            rsk_tilt,
            assembled=rsk_ok,
            source="world.risk_on",
        ),
        "gold_index_comove": _component(
            "gold_index_comove",
            idx_choice if idx.get("decidable") else None,
            idx_tilt,
            assembled=idx_ok,
            source="world.gold_vs_index",
        ),
    }


def ca_cross_asset_size_tilt(
    world: Mapping[str, Any] | None,
    *,
    side: Any = None,
    answers: Mapping[str, Any] | None = None,
) -> float:
    """Map PROVED CA labels onto ``[0.70, 1.00]``. Missing world → 1.0."""
    parts = ca_size_components(world, side=side, answers=answers)
    product = 1.0
    any_assembled = False
    for block in parts.values():
        if block.get("assembled"):
            any_assembled = True
            product *= float(block.get("tilt") or 1.0)
    if not any_assembled:
        return 1.0
    return _clamp(product)


def score_ca_size(
    world: Mapping[str, Any] | None,
    *,
    side: Any = None,
    answers: Mapping[str, Any] | None = None,
    house_block: bool = False,
    ticket: Any = None,
    apply: bool | None = None,
) -> dict[str, Any]:
    """Shadow product always. Live follows shadow only when APPLY is open for the row.

    Default ``apply=None`` reads ``GTOS_JEV_CA_SIZE_APPLY``. Explicit ``apply``
    still cannot override house_block or leave-orig. Cannot refuse. Cannot add
    size. Empty spine stays unassembled (tilt 1.0) — never invented HIGH.
    """
    parts = ca_size_components(world, side=side, answers=answers)
    assembled = [p for p in parts.values() if p.get("assembled")]
    shadow = 1.0 if house_block else ca_cross_asset_size_tilt(world, side=side, answers=answers)
    if apply is None:
        apply_flag = ca_size_apply_open(ticket=ticket, house_block=house_block)
    else:
        apply_flag = bool(apply) and (not house_block) and (not leave_orig_ticket(ticket))
    live = _clamp(shadow) if apply_flag else 1.0
    if apply_flag:
        live = min(live, CA_TILT_MAX)
    moved = abs(float(shadow) - 1.0) > 1e-9
    return {
        "schema": CA_SIZE_SCHEMA,
        "wire": WIRE_ID,
        "consumes": list(CONSUMED_LABELS),
        "shadow": shadow,
        "live": live,
        "apply": bool(apply_flag),
        "apply_env": APPLY_ENV,
        "decidable": bool(assembled) and not house_block,
        "moved": moved and not house_block,
        "n_components_assembled": len(assembled),
        "components": parts,
        "range": [CA_TILT_MIN, CA_TILT_MAX],
        "cannot_refuse": True,
        "cannot_add_size": True,
        "physical_size_stays_flow_x_cost": not apply_flag,
        "physical_size_stays_flow_x_cost_x_ca": True,
        "house_block": bool(house_block),
        "leave_orig": leave_orig_ticket(ticket),
        "this_module_places": False,
        "never_place": True,
        "invented_news_protocol": False,
    }
