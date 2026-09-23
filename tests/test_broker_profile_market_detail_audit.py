from scripts.audit_broker_profile_market_details import (
    audit_symbol,
    finalize_profile_result,
)


class _Resolver:
    def __call__(self, symbol):
        return {"GER40_cash": "GER40.cash"}.get(symbol, symbol)

    @staticmethod
    def supports(symbol):
        return symbol != "AVAUSD"


class _SymbolInfo:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class _MT5:
    def symbol_info(self, symbol):
        if symbol == "GER40.cash":
            return _SymbolInfo(
                name=symbol,
                digits=2,
                point=0.01,
                trade_tick_size=0.01,
                trade_tick_value=1.0,
                trade_contract_size=1.0,
                volume_min=0.01,
                volume_max=100.0,
                volume_step=0.01,
                trade_stops_level=0,
                trade_freeze_level=0,
                trade_mode=4,
                visible=True,
                swap_long=-1.0,
                swap_short=-1.0,
            )
        return None

    def symbol_info_tick(self, symbol):
        return _SymbolInfo(bid=100.0, ask=100.2, time=1, time_msc=1000)


def test_audit_symbol_accepts_matching_static_market_fields():
    profile = {
        "instruments": {
            "GER40_cash": {
                "market": {
                    "mt5_symbol": "GER40.cash",
                    "digits": 2,
                    "point": 0.01,
                    "trade_tick_size": 0.01,
                    "trade_tick_value": 1.0,
                    "contract_size": 1.0,
                    "volume_min": 0.01,
                    "volume_max": 100.0,
                    "volume_step": 0.01,
                    "trade_stops_level": 0,
                    "trade_freeze_level": 0,
                    "trade_mode": 4,
                }
            }
        }
    }

    row = audit_symbol(
        profile_name="ftmo",
        profile=profile,
        symbol="GER40_cash",
        resolver=_Resolver(),
        mt5_module=_MT5(),
        allowed_missing=set(),
    )

    assert row["status"] == "ok"
    assert row["issues"] == []
    assert row["tick_quality_without_symbol_select"] == "positive_quote"


def test_audit_symbol_reports_static_mismatch_as_issue():
    profile = {
        "instruments": {
            "GER40_cash": {
                "market": {
                    "mt5_symbol": "GER40.cash",
                    "digits": 3,
                    "point": 0.01,
                    "trade_tick_size": 0.01,
                    "trade_tick_value": 1.0,
                    "contract_size": 1.0,
                    "volume_min": 0.01,
                    "volume_max": 100.0,
                    "volume_step": 0.01,
                    "trade_stops_level": 0,
                    "trade_freeze_level": 0,
                    "trade_mode": 4,
                }
            }
        }
    }

    row = audit_symbol(
        profile_name="ftmo",
        profile=profile,
        symbol="GER40_cash",
        resolver=_Resolver(),
        mt5_module=_MT5(),
        allowed_missing=set(),
    )

    assert row["status"] == "issues"
    assert any(item["code"] == "profile_live_static_field_mismatch" for item in row["issues"])


def test_allowed_unsupported_symbol_is_not_hard_issue():
    row = audit_symbol(
        profile_name="redacted_account",
        profile={"instruments": {}},
        symbol="AVAUSD",
        resolver=_Resolver(),
        mt5_module=_MT5(),
        allowed_missing={"AVAUSD"},
    )
    assert row["status"] == "unsupported_allowed"
    assert row["issues"] == []


def test_finalize_profile_result_counts_unexpected_unsupported():
    result = finalize_profile_result(
        {
            "symbols": [
                {"symbol": "AVAUSD", "supported": False, "status": "unsupported_allowed"},
                {
                    "symbol": "GER40_cash",
                    "supported": False,
                    "status": "unsupported_unexpected",
                    "issues": [{"code": "unsupported_active_symbol_unexpected"}],
                    "warnings": [],
                },
            ],
            "issues": [{"code": "unsupported_active_symbol_unexpected"}],
            "warnings": [],
        }
    )
    assert result["ok"] is False
    assert result["summary"]["unsupported_symbol_count"] == 2
    assert result["summary"]["unexpected_unsupported_symbols"] == ["GER40_cash"]
