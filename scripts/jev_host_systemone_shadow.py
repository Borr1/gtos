#!/usr/bin/env python3
"""Host/VPS System One shadow. POST real answers when a key is in-process.

On VPS redacted_host the key is User env + secrets/TYPESAFE_API_KEY.txt +
.gitignored .env.typesafe. This Cloud VM does not inherit those — it records
never_sent (not 403) and tells the chair to route through redacted_account/VPS.

Budget ≤200. Ticket 293332188 leave orig. Never places. Never prints the key.
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

from src.judgment.compose import compose_shadow
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

DEFAULT_SHADOW = ROOT / "judgment/astra/lab/challenge_shadow_20260917/shadow.jsonl"
DEFAULT_OUT = ROOT / "judgment/astra/lab/wires/SYSTEMONE_SHADOW.jsonl"
TICKET = "293332188"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _is_sufficient(row: dict) -> bool:
    return bool(((row.get("state") or {}).get("completeness") or {}).get("state_sufficient_for_live"))


def _is_xau(row: dict) -> bool:
    ident = (row.get("state") or {}).get("identity") or {}
    return str(ident.get("symbol") or row.get("symbol") or "") == "XAUUSD"


def _is_xau_sufficient(row: dict) -> bool:
    return _is_xau(row) and _is_sufficient(row)


def _iter_targets(path: Path, limit: int):
    if not path.is_file():
        return
    ticket_row = None
    others: list[dict] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if str(row.get("ticket")) == TICKET:
                ticket_row = row
                continue
            if _is_sufficient(row):
                others.append(row)
    others.sort(key=lambda r: (0 if _is_xau(r) else 1))
    if ticket_row is not None:
        yield ticket_row
    for row in others[: max(0, limit - (1 if ticket_row is not None else 0))]:
        yield row


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shadow", type=Path, default=DEFAULT_SHADOW)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--limit", type=int, default=28, help="XAU sufficient rows after the leave-orig ticket")
    parser.add_argument("--timeout", type=float, default=8.0)
    args = parser.parse_args()
    reset_call_budget()
    present = api_key() is not None
    fp = key_fingerprint()
    summary = {
        "schema": "gtos.judgment.systemone_shadow.v0",
        "ran_at_utc": _now(),
        "vps_host": VPS_HOST,
        "never_print_key": True,
        "never_place": True,
        "leave_orig_293332188": True,
        "wire_apply": False,
        "max_calls": max_calls(),
        "inherited": present,
        "key_source": key_source(),
        "key_fingerprint": fp,
        "expected_fingerprint_sha256_8": redacted_account_KEY_FINGERPRINT,
        "fingerprint_matches": (fp == redacted_account_KEY_FINGERPRINT) if fp else False,
        "host_paths_present": host_paths_present(),
        "not_limitation": True,
    }
    if not present:
        summary.update(
            {
                "http": "never_sent",
                "not_403": True,
                "n_posted": 0,
                "n_real_answers": 0,
                "shadow_with_real_answers": False,
                "route": "redacted_account_box_or_vps_redacted_host",
                "note": (
                    "This process has no TypeSafe key (env / secrets/TYPESAFE_API_KEY.txt / "
                    ".env.typesafe all absent). Request never sent. Not a 403. "
                    f"VPS {VPS_HOST} is wired (fp 00000000). Route this command through "
                    "redacted_account box or the VPS: python scripts/jev_host_systemone_shadow.py"
                ),
            }
        )
        args.out.parent.mkdir(parents=True, exist_ok=True)
        summary_path = args.out.with_suffix(".summary.json")
        summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({k: summary[k] for k in (
            "inherited", "http", "not_403", "n_posted", "route", "leave_orig_293332188",
        )}))
        return 0

    args.out.parent.mkdir(parents=True, exist_ok=True)
    n_ok = 0
    n_err = 0
    http_codes: list[int] = []
    with args.out.open("w", encoding="utf-8") as handle:
        for row in _iter_targets(args.shadow, args.limit):
            if calls_remaining() <= 0:
                break
            state = row.get("state") or {}
            jev = evaluate(state, timeout_s=args.timeout)
            composed = compose_shadow(state, jev.get("answers") or {})
            out = {
                "schema": "gtos.judgment.systemone_shadow_row.v0",
                "ticket": row.get("ticket"),
                "kind": row.get("kind"),
                "leave_orig": str(row.get("ticket")) == TICKET,
                "jev": {k: jev.get(k) for k in ("ok", "skipped", "error", "http_status", "model", "key_fingerprint")},
                "n_answers": len(jev.get("answers") or {}),
                "answers": jev.get("answers") or {},
                "compose": composed,
                "live_size_tilt": composed.get("live_size_tilt"),
                "wire_apply": False,
            }
            handle.write(json.dumps(out, default=str) + "\n")
            if jev.get("http_status") is not None:
                http_codes.append(int(jev["http_status"]))
            if jev.get("ok"):
                n_ok += 1
            elif jev.get("error"):
                n_err += 1
    summary.update(
        {
            "http": http_codes[0] if http_codes else "sent",
            "not_403": 403 not in http_codes,
            "n_posted": calls_used(),
            "n_real_answers": n_ok,
            "n_http_error": n_err,
            "shadow_with_real_answers": n_ok > 0,
            "out": str(args.out),
            "note": (
                "Key present in this process; System One answers written. "
                "Ticket 293332188 leave orig. APPLY still closed."
            ),
        }
    )
    summary_path = args.out.with_suffix(".summary.json")
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "inherited": True,
        "http": summary["http"],
        "not_403": summary["not_403"],
        "n_posted": summary["n_posted"],
        "n_real_answers": n_ok,
        "key_fingerprint": fp,
        "leave_orig_293332188": True,
    }))
    return 0 if summary.get("not_403") else 3


if __name__ == "__main__":
    raise SystemExit(main())
