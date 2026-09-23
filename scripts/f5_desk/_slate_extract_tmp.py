import json
from pathlib import Path
p = Path(r"C:host-local/redacted_host/repo/pipeline_state/ultimate_book/operator/judgment/state/latest_slate.json")
meta = json.loads(p.read_text(encoding="utf-8"))
sp = Path(meta["path"])
d = json.loads(sp.read_text(encoding="utf-8"))
print("slate", meta.get("slate_id"), meta.get("fingerprint"))
print("keys", sorted(d.keys())[:50])
cands = d.get("candidates") or d.get("candidate_set") or d.get("rows") or []
opens = d.get("open_positions") or d.get("opens") or d.get("open_set") or []
print("ncand", len(cands) if isinstance(cands, list) else type(cands).__name__)
print("nopen", len(opens) if isinstance(opens, list) else type(opens).__name__)
for c in (cands if isinstance(cands, list) else [])[:40]:
    if isinstance(c, dict):
        print("C", c.get("candidate_id") or c.get("id"), c.get("status"), c.get("symbol") or c.get("sym"))
    else:
        print("C", c)
for o in (opens if isinstance(opens, list) else [])[:20]:
    if isinstance(o, dict):
        print("O", o.get("ticket"), o.get("symbol") or o.get("sym"), o.get("direction") or o.get("side"))
    else:
        print("O", o)
# also dump compact candidate ids if nested
if isinstance(cands, dict):
    for k,v in list(cands.items())[:30]:
        print("CK", k, str(v)[:80])
