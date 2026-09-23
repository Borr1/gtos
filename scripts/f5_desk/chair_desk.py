#!/usr/bin/env python3
"""F5 chair desk CLI. Formats a truthful card. Does not invent numbers.

    python scripts/f5_desk/chair_desk.py sit --snapshot card.json
    python scripts/f5_desk/chair_desk.py path --snapshot card.json --ticket 179105152

MT5 lives in ``chair_mt5`` and is imported only on ``--mt5``. Judgment stays
in the chair. This module does not HOLD, take, or tighten on its own.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.f5_desk import chair_card as card  # noqa: E402
from scripts.f5_desk import chair_ledger  # noqa: E402
from scripts.f5_desk.chair_observe import book_card  # noqa: E402


def render_proof(book: dict[str, Any]) -> str:
    lines = [
        f"login {book.get('login')} bal {book.get('balance')} eq {book.get('equity')}",
        f"day_net {book.get('day_net')} to_pass {book.get('to_pass')}",
        f"occupied {book.get('occupied')} fast_live {book.get('fast_family_live')}",
        f"positions {len(book.get('positions') or [])} pending {len(book.get('pending') or [])}",
    ]
    for p in book.get("positions") or []:
        row = {k: p.get(k) for k in (
            "ticket", "symbol", "sleeve", "side", "lots", "entry",
            "orig_sl", "live_sl", "tp", "mark", "profit_usd",
            "r_orig", "r_to_tp", "locked_r", "tape", "tick_age_s",
        )}
        for key in ("entry", "orig_sl", "live_sl", "tp", "mark"):
            row[key] = card.fmt_price(p.get(key), p.get("digits"))
        lines.append(
            "PATH {ticket} {symbol} {sleeve} {side} lots={lots} "
            "entry={entry} orig_sl={orig_sl} live_sl={live_sl} tp={tp} "
            "mark={mark} pnl={profit_usd} R_orig={r_orig} R_to_tp={r_to_tp} "
            "locked_r={locked_r} tape={tape} age={tick_age_s}".format(**row)
        )
    for o in book.get("pending") or []:
        lines.append(
            "ORD {ticket} {symbol} type={type} {type_name} price={price}".format(
                ticket=o.get("ticket"),
                symbol=card.norm_symbol(o.get("symbol")),
                type=o.get("type"),
                type_name=o.get("type_name") or "",
                price=card.fmt_price(o.get("price"), o.get("digits")),
            )
        )
    return "\n".join(lines) + "\n"


def card_from_snapshot(snap: dict[str, Any]) -> dict[str, Any]:
    return book_card(
        snap.get("account") or {},
        snap.get("positions") or [],
        baseline=snap.get("baseline"),
        ticks=snap.get("ticks") or {},
        orig_ledger=snap.get("orig_ledger") or {},
        now_unix=snap.get("now_unix"),
        orders=snap.get("orders") or [],
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="chair_desk")
    parser.add_argument("command", choices=("sit", "path"), default="sit", nargs="?")
    parser.add_argument("--snapshot", type=Path, help="JSON snapshot (no MT5)")
    parser.add_argument("--mt5", action="store_true", help="Read the live FTMO terminal")
    parser.add_argument("--repo", type=Path, default=_REPO, help="F5 repo root for ledgers")
    parser.add_argument("--orig-ledger", type=Path, default=None)
    parser.add_argument("--baseline", default=None, help="float or JSON path")
    parser.add_argument("--ticket", type=int, default=None)
    parser.add_argument("--proof", type=Path, default=None)
    args = parser.parse_args(argv)

    repo = Path(args.repo)
    orig_path = args.orig_ledger or chair_ledger.orig_path(repo)
    base_path = chair_ledger.baseline_path(repo)
    orig = chair_ledger.load_orig_ledger(orig_path)
    baseline = None
    if args.baseline is not None:
        try:
            baseline = float(args.baseline)
        except (TypeError, ValueError):
            baseline = chair_ledger.load_baseline(Path(args.baseline))
    if baseline is None:
        baseline = chair_ledger.load_baseline(base_path)

    if args.mt5:
        from scripts.f5_desk import chair_mt5
        snap = chair_mt5.snapshot(orig_ledger=orig)
        if snap.get("account") and snap["account"].get("balance") is not None:
            baseline = chair_ledger.maybe_roll_baseline(
                base_path, float(snap["account"]["balance"])
            )
            chair_ledger.persist_positions(orig_path, snap.get("positions") or [])
            orig = chair_ledger.load_orig_ledger(orig_path)
            snap["orig_ledger"] = orig
        snap["baseline"] = baseline
    elif args.snapshot:
        snap = json.loads(args.snapshot.read_text(encoding="utf-8"))
        snap.setdefault("orig_ledger", orig)
        if snap.get("baseline") is None:
            snap["baseline"] = baseline
    else:
        print("chair_desk: need --snapshot or --mt5", file=sys.stderr)
        return 2

    book = card_from_snapshot(snap)
    if args.command == "path" and args.ticket is not None:
        book["positions"] = [
            p for p in book.get("positions") or [] if int(p.get("ticket") or 0) == args.ticket
        ]
        if not book["positions"]:
            print(f"chair_desk: ticket {args.ticket} not in snapshot", file=sys.stderr)
            return 2
    text = render_proof(book)
    if args.mt5:
        from scripts.f5_desk.chair_wake_host import mark_sat
        mark_sat(repo)
    if args.proof:
        args.proof.parent.mkdir(parents=True, exist_ok=True)
        args.proof.write_text(text, encoding="ascii", errors="replace")
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
