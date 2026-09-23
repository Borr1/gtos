import os, sys, json
from pathlib import Path

repo = Path(r"host-local\redacted_host\repo")
os.chdir(repo)
sys.path.insert(0, str(repo))
from scripts.f5_desk.write_inbox_verdict import main
from scripts.f5_desk import common

mem = (
    "CLOSE 181134535 EURGBP LONG F5:vss_fxcross_l exit_class=broker_tp "
    "exit=0.86062 [tp 0.86064] vs orig_tp=0.86064 (deal 169864605); "
    "profit=+285.02 ~+1.90R unit150; flat EURGBP; isolated re-entry after 2026-09-03 19:01 ICT; "
    "no remint; leave GER40 180734064 orig; "
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
