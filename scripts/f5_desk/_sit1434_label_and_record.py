#!/usr/bin/env python3
"""F5 Chair Sit 2026-09-08 ~14:39 ICT: LABEL XAU 182201750 orig_stop + sit record."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(r"host-local\redacted_host\repo")
LIVE = REPO / "judgment" / "live"
sys.path.insert(0, str(REPO))

from scripts.f5_desk import write_inbox_verdict as wiv  # noqa: E402

ICT = timezone(timedelta(hours=7))
NOW = datetime.now(timezone.utc)
NOW_ICT = NOW.astimezone(ICT)
TS_ICT = NOW_ICT.strftime("%Y-%m-%d %H:%M ICT")
TS_UTC = NOW.isoformat().replace("+00:00", "Z")

# MT5 terminal clock ~+3h vs wall; wall times below match book-event payload_ts convention.
close = {
    "ticket": 182201750,
    "symbol": "XAUUSD",
    "side": "LONG",
    "tag": "dsp_accepted_",
    "exit_class": "orig_stop",
    "entry": 4400.23,
    "orig_sl": 4393.89,
    "orig_tp": 4450.4,
    "exit": 4393.83,
    "volume": 0.23,
    "deal_in": 170712671,
    "deal_out": 170734217,
    "order_out": 182225132,
    "broker_comment": "[sl 4393.89]",
    "deal_reason": 4,
    "profit": -147.2,
    "commission": -0.71,
    "realised_r_unit150": round((-147.2 + -0.71) / 150.0, 2),
    "r_points": 6.34,
    "slip_pts": 0.06,
    "fill_ict": "2026-09-08 13:31 ICT",
    "close_ict": "2026-09-08 14:39 ICT",
    "fill_utc": "2026-09-08T06:31:03Z",
    "close_utc": "2026-09-08T07:39:24Z",
    "held": "1h8m",
    "isolated_reentry_after_ict": "2026-09-08 14:54 ICT",
    "note": "since London session-open 14:31; book-event close not spoken yet; sit LABEL; orig never moved; slip 0.06",
}

# snap from MT5 probe ~07:39Z (+ minor drift); refresh if needed
bal, eq = 92449.83, 92110.46
day_net = round(92449.83 - 92597.74 + (-429.49), 2)  # prior day_net at 14:31 was -429.49 on bal 92597.74; after close bal drop ~147.91
# cleaner: use chair_desk day_net from first sit before close was -429.49 on bal 92597.74; after close bal=92449.83
# day_net typically = bal - start_of_day_bal; approximate from prior: day_net_new = -429.49 + (92449.83-92597.74) = -577.4
day_net = round(-429.49 + (92449.83 - 92597.74), 2)

open_now = [
    {
        "ticket": 180734064, "symbol": "GER40.cash", "side": "LONG", "tag": "mx_ger40_cash",
        "lots": 0.55, "entry": 25803.47, "orig_sl": 25568.61, "live_sl": 25568.61, "tp": 26273.19,
        "mark": 25880.14, "pnl": 48.97, "magic": 0,
        "spread": 1.33, "stop_dist": 234.86, "spread_over_R": round(1.33 / 234.86, 4),
        "trade_mode": 4, "broker_sl_present": True, "stop_not_original": False, "container": "ok",
        "age": "~6d7h",
    },
    {
        "ticket": 181801554, "symbol": "DASHUSD", "side": "LONG", "tag": "W7:crypto",
        "lots": 0.06, "entry": 69.02, "orig_sl": 61.55, "live_sl": 61.55, "tp": 98.88,
        "mark": 62.84, "pnl": -370.8, "magic": 20260401,
        "spread": 0.03, "stop_dist": 7.47, "spread_over_R": round(0.03 / 7.47, 4),
        "trade_mode": 4, "broker_sl_present": True, "stop_not_original": False, "container": "ok",
        "note": "red PnL alone not broken; dual W7 intentional; chair_desk PATH omits W7",
        "age": "~3d2h",
    },
    {
        "ticket": 181801555, "symbol": "DASHUSD", "side": "LONG", "tag": "F5:crypto",
        "lots": 0.02, "entry": 69.08, "orig_sl": 61.59, "live_sl": 61.59, "tp": 99.06,
        "mark": 62.84, "pnl": -124.8, "magic": 0,
        "spread": 0.03, "stop_dist": 7.49, "spread_over_R": round(0.03 / 7.49, 4),
        "trade_mode": 4, "broker_sl_present": True, "stop_not_original": False, "container": "ok",
        "note": "red PnL alone not broken",
        "age": "~3d2h",
    },
    {
        "ticket": 182201752, "symbol": "US30.cash", "side": "LONG", "tag": "dsp_accepted_",
        "lots": 6.78, "entry": 52932.72, "orig_sl": 52910.05, "live_sl": 52910.05, "tp": 53109.48,
        "mark": 52951.66, "pnl": 128.41, "magic": 0,
        "spread": 2.48, "stop_dist": 22.67, "spread_over_R": round(2.48 / 22.67, 4),
        "trade_mode": 4, "broker_sl_present": True, "stop_not_original": False, "container": "ok",
        "age": "~1h8m", "R_orig": round((52951.66 - 52932.72) / 22.67, 2),
    },
]

memory_lines = [
    (
        f"LABEL_CLOSE {close['symbol']} {close['ticket']} {close['side']} {close['tag']} "
        f"exit_class={close['exit_class']} exit={close['exit']} {close['broker_comment']} "
        f"profit={close['profit']} commission={close['commission']} "
        f"~{close['realised_r_unit150']}R(unit150) held {close['held']}; "
        f"filled {close['fill_ict']} closed {close['close_ict']}; "
        f"orig_sl={close['orig_sl']} orig_tp={close['orig_tp']}; "
        f"isolated re-entry after {close['isolated_reentry_after_ict']}; no remint"
    )
]

slate = wiv.load_slate(REPO)
payload = wiv.bind({
    "verdicts": [],
    "manage": [],
    "memory": memory_lines,
    "source": "f5-chair-sit",
    "note": "hourly sit 2026-09-08 14:39 ICT: LABEL XAU 182201750 orig_stop; OPEN4 leave-orig; no manage",
}, slate)
inbox = wiv._inbox_path(REPO)
inbox.parent.mkdir(parents=True, exist_ok=True)
inbox.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("WROTE_VERDICT", inbox, "slate", payload.get("slate_id"), "fp", payload.get("fingerprint"))

open_left = [
    "GER40 180734064 LONG",
    "DASHUSD 181801554 W7 LONG",
    "DASHUSD 181801555 F5 LONG",
    "US30 182201752 LONG",
]

card_text = (
    f"{TS_ICT} | 0 bal {bal} eq ~{eq:.0f}\n"
    f"CLOSE XAUUSD LONG {close['ticket']} exit_class={close['exit_class']} exit={close['exit']} "
    f"{close['broker_comment']} ~{close['realised_r_unit150']}R(unit150) broker_net={close['profit']} "
    f"held {close['held']} | orig never moved | flat; re-entry after {close['isolated_reentry_after_ict']}\n"
    f"leave GER40 `180734064` LONG + DASH W7 `181801554` + DASH F5 `181801555` + US30 `182201752` LONG | "
    f"pendings none | day_net ~{day_net} to_pass ~{round(105000-bal,2)} | spent 180717112 stays spent | no remint\n"
    f"ctx: sit backstop LABEL — XAU 182201750 orig_stop ~14:39 after London open 14:31; "
    f"OPEN4 containers ok spread<<1R live==orig trade_mode4 | red DASH PnL alone not broken | "
    f"dual W7 intentional | fills XAU+US30 already LEAVE @13:36 | no HIGH inside 60m (next ECB 10 Sep) | "
    f"no place/remint/flatten"
)

def append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")

def write_json(path: Path, obj: dict) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

row = {
    "ts_ict": TS_ICT,
    "ts_utc": TS_UTC,
    "source": "f5-chair-sit",
    "kind": "close",
    "ticket": close["ticket"],
    "symbol": close["symbol"],
    "side": close["side"],
    "comment": close["tag"],
    "login": 0,
    "action": "LABEL_CLOSE",
    "spoken": True,
    "word": "LABEL",
    "place": False,
    "remint": False,
    "hold": False,
    "flatten": False,
    "exit_class": close["exit_class"],
    "breach": False,
    "entry": close["entry"],
    "orig_sl": close["orig_sl"],
    "orig_tp": close["orig_tp"],
    "exit": close["exit"],
    "volume": close["volume"],
    "deal_in": close["deal_in"],
    "deal_out": close["deal_out"],
    "order_out": close["order_out"],
    "broker_comment": close["broker_comment"],
    "deal_reason": close["deal_reason"],
    "profit": close["profit"],
    "commission": close["commission"],
    "realised_r_unit150": close["realised_r_unit150"],
    "r_points": close["r_points"],
    "slip_pts": close["slip_pts"],
    "fill_ict": close["fill_ict"],
    "close_ict": close["close_ict"],
    "fill_utc": close["fill_utc"],
    "close_utc": close["close_utc"],
    "held": close["held"],
    "isolated_reentry_after_ict": close["isolated_reentry_after_ict"],
    "note": close["note"],
    "open_left": open_left,
    "pending": 0,
    "account": {"login": 0, "balance": bal, "equity": eq},
    "spent_gold_180717112": "leave spent",
    "verdict": {
        "wrote": str(inbox),
        "slate_id": payload.get("slate_id"),
        "fingerprint": payload.get("fingerprint"),
        "n_verdicts": 0,
        "n_memory": len(memory_lines),
        "written_at_utc": TS_UTC,
        "schema": "gtos.f5.judge.verdict.v1",
    },
    "card": card_text,
    "session": "2026-09-08",
    "ledger": "label_close",
    "via": "hourly-chair-sit",
}

for name in ("book_event_ledger.jsonl", "book_event_spoken.jsonl", "chair_sit_spoken.jsonl"):
    append_jsonl(LIVE / name, row)
write_json(LIVE / f"_close_speak_{close['ticket']}.json", row)
write_json(LIVE / "book_event_spoken_last.json", {
    "kind": "close",
    "ticket": close["ticket"],
    "symbol": close["symbol"],
    "ts_utc": TS_UTC,
    "word": "LABEL",
    "exit_class": close["exit_class"],
})

sit = {
    "ts_ict": TS_ICT,
    "ts_utc": TS_UTC,
    "source": "f5-chair-sit",
    "kind": "hourly_sit",
    "routine": "f5-chair-sit",
    "login": 0,
    "spoken": True,
    "card": True,
    "fingerprint": f"hourly-sit-{NOW_ICT.strftime('%Y%m%dT%H%M')}-xau-orig-stop",
    "bal": bal,
    "eq": eq,
    "day_net": day_net,
    "to_pass": round(105000 - bal, 2),
    "positions": 4,
    "pending": 0,
    "open_left": open_left,
    "opens_snap": open_now,
    "broken_containers": [],
    "stop_not_original": [],
    "closes_labeled_now": [close],
    "closes_needing_label": [],
    "fills_covered_lt_50m": [
        {"ticket": 182201752, "labeled_by": "f5-chair-sit", "ict": "2026-09-08 13:36 ICT"},
    ],
    "calendar_within_60m": None,
    "spent_gold_180717112": "leave spent",
    "f5_new_orders": "owner dual F5+Astra-W7; opens leave orig; no place from chair",
    "path_note": "chair_desk PATH listed 4 (omitted W7 181801554); MT5 confirms 4 LIVE incl W7 after XAU close",
    "broker_via": "chair_desk sit --mt5 + MetaTrader5 history_deals_get(position=)",
    "release": "f5-live c19c3aff9 (2026-09-02)",
    "verdict": row["verdict"],
    "card_text": card_text,
    "session": "2026-09-08",
    "ledger": "chair_sit_spoken.jsonl",
    "why_card": "CLOSE XAU 182201750 orig_stop since London open; not covered by book-event in last 50m",
    "no_place_remint_flatten": True,
    "ok": True,
}
write_json(LIVE / "chair_sit_last.json", sit)
write_json(LIVE / "chair_last_sit.json", sit)
print("SIT_OK", sit["fingerprint"])
print(card_text)
