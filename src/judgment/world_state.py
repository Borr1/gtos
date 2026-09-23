"""assemble_world_state_v0 — closed desk object. Default-off research.

Sits *above* gold_state.v0. One world per as-of; many gold candidates may
point at it. Intelligence only — never place / remint / flatten.

Honest gaps stay named:
  * data/DXY_D1.csv exists but is not ICE DXY (prints ~25) — rejected
  * no US10Y / TNX yield tape; Sierra ZN is control-only and thin
  * NEWS_PROTOCOL is not in git — do not invent endpoints or HIGH rows
  * raw X firehose is not a field
  * Challenge prove never reads April historical as a peer book
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable, Mapping, Sequence

from .bars import (
    StampedBar,
    _is_single_tf_cache,
    books_for_symbol,
    landed_challenge_symbols,
    last_closed_at_or_before,
    normalize_symbol,
    tf_snap,
)
from .gold_state import EXPOST_KEYS, reject_expost
from .host_events import news_inventory_at
from .named_sources import (
    DXY_ABSENT_REASON,
    DXY_REJECTED_REASON,
    YIELD_ABSENT_REASON,
    inspect_dxy_csv,
)
from .news_spine import attach_news, load_spines
from .occupancy import CORR_CLUSTER, TapeTrade, corr_cluster, occupancy_at, occupancy_book_at
from .process_lock import stamp_lock

SCHEMA = "gtos.judgment.world_state.v0"
NEVER = {
    "never_place": True,
    "never_remint": True,
    "never_flatten": True,
    "never_invent_news_protocol": True,
    "never_ingest_raw_x": True,
}

USD_PROXY_SYMBOLS = ("EURUSD", "GBPUSD", "USDJPY")
RISK_PROXY_SYMBOLS = ("NAS100", "US30", "UK100")
METALS_CROSS_SYMBOLS = ("XAGUSD",)

_WEEKDAY = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def _as_of(as_of_utc: datetime) -> datetime:
    as_of = as_of_utc if as_of_utc.tzinfo else as_of_utc.replace(tzinfo=timezone.utc)
    return as_of.astimezone(timezone.utc)


def _stance_from_trend(trend: int | None) -> str | None:
    if trend not in (1, 0, -1):
        return "unassembled"
    from .state_choices import LEGACY, stance_choice

    chosen = stance_choice(int(trend))
    if chosen is not LEGACY:
        return chosen
    if trend == 1:
        return "up"
    if trend == -1:
        return "down"
    if trend == 0:
        return "flat"
    return "unassembled"


def _usd_from_pair(symbol: str, trend: int | None) -> int | None:
    """Map pair trend onto USD strength. +1 = USD stronger."""
    if trend not in (1, 0, -1):
        return None
    sym = normalize_symbol(symbol)
    if sym in {"EURUSD", "GBPUSD", "AUDUSD", "NZDUSD"}:
        return -trend
    if sym in {"USDJPY", "USDCHF", "USDCAD"}:
        return trend
    return None


def _combine_signed(votes: Sequence[int | None]) -> tuple[str | None, list[int]]:
    named = [v for v in votes if v in (1, 0, -1)]
    if not named:
        return "unassembled", []
    ups = sum(1 for v in named if v == 1)
    downs = sum(1 for v in named if v == -1)
    from .state_choices import LEGACY, combine_choice

    chosen = combine_choice(ups, downs)
    if chosen is not LEGACY:
        return chosen, named
    if ups and downs:
        return "mixed", named
    if ups:
        return "stronger", named
    if downs:
        return "weaker", named
    return "mixed", named


def snap_block(books: Mapping[str, list[StampedBar]] | None, as_of: datetime) -> dict[str, Any]:
    if not books:
        return {"h4": None, "d1": None, "source": "unassembled"}
    h4 = tf_snap(books.get("h4") or [], as_of, "H4", lookback=30) if books.get("h4") else None
    d1 = tf_snap(books.get("d1") or [], as_of, "D1", lookback=8) if books.get("d1") else None
    if not h4 and not d1:
        return {"h4": None, "d1": None, "source": "unassembled"}
    return {
        "h4": h4,
        "d1": d1,
        "source": "named_tf_snap",
        "trend": (d1 or {}).get("trend") if d1 and d1.get("trend") is not None else (h4 or {}).get("trend"),
    }


def _d1_closes(rows: Sequence[StampedBar], as_of: datetime, n: int = 60) -> list[tuple[str, float]]:
    idx = last_closed_at_or_before(list(rows), as_of)
    if idx is None:
        return []
    start = max(0, idx - n)
    out: list[tuple[str, float]] = []
    for i in range(start, idx + 1):
        out.append((rows[i].utc.date().isoformat(), float(rows[i].bar.c)))
    return out


def _returns(closes: Sequence[tuple[str, float]]) -> list[tuple[str, float]]:
    out: list[tuple[str, float]] = []
    for i in range(1, len(closes)):
        prev = closes[i - 1][1]
        if prev > 0:
            out.append((closes[i][0], closes[i][1] / prev - 1.0))
    return out


def pearson(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    n = len(xs)
    if n < 10 or n != len(ys):
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = sum((x - mx) ** 2 for x in xs) ** 0.5
    dy = sum((y - my) ** 2 for y in ys) ** 0.5
    if dx == 0.0 or dy == 0.0:
        return None
    return num / (dx * dy)


def aligned_returns(
    left: Sequence[StampedBar] | None,
    right: Sequence[StampedBar] | None,
    as_of: datetime,
    *,
    invert_right: bool = False,
    window: int = 60,
) -> list[tuple[float, float]]:
    if not left or not right:
        return []
    lmap = dict(_returns(_d1_closes(left, as_of, n=window + 1)))
    rmap = dict(_returns(_d1_closes(right, as_of, n=window + 1)))
    days = sorted(set(lmap) & set(rmap))
    pairs: list[tuple[float, float]] = []
    for day in days:
        rv = -rmap[day] if invert_right else rmap[day]
        pairs.append((lmap[day], rv))
    return pairs


def corr_flags(
    pairs: Sequence[tuple[float, float]],
    *,
    short_n: int = 20,
    long_n: int = 60,
) -> dict[str, Any]:
    if len(pairs) < 10:
        return {
            "n": len(pairs),
            "corr_20d": None,
            "corr_60d": None,
            "relation": "unassembled",
            "regime_broken": None,
            "source": "unassembled",
        }
    short = pairs[-short_n:] if len(pairs) >= short_n else pairs
    long = pairs[-long_n:] if len(pairs) >= long_n else pairs
    c20 = pearson([p[0] for p in short], [p[1] for p in short])
    c60 = pearson([p[0] for p in long], [p[1] for p in long])
    relation: str | None = "unassembled"
    if c20 is not None:
        from .state_choices import relation_choice

        chosen = relation_choice(c20)
        if isinstance(chosen, str) and chosen:
            relation = chosen
    broken = None
    if c20 is not None and c60 is not None:
        from .state_choices import broken_choice

        chosen_broken = broken_choice(c20, c60)
        if chosen_broken is True or chosen_broken is False:
            broken = chosen_broken
    return {
        "n": len(pairs),
        "corr_20d": None if c20 is None else round(c20, 4),
        "corr_60d": None if c60 is None else round(c60, 4),
        "relation": relation,
        "regime_broken": broken,
        "source": "named_d1_returns",
    }


def _usd_proxy_block(
    cross_books: Mapping[str, Mapping[str, list[StampedBar]]] | None,
    as_of: datetime,
) -> dict[str, Any]:
    snaps: dict[str, Any] = {}
    votes: list[int | None] = []
    present: list[str] = []
    for symbol in USD_PROXY_SYMBOLS:
        books = (cross_books or {}).get(symbol)
        block = snap_block(books, as_of)
        snaps[symbol.lower()] = block
        if block.get("source") == "named_tf_snap":
            present.append(symbol)
            votes.append(_usd_from_pair(symbol, block.get("trend")))
    stance, named_votes = _combine_signed(votes)
    source = "usd_fx_basket" if present else "unassembled"
    dxy = inspect_dxy_csv()
    return {
        "stance": stance,
        "votes": named_votes,
        "present": present,
        "snaps": snaps,
        "dxy": {
            "series": None,
            "source": "unassembled",
            "reason": dxy.get("reason") or DXY_ABSENT_REASON,
            "file_present": bool(dxy.get("file_present")),
            "usable_as_ice_dxy": bool(dxy.get("usable_as_ice_dxy")),
            "last_close": dxy.get("last_close"),
            "path": dxy.get("path"),
            "proxy_used_instead": "usd_fx_basket" if present else None,
        },
        "source": source,
    }


def _risk_proxy_block(
    cross_books: Mapping[str, Mapping[str, list[StampedBar]]] | None,
    as_of: datetime,
) -> dict[str, Any]:
    snaps: dict[str, Any] = {}
    votes: list[int | None] = []
    present: list[str] = []
    for symbol in RISK_PROXY_SYMBOLS:
        books = (cross_books or {}).get(symbol)
        block = snap_block(books, as_of)
        snaps[symbol.lower()] = block
        if block.get("source") == "named_tf_snap":
            present.append(symbol)
            trend = block.get("trend")
            votes.append(trend if trend in (1, 0, -1) else None)
    stance, _named = _combine_signed(votes)
    named = "unassembled"
    if stance == "stronger":
        named = "risk_on"
    elif stance == "weaker":
        named = "risk_off"
    elif stance == "mixed":
        named = "mixed"
    return {
        "stance": named,
        "present": present,
        "snaps": snaps,
        "source": "named_index_tapes" if present else "unassembled",
    }


def _metals_cross_block(
    cross_books: Mapping[str, Mapping[str, list[StampedBar]]] | None,
    as_of: datetime,
) -> dict[str, Any]:
    snaps: dict[str, Any] = {}
    present: list[str] = []
    for symbol in METALS_CROSS_SYMBOLS:
        books = (cross_books or {}).get(symbol)
        block = snap_block(books, as_of)
        snaps[symbol.lower()] = block
        if block.get("source") == "named_tf_snap":
            present.append(symbol)
    return {
        "present": present,
        "snaps": snaps,
        "source": "named_metals_cross" if present else "unassembled",
    }


def _rates_block(usd: dict[str, Any]) -> dict[str, Any]:
    """Yield tape is absent. USD FX basket is a proxy, never a rates print."""
    usd_ok = usd.get("source") == "usd_fx_basket"
    return {
        "path_named": "usd_proxy_basket" if usd_ok else "unassembled",
        "named_yield": {
            "series": None,
            "last_close": None,
            "trend": None,
            "source": "unassembled",
            "reason": YIELD_ABSENT_REASON,
            "sierra_zn": "control_only_absent",
        },
        "usd_proxy_only": bool(usd_ok),
        "assembled": False,
        "source": "usd_proxy_basket" if usd_ok else "unassembled",
    }


def _gold_usd_corr(
    gold_books: Mapping[str, list[StampedBar]] | None,
    cross_books: Mapping[str, Mapping[str, list[StampedBar]]] | None,
    as_of: datetime,
) -> dict[str, Any]:
    gold_d1 = (gold_books or {}).get("d1") if gold_books else None
    eurusd = ((cross_books or {}).get("EURUSD") or {}).get("d1")
    usdjpy = ((cross_books or {}).get("USDJPY") or {}).get("d1")
    used = None
    pairs: list[tuple[float, float]] = []
    if gold_d1 and eurusd:
        pairs = aligned_returns(gold_d1, eurusd, as_of, invert_right=True)
        used = "XAUUSD_vs_inv_EURUSD"
    elif gold_d1 and usdjpy:
        pairs = aligned_returns(gold_d1, usdjpy, as_of, invert_right=False)
        used = "XAUUSD_vs_USDJPY"
    flags = corr_flags(pairs)
    flags["pair"] = used
    return flags


def _cluster_occupancy(
    trades: Sequence[TapeTrade] | None,
    *,
    focus_symbol: str,
    as_of: datetime,
    this_ticket: Any = None,
) -> dict[str, Any]:
    clusters: dict[str, dict[str, Any]] = {}
    for symbol, cluster in CORR_CLUSTER.items():
        bucket = clusters.setdefault(
            cluster,
            {"cluster": cluster, "open_symbols": [], "n_open": 0},
        )
        if trades is None:
            continue
        occ = occupancy_at(
            trades,
            symbol=symbol,
            as_of_utc=as_of,
            this_ticket=this_ticket,
        )
        if occ.get("symbol_open"):
            bucket["open_symbols"].append(symbol)
            bucket["n_open"] = int(bucket["n_open"]) + 1
    focus = corr_cluster(focus_symbol)
    focus_row = clusters.get(focus or "", {})
    crowded = None if trades is None else bool(focus_row.get("n_open"))
    return {
        "clusters": clusters,
        "focus_cluster": focus,
        "focus_cluster_crowded": crowded,
        "source": "unassembled" if trades is None else "challenge_deals",
    }


def _liquidity_block(gold: Mapping[str, Any] | None) -> dict[str, Any]:
    gold = gold or {}
    cost = gold.get("cost") or {}
    feats = gold.get("sleeve_features") or {}
    sessions = gold.get("sessions") or {}
    spread = cost.get("spread_r_of_stop")
    if spread is None:
        spread = cost.get("spread_r")
    named = any(
        v is not None
        for v in (spread, feats.get("vol_ratio"), sessions.get("named"))
    )
    return {
        "spread_r_of_stop": spread,
        "vol_ratio": feats.get("vol_ratio"),
        "session_named": sessions.get("named"),
        "sierra_zn": "control_only_absent",
        "sierra_cl": "control_only_absent",
        "order_book": "unassembled",
        "source": "gold_cost_and_session" if named else "unassembled",
    }


def _focus_from(gold: Mapping[str, Any] | None, focus: Mapping[str, Any] | None) -> dict[str, Any]:
    identity = (gold or {}).get("identity") or {}
    extra = focus or {}
    return {
        "candidate_id": extra.get("candidate_id") or identity.get("candidate_id"),
        "symbol": normalize_symbol(str(extra.get("symbol") or identity.get("symbol") or "XAUUSD")),
        "side": str(extra.get("side") or identity.get("side") or "").lower() or None,
        "sleeve": extra.get("sleeve") or identity.get("sleeve"),
        "family_class": extra.get("family_class") or identity.get("family_class"),
        "origin_organism": extra.get("origin_organism") or identity.get("origin_organism"),
    }


def gold_sold_into_usd_strength(focus: Mapping[str, Any], usd: Mapping[str, Any]) -> bool | None:
    """Code fact for the hedge-fund shape. None when either side is unknown."""
    side = str(focus.get("side") or "").lower()
    stance = usd.get("stance")
    if stance in (None, "unassembled", "mixed"):
        return None
    if side not in {"long", "short", "buy", "sell"}:
        return None
    from .state_choices import LEGACY, sold_into_choice

    chosen = sold_into_choice(side, str(stance))
    if chosen is not LEGACY:
        return chosen
    short = side in {"short", "sell"}
    usd_strong = stance == "stronger"
    # Sold gold into USD strength, or bought gold into USD weakness.
    return (short and usd_strong) or ((not short) and (not usd_strong))


def load_peer_books(
    cache: dict | None = None,
    *,
    challenge_true: bool = True,
) -> dict[str, dict[str, list[StampedBar]]]:
    """Landed Challenge books only when challenge_true. Never April historical."""
    out: dict[str, dict[str, list[StampedBar]]] = {}
    if cache:
        if _is_single_tf_cache(cache):
            if cache.get("m15"):
                out["XAUUSD"] = cache  # type: ignore[assignment]
        else:
            for key, books in cache.items():
                if not books:
                    continue
                if isinstance(books, dict) and books.get("m15") is not None:
                    out[normalize_symbol(str(key))] = books
    if not challenge_true:
        return out
    for symbol in landed_challenge_symbols():
        if symbol in out:
            continue
        loaded = books_for_symbol(symbol, cache if isinstance(cache, dict) else None)
        if loaded and loaded.get("m15"):
            out[symbol] = loaded
    return out


def assemble_world_state_v0(
    *,
    as_of_utc: datetime,
    as_of_clock: str = "as_of_open_study",
    gold: Mapping[str, Any] | None = None,
    focus: Mapping[str, Any] | None = None,
    gold_books: Mapping[str, list[StampedBar]] | None = None,
    cross_books: Mapping[str, Mapping[str, list[StampedBar]]] | None = None,
    trades: Sequence[TapeTrade] | None = None,
    spines: dict[str, Any] | None = None,
    host_events: Iterable[dict[str, Any]] | None = None,
    this_ticket: Any = None,
    forbid_expost: Mapping[str, Any] | None = None,
    yield_books: Mapping[str, Mapping[str, list[StampedBar]]] | None = None,
    funding_rows: Sequence[Mapping[str, Any]] | None = None,
    include_rdf: bool = True,
    symbol: str = "XAUUSD",
    side: str | None = None,
    peer_books: Mapping[str, Mapping[str, Sequence[StampedBar]]] | None = None,
    xau_books: Mapping[str, Sequence[StampedBar]] | None = None,
    news: Mapping[str, Any] | None = None,
    occupancy_book: Mapping[str, Any] | None = None,
    utc_hour: int | None = None,
    is_friday: bool | None = None,
    origin_organism: str = "historical_lab",
) -> dict[str, Any]:
    """Build one closed world_state.v0 object. Missing blocks stay visible.

    Desk blocks (usd / rates / rdf / occupancy) stay the #12/#23 object.
    Cross-asset flatten keys (usd_proxy / challenge_true / n_peers_present)
    attach from CA-V0 so gold_state and CA tests can read them without a
    second assembler.
    """
    leaked = reject_expost(forbid_expost or gold, as_of_clock)
    if leaked and as_of_clock == "live_intent":
        raise ValueError(f"EXPOST keys illegal on live_intent world: {leaked}")

    as_of = _as_of(as_of_utc)
    weekday = as_of.weekday()
    if is_friday is None:
        is_friday = weekday == 4
    if utc_hour is None:
        utc_hour = as_of.hour
    if cross_books is None and peer_books:
        cross_books = peer_books  # type: ignore[assignment]
    if gold_books is None and xau_books:
        gold_books = xau_books  # type: ignore[assignment]
    if focus is None and (symbol or side):
        focus = {"symbol": symbol, "side": side}
    focus_block = _focus_from(gold, focus)
    news = attach_news(as_of, spines=spines if spines is not None else load_spines(), symbol=focus_block["symbol"])
    host_news = news_inventory_at(host_events, as_of)
    usd = _usd_proxy_block(cross_books, as_of)
    risk = _risk_proxy_block(cross_books, as_of)
    metals = _metals_cross_block(cross_books, as_of)
    rates = _rates_block(usd)
    corr = _gold_usd_corr(gold_books, cross_books, as_of)
    occ = _cluster_occupancy(
        trades,
        focus_symbol=focus_block["symbol"],
        as_of=as_of,
        this_ticket=this_ticket or focus_block.get("candidate_id"),
    )
    liq = _liquidity_block(gold)
    sold = gold_sold_into_usd_strength(focus_block, usd)

    missing: list[str] = []
    if usd["source"] == "unassembled":
        missing.append("usd.proxy")
    if risk["source"] == "unassembled":
        missing.append("risk.proxy")
    if metals["source"] == "unassembled":
        missing.append("metals_cross")
    missing.append("rates.named_yield")
    missing.append("usd.dxy")
    if news["spine_empty"]:
        missing.append("news.events")
    if occ["source"] == "unassembled":
        missing.append("occupancy.clusters")
    if corr["source"] == "unassembled":
        missing.append("corr.gold_vs_usd")
    if liq["source"] == "unassembled":
        missing.append("liquidity")

    desk_ok = bool(
        as_of
        and focus_block.get("symbol")
        and (
            usd["source"] != "unassembled"
            or (not news["spine_empty"])
            or occ["source"] != "unassembled"
        )
    )

    world = {
        "schema": SCHEMA,
        "as_of_clock": as_of_clock,
        **stamp_lock(),
        **NEVER,
        "clock": {
            "as_of_utc": as_of.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "broker_epoch": None,
            "rule": "new_york_plus_7",
            "weekday": weekday,
            "weekday_name": _WEEKDAY[weekday],
            "is_friday": weekday == 4,
        },
        "focus": focus_block,
        "usd": usd,
        "rates": rates,
        "risk": risk,
        "metals_cross": metals,
        "corr": {
            "gold_vs_usd": corr,
            "code_gold_sold_into_usd_strength": sold,
        },
        "liquidity": liq,
        "occupancy": occ,
        "news": {k: v for k, v in news.items() if k != "usd_high_in_10d"},
        "host_news": host_news,
        "narrative": {
            "source": "unassembled",
            "reason": "no_desk_brief_or_x_ingest_on_this_clone",
            "raw_x_forbidden": True,
        },
        "gold_schema": (gold or {}).get("schema"),
        "completeness": {
            "clock": True,
            "usd_proxy": usd["source"] != "unassembled",
            "risk_proxy": risk["source"] != "unassembled",
            "metals_cross": metals["source"] != "unassembled",
            "named_yield": False,
            "dxy": False,
            "news_spine": not news["spine_empty"],
            "host_news_read": host_news.get("host_news_inventory_status") == "READ",
            "occupancy": occ["source"] != "unassembled",
            "gold_usd_corr": corr["source"] != "unassembled",
            "liquidity": liq["source"] != "unassembled",
            "narrative": False,
            "state_sufficient_for_desk": desk_ok,
            "missing_fields": missing,
            "expost_rejected": leaked,
        },
    }
    if include_rdf:
        from .rates_dxy_funding import assemble_rates_dxy_funding_v0

        world["rdf"] = assemble_rates_dxy_funding_v0(
            as_of_utc=as_of,
            as_of_clock=as_of_clock,
            gold=gold,
            focus=focus_block,
            gold_books=gold_books,
            cross_books=cross_books,
            yield_books=yield_books,
            funding_rows=funding_rows,
        )

    challenge_true = origin_organism in {"f5_challenge", "w7_ultimate_book"} or origin_organism.endswith(
        "_challenge"
    )
    if origin_organism == "historical_lab":
        challenge_true = False
    occ_book = occupancy_book
    if occ_book is None:
        occ_book = occupancy_book_at(trades, as_of_utc=as_of, this_ticket=this_ticket)
    xau = xau_books or gold_books
    peers = dict(peer_books or cross_books or {})
    if xau is None and "XAUUSD" in peers:
        xau = peers["XAUUSD"]
    from .cross_asset import assemble_cross_asset_v0

    features = assemble_cross_asset_v0(
        as_of_utc=as_of,
        symbol=focus_block.get("symbol") or symbol,
        peer_books=peers,
        xau_books=xau,
        news=news,
        occupancy_book=occ_book,
        utc_hour=utc_hour,
        is_friday=bool(is_friday),
        challenge_true=challenge_true,
    )
    world["as_of_utc"] = as_of.strftime("%Y-%m-%dT%H:%M:%SZ")
    world["identity"] = {
        "symbol": normalize_symbol(str(focus_block.get("symbol") or symbol)),
        "side": side or focus_block.get("side"),
        "origin_organism": origin_organism,
    }
    world["cross_asset"] = features
    for key in (
        "peers",
        "n_peers_present",
        "usd_proxy",
        "rates_proxy",
        "risk_on",
        "gold_vs_usd",
        "gold_vs_index",
        "session_liquidity",
        "event_join",
        "occupancy_book",
        "challenge_true",
        "april_historical_used",
        "dxy_used",
    ):
        world[key] = features[key]
    ca_comp = dict(features.get("completeness") or {})
    ca_comp.pop("missing_fields", None)
    ca_comp.pop("usd_proxy", None)
    ca_comp.pop("dxy", None)
    world["completeness"] = {
        **world["completeness"],
        **ca_comp,
        "cross_asset_usd_proxy": bool((features.get("completeness") or {}).get("usd_proxy")),
        "cross_asset_peers": bool((features.get("n_peers_present") or 0) > 0),
        "missing_fields": missing,
        "expost_rejected": leaked,
        "state_sufficient_for_desk": desk_ok,
    }
    return world


def attach_world(gold: Mapping[str, Any], world: Mapping[str, Any]) -> dict[str, Any]:
    """Closed Jev state: gold body + world desk. Questions path-reference both."""
    leaked = [k for k in EXPOST_KEYS if k in gold and gold.get(k) is not None]
    return {
        "schema": "gtos.judgment.jev_state.gold_plus_world.v0",
        **NEVER,
        "gold": dict(gold),
        "world": dict(world),
        "expost_present": leaked,
    }
