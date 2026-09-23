import json, re, subprocess, sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
root = Path(r'C:host-local/redacted_host/repo')
print('===GIT===')
print(subprocess.check_output(['git','-C',str(root),'log','-3','--format=%h %ci %s'], text=True, encoding='utf-8', errors='replace'))
print('since c19', subprocess.check_output(['git','-C',str(root),'log','c19c3aff9..HEAD','--oneline'], text=True, encoding='utf-8', errors='replace') or '(none)')
print('===CAL===')
be = (root/'src/components/ultimate_book/book_engine.py').read_text(encoding='utf-8')
print('hits', be.count('_f5_calendar_events'))
for i,l in enumerate(be.splitlines(),1):
    if '_f5_calendar_events' in l or 'calendar_events' in l and 'self.' in l:
        print(f'{i}|{l.strip()[:200]}')
print('===LAUNCH===')
p = Path(r'C:host-local/redacted_host/f5_launch.ps1')
t = p.read_text(encoding='utf-8', errors='replace')
print('exists', p.exists(), 'mtime', p.stat().st_mtime)
print('!= 36', '!= 36' in t, '-ne 36', '-ne 36' in t)
print('!= 57', '!= 57' in t, '-ne 57', '-ne 57' in t)
for i,l in enumerate(t.splitlines(),1):
    if '36' in l or '57' in l or 'tag' in l.lower() and ('ne ' in l or '!=' in l or 'Count' in l):
        if i < 80 or 'tag' in l.lower() or '36' in l or '57' in l:
            if any(x in l for x in ['36','57','tagList','selected_tag']):
                print(f'{i}|{l.strip()[:180]}')
print('===PAIR===')
code = r'''
$procs = Get-CimInstance Win32_Process
foreach ($p in $procs) {
  $cl = [string]$p.CommandLine
  if ($cl -like '*run_book.py*' -and $cl -like '*operator*') {
    Write-Output ('PID=' + $p.ProcessId + ' CREATE=' + $p.CreationDate)
  }
}
'''
print(subprocess.check_output(['powershell','-NoProfile','-Command', code], text=True, encoding='utf-8', errors='replace')[:2000])
print('===KEEPALIVE TAGS===')
kp=json.loads((root/'pipeline_state/f5_keepalive_expected_argv.json').read_text(encoding='utf-8'))
req=kp.get('required') or []
i=req.index('--tags')
tags=req[i+1].split(',')
print('n', len(tags))
print('DONE')
