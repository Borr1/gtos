"""assemble_symbol_state_v0 — per-symbol typed state sibling to gold_state.

Default-off research / SHADOW observe. Never place / remint / flatten.
Never invent NEWS_PROTOCOL, DXY, or yields.

Non-XAU primaries get a real closed object (same completeness + missing_fields
contract as gold_state). Peers are class-aware. ``not_xau_primary`` is not a
dead end — it is rewritten to unassembled/challenge_csv on the named peer set.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from .bars import StampedBar, last_closed_at_or_before, normalize_symbol, tf_snap
from .chair_wires import apply_pack4_fold, assemble_chair_wires
from .gold_state import SCHEMA as SCHEMA_GOLD
from .gold_state import assemble_gold_state_v0, reject_expost
from .news_spine import attach_news, load_spines
from .a_plus_sleeve import attach_sleeve_object, gate_flow_block
from .symbol_class import (
    UNIVERSAL_BLOCKS,
    asset_class_for,
    cash_alias,
    news_currencies_for,
    peer_symbols_for,
    pip_scale,
    session_bias,
    split_pair,
    usd_from_pair_trend,
    usd_leg,
)

SCHEMA = "gtos.judgment.symbol_state.v0"
SIBLING_OF = "gtos.judgment.gold_state.v0"
NEVER = {
    "never_place": True,
    "never_remint": True,
    "never_flatten": True,
    "never_invent_news_protocol": True,
    "never_invent_dxy": True,
    "never_invent_tips": True,
    "never_apply_size_on_non_xau": True,
}

PEER_WIRE_KEYS = frozenset(
    {
        "usd_proxy_vs_xau",
        "gbpjpy_dual_leg_agree",
        "corr",
        "xau_eur_proxy",
    }
)


def _as_of(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _pearson(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    n = float(len(xs))
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = sum((x - mx) ** 2 for x in xs)
    dy = sum((y - my) ** 2 for y in ys)
    den = math.sqrt(dx * dy)
    if den == 0.0 or not math.isfinite(den):
        return None
    value = num / den
    return value if math.isfinite(value) else None


def _simple_returns(closes: Sequence[float]) -> list[float] | None:
    out: list[float] = []
    for prev, nxt in zip(closes, closes[1:]):
        if prev == 0:
            return None
        out.append((nxt - prev) / prev)
    return out


def aligned_closes(
    primary: Sequence[StampedBar] | None,
    peer: Sequence[StampedBar] | None,
    as_of_utc: datetime,
    n_closes: int,
) -> tuple[list[float], list[float]] | None:
    if not primary or not peer or n_closes < 2:
        return None
    as_of = _as_of(as_of_utc)
    ia = last_closed_at_or_before(list(primary), as_of)
    ib = last_closed_at_or_before(list(peer), as_of)
    if ia is None or ib is None:
        return None
    peer_by_utc = {row.utc: row.bar.c for row in peer[: ib + 1]}
    xs: list[float] = []
    ys: list[float] = []
    for row in primary[: ia + 1]:
        other = peer_by_utc.get(row.utc)
        if other is None:
            continue
        xs.append(row.bar.c)
        ys.append(other)
    if len(xs) < n_closes:
        return None
    return xs[-n_closes:], ys[-n_closes:]


def comove_20(
    primary_m15: Sequence[StampedBar] | None,
    peer_m15: Sequence[StampedBar] | None,
    as_of_utc: datetime,
) -> float | None:
    packed = aligned_closes(primary_m15, peer_m15, as_of_utc, 21)
    if packed is None:
        return None
    rx = _simple_returns(packed[0])
    ry = _simple_returns(packed[1])
    if rx is None or ry is None or len(rx) != 20:
        return None
    return _pearson(rx, ry)


def _empty_peer(*, source: str = "unassembled") -> dict[str, Any]:
    return {
        "present": False,
        "m15_atr14": None,
        "h4_trend": None,
        "comove_20": None,
        "atr_ratio": None,
        "source": source,
    }


def _peer_books_lookup(
    peer_books: Mapping[str, Any] | None,
    peer: str,
) -> Mapping[str, Any] | None:
    if not peer_books:
        return None
    return peer_books.get(peer) or peer_books.get(peer.lower())


def assemble_symbol_peers(
    *,
    symbol: str,
    as_of_utc: datetime,
    books: Mapping[str, list[StampedBar]] | None = None,
    peer_books: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Class-aware peers. Never emit ``not_xau_primary`` as a dead end."""
    primary = normalize_symbol(symbol)
    as_of = _as_of(as_of_utc)
    primary_m15 = (books or {}).get("m15") or []
    primary_snap = tf_snap(primary_m15, as_of, "M15") if primary_m15 else None
    primary_atr = (primary_snap or {}).get("atr14") if primary_snap else None

    # If PR #15 peers.py is present, lift USDJPY for XAU then rewrite dead ends.
    lifted: dict[str, Any] = {}
    try:
        from .peers import assemble_peers_block

        raw = assemble_peers_block(
            symbol=primary,
            as_of_utc=as_of,
            books=books,
            peer_books=peer_books,
        )
        usdjpy = (raw or {}).get("usdjpy") if isinstance(raw, dict) else None
        if isinstance(usdjpy, dict) and usdjpy.get("source") != "not_xau_primary":
            lifted["USDJPY"] = {
                "present": bool(usdjpy.get("present")),
                "m15_atr14": usdjpy.get("m15_atr14"),
                "h4_trend": usdjpy.get("h4_trend"),
                "comove_20": usdjpy.get("xau_usdjpy_comove_20"),
                "atr_ratio": usdjpy.get("atr_ratio"),
                "source": usdjpy.get("source") or "unassembled",
            }
            if primary == "XAUUSD":
                lifted["USDJPY"]["xau_usdjpy_comove_20"] = usdjpy.get("xau_usdjpy_comove_20")
    except Exception:
        lifted = {}

    out: dict[str, Any] = {}
    for peer in peer_symbols_for(primary):
        if peer in lifted:
            out[peer] = lifted[peer]
            continue
        block = _peer_books_lookup(peer_books, peer)
        if not block:
            out[peer] = _empty_peer(source="unassembled")
            continue
        m15_rows = block.get("m15") or []
        h4_rows = block.get("h4") or []
        m15 = tf_snap(m15_rows, as_of, "M15") if m15_rows else None
        h4 = tf_snap(h4_rows, as_of, "H4", lookback=30) if h4_rows else None
        if not m15 and not h4:
            out[peer] = _empty_peer(source="unassembled")
            continue
        peer_atr = (m15 or {}).get("atr14") if m15 else None
        atr_ratio = None
        if primary_atr and peer_atr and peer_atr > 0:
            atr_ratio = primary_atr / peer_atr
        row = {
            "present": True,
            "m15_atr14": peer_atr,
            "h4_trend": (h4 or {}).get("trend") if h4 else None,
            "comove_20": comove_20(primary_m15, m15_rows, as_of),
            "atr_ratio": atr_ratio,
            "source": "challenge_csv",
        }
        if primary == "XAUUSD" and peer == "USDJPY":
            row["xau_usdjpy_comove_20"] = row["comove_20"]
        out[peer] = row
    return out


