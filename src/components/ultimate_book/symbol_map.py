"""Canonical -> broker symbol resolution for the W7 book.

The sleeve registry is broker-agnostic: on_surface uses CANONICAL names (SPX500, US30_cash, USOIL_cash,
GER40, JP225, UK100) so the same book runs on either broker. But each broker exposes those instruments
under its OWN names, declared per-instrument in the active profile as `instruments[<canonical>].market
.mt5_symbol`:

    FTMO   : SPX500 -> US500.cash,  US30_cash -> US30.cash,  USOIL_cash -> USOIL.cash, ...
    redacted_account: SPX500 -> SPX500,   US30_cash -> US30,       USOIL_cash -> USOUSD

The execution path already crosses this boundary correctly (apply_instrument_overrides sets
market.mt5_symbol, ExecutionEngine.open_trade fetches get_tick(self.symbol)=mt5_symbol). The book's
own broker crossings — the engine bar fetch (get_closed_bars) and the owner tick fetch (get_tick) —
must use the SAME map, or index/oil sleeves silently get zero bars on FTMO (canonical name not on the
broker). This builds that resolver from the merged profile config. Identity fallback (canonical==broker)
for metals/crypto and for any config without an instruments map.
"""
from __future__ import annotations

from typing import Callable

from src.utils.config import resolve_instrument_config_key


def build_broker_symbol_resolver(config: dict) -> Callable[[str], str]:
    """Return resolve(canonical)->broker_symbol from config['instruments'][k].market.mt5_symbol.

    Unknown canonical names (or a config with no instruments map) resolve to themselves, so metals/
    crypto (canonical==broker) and minimal test configs keep working unchanged.
    """
    table: dict[str, str] = {}
    instruments = (config or {}).get("instruments", {}) or {}
    has_instrument_contracts = isinstance(instruments, dict) and bool(instruments)
    if isinstance(instruments, dict):
        for key, block in instruments.items():
            if not isinstance(block, dict):
                continue
            market = block.get("market", {}) or {}
            broker = market.get("mt5_symbol")
            if isinstance(broker, str) and broker:
                table[key] = broker

    def _instrument_key(canonical: str) -> str | None:
        try:
            return resolve_instrument_config_key(config or {}, canonical)
        except Exception:
            return None

    def resolve(canonical: str) -> str:
        if canonical in table:
            return table[canonical]
        key = _instrument_key(canonical)
        if key and key in table:
            return table[key]
        return canonical

    def supports(canonical: str) -> bool:
        if not has_instrument_contracts:
            return True
        return bool(_instrument_key(canonical))

    resolve.table = table  # type: ignore[attr-defined]  # introspection for probes/tests
    resolve.supports = supports  # type: ignore[attr-defined]  # active-profile support predicate
    return resolve
