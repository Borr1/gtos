import csv, subprocess, io
raw = subprocess.check_output(["wmic", "process", "where", "Name='python.exe'", "get", "ProcessId,CommandLine", "/FORMAT:CSV"])
text = raw.decode("utf-8", "replace")
rows = list(csv.DictReader(io.StringIO(text)))
for r in rows:
    cmd = r.get("CommandLine") or ""
    if "operator" in cmd and "wmic" not in cmd.lower() and "_pids.py" not in cmd:
        print(r.get("ProcessId"), cmd[:160])
