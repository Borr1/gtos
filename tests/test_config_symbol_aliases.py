from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from src.components.verification import _sl_beyond_floor
from src.utils.config import (
    apply_instrument_overrides,
    apply_profile_overrides,
    resolve_instrument_config_key,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
AGENT_CONFIG = PROJECT_ROOT / "config" / "agent_config.yaml"


def _agent_config() -> dict:
    with AGENT_CONFIG.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.mark.parametrize(
    "raw_symbol,expected_key,expected_mt5,expected_tick,expected_format",
    [
        ("US30.cash", "US30_cash", "US30.cash", 0.01, ".2f"),
        ("US30_cash", "US30_cash", "US30.cash", 0.01, ".2f"),
        ("US30", "US30_cash", "US30.cash", 0.01, ".2f"),
        ("YM", "US30_cash", "US30.cash", 0.01, ".2f"),
        ("YMM26-CME", "US30_cash", "US30.cash", 0.01, ".2f"),
        ("XAGUSD", "XAGUSD", None, 0.001, ".3f"),
        ("XAGUSD_SI", "XAGUSD", None, 0.001, ".3f"),
        ("SI", "XAGUSD", None, 0.001, ".3f"),
        ("SIM26-CME", "XAGUSD", None, 0.001, ".3f"),
        ("GCM26-CME", "XAUUSD", None, 0.01, ".2f"),
        ("NQM26-CME", "NAS100", None, 0.01, ".1f"),
        ("6EM26-CME", "EURUSD", None, 0.00001, ".5f"),
        ("6BM26-CME", "GBPUSD", None, 0.00001, ".5f"),
        ("6JM26-CME", "USDJPY", None, 0.001, ".3f"),
    ],
)
def test_apply_instrument_overrides_resolves_vnext_symbol_aliases(
    raw_symbol: str,
    expected_key: str,
    expected_mt5: str | None,
    expected_tick: float,
    expected_format: str,
):
    cfg = _agent_config()

    assert resolve_instrument_config_key(cfg, raw_symbol) == expected_key

    resolved = apply_instrument_overrides(cfg, raw_symbol)
    assert resolved["market"]["symbol"] == expected_key
    if raw_symbol != expected_key:
        assert resolved["market"]["requested_symbol"] == raw_symbol
        assert resolved["market"]["symbol_family"].endswith("_FAMILY")
    if expected_mt5 is not None:
        assert resolved["market"]["mt5_symbol"] == expected_mt5
    assert resolved["market"]["tick_size"] == pytest.approx(expected_tick)
    assert resolved["prompt"]["price_format"] == expected_format
    assert _sl_beyond_floor(price=1.0, config=resolved) >= expected_tick


def test_spx500_es_family_alias_is_ready_when_config_profile_exists():
    cfg = {
        "market": {"symbol": "XAUUSD", "tick_size": 0.01},
        "risk": {"max_spread_cents": 1},
        "prompt": {"price_format": ".2f"},
        "instruments": {
            "SPX500": {
                "market": {"symbol": "SPX500", "tick_size": 0.25},
                "risk": {"max_spread_cents": 500},
                "prompt": {"price_format": ".2f"},
            },
        },
    }

    assert resolve_instrument_config_key(cfg, "ESM26-CME") == "SPX500"
    assert resolve_instrument_config_key(cfg, "MESM26-CME") == "SPX500"

    resolved = apply_instrument_overrides(cfg, "ESM26-CME")
    assert resolved["market"]["symbol"] == "SPX500"
    assert resolved["market"]["requested_symbol"] == "ESM26-CME"
    assert resolved["market"]["symbol_family"] == "SPX500_ES_FAMILY"
    assert resolved["market"]["tick_size"] == pytest.approx(0.25)
    assert resolved["risk"]["max_spread_cents"] == 500


def test_unknown_symbol_still_fails_with_available_config_keys():
    cfg = _agent_config()

    with pytest.raises(ValueError) as excinfo:
        apply_instrument_overrides(cfg, "UNKNOWN_ALIAS")

    message = str(excinfo.value)
    assert "No instrument config for 'UNKNOWN_ALIAS'" in message
    assert "US30_cash" in message


def test_redacted_account_profile_pins_current_broker_native_aliases_and_specs():
    cfg = apply_profile_overrides(_agent_config(), "redacted_account")

    expected = {
        "GER40": ("GER30", 0.01),
        "NAS100": ("NDX100", 0.01),
        "UKOIL_cash": ("UKOUSD", 0.001),
        "US30_cash": ("US30", 0.01),
        "USOIL_cash": ("USOUSD", 0.001),
    }
    for symbol, (broker_symbol, tick_size) in expected.items():
        resolved = apply_instrument_overrides(cfg, symbol)
        assert resolved["market"]["symbol"] == symbol
        assert resolved["market"]["mt5_symbol"] == broker_symbol
        assert resolved["market"]["tick_size"] == pytest.approx(tick_size)
