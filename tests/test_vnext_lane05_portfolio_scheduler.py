from types import SimpleNamespace

import src.components.permissions as permissions
from src.mt5.mt5_interface import MAGIC_NUMBER


def _governed_vnext_trade(direction: str = "LONG"):
    return SimpleNamespace(
        trade_parameters=SimpleNamespace(
            direction=direction,
            gtos_vnext_production_execution_path=True,
            gtos_vnext_dynamic_policy_applied=True,
            gtos_vnext_dynamic_policy_selected="partial_be_runner",
            gtos_vnext_execution_policy_id="partial_be_runner",
            gtos_vnext_selected_cell_risk_pct=0.25,
            gtos_vnext_selected_cell_risk_cell_id="risk-cell-lane05",
        )
    )


def test_selected_cell_vnext_trade_bypasses_legacy_concurrent_count_cap(monkeypatch):
    def fail_if_legacy_counter_runs(_mt5):
        raise AssertionError("legacy count cap must be evidence-only for governed vNext")

    monkeypatch.setattr(permissions, "get_filled_position_count", fail_if_legacy_counter_runs)

    denial = permissions._reject_if_concurrent_cap_reached(
        SimpleNamespace(),
        {"risk": {"max_concurrent": 1, "risk_per_trade_pct": 2.0}},
        trade_params=_governed_vnext_trade(),
    )

    assert denial is None


def test_non_vnext_trade_still_uses_legacy_concurrent_count_cap(monkeypatch):
    monkeypatch.setattr(permissions, "get_filled_position_count", lambda _mt5: 2)

    denial = permissions._reject_if_concurrent_cap_reached(
        SimpleNamespace(),
        {"risk": {"max_concurrent": 1, "risk_per_trade_pct": 2.0}},
        trade_params=SimpleNamespace(trade_parameters=SimpleNamespace()),
    )

    assert denial is not None
    assert denial.reason == "concurrent_cap_reached"
    assert denial.details == {"filled_positions": 2, "max_concurrent": 1}


def test_governed_vnext_same_symbol_position_conflict_is_explicit_ticket_guard():
    class MT5:
        def __init__(self):
            self.queries = []

        def get_positions(self, symbol):
            self.queries.append(symbol)
            return [
                SimpleNamespace(
                    ticket=241779188,
                    symbol="NDX100",
                    type=0,
                    volume=0.1,
                    price_open=21300.0,
                    sl=21200.0,
                    tp=21500.0,
                    magic=MAGIC_NUMBER,
                )
            ]

    mt5 = MT5()
    denial = permissions._reject_if_same_symbol_vnext_lifecycle_conflict(
        mt5,
        "NAS100",
        {"market": {"symbol": "NAS100"}},
        _governed_vnext_trade(direction="SHORT"),
    )

    assert denial is not None
    assert denial.reason == "same_symbol_lifecycle_v4_hedge_conflict_rejected"
    assert denial.details["selected_cell_risk_pct"] == 0.25
    assert denial.details["selected_policy"] == "partial_be_runner"
    assert denial.details["execution_policy_id"] == "partial_be_runner"
    packet = denial.details["same_symbol_lifecycle_v4"]
    assert packet["candidate"]["side"] == "SHORT"
    assert packet["open_position_snapshot"][0]["ticket"] == 241779188
    assert "NDX100" in denial.details["symbol_aliases_checked"]
    assert mt5.queries
