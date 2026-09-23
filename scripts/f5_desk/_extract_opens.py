import json
p = r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\slates\slate_20260827T133306Z_37b15160e23c3bdb.json"
d = json.load(open(p, encoding="utf-8"))
print("fp", d.get("fingerprint"), "n_cands", len(d.get("candidates") or []))
opens = d.get("open_positions") or []
print("n_open", len(opens))
for x in opens:
    if isinstance(x, dict):
        print("open", x.get("ticket"), x.get("symbol"), x.get("side") or x.get("direction"))
    else:
        print("open", x)
