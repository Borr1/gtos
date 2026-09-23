#!/usr/bin/env python3
"""Book-event LABEL_CLOSE XAUUSD 182201750 orig_stop."""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(r"host-local\redacted_host\repo")
PY = r"C:\Users\MSI\Documents\ai-trading-agent\.venv-gtos\Scripts\python.exe"
WRITER = REPO / "scripts" / "f5_desk" / "write_inbox_verdict.py"
LIVE_BOX = Path("/workspace/gtos/live")  # only used if run on box; VPS paths below

TICKET = 182201750
SYMBOL = "XAUUSD"
SIDE = "LONG"
COMMENT = "dsp_accepted_20low_then_second_flush"
EXIT_CLASS = "orig_stop"
ENTRY = 4400.23
ORIG_SL = 4393.89
ORIG_TP = 4450.4
EXIT = 4393.83
VOLUME = 0.23
DEAL_IN = 170712671
DEAL_OUT = 170734217
ORDER_OUT = 182225132
BROKER_COMMENT = "[sl 4393.89]"
DEAL_REASON = 4
PROFIT = -147.2
COMM_RT = -1.42
SWAP = 0.0
BROKER_NET = -148.62
R_UNIT150 = -0.99
R_POINTS = 6.34
SLIP = 0.06
FILL_UTC = "2026-09-08T06:31:03Z"
CLOSE_UTC = "2026-09-08T07:39:24Z"
FILL_ICT = "2026-09-08 13:31 ICT"
CLOSE_ICT = "2026-09-08 14:39 ICT"
HELD = "1h8m21s"
REENTRY_ICT = "2026-09-08 14:54 ICT"
BODY_DIGEST = "sha256:e462df4cdcbf54021a4f894c3cec84b7cafd0c52a8f2fe4dc57faedeeed052f3"
PAYLOAD_TS = "2026-09-08T07:39:27Z"
LOGIN = 0
BAL = 92275.99
EQ = 91786.27
FLOATING = round(EQ - BAL, 2)
OPEN_LEFT = [
    "GER40 180734064 LONG",
    "DASHUSD 181801554 LONG",
    "DASHUSD 181801555 LONG",
]

