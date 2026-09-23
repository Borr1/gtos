from pathlib import Path
import json
p = Path(r"host-local\redacted_host\repo\judgment\live\book_event_spoken.jsonl")
lines = p.read_text(encoding="utf-8").splitlines()
keep = []
removed = 0
for ln in lines:
    if not ln.strip():
        continue
    try:
        o = json.loads(ln)
    except Exception:
        keep.append(ln)
        continue
    if o.get("via") == "f5-chair-sit-catchup" or (
        o.get("source") == "f5-chair-sit"
        and o.get("kind") == "close"
        and o.get("ticket") in (182134088, 182118705)
    ):
        removed += 1
        continue
    keep.append(ln)
p.write_text("\n".join(keep) + ("\n" if keep else ""), encoding="utf-8")
print("removed", removed, "kept", len(keep))
# also show last 2
for ln in keep[-2:]:
    o = json.loads(ln)
    print("LAST", o.get("ts_ict"), o.get("kind"), o.get("ticket"), o.get("source"))
