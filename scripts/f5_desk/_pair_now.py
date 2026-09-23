import subprocess, time
from pathlib import Path
print("UTC", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
r = subprocess.run(["schtasks", "/query", "/tn", "GTOS_F5_FTMO", "/fo", "LIST", "/v"], capture_output=True, text=True)
print(r.stdout)
print("---PROCS---")
r2 = subprocess.run(["wmic", "process", "where", "name='python.exe'", "get", "ProcessId,CommandLine", "/format:list"], capture_output=True, text=True)
keys = ("GTOS_F5", "book_owner", "ftmo_f5", "ultimate_book", "terminal64")
seen = False
for block in r2.stdout.split("\n\n"):
    if any(k.lower() in block.lower() for k in keys):
        print(block.strip())
        print("----")
        seen = True
if not seen:
    print("no matching python")
    # still print pid lines
    for line in r2.stdout.splitlines():
        if line.strip().startswith("ProcessId="):
            print(line)
hb_root = Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator")
print("---HBFILES---")
if hb_root.exists():
    files = sorted(hb_root.rglob("*"), key=lambda p: p.stat().st_mtime if p.is_file() else 0, reverse=True)[:15]
    for p in files:
        if p.is_file():
            print(int(p.stat().st_mtime), p)
else:
    print("missing", hb_root)
hb = Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\heartbeat.json")
print("---HBJSON---", hb.exists())
if hb.exists():
    print(hb.read_text(encoding="utf-8")[:800])
# common pair file
for cand in [
    r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\heartbeat.json",
    r"host-local\redacted_host\repo\judgment\live\heartbeat.json",
    r"host-local\redacted_host\repo\shadow_logs\heartbeat.json",
]:
    p = Path(cand)
    print("CAND", cand, p.exists(), p.stat().st_mtime if p.exists() else None)
