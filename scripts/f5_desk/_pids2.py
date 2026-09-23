import csv, subprocess, io
raw = subprocess.check_output(["wmic", "process", "where", "Name='python.exe'", "get", "ProcessId,CommandLine", "/FORMAT:CSV"])
text = raw.decode("utf-8", "replace")
print("RAW_LEN", len(text))
print("HEAD", repr(text[:400]))
rows = list(csv.DictReader(io.StringIO(text)))
print("NROWS", len(rows), "KEYS", list(rows[0].keys()) if rows else None)
for r in rows[:8]:
    cmd = list(r.values())
    print(cmd)
