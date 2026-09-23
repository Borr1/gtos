import json
from datetime import datetime, timezone
from pathlib import Path
cid="W7_BOOK::dsp_c42::XAUUSD::2026-08-23::LONG::dsp_session_open_already_live"
now=datetime.now(timezone.utc).isoformat()
root=Path(r"host-local\redacted_host\repo\judgment")
for day in ("2026-08-23","2026-08-24"):
    path=root/f"flow_{day}.json"
    data=json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"date":day,"verdicts":{}}
    data.setdefault("verdicts",{})
    row=data["verdicts"].get(cid) or {"candidate_id":cid,"seats":{}}
    row.setdefault("seats",{})
    row["seats"]["geometry"]={"decision":"pass","reason":"instance of declared already_live; 22:00 M15 1.14 ATR UP not L02 not compression; no 20-sweep; stop 5.53; not a known misshape","at":now}
    data["verdicts"][cid]=row
    data["updated_at"]=now
    path.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
    print(day, "geometry", row["seats"]["geometry"]["decision"])
