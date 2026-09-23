
import json, os, subprocess
from pathlib import Path

# pair / writer pids
try:
    out = subprocess.check_output(["wmic", "process", "where", "name='python.exe'", "get", "ProcessId,CommandLine"], text=True, errors="replace")
except Exception as e:
    out = f"wmic_err {e}\n"
    try:
        out = subprocess.check_output(["tasklist", "/FI", "IMAGENAME eq python.exe", "/V", "/FO", "CSV"], text=True, errors="replace")
    except Exception as e2:
        out += f"tasklist_err {e2}\n"

print("===PROCS===")
for line in out.splitlines():
    l = line.strip()
    if not l:
        continue
    low = l.lower()
    if any(x in low for x in ("ftmo", "book_owner", "writer", "pair", "judge", "f5", "16640", "15552", "commandline")):
        print(l[:300])

print("===VERIFY_TAIL===")
log = Path(r"host-local\redacted_host\repo\shadow_logs\f5_verification.log")
if log.exists():
    lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
    for line in lines[-40:]:
        print(line)
else:
    print("missing", log)

print("===SLATE_CANDS===")
slate = Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\state\latest_slate.json")
if slate.exists():
    d = json.loads(slate.read_text(encoding="utf-8"))
    print("slate_id", d.get("slate_id"), "fp", d.get("fingerprint"), "built", d.get("built_at_utc"))
    cands = d.get("candidates") or d.get("candidate_set") or d.get("rows") or []
    opens = d.get("open_positions") or d.get("opens") or []
    print("n_cands", len(cands), "n_open", len(opens))
    print("top_keys", list(d.keys())[:30])
    for c in cands[:40]:
        if isinstance(c, dict):
            print(c.get("candidate_id") or c.get("id"), c.get("status"), c.get("symbol"), c.get("direction"))
        else:
            print(c)
    for o in opens[:20]:
        print("OPEN", o)
else:
    print("missing slate")
