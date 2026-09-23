#!/usr/bin/env python3
"""Write gtos.f5.judge.verdict.v1 bound to the latest slate fingerprint.

The CHAIR's only write to the book. Never a copier of an unbound payload.
Usage:
  python write_inbox_verdict.py --repo ROOT [--abstain] [--memory LINE] ...
  python write_inbox_verdict.py --repo ROOT --stdin   # JSON body, fingerprint overwritten
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from scripts.f5_desk import common

SCHEMA = "gtos.f5.judge.verdict.v1"
MECHANISMS = frozenset({
    "microstructure", "correlation", "event_proximity", "weekend_carry",
    "container_broken", "owner_word", "",
})


def _slate_paths(repo: Path) -> Path:
    return common.judgment_state_dir(repo) / "state" / "latest_slate.json"


def _inbox_path(repo: Path) -> Path:
    return common.judgment_state_dir(repo) / "inbox" / "verdict.json"


def load_slate(repo: Path) -> dict:
    slate = common.read_json(_slate_paths(repo), default={}) or {}
    if not isinstance(slate, dict):
        slate = {}
    # pointer file may wrap the slate
    inner = slate.get("slate") if isinstance(slate.get("slate"), dict) else slate
    return inner if isinstance(inner, dict) else {}


def bind(payload: dict, slate: dict) -> dict:
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    out = dict(payload)
    out["schema"] = SCHEMA
    out["slate_id"] = slate.get("slate_id") or out.get("slate_id") or ""
    out["fingerprint"] = slate.get("fingerprint") or out.get("fingerprint") or ""
    out["written_at_utc"] = now
    out.setdefault("verdicts", [])
    out.setdefault("manage", [])
    out.setdefault("memory", [])
    if not out["fingerprint"] and not out["slate_id"]:
        raise SystemExit("latest_slate.json has no slate_id or fingerprint; refuse unbound verdict")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Write a slate-bound F5 inbox verdict")
    ap.add_argument("--repo", type=Path, default=common.repo_root_default())
    ap.add_argument("--stdin", action="store_true")
    ap.add_argument("--abstain-all", action="store_true")
    ap.add_argument("--memory", action="append", default=[])
    ap.add_argument("--hold", nargs=3, metavar=("CANDIDATE_ID", "MECHANISM", "WHY"), action="append", default=[])
    ap.add_argument("--approve", metavar="CANDIDATE_ID", action="append", default=[])
    ap.add_argument("--manage", nargs=4, metavar=("TICKET", "ACTION", "MECHANISM", "WHY"), action="append", default=[])
    args = ap.parse_args(argv)

    repo = Path(args.repo)
    slate = load_slate(repo)
    if args.stdin:
        raw = json.loads(sys.stdin.read() or "{}")
        if not isinstance(raw, dict):
            raise SystemExit("stdin must be a JSON object")
        payload = raw
    else:
        verdicts = []
        for cid in args.approve or []:
            verdicts.append({
                "candidate_id": cid, "verdict": "approve",
                "mechanism": "", "why_code": "chair_approve", "confidence": 0.0,
            })
        for cid, mech, why in args.hold or []:
            if mech not in MECHANISMS:
                raise SystemExit(f"unknown hold mechanism {mech}")
            verdicts.append({
                "candidate_id": cid, "verdict": "hold",
                "mechanism": mech, "why_code": why, "confidence": 0.0,
            })
        if args.abstain_all and not verdicts:
            for cand in slate.get("candidates") or []:
                cid = cand.get("candidate_id") if isinstance(cand, dict) else None
                if cid:
                    verdicts.append({
                        "candidate_id": cid, "verdict": "abstain",
                        "mechanism": "", "why_code": "no_mechanism", "confidence": 0.0,
                    })
        manage = []
        for ticket, action, mech, why in args.manage or []:
            manage.append({
                "ticket": int(ticket), "action": action, "new_stop": None,
                "mechanism": mech, "why_code": why, "ttl_s": 1800,
            })
        payload = {"verdicts": verdicts, "manage": manage, "memory": list(args.memory or [])}

    bound = bind(payload, slate)
    dst = _inbox_path(repo)
    ok = common.write_json_atomic(dst, bound)
    if not ok:
        raise SystemExit(f"failed to write {dst}")
    print(json.dumps({
        "wrote": str(dst),
        "slate_id": bound["slate_id"],
        "fingerprint": bound["fingerprint"],
        "n_verdicts": len(bound.get("verdicts") or []),
        "written_at_utc": bound["written_at_utc"],
        "schema": bound["schema"],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
