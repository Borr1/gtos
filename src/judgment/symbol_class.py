"""Challenge-true asset-class map for symbol_state.v0.

Code facts only. No DXY / yields / NEWS_PROTOCOL. No send path.
"""

from __future__ import annotations

from typing import Any

from .bars import normalize_symbol

SCHEMA_HINT = "gtos.judgment.symbol_state.v0"

METALS = frozenset({"XAUUSD", "XAGUSD"})
INDEX = frozenset({"US30", "UK100", "NAS100", "SPX500", "GER40", "JP225", "EU50", "FRA40"})
CRYPTO = frozenset({"BTCUSD", "ETHUSD"})
ENERGY = frozenset({"USOIL", "UKOIL", "USOIL_CASH", "UKOIL_CASH"})
FX_CCY = frozenset({"EUR", "GBP", "USD", "JPY", "AUD", "NZD", "CAD", "CHF", "XAU", "XAG"})

# Named Challenge / 24-surface peers. Missing tape stays unassembled — never XAU.
PEERS_BY_SYMBOL: dict[str, tuple[str, ...]] = {
    "XAUUSD": ("USDJPY", "EURUSD", "XAGUSD"),
    "XAGUSD": ("XAUUSD", "USDJPY"),
    "EURUSD": ("GBPUSD", "USDJPY", "XAUUSD"),
    "GBPUSD": ("EURUSD", "USDJPY", "XAUUSD"),
    "USDJPY": ("XAUUSD", "EURUSD", "US30"),
    "EURGBP": ("EURUSD", "GBPUSD", "USDJPY"),
    "GBPJPY": ("GBPUSD", "USDJPY", "XAUUSD"),
    "EURJPY": ("EURUSD", "USDJPY", "XAUUSD"),
    "AUDJPY": ("USDJPY", "AUDUSD", "XAUUSD"),
    "CHFJPY": ("USDJPY", "USDCHF", "XAUUSD"),
    "US30": ("USDJPY", "XAUUSD", "UK100"),
    "UK100": ("US30", "GBPUSD", "XAUUSD"),
    "NAS100": ("US30", "USDJPY", "XAUUSD"),
}

PEERS_BY_CLASS: dict[str, tuple[str, ...]] = {
    "fx": ("EURUSD", "USDJPY", "XAUUSD"),
    "metal": ("USDJPY", "EURUSD"),
    "index": ("US30", "USDJPY", "XAUUSD"),
    "crypto": ("USDJPY", "US30"),
    "energy": ("US30", "USDJPY"),
    "unknown": (),
}

UNIVERSAL_BLOCKS = (
    "identity",
    "clock",
    "sessions",
    "timeframes",
    "levels",
    "news",
    "sleeve_features",
    "geometry",
    "cost",
    "occupancy",
    "governor",
    "surface",
    "completeness",
)

CLASS_SPECIFIC_FIELDS: dict[str, tuple[str, ...]] = {
    "fx": (
        "class_specific.fx.pair",
        "class_specific.fx.usd_leg",
        "class_specific.fx.usd_from_pair",
        "class_specific.fx.session_bias",
        "class_specific.fx.pip_scale",
        "class_specific.fx.relevant_news_ccys",
        "class_specific.fx.fx_session_london_fit",
        "class_specific.fx.usdjpy_tokyo_event_liquidity",
    ),
    "metal": (
        "class_specific.metal.usd_sensitivity",
        "class_specific.metal.a8_source",
        "class_specific.metal.usd_proxy_vs_xau",
        "peers.usdjpy",
    ),
    "index": (
        "class_specific.index.cash_alias",
        "class_specific.index.house_us30_off",
        "class_specific.index.session_bias",
        "class_specific.index.us30_rth_vs_eth",
    ),
    "crypto": ("class_specific.crypto.trade_surface",),
    "energy": ("class_specific.energy.weekend",),
    "unknown": (),
}

INDEX_CASH_ALIAS = {"US30": "US30.cash", "UK100": "UK100.cash"}
INDEX_NEWS_CCY = {
    "US30": ("USD", "ALL"),
    "NAS100": ("USD", "ALL"),
    "SPX500": ("USD", "ALL"),
    "UK100": ("GBP", "USD", "ALL"),
    "GER40": ("EUR", "USD", "ALL"),
    "EU50": ("EUR", "USD", "ALL"),
    "FRA40": ("EUR", "USD", "ALL"),
    "JP225": ("JPY", "USD", "ALL"),
}


def asset_class_for(symbol: str | None) -> str | None:
    sym = normalize_symbol(symbol)
    if not sym:
        return "unknown"
    from .state_choices import LEGACY, asset_class_choice

    chosen = asset_class_choice(sym)
    if chosen is not LEGACY:
        return chosen
    if sym in METALS:
        return "metal"
    if sym in INDEX:
        return "index"
    if sym in CRYPTO:
        return "crypto"
    if sym in ENERGY:
        return "energy"
    base, quote = split_pair(sym)
    if base and quote and base in FX_CCY and quote in FX_CCY and base not in {"XAU", "XAG"}:
        return "fx"
    return "unknown"


def split_pair(symbol: str | None) -> tuple[str | None, str | None]:
    sym = normalize_symbol(symbol)
    if sym in INDEX:
        return (sym, "USD" if sym not in {"UK100", "GER40", "EU50", "FRA40", "JP225"} else {
            "UK100": "GBP",
            "GER40": "EUR",
            "EU50": "EUR",
            "FRA40": "EUR",
            "JP225": "JPY",
        }[sym])
    if len(sym) == 6:
        return sym[:3], sym[3:]
    if len(sym) == 7 and sym.endswith("USD"):
        return sym[:4], "USD"
    return None, None


