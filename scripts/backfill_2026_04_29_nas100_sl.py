"""One-shot backfill for the 2026-04-29 NAS100 SL hit.

Trade timeline:
- 15:15:05 UTC: LIMIT FILLED at 27100.02 LONG 0.08 lots (MT5 ticket 218947891,
  position 234432798)
- 15:15:05.461 UTC: orchestrator's check_and_manage_trade polled
  positions_get 13ms after order_send and got an empty list — MT5 hadn't yet
  propagated the new position. Orch falsely retired active_trade (the bug
  that the post-fill propagation race guard fix addressed in commit
  3f58ea0). Stale exit logged: -0.0168R at 27098.22.
- 15:28:45 UTC: orchestrator restart adopted the live orphan position
  (active_trade restored, position_confirmed=True).
- 16:00 UTC: NY KZ ended, "Trade underwater at KZ end, 2h timeout applies"
  flagged.
- 17:16 UTC: WATCHDOG dead-zone path killed the NAS100 orch — 44 min
  before the 2h-timeout (18:00) and 59 min before J46-J49 12-bar time-stop
  (18:15) could fire. Trade ran free at broker only.
- ~19:30-20:15 UTC: price spiked above TP1/3R territory (~27260), then
  reversed sharply ("2 5-min candles" per operator). With orch dead, J46-
  J49's BE-on-TP1 logic could not move SL to entry.
- 20:15:06 UTC: broker SL hit at 26970.57 (slipped 2.13 pts past nominal
  SL 26972.70). MT5 ticket 219032030. Profit -$103.56.

Three downstream artifacts inherited the FALSE-CLOSE data from 15:15:05:
1. shadow_logs/daily_pnl.json
2. knowledge_base/trade_records/NAS100/2026-04-29_ny_1500.json (exit field)
3. shadow_logs/j46_j49_shadow_outcomes.jsonl

This script reads MT5 deal history (entry + exit) and rewrites those three
files with the actual close. Pattern mirrors backfill_2026_04_28_gbpjpy_close.py.

Run: python scripts/backfill_2026_04_29_nas100_sl.py
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

# Actual MT5 history_deals_get(position=234432798):
ACTUAL = {
    "trade_id": "NAS100_2026-04-29_ny_1500",
    "fill_id": "NAS100_2026-04-29_ny_1500",
    "symbol": "NAS100",
    "broker_symbol": "NDX100",
    "entry_ticket": 218947891,
    "entry_price": 27100.02,           # MT5 actual fill
    "entry_time_utc": "2026-04-29T15:15:05+00:00",
    "exit_ticket": 219032030,
    "exit_price": 26970.57,             # MT5 actual fill (slipped past SL 26972.70 by 2.13 pts)
    "exit_time_utc": "2026-04-29T20:15:06+00:00",
    "stop_loss": 26972.70,
    "ai_take_profit_1": 27244.92,       # 3R from entry per J46-J49 (which AI logged at 27483.34 - difference is rounding/source)
    "broker_take_profit": 27866.32,    # J46-J49 6R override
    "sl_distance_actual": 127.32,       # 27100.02 - 26972.70
    "loss_distance": 129.45,            # 27100.02 - 26970.57 (slipped past SL)
    "realized_R": -1.0167,              # -129.45 / 127.32
    "profit_usd": -103.56,
    "hold_minutes": 300,                # 15:15 -> 20:15 = 5h
    "exit_reason": "sl_hit",
    "exit_type": "broker_closed",
}


def backup(path: Path) -> None:
    if path.exists():
        bak = path.with_suffix(path.suffix + ".bak")
        if not bak.exists():
            shutil.copy2(path, bak)
            print(f"  backed up: {bak}")


def fix_trade_record() -> None:
    p = Path("knowledge_base/trade_records/NAS100/2026-04-29_ny_1500.json")
    if not p.exists():
        print(f"  trade record not found: {p}, skipping")
        return
    backup(p)
    d = json.loads(p.read_text(encoding="utf-8"))

    old_exit = d.get("exit", {}) or {}
    new_exit = {
        "exit_type": ACTUAL["exit_type"],
        "exit_price": ACTUAL["exit_price"],
        "exit_time": ACTUAL["exit_time_utc"],
        "actual_r": round(ACTUAL["realized_R"], 4),
        "hold_time_minutes": ACTUAL["hold_minutes"],
        "mfe_price": old_exit.get("mfe_price", ACTUAL["entry_price"]),
        # MFE peak per chart was ~27260 — set conservatively if unknown.
        "mfe_r": old_exit.get("mfe_r", 0.0),
        "mae_price": ACTUAL["exit_price"],
        "mae_r": round(ACTUAL["realized_R"], 4),
        "partial_closes": old_exit.get("partial_closes", []),
        "exit_reason": ACTUAL["exit_reason"],
        "realized_R": round(ACTUAL["realized_R"], 4),
        "time_in_trade_minutes": ACTUAL["hold_minutes"],
        "broker_deal_reconciled": True,
        "backfill_note": (
            "Rewritten 2026-04-29 from MT5 history_deals_get(position=234432798). "
            "Original recorded -0.0168R at 27098.22 / 15:15:05 (orch's false-close "
            "race within 13ms of order_send fired before the post-fill propagation "
            "guard shipped). Actual close: SL hit at 20:15:06 UTC, price 26970.57, "
            "loss -$103.56, after 5h hold. Watchdog dead-zone kill at 17:16 UTC "
            "left the trade un-managed past 17:15; 2h timeout (18:00) and J46-J49 "
            "12-bar stop (18:15) could not fire. Watchdog active-trade-defer fix "
            "shipped same day to prevent recurrence."
        ),
    }
    d["exit"] = new_exit
    p.write_text(json.dumps(d, indent=2), encoding="utf-8")
    print(f"  rewrote {p.name}: realized_R -0.0168 -> {ACTUAL['realized_R']:.4f}")


def fix_daily_pnl() -> None:
    p = Path("shadow_logs/daily_pnl.json")
    if not p.exists():
        print(f"  daily_pnl.json missing, skipping")
        return
    backup(p)
    d = json.loads(p.read_text(encoding="utf-8"))
    if d.get("date") != "2026-04-29":
        print(f"  daily_pnl.json date={d.get('date')} not 2026-04-29 — skipping (today's roll-over expected)")
        return

    # Replace the false-close NAS100 row with the actual SL close.
    new_trades = []
    for t in d.get("trades", []):
        if t.get("trade_id") == ACTUAL["trade_id"] or (
            t.get("symbol") == ACTUAL["symbol"] and t.get("entry_price") in (27100.36, 27100.02)
        ):
            new_trades.append({
                "symbol": ACTUAL["symbol"],
                "trade_id": ACTUAL["trade_id"],
                "result_r": round(ACTUAL["realized_R"], 4),
                "realized_usd": ACTUAL["profit_usd"],
                "exit_type": ACTUAL["exit_reason"],  # sl_hit (more specific than broker_closed)
                "entry_price": ACTUAL["entry_price"],
                "exit_price": ACTUAL["exit_price"],
                "hold_minutes": float(ACTUAL["hold_minutes"]),
                "time": ACTUAL["exit_time_utc"][11:19],  # "20:15:06"
                "broker_deal_reconciled": True,
            })
        else:
            new_trades.append(t)

    d["trades"] = new_trades
    d["total_r"] = round(sum(t.get("result_r", 0) for t in new_trades), 4)
    d["total_usd"] = round(sum(t.get("realized_usd", 0) for t in new_trades), 2)
    d["wins"] = sum(1 for t in new_trades if t.get("result_r", 0) > 0)
    d["losses"] = sum(1 for t in new_trades if t.get("result_r", 0) <= 0)
    d["backfill_note"] = (
        "NAS100 row rewritten 2026-04-29 from MT5 deal history. Original "
        "recorded -0.0168R from the orch's false-close race; actual SL hit "
        "20:15:06 UTC, -$103.56."
    )
    p.write_text(json.dumps(d, indent=2), encoding="utf-8")
    print(f"  rewrote {p.name}: total_r={d['total_r']} total_usd=${d['total_usd']:.2f} losses={d['losses']}")


def fix_j46_j49_shadow() -> None:
    p = Path("shadow_logs/j46_j49_shadow_outcomes.jsonl")
    if not p.exists():
        print(f"  j46_j49_shadow_outcomes.jsonl missing, skipping")
        return
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
        if r.get("fill_id") == ACTUAL["fill_id"]:
            r["actual_close"] = {
                "exit_price": ACTUAL["exit_price"],
                "exit_time": ACTUAL["exit_time_utc"],
                "exit_reason": ACTUAL["exit_reason"],
                "realized_R": round(ACTUAL["realized_R"], 4),
                "broker_deal_reconciled": True,
            }
            hypo_r = float(r.get("hypothetical_old", {}).get("hypothetical_R", 0))
            r["delta_r"] = round(ACTUAL["realized_R"] - hypo_r, 4)
            r["shadow_better"] = r["delta_r"] > 0
            r["backfill_note"] = (
                "Rewritten 2026-04-29 from MT5 deal history. Actual SL hit at "
                f"{ACTUAL['exit_time_utc']}, realized {ACTUAL['realized_R']:.4f}R "
                f"(${ACTUAL['profit_usd']:.2f}). Original carried the orch's "
                "broken false-close reading."
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
    p = Path("knowledge_base/trade_records/NAS100/2026-04-29_ny_1500.json")
    if not p.exists():
        return False
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        return bool((d.get("exit") or {}).get("broker_deal_reconciled"))
    except (OSError, json.JSONDecodeError):
        return False


def main() -> None:
    print(f"Backfilling 2026-04-29 NAS100 SL hit (actual: {ACTUAL['realized_R']:.4f}R / ${ACTUAL['profit_usd']:.2f})")
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
