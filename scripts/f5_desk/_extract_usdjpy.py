import json, os, glob
base = r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment"
ptr = json.load(open(os.path.join(base, r"state\latest_slate.json"), encoding="utf-8"))
print("PTR slate_id", ptr.get("slate_id"))
print("PTR fingerprint", ptr.get("fingerprint"))
print("PTR keys", list(ptr.keys())[:20])
sid = ptr.get("slate_id")
path = ptr.get("slate_path") or ptr.get("path")
if not path:
    cands = glob.glob(os.path.join(base, r"slates", f"*{sid}*.json"))
    path = cands[0] if cands else None
print("PATH", path)
if path and os.path.exists(path):
    d = json.load(open(path, encoding="utf-8"))
    print("FILE slate_id", d.get("slate_id"))
    print("FILE fingerprint", d.get("fingerprint"))
    items = d.get("candidates") or d.get("intents") or []
    if isinstance(items, dict):
        items = list(items.values())
    print("n", len(items))
    for x in items:
        if not isinstance(x, dict):
            continue
        cid = x.get("candidate_id") or x.get("id") or ""
        if "USDJPY" in cid:
            print(cid)
