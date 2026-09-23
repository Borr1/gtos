import json, subprocess
from datetime import datetime, timezone
from pathlib import Path

ps = r'''
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -match 'operator|GTOS_F5_FTMO|FrozenPriceIntent' } |
  Select-Object ProcessId, ParentProcessId |
  ConvertTo-Json -Compress
'''
print("F5_PROCS", subprocess.check_output(["powershell", "-NoProfile", "-Command", ps], text=True, errors="replace")[:800])
ps2 = r'''
20216,22396 | ForEach-Object {
  $p = Get-CimInstance Win32_Process -Filter "ProcessId=$_"
  if ($p) { "{0} parent={1}" -f $p.ProcessId, $p.ParentProcessId } else { "$_ MISSING" }
}
'''
print("PAIR", subprocess.check_output(["powershell", "-NoProfile", "-Command", ps2], text=True, errors="replace").strip())

hb = Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\heartbeat.json")
print("HEARTBEAT", hb.read_text(errors="replace")[:500])

ra = Path(r"host-local\redacted_host\repo\judgment\live\recent_allows.json")
d = json.loads(ra.read_text(encoding="utf-8"))
items = d if isinstance(d, list) else (d.get("allows") or [])
newest = None
for it in items:
    if isinstance(it, dict):
        ts = it.get("generated_at_utc")
        if ts and (newest is None or ts > newest["ts"]):
            newest = {"ts": ts, "cid": it.get("candidate_id"), "action": it.get("action")}
print("NEWEST_ALLOW", json.dumps(newest))

log = Path(r"host-local\redacted_host\repo\shadow_logs\f5_verification.log")
text = log.read_text(encoding="utf-16")
lines = [ln for ln in text.splitlines() if ln.strip()]
print("LOG_LAST", lines[-1][:240])
late = [ln for ln in lines if ln.startswith("2026-08-27 10:") or ln.startswith("2026-08-27 11:")]
holes = [ln for ln in late if ("reconciliation FAILED" in ln or "immutable_entry_risk_unavailable" in ln or "governor_ready false" in ln.lower())]
print("HOLES_AFTER_10Z", len(holes))
if holes:
    print("HOLE_LAST", holes[-1][:240])

flow = Path(r"host-local\redacted_host\repo\judgment\flow_2026-08-27.json")
print("FLOW_MTIME", datetime.fromtimestamp(flow.stat().st_mtime, timezone.utc).isoformat())