def _pair_news(news: Mapping[str, Any], symbol: str) -> dict[str, Any]:
    """Filter the existing spine by pair currencies. Do not invent events."""
    packed = dict(news)
    ccys = news_currencies_for(symbol)
    events = list(packed.get("events") or [])
    pair_high = [e for e in events if (e.get("currency") or "") in ccys]
    packed["relevant_currencies"] = list(ccys)
    packed["pair_high_events"] = pair_high
    if packed.get("spine_empty"):
        packed["pair_high_in_f5_window"] = None
    else:
        packed["pair_high_in_f5_window"] = any(
            -60 <= int(e.get("minutes_from_as_of") or 9999) <= 15 for e in pair_high
        )
    packed["pair_high_n"] = len(pair_high)
    return packed


def _class_specific(
    *,
    symbol: str,
    gold: Mapping[str, Any],
    peers: Mapping[str, Any],
) -> dict[str, Any]:
    asset = asset_class_for(symbol)
    if asset is None:
        return {
            "asset_class": None,
            "assembled": False,
            "source": "class_not_decided",
        }
    named = ((gold.get("sessions") or {}).get("named"))
    trend = ((gold.get("timeframes") or {}).get("h4") or {}).get("trend")
    feats = gold.get("sleeve_features") or {}
    base, quote = split_pair(symbol)
    block: dict[str, Any] = {
        "asset_class": asset,
        "assembled": True,
        "source": "symbol_class_v0",
    }
    if asset == "fx":
        block["fx"] = {
            "pair": {"base": base, "quote": quote},
            "usd_leg": usd_leg(symbol),
            "usd_from_pair": usd_from_pair_trend(symbol, trend),
            "session_bias": session_bias(symbol, named),
            "pip_scale": pip_scale(symbol),
            "relevant_news_ccys": list(news_currencies_for(symbol)),
        }
    elif asset == "metal":
        block["metal"] = {
            "usd_sensitivity": "usd_proxy_only",
            "a8_source": feats.get("a8_source") or "unassembled",
            "ac60": feats.get("ac60"),
            "vol_ratio": feats.get("vol_ratio"),
            "peer_usdjpy_present": bool((peers.get("USDJPY") or {}).get("present")),
        }
    elif asset == "index":
        block["index"] = {
            "cash_alias": cash_alias(symbol),
            "house_us30_off": True,
            "session_bias": session_bias(symbol, named),
        }
    elif asset == "crypto":
        block["crypto"] = {"trade_surface": "house_hard_off_not_a_fire"}
    elif asset == "energy":
        block["energy"] = {"weekend": "energy"}
    else:
        block["assembled"] = False
        block["source"] = "unknown_symbol"
    return block


