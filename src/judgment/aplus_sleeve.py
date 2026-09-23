"""APlusSleeveV0 — A+ setups as first-class sleeves on the Challenge gate pipe.

Not a side catalog. Each named A+ setup is a sleeve identity that rides the
same gold_state → admit / fluid / selector-observe / Jev compose path as
live Challenge tags. SHADOW only: never APPLY size, never place, remint,
or flatten.

Peer / CA slots stay named hooks. SYMBOL_STATE_V0 may later fill
``peers.peer_state``; this module does not invent DXY, funding, or peer
prices.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from .bars import StampedBar, normalize_symbol
from .chair_fields import CHAIR_FIELD_IDS, assemble_chair_fields
from .pack2_fields import PACK2_FIELD_IDS, assemble_pack2_fields
from .pack3_fields import PACK3_FIELD_IDS, assemble_pack3_fields
from .pack4_fields import PACK4_FIELD_IDS, assemble_pack4_fields
from .pack5_fields import PACK5_FIELD_IDS, assemble_pack5_fields
from .pack6_fields import PACK6_FIELD_IDS, assemble_pack6_fields
from .family import family_class_for
from .gold_state import assemble_gold_state_v0
from .occupancy import occupancy_at
from .sleeve_from_tape import features_from_books

SCHEMA = "gtos.judgment.aplus_sleeve.v0"
ORIGIN = "aplus_research"
SLEEVE_KIND = "aplus_v0"
FAMILY_CLASS = "a_plus_study"
SLEEVE_PREFIX = "aplus_"

GEOMETRY_KEYS = (
    "entry",
    "stop",
    "target",
    "stop_dist",
    "target_dist",
    "plan_r",
    "stop_atr",
    "target_atr",
    "order_type",
    "atr14",
)

SESSIONS = frozenset({"asia", "tokyo", "london", "ny", "either"})
SIDES = frozenset({"long", "short", "either"})

# Research stubs — geometry keys are the contract, not live stops.
# Occupancy KEEP-one / 2-stop COUNT stay envelope integers.
CATALOG: dict[str, dict[str, Any]] = {
    "xau_london_ob_retest": {
        "setup_id": "xau_london_ob_retest",
        "symbol": "XAUUSD",
        "side": "either",
        "session": "london",
        "family": "ob_retest",
        "geometry_defaults": {
            "stop_atr": 1.5,
            "target_atr": 3.0,
            "plan_r": 2.0,
            "order_type": "MARKET",
        },
        "occupancy_hooks": {
            "cluster": "metals",
            "keep_one_symbol": True,
            "isolated_reentry_minutes": 15.0,
        },
        "peer_ca_hooks": {
            "peers": ("USDJPY",),
            "ca_role": "xau_usd_peer",
            "dxy_hook": "named_only",
            "funding_hook": "named_only",
        },
    },
    "gbpjpy_london_session_sweep": {
        "setup_id": "gbpjpy_london_session_sweep",
        "symbol": "GBPJPY",
        "side": "either",
        "session": "london",
        "family": "session_sweep",
        "geometry_defaults": {
            "stop_atr": 1.5,
            "target_atr": 3.0,
            "plan_r": 2.0,
            "order_type": "MARKET",
        },
        "occupancy_hooks": {
            "cluster": "jpy",
            "keep_one_symbol": True,
            "isolated_reentry_minutes": 15.0,
        },
        "peer_ca_hooks": {
            "peers": ("USDJPY", "EURJPY"),
            "ca_role": "jpy_cross",
            "dxy_hook": "named_only",
            "funding_hook": "named_only",
        },
    },
    "eurusd_ny_ob_retest": {
        "setup_id": "eurusd_ny_ob_retest",
        "symbol": "EURUSD",
        "side": "either",
        "session": "ny",
        "family": "ob_retest",
        "geometry_defaults": {
            "stop_atr": 1.2,
            "target_atr": 2.4,
            "plan_r": 2.0,
            "order_type": "MARKET",
        },
        "occupancy_hooks": {
            "cluster": "fx_major",
            "keep_one_symbol": True,
            "isolated_reentry_minutes": 15.0,
        },
        "peer_ca_hooks": {
            "peers": ("GBPUSD", "DXY"),
            "ca_role": "fx_major_dxy",
            "dxy_hook": "named_only",
            "funding_hook": "named_only",
        },
    },
    "usdjpy_tokyo_asia_fade": {
        "setup_id": "usdjpy_tokyo_asia_fade",
        "symbol": "USDJPY",
        "side": "either",
        "session": "tokyo",
        "family": "asia_fade",
        "geometry_defaults": {
            "stop_atr": 1.2,
            "target_atr": 2.4,
            "plan_r": 2.0,
            "order_type": "MARKET",
        },
        "occupancy_hooks": {
            "cluster": "jpy",
            "keep_one_symbol": True,
            "isolated_reentry_minutes": 15.0,
        },
        "peer_ca_hooks": {
            "peers": ("XAUUSD", "GBPJPY"),
            "ca_role": "usd_jpy_peer",
            "dxy_hook": "named_only",
            "funding_hook": "named_only",
        },
    },
    "xau_dsp_shakeout": {
        "setup_id": "xau_dsp_shakeout",
        "symbol": "XAUUSD",
        "side": "either",
        "session": "either",
        "family": "dsp_shakeout",
        "geometry_defaults": {
            "stop_atr": 1.5,
            "target_atr": 3.0,
            "plan_r": 2.0,
            "order_type": "MARKET",
        },
        "occupancy_hooks": {
            "cluster": "metals",
            "keep_one_symbol": True,
            "isolated_reentry_minutes": 15.0,
        },
        "peer_ca_hooks": {
            "peers": ("USDJPY",),
            "ca_role": "xau_usd_peer",
            "dxy_hook": "named_only",
            "funding_hook": "named_only",
        },
    },
}

REQUIRED_STUB_SYMBOLS = ("XAUUSD", "GBPJPY", "EURUSD")


@dataclass(frozen=True)
class APlusSleeveV0:
    setup_id: str
    symbol: str
    side: str
    session: str
    family: str
    geometry_defaults: dict[str, Any] = field(default_factory=dict)
    occupancy_hooks: dict[str, Any] = field(default_factory=dict)
    peer_ca_hooks: dict[str, Any] = field(default_factory=dict)

    @property
    def sleeve(self) -> str:
        return sleeve_name(self.setup_id)

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "setup_id": self.setup_id,
            "sleeve": self.sleeve,
            "symbol": self.symbol,
            "side": self.side,
            "session": self.session,
            "family": self.family,
            "geometry_keys": list(GEOMETRY_KEYS),
            "geometry_defaults": dict(self.geometry_defaults),
            "occupancy_hooks": dict(self.occupancy_hooks),
            "peer_ca_hooks": {
                **dict(self.peer_ca_hooks),
                "peers": tuple(self.peer_ca_hooks.get("peers") or ()),
            },
            "origin_organism": ORIGIN,
            "sleeve_kind": SLEEVE_KIND,
            "never_place": True,
            "never_apply_size": True,
            "shadow_only": True,
        }


def sleeve_name(setup_id: str) -> str:
    raw = str(setup_id or "").strip().lower()
    if raw.startswith(SLEEVE_PREFIX):
        return raw
    return f"{SLEEVE_PREFIX}{raw}"


def is_aplus_sleeve(value: Any) -> bool:
    if isinstance(value, APlusSleeveV0):
        return True
    if isinstance(value, Mapping):
        identity = value.get("identity") if isinstance(value.get("identity"), Mapping) else value
        if identity.get("sleeve_kind") == SLEEVE_KIND:
            return True
        if identity.get("origin_organism") == ORIGIN:
            return True
        if str(identity.get("sleeve") or "").startswith(SLEEVE_PREFIX):
            return True
        if value.get("aplus_shadow_only") is True:
            return True
        aplus = value.get("aplus")
        if isinstance(aplus, Mapping) and aplus.get("setup_id"):
            return True
        if value.get("setup_id") and (
            value.get("schema") == SCHEMA or str(value.get("sleeve") or "").startswith(SLEEVE_PREFIX)
        ):
            return True
        return False
    text = str(value or "").strip().lower()
    return text.startswith(SLEEVE_PREFIX) or text == ORIGIN


def is_aplus_shadow_only(
    state: Mapping[str, Any] | None = None,
    *,
    compose_row: Mapping[str, Any] | None = None,
    sleeve: Any = None,
) -> bool:
    """True when size APPLY / haircut must stay off."""
    if compose_row and compose_row.get("aplus_shadow_only"):
        return True
    if sleeve is not None and is_aplus_sleeve(sleeve):
        return True
    if state is not None and is_aplus_sleeve(state):
        return True
    return False


def spec_completeness(spec: APlusSleeveV0 | Mapping[str, Any]) -> dict[str, Any]:
    packed = spec.as_dict() if isinstance(spec, APlusSleeveV0) else dict(spec)
    missing: list[str] = []
    setup_id = str(packed.get("setup_id") or "").strip()
    symbol = str(packed.get("symbol") or "").strip()
    session = str(packed.get("session") or "").strip()
    side = str(packed.get("side") or "").strip()
    family = str(packed.get("family") or "").strip()
    if not setup_id:
        missing.append("setup_id")
    if not symbol:
        missing.append("symbol")
    if session not in SESSIONS:
        missing.append("session")
    if side not in SIDES:
        missing.append("side")
    if not family:
        missing.append("family")
    geo = packed.get("geometry_defaults") or {}
    for key in ("stop_atr", "target_atr", "plan_r", "order_type"):
        if geo.get(key) is None:
            missing.append(f"geometry.{key}")
    occ = packed.get("occupancy_hooks") or {}
    if not occ.get("cluster"):
        missing.append("occupancy_hooks.cluster")
    peers = packed.get("peer_ca_hooks") or {}
    if not peers.get("peers"):
        missing.append("peer_ca_hooks.peers")
    if not peers.get("ca_role"):
        missing.append("peer_ca_hooks.ca_role")
    return {
        "schema": SCHEMA,
        "setup_id": setup_id or None,
        "symbol": symbol or None,
        "spec_complete": not missing,
        "missing_fields": missing,
        "geometry_keys": list(GEOMETRY_KEYS),
        "peers_assembled": False,
        "invented_peers": False,
        "shadow_only": True,
    }


def from_catalog(setup_id: str) -> APlusSleeveV0:
    row = CATALOG.get(setup_id) or CATALOG.get(str(setup_id).removeprefix(SLEEVE_PREFIX))
    if row is None:
        raise KeyError(setup_id)
    return APlusSleeveV0(
        setup_id=str(row["setup_id"]),
        symbol=normalize_symbol(str(row["symbol"])),
        side=str(row["side"]),
        session=str(row["session"]),
        family=str(row["family"]),
        geometry_defaults=dict(row.get("geometry_defaults") or {}),
        occupancy_hooks=dict(row.get("occupancy_hooks") or {}),
        peer_ca_hooks=dict(row.get("peer_ca_hooks") or {}),
    )


def catalog_sleeves(*, require_symbols: Sequence[str] = REQUIRED_STUB_SYMBOLS) -> list[APlusSleeveV0]:
    sleeves = [from_catalog(setup_id) for setup_id in CATALOG]
    have = {s.symbol for s in sleeves}
    missing = [s for s in require_symbols if normalize_symbol(s) not in have]
    if missing:
        raise RuntimeError(f"APlus catalog missing required symbols: {missing}")
    return sleeves


def geometry_from_sleeve(
    spec: APlusSleeveV0,
    candidate: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    geo = {key: None for key in GEOMETRY_KEYS}
    geo.update({k: v for k, v in spec.geometry_defaults.items() if k in GEOMETRY_KEYS})
    cand = dict(candidate or {})
    for key in GEOMETRY_KEYS:
        if cand.get(key) is not None:
            geo[key] = cand[key]
    if geo.get("stop_dist") is None:
        try:
            entry = float(geo["entry"]) if geo.get("entry") is not None else None
            stop = float(geo["stop"]) if geo.get("stop") is not None else None
        except (TypeError, ValueError):
            entry = stop = None
        if entry is not None and stop is not None:
            geo["stop_dist"] = abs(entry - stop)
    if geo.get("target_dist") is None:
        try:
            entry = float(geo["entry"]) if geo.get("entry") is not None else None
            target = float(geo["target"]) if geo.get("target") is not None else None
        except (TypeError, ValueError):
            entry = target = None
        if entry is not None and target is not None:
            geo["target_dist"] = abs(target - entry)
    if geo.get("plan_r") is None and geo.get("stop_dist") and geo.get("target_dist"):
        den = float(geo["stop_dist"])
        if den > 0:
            geo["plan_r"] = float(geo["target_dist"]) / den
    geo["order_type"] = geo.get("order_type") or "MARKET"
    return geo


def occupancy_from_hooks(
    spec: APlusSleeveV0,
    *,
    deal_tape=None,
    as_of_utc: datetime | None = None,
    this_ticket: Any = None,
) -> dict[str, Any]:
    hooks = spec.occupancy_hooks
    base = {
        "cluster_named": hooks.get("cluster"),
        "keep_one_symbol": hooks.get("keep_one_symbol"),
        "isolated_reentry_minutes": hooks.get("isolated_reentry_minutes"),
        "occupancy_source": "aplus_hooks_unassembled" if deal_tape is None else "aplus_hooks+deal_tape",
        "symbol_open": None,
        "symbol_pending": None,
        "already_placed_today": None,
        "cluster_placed_today": None,
        "isolated_reentry_legal": None,
        "minutes_since_flat": None,
        "corr_hold_named": None,
    }
    if deal_tape is None or as_of_utc is None:
        return base
    live = occupancy_at(
        deal_tape,
        symbol=spec.symbol,
        as_of_utc=as_of_utc,
        this_ticket=this_ticket,
    )
    out = {**base, **live}
    out["cluster_named"] = hooks.get("cluster")
    out["keep_one_symbol"] = hooks.get("keep_one_symbol")
    out["isolated_reentry_minutes"] = hooks.get("isolated_reentry_minutes")
    out["occupancy_source"] = "aplus_hooks+deal_tape"
    return out


def peer_ca_block(spec: APlusSleeveV0, *, peer_state: Mapping[str, Any] | None = None) -> dict[str, Any]:
    hooks = spec.peer_ca_hooks
    assembled = bool(peer_state)
    return {
        "peers": list(hooks.get("peers") or ()),
        "ca_role": hooks.get("ca_role"),
        "dxy_hook": hooks.get("dxy_hook") or "named_only",
        "funding_hook": hooks.get("funding_hook") or "named_only",
        "peer_state": dict(peer_state) if assembled else None,
        "source": "symbol_state_v0" if assembled else "aplus_peer_ca_hooks",
        "invented": False,
        "assembled": assembled,
    }


def aplus_block(spec: APlusSleeveV0) -> dict[str, Any]:
    complete = spec_completeness(spec)
    return {
        "schema": SCHEMA,
        "setup_id": spec.setup_id,
        "sleeve": spec.sleeve,
        "session": spec.session,
        "family": spec.family,
        "geometry_keys": list(GEOMETRY_KEYS),
        "occupancy_hooks": dict(spec.occupancy_hooks),
        "peer_ca_hooks": {
            "peers": list(spec.peer_ca_hooks.get("peers") or ()),
            "ca_role": spec.peer_ca_hooks.get("ca_role"),
            "dxy_hook": spec.peer_ca_hooks.get("dxy_hook") or "named_only",
            "funding_hook": spec.peer_ca_hooks.get("funding_hook") or "named_only",
        },
        "spec_complete": complete["spec_complete"],
        "chair_field_ids": list(CHAIR_FIELD_IDS),
        "pack2_field_ids": list(PACK2_FIELD_IDS),
        "pack3_field_ids": list(PACK3_FIELD_IDS),
        "pack4_field_ids": list(PACK4_FIELD_IDS),
        "pack5_field_ids": list(PACK5_FIELD_IDS),
        "pack6_field_ids": list(PACK6_FIELD_IDS),
        "source": "aplus_sleeve_v0",
        "shadow_only": True,
        "never_apply_size": True,
    }


def assemble_aplus_state(
    spec: APlusSleeveV0 | str,
    *,
    as_of_utc: datetime,
    side: str | None = None,
    candidate_id: str | None = None,
    as_of_clock: str = "as_of_open_study",
    books: Mapping[str, Sequence[StampedBar]] | None = None,
    geometry: Mapping[str, Any] | None = None,
    cost: Mapping[str, Any] | None = None,
    deal_tape=None,
    occupancy: Mapping[str, Any] | None = None,
    peer_state: Mapping[str, Any] | None = None,
    spines: dict[str, Any] | None = None,
    sleeve_features: Mapping[str, Any] | None = None,
    extra: Mapping[str, Any] | None = None,
    chair_values: Mapping[str, Any] | None = None,
    pack2_values: Mapping[str, Any] | None = None,
    pack3_values: Mapping[str, Any] | None = None,
    pack4_values: Mapping[str, Any] | None = None,
    pack5_values: Mapping[str, Any] | None = None,
    pack6_values: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Closed gold_state.v0 with A+ sleeve identity. Missing tape stays visible."""
    sleeve = from_catalog(spec) if isinstance(spec, str) else spec
    as_of = as_of_utc if as_of_utc.tzinfo else as_of_utc.replace(tzinfo=timezone.utc)
    as_of = as_of.astimezone(timezone.utc)
    chosen_side = side if side and side != "either" else (sleeve.side if sleeve.side != "either" else "unknown")
    geo = geometry_from_sleeve(sleeve, geometry)
    occ = dict(occupancy_from_hooks(sleeve, deal_tape=deal_tape, as_of_utc=as_of, this_ticket=candidate_id))
    if occupancy:
        occ.update(occupancy)
    feats = dict(sleeve_features or {})
    if books and not feats:
        feats = features_from_books(books, as_of, tag=sleeve.sleeve, cluster=sleeve.occupancy_hooks.get("cluster"))
    feats.setdefault("tag", sleeve.sleeve)
    feats.setdefault("cluster", sleeve.occupancy_hooks.get("cluster"))
    feats.setdefault("session", sleeve.session)
    feats.setdefault("setup_id", sleeve.setup_id)
    extra_block = {
        "setup_id": sleeve.setup_id,
        "sleeve_kind": SLEEVE_KIND,
        **dict(extra or {}),
    }
    from .gold_state import _session_named
    from .news_spine import attach_news, load_spines

    weekday = as_of.weekday()
    session_named = _session_named(as_of.hour, weekday == 4)
    chair = assemble_chair_fields(
        symbol=sleeve.symbol,
        as_of_utc=as_of,
        session_named=session_named,
        peer_state=peer_state,
        chair_values=chair_values,
        m15_vol=geo.get("atr14"),
    )
    news_for_pack2 = attach_news(
        as_of,
        spines=spines if spines is not None else load_spines(),
        symbol=sleeve.symbol,
    )
    pack2 = assemble_pack2_fields(
        symbol=sleeve.symbol,
        as_of_utc=as_of,
        session_named=session_named,
        peer_state=peer_state,
        pack2_values=pack2_values,
        news=news_for_pack2,
    )
    pack3 = assemble_pack3_fields(
        symbol=sleeve.symbol,
        time_utc=as_of,
        peer_state=peer_state,
        pack3_values=pack3_values,
        news=news_for_pack2,
        m15_vol=geo.get("atr14"),
    )
    pack4 = assemble_pack4_fields(
        symbol=sleeve.symbol,
        setup_id=sleeve.setup_id,
        pack3=pack3,
        pack4_values=pack4_values,
        session_named=session_named,
    )
    pack5 = assemble_pack5_fields(
        symbol=sleeve.symbol,
        setup_id=sleeve.setup_id,
        pack2=pack2,
        pack3=pack3,
        pack4=pack4,
        pack5_values=pack5_values,
        session_named=session_named,
    )
    pack6 = assemble_pack6_fields(
        symbol=sleeve.symbol,
        setup_id=sleeve.setup_id,
        pack6_values=pack6_values,
    )
    aplus = aplus_block(sleeve)
    aplus["chair_fields"] = chair
    aplus["pack2_fields"] = pack2
    aplus["pack3_fields"] = pack3
    aplus["pack4_fields"] = pack4
    aplus["pack5_fields"] = pack5
    aplus["pack6_fields"] = pack6
    state = assemble_gold_state_v0(
        as_of_utc=as_of,
        side=chosen_side,
        sleeve=sleeve.sleeve,
        symbol=sleeve.symbol,
        candidate_id=candidate_id,
        origin_organism=ORIGIN,
        as_of_clock=as_of_clock,
        extra=extra_block,
        books=books,
        spines=spines,
        geometry=geo,
        cost=cost,
        occupancy=occ,
        sleeve_features=feats,
        aplus=aplus,
        peers=peer_ca_block(sleeve, peer_state=peer_state),
        chair_fields=chair,
        pack2_fields=pack2,
        pack3_fields=pack3,
        pack4_fields=pack4,
        pack5_fields=pack5,
        pack6_fields=pack6,
        surface={"aplus_shadow_only": True, "never_apply_size": True},
    )
    return state


