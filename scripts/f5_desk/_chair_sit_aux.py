import json, subprocess, re
from pathlib import Path

slate_ptr = Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\state\latest_slate.json")
ptr = json.loads(slate_ptr.read_text(encoding="utf-8"))
print("SLATE", ptr.get("slate_id"), ptr.get("fingerprint"), ptr.get("built_at_utc"))
sp = Path(ptr["path"])
j = json.loads(sp.read_text(encoding="utf-8"))
print("KEYS", sorted(j.keys()))
cands = j.get("candidates") or j.get("candidate_set") or j.get("rows") or []
opens = j.get("open_positions") or j.get("opens") or j.get("open_set") or []
print("NCANDS", len(cands) if hasattr(cands, "__len__") else type(cands))
print("NOPENS", len(opens) if hasattr(opens, "__len__") else type(opens))
if isinstance(cands, list):
    for c in cands[:20]:
        if isinstance(c, dict):
            print("C", c.get("id") or c.get("candidate_id") or c.get("cid"), c.get("status"), c.get("symbol") or c.get("instrument"))
        else:
            print("C", c)
elif isinstance(cands, dict):
    for k,v in list(cands.items())[:20]:
        print("C", k, v if not isinstance(v, dict) else (v.get("status"), v.get("symbol")))
if isinstance(opens, list):
    for o in opens:
        if isinstance(o, dict):
            print("O", o.get("ticket") or o.get("id"), o.get("symbol"), o.get("direction") or o.get("side") or o.get("dir"))
        else:
            print("O", o)

# tasks
try:
    out = subprocess.check_output(["schtasks", "/Query", "/FO", "LIST"], text=True, errors="replace")
    name=None
    for line in out.splitlines():
        if line.startswith("TaskName:"):
            name=line.split(":",1)[1].strip()
        if line.startswith("Status:") and name and "GTOS" in name:
            print("TASK", name, line.split(":",1)[1].strip())
            name=None
except Exception as e:
    print("TASK_ERR", e)

# python procs
try:
    out = subprocess.check_output(
        ["wmic", "process", "where", "name='python.exe'", "get", "ProcessId,CommandLine", "/FORMAT:LIST"],
        text=True, errors="replace",
    )
    for chunk in out.split("\n\n"):
        low = chunk.lower()
        if not any(x in low for x in ("gtos", "book_owner", "ftmo_f5", "pair", "judge", "writer")):
            continue
        pid=""; cmd=""
        for line in chunk.splitlines():
            if line.startswith("ProcessId="): pid=line.split("=",1)[1].strip()
            if line.startswith("CommandLine="): cmd=line.split("=",1)[1].strip()[:200]
        if pid:
            print("PID", pid, cmd)
except Exception as e:
    print("PID_ERR", e)

# governor / recon hints in recent verification log
log = Path(r"host-local\redacted_host\repo\shadow_logs\f5_verification.log")
if log.exists():
    text = log.read_text(encoding="utf-8", errors="replace").splitlines()[-200:]
    keys = ("reconciliation", "FAILED", "immutable_entry_risk", "governor_ready", "writer healthy", "pair")
    for line in text:
        if any(k.lower() in line.lower() for k in keys):
            print("LOG", line[-240:])
