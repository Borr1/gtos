import subprocess
r = subprocess.run(["wmic","process","where","name='python.exe'","get","ProcessId,CommandLine","/format:csv"], capture_output=True, text=True)
for line in r.stdout.splitlines():
    if "operator" in line or "f5_launch" in line:
        parts = [p.strip() for p in line.split(",")]
        print("PIDLINE", parts[-1] if parts else line[:80])
        # csv: Node,CommandLine,ProcessId
        if len(parts) >= 3:
            print("PID", parts[-1], "ns", "f5" if "operator" in line else "other")
r2 = subprocess.run(["wmic","process","where","name='powershell.exe'","get","ProcessId,CommandLine","/format:csv"], capture_output=True, text=True)
for line in r2.stdout.splitlines():
    if "f5_launch" in line or "GTOS_F5" in line:
        parts = [p.strip() for p in line.split(",")]
        print("PS", parts[-1] if parts else line[:120])
