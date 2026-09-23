#!/usr/bin/env python3
"""Print the autonomous friend-copy plan. Never order_send.

Challenge 0 is the writer. SH / redacted_account / redacted_account copy the same lots
and the same Challenge broker SL/TP. Agents do not place, close, or resize.
redacted_account idle. Verification quarantined.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.judgment.friend_copy import (  # noqa: E402
    MEASURED_CHALLENGE_FILLS,
    FriendCopyError,
    agent_may_mutate_friend,
    print_plan,
    protection_sync_plan,
)


def _load_json(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"not an object: {path}")
    return payload


def _refuse_send() -> int:
    print(
        json.dumps(
            {
                "ok": False,
                "reason": "agent_order_send_refused",
                "order_send": False,
                "agent_may_mutate_friend": False,
                "place_on_challenge": False,
                "redacted_account_idle": True,
            },
            indent=2,
        )
    )
    return 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--print-plan", action="store_true", default=True)
    parser.add_argument("--event", type=Path, default=None)
    parser.add_argument("--trade-record", type=Path, default=None)
    parser.add_argument("--ns", default="")
    parser.add_argument("--login", type=int, default=0)
    parser.add_argument("--price", type=float, default=0.0)
    parser.add_argument("--demo-ticket", default="")
    parser.add_argument("--demo-sl", type=float, default=0.0)
    parser.add_argument("--demo-tp", type=float, default=0.0)
    parser.add_argument(
        "--send",
        action="store_true",
        help="Refused. Agents never order_send.",
    )
    args = parser.parse_args(argv)
    if args.send:
        return _refuse_send()

    event = _load_json(args.event)
    record = _load_json(args.trade_record)
    plans: list[dict[str, Any]] = []
    if event is not None or record is not None:
        ns = args.ns or "redacted_account_f5_minimal"
        login = args.login or 0
        row = print_plan(
            event,
            record,
            ns=ns,
            login=login,
            price=args.price,
        )
        if args.demo_ticket:
            row["protection"] = protection_sync_plan(
                challenge_ticket=(event or {}).get("ticket") if event else None,
                demo_ticket=args.demo_ticket,
                demo_symbol=str((event or {}).get("symbol") or (record or {}).get("symbol") or ""),
                demo_sl=args.demo_sl,
                demo_tp=args.demo_tp,
                event=event,
                trade_record=record,
            )
        plans.append(row)
    else:
        for item in MEASURED_CHALLENGE_FILLS:
            ns = args.ns or str(item["ns"])
            login = args.login or int(item["login"])
            row = print_plan(
                item["event"],
                item["trade_record"],
                ns=ns,
                login=login,
                price=float(args.price or item["price"]),
            )
            row["protection"] = protection_sync_plan(
                challenge_ticket=item["event"]["ticket"],
                demo_ticket=item["demo_ticket"],
                demo_symbol=str(item["event"]["symbol"]),
                demo_sl=0.0,
                demo_tp=0.0,
                event=item["event"],
                trade_record=item["trade_record"],
            )
            plans.append(row)

    payload = {
        "ok": all(row.get("ok") for row in plans),
        "n": len(plans),
        "plans": plans,
        "order_send": False,
        "agent_may_mutate_friend": agent_may_mutate_friend(),
        "place_on_challenge": False,
        "redacted_account_idle": True,
        "never_flatten_challenge": True,
    }
    print(json.dumps(payload, indent=2, default=str))
    if not payload["ok"]:
        return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except FriendCopyError as exc:
        print(json.dumps({"ok": False, "reason": exc.reason, "order_send": False}, indent=2))
        raise SystemExit(2)
