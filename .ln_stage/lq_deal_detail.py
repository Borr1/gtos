#!/usr/bin/env python3
"""Read-only deal detail 2026-07-01..2026-08-07 for both books. Places nothing."""
from __future__ import annotations

import datetime as dt
import sys

TERMINALS = {
    "ftmo": r"C:\MT5\FTMO\terminal64.exe",
    "fn": r"C:\MT5\redacted_account\terminal64.exe",
}
ENTRY = {0: "IN", 1: "OUT", 2: "INOUT", 3: "OUT_BY"}


def main() -> int:
    import MetaTrader5 as mt5

    def _refuse(*a, **k):
        raise RuntimeError("order_send disabled in LQ read-only deal detail reader")

    mt5.order_send = _refuse

    frm = dt.datetime(2026, 6, 30)
    to = dt.datetime(2026, 8, 7)

    for book, term in TERMINALS.items():
        print(f"\n================ {book}")
        if not mt5.initialize(path=term):
            print("  initialize FAILED:", mt5.last_error())
            continue
        try:
            deals = mt5.history_deals_get(frm, to) or []
            print(f"  {'time_utc':<20}{'symbol':<14}{'type':>5}{'entry':>7}{'vol':>7}"
                  f"{'price':>11}{'profit':>10}  magic  comment")
            for d in sorted(deals, key=lambda x: x.time):
                t = dt.datetime.fromtimestamp(d.time, dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                print(f"  {t:<20}{d.symbol:<14}{d.type:>5}{ENTRY.get(d.entry, d.entry):>7}"
                      f"{d.volume:>7.2f}{d.price:>11.2f}{d.profit:>10.2f}  {d.magic}  {d.comment!r}")
        finally:
            mt5.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
