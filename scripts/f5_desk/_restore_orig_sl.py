import os, sys, json
from datetime import datetime, timezone
from pathlib import Path
repo = Path(r"host-local\redacted_host\repo")
os.chdir(repo); sys.path.insert(0, str(repo))
from scripts.f5_desk import common
p = repo / "judgment" / "state" / "chair_orig_sl.json"
prior = {
    "181278429": 53260.62,
    "180734064": 25568.61,
    "181278435": 1.35003,
    "181290161": 63130.5,
    "181295784": 4481.6,
}
cur = json.loads(p.read_text(encoding="utf-8-sig"))
tk = dict(cur.get("tickets") or {})
for k, v in prior.items():
    tk.setdefault(k, v)
tk.setdefault("181349108", 53296.5)
out = {
    "tickets": tk,
    "updated_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    "note": "chair-persisted orig SL from broker-held prints; never moved",
}
print("write", common.write_json_atomic(p, out))
print(p.read_text(encoding="utf-8-sig"))
