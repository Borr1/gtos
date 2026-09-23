import os, sys, json
from pathlib import Path
repo = Path(r"host-local\redacted_host\repo")
os.chdir(repo)
sys.path.insert(0, str(repo))
from scripts.f5_desk.write_inbox_verdict import main
mem = (
    "CLOSE 181037756 XAUUSD LONG dsp_descending_lows_accepted exit_class=broker_tp "
    "exit=4387.81 vs tp=4387.72 (deal 169684499 [tp]); profit=+301.17 ~+2.01R unit150; "
    "flat; isolated re-entry after 02:59 ICT; no remint; spent 180717112 stays spent; "
    "leave GER40 180734064 + US30 181037758 orig"
)
rc = main(["--repo", str(repo), "--memory", mem])
print("rc", rc)
from scripts.f5_desk import common
inbox = common.judgment_state_dir(repo) / "inbox" / "verdict.json"
print("inbox", inbox, "exists", inbox.exists())
if inbox.exists():
    print(inbox.read_text(encoding="utf-8")[:2500])
slate = common.judgment_state_dir(repo) / "state" / "latest_slate.json"
print("slate_ptr", slate, "exists", slate.exists())
if slate.exists():
    print(slate.read_text(encoding="utf-8")[:400])
