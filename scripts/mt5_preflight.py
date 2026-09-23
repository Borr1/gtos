#!/usr/bin/env python3
"""MT5 Pre-flight check for demo deployment."""
import argparse
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
# Load .env from project root, not scripts dir
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))


RETIRED_ARM_MESSAGE = """\
REFUSING TO RUN: the order-placing mode of this script was retired on 2026-07-27.

  It was the last path in the repository that called a raw `mt5.order_send`
  with no runtime-halt check and no activation token — on a host with two
  funded accounts and `trade_allowed: true`. Its failure mode was not
  theoretical: if the cancel leg failed it left a real resting order carrying
  magic 99999999, which no GTOS component recognises.

  Test 5 now answers the same question with `mt5.order_check`, which validates
  the request against the broker's server and returns the same retcode WITHOUT
  placing anything. Just run:

      python scripts/mt5_preflight.py

  If you genuinely need a live order round-trip, use the gated
  `scripts/fn_smoke_trade.py`, which requires an activation token.
"""


def _parse_args():
    parser = argparse.ArgumentParser(description="Run MT5 connectivity and live-data preflight checks.")
    parser.add_argument(
        "--test-order",
        action="store_true",
        help="RETIRED 2026-07-27 — refuses to run. Test 5 now uses order_check (no broker mutation).",
    )
    return parser.parse_args()


args = _parse_args()
# Fail loudly rather than silently changing what an old runbook line does. An
# operator who types `--test-order` must not be left believing an order was
# placed, and a stale `GTOS_MT5_PREFLIGHT_TEST_ORDER=1` in a VPS environment
# must not be quietly ignored either — it is evidence of an expectation that no
# longer holds.
if args.test_order or os.getenv("GTOS_MT5_PREFLIGHT_TEST_ORDER", "").lower() in {"1", "true", "yes"}:
    print(RETIRED_ARM_MESSAGE)
    raise SystemExit(2)

print("=" * 60)
print("MT5 PRE-FLIGHT CHECK")
print("=" * 60)

# ---- Test 1: MT5 connection ----
print("\n[1/8] MT5 Connection...")
import MetaTrader5 as mt5
if not mt5.initialize():
    print(f"  FAIL: {mt5.last_error()}")
    sys.exit(1)
print(f"  OK: MT5 v{mt5.version()}")

account = mt5.account_info()
print(f"  Account: {account.login}")
print(f"  Balance: ${account.balance:,.2f}")
print(f"  Equity: ${account.equity:,.2f}")
print(f"  Server: {account.server}")
print(f"  Trade mode: {'DEMO' if account.trade_mode == 0 else 'LIVE — DANGER'}")

if account.trade_mode != 0:
    print("\n  *** WARNING: THIS IS A LIVE ACCOUNT, NOT DEMO ***")
    print("  *** Proceeding with extreme caution ***")
    input("  Press Enter to continue or Ctrl+C to abort...")

# ---- Test 2: Symbol ----
print("\n[2/8] Symbol Check...")
import yaml
# Resolve against the repo, not the CWD: an operator running this from
# C:\MT5\ or from scripts\ otherwise gets a FileNotFoundError on a check that
# has nothing to do with where they were standing.
_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'agent_config.yaml')
with open(_CONFIG_PATH) as f:
    config = yaml.safe_load(f)
symbol = config.get('market', {}).get('symbol', 'XAUUSD')

info = mt5.symbol_info(symbol)
if info is None:
    print(f"  FAIL: '{symbol}' not found in MT5")
    print("  Trying alternatives...")
    found = False
    for alt in ["GOLD", "XAUUSDm", "XAUUSD.a", "XAUUSDc", "XAUUSD.raw", "XAUUSD.i", "XAUUSDx"]:
        if mt5.symbol_info(alt):
            print(f"  FOUND: '{alt}' — update config/agent_config.yaml: symbol: \"{alt}\"")
            found = True
    if not found:
        print("  No gold symbol found. Open MT5 → Market Watch → right-click → Show All")
    sys.exit(1)
else:
    print(f"  OK: {symbol}")
    print(f"  Contract size: {info.trade_contract_size} {'(STANDARD)' if info.trade_contract_size == 100 else '(NON-STANDARD — CHECK LOT CALC!)'}")
    print(f"  Volume: min={info.volume_min}, max={info.volume_max}, step={info.volume_step}")
    print(f"  Trade mode: {info.trade_mode} {'(FULL)' if info.trade_mode == 4 else '(RESTRICTED!)'}")
    print(f"  Digits: {info.digits}")
    print(f"  Point: {info.point}")

# ---- Test 3: Data availability (all timeframes) ----
print("\n[3/8] Data Availability...")
timeframes = {
    "M15": mt5.TIMEFRAME_M15,
    "H1": mt5.TIMEFRAME_H1,
    "H4": mt5.TIMEFRAME_H4,
    "D1": mt5.TIMEFRAME_D1,
}
lookbacks = {"M15": 672, "H1": 168, "H4": 80, "D1": 30}

for name, tf in timeframes.items():
    rates = mt5.copy_rates_from_pos(symbol, tf, 0, lookbacks[name])
    if rates is None or len(rates) == 0:
        print(f"  FAIL: No {name} data")
    else:
        from datetime import datetime, timezone
        latest = datetime.fromtimestamp(rates[-1]['time'], tz=timezone.utc)
        pct = len(rates) / lookbacks[name] * 100
        status = "OK" if pct >= 90 else "WARNING (< 90%)"
        print(f"  {status}: {name} — {len(rates)}/{lookbacks[name]} candles ({pct:.0f}%), latest: {latest.strftime('%Y-%m-%d %H:%M UTC')}")

