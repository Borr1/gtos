"""Round-turn commission from one account's own deals.

Same fit as ``scripts/build_broker_true_costs.py`` ``derive_commission``: a position
with no closing deal is excluded, because an entry-only charge is half a round turn
on a broker that bills both sides. A symbol with no closed round turn stays unset.
Nothing here is a stand-in rate.
"""

from __future__ import annotations

import math
import statistics
from typing import Any


def _field(deal: Any, name: str) -> Any:
    if isinstance(deal, dict):
        return deal.get(name)
    return getattr(deal, name, None)


def _float(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def _dispersion_pct(values: list[float]) -> float:
    high = max(values)
    low = min(values)
    if high == low:
        return 0.0
    med = statistics.median(values)
    if med == 0:
        return math.inf
    return 100.0 * (high - low) / abs(med)


def fit_symbol_commission(
    deals: Any,
    symbol: str,
    contract_size: float | None,
) -> dict[str, Any]:
    """Fit one symbol's round-turn schedule from closed deals, or say why not.

    ``status`` is ``captured`` only when at least one closed round turn priced.
    ``no_closed_round_turn`` leaves the rate unset. ``contract_size`` means the
    per-lot readings disagree and notional basis points cannot be fit, so the
    kind is unknown and the rate stays unset.
    """

    wanted = str(symbol)
    rows: list[dict[str, float]] = []
    entry_comm = 0.0
    exit_comm = 0.0
    by_pos: dict[Any, list[Any]] = {}
    for deal in deals or ():
        if str(_field(deal, "symbol") or "") != wanted:
            continue
        kind = _float(_field(deal, "type"))
        if kind not in (0.0, 1.0):
            continue
        position_id = _field(deal, "position_id")
        if position_id is None:
            continue
        by_pos.setdefault(position_id, []).append(deal)

    for deals_for_position in by_pos.values():
        entries = [d for d in deals_for_position if _float(_field(d, "entry")) == 0.0]
        exits = [d for d in deals_for_position if _float(_field(d, "entry")) == 1.0]
        entry_values = [_float(_field(d, "commission")) for d in entries]
        exit_values = [_float(_field(d, "commission")) for d in exits]
        if any(v is None for v in entry_values + exit_values):
            continue
        entry_comm += sum(v or 0.0 for v in entry_values)
        exit_comm += sum(v or 0.0 for v in exit_values)
        if not entries or not exits:
            continue
        volume = sum(_float(_field(d, "volume")) or 0.0 for d in entries)
        price = _float(_field(entries[0], "price"))
        if volume <= 0 or price is None or price <= 0:
            continue
        commission = -sum((v or 0.0) for v in entry_values + exit_values)
        row = {"per_lot": commission / volume, "price": price, "volume": volume}
        size = _float(contract_size)
        if size is not None and size > 0:
            row["notional_bp"] = commission / (volume * size * price) * 1e4
        rows.append(row)

    if not rows:
        return {"status": "no_closed_round_turn", "symbol": wanted}

    if exit_comm == 0:
        charge_side = "entry_only"
    elif entry_comm != 0:
        charge_side = "both_sides"
    else:
        charge_side = "exit_only"

    per_lot = [row["per_lot"] for row in rows]
    if all(value == 0 for value in per_lot):
        return {
            "status": "captured",
            "symbol": wanted,
            "kind": "zero",
            "value": 0.0,
            "n_round_turns": len(rows),
            "charge_side": charge_side,
        }

    bp_values = [row["notional_bp"] for row in rows if "notional_bp" in row]
    if len(bp_values) != len(rows):
        if max(per_lot) != min(per_lot):
            return {
                "status": "contract_size",
                "symbol": wanted,
                "n_round_turns": len(rows),
                "charge_side": charge_side,
            }
        kind, value = "per_lot", statistics.median(per_lot)
    else:
        lot_flat = max(per_lot) == min(per_lot)
        bp_flat = max(bp_values) == min(bp_values)
        if lot_flat or (
            not bp_flat and _dispersion_pct(per_lot) <= _dispersion_pct(bp_values)
        ):
            kind, value = "per_lot", statistics.median(per_lot)
        else:
            kind, value = "notional_bp", statistics.median(bp_values)
    return {
        "status": "captured",
        "symbol": wanted,
        "kind": kind,
        "value": float(value),
        "n_round_turns": len(rows),
        "charge_side": charge_side,
    }
