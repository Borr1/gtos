from __future__ import annotations

import math

import yaml

from src.components.ultimate_book.admission import SLEEVE_REGISTRY, TradeIntent
from src.components.ultimate_book.book_engine import effective_generation_specs
from src.components.ultimate_book.primitives import Bar, autocorr
from src.components.ultimate_book.sleeves import crypto
from src.components.ultimate_book.sleeves import registry
from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver
from src.utils.config import apply_profile_overrides


LIVE_TAGS = ("crypto", "energy_agri", "sub_xvol_pullback")


def _base_config() -> dict:
    with open("config/agent_config.yaml", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _breakout_bars(n: int = 240) -> list[Bar]:
    bars: list[Bar] = []
    price = 100.0
    for index in range(n):
        step = 2.0 if (index // 30) % 2 == 0 else 0.1
        price += step
        bars.append(Bar(price - step, price + 0.1, price - step - 0.1, price))
    close = max(bar.h for bar in bars[-20:]) + 0.5
    bars.append(Bar(bars[-1].c, close + 0.1, bars[-1].c - 0.1, close))
    return bars


def test_ethusd_surface_and_generator_are_the_same_live_crypto_rule():
    assert crypto.ON_SURFACE == ("BTCUSD", "DASHUSD", "ETHUSD")
    assert registry.BUILT["crypto"].on_surface is crypto.ON_SURFACE
    assert tuple(SLEEVE_REGISTRY["crypto"].symbols) == crypto.ON_SURFACE

    bars = _breakout_bars()
    index = len(bars) - 1
    assert autocorr(bars, index, 60) >= crypto.AC_THR
    eth = crypto.generate("ETHUSD", bars, "2026-08-11")
    btc = crypto.generate("BTCUSD", bars, "2026-08-11")
    assert isinstance(eth, TradeIntent) and isinstance(btc, TradeIntent)
    assert (eth.direction, eth.stop_dist, eth.target_dist) == (
        btc.direction,
        btc.stop_dist,
        btc.target_dist,
    )
    assert math.isclose(eth.target_dist / eth.stop_dist, crypto.TARGET_R, rel_tol=1e-12)


def test_live_generation_slots_are_ftmo_23_and_redacted_account_16_of_23():
    base = _base_config()
    specs = effective_generation_specs(base["gtos_vnext_runtime"], LIVE_TAGS)
    slots = [(spec.tag, symbol) for spec in specs for symbol in spec.on_surface]
    assert len(slots) == 23

    ftmo = build_broker_symbol_resolver(
        apply_profile_overrides(base, "operator_profile")
    )
    redacted_account = build_broker_symbol_resolver(
        apply_profile_overrides(base, "redacted_account")
    )
    assert sum(1 for _tag, symbol in slots if ftmo.supports(symbol)) == 23
    unsupported = sorted({symbol for _tag, symbol in slots if not redacted_account.supports(symbol)})
    assert sum(1 for _tag, symbol in slots if redacted_account.supports(symbol)) == 16
    assert unsupported == [
        "CORN_c",
        "COTTON_c",
        "DASHUSD",
        "XAGAUD",
        "XAGEUR",
        "XAUAUD",
        "XAUEUR",
    ]
