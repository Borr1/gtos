from types import SimpleNamespace

import pytest

from src.utils.broker_accounting import (
    BrokerDealAccountingError,
    trade_deal_cash_delta,
    trade_deals_cash_delta,
)


def test_trade_cash_includes_entry_and_exit_side_costs_and_fee():
    deals = [
        {"type": 0, "entry": 0, "profit": 0.0, "commission": -1.06, "swap": 0.0, "fee": 0.0},
        SimpleNamespace(type=1, entry=1, profit=-5.00, commission=-0.70, swap=-0.25, fee=-0.05),
    ]
    assert trade_deals_cash_delta(deals) == pytest.approx(-7.06)


def test_nontrading_balance_operation_is_not_trading_pnl():
    balance_credit = {"type": 2, "entry": 0, "profit": 1000.0, "commission": 0.0}
    assert trade_deal_cash_delta(balance_credit) == 0.0


@pytest.mark.parametrize("deal", [
    {"entry": 1, "profit": -10.0},
    {"type": "unknown", "profit": -10.0},
    {"type": 0, "profit": float("nan")},
    {"type": 1, "commission": True},
])
def test_malformed_trade_deal_refuses_instead_of_deleting_unknown_loss(deal):
    with pytest.raises(BrokerDealAccountingError):
        trade_deal_cash_delta(deal)
