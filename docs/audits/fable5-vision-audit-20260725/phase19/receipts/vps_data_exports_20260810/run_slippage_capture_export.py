"""T2: raw broker order/deal history export for the CS breaker slippage candidate.

Exports, from BOTH terminals, the complete MT5 history over the widest range the
terminal will serve:

  <broker>_deals_ALL.csv    every HistoryDeals row,  every field, unfiltered
  <broker>_orders_ALL.csv   every HistoryOrders row, every field, unfiltered
  <broker>_deals_<SYM>.csv  strict row subsets for the six target symbols
  <broker>_orders_<SYM>.csv strict row subsets for the six target symbols

Fields come from the MT5 namedtuple's own ``_asdict()``, so the column set is
whatever MT5 provides rather than a hand-picked list — tickets, both millisecond
time columns, requested vs executed price, volumes, commission, swap, fee,
comment, external_id, everything.

The per-symbol files are row SUBSETS of the ALL files, selected on the ``symbol``
column and nothing else. No value is rounded, reordered, derived or renamed: the
ALL files are the raw truth and the subsets are a convenience view of them.

READ-ONLY. Places, modifies and cancels nothing.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import MetaTrader5 as mt5

TERMINALS = {
    "ftmo": r"C:\MT5\FTMO\terminal64.exe",
    "redacted_account": r"C:\MT5\redacted_account\terminal64.exe",
}

# canonical -> per-broker spelling, resolved from each terminal by
# probe_prestate_and_symbols.py (see PROBE_PRESTATE_SYMBOLS.json)
TARGETS = {
    "ftmo": {
        "AUDJPY": "AUDJPY",
        "CHFJPY": "CHFJPY",
        "EURJPY": "EURJPY",
        "UKOIL_cash": "UKOIL.cash",
        "USOIL_cash": "USOIL.cash",
        "XAGUSD": "XAGUSD",
    },
    "redacted_account": {
        "AUDJPY": "AUDJPY",
        "CHFJPY": "CHFJPY",
        "EURJPY": "EURJPY",
        "UKOIL_cash": "UKOUSD",
        "USOIL_cash": "USOUSD",
        "XAGUSD": "XAGUSD",
    },
}


def _sha256(path: Path) -> str:
    d = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            d.update(chunk)
    return d.hexdigest()


def _rows(records) -> tuple[list[str], list[dict]]:
    """Turn MT5 namedtuples into dict rows carrying every field MT5 exposes."""
    if not records:
        return [], []
    out = [r._asdict() for r in records]
    return list(out[0].keys()), out


def _write(path: Path, header: list[str], rows: list[dict]) -> dict:
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=header)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    return {
        "path": str(path).replace("\\", "/"),
        "rows": len(rows),
        "columns": header,
        "sha256": _sha256(path),
    }


def export(book: str, path: str, out_dir: Path, start: datetime, end: datetime) -> dict:
    if not mt5.initialize(path=path, portable=True):
        raise RuntimeError(f"{book}: initialize failed: {mt5.last_error()}")
    try:
        acc = mt5.account_info()
        if acc is None:
            raise RuntimeError(f"{book}: account_info None")

        deals = mt5.history_deals_get(start, end)
        orders = mt5.history_orders_get(start, end)
        deal_err = None if deals is not None else str(mt5.last_error())
        order_err = None if orders is not None else str(mt5.last_error())

        d_hdr, d_rows = _rows(deals or ())
        o_hdr, o_rows = _rows(orders or ())

        files: dict[str, dict] = {}
        if d_rows:
            files[f"{book}_deals_ALL"] = _write(
                out_dir / f"{book}_deals_ALL.csv", d_hdr, d_rows
            )
        if o_rows:
            files[f"{book}_orders_ALL"] = _write(
                out_dir / f"{book}_orders_ALL.csv", o_hdr, o_rows
            )

        per_symbol = {}
        for canonical, broker_symbol in TARGETS[book].items():
            ds = [r for r in d_rows if r.get("symbol") == broker_symbol]
            os_ = [r for r in o_rows if r.get("symbol") == broker_symbol]
            per_symbol[canonical] = {
                "broker_symbol": broker_symbol,
                "deal_rows": len(ds),
                "order_rows": len(os_),
            }
            if ds:
                files[f"{book}_deals_{canonical}"] = _write(
                    out_dir / f"{book}_deals_{canonical}.csv", d_hdr, ds
                )
            if os_:
                files[f"{book}_orders_{canonical}"] = _write(
                    out_dir / f"{book}_orders_{canonical}.csv", o_hdr, os_
                )

        symbols_seen = sorted({r.get("symbol") for r in d_rows if r.get("symbol")})
        return {
            "book": book,
            "terminal_path": path,
            "account_login_sha256": hashlib.sha256(str(acc.login).encode()).hexdigest(),
            "account_server_sha256": hashlib.sha256(str(acc.server).encode()).hexdigest(),
            "trade_mode": acc.trade_mode,
            "request_start_utc": start.isoformat(),
            "request_end_utc": end.isoformat(),
            "history_deals_total": len(d_rows),
            "history_orders_total": len(o_rows),
            "history_deals_error": deal_err,
            "history_orders_error": order_err,
            "deal_columns": d_hdr,
            "order_columns": o_hdr,
            "distinct_deal_symbols": symbols_seen,
            "target_symbols": per_symbol,
            "files": files,
        }
    finally:
        mt5.shutdown()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--start", default="2015-01-01T00:00:00+00:00")
    ap.add_argument("--end", required=True)
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    start = datetime.fromisoformat(args.start)
    end = datetime.fromisoformat(args.end)

    manifest = {
        "schema_version": "mt5_slippage_capture_raw_history_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "read_only": True,
        "purpose": (
            "CS breaker candidate: reconciled price-domain slippage samples for "
            "AUDJPY, CHFJPY, EURJPY, UKOIL_cash, USOIL_cash, XAGUSD from both brokers."
        ),
        "raw_truth_note": (
            "*_ALL.csv are the complete unfiltered HistoryDeals/HistoryOrders sets with "
            "every field MT5 provides. Per-symbol files are strict row subsets selected "
            "on the symbol column only. Nothing is rounded, derived, renamed or reordered."
        ),
        "timebase_note": (
            "'time'/'time_msc'/'time_setup*'/'time_done*' are MT5 epoch values on the "
            "BROKER server clock, not UTC. Convert via broker_clock before joining "
            "against UTC-stamped runtime logs."
        ),
        "price_domain_note": (
            "Order rows carry price_open (the requested price) and deals carry price "
            "(the executed price); join deal.order -> order.ticket to reconcile the two "
            "into a price-domain slippage sample."
        ),
        "books": {},
    }
    for book, path in TERMINALS.items():
        manifest["books"][book] = export(book, path, out_dir, start, end)

    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )
    json.dump(manifest, sys.stdout, indent=2, sort_keys=True, default=str)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
