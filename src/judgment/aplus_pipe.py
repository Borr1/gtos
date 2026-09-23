"""A+ setups × instruments — catalog vs the live gate / info pipe.

Owner vision: A+ setups on every instrument as **sleeves** on the same
flow as fluid gates + Jev observe (UB-AUTH-010 / UB-PLC-017 / FLUID-INVENTORY).

That is not the live wiring today.

* **A+** is Model A ``setup_grade`` (A+/A/B+/B/C) plus a framework
  (``ob_retest``, ``fvg_fill``, ``breaker_re_entry``, …). It lives on
  Primary Analyzer → Gate1 → Selector V4. It is a **catalog**.
* The **pipe** is W7 ``TradeIntent`` sleeves through ``admit_and_size``
  and ``_spread_cost_screen``. Jev observe is hooked there, and only
  there, via ``intent_gold_state``.

This module is diagnosis + a default-off observe stub. It does **not**
register a generator, expand ``--tags``, APPLY, or send. It does **not**
import ``selector_v4.py`` (R2-bound).
"""

from __future__ import annotations

from dataclasses import fields
from datetime import datetime, timezone
from typing import Any, Mapping

from .bars import normalize_symbol
from .gold_state import assemble_gold_state_v0
from .symbol_state import assemble_symbol_state_v0

SCHEMA = "gtos.judgment.aplus_pipe.v0"
OBSERVE_GATE = "APLU-OBS-001"

# Model A framework literals (analysis_models.PrimaryAnalysisOutput.framework).
A_PLUS_FRAMEWORKS: tuple[str, ...] = (
    "session_sweep",
    "ob_retest",
    "breaker_retest",
    "breaker_re_entry",
    "equal_sweep",
    "fvg_fill",
)

# agent_config.yaml model_a.enabled_frameworks — the live catalog subset.
MODEL_A_ENABLED: tuple[str, ...] = (
    "ob_retest",
    "fvg_fill",
    "breaker_re_entry",
)

# permissions._gate1_safety_checks admits only these grades.
GATE1_ADMIT_GRADES: tuple[str, ...] = ("A+", "A")

# TradeIntent (admission.py) carries sleeve mechanics, not Model A grade.
TRADE_INTENT_MISSING_APLUS_FIELDS: tuple[str, ...] = (
    "setup_grade",
    "framework",
    "kill_zone",
)

# Owner-declared armed W7 tags. Do not expand from this module.
ARMED_W7_SLEEVES: tuple[str, ...] = (
    "crypto",
    "energy_agri",
    "sub_xvol_pullback",
)


def aplus_sleeve_tag(framework: str | None) -> str:
    """Research-only tag. Not a BUILT / CANDIDATE_BUILT / --tags name."""
    name = (framework or "").strip() or "none"
    return f"aplus_{name}"


def _registry_tags() -> dict[str, frozenset[str]]:
    from src.components.ultimate_book.sleeves.registry import (
        BUILT,
        CANDIDATE_BUILT,
        MARKET_EXPANSION_BUILT,
    )

    return {
        "built": frozenset(BUILT),
        "candidate_built": frozenset(CANDIDATE_BUILT),
        "market_expansion_built": frozenset(MARKET_EXPANSION_BUILT),
    }


def trade_intent_field_names() -> frozenset[str]:
    from src.components.ultimate_book.admission import TradeIntent

    return frozenset(f.name for f in fields(TradeIntent))


