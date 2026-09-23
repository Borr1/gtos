# Persist F5 Chair Sit quiet result — 2026-09-17 ~15:28 ICT
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

ICT = timezone(timedelta(hours=7))
now_utc = datetime.now(timezone.utc)
now_ict = now_utc.astimezone(ICT)

live = Path(r"host-local\redacted_host\repo\judgment\live")
live.mkdir(parents=True, exist_ok=True)

payload = {
    "as_of_utc": now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
    "as_of_ict": now_ict.strftime("%Y-%m-%d %H:%M ICT"),
    "session": "ny",
    "session_note": f"{now_ict.strftime('%Y-%m-%d %H:%M ICT')}; NY afternoon; BOE T-45 at 17:15 ICT not yet",
    "account_login": 0,
    "balance": 95540.23,
    "equity": 95931.19,
    "day_net": 224.30,
    "to_pass": 14459.77,
    "pass_target": 110000,
    "opens": [
        {
            "ticket": 293332188,
            "symbol": "XAUUSD",
            "side": "SHORT",
            "sleeve": "dsp_two_bar_t",
            "lots": 0.27,
            "entry": 4331.45,
            "orig_sl": 4336.90,
            "live_sl": 4336.90,
            "tp": 4288.19,
            "mark": 4316.33,
            "pnl": 390.96,
            "R_orig": 2.64,
            "mechanics": {
                "broker_stop_present": True,
                "live_equals_orig": True,
                "symbol_trading": True,
                "trade_mode": "full",
                "spread": 0.40,
                "stop_dist": 5.45,
                "spread_R": 0.0734,
                "spread_vs_stop_ok": True,
                "broken_container": False,
                "note": "spread 0.40 vs stop 5.45 (~0.073R); SL present live==orig; XAU full trade; green PnL alone not broken",
            },
        }
    ],
    "pendings": [],
    "just_labeled": [],
    "prior_close_already_spoken": {
        "ticket": 293207416,
        "symbol": "XAUUSD",
        "kind": "close",
        "spoken_ict": "2026-09-17 11:46 ICT",
        "source": "f5-book-event",
        "exit_class": "time_stop",
        "broker_net": 224.94,
        "age_min_at_sit": 222.0,
    },
    "prior_fill_already_covered": {
        "ticket": 293332188,
        "kind": "fill",
        "source": "f5-book-event",
        "word": "LEAVE_ORIG",
        "covered_ict": "2026-09-17 14:33 ICT",
        "covered_utc": "2026-09-17T07:33:56Z",
        "within_50m": False,
        "age_min_at_sit": 54.0,
        "note": "fill LEAVE_ORIG latched book-event ~54m ago; occupancy alone is not a card trigger",
    },
    "decision": "QUIET; leave XAUUSD 293332188 orig; mechanics OK; fill LEAVE_ORIG spoken book-event 14:33 ICT; close 293207416 already LABEL'd 11:46; no broken/pending>45m; no place/manage/flatten",
    "composer": "f5-chair-sit",
    "card": None,
    "action": "QUIET",
    "spoken": False,
    "change": False,
    "fingerprint": "hourly-quiet-20260917T0828-xau-path",
    "reasons_quiet": [
        "open 293332188 mechanics OK (SL present live==orig, trade full, spread_R~0.073 < 1)",
        "fill LEAVE_ORIG covered by f5-book-event 14:33 ICT; floating green alone is not a change card",
        "close 293207416 already LABEL spoken book-event 11:46 ICT; no re-card",
        "pending 0; no broken container; BOE 17:15 ICT nearby HIGH alone not broken",
        "MCP+chair_desk agree: login 0 Challenge, positions 1 pending 0",
    ],
    "broker": {
        "via": [
            "chair_desk.py sit --mt5 via gtos-vps (.venv-gtos)",
            "user-mt5-ftmo MCP account/open/history/marketwatch",
        ],
        "positions": 1,
        "pending": 0,
        "occupied": ["XAUUSD"],
        "fast_live": True,
        "server": "FTMO-Server",
        "magic": 0,
    },
    "wake_parent": False,
    "verdict_wrote": False,
}

out = live / "latest.json"
out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print("wrote", out)

ledger_line = {
    "ts_ict": now_ict.strftime("%Y-%m-%d %H:%M ICT"),
    "ts_utc": now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
    "source": "f5-chair-sit",
    "kind": "sit",
    "action": "QUIET",
    "spoken": False,
    "login": 0,
    "note": payload["decision"],
    "ledger": "sit_backstop_quiet",
    "session": now_ict.strftime("%Y-%m-%d"),
    "fingerprint": payload["fingerprint"],
    "open_tickets": [293332188],
}
ledger = live / "book_event_ledger.jsonl"
with ledger.open("a", encoding="utf-8") as f:
    f.write(json.dumps(ledger_line, separators=(",", ":")) + "\n")
print("appended ledger", ledger)

# also refresh box mirror if present
box = Path("/workspace/gtos/live")
if box.exists():
    (box / "latest.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("mirrored box latest.json")
