import subprocess, re
raw = subprocess.check_output(
    "wmic process where \"CommandLine like '%%operator%%'\" get ProcessId,CommandLine /FORMAT:LIST",
    shell=True, text=True, errors="replace",
)
pids = []
for m in re.finditer(r"ProcessId=(\d+)", raw):
    pids.append(m.group(1))
print("pair", "/".join(pids) if pids else "none", "count", len(pids))
print("open_hint operator_alive", bool(pids))