def _maybe_world(
    *,
    as_of: datetime,
    as_of_clock: str,
    gold: Mapping[str, Any],
    books: Mapping[str, list[StampedBar]] | None,
    peer_books: Mapping[str, Any] | None,
    spines: dict[str, Any] | None,
    deal_tape: Any,
) -> dict[str, Any]:
    """Reuse WORLD_STATE_V0 / CA features when those modules are on the tree."""
    symbol = normalize_symbol((gold.get("identity") or {}).get("symbol"))
    gold_books = books if symbol == "XAUUSD" else None
    try:
        from .cross_asset import assemble_cross_asset_v0

        return assemble_cross_asset_v0(
            as_of_utc=as_of,
            gold=gold,
            gold_books=gold_books,
            peer_books=peer_books,
            spines=spines,
        )
    except Exception:
        pass
    try:
        from .world_state import assemble_world_state_v0

        return assemble_world_state_v0(
            as_of_utc=as_of,
            as_of_clock=as_of_clock,
            gold=gold,
            gold_books=gold_books,
            cross_books=peer_books,
            trades=deal_tape,
            spines=spines,
        )
    except Exception:
        return {
            "schema": "gtos.judgment.world_state.v0",
            "source": "unassembled",
            "reason": "world_state_module_absent_on_this_branch",
            "dxy": None,
            "rates": None,
            "never_invent_dxy": True,
            "never_invent_yield": True,
        }


