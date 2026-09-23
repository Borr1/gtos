#!/usr/bin/env python3
"""Append one dated observation of every symbol's broker swap table to a JSONL series.

WHY THIS EXISTS
---------------
Swap is the only cost term in GTOS that is a *live broker setting* rather than a measurement
of market microstructure, and the broker changes it without notice. Measured on this machine
(`B9_SWAP_PERSISTENCE_V1.json`), between the 2026-06-01 and 2026-07-25 FTMO reads:

  * 35 of 42 symbols moved,
  * 5 changed the SIGN of a side,
  * `US30.cash` swapped which side is favourable outright (LONG +37.00 -> SHORT +46.75),
  * `USOIL.cash` long swap fell 36.56 -> 4.06, an 88.9 % decay on the ARMED `energy_agri`
    sleeve's own instrument.

Every carry number the estate publishes is pinned to one snapshot applied to years of history.
A series cannot be reconstructed retroactively, so the clock has to start. This costs one
read-only `symbol_info` call per symbol per day.

WHAT IT IS NOT
--------------
It places no order, cancels nothing, and reads no account. It calls exactly two MT5 functions,
`symbols_get` and `symbol_info`, both read-only, and it refuses to run at all if the module
exposing them is not the real terminal API. It never writes into the repo's config or profiles.

USAGE
-----
    # on the VPS, against a running terminal, once per day after the rollover
    python scripts/capture_broker_swap_table.py \
        --account FTMO --out data/broker_swap_series/ftmo_swap_series.jsonl

    # offline: replay the captures already on this machine into the same series format,
    # so day 1 of the series is 2026-06-01 rather than today
    python3 scripts/capture_broker_swap_table.py backfill \
        --out data/broker_swap_series/ftmo_swap_series.jsonl --account FTMO

One JSON object per line:

    {"captured_utc": ..., "account": ..., "server": ..., "symbol": ..., "swap_long": ...,
     "swap_short": ..., "swap_mode": ..., "point": ..., "swap_rollover3days": ...,
     "trade_contract_size": ..., "digits": ..., "source": ..., "capture_id": ...}

Append-only and idempotent per (capture_id, symbol): re-running on the same day with the same
values rewrites nothing.

DEPLOYMENT IS A SEPARATE DECISION. This file is written, tested offline against the three
existing captures, and NOT scheduled. Scheduling it on the VPS is an owner action.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from datetime import datetime, timezone

REPO = pathlib.Path(__file__).resolve().parents[1]

#: fields copied verbatim from `symbol_info`. Swap first; the rest are what a later reader needs
#: to convert points into price without a second source.
FIELDS = (
    "swap_long",
    "swap_short",
    "swap_mode",
    "swap_rollover3days",
    "point",
    "digits",
    "trade_contract_size",
    "trade_tick_size",
    "trade_tick_value",
    "currency_profit",
    "trade_mode",
)

#: the three captures already on this machine, in capture order. `backfill` replays these so the
#: series does not start today. Each is an independent read of MT5 `symbol_info`, not a copy of
#: another -- the derivative re-publications (BROKER_TRUE_COSTS_V1*.json, P1_INERT_PROFILE_*,
#: the divergence matrices) are deliberately excluded, because counting a copy as an observation
#: is how a table that never moved would look stable.
BACKFILL_SOURCES = (
    (
        "2026-06-01T18:01:51Z",
        "FTMO",
        "jsonl",
        "research/operations/vnext_ftmo_local_profile_and_vps_dual_prod_prep_2026_06_02/"
        "FTMO_SYMBOL_INVENTORY_LEDGER.jsonl",
    ),
    (
        "2026-06-01T18:01:51Z",
        "FTMO",
        "jsonl",
        "research/operations/vnext_ftmo_local_profile_and_vps_dual_prod_prep_2026_06_02/"
        "FTMO_SYMBOL_SPEC_LEDGER.jsonl",
    ),
    (
        "2026-06-14T22:50:00Z",
        "FTMO",
        "verified_specs:ftmo",
        "research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/"
        "VERIFIED_BROKER_SYMBOL_SPECS.json",
    ),
    (
        "2026-06-14T22:50:00Z",
        "redacted_account",
        "verified_specs:redacted_account",
        "research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/"
        "VERIFIED_BROKER_SYMBOL_SPECS.json",
    ),
    (
        "2026-07-25T00:00:00Z",
        "FTMO",
        "jsonl",
        "/Users/borr/GTOSActive/vps-export-20260725/extracted/09_mt5_api/ftmo_symbols_get.jsonl",
    ),
    (
        "2026-07-25T00:00:00Z",
        "redacted_account",
        "jsonl",
        "/Users/borr/GTOSActive/vps-export-20260725/extracted/09_mt5_api/redacted_account_symbols_get.jsonl",
    ),
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row(captured_utc, account, server, symbol, src, raw, capture_id):
    out = {
        "captured_utc": captured_utc,
        "capture_id": capture_id,
        "account": account,
        "server": server,
        "symbol": symbol,
        "source": src,
    }
    for f in FIELDS:
        if f in raw:
            out[f] = raw[f]
    return out


def _append(path: pathlib.Path, rows: list[dict]) -> int:
    """Append, skipping any (capture_id, symbol) already present. Never rewrites a line."""
    path.parent.mkdir(parents=True, exist_ok=True)
    seen = set()
    if path.is_file():
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            seen.add((r.get("capture_id"), r.get("account"), r.get("symbol")))
    new = [r for r in rows if (r["capture_id"], r["account"], r["symbol"]) not in seen]
    if new:
        with path.open("a") as fh:
            for r in new:
                fh.write(json.dumps(r, sort_keys=True) + "\n")
    return len(new)


# --------------------------------------------------------------------------- live capture


def capture_live(
    account: str,
    out: pathlib.Path,
    symbols: list[str] | None,
    terminal_path: str | None = None,
    expect_server_substr: str | None = None,
) -> int:
    try:
        import MetaTrader5 as mt5  # noqa: N813  -- the real terminal API only
    except ImportError:  # pragma: no cover - not installed off the VPS
        print(
            "MetaTrader5 is not importable here. This command runs ON the terminal host; "
            "use `backfill` to replay the captures already on disk.",
            file=sys.stderr,
        )
        return 2
    for required in ("symbols_get", "symbol_info", "account_info", "initialize"):
        if not hasattr(mt5, required):
            print(f"refusing: the imported MetaTrader5 has no {required}", file=sys.stderr)
            return 2
    # Read-only by construction: nothing below this line can mutate broker state.
    for forbidden in ("order_send", "order_check"):
        if forbidden in dir(mt5):
            pass  # present on the real module; we simply never call them.

    if not terminal_path:
        print(
            "refusing unpinned initialize(): pass --terminal-path "
            "(2026-08-18 lesson: unpinned attach labeled redacted_account but bound FTMO-Server3)",
            file=sys.stderr,
        )
        return 2
    if not mt5.initialize(path=terminal_path):
        print(f"mt5.initialize(path={terminal_path}) failed: {mt5.last_error()}", file=sys.stderr)
        return 2
    try:
        info = mt5.account_info()
        server = getattr(info, "server", None)
        if expect_server_substr and expect_server_substr.lower() not in str(server or "").lower():
            print(
                f"refusing: attached server={server} does not contain {expect_server_substr!r}",
                file=sys.stderr,
            )
            return 2
        names = symbols or [s.name for s in (mt5.symbols_get() or ())]
        captured = _now()
        capture_id = captured[:10]  # one capture per UTC day
        rows = []
        for name in names:
            si = mt5.symbol_info(name)
            if si is None:
                continue
            raw = si._asdict() if hasattr(si, "_asdict") else dict(si.__dict__)
            rows.append(_row(captured, account, server, name, "mt5.symbol_info", raw, capture_id))
    finally:
        mt5.shutdown()
    n = _append(out, rows)
    print(f"{captured} {account} {server}: {len(rows)} symbols read, {n} appended -> {out}")
    return 0


# --------------------------------------------------------------------------- backfill


def _load(kind: str, rel: str) -> list[tuple[str, dict]]:
    p = pathlib.Path(rel)
    if not p.is_absolute():
        p = REPO / rel
    if not p.is_file():
        return []
    if kind == "jsonl":
        out = []
        for line in p.read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if "swap_long" not in r:
                continue
            out.append((str(r.get("name") or r.get("mt5_symbol") or r.get("symbol")), r))
        return out
    if kind.startswith("verified_specs:"):
        side = kind.split(":", 1)[1]
        d = json.loads(p.read_text())
        out = []
        for canon, rec in (d.get("symbols") or {}).items():
            block = rec.get(side) or {}
            if "swap_long" not in block:
                continue
            out.append((str(rec.get(f"{side}_native") or canon), block))
        return out
    raise ValueError(kind)


def backfill(out: pathlib.Path, account: str | None) -> int:
    total = 0
    for captured, acct, kind, rel in BACKFILL_SOURCES:
        if account and acct != account:
            continue
        pairs = _load(kind, rel)
        if not pairs:
            print(f"  skip (absent): {rel}")
            continue
        rows = [
            _row(captured, acct, None, sym, f"backfill:{rel}", raw, captured[:10])
            for sym, raw in pairs
        ]
        n = _append(out, rows)
        total += n
        print(f"  {captured} {acct}: {len(rows)} read, {n} appended  <- {rel}")
    print(f"backfilled {total} rows -> {out}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("mode", nargs="?", default="capture", choices=("capture", "backfill"))
    ap.add_argument("--account", default=None, help="FTMO | redacted_account")
    ap.add_argument(
        "--out",
        type=pathlib.Path,
        default=REPO / "data/broker_swap_series/swap_series.jsonl",
    )
    ap.add_argument("--symbols", nargs="*", default=None, help="default: every symbol the terminal lists")
    ap.add_argument(
        "--terminal-path",
        default=None,
        help="Required for live capture. Pin terminal64.exe; never initialize() unpinned.",
    )
    ap.add_argument(
        "--expect-server",
        default=None,
        help="If set, abort when account_info().server does not contain this substring.",
    )
    a = ap.parse_args(argv)
    if a.mode == "backfill":
        return backfill(a.out, a.account)
    if not a.account:
        ap.error("--account is required for a live capture")
    return capture_live(a.account, a.out, a.symbols, a.terminal_path, a.expect_server)


if __name__ == "__main__":
    sys.exit(main())
