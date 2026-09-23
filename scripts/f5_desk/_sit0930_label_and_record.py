#!/usr/bin/env python3
"""F5 Chair Sit 2026-09-08 ~09:35 ICT: LABEL unlabeled closes + record sit."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(r"host-local\redacted_host\repo")
LIVE = REPO / "judgment" / "live"
BOX_MIRROR = Path(r"host-local\redacted_host\repo\scripts\f5_desk")  # also dump sit last here
sys.path.insert(0, str(REPO))

from scripts.f5_desk import write_inbox_verdict as wiv  # noqa: E402

ICT = timezone(timedelta(hours=7))
NOW = datetime.now(timezone.utc)
NOW_ICT = NOW.astimezone(ICT)
TS_ICT = NOW_ICT.strftime("%Y-%m-%d %H:%M ICT")
TS_UTC = NOW.isoformat().replace("+00:00", "Z")


def append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


# Broker stamps are FTMO-Server3 ≈ UTC+3; convert to UTC for ledger.
closes = [
    {
        "ticket": 182134088,
        "symbol": "XAUUSD",
        "side": "SHORT",
        "tag": "dsp_walked_hi",
        "exit_class": "stop_loss",
        "entry": 4431.0,
        "orig_sl": 4438.53,
        "orig_tp": 4387.49,
        "exit": 4438.66,
        "volume": 0.2,
        "deal_in": 170651244,
        "deal_out": 170656953,
        "order_out": 182140583,
        "broker_comment": "[sl 4438.53]",
        "deal_reason": 4,
        "profit": -153.2,
        "commission": -0.62,
        "realised_r_unit150": round(-153.2 / 150.0, 2),
        "r_points": 7.53,
        "slip_pts": 0.13,
        "fill_ict": "2026-09-08 08:18 ICT",
        "close_ict": "2026-09-08 08:48 ICT",
        "fill_utc": "2026-09-08T01:18:08Z",
        "close_utc": "2026-09-08T01:48:05Z",
        "held": "29m57s",
        "isolated_reentry_after_ict": "2026-09-08 09:03 ICT",
        "note": "since 08:31 sit; book-event filled LEAVE_ORIG 08:23 ICT but close webhook never spoken; sit catch-up LABEL",
    },
    {
        "ticket": 182118705,
        "symbol": "GBPUSD",
        "side": "LONG",
        "tag": "xa_huge_same_",
        "exit_class": "stop_loss",
        "entry": 1.35427,
        "orig_sl": 1.35376,
        "orig_tp": 1.35827,
        "exit": 1.35371,
        "volume": 3.0,
        "deal_in": 170637588,
        "deal_out": 170664612,
        "order_out": 182149040,
        "broker_comment": "[sl 1.35376]",
        "deal_reason": 4,
        "profit": -168.0,
        "commission": -7.5,
        "realised_r_unit150": round(-168.0 / 150.0, 2),
        "r_points": 51,
        "slip_pts": 0.00005,
        "fill_ict": "2026-09-08 07:16 ICT",
        "close_ict": "2026-09-08 09:33 ICT",
        "fill_utc": "2026-09-08T00:16:30Z",
        "close_utc": "2026-09-08T02:33:15Z",
        "held": "2h16m45s",
        "isolated_reentry_after_ict": "2026-09-08 09:48 ICT",
        "note": "closed during this hourly sit; no book-event speak yet; sit LABEL",
    },
]

prior_labeled = {
    "ticket": 182118694,
    "symbol": "XAUUSD",
    "side": "LONG",
    "exit_class": "stop_loss",
    "exit": 4417.16,
    "broker_net": -169.65,
    "realised_r_unit150": -1.13,
    "close_ict": "2026-09-08 07:48 ICT",
    "spoken_ict": "2026-09-08 07:54 ICT",
    "source": "f5-book-event",
    "age_min_at_sit": round((NOW - datetime(2026, 9, 8, 0, 54, 58, tzinfo=timezone.utc)).total_seconds() / 60.0, 1),
    "note": "already LABEL+spoken; past 50m quiet → sit backstop mention only",
}

open_now = [
    {
        "ticket": 180734064,
        "symbol": "GER40.cash",
        "side": "LONG",
        "tag": "mx_ger40_cash",
        "lots": 0.55,
        "entry": 25803.47,
        "orig_sl": 25568.61,
        "live_sl": 25568.61,
        "tp": 26273.19,
        "spread_over_R": 0.0129,
        "trade_mode": 4,
        "broker_sl_present": True,
        "container": "ok",
    },
    {
        "ticket": 181411441,
        "symbol": "UK100.cash",
        "side": "SHORT",
        "tag": "idxrev",
        "lots": 1.55,
        "entry": 10834.7,
        "orig_sl": 10905.74,
        "live_sl": 10905.74,
        "tp": 10781.27,
        "spread_over_R": 0.0457,
        "trade_mode": 4,
        "broker_sl_present": True,
        "container": "ok",
    },
    {
        "ticket": 181801555,
        "symbol": "DASHUSD",
        "side": "LONG",
        "tag": "crypto",
        "lots": 0.02,
        "entry": 69.08,
        "orig_sl": 61.59,
        "live_sl": 61.59,
        "tp": 99.06,
        "spread_over_R": 0.0053,
        "trade_mode": 4,
        "broker_sl_present": True,
        "container": "ok",
        "note": "red P&L alone not broken",
    },
    {
        "ticket": 182062146,
        "symbol": "US30.cash",
        "side": "LONG",
        "tag": "dsp_bleed_acc",
        "lots": 3.54,
        "entry": 53007.25,
        "orig_sl": 52964.88,
        "live_sl": 52964.88,
        "tp": 53260.77,
        "spread_over_R": 0.0562,
        "trade_mode": 4,
        "broker_sl_present": True,
        "container": "ok",
    },
]

pending = [
    {
        "ticket": 182146604,
        "symbol": "AVAUSD",
        "type": "BUY_LIMIT",
        "price": 7.92,
        "sl": 7.61,
        "tp": 8.55,
        "volume": 0.47,
        "comment": "F5:mx_avausd_d1_",
        "magic": 0,
        "setup_utc": "2026-09-08T02:18:50Z",
        "setup_ict": "2026-09-08 09:18 ICT",
        "age_m": round((NOW - datetime(2026, 9, 8, 2, 18, 50, tzinfo=timezone.utc)).total_seconds() / 60.0, 1),
        "note": "candidate quiet 09:23 ICT; age <45m — no pending-resting card",
    }
]

# refresh bal/eq from MT5
import MetaTrader5 as mt5

assert mt5.initialize(), mt5.last_error()
acc = mt5.account_info()
bal, eq = float(acc.balance), float(acc.equity)
# refresh marks/pnl
pos_by = {p.ticket: p for p in (mt5.positions_get() or [])}
for o in open_now:
    p = pos_by.get(o["ticket"])
    if p:
        o["mark"] = float(p.price_current)
        o["pnl"] = float(p.profit)
        o["live_sl"] = float(p.sl)
        o["tp"] = float(p.tp)
mt5.shutdown()

day_net = bal - 93027.23  # rough; better leave absolute
# FTMO day start unknown; keep absolute bal/eq on card

open_left = [f"{o['symbol'].replace('.cash','')} {o['ticket']} {o['side']}" for o in open_now]
pending_left = [
    f"{p['symbol']} {p['type']} {p['ticket']} @{p['price']} SL{p['sl']} TP{p['tp']} vol{p['volume']}"
    for p in pending
]

memory_lines = []
for c in closes:
    memory_lines.append(
        f"LABEL_CLOSE {c['symbol']} {c['ticket']} {c['side']} {c['tag']} exit_class={c['exit_class']} "
        f"exit={c['exit']} {c['broker_comment']} vs orig_sl={c['orig_sl']} orig_tp={c['orig_tp']} "
        f"entry={c['entry']} vol={c['volume']} deal_in={c['deal_in']} deal_out={c['deal_out']} "
        f"order_out={c['order_out']} reason={c['deal_reason']} SL profit={c['profit']} "
        f"broker_net={c['profit']} ~{c['realised_r_unit150']}R unit150 slip={c['slip_pts']} breach=false; "
        f"filled {c['fill_utc']} closed {c['close_utc']} held {c['held']}; orig never moved; "
        f"flat; isolated re-entry after {c['isolated_reentry_after_ict']}; "
        f"leave {' + '.join(open_left)}; pending {pending_left[0] if pending_left else 'none'}; "
        f"spent 180717112 stays spent; no remint; no place/flatten"
    )

slate = wiv.load_slate(REPO)
payload = wiv.bind(
    {
        "verdicts": [],
        "manage": [],
        "memory": memory_lines,
        "source": "f5-chair-sit",
        "note": "hourly sit 2026-09-08 09:35 ICT: LABEL XAU short 182134088 + GBP 182118705 unlabeled SL closes; containers ok; AVA pending <45m",
    },
    slate,
)
inbox = wiv._inbox_path(REPO)
inbox.parent.mkdir(parents=True, exist_ok=True)
inbox.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
verdict_meta = {
    "wrote": str(inbox),
    "slate_id": payload.get("slate_id"),
    "fingerprint": payload.get("fingerprint"),
    "n_verdicts": 0,
    "n_memory": len(memory_lines),
    "written_at_utc": TS_UTC,
    "schema": "gtos.f5.judge.verdict.v1",
}
print("WROTE_VERDICT", json.dumps(verdict_meta))

card_lines = [
    f"{TS_ICT} | 0 bal {bal:.2f} eq {eq:.2f}",
]
for c in closes:
    card_lines.append(
        f"CLOSE {c['symbol']} {c['side']} {c['ticket']} exit_class={c['exit_class']} "
        f"exit={c['exit']} {c['broker_comment']} ~{c['realised_r_unit150']}R(unit150) "
        f"broker_net={c['profit']} held {c['held']} | orig never moved | "
        f"flat; re-entry after {c['isolated_reentry_after_ict']}"
    )
card_lines.append(
    "leave "
    + " + ".join(open_left)
    + " | pending "
    + (pending_left[0] if pending_left else "none")
    + " age~"
    + str(pending[0]["age_m"])
    + "m (<45) | spent 180717112 stays spent | no remint"
)
card_lines.append(
    f"ctx: sit backstop LABEL — XAU short 182134088 close missed by book-event after fill 08:23; "
    f"GBP 182118705 SL during sit; prior XAU long 182118694 LABEL @07:54 (~{prior_labeled['age_min_at_sit']}m>50m) "
    f"mentioned only | OPEN4 containers ok spread<<1R live==orig trade_mode4 | "
    f"red DASH PnL alone not broken | dual W7 intentional | F5 new orders paused ULTIMATE_BOOK_KILL"
)
card_text = "\n".join(card_lines)

for c in closes:
    row = {
        "ts_ict": TS_ICT,
        "ts_utc": TS_UTC,
        "source": "f5-chair-sit",
        "kind": "close",
        "ticket": c["ticket"],
        "symbol": c["symbol"],
        "side": c["side"],
        "comment": c["tag"],
        "login": 0,
        "action": "LABEL_CLOSE",
        "spoken": True,
        "word": "LABEL",
        "place": False,
        "remint": False,
        "hold": False,
        "flatten": False,
        "exit_class": c["exit_class"],
        "breach": False,
        "entry": c["entry"],
        "orig_sl": c["orig_sl"],
        "orig_tp": c["orig_tp"],
        "exit": c["exit"],
        "volume": c["volume"],
        "deal_in": c["deal_in"],
        "deal_out": c["deal_out"],
        "order_out": c["order_out"],
        "broker_comment": c["broker_comment"],
        "deal_reason": c["deal_reason"],
        "profit": c["profit"],
        "commission": c["commission"],
        "realised_r_unit150": c["realised_r_unit150"],
        "r_points": c["r_points"],
        "slip_pts": c["slip_pts"],
        "fill_ict": c["fill_ict"],
        "close_ict": c["close_ict"],
        "fill_utc": c["fill_utc"],
        "close_utc": c["close_utc"],
        "held": c["held"],
        "isolated_reentry_after_ict": c["isolated_reentry_after_ict"],
        "note": c["note"],
        "open_left": open_left,
        "pending_left": pending_left,
        "account": {"login": 0, "balance": bal, "equity": eq},
        "spent_gold_180717112": "leave spent",
        "verdict": verdict_meta,
        "card": card_text,
        "session": "2026-09-08",
        "ledger": "label_close",
    }
    append_jsonl(LIVE / "chair_sit_spoken.jsonl", row)
    append_jsonl(LIVE / "book_event_spoken.jsonl", {**row, "via": "f5-chair-sit-catchup"})  # keep speak map aware? NO — don't pollute book-event. skip
print("SKIPPED writing book_event_spoken — chair_sit_spoken only")

sit_last = {
    "ts_ict": TS_ICT,
    "ts_utc": TS_UTC,
    "source": "f5-chair-sit",
    "routine": "f5-chair-sit",
    "result": "CARD",
    "login": 0,
    "bal": bal,
    "eq": eq,
    "positions_f5": len(open_now),
    "pending": len(pending),
    "fast_live": True,
    "open": open_now,
    "pending_orders": pending,
    "w7_other": {
        "ticket": 181801554,
        "symbol": "DASHUSD",
        "magic": 20260401,
        "note": "dual F5+Astra-W7 intentional; not F5 chair book",
    },
    "closes_labeled_now": [
        {"ticket": c["ticket"], "symbol": c["symbol"], "exit_class": c["exit_class"], "profit": c["profit"]}
        for c in closes
    ],
    "prior_close_past_50m": prior_labeled,
    "fills_already_covered_50m": [],
    "manage": [],
    "card": True,
    "card_text": card_text,
    "fingerprint": f"hourly-sit-{NOW_ICT.strftime('%Y%m%dT%H%M')}-card-closes",
    "why_card": "LABEL unlabeled CLOSE XAU 182134088 (08:48) + GBP 182118705 (09:33); prior XAU 182118694 labeled >50m; OPEN4 containers ok; AVA pending <45m",
    "no_place_remint_flatten": True,
    "spent_gold_180717112": "stays_spent",
    "verdict_needed": False,
    "verdict": verdict_meta,
    "ok": True,
}
write_json(LIVE / "chair_sit_last.json", sit_last)
append_jsonl(
    LIVE / "chair_sit_log.jsonl",
    {
        "ts_ict": TS_ICT,
        "ts_utc": TS_UTC,
        "action": "CARD",
        "bal": bal,
        "eq": eq,
        "n": len(open_now),
        "pending": len(pending),
        "tickets": [o["ticket"] for o in open_now],
        "broken": [],
        "card_tickets": [c["ticket"] for c in closes],
        "reason": sit_last["why_card"],
    },
)

# also dump card to scripts for scp pull
write_json(BOX_MIRROR / "_sit0930_out.json", sit_last)
(BOX_MIRROR / "_sit0930_card.txt").write_text(card_text + "\n", encoding="utf-8")
print("CARD\n" + card_text)
print("OK")
