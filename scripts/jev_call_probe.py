#!/usr/bin/env python3
"""≤200-call TypeSafe probe. POST immediately when a key is in THIS process.

Absence here is not a product limitation — redacted_account already has the key
(fingerprint sha256[:8]=00000000). This script records inheritance honestly:
if no key, http=never_sent and not_403=true. Never prints the key.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.judgment.bars import load_challenge_books
from src.judgment.challenge_shadow import compact_ticket_row, load_json, score_position
from src.judgment.jev_client import (
    redacted_account_KEY_FINGERPRINT,
    VPS_HOST,
    api_key,
    calls_remaining,
    calls_used,
    evaluate,
    host_paths_present,
    key_fingerprint,
    key_source,
    max_calls,
    reset_call_budget,
)
from src.judgment.news_spine import load_spines

DEFAULT_OUT = ROOT / "judgment" / "astra" / "lab" / "wires" / "JEV_CALL_PROBE.json"
SIT = ROOT / "judgment" / "astra" / "lab" / "challenge_shadow_20260917" / "sit_20260917.json"
TICKET = 293332188


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ticket_state() -> dict | None:
    if not SIT.is_file():
        return None
    sit = load_json(SIT)
    books = load_challenge_books()
    spines = load_spines()
    for pos in sit.get("positions") or []:
        if str(pos.get("ticket")) != str(TICKET):
            continue
        item = dict(pos)
        item["_kind"] = "open"
        row = score_position(item, books=books, spines=spines, sit_meta={})
        return row
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--timeout", type=float, default=8.0)
    args = parser.parse_args()
    reset_call_budget()
    present = api_key() is not None
    fp = key_fingerprint()
    receipt: dict = {
        "schema": "gtos.judgment.jev_call_probe.v0",
        "probed_at_utc": _now(),
        "never_print_key": True,
        "never_place": True,
        "leave_orig_293332188": True,
        "boe_sit_leave_orig": True,
        "boe_print_approx_utc": "2026-09-17T11:01:00Z",
        "boe_sit_open_r_approx": 0.6,
        "max_calls": max_calls(),
        "inherited": present,
        "key_source": key_source(),
        "key_fingerprint": fp,
        "expected_redacted_account_fingerprint_sha256_8": redacted_account_KEY_FINGERPRINT,
        "fingerprint_matches_redacted_account": (fp == redacted_account_KEY_FINGERPRINT) if fp else False,
        "vps_host": VPS_HOST,
        "vps_wired": True,
        "host_paths_present": host_paths_present(),
        "not_limitation": True,
        "posts": [],
    }
    if not present:
        receipt.update(
            {
                "http": "never_sent",
                "not_403": True,
                "n_posted": 0,
                "calls_used": 0,
                "calls_remaining": max_calls(),
                "shadow_with_real_answers": False,
                "route": "redacted_account_box_or_vps_redacted_host",
                "note": (
                    "This Cloud VM did not inherit TYPESAFE_API_KEY / TYPESAFE_KEY / "
                    "secrets/TYPESAFE_API_KEY.txt / .env.typesafe. Request never sent. "
                    "Not a 403. VPS redacted_host is wired (fp 00000000). Route "
                    "python scripts/jev_host_systemone_shadow.py through redacted_account or the VPS."
                ),
            }
        )
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({k: receipt[k] for k in (
            "inherited", "http", "not_403", "n_posted", "key_source", "key_fingerprint",
            "leave_orig_293332188",
        )}))
        return 0

    # Key is here — POST immediately. Budget: 1 ping + ticket fanout. Stay ≪ 200.
    ping = evaluate({"identity": {"symbol": "XAUUSD", "probe": "ping"}}, timeout_s=args.timeout)
    receipt["posts"].append(
        {
            "kind": "ping",
            "ok": ping.get("ok"),
            "skipped": ping.get("skipped"),
            "error": ping.get("error"),
            "http_status": ping.get("http_status"),
            "n_answers": len(ping.get("answers") or {}),
        }
    )
    ticket_row = _ticket_state()
    ticket_jev = None
    if ticket_row is not None:
        # score_position already called evaluate once (second POST). Compact it.
        ticket_jev = ticket_row.get("jev") or {}
        receipt["posts"].append(
            {
                "kind": "ticket_293332188",
                "ok": ticket_jev.get("ok"),
                "skipped": ticket_jev.get("skipped"),
                "error": ticket_jev.get("error"),
                "http_status": ticket_jev.get("http_status"),
                "leave_orig": True,
                "live_size_tilt": (ticket_row.get("compose") or {}).get("live_size_tilt"),
                "n_answers": len(ticket_row.get("answers") or {}),
            }
        )
        ticket_path = args.out.parent / "ticket_293332188_called.json"
        ticket_path.write_text(
            json.dumps(compact_ticket_row(ticket_row), indent=2, default=str) + "\n",
            encoding="utf-8",
        )
        receipt["ticket_called_out"] = str(ticket_path.relative_to(ROOT))

    http_codes = [p.get("http_status") for p in receipt["posts"] if p.get("http_status") is not None]
    errors = [p.get("error") for p in receipt["posts"] if p.get("error")]
    receipt.update(
        {
            "http": http_codes[0] if http_codes else (errors[0] if errors else "sent"),
            "not_403": 403 not in http_codes and "http_403" not in errors,
            "n_posted": calls_used(),
            "calls_used": calls_used(),
            "calls_remaining": calls_remaining(),
            "shadow_with_real_answers": any(p.get("ok") for p in receipt["posts"]),
            "note": (
                "Key inherited in this process; POSTs counted against the 200 budget. "
                "Ticket 293332188 leave orig. APPLY still closed."
            ),
        }
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({
        "inherited": True,
        "http": receipt["http"],
        "not_403": receipt["not_403"],
        "n_posted": receipt["n_posted"],
        "key_fingerprint": fp,
        "shadow_with_real_answers": receipt["shadow_with_real_answers"],
        "leave_orig_293332188": True,
    }))
    return 0 if receipt.get("not_403") else 3


if __name__ == "__main__":
    raise SystemExit(main())
