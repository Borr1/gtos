from pathlib import Path
import json
p = Path(r"C:host-local/redacted_host/repo/pipeline_state/ultimate_book/operator/judgment/state/latest_slate.json")
j = json.loads(p.read_text(encoding="utf-8"))
print("POINTER", json.dumps(j))
slate = json.loads(Path(j["path"]).read_text(encoding="utf-8"))
print("slate_id", slate.get("slate_id"))
print("fingerprint", slate.get("fingerprint"))
print("KEYS", sorted(slate.keys()))
cands = slate.get("candidates") or slate.get("rows") or slate.get("candidate_rows") or []
print("ncands", len(cands))
for c in cands[:20]:
    if isinstance(c, dict):
        cid = c.get("candidate_id") or c.get("id") or c.get("cid")
        print("CAND", cid, "status=", c.get("status"), "sym=", c.get("symbol"), "dir=", c.get("direction"), "fam=", c.get("family") or c.get("setup_family"))
    else:
        print("CAND_RAW", c)
opens = slate.get("open_positions") or slate.get("opens") or []
print("nopens", len(opens))
for o in opens[:15]:
    if isinstance(o, dict):
        print("OPEN", o.get("ticket"), o.get("symbol"), o.get("direction"))
# also peek governor / reconciliation if present nearby
for rel in [
    r"C:host-local/redacted_host/repo/pipeline_state/ultimate_book/operator/runtime/governor_ready.json",
    r"C:host-local/redacted_host/repo/pipeline_state/ultimate_book/operator/runtime/reconciliation.json",
    r"C:host-local/redacted_host/repo/shadow_logs/writer_heart.json",
]:
    pp = Path(rel)
    print("FILE", rel, "exists", pp.exists())
