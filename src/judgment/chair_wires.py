"""Scout+Edge Chair wire candidates — SHADOW labels only.

Fold into symbol_state peers / sessions / clock / sleeve.ca_labels.
Never invent DXY or TIPS. Never APPLY. Never place / remint / flatten.
Not a fluid inventory gate.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from .bars import StampedBar, last_closed_at_or_before, normalize_symbol
from .symbol_class import asset_class_for, peer_symbols_for, usd_from_pair_trend

SCHEMA = "gtos.judgment.chair_wires.v0"
SOURCE = "scout_edge_shadow"
WIRE_NAMES = (
    "usd_proxy_vs_xau",
    "gbpjpy_dual_leg_agree",
    "us30_rth_vs_eth",
    "usdjpy_tokyo_event_liquidity",
    "fx_session_london_fit",
    "sess.ldn_ny_overlap_vol",
    "corr.eur_gbp_usd_co_move",
    "corr.xau_vs_eur_proxy_usd",
    "tokyo_fix_window_label",
)

# 9:55 JST = 00:55 UTC (Japan has no DST). Clock-only; not NEWS.
TOKYO_FIX_START_MIN = 0 * 60 + 45
TOKYO_FIX_END_MIN = 1 * 60 + 15
# London close / NY open overlap on the gold_state map (ny starts at 12Z).
LDN_NY_OVERLAP = (12, 16)
USD_PROXY_PEERS = ("EURUSD", "USDJPY")
GBPJPY_LEGS = ("GBPUSD", "USDJPY")


def _as_of(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _sign(value: float | None) -> int | None:
    if value is None:
        return None
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def tokyo_fix_window_label(as_of_utc: datetime) -> str:
    """Clock-only Tokyo 9:55 JST fix window. Never a news event."""
    as_of = _as_of(as_of_utc)
    minutes = as_of.hour * 60 + as_of.minute
    if TOKYO_FIX_START_MIN <= minutes < TOKYO_FIX_END_MIN:
        return "tokyo_fix"
    return "outside"


def _empty(*, reason: str = "unassembled") -> dict[str, Any]:
    return {
        "present": False,
        "label": None,
        "source": reason,
        "apply": False,
        "shadow": True,
    }


def _books_lookup(store: Mapping[str, Any] | None, symbol: str) -> Mapping[str, Any] | None:
    if not store:
        return None
    return store.get(symbol) or store.get(symbol.lower())


def _tf_rows(
    symbol: str,
    tf: str,
    *,
    primary: str,
    books: Mapping[str, list[StampedBar]] | None,
    peer_books: Mapping[str, Any] | None,
) -> list[StampedBar] | None:
    if normalize_symbol(symbol) == primary:
        rows = (books or {}).get(tf)
        return list(rows) if rows else None
    block = _books_lookup(peer_books, symbol)
    if not block:
        return None
    rows = block.get(tf)
    return list(rows) if rows else None


def _h4_direction(
    symbol: str,
    *,
    primary: str,
    gold: Mapping[str, Any],
    peers: Mapping[str, Any],
    books: Mapping[str, list[StampedBar]] | None,
    peer_books: Mapping[str, Any] | None,
    as_of: datetime,
) -> tuple[int | None, str]:
    trend = None
    if normalize_symbol(symbol) == primary:
        trend = ((gold.get("timeframes") or {}).get("h4") or {}).get("trend")
    else:
        trend = (peers.get(symbol) or {}).get("h4_trend")
    if trend in (1, 0, -1):
        return int(trend), "h4_trend"
    rows = _tf_rows(symbol, "h4", primary=primary, books=books, peer_books=peer_books)
    if not rows:
        return None, "unassembled"
    idx = last_closed_at_or_before(rows, as_of)
    if idx is None or idx < 1:
        return None, "unassembled"
    prev = max(0, idx - 4)
    return _sign(rows[idx].bar.c - rows[prev].bar.c), "h4_close_sign"


def _pair_usd(
    pair: str,
    *,
    primary: str,
    gold: Mapping[str, Any],
    peers: Mapping[str, Any],
    books: Mapping[str, list[StampedBar]] | None,
    peer_books: Mapping[str, Any] | None,
    as_of: datetime,
) -> dict[str, Any]:
    direction, src = _h4_direction(
        pair,
        primary=primary,
        gold=gold,
        peers=peers,
        books=books,
        peer_books=peer_books,
        as_of=as_of,
    )
    mapped = usd_from_pair_trend(pair, direction)
    return {"direction": direction, "usd": mapped, "source": src}


def usd_proxy_vs_xau(
    *,
    primary: str,
    gold: Mapping[str, Any],
    peers: Mapping[str, Any],
    books: Mapping[str, list[StampedBar]] | None,
    peer_books: Mapping[str, Any] | None,
    as_of: datetime,
) -> dict[str, Any]:
    """USD proxy vs XAU. USDJPY is PRIMARY. EURUSD is xau_eur_proxy alias only if USDJPY is null. No DXY."""
    usdjpy = _pair_usd(
        "USDJPY",
        primary=primary,
        gold=gold,
        peers=peers,
        books=books,
        peer_books=peer_books,
        as_of=as_of,
    )
    eurusd = _pair_usd(
        "EURUSD",
        primary=primary,
        gold=gold,
        peers=peers,
        books=books,
        peer_books=peer_books,
        as_of=as_of,
    )
    detail = {"USDJPY": usdjpy, "EURUSD": eurusd}
    alias = False
    if usdjpy.get("usd") in (1, -1):
        proxy = int(usdjpy["usd"])
        proxy_source = "peers.usdjpy"
    elif eurusd.get("usd") in (1, -1):
        proxy = int(eurusd["usd"])
        proxy_source = "xau_eur_proxy"
        alias = True
    else:
        proxy = None
        proxy_source = "unassembled"
    xau_dir, xau_src = _h4_direction(
        "XAUUSD",
        primary=primary,
        gold=gold,
        peers=peers,
        books=books,
        peer_books=peer_books,
        as_of=as_of,
    )
    xau_usd = usd_from_pair_trend("XAUUSD", xau_dir)
    if proxy is None or xau_usd is None:
        row = _empty(reason="unassembled")
        row.update(
            {
                "usd_proxy": proxy,
                "xau_h4": xau_dir,
                "xau_usd": xau_usd,
                "peers": detail,
                "alias": alias,
                "primary_peer": "USDJPY",
            }
        )
        return row
    if proxy == 0 or xau_usd == 0:
        label = "flat"
    elif proxy == xau_usd:
        label = "agree"
    else:
        label = "disagree"
    return {
        "present": True,
        "label": label,
        "usd_proxy": proxy,
        "xau_h4": xau_dir,
        "xau_usd": xau_usd,
        "xau_source": xau_src,
        "peers": detail,
        "alias": alias,
        "primary_peer": "USDJPY",
        "source": proxy_source,
        "apply": False,
        "shadow": True,
        "never_invent_dxy": True,
    }


def gbpjpy_dual_leg_agree(
    *,
    primary: str,
    gold: Mapping[str, Any],
    peers: Mapping[str, Any],
    books: Mapping[str, list[StampedBar]] | None,
    peer_books: Mapping[str, Any] | None,
    as_of: datetime,
) -> dict[str, Any]:
    """GBPJPY ≈ GBPUSD × USDJPY. Both +1 → cross up. Peers only."""
    legs: dict[str, Any] = {}
    dirs: list[int] = []
    for pair in GBPJPY_LEGS:
        direction, src = _h4_direction(
            pair,
            primary=primary,
            gold=gold,
            peers=peers,
            books=books,
            peer_books=peer_books,
            as_of=as_of,
        )
        legs[pair] = {"direction": direction, "source": src}
        if direction is None:
            row = _empty(reason="unassembled")
            row.update({"legs": legs, "composed": None, "gbpjpy_h4": None})
            return row
        dirs.append(int(direction))
    composed = _sign(float(sum(dirs)))
    cross_dir, cross_src = _h4_direction(
        "GBPJPY",
        primary=primary,
        gold=gold,
        peers=peers,
        books=books,
        peer_books=peer_books,
        as_of=as_of,
    )
    if composed == 0:
        label = "legs_disagree" if dirs[0] != dirs[1] else "flat"
    elif cross_dir is None:
        label = "legs_agree"
    elif cross_dir == composed:
        label = "agree"
    elif cross_dir == 0:
        label = "flat"
    else:
        label = "disagree"
    return {
        "present": True,
        "label": label,
        "composed": composed,
        "gbpjpy_h4": cross_dir,
        "gbpjpy_source": cross_src,
        "legs": legs,
        "source": "peers_gbpusd_usdjpy",
        "apply": False,
        "shadow": True,
    }


def us30_rth_vs_eth(*, named: str | None, symbol: str) -> dict[str, Any]:
    """Sessions choice. House US30 off stays. Not a lift."""
    session = named or "unknown"
    if session == "ny":
        choice = "rth"
    elif session in {"asia", "london", "dead_21_00z", "friday_cutoff"}:
        choice = "eth"
    else:
        choice = "unknown"
    return {
        "present": True,
        "label": choice,
        "choice": choice,
        "named": session,
        "applies": normalize_symbol(symbol) == "US30",
        "house_us30_off": True,
        "source": "sessions.named",
        "apply": False,
        "shadow": True,
    }


def _tokyo_clock_window(as_of: datetime, named: str | None) -> bool:
    if tokyo_fix_window_label(as_of) == "tokyo_fix":
        return True
    if named == "asia":
        return True
    hour = as_of.hour
    return hour == 0 or 0 < hour < 7


def usdjpy_tokyo_event_liquidity(
    *,
    symbol: str,
    named: str | None,
    news: Mapping[str, Any],
    as_of: datetime,
) -> dict[str, Any]:
    """Asia/Tokyo clock + pair HIGH on the landed spine. No invented events."""
    primary = normalize_symbol(symbol)
    applicable = (
        primary == "USDJPY"
        or "JPY" in primary
        or "USDJPY" in peer_symbols_for(primary)
    )
    in_tokyo = _tokyo_clock_window(as_of, named)
    pair_high = news.get("pair_high_in_f5_window")
    spine_empty = bool(news.get("spine_empty"))
    if not applicable:
        row = _empty(reason="not_applicable")
        row["label"] = "not_applicable"
        row["present"] = True
        row.update({"in_tokyo": in_tokyo, "pair_high_in_f5_window": pair_high})
        return row
    if not in_tokyo:
        label = "outside_tokyo"
    elif spine_empty or pair_high is None:
        label = "tokyo_clock_spine_empty"
    elif pair_high:
        label = "tokyo_pair_high"
    else:
        label = "tokyo_quiet"
    return {
        "present": True,
        "label": label,
        "in_tokyo": in_tokyo,
        "tokyo_fix": tokyo_fix_window_label(as_of) == "tokyo_fix",
        "pair_high_in_f5_window": pair_high,
        "pair_high_n": news.get("pair_high_n"),
        "spine_empty": spine_empty,
        "source": "sessions_plus_spine",
        "apply": False,
        "shadow": True,
        "never_invent_news_protocol": True,
    }


def fx_session_london_fit(*, symbol: str, named: str | None) -> dict[str, Any]:
    asset = asset_class_for(symbol)
    session = named or "unknown"
    if asset != "fx":
        label = "not_fx"
    elif session == "london":
        label = "fit"
    else:
        label = "outside"
    return {
        "present": True,
        "label": label,
        "named": session,
        "asset_class": asset,
        "source": "sessions.named",
        "apply": False,
        "shadow": True,
    }


def ldn_ny_overlap_vol(
    m15: Sequence[StampedBar] | None,
    as_of_utc: datetime,
) -> dict[str, Any]:
    """M15 volume in the 12–16Z London/NY overlap. Empty ≠ zero."""
    as_of = _as_of(as_of_utc)
    in_window = LDN_NY_OVERLAP[0] <= as_of.hour < LDN_NY_OVERLAP[1]
    if not m15:
        row = _empty(reason="unassembled")
        row.update(
            {
                "in_window": in_window,
                "n": 0,
                "mean_vol": None,
                "ratio_vs_session": None,
                "hours": list(LDN_NY_OVERLAP),
            }
        )
        return row
    idx = last_closed_at_or_before(list(m15), as_of)
    if idx is None:
        row = _empty(reason="unassembled")
        row.update({"in_window": in_window, "n": 0, "mean_vol": None, "ratio_vs_session": None})
        return row
    recent = list(m15[max(0, idx - 19) : idx + 1])
    overlap = [row for row in recent if LDN_NY_OVERLAP[0] <= row.utc.hour < LDN_NY_OVERLAP[1]]
    if not overlap:
        return {
            "present": False,
            "label": "outside_window" if not in_window else "in_window_no_bars",
            "in_window": in_window,
            "n": 0,
            "mean_vol": None,
            "ratio_vs_session": None,
            "hours": list(LDN_NY_OVERLAP),
            "source": "outside_window",
            "apply": False,
            "shadow": True,
        }
    omean = sum(row.bar.v for row in overlap) / float(len(overlap))
    smean = sum(row.bar.v for row in recent) / float(len(recent)) if recent else None
    ratio = (omean / smean) if smean else None
    return {
        "present": True,
        "label": "overlap" if in_window else "overlap_bars_only",
        "in_window": in_window,
        "n": len(overlap),
        "mean_vol": omean,
        "ratio_vs_session": ratio,
        "hours": list(LDN_NY_OVERLAP),
        "source": "challenge_csv",
        "apply": False,
        "shadow": True,
    }


def _corr_pair(
    left: str,
    right: str,
    *,
    primary: str,
    books: Mapping[str, list[StampedBar]] | None,
    peer_books: Mapping[str, Any] | None,
    as_of: datetime,
) -> float | None:
    from .symbol_state import comove_20

    a = _tf_rows(left, "m15", primary=primary, books=books, peer_books=peer_books)
    b = _tf_rows(right, "m15", primary=primary, books=books, peer_books=peer_books)
    return comove_20(a, b, as_of)


def corr_block(
    *,
    primary: str,
    books: Mapping[str, list[StampedBar]] | None,
    peer_books: Mapping[str, Any] | None,
    as_of: datetime,
) -> dict[str, Any]:
    eur_gbp = _corr_pair(
        "EURUSD",
        "GBPUSD",
        primary=primary,
        books=books,
        peer_books=peer_books,
        as_of=as_of,
    )
    xau_eur = _corr_pair(
        "XAUUSD",
        "EURUSD",
        primary=primary,
        books=books,
        peer_books=peer_books,
        as_of=as_of,
    )
    present = eur_gbp is not None or xau_eur is not None
    return {
        "present": present,
        "eur_gbp_usd_co_move": eur_gbp,
        "xau_vs_eur_proxy_usd": xau_eur,
        "source": "comove_20" if present else "unassembled",
        "apply": False,
        "shadow": True,
        "never_invent_dxy": True,
    }


READY_CHOICES = ("a_plus", "almost", "blocked", "null_state")
IDENTITY_RESID_MAX = 0.15
BOJ_LIVE = frozenset({"print", "guidance_live"})
BOJ_RATE_FACT = {
    "rate_pct": 1.25,
    "effective_date_utc": "2026-09-24",
    "effective_utc": "2026-09-24T00:00:00Z",
    "use": "bucket_timing_only",
    "never_invent_print": True,
    "never_invent_guidance": True,
}
_BOJ_PRINT = ("boj", "policy rate", "interest rate decision", "rate decision")
_BOJ_GUIDANCE = ("press conference", "guidance", "governor ueda", "outlook")


def _last_close(
    symbol: str,
    *,
    primary: str,
    books: Mapping[str, list[StampedBar]] | None,
    peer_books: Mapping[str, Any] | None,
    as_of: datetime,
) -> float | None:
    rows = _tf_rows(symbol, "m15", primary=primary, books=books, peer_books=peer_books)
    if not rows:
        return None
    idx = last_closed_at_or_before(rows, as_of)
    if idx is None:
        return None
    return rows[idx].bar.c


def gbpjpy_identity_resid(
    *,
    primary: str,
    books: Mapping[str, list[StampedBar]] | None,
    peer_books: Mapping[str, Any] | None,
    as_of: datetime,
) -> dict[str, Any]:
    """GBPJPY vs GBPUSD×USDJPY. identity_ok at |resid|≤0.15."""
    cross = _last_close("GBPJPY", primary=primary, books=books, peer_books=peer_books, as_of=as_of)
    gbp = _last_close("GBPUSD", primary=primary, books=books, peer_books=peer_books, as_of=as_of)
    jpy = _last_close("USDJPY", primary=primary, books=books, peer_books=peer_books, as_of=as_of)
    if cross is None or gbp is None or jpy is None or gbp * jpy == 0:
        return {
            "present": False,
            "resid": None,
            "identity_ok": None,
            "implied": None,
            "source": "unassembled",
            "max_abs": IDENTITY_RESID_MAX,
        }
    implied = gbp * jpy
    resid = (cross / implied) - 1.0
    return {
        "present": True,
        "resid": resid,
        "identity_ok": abs(resid) <= IDENTITY_RESID_MAX,
        "implied": implied,
        "last_gbpjpy": cross,
        "source": "m15_last_close",
        "max_abs": IDENTITY_RESID_MAX,
    }


def _stamped_boj(news: Mapping[str, Any]) -> str | None:
    """Print / guidance_live only with a stamped spine row. Never invent."""
    events = list(news.get("pair_high_events") or []) + list(news.get("events") or [])
    seen: set[tuple[str, Any]] = set()
    for event in events:
        if not isinstance(event, dict):
            continue
        key = (str(event.get("datetime_utc") or ""), event.get("event"))
        if key in seen:
            continue
        seen.add(key)
        ccy = str(event.get("currency") or "")
        if ccy not in {"JPY", "ALL"}:
            continue
        minutes = event.get("minutes_from_as_of")
        if minutes is None:
            continue
        try:
            mins = int(minutes)
        except (TypeError, ValueError):
            continue
        title = str(event.get("event") or "").lower()
        if any(token in title for token in _BOJ_GUIDANCE) and -60 <= mins <= 90:
            return "guidance_live"
        if any(token in title for token in _BOJ_PRINT) and -60 <= mins <= 30:
            return "print"
    return None


def boj_bucket(as_of_utc: datetime, news: Mapping[str, Any]) -> dict[str, Any]:
    """BOJ 1.25% effective 2026-09-24 — timing only unless a spine stamp exists."""
    as_of = _as_of(as_of_utc)
    stamped = _stamped_boj(news)
    if stamped in BOJ_LIVE:
        label = stamped
        source = "spine_stamp"
    else:
        eff = datetime(2026, 9, 24, tzinfo=timezone.utc).date()
        delta = (as_of.date() - eff).days
        if delta < -1:
            label = "pre_effective"
        elif -1 <= delta <= 1:
            label = "effective_window"
        else:
            label = "post_effective"
        source = "rate_fact_timing"
    return {
        "present": True,
        "label": label,
        "stamped": stamped,
        "rate_fact": dict(BOJ_RATE_FACT),
        "boj_clear": label not in BOJ_LIVE,
        "source": source,
        "apply": False,
        "shadow": True,
        "never_invent_news_protocol": True,
    }


def london_expand_block(gold: Mapping[str, Any], named: str | None, m15: Sequence[StampedBar] | None, as_of: datetime) -> dict[str, Any]:
    snap = ((gold.get("timeframes") or {}).get("m15") or {})
    atr = snap.get("atr14")
    last_range = snap.get("last_range")
    expand_range = (last_range / atr) if atr and last_range is not None and atr > 0 else None
    vol = ldn_ny_overlap_vol(m15, as_of)
    last_vol = None
    mean_vol = vol.get("mean_vol")
    if m15:
        idx = last_closed_at_or_before(list(m15), as_of)
        if idx is not None:
            last_vol = m15[idx].bar.v
    expand_vol = (last_vol / mean_vol) if last_vol and mean_vol else None
    in_london = named == "london"
    return {
        "london_expand_range": expand_range,
        "london_expand_vol": expand_vol,
        "london_expand_ok": bool(in_london and expand_range is not None and expand_range > 1.0),
        "named": named,
        "source": "m15_snap" if expand_range is not None else "unassembled",
        "apply": False,
        "shadow": True,
    }


def cluster_eur_gbp(corr: Mapping[str, Any]) -> dict[str, Any]:
    value = corr.get("eur_gbp_usd_co_move")
    return {
        "present": value is not None,
        "comove_20": value,
        "members": ["EURUSD", "GBPUSD", "EURGBP"],
        "source": "comove_20" if value is not None else "unassembled",
        "apply": False,
        "shadow": True,
    }


def _ready_choice(conjuncts: dict[str, bool | None], *, hard_block: bool) -> str:
    if hard_block:
        return "blocked"
    values = list(conjuncts.values())
    if any(value is None for value in values):
        return "null_state"
    if all(values):
        return "a_plus"
    if not any(values):
        return "blocked"
    return "almost"


def gbpjpy_a_plus_ready(
    *,
    named: str | None,
    in_overlap: bool,
    dual: Mapping[str, Any],
    identity: Mapping[str, Any],
    boj: Mapping[str, Any],
) -> dict[str, Any]:
    """Choice {a_plus,almost,blocked,null_state}. Never admit."""
    legs = dual.get("legs") or {}
    gbp_dir = (legs.get("GBPUSD") or {}).get("direction")
    jpy_dir = (legs.get("USDJPY") or {}).get("direction")
    session_ok = bool(named == "london" or in_overlap)
    if dual.get("source") == "unassembled" or gbp_dir is None or jpy_dir is None:
        dual_same: bool | None = None
        agree: bool | None = None
    else:
        dual_same = gbp_dir in (1, -1) and gbp_dir == jpy_dir
        agree = dual.get("label") == "agree"
    identity_ok = identity.get("identity_ok")
    boj_clear = bool(boj.get("boj_clear"))
    conjuncts = {
        "session_ok": session_ok,
        "identity_ok": identity_ok,
        "agree": agree,
        "dual_same": dual_same,
        "boj_clear": boj_clear,
    }
    hard = (boj.get("label") in BOJ_LIVE) or (identity_ok is False)
    choice = _ready_choice(conjuncts, hard_block=hard)
    return {
        "choice": choice,
        "admit": None,
        "never_admit_choice": True,
        "conjuncts": conjuncts,
        "resid": identity.get("resid"),
        "boj_bucket": boj.get("label"),
        "source": "scout_edge_shadow",
        "apply": False,
        "shadow": True,
    }


def xau_dsp_shakeout_ready(
    *,
    named: str | None,
    in_overlap: bool,
    proxy: Mapping[str, Any],
    news: Mapping[str, Any],
    sufficient: bool,
) -> dict[str, Any]:
    """Same Choice shape. event_gap fail-closed. USDJPY primary proxy. Never admit."""
    session_ok = bool(named in {"london", "ny"} or in_overlap)
    if proxy.get("source") == "unassembled" or proxy.get("usd_proxy") is None:
        agree: bool | None = None
        dual_same: bool | None = None
        identity_ok: bool | None = None if not sufficient else False
    else:
        agree = proxy.get("label") == "agree"
        usdjpy_usd = ((proxy.get("peers") or {}).get("USDJPY") or {}).get("usd")
        eurusd_usd = ((proxy.get("peers") or {}).get("EURUSD") or {}).get("usd")
        dual_same = usdjpy_usd in (1, -1) and (eurusd_usd in (None, 0) or eurusd_usd == usdjpy_usd)
        identity_ok = bool(sufficient) and proxy.get("primary_peer") == "USDJPY" and usdjpy_usd in (1, -1)
    spine_empty = bool(news.get("spine_empty"))
    nearest = news.get("minutes_to_nearest_high")
    pair_high = news.get("pair_high_in_f5_window")
    high_f5 = news.get("high_in_f5_window")
    if spine_empty or nearest is None:
        event_gap_ok = False
        event_gap = "fail_closed_empty_spine"
    else:
        in_window = bool(pair_high or high_f5)
        event_gap_ok = not in_window
        event_gap = "outside_f5" if event_gap_ok else "inside_f5"
    conjuncts = {
        "session_ok": session_ok,
        "identity_ok": identity_ok,
        "agree": agree,
        "dual_same": dual_same,
        "event_gap_ok": event_gap_ok,
    }
    hard = event_gap == "fail_closed_empty_spine" and sufficient
    choice = _ready_choice(conjuncts, hard_block=hard)
    return {
        "choice": choice,
        "admit": None,
        "never_admit_choice": True,
        "conjuncts": conjuncts,
        "event_gap": event_gap,
        "usd_proxy_source": proxy.get("source"),
        "source": "scout_edge_shadow",
        "apply": False,
        "shadow": True,
    }


def assemble_chair_wires(
    *,
    symbol: str,
    as_of_utc: datetime,
    gold: Mapping[str, Any],
    peers: Mapping[str, Any],
    news: Mapping[str, Any],
    books: Mapping[str, list[StampedBar]] | None = None,
    peer_books: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """One SHADOW block + fold pieces. Completeness never flips live-sufficient."""
    primary = normalize_symbol(symbol)
    as_of = _as_of(as_of_utc)
    named = (gold.get("sessions") or {}).get("named")
    proxy = usd_proxy_vs_xau(
        primary=primary,
        gold=gold,
        peers=peers,
        books=books,
        peer_books=peer_books,
        as_of=as_of,
    )
    dual = gbpjpy_dual_leg_agree(
        primary=primary,
        gold=gold,
        peers=peers,
        books=books,
        peer_books=peer_books,
        as_of=as_of,
    )
    rth = us30_rth_vs_eth(named=named, symbol=primary)
    tokyo_liq = usdjpy_tokyo_event_liquidity(
        symbol=primary,
        named=named,
        news=news,
        as_of=as_of,
    )
    london = fx_session_london_fit(symbol=primary, named=named)
    overlap = ldn_ny_overlap_vol((books or {}).get("m15"), as_of)
    corr = corr_block(primary=primary, books=books, peer_books=peer_books, as_of=as_of)
    fix = tokyo_fix_window_label(as_of)
    in_overlap = bool(overlap.get("in_window"))
    expand = london_expand_block(gold, named, (books or {}).get("m15"), as_of)
    cluster = cluster_eur_gbp(corr)
    identity = gbpjpy_identity_resid(
        primary=primary,
        books=books,
        peer_books=peer_books,
        as_of=as_of,
    )
    boj = boj_bucket(as_of, news)
    gbp_ready = gbpjpy_a_plus_ready(
        named=named,
        in_overlap=in_overlap,
        dual=dual,
        identity=identity,
        boj=boj,
    )
    xau_ready = xau_dsp_shakeout_ready(
        named=named,
        in_overlap=in_overlap,
        proxy=proxy,
        news=news,
        sufficient=bool((gold.get("completeness") or {}).get("state_sufficient_for_live")),
    )
    ny_rth_us30 = rth.get("choice") == "rth"
    wires = {
        "usd_proxy_vs_xau": proxy,
        "gbpjpy_dual_leg_agree": dual,
        "us30_rth_vs_eth": rth,
        "usdjpy_tokyo_event_liquidity": tokyo_liq,
        "fx_session_london_fit": london,
        "sess.ldn_ny_overlap_vol": overlap,
        "corr.eur_gbp_usd_co_move": {
            "present": corr.get("eur_gbp_usd_co_move") is not None,
            "value": corr.get("eur_gbp_usd_co_move"),
            "source": "comove_20" if corr.get("eur_gbp_usd_co_move") is not None else "unassembled",
            "apply": False,
            "shadow": True,
        },
        "corr.xau_vs_eur_proxy_usd": {
            "present": corr.get("xau_vs_eur_proxy_usd") is not None,
            "value": corr.get("xau_vs_eur_proxy_usd"),
            "source": "comove_20" if corr.get("xau_vs_eur_proxy_usd") is not None else "unassembled",
            "apply": False,
            "shadow": True,
        },
        "tokyo_fix_window_label": {
            "present": True,
            "label": fix,
            "source": "clock_only",
            "apply": False,
            "shadow": True,
            "never_invent_news_protocol": True,
        },
        "session.in_ldn_ny_overlap": {
            "present": True,
            "label": in_overlap,
            "source": "sessions.named",
            "apply": False,
            "shadow": True,
        },
        "cluster.eur_gbp": cluster,
        "cross.gbpjpy": dual,
        "information.boj_bucket": boj,
        "sleeve.gbpjpy_a_plus_ready": gbp_ready,
        "sleeve.xau_dsp_shakeout_ready": xau_ready,
    }
    unassembled = [
        name
        for name, row in wires.items()
        if (row or {}).get("source") in {None, "unassembled"} and not (row or {}).get("present")
    ]
    sleeve_labels = {
        "usd_proxy_vs_xau": proxy.get("label"),
        "gbpjpy_dual_leg_agree": dual.get("label"),
        "us30_rth_vs_eth": rth.get("choice"),
        "usdjpy_tokyo_event_liquidity": tokyo_liq.get("label"),
        "fx_session_london_fit": london.get("label"),
        "sess.ldn_ny_overlap_vol": overlap.get("label"),
        "corr.eur_gbp_usd_co_move": corr.get("eur_gbp_usd_co_move"),
        "corr.xau_vs_eur_proxy_usd": corr.get("xau_vs_eur_proxy_usd"),
        "tokyo_fix_window_label": fix,
        "session.in_ldn_ny_overlap": in_overlap,
        "cluster.eur_gbp": cluster.get("comove_20"),
        "information.boj_bucket": boj.get("label"),
        "gbpjpy_a_plus_ready": gbp_ready.get("choice"),
        "xau_dsp_shakeout_ready": xau_ready.get("choice"),
        "chair_wires_apply": False,
        "never_admit_choice": True,
    }
    return {
        "schema": SCHEMA,
        "source": SOURCE,
        "apply": False,
        "shadow": True,
        "never_place": True,
        "never_remint": True,
        "never_flatten": True,
        "never_invent_dxy": True,
        "never_invent_tips": True,
        "never_invent_news_protocol": True,
        "names": list(WIRE_NAMES),
        "wires": wires,
        "unassembled": unassembled,
        "fold": {
            "clock": {"tokyo_fix_window_label": fix},
            "sessions": {
                "fx_session_london_fit": london.get("label"),
                "ldn_ny_overlap_vol": overlap,
                "us30_rth_vs_eth": rth.get("choice"),
                "in_ldn_ny_overlap": in_overlap,
                "london_expand_range": expand.get("london_expand_range"),
                "london_expand_vol": expand.get("london_expand_vol"),
                "london_expand_ok": expand.get("london_expand_ok"),
                "ny_rth_us30": ny_rth_us30,
            },
            "peers": {
                "usd_proxy_vs_xau": proxy,
                "gbpjpy_dual_leg_agree": dual,
                "corr": corr,
                "xau_eur_proxy": {
                    "present": bool(proxy.get("alias")) or ((proxy.get("peers") or {}).get("EURUSD") or {}).get("usd") in (1, -1),
                    "alias": bool(proxy.get("alias")),
                    "usd": ((proxy.get("peers") or {}).get("EURUSD") or {}).get("usd"),
                    "used": bool(proxy.get("alias")),
                    "source": "xau_eur_proxy" if proxy.get("alias") else "standby",
                },
            },
            "cluster": {"eur_gbp": cluster},
            "cross": {"gbpjpy": dual},
            "information": {"boj_bucket": boj},
            "sleeve_ready": {
                "gbpjpy_a_plus_ready": gbp_ready,
                "xau_dsp_shakeout_ready": xau_ready,
            },
            "class_specific": {
                "fx": {
                    "fx_session_london_fit": london.get("label"),
                    "usdjpy_tokyo_event_liquidity": tokyo_liq.get("label"),
                },
                "metal": {"usd_proxy_vs_xau": proxy.get("label")},
                "index": {
                    "us30_rth_vs_eth": rth.get("choice"),
                    "house_us30_off": True,
                },
            },
            "sleeve_labels": sleeve_labels,
        },
    }


def apply_pack4_fold(state: Mapping[str, Any], chair: Mapping[str, Any]) -> dict[str, Any]:
    """Attach PACK 4 SHADOW paths onto gold_state or symbol_state.

    Never emit admit Choice. Never soften ``us30_off``. Never flip
    ``state_sufficient_for_live``. Never APPLY.
    """
    packed = dict(state)
    fold = chair.get("fold") or {}
    clock = dict(packed.get("clock") or {})
    clock.update(fold.get("clock") or {})
    packed["clock"] = clock
    sessions = dict(packed.get("sessions") or {})
    sessions.update(fold.get("sessions") or {})
    packed["sessions"] = sessions
    peers = dict(packed.get("peers") or {})
    peers.update(fold.get("peers") or {})
    packed["peers"] = peers
    packed["cluster"] = fold.get("cluster") or {"eur_gbp": None}
    packed["cross"] = fold.get("cross") or {"gbpjpy": None}
    packed["information"] = fold.get("information") or {"boj_bucket": None}
    packed["chair_wires"] = chair
    ready = fold.get("sleeve_ready") or {}
    sleeve_block = dict(packed.get("sleeve") or {})
    for key in ("gbpjpy_a_plus_ready", "xau_dsp_shakeout_ready"):
        row = ready.get(key)
        if isinstance(row, dict):
            row = dict(row)
            row["admit"] = None
            row["never_admit_choice"] = True
        sleeve_block[key] = row
    packed["sleeve"] = sleeve_block
    surface = dict(packed.get("surface") or {})
    surface["us30_off"] = True
    packed["surface"] = surface
    sufficient = (packed.get("completeness") or {}).get("state_sufficient_for_live")
    completeness = dict(packed.get("completeness") or {})
    completeness["chair_wires"] = chair.get("source") == SOURCE
    completeness["state_sufficient_for_live"] = sufficient
    packed["completeness"] = completeness
    return packed
