import json
from pathlib import Path
p = Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\slates\slate_20260828T065604Z_3a3e029ad80f4bd9.json")
d = json.loads(p.read_text(encoding="utf-8"))
print("keys", sorted(d.keys())[:50])
cands = d.get("candidates") or d.get("candidate_set") or d.get("candidate_ids") or []
opens = d.get("open_positions") or d.get("opens") or d.get("open_set") or []
print("ncands", len(cands) if hasattr(cands, "__len__") else type(cands))
if isinstance(cands, list):
    for c in cands[:40]:
        if isinstance(c, dict):
            print("C", c.get("id") or c.get("candidate_id"), c.get("status"), c.get("symbol") or c.get("broker_symbol"))
        else:
            print("C", c)
elif isinstance(cands, dict):
    for k, v in list(cands.items())[:40]:
        st = v.get("status") if isinstance(v, dict) else v
        print("C", k, st)
print("nopens", len(opens) if hasattr(opens, "__len__") else type(opens))
if isinstance(opens, list):
    for o in opens[:30]:
        if isinstance(o, dict):
            print("O", o.get("ticket") or o.get("ticket_id"), o.get("symbol"), o.get("direction") or o.get("side") or o.get("type"))
        else:
            print("O", o)
# also dump fingerprint fields if nested
print("slate_id", d.get("slate_id"))
print("fingerprint", d.get("fingerprint"))
