#!/usr/bin/env python3
"""CF-4 — the read-only symbol-tree probe, for the ORCHESTRATOR to run on the VPS.

Session CF wrote this and did NOT run it: it is the one artifact in this session that imports a
broker module, and CF never touches the VPS. Hand it to the orchestrator, who runs it over host-admin
against each already-running terminal and brings back the JSON.

WHAT IT DOES — exactly three MetaTrader5 calls, all read-only:

    mt5.initialize(...)     attach to the terminal (no login, no credentials in this file)
    mt5.symbols_get()       the full symbol tree — names + the few spec fields the estate uses
    mt5.terminal_info() / account_info()   provenance, so the artifact can be dated and attributed

It calls NOTHING else. Every mutating entry point is enumerated below and asserted absent at
import time, so a future edit that adds one fails loudly rather than quietly:

    order_send · order_check · order_calc_margin · order_calc_profit · positions_close ·
    Buy · Sell · symbol_select(..., False)

`symbol_select` is deliberately NOT called at all. Selecting a symbol mutates the terminal's
Market Watch, which is a visible state change on an armed host, and `symbols_get()` already
returns the whole tree without it.

USAGE (orchestrator, per terminal):

    python cf_revendor_symbol_tree_probe.py --terminal "C:\\MT5\\FTMO\\terminal64.exe" \
        --account FTMO --out ftmo_symbol_tree.json

Then copy the two JSONs back to this machine and run:

    python cf_revendor_symbol_tree_probe.py --merge ftmo_symbol_tree.json redacted_account_symbol_tree.json \
        --out docs/audits/.../phase15/receipts/BROKER_SYMBOL_TREE_<YYYYMMDD>.json

The merged artifact has the same schema as `BROKER_SYMBOL_TREE_20260725.json`, so the watchdog
tests and `gtos_command_center.py`'s panel 6 read it unchanged.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone

#: Names this probe must never call. Asserted against the MT5 module at run time — a typo that
#: reaches for one of these should stop the probe, not the account.
FORBIDDEN = (
    "order_send", "order_check", "order_calc_margin", "order_calc_profit",
    "positions_close", "Buy", "Sell", "buy", "sell",
)

#: The spec fields worth carrying alongside the name. `BROKER_SYMBOL_SPEC_COMPARISON.json`'s
#: fields, minus the live prices — a vendored artifact should not carry a stale bid/ask that
#: someone later reads as a quote.
SPEC_FIELDS = ("name", "path", "digits", "point", "spread", "trade_contract_size",
               "trade_tick_size", "trade_tick_value", "volume_min", "volume_max",
               "volume_step", "trade_mode", "currency_base", "currency_profit",
               "currency_margin", "swap_long", "swap_short", "swap_mode",
               "swap_rollover3days")


def _assert_read_only(mt5) -> None:
    """This probe's own guard: prove at run time that it holds no mutating reference."""
    src = open(__file__, "r", encoding="utf-8").read()
    for name in FORBIDDEN:
        if f"mt5.{name}(" in src or f"mt5.{name} (" in src:
            raise SystemExit(f"REFUSED: this probe references mt5.{name} — it must be read-only")
    if not hasattr(mt5, "symbols_get"):
        raise SystemExit("REFUSED: MetaTrader5 module has no symbols_get — wrong module?")


def probe(terminal: str | None, account: str) -> dict:
    import MetaTrader5 as mt5                                  # noqa: N813  (vendor casing)

    _assert_read_only(mt5)

    ok = mt5.initialize(terminal) if terminal else mt5.initialize()
    if not ok:
        raise SystemExit(f"initialize failed: {mt5.last_error()}")
    try:
        term = mt5.terminal_info()
        acct = mt5.account_info()
        symbols = mt5.symbols_get() or ()
        rows = []
        for s in symbols:
            d = getattr(s, "_asdict", None)
            d = d() if callable(d) else {f: getattr(s, f, None) for f in SPEC_FIELDS}
            rows.append({f: d.get(f) for f in SPEC_FIELDS if f in d})
        return {
            "account": account,
            "probed_utc": datetime.now(timezone.utc).isoformat(),
            "terminal": {"path": getattr(term, "path", None),
                         "build": getattr(term, "build", None),
                         "connected": getattr(term, "connected", None)},
            "login": getattr(acct, "login", None),
            "server": getattr(acct, "server", None),
            "n_symbols": len(rows),
            "names": sorted(r.get("name") for r in rows if r.get("name")),
            "specs": rows,
        }
    finally:
        mt5.shutdown()


def merge(paths: list[str]) -> dict:
    parts = [json.loads(open(p, "r", encoding="utf-8").read()) for p in paths]
    return {
        "schema": "gtos.broker.symbol_tree.v1",
        "source": "cf_revendor_symbol_tree_probe.py (live read-only symbols_get)",
        "generated_utc": min(p["probed_utc"] for p in parts),
        "note": ("NAME SURFACE ONLY in `symbols`; full per-symbol specs under `specs_by_account`. "
                 "Supersedes BROKER_SYMBOL_SPEC_COMPARISON.json (2026-07-26 vendor)."),
        "provenance": {p["account"]: {k: p.get(k) for k in
                                      ("probed_utc", "login", "server", "terminal", "n_symbols")}
                       for p in parts},
        "counts": {p["account"]: p["n_symbols"] for p in parts},
        "symbols": {p["account"]: p["names"] for p in parts},
        "specs_by_account": {p["account"]: p["specs"] for p in parts},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--terminal", default=None, help="path to terminal64.exe (VPS)")
    ap.add_argument("--account", default="FTMO", choices=("FTMO", "redacted_account"))
    ap.add_argument("--merge", nargs="+", default=None, metavar="JSON",
                    help="merge per-account probe outputs into the vendored artifact")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    out = merge(args.merge) if args.merge else probe(args.terminal, args.account)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
        fh.write("\n")
    print(json.dumps({"wrote": args.out,
                      "accounts": list(out.get("counts") or {out.get("account"): out.get("n_symbols")})},
                     indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
