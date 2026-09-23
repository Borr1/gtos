import json
from pathlib import Path
sp = Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\slates\slate_20260827T214602Z_0c024b5a5b6932df.json")
s = json.loads(sp.read_text(encoding="utf-8"))
print("GOVERNOR", json.dumps(s.get("governor"), default=str)[:2000])
print("REFUSALS", json.dumps(s.get("refusals"), default=str)[:2000])
print("SKIPS", json.dumps(s.get("skips"), default=str)[:1500])
print("FLOW", json.dumps(s.get("flow_state"), default=str)[:1500])
print("PACKET", json.dumps(s.get("packet_contract"), default=str)[:800])
# intent-only candidate ids
print("---INTENTS---")
for c in s.get("candidates") or []:
    st = (c.get("status") or "").lower()
    if st in ("intent", "eligible", "ready", "holdable", "pending"):
        print(json.dumps({k:c.get(k) for k in ["candidate_id","status","direction","symbol","family","stop","setup"]}, default=str))

base = Path(r"host-local\redacted_host\repo")
for q in [
    base/"pipeline_state"/"ultimate_book"/"operator"/"judgment"/"chair_orig_sl.json",
    base/"scripts"/"f5_desk"/"chair_orig_sl.json",
    Path(r"host-local\redacted_host\repo\judgment\chair_orig_sl.json"),
    Path(r"host-local\redacted_host\live\chair_orig_sl.json"),
]:
    if q.exists():
        print("ORIG", q)
        print(q.read_text(encoding="utf-8")[:2000])

# find orig
hits=[]
for root in [Path(r"host-local\redacted_host\repo"), Path(r"host-local\redacted_host")]:
    if not root.exists():
        continue
    for q in root.rglob("*orig_sl*"):
        if q.is_file():
            hits.append(str(q))
print("ORIGHITS", hits[:20])

inbox = Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\inbox")
applied = inbox / "applied"
if applied.exists():
    files = sorted(applied.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:1]
    for f in files:
        print("LAST_APPLIED", f.name)
        print(f.read_text(encoding="utf-8")[:2500])
tmp = inbox / "verdict.json.tmp"
if tmp.exists():
    print("TMP_EXISTS", tmp.stat().st_size)
vin = inbox / "_verdict_in.json"
if vin.exists():
    print("VERDICT_IN", vin.read_text(encoding="utf-8")[:2000])
