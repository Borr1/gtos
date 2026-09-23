from pathlib import Path
import json, os
# governor from slate
p = Path(r"C:host-local/redacted_host/repo/pipeline_state/ultimate_book/operator/judgment/state/latest_slate.json")
j = json.loads(p.read_text(encoding="utf-8"))
slate = json.loads(Path(j["path"]).read_text(encoding="utf-8"))
print("governor", json.dumps(slate.get("governor"), default=str)[:800])
print("refusals", json.dumps(slate.get("refusals"), default=str)[:800])
print("skips", json.dumps(slate.get("skips"), default=str)[:500])
print("flow_state", json.dumps(slate.get("flow_state"), default=str)[:500])
# intent-only candidates with more detail
for c in slate.get("candidates") or []:
    if c.get("status") == "intent":
        print("INTENT", c.get("candidate_id"), "why=", (c.get("why") or c.get("reason") or "")[:80], "keys", [k for k in c.keys() if k not in ("packet","bars","features")])
# writer pids via psutil or tasklist
import subprocess
r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq python.exe", "/FO", "CSV", "/NH"], capture_output=True, text=True)
print("TASKLIST", r.stdout[:500])
# look for pair file
for rel in [
 r"C:host-local/redacted_host/repo/pipeline_state/ultimate_book/operator/runtime",
 r"C:host-local/redacted_host/repo/shadow_logs",
]:
  d=Path(rel)
  if d.exists():
    names=sorted([x.name for x in d.iterdir()])[:40]
    print("DIR", rel, names)