now_utc = datetime.now(timezone.utc)
sit_ict = (now_utc + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M ICT")
ts_utc = now_utc.isoformat().replace("+00:00", "Z")

memory_line = (
    f"LABEL_CLOSE {SYMBOL} {TICKET} {SIDE} {COMMENT} exit_class={EXIT_CLASS} "
    f"exit={EXIT} {BROKER_COMMENT} vs orig_sl={ORIG_SL} orig_tp={ORIG_TP} "
    f"entry={ENTRY} vol={VOLUME} deal_in={DEAL_IN} deal_out={DEAL_OUT} order_out={ORDER_OUT} "
    f"reason={DEAL_REASON} SL profit={PROFIT:.2f} commission_roundtrip={COMM_RT:.2f} "
    f"broker_net={BROKER_NET:.2f} ~{R_UNIT150:.2f}R unit150 breach=false; "
    f"filled {FILL_UTC} closed {CLOSE_UTC} held {HELD}; orig never moved; "
    f"webhook price echoed entry; labelled off history_deals_get(position={TICKET})+trade_records; "
    f"XAU flat, isolated re-entry after {REENTRY_ICT}; "
    f"leave GER40 180734064 + DASH 181801554/181801555; "
    f"US30 182201752 also flat (separate object — not this webhook); "
    f"spent 180717112 stays spent; no remint"
)

cmd = [PY, str(WRITER), "--repo", str(REPO), "--memory", memory_line]
r = subprocess.run(cmd, capture_output=True, text=True)
print("write_inbox_verdict rc", r.returncode)
print(r.stdout)
print(r.stderr, file=sys.stderr)
if r.returncode != 0:
    sys.exit(r.returncode)
verdict_meta = json.loads(r.stdout.strip().splitlines()[-1])

card = (
    f"{sit_ict} | {LOGIN} bal {BAL:.2f} eq {EQ:.2f}\n"
    f"CLOSE {SYMBOL} {SIDE} {TICKET} exit_class={EXIT_CLASS} exit={EXIT} {BROKER_COMMENT} "
    f"~{R_UNIT150:.2f}R(unit150) broker_net={BROKER_NET:.2f} held {HELD} | orig never moved | "
    f"flat; re-entry after {REENTRY_ICT} | leave GER40 180734064 + DASH 181801554/181801555 | "
    f"US30 182201752 also flat (not this event) | spent 180717112 stays spent | no remint"
)

close_speak = {
    "ts_ict": sit_ict,
    "ts_utc": ts_utc,
    "source": "f5-book-event",
    "kind": "close",
    "ticket": TICKET,
    "symbol": SYMBOL,
    "side": SIDE,
    "comment": COMMENT,
    "sleeve": COMMENT,
    "login": LOGIN,
    "action": "LABEL_CLOSE",
    "spoken": True,
    "word": "LABEL",
    "place": False,
    "remint": False,
    "hold": False,
    "flatten": False,
    "exit_class": EXIT_CLASS,
    "breach": False,
    "entry": ENTRY,
    "orig_sl": ORIG_SL,
    "orig_tp": ORIG_TP,
    "exit": EXIT,
    "volume": VOLUME,
    "deal_in": DEAL_IN,
    "deal_out": DEAL_OUT,
    "order_out": ORDER_OUT,
    "broker_comment": BROKER_COMMENT,
    "deal_reason": DEAL_REASON,
    "profit": PROFIT,
    "commission_roundtrip": COMM_RT,
    "swap": SWAP,
    "realised_r_unit150": R_UNIT150,
    "r_points": R_POINTS,
    "slip_pts": SLIP,
    "broker_net_pnl": BROKER_NET,
    "fill_utc": FILL_UTC,
    "close_utc": CLOSE_UTC,
    "fill_ict": FILL_ICT,
    "close_ict": CLOSE_ICT,
    "held": HELD,
    "payload_ts_utc": PAYLOAD_TS,
    "body_digest": BODY_DIGEST,
    "webhook_price_echoed_entry": ENTRY,
    "orig_source": f"chair_orig_sl.json {ORIG_SL} / tp {ORIG_TP} == broker {BROKER_COMMENT}; never moved",
    "label_source": f"history_deals_get(position={TICKET}) + trade_records/{TICKET}.json",
    "symbol_flat_now": True,
    "isolated_reentry_after_ict": REENTRY_ICT,
    "open_left": OPEN_LEFT,
    "pending": 0,
    "note_book_state": "US30 182201752 also flat now; sit THAT object only — not labeled here",
    "account": {
        "balance": BAL,
        "equity": EQ,
        "floating": FLOATING,
        "login": LOGIN,
    },
    "spent_gold_180717112": "leave spent",
    "magic": 0,
    "verdict": {
        "wrote": verdict_meta.get("wrote"),
        "slate_id": verdict_meta.get("slate_id"),
        "fingerprint": verdict_meta.get("fingerprint"),
        "n_verdicts": verdict_meta.get("n_verdicts"),
        "n_memory": 1,
        "written_at_utc": verdict_meta.get("written_at_utc"),
        "schema": verdict_meta.get("schema"),
    },
    "reason": memory_line,
    "card": card,
    "session": "2026-09-08",
    "ledger": "label_close",
    "webhook_post_utc": PAYLOAD_TS,
    "chair_wake_utc": ts_utc,
    "dedup": "no prior close+182201750 spoken",
    "f5_new_orders": "paused ULTIMATE_BOOK_KILL (owner); opens leave orig",
}

# Prefer box live if present (this script may run on box after VPS write, or on VPS)
out_paths = []
for live in (
    Path(r"host-local\redacted_host\repo\judgment\live"),
    Path("/workspace/gtos/live"),
):
    try:
        live.mkdir(parents=True, exist_ok=True)
        (live / f"_close_speak_{TICKET}.json").write_text(
            json.dumps(close_speak, indent=2) + "\n", encoding="utf-8"
        )
        (live / f"_close_card_{TICKET}.txt").write_text(card + "\n", encoding="utf-8")
        (live / "book_event_last.json").write_text(
            json.dumps({
                "ts_ict": sit_ict,
                "ts_utc": ts_utc,
                "kind": "close",
                "ticket": TICKET,
                "symbol": SYMBOL,
                "action": "LABEL_CLOSE",
                "spoken": True,
                "exit_class": EXIT_CLASS,
                "body_digest": BODY_DIGEST,
                "path": str(live / f"_close_speak_{TICKET}.json"),
            }, indent=2) + "\n",
            encoding="utf-8",
        )
        for name in ("book_event_spoken.jsonl", "book_event_ledger.jsonl"):
            with (live / name).open("a", encoding="utf-8") as f:
                f.write(json.dumps(close_speak, ensure_ascii=False) + "\n")
        out_paths.append(str(live))
    except Exception as e:
        print("skip live", live, e)

print(json.dumps({"ok": True, "card": card, "verdict": verdict_meta, "lives": out_paths}, indent=2))
