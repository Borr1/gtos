
import json, glob
from pathlib import Path
root = Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment")
ptr = json.loads((root/"state"/"latest_slate.json").read_text(encoding="utf-8"))
sid = ptr["slate_id"]
fp = ptr["fingerprint"]
print("PTR", sid, fp, ptr.get("built_at_utc"))
slates = list((root/"slates").glob(f"slate_*_{sid}.json"))
print("matches", len(slates), [p.name for p in slates[:5]])
if not slates:
    slates = sorted((root/"slates").glob("slate_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:3]
    print("recent", [p.name for p in slates])
out = []
for p in slates[:1]:
    d = json.loads(p.read_text(encoding="utf-8"))
    print("FILE", p.name, "keys", sorted(d.keys())[:50])
    print("slate_id", d.get("slate_id"), "fp", d.get("fingerprint"))
    cands = d.get("candidates") or d.get("candidate_set") or []
    opens = d.get("open_positions") or d.get("opens") or d.get("open_set") or []
    print("n_cand", len(cands) if isinstance(cands, list) else type(cands))
    print("n_open", len(opens) if isinstance(opens, list) else type(opens))
    if isinstance(cands, list):
        for c in cands:
            if isinstance(c, dict):
                cid = c.get("id") or c.get("candidate_id") or c.get("cid")
                print("CAND", cid, "status", c.get("status"), "sym", c.get("symbol"), "dir", c.get("direction") or c.get("side"), "family", c.get("family") or c.get("setup") or c.get("tag"))
            else:
                print("CAND", c)
    if isinstance(opens, list):
        for o in opens:
            if isinstance(o, dict):
                print("OPEN", {k:o.get(k) for k in list(o)[:12]})
            else:
                print("OPEN", o)
    # governor bits
    for k,v in d.items():
        lk=k.lower()
        if any(s in lk for s in ("govern","reconcil","immutable","ready")):
            print("META", k, v)
    brief_cands=[]
    if isinstance(cands, list):
        for c in cands:
            if isinstance(c, dict):
                brief_cands.append({k:c.get(k) for k in ("id","candidate_id","cid","status","symbol","direction","side","family","setup","tag","why_code") if k in c})
            else:
                brief_cands.append(c)
    Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\state\_slate_archive_brief.json").write_text(json.dumps({
        "file": p.name,
        "slate_id": d.get("slate_id"),
        "fingerprint": d.get("fingerprint"),
        "keys": sorted(d.keys()),
        "candidates": brief_cands,
        "opens": opens if isinstance(opens, list) else str(type(opens)),
        "n_cand": len(cands) if isinstance(cands, list) else None,
        "n_open": len(opens) if isinstance(opens, list) else None,
    }, default=str)[:400000], encoding="utf-8")
    print("brief_ok")
# also reconcil / governor files
for rel in [
    r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\governor.json",
    r"host-local\redacted_host\repo\judgment\live\latest.json",
]:
    pp=Path(rel)
    print("EXISTS", rel, pp.exists(), "size", pp.stat().st_size if pp.exists() else None)
