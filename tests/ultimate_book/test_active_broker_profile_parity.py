import yaml

from src.components.ultimate_book.admission import resolve_market_expansion_sleeves
from src.components.ultimate_book.sleeves.registry import active_specs
from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver
from src.utils.config import apply_profile_overrides, resolve_instrument_config_key


def _base_config():
    with open("config/agent_config.yaml", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _active_book_symbols():
    cfg = _base_config()
    rt = cfg["gtos_vnext_runtime"]
    expansion_sleeves, error = resolve_market_expansion_sleeves(
        policy=rt["ultimate_book_market_expansion_policy"],
        explicit_sleeves=rt.get("ultimate_book_market_expansion_sleeves") or [],
    )
    assert error is None
    specs = active_specs(
        None,
        include_candidate_book=rt["ultimate_book_include_candidate_book"],
        candidate_book_sleeves=rt["ultimate_book_candidate_book_sleeves"],
        include_market_expansion_book=rt["ultimate_book_include_market_expansion_book"],
        market_expansion_sleeves=expansion_sleeves,
    )
    return sorted({symbol for spec in specs for symbol in spec.on_surface})


def test_active_book_ftmo_profile_supports_every_active_symbol():
    cfg = apply_profile_overrides(_base_config(), "operator_profile")
    resolver = build_broker_symbol_resolver(cfg)

    unsupported = [
        symbol for symbol in _active_book_symbols()
        if resolve_instrument_config_key(cfg, symbol) is None
    ]
    assert unsupported == []
    assert resolver("GER40_cash") == "GER40.cash"
    assert resolver("JP225_cash") == "JP225.cash"
    assert resolver("US100_cash") == "US100.cash"
    assert resolver("US500_cash") == "US500.cash"


def test_active_book_redacted_account_profile_supports_known_available_subset_only():
    cfg = apply_profile_overrides(_base_config(), "redacted_account")
    resolver = build_broker_symbol_resolver(cfg)

    unsupported = [
        symbol for symbol in _active_book_symbols()
        if resolve_instrument_config_key(cfg, symbol) is None
    ]
    assert unsupported == [
        "AVAUSD",
        "CORN_c",
        "COTTON_c",
        "DASHUSD",
        "XAGAUD",
        "XAGEUR",
        "XAUAUD",
        "XAUEUR",
        "XPDUSD",
        "XTZUSD",
    ]
    assert resolver("GER40_cash") == "GER30"
    assert resolver("JP225_cash") == "JP225"
    assert resolver("US100_cash") == "NDX100"
    assert resolver("US500_cash") == "SPX500"
    assert resolver("CADJPY") == "CADJPY"
    assert resolver("NZDJPY") == "NZDJPY"


def test_redacted_account_profile_uses_verified_vps_portable_terminal_paths():
    cfg = apply_profile_overrides(_base_config(), "redacted_account")

    assert cfg["mt5"]["terminal_path"] == r"C:\MT5\redacted_account\terminal64.exe"
    assert cfg["mt5"]["terminal_data_path"] == r"C:\MT5\redacted_account"
    assert cfg["mt5"]["portable"] is True
    expected = cfg["broker_profile"]["expected_account"]
    assert expected["terminal_path"] == r"C:\MT5\redacted_account"
    assert expected["terminal_data_path"] == r"C:\MT5\redacted_account"
