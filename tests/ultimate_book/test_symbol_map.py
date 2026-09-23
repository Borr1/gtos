"""BUILD-5 regression — the book crosses to the broker under mt5_symbol, not the canonical name.

Bug caught on the live FTMO terminal: index/oil sleeves (on_surface=SPX500/US30_cash/USOIL_cash/...) got
ZERO bars because the engine fetched under the canonical name, which does not exist on FTMO (the broker
exposes US500.cash/US30.cash/USOIL.cash). The fix resolves canonical->broker from instruments[].market
.mt5_symbol at the bar fetch (engine) and tick fetch (owner), while keeping intent.symbol canonical so the
execution path still resolves via apply_instrument_overrides. Metals/crypto are identity (no regression).
"""
import yaml

from src.utils.config import apply_profile_overrides
from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver
from src.components.ultimate_book.book_engine import UltimateBookLiveEngine


def _merged():
    cfg = yaml.safe_load(open("config/agent_config.yaml", encoding="utf-8"))
    return apply_profile_overrides(cfg, "operator_profile")


def test_resolver_maps_canonical_to_ftmo_broker_names():
    r = build_broker_symbol_resolver(_merged())
    # the exact mismatches the live probe exposed
    assert r("SPX500") == "US500.cash"
    assert r("US30_cash") == "US30.cash"
    assert r("USOIL_cash") == "USOIL.cash"
    assert r("UKOIL_cash") == "UKOIL.cash"
    assert r("GER40") == "GER40.cash"
    assert r("JP225") == "JP225.cash"
    assert r("UK100") == "UK100.cash"
    assert r("NAS100") == "US100.cash"
    # Market-expansion D1 uses cash-index canonical aliases; these must reuse the same
    # broker-native specs instead of falling through to nonexistent identity names.
    assert r("GER40_cash") == "GER40.cash"
    assert r("JP225_cash") == "JP225.cash"
    assert r("US100_cash") == "US100.cash"
    assert r("US500_cash") == "US500.cash"
    # metals/crypto are identity (canonical == broker)
    assert r("XAUUSD") == "XAUUSD"
    assert r("BTCUSD") == "BTCUSD"


def test_resolver_maps_redacted_account_broker_specific_names():
    cfg = yaml.safe_load(open("config/agent_config.yaml", encoding="utf-8"))
    merged = apply_profile_overrides(cfg, "redacted_account")
    r = build_broker_symbol_resolver(merged)

    assert r("GER40") == "GER30"
    assert r("GER40_cash") == "GER30"
    assert r("JP225") == "JP225"
    assert r("JP225_cash") == "JP225"
    assert r("NAS100") == "NDX100"
    assert r("US100_cash") == "NDX100"
    assert r("SPX500") == "SPX500"
    assert r("US500_cash") == "SPX500"
    assert r("US30_cash") == "US30"
    assert r("USOIL_cash") == "USOUSD"
    assert r("UKOIL_cash") == "UKOUSD"


def test_resolver_supports_tracks_profile_symbol_availability():
    ftmo = build_broker_symbol_resolver(_merged())
    cfg = yaml.safe_load(open("config/agent_config.yaml", encoding="utf-8"))
    redacted_account = build_broker_symbol_resolver(apply_profile_overrides(cfg, "redacted_account"))

    assert ftmo.supports("AVAUSD") is True
    assert ftmo.supports("US500_cash") is True
    assert redacted_account.supports("US500_cash") is True
    assert redacted_account.supports("CADJPY") is True
    assert redacted_account.supports("AVAUSD") is False
    assert redacted_account.supports("XPDUSD") is False


def test_resolver_identity_without_instruments():
    r = build_broker_symbol_resolver({})           # minimal/test config
    assert r("SPX500") == "SPX500" and r("XAUUSD") == "XAUUSD"
    assert r.supports("BTCUSD") is True


class _RecordingMT5:
    """Captures the symbol names the engine actually asks the broker for."""
    def __init__(self):
        self.requested = []
    def get_candles(self, symbol, tf, count):
        self.requested.append(symbol)
        return []      # no bars -> no intents; we only assert the NAME crossing here
    def get_account_equity(self):
        return 100000.0


def test_engine_fetches_under_broker_names():
    r = build_broker_symbol_resolver(_merged())
    rec = _RecordingMT5()
    eng = UltimateBookLiveEngine({}, rec, ".", namespace="t", broker_symbol=r)
    eng.evaluate(tags=("idxrev", "energy_agri", "crypto"))
    # indices/oil must be requested under the .cash broker names, NEVER the canonical ones
    assert "US500.cash" in rec.requested and "SPX500" not in rec.requested
    assert "US30.cash" in rec.requested and "US30_cash" not in rec.requested
    assert "USOIL.cash" in rec.requested and "USOIL_cash" not in rec.requested
    # crypto stays identity
    assert "BTCUSD" in rec.requested