def assemble_symbol_state_v0(
    *,
    as_of_utc: datetime,
    side: str,
    sleeve: str,
    symbol: str,
    candidate_id: str | None = None,
    origin_organism: str = "historical_lab",
    as_of_clock: str = "as_of_open_study",
    extra: Mapping[str, Any] | None = None,
    books: Mapping[str, list[StampedBar]] | None = None,
    spines: dict[str, Any] | None = None,
    geometry: Mapping[str, Any] | None = None,
    cost: Mapping[str, Any] | None = None,
    occupancy: Mapping[str, Any] | None = None,
    governor: Mapping[str, Any] | None = None,
    sleeve_features: Mapping[str, Any] | None = None,
    surface: Mapping[str, Any] | None = None,
    forbid_expost: Mapping[str, Any] | None = None,
    peer_books: Mapping[str, Any] | None = None,
    world: Mapping[str, Any] | None = None,
    deal_tape: Any = None,
) -> dict[str, Any]:
    """Build one closed symbol_state.v0 object. Missing blocks stay visible."""
    extra = extra or {}
    leaked = reject_expost(forbid_expost or extra, as_of_clock)
    if leaked and as_of_clock == "live_intent":
        raise ValueError(f"EXPOST keys illegal on live_intent: {leaked}")

    raw_symbol = (symbol or "").strip()
    # Empty stays empty. Do not wear XAUUSD via normalize_symbol(None/"").
    sym = normalize_symbol(raw_symbol) if raw_symbol else ""
    gold = assemble_gold_state_v0(
        as_of_utc=as_of_utc,
        side=side,
        sleeve=sleeve,
        symbol=sym,
        candidate_id=candidate_id,
        origin_organism=origin_organism,
        as_of_clock=as_of_clock,
        extra=extra,
        books=books,
        spines=spines if spines is not None else load_spines(),
        geometry=geometry,
        cost=cost,
        occupancy=occupancy,
        governor=governor,
        sleeve_features=sleeve_features,
        surface=surface,
        forbid_expost=forbid_expost,
        peer_books=peer_books,
    )
    as_of = _as_of(as_of_utc)
    news = _pair_news(gold.get("news") or attach_news(as_of, spines=spines, symbol=sym), sym)
    peers = assemble_symbol_peers(
        symbol=sym,
        as_of_utc=as_of,
        books=books,
        peer_books=peer_books,
    )
    asset = asset_class_for(sym)
    class_block = _class_specific(symbol=sym, gold=gold, peers=peers)
    world_block = dict(world) if world is not None else _maybe_world(
        as_of=as_of,
        as_of_clock=as_of_clock,
        gold=gold,
        books=books,
        peer_books=peer_books,
        spines=spines,
        deal_tape=deal_tape,
    )

    identity = dict(gold.get("identity") or {})
    base, quote = split_pair(sym)
    identity["asset_class"] = asset
    identity["base"] = base
    identity["quote"] = quote
    chair = assemble_chair_wires(
        symbol=sym,
        as_of_utc=as_of,
        gold=gold,
        peers=peers,
        news=news,
        books=books,
        peer_books=peer_books,
    )
    fold = chair.get("fold") or {}
    class_fold = (fold.get("class_specific") or {}).get(asset) or {}
    class_inner = class_block.get(asset)
    if isinstance(class_inner, dict) and class_fold:
        class_inner.update(class_fold)
    sleeve_block = attach_sleeve_object(
        symbol=sym,
        sleeve=str(identity.get("sleeve") or sleeve),
        family_class=identity.get("family_class"),
        origin_organism=str(identity.get("origin_organism") or origin_organism),
        world=world_block,
    )
    ca = sleeve_block.get("ca_labels")
    if isinstance(ca, dict):
        labels = dict(ca.get("labels") or {})
        labels.update(fold.get("sleeve_labels") or {})
        ca["labels"] = labels
        ca["never_invent_dxy"] = True
        ca["never_invent_tips"] = True
        ca["chair_wires_apply"] = False
        ca["never_admit_choice"] = True
    flow = gate_flow_block(
        a_plus=bool(sleeve_block.get("a_plus")),
        observe_only=bool(sleeve_block.get("observe_only")),
    )

    surface_block = dict(gold.get("surface") or {})
    xau = sym == "XAUUSD"
    a_plus = bool(sleeve_block.get("a_plus"))
    surface_block["apply_named_wires"] = xau and not a_plus
    surface_block["symbol_state_observe_only"] = (not xau) or a_plus
    surface_block["us30_off"] = True
    if surface:
        surface_block.update(surface)
        surface_block["us30_off"] = True
        surface_block["apply_named_wires"] = xau and not a_plus
        surface_block["symbol_state_observe_only"] = (not xau) or a_plus

    missing = list((gold.get("completeness") or {}).get("missing_fields") or [])
    symbol_peers = {
        key: row
        for key, row in peers.items()
        if key not in PEER_WIRE_KEYS
    }
    if not any((symbol_peers.get(p) or {}).get("present") for p in symbol_peers):
        if "peers" not in missing:
            missing.append("peers")
    if not class_block.get("assembled") and "class_specific" not in missing:
        missing.append("class_specific")
    if not sleeve_block.get("tag") and "sleeve" not in missing:
        missing.append("sleeve")

    completeness = dict(gold.get("completeness") or {})
    completeness["asset_class"] = asset != "unknown"
    completeness["class_specific"] = bool(class_block.get("assembled"))
    completeness["peers"] = any(
        bool((symbol_peers.get(p) or {}).get("present")) for p in symbol_peers
    )
    completeness["chair_wires"] = chair.get("source") == "scout_edge_shadow"
    completeness["news_pair_ccy"] = bool(news.get("relevant_currencies"))
    completeness["world"] = (world_block or {}).get("source") not in {None, "unassembled"}
    completeness["sleeve"] = bool(sleeve_block.get("tag"))
    completeness["gate_flow"] = flow.get("name") == "a_plus_sleeve_on_gate_flow"
    completeness["missing_fields"] = missing
    completeness["expost_rejected"] = leaked
    # Peers / world / chair_wires never flip the live-sufficient predicate (gold contract).
    completeness["state_sufficient_for_live"] = bool(
        (gold.get("completeness") or {}).get("state_sufficient_for_live")
    )

    packed = {
        "schema": SCHEMA,
        "sibling_of": SIBLING_OF,
        "as_of_clock": gold.get("as_of_clock") or as_of_clock,
        **NEVER,
        "identity": identity,
        "clock": dict(gold.get("clock") or {}),
        "sessions": dict(gold.get("sessions") or {}),
        "timeframes": gold.get("timeframes") or {},
        "levels": gold.get("levels"),
        "news": news,
        "sleeve_features": gold.get("sleeve_features"),
        "geometry": gold.get("geometry"),
        "cost": gold.get("cost"),
        "occupancy": gold.get("occupancy"),
        "governor": gold.get("governor"),
        "surface": surface_block,
        "class_specific": class_block,
        "peers": peers,
        "world": world_block,
        "sleeve": sleeve_block,
        "gate_flow": flow,
        "universal_blocks": list(UNIVERSAL_BLOCKS),
        "completeness": completeness,
        "gold_state": gold if xau else None,
    }
    packed = apply_pack4_fold(packed, chair)
    packed["surface"]["apply_named_wires"] = xau and not a_plus
    packed["surface"]["symbol_state_observe_only"] = (not xau) or a_plus
    packed["surface"]["us30_off"] = True
    packed["completeness"]["state_sufficient_for_live"] = bool(
        (gold.get("completeness") or {}).get("state_sufficient_for_live")
    )
    packed["generality"] = build_generality(sym, gold)
    packed["schema"] = SCHEMA
    packed["gold_state"] = gold if xau else packed.get("gold_state")
    if xau:
        # XAU still wraps gold_state.v0. Callers that need the gold body
        # (A+ observe preserve-gold, USDJPY peer tape) use assemble_gold_state_v0.
        packed["schema_gold"] = SCHEMA_GOLD
    return packed


