"""READ-ONLY: dump the COMPLETE symbol list of both terminals.

The candidate-spelling probe can only prove presence, never absence — a symbol it
misses may simply be spelled in a way the candidate table did not guess. This dumps
every symbol both brokers expose so 'does not exist on redacted_account' is provable by
exhaustion rather than by a failed guess. NO orders.
"""
from __future__ import annotations

import json
import sys

import MetaTrader5 as mt5

TERMINALS = {
    "ftmo": r"C:\MT5\FTMO\terminal64.exe",
    "redacted_account": r"C:\MT5\redacted_account\terminal64.exe",
}


def dump(path: str) -> list[dict]:
    if not mt5.initialize(path=path, portable=True):
        raise RuntimeError(f"initialize failed: {mt5.last_error()}")
    try:
        return [
            {
                "name": s.name,
                "path": s.path,
                "description": s.description,
                "base": s.currency_base,
                "profit": s.currency_profit,
                "digits": s.digits,
                "contract": s.trade_contract_size,
                "trade_mode": s.trade_mode,
                "visible": s.visible,
            }
            for s in sorted(mt5.symbols_get() or [], key=lambda x: x.name)
        ]
    finally:
        mt5.shutdown()


def main() -> int:
    out = {book: dump(path) for book, path in TERMINALS.items()}
    json.dump(out, sys.stdout, indent=2, default=str)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
