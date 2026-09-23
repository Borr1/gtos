"""One-shot backfill for the 2026-04-28 GBPJPY trade close.

Yesterday's GBPJPY LIMIT (placed by ``GBPJPY_2026-04-28_london_0900``) filled
at 09:30:06 UTC and exited at 15:31:06 UTC at +$1,380.81 (+0.738R). The
orchestrator's exit-detection path used ``self._last_tick_price`` (the bid
at detection time) and ``datetime.now(UTC)`` instead of querying MT5 deal
history, recording -0.0365R at 09:30:05 UTC at price 215.26.

Three downstream artifacts inherited the wrong data:

1. ``knowledge_base/trade_records/GBPJPY/2026-04-28_london_0900.json`` — exit
2. ``shadow_logs/daily_pnl.json``                              — result_r
3. ``shadow_logs/j46_j49_shadow_outcomes.jsonl``               — realized_R

This script reads the actual MT5 deal data and rewrites those three files.
The orchestrator-side fix (``_finalize_exit`` deal reconciliation, shipped
in the same commit) prevents this class of corruption going forward.

Run: ``python scripts/backfill_2026_04_28_gbpjpy_close.py``
The script makes ``.bak`` backups next to each rewritten file.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

# Actual values from MT5 history_deals_get(position=233955223):
#   entry  ticket=218505373  type=BUY   price=215.275  time=09:30:06 UTC
#   exit   ticket=218653828  type=SELL  price=215.559  time=15:31:06 UTC  profit=+$1380.81
#
# sl_distance from actual filled entry: 215.275 - 214.890 = 0.385
# realized_R = (215.559 - 215.275) / 0.385 = +0.738
ACTUAL = {
    "entry_price": 215.275,
    "entry_time_utc": "2026-04-28T09:30:06+00:00",
    "exit_price": 215.559,
    "exit_time_utc": "2026-04-28T15:31:06+00:00",
    "stop_loss": 214.89,
    "sl_distance": 0.385,  # actual fill (not 0.411 of proposed entry)
    "realized_R": 0.738,
    "profit_usd": 1380.81,
    "hold_minutes": 361,  # 09:30 -> 15:31 = 6h 1m = 361 min
    "ticket": 233955223,
    "exit_reason": "ny_close_force",  # bug-cascade force-close at end of NY
}


def backup(path: Path) -> None:
    if path.exists():
        bak = path.with_suffix(path.suffix + ".bak")
        if not bak.exists():
            shutil.copy2(path, bak)
            print(f"  backed up: {bak}")


def fix_trade_record() -> None:
    p = Path("knowledge_base/trade_records/GBPJPY/2026-04-28_london_0900.json")
    backup(p)
    d = json.loads(p.read_text(encoding="utf-8"))

    old_exit = d.get("exit", {})
    new_exit = {
        "exit_type": "broker_closed",
        "exit_price": ACTUAL["exit_price"],
        "exit_time": ACTUAL["exit_time_utc"],
        "actual_r": round(ACTUAL["realized_R"], 4),
        "hold_time_minutes": ACTUAL["hold_minutes"],
        # Preserve MFE/MAE if present (they were never recorded for this
        # trade but the schema expects the keys).
        "mfe_price": old_exit.get("mfe_price", ACTUAL["exit_price"]),
        "mfe_r": round(ACTUAL["realized_R"], 4),  # we know the exit hit ≥ this R
        "mae_price": old_exit.get("mae_price", ACTUAL["entry_price"]),
        "mae_r": 0.0,
        "partial_closes": old_exit.get("partial_closes", []),
        "exit_reason": ACTUAL["exit_reason"],
        "realized_R": round(ACTUAL["realized_R"], 4),
        "time_in_trade_minutes": ACTUAL["hold_minutes"],
        # Provenance: this record was rewritten from MT5 deal history because
        # the original exit-detection path used the wrong (detection-time) bid.
        "broker_deal_reconciled": True,
        "backfill_note": (
            "Rewritten 2026-04-29 from MT5 history_deals_get(position=233955223). "
            "Original exit recorded -0.0365R at 215.26 / 09:30:05 UTC; actual "
            "MT5 close at +0.738R, 215.559 / 15:31:06 UTC, profit +$1,380.81."
        ),
    }
    d["exit"] = new_exit
    p.write_text(json.dumps(d, indent=2), encoding="utf-8")
    print(f"  rewrote {p.name}: realized_R -0.0365 -> +0.738")


def fix_daily_pnl() -> None:
    p = Path("shadow_logs/daily_pnl.json")
    backup(p)
    d = json.loads(p.read_text(encoding="utf-8"))
    if d.get("date") != "2026-04-28":
        print(f"  daily_pnl.json date={d.get('date')} — not 2026-04-28, skipping")
        return
    d["trades"] = [
        {
            "symbol": "GBPJPY",
            "result_r": round(ACTUAL["realized_R"], 4),
            "exit_type": "broker_closed",
            "time": "15:31",  # was 09:30
            "broker_deal_reconciled": True,
        }
    ]
    d["total_r"] = round(ACTUAL["realized_R"], 4)
    d["wins"] = 1
    d["losses"] = 0
    d["backfill_note"] = (
        "Rewritten 2026-04-29 from MT5 deal history. Original recorded "
        "-0.0365R / time 09:30; actual +0.738R / 15:31 / +$1,380.81."
    )
    p.write_text(json.dumps(d, indent=2), encoding="utf-8")
    print(f"  rewrote {p.name}: total_r -0.0365 -> +0.738, wins 0->1")


def fix_j46_j49_shadow() -> None:
    p = Path("shadow_logs/j46_j49_shadow_outcomes.jsonl")
    backup(p)
    lines = p.read_text(encoding="utf-8").strip().splitlines()
    out_lines: list[str] = []
    rewrote = 0
    for line in lines:
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            out_lines.append(line)
            continue
        if r.get("fill_id") == "GBPJPY_2026-04-28_london_0900":
            r["actual_close"] = {
                "exit_price": ACTUAL["exit_price"],
                "exit_time": ACTUAL["exit_time_utc"],
                "exit_reason": ACTUAL["exit_reason"],
                "realized_R": round(ACTUAL["realized_R"], 4),
                "broker_deal_reconciled": True,
            }
            # Recompute delta_r vs the hypothetical_old (kept as-is — that
            # row's hypothetical was a counterfactual, which is independent
            # of the actual exit data).
            hypo_r = float(r.get("hypothetical_old", {}).get("hypothetical_R", 0))
            r["delta_r"] = round(ACTUAL["realized_R"] - hypo_r, 4)
            r["shadow_better"] = r["delta_r"] > 0
            r["backfill_note"] = (
                "Rewritten 2026-04-29 from MT5 deal history; original carried "
                "the orchestrator's broken -0.0365R reading."
            )
            rewrote += 1
        out_lines.append(json.dumps(r))
    p.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    print(f"  rewrote {p.name}: {rewrote} row(s) corrected")


def already_applied() -> bool:
    """Idempotency guard — return True if the backfill has already run.

    Detection: the trade_record's ``exit.broker_deal_reconciled`` flag is
    set ONLY by this script. If it's already True, re-running would
    overwrite any subsequent manual edits with stale ACTUAL values.
    """
    p = Path("knowledge_base/trade_records/GBPJPY/2026-04-28_london_0900.json")
    if not p.exists():
        return False
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        return bool((d.get("exit") or {}).get("broker_deal_reconciled"))
    except (OSError, json.JSONDecodeError):
        return False


def main() -> None:
    print("Backfilling 2026-04-28 GBPJPY close (actual: +0.738R / +$1,380.81)")
    print()
    if already_applied():
        print("ALREADY APPLIED — trade_record has broker_deal_reconciled=true.")
        print("Re-run guard: refusing to overwrite. To force, delete that flag from the")
        print("trade_record's exit field and re-execute. Existing .bak files are preserved.")
        return
    fix_trade_record()
    fix_daily_pnl()
    fix_j46_j49_shadow()
    print()
    print("Done. .bak files written next to each rewritten file.")


if __name__ == "__main__":
    main()
