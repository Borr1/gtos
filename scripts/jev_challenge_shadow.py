#!/usr/bin/env python3
"""Score Challenge sit / replay / slate as living tissue. Log only. No place."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.judgment.bars import landed_challenge_symbols, load_all_landed_challenge_books, load_challenge_books
from src.judgment.challenge_shadow import (
    ACCOUNT,
    build_deal_tape,
    challenge_as_of,
    compact_ticket_row,
    iter_jsonl,
    load_json,
    score_deals,
    score_replay_row,
    score_sit,
    score_slate,
)
from src.judgment.host_events import DEFAULT_EVENTS, load_host_events
from src.judgment.news_spine import load_spines
from src.judgment.occupancy import refusal_tape
from src.judgment.two_stop import siblings_doc_for_label


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sit", type=Path, required=False)
    parser.add_argument(
        "--slate",
        type=Path,
        required=False,
        default=ROOT / "judgment/astra/lab/challenge_shadow_20260917/slate_20260917T104105Z_bddc8ff9fad4a254.json",
        help="Host latest_slate.json drop (pointer or body)",
    )
    parser.add_argument(
        "--deals",
        type=Path,
        default=ROOT / "judgment/astra/lab/challenge_shadow_20260917/deals_since_20260909.jsonl",
    )
    parser.add_argument("--replay", type=Path, default=None, help="Optional old replay pack; omit when deals cover the same tickets")
    parser.add_argument("--out", type=Path, default=ROOT / "judgment/astra/lab/challenge_shadow_20260917/shadow.jsonl")
    parser.add_argument("--ticket", type=int, default=293332188)
    parser.add_argument("--replay-limit", type=int, default=45)
    parser.add_argument(
        "--events",
        type=Path,
        default=DEFAULT_EVENTS,
        help="Challenge host events.jsonl (trail + news inventory). Never invents HIGH.",
    )
    args = parser.parse_args()
    books = load_all_landed_challenge_books() or load_challenge_books()
    spines = load_spines()
    host_events = load_host_events(args.events) if args.events and args.events.is_file() else []
    args.out.parent.mkdir(parents=True, exist_ok=True)
    sit = load_json(args.sit) if args.sit and args.sit.is_file() else None
    slate = load_json(args.slate) if args.slate and args.slate.is_file() else None
    deals = list(iter_jsonl(args.deals)) if args.deals and args.deals.is_file() else []
    tape = build_deal_tape(sit, deals)
    refusals = refusal_tape(slate)
    feature_rows: list = []
    if sit:
        feature_rows.extend(sit.get("positions") or [])
        feature_rows.extend(sit.get("closes_since_2026_09_15_18UTC") or [])
    feature_rows.extend(deals)
    siblings = siblings_doc_for_label(feature_rows, stamp=challenge_as_of)
    rows = []
    seen_tickets: set[str] = set()
    deferred_sit_closes: list[dict] = []
    if sit is not None:
        sit_rows = score_sit(
            sit,
            books=books,
            spines=spines,
            deal_tape=tape,
            refusals=refusals,
            siblings_doc=siblings,
            feature_rows=feature_rows,
            host_events=host_events,
        )
        # Sit opens own leave-orig. Sit closes lack spread/stop — prefer the deal row.
        for row in sit_rows:
            if row.get("kind") == "open":
                rows.append(row)
                if row.get("ticket") is not None:
                    seen_tickets.add(str(row.get("ticket")))
            else:
                deferred_sit_closes.append(row)
    if slate is not None:
        rows.extend(
            score_slate(
                slate,
                books=books,
                spines=spines,
                deal_tape=tape,
                refusals=refusals,
                siblings_doc=siblings,
                feature_rows=feature_rows,
                host_events=host_events,
            )
        )
    if deals:
        deal_rows = score_deals(
            deals,
            books=books,
            spines=spines,
            skip_tickets=seen_tickets,  # leave-orig opens only
            deal_tape=tape,
            refusals=refusals,
            siblings_doc=siblings,
            feature_rows=feature_rows,
            host_events=host_events,
        )
        rows.extend(deal_rows)
        seen_tickets.update(str(r.get("ticket")) for r in deal_rows if r.get("ticket") is not None)
    for row in deferred_sit_closes:
        ticket = str(row.get("ticket") or "")
        if ticket and ticket in seen_tickets:
            continue
        rows.append(row)
        if ticket:
            seen_tickets.add(ticket)
    if args.replay and args.replay.is_file():
        for i, rec in enumerate(iter_jsonl(args.replay)):
            if i >= args.replay_limit:
                break
            ticket = str((rec.get("input") or rec).get("ticket") or "")
            if ticket and ticket in seen_tickets:
                continue
            rows.append(score_replay_row(rec, books=books, spines=spines, host_events=host_events))
    with args.out.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, default=str) + "\n")
    families = Counter((r.get("house") or {}).get("family_class") for r in rows)
    kinds = Counter(r.get("kind") for r in rows)
    missing_tape = sum(1 for r in rows if "timeframes.m15" in (r.get("missing_state") or []))
    news_empty = sum(1 for r in rows if (r.get("compose") or {}).get("news_spine_empty"))
    cost_complete = sum(1 for r in rows if ((r.get("state") or {}).get("completeness") or {}).get("cost"))
    def _is_xau(row: dict) -> bool:
        return str(((row.get("state") or {}).get("identity") or {}).get("symbol") or row.get("symbol") or "") == "XAUUSD"

    n_sufficient = sum(
        1
        for r in rows
        if ((r.get("state") or {}).get("completeness") or {}).get("state_sufficient_for_live")
    )
    sufficient = sum(
        1
        for r in rows
        if _is_xau(r) and ((r.get("state") or {}).get("completeness") or {}).get("state_sufficient_for_live")
    )
    n_non_xau_sufficient = n_sufficient - sufficient
    cost_tilt_moved = sum(
        1
        for r in rows
        if abs(float((r.get("compose") or {}).get("shadow_cost_tilt") or 1.0) - 1.0) > 1e-9
    )
    flow_tilt_moved = sum(
        1
        for r in rows
        if abs(float((r.get("compose") or {}).get("shadow_size_tilt") or 1.0) - 1.0) > 1e-9
    )
    summary = {
        "account": ACCOUNT,
        "n": len(rows),
        "kinds": dict(kinds),
        "families": dict(families),
        "n_missing_m15": missing_tape,
        "n_news_empty": news_empty,
        "landed_symbols": landed_challenge_symbols(),
        "n_sufficient": n_sufficient,
        "n_xau_sufficient": sufficient,
        "n_non_xau_sufficient": n_non_xau_sufficient,
        "n_cost_complete": cost_complete,
        "n_shadow_cost_tilt_moved": cost_tilt_moved,
        "n_shadow_flow_tilt_moved": flow_tilt_moved,
        "live_size_tilt_locked": all(
            abs(float((r.get("compose") or {}).get("live_size_tilt") or 1.0) - 1.0) < 1e-9
            for r in rows
        ),
        "out": str(args.out),
        "never_place": True,
        "leave_orig_293332188": True,
    }
    summary_path = args.out.with_suffix(".summary.json")
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    if args.ticket is not None:
        hit = next((r for r in rows if str(r.get("ticket")) == str(args.ticket)), None)
        if hit is not None:
            ticket_path = args.out.parent / f"ticket_{args.ticket}.json"
            ticket_path.write_text(json.dumps(compact_ticket_row(hit), indent=2, default=str) + "\n")
            summary["ticket_out"] = str(ticket_path)
    print(json.dumps(summary, indent=2))
    return 0 if rows else 3


if __name__ == "__main__":
    raise SystemExit(main())