def load_peer_books_for(symbol: str, cache: dict | None = None) -> dict[str, Any]:
    """Named peer set from Challenge CSVs. Never substitutes XAU. Never invents."""
    from .bars import books_for_symbol

    # A single-tf dict is the PRIMARY's M15/H4. Reusing it as a peer cache
    # would wear EURUSD/USDJPY bars as XAU (books_for_symbol XAU shortcut).
    peer_cache = cache
    if cache is not None:
        keys = {str(k).lower() for k in cache}
        if keys & {"m15", "h4", "d1"}:
            peer_cache = None
    out: dict[str, Any] = {}
    for peer in peer_symbols_for(symbol):
        loaded = books_for_symbol(peer, peer_cache)
        if loaded:
            out[peer] = loaded
    return out


SCHEMA_SYMBOL = SCHEMA
XAU_PEER_POLICY = "not_substituted"
MISSING_MACRO_SOURCES = {
    "dxy": {
        "status": "unassembled",
        "reason": "No DXY / dollar-index feed is committed on this tree. Do not invent one.",
    },
    "yields": {
        "status": "unassembled",
        "reason": "No Treasury / UST yield feed is committed on this tree. Do not invent one.",
    },
    "news_protocol": {
        "status": "not_invented",
        "reason": (
            "F5 NEWS_PROTOCOL / official_high_spine is leftover-ship, not on this main. "
            "Empty spine is honesty, not 'no HIGH'."
        ),
    },
}


