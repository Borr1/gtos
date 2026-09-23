"""Session LO: EMPIRICAL proof that redacted_account now authorizes an exposure-increasing request.

This drives a REAL ``RealMT5`` connected to the live redacted_account terminal, declares the
activation context exactly as ``run_book.py:307-308`` does, and then runs the choke point's
OWN check (``mt5_real.py:490-496``) verbatim -- stopping immediately before
``self._mt5.order_send``.

Safety: ``MetaTrader5.order_send`` is replaced with a function that raises, so this process
is structurally incapable of placing an order. ``order_check`` is a broker-side VALIDATION
call and places nothing.
"""
import sys

sys.path.insert(0, ".")

import MetaTrader5 as mt5  # noqa: E402

from src.mt5.mt5_real import RealMT5  # noqa: E402
from src.mt5.mt5_interface import TRADE_ACTION_DEAL, MAGIC_NUMBER  # noqa: E402
from src.safety.activation_token import (  # noqa: E402
    ActivationTokenError,
    config_digest_for,
    enforce_broker_mutation_authorized,
    token_dir,
)

BOOKS = {
    "fn": (r"C:\MT5\redacted_account\terminal64.exe", "redacted_account", "redacted_account_live_bee34003",
           "redacted_account"),
    "ftmo": (r"C:\MT5\FTMO\terminal64.exe", "operator_profile", "operator_profile",
             "redacted_account"),
}
BOOK = sys.argv[2] if len(sys.argv) > 2 else "fn"
TERMINAL, PROFILE, NAMESPACE, OLD_TOKEN_NAMESPACE = BOOKS[BOOK]


def _forbidden(*a, **k):
    raise AssertionError("order_send is disabled in this proof process")


rm = RealMT5(terminal_path=TERMINAL)
if not rm.connect():
    print("connect FAILED")
    raise SystemExit(1)

# Hard guard: nothing in this process can place an order from here on.
rm._mt5.order_send = _forbidden

# Exactly run_book.py:307-308
cfg_digest = config_digest_for("config/agent_config.yaml", PROFILE)
rm.set_activation_context(namespace=NAMESPACE, config_digest_sha256=cfg_digest)

print(f"token_dir          : {token_dir()}")
print(f"declared namespace : {rm._activation_namespace}")
print(f"declared cfg digest: {rm._activation_config_digest[:12]}")
print(f"account digest     : {rm.account_login_sha256()}")

# A realistic exposure-increasing ENTRY: DEAL, no position ticket, carries sl+tp.
# classify_request -> "exposure_increasing_new_deal" -- the exact classification
# in all 231 refusals.
sym = sys.argv[1] if len(sys.argv) > 1 else "XAUUSD"
info = mt5.symbol_info(sym)
tick = mt5.symbol_info_tick(sym)
if info is None or tick is None:
    print(f"symbol {sym} unavailable: {mt5.last_error()}")
    raise SystemExit(1)

vol = float(info.volume_min)
price = float(tick.ask)
digits = int(info.digits)
sl = round(price * 0.97, digits)
tp = round(price * 1.03, digits)

request = {
    "action": TRADE_ACTION_DEAL,
    "symbol": sym,
    "volume": vol,
    "type": mt5.ORDER_TYPE_BUY,
    "price": price,
    "sl": sl,
    "tp": tp,
    "deviation": 20,
    "magic": MAGIC_NUMBER,
    "comment": "LO_authz_proof_never_sent",
    "type_time": mt5.ORDER_TIME_GTC,
    "type_filling": mt5.ORDER_FILLING_IOC,
}
print(f"\nrequest: {sym} vol={vol} BUY @ {price} sl={sl} tp={tp}")


def choke_point_check(namespace, label):
    """The EXACT argument tuple from RealMT5.order_send (mt5_real.py:490-496)."""
    try:
        decision = enforce_broker_mutation_authorized(
            request,
            account_login_sha256=rm.account_login_sha256(),
            positions_provider=rm.positions_for_activation,
            namespace=namespace,
            config_digest_sha256=rm._activation_config_digest,
        )
        print(f"  [{label}] ALLOWED  reason={decision.reason} "
              f"classification={decision.classification} direction={decision.risk_direction}")
        return True
    except ActivationTokenError as exc:
        print(f"  [{label}] REFUSED  {exc}")
        return False


print("\n=== LAYER 1: the engine's own authorization path ===")
live = choke_point_check(rm._activation_namespace, "LIVE runtime namespace")
print("\n  -- negative controls (the gate must still discriminate) --")
old = choke_point_check(OLD_TOKEN_NAMESPACE, "OLD token namespace 'redacted_account'")
bogus = choke_point_check("not_a_real_namespace", "bogus namespace")
undeclared = choke_point_check(None, "namespace not declared")

print("\n=== LAYER 2: broker-side validation (order_check -- places NOTHING) ===")
checked = mt5.order_check(request)
if checked is None:
    print(f"  order_check -> None  {mt5.last_error()}")
else:
    print(f"  retcode={checked.retcode} comment={checked.comment!r}")
    print(f"  margin_free_after={checked.margin_free} balance={checked.balance}")

print("\n=== VERDICT ===")
ok = live and not old and not bogus and not undeclared
print(f"  live runtime namespace authorizes      : {live}")
print(f"  old/bogus/undeclared still refused     : {(not old) and (not bogus) and (not undeclared)}")
print(f"  order_send calls made                  : 0 (function disabled)")
print(f"  RESULT: {'PASS' if ok else 'FAIL'}")

mt5.shutdown()
raise SystemExit(0 if ok else 1)
