"""assemble_gold_state_v0 — closed XAUUSD object. Default-off research. No send path.

Per-symbol generalization lives in ``symbol_state.assemble_symbol_state_v0``.
This module stays the gold body. ``assemble_symbol_state_v0`` here remains a
compat alias of the gold assembler. It does not inject XAU D1 into another
pair (see ``symbol_state.xau_peer_d1_policy``). Do not invent DXY / yields /
NEWS_PROTOCOL here.

SHADOW PACK 4 extensions (sessions / cluster / cross / information / peers /
sleeve readiness) fold on after the gold contract. They never APPLY, never
emit admit Choice, and never soften ``us30_off``.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from .bars import StampedBar, last_closed_at_or_before, normalize_symbol, prior_day_levels, tf_snap
from .chair_wires import apply_pack4_fold, assemble_chair_wires
from .family import HARD_OFF_FAMILIES, KEEP_FAMILIES, family_class_for, hard_off_family
from .news_spine import attach_news, load_spines
from .peers import assemble_peers_block

SCHEMA = "gtos.judgment.gold_state.v0"
EXPOST_KEYS = frozenset(
    {
        "broker_net",
        "profit",
        "realized_pnl",
        "exit_class",
        "exit_price",
        "mfe",
        "mae",
        "won",
        "R",
        "close_reason",
    }
)

_WEEKDAY = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def reject_expost(payload: Mapping[str, Any] | None, as_of_clock: str) -> list[str]:
    if as_of_clock == "as_of_close_illegal_for_live":
        return []
    if not payload:
        return []
    return sorted(k for k in EXPOST_KEYS if k in payload and payload[k] is not None)


def _session_named(utc_hour: int | None, is_friday: bool) -> str | None:
    if utc_hour is None:
        return "unknown"
    from .state_choices import LEGACY, session_named_choice

    chosen = session_named_choice(utc_hour, is_friday)
    if chosen is not LEGACY:
        return chosen
    if is_friday and utc_hour >= 16:
        return "friday_cutoff"
    if utc_hour >= 21 or utc_hour == 0:
        return "dead_21_00z"
    if 0 < utc_hour < 7:
        return "asia"
    if 7 <= utc_hour < 12:
        return "london"
    if 12 <= utc_hour < 21:
        return "ny"
    return "unknown"


def assemble_gold_state_v0(
    *,
    as_of_utc: datetime,
    side: str,
    sleeve: str,
    symbol: str = "XAUUSD",
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
    aplus: Mapping[str, Any] | None = None,
    peers: Mapping[str, Any] | None = None,
    chair_fields: Mapping[str, Any] | None = None,
    pack2_fields: Mapping[str, Any] | None = None,
    pack3_fields: Mapping[str, Any] | None = None,
    pack4_fields: Mapping[str, Any] | None = None,
    pack5_fields: Mapping[str, Any] | None = None,
    pack6_fields: Mapping[str, Any] | None = None,
    world: Mapping[str, Any] | None = None,
    deal_tape: Any = None,
) -> dict[str, Any]:
    """Build one closed gold_state.v0 object. Missing blocks stay visible.

    PACK 4 Chair paths fold on as SHADOW extensions. They never flip
    ``state_sufficient_for_live``, never emit admit Choice, never APPLY,
    and never soften ``us30_off``.
    """
    extra = extra or {}
    aplus_block = dict(aplus or extra.get("aplus") or {})
    peers_block = dict(peers or extra.get("peers") or {})
    chair_block = dict(chair_fields or extra.get("chair_fields") or aplus_block.get("chair_fields") or {})
    pack2_block = dict(pack2_fields or extra.get("pack2_fields") or aplus_block.get("pack2_fields") or {})
    pack3_block = dict(pack3_fields or extra.get("pack3_fields") or aplus_block.get("pack3_fields") or {})
    pack4_block = dict(pack4_fields or extra.get("pack4_fields") or aplus_block.get("pack4_fields") or {})
    pack5_block = dict(pack5_fields or extra.get("pack5_fields") or aplus_block.get("pack5_fields") or {})
    pack6_block = dict(pack6_fields or extra.get("pack6_fields") or aplus_block.get("pack6_fields") or {})
    leaked = reject_expost(forbid_expost or extra, as_of_clock)
    if leaked and as_of_clock == "live_intent":
        raise ValueError(f"EXPOST keys illegal on live_intent: {leaked}")

    as_of = as_of_utc if as_of_utc.tzinfo else as_of_utc.replace(tzinfo=timezone.utc)
    as_of = as_of.astimezone(timezone.utc)
    weekday = as_of.weekday()  # Monday=0 — pinned
    broker_hour = None
    utc_hour = as_of.hour
    if books and books.get("m15"):
        idx = last_closed_at_or_before(books["m15"], as_of)
        if idx is not None:
            broker_hour = books["m15"][idx].broker_naive.hour

    m15 = tf_snap(books["m15"], as_of, "M15") if books and books.get("m15") else None
    h4 = tf_snap(books["h4"], as_of, "H4", lookback=30) if books and books.get("h4") else None
    d1 = tf_snap(books["d1"], as_of, "D1", lookback=8) if books and books.get("d1") else None
    pdh, pdl = prior_day_levels(books["d1"], as_of) if books and books.get("d1") else (None, None)

    news = attach_news(as_of, spines=spines if spines is not None else load_spines(), symbol=symbol)
    family = family_class_for(sleeve, symbol=symbol, origin=origin_organism)
    setup_id = extra.get("setup_id") or aplus_block.get("setup_id")
    sleeve_kind = extra.get("sleeve_kind") or (
        "aplus_v0" if aplus_block.get("setup_id") or str(sleeve).startswith("aplus_") else None
    )
    geo = dict(geometry or {})
    cost_block = dict(cost or {})
    occ = dict(occupancy or {})
    gov = dict(governor or {})
    feats = dict(sleeve_features or {})

    timeframes = {}
    if m15:
        timeframes["m15"] = m15
    if h4:
        timeframes["h4"] = h4
    if d1:
        timeframes["d1"] = d1

    missing: list[str] = []
    if not candidate_id:
        candidate_id = f"lab:{symbol}:{as_of.strftime('%Y%m%dT%H%M%S')}:{sleeve}:{side}"
    if not m15:
        missing.append("timeframes.m15")
    if not h4:
        missing.append("timeframes.h4")
    if not d1:
        missing.append("timeframes.d1")
    if pdh is None:
        missing.append("levels.prior_day_high")
    if news["spine_empty"]:
        missing.append("news.events")
    if geo.get("stop_dist") is None and not (geo.get("entry") and geo.get("stop")):
        missing.append("geometry.stop_dist")
    if not feats:
        missing.append("sleeve_features")
    if aplus_block and aplus_block.get("spec_complete") is False:
        missing.append("aplus.spec")
    if aplus_block and peers_block and not peers_block.get("assembled"):
        missing.append("peers.peer_state")
    for field_id in chair_block.get("missing_fields") or []:
        if field_id not in missing:
            missing.append(field_id)
    for field_id in pack2_block.get("missing_fields") or []:
        if field_id not in missing:
            missing.append(field_id)
    for field_id in pack3_block.get("missing_fields") or []:
        if field_id not in missing:
            missing.append(field_id)
    for field_id in pack4_block.get("missing_fields") or []:
        if field_id not in missing:
            missing.append(field_id)
    for field_id in pack5_block.get("missing_fields") or []:
        if field_id not in missing:
            missing.append(field_id)
    for field_id in pack6_block.get("missing_fields") or []:
        if field_id not in missing:
            missing.append(field_id)
    if cost_block.get("spread_r_of_stop") is None and cost_block.get("cost_r") is None:
        missing.append("cost")

    peers = assemble_peers_block(
        symbol=symbol,
        as_of_utc=as_of,
        books=books,
        peer_books=peer_books,
    )
    usdjpy_present = bool((peers.get("usdjpy") or {}).get("present"))
    if normalize_symbol(symbol) == "XAUUSD" and not usdjpy_present:
        missing.append("peers.usdjpy")

    # Multi-symbol Challenge drop is M15+H4. D1 stays on the XAU parent tape.
    # Missing D1 is visible; it does not TF-abstain a row that has M15+H4.
    tfs_ok = bool(m15 and h4)
    tfs_all_three = bool(m15 and h4 and d1)
    geo_ok = geo.get("stop_dist") is not None or (
        geo.get("entry") is not None and geo.get("stop") is not None
    )
    sufficient = bool(
        candidate_id
        and symbol
        and side
        and sleeve
        and tfs_ok
        and geo_ok
        and as_of
        and family != "unknown"
    )

    atr_basis = "missing"
    if geo.get("stop_dist") is not None:
        atr_basis = "intent_price"
    elif geo.get("stop_atr") is not None:
        atr_basis = "wave21_atr"

    surface_block = {
        "us30_off": True,
        "hard_off_families": list(HARD_OFF_FAMILIES),
        "keep_families": list(KEEP_FAMILIES),
        "circuit": "2-stop",
        "token_digest_matches": None,
        "hard_off_family_this_row": hard_off_family(sleeve, symbol),
    }
    if surface:
        surface_block.update(surface)
    surface_block["us30_off"] = True

    if world is not None:
        world_block = dict(world)
    else:
        from .world_state import assemble_world_state_v0

        xau_for_world = None
        if books and normalize_symbol(symbol) == "XAUUSD":
            xau_for_world = books
        elif peer_books and peer_books.get("XAUUSD"):
            xau_for_world = peer_books["XAUUSD"]
        world_block = assemble_world_state_v0(
            as_of_utc=as_of,
            as_of_clock=as_of_clock,
            symbol=symbol,
            side=side,
            peer_books=peer_books,
            xau_books=xau_for_world,
            trades=deal_tape,
            news=news,
            utc_hour=utc_hour,
            is_friday=weekday == 4,
            origin_organism=origin_organism,
            include_rdf=True,
        )
    world_comp = world_block.get("completeness") or {}

    state = {
        "schema": SCHEMA,
        "as_of_clock": as_of_clock,
        "identity": {
            "candidate_id": candidate_id,
            "symbol": symbol,
            "side": side,
            "sleeve": sleeve,
            "setup_id": setup_id,
            "sleeve_kind": sleeve_kind,
            "family_class": family,
            "origin_organism": origin_organism,
            "decision_day": as_of.date().isoformat(),
            "decision_bar_iso": as_of.strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        "clock": {
            "as_of_utc": as_of.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "broker_epoch": None,
            "rule": "new_york_plus_7",
            "weekday": weekday,
            "weekday_name": _WEEKDAY[weekday],
            "is_friday": weekday == 4,
        },
        "sessions": {
            "broker_hour": broker_hour,
            "utc_hour": utc_hour,
            "named": _session_named(utc_hour, weekday == 4),
            "bars_since_session_open": None,
            "session_open_range_width_atr": None,
            "source": "wave21_utc_session" if utc_hour is not None else "unassembled",
        },
        "timeframes": timeframes,
        "levels": {
            "prior_day_high": pdh,
            "prior_day_low": pdl,
            "prior_week_high": None,
            "prior_week_low": None,
            "dist_to_prior_high20_atr": None,
            "dist_to_prior_low20_atr": None,
            "fvg": None,
            "sweep_depth_atr": None,
            "poi": None,
            "source": "wave21" if pdh is not None else "unassembled",
        },
        "news": {k: v for k, v in news.items() if k != "usd_high_in_10d"},
        "sleeve_features": {
            "ac60": feats.get("ac60"),
            "vol_ratio": feats.get("vol_ratio") or feats.get("atr_ratio"),
            "htf_slope_norm": feats.get("htf_slope_norm"),
            "mom_20_atr": feats.get("mom_20_atr"),
            "fvg_freshness_bars": feats.get("fvg_freshness_bars"),
            "session_hour": feats.get("session_hour") or broker_hour,
            "a8_k_of_4_pass": feats.get("a8_k_of_4_pass"),
            "a8_source": feats.get("a8_source"),
            "intra_size": feats.get("intra_size"),
            "tag": feats.get("tag") or sleeve,
            "cluster": feats.get("cluster"),
            "setup_id": feats.get("setup_id") or setup_id,
            "session": feats.get("session") or aplus_block.get("session"),
        },
        "geometry": {
            "entry": geo.get("entry"),
            "stop": geo.get("stop"),
            "target": geo.get("target"),
            "stop_dist": geo.get("stop_dist"),
            "target_dist": geo.get("target_dist"),
            "plan_r": geo.get("plan_r"),
            "stop_atr": geo.get("stop_atr"),
            "target_atr": geo.get("target_atr"),
            "runner_r": geo.get("runner_r"),
            "order_type": geo.get("order_type") or "MARKET",
            "atr14": (m15 or {}).get("atr14") if m15 else geo.get("atr14"),
            "trigger_bar_range_atr": geo.get("trigger_bar_range_atr"),
            "trigger_bar_body_atr": geo.get("trigger_bar_body_atr"),
            "compression_ratio_prior_bar": geo.get("compression_ratio_prior_bar"),
            "close_position_in_lookback_range": geo.get("close_position_in_lookback_range"),
        },
        "cost": {
            "spread_r": cost_block.get("spread_r"),
            "spread_r_of_stop": cost_block.get("spread_r_of_stop"),
            "expected_slippage_r": cost_block.get("expected_slippage_r"),
            "swap_cost_r": cost_block.get("swap_cost_r"),
            "commission_r": cost_block.get("commission_r"),
            "cost_r": cost_block.get("cost_r"),
            "cost_screen_would_refuse": cost_block.get("cost_screen_would_refuse"),
            "source": cost_block.get("source") or ("tick" if cost_block else "unassembled"),
        },
        "occupancy": {
            "symbol_open": occ.get("symbol_open"),
            "symbol_pending": occ.get("pending") if "pending" in occ else occ.get("symbol_pending"),
            "already_placed_today": occ.get("already_placed_today"),
            "cluster_placed_today": occ.get("cluster_placed_today"),
            "isolated_reentry_legal": occ.get("isolated_reentry_legal"),
            "same_sleeve_orig_stops_utc_day": occ.get("same_sleeve_orig_stops_utc_day"),
            "two_stop_exhausted": occ.get("two_stop_exhausted"),
            "minutes_since_flat": occ.get("minutes_since_flat"),
            "corr_hold_named": occ.get("corr_hold_named"),
            "two_stop_source": occ.get("two_stop_source"),
            # A+ occupancy hooks are labels. KEEP-one / 2-stop COUNT stay integers.
            "cluster_named": occ.get("cluster_named") or occ.get("cluster"),
            "keep_one_symbol": occ.get("keep_one_symbol"),
            "isolated_reentry_minutes": occ.get("isolated_reentry_minutes"),
            "occupancy_source": occ.get("occupancy_source"),
        },
        "world": world_block,
        "governor": {
            "allow_new": gov.get("allow_new"),
            "cap_mult": gov.get("cap_mult"),
            "reason": gov.get("reason"),
            "realized_today_pct": gov.get("realized_today_pct"),
            "open_risk_pct": gov.get("open_risk_pct"),
        },
        "surface": surface_block,
        "chair_fields": chair_block,
        "pack2_fields": pack2_block,
        "pack3_fields": pack3_block,
        "pack4_fields": pack4_block,
        "pack5_fields": pack5_block,
        "pack6_fields": pack6_block,
        "peers": (
            {**peers, **peers_block}
            if peers_block
            else (
                {
                    **peers,
                    "peers": [],
                    "ca_role": None,
                    "dxy_hook": None,
                    "funding_hook": None,
                    "peer_state": None,
                    "source": "unassembled",
                    "invented": False,
                    "assembled": False,
                }
                if aplus_block
                else peers
            )
        ),
        "completeness": {
            "clock": True,
            "sessions": utc_hour is not None,
            "timeframes_m15_h4": tfs_ok,
            "timeframes_m15_h4_d1": tfs_all_three,
            "levels": pdh is not None,
            "news_spine": not news["spine_empty"],
            "sleeve_features": bool(feats),
            "geometry": geo_ok,
            "geometry_atr_basis": atr_basis,
            "cost": cost_block.get("spread_r_of_stop") is not None or cost_block.get("cost_r") is not None,
            "occupancy": any(
                occ.get(k) is not None
                for k in (
                    "symbol_open",
                    "symbol_pending",
                    "pending",
                    "already_placed_today",
                    "cluster_placed_today",
                    "isolated_reentry_legal",
                    "minutes_since_flat",
                    "same_sleeve_orig_stops_utc_day",
                    "two_stop_exhausted",
                    "corr_hold_named",
                )
            ),
            "peers_usdjpy": usdjpy_present,
            "aplus_sleeve": bool(aplus_block.get("setup_id") and aplus_block.get("spec_complete", True)),
            "chair_fields": bool(chair_block.get("ids")) and not chair_block.get("invented"),
            "pack2_fields": bool(pack2_block.get("ids")) and not pack2_block.get("invented"),
            "pack3_fields": bool(pack3_block.get("ids")) and not pack3_block.get("invented"),
            "pack4_fields": bool(pack4_block.get("ids")) and not pack4_block.get("invented"),
            "pack5_fields": bool(pack5_block.get("ids")) and not pack5_block.get("invented"),
            "pack6_fields": bool(pack6_block.get("ids")) and not pack6_block.get("invented"),
            "peers": bool(peers_block.get("assembled")),
            "world": bool(world_block),
            "cross_asset_peers": bool((world_block.get("n_peers_present") or 0) > 0),
            "cross_asset_usd_proxy": bool(world_comp.get("cross_asset_usd_proxy") or world_comp.get("usd_proxy")),
            "cross_asset_session_liquidity": bool(world_comp.get("session_liquidity")),
            "state_sufficient_for_live": sufficient,
            "missing_fields": missing,
            "expost_rejected": leaked,
        },
    }
    if aplus_block:
        state["aplus"] = aplus_block
    chair = assemble_chair_wires(
        symbol=symbol,
        as_of_utc=as_of,
        gold=state,
        peers={},
        news=news,
        books=books,
        peer_books=peer_books,
    )
    folded = apply_pack4_fold(state, chair)
    try:
        from .equity_frame import attach_account

        injected = extra.get("account") if extra else None
        if not isinstance(injected, Mapping):
            injected = None
        folded = attach_account(folded, injected=injected)
    except Exception:
        folded["account"] = {
            "login": 0,
            "equity": None,
            "to_pass": None,
            "floor_room": None,
            "terminal_read": "missing",
            "cash_unit_usd": 150.0,
            "invented": False,
            "reason": None,
        }
    try:
        from .jev_questions import hierarchical_labels

        if isinstance(folded, dict):
            folded["labels"] = hierarchical_labels(folded)
    except Exception:
        pass
    return folded


# gold_state.v0 is the closed symbol_state object. Name is historical; assembler
# is already multi-symbol (Challenge drop is M15+H4; D1 optional off XAU).
assemble_symbol_state_v0 = assemble_gold_state_v0
