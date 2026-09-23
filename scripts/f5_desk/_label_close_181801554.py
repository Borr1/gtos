#!/usr/bin/env python3
"""Chair-sit LABEL_CLOSE DASHUSD 181801554 W7 orig_stop (sibling of F5 181801555)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(r"host-local\redacted_host\repo")
PY = r"C:\Users\MSI\Documents\ai-trading-agent\.venv-gtos\Scripts\python.exe"
WRITER = REPO / "scripts" / "f5_desk" / "write_inbox_verdict.py"

TICKET = 181801554
SYMBOL = "DASHUSD"
SIDE = "LONG"
COMMENT = "crypto"
SLEEVE = "crypto"
EXIT_CLASS = "orig_stop"
ENTRY = 69.02
ORIG_SL = 61.55
ORIG_TP = 98.88
EXIT = 61.57
VOLUME = 0.06
DEAL_IN = 170361063
DEAL_OUT = 170964920
ORDER_OUT = 182475745
BROKER_COMMENT = "[sl 61.55]"
DEAL_REASON = 4
PROFIT = -447.00
COMM_RT = -2.55
SWAP = -3.21
BROKER_NET = -452.76
R_UNIT150 = -3.02
R_POINTS = 7.47
SLIP = 0.02
FILL_UTC = "2026-09-05T05:00:43Z"
CLOSE_UTC = "2026-09-08T18:55:21Z"
FILL_ICT = "2026-09-05 12:00 ICT"
CLOSE_ICT = "2026-09-09 01:55 ICT"
HELD = "3d13h54m38s"
REENTRY_ICT = "2026-09-09 02:10 ICT"
LOGIN = 0
BAL = 90775.17
EQ = 90678.81
FLOATING = round(EQ - BAL, 2)
OPEN_LEFT = [
    "GER40 180734064 LONG",
    "US500 182448957 LONG",
    "US30 182478404 LONG",
]
MAGIC = 20260401

now_utc = datetime.now(timezone.utc)
sit_ict = (now_utc + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M ICT")
ts_utc = now_utc.isoformat().replace("+00:00", "Z")

memory_line = (
    f"LABEL_CLOSE {SYMBOL} {TICKET} {SIDE} {COMMENT} W7 magic={MAGIC} exit_class={EXIT_CLASS} "
    f"exit={EXIT} {BROKER_COMMENT} vs orig_sl={ORIG_SL} orig_tp={ORIG_TP} "
    f"entry={ENTRY} vol={VOLUME} deal_in={DEAL_IN} deal_out={DEAL_OUT} order_out={ORDER_OUT} "
    f"reason={DEAL_REASON} SL profit={PROFIT:.2f} commission_roundtrip={COMM_RT:.2f} "
    f"swaps={SWAP:.2f} broker_net={BROKER_NET:.2f} ~{R_UNIT150:.2f}R unit150 breach=false; "
    f"filled {FILL_UTC} closed {CLOSE_UTC} held {HELD}; orig never moved; "
    f"hourly sit backstop (F5 sibling 181801555 labeled 01:59 ICT deferred W7 to sit); "
    f"labelled off history_deals_get(position={TICKET}); "
    f"DASH W7 flat, isolated re-entry after {REENTRY_ICT}; "
    f"leave GER40 180734064 + US500 182448957 + US30 182478404; "
    f"spent 180717112 stays spent; no remint"
)

env = os.environ.copy()
env["PYTHONPATH"] = str(REPO)
cmd = [PY, str(WRITER), "--repo", str(REPO), "--memory", memory_line]
r = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True, env=env)
print("write_inbox_verdict rc", r.returncode)
print(r.stdout)
print(r.stderr, file=sys.stderr)
if r.returncode != 0:
    sys.exit(r.returncode)
verdict_meta = json.loads(r.stdout.strip().splitlines()[-1])

card = (
    f"{sit_ict} | {LOGIN} bal {BAL:.2f} eq {EQ:.2f}\n"
    f"CLOSE {SYMBOL} {SIDE} {TICKET} W7 exit_class={EXIT_CLASS} exit={EXIT} {BROKER_COMMENT} "
    f"~{R_UNIT150:.2f}R(unit150) broker_net={BROKER_NET:.2f} held {HELD} | orig never moved | "
    f"flat; re-entry after {REENTRY_ICT} | leave GER40 180734064 + US500 182448957 + "
    f"US30 182478404 | spent 180717112 stays spent | no remint"
)

close_speak = {
    "ts_ict": sit_ict,
    "ts_utc": ts_utc,
    "source": "f5-chair-sit",
    "kind": "close",
    "ticket": TICKET,
    "symbol": SYMBOL,
    "side": SIDE,
    "comment": COMMENT,
    "sleeve": SLEEVE,
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
    "label_source": f"history_deals_get(position={TICKET})",
    "symbol_flat_now": True,
    "isolated_reentry_after_ict": REENTRY_ICT,
    "open_left": OPEN_LEFT,
    "pending": 0,
    "account": {"balance": BAL, "equity": EQ, "floating": FLOATING, "login": LOGIN},
    "spent_gold_180717112": "leave spent",
    "magic": MAGIC,
    "verdict": verdict_meta,
    "reason": memory_line,
    "card": card,
    "session": "2026-09-09",
    "ledger": "label_close",
    "chair_wake_utc": ts_utc,
    "dedup": "no prior close+181801554 spoken; F5 sibling 181801555 labeled 01:59 ICT deferred W7",
    "f5_new_orders": "paused ULTIMATE_BOOK_KILL (owner); opens leave orig",
    "broker_via": "user-mt5-ftmo MCP history + chair_desk sit --mt5",
    "context_change": "W7 DASH 181801554 orig_stop sit-backstop label; F5 sibling already labeled; leave GER40/US500/US30",
    "sibling_same_second": {
        "ticket": 181801555,
        "magic": 0,
        "comment": "F5:crypto",
        "exit_class": "orig_stop",
        "labeled_ict": "2026-09-09 01:59 ICT",
    },
}

out = Path(r"host-local\redacted_host\repo\judgment\live")
# also print JSON for box capture
print("CARD_BEGIN")
print(card)
print("CARD_END")
print("SPEAK_JSON_BEGIN")
print(json.dumps(close_speak, indent=2))
print("SPEAK_JSON_END")