def currencies_for(symbol: str | None) -> tuple[str, ...]:
    """Named quote currencies. Incomplete map stays empty — never invent DXY."""
    return tuple(news_currencies_for(symbol) or ())


def symbol_class_for(symbol: str | None) -> str:
    raw = asset_class_for(symbol)
    return {"metal": "metals"}.get(raw, raw)


def currency_map_complete(symbol: str | None) -> bool:
    return bool(currencies_for(symbol))


def xau_peer_d1_policy(symbol: str | None) -> dict[str, Any]:
    """XAU D1 is not a parent tape for another symbol."""
    key = normalize_symbol(symbol) if symbol else ""
    own = key in {"", "XAUUSD"}
    return {
        "policy": XAU_PEER_POLICY,
        "symbol": key or None,
        "xau_d1_injected": False,
        "applies_to_this_row": (not own) and bool(key),
        "d1_source": "own_symbol_or_missing",
        "reason": (
            "books_for_symbol never substitutes XAU for another pair. "
            "Missing non-XAU D1 stays missing; it does not wear the gold parent."
        ),
    }


def build_generality(symbol: str | None, body: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Honesty block. Missing sources stay named. No invented feeds."""
    key = normalize_symbol(symbol) if symbol else ""
    tfs = (body or {}).get("timeframes") or {}
    missing = list(((body or {}).get("completeness") or {}).get("missing_fields") or [])
    return {
        "assembler": "symbol_state.v0",
        "gold_body_schema": SCHEMA_GOLD,
        "symbol_class": symbol_class_for(symbol),
        "currencies": list(currencies_for(symbol)),
        "currency_map_complete": currency_map_complete(symbol),
        "xau_peer_d1": xau_peer_d1_policy(symbol),
        "macro": dict(MISSING_MACRO_SOURCES),
        "own_d1_present": bool(tfs.get("d1")),
        "d1_missing_named": "timeframes.d1" in missing,
        "never_place": True,
        "never_remint": True,
        "never_flatten": True,
        "never_invent_news_protocol": True,
        "never_invent_dxy": True,
        "never_invent_yields": True,
        "identity_defaulted_to_xau": False,
    }


def gold_keys_equal(gold: Mapping[str, Any], symbol_state: Mapping[str, Any]) -> list[str]:
    """Return gold keys whose values drifted. Extra symbol_state keys are ignored."""
    drifted: list[str] = []
    for key, value in gold.items():
        if key not in symbol_state:
            drifted.append(key)
            continue
        if symbol_state[key] != value:
            drifted.append(key)
    return drifted
