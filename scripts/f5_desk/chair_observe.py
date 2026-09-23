"""Build a truthful F5 chair card from a snapshot dict. No MT5. No I/O.

A snapshot is plain data the VPS I/O layer already fetched. This module is
what ``judge_eia_fills`` and ``vps_live_now`` TICK lines were trying to be:
R vs the original stop, day-net vs the 22:00 baseline, tape age, occupancy.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional

from scripts.f5_desk import chair_card as card


def _f(value: object) -> Optional[float]:
    try:
        out = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return out


def orig_sl_for_position(
    side: str,
    entry: object,
    live_sl: object,
    stored: object = None,
    stop_prev: object = None,
) -> Optional[float]:
    """Prefer a stored / slate ``stop_prev`` risk-side stop over the live lock."""
    return card.latch_orig_sl(side, entry, live_sl, stored if stored is not None else stop_prev)


def path_card(
    position: Mapping[str, Any],
    *,
    orig_sl: object = None,
    tick: Mapping[str, Any] | None = None,
    now_unix: object = None,
) -> dict[str, Any]:
    """One ticket. ``r_orig`` is the only R the chair may read."""
    side = str(position.get("side") or position.get("direction") or "").upper()
    entry = _f(position.get("entry") or position.get("entry_price") or position.get("price_open"))
    live_sl = _f(position.get("sl") or position.get("stop_now") or position.get("stop_loss"))
    tp = _f(position.get("tp") or position.get("take_profit_1"))
    mark = _f((tick or {}).get("mark") if tick is not None else None)
    if mark is None:
        mark = _f(position.get("mark") or position.get("price_current"))
    stored = orig_sl if orig_sl is not None else position.get("orig_sl")
    stop_prev = position.get("stop_prev")
    resolved = orig_sl_for_position(side, entry, live_sl, stored, stop_prev)
    r_orig = card.r_versus_original(side, entry, resolved, mark) if (
        entry is not None and resolved is not None and mark is not None
    ) else None
    r_to_tp = card.r_versus_original(side, entry, resolved, tp) if (
        entry is not None and resolved is not None and tp is not None
    ) else None
    locked_r = card.r_versus_original(side, entry, resolved, live_sl) if (
        entry is not None and resolved is not None and live_sl is not None
    ) else None
    age = card.tick_age_s((tick or {}).get("time_unix"), now_unix) if tick else None
    sleeve = str(position.get("sleeve") or "")
    digits = position.get("digits")
    if digits is None and tick is not None:
        digits = tick.get("digits")
    try:
        digits = int(digits) if digits is not None else None
    except (TypeError, ValueError):
        digits = None
    return {
        "ticket": position.get("ticket"),
        "symbol": card.norm_symbol(position.get("symbol")),
        "sleeve": sleeve,
        "side": side,
        "lots": _f(position.get("lots") or position.get("volume") or position.get("current_volume")),
        "entry": entry,
        "orig_sl": resolved,
        "live_sl": live_sl,
        "tp": tp,
        "mark": mark,
        "digits": digits,
        "profit_usd": _f(position.get("profit") or position.get("profit_usd")),
        "r_orig": r_orig,
        "r_to_tp": r_to_tp,
        "locked_r": locked_r,
        "tick_age_s": age,
        "tape": card.tape_state(age),
        "fast_family": card.is_fast_family(sleeve),
        "null_rule": card.is_null_rule(sleeve),
    }


def book_card(
    account: Mapping[str, Any],
    positions: Iterable[Mapping[str, Any]],
    *,
    baseline: object,
    ticks: Mapping[str, Mapping[str, Any]] | None = None,
    orig_ledger: Mapping[str, Any] | None = None,
    now_unix: object = None,
    orders: Iterable[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Account + paths. Day-net is balance now minus the 22:00 baseline."""
    balance = _f(account.get("balance"))
    occupied = set()
    paths = []
    ticks = ticks or {}
    orig_ledger = orig_ledger or {}
    for pos in positions:
        sym = card.norm_symbol(pos.get("symbol"))
        if sym:
            occupied.add(sym)
        ticket = pos.get("ticket")
        stored = None
        if ticket is not None and str(ticket) in orig_ledger:
            stored = orig_ledger[str(ticket)]
        elif ticket is not None and ticket in orig_ledger:
            stored = orig_ledger[ticket]
        tick = ticks.get(sym) or ticks.get(str(pos.get("symbol") or ""))
        paths.append(path_card(pos, orig_sl=stored, tick=tick, now_unix=now_unix))
    for order in orders:
        sym = card.norm_symbol(order.get("symbol"))
        if sym:
            occupied.add(sym)
    return {
        "login": account.get("login"),
        "balance": balance,
        "equity": _f(account.get("equity")),
        "day_net": card.day_net(balance, baseline) if balance is not None else None,
        "to_pass": card.to_pass(balance, card.pass_balance_for_login(account.get("login"))) if balance is not None else None,
        "positions": paths,
        "occupied": sorted(occupied),
        "pending": list(orders),
        "fast_family_live": any(
            p.get("fast_family") and p.get("tape") == "live" for p in paths
        ),
    }
