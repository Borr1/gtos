
import json
p = r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\slates\slate_20260828T084102Z_a97e375dd24fcdef.json"
d = json.load(open(p, encoding="utf-8"))
print("slate_id", d.get("slate_id"))
print("fingerprint", d.get("fingerprint"))
print("keys", sorted(d.keys()))
cands = d.get("candidates") or d.get("candidate_set") or d.get("candidate_ids") or []
opens = d.get("opens") or d.get("open_set") or d.get("open_positions") or d.get("positions") or []
print("cand_type", type(cands).__name__, "open_type", type(opens).__name__)
if isinstance(cands, list):
    print("cand_n", len(cands))
    for c in cands[:40]:
        if isinstance(c, dict):
            print("CAND", c.get("candidate_id") or c.get("id"), c.get("status"), c.get("symbol"), c.get("direction") or c.get("side"))
        else:
            print("CAND", c)
elif isinstance(cands, dict):
    print("cand_n", len(cands))
    for k, v in list(cands.items())[:40]:
        if isinstance(v, dict):
            print("CAND", k, v.get("status"), v.get("symbol"), v.get("direction") or v.get("side"))
        else:
            print("CAND", k, v)
if isinstance(opens, list):
    print("open_n", len(opens))
    for o in opens[:40]:
        if isinstance(o, dict):
            print("OPEN", o.get("ticket"), o.get("symbol"), o.get("direction") or o.get("side"), o.get("candidate_id") or o.get("id"))
        else:
            print("OPEN", o)
elif isinstance(opens, dict):
    print("open_n", len(opens))
    for k, v in list(opens.items())[:40]:
        print("OPEN", k, v if not isinstance(v, dict) else {kk: v.get(kk) for kk in ("ticket","symbol","direction","side","status","candidate_id") if kk in v})
