
import json
from pathlib import Path
p = Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\state\latest_slate.json")
d = json.loads(p.read_text(encoding="utf-8"))
print("slate_id", d.get("slate_id"))
print("fingerprint", d.get("fingerprint"))
print("keys", sorted(d.keys()))
for k in ("built_at_utc","as_of_utc","clock","governor_ready","reconciliation"):
    if k in d: print(k, d.get(k))
cands = d.get("candidates") or []
opens = d.get("open_positions") or d.get("opens") or []
print("n_cand", len(cands) if isinstance(cands, list) else type(cands))
print("n_open", len(opens) if isinstance(opens, list) else type(opens))
if isinstance(cands, list):
    for c in cands[:20]:
        if isinstance(c, dict):
            cid = c.get("id") or c.get("candidate_id") or c.get("cid")
            print("CAND", cid, "status", c.get("status"), "sym", c.get("symbol"), "dir", c.get("direction") or c.get("side"))
        else:
            print("CAND", c)
if isinstance(opens, list):
    for o in opens[:20]:
        if isinstance(o, dict):
            print("OPEN", o.get("ticket"), o.get("symbol"), o.get("direction") or o.get("type") or o.get("side"))
        else:
            print("OPEN", o)
# dump compact for local
Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\state\_slate_brief.json").write_text(
    json.dumps({
        "slate_id": d.get("slate_id"),
        "fingerprint": d.get("fingerprint"),
        "keys": sorted(d.keys()),
        "candidates": cands if isinstance(cands, list) else str(type(cands)),
        "open_positions": opens if isinstance(opens, list) else str(type(opens)),
        "governor": {k: d.get(k) for k in d if "govern" in k.lower() or "reconcil" in k.lower() or "immutable" in k.lower() or k in ("clock","built_at_utc","as_of_utc")},
    }, default=str)[:200000],
    encoding="utf-8",
)
print("brief_written")
