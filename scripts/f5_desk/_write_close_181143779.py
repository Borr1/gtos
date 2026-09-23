import os, sys, json
from pathlib import Path
from datetime import datetime, timezone, timedelta

repo = Path(r"host-local\redacted_host\repo")
os.chdir(repo)
sys.path.insert(0, str(repo))
from scripts.f5_desk.write_inbox_verdict import main
from scripts.f5_desk import common

mem = (
    "CLOSE 181143779 US30.cash LONG F5:dsp_descendin exit_class=orig_stop "
    "exit=53137.08 [sl 53137.71] vs orig_sl=53137.71 (deal 169774843); "
    "profit=-163.13 ~-1.09R unit150; flat US30; isolated re-entry after 2026-09-03 13:38 ICT; "
    "no remint; leave GER40 180734064 + XAUUSD 181112899 + EURGBP 181134535 orig; "
    "spent gold 180717112 stays spent"
)
rc = main(["--repo", str(repo), "--memory", mem])
print("rc", rc)
inbox = common.judgment_state_dir(repo) / "inbox" / "verdict.json"
print("inbox", inbox, "exists", inbox.exists())
if inbox.exists():
    print(inbox.read_text(encoding="utf-8")[:2500])
slate = common.judgment_state_dir(repo) / "state" / "latest_slate.json"
print("slate_ptr", slate, "exists", slate.exists())
if slate.exists():
    print(slate.read_text(encoding="utf-8")[:500])
