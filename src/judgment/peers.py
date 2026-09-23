"""Named XAU peers for gold_state. USDJPY only. Never invent DXY / yields / OB."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from .bars import (
    XAU_PEER_SYMBOLS,
    StampedBar,
    books_for_symbol,
    last_closed_at_or_before,
    normalize_symbol,
    tf_snap,
)

USDJPY_PEER_FIELDS = (
    "present",
    "m15_atr14",
    "h4_trend",
    "xau_usdjpy_comove_20",
    "atr_ratio",
    "source",
)

_EMPTY_USDJPY = {
    "present": False,
    "m15_atr14": None,
    "h4_trend": None,
    "xau_usdjpy_comove_20": None,
    "atr_ratio": None,
    "source": "unassembled",
}


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
    if not math.isfinite(value):
        return None
    return value


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
    """Last n closes that share the same UTC stamp on both tapes. Missing → None."""
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


def xau_usdjpy_comove_20(
    xau_m15: Sequence[StampedBar] | None,
    usdjpy_m15: Sequence[StampedBar] | None,
    as_of_utc: datetime,
) -> float | None:
    """Pearson of 20 aligned M15 simple returns. Short/unaligned tape stays None."""
    packed = aligned_closes(xau_m15, usdjpy_m15, as_of_utc, 21)
    if packed is None:
        return None
    rx = _simple_returns(packed[0])
    ry = _simple_returns(packed[1])
    if rx is None or ry is None or len(rx) != 20:
        return None
    return _pearson(rx, ry)


def _peer_books_from(peer_books: Mapping[str, Any] | None) -> Mapping[str, Any] | None:
    if not peer_books:
        return None
    return peer_books.get("USDJPY") or peer_books.get("usdjpy")


def peer_books_for_xau(cache: dict | None = None) -> dict[str, dict[str, list[StampedBar]]]:
    """Named peer set from Challenge CSVs via books_for_symbol. Never invents bars."""
    out: dict[str, dict[str, list[StampedBar]]] = {}
    for peer in XAU_PEER_SYMBOLS:
        loaded = books_for_symbol(peer, cache)
        if loaded:
            out[peer] = loaded
    return out


def empty_usdjpy(*, source: str = "unassembled") -> dict[str, Any]:
    row = dict(_EMPTY_USDJPY)
    row["source"] = source
    return row


def assemble_peers_block(
    *,
    symbol: str,
    as_of_utc: datetime,
    books: Mapping[str, list[StampedBar]] | None = None,
    peer_books: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Always emit peers.usdjpy. Missing metrics stay visible null. No DXY/yields/OB."""
    if normalize_symbol(symbol) != "XAUUSD":
        return {"usdjpy": empty_usdjpy(source="not_xau_primary")}

    usdjpy = _peer_books_from(peer_books)
    if not usdjpy:
        return {"usdjpy": empty_usdjpy(source="unassembled")}

    m15_rows = usdjpy.get("m15") or []
    h4_rows = usdjpy.get("h4") or []
    m15 = tf_snap(m15_rows, as_of_utc, "M15") if m15_rows else None
    h4 = tf_snap(h4_rows, as_of_utc, "H4", lookback=30) if h4_rows else None
    present = bool(m15 or h4)
    if not present:
        return {"usdjpy": empty_usdjpy(source="unassembled")}

    xau_m15_rows = (books or {}).get("m15") or []
    xau_m15 = tf_snap(xau_m15_rows, as_of_utc, "M15") if xau_m15_rows else None
    xau_atr = (xau_m15 or {}).get("atr14") if xau_m15 else None
    jpy_atr = (m15 or {}).get("atr14") if m15 else None
    atr_ratio = None
    if xau_atr and jpy_atr and jpy_atr > 0:
        atr_ratio = xau_atr / jpy_atr

    return {
        "usdjpy": {
            "present": True,
            "m15_atr14": jpy_atr,
            "h4_trend": (h4 or {}).get("trend") if h4 else None,
            "xau_usdjpy_comove_20": xau_usdjpy_comove_20(xau_m15_rows, m15_rows, as_of_utc),
            "atr_ratio": atr_ratio,
            "source": "challenge_csv",
        }
    }
