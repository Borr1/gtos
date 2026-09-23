#!/usr/bin/env python3
"""Prove a live book can actually authorize an entry — without placing one.

Why this exists
---------------
`gtos_activation_token.py status` reports a token as ``valid`` by verifying it
against **its own** declared namespace, so a token bound to the wrong namespace
reports healthy while refusing every entry the book attempts. That is exactly
how F1 survived: the redacted_account token bound ``redacted_account`` (the *profile* name)
while ``run_book.py`` declares ``redacted_account_live_bee34003`` (the *namespace*),
and 231 live orders were refused on 2026-08-04 while ``status`` said ``valid``.

`status` cannot catch this, because it never learns what the worker declares.
This script does: it builds the adapter the book builds, declares the activation
context exactly as ``run_book.py:307-308`` does, and runs the choke point's own
check (``mt5_real.py:490-496``) on a realistic exposure-increasing entry —
stopping immediately before ``self._mt5.order_send``.

It cannot place an order. ``MetaTrader5.order_send`` is replaced with a function
that raises, so this process is structurally incapable of trading, and
``order_check`` is a broker-side *validation* call that places nothing.

Usage
-----
    python scripts/verify_activation_authorization.py --book fn
    python scripts/verify_activation_authorization.py --book ftmo --symbol XAUUSD

Exit status is 0 only when the live namespace authorizes AND the gate still
refuses a wrong namespace — a check that only ever passes is not a check.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# The books' real launch parameters, from scripts/run_book_supervisor.ps1:140-141.
BOOKS = {
    "ftmo": {
        "terminal": r"C:\MT5\FTMO\terminal64.exe",
        "profile": "operator_profile",
        "namespace": "operator_profile",
    },
    "fn": {
        "terminal": r"C:\MT5\redacted_account\terminal64.exe",
        "profile": "redacted_account",
        "namespace": "redacted_account_live_bee34003",
    },
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--book", choices=sorted(BOOKS), required=True)
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--config", default="config/agent_config.yaml")
    parser.add_argument("--terminal-path", default=None,
                        help="override the terminal path for this book")
    args = parser.parse_args(argv)

    import MetaTrader5 as mt5

    from src.mt5.mt5_real import RealMT5
    from src.mt5.mt5_interface import TRADE_ACTION_DEAL, MAGIC_NUMBER
    from src.safety.activation_token import (
        ActivationTokenError,
        config_digest_for,
        enforce_broker_mutation_authorized,
        token_dir,
    )

    book = BOOKS[args.book]
    terminal = args.terminal_path or book["terminal"]

    adapter = RealMT5(terminal_path=terminal)
    if not adapter.connect():
        print(f"connect FAILED for {terminal}")
        return 2

    def _forbidden(*_a, **_k):
        raise AssertionError("order_send is disabled in this verifier")

    adapter._mt5.order_send = _forbidden

    # Exactly run_book.py:307-308.
    cfg_digest = config_digest_for(args.config, book["profile"], repo_root=REPO_ROOT)
    adapter.set_activation_context(namespace=book["namespace"],
                                   config_digest_sha256=cfg_digest)

    print(f"book               : {args.book}")
    print(f"token_dir          : {token_dir()}")
    print(f"declared namespace : {book['namespace']}")
    print(f"declared cfg digest: {(cfg_digest or 'unavailable')[:12]}")
    print(f"account digest     : {adapter.account_login_sha256()}")

    info = mt5.symbol_info(args.symbol)
    tick = mt5.symbol_info_tick(args.symbol)
    if info is None or tick is None:
        print(f"symbol {args.symbol} unavailable: {mt5.last_error()}")
        mt5.shutdown()
        return 2

    price = float(tick.ask)
    digits = int(info.digits)
    request = {
        "action": TRADE_ACTION_DEAL,
        "symbol": args.symbol,
        "volume": float(info.volume_min),
        "type": mt5.ORDER_TYPE_BUY,
        "price": price,
        # Opening geometry, so the request classifies as a genuine new entry
        # (`exposure_increasing_new_deal`) and not as a close.
        "sl": round(price * 0.97, digits),
        "tp": round(price * 1.03, digits),
        "deviation": 20,
        "magic": MAGIC_NUMBER,
        "comment": "activation_verify_never_sent",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    def check(namespace: str | None, label: str) -> bool:
        """The exact argument tuple from RealMT5.order_send."""
        try:
            decision = enforce_broker_mutation_authorized(
                request,
                account_login_sha256=adapter.account_login_sha256(),
                positions_provider=adapter.positions_for_activation,
                namespace=namespace,
                config_digest_sha256=adapter._activation_config_digest,
            )
            print(f"  [{label}] ALLOWED  reason={decision.reason} "
                  f"classification={decision.classification}")
            return True
        except ActivationTokenError as exc:
            print(f"  [{label}] REFUSED  {exc}")
            return False

    print("\n=== the engine's own authorization path ===")
    live = check(book["namespace"], "live runtime namespace")
    print("\n  -- negative controls: the gate must still discriminate --")
    wrong = check(book["profile"] + "_not_the_namespace", "wrong namespace")
    undeclared = check(None, "namespace not declared")

    print("\n=== broker-side validation (order_check — places NOTHING) ===")
    checked = mt5.order_check(request)
    if checked is None:
        print(f"  order_check -> None  {mt5.last_error()}")
    else:
        print(f"  retcode={checked.retcode} comment={checked.comment!r}")

    ok = live and not wrong and not undeclared
    print("\n=== VERDICT ===")
    print(f"  live namespace authorizes         : {live}")
    print(f"  wrong/undeclared still refused    : {(not wrong) and (not undeclared)}")
    print(f"  RESULT: {'PASS' if ok else 'FAIL'}")

    mt5.shutdown()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
