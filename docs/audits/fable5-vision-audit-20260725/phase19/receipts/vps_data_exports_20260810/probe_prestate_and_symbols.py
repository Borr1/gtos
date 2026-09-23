"""READ-ONLY MT5 probe for the 2026-08-10 data-export + FN-universe session.

Connects to each terminal in turn and reports:
  1. account state (login hash, equity, positions, pending orders)  -> T0 prestate / T3 flat gate
  2. resolution of the T1 deep-H4 target symbols                    -> T1
  3. resolution of the T2 slippage-capture symbols                  -> T2
  4. FULL symbol_info for the T3 redacted_account-missing symbols         -> T3 (broker-true specs)

NO orders. NO symbol_select persistence beyond what MT5 already does for reads.
Placed under receipts so the probe itself is committed evidence.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone

import MetaTrader5 as mt5

TERMINALS = {
    "ftmo": r"C:\MT5\FTMO\terminal64.exe",
    "redacted_account": r"C:\MT5\redacted_account\terminal64.exe",
}

# T1: the five symbols the Mac's W7 recost is blocked on (canonical file_symbol)
T1_FILE_SYMBOLS = ["CORN_c", "COTTON_c", "EU50_cash", "FRA40_cash", "US2000_cash"]

# T2: reconciled price-domain slippage samples
T2_SYMBOLS = ["AUDJPY", "CHFJPY", "EURJPY", "UKOIL_cash", "USOIL_cash", "XAGUSD"]

# T3: the symbols redacted_account skips on profile_missing_instrument_config
T3_SYMBOLS = ["DASHUSD", "XAUEUR", "XAGEUR", "XAUAUD", "XAGAUD", "CORN_c", "COTTON_c"]

# candidate broker spellings to try for a canonical name, in order
CANDIDATES = {
    "CORN_c": ["CORN_c", "CORN.c", "CORN", "CORNc", "ZC", "CORN.spot"],
    "COTTON_c": ["COTTON_c", "COTTON.c", "COTTON", "COTTONc", "CT"],
    "EU50_cash": ["EU50_cash", "EU50.cash", "EU50", "EUSTX50", "STOXX50", "SX5E", "ESTX50"],
    "FRA40_cash": ["FRA40_cash", "FRA40.cash", "FRA40", "CAC40", "FCE", "FR40"],
    "US2000_cash": ["US2000_cash", "US2000.cash", "US2000", "RUSSELL2000", "RUT", "US2000Roll"],
    "UKOIL_cash": ["UKOIL_cash", "UKOIL.cash", "UKOIL", "UKOUSD", "BRENT", "XBRUSD"],
    "USOIL_cash": ["USOIL_cash", "USOIL.cash", "USOIL", "USOUSD", "WTI", "XTIUSD"],
    "AUDJPY": ["AUDJPY"],
    "CHFJPY": ["CHFJPY"],
    "EURJPY": ["EURJPY"],
    "XAGUSD": ["XAGUSD"],
    "DASHUSD": ["DASHUSD", "DASH", "DSHUSD", "DASHUSDT"],
    "XAUEUR": ["XAUEUR"],
    "XAGEUR": ["XAGEUR"],
    "XAUAUD": ["XAUAUD"],
    "XAGAUD": ["XAGAUD"],
}

# substring patterns used to sweep the full broker symbol list when a name misses
SWEEP = ["CORN", "COTTON", "EU50", "STOXX", "SX5", "ESTX", "FRA", "CAC", "FR40",
         "US2000", "RUSSELL", "RUT", "OIL", "WTI", "BRENT", "XTI", "XBR",
         "DASH", "XAUEUR", "XAGEUR", "XAUAUD", "XAGAUD"]

# every field MT5 exposes on SymbolInfo that matters for an instrument config
SPEC_FIELDS = [
    "name", "description", "path", "currency_base", "currency_profit", "currency_margin",
    "digits", "point", "spread", "spread_float", "trade_mode", "trade_calc_mode",
    "trade_contract_size", "trade_tick_size", "trade_tick_value",
    "trade_tick_value_profit", "trade_tick_value_loss",
    "trade_stops_level", "trade_freeze_level", "trade_exemode",
    "volume_min", "volume_max", "volume_step", "volume_limit",
    "swap_mode", "swap_long", "swap_short", "swap_rollover3days",
    "margin_initial", "margin_maintenance", "filling_mode", "expiration_mode",
    "session_deals", "session_orders", "visible", "select", "custom",
    "bid", "ask", "last", "time",
]


def _spec(si) -> dict:
    out = {}
    for f in SPEC_FIELDS:
        v = getattr(si, f, None)
        if v is None:
            continue
        out[f] = v
    return out


def resolve(canonical: str) -> dict:
    """Find the broker's real spelling for a canonical symbol name."""
    for cand in CANDIDATES.get(canonical, [canonical]):
        si = mt5.symbol_info(cand)
        if si is not None:
            mt5.symbol_select(cand, True)
            si = mt5.symbol_info(cand)
            rates = mt5.copy_rates_from_pos(cand, mt5.TIMEFRAME_H4, 0, 10)
            return {
                "canonical": canonical,
                "found": True,
                "mt5_symbol": cand,
                "h4_probe_rows": 0 if rates is None else len(rates),
                "spec": _spec(si),
            }
    return {"canonical": canonical, "found": False, "mt5_symbol": None,
            "tried": CANDIDATES.get(canonical, [canonical])}


