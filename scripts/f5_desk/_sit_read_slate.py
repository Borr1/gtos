import json
from pathlib import Path
p = Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\state\latest_slate.json")
d = json.loads(p.read_text(encoding="utf-8"))
print("POINTER", json.dumps(d))
sp = Path(d["path"])
print("slate_exists", sp.exists())
s = json.loads(sp.read_text(encoding="utf-8"))
print("top_keys", sorted(s.keys()))
cands = s.get("candidates") or s.get("candidate_set") or s.get("rows") or []
print("ncand", len(cands))
for c in cands[:12]:
    if isinstance(c, str):
        print("C", c)
    elif isinstance(c, dict):
        print("C", c.get("id") or c.get("candidate_id") or c.get("cid"), "status", c.get("status"), "sym", c.get("symbol"))
opens = s.get("open_positions") or s.get("opens") or s.get("open_set") or []
print("nopen", len(opens))
for o in opens[:12]:
    if isinstance(o, dict):
        print("O", o.get("ticket"), o.get("symbol"), o.get("direction") or o.get("side"))
    else:
        print("O", o)
# recon / governor sniff
for rel in [
    r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\reconciliation.json",
    r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\governor_ready.json",
    r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\runtime\governor_ready.json",
]:
    pp = Path(rel)
    print("FILE", rel, "exists", pp.exists())
    if pp.exists():
        t = pp.read_text(encoding="utf-8", errors="replace")[:800]
        print(t)