def usd_leg(symbol: str | None) -> str | None:
    base, quote = split_pair(symbol)
    if base is None and quote is None:
        return None
    from .state_choices import LEGACY, usd_leg_choice

    chosen = usd_leg_choice(base, quote)
    if chosen is not LEGACY:
        return chosen
    if base == "USD":
        return "base"
    if quote == "USD":
        return "quote"
    return None


def usd_from_pair_trend(symbol: str | None, trend: int | None) -> int | None:
    """Map pair H4/D1 trend onto USD strength. +1 = USD stronger. No DXY."""
    if trend not in (1, 0, -1):
        return None
    sym = normalize_symbol(symbol)
    if usd_leg(sym) == "quote":
        return -trend
    if usd_leg(sym) == "base":
        return trend
    return None


def news_currencies_for(symbol: str | None) -> tuple[str, ...]:
    """Currencies already on the landed spine. Never invent HIGH rows."""
    sym = normalize_symbol(symbol)
    asset = asset_class_for(sym)
    if asset == "metal":
        metal = "XAU" if sym.startswith("XAU") else "XAG"
        return (metal, "USD", "ALL")
    if asset == "index":
        return INDEX_NEWS_CCY.get(sym, ("USD", "ALL"))
    if asset == "crypto":
        return ("USD", "ALL")
    if asset == "energy":
        return ("USD", "ALL")
    base, quote = split_pair(sym)
    ccys = [c for c in (base, quote, "ALL") if c]
    # JPY / GBP crosses still see USD HIGH on the host spine (risk-off). Not a new protocol.
    if asset == "fx" and "USD" not in ccys:
        ccys.append("USD")
    return tuple(dict.fromkeys(ccys))


def pip_scale(symbol: str | None) -> float | None:
    asset = asset_class_for(symbol)
    if asset == "index":
        return 1.0
    if asset in {"metal", "crypto", "energy"}:
        return None
    if asset != "fx":
        return None
    _base, quote = split_pair(symbol)
    if quote == "JPY":
        return 0.01
    return 0.0001


def session_bias(symbol: str | None, named: str | None) -> str | None:
    """Label on top of gold_state sessions.named. Not invented NEWS."""
    asset = asset_class_for(symbol)
    from .state_choices import LEGACY, session_bias_choice

    chosen = session_bias_choice(normalize_symbol(symbol) if symbol else "", asset, named)
    if chosen is not LEGACY:
        return chosen
    session = named or "unknown"
    if asset == "index":
        return "ny"
    if asset == "metal":
        return session
    if asset != "fx":
        return session
    if "JPY" in normalize_symbol(symbol):
        if session in {"asia", "ny"}:
            return "tokyo_ny"
        return session
    if session == "london":
        return "london"
    return session


def peer_symbols_for(symbol: str | None) -> tuple[str, ...]:
    sym = normalize_symbol(symbol)
    named = PEERS_BY_SYMBOL.get(sym)
    if named is None:
        named = PEERS_BY_CLASS.get(asset_class_for(sym), ())
    return tuple(p for p in named if p != sym)


def cash_alias(symbol: str | None) -> str | None:
    return INDEX_CASH_ALIAS.get(normalize_symbol(symbol))


def field_map() -> dict[str, Any]:
    """Universal vs class-specific field inventory for Chair / tests."""
    return {
        "schema": SCHEMA_HINT,
        "universal": list(UNIVERSAL_BLOCKS),
        "class_specific": {k: list(v) for k, v in CLASS_SPECIFIC_FIELDS.items()},
        "peers_by_symbol": {k: list(v) for k, v in PEERS_BY_SYMBOL.items()},
        "never_invent": ["DXY", "US10Y", "TIPS", "NEWS_PROTOCOL", "order_book"],
        "gate_flow": "a_plus_sleeve_on_gate_flow",
        "sleeve_object": "gtos.judgment.sleeve.v0",
        "side_catalog": False,
        "chair_wires_apply": False,
        "chair_wires": [
            "usd_proxy_vs_xau",
            "gbpjpy_dual_leg_agree",
            "us30_rth_vs_eth",
            "usdjpy_tokyo_event_liquidity",
            "fx_session_london_fit",
            "sess.ldn_ny_overlap_vol",
            "corr.eur_gbp_usd_co_move",
            "corr.xau_vs_eur_proxy_usd",
            "tokyo_fix_window_label",
            "session.in_ldn_ny_overlap",
            "cluster.eur_gbp",
            "cross.gbpjpy",
            "information.boj_bucket",
        ],
        "never_admit_choice": True,
        "ready_choices": ["a_plus", "almost", "blocked", "null_state"],
        "identity_resid_max": 0.15,
        "boj_rate_fact": {
            "rate_pct": 1.25,
            "effective_date_utc": "2026-09-24",
            "use": "bucket_timing_only",
        },
        "boj_live": ["print", "guidance_live"],
        "gold_state_extensions": [
            "session.in_ldn_ny_overlap",
            "london_expand_range",
            "london_expand_vol",
            "london_expand_ok",
            "ny_rth_us30",
            "cluster.eur_gbp",
            "cross.gbpjpy",
            "information.boj_bucket",
            "peers.usd_proxy_vs_xau",
            "peers.xau_eur_proxy",
            "sleeve.gbpjpy_a_plus_ready",
            "sleeve.xau_dsp_shakeout_ready",
        ],
        "n_non_xau_sufficient": 45,
        "non_xau_remeasure_symbols": ["EURUSD", "USDJPY", "GBPUSD", "EURGBP", "US30"],
        "non_xau_uses_symbol_state": True,
        "us30_hard_off": True,
        "never_place": True,
    }
