"""Counterfactual: what would `skip_first_ny_candle` skip if the bug was fully fixed?

Scans `knowledge_base/live_evaluations/XAUUSD/*.jsonl` and identifies the
M15 evaluation that processes the 13:00-opening NY-open candle on XAUUSD.

CADENCE NOTE
============
The orchestrator wakes at the next M15 close (xx:00 / xx:15 / xx:30 / xx:45)
and processes the candle that just closed. The "13:00 candle" is the M15
bar that opens at 13:00 UTC and closes at 13:15 UTC. Therefore the
orchestrator's evaluation of the 13:00-opening NY-open candle has a wall
clock timestamp of approximately 13:15:NN.

In the live_evaluations log, this is the entry whose ``timestamp`` (or
``candle_time``) minute-of-day falls in [13:15, 13:30). We treat the
13:15-bucket as the canonical "first NY candle" evaluation per day.

CAVEAT (separate window-bounds bug found during R2)
===================================================
The original orchestrator skip condition reads
``ny_start <= now < ny_start + 15`` (i.e., 13:00 - 13:15 wall-clock).
But the orchestrator only wakes on M15 close boundaries — and the
13:00-opening candle is processed at ~13:15:NN, NOT 13:00:NN. Even
once the config-lookup bug is fixed (R2's targeted change), the skip
would still never fire on the intended candle without ALSO updating
the window bound to ``ny_start + 15 <= now < ny_start + 30``.

This script reports the counterfactual under the FIXED-INTENT interpretation:
"what if the orchestrator skipped the 13:00-opening NY-open candle?"
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parents[1] / "knowledge_base" / "live_evaluations" / "XAUUSD"
TRADE_INDEX = Path(__file__).resolve().parents[1] / "knowledge_base" / "index" / "_trade_index.json"

NY_FIRST_CANDLE_PROCESSING_WINDOW_START = 13 * 60 + 15  # 13:15:00
NY_FIRST_CANDLE_PROCESSING_WINDOW_END = 13 * 60 + 30   # 13:30:00 (exclusive)


def minute_of_day(ts: str) -> int:
    dt = datetime.fromisoformat(ts)
    return dt.hour * 60 + dt.minute


def in_first_ny_processing_window(ts: str) -> bool:
    mod = minute_of_day(ts)
    return NY_FIRST_CANDLE_PROCESSING_WINDOW_START <= mod < NY_FIRST_CANDLE_PROCESSING_WINDOW_END


def extract_eval_timestamp(rec: dict) -> str | None:
    """Wall-clock at orchestrator wake (this is when the skip check would
    fire if working). live_evaluations schema uses ``timestamp``."""
    return rec.get("timestamp") or rec.get("timestamp_utc")


def main() -> None:
    files = sorted(EVAL_DIR.glob("*.jsonl"))
    print(f"XAUUSD evaluation files: {len(files)}")
    if not files:
        print("No evaluation files found — aborting")
        return
    print(f"Date range: {files[0].stem} .. {files[-1].stem}")

    start_date = datetime.fromisoformat(files[0].stem).date()
    end_date = datetime.fromisoformat(files[-1].stem).date()
    span_days = (end_date - start_date).days + 1
    print(f"Span: {span_days} calendar days, {len(files)} with data\n")

    decisions: Counter[str] = Counter()
    candidates: list[dict] = []
    all_window_hits: list[dict] = []
    per_date_hits: dict[str, list] = defaultdict(list)
    total_evals_scanned = 0

    for path in files:
        date_tag = path.stem
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                total_evals_scanned += 1
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ts = extract_eval_timestamp(rec)
                if not ts or not in_first_ny_processing_window(ts):
                    continue

                decision = rec.get("decision", "UNKNOWN")
                decisions[decision] += 1
                hit = {
                    "date": date_tag,
                    "timestamp": ts,
                    "candle_time": rec.get("candle_time"),
                    "decision": decision,
                    "kill_zone": rec.get("kill_zone"),
                    "setup_grade": rec.get("setup_grade"),
                    "framework": rec.get("framework"),
                }
                all_window_hits.append(hit)
                per_date_hits[date_tag].append(hit)
                if decision == "CANDIDATE":
                    candidates.append({
                        **hit,
                        "direction": rec.get("direction"),
                        "entry_price": rec.get("entry_price"),
                        "stop_loss": rec.get("stop_loss"),
                        "take_profit_1": rec.get("take_profit_1"),
                        "h1_zone": rec.get("h1_zone"),
                        "sweep_type": rec.get("sweep_type"),
                        "m15_displacement_quality": rec.get("m15_displacement_quality"),
                    })

    print(f"Total XAUUSD evals scanned: {total_evals_scanned:,}")
    print(f"Evals processing the 13:00-opening NY-open candle "
          f"(wake at 13:15-13:29 UTC): {len(all_window_hits)}")
    print(f"Decision breakdown:")
    for dec, n in decisions.most_common():
        print(f"  {dec}: {n}")

    print("\nPer-date 13:00-candle eval (one row per live trading day):")
    for d in sorted(per_date_hits):
        for h in per_date_hits[d]:
            print(f"  {d}  ts={h['timestamp']}  dec={h['decision']:9s}  "
                  f"grade={h.get('setup_grade')}  fw={h.get('framework')}")

    print(f"\nCANDIDATEs in window: {len(candidates)}")
    for c in candidates:
        print(f"\n  {c['date']} @ {c['timestamp']}  kz={c.get('kill_zone')}")
        print(f"    framework: {c.get('framework')} | grade: {c.get('setup_grade')}")
        print(f"    direction: {c.get('direction')}  entry={c.get('entry_price')}  "
              f"sl={c.get('stop_loss')}  tp1={c.get('take_profit_1')}")
        print(f"    h1_zone: {c.get('h1_zone')}  sweep: {c.get('sweep_type')}  "
              f"displ: {c.get('m15_displacement_quality')}")

    # Cross-reference candidate dates against the trade index for outcomes.
    # Trade IDs are typically formatted like XAUUSD_2026-04-15_NY_001.
    print("\nMatching CANDIDATE dates to trade_index outcomes (if any):")
    if TRADE_INDEX.exists():
        with open(TRADE_INDEX, encoding="utf-8") as fh:
            tindex = json.load(fh)
        trades = tindex.get("trades", [])
        for c in candidates:
            cdate = c["date"]
            matches = [
                t for t in trades
                if t.get("symbol") == "XAUUSD"
                and t.get("date") == cdate
                and (t.get("kill_zone") or "").lower() == "ny"
            ]
            print(f"  {cdate}: {len(matches)} matching XAUUSD/NY trades in index")
            for m in matches:
                print(f"    trade_id={m.get('trade_id')}  outcome={m.get('outcome')}  "
                      f"r={m.get('r_multiple')}  exit={m.get('exit_type')}")
    else:
        print(f"  (trade_index not found at {TRADE_INDEX})")


if __name__ == "__main__":
    main()
