import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

base = Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\state")
live = Path(r"host-local\redacted_host\repo\judgment\live")

def load(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception as e:
        return {"_error": str(e)}

for name in [
    "chair_last_sit.json",
    "latest_slate.json",
    "chair_health.json",
    "f5_high_calendar.json",
    "just_closed_siblings.json",
    "breach_counter.json",
    "last_judged.json",
    "chair_wake.json",
]:
    p = base / name
    data = load(p)
    print(f"==== {name} ====")
    print(json.dumps(data, indent=2, default=str)[:4000])
    print()

# book event state keys for open tickets
be = load(live / "book_event_watch_state.json")
print("==== book_event_watch_state (keys/snippet) ====")
if isinstance(be, dict):
    print("top_keys", list(be.keys())[:30])
    # search tickets
    s = json.dumps(be)
    for t in ["180622571", "180734064", "180775761", "180886874", "180717112", "180770382", "container", "close"]:
        print(f"contains {t}:", t in s)
    # try dump recent events
    for k in ["recent", "events", "last", "history", "tickets", "seen", "dedupe", "last_emit", "emitted"]:
        if k in be:
            print(f"field {k}:", json.dumps(be[k], default=str)[:1500])
else:
    print(be)

# tail book event log
logp = live / "book_event_watch.log"
print("==== book_event log tail ====")
if logp.exists():
    lines = logp.read_text(encoding="utf-8", errors="replace").splitlines()
    for line in lines[-30:]:
        print(line[:500])
