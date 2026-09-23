import json, subprocess
from pathlib import Path
from datetime import datetime, timezone

ps = r'''
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -match 'operator|GTOS_F5_FTMO|FrozenPriceIntent' } |
  Select-Object ProcessId, ParentProcessId, CommandLine |
  ConvertTo-Json -Compress
'''
r = subprocess.check_output(["powershell", "-NoProfile", "-Command", ps], text=True, errors="replace")
print("F5_PROCS", r[:2500])

# also check those two pids exist
ps2 = r'''
20216,22396 | ForEach-Object {
  $p = Get-CimInstance Win32_Process -Filter "ProcessId=$_"
  if ($p) { "{0} parent={1} name={2}" -f $p.ProcessId, $p.ParentProcessId, $p.Name }
  else { "$_ MISSING" }
}
'''
print("PAIR", subprocess.check_output(["powershell", "-NoProfile", "-Command", ps2], text=True, errors="replace"))

flow = Path(r"host-local\redacted_host\repo\judgment\flow_2026-08-27.json")
consume = Path(r"host-local\redacted_host\repo\judgment\consume_2026-08-27.json")

def last_bits(p, n=3):
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        d = json.loads(p.read_text(encoding="utf-16"))
    if isinstance(d, list):
        items = d[-n:]
        print(p.name, "n", len(d), "last", json.dumps(items, default=str)[:1200])
    elif isinstance(d, dict):
        print(p.name, "keys", list(d.keys())[:20])
        for k in ("last", "latest", "events", "skips", "rows"):
            if k in d:
                v = d[k]
                print(p.name, k, json.dumps(v[-n:] if isinstance(v, list) else v, default=str)[:1200])
                return
        print(p.name, "snip", json.dumps(d, default=str)[:800])

last_bits(flow)
last_bits(consume)