def framework_pipe_status(framework: str) -> dict[str, Any]:
    """Gold-only vs catalog-only walls that keep this framework off the pipe."""
    tags = _registry_tags()
    alias = aplus_sleeve_tag(framework)
    on_built = alias in tags["built"] or framework in tags["built"]
    on_candidate = alias in tags["candidate_built"] or framework in tags["candidate_built"]
    enabled = framework in MODEL_A_ENABLED
    return {
        "framework": framework,
        "research_sleeve_tag": alias,
        "model_a_enabled": enabled,
        "on_w7_built": on_built,
        "on_w7_candidate_built": on_candidate,
        "on_armed_tags": False,
        "pipe_status": "catalog_only_not_on_w7_gate",
        "observe_ready": True,
        "generate_ready": False,
        "apply_ready": False,
        "walls": {
            "catalog_only": (
                "Framework is a Primary Analyzer / Gate1 literal, not a "
                "SleeveSpec.generator. active_specs never yields it."
            ),
            "gold_only": (
                "Live Jev observe assembles via intent_gold_state "
                "(default symbol XAUUSD). KB / expertise / session ATR "
                "are XAU-only on the Model A path."
            ),
        },
    }


def aplus_catalog() -> dict[str, Any]:
    """Named inventory. Every A+ framework is off the W7 gate pipe."""
    tags = _registry_tags()
    intent_fields = trade_intent_field_names()
    return {
        "schema": SCHEMA,
        "owner_vision": "A+ setups × all instruments as sleeves on fluid + Jev observe",
        "never_place": True,
        "never_remint": True,
        "never_flatten": True,
        "never_apply": True,
        "do_not_edit_selector_v4": True,
        "do_not_expand_armed_tags": True,
        "a_plus_is": "Model A setup_grade + framework, not a Jev type",
        "frameworks": [framework_pipe_status(name) for name in A_PLUS_FRAMEWORKS],
        "model_a_enabled": list(MODEL_A_ENABLED),
        "gate1_admit_grades": list(GATE1_ADMIT_GRADES),
        "w7_built": sorted(tags["built"]),
        "w7_candidate_built": sorted(tags["candidate_built"]),
        "armed_w7_sleeves": list(ARMED_W7_SLEEVES),
        "trade_intent_has_setup_grade": "setup_grade" in intent_fields,
        "trade_intent_has_framework": "framework" in intent_fields,
        "trade_intent_missing_aplus_fields": [
            name for name in TRADE_INTENT_MISSING_APLUS_FIELDS if name not in intent_fields
        ],
        "observe_gate": OBSERVE_GATE,
        "observe_default_off": True,
        "observe_body_fields": ["setup_grade", "framework", "kill_zone", "poi"],
        "observe_wired_to_bridge": False,
        "observe_wired_to_book_owner": False,
        "observe_wired_to_selector_v4": False,
        "live_observe_assembler": "intent_gold_state",
        "stub_observe_assembler": "assemble_symbol_state_v0 / intent_symbol_state",
        "host_land": aplus_host_land(),
    }


def _attr(obj: Any, *names: str) -> Any:
    for name in names:
        if isinstance(obj, dict) and name in obj:
            value = obj.get(name)
            if value is not None:
                return value
        elif hasattr(obj, name):
            value = getattr(obj, name)
            if value is not None:
                return value
    return None


def _reasoning(packet: Any) -> Any:
    return _attr(packet, "reasoning") or {}


def extract_aplus_poi(packet: Any) -> dict[str, Any]:
    """POI from a PA packet. Missing stays ``unassembled``. Never invent.

    Reads ``reasoning.h1_setup`` / top-level ``h1_setup`` / ``poi_*``.
    Does **not** write ``gold_state.levels.poi`` — that key stays the gold
    body's None so ``gold_keys_equal`` holds.
    """
    reasoning = _reasoning(packet)
    nested = (
        _attr(packet, "h1_setup")
        or _attr(reasoning, "h1_setup")
        or _attr(packet, "poi")
        or {}
    )
    poi_type = _attr(nested, "poi_type", "type") or _attr(packet, "poi_type")
    identified = _attr(nested, "poi_identified", "identified")
    price = _attr(nested, "poi_price_level", "poi_price", "price")
    if price is None:
        price = _attr(packet, "poi_price_level", "poi_price")
    zone = _attr(nested, "zone") or _attr(packet, "zone")
    causing = _attr(nested, "causing_event_type") or _attr(packet, "causing_event_type")
    type_s = str(poi_type).strip() if poi_type is not None else ""
    if type_s.lower() == "none":
        type_s = ""
    price_n: float | None
    try:
        if price is None or price == "":
            price_n = None
        else:
            price_n = float(price)
            if price_n == 0.0 and not identified:
                price_n = None
    except (TypeError, ValueError):
        price_n = None
    present = bool(identified) or bool(type_s) or price_n is not None
    return {
        "identified": bool(identified) if identified is not None else present,
        "poi_type": type_s or None,
        "price": price_n,
        "zone": (str(zone).strip() or None) if zone not in (None, "") else None,
        "causing_event_type": (
            str(causing).strip() or None
        ) if causing not in (None, "") else None,
        "source": "packet" if present else "unassembled",
        "invented": False,
        "gold_levels_poi_untouched": True,
    }


