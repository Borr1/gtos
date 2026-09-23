#!/usr/bin/env python3
"""Assemble G-2W / G-2M / G-10M gold_state JSONL. No TypeSafe call unless --call.

Uses bar dates we actually have. News questions abstain when the as-of is not
covered by a real spine. Never invents HIGH.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.judgment.bars import default_gold_paths, load_gold_books
from src.judgment.compose import compose_shadow
from src.judgment.gold_state import assemble_gold_state_v0
from src.judgment.jev_client import evaluate
from src.judgment.news_spine import load_spines

SLICES = {
    "G-2W": ("2026-04-10", "2026-04-24"),
    "G-2M": ("2026-02-24", "2026-04-24"),
    "G-10M": ("2025-06-24", "2026-04-24"),
}


def _parse(day: str) -> datetime:
    return datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slice", choices=sorted(SLICES), default="G-2W")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--call", action="store_true", help="POST Jev when a TypeSafe key is present (explicit on; default is already on if the key is in-process)")
    parser.add_argument("--every-n", type=int, default=1, help="Keep every Nth H4 bar")
    args = parser.parse_args()
    start, end = SLICES[args.slice]
    start_dt, end_dt = _parse(start), _parse(end).replace(hour=23, minute=59)
    books = load_gold_books(default_gold_paths())
    spines = load_spines()
    h4 = books.get("h4") or []
    out = args.out or (ROOT / "judgment" / "astra" / "lab" / "gold" / f"{args.slice.lower()}.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    n_sufficient = 0
    n_spine = 0
    with_flow = against = unclear = 0
    if args.call:
        os.environ["GTOS_JEV_A1_CALL"] = "1"
    with out.open("w", encoding="utf-8") as handle:
        for i, row in enumerate(h4):
            if row.utc < start_dt or row.utc > end_dt:
                continue
            if args.every_n > 1 and (i % args.every_n):
                continue
            # Long and short — owner: when gold goes up AND down.
            for side in ("long", "short"):
                state = assemble_gold_state_v0(
                    as_of_utc=row.utc,
                    side=side,
                    sleeve="metals_core",
                    symbol="XAUUSD",
                    origin_organism="historical_lab",
                    as_of_clock="as_of_open_study",
                    books=books,
                    spines=spines,
                    geometry={
                        "entry": row.bar.c,
                        "order_type": "MARKET",
                    },
                    sleeve_features={"tag": "metals_core", "session_hour": row.broker_naive.hour},
                )
                # Study geometry: 1.0 ATR stop if M15 ATR exists (labeled).
                atr = ((state.get("timeframes") or {}).get("m15") or {}).get("atr14")
                if atr:
                    state["geometry"]["stop_dist"] = atr
                    state["geometry"]["target_dist"] = 2.0 * atr
                    state["geometry"]["plan_r"] = 2.0
                    state["geometry"]["stop"] = row.bar.c - atr if side == "long" else row.bar.c + atr
                    state["geometry"]["target"] = row.bar.c + 2.0 * atr if side == "long" else row.bar.c - 2.0 * atr
                    state["completeness"]["geometry"] = True
                    state["completeness"]["geometry_atr_basis"] = "study_atr14_stop1_target2"
                    state["completeness"]["state_sufficient_for_live"] = (
                        state["completeness"]["timeframes_m15_h4_d1"]
                        and state["identity"]["family_class"] != "unknown"
                    )
                    if "geometry.stop_dist" in state["completeness"]["missing_fields"]:
                        state["completeness"]["missing_fields"].remove("geometry.stop_dist")
                answers = evaluate(state) if args.call else {"answers": {}, "ok": False, "skipped": "no_call"}
                composed = compose_shadow(state, answers.get("answers") or {})
                rec = {
                    "slice": args.slice,
                    "as_of_utc": state["clock"]["as_of_utc"],
                    "side": side,
                    "state": state,
                    "compose": composed,
                    "jev": {k: answers.get(k) for k in ("ok", "skipped", "error", "model")},
                }
                handle.write(json.dumps(rec, default=str) + "\n")
                n += 1
                n_sufficient += int(state["completeness"]["state_sufficient_for_live"])
                n_spine += int(not state["news"]["spine_empty"])
                stance = composed["local_flow_stance"]
                if stance == "with_flow":
                    with_flow += 1
                elif stance == "against_flow":
                    against += 1
                else:
                    unclear += 1
    summary = {
        "slice": args.slice,
        "window": [start, end],
        "n_rows": n,
        "n_sufficient": n_sufficient,
        "n_news_covering": n_spine,
        "local_flow": {"with": with_flow, "against": against, "unclear": unclear},
        "out": str(out),
        "paths": {k: str(v) for k, v in default_gold_paths().items()},
        "note": "news covering is 0 unless a real spine overlaps April 2026 — do not invent",
    }
    summary_path = out.with_suffix(".summary.json")
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0 if n else 3


if __name__ == "__main__":
    raise SystemExit(main())
