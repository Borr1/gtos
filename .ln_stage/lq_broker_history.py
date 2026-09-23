#!/usr/bin/env python3
"""Read-only broker deal history for both books. Places nothing, mutates nothing.

Session LQ: ground truth for the redacted_account 2026-07-02 -> 2026-07-31 silence.
Only history_deals_get / account_info are called; order_send is disabled first.
"""
from __future__ import annotations

import collections
import datetime as dt
import sys

TERMINALS = {
    "ftmo": r"C:\MT5\FTMO\terminal64.exe",
    "fn": r"C:\MT5\redacted_account\terminal64.exe",
}


def main() -> int:
    import MetaTrader5 as mt5

    def _refuse(*a, **k):  # structural guarantee: this process cannot trade
        raise RuntimeError("order_send disabled in LQ read-only history reader")

    mt5.order_send = _refuse

    frm = dt.datetime(2026, 6, 1)
    to = dt.datetime(2026, 8, 7)

    for book, term in TERMINALS.items():
        print(f"\n================ {book}  ({term})")
        if not mt5.initialize(path=term):
            print("  initialize FAILED:", mt5.last_error())
            continue
        try:
            ai = mt5.account_info()
            print(f"  login={ai.login} server={ai.server} equity={ai.equity:.2f} "
                  f"balance={ai.balance:.2f} positions={len(mt5.positions_get() or [])}")
            deals = mt5.history_deals_get(frm, to)
            if deals is None:
                print("  history_deals_get returned None:", mt5.last_error())
                continue
            print(f"  deals 2026-06-01..2026-08-07: {len(deals)}")
            byday = collections.defaultdict(
                lambda: {"in": 0, "out": 0, "other": 0, "profit": 0.0, "syms": set()}
            )
            for d in deals:
                day = dt.datetime.utcfromtimestamp(d.time).strftime("%Y-%m-%d")
                b = byday[day]
                if d.entry == 0:
                    b["in"] += 1
                elif d.entry == 1:
                    b["out"] += 1
                else:
                    b["other"] += 1
                b["profit"] += d.profit
                if d.symbol:
                    b["syms"].add(d.symbol)
            print(f"    {'day':<12}{'entries':>8}{'exits':>7}{'other':>7}{'profit':>11}  symbols")
            for day in sorted(byday):
                b = byday[day]
                print(f"    {day:<12}{b['in']:>8}{b['out']:>7}{b['other']:>7}"
                      f"{b['profit']:>11.2f}  {','.join(sorted(b['syms']))[:60]}")
            jul = [d for d in deals
                   if "2026-07-02" <= dt.datetime.utcfromtimestamp(d.time).strftime("%Y-%m-%d") <= "2026-07-31"]
            jul_in = [d for d in jul if d.entry == 0]
            print(f"  >>> 2026-07-02..2026-07-31 : {len(jul)} deals, {len(jul_in)} ENTRY deals")
        finally:
            mt5.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