def aplus_observe_fields(packet: Any) -> dict[str, Any]:
    """The four fields the observe body must carry. Additive — not gold keys."""
    reasoning = _reasoning(packet)
    framework = str(_attr(packet, "framework") or _attr(reasoning, "framework") or "")
    grade = str(
        _attr(packet, "setup_grade")
        or _attr(reasoning, "setup_grade")
        or ""
    )
    kill_zone = str(_attr(packet, "kill_zone") or "")
    return {
        "setup_grade": grade,
        "framework": framework,
        "kill_zone": kill_zone,
        "poi": extract_aplus_poi(packet),
    }


def aplus_sleeve_features(packet: Any) -> dict[str, Any]:
    """A+ catalog fields. Metals A8 is not applied — that is wall B-20."""
    fields_here = aplus_observe_fields(packet)
    return {
        "tag": aplus_sleeve_tag(fields_here["framework"] or None),
        "setup_grade": fields_here["setup_grade"],
        "framework": fields_here["framework"],
        "kill_zone": fields_here["kill_zone"],
        "poi_type": fields_here["poi"].get("poi_type"),
        "poi_price": fields_here["poi"].get("price"),
        "pipe_status": "catalog_only_not_on_w7_gate",
        "metals_a8_applied": False,
        "on_w7_built": False,
        "generate_ready": False,
        "observe_ready": True,
        "a8_source": "not_aplus_features",
    }