def score_aplus_shadow(
    spec: APlusSleeveV0 | str,
    *,
    as_of_utc: datetime,
    side: str | None = None,
    candidate_id: str | None = None,
    books=None,
    geometry: Mapping[str, Any] | None = None,
    cost: Mapping[str, Any] | None = None,
    deal_tape=None,
    spines=None,
    answers: Mapping[str, Any] | None = None,
    ticket: Any = None,
    peer_state: Mapping[str, Any] | None = None,
    chair_values: Mapping[str, Any] | None = None,
    pack2_values: Mapping[str, Any] | None = None,
    pack3_values: Mapping[str, Any] | None = None,
    pack4_values: Mapping[str, Any] | None = None,
    pack5_values: Mapping[str, Any] | None = None,
    pack6_values: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Shadow pack for one A+ sleeve. Compose rides the 48 fluid gates. Never applies."""
    from .compose import compose_shadow

    sleeve = from_catalog(spec) if isinstance(spec, str) else spec
    state = assemble_aplus_state(
        sleeve,
        as_of_utc=as_of_utc,
        side=side,
        candidate_id=candidate_id or ticket,
        books=books,
        geometry=geometry,
        cost=cost,
        deal_tape=deal_tape,
        spines=spines,
        peer_state=peer_state,
        chair_values=chair_values,
        pack2_values=pack2_values,
        pack3_values=pack3_values,
        pack4_values=pack4_values,
        pack5_values=pack5_values,
        pack6_values=pack6_values,
    )
    composed = compose_shadow(
        state,
        dict(answers or {}),
        ticket=ticket or candidate_id,
        extra={"kind": "aplus_shadow", "setup_id": sleeve.setup_id},
    )
    return {
        "schema": "gtos.judgment.aplus_shadow.v0",
        "setup_id": sleeve.setup_id,
        "sleeve": sleeve.sleeve,
        "symbol": sleeve.symbol,
        "family_class": family_class_for(sleeve.sleeve, symbol=sleeve.symbol, origin=ORIGIN),
        "state": state,
        "compose": composed,
        "never_place": True,
        "never_remint": True,
        "never_flatten": True,
        "never_apply_size": True,
        "shadow_only": True,
        "apply_this_row": False,
        "missing_state": list(state["completeness"]["missing_fields"]),
    }
