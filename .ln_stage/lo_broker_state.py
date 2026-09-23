"""Session LO: READ-ONLY broker state probe. No order_send, no mutation of any kind.

Reads account_info + positions_get from ONE terminal and prints them. Run once per
terminal path. Nothing here can place, modify or close anything.
"""
import sys

import MetaTrader5 as mt5

path = sys.argv[1]
label = sys.argv[2]

if not mt5.initialize(path=path):
    print(f"{label}: initialize FAILED {mt5.last_error()}")
    raise SystemExit(1)

info = mt5.account_info()
positions = mt5.positions_get()
term = mt5.terminal_info()

print(f"=== {label} ===")
if info is None:
    print("  account_info: None")
else:
    print(f"  login={info.login} server={info.server}")
    print(f"  equity={info.equity:.2f} balance={info.balance:.2f} currency={info.currency}")
    print(f"  margin_free={info.margin_free:.2f} trade_allowed={info.trade_allowed}")
if term is not None:
    print(f"  terminal connected={term.connected} trade_allowed={term.trade_allowed}")
if positions is None:
    print(f"  positions_get -> None (READ FAILED) {mt5.last_error()}")
else:
    print(f"  open positions: {len(positions)}")
    for p in positions:
        print(f"    ticket={p.ticket} {p.symbol} type={p.type} vol={p.volume} "
              f"open={p.price_open} sl={p.sl} tp={p.tp} profit={p.profit:.2f} magic={p.magic}")

mt5.shutdown()