def assemble_aplus_observe_state(
    packet: Any,
    tick: Any = None,
    *,
    books: dict[str, Any] | None = None,
    as_of_utc: datetime | None = None,
    occupancy: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Closed observe object for an A+ catalog row. Missing symbol stays missing.

    Uses ``assemble_symbol_state_v0`` directly so metals A8 does not wear
    the A+ feature slot. Live A1 / APPLY stay on ``intent_gold_state``.
    """
    raw_symbol = str(_attr(packet, "symbol") or "").strip()
    symbol = raw_symbol
    framework = str(_attr(packet, "framework") or _attr(_reasoning(packet), "framework") or "")
    side = str(_attr(packet, "side", "direction") or "unknown")
    feats = aplus_sleeve_features(packet)
    bid = _attr(tick, "bid")
    ask = _attr(tick, "ask")
    stop_dist = _attr(packet, "stop_dist")
    spread_r = None
    try:
        sd = float(stop_dist or 0.0)
        if sd > 0 and bid is not None and ask is not None:
            spread_r = (float(ask) - float(bid)) / sd
    except (TypeError, ValueError):
        spread_r = None
    as_of = as_of_utc or datetime.now(timezone.utc)
    # XAU A+ observe keeps the gold body. Empty symbol stays empty (not XAU).
    assembler = (
        assemble_gold_state_v0
        if raw_symbol and normalize_symbol(raw_symbol) == "XAUUSD"
        else assemble_symbol_state_v0
    )
    try:
        state = assembler(
            as_of_utc=as_of,
            side=side,
            sleeve=feats["tag"],
            symbol=symbol,
            candidate_id=str(
                _attr(packet, "candidate_id", "ticket") or f"{symbol}:{feats['tag']}"
            ),
            origin_organism="aplus_catalog_observe",
            as_of_clock="aplus_observe",
            books=books,
            geometry={
                "entry": _attr(packet, "entry", "entry_price"),
                "stop": _attr(packet, "stop", "sl"),
                "target": _attr(packet, "target", "tp"),
                "stop_dist": stop_dist,
                "order_type": _attr(packet, "order_type") or "MARKET",
            },
            cost={
                "spread_r_of_stop": spread_r,
                "source": "tick" if spread_r is not None else "unassembled",
                "cost_screen_would_refuse": spread_r is not None and spread_r > 0.10,
            },
            sleeve_features=feats,
            occupancy=occupancy or {},
        )
    except Exception:
        return None
    # gold_state.v0 copies a fixed metals-A8 feature set. A+ identity is additive.
    # Do not write levels.poi — that would break the gold-body contract.
    observe_fields = aplus_observe_fields(packet)
    out = dict(state)
    out["aplus"] = {
        "schema": SCHEMA,
        "setup_grade": observe_fields["setup_grade"],
        "framework": observe_fields["framework"] or framework,
        "kill_zone": observe_fields["kill_zone"],
        "poi": observe_fields["poi"],
        "research_sleeve_tag": feats["tag"],
        "pipe_status": feats["pipe_status"],
        "metals_a8_applied": False,
        "gate1_would_admit": observe_fields["setup_grade"] in GATE1_ADMIT_GRADES,
        "on_w7_built": False,
        "generate_ready": False,
        "shadow_only": True,
        "never_apply": True,
    }
    return out


def observe_aplus_candidate(
    packet: Mapping[str, Any] | None,
    tick: Any = None,
    *,
    books: dict[str, Any] | None = None,
    as_of_utc: datetime | None = None,
) -> dict[str, Any]:
    """Default-off research observe. Same fluid questions, symbol_state body.

    Not imported from bridge.py / book_owner.py / selector_v4.py.
    """
    from .a1_log import observe, observe_fluid_inventory

    packet = dict(packet or {})
    state = assemble_aplus_observe_state(
        packet, tick, books=books, as_of_utc=as_of_utc
    )
    observe_fields = aplus_observe_fields(packet)
    extra = {
        "site": OBSERVE_GATE,
        "setup_grade": observe_fields["setup_grade"],
        "framework": observe_fields["framework"],
        "kill_zone": observe_fields["kill_zone"],
        "poi": observe_fields["poi"],
        "symbol": _attr(packet, "symbol") or "",
        "wired_to_host": False,
        "cannot_refuse": True,
        "cannot_place": True,
        "cannot_apply": True,
        "do_not_expand_armed_tags": True,
    }
    row = observe(OBSERVE_GATE, state, extra=extra)
    fluid = observe_fluid_inventory(state, extra={"site": OBSERVE_GATE, **extra})
    row["fluid_inventory"] = {
        "gate_id": fluid.get("gate_id"),
        "n_fluid": fluid.get("n_fluid"),
        "skipped": fluid.get("skipped"),
        "never_place": fluid.get("never_place"),
    }
    aplus_body = (state or {}).get("aplus") or {}
    row["aplus"] = {
        "schema": SCHEMA,
        "pipe_status": "catalog_only_not_on_w7_gate",
        "state_schema": (state or {}).get("schema"),
        "identity_symbol": ((state or {}).get("identity") or {}).get("symbol"),
        "setup_grade": aplus_body.get("setup_grade") or observe_fields["setup_grade"],
        "framework": aplus_body.get("framework") or observe_fields["framework"],
        "kill_zone": aplus_body.get("kill_zone") or observe_fields["kill_zone"],
        "poi": aplus_body.get("poi") or observe_fields["poi"],
        "shadow_only": True,
    }
    return row


def _intent_to_aplus_packet(intent: Any) -> dict[str, Any]:
    """Best-effort packet from a W7 intent or a PA-shaped dict. No send."""
    if isinstance(intent, dict):
        packet = dict(intent)
    else:
        packet = {}
    for name in (
        "symbol",
        "side",
        "direction",
        "sleeve",
        "tag",
        "framework",
        "setup_grade",
        "kill_zone",
        "entry",
        "entry_price",
        "stop",
        "sl",
        "stop_dist",
        "target",
        "tp",
        "candidate_id",
        "ticket",
        "order_type",
        "reasoning",
        "h1_setup",
        "poi",
        "poi_type",
        "poi_price",
        "poi_price_level",
    ):
        if name not in packet or packet.get(name) is None:
            value = _attr(intent, name)
            if value is not None:
                packet[name] = value
    if not packet.get("framework") and str(packet.get("sleeve") or "").startswith("aplus_"):
        packet["framework"] = str(packet["sleeve"])[len("aplus_") :]
    return packet


def maybe_observe_aplus_at_place(
    intent: Any,
    tick: Any,
    cost_skip: str | None,
) -> dict[str, Any]:
    """SHADOW helper the host book_owner would call after cost_skip.

    Default-off. Does **not** mutate ``cost_skip``. Does **not** place.
    Does **not** APPLY. Does **not** expand ``--tags``. Does **not**
    soften an envelope wall.

    Host must env-gate ``GTOS_JEV_A1_LOG`` / ``GTOS_JEV_ALIVE_SHADOW``
    **before** importing this function. Do not wholesale-copy
    ``book_owner.py``. Do not import from ``selector_v4.py``.
    This tree does **not** splice the call — see
    ``judgment/astra/lab/wires/HOST_APLU_OBS_LAND.md``.
    """
    from .a1_log import a1_enabled

    extra_land = {
        "cost_skip": cost_skip,
        "must_not_mutate_cost_skip": True,
        "host_splice": "after_cost_skip_call",
        "do_not_wholesale_copy_book_owner": True,
        "do_not_edit_selector_v4": True,
        "do_not_expand_armed_tags": True,
        "envelope_stays_integer": True,
        "never_apply": True,
        "never_place": True,
    }
    if not a1_enabled():
        return {
            "schema": "gtos.judgment.a1_log.v0",
            "gate_id": OBSERVE_GATE,
            "skipped": "GTOS_JEV_A1_LOG_off",
            "shadow_log_only": True,
            "never_place": True,
            "never_remint": True,
            "never_flatten": True,
            "never_apply": True,
            "extra": extra_land,
        }
    packet = _intent_to_aplus_packet(intent)
    row = observe_aplus_candidate(packet, tick)
    extra = dict(row.get("extra") or {})
    extra.update(extra_land)
    row["extra"] = extra
    return row


def aplus_host_land() -> dict[str, Any]:
    """Machine-readable HOST splice note. Not a live wire."""
    return {
        "schema": "gtos.judgment.aplus_host_land.v0",
        "gate_id": OBSERVE_GATE,
        "shadow_only": True,
        "wired_on_this_tree": False,
        "never_place": True,
        "never_apply": True,
        "do_not_wholesale_copy_book_owner": True,
        "do_not_edit_selector_v4": True,
        "do_not_expand_armed_tags": True,
        "envelope_stays_integer": True,
        "host_file": "src/components/ultimate_book/book_owner.py",
        "host_symbol": "def _spread_cost_screen",
        "host_line_pulled": 9531,
        "github_call_needle": "cost_skip = self._spread_cost_screen",
        "hook": (
            "AFTER cost_skip = self._spread_cost_screen(intent, tick). "
            "Env-gate GTOS_JEV_A1_LOG or GTOS_JEV_ALIVE_SHADOW BEFORE import. "
            "Call maybe_observe_aplus_at_place(intent, tick, cost_skip). "
            "Do not mutate cost_skip. Do not wholesale-copy book_owner."
        ),
        "env_before_import": ["GTOS_JEV_A1_LOG", "GTOS_JEV_ALIVE_SHADOW"],
        "helper": "src.judgment.aplus_pipe.maybe_observe_aplus_at_place",
        "note_path": "judgment/astra/lab/wires/HOST_APLU_OBS_LAND.md",
        "same_site_as": "UB-PLC-017",
    }

