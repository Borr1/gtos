#!/usr/bin/env python3
"""F5 Chair Sit 2026-09-18 ~10:26 ICT: LABEL XAU 293611741 orig_stop + GBPJPY 293540988 orig_tp; flat."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(r"host-local\redacted_host\repo")
LIVE = REPO / "judgment" / "live"
STATE = REPO / "pipeline_state" / "ultimate_book" / "operator" / "judgment" / "state"
sys.path.insert(0, str(REPO))

from scripts.f5_desk import write_inbox_verdict as wiv  # noqa: E402

ICT = timezone(timedelta(hours=7))
NOW = datetime.now(timezone.utc)
NOW_ICT = NOW.astimezone(ICT)
TS_ICT = NOW_ICT.strftime("%Y-%m-%d %H:%M ICT")
TS_UTC = NOW.isoformat().replace("+00:00", "Z")

closes = [
    {
        "ticket": 293611741,
        "symbol": "XAUUSD",
        "side": "LONG",
        "tag": "dsp_shakeout_",
        "exit_class": "orig_stop",
        "entry": 4347.32,
        "orig_sl": 4343.11,
        "orig_tp": 4380.73,
        "exit": 4342.95,
        "volume": 0.35,
        "deal_in": 274748646,
        "deal_out": 274764200,
        "order_out": 293628869,
        "broker_comment": "[sl 4343.11]",
        "profit": -152.95,
        "swap": 0.0,
        "commission_in": -1.07,
        "commission_out": -1.06,
        "broker_net": -155.08,
        "realised_r_unit150": -1.03,
        "fill_ict": "2026-09-18 08:45 ICT",
        "close_ict": "2026-09-18 10:16 ICT",
        "held": "1h31m",
        "isolated_reentry_after_ict": "2026-09-18 10:31 ICT",
    },
    {
        "ticket": 293540988,
        "symbol": "GBPJPY",
        "side": "LONG",
        "tag": "sub_mid_dn_re",
        "exit_class": "orig_tp",
        "entry": 208.333,
        "orig_sl": 207.826,
        "orig_tp": 209.855,
        "exit": 209.862,
        "volume": 0.46,
        "deal_in": 274692074,
        "deal_out": 274767623,
        "order_out": 293632030,
        "broker_comment": "[tp 209.855]",
        "profit": 444.75,
        "swap": 1.78,
        "commission_in": -1.15,
        "commission_out": -1.15,
        "broker_net": 444.23,
        "realised_r_unit150": 2.96,
        "fill_ict": "2026-09-18 00:00 ICT",
        "close_ict": "2026-09-18 10:23 ICT",
        "held": "10h23m",
        "isolated_reentry_after_ict": "2026-09-18 10:38 ICT",
    },
]

bal = 94654.37
eq = 94654.37
day_net = -52.62
to_pass = 15345.63

memory_lines = []
for c in closes:
    memory_lines.append(
        (
            f"LABEL_CLOSE {c['symbol']} {c['ticket']} {c['side']} {c['tag']} "
            f"exit_class={c['exit_class']} exit={c['exit']} {c['broker_comment']} "
            f"profit={c['profit']} swap={c['swap']} broker_net={c['broker_net']} "
            f"~{c['realised_r_unit150']}R(unit150) held {c['held']}; "
            f"filled {c['fill_ict']} closed {c['close_ict']}; "
            f"orig_sl={c['orig_sl']} orig_tp={c['orig_tp']}; "
            f"isolated re-entry after {c['isolated_reentry_after_ict']}; no remint; "
            f"sit backstop (book-event close emit missing)"
        )
    )

slate = wiv.load_slate(REPO)
payload = wiv.bind(
    {
        "verdicts": [],
        "manage": [],
        "memory": memory_lines,
        "source": "f5-chair-sit",
        "note": (
            "hourly sit 2026-09-18 10:26 ICT: LABEL XAU 293611741 orig_stop + "
            "GBPJPY 293540988 orig_tp; book flat; book-event close keys absent"
        ),
    },
    slate,
)
inbox = wiv._inbox_path(REPO)
inbox.parent.mkdir(parents=True, exist_ok=True)
inbox.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(
    "WROTE_VERDICT",
    inbox,
    "slate",
    payload.get("slate_id"),
    "fp",
    payload.get("fingerprint"),
)

card_lines = [
    f"{TS_ICT} | 0 bal {bal} eq {eq}",
    (
        f"CLOSE XAUUSD LONG 293611741 dsp_shakeout_ | exit_class=orig_stop exit=4342.95 "
        f"[sl 4343.11] vs orig SL 4343.11 TP 4380.73 (open 4347.32 vol 0.35) | "
        f"~-1.03R unit150 broker_net=-155.08 held 1h31m | deals 274748646->274764200 | "
        f"sit backstop LABEL (book-event close emit missing) | "
        f"isolated re-entry after 2026-09-18 10:31 ICT | no remint"
    ),
    (
        f"CLOSE GBPJPY LONG 293540988 sub_mid_dn_re | exit_class=orig_tp exit=209.862 "
        f"[tp 209.855] vs orig SL 207.826 TP 209.855 (open 208.333 vol 0.46) | "
        f"~+2.96R unit150 broker_net=+444.23 held 10h23m | deals 274692074->274767623 | "
        f"sit backstop LABEL (book-event close emit missing) | "
        f"isolated re-entry after 2026-09-18 10:38 ICT | no remint"
    ),
    (
        f"flat | pending 0 | day_net {day_net} to_pass {to_pass} | "
        f"slate {payload.get('slate_id')} / fp {payload.get('fingerprint')} | "
        f"PATH both closed leave-orig; no place/remint/flatten"
    ),
]
card_text = "\n".join(card_lines) + "\n"

(LIVE / "chair_last_close_card.txt").write_text(card_text, encoding="utf-8")
(LIVE / "chair_last_card.txt").write_text(card_text, encoding="utf-8")

sit = {
    "at_utc": TS_UTC,
    "at_ict": TS_ICT,
    "action": "CARD",
    "fingerprint": "hourly-close-293611741-293540988-20260918T0326",
    "open_tickets": [],
    "bal": bal,
    "eq": eq,
    "day_net": day_net,
    "to_pass": to_pass,
    "labeled_closes": [293611741, 293540988],
    "filled": [],
    "reason": (
        "CLOSE XAU 293611741 orig_stop ~-1.03R; CLOSE GBPJPY 293540988 orig_tp ~+2.96R; "
        "flat; book-event close emit missing"
    ),
}
(LIVE / "chair_last_sit.json").write_text(
    json.dumps(sit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
)
STATE.mkdir(parents=True, exist_ok=True)
(STATE / "chair_last_sit.json").write_text(
    json.dumps({"at_utc": TS_UTC, "unix": NOW.timestamp()}, indent=2) + "\n",
    encoding="utf-8",
)

# drop closed tickets from orig latch (keep file honest)
orig_path = LIVE / "chair_orig_sl.json"
orig = json.loads(orig_path.read_text(encoding="utf-8"))
tickets = orig.get("tickets") if isinstance(orig.get("tickets"), dict) else {}
dropped = []
for t in ("293611741", "293540988"):
    if t in tickets:
        tickets.pop(t)
        dropped.append(t)
orig["tickets"] = tickets
orig["updated_utc"] = TS_UTC
orig["updated_by"] = "f5-chair-sit-close-label"
orig["as_of_ict"] = TS_ICT
orig_path.write_text(json.dumps(orig, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("DROPPED_ORIG", dropped)
print("CARD_TEXT_BEGIN")
print(card_text, end="")
print("CARD_TEXT_END")
