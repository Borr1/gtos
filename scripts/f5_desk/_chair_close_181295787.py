import os, sys, json
from datetime import datetime, timezone
from pathlib import Path

repo = Path(r"host-local\redacted_host\repo")
os.chdir(repo)
sys.path.insert(0, str(repo))
from scripts.f5_desk.write_inbox_verdict import main
from scripts.f5_desk import common

# 1) latch orig for the live US30 re-entry if chair_wake_host has not (broker-held print, never moved)
orig_p = repo / "judgment" / "state" / "chair_orig_sl.json"
d = common.read_json(orig_p, default={}) or {}
tk = d.setdefault("tickets", {})
added = None
if "181349108" not in tk:
    tk["181349108"] = 53296.5
    added = "181349108=53296.5"
    d["updated_utc"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    d["note"] = "chair-persisted orig SL from broker-held prints; never moved"
    print("orig_write", common.write_json_atomic(orig_p, d), added)
else:
    print("orig_write skip already_latched", tk.get("181349108"))

mem = (
    "CLOSE 181295787 US30.cash LONG F5:dsp_descendin exit_class=broker_tp "
    "exit=53447.45 [tp 53445.76] vs orig_tp=53445.76 orig_sl=53343.73 entry=53377.74 "
    "(deal 169919916, out 2026-09-03T13:31:26Z, held 15m56s); profit=+307.42 ~+2.05R unit150; "
    "breach=false; orig held both sides, never moved; "
    "US30 NOT flat: isolated re-entry 181349108 LONG 2.23 @53363.6 orig SL 53296.5 TP 53900.41 dsp_wide_down "
    "filled 2026-09-03T14:30:50Z (+59m, 15m window clear) - orig latched by chair; "
    "webhook price field echoed entry not exit; book-event delivery ~87m behind (payload 13:31:29Z, wake 14:58:38Z); "
    "unlabeled closes still queued: XAUUSD 181295784 sl, XAUUSD 181316091 sl, XAUUSD 181349120 sl, GBPUSD 181278435 sl; "
    "no place/remint/flatten; leave GER40 180734064 + JP225 181290161 + US30 181349108 orig; "
    "spent gold 180717112 stays spent"
)
rc = main(["--repo", str(repo), "--memory", mem])
print("rc", rc)
inbox = common.judgment_state_dir(repo) / "inbox" / "verdict.json"
print("inbox_exists", inbox.exists())
if inbox.exists():
    print(inbox.read_text(encoding="utf-8")[:1800])
print("orig_now", (repo / "judgment" / "state" / "chair_orig_sl.json").read_text(encoding="utf-8"))
