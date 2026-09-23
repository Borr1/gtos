"""Canonical candidate geometry helpers.

These helpers are deliberately pure: they perform no broker, account, order,
filesystem, network, or time-sensitive operations. They only keep root geometry
and nested ``trade_parameters`` in agreement after replay or generator geometry
mutations.
"""

from __future__ import annotations

import math
from typing import Any, Mapping


def _finite_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _first_present(*values: Any) -> Any:
    for value in values:
        if value not in (None, ""):
            return value
    return None


def canonicalize_candidate_geometry(
    candidate: Mapping[str, Any],
    *,
    source: str,
) -> dict[str, Any]:
    """Return a candidate with root and nested trade geometry aligned.

    Root executable geometry is authoritative when present. If root
    ``entry_price``, ``stop_loss``, ``side``/``direction``, and
    ``risk_reward_ratio``/``rr`` are finite, ``take_profit_1`` and
    ``target_reference`` are recomputed from those fields. Nested
    ``trade_parameters`` then mirrors the canonical root fields.
    """

    row = dict(candidate)
    params = row.get("trade_parameters")
    params = dict(params) if isinstance(params, Mapping) else {}

    entry = _finite_float(_first_present(row.get("entry_price"), params.get("entry_price")))
    stop = _finite_float(_first_present(row.get("stop_loss"), params.get("stop_loss")))
    rr = _finite_float(
        _first_present(
            row.get("risk_reward_ratio"),
            row.get("rr"),
            params.get("risk_reward_ratio"),
            params.get("rr"),
        )
    )
    side = str(
        _first_present(
            row.get("side"),
            row.get("direction"),
            params.get("side"),
            params.get("direction"),
        )
        or ""
    ).upper()

    risk = abs(entry - stop) if entry is not None and stop is not None else None
    target = _finite_float(
        _first_present(
            row.get("take_profit_1"),
            row.get("take_profit"),
            params.get("take_profit_1"),
            params.get("take_profit"),
            row.get("target_reference"),
            params.get("target_reference"),
        )
    )
    recomputed_target = None
    invalid_side_for_recompute = bool(side and side not in {"LONG", "SHORT"})
    if (
        entry is not None
        and stop is not None
        and rr is not None
        and risk
        and risk > 0
        and side in {"LONG", "SHORT"}
    ):
        direction = 1.0 if side == "LONG" else -1.0
        recomputed_target = entry + direction * rr * risk
        target = recomputed_target

    if entry is not None:
        row["entry_price"] = entry
        params["entry_price"] = entry
    if stop is not None:
        row["stop_loss"] = stop
        row["stop_or_invalidation"] = stop
        params["stop_loss"] = stop
        params["stop_or_invalidation"] = stop
    if rr is not None:
        row["risk_reward_ratio"] = rr
        row["rr"] = rr
        params["risk_reward_ratio"] = rr
        params["rr"] = rr
    if target is not None:
        row["take_profit_1"] = target
        row["take_profit"] = target
        row["target_reference"] = target
        params["take_profit_1"] = target
        params["take_profit"] = target
        params["target_reference"] = target
    if side:
        row["side"] = side
        params["side"] = side
        params["direction"] = side

    row["trade_parameters"] = params
    if recomputed_target is not None:
        status = "canonicalized"
    elif invalid_side_for_recompute:
        status = "canonicalized_from_available_fields_invalid_side_no_target_recompute"
    else:
        status = "canonicalized_from_available_fields"
    row["canonical_geometry_status"] = status
    row["canonical_geometry_source"] = source
    row["canonical_geometry_target_recomputed"] = recomputed_target is not None
    return row
