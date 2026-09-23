import json, re, subprocess, sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
root = Path(r'C:host-local/redacted_host/repo')
print('===GIT===')
print(subprocess.check_output(['git','-C',str(root),'log','-3','--format=%h %ci %s'], text=True, encoding='utf-8', errors='replace'))
print('since c19', (subprocess.check_output(['git','-C',str(root),'log','c19c3aff9..HEAD','--oneline'], text=True, encoding='utf-8', errors='replace') or '(none)').strip())
st = subprocess.check_output(['git','-C',str(root),'status','-sb'], text=True, encoding='utf-8', errors='replace')
# code dirt only
print('branch', st.splitlines()[0] if st else '')
code = r'''
$procs = Get-CimInstance Win32_Process
foreach ($p in $procs) {
  $cl = [string]$p.CommandLine
  if ($cl -like '*run_book.py*' -and $cl -like '*operator*') {
    Write-Output ('PID=' + $p.ProcessId + ' CREATE=' + $p.CreationDate)
  }
}
'''
print('===PAIR===')
print(subprocess.check_output(['powershell','-NoProfile','-Command', code], text=True, encoding='utf-8', errors='replace')[:1500])
kp=json.loads((root/'pipeline_state/f5_keepalive_expected_argv.json').read_text(encoding='utf-8'))
req=kp.get('required') or []
i=req.index('--tags')
tags=req[i+1].split(',')
print('keepalive tags', len(tags), '150' , any('f5-minimal-size-usd' in str(x) for x in req) or True)
print('size token', next((req[j+1] for j,x in enumerate(req) if x=='--f5-minimal-size-usd'), None))
print('forbidden', kp.get('forbidden'))
be=(root/'src/components/ultimate_book/book_engine.py').read_text(encoding='utf-8')
print('cal assign', be.count('self._f5_calendar_events ='))
lp=Path(r'C:host-local/redacted_host/f5_launch.ps1').read_text(encoding='utf-8', errors='replace')
print('launch -ne 57', '-ne 57' in lp, '!= 57', '!= 57' in lp, '!= 36', '!= 36' in lp)
hb=json.loads((root/'pipeline_state/ultimate_book/operator/heartbeat.json').read_text(encoding='utf-8'))
print('hb', hb.get('ts'), 'pid', hb.get('pid'), 'healthy', hb.get('healthy'))
print('DONE')
