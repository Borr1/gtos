from pathlib import Path
import json
p = Path(r"host-local\redacted_host\repo\judgment\live\book_event_spoken.jsonl")
raw = p.read_text(encoding="utf-8")
lines = raw.splitlines()
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
    if not isinstance(o, dict):
        keep.append(ln)
        continue
    if o.get("via") == "f5-chair-sit-catchup":
        removed += 1
        continue
    if (
        o.get("source") == "f5-chair-sit"
        and o.get("kind") == "close"
        and o.get("ticket") in (182134088, 182118705)
    ):
        removed += 1
        continue
    keep.append(ln)
p.write_text("\n".join(keep) + ("\n" if keep else ""), encoding="utf-8")
print("removed", removed, "kept", len(keep))
for ln in keep[-3:]:
    o = json.loads(ln)
    if isinstance(o, dict):
        print("LAST", o.get("ts_ict"), o.get("kind"), o.get("ticket"), o.get("source"))
