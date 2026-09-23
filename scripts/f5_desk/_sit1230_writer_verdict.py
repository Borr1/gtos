import subprocess, re, json, sys
from pathlib import Path
from datetime import datetime, timezone

# writer health
out = subprocess.check_output(
    ['wmic', 'process', 'where', "name='python.exe'", 'get', 'ProcessId,CommandLine', '/FORMAT:LIST'],
    text=True, errors='replace'
)
hits = []
for b in out.split('\n\n'):
    if not b.strip():
        continue
    cl = ''
    pid = ''
    for line in b.splitlines():
        if line.startswith('CommandLine='):
            cl = line[len('CommandLine='):]
        elif line.startswith('ProcessId='):
            pid = line[len('ProcessId='):].strip()
    if re.search(r'book_owner|GTOS_F5|ftmo_f5|ultimate_book|writer', cl, re.I):
        hits.append((pid, cl[:200]))
print('writer_hits', len(hits))
for pid, cl in hits:
    print(pid, '|', cl)

raw = subprocess.check_output(
    "wmic process where \"CommandLine like '%%operator%%'\" get ProcessId,CommandLine /FORMAT:LIST",
    shell=True, text=True, errors='replace',
)
pids = re.findall(r'ProcessId=(\d+)', raw)
pair = '/'.join(pids) if pids else 'none'
print('pair', pair, 'count', len(pids))

try:
    t = subprocess.check_output(['schtasks', '/Query', '/TN', 'GTOS_F5_FTMO', '/FO', 'LIST', '/V'], text=True, errors='replace')
    for key in ('Status:', 'Last Run Time:', 'Last Result:', 'Next Run Time:'):
        for line in t.splitlines():
            if line.strip().startswith(key):
                print(line.strip())
except Exception as e:
    print('schtasks_err', e)

# verdict from latest slate
sys.path.insert(0, r'host-local\redacted_host\repo')
from scripts.f5_desk import common

slate_ptr = Path(r'host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\state\latest_slate.json')
ptr = json.loads(slate_ptr.read_text(encoding='utf-8'))
slate = json.loads(Path(ptr['path']).read_text(encoding='utf-8'))
slate_id = slate.get('slate_id') or ptr['slate_id']
fingerprint = slate.get('fingerprint') or ptr['fingerprint']
opens = slate.get('open_positions') or []
open_syms = set()
for o in opens:
    sym = (o.get('symbol') or '')
    open_syms.add(sym)
    open_syms.add(sym.replace('_cash', ''))

cands = slate.get('candidates') or []
verdicts = []
seen = set()
for c in cands:
    cid = c.get('candidate_id') or ''
    if not cid or cid in seen:
        continue
    seen.add(cid)
    status = (c.get('status') or '').lower()
    sym = (c.get('symbol') or c.get('broker_symbol') or '')
    sym_base = sym.replace('_cash', '')
    if status == 'filled':
        continue
    if sym_base == 'USDJPY':
        verdicts.append({
            'candidate_id': cid,
            'verdict': 'hold',
            'mechanism': 'microstructure',
            'why_code': 'usdjpy_scrub_full_verification_hold',
            'confidence': 0.85,
        })
        continue
    if sym_base in open_syms or sym in open_syms:
        verdicts.append({
            'candidate_id': cid,
            'verdict': 'hold',
            'mechanism': 'microstructure',
            'why_code': 'occupied_no_second_ticket',
            'confidence': 0.8,
        })
        continue
    if sym_base in ('XAUUSD', 'GOLD'):
        verdicts.append({
            'candidate_id': cid,
            'verdict': 'hold',
            'mechanism': 'microstructure',
            'why_code': 'owner_spent_gold_179380936_tonight',
            'confidence': 0.9,
        })
        continue
    if sym_base == 'EURUSD' and '179272692' in cid:
        continue
    verdicts.append({
        'candidate_id': cid,
        'verdict': 'abstain',
        'mechanism': '',
        'why_code': 'chair_sit_no_place_from_seat',
        'confidence': 0.55,
    })

holds = [v for v in verdicts if v['verdict'] == 'hold']
abstains = [v for v in verdicts if v['verdict'] == 'abstain'][:12]
notes = (
    '12:30 ICT sit: eq~98024 day_net~-561 open5 UK100/US30/EURUSD/GBPUSD/GER40 leave; '
    'USDJPY scrub HOLD; gold spent HOLD; no place/remint; writer pair %s; '
    'f5_verification close-fail noise retcode=10011; aim >100k'
) % pair
payload = {
    'schema': 'gtos.f5.judge.verdict.v1',
    'slate_id': slate_id,
    'fingerprint': fingerprint,
    'written_at_utc': datetime.now(timezone.utc).isoformat(),
    'verdicts': holds + abstains,
    'manage': [],
    'notes': notes[:2000],
}
inbox = Path(r'host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\inbox\verdict.json')
common.write_json_atomic(inbox, payload)
print('verdict_written', slate_id, fingerprint, 'holds', len(holds), 'abstains', len(abstains))
print('notes', notes)