# ---- Test 4: Spread ----
print("\n[4/8] Spread...")
tick = mt5.symbol_info_tick(symbol)
if tick:
    spread_cents = (tick.ask - tick.bid) * 100
    print(f"  Bid: {tick.bid}, Ask: {tick.ask}")
    print(f"  Spread: {spread_cents:.1f} cents {'(OK)' if spread_cents <= 30 else '(HIGH — will block trading)'}")
else:
    print("  FAIL: No tick data")

# ---- Test 5: Order capability (validated server-side; NOTHING is placed) ----
#
# This used to place a real 0.01-lot BUY LIMIT and cancel it. `order_check`
# submits the identical request to the broker's server for validation and
# returns the same retcode — including 10030 (unsupported filling mode), which
# is the one answer this test actually exists to produce — without creating an
# order, a ticket, or broker history. It also reports the margin the request
# would consume, which the place-and-cancel version never told us.
print("\n[5/8] Order Capability Test (order_check — no order is placed)...")
test_price = round(tick.bid - 100, 2) if tick else 3000.0
_base_request = {
    "action": mt5.TRADE_ACTION_PENDING,
    "symbol": symbol,
    "volume": 0.01,
    "type": mt5.ORDER_TYPE_BUY_LIMIT,
    "price": test_price,
    "sl": test_price - 10,
    "tp": test_price + 50,
    "deviation": 20,
    "magic": 99999999,
    "comment": "preflight_check",
    "type_time": mt5.ORDER_TIME_GTC,
}
_accepted = []
for _fill_name in ("ORDER_FILLING_IOC", "ORDER_FILLING_FOK", "ORDER_FILLING_RETURN"):
    _fill = getattr(mt5, _fill_name, None)
    if _fill is None:
        continue
    _check = mt5.order_check({**_base_request, "type_filling": _fill})
    if _check is None:
        print(f"  {_fill_name}: order_check returned None — {mt5.last_error()}")
        continue
    if _check.retcode == mt5.TRADE_RETCODE_DONE:
        _accepted.append(_fill_name)
        print(f"  OK: {_fill_name} accepted (margin {getattr(_check, 'margin', 0.0):.2f}, "
              f"free after {getattr(_check, 'margin_free', 0.0):.2f})")
    elif _check.retcode == 10030:
        print(f"  {_fill_name}: NOT supported by this broker (retcode 10030)")
    else:
        print(f"  {_fill_name}: retcode {_check.retcode} — {_check.comment}")
if _accepted:
    print(f"  RESULT: order placement permitted. Filling modes accepted: {', '.join(_accepted)}")
    print(f"  NOTE: verify execution.py's type_filling is one of these.")
else:
    print("  RESULT: NO filling mode was accepted — order placement looks restricted, or the")
    print("          request is invalid for this symbol. Check broker permissions and symbol spec.")

# ---- Test 6: Position check ----
print("\n[6/8] Existing Positions...")
positions = mt5.positions_get(symbol=symbol)
if positions:
    print(f"  WARNING: {len(positions)} open positions on {symbol}:")
    for p in positions:
        print(f"    Ticket {p.ticket}: {'BUY' if p.type == 0 else 'SELL'} {p.volume} lots @ {p.price_open}, P&L: ${p.profit:.2f}, Magic: {p.magic}")
    agent_positions = [p for p in positions if p.magic == 20260401]
    if agent_positions:
        print(f"  CRITICAL: {len(agent_positions)} positions with OUR magic number (20260401). These may be orphaned from a previous run!")
else:
    print(f"  OK: No open positions on {symbol}")

# ---- Test 7: Timezone ----
print("\n[7/8] Timezone...")
import time
from datetime import datetime, timezone, timedelta
local_now = datetime.now()
utc_now = datetime.now(timezone.utc)
offset = (local_now.hour - utc_now.hour) % 24
print(f"  Local time: {local_now.strftime('%H:%M:%S')}")
print(f"  UTC time: {utc_now.strftime('%H:%M:%S')}")
print(f"  Offset: UTC+{offset}")

hour_utc = utc_now.hour
minute_utc = utc_now.minute
in_london = 7 <= hour_utc < 9 or (hour_utc == 9 and minute_utc < 30)
in_ny = 13 <= hour_utc < 15 or (hour_utc == 15 and minute_utc < 30)
print(f"  In London KZ: {'YES' if in_london else 'no'}")
print(f"  In NY KZ: {'YES' if in_ny else 'no'}")
next_london = "07:00 UTC tomorrow" if hour_utc >= 10 else "07:00 UTC today"
next_ny = "13:00 UTC today" if hour_utc < 13 else "13:00 UTC tomorrow"
print(f"  Next London: {next_london}")
print(f"  Next NY: {next_ny}")

# ---- Test 8: API key ----
print("\n[8/8] Anthropic API Key...")
api_key = os.environ.get("ANTHROPIC_API_KEY", "")
if api_key:
    print(f"  OK: Key present ({api_key[:12]}...)")
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=10,
            messages=[{"role": "user", "content": "Reply with just the word OK"}]
        )
        print(f"  OK: API call succeeded ({response.content[0].text.strip()})")
    except Exception as e:
        print(f"  FAIL: API call failed: {e}")
else:
    print("  FAIL: No ANTHROPIC_API_KEY in environment or .env file")

mt5.shutdown()
print("\n" + "=" * 60)
print("PRE-FLIGHT COMPLETE")
print("=" * 60)
