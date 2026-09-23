"""Broker-account cash accounting shared by live governors and monitors.

MT5 books commission at whichever deal side the broker chooses. A daily-loss
reconstruction that sums only ``DEAL_ENTRY_OUT`` rows therefore drops entry-side
commission (and can drop fees), understating account loss. The account balance
contract is instead the cash delta of every BUY/SELL deal in the reset window:
profit + commission + swap + fee. Non-trading balance operations are excluded
and must be reconciled separately.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from typing import Any


TRADE_DEAL_TYPES = frozenset({0, 1})
_MISSING = object()


class BrokerDealAccountingError(ValueError):
    """A broker deal cannot be accounted without guessing."""


def _field(deal: Any, name: str, default: Any = _MISSING) -> Any:
    if isinstance(deal, Mapping):
        value = deal.get(name, _MISSING)
    else:
        value = getattr(deal, name, _MISSING)
    if value is _MISSING:
        if default is not _MISSING:
            return default
        raise BrokerDealAccountingError(f"missing_deal_field:{name}")
    return value


def _finite_cash(value: Any, field_name: str) -> float:
    if value is None:
        return 0.0
    if isinstance(value, bool):
        raise BrokerDealAccountingError(f"invalid_deal_cash:{field_name}:bool")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise BrokerDealAccountingError(f"invalid_deal_cash:{field_name}:{value!r}") from exc
    if not math.isfinite(result):
        raise BrokerDealAccountingError(f"nonfinite_deal_cash:{field_name}:{value!r}")
    return result


def trade_deal_cash_delta(deal: Any) -> float:
    """Return one BUY/SELL deal's account-cash delta, else zero."""

    raw_type = _field(deal, "type")
    if isinstance(raw_type, bool):
        raise BrokerDealAccountingError("invalid_deal_field:type:bool")
    try:
        deal_type = int(raw_type)
    except (TypeError, ValueError) as exc:
        raise BrokerDealAccountingError(f"invalid_deal_field:type:{raw_type!r}") from exc
    if deal_type not in TRADE_DEAL_TYPES:
        return 0.0
    return sum(
        _finite_cash(_field(deal, name, None), name)
        for name in ("profit", "commission", "swap", "fee")
    )


def trade_deals_cash_delta(deals: Iterable[Any]) -> float:
    """Return the exact BUY/SELL cash delta for an iterable of broker deals."""

    return float(sum(trade_deal_cash_delta(deal) for deal in deals))


__all__ = [
    "BrokerDealAccountingError",
    "TRADE_DEAL_TYPES",
    "trade_deal_cash_delta",
    "trade_deals_cash_delta",
]
