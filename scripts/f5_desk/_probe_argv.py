import subprocess, sys, json, re
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
# avoid $ in powershell by using -Filter Script
code = r'''
$procs = Get-CimInstance Win32_Process
foreach ($p in $procs) {
  $cl = [string]$p.CommandLine
  if ($cl -like '*run_book.py*') {
    Write-Output ('PID=' + $p.ProcessId + ' PPID=' + $p.ParentProcessId)
    Write-Output ('CREATE=' + $p.CreationDate)
    Write-Output ('CL=' + $cl)
    Write-Output '---'
  }
}
'''
out = subprocess.check_output(['powershell','-NoProfile','-Command', code], text=True, encoding='utf-8', errors='replace')
print(out)
# tag count + auto-be from last CL
for block in out.split('---'):
    if 'CL=' not in block:
        continue
    cl = block.split('CL=',1)[1].strip()
    m = re.search(r'--tags\s+(\S+)', cl)
    tags = m.group(1).split(',') if m else []
    print('tags_n', len(tags), 'auto-be' in cl.lower(), 'size', '--risk-unit' in cl)
    if tags:
        print('first5', tags[:5], 'last3', tags[-3:])
print('===CAL CONST===')
ms = Path(r'C:host-local/redacted_host/repo/src/components/ultimate_book/minimal_size.py').read_text(encoding='utf-8')
for name in ['F5_CAL_AMPLIFIER_PRE_MINUTES','F5_CAL_PRIME_SIZE_MULT','F5_NAMED_HIGH']:
    i = ms.find(name)
    print(name, 'idx', i)
    if i>=0:
        print(ms[i:i+180].split('\n')[0])
print('===XA RESOLVER SNIP===')
p = Path(r'C:host-local/redacted_host/repo/src/components/ultimate_book/sleeves/xa_huge_20_extreme.py')
t = p.read_text(encoding='utf-8')
idx = t.find('direction_resolver')
print(t[max(0,idx-200):idx+500] if idx>=0 else 'no resolver')
print('===DSP +3===')
p = Path(r'C:host-local/redacted_host/repo/src/components/ultimate_book/sleeves/dsp_walked_high_accepted_through.py')
t = p.read_text(encoding='utf-8')
idx = t.find('direction_resolver')
print(t[max(0,idx-120):idx+400] if idx>=0 else 'no resolver')
print('===KEEPALIVE TAGS COUNT===')
kp = json.loads(Path(r'C:host-local/redacted_host/repo/pipeline_state/f5_keepalive_expected_argv.json').read_text(encoding='utf-8'))
req = kp.get('required') or []
# tags is the token after --tags
try:
    i = req.index('--tags')
    tags = req[i+1].split(',')
    print('keepalive tags', len(tags))
except Exception as e:
    print('keepalive parse', e)
print('forbidden', kp.get('forbidden'))
