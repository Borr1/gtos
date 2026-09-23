import json, re, subprocess, sys
from pathlib import Path
from datetime import datetime, timezone
sys.stdout.reconfigure(encoding='utf-8')
root = Path(r'C:host-local/redacted_host/repo')
print('===GIT===')
print(subprocess.check_output(['git','-C',str(root),'log','-5','--format=%h %ci %s'], text=True, encoding='utf-8', errors='replace'))
print(subprocess.check_output(['git','-C',str(root),'status','-sb'], text=True, encoding='utf-8', errors='replace')[:1500])
print('===PAIR F5===')
code = r'''
$procs = Get-CimInstance Win32_Process
foreach ($p in $procs) {
  $cl = [string]$p.CommandLine
  if ($cl -like '*run_book.py*' -and $cl -like '*operator*') {
    Write-Output ('PID=' + $p.ProcessId + ' PPID=' + $p.ParentProcessId)
    Write-Output ('CREATE=' + $p.CreationDate)
    Write-Output ('CL=' + $cl)
    Write-Output '---'
  }
}
'''
out = subprocess.check_output(['powershell','-NoProfile','-Command', code], text=True, encoding='utf-8', errors='replace')
print(out[:6000])
for block in out.split('---'):
    if 'CL=' not in block: continue
    cl = block.split('CL=',1)[1].strip()
    m = re.search(r'--tags\s+(\S+)', cl)
    tags = m.group(1).split(',') if m else []
    print('tags_n', len(tags), 'usd150', '--f5-minimal-size-usd 150' in cl, 'autoBE', 'auto-be' in cl.lower() or 'auto_be' in cl.lower())
    print('v2_desc', 'dsp_descending_lows_accepted' in tags)
    print('first3', tags[:3], 'last3', tags[-3:] if tags else [])
print('===KEEPALIVE===')
kp = json.loads((root/'pipeline_state/f5_keepalive_expected_argv.json').read_text(encoding='utf-8'))
req = kp.get('required') or []
try:
    i = req.index('--tags')
    tags = req[i+1].split(',')
    print('keepalive tags', len(tags), 'desc', 'dsp_descending_lows_accepted' in tags)
    print('v2count', sum(1 for t in tags if t.startswith('dsp_') and t in {
        'dsp_high_vol_doji_after_reclaimed_flush','dsp_two_bar_thrust_into_20high_continues','dsp_climax_onto_20high_then_fade','dsp_first_crack_failed_reclaim','dsp_three_fresh_lower_lows','dsp_descending_lows_accepted','dsp_spring_close_on_20low_through_the_box','dsp_volume_ramp_into_unrepaired_low','dsp_small_bar_on_thrust_high','dsp_wide_bar_takes_both_extremes_then_reverse','dsp_three_bar_squeeze_into_high','dsp_isolated_20h_spike_then_fade','dsp_london_cascade_into_20low_springs','dsp_rejection_wick_then_through','dsp_shakeout_holds_run_lows','dsp_cascade_two_down_bars_then_third','dsp_take_of_low_already_falling_continues','dsp_spring_first_print_of_range_low','dsp_reclaim_then_giveback','dsp_accepted_20low_then_second_flush'
    }))
except Exception as e:
    print('keepalive parse', e)
print('===CALENDAR ASSIGN===')
be = (root/'src/components/ultimate_book/book_engine.py').read_text(encoding='utf-8')
print('getattr count', be.count('_f5_calendar_events'))
for i,line in enumerate(be.splitlines(),1):
    if '_f5_calendar_events' in line:
        print(f'{i}|{line.strip()[:180]}')
print('===LAUNCH ASSERT===')
for p in [root/'f5_launch.ps1', Path(r'C:host-local/redacted_host/f5_launch.ps1')]:
    if p.exists():
        t=p.read_text(encoding='utf-8', errors='replace')
        print(p, '!= 36' in t, '!= 56' in t, '!= 49' in t)
print('===EURUSD ON_SURFACE walked===')
# sample a dsp module ON_SURFACE for FX
for rel in ['sleeves/dsp_walked_high_accepted_through.py','sleeves/dsp_descending_lows_accepted.py']:
    p = root/'src/components/ultimate_book'/rel
    if not p.exists():
        print('missing', rel); continue
    t=p.read_text(encoding='utf-8')
    i=t.find('ON_SURFACE')
    print(rel, t[i:i+400].split(')')[0][:400])
print('DONE')
