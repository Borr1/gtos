
import subprocess, re
out = subprocess.check_output(["wmic", "process", "where", "name='python.exe'", "get", "ProcessId,CommandLine", "/FORMAT:LIST"], text=True, errors="replace")
blocks = out.split("\n\n")
for b in blocks:
    if not b.strip():
        continue
    pid=""; cmd=""
    for line in b.splitlines():
        if line.startswith("ProcessId="):
            pid=line.split("=",1)[1].strip()
        if line.startswith("CommandLine="):
            cmd=line.split("=",1)[1].strip()
    if not pid:
        continue
    tag=""
    low=cmd.lower()
    if "operator" in low or "ftmo_f5" in low:
        tag="F5_WRITER"
    elif "run_book.py" in low:
        tag="OTHER_BOOK"
    elif "chair_wake" in low:
        tag="CHAIR_WAKE"
    elif "scoreboard" in low:
        tag="SCOREBOARD"
    elif "judge" in low:
        tag="JUDGE"
    else:
        tag="PY"
    print(f"{tag} pid={pid} {cmd[:220]}")