def probe(book: str, path: str) -> dict:
    if not mt5.initialize(path=path, portable=True):
        raise RuntimeError(f"{book}: MT5 initialize failed: {mt5.last_error()}")
    try:
        acc = mt5.account_info()
        if acc is None:
            raise RuntimeError(f"{book}: account_info None: {mt5.last_error()}")
        positions = mt5.positions_get() or []
        orders = mt5.orders_get() or []
        term = mt5.terminal_info()

        report = {
            "book": book,
            "terminal_path": path,
            "probed_utc": datetime.now(timezone.utc).isoformat(),
            "account": {
                "login_sha256": hashlib.sha256(str(acc.login).encode()).hexdigest(),
                "server_sha256": hashlib.sha256(str(acc.server).encode()).hexdigest(),
                "trade_mode": acc.trade_mode,
                "margin_mode": acc.margin_mode,
                "trade_allowed": bool(acc.trade_allowed),
                "currency": acc.currency,
                "balance": acc.balance,
                "equity": acc.equity,
                "margin": acc.margin,
                "margin_free": acc.margin_free,
            },
            "terminal": {
                "connected": bool(getattr(term, "connected", False)),
                "trade_allowed": bool(getattr(term, "trade_allowed", False)),
                "build": getattr(term, "build", None),
            },
            "flat": {
                "open_positions": len(positions),
                "pending_orders": len(orders),
                "position_symbols": sorted({p.symbol for p in positions}),
                "order_symbols": sorted({o.symbol for o in orders}),
            },
            "total_broker_symbols": len(mt5.symbols_get() or []),
            "t1_deep_h4": [resolve(s) for s in T1_FILE_SYMBOLS],
            "t2_slippage": [resolve(s) for s in T2_SYMBOLS],
            "t3_fn_missing": [resolve(s) for s in T3_SYMBOLS],
        }

        # sweep the full list for anything the candidate table missed
        hits = []
        for s in (mt5.symbols_get() or []):
            up = s.name.upper()
            if any(p in up for p in SWEEP):
                hits.append(s.name)
        report["sweep_matches"] = sorted(set(hits))
        return report
    finally:
        mt5.shutdown()


def main() -> int:
    out = {}
    for book, path in TERMINALS.items():
        out[book] = probe(book, path)
    json.dump(out, sys.stdout, indent=2, default=str)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
