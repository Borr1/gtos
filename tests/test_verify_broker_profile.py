from __future__ import annotations

import yaml

from scripts.verify_broker_profile import verify_profile


def _profile(alias_for_nas100: str = "US100.cash") -> dict:
    instruments = {}
    for symbol in ("AUDJPY", "AUDUSD", "BTCUSD", "CHFJPY", "ETHUSD", "EURGBP", "EURJPY", "EURUSD",
                   "GBPJPY", "GBPUSD", "GER40", "JP225", "NAS100", "NZDUSD", "SPX500", "UK100",
                   "UKOIL_cash", "US30_cash", "USDCAD", "USDCHF", "USDJPY", "USOIL_cash", "XAGUSD", "XAUUSD"):
        alias = alias_for_nas100 if symbol == "NAS100" else symbol
        if symbol == "GER40":
            alias = "GER40.cash"
        elif symbol == "JP225":
            alias = "JP225.cash"
        elif symbol == "SPX500":
            alias = "US500.cash"
        elif symbol == "UK100":
            alias = "UK100.cash"
        elif symbol == "UKOIL_cash":
            alias = "UKOIL.cash"
        elif symbol == "US30_cash":
            alias = "US30.cash"
        elif symbol == "USOIL_cash":
            alias = "USOIL.cash"
        instruments[symbol] = {
            "market": {
                "mt5_symbol": alias,
                "tick_size": 0.01,
                "point": 0.01,
                "digits": 2,
                "trade_tick_size": 0.01,
                "trade_tick_value": 1.0,
                "contract_size": 100.0,
                "volume_min": 0.01,
                "volume_max": 100.0,
                "volume_step": 0.01,
                "trade_stops_level": 0,
                "trade_freeze_level": 0,
            }
        }
    return {
        "profile_name": "ftmo_test",
        "runtime": {
            "profile_namespace": "ftmo_test",
            "broker_account_namespace": "ftmo_test",
        },
        "mt5": {
            "terminal_path": "C:/MT5/FTMO/terminal64.exe",
            "terminal_data_path": "C:/MT5/FTMO",
        },
        "broker_profile": {
            "expected_account": {
                "server": "FTMO-Server3",
                "company": "FTMO Global Markets Ltd",
                "currency": "USD",
                "login_sha256": "abc",
                "terminal_path": "C:/MT5/FTMO",
                "terminal_data_path": "C:/MT5/FTMO",
            }
        },
        "runtime_paths": {
            "knowledge_base_root": "knowledge_base/ftmo_test",
            "trade_records_root": "knowledge_base/ftmo_test/trade_records",
            "pipeline_state_root": "pipeline_state/ftmo_test",
            "shadow_logs_root": "shadow_logs/ftmo_test",
            "m1_data_root": "data/m1/ftmo_test",
            "tick_data_root": "data/ticks/ftmo_test",
        },
        "instruments": instruments,
    }


def test_verify_broker_profile_accepts_complete_ftmo_geometry(tmp_path):
    profile_path = tmp_path / "ftmo.yaml"
    profile_path.write_text(yaml.safe_dump(_profile(), sort_keys=False), encoding="utf-8")

    result = verify_profile(profile_path)

    assert result["ok"] is True
    assert result["issue_count"] == 0


def test_verify_broker_profile_rejects_redacted_account_alias_leak(tmp_path):
    profile_path = tmp_path / "ftmo.yaml"
    profile_path.write_text(
        yaml.safe_dump(_profile(alias_for_nas100="NDX100"), sort_keys=False),
        encoding="utf-8",
    )

    result = verify_profile(profile_path)

    assert result["ok"] is False
    assert any(issue["code"] == "redacted_account_alias_leakage" for issue in result["issues"])


def test_verify_broker_profile_reports_allowed_current_book_gaps_and_aliases(tmp_path):
    profile = _profile()
    profile["instruments"]["GER40_cash"] = {
        "market": {
            "mt5_symbol": "GER40.cash",
            "tick_size": 0.01,
            "point": 0.01,
            "digits": 2,
            "trade_tick_size": 0.01,
            "trade_tick_value": 1.0,
            "contract_size": 100.0,
            "volume_min": 0.01,
            "volume_max": 100.0,
            "volume_step": 0.01,
            "trade_stops_level": 0,
            "trade_freeze_level": 0,
        }
    }
    profile_path = tmp_path / "profile.yaml"
    profile_path.write_text(yaml.safe_dump(profile, sort_keys=False), encoding="utf-8")

    result = verify_profile(
        profile_path,
        symbols=("GER40", "GER40_cash", "AVAUSD"),
        surface="ultimate-active",
        allowed_missing_symbols=("AVAUSD",),
        allow_duplicate_broker_aliases=True,
    )

    assert result["ok"] is True
    assert result["surface"] == "ultimate-active"
    assert result["missing_symbols_allowed"] == ["AVAUSD"]
    assert result["duplicate_broker_alias_groups"] == {"GER40.CASH": ["GER40", "GER40_cash"]}
